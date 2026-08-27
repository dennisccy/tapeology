"""The Hypothesis Foundry -- the generic candidate interpreter (spec §4). Turns an already
population-extracted set of candidate/comparator-eligible anchors into the boolean membership the
existing Scout screen consumes, and calls ``scout.screen_candidate`` directly (never the
registration/ledger path -- spec §4.2.1). See ``docs/hypothesis-foundry-spec.md`` §4 and
``docs/goal.md``'s Foundry Constitution §4 for the full rationale this module implements verbatim.

**Scope this iteration (goal-hypothesis-foundry-iter-2, J-03).** This module does not read a
dataset or call ``micro_join``/``micro_observer`` itself -- it operates on ``PopulationAnchor``
rows a caller (a hermetic test fixture today; a future real extraction step at J-06/J-07) has
already produced: one row per candidate/comparator-eligible opportunity, each carrying its own
per-conditioning-component resolution state (``ComponentResolution``). This mirrors
``foundry_compiler.py``'s own precedent of taking an already-authored ``CandidateBlueprint`` rather
than deriving content from prose at compile time -- here the interpreter takes already-resolved
per-component values rather than re-deriving "is `high` true" from a raw tick stream itself. What
IS this module's own job, and the reason it exists rather than reusing ``scout.extract_anchors``
directly, is exactly the four things spec §4 assigns the interpreter: (1) population-symmetric
component-resolution/exclusion accounting across an arbitrary conditioning set (§4.1), (2) the
timing law ``candidate_available_at = outcome_start = max(component.available_at)`` (§4.1.3-4),
(3) frozen membership-corner evaluation over that resolved set (§4.1.6), and (4) collapsing the
result to a boolean and calling the existing Scout screen with no second statistical rail (§4.2).

**Why membership-corner evaluation is a closed per-``relation.kind`` dispatch, not a parsed
expression.** ``CandidateCoordinate.threshold_corner_predicate`` is descriptive text (e.g.
``"quote_imbalance > 0"``) frozen for provenance/audit -- exactly like ``foundry_compiler.py``
never parses ``mechanism_statement`` at compile time, this module never ``eval()``s
``threshold_corner_predicate`` at interpret time (that would be exactly the "runtime LLM/string-
based interpretation" the goal's anti-goals forbid a hair's breadth from). Instead each
``ComponentResolution`` a caller supplies already carries its own ``corner_satisfied: bool | None``
-- the per-coordinate corner truth, evaluated by whatever authored the fixture/extraction row using
that coordinate's own frozen ``threshold_provenance``/``transform_orientation`` (a mechanical,
typed decision, never string-parsed here). This module's own job is then only to COMBINE those
already-evaluated per-component corners according to the CandidateSpec's frozen ``relation.kind``:
``direct_scalar_membership`` (exactly one coordinate; membership = that one corner) or
``conjunction`` (all coordinates; membership = every corner true). Any other ``relation.kind`` --
an ordered/sequenced lag with no frozen window, the only ordered form this era's source scope ever
raises (goal.md §12) -- is not one of these two closed forms and interpretation blocks with
``BLOCKED_UNSUPPORTED_RELATION`` rather than guessing a window (TC-8)."""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping, Sequence

from . import micro_features as mf
from . import scout

__all__ = [
    "SUPPORTED_RELATION_KINDS",
    "BLOCKED_UNSUPPORTED_RELATION",
    "UnsupportedRelationBlocked",
    "FOUNDRY_BOUNDARY_FEATURE_LABEL",
    "FOUNDRY_BOUNDARY_TRANSFORM",
    "FOUNDRY_BOUNDARY_PARAMS",
    "ComponentResolution",
    "PopulationAnchor",
    "ResolvedAnchor",
    "PopulationResolution",
    "InterpretationResult",
    "resolve_population",
    "project_boolean_membership",
    "read_model",
    "interpret_candidate",
    "interpreter_hermetic_fixture_view",
]

# --- §4.1's two closed relation forms this era's compiled sources can ever need (goal.md §12: "Do
# not treat the mere existence of two features in code as permission to enumerate"; the ordered
# form is the ONLY unsupported relation named anywhere in the source scope, so it is the one this
# module blocks rather than builds bespoke code for). ------------------------------------------
RELATION_DIRECT_SCALAR = "direct_scalar_membership"
RELATION_CONJUNCTION = "conjunction"
SUPPORTED_RELATION_KINDS = frozenset({RELATION_DIRECT_SCALAR, RELATION_CONJUNCTION})

