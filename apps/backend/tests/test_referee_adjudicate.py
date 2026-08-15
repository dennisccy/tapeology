"""``referee_adjudicate.py`` + the ``/research/desk/referee/{evaluations,evaluate,adjudications}*``
routes (Era 6 "The Referee", J-06) -- estimand engines and adjudication. Test-first contract: TC-1
through TC-37 in ``docs/phases/goal-referee-iter-7.md``.

Fixtures build REAL, internally-consistent signals by calling the imported rail's own
``desk_forward._measure_from`` directly against hand-built ``RawBar`` arrays (the
``test_referee_null.py`` precedent), then plant them into real ``PlaybookStore``/``BarStore``
instances through each store's own public write path, and build REAL matched-null records via
``referee_null.build_null_record``. Several estimand-math / fragility-trigger tests call this
module's own pooling/snapshot-building helpers DIRECTLY with hand-built inputs rather than
reverse-engineering bar prices to produce an exotic statistical outcome -- a precise, fast,
independent way to test the WIRING (does the fragility logic read the right fields) separately
from the arithmetic (already proven by ``test_referee_stats.py``/``test_referee_oracles.py``)."""

from __future__ import annotations

import datetime as dt
import json
import sys
import time as time_module
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

import app.research.referee_adjudicate as referee_adjudicate_module
from app.config import CONFIG
from app.main import app
from app.providers.adapters.base import RawBar
from app.research.bars import BarStore
from app.research.desk_forward import _measure_from
from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
from app.research.desk_playbook_features import side_sign
from app.research.referee_adjudicate import (
    REFEREE_GATE_VERSION,
    REFEREE_REGISTER,
    AdjudicationSnapshotStore,
    RefereeEvaluationComputeManager,
    RefereeEvaluationRunStore,
    RefereeEvaluationStore,
    _build_and_record_snapshot,
    _canonical,
    _family_bh_fold,
    _pool_against_null,
    _pool_cell_vs_complement,
    _sha256,
    adjudications_response,
    authorize_promotion,
    run_evaluation_and_record,
)
from app.research.referee_evidence import playbook_observations
from app.research.referee_null import (
    REFEREE_NULL_CONTEXT_SPEC_ID,
    REFEREE_NULL_TOD_SPEC_ID,
    REFEREE_TEST_PERM_SPEC_ID,
    RefereeNullStore,
    build_null_record,
)
from app.research.referee_registry import (
    CertificateStore,
    FamilyStore,
    HypothesisStore,
    WithdrawalStore,
    register_hypothesis,
    registry_response,
    withdraw_hypothesis,
)
from app.research.referee_routes import get_referee_eval_compute_manager
from app.research.referee_stats import run_oracle_attestation

_ET = ZoneInfo("America/New_York")


# --- fixture builders (real rail measurement + each store's own public write path) -----------------


