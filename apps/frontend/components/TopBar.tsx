"use client";

import { useState } from "react";
import type { ConnStatus, DataSourceMode, TapeSnapshot, WatchParams } from "@/lib/types";
import {
  ET_SESSION_CLOSE,
  ET_SESSION_OPEN,
  formatWatchedSource,
  isValidIsoDate,
  resolveEtWindowInstant,
} from "@/lib/datetime";
import { DataSourceSelector } from "./DataSourceSelector";
import { FeedBasisBadge } from "./FeedBasisBadge";
import { MarketStatusIndicator } from "./MarketStatusIndicator";
import { SymbolSearch } from "./SymbolSearch";

type DotSpec = { color: string; label: string };

// Pre-snapshot affordance only (idle / connecting before the first engine snapshot arrives).
const CONN_DOT: Record<ConnStatus, DotSpec> = {
  idle: { color: "bg-slate-600", label: "idle" },
  connecting: { color: "bg-amber-400 animate-pulse", label: "connecting" },
  live: { color: "bg-emerald-400", label: "live" },
  closed: { color: "bg-rose-500", label: "closed" },
  // J-23: an explicit surfaced connect-failure (initial snapshot / pre-snapshot WS failed) — rose,
  // distinct from a normal "closed", so the dot never sits on a frozen "connecting".
  failed: { color: "bg-rose-500", label: "failed" },
};

// The canonical engine stream status (single source of truth). Once a snapshot is present the
// dot reads THIS — so when a bounded sim stream exhausts and the engine flips to "closed", the
// dot tells the truth instead of a stale client-side "live".
const STREAM_DOT: Record<string, DotSpec> = {
  connecting: { color: "bg-amber-400 animate-pulse", label: "connecting" },
  // Waiting (J-26): stream open, no first event yet — amber + pulse to read as in-progress
  // (matching connecting). The dot MUST read "waiting", never a confident "live" over an empty tape.
  waiting: { color: "bg-amber-400 animate-pulse", label: "waiting" },
  live: { color: "bg-emerald-400", label: "live" },
  stale: { color: "bg-amber-400", label: "stale" },
  // Paused (J-19): amber, consistent with stale/absorption/unclear = amber. Read from the engine's
  // canonical paused status — never a client-side guess; the dot must read "paused", never "live".
  paused: { color: "bg-amber-400", label: "paused" },
  closed: { color: "bg-rose-500", label: "closed" },
  // Failed (J-27): a post-connect feeder failure surfaced by the canonical snapshot — rose,
  // distinct from a normal "closed". Read verbatim; the dot never sits on a frozen "live".
  failed: { color: "bg-rose-500", label: "failed" },
};

// The canonical row-14 `delivery_lag_seconds` readout (J-64): how far the processed tape trails real
// time, in seconds. Reads the SAME served value the `tape_lag_ok` entry-checklist check reads — the
// UI does DISPLAY ROUNDING ONLY, never any wall-clock arithmetic (zero client-side computation). An
// honest absence (`null`/`undefined` — before the feeder stamps the first lag) renders an explicit
// "lag —" placeholder, never a fabricated 0.
function formatDeliveryLag(lag: number | null | undefined): string {
  if (lag === null || lag === undefined) return "lag —";
  return `lag ${lag.toFixed(1)}s`;
}

const INPUT_CLASS =
  "rounded border border-slate-700 bg-slate-950 px-3 py-1.5 font-mono text-sm text-slate-100 placeholder-slate-600 transition-colors focus:border-emerald-500 focus:outline-none";

const REPLAY_SPEEDS = [1, 2, 5, 10];

