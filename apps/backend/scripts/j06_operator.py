"""The canonical J-06 operator bridge (``docs/rapid-validation-spec.md`` §7.2/§7.2.1/§7.3, r11).

**Why this exists.** ``tick_recorder.py`` and ``vault.py`` both existed, but nothing joined them:
the recorder's REST/CLI entry points take raw ``symbols``/``dates`` and start fetching, and
``seal_shard``/``assign_shard``/``expose_shard`` had no production caller. An operator running the
recorder directly over arbitrary symbol-days is NOT J-06 completion -- it skips the screen binding,
the universe freeze, the commitment, and the seal. This module owns the one lawful sequence:

    screen provenance -> date/panel validation -> vault secret -> universe registration
    -> HMAC membership -> recorder -> immediate seal of selected datasets
    -> batch verification -> paired bar backfill -> readiness

**It duplicates nothing.** The recorder walk, ``DatasetStore``, the split rule, the vault ledgers,
the HMAC seal, the bar backfill and readiness all come from their existing owners; this module is
sequencing and refusal only.

    python -m scripts.j06_operator provenance   # §4 bind the screen, before any registration
    python -m scripts.j06_operator register     # §6 validate -> register -> HMAC (pre-fetch)
    python -m scripts.j06_operator preflight    # §7 after registration, before market data
    python -m scripts.j06_operator record       # §8 the real recording + immediate seal
    python -m scripts.j06_operator verify       # §10/§12 batch verification + acceptance
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.env import load_env  # noqa: E402

load_env()  # the TAPEOLOGY_*/ALPACA_* contract lives in apps/backend/.env, never in this file

from app.config import CONFIG  # noqa: E402
from app.research import micro_tier_b_screen as tb  # noqa: E402
from app.research import tick_recorder as tr  # noqa: E402
from app.research import vault  # noqa: E402
from app.research.datasets import DatasetStore  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
SCREEN_DIR = REPO / "reports" / "tier-b-screen-r10"
STATE_DIR = REPO / "reports" / "j06-tranche"

UNIVERSE_ID = "rapid-microscope-j06-starter"
SCREEN_ID = "rapid-microscope-tier-b-r11"
EXPECTED_RESOLUTION_SHA = "fb89c5a276aa1a3b43eae2672bd62e478b933e6bb11970a3bb5e9b0dbea3dae5"

#: §6, frozen by the owner. Tier-A PG/AAPL/MSFT/NVDA + the three resolved Tier-B + the Tier-C ETF.
SYMBOL_RULE = ["PG", "AAPL", "MSFT", "NVDA", "AG", "LYFT", "WULF", "SPY"]
DATE_RULE = ["2026-06-10", "2026-06-17", "2026-06-24", "2026-07-01", "2026-07-08",
             "2026-07-15", "2026-07-22", "2026-07-29", "2026-08-05", "2026-08-12"]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _write(name: str, payload: dict) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def _ledgers():
    d = CONFIG.dataset_dir_resolved()
    return (vault.universe_ledger_for_dataset_dir(d), vault.shard_ledger_for_dataset_dir(d),
            vault.screen_provenance_ledger_for_dataset_dir(d), DatasetStore(d), d)


# === §2 + §4: verify the accepted screen, then bind it before any registration =====================


def _verify_screen() -> dict:
    """§2. Refuses outright on any mismatch -- the tranche is never registered against a screen
    whose artifacts moved."""
    res = SCREEN_DIR / "tier-b-resolution.json"
    sha = _sha(res)
    if sha != EXPECTED_RESOLUTION_SHA:
        raise SystemExit(f"STOP: resolution artifact sha256 {sha} != expected {EXPECTED_RESOLUTION_SHA}")
    resolution = json.loads(res.read_text())
    if resolution["resolved_tier_b"] != ["AG", "LYFT", "WULF"]:
        raise SystemExit(f"STOP: resolved Tier-B is {resolution['resolved_tier_b']!r}")
    snap = json.loads((SCREEN_DIR / "source-snapshot.json").read_text())
    for name, meta in snap["files"].items():
        if _sha(SCREEN_DIR / f"{name}.txt") != meta["sha256"]:
            raise SystemExit(f"STOP: frozen source snapshot {name} changed")
    abort = json.loads((SCREEN_DIR / "r10-execution-status.json").read_text())
    if abort["status"] != "ABORTED_PRE_RESOLUTION" or abort["superseded_by"] != "r11":
        raise SystemExit("STOP: the r10 abort artifact is not intact")
    spread = {r["ticker"]: r for r in json.loads((SCREEN_DIR / "spread.json").read_text())["rows"]}
    for tic in resolution["resolved_tier_b"]:
        done = [s["session"] for s in spread[tic]["per_session"]
                if "error" not in s and s.get("eligible_observations", 0) > 0]
        if len(done) != tb.SPREAD_SESSIONS:
            raise SystemExit(f"STOP: {tic} spread window is {len(done)}/{tb.SPREAD_SESSIONS}")
    universe = json.loads((SCREEN_DIR / "candidate-universe.json").read_text())
    return {"resolution": resolution, "snapshot": snap, "universe": universe}


def _validate_panel_and_dates(sessions: set[str] | None = None) -> dict:
    """§1. Every check is mechanical; ANY failure stops rather than substituting a date."""
    if sorted(SYMBOL_RULE) != sorted(set(SYMBOL_RULE)):
        raise SystemExit("STOP: duplicate symbol in symbol_rule")
    if sorted(DATE_RULE) != sorted(set(DATE_RULE)):
        raise SystemExit("STOP: duplicate date in date_rule")
    tb.assert_no_exposed_session(DATE_RULE)           # refuses a screening/EXPOSED session
    if sessions is not None:
        invalid = [d for d in DATE_RULE if d not in sessions]
        if invalid:
            raise SystemExit(f"STOP: not valid completed regular sessions: {invalid}")
    d0 = datetime.fromisoformat(DATE_RULE[0]).date()
    d1 = datetime.fromisoformat(DATE_RULE[-1]).date()
    span_days = (d1 - d0).days
    if span_days < 42:
        raise SystemExit(f"STOP: span {span_days}d < 6 calendar weeks")
    pairs = len(SYMBOL_RULE) * len(DATE_RULE)
    date_conc = len(SYMBOL_RULE) / pairs
    sym_conc = len(DATE_RULE) / pairs
    if pairs != 80 or date_conc > 0.20 or sym_conc > 0.25:
        raise SystemExit(f"STOP: arithmetic {pairs=} {date_conc=} {sym_conc=}")
    return {"planned_pairs": pairs, "span_days": span_days,
            "max_date_concentration": date_conc, "max_symbol_concentration": sym_conc}


def stage_provenance() -> dict:
    """§4. Binds the screen immutably into its own typed vault ledger BEFORE registration."""
    checked = _verify_screen()
    _, _, sled, _, _ = _ledgers()
    row = vault.record_screen_provenance(
        sled,
        screen_id=SCREEN_ID,
        spec_revision="r11",
        screening_cutoff_utc=checked["resolution"]["screening_cutoff_utc"],
        source_snapshot_sha256={k: v["sha256"] for k, v in checked["snapshot"]["files"].items()},
        candidate_universe_membership_hash=checked["universe"]["pre_filter_membership_hash"],
        screening_artifacts={p.name: _sha(p) for p in sorted(SCREEN_DIR.iterdir()) if p.is_file()},
        resolution_artifact_sha256=EXPECTED_RESOLUTION_SHA,
        resolved_tier_b=checked["resolution"]["resolved_tier_b"],
        resolution_rule_identity=(
            "§7.2.1 (h): passing seeds in documented order, then replacements ranked by "
            f"sha256({tb.TIER_B_R10_SALT!r} + normalized_ticker), exactly 3"),
    )
    out = {"stage": "screen_provenance", "screen_id": SCREEN_ID,
           "row_index": row.get("row_index"), "resolved_tier_b": row["resolved_tier_b"],
           "chain_ok": sled.verify_chain()["ok"], "recorded_at": row["recorded_at"]}
    _write("screen-provenance.json", out)
    return out


# === §6: registration + HMAC membership, BEFORE the first fetch ====================================


def stage_register(sessions: set[str] | None = None) -> dict:
    """§6. Registers exactly one immutable universe and computes the HMAC seal assignment for all
    80 pairs BEFORE any market data is requested. Idempotent: a restart re-resolves the SAME row,
    the SAME nonce and the SAME commitment (``register_universe``'s own discipline)."""
    _verify_screen()
    arithmetic = _validate_panel_and_dates(sessions)
    uled, _, sled, _, _ = _ledgers()
    if vault.find_screen_provenance(sled, SCREEN_ID) is None:
        raise SystemExit("STOP: screen provenance is not bound -- run `provenance` first (§4)")

    secret = vault.load_vault_secret()                      # never printed, logged or persisted
    commitment = vault.commit_vault_secret(secret)
    universe = vault.register_universe(
        uled, universe_id=UNIVERSE_ID, symbol_rule=SYMBOL_RULE, date_rule=DATE_RULE,
        vault_secret_commitment=commitment,
    )
    pairs = sorted(vault.expected_recording_pairs(universe))
    sealed_members = [[s, d] for s, d in pairs if vault.compute_seal(secret, s, d)]
    # The membership itself is NEVER served or written to a public artifact -- only its COUNT is.
    out = {
        "stage": "universe_registration", "universe_id": UNIVERSE_ID,
        "registered_at": universe["registered_at"], "rule_hash": universe["rule_hash"],
        "rule_commitment": universe["rule_commitment"],
        "vault_secret_commitment": universe["vault_secret_commitment"],
        "symbol_rule": SYMBOL_RULE, "date_rule": DATE_RULE,
        "expected_pairs": len(pairs), "hmac_selected_count": len(sealed_members),
        "arithmetic": arithmetic, "universe_ledger_chain_ok": uled.verify_chain()["ok"],
    }
    _write("universe-registration.json", out)
    # the hidden partition is kept OUT of reports/; the recorder reads it from the secret directly
    return out


# === §7: preflight after registration, before market data =========================================


def stage_preflight() -> dict:
    """§7. Every check is a refusal, not a warning."""
    uled, shled, sled, store, ddir = _ledgers()
    universe = vault.find_universe(uled, UNIVERSE_ID)
    if universe is None:
        raise SystemExit("STOP: no registered universe -- run `register` first (§6)")
    checks: dict = {}
    checks["universe_ledger_chain_ok"] = uled.verify_chain()["ok"]
    checks["shard_ledger_chain_ok"] = shled.verify_chain()["ok"]
    checks["screen_provenance_chain_ok"] = sled.verify_chain()["ok"]
    try:
        tr.verify_preservation_capability()
        checks["tr19_preservation"] = True
    except tr.RecorderPreservationCapabilityMissing as exc:
        raise SystemExit(f"STOP: TR-19 preservation capability missing: {exc}")
    pairs = sorted(vault.expected_recording_pairs(universe))
    checks["expected_pairs"] = len(pairs)
    if len(pairs) != 80:
        raise SystemExit(f"STOP: expected 80 pairs, universe computes {len(pairs)}")
    tb.assert_no_exposed_session(universe["date_rule"])
    checks["no_exposed_session_collision"] = True

    existing, errors = store.list()
    checks["dataset_store_readable"] = errors == []
    # `session_date`/`date` are NOT fields on a dataset record -- comparing them yielded
    # (symbol, None) and could never collide, so this check silently passed a real collision
    # (legacy NVDA 2026-07-08). The session date is DERIVED from the recorded window, as elsewhere.
    have = {(r["symbol"], _session_date_of(r)) for r in existing}
    collisions = sorted(p for p in pairs if p in have)
    checks["colliding_existing_datasets"] = collisions
    if collisions:
        raise SystemExit(
            f"STOP: {len(collisions)} proposed symbol-day(s) already exist as datasets: "
            f"{collisions[:5]}… A legacy/exposed dataset must never be counted as a newly recorded "
            "J-06 shard, and no date may be substituted.")
    ck = tr.resolve_tick_recorder_checkpoint_dir(ddir)
    Path(ck).mkdir(parents=True, exist_ok=True)
    checks["checkpoint_dir_writable"] = os.access(ck, os.W_OK)
    checks["bar_dir"] = CONFIG.bar_dir_resolved()
    chunks = tr.plan_recorder_chunks(universe["symbol_rule"], universe["date_rule"])
    checks["planned_chunks"] = len(chunks)
    st = os.statvfs(ddir)
    free_gb = st.f_bavail * st.f_frsize / 1e9
    checks["disk_free_gb"] = round(free_gb, 1)
    if free_gb < 20:
        raise SystemExit(f"STOP: only {free_gb:.1f} GB free")
    from app.research.routes import get_study_market_adapter
    adapter = get_study_market_adapter()
    checks["adapter"] = type(adapter).__name__
    checks["credentials_available"] = bool(adapter.is_available())
    checks["historical_feed"] = getattr(adapter, "historical_feed", None)
    if not checks["credentials_available"]:
        raise SystemExit("STOP: no Alpaca credentials available")
    out = {"stage": "preflight", "universe_id": UNIVERSE_ID, "checks": checks, "at": _utc()}
    _write("preflight.json", out)
    return out


# === §8/§9: the real recording, with immediate seal of HMAC-selected datasets =====================

CANCEL_SENTINEL = STATE_DIR / "CANCEL"


def _session_date_of(record: dict) -> str:
    """The dataset's ET session date -- derived from its own recorded window, never re-guessed."""
    from zoneinfo import ZoneInfo
    start = datetime.fromisoformat(record["window_start_utc"].replace("Z", "+00:00"))
    return start.astimezone(ZoneInfo("America/New_York")).date().isoformat()


def stage_record() -> dict:
    """§8. Walks the registered universe pair by pair through the EXISTING recorder, and seals each
    HMAC-selected dataset IMMEDIATELY after it finalizes -- before anything could read it.

    Restart-safe by construction (§9): the universe is looked up, never re-registered; the recorder's
    own checkpoint store means a completed chunk is never re-fetched; ``seal_shard`` refuses a second
    row for an already-sealed shard, so a re-run cannot double-seal. Cooperative cancellation is a
    sentinel file, so the in-flight symbol-day settles rather than being killed."""
    from app.research.routes import get_study_market_adapter

    uled, shled, sled, store, ddir = _ledgers()
    universe = vault.find_universe(uled, UNIVERSE_ID)
    if universe is None:
        raise SystemExit("STOP: no registered universe -- run `register` first")
    secret = vault.load_vault_secret()
    if universe["vault_secret_commitment"] != vault.commit_vault_secret(secret):
        raise SystemExit("STOP: the configured vault secret does not match the registered commitment")

    pairs = sorted(vault.expected_recording_pairs(universe))
    checkpoint = tr.RecorderCheckpointStore(tr.resolve_tick_recorder_checkpoint_dir(ddir))
    adapter = get_study_market_adapter()
    # NB: bar pairing (§11) is a SEPARATE stage -- it needs the registry/journal context the
    # recorder CLI builds, and eagerly resolving it here aborted this run at startup.

    # ONE full listing, at start. `DatasetStore.list()` re-hashes the whole store (4.3 GB and
    # growing), so calling it per pair made the walk quadratic -- ~105 s/pair and worsening. The
    # recorder already RETURNS the finalized `dataset_id`, and `store.get(id)` reads one record, so
    # the loop below needs no further full listing.
    existing = {(_session_date_of(r), r["symbol"]): r["id"] for r in store.list()[0]}
    outcomes, sealed_now, started = [], 0, time.time()
    cancelled = False
    for n, (symbol, date) in enumerate(pairs, 1):
        if CANCEL_SENTINEL.exists():
            cancelled = True
            sys.stderr.write(f"  cooperative cancel honoured after {n - 1}/{len(pairs)} pairs\n")
            break
        key = (date, symbol)
        if key in existing:
            outcomes.append({"symbol": symbol, "date": date, "outcome": "already_recorded",
                             "dataset_id": existing[key]})
        else:
            chunks = tr.plan_recorder_chunks([symbol], [date])
            try:
                tick_outcomes = tr.run_tick_recording(chunks, store, checkpoint, adapter, CONFIG)
            except (AttributeError, TypeError, NameError):
                raise  # a coding fault is never a disclosed vendor failure
            except Exception as exc:  # noqa: BLE001 -- disclosed, never silent, never substituted
                outcomes.append({"symbol": symbol, "date": date, "outcome": "failed",
                                 "detail": f"{type(exc).__name__}: {exc}"})
                continue
            dsid = next((o["dataset_id"] for o in tick_outcomes if o.get("dataset_id")), None)
            if dsid is None:
                failed = [o for o in tick_outcomes if o["outcome"] == "failed"]
                detail = failed[0].get("detail") if failed else "no dataset finalized for this pair"
                outcomes.append({"symbol": symbol, "date": date, "outcome": "failed",
                                 "detail": detail, "failed_chunks": len(failed)})
                continue
            existing[key] = dsid
            outcomes.append({"symbol": symbol, "date": date, "outcome": "recorded",
                             "dataset_id": dsid})
        # --- IMMEDIATE seal, before anything could read this dataset -------------------------
        rec = store.get(existing[key])
        if vault.compute_seal(secret, symbol, date):
            if vault._latest_shard_row(shled, rec["id"]) is None:
                counts = rec.get("event_counts") or {}
                vault.seal_shard(
                    shled, dataset_id=rec["id"], universe_id=UNIVERSE_ID,
                    content_checksum=rec["checksum"],
                    event_count=int(counts.get("trades", 0)) + int(counts.get("quotes", 0)),
                    vault_secret=secret,
                )
                sealed_now += 1
        if n % 5 == 0:
            done = sum(1 for o in outcomes if o["outcome"] in ("recorded", "already_recorded"))
            sys.stderr.write(f"  [{n}/{len(pairs)}] {done} recorded · {time.time() - started:.0f}s\n")

    out = {"stage": "recording", "universe_id": UNIVERSE_ID,
           "cancelled_cooperatively": cancelled,
           "pairs_attempted": len(outcomes),
           "recorded": sum(1 for o in outcomes if o["outcome"] == "recorded"),
           "already_recorded": sum(1 for o in outcomes if o["outcome"] == "already_recorded"),
           "failed": sum(1 for o in outcomes if o["outcome"] == "failed"),
           "sealed_this_run": sealed_now,
           "elapsed_seconds": round(time.time() - started, 1),
           "outcomes": outcomes, "at": _utc()}
    prior = []
    p = STATE_DIR / "recording-runs.json"
    if p.exists():
        prior = json.loads(p.read_text())["runs"]
    _write("recording-runs.json", {"runs": prior + [out]})
    return {k: v for k, v in out.items() if k != "outcomes"}


# === §11 paired bar backfill + §10/§12 verification and acceptance ===============================


def stage_bars() -> dict:
    """§11. The EXISTING paired bar-backfill path, over the symbol-days actually recorded. No second
    bar implementation; failures are reported honestly."""
    from app.research.bars import BarStore
    from app.research.routes import (ResearchRegistry, get_bar_index, get_study_market_adapter,
                                     set_registry)
    from app.research.store import JournalStore

    uled, _, _, store, ddir = _ledgers()
    universe = vault.find_universe(uled, UNIVERSE_ID)
    recorded = _recorded_pairs(store, universe)
    tick_outcomes = [{"symbol": s, "date": d, "outcome": "fetched", "dataset_id": i}
                     for (s, d), i in sorted(recorded.items())]
    journal = JournalStore(str(Path(ddir).parent / "journal.db"), CONFIG)
    set_registry(ResearchRegistry(journal, CONFIG))
    try:
        outcomes = tr.pair_bar_backfill_for_recorded_days(
            tick_outcomes, BarStore(CONFIG.bar_dir_resolved()), get_bar_index(),
            __import__("app.research.routes", fromlist=["get_registry"]).get_registry(),
        )
    finally:
        set_registry(None)
        journal.close()
    from collections import Counter
    out = {"stage": "paired_bar_backfill", "symbol_days": len(tick_outcomes),
           "outcomes": Counter(o.get("outcome", "?") for o in outcomes), "at": _utc()}
    out["outcomes"] = dict(out["outcomes"])
    _write("bar-pairing.json", out)
    return out


#: Only a dataset carrying the recorder's own schema basis is a J-06 shard. A legacy dataset that
#: happens to occupy a registered symbol-day is NOT one (§7: "do not silently count a legacy/exposed
#: dataset as a newly recorded J-06 shard").
J06_SCHEMA_BASIS = tr.RECORDER_SCHEMA_BASIS


def _recorded_pairs(store: DatasetStore, universe: dict, *, records=None) -> dict:
    """Every registered pair with a genuine J-06 shard, keyed (symbol, date) -> dataset id."""
    expected = set(vault.expected_recording_pairs(universe))
    out = {}
    for r in (records if records is not None else store.list()[0]):
        key = (r["symbol"], _session_date_of(r))
        if key in expected and r.get("schema_basis") == J06_SCHEMA_BASIS:
            out[key] = r["id"]
    return out


def _legacy_occupying_registered_pairs(store: DatasetStore, universe: dict, *, records=None) -> list:
    """Registered symbol-days occupied by a dataset this recorder did NOT write -- the §7 collision
    condition, surfaced explicitly rather than absorbed into the tranche count."""
    expected = set(vault.expected_recording_pairs(universe))
    out = []
    for r in (records if records is not None else store.list()[0]):
        key = (r["symbol"], _session_date_of(r))
        if key in expected and r.get("schema_basis") != J06_SCHEMA_BASIS:
            out.append({"symbol": key[0], "date": key[1], "dataset_id": r["id"],
                        "created_utc": r.get("created_utc"), "schema_basis": r.get("schema_basis")})
    return out


def stage_verify() -> dict:
    """§10 batch verification (TR-4) + §12 acceptance, computed from the CANONICAL stores."""
    from collections import Counter
    from zoneinfo import ZoneInfo

    uled, shled, sled, store, ddir = _ledgers()
    universe = vault.find_universe(uled, UNIVERSE_ID)
    records, errors = store.list()
    by_id = {r["id"]: r for r in records}
    expected = sorted(vault.expected_recording_pairs(universe))
    recorded = _recorded_pairs(store, universe, records=records)
    collisions = _legacy_occupying_registered_pairs(store, universe, records=records)
    disclosed = sorted(set(expected) - set(recorded))

    # --- TR-4: recorded == registered universe net of disclosed failures ---------------------
    tr4 = vault.verify_recording_batch(
        universe, recorded=list(recorded), disclosed_failures=disclosed)

    secret = vault.load_vault_secret()
    hmac_selected = [p for p in expected if vault.compute_seal(secret, *p)]
    sealed_ids = {r["dataset_id"] for r in shled.verified_rows()
                  if r.get("exposure_state") == vault.STATE_SEALED and r.get("dataset_id")}
    selected_recorded = [p for p in hmac_selected if p in recorded]
    sealed_selected = [p for p in selected_recorded if recorded[p] in sealed_ids]

    dates = sorted({d for _s, d in recorded})
    symbols = sorted({s for s, _d in recorded})
    n = len(recorded)
    date_conc = max(Counter(d for _s, d in recorded).values()) / n
    sym_conc = max(Counter(s for s, _d in recorded).values()) / n
    et = ZoneInfo("America/New_York")

    def _full_session(rec) -> bool:
        a = datetime.fromisoformat(rec["window_start_utc"].replace("Z", "+00:00")).astimezone(et)
        b = datetime.fromisoformat(rec["window_end_utc"].replace("Z", "+00:00")).astimezone(et)
        return (b - a).total_seconds() >= 6.4 * 3600

    new = [by_id[i] for i in recorded.values()]
    full = sum(1 for r in new if _full_session(r))
    d0 = datetime.fromisoformat(dates[0]).date(); d1 = datetime.fromisoformat(dates[-1]).date()
    runs = json.loads((STATE_DIR / "recording-runs.json").read_text())["runs"]

    out = {
        "stage": "acceptance", "universe_id": UNIVERSE_ID, "at": _utc(),
        "planned_pairs": len(expected), "recorded_pairs": n,
        "disclosed_failures": [list(p) for p in disclosed],
        "tr4_batch_verification": tr4,
        "legacy_collisions_excluded_from_tranche": collisions,
        "distinct_symbols": len(symbols), "symbols": symbols,
        "pg_present": "PG" in symbols, "spy_present": "SPY" in symbols,
        "resolved_tier_b_present": sorted(set(symbols) & {"AG", "LYFT", "WULF"}),
        "distinct_dates": len(dates), "calendar_span_days": (d1 - d0).days,
        "max_single_date_concentration": round(date_conc, 4),
        "max_single_symbol_concentration": round(sym_conc, 4),
        "full_session_pct": round(full / n * 100, 1),
        "all_checksummed": all(bool(r.get("checksum")) for r in new),
        "dataset_list_errors": len(errors),
        "schema_basis_distribution": {str(k): v for k, v in Counter(r.get("schema_basis") for r in new).items()},
        "quote_size_unit_distribution": {str(k): v for k, v in Counter(r.get("quote_size_unit") for r in new).items()},
        "split_distribution": {str(k): v for k, v in Counter(r.get("split") for r in new).items()},
        "hmac_selected_total": len(hmac_selected),
        "hmac_selected_recorded": len(selected_recorded),
        "sealed_shard_rows": len(sealed_ids),
        "sealed_of_selected_recorded": len(sealed_selected),
        "unsealed_selected_recorded": [list(p) for p in selected_recorded if p not in sealed_selected],
        "universe_registrations": len([r for r in uled.verified_rows()
                                       if r.get("universe_id") == UNIVERSE_ID]),
        "screen_provenance_bound": vault.find_screen_provenance(sled, SCREEN_ID) is not None,
        "universe_ledger_chain_ok": uled.verify_chain()["ok"],
        "shard_ledger_chain_ok": shled.verify_chain()["ok"],
        "screen_provenance_chain_ok": sled.verify_chain()["ok"],
        "duplicate_dataset_ids": len(recorded) - len(set(recorded.values())),
        "recording_runs": len(runs),
        "cooperative_cancel_observed": any(r["cancelled_cooperatively"] for r in runs),
        "legacy_datasets_untouched": len(records) - n,
        "research_gate_150_symbol_days": {"have": n, "target": 150, "met": n >= 150},
    }
    _write("acceptance.json", out)
    return out


_STAGES = {"provenance": stage_provenance, "register": stage_register,
           "preflight": stage_preflight, "record": stage_record,
           "bars": stage_bars, "verify": stage_verify}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in _STAGES:
        print(f"usage: python -m scripts.j06_operator {{{'|'.join(_STAGES)}}}")
        return 2
    out = _STAGES[sys.argv[1]]()
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
