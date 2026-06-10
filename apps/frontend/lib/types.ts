// Shapes mirrored from the backend engine snapshot (app/serializers.py). The UI renders
// these values verbatim — it never recomputes spread, ratios, impacts, or confidence.

export interface Market {
  bid: number | null;
  ask: number | null;
  spread: number | null;
  last: number | null;
}

export interface TradeRow {
  timestamp: number;
  price: number;
  size: number;
  side: "buy" | "sell" | "unknown";
}

export type FeatureSet = Record<string, number>;

// --- Research: thesis projection + taxonomy (capability 23/24) ---------------------------------
// The active-thesis projection — the SAME object returned by GET /research/thesis/active and
// carried on the WS frame's `thesis` key (verbatim-equal by construction). The strip renders these
// values VERBATIM; it derives nothing (no client-side verdict/status recompute). `null` when no
// thesis is active (a normal state, not an error). NOTE: `risk_flags` is deliberately ABSENT this
// iteration (an always-empty list would dishonestly read as "no risks found" — J-49 adds it).
export type ThesisVerdict =
  | "pending"
  | "confirming"
  | "weakening"
  | "rejecting"
  | "invalidated"
  | "expired";

// A frozen expected-behaviour statement with its LIVE status (recomputed server-side per event).
export type StatementStatus = "not_yet" | "met" | "violated";
export interface ThesisStatement {
  text: string;
  status: StatementStatus;
}

export interface ThesisProjection {
  id: string;
  ticker: string;
  setup_type: string;
  direction: "long" | "short";
  invalidation_price: number;
  level_price: number | null;
  status: string;
  verdict: ThesisVerdict;
  statements: ThesisStatement[];
  entry_context: Record<string, unknown>;
  bound_source: string;
  data_feed: "sim" | "sip" | "iex";
  config_fingerprint: string;
  // "ok" normally; "failed" if the research monitor or its store write errored — surfaced honestly.
  monitor_status: "ok" | "failed";
}

// GET /research/taxonomy — the single backend owner of every research label. The declare form is
// built from this (which setups exist, their display names, and whether each needs a level field);
// the frontend hardcodes none of it.
export interface TaxonomySetup {
  id: string;
  name: string;
  requires_level: boolean;
  statements: { text: string; kind: string }[];
}
export interface TaxonomyEnum {
  id: string;
  name: string;
}
export interface ResearchTaxonomy {
  setups: TaxonomySetup[];
  directions: TaxonomyEnum[];
  verdicts: TaxonomyEnum[];
  statement_statuses: string[];
  disclaimer: string;
}

// The result of POST /research/thesis — `ok` with the projection, or a backend error with its
// status + detail surfaced inline (422/409/404 — never a silent coercion).
export interface DeclareResult {
  ok: boolean;
  thesis?: ThesisProjection | null;
  status?: number;
  error?: string;
}

export interface TapeSnapshot {
  ticker: string;
  scenario: string;
  // The engine's canonical stream status (a free string here), owned once by the engine/feeder and
  // read VERBATIM — the UI never recomputes it. Values:
  //   "connecting" (pre-open) | "waiting" (stream open, no first event yet — J-26) |
  //   "live" (first event arrived) | "stale" (delivery-gap lull, incl. a waiting that never got a
  //   first event) | "paused" (J-19) | "closed" (stopped/exhausted) |
  //   "failed" (the feeder raised after connecting — J-27).
  // "waiting"/"failed" are added in J-25–J-27; an empty cold-start snapshot reads "waiting", so it
  // never renders as a settled "live" cockpit.
  stream_status: string;
  // Canonical paused flag (Data Contract row 11), owned once by the engine/feeder. The UI READS
  // this to render the PAUSED indicator and toggle the Pause/Resume control — it never guesses
  // paused client-side. Optional for backward compatibility with any pre-J-19 snapshot shape.
  paused?: boolean;
  warm?: boolean;
  timestamp: number;
  market: Market;
  tape_state: string;
  confidence: number;
  primary_window: string;
  features: Record<string, FeatureSet>; // keyed by window label, e.g. "30s"
  headline_features: FeatureSet;
  observations: string[];
  event_log: string[];
  recent_trades: TradeRow[];
  // Additive `thesis` key (data-contract row 15): the active-thesis projection (same object as
  // GET /research/thesis/active), or `null` when none. Optional so a pre-research snapshot shape
  // (e.g. the REST initial-paint assembly) is still valid; the strip reads it verbatim.
  thesis?: ThesisProjection | null;
}