def _iso(epoch: float) -> str:
    return (
        dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _session_open_epoch(session_date: str) -> float:
    day = dt.date.fromisoformat(session_date)
    return dt.datetime.combine(day, dt.time(9, 30), tzinfo=_ET).timestamp()


def _bars_flat_then_step(
    symbol: str, session_date: str, *, trigger_close: float, flat_close: float, count: int = 80,
) -> list[RawBar]:
    """``count`` 5m RTH bars starting 09:30 ET on ``session_date``: bar 0 = ``trigger_close``, bars
    1..count-1 = the CONSTANT ``flat_close`` -- enough bars (>=78) that the signal's own
    ``minutes_to_close`` reaches ``REFEREE_SESSION_COMPLETE_ET`` (15:55 ET), so the fixture counts
    as a completed-session record (spec Sec2). Every candidate null anchor (any bar in the "open"
    ToD bucket) then measures an IDENTICAL, exactly-zero "5m" return regardless of which subset the
    seeded draw picks -- a deterministic fixture whose expected T/p does not depend on WHICH 4
    anchors get drawn."""
    open_epoch = _session_open_epoch(session_date)
    bars = [RawBar(symbol, "5m", open_epoch, 100.0, 100.5, 99.5, trigger_close, 1000)]
    for i in range(1, count):
        bars.append(RawBar(symbol, "5m", open_epoch + i * 300.0, 100.0, 100.5, 99.5, flat_close, 1000))
    return bars


def _plant_bars(bar_store: BarStore, symbol: str, bars: list[RawBar]) -> None:
    bar_store.record(
        symbol=symbol, timeframe="5m", window_start_utc="2026-01-01T00:00:00Z",
        window_end_utc="2026-12-31T00:00:00Z", feed="test", bars=bars,
    )


def _plant_occurrence(
    playbook_store: PlaybookStore, bar_store: BarStore, symbol: str, session_date: str,
    bars: list[RawBar], *, setup_id: str = "capitulation", side: str = "long", signature: str | None = None,
) -> None:
    _plant_bars(bar_store, symbol, bars)
    sign = side_sign(side)
    forward = _measure_from(bars, 0, bars[0].close, "close", 5, sign)
    signal = {
        "setup_id": setup_id, "side": side, "symbol": symbol,
        "trigger_ts": _iso(bars[0].epoch), "entry": bars[0].close, "entry_kind": "close",
        "invalidation_price": bars[0].close - 0.5, "forward": forward,
        "invalidation_breached": False, "geometry": {"anchors": []},
    }
    playbook_store.record(
        session_date=session_date, config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature=signature or f"sig-{symbol}-{session_date}",
        payload_version=3, parameters=playbook_parameters(), register=PLAYBOOK_REGISTER,
        signals=[signal], absences=[], diagnostics=[],
    )


def _build_and_store_null(
    null_store: RefereeNullStore, observation: dict, *, playbook_store: PlaybookStore,
    bar_store: BarStore, null_spec_id: str = REFEREE_NULL_TOD_SPEC_ID,
) -> dict:
    fields = build_null_record(
        observation, null_spec_id=null_spec_id, playbook_store=playbook_store, bar_store=bar_store,
        config_fingerprint=CONFIG.config_fingerprint(),
    )
    return null_store.record(fields)


_REGISTERED_AT = "2026-06-10T12:00:00.000000Z"  # -> ET boundary "2026-06-10"
_BOUNDARY = "2026-06-10"


def _register_capitulation_hypothesis(
    family_store: FamilyStore, hypothesis_store: HypothesisStore, hypothesis_id: str, family_id: str,
    *, target_sessions: int = 12, min_occurrences: int = 12,
    null_spec_id: str | None = REFEREE_NULL_TOD_SPEC_ID, estimand: str = "A",
    setup_id: str = "capitulation", side: str = "long", context_predicate: dict | None = None,
    family_candidate_hypothesis_ids: list[str] | None = None, family_q: float = 0.10,
) -> dict:
    payload = {
        "hypothesis_id": hypothesis_id, "family_id": family_id, "family_q": family_q,
        "family_candidate_hypothesis_ids": family_candidate_hypothesis_ids or [hypothesis_id],
        "evidence_family": "playbook", "estimand": estimand, "setup_id": setup_id, "side": side,
        "context_predicate": context_predicate, "primary_measure_key": "5m", "primary_horizon": "5m",
        "sidedness": "greater", "null_spec_id": null_spec_id,
        "test_spec_id": REFEREE_TEST_PERM_SPEC_ID, "target_sessions": target_sessions,
        "min_occurrences": min_occurrences, "registered_at": _REGISTERED_AT,
    }
    return register_hypothesis(family_store, hypothesis_store, payload, confirm=True)


@pytest.fixture
def stores(tmp_path):
    bar_store = BarStore(tmp_path / "bars")
    playbook_store = PlaybookStore(tmp_path / "playbook")
    null_store = RefereeNullStore(tmp_path / "nulls")
    family_store = FamilyStore(tmp_path / "registry")
    hypothesis_store = HypothesisStore(tmp_path / "registry")
    evaluation_store = RefereeEvaluationStore(tmp_path / "eval")
    snapshot_store = AdjudicationSnapshotStore(tmp_path / "eval")
    run_store = RefereeEvaluationRunStore(tmp_path / "eval_runs")
    return {
        "bar_store": bar_store, "playbook_store": playbook_store, "null_store": null_store,
        "family_store": family_store, "hypothesis_store": hypothesis_store,
        "evaluation_store": evaluation_store, "snapshot_store": snapshot_store, "run_store": run_store,
    }


def _plant_known_corpus(
    stores: dict, hypothesis_id: str, family_id: str, *, n_sessions: int, trigger_close: float,
    flat_close: float, target_sessions: int = 12, min_occurrences: int = 12,
    start_index: int = 0,
) -> dict:
    """Plants ``n_sessions`` distinct, post-boundary, completed-session occurrences (one per
    UNIQUE symbol, avoiding any question of whether ``BarStore`` merges repeated ``record()`` calls
    for the same symbol across dates) plus their real matched-null records, and registers the
    hypothesis. Every session's own Delta_s is IDENTICAL by construction (module docstring) --
    ``trigger_close``/``flat_close`` fixes the sign/magnitude precisely."""
    hypothesis = _register_capitulation_hypothesis(
        stores["family_store"], stores["hypothesis_store"], hypothesis_id, family_id,
        target_sessions=target_sessions, min_occurrences=min_occurrences,
    )
    base = dt.date(2026, 7, 1)
    dates = [
        (base + dt.timedelta(days=i)).isoformat()
        for i in range(start_index, start_index + n_sessions)
    ]
    for i, date in enumerate(dates):
        symbol = f"{hypothesis_id[:6].upper()}{start_index + i}"
        bars = _bars_flat_then_step(
            symbol, date, trigger_close=trigger_close, flat_close=flat_close,
        )
        _plant_occurrence(stores["playbook_store"], stores["bar_store"], symbol, date, bars)
    projection = playbook_observations(stores["playbook_store"], CONFIG.config_fingerprint())
    for observation in projection["observations"]:
        if observation["measure_key"] == "5m" and observation["session_date"] in dates:
            _build_and_store_null(
                stores["null_store"], observation, playbook_store=stores["playbook_store"],
                bar_store=stores["bar_store"],
            )
    return hypothesis


def _run_eval(stores: dict, hypothesis_id: str, **overrides) -> dict:
    kwargs = dict(
        hypothesis_store=stores["hypothesis_store"], family_store=stores["family_store"],
        playbook_store=stores["playbook_store"], bar_store=stores["bar_store"], config=CONFIG,
        null_store=stores["null_store"], evaluation_store=stores["evaluation_store"],
        snapshot_store=stores["snapshot_store"], run_store=stores.get("run_store"),
    )
    kwargs.update(overrides)
    return run_evaluation_and_record(hypothesis_id, **kwargs)


# === the round trip: DoD fixture round-trip + TC-1 + TC-10/11/12 + checkpoint immutability ============


def test_known_positive_corpus_round_trip_checkpoints_corroborated(stores):
    """DoD: a synthetic known-positive family adjudicates ``corroborated`` end-to-end through the
    real registration -> null build -> evaluation -> snapshot code path. Also TC-1 (p < 0.05, T's
    sign matches "greater"), TC-10 (first eligible evaluation is the checkpoint, exactly one
    snapshot), TC-11 (a later evaluation is "monitoring", snapshot count stays at exactly 1), TC-12
    (two evaluations against an unchanged store share the identical evaluation_basis/attestation),
    and the DoD checkpoint-immutability clause (a later evaluation changes nothing served by
    ``adjudications_response()``, byte-identical across two successive calls)."""
    _plant_known_corpus(
        stores, "hyp-kp", "fam-kp", n_sessions=13, trigger_close=100.0, flat_close=102.0,
    )

    first = _run_eval(stores, "hyp-kp")
    assert first["cancelled"] is False
    record = first["record"]
    assert record["role"] == "checkpoint"
    assert record["confirmatory_eligible"] is True
    assert record["coverage"]["post_boundary_informative_sessions"] == 13
    # TC-1: the returned permutation_p is below 0.05 and T's sign matches "greater".
    assert record["permutation_p"] < 0.05
    assert record["T"] > 0.0
    # Every session's own Δ_s is identical (module docstring) -- entry-basis (close-anchored at the
    # SAME trigger bar the signal's own `entry`/`entry_kind` already used) reproduces the identical
    # value, so no fragility trigger fires from it.
    assert record["entry_basis_sign_flip"] is False
    assert record["equal_weight_T"] == pytest.approx(record["T"])
    assert record["ci_cluster"][0] <= record["ci_cluster"][1]
    assert record["ci_cluster"][0] > 0.0  # the degenerate CI excludes zero -- no cluster trigger

    snapshots, errors = stores["snapshot_store"].list()
    assert errors == []
    assert len(snapshots) == 1
    snapshot = first["snapshot"]
    assert snapshot is not None
    assert snapshot["verdict"] == "corroborated"
    assert snapshot["fragility_triggers"] == []
    assert snapshot["bh"]["bh_pass"] is True

    config_fingerprint = CONFIG.config_fingerprint()
    fold_before = adjudications_response(
        hypothesis_store=stores["hypothesis_store"], snapshot_store=stores["snapshot_store"],
        playbook_store=stores["playbook_store"], config_fingerprint=config_fingerprint,
    )
    entry_before = next(e for e in fold_before["entries"] if e["hypothesis_id"] == "hyp-kp")
    assert entry_before["verdict"] == "corroborated"

    # TC-12: a second evaluation act against the UNCHANGED store reuses the identical basis/
    # attestation (this module's own dedup path -- no fresh Monte Carlo re-run).
    second = _run_eval(stores, "hyp-kp")
    assert second["reused"] is True
    assert second["record"]["evaluation_basis"] == record["evaluation_basis"]
    assert second["record"]["attestation"] == record["attestation"]

    # TC-11: accrue a 14th post-boundary session, then evaluate AGAIN -- role is "monitoring", and
    # the snapshot store's own record count for this hypothesis stays at exactly 1.
    symbol14 = "HYPKP113"
    bars14 = _bars_flat_then_step(symbol14, "2026-07-14", trigger_close=100.0, flat_close=102.0)
    _plant_occurrence(stores["playbook_store"], stores["bar_store"], symbol14, "2026-07-14", bars14)
    projection = playbook_observations(stores["playbook_store"], config_fingerprint)
    new_observation = next(
        o for o in projection["observations"]
        if o["measure_key"] == "5m" and o["session_date"] == "2026-07-14"
    )
    _build_and_store_null(
        stores["null_store"], new_observation, playbook_store=stores["playbook_store"],
        bar_store=stores["bar_store"],
    )
    third = _run_eval(stores, "hyp-kp")
    assert third["reused"] is False  # coverage genuinely changed -- a new evaluation_basis
    assert third["record"]["role"] == "monitoring"
    assert third["record"]["coverage"]["post_boundary_informative_sessions"] == 14
    snapshots_after, errors_after = stores["snapshot_store"].list()
    assert errors_after == []
    assert len(snapshots_after) == 1  # still exactly one -- the monitoring run wrote no snapshot
    assert snapshots_after[0]["snapshot_id"] == snapshot["snapshot_id"]

    # DoD checkpoint immutability: `adjudications_response()`'s entry for this hypothesis is
    # BYTE-IDENTICAL to what it served before the monitoring run -- and byte-stable across two
    # successive calls against this (now unchanged) store (TC-23).
    fold_after_1 = adjudications_response(
        hypothesis_store=stores["hypothesis_store"], snapshot_store=stores["snapshot_store"],
        playbook_store=stores["playbook_store"], config_fingerprint=config_fingerprint,
    )
    entry_after_1 = next(e for e in fold_after_1["entries"] if e["hypothesis_id"] == "hyp-kp")
    assert entry_after_1 == entry_before
    fold_after_2 = adjudications_response(
        hypothesis_store=stores["hypothesis_store"], snapshot_store=stores["snapshot_store"],
        playbook_store=stores["playbook_store"], config_fingerprint=config_fingerprint,
    )
    assert fold_after_2 == fold_after_1


def test_known_null_corpus_round_trip_adjudicates_no_evidence(stores):
    """DoD: a synthetic known-null family (occurrence values identical to their matched-null
    anchors in every session -- T == 0.0 exactly) adjudicates ``no_evidence``."""
    _plant_known_corpus(
        stores, "hyp-kn", "fam-kn", n_sessions=13, trigger_close=100.0, flat_close=100.0,
    )
    result = _run_eval(stores, "hyp-kn")
    record = result["record"]
    assert record["role"] == "checkpoint"
    assert record["T"] == 0.0
    assert record["permutation_p"] > 0.10  # nowhere near the registered q -- BH must reject
    snapshot = result["snapshot"]
    assert snapshot["verdict"] == "no_evidence"
    assert snapshot["bh"]["bh_pass"] is False


# === TC-7, TC-8, TC-9: evaluation as an operator act, and the pre-boundary counter-test ================


def test_tc7_zero_post_boundary_sessions_is_pending_with_no_permutation_p(stores):
    _register_capitulation_hypothesis(stores["family_store"], stores["hypothesis_store"], "hyp-tc7", "fam-tc7")
    result = _run_eval(stores, "hyp-tc7")
    record = result["record"]
    assert record["role"] == "pending"
    assert record["confirmatory_eligible"] is False
    assert record["permutation_p"] is None
    assert record["T"] is None


def test_tc8_a_pre_boundary_and_deep_backfilled_record_never_contributes(stores):
    """TC-8: a record whose ``session_date`` is on/before the boundary -- including one recorded
    (``recorded_at``, the store's own real wall-clock stamp) well AFTER the hypothesis's own
    ``registered_at`` (2026-06-10) -- never contributes to coverage or T. Plants an ON-boundary date
    and a deep-backfilled OLD date (2026-05-01, planted by THIS test run, whose real ``recorded_at``
    is today's wall clock -- always after any fixed 2026 registration instant)."""
    _register_capitulation_hypothesis(stores["family_store"], stores["hypothesis_store"], "hyp-tc8", "fam-tc8")
    on_boundary_bars = _bars_flat_then_step("TC8A", _BOUNDARY, trigger_close=100.0, flat_close=102.0)
    _plant_occurrence(stores["playbook_store"], stores["bar_store"], "TC8A", _BOUNDARY, on_boundary_bars)
    deep_backfilled_bars = _bars_flat_then_step("TC8B", "2026-05-01", trigger_close=100.0, flat_close=102.0)
    _plant_occurrence(stores["playbook_store"], stores["bar_store"], "TC8B", "2026-05-01", deep_backfilled_bars)

    result = _run_eval(stores, "hyp-tc8")
    record = result["record"]
    assert record["coverage"]["post_boundary_informative_sessions"] == 0
    assert record["coverage"]["occurrences_pooled"] == 0
    assert record["role"] == "pending"


def test_tc9_below_target_reports_the_real_recount_never_the_registry_proxy(stores):
    """TC-9: below ``target_sessions``, ``coverage.post_boundary_informative_sessions`` is the real
    recomputed count (5 real sessions here), never any registry accrual proxy, and ``role`` is
    "pending"."""
    _plant_known_corpus(
        stores, "hyp-tc9", "fam-tc9", n_sessions=5, trigger_close=100.0, flat_close=102.0,
        target_sessions=12, min_occurrences=12,
    )
    result = _run_eval(stores, "hyp-tc9")
    record = result["record"]
    assert record["coverage"]["post_boundary_informative_sessions"] == 5
    assert record["role"] == "pending"
    assert record["confirmatory_eligible"] is False


def test_tc13_an_extra_payload_field_never_influences_the_recorded_coverage(stores):
    """TC-13 (route level): a ``POST .../evaluate`` body carrying an extra
    ``post_boundary_informative_sessions`` field is ignored -- pydantic's own default
    ``extra="ignore"`` behaviour -- the server always recomputes coverage itself."""
    _plant_known_corpus(
        stores, "hyp-tc13", "fam-tc13", n_sessions=5, trigger_close=100.0, flat_close=102.0,
    )
    app.dependency_overrides.clear()
    from app.research.referee_routes import (
        get_referee_eval_run_store,
        get_referee_eval_store,
        get_referee_family_store,
        get_referee_hypothesis_store,
        get_referee_null_store,
        get_referee_snapshot_store,
    )
    from app.research.desk_routes import get_playbook_store
    from app.research.routes import get_bar_store

    app.dependency_overrides[get_referee_hypothesis_store] = lambda: stores["hypothesis_store"]
    app.dependency_overrides[get_referee_family_store] = lambda: stores["family_store"]
    app.dependency_overrides[get_playbook_store] = lambda: stores["playbook_store"]
    app.dependency_overrides[get_bar_store] = lambda: stores["bar_store"]
    app.dependency_overrides[get_referee_null_store] = lambda: stores["null_store"]
    app.dependency_overrides[get_referee_eval_store] = lambda: stores["evaluation_store"]
    app.dependency_overrides[get_referee_snapshot_store] = lambda: stores["snapshot_store"]
    app.dependency_overrides[get_referee_eval_run_store] = lambda: stores["run_store"]
    try:
        with TestClient(app) as client:
            resp = client.post(
                "/research/desk/referee/evaluate",
                json={"hypothesis_id": "hyp-tc13", "post_boundary_informative_sessions": 999},
            )
            assert resp.status_code == 200
            assert resp.json()["started"] is True
            _wait_for_manager(
                get_referee_eval_compute_manager, "hyp-tc13",
            )
    finally:
        app.dependency_overrides.clear()
    records = stores["evaluation_store"].list_for_hypothesis("hyp-tc13")
    assert len(records) == 1
    assert records[0]["coverage"]["post_boundary_informative_sessions"] == 5  # never 999


def test_post_evaluate_unknown_hypothesis_id_is_refused_422_no_job_started(stores):
    app.dependency_overrides.clear()
    from app.research.referee_routes import get_referee_hypothesis_store

    app.dependency_overrides[get_referee_hypothesis_store] = lambda: stores["hypothesis_store"]
    try:
        with TestClient(app) as client:
            resp = client.post(
                "/research/desk/referee/evaluate", json={"hypothesis_id": "no-such-hypothesis"},
            )
            assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()
    assert stores["evaluation_store"].list()[0] == []


def _wait_for_manager(dependency_getter, hypothesis_id, timeout: float = 10.0):
    manager = app.dependency_overrides.get(dependency_getter, dependency_getter)()
    deadline = time_module.monotonic() + timeout
    while time_module.monotonic() < deadline:
        snap = manager.snapshot(hypothesis_id)
        if snap["status"] not in ("running", "cancelling"):
            return snap
        time_module.sleep(0.01)
    raise AssertionError("referee evaluation compute never reached a terminal state")


# === estimand pooling: TC-2, TC-3, TC-4 (unit-level, hand-built inputs) ================================


class _FakeContextResolver:
    """The wall at [99.9, 100.1]: prices near it resolve ``at_wall``, prices far from it resolve
    ``off_wall`` (the ``test_referee_null.py`` ``_FakeResolver`` pattern)."""

    def resolve(self, symbol, as_of_epoch):
        return {
            "bands": [
                {
                    "side": "support", "class": "A", "price_low": 99.9, "price_high": 100.1,
                    "quality_score": 1.0, "round_number": False, "member_count": 1,
                }
            ],
            "basis_as_of": "2026-06-21",
        }


def _b_occurrence(observation_id: str, session_date: str, *, entry: float, value: float) -> dict:
    return {
        "observation_id": observation_id, "session_date": session_date, "symbol": "TC2",
        "value": value, "side": "long", "anchor_ts": _iso(_session_open_epoch(session_date)),
        "measure_key": "1h", "signal": {"entry": entry, "invalidation_price": entry - 0.5},
    }


def test_tc2_estimand_b_only_the_dual_group_sessions_enter_t(stores):
    """TC-2: 10 sessions carrying BOTH the context cell (entry near the wall) and its complement
    (entry far from the wall), plus 4 sessions carrying only ONE group -- only the 10 dual-group
    sessions enter ``T``, and ``coverage.one_group_sessions_excluded`` equals 4."""
    hypothesis = {"context_predicate": {"backing_bucket": "at_wall"}}
    occurrences = []
    for i in range(10):
        date = f"2026-08-{i + 1:02d}"
        occurrences.append(_b_occurrence(f"obs-cell-{i}", date, entry=100.0, value=1.0))
        occurrences.append(_b_occurrence(f"obs-comp-{i}", date, entry=105.0, value=-0.5))
    for i in range(4):
        date = f"2026-08-{20 + i:02d}"
        occurrences.append(_b_occurrence(f"obs-onlycell-{i}", date, entry=100.0, value=1.0))

    pool = _pool_cell_vs_complement(occurrences, hypothesis, _FakeContextResolver())
    assert pool["informative_sessions"] == 10
    assert pool["one_group_sessions_excluded"] == 4
    assert len(pool["session_groups"]) == 10
    for cell_values, complement_values in pool["session_groups"].values():
        assert cell_values == [1.0]
        assert complement_values == [-0.5]


def test_tc3_estimand_c_zero_eligible_context_null_anchors_pools_nothing(stores):
    """TC-3: every occurrence's OWN context-matched-null record reports zero eligible anchors
    (``referee_null.py``'s own ``backing_bucket_eligibility_rate: None`` disclosure) -- the pool
    counts zero informative sessions from that cell, never a fabricated p from zero anchors."""
    null_store = stores["null_store"]
    signature = referee_adjudicate_module.null_context_spec_signature()
    occurrences = []
    for i in range(3):
        obs_id = f"playbook:rec{i}:0:1h"
        occurrences.append(
            {
                "observation_id": obs_id, "session_date": f"2026-08-{i + 1:02d}", "symbol": "TC3",
                "value": 1.0, "side": "long", "anchor_ts": _iso(_session_open_epoch(f"2026-08-{i+1:02d}")),
                "measure_key": "1h", "signal": {},
            }
        )
        null_store.record(
            {
                "null_record_id": _sha256(_canonical([obs_id, signature]))[:16],
                "null_spec_id": REFEREE_NULL_CONTEXT_SPEC_ID, "null_spec_signature": signature,
                "observation_id": obs_id, "symbol": "TC3", "session_date": f"2026-08-{i+1:02d}",
                "side": "long", "tod_bucket": "open", "k_requested": 4, "k_drawn": 0,
                "eligible_count": 0, "excluded": True, "anchors": [], "mean_window_overlap": None,
                "non_finite_excluded_count": 0, "backing_bucket_eligibility_rate": None,
                "context_algorithm_version": "playbook-band-context-v3",
                "provenance": {"config_fingerprint": CONFIG.config_fingerprint(), "computed_at": _iso(0)},
            }
        )
    pool = _pool_against_null(occurrences, null_store, REFEREE_NULL_CONTEXT_SPEC_ID)
    assert pool["informative_sessions"] == 0
    assert pool["occurrences_pooled"] == 0
    assert pool["session_groups"] == {}


def test_tc4_below_min_clusters_for_ci_serves_the_insufficient_sample_literal(stores):
    """TC-4: below ``REFEREE_MIN_CLUSTERS_FOR_CI`` (8) informative sessions, ``ci_cluster`` is the
    literal string ``"insufficient_sample"``, never a numeric interval -- exercised through the
    real evaluation wiring (this module's own field-serving logic), not a bare
    ``referee_stats.bootstrap_ci_cluster`` call (already covered by J-03's own suite)."""
    _plant_known_corpus(
        stores, "hyp-tc4", "fam-tc4", n_sessions=3, trigger_close=100.0, flat_close=102.0,
    )
    result = _run_eval(stores, "hyp-tc4")
    assert result["record"]["ci_cluster"] == "insufficient_sample"


# === TC-5, TC-6, TC-17, TC-18, TC-19: fragility triggers + verdict, via the snapshot builder ===========


def _hand_built_checkpoint_evaluation(
    stores: dict, hypothesis_id: str, family_id: str, *, permutation_p: float, T: float,
    equal_weight_T: float, entry_basis_sign_flip: bool, ci_cluster,
) -> dict:
    """Directly records ONE ``role == "checkpoint"`` evaluation with HAND-CHOSEN numeric fields --
    tests the fragility-trigger/verdict WIRING precisely (does it read the right fields the right
    way) independent of whether some exotic bar-price fixture happens to produce them. The caller
    is responsible for having already registered ``hypothesis_id``'s own family/hypothesis."""
    fields = {
        "hypothesis_id": hypothesis_id, "family_id": family_id, "evaluated_at": _iso(0),
        "evidence_family": "playbook", "estimand": "A", "evaluation_basis": f"basis-{hypothesis_id}",
        "coverage": {
            "post_boundary_informative_sessions": 12, "target_sessions": 12, "min_occurrences": 12,
            "occurrences_pooled": 12, "one_group_sessions_excluded": 0,
        },
        "confirmatory_eligible": True, "role": "checkpoint",
        "T": T, "permutation_p": permutation_p, "permutation_enumeration": False,
        "min_attainable_p": 1e-4, "ci_occurrence": [0.1, 0.9], "ci_cluster": ci_cluster,
        "sign_flip_p": 0.5, "equal_weight_T": equal_weight_T,
        "entry_basis_T": -T if entry_basis_sign_flip else T,
        "entry_basis_sign_flip": entry_basis_sign_flip,
        "attestation": run_oracle_attestation(),
        "provenance": {"config_fingerprint": CONFIG.config_fingerprint(), "computed_at": _iso(0)},
    }
    return stores["evaluation_store"].record(fields)


def test_tc5_entry_basis_sign_flip_triggers_fragile(stores):
    _register_capitulation_hypothesis(
        stores["family_store"], stores["hypothesis_store"], "hyp-tc5", "fam-tc5",
    )
    recorded = _hand_built_checkpoint_evaluation(
        stores, "hyp-tc5", "fam-tc5", permutation_p=0.001, T=1.0, equal_weight_T=1.0,
        entry_basis_sign_flip=True, ci_cluster=[0.5, 1.5],
    )
    snapshot = _build_and_record_snapshot(
        recorded, family_store=stores["family_store"], evaluation_store=stores["evaluation_store"],
        snapshot_store=stores["snapshot_store"],
    )
    assert snapshot["fragility_triggers"] == ["entry_basis_sign_flip"]
    assert snapshot["verdict"] == "fragile"


def test_tc6_clustered_ci_including_zero_triggers_fragile(stores):
    _register_capitulation_hypothesis(
        stores["family_store"], stores["hypothesis_store"], "hyp-tc6", "fam-tc6",
    )
    recorded = _hand_built_checkpoint_evaluation(
        stores, "hyp-tc6", "fam-tc6", permutation_p=0.001, T=1.0, equal_weight_T=1.0,
        entry_basis_sign_flip=False, ci_cluster=[-0.2, 1.5],
    )
    snapshot = _build_and_record_snapshot(
        recorded, family_store=stores["family_store"], evaluation_store=stores["evaluation_store"],
        snapshot_store=stores["snapshot_store"],
    )
    assert snapshot["fragility_triggers"] == ["cluster_ci_includes_zero"]
    assert snapshot["verdict"] == "fragile"


def test_tc17_by_fail_triggers_fragile_never_corroborated(stores):
    """TC-17: BH passes (single-hypothesis family, m=1, any p <= q passes trivially) but the BY
    adjusted p fails at the same q -- a p just barely under q, at m=1, gives
    ``by_adjusted_p == p`` (c(1) == 1) so a p ABOVE q would make BOTH fail simultaneously; the BY
    disclosure only diverges from BH within a MULTI-candidate family. Uses a 2-hypothesis family
    where the sibling's own p is 1.0 (never evaluated) -- BH's rank-1 threshold is q/2, so a p just
    under q/2 still passes BH at rank 1, while BY's c(2)=1.5 correction pushes the SAME p's
    adjusted value above q."""
    family_id = "fam-tc17"
    q = 0.10
    # BH rank-1 threshold at m=2: (1/2)*q = 0.05. p = 0.045 passes BH (0.045 <= 0.05).
    # BY: by_adjusted_p(rank=1) = min(1, c(2)*m*p/rank) = min(1, 1.5*2*0.045/1) = 0.135 > q=0.10.
    p = 0.045
    _register_capitulation_hypothesis(
        stores["family_store"], stores["hypothesis_store"], "hyp-tc17", family_id,
        family_q=q, family_candidate_hypothesis_ids=["hyp-tc17", "hyp-tc17-sib"],
    )
    recorded = _hand_built_checkpoint_evaluation(
        stores, "hyp-tc17", family_id, permutation_p=p, T=1.0, equal_weight_T=1.0,
        entry_basis_sign_flip=False, ci_cluster=[0.5, 1.5],
    )
    snapshot = _build_and_record_snapshot(
        recorded, family_store=stores["family_store"], evaluation_store=stores["evaluation_store"],
        snapshot_store=stores["snapshot_store"],
    )
    assert snapshot["bh"]["bh_pass"] is True
    assert snapshot["bh"]["by_pass"] is False
    assert snapshot["fragility_triggers"] == ["by_fail"]
    assert snapshot["verdict"] == "fragile"


def test_tc18_bh_pass_no_fragility_both_floors_met_is_corroborated(stores):
    _register_capitulation_hypothesis(
        stores["family_store"], stores["hypothesis_store"], "hyp-tc18", "fam-tc18",
    )
    recorded = _hand_built_checkpoint_evaluation(
        stores, "hyp-tc18", "fam-tc18", permutation_p=0.001, T=1.0, equal_weight_T=1.0,
        entry_basis_sign_flip=False, ci_cluster=[0.5, 1.5],
    )
    snapshot = _build_and_record_snapshot(
        recorded, family_store=stores["family_store"], evaluation_store=stores["evaluation_store"],
        snapshot_store=stores["snapshot_store"],
    )
    assert snapshot["fragility_triggers"] == []
    assert snapshot["verdict"] == "corroborated"


def test_tc19_bh_rejects_the_null_is_no_evidence(stores):
    _register_capitulation_hypothesis(
        stores["family_store"], stores["hypothesis_store"], "hyp-tc19", "fam-tc19",
    )
    recorded = _hand_built_checkpoint_evaluation(
        stores, "hyp-tc19", "fam-tc19", permutation_p=0.99, T=0.01, equal_weight_T=0.01,
        entry_basis_sign_flip=False, ci_cluster=[-0.5, 0.5],
    )
    snapshot = _build_and_record_snapshot(
        recorded, family_store=stores["family_store"], evaluation_store=stores["evaluation_store"],
        snapshot_store=stores["snapshot_store"],
    )
    assert snapshot["bh"]["bh_pass"] is False
    assert snapshot["verdict"] == "no_evidence"


# === TC-14, TC-15, TC-16: the family BH fold at a rank boundary =======================================


def test_tc14_bh_boundary_hand_computed_k_star_over_21_candidates(stores):
    """TC-14: 21 candidates (20 known-null + 1 known-positive) at q=0.10 -- the known-positive's
    own p sits EXACTLY at the (k*/m)*q threshold (p = q/m = 0.10/21). Hand-computed: k* = 1 (only
    the positive passes; the 20 nulls at p=0.99 sit far above every rank's own threshold, whose
    maximum is (21/21)*0.10 = 0.10)."""
    family = {"candidate_hypothesis_ids": [f"hyp-{i}" for i in range(21)], "q": 0.10}
    positive_p = 0.10 / 21  # exactly on the rank-1 boundary: p_(1) == (1/21)*0.10
    p_values = [positive_p] + [0.99] * 20

    positive = _family_bh_fold("hyp-0", family, p_values)
    assert positive["k_star"] == 1
    assert positive["m"] == 21
    assert positive["bh_pass"] is True

    for i in range(1, 21):
        null_result = _family_bh_fold(f"hyp-{i}", family, p_values)
        assert null_result["bh_pass"] is False, f"hyp-{i} unexpectedly passed BH"


def test_tc15_an_unevaluated_sibling_folds_as_p_equals_1_never_shrinking_m(stores):
    """TC-15: a family whose planned list includes one hypothesis still "registered" (never
    evaluated) when its 3 siblings checkpoint -- m still equals the family's full planned count
    (4, not 3), and the unevaluated candidate folds as p=1 in the BH input."""
    family_id = "fam-tc15"
    ids = ["hyp-tc15-a", "hyp-tc15-b", "hyp-tc15-c", "hyp-tc15-never-evaluated"]
    for hid in ids:
        _register_capitulation_hypothesis(
            stores["family_store"], stores["hypothesis_store"], hid, family_id,
            family_candidate_hypothesis_ids=ids, setup_id=f"setup-{hid}",
        )
    for hid, p in (("hyp-tc15-a", 0.001), ("hyp-tc15-b", 0.99), ("hyp-tc15-c", 0.99)):
        _hand_built_checkpoint_evaluation(
            stores, hid, family_id, permutation_p=p, T=1.0, equal_weight_T=1.0,
            entry_basis_sign_flip=False, ci_cluster=[0.5, 1.5],
        )
    family = stores["family_store"].get(family_id)
    p_values = referee_adjudicate_module._family_p_values(
        family, "hyp-tc15-a", 0.001, stores["evaluation_store"]
    )
    assert len(p_values) == 4  # m == 4, never shrunk to 3
    assert p_values[ids.index("hyp-tc15-never-evaluated")] == 1.0


def test_tc16_a_withdrawn_hypothesis_with_a_frozen_checkpoint_still_counts_toward_m(stores):
    """TC-16: a hypothesis withdrawn AFTER a post-boundary evaluation already exists (refused per
    J-05 -- so the withdrawal itself never lands, but the scenario this guards is "even if it
    somehow had", per spec Sec5's own "the hypothesis remains in m and folds as p=1 if NEVER
    evaluated" contrast) -- here, ALREADY evaluated, so its frozen checkpoint p-value still counts
    toward m regardless of any withdrawal-store state."""
    family_id = "fam-tc16"
    ids = ["hyp-tc16-a", "hyp-tc16-withdrawn"]
    for hid in ids:
        _register_capitulation_hypothesis(
            stores["family_store"], stores["hypothesis_store"], hid, family_id,
            family_candidate_hypothesis_ids=ids, setup_id=f"setup-{hid}",
        )
    _hand_built_checkpoint_evaluation(
        stores, "hyp-tc16-withdrawn", family_id, permutation_p=0.02, T=1.0, equal_weight_T=1.0,
        entry_basis_sign_flip=False, ci_cluster=[0.5, 1.5],
    )
    withdrawal_store = WithdrawalStore(stores["family_store"].root)
    withdraw_hypothesis(
        stores["hypothesis_store"], withdrawal_store, hypothesis_id="hyp-tc16-withdrawn",
        post_boundary_evaluation_exists=False,  # J-05's own injected-signal contract
    )
    family = stores["family_store"].get(family_id)
    p_values = referee_adjudicate_module._family_p_values(
        family, "hyp-tc16-a", 0.001, stores["evaluation_store"]
    )
    assert p_values[ids.index("hyp-tc16-withdrawn")] == 0.02  # NOT dropped, NOT folded to 1.0


# === TC-20 through TC-25: the read-side fold and verdict vocabulary ====================================


def test_tc20_zero_post_boundary_sessions_of_any_kind_is_registered(stores):
    _register_capitulation_hypothesis(stores["family_store"], stores["hypothesis_store"], "hyp-tc20", "fam-tc20")
    fold = adjudications_response(
        hypothesis_store=stores["hypothesis_store"], snapshot_store=stores["snapshot_store"],
        playbook_store=stores["playbook_store"], config_fingerprint=CONFIG.config_fingerprint(),
    )
    entry = next(e for e in fold["entries"] if e["hypothesis_id"] == "hyp-tc20")
    assert entry["verdict"] == "registered"


def test_tc21_a_retired_detector_basis_wins_regardless_of_other_state(stores, monkeypatch):
    _register_capitulation_hypothesis(stores["family_store"], stores["hypothesis_store"], "hyp-tc21", "fam-tc21")
    # Simulate a live detector-basis revision: the pinned hypothesis basis no longer matches.
    monkeypatch.setattr(
        referee_adjudicate_module, "current_playbook_detector_basis", lambda: "some-other-basis"
    )
    fold = adjudications_response(
        hypothesis_store=stores["hypothesis_store"], snapshot_store=stores["snapshot_store"],
        playbook_store=stores["playbook_store"], config_fingerprint=CONFIG.config_fingerprint(),
    )
    entry = next(e for e in fold["entries"] if e["hypothesis_id"] == "hyp-tc21")
    assert entry["verdict"] == "basis_retired"


def test_tc22_a_tampered_attestation_refuses_confirmatory_output(stores):
    """TC-22: a stored evaluation/snapshot record whose ``attestation.actual`` is test-mutated to
    no longer match ``attestation.expected`` folds to ``confirmatory_output_refused: True`` with a
    non-empty ``refusal_reason``, and ``verdict`` is never a confirmatory token."""
    _plant_known_corpus(
        stores, "hyp-tc22", "fam-tc22", n_sessions=13, trigger_close=100.0, flat_close=102.0,
    )
    result = _run_eval(stores, "hyp-tc22")
    assert result["snapshot"]["verdict"] == "corroborated"

    # Tamper the stored snapshot FILE directly: mutate attestation.actual, recompute the file
    # checksum so the load succeeds (this exercises attestation MISMATCH, not a raw integrity
    # failure).
    snapshot_path = stores["snapshot_store"]._path("hyp-tc22")
    data = json.loads(snapshot_path.read_text())
    data["record"]["meta"]["attestation"]["actual"]["permutation_p"] += 1.0
    data["file_checksum"] = _sha256(_canonical(data["record"]))
    snapshot_path.write_text(json.dumps(data))

    fold = adjudications_response(
        hypothesis_store=stores["hypothesis_store"], snapshot_store=stores["snapshot_store"],
        playbook_store=stores["playbook_store"], config_fingerprint=CONFIG.config_fingerprint(),
    )
    entry = next(e for e in fold["entries"] if e["hypothesis_id"] == "hyp-tc22")
    assert entry["confirmatory_output_refused"] is True
    assert entry["refusal_reason"]
    assert entry["verdict"] not in ("corroborated", "no_evidence", "fragile")
    assert entry["verdict"] == "insufficient_sample"


def test_tc23_two_successive_get_adjudications_calls_are_byte_identical(stores):
    _plant_known_corpus(
        stores, "hyp-tc23", "fam-tc23", n_sessions=5, trigger_close=100.0, flat_close=102.0,
    )
    kwargs = dict(
        hypothesis_store=stores["hypothesis_store"], snapshot_store=stores["snapshot_store"],
        playbook_store=stores["playbook_store"], config_fingerprint=CONFIG.config_fingerprint(),
    )
    first = adjudications_response(**kwargs)
    second = adjudications_response(**kwargs)
    assert first == second


def test_tc24_the_register_field_equals_referee_register_verbatim(stores):
    _register_capitulation_hypothesis(stores["family_store"], stores["hypothesis_store"], "hyp-tc24", "fam-tc24")
    fold = adjudications_response(
        hypothesis_store=stores["hypothesis_store"], snapshot_store=stores["snapshot_store"],
        playbook_store=stores["playbook_store"], config_fingerprint=CONFIG.config_fingerprint(),
    )
    assert fold["register"] == REFEREE_REGISTER
    assert fold["register"] == REFEREE_REGISTER  # a second read -- still verbatim, not regenerated


def test_tc25_zero_hypotheses_registered_returns_200_with_empty_lists(stores):
    registry = registry_response(
        family_store=stores["family_store"], hypothesis_store=stores["hypothesis_store"],
        withdrawal_store=WithdrawalStore(stores["family_store"].root),
        certificate_store=CertificateStore(stores["family_store"].root),
        playbook_store=stores["playbook_store"], config_fingerprint=CONFIG.config_fingerprint(),
    )
    assert registry["hypotheses"] == []
    fold = adjudications_response(
        hypothesis_store=stores["hypothesis_store"], snapshot_store=stores["snapshot_store"],
        playbook_store=stores["playbook_store"], config_fingerprint=CONFIG.config_fingerprint(),
    )
    assert fold["entries"] == []


# === TC-26, TC-27, TC-28: authorize_promotion ==========================================================


def _fixture_certificate(**overrides) -> dict:
    fields = {
        "certificate_id": "cert-1",
        "candidate": {"strategy_id": "structure_tape", "profile": "default"},
        "champion_identity_at_scan_time": {"strategy_id": "v1", "profile": "default"},
        "train_dataset": {"id": "ds-train", "checksum": "abc123", "split": "train"},
        "holdout_dataset": {"id": "ds-holdout", "checksum": "def456", "split": "holdout"},
        "config_fingerprint": CONFIG.config_fingerprint(),
        "gate_version": REFEREE_GATE_VERSION,
        "referee_parameters_hash": "0" * 16,
        "family_id": "fam-x", "hypothesis_id": "hyp-x",
        "gate_results": {"calibrated_p": 0.01, "bh_pass": True, "ci": [0.1, 0.9], "floors_met": True},
    }
    fields.update(overrides)
    return fields


def _live_scan_context_matching(cert: dict) -> dict:
    return {
        "champion_identity": cert["champion_identity_at_scan_time"],
        "train_dataset": cert["train_dataset"], "holdout_dataset": cert["holdout_dataset"],
        "config_fingerprint": cert["config_fingerprint"], "gate_version": cert["gate_version"],
        "referee_parameters_hash": cert["referee_parameters_hash"],
    }


def test_tc26_no_certificate_at_all_refuses(tmp_path):
    certificate_store = CertificateStore(tmp_path / "registry")
    result = authorize_promotion(
        {"strategy_id": "structure_tape", "profile": "default"}, certificate_store, {},
    )
    assert result == {"authorized": False, "refusal_class": "no_certificate", "reason": result["reason"]}
    assert result["reason"]


def test_tc27_a_stale_config_fingerprint_refuses(tmp_path):
    certificate_store = CertificateStore(tmp_path / "registry")
    cert = _fixture_certificate()
    certificate_store.record(cert)
    live = _live_scan_context_matching(cert)
    live["config_fingerprint"] = "some-other-fingerprint"
    result = authorize_promotion(cert["candidate"], certificate_store, live)
    assert result["authorized"] is False
    assert result["refusal_class"] == "stale"


def test_tc28_every_pin_matching_and_bh_pass_authorizes(tmp_path):
    certificate_store = CertificateStore(tmp_path / "registry")
    cert = _fixture_certificate()
    certificate_store.record(cert)
    live = _live_scan_context_matching(cert)
    result = authorize_promotion(cert["candidate"], certificate_store, live)
    assert result == {"authorized": True, "refusal_class": None, "reason": None}


def test_authorize_promotion_wrong_candidate_profile_refuses(tmp_path):
    certificate_store = CertificateStore(tmp_path / "registry")
    cert = _fixture_certificate()
    certificate_store.record(cert)
    live = _live_scan_context_matching(cert)
    result = authorize_promotion(
        {"strategy_id": "structure_tape", "profile": "aggressive"}, certificate_store, live,
    )
    assert result["authorized"] is False
    assert result["refusal_class"] == "wrong_candidate"


def test_authorize_promotion_mismatched_datasets_refuses(tmp_path):
    certificate_store = CertificateStore(tmp_path / "registry")
    cert = _fixture_certificate()
    certificate_store.record(cert)
    live = _live_scan_context_matching(cert)
    live["train_dataset"] = {"id": "ds-train-2", "checksum": "different", "split": "train"}
    result = authorize_promotion(cert["candidate"], certificate_store, live)
    assert result["authorized"] is False
    assert result["refusal_class"] == "mismatched_datasets"


def test_authorize_promotion_failed_gates_refuses(tmp_path):
    certificate_store = CertificateStore(tmp_path / "registry")
    cert = _fixture_certificate(gate_results={"calibrated_p": 0.5, "bh_pass": False, "ci": [-1, 1], "floors_met": True})
    certificate_store.record(cert)
    live = _live_scan_context_matching(cert)
    result = authorize_promotion(cert["candidate"], certificate_store, live)
    assert result["authorized"] is False
    assert result["refusal_class"] == "failed_gates"


def test_authorize_promotion_malformed_unverifiable_refuses(tmp_path):
    registry_dir = tmp_path / "registry"
    certificate_store = CertificateStore(registry_dir)
    cert = _fixture_certificate()
    certificate_store.record(cert)
    (registry_dir / "certificate-corrupt.json").write_text("not valid json")
    live = _live_scan_context_matching(cert)
    result = authorize_promotion(cert["candidate"], certificate_store, live)
    assert result["authorized"] is False
    assert result["refusal_class"] == "malformed_unverifiable"


def test_a_corrupted_snapshot_file_refuses_rather_than_silently_reverting_to_live(stores):
    """A hypothesis's OWN adjudication-snapshot file failing its integrity check must NEVER
    silently fall back to the live (pre-checkpoint) fold -- that would misrepresent an
    already-`corroborated` hypothesis as merely "pending". Folds to a dedicated refusal instead,
    named the same way TC-22's attestation-refusal case is."""
    _plant_known_corpus(
        stores, "hyp-corruptsnap", "fam-corruptsnap", n_sessions=13, trigger_close=100.0,
        flat_close=102.0,
    )
    result = _run_eval(stores, "hyp-corruptsnap")
    assert result["snapshot"]["verdict"] == "corroborated"

    snapshot_path = stores["snapshot_store"]._path("hyp-corruptsnap")
    snapshot_path.write_text("not valid json at all")

    fold = adjudications_response(
        hypothesis_store=stores["hypothesis_store"], snapshot_store=stores["snapshot_store"],
        playbook_store=stores["playbook_store"], config_fingerprint=CONFIG.config_fingerprint(),
    )
    entry = next(e for e in fold["entries"] if e["hypothesis_id"] == "hyp-corruptsnap")
    assert entry["confirmatory_output_refused"] is True
    assert entry["refusal_reason"]
    assert entry["verdict"] == "insufficient_sample"
    assert entry["snapshot"] is None  # never serves the unverifiable content


# === TC-30 (route-level): a corrupted evaluation file is surfaced, never a 500 =========================


def test_tc30_a_corrupted_evaluation_file_is_surfaced_in_integrity_errors(stores):
    _plant_known_corpus(
        stores, "hyp-tc30", "fam-tc30", n_sessions=5, trigger_close=100.0, flat_close=102.0,
    )
    _run_eval(stores, "hyp-tc30")
    records, errors = stores["evaluation_store"].list()
    assert len(records) == 1
    assert errors == []

    eval_dir = stores["evaluation_store"].root
    (eval_dir / "evaluation-corrupt.json").write_text("not valid json at all")

    records2, errors2 = stores["evaluation_store"].list()
    assert len(records2) == 1  # the healthy record still lists
    assert len(errors2) == 1
    assert errors2[0]["file"] == "evaluation-corrupt.json"


# === TC-32, TC-33, TC-34: the compute manager and CLI ==================================================


def _wait_for_manager_not_running(manager: RefereeEvaluationComputeManager, hypothesis_id: str, timeout: float = 10.0) -> dict:
    deadline = time_module.monotonic() + timeout
    while time_module.monotonic() < deadline:
        snap = manager.snapshot(hypothesis_id)
        if snap["status"] not in ("running", "cancelling"):
            return snap
        time_module.sleep(0.01)
    raise AssertionError("referee evaluation compute never reached a terminal state")


def test_tc32_single_flight_per_hypothesis_a_different_hypothesis_starts_independently(stores):
    _plant_known_corpus(
        stores, "hyp-tc32-a", "fam-tc32-a", n_sessions=13, trigger_close=100.0, flat_close=102.0,
    )
    _plant_known_corpus(
        stores, "hyp-tc32-b", "fam-tc32-b", n_sessions=13, trigger_close=100.0, flat_close=102.0,
        start_index=20,
    )
    manager = RefereeEvaluationComputeManager()
    kwargs = dict(
        hypothesis_store=stores["hypothesis_store"], family_store=stores["family_store"],
        playbook_store=stores["playbook_store"], bar_store=stores["bar_store"], config=CONFIG,
        null_store=stores["null_store"], evaluation_store=stores["evaluation_store"],
        snapshot_store=stores["snapshot_store"],
    )
    first = manager.trigger("hyp-tc32-a", **kwargs)
    assert first["started"] is True
    second_same = manager.trigger("hyp-tc32-a", **kwargs)
    assert second_same["started"] is False
    assert second_same["compute"]["id"] == first["compute"]["id"]

    third_other = manager.trigger("hyp-tc32-b", **kwargs)
    assert third_other["started"] is True

    _wait_for_manager_not_running(manager, "hyp-tc32-a")
    _wait_for_manager_not_running(manager, "hyp-tc32-b")
    manager.join_all(timeout=10.0)


def test_tc33_cancel_reaches_a_terminal_ledger_state_with_no_duplicate_record(stores):
    """TC-33: a cancel signalled immediately reaches a terminal ledger state (the race between
    "cancelled" and "completed" is real -- both are honest, the ``test_referee_null.py`` TC-20
    precedent) -- and the evaluation store never carries a duplicate for this hypothesis's key."""
    _plant_known_corpus(
        stores, "hyp-tc33", "fam-tc33", n_sessions=13, trigger_close=100.0, flat_close=102.0,
    )
    manager = RefereeEvaluationComputeManager()
    kwargs = dict(
        hypothesis_store=stores["hypothesis_store"], family_store=stores["family_store"],
        playbook_store=stores["playbook_store"], bar_store=stores["bar_store"], config=CONFIG,
        null_store=stores["null_store"], evaluation_store=stores["evaluation_store"],
        snapshot_store=stores["snapshot_store"], run_store=stores["run_store"],
    )
    trigger = manager.trigger("hyp-tc33", **kwargs)
    assert trigger["started"] is True
    manager.cancel("hyp-tc33")
    _wait_for_manager_not_running(manager, "hyp-tc33")
    manager.join_all(timeout=10.0)

    runs, errors = stores["run_store"].list()
    assert errors == []
    assert len(runs) == 1
    assert runs[0]["hypothesis_id"] == "hyp-tc33"
    assert runs[0]["state"] in ("cancelled", "completed")
    records, record_errors = stores["evaluation_store"].list()
    assert record_errors == []
    keys = [(r["hypothesis_id"], r["evaluation_basis"]) for r in records]
    assert len(keys) == len(set(keys))  # no duplicate under any key


def test_tc33b_should_abort_true_from_the_start_writes_no_evaluation_record(stores):
    """A direct, deterministic proof of TC-33's "no partial record" clause: ``should_abort``
    returns ``True`` from the very first check -- no evaluation record is ever written."""
    _plant_known_corpus(
        stores, "hyp-tc33b", "fam-tc33b", n_sessions=13, trigger_close=100.0, flat_close=102.0,
    )
    result = _run_eval(stores, "hyp-tc33b", should_abort=lambda: True)
    assert result["cancelled"] is True
    assert result["record"] is None
    assert stores["evaluation_store"].list_for_hypothesis("hyp-tc33b") == []


def test_tc34_the_cli_evaluate_subcommand_reuses_on_a_second_run(tmp_path, monkeypatch):
    universe_dir = str(tmp_path / "universe")
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", universe_dir)
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_NULL_DIR", str(tmp_path / "nulls"))
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_REGISTRY_DIR", str(tmp_path / "registry"))
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_EVAL_DIR", str(tmp_path / "eval"))
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_EVAL_LOG_DIR", str(tmp_path / "eval_runs"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))

    bar_store = BarStore(tmp_path / "bars")
    playbook_store = PlaybookStore(tmp_path / "playbook")
    null_store = RefereeNullStore(tmp_path / "nulls")
    family_store = FamilyStore(tmp_path / "registry")
    hypothesis_store = HypothesisStore(tmp_path / "registry")
    cli_stores = {
        "bar_store": bar_store, "playbook_store": playbook_store, "null_store": null_store,
        "family_store": family_store, "hypothesis_store": hypothesis_store,
    }
    _plant_known_corpus(
        cli_stores, "hyp-tc34", "fam-tc34", n_sessions=13, trigger_close=100.0, flat_close=102.0,
    )

    monkeypatch.setattr(
        sys, "argv", ["referee_adjudicate", "evaluate", "--hypothesis-id", "hyp-tc34"],
    )
    assert referee_adjudicate_module.main() == 0
    eval_dir = tmp_path / "eval"
    records_first = list(eval_dir.glob("evaluation-*.json"))
    assert len(records_first) == 1
    checksum_first = records_first[0].read_text()

    assert referee_adjudicate_module.main() == 0  # second run, unchanged store
    records_second = list(eval_dir.glob("evaluation-*.json"))
    assert len(records_second) == 1  # reused -- never a second file
    assert records_second[0].read_text() == checksum_first


def test_cli_rejects_missing_required_hypothesis_id_flag(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["referee_adjudicate", "evaluate"])
    with pytest.raises(SystemExit) as exc_info:
        referee_adjudicate_module.main()
    assert exc_info.value.code == 2


# === the routes: GET /evaluations, GET /evaluate, GET /evaluate/runs, GET /adjudications ==============


@pytest.fixture
def route_ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_NULL_DIR", str(tmp_path / "nulls"))
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_REGISTRY_DIR", str(tmp_path / "registry"))
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_EVAL_DIR", str(tmp_path / "eval"))
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_EVAL_LOG_DIR", str(tmp_path / "eval_runs"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    with TestClient(app) as client:
        yield client, tmp_path


def test_get_evaluations_and_adjudications_honest_empty_states(route_ctx):
    client, _tmp = route_ctx
    resp = client.get("/research/desk/referee/evaluations")
    assert resp.status_code == 200
    assert resp.json() == {"records": [], "integrity_errors": []}

    resp2 = client.get("/research/desk/referee/adjudications")
    assert resp2.status_code == 200
    body = resp2.json()
    assert body["entries"] == []
    assert body["register"] == REFEREE_REGISTER

    resp3 = client.get("/research/desk/referee/evaluate/runs")
    assert resp3.status_code == 200
    assert resp3.json() == {"runs": [], "latest": None, "integrity_errors": []}

    resp4 = client.get("/research/desk/referee/evaluate", params={"hypothesis_id": "no-such-hyp"})
    assert resp4.status_code == 200
    assert resp4.json()["status"] == "idle"


def test_route_round_trip_register_evaluate_and_read_adjudications(route_ctx):
    client, tmp_path = route_ctx
    bar_store = BarStore(tmp_path / "bars")
    playbook_store = PlaybookStore(tmp_path / "playbook")
    null_store = RefereeNullStore(tmp_path / "nulls")
    family_store = FamilyStore(tmp_path / "registry")
    hypothesis_store = HypothesisStore(tmp_path / "registry")
    route_stores = {
        "bar_store": bar_store, "playbook_store": playbook_store, "null_store": null_store,
        "family_store": family_store, "hypothesis_store": hypothesis_store,
    }
    _plant_known_corpus(
        route_stores, "hyp-route", "fam-route", n_sessions=13, trigger_close=100.0, flat_close=102.0,
    )

    trigger = client.post("/research/desk/referee/evaluate", json={"hypothesis_id": "hyp-route"})
    assert trigger.status_code == 200
    assert trigger.json()["started"] is True

    deadline = time_module.monotonic() + 15.0
    status = None
    while time_module.monotonic() < deadline:
        status = client.get(
            "/research/desk/referee/evaluate", params={"hypothesis_id": "hyp-route"}
        ).json()
        if status["status"] not in ("running", "cancelling"):
            break
        time_module.sleep(0.05)
    assert status is not None and status["status"] == "done"

    evaluations = client.get("/research/desk/referee/evaluations").json()
    assert len(evaluations["records"]) == 1
    assert evaluations["records"][0]["role"] == "checkpoint"

    adjudications = client.get("/research/desk/referee/adjudications").json()
    entry = next(e for e in adjudications["entries"] if e["hypothesis_id"] == "hyp-route")
    assert entry["verdict"] == "corroborated"

    second_trigger = client.post(
        "/research/desk/referee/evaluate", json={"hypothesis_id": "hyp-route"}
    )
    assert second_trigger.status_code == 200  # unchanged store -- reuses, never errors
    # Wait for the second (dedup-reused) job to reach ITS OWN terminal state before probing the
    # idle-cancel refusal -- `manager.trigger()` starts a new background thread even on a dedup
    # reuse, so an immediate cancel call would otherwise race a genuinely still-"running" job.
    deadline2 = time_module.monotonic() + 15.0
    status2 = None
    while time_module.monotonic() < deadline2:
        status2 = client.get(
            "/research/desk/referee/evaluate", params={"hypothesis_id": "hyp-route"}
        ).json()
        if status2["status"] not in ("running", "cancelling"):
            break
        time_module.sleep(0.05)
    assert status2 is not None and status2["status"] == "done"

    cancel_when_idle = client.post(
        "/research/desk/referee/evaluate/cancel", json={"hypothesis_id": "hyp-route"}
    )
    assert cancel_when_idle.status_code == 409
