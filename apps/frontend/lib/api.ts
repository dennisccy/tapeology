import { API_BASE, WATCH_REQUEST_TIMEOUT_MS } from "./config";
import type {
  DeclareResult,
  MarketClock,
  ResearchTaxonomy,
  SymbolMatch,
  TapeHistory,
  TapeSnapshot,
  WatchParams,
} from "./types";

// Client-side request-timeout backstop (J-22 / no-unbounded-waits anti-goal). Wrap a fetch in an
// AbortController that aborts after WATCH_REQUEST_TIMEOUT_MS (the single config constant — no
// inline millisecond literal), so a slow/hung backend never leaves the Watch flow hanging forever.
// An aborted request throws (a DOMException with name "AbortError"); callers map that to an
// explicit, distinct error result so the connecting state resolves to a visible timeout error.
// `isTimeoutError` lets callers distinguish a timeout from a plain network failure.
export class RequestTimeoutError extends Error {
  constructor(message = "Request timed out") {
    super(message);
    this.name = "RequestTimeoutError";
  }
}

export function isTimeoutError(err: unknown): boolean {
  return (
    err instanceof RequestTimeoutError ||
    (err instanceof DOMException && err.name === "AbortError") ||
    (typeof err === "object" && err !== null && (err as { name?: string }).name === "AbortError")
  );
}

async function fetchWithTimeout(
  input: string,
  init: RequestInit = {},
  timeoutMs: number = WATCH_REQUEST_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    // Always clear the timer — on success, network error, OR abort — so no dangling timeout
    // leaks and a swallowed rejection can never hide here (the rejection still propagates).
    clearTimeout(timer);
  }
}

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
    const res = await fetchWithTimeout(`${API_BASE}/watch/${encodeURIComponent(ticker)}`, init);
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
  } catch (err) {
    // A client-side timeout (the AbortController fired) is a distinct, explicit error so the
    // connecting state resolves to a visible "timed out" message rather than hanging forever
    // (J-22 frontend half). Any other throw is an unreachable/failed backend.
    if (isTimeoutError(err)) {
      return {
        ok: false,
        error: "Market data provider timed out — please try again.",
        reason: "provider_timeout",
      };
    }
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

// GET /symbols/search?q= — real tradable suggestions for the search box (J-13 / J-30). Any
// failure or empty query yields an empty list (free-text watch entry always remains possible); the
// UI renders these verbatim and never fabricates a suggestion.
//
// Cancellation (J-30): the caller passes an `AbortSignal` so a newer keystroke can cancel this
// in-flight request — preventing a pile-up and an out-of-order overwrite where a slow earlier
// response clobbers a newer result. An aborted request resolves to "no result" (`[]`), NEVER an
// error: the dropdown simply shows nothing for the cancelled query rather than an error banner or
// a stuck "Searching…". A vendor hiccup likewise degrades to `[]` here.
export async function searchSymbols(
  q: string,
  signal?: AbortSignal,
): Promise<SymbolMatch[]> {
  const query = q.trim();
  if (!query) return [];
  try {
    const res = await fetch(
      `${API_BASE}/symbols/search?q=${encodeURIComponent(query)}`,
      { signal },
    );
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? (data as SymbolMatch[]) : [];
  } catch (err) {
    // An abort (a newer keystroke cancelled this request) is NOT an error — resolve to no result
    // so a late/cancelled response can never overwrite a newer one. Any other failure (vendor
    // hiccup / unreachable backend) also degrades to an empty list, never a thrown error.
    if (isTimeoutError(err)) return [];
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
      // The canonical display/epoch anchor (row 13, J-31), read VERBATIM so the chart renders
      // true clock time. `null` when the backend has no anchor (empty/anchorless window).
      epoch_anchor: typeof data.epoch_anchor === "number" ? data.epoch_anchor : null,
      bars: Array.isArray(data.bars) ? data.bars : [],
      markers: Array.isArray(data.markers) ? data.markers : [],
    };
  } catch {
    return null;
  }
}

// POST /watch/{ticker}/pause — freeze a watched session WITHOUT teardown (J-19). The backend
// flips the canonical paused flag + stream_status to "paused" (owned once by the engine/feeder);
// the UI reads that off the snapshot/stream and never guesses paused. A 404 means the ticker is
// not (or no longer) watched. The cockpit is NOT cleared by a pause.
export async function pauseTicker(ticker: string): Promise<StopResult> {
  return postWatchAction(ticker, "pause");
}

// POST /watch/{ticker}/resume — continue a paused watch (J-19). The backend clears paused and
// restores the prior stream_status (never a fabricated "live"); feeding continues with no
// synthesized catch-up. The UI reads the restored status off the snapshot/stream.
export async function resumeTicker(ticker: string): Promise<StopResult> {
  return postWatchAction(ticker, "resume");
}

// POST /watch/{ticker}/speed — change the replay speed of a RUNNING historical replay (J-32).
// This is NOT a re-Watch: the backend re-paces the in-progress replay (no re-fetch, no engine
// restart, no teardown), so the cockpit/chart continue from their current position at the new
// cadence. The backend validates the speed against its allowed set (out-of-set => 422,
// authoritative); a 404 means the ticker is not (or no longer) watched. The frontend control only
// offers in-set values as a courtesy. Speed is delivery-pacing only — never a displayed value, so
// nothing in the cockpit's canonical engine values changes (determinism preserved).
export async function setReplaySpeed(
  ticker: string,
  speed: number,
): Promise<StopResult> {
  try {
    const res = await fetch(
      `${API_BASE}/watch/${encodeURIComponent(ticker)}/speed`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ speed }),
      },
    );
    if (res.ok) return { ok: true };
    let error = `replay speed could not be changed`;
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

