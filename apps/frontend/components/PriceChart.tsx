"use client";

// Tape-state prediction chart (J-17 / J-18): a candlestick chart of the watched price with
// markers at meaningful tape-state transitions, plus a 10 / 30 / 60 s bar-size selector.
//
// Single source of truth (one focused chart, computed once): every candle and marker is read
// VERBATIM from GET /tape/{ticker}/history — this component re-bins NO candles and re-derives NO
// marker state/side/price. It polls `…/history` on the stream cadence (it does NOT open a second
// WebSocket). An empty / not-yet-warmed window shows an empty treatment — never invented candles.
//
// The chart library (lightweight-charts) is client-only: it is imported dynamically INSIDE an
// effect so it never runs during server render (no SSR), and adds no backend dependency. It is
// candlestick + markers only — no indicators, studies, drawing tools, or any order/execution
// affordance (Stay-in-scope / No-execution anti-goals).

import { useEffect, useRef, useState } from "react";
import { fetchHistory, fetchStrategies, fetchTradability } from "@/lib/api";
import { formatDateTimeDMY } from "@/lib/datetime";
import {
  HISTORY_BAR_SIZES,
  type HistoryBarSize,
  type StrategiesPayload,
  type TapeHistory,
  type ThesisGeometry,
  type ThesisProjection,
  type TradabilityResponse,
} from "@/lib/types";
import { Panel, EmptyHint } from "./Panel";

// era-5B J-06 (additive): the cockpit gains a tradable-band overlay + a descriptive confluence
// chip beside the existing candles/tape-state markers/thesis geometry above — sim/historical modes
// only (the parent's existing mode gate in app/page.tsx already fully unmounts this component in
// live mode; untouched by this addition). Bands come from GET /research/tradability (era-5B J-01);
// the chip's rejection/breakthrough state mapping comes from GET /research/strategies's
// `structure_tape_map` entry (era-5B J-04). Both are read VERBATIM — this component computes no
// score, cluster, class, or mapping of its own; it only draws served fields and evaluates a display
// conjunction (is the last price inside a served band AND does the served tape state match the
// served mapping for that band's side).

// How often we re-pull `…/history` while a ticker is watched — matches the cockpit's WS push
// cadence so the chart accrues new candles in step with the rest of the cockpit (no 2nd socket).
const POLL_INTERVAL_MS = 1000;

// Marker color by tape state — the SAME load-bearing semantics as the rest of the cockpit
// (emerald = buyer_control, rose = seller_control, amber = absorption). `unclear` is never marked
// by the backend, so it has no entry here. Hex values mirror the DESIGN SYSTEM Tailwind tokens
// (emerald-400 / rose-400 / amber-400) because the charting canvas takes raw colors, not classes.
const MARKER_COLORS: Record<string, string> = {
  buyer_control: "#34d399", // emerald-400
  seller_control: "#fb7185", // rose-400
  bid_absorption: "#fbbf24", // amber-400
  ask_absorption: "#fbbf24", // amber-400
};

const STATE_LABELS: Record<string, string> = {
  buyer_control: "Buyer Control",
  seller_control: "Seller Control",
  bid_absorption: "Bid Absorption",
  ask_absorption: "Ask Absorption",
};

// Thesis-geometry colors (J-48), reusing the established verdict/side semantics so the chart, the
// thesis strip, and the timeline all speak the same color language. Verdict markers: confirming
// emerald, weakening amber, rejecting/invalidated rose, pending slate (the design-direction verdict
// palette). The invalidation price-line is rose (the idea is dead beyond it); the level line is
// slate (a neutral reference). Hex values mirror the DESIGN SYSTEM Tailwind tokens because the
// charting canvas takes raw colors, not classes.
const VERDICT_COLORS: Record<string, string> = {
  confirming: "#34d399", // emerald-400
  weakening: "#fbbf24", // amber-400
  rejecting: "#fb7185", // rose-400
  invalidated: "#fb7185", // rose-400
  pending: "#94a3b8", // slate-400
  expired: "#94a3b8", // slate-400
};
const PRICE_LINE_COLORS: Record<string, string> = {
  invalidation: "#fb7185", // rose-400 — the idea is invalidated beyond this price
  level: "#94a3b8", // slate-400 — a neutral declared reference
};
// Entry/exit marks render in their own slate-200 treatment, distinct from the verdict palette.
const MARK_COLOR = "#e2e8f0"; // slate-200

