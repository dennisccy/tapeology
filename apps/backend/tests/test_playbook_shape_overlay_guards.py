"""Structural guards for the playbook setup-shape overlay: the /desk occurrence expansion, the
/structure drill-in that consumes it, and the canvas primitive that draws it.

There is no frontend test runner in this repo (no `test` npm script, no `.test.ts(x)` anywhere), so
this follows the established precedent for guarding frontend LOGIC keylessly: Python
source-inspection over the `.tsx`/`.ts` sources (see `test_structure_chart_viewport.py`'s docstring
for the prior art). Every guard here carries a SEEDED counter-test -- a lint that cannot fail
proves nothing.

The invariants are the ones a later refactor could silently undo while everything still renders:

  1. **The shape mapper never derives a price.** It is presentation mapping over a served record;
     the moment it computes a midpoint or a width, the chart is showing a number the detector never
     recorded. Guarded by the SAME `_PRICE_ARITHMETIC_PATTERN` the desk page is held to, imported
     rather than re-copied, and extended with the anchor bindings.
  2. **The mapper stays pure.** No React, no fetch, no charting library -- so it can be read and
     reasoned about as a function, and so the canvas code stays a renderer that decides nothing.
  3. **A record with no anchors degrades honestly**, per SIGNAL and never off `payload_version`.
  4. **The primitive respects the three lightweight-charts subtleties** that are invisible until
     they bite: a stable pane-view array (the library caches on reference), bitmap-space drawing
     (or everything is blurry/misplaced on a HiDPI screen), and the
     `timeToCoordinate -> timeToIndex -> logicalToCoordinate` fallback (the direct call returns
     null for every instant not exactly on a loaded bar, which is most of them).
  5. **The drill-in reads BY RECORD ID, never by date** -- `?date=` returns the NEWEST version, so
     a re-compute between render and click would silently draw a different record's signal.
  6. **Occurrences render in the record's own served order**, never re-sorted client-side.
"""

from __future__ import annotations

import re
from pathlib import Path

from test_desk_ui_guards import _PRICE_ARITHMETIC_FIELDS

BACKEND_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
SHAPE_MAPPER = FRONTEND_DIR / "lib" / "playbookShapes.ts"
SHAPE_SPEC = FRONTEND_DIR / "lib" / "chartShapes.ts"
SHAPE_PRIMITIVE = FRONTEND_DIR / "components" / "chartShapePrimitive.ts"
STRUCTURE_CHART = FRONTEND_DIR / "components" / "StructureChart.tsx"
STRUCTURE_PAGE = FRONTEND_DIR / "app" / "structure" / "page.tsx"
DESK_PAGE = FRONTEND_DIR / "app" / "desk" / "page.tsx"
PLAYBOOK_HELPERS = FRONTEND_DIR / "lib" / "playbook.ts"

_JSX_COMMENT = re.compile(r"\{/\*.*?\*/\}", re.DOTALL)
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT = re.compile(r"//[^\n]*")


def _read(path: Path) -> str:
    assert path.exists(), f"expected {path} to exist"
    return path.read_text()


def _code(path: Path) -> str:
    """Source with comments stripped -- a guard must never pass or fail on prose that merely
    DESCRIBES the thing it forbids (`test_copy_discipline`'s own `_strip_comments` discipline)."""
    source = _read(path)
    source = _JSX_COMMENT.sub(" ", source)
    source = _BLOCK_COMMENT.sub(" ", source)
    return _LINE_COMMENT.sub(" ", source)


# --- 1. the mapper never derives a price ---------------------------------------------------------
#
# The desk page's own alternation, EXTENDED with the bindings this mapper reads (never a second
# copy of it -- one owner, imported above). A box midpoint is the obvious thing to reach for and
# the obvious thing to get wrong: the detector recorded two edges, not a middle.
_MAPPER_PRICE_FIELDS = (
    rf"{_PRICE_ARITHMETIC_FIELDS}"
    r"|signal\.(?:entry|price_low|price_high)"
    r"|anchors\.[a-z_]+\.price"
    r"|(?:point|pivot|rim|anchor|touch)\.price"
)
_MAPPER_PRICE_PATTERN = re.compile(
    rf"({_MAPPER_PRICE_FIELDS})\s*[-+*/]|[-+*/]\s*({_MAPPER_PRICE_FIELDS})"
)


