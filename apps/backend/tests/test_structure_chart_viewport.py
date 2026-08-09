"""Structural guards for the /structure chart's viewport paging + band-line legibility.

There is no frontend test runner in this repo (no `test` npm script, no `.test.ts(x)` file
anywhere), so this module follows the established precedent for testing frontend LOGIC keylessly:
a Python source-inspection test that reads the `.tsx`/`.ts` source directly (see
`test_price_chart_confluence.py`'s module docstring for the full list of prior art).

The invariants guarded here are the ones a later refactor could silently undo while everything
still renders:

  1. **The page never asks for every candle again.** The Structure page's bar-series read carries
     `includeBars: false` (metadata only) and the candles arrive through the bounded
     `GET /research/bars/{id}/candles` window — the whole point of the paging work. Re-introducing
     a no-param `fetchBarSeriesList()` here would quietly restore a multi-megabyte page load.
  2. **The chart is created ONCE and updated in place**, and lazily extends on scroll. Re-creating
     it per data change (the pre-paging behavior — the effect's dep array carried `bars`) would
     throw away the operator's scroll position on every appended page, making lazy loading useless.
     `fitContent()` must stay gone: it squeezes the whole loaded window into the canvas width,
     which is exactly the "thousands of unreadable 1px candles" state paging exists to end.
  3. **Band lines are thin and labelled once.** Both edges of a band carry the same description, so
     labelling both doubled every tag on a 288px-tall canvas.
"""

from __future__ import annotations

import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
STRUCTURE_CHART = FRONTEND_DIR / "components" / "StructureChart.tsx"
STRUCTURE_PAGE = FRONTEND_DIR / "app" / "structure" / "page.tsx"
BAR_WINDOW = FRONTEND_DIR / "lib" / "useBarWindow.ts"
API_TS = FRONTEND_DIR / "lib" / "api.ts"
# The ONE shared recorded-series metadata read (both /structure and the cockpit container use it).
RECORDED_SERIES_HOOK = FRONTEND_DIR / "lib" / "useRecordedSeries.ts"


def _read(path: Path) -> str:
    assert path.exists(), f"expected {path} to exist"
    return path.read_text()


def _code(path: Path) -> str:
    """The source with `//` line comments stripped — for the "this call must not reappear" guards,
    where the prose explaining WHY it is gone would otherwise match itself."""
    return "\n".join(re.sub(r"//.*$", "", line) for line in _read(path).splitlines())


# --- 1. the page reads metadata, then pages candles ---------------------------------------------


def test_structure_page_requests_bar_series_metadata_only():
    """The metadata-only invariant, asserted where the read now LIVES: the page (and the cockpit
    container) reads series metadata through the shared `useRecordedSeries` hook, and THAT hook
    requests the metadata-only projection."""
    source = _read(STRUCTURE_PAGE)
    hook = _read(RECORDED_SERIES_HOOK)
    assert "useRecordedSeries(" in source, (
        "the Structure page must read series metadata through the shared useRecordedSeries hook "
        "(the same read the cockpit container uses)"
    )
    assert "includeBars: false" in hook, (
        "the shared hook must request the metadata-only bar-series projection — a full "
        "fetchBarSeriesList() pulls every candle of every registered series into the browser"
    )
    for text in (source, hook):
        assert "fetchBarSeriesList()" not in text, "found a no-param (full-candle) bar-series read"
    assert "useBarWindow(" in source, "the charts must draw a paged window, not a whole series"


def test_candles_window_is_read_through_the_canonical_bounded_endpoint():
    api = _read(API_TS)
    assert "/research/bars/${seriesId}/candles?" in api
    assert "/research/candles?" in api, "expected the merged candle read"
    for param in ("before_ts", "after_ts", "limit"):
        assert param in api, f"expected the candles read to send {param}"

    hook = _read(BAR_WINDOW)
    # The window reports the ENDPOINT's own flags — never a count-based guess at whether more rows
    # exist (which would keep asking forever at the true series edge, or stop early mid-series).
    for flag in ("has_more_before", "has_more_after"):
        assert flag in hook, f"expected the hook to read the served {flag} flag"


def test_charts_page_the_merged_read_not_a_single_recording():
    """A symbol accumulates many overlapping recordings; a chart bound to ONE of them stops loading
    while longer recordings of the same symbol+timeframe sit in the store — the "zooming out loads
    nothing" defect. The window hook must therefore be keyed on symbol+timeframe and read the merged
    endpoint."""
    hook = _read(BAR_WINDOW)
    assert "fetchMergedCandles(" in hook
    assert "fetchBarCandles(" not in hook, "the window must not page a single recording"
    assert "series_count" in hook and "revised_timestamps" in hook, (
        "the hook must carry the served merge facts through for the caption"
    )
    page = _read(STRUCTURE_PAGE)
    assert re.search(r"useBarWindow\(\s*\n?\s*[^)]*symbol", page), (
        "expected the page to key the window on the loaded symbol"
    )


