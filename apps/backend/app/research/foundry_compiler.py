"""The Hypothesis Foundry -- the compiler: the canonical ``CandidateSpec`` schema (spec §3) and
compilation of ``COMPILED``-disposition ``SourceRecord``s (``foundry_source_registry.py``) into
real ``CandidateSpec`` objects. See ``docs/hypothesis-foundry-spec.md`` §3 for the schema
rationale and the hash discipline this module implements verbatim.

**Scope this iteration (goal-hypothesis-foundry-iter-1).** Deferred/population-resolution
machinery -- the generic interpreter that would derive ``coordinates``/``population``/``outcome``
content from a ``mechanism_statement``'s own prose, or resolve a multi-coordinate/deferred
membership corner -- is ``foundry_interpreter.py``, explicitly future work (``docs/goal.md``
Binding Execution Order step 3 / J-03). This module only compiles a source whose scientific
content is ALREADY fully resolved and non-deferred: the caller of ``compile_sources`` passes
one ``CandidateBlueprint`` per compileable ``source_id`` -- the rest of the §3 schema, already
frozen by the same audited authoring act that filled in the record's §1.4 fields, exactly as
mechanical as those fields are (never derived from parsing ``mechanism_statement`` text at
compile time). A record this module cannot build a spec for despite reaching ``COMPILED`` (no
blueprint supplied, or one naming a deferred join) is left ``FROZEN_READY``-incomplete this
revision rather than approximated -- see ``docs/hypothesis-foundry-spec.md`` §12."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

from . import scout
from .foundry_source_registry import (
    DISPOSITION_COMPILED,
    SourceRecord,
    compile_source_disposition,
    lint_quoted_spans,
    source_registry_hash as _registry_hash,
)

__all__ = [
    "AVAILABILITY_RULE",
    "UNRESOLVED_COMPONENT_POLICY",
    "COMPARATOR_RULE",
    "OUTCOME_MEASURE",
    "CandidateCoordinate",
    "CandidatePopulation",
    "CandidateRelation",
    "CandidateOutcome",
    "EconomicFloorRule",
    "CandidateBlueprint",
    "CandidateSpec",
    "CompilationResult",
    "FamilyOrdinalCollision",
    "compile_sources",
    "compiler_hash",
]

# --- §3 frozen literal-valued fields -- named constants so a caller/test never re-types the
# literal string (and so a typo can't silently mint a second value that MEANS the same thing). ---
AVAILABILITY_RULE = "max_conditioning_available_at"
UNRESOLVED_COMPONENT_POLICY = "exclude_and_count"
COMPARATOR_RULE = "complement_within_same_eligible_population"
OUTCOME_MEASURE = "return_bps"


@dataclass(frozen=True)
class CandidateCoordinate:
    """One §3 ``coordinates[]`` entry. ``resolution_join_rule`` is ``"immediate"`` for every
    fixture this revision compiles (no deferred construct -- that is ``foundry_interpreter.py``'s
    future job); a non-``"immediate"`` value is accepted by the schema (future-proofing §3's own
    "if a deferred completion cannot be uniquely joined... compilation blocks" rule) but this
    module's ``compile_sources`` refuses to build a spec around one this revision."""

    feature_construct_id: str
    semantic_role: str
    transform_orientation: str
    threshold_corner_predicate: str
    threshold_provenance: str | None
    aggressor_derived: bool
    unit_basis: str
    anchor_at: str
    available_at: str
    resolution_join_rule: str = "immediate"


@dataclass(frozen=True)
class CandidatePopulation:
    structure_context_kind: str
    side_filter: str | None
    setup_context_id: str | None


@dataclass(frozen=True)
class CandidateRelation:
    kind: str
    parameters: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidateOutcome:
    horizon_key: str
    sidedness: str
    measure: str = OUTCOME_MEASURE

    def __post_init__(self) -> None:
        if self.horizon_key not in scout.HORIZON_KEYS:
            # §3.1: "Foundry candidates may use only horizon keys actually accepted by the existing
            # block-length rail... implementation must verify this from current code rather than
            # infer it." Verified against `scout.HORIZON_KEYS` directly, never a second literal set.
            raise ValueError(
                f"horizon_key {self.horizon_key!r} is not a legal Scout horizon "
                f"(scout.HORIZON_KEYS={sorted(scout.HORIZON_KEYS)!r})"
            )
        if self.sidedness not in ("long", "short"):
            raise ValueError(f"sidedness must be 'long' or 'short', got {self.sidedness!r}")


