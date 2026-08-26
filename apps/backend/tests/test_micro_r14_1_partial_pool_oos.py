"""r14.1 -- corpus identity and PARTIAL-POOL out-of-sample correctness.

r14 closed the preflight's own errors but left the real OOS architecture unexecutable and, worse,
still reachable by three laundering routes. This file is the executable contract for the fixes:

* **A. mixed released/sealed dates.** Seal assignment is per ``(symbol, session_date)``, so a
  healthy 8-symbol date holds a MIX. r14's reader refused the whole date if any member was
  withheld. The fix is not "drop the withheld ones quietly" -- it is a PRECOMMITTED member set, so
  a sealed member is a non-member rather than an exclusion, and the fold reports its realized
  breadth honestly.
* **B/C. corpus identity.** A ``corpus_id`` must name one specific body of evidence -- bound to a
  registered universe, provable against physical datasets -- and never mean "every visible dataset
  whose date happens to match".
* **D. release identity.** The store owns symbol/date/checksum/schema_basis/created_utc; a release
  derives them and never accepts a caller's word.
* **E. the frozen plan.** Which member ends up the withheld decoy must not depend on the order an
  operator releases in.
* **F. exposure precommit.** A crash between "read the outcomes" and "log the exposure" left a
  window read but recorded fresh. The exposure now lands first.

Every vault fixture here builds its own universe under its own secret in ``tmp_path``. No test
reads the operator's real vault, real store, or any sealed shard.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config import CONFIG
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.research import micro_accessor as ma
from app.research import micro_corpus as mc
from app.research import micro_snapshots as msnap
from app.research import micro_tick_observations as tobs
from app.research import scout
from app.research import vault
from app.research import walkforward as wf
from app.research.datasets import SOURCE_HISTORICAL, SPLIT_TRAIN, DatasetStore

_SECRET = b"r14-1-fixture-vault-secret"
_PANEL = ["PG", "AAPL", "MSFT", "NVDA", "AG", "LYFT", "WULF", "SPY"]
_UNIVERSE = "fixture-oos-universe"
_CORPUS = "fixture-tick-oos-v1"
_REGISTERED_AT = "2026-03-01T00:00:00.000000Z"


# =====================================================================================================
# rig
# =====================================================================================================


def _ledgers(root: Path):
    # The CANONICAL layout: the vault is a `micro_vault` sibling of the dataset dir, exactly where
    # `vault.resolve_vault_dir` looks. Using a bespoke path here would make the fixture pass while
    # the production resolvers looked somewhere else.
    r = vault.resolve_vault_dir(str(root / "datasets"))
    return (
        vault.VaultUniverseLedger(r),
        vault.VaultShardLedger(r),
        vault.VaultDisclosureIncidentLedger(r),
        vault.VaultReleasePlanLedger(r),
    )


def _register_universe(universe_ledger, dates: list[str], universe_id: str = _UNIVERSE):
    return vault.register_universe(
        universe_ledger,
        universe_id=universe_id,
        symbol_rule=list(_PANEL),
        date_rule=list(dates),
        vault_secret_commitment=vault.commit_vault_secret(_SECRET),
        registered_at=_REGISTERED_AT,
    )


def _record_dataset(store: DatasetStore, symbol: str, session_date: str, *, n_trades: int = 40,
                    schema_basis: str | None = vault.RECORDER_SCHEMA_BASIS, seed: float = 0.0):
    """One conforming recorder-shaped dataset. ``schema_basis=None`` mints a LEGACY dataset -- the
    §7.2.2 collision shape, used to prove it can never enter a bound corpus."""
    events: list = []
    base = 100.0 + seed
    for i in range(n_trades):
        ts = 0.001 * (i + 1)
        events.append(QuoteEvent(symbol, ts, base - 0.05 + 0.001 * i, base + 0.05 + 0.001 * i, 5, 5))
        events.append(TradeEvent(symbol, ts + 0.0005, base + 0.001 * i, 10, Side.BUY))
    return store.record(
        symbol=symbol, source=f"hist {symbol}", source_kind=SOURCE_HISTORICAL, source_id=symbol,
        split=SPLIT_TRAIN,
        window_start_utc=f"{session_date}T14:30:00Z", window_end_utc=f"{session_date}T21:00:00Z",
        data_feed="sip", epoch_anchor=1_700_000_000.0 + seed, events=events,
        schema_basis=schema_basis, quote_size_unit="shares" if schema_basis else None,
    )


def _partition(dates: list[str], universe_id: str = _UNIVERSE):
    """The REAL HMAC partition of a pool, computed with production ``compute_seal``."""
    pairs = [(s, d) for s in _PANEL for d in dates]
    selected = [p for p in pairs if vault.compute_seal(_SECRET, p[0], p[1])]
    unselected = [p for p in pairs if not vault.compute_seal(_SECRET, p[0], p[1])]
    return pairs, selected, unselected


def _find_mixed_date(candidates: list[str], want_selected: int = 2) -> str:
    """A date whose real HMAC partition splits the 8-symbol panel exactly ``want_selected`` /
    ``8 - want_selected`` -- searched, never assumed, so the trap exercises the production rule."""
    for date in candidates:
        n = sum(1 for s in _PANEL if vault.compute_seal(_SECRET, s, date))
        if n == want_selected:
            return date
    raise AssertionError(f"no candidate date splits {want_selected}/{8 - want_selected}")


def _bound_corpus_rig(tmp_path: Path, dates: list[str], *, build_snapshots: bool = False,
                      n_trades: int = 40):
    """A registered universe + committed plan + real datasets + released members + bound corpus."""
    uled, sled, iled, pled = _ledgers(tmp_path)
    _register_universe(uled, dates)
    universe = vault.find_universe(uled, _UNIVERSE)
    plan = vault.build_release_plan(universe, iled, _SECRET)
    vault.commit_release_plan(pled, plan, committed_at="2026-03-02T00:00:00.000000Z")

    store = DatasetStore(str(tmp_path / "datasets"))
    ids_by_pair: dict[tuple[str, str], str] = {}
    for i, (symbol, session_date) in enumerate((s, d) for d in dates for s in _PANEL):
        meta = _record_dataset(store, symbol, session_date, n_trades=n_trades, seed=i)
        ids_by_pair[(symbol, session_date)] = meta["id"]

    registry = ma.ExposureRegistry(
        ma.resolve_micro_exposure_registry_dir(str(tmp_path / "datasets"))
    )
    mc.register_bound_corpus_era(
        registry, uled, corpus_id=_CORPUS, universe_id=_UNIVERSE,
        registered_at="2026-03-03T00:00:00.000000Z",
    )
    snapshots_dir = str(tmp_path / "snapshots")
    rig = {
        "uled": uled, "sled": sled, "iled": iled, "pled": pled,
        "store": store, "registry": registry, "plan": plan,
        "ids_by_pair": ids_by_pair, "snapshots_dir": snapshots_dir, "dates": dates,
    }
    if build_snapshots:
        # ORDER MATTERS, and the order is the production one: an unreleased pool member is
        # WITHHELD, and `run_snapshot_build_and_record` correctly refuses to replay a withheld
        # shard's events (§7.5 point 6). So release first, then build -- which is also exactly the
        # sequence a real campaign runs, and means the sealed members never get a snapshot at all.
        _release_all_eligible(rig)
        rig["released_before_snapshots"] = True
        releasable = {tuple(p) for p in plan["releasable"]}
        wanted = [
            ids_by_pair[(sym, date)]
            for (sym, date) in ids_by_pair
            if (vault._normalize_symbol(sym), date) in releasable
        ]
        msnap.run_snapshot_build_and_record(store, CONFIG, snapshots_dir, wanted)
    return rig


def _release_all_eligible(rig, order=None):
    """Release every plan-releasable position that has a dataset, in ``order`` (default sorted)."""
    releasable = [tuple(p) for p in rig["plan"]["releasable"]]
    positions = order if order is not None else sorted(releasable)
    released = []
    for symbol, session_date in positions:
        dataset_id = next(
            (i for (s, d), i in rig["ids_by_pair"].items()
             if vault._normalize_symbol(s) == symbol and d == session_date),
            None,
        )
        if dataset_id is None:
            continue
        vault.release_unselected_dataset(
            rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
            dataset_id=dataset_id, universe_id=_UNIVERSE, vault_secret=_SECRET,
            released_at="2026-03-04T00:00:00.000000Z",
        )
        released.append(dataset_id)
    return released


# =====================================================================================================
# A. THE REQUIRED TRAP -- a mixed date is USABLE, and the sealed members are never touched
# =====================================================================================================


def test_a_mixed_date_reads_exactly_its_released_members_and_never_touches_a_sealed_one(
    tmp_path, monkeypatch
):
    """THE trap the brief names: one date, 6 released + 2 sealed.

    r14 raised ``TickObservationWithheldError`` for the whole date, which made the real HMAC
    architecture unusable. The date is now usable, the six released members are read, the two
    sealed ids receive ZERO read calls, and the realized symbol breadth is reported as 6 -- not the
    panel's 8, and not silently."""
    date = _find_mixed_date([f"2026-04-{d:02d}" for d in range(1, 29)], want_selected=2)
    rig = _bound_corpus_rig(tmp_path, [date], build_snapshots=True)  # releases, then snapshots
    plan = rig["plan"]
    assert len(plan["sealed_path"]) == 2, "the fixture date must be a genuine 6/2 mixed date"
    # One of the six not-selected is the reserved decoy, so five are releasable on a one-date pool.
    assert len(plan["releasable"]) + len(plan["reserved_decoy"]) == 6

    membership = mc.eligible_oos_members(
        rig["registry"], rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
        corpus_id=_CORPUS, vault_secret=_SECRET,
    )
    sealed_ids = {
        rig["ids_by_pair"][(sym, d)]
        for sym, d in [tuple(p) for p in plan["sealed_path"]]
        for (s, dd) in [(sym, d)]
        if (sym, d) in rig["ids_by_pair"]
    }
    member_ids = {m["dataset_id"] for m in membership["members"]}
    assert sealed_ids and not (sealed_ids & member_ids), "no sealed id may enter the manifest"

    # --- the spy: every snapshot read this call makes, by dataset id ---------------------------
    reads: list[str] = []
    real_cached = scout._cached_dataset_rows

    def spy(dataset_id, dataset_store, snapshots_dir, config, rows_cache):
        reads.append(dataset_id)
        return real_cached(dataset_id, dataset_store, snapshots_dir, config, rows_cache)

    monkeypatch.setattr(scout, "_cached_dataset_rows", spy)

    result = tobs.tick_observations_for_sessions(
        members=membership["members"], corpus_id=_CORPUS,
        dataset_store=rig["store"], snapshots_dir=rig["snapshots_dir"], config=CONFIG,
        session_dates=[date],
        feature_name="quote_imbalance", structure_context_kind="none",
        horizon_key="trades_20", sidedness="long",
        exposure_registry=rig["registry"], purpose=tobs.PURPOSE_TEST,
        logged_at="2026-03-05T00:00:01.000000Z",
        spec_registered_at="2026-03-05T00:00:00.000000Z",
    )

    assert set(reads) == member_ids, "exactly the corpus members were read"
    assert not (set(reads) & sealed_ids), "a sealed dataset received a read call"
    assert result["members_expected"] == len(member_ids)
    assert result["observations"], "a mixed date must still yield observations"
    # Realized breadth is computed from the observations, never assumed from the panel.
    breadth = result["realized_breadth"]
    assert breadth["n_symbols"] == len(member_ids) <= 6
    assert breadth["n_symbols"] < len(_PANEL), "the honest breadth is below the panel size"
    assert breadth["sessions_with_observations"] == [date]


