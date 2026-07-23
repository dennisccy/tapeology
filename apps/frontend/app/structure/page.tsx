"use client";

import { useEffect, useRef, useState } from "react";
import {
  cancelEdgeReportCompute,
  createBacktest,
  fetchBacktest,
  fetchDatasets,
  fetchEdgeReport,
  fetchEdgeReportCompute,
  fetchLevels,
  fetchPnlLedger,
  fetchProfiles,
  fetchSetupDetail,
  fetchSetups,
  fetchStrategies,
  recordBarSeries,
  triggerEdgeReportCompute,
} from "@/lib/api";
import type {
  Backtest,
  BacktestAggregate,
  BacktestClassAggregate,
  BacktestResult,
  BarSeriesRecord,
  ConfluenceZone,
  Dataset,
  DatasetsListResult,
  EdgeReportCell,
  EdgeReportComputeSnapshot,
  EdgeReportPayload,
  EdgeReportResponse,
  EdgeReportSurvivingCell,
  LevelsResponse,
  PnlLedger,
  ProfilesPayload,
  SetupEvent,
  Strategy,
  StrategiesPayload,
  TradabilityBand,
} from "@/lib/types";
import { MAX_LOADED_BARS, useBarWindow } from "@/lib/useBarWindow";
import { useRecordedSeries } from "@/lib/useRecordedSeries";
import { useTradability } from "@/lib/useTradability";
import { boundaryTs, pickRepresentativeSeries, timeframesInOrder } from "@/lib/timeframes";
import { SymbolSearch } from "@/components/SymbolSearch";
import { StructureChart } from "@/components/StructureChart";
import { Panel } from "@/components/Panel";
import { FeedBasisBadge } from "@/components/FeedBasisBadge";

// The /structure page — the era-4/5/5B structure stack's browser home. For a chosen symbol +
// as-of time it renders a price chart with one dashed line per S/R level plus a confluence-zones
// table badged A/B/C (era-4 J-01); below that, a read-only Registry section shows the registered
// strategies plus the current champion (era-4 J-02); below THAT, a Comparison section runs
// `structure_tape` against the champion `v1` over a chosen dataset and renders both strategies'
// aggregates + per-class A/B/C breakdown side by side, beside the champion pointer and the
// founding PnL-ledger baseline row (era-4 J-03). Reached from the top-bar link, served by
// GET /meta/ui-routes (data-driven NavBar — no client hardcoding; see apps/backend/app/meta.py
// UI_ROUTES). Follows the /performance page pattern: client component, no business logic,
// canonical endpoints read verbatim, `{ok, data, error}`-shaped fetch results.
//
// Era-5 J-05 added the page's first explicit write action: a fetch-control section (symbol +
// timeframe + UTC date range + a "Fetch from Yahoo Finance" button). Submitting POSTs
// `/research/bars` (keyless; store-first — an already-fetched window is served from storage with
// zero network calls, never a `409`), then loads the fetched symbol/window-end through the
// EXISTING Load path (`handleLoad`). A "Yahoo Finance" provenance badge (the SAME `FeedBasisBadge`
// the cockpit uses, keyed off the charted series' own `feed` field) renders beside the raw-levels
// chart. The fetch control computes no level/zone/PnL/champion value and never promotes.
//
// Era-5B J-05 (this iteration) DECLUTTERS the page: **Tradable Map** (era-5B J-01's ≤10
// quality-scored bands) is now the default view the Load form drives, with the prior raw
// levels/confluence-zones rendering moved behind an explicit, off-by-default "Show raw levels"
// toggle (byte-identical when on — zero change to that code path). Two new sections follow:
// **Case Studies** (era-5B J-02's touch-event registry, filterable by symbol/reaction, with a
// row drill-in showing the era-5B J-03 tape-at-the-wall timeline when a dataset was recorded) and
// **Edge Report** (era-5B J-04's 3-way `v1` / `structure_tape` / `structure_tape_map` comparison,
// register-carrying, honest even when every cell is `insufficient_sample`). The era-5 fetch
// control, provenance badge, Registry, and Comparison sections are unchanged, only repositioned
// below the three new sections (Foundation invariant — nothing existing regresses). Every new
// value is read VERBATIM from its owning endpoint; this iteration recomputes nothing (the
// coherence-auditor's central rail for J-05).
//
// THIRTEEN canonical endpoints (twelve read, one write), rendered VERBATIM and nothing else:
//   * GET /research/levels?symbol=&as_of=  (Data Contract row 39) — levels + confluence zones +
//     the `no_bar_series_for_symbol` honesty flag. The A/B/C badge is `zone.class`, the score is
//     `zone.score` — neither is ever recomputed from breadth or member strength.
//   * GET /research/bars?symbol=&include_bars=false  (Data Contract row 38) — the registered bar
//     series for the loaded symbol, METADATA ONLY (identity/timeframe/feed/bar_count; no candles).
//     Drives the timeframe selector and the representative-series pick. The page still filters the
//     returned array CLIENT-SIDE by the already-served `symbol` field — the SAME filtering
//     discipline NavBar applies to `nav: true` (filtering already-served rows is not a
//     recomputation of any value).
//   * GET /research/candles?symbol=&timeframe=&before_ts|after_ts=&limit=  (Data Contract row 38)
//     — ONE viewport-sized window of the symbol+timeframe's recorded candles, MERGED across every
//     recording for that pair server-side and extended as the operator zooms or scrolls (see
//     `lib/useBarWindow.ts`). Rows are the store's own rows, verbatim; the page chooses only WHICH
//     already-recorded rows are currently in memory (a display/paging choice, exactly like which
//     timeframe to chart) — it never merges, re-bins, gap-fills, or synthesizes a candle. The
//     served `series_count` / `bar_count` / `revised_timestamps` are printed in the chart caption
//     verbatim, so the operator can see how the drawn history was assembled.
//   * POST /research/bars  (Data Contract row 38, era-5 J-05) — the fetch control's one write
//     action: fetch-or-store-first-serve a real Yahoo bar series for {symbol, timeframe, start,
//     end}. The response's own `feed`/`symbol`/`window_end_utc` seed the existing read path above;
//     nothing from this response is rendered directly.
//   * GET /research/strategies  (Data Contract row 40/41, era-4 J-02) — the strategy registry
//     (`v1` + `structure_tape` + `structure_tape_map`) + the champion pointer. Fetched on mount,
//     independent of the Load button (the registry and champion are populated even keyless).
//   * GET /research/profiles  (Data Contract row 33) — read ONLY to cross-check its `champion`
//     against `/research/strategies`'s own `champion` (both read the SAME store pointer — never a
//     second champion source).
//   * GET /research/datasets  (Data Contract row 30, era-4 J-03) — every registered dataset,
//     fetched on mount to populate the Comparison section's dataset selector.
//   * POST /research/backtests + GET /research/backtests/{id}  (Data Contract row 31, era-4 J-03)
//     — the Comparison section's "Run comparison" starts TWO backtests (`v1` + `structure_tape`,
//     both `profile=default`) on the chosen dataset and polls both to a terminal status, reusing
//     the Studies job/poll PATTERN (not its endpoint). Every aggregate, per-class value, and the
//     register line is read verbatim from the terminal payload — zero recomputation.
//   * GET /research/pnl/ledger  (Data Contract row 32, era-4 J-03) — read ONLY for the founding
//     baseline row (`rows.find(r => r.founding)`) shown beside the comparison; the champion badge
//     reuses the ALREADY-fetched `/research/strategies` champion (no second champion fetch).
//   * GET /research/tradability?symbol=&as_of=  (era-5B J-01, THIS iteration) — the tradable
//     level map (bands: range, side, quality score, inherited class, member count, round-number
//     flag, `basis_as_of`), driven by the SAME Load form as the raw-levels read above. Every band
//     field is `String(...)`-rendered verbatim — never recomputed, clustered, or re-scored here.
//   * GET /research/setups (optionally `?symbol=&reaction=`) + GET /research/setups/{id}  (era-5B
//     J-02/J-03, THIS iteration) — the case-study registry, fetched once on mount and filtered
//     client-side (the SAME `bar_series.filter` display-filter precedent above — never a second
//     computation); a row click fetches the drill-in, whose `tape_timeline` is present-but-empty
//     until a recorded dataset covers the touch.
//   * GET /research/edge-report  (era-5B J-04, THIS iteration) — the 3-way strategy-comparison
//     report, fetched once on mount and rendered verbatim, including the honest empty /
//     all-`insufficient_sample` shape on the keyless PG-only-dataset fixture.
//
// The fetch control (era-5 J-05) has its own distinct honest states — see `fetch-yahoo-*`
// testids: idle (fields unset, button disabled), fetching (button disabled, "Fetching…" label),
// success (folds into the Load states below via `handleLoad`), and a POST error surfaced VERBATIM
// via `UnavailablePanel` (distinct backend `detail` text per 422/503/504/409 — never one generic
// message). The provenance badge is absent whenever no series is charted (honest absence, the SAME
// rule `FeedBasisBadge` already enforces for the cockpit).
//
// The Tradable Map section (era-5B J-01, THIS iteration's new default view) has its own distinct
// honest states — see `tradable-map-*` testids — mirroring the raw-levels section's own four-state
// shape: idle, loading, `no_bar_series_for_symbol` (needs provider credentials), a resolved basis
// with zero bands is not a reachable state per `tradability.py`'s own docstring so no such empty
// copy exists, an UNRESOLVED basis (`basis_as_of: null`, `bands: []` — "nothing derivable yet"),
// and backend-unreachable/any non-200 (folded into the shared degraded state, the SAME
// validation-refusal-folding precedent immediately below).
//
// Four distinct honest states for the raw-levels section (toggle-gated, off by default; never
// share copy, never fabricate a chart/level/zone):
//   1. no_bar_series_for_symbol: true            -> explicit "needs provider credentials" state
//   2. no_bar_series_for_symbol: false, levels: []  -> distinct "no levels found" state
//   3. levels non-empty, confluence_zones: []     -> distinct "no qualifying confluence zone"
//      state, scoped to the zones panel only (the chart + level lines still render — the levels
//      DO exist, only no cluster qualifies)
//   4. backend unreachable / any non-200 (including a malformed as_of's 422) -> the shared
//      degraded state (the NavBar/UnavailablePanel pattern), surfacing the backend's own message
//      verbatim — folding a validation refusal into the same honest "couldn't load" treatment
//      satisfies the "never crash, never fabricate" bar without inventing a fifth copy.
//
// The Registry section (era-4 J-02) has its own distinct honest states — loading,
// registry-unavailable (`/research/strategies` unreachable/non-200), and populated — see
// `structure-registry-*` testids.
//
// The Comparison section (era-4 J-03) has several distinct honest states — see `comparison-*`
// testids: no datasets registered, the dataset list unreachable, idle (a dataset list is
// populated but Run has not been clicked), a backtest queued/running (per side, independently), a
// backtest failed (per side), a backtest cancelled (per side, carrying NO result — never a
// partial simulated PnL), a poll-time backend-unreachable notice, and done (aggregates + per-class
// table, `insufficient_sample` shown inline — never a separate "insufficient" state). The section
// NEVER moves the champion pointer and writes NOTHING to the PnL ledger.
//
// The Case Studies section (era-5B J-02/J-03, THIS iteration) has its own distinct honest states —
// see `case-studies-*` testids: loading, unavailable, a true-empty registry (zero events scanned
// anywhere), a filtered-to-zero result (distinct from true-empty — the registry has rows, this
// filter combination simply matches none), and populated. The drill-in (`case-drillin-*` testids)
// adds its own loading/unavailable states plus two more: a recency-boundary disclosure
// (`reaction_boundary_truncated: true` — never presented as a full-horizon reaction) and an
// honest "no recorded tape" state (`tape_timeline: []`, distinct from a populated timeline list).
//
// The Edge Report section (era-5B J-04, THIS iteration) has its own distinct honest states — see
// `edge-report-*` testids: loading, unavailable, and an honest empty/all-`insufficient_sample`
// report (a valid, first-class, never-hidden outcome per goal.md's own "no gate bending for a
// headline" anti-goal) versus a populated report — `insufficient_sample` renders INLINE on each
// cell's real numbers, the SAME `BacktestClassTable` precedent the Comparison section established.
//
// Dark instrument-panel style consistent with /journal, /studies, /performance: slate surfaces,
// restrained borders, font-mono numerics, amber for the honest-empty/degraded states.

const INPUT_CLASS =
  "w-full rounded-md border border-slate-700 bg-slate-950/60 px-2.5 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-600";

const NUMERIC_CELL = "px-2 py-1.5 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
const HEADER_CELL = "px-2 py-1 text-right text-[11px] font-medium text-slate-500";
const LABEL_CELL = "px-2 py-1.5 text-left text-xs text-slate-400 whitespace-nowrap";

// The two registered strategy ids + the frozen default profile id — mirrors the backend's OWN
// config-owned constants byte-for-byte (app/config.py: STRATEGY_V1_ID = "v1", STRATEGY_TAPE_ID =
// "structure_tape", PROFILE_DEFAULT = "default"). These are the REQUEST parameters the Comparison
// section sends to POST /research/backtests — never a client-side strategy/profile definition; the
// registered entries + their own parameters are read verbatim from GET /research/strategies (the
// Registry section above).
const STRATEGY_V1_ID = "v1";
const STRATEGY_TAPE_ID = "structure_tape";
const COMPARISON_PROFILE = "default";

// The backtest status vocabulary's terminal subset (mirrors `backtests.py`'s `TERMINAL_STATUSES`).
// `needsPolling` is `false` for `null` (nothing started yet — nothing to poll) so the J-03 poll
// effect naturally stays quiet before "Run comparison" is clicked and stops once BOTH backtests
// reach a terminal status — not after either one alone.
const BACKTEST_TERMINAL_STATUSES = new Set(["done", "cancelled", "failed"]);

function needsPolling(backtest: Backtest | null): boolean {
  return backtest !== null && !BACKTEST_TERMINAL_STATUSES.has(backtest.status);
}

// `TIMEFRAME_ORDER`, `pickRepresentativeSeries`, `timeframesInOrder`, and `boundaryTs` now live in
// `@/lib/timeframes` (imported above) so the cockpit chart shares this one copy — see that module.

// The era-5 J-05 fetch-control's timeframe set — the SIX Yahoo-supported neutral timeframes
// (goal.md's enumeration), in the order ONE "Fetch from Yahoo Finance" click fetches them (era-5C:
// the control no longer asks the user to pick — a single click records all six). Deliberately a
// SUBSET of the backend's full `CONFIG.bar_timeframes` (nine entries, mirrored in `TIMEFRAME_ORDER`
// above): `15m`/`8h`/`1mo` are valid `bar_timeframes` entries the Yahoo adapter itself does not map
// (`UnsupportedTimeframe`) — fetching them would only reach a statically-known vendor-unsupported
// 422, so the loop simply never attempts them. This is a DISPLAY CHOICE (which already-known-good
// timeframes to fetch), not a second validation authority — the backend's own `bar_timeframes` +
// Yahoo-adapter checks remain the sole enforcement (an out-of-set value still 422s server-side).
const YAHOO_TIMEFRAMES = ["1w", "1d", "4h", "1h", "5m", "1m"];

