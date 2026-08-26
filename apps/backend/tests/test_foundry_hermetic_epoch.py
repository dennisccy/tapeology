"""The Hypothesis Foundry -- the composite hermetic "complete factory" oracle suite
(goal-hypothesis-foundry-iter-3, J-05). Test-first contract: TC-1 through TC-8 in
``docs/phases/goal-hypothesis-foundry-iter-3.md``.

**What this file proves that no single ``foundry_*.py`` module's own test file does.** Every prior
Foundry test file (``test_foundry_compiler.py``, ``test_foundry_interpreter.py``,
``test_foundry_family.py``, ``test_foundry_freeze.py``, ``test_foundry_ledger.py``,
``test_foundry_runner.py``) exercises exactly one module in isolation, or two adjacent modules at
most (``test_foundry_runner.py``'s own small fixtures). This file drives the REAL production
``foundry_compiler`` -> ``foundry_interpreter`` -> ``foundry_family`` -> ``foundry_ledger`` ->
``foundry_runner`` path together, over one composite epoch containing every possible outcome type
at once (a ``BLOCKED_*`` source, an ``EXCLUDED_*`` source, an ``ALIASED_*`` source, and
``FROZEN_READY`` variants terminating each of ``EVALUATED_INSUFFICIENT``/``EVALUATED_KILLED`` (via
every one of the five kill reasons)/``DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN``), plus the all-blocked,
all-killed, multi-survivor, large-scale checkpoint/resume, and protected-data-trip/
evidence-class-immutability fixtures the goal's own Constraints demand before the real freeze
("use large hermetic synthetic fixtures to prove performance/checkpoint behavior... before the real
freeze"). No mock of any of the five modules under test appears anywhere below -- every fixture is a
hermetic, synthetic ANCHOR list (never a real dataset/network read), fed through the real functions.

**Kill-type fixture provenance.** Every per-outcome anchor generator below is a direct, deliberate
translation of an ALREADY-hermetically-proven ``scout.py`` fixture from ``test_scout.py`` (the
``killed_null``/``killed_direction``/``killed_concentration``/``killed_economic``/
``killed_insufficient_n``/``killed_fragile``/``survive`` fixtures there) into the Foundry's own
``PopulationAnchor``/``ComponentResolution`` shape (``is_candidate`` <-> the direct-scalar-corner
boolean the scout fixtures express as ``feature_value >= 0``) -- never invented from scratch, so a
kill-type reliably reaching its OWN decision branch through the REAL block-permutation null is
already known-good production behavior, not a hand-tuned coincidence of this file."""

from __future__ import annotations

import random

import pytest

from app.research import foundry_compiler as fc
from app.research import foundry_family as ff
from app.research import foundry_interpreter as fi
from app.research import foundry_ledger as fl
from app.research import foundry_runner as fr
from app.research import foundry_source_registry as fsr
from app.research import micro_features as mf
from app.research import scout
from app.research.micro_accessor import MicroAccessorOriginFenceError, MicroAccessorSealedShardError

# --- shared fixtures ------------------------------------------------------------------------------

_ECON_FLOOR_TINY = {
    "floor_bps": 0.001, "unit": "bps", "rule": "scout_quoted_spread_floor", "multiple": 1.0,
}
_ECON_FLOOR_HUGE = {
    "floor_bps": 1000.0, "unit": "bps", "rule": "scout_quoted_spread_floor", "multiple": 1.0,
}


def _spec(ordinal: int, *, family_id: str, family_count: int, sidedness: str = "long") -> fc.CandidateSpec:
    """One direct-scalar-membership ``CandidateSpec`` -- the SAME one-coordinate shape
    ``test_foundry_runner.py``'s own ``_scalar_spec`` uses, so ``foundry_ledger.prospective_root_status``
    resolves to the family id (never ``root_deferred_composite``) for every variant this file builds."""
    coord = fc.CandidateCoordinate(
        feature_construct_id="q", semantic_role="candidate_signal", transform_orientation="ge",
        threshold_corner_predicate="q >= 1", threshold_provenance="natural_semantic_boundary",
        aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
    )
    source_id = f"{family_id}:{ordinal}"
    return fc.CandidateSpec(
        foundry_spec_version="v1", epoch_id="epoch:hermetic-complete-factory", source_ids=(source_id,),
        lineage_id=source_id, foundry_family_id=family_id,
        variant_id=f"{family_id}:{ordinal}", variant_ordinal=ordinal,
        population=fc.CandidatePopulation(structure_context_kind="none", side_filter=None, setup_context_id=None),
        coordinates=(coord,), relation=fc.CandidateRelation(kind="direct_scalar_membership"),
        membership_corner="q >= 1", outcome=fc.CandidateOutcome(horizon_key="trades_20", sidedness=sidedness),
        economic_floor_rule=fc.EconomicFloorRule(), foundry_family_variant_count=family_count,
    ).with_hash()


