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
