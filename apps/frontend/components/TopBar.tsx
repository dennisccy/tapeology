"use client";

import { useState } from "react";
import type { ConnStatus, TapeSnapshot } from "@/lib/types";

const DOT_COLOR: Record<ConnStatus, string> = {
  idle: "bg-slate-600",
  connecting: "bg-amber-400 animate-pulse",
  live: "bg-emerald-400",
  closed: "bg-rose-500",
};

export function TopBar({
  watched,
  snapshot,
  connStatus,
  onWatch,
  error,
}: {
  watched: string | null;
  snapshot: TapeSnapshot | null;
  connStatus: ConnStatus;
  onWatch: (ticker: string) => void;
  error: string | null;
}) {
  const [input, setInput] = useState("");

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
          </div>
        )}

        {watched && snapshot?.scenario && (
          <div className="rounded bg-slate-800 px-2 py-1 text-xs text-slate-300">
            scenario: <span className="font-mono">{snapshot.scenario}</span>
          </div>
        )}

        <div className="ml-auto flex items-center gap-2 text-xs text-slate-400">
          <span className={`inline-block h-2.5 w-2.5 rounded-full ${DOT_COLOR[connStatus]}`} />
          <span className="capitalize">{connStatus}</span>
        </div>
      </div>

      {error && (
        <div className="mx-auto max-w-7xl px-4 pb-3 text-sm text-rose-400">{error}</div>
      )}
    </header>
  );
}