@dataclass(frozen=True)
class EconomicFloorRule:
    """§6: "the manifest freezes the existing economic-floor RULE, not a result-dependent floor
    number." ``numeric_floor_bps`` is always ``None`` out of this module -- it "materializes later
    before outcome read and cannot be back-filled" (§6/§3), which is real-epoch/exhaust-runner
    territory (J-07), not compile-time territory."""

    rule: str = "scout_quoted_spread_floor"
    multiple: float = 0.0
    numeric_floor_bps: float | None = None


@dataclass(frozen=True)
class CandidateBlueprint:
    """The non-deferred rest of the §3 schema a ``SourceRecord`` author already froze by hand --
    see this module's own docstring for why this is a fixture/hermetic-authoring input this
    revision, not a derivation."""

    population: CandidatePopulation
    coordinates: tuple[CandidateCoordinate, ...]
    relation: CandidateRelation
    membership_corner: str
    outcome: CandidateOutcome
    economic_floor_rule: EconomicFloorRule = field(default_factory=EconomicFloorRule)

    def is_immediate(self) -> bool:
        """``True`` only when every coordinate resolves without a deferred join -- the condition
        under which THIS module (rather than the future ``foundry_interpreter.py``) may compile
        it."""
        return all(c.resolution_join_rule == "immediate" for c in self.coordinates)


