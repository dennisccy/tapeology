"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { BarRow, SrLevel, TradabilityBand } from "@/lib/types";
import type { ChartShapeSpec } from "@/lib/chartShapes";
import { chartShapeTimeSpan } from "@/lib/chartShapes";
import { formatDateET, formatDateTimeET, formatTimeET } from "@/lib/datetime";
import { ChartShapePrimitive } from "./chartShapePrimitive";
import { EmptyHint } from "./Panel";

// The /structure page's price chart (J-01): candles from ONE representative recorded bar series
// (the page picks it — see `pickRepresentativeSeries` in lib/timeframes) plus one dashed price line
// per S/R level, labelled by its OWN timeframe + type. Every candle and every level's
// price/timeframe/type is read VERBATIM from the props (already fetched by the page) — this
// component computes nothing; it only draws.
//
// It is now ALSO the cockpit chart's renderer (app/page.tsx's PriceChart delegates its drawing
// here), via a set of OPTIONAL, defaulted props that are all absent for the /structure call sites
// (so those render byte-identically to before):
//   * `liveBars` — the tape's live moving bars, drawn on a SECOND candlestick series to the right of
//     the recorded store bars; updated in place each poll so the last bar animates.
//   * `extraMarkers` / `extraPriceLines` — pre-built display specs (tape-state markers + thesis
//     geometry) the cockpit overlays; the component draws them verbatim, deciding nothing.
//   * `secondsVisible` — the cockpit's second-resolution axis (the tape's own granularity).
//   * `asOfLabel` — the boundary marker's caption ("start" on the cockpit, "as-of" on /structure).
//
// era-5B J-05 (additive): an optional `bands` prop overlays the tradable map's price bands
// (GET /research/tradability, read verbatim by the page) beside the existing level lines. Default
// `[]` means every EXISTING caller (the raw-levels toggle's "on" render) draws byte-identically to
// before this iteration — this is a pure additive prop, never a rewrite of the level-line path.
//
// Candle range vs. as-of: the page passes a WINDOW of the recorded bar series (candles extend past
// the query time so later price action is visible against the historically-marked lines). The
// optional `asOfTs` prop marks the boundary — an "as-of" marker on the last bar the level/band
// computation could see; bars to its right are later context only. The lines stay lookahead-free
// (computed by the backend as of the query time); this component still only draws.
//
// Viewport paging: the chart no longer receives (or `fitContent()`-squeezes) a whole series. The
// page's `useBarWindow` hook holds one window, and this component asks for exactly what its VISIBLE
// SPAN is missing — `onNeedOlder` / `onNeedNewer` — whenever a zoom or a pan leaves part of that
// span unloaded. It decides only WHEN more rows are wanted and how many are missing; which rows
// exist remains entirely the endpoint's answer.
//
// The deficit is measured off the visible logical range itself, NOT off
// `timeScale().options().barSpacing`: in lightweight-charts v5 a user zoom updates a private field
// (`_private__setBarSpacing`) while `options()` keeps returning the CONFIGURED value, so anything
// derived from it is blind to zoom — the reason an earlier revision of this component asked for a
// fixed ~200 bars however far out the operator zoomed, and appeared to "not refresh".

// Come within this many bars of a loaded edge and the next rows are requested — far enough ahead
// that the fetch usually lands before the edge is actually reached.
const EDGE_BARS = 20;
// Extra bars requested beyond the measured deficit, as a share of the visible span — one gesture in
// the same direction then usually needs no second round trip.
const LOOKAHEAD_SHARE = 0.5;
// The first viewport's width in bars when the container has not been measured yet (SSR/first frame).
const INITIAL_VIEWPORT_BARS = 300;
// Where the as-of bar sits in the first visible window: 80% across, leaving the later price action
// visible to its right (matching how the page's first window is fetched).
const AS_OF_VIEWPORT_SHARE = 0.8;
// A drilled-in setup's own framing: the breathing room left to the left of a formation whose start
// would otherwise sit hard against the edge of the window, as a share of the current viewport.
const FOCUS_MARGIN_SHARE = 0.1;
// Beyond this many raw levels the per-line price-scale labels stop being readable as a scale and
// start being a wall of overlapping text — the lines themselves are all still drawn.
const MAX_LEVEL_AXIS_LABELS = 12;

// The band palette: the SAME up/down colors the candle series itself uses, so resistance/support
// read as one visual family with the candles. Non-A-class bands (and unclassed ones) draw in a
// dimmed variant so conviction is legible at a glance — a display mapping of the SERVED `class`
// value, never a re-scoring of it.
const BAND_COLORS = {
  resistance: { strong: "#fb7185", dim: "#9f5866" }, // rose-400 / dimmed rose
  support: { strong: "#34d399", dim: "#3f8570" }, // emerald-400 / dimmed emerald
};

