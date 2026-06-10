"use client";

import { useState } from "react";
import { useTapeStream } from "@/lib/useTapeStream";
import {
  watchTicker,
  stopTicker,
  pauseTicker,
  resumeTicker,
  setReplaySpeed,
} from "@/lib/api";
import type { DataSourceMode, FailureReason, WatchParams } from "@/lib/types";
import { TopBar } from "@/components/TopBar";
import { Cockpit } from "@/components/Cockpit";
import { PriceChart } from "@/components/PriceChart";
import { ThesisStrip } from "@/components/ThesisStrip";
import {
  IdleState,
  ConnectingState,
  StreamFailedState,
  WaitingState,
} from "@/components/IdleState";
import { ProviderUnavailable } from "@/components/ProviderUnavailable";

// Real-data failures that get their own distinct honest non-cockpit panel (row 9). Any other
// failure (e.g. the live creds-present "not yet available", or a bad sim ticker) falls through
// to the generic error banner.
const HONEST_REASONS: FailureReason[] = [
  "provider_unavailable",
  "symbol_not_tradable",
  "no_data_for_window",
  "market_closed",
];

function isHonestReason(reason: string | undefined): reason is FailureReason {
  return !!reason && (HONEST_REASONS as string[]).includes(reason);
}

export default function Page() {
  const [ticker, setTicker] = useState<string | null>(null);
  const [mode, setMode] = useState<DataSourceMode>("sim");
  const [error, setError] = useState<string | null>(null);
  // Pending/connecting acknowledgement (J-21): set SYNCHRONOUSLY the instant Watch is clicked —
  // before the teardown/watch round-trip — so the cockpit immediately leaves idle and shows
  // "Connecting to <SYMBOL>…". Cleared/replaced when the watch resolves (cockpit / honest panel /
  // error). It carries the symbol so the acknowledgement is distinct per click, in every mode.
  const [pending, setPending] = useState<string | null>(null);
  // When a real-mode Watch is honestly refused, show the distinct non-cockpit panel for that
  // reason in place of the cockpit — never a fabricated cockpit, never a fall-back to Simulated.
  const [failure, setFailure] = useState<{
    reason: FailureReason;
    mode: DataSourceMode;
    nextOpen?: string;
  } | null>(null);
  const { snapshot, connStatus, connError } = useTapeStream(ticker);

  // Lifecycle hardening (iter-0 lesson): tear down any active watch (backend DELETE + close the
  // WS) BEFORE starting a new one, so a source/symbol switch never leaves an orphaned backend
  // watch or a leaked replay feeder. setTicker(null) triggers useTapeStream's cleanup, which
  // closes the WebSocket client-side.
  async function teardownActiveWatch() {
    if (!ticker) return;
    await stopTicker(ticker);
    setTicker(null);
  }

  async function handleWatch(rawSymbol: string, params: WatchParams) {
    const candidate = rawSymbol.trim().toUpperCase();
    // J-24 client-side backstop: an empty/whitespace symbol is an immediate inline validation,
    // never a silent no-op. (TopBar also disables Watch + shows the inline message; this guards
    // the handler too.) The historical missing/invalid-window case is validated in TopBar before
    // it ever calls onWatch, and the backend 422 remains the server-side backstop.
    if (!candidate) {
      setError("Enter a ticker symbol to watch.");
      return;
    }
    setError(null);
    setFailure(null);
    // J-21: acknowledge the click NOW — synchronously, before the awaited teardown/watch round-
    // trip — so the idle screen never lingers after a valid Watch click in any mode.
    setPending(candidate);
    await teardownActiveWatch();

    const result = await watchTicker(candidate, params);
    setPending(null);
    if (result.ok) {
      setTicker(candidate);
    } else if (isHonestReason(result.reason)) {
      setTicker(null);
      setFailure({ reason: result.reason, mode: params.mode, nextOpen: result.nextOpen });
    } else {
      // Everything else — a client-side timeout (`provider_timeout`), an unreachable backend, or
      // a bad sim ticker — resolves to the explicit error banner (never a frozen spinner).
      setTicker(null);
      setError(result.error ?? "Could not watch ticker");
    }
  }

  // Switching the data source tears down the prior watch and returns the cockpit area to idle
  // before revealing the new mode's controls.
  async function handleModeChange(next: DataSourceMode) {
    if (next === mode) return;
    await teardownActiveWatch();
    setError(null);
    setFailure(null);
    setPending(null);
    setMode(next);
  }

  async function handleStop() {
    if (!ticker) return;
    // Idle is the truthful end state regardless of the result, so we return to idle even if the
    // call fails: setTicker(null) renders <IdleState/> and triggers useTapeStream's cleanup,
    // which closes the WS client-side (it must not depend on the server closing the socket).
    await stopTicker(ticker);
    setTicker(null);
    setPending(null);
    setError(null);
  }

  // Pause (J-19): freeze the watch WITHOUT teardown — the deliberate opposite of Stop. It MUST NOT
  // call stopTicker and MUST NOT setTicker(null): the cockpit + chart stay mounted, and the engine
  // (whose feeder stays alive) keeps the WS open, pushing the frozen snapshot now carrying
  // paused=true / stream_status="paused". The UI flips to the PAUSED indicator with NO client-side
  // guess (it reads the canonical paused state), and the cockpit/chart freeze because the engine
  // accrues no new snapshots/candles while paused.
  async function handlePause() {
    if (!ticker) return;
    const result = await pauseTicker(ticker);
    if (!result.ok) setError(result.error ?? "Could not pause watch");
  }

  // Resume (J-19): continue the paused watch. The backend clears paused and restores the prior
  // stream_status (never a fabricated "live"); feeding continues with no synthesized catch-up. The
  // restored status flows back in over the WS stream — again, no client-side recompute.
  async function handleResume() {
    if (!ticker) return;
    const result = await resumeTicker(ticker);
    if (!result.ok) setError(result.error ?? "Could not resume watch");
  }

  // Change the replay speed of the RUNNING historical replay (J-32): POST /watch/{ticker}/speed —
  // NOT a re-Watch. The backend re-paces the in-progress replay (no re-fetch / restart / teardown),
  // so the cockpit + chart continue from their current position at the new cadence; the canonical
  // engine values are unchanged (speed is delivery-pacing only). A failure surfaces in the banner.
  async function handleSpeedChange(speed: number) {
    if (!ticker) return;
    const result = await setReplaySpeed(ticker, speed);
    if (!result.ok) setError(result.error ?? "Could not change replay speed");
  }

  // A connect failure surfaced by the stream hook (J-23): the initial snapshot fetch or the WS
  // failed before any frame arrived (pre-snapshot). Surface it via the error banner (and a failure
  // cockpit treatment) within a bounded time — never a frozen "Connecting…".
  const streamFailed = !!ticker && connStatus === "failed";
  // Post-connect lifecycle states owned by the canonical engine snapshot (J-25/J-26/J-27): the
  // feeder connected, then either has no first event yet (`waiting`) or RAISED (`failed`). These are
  // distinct from the pre-snapshot `connStatus === "failed"` above — they ride the snapshot's
  // row-6 `stream_status`, read VERBATIM (no client-side "is the tape empty?" guess). An empty
  // cold-start snapshot now arrives as `waiting`, so it can never short-circuit into the full
  // cockpit grid as a settled `live` connection.
  const snapshotWaiting = !!ticker && snapshot?.stream_status === "waiting";
  const snapshotFailed = !!ticker && snapshot?.stream_status === "failed";
  // A snapshot can briefly read the pre-open `connecting` rung if it is fetched in the instant
  // before the feeder sets `waiting`. That is still an empty, not-yet-connected tape — render the
  // connecting acknowledgement, NOT the full cockpit grid (the cold-start snapshot must never
  // short-circuit into a settled `live` cockpit).
  const snapshotConnecting = !!ticker && snapshot?.stream_status === "connecting";
  // The dot/status while the pending acknowledgement is showing reads "connecting" (J-21); once a
  // real watch is mounted the hook's connStatus drives it.
  const effectiveConnStatus = pending && !ticker ? "connecting" : connStatus;
  const bannerError =
    error ??
    (streamFailed ? connError : null) ??
    (snapshotFailed ? "The tape feed failed after connecting. No tape is shown." : null);

  return (
    <div className="min-h-screen">
      <TopBar
        watched={ticker ?? pending}
        snapshot={snapshot}
        connStatus={effectiveConnStatus}
        mode={mode}
        onModeChange={handleModeChange}
        onWatch={handleWatch}
        onStop={handleStop}
        onPause={handlePause}
        onResume={handleResume}
        onSpeedChange={handleSpeedChange}
        error={bannerError}
      />
      <main className="mx-auto max-w-7xl px-4 py-6">
        {/* Tape-state prediction chart — above the cockpit, for Simulated + Historical only
            (hidden for Live, per the blueprint IA). Hidden while the stream has failed (pre- or
            post-connect) or is still waiting for its first event — there is nothing to chart yet,
            and the chart must never invent candles. Reads GET …/history verbatim. */}
        {ticker &&
          !streamFailed &&
          !snapshotFailed &&
          !snapshotWaiting &&
          !snapshotConnecting &&
          (mode === "sim" || mode === "historical") && <PriceChart ticker={ticker} />}
        {pending && !ticker ? (
          // J-21: pending acknowledgement — shown the instant Watch is clicked, before any data.
          <ConnectingState symbol={pending} />
        ) : streamFailed ? (
          // J-23: an explicit, distinct PRE-snapshot connect-failure state (no frozen spinner).
          <StreamFailedState message={connError ?? undefined} />
        ) : snapshotFailed ? (
          // J-27: a POST-connect feeder failure surfaced by the canonical snapshot — the feeder
          // raised after connecting. Reuse the same explicit failure treatment + banner; never a
          // mute/blank `live` cockpit and never frozen at "Connecting…".
          <StreamFailedState message="The tape feed failed after connecting. No tape is shown." />
        ) : snapshotWaiting ? (
          // J-26: connected but no first event yet — an explicit waiting treatment labelled with
          // the symbol + mode, IN PLACE OF blank panels under a misleading status.
          <WaitingState symbol={ticker ?? undefined} mode={mode} />
        ) : snapshotConnecting ? (
          // Pre-open snapshot (transient, before the feeder sets `waiting`): the connecting
          // acknowledgement, never the full grid over an empty tape.
          <ConnectingState symbol={ticker ?? undefined} />
        ) : ticker ? (
          <>
            {/* Thesis strip (J-38) — between the price chart and the panel grid. Shown only once
                the cockpit grid itself is shown (a live/settled snapshot), so it never appears over
                a waiting/connecting/failed tape. Idle = one declare line (nothing else moves);
                active = the WS `thesis` projection rendered verbatim. */}
            {snapshot &&
              snapshot.stream_status !== "waiting" &&
              snapshot.stream_status !== "connecting" &&
              snapshot.stream_status !== "failed" && (
                <ThesisStrip ticker={ticker} thesis={snapshot.thesis} />
              )}
            <Cockpit snapshot={snapshot} />
          </>
        ) : failure ? (
          <ProviderUnavailable
            reason={failure.reason}
            mode={failure.mode}
            nextOpen={failure.nextOpen}
          />
        ) : (
          <IdleState />
        )}
      </main>
      <footer className="mx-auto max-w-7xl px-4 pb-8 text-xs text-slate-600">
        Tapeology reads and classifies the live tape for a single ticker. Descriptive only —
        not trading advice.
      </footer>
    </div>
  );
}