def _anchor(session: str, idx: int, symbol: str, member: bool, outcome_bps: float, *, tod: str = "mid") -> fi.PopulationAnchor:
    comp = fi.ComponentResolution("q", True, float(idx), 1.0 if member else 0.0, member)
    return fi.PopulationAnchor(f"ds-{session}", symbol, session, idx, tod, None, outcome_bps, mf.OUTCOME_UNIT, (comp,))


# --- per-kill-type anchor generators, each a direct translation of an already-proven test_scout.py
# fixture (see module docstring) ---------------------------------------------------------------


def _survive_anchors(seed: int, *, effect_bps: float = 60.0, n_sessions: int = 6, n_per_session: int = 40, symbol: str = "AAPL") -> list[fi.PopulationAnchor]:
    """Translation of ``test_scout.py``'s ``_planted_effect_anchors``: a genuine planted effect,
    single symbol, evenly spread across sessions -- reliably ``survive``s at ``effect_bps=60``."""
    rng = random.Random(f"factory-survive:{seed}")
    anchors = []
    for s in range(n_sessions):
        session = f"2026-08-{10 + s:02d}"
        for i in range(n_per_session):
            member = rng.random() < 0.5
            outcome = rng.gauss(effect_bps if member else 0.0, 1.0)
            anchors.append(_anchor(session, i, symbol, member, outcome))
    return anchors


def _wrong_direction_anchors(seed: int, *, effect_bps: float = 60.0) -> list[fi.PopulationAnchor]:
    """Translation of ``test_scout.py``'s ``test_screen_candidate_kills_direction_on_a_wrong_signed_effect``:
    the SAME planted-effect population, outcome sign flipped -- significant but wrong-signed."""
    base = _survive_anchors(seed, effect_bps=effect_bps)
    return [
        fi.PopulationAnchor(a.dataset_id, a.symbol, a.session_date, a.trade_index, a.tod_bucket, a.fallback_frac, -a.outcome_bps, a.outcome_unit, a.components)
        for a in base
    ]


def _null_anchors(seed: int, *, n_sessions: int = 6, n_per_session: int = 20, symbol: str = "PG") -> list[fi.PopulationAnchor]:
    """Translation of ``test_scout.py``'s ``test_screen_candidate_kills_null_on_an_unrelated_feature``:
    membership and outcome are independently drawn -- no true relationship."""
    rng = random.Random(f"factory-null:{seed}")
    anchors = []
    for s in range(n_sessions):
        session = f"2026-08-{s + 1:02d}"
        for i in range(n_per_session):
            member = rng.random() < 0.5
            outcome = rng.gauss(0.0, 1.0)
            anchors.append(_anchor(session, i, symbol, member, outcome))
    return anchors


def _concentration_anchors(seed: int, *, n_sessions: int = 6, n_per_session: int = 20) -> list[fi.PopulationAnchor]:
    """Translation of ``test_scout.py``'s ``test_screen_candidate_kills_concentration_when_the_effect_is_symbol_skewed``:
    a genuine, significant, positive effect whose candidate cell is symbol-skewed (>80% one symbol)."""
    rng = random.Random(f"factory-concentration:{seed}")
    anchors = []
    for s in range(n_sessions):
        session = f"2026-09-{s + 1:02d}"
        for i in range(n_per_session):
            member = rng.random() < 0.5
            outcome = rng.gauss(3.0 if member else 0.0, 1.0)
            symbol = "AAA" if (not member or rng.random() < 0.9) else "BBB"
            anchors.append(_anchor(session, i, symbol, member, outcome))
    return anchors


def _insufficient_anchors() -> list[fi.PopulationAnchor]:
    """Translation of ``test_scout.py``'s ``test_screen_candidate_kills_insufficient_n_on_a_single_session``:
    a single session -- below ``SCOUT_MIN_SESSION_CLUSTERS`` regardless of per-cell counts."""
    anchors = []
    session = "2026-07-01"
    for i in range(20):
        member = i % 2 == 0
        anchors.append(_anchor(session, i, "AAPL", member, 3.0 if member else -3.0))
    return anchors


def _fragile_anchors() -> list[fi.PopulationAnchor]:
    """VERBATIM translation of ``test_scout.py``'s
    ``test_screen_candidate_kills_fragile_when_the_sign_depends_on_one_dominant_session`` fixture:
    three sessions where the WITH-all-sessions effect is positive but dropping session "B" (the
    biggest candidate-cell contributor) flips the sign. Reaching ``killed_fragile`` still needs the
    SAME ``scout._two_sided_p`` monkeypatch that production test uses (see its own docstring: forcing
    significance in isolation is the only reliable way to reach this branch, since a genuinely tiny
    p-value AND a session-count-driven sign flip at once is "hard to hand-tune reliably")."""
    anchors = []
    for i in range(8):
        anchors.append(_anchor("A", 2 * i, "PG", True, -0.2))
        anchors.append(_anchor("A", 2 * i + 1, "PG", False, 0.0))
    for i in range(12):
        anchors.append(_anchor("B", 2 * i, "PG", True, 2.0))
        anchors.append(_anchor("B", 2 * i + 1, "PG", False, 0.0))
    for i in range(8):
        anchors.append(_anchor("C", 2 * i, "PG", True, -0.2))
        anchors.append(_anchor("C", 2 * i + 1, "PG", False, 0.0))
    return anchors


