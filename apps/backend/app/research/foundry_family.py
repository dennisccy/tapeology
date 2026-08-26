"""The Hypothesis Foundry -- the family denominator (spec §5). A ``foundry_family_id`` groups
every predeclared variant that is an alternative representation/corner of one mechanism lineage
under the source registry (§5.1); this module freezes that group's COMPLETE variant denominator
before any evaluation, enforces the hard family cap (§5.2), and refuses late insertion (§5.3) --
the Foundry's own multiplicity bookkeeping, deliberately independent of the existing Scout ledger
(the Foundry "does not claim the existing Scout ledger pre-registers families; it does not").

**Why this module, not the Scout ledger, owns this.** ``scout.py``'s own family/variant tracking
(``build_candidate_spec_fields``, the 24-variant cap in ``register_and_screen_candidate``) is a
Do-Not-Redo module this era must not touch or duplicate: it enforces the SAME
``SCOUT_MAX_VARIANTS_PER_FAMILY`` constant (imported here, never re-defined -- single source of
truth) over registrations that flow through the Scout LEDGER, which Foundry trials never do
(§4.2.1). This module is the Foundry-side analogue for the Foundry's OWN family concept."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .scout import SCOUT_MAX_VARIANTS_PER_FAMILY

__all__ = [
    "SCOUT_MAX_VARIANTS_PER_FAMILY",
    "FAMILY_BLOCKED_VARIANT_EXPLOSION",
    "LateInsertionRefused",
    "FoundryFamily",
    "build_family_registry",
    "eligible_variant_ordinals",
    "attempt_late_insertion",
    "n_variants_tried_for",
]

FAMILY_BLOCKED_VARIANT_EXPLOSION = "BLOCKED_VARIANT_EXPLOSION"


@dataclass(frozen=True)
class FoundryFamily:
    """A frozen-by-construction Foundry family (spec §5.1: "frozen before outcomes and may not be
    repartitioned after seeing results"). There is deliberately no mutation method on this
    dataclass -- ``attempt_late_insertion`` below is the only API surface a caller has for "adding"
    a variant, and it always refuses (see that function's own docstring)."""

    foundry_family_id: str
    variant_ordinals: tuple[int, ...]
    variant_count: int
    blocked: bool


def build_family_registry(variant_ids_by_family: Mapping[str, Sequence[str]]) -> dict[str, FoundryFamily]:
    """Builds one ``FoundryFamily`` per key of ``variant_ids_by_family`` (each value is that
    family's COMPLETE, pre-outcome variant id list, in canonical order -- ``variant_ordinals`` is
    simply that list's own index sequence, per ``foundry_compiler.compile_sources``'s own
    ``variant_ordinal`` convention). A family whose complete count exceeds
    ``SCOUT_MAX_VARIANTS_PER_FAMILY`` is ``blocked=True`` WHOLE (spec §5.2: never a subset, never
    the "most plausible" N, never split into artificial subfamilies to evade the cap) -- the count
    itself is still recorded (TC-9: "the complete Foundry denominator is visible before any
    result", including for a blocked family)."""
    registry: dict[str, FoundryFamily] = {}
    for family_id, variant_ids in variant_ids_by_family.items():
        count = len(variant_ids)
        registry[family_id] = FoundryFamily(
            foundry_family_id=family_id,
            variant_ordinals=tuple(range(count)),
            variant_count=count,
            blocked=count > SCOUT_MAX_VARIANTS_PER_FAMILY,
        )
    return registry


def eligible_variant_ordinals(family: FoundryFamily) -> tuple[int, ...]:
    """The ordinals actually eligible to proceed to evaluation -- empty for a blocked family (spec
    §5.2: "zero of its variants proceeding"), else the family's complete ordinal sequence."""
    return () if family.blocked else family.variant_ordinals


class LateInsertionRefused(Exception):
    """Raised unconditionally by ``attempt_late_insertion`` -- see that function's own docstring
    for why this is correct rather than merely convenient."""


def attempt_late_insertion(family: FoundryFamily, *, new_variant_ordinal: int) -> None:
    """ALWAYS refuses (spec §5.1/§9.3: "no late variant insertion"). ``FoundryFamily`` has no
    mutation API -- there is no code path anywhere in this module that could grow
    ``variant_count`` after ``build_family_registry`` returned it, so this function exists purely
    to give a caller/test a typed, explicit refusal to call against (TC-10) rather than attempting
    (and getting a ``FrozenInstanceError`` from) a direct dataclass-field mutation, which would be
    an implementation-detail exception, not a Foundry-domain one."""
    raise LateInsertionRefused(
        f"family {family.foundry_family_id!r} is frozen at variant_count={family.variant_count} "
        f"(ordinals {family.variant_ordinals!r}) -- variant ordinal {new_variant_ordinal!r} cannot "
        "be inserted after freeze"
    )


def n_variants_tried_for(family: FoundryFamily) -> int:
    """§5.3: the ``n_variants_tried`` disclosure every sibling variant's screen receives -- the
    COMPLETE frozen denominator, deliberately independent of how many siblings have physically
    executed (this reads only ``variant_count``, never an execution/progress counter)."""
    return family.variant_count
