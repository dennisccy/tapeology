import type { Hint, TapeSnapshot } from "@/lib/types";
import { QuotePanel } from "./QuotePanel";
import { RecentTradesPanel } from "./RecentTradesPanel";
import { FeaturesPanel } from "./FeaturesPanel";
import { TapeStatePanel } from "./TapeStatePanel";
import { HintDock } from "./HintDock";
import { ObservationsPanel } from "./ObservationsPanel";
import { EventLogPanel } from "./EventLogPanel";
import { ConnectingState, WaitingState } from "./IdleState";

export function Cockpit({
  snapshot,
  onHintDeclare,
}: {
  snapshot: TapeSnapshot | null;
  // Prefill the thesis declare form from an active hint's declare affordance (J-65). Lifted to the
  // page so the dock (under the tape-state panel) can drive the thesis strip (above the grid).
  onHintDeclare?: (hint: Hint) => void;
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
      {/* The tape-state panel and — directly UNDER it (its pre-registered blueprint home, J-65) — the
          setup-forming hint dock. The dock is ABSENT unless a hint is active, so this cell is just the
          tape-state panel on an idle/unclear tape (no empty-state chrome). Reads the snapshot's `hint`
          key verbatim. */}
      <div className="flex flex-col gap-4">
        <TapeStatePanel
          state={snapshot.tape_state}
          confidence={snapshot.confidence}
          warm={snapshot.warm}
        />
        <HintDock
          hint={snapshot.hint}
          thesisActive={!!snapshot.thesis}
          onDeclare={(h) => onHintDeclare?.(h)}
        />
      </div>
      <QuotePanel market={snapshot.market} />
      <FeaturesPanel features={snapshot.features} primaryWindow={snapshot.primary_window} />
      <RecentTradesPanel trades={snapshot.recent_trades} />
      <ObservationsPanel observations={snapshot.observations} />
      <EventLogPanel log={snapshot.event_log} />
    </div>
  );
}
