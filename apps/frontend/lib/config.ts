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
export const WATCH_REQUEST_TIMEOUT_MS = 12000;
