"use client";

import { useEffect, useRef } from "react";
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
export function StructureChart({
  bars,
  levels,
  bands = [],
}: {
  bars: BarRow[];
  levels: SrLevel[];
  bands?: TradabilityBand[];
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    let disposed = false;
    // Typed loosely: the module is loaded dynamically (client-only, matching PriceChart.tsx) and
    // its types are never imported at module scope.
    let chart: any = null;

    (async () => {
      const lc = await import("lightweight-charts");
      if (disposed || !containerRef.current) return;

      chart = lc.createChart(containerRef.current, {
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

      // Candles VERBATIM from the recorded series. `ts` is already a real UTC-epoch-seconds value
      // (the bar store's own field — see research/bars.py's `_bar_to_row`), so — unlike
      // PriceChart.tsx's logical-time-to-epoch mapping — no anchor offset is needed here.
      const candles = bars.map((b) => ({
        time: b.ts as any,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      }));
      series.setData(candles);

      // One dashed price line per level — the declared-reference-line convention PriceChart.tsx
      // already established for thesis geometry. Price/timeframe/type are read verbatim; drawn
      // regardless of whether the price falls inside the charted series' visible range (a level
      // can be sourced from a longer-window timeframe than the one charted).
      for (const level of levels) {
        series.createPriceLine({
          price: level.price,
          color: "#94a3b8", // slate-400 — the SAME neutral "declared reference" color PriceChart uses
          lineWidth: 1,
          lineStyle: 2, // LineStyle.Dashed
          axisLabelVisible: true,
          title: `${level.timeframe} ${level.type}`,
        });
      }

      // era-5B J-05: one SOLID price line per tradable-band edge (visually distinct from the
      // dashed raw-level lines above), colored by side — the SAME up/down palette the candle
      // series itself uses, so resistance/support read as one visual family with the candles.
      // price_low/price_high/side/class/quality_score/round_number are read verbatim off the
      // prop; this component performs no scoring or clustering of its own. A single-price band
      // (price_low === price_high) draws one line, never a duplicate.
      for (const band of bands) {
        const color = band.side === "resistance" ? "#fb7185" : "#34d399"; // rose-400 / emerald-400
        const sideLabel = band.side === "resistance" ? "R" : "S";
        const classLabel = band.class ? ` class ${band.class}` : "";
        const title = `${sideLabel}${classLabel} · score ${band.quality_score}${band.round_number ? " · round" : ""}`;
        const edges =
          band.price_low === band.price_high ? [band.price_low] : [band.price_low, band.price_high];
        for (const price of edges) {
          series.createPriceLine({
            price,
            color,
            lineWidth: 2,
            lineStyle: 0, // LineStyle.Solid — distinct from the dashed raw-level lines
            axisLabelVisible: true,
            title,
          });
        }
      }

      if (candles.length > 0) chart.timeScale().fitContent();
    })();

    return () => {
      disposed = true;
      if (chart) chart.remove();
    };
  }, [bars, levels, bands]);

  const hasBars = bars.length > 0;

  return (
    <div className="relative">
      <div ref={containerRef} data-testid="structure-chart-canvas" className="h-72 w-full" />
      {!hasBars && (
        <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
          <EmptyHint>No candles to draw at this as-of time.</EmptyHint>
        </div>
      )}
    </div>
  );
}
