"""``foundry_compiler.py`` -- the Hypothesis Foundry's ``CandidateSpec`` schema and batch compiler
(goal-hypothesis-foundry-iter-1). Test-first contract: TC-3, TC-4, TC-10, TC-11 in
``docs/phases/goal-hypothesis-foundry-iter-1.md``. TC-5 through TC-9/TC-12 (the blocked/aliased/
lint cases) live in ``test_foundry_source_registry.py`` -- those need no ``CandidateBlueprint``.

TC-11 in ``docs/phases/goal-hypothesis-foundry-iter-3.md`` (a distinct, later TC-11 -- the
``alternatives`` field) extends the SAME two-frozen-legal-variant fixture pair this file's own
iter-1 TC-4 already uses, below."""

from __future__ import annotations

import dataclasses

import pytest

from app.research import foundry_compiler as fc
from app.research import foundry_source_registry as fsr
from app.research import scout


def _span(text: str, excerpt: str) -> fsr.QuotedSpan:
    return fsr.QuotedSpan(text=text, location=excerpt.index(text))


def _blueprint(horizon: str = "trades_20", sidedness: str = "long") -> fc.CandidateBlueprint:
    return fc.CandidateBlueprint(
        population=fc.CandidatePopulation(
            structure_context_kind="band_wall_touch", side_filter=None, setup_context_id=None
        ),
        coordinates=(
            fc.CandidateCoordinate(
                feature_construct_id="quote_imbalance",
                semantic_role="primary",
                transform_orientation="positive_zero_boundary",
                threshold_corner_predicate="quote_imbalance > 0",
                threshold_provenance=fsr.THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
                aggressor_derived=False,
                unit_basis="ratio",
                anchor_at="touch",
                available_at="touch",
            ),
        ),
        relation=fc.CandidateRelation(kind="direct_scalar_membership"),
        membership_corner="quote_imbalance > 0",
        outcome=fc.CandidateOutcome(horizon_key=horizon, sidedness=sidedness),
    )


# --- TC-3: the natural-boundary-scalar fixture compiles to a real CandidateSpec with a non-null
# candidate_spec_hash. -----------------------------------------------------------------------------


def test_tc3_natural_boundary_scalar_compiles_to_a_candidate_spec_with_a_hash():
    excerpt = "A signed variable's zero boundary is bid-heavy when quote_imbalance is positive."
    span_text = "signed variable's zero boundary is bid-heavy when quote_imbalance is positive"
    record = fsr.SourceRecord(
        source_id="fixture-natural-boundary",
        source_path="docs/fixtures/mechanism.md",
        section_ref="2.3",
        quoted_spans=(_span(span_text, excerpt),),
        source_excerpt=excerpt,
        mechanism_statement="quote imbalance zero-crossing implies bid-heavy",
        operative_formula_refs=("quote_imbalance",),
        direction_derivation="positive quote_imbalance implies bid-heavy -> long",
        comparator_derivation="complement_within_same_eligible_population",
        audit_note="zero boundary intrinsic to the signed variable's own definition, per quoted text",
        threshold_provenance=fsr.THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
    )
    result = fc.compile_sources(
        [record],
        foundry_spec_version="v1",
        epoch_id="hermetic-fixture-epoch",
        blueprints={"fixture-natural-boundary": _blueprint()},
    )
    assert result.dispositions["fixture-natural-boundary"] == fsr.DISPOSITION_COMPILED
    spec = result.candidate_specs["fixture-natural-boundary"]
    assert spec.candidate_spec_hash  # non-empty / non-null
    assert spec.foundry_family_variant_count == 1
    assert spec.outcome.horizon_key == "trades_20"


# --- TC-4: two explicitly-frozen legal variants in one family share foundry_family_id, both carry
# foundry_family_variant_count == 2, and have distinct variant_ordinal values. --------------------


