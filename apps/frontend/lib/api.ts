import { API_BASE, WATCH_REQUEST_TIMEOUT_MS } from "./config";
import type {
  Backtest,
  BarCandlesPage,
  BarSeriesListResult,
  BarSeriesRecord,
  CreateBacktestParams,
  DatasetsListResult,
  DeskScreenComputeSnapshot,
  DeskScreenListResult,
  DeskTopupComputeSnapshot,
  EdgeReportComputeSnapshot,
  EdgeReportPayload,
  LevelsResponse,
  MarketClock,
  MergedCandlesPage,
  PnlLedger,
  ProfilesPayload,
  RecordBarSeriesResult,
  ResearchTaxonomy,
  SetupDetailResult,
  SetupsListResult,
  StrategiesPayload,
  SymbolMatch,
  TapeHistory,
  TapeSnapshot,
  TapeTimeframeHistory,
  TradabilityResponse,
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

// GET /tape/{ticker}/history?timeframe= — the cockpit chart's wall-clock "history" mode: real-epoch
// OHLC+volume candles built live from the tape, plus the no-lookahead boundary and per-marker
// bucket. Read VERBATIM (the chart recomputes nothing). `null` on any failure so the caller keeps
// whatever it had rather than a fabricated series. Additive sibling of `fetchHistory` above (which
// is untouched); the backend's own 422 is the timeframe-validation authority.
export async function fetchTimeframeHistory(
  ticker: string,
  timeframe: string,
): Promise<TapeTimeframeHistory | null> {
  try {
    const res = await fetch(
      `${API_BASE}/tape/${encodeURIComponent(ticker)}/history?timeframe=${encodeURIComponent(timeframe)}`,
    );
    if (!res.ok) return null;
    const data = await res.json();
    return {
      timeframe: typeof data.timeframe === "string" ? data.timeframe : timeframe,
      timeframe_seconds:
        typeof data.timeframe_seconds === "number" ? data.timeframe_seconds : 0,
      epoch_anchor: typeof data.epoch_anchor === "number" ? data.epoch_anchor : null,
      anchor_bucket_start:
        typeof data.anchor_bucket_start === "number" ? data.anchor_bucket_start : null,
      timeframe_bars: Array.isArray(data.timeframe_bars) ? data.timeframe_bars : [],
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
    // Row 14: read the feeder-owned lag VERBATIM (null when not yet stamped) — zero client arithmetic.
    delivery_lag_seconds: summary.delivery_lag_seconds ?? null,
    // Row 29 (J-67): read the served current-watch feed basis VERBATIM (never client-derived from
    // scenario). Absent on a pre-J-67 backend => undefined (the badge then renders nothing).
    data_feed: summary.data_feed,
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

// --- Research: taxonomy (capability 23/24) -------------------------------------------------------

// GET /research/taxonomy — the single backend owner of every research label (era-5D J-02: now just
// the KEPT feed_basis + source labels, per the J-01-slimmed payload). Returns null on any failure so
// the badge can show an explicit degraded state rather than a fabricated label.
export async function fetchTaxonomy(): Promise<ResearchTaxonomy | null> {
  try {
    const res = await fetch(`${API_BASE}/research/taxonomy`);
    if (!res.ok) return null;
    return (await res.json()) as ResearchTaxonomy;
  } catch {
    return null;
  }
}

// GET /research/pnl/ledger (Data Contract row 32) — the append-only PnL ledger, served VERBATIM
// (register + min_sample_size + stored rows). On any failure the caller shows an explicit
// unavailable state: `ledger: null` — NEVER cached or fabricated rows.
export async function fetchPnlLedger(): Promise<{
  ok: boolean;
  ledger: PnlLedger | null;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/research/pnl/ledger`);
    if (res.ok) {
      return { ok: true, ledger: (await res.json()) as PnlLedger };
    }
    return { ok: false, ledger: null, error: "The PnL ledger could not be loaded." };
  } catch {
    return { ok: false, ledger: null, error: "Backend unreachable — is the API running?" };
  }
}

// GET /research/profiles (Data Contract row 33) — the profile registry + champion pointer,
// served VERBATIM (the ONLY source of the champion — never inferred client-side). On any
// failure the caller shows an explicit unavailable state: `profiles: null`.
export async function fetchProfiles(): Promise<{
  ok: boolean;
  profiles: ProfilesPayload | null;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/research/profiles`);
    if (res.ok) {
      return { ok: true, profiles: (await res.json()) as ProfilesPayload };
    }
    return { ok: false, profiles: null, error: "The profile registry could not be loaded." };
  } catch {
    return { ok: false, profiles: null, error: "Backend unreachable — is the API running?" };
  }
}

// GET /research/strategies (Data Contract row 40/41; era-4 capability 4, surfaced this interlude
// at the /structure Registry section, J-02) — the strategy registry (`v1` + `structure_tape`) +
// the current champion pointer, served VERBATIM. This is the SAME store-owned champion pointer
// `fetchProfiles` reads (one pointer, two read views — never a second champion source). On any
// failure the caller shows an explicit unavailable state: `strategies: null` — never a fabricated
// registry, mirroring `fetchProfiles`'s pattern byte-for-byte.
export async function fetchStrategies(): Promise<{
  ok: boolean;
  strategies: StrategiesPayload | null;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/research/strategies`);
    if (res.ok) {
      return { ok: true, strategies: (await res.json()) as StrategiesPayload };
    }
    return { ok: false, strategies: null, error: "The strategy registry could not be loaded." };
  } catch {
    return { ok: false, strategies: null, error: "Backend unreachable — is the API running?" };
  }
}

// --- Structure: S/R levels + confluence zones + recorded bar series (Data Contract row 39/38,
// surfaced this interlude at /structure, J-01) -----------------------------------------------------

// GET /research/levels?symbol=&as_of= — the S/R levels + confluence zones, served VERBATIM. The
// backend's own 422 (empty symbol / malformed as_of) is folded into the SAME `ok:false` result as
// an unreachable backend — the page renders one shared degraded state for both, surfacing the
// backend's `detail` message verbatim rather than fabricating a distinct copy for a rare
// client-input mistake. `data: null` on any failure so the caller never shows a stale/fabricated
// chart or zones table in its place.
export async function fetchLevels(
  symbol: string,
  asOf: string,
): Promise<{ ok: boolean; data: LevelsResponse | null; error?: string; status?: number }> {
  try {
    const res = await fetch(
      `${API_BASE}/research/levels?symbol=${encodeURIComponent(symbol)}&as_of=${encodeURIComponent(asOf)}`,
    );
    if (res.ok) {
      return { ok: true, data: (await res.json()) as LevelsResponse, status: res.status };
    }
    let error = "The levels could not be loaded.";
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") error = data.detail;
    } catch {
      /* keep default */
    }
    return { ok: false, data: null, error, status: res.status };
  } catch {
    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
  }
}

// GET /research/bars (Data Contract row 38) — every registered bar series, served VERBATIM. This
// is a LIST endpoint with no symbol query param (mirroring /research/datasets); the Structure page
// filters the returned array client-side by the already-served `symbol` field — the SAME
// filtering discipline NavBar already applies to `nav: true` (filtering already-served rows is not
// a recomputation of any value). `data: null` on any failure so the caller shows an explicit
// unavailable state rather than a fabricated/empty chart.
// Optional narrowing params (all ADDITIVE, all served by the same route): `symbol`/`timeframe`
// filter server-side through the bar index, and `includeBars: false` asks for the metadata-only
// projection (each record without its `bars` key). A no-arg call still hits the bare URL, so every
// pre-existing caller — and the MCP `bars` proxy — is unaffected. The Structure page uses
// `{symbol, includeBars: false}` so a Load transfers a few KB of series metadata instead of every
// candle of every recorded series; the candles themselves arrive one viewport at a time through
// `fetchBarCandles` below.
export async function fetchBarSeriesList(params?: {
  symbol?: string;
  timeframe?: string;
  includeBars?: boolean;
}): Promise<{
  ok: boolean;
  data: BarSeriesListResult | null;
  error?: string;
}> {
  const query = new URLSearchParams();
  if (params?.symbol) query.set("symbol", params.symbol);
  if (params?.timeframe) query.set("timeframe", params.timeframe);
  if (params?.includeBars === false) query.set("include_bars", "false");
  const suffix = query.toString() ? `?${query}` : "";
  try {
    const res = await fetch(`${API_BASE}/research/bars${suffix}`);
    if (res.ok) {
      return { ok: true, data: (await res.json()) as BarSeriesListResult };
    }
    return { ok: false, data: null, error: "The bar series list could not be loaded." };
  } catch {
    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
  }
}

// GET /research/bars/{id}/candles — ONE bounded window of a series' stored candles. Pass at most
// one cursor: `beforeTs` (inclusive) for the last `limit` rows at or before that epoch-seconds
// instant, `afterTs` (inclusive) for the first `limit` rows at or after it, neither for the newest
// `limit` rows. Both cursors are inclusive, so a cursor taken from an already-loaded row re-serves
// that row — the caller de-duplicates by `ts` when merging (never an off-by-one hole mid-chart).
// `data: null` on any failure so the caller shows an explicit state rather than a silently short
// candle window.
// GET /research/candles — the MERGED window: the same bounded slice as `fetchBarCandles`, but over
// every recorded series for one symbol+timeframe (identical cursor semantics). This is what the
// /structure charts page through: a chart bound to a single recording can only ever show that
// recording's window, so zooming out runs out of bars while longer recordings of the same
// symbol+timeframe sit in the store. The merge (dedupe by timestamp, newest recording wins a
// revision) happens server-side in `research/bars.py` — the browser folds nothing.
export async function fetchMergedCandles(
  symbol: string,
  timeframe: string,
  params: { beforeTs?: number; afterTs?: number; limit: number },
): Promise<{ ok: boolean; data: MergedCandlesPage | null; error?: string }> {
  const query = new URLSearchParams({
    symbol,
    timeframe,
    limit: String(params.limit),
  });
  if (params.beforeTs !== undefined) query.set("before_ts", String(params.beforeTs));
  if (params.afterTs !== undefined) query.set("after_ts", String(params.afterTs));
  try {
    const res = await fetch(`${API_BASE}/research/candles?${query}`);
    if (res.ok) {
      return { ok: true, data: (await res.json()) as MergedCandlesPage };
    }
    return { ok: false, data: null, error: "The candle window could not be loaded." };
  } catch {
    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
  }
}

export async function fetchBarCandles(
  seriesId: string,
  params: { beforeTs?: number; afterTs?: number; limit: number },
): Promise<{ ok: boolean; data: BarCandlesPage | null; error?: string }> {
  const query = new URLSearchParams({ limit: String(params.limit) });
  if (params.beforeTs !== undefined) query.set("before_ts", String(params.beforeTs));
  if (params.afterTs !== undefined) query.set("after_ts", String(params.afterTs));
  try {
    const res = await fetch(`${API_BASE}/research/bars/${seriesId}/candles?${query}`);
    if (res.ok) {
      return { ok: true, data: (await res.json()) as BarCandlesPage };
    }
    return { ok: false, data: null, error: "The candle window could not be loaded." };
  } catch {
    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
  }
}

// POST /research/bars (era-5 J-05) — the ONE new explicit write action in the app: the
// `/structure` "Fetch from Yahoo Finance" control. The `end` of the window is INCLUSIVE by UTC
// calendar date server-side (era-5C: the route extends the vendor fetch through the end of that
// day). The store-first coordinator either serves an
// already-stored window from storage (zero adapter/network calls) or fetches it fresh — both
// resolve `200` (a repeat window is NEVER a `409` — the iter-3 lesson; a `409` here means a
// DIFFERENT window whose fetched content happens to duplicate content already on file). The
// backend's own 422 (unsupported timeframe / no data for that window / malformed window) / 503
// (adapter unavailable, e.g. a non-Yahoo override with no credentials) / 504 (vendor timeout) /
// 409 (content-duplicate refusal) detail is surfaced VERBATIM — never coerced into one generic
// message. The frontend computes nothing: on success the caller re-reads the canonical
// bars/levels endpoints (the existing read path) rather than rendering this response directly.
// `vendor` (optional) picks the source for THIS call: the default keyless Yahoo, or `"alpaca"` for
// the credentialed deep-history path. Yahoo caps intraday history (1m to the last 30 days, 5m to
// 60, 1h to 730 — its own measured limits), so a request reaching further back is recorded in two
// pieces, one per vendor, each an honest recording of what that vendor served. The merged candle
// read stitches them by timestamp.
export async function recordBarSeries(params: {
  symbol: string;
  timeframe: string;
  start: string;
  end: string;
  vendor?: "yahoo" | "alpaca";
}): Promise<RecordBarSeriesResult> {
  try {
    const res = await fetch(`${API_BASE}/research/bars`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (res.ok) {
      const data = await res.json();
      return { ok: true, bar_series: data.bar_series as BarSeriesRecord, status: res.status };
    }
    let error = "The bar series could not be fetched.";
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

// --- structure_tape-vs-v1 backtest comparison (era-3 capability 4 / era-4 capability 5, surfaced
// this interlude at /structure's Comparison section, J-03) ---------------------------------------

// GET /research/datasets (Data Contract row 30) — every registered dataset's metadata, served
// VERBATIM (each file checksum-verified on load). Mirrors `fetchBarSeriesList()`'s shape byte-for-
// byte (a LIST endpoint with no query params). `data: null` on any failure so the caller shows an
// explicit unavailable state rather than a fabricated/empty selector.
export async function fetchDatasets(): Promise<{
  ok: boolean;
  data: DatasetsListResult | null;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/research/datasets`);
    if (res.ok) {
      return { ok: true, data: (await res.json()) as DatasetsListResult };
    }
    return { ok: false, data: null, error: "The dataset list could not be loaded." };
  } catch {
    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
  }
}

