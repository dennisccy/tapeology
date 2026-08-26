"""r14.2 -- physical evidence may earn out-of-sample credit exactly ONCE.

r14.1 bound a ``corpus_id`` to a universe, scoped membership, proved release identity and made the
decoy deterministic. A post-commit review found four ways evidence could still be re-earned, or
counted twice, or claimed on a date count alone. This file is the executable contract for closing
them:

* **§1 one universe, one corpus era.** ``corpus_id -> universe`` was enforced; the INVERSE was
  free. Bind ``corpus_A`` to universe ``U``, spend it, then bind a fresh ``corpus_B`` to the same
  ``U``: because exposure is scoped by ``corpus_id``, ``corpus_B`` opens a pristine exposure
  namespace over identical bytes and every spent window reads ``historical_oos`` again.
* **§2 release IS exposure.** Exploratory release turns a withheld dataset into servable evidence.
  r14.1 recorded no exposure for it, so a rule frozen AFTERWARDS could claim out-of-sample credit
  over tape anyone could already read.
* **§3 one registered position, one dataset.** A retry can leave two genuine recorder datasets on
  one ``(symbol, session_date)``. Admitting both double-weights that session's cluster and inflates
  every breadth floor computed from distinct sessions.
* **§4 constructible is not sufficient.** 105 dates guarantee three CONSTRUCTIBLE folds. Whether any
  of them is SUFFICIENT depends on observation density, which no date count can know.

Plus §5's durable Mode B predeclaration and §7's continuous Study 2 representation.

Every vault fixture builds its own universe under its own secret in ``tmp_path``. No test here
reads the operator's real vault, real store, or any sealed shard.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import CONFIG
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.research import micro_accessor as ma
from app.research import micro_corpus as mc
from app.research import micro_features as mf
from app.research import micro_study2_diagnostic as s2
from app.research import scout
from app.research import vault
from app.research import walkforward as wf
from app.research.datasets import SOURCE_HISTORICAL, SPLIT_TRAIN, DatasetStore

_SECRET = b"r14-2-fixture-vault-secret"
_PANEL = ["PG", "AAPL", "MSFT", "NVDA", "AG", "LYFT", "WULF", "SPY"]
_UNIVERSE = "r142-universe"
_CORPUS = "r142-corpus-v1"
_REGISTERED_AT = "2026-03-01T00:00:00.000000Z"


# =====================================================================================================
# rig
# =====================================================================================================


def _ledgers(root: Path):
    r = vault.resolve_vault_dir(str(root / "datasets"))
    return (
        vault.VaultUniverseLedger(r),
        vault.VaultShardLedger(r),
        vault.VaultDisclosureIncidentLedger(r),
        vault.VaultReleasePlanLedger(r),
    )


def _registry(root: Path):
    return ma.ExposureRegistry(ma.resolve_micro_exposure_registry_dir(str(root / "datasets")))


def _register_universe(universe_ledger, dates, universe_id=_UNIVERSE, registered_at=_REGISTERED_AT):
    return vault.register_universe(
        universe_ledger,
        universe_id=universe_id,
        symbol_rule=list(_PANEL),
        date_rule=list(dates),
        vault_secret_commitment=vault.commit_vault_secret(_SECRET),
        registered_at=registered_at,
    )


def _record_dataset(store, symbol, session_date, *, n_trades=6,
                    schema_basis=vault.RECORDER_SCHEMA_BASIS, seed=0.0):
    events = []
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


def _rig(tmp_path: Path, dates, *, bind=True, n_trades=6):
    """Registered universe + committed plan + one dataset per pair + (optionally) a bound era."""
    uled, sled, iled, pled = _ledgers(tmp_path)
    _register_universe(uled, dates)
    universe = vault.find_universe(uled, _UNIVERSE)
    plan = vault.build_release_plan(universe, iled, _SECRET)
    vault.commit_release_plan(pled, plan, committed_at="2026-03-02T00:00:00.000000Z")
    store = DatasetStore(str(tmp_path / "datasets"))
    ids_by_pair = {}
    for i, (symbol, session_date) in enumerate((s, d) for d in dates for s in _PANEL):
        ids_by_pair[(symbol, session_date)] = _record_dataset(
            store, symbol, session_date, n_trades=n_trades, seed=i
        )["id"]
    registry = _registry(tmp_path)
    if bind:
        mc.register_bound_corpus_era(
            registry, uled, corpus_id=_CORPUS, universe_id=_UNIVERSE,
            registered_at="2026-03-03T00:00:00.000000Z",
        )
    return {
        "uled": uled, "sled": sled, "iled": iled, "pled": pled, "store": store,
        "registry": registry, "plan": plan, "ids_by_pair": ids_by_pair,
        "universe": universe, "dates": list(dates), "tmp_path": tmp_path,
    }


def _release(rig, symbol, session_date, *, released_at="2026-03-04T00:00:00.000000Z",
             dataset_id=None):
    if dataset_id is None:
        dataset_id = rig["ids_by_pair"][(symbol, session_date)]
    return vault.release_unselected_dataset(
        rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"], rig["registry"],
        dataset_id=dataset_id, universe_id=_UNIVERSE, vault_secret=_SECRET,
        released_at=released_at,
    )


def _is_withheld(rig, dataset_id: str) -> bool:
    """The real "not servable yet" predicate. ``withheld_dataset_ids`` indexes shard ROWS, so a
    dataset that has never been sealed or released carries no row and is invisible to it -- it is
    withheld as an UNRESOLVED POOL MEMBER, which is what this asks."""
    records, _errors = rig["store"].list()
    return dataset_id in vault.unresolved_pool_universe_by_dataset_id(
        rig["sled"], rig["uled"],
        [
            (m["id"], m["symbol"], vault._et_session_date_of(m["window_start_utc"]),
             m.get("created_utc", ""))
            for m in records
        ],
    )


def _first_releasable(rig):
    return tuple(sorted(tuple(p) for p in rig["plan"]["releasable"])[0])


def _dataset_id_for(rig, position):
    symbol, session_date = position
    return next(
        i for (s, d), i in rig["ids_by_pair"].items()
        if vault._normalize_symbol(s) == symbol and d == session_date
    )


_TEN = [f"2026-04-{d:02d}" for d in range(1, 11)]


# =====================================================================================================
# §1. ONE REGISTERED UNIVERSE = ONE OOS CORPUS ERA
# =====================================================================================================


def test_a_second_corpus_id_on_the_same_universe_refuses(tmp_path):
    """**The replay this closes.** corpus_A spends universe U; corpus_B would re-open a pristine
    exposure namespace over the very same physical recordings."""
    rig = _rig(tmp_path, _TEN)
    with pytest.raises(ma.UniverseAlreadyBoundToCorpusError, match="already founded corpus era"):
        mc.register_bound_corpus_era(
            rig["registry"], rig["uled"], corpus_id="r142-corpus-v2", universe_id=_UNIVERSE,
            registered_at="2026-03-10T00:00:00.000000Z",
        )


def test_b_the_refusal_holds_when_the_first_era_has_zero_exposure_rows(tmp_path):
    """The exploit is the fresh NAMESPACE, not the rows already in it -- so an unspent first era
    must be just as binding as a spent one."""
    rig = _rig(tmp_path, _TEN)
    assert not any(
        ma._is_exposure_row(r) and r.get("corpus_id") == _CORPUS
        for r in rig["registry"].all_rows()
    ), "precondition: the first era has been registered but never exposed"
    with pytest.raises(ma.UniverseAlreadyBoundToCorpusError):
        mc.register_bound_corpus_era(
            rig["registry"], rig["uled"], corpus_id="r142-corpus-v2", universe_id=_UNIVERSE,
            registered_at="2026-03-10T00:00:00.000000Z",
        )


def test_c_the_exact_same_binding_is_idempotent(tmp_path):
    """Replaying the identical promise claims nothing new and must stay free."""
    rig = _rig(tmp_path, _TEN)
    before = len(rig["registry"].all_rows())
    again = mc.register_bound_corpus_era(
        rig["registry"], rig["uled"], corpus_id=_CORPUS, universe_id=_UNIVERSE,
        registered_at="2026-03-99T00:00:00.000000Z",  # a later instant must NOT move the record
    )
    assert len(rig["registry"].all_rows()) == before, "an idempotent replay appends no row"
    assert again["registered_at"] == "2026-03-03T00:00:00.000000Z", (
        "the FIRST registration instant is the one a freshness claim is anchored to"
    )


def test_d_the_same_corpus_id_under_a_changed_universe_identity_still_refuses(tmp_path):
    """r14.1's conflict refusal must survive r14.2's new inverse check, and must be reached."""
    rig = _rig(tmp_path, _TEN)
    _register_universe(rig["uled"], _TEN, universe_id="other-universe",
                       registered_at="2026-03-05T00:00:00.000000Z")
    with pytest.raises(ma.ConflictingCorpusEraError, match="differs on"):
        mc.register_bound_corpus_era(
            rig["registry"], rig["uled"], corpus_id=_CORPUS, universe_id="other-universe",
            registered_at="2026-03-10T00:00:00.000000Z",
        )


def test_the_inverse_index_is_read_from_the_durable_ledger_not_process_state(tmp_path):
    """A fresh ``ExposureRegistry`` over the same directory -- a different process, another
    operator -- must see the binding and refuse identically."""
    rig = _rig(tmp_path, _TEN)
    reopened = _registry(tmp_path)
    assert ma.corpus_era_record_for_universe(reopened, _UNIVERSE)["corpus_id"] == _CORPUS
    with pytest.raises(ma.UniverseAlreadyBoundToCorpusError):
        mc.register_bound_corpus_era(
            reopened, rig["uled"], corpus_id="r142-corpus-v3", universe_id=_UNIVERSE,
            registered_at="2026-03-11T00:00:00.000000Z",
        )


def test_a_different_universe_may_still_found_its_own_era(tmp_path):
    """The refusal must be narrow: it bars a second era on ONE universe, never a second era."""
    rig = _rig(tmp_path, _TEN)
    _register_universe(rig["uled"], _TEN, universe_id="second-universe",
                       registered_at="2026-03-05T00:00:00.000000Z")
    row = mc.register_bound_corpus_era(
        rig["registry"], rig["uled"], corpus_id="second-corpus", universe_id="second-universe",
        registered_at="2026-03-12T00:00:00.000000Z",
    )
    assert row["universe_id"] == "second-universe"


# =====================================================================================================
# §2. RELEASE IS A PHYSICAL EXPOSURE EVENT
# =====================================================================================================


def test_release_precommits_the_exposure_before_the_dataset_is_servable(tmp_path):
    """The order is the safety property: the window's exposure row must exist before anything can
    read the released dataset's outcomes."""
    rig = _rig(tmp_path, _TEN)
    symbol, session_date = _first_releasable(rig)
    dataset_id = _dataset_id_for(rig, (symbol, session_date))
    assert _is_withheld(rig, dataset_id), "precondition: withheld"

    row = _release(rig, symbol, session_date, dataset_id=dataset_id)

    assert row["corpus_id"] == _CORPUS, "the corpus was RESOLVED, never supplied by the operator"
    assert row["exposure_window"] == session_date
    assert not _is_withheld(rig, dataset_id), "now servable"
    assert rig["registry"].is_exposed_before(
        corpus_id=_CORPUS, window=session_date, instant="2999-01-01T00:00:00.000000Z"
    ) is True, "the release burned the window"


