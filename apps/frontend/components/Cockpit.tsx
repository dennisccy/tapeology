import type { TapeSnapshot } from "@/lib/types";
import { QuotePanel } from "./QuotePanel";
import { RecentTradesPanel } from "./RecentTradesPanel";
import { FeaturesPanel } from "./FeaturesPanel";
import { TapeStatePanel } from "./TapeStatePanel";
import { ObservationsPanel } from "./ObservationsPanel";
import { EventLogPanel } from "./EventLogPanel";
import { ConnectingState, WaitingState } from "./IdleState";

export function Cockpit({
  snapshot,
}: {
  snapshot: TapeSnapshot | null;
}) {
  if (!snapshot) return <ConnectingState />;

  // Guard against ever rendering the full panel grid for a connected-but-empty tape. When the
  // canonical engine status reads `waiting` (stream open, no first event), show the explicit
  // waiting treatment IN PLACE OF blank panels — never a confident `live` over an empty tape. The
  // page also routes `waiting`/`failed` (it has the data-source mode for the label); this is the
  // backstop so the Cockpit itself can't display a mute grid. Read verbatim — no client guess.
  if (snapshot.stream_status === "waiting") {
    return <WaitingState symbol={snapshot.ticker} />;
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      <TapeStatePanel
        state={snapshot.tape_state}
        confidence={snapshot.confidence}
        warm={snapshot.warm}
      />
      <QuotePanel market={snapshot.market} />
      <FeaturesPanel features={snapshot.features} primaryWindow={snapshot.primary_window} />
      <RecentTradesPanel trades={snapshot.recent_trades} />
      <ObservationsPanel observations={snapshot.observations} />
      <EventLogPanel log={snapshot.event_log} />
    </div>
  );
}