# --- non-compiled source fixtures: one BLOCKED_*, one EXCLUDED_*, one ALIASED_* -- direct
# translations of test_foundry_source_registry.py's own already-proven archetypes. --------------


def _blocked_source() -> fsr.SourceRecord:
    excerpt = "A collapse in impact defines a high-aggression signal at the wall."
    span_text = "collapse in impact defines a high-aggression signal"
    return fsr.SourceRecord(
        source_id="factory-blocked-spec-gap", source_path="docs/fixtures/mechanism.md", section_ref="1.9",
        quoted_spans=(fsr.QuotedSpan(text=span_text, location=excerpt.index(span_text)),), source_excerpt=excerpt,
        mechanism_statement="impact collapse at the wall implies reversal", operative_formula_refs=("impact_efficiency",),
        direction_derivation="collapse implies reversal -> long",
        comparator_derivation="complement_within_same_eligible_population",
        audit_note="'collapse'/'high' are undefined magnitude words -- no ratified numeric meaning exists",
        unresolved_magnitude_words=("collapse", "high"),
    )


def _excluded_source() -> fsr.SourceRecord:
    excerpt = "Card 9.1/Study 2 was previously killed and may not be recompiled."
    span_text = "Card 9.1/Study 2 was previously killed and may not be recompiled"
    return fsr.SourceRecord(
        source_id="factory-excluded-previously-killed", source_path="docs/fixtures/mechanism.md", section_ref="9.1",
        quoted_spans=(fsr.QuotedSpan(text=span_text, location=excerpt.index(span_text)),), source_excerpt=excerpt,
        mechanism_statement="Card 9.1/Study 2 mechanism", operative_formula_refs=(),
        direction_derivation=fsr.BLOCKED_DIRECTION_SENTINEL,
        comparator_derivation="complement_within_same_eligible_population",
        audit_note="Card 9.1/Study 2 was previously killed -- may not be recompiled, reversed, or rerun",
        explicit_exclusion=fsr.DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED,
    )


def _aliased_source() -> fsr.SourceRecord:
    excerpt = "Card 9.7 event-time windows are already embodied by the current frozen feature windows."
    span_text = "event-time windows are already embodied by the current frozen feature windows"
    return fsr.SourceRecord(
        source_id="factory-aliased-variant-vocabulary", source_path="docs/fixtures/mechanism.md", section_ref="9.7",
        quoted_spans=(fsr.QuotedSpan(text=span_text, location=excerpt.index(span_text)),), source_excerpt=excerpt,
        mechanism_statement="event-time feature windows", operative_formula_refs=("event_time_window",),
        direction_derivation="long", comparator_derivation="complement_within_same_eligible_population",
        audit_note="Card 9.7 is variant vocabulary for an already-frozen current feature window, per §1.3",
        superseded_fields={"event_time_window": "docs/rapid-validation-spec.md#feature-windows"},
        supersession=fsr.SupersessionDeclaration(
            newer_source_ref="docs/rapid-validation-spec.md#feature-windows",
            alias_kind=fsr.DISPOSITION_ALIASED_VARIANT_VOCABULARY,
        ),
    )


# === TC-1/TC-2: the composite "complete factory" epoch ==============================================


