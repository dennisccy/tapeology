import { API_BASE } from "./config";
import type {
  MarketClock,
  SymbolMatch,
  TapeHistory,
  TapeSnapshot,
  WatchParams,
} from "./types";

export interface WatchResult {
  ok: boolean;
  scenario?: string;
  error?: string;
  // The distinct honest failure `reason` when the backend refused a real-mode watch (row 9):
  // "provider_unavailable" | "symbol_not_tradable" | "no_data_for_window" | "market_closed" (or
  // another reason string). The UI renders a distinct non-cockpit panel per reason — never a
  // fabricated cockpit, never a silent fall-back to Simulated.
  reason?: string;
  // The next market open (ISO-8601 UTC) carried by a "market_closed" refusal, so the honest
  // closed-market panel can show when the market reopens. Absent for the other reasons.
  nextOpen?: string;
}

export interface StopResult {
  ok: boolean;
  error?: string;
}

// POST /watch/{ticker}. Simulated mode sends NO body (byte-for-byte the prior request, so the
// sim path is unchanged); Live / Historical send the mode + params. An unknown / non-sim ticker
// returns an explicit error and a real mode with no credentials returns 503 (no fabrication).
export async function watchTicker(
  ticker: string,
  params?: WatchParams,
): Promise<WatchResult> {
  try {
    const init: RequestInit = { method: "POST" };
    // Only attach a JSON body for the real modes; Simulated stays a bodyless POST.
    if (params && params.mode !== "sim") {
      init.headers = { "Content-Type": "application/json" };
      init.body = JSON.stringify(params);
    }
    const res = await fetch(`${API_BASE}/watch/${encodeURIComponent(ticker)}`, init);
    if (res.ok) {
      const data = await res.json();
      return { ok: true, scenario: data.scenario };
    }
    let error = `'${ticker}' could not be watched`;
    let reason: string | undefined;
    let nextOpen: string | undefined;
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") error = data.detail;
      if (typeof data?.reason === "string") reason = data.reason;
      if (typeof data?.next_open === "string") nextOpen = data.next_open;
    } catch {
      /* keep default */
    }
    return { ok: false, error, reason, nextOpen };
  } catch {
    return { ok: false, error: "Backend unreachable — is the API running?" };
  }
}

// GET /market/clock (data-contract row 8) — the real market session status for the Live
// market-status indicator. Read verbatim (the UI never recomputes open/closed). Any failure or
// a non-OK response yields an explicit `available:false` (the indicator shows "unavailable"),
// never a fabricated open/closed status.
export async function getMarketClock(): Promise<MarketClock> {
  const unavailable: MarketClock = {
    available: false,
    is_open: null,
    next_open: null,
    next_close: null,
  };
  try {
    const res = await fetch(`${API_BASE}/market/clock`);
    if (!res.ok) return unavailable;
    const data = await res.json();
    return {
      available: !!data.available,
      is_open: typeof data.is_open === "boolean" ? data.is_open : null,
      next_open: typeof data.next_open === "string" ? data.next_open : null,
      next_close: typeof data.next_close === "string" ? data.next_close : null,
    };
  } catch {
    return unavailable;
  }
}

// GET /symbols/search?q= — real tradable suggestions for the search box (J-13). Any failure or
// empty/short query yields an empty list (free-text watch entry always remains possible); the
// UI renders these verbatim and never fabricates a suggestion.
export async function searchSymbols(q: string): Promise<SymbolMatch[]> {
  const query = q.trim();
  if (!query) return [];
  try {
    const res = await fetch(`${API_BASE}/symbols/search?q=${encodeURIComponent(query)}`);
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? (data as SymbolMatch[]) : [];
  } catch {
    return [];
  }
}

// GET /tape/{ticker}/history?bar= — engine-computed OHLC candles + tape-state markers for the
// prediction chart (J-17 / J-18). The chart reads these VERBATIM (single source of truth); it
// never re-bins candles or re-derives a marker. A not-watched ticker (404), a not-yet-warmed
// window, or any error yields null/empty so the chart falls back to its empty treatment — it
// NEVER invents candles. `bar` is one of the configured sizes (an out-of-set value is a 422).
export async function fetchHistory(
  ticker: string,
  bar: number,
): Promise<TapeHistory | null> {
  try {
    const res = await fetch(
      `${API_BASE}/tape/${encodeURIComponent(ticker)}/history?bar=${bar}`,
    );
    if (!res.ok) return null;
    const data = await res.json();
    return {
      bar: typeof data.bar === "number" ? data.bar : bar,
      bars: Array.isArray(data.bars) ? data.bars : [],
      markers: Array.isArray(data.markers) ? data.markers : [],
    };
  } catch {
    return null;
  }
}

// DELETE /watch/{ticker}: stop watching. A 404 means the ticker is already not watched —
// effectively stopped, so we treat it as success (the UI returns to idle either way).
export async function stopTicker(ticker: string): Promise<StopResult> {
  try {
    const res = await fetch(`${API_BASE}/watch/${encodeURIComponent(ticker)}`, {
      method: "DELETE",
    });
    if (res.ok || res.status === 404) {
      return { ok: true };
    }
    let error = `'${ticker}' could not be stopped`;
    try {
      const data = await res.json();
      if (data?.detail) error = data.detail;
    } catch {
      /* keep default */
    }
    return { ok: false, error };
  } catch {
    return { ok: false, error: "Backend unreachable — is the API running?" };
  }
}

// Initial paint via REST: assemble one snapshot from the canonical reads. These return the
// same engine snapshot values the WS stream pushes, so the UI shows one value per metric.
export async function fetchInitialSnapshot(
  ticker: string,
): Promise<TapeSnapshot | null> {
  const t = encodeURIComponent(ticker);
  try {
    const [summaryRes, featuresRes, eventsRes] = await Promise.all([
      fetch(`${API_BASE}/tape/${t}/summary`),
      fetch(`${API_BASE}/tape/${t}/features`),
      fetch(`${API_BASE}/tape/${t}/events`),
    ]);
    if (!summaryRes.ok || !featuresRes.ok || !eventsRes.ok) return null;
    const summary = await summaryRes.json();
    const features = await featuresRes.json();
    const events = await eventsRes.json();
    return {
      ticker: summary.ticker,
      scenario: summary.scenario,
      stream_status: summary.stream_status,
      timestamp: summary.timestamp,
      market: summary.market,
      tape_state: summary.tape_state,
      confidence: summary.confidence,
      primary_window: summary.primary_window ?? features.primary_window,
      features: features.windows,
      headline_features: summary.headline_features,
      observations: summary.observations ?? events.observations ?? [],
      event_log: events.event_log ?? [],
      recent_trades: events.recent_trades ?? [],
    };
  } catch {
    return null;
  }
}
