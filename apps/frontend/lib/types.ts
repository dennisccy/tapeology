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

// The holding-period MANAGEMENT STANCE (capability 27, J-53; data-contract row 25 stance half) —
// read VERBATIM from the WS `thesis` key (or `/research/thesis/active`). Present ONLY while the thesis
// is ENTRY-MARKED and unresolved and a live monitor is evaluating; absent otherwise (no frozen-stale
// stance). Computed ONCE server-side from the latest published verdict — the strip renders the
// `value` color + the `label` text + the `evidence` line and DERIVES NOTHING.
//   * thesis_intact      — the tape published a confirmation; the position holds (emerald);
//   * thesis_weakening   — the confirming evidence faded / never confirmed (amber);
//   * thesis_invalidated — the J-44 system auto-resolve; terminal (rose, terminal treatment).
export interface ManagementStance {
  value: "thesis_intact" | "thesis_weakening" | "thesis_invalidated";
  evidence: string;
  label: string;
}
// The live distance from the current last to the declared invalidation (capability 27 / row 27),
// computed ONCE server-side via the ONE r_basis() helper. `dollars` is signed (POSITIVE = the safe
// side of the invalidation; negative once price crosses it); `r` is that distance in R units (`null`
// on a degenerate R == 0 basis or before any last). The strip renders both in font-mono, verbatim.
export interface DistanceToInvalidation {
  dollars: number | null;
  r: number | null;
}

// The ENTRY CHECKLIST (capability 33, J-63; data-contract row 25 checklist half) — read VERBATIM from
// the WS `thesis` key (or `/research/thesis/active`). Present ONLY on the PRE-ENTRY-MARK cue path (an
// active, evaluated, NOT-yet-entry-marked thesis); absent once an entry is marked (the management
// stance takes over — mutually exclusive) and on the no-thesis / not-evaluated paths. Computed ONCE
// server-side: the strip renders each check's label + margin verbatim and DERIVES NOTHING (zero client
// arithmetic, zero stance derivation; display rounding only).
//   * conditions_met     — every check passes after confirmation (emerald);
//   * conditions_not_met — at least one check is unmet, with the blocker list (slate);
//   * tape_against       — the published verdict is rejecting the thesis (rose);
//   * no_fresh_tape      — the feed is not live / the tape is not current (amber) — never a frozen green.
export interface ChecklistCheck {
  check: string;
  label: string;
  caption: string;
  passed: boolean;
  // The live measured margin in this check's OWN units (a verdict string; events vs floor; the stream
  // status; lag s vs bound; spread bps vs cap; speed vs floor; spread-multiples vs floor; chase return
  // vs threshold). Rendered VERBATIM in font-mono — the frontend does no arithmetic on it.
  margin: string;
}
export interface ChecklistStance {
  value: "conditions_met" | "conditions_not_met" | "tape_against" | "no_fresh_tape";
  label: string;
  evidence: string;
}
export interface ChecklistNearestCounterevidence {
  check: string;
  label: string;
  margin: string;
  line: string;
}
export interface EntryChecklist {
  stance: ChecklistStance;
  checks: ChecklistCheck[];
  passed: number;
  total: number;
  // The failing checks (their ids) — named only when the conditions are not met; empty on met.
  blockers: string[];
  // The closest condition that would FLIP the current read, with its margin — or null if none.
  nearest_counterevidence: ChecklistNearestCounterevidence | null;
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
  // The holding-period management stance + live readouts (capability 27, J-53; row 25 stance half) —
  // present as additive keys ONLY while the thesis is ENTRY-MARKED and unresolved and a live monitor
  // is evaluating (computed ONCE server-side; the strip renders them verbatim, derives nothing).
  // Absent otherwise (no entry mark, or the surviving not-evaluated path — NO frozen-stale stance).
  management_stance?: ManagementStance;
  // The live distance from the current last to the invalidation, in $ and R (signed). Present with
  // the stance; absent otherwise. Rendered in font-mono, verbatim.
  distance_to_invalidation?: DistanceToInvalidation;
  // The current open move in R, signed by direction (a move in the thesis's favor is positive); the
  // SAME sign convention as the realized-move readout. `null` before any last / on a degenerate R==0.
  open_r?: number | null;
  // The entry checklist (capability 33, J-63; row 25 checklist half) — present as an additive key ONLY
  // on the PRE-ENTRY-MARK cue path (active + evaluated + NO entry mark), mutually exclusive with the
  // management stance. Computed ONCE server-side; the strip renders it verbatim, derives nothing.
  entry_checklist?: EntryChecklist;
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
  // The replay-studies display copy (capability 32, J-60/J-61/J-62) — the /studies page renders every
  // label / caption / framing + each status's own absence sentence VERBATIM (the frontend hardcodes
  // none). Optional so a pre-J-60 taxonomy payload stays valid (the page then falls back to its own
  // minimal copy register).
  studies?: StudiesTaxonomy;
  // The management-stance catalog (capability 27, J-53; row 25 stance half) — the three stance labels,
  // the two DISTINCT honest-absence copies (no entry mark yet vs not currently evaluated), and the
  // journaled-measurement readout caption. The strip renders the per-thesis stance's own `label`, so
  // it reads `stance_absence` (for the no-entry-mark copy) + `stance_readout_caption` here. Optional so
  // a pre-J-53 taxonomy payload stays valid (the strip then falls back to its own minimal copy).
  management_stances?: TaxonomyEnum[];
  stance_absence?: { no_entry_mark: string; not_evaluated: string };
  stance_readout_caption?: string;
  // The entry-checklist catalog (capability 33, J-63; row 25 checklist half) — the eight check labels +
  // unit captions, the four aggregate-stance labels, and the checklist honest-absence copy. The strip
  // renders each per-thesis check's own `label`/`margin` + the stance's own `label`/`evidence` verbatim
  // off the projection, so it needs these only for completeness/discoverability + the absence copy.
  // Optional so a pre-J-63 taxonomy payload stays valid.
  checklist_checks?: { id: string; name: string; caption: string }[];
  checklist_stances?: TaxonomyEnum[];
  checklist_absence?: { no_fresh_tape: string };
  // The setup-forming hints display copy (capability 33, J-65) — the cockpit hint dock + the /journal
  // hint-log view render every label / register line / column / empty-state copy VERBATIM (the frontend
  // hardcodes none). The per-hint evidence + baseline citation travel on each hint object. Optional so a
  // pre-J-65 taxonomy payload stays valid (the surfaces then fall back to their own minimal copy).
  hints?: HintsTaxonomy;
  // The feed-basis display copy (capability 28 honesty stamps, J-67; data-contract row 24 additive) —
  // the cockpit feed-basis badge renders the served `data_feed` with these per-feed labels, and on the
  // live IEX basis the disclosure line renders beside it. The /journal hint-log stamp also reads the
  // per-feed label here. The frontend hardcodes NONE of it. Optional so a pre-J-67 taxonomy payload
  // stays valid (the badge then falls back to the raw feed id).
  feed_basis?: FeedBasisTaxonomy;
  // The optional sound-cue display copy + the config-owned cooldown VALUE (capability 33 final item,
  // J-66; data-contract row 24 additive) — the cockpit's sound-cue toggle renders the label /
  // description / register VERBATIM and reads the cooldown number (no UI magic number). The frontend
  // hardcodes NONE of it. Optional so a pre-J-66 taxonomy payload stays valid (the toggle then renders
  // nothing rather than fabricate copy).
  sound_cue?: SoundCueTaxonomy;
  disclaimer: string;
}