def test_tc1_tc2_composite_complete_factory_epoch_reaches_every_outcome_type_in_canonical_order(monkeypatch, tmp_path):
    # --- non-compiled sources: proven at the disposition layer, coexisting in the SAME epoch as the
    # seven evaluable variants below (never interfering with each other). ---------------------------
    non_compiled = [_blocked_source(), _excluded_source(), _aliased_source()]
    dispositions = {r.source_id: fsr.compile_source_disposition(r) for r in non_compiled}
    assert dispositions["factory-blocked-spec-gap"] == fsr.DISPOSITION_BLOCKED_SPEC_GAP
    assert dispositions["factory-excluded-previously-killed"] == fsr.DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED
    assert dispositions["factory-aliased-variant-vocabulary"] == fsr.DISPOSITION_ALIASED_VARIANT_VOCABULARY

    # --- seven FROZEN_READY variants, one Foundry family, canonical ordinal order 0..6. -------------
    family_id = "family:complete-factory"
    family = ff.build_family_registry({family_id: [f"{family_id}:{i}" for i in range(7)]})[family_id]
    assert family.blocked is False
    assert family.variant_count == 7

    plan = [
        ("insufficient", _insufficient_anchors(), _ECON_FLOOR_TINY, False),
        ("null", _null_anchors(1), _ECON_FLOOR_TINY, False),
        ("direction", _wrong_direction_anchors(2), _ECON_FLOOR_TINY, False),
        ("concentration", _concentration_anchors(3), _ECON_FLOOR_TINY, False),
        ("economic", _survive_anchors(4, effect_bps=40.0), _ECON_FLOOR_HUGE, False),
        ("fragile", _fragile_anchors(), _ECON_FLOOR_TINY, True),
        ("survive", _survive_anchors(6, effect_bps=60.0), _ECON_FLOOR_TINY, False),
    ]

    ledger = fl.FoundryLedger(tmp_path)
    manifest_hash = "manifest:complete-factory"
    specs = [_spec(i, family_id=family_id, family_count=7) for i in range(len(plan))]
    results = []
    for (label, anchors, floor, needs_fragile_patch), spec in zip(plan, specs):
        if needs_fragile_patch:
            with monkeypatch.context() as m:
                m.setattr(scout, "_two_sided_p", lambda observed, null: 0.0001)
                row = fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=floor, manifest_hash=manifest_hash, family=family)
        else:
            row = fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=floor, manifest_hash=manifest_hash, family=family)
        results.append((label, spec, row))

    expected_states = {
        "insufficient": "EVALUATED_INSUFFICIENT",
        "null": "EVALUATED_KILLED",
        "direction": "EVALUATED_KILLED",
        "concentration": "EVALUATED_KILLED",
        "economic": "EVALUATED_KILLED",
        "fragile": "EVALUATED_KILLED",
        "survive": "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
    }
    expected_reasons = {
        "null": "killed_null", "direction": "killed_direction", "concentration": "killed_concentration",
        "economic": "killed_economic", "fragile": "killed_fragile", "insufficient": "killed_insufficient_n",
        "survive": "survive",
    }
    for label, spec, row in results:
        assert row["foundry_state"] == expected_states[label], f"{label}: {row['foundry_state']}"
        assert row["screen_result"]["reason"] == expected_reasons[label], f"{label}: {row['screen_result']}"
        # TC-2: every terminal row carries the pre-frozen family denominator, regardless of
        # execution progress, position, or verdict.
        assert row["foundry_family_variant_count"] == 7, label
        assert row["screen_result"]["screen_result"]["best_of_n_disclosure"]["n"] == 7, label

    # TC-1: canonical-order visiting is unaffected by any kill/survivor encountered along the way --
    # the ledger's terminal rows appear in EXACTLY the order the variants were given (ordinal 0..6).
    terminal_hashes = [r["candidate_spec_hash"] for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL]
    assert terminal_hashes == [spec.candidate_spec_hash for _, spec, _ in results]

    # every non-compiled source keeps its declared disposition, unaffected by the seven terminal
    # candidates that ran alongside it in the same epoch.
    for record in non_compiled:
        assert fsr.compile_source_disposition(record) == dispositions[record.source_id]

    # ledger integrity holds after the full mixed-outcome sequence.
    assert ledger.verify_chain()["ok"] is True


# === TC-1 (compiler seam): the FROZEN_READY variants the runner evaluates are the ones the REAL ====
# compiler produced from real SourceRecords -- not hand-built CandidateSpec objects. =================


def _compilable_variant_record(source_id: str, ordinal: int) -> fsr.SourceRecord:
    """A COMPILED-disposition source record (the natural-boundary-scalar archetype
    ``test_foundry_compiler.py``'s own iter-1 TC-3/TC-4 fixtures use), carrying a shared
    ``foundry_family_key`` so ``fc.compile_sources`` derives the family identity itself."""
    excerpt = f"{source_id}: a signed variable's zero boundary is bid-heavy when quote_imbalance is positive."
    span_text = "signed variable's zero boundary is bid-heavy when quote_imbalance is positive"
    return fsr.SourceRecord(
        source_id=source_id, source_path="docs/fixtures/mechanism.md", section_ref="2.3",
        quoted_spans=(fsr.QuotedSpan(text=span_text, location=excerpt.index(span_text)),),
        source_excerpt=excerpt,
        mechanism_statement="quote imbalance zero-crossing implies bid-heavy",
        operative_formula_refs=("quote_imbalance",),
        direction_derivation="positive quote_imbalance implies bid-heavy -> long",
        comparator_derivation="complement_within_same_eligible_population",
        audit_note="zero boundary intrinsic to the signed variable's own definition, per quoted text",
        threshold_provenance=fsr.THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
        foundry_family_key="factory-compiled-family", variant_ordinal=ordinal,
    )


def _compilable_blueprint(horizon: str = "trades_20") -> fc.CandidateBlueprint:
    """The same fully-immediate blueprint shape ``test_foundry_compiler.py``'s own ``_blueprint``
    builds -- copied rather than imported so this oracle file stays self-contained."""
    return fc.CandidateBlueprint(
        population=fc.CandidatePopulation(
            structure_context_kind="band_wall_touch", side_filter=None, setup_context_id=None
        ),
        coordinates=(
            fc.CandidateCoordinate(
                feature_construct_id="quote_imbalance", semantic_role="primary",
                transform_orientation="positive_zero_boundary",
                threshold_corner_predicate="quote_imbalance > 0",
                threshold_provenance=fsr.THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
                aggressor_derived=False, unit_basis="ratio", anchor_at="touch", available_at="touch",
            ),
        ),
        relation=fc.CandidateRelation(kind="direct_scalar_membership"),
        membership_corner="quote_imbalance > 0",
        outcome=fc.CandidateOutcome(horizon_key=horizon, sidedness="long"),
    )