def test_loaded_window_is_capped_and_the_cap_is_disclosed():
    hook = _read(BAR_WINDOW)
    assert "MAX_LOADED_BARS" in hook
    assert re.search(r"MAX_LOADED_BARS\s*=\s*\d+", hook), "the cap must be an explicit constant"
    page = _read(STRUCTURE_PAGE)
    assert "MAX_LOADED_BARS" in page and "held at once" in page, (
        "a capped window must say so in the chart caption rather than silently truncating history"
    )


# --- 2. one chart instance, extended on scroll --------------------------------------------------


def test_chart_is_created_once_and_not_rebuilt_per_data_change():
    source = _read(STRUCTURE_CHART)
    creation = source.index("lc.createChart(")
    tail = source[creation:]
    deps = re.search(r"\},\s*\[([^\]]*)\]\s*\)\s*;", tail)
    assert deps, "could not find the chart-creation effect's dependency array"
    assert deps.group(1).strip() == "", (
        "the chart-creation effect must be mount-only ([]) — re-creating the chart per data change "
        f"discards the operator's scroll position; found deps=[{deps.group(1).strip()}]"
    )


def test_chart_lazily_requests_more_bars_and_never_squeezes_the_whole_window():
    source = _read(STRUCTURE_CHART)
    assert "subscribeVisibleLogicalRangeChange" in source, (
        "the chart must watch the visible range to lazily extend the loaded window"
    )
    assert "onNeedOlder" in source and "onNeedNewer" in source
    assert "fitContent(" not in _code(STRUCTURE_CHART), (
        "fitContent() crushes the entire loaded window into the canvas width — the paged chart "
        "must set an explicit viewport-sized visible range instead"
    )
    assert "setVisibleLogicalRange" in source


def test_request_size_is_measured_from_the_visible_range_not_the_barspacing_option():
    """`timeScale().options().barSpacing` returns the CONFIGURED spacing; a user zoom updates a
    private field instead, so anything sized from it is blind to zoom (the defect that made a
    zoomed-out chart ask for a fixed ~200 bars and appear not to refresh). The deficit must come
    from the visible logical range itself."""
    code = _code(STRUCTURE_CHART)
    for expression in ("EDGE_BARS - range.from", "range.to - (loaded - 1 - EDGE_BARS)"):
        assert expression in code, f"expected the deficit to be measured as {expression}"
    # options().barSpacing may still size the FIRST viewport (before any zoom exists) — but never
    # the paging deficit, so it must not appear in the trigger.
    trigger = code[code.index("function requestMissingBars") : code.index("function initialViewportBars")]
    assert "barSpacing" not in trigger


def test_chart_keeps_filling_after_a_page_lands():
    """One page rarely covers a wide zoom-out, and requests dropped by the hook's in-flight guard
    would otherwise never be re-issued — so the same deficit check must run after every data
    update, not only on operator gestures."""
    code = _code(STRUCTURE_CHART)
    assert "requestMissingBars(range, { fill: false })" in code, "expected the gesture trigger"
    assert "{ fill: true }" in code, "expected the post-update fill re-check"


def test_a_zoomed_out_window_is_filled_from_one_side_only():
    """With the cap trimming the far end, requesting BOTH directions for a span wider than the
    loaded window would ping-pong: load older, trim newer, load newer, trim older, forever."""
    code = _code(STRUCTURE_CHART)
    assert "missingBefore > 0 && missingAfter > 0" in code
    assert "movingNewer" in code


def test_draw_effects_wait_for_the_dynamically_imported_chart():
    """The candle window resolves in milliseconds and can land BEFORE the dynamic
    `import("lightweight-charts")` does. Every draw effect must therefore depend on the
    chart-created STATE flag, or it bails out on a missing series and — with nothing left to
    re-trigger it — leaves a permanently blank chart (observed in the browser before this guard)."""
    source = _read(STRUCTURE_CHART)
    assert "setChartReady(true)" in source, "the chart-creation effect must publish a ready flag"
    dep_arrays = re.findall(r"\},\s*\[([^\]]*)\]\s*\)\s*;", source)
    draw_deps = [deps for deps in dep_arrays if "bars" in deps or "levels" in deps]
    assert draw_deps, "expected draw effects keyed on the drawn data"
    for deps in draw_deps:
        assert "chartReady" in deps, f"draw effect deps [{deps}] must include chartReady"


