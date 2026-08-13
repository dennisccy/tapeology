import type { DeskPlaybookBandContext, DeskPlaybookContext, DeskPlaybookSignal } from "./types";

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

// --- The band-context join (docs/playbook-detector-spec.md §6) -------------------------------------
// The served context lists its signals in the SAME record order the record itself serves them, but
// the two are paired by IDENTITY rather than by position, so a filtered or re-sorted table can
// never shift a location onto the wrong row.
//
// The key carries `side` on purpose, unlike `playbookSignalKey`: `range_trade` is one setup_id that
// fires BOTH sides, so a same-instant long and short on one symbol would otherwise collide and one
// row would inherit the other's wall.
function playbookContextKey(
  triggerTs: string | null,
  symbol: string | null,
  setupId: string | null,
  side: string | null,
): string {
  return `${triggerTs}:${symbol}:${setupId}:${side}`;
}

export function playbookSignalContextKey(signal: DeskPlaybookSignal): string {
  return playbookContextKey(signal.trigger_ts, signal.symbol, signal.setup_id, signal.side);
}

// `null` context (never read, or none served) yields an EMPTY map, so every lookup misses and every
// row honestly shows an em-dash rather than a borrowed or invented location.
export function playbookContextIndex(
  context: DeskPlaybookContext | null,
): Map<string, DeskPlaybookBandContext> {
  const index = new Map<string, DeskPlaybookBandContext>();
  for (const entry of context?.signals ?? []) {
    index.set(
      playbookContextKey(entry.trigger_ts, entry.symbol, entry.setup_id, entry.side),
      entry.band_context,
    );
  }
  return index;
}

// One wall cell's short label, rendered from SERVED fields only -- this derives no price, no
// distance, and no class. "inside 217.13–218.63 A" when the entry sits within a band on that side
// of the frame, "214.11–215.60 A · 93 bps" for a wall standing off it, an em-dash for nothing
// there. The containing band is shown on the side it sits on relative to its own edges, so one
// band never appears in both cells.
export function playbookWallLabel(
  context: DeskPlaybookBandContext | undefined,
  side: "below" | "above",
): string {
  if (!context) return "—";
  const containing = context.containing_band;
  if (containing !== null) {
    // An entry inside a band is bracketed by that band's own edges: it is the nearest structure in
    // BOTH directions, so it is named once, on the side the reader is looking at.
    const label = `inside ${containing.price_low.toFixed(2)}–${containing.price_high.toFixed(2)} ${containing.class ?? "—"}`;
    if (side === "below") return label;
  }
  const wall = side === "below" ? context.wall_below : context.wall_above;
  if (wall === null) return containing !== null && side === "above" ? "inside" : "—";
  return `${wall.price_low.toFixed(2)}–${wall.price_high.toFixed(2)} ${wall.class ?? "—"} · ${wall.distance_bps.toFixed(0)} bps`;
}
