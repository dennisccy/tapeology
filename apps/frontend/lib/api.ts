import { API_BASE } from "./config";
import type { SymbolMatch, TapeSnapshot, WatchParams } from "./types";

export interface WatchResult {
  ok: boolean;
  scenario?: string;
  error?: string;
  // The distinct honest failure `reason` when the backend refused a real-mode watch (row 9):
  // "provider_unavailable" | "symbol_not_tradable" | "no_data_for_window" (or another reason
  // string). The UI renders a distinct non-cockpit panel per reason — never a fabricated
  // cockpit, never a silent fall-back to Simulated.
  reason?: string;
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
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") error = data.detail;
      if (typeof data?.reason === "string") reason = data.reason;
    } catch {
      /* keep default */
    }
    return { ok: false, error, reason };
  } catch {
    return { ok: false, error: "Backend unreachable — is the API running?" };
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