def test_compiled_candidate_specs_flow_from_the_real_compiler_into_the_real_runner(tmp_path):
    """The one seam the rest of this file (and every other ``test_foundry_*.py``) leaves untested:
    every other interpreter/runner fixture hand-builds its ``CandidateSpec``, so nothing proved
    that the object ``fc.compile_sources`` ACTUALLY produces from a ``SourceRecord`` is directly
    evaluable by ``foundry_interpreter``/``foundry_runner`` and lands its own frozen identities
    (spec hash, family id, family denominator, deterministic rule_id) on the terminal ledger row
    unchanged. Added by the iter-3 audit pass; this is the exact compiler -> runner handoff J-06's
    real epoch will depend on."""
    records = [_compilable_variant_record("factory-compiled-a", 0), _compilable_variant_record("factory-compiled-b", 1)]
    result = fc.compile_sources(
        records, foundry_spec_version="v1", epoch_id="epoch:hermetic-complete-factory",
        blueprints={
            "factory-compiled-a": _compilable_blueprint("trades_20"),
            "factory-compiled-b": _compilable_blueprint("trades_100"),
        },
    )
    assert result.dispositions == {
        "factory-compiled-a": fsr.DISPOSITION_COMPILED, "factory-compiled-b": fsr.DISPOSITION_COMPILED,
    }
    spec_a = result.candidate_specs["factory-compiled-a"]
    spec_b = result.candidate_specs["factory-compiled-b"]
    assert spec_a.foundry_family_id == spec_b.foundry_family_id  # the COMPILER derived the family
    assert spec_a.candidate_spec_hash != spec_b.candidate_spec_hash

    family_id = spec_a.foundry_family_id
    family = ff.build_family_registry({family_id: [spec_a.variant_id, spec_b.variant_id]})[family_id]
    ledger = fl.FoundryLedger(tmp_path)
    rows = fr.run_family(
        family,
        [(spec_a, _survive_anchors(41, effect_bps=60.0)), (spec_b, _null_anchors(42))],
        ledger=ledger, econ_floor=_ECON_FLOOR_TINY, manifest_hash="manifest:compiled-flow",
    )

    # the compiled specs really evaluate: one survivor, one null kill, through the production path.
    assert rows[0]["foundry_state"] == "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"
    assert rows[1]["foundry_state"] == "EVALUATED_KILLED"
    assert rows[1]["screen_result"]["reason"] == "killed_null"
    # every identity on the terminal rows came from the COMPILER's own frozen objects, unchanged.
    assert [r["candidate_spec_hash"] for r in rows] == [spec_a.candidate_spec_hash, spec_b.candidate_spec_hash]
    assert [r["foundry_family_id"] for r in rows] == [family_id, family_id]
    assert [r["foundry_family_variant_count"] for r in rows] == [2, 2]
    assert rows[0]["rule_id"] == f"foundry:{spec_a.epoch_id}:{spec_a.candidate_spec_hash}"
    assert rows[0]["screen_result"]["screen_result"]["evidence_class"] == scout.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
    assert ledger.verify_chain()["ok"] is True


# === TC-3: an all-BLOCKED_*/EXCLUDED_*/ALIASED_* epoch (zero FROZEN_READY variants) completes ======
# honestly, not as an error. ==========================================================================