// era-5C: the per-timeframe outcome of ONE fetch click — each of the six timeframes reports its own
// honest result (fetched/served, already-stored 409, or the backend's own refusal detail) instead
// of one aggregate line, so a timeframe Yahoo cannot serve for this window (e.g. 1m beyond its
// retention) never masks the others that did succeed.
type FetchTimeframeOutcome = {
  timeframe: string;
  state: "pending" | "ok" | "stored" | "error";
  message: string;
};

// Per-state color for a fetch-result row — literal class strings (never interpolated) so Tailwind's
// JIT scanner emits them. Matches the page's existing slate/emerald/amber/rose palette.
const FETCH_RESULT_COLOR: Record<FetchTimeframeOutcome["state"], string> = {
  pending: "text-slate-500",
  ok: "text-emerald-700",
  stored: "text-amber-700",
  error: "text-rose-700",
};

// era-5C: the as-of instant to seed the Load form with after an inclusive-end fetch. The backend's
// levels `_bars_as_of` and this page's own chart filter are BOTH `<= as_of`, and a bar ON the end
// date is stamped AFTER that date's UTC midnight (a 1d bar ~04:00Z, intraday later) — so seeding the
// verbatim `window_end_utc` (midnight) would hide every newly-included end-date bar. Seeding the
// LAST second of the end's UTC day admits every end-date bar (the last 1m bucket starts 23:59:00)
// and never a next-day bar. Bare `YYYY-MM-DD` gets the suffix; a naive timestamp is treated as UTC
// (matching the backend's own `parse_utc_epoch`); an unparseable value is returned unchanged (the
// fetch itself would already have 422'd).
function endOfDayUtc(rawEnd: string): string {
  const trimmed = rawEnd.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) return `${trimmed}T23:59:59Z`;
  const hasTz = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(trimmed);
  const ms = Date.parse(hasTz ? trimmed : `${trimmed}Z`);
  if (Number.isNaN(ms)) return trimmed;
  return `${new Date(ms).toISOString().slice(0, 10)}T23:59:59Z`;
}

// The one caption both charts print under their canvas: what is actually loaded, out of what the
// merged recordings hold, and how that merge was built. Every number is served
// (`GET /research/candles`) or a count of already-served rows — nothing here is estimated.
// `revised` names the timestamps more than one recording covered with differing values (Yahoo
// re-derives adjusted prices per fetch; a mid-session bar is superseded by its completed self) —
// the server serves the most recently fetched recording for those and reports how many there were.
function chartCaption(args: {
  timeframe: string;
  loaded: number;
  available: number;
  seriesCount: number;
  revised: number;
  capped: boolean;
  maxLoaded: number;
}): string {
  const { timeframe, loaded, available, seriesCount, revised, capped, maxLoaded } = args;
  const recordings = `${seriesCount} recording${seriesCount === 1 ? "" : "s"} merged`;
  const revisions =
    revised > 0
      ? `; ${revised.toLocaleString()} timestamp${revised === 1 ? "" : "s"} had more than one recording — the newest fetch is drawn`
      : "";
  const cap = capped
    ? ` At most ${maxLoaded.toLocaleString()} bars are held at once, so the window slides as you scroll.`
    : "";
  return (
    `Candles: ${timeframe} — ${loaded.toLocaleString()} of ${available.toLocaleString()} bars loaded ` +
    `around the query time (${recordings}${revisions}). Zoom or scroll to load more.${cap}`
  );
}

// One recorded series, described the way the fetch rows report it: how many bars, which vendor, and
// the range those bars actually COVER (the server's own `covered_*` fields, not the requested
// window — the two differ whenever a vendor cap shortened the fetch, which is exactly the case
// worth seeing). A recording made before coverage existed simply omits the range.
function describeRecording(record: BarSeriesRecord, vendorLabel: string): string {
  const covered =
    record.covered_start_utc && record.covered_end_utc
      ? ` ${record.covered_start_utc.slice(0, 10)} → ${record.covered_end_utc.slice(0, 10)}`
      : "";
  return `${vendorLabel} ${record.bar_count.toLocaleString()} bars${covered}`;
}

// Today's UTC calendar date (`YYYY-MM-DD`) — the value both "Today" shortcut buttons fill their
// date fields with. UTC (never the browser's local date) because every date field on this page is
// UTC-labelled and the backend parses them as UTC; using a local date would silently shift the
// window by a day for operators west of Greenwich late in the day.
function todayUtcDate(): string {
  return new Date().toISOString().slice(0, 10);
}

// The secondary (quieter) button styling used by the two "Today" shortcuts — the same shape as the
// page's primary Load/Fetch buttons, one step down in contrast so a shortcut never competes with
// the action it fills in for.
const SECONDARY_BUTTON_CLASS =
  "rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm font-medium text-slate-400 transition-colors hover:border-slate-600 hover:bg-slate-800 hover:text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-950";

// era-5B J-05 (THIS iteration): the Case Studies reaction filter's <select> options — mirrors
// `research/setups.py`'s own config-owned, pre-registered `REJECTED`/`BROKE`/`CHOPPED` constants
// (route-level enforced by `routes.py`'s `_VALID_REACTIONS`). The SAME `YAHOO_TIMEFRAMES` display-
// choice precedent immediately above: a courtesy option list, never a second validation authority
// — an out-of-set value would still 422 server-side (this page never sends one; the filter is
// applied client-side over the already-served, unfiltered event list — see `handleSetupsFilter*`).
const SETUP_REACTIONS = ["rejected", "broke", "chopped"];

// The Case Studies section (era-5B J-02/J-03 touch-event registry + drill-in) is suppressed from
// the Structure page — flip to `true` to bring it back. Typed as `boolean` (not the `false` literal)
// so the render-time gate below is a normal conditional, not narrowed to dead code. All Case Studies
// state/handlers are kept intact; only its rendered section is withheld.
const SHOW_CASE_STUDIES: boolean = false;

type LoadState<T> =
  | { phase: "idle" }
  | { phase: "loading" }
  | { phase: "error"; message: string }
  | { phase: "ready"; data: T };

// The explicit degraded state (the NavBar/UnavailablePanel pattern): honestly no data — never
// cached or fabricated content in its place.
function UnavailablePanel({ testid, message }: { testid: string; message: string }) {
  return (
    <div
      data-testid={testid}
      className="rounded-lg border border-amber-800/60 bg-amber-900/20 px-4 py-6 text-center"
    >
      <p className="text-sm font-medium text-amber-300">{message}</p>
      <p className="mt-1 text-xs text-amber-200/70">
        Nothing cached and nothing fabricated is shown in its place.
      </p>
    </div>
  );
}

// A quiet loading placeholder (no fabricated values — just a pulse block).
function LoadingPanel({ testid }: { testid: string }) {
  return (
    <div
      data-testid={testid}
      className="animate-pulse rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-6"
    >
      <div className="h-3 w-1/3 rounded bg-slate-800" />
      <div className="mt-3 h-3 w-2/3 rounded bg-slate-800" />
      <div className="mt-3 h-3 w-1/2 rounded bg-slate-800" />
    </div>
  );
}

// The honest not-computed state (era-fast_wall J-01): a cold cache with a non-empty registry —
// distinct from `UnavailablePanel` (a fetch/backend failure) and `EmptyState` (a genuinely
// computed, empty result). Reuses `UnavailablePanel`'s amber degraded-state treatment (no new
// visual language) with its own testid + its own headline/detail copy; `detail` is the backend's
// OWN trigger explanation, rendered verbatim — never a frontend-authored string.
//
// era-fast_wall J-04: gains the "Compute edge report" button + live progress line + failed-state
// render. `compute` (the live/last snapshot, kept fresh by the poll effect in `StructurePage`)
// drives five states: idle (button enabled, no progress line), running (button shows "Computing…"
// and is disabled; a pulsing dot, the done/total counts, the CURRENT dataset x strategy pair, a
// live elapsed clock, and a Cancel button all render — the user can always see the job is alive),
// done (this panel is no longer rendered — the parent swaps to `EdgeReportBody` once the
// re-fetched report loses its `not_computed` status), cancelled (explicit copy — completed
// backtests stay banked in the durable per-pair cache, so a re-run resumes), and failed (the
// snapshot's `error` renders verbatim, button re-enabled reading "Retry compute").
// `triggerError` is a SEPARATE, POST-specific failure (e.g. backend unreachable at click time) —
// distinct from a `failed` compute job, which is a server-side outcome of a job that DID start.
// The current pair's dataset id resolves to its symbol via the ALREADY-FETCHED registry rows (a
// pure lookup of served values — nothing recomputed); the elapsed clock derives from the
// snapshot's own `started_utc` at render time (the 700ms poll re-renders it — display only,
// never a research value).
function formatComputeElapsed(startedUtc: string | null): string | null {
  if (!startedUtc) return null;
  const ms = Date.now() - Date.parse(startedUtc);
  if (!Number.isFinite(ms) || ms < 0) return null;
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  return m > 0 ? `${m}m ${String(s % 60).padStart(2, "0")}s` : `${s}s`;
}