// The registered structure_tape_map strategy id (era-5B J-04) — mirrors app/structure/page.tsx's
// OWN `STRATEGY_TAPE_ID = "structure_tape"` constant precedent byte-for-byte: this is a
// REGISTRY-LOOKUP key (which entry to read off the fetched strategies list), never tape-state
// confirmation vocabulary. The confirmation mapping itself is read off that entry's OWN
// `rejection_states`/`breakthrough_states` fields below — never restated as a literal here.
const STRATEGY_TAPE_MAP_ID = "structure_tape_map";

export function PriceChart({
  ticker,
  thesis,
  tapeState,
}: {
  ticker: string | null;
  // The live thesis projection (WS `thesis` key) or null. Read VERBATIM for its `geometry`; the
  // chart derives nothing. `null` (no/cleared/resolved-non-invalidated thesis) => no overlay.
  thesis?: ThesisProjection | null;
  // The engine-owned CURRENT tape state (era-5B J-06), read VERBATIM off the WS snapshot's own
  // `tape_state` field — page.tsx passes `snapshot?.tape_state ?? null`, the SAME value
  // Cockpit.tsx already renders. Drives the confluence chip's matching decision below; NEVER
  // derived from `history.markers` here — a silent transition into `unclear` is never marked, so
  // scanning markers for "the latest state" can go stale/wrong.
  tapeState: string | null;
}) {
  const [barSize, setBarSize] = useState<HistoryBarSize>(HISTORY_BAR_SIZES[0]);
  const [history, setHistory] = useState<TapeHistory | null>(null);
  // `loaded` distinguishes "haven't fetched yet" (connecting) from "fetched, genuinely empty"
  // (an empty window) so the empty treatment reads honestly in both cases.
  const [loaded, setLoaded] = useState(false);
  // The watched symbol's tradable bands (era-5B J-06) — `phase` distinguishes "not fetched yet"
  // from "fetched, genuinely empty" (SIM-*/no-bar-series), mirroring `loaded` above so the empty
  // treatment is honest in both cases. Additive/non-blocking: `idle`/`loading`/`error` render
  // nothing extra — the chart + tape markers never wait on this fetch.
  const [tradabilityState, setTradabilityState] = useState<{
    phase: "idle" | "loading" | "ready" | "error";
    data: TradabilityResponse | null;
  }>({ phase: "idle", data: null });
  // The strategy registry (era-5B J-06) — ticker-independent config/registry data, fetched once.
  // Supplies the confluence chip's rejection/breakthrough state mapping.
  const [strategies, setStrategies] = useState<StrategiesPayload | null>(null);

  const containerRef = useRef<HTMLDivElement | null>(null);
  // Library object handles kept across renders; typed loosely because the module is loaded
  // dynamically (client-only) and we never import its types at module scope.
  const chartRef = useRef<any>(null);
  const seriesRef = useRef<any>(null);
  const markersRef = useRef<any>(null);
  const createMarkersRef = useRef<any>(null);
  // The thesis price-line handles currently attached to the series (J-48). Tracked so each geometry
  // update REMOVES the prior lines before adding the new ones (no stale/duplicate lines) and so a
  // cleared/resolved thesis removes them entirely.
  const priceLinesRef = useRef<any[]>([]);
  // The tradable-band price-line handles (era-5B J-06) — tracked SEPARATELY from `priceLinesRef`
  // (the thesis geometry's own dashed lines) so redrawing one family never clobbers the other.
  const bandPriceLinesRef = useRef<any[]>([]);
  // The latest tape-state markers (engine-owned) and thesis markers (research-owned). They share the
  // ONE series-marker primitive, so both effects funnel through `setCombinedMarkers` which sets the
  // union in a single call (lightweight-charts' setMarkers replaces the whole set).
  const stateMarkersRef = useRef<any[]>([]);
  const thesisMarkersRef = useRef<any[]>([]);

  // Set the union of engine tape-state markers + thesis-geometry markers in one call (they share the
  // single series-marker mechanism; markers must be sorted ascending by time for the library).
  function setCombinedMarkers() {
    if (!markersRef.current) return;
    const all = [...stateMarkersRef.current, ...thesisMarkersRef.current].sort(
      (a, b) => a.time - b.time,
    );
    markersRef.current.setMarkers(all);
  }

  // --- Poll …/history verbatim while a ticker is watched (reset on ticker/bar change) -------
  useEffect(() => {
    if (!ticker) {
      setHistory(null);
      setLoaded(false);
      return;
    }
    let cancelled = false;
    setHistory(null);
    setLoaded(false);

    async function pull() {
      const data = await fetchHistory(ticker as string, barSize);
      if (cancelled) return;
      setHistory(data);
      setLoaded(true);
    }
    pull();
    const id = setInterval(pull, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [ticker, barSize]);

  // --- Fetch the watched symbol's tradable bands (era-5B J-06) -------------------------------
  // Keyed on `[ticker, history?.epoch_anchor]` (not `barSize`, not polled every second): the
  // morning-markup basis is date-bounded and does not move intraday, unlike the 1s `…/history`
  // poll above — `epoch_anchor` itself is a STABLE per-watch value (the engine sets it once at
  // watch-start; it never changes while the SAME ticker stays watched), so this still fetches at
  // most once per watch, not on every poll tick.
  //
  // `as_of` is the WATCHED SESSION's own current moment, verbatim: `history.epoch_anchor` (Data
  // Contract row 13, ALREADY fetched by the poll above — no new fetch) is "the real UTC epoch a
  // watched session's logical time 0 maps to" — a real market epoch for a historical replay, so
  // during e.g. the 2026-06-22 replay this correctly resolves THAT session's own prior-close basis
  // (2026-06-18) rather than today's. Falls back to the current wall-clock time only before the
  // first `history` response lands (first paint) or for a SIM ticker (whose synthetic anchor is
  // moot anyway — SIM-* symbols resolve `no_bar_series_for_symbol` regardless of `as_of`). This is
  // STILL zero client "which session" math (no-lookahead): `_resolve_basis` (tradability.py) alone
  // decides the prior session server-side; converting an epoch-seconds field to an ISO string is
  // the SAME pure unit/format conversion this file already does for candle timestamps above
  // (`toClock`), never a date computation of "which session."
  useEffect(() => {
    if (!ticker) {
      setTradabilityState({ phase: "idle", data: null });
      return;
    }
    let cancelled = false;
    setTradabilityState({ phase: "loading", data: null });
    const asOf =
      history?.epoch_anchor != null
        ? new Date(history.epoch_anchor * 1000).toISOString()
        : new Date().toISOString();
    fetchTradability(ticker, asOf).then((res) => {
      if (cancelled) return;
      if (res.ok && res.data) {
        setTradabilityState({ phase: "ready", data: res.data });
      } else {
        setTradabilityState({ phase: "error", data: null });
      }
    });
    return () => {
      cancelled = true;
    };
  }, [ticker, history?.epoch_anchor]);

  // --- Fetch the strategy registry ONCE (era-5B J-06) -----------------------------------------
  // Ticker-independent config/registry data (the SAME GET /research/strategies read `/structure`'s
  // Registry section already established). Supplies the confluence chip's rejection/breakthrough
  // state mapping — read verbatim below, never restated as a client-side literal.
  useEffect(() => {
    let cancelled = false;
    fetchStrategies().then((res) => {
      if (!cancelled && res.ok) setStrategies(res.strategies);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // --- Create the chart once (client-only dynamic import, never at SSR) ---------------------
  useEffect(() => {
    if (!ticker) return;
    let disposed = false;

    (async () => {
      const lc = await import("lightweight-charts");
      if (disposed || !containerRef.current) return;

      const chart = lc.createChart(containerRef.current, {
        autoSize: true,
        layout: {
          // Match the dark instrument-panel surface so it does not read as a bright widget.
          background: { type: lc.ColorType.Solid, color: "#020617" }, // slate-950
          textColor: "#94a3b8", // slate-400
          fontFamily:
            "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        },
        grid: {
          vertLines: { color: "#1e293b" }, // slate-800
          horzLines: { color: "#1e293b" },
        },
        rightPriceScale: { borderColor: "#1e293b" },
        timeScale: {
          borderColor: "#1e293b",
          timeVisible: true,
          secondsVisible: true,
          // TRUE clock time on the axis (J-31): each candle's `time` is a real UTC epoch
          // (anchor + logical_ts, see the data effect), and this formatter renders the axis ticks
          // as `dd-MM-yyyy HH:mm:ss` in the operator's LOCAL zone via the ONE shared formatter
          // (J-35) — never an elapsed 0…600 s counter. lightweight-charts passes UTCTimestamp
          // SECONDS, so multiply to ms for the Date-based formatter.
          tickMarkFormatter: (time: number) => formatDateTimeDMY(time * 1000),
        },
        // The crosshair tooltip time, also TRUE clock time via the shared `dd-MM-yyyy HH:mm:ss`
        // formatter (J-31 / J-35) — consistent with the axis ticks.
        localization: {
          timeFormatter: (time: number) => formatDateTimeDMY(time * 1000),
        },
        crosshair: { mode: lc.CrosshairMode.Normal },
      });
      const series = chart.addSeries(lc.CandlestickSeries, {
        upColor: "#34d399", // emerald-400
        downColor: "#fb7185", // rose-400
        wickUpColor: "#34d399",
        wickDownColor: "#fb7185",
        borderVisible: false,
      });

      chartRef.current = chart;
      seriesRef.current = series;
      createMarkersRef.current = lc.createSeriesMarkers;
      markersRef.current = lc.createSeriesMarkers(series, []);
    })();

    return () => {
      disposed = true;
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
        seriesRef.current = null;
        markersRef.current = null;
      }
    };
  }, [ticker]);

  // --- Feed the verbatim candles + markers into the chart whenever data changes -------------
  useEffect(() => {
    const series = seriesRef.current;
    if (!series || !history) return;

    // TRUE clock time (J-31): map each LOGICAL bin/marker time to a real UTC-epoch SECONDS value
    // as `epoch_anchor + logical_ts` — a pure ADDITIVE display offset (the chart recomputes NO
    // price/side/state; the engine's logical timeline + classification are unchanged). The anchor
    // is real market epoch for historical and the synthetic session-start for simulated. When the
    // backend has no anchor (an empty/anchorless window) we fall back to the logical seconds — the
    // chart is empty in that case anyway, so no fabricated timestamp is shown.
    const anchor = history.epoch_anchor ?? 0;
    const toClock = (logical: number) => Math.round(anchor + logical);

    // Candles VERBATIM from the engine buffer (no re-binning). Logical-second bin starts are
    // whole multiples of the bar size; map to the true-clock epoch and keep ascending order
    // (the backend already returns them sorted + unique per bar).
    const candles = history.bars.map((b) => ({
      time: toClock(b.time) as any,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));
    series.setData(candles);

    // Markers VERBATIM from the engine buffer (the marker's own state/confidence — no
    // re-derivation). One marker per meaningful transition, colored by state, stamped at true
    // clock time so it aligns with the candle under it. Tape-state markers sit ABOVE the bar with a
    // down-arrow — kept visually distinct from the thesis markers (which sit BELOW the bar), so the
    // two registered marker owners never read as one layer (J-48).
    if (markersRef.current && createMarkersRef.current) {
      stateMarkersRef.current = history.markers.map((m) => ({
        time: toClock(m.time) as any,
        position: "aboveBar" as const,
        color: MARKER_COLORS[m.state] ?? "#fbbf24",
        shape: "arrowDown" as const,
        text: STATE_LABELS[m.state] ?? m.state,
      }));
      setCombinedMarkers();
    }

    if (chartRef.current && candles.length > 0) {
      chartRef.current.timeScale().fitContent();
    }
  }, [history]);

  // --- Draw the thesis geometry VERBATIM (J-48): price-lines + thesis markers ---------------------
  // Reads the served `geometry` (declared prices + the append-only timeline + the marks, computed
  // once server-side) and draws it on the SAME epoch anchor the candles use (`anchor + logical_ts`).
  // The chart derives NO price/side/state/time of its own. With `thesis: null` (or no geometry) it
  // removes every line and clears the thesis-marker layer — exactly the no-thesis render (J-68/J-17).
  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;
    const geometry: ThesisGeometry | undefined = thesis?.geometry;

    // Always clear prior price-lines first so an update never leaves a stale/duplicate line and a
    // cleared/resolved thesis removes them entirely.
    for (const line of priceLinesRef.current) {
      try {
        series.removePriceLine(line);
      } catch {
        // The series may have been disposed between renders — ignore (it is being torn down).
      }
    }
    priceLinesRef.current = [];

    if (!geometry) {
      // No thesis => no overlay. Clear the thesis-marker layer and re-set the combined markers so
      // only the engine tape-state markers remain (the exact no-thesis render).
      thesisMarkersRef.current = [];
      setCombinedMarkers();
      return;
    }

    // Price-lines (time-independent) — invalidation always; level only when served. Each labeled
    // with the backend-owned copy, rendered verbatim. Dashed so they read as declared reference
    // lines, not data.
    for (const pl of geometry.price_lines) {
      const handle = series.createPriceLine({
        price: pl.price,
        color: PRICE_LINE_COLORS[pl.kind] ?? "#94a3b8",
        lineWidth: 1,
        lineStyle: 2, // LineStyle.Dashed
        axisLabelVisible: true,
        title: pl.label,
      });
      priceLinesRef.current.push(handle);
    }

    // Thesis markers — visually DISTINCT from tape-state markers: they sit BELOW the bar (vs above)
    // and use a circle (verdict / first-confirmation) or arrow-up (entry/exit) shape (vs the
    // tape-state down-arrow). x-placement uses the SAME epoch anchor as the candles.
    const anchor = history?.epoch_anchor ?? 0;
    const toClock = (logical: number) => Math.round(anchor + logical);
    thesisMarkersRef.current = geometry.markers.map((m) => {
      if (m.kind === "entry" || m.kind === "exit") {
        // The user's own action mark — its own slate treatment with the verbatim mono price.
        const priceText = m.price != null ? ` ${m.price.toFixed(2)}` : "";
        return {
          time: toClock(m.logical_ts) as any,
          position: "belowBar" as const,
          color: MARK_COLOR,
          shape: "arrowUp" as const,
          text: `${m.label}${priceText}`,
        };
      }
      // A verdict-transition marker or the first-confirmation marker — verdict palette, circle shape.
      const color =
        m.kind === "first_confirmation"
          ? VERDICT_COLORS.confirming
          : VERDICT_COLORS[m.verdict ?? "pending"] ?? "#94a3b8";
      return {
        time: toClock(m.logical_ts) as any,
        position: "belowBar" as const,
        color,
        shape: "circle" as const,
        text: m.label,
      };
    });
    setCombinedMarkers();
  }, [thesis, history]);

  // --- Draw the tradable-band overlay VERBATIM (era-5B J-06) ---------------------------------
  // One SOLID price line per band edge, colored by side — reuses StructureChart.tsx's L97-120
  // pattern byte-for-byte. Bands are read off the served prop only; this component performs no
  // scoring or clustering of its own. Keyed on `[tradabilityState, history]` rather than just
  // `tradabilityState`: `history` polls every second (see POLL_INTERVAL_MS above), so if the chart
  // series is not yet created the very first time bands resolve, the next poll tick re-runs this
  // effect and draws them — the SAME self-healing dependency the thesis-geometry effect just above
  // already relies on for the identical series-not-ready race.
  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;

    // Always clear prior band lines first (mirrors the thesis-geometry effect's own clear-then-
    // redraw pattern) so a re-fetch or ticker change never leaves a stale/duplicate line.
    for (const line of bandPriceLinesRef.current) {
      try {
        series.removePriceLine(line);
      } catch {
        // The series may have been disposed between renders — ignore (it is being torn down).
      }
    }
    bandPriceLinesRef.current = [];

    const bands = tradabilityState.data?.bands ?? [];
    for (const band of bands) {
      const color = band.side === "resistance" ? "#fb7185" : "#34d399"; // rose-400 / emerald-400
      const sideLabel = band.side === "resistance" ? "R" : "S";
      const classLabel = band.class ? ` class ${band.class}` : "";
      const title = `${sideLabel}${classLabel} · score ${band.quality_score}${band.round_number ? " · round" : ""}`;
      const edges =
        band.price_low === band.price_high ? [band.price_low] : [band.price_low, band.price_high];
      for (const price of edges) {
        const handle = series.createPriceLine({
          price,
          color,
          lineWidth: 2,
          lineStyle: 0, // LineStyle.Solid — distinct from this component's own DASHED thesis lines
          axisLabelVisible: true,
          title,
        });
        bandPriceLinesRef.current.push(handle);
      }
    }
  }, [tradabilityState, history]);

  if (!ticker) return null;

  const hasBars = !!history && history.bars.length > 0;

  // --- Confluence chip (era-5B J-06) ----------------------------------------------------------
  // A pure DISPLAY CONJUNCTION over already-fetched/served values — price-in-band × served tape
  // state × the served rejection/breakthrough mapping. No scoring, no clustering, no client-side
  // mapping literal: `rejectionState`/`breakthroughState` are read off the FETCHED
  // structure_tape_map entry, never restated (the only place this file hardcodes the four tape-
  // state names is the pre-existing MARKER_COLORS/STATE_LABELS cosmetic dicts above, unrelated to
  // this decision).
  const lastPrice =
    history && history.bars.length > 0 ? history.bars[history.bars.length - 1].close : null;
  const bands = tradabilityState.data?.bands ?? [];
  const matchedBand =
    lastPrice != null
      ? bands.find((b) => lastPrice >= b.price_low && lastPrice <= b.price_high) ?? null
      : null;
  // Structural side->direction reading (named explicitly in the phase spec's Notes — NOT tape-state
  // vocabulary): a resistance band defends a ceiling (a short-direction reading); a support band
  // defends a floor (a long-direction reading).
  const direction: "long" | "short" | null =
    matchedBand == null ? null : matchedBand.side === "resistance" ? "short" : "long";
  const mapEntry = strategies?.strategies.find((s) => s.strategy_id === STRATEGY_TAPE_MAP_ID)?.entries;
  const rejectionState = direction ? mapEntry?.rejection_states?.[direction] : undefined;
  const breakthroughState = direction ? mapEntry?.breakthrough_states?.[direction] : undefined;
  const matchKind: "rejection" | "breakthrough" | null =
    tapeState != null && tapeState === rejectionState
      ? "rejection"
      : tapeState != null && tapeState === breakthroughState
        ? "breakthrough"
        : null;
  const confluence = matchedBand && matchKind ? { band: matchedBand, kind: matchKind } : null;

  // Honest "no tradable map" state (SIM-*/no-bar-series symbols) — shown ONLY once the bands fetch
  // genuinely resolved empty, never while still loading/failed (the overlay/chip are a pure
  // ADDITION that never blocks or degrades the chart/markers above).
  const tradabilityEmpty =
    tradabilityState.phase === "ready" &&
    !!tradabilityState.data &&
    (tradabilityState.data.no_bar_series_for_symbol || tradabilityState.data.bands.length === 0);

  return (
    <Panel title="Price Chart — Tape-State Markers" className="mb-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-xs text-slate-500">Bar size</span>
        <div className="flex gap-1" role="group" aria-label="Bar size">
          {HISTORY_BAR_SIZES.map((size) => {
            const selected = size === barSize;
            return (
              <button
                key={size}
                type="button"
                onClick={() => setBarSize(size)}
                aria-pressed={selected}
                className={
                  "rounded border px-2.5 py-1 font-mono text-xs transition-colors " +
                  (selected
                    ? "border-slate-600 bg-slate-700 text-slate-100"
                    : "border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700 hover:text-slate-200 focus:border-slate-600 focus:text-slate-200 active:bg-slate-800")
                }
              >
                {size}s
              </button>
            );
          })}
        </div>
      </div>

      {/* The chart canvas. The container is always mounted so the library can attach; the empty
          treatment overlays it before any candle exists (never placeholder candles). */}
      <div className="relative">
        <div ref={containerRef} className="h-64 w-full" />
        {!hasBars && (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <EmptyHint>
              {loaded ? "No price history for this window yet" : "Loading price history…"}
            </EmptyHint>
          </div>
        )}
      </div>

      {/* era-5B J-06: the tradable-band overlay's companion strip. Additive/non-blocking — while
          the bands fetch is idle/loading/failed this renders nothing, so the chart + tape markers
          above never wait on it. Neutral slate "factual stamp" styling (mirrors
          FeedBasisBadge.tsx's chip family) — this app reserves amber for degraded/empty/truncated
          states; a confluence chip is a positive descriptive signal, not a warning. */}
      {confluence && (
        <div
          data-testid="confluence-chip"
          className="mt-3 rounded bg-slate-800 px-2.5 py-1.5 text-xs text-slate-300"
        >
          Inside {confluence.band.side === "resistance" ? "R" : "S"}-band{" "}
          {confluence.band.price_low.toFixed(2)}–{confluence.band.price_high.toFixed(2)}
          {confluence.band.class ? ` (class ${confluence.band.class})` : ""} · tape:{" "}
          {STATE_LABELS[tapeState ?? ""] ?? tapeState} ({confluence.kind}) · measured history:{" "}
          edge report
        </div>
      )}
      {tradabilityEmpty && (
        <div className="mt-3" data-testid="no-tradable-map">
          <EmptyHint>No tradable map for {ticker}.</EmptyHint>
        </div>
      )}
    </Panel>
  );
}
