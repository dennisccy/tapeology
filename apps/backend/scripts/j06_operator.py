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
from app.research.dataset_index import indexed_dataset_store  # noqa: E402
from app.research.datasets import DatasetStore  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
SCREEN_DIR = REPO / "reports" / "tier-b-screen-r10"
#: The STARTER tranche's own artifact directory. Immutable: every file the 2026-08 campaign wrote
#: lives here and must never be overwritten by a later era.
STARTER_STATE_DIR = REPO / "reports" / "j06-tranche"
#: The per-invocation artifact directory. Rebound by `_select_universe` for a later era so a second
#: campaign cannot clobber the first's acceptance.json, recording-runs.json or TR-2 analysis
#: (r14.1, G) -- pre-r14.1 every stage wrote to the one shared path regardless of universe.
STATE_DIR = STARTER_STATE_DIR

#: The ORIGINAL starter tranche's frozen identity. Immutable: `vault.register_universe` refuses a
#: second registration of this id under any different rule, and nothing below may re-derive it.
STARTER_UNIVERSE_ID = "rapid-microscope-j06-starter"
SCREEN_ID = "rapid-microscope-tier-b-r11"
EXPECTED_RESOLUTION_SHA = "fb89c5a276aa1a3b43eae2672bd62e478b933e6bb11970a3bb5e9b0dbea3dae5"

#: §7.2.1(i), frozen by the owner. Tier-A PG/AAPL/MSFT/NVDA + the three RESOLVED Tier-B + the
#: Tier-C ETF. **Shared by every universe this script ever registers**: §7.2.1(j)'s screen-once
#: discipline forbids re-running the Tier-B screen, and §7.2.1(i) names these exact eight slots, so
#: a second era reuses the resolved list verbatim rather than deriving a new one.
SYMBOL_RULE = ["PG", "AAPL", "MSFT", "NVDA", "AG", "LYFT", "WULF", "SPY"]

#: The starter tranche's own ten dates. A LATER era supplies its own via `--dates-file`; this list is
#: never edited (doing so would silently redefine `expected_recording_pairs` for a registered
#: universe, which `register_universe` refuses anyway).
STARTER_DATE_RULE = ["2026-06-10", "2026-06-17", "2026-06-24", "2026-07-01", "2026-07-08",
                     "2026-07-15", "2026-07-22", "2026-07-29", "2026-08-05", "2026-08-12"]

# --- r14: the per-invocation universe, defaulting to the starter tranche ---------------------------
#
# Pre-r14 every stage read the two module constants directly, so a SECOND corpus era could not be
# registered without editing this file -- which would have silently redefined the FIRST universe's
# own rule for every later verification run. The two names below are what the stages read; they
# default to the starter identity, so every existing invocation is byte-identical, and
# `_select_universe` is the only thing that ever changes them.
UNIVERSE_ID = STARTER_UNIVERSE_ID
DATE_RULE = list(STARTER_DATE_RULE)

#: The starter tranche's frozen pair arithmetic (§7.2.1(i): 8 symbols x 10 dates). Enforced ONLY for
#: the starter universe -- a later era's own arithmetic is its date-rule size times the same panel.
STARTER_EXPECTED_PAIRS = 80


def _is_starter() -> bool:
    """Whether this invocation is operating on the ORIGINAL starter tranche."""
    return UNIVERSE_ID == STARTER_UNIVERSE_ID


def _select_universe(universe_id: str | None, dates_file: str | None) -> dict:
    """r14: point this script at a DIFFERENT registered universe for a later corpus era.

    Both must be given together -- a new universe id with the starter's dates, or new dates under
    the starter's id, are each a way to corrupt a frozen registration, so neither is allowed alone.
    `SYMBOL_RULE` is deliberately NOT parameterized: §7.2.1(i) fixes the panel at those eight slots
    and §7.2.1(j) forbids re-screening Tier-B, so a second era reuses it unchanged."""
    global UNIVERSE_ID, DATE_RULE, STATE_DIR
    if universe_id is None and dates_file is None:
        return {"universe_id": UNIVERSE_ID, "date_rule_size": len(DATE_RULE), "source": "starter"}
    if universe_id is None or dates_file is None:
        raise SystemExit(
            "STOP: --universe-id and --dates-file must be given together. A new universe id under "
            "the starter's dates (or vice versa) is a way to corrupt a frozen registration."
        )
    if universe_id == STARTER_UNIVERSE_ID:
        raise SystemExit(
            f"STOP: {STARTER_UNIVERSE_ID!r} is the ORIGINAL starter tranche and is immutable -- a "
            "later era registers its own universe id, never a second rule under this one."
        )
    dates = [line.strip() for line in Path(dates_file).read_text().splitlines() if line.strip()]
    if sorted(dates) != sorted(set(dates)):
        raise SystemExit("STOP: duplicate date in --dates-file")
    UNIVERSE_ID = universe_id
    DATE_RULE = sorted(dates)
    # r14.1 (G): a later era writes to its OWN artifact directory. Without this, `verify` on the
    # second era would overwrite the starter's committed acceptance.json.
    STATE_DIR = REPO / "reports" / f"universe-{universe_id}"
    return {
        "universe_id": UNIVERSE_ID,
        "date_rule_size": len(DATE_RULE),
        "source": dates_file,
        "state_dir": str(STATE_DIR),
        "starter_state_dir_untouched": str(STARTER_STATE_DIR),
    }


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
    # r14 (performance, byte-identical): every stage below walks the whole store, and at the
    # projected corpus size a bare construction re-hashes hundreds of GB per call.
    return (vault.universe_ledger_for_dataset_dir(d), vault.shard_ledger_for_dataset_dir(d),
            vault.screen_provenance_ledger_for_dataset_dir(d),
            indexed_dataset_store(d, DatasetStore), d)


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
    # r14.1 (G): the §7.6 CONCENTRATION floors bind every era; the exact-80 identity binds only the
    # STARTER tranche. Pre-r14.1 the `pairs != 80` check was unconditional, which made a 105-date
    # era (8 x 105 = 840 pairs) structurally impossible to register at all.
    if date_conc > 0.20 or sym_conc > 0.25:
        raise SystemExit(f"STOP: concentration {date_conc=} {sym_conc=}")
    if len(DATE_RULE) < 10:
        raise SystemExit(f"STOP: {len(DATE_RULE)} dates < the §7.6 minimum of 10")
    if _is_starter() and pairs != STARTER_EXPECTED_PAIRS:
        raise SystemExit(
            f"STOP: the starter tranche's own arithmetic is frozen at {STARTER_EXPECTED_PAIRS} "
            f"pairs; this computes {pairs}"
        )
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


