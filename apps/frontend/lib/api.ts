import { API_BASE, WATCH_REQUEST_TIMEOUT_MS } from "./config";
import type {
  Analytics,
  AnalyticsResult,
  CreateStudyParams,
  CreateStudyResult,
  DeclareResult,
  JournalDetail,
  JournalFilters,
  JournalRow,
  MarketClock,
  ResearchTaxonomy,
  Study,
  SymbolMatch,
  TapeHistory,
  TapeSnapshot,
  ThesisProjection,
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

// POST /research/thesis/{id}/action — journal the user's ACTUAL entry / exit on the active thesis
// (J-52). This is a JOURNALING record of the user's OWN already-taken action — never a fill, never a
// simulated execution, never an order. `price` is sent VERBATIM (the backend records it exactly as
// submitted); the backend stamps the logical/wall time and the moment spread-at-mark itself. The
// backend's 422 (unknown kind / non-positive or malformed price) and 409 (already resolved /
// duplicate entry / duplicate exit / exit-before-entry) detail is surfaced VERBATIM for an inline
// message — never a swallowed failure or a dead click. On success the next WS frame carries the
// recorded marks on the `thesis` key, so the strip updates on its own (the frontend derives nothing).
export async function recordAction(
  thesisId: string,
  kind: "entry" | "exit",
  price: number,
): Promise<StopResult> {
  try {
    const res = await fetch(
      `${API_BASE}/research/thesis/${encodeURIComponent(thesisId)}/action`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind, price }),
      },
    );
    if (res.ok) return { ok: true };
    let error = `The ${kind} mark could not be recorded.`;
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