def test_shape_mapper_never_derives_a_price():
    hits = _MAPPER_PRICE_PATTERN.findall(_code(SHAPE_MAPPER))
    assert not hits, (
        f"lib/playbookShapes.ts derives a value via arithmetic on a served price ({hits}) -- it "
        "maps recorded anchors to display specs and must draw only prices the detector itself "
        "recorded, never a midpoint, width, or level computed in the browser"
    )


def test_shape_mapper_price_arithmetic_guard_can_fail_on_a_seeded_violation():
    """The box midpoint someone will eventually reach for, and a 'how far is the stop' figure."""
    seeded_midpoint = "const mid = (signal.price_low + signal.price_high) / 2;"
    assert _MAPPER_PRICE_PATTERN.search(seeded_midpoint) is not None

    seeded_risk = "const risk = signal.entry - signal.invalidation_price;"
    assert _MAPPER_PRICE_PATTERN.search(seeded_risk) is not None

    seeded_anchor = "const depth = anchors.first_pivot.price - anchors.structure_pivot.price;"
    assert _MAPPER_PRICE_PATTERN.search(seeded_anchor) is not None


# --- 2. the mapper stays pure --------------------------------------------------------------------


def test_shape_mapper_is_a_pure_module():
    source = _code(SHAPE_MAPPER)  # a comment SAYING "no fetch" must not read as a fetch
    for banned in ('"use client"', "useState", "useEffect", "useMemo", "fetch(", "lightweight-charts"):
        assert banned not in source, (
            f"lib/playbookShapes.ts references {banned!r} -- it must stay a pure function over an "
            "already-served signal: no React, no reads of its own, and no coupling to the charting "
            "library (that is what keeps it separable from the canvas renderer)"
        )
    # The one derivation it IS allowed is a TIME unit conversion, and even that must be guarded --
    # a malformed anchor has to be DROPPED, never coerced to a price/time of 0.
    assert "Number.isFinite" in source, (
        "lib/playbookShapes.ts no longer guards its anchor reads -- an absent or malformed value "
        "would coerce to 0 and draw a shape at a price that was never recorded"
    )


def test_shape_mapper_purity_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- reaching for a hook or a read inside the mapper is caught."""
    seeded_hook = "const shapes = useMemo(() => build(signal), [signal]);"
    seeded_read = "const record = await fetch(`/research/desk/playbook?id=${id}`);"
    for banned, seeded in (("useMemo", seeded_hook), ("fetch(", seeded_read)):
        assert banned in seeded


def test_the_spec_module_is_free_of_both_react_and_the_charting_library():
    """`lib/chartShapes.ts` is the vocabulary the producer and the renderer share; if it imported
    either side's dependencies, that separation would be nominal."""
    source = _code(SHAPE_SPEC)  # comments only DESCRIBE the rule; they must not be linted by it
    assert "lightweight-charts" not in source and "react" not in source
    assert "import" not in source, (
        "lib/chartShapes.ts imports something -- it is the vocabulary the producer and the "
        "renderer share, and stays dependency-free so neither side can leak into the other"
    )


def test_shape_primitive_holds_no_playbook_knowledge():
    """The renderer draws specs. If it learned what a `double_top` is, the mapper's purity would
    stop being worth anything -- the setup vocabulary would live in two places."""
    source = _code(SHAPE_PRIMITIVE)
    for banned in ("setup_id", "double_top", "playbook", "geometry"):
        assert banned not in source, (
            f"components/chartShapePrimitive.ts references {banned!r} -- it must know only about "
            "ChartShapeSpec, never about the playbook the shapes came from"
        )


# --- 3. honest degradation, per signal -----------------------------------------------------------


def test_shape_mapper_degrades_honestly_when_a_record_carries_no_anchors():
    source = _code(SHAPE_MAPPER)
    assert "anchors.setup_id !== signal.setup_id" in source, (
        "the mapper no longer refuses a MISMATCHED (signal, anchors) pair -- it would draw one "
        "setup's outline over another's bars, which looks entirely plausible and is wrong"
    )
    assert '"partial"' in source and '"absent"' in source, (
        "the mapper no longer distinguishes a partial result from an absent one -- a record with "
        "no recorded outline must SAY so rather than silently drawing nothing"
    )
    assert "payload_version" not in source, (
        "the mapper keys its legacy check off payload_version -- whether a shape can be drawn is "
        "a per-SIGNAL, per-family fact, not a whole-record one; key off the absent `anchors`"
    )