def test_window_changes_preserve_the_visible_range():
    """Logical indices are positions in the LOADED window, so they shift when an older page is
    prepended AND when the cap trims rows off the left. Re-basing the range on a remembered visible
    bar's TIMESTAMP covers both; a prepend-count-only shift (the first implementation) would jump
    the view the moment a trim happened."""
    code = _code(STRUCTURE_CHART)
    assert "getVisibleLogicalRange()" in code
    assert re.search(r"anchor\s*=", code), "expected a remembered anchor bar"
    # The array named here is whatever the component actually FED the library (era-desk-iter-4 audit
    # B1 renamed it `drawableBars` — the finite-price-filtered view — so the anchor index and the
    # library's own logical index stay the same number). The invariant under test is unchanged: the
    # anchor is re-located by TIMESTAMP, never by a row count.
    assert re.search(r"\w*[Bb]ars\.findIndex\(\(b\) => b\.ts === anchor\.ts\)", code), (
        "the anchor must be re-located by timestamp, not by a row count"
    )
    assert "anchor.offset" in code, "the anchor's offset from the range's left edge must be kept"


# --- 3. thin, singly-labelled band lines --------------------------------------------------------


def test_band_and_level_lines_are_one_pixel():
    source = _read(STRUCTURE_CHART)
    widths = set(re.findall(r"lineWidth:\s*(\d+)", source))
    assert widths == {"1"}, f"expected every reference line to be 1px thin, found widths {widths}"


def test_only_one_edge_of_a_band_carries_a_label():
    source = _read(STRUCTURE_CHART)
    assert re.search(r"labelled:\s*true", source) and re.search(r"labelled:\s*false", source), (
        "expected a band's two edges to be drawn with ONE labelled edge and one unlabelled edge"
    )
    assert "axisLabelVisible: edge.labelled" in source
    assert 'title: edge.labelled ? title : ""' in source


def test_band_lines_still_read_only_served_band_fields():
    """The thinner styling must not have introduced any client-side scoring/clustering — every
    drawn value is still a served `TradabilityBand` field, verbatim."""
    source = _read(STRUCTURE_CHART)
    for field in (
        "band.side",
        "band.price_low",
        "band.price_high",
        "band.class",
        "band.quality_score",
        "band.round_number",
    ):
        assert field in source, f"expected the band overlay to read {field} verbatim"


# --- the current-day shortcuts -------------------------------------------------------------------


def test_today_shortcut_buttons_fill_market_dates_without_submitting():
    """Both shortcuts fill only -- neither submits -- and both resolve "today" on the EXCHANGE
    clock.

    The date they fill is the market's, not the browser's and not UTC's. Either of those rolls over
    while New York is still on the prior evening, so for an operator east of Greenwich they fill in
    a session that has not traded yet: at 09:00 in Hong Kong both already read tomorrow. `Today` is
    a shortcut for "the session I am looking at", and only the exchange's own date is that."""
    source = _read(STRUCTURE_PAGE)
    for testid in ("fetch-today-button", "structure-as-of-today-button"):
        assert f'data-testid="{testid}"' in source
        marker = source.index(f'data-testid="{testid}"')
        window = source[marker - 200 : marker + 400]
        assert 'type="button"' in window, f"{testid} must not submit its form"
        assert "todayEtDate()" in window, (
            f"{testid} no longer resolves today on the market clock -- a UTC or local date fills a "
            "session that has not happened for any operator east of New York"
        )
    assert "todayUtcDate()" not in source, (
        "the page is resolving its own UTC today again -- there is one shared `todayEtDate()`"
    )
    # The as-of shortcut reuses the page's EXISTING end-of-day convention rather than inventing a
    # second one (the same instant a post-fetch As-of seed uses). The DAY is the market's; the
    # end-of-day INSTANT stays anchored to that day's UTC midnight, because the backend's
    # `_resolve_basis` selects the prior session off the as-of's own UTC calendar date -- moving it
    # to the end of the ET day would cross UTC midnight and advance the basis by a session.
    assert "endOfDayUtc(todayEtDate())" in source
    assert "toISOString().slice(0, 10)" in source, (
        "endOfDayUtc no longer derives its day-end from the value's own UTC calendar date"
    )


# --- 4. the traded-volume pane ------------------------------------------------------------------
#
# The histogram under the candles is drawn by the SHARED chart component, so one set of properties
# governs it on the cockpit and on both /structure charts. Four of them could be undone by a
# refactor while the pane still rendered something, and each failure is quiet:
#
#   * created outside the mount-only effect -> a second series added per data change, leaking one
#     per update until the chart is unusable;
#   * on the candles' own price scale -> volume is orders of magnitude larger than price, so the
#     candles flatten to a line;
#   * fed from a NEW third data effect -> it stops inheriting the paging/anchor and in-place-update
#     work the two existing effects already do, and drifts out of step with the candles it annotates;
#   * a constant colour -> the bar no longer says which way its own candle went, which is the only
#     reason to tint it at all.