def test_no_released_dataset_is_servable_before_its_exposure_entry_exists(tmp_path):
    """Proved by ORDER, not by inspection after the fact: a registry that refuses to append makes
    the release fail, and the dataset must still be withheld."""
    rig = _rig(tmp_path, _TEN)
    symbol, session_date = _first_releasable(rig)
    dataset_id = _dataset_id_for(rig, (symbol, session_date))

    class _RefusingRegistry:
        def __init__(self, inner):
            self._inner = inner

        def all_rows(self):
            return self._inner.all_rows()

        def log_exposure(self, **kwargs):
            raise RuntimeError("ledger write failed")

    with pytest.raises(RuntimeError, match="ledger write failed"):
        vault.release_unselected_dataset(
            rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
            _RefusingRegistry(rig["registry"]),
            dataset_id=dataset_id, universe_id=_UNIVERSE, vault_secret=_SECRET,
            released_at="2026-03-04T00:00:00.000000Z",
        )
    assert _is_withheld(rig, dataset_id), (
        "the exposure append failed, so the dataset must NEVER have become servable"
    )


def test_a_crash_after_the_exposure_append_burns_the_evidence(tmp_path):
    """The acceptable failure direction, made explicit. A crash between the two appends leaves the
    window exposed and the dataset withheld: evidence destroyed, never contamination hidden."""
    rig = _rig(tmp_path, _TEN)
    symbol, session_date = _first_releasable(rig)
    dataset_id = _dataset_id_for(rig, (symbol, session_date))

    class _CrashAfterExposure:
        def __init__(self, inner):
            self._inner = inner

        def all_rows(self):
            return self._inner.all_rows()

        def log_exposure(self, **kwargs):
            self._inner.log_exposure(**kwargs)
            raise KeyboardInterrupt("power lost between the two ledgers")

    with pytest.raises(KeyboardInterrupt):
        vault.release_unselected_dataset(
            rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
            _CrashAfterExposure(rig["registry"]),
            dataset_id=dataset_id, universe_id=_UNIVERSE, vault_secret=_SECRET,
            released_at="2026-03-04T00:00:00.000000Z",
        )
    assert _is_withheld(rig, dataset_id), "no release row landed"
    assert rig["registry"].is_exposed_before(
        corpus_id=_CORPUS, window=session_date, instant="2999-01-01T00:00:00.000000Z"
    ) is True, "the window is burned anyway -- evidence destroyed, which is the safe direction"
    # And the consequence a later spec actually sees: this window can never again read as fresh.
    assert wf.classify_evidence_class(
        rig["registry"], corpus_id=_CORPUS, window_sessions=[session_date],
        registered_at="2026-12-01T00:00:00.000000Z",
    ) == wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC


def test_a_spec_frozen_before_the_release_may_still_receive_oos(tmp_path):
    """T1 < T2: the pre-frozen hypothesis is exactly what an OOS campaign is for."""
    rig = _rig(tmp_path, _TEN)
    symbol, session_date = _first_releasable(rig)
    _release(rig, symbol, session_date, released_at="2026-06-01T00:00:00.000000Z")
    assert wf.classify_evidence_class(
        rig["registry"], corpus_id=_CORPUS, window_sessions=[session_date],
        registered_at="2026-05-01T00:00:00.000000Z",   # T1, before the release
    ) == wf.EVIDENCE_CLASS_HISTORICAL_OOS


def test_a_spec_frozen_after_the_release_sees_diagnostic(tmp_path):
    """T3 > T2: the same window, the same bytes, and permanently diagnostic. No special-casing --
    only timestamps and the existing rule."""
    rig = _rig(tmp_path, _TEN)
    symbol, session_date = _first_releasable(rig)
    _release(rig, symbol, session_date, released_at="2026-06-01T00:00:00.000000Z")
    assert wf.classify_evidence_class(
        rig["registry"], corpus_id=_CORPUS, window_sessions=[session_date],
        registered_at="2026-07-01T00:00:00.000000Z",   # T3, after the release
    ) == wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC


def test_a_release_under_a_universe_with_no_bound_corpus_refuses(tmp_path):
    """No binding means there is nowhere honest to record the exposure, so the act cannot proceed."""
    rig = _rig(tmp_path, _TEN, bind=False)
    symbol, session_date = _first_releasable(rig)
    dataset_id = _dataset_id_for(rig, (symbol, session_date))
    with pytest.raises(vault.UnboundReleaseCorpusError, match="founded no corpus era"):
        _release(rig, symbol, session_date, dataset_id=dataset_id)
    assert _is_withheld(rig, dataset_id), "a refused release changes nothing"


def test_release_exposure_is_deduped_per_corpus_and_session_window(tmp_path):
    """A healthy date carries several members. Releasing six symbols on one date is ONE exposure
    fact, not six."""
    rig = _rig(tmp_path, _TEN)
    releasable = sorted(tuple(p) for p in rig["plan"]["releasable"])
    date = releasable[0][1]
    same_date = [p for p in releasable if p[1] == date]
    assert len(same_date) >= 2, "fixture must give this date at least two releasable members"

    for symbol, session_date in same_date:
        _release(rig, symbol, session_date, dataset_id=_dataset_id_for(rig, (symbol, session_date)))

    rows = [
        r for r in rig["registry"].all_rows()
        if ma._is_exposure_row(r) and r.get("corpus_id") == _CORPUS and r.get("window") == date
    ]
    assert len(rows) == 1, f"{len(same_date)} releases on one date produced {len(rows)} exposure rows"
    assert rows[0]["surface"] == "vault_exploratory_release"


def test_a_later_exposure_row_does_not_discharge_an_earlier_release(tmp_path):
    """The dedupe is "already exposed AT OR BEFORE this instant", never merely "a row exists" -- a
    row stamped later would leave a gap a spec could be frozen into."""
    rig = _rig(tmp_path, _TEN)
    symbol, session_date = _first_releasable(rig)
    rig["registry"].log_exposure(
        corpus_id=_CORPUS, window=session_date, surface="something_later",
        logged_at="2027-01-01T00:00:00.000000Z",
    )
    _release(rig, symbol, session_date, released_at="2026-06-01T00:00:00.000000Z")
    assert rig["registry"].is_exposed_before(
        corpus_id=_CORPUS, window=session_date, instant="2026-06-02T00:00:00.000000Z"
    ) is True, "the release wrote its OWN earlier row rather than trusting the later one"


# =====================================================================================================
# §3. ONE REGISTERED POSITION = ONE SCIENTIFIC DATASET
# =====================================================================================================


def test_two_genuine_datasets_at_one_registered_pair_refuse_membership(tmp_path):
    """A retry leaves a second complete recording. No frozen supersession rule says which is THE
    recording, so membership fails closed rather than picking one."""
    rig = _rig(tmp_path, _TEN)
    symbol, session_date = _first_releasable(rig)
    _release(rig, symbol, session_date)
    duplicate = _record_dataset(rig["store"], symbol, session_date, seed=999.0)
    # The public release path already refuses this (proved by the next test), so the duplicate
    # is forced onto the ledger through the private append -- otherwise it stays an unresolved pool
    # member and never reaches membership resolution at all, and this test would prove nothing.
    vault._append_exploratory_release(
        rig["sled"], rig["uled"], rig["iled"],
        identity={
            "dataset_id": duplicate["id"], "symbol": symbol, "session_date": session_date,
            "content_checksum": duplicate["checksum"], "event_count": 12,
        },
        universe_id=_UNIVERSE, vault_secret=_SECRET, released_at="2026-03-05T00:00:00.000000Z",
    )
    with pytest.raises(mc.DuplicateCorpusPositionError, match="more than"):
        mc.eligible_oos_members(
            rig["registry"], rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
            corpus_id=_CORPUS, vault_secret=_SECRET,
        )


