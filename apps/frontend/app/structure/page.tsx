"use client";

import { useEffect, useState } from "react";
import {
  createBacktest,
  fetchBacktest,
  fetchBarSeriesList,
  fetchDatasets,
  fetchEdgeReport,
  fetchLevels,
  fetchPnlLedger,
  fetchProfiles,
  fetchSetupDetail,
  fetchSetups,
  fetchStrategies,
  fetchTradability,
  recordBarSeries,
} from "@/lib/api";
import type {
  Backtest,
  BacktestAggregate,
  BacktestClassAggregate,
  BacktestResult,
  BarSeriesListResult,
  BarSeriesRecord,
  ConfluenceZone,
  Dataset,
  DatasetsListResult,
  EdgeReportCell,
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
  TradabilityResponse,
} from "@/lib/types";
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
//   * GET /research/bars  (Data Contract row 38) — every registered bar series. This is a LIST
//     endpoint with no symbol query param, so this page filters the returned array CLIENT-SIDE by
//     the already-served `symbol` field to find candles for the chart — the SAME filtering
//     discipline NavBar already applies to `nav: true` (filtering already-served rows is not a
//     recomputation of any value).
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

// The era-5 J-05 fetch-control's OWN timeframe set — the SIX Yahoo-supported neutral timeframes
// (goal.md's enumeration), in display order. Deliberately a SUBSET of the backend's full
// `CONFIG.bar_timeframes` (nine entries, mirrored in `TIMEFRAME_ORDER` above): `15m`/`8h`/`1mo` are
// valid `bar_timeframes` entries the Yahoo adapter itself does not map (`UnsupportedTimeframe`) —
// offering them here would let a click reach a statically-known vendor-unsupported 422 the control
// can instead simply never offer. This is a DISPLAY CHOICE (which already-known-good options to
// list), not a second validation authority — the backend's own `bar_timeframes` + Yahoo-adapter
// checks remain the sole enforcement (an out-of-set value still 422s server-side either way).
const YAHOO_TIMEFRAMES = ["1w", "1d", "4h", "1h", "5m", "1m"];

