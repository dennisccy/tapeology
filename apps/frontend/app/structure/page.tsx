"use client";

import { useEffect, useState } from "react";
import { fetchBarSeriesList, fetchLevels, fetchProfiles, fetchStrategies } from "@/lib/api";
import type {
  BarSeriesListResult,
  BarSeriesRecord,
  ConfluenceZone,
  LevelsResponse,
  ProfilesPayload,
  Strategy,
  StrategiesPayload,
} from "@/lib/types";
import { SymbolSearch } from "@/components/SymbolSearch";
import { StructureChart } from "@/components/StructureChart";
import { Panel } from "@/components/Panel";

// The /structure page (J-01 + J-02) — the era-4 structure stack's browser home. For a chosen
// symbol + as-of time it renders a price chart with one dashed line per S/R level plus a
// confluence-zones table badged A/B/C (J-01); below that, a read-only Registry section shows the
// two registered strategies plus the current champion (J-02). Reached from the top-bar link,
// served by GET /meta/ui-routes (data-driven NavBar — no client hardcoding; see
// apps/backend/app/meta.py UI_ROUTES). Follows the /performance page pattern: client component, no
// business logic, canonical endpoints read verbatim, `{ok, data, error}`-shaped fetch results.
//
// FOUR canonical endpoints, rendered VERBATIM and nothing else:
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
//     second champion source). J-03 (backtest comparison) is a LATER section of this same page —
//     not built this iteration.
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
// Dark instrument-panel style consistent with /journal, /studies, /performance: slate surfaces,
// restrained borders, font-mono numerics, amber for the honest-empty/degraded states.

const INPUT_CLASS =
  "w-full rounded-md border border-slate-700 bg-slate-950/60 px-2.5 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-600";

const NUMERIC_CELL = "px-2 py-1.5 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
const HEADER_CELL = "px-2 py-1 text-right text-[11px] font-medium text-slate-500";
const LABEL_CELL = "px-2 py-1.5 text-left text-xs text-slate-400 whitespace-nowrap";

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

  useEffect(() => {
    let alive = true;
    fetchStrategies().then((result) => {
      if (alive) setStrategiesResult(result);
    });
    fetchProfiles().then((result) => {
      if (alive) setProfilesResult(result);
    });
    return () => {
      alive = false;
    };
  }, []);

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

  return (
    <div className="min-h-screen">
      <main className="mx-auto max-w-7xl px-4 py-6">
        <header className="mb-4">
          <h1 data-testid="structure-title" className="text-lg font-semibold text-slate-200">
            Structure
          </h1>
          <p className="mt-1 max-w-3xl text-sm text-slate-500">
            Deterministic support/resistance levels and A/B/C confluence zones for a chosen symbol
            and as-of time.
          </p>
          <p data-testid="structure-framing" className="mt-2 max-w-3xl text-xs text-slate-600">
            Read-only: every level, zone class, and score below is read verbatim from
            GET /research/levels — nothing here is recomputed in the browser.
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
      </main>
    </div>
  );
}