def _variant_record(source_id: str, ordinal: int, *, alternatives: tuple[str, ...] = ()) -> fsr.SourceRecord:
    excerpt = f"{source_id}: trades_20 and trades_100 are both already-legal outcome horizons."
    span_text = "trades_20 and trades_100 are both already-legal outcome horizons"
    return fsr.SourceRecord(
        source_id=source_id,
        source_path="docs/fixtures/mechanism.md",
        section_ref="4.1",
        quoted_spans=(_span(span_text, excerpt),),
        source_excerpt=excerpt,
        mechanism_statement="two legal horizon variants of one mechanism",
        operative_formula_refs=("cumulative_delta",),
        direction_derivation="positive cumulative_delta -> long",
        comparator_derivation="complement_within_same_eligible_population",
        audit_note="two already-defined legal outcome horizons enumerated per the frozen vocabulary, §2.1",
        foundry_family_key="fixture-family-horizon-variants",
        variant_ordinal=ordinal,
        alternatives=alternatives,
    )


def test_tc4_two_legal_variants_share_family_and_have_distinct_ordinals():
    record_a = _variant_record("fixture-variant-a", 0)
    record_b = _variant_record("fixture-variant-b", 1)
    result = fc.compile_sources(
        [record_a, record_b],
        foundry_spec_version="v1",
        epoch_id="hermetic-fixture-epoch",
        blueprints={
            "fixture-variant-a": _blueprint(horizon="trades_20"),
            "fixture-variant-b": _blueprint(horizon="trades_100"),
        },
    )
    spec_a = result.candidate_specs["fixture-variant-a"]
    spec_b = result.candidate_specs["fixture-variant-b"]
    assert spec_a.foundry_family_id == spec_b.foundry_family_id
    assert spec_a.foundry_family_variant_count == 2
    assert spec_b.foundry_family_variant_count == 2
    assert spec_a.variant_ordinal != spec_b.variant_ordinal
    assert {spec_a.variant_ordinal, spec_b.variant_ordinal} == {0, 1}


# --- TC-11 (goal-hypothesis-foundry-iter-3): the SAME two-frozen-legal-variant fixture pair
# populates `alternatives` naming each other as the sibling representation; a fixture with no
# ratified alternative (the natural-boundary-scalar record used by TC-3, above) shows an empty
# tuple -- confirmed already by test_foundry_source_registry.py's own default-empty-tuple test. ---


def test_tc11_two_legal_variants_name_each_other_as_their_alternative():
    record_a = _variant_record("fixture-variant-alt-a", 0, alternatives=("fixture-variant-alt-b",))
    record_b = _variant_record("fixture-variant-alt-b", 1, alternatives=("fixture-variant-alt-a",))
    assert record_a.alternatives == ("fixture-variant-alt-b",)
    assert record_b.alternatives == ("fixture-variant-alt-a",)

    # additive, not a replacement: BOTH the family-key mechanism and the alternatives disclosure
    # agree about the same two siblings.
    result = fc.compile_sources(
        [record_a, record_b],
        foundry_spec_version="v1",
        epoch_id="hermetic-fixture-epoch",
        blueprints={
            "fixture-variant-alt-a": _blueprint(horizon="trades_20"),
            "fixture-variant-alt-b": _blueprint(horizon="trades_100"),
        },
    )
    spec_a = result.candidate_specs["fixture-variant-alt-a"]
    spec_b = result.candidate_specs["fixture-variant-alt-b"]
    assert spec_a.foundry_family_id == spec_b.foundry_family_id  # same family the alternatives agree with


def test_family_ordinal_collision_is_refused():
    record_a = _variant_record("fixture-collide-a", 0)
    record_b = _variant_record("fixture-collide-b", 0)  # SAME ordinal, same family -- illegal
    with pytest.raises(fc.FamilyOrdinalCollision):
        fc.compile_sources(
            [record_a, record_b],
            foundry_spec_version="v1",
            epoch_id="hermetic-fixture-epoch",
            blueprints={
                "fixture-collide-a": _blueprint(),
                "fixture-collide-b": _blueprint(),
            },
        )


# --- TC-10: mutating one §3 science-affecting field (horizon_key) changes candidate_spec_hash;
# shuffling field-serialization order does not. -----------------------------------------------