BLOCKED_UNSUPPORTED_RELATION = "BLOCKED_UNSUPPORTED_RELATION"


class UnsupportedRelationBlocked(Exception):
    """Raised (never silently produces a guessed window) when a ``CandidateSpec.relation.kind`` is
    outside ``SUPPORTED_RELATION_KINDS`` -- spec §4/§12, TC-8. Carries ``.disposition`` so a caller
    can record the typed block without string-matching the message."""

    def __init__(self, relation_kind: str) -> None:
        super().__init__(
            f"relation.kind={relation_kind!r} is not one of this era's supported closed forms "
            f"{sorted(SUPPORTED_RELATION_KINDS)!r} -- {BLOCKED_UNSUPPORTED_RELATION}, no ordered "
            "lag/window is ever guessed"
        )
        self.disposition = BLOCKED_UNSUPPORTED_RELATION
        self.relation_kind = relation_kind


# --- §4.2's Scout-boundary encoding: a fixed, non-scientific orchestration label + the mechanical
# `threshold` / `feature_value >= 1.0` transform. Never a member of `scout.AGGRESSOR_DERIVED_
# FEATURES` (a synthetic boolean-membership column is never itself an aggressor-derived raw
# feature) so `scout._fallback_tercile_slices` correctly renders `None` for every Foundry trial --
# the adapter must not "pretend this synthetic membership is an existing scientific feature" (§4.2).
FOUNDRY_BOUNDARY_FEATURE_LABEL = "foundry_boolean_membership"
FOUNDRY_BOUNDARY_TRANSFORM = "threshold"
FOUNDRY_BOUNDARY_PARAMS: Mapping[str, object] = {"op": "ge", "value": 1.0}


@dataclass(frozen=True)
class ComponentResolution:
    """One conditioning component's resolution outcome for one population anchor (spec §4.1 step
    1). ``resolved=False`` means this component never fired/joined for this anchor -- the ANCHOR is
    then excluded from both cells per ``unresolved_component_policy=exclude_and_count`` (step 2);
    ``available_at``/``raw_value``/``corner_satisfied`` are only meaningful (non-``None``) when
    ``resolved=True``."""

    component_id: str
    resolved: bool
    available_at: float | None
    raw_value: float | None
    corner_satisfied: bool | None
    unavailable_reason: str | None = None


@dataclass(frozen=True)
class PopulationAnchor:
    """One raw pre-Scout-boundary population anchor. Every field ``scout.screen_candidate``
    ultimately needs downstream (everything ``scout._extract_none_anchors`` et al. already produce
    per anchor row) rides straight through into the Scout-facing anchor untouched;
    ``feature_value`` itself is deliberately ABSENT here -- ``project_boolean_membership`` is the
    only place that ever adds it, always as the 1.0/0.0 boolean encoding (§4.2), never a raw
    magnitude."""

    dataset_id: str
    symbol: str
    session_date: str
    trade_index: int
    tod_bucket: str | None
    fallback_frac: float | None
    outcome_bps: float
    outcome_unit: str
    components: tuple[ComponentResolution, ...]


@dataclass(frozen=True)
class ResolvedAnchor:
    """One eligible (every conditioning component resolved) population anchor after §4.1's timing
    law and membership-corner evaluation."""

    anchor: PopulationAnchor
    candidate_available_at: float
    outcome_start: float
    is_candidate: bool


@dataclass(frozen=True)
class PopulationResolution:
    total_anchors: int
    eligible: tuple[ResolvedAnchor, ...]
    unavailable_by_reason: Mapping[str, int]


def _evaluate_membership(components: Sequence[ComponentResolution], relation_kind: str) -> bool:
    """§4.1 step 6: the frozen membership corner, evaluated as a closed dispatch over the SET of
    already-resolved per-component corners -- see this module's own docstring for why this is a
    typed dispatch, never a parsed expression."""
    if relation_kind == RELATION_DIRECT_SCALAR:
        if len(components) != 1:
            raise ValueError(
                f"relation.kind={RELATION_DIRECT_SCALAR!r} requires exactly one coordinate/"
                f"component, got {len(components)}"
            )
        return bool(components[0].corner_satisfied)
    if relation_kind == RELATION_CONJUNCTION:
        return all(bool(c.corner_satisfied) for c in components)
    raise UnsupportedRelationBlocked(relation_kind)