// POST /research/backtests (era-3 capability 4, J-03) — create + START a deterministic backtest
// job over one registered dataset. Exactly the three fields `BacktestRequest` accepts
// (routes.py:160-171) — no `null_baseline_seed` field exists on this request. The backend's 404
// (unknown dataset) / 422 (unknown strategy/profile) detail is surfaced VERBATIM — never coerced.
// On success the queued payload is returned; the frontend computes nothing.
export async function createBacktest(
  params: CreateBacktestParams,
): Promise<{ ok: boolean; backtest?: Backtest; status?: number; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/research/backtests`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (res.ok) {
      const data = await res.json();
      return { ok: true, backtest: data.backtest as Backtest, status: res.status };
    }
    let error = "The backtest could not be created.";
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

// GET /research/backtests/{id} (era-3 capability 4, J-03) — one backtest's status + stored
// report, served VERBATIM. Returns `null` on a 404 / any error (the caller keeps the prior view;
// never fabricates a backtest).
export async function fetchBacktest(backtestId: string): Promise<Backtest | null> {
  try {
    const res = await fetch(`${API_BASE}/research/backtests/${encodeURIComponent(backtestId)}`);
    if (!res.ok) return null;
    const data = await res.json();
    return (data?.backtest as Backtest) ?? null;
  } catch {
    return null;
  }
}

// --- Era-5B: tradable map, case-study setups, and the 3-way edge report (capabilities 1/2/6,
// J-01/J-02/J-04), wired to the browser this iteration (J-05) at /structure's three new sections.
// All four functions follow `fetchLevels`/`fetchStrategies` immediately above byte-for-byte: the
// `{ok, data, error}` shape, the backend's own `detail` surfaced verbatim on a non-200 (folding a
// validation refusal — e.g. a malformed `as_of` 422 — into the SAME degraded-state treatment as an
// unreachable backend), and `data: null` on any failure so the caller never shows a stale or
// fabricated view in its place.

// GET /research/tradability?symbol=&as_of= — the tradable level map, served VERBATIM. Mirrors
// `fetchLevels` exactly (same required params, same 422/unreachable folding).
export async function fetchTradability(
  symbol: string,
  asOf: string,
): Promise<{ ok: boolean; data: TradabilityResponse | null; error?: string; status?: number }> {
  try {
    const res = await fetch(
      `${API_BASE}/research/tradability?symbol=${encodeURIComponent(symbol)}&as_of=${encodeURIComponent(asOf)}`,
    );
    if (res.ok) {
      return { ok: true, data: (await res.json()) as TradabilityResponse, status: res.status };
    }
    let error = "The tradable map could not be loaded.";
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") error = data.detail;
    } catch {
      /* keep default */
    }
    return { ok: false, data: null, error, status: res.status };
  } catch {
    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
  }
}

// GET /research/setups (optionally filtered by symbol/reaction/band_class — server-side,
// AND-combined; an unknown enum `reaction`/`band_class` is a backend 422) — the touch-event
// case-study registry, served VERBATIM. `filters` follows the optional-filter-params pattern used
// elsewhere in this file; an omitted filter is left off the query string entirely (never sent as an
// empty param).
export async function fetchSetups(filters?: {
  symbol?: string;
  reaction?: string;
  band_class?: string;
}): Promise<{ ok: boolean; data: SetupsListResult | null; error?: string }> {
  const params = new URLSearchParams();
  if (filters?.symbol) params.set("symbol", filters.symbol);
  if (filters?.reaction) params.set("reaction", filters.reaction);
  if (filters?.band_class) params.set("band_class", filters.band_class);
  const qs = params.toString();
  try {
    const res = await fetch(`${API_BASE}/research/setups${qs ? `?${qs}` : ""}`);
    if (res.ok) {
      return { ok: true, data: (await res.json()) as SetupsListResult };
    }
    let error = "The case-study registry could not be loaded.";
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") error = data.detail;
    } catch {
      /* keep default */
    }
    return { ok: false, data: null, error };
  } catch {
    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
  }
}

// GET /research/setups/{id} — one event's drill-in (band, reaction, forward returns, and the J-03
// `tape_timeline` — present-but-empty when no recorded dataset covers the touch), served VERBATIM.
// A 404 (unknown id) folds into the same `ok:false` degraded result as any other failure — the
// backend's own `detail` ("no setup event with id '…'") is surfaced verbatim, so the caller never
// needs a separate not-found branch (mirrors `fetchLevels`'s "fold validation refusals into the
// shared degraded state" precedent, applied to a 404 instead of a 422).
export async function fetchSetupDetail(
  id: string,
): Promise<{ ok: boolean; data: SetupDetailResult | null; error?: string; status?: number }> {
  try {
    const res = await fetch(`${API_BASE}/research/setups/${encodeURIComponent(id)}`);
    if (res.ok) {
      return { ok: true, data: (await res.json()) as SetupDetailResult, status: res.status };
    }
    let error = "The case-study event could not be loaded.";
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") error = data.detail;
    } catch {
      /* keep default */
    }
    return { ok: false, data: null, error, status: res.status };
  } catch {
    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
  }
}

// GET /research/edge-report — the 3-way strategy-comparison report (`v1` / `structure_tape` /
// `structure_tape_map`), served VERBATIM. Mirrors `fetchDatasets`/`fetchBarSeriesList` (a LIST-
// shaped endpoint with no query params). An all-empty or all-`insufficient_sample` report is a
// valid `ok:true` result — the caller renders it as an honest first-class state, never as a
// failure; `data: null` is reserved for a genuine non-200 / unreachable backend.
export async function fetchEdgeReport(): Promise<{
  ok: boolean;
  data: EdgeReportPayload | null;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/research/edge-report`);
    if (res.ok) {
      return { ok: true, data: (await res.json()) as EdgeReportPayload };
    }
    let error = "The edge report could not be loaded.";
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") error = data.detail;
    } catch {
      /* keep default */
    }
    return { ok: false, data: null, error };
  } catch {
    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
  }
}

