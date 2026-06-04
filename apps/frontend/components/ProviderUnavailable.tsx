import { Panel } from "./Panel";

// Honest non-cockpit state (J-14, no-credentials path): rendered IN PLACE OF the cockpit when a
// Live / Historical Watch returns 503 provider-unavailable. Never a fabricated cockpit, never a
// silent fall-back to Simulated. Amber = unavailable/unclear (load-bearing color semantics).
export function ProviderUnavailable({ mode }: { mode: "live" | "historical" }) {
  const modeLabel = mode === "live" ? "Live" : "Historical";
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <Panel
        title="Real-data provider unavailable"
        className="max-w-lg border-amber-500/40 bg-amber-500/5"
      >
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="text-4xl text-amber-400" aria-hidden="true">
            ⚠
          </div>
          <p className="text-base font-semibold text-amber-300">
            real-data provider unavailable
          </p>
          <p className="max-w-md text-sm text-slate-400">
            {modeLabel} data needs vendor API credentials, which are not configured. No tape is
            shown — Tapeology never fabricates data to fill the gap. Set the Alpaca API key and
            secret in the backend environment, or switch to{" "}
            <span className="font-semibold text-slate-200">Simulated</span> to use the built-in
            scenarios.
          </p>
        </div>
      </Panel>
    </div>
  );
}
