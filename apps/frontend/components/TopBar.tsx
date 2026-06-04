"use client";

import { useState } from "react";
import type { ConnStatus, DataSourceMode, TapeSnapshot, WatchParams } from "@/lib/types";
import { DataSourceSelector } from "./DataSourceSelector";
import { MarketStatusIndicator } from "./MarketStatusIndicator";
import { SymbolSearch } from "./SymbolSearch";

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

const INPUT_CLASS =
  "rounded border border-slate-700 bg-slate-950 px-3 py-1.5 font-mono text-sm text-slate-100 placeholder-slate-600 transition-colors focus:border-emerald-500 focus:outline-none";

const REPLAY_SPEEDS = [1, 2, 5, 10];

export function TopBar({
  watched,
  snapshot,
  connStatus,
  mode,
  onModeChange,
  onWatch,
  onStop,
  error,
}: {
  watched: string | null;
  snapshot: TapeSnapshot | null;
  connStatus: ConnStatus;
  mode: DataSourceMode;
  onModeChange: (mode: DataSourceMode) => void;
  onWatch: (symbol: string, params: WatchParams) => void;
  onStop: () => void;
  error: string | null;
}) {
  const [symbol, setSymbol] = useState("");
  const [date, setDate] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [speed, setSpeed] = useState(1);

  // Prefer the engine's canonical stream status whenever a snapshot is present; fall back to
  // the client connection status only for the pre-snapshot idle/connecting affordance.
  const dot: DotSpec = snapshot
    ? STREAM_DOT[snapshot.stream_status] ?? { color: "bg-slate-600", label: snapshot.stream_status }
    : CONN_DOT[connStatus];

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (mode === "historical") {
      const start = date && startTime ? `${date}T${startTime}` : undefined;
      const end = date && endTime ? `${date}T${endTime}` : undefined;
      onWatch(symbol, { mode, start, end, speed });
    } else {
      onWatch(symbol, { mode });
    }
  }

  const symbolPlaceholder = mode === "sim" ? "Ticker e.g. SIM-BUYER" : "Symbol e.g. AAPL";
  const symbolLabel = mode === "sim" ? "Ticker" : "Symbol search";

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
        <div className="text-lg font-bold tracking-tight text-slate-100">Tapeology</div>

        <DataSourceSelector mode={mode} onChange={onModeChange} />

        <form onSubmit={handleSubmit} className="flex flex-wrap items-center gap-2">
          {mode === "sim" ? (
            <input
              aria-label={symbolLabel}
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder={symbolPlaceholder}
              className={`w-48 ${INPUT_CLASS}`}
            />
          ) : (
            // Live / Historical: real symbol search (J-13). Free-text entry still works.
            <SymbolSearch
              value={symbol}
              onChange={setSymbol}
              onPick={setSymbol}
              placeholder={symbolPlaceholder}
              ariaLabel={symbolLabel}
              inputClassName={`w-48 ${INPUT_CLASS}`}
            />
          )}

          {mode === "historical" && (
            <>
              <input
                type="date"
                aria-label="Date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className={`${INPUT_CLASS} [color-scheme:dark]`}
              />
              <input
                type="time"
                aria-label="Start time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className={`${INPUT_CLASS} [color-scheme:dark]`}
              />
              <span className="text-slate-600">–</span>
              <input
                type="time"
                aria-label="End time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className={`${INPUT_CLASS} [color-scheme:dark]`}
              />
              <select
                aria-label="Replay speed"
                value={speed}
                onChange={(e) => setSpeed(Number(e.target.value))}
                className={INPUT_CLASS}
              >
                {REPLAY_SPEEDS.map((s) => (
                  <option key={s} value={s}>
                    {s}×
                  </option>
                ))}
              </select>
            </>
          )}

          <button
            type="submit"
            className="rounded bg-emerald-600 px-3 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-400 active:bg-emerald-700"
          >
            Watch
          </button>
        </form>

        {/* Live market-status indicator (row 8): the REAL session status from GET /market/clock,
            replacing the prior hardcoded "unavailable" stub. Mounted only in Live mode, so its
            poll is torn down on mode-change. */}
        {mode === "live" && <MarketStatusIndicator />}

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