def test_a_second_dataset_at_an_already_released_pair_refuses_release(tmp_path):
    """The same invariant enforced at the WRITE boundary, so the duplicate never lands at all."""
    rig = _rig(tmp_path, _TEN)
    symbol, session_date = _first_releasable(rig)
    _release(rig, symbol, session_date)
    duplicate = _record_dataset(rig["store"], symbol, session_date, seed=999.0)
    with pytest.raises(vault.DuplicateReleasedPositionError, match="already held by dataset"):
        vault.release_unselected_dataset(
            rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"], rig["registry"],
            dataset_id=duplicate["id"], universe_id=_UNIVERSE, vault_secret=_SECRET,
            released_at="2026-03-05T00:00:00.000000Z",
        )
    assert _is_withheld(rig, duplicate["id"])


def test_a_duplicate_can_never_double_the_observation_count(tmp_path):
    """The consequence the refusals exist to prevent, stated as arithmetic: one registered position
    contributes exactly one member, so its session cluster is weighted once."""
    rig = _rig(tmp_path, _TEN)
    for symbol, session_date in sorted(tuple(p) for p in rig["plan"]["releasable"]):
        _release(rig, symbol, session_date, dataset_id=_dataset_id_for(rig, (symbol, session_date)))
    membership = mc.eligible_oos_members(
        rig["registry"], rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
        corpus_id=_CORPUS, vault_secret=_SECRET,
    )
    positions = [
        (vault._normalize_symbol(m["symbol"]), m["session_date"]) for m in membership["members"]
    ]
    assert len(positions) == len(set(positions)), "a position appeared twice in the manifest"
    assert membership["member_count"] == len(rig["plan"]["releasable"])


def test_the_manifest_positions_are_unique_by_symbol_and_session_date(tmp_path):
    """The manifest hash is over ``(dataset_id, checksum)``; this proves the POSITIONS behind it are
    themselves unique, which is what makes that hash mean one body of evidence."""
    rig = _rig(tmp_path, _TEN)
    for symbol, session_date in sorted(tuple(p) for p in rig["plan"]["releasable"]):
        _release(rig, symbol, session_date, dataset_id=_dataset_id_for(rig, (symbol, session_date)))
    membership = mc.eligible_oos_members(
        rig["registry"], rig["store"], rig["sled"], rig["uled"], rig["iled"], rig["pled"],
        corpus_id=_CORPUS, vault_secret=_SECRET,
    )
    seen = set()
    for m in membership["members"]:
        key = (vault._normalize_symbol(m["symbol"]), m["session_date"])
        assert key not in seen, f"duplicate registered position {key} in the manifest"
        seen.add(key)


# =====================================================================================================
# §5. THE DURABLE MODE B PREDECLARATION
# =====================================================================================================


def test_a_mode_b_predeclaration_is_a_hash_chained_row_written_before_any_release(tmp_path):
    """The whole ``historical_oos`` claim rests on the spec being ON DISK before the windows were
    exposed -- so the predeclaration must be durable, and it must precede the release."""
    rig = _rig(tmp_path, _TEN)
    ledger = wf.WalkForwardLedger(str(tmp_path / "wf"))
    spec = wf.register_mode_b_spec(
        corpus_id=_CORPUS, rule_id="divergence_at_level_bearish:trades_20:return_bps",
        sidedness="short", econ_floor={"unit": "return_bps", "value_bps": 3.0},
        registered_at="2026-05-01T00:00:00.000000Z",
    )
    row = wf.record_mode_b_predeclaration(ledger, spec)
    assert row["row_kind"] == "mode_b_spec"
    assert ledger.verify_chain()["ok"] is True
    for frozen in ("corpus_id", "rule_id", "sidedness", "econ_floor", "spec_hash", "registered_at"):
        assert row[frozen] == spec[frozen], f"{frozen} must be frozen into the durable row"

    symbol, session_date = _first_releasable(rig)
    _release(rig, symbol, session_date, released_at="2026-06-01T00:00:00.000000Z")
    assert wf.classify_evidence_class(
        rig["registry"], corpus_id=_CORPUS, window_sessions=[session_date],
        registered_at=row["registered_at"],
    ) == wf.EVIDENCE_CLASS_HISTORICAL_OOS


def test_an_identical_mode_b_replay_is_idempotent(tmp_path):
    ledger = wf.WalkForwardLedger(str(tmp_path / "wf"))
    spec = wf.register_mode_b_spec(
        corpus_id=_CORPUS, rule_id="r", sidedness="short", econ_floor=None,
        registered_at="2026-05-01T00:00:00.000000Z",
    )
    first = wf.record_mode_b_predeclaration(ledger, spec)
    again = wf.record_mode_b_predeclaration(
        ledger,
        wf.register_mode_b_spec(
            corpus_id=_CORPUS, rule_id="r", sidedness="short", econ_floor=None,
            registered_at="2026-09-09T00:00:00.000000Z",  # a later instant must not be recorded
        ),
    )
    assert again["registered_at"] == first["registered_at"]
    assert len(wf.mode_b_predeclarations_for_sequence(ledger, spec["sequence_id"])) == 1


def test_a_conflicting_mode_b_replay_refuses(tmp_path):
    """A changed promise is a NEW hypothesis. Appending it beside the original would leave two
    contradictory predeclarations for one sequence, and a reader free to pick."""
    ledger = wf.WalkForwardLedger(str(tmp_path / "wf"))
    wf.record_mode_b_predeclaration(ledger, wf.register_mode_b_spec(
        corpus_id=_CORPUS, rule_id="r", sidedness="short", econ_floor=None,
        registered_at="2026-05-01T00:00:00.000000Z",
    ))
    with pytest.raises(wf.ConflictingModeBPredeclarationError, match="already predeclared"):
        wf.record_mode_b_predeclaration(ledger, wf.register_mode_b_spec(
            corpus_id=_CORPUS, rule_id="r", sidedness="long",   # the flip
            econ_floor=None, registered_at="2026-05-02T00:00:00.000000Z",
        ))
    assert len(wf.mode_b_predeclarations_for_sequence(
        ledger, wf.sequence_id_for(_CORPUS, "r"))) == 1