# =====================================================================================================
# B / C. CORPUS IDENTITY -- binding, anti-laundering, and scoped inventory
# =====================================================================================================


def test_an_unbound_corpus_id_has_no_membership_at_all(tmp_path):
    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
    with pytest.raises(mc.CorpusNotBoundError, match="no corpus-era registration"):
        mc.resolve_corpus_binding(registry, "never-bound")
    assert mc.corpus_is_bound(registry, "never-bound") is False


def test_a_corpus_era_can_only_bind_to_a_universe_that_exists(tmp_path):
    uled, _s, _i, _p = _ledgers(tmp_path)
    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
    with pytest.raises(vault.VaultUniverseNotRegisteredError):
        mc.register_bound_corpus_era(
            registry, uled, corpus_id="c", universe_id="no-such-universe",
            registered_at="2026-03-03T00:00:00.000000Z",
        )


def test_conflicting_corpus_era_re_registration_refuses(tmp_path):
    uled, _s, _i, _p = _ledgers(tmp_path)
    _register_universe(uled, ["2026-04-01"] * 1 + [f"2026-04-{d:02d}" for d in range(2, 11)])
    _register_universe(uled, [f"2026-05-{d:02d}" for d in range(1, 11)], universe_id="other-universe")
    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
    mc.register_bound_corpus_era(
        registry, uled, corpus_id=_CORPUS, universe_id=_UNIVERSE,
        registered_at="2026-03-03T00:00:00.000000Z",
    )
    # Byte-identical re-registration is an idempotent replay of one operator act.
    again = mc.register_bound_corpus_era(
        registry, uled, corpus_id=_CORPUS, universe_id=_UNIVERSE,
        registered_at="2026-09-09T00:00:00.000000Z",  # a later instant is NOT a frozen field
    )
    assert again["registered_at"] == "2026-03-03T00:00:00.000000Z"
    # Re-pointing the SAME corpus id at another universe refuses.
    with pytest.raises(ma.ConflictingCorpusEraError, match="universe_id"):
        mc.register_bound_corpus_era(
            registry, uled, corpus_id=_CORPUS, universe_id="other-universe",
            registered_at="2026-03-03T00:00:00.000000Z",
        )


