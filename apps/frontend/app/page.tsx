"use client";

import { useState } from "react";
import { useTapeStream } from "@/lib/useTapeStream";
import { watchTicker, stopTicker } from "@/lib/api";
import type { DataSourceMode, FailureReason, WatchParams } from "@/lib/types";
import { TopBar } from "@/components/TopBar";
import { Cockpit } from "@/components/Cockpit";
import { IdleState } from "@/components/IdleState";
import { ProviderUnavailable } from "@/components/ProviderUnavailable";

// Real-data failures that get their own distinct honest non-cockpit panel (row 9). Any other
// failure (e.g. the live creds-present "not yet available", or a bad sim ticker) falls through
// to the generic error banner.
const HONEST_REASONS: FailureReason[] = [
  "provider_unavailable",
  "symbol_not_tradable",
  "no_data_for_window",
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
  const [failure, setFailure] = useState<{ reason: FailureReason; mode: DataSourceMode } | null>(
    null,
  );
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
      setFailure({ reason: result.reason, mode: params.mode });
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
        error={error}
      />
      <main className="mx-auto max-w-7xl px-4 py-6">
        {ticker ? (
          <Cockpit snapshot={snapshot} />
        ) : failure ? (
          <ProviderUnavailable reason={failure.reason} mode={failure.mode} />
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