// The candle palette, named once so the volume histogram below can tint each bar to match the
// candle it sits under (rather than restating the hex values a third time).
const UP_COLOR = "#34d399"; // emerald-400
const DOWN_COLOR = "#fb7185"; // rose-400

// The volume pane's own price scale. Kept off the candles' scale so volume — which is orders of
// magnitude larger than price — can never rescale or flatten them. `scaleMargins.top` pushes the
// histogram into the bottom fifth of the canvas; the candles' own margins keep them clear of it.
const VOLUME_SCALE_ID = "volume";
const VOLUME_SCALE_MARGINS = { top: 0.8, bottom: 0 } as const;
const PRICE_SCALE_MARGINS = { top: 0.1, bottom: 0.25 } as const;

// Volume bars sit UNDER the candles, so they are drawn at reduced opacity: at full strength the
// histogram competes with the price action it is meant to annotate. `88` is the alpha byte.
const VOLUME_ALPHA = "88";

// A ready-to-draw series marker (the cockpit builds these from its served tape-state + thesis
// values; this component draws them verbatim on the live series).
export interface ChartMarkerSpec {
  time: number;
  position: "aboveBar" | "belowBar";
  color: string;
  shape: "arrowDown" | "arrowUp" | "circle";
  text: string;
}

// A ready-to-draw horizontal price line (the cockpit builds these from its served thesis geometry).
export interface ChartPriceLineSpec {
  price: number;
  color: string;
  lineWidth: number;
  lineStyle: number;
  axisLabelVisible: boolean;
  title: string;
}

// Is ONE served row drawable as a candle? The charting library asserts (and THROWS, unmounting the
// whole page) on a candle whose open/high/low/close is not a number — and JSON serves a stored
// non-finite price as `null`. The backend now excludes such rows from the merged read and reports
// them in `integrity_errors` (research/bars.py), so this is defence in depth, not the fix: one
// unusable row must degrade the CHART (dropped, and said so beneath it), never delete the page.
// era-desk-iter-4 audit B1 — the reproduced failure was exactly "Assertion failed: Candlestick
// series item data value of open must be a number, got=object, value=null", 0.1s after the wall
// rendered, on 58 symbols including the era's pinned AAPL.
function isDrawableCandle(bar: BarRow): boolean {
  return (
    Number.isFinite(bar.ts) &&
    Number.isFinite(bar.open) &&
    Number.isFinite(bar.high) &&
    Number.isFinite(bar.low) &&
    Number.isFinite(bar.close)
  );
}

// One served row as a volume histogram point, tinted to match the candle above it. A row whose
// stored `volume` is missing or non-finite contributes 0 height rather than crashing the series —
// the same defence-in-depth `isDrawableCandle` applies to prices. The bar is still drawn (its
// candle is), so a zero here reads as "no volume recorded for this bar", never as a gap.
function volumePoint(bar: BarRow) {
  return {
    time: bar.ts as any,
    value: Number.isFinite(bar.volume) ? bar.volume : 0,
    color: (bar.close >= bar.open ? UP_COLOR : DOWN_COLOR) + VOLUME_ALPHA,
  };
}

