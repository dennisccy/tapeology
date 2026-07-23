import type { BarSeriesRecord } from "./types";

// Shared bar-series timeframe helpers, used by BOTH the /structure Tradable Map chart and the
// cockpit chart (app/page.tsx's PriceChart). Pure reads over already-served bar-series metadata —
// they select among existing rows and never compute a new price/level/zone value. Lifted verbatim
// out of app/structure/page.tsx so the two pages share one copy (no second TIMEFRAME_ORDER literal).

// The canonical bar-store timeframe order (mirrors apps/backend/app/config.py's `bar_timeframes`
// tuple), shortest → longest. Used to (a) order the viewing-timeframe <select>'s options and (b)
// pick the fallback series when the user's chosen timeframe isn't recorded (shortest wins). A single
// candlestick chart cannot honestly overlay two timeframes' OHLC at once, so exactly one series is
// drawn. This is a DISPLAY CHOICE over already-served records — it selects among existing rows,
// computing no new price/level/zone value.
export const TIMEFRAME_ORDER = ["1m", "5m", "15m", "1h", "4h", "8h", "1d", "1w", "1mo"];

export function pickRepresentativeSeries(
  seriesForSymbol: BarSeriesRecord[],
): BarSeriesRecord | null {
  if (seriesForSymbol.length === 0) return null;
  const ranked = [...seriesForSymbol].sort((a, b) => {
    const rankA = TIMEFRAME_ORDER.indexOf(a.timeframe);
    const rankB = TIMEFRAME_ORDER.indexOf(b.timeframe);
    const safeA = rankA === -1 ? TIMEFRAME_ORDER.length : rankA;
    const safeB = rankB === -1 ? TIMEFRAME_ORDER.length : rankB;
    if (safeA !== safeB) return safeA - safeB;
    // Same timeframe (or same unrecognized rank): most-recently-created wins — mirrors the
    // backend's OWN tie-break for the identical (symbol, timeframe) case
    // (research/levels.py's `_select_one_series_per_timeframe`), so the chart's chosen series is
    // never in tension with which series the levels computation itself read for that timeframe.
    return b.created_utc.localeCompare(a.created_utc);
  });
  return ranked[0];
}

// The distinct timeframes actually recorded for a symbol, ordered shortest-first by TIMEFRAME_ORDER
// (any unrecognized timeframe appended alphabetically). Drives the viewing-timeframe <select>'s
// options; index 0 is the shortest recorded timeframe (the fallback default when "1d" isn't
// recorded). A pure read over already-served rows — never a recomputation.
export function timeframesInOrder(series: BarSeriesRecord[]): string[] {
  const present = new Set(series.map((s) => s.timeframe));
  const known = TIMEFRAME_ORDER.filter((tf) => present.has(tf));
  const unknown = [...present].filter((tf) => !TIMEFRAME_ORDER.includes(tf)).sort();
  return [...known, ...unknown];
}

// The ts (epoch seconds) of the last bar the as-of computation could see — max ts among bars with
// `ts * 1000 <= asOfEpochMs`. This is the candle the "as-of" chart marker anchors to (always a real
// drawn bar, never a between-bars instant). Returns undefined when as-of predates every bar, the
// epoch is NaN, or there are no bars. Order-independent (correct on a non-ascending array).
export function boundaryTs(
  bars: { ts: number }[] | undefined,
  asOfEpochMs: number,
): number | undefined {
  if (!bars || Number.isNaN(asOfEpochMs)) return undefined;
  let best: number | undefined;
  for (const b of bars) {
    if (b.ts * 1000 <= asOfEpochMs && (best === undefined || b.ts > best)) best = b.ts;
  }
  return best;
}