def colliding_registered_pairs(records: list[dict], pairs) -> list:
    """Registered pairs already occupied by SOME dataset -- the §7 pre-registration STOP condition.

    The session date is DERIVED from each record's own ``window_start_utc``. The pre-fix check read
    ``r.get("session_date") or r.get("date")``; neither is a field on a dataset record, so every
    record keyed as ``(symbol, None)``, nothing could ever collide, and a real collision (the legacy
    NVDA 2026-07-08 partial) passed preflight silently. Kept as a pure function so that failure mode
    is testable directly rather than only through the full preflight stage."""
    have = {(r["symbol"], _session_date_of(r)) for r in records}
    return sorted(p for p in pairs if p in have)


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
    expected_pairs = len(SYMBOL_RULE) * len(DATE_RULE)
    if len(pairs) != expected_pairs:
        raise SystemExit(f"STOP: expected {expected_pairs} pairs, universe computes {len(pairs)}")
    if _is_starter() and len(pairs) != STARTER_EXPECTED_PAIRS:
        raise SystemExit(f"STOP: the starter tranche is frozen at {STARTER_EXPECTED_PAIRS} pairs")
    tb.assert_no_exposed_session(universe["date_rule"])
    checks["no_exposed_session_collision"] = True

    existing, errors = store.list()
    checks["dataset_store_readable"] = errors == []
    collisions = colliding_registered_pairs(existing, pairs)
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


#: §12's full-session floor: a J-06 shard covers the whole 09:30-16:00 ET regular session (6.5 h);
#: 6.4 h absorbs a vendor's first/last-print jitter without admitting a partial window.
J06_FULL_SESSION_SECONDS = 6.4 * 3600


def _full_session(record: dict) -> bool:
    from zoneinfo import ZoneInfo
    et = ZoneInfo("America/New_York")
    a = datetime.fromisoformat(record["window_start_utc"].replace("Z", "+00:00")).astimezone(et)
    b = datetime.fromisoformat(record["window_end_utc"].replace("Z", "+00:00")).astimezone(et)
    return (b - a).total_seconds() >= J06_FULL_SESSION_SECONDS


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
    # ``already_recorded`` is permitted ONLY for a dataset that is itself a genuine J-06 shard.
    # Keying on (session_date, symbol) alone let the legacy partial NVDA 2026-07-08 dataset
    # short-circuit the recorder, so a registered pair was silently never recorded.
    existing = _recorded_pairs(store, universe)
    disclosed_positions = vault.disclosed_pool_positions(
        vault.disclosure_incident_ledger_for_dataset_dir(ddir), UNIVERSE_ID)
    outcomes, sealed_now, started = [], 0, time.time()
    cancelled = False
    for n, (symbol, date) in enumerate(pairs, 1):
        if CANCEL_SENTINEL.exists():
            cancelled = True
            sys.stderr.write(f"  cooperative cancel honoured after {n - 1}/{len(pairs)} pairs\n")
            break
        key = (symbol, date)
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
        # belt-and-braces: a disclosed pool position can never take sealed-side credit, even if
        # the HMAC rule would otherwise select it (`assign_shard` refuses independently).
        if key in disclosed_positions:
            continue
        if not vault.compute_seal(secret, symbol, date):
            continue
        if vault._latest_shard_row(shled, existing[key]) is not None:
            continue                     # already sealed by an earlier run -- never double-seal
        # `store.get` re-verifies the dataset's content, so it is read ONLY for a pair that is
        # actually about to be sealed, never once per pair (the store is 22 GB).
        rec = store.get(existing[key])
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


def is_genuine_j06_dataset(record: dict, expected: set) -> bool:
    """The ONE canonical J-06 eligibility test, shared by the recorder walk (§8: what may count as
    ``already_recorded``) and by acceptance (§12: what may count toward the tranche).

    A dataset that merely occupies a registered symbol-day is NOT a J-06 shard. Before the owner's
    repair ruling these were two definitions: the walk keyed only on ``(session_date, symbol)`` and
    so let a legacy partial short-circuit the recorder, while acceptance additionally required the
    recorder's own ``schema_basis``. One predicate, no drift."""
    if record.get("schema_basis") != J06_SCHEMA_BASIS:
        return False
    if (record["symbol"], _session_date_of(record)) not in expected:
        return False
    if not record.get("checksum"):
        return False
    return _full_session(record)