// Client-side connection status for the pre-snapshot / no-snapshot window. "failed" (J-23) is the
// surfaced connect-failure: the initial snapshot fetch threw (backend unreachable / client-side
// timeout) AND/OR the WS errored/closed before any snapshot arrived — never silently swallowed.
export type ConnStatus = "idle" | "connecting" | "live" | "closed" | "failed";

// The watch data-source mode (wire values; the selector renders Live / Historical / Simulated).
// "sim" is the default and preserves the existing backward-compatible no-body watch.
export type DataSourceMode = "sim" | "live" | "historical";

// Optional params carried by the watch body. `mode` selects the source; `start`/`end`/`speed`
// drive a Historical replay (fetched + replayed through the engine — J-11).
export interface WatchParams {
  mode: DataSourceMode;
  start?: string;
  end?: string;
  speed?: number;
}

// One symbol-search suggestion from GET /symbols/search (J-13) — rendered verbatim.
export interface SymbolMatch {
  symbol: string;
  name: string;
}

// Price-history / prediction-chart shapes from GET /tape/{ticker}/history?bar= (J-17 / J-18).
// The chart renders these VERBATIM — it never re-bins candles or re-derives a marker's state.

// One OHLC candle: `time` is the bin's left edge in LOGICAL seconds (the engine's timeline).
export interface OhlcBar {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

// One meaningful tape-state-transition marker. `state`/`confidence` are the engine's OWN
// classifier values at the transition (reused verbatim — never recomputed in the UI). Only
// meaningful states appear (buyer_control | seller_control | bid_absorption | ask_absorption);
// a transition into `unclear` is not marked.
export interface TapeMarker {
  time: number;
  state: string;
  confidence: number;
}

// GET /tape/{ticker}/history?bar= response — the OHLC series + markers for one bar size. An
// empty (or not-yet-warmed) window yields empty arrays (the chart shows an empty treatment).
//
// `epoch_anchor` (Data Contract row 13, J-31) is the canonical display anchor: the real UTC epoch
// (SECONDS) that logical-time 0 maps to. The chart renders TRUE clock time as `epoch_anchor +
// bar.time` (real market time for historical; a synthetic session clock for simulated) — a pure
// additive offset, so the chart still recomputes no price/side/state. `null` when there is no
// anchor (an empty/anchorless window): the chart stays empty and fabricates no timestamps.
export interface TapeHistory {
  bar: number;
  epoch_anchor: number | null;
  bars: OhlcBar[];
  markers: TapeMarker[];
}

// The bar sizes (logical seconds) the chart's selector offers — must match the backend's
// configured `history_bar_sizes`. An out-of-set value is rejected by the backend with a 422.
export const HISTORY_BAR_SIZES = [10, 30, 60] as const;
export type HistoryBarSize = (typeof HISTORY_BAR_SIZES)[number];

// Distinct honest real-data failure reasons surfaced by POST /watch (data-contract row 9). The
// UI renders a distinct non-cockpit panel per reason — never a fabricated cockpit, never a
// silent fall-back to Simulated.
export type FailureReason =
  | "provider_unavailable"
  | "symbol_not_tradable"
  | "no_data_for_window"
  | "market_closed";

// GET /market/clock (data-contract row 8) — the market session status read VERBATIM by the Live
// market-status indicator (the UI never recomputes open/closed). `available:false` (with null
// fields) means no credentials or the clock could not be reached — the indicator shows
// "unavailable", never a fabricated open/closed. `next_open`/`next_close` are ISO-8601 UTC.
export interface MarketClock {
  available: boolean;
  is_open: boolean | null;
  next_open: string | null;
  next_close: string | null;
}