def test_an_unsided_mode_b_spec_refuses():
    """Unsided is legal for an exploratory Scout candidate -- it is a question. Mode B is a claim,
    and an unsided claim passes its own test in either direction."""
    with pytest.raises(wf.UnsidedModeBSpecError, match="no sidedness"):
        wf.register_mode_b_spec(corpus_id=_CORPUS, rule_id="r", sidedness=None, econ_floor=None)
    # And the Scout boundary is deliberately unchanged.
    assert mf.validate_candidate_direction(None) is None


# =====================================================================================================
# §7. STUDY 2 -- THE CONTINUOUS REPRESENTATION
# =====================================================================================================


def _divergence(p1, p2, cd1, cd2, volumes):
    return mf.divergence_at_level(
        price_history=[(0.0, p1), (10.0, p2)], tau1=0.0, tau2=10.0,
        cum_delta_at_tau1=cd1, cum_delta_at_tau2=cd2, baseline_volumes=volumes,
    )


def test_price_extension_bps_hand_oracle():
    """100.00 -> 100.50 is +50 bps, by hand: 0.50/100.00 * 10_000."""
    out = _divergence(100.0, 100.5, 0.0, 0.0, [100.0] * 5)
    assert out["price_extension_bps"] == pytest.approx(50.0)
    # And a lower later extreme is negative, symmetric and by the same arithmetic.
    down = _divergence(100.0, 99.5, 0.0, 0.0, [100.0] * 5)
    assert down["price_extreme_tau2"] == 100.0, (
        "price_extreme_trailing takes the MAX over the trailing window, so a dip cannot lower it"
    )
    assert down["price_extension_bps"] == pytest.approx(0.0)


def test_delta_weakening_multiple_hand_oracle():
    """delta = 0.25 x median([100]*5) = 25.0; cd falls 1000 -> 0, so 1000/25 = 40 threshold-widths."""
    out = _divergence(100.0, 100.5, 1000.0, 0.0, [100.0] * 5)
    assert out["delta_volume_fraction_threshold"] == pytest.approx(25.0)
    assert out["delta_weakening_multiple"] == pytest.approx(40.0)
    # Exactly one threshold-width is exactly 1.0 -- Card 9.1's own bar, and inclusive.
    exact = _divergence(100.0, 100.5, 25.0, 0.0, [100.0] * 5)
    assert exact["delta_weakening_multiple"] == pytest.approx(1.0)
    assert exact["bearish_divergence"] is True


def test_an_undefined_denominator_returns_none_never_a_fabricated_number():
    """Two distinct undefined cases: too thin a baseline (<5 windows) and a zero median volume."""
    thin = _divergence(100.0, 100.5, 1000.0, 0.0, [100.0] * 4)
    assert thin["delta_volume_fraction_threshold"] is None
    assert thin["delta_weakening_multiple"] is None
    assert thin["bearish_divergence"] is None

    zero_volume = _divergence(100.0, 100.5, 1000.0, 0.0, [0.0] * 5)
    assert zero_volume["delta_volume_fraction_threshold"] == 0.0
    assert zero_volume["delta_weakening_multiple"] is None, (
        "zero is not a positive measured denominator -- never infinity, never a divide-by-zero"
    )
    assert zero_volume["bearish_divergence"] is True, (
        "the DISCLOSED asymmetry: Card 9.1's boolean is frozen and stays defined at delta == 0"
    )


@pytest.mark.parametrize(
    "p1,p2,cd1,cd2",
    [
        (100.0, 100.5, 1000.0, 0.0),      # both conjuncts
        (100.0, 100.5, 1000.0, 990.0),    # extended, but weakening below one threshold-width
        (100.0, 100.0, 1000.0, 0.0),      # weakened, but no further extension
        (100.0, 100.0, 1000.0, 999.0),    # neither
        (100.0, 100.5, 0.0, 1000.0),      # delta STRENGTHENED -- a negative multiple
    ],
)
def test_the_boolean_is_exactly_the_predeclared_corner_of_the_continuous_plane(p1, p2, cd1, cd2):
    """Card 9.1's semantics are unchanged: the boolean is one transform of the two coordinates,
    never an independent measurement."""
    out = _divergence(p1, p2, cd1, cd2, [100.0] * 5)
    ext, mult = out["price_extension_bps"], out["delta_weakening_multiple"]
    assert ext is not None and mult is not None
    assert out["bearish_divergence"] == (ext > 0 and mult >= 1)


def test_available_at_remains_tau2_and_no_lookahead_is_introduced():
    """The continuous coordinates are computed from the SAME two touches the boolean uses, so the
    instant the comparison becomes available cannot have moved."""
    out = _divergence(100.0, 100.5, 1000.0, 0.0, [100.0] * 5)
    assert out["available_at"] == out["tau2"] == 10.0
    # Nothing after tau2 can influence either coordinate.
    later = mf.divergence_at_level(
        price_history=[(0.0, 100.0), (10.0, 100.5), (99.0, 500.0)], tau1=0.0, tau2=10.0,
        cum_delta_at_tau1=1000.0, cum_delta_at_tau2=0.0, baseline_volumes=[100.0] * 5,
    )
    assert later["price_extension_bps"] == out["price_extension_bps"]
    assert later["delta_weakening_multiple"] == out["delta_weakening_multiple"]
    assert later["available_at"] == 10.0


def test_the_paired_touch_identity_is_unchanged():
    """Everything Card 9.1 already returned still comes back byte-identically."""
    out = _divergence(100.0, 100.5, 1000.0, 0.0, [100.0] * 5)
    for key, expected in (
        ("tau1", 0.0), ("tau2", 10.0), ("price_extreme_tau1", 100.0),
        ("price_extreme_tau2", 100.5), ("cum_delta_tau1", 1000.0), ("cum_delta_tau2", 0.0),
        ("delta_volume_fraction_threshold", 25.0), ("bearish_divergence", True),
        ("available_at", 10.0),
    ):
        assert out[key] == expected, f"{key} moved"


# =====================================================================================================
# §8. THE STUDY 2 DISCOVERY CONTRACT (capability only -- no real discovery is run)
# =====================================================================================================


def _anchor(session_date, symbol, ext, mult, outcome_bps):
    return {
        "session_date": session_date, "symbol": symbol,
        "price_extension_bps": ext, "delta_weakening_multiple": mult,
        "outcome_bps": outcome_bps, "outcome_unit": mf.OUTCOME_UNIT,
    }


