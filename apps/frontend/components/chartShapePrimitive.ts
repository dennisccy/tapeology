import type {
  AutoscaleInfo,
  IChartApiBase,
  IPrimitivePaneRenderer,
  IPrimitivePaneView,
  ISeriesApi,
  ISeriesPrimitive,
  Logical,
  PrimitivePaneViewZOrder,
  SeriesAttachedParameter,
  SeriesType,
  Time,
} from "lightweight-charts";
import type { ChartShapeSpec } from "@/lib/chartShapes";
import { chartShapePriceSpan } from "@/lib/chartShapes";

// The canvas overlay that draws a playbook setup's outline on the price chart — the one place in
// this app that implements lightweight-charts' series-primitive API. It exists because the chart's
// existing overlay vocabulary is `createPriceLine` (a horizontal line across the WHOLE pane) and
// series markers (a point on a bar), and a formation is neither: an opening range is a box bounded
// in time and price, a cup is a path through three bars, a neckline spans its own two pivots.
//
// It DECIDES nothing. `lib/playbookShapes.ts` turns a served signal into `ChartShapeSpec`s; this
// draws exactly those, and holds no knowledge of setups, prices, or the playbook at all.
//
// The imports are TYPE-ONLY on purpose: `lightweight-charts` is loaded through a dynamic `import()`
// inside StructureChart's mount effect so it never runs at SSR, and `import type` is fully erased,
// so this module adds no runtime dependency and no bundle weight.

// The canvas scope fancy-canvas hands a renderer. Declared STRUCTURALLY rather than imported from
// `fancy-canvas`: that package is a TRANSITIVE dependency of lightweight-charts and is not in this
// app's own package.json, so importing a type from it would be a phantom dependency.
interface BitmapScope {
  readonly context: CanvasRenderingContext2D;
  readonly bitmapSize: { readonly width: number; readonly height: number };
  readonly horizontalPixelRatio: number;
  readonly verticalPixelRatio: number;
}

interface CanvasTarget {
  useBitmapCoordinateSpace<T>(f: (scope: BitmapScope) => T): T;
}

const DASH_PATTERN = [4, 3];
const LABEL_PADDING = 3;
const DEFAULT_DOT_RADIUS = 4;
const DEFAULT_LINE_WIDTH = 1;
// A mark narrower than this (in media px) is not labelled -- the text would be wider than the
// thing it names and would collide with whatever it sits against.
const MIN_LABEL_WIDTH = 56;

type AnySeries = ISeriesApi<SeriesType, Time>;

/** One pane's worth of drawing: the renderer closes over the primitive so it always reads the
 *  CURRENT shapes and the CURRENT coordinate converters, never a snapshot. */
class ShapePaneView implements IPrimitivePaneView {
  constructor(
    private readonly _owner: ChartShapePrimitive,
    private readonly _layer: PrimitivePaneViewZOrder,
    private readonly _renderer: IPrimitivePaneRenderer,
  ) {}

  zOrder(): PrimitivePaneViewZOrder {
    return this._layer;
  }

  renderer(): IPrimitivePaneRenderer | null {
    return this._owner.hasShapes() ? this._renderer : null;
  }
}

export class ChartShapePrimitive implements ISeriesPrimitive<Time> {
  private _shapes: readonly ChartShapeSpec[];
  private _chart: IChartApiBase<Time> | null = null;
  private _series: AnySeries | null = null;
  private _requestUpdate: (() => void) | null = null;
  // Built ONCE and never replaced. The library caches pane views by array reference and its own
  // docs ask a primitive to "return the same array if nothing changed" — a fresh array per call
  // would defeat that cache on every repaint. The shapes behind the views are what change.
  private readonly _paneViews: readonly IPrimitivePaneView[];

  constructor(shapes: readonly ChartShapeSpec[]) {
    this._shapes = shapes;
    this._paneViews = [
      // Fills sit UNDER the candles, so a translucent formation never washes out the price action
      // it describes. Strokes and marks sit at "normal" — above the series, but deliberately not
      // "top", which would draw them over the operator's own crosshair readout.
      new ShapePaneView(this, "bottom", { draw: (target) => this._drawFills(target as CanvasTarget) }),
      new ShapePaneView(this, "normal", { draw: (target) => this._drawMarks(target as CanvasTarget) }),
    ];
  }

  // --- lifecycle ---------------------------------------------------------------------------------

  attached(param: SeriesAttachedParameter<Time>): void {
    this._chart = param.chart;
    this._series = param.series as AnySeries;
    this._requestUpdate = param.requestUpdate;
  }

