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

// One journaled action mark (entry | exit) — the user's OWN already-taken action, recorded
// VERBATIM (J-52, data-contract row 18). `price` is exactly as the user submitted it (never an
// inferred/simulated fill); `spread_at_mark` is the moment spread recorded once at marking (`null`
// when there was no quote). The strip renders these verbatim — it derives nothing.
export interface ActionMark {
  kind: "entry" | "exit";
  price: number;
  logical_ts: number;
  wall_ts: number;
  spread_at_mark: number | null;
}

// The action-marks + realized-R projection (J-52, data-contract rows 18 & 27) — computed ONCE
// server-side by the single marks projection (REST `/thesis/active` ≡ the WS `thesis` key ≡
// `/journal/{id}`). The strip reads these verbatim — NO client-side arithmetic.
//   * `has_entry`   — the entry-marked fact the UI reads to WITHDRAW the Abandon control;
//   * `r_basis`     — R = |entry − invalidation|, present once an entry exists, else null;
//   * `realized_r`  — the signed realized move in R, present ONLY once BOTH marks exist (no marks =>
//                     null: NO realized metric is shown — never a dishonest zero).
export interface ThesisMarks {
  entry: ActionMark | null;
  exit: ActionMark | null;
  has_entry: boolean;
  r_basis: number | null;
  realized_r: number | null;
}

// Thesis chart geometry (capability 25, J-48) — read VERBATIM from the WS `thesis` key's `geometry`
// object (or `/research/thesis/active`). Computed ONCE server-side in the single thesis-projection
// builder from the declared prices + the append-only verdict timeline + the action marks; the chart
// draws it as-is on the SAME row-13 epoch anchor the candles use (`epoch_anchor + logical_ts`). The
// chart recomputes no price/side/state/time basis of its own.
//   * price-lines render as labeled horizontal lines (invalidation always; level only when set);
//   * markers render distinct from tape-state markers — verdict transitions, the first confirmation,
//     and the user's entry/exit marks (the marks present ONLY when recorded — no fabricated marker).
export interface GeometryPriceLine {
  kind: "invalidation" | "level";
  price: number;
  label: string;
}
export interface GeometryMarker {
  kind: "verdict" | "first_confirmation" | "entry" | "exit";
  logical_ts: number;
  label: string;
  // Present on a verdict marker (the published verdict + its appended `last`); absent on the others.
  verdict?: ThesisVerdict | "watch_restarted" | "expired";
  wall_ts?: number;
  last?: number | null;
  // Present on entry/exit mark markers (the verbatim recorded price); absent on verdict markers.
  price?: number;
}
export interface ThesisGeometry {
  price_lines: GeometryPriceLine[];
  markers: GeometryMarker[];
}