# ---------------------------------------------------------------------------------------------------
# RETIRED BY r14.3. Four tests here pinned r14.2's home-made decision rail -- a 30-anchor floor
# borrowed from the WALK-FORWARD fold floor, and a verdict read off the mechanism-fired cell's own
# raw mean. Both were wrong, and the decision now delegates to `scout.screen_candidate`. Their
# replacements live in `test_micro_r14_3_study2_scout_rail.py` (cases A-I).
#
# The one below is kept, re-targeted, because the fixture it used is itself the clearest statement
# of what was broken.
# ---------------------------------------------------------------------------------------------------


def test_the_old_promising_fixture_had_no_comparator_at_all_and_is_now_insufficient():
    """**r14.2's own "PROMISING" fixture, replayed against the Scout rail.**

    Forty anchors, every one of them firing, no comparator cell in existence -- and the retired rail
    scored it ``PROMISING_FOR_MODE_B_FREEZE`` because 40 >= its 30-anchor floor and the fired cell's
    raw mean was -9 bps. There was nothing to compare -9 against. Scout refuses on its own cell
    floor, which is what a sufficiency rule is for."""
    anchors = [
        _anchor(f"2026-04-{(i % 12) + 1:02d}", ["AAPL", "MSFT", "SPY"][i % 3], 10.0, 2.0, -9.0)
        for i in range(40)
    ]
    for a in anchors:                      # the Scout screen reads the thresholded feature value
        a["feature_value"] = 1.0
        a.setdefault("tod_bucket", "midday")      # disclosure slices the screen always reports
        a.setdefault("fallback_frac", 0.0)
    assert all(a["price_extension_bps"] > 0 and a["delta_weakening_multiple"] >= 1 for a in anchors)

    screen = scout.screen_candidate(
        feature_name="divergence_at_level_bearish", transform="threshold",
        params={"op": "ge", "value": 1.0}, sidedness=None, horizon_key="trades_20",
        econ_floor={
            "multiple": scout.ECON_FLOOR_SPREAD_MULTIPLE, "family_median_spread_bps": 1.0,
            "floor_bps": 1.0, "unit": mf.BPS_UNIT, "proxy_sentence": scout.ECON_PROXY_SENTENCE,
        },
        anchors=anchors, family_id="r142-retired-fixture", n_variants_tried=1,
    )
    assert screen["screen_result"]["n_comparator"] == 0, "there was never anything to compare to"
    result = s2.study2_diagnostic(anchors, screen=screen)
    assert result["outcome"] == s2.OUTCOME_INSUFFICIENT
    assert result["proposed_direction"] is None
    # The continuous half is unchanged and still reports the cell honestly.
    assert result["mechanism_raw_return_bps"] == pytest.approx(-9.0)
    assert result["evidence_class"] == "historical_exposed_diagnostic"


def test_the_quadrants_reproduce_the_boolean_exactly_over_the_defined_domain():
    """``both`` IS ``bearish_divergence``: the boolean is a corner of this plane, not a second
    measurement."""
    anchors = [
        _anchor("2026-04-01", "AAPL", 10.0, 2.0, -1.0),    # both
        _anchor("2026-04-01", "MSFT", 10.0, 0.5, -1.0),    # extension only
        _anchor("2026-04-02", "SPY", -3.0, 2.0, -1.0),     # weakening only
        _anchor("2026-04-02", "AAPL", -3.0, 0.5, -1.0),    # neither
        _anchor("2026-04-03", "MSFT", None, 2.0, -1.0),    # undefined
    ]
    counts = s2.quadrant_counts(anchors)
    assert counts == {"both": 1, "extension_only": 1, "weakening_only": 1, "neither": 1,
                      "undefined": 1}


def test_an_undefined_coordinate_is_counted_and_excluded_never_imputed():
    """Substituting zero would silently move mass onto the very axis origin the boolean tests."""
    dist = s2.continuous_distribution([1.0, 2.0, 3.0, None, None])
    assert dist["n"] == 3 and dist["n_undefined"] == 2
    assert dist["median"] == 2.0


def test_the_conditional_raw_return_is_a_session_cluster_mean_not_a_flat_pooled_mean():
    """One busy session must not dominate -- the same aggregation §5.3 and the folds already use."""
    anchors = [
        _anchor("2026-04-01", "AAPL", 10.0, 2.0, -10.0),
        _anchor("2026-04-01", "AAPL", 10.0, 2.0, -10.0),
        _anchor("2026-04-01", "AAPL", 10.0, 2.0, -10.0),
        _anchor("2026-04-02", "MSFT", 10.0, 2.0, -2.0),
    ]
    out = s2.conditional_raw_return(anchors, lambda a: True)
    assert out["raw_return_bps"] == pytest.approx(-6.0), "mean of (-10, -2), not the pooled -8.0"
    assert out["n_sessions"] == 2 and out["n_symbols"] == 2


def test_an_outcome_in_the_wrong_unit_refuses_before_it_is_averaged():
    bad = [{**_anchor("2026-04-01", "AAPL", 10.0, 2.0, -5.0), "outcome_unit": "percent"}]
    with pytest.raises(mf.UnitMismatchError):
        s2.conditional_raw_return(bad, lambda a: True)


# =====================================================================================================
# §4. 105 DATES = THREE CONSTRUCTIBLE FOLDS. NOT THREE SUFFICIENT ONES.
# =====================================================================================================

_ONE_OH_FIVE = [f"2026-{m:02d}-{d:02d}" for m in range(1, 8) for d in range(1, 16)][:105]
_ECON_FLOOR = {"kind": "median_spread_multiple", "unit": "return_bps", "value_bps": 3.0}


def _observation(session_date, symbol, value_bps):
    return {
        "session_date": session_date, "symbol": symbol,
        "value": value_bps, "value_unit": wf.WF_OBSERVATION_UNIT,
    }


