// Backend base URL. The QA harness sets NEXT_PUBLIC_API_URL (and may use an offset port),
// so prefer it; NEXT_PUBLIC_API_BASE is an accepted alias; otherwise default to :8000.
export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ??
  process.env.NEXT_PUBLIC_API_BASE ??
  "http://localhost:8000";

// WebSocket base derived from the API base (http -> ws, https -> wss).
export const WS_BASE = API_BASE.replace(/^http/, "ws");