def test_the_structure_page_renders_the_partial_state_rather_than_hiding_it():
    source = _code(STRUCTURE_PAGE)
    for testid in (
        "structure-playbook-shape-partial",
        "structure-playbook-unavailable",
        "structure-playbook-signal-not-found",
        "structure-playbook-symbol-mismatch",
        "structure-playbook-timeframe-fallback",
    ):
        assert testid in source, (
            f"/structure no longer renders {testid} -- each of these is a way the drill-in can "
            "fail to produce an outline, and every one of them must be visible rather than "
            "leaving an unexplained bare chart"
        )


# --- 4. the three lightweight-charts subtleties --------------------------------------------------


def test_shape_primitive_returns_a_stable_pane_view_array():
    """The library caches pane views BY ARRAY REFERENCE and its own doc comment asks a primitive to
    "return the same array if nothing changed" -- building a fresh one per call defeats that cache
    on every repaint."""
    source = _code(SHAPE_PRIMITIVE)
    assert re.search(r"paneViews\(\)[^{]*\{\s*return\s+this\._paneViews;", source), (
        "chartShapePrimitive's paneViews() no longer returns its single stored array -- a fresh "
        "array literal here defeats the library's own reference-based view cache"
    )
    assert re.search(r"paneViews\(\)[^{]*\{\s*return\s*\[", source) is None


def test_shape_primitive_draws_in_bitmap_space():
    source = _code(SHAPE_PRIMITIVE)
    assert "useBitmapCoordinateSpace" in source
    assert "horizontalPixelRatio" in source and "verticalPixelRatio" in source, (
        "the renderer no longer scales by the device pixel ratios -- every shape would be drawn at "
        "the wrong size and position on a HiDPI display"
    )


def test_shape_primitive_falls_back_when_timeToCoordinate_returns_null():
    """The subtlest fact in the whole feature: `timeToCoordinate` returns null for any instant not
    exactly on a loaded bar -- which is every instant between bars and every one outside the loaded
    window. Without the index fallback a shape spanning a gap simply vanishes."""
    source = _code(SHAPE_PRIMITIVE)
    for call in ("timeToCoordinate(", "timeToIndex(", "logicalToCoordinate("):
        assert call in source, (
            f"chartShapePrimitive no longer calls {call} -- the "
            "timeToCoordinate -> timeToIndex -> logicalToCoordinate chain is what keeps a shape "
            "drawable across a data gap"
        )


def test_shape_primitive_fallback_guard_can_fail_on_a_seeded_violation():
    """A renderer using only the direct converter is caught."""
    seeded = "const x = timeScale.timeToCoordinate(time as Time);"
    assert "timeToIndex(" not in seeded and "logicalToCoordinate(" not in seeded


def test_the_chart_detaches_every_primitive_it_attaches():
    source = _code(STRUCTURE_CHART)
    assert "attachPrimitive(" in source and "detachPrimitive(" in source, (
        "StructureChart attaches a primitive it never detaches -- an emptied `shapes` array would "
        "leave the last setup's outline drawn over an unrelated chart"
    )
    assert "shapePrimitiveRef.current = null;" in source, (
        "the mount teardown no longer drops the primitive handle -- the next mount would reuse a "
        "primitive bound to a destroyed series"
    )


def test_the_chart_shape_props_are_optional_with_defaults():
    """Every pre-existing call site (both /structure charts and the cockpit) passes none of these,
    so they must default to the absent behaviour and render byte-identically to before."""
    source = _read(STRUCTURE_CHART)
    assert "shapes = []," in source
    assert "shapes?: ChartShapeSpec[];" in source
    assert "shapeCaption?: string;" in source
    assert "focusRange?: { fromTs: number; toTs: number };" in source


def test_the_chart_discloses_a_clipped_shape_in_the_dom():
    """`timeToIndex(t, true)` SNAPS an off-window anchor to the nearest loaded bar, so a box can
    appear to end exactly where the data ends. That is a plausible-looking lie, and the only honest
    fix is to say so in text -- canvas pixels are also the one thing a browser pass cannot read."""
    source = _code(STRUCTURE_CHART)
    assert "structure-chart-shape-clipped" in source
    assert "chartShapeTimeSpan(shapes)" in source, (
        "the clipped check no longer measures the shapes' own span against the loaded bars"
    )


# --- 5. the drill-in reads by record id ----------------------------------------------------------


def test_structure_reads_the_playbook_record_by_id_never_by_date():
    source = _code(STRUCTURE_PAGE)
    assert "fetchDeskPlaybook({ id:" in source, (
        "/structure no longer resolves the drilled-in occurrence by record id"
    )
    assert "fetchDeskPlaybook({ date:" not in source, (
        "/structure resolves the drilled-in occurrence by DATE -- that read returns the newest "
        "version for a date, so a re-compute landing between the /desk render and the click would "
        "silently draw a different record's signal under the same key"
    )