def resolve_population(
    anchors: Sequence[PopulationAnchor], *, relation_kind: str
) -> PopulationResolution:
    """§4.1 steps 1-6, in full:

    1. every anchor's conditioning components are already resolved-or-not by the caller (this
       module's own scope boundary -- see the module docstring);
    2. an anchor with ANY unresolved component is excluded from BOTH cells and counted under its
       first unresolved component's own typed reason (deterministic: ``anchor.components`` is an
       ordered tuple, so "first" never varies run to run);
    3. ``candidate_available_at = max(component.available_at)`` over the anchor's own resolved set;
    4. ``outcome_start`` is computed by calling the existing timing helper directly
       (``micro_features.resolve_outcome_start``) over that SAME resolved ``available_at`` set --
       there is no further offset in this era's Foundry integration, so this call always returns
       exactly ``candidate_available_at`` (matching TC-6's own "share
       `outcome_start=max(available_at)`" assertion), but it is the helper itself that is called,
       never a second, independently-written ``max()`` -- so a future change to that helper's own
       rule is inherited here automatically rather than silently diverging;
    5-6. the same canonical outcome (``outcome_bps``, already measured identically for every
       eligible anchor regardless of which cell it lands in) and the frozen membership corner are
       evaluated for every eligible anchor -- population-symmetric by construction: an anchor's
       cell membership is decided ONLY by ``_evaluate_membership``, never by a different timing or
       outcome rule for candidate vs. comparator.

    Raises ``UnsupportedRelationBlocked`` (TC-8) before touching any anchor when ``relation_kind``
    is outside ``SUPPORTED_RELATION_KINDS`` -- checked first so an unsupported relation never
    silently walks a (possibly empty) anchor list and appears to "succeed" trivially."""
    if relation_kind not in SUPPORTED_RELATION_KINDS:
        raise UnsupportedRelationBlocked(relation_kind)

    unavailable_by_reason: dict[str, int] = defaultdict(int)
    eligible: list[ResolvedAnchor] = []
    for anchor in anchors:
        unresolved = [c for c in anchor.components if not c.resolved]
        if unresolved:
            reason = unresolved[0].unavailable_reason or "component_unresolved"
            unavailable_by_reason[reason] += 1
            continue
        conditioning_available_at = [c.available_at for c in anchor.components]  # type: ignore[misc]
        candidate_available_at = mf.resolve_outcome_start(conditioning_available_at)
        outcome_start = mf.resolve_outcome_start(conditioning_available_at)  # the existing timing
        # helper, called directly (never a second, independently-written max()) -- see the
        # docstring paragraph above for why the two calls are guaranteed identical this era.
        is_candidate = _evaluate_membership(anchor.components, relation_kind)
        eligible.append(
            ResolvedAnchor(
                anchor=anchor, candidate_available_at=candidate_available_at,
                outcome_start=outcome_start, is_candidate=is_candidate,
            )
        )

    return PopulationResolution(
        total_anchors=len(anchors), eligible=tuple(eligible), unavailable_by_reason=dict(unavailable_by_reason),
    )


def project_boolean_membership(resolution: PopulationResolution) -> list[dict]:
    """§4.2: every eligible anchor becomes ONE Scout-canonical anchor dict, with
    ``feature_value = 1.0`` when the frozen corner was true, else ``0.0`` -- the ONLY value that
    ever reaches the Scout boundary; raw coordinate values never appear on the returned dict (TC-5:
    "raw coordinates remain descriptive provenance", never a Scout-facing feature)."""
    projected: list[dict] = []
    for resolved in resolution.eligible:
        a = resolved.anchor
        projected.append(
            {
                "dataset_id": a.dataset_id,
                "symbol": a.symbol,
                "session_date": a.session_date,
                "anchor_at": resolved.outcome_start,
                "trade_index": a.trade_index,
                "feature_value": 1.0 if resolved.is_candidate else 0.0,
                "outcome_bps": a.outcome_bps,
                "outcome_unit": a.outcome_unit,
                "tod_bucket": a.tod_bucket,
                "fallback_frac": a.fallback_frac,
            }
        )
    return projected