def _recorded_pairs(store: DatasetStore, universe: dict, *, records=None) -> dict:
    """Every registered pair with a genuine J-06 shard, keyed (symbol, date) -> dataset id.

    ``store.list()`` returns healthy records and a separate error list, so membership here already
    means the ``DatasetStore`` record itself read back cleanly."""
    expected = set(vault.expected_recording_pairs(universe))
    out = {}
    for r in (records if records is not None else store.list()[0]):
        if is_genuine_j06_dataset(r, expected):
            out[(r["symbol"], _session_date_of(r))] = r["id"]
    return out


def _legacy_occupying_registered_pairs(store: DatasetStore, universe: dict, *, records=None) -> list:
    """Registered symbol-days occupied by a dataset this recorder did NOT write -- the §7 collision
    condition, surfaced explicitly rather than absorbed into the tranche count."""
    expected = set(vault.expected_recording_pairs(universe))
    out = []
    for r in (records if records is not None else store.list()[0]):
        key = (r["symbol"], _session_date_of(r))
        if key in expected and not is_genuine_j06_dataset(r, expected):
            out.append({"symbol": key[0], "date": key[1], "dataset_id": r["id"],
                        "created_utc": r.get("created_utc"), "schema_basis": r.get("schema_basis")})
    return out


# === §10: the TYPED J-06 batch verifier ==========================================================
#
# The gap this closes. `stage_verify` used to compute `disclosed = expected - recorded` and hand
# that set straight to `vault.verify_recording_batch`. That makes TR-4 vacuous through this path:
# ANY missing pair launders itself into the "disclosed vendor failure" category simply by being
# missing, and the check can then never fail. `verify_recording_batch` is a generic primitive and
# stays exactly as it is -- it validates a batch against a rule net of failures its CALLER vouches
# for. This module is that caller for J-06, so the vouching belongs here, and it must come from
# recorder evidence, never from arithmetic.

#: The typed reasons a registered pair can lack a genuine J-06 shard. Only the first is lawful.
MISSING_VENDOR_FAILURE = "unrecovered_vendor_failure"
MISSING_LEGACY_COLLISION = "legacy_dataset_collision"
MISSING_UNEXPLAINED = "unexplained"


def unrecovered_vendor_failures(runs: list[dict]) -> dict:
    """Pairs whose LAST recorder outcome across every run is a vendor failure, with that run's own
    failure detail as the evidence. A pair re-attempted and later recorded is NOT a failure; a pair
    that was never attempted has no evidence at all and can never appear here."""
    last: dict = {}
    for run in runs:
        for o in run.get("outcomes") or []:
            last[(o["symbol"], o["date"])] = (run.get("at"), o)
    return {pair: {"at": at, "detail": o.get("detail"), "outcome": o.get("outcome")}
            for pair, (at, o) in last.items() if o.get("outcome") == "failed"}


def classify_missing_pairs(expected, recorded, collisions, runs) -> dict:
    """Every registered pair without a genuine J-06 shard, mapped to its TYPED condition.

    A legacy collision DOMINATES: a pair blocked by a pre-existing dataset is a collision even if a
    later run also failed on it, because the collision -- not the vendor -- is why no lawful shard
    exists. That precedence is what makes "a collision may never be converted into a vendor
    failure merely because the pair is missing" structural rather than a naming convention."""
    collided = {(c["symbol"], c["date"]) for c in collisions}
    failures = unrecovered_vendor_failures(runs)
    out = {}
    for pair in sorted(set(expected) - set(recorded)):
        if pair in collided:
            out[pair] = {"condition": MISSING_LEGACY_COLLISION}
        elif pair in failures:
            out[pair] = {"condition": MISSING_VENDOR_FAILURE, "evidence": failures[pair]}
        else:
            out[pair] = {"condition": MISSING_UNEXPLAINED}
    return out


def verify_j06_batch(universe: dict, *, recorded, collisions, runs) -> dict:
    """TR-4 for J-06. Takes NO caller-supplied ``disclosed_failures`` -- that argument is exactly
    the laundering surface, so it is not reachable from here. The disclosed set is DERIVED from
    recorder run evidence and every other missing pair blocks acceptance outright."""
    expected = vault.expected_recording_pairs(universe)
    classified = classify_missing_pairs(expected, recorded, collisions, runs)
    blocking = {p: c for p, c in classified.items() if c["condition"] != MISSING_VENDOR_FAILURE}
    disclosed = sorted(p for p, c in classified.items() if c["condition"] == MISSING_VENDOR_FAILURE)
    result = {
        "verifier": "j06_typed",
        "disclosed_vendor_failures": [list(p) for p in disclosed],
        "blocking_missing_pairs": {f"{s} {d}": c["condition"] for (s, d), c in sorted(blocking.items())},
        "vendor_failure_evidence": {f"{s} {d}": classified[(s, d)]["evidence"] for s, d in disclosed},
    }
    if blocking:
        result["ok"] = False
        result["refusal"] = (
            "TR-4 refused: registered pair(s) lack a genuine J-06 dataset and have no "
            "provenance-backed unrecovered vendor failure permitted by §7.2")
        return result
    result.update(vault.verify_recording_batch(
        universe, recorded=list(recorded), disclosed_failures=disclosed))
    return result