// --- era-fast_wall J-04: the operator-run edge-report compute -- POST the single-flight trigger,
// GET the poll-while-active snapshot, POST the cooperative cancel. All three mirror
// `createBacktest`/`fetchBacktest`'s exact `{ok, data/…, error}` shape and 422/unreachable folding
// byte-for-byte (both immediately above and below in this file).

// POST /research/edge-report/compute — start (or, while one is already running, observe) the
// single-flight compute job. Mirrors `createBacktest`'s exact shape: `data` carries the full
// `{started, compute}` body on success; the backend's own 422/unreachable `detail` is surfaced
// VERBATIM on failure — never a client-fabricated message in its place.
export async function triggerEdgeReportCompute(
  force?: boolean,
): Promise<{
  ok: boolean;
  data?: { started: boolean; compute: EdgeReportComputeSnapshot };
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/research/edge-report/compute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ force: force ?? false }),
    });
    if (res.ok) {
      const data = await res.json();
      return { ok: true, data };
    }
    let error = "The edge-report compute could not be started.";
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

// GET /research/edge-report/compute — the compute job's current/last snapshot, served VERBATIM,
// or `null` if none has ever run. Mirrors `fetchBacktest`'s pattern: `ok:false, data:null` on any
// failure so a poll tick's caller keeps the last known view — never fabricates a snapshot.
export async function fetchEdgeReportCompute(): Promise<{
  ok: boolean;
  data: EdgeReportComputeSnapshot | null;
}> {
  try {
    const res = await fetch(`${API_BASE}/research/edge-report/compute`);
    if (!res.ok) return { ok: false, data: null };
    const data = await res.json();
    return { ok: true, data: (data as EdgeReportComputeSnapshot | null) ?? null };
  } catch {
    return { ok: false, data: null };
  }
}