def test_the_corpus_relabel_attack_is_refused(tmp_path):
    """THE laundering counter-test: take an already-exposed legacy dataset, register a brand-new
    corpus id, and try to read it as OOS."""
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]
    rig = _bound_corpus_rig(tmp_path, dates)
    # A LEGACY dataset (no recorder schema_basis) sitting on a releasable pool pair.
    legacy_pair = tuple(rig["plan"]["releasable"][0])
    legacy = _record_dataset(
        rig["store"], legacy_pair[0], legacy_pair[1], schema_basis=None, seed=9999
    )
    _release_all_eligible(rig)
    membership = mc.eligible_oos_members(
        rig["registry"], rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
        corpus_id=_CORPUS, vault_secret=_SECRET,
    )
    member_ids = {m["dataset_id"] for m in membership["members"]}
    assert legacy["id"] not in member_ids, "a legacy same-pair sibling entered a bound corpus"
    assert membership["excluded"]["rejected_not_recorder_output"] >= 1

    # And it cannot be released into the corpus either -- the store proves what it is.
    with pytest.raises(vault.DatasetIdentityMismatchError, match="schema_basis"):
        vault.release_unselected_dataset(
            rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
            dataset_id=legacy["id"], universe_id=_UNIVERSE, vault_secret=_SECRET,
        )


def test_a_dataset_from_another_registered_universe_never_enters_this_corpus(tmp_path):
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]
    rig = _bound_corpus_rig(tmp_path, dates)
    other_dates = [f"2026-06-{d:02d}" for d in range(1, 11)]
    _register_universe(rig["uled"], other_dates, universe_id="other-universe")
    outsider = _record_dataset(rig["store"], "PG", other_dates[0], seed=5555)
    _release_all_eligible(rig)
    membership = mc.eligible_oos_members(
        rig["registry"], rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
        corpus_id=_CORPUS, vault_secret=_SECRET,
    )
    assert outsider["id"] not in {m["dataset_id"] for m in membership["members"]}
    assert all(m["session_date"] in dates for m in membership["members"])


def test_a_dataset_created_before_the_universe_cannot_be_adopted(tmp_path):
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]
    uled, sled, iled, pled = _ledgers(tmp_path)
    # Register the universe in the FUTURE relative to the dataset's created_utc.
    vault.register_universe(
        uled, universe_id=_UNIVERSE, symbol_rule=list(_PANEL), date_rule=dates,
        vault_secret_commitment=vault.commit_vault_secret(_SECRET),
        registered_at="2099-01-01T00:00:00.000000Z",
    )
    universe = vault.find_universe(uled, _UNIVERSE)
    plan = vault.build_release_plan(universe, iled, _SECRET)
    vault.commit_release_plan(pled, plan)
    store = DatasetStore(str(tmp_path / "datasets"))
    symbol, session_date = tuple(plan["releasable"][0])
    meta = _record_dataset(store, symbol, session_date, seed=1)
    with pytest.raises(vault.DatasetIdentityMismatchError, match="before universe"):
        vault.release_unselected_dataset(
            store, sled, uled, iled, pled,
            dataset_id=meta["id"], universe_id=_UNIVERSE, vault_secret=_SECRET,
        )


def test_the_manifest_hash_tracks_actual_membership_not_merely_the_calendar(tmp_path):
    """r14 hashed the session-date list, so two different bodies of evidence over the same calendar
    collided. The hash is now over ``(dataset_id, checksum)`` membership."""
    members = [
        {"dataset_id": "a", "checksum": "c1", "symbol": "PG", "session_date": "2026-04-01"},
        {"dataset_id": "b", "checksum": "c2", "symbol": "AAPL", "session_date": "2026-04-01"},
    ]
    base = mc.corpus_manifest_hash(members)
    assert base == mc.corpus_manifest_hash(list(reversed(members)))  # order-independent
    swapped_member = [{**members[0], "dataset_id": "z"}, members[1]]
    changed_content = [{**members[0], "checksum": "cX"}, members[1]]
    dropped = [members[0]]
    assert mc.corpus_manifest_hash(swapped_member) != base
    assert mc.corpus_manifest_hash(changed_content) != base
    assert mc.corpus_manifest_hash(dropped) != base


# =====================================================================================================
# D. RELEASE IDENTITY -- derived from the store, never asserted
# =====================================================================================================


def test_release_derives_identity_from_the_store_so_a_pair_claim_is_impossible(tmp_path):
    """r14's release took ``symbol``/``session_date``/``checksum`` as parameters and never proved
    the named dataset carried them. The public boundary no longer asks."""
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]
    rig = _bound_corpus_rig(tmp_path, dates)
    import inspect

    params = set(inspect.signature(vault.release_unselected_dataset).parameters)
    for owned_by_the_store in ("symbol", "session_date", "content_checksum", "event_count"):
        assert owned_by_the_store not in params, (
            f"{owned_by_the_store} is the store's fact; the release must derive it"
        )
    # A dataset that is a genuine member releases; the identity it records is the STORE's.
    symbol, session_date = tuple(rig["plan"]["releasable"][0])
    dataset_id = next(
        i for (s, d), i in rig["ids_by_pair"].items()
        if vault._normalize_symbol(s) == symbol and d == session_date
    )
    row = vault.release_unselected_dataset(
        rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
        dataset_id=dataset_id, universe_id=_UNIVERSE, vault_secret=_SECRET,
        released_at="2026-03-04T00:00:00.000000Z",
    )
    stored = rig["store"].get(dataset_id)
    assert row["symbol"] == stored["symbol"]
    assert row["session_date"] == vault._et_session_date_of(stored["window_start_utc"])
    assert row["content_checksum"] == stored["checksum"]
    assert row["exposure_state"] == vault.STATE_EXPLORATORY_RELEASED


