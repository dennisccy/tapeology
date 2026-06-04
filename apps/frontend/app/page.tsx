"use client";

import { useState } from "react";
import { useTapeStream } from "@/lib/useTapeStream";
import { watchTicker, stopTicker } from "@/lib/api";
import type { DataSourceMode, WatchParams } from "@/lib/types";
import { TopBar } from "@/components/TopBar";
import { Cockpit } from "@/components/Cockpit";
import { IdleState } from "@/components/IdleState";
import { ProviderUnavailable } from "@/components/ProviderUnavailable";

export default function Page() {
  const [ticker, setTicker] = useState<string | null>(null);
  const [mode, setMode] = useState<DataSourceMode>("sim");
  const [error, setError] = useState<string | null>(null);
  // When a real-mode Watch is honestly refused (503), show the explicit "provider unavailable"
  // panel in place of the cockpit — never a fabricated cockpit, never a fall-back to Simulated.
  const [unavailableMode, setUnavailableMode] = useState<"live" | "historical" | null>(null);
  const { snapshot, connStatus } = useTapeStream(ticker);

  // Lifecycle hardening (iter-0 lesson): tear down any active watch (backend DELETE + close the
  // WS) BEFORE starting a new one, so a source/symbol switch never leaves an orphaned backend
  // watch — or, once the live provider lands, a leaked vendor socket. setTicker(null) triggers
  // useTapeStream's cleanup, which closes the WebSocket client-side.
  async function teardownActiveWatch() {
    if (!ticker) return;
    await stopTicker(ticker);
    setTicker(null);
  }

  async function handleWatch(rawSymbol: string, params: WatchParams) {
    const candidate = rawSymbol.trim().toUpperCase();
    if (!candidate) return;
    setError(null);
    setUnavailableMode(null);
    await teardownActiveWatch();

    const result = await watchTicker(candidate, params);
    if (result.ok) {
      setTicker(candidate);
    } else if (result.providerUnavailable) {
      setTicker(null);
      setUnavailableMode(params.mode === "historical" ? "historical" : "live");
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
    setUnavailableMode(null);
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
        ) : unavailableMode ? (
          <ProviderUnavailable mode={unavailableMode} />
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