def stage_verify() -> dict:
    """§10 batch verification (TR-4) + §12 acceptance, computed from the CANONICAL stores."""
    from collections import Counter

    uled, shled, sled, store, ddir = _ledgers()
    universe = vault.find_universe(uled, UNIVERSE_ID)
    records, errors = store.list()
    by_id = {r["id"]: r for r in records}
    expected = sorted(vault.expected_recording_pairs(universe))
    recorded = _recorded_pairs(store, universe, records=records)
    collisions = _legacy_occupying_registered_pairs(store, universe, records=records)
    runs = json.loads((STATE_DIR / "recording-runs.json").read_text())["runs"]

    # --- TR-4, through the TYPED J-06 verifier (never set subtraction) ------------------------
    tr4 = verify_j06_batch(universe, recorded=recorded, collisions=collisions, runs=runs)
    disclosed = [tuple(p) for p in tr4["disclosed_vendor_failures"]]

    secret = vault.load_vault_secret()
    hmac_selected = [p for p in expected if vault.compute_seal(secret, *p)]
    shard_rows = shled.verified_rows()
    tracked_ids = {r["dataset_id"] for r in shard_rows if r.get("dataset_id")}
    sealed_ids = {r["dataset_id"] for r in shard_rows
                  if r.get("exposure_state") == vault.STATE_SEALED and r.get("dataset_id")}
    dled = vault.disclosure_incident_ledger_for_dataset_dir(ddir)
    disclosed_positions = vault.disclosed_pool_positions(dled, UNIVERSE_ID)
    selected_recorded = [p for p in hmac_selected if p in recorded]
    sealed_selected = [p for p in selected_recorded if recorded[p] in sealed_ids]

    dates = sorted({d for _s, d in recorded})
    symbols = sorted({s for s, _d in recorded})
    n = len(recorded)
    date_conc = max(Counter(d for _s, d in recorded).values()) / n
    sym_conc = max(Counter(s for s, _d in recorded).values()) / n
    new = [by_id[i] for i in recorded.values()]
    full = sum(1 for r in new if _full_session(r))
    d0 = datetime.fromisoformat(dates[0]).date(); d1 = datetime.fromisoformat(dates[-1]).date()

    out = {
        "stage": "acceptance", "universe_id": UNIVERSE_ID, "at": _utc(),
        "planned_pairs": len(expected), "recorded_pairs": n,
        "unrecovered_disclosed_vendor_failures": [list(p) for p in disclosed],
        "tr4_batch_verification": tr4,
        "legacy_collisions_present": len(collisions),
        "legacy_collisions_counted_as_j06": 0,
        "legacy_collisions_excluded_from_tranche": collisions,
        "genuine_j06_recorded_pairs": len(recorded),
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
        "preservation_capability_present": all(
            r.get("schema_basis") == J06_SCHEMA_BASIS for r in new),
        "quote_size_unit_present": all(r.get("quote_size_unit") for r in new),
        "hmac_selected_total": len(hmac_selected),
        "hmac_selected_recorded": len(selected_recorded),
        "sealed_shard_rows": len(sealed_ids),
        "sealed_of_selected_recorded": len(sealed_selected),
        "unsealed_selected_recorded": [list(p) for p in selected_recorded if p not in sealed_selected],
        "universe_registrations": len([r for r in uled.verified_rows()
                                       if r.get("universe_id") == UNIVERSE_ID]),
        # the §7 same-universe invariants, read back from the ledger itself rather than from the
        # registration artifact, so a rewritten artifact could not fake them
        "registered_at": universe["registered_at"],
        "rule_hash": universe["rule_hash"],
        "rule_commitment": universe["rule_commitment"],
        "vault_secret_commitment": universe["vault_secret_commitment"],
        "configured_secret_matches_registered_commitment":
            universe["vault_secret_commitment"] == vault.commit_vault_secret(secret),
        "symbol_rule_unchanged": universe["symbol_rule"] == SYMBOL_RULE,
        "date_rule_unchanged": universe["date_rule"] == DATE_RULE,
        "screen_provenance_bound": vault.find_screen_provenance(sled, SCREEN_ID) is not None,
        "screening_acts": len(sled.verified_rows()),
        "disclosure_incidents": len(dled.verified_rows()),
        "disclosed_positions": len(disclosed_positions),
        "disclosed_positions_with_any_shard_row": len(
            [p for p in disclosed_positions if p in recorded and recorded[p] in tracked_ids]),
        "disclosure_ledger_chain_ok": dled.verify_chain()["ok"],
        "universe_ledger_chain_ok": uled.verify_chain()["ok"],
        "shard_ledger_chain_ok": shled.verify_chain()["ok"],
        "screen_provenance_chain_ok": sled.verify_chain()["ok"],
        "duplicate_dataset_ids": len(recorded) - len(set(recorded.values())),
        "duplicate_seal_rows": len([r for r in shard_rows
                                    if r.get("exposure_state") == vault.STATE_SEALED])
                               - len(sealed_ids),
        "legacy_dataset_ids_with_shard_rows": len(
            {c["dataset_id"] for c in collisions} & tracked_ids),
        "recording_runs": len(runs),
        "cooperative_cancel_observed": any(r["cancelled_cooperatively"] for r in runs),
        "legacy_datasets_untouched": len(records) - n,
        "research_gate_150_symbol_days": {"have": n, "target": 150, "met": n >= 150},
    }
    _write("acceptance.json", out)
    return out


# === the pool-position disclosure incident + its TR-2 re-analysis =================================

DISCLOSURE_INCIDENT_ID = "j06-operator-report-pool-position-2026-08-22"
#: The operator report that made the disclosure, located in this session's own transcript.
DISCLOSURE_PROVENANCE = {
    "channel": "operator report (assistant turn, Claude Code session)",
    "session_id": "10421d4e-9e80-4737-b7d7-02a38eafa132",
    "message_uuid": "d3ee23a0-2996-48bd-8851-d92745c2eecd",
    "occurred_at": "2026-08-22T00:55:23Z",
    "quoted_text": "NVDA 2026-07-08 is not HMAC-selected, so nothing legacy was ever sealed",
}
DISCLOSED_PAIRS = [("NVDA", "2026-07-08")]


