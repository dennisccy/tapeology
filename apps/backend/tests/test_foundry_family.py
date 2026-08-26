"""``foundry_family.py`` (goal-hypothesis-foundry-iter-2, J-04): the Foundry-family denominator,
hard cap enforcement, and late-insertion refusal (spec §5.1/§5.2/§5.3). TC-9/TC-10 in
``docs/phases/goal-hypothesis-foundry-iter-2.md``."""

from __future__ import annotations

import pytest

from app.research import foundry_family as ff
from app.research import scout


def test_tc9_family_of_one_exposes_its_denominator_before_evaluation():
    registry = ff.build_family_registry({"family:solo": ["family:solo:0"]})
    family = registry["family:solo"]
    assert family.variant_count == 1
    assert family.blocked is False
    assert family.variant_ordinals == (0,)


def test_tc9_family_of_multiple_exposes_the_complete_denominator():
    variants = [f"family:multi:{i}" for i in range(5)]
    registry = ff.build_family_registry({"family:multi": variants})
    family = registry["family:multi"]
    assert family.variant_count == 5
    assert family.blocked is False


def test_tc9_family_at_exactly_the_cap_is_not_blocked():
    variants = [f"family:cap:{i}" for i in range(scout.SCOUT_MAX_VARIANTS_PER_FAMILY)]
    registry = ff.build_family_registry({"family:cap": variants})
    family = registry["family:cap"]
    assert family.variant_count == scout.SCOUT_MAX_VARIANTS_PER_FAMILY
    assert family.blocked is False


def test_tc9_over_cap_family_blocks_whole_with_zero_variants_proceeding():
    variants = [f"family:over:{i}" for i in range(scout.SCOUT_MAX_VARIANTS_PER_FAMILY + 1)]
    registry = ff.build_family_registry({"family:over": variants})
    family = registry["family:over"]
    assert family.blocked is True
    assert family.variant_count == scout.SCOUT_MAX_VARIANTS_PER_FAMILY + 1
    assert ff.eligible_variant_ordinals(family) == ()


def test_tc9_multiple_families_are_independent():
    registry = ff.build_family_registry(
        {
            "family:a": ["a:0"],
            "family:b": [f"b:{i}" for i in range(scout.SCOUT_MAX_VARIANTS_PER_FAMILY + 3)],
            "family:c": [f"c:{i}" for i in range(4)],
        }
    )
    assert registry["family:a"].blocked is False
    assert registry["family:b"].blocked is True
    assert registry["family:c"].blocked is False
    assert registry["family:c"].variant_count == 4


def test_tc10_late_insertion_after_freeze_is_refused_and_denominator_is_unchanged():
    registry = ff.build_family_registry({"family:frozen": ["family:frozen:0", "family:frozen:1"]})
    family = registry["family:frozen"]
    before = family.variant_count
    with pytest.raises(ff.LateInsertionRefused):
        ff.attempt_late_insertion(family, new_variant_ordinal=2)
    assert family.variant_count == before == 2


def test_n_variants_tried_is_the_frozen_denominator_regardless_of_execution_progress():
    """§5.3: every sibling variant's screen receives the COMPLETE frozen denominator, even before
    siblings have physically executed -- trivially true here since `n_variants_tried_for` reads
    only the frozen `variant_count`, never an execution-progress counter."""
    registry = ff.build_family_registry({"family:x": ["x:0", "x:1", "x:2"]})
    family = registry["family:x"]
    assert ff.n_variants_tried_for(family) == 3 == ff.n_variants_tried_for(family)


def test_foundry_family_variant_explosion_disposition_is_the_closed_sentinel():
    assert ff.FAMILY_BLOCKED_VARIANT_EXPLOSION == "BLOCKED_VARIANT_EXPLOSION"
