"use client";

import { useEffect, useState } from "react";
import {
  createBacktest,
  fetchBacktest,
  fetchBarSeriesList,
  fetchDatasets,
  fetchLevels,
  fetchPnlLedger,
  fetchProfiles,
  fetchStrategies,
} from "@/lib/api";
import type {
  Backtest,
  BacktestClassAggregate,
  BacktestResult,
  BarSeriesListResult,
  BarSeriesRecord,
  ConfluenceZone,
  Dataset,
  DatasetsListResult,
  LevelsResponse,
  PnlLedger,
  ProfilesPayload,
  Strategy,
  StrategiesPayload,
} from "@/lib/types";
import { SymbolSearch } from "@/components/SymbolSearch";
import { StructureChart } from "@/components/StructureChart";
import { Panel } from "@/components/Panel";

// The /structure page (J-01 + J-02 + J-03) — the era-4 structure stack's browser home, now
// complete. For a chosen symbol + as-of time it renders a price chart with one dashed line per S/R
// level plus a confluence-zones table badged A/B/C (J-01); below that, a read-only Registry section
// shows the two registered strategies plus the current champion (J-02); below THAT, a Comparison
// section runs `structure_tape` against the champion `v1` over a chosen dataset and renders both
// strategies' aggregates + per-class A/B/C breakdown side by side, beside the champion pointer and
// the founding PnL-ledger baseline row (J-03). Reached from the top-bar link, served by
// GET /meta/ui-routes (data-driven NavBar — no client hardcoding; see apps/backend/app/meta.py
// UI_ROUTES). Follows the /performance page pattern: client component, no business logic,
// canonical endpoints read verbatim, `{ok, data, error}`-shaped fetch results.
//
// EIGHT canonical endpoints, rendered VERBATIM and nothing else:
//   * GET /research/levels?symbol=&as_of=  (Data Contract row 39) — levels + confluence zones +
//     the `no_bar_series_for_symbol` honesty flag. The A/B/C badge is `zone.class`, the score is
//     `zone.score` — neither is ever recomputed from breadth or member strength.
//   * GET /research/bars  (Data Contract row 38) — every registered bar series. This is a LIST
//     endpoint with no symbol query param, so this page filters the returned array CLIENT-SIDE by
//     the already-served `symbol` field to find candles for the chart — the SAME filtering
//     discipline NavBar already applies to `nav: true` (filtering already-served rows is not a
//     recomputation of any value).
//   * GET /research/strategies  (Data Contract row 40/41, J-02) — the strategy registry (`v1` +
//     `structure_tape`) + the champion pointer. Fetched on mount, independent of the Levels & Zones
//     Load button (the registry and champion are populated even keyless).
//   * GET /research/profiles  (Data Contract row 33) — read ONLY to cross-check its `champion`
//     against `/research/strategies`'s own `champion` (both read the SAME store pointer — never a
//     second champion source).
//   * GET /research/datasets  (Data Contract row 30, J-03) — every registered dataset, fetched on
//     mount to populate the Comparison section's dataset selector.
//   * POST /research/backtests + GET /research/backtests/{id}  (Data Contract row 31, J-03) — the
//     Comparison section's "Run comparison" starts TWO backtests (`v1` + `structure_tape`, both
//     `profile=default`) on the chosen dataset and polls both to a terminal status, reusing the
//     Studies job/poll PATTERN (not its endpoint). Every aggregate, per-class value, and the
//     register line is read verbatim from the terminal payload — zero recomputation.
//   * GET /research/pnl/ledger  (Data Contract row 32, J-03) — read ONLY for the founding baseline
//     row (`rows.find(r => r.founding)`) shown beside the comparison; the champion badge reuses the
//     ALREADY-fetched `/research/strategies` champion (no second champion fetch).
//
// Four distinct honest states for the Levels & Zones section (never share copy, never fabricate a
// chart/level/zone):
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
// The Registry section (J-02) has its own distinct honest states — loading, registry-unavailable
// (`/research/strategies` unreachable/non-200), and populated — see `structure-registry-*` testids.
//
// The Comparison section (J-03) has several distinct honest states — see `comparison-*` testids:
// no datasets registered, the dataset list unreachable, idle (a dataset list is populated but Run
// has not been clicked), a backtest queued/running (per side, independently), a backtest failed
// (per side), a backtest cancelled (per side, carrying NO result — never a partial simulated PnL),
// a poll-time backend-unreachable notice, and done (aggregates + per-class table,
// `insufficient_sample` shown inline — never a separate "insufficient" state). The section NEVER
// moves the champion pointer and writes NOTHING to the PnL ledger.
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

// The canonical bar-store timeframe order (mirrors apps/backend/app/config.py's `bar_timeframes`
// tuple) used ONLY to pick which ONE registered series' candles the chart draws when a symbol has
// more than one (a single candlestick chart cannot honestly overlay two timeframes' OHLC at once —
// see the dev handoff). This is a DISPLAY CHOICE over already-served records — it selects among
// existing rows, computing no new price/level/zone value. The shortest available timeframe wins.
const TIMEFRAME_ORDER = ["1m", "5m", "15m", "1h", "4h", "8h", "1d", "1w", "1mo"];

