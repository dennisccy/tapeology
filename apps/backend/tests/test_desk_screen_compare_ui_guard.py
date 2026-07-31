"""goal-desk-iter-35 (J-20) source-introspection guard test -- the ``test_desk_ui_guards.py``
pattern (read ``apps/frontend/app/desk/page.tsx`` as TEXT, assert on substrings/structure; no
browser, no runtime) applied to the new Screen Comparison section.

Proves the two structural properties goal.md J-20 step 6 names explicitly:

  (a) the new section introduces no attribute/selector an EXISTING shipped golden's click target
      could resolve into -- it never reuses ``data-screen-id``, ``desk-history-row``,
      ``desk-screen-row``, or any ``desk-row-*`` testid.
  (b) the section is rendered strictly AFTER the ranked briefing table in the actual JSX call
      order (not merely the source TEXT order of function *definitions*, which does not determine
      DOM order) -- so the replay tool's first-visible-match text search
      (``incredible_auto_dev/scripts/automation/lib/demo_runner.py:641``) can never resolve into
      it instead of its real target.

A guard that can never fail proves nothing -- each check carries a seeded counter-test."""

from __future__ import annotations

import pathlib
import re

_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"

# Actual JSX ATTRIBUTE usages only (`data-testid="..."`/`data-screen-id=...`) -- a bare mention of
# these names in a prose comment (this guard's OWN docstring included) must never trip the check,
# so the pattern requires the real attribute syntax, not just the substring anywhere in the file.
_FORBIDDEN_TESTID_ATTRS = ('data-testid="desk-history-row"', 'data-testid="desk-screen-row"')
# `data-screen-id` (`DeskHistoryRow`, `page.tsx:759`) is its OWN bare custom attribute, not a
# `data-testid` value -- checked separately, by its real attribute-name syntax.
_FORBIDDEN_DATA_SCREEN_ID_ATTR = "data-screen-id="
_FORBIDDEN_ROW_TESTID_ATTR_RE = re.compile(r'data-testid="desk-row-[a-z-]+"')


def _compare_block(source: str) -> str:
    """The full source text of every J-20 component definition -- from the section's own leading
    comment through the next section's own leading comment, so every helper component
    (``ScreenCompareMeta``/``ScreenCompareRowView``/``ScreenCompareTable``/
    ``ScreenComparisonSection``) is covered, never just one of them."""
    start = source.index("// --- Screen comparison (goal-desk-iter-35, J-20)")
    end = source.index("// --- Provenance line", start)
    return source[start:end]


def test_screen_comparison_block_never_reuses_a_golden_click_target_testid():
    block = _compare_block(_DESK_PAGE.read_text())
    attr_hits = [attr for attr in _FORBIDDEN_TESTID_ATTRS if attr in block]
    assert not attr_hits, (
        f"the Screen Comparison section reuses the JSX attribute(s) {attr_hits} -- it must "
        "introduce ONLY its own desk-screen-compare-* testids, never an attribute an existing "
        "golden's click target already matches"
    )
    assert _FORBIDDEN_DATA_SCREEN_ID_ATTR not in block, (
        "the Screen Comparison section reuses the data-screen-id attribute"
    )
    row_hits = _FORBIDDEN_ROW_TESTID_ATTR_RE.findall(block)
    assert not row_hits, (
        f"the Screen Comparison section reuses desk-row-* testid attribute(s) {row_hits} -- it "
        "must never share a selector with the ranked briefing table's own row cells"
    )


def test_screen_comparison_block_reused_testid_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing."""
    seeded_source = '<tr data-testid="desk-screen-row">'
    attr_hits = [attr for attr in _FORBIDDEN_TESTID_ATTRS if attr in seeded_source]
    assert attr_hits == ['data-testid="desk-screen-row"']

    seeded_row_source = '<td data-testid="desk-row-symbol">'
    assert _FORBIDDEN_ROW_TESTID_ATTR_RE.findall(seeded_row_source) == ['data-testid="desk-row-symbol"']

    # and a bare PROSE mention (this guard's own docstring style) must NOT trip either check --
    # the lint targets real JSX attribute syntax only.
    seeded_prose = "// never reuses desk-screen-row or any desk-row-* testid"
    assert not [attr for attr in _FORBIDDEN_TESTID_ATTRS if attr in seeded_prose]
    assert _FORBIDDEN_ROW_TESTID_ATTR_RE.findall(seeded_prose) == []


def test_screen_comparison_section_is_used_after_the_ranked_table_in_render_order():
    """(b): the ranked table's own JSX CALL site (``<DeskRowsTable``, rendered inside
    ``DeskPopulatedScreen``) precedes the new section's own JSX CALL site
    (``<ScreenComparisonSection``, rendered as the page's own last section) -- comparing call
    sites, not component *definitions* (which do not determine DOM order in JS/TSX)."""
    source = _DESK_PAGE.read_text()
    ranked_table_call = source.index("<DeskRowsTable")
    compare_section_call = source.index("<ScreenComparisonSection")
    assert compare_section_call > ranked_table_call, (
        "<ScreenComparisonSection> is rendered before <DeskRowsTable> -- the Screen Comparison "
        "section must render strictly AFTER the ranked briefing table so the replay tool's "
        "first-visible-match text search cannot resolve into it"
    )


def test_render_order_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing."""
    seeded_source = "<ScreenComparisonSection result={x} />\n<DeskRowsTable rows={y} asOf={z} />"
    ranked_table_call = seeded_source.index("<DeskRowsTable")
    compare_section_call = seeded_source.index("<ScreenComparisonSection")
    assert not (compare_section_call > ranked_table_call)


def test_screen_comparison_section_carries_its_own_namespaced_testid():
    """A cheap sanity check that the section's own root testid actually exists at all -- otherwise
    the two tests above would both vacuously pass on a page that never renders the section."""
    source = _DESK_PAGE.read_text()
    assert 'data-testid="desk-screen-compare-section"' in source