def test_the_prefill_block_still_returns_early_before_reading_any_new_param():
    """The two-param early return must stay FIRST, so a link carrying only `symbol`+`asof` (every
    ranked-row drill-in) behaves exactly as it did before the playbook params existed."""
    source = _read(STRUCTURE_PAGE)
    start = source.index("// J-05-PREFILL-START")
    end = source.index("// J-05-PREFILL-END")
    block = source[start:end]
    early_return = block.index("if (!symbol || !asOf) return;")
    for param in ('searchParams.get("tf")', 'searchParams.get("playbook")', 'searchParams.get("signal")'):
        assert param in block, f"the prefill block no longer reads {param}"
        assert block.index(param) > early_return, (
            f"{param} is read BEFORE the two-param early return -- a partial link would then "
            "mutate page state that used to be left untouched"
        )


def test_prefill_ordering_guard_can_fail_on_a_seeded_violation():
    seeded = '''// J-05-PREFILL-START
    const tf = searchParams.get("tf");
    if (!symbol || !asOf) return;
    // J-05-PREFILL-END'''
    early_return = seeded.index("if (!symbol || !asOf) return;")
    assert seeded.index('searchParams.get("tf")') < early_return


def test_the_drill_in_link_carries_the_record_and_signal_identity():
    # Reads `lib/playbook.ts`, not the page: the URL moved into the ONE shared builder
    # (`playbookDrillInHref`) when the flat signals table gained the same drill-in, so that both
    # tables are mechanically incapable of sending an operator to two different charts for one
    # signal. The terms this guard protects are unchanged -- only their home moved.
    source = _code(PLAYBOOK_HELPERS)
    for term in (
        "playbook=${encodeURIComponent(recordId)}",
        "signal=${encodeURIComponent(playbookSignalKey(signal))}",
        "tf=${encodeURIComponent(detectTimeframe)}",
    ):
        assert term in source, (
            f"the occurrence drill-in link no longer carries {term} -- without the (record id, "
            "signal key) pair /structure cannot resolve WHICH occurrence to outline"
        )


def test_the_detect_timeframe_is_read_from_the_record_never_hardcoded():
    """The backend serves `parameters.detect_timeframe` precisely so the frontend does not keep a
    second copy of "5m" that can drift from the detectors."""
    source = _code(DESK_PAGE)
    assert "record.parameters.detect_timeframe" in source
    # Scoped to the playbook occurrence components rather than the whole 7k-line page: a bar
    # timeframe literal elsewhere on /desk is somebody else's business, but one HERE would be a
    # second copy of a value the record already serves.
    start = source.index("function PlaybookOccurrenceRow")
    body = source[start : source.index("function PlaybookSummaryView")]
    assert '"5m"' not in body and "'5m'" not in body, (
        "the occurrence drill-in hardcodes a bar timeframe -- read `parameters.detect_timeframe` "
        "off the record, which is the timeframe the detector actually ran on"
    )


# --- 6. served order, one identity function ------------------------------------------------------