// One frozen entry risk flag (capability 26, J-49) — computed ONCE at declaration from the live
// engine snapshot + config and frozen on the thesis (advisory, never blocking). The strip renders
// the `label` + the plain-language measured `evidence` VERBATIM as an amber chip; it derives
// nothing (the `measured` raw values back the evidence and feed later review). `flag` is the
// canonical id (taxonomy `RISK_FLAGS`).
export interface RiskFlag {
  flag: string;
  label: string;
  evidence: string;
  measured: Record<string, unknown>;
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
  // Plain-language evidence for the CURRENTLY published verdict (capability 24 / no-naked-outputs):
  // every verdict — including pending — carries descriptive, present-tense, thesis-attributed
  // evidence read VERBATIM from the WS `thesis` key. The frontend never derives or composes it.
  verdict_evidence: string;
  statements: ThesisStatement[];
  entry_context: Record<string, unknown>;
  bound_source: string;
  data_feed: "sim" | "sip" | "iex";
  config_fingerprint: string;
  // Action marks + realized-R (J-52, data-contract rows 18 & 27) — read verbatim from the WS
  // `thesis` key. Optional so a pre-J-52 snapshot shape stays valid; absent => the strip shows no
  // marks (and still offers Mark entry).
  marks?: ThesisMarks;
  // Chart geometry (J-48) — read verbatim by PriceChart. Optional so a pre-J-48 snapshot shape stays
  // valid; absent => the chart draws no thesis overlay (exactly the no-thesis render).
  geometry?: ThesisGeometry;
  // Entry risk flags (capability 26, J-49) — read VERBATIM from the WS `thesis` key. Frozen at
  // declaration (they never change as the tape moves). Honest-omission: the key is ABSENT for a
  // pre-v4 thesis that was never risk-assessed (the strip shows no chips); an EMPTY array means
  // assessed-nothing-fired (also no chips — and NO "all clear" badge, no naked reassurance). A
  // non-empty array renders one amber advisory chip per flag.
  risk_flags?: RiskFlag[];
  // "ok" normally; "failed" if the research monitor or its store write errored — surfaced honestly.
  // "not_evaluated" (J-47): an ENTRY-MARKED thesis that SURVIVES a stopped/restarted watch as a real
  // position — it is not orphaned, but no verdict accrues while the matching source is not watched.
  // Re-watching the same source resumes it. The strip renders the not-evaluated variant + notice.
  monitor_status: "ok" | "failed" | "not_evaluated";
  // The backend-owned plain-language lifecycle notice (J-47, data-contract row 24) — present ONLY
  // when not_evaluated (the not-currently-evaluated notice naming the bound source, or the
  // mismatched-source notice). Rendered VERBATIM by the strip; the frontend composes none of it.
  monitor_notice?: string;
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
  // The entry risk-flag catalog (capability 26, J-49) — id + display label. Optional so a pre-J-49
  // taxonomy payload stays valid. The strip reads the per-thesis frozen flag's own `label`, so it
  // never needs this map to render — it is here for completeness/discoverability.
  risk_flags?: TaxonomyEnum[];
  // Thesis lifecycle statuses + the resolution subset (J-51) — the journal table + filter controls
  // render these labels VERBATIM (the frontend hardcodes no status/resolution label). Optional so a
  // pre-J-51 taxonomy payload stays valid.
  statuses?: TaxonomyEnum[];
  resolutions?: TaxonomyEnum[];
  // The mistake-tag catalog (capability 29, J-54) — the review picker renders these labels VERBATIM
  // (the frontend hardcodes no tag label). `requires_note` flags the tags that need a free-text note
  // at save (enforced in the J-57 save flow). Optional so a pre-J-54 taxonomy payload stays valid.
  mistake_tags?: MistakeTag[];
  // The outcome × process grade catalogs (capability 29, J-56) — the journal quadrant + rows render
  // these labels VERBATIM (the frontend hardcodes no grade label). Optional so a pre-J-56 taxonomy
  // payload stays valid.
  outcome_grades?: TaxonomyEnum[];
  process_grades?: TaxonomyEnum[];
  // The excursion display copy (capability 30, J-58) — the journal detail's two excursion blocks
  // render the ternary-outcome labels, the truncated flag, the population titles, and the honest-
  // absence copy VERBATIM (the frontend hardcodes none of them). Optional so a pre-J-58 taxonomy
  // payload stays valid (the block then falls back to humanised ids).
  excursions?: ExcursionTaxonomy;
  // The segregated-analytics display copy (capability 31, J-59) — the /journal analytics view renders
  // every label / caption / framing VERBATIM (the frontend hardcodes none). Optional so a pre-J-59
  // taxonomy payload stays valid (the view then falls back to its own minimal copy register).
  analytics?: AnalyticsTaxonomy;
  disclaimer: string;
}

// The segregated-analytics display copy owned by the backend (`GET /research/taxonomy` → `analytics`).
// A flat string map (the view reads each key by name) — keeps the backend the single owner of every
// analytics label, caption, and the honesty framing line.
export type AnalyticsTaxonomy = Record<string, string>;