def read_model(resolution: PopulationResolution) -> dict:
    """§4.1's own required read model: total source anchors, eligible resolved anchors,
    unavailable/excluded anchors by typed reason, candidate count, comparator count, and common
    usable sessions (sessions with at least one anchor in EACH cell -- the same
    ``usable_sessions`` law ``scout.screen_candidate`` itself applies)."""
    candidate_count = sum(1 for r in resolution.eligible if r.is_candidate)
    comparator_count = len(resolution.eligible) - candidate_count
    cand_sessions = {r.anchor.session_date for r in resolution.eligible if r.is_candidate}
    comp_sessions = {r.anchor.session_date for r in resolution.eligible if not r.is_candidate}
    usable_sessions = sorted(cand_sessions & comp_sessions)
    return {
        "total_anchors": resolution.total_anchors,
        "eligible_anchors": len(resolution.eligible),
        "unavailable_by_reason": dict(resolution.unavailable_by_reason),
        "candidate_count": candidate_count,
        "comparator_count": comparator_count,
        "usable_sessions": usable_sessions,
    }


@dataclass(frozen=True)
class InterpretationResult:
    read_model: Mapping[str, object]
    screen: Mapping[str, object]


def interpret_candidate(
    spec, anchors: Sequence[PopulationAnchor], *, econ_floor: dict, family_id: str, n_variants_tried: int,
) -> InterpretationResult:
    """The full §4 pipeline for one ``CandidateSpec`` (``foundry_compiler.CandidateSpec``):
    population resolution -> boolean projection -> the Scout-boundary adapter (§4.2.1) -- calling
    ``scout.screen_candidate`` DIRECTLY on the pre-extracted, already-boolean-projected anchors,
    never the Scout registration/ledger path (so this call alone can never write a Scout ledger
    row -- TC-18's boundary). ``family_id``/``n_variants_tried`` are passed straight through to
    ``scout.screen_candidate`` -- the SAME ``family_id``/permutation-seed scope the direct Scout
    path uses (TC-4), and the complete frozen Foundry-family denominator (``foundry_family.py``'s
    own job to compute -- this function never derives it itself, spec §5.3)."""
    resolution = resolve_population(anchors, relation_kind=spec.relation.kind)
    scout_anchors = project_boolean_membership(resolution)
    screen = scout.screen_candidate(
        feature_name=FOUNDRY_BOUNDARY_FEATURE_LABEL,
        transform=FOUNDRY_BOUNDARY_TRANSFORM,
        params=dict(FOUNDRY_BOUNDARY_PARAMS),
        sidedness=spec.outcome.sidedness,
        horizon_key=spec.outcome.horizon_key,
        econ_floor=econ_floor,
        anchors=scout_anchors,
        family_id=family_id,
        n_variants_tried=n_variants_tried,
    )
    return InterpretationResult(read_model=read_model(resolution), screen=screen)


_FIXTURE_ECON_FLOOR: Mapping[str, object] = {
    "floor_bps": 0.0, "unit": "bps", "rule": "scout_quoted_spread_floor", "multiple": 0.0,
}


def _fixture_spec(*, relation_kind: str, coordinates: tuple, membership_corner: str, sidedness: str = "long"):
    """A minimal, self-contained ``CandidateSpec`` builder for this module's own hermetic fixture
    view -- the SAME shape ``test_foundry_interpreter.py``'s own ``_spec`` helper builds, but
    defined here (not imported from ``tests/``) so this production subview stays self-contained.
    Local import avoids a module-load-time cycle (``foundry_compiler`` never imports THIS module,
    so this is safe at any point, but importing lazily keeps the cycle direction obviously one-way
    to a future reader)."""
    from . import foundry_compiler as fc

    return fc.CandidateSpec(
        foundry_spec_version="v1", epoch_id="epoch:hermetic-fixture-interpreter",
        source_ids=("fixture-interpreter-src",), lineage_id="fixture-interpreter-src",
        foundry_family_id="family:fixture-interpreter-src", variant_id="family:fixture-interpreter-src:0",
        variant_ordinal=0,
        population=fc.CandidatePopulation(structure_context_kind="none", side_filter=None, setup_context_id=None),
        coordinates=coordinates, relation=fc.CandidateRelation(kind=relation_kind),
        membership_corner=membership_corner,
        outcome=fc.CandidateOutcome(horizon_key="trades_20", sidedness=sidedness),
        economic_floor_rule=fc.EconomicFloorRule(), foundry_family_variant_count=1,
    ).with_hash()