def _mount_effect(source: str) -> str:
    """The chart-creation effect's body -- from `lc.createChart(` to its own `}, []);`.

    `test_chart_is_created_once_and_not_rebuilt_per_data_change` above already proves that terminator
    IS mount-only, so slicing to it is the same boundary, not a second opinion about it."""
    creation = source.index("lc.createChart(")
    tail = source[creation:]
    end = re.search(r"\},\s*\[\s*\]\s*\)\s*;", tail)
    assert end, "could not find the end of the mount-only chart-creation effect"
    return tail[: end.end()]


def test_the_volume_pane_is_built_once_on_its_own_scale():
    source = _read(STRUCTURE_CHART)
    mount = _mount_effect(source)
    assert mount.count("lc.HistogramSeries") == 2, (
        "the two volume series (recorded + live) are no longer created inside the mount-only "
        "effect -- creating a series per data change leaks one on every update"
    )
    assert source.count("lc.HistogramSeries") == 2, (
        "a volume series is created somewhere outside the mount-only effect"
    )
    assert "priceScaleId: VOLUME_SCALE_ID" in mount, (
        "the volume series no longer has a price scale of its own -- sharing the candles' scale "
        "flattens them, since volume is orders of magnitude larger than price"
    )
    assert "chart.priceScale(VOLUME_SCALE_ID).applyOptions({" in mount
    assert "const VOLUME_SCALE_MARGINS = { top: 0.8, bottom: 0 } as const;" in source, (
        "the volume scale's margins no longer confine the histogram to the bottom fifth"
    )
    assert "scaleMargins: VOLUME_SCALE_MARGINS" in mount


def test_the_volume_pane_rides_the_two_existing_data_effects():
    """Both the recorded-bar path and the live-bar path feed it, and neither is a new effect."""
    source = _read(STRUCTURE_CHART)
    assert "volumeSeriesRef.current?.setData(drawableBars.map(volumePoint));" in source, (
        "the recorded-bars effect no longer feeds the volume pane -- it would keep whatever the "
        "previous window left behind while the candles paged away from it"
    )
    assert "liveVolume?.update(volumePoint(" in source, (
        "the live path no longer updates the last volume bar IN PLACE -- the growing bar's volume "
        "would freeze while its candle kept moving"
    )
    assert "liveVolume?.setData(drawableLiveBars.map(volumePoint));" in source, (
        "the live path's wholesale-redraw branch no longer feeds the volume pane"
    )
    # The effect inventory is unchanged: the pane was threaded through what was already there.
    assert len(re.findall(r"\buseEffect\(", source)) == 8, (
        "the number of effects in StructureChart changed -- the volume pane must ride the two "
        "EXISTING data effects (store bars, live bars), never add a third of its own"
    )


def test_each_volume_bar_is_tinted_by_its_own_candles_direction():
    source = _read(STRUCTURE_CHART)
    assert "color: (bar.close >= bar.open ? UP_COLOR : DOWN_COLOR) + VOLUME_ALPHA," in source, (
        "volume bars no longer take their colour from their own candle's direction -- a single "
        "flat colour says nothing the candle above it does not already say"
    )
    # The palette is named once and shared with the candles, never restated as a second literal.
    assert 'const UP_COLOR = "#34d399"' in source and 'const DOWN_COLOR = "#fb7185"' in source
    assert "upColor: UP_COLOR" in source, (
        "the candle series no longer reads the same palette constants the histogram tints from -- "
        "the two would drift apart"
    )
    # A row with no recorded volume draws a zero-height bar rather than crashing the series.
    assert "Number.isFinite(bar.volume) ? bar.volume : 0" in source


def test_the_volume_pane_guards_can_fail_on_seeded_violations():
    """Each detection above, seeded -- a guard that cannot fail proves nothing."""
    seeded_own_effect = (
        "useEffect(() => {\n"
        "  chart.addSeries(lc.HistogramSeries, volumeOptions);\n"
        "}, [drawableBars]);\n"
    )
    assert re.search(r"\},\s*\[\s*\]\s*\)\s*;", seeded_own_effect) is None

    seeded_shared_scale = "chart.addSeries(lc.HistogramSeries, { priceFormat: { type: 'volume' } });"
    assert "priceScaleId: VOLUME_SCALE_ID" not in seeded_shared_scale

    seeded_flat_color = 'color: "#34d399" + VOLUME_ALPHA,'
    assert (
        "color: (bar.close >= bar.open ? UP_COLOR : DOWN_COLOR) + VOLUME_ALPHA,"
        not in seeded_flat_color
    )
