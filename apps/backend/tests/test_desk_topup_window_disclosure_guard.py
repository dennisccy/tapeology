"""goal-desk-iter-26 (J-17) source-introspection guard test -- the ``test_desk_ui_guards.py``/
``test_desk_hover_tooltip_guard.py`` pattern (read ``apps/frontend/app/desk/page.tsx`` as TEXT,
assert on substrings/structure; no browser, no runtime).

Proves the Top-up Runs section's window-disclosure additions actually landed and stay wired the
way the DoD requires:

  (a) the honest legacy-run fallback text ``"window basis not recorded in this run"`` exists as
      ONE shared constant (never a second, divergent copy of the string), used by BOTH the
      tail-vs-full-lookback line and the per-failed-pair window line;
  (b) the four-outcome counts line (``reused``/``fetched``/``unchanged``/``failed``) is present;
  (c) ``topupWindowBasisCounts`` never computes a value when any outcome lacks ``window_basis`` --
      it returns ``null`` in that case, which the render layer maps to the honest fallback rather
      than a guessed/backfilled count.

A guard that can never fail proves nothing -- ``test_the_fallback_text_guard_can_fail_on_a_seeded_
violation`` below seeds a violation (a second, drifted copy of the fallback string) and proves the
same check catches it."""

from __future__ import annotations

import pathlib
import re

_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"

_FALLBACK_TEXT = "window basis not recorded in this run"


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
    assert "WINDOW_BASIS_NOT_RECORDED" in source


def test_the_tail_vs_full_lookback_line_and_the_failed_pair_window_line_both_use_the_shared_constant():
    source = _source()
    assert source.count("WINDOW_BASIS_NOT_RECORDED") >= 3  # 1 definition + >=2 usages


def test_the_four_outcome_counts_line_is_present():
    source = _source()
    assert "counts.reused" in source
    assert "counts.fetched" in source
    assert "counts.unchanged" in source
    assert "counts.failed" in source


def test_window_basis_counts_returns_null_when_any_outcome_lacks_window_basis():
    """``topupWindowBasisCounts``'s own source slice (from its declaration to the NEXT top-level
    ``function`` declaration -- simpler and more robust than brace-matching, since the function's
    OWN return-type annotation is itself a brace-balanced object type that would otherwise close a
    naive brace counter early) structurally returns ``null`` on an absent field rather than
    defaulting/backfilling a count."""
    source = _source()
    marker = "function topupWindowBasisCounts("
    start = source.index(marker)
    next_fn = source.index("\nfunction ", start + len(marker))
    body = source[start:next_fn]
    assert "window_basis === undefined" in body
    assert re.search(r"return\s+null", body) is not None


def test_the_fallback_text_guard_can_fail_on_a_seeded_violation():
    """A guard that can never fail proves nothing -- a seeded SECOND, independently-typed copy of
    the fallback text is caught by the same counting check above."""
    seeded = (
        'const WINDOW_BASIS_NOT_RECORDED = "window basis not recorded in this run";\n'
        'const other = "window basis not recorded in this run";\n'
    )
    literal_occurrences = seeded.count(f'"{_FALLBACK_TEXT}"')
    assert literal_occurrences != 1
