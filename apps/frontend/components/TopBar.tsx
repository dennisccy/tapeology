"use client";

import { useState } from "react";
import type { ConnStatus, TapeSnapshot } from "@/lib/types";

type DotSpec = { color: string; label: string };

// Pre-snapshot affordance only (idle / connecting before the first engine snapshot arrives).
const CONN_DOT: Record<ConnStatus, DotSpec> = {
  idle: { color: "bg-slate-600", label: "idle" },
  connecting: { color: "bg-amber-400 animate-pulse", label: "connecting" },
  live: { color: "bg-emerald-400", label: "live" },
  closed: { color: "bg-rose-500", label: "closed" },
};

// The canonical engine stream status (single source of truth). Once a snapshot is present the
// dot reads THIS — so when a bounded sim stream exhausts and the engine flips to "closed", the
// dot tells the truth instead of a stale client-side "live".
const STREAM_DOT: Record<string, DotSpec> = {
  connecting: { color: "bg-amber-400 animate-pulse", label: "connecting" },
  live: { color: "bg-emerald-400", label: "live" },
  stale: { color: "bg-amber-400", label: "stale" },
  closed: { color: "bg-rose-500", label: "closed" },
};

export function TopBar({
  watched,
  snapshot,
  connStatus,
  onWatch,
  onStop,
  error,
}: {
  watched: string | null;
  snapshot: TapeSnapshot | null;
  connStatus: ConnStatus;
  onWatch: (ticker: string) => void;
  onStop: () => void;
  error: string | null;
}) {
  const [input, setInput] = useState("");

  // Prefer the engine's canonical stream status whenever a snapshot is present; fall back to
  // the client connection status only for the pre-snapshot idle/connecting affordance.
  const dot: DotSpec = snapshot
    ? STREAM_DOT[snapshot.stream_status] ?? { color: "bg-slate-600", label: snapshot.stream_status }
    : CONN_DOT[connStatus];

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
        <div className="text-lg font-bold tracking-tight text-slate-100">Tapeology</div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            onWatch(input);
          }}
          className="flex items-center gap-2"
        >
          <input
            aria-label="Ticker"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ticker e.g. SIM-BUYER"
            className="w-48 rounded border border-slate-700 bg-slate-950 px-3 py-1.5 font-mono text-sm text-slate-100 placeholder-slate-600 transition-colors focus:border-emerald-500 focus:outline-none"
          />
          <button
            type="submit"
            className="rounded bg-emerald-600 px-3 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-500 active:bg-emerald-700"
          >
            Watch
          </button>
        </form>

        {watched && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-500">Watching</span>
            <span className="font-mono font-semibold text-slate-100">{watched}</span>
            <button
              type="button"
              onClick={onStop}
              aria-label="Stop watching"
              className="rounded border border-rose-500/70 px-2.5 py-1 text-xs font-semibold text-rose-400 transition-colors hover:bg-rose-500/10 hover:text-rose-300 focus:outline-none focus:ring-1 focus:ring-rose-400 active:bg-rose-500/20"
            >
              Stop
            </button>
          </div>
        )}

        {watched && snapshot?.scenario && (
          <div className="rounded bg-slate-800 px-2 py-1 text-xs text-slate-300">
            scenario: <span className="font-mono">{snapshot.scenario}</span>
          </div>
        )}

        <div className="ml-auto flex items-center gap-2 text-xs text-slate-400">
          <span className={`inline-block h-2.5 w-2.5 rounded-full ${dot.color}`} />
          <span className="capitalize">{dot.label}</span>
        </div>
      </div>

      {error && (
        <div className="mx-auto max-w-7xl px-4 pb-3 text-sm text-rose-400">{error}</div>
      )}
    </header>
  );
}