def stage_disclosure() -> dict:
    """Records the named, immutable pool-position disclosure incident.

    The §14 operator report stated in plain text that one registered pair is NOT HMAC-selected.
    That is a real leak of one bit of the hidden partition, and it has already happened -- so it is
    recorded as an incident rather than glossed. It is a NON-sealed-side disclosure: no sealed
    member's identity was revealed, and no second member is disclosed to "balance" it."""
    uled, shled, _sled, store, ddir = _ledgers()
    if vault.find_universe(uled, UNIVERSE_ID) is None:
        raise SystemExit("STOP: no registered universe")
    dled = vault.disclosure_incident_ledger_for_dataset_dir(ddir)
    row = vault.record_disclosure_incident(
        dled,
        incident_id=DISCLOSURE_INCIDENT_ID,
        disclosure_type=vault.DISCLOSURE_NON_SEALED_POOL_POSITION,
        universe_id=UNIVERSE_ID,
        pairs=DISCLOSED_PAIRS,
        source="operator report to the owner (see provenance)",
        occurred_at=DISCLOSURE_PROVENANCE["occurred_at"],
        sealed_member_identity_disclosed=False,
        evidence_consequence=(
            "PERMANENT. The disclosed pool position may never receive sealed, blind or "
            "historical_oos credit: `vault.assign_shard` refuses it for the lifetime of this vault "
            "directory, and the J-06 recorder walk refuses to seal it. Its dataset remains a "
            "lawful member of the recorded tranche for corpus-size and coverage purposes only."),
        provenance=DISCLOSURE_PROVENANCE,
    )
    # the consequence is proven against the REAL ledgers, not asserted in prose: the pair is in the
    # set `assign_shard` reads, and no dataset at that pair carries any shard-lifecycle row at all.
    disclosed = vault.disclosed_pool_positions(dled, UNIVERSE_ID)
    records, _errors = store.list()
    tracked = {r["dataset_id"] for r in shled.verified_rows() if r.get("dataset_id")}
    proof = {}
    for pair in DISCLOSED_PAIRS:
        at_pair = [r["id"] for r in records
                   if (r["symbol"], _session_date_of(r)) == pair]
        proof[f"{pair[0]} {pair[1]}"] = {
            "in_disclosure_ledger_assign_shard_reads": pair in disclosed,
            "datasets_at_this_pair": len(at_pair),
            "shard_lifecycle_rows_for_those_datasets": len(set(at_pair) & tracked),
        }
    out = {"stage": "pool_position_disclosure", "incident_id": DISCLOSURE_INCIDENT_ID,
           "row_index": row.get("row_index"), "disclosed_positions": len(disclosed),
           "sealed_member_identity_disclosed": False,
           "chain_ok": dled.verify_chain()["ok"], "refusal_proof": proof, "at": _utc()}
    _write("pool-position-disclosure.json", out)
    return out


def residual_pool_uncertainty(
    universe_pairs: int, selected_count: int, disclosed_non_selected: int, exposed_count: int = 0
) -> dict:
    """The attacker's residual candidate space for the hidden HMAC partition, given the registered
    universe size, the publicly published selected COUNT, and however many pool positions have been
    disclosed as non-selected.

    Certainty arrives in exactly two ways, and both are computed rather than assumed: the unknown
    positions shrink to the number still selected (the whole hidden set is then pinned), or fewer
    than two candidate identities remain for a shard. Pure arithmetic, so the non-vacuity
    counter-case (disclose enough positions and certainty DOES arrive) is testable."""
    from math import comb

    unknown = universe_pairs - disclosed_non_selected
    still_unexposed = selected_count - exposed_count
    determined = unknown == selected_count
    return {
        "universe_pairs": universe_pairs,
        "publicly_published_selected_count": selected_count,
        "disclosed_non_selected_positions": disclosed_non_selected,
        "unknown_positions": unknown,
        "still_unexposed_selected_shards": still_unexposed,
        "feasible_selection_assignments": comb(unknown, selected_count) if unknown >= selected_count else 0,
        "candidate_identities_per_unexposed_selected_shard": unknown,
        "hidden_set_fully_determined": determined,
        "any_identity_certain": determined or unknown < 2,
    }


RECORDING_RUNS_PATH = STATE_DIR / "recording-runs.json"


def _load_recording_runs(path: Path = RECORDING_RUNS_PATH) -> list[dict]:
    """The committed §8 run ledger (``reports/j06-tranche/recording-runs.json``) -- read-only,
    never written by this stage (record-integrity: iteration 24 narrows what is SERVED going
    forward, it does not retroactively edit a committed operator report)."""
    return json.loads(path.read_text())["runs"]


