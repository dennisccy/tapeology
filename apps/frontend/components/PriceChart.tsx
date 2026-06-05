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
import {
  HISTORY_BAR_SIZES,
  type HistoryBarSize,
  type TapeHistory,
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

export function PriceChart({ ticker }: { ticker: string | null }) {
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
        timeScale: { borderColor: "#1e293b", timeVisible: true, secondsVisible: true },
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

    // Candles VERBATIM from the engine buffer (no re-binning). Logical-second bin starts are
    // whole multiples of the bar size; coerce to integer for the library's time scale and keep
    // ascending order (the backend already returns them sorted + unique per bar).
    const candles = history.bars.map((b) => ({
      time: Math.round(b.time) as any,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));
    series.setData(candles);

    // Markers VERBATIM from the engine buffer (the marker's own state/confidence — no
    // re-derivation). One marker per meaningful transition, colored by state.
    if (markersRef.current && createMarkersRef.current) {
      const markers = history.markers.map((m) => ({
        time: Math.round(m.time) as any,
        position: "aboveBar" as const,
        color: MARKER_COLORS[m.state] ?? "#fbbf24",
        shape: "arrowDown" as const,
        text: STATE_LABELS[m.state] ?? m.state,
      }));
      markersRef.current.setMarkers(markers);
    }

    if (chartRef.current && candles.length > 0) {
      chartRef.current.timeScale().fitContent();
    }
  }, [history]);

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