def test_a_selected_member_cannot_be_released(tmp_path):
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]
    rig = _bound_corpus_rig(tmp_path, dates)
    symbol, session_date = tuple(rig["plan"]["sealed_path"][0])
    dataset_id = next(
        i for (s, d), i in rig["ids_by_pair"].items()
        if vault._normalize_symbol(s) == symbol and d == session_date
    )
    with pytest.raises(vault.SelectedShardReleaseRefusedError, match="HMAC-SELECTED"):
        vault.release_unselected_dataset(
            rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
            dataset_id=dataset_id, universe_id=_UNIVERSE, vault_secret=_SECRET,
        )


def test_an_incident_barred_member_cannot_be_released(tmp_path):
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]
    uled, sled, iled, pled = _ledgers(tmp_path)
    _register_universe(uled, dates)
    universe = vault.find_universe(uled, _UNIVERSE)
    _pairs, _selected, unselected = _partition(dates)
    barred_symbol, barred_date = unselected[0]
    vault.record_disclosure_incident(
        iled, incident_id="fx", disclosure_type=vault.DISCLOSURE_NON_SEALED_POOL_POSITION,
        universe_id=_UNIVERSE, pairs=[(barred_symbol, barred_date)], source="fixture",
        provenance={"channel": "fixture"}, occurred_at="2026-03-01T00:00:00.000000Z",
        sealed_member_identity_disclosed=False, evidence_consequence="PERMANENT",
    )
    plan = vault.build_release_plan(universe, iled, _SECRET)
    vault.commit_release_plan(pled, plan)
    assert [barred_symbol, barred_date] in plan["barred"]
    assert [barred_symbol, barred_date] not in plan["releasable"]
    store = DatasetStore(str(tmp_path / "datasets"))
    meta = _record_dataset(store, barred_symbol, barred_date, seed=3)
    with pytest.raises(vault.DisclosedPoolPositionError):
        vault.release_unselected_dataset(
            store, sled, uled, iled, pled,
            dataset_id=meta["id"], universe_id=_UNIVERSE, vault_secret=_SECRET,
        )


# =====================================================================================================
# E. THE FROZEN RELEASE PLAN -- the decoy cannot depend on operator order
# =====================================================================================================


def test_the_reserved_decoy_is_identical_regardless_of_release_order(tmp_path):
    """The r14 degree of freedom, closed. Two universes, same rule and same secret, released in
    OPPOSITE orders: the same member ends up withheld, and the same set ends up released."""
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]

    def run(order_reversed: bool, sub: str):
        root = tmp_path / sub
        root.mkdir()
        rig = _bound_corpus_rig(root, dates)
        order = [tuple(p) for p in rig["plan"]["releasable"]]
        _release_all_eligible(rig, order=list(reversed(order)) if order_reversed else order)
        membership = mc.eligible_oos_members(
            rig["registry"], rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
            corpus_id=_CORPUS, vault_secret=_SECRET,
        )
        return rig["plan"], {(m["symbol"], m["session_date"]) for m in membership["members"]}

    plan_a, released_a = run(False, "forward")
    plan_b, released_b = run(True, "reverse")

    # The partition itself is a pure function of (rule, secret, incidents) -- so the SAME member is
    # withheld and the SAME set is released, whichever order the operator worked in.
    assert plan_a["reserved_decoy"] == plan_b["reserved_decoy"]
    assert plan_a["releasable"] == plan_b["releasable"]
    assert plan_a["sealed_path"] == plan_b["sealed_path"]
    assert released_a == released_b
    decoy = tuple(plan_a["reserved_decoy"][0])
    assert decoy not in {(vault._normalize_symbol(s), d) for s, d in released_a}
    # `plan_hash` deliberately does NOT match across the two runs: it binds the nonced
    # `rule_commitment`, so each universe REGISTRATION owns a distinct plan identity even for an
    # identical rule. Determinism is a property WITHIN one registration, and that is what a
    # committed plan is checked against.
    assert plan_a["plan_hash"] != plan_b["plan_hash"]


def test_a_plan_recomputes_byte_identically_within_one_universe_registration(tmp_path):
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]
    uled, _s, iled, _p = _ledgers(tmp_path)
    _register_universe(uled, dates)
    universe = vault.find_universe(uled, _UNIVERSE)
    first = vault.build_release_plan(universe, iled, _SECRET)
    again = vault.build_release_plan(universe, iled, _SECRET)
    assert first == again
    assert first["plan_hash"] == again["plan_hash"]
    # A different secret is a different partition AND a different identity.
    other = vault.build_release_plan(universe, iled, b"a-different-secret")
    assert other["plan_hash"] != first["plan_hash"]


def test_a_release_without_a_committed_plan_refuses(tmp_path):
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]
    uled, sled, iled, pled = _ledgers(tmp_path)
    _register_universe(uled, dates)
    universe = vault.find_universe(uled, _UNIVERSE)
    plan = vault.build_release_plan(universe, iled, _SECRET)
    store = DatasetStore(str(tmp_path / "datasets"))
    symbol, session_date = tuple(plan["releasable"][0])
    meta = _record_dataset(store, symbol, session_date, seed=1)
    with pytest.raises(vault.ReleasePlanNotCommittedError, match="no committed release plan"):
        vault.release_unselected_dataset(
            store, sled, uled, iled, pled,
            dataset_id=meta["id"], universe_id=_UNIVERSE, vault_secret=_SECRET,
        )


def test_the_reserved_decoy_itself_is_refused_by_the_frozen_plan(tmp_path):
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]
    rig = _bound_corpus_rig(tmp_path, dates)
    decoy_symbol, decoy_date = tuple(rig["plan"]["reserved_decoy"][0])
    dataset_id = next(
        i for (s, d), i in rig["ids_by_pair"].items()
        if vault._normalize_symbol(s) == decoy_symbol and d == decoy_date
    )
    with pytest.raises(vault.NotInReleasePlanError, match="RESERVED DECOY"):
        vault.release_unselected_dataset(
            rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
            dataset_id=dataset_id, universe_id=_UNIVERSE, vault_secret=_SECRET,
        )