def residual_pool_uncertainty_by_run_time_bucket(
    runs: list[dict], served_sealed_at_values: list[str]
) -> dict:
    """The RUN-AWARE half of TR-2 (iteration 24, closing the sealing-time leak the iter-23 audit
    found): the combinatorial half above never reads ``recording-runs.json`` at all, so a channel
    that joins the committed per-run ``sealed_this_run`` counts against the SERVED per-shard
    ``sealed_at`` values was a genuine blind spot -- a future run could narrow a still-sealed
    shard's identity through this join without the automated check ever seeing it.

    Deliberately generic over whatever PRECISION ``served_sealed_at_values`` carries -- it buckets
    both sides by that precision (a run's own ``at`` timestamp truncated to the same length),
    rather than hardcoding "date-only". Fed the REAL, now-coarsened (date-only) served values, every
    run sealed on the same calendar day collapses into ONE bucket, so the residual candidate count
    per bucket is the number of still-currently-sealed shards sharing that day -- today, all 21 fall
    on one day, so the floor comfortably holds. Fed any full-precision reproduction of the OLD
    served shape instead (the iter-24 non-vacuity counter-tests), the same logic instead separates
    the runs from each other -- and since each shard's own seal instant is distinct at that
    precision, every bucket collapses to a candidate count of 1, correctly BELOW the floor.

    Asserted against the SAME existing floor ``residual_pool_uncertainty`` already enforces
    (``candidate_identities_per_unexposed_selected_shard >= 2``) -- no new floor number invented
    here."""
    if not served_sealed_at_values:
        return {"buckets": {}, "any_bucket_below_floor": False, "worst_bucket_candidates": None}

    bucket_len = len(served_sealed_at_values[0])
    run_sealed_by_bucket: dict[str, int] = {}
    for run in runs:
        key = str(run.get("at", ""))[:bucket_len]
        run_sealed_by_bucket[key] = run_sealed_by_bucket.get(key, 0) + int(run.get("sealed_this_run", 0))

    served_by_bucket: dict[str, int] = {}
    for value in served_sealed_at_values:
        served_by_bucket[value] = served_by_bucket.get(value, 0) + 1

    # Iterate the SERVED buckets, not the run buckets (iteration-24 audit finding B1). The
    # attacker's starting point is a served `sealed_at` value, so EVERY served value must sit in an
    # anonymity set of >= 2 -- including one that no run's own bucket claims. Walking the run
    # buckets instead (and skipping a bucket with `run_sealed_count <= 0`) made the check silently
    # blind at fine precision: a run's `at` is stamped at the END of the run by `_utc()`
    # (second precision) while each shard's `sealed_at` is stamped per-seal by `vault._iso_utc_now`
    # (microsecond precision), so at full precision NO served value ever prefix-equals a run key,
    # every bucket was skipped, and the check reported "safe" against exactly the leak it exists to
    # catch. Keyed on the served value, the same fine precision instead gives each shard its own
    # bucket of 1 -- correctly BELOW the floor. `sealed_this_run_total` stays in the record (0 when
    # no run claims the bucket, itself a finding worth reading) but never gates.
    buckets = {}
    for key, served_count in served_by_bucket.items():
        buckets[key] = {
            "sealed_this_run_total": run_sealed_by_bucket.get(key, 0),
            "currently_sealed_served_count": served_count,
            "candidate_identities_per_unexposed_selected_shard": served_count,
        }
    candidate_counts = [b["candidate_identities_per_unexposed_selected_shard"] for b in buckets.values()]
    return {
        "buckets": buckets,
        "any_bucket_below_floor": any(c < 2 for c in candidate_counts),
        "worst_bucket_candidates": min(candidate_counts) if candidate_counts else None,
    }


def stage_tr2() -> dict:
    """TR-2 re-run with the disclosure treated as attacker-known public information.

    Three independent halves, because the leak has three shapes:

    (1) COMBINATORIAL. The attacker knows the registered universe (80 pairs), the publicly
        published selected COUNT, and now that one specific position is non-selected. Certainty
        about any still-unexposed selected shard requires the residual candidate space to collapse
        -- either the unknown positions shrink to exactly the remaining selected count (the whole
        hidden set is then determined), or some position becomes the unique candidate for a given
        sealed row. Both are computed here, not asserted.

    (2) OBSERVATIONAL. Every genuine J-06 dataset must still be withheld from the served surfaces
        by the shared opaque-pool predicate, so no listing can be differenced against the universe.

    (3) RUN-AWARE (iteration 24). The committed per-run ``sealed_this_run`` counts
        (``reports/j06-tranche/recording-runs.json``) joined against the SERVED per-shard
        ``sealed_at`` values -- the channel (1) and (2) do not model at all. See
        ``residual_pool_uncertainty_by_run_time_bucket`` above.
    """
    uled, shled, _sled, store, ddir = _ledgers()
    universe = vault.find_universe(uled, UNIVERSE_ID)
    secret = vault.load_vault_secret()
    expected = sorted(vault.expected_recording_pairs(universe))
    selected = [p for p in expected if vault.compute_seal(secret, *p)]
    dled = vault.disclosure_incident_ledger_for_dataset_dir(ddir)
    disclosed = vault.disclosed_pool_positions(dled, UNIVERSE_ID)

    # a disclosed position that turned out to BE selected would be a graver, different incident
    wrongly = [p for p in disclosed if p in set(selected)]
    if wrongly:
        raise SystemExit("STOP: a disclosed position is HMAC-SELECTED -- that is a sealed-member "
                         "identity leak, which this model has no lawful containment for")

    exposed_rows = [r for r in shled.verified_rows()
                    if r.get("universe_id") == UNIVERSE_ID
                    and r.get("exposure_state") == vault.STATE_EXPOSED]
    combinatorial = residual_pool_uncertainty(
        len(expected), len(selected), len(disclosed), len(exposed_rows))

    # --- (2) the observational half, against the REAL store ------------------------------------
    records, _errors = store.list()
    by_id = {r["id"]: r for r in records}
    recorded = _recorded_pairs(store, universe, records=records)
    tuples = [(r["id"], r["symbol"], _session_date_of(r), r.get("created_utc") or "")
              for r in records]
    withheld = vault.unresolved_pool_dataset_ids(shled, uled, tuples)
    j06_ids = set(recorded.values())
    served_j06 = sorted(j06_ids - set(withheld))
    observational = {
        "genuine_j06_datasets": len(j06_ids),
        "withheld_from_served_surfaces": len(j06_ids & set(withheld)),
        "leaked_to_served_surfaces": len(served_j06),
        # Pre-registration legacy datasets stay visible BY DESIGN (`created_utc >= registered_at`
        # guard): they existed before the universe did, so their visibility cannot be differenced
        # against it. Counted, so the number is on the record rather than implied.
        "legacy_datasets_visible_by_design": len(by_id) - len(withheld),
    }

    # --- (3) the run-aware half, against the REAL committed run report + REAL served state -------
    runs = _load_recording_runs()
    served_state = vault.build_vault_state(shled, uled)
    served_sealed_at_values = [
        entry["sealed_at"] for entry in served_state["shards"]
        if entry.get("universe_id") == UNIVERSE_ID
        and entry.get("exposure_state") == vault.STATE_SEALED
    ]
    run_aware = residual_pool_uncertainty_by_run_time_bucket(runs, served_sealed_at_values)

    ok = (not combinatorial["any_identity_certain"]
          and combinatorial["candidate_identities_per_unexposed_selected_shard"] >= 2
          and observational["leaked_to_served_surfaces"] == 0
          and not run_aware["any_bucket_below_floor"])
    out = {"stage": "tr2_disclosure_analysis", "universe_id": UNIVERSE_ID, "at": _utc(),
           "attacker_knowledge": [
               "the registered universe rule (8 symbols x 10 dates = 80 pairs)",
               "every served/public artifact, including the published selected COUNT",
               "the legacy-dataset collision at one registered pair",
               f"the disclosed non-selected pool position(s): {len(disclosed)}",
               "readiness / dataset / run / UI / MCP surfaces",
               "the committed per-run sealed_this_run counts, joined against served sealed_at"],
           "combinatorial": combinatorial, "observational": observational, "run_aware": run_aware,
           "no_identity_determinable_with_certainty": ok}
    _write("tr2-disclosure-analysis.json", out)
    if not ok:
        raise SystemExit(f"STOP: TR-2 fails under the disclosure: {json.dumps(out)}")
    return out