// US regular-trading-hours session quick-picks (J-20). The ET wall-clock anchors come from named
// constants in lib/datetime (no scattered literals). Each entry fills the start/end window in one
// click.
//
// Now that the time fields are themselves read as ET wall-clock, a quick-pick is a LITERAL fill of
// those fields — the anchors go straight in and `resolveHistoricalWindow` maps them to UTC through
// the same path a hand-typed window takes. (While entry was operator-local these had to be
// converted to the reader's zone first, and the resolved instants stashed separately, because an ET
// session can straddle two LOCAL calendar dates — 16:00 ET is 04:00 next-day in Hong Kong — which
// re-resolving local HH:MM against the single date field would silently shift. On the exchange
// clock the fields and the anchors agree by construction, so that whole apparatus is gone.)
const SESSION_QUICK_PICKS: {
  key: string;
  label: string;
  start: { hour: number; minute: number };
  end: { hour: number; minute: number };
}[] = [
  { key: "open", label: "Open 9:30 ET", start: ET_SESSION_OPEN, end: ET_SESSION_OPEN },
  { key: "close", label: "Close 16:00 ET", start: ET_SESSION_CLOSE, end: ET_SESSION_CLOSE },
  { key: "rth", label: "Full RTH 9:30–16:00 ET", start: ET_SESSION_OPEN, end: ET_SESSION_CLOSE },
];

// A small window so single-instant presets (Open / Close) yield a valid start < end: anchor +
// this many minutes. RTH uses the full 9:30->16:00 span, so this only pads the point presets.
const PRESET_POINT_SPAN_MIN = 1;

