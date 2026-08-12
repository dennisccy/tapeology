import type {
  DeskPlaybookAnchorPoint,
  DeskPlaybookAnchorSpan,
  DeskPlaybookAnchors,
  DeskPlaybookSignal,
} from "./types";
import type { ChartShapeSpec } from "./chartShapes";
import { chartShapeTimeSpan } from "./chartShapes";
import { playbookSetupLabel } from "./playbook";

// One served playbook signal in, ready-to-draw display specs out.
//
// PRESENTATION MAPPING ONLY. Every price below is a verbatim copy of a served field — an anchor's
// own `price`, or the signal's `entry`/`invalidation_price`/`price_low`/`price_high`. This module
// computes no midpoint, no width, no ratio, no level, nothing the detector did not already record.
// The single derivation it performs is a TIME UNIT conversion (`ts` is already epoch seconds, so
// even that is usually a copy), and the one decision it makes is which mark shape expresses which
// anchor — a display choice, not an analytic one.
//
// The colours live here rather than in StructureChart because they belong to the setup vocabulary,
// not to the chart. The chart's own palette is already spent: slate for raw levels, emerald/rose
// for tradable bands and candles. Amber is the product's established disclosure/attention family
// and collides with none of them; violet/purple separates the two reference LEVELS from the
// formation outline itself.
const SHAPE_OUTLINE = "#fbbf24"; // amber-400  — box strokes, formation polylines
const SHAPE_FILL = "rgba(251, 191, 36, 0.07)"; // amber-400, faint — box fill, under the candles
const SHAPE_PIVOT = "#fcd34d"; // amber-300  — pivots, zone touches, the climax bar
const SHAPE_TRIGGER = "#f59e0b"; // amber-500 — the trigger bar itself
const SHAPE_ENTRY = "#a78bfa"; // violet-400 — entry
const SHAPE_INVALIDATION = "#c084fc"; // purple-400 — invalidation
const SHAPE_EXTENT = "#64748b"; // slate-500  — the partial state's price-extent lines

// The formation outline is 2px on purpose. StructureChart holds every REFERENCE line to 1px (a
// guard pins it) so the band/level lines stay quiet at small canvas heights; a formation outline is
// a different class of mark and has to separate from them. Entry and invalidation ARE reference
// lines, so they stay 1px, honouring that rule where it applies.
const OUTLINE_WIDTH = 2;
const LEVEL_WIDTH = 1;

export interface PlaybookShapeLegendItem {
  swatch: string;
  label: string;
}

export interface PlaybookShapeResult {
  /** Ready-to-draw specs, in draw order (fills first, marks last). */
  shapes: ChartShapeSpec[];
  /** The on-chart badge naming the setup. */
  caption: string;
  /** The formation's own time extent, for the chart's focus range; `null` when nothing is anchored. */
  span: { fromTs: number; toTs: number } | null;
  /** `"full"` — every anchor this family draws from was recorded and parsed.
   *  `"partial"` — the outline is not on file; only the always-served levels could be drawn.
   *  `"absent"` — nothing drawable at all. */
  completeness: "full" | "partial" | "absent";
  /** The exact sentence to render for a non-`"full"` result; `null` when full. */
  note: string | null;
  /** Only the mark families actually drawn, so the legend never lists something absent. */
  legend: PlaybookShapeLegendItem[];
}

const NO_ANCHORS_NOTE =
  "This record was computed before shape anchors were recorded, so the setup's outline is not on " +
  "file. Its trigger, entry, invalidation and price extent are drawn as levels instead.";

const MISMATCHED_ANCHORS_NOTE =
  "This signal's recorded anchors name a different setup than the signal itself, so no outline is " +
  "drawn — the levels below are the signal's own served prices.";

/** A finite number, or `null`. Anchors arrive as JSON, and a malformed one is DROPPED rather than
 *  coerced to 0 — a shape missing a piece degrades honestly; a shape drawn at price 0 lies. */
function finite(value: number | undefined): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function point(anchor: DeskPlaybookAnchorPoint | undefined): ChartShapeSpec | null {
  if (!anchor) return null;
  const time = finite(anchor.ts);
  const price = finite(anchor.price);
  if (time === null || price === null) return null;
  return { kind: "dot", time, price, color: SHAPE_PIVOT, radius: 4 };
}

