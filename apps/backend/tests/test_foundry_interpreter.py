"""``foundry_interpreter.py`` (goal-hypothesis-foundry-iter-2, J-03): population resolution (spec
§4.1), boolean projection into the existing Scout screen (spec §4.2), and the Scout-boundary
scalar-equivalence oracle (spec §4.2.1 / goal Success Criterion 11). TC-4..TC-8 in
``docs/phases/goal-hypothesis-foundry-iter-2.md``.

Every fixture here is hermetic: plain Python dicts/dataclasses built in-test, never a real
DatasetStore/snapshot read. The interpreter's own contract is that it operates on already
population-extracted anchor rows (``PopulationAnchor`` -- one row per candidate/comparator-
eligible opportunity, carrying its own per-conditioning-component resolution state), never a raw
dataset."""

from __future__ import annotations

import pytest

from app.research import foundry_compiler as fc
from app.research import foundry_interpreter as fi
from app.research import scout


def _spec(*, relation_kind: str, coordinates: tuple, membership_corner: str, sidedness: str = "long",
          horizon_key: str = "trades_20") -> fc.CandidateSpec:
    return fc.CandidateSpec(
        foundry_spec_version="v1",
        epoch_id="epoch:hermetic",
        source_ids=("src-1",),
        lineage_id="src-1",
        foundry_family_id="family:src-1",
        variant_id="family:src-1:0",
        variant_ordinal=0,
        population=fc.CandidatePopulation(structure_context_kind="none", side_filter=None, setup_context_id=None),
        coordinates=coordinates,
        relation=fc.CandidateRelation(kind=relation_kind),
        membership_corner=membership_corner,
        outcome=fc.CandidateOutcome(horizon_key=horizon_key, sidedness=sidedness),
        economic_floor_rule=fc.EconomicFloorRule(),
        foundry_family_variant_count=1,
    ).with_hash()


def _component(component_id, *, resolved=True, available_at=0.0, raw_value=None, corner_satisfied=None,
                unavailable_reason=None):
    return fi.ComponentResolution(
        component_id=component_id, resolved=resolved, available_at=available_at if resolved else None,
        raw_value=raw_value, corner_satisfied=corner_satisfied, unavailable_reason=unavailable_reason,
    )


def _anchor(idx, *, session_date, symbol="AAPL", components, outcome_bps):
    return fi.PopulationAnchor(
        dataset_id=f"ds-{symbol}-{session_date}",
        symbol=symbol,
        session_date=session_date,
        trade_index=idx,
        tod_bucket="mid",
        fallback_frac=None,
        outcome_bps=outcome_bps,
        outcome_unit="return_bps",
        components=components,
    )


_ECON_FLOOR = {"floor_bps": 0.0, "unit": "bps", "rule": "scout_quoted_spread_floor", "multiple": 0.0}