  detached(): void {
    this._chart = null;
    this._series = null;
    this._requestUpdate = null;
  }

  paneViews(): readonly IPrimitivePaneView[] {
    return this._paneViews;
  }

  /** Nothing is cached between draws — `draw` recomputes every coordinate from the live converters,
   *  which is also why panning and zooming need no subscription here: the library re-runs the
   *  renderer on each repaint. So there is genuinely nothing to invalidate. */
  updateAllViews(): void {}

  /** Keeps a shape that sits outside the candles' own price range (an invalidation level below
   *  every low, say) on screen instead of clipped off the pane. */
  autoscaleInfo(): AutoscaleInfo | null {
    const span = chartShapePriceSpan(this._shapes);
    if (span === null) return null;
    return { priceRange: { minValue: span.min, maxValue: span.max } };
  }

  hasShapes(): boolean {
    return this._shapes.length > 0;
  }

  setShapes(shapes: readonly ChartShapeSpec[]): void {
    this._shapes = shapes;
    this._requestUpdate?.();
  }

  // --- coordinates -------------------------------------------------------------------------------

  /** `timeToCoordinate` returns null for any time not present in the series data — which is every
   *  instant BETWEEN bars and every instant outside the loaded window. Fall back through the index
   *  so a shape spanning a gap still draws.
   *
   *  Note `findNearest` SNAPS: an anchor beyond the loaded window clamps to the window's edge, so a
   *  box can appear to end where the data ends. That would be a plausible-looking lie, which is why
   *  StructureChart discloses a clipped shape in the DOM rather than leaving it to the pixels. */
  private _x(time: number): number | null {
    const timeScale = this._chart?.timeScale();
    if (!timeScale) return null;
    const direct = timeScale.timeToCoordinate(time as Time);
    if (direct !== null) return direct;
    const index = timeScale.timeToIndex(time as Time, true);
    return index === null ? null : timeScale.logicalToCoordinate(index as unknown as Logical);
  }

  private _y(price: number): number | null {
    return this._series?.priceToCoordinate(price) ?? null;
  }

  // --- drawing -----------------------------------------------------------------------------------

  private _drawFills(target: CanvasTarget): void {
    target.useBitmapCoordinateSpace((scope) => {
      const { context, horizontalPixelRatio: hx, verticalPixelRatio: vy } = scope;
      context.save();
      for (const shape of this._shapes) {
        if (shape.kind !== "box" || !shape.fill) continue;
        const rect = this._boxRect(shape.from, shape.to, shape.priceLow, shape.priceHigh, hx, vy);
        if (rect === null) continue;
        context.fillStyle = shape.fill;
        context.fillRect(rect.left, rect.top, rect.width, rect.height);
      }
      context.restore();
    });
  }