// The optional sound-cue taxonomy block (J-66) — the toggle label, the off-by-default/transition-only
// description, the fired-indicator label, the reused register line, and the config-owned cooldown (s).
export interface SoundCueTaxonomy {
  copy: {
    toggle_label: string;
    description: string;
    fired_indicator_label: string;
    register: string;
  };
  cooldown_seconds: number;
}

// The feed-basis taxonomy block (J-67) — per-feed display labels + the live IEX-vs-SIP disclosure
// line, owned once on the backend and rendered VERBATIM (the frontend never hardcodes a feed label
// or the disclosure text).
export interface FeedBasisTaxonomy {
  feeds: TaxonomyEnum[]; // [{id:"sim"|"iex"|"sip", name}]
  live_disclosure: string;
}

// The setup-forming hints display copy owned by the backend (`GET /research/taxonomy` → `hints`).
export interface HintsTaxonomy {
  patterns: { id: string; name: string; setup_type: string; direction: string }[];
  copy: {
    dock_title: string;
    dock_register: string;
    declare_label: string;
    declare_caption: string;
    declared_from_label: string;
    log_title: string;
    log_empty: string;
  };
  log_columns: {
    time: string;
    ticker: string;
    pattern: string;
    // The stored `data_feed` stamp column (J-67, additive). Optional so a pre-J-67 taxonomy payload
    // stays valid (the column header then falls back to "Feed").
    feed?: string;
    evidence: string;
    baseline: string;
    declared_from: string;
  };
  baseline_unvalidated: string;
}

// The replay-studies display copy owned by the backend (`GET /research/taxonomy` → `studies`).
export interface StudiesTaxonomy {
  statuses: TaxonomyEnum[];
  // Per-status honest-absence copy — each status its OWN explicit sentence (iter-15 lesson). Keyed by
  // status id (queued / running / cancelled / failed).
  status_absence: Record<string, string>;
  // The flat copy register (title, framing, form labels, results labels, captions). The page reads
  // each key by name — the backend stays the single owner of every studies label/caption.
  copy: Record<string, string>;
  state_native_setups: string[];
  level_setups: string[];
  ternary_outcomes: TaxonomyEnum[];
}

