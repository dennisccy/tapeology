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

export interface TaxonomyEnum {
  id: string;
  name: string;
}
// GET /research/taxonomy — the single backend owner of every research label the KEPT surfaces
// read. era-5D J-01 ("The Clean Slate" demolition interlude) slimmed the served payload to
// exactly this shape: the feed_basis block is the ONLY family a kept surface reads
// (FeedBasisBadge.tsx's feed label + the live IEX-vs-SIP disclosure line). Every other family
// this type used to carry (setups/directions/verdicts/statuses/mistake_tags/grades/excursions/
// analytics/studies/management_stances/checklist_*/hints/sound_cue) is gone with its owner.
export interface ResearchTaxonomy {
  feed_basis: FeedBasisTaxonomy;
}

// The feed-basis taxonomy block (J-67) — per-feed display labels + the live IEX-vs-SIP disclosure
// line, owned once on the backend and rendered VERBATIM (the frontend never hardcodes a feed label
// or the disclosure text).
export interface FeedBasisTaxonomy {
  feeds: TaxonomyEnum[]; // [{id:"sim"|"iex"|"sip", name}]
  live_disclosure: string;
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
  // Canonical feeder-owned delivery lag (Data Contract row 14, J-63/J-64): how far the processed
  // tape trails real time, in SECONDS. Owned once by the feeder and read VERBATIM here — the UI does
  // NO wall-clock arithmetic (zero client-side computation; it reads the SAME value the `tape_lag_ok`
  // entry-checklist check reads). `null`/absent before the feeder stamps a lag (cold construction) —
  // an honest "no lag measured", rendered as an explicit placeholder, never a fabricated 0.
  delivery_lag_seconds?: number | null;
  // Canonical current-watch FEED BASIS (Data Contract row 29, J-67): sim | iex | sip — computed ONCE
  // server-side by the one config-aligned scenario->data_feed mapping, served on /summary and
  // re-exposed by the WS frame VERBATIM. The cockpit feed-basis badge reads THIS value (never
  // client-derived from `scenario`). Optional/absent for a pre-J-67 snapshot shape (the badge then
  // renders nothing — honest absence, never a fabricated "live"/"iex" guess).
  data_feed?: "sim" | "iex" | "sip";
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
// `volume` sums the bin's own trade sizes (engine/history.py's `_BarAccumulator`) — the same
// figure the wall-clock `BarRow` carries, so the chart's volume pane draws real traded volume in
// tape mode as well as history mode.
export interface OhlcBar {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
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

// The wall-clock timeframes the cockpit chart's "History" group offers — the fixed-duration subset
// the tape can honestly bin live moving bars into (mirrors the backend's `TIMEFRAME_SECONDS` in
// app/engine/history.py). `1w`/`1mo` are deliberately absent (calendar-irregular). The chart offers
// only the intersection of these with the timeframes actually RECORDED for the symbol; the backend's
// own 422 stays the validation authority (this list is a display grouping, the HISTORY_BAR_SIZES
// precedent).
export const TIMEFRAMES_WITH_LIVE_BARS = [
  "1m",
  "5m",
  "15m",
  "1h",
  "4h",
  "8h",
  "1d",
] as const;

// One wall-clock tape-state marker: the same state/confidence as the logical-second `TapeMarker`,
// plus `bucket_ts` — the real-epoch left edge of the timeframe bucket that CONTAINS the marker
// (`null` when the engine has no anchor yet). The chart places the marker on its containing candle
// at a coarse timeframe from this served value; it re-buckets nothing.
export interface TapeTimeframeMarker {
  time: number;
  state: string;
  confidence: number;
  bucket_ts: number | null;
}

// GET /tape/{ticker}/history?timeframe= response — the wall-clock, real-epoch OHLC+volume candles
// built LIVE from the tape (the cockpit chart's "history" mode), plus the no-lookahead boundary.
// `timeframe_bars` share the recorded store's `BarRow` shape (real UTC-epoch `ts` + volume), so the
// chart draws them beside store candles on one grid. `anchor_bucket_start` is the real-epoch left
// edge of the anchor's bucket (`null` when anchorless) — the chart clamps its recorded-store window
// strictly before it (no lookahead) and grows the live tape's own bars from it onward.
export interface TapeTimeframeHistory {
  timeframe: string;
  timeframe_seconds: number;
  epoch_anchor: number | null;
  anchor_bucket_start: number | null;
  timeframe_bars: BarRow[];
  markers: TapeTimeframeMarker[];
}

// The cockpit chart's one polled-history state, discriminated by the active view: the logical-second
// tape bars (`?bar=`) or the wall-clock timeframe bars (`?timeframe=`). Both variants carry
// `epoch_anchor` at the top level, so the tradable-band fetch keys on `history?.epoch_anchor`
// uniformly regardless of which mode is showing.
export type CockpitHistory =
  | (TapeHistory & { kind: "tape" })
  | (TapeTimeframeHistory & { kind: "timeframe" });

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

// --- The PnL ledger + the profile registry (era 3, J-05) ---------------------------------------

// One split's measurement inside a PnL-ledger row (GET /research/pnl/ledger — Data Contract
// row 32). Values are the backend's stored aggregates served VERBATIM; `insufficient_sample` is
// the backend's config-owned label marker (n < the served `min_sample_size`) — the page renders
// it, never re-derives it.
export interface PnlSplitMeasurement {
  net_r: number;
  net_usd: number;
  n: number;
  insufficient_sample: boolean;
}

// The two frozen splits, always SEPARATE (never pooled — no combined figure exists anywhere).
export interface PnlSplitPair {
  train: PnlSplitMeasurement;
  holdout: PnlSplitMeasurement;
}

// One split's provenance stamps (read from the cited backtest report's own stored stamps).
export interface PnlSplitProvenance {
  backtest_id: string;
  dataset_id: string;
  dataset_checksum: string;
}

// One append-only ledger row. A FOUNDING row has no prior incumbent: `baseline` is explicitly
// null (the page renders an explicit absence marker — NEVER fabricated zeros).
export interface PnlLedgerRow {
  enhancement_id: string;
  title: string;
  founding: boolean;
  baseline: PnlSplitPair | null;
  candidate: PnlSplitPair;
  provenance: {
    strategy_id: string;
    profile: string;
    config_fingerprint: string;
    train: PnlSplitProvenance;
    holdout: PnlSplitProvenance;
  };
  created_wall_ts: number;
  created_utc: string;
}

// GET /research/pnl/ledger — the whole served projection: the visible simulated register (the
// backend's ONE register constant — the page renders THIS string, never a frontend copy), the
// config-owned label minimum, and the stored rows verbatim in append order.
export interface PnlLedger {
  register: string;
  min_sample_size: number;
  rows: PnlLedgerRow[];
}

// GET /research/profiles (Data Contract row 33) — the config-owned indicator-profile registry
// plus the current champion pointer, served verbatim. The champion is read ONLY from here —
// never inferred from ledger provenance, never hardcoded.
export interface IndicatorProfile {
  id: string;
  frozen: boolean;
  is_default: boolean;
}

export interface ProfilesPayload {
  profiles: IndicatorProfile[];
  champion: { strategy_id: string; profile: string };
}

// --- Structure: S/R levels, confluence zones, and recorded bar series ---------------------------
// (era-4 capabilities 1-3, surfaced this interlude at /structure, J-01). Every field below is read
// VERBATIM from its canonical endpoint (GET /research/levels, GET /research/bars) — the Structure
// page recomputes no price, class, score, or candle.

// One recorded OHLC candle row, as stored (GET /research/bars — Data Contract row 38). Distinct
// shape from `OhlcBar` above (that one is the tape engine's LOGICAL-second candle from
// GET /tape/{ticker}/history); this is a bar-store row with a real UTC-epoch-seconds `ts` and a
// `volume` field.
export interface BarRow {
  ts: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// One registered bar series' metadata + embedded candles, served verbatim by GET /research/bars
// (list) and GET /research/bars/{id} (detail). `bars` is OPTIONAL because the list endpoint's
// `?include_bars=false` projection omits the key entirely (the honest "not asked for" — never an
// empty array, which would be indistinguishable from a series holding no candles). `bar_count`
// always reports the series' true stored length, so a metadata-only record still states honestly
// how many candles exist behind it.
export interface BarSeriesRecord {
  id: string;
  symbol: string;
  timeframe: string;
  window_start_utc: string;
  window_end_utc: string;
  feed: string;
  bar_count: number;
  checksum: string;
  created_utc: string;
  bars?: BarRow[];
  // Coverage (server-owned, present on anything recorded since the vendor-cap work): the first and
  // last bar's own timestamps, and the vendor cap that shortened the fetch — `null` when the
  // requested window was served in full. Without these, a recording whose window says
  // `2026-01-01..2026-07-21` but which holds only the last 30 days (Yahoo caps 1m there) is
  // indistinguishable from a complete one. Optional: recordings made before this existed lack them.
  covered_start_utc?: string;
  covered_end_utc?: string;
  vendor_limit?: string | null;
}

// GET /research/bars/{id}/candles — one bounded, cursor-anchored window of a series' stored
// candles, served verbatim. The paging seam the /structure charts scroll through instead of
// pulling a whole series into the browser: `has_more_before`/`has_more_after` say honestly whether
// stored rows exist outside this window on that side, so the caller knows when to stop asking.
export interface BarCandlesPage {
  bar_series_id: string;
  symbol: string;
  timeframe: string;
  bar_count: number;
  bars: BarRow[];
  has_more_before: boolean;
  has_more_after: boolean;
}

// GET /research/candles — the same bounded window, but over EVERY recorded series for one
// symbol+timeframe folded into one ascending series (a symbol accumulates many overlapping
// immutable recordings; paging just one of them runs out of history while a longer recording of the
// same pair sits on disk). `series_count`/`series_ids` name the contributing recordings;
// `revised_timestamps` counts the timestamps more than one recording held with differing values
// (resolved in favour of the most recently fetched recording, server-side — reported, not hidden);
// `bar_count` is the merged total available behind this window.
export interface MergedCandlesPage {
  symbol: string;
  timeframe: string;
  bars: BarRow[];
  bar_count: number;
  series_count: number;
  series_ids: string[];
  revised_timestamps: number;
  has_more_before: boolean;
  has_more_after: boolean;
  integrity_errors: { file: string; error: string }[];
}

// GET /research/bars — the full list payload (no symbol query param; callers filter the returned
// array client-side by the already-served `symbol` field). A corrupt file surfaces explicitly in
// `integrity_errors` (never silently hidden, never served as data) — unused by the Structure page
// this iteration, but part of the endpoint's real shape.
export interface BarSeriesListResult {
  bar_series: BarSeriesRecord[];
  integrity_errors: { file: string; error: string }[];
}

// POST /research/bars (era-5 J-05) result — the ONE new explicit write action in the app: fetch
// (or store-first serve) a real bar series for a chosen symbol/timeframe/date-range. `{ok,
// bar_series}` on success (a fresh Yahoo fetch OR a store-first hit — both `200`, never `409` for a
// repeat window), or `{ok:false, error, status}` with the backend's own 422/503/504/409 detail
// surfaced verbatim.
export interface RecordBarSeriesResult {
  ok: boolean;
  bar_series?: BarSeriesRecord;
  status?: number;
  error?: string;
}

// One deterministic support/resistance level (GET /research/levels — Data Contract row 39). `type`
// is one of "swing-pivot" | "prior-period-extreme" — kept as `string` (not a union) so an
// unrecognized future type still renders rather than silently vanishing at a type guard.
export interface SrLevel {
  price: number;
  timeframe: string;
  type: string;
  touch_count: number;
  strength: number;
}

// One A/B/C confluence zone (GET /research/levels' `confluence_zones` — Data Contract row 39). The
// `class` badge and `score` are read VERBATIM here — never recomputed from the member levels'
// breadth or strength.
export interface ConfluenceZone {
  levels: SrLevel[];
  score: number;
  class: "A" | "B" | "C";
}

// GET /research/levels?symbol=&as_of= — the full served projection, read VERBATIM. Two fields
// together carry THREE honest, distinct states: `no_bar_series_for_symbol: true` (no recorded
// series at all) vs. `false` with an empty `levels` (series exist, nothing derivable at `as_of`)
// vs. non-empty `levels` with an empty `confluence_zones` (levels exist, no qualifying cluster).
export interface LevelsResponse {
  symbol: string;
  as_of: string;
  levels: SrLevel[];
  no_bar_series_for_symbol: boolean;
  confluence_zones: ConfluenceZone[];
}

// --- Structure: strategy registry + champion (era-4 capability 4, surfaced this interlude at the
// /structure Registry section, J-02). Every field is read VERBATIM from GET /research/strategies
// (app/research/strategies.py's `strategies_projection`, built entirely from
// `Config.strategy_definition`) — the Registry section recomputes no entry/exit rule and no
// class-scaled value.

// One exit rule's own descriptor. `rule` is the one field every exit shares; the class-scaled maps
// are present ONLY where the backend's OWN grammar carries them (`stop_bps_by_class` on
// structure_tape's `r_stop`; `r_multiple_by_class` on its `reward_target`) — v1's `r_stop` carries
// neither (an honest field omission, never a fabricated map for v1). One shared shape for both
// `r_stop` and `reward_target` rather than two near-duplicate interfaces, mirroring `SrLevel.type`'s
// existing precedent of tolerating a broader shape rather than a rigid per-strategy union.
export interface StrategyExitRule {
  rule: string;
  stop_bps_by_class?: Record<string, number>;
  r_multiple_by_class?: Record<string, number>;
}

// One strategy's exit block. `reward_target` is present ONLY on structure_tape — v1 genuinely has
// no reward-target exit (an honest omission, not a gap; see the dev handoff for why this and
// `dataset_end` are modelled even though the spec's "r_stop -> reward_target -> state_flip ->
// horizon" precedence phrase itself only names four of these five fields).
export interface StrategyExits {
  r_stop: StrategyExitRule;
  reward_target?: StrategyExitRule;
  horizon_seconds: number;
  state_flip: { rule: string };
  dataset_end: { rule: string };
}

// One strategy's `entries` block (GET /research/strategies). `rule` is the one field every
// strategy shares; the rest are present ONLY where the backend's OWN grammar carries them
// (`structure_tape` / `structure_tape_map`'s `structure_level_tape_confirmation` rule —
// config.py:1516-1523) — v1's `entries` carries only `rule` (an honest field omission, never a
// fabricated value for v1). `rejection_states`/`breakthrough_states` are the era-5B J-06 cockpit
// confluence chip's OWN mapping source (Record<direction, tape-state-name>) — read verbatim by
// PriceChart.tsx, never restated as a client-side literal.
export interface StrategyEntries {
  rule: string;
  proximity_band_bps?: number;
  rejection_states?: Record<"long" | "short", string>;
  breakthrough_states?: Record<"long" | "short", string>;
  arm_cooldown_seconds?: number;
  concurrency?: string;
}

// One registered strategy (GET /research/strategies — Data Contract row 40/41). `size_multiple_by_class`
// is present ONLY on structure_tape (v1 has no class-scaled simulated size) — an honest field
// omission, never a fabricated map for v1.
export interface Strategy {
  strategy_id: string;
  entries: StrategyEntries;
  exits: StrategyExits;
  fees: { per_share: number; min_per_trade: number };
  slippage: { spread_fraction: number };
  dollars_per_r: number;
  size_multiple_by_class?: Record<string, number>;
}

// GET /research/strategies — the full served projection, read VERBATIM. `champion` reuses
// `ProfilesPayload`'s own champion shape byte-for-byte (the backend serves both from the identical
// `store.get_champion_pointer()` call) — this is NOT a second champion shape.
export interface StrategiesPayload {
  strategies: Strategy[];
  champion: ProfilesPayload["champion"];
}

// --- Structure: the structure_tape-vs-v1 backtest comparison (era-3 capability 4 / era-4
// capability 5, surfaced this interlude at the /structure Comparison section, J-03). Every field
// below is read VERBATIM from GET /research/datasets and GET /research/backtests/{id}
// (app/research/backtests.py's `_aggregate` / `_aggregate_by_class`, the runner's persisted
// `result` block) — the Comparison section recomputes no R, $, win-rate, or class partition.

// One registered dataset's metadata (GET /research/datasets — Data Contract row 30). A dataset is
// a checksum-verified store record like `BarSeriesRecord`, but carries no embedded `bars` field —
// its content is a raw trade/quote event stream, not candles.
export interface Dataset {
  id: string;
  symbol: string;
  window_start_utc: string;
  window_end_utc: string;
  data_feed: string;
  event_counts: { trades: number; quotes: number; total: number };
  checksum: string;
  split: string;
  source: string;
  source_kind: string;
  source_id: string;
  epoch_anchor: number | null;
  created_utc: string;
}

// GET /research/datasets — the full list payload (mirrors `BarSeriesListResult`'s shape: a LIST
// endpoint with no query params). A corrupt file surfaces explicitly in `integrity_errors` — never
// silently hidden, never served as data.
export interface DatasetsListResult {
  datasets: Dataset[];
  integrity_errors: { file: string; error: string }[];
}

// One population's aggregate (`GET /research/backtests/{id}`'s `result.aggregates` /
// `result.null_baseline.aggregates` — `backtests.py`'s `_aggregate()`). `win_rate` /
// `max_drawdown_r` are honestly `null` on an empty population (n=0) — never a fabricated 0.
export interface BacktestAggregate {
  n: number;
  gross_r: number;
  net_r: number;
  gross_usd: number;
  net_usd: number;
  win_rate: number | null;
  max_drawdown_r: number | null;
}

// One class's aggregate inside `result.aggregates_by_class` — the SAME `BacktestAggregate` shape
// plus the config-owned `insufficient_sample` label (`backtests.py`'s `_aggregate_by_class()`,
// reusing the existing `pnl_min_sample_size` floor — never a fourth minimum). Rendered via
// `Object.entries()` in the payload's own key order (the `ClassMapTable` precedent) — always all
// three classes (A/B/C), even a class with zero trades (the honest `_aggregate([])` emptiness).
export interface BacktestClassAggregate extends BacktestAggregate {
  insufficient_sample: boolean;
}

// The terminal `result` block (`GET /research/backtests/{id}`) — present ONLY once `status` is
// "done". A `cancelled` backtest carries NO result block at all (`backtests.py`'s own docstring:
// "a cancelled backtest carries NO result block" — a partial simulated PnL is never served).
// `dataset`/`strategy` reuse the EXISTING `Dataset` / `Strategy` types verbatim (the report echoes
// the exact stored dataset metadata and the resolved strategy config — never a second shape).
export interface BacktestResult {
  register: string;
  dataset: Dataset;
  strategy: Strategy;
  config_fingerprint: string;
  aggregates: BacktestAggregate;
  aggregates_by_class: Record<string, BacktestClassAggregate>;
  null_baseline: {
    seed: number;
    entry_count: number;
    aggregates: BacktestAggregate;
  };
}

// GET /research/backtests/{id} (and each `GET /research/backtests` list row) — the full backtest
// projection, read VERBATIM. `result` is present only once `status` is "done"; `error` is present
// only once `status` is "failed" (an explicit error, never an empty success); `events_processed` is
// present only while "running" (throttled progress). The Comparison section renders nothing until
// `status === "done"` (and `result` itself is present) — a terminal-with-results gate that
// deliberately excludes "cancelled" (which never carries a result here).
export interface Backtest {
  id: string;
  status: "queued" | "running" | "done" | "cancelled" | "failed";
  dataset_id: string;
  strategy_id: string;
  profile: string;
  events_processed?: number;
  error?: string;
  result?: BacktestResult;
}

// Body for POST /research/backtests (era-3 capability 4, J-03) — exactly the three fields
// `BacktestRequest` accepts (routes.py:160-171); no `null_baseline_seed` field exists on this
// request (the backend always falls back to its own config-owned default seed).
export interface CreateBacktestParams {
  dataset_id: string;
  strategy_id: string;
  profile: string;
}

// --- Era-5B: the tradable level map (capability 1, J-01), surfaced this iteration (J-05) at
// /structure's new default Tradable Map view. Every field below is read VERBATIM from
// GET /research/tradability (app/research/tradability.py's `compute_tradability` — a LENS over
// the frozen `compute_levels` output, never a second levels engine) — the page recomputes no
// price, class, or score.

// One tradable band (GET /research/tradability's `bands[]`). `class` is a PROJECTION of the
// band's best overlapping confluence zone (owned by levels.py) — `null` is an honest "no
// overlapping zone", never a fabricated/defaulted grade. `members` reuses the EXISTING
// `SrLevel`-shaped entry byte-for-byte (the backend's own band member IS a levels.py level dict).
export interface TradabilityBand {
  side: "support" | "resistance";
  price_low: number;
  price_high: number;
  class: "A" | "B" | "C" | null;
  quality_score: number;
  round_number: boolean;
  member_count: number;
  members: SrLevel[];
}

// GET /research/tradability?symbol=&as_of= — the full served projection, read VERBATIM. Two
// fields together carry the SAME three honest, distinct states `LevelsResponse` already
// established: `no_bar_series_for_symbol: true` (no recorded series at all) vs. `false` with an
// empty `bands` + `basis_as_of: null` (series exist, no basis derivable at `as_of`) vs. a
// resolved `basis_as_of` with non-empty `bands` (once a basis resolves, at least one band always
// exists — the module's own docstring: a resolved basis with zero bands is not a reachable state).
export interface TradabilityResponse {
  symbol: string;
  as_of: string;
  bands: TradabilityBand[];
  no_bar_series_for_symbol: boolean;
  basis_as_of: string | null;
}

// --- Era-5B: the touch-event scanner + case-study registry (capability 2, J-02) + the
// tape-at-the-wall join (capability 4, J-03), surfaced this iteration (J-05) at /structure's new
// Case Studies section. Every field is read VERBATIM from GET /research/setups /
// GET /research/setups/{id} (app/research/setups.py's `compute_setups` /
// `enrich_with_tape_timeline`) — the page recomputes no reaction, forward return, or tape state.

// One forward-return reading at a config-owned horizon. `return_fraction` is honestly `null` when
// that horizon reaches past the end of the stored series — never a fabricated number.
export interface SetupForwardReturn {
  horizon_bars: number;
  return_fraction: number | null;
}

// One meaningful tape-state-transition entry in an event's `tape_timeline` (J-03's tape-at-the-
// wall join). `timestamp` is honestly `null` only when the joined dataset carries no
// `epoch_anchor` (the identical `epoch_anchor + logical_ts` reconstruction the chart already
// uses) — state/confidence are the FROZEN engine's own classifier values, reused verbatim.
export interface SetupTapeTimelineEntry {
  timestamp: string | null;
  state: string;
  confidence: number;
}

// The three config-owned, pre-registered reaction labels (`setups.py`'s own `REJECTED` / `BROKE`
// / `CHOPPED` constants, mirrored — never re-derived). Kept as `string` (not a narrowed literal
// union) on the served event below, the SAME `SrLevel.type` tolerance already established on this
// page: an unrecognized future value still renders rather than silently vanishing at a guard.
export type SetupReaction = "rejected" | "broke" | "chopped";

// One band-touch event (GET /research/setups' `events[]`, and GET /research/setups/{id}'s
// `event`). `tape_timeline` is present-but-empty until a recorded dataset's window covers the
// touch (J-03) — an honest absence, never fabricated. `effective_reaction_horizon_bars` /
// `reaction_boundary_truncated` are the iter-5 B1 additive recency-boundary disclosure: a touch
// inside the store's most-recent session may have its `reaction` read from a TRUNCATED
// sub-horizon (the store simply has not accumulated `horizons[0]` bars past it yet) — disclosed
// here, never silently presented as a full-horizon reaction.
export interface SetupEvent {
  id: string;
  symbol: string;
  session_date: string;
  band: TradabilityBand;
  touch_ts: string;
  touch_open: number;
  touch_high: number;
  touch_low: number;
  touch_close: number;
  touch_volume: number;
  reaction: SetupReaction;
  forward_returns: SetupForwardReturn[];
  effective_reaction_horizon_bars: number;
  reaction_boundary_truncated: boolean;
  tape_timeline: SetupTapeTimelineEntry[];
}

// GET /research/setups (optionally filtered by symbol/reaction/band_class — server-side,
// AND-combined) — read VERBATIM. An empty list is an honest "nothing scanned/touched yet", never
// an error.
export interface SetupsListResult {
  events: SetupEvent[];
}

// GET /research/setups/{id} — the SAME event shape as a list row, plus the J-03 tape join applied
// (list rows never carry a non-empty `tape_timeline`; only this detail read does).
export interface SetupDetailResult {
  event: SetupEvent;
}

// --- Era-5B: the 3-way strategy-comparison edge report (capability 6, J-04), surfaced this
// iteration (J-05) at /structure's new Edge Report section. Every field is read VERBATIM from
// GET /research/edge-report (app/research/edge_report.py's `run_strategy_comparison_report`) —
// the page recomputes no R, $, win-rate, or class/side/reaction partition. `measurement` /
// `null_baseline` reuse the EXISTING `BacktestAggregate` shape byte-for-byte (both are built by
// the SAME `_aggregate()` the Comparison section's own backtest results already render).

// One strategy x class x side x reaction x feed cell (never pooled across feeds — the
// never-pool-across-feeds anti-goal). `dataset_ids` are the recorded windows this cell pooled
// trades from (sorted); `insufficient_sample` gates DISPLAY only — the real measurement is always
// shown alongside it (the `BacktestClassTable` precedent: never a separate hidden state).
export interface EdgeReportCell {
  strategy_id: string;
  band_class: "A" | "B" | "C";
  band_side: "support" | "resistance";
  reaction: SetupReaction;
  feed: string;
  dataset_ids: string[];
  measurement: BacktestAggregate;
  null_baseline: BacktestAggregate;
  insufficient_sample: boolean;
}

// One ranked, informational TRAIN cell that clears the positivity gate, paired with its own
// matching hold-out cell's status. `holdout_cell` is honestly `null` when no hold-out data exists
// yet for that exact (strategy, class, side, reaction, feed) key — never a fabricated verdict.
// This list promotes nothing (the champion pointer is untouched by this report — see
// edge_report.py's own module docstring); it is purely informational ranking.
export interface EdgeReportSurvivingCell {
  train_cell: EdgeReportCell;
  holdout_cell: EdgeReportCell | null;
  holdout_positive_edge: boolean;
}

// GET /research/edge-report — the full served projection, read VERBATIM. `register` is the
// backend's ONE simulated-PnL disclosure string (the page renders THIS string, never a frontend
// copy — mirrors `PnlLedger.register` / `BacktestResult.register`). An all-empty
// (`train.cells: []` and `holdout.cells: []`) or all-`insufficient_sample` report is a valid,
// honest outcome — never hidden, never a fabricated survivor. No `champion` key exists on this
// report (it is never about a single champion pointer — unlike the era-3 champion-only CLI
// report this module also computes).
export interface EdgeReportResponse {
  register: string;
  pnl_min_sample_size: number;
  train: { cells: EdgeReportCell[] };
  holdout: { cells: EdgeReportCell[] };
  surviving_train_cells: EdgeReportSurvivingCell[];
  status?: undefined;
}

// era-fast_wall J-04 -- the operator-run compute-job snapshot, owned by
// app/research/edge_report_compute.py's `EdgeReportComputeManager`. Served VERBATIM by
// GET /research/edge-report/compute (poll), started by POST /research/edge-report/compute,
// cancelled by POST /research/edge-report/compute/cancel -- and embedded VERBATIM as the
// not-computed edge-report payload's own `compute` field below (one owner, one read, two
// callers -- never a second derivation).
export interface EdgeReportComputeProgress {
  phase: string;
  backtests_total: number;
  backtests_done: number;
  backtests_from_cache: number;
  current: { dataset_id: string; strategy_id: string } | null;
}

export interface EdgeReportComputeSnapshot {
  id: string;
  state: "running" | "done" | "cancelled" | "failed";
  force: boolean;
  started_utc: string | null;
  finished_utc: string | null;
  error: string | null;
  progress: EdgeReportComputeProgress;
}

// GET /research/edge-report — the honest not-computed payload (era-fast_wall J-01): a cold cache
// key with a non-empty dataset registry. `status` is the sole discriminator against
// `EdgeReportResponse` above (absent -- `undefined` -- on a real report). `detail` is the
// backend's OWN trigger explanation, rendered verbatim, never a frontend-authored string.
// `compute` (era-fast_wall J-04: widened from its former `null`-only literal type) is the
// compute manager's current/last snapshot, or `null` if no compute has ever been triggered --
// read VERBATIM, never re-derived client-side.
export interface EdgeReportNotComputed {
  status: "not_computed";
  detail: string;
  dataset_count: number;
  register: string;
  compute: EdgeReportComputeSnapshot | null;
}

// The discriminated union `fetchEdgeReport()` actually returns -- a real report or the
// not-computed payload. `payload.status === "not_computed"` is the render branch's discriminator
// (see `structure/page.tsx`'s Edge Report section).
export type EdgeReportPayload = EdgeReportResponse | EdgeReportNotComputed;

// --- Era B "The Desk" iter-4 (J-04) -- the /desk briefing page's types. Mirrors the backend's
// registered shapes verbatim (runs/goal-session-desk/state/blueprint.md's Data Contract "New rows
// this era" table) -- every value here is rendered read-only; nothing is recomputed client-side.

// One ranked screen row (`desk_screen.py`'s `compute_screen`), owned by `app/research/desk_screen.py`,
// served verbatim by `GET /research/desk/screen`. `band_class`/`distance_bps`/`band_score`/
// `price_low`/`price_high` all come from ONE `compute_tradability` band per symbol -- never
// recomputed here. `coverage` is keyed by timeframe (e.g. "1h"/"4h"/"1d"/"1w"), each entry read
// verbatim from `desk_coverage.get_desk_coverage` -- rendered honestly per-timeframe (a symbol may
// hold bars for some pinned timeframes and not others; never assumed uniform).
// era-desk-iter-9 (J-08) -- basis disclosure: the daily bar `compute_tradability` actually
// measured this row's distance/class from, and how many calendar days before the screen's own
// `as_of` that bar is dated. Always present (non-null) on a NEWLY computed ranked row -- a row
// only exists in this branch once `compute_tradability` resolved a basis (desk_screen.py's
// row-builder `elif result["basis_as_of"] is None: skipped...` branch is the only other outcome).
// Typed nullable because a screen snapshot recorded BEFORE this iteration has ranked rows that
// OMIT these two keys ENTIRELY (the append-only rail: legacy snapshots are never backfilled) --
// the runtime value there is `undefined`, not `null`, so callers must check
// `row.basis_as_of == null` (loose equality) to catch both, never `=== null` alone.
// era-desk-iter-15 (J-11) -- history disclosure: how many completed daily sessions (and from what
// start date) `basis_as_of` was measured over -- derived in the SAME `desk_screen.py` walk that
// resolves `basis_as_of`/`basis_age_days`, so it carries the identical presence contract: always
// non-null on a NEWLY computed ranked row, entirely ABSENT (not `null`) on a row recorded before
// this iteration -- callers must check `row.history_sessions == null` (loose equality), same as
// the basis fields above.
// era-desk-iter-17 (J-13) -- reference-close disclosure: the exact daily close the row's band
// selection and `distance_bps` were measured against, copied verbatim from the SAME `close` local
// `desk_screen.py` already resolves for the basis/history fields above -- zero new backend read.
// Renders beside the row's own already-typed `price_low`/`price_high` band range so "the price is
// inside the wall" is a fact on screen instead of arithmetic inverted out of `distance_bps`. Same
// presence contract as basis/history: always non-null on a NEWLY computed ranked row, entirely
// ABSENT (not `null`) on a row recorded before this iteration -- callers must check
// `row.reference_close == null` (loose equality).
// era-desk-iter-18 (J-14) -- opposite-band disclosure: the nearest band on the side of price the
// row's own selected band did NOT choose (`opposite_band`, itself nullable when
// `compute_tradability` served no band on that other side at all), plus a per-class count of every
// band `compute_tradability` returned for that symbol (`bands_by_class`) -- both selected/counted
// from the SAME `result["bands"]` list `desk_screen.py` already holds for `reference_close`, zero
// new backend read. Same legacy-row presence contract as basis/history/reference-close: both keys
// are always present (though `opposite_band` may itself legitimately be `null`) on a NEWLY computed
// ranked row, entirely ABSENT (not merely `null`) on a row recorded before this iteration --
// callers must check `row.opposite_band === undefined` / `row.bands_by_class === undefined` (a
// present `opposite_band: null` is an honest "no band on the other side", distinct from "not
// recorded in this snapshot").
export interface DeskScreenRow {
  symbol: string;
  side: "support" | "resistance";
  band_class: "A" | "B" | "C" | null;
  distance_bps: number;
  band_score: number;
  price_low: number;
  price_high: number;
  coverage: Record<string, { has_bars: boolean; latest_window_end_utc: string | null }>;
  tick_evidence: boolean;
  basis_as_of: string | null;
  basis_age_days: number | null;
  history_sessions: number | null;
  history_start: string | null;
  reference_close?: number | null;
  opposite_band?: {
    side: "support" | "resistance";
    band_class: "A" | "B" | "C" | null;
    price_low: number;
    price_high: number;
    band_score: number;
    distance_bps: number;
  } | null;
  bands_by_class?: { A: number; B: number; C: number; unclassified: number };
  // goal-desk-iter-23 (J-15): copied VERBATIM from the SAME `best` band `desk_screen.py` already
  // selected -- that band's own `member_count`/`round_number` (tradability.py:343) plus a plain
  // per-timeframe tally of that SAME band's own `members` list (keys are only the timeframes
  // actually present, never a fabricated zero). A row from a snapshot recorded BEFORE this
  // iteration has all three keys entirely ABSENT (`undefined`), never present as `null` --
  // `band_member_count` is always >= 1 on any row that carries it at all, so `=== undefined` is
  // the honest legacy-absence check, matching `bands_by_class`'s own convention.
  band_member_count?: number;
  band_round_number?: boolean;
  band_member_timeframes?: Record<string, number>;
}

// A member the screen walked but could not rank -- two honest, distinct reasons, never conflated:
// "no_bars" (no bar series recorded at all) vs "no_basis" (a daily series exists but no prior
// session resolves as a basis).
export interface DeskScreenSkip {
  symbol: string;
  skipped: true;
  reason: "no_bars" | "no_basis";
  coverage: Record<string, { has_bars: boolean; latest_window_end_utc: string | null }>;
  tick_evidence: boolean;
}

// One full, persisted screen snapshot -- frozen JSON, append-only, keyed on five pins
// (`screen_date`, `as_of`, `universe_snapshot_id`, `config_fingerprint`, `bar_store_signature`).
// `rows` is already in the snapshot's OWN served rank order (class desc, distance asc, score
// desc, symbol asc). That order is what the page renders by DEFAULT and the only order it chooses
// on its own; an operator can click a column header for another, which is disclosed above the table
// and reversible from it. Each row's `rank` cell always names its position in THIS array.
export interface DeskScreenSnapshot {
  id: string;
  screen_date: string;
  as_of: string;
  universe_snapshot_id: string | null;
  config_fingerprint: string;
  bar_store_signature: string;
  created_utc: string;
  rows: DeskScreenRow[];
  skipped: DeskScreenSkip[];
}

// The lightweight, meta-only projection `GET /research/desk/screen`'s bulk `screens` list serves
// for EVERY historical snapshot -- id/pins/counts only, NEVER the full `rows`/`skipped` arrays (a
// screen snapshot is materially larger than a universe snapshot -- desk_screen.py module
// docstring). The read-only screen-history list on `/desk` renders this verbatim, no click-through
// (J-05 scope, deferred).
export interface DeskScreenMeta {
  id: string;
  screen_date: string;
  as_of: string;
  universe_snapshot_id: string | null;
  config_fingerprint: string;
  bar_store_signature: string;
  created_utc: string;
  counts: { rows: number; skipped: number };
}

// `GET /research/desk/screen` (no `date` param) -- honest-empty-or-populated, HTTP 200 always,
// never 404. `latest === null` iff no screen has EVER been computed -- the page's ONE discriminator
// for the "Desk screen not computed yet." empty state (never conflated with a computed screen that
// simply skipped every member, which renders `rows: []` with a non-empty `latest`).
export interface DeskScreenListResult {
  screens: DeskScreenMeta[];
  latest: DeskScreenSnapshot | null;
  integrity_errors: { file: string; error: string }[];
}

// era-desk-iter-4 (J-04) -- the screen compute manager's job snapshot (`DeskScreenComputeManager`,
// `app/research/desk_screen_compute.py`), served VERBATIM by GET/POST `/research/desk/screen/compute`.
// `reused`/`screen_id` are THIS iteration's additive amendment to the row (audit B2): `screen_id`
// is the resulting persisted snapshot's own id once a terminal state resolves (`null` while
// running or before any trigger); `reused` is `true` iff that snapshot already existed under the
// SAME 5-pin key before this job ran (a pure re-read, zero new file written), `false` when this
// job's own walk is what created it.
export interface DeskScreenComputeProgress {
  members_total: number;
  members_done: number;
  current: string | null;
}

export interface DeskScreenComputeSnapshot {
  id: string;
  state: "running" | "done" | "cancelled" | "failed";
  screen_date: string;
  started_utc: string | null;
  finished_utc: string | null;
  error: string | null;
  reused: boolean;
  screen_id: string | null;
  progress: DeskScreenComputeProgress;
}

// The desk bar top-up compute manager's job snapshot (`DeskTopupComputeManager`, shipped J-02,
// iter-2), served VERBATIM by GET/POST `/research/desk/topup/compute`. THIS iteration (J-04) is
// its first-ever UI consumer (a Top-up button on `/desk`) -- read-only wiring, zero shape change.
// goal-desk-iter-26 (J-17): `requested_window`/`store_frozen_from`/`store_frozen_through`/
// `window_basis` are additive to every per-pair outcome entry of a run recorded from THIS
// iteration onward -- a run recorded BEFORE this iteration's code shipped never carries them
// (`undefined` on that entry, never backfilled or computed at read time; the page renders the
// honest "window basis not recorded in this run" fallback for such a run instead). `"unchanged"`
// is a NEW outcome value: a vendor call ran and returned only bars already frozen (distinct from
// `"reused"`'s zero-vendor-calls store-first hit).
export interface DeskTopupOutcome {
  symbol: string;
  timeframe: string;
  outcome: "reused" | "fetched" | "unchanged" | "failed";
  detail: string | null;
  requested_window?: { start: string; end: string };
  store_frozen_from?: string | null;
  store_frozen_through?: string | null;
  window_basis?: "tail" | "full_lookback";
  // goal-desk-iter-32 (J-19) -- this pair's own newest frozen bar AFTER the attempt (never
  // `bar_index`'s `window_end_utc`); optional/additive, absent on a run recorded before this
  // iteration's code shipped (the `store_frozen_through`-absence legacy contract, mirrored).
  store_frozen_through_after?: string | null;
}

export interface DeskTopupComputeProgress {
  pairs_total: number;
  pairs_done: number;
  outcomes: DeskTopupOutcome[];
}

export interface DeskTopupComputeSnapshot {
  id: string;
  state: "running" | "done" | "cancelled" | "failed";
  started_utc: string | null;
  finished_utc: string | null;
  error: string | null;
  progress: DeskTopupComputeProgress;
}

// era-desk-iter-11 (J-09) -- the durable, append-only top-up run log, served by
// `GET /research/desk/topup/runs`. Distinct from `DeskTopupComputeSnapshot` above: the compute
// snapshot is the CURRENT/last in-flight job's process-scoped progress (lost on restart, replaced
// the instant a newer run starts); this is every COMPLETED run's terminal outcome, persisted to
// disk once and never rewritten. `requested_window`/`pairs_total`/`pairs_attempted` are the run's
// own recorded provenance -- never recomputed client-side. `outcomes` reuses `DeskTopupOutcome`
// verbatim (byte-identical shape to the live compute progress's own per-pair entries).
export interface DeskTopupRunMeta {
  id: string;
  universe_snapshot_id: string | null;
  requested_window: { start: string; end: string };
  config_fingerprint: string;
  started_utc: string;
  finished_utc: string;
  state: "done" | "cancelled" | "failed";
  pairs_total: number;
  pairs_attempted: number;
}

// The full persisted record -- `DeskTopupRunMeta` plus the per-pair `outcomes` array. Only
// `latest` (below) ever carries this full shape; the bulk `runs` list is meta-only (mirrors
// `DeskScreenSnapshot`/`DeskScreenMeta`'s identical split).
export interface DeskTopupRun extends DeskTopupRunMeta {
  outcomes: DeskTopupOutcome[];
}

// `GET /research/desk/topup/runs` -- honest-empty-or-populated, HTTP 200 always, never 404.
// `latest === null` iff no top-up run has EVER reached a terminal state -- the page's ONE
// discriminator for the "No top-up runs recorded yet." empty state. `integrity_errors`
// (goal-desk-iter-16, J-12) mirrors `DeskScreenListResult`/`DeskUniverseResult`'s identical field
// -- surfaced from the store's own `.list()` return, never silently dropped.
export interface DeskTopupRunsListResult {
  runs: DeskTopupRunMeta[];
  latest: DeskTopupRun | null;
  integrity_errors: { file: string; error: string }[];
}

// era-desk-iter-14 (J-10) -- the coverage-index reconciliation: drift classification between the
// frozen bar-series files and the derived `bar_index`, repaired through the existing
// `BarIndex.reindex()` (never a second index-building path). Mirrors `app/research/
// desk_index_reconcile.py`'s served shapes byte-for-byte. Three honest drift buckets: a healthy
// series with no index row (attributed by symbol+timeframe), an index row whose series_id is on
// disk nowhere (orphan, series_id alone), an index row whose series_id points at a corrupted file
// (stale checksum, series_id alone) -- the two `series_id`-only shapes are structurally identical
// but kept as distinct named types (never a shared alias) so a future field added to only one
// bucket cannot silently leak onto the other.
export interface DeskReconcileUnindexedSeries {
  series_id: string;
  symbol: string;
  timeframe: string;
}

export interface DeskReconcileOrphanRow {
  series_id: string;
}

export interface DeskReconcileStaleChecksumRow {
  series_id: string;
}

export interface DeskReconcileDrift {
  unindexed_series: DeskReconcileUnindexedSeries[];
  orphan_index_rows: DeskReconcileOrphanRow[];
  stale_checksum_rows: DeskReconcileStaleChecksumRow[];
}

export interface DeskReconcileStoreError {
  file: string;
  error: string;
}

export interface DeskReconcileRunMeta {
  id: string;
  config_fingerprint: string;
  started_utc: string;
  finished_utc: string;
  state: "done" | "cancelled" | "failed";
  series_on_disk: number;
  rows_indexed_before: number;
  rows_indexed_after: number;
}

// The full persisted record -- `DeskReconcileRunMeta` plus the before/after drift detail and any
// store errors (corrupt files, surfaced verbatim). Only `latest` (below) ever carries this full
// shape; the bulk `runs` list is meta-only (mirrors `DeskTopupRun`/`DeskTopupRunMeta`'s identical
// split).
export interface DeskReconcileRun extends DeskReconcileRunMeta {
  drift_before: DeskReconcileDrift;
  drift_after: DeskReconcileDrift;
  store_errors: DeskReconcileStoreError[];
}

// `GET /research/desk/coverage/reconcile/runs` -- honest-empty-or-populated, HTTP 200 always,
// never 404. `latest === null` iff no reconciliation has EVER reached a terminal state -- the
// page's ONE discriminator for the "No reconciliation run recorded yet." empty state.
// `integrity_errors` (goal-desk-iter-16, J-12) mirrors `DeskScreenListResult`/
// `DeskUniverseResult`'s identical field -- surfaced from the store's own `.list()` return, never
// silently dropped.
export interface DeskReconcileRunsListResult {
  runs: DeskReconcileRunMeta[];
  latest: DeskReconcileRun | null;
  integrity_errors: { file: string; error: string }[];
}

// The reconciliation compute manager's job snapshot, served VERBATIM by GET/POST
// `/research/desk/coverage/reconcile/compute`. Mirrors `DeskTopupComputeSnapshot`'s shape;
// `progress` here carries only a `phase` label -- reconciliation is a single classify-repair-verify
// walk, not a per-pair loop, so there is no pairs_total/pairs_done counter to report.
export interface DeskReconcileComputeProgress {
  phase: "classifying" | "reindexing" | "verifying";
}

export interface DeskReconcileComputeSnapshot {
  id: string;
  state: "running" | "done" | "cancelled" | "failed";
  started_utc: string | null;
  finished_utc: string | null;
  error: string | null;
  progress: DeskReconcileComputeProgress;
}

// goal-desk-iter-29 (J-18) -- the durable, append-only SCREEN run log, served by
// `GET /research/desk/screen/runs`. Distinct from `DeskScreenComputeSnapshot`: the compute
// snapshot is the CURRENT/last in-flight job's process-scoped progress (lost on restart, replaced
// the instant a newer run starts); this is every COMPLETED run's terminal outcome, persisted to
// disk once and never rewritten. Mirrors `DeskTopupRunMeta`/`DeskReconcileRunMeta`'s identical
// meta-only-list/full-latest split: the bulk `runs` list omits `ranked_count`/`skipped_by_reason`/
// `error`/`failed_member` -- only `latest` (below) ever carries them.
export interface DeskScreenRunMeta {
  id: string;
  screen_date: string;
  universe_snapshot_id: string | null;
  config_fingerprint: string;
  bar_store_signature: string | null;
  started_utc: string;
  finished_utc: string;
  state: "done" | "cancelled" | "failed";
  reused: boolean;
  members_total: number;
  members_attempted: number;
  screen_id: string | null;
}

export interface DeskScreenSkippedByReason {
  no_bars: number;
  no_basis: number;
}

// The full persisted record -- `DeskScreenRunMeta` plus the ranked/skipped-by-reason counts and
// (failed runs only) the verbatim error + the member the walk was on when it raised. Only `latest`
// (below) ever carries this full shape; the bulk `runs` list is meta-only.
export interface DeskScreenRun extends DeskScreenRunMeta {
  ranked_count: number;
  skipped_by_reason: DeskScreenSkippedByReason;
  error: string | null;
  failed_member: string | null;
}

// `GET /research/desk/screen/runs` -- honest-empty-or-populated, HTTP 200 always, never 404.
// `latest === null` iff no screen run has EVER reached a terminal state -- the page's ONE
// discriminator for the "No screen runs recorded yet." empty state. `integrity_errors` mirrors
// `DeskTopupRunsListResult`/`DeskReconcileRunsListResult`'s identical field -- surfaced from the
// store's own `.list()` return, never silently dropped.
export interface DeskScreenRunsListResult {
  runs: DeskScreenRunMeta[];
  latest: DeskScreenRun | null;
  integrity_errors: { file: string; error: string }[];
}

// goal-desk-iter-35 (J-20) -- the screen-comparison payload served by
// `GET /research/desk/screen/compare`. `compare`/`base` are each a lightweight snapshot-identity
// projection (pins + counts only -- never the full `rows`/`skipped` arrays, mirroring
// `DeskScreenMeta`'s own convention); `base` is `null` on the ledger's oldest recorded snapshot
// (`base_resolution: "none_earlier"`) or when an explicit `base=` id does not resolve
// (`base_resolution` stays `"explicit"` either way -- a specific base WAS asked for, it just isn't
// there). Every `compare_*`/`base_*` field on a row is copied VERBATIM from that snapshot's own
// recorded row -- never derived client-side.
export interface DeskScreenCompareSnapshotMeta {
  id: string;
  screen_date: string;
  as_of: string;
  created_utc: string;
  bar_store_signature: string;
  universe_snapshot_id: string | null;
  ranked_count: number;
  skipped_count: number;
}

export interface DeskScreenCompareRow {
  symbol: string;
  status: "compared" | "entered" | "left";
  compare_rank: number | null;
  base_rank: number | null;
  rank_change: number | null;
  compare_side: "support" | "resistance" | null;
  base_side: "support" | "resistance" | null;
  compare_band_class: "A" | "B" | "C" | null;
  base_band_class: "A" | "B" | "C" | null;
  compare_distance_bps: number | null;
  base_distance_bps: number | null;
  compare_basis_as_of: string | null;
  base_basis_as_of: string | null;
  skip_reason: "no_bars" | "no_basis" | null;
}

export interface DeskScreenCompareCounts {
  compared: number;
  rank_changed: number;
  side_changed: number;
  entered: number;
  left: number;
}

export interface DeskScreenCompareResult {
  compare: DeskScreenCompareSnapshotMeta | null;
  base: DeskScreenCompareSnapshotMeta | null;
  base_resolution: "explicit" | "default_prior_date" | "none_earlier" | null;
  rows: DeskScreenCompareRow[];
  identical: boolean;
  counts: DeskScreenCompareCounts;
}

// goal-desk-iter-36 (J-21) -- `GET /research/desk/screen/pins?screen_date=`: the five pins a
// screen run for that date would resolve RIGHT NOW, and whether a screen is already recorded
// under them. `recorded` names the already-registered snapshot verbatim (its own `id`/
// `created_utc`/`bar_store_signature`/ranked+skipped counts) or is an honest `null` -- the
// presence/absence of `recorded` IS the match/differ statement (computed at the owner, served;
// the page derives no equality of its own, the J-20 rule). An honest empty payload
// (`universe_snapshot_id`/`bar_store_signature`: `null`, `members_total: 0`, `recorded: null`)
// before any universe snapshot is registered -- HTTP 200, never a 404.
export interface DeskScreenPinsRecorded {
  id: string;
  screen_date: string;
  created_utc: string;
  bar_store_signature: string;
  ranked_count: number;
  skipped_count: number;
}

export interface DeskScreenPinsResult {
  screen_date: string;
  as_of: string;
  universe_snapshot_id: string | null;
  config_fingerprint: string;
  bar_store_signature: string | null;
  members_total: number;
  recorded: DeskScreenPinsRecorded | null;
}

// Forward-test era v2 (touch-anchored) -- GET /research/desk/forward(?screen_id=) + its compute
// trio. Every field is `desk_forward.py`'s own served shape VERBATIM (the authoritative payload);
// nothing here is ever derived client-side -- the desk arithmetic guard covers the numeric paths.
// All return/drawdown values are PERCENT, converted backend-side.
export interface DeskForwardHorizonMeasure {
  return_pct: number | null;
  // The close the return was measured TO (the last bar's close when truncated), and this
  // horizon's OWN pair of max drawdowns — measured over its own window, not the whole session.
  // OPTIONAL: absent from records written before these were measured. Rendered as an absence
  // there, never as a zero (the return_sign_convention precedent).
  exit_price?: number | null;
  mdd_long_pct?: number | null;
  mdd_short_pct?: number | null;
  truncated: boolean;
  effective_minutes: number | null;
  reason: string | null;
}

// ONE anchored measurement -- the SHARED shape for a touch and a baseline anchor (touches carry
// entry_kind "edge"/"open"; anchors carry "close").
export interface DeskForwardTouch {
  at_utc: string;
  entry_price: number;
  entry_kind: "edge" | "open" | "close";
  horizons: Record<string, DeskForwardHorizonMeasure>;
  to_close_pct: number;
  // to_close's own exit — the session's last close. Optional for the same reason as the horizon
  // fields above.
  close_price?: number | null;
  minutes_to_close: number;
  mdd_long_pct: number;
  mdd_short_pct: number;
}

export interface DeskForwardAvgCell {
  n: number;
  mean_pct: number | null;
  median_pct: number | null;
  n_truncated: number;
}

export interface DeskForwardRow {
  symbol: string;
  side: "support" | "resistance";
  band_class: string | null;
  band_price_low: number | null;
  band_price_high: number | null;
  reason: string | null;
  touch_basis: { timeframe: string; session_date: string; bars_in_session: number } | null;
  touch_count: number;
  touches_beyond_cap: number;
  bars_fully_beyond_band: number;
  gap_through_before_first_touch: boolean;
  anchors_in_band: number;
  touches: DeskForwardTouch[];
  baseline_anchors: DeskForwardTouch[];
  averages: Record<string, DeskForwardAvgCell>;
}

export interface DeskForwardSummaryCell {
  touches: DeskForwardAvgCell;
  baseline: DeskForwardAvgCell;
}

export interface DeskForwardParameters {
  horizons_minutes: [string, number][];
  max_touches_per_row: number;
  baseline_seed: number;
  touch_timeframes: string[];
  // The sign convention the record's directional returns (horizons + to_close) were computed
  // under. OPTIONAL because it is absent from records written before the convention existed —
  // those carry raw price moves, and the panel says so rather than relabelling them.
  return_sign_convention?: string;
  // What each horizon leaf in this record carries. Declared in the payload so a shape change
  // re-keys the record instead of being silently reused. Optional for the same legacy reason.
  horizon_measures?: string[];
}

export interface DeskForwardRecord {
  id: string;
  screen_id: string;
  screen_date: string;
  as_of: string;
  config_fingerprint: string;
  forward_input_signature: string;
  payload_version: number;
  parameters: DeskForwardParameters;
  register: string;
  created_utc: string;
  rows: DeskForwardRow[];
  summary: Record<"support" | "resistance", Record<string, DeskForwardSummaryCell>>;
  rows_with_touches: number;
  total_touches: number;
}

export interface DeskForwardReadResult {
  forward: DeskForwardRecord | null;
  versions: number;
}

// `GET /research/desk/forward/pins?screen_id=` -- how much of that snapshot a measurement could
// POSSIBLY reach, disclosed before anything is clicked. `members_with_fine_series` is an UPPER
// BOUND (a recorded 1m/5m series whose WINDOW covers the session, which is not the same as bars in
// it), and every string rendered from it must say so.
export interface DeskForwardPinsResult {
  screen_id: string;
  screen_date: string | null;
  as_of: string | null;
  touch_timeframes: string[];
  members_total: number;
  members_with_fine_series: number;
  versions: number;
  recorded: {
    id: string;
    created_utc: string;
    rows_with_touches: number;
    total_touches: number;
  } | null;
  /**
   * Where the screen date sits relative to the DAILY bars on file — the one thing that separates
   * "this date is a weekend or a market holiday" from "this real session's fine bars fell off the
   * vendor's retention floor" from "this date has not happened yet". Resolved by
   * `desk_sessions.py` over the screen's own ranked members; `"unknown"` whenever the daily bars
   * cannot answer, never a guess.
   */
  session: {
    state:
      | "recorded_session"
      | "not_a_recorded_session"
      | "after_recorded_evidence"
      | "before_recorded_evidence"
      | "unknown";
    evidence: DeskSessionEvidence | null;
  };
}

/** What a session claim rests on: which members' daily bars were read, and the span they cover. */
export interface DeskSessionEvidence {
  anchor_timeframe: string;
  anchor_symbols: string[];
  from: string | null;
  through: string | null;
  sessions_total: number;
}

/** `GET /research/desk/sessions` — which dates in range are recorded trading sessions. */
export interface DeskSessionsResult {
  sessions: string[];
  non_sessions: string[];
  evidence: DeskSessionEvidence;
}

/**
 * `GET /research/desk/backfill/plan` — what a deep 1m/5m backfill WOULD fetch, said before it is
 * started. `clamped_end` is the load-bearing disclosure: every window ends before the region the
 * Yahoo top-up already covers (~30 days back for 1m, ~60 for 5m), because a contested timestamp
 * resolves in favour of the most recently recorded series and an overlap would permanently replace
 * the recent tape's Yahoo prices with SIP ones.
 */
export interface DeskDeepBackfillPlan {
  requested_window: { start: string; end: string };
  timeframes: string[];
  members_total: number;
  chunks_total: number;
  per_timeframe: Record<string, { chunks: number; clamped_end: string }>;
}

/** One chunk's outcome inside a running or finished backfill. */
export interface DeskDeepBackfillOutcome {
  symbol: string;
  timeframe: string;
  start: string;
  end: string;
  outcome: "fetched" | "reused" | "unchanged" | "failed";
  detail: string | null;
  bars_recorded: number;
}

/** The process-scoped snapshot of the single in-flight (or last-terminal) backfill job. */
export interface DeskDeepBackfillComputeSnapshot {
  id: string;
  state: "running" | "done" | "cancelled" | "failed";
  started_utc: string;
  finished_utc: string | null;
  error: string | null;
  requested_window: { start: string; end: string };
  timeframes: string[];
  progress: {
    chunks_total: number;
    chunks_done: number;
    bars_recorded: number;
    outcomes: DeskDeepBackfillOutcome[];
  };
}

// One terminal forward-measurement attempt, from the durable append-only run log. Survives the
// compute manager's process-scoped snapshot, which is what makes "this ran and found nothing"
// (a `done` row whose `rows_absent_no_fine_bars` covers the whole snapshot) distinguishable from
// "this never ran" (no row at all) after a reload.
export interface DeskForwardRun {
  id: string;
  screen_id: string;
  screen_date: string | null;
  config_fingerprint: string;
  forward_input_signature: string | null;
  started_utc: string;
  finished_utc: string;
  state: "done" | "cancelled" | "failed";
  reused: boolean;
  rows_total: number;
  rows_measured: number;
  rows_absent_no_fine_bars: number;
  rows_with_touches: number;
  total_touches: number;
  forward_id: string | null;
  error: string | null;
}

// `GET /research/desk/forward/runs` -- honest-empty-or-populated, HTTP 200 always, never 404.
// Unlike the screen ledger's list this is NOT meta-only: a forward run record carries counts only,
// so `runs` and `latest` are the same shape.
export interface DeskForwardRunsListResult {
  runs: DeskForwardRun[];
  latest: DeskForwardRun | null;
  integrity_errors: { file: string; error: string }[];
}

export interface DeskForwardComputeSnapshot {
  id: string;
  state: "running" | "done" | "cancelled" | "failed";
  screen_id: string;
  started_utc: string | null;
  finished_utc: string | null;
  error: string | null;
  reused: boolean;
  forward_id: string | null;
  progress: { rows_total: number; rows_done: number; current: string | null };
}

// --- The Playbook (Era B2, J-01/J-02/J-03) -- GET /research/desk/playbook(?date=|?id=) + its
// compute trio + its durable run ledger. Every field is `desk_playbook.py`'s/
// `desk_playbook_compute.py`'s/`desk_playbook_log.py`'s own served shape VERBATIM; nothing here is
// ever derived client-side. A signal's own `forward` block reuses `DeskForwardTouch` /
// `DeskForwardHorizonMeasure` VERBATIM (not re-declared as a lookalike): `_measure_signal` measures
// every playbook signal through the SAME `desk_forward._measure_from` the forward rail's own
// touches/anchors are measured through, so the shape is byte-identical by construction. ------------

// goal-playbook-iter-4 (J-04): `open_high_break`/`open_low_break`'s own geometry fields become
// OPTIONAL here -- the JBE/DBI and cup_handle setups this iteration adds serve a DIFFERENT
// geometry shape on the SAME `signal.geometry` object (one owner, `desk_playbook_detect.py`, per
// setup). `slots_to_break` is the one field every setup serves (it is what `_measure_signal`
// anchors on) -- it stays required.
// goal-playbook-iter-5 (J-05): `capitulation` adds its own four fields below the same way --
// `euphoria` never appears here at all (it is a marker, never a served signal -- see
// `DeskPlaybookDisclosures.euphoria_recent` for its only visible trace).
// ONE shape anchor: a bar the detector actually read, in the two renderings it serves, plus an
// absolute price. `ts` is epoch SECONDS -- deliberately the byte-identical key `GET
// /research/candles` serves its own rows under, so a chart joins an anchor to a candle by equality
// and never reconstructs the RTH 5m session grid `slots_to_break` indexes into (that route applies
// no RTH filter, so matching by timestamp is the only safe join). `ts_utc` is the same instant in
// the ISO form `trigger_ts` already uses.
export interface DeskPlaybookAnchorPoint {
  ts: number;
  ts_utc: string;
  price: number;
}

// A formation WINDOW's time-only bounds (an opening range, a base, a handle, a trading range).
// Time-only because a window's own boundary need not be a bar at all: the opening range's bounds
// are the wall-clock ET 09:30 .. 09:30+or_minutes instants.
export interface DeskPlaybookAnchorSpan {
  from_ts: number;
  from_ts_utc: string;
  to_ts: number;
  to_ts_utc: string;
}

// The drawable outline of ONE signal's formation: the recorded bars and prices the detector read
// it from, so a chart shows the detector's own reading rather than a second, re-derived one.
// Which subset of the optional fields is populated is decided by `setup_id`, exactly as the rest
// of `geometry` already varies by family.
//
// `entry` and `invalidation_price` are deliberately NOT here. Their natural right edge is the
// session close, which depends on bars AFTER the trigger -- anchoring them would break the
// truncation-invariance the whole `geometry` object is held to. Both are served flat on the
// signal, and drawing a line at a served price is formatting, not a recomputation.
export interface DeskPlaybookAnchors {
  // The vocabulary these anchors are written in, and an echo of the signal's own setup_id so a
  // consumer can refuse a mismatched pair rather than draw one setup's outline as another's.
  schema: string;
  setup_id: string;
  // Every family: the whole formation's extent (earliest anchor .. trigger bar) and the trigger.
  formation: DeskPlaybookAnchorSpan;
  trigger: DeskPlaybookAnchorPoint;
  // open_high_break / open_low_break (its two prices are `or_low`/`or_high` above)
  opening_range?: DeskPlaybookAnchorSpan;
  // jbe / dbi (the base's two prices are the signal's own `price_low`/`price_high`)
  base?: DeskPlaybookAnchorSpan;
  jump_start?: DeskPlaybookAnchorPoint;
  jump_end?: DeskPlaybookAnchorPoint;
  // capitulation (the leg low is the signal's own `price_low`)
  decline_start?: DeskPlaybookAnchorPoint;
  climax?: DeskPlaybookAnchorPoint;
  // cup_handle
  left_rim?: DeskPlaybookAnchorPoint;
  cup_bottom?: DeskPlaybookAnchorPoint;
  right_rim?: DeskPlaybookAnchorPoint;
  handle?: DeskPlaybookAnchorSpan;
  handle_bottom?: DeskPlaybookAnchorPoint;
  // range_trade (the range's two prices are the signal's own `price_low`/`price_high`)
  range?: DeskPlaybookAnchorSpan;
  low_zone_touches?: DeskPlaybookAnchorPoint[];
  high_zone_touches?: DeskPlaybookAnchorPoint[];
  // double_top / double_bottom -- `structure_pivot` is the valley/peak the neckline sits at
  first_pivot?: DeskPlaybookAnchorPoint;
  second_pivot?: DeskPlaybookAnchorPoint;
  structure_pivot?: DeskPlaybookAnchorPoint;
}

export interface DeskPlaybookGeometry {
  slots_to_break: number;
  // open_high_break / open_low_break only (J-01)
  or_high?: number;
  or_low?: number;
  or_width_mbr?: number;
  or_bars_used?: number;
  opening_range_basis?: "1m" | "5m";
  open_vs_prior_close_pct?: number | null;
  // jbe / dbi only (J-04, spec §3.3-3.4)
  jump_mbr?: number;
  base_range_mbr?: number;
  base_bars?: number;
  base_flatline?: boolean;
  base_lows_ascending?: boolean;
  ladder_step_ratio?: number | null;
  // cup_handle only (J-04, spec §3.6)
  cup_bars?: number;
  cup_depth_mbr?: number;
  handle_retrace_frac?: number;
  handle_duration_frac?: number;
  cup_optimal?: boolean;
  handle_duration_desirable?: boolean;
  cup_middle_third_rvol_median?: number;
  cup_outer_third_rvol_median?: number;
  handle_rvol_median?: number;
  // capitulation only (J-05, spec §3.5)
  decline_mbr?: number;
  decline_bars?: number;
  climax_rvol?: number;
  bars_from_climax_to_trigger?: number;
  // range_trade only (J-06, spec §3.7)
  range_width_mbr?: number;
  low_zone_touches?: number;
  high_zone_touches?: number;
  crossed_midrange?: boolean;
  // goal-playbook-iter-10 (R-3.2(b)): the BOOK midrange rule's second half -- whether the
  // approach swing turned at the range's midpoint, beside the existing `crossed_midrange`. Optional
  // like every other geometry field: absent (never `null`) on every record recorded before this
  // field shipped.
  turned_at_midrange?: boolean;
  absorption_bar_present?: boolean;
  // double_top / double_bottom only (J-06, spec §3.8-3.9)
  tops_gap_mbr?: number;
  tops_separation_bars?: number;
  valley_depth_mbr?: number;
  nominal_risk_mbr?: number;
  second_top_rvol_vs_first?: number | null;
  // The drawable outline's own anchors. Optional like every other geometry field: absent (never
  // `null`) on every record recorded before anchors shipped -- and THAT absence is the per-signal
  // legacy check the chart keys on, the same way `signal.forward === undefined` already works.
  // Never key this off `payload_version`: a version is a whole-record fact, while whether a shape
  // can be drawn is a per-signal, per-family one.
  anchors?: DeskPlaybookAnchors;
}

export interface DeskPlaybookVolume {
  rvol_trigger_bar: number | null;
  approach_rvol_max: number | null;
  spike_into_trigger_verdict: "exhausted_spike" | "constructive" | "neutral";
  spiky_approach: boolean;
}

export interface DeskPlaybookMarket {
  direction: "supportive" | "against" | "neutral" | null;
  market_move_mbr: number | null;
  book_would_skip_market: boolean;
  relative_strength_strong: boolean;
  source: "SPY";
  reason: string | null;
}

export interface DeskPlaybookDisclosures {
  gapped_beyond_chase: boolean;
  session_bar_count: number;
  attempt_count: number;
  bars_to_close: number;
  concurrent_signals: string[];
  euphoria_recent: boolean;
  capitulation_recent: boolean;
}

// `_invalidation_breached`'s own flat shape: one boolean per rail horizon label plus `to_close`,
// and the ONE session-wide `first_breach_minutes` fact every horizon leaf reads (never re-derived
// per horizon). The index signature covers the per-horizon-label keys (`"1m"`/`"5m"`/`"1h"`/`"4h"`),
// which vary with the record's own `parameters.rail_horizons_minutes` rather than a hardcoded set.
export interface DeskPlaybookInvalidationBreached {
  to_close: boolean;
  first_breach_minutes: number | null;
  [horizonLabel: string]: boolean | number | null;
}

export interface DeskPlaybookSignal {
  symbol: string;
  setup_id: string;
  side: "long" | "short";
  trigger_ts: string;
  trigger_price: number;
  entry: number;
  entry_kind: "level" | "gap_open";
  price_low: number;
  price_high: number;
  invalidation_price: number;
  geometry: DeskPlaybookGeometry;
  volume: DeskPlaybookVolume;
  market: DeskPlaybookMarket;
  principles: string[];
  disclosures: DeskPlaybookDisclosures;
  // OPTIONAL: absent on a `payload_version` 1 (J-01-era, pre-measurement) record's signal -- the
  // panel renders the literal "measurement not recorded in this record" string for these, never a
  // blank or a fabricated value.
  forward?: DeskForwardTouch;
  invalidation_breached?: DeskPlaybookInvalidationBreached;
}

export interface DeskPlaybookAbsence {
  symbol: string;
  reason: string;
}

export interface DeskPlaybookDiagnostic {
  symbol: string;
  diagnostic: string;
  at_utc: string;
}

// One (setup_id:side) pool's per-measure-key summary cell -- the playbook's OWN `{signals,
// baseline}` split (its record's own field name is `signals`, never `touches` -- the forward
// rail's vocabulary for a wall's price touches has no playbook analogue).
export interface DeskPlaybookSummaryCell {
  signals: DeskForwardAvgCell;
  baseline: DeskForwardAvgCell;
}

// The parameters blob embedded verbatim in every record AND hashed into `playbook_input_signature`
// -- ~45 pre-registered constants (docs/playbook-detector-spec.md). Only the two fields the UI
// actually reads are named; the rest stay reachable through the index signature rather than being
// individually re-declared for no reader (nothing here is rendered as arithmetic in any case).
export interface DeskPlaybookParameters {
  setups: string[];
  rail_horizons_minutes: [string, number][];
  // The rail's own measure-key shape, echoed verbatim (DESK_FORWARD_MEASURE_KEYS) -- the ONE list
  // every `summary`/`baseline_anchors` pool cell is keyed by; read here rather than re-derived
  // client-side from `rail_horizons_minutes` (the `forwardMeasureKeys` precedent this section
  // deliberately does NOT repeat, since the backend already serves the exact list it used).
  signal_measures: string[];
  // The rail's own per-row touch cap, reused as the per-(setup_id, side) POOLING cap. Read it to
  // say honestly which occurrences fed a pool's means: `record.signals` carries every detected
  // signal, including the ones past this cap, which the summary above them never pooled.
  rail_max_touches_per_row?: number;
  // The bar timeframe every detector's own session series is sliced at -- served so a chart
  // drilling in from a signal asks for the SAME series the detector saw, rather than a second
  // hardcoded copy of "5m" in the frontend that could silently drift from the backend.
  detect_timeframe?: string;
  [key: string]: unknown;
}

export interface DeskPlaybookRecord {
  id: string;
  session_date: string;
  config_fingerprint: string;
  playbook_input_signature: string;
  payload_version: number;
  parameters: DeskPlaybookParameters;
  register: string;
  recorded_at: string;
  signals: DeskPlaybookSignal[];
  absences: DeskPlaybookAbsence[];
  diagnostics: DeskPlaybookDiagnostic[];
  baseline_anchors: Record<string, DeskForwardTouch[]>;
  summary: Record<string, Record<string, DeskPlaybookSummaryCell>>;
  signals_beyond_cap: Record<string, number>;
  // The per-symbol MBR every `*_mbr` ratio on this record is normalized by (plus the market
  // symbol's own, which `market.market_move_mbr` uses). Present so an MBR figure is READABLE --
  // never so a consumer can multiply a ratio back into a price; every price drawn is served
  // absolutely, as its own field or as a shape anchor. `{}` on a record recorded before it shipped.
  symbol_scales: Record<string, DeskPlaybookSymbolScale>;
}

export interface DeskPlaybookSymbolScale {
  mbr: number;
  baseline_sessions: number;
}

// `GET /research/desk/playbook?date=` -- mirrors `DeskForwardReadResult`'s shape. `versions` is
// OMITTED by the `?id=` read (the record it names either exists or it doesn't; "how many versions
// this date has ever accumulated" is a `?date=`-only question) -- never fabricated as 0/1 there.
export interface DeskPlaybookReadResult {
  playbook: DeskPlaybookRecord | null;
  versions?: number;
}

export interface DeskPlaybookComputeSnapshot {
  // The job's own ephemeral, process-scoped id -- `null` before any compute has ever run this
  // process. A completed cancel reverts every OTHER field to the idle shape but keeps this id, so
  // a waiter can tell "my cancel finished" from "the backend restarted" (`_resolve_cancelled`).
  id: string | null;
  status: "idle" | "running" | "cancelling" | "done" | "error";
  session_date: string | null;
  signals_done: number;
  signals_total: number;
  error: string | null;
}

// One terminal playbook-compute attempt, from the durable append-only run log -- survives the
// compute manager's process-scoped snapshot (the `DeskForwardRun` precedent). Never `"cancelled"`:
// a cancelled playbook run is never logged at all (`desk_playbook_log.py`'s own terminal-excludes-
// cancelled contract).
export interface DeskPlaybookRun {
  run_id: string;
  session_date: string;
  config_fingerprint: string;
  playbook_input_signature: string | null;
  started_at: string;
  finished_at: string;
  outcome: "recorded" | "reused" | "refused_non_session" | "failed";
  signals_recorded: number;
  playbook_id: string | null;
  error: string | null;
}

export interface DeskPlaybookRunsListResult {
  runs: DeskPlaybookRun[];
  latest: DeskPlaybookRun | null;
  integrity_errors: { file: string; error: string }[];
}

// --- The playbook back-scan (Era B2, J-07) -- a plan preview + resumable/cancel-safe compute over
// a From/To range, walking every planned date through the ONE existing shared playbook
// detect+measure+record entry point. -------------------------------------------------------------

/** `GET /research/desk/playbook/backscan/plan` -- what a back-scan over `[from, to]` would find,
 * said before anything is clicked. Every calendar day in range, classified against the playbook
 * store's own already-recorded files at the CURRENT `playbook_input_signature` -- pure and
 * metadata-only, writes/triggers nothing. */
export interface DeskPlaybookBackscanPlanDate {
  session_date: string;
  status: "recorded_at_current_signature" | "missing_at_current_signature";
}

export interface DeskPlaybookBackscanPlan {
  from: string;
  to: string;
  playbook_input_signature: string;
  dates: DeskPlaybookBackscanPlanDate[];
  total: number;
  missing: number;
}

export interface DeskPlaybookBackscanOutcomeCounts {
  reused: number;
  recorded: number;
  refused_non_session: number;
  failed: number;
}

/** The process-scoped snapshot of the single in-flight (or last-terminal) back-scan job. */
export interface DeskPlaybookBackscanComputeSnapshot {
  /** The job's own ephemeral, process-scoped id -- `null` before any back-scan has ever run. */
  id: string | null;
  status: "idle" | "running" | "done" | "cancelled" | "error";
  from: string | null;
  to: string | null;
  planned_total: number;
  completed: number;
  outcomes: DeskPlaybookBackscanOutcomeCounts;
  current_date: string | null;
  error: string | null;
}

// One terminal back-scan attempt, from the durable append-only run log -- survives the compute
// manager's process-scoped snapshot. A cancel that measured nothing is never logged at all (the
// module's own terminal-state-only rule; a partial cancel that recorded at least one date IS
// logged, unlike the single-date playbook run log's own cancel-is-never-logged contract).
export interface DeskPlaybookBackscanRun {
  run_id: string;
  from: string;
  to: string;
  started_at: string;
  finished_at: string;
  status: "done" | "cancelled" | "error";
  outcomes: DeskPlaybookBackscanOutcomeCounts;
}

export interface DeskPlaybookBackscanRunsListResult {
  runs: DeskPlaybookBackscanRun[];
  latest: DeskPlaybookBackscanRun | null;
  integrity_errors: { file: string; error: string }[];
}

// The Playbook Evidence view (Era B2, J-08) -- GET /research/desk/playbook/evidence's own served
// shapes. `DeskPlaybookEvidenceCellStats` deliberately does NOT reuse `DeskForwardAvgCell`: the
// evidence fold serves p25_pct/p75_pct the rail's own avg cell never had (desk_playbook_evidence.py
// pools them with its own new quartile math -- see that module's docstring for why this is NOT a
// second implementation of the rail).
// goal-playbook-iter-12 (J-11): both stats shapes gain n_unmeasured/n_sessions (baseline also
// gains n_truncated -- already computed server-side, previously discarded) -- every new count a
// straight pass-through of GET /research/desk/playbook/evidence's enriched body, no client math.
// `n_positive` counts this cell's OWN pooled values strictly greater than zero -- the same
// untruncated list its median and mean come from. `null` on every `mdd_*` measure, which is clamped
// <= 0 by construction so "greater than zero" is not a fact it can carry. A recorded count, never a
// probability: the served register says so, and this UI only renders what is served.
export interface DeskPlaybookEvidenceCellStats {
  n: number;
  n_positive: number | null;
  // `n_positive / n`, served so no surface divides two served numbers of its own.
  positive_share: number | null;
  n_truncated: number;
  n_unmeasured: number;
  n_sessions: number;
  median_pct: number | null;
  p25_pct: number | null;
  p75_pct: number | null;
  mean_pct: number | null;
}

export interface DeskPlaybookEvidenceBaselineStats {
  n_baseline: number;
  n_positive: number | null;
  positive_share: number | null;
  n_truncated: number;
  n_unmeasured: number;
  n_sessions: number;
  median_pct: number | null;
  p25_pct: number | null;
  p75_pct: number | null;
  mean_pct: number | null;
}

export interface DeskPlaybookEvidenceCell {
  setup_id: string;
  side: "long" | "short";
  measure: string;
  signal: DeskPlaybookEvidenceCellStats;
  baseline: DeskPlaybookEvidenceBaselineStats;
  below_min_n: boolean;
}

export interface DeskPlaybookEvidenceBreach {
  setup_id: string;
  side: "long" | "short";
  horizon: string;
  breached_count: number;
  total_count: number;
}

export interface DeskPlaybookEvidenceOtherSignature {
  signature: string;
  dates: string[];
  n_records: number;
  created_span: { from: string; to: string };
}

// goal-playbook-iter-12 (J-11): the pooled/default signature's OWN basis disclosure -- built by the
// same per-signature summarizer `other_signatures[]` above already uses. `created_span` is `null`
// iff `n_records` is `0` (an entirely empty store) -- the ONE case `other_signatures[]` entries
// never hit (a signature only appears there once it has recorded >= 1 file).
export interface DeskPlaybookEvidenceBasis {
  dates: string[];
  n_records: number;
  created_span: { from: string; to: string } | null;
}

// --- The read-side band-context lens (docs/playbook-detector-spec.md §6) -------------------------
// Where a recorded signal sits relative to the desk's own tradable band map at that session's
// basis. EVERY field here is served; this UI computes no distance, no bucket, and no caption.

export type DeskPlaybookBandStatus = "located" | "no_band_context" | "not_computed";
export type DeskPlaybookBackingBucket = "at_wall" | "off_wall" | "no_wall_behind";
export type DeskPlaybookRoomBucket =
  | "room_lt_1r"
  | "room_1r_2r"
  | "room_ge_2r"
  | "no_wall_ahead"
  // Headroom measured but no invalidation distance to divide by -- an honest state, counted in the
  // split's basis, never one of its cells.
  | "room_unmeasured";

export interface DeskPlaybookBandSummary {
  side: "support" | "resistance";
  class: "A" | "B" | "C" | null;
  price_low: number;
  price_high: number;
  quality_score: number;
  round_number: boolean;
  member_count: number;
}

// A wall is a band plus THIS event's distance to its facing edge -- served together so no surface
// has to pair them or invert a sign.
export interface DeskPlaybookWall extends DeskPlaybookBandSummary {
  distance_bps: number;
}

// The bracket frame (docs/playbook-detector-spec.md §6 v2): what is under the entry, what is over
// it, and how much room that leaves against the trade's own invalidation distance. Every reading is
// served; nothing here is computed in the browser.
export interface DeskPlaybookBandContext {
  status: DeskPlaybookBandStatus;
  containing_band: DeskPlaybookBandSummary | null;
  wall_below: DeskPlaybookWall | null;
  wall_above: DeskPlaybookWall | null;
  // Side-relative: "behind" is below a long and above a short. `0.0` when the entry sits inside a
  // band; `null` when nothing is behind it at all.
  backing_bps: number | null;
  headroom_bps: number | null;
  risk_bps: number | null;
  risk_source: "own" | "paired_signal" | null;
  room_r: number | null;
  backing_bucket: DeskPlaybookBackingBucket | null;
  room_bucket: DeskPlaybookRoomBucket | null;
  basis_as_of: string | null;
  caption: string;
}

export interface DeskPlaybookContextSignal {
  symbol: string | null;
  setup_id: string | null;
  side: string | null;
  pool_key: string;
  trigger_ts: string | null;
  entry: number | null;
  measured: boolean;
  band_context: DeskPlaybookBandContext;
}

export interface DeskPlaybookContextAnchor {
  index: number;
  at_utc: string | null;
  entry_price: number | null;
  symbol: string | null;
  attribution: "positional_verified" | "unattributable";
  band_context: DeskPlaybookBandContext;
}

export interface DeskPlaybookContextParameters {
  algorithm: string;
  near_band_bps: number;
  room_r_edges: number[];
  distance_from: string;
  statuses: string[];
  backing_buckets: string[];
  room_buckets: string[];
}

export interface DeskPlaybookContext {
  playbook_id: string;
  session_date: string;
  playbook_input_signature: string;
  parameters: DeskPlaybookContextParameters;
  signals: DeskPlaybookContextSignal[];
  baseline_anchors: Record<string, DeskPlaybookContextAnchor[]>;
  basis: Record<string, number>;
  register: string;
}

// --- Cohorts of the band context (docs/playbook-detector-spec.md §7) ------------------------------
// The record's OWN recorded pooled means, re-pooled per declared location cohort by the backend, so
// the desk's per-setup summary can follow its display filters without the browser re-pooling a
// served aggregate. `cohorts["all:all"].summary` is byte-identical to `record.summary`.

export type DeskPlaybookBackingValue = "all" | "at_wall" | "at_wall_room_ge_1r";
export type DeskPlaybookInsideValue = "all" | "inside" | "not_inside";

// Why a signal joins no NARROWED cohort. Counted, never dropped: "nothing was at a wall" and "no
// map has been computed yet" both produce an n: 0 cell, and only these separate them.
export interface DeskPlaybookCohortPoolBasis {
  n_eligible: number;
  n_signals: number;
  n_anchors: number;
  n_anchors_unattributable: number;
  n_excluded_not_computed: number;
  n_excluded_no_band_context: number;
  n_excluded_room_unmeasured: number;
  n_excluded_other_location: number;
  n_excluded_no_context: number;
  context_aligned: boolean;
}

export interface DeskPlaybookCohort {
  backing: DeskPlaybookBackingValue;
  inside: DeskPlaybookInsideValue;
  // EXACTLY `record.summary`'s shape, so the summary cells render unchanged.
  summary: Record<string, Record<string, DeskPlaybookSummaryCell>>;
  pools: Record<string, DeskPlaybookCohortPoolBasis>;
  basis: Record<string, number>;
}

export interface DeskPlaybookCohortSignal {
  symbol: string;
  setup_id: string;
  side: string;
  pool_key: string;
  trigger_ts: string;
  measured: boolean;
  // Whether this signal fed the pooled means. The "beyond cap" chip must read THIS rather than a
  // row's position, which a display filter re-origins.
  in_cap: boolean;
  cohorts: string[];
}

export interface DeskPlaybookCohortSummaries {
  playbook_id: string;
  session_date: string;
  parameters: {
    algorithm: string;
    context_algorithm: string;
    backing_values: DeskPlaybookBackingValue[];
    inside_values: DeskPlaybookInsideValue[];
    cohort_keys: string[];
    unfiltered_cohort: string;
    pooling: string;
    baseline_pairing: string;
    room_ge_1r_buckets: string[];
    pool_keys: string[];
    measures: string[];
  };
  cohorts: Record<string, DeskPlaybookCohort>;
  signals: DeskPlaybookCohortSignal[];
  basis: Record<string, number | string>;
  register: string;
}

// One split cell -- the SAME stat blocks as an unsplit cell, plus the bucket that names which
// comparison half it belongs to.
export interface DeskPlaybookEvidenceBandContextCell extends DeskPlaybookEvidenceCell {
  backing_bucket: DeskPlaybookBackingBucket;
  room_bucket: Exclude<DeskPlaybookRoomBucket, "room_unmeasured">;
}

export interface DeskPlaybookEvidenceBandContext {
  parameters: DeskPlaybookContextParameters;
  cells: DeskPlaybookEvidenceBandContextCell[];
  basis: Record<string, number>;
  register: string;
}

export interface DeskPlaybookEvidence {
  signature: string;
  cells: DeskPlaybookEvidenceCell[];
  invalidation_breached: DeskPlaybookEvidenceBreach[];
  other_signatures: DeskPlaybookEvidenceOtherSignature[];
  basis: DeskPlaybookEvidenceBasis;
  parameters: DeskPlaybookParameters;
  band_context: DeskPlaybookEvidenceBandContext;
  register: string;
}

// ONE registered universe membership snapshot's own served meta -- `UniverseStore.record`'s return
// value verbatim (desk_universe.py's `meta` dict), which `POST /research/desk/universe/fetch`
// serves under its `universe` key. Every field is the store's own; nothing here is derived. The
// refresh chain reads only `id` and `member_count`, but the shape is declared in full so a future
// reader of this payload is not tempted to re-declare a narrower one.
export interface DeskUniverseSnapshotMeta {
  id: string;
  date: string;
  checksum: string;
  member_count: number;
  source_url: string;
  min_members: number;
  max_members: number;
  created_utc: string;
  members: string[];
  raw_members: Record<string, string>;
}

// --- Era 6 "The Referee" (goal-referee-iter-8, J-07) -- the FIRST Referee UI slice. Nothing
// referee-related existed in this file before this iteration. Every field below is served
// VERBATIM by its owning backend fold (referee_registry.py) -- no client-side arithmetic on any
// of them (test_desk_ui_guards.py's extended _PRICE_ARITHMETIC_FIELDS covers the ones this
// iteration's JSX actually reads).

export type RefereeEstimand = "A" | "B" | "C";
export type RefereeSidedness = "greater" | "less" | "two-sided";
export type RefereeEvidenceFamily = "playbook" | "strategy";
export type RefereeSide = "long" | "short";

export interface RefereeContextPredicate {
  backing_bucket: string;
}

// GET /research/desk/referee/registry/shortlist -- spec Sec7's five pre-registered candidates
// (S-1..S-5, pinned module constants on the backend) beside LIVE sample-size readiness.
export interface RefereeShortlistCandidate {
  candidate_id: string;
  estimand: RefereeEstimand;
  evidence_family: RefereeEvidenceFamily;
  setup_id: string;
  side: RefereeSide;
  context_predicate: RefereeContextPredicate | null;
  primary_measure_key: string;
  primary_horizon: string;
  sidedness: RefereeSidedness;
  null_spec_id: string | null;
  test_spec_id: string;
  rationale: string;
  n: number;
  n_sessions: number;
  target_sessions: number;
  min_occurrences: number;
  accrual_rate_sessions_per_day: number;
  // `null` only when `accrual_rate_sessions_per_day` is 0 -- never a divide-by-zero value.
  projected_days_to_target: number | null;
  // goal-referee-iter-12 (J-11): BESIDE (never replacing) the calendar-day pair above -- the SAME
  // rate/projection shape measured against the corpus's own recorded-session basis
  // (`accrual_basis.pooled_sessions_at_current_basis`) instead of a raw calendar-day span. `0.0`
  // when the denominator (the corpus-wide pooled-session count) is 0 -- never a divide-by-zero
  // value; `projected_pooled_sessions_to_target` is `null` in that same case.
  informative_sessions_per_pooled_session: number;
  projected_pooled_sessions_to_target: number | null;
}

// goal-referee-iter-12 (J-11): the corpus's own recorded-session accounting -- a read-side
// planning disclosure (docs/referee-statistical-spec.md Sec9 addendum) no statistical procedure
// consumes. `corpus_span_days` is byte-identical to the value the shipped
// `accrual_rate_sessions_per_day` already divides by; the four session-date/count fields read ""
// / `0` on an empty corpus, never a crash.
export interface RefereeAccrualBasis {
  corpus_first_session_date: string;
  corpus_last_session_date: string;
  corpus_span_days: number;
  recorded_sessions_in_span: number;
  pooled_sessions_at_current_basis: number;
  longest_zero_session_stretch_days: number;
  longest_zero_session_stretch_start: string;
  longest_zero_session_stretch_end: string;
}

// goal-referee-iter-9 rider: `family_id`/`family_q` are the starter family's own
// registration-mechanics fields, moved backend-side (previously only an unowned
// apps/frontend/app/desk/page.tsx literal) -- served here for the first time.
export interface RefereeShortlistResponse {
  candidates: RefereeShortlistCandidate[];
  family_id: string;
  family_q: number;
  // goal-referee-iter-12 (J-11): the accrual-basis disclosure, computed once inside
  // shortlist_response()'s existing single store scan (referee_registry.py) -- no second owner.
  accrual_basis: RefereeAccrualBasis;
}

// The read-side fold additions GET /research/desk/referee/registry adds to every hypothesis
// entry -- never persisted on the record itself.
export interface RefereeAccrual {
  informative_post_boundary_sessions: number;
  target_sessions: number;
  is_proxy: boolean;
  basis_current: boolean;
}

// The `discovery (exploratory)` block (goal-referee-iter-8, J-07 Step 4) -- pre-boundary
// historical observations in the hypothesis's own cell, visibly distinct from `accrual`. NEVER a
// confirmatory count (the historical atlas is exploratory forever).
export interface RefereeDiscovery {
  n: number;
  n_sessions: number;
  label: string;
}

export interface RefereeHypothesis {
  hypothesis_id: string;
  family_id: string;
  registered_at: string;
  evidence_family: RefereeEvidenceFamily;
  estimand: RefereeEstimand;
  setup_id: string;
  side: RefereeSide;
  context_predicate: RefereeContextPredicate | null;
  primary_measure_key: string;
  primary_horizon: string;
  sidedness: RefereeSidedness;
  null_spec_id: string | null;
  test_spec_id: string;
  detector_basis: string | null;
  context_algorithm_version: string | null;
  confirmation_start_boundary: string;
  target_sessions: number;
  min_occurrences: number;
  origin: string;
  status: "active" | "withdrawn";
  accrual: RefereeAccrual;
  discovery: RefereeDiscovery;
}

export interface RefereeFamily {
  family_id: string;
  q: number;
  candidate_hypothesis_ids: string[];
  registered_at: string;
}

export interface RefereeWithdrawal {
  hypothesis_id: string;
  withdrawn_at: string;
  reason: string | null;
}

export interface RefereeIntegrityError {
  store: string;
  file: string;
  error: string;
}

// GET /research/desk/referee/registry -- the pinned five-key registry fold, served verbatim.
export interface RefereeRegistryResponse {
  families: RefereeFamily[];
  hypotheses: RefereeHypothesis[];
  withdrawals: RefereeWithdrawal[];
  certificates: unknown[];
  integrity_errors: RefereeIntegrityError[];
}

// POST /research/desk/referee/registry/hypotheses -- the real registration act's own request
// body. `confirm: true` is the explicit-confirmation-required gate every write on this page
// carries; the rest are the candidate's OWN fields, read verbatim off a shortlist entry (never
// hand-typed) plus the caller's own family framing.
export interface RefereeHypothesisRegistrationPayload {
  confirm: true;
  hypothesis_id: string;
  family_id: string;
  family_q: number;
  family_candidate_hypothesis_ids: string[];
  evidence_family: RefereeEvidenceFamily;
  estimand: RefereeEstimand;
  setup_id: string;
  side: RefereeSide;
  context_predicate: RefereeContextPredicate | null;
  primary_measure_key: string;
  primary_horizon: string;
  sidedness: RefereeSidedness;
  null_spec_id: string | null;
  test_spec_id: string;
  target_sessions: number;
  min_occurrences: number;
}

// --- Era 6 "The Referee" (goal-referee-iter-10, J-09) -- Referee Adjudications + Referee Runs, the
// era's LAST two `/desk` sections. Every field below is served VERBATIM by its owning backend fold
// (referee_adjudicate.py's `adjudications_response()`, `RefereeNullComputeManager`/
// `RefereeEvaluationComputeManager`, `RefereeNullRunStore`/`RefereeEvaluationRunStore`) -- no
// client-side arithmetic or verdict derivation anywhere downstream
// (test_desk_ui_guards.py's extended `_PRICE_ARITHMETIC_FIELDS` covers the numerics this
// iteration's JSX actually reads).

export interface RefereeBhFold {
  q: number;
  m: number;
  k_star: number;
  bh_pass: boolean;
  by_adjusted_p: number;
  by_pass: boolean;
}

// `expected`/`actual`/`tolerance` share one shape (referee_stats.py's `_ATTESTATION_EXPECTED`/
// `_ATTESTATION_TOLERANCE`).
export interface RefereeAttestationQuantities {
  permutation_p: number;
  permutation_enumeration: boolean;
  ci_low: number;
  ci_high: number;
}

export interface RefereeAttestation {
  expected: RefereeAttestationQuantities;
  actual: RefereeAttestationQuantities;
  tolerance: RefereeAttestationQuantities;
  stats_core_version: string;
  passed: boolean;
}

// A hypothesis's ONE permanent, append-only confirmatory checkpoint -- present on an adjudication
// entry only once that hypothesis has reached its checkpoint evaluation.
export interface RefereeAdjudicationSnapshot {
  snapshot_id: string;
  hypothesis_id: string;
  family_id: string;
  checkpoint_evaluation_id: string;
  snapshot_at: string;
  bh: RefereeBhFold;
  fragility_triggers: string[];
  verdict: "no_evidence" | "fragile" | "corroborated";
  evaluation_basis: string;
  attestation: RefereeAttestation;
}

export type RefereeVerdict =
  | "registered"
  | "pending_forward_confirmation"
  | "insufficient_sample"
  | "fragile"
  | "no_evidence"
  | "corroborated"
  | "basis_retired";

// The live (pre-checkpoint) accrual fold -- present only when `snapshot` is `null`.
export interface RefereeLiveCoverage {
  post_boundary_sessions: number;
  target_sessions: number;
}

export interface RefereeAdjudicationEntry {
  hypothesis_id: string;
  verdict: RefereeVerdict;
  confirmatory_output_refused: boolean;
  refusal_reason: string | null;
  snapshot: RefereeAdjudicationSnapshot | null;
  live_coverage: RefereeLiveCoverage | null;
}

// GET /research/desk/referee/adjudications -- the read-side adjudication fold, served verbatim,
// beside the served REFEREE_REGISTER disclosure text (what a verdict does NOT mean).
export interface RefereeAdjudicationsResponse {
  entries: RefereeAdjudicationEntry[];
  register: string;
  integrity_errors: RefereeIntegrityError[];
}

// The process-scoped snapshot of ONE in-flight (or last-terminal) null-build / evaluation job --
// mirrors `DeskPlaybookBackscanComputeSnapshot`'s `status`/`"idle"` shape. Keyed PER null_spec_id /
// hypothesis_id in this page's own state (never a single page-wide singleton): both compute
// managers are single-flight PER KEY, not process-global, unlike every other desk compute control.
export interface RefereeNullComputeSnapshot {
  id: string | null;
  status: "idle" | "running" | "cancelling" | "done" | "error";
  null_spec_id: string | null;
  done: number;
  total: number;
  error: string | null;
}

export interface RefereeEvaluationComputeSnapshot {
  id: string | null;
  status: "idle" | "running" | "cancelling" | "done" | "error";
  hypothesis_id: string | null;
  done: number;
  total: number;
  error: string | null;
}

// One terminal null-build attempt from the durable, append-only, terminal-state-only run log.
export interface RefereeNullRun {
  run_id: string;
  null_spec_id: string;
  state: "completed" | "failed" | "cancelled";
  started_at: string;
  finished_at: string;
  progress: { done: number; total: number };
  error: string | null;
}

// GET /research/desk/referee/nulls/runs -- honest-empty-or-populated, HTTP 200 always, never 404.
export interface RefereeNullRunsListResult {
  runs: RefereeNullRun[];
  latest: RefereeNullRun | null;
  integrity_errors: RefereeIntegrityError[];
}

// One terminal evaluation attempt from the durable, append-only, terminal-state-only run log.
export interface RefereeEvaluationRun {
  run_id: string;
  hypothesis_id: string;
  state: "completed" | "failed" | "cancelled";
  started_at: string;
  finished_at: string;
  progress: { done: number; total: number };
  error: string | null;
}

// GET /research/desk/referee/evaluate/runs -- honest-empty-or-populated, HTTP 200 always, never 404.
export interface RefereeEvaluateRunsListResult {
  runs: RefereeEvaluationRun[];
  latest: RefereeEvaluationRun | null;
  integrity_errors: RefereeIntegrityError[];
}

// --- Era 6 "The Referee" (goal-referee-iter-13, J-12) -- GET /research/desk/referee/evidence's
// FIRST direct UI reader. `app/research/referee_evidence.py::referee_evidence()` has served this
// shape since J-01 (iteration 1); this iteration adds ZERO backend field/value -- every interface
// below matches the served body field-for-field (docs/goal.md J-12 Step 1). Each block's own
// `integrity_errors` is the plain `{file, error}[]` shape every OTHER single-store desk section
// already uses (DeskTopupRunsListResult et al., types.ts:1020/1087/1152/... — 9+ precedents) --
// distinct from `RefereeIntegrityError[]` above (registry/adjudications), which labels errors
// across FOUR stores and so carries an extra `store` field neither `playbook_occurrence` nor
// `strategy_trade` needs (each reads exactly ONE store's own `.list()`, confirmed by reading
// referee_evidence.py's `playbook_occurrence_readiness()`/`strategy_trade_readiness()` live).

export interface RefereeEvidencePerSetupSideCell {
  setup: string;
  side: string;
  n: number;
  n_sessions: number;
}

export interface RefereeEvidenceStaleBasisDate {
  session_date: string;
  record_detector_basis: string;
}

export interface RefereePlaybookOccurrenceReadiness {
  detector_basis: string;
  config_fingerprint: string;
  records: number;
  distinct_sessions: number;
  signals_at_current_basis: number;
  per_setup_side: RefereeEvidencePerSetupSideCell[];
  stale_basis_dates: RefereeEvidenceStaleBasisDate[];
  integrity_errors: { file: string; error: string }[];
}

export interface RefereeStrategyTradeReadiness {
  dataset_count: number;
  per_split_counts: { train: number; holdout: number };
  trade_count: number;
  tick_gate_met: boolean;
  tick_gate_statement: string;
  basis_caveats: string[];
  integrity_errors: { file: string; error: string }[];
}

// GET /research/desk/referee/evidence -- the readiness fold, served verbatim.
export interface RefereeEvidenceResponse {
  playbook_occurrence: RefereePlaybookOccurrenceReadiness;
  strategy_trade: RefereeStrategyTradeReadiness;
}

// GET /research/desk/micro/readiness -- goal-rapid-microscope-iter-1 (J-01): the era's first
// served value, the corpus-truth surface every later Rapid-Microscope journey depends on. Served
// verbatim -- see MicroReadinessSection in app/desk/page.tsx.
export interface MicroReadinessTotals {
  distinct_symbol_days: number;
  distinct_datasets: number;
  rth_minutes_covered: number;
  session_equivalents: number;
  // r14: spec §0 -- a session IS an ET RTH trading date, and every fold floor counts DATES.
  // `full_session_equivalents` is RTH COVERAGE (minutes / 390) and is a different quantity.
  // Neither is ever substituted for the other.
  distinct_session_dates: number;
  full_session_equivalents: number;
  session_count_basis: string;
  referee_tick_gate_symbol_days: number;
}

export interface MicroReadinessShard {
  dataset_id: string;
  symbol: string;
  session_date: string;
  data_feed: string;
  window_start_utc: string;
  window_end_utc: string;
  trade_count: number;
  quote_count: number;
  bytes: number;
  coverage_gaps: string[];
  fallback_frac: number;
  checksum: string;
  split_provenance: string;
  exposure_state: string;
}

export interface MicroReadinessStudyFloor {
  study_id: string;
  floor_name: string;
  required_sessions: number;
  available_sessions: number;
  // r14: `required_sessions` (40 + 20) omits the fold spec's embargo and therefore never meant
  // "a fold can run". The basis token says so, and the two executable floors sit beside it.
  required_sessions_basis: string;
  required_sessions_note: string;
  available_session_dates: number;
  first_fold_min_session_dates: number;
  // r14.2: the accurate name. `survivor_min_session_dates` is the SAME number under r14's own
  // misnomer -- a session COUNT can say folds are CONSTRUCTIBLE, never that a survivor is
  // reachable, which depends on the observation floors inside each test window.
  constructible_folds_min_session_dates: number;
  survivor_min_session_dates: number;
  first_fold_status: string;
  constructible_folds_status: string;
  survivor_status: string;
  folds_constructible: number;
  min_sufficient_folds: number;
  sufficiency_note: string;
  status: string;
}

// goal-rapid-microscope-iter-15 (J-08 half 2): `joinable_corpus` and `sealed_tranche` -- both
// ALREADY served by `micro_readiness.py`'s unchanged `build_readiness` (transcribed verbatim from
// its own return statement) -- were fetched but silently dropped by this interface until now. Only
// `joinable_corpus.withheld_excluded` and every `sealed_tranche` field are rendered this iteration
// (aggregate-only, spec section 7.5); `total`/`playbook_signal_count`/`band_touch_count`/
// `by_setup_id`/`playbook_integrity_errors` stay typed/fetched but UNRENDERED.
// goal-rapid-microscope-iter-21 (J-09): `band_touch_count` is now rendered too (the "future J-09
// home" this comment used to name) -- the real materialized int, or the honest typed
// `not_enumerated` state, never a bare number a reader could mistake for a real zero.
export interface MicroReadinessJoinableCorpus {
  total: number;
  playbook_signal_count: number;
  band_touch_count: { status: string; count: number | null };
  by_setup_id: Record<string, number>;
  playbook_integrity_errors: { file: string; error: string }[];
  withheld_excluded: number;
}

export interface MicroReadinessSealedTranche {
  shard_count: number;
  symbol_days: number;
  by_universe: Record<string, { shard_count: number; symbol_days: number }>;
}

export interface MicroReadinessResponse {
  totals: MicroReadinessTotals;
  shards: MicroReadinessShard[];
  study_floors: MicroReadinessStudyFloor[];
  integrity_errors: { file: string; error: string }[];
  joinable_corpus: MicroReadinessJoinableCorpus;
  sealed_tranche: MicroReadinessSealedTranche;
}

// goal-rapid-microscope-iter-14 (J-08 half 1): Scout Ledger, Walk-Forward, and Validation Vault --
// three already-shipped backend endpoints rendered on /desk for the first time. Every shape below
// is transcribed directly from `apps/backend/app/research/{micro_routes,scout,scout_ledger,
// walkforward,walkforward_ledger,vault}.py`, read this planning pass -- never re-derived from
// goal.md prose alone. A candidate/fold's own inner payload (`screen_result`, `econ_floor`,
// `feature`, `outcome`, `structure_context`, a fold's `missing`) varies by candidate/fold type and
// is typed as `Record<string, unknown>` rather than enumerated -- the page renders it as an opaque,
// verbatim JSON detail (never guesses a fixed shape, so a field already served is never silently
// dropped by a mis-typed interface).

export interface MicroChainVerification {
  ok: boolean;
  failed_at_row: number | null;
  reason: string | null;
}

// --- Scout Ledger -- GET /research/desk/micro/scout (scout.py `list_scout_families`,
// `register_and_screen_candidate`/`build_candidate_spec_fields`'s own row shape) -----------------

export interface ScoutTrialRow {
  family_id: string;
  family_root_id: string;
  candidate_id: string;
  spec_hash: string;
  feature: { name: string; transform: string; params: Record<string, unknown> };
  // J-09: `setup_id` is additive and OPTIONAL -- present only on a "playbook_signal"-kind
  // candidate whose frozen spec names one verbatim (e.g. Study 3's "capitulation"); absent
  // everywhere else, byte-identical to the pre-J-09 `{ kind: string }` shape.
  structure_context: { kind: string; setup_id?: string };
  outcome: { horizon_key: string; sidedness: string | null };
  fitting_rule: string | null;
  econ_floor: Record<string, unknown>;
  corpus_manifest: unknown[];
  grid_version: number;
  registered_at: string;
  econ_floor_computed_at: string;
  params_hash: string;
  decision: string;
  reason: string | null;
  notes: string | null;
  screen_result: Record<string, unknown>;
  superseded_by: string | null;
  // spec section 7.5 point 6 (r4): how many registered datasets this candidate's corpus manifest
  // left out because their vault shards are withheld -- a disclosed COUNT, never an id.
  withheld_excluded: number;
}

export interface ScoutFamily {
  family_id: string;
  family_root_id: string;
  // The union-N denominator across every grid_version ever run for this family -- never a
  // client-recount of `trials.length` (a superseded/tampered row must not silently change it).
  variants_tried: number;
  trials: ScoutTrialRow[];
}

export interface DeskScoutResponse {
  families: ScoutFamily[];
  chain_verification: MicroChainVerification;
}

export interface DeskScoutComputeProgress {
  candidates_total: number;
  candidates_done: number;
  current_candidate_id: string | null;
}

// GET/POST /research/desk/micro/scout/compute -- served verbatim, no `id`/`run_id` field on the
// GET shape (unlike DeskScreenComputeSnapshot/DeskTopupComputeSnapshot; confirmed against
// `get_scout_compute`'s own return statement, not assumed from a sibling type).
export interface DeskScoutComputeSnapshot {
  state: "idle" | "running" | "done" | "cancelled" | "failed";
  progress: DeskScoutComputeProgress;
  started_utc: string | null;
  finished_utc: string | null;
  error: string | null;
}

// POST /research/desk/micro/scout/compute's own two-shape body (both at HTTP 200 -- a refusal is
// NOT an HTTP error here, unlike the topup/reconcile precedent): confirmed against
// `trigger_scout_compute`'s own body.
export type DeskScoutComputeTriggerResponse =
  | { state: "running"; run_id: string }
  | { state: "refused"; reason: string };

export interface DeskScoutRunLogEntry {
  run_id: string;
  state: "done" | "cancelled" | "failed";
  started_utc: string;
  finished_utc: string;
  candidates_done: number;
  candidates_total: number;
  error: string | null;
}

export interface DeskScoutRunsResponse {
  runs: DeskScoutRunLogEntry[];
}

// --- Walk-Forward -- GET /research/desk/micro/walkforward (walkforward.py `list_fold_specs`,
// `list_walkforward_sequences`, `decay_view`, `sequence_verdict`/`evaluate_survivor_rule`) -------

export interface WalkForwardFoldResultRow {
  sequence_id: string;
  corpus_id: string;
  mode: string;
  rule_id?: string;
  fitting_rule?: string | null;
  spec_hash?: string;
  fold_index: number;
  sidedness: string;
  econ_floor: Record<string, unknown> | null;
  evidence_class: string;
  process_label: string;
  registered_at: string;
  status: string;
  n: number;
  n_sessions: number;
  n_symbols: number;
  effect: number | null;
  unit: string;
  sign: string | null;
  missing: Record<string, string>;
}

export interface WalkForwardDecayFoldRow {
  fold_index: number;
  status: string;
  effect: number | null;
  // r13: the unit this row's own `effect` is in — `return_bps` for a row written under the r13
  // contract, `legacy_percent` for a pre-r13 row that declared none. Served per row precisely so
  // a percent magnitude can never be read under a bps column header.
  unit: string;
  n: number;
  n_sessions: number;
  sign: string | null;
  evidence_class: string;
  process_label: string;
}

export interface WalkForwardDecayView {
  fold_rows: WalkForwardDecayFoldRow[];
  recency: {
    older_fold_count: number;
    recent_fold_count: number;
    older_positive_share: number | null;
    recent_positive_share: number | null;
  };
}

// WF_SURVIVOR_RULE_V1's own two-shape verdict (walkforward.py `sequence_verdict`): a refusal below
// WF_MIN_SUFFICIENT_FOLDS, never a fabricated result, or the full five-condition predicate.
export interface WalkForwardSurvivorConditions {
  sufficient_oos_rule_process_folds: boolean;
  sign_agreement: boolean;
  pooled_effect_clears_econ_floor: boolean;
  no_opposite_direction_sufficient_fold: boolean;
  zero_voiding_events: boolean;
}

export type WalkForwardSequenceVerdict =
  | { refused: true; reason: string; n_sufficient_folds: number }
  | {
      refused: false;
      verdict: string;
      rule_name: string;
      conditions: WalkForwardSurvivorConditions;
      n_sufficient_folds: number;
      n_eligible_folds: number;
      sign_agreement: number;
      pooled_effect: number | null;
    };

export interface WalkForwardSequence {
  sequence_id: string;
  corpus_id: string;
  mode: string | null;
  fitting_rule: string | null;
  rule_id: string | null;
  sidedness: string;
  econ_floor: Record<string, unknown> | null;
  voided: boolean;
  fold_results: WalkForwardFoldResultRow[];
  decay_view: WalkForwardDecayView;
  sequence_verdict: WalkForwardSequenceVerdict;
}

// `latest_fold_spec`'s own row -- carries at least `corpus_id`; the rest of the frozen geometry
// (fold counts/day-widths/purge/embargo) rendered verbatim via an index signature rather than
// enumerated field-for-field (T-1: never invent a shape not directly verified this pass).
export interface WalkForwardFoldSpec {
  corpus_id: string;
  [key: string]: unknown;
}

export interface DeskWalkforwardResponse {
  fold_specs: WalkForwardFoldSpec[];
  sequences: WalkForwardSequence[];
  chain_verification: MicroChainVerification;
}

export interface DeskWalkforwardComputeProgress {
  steps_total: number;
  steps_done: number;
  current_step: string | null;
}

export interface DeskWalkforwardComputeSnapshot {
  state: "idle" | "running" | "done" | "cancelled" | "failed";
  progress: DeskWalkforwardComputeProgress;
  started_utc: string | null;
  finished_utc: string | null;
  error: string | null;
}

export type DeskWalkforwardComputeTriggerResponse =
  | { state: "running"; run_id: string }
  | { state: "refused"; reason: string };

export interface DeskWalkforwardRunLogEntry {
  run_id: string;
  state: "done" | "cancelled" | "failed";
  started_utc: string;
  finished_utc: string;
  steps_done: number;
  steps_total: number;
  error: string | null;
  // `trigger_walkforward_compute`'s own extra terminal-log fields (merged onto the run-log entry
  // on success only -- absent on a `failed`/`cancelled` entry, since `_work`'s return is never
  // reached in that path).
  folds_evaluated?: number;
  folds_replayed?: number;
  validation_sessions?: number;
  session_count?: number;
}

export interface DeskWalkforwardRunsResponse {
  runs: DeskWalkforwardRunLogEntry[];
}

// --- Validation Vault -- GET /research/desk/micro/vault, READ-ONLY this iteration (vault.py
// `build_vault_state`/`_serialize_shard`/`_serialize_universe`) ------------------------------------
//
// Section 7.5's three-stage shard reveal and the r7 two-stage universe reveal, both transcribed as
// an explicit per-stage whitelist matching `vault.py`'s own positive whitelist (never a superset --
// TC-4/TC-5/TC-15 depend on the FRONTEND never widening what the backend already narrowed).

// `exposure_state` is the discriminant across BOTH interfaces (disjoint literal sets, never
// widened to the full three-value union on either side) so the page can narrow on
// `shard.exposure_state === "sealed"` — the server's own stage label — rather than on which
// optional fields happen to be present (vault.py's own "never field-presence inference" rule,
// carried into the type layer).
export interface VaultOpaqueShard {
  shard_id: string;
  universe_id: string;
  // Order-of-magnitude ONLY (`vault._coarse_size_bucket`: "~0" or "~10^N") -- never an exact count,
  // and never arithmetic material (TC-9/Guardrails: no count is ever derived from this field).
  size_bucket: string;
  checksum_commitment: string;
  sealed_at: string;
  exposure_state: "sealed";
}

export interface VaultRevealedShard {
  shard_id: string;
  universe_id: string;
  size_bucket: string;
  checksum_commitment: string;
  sealed_at: string;
  exposure_state: "assigned" | "exposed";
  dataset_id: string;
  family_root_id: string;
  symbol: string;
  session_date: string;
  assigned_at: string;
  exposed_at: string | null;
  // Present only once `exposure_state === "exposed"` (vault.py `_serialize_shard`).
  content_checksum?: string;
}

export type VaultShardRow = VaultOpaqueShard | VaultRevealedShard;

export interface VaultCommittedUniverse {
  universe_id: string;
  registered_at: string;
  rule_commitment: string;
  vault_secret_commitment: string;
  symbol_rule_size: number;
  date_rule_size: number;
  rule_disclosure: "committed";
}

export interface VaultRevealedUniverse {
  universe_id: string;
  registered_at: string;
  rule_commitment: string;
  vault_secret_commitment: string;
  symbol_rule: string[];
  date_rule: string[];
  commitment_nonce: string;
  rule_disclosure: "revealed";
}

export type VaultUniverseRow = VaultCommittedUniverse | VaultRevealedUniverse;

export interface DeskVaultResponse {
  universes: VaultUniverseRow[];
  shards: VaultShardRow[];
  // TWO distinct chain-verification fields (never one shared `chain_verification` like Scout/
  // Walk-Forward) -- the shard ledger and the universe ledger are separate hash chains.
  shard_ledger_chain_verification: MicroChainVerification;
  universe_ledger_chain_verification: MicroChainVerification;
}

// --- Graduation -- GET /research/desk/micro/graduation (micro_graduation.py
// `list_graduation_families`), J-11: the funnel's terminal state, read verbatim for the first
// time -- zero UI readers before this iteration. A family's own `transitions`/`sealed_evaluations`
// rows vary in shape by transition target state / evaluation artifact (the `WalkForwardFoldSpec`
// precedent above): each carries the few fields this page destructures directly, plus an index
// signature for everything else, rendered as an opaque, verbatim JSON detail (never enumerated
// field-by-field -- the `screen_result`/raw `fold_results` precedent).
export interface GraduationTransitionRow {
  from_state: string;
  to_state: string;
  evaluated_at: string;
  [key: string]: unknown;
}

export interface GraduationSealedEvaluationRow {
  dataset_id: string;
  verdict: string;
  n: number;
  evaluated_at: string;
  [key: string]: unknown;
}

export interface GraduationFamily {
  family_root_id: string;
  state: string;
  transitions: GraduationTransitionRow[];
  sealed_evaluations: GraduationSealedEvaluationRow[];
}

export interface DeskGraduationResponse {
  families: GraduationFamily[];
  // Set to the ledger's own `EMPTY_LEDGER_MESSAGE` ("No candidates ledgered.") when `families` is
  // empty, `null` otherwise -- rendered verbatim, never a hardcoded fallback string.
  message: string | null;
  chain_verification: MicroChainVerification;
}

// --- Feature Snapshots -- GET /research/desk/micro/snapshots (micro_snapshots.py
// `snapshot_meta_report`), J-12: the observer's build-metadata surface -- registered since era
// baseline (J-02), read verbatim for the first time in the browser this iteration. Every field is
// the snapshot's own seven-component identity tuple (spec section 2.3) plus quote_size_unit/
// row_count/bytes_on_disk/built_utc, beside two disclosure counts the SAME route now serves.
export interface SnapshotMeta {
  dataset_id: string;
  dataset_checksum: string;
  micro_algo_version: number;
  snapshot_format_version: string;
  feature_source_hash: string;
  config_fingerprint: string;
  params_hash: string;
  quote_size_unit: string;
  row_count: number;
  bytes_on_disk: number;
  built_utc: string;
}

export interface DeskMicroSnapshotsResponse {
  snapshots: SnapshotMeta[];
  // Pool-derived (never snapshot-file-derived, TC-7): how many unresolved-pool datasets this
  // enumeration withheld.
  withheld_excluded: number;
  // A meta file present on disk whose identity re-verification failed (TR-7) -- "built, then
  // invalidated", never "never built". Never carries the stale value itself, only its count.
  stale_excluded: number;
}

export interface DeskMicroSnapshotRunLogEntry {
  run_id: string;
  state: "done" | "cancelled" | "failed";
  started_utc: string;
  finished_utc: string;
  datasets_done: number;
  datasets_total: number;
  error: string | null;
  withheld_excluded: number;
}

export interface DeskMicroSnapshotRunsResponse {
  runs: DeskMicroSnapshotRunLogEntry[];
}
