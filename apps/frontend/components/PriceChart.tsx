"use client";

// Tape-state prediction chart (J-17 / J-18): a candlestick chart of the watched price with
// markers at meaningful tape-state transitions, plus a 10 / 30 / 60 s bar-size selector.
//
// Single source of truth (one focused chart, computed once): every candle and marker is read
// VERBATIM from GET /tape/{ticker}/history — this component re-bins NO candles and re-derives NO
// marker state/side/price. It polls `…/history` on the stream cadence (it does NOT open a second
// WebSocket). An empty / not-yet-warmed window shows an empty treatment — never invented candles.
//
// The chart library (lightweight-charts) is client-only: it is imported dynamically INSIDE an
// effect so it never runs during server render (no SSR), and adds no backend dependency. It is
// candlestick + markers only — no indicators, studies, drawing tools, or any order/execution
// affordance (Stay-in-scope / No-execution anti-goals).

import { useEffect, useRef, useState } from "react";
import { fetchHistory } from "@/lib/api";
import { formatDateTimeDMY } from "@/lib/datetime";
import {
  HISTORY_BAR_SIZES,
  type HistoryBarSize,
  type TapeHistory,
  type ThesisGeometry,
  type ThesisProjection,
} from "@/lib/types";
import { Panel, EmptyHint } from "./Panel";

// How often we re-pull `…/history` while a ticker is watched — matches the cockpit's WS push
// cadence so the chart accrues new candles in step with the rest of the cockpit (no 2nd socket).
const POLL_INTERVAL_MS = 1000;

// Marker color by tape state — the SAME load-bearing semantics as the rest of the cockpit
// (emerald = buyer_control, rose = seller_control, amber = absorption). `unclear` is never marked
// by the backend, so it has no entry here. Hex values mirror the DESIGN SYSTEM Tailwind tokens
// (emerald-400 / rose-400 / amber-400) because the charting canvas takes raw colors, not classes.
const MARKER_COLORS: Record<string, string> = {
  buyer_control: "#34d399", // emerald-400
  seller_control: "#fb7185", // rose-400
  bid_absorption: "#fbbf24", // amber-400
  ask_absorption: "#fbbf24", // amber-400
};

const STATE_LABELS: Record<string, string> = {
  buyer_control: "Buyer Control",
  seller_control: "Seller Control",
  bid_absorption: "Bid Absorption",
  ask_absorption: "Ask Absorption",
};

// Thesis-geometry colors (J-48), reusing the established verdict/side semantics so the chart, the
// thesis strip, and the timeline all speak the same color language. Verdict markers: confirming
// emerald, weakening amber, rejecting/invalidated rose, pending slate (the design-direction verdict
// palette). The invalidation price-line is rose (the idea is dead beyond it); the level line is
// slate (a neutral reference). Hex values mirror the DESIGN SYSTEM Tailwind tokens because the
// charting canvas takes raw colors, not classes.
const VERDICT_COLORS: Record<string, string> = {
  confirming: "#34d399", // emerald-400
  weakening: "#fbbf24", // amber-400
  rejecting: "#fb7185", // rose-400
  invalidated: "#fb7185", // rose-400
  pending: "#94a3b8", // slate-400
  expired: "#94a3b8", // slate-400
};
const PRICE_LINE_COLORS: Record<string, string> = {
  invalidation: "#fb7185", // rose-400 — the idea is invalidated beyond this price
  level: "#94a3b8", // slate-400 — a neutral declared reference
};
// Entry/exit marks render in their own slate-200 treatment, distinct from the verdict palette.
const MARK_COLOR = "#e2e8f0"; // slate-200

