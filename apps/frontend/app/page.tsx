"use client";

import { useState } from "react";
import { useTapeStream } from "@/lib/useTapeStream";
import { watchTicker } from "@/lib/api";
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

  return (
    <div className="min-h-screen">
      <TopBar
        watched={ticker}
        snapshot={snapshot}
        connStatus={connStatus}
        onWatch={handleWatch}
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