def test_one_hundred_and_five_dates_produce_exactly_three_constructible_folds():
    """The claim r14.1 actually proved, restated in the words that make its scope explicit. This is
    calendar arithmetic over the fold windows -- 40 train + 5 embargo + 20 test + 2 x 20 step -- and
    it says nothing whatever about whether any of those folds will hold enough evidence."""
    assert len(_ONE_OH_FIVE) == 105
    assert wf.minimum_sessions_for_constructible_folds(wf.DIAGNOSTIC_GEOMETRY) == 105
    folds = wf.build_folds(_ONE_OH_FIVE, wf.DIAGNOSTIC_GEOMETRY)
    assert len(folds) == wf.WF_MIN_SUFFICIENT_FOLDS == 3
    assert sum(len(f["test_sessions"]) for f in folds) == 60
    # 104 dates cannot, so 105 is exactly the boundary and not a rounded-up convenience.
    assert len(wf.build_folds(_ONE_OH_FIVE[:104], wf.DIAGNOSTIC_GEOMETRY)) == 2
    # And the deprecated alias still answers the same number for any existing caller.
    assert wf.minimum_sessions_for_sufficient_folds(wf.DIAGNOSTIC_GEOMETRY) == 105


def test_the_negative_case_105_dates_with_a_sparse_candidate_yields_no_sufficient_folds(tmp_path):
    """**The correction this section exists to make.** A sparse candidate fires on a handful of
    anchors across 105 dates. The calendar clears every floor; the evidence clears none. Three folds
    are constructed, zero are sufficient, and the sequence verdict REFUSES rather than computing a
    result over an insufficient sample."""
    folds = wf.build_folds(_ONE_OH_FIVE, wf.DIAGNOSTIC_GEOMETRY)
    assert len(folds) == 3, "constructible: the calendar is long enough"

    # Two anchors per fold on ONE symbol -- far below 30 observations / 8 signal sessions / 2 symbols.
    sparse = []
    for fold in folds:
        for session_date in fold["test_sessions"][:2]:
            sparse.append(_observation(session_date, "AAPL", -9.0))

    results = []
    for fold in folds:
        window = wf.observations_in_sessions(sparse, fold["test_sessions"],
                                            boundary_name="test_sessions")
        results.append({
            "fold_index": fold["fold_index"],
            **wf.summarize_fold_observations(window, {}),
        })

    summary = wf.fold_sufficiency_summary(results)
    assert summary["constructible_fold_count"] == 3
    assert summary["sufficient_fold_count"] == 0
    assert summary["meets_sequence_floor"] is False
    # Every fold names WHICH floor bit -- never a bare "insufficient".
    for shortfall in summary["shortfalls"]:
        assert set(shortfall["missing"]) >= {"observations", "signal_sessions", "symbols"}

    verdict = wf.sequence_verdict(results, sidedness="short", econ_floor=_ECON_FLOOR, voided=False)
    assert verdict["refused"] is True
    assert verdict["n_sufficient_folds"] == 0
    assert "3 sufficient folds" in verdict["reason"]


def test_the_positive_case_105_dates_with_dense_observations_can_reach_three_sufficient_folds(tmp_path):
    """The complement: sufficiency is reachable on 105 dates, but only when the OBSERVATIONS are
    there. Every fold clears all three per-fold floors, and every fold is ``historical_oos`` because
    the spec was frozen before any of its windows was exposed."""
    folds = wf.build_folds(_ONE_OH_FIVE, wf.DIAGNOSTIC_GEOMETRY)
    symbols = ["AAPL", "MSFT", "SPY", "NVDA"]
    dense = []
    for fold in folds:
        # 10 sessions x 4 symbols = 40 observations per fold: past 30 / 8 / 2 on every axis.
        for i, session_date in enumerate(fold["test_sessions"][:10]):
            for symbol in symbols:
                dense.append(_observation(session_date, symbol, -9.0))

    registry = _registry(tmp_path)
    ma.register_fresh_corpus_era(
        registry, corpus_id=_CORPUS, universe_id=_UNIVERSE,
        universe_registered_at=_REGISTERED_AT, rule_commitment="rc", vault_secret_commitment="vc",
        expected_pair_count=840, freshness_boundary=_REGISTERED_AT,
        registered_at="2026-03-03T00:00:00.000000Z",
    )
    ledger = wf.WalkForwardLedger(str(tmp_path / "wf"))
    spec = wf.register_mode_b_spec(
        corpus_id=_CORPUS, rule_id="dense-fixture-rule", sidedness="short",
        econ_floor=_ECON_FLOOR, registered_at="2026-05-01T00:00:00.000000Z",
    )
    spec = {**spec, "registered_at": wf.record_mode_b_predeclaration(ledger, spec)["registered_at"]}

    results = [
        wf.evaluate_mode_b_fold(ledger, registry, spec=spec, fold=fold, observations=dense,
                                floors={})
        for fold in folds
    ]

    summary = wf.fold_sufficiency_summary(results)
    assert summary["constructible_fold_count"] == 3
    assert summary["sufficient_fold_count"] == 3
    assert summary["meets_sequence_floor"] is True
    for row in results:
        assert row["n"] == 40 and row["n_sessions"] == 10 and row["n_symbols"] == 4
        assert row["evidence_class"] == wf.EVIDENCE_CLASS_HISTORICAL_OOS
        assert row["process_label"] == wf.PROCESS_LABEL_RULE

    verdict = wf.sequence_verdict(results, sidedness="short", econ_floor=_ECON_FLOOR, voided=False)
    assert verdict.get("refused") is not True, (
        "three sufficient historical_oos folds must reach a real verdict, not a floor refusal"
    )


def test_the_two_counts_are_never_conflated_in_the_reported_summary():
    """The reporting contract itself: a caller reading this dict cannot mistake one for the other."""
    mixed = [
        {"fold_index": 0, "status": wf.FOLD_STATUS_SUFFICIENT, "missing": {}},
        {"fold_index": 1, "status": wf.FOLD_STATUS_INSUFFICIENT, "missing": {"observations": "4 < 30"}},
        {"fold_index": 2, "status": wf.FOLD_STATUS_INSUFFICIENT, "missing": {"symbols": "1 < 2"}},
    ]
    summary = wf.fold_sufficiency_summary(mixed)
    assert summary["constructible_fold_count"] == 3
    assert summary["sufficient_fold_count"] == 1
    assert summary["insufficient_fold_count"] == 2
    assert summary["meets_sequence_floor"] is False
    assert [s["fold_index"] for s in summary["shortfalls"]] == [1, 2]


# =====================================================================================================
# §6. STUDIES 1 AND 3 ARE PARKED -- and must not be screened as their full stated mechanisms
# =====================================================================================================


