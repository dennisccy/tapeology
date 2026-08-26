"""``foundry_runner.py`` (goal-hypothesis-foundry-iter-2, J-04/J-03 integration): canonical-order
exhaustion, mechanical Scout-verdict mapping, and checkpoint/resume/single-flight (spec §7.2/§9).
TC-14 (runner-level parts)/TC-15/TC-16/TC-17 in
``docs/phases/goal-hypothesis-foundry-iter-2.md``."""

from __future__ import annotations

import random

import pytest

from app.research import foundry_compiler as fc
from app.research import foundry_family as ff
from app.research import foundry_interpreter as fi
from app.research import foundry_ledger as fl
from app.research import foundry_runner as fr


_ECON_FLOOR = {"floor_bps": 0.0, "unit": "bps", "rule": "scout_quoted_spread_floor", "multiple": 0.0}


def _scalar_spec(variant_ordinal, *, family_id="family:fixture", family_count=1, sidedness="long"):
    coord = fc.CandidateCoordinate(
        feature_construct_id="q", semantic_role="candidate_signal", transform_orientation="ge",
        threshold_corner_predicate="q >= 1", threshold_provenance="natural_semantic_boundary",
        aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
    )
    return fc.CandidateSpec(
        foundry_spec_version="v1", epoch_id="epoch:hermetic", source_ids=(f"s{variant_ordinal}",),
        lineage_id=f"s{variant_ordinal}", foundry_family_id=family_id,
        variant_id=f"{family_id}:{variant_ordinal}", variant_ordinal=variant_ordinal,
        population=fc.CandidatePopulation(structure_context_kind="none", side_filter=None, setup_context_id=None),
        coordinates=(coord,), relation=fc.CandidateRelation(kind="direct_scalar_membership"),
        membership_corner="q >= 1", outcome=fc.CandidateOutcome(horizon_key="trades_20", sidedness=sidedness),
        economic_floor_rule=fc.EconomicFloorRule(), foundry_family_variant_count=family_count,
    ).with_hash()


