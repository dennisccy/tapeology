"use client";

import { useState } from "react";
import { useTapeStream } from "@/lib/useTapeStream";
import { watchTicker, stopTicker } from "@/lib/api";
import { TopBar } from "@/components/TopBar";
import { Cockpit } from "@/components/Cockpit";
import { IdleState } from "@/components/IdleState";

export default function Page() {
  const [ticker, setTicker] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { snapshot, connStatus } = useTapeStream(ticker);

  async function handleWatch(raw: string) {
    const candidate = raw.trim().toUpperCase();
    if (!candidate) return;
    setError(null);
    const result = await watchTicker(candidate);
    if (result.ok) {
      setTicker(candidate);
    } else {
      setTicker(null);
      setError(result.error ?? "Could not watch ticker");
    }
  }

  async function handleStop() {
    if (!ticker) return;
    // Tell the backend to tear the engine down (DELETE /watch). Idle is the truthful end
    // state regardless of the result, so we return to idle even if the call fails: setTicker(null)
    // renders <IdleState/> and triggers useTapeStream's cleanup, which closes the WS client-side
    // (the "no further updates" mechanism — it must not depend on the server closing the socket).
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
        onWatch={handleWatch}
        onStop={handleStop}
        error={error}
      />
      <main className="mx-auto max-w-7xl px-4 py-6">
        {ticker ? <Cockpit snapshot={snapshot} /> : <IdleState />}
      </main>
      <footer className="mx-auto max-w-7xl px-4 pb-8 text-xs text-slate-600">
        Tapeology reads and classifies the live tape for a single ticker. Descriptive only —
        not trading advice.
      </footer>
    </div>
  );
}
