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
same check catches it.

goal-desk-iter-34 (J-19 fix) extends this file with two more structural checks, each with its own
seeded-violation counterpart:

  (d) the grouping decision inside ``topupLibraryReach`` compares a DAY-TRUNCATED key
      (``store_frozen_through_after.slice(0, 10)``), never the raw microsecond-precision string --
      the iter-32/33 bug compared ``store_frozen_through_after === newestDate`` /
      ``!== newestDate`` directly, so two pairs recorded on the SAME calendar day at different
      times were miscounted as "earlier" relative to each other;
  (e) the returned ``earlier`` array is capped at ``EARLIER_PAIRS_DISPLAY_CAP`` (20) entries while
      a separate true-total value is preserved, so the heading can disclose an honest
      "showing 20 of N" instead of silently truncating or rendering an unbounded list."""

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


# goal-desk-iter-34 (J-19 fix, TC-4/TC-5): the "showing 20 of N" disclosure sits inside the
# already-registered earlier-pairs block (between its heading and the failed-pairs block below),
# is gated on the TRUE total exceeding the cap (never shown for a run whose true total is <= 20),
# and the heading itself counts the true total, not the capped, rendered array length.
def test_the_cap_disclosure_sits_inside_the_earlier_block_and_is_conditionally_gated():
    source = _source()
    earlier_idx = source.index('data-testid="desk-topup-run-latest-reach-earlier"')
    failed_idx = source.index('data-testid="desk-topup-run-latest-failed"')
    cap_note_idx = source.index('data-testid="desk-topup-run-latest-reach-earlier-cap"')
    assert earlier_idx < cap_note_idx < failed_idx
    # The cap note only renders when the true total exceeds the cap -- never unconditionally.
    cap_note_line_start = source.rindex("\n", 0, cap_note_idx)
    guard_clause = source[max(0, cap_note_line_start - 200) : cap_note_idx]
    assert "earlierTotal > EARLIER_PAIRS_DISPLAY_CAP" in guard_clause
    # The literal disclosure text carries the word "showing" plus both the shown and true counts.
    assert "showing {libraryReach.earlier.length} of {libraryReach.earlierTotal}" in source
    # The heading counts the TRUE total (earlierTotal), never the capped array's own length --
    # otherwise a run with 25 true earlier pairs would print "Pairs recorded earlier (20)", quietly
    # hiding the truncation instead of disclosing it.
    assert "Pairs recorded earlier ({libraryReach.earlierTotal})" in source
    assert "Pairs recorded earlier ({libraryReach.earlier.length})" not in source


def test_the_cap_disclosure_guard_can_fail_on_a_seeded_violation():
    """A guard that can never fail proves nothing -- a seeded heading that counts the CAPPED array
    length instead of the true total (silently hiding truncation) is caught by the check above."""
    seeded_source = "Pairs recorded earlier ({libraryReach.earlier.length})"
    assert "Pairs recorded earlier ({libraryReach.earlierTotal})" not in seeded_source


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


def _topup_library_reach_body(source: str) -> str:
    marker = "function topupLibraryReach("
    start = source.index(marker)
    next_fn = source.index("\nfunction ", start + len(marker))
    return source[start:next_fn]


# goal-desk-iter-34 (J-19 fix, TC-2/TC-7): the grouping decision must compare a day-truncated key,
# never the raw microsecond-precision `store_frozen_through_after` string directly against the
# selected extreme -- that raw comparison is EXACTLY the iter-32/33 bug (confirmed live: 202 of 303
# pairs shown under "Pairs recorded earlier" printed the SAME calendar day the reach line named as
# newest). This check is a pure function of the source text so it can be re-run, unmodified,
# against a seeded violation below.
def _day_truncation_check(body: str) -> bool:
    has_day_truncated_key = (
        re.search(r"store_frozen_through_after[^\n;]*\.slice\(0,\s*10\)", body) is not None
    )
    has_raw_precision_bug = (
        "store_frozen_through_after === newestDate" in body
        or "store_frozen_through_after !== newestDate" in body
    )
    return has_day_truncated_key and not has_raw_precision_bug


def test_topup_library_reach_groups_by_day_truncated_key_not_raw_timestamp():
    """TC-2: two outcomes whose `store_frozen_through_after` values share a calendar day but carry
    different microsecond timestamps must be grouped as the SAME day -- structurally proven by
    (a) a day-truncated key derived from the field inside the function body, and (b) the absence
    of the iter-32/33 bug's raw full-precision equality/inequality comparison against the selected
    extreme."""
    body = _topup_library_reach_body(_source())
    assert _day_truncation_check(body) is True, (
        "topupLibraryReach must derive a day-truncated key from store_frozen_through_after and use "
        "it for every grouping/comparison decision -- comparing the raw timestamp directly against "
        "newestDate is exactly the iter-32/33 bug"
    )


def test_day_truncation_guard_can_fail_on_a_seeded_violation():
    """A guard that can never fail proves nothing -- a seeded copy of the ACTUAL iter-32/33 buggy
    body (raw full-precision comparison, no day-truncated key) is caught by the same check above."""
    seeded_body = (
        "function topupLibraryReach(outcomes) {\n"
        "  const newestDate = dates.reduce((max, d) => (d > max ? d : max), dates[0]);\n"
        "  const newestCount = outcomes.filter((o) => o.store_frozen_through_after === newestDate)"
        ".length;\n"
        "  const earlier = outcomes.filter((o) => o.store_frozen_through_after !== newestDate);\n"
        "}\n"
    )
    assert _day_truncation_check(seeded_body) is False


# goal-desk-iter-34 (J-19 fix, TC-3/TC-8): the returned `earlier` array is capped at
# `EARLIER_PAIRS_DISPLAY_CAP` entries while a separate true-total value survives, so the render can
# disclose an honest "showing 20 of N" rather than truncating silently or rendering an unbounded
# list (the iter-32/33 bug: 303 rows, no cap, no disclosure).
def _cap_check(body: str) -> bool:
    has_cap_constant = "EARLIER_PAIRS_DISPLAY_CAP" in body
    has_capped_slice = re.search(r"\.slice\(0,\s*EARLIER_PAIRS_DISPLAY_CAP\)", body) is not None
    has_separate_true_total = re.search(r"\bearlierTotal\b", body) is not None
    return has_cap_constant and has_capped_slice and has_separate_true_total


def test_topup_library_reach_caps_the_earlier_list_and_preserves_the_true_total():
    """TC-3: the returned `earlier` array is capped at 20 entries; a separate true-total value is
    preserved so the heading can disclose the real count honestly."""
    source = _source()
    assert "const EARLIER_PAIRS_DISPLAY_CAP = 20;" in source
    body = _topup_library_reach_body(source)
    assert _cap_check(body) is True, (
        "topupLibraryReach must cap the returned `earlier` array at EARLIER_PAIRS_DISPLAY_CAP "
        "entries while preserving the true total separately (earlierTotal) -- an uncapped list "
        "silently renders every recorded pair, unbounded"
    )


def test_cap_guard_can_fail_on_a_seeded_violation():
    """A guard that can never fail proves nothing -- a seeded uncapped `earlier` array (the
    iter-32/33 bug: every pair earlier than the newest day, however many there are, with no
    separate true-total tracked) is caught by the same check above."""
    seeded_body = (
        "function topupLibraryReach(outcomes) {\n"
        "  const earlier = outcomes\n"
        "    .filter((o) => o.store_frozen_through_after !== newestDate)\n"
        "    .map((o) => ({ symbol: o.symbol, timeframe: o.timeframe }));\n"
        "  return { newestDate, newestCount, earlier };\n"
        "}\n"
    )
    assert _cap_check(seeded_body) is False
