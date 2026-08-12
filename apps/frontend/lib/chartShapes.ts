// A declarative, library-agnostic description of one drawable mark on the price chart. Pure data:
// no lightweight-charts import, no React, no behaviour. `components/chartShapePrimitive.ts` renders
// these; `lib/playbookShapes.ts` produces them. Keeping the two apart is what lets the producer
// stay a pure function over an already-served payload — unit-readable and guardable — while the
// canvas code stays a renderer that decides nothing.
//
// TIME is epoch SECONDS — the bar store's own `BarRow.ts` unit AND lightweight-charts' own
// UTCTimestamp unit, so no converter sits between a spec and the canvas.
// PRICE is an absolute price in the instrument's own units, copied verbatim from a served field.

export type ChartShapeLineStyle = "solid" | "dashed";

export interface ChartShapePoint {
  /** epoch SECONDS */
  time: number;
  price: number;
}

/** A time-and-price bounded rectangle — an opening range, a base, a trading range, a handle. */
export interface ChartShapeBox {
  kind: "box";
  from: number;
  to: number;
  priceLow: number;
  priceHigh: number;
  color: string;
  /** rgba fill drawn UNDER the candles; omitted = outline only. */
  fill?: string;
  lineWidth?: number;
  lineStyle?: ChartShapeLineStyle;
  label?: string;
}

/** An open path through >= 2 points — a decline leg, a jump leg, a cup, an M/W outline. */
export interface ChartShapePolyline {
  kind: "polyline";
  points: ChartShapePoint[];
  color: string;
  lineWidth?: number;
  lineStyle?: ChartShapeLineStyle;
  label?: string;
}

/** A horizontal price line BOUNDED in time — a neckline spanning its own two pivots, a broken rim. */
export interface ChartShapeSegment {
  kind: "segment";
  from: number;
  to: number;
  price: number;
  color: string;
  lineWidth?: number;
  lineStyle?: ChartShapeLineStyle;
  label?: string;
}

/** A horizontal price line spanning the FULL pane — used for the two levels that are deliberately
 *  never anchored in time (entry, invalidation), and as the honest fallback for a record whose
 *  outline was never recorded. */
export interface ChartShapeLevel {
  kind: "level";
  price: number;
  color: string;
  lineWidth?: number;
  lineStyle?: ChartShapeLineStyle;
  label?: string;
}

/** A pivot / touch / climax / trigger mark. */
export interface ChartShapeDot {
  kind: "dot";
  time: number;
  price: number;
  color: string;
  radius?: number;
  label?: string;
}

export type ChartShapeSpec =
  | ChartShapeBox
  | ChartShapePolyline
  | ChartShapeSegment
  | ChartShapeLevel
  | ChartShapeDot;

/** The time extent of a shape set, or `null` when no shape in it carries a time (a `level`-only
 *  partial). Pure; drives the chart's focus range and its off-window disclosure. */
export function chartShapeTimeSpan(
  shapes: readonly ChartShapeSpec[],
): { from: number; to: number } | null {
  const stamps: number[] = [];
  for (const shape of shapes) {
    if (shape.kind === "box" || shape.kind === "segment") stamps.push(shape.from, shape.to);
    else if (shape.kind === "dot") stamps.push(shape.time);
    else if (shape.kind === "polyline") for (const p of shape.points) stamps.push(p.time);
  }
  if (stamps.length === 0) return null;
  return { from: Math.min(...stamps), to: Math.max(...stamps) };
}

/** The price extent of a shape set, or `null` when empty. Feeds the primitive's `autoscaleInfo` so
 *  an invalidation line sitting outside the candles' own range is still on screen. */
export function chartShapePriceSpan(
  shapes: readonly ChartShapeSpec[],
): { min: number; max: number } | null {
  const prices: number[] = [];
  for (const shape of shapes) {
    if (shape.kind === "box") prices.push(shape.priceLow, shape.priceHigh);
    else if (shape.kind === "segment" || shape.kind === "level" || shape.kind === "dot") {
      prices.push(shape.price);
    } else if (shape.kind === "polyline") for (const p of shape.points) prices.push(p.price);
  }
  if (prices.length === 0) return null;
  return { min: Math.min(...prices), max: Math.max(...prices) };
}