// One per-horizon ternary distribution row for a study population (setup or null baseline). The
// resolved-outcome counts + a SEPARATE truncated count (never folded into the resolved buckets).
export interface StudyHorizonRow {
  horizon: number;
  "+1R_first": number;
  "-1R_first": number;
  neither_within_horizon: number;
  truncated: number;
}

// One armed occurrence row (setup or null) — read VERBATIM (the page recomputes nothing).
export interface StudyOccurrence {
  arm_logical_ts: number;
  arm_price: number;
  spread_at_arm: number | null;
  invalidation_price: number;
  r_basis: number;
  horizons: { horizon: number; outcome: string | null; truncated: boolean; mfe_r: number; mae_r: number }[];
  verdict_summary?: string;
}

// One population's aggregate (n + the per-horizon ternary distribution).
export interface StudyPopulationAggregate {
  n: number;
  horizons: StudyHorizonRow[];
}

// The full study projection served by `GET /research/studies/{id}` (and each list row). Status /
// progress while running; occurrence rows + aggregates + the seeded null baseline once terminal. Read
// VERBATIM — the page computes nothing.
export interface Study {
  id: string;
  status: "queued" | "running" | "done" | "cancelled" | "failed";
  source_kind: string;
  source_id: string;
  source: string;
  setup_type: string;
  direction: string;
  level_price: number | null;
  data_feed: string;
  config_fingerprint: string;
  null_baseline_seed: number;
  null_arm_count: number;
  hindsight_level: boolean;
  excluded_from_cross_study_aggregate: boolean;
  created_wall_ts: number;
  partial?: boolean;
  error?: string;
  events_processed?: number;
  min_sample_size?: number;
  occurrences?: StudyOccurrence[];
  null_occurrences?: StudyOccurrence[];
  aggregates?: {
    setup: StudyPopulationAggregate;
    null_baseline: StudyPopulationAggregate;
  };
}

// The body for `POST /research/studies` (capability 32, J-60).
export interface CreateStudyParams {
  source_kind: "reference" | "sim" | "historical";
  source_id: string;
  setup_type: string;
  direction: string;
  level_price?: number | null;
  start?: string;
  end?: string;
  null_baseline_seed?: number;
}

export interface CreateStudyResult {
  ok: boolean;
  study?: Study;
  status?: number;
  error?: string;
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
  // Additive `thesis` key (data-contract row 15): the active-thesis projection (same object as
  // GET /research/thesis/active), or `null` when none. Optional so a pre-research snapshot shape
  // (e.g. the REST initial-paint assembly) is still valid; the strip reads it verbatim.
  thesis?: ThesisProjection | null;
  // Additive `hint` key (data-contract row 22, J-65): the active setup-forming hint projection (same
  // object as GET /research/hints/active), or `null` when none. Optional for the same backward-compat
  // reason; the hint dock reads it verbatim (it never recomputes evidence or citation).
  hint?: Hint | null;
}

// One active setup-forming hint (capability 33, J-65) — the dock reads this VERBATIM (the backend
// computes evidence + baseline citation once; the frontend renders, never derives). Identical shape
// for the active projection AND each persisted hint-log row (the log record IS the projection).
export interface Hint {
  id: string;
  ticker: string;
  pattern_id: string;
  pattern_label: string;
  // Plain-language, present-tense evidence with a measured value (no naked output).
  evidence: string;
  // The setup-type context + direction the declare affordance prefills.
  setup_type: string;
  direction: string;
  // The user's matching studied baseline cited verbatim, or exactly "no studied baseline —
  // unvalidated pattern".
  baseline_citation: string;
  // Honesty stamps (assigned once at fire).
  bound_source: string;
  data_feed: string;
  config_fingerprint: string;
  logical_ts: number;
  wall_ts: number;
  // Present only once the user completed a declaration FROM this hint (the created thesis id).
  declared_from?: string;
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
// (or store-first serve) a real bar series for a chosen symbol/timeframe/date-range. Mirrors
// `CreateStudyResult`/`DeclareResult`'s shape byte-for-byte: `{ok, bar_series}` on success (a
// fresh Yahoo fetch OR a store-first hit — both `200`, never `409` for a repeat window), or
// `{ok:false, error, status}` with the backend's own 422/503/504/409 detail surfaced verbatim.
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
// "a cancelled backtest carries NO result block" — a partial simulated PnL is never served, unlike
// a Study's cancelled-but-partial results). `dataset`/`strategy` reuse the EXISTING `Dataset` /
// `Strategy` types verbatim (the report echoes the exact stored dataset metadata and the resolved
// strategy config — never a second shape).
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
// present only while "running" (throttled progress, the `Study.events_processed` precedent). The
// Comparison section renders nothing until `status === "done"` (and `result` itself is present) —
// mirroring `StudyResultsView`'s terminal-with-results gate, but WITHOUT including "cancelled"
// (which never carries a result here).
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