export function PriceChart({
  ticker,
  thesis,
}: {
  ticker: string | null;
  // The live thesis projection (WS `thesis` key) or null. Read VERBATIM for its `geometry`; the
  // chart derives nothing. `null` (no/cleared/resolved-non-invalidated thesis) => no overlay.
  thesis?: ThesisProjection | null;
}) {
  const [barSize, setBarSize] = useState<HistoryBarSize>(HISTORY_BAR_SIZES[0]);
  const [history, setHistory] = useState<TapeHistory | null>(null);
  // `loaded` distinguishes "haven't fetched yet" (connecting) from "fetched, genuinely empty"
  // (an empty window) so the empty treatment reads honestly in both cases.
  const [loaded, setLoaded] = useState(false);

  const containerRef = useRef<HTMLDivElement | null>(null);
  // Library object handles kept across renders; typed loosely because the module is loaded
  // dynamically (client-only) and we never import its types at module scope.
  const chartRef = useRef<any>(null);
  const seriesRef = useRef<any>(null);
  const markersRef = useRef<any>(null);
  const createMarkersRef = useRef<any>(null);
  // The thesis price-line handles currently attached to the series (J-48). Tracked so each geometry
  // update REMOVES the prior lines before adding the new ones (no stale/duplicate lines) and so a
  // cleared/resolved thesis removes them entirely.
  const priceLinesRef = useRef<any[]>([]);
  // The latest tape-state markers (engine-owned) and thesis markers (research-owned). They share the
  // ONE series-marker primitive, so both effects funnel through `setCombinedMarkers` which sets the
  // union in a single call (lightweight-charts' setMarkers replaces the whole set).
  const stateMarkersRef = useRef<any[]>([]);
  const thesisMarkersRef = useRef<any[]>([]);

  // Set the union of engine tape-state markers + thesis-geometry markers in one call (they share the
  // single series-marker mechanism; markers must be sorted ascending by time for the library).
  function setCombinedMarkers() {
    if (!markersRef.current) return;
    const all = [...stateMarkersRef.current, ...thesisMarkersRef.current].sort(
      (a, b) => a.time - b.time,
    );
    markersRef.current.setMarkers(all);
  }

  // --- Poll …/history verbatim while a ticker is watched (reset on ticker/bar change) -------
  useEffect(() => {
    if (!ticker) {
      setHistory(null);
      setLoaded(false);
      return;
    }
    let cancelled = false;
    setHistory(null);
    setLoaded(false);

    async function pull() {
      const data = await fetchHistory(ticker as string, barSize);
      if (cancelled) return;
      setHistory(data);
      setLoaded(true);
    }
    pull();
    const id = setInterval(pull, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [ticker, barSize]);

  // --- Create the chart once (client-only dynamic import, never at SSR) ---------------------
  useEffect(() => {
    if (!ticker) return;
    let disposed = false;

    (async () => {
      const lc = await import("lightweight-charts");
      if (disposed || !containerRef.current) return;

      const chart = lc.createChart(containerRef.current, {
        autoSize: true,
        layout: {
          // Match the dark instrument-panel surface so it does not read as a bright widget.
          background: { type: lc.ColorType.Solid, color: "#020617" }, // slate-950
          textColor: "#94a3b8", // slate-400
          fontFamily:
            "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        },
        grid: {
          vertLines: { color: "#1e293b" }, // slate-800
          horzLines: { color: "#1e293b" },
        },
        rightPriceScale: { borderColor: "#1e293b" },
        timeScale: {
          borderColor: "#1e293b",
          timeVisible: true,
          secondsVisible: true,
          // TRUE clock time on the axis (J-31): each candle's `time` is a real UTC epoch
          // (anchor + logical_ts, see the data effect), and this formatter renders the axis ticks
          // as `dd-MM-yyyy HH:mm:ss` in the operator's LOCAL zone via the ONE shared formatter
          // (J-35) — never an elapsed 0…600 s counter. lightweight-charts passes UTCTimestamp
          // SECONDS, so multiply to ms for the Date-based formatter.
          tickMarkFormatter: (time: number) => formatDateTimeDMY(time * 1000),
        },
        // The crosshair tooltip time, also TRUE clock time via the shared `dd-MM-yyyy HH:mm:ss`
        // formatter (J-31 / J-35) — consistent with the axis ticks.
        localization: {
          timeFormatter: (time: number) => formatDateTimeDMY(time * 1000),
        },
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
      createMarkersRef.current = lc.createSeriesMarkers;
      markersRef.current = lc.createSeriesMarkers(series, []);
    })();

    return () => {
      disposed = true;
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
        seriesRef.current = null;
        markersRef.current = null;
      }
    };
  }, [ticker]);

  // --- Feed the verbatim candles + markers into the chart whenever data changes -------------
  useEffect(() => {
    const series = seriesRef.current;
    if (!series || !history) return;

    // TRUE clock time (J-31): map each LOGICAL bin/marker time to a real UTC-epoch SECONDS value
    // as `epoch_anchor + logical_ts` — a pure ADDITIVE display offset (the chart recomputes NO
    // price/side/state; the engine's logical timeline + classification are unchanged). The anchor
    // is real market epoch for historical and the synthetic session-start for simulated. When the
    // backend has no anchor (an empty/anchorless window) we fall back to the logical seconds — the
    // chart is empty in that case anyway, so no fabricated timestamp is shown.
    const anchor = history.epoch_anchor ?? 0;
    const toClock = (logical: number) => Math.round(anchor + logical);

    // Candles VERBATIM from the engine buffer (no re-binning). Logical-second bin starts are
    // whole multiples of the bar size; map to the true-clock epoch and keep ascending order
    // (the backend already returns them sorted + unique per bar).
    const candles = history.bars.map((b) => ({
      time: toClock(b.time) as any,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));
    series.setData(candles);

    // Markers VERBATIM from the engine buffer (the marker's own state/confidence — no
    // re-derivation). One marker per meaningful transition, colored by state, stamped at true
    // clock time so it aligns with the candle under it. Tape-state markers sit ABOVE the bar with a
    // down-arrow — kept visually distinct from the thesis markers (which sit BELOW the bar), so the
    // two registered marker owners never read as one layer (J-48).
    if (markersRef.current && createMarkersRef.current) {
      stateMarkersRef.current = history.markers.map((m) => ({
        time: toClock(m.time) as any,
        position: "aboveBar" as const,
        color: MARKER_COLORS[m.state] ?? "#fbbf24",
        shape: "arrowDown" as const,
        text: STATE_LABELS[m.state] ?? m.state,
      }));
      setCombinedMarkers();
    }

    if (chartRef.current && candles.length > 0) {
      chartRef.current.timeScale().fitContent();
    }
  }, [history]);

  // --- Draw the thesis geometry VERBATIM (J-48): price-lines + thesis markers ---------------------
  // Reads the served `geometry` (declared prices + the append-only timeline + the marks, computed
  // once server-side) and draws it on the SAME epoch anchor the candles use (`anchor + logical_ts`).
  // The chart derives NO price/side/state/time of its own. With `thesis: null` (or no geometry) it
  // removes every line and clears the thesis-marker layer — exactly the no-thesis render (J-68/J-17).
  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;
    const geometry: ThesisGeometry | undefined = thesis?.geometry;

    // Always clear prior price-lines first so an update never leaves a stale/duplicate line and a
    // cleared/resolved thesis removes them entirely.
    for (const line of priceLinesRef.current) {
      try {
        series.removePriceLine(line);
      } catch {
        // The series may have been disposed between renders — ignore (it is being torn down).
      }
    }
    priceLinesRef.current = [];

    if (!geometry) {
      // No thesis => no overlay. Clear the thesis-marker layer and re-set the combined markers so
      // only the engine tape-state markers remain (the exact no-thesis render).
      thesisMarkersRef.current = [];
      setCombinedMarkers();
      return;
    }

    // Price-lines (time-independent) — invalidation always; level only when served. Each labeled
    // with the backend-owned copy, rendered verbatim. Dashed so they read as declared reference
    // lines, not data.
    for (const pl of geometry.price_lines) {
      const handle = series.createPriceLine({
        price: pl.price,
        color: PRICE_LINE_COLORS[pl.kind] ?? "#94a3b8",
        lineWidth: 1,
        lineStyle: 2, // LineStyle.Dashed
        axisLabelVisible: true,
        title: pl.label,
      });
      priceLinesRef.current.push(handle);
    }

    // Thesis markers — visually DISTINCT from tape-state markers: they sit BELOW the bar (vs above)
    // and use a circle (verdict / first-confirmation) or arrow-up (entry/exit) shape (vs the
    // tape-state down-arrow). x-placement uses the SAME epoch anchor as the candles.
    const anchor = history?.epoch_anchor ?? 0;
    const toClock = (logical: number) => Math.round(anchor + logical);
    thesisMarkersRef.current = geometry.markers.map((m) => {
      if (m.kind === "entry" || m.kind === "exit") {
        // The user's own action mark — its own slate treatment with the verbatim mono price.
        const priceText = m.price != null ? ` ${m.price.toFixed(2)}` : "";
        return {
          time: toClock(m.logical_ts) as any,
          position: "belowBar" as const,
          color: MARK_COLOR,
          shape: "arrowUp" as const,
          text: `${m.label}${priceText}`,
        };
      }
      // A verdict-transition marker or the first-confirmation marker — verdict palette, circle shape.
      const color =
        m.kind === "first_confirmation"
          ? VERDICT_COLORS.confirming
          : VERDICT_COLORS[m.verdict ?? "pending"] ?? "#94a3b8";
      return {
        time: toClock(m.logical_ts) as any,
        position: "belowBar" as const,
        color,
        shape: "circle" as const,
        text: m.label,
      };
    });
    setCombinedMarkers();
  }, [thesis, history]);

  if (!ticker) return null;

  const hasBars = !!history && history.bars.length > 0;

  return (
    <Panel title="Price Chart — Tape-State Markers" className="mb-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-xs text-slate-500">Bar size</span>
        <div className="flex gap-1" role="group" aria-label="Bar size">
          {HISTORY_BAR_SIZES.map((size) => {
            const selected = size === barSize;
            return (
              <button
                key={size}
                type="button"
                onClick={() => setBarSize(size)}
                aria-pressed={selected}
                className={
                  "rounded border px-2.5 py-1 font-mono text-xs transition-colors " +
                  (selected
                    ? "border-slate-600 bg-slate-700 text-slate-100"
                    : "border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700 hover:text-slate-200 focus:border-slate-600 focus:text-slate-200 active:bg-slate-800")
                }
              >
                {size}s
              </button>
            );
          })}
        </div>
      </div>

      {/* The chart canvas. The container is always mounted so the library can attach; the empty
          treatment overlays it before any candle exists (never placeholder candles). */}
      <div className="relative">
        <div ref={containerRef} className="h-64 w-full" />
        {!hasBars && (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <EmptyHint>
              {loaded ? "No price history for this window yet" : "Loading price history…"}
            </EmptyHint>
          </div>
        )}
      </div>
    </Panel>
  );
}