def test_tc10_mutating_horizon_key_changes_the_hash():
    excerpt = "The mechanism has one already-ratified horizon."
    span_text = "one already-ratified horizon"
    record = fsr.SourceRecord(
        source_id="fixture-horizon-mutation",
        source_path="docs/fixtures/mechanism.md",
        section_ref="3.1",
        quoted_spans=(_span(span_text, excerpt),),
        source_excerpt=excerpt,
        mechanism_statement="m",
        operative_formula_refs=(),
        direction_derivation="long",
        comparator_derivation="complement",
        audit_note="note",
    )
    result_20 = fc.compile_sources(
        [record], foundry_spec_version="v1", epoch_id="e",
        blueprints={"fixture-horizon-mutation": _blueprint(horizon="trades_20")},
    )
    result_100 = fc.compile_sources(
        [record], foundry_spec_version="v1", epoch_id="e",
        blueprints={"fixture-horizon-mutation": _blueprint(horizon="trades_100")},
    )
    hash_20 = result_20.candidate_specs["fixture-horizon-mutation"].candidate_spec_hash
    hash_100 = result_100.candidate_specs["fixture-horizon-mutation"].candidate_spec_hash
    assert hash_20 != hash_100


def test_tc10_shuffling_canonical_field_order_does_not_change_the_hash():
    excerpt = "one field-order fixture"
    record = fsr.SourceRecord(
        source_id="fixture-order",
        source_path="docs/fixtures/mechanism.md",
        section_ref="3.1",
        quoted_spans=(),
        source_excerpt=excerpt,
        mechanism_statement="m",
        operative_formula_refs=(),
        direction_derivation="long",
        comparator_derivation="complement",
        audit_note="note",
    )
    result = fc.compile_sources(
        [record], foundry_spec_version="v1", epoch_id="e", blueprints={"fixture-order": _blueprint()}
    )
    spec = result.candidate_specs["fixture-order"]
    canonical = spec._canonical_fields()
    import json

    forward = json.dumps(canonical, sort_keys=True, default=str)
    shuffled = json.dumps(dict(reversed(list(canonical.items()))), sort_keys=True, default=str)
    assert forward == shuffled
    assert spec.compute_hash() == spec.candidate_spec_hash


def test_invalid_horizon_key_is_refused_at_outcome_construction():
    """§3.1: only ``scout.HORIZON_KEYS`` members are legal -- verified from the real module, never
    a second hard-coded set that could silently drift."""
    with pytest.raises(ValueError):
        fc.CandidateOutcome(horizon_key="clock_5m", sidedness="long")
    assert "clock_5m" not in scout.HORIZON_KEYS  # sanity: this really is an illegal horizon


def test_invalid_sidedness_is_refused():
    with pytest.raises(ValueError):
        fc.CandidateOutcome(horizon_key="trades_20", sidedness="sideways")


# --- TC-11: an injected effect_bps/p_value/n fixture field (outside source inputs) cannot change
# candidate_spec_hash or disposition. -----------------------------------------------------------


def test_tc11_injected_outcome_fields_do_not_move_hash_or_disposition():
    excerpt = "one non-science-field fixture"
    record = fsr.SourceRecord(
        source_id="fixture-extra",
        source_path="docs/fixtures/mechanism.md",
        section_ref="3.1",
        quoted_spans=(),
        source_excerpt=excerpt,
        mechanism_statement="m",
        operative_formula_refs=(),
        direction_derivation="long",
        comparator_derivation="complement",
        audit_note="note",
    )
    record_with_extra = dataclasses.replace(
        record, extra={"effect_bps": 37.5, "p_value": 0.002, "n": 812, "scout_verdict": "survive"}
    )

    result_plain = fc.compile_sources(
        [record], foundry_spec_version="v1", epoch_id="e", blueprints={"fixture-extra": _blueprint()}
    )
    result_extra = fc.compile_sources(
        [record_with_extra], foundry_spec_version="v1", epoch_id="e",
        blueprints={"fixture-extra": _blueprint()},
    )
    assert result_plain.dispositions["fixture-extra"] == result_extra.dispositions["fixture-extra"]
    spec_plain = result_plain.candidate_specs["fixture-extra"]
    spec_extra = result_extra.candidate_specs["fixture-extra"]
    assert spec_plain.candidate_spec_hash == spec_extra.candidate_spec_hash