function polyline(anchors: (DeskPlaybookAnchorPoint | undefined)[]): ChartShapeSpec | null {
  const points = [];
  for (const anchor of anchors) {
    if (!anchor) return null;
    const time = finite(anchor.ts);
    const price = finite(anchor.price);
    if (time === null || price === null) return null;
    points.push({ time, price });
  }
  if (points.length < 2) return null;
  return { kind: "polyline", points, color: SHAPE_OUTLINE, lineWidth: OUTLINE_WIDTH };
}

function box(
  span: DeskPlaybookAnchorSpan | undefined,
  priceLow: number,
  priceHigh: number,
  label: string,
): ChartShapeSpec | null {
  if (!span) return null;
  const from = finite(span.from_ts);
  const to = finite(span.to_ts);
  if (from === null || to === null) return null;
  return {
    kind: "box", from, to, priceLow, priceHigh, color: SHAPE_OUTLINE, fill: SHAPE_FILL,
    lineWidth: OUTLINE_WIDTH, label,
  };
}

function segment(
  fromAnchor: DeskPlaybookAnchorPoint | undefined,
  toAnchor: DeskPlaybookAnchorPoint | undefined,
  price: number,
  label: string,
): ChartShapeSpec | null {
  const from = finite(fromAnchor?.ts);
  const to = finite(toAnchor?.ts);
  if (from === null || to === null) return null;
  return {
    kind: "segment", from, to, price, color: SHAPE_OUTLINE, lineWidth: OUTLINE_WIDTH, label,
  };
}

/** The trigger mark and the two reference levels every family carries — the levels deliberately
 *  span the full pane, since the record anchors neither of them in time (see DeskPlaybookAnchors). */
function commonMarks(signal: DeskPlaybookSignal, triggerTs: number | null): ChartShapeSpec[] {
  const marks: ChartShapeSpec[] = [];
  const triggerPrice = finite(signal.trigger_price);
  if (triggerTs !== null && triggerPrice !== null) {
    marks.push({
      kind: "dot", time: triggerTs, price: triggerPrice, color: SHAPE_TRIGGER, radius: 5,
      label: "trigger",
    });
  }
  const entry = finite(signal.entry);
  if (entry !== null) {
    marks.push({
      kind: "level", price: entry, color: SHAPE_ENTRY, lineWidth: LEVEL_WIDTH, label: "entry",
    });
  }
  const invalidation = finite(signal.invalidation_price);
  if (invalidation !== null) {
    marks.push({
      kind: "level", price: invalidation, color: SHAPE_INVALIDATION, lineWidth: LEVEL_WIDTH,
      lineStyle: "dashed", label: "invalidation",
    });
  }
  return marks;
}

/** The outline, per family. Returns the formation marks only — the trigger and the two levels are
 *  added by the caller, identically for every family. */
function formationShapes(
  signal: DeskPlaybookSignal,
  anchors: DeskPlaybookAnchors,
): ChartShapeSpec[] {
  const priceLow = finite(signal.price_low);
  const priceHigh = finite(signal.price_high);
  const shapes: (ChartShapeSpec | null)[] = [];

  switch (signal.setup_id) {
    case "open_high_break":
    case "open_low_break": {
      // The box's two prices are the opening range itself; its bounds are the wall-clock window.
      const orLow = finite(signal.geometry.or_low);
      const orHigh = finite(signal.geometry.or_high);
      if (orLow !== null && orHigh !== null) {
        shapes.push(box(anchors.opening_range, orLow, orHigh, "opening range"));
        // The edge that actually broke, carried from the range's close to the trigger.
        const broken = signal.side === "long" ? orHigh : orLow;
        shapes.push(
          segment(
            anchors.opening_range && {
              ts: anchors.opening_range.to_ts, ts_utc: anchors.opening_range.to_ts_utc,
              price: broken,
            },
            anchors.trigger,
            broken,
            signal.side === "long" ? "range high" : "range low",
          ),
        );
      }
      break;
    }
    case "jbe":
    case "dbi": {
      shapes.push(polyline([anchors.jump_start, anchors.jump_end]));
      if (priceLow !== null && priceHigh !== null) {
        shapes.push(box(anchors.base, priceLow, priceHigh, "base"));
      }
      break;
    }
    case "capitulation": {
      shapes.push(polyline([anchors.decline_start, anchors.climax]));
      shapes.push(point(anchors.climax));
      break;
    }
    case "cup_handle": {
      shapes.push(polyline([anchors.left_rim, anchors.cup_bottom, anchors.right_rim]));
      shapes.push(point(anchors.left_rim));
      shapes.push(point(anchors.cup_bottom));
      shapes.push(point(anchors.right_rim));
      const handleBottom = finite(anchors.handle_bottom?.price);
      const rightRim = finite(anchors.right_rim?.price);
      if (handleBottom !== null && rightRim !== null) {
        shapes.push(box(anchors.handle, handleBottom, rightRim, "handle"));
      }
      break;
    }
    case "range_trade": {
      if (priceLow !== null && priceHigh !== null) {
        shapes.push(box(anchors.range, priceLow, priceHigh, "range"));
      }
      for (const touch of anchors.low_zone_touches ?? []) shapes.push(point(touch));
      for (const touch of anchors.high_zone_touches ?? []) shapes.push(point(touch));
      break;
    }
    case "double_top":
    case "double_bottom": {
      // The M / W the pattern is named for, then its two peaks, then the neckline it broke.
      shapes.push(polyline([anchors.first_pivot, anchors.structure_pivot, anchors.second_pivot]));
      shapes.push(point(anchors.first_pivot));
      shapes.push(point(anchors.second_pivot));
      const neckline = finite(anchors.structure_pivot?.price);
      if (neckline !== null) {
        shapes.push(segment(anchors.first_pivot, anchors.trigger, neckline, "neckline"));
      }
      break;
    }
    default:
      break;
  }
  return shapes.filter((shape): shape is ChartShapeSpec => shape !== null);
}

