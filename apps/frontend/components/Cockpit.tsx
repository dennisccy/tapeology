import type { TapeSnapshot } from "@/lib/types";
import { QuotePanel } from "./QuotePanel";
import { RecentTradesPanel } from "./RecentTradesPanel";
import { FeaturesPanel } from "./FeaturesPanel";
import { TapeStatePanel } from "./TapeStatePanel";
import { ObservationsPanel } from "./ObservationsPanel";
import { EventLogPanel } from "./EventLogPanel";
import { ConnectingState } from "./IdleState";

export function Cockpit({ snapshot }: { snapshot: TapeSnapshot | null }) {
  if (!snapshot) return <ConnectingState />;

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