# === r14.1 (H) -- the four operator acts r14 built primitives for but never exposed ================
#
# Every one is DRY BY DEFAULT and requires an explicit `--commit` to write. A real campaign should
# never need Python-console ceremony to perform a ledgered act, and a dry run must be able to show
# exactly what a commit would do without doing it.

#: Extra per-invocation arguments the r14.1 stages read (set by `main`).
CORPUS_ID: str | None = None
PROBE_DATE: str | None = None
PROBE_NOTE: str = ""
COMMIT: bool = False


def _exposure_registry():
    from app.research.micro_accessor import (
        ExposureRegistry,
        resolve_micro_exposure_registry_dir,
    )

    return ExposureRegistry(resolve_micro_exposure_registry_dir(CONFIG.dataset_dir_resolved()))


def _require_commit(act: str, payload: dict) -> dict:
    """Dry-run gate. A stage computes everything, reports what it WOULD do, and writes only when
    the operator passed `--commit` -- so a preflight is always available and never a side effect."""
    if not COMMIT:
        return {**payload, "committed": False, "note": f"DRY RUN -- pass --commit to {act}"}
    return {**payload, "committed": True}


def stage_corpus_era() -> dict:
    """r14.1: bind a fresh corpus era to this universe (structured provenance, §6.7)."""
    from app.research import micro_corpus as mc

    if not CORPUS_ID:
        raise SystemExit("STOP: --corpus-id is required for the corpus-era stage")
    uled, _sled, _pled, _store, _d = _ledgers()
    universe = vault.find_universe(uled, UNIVERSE_ID)
    if universe is None:
        raise SystemExit(f"STOP: universe {UNIVERSE_ID!r} is not registered")
    payload = {
        "stage": "corpus_era",
        "at": _utc(),
        "corpus_id": CORPUS_ID,
        "universe_id": UNIVERSE_ID,
        "universe_registered_at": universe["registered_at"],
        "rule_commitment": universe["rule_commitment"],
        "expected_pair_count": len(vault.expected_recording_pairs(universe)),
        "freshness_boundary": universe["registered_at"],
    }
    out = _require_commit("register the corpus era", payload)
    if out["committed"]:
        row = mc.register_bound_corpus_era(
            _exposure_registry(), uled,
            corpus_id=CORPUS_ID, universe_id=UNIVERSE_ID, registered_at=_utc(),
            provenance_note="registered by scripts.j06_operator corpus-era",
        )
        out["row_index"] = row["row_index"]
    _write("corpus-era.json", out)
    return out


def stage_release_plan() -> dict:
    """r14.1: derive and COMMIT the universe's frozen release plan, before any release."""
    uled, sled, _pled, _store, d = _ledgers()
    universe = vault.find_universe(uled, UNIVERSE_ID)
    if universe is None:
        raise SystemExit(f"STOP: universe {UNIVERSE_ID!r} is not registered")
    secret = vault.load_vault_secret()
    incidents = vault.disclosure_incident_ledger_for_dataset_dir(d)
    plan_ledger = vault.release_plan_ledger_for_dataset_dir(d)
    plan = vault.build_release_plan(universe, incidents, secret)
    # SIZES only -- publishing which position is the decoy would itself be a §7.2.2 disclosure.
    payload = {
        "stage": "release_plan",
        "at": _utc(),
        "universe_id": UNIVERSE_ID,
        "rule": plan["rule"],
        "plan_hash": plan["plan_hash"],
        "universe_pairs": plan["universe_pairs"],
        "sealed_path_size": len(plan["sealed_path"]),
        "barred_size": len(plan["barred"]),
        "reserved_decoy_size": len(plan["reserved_decoy"]),
        "releasable_size": len(plan["releasable"]),
        "already_committed": vault.find_release_plan_commitment(plan_ledger, UNIVERSE_ID) is not None,
    }
    out = _require_commit("commit the release plan", payload)
    if out["committed"]:
        row = vault.commit_release_plan(plan_ledger, plan, committed_at=_utc())
        out["plan_commitment"] = row["plan_commitment"]
    _write("release-plan.json", out)
    return out


