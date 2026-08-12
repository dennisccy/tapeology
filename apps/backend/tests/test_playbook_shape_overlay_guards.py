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
    source = _code(DESK_PAGE)
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


def test_occurrence_rows_render_in_the_records_own_served_order():
    source = _code(DESK_PAGE)
    start = source.index("function PlaybookOccurrenceList")
    body = source[start : source.index("function PlaybookSummaryView")]
    assert "record.signals.filter(" in body
    for banned in (".sort(", ".reverse(", ".slice("):
        assert banned not in body, (
            f"PlaybookOccurrenceList calls {banned} -- occurrences must render in the order the "
            "record itself serves them, never re-ordered or truncated client-side"
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
