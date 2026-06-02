import { useEffect, useState } from "react";
import { WS_BASE } from "./config";
import { fetchInitialSnapshot } from "./api";
import type { ConnStatus, TapeSnapshot } from "./types";

// Live tape feed for one ticker: initial paint via REST, then live updates via the
// WebSocket. The hook only stores what the engine sends — it never recomputes a value.
export function useTapeStream(ticker: string | null): {
  snapshot: TapeSnapshot | null;
  connStatus: ConnStatus;
} {
  const [snapshot, setSnapshot] = useState<TapeSnapshot | null>(null);
  const [connStatus, setConnStatus] = useState<ConnStatus>("idle");

  useEffect(() => {
    if (!ticker) {
      setSnapshot(null);
      setConnStatus("idle");
      return;
    }

    let cancelled = false;
    setConnStatus("connecting");
    setSnapshot(null);

    fetchInitialSnapshot(ticker)
      .then((initial) => {
        if (!cancelled && initial) setSnapshot(initial);
      })
      .catch(() => {});

    const ws = new WebSocket(`${WS_BASE}/tape/${encodeURIComponent(ticker)}/stream`);
    ws.onopen = () => {
      if (!cancelled) setConnStatus("live");
    };
    ws.onmessage = (event) => {
      if (cancelled) return;
      try {
        setSnapshot(JSON.parse(event.data) as TapeSnapshot);
      } catch {
        /* ignore malformed frame */
      }
    };
    ws.onclose = () => {
      if (!cancelled) setConnStatus("closed");
    };
    ws.onerror = () => {
      if (!cancelled) setConnStatus("closed");
    };

    return () => {
      cancelled = true;
      ws.close();
    };
  }, [ticker]);

  return { snapshot, connStatus };
}