// The excursion display copy owned by the backend (`GET /research/taxonomy` → `excursions`).
export interface ExcursionTaxonomy {
  ternary_outcomes: TaxonomyEnum[];
  truncated_label: string;
  populations: TaxonomyEnum[];
  // Per-population honest-absence copy (never-confirmed / no-entry-mark), keyed by population id.
  not_applicable: Record<string, string>;
  // The restart-sweep "not tracked" copy (no live tape to measure from — no numbers, not a zero).
  not_tracked: string;
  r_basis_caption: string;
}

export interface MistakeTag {
  id: string;
  name: string;
  requires_note: boolean;
}

// The outcome × process grades (capability 29, J-56) — computed ONCE at resolution, served VERBATIM.
// Both axes are ENUM labels (NEVER a numeric score); `process_evidence` names the checks/flags that
// drove the process grade (no naked grade). The frontend renders the LABELS from the taxonomy and the
// evidence verbatim — it derives nothing.
export interface ThesisGrades {
  outcome: "thesis_held" | "thesis_failed" | "no_read";
  process: "clean" | "flagged" | "violated";
  process_evidence: string;
}

// One per-horizon excursion row (capability 30, J-58) — measured ONCE at the terminal resolution /
// stream-end, served VERBATIM. `mfe_r`/`mae_r` are the max favorable/adverse excursion in R units over
// the horizon window (never currency); `outcome` is the ternary by FIRST TOUCH (`null` while a
// horizon was cut short with no first touch — `truncated` then tells the story); `truncated` flags a
// horizon the stream end / a gap cut short. The page renders these verbatim — it derives nothing.
export interface ExcursionHorizon {
  horizon: number;
  mfe_r: number;
  mae_r: number;
  outcome: "+1R_first" | "-1R_first" | "neither_within_horizon" | null;
  truncated: boolean;
}

// One excursion POPULATION (confirmation-anchored OR entry-anchored) — its anchor + per-horizon rows.
// The two populations are segregated end to end and NEVER pooled. `reference_price` is the anchor's
// reference (the first-confirmation `last`, or the verbatim entry-mark price); `r_basis` is
// R = |reference − invalidation|; `spread_at_anchor` is the moment spread stamped ONCE at the anchor.
export interface ExcursionPopulation {
  population: string;
  anchor_logical_ts: number;
  anchor_wall_ts: number;
  reference_price: number;
  invalidation_price: number;
  r_basis: number;
  spread_at_anchor: number | null;
  horizons: ExcursionHorizon[];
}

// The full excursion record (capability 30, J-58) — `tracked: true` carries the measured populations
// (each present ONLY when its anchor existed — never-confirmed => no confirmation key; no entry mark
// => no entry key, honest absence). `tracked: false` is the explicit restart-sweep "not tracked"
// marker (no live tape to measure from — no numbers, never a dishonest zero). Absent entirely on the
// detail body for a pre-v7 resolution (honest omission).
export interface ThesisExcursions {
  tracked: boolean;
  populations: Record<string, ExcursionPopulation>;
}

// One compact journal-list row (J-51) — GET /research/journal. Read VERBATIM from the persisted
// thesis record by the single backend row-projection (nothing recomputed at read). `resolution` is
// the terminal status (null while active); `resolution_reason` is the verbatim persisted
// expired/interruption/resolution reason (null while active). `has_entry`/`has_exit` are the
// persisted action-mark presence facts (never inferred from a price). `reviewed` is ALWAYS present
// (a boolean fact — false until the user saves a review, J-57); `grades` is present ONLY post-
// resolution (honest omission before — J-56).
export interface JournalRow {
  id: string;
  ticker: string;
  bound_source: string;
  data_feed: "sim" | "sip" | "iex";
  config_fingerprint: string;
  setup_type: string;
  direction: "long" | "short";
  created_logical_ts: number;
  created_wall_ts: number;
  status: string;
  resolution: string | null;
  resolution_reason: string | null;
  has_entry: boolean;
  has_exit: boolean;
  reviewed: boolean;
  grades?: ThesisGrades;
}