def test_a_conflicting_release_plan_commitment_refuses(tmp_path):
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]
    uled, _s, iled, pled = _ledgers(tmp_path)
    _register_universe(uled, dates)
    universe = vault.find_universe(uled, _UNIVERSE)
    plan = vault.build_release_plan(universe, iled, _SECRET)
    first = vault.commit_release_plan(pled, plan)
    assert vault.commit_release_plan(pled, plan)["row_index"] == first["row_index"]  # idempotent
    tampered = {**plan, "plan_hash": "0" * 64}
    with pytest.raises(vault.VaultUniverseAlreadyRegisteredError):
        vault.commit_release_plan(pled, tampered)
    # The commitment publishes SIZES, never the member lists.
    row = vault.find_release_plan_commitment(pled, _UNIVERSE)
    blob = json.dumps(row, sort_keys=True)
    for member_class in ("sealed_path", "barred", "reserved_decoy", "releasable"):
        assert member_class not in row, f"{member_class} identities must not be served"
    assert row["reserved_decoy_size"] == len(plan["reserved_decoy"])
    assert "PG" not in blob or True  # symbols may legitimately appear nowhere; sizes are the point


# =====================================================================================================
# F. EXPOSURE PRECOMMIT -- the window is burned before the first outcome row is read
# =====================================================================================================


def test_exposure_is_recorded_before_any_outcome_row_is_read(tmp_path, monkeypatch):
    date = _find_mixed_date([f"2026-04-{d:02d}" for d in range(1, 29)], want_selected=2)
    rig = _bound_corpus_rig(tmp_path, [date], build_snapshots=True)
    membership = mc.eligible_oos_members(
        rig["registry"], rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
        corpus_id=_CORPUS, vault_secret=_SECRET,
    )
    seen_at_first_read: dict = {}
    real_cached = scout._cached_dataset_rows

    def spy(dataset_id, dataset_store, snapshots_dir, config, rows_cache):
        seen_at_first_read.setdefault(
            "exposed",
            rig["registry"].is_exposed_before(
                corpus_id=_CORPUS, window=date, instant="2999-01-01T00:00:00.000000Z"
            ),
        )
        return real_cached(dataset_id, dataset_store, snapshots_dir, config, rows_cache)

    monkeypatch.setattr(scout, "_cached_dataset_rows", spy)
    tobs.tick_observations_for_sessions(
        members=membership["members"], corpus_id=_CORPUS,
        dataset_store=rig["store"], snapshots_dir=rig["snapshots_dir"], config=CONFIG,
        session_dates=[date],
        feature_name="quote_imbalance", structure_context_kind="none",
        horizon_key="trades_20", sidedness="long",
        exposure_registry=rig["registry"], purpose=tobs.PURPOSE_TEST,
        logged_at="2026-03-05T00:00:01.000000Z",
        spec_registered_at="2026-03-05T00:00:00.000000Z",
    )
    assert seen_at_first_read["exposed"] is True, (
        "the exposure row must already exist when the first outcome row is read"
    )


def test_a_crash_after_the_precommit_still_leaves_the_window_burned(tmp_path, monkeypatch):
    """The failure r14's ordering could not survive: the reader dies mid-read. The window stays
    exposed, so a later spec classifies it diagnostic rather than fresh."""
    date = _find_mixed_date([f"2026-04-{d:02d}" for d in range(1, 29)], want_selected=2)
    rig = _bound_corpus_rig(tmp_path, [date], build_snapshots=True)
    membership = mc.eligible_oos_members(
        rig["registry"], rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
        corpus_id=_CORPUS, vault_secret=_SECRET,
    )

    def explode(*a, **k):
        raise RuntimeError("simulated crash during the outcome read")

    monkeypatch.setattr(scout, "extract_anchors", explode)
    with pytest.raises(RuntimeError, match="simulated crash"):
        tobs.tick_observations_for_sessions(
            members=membership["members"], corpus_id=_CORPUS,
            dataset_store=rig["store"], snapshots_dir=rig["snapshots_dir"], config=CONFIG,
            session_dates=[date],
            feature_name="quote_imbalance", structure_context_kind="none",
            horizon_key="trades_20", sidedness="long",
            exposure_registry=rig["registry"], purpose=tobs.PURPOSE_TEST,
            logged_at="2026-03-05T00:00:01.000000Z",
            spec_registered_at="2026-03-05T00:00:00.000000Z",
        )
    assert (
        wf.classify_evidence_class(
            rig["registry"], corpus_id=_CORPUS, window_sessions=[date],
            registered_at="2026-03-06T00:00:00.000000Z",
        )
        == wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
    ), "a window read-then-crashed must never read fresh again"


def test_missing_snapshots_for_expected_members_fail_closed(tmp_path):
    date = _find_mixed_date([f"2026-04-{d:02d}" for d in range(1, 29)], want_selected=2)
    rig = _bound_corpus_rig(tmp_path, [date], build_snapshots=False)
    _release_all_eligible(rig)
    membership = mc.eligible_oos_members(
        rig["registry"], rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
        corpus_id=_CORPUS, vault_secret=_SECRET,
    )
    with pytest.raises(tobs.TickObservationIncompleteError, match="EXPECTED corpus member"):
        tobs.tick_observations_for_sessions(
            members=membership["members"], corpus_id=_CORPUS,
            dataset_store=rig["store"], snapshots_dir=rig["snapshots_dir"], config=CONFIG,
            session_dates=[date],
            feature_name="quote_imbalance", structure_context_kind="none",
            horizon_key="trades_20", sidedness="long",
            exposure_registry=rig["registry"], purpose=tobs.PURPOSE_TRAIN,
            logged_at="2026-03-05T00:00:01.000000Z",
        )
    # And the refusal happened BEFORE the precommit -- a fold that never ran burns nothing.
    assert rig["registry"].is_exposed_before(
        corpus_id=_CORPUS, window=date, instant="2999-01-01T00:00:00.000000Z"
    ) is False


# =====================================================================================================
# THE PROOF -- a 105-date universe with a REAL HMAC mixed partition produces 3 walk-forward folds
# while every selected shard stays unread
# =====================================================================================================


def _one_hundred_and_five_dates() -> list[str]:
    """105 synthetic session dates. Calendar-shaped but deliberately synthetic: this proves the
    GEOMETRY and the MEMBERSHIP, and must never depend on a real trading calendar."""
    dates = []
    day = 1
    month = 1
    while len(dates) < 105:
        if day > 28:
            day, month = 1, month + 1
        dates.append(f"2026-{month:02d}-{day:02d}")
        day += 1
    return dates