def _scalar_fixture(n=40, threshold=1.0):
    """A one-coordinate `direct_scalar_membership` corpus with a genuine planted effect: the
    candidate cell's outcome distribution is shifted up relative to the comparator cell, across two
    sessions, so the equivalence oracle exercises a real (non-insufficient, non-null) decision."""
    anchors = []
    for s in range(2):
        session = f"2026-08-{10 + s:02d}"
        for i in range(n // 2):
            is_member = i % 2 == 0
            raw_value = 2.0 if is_member else 0.0
            outcome = 12.0 + (i % 5) if is_member else -1.0 + (i % 5) * 0.1
            comp = _component("q_imbalance", resolved=True, available_at=float(i), raw_value=raw_value,
                               corner_satisfied=raw_value >= threshold)
            anchors.append(_anchor(i, session_date=session, components=(comp,), outcome_bps=outcome))
    return anchors


def test_tc4_scalar_adapter_is_byte_identical_to_the_direct_scout_path():
    fixture_feature = "foundry_fixture_scalar_q_imbalance"
    threshold = 1.0
    anchors = _scalar_fixture(threshold=threshold)

    # -- the existing DIRECT Scout path: raw (non-boolean) feature_value, real threshold ----------
    direct_anchors = [
        {
            "dataset_id": a.dataset_id, "symbol": a.symbol, "session_date": a.session_date,
            "anchor_at": a.components[0].available_at, "trade_index": a.trade_index,
            "feature_value": a.components[0].raw_value, "outcome_bps": a.outcome_bps,
            "outcome_unit": a.outcome_unit, "tod_bucket": a.tod_bucket, "fallback_frac": a.fallback_frac,
        }
        for a in anchors
    ]
    direct_result = scout.screen_candidate(
        feature_name=fixture_feature, transform="threshold", params={"op": "ge", "value": threshold},
        sidedness="long", horizon_key="trades_20", econ_floor=_ECON_FLOOR, anchors=direct_anchors,
        family_id="fixture-family-tc4", n_variants_tried=1,
    )

    # -- the Foundry adapter path: generic interpreter -> boolean projection -> same screen call ---
    spec = _spec(
        relation_kind="direct_scalar_membership",
        coordinates=(
            fc.CandidateCoordinate(
                feature_construct_id="q_imbalance", semantic_role="candidate_signal",
                transform_orientation="ge", threshold_corner_predicate="q_imbalance >= 1.0",
                threshold_provenance="literal_ratified_threshold", aggressor_derived=False,
                unit_basis="ratio", anchor_at="anchor_at", available_at="anchor_at",
            ),
        ),
        membership_corner="q_imbalance >= 1.0",
    )
    interpretation = fi.interpret_candidate(
        spec, anchors, econ_floor=_ECON_FLOOR, family_id="fixture-family-tc4", n_variants_tried=1,
    )

    assert interpretation.screen == direct_result
    assert interpretation.screen["decision"] not in ("killed_insufficient_n",)  # a real decision was exercised


def test_tc5_conjunction_projects_only_boolean_membership_raw_coordinates_stay_provenance_only():
    anchors = []
    for s in range(2):
        session = f"2026-08-{10 + s:02d}"
        for i in range(24):
            both_true = i % 3 == 0
            c1 = _component("c1", available_at=float(i), raw_value=5.0 if both_true else 0.0,
                             corner_satisfied=both_true)
            c2 = _component("c2", available_at=float(i) + 0.5, raw_value=9.0 if both_true else 1.0,
                             corner_satisfied=both_true)
            outcome = 15.0 if both_true else -0.5
            anchors.append(_anchor(i, session_date=session, components=(c1, c2), outcome_bps=outcome))

    spec = _spec(
        relation_kind="conjunction",
        coordinates=(
            fc.CandidateCoordinate(
                feature_construct_id="c1", semantic_role="candidate_signal", transform_orientation="gt",
                threshold_corner_predicate="c1 > 0", threshold_provenance="natural_semantic_boundary",
                aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
            ),
            fc.CandidateCoordinate(
                feature_construct_id="c2", semantic_role="candidate_signal", transform_orientation="gt",
                threshold_corner_predicate="c2 > 5", threshold_provenance="literal_ratified_threshold",
                aggressor_derived=False, unit_basis="ratio", anchor_at="anchor_at", available_at="anchor_at",
            ),
        ),
        membership_corner="c1 > 0 and c2 > 5",
    )
    interpretation = fi.interpret_candidate(
        spec, anchors, econ_floor=_ECON_FLOOR, family_id="fixture-family-tc5", n_variants_tried=1,
    )

    scout_anchors = fi.project_boolean_membership(fi.resolve_population(anchors, relation_kind="conjunction"))
    # The ONLY feature values reaching the Scout boundary are 1.0/0.0 -- never a raw coordinate.
    assert {a["feature_value"] for a in scout_anchors} <= {0.0, 1.0}
    assert interpretation.read_model["candidate_count"] == sum(1 for a in scout_anchors if a["feature_value"] == 1.0)
    # Raw coordinate values are never present on the anchor dict handed to `scout.screen_candidate`.
    assert all("raw_value" not in a and "c1" not in a and "c2" not in a for a in scout_anchors)


def test_tc6_deferred_unresolved_anchors_excluded_from_both_cells_and_counted_and_timing_is_symmetric():
    anchors = []
    session = "2026-08-10"
    for i in range(30):
        unresolved = i % 5 == 0  # every 5th anchor's refill never completed
        member = i % 2 == 0
        if unresolved:
            comp = _component("refill_consistent", resolved=False, unavailable_reason="refill_unresolved")
        else:
            comp = _component(
                "refill_consistent", resolved=True, available_at=float(i) + 3.0, raw_value=1.0 if member else 0.0,
                corner_satisfied=member,
            )
        outcome = 10.0 if member else -2.0
        anchors.append(_anchor(i, session_date=session, components=(comp,), outcome_bps=outcome))

    resolution = fi.resolve_population(anchors, relation_kind="direct_scalar_membership")

    n_unresolved = sum(1 for a in anchors if a.components[0].resolved is False)
    assert resolution.unavailable_by_reason == {"refill_unresolved": n_unresolved}
    assert len(resolution.eligible) == len(anchors) - n_unresolved

    # Population symmetry: every ELIGIBLE anchor (candidate or comparator alike) shares the exact
    # outcome_start = max(component.available_at) timing law -- never backdated, never special-
    # cased by which cell it lands in.
    for resolved_anchor in resolution.eligible:
        expected = max(c.available_at for c in resolved_anchor.anchor.components)
        assert resolved_anchor.outcome_start == expected
        assert resolved_anchor.candidate_available_at == expected

    read_model = fi.read_model(resolution)
    assert read_model["total_anchors"] == len(anchors)
    assert read_model["eligible_anchors"] == len(resolution.eligible)
    assert read_model["unavailable_by_reason"] == {"refill_unresolved": n_unresolved}
    assert read_model["candidate_count"] + read_model["comparator_count"] == read_model["eligible_anchors"]


def test_tc7_mirrored_sidedness_is_predeclared_and_opposite_result_dies_through_killed_direction():
    # Build a corpus where the SHORT-sided candidate cell has a genuinely NEGATIVE (favorable for
    # short) effect, so a `long`-sidedness registration of the identical corpus dies on
    # `killed_direction` (effect points the wrong way for a long candidate) while the `short`
    # registration survives the direction gate.
    # Deliberately NOT a period-2/period-block-length alternating membership pattern: the block-
    # rotation permutation null (scout.py's ``_rotated_null_deltas``) is invariant to rotations by
    # a multiple of the block length, so a perfectly periodic membership assignment aligned with
    # that period makes every null draw reproduce the observed effect exactly (a degenerate,
    # always-`p_screen=1.0` null) -- a fixture-construction pitfall, not an interpreter bug. A
    # per-session RANDOM (but fixture-seeded, deterministic) membership assignment avoids it.
    import random as _random

    anchors = []
    for s in range(4):
        session = f"2026-08-{10 + s:02d}"
        order = list(range(40))
        _random.Random(s).shuffle(order)
        members = set(order[:20])
        for i in range(40):
            member = i in members
            comp = _component("wall_reject", available_at=float(i), raw_value=1.0 if member else 0.0,
                               corner_satisfied=member)
            outcome = -80.0 + (i % 5) * 0.1 if member else 0.05 * (i % 5)
            anchors.append(_anchor(i, session_date=session, components=(comp,), outcome_bps=outcome))

    long_spec = _spec(
        relation_kind="direct_scalar_membership",
        coordinates=(
            fc.CandidateCoordinate(
                feature_construct_id="wall_reject", semantic_role="candidate_signal",
                transform_orientation="ge", threshold_corner_predicate="wall_reject >= 1",
                threshold_provenance="natural_semantic_boundary", aggressor_derived=False,
                unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
            ),
        ),
        membership_corner="wall_reject >= 1", sidedness="long",
    )
    long_result = fi.interpret_candidate(
        long_spec, anchors, econ_floor=_ECON_FLOOR, family_id="fixture-family-tc7", n_variants_tried=1,
    )
    assert long_spec.outcome.sidedness == "long"
    assert long_result.screen["decision"] == "killed_direction"


def test_tc8_unfrozen_ordered_relation_blocks_with_no_candidate_spec_produced():
    spec = _spec(
        relation_kind="ordered_sequence_lag",
        coordinates=(
            fc.CandidateCoordinate(
                feature_construct_id="thin_then_refill", semantic_role="candidate_signal",
                transform_orientation="ge", threshold_corner_predicate="ordered lag unresolved",
                threshold_provenance=None, aggressor_derived=False, unit_basis="bool",
                anchor_at="anchor_at", available_at="anchor_at",
            ),
        ),
        membership_corner="ordered_lag_unresolved",
    )
    with pytest.raises(fi.UnsupportedRelationBlocked) as exc_info:
        fi.interpret_candidate(spec, [], econ_floor=_ECON_FLOOR, family_id="f", n_variants_tried=1)
    assert exc_info.value.disposition == fi.BLOCKED_UNSUPPORTED_RELATION


def test_relation_kind_dispatch_is_closed_unknown_kind_also_blocks():
    with pytest.raises(fi.UnsupportedRelationBlocked):
        fi.resolve_population([], relation_kind="some_new_ordered_form")