def _anchors(seed, *, effect_bps=40.0, n_per_session=60, n_sessions=6, insufficient=False):
    if insufficient:
        n_per_session, n_sessions = 3, 1
    anchors = []
    for s in range(n_sessions):
        session = f"2026-08-{10 + s:02d}"
        order = list(range(n_per_session))
        random.Random(f"{seed}:{s}").shuffle(order)
        members = set(order[: n_per_session // 2])
        for i in range(n_per_session):
            member = i in members
            comp = fi.ComponentResolution("q", True, float(i), 1.0 if member else 0.0, member)
            outcome = effect_bps + (i % 5) * 0.01 if member else -0.01 * (i % 5)
            anchors.append(fi.PopulationAnchor(f"ds-{session}", "AAPL", session, i, "mid", None, outcome, "return_bps", (comp,)))
    return anchors


def test_tc17_mechanical_scout_verdict_mapping_is_exhaustive_and_closed():
    for scout_decision, expected in (
        ("killed_insufficient_n", "EVALUATED_INSUFFICIENT"),
        ("killed_null", "EVALUATED_KILLED"),
        ("killed_direction", "EVALUATED_KILLED"),
        ("killed_concentration", "EVALUATED_KILLED"),
        ("killed_economic", "EVALUATED_KILLED"),
        ("killed_fragile", "EVALUATED_KILLED"),
        ("survive", "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"),
    ):
        assert fr.map_scout_decision(scout_decision) == expected
    with pytest.raises(ValueError):
        fr.map_scout_decision("some_unknown_decision")


def test_tc16_canonical_order_kill_does_not_skip_a_later_survivor_and_vice_versa(tmp_path):
    family = ff.build_family_registry({"family:multi": ["family:multi:0", "family:multi:1", "family:multi:2"]})[
        "family:multi"
    ]
    variants = [
        (_scalar_spec(0, family_id="family:multi", family_count=3), _anchors(1, insufficient=True)),
        (_scalar_spec(1, family_id="family:multi", family_count=3), _anchors(2, effect_bps=100.0)),
        (_scalar_spec(2, family_id="family:multi", family_count=3), _anchors(3, insufficient=True)),
    ]
    ledger = fl.FoundryLedger(tmp_path)
    results = fr.run_family(family, variants, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m1")

    assert len(results) == 3
    assert results[0]["foundry_state"] == "EVALUATED_INSUFFICIENT"
    assert results[1]["foundry_state"] == "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"
    assert results[2]["foundry_state"] == "EVALUATED_INSUFFICIENT"
    # every result carries the COMPLETE frozen denominator, regardless of position/verdict
    assert all(r["foundry_family_variant_count"] == 3 for r in results)
    # canonical order was followed -- ledger rows appear in the SAME order as the input variants
    terminal_hashes = [row["candidate_spec_hash"] for row in ledger.all_rows() if row["row_kind"] == fl.ROW_KIND_TERMINAL]
    assert terminal_hashes == [spec.candidate_spec_hash for spec, _ in variants]


def test_tc14_already_terminal_candidate_is_verified_and_skipped_not_re_executed(tmp_path):
    family = ff.build_family_registry({"family:solo": ["family:solo:0"]})["family:solo"]
    spec = _scalar_spec(0, family_id="family:solo", family_count=1)
    anchors = _anchors(5, effect_bps=50.0)
    ledger = fl.FoundryLedger(tmp_path)

    first = fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m1", family=family)
    n_rows_after_first = len(ledger.all_rows())

    second = fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m1", family=family)
    assert second == first
    assert len(ledger.all_rows()) == n_rows_after_first  # no new row appended on the skip


def test_tc15_intent_without_terminal_after_a_simulated_crash_resumes_and_appends_exactly_one_terminal_row(tmp_path):
    family = ff.build_family_registry({"family:crash": ["family:crash:0"]})["family:crash"]
    spec = _scalar_spec(0, family_id="family:crash", family_count=1)
    anchors = _anchors(6, effect_bps=45.0)
    ledger = fl.FoundryLedger(tmp_path)

    # Simulate the crash: an intent row exists, but no terminal row yet.
    ledger.record_intent(
        candidate_spec_hash=spec.candidate_spec_hash, manifest_hash="m1",
        econ_floor_bps=_ECON_FLOOR["floor_bps"], econ_floor_provenance=_ECON_FLOOR["rule"],
    )
    assert ledger.terminal_row_for(spec.candidate_spec_hash) is None

    result = fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m1", family=family)

    assert result["row_kind"] == fl.ROW_KIND_TERMINAL
    intent_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_INTENT]
    terminal_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL]
    assert len(intent_rows) == 1  # no duplicate intent row was appended on resume
    assert len(terminal_rows) == 1  # exactly one terminal row


def test_tc51_resume_econ_floor_mismatch_halts(tmp_path):
    family = ff.build_family_registry({"family:mismatch": ["family:mismatch:0"]})["family:mismatch"]
    spec = _scalar_spec(0, family_id="family:mismatch", family_count=1)
    anchors = _anchors(7, effect_bps=45.0)
    ledger = fl.FoundryLedger(tmp_path)
    ledger.record_intent(
        candidate_spec_hash=spec.candidate_spec_hash, manifest_hash="m1", econ_floor_bps=99.0,
        econ_floor_provenance=_ECON_FLOOR["rule"],
    )
    with pytest.raises(fr.FoundryResumeIdentityMismatch):
        fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m1", family=family)


def test_tc14_single_flight_lock_rejects_a_concurrent_second_runner(tmp_path):
    lock_path = tmp_path / "foundry_runner.lock"
    lock = fr.SingleFlightLock(lock_path)
    with lock.acquire():
        second = fr.SingleFlightLock(lock_path)
        with pytest.raises(fr.ConcurrentRunnerRefused):
            with second.acquire():
                pass  # pragma: no cover -- must never be reached


def test_tc14_lock_releases_cleanly_a_sequential_second_acquire_succeeds(tmp_path):
    lock_path = tmp_path / "foundry_runner.lock"
    lock = fr.SingleFlightLock(lock_path)
    with lock.acquire():
        pass
    with lock.acquire():  # the FIRST lock released -- a later, non-concurrent acquire is fine
        pass
