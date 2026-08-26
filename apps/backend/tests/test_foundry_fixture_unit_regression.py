"""Regression test for the QA-rig-crashing fixture bug the iter-0 evaluator found (goal-hypothesis-
foundry-iter-1, TC-2): ``seed_micro_graduation_iter18_fixture.py::_observation()`` was missing
``value_unit`` on all 30 seeded observations, which trips ``walkforward.
require_canonical_observation_units`` and prevents the scoped :8301 QA rig from ever starting
(``lessons.md`` iter-0). TC-1 (the rig itself starts healthy on port 8301) is an infra-level check
outside a unit test's reach -- verified operationally instead (see the dev handoff).

This test does NOT touch the real ``.data`` store: it imports the seed script's own pure
functions and calls the SAME production ``walkforward.require_canonical_observation_units`` guard
directly, never spinning up a backend or writing any file."""

from __future__ import annotations

from app.research import walkforward as wf
from scripts import seed_micro_graduation_iter18_fixture as seed_script


def test_observation_declares_the_canonical_return_bps_unit():
    row = seed_script._observation("2026-06-09", "PGQA", 10.0)
    assert row["value_unit"] == wf.WF_OBSERVATION_UNIT == "return_bps"


def test_tc2_thirty_seeded_observations_pass_the_canonical_unit_guard_without_raising():
    observations = seed_script._passing_observations()
    assert len(observations) == 30
    # Must not raise UnitMismatchError -- the exact failure the iter-0 evaluator reproduced at
    # `seed_micro_graduation_iter18_fixture.py:175` before this fix.
    wf.require_canonical_observation_units(observations)


def test_seeded_observation_values_are_unchanged_only_the_unit_declaration_was_added():
    """The bug was a missing DECLARATION, never a wrong unit (docstring rationale in the fix
    itself): the 30 values still average to exactly 10.0, clearing the fixture's own 5.0 bps
    floor in the registered `long` direction."""
    values = [row["value"] for row in seed_script._passing_observations()]
    assert len(values) == 30
    assert sum(values) / len(values) == 10.0
