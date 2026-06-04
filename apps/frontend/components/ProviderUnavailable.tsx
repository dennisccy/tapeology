import { Panel } from "./Panel";
import { formatMarketTime } from "@/lib/datetime";
import type { DataSourceMode, FailureReason } from "@/lib/types";

// Honest non-cockpit state (J-14): rendered IN PLACE OF the cockpit when a Live / Historical
// Watch is refused. A distinct panel per real-data failure reason — never a fabricated cockpit,
// never a silent fall-back to Simulated. Amber = unavailable / unclear / honest-fail (the
// load-bearing color semantics). The emphasized `phrase` is the exact wording each reason
// surfaces (it matches the backend `detail`), so the message is honest and verifiable.

type Copy = { title: string; phrase: string; help: string };

function copyFor(reason: FailureReason, mode?: DataSourceMode, nextOpen?: string): Copy {
  const modeLabel = mode === "historical" ? "Historical" : "Live";
  switch (reason) {
    case "market_closed":
      return {
        title: "Market is closed",
        phrase: "market is closed",
        help:
          (nextOpen
            ? `The US market is closed right now — it next opens ${formatMarketTime(nextOpen)}. `
            : "The US market is closed right now. ") +
          "Live streaming resumes during market hours. No tape is shown — Tapeology never " +
          "fabricates data to fill the gap. You can replay a past session with Historical instead.",
      };
    case "symbol_not_tradable":
      return {
        title: "Symbol not tradable",
        phrase: "not a tradable symbol",
        help:
          "That symbol isn’t a tradable US equity at the data provider. Check the spelling or " +
          "use the search box to pick a valid symbol. No tape is shown — Tapeology never " +
          "fabricates data to fill the gap.",
      };
    case "no_data_for_window":
      return {
        title: "No data for that window",
        phrase: "no data for that window",
        help:
          "The provider returned no trades for that symbol over the date/time window you chose. " +
          "Try a different window during regular market hours. No tape is shown — Tapeology " +
          "never fabricates data to fill the gap.",
      };
    case "provider_unavailable":
    default:
      return {
        title: "Real-data provider unavailable",
        phrase: "real-data provider unavailable",
        help:
          `${modeLabel} data needs vendor API credentials, which are not configured. No tape is ` +
          "shown — Tapeology never fabricates data to fill the gap. Set the Alpaca API key and " +
          "secret in the backend environment, or switch to Simulated to use the built-in scenarios.",
      };
  }
}

export function ProviderUnavailable({
  reason,
  mode,
  nextOpen,
}: {
  reason: FailureReason;
  mode?: DataSourceMode;
  nextOpen?: string;
}) {
  const copy = copyFor(reason, mode, nextOpen);
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <Panel title={copy.title} className="max-w-lg border-amber-500/40 bg-amber-500/5">
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="text-4xl text-amber-400" aria-hidden="true">
            ⚠
          </div>
          <p className="text-base font-semibold text-amber-300">{copy.phrase}</p>
          <p className="max-w-md text-sm text-slate-400">{copy.help}</p>
        </div>
      </Panel>
    </div>
  );
}
