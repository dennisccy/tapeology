"use client";

import { useState } from "react";
import { fetchBarSeriesList, fetchLevels } from "@/lib/api";
import type {
  BarSeriesListResult,
  BarSeriesRecord,
  ConfluenceZone,
  LevelsResponse,
} from "@/lib/types";
import { SymbolSearch } from "@/components/SymbolSearch";
import { StructureChart } from "@/components/StructureChart";
import { Panel } from "@/components/Panel";

// The /structure page (J-01) — the era-4 structure stack's first browser home. For a chosen symbol
// + as-of time it renders a price chart with one dashed line per S/R level plus a confluence-zones
// table badged A/B/C. Reached from the new top-bar link, which is served by GET /meta/ui-routes
// (data-driven NavBar — no client hardcoding; see apps/backend/app/meta.py UI_ROUTES). Follows the
// /performance page pattern: client component, no business logic, canonical endpoints read
// verbatim, `{ok, data, error}`-shaped fetch results.
//
// TWO canonical endpoints, rendered VERBATIM and nothing else:
//   * GET /research/levels?symbol=&as_of=  (Data Contract row 39) — levels + confluence zones +
//     the `no_bar_series_for_symbol` honesty flag. The A/B/C badge is `zone.class`, the score is
//     `zone.score` — neither is ever recomputed from breadth or member strength.
//   * GET /research/bars  (Data Contract row 38) — every registered bar series. This is a LIST
//     endpoint with no symbol query param, so this page filters the returned array CLIENT-SIDE by
//     the already-served `symbol` field to find candles for the chart — the SAME filtering
//     discipline NavBar already applies to `nav: true` (filtering already-served rows is not a
//     recomputation of any value). J-02 (strategy registry) and J-03 (backtest comparison) are
//     LATER sections of this same page — not built this iteration.
//
// Four distinct honest states (never share copy, never fabricate a chart/level/zone):
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

export default function StructurePage() {
  const [symbolInput, setSymbolInput] = useState("");
  const [asOfInput, setAsOfInput] = useState("");
  const [levelsState, setLevelsState] = useState<LoadState<LevelsResponse>>({ phase: "idle" });
  const [barsState, setBarsState] = useState<LoadState<BarSeriesListResult>>({ phase: "idle" });

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
      </main>
    </div>
  );
}