def test_studies_one_and_three_are_parked_pending_an_owner_specification():
    """Not a coding gap. Each needs the OWNER to specify the missing mechanism -- what counts as
    "then", over what window, with what replenishment measure -- and inventing that here would be
    choosing the hypothesis after seeing the tape."""
    from app.research import micro_readiness as mr

    for study_id in ("range_wall_failed_aggression", "capitulation_exhaustion"):
        entry = mr.PILOT_STUDY_STATUS[study_id]
        assert entry["status"] == mr.STUDY_STATUS_PARKED_PENDING_OWNER_SPEC
        assert entry["missing"], "a parked study must name what is missing"
        assert entry["do_not"], "a parked study must name the proxy it must not be screened as"


def test_study_two_is_the_only_full_mechanism_ready_pilot_and_is_continuous_first():
    from app.research import micro_readiness as mr

    entry = mr.PILOT_STUDY_STATUS["delta_divergence_level_tests"]
    assert entry["status"] == mr.STUDY_STATUS_FULL_MECHANISM_READY
    assert "continuous" in entry["representation"]
    assert set(mr.PILOT_STUDY_STATUS) == set(mr.PILOT_STUDY_IDS), (
        "every pilot id must carry a status, and no status may name a study that does not exist"
    )


def test_the_readiness_floors_no_longer_claim_a_survivor_from_a_date_count():
    """The served contract itself: a met date-floor says folds are BUILDABLE, never that a survivor
    is reachable."""
    from app.research import micro_readiness as mr

    assert "does NOT guarantee" in mr.SUFFICIENCY_NOTE
    assert "misnomer" in mr.SUFFICIENCY_NOTE
    assert "survivor" not in mr.FLOOR_BASIS_NOTE, (
        "r14's note promised a survivor verdict from a session count"
    )


# =====================================================================================================
# §5 (operator). THE DURABLE PREDECLARATION STAGE -- dry by default, like every other real act
# =====================================================================================================


@pytest.fixture()
def operator(monkeypatch, tmp_path):
    import scripts.j06_operator as op

    saved = (op.UNIVERSE_ID, list(op.DATE_RULE), op.STATE_DIR, op.CORPUS_ID, op.COMMIT,
             op.RULE_ID, op.SIDEDNESS, op.ECON_FLOOR_BPS)
    op.UNIVERSE_ID = op.STARTER_UNIVERSE_ID
    op.DATE_RULE = list(op.STARTER_DATE_RULE)
    op.STATE_DIR = tmp_path / "artifacts"
    op.CORPUS_ID = op.RULE_ID = op.SIDEDNESS = op.ECON_FLOOR_BPS = None
    op.COMMIT = False
    # CONFIG is a frozen dataclass; the supported scoping hook is the env var it reads.
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    monkeypatch.setenv("TAPEOLOGY_MICRO_WALKFORWARD_DIR", str(tmp_path / "wf"))
    yield op
    (op.UNIVERSE_ID, op.DATE_RULE, op.STATE_DIR, op.CORPUS_ID, op.COMMIT,
     op.RULE_ID, op.SIDEDNESS, op.ECON_FLOOR_BPS) = saved


def _bind_starter_era(op, tmp_path):
    """The stage's own precondition: a bound corpus era for the universe being predeclared against."""
    uled = vault.VaultUniverseLedger(vault.resolve_vault_dir(str(tmp_path / "datasets")))
    vault.register_universe(
        uled, universe_id=op.UNIVERSE_ID, symbol_rule=list(op.SYMBOL_RULE),
        date_rule=list(op.DATE_RULE), vault_secret_commitment=vault.commit_vault_secret(_SECRET),
        registered_at=_REGISTERED_AT,
    )
    registry = _registry(tmp_path)
    mc.register_bound_corpus_era(
        registry, uled, corpus_id="op-corpus-v1", universe_id=op.UNIVERSE_ID,
        registered_at="2026-03-03T00:00:00.000000Z",
    )
    return registry


def test_the_predeclare_stage_is_dry_by_default_and_writes_nothing(operator, tmp_path):
    op = operator
    _bind_starter_era(op, tmp_path)
    op.CORPUS_ID, op.RULE_ID, op.SIDEDNESS = "op-corpus-v1", "some-rule", "short"
    out = op.stage_mode_b_predeclare()
    assert out["committed"] is False
    assert "DRY RUN" in out["note"]
    assert out["spec_hash"], "a dry run still reports the exact hash it WOULD freeze"
    ledger = wf.WalkForwardLedger(str(tmp_path / "wf"))
    assert ledger.all_rows() == [], "a dry run appends nothing"


def test_the_predeclare_stage_refuses_an_unsided_or_unbound_hypothesis(operator, tmp_path):
    op = operator
    _bind_starter_era(op, tmp_path)
    op.CORPUS_ID, op.RULE_ID, op.SIDEDNESS = "op-corpus-v1", "some-rule", None
    with pytest.raises(SystemExit, match="must be long or short"):
        op.stage_mode_b_predeclare()
    op.SIDEDNESS = "short"
    op.CORPUS_ID = "never-bound-corpus"
    with pytest.raises(SystemExit, match="not bound to a registered universe"):
        op.stage_mode_b_predeclare()


def test_the_committed_predeclaration_is_durable_and_refuses_a_changed_replay(operator, tmp_path):
    op = operator
    _bind_starter_era(op, tmp_path)
    op.CORPUS_ID, op.RULE_ID, op.SIDEDNESS, op.ECON_FLOOR_BPS = (
        "op-corpus-v1", "some-rule", "short", 3.0
    )
    op.COMMIT = True
    first = op.stage_mode_b_predeclare()
    assert first["committed"] is True and first["registered_at"]

    ledger = wf.WalkForwardLedger(str(tmp_path / "wf"))
    rows = wf.mode_b_predeclarations_for_sequence(ledger, first["sequence_id"])
    assert len(rows) == 1 and ledger.verify_chain()["ok"] is True
    assert rows[0]["econ_floor"]["value_bps"] == 3.0

    replay = op.stage_mode_b_predeclare()
    assert replay["registered_at"] == first["registered_at"], "an identical replay is idempotent"
    assert len(wf.mode_b_predeclarations_for_sequence(ledger, first["sequence_id"])) == 1

    op.SIDEDNESS = "long"  # the flip
    with pytest.raises(wf.ConflictingModeBPredeclarationError):
        op.stage_mode_b_predeclare()