/** The price extent and trigger a signal ALWAYS carries, drawn when its outline is not on file. */
function partialShapes(signal: DeskPlaybookSignal): ChartShapeSpec[] {
  const shapes: ChartShapeSpec[] = [];
  for (const [value, label] of [
    [signal.price_low, "price low"],
    [signal.price_high, "price high"],
  ] as const) {
    const price = finite(value);
    if (price !== null) {
      shapes.push({
        kind: "level", price, color: SHAPE_EXTENT, lineWidth: LEVEL_WIDTH, lineStyle: "dashed",
        label,
      });
    }
  }
  return shapes;
}

function legendFor(shapes: readonly ChartShapeSpec[]): PlaybookShapeLegendItem[] {
  const items: PlaybookShapeLegendItem[] = [];
  const seen = new Set<string>();
  const add = (swatch: string, label: string) => {
    if (seen.has(label)) return;
    seen.add(label);
    items.push({ swatch, label });
  };
  for (const shape of shapes) {
    if (shape.kind === "box" || shape.kind === "polyline") add(SHAPE_OUTLINE, "formation");
    else if (shape.kind === "segment") add(SHAPE_OUTLINE, shape.label ?? "formation");
    else if (shape.kind === "dot") {
      add(shape.color, shape.color === SHAPE_TRIGGER ? "trigger" : "pivot / touch");
    } else if (shape.kind === "level") add(shape.color, shape.label ?? "level");
  }
  return items;
}

/**
 * Pure. One served signal in, display specs out. No React, no fetch, no formatting of a price.
 *
 * Degrades honestly in two ways, both of which the caller renders as text rather than hiding:
 * a signal with no `geometry.anchors` (a record written before anchors shipped) draws only its
 * always-served levels, and a signal whose anchors name a different setup draws the same, rather
 * than risking one family's outline over another's bars.
 */
export function playbookSignalShapes(signal: DeskPlaybookSignal): PlaybookShapeResult {
  const anchors = signal.geometry.anchors;
  const triggerTs = anchors ? finite(anchors.trigger?.ts) : null;
  const caption = `${signal.symbol} · ${playbookSetupLabel(signal.setup_id)} · ${signal.side}`;

  if (!anchors || anchors.setup_id !== signal.setup_id) {
    const shapes = [...partialShapes(signal), ...commonMarks(signal, null)];
    return {
      shapes,
      caption,
      span: null,
      completeness: shapes.length > 0 ? "partial" : "absent",
      note: anchors ? MISMATCHED_ANCHORS_NOTE : NO_ANCHORS_NOTE,
      legend: legendFor(shapes),
    };
  }

  const formation = formationShapes(signal, anchors);
  const shapes = [...formation, ...commonMarks(signal, triggerTs)];
  const timeSpan = chartShapeTimeSpan(shapes);
  return {
    shapes,
    caption,
    span: timeSpan ? { fromTs: timeSpan.from, toTs: timeSpan.to } : null,
    completeness: formation.length > 0 ? "full" : "partial",
    note:
      formation.length > 0
        ? null
        : "This signal's recorded anchors carry no outline for its own setup family — only its " +
          "trigger, entry and invalidation are drawn.",
    legend: legendFor(shapes),
  };
}
