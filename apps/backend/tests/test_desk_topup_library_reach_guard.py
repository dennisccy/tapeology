"""goal-desk-iter-32 (J-19) source-introspection guard test -- the ``test_desk_ui_guards.py``/
``test_desk_topup_window_disclosure_guard.py`` pattern (read ``apps/frontend/app/desk/page.tsx`` as
TEXT, assert on substrings/structure; no browser, no runtime).

Proves the Top-up Runs section's library-reach disclosure actually landed and stays wired the way
the DoD requires:

  (a) the honest legacy-run fallback text ``"library reach not recorded in this run"`` exists as
      ONE shared constant (never a second, divergent copy of the string);
  (b) the new descriptive line and the earlier-pairs list are both present, rendered beside the
      existing ``desk-topup-run-latest-window-basis`` line -- no new section, no new control;
  (c) ``topupLibraryReach`` never computes a value when any outcome lacks
      `store_frozen_through_after` -- it returns ``null`` in that case, which the render layer maps
      to the honest fallback rather than a guessed/backfilled date.

A guard that can never fail proves nothing -- ``test_the_fallback_text_guard_can_fail_on_a_seeded_
violation`` below seeds a violation (a second, drifted copy of the fallback string) and proves the
same check catches it."""

from __future__ import annotations

import pathlib
import re

_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"

_FALLBACK_TEXT = "library reach not recorded in this run"


def _source() -> str:
    return _DESK_PAGE.read_text()


def test_the_legacy_fallback_text_is_a_single_shared_constant():
    source = _source()
    # Exactly ONE string literal carries the fallback text (a `const` definition) -- every OTHER
    # occurrence in the file references that constant by name, never repeats the literal.
    literal_occurrences = source.count(f'"{_FALLBACK_TEXT}"')
    assert literal_occurrences == 1, (
        f"expected the fallback text to be defined as ONE shared string literal, found "
        f"{literal_occurrences} -- a second, independently-typed copy risks drifting out of sync"
    )
    assert "LIBRARY_REACH_NOT_RECORDED" in source


def test_the_reach_line_uses_the_shared_constant():
    source = _source()
    assert source.count("LIBRARY_REACH_NOT_RECORDED") >= 2  # 1 definition + >=1 usage


def test_the_reach_line_and_earlier_list_are_present_beside_the_window_basis_line():
    source = _source()
    window_basis_idx = source.index('data-testid="desk-topup-run-latest-window-basis"')
    reach_idx = source.index('data-testid="desk-topup-run-latest-reach"')
    earlier_idx = source.index('data-testid="desk-topup-run-latest-reach-earlier"')
    failed_idx = source.index('data-testid="desk-topup-run-latest-failed"')
    # The new block sits AFTER the existing window-basis line and BEFORE the existing failed-pairs
    # block -- no new section, no reordering of already-shipped disclosures.
    assert window_basis_idx < reach_idx < earlier_idx < failed_idx


def test_topup_library_reach_returns_null_when_any_outcome_lacks_store_frozen_through_after():
    """``topupLibraryReach``'s own source slice (from its declaration to the NEXT top-level
    ``function`` declaration) structurally returns ``null`` on an absent field rather than
    defaulting/backfilling a date."""
    source = _source()
    marker = "function topupLibraryReach("
    start = source.index(marker)
    next_fn = source.index("\nfunction ", start + len(marker))
    body = source[start:next_fn]
    assert "store_frozen_through_after === undefined" in body
    assert re.search(r"return\s+null", body) is not None


def test_the_fallback_text_guard_can_fail_on_a_seeded_violation():
    """A guard that can never fail proves nothing -- a seeded SECOND, independently-typed copy of
    the fallback text is caught by the same counting check above."""
    seeded = (
        'const LIBRARY_REACH_NOT_RECORDED = "library reach not recorded in this run";\n'
        'const other = "library reach not recorded in this run";\n'
    )
    literal_occurrences = seeded.count(f'"{_FALLBACK_TEXT}"')
    assert literal_occurrences != 1