def test_tc3_all_non_compiled_epoch_reaches_an_honest_zero_candidate_completion(tmp_path):
    records = [_blocked_source(), _excluded_source(), _aliased_source()]
    result = fc.compile_sources(
        records, foundry_spec_version="v1", epoch_id="epoch:all-non-compiled", blueprints={},
    )
    # zero CandidateSpecs -- every source's own disposition is non-COMPILED.
    assert result.candidate_specs == {}
    assert result.dispositions == {
        "factory-blocked-spec-gap": fsr.DISPOSITION_BLOCKED_SPEC_GAP,
        "factory-excluded-previously-killed": fsr.DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED,
        "factory-aliased-variant-vocabulary": fsr.DISPOSITION_ALIASED_VARIANT_VOCABULARY,
    }

    # there is nothing in canonical order for the exhaust runner to visit -- the family/read-model
    # layer produces a valid, non-error, honestly-zero summary rather than crashing on an empty set.
    empty_family_registry = ff.build_family_registry({})
    assert empty_family_registry == {}

    # the EXHAUST RUNNER itself (not just the compiler/read-model layers) reaches valid terminal
    # completion over this epoch: walking every family in the manifest -- there are none -- and a
    # zero-eligible-variant family both return an empty result list rather than raising, and the
    # Foundry trial ledger ends the epoch with ZERO rows of any kind (no intent row, no terminal
    # row). TC-3's own wording is "when the runner exhausts it, then it reaches a valid terminal
    # completion state with zero terminal rows"; added by the iter-3 audit pass, which found the
    # runner clause of TC-3 unexercised.
    ledger = fl.FoundryLedger(tmp_path)
    manifest_hash = "manifest:all-non-compiled"
    visited = [
        row
        for fam in empty_family_registry.values()
        for row in fr.run_family(fam, [], ledger=ledger, econ_floor=_ECON_FLOOR_TINY, manifest_hash=manifest_hash)
    ]
    assert visited == []
    zero_variant_family = ff.build_family_registry({"family:all-non-compiled": []})["family:all-non-compiled"]
    assert ff.eligible_variant_ordinals(zero_variant_family) == ()
    assert fr.run_family(
        zero_variant_family, [], ledger=ledger, econ_floor=_ECON_FLOOR_TINY, manifest_hash=manifest_hash
    ) == []
    assert ledger.all_rows() == []
    assert ledger.verify_chain()["ok"] is True

    resolution = fi.resolve_population([], relation_kind="direct_scalar_membership")
    summary = fi.read_model(resolution)
    assert summary == {
        "total_anchors": 0, "eligible_anchors": 0, "unavailable_by_reason": {},
        "candidate_count": 0, "comparator_count": 0, "usable_sessions": [],
    }


# === TC-4: an all-killed epoch (every FROZEN_READY variant terminates INSUFFICIENT/KILLED) =========
# completes validly with zero survivor rows. ==========================================================


def test_tc4_all_killed_epoch_completes_validly_with_zero_survivor_rows(monkeypatch, tmp_path):
    family_id = "family:all-killed"
    family = ff.build_family_registry({family_id: [f"{family_id}:{i}" for i in range(6)]})[family_id]

    plan = [
        ("insufficient", _insufficient_anchors(), _ECON_FLOOR_TINY, False),
        ("null", _null_anchors(11), _ECON_FLOOR_TINY, False),
        ("direction", _wrong_direction_anchors(12), _ECON_FLOOR_TINY, False),
        ("concentration", _concentration_anchors(13), _ECON_FLOOR_TINY, False),
        ("economic", _survive_anchors(14, effect_bps=40.0), _ECON_FLOOR_HUGE, False),
        ("fragile", _fragile_anchors(), _ECON_FLOOR_TINY, True),
    ]

    ledger = fl.FoundryLedger(tmp_path)
    manifest_hash = "manifest:all-killed"
    for i, (label, anchors, floor, needs_fragile_patch) in enumerate(plan):
        spec = _spec(i, family_id=family_id, family_count=6)
        if needs_fragile_patch:
            with monkeypatch.context() as m:
                m.setattr(scout, "_two_sided_p", lambda observed, null: 0.0001)
                row = fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=floor, manifest_hash=manifest_hash, family=family)
        else:
            row = fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=floor, manifest_hash=manifest_hash, family=family)
        assert row["foundry_state"] != "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN", label

    terminal_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL]
    assert len(terminal_rows) == 6
    assert all(r["foundry_state"] in ("EVALUATED_INSUFFICIENT", "EVALUATED_KILLED") for r in terminal_rows)
    assert sum(1 for r in terminal_rows if r["foundry_state"] == "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN") == 0


# === TC-5: a multi-survivor epoch preserves EVERY survivor -- no ranking/selection/demotion. ========


def test_tc5_multi_survivor_epoch_preserves_every_survivor_with_no_ranking(tmp_path):
    family_id = "family:multi-survivor"
    family = ff.build_family_registry({family_id: [f"{family_id}:{i}" for i in range(3)]})[family_id]

    variants = [
        (_spec(0, family_id=family_id, family_count=3), _survive_anchors(21, effect_bps=50.0)),
        (_spec(1, family_id=family_id, family_count=3), _null_anchors(22)),  # kill in the middle
        (_spec(2, family_id=family_id, family_count=3), _survive_anchors(23, effect_bps=70.0)),
    ]
    ledger = fl.FoundryLedger(tmp_path)
    manifest_hash = "manifest:multi-survivor"
    results = [
        fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=_ECON_FLOOR_TINY, manifest_hash=manifest_hash, family=family)
        for spec, anchors in variants
    ]

    assert results[0]["foundry_state"] == "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"
    assert results[1]["foundry_state"] != "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"
    assert results[2]["foundry_state"] == "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"

    survivor_hashes = {results[0]["candidate_spec_hash"], results[2]["candidate_spec_hash"]}
    assert len(survivor_hashes) == 2  # both distinct survivors are present, neither dropped

    # No ranking/selection: both survivor terminal rows carry the SAME frozen family denominator
    # and neither embeds any comparison to the other (no "winner" field/ordering exists at all --
    # the ledger simply holds two independent terminal rows, exactly like it holds the killed one).
    for row in (results[0], results[2]):
        assert row["foundry_family_variant_count"] == 3
    terminal_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL]
    assert len(terminal_rows) == 3  # every candidate recorded, none demoted/omitted
    assert sum(1 for r in terminal_rows if r["foundry_state"] == "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN") == 2