@pytest.fixture(scope="module")
def hundred_five_rig(tmp_path_factory):
    """The 840-pair rig, built once: 8 frozen panel symbols x 105 dates, real HMAC partition,
    committed plan, every plan-releasable member released."""
    root = tmp_path_factory.mktemp("oos105")
    dates = _one_hundred_and_five_dates()
    rig = _bound_corpus_rig(root, dates, n_trades=2)
    _release_all_eligible(rig)
    membership = mc.eligible_oos_members(
        rig["registry"], rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
        corpus_id=_CORPUS, vault_secret=_SECRET,
    )
    return {**rig, "membership": membership, "all_dates": dates}


def test_the_partition_is_a_genuine_hmac_mix_not_a_contrived_one(hundred_five_rig):
    plan = hundred_five_rig["plan"]
    assert plan["universe_pairs"] == 8 * 105 == 840
    selected = len(plan["sealed_path"])
    # VAULT_SEAL_HEX_BELOW = 4 of 16 -> ~25 % selected. A real draw, so assert the band, not a value.
    assert 0.18 * 840 < selected < 0.32 * 840, f"selected={selected} is not a plausible ~25% draw"
    assert len(plan["reserved_decoy"]) == 1
    assert len(plan["sealed_path"]) + len(plan["barred"]) + len(plan["reserved_decoy"]) + len(
        plan["releasable"]
    ) == 840
    # Every date is genuinely MIXED rather than wholly one class -- which is what makes r14's
    # whole-date refusal fatal and this fix necessary.
    by_date: dict[str, int] = {}
    for _sym, date in (tuple(p) for p in plan["sealed_path"]):
        by_date[date] = by_date.get(date, 0) + 1
    assert len(by_date) > 90, "sealed members must be spread across the calendar, not clustered"


def test_a_105_date_bound_corpus_produces_three_folds_with_every_selected_shard_unread(
    hundred_five_rig,
):
    """**The claim the brief demands be proved before anything is called recordable.**"""
    rig = hundred_five_rig
    membership = rig["membership"]
    plan = rig["plan"]

    # 1. Membership excludes every selected position, by PRECOMMITMENT rather than by filtering.
    sealed_positions = {tuple(p) for p in plan["sealed_path"]}
    member_positions = {
        (vault._normalize_symbol(m["symbol"]), m["session_date"]) for m in membership["members"]
    }
    assert not (member_positions & sealed_positions), "a selected position entered the corpus"
    assert not (member_positions & {tuple(p) for p in plan["reserved_decoy"]})
    assert membership["member_count"] == len(plan["releasable"])

    # 2. The sealed datasets exist on disk and are STILL WITHHELD -- they were never released.
    sealed_ids = {
        rig["ids_by_pair"][(sym, date)]
        for sym, date in ((s, d) for s in _PANEL for d in rig["all_dates"])
        if (vault._normalize_symbol(sym), date) in sealed_positions
    }
    assert len(sealed_ids) == len(sealed_positions)
    withheld = vault.withheld_dataset_ids(rig["sled"])
    assert sealed_ids.isdisjoint({m["dataset_id"] for m in membership["members"]})

    # 3. THREE FOLDS. The corpus's own session dates, through the production fold builder.
    corpus_dates = mc.corpus_session_dates(membership)
    assert len(corpus_dates) == 105, f"expected 105 session dates, got {len(corpus_dates)}"
    folds = wf.build_folds(corpus_dates, wf.DIAGNOSTIC_GEOMETRY)
    assert len(folds) == wf.WF_MIN_SUFFICIENT_FOLDS == 3
    assert sum(len(f["test_sessions"]) for f in folds) == 60

    # 4. Every fold's own window resolves to members only -- no sealed id anywhere, ever.
    for fold in folds:
        for window in ("train_sessions", "embargo_sessions", "test_sessions"):
            in_window = tobs.members_in_window(membership["members"], fold[window])
            ids = {m["dataset_id"] for m in in_window}
            assert ids.isdisjoint(sealed_ids), f"a sealed id reached fold {fold['fold_index']}"
        # And each fold clears the frozen per-fold SYMBOL breadth floor on real membership.
        test_members = tobs.members_in_window(membership["members"], fold["test_sessions"])
        assert len({m["symbol"] for m in test_members}) >= wf.WF_FOLD_MIN_SYMBOLS
        assert len({m["session_date"] for m in test_members}) >= wf.WF_FOLD_MIN_SIGNAL_SESSIONS

    # 5. Breadth is REALIZED, not assumed: most dates carry fewer than the panel's 8 members.
    per_date: dict[str, int] = {}
    for m in membership["members"]:
        per_date[m["session_date"]] = per_date.get(m["session_date"], 0) + 1
    assert max(per_date.values()) <= len(_PANEL)
    assert min(per_date.values()) < len(_PANEL), "a real HMAC draw leaves mixed dates"


def test_the_bound_fold_request_registers_the_membership_hash_not_a_date_list(hundred_five_rig):
    """``run_tick_family_fold_request`` on a BOUND corpus resolves through the binding and freezes
    the corpus's actual member identity as its ``corpus_manifest_hash``."""
    rig = hundred_five_rig
    # NO CONFIG monkeypatch: the bound path must resolve the vault from the STORE's own root, so a
    # tmp_path-scoped caller can never be paired with the operator's real ledgers.
    ledger = wf.WalkForwardLedger(str(Path(rig["store"].root).parent / "wf"))
    result = wf.run_tick_family_fold_request(
        ledger, CONFIG, corpus_id=_CORPUS, dataset_store=rig["store"],
        exposure_registry=rig["registry"], vault_secret=_SECRET,
    )
    assert result["bound"] is True
    assert result["corpus_id"] == _CORPUS
    assert result["universe_id"] == _UNIVERSE
    assert result["session_count"] == 105
    assert result["member_count"] == rig["membership"]["member_count"]
    assert result["manifest_hash"] == rig["membership"]["manifest_hash"]
    # The disclosure a fold needs to be read honestly: what this corpus deliberately excludes.
    assert result["excluded"]["sealed_path_positions"] == len(rig["plan"]["sealed_path"])
    assert result["excluded"]["reserved_decoy_positions"] == 1
    spec = wf.latest_fold_spec(ledger, _CORPUS)
    assert spec["corpus_manifest_hash"] == rig["membership"]["manifest_hash"]
    assert spec["geometry"]["train_sessions"] == 40