async function postWatchAction(
  ticker: string,
  action: "pause" | "resume",
): Promise<StopResult> {
  try {
    const res = await fetch(
      `${API_BASE}/watch/${encodeURIComponent(ticker)}/${action}`,
      { method: "POST" },
    );
    if (res.ok) return { ok: true };
    let error = `'${ticker}' could not be ${action}d`;
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
//
// Outcomes (J-23 — a failed initial connection must NOT be swallowed):
//   * Resolves to a TapeSnapshot when all three canonical reads succeed.
//   * Resolves to `null` when a read came back not-ok (e.g. 404 not-yet-watched / not-warmed) —
//     a clean "no snapshot yet", not a failure; the WS will paint the first frame instead.
//   * THROWS on a hard transport failure (backend unreachable / client-side timeout) so the
//     caller can SURFACE an explicit connect-failure rather than silently dropping it. The throw
//     re-uses RequestTimeoutError for an abort so the caller can label a timeout distinctly.
export async function fetchInitialSnapshot(
  ticker: string,
): Promise<TapeSnapshot | null> {
  const t = encodeURIComponent(ticker);
  let summaryRes: Response, featuresRes: Response, eventsRes: Response;
  try {
    [summaryRes, featuresRes, eventsRes] = await Promise.all([
      fetchWithTimeout(`${API_BASE}/tape/${t}/summary`),
      fetchWithTimeout(`${API_BASE}/tape/${t}/features`),
      fetchWithTimeout(`${API_BASE}/tape/${t}/events`),
    ]);
  } catch (err) {
    // Do NOT swallow: a transport failure/timeout is rethrown (as a RequestTimeoutError for an
    // abort) so useTapeStream can record an explicit connect-failure status.
    if (isTimeoutError(err)) throw new RequestTimeoutError("Tape stream request timed out");
    throw err;
  }
  // A not-ok response is a clean "no snapshot yet" (e.g. just-watched, not warmed) — return null
  // and let the WS paint the first frame; this is NOT a hard failure.
  if (!summaryRes.ok || !featuresRes.ok || !eventsRes.ok) return null;
  const summary = await summaryRes.json();
  const features = await featuresRes.json();
  const events = await eventsRes.json();
  return {
    ticker: summary.ticker,
    scenario: summary.scenario,
    stream_status: summary.stream_status,
    paused: summary.paused ?? false,
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
}

// --- Research: taxonomy, declare, active read (capability 23/24) --------------------------------

// GET /research/taxonomy — the single backend owner of every research label. The declare form is
// built from this (setups, directions, per-setup level requirement). Returns null on any failure so
// the strip can show an explicit "couldn't load the catalog" state rather than a fabricated form.
export async function fetchTaxonomy(): Promise<ResearchTaxonomy | null> {
  try {
    const res = await fetch(`${API_BASE}/research/taxonomy`);
    if (!res.ok) return null;
    return (await res.json()) as ResearchTaxonomy;
  } catch {
    return null;
  }
}

// POST /research/thesis — declare a thesis with HONEST validation. The backend's 422/409/404 detail
// is surfaced VERBATIM for an inline message (never a client-side coercion); nothing is created on
// rejection. On success the full projection is returned. `level_price` is sent only when provided.
export async function declareThesis(params: {
  ticker: string;
  setup_type: string;
  direction: string;
  invalidation_price: number;
  level_price?: number | null;
}): Promise<DeclareResult> {
  try {
    const body: Record<string, unknown> = {
      ticker: params.ticker,
      setup_type: params.setup_type,
      direction: params.direction,
      invalidation_price: params.invalidation_price,
    };
    if (params.level_price !== undefined && params.level_price !== null) {
      body.level_price = params.level_price;
    }
    const res = await fetch(`${API_BASE}/research/thesis`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (res.ok) {
      const data = await res.json();
      return { ok: true, thesis: data.thesis, status: res.status };
    }
    // Surface the backend detail verbatim for the inline message (422 wrong-side / missing-or-
    // forbidden level / unknown enum; 409 active-thesis-exists; 404 not-watched).
    let error = "The thesis could not be declared.";
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") error = data.detail;
    } catch {
      /* keep default */
    }
    return { ok: false, status: res.status, error };
  } catch {
    return { ok: false, error: "Backend unreachable — is the API running?" };
  }
}

// POST /research/thesis/{id}/resolve — honestly close out a USER-declared thesis (J-50). The user
// may set ONLY `played_out` or `abandoned`; `invalidated`/`expired` are system-owned (the backend
// returns 422). On success the backend flips the terminal status, appends the final timeline event,
// and detaches the monitor — the next WS frame then carries `thesis: null`, so the strip returns to
// the declare affordance on its own (the frontend derives nothing). A 409 (already resolved /
// entry-marked-refuses-abandon) or 422 detail is surfaced VERBATIM for an inline message — never a
// swallowed failure or a dead click.
export async function resolveThesis(
  thesisId: string,
  resolution: "played_out" | "abandoned",
): Promise<StopResult> {
  try {
    const res = await fetch(
      `${API_BASE}/research/thesis/${encodeURIComponent(thesisId)}/resolve`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resolution }),
      },
    );
    if (res.ok) return { ok: true };
    let error = "The thesis could not be resolved.";
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") error = data.detail;
    } catch {
      /* keep default */
    }
    return { ok: false, error };
  } catch {
    return { ok: false, error: "Backend unreachable — is the API running?" };
  }
}

// NOTE: the canonical thesis projection (`GET /research/thesis/active?ticker=`) is the REST
// counterpart of the WS `thesis` key. The strip reads the WS `thesis` key only (one read path per
// contract value — data-contract row 15); QA probes the REST endpoint directly for the
// verbatim-equality check. No parallel UI-layer REST fetch is kept here on purpose.