// POST /research/edge-report/compute/cancel — cancel the in-flight compute job. Mirrors this
// file's own `{ok, error?}` shape (the `StopResult`-family pattern); the backend's 409 (idle)
// `detail` is surfaced VERBATIM.
export async function cancelEdgeReportCompute(): Promise<{ ok: boolean; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/research/edge-report/compute/cancel`, { method: "POST" });
    if (res.ok) return { ok: true };
    let error = "The edge-report compute could not be cancelled.";
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

// --- era-desk-iter-4 (J-04): the /desk page's seven fetch/trigger/cancel functions. Mirror
// `triggerEdgeReportCompute`/`fetchEdgeReportCompute`/`cancelEdgeReportCompute` immediately above
// exact `{ok, data, error}` shape and 422/unreachable-fold behavior byte-for-byte.

// GET /research/desk/screen — the screen-history list + latest full snapshot, served VERBATIM.
// Mirrors `fetchEdgeReport`/`fetchDatasets` (a LIST-shaped endpoint, no query params — the
// `?date=` variant is J-05 scope, deferred). An honest-empty (`{screens: [], latest: null,
// integrity_errors: []}`) result is a valid `ok:true` outcome — the caller renders it as the
// "Desk screen not computed yet." state, never a failure; `data: null` is reserved for a genuine
// non-200 / unreachable backend.
export async function fetchDeskScreen(): Promise<{
  ok: boolean;
  data: DeskScreenListResult | null;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/research/desk/screen`);
    if (res.ok) {
      return { ok: true, data: (await res.json()) as DeskScreenListResult };
    }
    let error = "The desk screen could not be loaded.";
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") error = data.detail;
    } catch {
      /* keep default */
    }
    return { ok: false, data: null, error };
  } catch {
    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
  }
}

// POST /research/desk/screen/compute — start (or, while one is already running, observe) the
// single-flight screen compute job. `screenDate` is the CALLER's own today (the `todayUtcDate()`
// helper, /structure's own "Today" shortcut precedent) — this function takes it as a parameter
// rather than resolving it itself, so the page owns the ONE date source. Mirrors
// `triggerEdgeReportCompute`'s exact shape; the backend's own 422 (e.g. no universe registered)
// `detail` is surfaced VERBATIM, never a client-fabricated message.
export async function triggerDeskScreenCompute(screenDate: string): Promise<{
  ok: boolean;
  data?: { started: boolean; compute: DeskScreenComputeSnapshot };
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/research/desk/screen/compute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ screen_date: screenDate }),
    });
    if (res.ok) {
      const data = await res.json();
      return { ok: true, data };
    }
    let error = "The screen compute could not be started.";
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

// GET /research/desk/screen/compute — the screen compute job's current/last snapshot, served
// VERBATIM, or `null` if none has ever run. Mirrors `fetchEdgeReportCompute`: `ok:false, data:null`
// on any failure so a poll tick's caller keeps the last known view — never fabricates a snapshot.
export async function fetchDeskScreenCompute(): Promise<{
  ok: boolean;
  data: DeskScreenComputeSnapshot | null;
}> {
  try {
    const res = await fetch(`${API_BASE}/research/desk/screen/compute`);
    if (!res.ok) return { ok: false, data: null };
    const data = await res.json();
    return { ok: true, data: (data as DeskScreenComputeSnapshot | null) ?? null };
  } catch {
    return { ok: false, data: null };
  }
}

// POST /research/desk/screen/compute/cancel — cancel the in-flight screen compute job. Mirrors
// `cancelEdgeReportCompute`'s `{ok, error?}` shape; the backend's 409 (idle) `detail` is surfaced
// VERBATIM.
export async function cancelDeskScreenCompute(): Promise<{ ok: boolean; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/research/desk/screen/compute/cancel`, { method: "POST" });
    if (res.ok) return { ok: true };
    let error = "The screen compute could not be cancelled.";
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

// POST /research/desk/topup/compute — start (or, while one is already running, observe) the
// single-flight desk bar top-up job over the latest universe snapshot's members. No request body
// (the backend resolves the latest universe snapshot itself). Mirrors
// `triggerDeskScreenCompute`'s shape; this is the FIRST-EVER UI caller of this endpoint (shipped
// J-02, iter-2 — CLI/POST-only until now).
export async function triggerDeskTopupCompute(): Promise<{
  ok: boolean;
  data?: { started: boolean; compute: DeskTopupComputeSnapshot };
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/research/desk/topup/compute`, { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      return { ok: true, data };
    }
    let error = "The bar top-up could not be started.";
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

// GET /research/desk/topup/compute — the top-up job's current/last snapshot, served VERBATIM, or
// `null` if none has ever run this process. Mirrors `fetchDeskScreenCompute`.
export async function fetchDeskTopupCompute(): Promise<{
  ok: boolean;
  data: DeskTopupComputeSnapshot | null;
}> {
  try {
    const res = await fetch(`${API_BASE}/research/desk/topup/compute`);
    if (!res.ok) return { ok: false, data: null };
    const data = await res.json();
    return { ok: true, data: (data as DeskTopupComputeSnapshot | null) ?? null };
  } catch {
    return { ok: false, data: null };
  }
}

// POST /research/desk/topup/compute/cancel — cancel the in-flight top-up job. Mirrors
// `cancelDeskScreenCompute`.
export async function cancelDeskTopupCompute(): Promise<{ ok: boolean; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/research/desk/topup/compute/cancel`, { method: "POST" });
    if (res.ok) return { ok: true };
    let error = "The bar top-up could not be cancelled.";
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