function NotComputedPanel({
  detail,
  compute,
  datasets,
  onTriggerCompute,
  triggering,
  triggerError,
  onCancelCompute,
  cancelRequested,
  cancelError,
}: {
  detail: string;
  compute: EdgeReportComputeSnapshot | null;
  datasets: Dataset[];
  onTriggerCompute: () => void;
  triggering: boolean;
  triggerError: string | null;
  onCancelCompute: () => void;
  cancelRequested: boolean;
  cancelError: string | null;
}) {
  const isRunning = compute?.state === "running";
  const isFailed = compute?.state === "failed";
  const isCancelled = compute?.state === "cancelled";
  const buttonLabel = isRunning ? "Computing…" : isFailed ? "Retry compute" : "Compute edge report";
  const current = isRunning ? compute.progress.current : null;
  const currentSymbol = current
    ? datasets.find((d) => d.id === current.dataset_id)?.symbol ?? current.dataset_id.slice(0, 8)
    : null;
  const elapsed = isRunning ? formatComputeElapsed(compute.started_utc) : null;
  return (
    <div
      data-testid="edge-report-not-computed"
      className="rounded-lg border border-amber-800/60 bg-amber-900/20 px-4 py-6 text-center"
    >
      <p className="text-sm font-medium text-amber-300">Edge report not computed yet.</p>
      <p className="mt-1 text-xs text-amber-200/70">{detail}</p>
      {isFailed && compute?.error && (
        <p data-testid="edge-report-compute-error" className="mt-2 text-xs text-red-300">
          {compute.error}
        </p>
      )}
      {triggerError && (
        <p data-testid="edge-report-compute-trigger-error" className="mt-2 text-xs text-red-300">
          {triggerError}
        </p>
      )}
      {isCancelled && (
        <p data-testid="edge-report-compute-cancelled" className="mt-2 text-xs text-amber-200/70">
          Compute cancelled — nothing was published this run; already-completed backtests are
          banked in the durable cache, so the next run resumes from them.
        </p>
      )}
      <button
        type="button"
        data-testid="edge-report-compute-button"
        onClick={onTriggerCompute}
        disabled={triggering || isRunning}
        className="mt-3 rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:border-slate-500 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-600 disabled:hover:bg-slate-800"
      >
        {buttonLabel}
      </button>
      {isRunning && (
        <div data-testid="edge-report-compute-running" className="mt-2 flex flex-col items-center gap-1">
          <p data-testid="edge-report-compute-progress" className="text-xs text-amber-200/70">
            <span
              aria-hidden="true"
              className="mr-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400 align-middle"
            />
            {compute.progress.backtests_done} / {compute.progress.backtests_total} backtests
            {compute.progress.backtests_from_cache > 0
              ? ` (${compute.progress.backtests_from_cache} from cache)`
              : ""}
            {elapsed && (
              <span data-testid="edge-report-compute-elapsed"> · running {elapsed}</span>
            )}
          </p>
          {current && (
            <p data-testid="edge-report-compute-current" className="text-xs text-amber-200/70">
              current: {currentSymbol} × {current.strategy_id}
            </p>
          )}
          <button
            type="button"
            data-testid="edge-report-compute-cancel"
            onClick={onCancelCompute}
            disabled={cancelRequested}
            className="mt-1 rounded-md border border-slate-700 bg-transparent px-2.5 py-1 text-xs font-medium text-slate-400 transition-colors hover:border-slate-500 hover:text-slate-200 focus:outline-none focus:ring-1 focus:ring-red-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {cancelRequested ? "Cancelling — finishing the current backtest…" : "Cancel compute"}
          </button>
          {cancelError && (
            <p data-testid="edge-report-compute-cancel-error" className="text-xs text-red-300">
              {cancelError}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// A distinct, honest empty state — its own testid + its own copy every time (never shared, per
// the interlude's honest-state anti-goal).
function EmptyState({
  testid,
  title,
  detail,
}: {
  testid: string;
  title: string;
  detail?: string;
}) {
  return (
    <div
      data-testid={testid}
      className="flex min-h-[20vh] flex-col items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-10 text-center"
    >
      <span className="text-2xl text-slate-700">∅</span>
      <p className="mt-2 text-sm text-slate-500">{title}</p>
      {detail && <p className="mt-1 text-xs text-slate-600">{detail}</p>}
    </div>
  );
}

// One confluence zone: the A/B/C badge + score (verbatim), then its member levels (price +
// timeframe + type, verbatim) — one row per `confluence_zones[]` entry, per the DoD.
function ZoneRow({ zone, index }: { zone: ConfluenceZone; index: number }) {
  return (
    <article
      data-testid="zone-row"
      data-zone-class={zone.class}
      className="rounded-lg border border-slate-800 bg-slate-900/60 p-3"
    >
      <header className="mb-2 flex flex-wrap items-center gap-2">
        <span
          data-testid="zone-class-badge"
          className="inline-block rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[11px] font-semibold text-slate-300"
        >
          Class {zone.class}
        </span>
        <span className="text-xs text-slate-500">
          zone {index + 1} · score{" "}
          <span data-testid="zone-score" className="font-mono text-slate-300">
            {String(zone.score)}
          </span>
        </span>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-slate-800">
              <th className={HEADER_CELL}>price</th>
              <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">
                timeframe
              </th>
              <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">type</th>
            </tr>
          </thead>
          <tbody>
            {zone.levels.map((lvl, i) => (
              <tr
                key={i}
                data-testid="zone-member-level"
                className="border-b border-slate-800/60 last:border-b-0"
              >
                <td className={NUMERIC_CELL}>{String(lvl.price)}</td>
                <td className={LABEL_CELL}>{lvl.timeframe}</td>
                <td className={LABEL_CELL}>{lvl.type}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}

// --- Tradable Map section (era-5B J-01, THIS iteration's new default view) ----------------------

// One tradable band row: side, range, inherited class, quality score, member count, round-number
// flag — every value `String(...)`-rendered verbatim off the prop (the `ZoneRow` precedent).
// `class: null` renders an honest "Unclassified" label — never a fabricated grade (a band with no
// overlapping confluence zone genuinely has none; `levels.py` alone owns A/B/C).
function BandRow({ band }: { band: TradabilityBand }) {
  return (
    <tr
      data-testid="tradable-band-row"
      data-band-side={band.side}
      className="border-b border-slate-800/60 last:border-b-0"
    >
      <td className={LABEL_CELL}>{band.side}</td>
      <td className={NUMERIC_CELL} data-testid="tradable-band-range">
        {String(band.price_low)}–{String(band.price_high)}
      </td>
      <td className={LABEL_CELL} data-testid="tradable-band-class">
        {band.class !== null ? `Class ${band.class}` : "Unclassified"}
      </td>
      <td className={NUMERIC_CELL} data-testid="tradable-band-score">
        {String(band.quality_score)}
      </td>
      <td className={NUMERIC_CELL}>{String(band.member_count)}</td>
      <td className="px-2 py-1.5 text-left">
        {band.round_number && (
          <span
            data-testid="tradable-band-round-number"
            className="inline-block whitespace-nowrap rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[11px] text-slate-300"
          >
            round number
          </span>
        )}
      </td>
    </tr>
  );
}

// The bands table (range/side/quality-score/class/member-count/round-number — the DoD's exact
// column list). `bands` is rendered in the endpoint's OWN served order (side, then descending
// quality score — never re-sorted here).
function BandsTable({ bands }: { bands: TradabilityBand[] }) {
  return (
    <div className="overflow-x-auto">
      <table data-testid="tradable-map-table" className="w-full border-collapse">
        <thead>
          <tr className="border-b border-slate-800">
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">side</th>
            <th className={HEADER_CELL}>range</th>
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">class</th>
            <th className={HEADER_CELL}>score</th>
            <th className={HEADER_CELL}>members</th>
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500" />
          </tr>
        </thead>
        <tbody>
          {bands.map((band, i) => (
            <BandRow key={i} band={band} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

// --- Case Studies section (era-5B J-02/J-03, THIS iteration) -------------------------------------

// Every configured forward-return horizon rendered verbatim (horizon_bars + the RAW
// return_fraction — never a client-side percentage conversion or rounding). `return_fraction:
// null` renders an honest "—" (that horizon reaches past the end of the stored series; never a
// fabricated number).
function ForwardReturnsList({ forwardReturns }: { forwardReturns: SetupEvent["forward_returns"] }) {
  return (
    <span data-testid="case-forward-returns" className="font-mono text-xs text-slate-300">
      {forwardReturns.map((fr, i) => (
        <span key={fr.horizon_bars} className="whitespace-nowrap">
          {i > 0 && " · "}
          {String(fr.horizon_bars)}b: {fr.return_fraction === null ? "—" : String(fr.return_fraction)}
        </span>
      ))}
    </span>
  );
}

// One case-registry row: symbol, session date, band range/side/class, reaction, forward returns —
// the DoD's exact column list. Clicking anywhere on the row opens the drill-in below the table.
function SetupRow({
  event,
  selected,
  onSelect,
}: {
  event: SetupEvent;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <tr
      data-testid="case-studies-row"
      data-reaction={event.reaction}
      onClick={onSelect}
      aria-selected={selected}
      className={`cursor-pointer border-b border-slate-800/60 last:border-b-0 hover:bg-slate-800/40 ${
        selected ? "bg-slate-800/60" : ""
      }`}
    >
      <td className={LABEL_CELL}>{event.symbol}</td>
      <td className={LABEL_CELL}>{event.session_date}</td>
      <td className={LABEL_CELL}>
        {event.band.side} · {String(event.band.price_low)}–{String(event.band.price_high)} ·{" "}
        {event.band.class !== null ? `Class ${event.band.class}` : "Unclassified"}
      </td>
      <td className={LABEL_CELL} data-testid="case-studies-row-reaction">
        {event.reaction}
        {event.reaction_boundary_truncated && (
          <span
            data-testid="case-studies-row-boundary-flag"
            className="ml-1 inline-block whitespace-nowrap rounded border border-amber-800/60 bg-amber-900/20 px-1 py-0.5 text-[10px] text-amber-300"
          >
            truncated horizon
          </span>
        )}
      </td>
      <td className="px-2 py-1.5 text-left">
        <ForwardReturnsList forwardReturns={event.forward_returns} />
      </td>
    </tr>
  );
}

// The tape-at-the-wall timeline (era-5B J-03) — a list of state-transition entries, or an honest
// "no recorded tape" empty state (distinct from a populated list — never silently omitted).
function TapeTimelineList({ timeline }: { timeline: SetupEvent["tape_timeline"] }) {
  if (timeline.length === 0) {
    return (
      <p data-testid="case-drillin-tape-timeline-empty" className="text-xs text-slate-600">
        No recorded tape for this event.
      </p>
    );
  }
  return (
    <ol data-testid="case-drillin-tape-timeline" className="space-y-1">
      {timeline.map((entry, i) => (
        <li
          key={i}
          data-testid="case-drillin-tape-timeline-entry"
          className="flex items-baseline justify-between gap-2 font-mono text-xs text-slate-300"
        >
          <span className="text-slate-500">{entry.timestamp ?? "—"}</span>
          <span>{entry.state}</span>
          <span className="text-slate-500">{String(entry.confidence)}</span>
        </li>
      ))}
    </ol>
  );
}

// The row drill-in: band, reaction (+ the honest recency-boundary disclosure), forward returns,
// and the tape timeline. Renders whichever `LoadState<SetupEvent>` phase is current — its own
// distinct loading/unavailable states, the page's established `LoadState<T>` pattern.
function SetupDrillIn({ state }: { state: LoadState<SetupEvent> }) {
  return (
    <Panel title="Case Studies — drill-in" className="mt-3">
      {state.phase === "loading" && <LoadingPanel testid="case-drillin-loading" />}
      {state.phase === "error" && (
        <UnavailablePanel testid="case-drillin-unavailable" message={state.message} />
      )}
      {state.phase === "ready" && (
        <div data-testid="case-drillin" className="space-y-3">
          <dl className="space-y-1.5">
            <div className="flex items-baseline justify-between gap-2">
              <dt className="text-xs text-slate-500">symbol / session</dt>
              <dd className="font-mono text-xs text-slate-200">
                {state.data.symbol} · {state.data.session_date}
              </dd>
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <dt className="text-xs text-slate-500">band</dt>
              <dd className="font-mono text-xs text-slate-200">
                {state.data.band.side} · {String(state.data.band.price_low)}–
                {String(state.data.band.price_high)} ·{" "}
                {state.data.band.class !== null ? `Class ${state.data.band.class}` : "Unclassified"}
              </dd>
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <dt className="text-xs text-slate-500">reaction</dt>
              <dd data-testid="case-drillin-reaction" className="font-mono text-xs text-slate-200">
                {state.data.reaction}
              </dd>
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <dt className="text-xs text-slate-500">forward returns</dt>
              <dd>
                <ForwardReturnsList forwardReturns={state.data.forward_returns} />
              </dd>
            </div>
          </dl>
          {state.data.reaction_boundary_truncated && (
            <p
              data-testid="case-drillin-boundary-note"
              className="rounded border border-amber-800/60 bg-amber-900/20 px-2 py-1.5 text-[11px] text-amber-200"
            >
              Reaction read at a truncated {String(state.data.effective_reaction_horizon_bars)}-bar
              horizon — the store does not yet hold the full configured horizon past this touch.
            </p>
          )}
          <div>
            <p className="mb-1 text-[11px] font-medium uppercase tracking-wider text-slate-500">
              Tape timeline
            </p>
            <TapeTimelineList timeline={state.data.tape_timeline} />
          </div>
        </div>
      )}
    </Panel>
  );
}

// --- Edge Report section (era-5B J-04, THIS iteration) --------------------------------------------

// One measurement's four headline numbers (n / net R / net $ / win_rate) — reuses
// `formatNullableAggregateField` (defined below, alongside the Comparison section) for the honest
// n=0 "no trades" reading; labeled "win_rate" (the literal field name, no space or hyphen) — the
// SAME copy-discipline precedent `BacktestResultBlock` already established on this page. A
// function DECLARATION (hoisted), so this forward reference is safe.
function EdgeReportMeasurementCells({ measurement }: { measurement: BacktestAggregate }) {
  return (
    <>
      <td className={NUMERIC_CELL}>{String(measurement.n)}</td>
      <td className={NUMERIC_CELL}>{String(measurement.net_r)}</td>
      <td className={NUMERIC_CELL}>{String(measurement.net_usd)}</td>
      <td className={NUMERIC_CELL}>{formatNullableAggregateField(measurement.win_rate)}</td>
    </>
  );
}

// One edge-report cell row: strategy × class × side × reaction × feed identity, then the
// measurement's headline numbers with `insufficient_sample` shown INLINE on the real numbers —
// never a separate hidden state (the `BacktestClassTable` precedent this page already
// established, copy included: `insufficient sample (n < ${minSampleSize})`).
function EdgeReportCellRow({
  cell,
  minSampleSize,
}: {
  cell: EdgeReportCell;
  minSampleSize: number;
}) {
  return (
    <tr data-testid="edge-report-cell-row" className="border-b border-slate-800/60 last:border-b-0">
      <td className={LABEL_CELL}>{cell.strategy_id}</td>
      <td className={LABEL_CELL}>Class {cell.band_class}</td>
      <td className={LABEL_CELL}>{cell.band_side}</td>
      <td className={LABEL_CELL}>{cell.reaction}</td>
      <td className={LABEL_CELL}>{cell.feed}</td>
      <EdgeReportMeasurementCells measurement={cell.measurement} />
      <td className="px-2 py-1.5 text-left">
        {cell.insufficient_sample ? (
          <span
            data-testid="edge-report-insufficient-sample"
            className="inline-block whitespace-nowrap rounded border border-amber-800/60 bg-amber-900/20 px-1.5 py-0.5 text-[11px] text-amber-300"
          >
            {`insufficient sample (n < ${minSampleSize})`}
          </span>
        ) : (
          <span className="text-[11px] text-slate-500">ok</span>
        )}
      </td>
    </tr>
  );
}

// One split's cells table (train or hold-out) — an EMPTY split is its own honest, first-class
// state (never hidden, never treated as an error): the DoD's own "an empty edge report is a
// valid, publishable outcome" clause, applied per-split.
function EdgeReportCellsTable({
  cells,
  minSampleSize,
  testid,
}: {
  cells: EdgeReportCell[];
  minSampleSize: number;
  testid: string;
}) {
  if (cells.length === 0) {
    return (
      <EmptyState
        testid={`${testid}-empty`}
        title="No cells in this split."
        detail="No recorded dataset resolved an owning, classified scan event for this split yet."
      />
    );
  }
  return (
    <div className="overflow-x-auto">
      <table data-testid={testid} className="w-full border-collapse">
        <thead>
          <tr className="border-b border-slate-800">
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">strategy</th>
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">class</th>
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">side</th>
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">reaction</th>
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">feed</th>
            <th className={HEADER_CELL}>n</th>
            <th className={HEADER_CELL}>net R</th>
            <th className={HEADER_CELL}>net $</th>
            <th className={HEADER_CELL}>win_rate</th>
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">sample</th>
          </tr>
        </thead>
        <tbody>
          {cells.map((cell, i) => (
            <EdgeReportCellRow key={i} cell={cell} minSampleSize={minSampleSize} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

// A ranked, informational list of TRAIN cells that clear the positivity gate, each paired with its
// own hold-out cell's status. This list promotes nothing — the champion pointer moves ONLY through
// the existing sweep gate on hold-out data (goal.md's own anti-goal); it is purely informational.
function SurvivingCellRow({ survivor }: { survivor: EdgeReportSurvivingCell }) {
  const cell = survivor.train_cell;
  return (
    <tr
      data-testid="edge-report-surviving-row"
      className="border-b border-slate-800/60 last:border-b-0"
    >
      <td className={LABEL_CELL}>{cell.strategy_id}</td>
      <td className={LABEL_CELL}>Class {cell.band_class}</td>
      <td className={LABEL_CELL}>{cell.band_side}</td>
      <td className={LABEL_CELL}>{cell.reaction}</td>
      <td className={LABEL_CELL}>{cell.feed}</td>
      <td className={NUMERIC_CELL}>{String(cell.measurement.net_r)}</td>
      <td className={LABEL_CELL} data-testid="edge-report-surviving-holdout-status">
        {survivor.holdout_cell === null
          ? "no hold-out data yet for this cell"
          : survivor.holdout_positive_edge
            ? "hold-out: clears the gate"
            : "hold-out: does not clear the gate"}
      </td>
    </tr>
  );
}

function SurvivingCellsTable({ survivors }: { survivors: EdgeReportSurvivingCell[] }) {
  if (survivors.length === 0) {
    return (
      <p data-testid="edge-report-surviving-empty" className="text-xs text-slate-600">
        No train cell currently clears the positivity gate.
      </p>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table data-testid="edge-report-surviving-table" className="w-full border-collapse">
        <thead>
          <tr className="border-b border-slate-800">
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">strategy</th>
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">class</th>
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">side</th>
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">reaction</th>
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">feed</th>
            <th className={HEADER_CELL}>train net R</th>
            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">
              hold-out status
            </th>
          </tr>
        </thead>
        <tbody>
          {survivors.map((s, i) => (
            <SurvivingCellRow key={i} survivor={s} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

// The full Edge Report body: the register + both splits' cell tables + the surviving-cells
// ranking. An all-empty report (train AND hold-out both carry zero cells) is its own distinct
// honest state — never hidden, never a fabricated survivor (goal.md's "no gate bending for a
// headline" anti-goal; the DoD's own "an empty edge report is a valid, publishable outcome").
function EdgeReportBody({ report }: { report: EdgeReportResponse }) {
  const isEmpty = report.train.cells.length === 0 && report.holdout.cells.length === 0;
  return (
    <div className="space-y-4">
      <p
        data-testid="edge-report-register"
        className="rounded border border-amber-800/60 bg-amber-900/20 px-2 py-1.5 text-[11px] text-amber-200"
      >
        {report.register}
      </p>
      {isEmpty ? (
        <EmptyState
          testid="edge-report-empty"
          title="No edge-report cells yet."
          detail="No recorded dataset has resolved an owning, classified scan event — an honest, valid outcome, never hidden."
        />
      ) : (
        <>
          <div>
            <p className="mb-1 text-[11px] font-medium uppercase tracking-wider text-slate-500">
              Train
            </p>
            <EdgeReportCellsTable
              cells={report.train.cells}
              minSampleSize={report.pnl_min_sample_size}
              testid="edge-report-train-table"
            />
          </div>
          <div>
            <p className="mb-1 text-[11px] font-medium uppercase tracking-wider text-slate-500">
              Hold-out
            </p>
            <EdgeReportCellsTable
              cells={report.holdout.cells}
              minSampleSize={report.pnl_min_sample_size}
              testid="edge-report-holdout-table"
            />
          </div>
          <div>
            <p className="mb-1 text-[11px] font-medium uppercase tracking-wider text-slate-500">
              Surviving train cells (informational — never a promotion)
            </p>
            <SurvivingCellsTable survivors={report.surviving_train_cells} />
          </div>
        </>
      )}
    </div>
  );
}

// --- Registry section (J-02) ---------------------------------------------------------------------

// The exit-precedence caption is prose framing describing the runner's general exit-check order
// (goal.md / the phase spec's own phrase), NOT a literal field read out of the JSON — v1's `exits`
// object has no `reward_target` key at all, and neither strategy's raw dict key order matches this
// phrase exactly. Each exit field below still renders its OWN actual value verbatim; this caption
// only explains the fixed display order chosen for them.
const EXIT_PRECEDENCE_CAPTION =
  "Exit precedence: r_stop → reward_target → state_flip → horizon (dataset_end forces a close at stream end).";

// One class-scaled map (`stop_bps_by_class` / `r_multiple_by_class` / `size_multiple_by_class`), a
// small table of class -> value. Rows render in the SAME key order the payload itself carries
// (Object.entries — never re-sorted, never assumed to be exactly A/B/C: an unrecognized class key
// still renders, the SAME tolerance `SrLevel.type` already established for this page).
function ClassMapTable({
  label,
  testid,
  map,
}: {
  label: string;
  testid: string;
  map: Record<string, number>;
}) {
  return (
    <div data-testid={testid} className="mt-2">
      <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">{label}</p>
      <table className="mt-1 w-full border-collapse">
        <tbody>
          {Object.entries(map).map(([cls, value]) => (
            <tr key={cls} className="border-b border-slate-800/60 last:border-b-0">
              <td className={LABEL_CELL}>{cls}</td>
              <td className={NUMERIC_CELL}>{String(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// One registered strategy: entry rule, the exit fields in the caption's fixed order, then (only
// where the payload itself carries them — never assumed by strategy_id) the three class-scaled
// maps. Every value is `String(...)`-rendered verbatim from the prop, the page's established
// precedent (matching `ZoneRow`'s `String(zone.score)` / `String(lvl.price)`).
function StrategyCard({ strategy }: { strategy: Strategy }) {
  const { exits } = strategy;
  return (
    <article
      data-testid="strategy-card"
      data-strategy-id={strategy.strategy_id}
      className="rounded-lg border border-slate-800 bg-slate-900/60 p-4"
    >
      <header className="mb-3">
        <h3 className="font-mono text-sm font-semibold text-slate-200">
          {String(strategy.strategy_id)}
        </h3>
      </header>

      <dl className="space-y-1.5">
        <div className="flex items-baseline justify-between gap-2">
          <dt className="text-xs text-slate-500">entry rule</dt>
          <dd data-testid="strategy-entry-rule" className="font-mono text-xs text-slate-200">
            {String(strategy.entries.rule)}
          </dd>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <dt className="text-xs text-slate-500">r_stop</dt>
          <dd data-testid="strategy-exit-r-stop" className="font-mono text-xs text-slate-200">
            {String(exits.r_stop.rule)}
          </dd>
        </div>
        {exits.reward_target && (
          <div className="flex items-baseline justify-between gap-2">
            <dt className="text-xs text-slate-500">reward_target</dt>
            <dd
              data-testid="strategy-exit-reward-target"
              className="font-mono text-xs text-slate-200"
            >
              {String(exits.reward_target.rule)}
            </dd>
          </div>
        )}
        <div className="flex items-baseline justify-between gap-2">
          <dt className="text-xs text-slate-500">state_flip</dt>
          <dd data-testid="strategy-exit-state-flip" className="font-mono text-xs text-slate-200">
            {String(exits.state_flip.rule)}
          </dd>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <dt className="text-xs text-slate-500">horizon (seconds)</dt>
          <dd data-testid="strategy-exit-horizon" className="font-mono text-xs text-slate-200">
            {String(exits.horizon_seconds)}
          </dd>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <dt className="text-xs text-slate-500">dataset_end</dt>
          <dd
            data-testid="strategy-exit-dataset-end"
            className="font-mono text-xs text-slate-200"
          >
            {String(exits.dataset_end.rule)}
          </dd>
        </div>
      </dl>

      <p className="mt-2 text-[11px] text-slate-600">{EXIT_PRECEDENCE_CAPTION}</p>

      {exits.r_stop.stop_bps_by_class && (
        <ClassMapTable
          label="stop (bps by class)"
          testid="strategy-stop-bps-by-class"
          map={exits.r_stop.stop_bps_by_class}
        />
      )}
      {exits.reward_target && exits.reward_target.r_multiple_by_class && (
        <ClassMapTable
          label="reward target (R-multiple by class)"
          testid="strategy-r-multiple-by-class"
          map={exits.reward_target.r_multiple_by_class}
        />
      )}
      {strategy.size_multiple_by_class && (
        <ClassMapTable
          label="size (multiple by class)"
          testid="strategy-size-multiple-by-class"
          map={strategy.size_multiple_by_class}
        />
      )}
    </article>
  );
}

// Deep-equal over the small flat `{strategy_id, profile}` champion shape only (no generic deep-
// equal utility needed for two known string fields) — used ONLY to narrate agreement/disagreement
// between the two endpoints that share one store source; it never picks a value (no "champion
// resolution" — the anti-goal this interlude names explicitly).
function championsMatch(
  a: { strategy_id: string; profile: string },
  b: { strategy_id: string; profile: string },
): boolean {
  return a.strategy_id === b.strategy_id && a.profile === b.profile;
}

// --- Comparison section (J-03) --------------------------------------------------------------------

// The per-class (A/B/C) breakdown table from `result.aggregates_by_class` — a SIBLING to
// `ClassMapTable` (J-02), not a reuse of it: that table's value is a single number per class,
// while this one is a whole aggregate object (n/net_r/net_usd/insufficient_sample) per class, so
// force-fitting `ClassMapTable` would lose fields rather than share real structure. Rows render via
// `Object.entries()` in the payload's own key order (never re-sorted, never assumed to be exactly
// {A,B,C}) — the SAME tolerance `ClassMapTable`/`SrLevel.type` already established on this page.
// `insufficient_sample` is shown INLINE on the real numbers — never as a separate state (per the
// interlude's own T10 anti-goal: no derived/fabricated "non-survivor" boolean anywhere here).
function BacktestClassTable({
  byClass,
  testid,
  minSampleSize,
}: {
  byClass: Record<string, BacktestClassAggregate>;
  testid: string;
  minSampleSize: number | null;
}) {
  return (
    <div data-testid={testid}>
      <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
        Per-class (A/B/C)
      </p>
      <div className="overflow-x-auto">
        <table className="mt-1 w-full border-collapse">
          <thead>
            <tr className="border-b border-slate-800">
              <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">class</th>
              <th className={HEADER_CELL}>n</th>
              <th className={HEADER_CELL}>net R</th>
              <th className={HEADER_CELL}>net $</th>
              <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">sample</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(byClass).map(([cls, agg]) => (
              <tr
                key={cls}
                data-testid="comparison-class-row"
                data-class={cls}
                className="border-b border-slate-800/60 last:border-b-0"
              >
                <td className={LABEL_CELL}>Class {cls}</td>
                <td className={NUMERIC_CELL}>{String(agg.n)}</td>
                <td className={NUMERIC_CELL}>{String(agg.net_r)}</td>
                <td className={NUMERIC_CELL}>{String(agg.net_usd)}</td>
                <td className="px-2 py-1.5 text-left">
                  {agg.insufficient_sample ? (
                    <span
                      data-testid="comparison-insufficient-sample"
                      className="inline-block whitespace-nowrap rounded border border-amber-800/60 bg-amber-900/20 px-1.5 py-0.5 text-[11px] text-amber-300"
                    >
                      {minSampleSize === null
                        ? "insufficient sample"
                        : `insufficient sample (n < ${minSampleSize})`}
                    </span>
                  ) : (
                    <span className="text-[11px] text-slate-500">ok</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// An honest `null` win_rate/max_drawdown_r is n=0 (`_aggregate()` — never a fabricated 0); this
// names the reason inline rather than a bare dash, matching the codebase's evidence-attached copy.
function formatNullableAggregateField(value: number | null): string {
  return value === null ? "no trades (n=0)" : String(value);
}

// One strategy's terminal result: the blended aggregates, the per-class table, and the simulated
// register — every value `String(...)`-rendered verbatim from `result` (zero client arithmetic).
function BacktestResultBlock({
  result,
  testid,
  minSampleSize,
}: {
  result: BacktestResult;
  testid: string;
  minSampleSize: number | null;
}) {
  const agg = result.aggregates;
  return (
    <div className="space-y-3">
      <dl className="space-y-1.5">
        <div className="flex items-baseline justify-between gap-2">
          <dt className="text-xs text-slate-500">n</dt>
          <dd data-testid={`${testid}-n`} className="font-mono text-xs text-slate-200">
            {String(agg.n)}
          </dd>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <dt className="text-xs text-slate-500">net R</dt>
          <dd data-testid={`${testid}-net-r`} className="font-mono text-xs text-slate-200">
            {String(agg.net_r)}
          </dd>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <dt className="text-xs text-slate-500">net $</dt>
          <dd data-testid={`${testid}-net-usd`} className="font-mono text-xs text-slate-200">
            {String(agg.net_usd)}
          </dd>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          {/* Labeled with the raw payload field name (matching this file's own StrategyCard
              precedent of "r_stop"/"reward_target"/"state_flip"/"dataset_end") — ALSO required so
              this stays clear of the backend's J-66 copy-discipline lint, which bans a bare
              "win rate"/"win-rate" phrase (a positive edge/certainty claim) in frontend source;
              "win_rate" (the literal field name, no space or hyphen) is unaffected. */}
          <dt className="text-xs text-slate-500">win_rate</dt>
          <dd data-testid={`${testid}-win_rate`} className="font-mono text-xs text-slate-200">
            {formatNullableAggregateField(agg.win_rate)}
          </dd>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <dt className="text-xs text-slate-500">max drawdown (R)</dt>
          <dd data-testid={`${testid}-max-drawdown-r`} className="font-mono text-xs text-slate-200">
            {formatNullableAggregateField(agg.max_drawdown_r)}
          </dd>
        </div>
      </dl>

      <BacktestClassTable
        byClass={result.aggregates_by_class}
        testid={`${testid}-class-table`}
        minSampleSize={minSampleSize}
      />

      <p
        data-testid={`${testid}-register`}
        className="rounded border border-amber-800/60 bg-amber-900/20 px-2 py-1.5 text-[11px] text-amber-200"
      >
        {result.register}
      </p>
    </div>
  );
}

// One side of the comparison (`v1` or `structure_tape`): renders whichever of the five honest
// states this backtest is currently in. `backtest === null` means "Run comparison" has not been
// clicked yet for this side. A `cancelled` backtest renders its OWN distinct copy — it carries NO
// result at all (`backtests.py`'s own docstring), unlike a Study's cancelled-but-partial results,
// so this is intentionally NOT a reuse of `StudyResultsView`'s `results-cancelled` copy.
function BacktestPanel({
  label,
  backtest,
  testid,
  minSampleSize,
}: {
  label: string;
  backtest: Backtest | null;
  testid: string;
  minSampleSize: number | null;
}) {
  return (
    <div
      data-testid={testid}
      data-status={backtest?.status ?? "not_started"}
      className="rounded-lg border border-slate-800 bg-slate-900/60 p-4"
    >
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</h3>
      {backtest === null && <LoadingPanel testid={`${testid}-loading`} />}
      {backtest && (backtest.status === "queued" || backtest.status === "running") && (
        <div
          data-testid={`${testid}-in-progress`}
          className="rounded-md border border-slate-800 bg-slate-950/40 px-3 py-3 text-sm text-slate-400"
        >
          {backtest.status === "queued" ? "Queued…" : "Running…"}
          {backtest.status === "running" && backtest.events_processed != null && (
            <span className="ml-2 font-mono text-amber-300">
              {backtest.events_processed} events processed
            </span>
          )}
        </div>
      )}
      {backtest && backtest.status === "failed" && (
        <div
          data-testid={`${testid}-failed`}
          role="alert"
          className="rounded-md border border-rose-700/70 bg-rose-900/30 px-3 py-2 text-sm text-rose-200"
        >
          This backtest could not produce a result. The explicit reason is shown — never an empty
          success.
          {backtest.error && (
            <p className="mt-1 font-mono text-xs text-rose-300/90">{backtest.error}</p>
          )}
        </div>
      )}
      {backtest && backtest.status === "cancelled" && (
        <div
          data-testid={`${testid}-cancelled`}
          className="rounded-md border border-slate-700 bg-slate-800/40 px-3 py-2 text-xs text-slate-300"
        >
          This backtest was cancelled before it finished. A partial simulated result is never
          served — no result is shown.
        </div>
      )}
      {backtest && backtest.status === "done" && backtest.result && (
        <BacktestResultBlock result={backtest.result} testid={testid} minSampleSize={minSampleSize} />
      )}
    </div>
  );
}

export default function StructurePage() {
  const [symbolInput, setSymbolInput] = useState("");
  const [asOfInput, setAsOfInput] = useState("");
  const [levelsState, setLevelsState] = useState<LoadState<LevelsResponse>>({ phase: "idle" });
  // The raw-levels toggle (era-5B J-05) — OFF by default (the DoD's own requirement); toggling it
  // on renders the pre-existing Levels & Zones section byte-identically to before this iteration.
  const [showRawLevels, setShowRawLevels] = useState(false);
  // The query the Load button last submitted — the ONE driver of this page's per-symbol reads.
  // `null` until the first Load; `seq` increments per click so a re-Load of the SAME
  // (symbol, asOf) still refetches (the store may have changed underneath — e.g. right after a
  // "Fetch from Yahoo Finance" recorded new bars; the hooks key on it as their reloadSeq).
  const [loadedQuery, setLoadedQuery] = useState<{
    symbol: string;
    asOf: string;
    seq: number;
  } | null>(null);
  // The query the DEFERRED raw-levels read has already been ISSUED for (`symbol|as_of|seq`). A
  // ref, not state: it exists only to keep the effect below from re-issuing the same read —
  // including after a failure, where re-running on `levelsState` would loop — and must never
  // itself trigger a render.
  const levelsRequestedForRef = useRef<string | null>(null);

  // era-5B J-01 Tradable Map (the default view) + the recorded-series metadata behind the
  // timeframe selector — both now read through the SHARED hooks the cockpit's PriceChart uses
  // (`lib/useTradability.ts` / `lib/useRecordedSeries.ts`): one fetch path per read, one backend
  // route, one durable cache — an enhancement to either lands on both surfaces at once. Driven by
  // the SAME Load form/button (`handleLoad` publishes `loadedQuery`), never a second trigger.
  const tradabilityState = useTradability(
    loadedQuery?.symbol ?? null,
    loadedQuery?.asOf ?? null,
    loadedQuery?.seq ?? 0,
  );
  const barSeriesState = useRecordedSeries(loadedQuery?.symbol ?? null, loadedQuery?.seq ?? 0);
  // The viewing-timeframe selector (default "1d"). This is the user's PREFERENCE — the timeframe
  // actually drawn is `effectiveTimeframe` below, which falls back when the loaded symbol has no
  // series at this timeframe. It only chooses WHICH recorded series' candles both charts draw; it
  // never changes the as-of levels/bands (multi-timeframe backend aggregates).
  const [chartTimeframe, setChartTimeframe] = useState("1d");

  // era-5B J-02/J-03 Case Studies state — the FULL, unfiltered registry is fetched ONCE on mount
  // (the `strategiesResult`/`datasetsResult` null-then-resolved pattern below); the symbol/reaction
  // filters are applied CLIENT-SIDE over the already-served rows (a display filter of served rows,
  // the SAME `bar_series.filter` precedent this page already established — never a second
  // computation or a re-fetch per keystroke). `selectedSetupId`/`setupDetailState` drive the
  // row-click drill-in (its own independent fetch of `GET /research/setups/{id}`).
  const [setupsResult, setSetupsResult] = useState<{
    ok: boolean;
    events: SetupEvent[];
    error?: string;
  } | null>(null);
  const [setupsFilterSymbol, setSetupsFilterSymbol] = useState("");
  const [setupsFilterReaction, setSetupsFilterReaction] = useState("");
  const [selectedSetupId, setSelectedSetupId] = useState<string | null>(null);
  const [setupDetailState, setSetupDetailState] = useState<LoadState<SetupEvent>>({ phase: "idle" });

  // era-5B J-04 Edge Report state — fetched once on mount, the SAME null-then-resolved pattern.
  // era-fast_wall J-01: `data` is now the discriminated `EdgeReportPayload` union (a real report
  // or the honest not-computed shape) -- see the render branch below.
  const [edgeReportResult, setEdgeReportResult] = useState<{
    ok: boolean;
    data: EdgeReportPayload | null;
    error?: string;
  } | null>(null);

  // era-fast_wall J-04 — the operator-run edge-report compute. `computeSnapshot` is seeded from
  // the not-computed payload's own `compute` field on mount (see the mount effect below), so a
  // page load mid-job or post-terminal resumes the correct view without a spurious extra click;
  // the poll effect then keeps it fresh while `state === "running"`. `computeTriggerError` is the
  // POST's own failure (e.g. backend unreachable at click time) — distinct from a `failed` job.
  const [computeSnapshot, setComputeSnapshot] = useState<EdgeReportComputeSnapshot | null>(null);
  const [computeTriggering, setComputeTriggering] = useState(false);
  const [computeTriggerError, setComputeTriggerError] = useState<string | null>(null);
  // The cooperative cancel is observed BETWEEN backtests server-side, so after a successful POST
  // the job may stay `running` until the current pair finishes — `computeCancelRequested` keeps
  // the Cancel button honest ("Cancelling — finishing the current backtest…") until the poll
  // observes the terminal snapshot. Reset on every new trigger.
  const [computeCancelRequested, setComputeCancelRequested] = useState(false);
  const [computeCancelError, setComputeCancelError] = useState<string | null>(null);

  // J-05 fetch-control state — the page's ONE new explicit write action. Independent of
  // `symbolInput`/`asOfInput` above (the pre-existing read-only Load form) until a successful
  // fetch seeds them (see `handleFetchYahoo` below). era-5C: one click fetches all six timeframes,
  // so there is no timeframe input — `fetchResults` holds the per-timeframe outcome list (each
  // row's backend `detail` VERBATIM), and `fetchError` now fires ONLY when all six fail.
  const [fetchSymbolInput, setFetchSymbolInput] = useState("");
  const [fetchStartInput, setFetchStartInput] = useState("");
  const [fetchEndInput, setFetchEndInput] = useState("");
  const [fetchSubmitting, setFetchSubmitting] = useState(false);
  const [fetchResults, setFetchResults] = useState<FetchTimeframeOutcome[] | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // J-02 Registry section state — fetched once on mount, independent of the Levels & Zones Load
  // button (the registry and champion are populated even keyless). `null` = fetch in flight;
  // `{ok: false}` resolves to the explicit registry-unavailable state — mirrors
  // /performance/page.tsx's own null-then-resolved pattern byte-for-byte.
  const [strategiesResult, setStrategiesResult] = useState<{
    ok: boolean;
    strategies: StrategiesPayload | null;
    error?: string;
  } | null>(null);
  const [profilesResult, setProfilesResult] = useState<{
    ok: boolean;
    profiles: ProfilesPayload | null;
    error?: string;
  } | null>(null);

  // J-03 Comparison section state. `datasetsResult`/`ledgerResult` are fetched once on mount,
  // the SAME null-then-resolved pattern as `strategiesResult`/`profilesResult` above. The champion
  // badge in the Comparison section reuses `strategiesResult` — it is NEVER re-fetched.
  const [datasetsResult, setDatasetsResult] = useState<{
    ok: boolean;
    data: DatasetsListResult | null;
    error?: string;
  } | null>(null);
  const [ledgerResult, setLedgerResult] = useState<{
    ok: boolean;
    ledger: PnlLedger | null;
    error?: string;
  } | null>(null);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [comparisonSubmitting, setComparisonSubmitting] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);
  const [comparisonPollError, setComparisonPollError] = useState<string | null>(null);
  const [v1Backtest, setV1Backtest] = useState<Backtest | null>(null);
  const [structureTapeBacktest, setStructureTapeBacktest] = useState<Backtest | null>(null);

  useEffect(() => {
    let alive = true;
    fetchStrategies().then((result) => {
      if (alive) setStrategiesResult(result);
    });
    fetchProfiles().then((result) => {
      if (alive) setProfilesResult(result);
    });
    fetchDatasets().then((result) => {
      if (alive) setDatasetsResult(result);
    });
    fetchPnlLedger().then((result) => {
      if (alive) setLedgerResult(result);
    });
    // era-5B J-02/J-03: the full, UNFILTERED case-study registry — fetched once, filtered
    // client-side by `setupsFilterSymbol`/`setupsFilterReaction` below (never a per-keystroke
    // re-fetch).
    fetchSetups().then((result) => {
      if (alive) setSetupsResult({ ok: result.ok, events: result.data?.events ?? [], error: result.error });
    });
    // era-5B J-04: the 3-way edge report. era-fast_wall J-04: the not-computed payload's own
    // `compute` field seeds `computeSnapshot` on mount, so a page load mid-job or post-terminal
    // resumes the correct view without a spurious extra click (the poll effect below then keeps
    // it fresh while running).
    fetchEdgeReport().then((result) => {
      if (!alive) return;
      setEdgeReportResult(result);
      if (result.ok && result.data && result.data.status === "not_computed") {
        setComputeSnapshot(result.data.compute);
      }
    });
    return () => {
      alive = false;
    };
  }, []);

  // era-fast_wall J-04: poll the compute job's snapshot while it is running (mirrors the EXISTING
  // `needsPolling`/`setInterval(..., 700)` backtest-poll pattern above — reusing the PATTERN, not
  // the endpoint). Stops the moment `computeSnapshot.state` is no longer `"running"` (the effect
  // re-runs on every `computeSnapshot` change and simply declines to schedule a new interval).
  // The instant a tick observes `state === "done"`, the edge report is re-fetched exactly once so
  // the panel falls through to the pre-existing `EdgeReportBody` render — zero new report-
  // rendering code, the SAME "zero client recomputation" discipline every other section follows.
  useEffect(() => {
    if (computeSnapshot?.state !== "running") return;
    const handle = setInterval(async () => {
      const next = await fetchEdgeReportCompute();
      if (!next.ok) return; // an honest "couldn't reach the backend this tick" — keep polling
      setComputeSnapshot(next.data);
      if (next.data && next.data.state === "done") {
        const report = await fetchEdgeReport();
        setEdgeReportResult(report);
      }
    }, 700);
    return () => clearInterval(handle);
  }, [computeSnapshot]);

  // era-fast_wall J-04: POST the trigger, then seed the freshly-started (or already-running)
  // snapshot from the response so the poll effect above picks it up immediately.
  async function handleTriggerEdgeReportCompute() {
    setComputeTriggering(true);
    setComputeTriggerError(null);
    setComputeCancelRequested(false);
    setComputeCancelError(null);
    const result = await triggerEdgeReportCompute();
    setComputeTriggering(false);
    if (result.ok && result.data) {
      setComputeSnapshot(result.data.compute);
    } else {
      setComputeTriggerError(result.error ?? "The edge-report compute could not be started.");
    }
  }

  // era-fast_wall follow-up: the Cancel action beside the running progress line. On a successful
  // POST the button flips to its "Cancelling…" copy and stays disabled — the poll effect above is
  // the ONE observer that resolves the terminal `cancelled` snapshot (no client-side state
  // fabrication). A failed POST (409 idle / unreachable) re-enables the button and surfaces the
  // backend's own detail verbatim.
  async function handleCancelEdgeReportCompute() {
    setComputeCancelRequested(true);
    setComputeCancelError(null);
    const result = await cancelEdgeReportCompute();
    if (!result.ok) {
      setComputeCancelRequested(false);
      setComputeCancelError(result.error ?? "The compute could not be cancelled.");
    }
  }

  // era-5B J-02/J-03: fetch the drill-in whenever a Case Studies row is selected. Clears to
  // `{phase: "idle"}` when nothing is selected (e.g. never rendered — the drill-in Panel only
  // mounts once a row has been clicked, so "idle" is never actually shown, but keeps the state
  // machine total).
  useEffect(() => {
    if (selectedSetupId === null) {
      setSetupDetailState({ phase: "idle" });
      return;
    }
    let alive = true;
    setSetupDetailState({ phase: "loading" });
    fetchSetupDetail(selectedSetupId).then((result) => {
      if (!alive) return;
      setSetupDetailState(
        result.ok && result.data
          ? { phase: "ready", data: result.data.event }
          : { phase: "error", message: result.error ?? "The case-study event could not be loaded." },
      );
    });
    return () => {
      alive = false;
    };
  }, [selectedSetupId]);

  // Poll both backtests while EITHER is non-terminal (mirrors studies/page.tsx's
  // `setInterval(loadStudies, 700)` poll-while-active pattern, reusing the PATTERN not the
  // endpoint) and stop once BOTH reach a terminal status — not after either one alone. A poll
  // response of `null` for a side that is still non-terminal is an honest "couldn't reach the
  // backend this tick" — the last known status is kept and surfaced via `comparisonPollError`
  // rather than silently freezing forever with no diagnostic.
  useEffect(() => {
    if (!needsPolling(v1Backtest) && !needsPolling(structureTapeBacktest)) return;
    const handle = setInterval(async () => {
      const [nextV1, nextStructureTape] = await Promise.all([
        needsPolling(v1Backtest) ? fetchBacktest(v1Backtest!.id) : Promise.resolve(v1Backtest),
        needsPolling(structureTapeBacktest)
          ? fetchBacktest(structureTapeBacktest!.id)
          : Promise.resolve(structureTapeBacktest),
      ]);
      const v1Missed = needsPolling(v1Backtest) && !nextV1;
      const structureTapeMissed = needsPolling(structureTapeBacktest) && !nextStructureTape;
      setComparisonPollError(
        v1Missed || structureTapeMissed
          ? "Backend unreachable while polling — showing the last known status."
          : null,
      );
      if (nextV1) setV1Backtest(nextV1);
      if (nextStructureTape) setStructureTapeBacktest(nextStructureTape);
    }, 700);
    return () => clearInterval(handle);
  }, [v1Backtest, structureTapeBacktest]);

  function handleLoad(symbol: string, asOf: string) {
    const trimmedSymbol = symbol.trim();
    const trimmedAsOf = asOf.trim();
    if (!trimmedSymbol || !trimmedAsOf) return; // the Load button is already disabled in this case
    // Publishing `loadedQuery` is the WHOLE load action now: the shared `useTradability` /
    // `useRecordedSeries` hooks above key on it and issue the reads (the `seq` bump makes a
    // re-Load of the same query a genuine refetch — the store may have changed underneath). The
    // raw-levels read stays DEFERRED (see the effect below), so a Load never spends a full level
    // computation on a section that is hidden by default. `levelsState` still goes to `loading`
    // here so the section, if it IS open, shows its loading panel from the click rather than a
    // stale ready-state for the previous date.
    setLevelsState({ phase: "loading" });
    setLoadedQuery((previous) => ({
      symbol: trimmedSymbol,
      asOf: trimmedAsOf,
      seq: (previous?.seq ?? 0) + 1,
    }));
  }

  // The DEFERRED raw-levels read (GET /research/levels). The Levels & Zones section is OFF by
  // default and its every state — idle, loading, error, ready — renders only behind
  // `showRawLevels`, so fetching it on a Load spent a second full level computation on a section
  // nobody was looking at. It now runs when there IS a loaded query AND the section is open, which
  // is the SAME "a hidden surface must not spend requests" rule `levelsWindow` below already
  // applies to that section's candle paging — and only once the Tradable Map read has SETTLED
  // (ready or error): the map is the default view, and both reads run a backtest-grade level
  // computation server-side, so issuing them together would make each wait on the other rather
  // than showing the map sooner (the sequencing `handleLoad` itself used to enforce by publishing
  // the query last). Issued at most once per (query, open) pair — the seq-qualified ref guard
  // covers a failed read too, so an error is shown once rather than retried in a loop.
  useEffect(() => {
    if (!showRawLevels || !loadedQuery) return;
    if (tradabilityState.phase !== "ready" && tradabilityState.phase !== "error") return;
    const key = `${loadedQuery.symbol}|${loadedQuery.asOf}|${loadedQuery.seq}`;
    if (levelsRequestedForRef.current === key) return;
    levelsRequestedForRef.current = key;
    let alive = true;
    setLevelsState({ phase: "loading" });
    fetchLevels(loadedQuery.symbol, loadedQuery.asOf).then((result) => {
      if (!alive) return;
      setLevelsState(
        result.ok && result.data
          ? { phase: "ready", data: result.data }
          : { phase: "error", message: result.error ?? "The levels could not be loaded." },
      );
    });
    return () => {
      alive = false;
    };
  }, [showRawLevels, loadedQuery, tradabilityState.phase]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    handleLoad(symbolInput, asOfInput);
  }

  // J-05 (era-5C): the fetch control's submit — ONE click fetches ALL six Yahoo timeframes. The
  // backend endpoint stays single-timeframe, so this loops `YAHOO_TIMEFRAMES` sequentially issuing
  // one POST /research/bars per timeframe (store-first makes an already-recorded window free;
  // sequential is gentle on the vendor and lets each row's outcome land as it completes). Each
  // timeframe reports its OWN honest outcome (fetched/served `200`, content-duplicate `409`, or the
  // backend's distinct 422/503/504 detail VERBATIM) — a timeframe Yahoo cannot serve for this window
  // (e.g. 1m beyond retention) never masks the ones that did. After the loop, IF anything landed
  // (a fresh record OR an already-stored 409, both mean the data is on file), seed the read-only
  // Load form and run the EXISTING read path (`handleLoad`) once so Levels & Zones + the Tradable
  // Map render with ZERO new rendering code. Only if ALL six fail is `fetchError` set and load
  // skipped — nothing loaded, nothing fabricated.
  async function handleFetchYahoo() {
    const symbol = fetchSymbolInput.trim();
    const start = fetchStartInput.trim();
    const end = fetchEndInput.trim();
    if (!symbol || !start || !end) return; // the button is already disabled otherwise
    setFetchSubmitting(true);
    setFetchError(null);
    const results: FetchTimeframeOutcome[] = YAHOO_TIMEFRAMES.map((timeframe) => ({
      timeframe,
      state: "pending",
      message: "queued…",
    }));
    setFetchResults([...results]);
    let firstRecorded: BarSeriesRecord | null = null;
    let anyStored = false;
    for (let i = 0; i < YAHOO_TIMEFRAMES.length; i++) {
      const timeframe = YAHOO_TIMEFRAMES[i];
      results[i] = { timeframe, state: "pending", message: "fetching…" };
      setFetchResults([...results]);
      const result = await recordBarSeries({ symbol, timeframe, start, end });
      if (result.ok && result.bar_series) {
        if (!firstRecorded) firstRecorded = result.bar_series;
        // Yahoo caps intraday history (1m to the last 30 days, 5m to 60, 1h to 730), and says so in
        // `vendor_limit`. ONLY when a cap actually left the older part of the requested range
        // unfetched is the remainder asked of Alpaca — a second, separately-recorded series, so
        // each recording still names exactly one vendor. Nothing is inferred client-side: both the
        // trigger (`vendor_limit`) and the gap boundary (`covered_start_utc`) are the server's own.
        const deep = await fetchDeepHistoryGap(symbol, timeframe, start, result.bar_series);
        if (deep?.recorded) anyStored = true;
        results[i] = {
          timeframe,
          state: "ok",
          message: `${describeRecording(result.bar_series, "Yahoo")}${deep ? ` · ${deep.message}` : ""}`,
        };
      } else if (result.status === 409) {
        // Content-identical to a series already on file (a DIFFERENT window key) — the data exists;
        // same benign "already stored" treatment as populate_panel_bars.py's SKIP.
        anyStored = true;
        results[i] = {
          timeframe,
          state: "stored",
          message: result.error ?? "identical content already stored",
        };
      } else {
        // Yahoo served nothing at all (e.g. a 1m window entirely older than its 30-day retention —
        // its own 422 detail names the limit). The whole requested range is then asked of Alpaca,
        // which keeps intraday history for years.
        const deep = await fetchDeepHistoryGap(symbol, timeframe, start, null, end);
        if (deep?.recorded) {
          anyStored = true;
          if (!firstRecorded && deep.record) firstRecorded = deep.record;
        }
        results[i] = deep?.recorded
          ? {
              timeframe,
              state: "ok",
              message: `${deep.message} · Yahoo: ${result.error ?? "no data for this window"}`,
            }
          : {
              timeframe,
              state: "error",
              message: `${result.error ?? "The bar series could not be fetched."}${deep ? ` · ${deep.message}` : ""}`,
            };
      }
      setFetchResults([...results]);
    }
    setFetchSubmitting(false);
    if (!firstRecorded && !anyStored) {
      setFetchError(
        "All six timeframes failed — each one's own reason is listed above. Nothing was loaded, and nothing cached or fabricated is shown in its place.",
      );
      return;
    }
    const seedSymbol = firstRecorded ? firstRecorded.symbol : symbol.toUpperCase();
    const seedAsOf = endOfDayUtc(firstRecorded ? firstRecorded.window_end_utc : end);
    setSymbolInput(seedSymbol);
    setAsOfInput(seedAsOf);
    // Publishing the query IS the load now (the shared hooks fetch off it); the seq bump inside
    // guarantees a genuine refetch even when the seeded query equals the previous one — required
    // here, since the store just gained the recordings this very flow wrote.
    handleLoad(seedSymbol, seedAsOf);
  }

  // The deep-history leg of one timeframe's fetch. `yahooRecord` is what Yahoo just recorded (or
  // `null` when it served nothing at all, in which case `fallbackEnd` bounds the whole requested
  // range). Returns `null` when there is no gap to fill — the requested range was served in full,
  // so no second vendor is asked and no extra call is made.
  async function fetchDeepHistoryGap(
    symbol: string,
    timeframe: string,
    requestedStart: string,
    yahooRecord: BarSeriesRecord | null,
    fallbackEnd?: string,
  ): Promise<{ message: string; recorded: boolean; record?: BarSeriesRecord } | null> {
    // A gap exists only when the vendor's own retention cap ACTUALLY shortened the window — the
    // server says so in `vendor_limit`, and that is the only honest signal for it. Yahoo's first
    // bar simply falling later than the requested start is NOT a gap: a start date on a weekend or
    // a market holiday always does that, and treating it as one recorded a junk 1–2 day Alpaca
    // series (and burned a credentialed vendor call) on every fetch that began on a non-trading
    // day. `yahooRecord === null` — Yahoo served nothing at all for this timeframe — is a
    // different case entirely: the WHOLE requested range is then asked of Alpaca, bounded by
    // `fallbackEnd`.
    //
    // The gap ENDS where Yahoo's coverage begins — the server's own `covered_start_utc`, never a
    // client-side guess at what the vendor's cap must have been. The end date is inclusive, so
    // using that same UTC date overlaps Yahoo's first day by one day rather than risking a hole;
    // the merged bar read de-duplicates by timestamp.
    const gapEnd = yahooRecord
      ? yahooRecord.vendor_limit && yahooRecord.covered_start_utc
        ? yahooRecord.covered_start_utc.slice(0, 10)
        : undefined
      : fallbackEnd;
    if (!gapEnd || gapEnd <= requestedStart) return null;

    const deep = await recordBarSeries({
      symbol,
      timeframe,
      start: requestedStart,
      end: gapEnd,
      vendor: "alpaca",
    });
    if (deep.ok && deep.bar_series) {
      return {
        message: describeRecording(deep.bar_series, `Alpaca ${deep.bar_series.feed}`),
        recorded: true,
        record: deep.bar_series,
      };
    }
    if (deep.status === 409) {
      return { message: "Alpaca: identical content already stored", recorded: true };
    }
    return {
      message: `Alpaca (${requestedStart} → ${gapEnd}): ${deep.error ?? "not fetched"}`,
      recorded: false,
    };
  }

  function handleFetchSubmit(e: React.FormEvent) {
    e.preventDefault();
    handleFetchYahoo();
  }

  // J-03: start BOTH backtests (v1 + structure_tape, both profile=default) on the chosen dataset
  // via Promise.all (the plan's own grounding — never sequential, never one without the other).
  // Resets any prior run's state first so a re-run never shows a stale mix of an old and a new
  // result. If EITHER create call fails, nothing is shown as running (the other side's job may
  // still be executing server-side, but this view never displays a lone, unpaired result).
  async function handleRunComparison() {
    if (!selectedDatasetId) return;
    setComparisonSubmitting(true);
    setComparisonError(null);
    setComparisonPollError(null);
    setV1Backtest(null);
    setStructureTapeBacktest(null);
    const [v1Result, structureTapeResult] = await Promise.all([
      createBacktest({
        dataset_id: selectedDatasetId,
        strategy_id: STRATEGY_V1_ID,
        profile: COMPARISON_PROFILE,
      }),
      createBacktest({
        dataset_id: selectedDatasetId,
        strategy_id: STRATEGY_TAPE_ID,
        profile: COMPARISON_PROFILE,
      }),
    ]);
    setComparisonSubmitting(false);
    if (!v1Result.ok || !v1Result.backtest) {
      setComparisonError(v1Result.error ?? "The v1 backtest could not be started.");
      return;
    }
    if (!structureTapeResult.ok || !structureTapeResult.backtest) {
      setComparisonError(
        structureTapeResult.error ?? "The structure_tape backtest could not be started.",
      );
      return;
    }
    setV1Backtest(v1Result.backtest);
    setStructureTapeBacktest(structureTapeResult.backtest);
  }

  function handleComparisonSubmit(e: React.FormEvent) {
    e.preventDefault();
    handleRunComparison();
  }

  const canSubmit = symbolInput.trim() !== "" && asOfInput.trim() !== "";
  const canFetch =
    fetchSymbolInput.trim() !== "" &&
    fetchStartInput.trim() !== "" &&
    fetchEndInput.trim() !== "";
  const levels = levelsState.phase === "ready" ? levelsState.data : null;
  const tradability = tradabilityState.phase === "ready" ? tradabilityState.data : null;

  // --- Shared viewing-timeframe derivation (ONE <select> governs BOTH charts below) --------------
  // Available timeframes = the loaded symbol's recorded series. The EFFECTIVE (drawn) timeframe is
  // the user's `chartTimeframe` if recorded, else "1d" if recorded, else the shortest recorded — so
  // the <select> never offers a dead option and the chart is never unexpectedly empty for a symbol
  // that HAS bars. "" only when the symbol has no series at all (each chart branch already gates
  // that behind its own no-bar-series empty state).
  const loadedSymbol = tradability?.symbol ?? levels?.symbol ?? null;
  const recordedSeriesForSymbol = loadedSymbol
    ? barSeriesState.series.filter((s) => s.symbol === loadedSymbol)
    : [];
  const availableTimeframes = timeframesInOrder(recordedSeriesForSymbol);
  const effectiveTimeframe = availableTimeframes.includes(chartTimeframe)
    ? chartTimeframe
    : availableTimeframes.includes("1d")
      ? "1d"
      : (availableTimeframes[0] ?? "");

  // --- Raw-levels chart pipeline -----------------------------------------------------------------
  // Candles now EXTEND to the latest recorded bar (no as-of truncation) so later price action shows
  // against the historically-marked lines. `levels.levels` stays lookahead-free (backend
  // research/levels.py `_bars_as_of`); extending is a pure display choice over already-served rows.
  // `asOfEpochMs` is retained ONLY to locate the as-of MARKER bar (via `boundaryTs`), never to drop
  // candles. `representative` is now the recorded series matching the chosen viewing timeframe (its
  // created_utc tie-break picks among multiple windows of that timeframe — the same series
  // levels.py itself read for it).
  const seriesForSymbol = levels
    ? barSeriesState.series.filter((s) => s.symbol === levels.symbol)
    : [];
  const representative = pickRepresentativeSeries(
    seriesForSymbol.filter((s) => s.timeframe === effectiveTimeframe),
  );
  const asOfEpochMs = levels ? Date.parse(levels.as_of) : NaN;
  // The candles are paged in one viewport at a time (see `lib/useBarWindow.ts`) rather than read
  // off the series record — the metadata-only list carries no `bars`. The window is anchored around
  // the as-of instant and extends on zoom/scroll; `boundaryTs` runs over the LOADED window, so the
  // as-of marker is drawn exactly when its bar is on the chart (unchanged semantics: the last bar
  // at or before the as-of instant).
  //
  // Keyed on SYMBOL + TIMEFRAME, not on one series id: the hook reads GET /research/candles, which
  // merges every recording for that pair server-side. `representative` still names the ONE series
  // whose stored metadata the provenance badge reads — it no longer bounds what the chart can draw.
  // Gated on `showRawLevels`: the raw-levels chart is OFF by default, and a hidden chart must not
  // spend requests paging candles nobody is looking at (a `null` symbol keeps the hook itself
  // unconditional while fetching nothing). Toggling the section on loads its window then.
  const levelsWindow = useBarWindow(
    showRawLevels ? (levels?.symbol ?? null) : null,
    effectiveTimeframe || null,
    asOfEpochMs,
  );
  const chartBars = levelsWindow.bars;
  const asOfBoundaryTs = boundaryTs(chartBars, asOfEpochMs);

  // --- Tradable Map chart pipeline ---------------------------------------------------------------
  // Mirrors the raw-levels block (same extend + boundary-marker logic) but keyed off `tradability`.
  // Kept as a SEPARATE block (never a shared selection helper) so each chart renders correctly even
  // in the rare case GET /research/tradability and GET /research/levels resolve to DIFFERENT honest
  // states for the identical symbol/as-of (e.g. levels on a non-daily timeframe but no basis series
  // for tradability — see tradability.py's docstring). Bands stay lookahead-free and never change
  // with the chosen timeframe.
  const tradabilitySeriesForSymbol = tradability
    ? barSeriesState.series.filter((s) => s.symbol === tradability.symbol)
    : [];
  const tradabilityRepresentative = pickRepresentativeSeries(
    tradabilitySeriesForSymbol.filter((s) => s.timeframe === effectiveTimeframe),
  );
  const tradabilityAsOfEpochMs = tradability ? Date.parse(tradability.as_of) : NaN;
  const tradabilityWindow = useBarWindow(
    tradability?.symbol ?? null,
    effectiveTimeframe || null,
    tradabilityAsOfEpochMs,
  );
  const tradabilityChartBars = tradabilityWindow.bars;
  const tradabilityAsOfBoundaryTs = boundaryTs(tradabilityChartBars, tradabilityAsOfEpochMs);

  // era-5B J-02/J-03 (THIS iteration) Case Studies derived values. `filteredSetupsEvents` is a
  // CLIENT-SIDE display filter of the already-served, unfiltered registry (never a recomputation
  // or a second fetch) — the SAME `bar_series.filter` precedent this page already established.
  const setupsEvents = setupsResult?.ok ? setupsResult.events : [];
  const trimmedSetupsFilterSymbol = setupsFilterSymbol.trim().toUpperCase();
  const filteredSetupsEvents = setupsEvents.filter(
    (e) =>
      (trimmedSetupsFilterSymbol === "" || e.symbol === trimmedSetupsFilterSymbol) &&
      (setupsFilterReaction === "" || e.reaction === setupsFilterReaction),
  );

  // era-5B J-04 (THIS iteration) Edge Report derived value.
  const edgeReport = edgeReportResult?.ok ? edgeReportResult.data : null;

  // J-02 Registry section derived values.
  const registry = strategiesResult?.ok ? strategiesResult.strategies : null;
  const profiles = profilesResult?.ok ? profilesResult.profiles : null;
  // The cross-check caption: a plain-language narration of agreement between the two endpoints
  // that share one store source — it never picks a value (no "champion resolution"). Distinct,
  // honest copy per state: still loading, the profiles cross-check itself unavailable (registry
  // still renders — profiles is not required to show the strategies-sourced badge), confirmed
  // match, or (structurally near-impossible given one shared store call, but never silently
  // hidden) a disagreement.
  const championCrossCheck = !registry
    ? null
    : profilesResult === null
      ? { testid: "structure-champion-crosscheck-pending", text: "Cross-checking against GET /research/profiles…" }
      : !profiles
        ? {
            testid: "structure-champion-crosscheck-unavailable",
            text: "Cross-check against GET /research/profiles: unavailable.",
          }
        : championsMatch(registry.champion, profiles.champion)
          ? {
              testid: "structure-champion-crosscheck-match",
              text: "Confirmed identical to the champion served by GET /research/profiles — one store pointer, two read views.",
            }
          : {
              testid: "structure-champion-crosscheck-mismatch",
              text: "Warning: does not match the champion served by GET /research/profiles.",
            };

  // J-03 Comparison section derived values. `datasets`/`ledger` unwrap their `{ok, data, error?}`
  // results (the SAME pattern as `registry`/`profiles` above); `foundingRow` is read straight off
  // the already-fetched ledger — no new fetch, no derived/fabricated founding marker.
  const datasets = datasetsResult?.ok ? (datasetsResult.data?.datasets ?? []) : [];
  const ledger = ledgerResult?.ok ? ledgerResult.ledger : null;
  const foundingRow = ledger ? (ledger.rows.find((r) => r.founding) ?? null) : null;
  const comparisonRunning =
    comparisonSubmitting || needsPolling(v1Backtest) || needsPolling(structureTapeBacktest);

  return (
    <div className="min-h-screen">
      <main className="mx-auto max-w-7xl px-4 py-6">
        <header className="mb-4">
          <h1 data-testid="structure-title" className="text-lg font-semibold text-slate-200">
            Structure
          </h1>
          <p className="mt-1 max-w-3xl text-sm text-slate-500">
            Load a symbol and an as-of time to see its tradable level map — at most a handful of
            quality-scored bands, not the full raw level set — and read the 3-way strategy edge
            report.
          </p>
          <p data-testid="structure-framing" className="mt-2 max-w-3xl text-xs text-slate-600">
            Tradable Map is the default view, read verbatim from GET /research/tradability; toggle
            &quot;Show raw levels&quot; for the underlying S/R levels and confluence zones (off by
            default). Edge Report compares v1, structure_tape, and structure_tape_map over recorded
            windows, register included. Fetching bars below (Yahoo Finance, with Alpaca for history
            beyond Yahoo&apos;s limits) is this page&apos;s one explicit write action — everything else, including the
            strategy registry/champion and the structure_tape-vs-v1 comparison, is read-only. Every
            value on this page is read verbatim from its canonical endpoint — nothing here is
            recomputed in the browser.
          </p>
        </header>

        <form
          onSubmit={handleSubmit}
          className="mb-4 flex flex-wrap items-end gap-3 rounded-lg border border-slate-800 bg-slate-900/40 p-4"
        >
          <label className="block">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-slate-500">
              Symbol
            </span>
            <SymbolSearch
              value={symbolInput}
              onChange={setSymbolInput}
              onPick={setSymbolInput}
              placeholder="e.g. PG"
              ariaLabel="Structure symbol"
              inputClassName={INPUT_CLASS}
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-slate-500">
              As-of (UTC, ISO-8601)
            </span>
            <input
              data-testid="structure-as-of-input"
              value={asOfInput}
              onChange={(e) => setAsOfInput(e.target.value)}
              placeholder="2026-06-09T21:00:00Z"
              className={INPUT_CLASS}
            />
          </label>
          {/* The as-of shortcut: fills the field with the LAST second of today's UTC day — the
              SAME `endOfDayUtc` instant this page already seeds As-of with after a fetch, so a
              "today" load admits every bar recorded so far today and never a next-day bar. It
              fills the field only; loading stays the operator's explicit click. */}
          <button
            type="button"
            data-testid="structure-as-of-today-button"
            onClick={() => setAsOfInput(endOfDayUtc(todayUtcDate()))}
            className={SECONDARY_BUTTON_CLASS}
          >
            Today
          </button>
          <button
            type="submit"
            data-testid="structure-load-button"
            disabled={!canSubmit}
            className="rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:border-slate-500 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-600 disabled:hover:bg-slate-800"
          >
            Load
          </button>
        </form>

        {/* The viewing-timeframe selector — a page-level control governing BOTH charts below (they
            share one recorded-bars source). Shown once the loaded symbol has any recorded series;
            `value` is the EFFECTIVE (drawn) timeframe so it always reflects what's on screen. */}
        {availableTimeframes.length > 0 && (
          <div className="mt-4 max-w-xs">
            <label className="block">
              <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-slate-500">
                Chart timeframe
              </span>
              <select
                data-testid="structure-timeframe-select"
                value={effectiveTimeframe}
                onChange={(e) => setChartTimeframe(e.target.value)}
                className={INPUT_CLASS}
              >
                {availableTimeframes.map((tf) => (
                  <option key={tf} value={tf}>
                    {tf}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}

        {/* era-5B J-01 (THIS iteration) — the NEW default view: at most a handful of
            quality-scored bands, read verbatim from GET /research/tradability. Driven by the SAME
            Load form above. */}
        <section aria-label="Tradable map">
          <Panel title="Tradable Map">
            <p className="mb-3 -mt-1 max-w-3xl text-xs text-slate-600">
              A distilled tradable level map — at most a handful of quality-scored bands per side,
              clustered and scored from the raw S/R levels under morning-markup as-of discipline.
              Every band's range, side, class, quality score, member count, and round-number flag
              below is read verbatim from GET /research/tradability — nothing here is recomputed.
            </p>
            {tradabilityState.phase === "idle" && (
              <EmptyState
                testid="tradable-map-idle"
                title="Choose a symbol and an as-of time, then Load, to see its tradable level map."
              />
            )}
            {tradabilityState.phase === "loading" && <LoadingPanel testid="tradable-map-loading" />}
            {tradabilityState.phase === "error" && (
              <UnavailablePanel
                testid="tradable-map-unavailable"
                message={tradabilityState.error ?? "The tradable map could not be loaded."}
              />
            )}
            {tradabilityState.phase === "ready" &&
              tradability &&
              (tradability.no_bar_series_for_symbol ? (
                <EmptyState
                  testid="tradable-map-no-bar-series"
                  title={`No bar series recorded for ${tradability.symbol}.`}
                  detail="Recording historical bars needs provider credentials."
                />
              ) : tradability.bands.length === 0 ? (
                <EmptyState
                  testid="tradable-map-no-bands"
                  title={`No tradable map derivable for ${tradability.symbol} as of ${tradability.as_of}.`}
                  detail="A bar series is recorded, but no prior-session basis is derivable yet."
                />
              ) : (
                <div className="space-y-4">
                  <p data-testid="tradable-map-basis" className="text-xs text-slate-500">
                    Map basis (prior completed session close):{" "}
                    <span className="font-mono text-slate-300">{tradability.basis_as_of}</span>
                  </p>
                  {barSeriesState.phase === "loading" ? (
                    <LoadingPanel testid="tradable-map-chart-loading" />
                  ) : barSeriesState.phase === "error" ? (
                    <UnavailablePanel
                      testid="tradable-map-chart-unavailable"
                      message={barSeriesState.error ?? "The bar series list could not be loaded."}
                    />
                  ) : (
                    <>
                      <StructureChart
                        key={`tradability|${tradability.symbol}|${tradability.as_of}`}
                        bars={tradabilityChartBars}
                        levels={[]}
                        bands={tradability.bands}
                        asOfTs={tradabilityAsOfBoundaryTs}
                        onNeedOlder={tradabilityWindow.loadOlder}
                        onNeedNewer={tradabilityWindow.loadNewer}
                        loadingMore={tradabilityWindow.loading}
                      />
                      <p
                        data-testid="tradable-map-chart-caption"
                        className="mt-2 text-[11px] text-slate-600"
                      >
                        {tradabilityWindow.seriesCount > 0
                          ? `${chartCaption({
                              timeframe: effectiveTimeframe,
                              loaded: tradabilityChartBars.length,
                              available: tradabilityWindow.availableBars,
                              seriesCount: tradabilityWindow.seriesCount,
                              revised: tradabilityWindow.revisedTimestamps,
                              capped: tradabilityWindow.capped,
                              maxLoaded: MAX_LOADED_BARS,
                            })} The "as-of" marker is the last bar known at the query time; bars to its right are later price action (context only). Band lines are multi-timeframe aggregates computed strictly as of the query time (lookahead-free) and do not change with the chart timeframe.`
                          : "No recorded candle series available to draw for this symbol."}
                      </p>
                      {tradabilityWindow.error && (
                        <p
                          data-testid="tradable-map-chart-window-error"
                          className="mt-1 text-[11px] text-rose-700"
                        >
                          {tradabilityWindow.error}
                        </p>
                      )}
                    </>
                  )}
                  <BandsTable bands={tradability.bands} />
                </div>
              ))}
          </Panel>
        </section>

        {/* era-5B J-05 (THIS iteration) — the raw-levels toggle, OFF by default. Toggling it on
            renders the pre-existing Levels & Zones section, byte-identically to before this
            iteration (the section immediately below is untouched code). */}
        <div className="mt-4">
          <button
            type="button"
            data-testid="raw-levels-toggle"
            onClick={() => setShowRawLevels((prev) => !prev)}
            className="rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:border-slate-500 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-900"
          >
            {showRawLevels ? "Hide raw levels" : "Show raw levels"}
          </button>
        </div>

        {showRawLevels && (
          <div className="mt-4">
            <section aria-label="Levels and zones">
              {levelsState.phase === "idle" && (
                <EmptyState
                  testid="structure-idle"
                  title="Choose a symbol and an as-of time, then Load, to see its S/R levels and confluence zones."
                />
              )}
              {levelsState.phase === "loading" && <LoadingPanel testid="structure-loading" />}
              {levelsState.phase === "error" && (
                <UnavailablePanel testid="structure-degraded" message={levelsState.message} />
              )}
              {levelsState.phase === "ready" &&
                levels &&
                (levels.no_bar_series_for_symbol ? (
                  <EmptyState
                    testid="structure-no-bar-series"
                    title={`No bar series recorded for ${levels.symbol}.`}
                    detail="Recording historical bars needs provider credentials."
                  />
                ) : levels.levels.length === 0 ? (
                  <EmptyState
                    testid="structure-no-levels"
                    title={`No levels found for ${levels.symbol} as of ${levels.as_of}.`}
                    detail="A bar series is recorded, but nothing is derivable at this as-of time."
                  />
                ) : (
                  <div className="space-y-4">
                    <Panel title="Price chart — S/R levels">
                      {barSeriesState.phase === "loading" ? (
                        <LoadingPanel testid="structure-chart-loading" />
                      ) : barSeriesState.phase === "error" ? (
                        <UnavailablePanel
                          testid="structure-chart-unavailable"
                          message={barSeriesState.error ?? "The bar series list could not be loaded."}
                        />
                      ) : (
                        <>
                          {/* J-05 provenance badge: reuses the SAME taxonomy-driven FeedBasisBadge the
                              cockpit uses, keyed off the charted series' own `feed` field (verbatim off
                              GET /research/bars — zero client recomputation). Honestly absent when no
                              series is charted (the component's own no-fabrication rule). */}
                          {representative && (
                            <div className="mb-2">
                              <FeedBasisBadge dataFeed={representative.feed} />
                            </div>
                          )}
                          <StructureChart
                            key={`${levels.symbol}|${levels.as_of}`}
                            bars={chartBars}
                            levels={levels.levels}
                            asOfTs={asOfBoundaryTs}
                            onNeedOlder={levelsWindow.loadOlder}
                            onNeedNewer={levelsWindow.loadNewer}
                            loadingMore={levelsWindow.loading}
                          />
                          <p
                            data-testid="structure-chart-caption"
                            className="mt-2 text-[11px] text-slate-600"
                          >
                            {levelsWindow.seriesCount > 0
                              ? `${chartCaption({
                                  timeframe: effectiveTimeframe,
                                  loaded: chartBars.length,
                                  available: levelsWindow.availableBars,
                                  seriesCount: levelsWindow.seriesCount,
                                  revised: levelsWindow.revisedTimestamps,
                                  capped: levelsWindow.capped,
                                  maxLoaded: MAX_LOADED_BARS,
                                })} The "as-of" marker is the last bar the level computation could see; bars to its right are later price action (context only). S/R level lines are computed strictly as of the query time (lookahead-free) and span every recorded timeframe.`
                              : "No recorded candle series available to draw for this symbol."}
                          </p>
                          {levelsWindow.error && (
                            <p
                              data-testid="structure-chart-window-error"
                              className="mt-1 text-[11px] text-rose-700"
                            >
                              {levelsWindow.error}
                            </p>
                          )}
                        </>
                      )}
                    </Panel>

                    <Panel title="Confluence zones">
                      {levels.confluence_zones.length === 0 ? (
                        <EmptyState
                          testid="structure-no-zones"
                          title="No qualifying confluence zone among these levels."
                          detail="Levels exist, but none cluster closely enough across timeframes to form a zone."
                        />
                      ) : (
                        <div className="space-y-3">
                          {levels.confluence_zones.map((zone, i) => (
                            <ZoneRow key={i} zone={zone} index={i} />
                          ))}
                        </div>
                      )}
                    </Panel>
                  </div>
                ))}
            </section>
          </div>
        )}

        {/* era-5B J-02/J-03 (THIS iteration) — the case-study registry: every historical
            band-touch event, filterable by symbol/reaction, with a row drill-in showing the tape
            timeline once a dataset was recorded around that event. */}
        {SHOW_CASE_STUDIES && (
        <section aria-label="Case studies" className="mt-6">
          <Panel title="Case Studies">
            <p className="mb-3 -mt-1 max-w-3xl text-xs text-slate-600">
              Every band-touch event this store has scanned, read verbatim from GET
              /research/setups — reaction, forward returns, and (once a dataset was recorded around
              it) the tape timeline. The filters below narrow the already-served rows; nothing here
              is recomputed.
            </p>
            <div className="mb-3 flex flex-wrap items-end gap-3">
              <label className="block">
                <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-slate-500">
                  Symbol
                </span>
                <input
                  data-testid="case-studies-filter-symbol"
                  value={setupsFilterSymbol}
                  onChange={(e) => setSetupsFilterSymbol(e.target.value)}
                  placeholder="e.g. AAPL"
                  className={INPUT_CLASS}
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-slate-500">
                  Reaction
                </span>
                <select
                  data-testid="case-studies-filter-reaction"
                  value={setupsFilterReaction}
                  onChange={(e) => setSetupsFilterReaction(e.target.value)}
                  className={INPUT_CLASS}
                >
                  <option value="">All</option>
                  {SETUP_REACTIONS.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {setupsResult === null ? (
              <LoadingPanel testid="case-studies-loading" />
            ) : !setupsResult.ok ? (
              <UnavailablePanel
                testid="case-studies-unavailable"
                message={setupsResult.error ?? "The case-study registry could not be loaded."}
              />
            ) : setupsEvents.length === 0 ? (
              <EmptyState testid="case-studies-empty" title="No band-touch events scanned yet." />
            ) : filteredSetupsEvents.length === 0 ? (
              <EmptyState
                testid="case-studies-no-match"
                title="No events match these filters."
                detail="The registry has rows — this filter combination simply matches none."
              />
            ) : (
              <div className="overflow-x-auto">
                <table data-testid="case-studies-table" className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800">
                      <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">
                        symbol
                      </th>
                      <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">
                        session
                      </th>
                      <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">
                        band
                      </th>
                      <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">
                        reaction
                      </th>
                      <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">
                        forward returns
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredSetupsEvents.map((event) => (
                      <SetupRow
                        key={event.id}
                        event={event}
                        selected={event.id === selectedSetupId}
                        onSelect={() => setSelectedSetupId(event.id)}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {selectedSetupId !== null && <SetupDrillIn state={setupDetailState} />}
          </Panel>
        </section>
        )}

        {/* era-5B J-04 (THIS iteration) — the 3-way strategy-comparison edge report. */}
        <section aria-label="Edge report" className="mt-6">
          <Panel title="Edge Report">
            <p className="mb-3 -mt-1 max-w-3xl text-xs text-slate-600">
              The v1 / structure_tape / structure_tape_map comparison over recorded event windows,
              read verbatim from GET /research/edge-report — per-cell n, R, and $ carry the full
              simulated register; train and hold-out are never pooled. An empty or
              all-insufficient-sample report is an honest, valid outcome.
            </p>
            {edgeReportResult === null ? (
              <LoadingPanel testid="edge-report-loading" />
            ) : !edgeReportResult.ok || !edgeReport ? (
              <UnavailablePanel
                testid="edge-report-unavailable"
                message={edgeReportResult.error ?? "The edge report could not be loaded."}
              />
            ) : edgeReport.status === "not_computed" ? (
              <NotComputedPanel
                detail={edgeReport.detail}
                compute={computeSnapshot}
                datasets={datasetsResult?.data?.datasets ?? []}
                onTriggerCompute={handleTriggerEdgeReportCompute}
                triggering={computeTriggering}
                triggerError={computeTriggerError}
                onCancelCompute={handleCancelEdgeReportCompute}
                cancelRequested={computeCancelRequested}
                cancelError={computeCancelError}
              />
            ) : (
              <EdgeReportBody report={edgeReport} />
            )}
          </Panel>
        </section>

        {/* era-5 J-05 — the Fetch-from-Yahoo control, repositioned below the three new sections
            above (Foundation invariant: unchanged behavior, only moved). */}
        <section aria-label="Fetch bars" className="mt-6">
          <Panel title="Fetch bars">
            <p className="mb-3 -mt-1 max-w-3xl text-xs text-slate-600">
              Fetch real historical bars for a symbol and UTC date range, on this explicit click.
              One click fetches all six supported timeframes (1w, 1d, 4h, 1h, 5m, 1m; 4h is derived
              from real 1h bars). The end date is included in full. Yahoo Finance is the keyless
              source, and it keeps intraday history for a limited time — 1m for the last 30 days,
              5m for 60, 1h for 730; 1d and 1w are unlimited. When the requested range reaches
              further back than that, the remainder is fetched from Alpaca (credentialed), recorded
              separately, and stitched into the charts by timestamp. Alpaca&apos;s SIP feed includes
              pre- and post-market bars, so the older part of a range can cover a wider session than
              the Yahoo part. Each timeframe reports below exactly which vendor covered which dates;
              an already-fetched window is served from storage. On success, the Tradable Map and
              Levels &amp; Zones sections above load the fetched symbol automatically.
            </p>
            <form onSubmit={handleFetchSubmit} className="flex flex-wrap items-end gap-3">
              <label className="block">
                <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-slate-500">
                  Symbol
                </span>
                <SymbolSearch
                  value={fetchSymbolInput}
                  onChange={setFetchSymbolInput}
                  onPick={setFetchSymbolInput}
                  placeholder="e.g. AAPL"
                  ariaLabel="Fetch symbol"
                  inputClassName={INPUT_CLASS}
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-slate-500">
                  Start date (UTC)
                </span>
                <input
                  data-testid="fetch-start-input"
                  value={fetchStartInput}
                  onChange={(e) => setFetchStartInput(e.target.value)}
                  placeholder="2026-06-01"
                  className={INPUT_CLASS}
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-slate-500">
                  End date (UTC, inclusive)
                </span>
                <input
                  data-testid="fetch-end-input"
                  value={fetchEndInput}
                  onChange={(e) => setFetchEndInput(e.target.value)}
                  placeholder="2026-06-04"
                  className={INPUT_CLASS}
                />
              </label>
              {/* The current-day shortcut: sets BOTH dates to today's UTC calendar date (the end
                  date is inclusive server-side, so start = end = today is exactly today's session).
                  It fills the fields only — fetching stays the operator's explicit click, since it
                  is this page's one write action. */}
              <button
                type="button"
                data-testid="fetch-today-button"
                onClick={() => {
                  const today = todayUtcDate();
                  setFetchStartInput(today);
                  setFetchEndInput(today);
                }}
                className={SECONDARY_BUTTON_CLASS}
              >
                Today
              </button>
              <button
                type="submit"
                data-testid="fetch-yahoo-button"
                disabled={!canFetch || fetchSubmitting}
                className="rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:border-slate-500 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-600 disabled:hover:bg-slate-800"
              >
                {fetchSubmitting ? "Fetching…" : "Fetch bars"}
              </button>
            </form>
            {fetchResults && (
              <ul data-testid="fetch-results" className="mt-3 flex flex-col gap-1">
                {fetchResults.map((row) => (
                  <li
                    key={row.timeframe}
                    data-testid={`fetch-result-${row.timeframe}`}
                    className={`flex items-baseline gap-2 text-xs ${FETCH_RESULT_COLOR[row.state]}`}
                  >
                    <span className="w-8 shrink-0 font-mono font-medium">{row.timeframe}</span>
                    <span>{row.message}</span>
                  </li>
                ))}
              </ul>
            )}
            {fetchError && (
              <div className="mt-3">
                <UnavailablePanel testid="fetch-yahoo-error" message={fetchError} />
              </div>
            )}
          </Panel>
        </section>

        {/* J-02: the strategy registry + champion — fetched on mount (see the useEffect above),
            independent of the Load button above; populated even without any recorded bars. */}
        <section aria-label="Strategy registry" className="mt-6">
          {strategiesResult === null ? (
            <LoadingPanel testid="structure-registry-loading" />
          ) : !strategiesResult.ok || !registry ? (
            <UnavailablePanel
              testid="structure-registry-unavailable"
              message={strategiesResult.error ?? "The strategy registry could not be loaded."}
            />
          ) : (
            <Panel title="Registry">
              <p className="mb-3 -mt-1 max-w-3xl text-xs text-slate-600">
                Read-only: every strategy field and the champion below are read verbatim from
                GET /research/strategies — nothing here is recomputed in the browser.
              </p>
              <div className="space-y-4">
                <div
                  data-testid="champion-summary"
                  className="rounded-lg border border-slate-800 bg-slate-900/60 p-4"
                >
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Champion
                  </h3>
                  <dl className="space-y-2">
                    <div className="flex items-baseline justify-between gap-2">
                      <dt className="text-xs text-slate-500">strategy</dt>
                      <dd
                        data-testid="champion-strategy"
                        className="font-mono text-sm text-slate-200"
                      >
                        {registry.champion.strategy_id}
                      </dd>
                    </div>
                    <div className="flex items-baseline justify-between gap-2">
                      <dt className="text-xs text-slate-500">profile</dt>
                      <dd
                        data-testid="champion-profile"
                        className="font-mono text-sm text-slate-200"
                      >
                        {registry.champion.profile}
                      </dd>
                    </div>
                  </dl>
                  {championCrossCheck && (
                    <p
                      data-testid={championCrossCheck.testid}
                      className="mt-2 text-[11px] text-slate-600"
                    >
                      {championCrossCheck.text}
                    </p>
                  )}
                </div>

                {registry.strategies.map((strategy) => (
                  <StrategyCard key={strategy.strategy_id} strategy={strategy} />
                ))}
              </div>
            </Panel>
          )}
        </section>

        {/* J-03: the honest structure_tape-vs-v1 comparison. A dataset selector + "Run comparison"
            starts two backtests (v1 + structure_tape, both profile=default) and polls both to a
            terminal status, then renders both strategies' aggregates + the per-class A/B/C
            breakdown side by side, beside the read-only champion pointer (reused from the
            Registry section's own fetch above — never a second champion fetch) and the founding
            baseline row from the PnL ledger. This view starts a research job; it moves the
            champion NEVER and writes nothing to the ledger. */}
        <section aria-label="structure_tape vs v1 comparison" className="mt-6">
          <Panel title="Comparison">
            <p className="mb-3 -mt-1 max-w-3xl text-xs text-slate-600">
              Read-only: every aggregate, per-class value, and the register line below are read
              verbatim from GET /research/backtests — nothing here is recomputed in the browser.
              Running a comparison starts an offline research job over an already-recorded
              dataset; it places nothing and never moves the champion.
            </p>

            <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div
                data-testid="comparison-champion"
                className="rounded-lg border border-slate-800 bg-slate-900/60 p-3"
              >
                <h4 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Champion (moved never by this view)
                </h4>
                {registry ? (
                  <dl className="space-y-1">
                    <div className="flex items-baseline justify-between gap-2">
                      <dt className="text-xs text-slate-500">strategy</dt>
                      <dd
                        data-testid="comparison-champion-strategy"
                        className="font-mono text-xs text-slate-200"
                      >
                        {registry.champion.strategy_id}
                      </dd>
                    </div>
                    <div className="flex items-baseline justify-between gap-2">
                      <dt className="text-xs text-slate-500">profile</dt>
                      <dd
                        data-testid="comparison-champion-profile"
                        className="font-mono text-xs text-slate-200"
                      >
                        {registry.champion.profile}
                      </dd>
                    </div>
                  </dl>
                ) : (
                  <p className="text-xs text-slate-600">
                    Champion not yet loaded (see the Registry section above).
                  </p>
                )}
              </div>

              <div
                data-testid="comparison-founding-baseline"
                className="rounded-lg border border-slate-800 bg-slate-900/60 p-3"
              >
                <h4 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Founding baseline (PnL ledger)
                </h4>
                {ledgerResult === null ? (
                  <LoadingPanel testid="comparison-founding-loading" />
                ) : !ledgerResult.ok || !ledger ? (
                  <UnavailablePanel
                    testid="comparison-founding-unavailable"
                    message={ledgerResult.error ?? "The PnL ledger could not be loaded."}
                  />
                ) : foundingRow ? (
                  <dl data-testid="comparison-founding-row" className="space-y-1">
                    <div className="flex items-baseline justify-between gap-2">
                      <dt className="text-xs text-slate-500">{foundingRow.title}</dt>
                    </div>
                    <div className="flex items-baseline justify-between gap-2">
                      <dt className="text-xs text-slate-500">candidate train net R</dt>
                      <dd className="font-mono text-xs text-slate-200">
                        {String(foundingRow.candidate.train.net_r)}
                      </dd>
                    </div>
                    <div className="flex items-baseline justify-between gap-2">
                      <dt className="text-xs text-slate-500">candidate hold-out net R</dt>
                      <dd className="font-mono text-xs text-slate-200">
                        {String(foundingRow.candidate.holdout.net_r)}
                      </dd>
                    </div>
                  </dl>
                ) : (
                  <p data-testid="comparison-no-founding-row" className="text-xs text-slate-600">
                    No founding row yet — the PnL ledger is empty.
                  </p>
                )}
              </div>
            </div>

            {datasetsResult === null ? (
              <LoadingPanel testid="comparison-datasets-loading" />
            ) : !datasetsResult.ok ? (
              <UnavailablePanel
                testid="comparison-datasets-unavailable"
                message={datasetsResult.error ?? "The dataset list could not be loaded."}
              />
            ) : datasets.length === 0 ? (
              <EmptyState
                testid="comparison-no-datasets"
                title="No datasets registered."
                detail="Record a dataset (via POST /research/datasets, or the Studies workflow) before running a comparison."
              />
            ) : (
              <>
                <form
                  onSubmit={handleComparisonSubmit}
                  className="mb-4 flex flex-wrap items-end gap-3 rounded-lg border border-slate-800 bg-slate-900/40 p-4"
                >
                  <label className="block">
                    <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-slate-500">
                      Dataset
                    </span>
                    <select
                      data-testid="comparison-dataset-select"
                      value={selectedDatasetId}
                      onChange={(e) => setSelectedDatasetId(e.target.value)}
                      className={INPUT_CLASS}
                    >
                      <option value="">Choose a dataset…</option>
                      {datasets.map((d: Dataset) => (
                        <option key={d.id} value={d.id}>
                          {d.symbol} · {d.split} · {d.id.slice(0, 8)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button
                    type="submit"
                    data-testid="comparison-run-button"
                    disabled={!selectedDatasetId || comparisonRunning}
                    className="rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:border-slate-500 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-600 disabled:hover:bg-slate-800"
                  >
                    {comparisonRunning ? "Running…" : "Run comparison"}
                  </button>
                </form>

                {comparisonError && (
                  <UnavailablePanel testid="comparison-run-error" message={comparisonError} />
                )}
                {comparisonPollError && !comparisonError && (
                  <p data-testid="comparison-poll-error" className="mb-3 text-xs text-amber-300">
                    {comparisonPollError}
                  </p>
                )}

                {!comparisonError && !v1Backtest && !structureTapeBacktest && (
                  <EmptyState
                    testid="comparison-idle"
                    title="Choose a dataset, then Run comparison, to compare structure_tape against v1."
                  />
                )}

                {(v1Backtest || structureTapeBacktest) && (
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <BacktestPanel
                      label="v1 (champion strategy)"
                      backtest={v1Backtest}
                      testid="comparison-v1"
                      minSampleSize={ledger?.min_sample_size ?? null}
                    />
                    <BacktestPanel
                      label="structure_tape"
                      backtest={structureTapeBacktest}
                      testid="comparison-structure-tape"
                      minSampleSize={ledger?.min_sample_size ?? null}
                    />
                  </div>
                )}
              </>
            )}
          </Panel>
        </section>
      </main>
    </div>
  );
}
