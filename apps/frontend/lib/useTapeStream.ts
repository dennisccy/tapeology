import { useEffect, useState } from "react";
import { WS_BASE } from "./config";
import { fetchInitialSnapshot, isTimeoutError } from "./api";
import type { ConnStatus, TapeSnapshot } from "./types";

// Live tape feed for one ticker: initial paint via REST, then live updates via the
// WebSocket. The hook only stores what the engine sends — it never recomputes a value.
//
// Honest connection lifecycle (J-23 — no swallowed failures):
//   * The initial-snapshot fetch failure is NOT swallowed (the old `.catch(() => {})`). A hard
//     transport failure/timeout records an explicit `failed` connect status + a message.
//   * A WS `onerror` / early `onclose` BEFORE any snapshot has arrived is a surfaced
//     "couldn't connect to the tape stream" failure (`failed`), not a silent `closed`.
//   * Once at least one snapshot has arrived, a later close is the normal end-of-stream
//     `closed` (the engine's own status dot then tells the truth) — not a connect failure.
export function useTapeStream(ticker: string | null): {
  snapshot: TapeSnapshot | null;
  connStatus: ConnStatus;
  connError: string | null;
} {
  const [snapshot, setSnapshot] = useState<TapeSnapshot | null>(null);
  const [connStatus, setConnStatus] = useState<ConnStatus>("idle");
  const [connError, setConnError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) {
      setSnapshot(null);
      setConnStatus("idle");
      setConnError(null);
      return;
    }

    let cancelled = false;
    // Whether any frame (REST snapshot OR a WS message) has painted yet. A pre-snapshot WS
    // error/close is a connect FAILURE; a post-snapshot one is the normal end-of-stream close.
    let gotFrame = false;
    setConnStatus("connecting");
    setConnError(null);
    setSnapshot(null);

    function fail(message: string) {
      if (cancelled || gotFrame) return;
      setConnStatus("failed");
      setConnError(message);
    }

    fetchInitialSnapshot(ticker)
      .then((initial) => {
        if (cancelled || !initial) return;
        gotFrame = true;
        setSnapshot(initial);
      })
      .catch((err) => {
        // Surface (do NOT swallow) a hard initial-connection failure. A timeout gets a distinct
        // message; any other transport error reads as a generic stream-connect failure.
        fail(
          isTimeoutError(err)
            ? "Tape stream request timed out — couldn’t connect."
            : "Couldn’t connect to the tape stream.",
        );
      });

    const ws = new WebSocket(`${WS_BASE}/tape/${encodeURIComponent(ticker)}/stream`);
    ws.onopen = () => {
      if (!cancelled) setConnStatus("live");
    };
    ws.onmessage = (event) => {
      if (cancelled) return;
      try {
        gotFrame = true;
        setSnapshot(JSON.parse(event.data) as TapeSnapshot);
        setConnStatus("live");
      } catch {
        /* ignore a single malformed frame (the next frame repaints) */
      }
    };
    ws.onclose = () => {
      if (cancelled) return;
      // Closed BEFORE any frame => the stream never connected (e.g. backend stopped right after
      // Watch, or a 4404 rejection): surface it. Closed AFTER a frame => normal end-of-stream.
      if (!gotFrame) fail("Couldn’t connect to the tape stream.");
      else setConnStatus("closed");
    };
    ws.onerror = () => {
      if (!cancelled && !gotFrame) fail("Couldn’t connect to the tape stream.");
    };

    return () => {
      cancelled = true;
      ws.close();
    };
  }, [ticker]);

  return { snapshot, connStatus, connError };
}