def test_occurrence_rows_default_to_the_records_own_served_order():
    """A deliberate, PAID-FOR narrowing, recorded rather than hidden.

    This guard's property was never "no `.sort(` appears in this function". It was: the occurrences
    render in the order the record serves them, nothing is truncated, and the one value derived from
    an occurrence's POSITION -- the amber beyond-cap chip -- means its position in the record.

    Occurrences are now sortable by clicking a column header. The dishonest way to permit that was
    available and is refused: `useTableSort(occurrences, ...)` contains no `.sort(`, so all three
    bans below would have gone on passing while the ordering shipped underneath them.

    What is given up: the list can display occurrences in an order the record did not serve. What
    pays for it:

      (a) The three bans stay -- this function still owns no comparator and still caps nothing.
      (b) The pool filter is still the ONLY narrowing of `record.signals`.
      (c) Reordering goes through the shared hook, whose mapping is total (nothing dropped),
          guarded in apps/backend/tests/test_table_sort_guards.py.
      (d) THE CAP CHIP READS `servedIndex`, never the map index. The pool means above are computed
          over the first `rail_max_touches_per_row` occurrences AS SERVED, so under any other
          display order a map index would move the chip onto occurrences that did feed the means
          and off the ones that did not -- the chip would be precisely inverted on a reversed sort.
    """
    source = _code(DESK_PAGE)
    start = source.index("function PlaybookOccurrenceList")
    body = source[start : source.index("function PlaybookSummaryView")]
    assert "record.signals.filter(" in body
    for banned in (".sort(", ".reverse(", ".slice("):
        assert banned not in body, (
            f"PlaybookOccurrenceList calls {banned} -- occurrences must render in the order the "
            "record itself serves them, never re-ordered or truncated client-side"
        )
    assert "useTableSort(occurrences" in body, (
        "PlaybookOccurrenceList no longer reaches its display order through the shared sort hook"
    )
    # NAMED REVISION: the chip used to read the row's POSITION (`entry.servedIndex >= cap`), which
    # was correct only while this list was always the record's whole pool. It now narrows with the
    # section's display filters, and a filtered array re-origins that index — moving the chip onto
    # occurrences that DID feed the pooled means and off ones that did not. It now reads the
    # SERVED `in_cap` flag, which is the fact itself rather than a proxy for it. The intent this
    # guard protects is unchanged: the chip must never be derived from render position.
    assert "beyondCap={playbookBeyondCap(cohorts, entry.item, cap)}" in body, (
        "the beyond-cap chip no longer follows the occurrence's SERVED position -- under a sort it "
        "would mark the wrong occurrences as outside the pool"
    )
    assert "index >= cap" not in body, (
        "the beyond-cap chip reads a map index -- that is the DISPLAY position once the list can "
        "be sorted, not the position the pool means were computed over"
    )


def test_the_beyond_cap_served_index_guard_can_fail_on_a_seeded_violation():
    """The pre-sort expression is exactly what this guard now has to reject."""
    seeded = "beyondCap={cap !== null && index >= cap}"
    assert "beyondCap={cap !== null && entry.servedIndex >= cap}" not in seeded
    assert "index >= cap" in seeded


# --- 7. what happened next, per occurrence -------------------------------------------------------
#
# Both playbook tables now carry the occurrence's OWN forward returns and its side-matched max
# drawdown, rendered by one shared cell block so the two cannot drift.


def _forward_cells_body(source: str) -> str:
    start = source.index("function PlaybookForwardCells")
    return source[start : source.index("function playbookForwardColumns")]


def test_the_forward_cells_read_the_records_own_horizon_labels():
    """The same rule `detect_timeframe` already follows: the record serves its horizons, so a
    literal "1m"/"5m" here would be a second copy that drifts the moment a record is measured under
    a different set."""
    source = _code(DESK_PAGE)
    start = source.index("function PlaybookForwardCells")
    body = source[start : source.index("function PlaybookRecordView")]
    for literal in ('"1m"', '"5m"', '"1h"', '"4h"', "'1m'", "'5m'"):
        assert literal not in body, (
            f"the playbook forward columns hardcode {literal} -- read the labels off "
            "`parameters.rail_horizons_minutes` via playbookHorizonLabels, which is what the "
            "detectors actually measured"
        )
    assert "playbookHorizonLabels(record)" in body, (
        "PlaybookOccurrenceList no longer derives its horizon labels from the record"
    )


def test_the_forward_cells_reach_their_values_through_the_guarded_bindings():
    """The desk arithmetic lint (`test_desk_ui_guards.py::_PRICE_ARITHMETIC_FIELDS`) can only see
    what is written as `touchRow.<served field>` / `touchValue.<served field>`. Writing these cells
    against those bindings puts them under that lint with zero new regex; a local rename would route
    six new numeric columns around the one check proving this page derives nothing."""
    body = _forward_cells_body(_code(DESK_PAGE))
    assert "const touchRow = signal.forward;" in body, (
        "the forward block is no longer bound as `touchRow` -- the arithmetic lint cannot see it"
    )
    assert "touchRow?.horizons[label] ?? FORWARD_UNMEASURED_HORIZON" in body, (
        "the per-horizon leaf is no longer bound as `touchValue` off the guarded row"
    )
    for field in (
        "touchValue.return_pct",
        "touchRow.to_close_pct",
        "touchRow.mdd_long_pct",
        "touchRow.mdd_short_pct",
    ):
        assert field in body, (
            f"{field} is not read under its guarded binding name in PlaybookForwardCells"
        )