# === TC-6: a large-N synthetic fixture spanning multiple families, with a simulated mid-epoch =======
# crash -- resume reconstructs position from the Foundry trial ledger, never a stale checkpoint. ======


_CRASH_FAMILY_LETTERS = ("A", "B", "C", "D")
_CRASH_VARIANTS_PER_FAMILY = 5


def _crash_fixture_variants() -> list[tuple[str, fc.CandidateSpec, list[fi.PopulationAnchor]]]:
    """20 candidates (4 families x 5 variants), in canonical order: family order, then ordinal
    within family. Every 5th variant is a guaranteed ``EVALUATED_INSUFFICIENT``; the rest are
    guaranteed ``survive``s -- the specific MIX does not matter for this TC (only checkpoint/resume
    integrity does); what matters is that 20 real candidates go through the real production path."""
    family_ids = {f"family:crash-{letter}": [f"family:crash-{letter}:{i}" for i in range(_CRASH_VARIANTS_PER_FAMILY)] for letter in _CRASH_FAMILY_LETTERS}
    registry = ff.build_family_registry(family_ids)
    out = []
    global_i = 0
    for letter in _CRASH_FAMILY_LETTERS:
        family_id = f"family:crash-{letter}"
        family = registry[family_id]
        for ordinal in range(_CRASH_VARIANTS_PER_FAMILY):
            spec = _spec(ordinal, family_id=family_id, family_count=_CRASH_VARIANTS_PER_FAMILY)
            if global_i % 5 == 0:
                anchors = _insufficient_anchors()
            else:
                anchors = _survive_anchors(1000 + global_i, effect_bps=55.0)
            out.append((family_id, family, spec, anchors))
            global_i += 1
    return out


def test_tc6_large_scale_checkpoint_resume_after_a_simulated_mid_epoch_crash(tmp_path):
    all_variants = _crash_fixture_variants()
    assert len(all_variants) == len(_CRASH_FAMILY_LETTERS) * _CRASH_VARIANTS_PER_FAMILY == 20
    manifest_hash = "manifest:crash-resume"

    # --- run #1: process only the FIRST 12 candidates (families A, B fully done, C's first two
    # ordinals done) then "crash" -- drop every in-memory object, including the ledger instance. ---
    ledger_run1 = fl.FoundryLedger(tmp_path)
    pre_crash_rows = []
    for family_id, family, spec, anchors in all_variants[:12]:
        row = fr.run_one_candidate(spec, anchors, ledger=ledger_run1, econ_floor=_ECON_FLOOR_TINY, manifest_hash=manifest_hash, family=family)
        pre_crash_rows.append(row)
    assert len([r for r in ledger_run1.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL]) == 12
    del ledger_run1  # simulate the crash: no Python-level state survives

    # --- run #2 ("resume"): a BRAND NEW FoundryLedger instance re-opened on the SAME on-disk
    # directory, with NO memory of where run #1 left off -- it deliberately re-visits the FULL
    # canonical sequence from ordinal 0 rather than trusting any external "resume from candidate 12"
    # position hint, proving position is reconstructed from the LEDGER's own already-terminal rows,
    # never from a stale/assumed checkpoint. -------------------------------------------------------
    ledger_run2 = fl.FoundryLedger(tmp_path)
    post_crash_rows = []
    for family_id, family, spec, anchors in all_variants:
        row = fr.run_one_candidate(spec, anchors, ledger=ledger_run2, econ_floor=_ECON_FLOOR_TINY, manifest_hash=manifest_hash, family=family)
        post_crash_rows.append(row)

    # every already-terminal candidate (the first 12) verified+skipped -- byte-identical to what
    # run #1 already recorded, no re-execution, no duplicate row.
    for i in range(12):
        assert post_crash_rows[i] == pre_crash_rows[i]

    all_rows = ledger_run2.all_rows()
    terminal_rows = [r for r in all_rows if r["row_kind"] == fl.ROW_KIND_TERMINAL]
    assert len(terminal_rows) == 20  # exactly one terminal row per candidate, zero duplicates

    # canonical order held across the crash boundary: terminal rows appear in the SAME order the
    # full 20-candidate sequence defines.
    expected_hash_order = [spec.candidate_spec_hash for _, _, spec, _ in all_variants]
    assert [r["candidate_spec_hash"] for r in terminal_rows] == expected_hash_order

    # the chain itself verifies clean end to end (append-only hash-chain integrity survived the
    # simulated crash/resume boundary).
    assert ledger_run2.verify_chain()["ok"] is True

    # the remaining 8 (indices 12..19) genuinely executed fresh this run -- not silently skipped.
    assert len(post_crash_rows) == 20
    n_insufficient = sum(1 for r in post_crash_rows if r["foundry_state"] == "EVALUATED_INSUFFICIENT")
    assert n_insufficient == 4  # indices 0, 5, 10, 15 -- global_i % 5 == 0