def stage_release() -> dict:
    """r14.1: release every plan-releasable member that has a genuine dataset in this store."""
    from app.research import micro_corpus as mc  # noqa: F401 -- symmetry with the other stages

    uled, sled, _pled, store, d = _ledgers()
    universe = vault.find_universe(uled, UNIVERSE_ID)
    if universe is None:
        raise SystemExit(f"STOP: universe {UNIVERSE_ID!r} is not registered")
    secret = vault.load_vault_secret()
    incidents = vault.disclosure_incident_ledger_for_dataset_dir(d)
    plan_ledger = vault.release_plan_ledger_for_dataset_dir(d)
    if vault.find_release_plan_commitment(plan_ledger, UNIVERSE_ID) is None:
        raise SystemExit("STOP: commit the release plan first (stage release-plan --commit)")
    plan = vault.build_release_plan(universe, incidents, secret)
    releasable = {tuple(p) for p in plan["releasable"]}

    records, _errors = store.list()
    candidates = []
    for meta in records:
        session_date = vault._et_session_date_of(meta["window_start_utc"])
        if (vault._normalize_symbol(meta["symbol"]), session_date) not in releasable:
            continue
        if meta.get("schema_basis") != vault.RECORDER_SCHEMA_BASIS:
            continue
        if meta.get("created_utc", "") < universe["registered_at"]:
            continue
        candidates.append(meta["id"])

    payload = {
        "stage": "release",
        "at": _utc(),
        "universe_id": UNIVERSE_ID,
        "plan_hash": plan["plan_hash"],
        "releasable_positions": len(releasable),
        "datasets_eligible_now": len(candidates),
        "reserved_decoy_size": len(plan["reserved_decoy"]),
    }
    out = _require_commit("release the eligible members", payload)
    if out["committed"]:
        released, refused = 0, []
        for dataset_id in sorted(candidates):
            try:
                vault.release_unselected_dataset(
                    store, sled, uled, incidents, plan_ledger,
                    dataset_id=dataset_id, universe_id=UNIVERSE_ID,
                    vault_secret=secret, released_at=_utc(),
                )
                released += 1
            except Exception as exc:  # disclosed, already-rowed, decoy: reported, never silent
                refused.append({"dataset_id": dataset_id, "refusal": type(exc).__name__})
        out["released"] = released
        out["refused"] = refused
    _write("release.json", out)
    return out


def stage_probe() -> dict:
    """r14.1: log a retention/availability probe as the SACRIFICIAL exposure it actually is."""
    from app.research import walkforward as wf

    if not CORPUS_ID or not PROBE_DATE:
        raise SystemExit("STOP: --corpus-id and --probe-date are both required for the probe stage")
    payload = {
        "stage": "retention_probe_exposure",
        "at": _utc(),
        "corpus_id": CORPUS_ID,
        "session_date": PROBE_DATE,
        "note": PROBE_NOTE,
        "consequence": (
            "PERMANENT: a tick fetch READS this date's tape, so the date is exposed from this "
            "instant and can never afterwards carry historical_oos evidence for this corpus."
        ),
    }
    out = _require_commit("burn this date as a sacrificial probe", payload)
    if out["committed"]:
        row = wf.record_sacrificial_probe_exposure(
            _exposure_registry(), corpus_id=CORPUS_ID, session_date=PROBE_DATE,
            logged_at=_utc(), note=PROBE_NOTE,
        )
        out["row_index"] = row["row_index"]
    _write("retention-probe.json", out)
    return out


_STAGES = {"provenance": stage_provenance, "register": stage_register,
           "preflight": stage_preflight, "record": stage_record,
           "bars": stage_bars, "verify": stage_verify,
           "disclosure": stage_disclosure, "tr2": stage_tr2,
           # r14.1 (H): the four acts r14 left as library-only primitives.
           "corpus-era": stage_corpus_era, "release-plan": stage_release_plan,
           "release": stage_release, "probe": stage_probe}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in _STAGES:
        print(
            f"usage: python -m scripts.j06_operator {{{'|'.join(_STAGES)}}} "
            "[--universe-id ID --dates-file PATH] [--corpus-id ID] "
            "[--probe-date YYYY-MM-DD] [--probe-note TEXT] [--commit]"
        )
        return 2
    global CORPUS_ID, PROBE_DATE, PROBE_NOTE, COMMIT
    stage = sys.argv[1]
    rest = sys.argv[2:]
    universe_id = dates_file = None
    while rest:
        flag = rest.pop(0)
        if flag == "--universe-id" and rest:
            universe_id = rest.pop(0)
        elif flag == "--dates-file" and rest:
            dates_file = rest.pop(0)
        elif flag == "--corpus-id" and rest:
            CORPUS_ID = rest.pop(0)
        elif flag == "--probe-date" and rest:
            PROBE_DATE = rest.pop(0)
        elif flag == "--probe-note" and rest:
            PROBE_NOTE = rest.pop(0)
        elif flag == "--commit":
            COMMIT = True
        else:
            print(f"unknown argument {flag!r}")
            return 2
    selected = _select_universe(universe_id, dates_file)
    out = _STAGES[stage]()
    if selected["source"] != "starter":
        out = {**out, "universe_selection": selected}
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