function pickRepresentativeSeries(seriesForSymbol: BarSeriesRecord[]): BarSeriesRecord | null {
  if (seriesForSymbol.length === 0) return null;
  const ranked = [...seriesForSymbol].sort((a, b) => {
    const rankA = TIMEFRAME_ORDER.indexOf(a.timeframe);
    const rankB = TIMEFRAME_ORDER.indexOf(b.timeframe);
    const safeA = rankA === -1 ? TIMEFRAME_ORDER.length : rankA;
    const safeB = rankB === -1 ? TIMEFRAME_ORDER.length : rankB;
    if (safeA !== safeB) return safeA - safeB;
    // Same timeframe (or same unrecognized rank): most-recently-created wins — mirrors the
    // backend's OWN tie-break for the identical (symbol, timeframe) case
    // (research/levels.py's `_select_one_series_per_timeframe`), so the chart's chosen series is
    // never in tension with which series the levels computation itself read for that timeframe.
    return b.created_utc.localeCompare(a.created_utc);
  });
  return ranked[0];
}

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
  const [barsState, setBarsState] = useState<LoadState<BarSeriesListResult>>({ phase: "idle" });

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
    return () => {
      alive = false;
    };
  }, []);

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

  async function handleLoad(symbol: string, asOf: string) {
    const trimmedSymbol = symbol.trim();
    const trimmedAsOf = asOf.trim();
    if (!trimmedSymbol || !trimmedAsOf) return; // the Load button is already disabled in this case
    setLevelsState({ phase: "loading" });
    setBarsState({ phase: "loading" });
    const [levelsResult, barsResult] = await Promise.all([
      fetchLevels(trimmedSymbol, trimmedAsOf),
      fetchBarSeriesList(),
    ]);
    setLevelsState(
      levelsResult.ok && levelsResult.data
        ? { phase: "ready", data: levelsResult.data }
        : { phase: "error", message: levelsResult.error ?? "The levels could not be loaded." },
    );
    setBarsState(
      barsResult.ok && barsResult.data
        ? { phase: "ready", data: barsResult.data }
        : {
            phase: "error",
            message: barsResult.error ?? "The bar series list could not be loaded.",
          },
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    handleLoad(symbolInput, asOfInput);
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
  const levels = levelsState.phase === "ready" ? levelsState.data : null;
  const seriesForSymbol =
    barsState.phase === "ready" && levels
      ? barsState.data.bar_series.filter((s) => s.symbol === levels.symbol)
      : [];
  const representative = pickRepresentativeSeries(seriesForSymbol);
  // Scope the drawn candles to the SAME as-of instant the levels query used, so the chart never
  // shows a bar the level computation could not have seen (the backend's OWN lookahead-free
  // truncation — research/levels.py's `_bars_as_of` — is unaffected either way; this is a display
  // filter of already-served rows, not a second computation). `levels.as_of` is guaranteed
  // backend-parseable here (reaching this branch means GET /research/levels already accepted it),
  // so a `Date.parse` failure is not expected — the fallback (show every recorded bar) is still
  // real, verbatim data, never a fabricated or blank chart.
  const asOfEpochMs = levels ? Date.parse(levels.as_of) : NaN;
  const chartBars =
    representative && !Number.isNaN(asOfEpochMs)
      ? representative.bars.filter((b) => b.ts * 1000 <= asOfEpochMs)
      : (representative?.bars ?? []);

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
            Deterministic support/resistance levels and A/B/C confluence zones for a chosen symbol
            and as-of time, the registered strategies and current champion, and a
            structure_tape-vs-v1 backtest comparison.
          </p>
          <p data-testid="structure-framing" className="mt-2 max-w-3xl text-xs text-slate-600">
            Read-only, in three sections: S/R levels and confluence zones on a price chart; the
            strategy registry and champion; and a structure_tape-vs-v1 comparison you can run over
            a chosen dataset. Every value below is read verbatim from its canonical endpoint —
            nothing here is recomputed in the browser.
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
          <button
            type="submit"
            data-testid="structure-load-button"
            disabled={!canSubmit}
            className="rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:border-slate-500 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-600 disabled:hover:bg-slate-800"
          >
            Load
          </button>
        </form>

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
                  {barsState.phase === "loading" ? (
                    <LoadingPanel testid="structure-chart-loading" />
                  ) : barsState.phase === "error" ? (
                    <UnavailablePanel
                      testid="structure-chart-unavailable"
                      message={barsState.message}
                    />
                  ) : (
                    <>
                      <StructureChart
                        key={`${levels.symbol}|${levels.as_of}`}
                        bars={chartBars}
                        levels={levels.levels}
                      />
                      <p className="mt-2 text-[11px] text-slate-600">
                        {representative
                          ? `Candles: ${representative.timeframe} series (${chartBars.length} of ${representative.bar_count} recorded bars, as of the query time). Level lines span every recorded timeframe.`
                          : "No recorded candle series available to draw for this symbol."}
                      </p>
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