# === TC-7: a hermetic population source that raises MicroAccessorSealedShardError/ ==================
# MicroAccessorOriginFenceError during anchor resolution -- the Foundry side fails closed. ===========


def _population_source_raising(exc: Exception, *, n_good: int = 5):
    """A hermetic stand-in for a real anchor-extraction step (J-06/J-07 territory, not built this
    iteration): yields ``n_good`` legitimate anchors, then raises ``exc`` -- simulating discovering a
    sealed/origin-fenced dataset id partway through building one candidate's own population. A lazy
    generator (never a plain list) so the raise happens DURING ``foundry_interpreter.resolve_population``'s
    own iteration, exactly where a real accessor call would sit."""
    for i in range(n_good):
        yield _anchor("2026-08-01", i, "AAPL", i % 2 == 0, 5.0 if i % 2 == 0 else -5.0)
    raise exc


@pytest.mark.parametrize(
    "exc_factory",
    [
        lambda: MicroAccessorSealedShardError("hermetic-sealed-shard-1"),
        lambda: MicroAccessorOriginFenceError("origin fence tripped for hermetic-fenced-shard-1"),
    ],
    ids=["sealed_shard", "origin_fence"],
)
def test_tc7_a_protected_data_trip_during_anchor_resolution_fails_closed(tmp_path, exc_factory):
    family_id = "family:protected-trip"
    family = ff.build_family_registry({family_id: [f"{family_id}:0"]})[family_id]
    spec = _spec(0, family_id=family_id, family_count=1)
    ledger = fl.FoundryLedger(tmp_path)

    exc_type = type(exc_factory())
    with pytest.raises(exc_type):
        fr.run_one_candidate(
            spec, _population_source_raising(exc_factory()), ledger=ledger, econ_floor=_ECON_FLOOR_TINY,
            manifest_hash="manifest:protected-trip", family=family,
        )

    # fail-closed: no terminal EVALUATED_*/survivor row was ever written for this candidate.
    assert ledger.terminal_row_for(spec.candidate_spec_hash) is None
    # the intent row (recorded BEFORE anchor resolution/screening, per §6 step 4) is a legitimate
    # "evaluation started" record, not an evaluated/terminal state -- it may exist, but nothing
    # downstream of it does.
    for row in ledger.all_rows():
        assert row["row_kind"] != fl.ROW_KIND_TERMINAL


def test_tc7_no_new_accessor_abstraction_is_introduced():
    """The reused exception types are the REAL, existing ``micro_accessor`` ones -- no Foundry-local
    subclass/wrapper/parallel evidence-control exception type exists anywhere in this module."""
    import app.research.micro_accessor as micro_accessor_module

    assert MicroAccessorSealedShardError is micro_accessor_module.MicroAccessorSealedShardError
    assert MicroAccessorOriginFenceError is micro_accessor_module.MicroAccessorOriginFenceError


# === TC-8: across the whole oracle suite, every evidence_class is the fixed literal =================
# `historical_exposed_diagnostic` -- no code path in this suite ever sets any other value. ===========


def test_tc8_every_screen_result_evidence_class_across_the_suite_is_historical_exposed_diagnostic(monkeypatch, tmp_path):
    family_id = "family:evidence-class-sweep"
    labelled_plan = [
        (_insufficient_anchors(), _ECON_FLOOR_TINY, False),
        (_null_anchors(31), _ECON_FLOOR_TINY, False),
        (_wrong_direction_anchors(32), _ECON_FLOOR_TINY, False),
        (_concentration_anchors(33), _ECON_FLOOR_TINY, False),
        (_survive_anchors(34, effect_bps=40.0), _ECON_FLOOR_HUGE, False),
        (_fragile_anchors(), _ECON_FLOOR_TINY, True),
        (_survive_anchors(36, effect_bps=60.0), _ECON_FLOOR_TINY, False),
    ]
    family = ff.build_family_registry({family_id: [f"{family_id}:{i}" for i in range(len(labelled_plan))]})[family_id]
    ledger = fl.FoundryLedger(tmp_path)
    for i, (anchors, floor, needs_fragile_patch) in enumerate(labelled_plan):
        spec = _spec(i, family_id=family_id, family_count=len(labelled_plan))
        if needs_fragile_patch:
            with monkeypatch.context() as m:
                m.setattr(scout, "_two_sided_p", lambda observed, null: 0.0001)
                fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=floor, manifest_hash="manifest:evidence-sweep", family=family)
        else:
            fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=floor, manifest_hash="manifest:evidence-sweep", family=family)

    terminal_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL]
    assert len(terminal_rows) == len(labelled_plan)
    for row in terminal_rows:
        evidence_class = row["screen_result"]["screen_result"]["evidence_class"]
        assert evidence_class == scout.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC == "historical_exposed_diagnostic"
        assert evidence_class not in ("historical_oos", "live_confirmatory")