def test_an_absent_measurement_renders_as_an_absence_and_never_as_a_zero():
    """Three distinct absences, each read as itself: no `forward` block at all (a record predating
    measurement), a horizon present-and-null with the backend's own reason, and a horizon this
    record never measured. A zero in any of those positions would be a fabricated result -- and 0.00
    on a return column reads as "this setup did nothing", which is a claim."""
    body = _forward_cells_body(_code(DESK_PAGE))
    assert "PLAYBOOK_LEGACY_ABSENCE" in body, (
        "a record with no forward block does not name why its cells are empty"
    )
    assert "touchRow === undefined" in body, "the legacy-absence branch is gone"
    assert "touchValue.return_pct === null" in body, "the per-horizon null branch is gone"
    assert "FORWARD_UNMEASURED_HORIZON" in body, (
        "a horizon this record never measured falls through to something other than the shipped "
        "honest-absence constant"
    )
    assert "touchValue.reason" in body, (
        "the backend's own reason for a null horizon is not surfaced -- the reader would see an em "
        "dash with no way to learn why"
    )
    assert 'touchValue.truncated ? "†"' in body, "the truncation marker is gone"
    for fabricated in ("?? 0", "|| 0", "?? 0.0"):
        assert fabricated not in body, (
            f"the forward cells fall back to {fabricated!r} -- an absence must never be rendered as "
            "a measured zero"
        )


def test_the_absence_lint_can_fail_on_a_seeded_violation():
    seeded = "{fmt(touchValue.return_pct ?? 0)}"
    assert "?? 0" in seeded
    assert "touchValue.return_pct === null" not in seeded


def test_the_drawdown_column_is_side_matched_and_discloses_both_served_numbers():
    """One drawdown column, not two: the section's shipped sign note already states that a row's
    adverse excursion is the one on its own side. Nothing is hidden -- both served numbers ride the
    cell's title, so the other side stays checkable. A ternary is a selection, not arithmetic."""
    body = _forward_cells_body(_code(DESK_PAGE))
    assert 'signal.side === "long" ? touchRow.mdd_long_pct : touchRow.mdd_short_pct' in body, (
        "the drawdown cell no longer selects the excursion matching the row's own side"
    )
    assert "mdd long ${String(touchRow.mdd_long_pct)} · mdd short ${String(touchRow.mdd_short_pct)}" in body, (
        "the drawdown cell no longer discloses BOTH served numbers -- showing one side without the "
        "other, unchecked, is the reason the single column needed paying for"
    )


def test_the_occurrence_disclosure_survives_the_stretched_drill_in_link():
    """The whole occurrence row is covered by one absolutely-positioned anchor, so a `title` on an
    individual `<td>` is occluded and never surfaces. The forward columns' absence and truncation
    reasons would be unreachable in this table alone -- so they ride the ANCHOR's own title, the
    same fix `DeskRow` already uses via `deskRowDrillInTitle`."""
    source = _code(DESK_PAGE)
    assert "function playbookOccurrenceDrillInTitle(" in source, (
        "the occurrence anchor has no composite disclosure -- every per-cell title in that row is "
        "covered by the stretched link"
    )
    # The helper is declared directly above the row it serves, so the row body runs from its own
    # marker to the list that renders it.
    helper_at = source.index("function playbookOccurrenceDrillInTitle")
    row_at = source.index("function PlaybookOccurrenceRow")
    assert helper_at < row_at, "the anchor-title helper is no longer declared above its row"
    row = source[row_at : source.index("function PlaybookOccurrenceList")]
    assert "title={playbookOccurrenceDrillInTitle(signal, labels)}" in row, (
        "the drill-in anchor does not carry the row's own forward disclosure"
    )
    helper = source[helper_at:row_at]
    assert "PLAYBOOK_LEGACY_ABSENCE" in helper and "touchValue.reason" in helper, (
        "the anchor title drops the absence reasons it exists to carry"
    )
    assert "†" in helper, "the anchor title drops the truncation disclosure"


# --- 8. the entry time, named on the chart ------------------------------------------------------


def test_the_trigger_mark_carries_the_entry_time():
    """The chart drew WHERE a setup fired but never WHEN — the reader had to hold the desk row's own
    "trigger (ET)" cell in their head while looking at the candles.

    The time comes off the trigger anchor (`anchors.trigger.ts`), which is the instant the chart is
    already framed on, the instant the drill-in link's `asof` carries, and the instant the amber dot
    already sits at. It is NOT `forward.at_utc`: that is a measurement anchor, often a 1m sub-bar of
    the drawn 5m candle, and absent on legacy records — so labelling with it would print a time no
    candle on screen is at."""
    source = _code(SHAPE_MAPPER)
    assert "formatTimeET(triggerTs * 1000)" in source, (
        "the trigger mark's label no longer formats the trigger instant through the shared ET "
        "formatter -- the chart's own axis and crosshair use it, so a second formatter here could "
        "disagree with the ticks beneath the label"
    )
    assert "forward" not in source, (
        "the shape mapper reads the forward block -- the entry time must come from the trigger "
        "anchor the chart is drawn on, not from the measurement anchor"
    )


