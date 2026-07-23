"use client";

// The cockpit price chart (J-17 / J-18): the watched instrument as candlesticks, with markers at
// meaningful tape-state transitions and the live thesis geometry. This component is the cockpit's
// smart CONTAINER — it polls the served data and composes it — while the drawing itself is delegated
// to the shared `StructureChart` (the /structure Tradable Map's own renderer), so both surfaces
// share one chart implementation.
//
// Two view modes, chosen with the selector:
//   * "Tape" (10 / 30 / 60 s) — the tape engine's own logical-second candles for the replay window
//     (GET /tape/{ticker}/history?bar=), the original cockpit chart.
//   * "History" (real timeframes) — recorded store candles up to the replay start (context) PLUS the
//     wall-clock bars built LIVE from the tape from the start onward (GET …/history?timeframe= for
//     the live bars, GET /research/candles for the recorded context). The store window is clamped
//     strictly BEFORE the replay start (no lookahead); the live tape owns everything from it on.
//
// Single source of truth (one focused chart, computed once): every candle and marker is read
// VERBATIM from the served payloads — this component re-bins NO candles and re-derives NO marker
// state/side/price. It polls on the stream cadence (it does NOT open a second WebSocket). An empty /
// not-yet-warmed window shows an empty treatment — never invented candles.
//
// era-5B J-06 (additive): the tradable-band overlay + a descriptive confluence chip beside the
// candles/markers. Bands come from GET /research/tradability (era-5B J-01); the chip's
// rejection/breakthrough state mapping comes from GET /research/strategies's `structure_tape_map`
// entry (era-5B J-04). Both are read VERBATIM — this component computes no score, cluster, class, or
// mapping of its own; it only draws served fields and evaluates a display conjunction (is the last
// price inside a served band AND does the served tape state match the served mapping for that side).

import { useEffect, useMemo, useState } from "react";
import { fetchHistory, fetchStrategies, fetchTimeframeHistory } from "@/lib/api";
import { boundaryTs, timeframesInOrder } from "@/lib/timeframes";
import { useBarWindow } from "@/lib/useBarWindow";
import { useRecordedSeries } from "@/lib/useRecordedSeries";
import { useTradability } from "@/lib/useTradability";
import {
  HISTORY_BAR_SIZES,
  TIMEFRAMES_WITH_LIVE_BARS,
  type BarRow,
  type CockpitHistory,
  type HistoryBarSize,
  type StrategiesPayload,
  type ThesisProjection,
} from "@/lib/types";
import {
  StructureChart,
  type ChartMarkerSpec,
  type ChartPriceLineSpec,
} from "./StructureChart";
import { Panel, EmptyHint } from "./Panel";

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

// The active chart view: one logical-second tape bar size, or one wall-clock timeframe.
type ChartView =
  | { kind: "tape"; bar: HistoryBarSize }
  | { kind: "history"; timeframe: string };