// POST /research/thesis/{id}/review — save the user's CONFIRMED review (J-57): mistake tags + an
// optional note. The user CONFIRMS the tags (the machine only SUGGESTS them); on success the backend
// persists the tags + note verbatim and flips the thesis to `reviewed`. The backend's validation
// (422 unknown tag / 422 `other` without a note / 409 unresolved / 409 already-reviewed / 404 unknown
// id) detail is surfaced VERBATIM for an inline message — never a swallowed failure or a dead click.
// The client also blocks Save when `other` is selected without a note as a courtesy, but the backend
// is the authority. On success the page re-reads the detail to render the persisted review.
export async function saveReview(
  thesisId: string,
  mistakeTags: string[],
  note: string | null,
): Promise<StopResult> {
  try {
    const body: Record<string, unknown> = { mistake_tags: mistakeTags };
    if (note !== null && note.trim() !== "") body.note = note;
    const res = await fetch(
      `${API_BASE}/research/thesis/${encodeURIComponent(thesisId)}/review`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (res.ok) return { ok: true };
    let error = "The review could not be saved.";
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

// The canonical thesis projection (`GET /research/thesis/active?ticker=`) is the REST counterpart
// of the WS `thesis` key (verbatim-equal by construction — data-contract row 15). While a watch is
// LIVE the strip reads the WS `thesis` key only (one read path per contract value). This REST fetch
// is used ONLY when there is NO live stream — after a Stop — to discover a SURVIVING entry-marked
// thesis (J-47): an entry-marked thesis is not orphaned by a stop, so the cockpit surface keeps
// showing it as not-currently-evaluated (read from the SAME endpoint, never recomputed client-side).
// Returns the projection, `null` when nothing survives (a normal state), or `null` on any error
// (the caller simply shows the idle cockpit — no fabricated thesis).
export async function fetchActiveThesis(
  ticker: string,
): Promise<ThesisProjection | null> {
  try {
    const res = await fetchWithTimeout(
      `${API_BASE}/research/thesis/active?ticker=${encodeURIComponent(ticker)}`,
    );
    if (!res.ok) return null;
    const data = await res.json();
    return (data?.thesis as ThesisProjection | null) ?? null;
  } catch {
    return null;
  }
}

// The result of a journal LIST fetch (J-51). `ok` with the rows, or an explicit error so the
// /journal page can show a styled error state rather than a blank/fabricated table. A backend 422
// (unknown enum filter) detail is surfaced verbatim — never coerced.
export interface JournalListResult {
  ok: boolean;
  rows: JournalRow[];
  error?: string;
}

// GET /research/journal — the ONLY serving path for journal rows (J-51). Filters drive a SERVER-side
// re-fetch (the frontend does no client-side filtering). Reads rows VERBATIM; the frontend recomputes
// nothing. An unknown enum filter is a backend 422 surfaced as an explicit error; an unreachable
// backend resolves to an explicit error too (never a silent empty table).
export async function fetchJournal(
  filters: JournalFilters = {},
): Promise<JournalListResult> {
  const params = new URLSearchParams();
  if (filters.ticker) params.set("ticker", filters.ticker);
  if (filters.setup_type) params.set("setup_type", filters.setup_type);
  if (filters.direction) params.set("direction", filters.direction);
  if (filters.resolution) params.set("resolution", filters.resolution);
  if (filters.status) params.set("status", filters.status);
  const qs = params.toString();
  try {
    const res = await fetch(`${API_BASE}/research/journal${qs ? `?${qs}` : ""}`);
    if (res.ok) {
      const data = await res.json();
      return { ok: true, rows: (data?.rows as JournalRow[]) ?? [] };
    }
    let error = "The journal could not be loaded.";
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") error = data.detail;
    } catch {
      /* keep default */
    }
    return { ok: false, rows: [], error };
  } catch {
    return { ok: false, rows: [], error: "Backend unreachable — is the API running?" };
  }
}

// The result of a journal-detail fetch (J-55). `ok` with the detail, `notFound` for an unknown id
// (the page shows an explicit honest error state, never a blank page), or a generic error.
export interface JournalDetailResult {
  ok: boolean;
  detail?: JournalDetail;
  notFound?: boolean;
  error?: string;
}

// GET /research/journal/{id} — the ONLY serving path for the per-thesis review detail (J-55). Reads
// the thesis + frozen statements + frozen risk flags + action marks + the append-only verdict
// timeline + the machine-derived execution checks (computed once at resolution) VERBATIM; the page
// recomputes nothing. A 404 (unknown id) resolves to `notFound` so the page renders an explicit
// honest error state; an unreachable backend resolves to an explicit error too (never a blank page).
export async function fetchJournalDetail(
  thesisId: string,
): Promise<JournalDetailResult> {
  try {
    const res = await fetch(
      `${API_BASE}/research/journal/${encodeURIComponent(thesisId)}`,
    );
    if (res.ok) {
      const data = (await res.json()) as JournalDetail;
      return { ok: true, detail: data };
    }
    if (res.status === 404) {
      return { ok: false, notFound: true, error: "No thesis with that id was found." };
    }
    let error = "The thesis could not be loaded.";
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

// GET /research/analytics — the ONLY serving path for the segregated journal analytics (J-59). The
// backend computes the full partitioned projection (read-only over persisted rows, never pooled); the
// view renders it VERBATIM (display rounding only). An empty journal returns an honest empty payload
// (partitions: []), NOT an error; an unreachable backend resolves to an explicit error (never a blank).
export async function fetchAnalytics(): Promise<AnalyticsResult> {
  try {
    const res = await fetch(`${API_BASE}/research/analytics`);
    if (res.ok) {
      const data = (await res.json()) as Analytics;
      return { ok: true, analytics: data };
    }
    let error = "The analytics could not be loaded.";
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

// --- Replay studies (capability 32, J-60/J-61/J-62) ---------------------------------------------

// POST /research/studies — create + START a replay study (J-60). The backend persists it ``queued``,
// starts it as a background job, and returns the full queued projection. The backend's 422 (unknown
// setup/direction/source, missing/forbidden level, missing window, unavailable credentials) detail is
// surfaced VERBATIM — never coerced. `level_price` / `start` / `end` / `null_baseline_seed` are sent
// only when provided. The frontend computes nothing — it renders the returned projection.
export async function createStudy(params: CreateStudyParams): Promise<CreateStudyResult> {
  try {
    const body: Record<string, unknown> = {
      source_kind: params.source_kind,
      source_id: params.source_id,
      setup_type: params.setup_type,
      direction: params.direction,
    };
    if (params.level_price !== undefined && params.level_price !== null) {
      body.level_price = params.level_price;
    }
    if (params.start) body.start = params.start;
    if (params.end) body.end = params.end;
    if (params.null_baseline_seed !== undefined) body.null_baseline_seed = params.null_baseline_seed;
    const res = await fetch(`${API_BASE}/research/studies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (res.ok) {
      const data = await res.json();
      return { ok: true, study: data.study as Study, status: res.status };
    }
    let error = "The study could not be created.";
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

// GET /research/studies — list studies most-recent-first. Read VERBATIM (each row is the runner's
// persisted payload; the page recomputes nothing). Any failure resolves to an empty list with an
// explicit error so the page shows a styled error rather than a blank/fabricated list.
export async function fetchStudies(): Promise<{ ok: boolean; studies: Study[]; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/research/studies`);
    if (res.ok) {
      const data = await res.json();
      return { ok: true, studies: (data?.studies as Study[]) ?? [] };
    }
    return { ok: false, studies: [], error: "The studies could not be loaded." };
  } catch {
    return { ok: false, studies: [], error: "Backend unreachable — is the API running?" };
  }
}

// GET /research/studies/{id} — one study's status/progress + stored results, served VERBATIM. Returns
// null on a 404 / any error (the caller keeps the prior view; never fabricates a study).
export async function fetchStudy(studyId: string): Promise<Study | null> {
  try {
    const res = await fetch(`${API_BASE}/research/studies/${encodeURIComponent(studyId)}`);
    if (!res.ok) return null;
    const data = await res.json();
    return (data?.study as Study) ?? null;
  } catch {
    return null;
  }
}

// POST /research/studies/{id}/cancel — cancel a running/queued study (J-61). The backend's 404
// (unknown id) / 409 (already terminal) detail is surfaced VERBATIM. On success the job resolves to
// explicit `cancelled` with partial-marked results (the next poll shows it).
export async function cancelStudy(studyId: string): Promise<{ ok: boolean; error?: string }> {
  try {
    const res = await fetch(
      `${API_BASE}/research/studies/${encodeURIComponent(studyId)}/cancel`,
      { method: "POST" },
    );
    if (res.ok) return { ok: true };
    let error = "The study could not be cancelled.";
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
