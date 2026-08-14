import type {
  DeskPlaybookBandContext,
  DeskPlaybookContext,
  DeskPlaybookSignal,
  DeskPlaybookWall,
} from "./types";

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

function wallText(wall: DeskPlaybookWall | null): string {
  if (wall === null) return "—";
  return `${wall.price_low.toFixed(2)}–${wall.price_high.toFixed(2)} ${wall.class ?? "—"} · ${wall.distance_bps.toFixed(0)} bps`;
}

// One wall cell's short label, rendered from SERVED fields only -- this derives no price, no
// distance, and no class.
//
// The slot is TRADE-RELATIVE, not geometric: `behind` is the wall the trade leans on (below a long,
// above a short) and `ahead` is the one its room is measured to. Selecting between the two served
// wall objects by the row's own served `side` is the same move the side-matched drawdown column
// already makes -- a choice between served values, never arithmetic.
//
// Geometric below/above headers were tried first and read wrong for shorts: an entry INSIDE a band
// is the nearest structure in BOTH directions, so naming it once (to avoid printing one band in two
// cells) had to pick a column, and picking "below" silently assumed every row was a long. A short
// fading a resistance band it sits inside then found that band in neither cell. Behind/ahead has one
// meaning per row for both sides, and matches the frame's own served readings (`backing_bps`,
// `headroom_bps`, `room_r`), the caption, and the filter's "at a wall behind".
export function playbookWallLabel(
  context: DeskPlaybookBandContext | undefined,
  side: string,
  slot: "behind" | "ahead",
): string {
  if (!context) return "—";
  const behind = side === "long" ? context.wall_below : context.wall_above;
  const ahead = side === "long" ? context.wall_above : context.wall_below;
  if (slot === "ahead") return wallText(ahead);
  const containing = context.containing_band;
  if (containing !== null) {
    // Inside a band the trade is backed AT it -- the served `backing_bps` is 0.0 -- so the band
    // itself is what stands behind the trade, whichever way the trade faces.
    return `inside ${containing.price_low.toFixed(2)}–${containing.price_high.toFixed(2)} ${containing.class ?? "—"}`;
  }
  return wallText(behind);
}

// The ONE drill-in URL both playbook tables build. Extracted so the flat signals table and the
// per-setup occurrence list can never send an operator to two different charts for one signal:
// `asof` positions the chart and the band map, `tf` names the timeframe the setup was detected on,
// and the immutable (record id, signal key) pair is what makes /structure draw THIS occurrence's
// own recorded outline rather than re-deriving one.
export function playbookDrillInHref(
  signal: DeskPlaybookSignal,
  recordId: string,
  detectTimeframe: string,
): string {
  return (
    `/structure?symbol=${encodeURIComponent(signal.symbol)}` +
    `&asof=${encodeURIComponent(signal.trigger_ts)}` +
    (detectTimeframe ? `&tf=${encodeURIComponent(detectTimeframe)}` : "") +
    `&playbook=${encodeURIComponent(recordId)}` +
    `&signal=${encodeURIComponent(playbookSignalKey(signal))}`
  );
}
