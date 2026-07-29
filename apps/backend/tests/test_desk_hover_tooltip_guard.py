"""era-desk-iter-7 (audit finding F2) source-introspection guard test -- the
``test_desk_ui_guards.py`` pattern (read ``apps/frontend/app/desk/page.tsx`` as TEXT, assert on
substrings/structure; no browser, no runtime).

iter-6's audit found F2: the row's stretched drill-in anchor (``desk-row-drill-in`` /
``desk-skip-row-drill-in``, ``absolute inset-0``) paints above every cell in the row, so the
per-cell ``title``s at ``desk-row-distance``/``desk-row-score`` and each coverage badge's own
``title`` -- which carried the row's full-precision ``distance_bps``/``band_score`` and each
timeframe's "window last requested" freshness -- became pointer-unreachable no matter how deep a
hover targets. iter-7's fix consolidates that lost detail onto the anchor's OWN ``title`` instead
of any covered cell (the anchor is already the topmost element everywhere in the row, so this is
the one placement that stays reachable), with ZERO change to the anchor's ``href``,
``absolute inset-0`` class, or ``data-testid`` -- the click/navigation geometry J-05's own golden
script already depends on stays byte-unchanged.

This guard proves the consolidation actually happened and stays that way: each anchor carries a
dynamic (never static, never empty) ``title`` expression that calls a named function, and that
function's OWN source references the exact fields the fix is required to carry -- full
``row.distance_bps``/``row.band_score`` plus coverage ``latest_window_end_utc`` for the ranked-row
anchor; ONLY the coverage ``latest_window_end_utc`` for the skip-row anchor (a skipped member has
no distance/score value to show, and fabricating one would violate the "honest absence" rule).

A guard that can never fail proves nothing -- ``test_guard_can_fail_on_a_seeded_violation`` below
seeds both a static-title regression and a field-dropped regression and proves the same checks
catch each."""

from __future__ import annotations

import pathlib
import re

import pytest

_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"

_TITLE_EXPR_RE = re.compile(r"title=\{\s*([A-Za-z_][A-Za-z0-9_]*)\(")


def _anchor_block(source: str, testid: str) -> str:
    """The single self-closing ``<Link ... data-testid="<testid>" ... />`` element's own source
    text -- located by its testid, sliced from the nearest preceding ``<Link`` to its own closing
    ``/>`` -- so every check below inspects ONLY that element's own attributes, never the whole
    file."""
    marker = f'data-testid="{testid}"'
    idx = source.index(marker)
    start = source.rindex("<Link", 0, idx)
    end = source.index("/>", idx) + len("/>")
    return source[start:end]


def _anchor_title_function_name(source: str, testid: str) -> str:
    """The name of the function the anchor's ``title={...}`` expression calls. Raises (via a
    failed ``assert``) if the anchor carries no ``title`` at all, or a static one (e.g.
    ``title="drill in"``) -- a static/absent title is exactly the F2 regression this guard exists
    to catch."""
    block = _anchor_block(source, testid)
    match = _TITLE_EXPR_RE.search(block)
    assert match is not None, (
        f"anchor {testid!r} carries no dynamic title={{fn(...)}} expression -- its hover tooltip "
        f"is unreachable or static:\n{block}"
    )
    return match.group(1)


def _extract_function(source: str, name: str) -> str:
    """The full source text of function ``name``'s block, from its ``function name(`` declaration
    to its own matching closing brace -- a plain brace-depth walk (TSX has no Python ``ast``
    module to lean on here), the same "read as TEXT" discipline this whole module uses."""
    marker = f"function {name}("
    start = source.index(marker)
    brace_start = source.index("{", start)
    depth = 0
    end = brace_start
    for i in range(brace_start, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    return source[start : end + 1]


def test_ranked_row_drill_in_tooltip_is_built_from_distance_score_and_coverage_freshness():
    """The ranked-row (``desk-row-drill-in``) anchor's tooltip-building function references the
    row's own full ``distance_bps``, full ``band_score``, and coverage ``latest_window_end_utc``
    -- the exact three fields audit F2 found unreachable once the anchor started painting above
    their per-cell ``title``s. goal-desk-iter-9 (J-08) adds two more required needles:
    ``basis_as_of``/``basis_age_days`` -- the new basis column is a plain descriptive `<td>` with
    NO per-cell ``title`` of its own (the same F2 lesson applied proactively), so its full-precision
    detail must join this SAME consolidated tooltip or it is unreachable by pointer, exactly like
    the three fields above. goal-desk-iter-15 (J-11) adds one more: ``row.history_start`` -- the
    new history column applies the identical F2-proactive discipline."""
    source = _DESK_PAGE.read_text()
    fn_name = _anchor_title_function_name(source, "desk-row-drill-in")
    fn_source = _extract_function(source, fn_name)
    for needle in (
        "row.distance_bps", "row.band_score", "latest_window_end_utc",
        "row.basis_as_of", "row.basis_age_days", "row.history_start",
    ):
        assert needle in fn_source, (
            f"{fn_name}() never references {needle!r} -- the ranked row's composite hover "
            "tooltip must carry the row's own full-precision distance/score/basis plus coverage "
            "freshness, not a static or empty string"
        )


def test_skip_row_drill_in_tooltip_carries_coverage_freshness_only():
    """The skip-row (``desk-skip-row-drill-in``) anchor's tooltip-building function references
    coverage ``latest_window_end_utc`` but NEVER ``distance_bps``/``band_score`` -- a skipped
    member has no distance/score value, and fabricating one would violate the honest-absence
    rule."""
    source = _DESK_PAGE.read_text()
    fn_name = _anchor_title_function_name(source, "desk-skip-row-drill-in")
    fn_source = _extract_function(source, fn_name)
    assert "latest_window_end_utc" in fn_source, (
        f"{fn_name}() never references latest_window_end_utc -- the skip row's tooltip must still "
        "carry its own coverage-freshness detail"
    )
    for forbidden in ("distance_bps", "band_score"):
        assert forbidden not in fn_source, (
            f"{fn_name}() references {forbidden!r} -- a skipped member has no distance/score "
            "value to show; this would fabricate one"
        )


def test_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing. Two seeded regressions, each
    caught by the checks above: (1) a static ``title`` on the anchor (no dynamic expression to
    find at all), and (2) a tooltip function that dropped one of the required fields."""
    seeded_static_title = (
        '<td>\n  <Link href="/structure" data-testid="desk-row-drill-in" title="drill in" '
        'className="absolute inset-0" />\n</td>'
    )
    with pytest.raises(AssertionError):
        _anchor_title_function_name(seeded_static_title, "desk-row-drill-in")

    seeded_field_dropped = (
        "function deskRowDrillInTitle(row: DeskScreenRow): string {\n"
        "  return `distance ${row.distance_bps} bps`;\n"
        "}\n\n"
        "<td>\n"
        '  <Link data-testid="desk-row-drill-in" title={deskRowDrillInTitle(row)} '
        'className="absolute inset-0" />\n'
        "</td>"
    )
    fn_name = _anchor_title_function_name(seeded_field_dropped, "desk-row-drill-in")
    fn_source = _extract_function(seeded_field_dropped, fn_name)
    assert "row.distance_bps" in fn_source
    assert "row.band_score" not in fn_source  # the seeded violation: score was dropped
    assert "latest_window_end_utc" not in fn_source  # the seeded violation: coverage was dropped
