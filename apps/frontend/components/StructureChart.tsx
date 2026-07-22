"use client";

import { useEffect, useRef, useState } from "react";
import type { BarRow, SrLevel, TradabilityBand } from "@/lib/types";
import { EmptyHint } from "./Panel";

// The /structure page's price chart (J-01): candles from ONE representative recorded bar series
// (the page picks it — see `pickRepresentativeSeries` in app/structure/page.tsx) plus one dashed
// price line per S/R level, labelled by its OWN timeframe + type. Every candle and every level's
// price/timeframe/type is read VERBATIM from the props (already fetched by the page) — this
// component computes nothing; it only draws.
//
// Follows PriceChart.tsx's PATTERN (client-only dynamic `lightweight-charts` import, dark chart
// options, dashed declared-reference price lines) but is a fresh, purpose-built component:
// PriceChart.tsx polls the tape engine's `/tape/{ticker}/history` (logical-second candles + live
// tape-state markers); this component renders ONE already-fetched query result from
// `/research/bars` (real UTC-epoch-seconds candles, no polling, no markers).
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

export function StructureChart({
  bars,
  levels,
  bands = [],
  asOfTs,
  onNeedOlder,
  onNeedNewer,
  loadingMore = false,
}: {
  bars: BarRow[];
  levels: SrLevel[];
  bands?: TradabilityBand[];
  asOfTs?: number;
  onNeedOlder?: (count: number, opts?: { fill?: boolean }) => void;
  onNeedNewer?: (count: number, opts?: { fill?: boolean }) => void;
  loadingMore?: boolean;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
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
        rightPriceScale: { borderColor: "#1e293b" },
        timeScale: { borderColor: "#1e293b", timeVisible: true, secondsVisible: false },
        crosshair: { mode: lc.CrosshairMode.Normal },
      });
      const series = chart.addSeries(lc.CandlestickSeries, {
        upColor: "#34d399", // emerald-400
        downColor: "#fb7185", // rose-400
        wickUpColor: "#34d399",
        wickDownColor: "#fb7185",
        borderVisible: false,
      });

      chartRef.current = chart;
      seriesRef.current = series;
      libRef.current = lc;

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
        markersRef.current = null;
        priceLinesRef.current = [];
        drawnRef.current = false;
        drawnBarsRef.current = [];
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
    const candles = bars.map((b) => ({
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
    drawnBarsRef.current = bars;

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
      const asOfIndex = asOfTs === undefined ? -1 : bars.findIndex((b) => b.ts === asOfTs);
      const to =
        asOfIndex >= 0
          ? Math.min(candles.length, asOfIndex + Math.round(viewport * (1 - AS_OF_VIEWPORT_SHARE)))
          : candles.length;
      chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, to - viewport), to });
    } else if (anchor && visibleRange) {
      const newIndex = bars.findIndex((b) => b.ts === anchor.ts);
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
  }, [bars, asOfTs, chartReady]);

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

  // --- The as-of boundary marker ----------------------------------------------------------------
  // `asOfTs` is the ts of the LAST drawn bar the level/band computation could see (the page picks
  // it as an ACTUAL bar time, never a between-bars instant, so it always lands on a real candle).
  // Candles to its right are LATER price action shown for context; the level/band lines themselves
  // remain computed strictly as of the query time (lookahead-free). Uses the SAME v5 series-marker
  // mechanism PriceChart.tsx uses.
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
              text: "as-of",
            },
          ];
    if (markersRef.current) {
      markersRef.current.setMarkers(markers);
    } else {
      markersRef.current = lc.createSeriesMarkers(series, markers);
    }
  }, [asOfTs, bars, chartReady]);

  const hasBars = bars.length > 0;

  return (
    <div className="relative">
      <div ref={containerRef} data-testid="structure-chart-canvas" className="h-72 w-full" />
      {!hasBars && !loadingMore && (
        <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
          <EmptyHint>No candles to draw for this timeframe.</EmptyHint>
        </div>
      )}
      {loadingMore && (
        <div
          data-testid="structure-chart-loading-more"
          className="pointer-events-none absolute left-2 top-2 z-10 rounded bg-slate-900/80 px-2 py-1 text-[11px] text-slate-400"
        >
          Loading bars…
        </div>
      )}
    </div>
  );
}