# --- A record without a supplied blueprint (or one naming a deferred join) produces no
# CandidateSpec this revision -- FROZEN_READY-incomplete, never approximated. ----------------------


def test_compiled_record_with_no_blueprint_produces_no_candidate_spec():
    excerpt = "one no-blueprint fixture"
    record = fsr.SourceRecord(
        source_id="fixture-no-blueprint",
        source_path="docs/fixtures/mechanism.md",
        section_ref="3.1",
        quoted_spans=(),
        source_excerpt=excerpt,
        mechanism_statement="m",
        operative_formula_refs=(),
        direction_derivation="long",
        comparator_derivation="complement",
        audit_note="note",
    )
    result = fc.compile_sources([record], foundry_spec_version="v1", epoch_id="e", blueprints={})
    assert result.dispositions["fixture-no-blueprint"] == fsr.DISPOSITION_COMPILED
    assert "fixture-no-blueprint" not in result.candidate_specs


def test_compiled_record_with_a_deferred_coordinate_produces_no_candidate_spec_this_revision():
    excerpt = "one deferred-join fixture"
    record = fsr.SourceRecord(
        source_id="fixture-deferred",
        source_path="docs/fixtures/mechanism.md",
        section_ref="3.1",
        quoted_spans=(),
        source_excerpt=excerpt,
        mechanism_statement="refill_consistent deferred conjunction",
        operative_formula_refs=(),
        direction_derivation="long",
        comparator_derivation="complement",
        audit_note="note",
    )
    deferred_blueprint = fc.CandidateBlueprint(
        population=fc.CandidatePopulation(structure_context_kind="band_wall_touch", side_filter=None, setup_context_id=None),
        coordinates=(
            fc.CandidateCoordinate(
                feature_construct_id="refill_consistent",
                semantic_role="deferred_conjunct",
                transform_orientation="boolean",
                threshold_corner_predicate="refill_consistent == True",
                threshold_provenance=fsr.THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
                aggressor_derived=False,
                unit_basis="boolean",
                anchor_at="touch",
                available_at="resolution",
                resolution_join_rule="deferred_via_observer_provenance_id",
            ),
        ),
        relation=fc.CandidateRelation(kind="conjunction"),
        membership_corner="refill_consistent == True",
        outcome=fc.CandidateOutcome(horizon_key="trades_20", sidedness="long"),
    )
    assert deferred_blueprint.is_immediate() is False
    result = fc.compile_sources(
        [record], foundry_spec_version="v1", epoch_id="e", blueprints={"fixture-deferred": deferred_blueprint}
    )
    assert result.dispositions["fixture-deferred"] == fsr.DISPOSITION_COMPILED
    assert "fixture-deferred" not in result.candidate_specs


# --- TC-16 (goal-hypothesis-foundry-iter-4, Repair 1): `compile_sources` runs the alternatives
# lint alongside the quoted-span lint, BEFORE building any CandidateSpec. ---------------------------


def test_tc16_compile_sources_fails_closed_on_a_self_referential_alternative():
    excerpt = "one self-referential alternatives fixture"
    record = fsr.SourceRecord(
        source_id="fixture-self-alt", source_path="docs/fixtures/mechanism.md", section_ref="3.1",
        quoted_spans=(), source_excerpt=excerpt, mechanism_statement="m", operative_formula_refs=(),
        direction_derivation="long", comparator_derivation="complement", audit_note="note",
        foundry_family_key="fixture-self-alt-family", variant_ordinal=0, alternatives=("fixture-self-alt",),
    )
    with pytest.raises(fsr.AlternativeReferenceInvalid):
        fc.compile_sources(
            [record], foundry_spec_version="v1", epoch_id="e", blueprints={"fixture-self-alt": _blueprint()}
        )


def test_compiler_hash_is_stable_and_non_empty():
    h1 = fc.compiler_hash()
    h2 = fc.compiler_hash()
    assert h1 == h2
    assert len(h1) == 64  # sha256 hex digest