  private _drawMarks(target: CanvasTarget): void {
    target.useBitmapCoordinateSpace((scope) => {
      const { context, horizontalPixelRatio: hx, verticalPixelRatio: vy, bitmapSize } = scope;
      context.save();
      for (const shape of this._shapes) {
        switch (shape.kind) {
          case "box": {
            const rect = this._boxRect(shape.from, shape.to, shape.priceLow, shape.priceHigh, hx, vy);
            if (rect === null) break;
            this._stroke(context, shape.color, shape.lineWidth ?? DEFAULT_LINE_WIDTH, shape.lineStyle, vy);
            context.strokeRect(rect.left, rect.top, rect.width, rect.height);
            if (shape.label && rect.width >= MIN_LABEL_WIDTH * hx) {
              this._label(context, shape.label, rect.left, rect.top, shape.color, vy);
            }
            break;
          }
          case "polyline": {
            const points = shape.points
              .map((p) => this._pixel(p.time, p.price, hx, vy))
              .filter((p): p is { x: number; y: number } => p !== null);
            if (points.length < 2) break;
            this._stroke(context, shape.color, shape.lineWidth ?? DEFAULT_LINE_WIDTH, shape.lineStyle, vy);
            context.beginPath();
            context.moveTo(points[0].x, points[0].y);
            for (const p of points.slice(1)) context.lineTo(p.x, p.y);
            context.stroke();
            break;
          }
          case "segment": {
            const from = this._pixel(shape.from, shape.price, hx, vy);
            const to = this._pixel(shape.to, shape.price, hx, vy);
            if (from === null || to === null) break;
            this._stroke(context, shape.color, shape.lineWidth ?? DEFAULT_LINE_WIDTH, shape.lineStyle, vy);
            context.beginPath();
            context.moveTo(from.x, from.y);
            context.lineTo(to.x, to.y);
            context.stroke();
            // Labelled at the FAR end, right-aligned, and only when the segment is long enough to
            // carry the text. A segment usually begins where a box ends (an opening range's broken
            // edge starts at the range's own right edge), so on a tight formation a label here
            // lands on top of the box's own -- and two overlapping words say less than one.
            if (shape.label && Math.abs(to.x - from.x) >= MIN_LABEL_WIDTH * hx) {
              this._label(context, shape.label, to.x, to.y, shape.color, vy, "right");
            }
            break;
          }
          case "level": {
            const y = this._y(shape.price);
            if (y === null) break;
            const py = y * vy;
            this._stroke(context, shape.color, shape.lineWidth ?? DEFAULT_LINE_WIDTH, shape.lineStyle, vy);
            context.beginPath();
            context.moveTo(0, py);
            context.lineTo(bitmapSize.width, py);
            context.stroke();
            // Right-aligned, unlike every other label here. A `level` spans the whole pane, so its
            // label has no natural anchor — and the left edge is where the setup caption sits, so
            // labelling there collided with it whenever a level landed near the top of the pane.
            if (shape.label) {
              this._label(context, shape.label, bitmapSize.width, py, shape.color, vy, "right");
            }
            break;
          }
          case "dot": {
            const at = this._pixel(shape.time, shape.price, hx, vy);
            if (at === null) break;
            const radius = (shape.radius ?? DEFAULT_DOT_RADIUS) * vy;
            context.beginPath();
            context.arc(at.x, at.y, radius, 0, Math.PI * 2);
            context.fillStyle = shape.color;
            context.fill();
            // A background-coloured ring so a dot stays readable over a filled candle body.
            context.lineWidth = Math.max(1, Math.round(vy));
            context.setLineDash([]);
            context.strokeStyle = "#020617";
            context.stroke();
            // A dot's label is drawn unconditionally: the width test the box and segment labels use
            // asks whether the text is wider than the mark it names, and a dot has no width to
            // compare against. This branch used to be missing entirely, so a dot could carry a
            // label that silently never drew.
            //
            // BELOW the dot, and that side is measured rather than chosen. Above it, live, three
            // things converged on one point and read as a single run-on string: the chart's own
            // `as-of` series marker (which draws above this very bar, since a playbook drill-in's
            // `asof` IS the trigger instant), a segment label right-aligned into the same corner,
            // and this one. Below the dot is the only side with nothing already on it.
            if (shape.label) {
              const fontHeight = Math.round(10 * vy);
              const below = at.y + radius + fontHeight + LABEL_PADDING * vy;
              this._label(context, shape.label, at.x, below, shape.color, vy);
            }
            break;
          }
        }
      }
      context.restore();
    });
  }

  private _pixel(
    time: number, price: number, hx: number, vy: number,
  ): { x: number; y: number } | null {
    const x = this._x(time);
    const y = this._y(price);
    if (x === null || y === null) return null;
    return { x: x * hx, y: y * vy };
  }

  private _boxRect(
    from: number, to: number, priceLow: number, priceHigh: number, hx: number, vy: number,
  ): { left: number; top: number; width: number; height: number } | null {
    const left = this._x(from);
    const right = this._x(to);
    const top = this._y(priceHigh);
    const bottom = this._y(priceLow);
    if (left === null || right === null || top === null || bottom === null) return null;
    const x0 = Math.min(left, right) * hx;
    const x1 = Math.max(left, right) * hx;
    const y0 = Math.min(top, bottom) * vy;
    const y1 = Math.max(top, bottom) * vy;
    return { left: x0, top: y0, width: Math.max(x1 - x0, 1), height: Math.max(y1 - y0, 1) };
  }

  private _stroke(
    context: CanvasRenderingContext2D,
    color: string,
    width: number,
    style: "solid" | "dashed" | undefined,
    vy: number,
  ): void {
    context.strokeStyle = color;
    context.lineWidth = Math.max(1, Math.round(width * vy));
    context.setLineDash(style === "dashed" ? DASH_PATTERN.map((d) => d * vy) : []);
  }

  private _label(
    context: CanvasRenderingContext2D,
    text: string,
    x: number,
    y: number,
    color: string,
    vy: number,
    align: "left" | "right" = "left",
  ): void {
    context.setLineDash([]);
    context.font = `${Math.round(10 * vy)}px ui-sans-serif, system-ui, sans-serif`;
    context.fillStyle = color;
    context.textBaseline = "bottom";
    context.textAlign = align;
    const pad = LABEL_PADDING * vy;
    context.fillText(text, align === "right" ? x - pad : x + pad, y - pad);
    context.textAlign = "left";
  }
}