function segmentClass(selected: boolean): string {
  return (
    "rounded border px-2.5 py-1 font-mono text-xs transition-colors " +
    (selected
      ? "border-slate-600 bg-slate-700 text-slate-100"
      : "border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700 hover:text-slate-200 focus:border-slate-600 focus:text-slate-200 active:bg-slate-800")
  );
}

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
  const [view, setView] = useState<ChartView>({ kind: "tape", bar: HISTORY_BAR_SIZES[0] });
  const [history, setHistory] = useState<CockpitHistory | null>(null);
  // The watched session's LATCHED epoch anchor (era-5B J-06, restructured onto the shared hook).
  // `history.epoch_anchor` (Data Contract row 13) is "the real UTC epoch a watched session's
  // logical time 0 maps to" — a STABLE per-watch value the engine sets once at watch-start. But
  // the raw `history` object itself transiently nulls on every VIEW SWITCH (the poll effect
  // resets it), so reading the anchor off `history` directly made the band overlay vanish and
  // refetch on every Tape/History toggle. This latch keeps the anchor once it resolves — reset
  // ONLY on a ticker change (a new watch is genuinely a new session) — so the tradable-map read
  // below stays keyed on a stable value for the whole watch: at most one fetch per watch, and
  // the bands never flash off on a view switch.
  const [latchedAnchor, setLatchedAnchor] = useState<number | null>(null);
  useEffect(() => {
    setLatchedAnchor(null); // a NEW ticker is a new watched session -- its anchor must re-resolve
  }, [ticker]);
  useEffect(() => {
    // Latch only a RESOLVED anchor; the transient nulls of a view-switch reset never clear it.
    if (history?.epoch_anchor != null) setLatchedAnchor(history.epoch_anchor);
  }, [history?.epoch_anchor]);
  // `as_of` is the WATCHED SESSION's own current moment, verbatim: the latched anchor converted
  // to ISO — a real market epoch for a historical replay, so during e.g. the 2026-06-22 replay
  // this correctly resolves THAT session's own prior-close basis (2026-06-18) rather than
  // today's. `null` until the anchor resolves: the shared hook then DEFERS the fetch entirely
  // (no request, phase "loading", never "idle") — there is NO wall-clock fallback anywhere in
  // this computation; `_resolve_basis` (tradability.py) alone decides the prior session
  // server-side. The epoch-seconds -> ms conversion is the SAME pure unit conversion this file
  // already does for candle timestamps (`toClock`), never a date computation of "which session".
  const tradabilityAsOfIso =
    latchedAnchor != null ? new Date(latchedAnchor * 1000).toISOString() : null;
  // The watched symbol's tradable bands (era-5B J-06) — the SAME shared read /structure's
  // Tradable Map uses (`lib/useTradability.ts`; one fetch path, one backend route, one durable
  // cache). Additive/non-blocking: `idle`/`loading`/`error` render nothing extra — the chart +
  // tape markers never wait on this fetch.
  const tradabilityState = useTradability(ticker, tradabilityAsOfIso);
  // The symbol's recorded bar-series metadata (candles omitted) — drives the "History" group's
  // timeframe options; the SAME shared read /structure uses (`lib/useRecordedSeries.ts`). A
  // SIM-*/unrecorded symbol resolves to [] (the honest empty History group).
  const { series: recordedSeries } = useRecordedSeries(ticker);
  // The strategy registry (era-5B J-06) — ticker-independent config/registry data, fetched once.
  // Supplies the confluence chip's rejection/breakthrough state mapping.
  const [strategies, setStrategies] = useState<StrategiesPayload | null>(null);

  const viewKey = view.kind === "tape" ? `tape:${view.bar}` : `history:${view.timeframe}`;

  // The no-lookahead recorded-store window (History mode only): the bars strictly BEFORE the replay
  // start (the anchor's timeframe bucket), paged backward on scroll. `beforeOnly` refuses to page
  // forward, and the cursor `anchor_bucket_start - 1` (inclusive) keeps every fetched store bar's ts
  // < the anchor bucket, so the store never reveals a bar at/after the replay start (the live tape
  // owns that side). Called unconditionally (hooks rule); `symbol: null` until the boundary resolves.
  const anchorBucketStart =
    history?.kind === "timeframe" ? history.anchor_bucket_start : null;
  const barWindow = useBarWindow(
    view.kind === "history" && anchorBucketStart != null ? ticker : null,
    view.kind === "history" ? view.timeframe : null,
    anchorBucketStart != null ? (anchorBucketStart - 1) * 1000 : NaN,
    { beforeOnly: true },
  );

  // The live tape bars (the moving bars), mapped to the shared real-epoch `BarRow` shape the chart
  // draws. Tape mode: the logical-second candles at true clock time (`epoch_anchor + logical_ts`,
  // volume unknown -> 0). History mode: the wall-clock timeframe candles VERBATIM (already real-epoch
  // rows with volume). Read-only projections — no re-binning.
  const liveBars = useMemo<BarRow[]>(() => {
    if (!history) return [];
    if (history.kind === "tape") {
      const anchor = history.epoch_anchor ?? 0;
      return history.bars.map((b) => ({
        ts: Math.round(anchor + b.time),
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
        volume: 0,
      }));
    }
    return history.timeframe_bars;
  }, [history]);

  // The tape-state + thesis markers, as ready-to-draw specs the chart renders verbatim. Tape-state
  // markers sit ABOVE the bar (down-arrow, colored by state); thesis markers sit BELOW (circle for a
  // verdict / first confirmation, up-arrow for an entry/exit mark) — the SAME two-layer language the
  // retired inline chart used. In History mode a tape-state marker is placed on its served containing
  // bucket (`bucket_ts`); a thesis marker is floored to that timeframe's bucket, both pure display
  // placement using served values.
  const extraMarkers = useMemo<ChartMarkerSpec[]>(() => {
    if (!history) return [];
    const anchor = history.epoch_anchor ?? 0;
    const toClock = (logical: number) => Math.round(anchor + logical);
    const stateSpecs: ChartMarkerSpec[] =
      history.kind === "tape"
        ? history.markers.map((m) => ({
            time: toClock(m.time),
            position: "aboveBar",
            color: MARKER_COLORS[m.state] ?? "#fbbf24",
            shape: "arrowDown",
            text: STATE_LABELS[m.state] ?? m.state,
          }))
        : history.markers.map((m) => ({
            time: m.bucket_ts ?? toClock(m.time),
            position: "aboveBar",
            color: MARKER_COLORS[m.state] ?? "#fbbf24",
            shape: "arrowDown",
            text: STATE_LABELS[m.state] ?? m.state,
          }));
    const secs = history.kind === "timeframe" ? history.timeframe_seconds : 0;
    const placeThesis = (logical: number) =>
      secs > 0 ? Math.floor((anchor + logical) / secs) * secs : toClock(logical);
    const geometry = thesis?.geometry;
    const thesisSpecs: ChartMarkerSpec[] = geometry
      ? geometry.markers.map((m) => {
          if (m.kind === "entry" || m.kind === "exit") {
            // The user's own action mark — its own slate treatment with the verbatim mono price.
            const priceText = m.price != null ? ` ${m.price.toFixed(2)}` : "";
            return {
              time: placeThesis(m.logical_ts),
              position: "belowBar",
              color: MARK_COLOR,
              shape: "arrowUp",
              text: `${m.label}${priceText}`,
            };
          }
          // A verdict-transition marker or the first-confirmation marker — verdict palette, circle.
          const color =
            m.kind === "first_confirmation"
              ? VERDICT_COLORS.confirming
              : VERDICT_COLORS[m.verdict ?? "pending"] ?? "#94a3b8";
          return {
            time: placeThesis(m.logical_ts),
            position: "belowBar",
            color,
            shape: "circle",
            text: m.label,
          };
        })
      : [];
    return [...stateSpecs, ...thesisSpecs];
  }, [history, thesis]);

  // The thesis-geometry price lines (invalidation always; level when set), as dashed reference lines
  // the chart draws verbatim. `null`/no geometry => none (the exact no-thesis render).
  const extraPriceLines = useMemo<ChartPriceLineSpec[]>(() => {
    const geometry = thesis?.geometry;
    if (!geometry) return [];
    return geometry.price_lines.map((pl) => ({
      price: pl.price,
      color: PRICE_LINE_COLORS[pl.kind] ?? "#94a3b8",
      lineWidth: 1,
      lineStyle: 2, // LineStyle.Dashed
      axisLabelVisible: true,
      title: pl.label,
    }));
  }, [thesis]);

  // --- Poll …/history verbatim while a ticker is watched (reset on ticker/view change) --------
  useEffect(() => {
    if (!ticker) {
      setHistory(null);
      return;
    }
    let cancelled = false;
    setHistory(null);

    async function pull() {
      if (view.kind === "tape") {
        const data = await fetchHistory(ticker as string, view.bar);
        if (cancelled) return;
        setHistory(data ? { ...data, kind: "tape" } : null);
      } else {
        const data = await fetchTimeframeHistory(ticker as string, view.timeframe);
        if (cancelled) return;
        setHistory(data ? { ...data, kind: "timeframe" } : null);
      }
    }
    pull();
    const id = setInterval(pull, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [ticker, viewKey]);

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

  if (!ticker) return null;

  // The recorded timeframes offering live bars (recorded ∩ the fixed-duration supported set),
  // shortest-first. Empty for a SIM-*/unrecorded symbol — the honest empty History group.
  const historyTimeframes = timeframesInOrder(recordedSeries).filter((tf) =>
    (TIMEFRAMES_WITH_LIVE_BARS as readonly string[]).includes(tf),
  );

  // The recorded store context (History mode only): bars strictly LEFT of the replay start, with the
  // "start" boundary marker on the last of them. Tape mode has no recorded context.
  const storeBars = view.kind === "history" ? barWindow.bars : [];
  const boundaryEpochMs = anchorBucketStart != null ? anchorBucketStart * 1000 : NaN;

  // --- Confluence chip (era-5B J-06) ----------------------------------------------------------
  // A pure DISPLAY CONJUNCTION over already-fetched/served values — price-in-band × served tape
  // state × the served rejection/breakthrough mapping. No scoring, no clustering, no client-side
  // mapping literal: `rejectionState`/`breakthroughState` are read off the FETCHED
  // structure_tape_map entry, never restated (the only place this file hardcodes the four tape-
  // state names is the pre-existing MARKER_COLORS/STATE_LABELS cosmetic dicts above, unrelated to
  // this decision). The last price is the last live bar's close (the current tape price).
  const lastPrice = liveBars.length > 0 ? liveBars[liveBars.length - 1].close : null;
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
    <Panel title="Price Chart — Recorded History + Live Tape" className="mb-4">
      <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Tape</span>
          <div className="flex gap-1" role="group" aria-label="Tape bar size">
            {HISTORY_BAR_SIZES.map((size) => {
              const selected = view.kind === "tape" && view.bar === size;
              return (
                <button
                  key={`tape-${size}`}
                  type="button"
                  onClick={() => setView({ kind: "tape", bar: size })}
                  aria-pressed={selected}
                  className={segmentClass(selected)}
                >
                  {size}s
                </button>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">History</span>
          {historyTimeframes.length > 0 ? (
            <div className="flex flex-wrap gap-1" role="group" aria-label="History timeframe">
              {historyTimeframes.map((tf) => {
                const selected = view.kind === "history" && view.timeframe === tf;
                return (
                  <button
                    key={`hist-${tf}`}
                    type="button"
                    onClick={() => setView({ kind: "history", timeframe: tf })}
                    aria-pressed={selected}
                    className={segmentClass(selected)}
                  >
                    {tf}
                  </button>
                );
              })}
            </div>
          ) : (
            <EmptyHint>No recorded bars for {ticker}.</EmptyHint>
          )}
        </div>
      </div>

      {/* The shared chart renderer. In History mode the recorded store bars sit left of the "start"
          marker and the live tape bars grow to its right; in Tape mode only the live tape bars show.
          The band overlay + tape-state/thesis markers are drawn from the served values passed here —
          this container computes none of them. */}
      <StructureChart
        key={`${ticker}|${viewKey}`}
        bars={storeBars}
        liveBars={liveBars}
        levels={[]}
        bands={tradabilityState.data?.bands ?? []}
        asOfTs={boundaryTs(storeBars, boundaryEpochMs)}
        asOfLabel="start"
        onNeedOlder={barWindow.loadOlder}
        loadingMore={barWindow.loading}
        secondsVisible={view.kind === "tape"}
        clockFormatter
        extraMarkers={extraMarkers}
        extraPriceLines={extraPriceLines}
      />

      <p className="mt-2 text-xs text-slate-500" data-testid="cockpit-chart-caption">
        {view.kind === "history"
          ? `Recorded ${view.timeframe} bars sit left of the start marker; bars to its right are built live from the tape.`
          : `Logical ${view.bar}s bars built live from the tape.`}
      </p>

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
