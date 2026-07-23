"use client";

import { useEffect, useState } from "react";
import { fetchTradability } from "./api";
import type { TradabilityResponse } from "./types";

// The ONE shared tradable-map read (GET /research/tradability), used by BOTH surfaces that draw
// the band overlay — the /structure Tradable Map (app/structure/page.tsx, form-driven) and the
// cockpit price chart (components/PriceChart.tsx, watch-anchor-driven). Lifted out of both so a
// future enhancement to how the map is fetched lands ONCE; the backend side of that principle
// already holds (one route, one durable tradability cache, one vectorized computation).
//
// Invariants (moved here verbatim from the two per-surface effects this replaces; pinned by
// apps/backend/tests/test_price_chart_confluence.py's source-inspection tests):
//
//   * VALUE-KEYED, never polled: the fetch effect re-runs only when (symbol, asOfIso, reloadSeq)
//     actually changes — the cockpit's 1s history poll and its transient view-switch resets never
//     reach this hook, because the caller passes a LATCHED, per-watch-stable anchor.
//   * DEFERRED until the moment is known, never a wall-clock fallback: `asOfIso == null` with a
//     symbol set issues NO request and reports `loading` (not `idle`, so ready-only empty-state
//     logic downstream never fires prematurely). There is no `new Date()`-"now" anywhere in this
//     hook — a historical replay must resolve THAT session's own basis, and the sub-second window
//     before the caller's anchor resolves must simply wait, not ask about today.
//   * ZERO client-side session math (no-lookahead): this hook only forwards WHICH moment to
//     resolve; `_resolve_basis` (apps/backend/app/research/tradability.py) alone decides the
//     prior session server-side.
//   * `reloadSeq` forces a refetch for the SAME (symbol, asOfIso) when the caller knows the
//     store changed underneath it — /structure bumps it per Load click so a re-Load after
//     "Fetch from Yahoo Finance" serves the newly recorded bars' map, never a stale read. The
//     cockpit passes the default (its store cannot change mid-watch).
//
// Error carries the backend's own detail verbatim (the /structure UnavailablePanel renders it);
// `data: null` on every non-ready phase so a caller can never draw a stale/fabricated map.
export function useTradability(
  symbol: string | null,
  asOfIso: string | null,
  reloadSeq: number = 0,
): {
  phase: "idle" | "loading" | "ready" | "error";
  data: TradabilityResponse | null;
  error: string | null;
} {
  const [state, setState] = useState<{
    phase: "idle" | "loading" | "ready" | "error";
    data: TradabilityResponse | null;
    error: string | null;
  }>({ phase: "idle", data: null, error: null });

  useEffect(() => {
    if (symbol == null) {
      setState({ phase: "idle", data: null, error: null });
      return;
    }
    if (asOfIso == null) {
      // The caller has not resolved WHICH moment to ask about yet — defer entirely (no request),
      // and report loading so downstream ready-only logic stays quiet. Never a wall-clock "now".
      setState({ phase: "loading", data: null, error: null });
      return;
    }
    let alive = true;
    setState({ phase: "loading", data: null, error: null });
    fetchTradability(symbol, asOfIso).then((result) => {
      if (!alive) return;
      setState(
        result.ok && result.data
          ? { phase: "ready", data: result.data, error: null }
          : {
              phase: "error",
              data: null,
              error: result.error ?? "The tradable map could not be loaded.",
            },
      );
    });
    return () => {
      alive = false;
    };
  }, [symbol, asOfIso, reloadSeq]);

  return state;
}
