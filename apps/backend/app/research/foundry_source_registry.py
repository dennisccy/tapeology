"""The Hypothesis Foundry (goal-hypothesis-foundry) -- the source registry: the closed §7.1
disposition vocabulary, the §1.4 per-source-record schema, the §2 owner meta-policy compile
precedence, the §1.4 exact-quote lint, and the era-open baseline snapshot. See
``docs/hypothesis-foundry-spec.md`` (this module implements that spec's §1.4/§2/§7.1 verbatim;
section numbers below match both that file and ``docs/goal.md``'s Foundry Constitution).

**What this module deliberately is NOT.** It never reads a candidate outcome, Scout result,
p-value, effect, or sample count -- ``compile_source_disposition`` below takes only the
mechanically-declared fields a ``SourceRecord`` already carries and returns one disposition from
the closed vocabulary, with no branch anywhere keyed on anything outcome-shaped. It authors no
real source object this iteration (that is ``J-06``); every record this module's own tests build
is one of the seven hermetic fixture taxonomy examples ``docs/goal.md`` J-02 step 2 names.

**Why ``compile_source_disposition`` takes a single ``SourceRecord`` and not a batch.** Disposition
is a per-record decision (proxy / supersession / spec-gap / direction / study-form / natural
threshold), fully determined by that record's own declared fields -- it never depends on which
other records exist. Family bookkeeping (grouping ``COMPILED`` records that share a
``foundry_family_key``, assigning ``foundry_family_variant_count``) is instead ``foundry_compiler.
compile_sources``'s job, because THAT decision genuinely needs the whole batch."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

__all__ = [
    "SOURCE_DISPOSITIONS",
    "DISPOSITION_COMPILED",
    "DISPOSITION_ALIASED_PROXY_ONLY",
    "DISPOSITION_ALIASED_VARIANT_VOCABULARY",
    "DISPOSITION_ALIASED_LINEAGE",
    "DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED",
    "DISPOSITION_EXCLUDED_PREREQUISITE_UNMET",
    "DISPOSITION_EXCLUDED_GATE_CLOSED",
    "DISPOSITION_BLOCKED_SPEC_GAP",
    "DISPOSITION_BLOCKED_MISSING_PRIMITIVE",
    "DISPOSITION_BLOCKED_UNSUPPORTED_STUDY_FORM",
    "DISPOSITION_BLOCKED_UNSUPPORTED_RELATION",
    "DISPOSITION_BLOCKED_DIRECTION",
    "DISPOSITION_BLOCKED_VARIANT_EXPLOSION",
    "DISPOSITION_BLOCKED_UNIT_CONTRACT",
    "BLOCKED_DIRECTION_SENTINEL",
    "BLOCKED_UNSUPPORTED_STUDY_FORM_SENTINEL",
    "THRESHOLD_LITERAL_RATIFIED",
    "THRESHOLD_FROZEN_FEATURE_CONTRACT",
    "THRESHOLD_NATURAL_SEMANTIC_BOUNDARY",
    "LEGAL_THRESHOLD_PROVENANCES",
    "QuotedSpan",
    "ProxyDeclaration",
    "SupersessionDeclaration",
    "SourceRecord",
    "QuoteMismatch",
    "compile_source_disposition",
    "lint_quoted_spans",
    "source_registry_hash",
    "resolve_foundry_dir",
    "record_era_open_baseline",
    "read_era_open_baseline",
    "REFEREE_MODULES",
    "FOUNDRY_SPEC_VERSION",
    "PREVIOUS_ERA",
    "PREVIOUS_ERA_STATUS",
    "CURRENT_ERA",
    "CURRENT_ERA_STATUS",
    "foundry_era_identity",
]

# --- §7.1: the closed source-disposition vocabulary -----------------------------------------------
DISPOSITION_COMPILED = "COMPILED"
DISPOSITION_ALIASED_PROXY_ONLY = "ALIASED_PROXY_ONLY"
DISPOSITION_ALIASED_VARIANT_VOCABULARY = "ALIASED_VARIANT_VOCABULARY"
DISPOSITION_ALIASED_LINEAGE = "ALIASED_LINEAGE"
DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED = "EXCLUDED_PREVIOUSLY_KILLED"
DISPOSITION_EXCLUDED_PREREQUISITE_UNMET = "EXCLUDED_PREREQUISITE_UNMET"
DISPOSITION_EXCLUDED_GATE_CLOSED = "EXCLUDED_GATE_CLOSED"
DISPOSITION_BLOCKED_SPEC_GAP = "BLOCKED_SPEC_GAP"
DISPOSITION_BLOCKED_MISSING_PRIMITIVE = "BLOCKED_MISSING_PRIMITIVE"
DISPOSITION_BLOCKED_UNSUPPORTED_STUDY_FORM = "BLOCKED_UNSUPPORTED_STUDY_FORM"
DISPOSITION_BLOCKED_UNSUPPORTED_RELATION = "BLOCKED_UNSUPPORTED_RELATION"
DISPOSITION_BLOCKED_DIRECTION = "BLOCKED_DIRECTION"
DISPOSITION_BLOCKED_VARIANT_EXPLOSION = "BLOCKED_VARIANT_EXPLOSION"
DISPOSITION_BLOCKED_UNIT_CONTRACT = "BLOCKED_UNIT_CONTRACT"

SOURCE_DISPOSITIONS = frozenset(
    {
        DISPOSITION_COMPILED,
        DISPOSITION_ALIASED_PROXY_ONLY,
        DISPOSITION_ALIASED_VARIANT_VOCABULARY,
        DISPOSITION_ALIASED_LINEAGE,
        DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED,
        DISPOSITION_EXCLUDED_PREREQUISITE_UNMET,
        DISPOSITION_EXCLUDED_GATE_CLOSED,
        DISPOSITION_BLOCKED_SPEC_GAP,
        DISPOSITION_BLOCKED_MISSING_PRIMITIVE,
        DISPOSITION_BLOCKED_UNSUPPORTED_STUDY_FORM,
        DISPOSITION_BLOCKED_UNSUPPORTED_RELATION,
        DISPOSITION_BLOCKED_DIRECTION,
        DISPOSITION_BLOCKED_VARIANT_EXPLOSION,
        DISPOSITION_BLOCKED_UNIT_CONTRACT,
    }
)

# A record with no mechanical direction rule declares this literal sentinel rather than leaving
# `direction_derivation` empty/None -- an explicit typed refusal, never an absence a caller could
# mistake for "not yet filled in" (spec §3.2 / goal.md §2.2).
BLOCKED_DIRECTION_SENTINEL = "BLOCKED_DIRECTION"
BLOCKED_UNSUPPORTED_STUDY_FORM_SENTINEL = "BLOCKED_UNSUPPORTED_STUDY_FORM"

# --- §2.3: the natural-boundary law's three (and only three) legal threshold provenances ----------
THRESHOLD_LITERAL_RATIFIED = "literal_ratified_threshold"
THRESHOLD_FROZEN_FEATURE_CONTRACT = "frozen_rapid_validation_feature_contract"
THRESHOLD_NATURAL_SEMANTIC_BOUNDARY = "natural_semantic_boundary"
LEGAL_THRESHOLD_PROVENANCES = frozenset(
    {THRESHOLD_LITERAL_RATIFIED, THRESHOLD_FROZEN_FEATURE_CONTRACT, THRESHOLD_NATURAL_SEMANTIC_BOUNDARY}
)


@dataclass(frozen=True)
class QuotedSpan:
    """One exact quoted source span backing a load-bearing compile/audit decision (spec §1.4).
    ``location`` is the exact character OFFSET into the owning record's ``source_excerpt`` -- the
    lint below checks the substring AT that offset, never "appears somewhere", so a span whose
    text matches but whose location does not is still a lint failure (TC-12's "fails closed")."""

    text: str
    location: int


@dataclass(frozen=True)
class ProxyDeclaration:
    """Marks a ``SourceRecord`` as a frozen pilot-proxy request for a parked study (goal.md
    §1.1's "these proxies are source objects for provenance, not permission to launder a partial
    proxy as the full mechanism"). ``do_not`` is the proxy's own existing restriction, preserved
    verbatim onto the compiled record (TC-6)."""

    parked_study_source_id: str
    do_not: str


@dataclass(frozen=True)
class SupersessionDeclaration:
    """Marks a ``SourceRecord`` as the OLDER member of a formula-scoped supersession pair (spec
    §1.3). ``newer_source_ref`` is what ``superseded_fields`` cites; ``alias_kind`` selects which
    of the two alias dispositions this record reaches."""

    newer_source_ref: str
    alias_kind: str = DISPOSITION_ALIASED_VARIANT_VOCABULARY

    def __post_init__(self) -> None:
        if self.alias_kind not in (DISPOSITION_ALIASED_VARIANT_VOCABULARY, DISPOSITION_ALIASED_LINEAGE):
            raise ValueError(f"alias_kind must be one of the two alias dispositions, got {self.alias_kind!r}")


@dataclass(frozen=True)
class SourceRecord:
    """The §1.4 per-source-record schema, verbatim. See ``docs/hypothesis-foundry-spec.md`` §1.4
    for the full field-by-field rationale. Every collection field is a ``tuple``/mapping-of-str so
    the whole record stays hashable and JSON-serializes deterministically for
    ``source_registry_hash`` below."""

    source_id: str
    source_path: str
    section_ref: str
    quoted_spans: tuple[QuotedSpan, ...]
    source_excerpt: str
    mechanism_statement: str
    operative_formula_refs: tuple[str, ...]
    direction_derivation: str
    comparator_derivation: str
    audit_note: str
    lineage_id: str | None = None
    foundry_family_key: str | None = None
    variant_ordinal: int | None = None
    threshold_provenance: str | None = None
    unresolved_magnitude_words: tuple[str, ...] = ()
    superseded_fields: Mapping[str, str] = field(default_factory=dict)
    proxy_of: ProxyDeclaration | None = None
    supersession: SupersessionDeclaration | None = None
    explicit_exclusion: str | None = None  # one of the three EXCLUDED_* dispositions, or None
    aliases_lineage_ids: tuple[str, ...] = ()
    # Caller-supplied metadata the compiler NEVER reads (TC-11): an injected effect/p-value/n
    # fixture field lives here and provably cannot move a disposition or a CandidateSpec hash,
    # because nothing below ever looks at this mapping.
    extra: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.threshold_provenance is not None and self.threshold_provenance not in LEGAL_THRESHOLD_PROVENANCES:
            # Spec §2.3: an illegal/unratified threshold provenance is exactly the shape of source
            # this era must not silently compile -- refuse the OBJECT at construction rather than
            # let a caller build one and forget to route it through `unresolved_magnitude_words`.
            raise ValueError(
                f"{self.source_id}: threshold_provenance {self.threshold_provenance!r} is not one "
                f"of the three §2.3 natural-boundary categories -- represent an unratified "
                "magnitude/threshold as `unresolved_magnitude_words` instead, never as a fourth "
                "threshold_provenance value"
            )
        if self.explicit_exclusion is not None and self.explicit_exclusion not in (
            DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED,
            DISPOSITION_EXCLUDED_PREREQUISITE_UNMET,
            DISPOSITION_EXCLUDED_GATE_CLOSED,
        ):
            raise ValueError(f"{self.source_id}: explicit_exclusion must be one of the three EXCLUDED_* dispositions")


class QuoteMismatch(Exception):
    """Raised by ``lint_quoted_spans`` (never swallowed -- fail closed, spec §1.4)."""


def lint_quoted_spans(records: Sequence[SourceRecord]) -> None:
    """Verifies every ``QuotedSpan`` across ``records`` is an EXACT substring of its own record's
    ``source_excerpt`` AT the recorded character offset. Raises ``QuoteMismatch`` on the first
    failure (TC-12's "fails closed on an injected mismatched span") -- never a keyword/fuzzy
    match, per spec §1.4's own explicit "deliberately does not use keyword matching"."""
    for record in records:
        for span in record.quoted_spans:
            end = span.location + len(span.text)
            actual = record.source_excerpt[span.location:end]
            if actual != span.text:
                raise QuoteMismatch(
                    f"{record.source_id}: quoted span {span.text!r} does not match "
                    f"source_excerpt[{span.location}:{end}] = {actual!r}"
                )


def compile_source_disposition(record: SourceRecord) -> str:
    """The §2 owner meta-policy, as one fixed precedence -- no branch below is keyed on which
    fixture archetype a caller thinks it is building; every decision reads only the record's own
    declared fields. See ``docs/hypothesis-foundry-spec.md`` §2 for the full rationale behind this
    exact order."""
    if record.explicit_exclusion is not None:
        return record.explicit_exclusion
    if record.proxy_of is not None:
        return DISPOSITION_ALIASED_PROXY_ONLY
    if record.supersession is not None:
        return record.supersession.alias_kind
    if record.unresolved_magnitude_words:
        return DISPOSITION_BLOCKED_SPEC_GAP
    if record.direction_derivation == BLOCKED_DIRECTION_SENTINEL:
        return DISPOSITION_BLOCKED_DIRECTION
    if record.comparator_derivation == BLOCKED_UNSUPPORTED_STUDY_FORM_SENTINEL:
        return DISPOSITION_BLOCKED_UNSUPPORTED_STUDY_FORM
    return DISPOSITION_COMPILED


def _canonical_source_record(record: SourceRecord) -> dict:
    """A plain, JSON-serializable, order-independent projection of ``record`` -- the ONE
    canonicalization ``source_registry_hash`` and ``foundry_compiler``'s CandidateSpec hashing
    both build on, so a family's registry hash and a variant's spec hash can never silently
    diverge in how they see the same record."""
    return {
        "source_id": record.source_id,
        "source_path": record.source_path,
        "section_ref": record.section_ref,
        "quoted_spans": [{"text": s.text, "location": s.location} for s in record.quoted_spans],
        "source_excerpt": record.source_excerpt,
        "mechanism_statement": record.mechanism_statement,
        "operative_formula_refs": list(record.operative_formula_refs),
        "direction_derivation": record.direction_derivation,
        "comparator_derivation": record.comparator_derivation,
        "lineage_id": record.lineage_id,
        "foundry_family_key": record.foundry_family_key,
        "variant_ordinal": record.variant_ordinal,
        "threshold_provenance": record.threshold_provenance,
        "unresolved_magnitude_words": list(record.unresolved_magnitude_words),
        "superseded_fields": dict(record.superseded_fields),
        "proxy_of": (
            {"parked_study_source_id": record.proxy_of.parked_study_source_id, "do_not": record.proxy_of.do_not}
            if record.proxy_of is not None
            else None
        ),
        "supersession": (
            {"newer_source_ref": record.supersession.newer_source_ref, "alias_kind": record.supersession.alias_kind}
            if record.supersession is not None
            else None
        ),
        "explicit_exclusion": record.explicit_exclusion,
        "aliases_lineage_ids": list(record.aliases_lineage_ids),
    }


def source_registry_hash(records: Sequence[SourceRecord]) -> str:
    """A deterministic ``sha256`` over the whole registry batch, order-invariant in field
    serialization (``sort_keys=True``) but sensitive to record CONTENT and to which records are
    present -- the same discipline ``CandidateSpec.candidate_spec_hash`` uses one level down.
    Deliberately excludes ``record.extra`` (TC-11's non-science escape hatch, spec §1.4)."""
    canonical = [_canonical_source_record(r) for r in records]
    blob = json.dumps(canonical, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# --- era-open baseline: recorded ONCE, never recomputed on a page-load GET ------------------------

_FOUNDRY_DIR_ENV = "TAPEOLOGY_FOUNDRY_DIR"
_BASELINE_FILENAME = "era_open_baseline.json"

# The six referee_*.py modules whose SHA-256 the era-open baseline pins (goal.md J-01 step 5 /
# this iteration's IN SCOPE list) -- one fixed list, never derived from a directory glob, so an
# unrelated future referee_*.py addition cannot silently widen what "the baseline" means.
REFEREE_MODULES = (
    "referee_adjudicate.py",
    "referee_evidence.py",
    "referee_null.py",
    "referee_registry.py",
    "referee_routes.py",
    "referee_stats.py",
)


def resolve_foundry_dir(dataset_dir_resolved: str) -> str:
    """``TAPEOLOGY_FOUNDRY_DIR`` if set, else a ``foundry`` SIBLING of the caller's already-
    resolved dataset directory -- the ``micro_graduation.resolve_micro_graduation_dir``/
    ``vault.resolve_vault_dir`` pattern verbatim. Never a ``Config`` field (an operational
    storage-location knob, goal.md Constraints)."""
    override = os.environ.get(_FOUNDRY_DIR_ENV)
    if override:
        return override
    return str(Path(dataset_dir_resolved).parent / "foundry")


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_era_open_baseline(
    foundry_dir: str | Path,
    *,
    suite_passed: int,
    suite_skipped: int,
    suite_failed: int,
    tsc_error_count: int,
    config_fingerprint: str,
    research_dir: str | Path,
) -> dict:
    """Computes ONCE and persists the static era-open baseline snapshot (goal.md J-01 step 5):
    the full-suite pass/skip/failed counts and ``tsc --noEmit`` error count are supplied by the
    caller (an operator/CLI act that actually ran those -- this function never shells out to
    pytest/tsc itself, exactly like every other recording act in this codebase is a distinct step
    from the GET route that later serves it verbatim); ``config_fingerprint`` likewise comes from
    the caller's own ``CONFIG.config_fingerprint()`` read. The six ``referee_*.py`` module hashes
    ARE computed here (cheap, deterministic file reads, no external process). Overwrites any prior
    snapshot at this path -- re-recording is itself an explicit operator act, never something a
    GET triggers (spec §0 / goal.md T-8: page loads never compute)."""
    research_path = Path(research_dir)
    referee_hashes = {name: _hash_file(research_path / name) for name in REFEREE_MODULES}
    snapshot = {
        "backend_suite": {"passed": suite_passed, "skipped": suite_skipped, "failed": suite_failed},
        "tsc_error_count": tsc_error_count,
        "config_fingerprint": config_fingerprint,
        "referee_module_sha256": referee_hashes,
    }
    out_dir = Path(foundry_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / _BASELINE_FILENAME
    out_path.write_text(json.dumps(snapshot, sort_keys=True, indent=2), encoding="utf-8")
    return snapshot


def read_era_open_baseline(foundry_dir: str | Path) -> dict | None:
    """Reads the persisted snapshot VERBATIM -- no recomputation, ever (this is the only function
    the GET route calls). ``None`` when no snapshot has been recorded yet (a fresh install before
    the operator recording act ran) -- never a fabricated placeholder."""
    path = Path(foundry_dir) / _BASELINE_FILENAME
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# --- era/session identity (goal.md J-01 step 2: distinguishes Rapid Microscope, closed
# foundation, from the Foundry, the active era) -----------------------------------------------

FOUNDRY_SPEC_VERSION = "v1"  # docs/hypothesis-foundry-spec.md's own revision tag (top of that file)
PREVIOUS_ERA = "rapid-microscope"
PREVIOUS_ERA_STATUS = "closed"
CURRENT_ERA = "hypothesis-foundry"
CURRENT_ERA_STATUS = "active"


def foundry_era_identity() -> dict:
    """A plain, static dict -- never derived from anything computed per-request, so
    ``GET /research/desk/micro/foundry`` can serve it on every call with no recomputation
    (goal.md's own page-load-never-computes convention)."""
    return {
        "previous_era": PREVIOUS_ERA,
        "previous_era_status": PREVIOUS_ERA_STATUS,
        "current_era": CURRENT_ERA,
        "current_era_status": CURRENT_ERA_STATUS,
        "foundry_spec_version": FOUNDRY_SPEC_VERSION,
    }