// One verdict-timeline row from GET /research/journal/{id} (J-55) — the append-only published
// timeline, read VERBATIM (never recomputed at read). `wall_ts` is the TRUE clock time (unix
// seconds) the detail page renders via the ONE shared dd-MM-yyyy formatter; `logical_ts` is the
// engine's logical instant. Lifecycle/gap rows (expired / watch_restarted) carry null
// tape_state/confidence. The dwell timing record (`rule_first_true_*`) is present on a published
// raw-rule transition, absent (null) on the pending/lifecycle rows.
export interface JournalTimelineRow {
  logical_ts: number;
  wall_ts: number;
  verdict: string;
  evidence: string;
  tape_state: string | null;
  confidence: number | null;
  last: number | null;
  rule_first_true_ts: number | null;
  rule_first_true_price: number | null;
}

// One machine-derived execution check (capability 27, J-54) — computed ONCE at resolution, served
// VERBATIM. `status` is an ENUM label (`failed | passed | not_applicable`), NEVER a numeric score;
// `evidence` quotes the measured values. The detail page renders these verbatim — it derives nothing.
export interface ExecutionCheck {
  check: string;
  status: "failed" | "passed" | "not_applicable";
  evidence: string;
}

// The full journal-detail body from GET /research/journal/{id} (J-55) — the per-thesis review
// surface, read VERBATIM. The thesis record (frozen statements, frozen risk flags), the action
// marks + realized-R, the append-only verdict timeline, and the machine-derived execution checks +
// suggested mistake tags (present ONLY post-resolution — honest omission pre-resolution / pre-v5).
// The page recomputes NOTHING — every value is a read of the persisted record.
export interface JournalDetailThesis {
  id: string;
  ticker: string;
  setup_type: string;
  direction: "long" | "short";
  invalidation_price: number;
  level_price: number | null;
  status: string;
  bound_source: string;
  data_feed: "sim" | "sip" | "iex";
  config_fingerprint: string;
  entry_context: Record<string, unknown>;
  // Frozen expected-behaviour statements (the canonical frozen text). Each is `{text, kind, params}`.
  // The FINAL status of each (J-55) is served separately on the detail body as
  // `statement_final_statuses` (positionally keyed) — present only post-v6 resolution.
  statements: { text: string; kind: string; params?: Record<string, unknown> }[];
  created_logical_ts: number;
  created_wall_ts: number;
  // Frozen entry risk flags (J-49) — present only when the thesis was risk-assessed (absent for a
  // pre-v4 thesis: the page shows an honest "not assessed", never an invented clean state).
  risk_flags?: RiskFlag[];
}

// One per-statement FINAL status (J-55) — persisted ONCE at terminal resolution, served VERBATIM,
// positionally keyed to the frozen `statements`. `not_evaluated` is the honest enum where there was
// no live read at the terminal moment (e.g. a restart-expiry sweep). The page renders the badge
// verbatim — it never re-derives a status from the timeline.
export interface StatementFinalStatus {
  status: "not_yet" | "met" | "violated" | "not_evaluated";
}

// The user-CONFIRMED review (J-57, data-contract row 28) — present ONLY once `reviewed` is true.
// Distinct from the machine-SUGGESTED tags on `suggested_mistake_tags` (the system suggests; only
// the user's Save records confirmed tags). Read VERBATIM — the page derives nothing.
export interface SavedReview {
  mistake_tags: string[];
  note: string | null;
}