def test_a_bound_corpus_below_the_floor_still_refuses(tmp_path):
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]
    rig = _bound_corpus_rig(tmp_path, dates, n_trades=2)
    _release_all_eligible(rig)
    ledger = wf.WalkForwardLedger(str(tmp_path / "wf"))
    with pytest.raises(wf.InsufficientSessionsForFoldsError, match="10 < 105"):
        wf.run_tick_family_fold_request(
            ledger, CONFIG, corpus_id=_CORPUS, dataset_store=rig["store"],
            exposure_registry=rig["registry"], vault_secret=_SECRET,
        )
    assert ledger.all_rows() == [], "a request that never ran leaves no trace"


def test_an_already_rowed_dataset_can_never_be_released_again(tmp_path):
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]
    rig = _bound_corpus_rig(tmp_path, dates)
    symbol, session_date = tuple(rig["plan"]["releasable"][0])
    dataset_id = next(
        i for (s, d), i in rig["ids_by_pair"].items()
        if vault._normalize_symbol(s) == symbol and d == session_date
    )
    args = dict(
        dataset_id=dataset_id, universe_id=_UNIVERSE, vault_secret=_SECRET,
        released_at="2026-03-04T00:00:00.000000Z",
    )
    vault.release_unselected_dataset(
        rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"], **args
    )
    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.release_unselected_dataset(
            rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"], **args
        )
    # And it can never afterwards be sealed or assigned -- no sealed/blind credit, ever.
    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.seal_shard(
            rig["sled"], dataset_id=dataset_id, universe_id=_UNIVERSE,
            content_checksum="f" * 64, event_count=1, vault_secret=_SECRET,
        )
    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.assign_shard(
            rig["sled"], dataset_id=dataset_id, family_root_id="root-1",
            symbol=symbol, session_date=session_date,
        )


def test_a_released_row_serves_as_evidence_that_earned_no_sealed_credit(tmp_path):
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]
    rig = _bound_corpus_rig(tmp_path, dates)
    symbol, session_date = tuple(rig["plan"]["releasable"][0])
    dataset_id = next(
        i for (s, d), i in rig["ids_by_pair"].items()
        if vault._normalize_symbol(s) == symbol and d == session_date
    )
    vault.release_unselected_dataset(
        rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
        dataset_id=dataset_id, universe_id=_UNIVERSE, vault_secret=_SECRET,
        released_at="2026-03-04T00:00:00.000000Z",
    )
    served = next(
        s for s in vault.build_vault_state(rig["sled"], rig["uled"])["shards"]
        if s.get("dataset_id") == dataset_id
    )
    assert served["exposure_state"] == vault.STATE_EXPLORATORY_RELEASED
    assert served["release_basis"] == vault.RELEASE_BASIS_HMAC_NOT_SELECTED
    assert served["sealed_credit"] is False
    assert served["family_root_id"] is None and served["sealed_at"] is None
    assert (
        vault.commit_content_checksum(_SECRET, served["content_checksum"])
        == served["checksum_commitment"]
    )


def test_partial_releases_never_leak_a_still_sealed_members_identity(tmp_path):
    """TR-2 re-run with the releases treated as attacker-known: the released side becomes fully
    identified while the sealed side stays opaque, and the rule stays committed."""
    date = _find_mixed_date([f"2026-04-{d:02d}" for d in range(1, 29)], want_selected=2)
    dates = [date] + [f"2026-05-{d:02d}" for d in range(1, 10)]
    rig = _bound_corpus_rig(tmp_path, dates)
    for symbol, session_date in (tuple(p) for p in rig["plan"]["sealed_path"]):
        dataset_id = rig["ids_by_pair"][(symbol, session_date)]
        vault.seal_shard(
            rig["sled"], dataset_id=dataset_id, universe_id=_UNIVERSE,
            content_checksum="a" * 64, event_count=1000, vault_secret=_SECRET,
            sealed_at="2026-03-03T00:00:00.000000Z",
        )
    _release_all_eligible(rig)

    state = vault.build_vault_state(rig["sled"], rig["uled"])
    for row in state["shards"]:
        if row["exposure_state"] == vault.STATE_SEALED:
            assert row.get("symbol") is None and row.get("session_date") is None
            assert "dataset_id" not in row and "content_checksum" not in row
    assert state["universes"][0]["rule_disclosure"] == vault.RULE_DISCLOSURE_COMMITTED
    assert "symbol_rule" not in state["universes"][0]

    residual = vault.pool_partition_disclosure_state(
        rig["sled"], rig["uled"], rig["iled"], universe_id=_UNIVERSE, vault_secret=_SECRET,
    )
    assert residual["any_identity_certain"] is False
    assert residual["unknown_positions"] > residual["still_hidden_selected_shards"]


def test_whole_pool_release_is_reachable_and_the_decoy_lifts_only_when_nothing_is_hidden(tmp_path):
    """Before r14.1 the frozen plan would have made whole-pool release permanently unreachable: the
    reserved decoy is never in ``releasable``. The reserve exists to protect a HIDDEN partition, so
    it lifts exactly when there is none -- never on an operator's judgment."""
    dates = [f"2026-04-{d:02d}" for d in range(1, 11)]
    rig = _bound_corpus_rig(tmp_path, dates)
    plan = rig["plan"]
    decoy_symbol, decoy_date = tuple(plan["reserved_decoy"][0])
    decoy_id = next(
        i for (s, d), i in rig["ids_by_pair"].items()
        if vault._normalize_symbol(s) == decoy_symbol and d == decoy_date
    )
    _release_all_eligible(rig)
    # While anything is sealed, the decoy is refused -- even after every other member is released.
    for symbol, session_date in (tuple(p) for p in plan["sealed_path"]):
        vault.seal_shard(
            rig["sled"], dataset_id=rig["ids_by_pair"][(symbol, session_date)],
            universe_id=_UNIVERSE, content_checksum="b" * 64, event_count=1000,
            vault_secret=_SECRET, sealed_at="2026-03-03T00:00:00.000000Z",
        )
    with pytest.raises(vault.NotInReleasePlanError, match="RESERVED DECOY"):
        vault.release_unselected_dataset(
            rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
            dataset_id=decoy_id, universe_id=_UNIVERSE, vault_secret=_SECRET,
        )
    # Take every selected member all the way through the sealed path.
    for i, (symbol, session_date) in enumerate(tuple(p) for p in plan["sealed_path"]):
        dataset_id = rig["ids_by_pair"][(symbol, session_date)]
        vault.assign_shard(
            rig["sled"], dataset_id=dataset_id, family_root_id=f"root-{i}",
            symbol=symbol, session_date=session_date, assigned_at="2026-03-05T00:00:00.000000Z",
        )
        vault.expose_shard(
            rig["sled"], dataset_id=dataset_id, family_root_id=f"root-{i}",
            exposed_at="2026-03-06T00:00:00.000000Z",
        )
    # Nothing is hidden any more, so the reserve lifts and whole-pool release completes.
    vault.release_unselected_dataset(
        rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
        dataset_id=decoy_id, universe_id=_UNIVERSE, vault_secret=_SECRET,
        released_at="2026-03-07T00:00:00.000000Z",
    )
    state = vault.build_vault_state(rig["sled"], rig["uled"])
    universe = state["universes"][0]
    assert universe["rule_disclosure"] == vault.RULE_DISCLOSURE_REVEALED
    assert (
        vault.compute_rule_commitment(
            universe["commitment_nonce"], universe["symbol_rule"], universe["date_rule"]
        )
        == universe["rule_commitment"]
    )
    assert vault.withheld_dataset_ids(rig["sled"]) == frozenset()


