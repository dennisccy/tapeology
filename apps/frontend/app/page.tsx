"use client";

import { useState } from "react";
import { useTapeStream } from "@/lib/useTapeStream";
import { watchTicker, stopTicker, pauseTicker, resumeTicker } from "@/lib/api";
import type { DataSourceMode, FailureReason, WatchParams } from "@/lib/types";
import { TopBar } from "@/components/TopBar";
import { Cockpit } from "@/components/Cockpit";
import { PriceChart } from "@/components/PriceChart";
import { IdleState } from "@/components/IdleState";
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
  // When a real-mode Watch is honestly refused, show the distinct non-cockpit panel for that
  // reason in place of the cockpit — never a fabricated cockpit, never a fall-back to Simulated.
  const [failure, setFailure] = useState<{
    reason: FailureReason;
    mode: DataSourceMode;
    nextOpen?: string;
  } | null>(null);
  const { snapshot, connStatus } = useTapeStream(ticker);

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
    if (!candidate) return;
    setError(null);
    setFailure(null);
    await teardownActiveWatch();

    const result = await watchTicker(candidate, params);
    if (result.ok) {
      setTicker(candidate);
    } else if (isHonestReason(result.reason)) {
      setTicker(null);
      setFailure({ reason: result.reason, mode: params.mode, nextOpen: result.nextOpen });
    } else {
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
    setMode(next);
  }

  async function handleStop() {
    if (!ticker) return;
    // Idle is the truthful end state regardless of the result, so we return to idle even if the
    // call fails: setTicker(null) renders <IdleState/> and triggers useTapeStream's cleanup,
    // which closes the WS client-side (it must not depend on the server closing the socket).
    await stopTicker(ticker);
    setTicker(null);
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

  return (
    <div className="min-h-screen">
      <TopBar
        watched={ticker}
        snapshot={snapshot}
        connStatus={connStatus}
        mode={mode}
        onModeChange={handleModeChange}
        onWatch={handleWatch}
        onStop={handleStop}
        onPause={handlePause}
        onResume={handleResume}
        error={error}
      />
      <main className="mx-auto max-w-7xl px-4 py-6">
        {/* Tape-state prediction chart — above the cockpit, for Simulated + Historical only
            (hidden for Live, per the blueprint IA). Reads GET …/history verbatim. */}
        {ticker && (mode === "sim" || mode === "historical") && (
          <PriceChart ticker={ticker} />
        )}
        {ticker ? (
          <Cockpit snapshot={snapshot} />
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