@dataclass(frozen=True)
class CandidateSpec:
    """The canonical, frozen scientific object (spec §3), implementing every required field.
    ``candidate_spec_hash`` (set by ``compile_sources``, never at construction) is a ``sha256``
    over every field below EXCEPT the four hash/pointer fields themselves
    (``manifest_hash``, ``source_registry_hash``, ``compiler_hash``, ``candidate_spec_hash``) --
    see ``_canonical_fields`` below and ``docs/hypothesis-foundry-spec.md`` §3."""

    foundry_spec_version: str
    epoch_id: str
    source_ids: tuple[str, ...]
    lineage_id: str
    foundry_family_id: str
    variant_id: str
    variant_ordinal: int
    population: CandidatePopulation
    coordinates: tuple[CandidateCoordinate, ...]
    relation: CandidateRelation
    membership_corner: str
    outcome: CandidateOutcome
    economic_floor_rule: EconomicFloorRule
    foundry_family_variant_count: int
    availability_rule: str = AVAILABILITY_RULE
    unresolved_component_policy: str = UNRESOLVED_COMPONENT_POLICY
    comparator: str = COMPARATOR_RULE
    manifest_hash: str | None = None
    source_registry_hash: str = ""
    compiler_hash: str = ""
    candidate_spec_hash: str = ""

    def _canonical_fields(self) -> dict:
        """Every field EXCEPT the four hash/pointer fields -- ``manifest_hash`` is excluded
        because it is computed FROM the whole compiled manifest (including this spec), so
        including it here would be circular; ``source_registry_hash``/``compiler_hash`` are
        excluded for the SAME reason this schema keeps them as separate provenance pointers
        rather than folding them into the spec's own scientific identity; ``candidate_spec_hash``
        obviously excludes itself. ``dataclasses.asdict`` + ``sort_keys=True`` below makes this
        invariant to Python field-construction/serialization order (TC-10)."""
        raw = asdict(self)
        for key in ("manifest_hash", "source_registry_hash", "compiler_hash", "candidate_spec_hash"):
            raw.pop(key, None)
        return raw

    def compute_hash(self) -> str:
        blob = json.dumps(self._canonical_fields(), sort_keys=True, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def with_hash(self) -> "CandidateSpec":
        """Returns a copy with ``candidate_spec_hash`` filled in -- the ONE place this module ever
        sets it, always computed AFTER every other field is final."""
        object.__setattr__(self, "candidate_spec_hash", self.compute_hash())
        return self


class FamilyOrdinalCollision(Exception):
    """Two ``COMPILED`` records share one ``foundry_family_key`` and the SAME ``variant_ordinal``
    -- refused before any ``CandidateSpec`` is built (never silently overwritten)."""


@dataclass(frozen=True)
class CompilationResult:
    source_registry_hash: str
    dispositions: Mapping[str, str]
    candidate_specs: Mapping[str, CandidateSpec]


def compiler_hash() -> str:
    """A ``sha256`` of THIS module's own source file -- the compiler's own identity, exactly like
    ``docs/goal.md §8.4``'s freeze-set will later pin every science-affecting module by content
    hash. Recomputed fresh every call (cheap, deterministic) rather than cached, so it can never
    silently go stale after an edit."""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def compile_sources(
    records: Sequence[SourceRecord],
    *,
    foundry_spec_version: str,
    epoch_id: str,
    blueprints: Mapping[str, CandidateBlueprint] | None = None,
    manifest_hash: str | None = None,
) -> CompilationResult:
    """Compiles a WHOLE batch of ``SourceRecord``s (spec §0/§2): lints every quoted span first
    (fails closed before any ``CandidateSpec`` is built -- TC-12), derives each record's
    disposition via the fixed §2 precedence, groups ``COMPILED`` records sharing a
    ``foundry_family_key`` into one family (TC-4: shared ``foundry_family_id``, shared
    ``foundry_family_variant_count``, distinct ``variant_ordinal``), and builds a ``CandidateSpec``
    for every ``COMPILED`` record whose ``source_id`` key appears in ``blueprints`` with a fully
    immediate blueprint (no deferred coordinate -- ``foundry_interpreter.py`` future work
    otherwise, TC-5/TC-6/TC-7/TC-9's blocked/aliased fixtures never reach this branch at all since
    their disposition is not ``COMPILED``).

    ``blueprints`` is keyed by ``source_id`` and passed SEPARATELY from ``records`` rather than
    living as a field on ``SourceRecord`` -- the §1.4 source-record schema
    (``foundry_source_registry.SourceRecord``) and the §3 ``CandidateSpec`` schema this module
    owns are deliberately two separate schemas (goal.md itself lists them as two distinct
    sections); keeping ``CandidateBlueprint`` out of ``SourceRecord`` avoids a needless import
    cycle between the two modules and keeps each module's own schema self-contained."""
    lint_quoted_spans(records)
    blueprints = blueprints or {}
    registry_hash = _registry_hash(records)
    this_compiler_hash = compiler_hash()

    dispositions: dict[str, str] = {}
    family_members: dict[str, list[SourceRecord]] = defaultdict(list)
    for record in records:
        disposition = compile_source_disposition(record)
        dispositions[record.source_id] = disposition
        if disposition == DISPOSITION_COMPILED and record.foundry_family_key is not None:
            family_members[record.foundry_family_key].append(record)

    for family_key, members in family_members.items():
        ordinals = [m.variant_ordinal for m in members]
        if len(set(ordinals)) != len(ordinals):
            raise FamilyOrdinalCollision(
                f"foundry family {family_key!r} has a duplicate variant_ordinal among {ordinals!r}"
            )

    specs: dict[str, CandidateSpec] = {}
    for record in records:
        if dispositions[record.source_id] != DISPOSITION_COMPILED:
            continue
        blueprint = blueprints.get(record.source_id)
        if blueprint is None or not blueprint.is_immediate():
            # This revision's scope: only fully-immediate, non-deferred blueprints compile here.
            # A COMPILED-but-not-yet-spec'd record simply produces no CandidateSpec this revision
            # (§7.2's FROZEN_READY-incomplete state) -- never approximated.
            continue

        if record.foundry_family_key is not None:
            family_key = record.foundry_family_key
            members = family_members[family_key]
            family_variant_count = len(members)
        else:
            family_key = record.source_id
            family_variant_count = 1

        foundry_family_id = f"family:{family_key}"
        variant_ordinal = record.variant_ordinal if record.variant_ordinal is not None else 0
        variant_id = f"{foundry_family_id}:{variant_ordinal}"

        spec = CandidateSpec(
            foundry_spec_version=foundry_spec_version,
            epoch_id=epoch_id,
            source_ids=(record.source_id,),
            lineage_id=record.lineage_id or record.source_id,
            foundry_family_id=foundry_family_id,
            variant_id=variant_id,
            variant_ordinal=variant_ordinal,
            population=blueprint.population,
            coordinates=blueprint.coordinates,
            relation=blueprint.relation,
            membership_corner=blueprint.membership_corner,
            outcome=blueprint.outcome,
            economic_floor_rule=blueprint.economic_floor_rule,
            foundry_family_variant_count=family_variant_count,
            manifest_hash=manifest_hash,
            source_registry_hash=registry_hash,
            compiler_hash=this_compiler_hash,
        ).with_hash()
        specs[record.source_id] = spec

    return CompilationResult(source_registry_hash=registry_hash, dispositions=dispositions, candidate_specs=specs)