def interpreter_hermetic_fixture_view() -> dict:
    """The ``interpreter_fixtures`` Foundry read-surface subview (goal-hypothesis-foundry-iter-4,
    J-03): the SAME 5 hermetic scenario shapes already proven in ``test_foundry_interpreter.py``
    (immediate-scalar Foundry-vs-direct-Scout equivalence, conjunction, deferred
    ``refill_consistent``, mirrored support-long/resistance-short, unsupported ordered relation),
    run through the REAL ``resolve_population``/``interpret_candidate`` pipeline -- never a
    hand-typed expected screen. A pure, deterministic function (fixed random seeds) --
    ``micro_routes.py`` calls this exactly ONCE (module-import time), never per request."""
    from . import foundry_compiler as fc

    scenarios: list[dict] = []

    # --- 1. immediate_scalar_equivalence: byte-identical Foundry-adapter vs. direct-Scout path. ---
    threshold = 1.0
    scalar_anchors: list[PopulationAnchor] = []
    for s in range(2):
        session = f"2026-08-{10 + s:02d}"
        for i in range(20):
            is_member = i % 2 == 0
            raw_value = 2.0 if is_member else 0.0
            outcome = 12.0 + (i % 5) if is_member else -1.0 + (i % 5) * 0.1
            comp = ComponentResolution("q_imbalance", True, float(i), raw_value, raw_value >= threshold)
            scalar_anchors.append(
                PopulationAnchor(f"ds-{session}", "AAPL", session, i, "mid", None, outcome, "return_bps", (comp,))
            )
    direct_anchors = [
        {
            "dataset_id": a.dataset_id, "symbol": a.symbol, "session_date": a.session_date,
            "anchor_at": a.components[0].available_at, "trade_index": a.trade_index,
            "feature_value": a.components[0].raw_value, "outcome_bps": a.outcome_bps,
            "outcome_unit": a.outcome_unit, "tod_bucket": a.tod_bucket, "fallback_frac": a.fallback_frac,
        }
        for a in scalar_anchors
    ]
    direct_result = scout.screen_candidate(
        feature_name="foundry_fixture_scalar_q_imbalance", transform="threshold",
        params={"op": "ge", "value": threshold}, sidedness="long", horizon_key="trades_20",
        econ_floor=_FIXTURE_ECON_FLOOR, anchors=direct_anchors,
        family_id="fixture-family-interpreter-scalar", n_variants_tried=1,
    )
    scalar_spec = _fixture_spec(
        relation_kind=RELATION_DIRECT_SCALAR,
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
    scalar_interpretation = interpret_candidate(
        scalar_spec, scalar_anchors, econ_floor=_FIXTURE_ECON_FLOOR,
        family_id="fixture-family-interpreter-scalar", n_variants_tried=1,
    )
    scenarios.append(
        {
            "scenario_id": "fixture-immediate-scalar-equivalence",
            "kind": "immediate_scalar_equivalence",
            "foundry_screen": scalar_interpretation.screen,
            "direct_scout_screen": direct_result,
            "screens_equal": scalar_interpretation.screen == direct_result,
            "unresolved_excluded_count": 0,
            "outcome_start_candidate": None,
            "outcome_start_comparator": None,
            "block_reason": None,
            "predeclared_sidedness": None,
        }
    )

    # --- 2. conjunction: only boolean membership crosses the Scout boundary. -----------------------
    conj_anchors: list[PopulationAnchor] = []
    for s in range(2):
        session = f"2026-08-{10 + s:02d}"
        for i in range(24):
            both_true = i % 3 == 0
            c1 = ComponentResolution("c1", True, float(i), 5.0 if both_true else 0.0, both_true)
            c2 = ComponentResolution("c2", True, float(i) + 0.5, 9.0 if both_true else 1.0, both_true)
            outcome = 15.0 if both_true else -0.5
            conj_anchors.append(
                PopulationAnchor(f"ds-{session}", "AAPL", session, i, "mid", None, outcome, "return_bps", (c1, c2))
            )
    conjunction_spec = _fixture_spec(
        relation_kind=RELATION_CONJUNCTION,
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
    conjunction_interpretation = interpret_candidate(
        conjunction_spec, conj_anchors, econ_floor=_FIXTURE_ECON_FLOOR,
        family_id="fixture-family-interpreter-conjunction", n_variants_tried=1,
    )
    scenarios.append(
        {
            "scenario_id": "fixture-conjunction",
            "kind": "conjunction",
            "foundry_screen": conjunction_interpretation.screen,
            "direct_scout_screen": None,
            "screens_equal": None,
            "unresolved_excluded_count": sum(conjunction_interpretation.read_model["unavailable_by_reason"].values()),
            "outcome_start_candidate": None,
            "outcome_start_comparator": None,
            "block_reason": None,
            "predeclared_sidedness": None,
        }
    )

    # --- 3. deferred_refill_consistent: unresolved anchors excluded from both cells; symmetric ------
    # outcome_start timing law. -----------------------------------------------------------------
    deferred_anchors: list[PopulationAnchor] = []
    deferred_session = "2026-08-10"
    for i in range(30):
        unresolved = i % 5 == 0
        member = i % 2 == 0
        if unresolved:
            comp = ComponentResolution("refill_consistent", False, None, None, None, unavailable_reason="refill_unresolved")
        else:
            comp = ComponentResolution("refill_consistent", True, float(i) + 3.0, 1.0 if member else 0.0, member)
        outcome = 10.0 if member else -2.0
        deferred_anchors.append(
            PopulationAnchor(f"ds-{deferred_session}", "AAPL", deferred_session, i, "mid", None, outcome, "return_bps", (comp,))
        )
    deferred_spec = _fixture_spec(
        relation_kind=RELATION_DIRECT_SCALAR,
        coordinates=(
            fc.CandidateCoordinate(
                feature_construct_id="refill_consistent", semantic_role="deferred_conjunct",
                transform_orientation="boolean", threshold_corner_predicate="refill_consistent == True",
                threshold_provenance="natural_semantic_boundary", aggressor_derived=False,
                unit_basis="boolean", anchor_at="touch", available_at="resolution",
                resolution_join_rule="deferred_via_observer_provenance_id",
            ),
        ),
        membership_corner="refill_consistent == True",
    )
    deferred_interpretation = interpret_candidate(
        deferred_spec, deferred_anchors, econ_floor=_FIXTURE_ECON_FLOOR,
        family_id="fixture-family-interpreter-deferred", n_variants_tried=1,
    )
    scenarios.append(
        {
            "scenario_id": "fixture-deferred-refill-consistent",
            "kind": "deferred_refill_consistent",
            "foundry_screen": deferred_interpretation.screen,
            "direct_scout_screen": None,
            "screens_equal": None,
            "unresolved_excluded_count": sum(deferred_interpretation.read_model["unavailable_by_reason"].values()),
            # §4.1: both cells share the SAME `outcome_start = max(component.available_at)` rule --
            # rendered as the one shared literal both sides use (`foundry_compiler.AVAILABILITY_
            # RULE`), never a divergent per-side formula.
            "outcome_start_candidate": fc.AVAILABILITY_RULE,
            "outcome_start_comparator": fc.AVAILABILITY_RULE,
            "block_reason": None,
            "predeclared_sidedness": None,
        }
    )

    # --- 4. mirrored_direction: predeclared sidedness on BOTH sides, shown before any outcome. ------
    mirrored_anchors: list[PopulationAnchor] = []
    for s in range(4):
        session = f"2026-08-{10 + s:02d}"
        order = list(range(40))
        random.Random(s).shuffle(order)
        members = set(order[:20])
        for i in range(40):
            member = i in members
            comp = ComponentResolution("wall_reject", True, float(i), 1.0 if member else 0.0, member)
            outcome = -80.0 + (i % 5) * 0.1 if member else 0.05 * (i % 5)
            mirrored_anchors.append(
                PopulationAnchor(f"ds-{session}", "AAPL", session, i, "mid", None, outcome, "return_bps", (comp,))
            )
    # A resistance/short thesis realizes a POSITIVE thesis-relative return exactly when the raw
    # canonical `return_bps` (Constraints: `(mid_horizon - mid_start) / mid_start * 10_000`) is
    # negative -- shorting profits from a price fall. The support/long side below uses the raw
    # anchors verbatim; the resistance/short side uses the SAME membership/timing but the sign-
    # negated outcome a short position would realize on that same market (goal §3.2: "aggression-
    # toward-wall signing is mechanically buy->resistance / sell->support") -- never a second
    # statistical rail, only the thesis-relative sign a real short extraction step would already
    # apply before this era's unchanged Scout direction gate (`effect_bps > 0`) ever runs.
    mirrored_coord = fc.CandidateCoordinate(
        feature_construct_id="wall_reject", semantic_role="candidate_signal", transform_orientation="ge",
        threshold_corner_predicate="wall_reject >= 1", threshold_provenance="natural_semantic_boundary",
        aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
    )
    short_anchors = [
        PopulationAnchor(
            a.dataset_id, a.symbol, a.session_date, a.trade_index, a.tod_bucket, a.fallback_frac,
            -a.outcome_bps, a.outcome_unit, a.components,
        )
        for a in mirrored_anchors
    ]
    support_long_spec = _fixture_spec(
        relation_kind=RELATION_DIRECT_SCALAR, coordinates=(mirrored_coord,),
        membership_corner="wall_reject >= 1", sidedness="long",
    )
    resistance_short_spec = _fixture_spec(
        relation_kind=RELATION_DIRECT_SCALAR, coordinates=(mirrored_coord,),
        membership_corner="wall_reject >= 1", sidedness="short",
    )
    support_long_result = interpret_candidate(
        support_long_spec, mirrored_anchors, econ_floor=_FIXTURE_ECON_FLOOR,
        family_id="fixture-family-interpreter-mirrored-long", n_variants_tried=1,
    )
    resistance_short_result = interpret_candidate(
        resistance_short_spec, short_anchors, econ_floor=_FIXTURE_ECON_FLOOR,
        family_id="fixture-family-interpreter-mirrored-short", n_variants_tried=1,
    )
    scenarios.append(
        {
            "scenario_id": "fixture-mirrored-support-long-resistance-short",
            "kind": "mirrored_direction",
            "foundry_screen": {
                "support_long": support_long_result.screen,
                "resistance_short": resistance_short_result.screen,
            },
            "direct_scout_screen": None,
            "screens_equal": None,
            "unresolved_excluded_count": 0,
            "outcome_start_candidate": None,
            "outcome_start_comparator": None,
            "block_reason": None,
            # Additive (goal.md's own "canonical values" lists are floors, not ceilings): the
            # predeclared `long`/`short` sidedness is already fixed on each CandidateSpec BEFORE
            # either screen above ever ran -- J-03 step 4's own acceptance ("predeclared sidedness
            # is inside CandidateSpec before the outcome").
            "predeclared_sidedness": {
                "support_long": support_long_spec.outcome.sidedness,
                "resistance_short": resistance_short_spec.outcome.sidedness,
            },
        }
    )

    # --- 5. unsupported_ordered_relation: typed block, never a guessed window/lag. -------------------
    ordered_coord = fc.CandidateCoordinate(
        feature_construct_id="thin_then_refill", semantic_role="candidate_signal", transform_orientation="ge",
        threshold_corner_predicate="ordered lag unresolved", threshold_provenance=None, aggressor_derived=False,
        unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
    )
    ordered_spec = _fixture_spec(
        relation_kind="ordered_sequence_lag", coordinates=(ordered_coord,),
        membership_corner="ordered_lag_unresolved",
    )
    try:
        interpret_candidate(ordered_spec, [], econ_floor=_FIXTURE_ECON_FLOOR, family_id="f", n_variants_tried=1)
    except UnsupportedRelationBlocked as exc:
        block_reason = exc.disposition
    else:  # pragma: no cover -- this relation kind is never supported
        block_reason = None
    scenarios.append(
        {
            "scenario_id": "fixture-unsupported-ordered-relation",
            "kind": "unsupported_ordered_relation",
            "foundry_screen": None,
            "direct_scout_screen": None,
            "screens_equal": None,
            "unresolved_excluded_count": None,
            "outcome_start_candidate": None,
            "outcome_start_comparator": None,
            "block_reason": block_reason,
            "predeclared_sidedness": None,
        }
    )

    return {"scenarios": scenarios}