// `HH:MM:SS` for an ET anchor, the shape the `step="1"` time inputs carry.
function timeInputValue(hour: number, minute: number, second = 0): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(hour)}:${pad(minute)}:${pad(second)}`;
}

// Shared chrome for the quick-pick buttons (neutral — no buy/sell semantics on the picker).
const QUICK_PICK_CLASS =
  "rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-300 transition-colors hover:border-slate-500 hover:text-slate-100 focus:border-emerald-500 focus:outline-none active:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40";

export function TopBar({
  watched,
  snapshot,
  connStatus,
  mode,
  onModeChange,
  onWatch,
  onStop,
  onPause,
  onResume,
  onSpeedChange,
  error,
}: {
  watched: string | null;
  snapshot: TapeSnapshot | null;
  connStatus: ConnStatus;
  mode: DataSourceMode;
  onModeChange: (mode: DataSourceMode) => void;
  onWatch: (symbol: string, params: WatchParams) => void;
  onStop: () => void;
  onPause: () => void;
  onResume: () => void;
  // J-32: change the replay speed of a RUNNING historical replay (applies live via
  // POST /watch/{ticker}/speed — NOT a re-Watch). Called only when a historical watch is active.
  onSpeedChange: (speed: number) => void;
  error: string | null;
}) {
  const [symbol, setSymbol] = useState("");
  // The custom `yyyy-MM-dd` date field: the typed text IS the internal value the row-12 resolver
  // and the ET quick-picks consume, so there is no second date representation to keep in step.
  // (A native `<input type="date">` is deliberately not used — it renders and reads in the
  // BROWSER's locale and zone, the two things this product now fixes to one format and one clock.)
  const [dateText, setDateText] = useState("");
  const date = isValidIsoDate(dateText) ? dateText.trim() : ""; // "" when invalid/empty
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [speed, setSpeed] = useState(1);
  // Inline validation message (J-24): set on a Watch attempt with invalid input, so an empty
  // symbol or a missing/invalid historical window gives immediate feedback and is NEVER a silent
  // no-op. Cleared as soon as the offending input is corrected (the field onChange handlers).
  const [validationError, setValidationError] = useState<string | null>(null);

  // Manual edits to any window field clear a stale validation message (J-24) so the inline
  // feedback tracks the live input.
  function onDateChange(value: string) {
    setDateText(value);
    setValidationError(null);
  }
  function onStartTimeChange(value: string) {
    setStartTime(value);
    setValidationError(null);
  }
  function onEndTimeChange(value: string) {
    setEndTime(value);
    setValidationError(null);
  }
  // Symbol edits clear a stale validation message too (J-24).
  function onSymbolChange(value: string) {
    setSymbol(value);
    setValidationError(null);
  }

  // Apply a US-session quick-pick: fill the ET time fields with the session anchors directly. The
  // fields ARE the exchange clock now, so a pick needs no conversion and nothing stashed aside —
  // `resolveHistoricalWindow` maps the filled values to UTC through the same DST-correct path a
  // hand-typed window takes. A point preset (Open / Close) is padded by PRESET_POINT_SPAN_MIN so
  // start < end is always valid.
  function applyQuickPick(pick: (typeof SESSION_QUICK_PICKS)[number]) {
    if (!date) return; // disabled in the UI, but never produce a malformed/empty window
    const isPoint =
      pick.end.hour === pick.start.hour && pick.end.minute === pick.start.minute;
    const endMinutes = isPoint
      ? pick.start.hour * 60 + pick.start.minute + PRESET_POINT_SPAN_MIN
      : pick.end.hour * 60 + pick.end.minute;
    setStartTime(timeInputValue(pick.start.hour, pick.start.minute));
    setEndTime(timeInputValue(Math.floor(endMinutes / 60), endMinutes % 60));
    setValidationError(null);
  }

  // Prefer the engine's canonical stream status whenever a snapshot is present; fall back to
  // the client connection status only for the pre-snapshot idle/connecting affordance.
  const dot: DotSpec = snapshot
    ? STREAM_DOT[snapshot.stream_status] ?? { color: "bg-slate-600", label: snapshot.stream_status }
    : CONN_DOT[connStatus];

  // Pause/Resume visibility is read ONLY from the engine's canonical snapshot (single source of
  // truth — the UI never guesses paused). `paused` toggles the control to Resume; `pauseable`
  // gates the Pause button to an active feed (connecting / live / stale) so it's hidden once the
  // stream is closed (a closed/idle session has nothing to pause).
  const paused = snapshot?.paused === true;
  const pauseable =
    !!snapshot && ["connecting", "live", "stale"].includes(snapshot.stream_status);

  // J-32: a historical replay is "running" (so a speed change applies LIVE rather than only
  // staging the next Watch) when we are in Historical mode and an active engine snapshot is
  // mounted — any non-terminal stream status (a closed/failed stream has nothing to re-pace; a
  // change made while paused applies on resume, so paused counts as running). Read from the
  // canonical snapshot — never a client-side guess.
  const replayRunning =
    mode === "historical" &&
    !!watched &&
    !!snapshot &&
    !["closed", "failed"].includes(snapshot.stream_status);

  // Resolve the Historical window once, reading the date + time fields as ET wall-clock. Returns
  // null when the window is missing/invalid (end <= start) so both the disabled-Watch gate and the
  // submit guard share one definition of "valid window" — no divergence.
  function resolveHistoricalWindow(): { start: string; end: string } | null {
    const start = resolveEtWindowInstant(date, startTime);
    const end = resolveEtWindowInstant(date, endTime);
    if (!start || !end) return null;
    if (new Date(end).getTime() <= new Date(start).getTime()) return null;
    return { start, end };
  }

  const symbolValid = symbol.trim().length > 0;
  const windowValid = mode !== "historical" || resolveHistoricalWindow() !== null;
  const watchDisabled = !symbolValid || !windowValid;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // J-24: client-side inline validation BEFORE any round-trip — never a silent no-op. The
    // backend 422 remains the server-side backstop.
    if (!symbolValid) {
      setValidationError("Enter a ticker symbol.");
      return;
    }
    if (mode === "historical") {
      // A non-empty but malformed/out-of-range date gets its own explicit message (e.g.
      // 2026-02-31) rather than the generic window message — never a silent no-op.
      if (dateText.trim() && !isValidIsoDate(dateText)) {
        setValidationError("Enter a valid date as yyyy-MM-dd.");
        return;
      }
      const window = resolveHistoricalWindow();
      if (!window) {
        setValidationError("Choose a valid time window.");
        return;
      }
      setValidationError(null);
      // Send explicit `...Z` instants — never the old naive `${date}T${startTime}` the backend
      // then treated as UTC (the iter-2 load-bearing bug). (Data Contract row 12.)
      onWatch(symbol, { mode, start: window.start, end: window.end, speed });
    } else {
      setValidationError(null);
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
              onChange={(e) => onSymbolChange(e.target.value)}
              placeholder={symbolPlaceholder}
              className={`w-48 ${INPUT_CLASS}`}
            />
          ) : (
            // Live / Historical: real symbol search (J-13). Free-text entry still works.
            <SymbolSearch
              value={symbol}
              onChange={onSymbolChange}
              onPick={onSymbolChange}
              placeholder={symbolPlaceholder}
              ariaLabel={symbolLabel}
              inputClassName={`w-48 ${INPUT_CLASS}`}
            />
          )}

          {mode === "historical" && (
            <>
              {/* Custom yyyy-MM-dd date input — replaces the native <input type="date">, whose
                  rendering AND reading both follow the browser's locale/zone, the two things this
                  product fixes to one format and one clock. Entry is US-Eastern (see the ET label
                  below) and resolves to a tz-aware UTC instant via the row-12 resolver before the
                  fetch (no naive value, no silent UTC shift). An invalid value drives inline
                  validation (J-24) — never a silent no-op. */}
              <input
                type="text"
                inputMode="numeric"
                aria-label="Date (US Eastern)"
                value={dateText}
                onChange={(e) => onDateChange(e.target.value)}
                placeholder="yyyy-MM-dd"
                aria-invalid={dateText.trim().length > 0 && !isValidIsoDate(dateText)}
                className={`w-32 ${INPUT_CLASS} ${
                  dateText.trim().length > 0 && !isValidIsoDate(dateText)
                    ? "border-amber-500"
                    : ""
                }`}
              />
              {/* `step="1"` so the fields read HH:MM:SS — the same second-resolution shape every
                  date-time this product displays carries. */}
              <input
                type="time"
                step="1"
                aria-label="Start time (US Eastern)"
                value={startTime}
                onChange={(e) => onStartTimeChange(e.target.value)}
                className={`${INPUT_CLASS} [color-scheme:dark]`}
              />
              <span className="text-slate-600">–</span>
              <input
                type="time"
                step="1"
                aria-label="End time (US Eastern)"
                value={endTime}
                onChange={(e) => onEndTimeChange(e.target.value)}
                className={`${INPUT_CLASS} [color-scheme:dark]`}
              />
              {/* Explicit zone label: the date/time entry beside it is read as US EXCHANGE time and
                  resolved to a tz-aware UTC instant before the fetch (no silent UTC shift). */}
              <span
                aria-label="Entry timezone"
                title="Your date and time entry is read as US Eastern (exchange) time"
                className="font-mono text-xs text-slate-500"
              >
                ET
              </span>
              <select
                aria-label="Replay speed"
                value={speed}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  setSpeed(next);
                  // J-32: if a historical replay is already RUNNING (a snapshot is mounted for the
                  // watched ticker), apply the new speed LIVE via POST /watch/{ticker}/speed — NOT a
                  // re-Watch. Out-of-set values can't be chosen here (only REPLAY_SPEEDS are
                  // offered), and the backend 422 stays authoritative. When no watch is running yet
                  // the value is just the speed the next Watch submits with (unchanged behavior).
                  if (replayRunning) onSpeedChange(next);
                }}
                className={INPUT_CLASS}
              >
                {REPLAY_SPEEDS.map((s) => (
                  <option key={s} value={s}>
                    {s}×
                  </option>
                ))}
              </select>

              {/* US-session quick-picks (J-20). Each fills a valid RTH start/end in one click.
                  The fields are the exchange clock, so a pick's anchors go in verbatim and need no
                  local-equivalent annotation. Disabled until a date is chosen, so a pick can never
                  produce a malformed/empty window. */}
              <div
                role="group"
                aria-label="US session quick-picks"
                className="flex flex-wrap items-center gap-1.5"
              >
                {SESSION_QUICK_PICKS.map((pick) => (
                  <button
                    key={pick.key}
                    type="button"
                    onClick={() => applyQuickPick(pick)}
                    disabled={!date}
                    aria-label={pick.label}
                    title={
                      date ? `Fill the window with ${pick.label}` : "Choose a date first"
                    }
                    className={QUICK_PICK_CLASS}
                  >
                    {pick.label}
                  </button>
                ))}
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={watchDisabled}
            aria-disabled={watchDisabled}
            title={
              !symbolValid
                ? "Enter a ticker symbol"
                : !windowValid
                  ? "Choose a valid time window"
                  : "Watch this ticker"
            }
            className="rounded bg-emerald-600 px-3 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-400 active:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400 disabled:hover:bg-slate-700"
          >
            Watch
          </button>

          {/* Inline validation feedback (J-24): an always-visible hint while the input is invalid
              (so a Watch attempt is never a silent no-op), plus the explicit message set on a
              submit attempt. Amber = needs-attention, consistent with the palette. */}
          {(validationError || watchDisabled) && (
            <span
              role="status"
              aria-live="polite"
              data-testid="watch-validation"
              className="font-mono text-xs text-amber-400"
            >
              {validationError ??
                (!symbolValid ? "Enter a ticker symbol" : "Choose a valid time window")}
            </span>
          )}
        </form>

        {/* Live market-status indicator (row 8): the REAL session status from GET /market/clock,
            replacing the prior hardcoded "unavailable" stub. Mounted only in Live mode, so its
            poll is torn down on mode-change. */}
        {mode === "live" && <MarketStatusIndicator />}

        {watched && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-500">Watching</span>
            <span className="font-mono font-semibold text-slate-100">{watched}</span>
            {/* Pause / Resume (J-19): driven ONLY by the engine's canonical paused state — no
                client guess. Resume shows while paused; Pause shows while the feed is active
                (connecting / live / stale) and not paused. Both are hidden once the stream is
                closed/idle. Amber (paused = amber, consistent with the status dot). */}
            {paused ? (
              <button
                type="button"
                onClick={onResume}
                aria-label="Resume watching"
                className="rounded border border-amber-400/70 px-2.5 py-1 text-xs font-semibold text-amber-400 transition-colors hover:bg-amber-400/10 hover:text-amber-300 focus:outline-none focus:ring-1 focus:ring-amber-400 active:bg-amber-400/20"
              >
                Resume
              </button>
            ) : (
              pauseable && (
                <button
                  type="button"
                  onClick={onPause}
                  aria-label="Pause watching"
                  className="rounded border border-amber-400/70 px-2.5 py-1 text-xs font-semibold text-amber-400 transition-colors hover:bg-amber-400/10 hover:text-amber-300 focus:outline-none focus:ring-1 focus:ring-amber-400 active:bg-amber-400/20"
                >
                  Pause
                </button>
              )
            )}
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
            scenario:{" "}
            <span className="font-mono">{formatWatchedSource(snapshot.scenario)}</span>
          </div>
        )}

        {/* Feed-basis badge (J-67, data-contract row 29 + row 24 copy): the SERVED current-watch feed
            basis (sim | iex | sip) rendered VERBATIM beside the watched-source indicator, with the
            backend-owned IEX-vs-SIP disclosure line on the live IEX basis. Reads the snapshot's
            `data_feed` key only — never client-derived. Honest absence (no watch / no basis) => the
            badge renders nothing (it self-guards on `data_feed`). */}
        {watched && <FeedBasisBadge dataFeed={snapshot?.data_feed} />}

        <div className="ml-auto flex items-center gap-2 text-xs text-slate-400">
          {/* Canonical delivery-lag readout (row 14, J-64): the served snapshot's
              `delivery_lag_seconds`, mono numerics, display rounding only — beside the stream-status
              indicator. Reads the SAME value the `tape_lag_ok` check reads; honest "lag —" when the
              feeder has not stamped a lag yet (null/absent), never a fabricated 0. Shown only while a
              snapshot is present (a watched ticker). */}
          {watched && snapshot && (
            <span
              data-testid="delivery-lag"
              title="How far the processed tape trails real time (canonical, read-only)"
              className="font-mono text-slate-500"
            >
              {formatDeliveryLag(snapshot.delivery_lag_seconds)}
            </span>
          )}
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