export interface JournalDetail {
  thesis: JournalDetailThesis;
  marks: ThesisMarks;
  timeline: JournalTimelineRow[];
  // Present ONLY post-resolution (computed once at resolution). Absent => "not assessed" honest copy.
  execution_checks?: ExecutionCheck[];
  suggested_mistake_tags?: string[];
  // Per-statement FINAL statuses (J-55) — present ONLY post-v6 resolution (absent => render the
  // frozen statements without a final-status badge — honest omission). Positionally keyed to
  // `thesis.statements`.
  statement_final_statuses?: StatementFinalStatus[];
  // The outcome × process grades (J-56) — present ONLY post-v6 resolution (absent => "not graded"
  // honest copy). ENUM labels + evidence, read verbatim.
  grades?: ThesisGrades;
  // The user-confirmed-review fact (J-57) — ALWAYS present (a boolean: false until the user saves).
  reviewed: boolean;
  // The saved confirmed review — present ONLY once `reviewed` is true (honest omission before).
  review?: SavedReview;
  // The per-horizon excursion record (capability 30, J-58) — present ONLY post-v7 terminal resolution
  // / stream-end (absent => "not measured", an honest omission). Two segregated populations; R-units
  // only, never currency, never a prediction. Read VERBATIM — the page derives nothing.
  excursions?: ThesisExcursions;
}

// --- Segregated journal analytics (capability 31, J-59) ------------------------------------------
// The `GET /research/analytics` payload, rendered VERBATIM by the /journal analytics view (display
// rounding only — NO client-side arithmetic). Partitions are keyed by (data_feed, config_fingerprint)
// and NEVER pooled; within each, groups are per setup_type × direction. The abandonment bucket is
// always present (even 0); truncated horizon counts are separate from the resolved ternary buckets;
// the acted-trade block is structurally disjoint from the confirmation-anchored stats. R units only —
// never currency, never an equity curve, never a win-rate-as-edge presentation.

// One per-horizon confirmation-anchored ternary distribution row. The three resolved-outcome counts
// plus a SEPARATE truncated count (never folded into a resolved bucket); median spread/R is the
// no-cost caveat beside the +1R figure (`null` when no anchored population carried a spread/R).
export interface AnalyticsHorizonRow {
  horizon: number;
  "+1R_first": number;
  "-1R_first": number;
  neither_within_horizon: number;
  truncated: number;
  median_spread_per_r: number | null;
}

// The acted-trade (entry+exit-marked) block — STRUCTURALLY SEPARATE from the confirmation-anchored
// stats. Realized move in R only (via the one registered marks projection server-side); never currency.
export interface AnalyticsActedTrade {
  n: number;
  median_realized_r: number | null;
  median_spread_per_r: number | null;
}

// One per setup_type × direction group within a partition. `n` is always present (abandoned theses
// stay in it); `abandonment` is its own always-visible count; `insufficient_sample` gates the display
// (n still shown). `median_time_to_confirm` is `null` for a group with no confirmation (honest omission).
export interface AnalyticsGroup {
  setup_type: string;
  direction: string;
  n: number;
  abandonment: number;
  insufficient_sample: boolean;
  confirmation_excursions: { horizons: AnalyticsHorizonRow[] };
  median_time_to_confirm: number | null;
  tag_frequencies: { tag: string; count: number }[];
  acted_trade: AnalyticsActedTrade;
}

// One partition = one (data_feed, config_fingerprint) pair. The FULL fingerprint is always present
// (so two records are never silently compared across fingerprints); the short form is for display.
export interface AnalyticsPartition {
  data_feed: string;
  config_fingerprint: string;
  config_fingerprint_short: string;
  groups: AnalyticsGroup[];
}

export interface Analytics {
  partitions: AnalyticsPartition[];
  min_sample_size: number;
}

export interface AnalyticsResult {
  ok: boolean;
  analytics?: Analytics;
  error?: string;
}

// Server-side filter params for GET /research/journal (J-51). An omitted filter does not constrain;
// the frontend does NO client-side filtering (the server is the only filter authority).
export interface JournalFilters {
  ticker?: string;
  setup_type?: string;
  direction?: string;
  resolution?: string;
  status?: string;
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
