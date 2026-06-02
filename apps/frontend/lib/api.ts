import { API_BASE } from "./config";
import type { TapeSnapshot } from "./types";

export interface WatchResult {
  ok: boolean;
  scenario?: string;
  error?: string;
}

// POST /watch/{ticker}. An unknown / non-sim ticker returns an explicit error (no fabrication).
export async function watchTicker(ticker: string): Promise<WatchResult> {
  try {
    const res = await fetch(`${API_BASE}/watch/${encodeURIComponent(ticker)}`, {
      method: "POST",
    });
    if (res.ok) {
      const data = await res.json();
      return { ok: true, scenario: data.scenario };
    }
    let error = `'${ticker}' could not be watched`;
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
