"""Forward-test era: source-introspection guards for the ``/desk`` Forward Returns panel -- the
``test_desk_screen_compare_ui_guard.py`` pattern (read the .tsx as TEXT, assert on structure).

Four properties, each the cheapest static proof available:
  (a) the panel's own block exists and ships its primary testids;
  (b) its call site renders DEAD LAST -- after both the ranked table and the Screen Comparison
      section, so no shipped golden's first-visible-match text search can resolve into it;
  (c) the block never sorts/reverses/slices what it renders (all rows, served order, uncapped);
  (d) the block never reuses a golden click-target attribute (the compare-guard's own tuple).

Like every guard in this family, these prove source structure, never runtime behaviour; each
carries a seeded counter-test."""

from __future__ import annotations

import pathlib
import re

_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"

_BLOCK_START = "// --- Forward returns (forward-test era"
_BLOCK_END = "// --- Screen comparison (goal-desk-iter-35, J-20)"

_REQUIRED_FORWARD_TESTIDS = (
    'data-testid="desk-forward-section"',
    'data-testid="desk-forward-table"',
    'data-testid="desk-forward-compute-button"',
    'data-testid="desk-forward-register"',
    'data-testid="desk-forward-not-computed"',
    # v2 touch-anchored surfaces: the per-row drill-in panel, its per-touch lines, and the
    # collapsed baseline-anchors disclosure -- static presence is their only automated proof
    # (no golden ever clicks a forward row; the panel is a read of an already-loaded record).
    'data-testid="desk-forward-detail"',
    'data-testid="desk-forward-detail-touch"',
    'data-testid="desk-forward-detail-baseline"',
    'data-testid="desk-forward-summary-baseline"',
)

# The golden click-target attributes the compare guard already forbids its own block from reusing
# -- the same tuple, applied to the forward block.
_FORBIDDEN_TESTID_ATTRS = (
    'data-testid="desk-history-row"',
    'data-testid="desk-screen-row"',
)
_FORBIDDEN_DATA_SCREEN_ID_ATTR = "data-screen-id="
_FORBIDDEN_ROW_TESTID_ATTR_RE = re.compile(r'data-testid="desk-row-[a-z-]+"')

_REORDER_RE = re.compile(r"\.\s*(?:sort|reverse|slice)\s*\(")


def _forward_block(source: str) -> str:
    start = source.index(_BLOCK_START)
    end = source.index(_BLOCK_END)
    assert start < end, "the forward block must precede the screen-comparison block in source"
    return source[start:end]


def test_the_forward_block_exists_and_ships_its_testids():
    source = _DESK_PAGE.read_text()
    block = _forward_block(source)
    missing = [testid for testid in _REQUIRED_FORWARD_TESTIDS if testid not in block]
    assert not missing, (
        f"the Forward Returns block is missing testid(s) {missing} -- its primary surfaces must "
        "stay statically present (no golden ever clicks a write path, so presence is the proof)"
    )


def test_the_forward_section_call_site_renders_dead_last():
    """DOM order is call-site order here: the ranked table, then the Screen Comparison section,
    then the Forward Returns section — so every pinned golden text resolves to an element ABOVE
    the new panel, and nothing renders after it to intercept."""
    source = _DESK_PAGE.read_text()
    ranked_call = source.index("<DeskRowsTable")
    compare_call = source.index("<ScreenComparisonSection")
    forward_call = source.index("<DeskForwardSection")
    assert ranked_call < compare_call < forward_call, (
        "the Forward Returns section must render after both the ranked table and the Screen "
        "Comparison section — bottom placement is what makes its copy interception-safe"
    )


def test_the_forward_block_never_reorders_or_caps_what_it_renders():
    source = _DESK_PAGE.read_text()
    block = _forward_block(source)
    hits = _REORDER_RE.findall(block)
    assert not hits, (
        f"the Forward Returns block sorts/reverses/slices its rendered data ({hits}) -- every row "
        "renders in served order, uncapped; the scroll container is the size rail, never a slice"
    )


def test_the_forward_block_reuses_no_golden_click_target():
    source = _DESK_PAGE.read_text()
    block = _forward_block(source)
    for needle in _FORBIDDEN_TESTID_ATTRS:
        assert needle not in block, f"the Forward Returns block reuses {needle}"
    assert _FORBIDDEN_DATA_SCREEN_ID_ATTR not in block, (
        "the Forward Returns block reuses data-screen-id= (a golden CSS click target)"
    )
    assert _FORBIDDEN_ROW_TESTID_ATTR_RE.search(block) is None, (
        "the Forward Returns block reuses a desk-row-* testid (the ranked table's own family)"
    )


def test_the_guards_can_fail_on_seeded_violations():
    """Counter-tests: each detection actually catches its violation."""
    assert _REORDER_RE.search("record.rows.slice(0, 20).map(") is not None
    assert _REORDER_RE.search("forwardRows.sort((a, b) => a.symbol.localeCompare(b.symbol))") is not None
    assert _FORBIDDEN_ROW_TESTID_ATTR_RE.search('<td data-testid="desk-row-distance">') is not None
    seeded_missing = "const x = 1;"
    assert [t for t in _REQUIRED_FORWARD_TESTIDS if t not in seeded_missing] == list(
        _REQUIRED_FORWARD_TESTIDS
    )