export function StructureChart({
  bars,
  levels,
  bands = [],
  asOfTs,
  asOfLabel = "as-of",
  onNeedOlder,
  onNeedNewer,
  loadingMore = false,
  liveBars = [],
  extraMarkers = [],
  extraPriceLines = [],
  secondsVisible = false,
  shapes = [],
  shapeCaption,
  focusRange,
}: {
  bars: BarRow[];
  levels: SrLevel[];
  bands?: TradabilityBand[];
  asOfTs?: number;
  asOfLabel?: string;
  onNeedOlder?: (count: number, opts?: { fill?: boolean }) => void;
  onNeedNewer?: (count: number, opts?: { fill?: boolean }) => void;
  loadingMore?: boolean;
  // Cockpit-only additive props (absent for /structure -> byte-identical there).
  liveBars?: BarRow[];
  extraMarkers?: ChartMarkerSpec[];
  extraPriceLines?: ChartPriceLineSpec[];
  secondsVisible?: boolean;
  // Playbook-shape-overlay additive props (absent at every pre-existing call site -> byte-identical
  // there). `shapes` are ready-to-draw display specs the PAGE built from a served playbook record;
  // this component draws them verbatim and decides nothing about them. MEMOIZE them in the caller:
  // a fresh array each render would re-run the attach/update effect on every render.
  shapes?: ChartShapeSpec[];
  shapeCaption?: string;
  // Widens the FIRST viewport so a whole formation fits, never narrows it (see the effect below).
  focusRange?: { fromTs: number; toTs: number };
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  // Only drawable rows reach the library (see isDrawableCandle). Everything downstream — the
  // viewport anchoring, the as-of index, the "any candles at all" hint — indexes into THIS array,
  // so a dropped row can never shift the operator's scroll position onto the wrong candle.
  const drawableBars = useMemo(() => bars.filter(isDrawableCandle), [bars]);
  const drawableLiveBars = useMemo(() => liveBars.filter(isDrawableCandle), [liveBars]);
  const undrawableCount = bars.length - drawableBars.length + (liveBars.length - drawableLiveBars.length);
  // Whether a drawn setup extends past the candles currently loaded. Checked here on the DATA, not
  // in the canvas: the renderer's own coordinate fallback SNAPS an off-window anchor to the nearest
  // loaded bar, which would draw a box that appears to end where the data ends — a plausible
  // looking lie. Saying so in the DOM is what keeps that honest (and gives a browser pass something
  // to read; canvas pixels are not assertable).
  const shapeSpan = useMemo(() => chartShapeTimeSpan(shapes), [shapes]);
  const shapeClipped =
    shapeSpan !== null &&
    drawableBars.length > 0 &&
    (shapeSpan.from < drawableBars[0].ts || shapeSpan.to > drawableBars[drawableBars.length - 1].ts);
  // `chartReady` flips once the dynamically imported chart library has built the chart+series. It
  // is STATE (not just a ref) on purpose: the candle window resolves in a few milliseconds and can
  // easily land BEFORE the dynamic import does, and a ref would leave the draw effects with nothing
  // to draw into and nothing to re-trigger them — a permanently blank chart. As a dependency of
  // every draw effect below it re-runs them the moment the chart exists. (PriceChart.tsx never hit
  // this: its data polls every second, so its next tick re-runs the effect anyway.)
  const [chartReady, setChartReady] = useState(false);
  // The chart is created ONCE per mount and updated in place (PriceChart.tsx's own lifecycle):
  // re-creating it per data change would discard the operator's scroll position on every lazily
  // appended page — the exact interaction this component now depends on.
  const chartRef = useRef<any>(null);
  const seriesRef = useRef<any>(null);
  const libRef = useRef<any>(null);
  const markersRef = useRef<any>(null);
  const priceLinesRef = useRef<any[]>([]);
  const shapePrimitiveRef = useRef<ChartShapePrimitive | null>(null);
  // The setup framing is applied at most once per mount — see the focus effect below.
  const focusAppliedRef = useRef(false);
  // The SECOND candlestick series holding the tape's live moving bars (cockpit only). Kept distinct
  // from the recorded-store series so the no-lookahead boundary is structural: store bars strictly
  // left of the replay start, live bars from it onward, disjoint by `ts`.
  const liveSeriesRef = useRef<any>(null);
  const liveMarkersRef = useRef<any>(null);
  const drawnLiveRef = useRef<BarRow[]>([]);
  const extraPriceLinesRef = useRef<any[]>([]);
  // The two volume histogram series, mirroring the two candlestick series one-for-one (recorded
  // store bars and live tape bars) so each inherits its partner's paging / in-place-update path.
  const volumeSeriesRef = useRef<any>(null);
  const liveVolumeSeriesRef = useRef<any>(null);
  // Whether anything has been drawn yet — the first data for a chart chooses its own viewport,
  // every later update preserves the operator's.
  const drawnRef = useRef(false);
  // The exact rows currently drawn, so the next update can map a remembered visible bar's timestamp
  // back to its logical index (see the data effect's anchor).
  const drawnBarsRef = useRef<BarRow[]>([]);
  // Paging callbacks live in a ref: the time-scale subscription is installed once, and reading the
  // latest callbacks through a ref keeps it from being torn down and re-installed on every render.
  const needMoreRef = useRef<{
    older?: (count: number, opts?: { fill?: boolean }) => void;
    newer?: (count: number, opts?: { fill?: boolean }) => void;
  }>({});
  needMoreRef.current = { older: onNeedOlder, newer: onNeedNewer };
  const loadedCountRef = useRef(0);
  loadedCountRef.current = bars.length;
  // The previous visible range, so a both-sides-short window (a zoom-out) can be filled in the ONE
  // direction the operator actually moved toward.
  const lastRangeRef = useRef<{ from: number; to: number } | null>(null);

  // --- Create the chart once (client-only dynamic import, never at SSR) -------------------------
  useEffect(() => {
    let disposed = false;

    (async () => {
      const lc = await import("lightweight-charts");
      if (disposed || !containerRef.current) return;

      const chart = lc.createChart(containerRef.current, {
        autoSize: true,
        layout: {
          // The SAME dark instrument-panel surface PriceChart.tsx uses, so the two charts read as
          // one visual family.
          background: { type: lc.ColorType.Solid, color: "#020617" }, // slate-950
          textColor: "#94a3b8", // slate-400
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        },
        grid: {
          vertLines: { color: "#1e293b" }, // slate-800
          horzLines: { color: "#1e293b" },
        },
        rightPriceScale: { borderColor: "#1e293b", scaleMargins: PRICE_SCALE_MARGINS },
        timeScale: {
          borderColor: "#1e293b",
          timeVisible: true,
          secondsVisible: false,
          // A lazily-loaded page must NEVER move the operator's view. The library's default is to
          // shift the visible range when a bar is appended, which is right for a LIVE feed and
          // wrong for a paged history: with the view sitting at the right edge (which the first
          // window's own framing can produce), every appended page scrolls the chart right, which
          // re-fires the lazy-load subscription, which appends another page -- a fill loop that
          // walks the window from the as-of all the way to the end of the recorded series, one
          // page at a time. Observed as a chain of ~30 forward requests when a /desk drill-in
          // opened a 5m chart six weeks before the end of the series.
          //
          // `onNeedNewer` is exactly the right discriminator, not a proxy for one: a chart that
          // can page FORWARD is the only kind that can enter that loop, and a chart that cannot
          // (the cockpit, whose right edge is the live tape) genuinely wants to follow its own
          // newest bar. Read once, at creation -- both are fixed per call site.
          shiftVisibleRangeOnNewBar: onNeedNewer === undefined,
          // Every candle's real UTC-epoch `time` is read on the MARKET clock through the ONE shared
          // formatter — the same clock the rest of the product shows, so an axis reading can be
          // compared against a table cell without converting anything. lightweight-charts passes
          // UTCTimestamp SECONDS. Applied unconditionally: /structure previously fell through to
          // the library's own UTC default while the cockpit rendered local time, which made the two
          // charts disagree about what "09:30" meant.
          //
          // The library also passes the tick's own GRANULARITY, and the label follows it: a tick
          // that marks a day/month/year prints `yyyy-MM-dd`, a tick inside a session prints the
          // clock time alone. Both are shapes this product already uses, and both are ET. Printing
          // the full 23-character stamp on every tick instead would leave a wide chart showing four
          // labels, and would repeat a meaningless `00:00:00` across every daily bar. The COMPLETE
          // stamp lives on the crosshair readout below, which is where a precise reading is asked
          // for rather than scanned.
          tickMarkFormatter: (time: number, tickMarkType: number) =>
            tickMarkType === lc.TickMarkType.TimeWithSeconds
              ? formatTimeET(time * 1000)
              : tickMarkType === lc.TickMarkType.Time
                ? formatTimeET(time * 1000, { seconds: false })
                : formatDateET(time * 1000),
        },
        localization: {
          timeFormatter: (time: number) => formatDateTimeET(time * 1000),
        },
        crosshair: { mode: lc.CrosshairMode.Normal },
      });
      const series = chart.addSeries(lc.CandlestickSeries, {
        upColor: UP_COLOR,
        downColor: DOWN_COLOR,
        wickUpColor: UP_COLOR,
        wickDownColor: DOWN_COLOR,
        borderVisible: false,
      });
      // The live tape-bar series — SAME palette, so recorded + live candles read as one instrument.
      const liveSeries = chart.addSeries(lc.CandlestickSeries, {
        upColor: UP_COLOR,
        downColor: DOWN_COLOR,
        wickUpColor: UP_COLOR,
        wickDownColor: DOWN_COLOR,
        borderVisible: false,
      });
      // The traded-volume pane: one histogram per candlestick series, both bound to their own
      // price scale in the bottom fifth of the canvas. `volume` is served on every bar row the
      // chart already draws (the recorded store's `BarRow` and, since the logical-bar volume
      // addition, the tape's own candles too) — these draw that value, deriving nothing.
      const volumeOptions = {
        priceFormat: { type: "volume" as const },
        priceScaleId: VOLUME_SCALE_ID,
        lastValueVisible: false,
        priceLineVisible: false,
      };
      const volumeSeries = chart.addSeries(lc.HistogramSeries, volumeOptions);
      const liveVolumeSeries = chart.addSeries(lc.HistogramSeries, volumeOptions);
      chart.priceScale(VOLUME_SCALE_ID).applyOptions({
        scaleMargins: VOLUME_SCALE_MARGINS,
        borderVisible: false,
      });

      chartRef.current = chart;
      seriesRef.current = series;
      liveSeriesRef.current = liveSeries;
      volumeSeriesRef.current = volumeSeries;
      liveVolumeSeriesRef.current = liveVolumeSeries;
      libRef.current = lc;
      // The tape-state + thesis markers ride the live series' own marker primitive (the as-of
      // boundary marker rides the store series' — created lazily below).
      liveMarkersRef.current = lc.createSeriesMarkers(liveSeries, []);

      // The lazy-load trigger: every zoom or pan re-measures what the visible span is missing.
      // The hook it calls no-ops when a request is already in flight or when the endpoint reported
      // nothing more exists on that side — so a continuous gesture issues one page at a time and
      // stops honestly at the true edge of what is recorded.
      chart.timeScale().subscribeVisibleLogicalRangeChange((range: any) => {
        requestMissingBars(range, { fill: false });
      });

      setChartReady(true);
    })();

    return () => {
      disposed = true;
      setChartReady(false);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
        seriesRef.current = null;
        liveSeriesRef.current = null;
        volumeSeriesRef.current = null;
        liveVolumeSeriesRef.current = null;
        markersRef.current = null;
        liveMarkersRef.current = null;
        priceLinesRef.current = [];
        extraPriceLinesRef.current = [];
        // The primitive dies with the series it was attached to -- no detach call here, since
        // `chart.remove()` has already disposed it; dropping the handle is what stops the next
        // mount from reusing a primitive bound to a destroyed series.
        shapePrimitiveRef.current = null;
        focusAppliedRef.current = false;
        drawnRef.current = false;
        drawnBarsRef.current = [];
        drawnLiveRef.current = [];
        lastRangeRef.current = null;
      }
    };
  }, []);

  // Ask the page for whatever the VISIBLE SPAN is missing, in bars.
  //
  // Logical indices make this exact: index 0 is the oldest loaded bar, `loaded - 1` the newest, and
  // a range extending past either end (`from` negative, `to` beyond the last index) is empty chart
  // space — precisely the bars that should be there but are not. Zooming out widens the range, so
  // the deficit — and the request — scales with the zoom automatically; panning slides it, so the
  // deficit appears on the side being moved toward.
  //
  // `fill: true` marks a top-up the CHART triggered for itself after data landed (see the data
  // effect) rather than an operator gesture; the hook refuses those once its cap is reached, so a
  // span wider than the cap can never walk the window backwards through the whole history.
  function requestMissingBars(range: any, opts: { fill: boolean }) {
    const loaded = loadedCountRef.current;
    if (!range || loaded === 0) return;
    const span = Math.max(1, range.to - range.from);
    const lookahead = Math.ceil(span * LOOKAHEAD_SHARE);
    const missingBefore = Math.ceil(EDGE_BARS - range.from);
    const missingAfter = Math.ceil(range.to - (loaded - 1 - EDGE_BARS));
    const previous = lastRangeRef.current;
    lastRangeRef.current = { from: range.from, to: range.to };

    if (missingBefore > 0 && missingAfter > 0) {
      // The visible span outruns the loaded window on BOTH sides (a wide zoom-out). Ask in ONE
      // direction only — the one the operator moved toward, defaulting to history — so that at the
      // cap, where a load in one direction trims the other end, the two can never ping-pong.
      const movingNewer = previous != null && range.to > previous.to && range.from >= previous.from;
      if (movingNewer) needMoreRef.current.newer?.(missingAfter + lookahead, opts);
      else needMoreRef.current.older?.(missingBefore + lookahead, opts);
      return;
    }
    if (missingBefore > 0) needMoreRef.current.older?.(missingBefore + lookahead, opts);
    if (missingAfter > 0) needMoreRef.current.newer?.(missingAfter + lookahead, opts);
  }

  // How many bars fit across the drawn area at the chart's DEFAULT bar spacing — used only to size
  // the very first viewport, before the operator has zoomed anything.
  function initialViewportBars(): number {
    const chart = chartRef.current;
    const width = containerRef.current?.clientWidth ?? 0;
    if (!chart || width <= 0) return INITIAL_VIEWPORT_BARS;
    const spacing = chart.timeScale().options().barSpacing || 6;
    return Math.max(EDGE_BARS * 2, Math.ceil(width / spacing));
  }

  // --- Feed the verbatim candles in, preserving the operator's scroll position ------------------
  useEffect(() => {
    const series = seriesRef.current;
    const chart = chartRef.current;
    if (!series || !chart) return;

    // Candles VERBATIM from the loaded window. `ts` is already a real UTC-epoch-seconds value
    // (the bar store's own field — see research/bars.py's `_bar_to_row`), so — unlike
    // PriceChart.tsx's logical-time-to-epoch mapping — no anchor offset is needed here.
    const candles = drawableBars.map((b) => ({
      time: b.ts as any,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));

    const alreadyDrawn = drawnRef.current;
    const visibleRange = chart.timeScale().getVisibleLogicalRange();
    // The leftmost VISIBLE bar, remembered by timestamp before the data changes. Logical indices
    // are positions in the loaded window, so they shift whenever rows are prepended (a lazy older
    // page) or dropped off the left (a cap trim) — re-basing the range on this bar's NEW index is
    // what keeps the operator looking at the same candles through both. Its offset from the range's
    // left edge is preserved too, so a range that extends into empty space stays put.
    const anchor =
      alreadyDrawn && visibleRange && drawnBarsRef.current.length > 0
        ? (() => {
            const index = Math.min(
              drawnBarsRef.current.length - 1,
              Math.max(0, Math.round(visibleRange.from)),
            );
            return { ts: drawnBarsRef.current[index].ts, offset: index - visibleRange.from };
          })()
        : null;

    series.setData(candles);
    // The volume pane rides the SAME rows in the SAME effect, so it inherits the paging, the cap
    // trim and the anchor-preserving viewport logic below without a second data path of its own.
    volumeSeriesRef.current?.setData(drawableBars.map(volumePoint));
    drawnBarsRef.current = drawableBars;

    if (candles.length === 0) {
      drawnRef.current = false;
      return;
    }

    if (!alreadyDrawn) {
      // The FIRST window for this chart: show one viewport ending just past the as-of bar, at the
      // chart's natural bar spacing. (`fitContent()` — the pre-paging behavior — would instead
      // crush the whole window into the canvas width, which is exactly what made a long series
      // unreadable and expensive to draw.)
      const viewport = initialViewportBars();
      const asOfIndex = asOfTs === undefined ? -1 : drawableBars.findIndex((b) => b.ts === asOfTs);
      const to =
        asOfIndex >= 0
          ? Math.min(candles.length, asOfIndex + Math.round(viewport * (1 - AS_OF_VIEWPORT_SHARE)))
          : candles.length;
      chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, to - viewport), to });
    } else if (anchor && visibleRange) {
      const newIndex = drawableBars.findIndex((b) => b.ts === anchor.ts);
      if (newIndex >= 0) {
        const from = newIndex - anchor.offset;
        chart.timeScale().setVisibleLogicalRange({
          from,
          to: from + (visibleRange.to - visibleRange.from),
        });
      }
    }
    drawnRef.current = true;

    // Keep filling: the page that just landed may still not cover the visible span (a wide
    // zoom-out needs several), and any request the hook dropped while this one was in flight is
    // re-issued here. Marked `fill` so the hook can refuse it at its cap. This is what makes the
    // chart converge on a full viewport instead of loading exactly one page per operator gesture.
    requestMissingBars(chart.timeScale().getVisibleLogicalRange(), { fill: true });
  }, [drawableBars, asOfTs, chartReady]);

  // --- Extend the first viewport LEFT to fit a drilled-in setup (playbook drill-in only) --------
  // Its OWN effect rather than a branch of the data effect above, because `focusRange` is derived
  // from a record the page fetches SEPARATELY from the candles: it routinely arrives after the
  // first draw has already happened, at which point that effect's `!alreadyDrawn` branch is closed
  // forever. Applied at most ONCE per mount, so it frames the setup on arrival and then never
  // fights the operator's own scrolling.
  //
  // It moves the LEFT edge only, and only leftward. A formation can begin well before the as-of
  // bar the first window is framed around (an opening range anchored at the session open, with a
  // trigger hours later) and would otherwise be cut off at the left. The right edge is never
  // touched, which is not merely conservative: a visible range extending past the last loaded bar
  // makes the library hold the right edge, which re-fires the lazy-load subscription, which loads
  // another page whose end the range still overruns -- a fill loop that marches the chart all the
  // way to the end of the recorded series, far from the setup it was asked to show.
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart || !focusRange || focusAppliedRef.current || drawableBars.length === 0) return;
    const fromIndex = drawableBars.findIndex((b) => b.ts >= focusRange.fromTs);
    if (fromIndex < 0) return;
    const visible = chart.timeScale().getVisibleLogicalRange();
    if (!visible) return;
    focusAppliedRef.current = true;
    const margin = Math.ceil((visible.to - visible.from) * FOCUS_MARGIN_SHARE);
    const wanted = fromIndex - margin;
    if (wanted >= visible.from) return; // the whole formation is already on screen
    chart.timeScale().setVisibleLogicalRange({ from: wanted, to: visible.to });
  }, [focusRange, drawableBars, chartReady]);

  // --- Attach / update the setup-shape overlay (its own ISeriesPrimitive) -----------------------
  // Its OWN effect and its OWN handle, so redrawing a shape never disturbs the level/band price
  // lines and vice versa (the `extraPriceLines` precedent). `chartReady` is a dependency because
  // the primitive can only attach once the dynamically imported series exists.
  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;
    if (shapes.length === 0) {
      if (shapePrimitiveRef.current) {
        try {
          series.detachPrimitive(shapePrimitiveRef.current);
        } catch {
          // The series may already be disposed — the same tolerance `removePriceLine` needs.
        }
        shapePrimitiveRef.current = null;
      }
      return;
    }
    if (shapePrimitiveRef.current === null) {
      shapePrimitiveRef.current = new ChartShapePrimitive(shapes);
      series.attachPrimitive(shapePrimitiveRef.current);
    } else {
      shapePrimitiveRef.current.setShapes(shapes);
    }
  }, [shapes, chartReady]);

  // --- Feed the live tape bars into the second series (cockpit only) ----------------------------
  // Updated in place so the last bar animates as trades arrive: when the new array is an append-only
  // extension of the drawn one (same bar at the old last index), only the possibly-changed last bar
  // and any appended bars are `update()`d (cheap, and it lets the library follow the right edge);
  // otherwise (first draw, a timeframe switch, or a multi-bucket jump at high replay speed that
  // broke the prefix) it redraws wholesale with `setData`. No `fitContent()` — the viewport is the
  // paged one.
  useEffect(() => {
    const chart = chartRef.current;
    const liveSeries = liveSeriesRef.current;
    if (!chart || !liveSeries) return;

    const candles = drawableLiveBars.map((b) => ({
      time: b.ts as any,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));

    const prev = drawnLiveRef.current;
    const canIncrement =
      prev.length > 0 &&
      candles.length >= prev.length &&
      drawableLiveBars[prev.length - 1]?.ts === prev[prev.length - 1]?.ts;

    const liveVolume = liveVolumeSeriesRef.current;

    if (canIncrement) {
      for (let i = prev.length - 1; i < candles.length; i++) {
        liveSeries.update(candles[i]);
        // The last bar's volume grows with it as trades land, so it is `update`d on exactly the
        // same in-place path as the candle it belongs to.
        liveVolume?.update(volumePoint(drawableLiveBars[i]));
      }
    } else {
      liveSeries.setData(candles);
      liveVolume?.setData(drawableLiveBars.map(volumePoint));
      // First live paint with NO recorded store bars owning the viewport (tape mode, or history
      // mode for a symbol with no recordings): show the last screenful of live bars. When store
      // candles exist, the store data effect above owns the viewport (around the as-of boundary),
      // so this leaves it alone.
      if (prev.length === 0 && !drawnRef.current && candles.length > 0) {
        const viewport = initialViewportBars();
        const to = candles.length;
        chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, to - viewport), to });
      }
    }
    drawnLiveRef.current = drawableLiveBars;
  }, [drawableLiveBars, chartReady]);

  // --- Draw the level + band reference lines (clear-then-redraw, PriceChart.tsx's pattern) ------
  // Kept in its OWN effect so appending a lazily-loaded candle page never re-creates every line.
  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;

    for (const line of priceLinesRef.current) {
      try {
        series.removePriceLine(line);
      } catch {
        // The series may have been disposed between renders — ignore (it is being torn down).
      }
    }
    priceLinesRef.current = [];

    // One dashed price line per level — the declared-reference-line convention PriceChart.tsx
    // already established for thesis geometry. Price/timeframe/type are read verbatim; drawn
    // regardless of whether the price falls inside the charted series' visible range (a level
    // can be sourced from a longer-window timeframe than the one charted). Past
    // MAX_LEVEL_AXIS_LABELS lines the per-line AXIS labels are dropped (the lines stay) so the
    // price scale remains a readable scale rather than a stack of overlapping tags.
    const levelAxisLabels = levels.length <= MAX_LEVEL_AXIS_LABELS;
    for (const level of levels) {
      priceLinesRef.current.push(
        series.createPriceLine({
          price: level.price,
          color: "#94a3b8", // slate-400 — the SAME neutral "declared reference" color PriceChart uses
          lineWidth: 1,
          lineStyle: 2, // LineStyle.Dashed
          axisLabelVisible: levelAxisLabels,
          title: `${level.timeframe} ${level.type}`,
        }),
      );
    }

    // era-5B J-05: one THIN SOLID price line per tradable-band edge (visually distinct from the
    // dashed raw-level lines above), colored by side and dimmed below class A.
    // price_low/price_high/side/class/quality_score/round_number are read verbatim off the prop;
    // this component performs no scoring or clustering of its own. A single-price band
    // (price_low === price_high) draws one line, never a duplicate.
    //
    // Only the band's UPPER edge carries the title + axis label: both edges bear the same
    // description, so labelling both doubled every tag on a 288px-tall canvas and made a
    // ten-band map unreadable. One label per band names the band; the second edge draws as a
    // plain thin line closing it.
    for (const band of bands) {
      const palette = band.side === "resistance" ? BAND_COLORS.resistance : BAND_COLORS.support;
      const color = band.class === "A" ? palette.strong : palette.dim;
      const sideLabel = band.side === "resistance" ? "R" : "S";
      const classLabel = band.class ? ` ${band.class}` : "";
      // The score is DISPLAY-rounded to one decimal in this label only (a served 78.38461538461539
      // renders as `78.4`): a 16-digit tag is unreadable stacked against its neighbours on a 288px
      // canvas. The exact served value is shown verbatim in the Bands table directly below the
      // chart — nothing is recomputed, and no other value is rounded (the price lines themselves
      // are drawn at the served band prices, unrounded).
      const score = Number(band.quality_score.toFixed(1));
      const title = `${sideLabel}${classLabel} · ${score}${band.round_number ? " · round" : ""}`;
      const edges =
        band.price_low === band.price_high
          ? [{ price: band.price_low, labelled: true }]
          : [
              { price: band.price_high, labelled: true },
              { price: band.price_low, labelled: false },
            ];
      for (const edge of edges) {
        priceLinesRef.current.push(
          series.createPriceLine({
            price: edge.price,
            color,
            lineWidth: 1,
            lineStyle: 0, // LineStyle.Solid — distinct from the dashed raw-level lines
            axisLabelVisible: edge.labelled,
            title: edge.labelled ? title : "",
          }),
        );
      }
    }
  }, [levels, bands, chartReady]);

  // --- Draw the cockpit's extra thesis-geometry price lines (clear-then-redraw) ------------------
  // Kept SEPARATE from the level/band lines (own handle ref) so redrawing one family never clobbers
  // the other. Attached to the live series (the tape bars own the price scale on the cockpit); the
  // prices/colors/widths are the served thesis geometry the page pre-built — drawn verbatim.
  useEffect(() => {
    const liveSeries = liveSeriesRef.current;
    if (!liveSeries) return;
    for (const line of extraPriceLinesRef.current) {
      try {
        liveSeries.removePriceLine(line);
      } catch {
        // The series may have been disposed between renders — ignore (it is being torn down).
      }
    }
    extraPriceLinesRef.current = [];
    for (const spec of extraPriceLines) {
      extraPriceLinesRef.current.push(
        liveSeries.createPriceLine({
          price: spec.price,
          color: spec.color,
          lineWidth: spec.lineWidth,
          lineStyle: spec.lineStyle,
          axisLabelVisible: spec.axisLabelVisible,
          title: spec.title,
        }),
      );
    }
  }, [extraPriceLines, chartReady]);

  // --- Draw the cockpit's tape-state + thesis markers on the live series (verbatim) --------------
  useEffect(() => {
    const primitive = liveMarkersRef.current;
    if (!primitive) return;
    const sorted = [...extraMarkers].sort((a, b) => a.time - b.time);
    primitive.setMarkers(
      sorted.map((m) => ({
        time: m.time as any,
        position: m.position,
        color: m.color,
        shape: m.shape,
        text: m.text,
      })),
    );
  }, [extraMarkers, chartReady]);

  // --- Apply the true-clock second-resolution axis toggle (cockpit only) ------------------------
  // This is what decides whether the library asks the tick formatter above for a `Time` or a
  // `TimeWithSeconds` tick, so it still governs the axis label's shape (`HH:mm` vs `HH:mm:ss`) —
  // the tape watches seconds, the recorded-bar charts do not.
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;
    chart.applyOptions({ timeScale: { secondsVisible: !!secondsVisible } });
  }, [secondsVisible, chartReady]);

  // --- The as-of / start boundary marker --------------------------------------------------------
  // `asOfTs` is the ts of the LAST drawn bar the level/band computation could see (the page picks
  // it as an ACTUAL bar time, never a between-bars instant, so it always lands on a real candle).
  // Candles to its right are LATER price action shown for context; the level/band lines themselves
  // remain computed strictly as of the query time (lookahead-free). Uses the SAME v5 series-marker
  // mechanism PriceChart.tsx uses. `asOfLabel` names it ("as-of" on /structure, "start" on the
  // cockpit, where the bars to its right are the live tape's own moving bars).
  useEffect(() => {
    const series = seriesRef.current;
    const lc = libRef.current;
    if (!series || !lc) return;
    const markers =
      asOfTs == null
        ? []
        : [
            {
              time: asOfTs as any,
              position: "aboveBar" as const,
              color: "#94a3b8", // slate-400 — the SAME neutral "declared reference" tone as the lines
              shape: "arrowDown" as const,
              text: asOfLabel,
            },
          ];
    if (markersRef.current) {
      markersRef.current.setMarkers(markers);
    } else {
      markersRef.current = lc.createSeriesMarkers(series, markers);
    }
  }, [asOfTs, asOfLabel, bars, chartReady]);

  const hasBars = drawableBars.length > 0 || drawableLiveBars.length > 0;

  return (
    <div className="relative">
      <div ref={containerRef} data-testid="structure-chart-canvas" className="h-72 w-full" />
      {!hasBars && !loadingMore && (
        <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
          <EmptyHint>No candles to draw for this timeframe.</EmptyHint>
        </div>
      )}
      {undrawableCount > 0 && (
        <p
          data-testid="structure-chart-undrawable-rows"
          className="mt-1 text-[11px] text-amber-300/80"
        >
          {undrawableCount} row(s) in this window carry no price and are not drawn.
        </p>
      )}
      {loadingMore && (
        <div
          data-testid="structure-chart-loading-more"
          className="pointer-events-none absolute left-2 top-2 z-10 rounded bg-slate-900/80 px-2 py-1 text-[11px] text-slate-400"
        >
          Loading bars…
        </div>
      )}
      {shapeCaption && (
        <div
          data-testid="structure-chart-shape-caption"
          className="pointer-events-none absolute left-2 top-9 z-10 rounded bg-slate-900/80 px-2 py-1 text-[11px] text-amber-200"
        >
          {shapeCaption}
        </div>
      )}
      {shapeClipped && (
        <p data-testid="structure-chart-shape-clipped" className="mt-1 text-[11px] text-amber-300/80">
          Part of this setup falls outside the loaded candle window — scroll left to load more bars.
        </p>
      )}
    </div>
  );
}