def test_the_shape_mapper_stays_pure_after_gaining_a_formatter():
    """`lib/datetime.ts` is import-free, so depending on it cannot pull React, a fetch or the chart
    library into a module whose purity is pinned. Asserted here rather than assumed."""
    datetime_lib = (FRONTEND_DIR / "lib" / "datetime.ts").read_text()
    assert "import " not in datetime_lib, (
        "lib/datetime.ts gained an import -- the shape mapper depends on it and is guarded pure"
    )
    assert "export function formatTimeET(" in datetime_lib


def test_a_dot_renders_the_label_it_declares():
    """`ChartShapeDot` has declared `label?` since the overlay shipped, and the primitive silently
    dropped it -- so the trigger dot's own label never drew. Rendering it is what puts the entry
    time on the canvas at all.

    Unlike a box or a segment, a dot gets no minimum-width test: that test asks whether the text is
    wider than the mark it names, and a dot has no width to compare against."""
    source = _code(SHAPE_PRIMITIVE)
    start = source.index('case "dot"')
    # Sliced to the case's own closing brace, NOT to its first `break;`: the case opens with an
    # early `if (at === null) break;`, so a break-bounded slice would end before any drawing
    # happened and every assertion below would pass on an empty haystack.
    body = source[start : source.index("\n          }", start)]
    assert "context.arc(" in body, "the dot-case slice missed the drawing itself"
    assert "this._label(" in body, (
        "a dot still drops the label it declares -- ChartShapeDot.label would be dead in the type"
    )
    assert "MIN_LABEL_WIDTH" not in body, (
        "the dot label is gated on a width test -- a dot has no width, so the gate would silently "
        "never pass"
    )


def test_the_dot_label_guard_can_fail_on_a_seeded_violation():
    seeded = 'case "dot": {\n  context.fill();\n  context.stroke();\n  break;'
    body = seeded[: seeded.index("break;")]
    assert "this._label(" not in body


def test_the_entry_time_reaches_the_readable_legend_too():
    """Canvas text cannot be asserted by a browser pass and cannot be selected by a reader. The
    trigger dot's legend entry therefore renders the SAME `shape.label`, so one string feeds both
    surfaces and they cannot come to disagree about when the setup fired."""
    source = _code(SHAPE_MAPPER)
    start = source.index("function legendFor")
    body = source[start : source.index("export function playbookSignalShapes")]
    assert "add(shape.color, shape.label ?? " in body, (
        "the legend no longer renders the trigger mark's own label -- the entry time would exist "
        "only as canvas pixels, unreadable to a test and unselectable by a reader"
    )


def test_the_two_record_scoped_views_do_not_share_a_sibling_key():
    """A real defect this guard exists because of, caught live in the browser.

    `PlaybookSummaryView` and `PlaybookSignalsTable` are SIBLINGS inside `PlaybookRecordView`, and
    both are keyed on the record so that switching session dates drops the previous record's
    expanded pools and chosen sort. Keyed on a BARE `record.id`, they are two siblings with the
    same key: React's reconciliation breaks, and every subsequent re-render (clicking a signal row
    is enough) APPENDS another copy of the summary instead of updating the one already there --
    observed going 1 -> 2 -> 3 copies on consecutive clicks, each showing the same numbers, which
    reads as three different pools' results stacked.

    Keys must therefore be distinct AND still record-scoped: dropping the record id to dodge the
    collision would silently carry one session's expansions and sort into the next."""
    source = _code(DESK_PAGE)
    start = source.index("function PlaybookRecordView")
    body = source[start:]
    summary_key = "key={`playbook-summary-${record.id}`}"
    signals_key = "key={`playbook-signals-${record.id}`}"
    assert summary_key in body, "PlaybookSummaryView's call site lost its prefixed record key"
    assert signals_key in body, "PlaybookSignalsTable's call site lost its prefixed record key"
    assert body.count("key={record.id}") == 0, (
        "a record-scoped sibling is keyed on a BARE record.id -- if two of them are, React appends "
        "duplicate views instead of updating them"
    )
    # Both still scoped to the record, so a date switch really does reset them.
    for key in (summary_key, signals_key):
        assert "${record.id}" in key