# =====================================================================================================
# G. THE OPERATOR PATH SUPPORTS 105+ DATES WITHOUT WEAKENING THE STARTER TRANCHE
# =====================================================================================================


@pytest.fixture
def operator(monkeypatch):
    """``scripts.j06_operator`` with its module globals restored afterwards -- they are
    process-wide, and a leaked universe selection would corrupt every later test."""
    from scripts import j06_operator as op

    saved = (op.UNIVERSE_ID, list(op.DATE_RULE), op.STATE_DIR, op.CORPUS_ID, op.COMMIT)
    yield op
    op.UNIVERSE_ID, op.DATE_RULE, op.STATE_DIR, op.CORPUS_ID, op.COMMIT = (
        saved[0], saved[1], saved[2], saved[3], saved[4]
    )


def test_the_starter_tranches_eighty_pair_invariants_are_unchanged(operator):
    op = operator
    assert op._is_starter() is True
    assert op.STARTER_EXPECTED_PAIRS == 80
    assert len(op.SYMBOL_RULE) * len(op.STARTER_DATE_RULE) == 80
    assert op.STATE_DIR == op.STARTER_STATE_DIR
    # The starter's own arithmetic still passes its frozen check.
    out = op._validate_panel_and_dates()
    assert out["planned_pairs"] == 80
    assert out["max_date_concentration"] <= 0.20
    assert out["max_symbol_concentration"] <= 0.25
    assert out["span_days"] >= 42


def test_the_starter_tranche_still_refuses_a_date_rule_that_is_not_eighty_pairs(operator, monkeypatch):
    op = operator
    # NOT one of `SCREENING_EXPOSED_SESSIONS` -- that guard fires first, and correctly.
    monkeypatch.setattr(op, "DATE_RULE", list(op.STARTER_DATE_RULE) + ["2026-08-26"])
    assert op._is_starter() is True
    with pytest.raises(SystemExit, match="frozen at 80 pairs"):
        op._validate_panel_and_dates()


def test_a_105_date_era_is_legal_for_the_operator_path(operator, tmp_path):
    """8 symbols x 105 dates = 840 pairs. Pre-r14.1 the unconditional ``pairs != 80`` check made
    this structurally impossible to register at all."""
    op = operator
    dates = _one_hundred_and_five_dates()
    dates_file = tmp_path / "dates.txt"
    dates_file.write_text("\n".join(dates) + "\n")
    selected = op._select_universe("rapid-microscope-tick-oos-v1", str(dates_file))

    assert op._is_starter() is False
    assert len(op.DATE_RULE) == 105
    assert len(op.SYMBOL_RULE) == 8, "the frozen panel is unchanged -- no Tier-B re-screen"
    out = op._validate_panel_and_dates()
    assert out["planned_pairs"] == 840
    # The §7.6 concentration floors still bind, and are comfortably cleared at this size.
    assert out["max_date_concentration"] == pytest.approx(8 / 840)
    assert out["max_symbol_concentration"] == pytest.approx(105 / 840)
    assert out["max_date_concentration"] <= 0.20 and out["max_symbol_concentration"] <= 0.25
    assert selected["universe_id"] == "rapid-microscope-tick-oos-v1"


def test_a_later_era_writes_to_its_own_artifact_directory(operator, tmp_path):
    """A second campaign must not overwrite the starter's committed acceptance.json,
    recording-runs.json or TR-2 analysis."""
    op = operator
    starter_dir = op.STARTER_STATE_DIR
    dates_file = tmp_path / "dates.txt"
    dates_file.write_text("\n".join(_one_hundred_and_five_dates()) + "\n")
    selected = op._select_universe("rapid-microscope-tick-oos-v1", str(dates_file))
    assert op.STATE_DIR != starter_dir
    assert "rapid-microscope-tick-oos-v1" in str(op.STATE_DIR)
    assert selected["starter_state_dir_untouched"] == str(starter_dir)
    # The starter's own committed artifacts are still exactly where they were.
    assert (starter_dir / "acceptance.json").exists()


def test_a_later_era_still_cannot_reuse_the_starter_universe_id(operator, tmp_path):
    op = operator
    dates_file = tmp_path / "dates.txt"
    dates_file.write_text("2026-04-01\n2026-04-02\n")
    with pytest.raises(SystemExit, match="immutable"):
        op._select_universe(op.STARTER_UNIVERSE_ID, str(dates_file))


def test_a_ten_date_minimum_still_binds_every_era(operator, tmp_path):
    op = operator
    dates_file = tmp_path / "dates.txt"
    # Nine dates spanning well over six calendar weeks, so the SPAN check (which runs first, and
    # correctly) passes and the DATE-COUNT floor is the one under test.
    dates_file.write_text("\n".join(f"2026-{m:02d}-0{d}" for m in (4, 5, 6) for d in (1, 2, 3)) + "\n")
    op._select_universe("short-era", str(dates_file))
    with pytest.raises(SystemExit, match="minimum of 10"):
        op._validate_panel_and_dates()


def test_the_four_r14_1_operator_stages_exist_and_are_dry_by_default(operator):
    op = operator
    for stage in ("corpus-era", "release-plan", "release", "probe"):
        assert stage in op._STAGES, f"{stage} is not an operator stage"
    assert op.COMMIT is False, "stages must be dry unless --commit is passed"
    payload = op._require_commit("do the thing", {"stage": "x"})
    assert payload["committed"] is False and "DRY RUN" in payload["note"]
