"use client";

import { useEffect, useState } from "react";
import { fetchBarSeriesList } from "./api";
import type { BarSeriesRecord } from "./types";

// The ONE shared recorded-bar-series METADATA read (GET /research/bars?symbol=&include_bars=false),
// used by both surfaces that offer a timeframe selector over a symbol's recordings — the
// /structure charts and the cockpit price chart's History group. Metadata only (`bars` omitted;
// the /structure paging precedent): each record's identity/timeframe/bar_count drives display
// choices, while candles themselves arrive one viewport at a time through `useBarWindow`.
//
// Same contract as `useTradability` (the sibling shared read this pattern mirrors): value-keyed
// on (symbol, reloadSeq) — never polled; `symbol == null` clears to `idle`; `reloadSeq` lets a
// caller force a refetch for the SAME symbol after it knows new series were recorded (/structure
// bumps it per Load click; the cockpit passes the default).
export function useRecordedSeries(
  symbol: string | null,
  reloadSeq: number = 0,
): {
  phase: "idle" | "loading" | "ready" | "error";
  series: BarSeriesRecord[];
  error: string | null;
} {
  const [state, setState] = useState<{
    phase: "idle" | "loading" | "ready" | "error";
    series: BarSeriesRecord[];
    error: string | null;
  }>({ phase: "idle", series: [], error: null });

  useEffect(() => {
    if (symbol == null) {
      setState({ phase: "idle", series: [], error: null });
      return;
    }
    let alive = true;
    setState({ phase: "loading", series: [], error: null });
    fetchBarSeriesList({ symbol, includeBars: false }).then((result) => {
      if (!alive) return;
      setState(
        result.ok && result.data
          ? { phase: "ready", series: result.data.bar_series, error: null }
          : {
              phase: "error",
              series: [],
              error: result.error ?? "The bar series list could not be loaded.",
            },
      );
    });
    return () => {
      alive = false;
    };
  }, [symbol, reloadSeq]);

  return state;
}