// era-5B J-05 (THIS iteration): the Case Studies reaction filter's <select> options — mirrors
// `research/setups.py`'s own config-owned, pre-registered `REJECTED`/`BROKE`/`CHOPPED` constants
// (route-level enforced by `routes.py`'s `_VALID_REACTIONS`). The SAME `YAHOO_TIMEFRAMES` display-
// choice precedent immediately above: a courtesy option list, never a second validation authority
// — an out-of-set value would still 422 server-side (this page never sends one; the filter is
// applied client-side over the already-served, unfiltered event list — see `handleSetupsFilter*`).
const SETUP_REACTIONS = ["rejected", "broke", "chopped"];

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
function NotComputedPanel({ detail }: { detail: string }) {
  return (
    <div
      data-testid="edge-report-not-computed"
      className="rounded-lg border border-amber-800/60 bg-amber-900/20 px-4 py-6 text-center"
    >
      <p className="text-sm font-medium text-amber-300">Edge report not computed yet.</p>
      <p className="mt-1 text-xs text-amber-200/70">{detail}</p>
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
  const [barsState, setBarsState] = useState<LoadState<BarSeriesListResult>>({ phase: "idle" });

  // era-5B J-01 Tradable Map state (THIS iteration's new default view) — driven by the SAME Load
  // form/button as `levelsState`/`barsState` above (see `handleLoad`), never a second trigger.
  const [tradabilityState, setTradabilityState] = useState<LoadState<TradabilityResponse>>({
    phase: "idle",
  });
  // The raw-levels toggle (era-5B J-05) — OFF by default (the DoD's own requirement); toggling it
  // on renders the pre-existing Levels & Zones section byte-identically to before this iteration.
  const [showRawLevels, setShowRawLevels] = useState(false);

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

  // J-05 fetch-control state — the page's ONE new explicit write action. Independent of
  // `symbolInput`/`asOfInput` above (the pre-existing read-only Load form) until a successful
  // fetch seeds them (see `handleFetchYahoo` below). `fetchError` carries the backend's own
  // 422/503/504/409 `detail` VERBATIM — folded into the shared `UnavailablePanel` treatment, never
  // a single generic message.
  const [fetchSymbolInput, setFetchSymbolInput] = useState("");
  const [fetchTimeframeInput, setFetchTimeframeInput] = useState("");
  const [fetchStartInput, setFetchStartInput] = useState("");
  const [fetchEndInput, setFetchEndInput] = useState("");
  const [fetchSubmitting, setFetchSubmitting] = useState(false);
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
    // era-5B J-04: the 3-way edge report.
    fetchEdgeReport().then((result) => {
      if (alive) setEdgeReportResult(result);
    });
    return () => {
      alive = false;
    };
  }, []);

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

  async function handleLoad(symbol: string, asOf: string) {
    const trimmedSymbol = symbol.trim();
    const trimmedAsOf = asOf.trim();
    if (!trimmedSymbol || !trimmedAsOf) return; // the Load button is already disabled in this case
    setLevelsState({ phase: "loading" });
    setBarsState({ phase: "loading" });
    // era-5B J-01 (THIS iteration): the SAME Load form now also drives the Tradable Map — fetched
    // alongside levels/bars via the SAME Promise.all, never a second trigger.
    setTradabilityState({ phase: "loading" });
    const [levelsResult, barsResult, tradabilityResult] = await Promise.all([
      fetchLevels(trimmedSymbol, trimmedAsOf),
      fetchBarSeriesList(),
      fetchTradability(trimmedSymbol, trimmedAsOf),
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
    setTradabilityState(
      tradabilityResult.ok && tradabilityResult.data
        ? { phase: "ready", data: tradabilityResult.data }
        : {
            phase: "error",
            message: tradabilityResult.error ?? "The tradable map could not be loaded.",
          },
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    handleLoad(symbolInput, asOfInput);
  }

  // J-05: the fetch control's submit — POST /research/bars (store-first: serves-or-fetches, both
  // `200`), then load the fetched symbol/window-end through the EXISTING read path (`handleLoad`)
  // so the Levels & Zones section below renders the real candles + levels + zones with ZERO new
  // rendering code. `symbolInput`/`asOfInput` are updated too, so the pre-existing read-only Load
  // form reflects what is now shown (a manual re-submit of THAT form repeats the same read, never a
  // second write). A failure surfaces the backend's own distinct 422/503/504/409 detail verbatim —
  // nothing is loaded, nothing fabricated.
  async function handleFetchYahoo() {
    const symbol = fetchSymbolInput.trim();
    const timeframe = fetchTimeframeInput;
    const start = fetchStartInput.trim();
    const end = fetchEndInput.trim();
    if (!symbol || !timeframe || !start || !end) return; // the button is already disabled otherwise
    setFetchSubmitting(true);
    setFetchError(null);
    const result = await recordBarSeries({ symbol, timeframe, start, end });
    setFetchSubmitting(false);
    if (!result.ok || !result.bar_series) {
      setFetchError(result.error ?? "The bar series could not be fetched.");
      return;
    }
    setSymbolInput(result.bar_series.symbol);
    setAsOfInput(result.bar_series.window_end_utc);
    await handleLoad(result.bar_series.symbol, result.bar_series.window_end_utc);
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
    fetchTimeframeInput !== "" &&
    fetchStartInput.trim() !== "" &&
    fetchEndInput.trim() !== "";
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

  // era-5B J-01 (THIS iteration): the Tradable Map's OWN candle selection, mirroring
  // `seriesForSymbol`/`representative`/`asOfEpochMs`/`chartBars` above line-for-line but keyed off
  // `tradability` instead of `levels` — kept as a SEPARATE block (never a shared helper) so the
  // raw-levels section above stays byte-identical, untouched code, and so the Tradable Map's own
  // chart renders correctly even in the rare case `GET /research/tradability` and
  // `GET /research/levels` resolve to DIFFERENT honest states for the identical symbol/as-of (e.g.
  // a symbol with levels on a non-daily timeframe but no "1d" series to resolve a tradability
  // basis from — see `tradability.py`'s own docstring).
  const tradability = tradabilityState.phase === "ready" ? tradabilityState.data : null;
  const tradabilitySeriesForSymbol =
    barsState.phase === "ready" && tradability
      ? barsState.data.bar_series.filter((s) => s.symbol === tradability.symbol)
      : [];
  const tradabilityRepresentative = pickRepresentativeSeries(tradabilitySeriesForSymbol);
  const tradabilityAsOfEpochMs = tradability ? Date.parse(tradability.as_of) : NaN;
  const tradabilityChartBars =
    tradabilityRepresentative && !Number.isNaN(tradabilityAsOfEpochMs)
      ? tradabilityRepresentative.bars.filter((b) => b.ts * 1000 <= tradabilityAsOfEpochMs)
      : (tradabilityRepresentative?.bars ?? []);

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
            quality-scored bands, not the full raw level set — browse every historical band-touch
            case with its reaction and tape timeline, and read the 3-way strategy edge report.
          </p>
          <p data-testid="structure-framing" className="mt-2 max-w-3xl text-xs text-slate-600">
            Tradable Map is the default view, read verbatim from GET /research/tradability; toggle
            &quot;Show raw levels&quot; for the underlying S/R levels and confluence zones (off by
            default). Case Studies lists every band-touch event with its reaction, forward returns,
            and — once recorded — its tape timeline; Edge Report compares v1, structure_tape, and
            structure_tape_map over recorded windows, register included. Fetching bars from Yahoo
            Finance below is this page's one explicit write action — everything else, including the
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
          <button
            type="submit"
            data-testid="structure-load-button"
            disabled={!canSubmit}
            className="rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:border-slate-500 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-600 disabled:hover:bg-slate-800"
          >
            Load
          </button>
        </form>

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
              <UnavailablePanel testid="tradable-map-unavailable" message={tradabilityState.message} />
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
                  {barsState.phase === "loading" ? (
                    <LoadingPanel testid="tradable-map-chart-loading" />
                  ) : barsState.phase === "error" ? (
                    <UnavailablePanel
                      testid="tradable-map-chart-unavailable"
                      message={barsState.message}
                    />
                  ) : (
                    <StructureChart
                      key={`tradability|${tradability.symbol}|${tradability.as_of}`}
                      bars={tradabilityChartBars}
                      levels={[]}
                      bands={tradability.bands}
                    />
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
                      {barsState.phase === "loading" ? (
                        <LoadingPanel testid="structure-chart-loading" />
                      ) : barsState.phase === "error" ? (
                        <UnavailablePanel
                          testid="structure-chart-unavailable"
                          message={barsState.message}
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
          </div>
        )}

        {/* era-5B J-02/J-03 (THIS iteration) — the case-study registry: every historical
            band-touch event, filterable by symbol/reaction, with a row drill-in showing the tape
            timeline once a dataset was recorded around that event. */}
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
              <NotComputedPanel detail={edgeReport.detail} />
            ) : (
              <EdgeReportBody report={edgeReport} />
            )}
          </Panel>
        </section>

        {/* era-5 J-05 — the Fetch-from-Yahoo control, repositioned below the three new sections
            above (Foundation invariant: unchanged behavior, only moved). */}
        <section aria-label="Fetch from Yahoo Finance" className="mt-6">
          <Panel title="Fetch from Yahoo Finance">
            <p className="mb-3 -mt-1 max-w-3xl text-xs text-slate-600">
              Fetch a real historical bar series from Yahoo Finance for a symbol, timeframe, and
              UTC date range — keyless, on this explicit click. An already-fetched window is
              served from storage with no repeat network call. On success, the Tradable Map and
              Levels &amp; Zones sections above load the fetched symbol and window automatically.
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
                  Timeframe
                </span>
                <select
                  data-testid="fetch-timeframe-select"
                  value={fetchTimeframeInput}
                  onChange={(e) => setFetchTimeframeInput(e.target.value)}
                  className={INPUT_CLASS}
                >
                  <option value="">Choose…</option>
                  {YAHOO_TIMEFRAMES.map((tf) => (
                    <option key={tf} value={tf}>
                      {tf}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-slate-500">
                  Start (UTC, ISO-8601)
                </span>
                <input
                  data-testid="fetch-start-input"
                  value={fetchStartInput}
                  onChange={(e) => setFetchStartInput(e.target.value)}
                  placeholder="2026-06-01T00:00:00Z"
                  className={INPUT_CLASS}
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-slate-500">
                  End (UTC, ISO-8601)
                </span>
                <input
                  data-testid="fetch-end-input"
                  value={fetchEndInput}
                  onChange={(e) => setFetchEndInput(e.target.value)}
                  placeholder="2026-06-04T00:00:00Z"
                  className={INPUT_CLASS}
                />
              </label>
              <button
                type="submit"
                data-testid="fetch-yahoo-button"
                disabled={!canFetch || fetchSubmitting}
                className="rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:border-slate-500 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-600 disabled:hover:bg-slate-800"
              >
                {fetchSubmitting ? "Fetching…" : "Fetch from Yahoo Finance"}
              </button>
            </form>
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
