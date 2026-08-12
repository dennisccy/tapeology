import type { DeskPlaybookSignal } from "./types";

// Shared playbook-signal identity and labelling helpers, used by BOTH the /desk Playbook section
// and the /structure page's playbook drill-in. Pure reads over an already-served signal — they
// derive no price, no level, no measure. Lifted verbatim out of app/desk/page.tsx so the two pages
// share one copy (no second signal-key literal), the way lib/timeframes.ts was lifted out of
// app/structure/page.tsx for the cockpit.

export function playbookSetupLabel(setupId: string): string {
  if (setupId === "open_high_break") return "Open-High Break";
  if (setupId === "open_low_break") return "Open-Low Break";
  if (setupId === "jbe") return "Jump-Base Explosion";
  if (setupId === "dbi") return "Drop-Base Implosion";
  if (setupId === "cup_handle") return "Cup and Handle";
  if (setupId === "capitulation") return "Capitulation";
  if (setupId === "range_trade") return "Range Trade";
  if (setupId === "double_top") return "Double Top";
  if (setupId === "double_bottom") return "Double Bottom";
  return setupId;
}

// The (setup_id, side) pool a signal belongs to — the SAME key `compute_playbook` itself pools by
// (apps/backend/app/research/desk_playbook.py's `f"{signal['setup_id']}:{signal['side']}"`), so a
// summary row and the occurrences listed under it can never disagree about membership.
export function playbookPoolKey(signal: DeskPlaybookSignal): string {
  return `${signal.setup_id}:${signal.side}`;
}

// The signals table's own row identity -- (trigger_ts, symbol, setup_id) is unique within one
// record even once a future detector (J-04) can fire more than once for the same symbol in a
// session, since each firing has its own trigger_ts. Also the `signal=` term of the /structure
// drill-in link, so a row and its link can never identify different signals.
export function playbookSignalKey(signal: DeskPlaybookSignal): string {
  return `${signal.trigger_ts}:${signal.symbol}:${signal.setup_id}`;
}