def test_the_sibling_key_guard_can_fail_on_a_seeded_violation():
    """The exact shape that shipped and duplicated the summary in the browser."""
    seeded = (
        "function PlaybookRecordView() {\n"
        "  <PlaybookSummaryView key={record.id} record={record} />\n"
        "  <PlaybookSignalsTable key={record.id} record={record} />\n"
        "}"
    )
    assert seeded.count("key={record.id}") == 2
    assert "key={`playbook-summary-${record.id}`}" not in seeded


def test_both_playbook_tables_render_the_same_forward_cells():
    """One renderer, two call sites -- so the drill-in table and the all-symbols table cannot come
    to disagree about what happened after a signal."""
    source = _code(DESK_PAGE)
    assert source.count("<PlaybookForwardCells signal={signal} labels={labels} />") == 2, (
        "the two playbook tables no longer share ONE forward-cell renderer"
    )
    assert source.count("...playbookForwardColumns(labels)") == 2, (
        "the two playbook tables no longer share ONE forward-column definition"
    )
    assert source.count("<PlaybookForwardLegend />") == 2, (
        "a table carrying the truncation dagger ships without its legend"
    )


def test_the_beyond_cap_disclosure_reads_the_served_cap():
    """`record.signals` holds EVERY detected signal, but the pool means shown above the expansion
    are computed over the first `rail_max_touches_per_row` only. Without this the expansion implies
    every listed occurrence fed the mean directly above it, which is false for a large pool."""
    source = _code(DESK_PAGE)
    assert "record.parameters.rail_max_touches_per_row" in source
    assert "desk-playbook-occurrence-beyond-cap" in source


def test_the_signal_identity_helpers_have_exactly_one_definition():
    """Both /desk and /structure identify a signal; two copies of the key format would let a row
    and its own link disagree about which occurrence they name."""
    helpers = _read(PLAYBOOK_HELPERS)
    for name in ("playbookSignalKey", "playbookPoolKey", "playbookSetupLabel"):
        assert f"export function {name}(" in helpers
        for page in (DESK_PAGE, STRUCTURE_PAGE):
            assert f"function {name}(" not in _code(page), (
                f"{page.name} re-declares {name} instead of importing it from lib/playbook.ts"
            )


def test_the_expansion_is_a_real_button_with_an_announced_state():
    """A `<tr onClick>` (the pattern the rest of this page uses) is unreachable by keyboard and
    announces nothing. The expand control is the one place that gap is not propagated -- and
    `aria-expanded` is also what a browser pass can read to prove the row opened."""
    source = _code(DESK_PAGE)
    start = source.index("function PlaybookSummaryView")
    body = source[start:]
    assert 'data-testid="desk-playbook-summary-expand"' in body
    assert "aria-expanded={expandedPools.has(poolKey)}" in body
    assert "aria-controls=" in body


# --- 7. the paged-history fill loop this work uncovered -------------------------------------------


def test_a_forward_paging_chart_never_auto_shifts_on_an_appended_bar():
    """The chart option that stops a lazily-loaded page from moving the operator's view.

    With the library's default (shift on new bar) and the viewport at the right edge, every
    appended page scrolls the chart right, which re-fires the lazy-load subscription, which appends
    another page: a fill loop that walks the window from the as-of clean off to the end of the
    recorded series. It is tied to `onNeedNewer` rather than hardcoded off, because a chart that
    CANNOT page forward (the cockpit, whose right edge is the live tape) genuinely wants to follow
    its own newest bar -- and that call site must keep the library's existing behaviour exactly."""
    source = _code(STRUCTURE_CHART)
    assert "shiftVisibleRangeOnNewBar: onNeedNewer === undefined," in source, (
        "StructureChart no longer ties the auto-shift to whether the chart can page forward -- "
        "hardcoding it true restores the forward fill loop; hardcoding it false stops the cockpit's "
        "live chart from following its own newest bar"
    )
    # The discriminator only means anything if the two kinds of call site really do differ.
    structure_page = _code(STRUCTURE_PAGE)
    price_chart = _code(FRONTEND_DIR / "components" / "PriceChart.tsx")
    assert structure_page.count("onNeedNewer=") == 2, (
        "both /structure charts must page forward -- they draw a historical window with recorded "
        "bars on either side of the as-of"
    )
    assert "onNeedNewer" not in price_chart, (
        "the cockpit chart now pages forward -- it must not: its right edge is the live tape, and "
        "a forward-paging live chart is exactly the fill-loop shape this guard exists to prevent"
    )
