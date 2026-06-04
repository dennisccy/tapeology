"use client";

import { useEffect, useState } from "react";
import { getMarketClock } from "@/lib/api";
import { formatMarketTime } from "@/lib/datetime";
import type { MarketClock } from "@/lib/types";

// Poll cadence for the Live market-status indicator. Session status changes slowly, so a calm
// 60s cadence is plenty. A named constant (mirrors TopBar's REPLAY_SPEEDS / api WS_PUSH_INTERVAL)
// — not an inline literal.
const POLL_INTERVAL_MS = 60_000;

type IndicatorSpec = {
  dotClass: string;
  textClass: string;
  label: string;
  detail?: string;
  title: string;
};

// Map the canonical row-8 clock onto the load-bearing color semantics: emerald = open,
// amber = closed / next-open / unavailable, slate = pre-first-fetch placeholder. This is a pure
// READ of GET /market/clock — open/closed is never recomputed here.
function indicatorSpec(clock: MarketClock | null): IndicatorSpec {
  if (clock === null) {
    // Before the first fetch resolves: a calm placeholder, never a fabricated "open".
    return {
      dotClass: "bg-slate-600",
      textClass: "text-slate-400",
      label: "…",
      title: "Checking market status…",
    };
  }
  if (!clock.available) {
    return {
      dotClass: "bg-amber-400",
      textClass: "text-amber-400",
      label: "unavailable",
      title: "Live market status needs vendor credentials (not configured)",
    };
  }
  if (clock.is_open) {
    return {
      dotClass: "bg-emerald-400",
      textClass: "text-emerald-400",
      label: "open",
      title: "The US market is open",
    };
  }
  return {
    dotClass: "bg-amber-400",
    textClass: "text-amber-400",
    label: "closed",
    detail: clock.next_open ? `next open ${formatMarketTime(clock.next_open)}` : undefined,
    title: "The US market is closed",
  };
}

// The Live market-status indicator (data-contract row 8). Fetches GET /market/clock on mount and
// on a fixed interval, and renders the REAL session status — open / closed (+ next open) /
// unavailable. This component is mounted ONLY while mode === "live" (TopBar conditional render),
// so its poll is torn down on unmount / mode-change (iter-0 resource-leak lesson) by the effect
// cleanup that clears the interval and ignores any in-flight response.
export function MarketStatusIndicator() {
  const [clock, setClock] = useState<MarketClock | null>(null);

  useEffect(() => {
    let active = true;
    async function poll() {
      const next = await getMarketClock();
      if (active) setClock(next);
    }
    poll();
    const id = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  const spec = indicatorSpec(clock);
  return (
    <div
      className={`flex items-center gap-1.5 rounded bg-slate-800 px-2 py-1 text-xs ${spec.textClass}`}
      title={spec.title}
    >
      <span className={`inline-block h-2 w-2 rounded-full ${spec.dotClass}`} />
      <span>market</span>
      <span className="font-mono">{spec.label}</span>
      {spec.detail && <span className="font-mono text-slate-400">— {spec.detail}</span>}
    </div>
  );
}
