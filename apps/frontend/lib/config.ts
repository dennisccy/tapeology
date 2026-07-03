// Backend base URL. The QA harness sets NEXT_PUBLIC_API_URL (and may use an offset port),
// so prefer it; NEXT_PUBLIC_API_BASE is an accepted alias; otherwise default to :8000.
export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ??
  process.env.NEXT_PUBLIC_API_BASE ??
  "http://localhost:8000";

// WebSocket base derived from the API base (http -> ws, https -> wss).
export const WS_BASE = API_BASE.replace(/^http/, "ws");

// Client-side request-timeout backstop for the Watch path (J-22 / no-unbounded-waits anti-goal).
// `watchTicker` and `fetchInitialSnapshot` abort with an AbortController after this many
// milliseconds, so a slow or hung backend always resolves the connecting state to a visible error
// rather than a frozen UI. This is the ONE source of the value — no inline millisecond literal in
// the fetch helpers. It sits comfortably above the backend's own per-call vendor timeout so the
// backend's explicit error wins when reachable, and this is the backstop for an unreachable/hung
// backend that never even responds.
//
// ORDERING INVARIANT (J-28): this MUST stay strictly greater than the backend's effective
// vendor bound (vendor_http_timeout_seconds <= vendor_call_timeout_seconds = 8s in
// apps/backend/app/config.py) so the user always sees the backend's honest, actionable error
// (e.g. "try a shorter range") rather than a client-side give-up when the backend is reachable.
export const WATCH_REQUEST_TIMEOUT_MS = 12000;

// Symbol-search tuning (J-30 / bounded-honest-vendor-calls anti-goal). The ONE source for both
// values — no inline literal in SymbolSearch.tsx.
//   * DEBOUNCE_MS: a quiet period after the last keystroke before a lookup fires (rapid typing
//     does not fire a request per character).
//   * MIN_QUERY: the minimum query length before any lookup fires, MIRRORING the backend
//     `symbol_search_min_query` so a too-short query is dropped client-side (no over-broad scan)
//     exactly as the backend would drop it. Free-text watch entry is unaffected (the user can
//     still type and Watch a full symbol; only the suggestions dropdown waits for MIN_QUERY).
export const SYMBOL_SEARCH_DEBOUNCE_MS = 250;
export const SYMBOL_SEARCH_MIN_QUERY = 1;

// Route-map fetch backstop (J-01). The nav loads its links from GET /meta/ui-routes (the single
// canonical route source — Data Contract row 35); if the backend HANGS rather than refusing, this
// abort resolves the nav to its explicit degraded state instead of loading forever (a refused
// connection already fails fast on its own). The ONE source of the value — no inline literal in
// NavBar.tsx.
export const UI_ROUTES_REQUEST_TIMEOUT_MS = 8000;
