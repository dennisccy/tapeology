"use client";

import Link from "next/link";
import { Fragment, useEffect, useRef, useState } from "react";
import {
  cancelDeskForwardCompute,
  cancelDeskReconcileCompute,
  cancelDeskScreenCompute,
  cancelDeskTopupCompute,
  fetchDeskForward,
  fetchDeskForwardCompute,
  fetchDeskReconcileCompute,
  fetchDeskReconcileRuns,
  fetchDeskScreen,
  fetchDeskScreenById,
  fetchDeskScreenCompare,
  fetchDeskScreenCompute,
  fetchDeskScreenPins,
  fetchDeskScreenRuns,
  fetchDeskTopupCompute,
  fetchDeskTopupRuns,
  triggerDeskForwardCompute,
  triggerDeskReconcileCompute,
  triggerDeskScreenCompute,
  triggerDeskTopupCompute,
  triggerDeskUniverseFetch,
} from "@/lib/api";
import type {
  DeskForwardAvgCell,
  DeskForwardComputeSnapshot,
  DeskForwardHorizonMeasure,
  DeskForwardReadResult,
  DeskForwardRecord,
  DeskForwardRow,
  DeskForwardTouch,
  DeskReconcileComputeSnapshot,
  DeskReconcileDrift,
  DeskReconcileRun,
  DeskReconcileRunMeta,
  DeskReconcileRunsListResult,
  DeskScreenCompareResult,
  DeskScreenCompareRow,
  DeskScreenCompareSnapshotMeta,
  DeskScreenComputeSnapshot,
  DeskScreenListResult,
  DeskScreenMeta,
  DeskScreenPinsResult,
  DeskScreenRow,
  DeskScreenRun,
  DeskScreenRunMeta,
  DeskScreenRunsListResult,
  DeskScreenSkip,
  DeskScreenSnapshot,
  DeskTopupComputeSnapshot,
  DeskTopupOutcome,
  DeskTopupRun,
  DeskTopupRunMeta,
  DeskTopupRunsListResult,
} from "@/lib/types";
import { Metric, Panel } from "@/components/Panel";
import { fmt } from "@/lib/format";

// The /desk page (Era B "The Desk" J-04) — the third top-nav page, reached from the persistent
// NavBar (data-driven from GET /meta/ui-routes; no client hardcoding, see apps/backend/app/meta.py
// UI_ROUTES). Renders the LATEST screen snapshot as a dense, descriptive briefing: ranked rows
// (band class/distance/score/coverage/tick-evidence/basis-age, all read verbatim — the "basis"
// column is era-desk-iter-9/J-08, honestly absent as "basis not recorded in this snapshot" on any
// row from a screen recorded before that iteration), an honestly-grouped skipped-members section,
// a provenance line, and a read-only screen-history list. "Run Screen" and "Top-up" wire the
// J-03/J-02 compute managers with live progress + cancel — mirrors the Edge Report Compute button
// UX pattern already shipped on /structure (NotComputedPanel/poll-loop).
//
// FOUR canonical endpoints (three read, one write path split across two triggers), rendered
// VERBATIM and nothing else:
//   * GET  /research/desk/screen          — screen-history list (meta only) + the latest FULL
//     snapshot (rows/skipped/provenance). `latest === null` is the ONE discriminator for the
//     honest "Desk screen not computed yet." empty state — never conflated with a computed screen
//     that skipped every member (`rows: []`, `skipped` non-empty, `latest !== null`).
//   * POST/GET/POST-cancel /research/desk/screen/compute — the screen compute manager
//     (single-flight, pollable progress, cancellable; `screen_date` is always the CLIENT's own
//     today — no date-picker ships this iteration, see assumptions.md iter-4 entry 2).
//   * POST/GET/POST-cancel /research/desk/topup/compute — the bar top-up compute manager (shipped
//     J-02; THIS page is its first-ever UI surface).
// Page-load GETs never trigger a compute (mount issues three GETs only; every POST is an explicit
// button click). Nothing on this page is recomputed in the browser — every rendered value is a
// verbatim re-format of what its owning endpoint already served.
//
// era-desk-iter-6 (J-05): the screen-history list is now interactive. Clicking a past entry issues
// ONE new GET — `/research/desk/screen?date=<screen_date>` (already shipped J-03/iter-3,
// `desk_routes.py:248-266`; this page is its first UI caller) — and renders THAT snapshot's own
// `rows`/`skipped`/provenance in place of the currently-shown one (a read-only display swap, no
// recompute, no route change). A "Latest" control reverts to the top-level `latest` snapshot
// already held in `screenResult` state (no refetch). Every ranked/skip row is also a `Link` to
// `/structure?symbol=<sym>&asof=<displayed snapshot's as_of>` — the era's one sanctioned additive
// edit to `/structure` (its own query-param prefill, see that page's own comment).
//
// era-desk-iter-11 (J-09): a 4th mount-time GET — `/research/desk/topup/runs` — renders a
// read-only, non-interactive "Top-up Runs" panel (no click-through, no new control; the OUT OF
// SCOPE text for this iteration is explicit: read-only disclosure only). PLACEMENT: rendered
// independent of whether a screen has EVER been computed (unlike Screen History, which lives only
// inside the populated-screen view) — a top-up run is a wholly separate operator act from a screen
// run, and the honest-empty/populated states this journey requires (TC-12/TC-13) never presuppose
// a screen exists. This is a deliberate placement choice logged in
// `runs/goal-session-desk/state/assumptions.md` (iter-11 entry), not the plan's own literal
// "immediately after Screen History" suggestion (which that same plan text marks as non-binding).
//
// era-desk-iter-14 (J-10): a THIRD compute manager + a THIRD durable, append-only history section —
// "Index Reconciliation" — repairing the derived `bar_index` against the frozen `BarStore` through
// the existing `BarIndex.reindex()`. A 5th/6th mount-time GET (`/research/desk/coverage/
// reconcile/compute` + `/research/desk/coverage/reconcile/runs`); `ReconcileIndexControl` sits
// beside `ScreenComputeControl`/`TopupComputeControl` in the shared trigger panel (same UX pattern,
// same live-progress-with-cancel shape); the read-only "Index Reconciliation" section is rendered
// unconditionally, immediately after "Top-up runs" — the SAME "independent of screen state"
// placement precedent iter-11 established, since reconciliation touches only the bar store/index,
// never a screen. Page-load GETs still trigger nothing (T-4/5C, unchanged).
//
// goal-desk-iter-16 (J-12): individual addressability + honest ledger disclosure, zero new
// endpoint/section. Screen History selection/highlighting switches from `screen_date`-keyed to
// `id`-keyed (`fetchDeskScreenById`, the new `?id=` read) so an EARLIER same-`screen_date`
// recording — unreachable via `?date=`, which always resolves the newest match — is individually
// openable, and each history row now shows its own `created_utc` so two same-date rows read
// distinctly. Provenance gains the displayed snapshot's own `id`/`created_utc` and, in the
// default (latest) view only, describes itself as the most recently RECORDED screen rather than
// "the latest screen date". The Screen History, Top-up Runs, and Index Reconciliation sections
// each gained a count-plus-filename `IntegrityErrorsNote` whenever that ledger's own
// `integrity_errors` carries an entry — the Universe ledger has no existing frontend section to
// extend (never fetched/rendered on this page today, unlike the plan's premise; see the dev
// handoff's Known Issues).
//
// goal-desk-iter-17 (J-13): a new `band` column on the ranked-rows table (`DeskRow`/
// `DeskRowsTable`), plus one more line on the row's composite drill-in tooltip — the row's own
// `reference_close` (the exact daily close its band selection and `distance_bps` were measured
// against) rendered beside the row's already-recorded `price_low`–`price_high` band range, so
// "the price is inside the wall" is a fact visible on screen instead of arithmetic recovered by
// inverting `distance_bps` against a band edge. Read-only render, zero new endpoint, zero new
// control — `reference_close` rides the already-fetched `GET /research/desk/screen` response.
//
// goal-desk-iter-18 (J-14): a new `opposite` column on the ranked-rows table — the row's own
// `opposite_band` (the nearest band on the side of price the row's selected band did NOT choose),
// rendered beside the existing columns with the same rounded-display split (full precision is not
// carried in the tooltip for this field this iteration — only `bands_by_class` is, see below), an
// honest "no band on the other side" for a recorded `null`, and the established legacy-absent copy
// "opposite wall not recorded in this snapshot" for a pre-iteration row. Plus one more composite
// drill-in tooltip line carrying the row's full-precision `bands_by_class` (a per-class count of
// every band the canonical tradability computation returned for the symbol). Read-only render,
// zero new endpoint, zero new control, zero client-side arithmetic — both fields ride the
// already-fetched `GET /research/desk/screen` response verbatim.
//
// goal-desk-iter-23 (J-15): a new `levels` column on the ranked-rows table — the row's own
// `band_member_count`/`band_member_timeframes` rendered as a tally string (e.g. `155 levels · 1d
// 68 · 1h 57 · 4h 19 · 1w 11`) plus `/structure`'s own "round number" badge (reused verbatim,
// including its `data-testid`/className) when `band_round_number` is true. No new tooltip line —
// every one of the three values is an exact integer or boolean, so there is nothing rounded to
// disclose full precision for. The established legacy-absent copy "composition not recorded in
// this snapshot" covers a pre-iteration row (`band_member_count === undefined`, never a computed
// or inferred fallback from `band_score`/the band range/`bands_by_class`). Read-only render, zero
// new endpoint, zero new control — all three fields ride the already-fetched `GET
// /research/desk/screen` response verbatim.
//
// goal-desk-iter-24 (J-16) — the ranked table's own REFLOW, zero backend diff, zero new value.
// Iter-23's own `UT-07` measured the table at `scrollWidth` 1795px inside a 1214px container (the
// `levels`/`opposite` columns fell entirely off-screen) and each row at ~115px tall (the coverage
// badges wrapped into four lines). This iteration renders the SAME twelve disclosures, plus one
// new `rank` cell (the row's own 1-based position in the served `rows` array -- rendered from the
// `.map` index, never a client-side sort/reorder), inside a `table-fixed` + `<colgroup>` layout
// sized to the page's own `mx-auto max-w-7xl` container: the coverage badges lose their
// `flex-wrap` (one line, not four), the class/distance cells gain the page's own existing chip
// style (`CHIP_CLASS` above), and the five widest disclosure cells (basis/history/band/opposite/
// levels) relax `whitespace-nowrap` so long values wrap onto a second line inside a fixed column
// width instead of stretching the table. Three of those five (basis/history/levels) also drop the
// in-cell label prefix the column header already states; `band ` and `opposite ` KEEP theirs,
// because the stored golden replay scripts J-13.json/J-14.json assert those two cells' literal
// rendered text and TC-6 permits zero script edits (iter-24 review, two CRITICAL findings). Every
// `data-testid`, every honest legacy-absence string ("basis not recorded in this snapshot", etc.),
// and the row's stretched drill-in anchor (`href`, `absolute inset-0`, `data-testid`, composite
// `title`) stay byte-unchanged -- only the layout and three redundant label words moved.
//
// goal-desk-iter-36 (J-21) -- the screen-pin disclosure. Before clicking Run Screen (or before
// reading a past screen's own provenance), the operator sees whether a run right now would reuse
// an already-recorded snapshot or walk the universe fresh -- an 8th mount-time GET (`GET
// /research/desk/screen/pins?screen_date=`), rendered in TWO places, both extensions of already-
// shipped sections (no new section, no new page): (a) `DeskProvenance` gains the pins resolved for
// the DISPLAYED snapshot's own `screen_date`, refetched whenever the displayed snapshot changes
// (mirrors `screenCompareResult`'s own effect, keyed the same way); (b) `ScreenComputeControl`
// gains one descriptive line querying the SAME endpoint for the resolved To day -- the identical value
// the trigger already submits -- so it renders beside the Run Screen button in BOTH the empty-state
// panel and the populated page (the ONE shared component, never duplicated). In both places, the
// served `recorded`-or-`null` answer IS the match/differ statement -- this page computes no
// equality of its own (the J-20 rule; see `assumptions.md` iter-36 entry 1): a non-null `recorded`
// names the snapshot a run would reuse (its own id + recorded-at), a `null` states that no screen
// is recorded under the resolved pins and that a run would walk `members_total` members. Zero new
// ranked-table column, zero change to any existing `data-testid`'s element or text -- purely
// additive disclosure.

const NUMERIC_CELL = "px-2 py-1.5 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
const HEADER_CELL = "px-2 py-1 text-right text-[11px] font-medium text-slate-500";
const HEADER_CELL_LEFT = "px-2 py-1 text-left text-[11px] font-medium text-slate-500";
const LABEL_CELL = "px-2 py-1.5 text-left text-xs text-slate-400 whitespace-nowrap";

// goal-desk-iter-24 (J-16): the ranked table's own reflow, so every disclosure fits the page's
// own `mx-auto max-w-7xl` container at a 1440px viewport with zero horizontal scroll (see the
// comment above `DeskRowsTable`). `WRAP_LABEL_CELL` is `LABEL_CELL` minus `whitespace-nowrap` --
// used ONLY on the five long disclosure cells (basis/history/band/opposite/levels), which now wrap
// onto a second line inside their own `<colgroup>`-fixed column width instead of stretching the
// table wider than its container. `CHIP_CLASS` is the page's OWN existing bordered badge style
// (`desk-coverage-badge`'s non-conditional half, `TickEvidenceBadge`, and the `band_round_number`
// badge already use this exact className) -- reused verbatim, never a new visual effect, for the
// new class/distance chips.
// goal-desk-iter-29 (J-18): a FOURTH durable, append-only history section — "Screen Runs" —
// recording every screen run's own terminal outcome (done/cancelled/failed, reused or not),
// mirroring "Top-up Runs"/"Index Reconciliation"'s exact section shape. A 7th mount-time GET
// (`/research/desk/screen/runs`); the screen-compute poll's OWN terminal tick now also refreshes
// this ledger once (the SAME "on terminal, refresh the durable list" precedent iter-11/iter-14
// established for their own run logs). Rendered unconditionally as the fourth section, immediately
// after "Index Reconciliation" — the SAME "independent of screen state" placement precedent its
// three siblings already establish. No new ranked-table column, no new control: the existing Run
// Screen button simply becomes cheaper on a duplicate-pin retrigger now that the backend resolves
// the five pins before paying for the walk (`desk_screen_compute.py`'s own reuse short-circuit) —
// that behavior change is invisible here beyond the new ledger disclosing it.
const WRAP_LABEL_CELL = "px-1.5 py-1 text-left text-xs text-slate-400 align-top";
// The ranked table's OWN cell padding -- `py-1` (4px, vertical) and `px-1.5` (6px, horizontal)
// instead of the `py-1.5`/`px-2` the shared constants above keep for the history/top-up/
// reconciliation tables. Both numbers are load-bearing measurements, not taste:
//   * `py-1` -- 4px less row height per cell is the difference between a 3-line ranked row
//     measuring 61px (OVER J-16's own <=60px target) and 57px (inside it).
//   * `px-1.5` -- 2px per cell side x 13 columns = 52px of the fixed 1214px container handed back
//     to content instead of gutter, which is what lets the five wrapping disclosure columns hold
//     their values in 3 lines instead of 4-5 (a 4-line row is 73px). The gutter between two
//     columns' text is still 12px.
// Type scale is untouched (`text-xs` body, `text-[11px]` chips/header) and only this one table is
// affected -- `LABEL_CELL`/`NUMERIC_CELL`/`HEADER_CELL`/`HEADER_CELL_LEFT` above stay byte-
// unchanged for the other three tables on this page.
const ROW_LABEL_CELL = "px-1.5 py-1 text-left text-xs text-slate-400 whitespace-nowrap";
const ROW_NUMERIC_CELL = "px-1.5 py-1 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
const ROW_BADGE_CELL = "px-1.5 py-1 text-left";
const ROW_HEADER_CELL = "px-1.5 py-1 text-right text-[11px] font-medium text-slate-500";
const ROW_HEADER_CELL_LEFT = "px-1.5 py-1 text-left text-[11px] font-medium text-slate-500";
const CHIP_CLASS =
  "inline-block whitespace-nowrap rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[11px] text-slate-300";

const PRIMARY_BUTTON_CLASS =
  "rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:border-slate-500 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-600 disabled:hover:bg-slate-800";

const CANCEL_BUTTON_CLASS =
  "mt-1 rounded-md border border-slate-700 bg-transparent px-2.5 py-1 text-xs font-medium text-slate-400 transition-colors hover:border-slate-500 hover:text-slate-200 focus:outline-none focus:ring-1 focus:ring-red-500 disabled:cursor-not-allowed disabled:opacity-50";

// The as-of day text fields (forward-test era) — mirrors structure/page.tsx's own `INPUT_CLASS`
// shape (each page owns its own copy of this tiny constant per this project's established
// convention), narrowed and centered for a bare YYYY-MM-DD value.
const ASOF_INPUT_CLASS =
  "w-36 rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-center font-mono text-xs text-slate-200 placeholder:text-slate-600 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 disabled:cursor-not-allowed disabled:opacity-50";

// The secondary (quieter) button styling for the "Latest" history control — mirrors
// structure/page.tsx's own `SECONDARY_BUTTON_CLASS` byte-for-byte (each page owns its own copy of
// this tiny constant per this project's established convention — see this file's own
// LoadingPanel/UnavailablePanel comment above).
const SECONDARY_BUTTON_CLASS =
  "rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm font-medium text-slate-400 transition-colors hover:border-slate-600 hover:bg-slate-800 hover:text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-950";

// The ranked table's page controls — SECONDARY_BUTTON_CLASS at a smaller scale, PLUS the
// `disabled:` utilities it deliberately lacks (nothing else on this page disables a secondary
// button). On the first and last page one of these is genuinely unavailable, and it has to read
// that way rather than as a live control that does nothing.
const PAGER_BUTTON_CLASS =
  "rounded-md border border-slate-700 bg-slate-900 px-2 py-0.5 text-[11px] font-medium text-slate-400 transition-colors hover:border-slate-600 hover:bg-slate-800 hover:text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-700 disabled:hover:bg-slate-900 disabled:hover:text-slate-400";

// Today's UTC calendar date (YYYY-MM-DD) — the reference day the page's own copy compares against.
// Mirrors /structure's own `todayUtcDate()` helper byte-for-byte (this project's own convention:
// each module owns its tiny formatting helper rather than sharing one — see desk_screen.py's
// `_iso` docstring). UTC, never the browser's local date, so the submitted date always matches
// what the backend's own session-close basis resolves.
function todayUtcDate(): string {
  return new Date().toISOString().slice(0, 10);
}

// The `nth` Sunday of a month as a UTC calendar date — the two US daylight-time boundaries below.
function nthSundayUtc(year: number, monthIndex: number, nth: number): string {
  const first = new Date(Date.UTC(year, monthIndex, 1));
  const toFirstSunday = (7 - first.getUTCDay()) % 7;
  return new Date(Date.UTC(year, monthIndex, 1 + toFirstSunday + (nth - 1) * 7))
    .toISOString()
    .slice(0, 10);
}

// US eastern daylight time runs from the second Sunday of March to the first Sunday of November.
// Date granularity is exact for every value this can influence: both transitions fall on Sundays,
// and `nextTradingStamp` rolls a weekend to Monday whatever the hour, so the close-hour branch is
// never evaluated on a boundary day.
function isUsEasternDaylightDate(day: string): boolean {
  const year = Number(day.slice(0, 4));
  return day >= nthSundayUtc(year, 2, 2) && day < nthSundayUtc(year, 10, 1);
}

// 16:00 US eastern expressed in UTC, on each side of the daylight-time boundary.
const US_CLOSE_HOUR_UTC_DAYLIGHT = 20;
const US_CLOSE_HOUR_UTC_STANDARD = 21;

// The session a run started NOW would be marked up for — the value "Run Screen" submits as
// `screen_date`, and the whole point of `screen_date` being the TRADE day: a screen dated D is
// built from the last completed session before D (`tradability._resolve_basis`), so the useful
// stamp is the next session an operator can still act on, never the one that already closed.
//
// Before that day's US close, that is today; at or after it, and on Saturdays and Sundays, it is
// the next weekday. This keys on the ABSOLUTE close instant, so the operator's own timezone never
// enters the result: preparing at 22:00 in London — an hour after the close, but still the same
// UTC day — correctly stamps tomorrow, which stamping today's UTC date silently got wrong every
// evening.
//
// US market holidays are deliberately NOT modelled. A stamp landing on one records a screen whose
// map is real (the prior session's) and whose own session simply has no bars, which the forward
// measurement already reports as an honest absence rather than a zero.
//
// `now` is a parameter so the boundaries can be exercised deterministically.
function nextTradingStamp(now: Date = new Date()): string {
  const cursor = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()),
  );
  const today = cursor.toISOString().slice(0, 10);
  const closeHour = isUsEasternDaylightDate(today)
    ? US_CLOSE_HOUR_UTC_DAYLIGHT
    : US_CLOSE_HOUR_UTC_STANDARD;
  const isWeekend = cursor.getUTCDay() === 0 || cursor.getUTCDay() === 6;
  if (!isWeekend && now.getUTCHours() < closeHour) return today;
  do {
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  } while (cursor.getUTCDay() === 0 || cursor.getUTCDay() === 6);
  return cursor.toISOString().slice(0, 10);
}

// --- Local loading/unavailable helpers — mirror structure/page.tsx's own LoadingPanel/
// UnavailablePanel verbatim (shape + testid convention); not exported from components/, so each
// page owns its own copy per this project's established convention. ------------------------------

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

function EmptyState({ testid, title }: { testid: string; title: string }) {
  return (
    <div
      data-testid={testid}
      className="flex min-h-[12vh] flex-col items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-8 text-center"
    >
      <span className="text-2xl text-slate-700">∅</span>
      <p className="mt-2 text-sm text-slate-500">{title}</p>
    </div>
  );
}

// --- Coverage badges — one badge per timeframe key PRESENT in the served `coverage` object
// (never a hardcoded timeframe list — the iter-2 lesson: a symbol may hold bars for some pinned
// timeframes and not others; render each honestly). ------------------------------------------------

function DeskCoverageBadges({
  coverage,
}: {
  coverage: Record<string, { has_bars: boolean; latest_window_end_utc: string | null }>;
}) {
  return (
    // goal-desk-iter-24 (J-16): `flex-wrap` dropped -- the four badges now render on ONE line
    // (TC-3), the direct fix for the ~115px row height `UT-07-fail.png` measured (four badges
    // wrapping into four lines).
    <span data-testid="desk-coverage-badges" className="flex flex-nowrap items-center gap-1">
      {Object.entries(coverage).map(([timeframe, tf]) => (
        <span
          key={timeframe}
          data-testid="desk-coverage-badge"
          data-timeframe={timeframe}
          data-has-bars={tf.has_bars}
          title={`window last requested: ${tf.latest_window_end_utc ?? "never"}`}
          className={`inline-block whitespace-nowrap rounded border px-1.5 py-0.5 text-[11px] ${
            tf.has_bars
              ? "border-emerald-800/60 bg-emerald-900/20 text-emerald-300"
              : "border-slate-700 bg-slate-800/40 text-slate-500"
          }`}
        >
          {timeframe}
        </span>
      ))}
    </span>
  );
}

function TickEvidenceBadge({ testid }: { testid: string }) {
  return (
    <span
      data-testid={testid}
      className="inline-block whitespace-nowrap rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[11px] text-slate-300"
    >
      tick evidence
    </span>
  );
}

// --- Briefing table (ranked rows) ------------------------------------------------------------------

// Is every timeframe in a served coverage map reporting no bars? (era-desk-iter-4 audit F2 — the
// footnote below the table explains the row that reads "Class A resistance, 0.4 bps" beside four
// dark badges; this predicate is what decides whether that footnote is on screen at all.)
function hasNoCoverageAtAll(coverage: Record<string, { has_bars: boolean }>): boolean {
  const entries = Object.values(coverage);
  return entries.length > 0 && entries.every((tf) => !tf.has_bars);
}

// era-desk-iter-7 audit F2 fix: the row's stretched drill-in anchor (`absolute inset-0`) paints
// above every cell in the row, including the per-cell `title`s at desk-row-distance/desk-row-score
// and each coverage badge's own `title` -- those became pointer-unreachable the moment the anchor
// started covering the whole row. Rather than touch the anchor's `href`/class/`data-testid` (any
// of which risks J-05's already-passing whole-row click), the full-precision detail those per-cell
// titles carried is composed directly onto the ANCHOR's own `title` instead: hovering ANYWHERE in
// the row now reveals one composite tooltip. Full precision -- never the rounded 2-decimal DISPLAY
// audit F3 chose for scanability (this is a hover detail, not a rendered cell).
// era-desk-iter-9 (J-08): the composite tooltip also carries the row's full-precision basis
// detail -- `row.basis_as_of` untruncated (the visible "basis" cell below shows only the date
// portion for scanability, the SAME rounded-display/full-precision-on-hover split already
// established for distance/score) plus `row.basis_age_days`. A legacy row (recorded before this
// iteration) has BOTH keys absent, not merely `null` -- `== null` (loose equality) catches both
// `undefined` and `null` in one check, per this project's own `fmt()` convention (lib/format.ts).
// era-desk-iter-15 (J-11): the SAME tooltip also carries the row's history-depth detail --
// `row.history_sessions` plus `row.history_start` untruncated (the visible "history" cell below
// shows only the date portion, the SAME rounded-display/full-precision-on-hover split as basis) --
// a legacy row (recorded before this iteration) has both keys absent, `== null` catches both.
// era-desk-iter-17 (J-13): the SAME tooltip also carries the row's full-precision `reference_close`
// beside its own `price_low`/`price_high` band range (the visible "band" cell below shows the
// rounded values, the SAME split as distance/score/basis/history) -- a legacy row (recorded before
// this iteration) has the key absent, `== null` catches both `undefined` and `null`.
// era-desk-iter-18 (J-14): the SAME tooltip also carries the row's full-precision `bands_by_class`
// -- a per-class count of every band the canonical tradability computation returned for the symbol
// (the visible "opposite" cell below shows only the nearest opposite band, never this per-class
// breakdown). A legacy row (recorded before this iteration) has the key entirely absent
// (`undefined`, not `null`) -- `=== undefined` catches exactly that (unlike the `== null` fields
// above, `bands_by_class` itself is never legitimately recorded as `null` on a new row, only absent
// on a legacy one, so the stricter check is the honest one here).
function deskRowDrillInTitle(row: DeskScreenRow): string {
  const coverageLines = Object.entries(row.coverage)
    .map(([timeframe, tf]) => `${timeframe} window last requested: ${tf.latest_window_end_utc ?? "never"}`)
    .join(" · ");
  const basisLine =
    row.basis_as_of == null || row.basis_age_days == null
      ? "basis not recorded in this snapshot"
      : `basis ${row.basis_as_of} (${row.basis_age_days} d before as-of)`;
  const historyLine =
    row.history_sessions == null || row.history_start == null
      ? "history not recorded in this snapshot"
      : `history ${row.history_sessions} sessions from ${row.history_start}`;
  // The band RANGE is recorded on every ranked row of every snapshot ever written (including every
  // pre-iter-17 one), so it renders unconditionally -- only the CLOSE segment falls back when a
  // legacy row has no `reference_close` key (goal.md J-13: "/desk renders their rows with their OWN
  // recorded band range plus the honest 'close not recorded in this snapshot' state").
  const bandLine =
    row.reference_close == null
      ? `band ${row.price_low}–${row.price_high} · close not recorded in this snapshot`
      : `band ${row.price_low}–${row.price_high} · close ${row.reference_close}`;
  const bandsByClassLine =
    row.bands_by_class === undefined
      ? "bands by class not recorded in this snapshot"
      : `bands by class A ${row.bands_by_class.A} · B ${row.bands_by_class.B} · C ${row.bands_by_class.C} · unclassified ${row.bands_by_class.unclassified}`;
  return `distance ${row.distance_bps} bps · score ${row.band_score} · ${basisLine} · ${historyLine} · ${bandLine} · ${bandsByClassLine}${
    coverageLines ? ` · ${coverageLines}` : ""
  }`;
}

// A skipped member has no distance_bps/band_score -- its anchor's tooltip carries ONLY the
// coverage-freshness portion, never a fabricated value for a field that does not exist on that row.
function deskSkipDrillInTitle(skip: DeskScreenSkip): string {
  return Object.entries(skip.coverage)
    .map(([timeframe, tf]) => `${timeframe} window last requested: ${tf.latest_window_end_utc ?? "never"}`)
    .join(" · ");
}

// One ranked row: symbol, side, band-class chip, distance-bps chip, band score, per-timeframe
// coverage badges, tick-evidence badge, basis column (era-desk-iter-9/J-08), history column
// (era-desk-iter-15/J-11) — every value read verbatim from the snapshot. Distance and score are
// DISPLAYED to two decimals (a `0.33523150389608725 bps` cell defeated the scanability the
// briefing exists for — audit F3); the full-precision value is not lost — it is reachable via the
// row's own drill-in anchor's composite `title` (`deskRowDrillInTitle` above, audit F2 fix), never
// a per-cell `title` (iter-7 audit F1: this comment used to claim the opposite). The basis,
// history, and band columns follow the SAME split: a rounded display with the full-precision
// value reachable only via that same composite tooltip. The band-class chip carries the "nearest
// same-class band" caption
// (assumptions.md iter-4 entry 1 — `_select_best_band` itself stays byte-unchanged; this copy
// keeps the chip honest about what the ranking actually selects rather than implying it is the
// symbol's single strongest band).
// `asOf` is the DISPLAYED snapshot's own `as_of` (shared by every row in one screen, never a
// per-row field) — the drill-in target's second query param. The `Link` fills the whole row via
// the "stretched link" pattern (`position: relative` on the `<tr>`, `absolute inset-0` on the
// `<a>`): one real `next/link` anchor, valid nested-in-a-`<td>` markup, clickable anywhere in the
// row — never a raw `<a>` wrapping the `<tr>` directly (invalid HTML) and never `router.push`.
// goal-desk-iter-24 (J-16): `rank` is the row's own 1-based position in the DISPLAYED snapshot's
// served `rows` array -- passed down from `DeskRowsTable`'s own `.map((row, index) => ...)`
// index, never a value this component (or any client-side sort/reorder) computes itself. A plain
// integer, no label implying action/quality/urgency (goal.md J-16 step 2).
function DeskRow({ row, asOf, rank }: { row: DeskScreenRow; asOf: string; rank: number }) {
  return (
    <tr
      data-testid="desk-screen-row"
      data-symbol={row.symbol}
      data-band-class={row.band_class ?? "none"}
      className="relative border-b border-slate-800/60 last:border-b-0 hover:bg-slate-900/40"
    >
      <td className={ROW_NUMERIC_CELL} data-testid="desk-row-rank">
        {rank}
      </td>
      <td className={ROW_LABEL_CELL} data-testid="desk-row-symbol">
        <Link
          href={`/structure?symbol=${encodeURIComponent(row.symbol)}&asof=${encodeURIComponent(asOf)}`}
          data-testid="desk-row-drill-in"
          aria-label={`Open ${row.symbol} in Structure as of ${asOf}`}
          title={deskRowDrillInTitle(row)}
          className="absolute inset-0"
        />
        {row.symbol}
      </td>
      <td className={ROW_LABEL_CELL} data-testid="desk-row-side">
        {row.side}
      </td>
      {/* goal-desk-iter-24 (J-16): the class/distance cells now render inside the page's OWN
          existing chip style (`CHIP_CLASS` -- the same className `TickEvidenceBadge`/the
          `band_round_number` badge already use), with the SAME text either cell rendered before
          this iteration -- every stored golden's text expect stays true. */}
      <td className={ROW_LABEL_CELL} data-testid="desk-row-band-class">
        {row.band_class !== null ? (
          <>
            <span className={CHIP_CLASS}>{`Class ${row.band_class}`}</span>
            <span className="block whitespace-normal text-[11px] text-slate-500">
              nearest same-class band
            </span>
          </>
        ) : (
          <span className={CHIP_CLASS}>Unclassified</span>
        )}
      </td>
      <td className={ROW_NUMERIC_CELL} data-testid="desk-row-distance" title={String(row.distance_bps)}>
        <span className={CHIP_CLASS}>{fmt(row.distance_bps)} bps</span>
      </td>
      <td className={ROW_NUMERIC_CELL} data-testid="desk-row-score" title={String(row.band_score)}>
        {fmt(row.band_score)}
      </td>
      <td className={ROW_BADGE_CELL} data-testid="desk-row-coverage">
        <DeskCoverageBadges coverage={row.coverage} />
      </td>
      <td className={ROW_BADGE_CELL}>
        {row.tick_evidence && <TickEvidenceBadge testid="desk-row-tick-evidence" />}
      </td>
      {/* era-desk-iter-9 (J-08): descriptive only, date portion of `basis_as_of` (full precision
          lives in the row anchor's own composite `title` above -- NEVER a per-cell `title` here,
          the iter-6/iter-7 F2 lesson applied proactively: a per-cell title under the stretched
          `absolute inset-0` anchor is pointer-unreachable). `== null` catches a legacy row's
          ENTIRELY ABSENT keys (`undefined`), not just an explicit `null`.
          goal-desk-iter-24 (J-16): the redundant "basis " label prefix is dropped (the column
          header already states it) and the cell switches to `WRAP_LABEL_CELL` so a long populated
          value wraps onto a second line inside its own fixed column width instead of stretching
          the table -- the honest-absence string itself is untouched. */}
      <td className={WRAP_LABEL_CELL} data-testid="desk-row-basis">
        {row.basis_as_of == null || row.basis_age_days == null
          ? "basis not recorded in this snapshot"
          : `${row.basis_as_of.slice(0, 10)} · ${row.basis_age_days} d before as-of`}
      </td>
      {/* era-desk-iter-15 (J-11): descriptive only, session count + start date (full precision --
          the untruncated `history_start` -- lives in the row anchor's own composite `title` above,
          NEVER a per-cell `title` here, the same F2 lesson the basis column above already applies).
          `== null` catches a legacy row's ENTIRELY ABSENT keys (`undefined`), not just `null`.
          goal-desk-iter-24 (J-16): "history " label prefix dropped, `WRAP_LABEL_CELL` -- same
          reflow as the basis cell above. */}
      <td className={WRAP_LABEL_CELL} data-testid="desk-row-history">
        {row.history_sessions == null || row.history_start == null
          ? "history not recorded in this snapshot"
          : `${row.history_sessions} sessions · from ${row.history_start.slice(0, 10)}`}
      </td>
      {/* era-desk-iter-17 (J-13): the exact price the row's band was measured from, beside its own
          already-recorded price_low-price_high band range -- "the price is inside the wall"
          becomes a legible fact instead of arithmetic recovered by inverting distance_bps against
          a band edge (full precision -- the untruncated reference_close/price_low/price_high --
          lives in the row anchor's own composite title above, NEVER a per-cell title here, the
          same F2 lesson the basis/history columns already apply). `== null` catches a legacy
          row's ENTIRELY ABSENT key (`undefined`), not just an explicit `null` -- and only the
          CLOSE segment falls back: `price_low`/`price_high` are recorded on every ranked row of
          every snapshot ever written, so the range itself always renders (goal-desk-iter-17 audit
          F1). goal-desk-iter-24 (J-16): this cell keeps its "band " label prefix on BOTH branches,
          byte-unchanged -- iter-24's own review caught that J-13.json step 3 asserts the LITERAL
          rendered text "band 488.50–490.91 · close 490.91" through `page.get_by_text` (visible DOM
          text only -- the composite drill-in `title` this word also appears in is invisible to that
          matcher), so dropping it here would fail a stored golden replay with zero script edits
          allowed (TC-6). Only `WRAP_LABEL_CELL` (wrap instead of `whitespace-nowrap`) applies. */}
      <td className={WRAP_LABEL_CELL} data-testid="desk-row-band">
        {row.reference_close == null
          ? `band ${fmt(row.price_low)}–${fmt(row.price_high)} · close not recorded in this snapshot`
          : `band ${fmt(row.price_low)}–${fmt(row.price_high)} · close ${fmt(row.reference_close)}`}
      </td>
      {/* era-desk-iter-18 (J-14): the nearest band on the side of price the row's OWN selected band
          did NOT choose -- descriptive only, rounded display (full precision for this field is not
          carried in the tooltip this iteration; the tooltip instead gains the row's `bands_by_class`
          breakdown, see `deskRowDrillInTitle` above). Three distinguishable states: a populated
          `opposite_band` (`opposite <side> <class> <low>–<high> · <distance> bps`), an honest "no
          band on the other side" for a recorded `null` (the canonical band computation served no band on
          that side at all), and the established legacy-absent copy "opposite wall not recorded in
          this snapshot" for a row from before this iteration (`undefined`, not `null`).
          goal-desk-iter-24 (J-16): this cell keeps its "opposite " label prefix on the populated
          branch, byte-unchanged, for the SAME reason the band cell above does -- J-14.json step 3
          asserts the literal rendered text "opposite resistance A 490.97–494.39 · 1.22 bps" via
          `page.get_by_text`, and TC-6 allows zero script edits. Only `WRAP_LABEL_CELL` applies. */}
      <td className={WRAP_LABEL_CELL} data-testid="desk-row-opposite">
        {row.opposite_band === undefined
          ? "opposite wall not recorded in this snapshot"
          : row.opposite_band === null
            ? "no band on the other side"
            : `opposite ${row.opposite_band.side} ${row.opposite_band.band_class ?? "unclassified"} ${fmt(
                row.opposite_band.price_low
              )}–${fmt(row.opposite_band.price_high)} · ${fmt(row.opposite_band.distance_bps)} bps`}
      </td>
      {/* goal-desk-iter-23 (J-15): what the row's own selected wall is actually made of --
          band_member_count/band_member_timeframes as an exact tally string, plus /structure's own
          "round number" badge (same data-testid/className, reused verbatim) when
          band_round_number is true. Every value here is an exact integer or boolean -- no
          rounding -- so no per-cell title is added (the F2 lesson does not apply: there is no
          full-precision detail to hide behind a hover). `=== undefined` catches a legacy row's
          ENTIRELY ABSENT key (band_member_count is always >= 1 by construction whenever it is
          recorded at all, so it is never legitimately null) -- the same strict check
          bands_by_class already uses.
          goal-desk-iter-24 (J-16): the redundant " levels" label word is dropped from the tally
          (the column header already says "levels"; the count/breakdown itself is unchanged text),
          `WRAP_LABEL_CELL`. */}
      <td className={WRAP_LABEL_CELL} data-testid="desk-row-levels">
        {row.band_member_count === undefined || row.band_member_timeframes === undefined
          ? "composition not recorded in this snapshot"
          : (
              <>
                {`${row.band_member_count} · ${Object.entries(row.band_member_timeframes)
                  .map(([timeframe, count]) => `${timeframe} ${count}`)
                  .join(" · ")}`}{" "}
                {row.band_round_number && (
                  <span
                    data-testid="tradable-band-round-number"
                    className="inline-block whitespace-nowrap rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[11px] text-slate-300"
                  >
                    round number
                  </span>
                )}
              </>
            )}
      </td>
    </tr>
  );
}

// The ranked table renders one contiguous WINDOW of the served order at a time. This is not a
// cap and not a reorder: every served row stays reachable through the pager, the order and
// direction are the snapshot's own, and each rendered rank stays the row's ABSOLUTE position in
// the served array (`pageStart + index + 1`) — so row 11 reads 11, never 1. The two shipped
// display caps on this page (EARLIER_PAIRS_DISPLAY_CAP, SCREEN_COMPARE_ROWS_DISPLAY_CAP) TRUNCATE
// with a disclosure; this one PAGES with a disclosure. Page state lives inside this component and
// is reset by a `key={snapshot.id}` at the call site — a remount, never a twelfth effect.
const RANKED_ROWS_PAGE_SIZE = 10;

function DeskRowsTable({ rows, asOf }: { rows: DeskScreenRow[]; asOf: string }) {
  const uncoveredRanked = rows.filter((row) => hasNoCoverageAtAll(row.coverage)).length;
  const [page, setPage] = useState(1);
  const pageCount = Math.ceil(rows.length / RANKED_ROWS_PAGE_SIZE);
  const pageStart = (page - 1) * RANKED_ROWS_PAGE_SIZE;
  const pageRows = rows.slice(pageStart, pageStart + RANKED_ROWS_PAGE_SIZE);
  return (
    <div className="overflow-x-auto">
      {uncoveredRanked > 0 && (
        <p data-testid="desk-coverage-divergence-note" className="mb-2 text-[11px] text-slate-600">
          {uncoveredRanked} ranked row(s) in this screen show every timeframe badge dark — counted
          over every ranked row the screen served, not only the page shown below. A row&apos;s rank
          comes from the bar store the screen read directly; its coverage badges come from the
          derived bar index — two independent reads, each rendered as served. A dark badge set beside
          a ranked row therefore means the index holds no entry for that pair, not that the screen
          ranked a symbol whose bars it never read.
        </p>
      )}
      {/* The pager appears only when the snapshot has more rows than one page holds, so every
          snapshot small enough to fit renders exactly as it did before the window existed. */}
      {pageCount > 1 && (
        <div data-testid="desk-rows-pagination" className="mb-2 flex items-center gap-3">
          <button
            type="button"
            data-testid="desk-rows-prev-page"
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            disabled={page <= 1}
            className={PAGER_BUTTON_CLASS}
          >
            Previous
          </button>
          <p data-testid="desk-rows-page-note" className="text-[11px] text-slate-500">
            showing {pageStart + 1}–{pageStart + pageRows.length} of {rows.length} ranked rows ·
            page {page} of {pageCount}
          </p>
          <button
            type="button"
            data-testid="desk-rows-next-page"
            onClick={() => setPage((current) => Math.min(pageCount, current + 1))}
            disabled={page >= pageCount}
            className={PAGER_BUTTON_CLASS}
          >
            Next
          </button>
        </div>
      )}
      {/* goal-desk-iter-24 (J-16): `table-fixed` + an explicit `<colgroup>` -- each column takes
          exactly its own assigned width regardless of content, so the table's OWN total width
          (the sum of these thirteen widths) is a fixed, known quantity instead of the browser's
          auto layout expanding to fit each column's widest single-line content (the direct cause
          of iter-23's 1795px `scrollWidth`). The five long disclosure columns pair with
          `WRAP_LABEL_CELL` (no `whitespace-nowrap`) so a value too long for its own column wraps
          onto a second line instead of stretching the table wider than its container.
          Every width below is a MEASURED number, not an estimate: the eight non-wrapping columns
          each hold their own widest rendered content (measured cell-by-cell over the header plus
          all 100 ranked rows of the latest populated screen, with zero overflow past any cell's
          border box), and the remaining width is split across the five wrapping columns so each
          one's longest value lands in 3 text lines -- a 3-line row measures 57px, inside J-16's
          own <=60px target. They sum to 1214px, which is exactly this page's own
          `mx-auto max-w-7xl` container width inside its `Panel` padding at a 1440px viewport, so
          `scrollWidth === clientWidth` and no horizontal scrollbar can appear.
          That measurement predates the page window above and survives it unchanged: because the
          layout is `table-fixed`, column widths are content-independent by construction, so a
          10-row page renders in exactly the same 1214px as all 100 rows did. The window changes
          WHICH rows are on screen, never how wide any column is. */}
      <table data-testid="desk-screen-rows-table" className="w-full table-fixed border-collapse">
        <colgroup>
          <col className="w-[36px]" />
          <col className="w-[52px]" />
          <col className="w-[66px]" />
          <col className="w-[140px]" />
          <col className="w-[96px]" />
          <col className="w-[60px]" />
          <col className="w-[122px]" />
          <col className="w-[87px]" />
          <col className="w-[81px]" />
          <col className="w-[86px]" />
          <col className="w-[96px]" />
          <col className="w-[126px]" />
          <col className="w-[166px]" />
        </colgroup>
        <thead>
          <tr className="border-b border-slate-800">
            <th className={ROW_HEADER_CELL}>rank</th>
            <th className={ROW_HEADER_CELL_LEFT}>symbol</th>
            <th className={ROW_HEADER_CELL_LEFT}>side</th>
            <th className={ROW_HEADER_CELL_LEFT}>class</th>
            <th className={ROW_HEADER_CELL}>distance</th>
            <th className={ROW_HEADER_CELL}>score</th>
            <th className={ROW_HEADER_CELL_LEFT}>coverage</th>
            <th className={ROW_HEADER_CELL_LEFT}>tick evidence</th>
            <th className={ROW_HEADER_CELL_LEFT}>basis</th>
            <th className={ROW_HEADER_CELL_LEFT}>history</th>
            <th className={ROW_HEADER_CELL_LEFT}>band</th>
            <th className={ROW_HEADER_CELL_LEFT}>opposite</th>
            <th className={ROW_HEADER_CELL_LEFT}>levels</th>
          </tr>
        </thead>
        <tbody>
          {pageRows.map((row, index) => (
            <DeskRow key={row.symbol} row={row} asOf={asOf} rank={pageStart + index + 1} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

// --- Skipped-members section — grouped under an honest heading, "no_bars" vs "no_basis" never
// conflated (two distinct, honest absences). ---------------------------------------------------

// Per the goal's own iter-6 assumption (a skipped symbol still drills into `/structure`, which
// honestly shows its own no-bars/empty state there — no fabrication risk): skip rows link exactly
// like ranked rows, same `asOf`, same "stretched link" pattern (see `DeskRow`'s comment above).
function DeskSkipRow({ skip, asOf }: { skip: DeskScreenSkip; asOf: string }) {
  return (
    <tr
      data-testid="desk-skip-row"
      data-symbol={skip.symbol}
      data-reason={skip.reason}
      className="relative border-b border-slate-800/60 last:border-b-0 hover:bg-slate-900/40"
    >
      <td className={LABEL_CELL}>
        <Link
          href={`/structure?symbol=${encodeURIComponent(skip.symbol)}&asof=${encodeURIComponent(asOf)}`}
          data-testid="desk-skip-row-drill-in"
          aria-label={`Open ${skip.symbol} in Structure as of ${asOf}`}
          title={deskSkipDrillInTitle(skip)}
          className="absolute inset-0"
        />
        {skip.symbol}
      </td>
      <td className={LABEL_CELL} data-testid="desk-skip-reason">
        {skip.reason === "no_bars" ? "no bars" : "no basis"}
      </td>
      <td className="px-2 py-1.5 text-left">
        <DeskCoverageBadges coverage={skip.coverage} />
      </td>
      <td className="px-2 py-1.5 text-left">
        {skip.tick_evidence && <TickEvidenceBadge testid="desk-skip-tick-evidence" />}
      </td>
    </tr>
  );
}

function DeskSkipTable({ rows, asOf }: { rows: DeskScreenSkip[]; asOf: string }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-slate-800">
            <th className={HEADER_CELL_LEFT}>symbol</th>
            <th className={HEADER_CELL_LEFT}>reason</th>
            <th className={HEADER_CELL_LEFT}>coverage</th>
            <th className={HEADER_CELL_LEFT}>tick evidence</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((skip) => (
            <DeskSkipRow key={skip.symbol} skip={skip} asOf={asOf} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DeskSkippedSection({ skipped, asOf }: { skipped: DeskScreenSkip[]; asOf: string }) {
  const noBars = skipped.filter((s) => s.reason === "no_bars");
  const noBasis = skipped.filter((s) => s.reason === "no_basis");
  return (
    <div data-testid="desk-skipped-section" className="space-y-4">
      {noBars.length > 0 && (
        <div>
          <h3
            data-testid="desk-skipped-no-bars-heading"
            className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500"
          >
            Skipped — no bars ({noBars.length})
          </h3>
          <DeskSkipTable rows={noBars} asOf={asOf} />
        </div>
      )}
      {noBasis.length > 0 && (
        <div>
          <h3
            data-testid="desk-skipped-no-basis-heading"
            className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500"
          >
            Skipped — no basis session ({noBasis.length})
          </h3>
          <DeskSkipTable rows={noBasis} asOf={asOf} />
        </div>
      )}
    </div>
  );
}

// --- Screen history — a year-at-a-glance calendar over the meta-only `screens` list. era-desk-iter-6
// (J-05): CLICKABLE — selecting a recorded day fetches that exact snapshot
// (`GET /research/desk/screen?id=`) and swaps it into the page's display in place; the click-through
// itself is a same-page state swap, never a navigation, so it stays a plain `onClick` (not a `Link`
// — the `Link`/drill-in requirement below is only for jumping to `/structure`).
//
// goal-desk-iter-16 (J-12): selection/highlighting is `id`-keyed, not `screen_date`-keyed, and each
// cell carries BOTH (`data-screen-id`/`data-screen-date`). `selectedId` highlights the
// currently-displayed snapshot's own id (see `DeskPage`'s `displayedSnapshot?.id`, which covers BOTH
// a selected history entry and the default latest view).
//
// **Why a calendar replaced the table.** The backend now settles one snapshot per date
// (`desk_screen_decision.py`) — under the old 5-pin key a top-up of LATER days' bars re-keyed an
// EARLIER date and wrote a second row for it, and the table's job was largely to tell those
// near-duplicate rows apart by `created_utc`. With a date carrying one snapshot, the useful question
// is which dates the forward test actually covers and where the gaps are, which a list of rows
// answers badly and a year grid answers at a glance. Nothing was lost with the row: the selected
// snapshot's own id, `created_utc` and pins are exactly what the Provenance panel at the foot of
// this page already renders, and per-day counts ride along in each cell's own `title`/`aria-label`.
//
// Days across, months down: twelve rows of a fixed 31 columns, so a gap reads as a gap rather than
// as a shorter row. A day that does not exist in its month (Feb 30) renders as blank space — never
// a dot, which would claim a date that never existed. -----------------------------------------------

const MONTH_LABELS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
] as const;

const CALENDAR_DAYS = Array.from({ length: 31 }, (_, index) => index + 1);

// Literal class strings, never interpolated, so Tailwind's scanner emits them. Fixed-width cells
// in fixed-width columns: a column that stretched to fill the panel turned each recorded day into
// a wide bar and each empty one into a lone dot in a sea of space, which reads as a chart of
// nothing. At `1.5rem` the 31 day columns sit as one compact block a reader takes in at a glance,
// and a year is twelve short rows rather than a 31-row scroll.
const CALENDAR_CELL_BASE =
  "flex h-5 w-full items-center justify-center rounded-sm border font-mono text-[10px] transition-colors";
const CALENDAR_CELL_EMPTY = "border-transparent text-slate-700";
const CALENDAR_CELL_RECORDED =
  "cursor-pointer border-emerald-700/60 bg-emerald-900/40 text-emerald-200 hover:bg-emerald-800/60";
const CALENDAR_CELL_SELECTED =
  "cursor-pointer border-emerald-300 bg-emerald-500/80 font-semibold text-slate-950";
const CALENDAR_AXIS_LABEL = "font-mono text-[10px] text-slate-500";

/** `YYYY-MM-DD` for a plain year/month/day triple — the same zero-padded shape every recorded
 * `screen_date` already uses, built by string formatting rather than by constructing a `Date` (a
 * `new Date(y, m, d)` would be LOCAL time and could land on the neighbouring UTC day). */
function isoDay(year: number, monthIndex: number, day: number): string {
  return `${year}-${String(monthIndex + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

/** Whether `day` exists in that month at all — the one place the grid's blanks come from. */
function isRealDayOfMonth(year: number, monthIndex: number, day: number): boolean {
  return day <= new Date(Date.UTC(year, monthIndex + 1, 0)).getUTCDate();
}

function DeskHistoryDayCell({
  isoDate,
  meta,
  onSelect,
  selected,
}: {
  isoDate: string;
  meta: DeskScreenMeta | undefined;
  onSelect: (id: string) => void;
  selected: boolean;
}) {
  const day = isoDate.slice(8);
  if (meta === undefined) {
    return (
      <button
        type="button"
        data-testid="desk-history-day"
        data-screen-date={isoDate}
        data-has-screen="false"
        disabled
        title={`${isoDate} — no screen recorded`}
        className={`${CALENDAR_CELL_BASE} ${CALENDAR_CELL_EMPTY}`}
      >
        ·
      </button>
    );
  }
  const label =
    `${isoDate} — ${meta.counts.rows} ranked, ${meta.counts.skipped} skipped, ` +
    `recorded ${meta.created_utc}`;
  return (
    <button
      type="button"
      data-testid="desk-history-day"
      data-screen-id={meta.id}
      data-screen-date={isoDate}
      data-has-screen="true"
      data-selected={selected}
      onClick={() => onSelect(meta.id)}
      title={label}
      aria-label={label}
      className={`${CALENDAR_CELL_BASE} ${
        selected ? CALENDAR_CELL_SELECTED : CALENDAR_CELL_RECORDED
      }`}
    >
      {day}
    </button>
  );
}

function DeskHistoryCalendar({
  screens,
  onSelect,
  selectedId,
  shownYear,
  onShowYear,
}: {
  screens: DeskScreenMeta[];
  onSelect: (id: string) => void;
  selectedId: string | null;
  shownYear: number;
  onShowYear: (year: number) => void;
}) {
  if (screens.length === 0) {
    return <EmptyState testid="desk-history-empty" title="No screens recorded yet." />;
  }
  // One snapshot per date is the backend's own rule; keeping the LAST match is the honest tie-break
  // if a stray second copy is ever on disk (`screens` arrives `created_utc`-ascending), and it
  // never hides that copy from the ledger the API serves — it only picks which one this cell opens.
  const byDate = new Map<string, DeskScreenMeta>();
  for (const meta of screens) {
    byDate.set(meta.screen_date, meta);
  }
  const recordedThisYear = screens.filter((meta) =>
    meta.screen_date.startsWith(`${shownYear}-`),
  ).length;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <button
          type="button"
          data-testid="desk-history-prev-year"
          onClick={() => onShowYear(shownYear - 1)}
          className={PAGER_BUTTON_CLASS}
        >
          Previous
        </button>
        <span data-testid="desk-history-year-label" className="font-mono text-sm text-slate-200">
          {shownYear}
        </span>
        <button
          type="button"
          data-testid="desk-history-next-year"
          onClick={() => onShowYear(shownYear + 1)}
          className={PAGER_BUTTON_CLASS}
        >
          Next
        </button>
        <span className="text-xs text-slate-500">
          {recordedThisYear} recorded screen(s) in {shownYear}
        </span>
      </div>
      <div className="overflow-x-auto">
        <div data-testid="desk-history-calendar" className="w-fit">
          <div className="grid grid-cols-[2.5rem_repeat(31,1.5rem)] gap-x-[2px] gap-y-[2px]">
            <span />
            {CALENDAR_DAYS.map((day) => (
              <span key={day} className={`${CALENDAR_AXIS_LABEL} text-center`}>
                {String(day).padStart(2, "0")}
              </span>
            ))}
            {MONTH_LABELS.map((month, monthIndex) => (
              <Fragment key={month}>
                <span className={`${CALENDAR_AXIS_LABEL} text-right`}>{month}</span>
                {CALENDAR_DAYS.map((day) => {
                  if (!isRealDayOfMonth(shownYear, monthIndex, day)) {
                    return <span key={day} />;
                  }
                  const isoDate = isoDay(shownYear, monthIndex, day);
                  const meta = byDate.get(isoDate);
                  return (
                    <DeskHistoryDayCell
                      key={day}
                      isoDate={isoDate}
                      meta={meta}
                      onSelect={onSelect}
                      selected={meta !== undefined && meta.id === selectedId}
                    />
                  );
                })}
              </Fragment>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// --- Top-up run history (era-desk-iter-11, J-09) — a durable, append-only record of every top-up
// run's outcome, read verbatim from `GET /research/desk/topup/runs` and nothing recomputed. Two
// tiers, mirroring the meta-only-list / full-latest split the backend itself serves (the SAME
// split `DeskHistoryCalendar` above uses for screens): `TopupRunsTable` renders every recorded run's
// summary (date + id, universe snapshot, terminal state, attempted-of-total — the ONLY fields the
// meta-only `runs` list carries), and `LatestTopupRunDetail` renders the full per-pair detail
// (per-outcome counts, every failed pair's detail verbatim, the honest unreached-pairs count) for
// the latest run ONLY — the one entry the backend's `latest` field actually carries `outcomes` for.
// Read-only, no click-through, no new control (this iteration's own OUT OF SCOPE text). -----------
//
// goal-desk-iter-26 (J-17): the counts line gains an `unchanged` bucket (a vendor call ran and
// returned only bars already frozen -- distinct from `reused`'s zero-vendor-calls meaning); a new
// descriptive line states how many pairs asked for a tail window vs. the full lookback window
// (`topupWindowBasisCounts` -- a plain tally, nothing derived); and each already-rendered failed
// pair additionally shows its own recorded `requested_window`. A run recorded BEFORE this
// iteration's code shipped lacks all four new fields on every outcome entry -- rendered as the
// honest `WINDOW_BASIS_NOT_RECORDED` fallback, never computed or backfilled. No new section, no
// new control, no new ranked-table column (J-16's measured width contract stays untouched).

function topupOutcomeCounts(outcomes: DeskTopupOutcome[]): {
  reused: number;
  fetched: number;
  unchanged: number;
  failed: number;
} {
  return {
    reused: outcomes.filter((o) => o.outcome === "reused").length,
    fetched: outcomes.filter((o) => o.outcome === "fetched").length,
    unchanged: outcomes.filter((o) => o.outcome === "unchanged").length,
    failed: outcomes.filter((o) => o.outcome === "failed").length,
  };
}

// goal-desk-iter-26 (J-17) -- the honest fallback for a run recorded BEFORE this iteration's code
// shipped: legacy runs never carry `window_basis` on any outcome entry, and the fields are never
// computed or backfilled at read time (the established J-08/J-11/J-13 legacy-absence pattern).
const WINDOW_BASIS_NOT_RECORDED = "window basis not recorded in this run";

// A plain tally of the served payload's own `window_basis` field, nothing derived (the
// `topupOutcomeCounts` precedent) -- `null` when ANY outcome in the run lacks `window_basis`
// (a single shared writer lands a run's outcomes all at once, so a run is either entirely
// pre-iter-26 or entirely post-iter-26 -- never a mix).
function topupWindowBasisCounts(
  outcomes: DeskTopupOutcome[],
): { tail: number; full_lookback: number } | null {
  if (outcomes.some((o) => o.window_basis === undefined)) return null;
  return {
    tail: outcomes.filter((o) => o.window_basis === "tail").length,
    full_lookback: outcomes.filter((o) => o.window_basis === "full_lookback").length,
  };
}

// goal-desk-iter-32 (J-19) -- the actual date each pair's frozen history reaches AFTER the run,
// distinct from `store_frozen_through` (this pair's PRE-fetch value, never rendered standalone on
// this page) and from `window_basis`'s tail/full_lookback tally above: an EXTREME (the newest
// `store_frozen_through_after` across the run's own pairs) plus how many pairs reach it, plus a
// short list of the pairs whose own recorded reach date is earlier than that newest date (or
// `null`) -- a plain read of the served payload, nothing derived from bars (the
// `topupWindowBasisCounts` precedent). `null` when ANY outcome in the run lacks
// `store_frozen_through_after` (a legacy run, pre-iter-32) -- rendered as the honest
// LIBRARY_REACH_NOT_RECORDED fallback, never computed or backfilled.
const LIBRARY_REACH_NOT_RECORDED = "library reach not recorded in this run";

// goal-desk-iter-34 (J-19 fix) -- the "earlier" list renders at most this many rows; the TRUE
// total is preserved separately (`earlierTotal`) so the heading can disclose an honest
// "showing 20 of N" instead of silently truncating or rendering an unbounded, fourteen-screen-tall
// list (the iter-32/33 bug: 303 rows, no cap, no disclosure).
const EARLIER_PAIRS_DISPLAY_CAP = 20;

function topupLibraryReach(
  outcomes: DeskTopupOutcome[],
): {
  newestDate: string | null;
  newestCount: number;
  earlier: { symbol: string; timeframe: string; date: string | null }[];
  earlierTotal: number;
} | null {
  if (outcomes.some((o) => o.store_frozen_through_after === undefined)) return null;
  // goal-desk-iter-34 (J-19 fix) -- one day-truncated grouping key per outcome, derived ONCE
  // (the SAME calendar-day precision the render already displays via `.slice(0, 10)`). Every
  // grouping/comparison decision below reads this key -- never the raw microsecond-precision
  // timestamp -- so a pair recorded a few hours behind another pair on the IDENTICAL calendar day
  // can never be misclassified as "earlier" purely because of its own sub-day precision (the
  // iter-32/33 bug, reproduced live: 202 of 303 pairs shown under "Pairs recorded earlier" printed
  // the SAME day the reach line named as newest).
  const dayKeyed = outcomes.map((o) => ({
    outcome: o,
    day:
      typeof o.store_frozen_through_after === "string"
        ? o.store_frozen_through_after.slice(0, 10)
        : null,
  }));
  const days = dayKeyed.map((d) => d.day).filter((d): d is string => d !== null);
  if (days.length === 0) {
    // Every pair in this run holds no frozen bars at all -- an honest all-null run, never a
    // computed extreme over an empty set.
    return { newestDate: null, newestCount: 0, earlier: [], earlierTotal: 0 };
  }
  const newestDay = days.reduce((max, d) => (d > max ? d : max), days[0]);
  const newestCount = dayKeyed.filter((d) => d.day === newestDay).length;
  // Full precision is kept for the RETURNED `newestDate` (the render already truncates it to a
  // calendar day at display time via `.slice(0, 10)`) -- only the grouping decision above used the
  // truncated key.
  const newestOutcome = dayKeyed.find((d) => d.day === newestDay)!.outcome;
  const earlierAll = dayKeyed
    .filter((d) => d.day !== newestDay)
    .map(({ outcome }) => ({
      symbol: outcome.symbol,
      timeframe: outcome.timeframe,
      date: outcome.store_frozen_through_after ?? null,
    }));
  return {
    newestDate: newestOutcome.store_frozen_through_after ?? null,
    newestCount,
    earlier: earlierAll.slice(0, EARLIER_PAIRS_DISPLAY_CAP),
    earlierTotal: earlierAll.length,
  };
}

function TopupRunRow({ meta }: { meta: DeskTopupRunMeta }) {
  return (
    <tr data-testid="desk-topup-run-row" className="border-b border-slate-800/60 last:border-b-0">
      <td className={LABEL_CELL}>{meta.started_utc.slice(0, 10)}</td>
      <td className={LABEL_CELL} data-testid="desk-topup-run-id">
        {meta.id}
      </td>
      <td className={LABEL_CELL} data-testid="desk-topup-run-state">
        {meta.state}
      </td>
      <td className={NUMERIC_CELL} data-testid="desk-topup-run-attempted">
        {meta.pairs_attempted} / {meta.pairs_total}
      </td>
      <td className={LABEL_CELL} data-testid="desk-topup-run-universe">
        {meta.universe_snapshot_id ?? "—"}
      </td>
    </tr>
  );
}

function TopupRunsTable({ runs }: { runs: DeskTopupRunMeta[] }) {
  if (runs.length === 0) {
    return <EmptyState testid="desk-topup-runs-empty" title="No top-up runs recorded yet." />;
  }
  return (
    <div className="overflow-x-auto">
      <table data-testid="desk-topup-runs-table" className="w-full border-collapse">
        <thead>
          <tr className="border-b border-slate-800">
            <th className={HEADER_CELL_LEFT}>date</th>
            <th className={HEADER_CELL_LEFT}>run</th>
            <th className={HEADER_CELL_LEFT}>state</th>
            <th className={HEADER_CELL}>attempted / total</th>
            <th className={HEADER_CELL_LEFT}>universe snapshot</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((meta) => (
            <TopupRunRow key={meta.id} meta={meta} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

// The latest run's own full detail — attempted-of-total, per-outcome counts, every failed pair's
// detail rendered VERBATIM and legible (never truncated — TC-13 requires it readable in one
// screenshot), and the honest count of pairs the run never reached (`pairs_total -
// pairs_attempted`, zero when the run reached every pair — never rendered as a false "0 not
// reached" claim of completeness the run didn't make; it is simply omitted when zero).
function LatestTopupRunDetail({ run }: { run: DeskTopupRun }) {
  const counts = topupOutcomeCounts(run.outcomes);
  const windowBasisCounts = topupWindowBasisCounts(run.outcomes);
  const libraryReach = topupLibraryReach(run.outcomes);
  const unreached = run.pairs_total - run.pairs_attempted;
  const failedOutcomes = run.outcomes.filter((o) => o.outcome === "failed");
  return (
    <div
      data-testid="desk-topup-run-latest-detail"
      className="mt-4 space-y-3 border-t border-slate-800 pt-4"
    >
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
        Latest run — {run.started_utc.slice(0, 10)} · {run.id}
      </h3>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
        <span data-testid="desk-topup-run-latest-state">state: {run.state}</span>
        <span data-testid="desk-topup-run-latest-attempted">
          {run.pairs_attempted} of {run.pairs_total} pairs attempted
        </span>
        <span data-testid="desk-topup-run-latest-counts">
          {counts.reused} reused · {counts.fetched} fetched · {counts.unchanged} unchanged ·{" "}
          {counts.failed} failed
        </span>
        {unreached > 0 && (
          <span data-testid="desk-topup-run-latest-unreached" className="text-amber-200/70">
            {unreached} pair{unreached === 1 ? "" : "s"} not reached
          </span>
        )}
      </div>
      <div data-testid="desk-topup-run-latest-window-basis" className="text-xs text-slate-400">
        {windowBasisCounts === null
          ? WINDOW_BASIS_NOT_RECORDED
          : `${windowBasisCounts.tail} pair${windowBasisCounts.tail === 1 ? "" : "s"} asked for a ` +
            `tail window · ${windowBasisCounts.full_lookback} pair` +
            `${windowBasisCounts.full_lookback === 1 ? "" : "s"} asked for the full lookback window`}
      </div>
      <div data-testid="desk-topup-run-latest-reach" className="text-xs text-slate-400">
        {libraryReach === null || libraryReach.newestDate === null
          ? LIBRARY_REACH_NOT_RECORDED
          : `newest recorded reach ${libraryReach.newestDate.slice(0, 10)} · ` +
            `${libraryReach.newestCount} pair${libraryReach.newestCount === 1 ? "" : "s"} reach it`}
      </div>
      {libraryReach !== null && libraryReach.earlierTotal > 0 && (
        <div data-testid="desk-topup-run-latest-reach-earlier">
          <h4 className="mb-1 text-[11px] font-medium text-slate-500">
            Pairs recorded earlier ({libraryReach.earlierTotal})
          </h4>
          {libraryReach.earlierTotal > EARLIER_PAIRS_DISPLAY_CAP && (
            <p data-testid="desk-topup-run-latest-reach-earlier-cap" className="mb-1 text-xs text-slate-400">
              showing {libraryReach.earlier.length} of {libraryReach.earlierTotal}
            </p>
          )}
          <ul className="space-y-1">
            {libraryReach.earlier.map((item, index) => (
              <li
                key={`${item.symbol}-${item.timeframe}-${index}`}
                data-testid="desk-topup-run-latest-reach-earlier-row"
                className="text-xs text-slate-400"
              >
                <span className="font-mono text-slate-300">
                  {item.symbol} {item.timeframe}
                </span>{" "}
                — {item.date ? item.date.slice(0, 10) : "no bars recorded"}
              </li>
            ))}
          </ul>
        </div>
      )}
      {failedOutcomes.length > 0 && (
        <div data-testid="desk-topup-run-latest-failed">
          <h4 className="mb-1 text-[11px] font-medium text-slate-500">
            Failed pairs ({failedOutcomes.length})
          </h4>
          <ul className="space-y-1">
            {failedOutcomes.map((outcome, index) => (
              <li
                key={`${outcome.symbol}-${outcome.timeframe}-${index}`}
                data-testid="desk-topup-run-latest-failed-row"
                className="text-xs text-slate-400"
              >
                <span className="font-mono text-slate-300">
                  {outcome.symbol} {outcome.timeframe}
                </span>{" "}
                —{" "}
                <span data-testid="desk-topup-run-latest-failed-detail">
                  {outcome.detail ?? "(no detail recorded)"}
                </span>{" "}
                <span data-testid="desk-topup-run-latest-failed-window" className="text-slate-500">
                  ·{" "}
                  {outcome.requested_window
                    ? `requested ${outcome.requested_window.start.slice(0, 10)} → ` +
                      `${outcome.requested_window.end.slice(0, 10)}`
                    : WINDOW_BASIS_NOT_RECORDED}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// --- Ledger integrity-error disclosure (goal-desk-iter-16, J-12) — a count-plus-filename inline
// note, mirroring `desk-provenance-signature-note`'s plain-text styling (never a new alert/badge
// component). Renders ONLY when the ledger's own payload carries at least one entry — absent
// otherwise, never an empty-array placeholder. Shared across the Screen History, Top-up Runs, and
// Index Reconciliation sections below (each already receives `integrity_errors` verbatim from its
// own GET). ------------------------------------------------------------------------------------

function IntegrityErrorsNote({
  errors,
  testid,
}: {
  errors: { file: string; error: string }[];
  testid: string;
}) {
  if (errors.length === 0) return null;
  return (
    <p data-testid={testid} className="mt-2 text-[11px] text-amber-300">
      {errors.length} file{errors.length === 1 ? "" : "s"} failed an integrity check and{" "}
      {errors.length === 1 ? "is" : "are"} excluded: {errors.map((e) => e.file).join(", ")}
    </p>
  );
}

// The section's own Loading/Unavailable/Populated states — independent of `screenResult` (a
// top-up run's history is a separate concern from a screen's), fed by its own mount-time GET (see
// `DeskPage` below). Mirrors the top-level ternary's exact three-state shape.
function TopupRunsSection({
  result,
}: {
  result: { ok: boolean; data: DeskTopupRunsListResult | null; error?: string } | null;
}) {
  if (result === null) {
    return <LoadingPanel testid="desk-topup-runs-loading" />;
  }
  if (!result.ok || result.data === null) {
    return (
      <UnavailablePanel
        testid="desk-topup-runs-unavailable"
        message={result.error ?? "The top-up run history could not be loaded."}
      />
    );
  }
  return (
    <div>
      <TopupRunsTable runs={result.data.runs} />
      {result.data.latest !== null && <LatestTopupRunDetail run={result.data.latest} />}
      <IntegrityErrorsNote
        errors={result.data.integrity_errors}
        testid="desk-topup-runs-integrity-errors"
      />
    </div>
  );
}

// --- Index reconciliation history (era-desk-iter-14, J-10) — a durable, append-only record of
// every coverage-index reconciliation, read verbatim from `GET /research/desk/coverage/
// reconcile/runs` and nothing recomputed. Mirrors the Top-up Runs split exactly:
// `IndexReconciliationTable` renders every recorded run's summary (date + id, state, series on
// disk, rows indexed before → after — the ONLY fields the meta-only `runs` list carries), and
// `LatestReconciliationDetail` renders the full before/after drift detail + store errors for the
// latest run ONLY — the one entry the backend's `latest` field actually carries them for.
// Read-only, no click-through, no new control beyond the trigger/cancel button (which lives in the
// shared "Run Screen / Top-up / Reconcile Index" panel below, not here). --------------------------

function driftEntryCount(drift: DeskReconcileDrift): number {
  return drift.unindexed_series.length + drift.orphan_index_rows.length + drift.stale_checksum_rows.length;
}

// Every affected pair/row across the three honest buckets, rendered as one flat, labeled list — the
// bucket a row came from is stated inline (never merged into a single unlabeled count) since the
// three buckets mean genuinely different things (a series never indexed vs. an index row with
// nothing on disk vs. an index row whose file the store can no longer verify).
function DriftList({ drift, testid }: { drift: DeskReconcileDrift; testid: string }) {
  const total = driftEntryCount(drift);
  if (total === 0) {
    return (
      <p data-testid={`${testid}-empty`} className="text-xs text-slate-500">
        no drift
      </p>
    );
  }
  return (
    <ul data-testid={testid} className="space-y-0.5">
      {drift.unindexed_series.map((entry) => (
        <li key={`unindexed-${entry.series_id}`} data-testid={`${testid}-entry`} className="text-xs text-slate-400">
          <span className="font-mono text-slate-300">
            {entry.symbol} {entry.timeframe}
          </span>{" "}
          — series on disk, no index row ({entry.series_id})
        </li>
      ))}
      {drift.orphan_index_rows.map((entry) => (
        <li key={`orphan-${entry.series_id}`} data-testid={`${testid}-entry`} className="text-xs text-slate-400">
          <span className="font-mono text-slate-300">{entry.series_id}</span> — index row, no file on disk
        </li>
      ))}
      {drift.stale_checksum_rows.map((entry) => (
        <li key={`stale-${entry.series_id}`} data-testid={`${testid}-entry`} className="text-xs text-slate-400">
          <span className="font-mono text-slate-300">{entry.series_id}</span> — index row, file on disk
          fails its checksum
        </li>
      ))}
    </ul>
  );
}

function IndexReconciliationRunRow({ meta }: { meta: DeskReconcileRunMeta }) {
  return (
    <tr data-testid="desk-reconcile-run-row" className="border-b border-slate-800/60 last:border-b-0">
      <td className={LABEL_CELL}>{meta.started_utc.slice(0, 10)}</td>
      <td className={LABEL_CELL} data-testid="desk-reconcile-run-id">
        {meta.id}
      </td>
      <td className={LABEL_CELL} data-testid="desk-reconcile-run-state">
        {meta.state}
      </td>
      <td className={NUMERIC_CELL} data-testid="desk-reconcile-run-series-on-disk">
        {meta.series_on_disk}
      </td>
      <td className={NUMERIC_CELL} data-testid="desk-reconcile-run-rows-indexed">
        {meta.rows_indexed_before} {"→"} {meta.rows_indexed_after}
      </td>
    </tr>
  );
}

function IndexReconciliationTable({ runs }: { runs: DeskReconcileRunMeta[] }) {
  if (runs.length === 0) {
    return <EmptyState testid="desk-reconcile-runs-empty" title="No reconciliation run recorded yet." />;
  }
  return (
    <div className="overflow-x-auto">
      <table data-testid="desk-reconcile-runs-table" className="w-full border-collapse">
        <thead>
          <tr className="border-b border-slate-800">
            <th className={HEADER_CELL_LEFT}>date</th>
            <th className={HEADER_CELL_LEFT}>run</th>
            <th className={HEADER_CELL_LEFT}>state</th>
            <th className={HEADER_CELL}>series on disk</th>
            <th className={HEADER_CELL}>rows indexed (before {"→"} after)</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((meta) => (
            <IndexReconciliationRunRow key={meta.id} meta={meta} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

// The latest run's own full detail — series on disk, rows indexed before/after, the affected pairs
// in BOTH the before and after drift (after is expected empty for every pair this run repaired —
// rendered as "no drift" when it genuinely is, never hidden), and any store errors (corrupt files)
// verbatim and legible (never truncated).
function LatestReconciliationDetail({ run }: { run: DeskReconcileRun }) {
  return (
    <div
      data-testid="desk-reconcile-run-latest-detail"
      className="mt-4 space-y-3 border-t border-slate-800 pt-4"
    >
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
        Latest run — {run.started_utc.slice(0, 10)} · {run.id}
      </h3>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
        <span data-testid="desk-reconcile-run-latest-state">state: {run.state}</span>
        <span data-testid="desk-reconcile-run-latest-series-on-disk">{run.series_on_disk} series on disk</span>
        <span data-testid="desk-reconcile-run-latest-rows-indexed">
          rows indexed: {run.rows_indexed_before} before, {run.rows_indexed_after} after
        </span>
      </div>
      <div>
        <h4 className="mb-1 text-[11px] font-medium text-slate-500">
          Drift before ({driftEntryCount(run.drift_before)})
        </h4>
        <DriftList drift={run.drift_before} testid="desk-reconcile-run-latest-drift-before" />
      </div>
      <div>
        <h4 className="mb-1 text-[11px] font-medium text-slate-500">
          Drift after ({driftEntryCount(run.drift_after)})
        </h4>
        <DriftList drift={run.drift_after} testid="desk-reconcile-run-latest-drift-after" />
      </div>
      {run.store_errors.length > 0 && (
        <div data-testid="desk-reconcile-run-latest-store-errors">
          <h4 className="mb-1 text-[11px] font-medium text-slate-500">
            Store errors ({run.store_errors.length})
          </h4>
          <ul className="space-y-1">
            {run.store_errors.map((error, index) => (
              <li
                key={`${error.file}-${index}`}
                data-testid="desk-reconcile-run-latest-store-error-row"
                className="text-xs text-slate-400"
              >
                <span className="font-mono text-slate-300">{error.file}</span> —{" "}
                <span data-testid="desk-reconcile-run-latest-store-error-detail">{error.error}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// The section's own Loading/Unavailable/Populated states — mirrors `TopupRunsSection`'s identical
// three-state shape, fed by its own mount-time GET.
function ReconciliationSection({
  result,
}: {
  result: { ok: boolean; data: DeskReconcileRunsListResult | null; error?: string } | null;
}) {
  if (result === null) {
    return <LoadingPanel testid="desk-reconcile-runs-loading" />;
  }
  if (!result.ok || result.data === null) {
    return (
      <UnavailablePanel
        testid="desk-reconcile-runs-unavailable"
        message={result.error ?? "The index reconciliation history could not be loaded."}
      />
    );
  }
  return (
    <div>
      <IndexReconciliationTable runs={result.data.runs} />
      {result.data.latest !== null && <LatestReconciliationDetail run={result.data.latest} />}
      <IntegrityErrorsNote
        errors={result.data.integrity_errors}
        testid="desk-reconcile-runs-integrity-errors"
      />
    </div>
  );
}

// --- Screen run history (goal-desk-iter-29, J-18) — a durable, append-only record of every screen
// run's outcome — including ones that reused an already-recorded snapshot, were cancelled, or
// failed — read verbatim from `GET /research/desk/screen/runs` and nothing recomputed. Mirrors the
// Top-up Runs / Index Reconciliation split exactly: `ScreenRunsTable` renders every recorded run's
// summary (date + id, terminal state, members attempted-of-total, and what it produced — the ONLY
// fields the meta-only `runs` list carries), and `LatestScreenRunDetail` renders the full detail
// (elapsed, ranked/skipped-by-reason counts, verbatim failure detail) for the latest run ONLY — the
// one entry the backend's `latest` field actually carries them for. Read-only, no click-through, no
// new control — the existing Run Screen button above simply becomes cheaper on a duplicate-pin
// retrigger (the backend's own reuse short-circuit); that is not a new control. No new ranked-table
// column, no change to the ranked table (J-16's measured width contract stays untouched). ----------

// A run's own start→finish duration — a plain difference of two ALREADY-RECORDED timestamps (never
// `Date.now()`, unlike `formatComputeElapsed` above which clocks a STILL-RUNNING job): a completed
// run's elapsed time is itself a fixed, deterministic fact once both timestamps are on disk.
function formatScreenRunElapsed(startedUtc: string, finishedUtc: string): string {
  const ms = Date.parse(finishedUtc) - Date.parse(startedUtc);
  if (!Number.isFinite(ms) || ms < 0) return "—";
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return minutes > 0 ? `${minutes}m ${String(seconds).padStart(2, "0")}s` : `${seconds}s`;
}

// The one-line, honest statement of what a run produced -- a freshly-recorded snapshot's own id, a
// reused run's plain "no walk was performed" note, or (cancelled/failed) "nothing recorded" -- never
// a fabricated id for a run that produced none.
function screenRunOutcomeText(meta: DeskScreenRunMeta): string {
  if (meta.state === "done" && meta.reused) {
    return `reused ${meta.screen_id ?? "—"} — no walk was performed`;
  }
  if (meta.state === "done") {
    return meta.screen_id ?? "nothing recorded";
  }
  return "nothing recorded";
}

function ScreenRunRow({ meta }: { meta: DeskScreenRunMeta }) {
  return (
    <tr data-testid="desk-screen-run-row" className="border-b border-slate-800/60 last:border-b-0">
      <td className={LABEL_CELL}>{meta.screen_date}</td>
      <td className={LABEL_CELL} data-testid="desk-screen-run-id">
        {meta.id}
      </td>
      <td className={LABEL_CELL} data-testid="desk-screen-run-state">
        {meta.state}
      </td>
      <td className={NUMERIC_CELL} data-testid="desk-screen-run-attempted">
        {meta.members_attempted} / {meta.members_total}
      </td>
      <td className={LABEL_CELL} data-testid="desk-screen-run-outcome">
        {screenRunOutcomeText(meta)}
      </td>
    </tr>
  );
}

function ScreenRunsTable({ runs }: { runs: DeskScreenRunMeta[] }) {
  if (runs.length === 0) {
    return <EmptyState testid="desk-screen-runs-empty" title="No screen runs recorded yet." />;
  }
  return (
    <div className="overflow-x-auto">
      <table data-testid="desk-screen-runs-table" className="w-full border-collapse">
        <thead>
          <tr className="border-b border-slate-800">
            <th className={HEADER_CELL_LEFT}>date</th>
            <th className={HEADER_CELL_LEFT}>run</th>
            <th className={HEADER_CELL_LEFT}>state</th>
            <th className={HEADER_CELL}>attempted / total</th>
            <th className={HEADER_CELL_LEFT}>produced</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((meta) => (
            <ScreenRunRow key={meta.id} meta={meta} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

// The latest run's own full detail — state, attempted-of-total, elapsed, what it produced (or the
// honest reused/nothing-recorded note), the ranked/skipped-by-reason counts on a completed walk,
// and (state === "failed" only) the raising member's name plus the exception detail rendered
// VERBATIM and legible (never truncated).
function LatestScreenRunDetail({ run }: { run: DeskScreenRun }) {
  const unreached = run.members_total - run.members_attempted;
  return (
    <div
      data-testid="desk-screen-run-latest-detail"
      className="mt-4 space-y-3 border-t border-slate-800 pt-4"
    >
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
        Latest run — {run.screen_date} · {run.id}
      </h3>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
        <span data-testid="desk-screen-run-latest-state">state: {run.state}</span>
        <span data-testid="desk-screen-run-latest-attempted">
          {run.members_attempted} of {run.members_total} members attempted
        </span>
        <span data-testid="desk-screen-run-latest-elapsed">
          {formatScreenRunElapsed(run.started_utc, run.finished_utc)} elapsed
        </span>
        <span data-testid="desk-screen-run-latest-outcome">{screenRunOutcomeText(run)}</span>
        {unreached > 0 && !(run.state === "done" && run.reused) && (
          <span data-testid="desk-screen-run-latest-unreached" className="text-amber-200/70">
            {unreached} member{unreached === 1 ? "" : "s"} not reached
          </span>
        )}
      </div>
      {run.state === "done" && !run.reused && (
        <div data-testid="desk-screen-run-latest-counts" className="text-xs text-slate-400">
          {run.ranked_count} ranked · {run.skipped_by_reason.no_bars} skipped (no bars) ·{" "}
          {run.skipped_by_reason.no_basis} skipped (no basis)
        </div>
      )}
      {run.state === "failed" && (
        <div data-testid="desk-screen-run-latest-failed" className="text-xs text-slate-400">
          <span className="font-mono text-slate-300">
            {run.failed_member ?? "(member not recorded)"}
          </span>{" "}
          —{" "}
          <span data-testid="desk-screen-run-latest-failed-detail">
            {run.error ?? "(no detail recorded)"}
          </span>
        </div>
      )}
    </div>
  );
}

// The section's own Loading/Unavailable/Populated states — mirrors `TopupRunsSection`'s/
// `ReconciliationSection`'s identical three-state shape, fed by its own mount-time GET.
function ScreenRunsSection({
  result,
}: {
  result: { ok: boolean; data: DeskScreenRunsListResult | null; error?: string } | null;
}) {
  if (result === null) {
    return <LoadingPanel testid="desk-screen-runs-loading" />;
  }
  if (!result.ok || result.data === null) {
    return (
      <UnavailablePanel
        testid="desk-screen-runs-unavailable"
        message={result.error ?? "The screen run history could not be loaded."}
      />
    );
  }
  return (
    <div>
      <ScreenRunsTable runs={result.data.runs} />
      {result.data.latest !== null && <LatestScreenRunDetail run={result.data.latest} />}
      <IntegrityErrorsNote
        errors={result.data.integrity_errors}
        testid="desk-screen-runs-integrity-errors"
      />
    </div>
  );
}

// --- Forward returns (forward-test era, v2 touch-anchored) — the read-only surface over the
// append-only forward ledger: for whichever screen snapshot the page currently DISPLAYS, each
// ranked row's intraday touches of its OWN wall during the screen date's session (out-of-sample:
// the wall map's basis reads sessions strictly before the screen date), per touch the modeled
// limit-fill entry, forward moves in PERCENT at trading-bar horizons + to the session close —
// SIGNED to each row's own side by the backend (support long, resistance negated: positive always
// means the wall worked), with the two max drawdowns left unsigned — and server-computed per-row
// averages (untruncated-only pools, truncation counted), a per-side summary of touches BESIDE the
// seeded random-minute baseline (drawn on the SAME sign, so the null is like-for-like),
// and the record's register rendered VERBATIM. Every value is the served payload's own; nothing
// is derived, capped, sorted, or sliced client-side. Clicking a row opens a detail panel BELOW
// the table (the /structure SetupDrillIn separate-panel precedent) rendered from the ALREADY
// loaded record — plain selection state, zero new effects, no fetch. Rendered THIRD on the page,
// directly above the ranked briefing (it originally rendered dead last, for interception safety
// the golden bare-symbol guard now provides instead). The compute is an explicit operator act —
// its own button, its own poll, and (reversed) the Refresh Data chain's fifth step, which measures
// every snapshot that click recorded. Never a page load and never a timer: both entry points are
// a click. ------------------------------------------------------------------------------------------

interface ForwardControlProps {
  compute: DeskForwardComputeSnapshot | null;
  onTrigger: () => void;
  triggering: boolean;
  triggerError: string | null;
  onCancel: () => void;
  cancelRequested: boolean;
  cancelError: string | null;
  screenId: string | null;
}

function DeskForwardComputeControl({
  compute,
  onTrigger,
  triggering,
  triggerError,
  onCancel,
  cancelRequested,
  cancelError,
  screenId,
}: ForwardControlProps) {
  const isRunning = compute?.state === "running";
  const isFailed = compute?.state === "failed";
  const isCancelled = compute?.state === "cancelled";
  const buttonLabel = isRunning ? "Computing…" : isFailed ? "Retry Compute Forward" : "Compute Forward";
  return (
    <div className="flex flex-col items-center gap-1">
      {isFailed && compute?.error && (
        <p data-testid="desk-forward-compute-error" className="text-xs text-red-300">
          {compute.error}
        </p>
      )}
      {triggerError && (
        <p data-testid="desk-forward-compute-trigger-error" className="text-xs text-red-300">
          {triggerError}
        </p>
      )}
      {isCancelled && (
        <p data-testid="desk-forward-compute-cancelled" className="text-xs text-amber-200/70">
          Forward compute cancelled — nothing was recorded this run.
        </p>
      )}
      {compute?.state === "done" && compute.forward_id !== null && (
        <p data-testid="desk-forward-compute-outcome" className="text-xs text-slate-500">
          {compute.reused
            ? `Reused the forward result already recorded for these inputs — ${compute.forward_id}`
            : `Recorded a new forward result — ${compute.forward_id}`}
        </p>
      )}
      {compute !== null && screenId !== null && compute.screen_id !== screenId && (
        <p data-testid="desk-forward-compute-other-screen" className="text-xs text-slate-500">
          The job shown describes {compute.screen_id}, not the snapshot displayed above.
        </p>
      )}
      <button
        type="button"
        data-testid="desk-forward-compute-button"
        onClick={onTrigger}
        disabled={triggering || isRunning || screenId === null}
        className={PRIMARY_BUTTON_CLASS}
      >
        {buttonLabel}
      </button>
      {isRunning && (
        <div data-testid="desk-forward-compute-running" className="mt-1 flex flex-col items-center gap-1">
          <p data-testid="desk-forward-compute-progress" className="text-xs text-amber-200/70">
            <span
              aria-hidden="true"
              className="mr-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400 align-middle"
            />
            {compute.progress.rows_done} / {compute.progress.rows_total} rows
          </p>
          {compute.progress.current && (
            <p data-testid="desk-forward-compute-current" className="text-xs text-amber-200/70">
              current: {compute.progress.current}
            </p>
          )}
          <button
            type="button"
            data-testid="desk-forward-compute-cancel"
            onClick={onCancel}
            disabled={cancelRequested}
            className={CANCEL_BUTTON_CLASS}
          >
            {cancelRequested ? "Cancelling — finishing the current row…" : "Cancel"}
          </button>
          {cancelError && (
            <p data-testid="desk-forward-compute-cancel-error" className="text-xs text-red-300">
              {cancelError}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// The horizon labels this record was measured at, read from its OWN parameters — never a
// hardcoded list, so a record computed under a different horizon set still renders its own.
function forwardHorizonLabels(record: DeskForwardRecord): string[] {
  return record.parameters.horizons_minutes.map(([label]) => label);
}

// Every measure column an averages/summary block serves, in the backend's own serving order
// (DESK_FORWARD_MEASURE_KEYS): the horizon returns, the session-end mark, then each adverse
// excursion at every one of those SAME windows. `mdd_long_1h` is the worst move below entry
// within the hour the `1h` return was measured over; the unsuffixed pair stays the session end.
function forwardMeasureKeys(record: DeskForwardRecord): string[] {
  const labels = forwardHorizonLabels(record);
  return [
    ...labels,
    "to_close",
    ...labels.map((label) => `mdd_long_${label}`),
    "mdd_long",
    ...labels.map((label) => `mdd_short_${label}`),
    "mdd_short",
  ];
}

function forwardMeasureHeader(key: string): string {
  if (key === "to_close") return "avg to close (%)";
  if (key === "mdd_long") return "avg max drawdown to close (long, %)";
  if (key === "mdd_short") return "avg max drawdown to close (short, %)";
  if (key.startsWith("mdd_long_")) return `avg max drawdown ${key.substring(9)} (long, %)`;
  if (key.startsWith("mdd_short_")) return `avg max drawdown ${key.substring(10)} (short, %)`;
  return `avg fwd ${key} (%)`;
}

// The same seven-or-fifteen columns, in the compact form the side×source summary uses.
function forwardMeasureShortHeader(key: string): string {
  if (key === "to_close") return "to close";
  if (key === "mdd_long") return "mdd long close";
  if (key === "mdd_short") return "mdd short close";
  if (key.startsWith("mdd_long_")) return `mdd long ${key.substring(9)}`;
  if (key.startsWith("mdd_short_")) return `mdd short ${key.substring(10)}`;
  return `fwd ${key}`;
}

// The record's own declared sign convention, read VERBATIM from its served parameters. A record
// written before the convention existed carries no key at all — it is reported as raw rather than
// relabelled as something it is not (the numbers on disk are immutable; only the label can be
// honest about them).
const FORWARD_SIDE_RELATIVE = "side_relative";

function forwardSignConvention(record: DeskForwardRecord): string {
  return record.parameters.return_sign_convention ?? "raw";
}

// One line, rendered once above both tables, stating how to READ every directional number below.
// Which sentence shows is a function of the record's own parameters — never an assumption.
function ForwardSignNote({ record }: { record: DeskForwardRecord }) {
  const convention = forwardSignConvention(record);
  const sideRelative = convention === FORWARD_SIDE_RELATIVE;
  return (
    <p
      data-testid="desk-forward-sign-convention"
      className={`text-[11px] ${sideRelative ? "text-slate-400" : "text-amber-200/80"}`}
    >
      {sideRelative ? (
        <>
          The forward columns (
          <span className="text-slate-300">fwd</span> and{" "}
          <span className="text-slate-300">to close</span>) are{" "}
          <span className="text-slate-300">signed to each row&apos;s own side</span> — a support
          wall reads long, a resistance wall reads short — so a positive number always means price
          went the way the wall implied. The two max drawdowns are deliberately unsigned: they stay
          in absolute price direction, so a row&apos;s own adverse excursion is the one matching
          its side (support → long, resistance → short).
        </>
      ) : (
        <>
          This record was computed before the side-relative convention and carries{" "}
          <span className="text-amber-100">raw price moves</span> — on a resistance row a positive
          number means price ROSE, against the wall. Compute again to record it under the current
          convention (
          <span className="font-mono">{convention}</span>).
        </>
      )}
    </p>
  );
}

// One averages cell: the served mean, full detail in the tooltip. n=0 is an honest dash (with
// the truncation count named when that is the whole story).
function ForwardAvgCellView({ cell, measureKey }: { cell: DeskForwardAvgCell | null; measureKey: string }) {
  const avgCell = cell;
  if (avgCell === null || avgCell.n === 0) {
    return (
      <td
        className={ROW_NUMERIC_CELL}
        data-testid={`desk-forward-row-avg-${measureKey}`}
        title={
          avgCell !== null && avgCell.n_truncated > 0
            ? `no untruncated measurements — ${avgCell.n_truncated} truncated at the session end`
            : undefined
        }
      >
        —
      </td>
    );
  }
  return (
    <td
      className={ROW_NUMERIC_CELL}
      data-testid={`desk-forward-row-avg-${measureKey}`}
      title={`n ${avgCell.n} · mean ${String(avgCell.mean_pct)} · median ${String(avgCell.median_pct)} · truncated ${avgCell.n_truncated}`}
    >
      {fmt(avgCell.mean_pct)}
    </td>
  );
}

function DeskForwardRowView({
  row,
  measureKeys,
  selected,
  onSelect,
}: {
  row: DeskForwardRow;
  measureKeys: string[];
  selected: boolean;
  onSelect: () => void;
}) {
  const touchTitle = [
    row.reason ?? "",
    row.touches_beyond_cap > 0 ? `${row.touches_beyond_cap} further touch(es) beyond the recorded cap` : "",
    row.gap_through_before_first_touch
      ? "price gapped entirely beyond the band before the first touch — not counted as a touch"
      : "",
    row.bars_fully_beyond_band > 0 ? `${row.bars_fully_beyond_band} bar(s) entirely beyond the band` : "",
  ]
    .filter((line) => line !== "")
    .join(" · ");
  return (
    <tr
      data-testid="desk-forward-row"
      onClick={onSelect}
      aria-selected={selected}
      className={`cursor-pointer border-t border-slate-800/60 transition-colors hover:bg-slate-800/40 ${
        selected ? "bg-slate-800/60" : ""
      }`}
      title={touchTitle !== "" ? touchTitle : undefined}
    >
      <td className={ROW_BADGE_CELL} data-testid="desk-forward-row-symbol">
        <span className="font-mono text-xs text-slate-200">{row.symbol}</span>
      </td>
      <td className={ROW_BADGE_CELL} data-testid="desk-forward-row-side">
        <span className={CHIP_CLASS}>{row.side}</span>
      </td>
      <td className={ROW_BADGE_CELL} data-testid="desk-forward-row-class">
        <span className={CHIP_CLASS}>{row.band_class === null ? "Unclassified" : `Class ${row.band_class}`}</span>
      </td>
      <td className={ROW_NUMERIC_CELL} data-testid="desk-forward-row-touches">
        {row.touch_count}
        {row.touches_beyond_cap > 0 && (
          <span className="ml-1 text-[10px] text-amber-200/70">+{row.touches_beyond_cap}</span>
        )}
      </td>
      {measureKeys.map((measureKey) => (
        <ForwardAvgCellView key={measureKey} cell={row.averages[measureKey] ?? null} measureKey={measureKey} />
      ))}
    </tr>
  );
}

// The per-touch detail is a TABLE, not a line: every horizon now serves four numbers (the price
// the return was measured to, the return itself, and that horizon's OWN two max drawdowns), and a
// flex-wrapped run of ~23 values per touch is not readable. The exit price is here so the
// arithmetic is checkable rather than asserted — entry, exit and return sit in one row — and each
// horizon's drawdowns describe ITS window, so a 1h return no longer sits beside an excursion
// measured over the remaining session.
//
// Cell shells, hoisted as literal class strings (Tailwind's scanner never sees an interpolation).
const FORWARD_TOUCH_HEAD = "px-1.5 py-1 text-left text-[10px] font-medium text-slate-500";
const FORWARD_TOUCH_GROUP_HEAD =
  "border-l border-slate-800 px-1.5 pt-1 text-center text-[10px] font-medium text-slate-400";
const FORWARD_TOUCH_CELL = "whitespace-nowrap px-1.5 py-1 text-right font-mono text-[11px] text-slate-300";
const FORWARD_TOUCH_CELL_LEFT = "whitespace-nowrap px-1.5 py-1 text-left font-mono text-[11px] text-slate-300";
const FORWARD_TOUCH_CELL_GROUP =
  "whitespace-nowrap border-l border-slate-800 px-1.5 py-1 text-right font-mono text-[11px] text-slate-300";
const FORWARD_TOUCH_CELL_ABSENT = "whitespace-nowrap px-1.5 py-1 text-right font-mono text-[11px] text-slate-600";

// The four cells one horizon group renders. Every number is reached through `touchValue.<the
// served field's own name>` — deliberately, and not merely as a style: that binding is what the
// desk arithmetic guard scans for, so renaming these into local props would route the whole group
// around the one lint that proves the page derives no value of its own.
function ForwardTouchMeasureCells({
  measure,
  returnTitle,
}: {
  measure: DeskForwardHorizonMeasure;
  returnTitle: string;
}) {
  const touchValue = measure;
  // A record written before the exit price and per-horizon drawdowns were measured carries none
  // of them; a horizon finer than its own touch series carries them present-and-null. Both are
  // absences and read as one — never a fabricated zero.
  const absent = touchValue.return_pct === null;
  return (
    <>
      <td
        className={absent ? FORWARD_TOUCH_CELL_ABSENT : FORWARD_TOUCH_CELL_GROUP}
        title={touchValue.reason ?? undefined}
      >
        {touchValue.exit_price === null || touchValue.exit_price === undefined
          ? "—"
          : fmt(touchValue.exit_price)}
      </td>
      <td className={absent ? FORWARD_TOUCH_CELL_ABSENT : FORWARD_TOUCH_CELL} title={returnTitle}>
        {touchValue.return_pct === null ? "—" : fmt(touchValue.return_pct)}
        {touchValue.truncated ? "†" : ""}
      </td>
      <td className={FORWARD_TOUCH_CELL}>
        {touchValue.mdd_long_pct === null || touchValue.mdd_long_pct === undefined
          ? "—"
          : fmt(touchValue.mdd_long_pct)}
      </td>
      <td className={FORWARD_TOUCH_CELL}>
        {touchValue.mdd_short_pct === null || touchValue.mdd_short_pct === undefined
          ? "—"
          : fmt(touchValue.mdd_short_pct)}
      </td>
    </>
  );
}

// The session-end group in the SAME shape as a horizon leaf, so one renderer serves both. Every
// field is a verbatim copy of a served value under a different key — never a derivation.
function forwardCloseMeasure(touch: DeskForwardTouch): DeskForwardHorizonMeasure {
  const touchRow = touch;
  return {
    return_pct: touchRow.to_close_pct,
    exit_price: touchRow.close_price ?? null,
    mdd_long_pct: touchRow.mdd_long_pct,
    mdd_short_pct: touchRow.mdd_short_pct,
    truncated: false, // the session end is where the bars stop, never a truncated horizon
    effective_minutes: touchRow.minutes_to_close,
    reason: null,
  };
}

// A horizon this record never measured at all (a record predating a horizon in its own
// parameters). Present-and-null, matching how the backend writes its own honest absences.
const FORWARD_UNMEASURED_HORIZON: DeskForwardHorizonMeasure = {
  return_pct: null,
  exit_price: null,
  mdd_long_pct: null,
  mdd_short_pct: null,
  truncated: false,
  effective_minutes: null,
  reason: null,
};

// One anchored measurement row — the SHARED renderer for a touch and a baseline anchor (the
// payload shapes are identical; anchors carry entry_kind "close").
function ForwardTouchRow({ touch, labels }: { touch: DeskForwardTouch; labels: string[] }) {
  const touchRow = touch;
  return (
    <tr data-testid="desk-forward-detail-touch" className="border-t border-slate-800/40">
      <td className={FORWARD_TOUCH_CELL_LEFT}>{touchRow.at_utc.substring(11, 19)}Z</td>
      <td className={FORWARD_TOUCH_CELL_LEFT}>{touchRow.entry_kind}</td>
      <td className={FORWARD_TOUCH_CELL} title={String(touchRow.entry_price)}>
        {fmt(touchRow.entry_price)}
      </td>
      {labels.map((label) => {
        const touchValue = touchRow.horizons[label] ?? FORWARD_UNMEASURED_HORIZON;
        return (
          <ForwardTouchMeasureCells
            key={label}
            measure={touchValue}
            returnTitle={
              touchValue.return_pct === null
                ? (touchValue.reason ?? "")
                : `${String(touchValue.return_pct)} · effective ${String(touchValue.effective_minutes)} min`
            }
          />
        );
      })}
      <ForwardTouchMeasureCells
        measure={forwardCloseMeasure(touchRow)}
        returnTitle={`${String(touchRow.to_close_pct)} · ${touchRow.minutes_to_close} min to the session end`}
      />
    </tr>
  );
}

// The touch/anchor table. Two header rows: one group per horizon (plus the session end), each
// spanning its own four columns. ~23 columns fit no viewport, so it scrolls in its OWN container
// — never the page body.
function ForwardTouchTable({
  touches,
  labels,
  testid,
}: {
  touches: DeskForwardTouch[];
  labels: string[];
  testid: string;
}) {
  return (
    <div className="mt-1 overflow-x-auto">
      <table data-testid={testid} className="w-full border-collapse">
        <thead>
          <tr>
            <th className={FORWARD_TOUCH_HEAD} colSpan={3} />
            {[...labels, "close"].map((label) => (
              <th key={label} className={FORWARD_TOUCH_GROUP_HEAD} colSpan={4}>
                {label}
              </th>
            ))}
          </tr>
          <tr className="border-b border-slate-800">
            <th className={FORWARD_TOUCH_HEAD}>time</th>
            <th className={FORWARD_TOUCH_HEAD}>fill</th>
            <th className={`${FORWARD_TOUCH_HEAD} text-right`}>entry</th>
            {[...labels, "close"].map((label) => (
              <Fragment key={label}>
                <th className={`${FORWARD_TOUCH_HEAD} border-l border-slate-800 text-right`}>
                  exit
                </th>
                <th className={`${FORWARD_TOUCH_HEAD} text-right`}>ret %</th>
                <th className={`${FORWARD_TOUCH_HEAD} text-right`}>MDD L %</th>
                <th className={`${FORWARD_TOUCH_HEAD} text-right`}>MDD S %</th>
              </Fragment>
            ))}
          </tr>
        </thead>
        <tbody>
          {touches.map((touch) => (
            <ForwardTouchRow key={touch.at_utc} touch={touch} labels={labels} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DeskForwardDetail({ row, labels }: { row: DeskForwardRow; labels: string[] }) {
  return (
    <div
      data-testid="desk-forward-detail"
      className="rounded border border-slate-800 bg-slate-900/40 px-3 py-2"
    >
      <p className="text-xs text-slate-400">
        <span className="font-mono text-slate-200">{row.symbol}</span>{" "}
        <span className={CHIP_CLASS}>{row.side}</span> band{" "}
        <span className="font-mono">
          {row.band_price_low === null ? "—" : fmt(row.band_price_low)}–
          {row.band_price_high === null ? "—" : fmt(row.band_price_high)}
        </span>
        {row.touch_basis !== null && (
          <span className="ml-2 text-slate-500">
            measured on {row.touch_basis.timeframe} · {row.touch_basis.bars_in_session} bars in the
            session
          </span>
        )}
      </p>
      {row.reason !== null && <p className="mt-1 text-xs text-amber-300">{row.reason}</p>}
      {row.gap_through_before_first_touch && (
        <p className="mt-1 text-[11px] text-amber-200/70">
          price gapped entirely beyond the band before the first touch — a resting order at the
          edge would have filled there, but a gap is not a touch and is disclosed, never counted.
        </p>
      )}
      {row.touches.length === 0 ? (
        <p className="mt-1 text-xs text-slate-500">
          The band was never touched in this session — every cell above is an honest absence.
        </p>
      ) : (
        <ForwardTouchTable
          touches={row.touches}
          labels={labels}
          testid="desk-forward-detail-table"
        />
      )}
      <p className="mt-1 text-[10px] text-slate-600">
        † truncated at the session end · exit is the close the return was measured to · each
        group&apos;s MDD covers that horizon&apos;s own window
      </p>
      {row.baseline_anchors.length > 0 && (
        <details data-testid="desk-forward-detail-baseline" className="mt-2">
          <summary className="cursor-pointer text-[11px] text-slate-500">
            the seeded random-minute anchors this row is compared against ({row.baseline_anchors.length}
            {row.anchors_in_band > 0 ? ` · ${row.anchors_in_band} inside the band` : ""})
          </summary>
          <ForwardTouchTable
            touches={row.baseline_anchors}
            labels={labels}
            testid="desk-forward-detail-baseline-table"
          />
        </details>
      )}
    </div>
  );
}

// The measure cells for ONE summary line (touches or baseline) — shared so the two explicit
// rows above cannot drift apart.
function ForwardSummaryCells({
  record,
  side,
  source,
  measureKeys,
}: {
  record: DeskForwardRecord;
  side: "support" | "resistance";
  source: "touches" | "baseline";
  measureKeys: string[];
}) {
  return (
    <>
      {measureKeys.map((measureKey) => {
        const summaryCell = record.summary[side]?.[measureKey]?.[source] ?? null;
        if (summaryCell === null || summaryCell.n === 0) {
          return (
            <td key={measureKey} className={ROW_NUMERIC_CELL}>
              —
            </td>
          );
        }
        return (
          <td
            key={measureKey}
            className={ROW_NUMERIC_CELL}
            title={`n ${summaryCell.n} · mean ${String(summaryCell.mean_pct)} · median ${String(summaryCell.median_pct)} · truncated ${summaryCell.n_truncated}`}
          >
            n {summaryCell.n} · {fmt(summaryCell.mean_pct)}
          </td>
        );
      })}
    </>
  );
}

function DeskForwardSummaryView({ record }: { record: DeskForwardRecord }) {
  const measureKeys = forwardMeasureKeys(record);
  const sides: Array<"support" | "resistance"> = ["support", "resistance"];
  return (
    <div data-testid="desk-forward-summary" className="overflow-x-auto">
      <p className="mb-1 text-[11px] text-slate-500">
        touches vs the seeded random-minute baseline — mean (%), untruncated pools only. Both
        lines carry the same sign as their side, so a touch row above its baseline row beat a
        random minute of the same session.
      </p>
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            <th className={ROW_HEADER_CELL_LEFT}>side</th>
            <th className={ROW_HEADER_CELL_LEFT}>source</th>
            {measureKeys.map((measureKey) => (
              <th key={measureKey} className={ROW_HEADER_CELL}>
                {forwardMeasureShortHeader(measureKey)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sides.map((side) => (
            <Fragment key={side}>
              <tr data-testid="desk-forward-summary-touches" className="border-t border-slate-800/60">
                <td className={ROW_BADGE_CELL} rowSpan={2}>
                  <span className={CHIP_CLASS}>{side}</span>
                </td>
                <td className={`${ROW_BADGE_CELL} text-[11px] text-slate-300`}>touches</td>
                <ForwardSummaryCells record={record} side={side} source="touches" measureKeys={measureKeys} />
              </tr>
              <tr data-testid="desk-forward-summary-baseline" className="border-t border-slate-800/40">
                <td className={`${ROW_BADGE_CELL} text-[11px] text-slate-500`}>baseline</td>
                <ForwardSummaryCells record={record} side={side} source="baseline" measureKeys={measureKeys} />
              </tr>
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DeskForwardTable({
  record,
  selectedSymbol,
  onSelectSymbol,
}: {
  record: DeskForwardRecord;
  selectedSymbol: string | null;
  onSelectSymbol: (symbol: string) => void;
}) {
  const measureKeys = forwardMeasureKeys(record);
  if (record.rows.length === 0) {
    return (
      <EmptyState
        testid="desk-forward-rows-empty"
        title="No members carry a forward result in this record."
      />
    );
  }
  return (
    <div
      data-testid="desk-forward-table-scroll"
      className="max-h-[26rem] overflow-x-auto overflow-y-auto rounded border border-slate-800"
    >
      <table data-testid="desk-forward-table" className="w-full border-collapse">
        <thead className="sticky top-0 z-10 bg-slate-900">
          <tr>
            <th className={ROW_HEADER_CELL_LEFT}>member</th>
            <th className={ROW_HEADER_CELL_LEFT}>side</th>
            <th className={ROW_HEADER_CELL_LEFT}>class</th>
            <th className={ROW_HEADER_CELL}>touches</th>
            {measureKeys.map((measureKey) => (
              <th key={measureKey} className={ROW_HEADER_CELL}>
                {forwardMeasureHeader(measureKey)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {record.rows.map((row) => (
            <DeskForwardRowView
              key={row.symbol}
              row={row}
              measureKeys={measureKeys}
              selected={row.symbol === selectedSymbol}
              onSelect={() => onSelectSymbol(row.symbol)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DeskForwardSection({
  result,
  control,
  selectedSymbol,
  onSelectSymbol,
}: {
  result: { ok: boolean; data: DeskForwardReadResult | null; error?: string } | null;
  control: ForwardControlProps;
  selectedSymbol: string | null;
  onSelectSymbol: (symbol: string) => void;
}) {
  if (result === null) {
    return <LoadingPanel testid="desk-forward-loading" />;
  }
  if (!result.ok || result.data === null) {
    return (
      <UnavailablePanel
        testid="desk-forward-unavailable"
        message={result.error ?? "The forward record could not be loaded."}
      />
    );
  }
  const record = result.data.forward;
  if (record === null) {
    return (
      <div
        data-testid="desk-forward-not-computed"
        className="rounded-lg border border-amber-800/60 bg-amber-900/20 px-4 py-6 text-center"
      >
        <p className="text-sm font-medium text-amber-300">
          No forward result is recorded for this snapshot.
        </p>
        <p className="mt-1 text-xs text-amber-200/70">
          Compute reads the fine bars recorded for the snapshot&apos;s own session and measures
          every intraday touch of each ranked wall — an explicit operator act, nothing runs on
          page load.
        </p>
        <div className="mt-3 flex justify-center">
          <DeskForwardComputeControl {...control} />
        </div>
      </div>
    );
  }
  const selectedRow =
    selectedSymbol === null
      ? null
      : record.rows.find((candidate) => candidate.symbol === selectedSymbol) ?? null;
  return (
    <div data-testid="desk-forward-section" className="space-y-3">
      <div data-testid="desk-forward-meta" className="grid grid-cols-1 gap-1 sm:grid-cols-3">
        <Metric label="Record" value={record.id} />
        <Metric label="Recorded at" value={record.created_utc} />
        <Metric label="For snapshot" value={record.screen_id} />
      </div>
      <p data-testid="desk-forward-counts" className="text-[11px] text-slate-500">
        {record.rows_with_touches} of {record.rows.length} members touched their wall ·{" "}
        {record.total_touches} touch(es) in all · click a row for every touch and the anchors it
        is compared against
      </p>
      {result.data.versions > 1 && (
        <p data-testid="desk-forward-versions" className="text-[11px] text-slate-500">
          showing the newest recorded result of {result.data.versions} — earlier versions stay on
          file (new bars arriving re-key the inputs; nothing is rewritten)
        </p>
      )}
      <ForwardSignNote record={record} />
      <p data-testid="desk-forward-window-note" className="text-[11px] text-slate-500">
        Touches and every forward number here are measured within the screen date&apos;s own
        session — the wall map itself was built only from sessions before it.
      </p>
      <DeskForwardSummaryView record={record} />
      <DeskForwardTable
        record={record}
        selectedSymbol={selectedSymbol}
        onSelectSymbol={onSelectSymbol}
      />
      {selectedRow !== null && (
        <DeskForwardDetail row={selectedRow} labels={forwardHorizonLabels(record)} />
      )}
      <p
        data-testid="desk-forward-register"
        className="rounded border border-amber-800/60 bg-amber-900/20 px-2 py-1.5 text-[11px] text-amber-200"
      >
        {record.register}
      </p>
      <div className="flex justify-center">
        <DeskForwardComputeControl {...control} />
      </div>
    </div>
  );
}

// --- Screen comparison (goal-desk-iter-35, J-20) — a new read-only disclosure of how the screen
// `/desk` is currently DISPLAYING differs from the screen recorded immediately before it. A pure,
// stateless GET (`GET /research/desk/screen/compare?id=<the displayed screen's own id>`), fed by
// its own mount/id-change effect in the page component below — no new control, no recompute
// trigger (page-load GETs never trigger a compute, T-4/5C). Rendered as the LAST section on the
// page (after Screen Runs, in its own top-level `<section>` below `DeskPopulatedScreen`) so no
// EXISTING golden's own first-visible-match text search can ever resolve into it instead of its
// real target (goal.md step 6) — the section also introduces no attribute/selector any shipped
// golden's click target matches (never `data-screen-id`/`desk-history-row`/`desk-screen-row`/any
// `desk-row-*` testid; every testid here is its own `desk-screen-compare-*` namespace). Every value
// rendered is a verbatim re-format of the compare endpoint's own response; the one client-side
// operation is a plain array slice for the display cap (the shipped `EARLIER_PAIRS_DISPLAY_CAP`
// pattern, `topupLibraryReach` above), never a re-rank, re-score, or client-derived diff.

const SCREEN_COMPARE_ROWS_DISPLAY_CAP = 20;

function ScreenCompareMeta({
  label,
  meta,
  testid,
}: {
  label: string;
  meta: DeskScreenCompareSnapshotMeta;
  testid: string;
}) {
  return (
    <div data-testid={testid} className="text-xs text-slate-400">
      <p className="text-slate-300">{label}</p>
      <p data-testid={`${testid}-id`}>id {meta.id}</p>
      <p data-testid={`${testid}-dates`}>
        screen date {meta.screen_date} · recorded {meta.created_utc}
      </p>
      <p data-testid={`${testid}-signature`}>bar-store signature {meta.bar_store_signature}</p>
    </div>
  );
}

// Every cell renders the served value verbatim; a `null` field is only ever reached on an
// "entered"/"left" row (the symbol has no row at all on that side — `side`/`distance_bps` have
// carried no legacy-absence case since J-03's very first shipment), so the honest copy names WHICH
// snapshot has no row for this symbol — the J-08/J-13/J-14 legacy-absence phrasing pattern, applied
// here to a structurally-absent row rather than an omitted field on an existing one.
function ScreenCompareRowView({ row }: { row: DeskScreenCompareRow }) {
  const compareRankText = row.compare_rank ?? "not recorded in the compared snapshot";
  const baseRankText = row.base_rank ?? "not recorded in the base snapshot";
  const compareSideText = row.compare_side ?? "not recorded in the compared snapshot";
  const baseSideText = row.base_side ?? "not recorded in the base snapshot";
  const compareDistanceText =
    row.compare_distance_bps == null
      ? "not recorded in the compared snapshot"
      : fmt(row.compare_distance_bps);
  const baseDistanceText =
    row.base_distance_bps == null ? "not recorded in the base snapshot" : fmt(row.base_distance_bps);
  return (
    <tr
      data-testid="desk-screen-compare-row"
      className="border-b border-slate-800/60 last:border-b-0"
    >
      <td className={LABEL_CELL} data-testid="desk-screen-compare-row-symbol">
        {row.symbol}
      </td>
      <td className={LABEL_CELL} data-testid="desk-screen-compare-row-status">
        {row.status}
      </td>
      <td className={NUMERIC_CELL} data-testid="desk-screen-compare-row-compare-rank">
        {compareRankText}
      </td>
      <td className={NUMERIC_CELL} data-testid="desk-screen-compare-row-base-rank">
        {baseRankText}
      </td>
      <td className={NUMERIC_CELL} data-testid="desk-screen-compare-row-rank-change">
        {row.rank_change ?? "—"}
      </td>
      <td className={LABEL_CELL} data-testid="desk-screen-compare-row-compare-side">
        {compareSideText}
      </td>
      <td className={LABEL_CELL} data-testid="desk-screen-compare-row-base-side">
        {baseSideText}
      </td>
      <td className={NUMERIC_CELL} data-testid="desk-screen-compare-row-compare-distance">
        {compareDistanceText}
      </td>
      <td className={NUMERIC_CELL} data-testid="desk-screen-compare-row-base-distance">
        {baseDistanceText}
      </td>
    </tr>
  );
}

// The capped table of the COMPARE snapshot's own first N rows (goal.md step 5, the shipped
// `EARLIER_PAIRS_DISPLAY_CAP` pattern) — "left" rows describe symbols the compare snapshot never
// ranked at all, so they are excluded from "the compare snapshot's own first N rows" and never
// counted toward the cap. Order is rendered EXACTLY as `rows` already carries it (the compare
// snapshot's own served rank order) — no `.sort(`/`.reverse(` of any kind, only a `.slice(` for the
// cap (never applied to a variable literally named `rows`, so this table's own cap can never be
// mistaken for a client-side reorder of the ranked briefing table above).
function ScreenCompareTable({ rows }: { rows: DeskScreenCompareRow[] }) {
  const compareOrdered = rows.filter((entry) => entry.status !== "left");
  if (compareOrdered.length === 0) {
    return (
      <EmptyState
        testid="desk-screen-compare-rows-empty"
        title="No members ranked in the compared snapshot."
      />
    );
  }
  const shown = compareOrdered.slice(0, SCREEN_COMPARE_ROWS_DISPLAY_CAP);
  return (
    <div>
      {compareOrdered.length > SCREEN_COMPARE_ROWS_DISPLAY_CAP && (
        <p data-testid="desk-screen-compare-cap-note" className="mb-1 text-xs text-slate-400">
          showing {shown.length} of {compareOrdered.length} rows
        </p>
      )}
      <table data-testid="desk-screen-compare-table" className="w-full border-collapse">
        <thead>
          <tr>
            <th className={HEADER_CELL_LEFT}>symbol</th>
            <th className={HEADER_CELL_LEFT}>status</th>
            <th className={HEADER_CELL}>rank (this)</th>
            <th className={HEADER_CELL}>rank (base)</th>
            <th className={HEADER_CELL}>rank change</th>
            <th className={HEADER_CELL_LEFT}>side (this)</th>
            <th className={HEADER_CELL_LEFT}>side (base)</th>
            <th className={HEADER_CELL}>distance (this)</th>
            <th className={HEADER_CELL}>distance (base)</th>
          </tr>
        </thead>
        <tbody>
          {shown.map((row) => (
            <ScreenCompareRowView key={row.symbol} row={row} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

// The section's own Loading/Unavailable/Populated states — mirrors `TopupRunsSection`'s/
// `ScreenRunsSection`'s identical three-state shape, fed by its own mount/id-change effect in the
// page component below. `data.compare === null` (an unresolved id) folds into the SAME Unavailable
// rendering as a genuine fetch failure — this page never requests a compare for anything other
// than the screen it is already displaying, so an honest "not found" here would only ever mean a
// stale/raced fetch, not a state an operator can act on.
function ScreenComparisonSection({
  result,
}: {
  result: { ok: boolean; data: DeskScreenCompareResult | null; error?: string } | null;
}) {
  if (result === null) {
    return <LoadingPanel testid="desk-screen-compare-loading" />;
  }
  if (!result.ok || result.data === null || result.data.compare === null) {
    return (
      <UnavailablePanel
        testid="desk-screen-compare-unavailable"
        message={result.error ?? "The screen comparison could not be loaded."}
      />
    );
  }
  const { compare, base, rows, identical, counts } = result.data;
  return (
    <div data-testid="desk-screen-compare-section" className="space-y-3">
      <ScreenCompareMeta
        label="This screen"
        meta={compare}
        testid="desk-screen-compare-meta-compare"
      />
      {base === null ? (
        <p data-testid="desk-screen-compare-no-earlier" className="text-sm text-slate-400">
          No earlier recorded screen exists to compare against.
        </p>
      ) : (
        <>
          <ScreenCompareMeta label="Compared against" meta={base} testid="desk-screen-compare-meta-base" />
          <p data-testid="desk-screen-compare-counts" className="text-xs text-slate-400">
            rows compared {counts.compared} · rank changed {counts.rank_changed} · side changed{" "}
            {counts.side_changed} · entered {counts.entered} · left {counts.left}
          </p>
          {identical ? (
            <p data-testid="desk-screen-compare-identical" className="text-sm text-slate-300">
              The compared snapshots&apos; ranked rows are identical.
            </p>
          ) : (
            <ScreenCompareTable rows={rows} />
          )}
        </>
      )}
    </div>
  );
}

// --- Provenance line — snapshot id + recorded-at time, universe snapshot id + date, as_of,
// config_fingerprint, and the pinned bar-store signature. -------------------------------------
//
// The signature's LABEL (era-desk-iter-4 audit F1): `bar_store_signature` is a checksum —
// `sha256(sorted (symbol, timeframe, latest_window_end_utc) tuples)[:16]` (desk_screen.py) — not a
// timestamp. Labelling it "Window last requested" (as this line first shipped, following the spec
// and blueprint wording verbatim) put a false claim on a hex digest: the operator read
// "Window last requested  d7bc8f8127904d0a". The freshness LABEL belongs to the value that really
// is a window end — each coverage badge's own `latest_window_end_utc` tooltip, which keeps it. Here
// the honest name is the signature's own, with a caption saying what it summarizes. The blueprint's
// registered wording is amended in the same commit.
//
// goal-desk-iter-16 (J-12): `id`/`created_utc` (a straight re-format of fields `DeskScreenSnapshot`
// already carries — nothing derived) name EXACTLY which of possibly several same-date recordings is
// on screen. `isViewingLatest` gates a default-view-only note: while showing `latest`
// (`created_utc`-sorted newest recording, TC-12), the copy describes itself as "the most recently
// recorded screen", never "the latest screen date" — a same-date recording can still exist earlier
// and be reachable from Screen History above (this line now renders dead last on the page).
// goal-desk-iter-36 (J-21): the resolved-pins block appended to `DeskProvenance` below -- the pins
// a run for THIS DISPLAYED snapshot's own `screen_date` would resolve right now, fetched via
// `GET /research/desk/screen/pins`. `recorded === null` here means the DISPLAYED snapshot's own
// key no longer matches what would resolve today (a "differ" state -- see the top-of-file comment
// for why the page itself computes no separate match/differ equality).
function DeskProvenancePins({
  pins,
}: {
  pins: { ok: boolean; data: DeskScreenPinsResult | null; error?: string } | null;
}) {
  if (pins === null) {
    return <p data-testid="desk-provenance-pins-loading" className="mt-2 text-[11px] text-slate-600">
      Resolving the pins a run would use right now…
    </p>;
  }
  if (!pins.ok || pins.data === null) {
    return (
      <p data-testid="desk-provenance-pins-unavailable" className="mt-2 text-[11px] text-amber-300">
        {pins.error ?? "The pins that would resolve right now could not be loaded."}
      </p>
    );
  }
  // A screen only ever exists once a universe does (snapshots are never deleted -- Anti-goals'
  // append-only rail), so `data.universe_snapshot_id` is never null here in practice; no separate
  // empty-state branch is needed (the "differ" branch below already renders correctly on an all-
  // null payload, see the module docstring precedent in `desk_screen_pins.py`).
  const { data } = pins;
  return (
    <div data-testid="desk-provenance-pins" className="mt-2 border-t border-slate-800 pt-2">
      <p className="text-[11px] font-medium text-slate-500">Pins resolved right now for this screen date</p>
      <Metric label="Universe snapshot (resolved now)" value={data.universe_snapshot_id ?? "—"} />
      <Metric label="Config fingerprint (resolved now)" value={data.config_fingerprint} />
      <Metric label="Bar-store signature (resolved now)" value={data.bar_store_signature ?? "—"} />
      {data.recorded !== null ? (
        <p data-testid="desk-provenance-pins-match" className="mt-1 text-[11px] text-slate-400">
          A screen is recorded under these exact pins — {data.recorded.id}, recorded{" "}
          {data.recorded.created_utc}.
        </p>
      ) : (
        <p data-testid="desk-provenance-pins-differ" className="mt-1 text-[11px] text-slate-400">
          No screen is recorded under the pins that resolve right now for this date — a run would
          walk {data.members_total} members.
        </p>
      )}
    </div>
  );
}

function DeskProvenance({
  snapshot,
  isViewingLatest,
  pins,
}: {
  snapshot: DeskScreenSnapshot;
  isViewingLatest: boolean;
  pins: { ok: boolean; data: DeskScreenPinsResult | null; error?: string } | null;
}) {
  return (
    <div data-testid="desk-provenance">
      <Metric label="Snapshot id" value={snapshot.id} />
      <Metric label="Recorded at" value={snapshot.created_utc} />
      <Metric label="Universe snapshot" value={snapshot.universe_snapshot_id ?? "—"} />
      <Metric label="Screen date" value={snapshot.screen_date} />
      <Metric label="As of" value={snapshot.as_of} />
      <Metric label="Config fingerprint" value={snapshot.config_fingerprint} />
      <Metric label="Bar-store signature" value={snapshot.bar_store_signature} />
      {isViewingLatest && (
        <p data-testid="desk-provenance-latest-note" className="mt-1 text-[11px] text-slate-600">
          This is the most recently recorded screen (by recorded-at time), not necessarily the
          latest screen date — an earlier same-date recording can still exist and be opened from
          Screen History above.
        </p>
      )}
      <p data-testid="desk-provenance-signature-note" className="mt-1 text-[11px] text-slate-600">
        The bar-store signature is a checksum over every member&apos;s window-last-requested
        timestamp at the moment this screen was computed — a pin, never a time. Each coverage
        badge&apos;s tooltip carries that member&apos;s own window-last-requested value.
      </p>
      <DeskProvenancePins pins={pins} />
    </div>
  );
}

// --- Run Screen / Top-up controls — mirrors /structure's NotComputedPanel Compute-button UX
// pattern (live progress with a pulsing dot, a Cancel control while running, error/cancelled
// copy) applied to two independent compute managers. Kept as two separate, non-generic
// components (rather than one shared abstraction) since their progress shapes genuinely differ
// (members vs pairs+outcomes) — this project's own simplicity convention. --------------------------

// goal-desk-iter-36 (J-21): the descriptive line beside the Run Screen control, querying
// `GET /research/desk/screen/pins` for the RESOLVED To day -- the SAME value
// `handleTriggerScreen`'s no-arg form submits to the trigger (below; blank inputs resolve to the
// upcoming US session date). Renders in BOTH places `ScreenComputeControl`
// itself renders, since it lives inside that ONE shared component -- no duplication. Honest empty
// state (T-11): before any universe snapshot is registered, `data.universe_snapshot_id` is `null`
// and this renders that fact plainly. The five testids are pinned by golden J-21 (existence-only)
// and stay byte-identical; only the day-copy varies, keyed off the SERVED payload's own
// `screen_date` (a mid-edit hold stays honest about which day it answers for).
function TodayScreenPinsNote({
  pins,
  runDay,
}: {
  pins: { ok: boolean; data: DeskScreenPinsResult | null; error?: string } | null;
  runDay: string | null;
}) {
  const pendingIsToday = runDay === null || runDay === todayUtcDate();
  if (pins === null) {
    return (
      <p data-testid="desk-run-screen-pins-loading" className="text-[11px] text-slate-600">
        {pendingIsToday
          ? "Resolving whether today's pins would reuse a recorded screen…"
          : `Resolving whether the pins for ${runDay} would reuse a recorded screen…`}
      </p>
    );
  }
  if (!pins.ok || pins.data === null) {
    return (
      <p data-testid="desk-run-screen-pins-unavailable" className="text-[11px] text-amber-300">
        {pins.error ??
          (pendingIsToday
            ? "Whether today's pins would reuse a recorded screen could not be loaded."
            : `Whether the pins for ${runDay} would reuse a recorded screen could not be loaded.`)}
      </p>
    );
  }
  const { data } = pins;
  const servedIsToday = data.screen_date === todayUtcDate();
  if (data.universe_snapshot_id === null) {
    return (
      <p data-testid="desk-run-screen-pins-empty" className="text-[11px] text-slate-600">
        {servedIsToday
          ? "No universe snapshot is registered — whether a run today would reuse a recorded screen cannot be named."
          : `No universe snapshot is registered — whether a run for ${data.screen_date} would reuse a recorded screen cannot be named.`}
      </p>
    );
  }
  if (data.recorded !== null) {
    return (
      <p data-testid="desk-run-screen-pins-match" className="text-[11px] text-slate-500">
        {servedIsToday
          ? `A run today would reuse the snapshot already recorded under today's pins — ${data.recorded.id}, recorded ${data.recorded.created_utc}.`
          : `A run for ${data.screen_date} would reuse the snapshot already recorded under that day's pins — ${data.recorded.id}, recorded ${data.recorded.created_utc}.`}
      </p>
    );
  }
  return (
    <p data-testid="desk-run-screen-pins-differ" className="text-[11px] text-slate-500">
      {servedIsToday
        ? `No screen is recorded under the pins that resolve for today — a run would walk ${data.members_total} members.`
        : `No screen is recorded under the pins that resolve for ${data.screen_date} — a run would walk ${data.members_total} members.`}
    </p>
  );
}

function ScreenComputeControl({
  compute,
  onTrigger,
  triggering,
  triggerError,
  onCancel,
  cancelRequested,
  cancelError,
  pins,
  runDay,
}: {
  compute: DeskScreenComputeSnapshot | null;
  onTrigger: () => void;
  triggering: boolean;
  triggerError: string | null;
  onCancel: () => void;
  cancelRequested: boolean;
  cancelError: string | null;
  pins: { ok: boolean; data: DeskScreenPinsResult | null; error?: string } | null;
  runDay: string | null;
}) {
  const isRunning = compute?.state === "running";
  const isFailed = compute?.state === "failed";
  const isCancelled = compute?.state === "cancelled";
  const buttonLabel = isRunning ? "Computing…" : isFailed ? "Retry Run Screen" : "Run Screen";
  return (
    <div className="flex flex-col items-center gap-1">
      {isFailed && compute?.error && (
        <p data-testid="desk-screen-compute-error" className="text-xs text-red-300">
          {compute.error}
        </p>
      )}
      {triggerError && (
        <p data-testid="desk-screen-compute-trigger-error" className="text-xs text-red-300">
          {triggerError}
        </p>
      )}
      {isCancelled && (
        <p data-testid="desk-screen-compute-cancelled" className="text-xs text-amber-200/70">
          Screen compute cancelled — nothing was recorded this run.
        </p>
      )}
      {/* The honest reuse signal the backend threads onto the terminal snapshot (`reused` +
          `screen_id`, added this iteration to close audit B2). Without it on screen, a compute over
          an already-recorded 5-pin key looks identical to a fresh one — the very ambiguity the two
          fields exist to remove (audit F5). */}
      {compute?.state === "done" && compute.screen_id !== null && (
        <p data-testid="desk-screen-compute-outcome" className="text-xs text-slate-500">
          {compute.reused
            ? `Reused the snapshot already recorded for this key — ${compute.screen_id}`
            : `Recorded a new snapshot — ${compute.screen_id}`}
        </p>
      )}
      <TodayScreenPinsNote pins={pins} runDay={runDay} />
      {/* The day the click will actually submit, stated BEFORE it is clicked. The resolved To day
          is no longer always today's UTC date, and the case where it differs is the ordinary one:
          an evening operator preparing after the US close is stamping tomorrow's session. */}
      {runDay !== null && (
        <p data-testid="desk-run-screen-stamp" className="text-[11px] text-slate-500">
          Run Screen will record {runDay}.
        </p>
      )}
      <button
        type="button"
        data-testid="desk-run-screen-button"
        onClick={onTrigger}
        disabled={triggering || isRunning || runDay === null}
        className={PRIMARY_BUTTON_CLASS}
      >
        {buttonLabel}
      </button>
      {isRunning && (
        <div data-testid="desk-screen-compute-running" className="mt-1 flex flex-col items-center gap-1">
          <p data-testid="desk-screen-compute-progress" className="text-xs text-amber-200/70">
            <span
              aria-hidden="true"
              className="mr-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400 align-middle"
            />
            {compute.progress.members_done} / {compute.progress.members_total} members
          </p>
          {compute.progress.current && (
            <p data-testid="desk-screen-compute-current" className="text-xs text-amber-200/70">
              current: {compute.progress.current}
            </p>
          )}
          <button
            type="button"
            data-testid="desk-screen-compute-cancel"
            onClick={onCancel}
            disabled={cancelRequested}
            className={CANCEL_BUTTON_CLASS}
          >
            {cancelRequested ? "Cancelling — finishing the current member…" : "Cancel"}
          </button>
          {cancelError && (
            <p data-testid="desk-screen-compute-cancel-error" className="text-xs text-red-300">
              {cancelError}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function TopupComputeControl({
  compute,
  onTrigger,
  triggering,
  triggerError,
  onCancel,
  cancelRequested,
  cancelError,
}: {
  compute: DeskTopupComputeSnapshot | null;
  onTrigger: () => void;
  triggering: boolean;
  triggerError: string | null;
  onCancel: () => void;
  cancelRequested: boolean;
  cancelError: string | null;
}) {
  const isRunning = compute?.state === "running";
  const isFailed = compute?.state === "failed";
  const isCancelled = compute?.state === "cancelled";
  const buttonLabel = isRunning ? "Topping up…" : isFailed ? "Retry Top-up" : "Top-up";
  const latestOutcome =
    isRunning && compute.progress.outcomes.length > 0
      ? compute.progress.outcomes[compute.progress.outcomes.length - 1]
      : null;
  return (
    <div className="flex flex-col items-center gap-1">
      {isFailed && compute?.error && (
        <p data-testid="desk-topup-compute-error" className="text-xs text-red-300">
          {compute.error}
        </p>
      )}
      {triggerError && (
        <p data-testid="desk-topup-compute-trigger-error" className="text-xs text-red-300">
          {triggerError}
        </p>
      )}
      {isCancelled && (
        <p data-testid="desk-topup-compute-cancelled" className="text-xs text-amber-200/70">
          Top-up cancelled — pairs already recorded before the cancel stay stored.
        </p>
      )}
      <button
        type="button"
        data-testid="desk-topup-button"
        onClick={onTrigger}
        disabled={triggering || isRunning}
        className={PRIMARY_BUTTON_CLASS}
      >
        {buttonLabel}
      </button>
      {isRunning && (
        <div data-testid="desk-topup-compute-running" className="mt-1 flex flex-col items-center gap-1">
          <p data-testid="desk-topup-compute-progress" className="text-xs text-amber-200/70">
            <span
              aria-hidden="true"
              className="mr-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400 align-middle"
            />
            {compute.progress.pairs_done} / {compute.progress.pairs_total} pairs
          </p>
          {latestOutcome && (
            <p data-testid="desk-topup-compute-current" className="text-xs text-amber-200/70">
              last: {latestOutcome.symbol} {latestOutcome.timeframe} — {latestOutcome.outcome}
            </p>
          )}
          <button
            type="button"
            data-testid="desk-topup-compute-cancel"
            onClick={onCancel}
            disabled={cancelRequested}
            className={CANCEL_BUTTON_CLASS}
          >
            {cancelRequested ? "Cancelling — finishing the current pair…" : "Cancel"}
          </button>
          {cancelError && (
            <p data-testid="desk-topup-compute-cancel-error" className="text-xs text-red-300">
              {cancelError}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// era-desk-iter-14 (J-10): a third compute control, wired exactly like `TopupComputeControl` — the
// operation has no per-pair counters (it is a single classify-repair-verify walk, not a walk over
// many pairs), so the running indicator shows the compute's own `progress.phase` label instead of
// an "N / M" count.
function ReconcileIndexControl({
  compute,
  onTrigger,
  triggering,
  triggerError,
  onCancel,
  cancelRequested,
  cancelError,
}: {
  compute: DeskReconcileComputeSnapshot | null;
  onTrigger: () => void;
  triggering: boolean;
  triggerError: string | null;
  onCancel: () => void;
  cancelRequested: boolean;
  cancelError: string | null;
}) {
  const isRunning = compute?.state === "running";
  const isFailed = compute?.state === "failed";
  const isCancelled = compute?.state === "cancelled";
  const buttonLabel = isRunning ? "Reconciling…" : isFailed ? "Retry Reconcile Index" : "Reconcile Index";
  return (
    <div className="flex flex-col items-center gap-1">
      {isFailed && compute?.error && (
        <p data-testid="desk-reconcile-compute-error" className="text-xs text-red-300">
          {compute.error}
        </p>
      )}
      {triggerError && (
        <p data-testid="desk-reconcile-compute-trigger-error" className="text-xs text-red-300">
          {triggerError}
        </p>
      )}
      {isCancelled && (
        <p data-testid="desk-reconcile-compute-cancelled" className="text-xs text-amber-200/70">
          Index reconciliation cancelled — the index was not repaired this run.
        </p>
      )}
      <button
        type="button"
        data-testid="desk-reconcile-button"
        onClick={onTrigger}
        disabled={triggering || isRunning}
        className={PRIMARY_BUTTON_CLASS}
      >
        {buttonLabel}
      </button>
      {isRunning && (
        <div data-testid="desk-reconcile-compute-running" className="mt-1 flex flex-col items-center gap-1">
          <p data-testid="desk-reconcile-compute-progress" className="text-xs text-amber-200/70">
            <span
              aria-hidden="true"
              className="mr-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400 align-middle"
            />
            {compute.progress.phase}
          </p>
          <button
            type="button"
            data-testid="desk-reconcile-compute-cancel"
            onClick={onCancel}
            disabled={cancelRequested}
            className={CANCEL_BUTTON_CLASS}
          >
            {cancelRequested ? "Cancelling…" : "Cancel"}
          </button>
          {cancelError && (
            <p data-testid="desk-reconcile-compute-cancel-error" className="text-xs text-red-300">
              {cancelError}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// REFRESH-CHAIN-START
// One control that runs the four refresh acts in the order the data actually depends on:
// the universe membership, the bar top-up, the bar index repair, then the screen for today.
//
// The order is not cosmetic. A screen's `bar_store_signature` pin is derived from `bar_index`
// coverage and is resolved ONCE, before the member walk starts (desk_screen_compute.py) — so a
// screen run that precedes the top-up and the index repair records a snapshot pinned to bars it
// did not actually read.
//
// This is a CLIENT-side sequence over the four endpoints each existing control already calls. It
// deliberately does NOT add a backend orchestrator: reaching the real compute managers from a
// compute module would be a circular import (desk_topup_compute.py's own documented constraint),
// so an orchestrator would have to call the walker functions directly and would therefore bypass
// each manager's single-flight slot — letting a chained run and a hand-clicked control walk the
// same BarStore at once. Driving the real endpoints gets single-flight for free: a POST against a
// running job returns that job unchanged (`started: false`), which this chain ADOPTS.
//
// It also adds ZERO polling. The three per-compute poll effects inside DeskPage already keep
// `topupCompute`/`reconcileCompute`/`screenCompute` current and already do their own terminal-tick
// ledger refreshes; this chain only WAITS on the state they maintain, read through a ref mirror so
// a plain async driver can see the newest value.
//
// Every step is an explicit operator act: the driver is reachable from the button's onClick and
// nothing else. It is never called from an effect, never resumed after a reload, and never
// scheduled. Re-clicking after an interrupted run is cheap and idempotent — the membership fetch
// answers 409, the top-up is store-first, and a screen under identical pins short-circuits to a
// reuse.

const REFRESH_CHAIN_STEP_KEYS = ["universe", "topup", "reconcile", "screen", "forward"] as const;
type RefreshChainStepKey = (typeof REFRESH_CHAIN_STEP_KEYS)[number];

const REFRESH_CHAIN_STEP_LABELS: Record<RefreshChainStepKey, string> = {
  universe: "Universe membership",
  topup: "Bar top-up",
  reconcile: "Bar index",
  screen: "Screen for today",
  forward: "Forward returns",
};

// --- the as-of day range (forward-test era) -------------------------------------------------------
// Two validated text fields govern the screen compute: To (blank = the upcoming US session date)
// and From (blank = the To day). The chain's screen step loops EVERY day in [From, To]; the standalone Run Screen
// button runs only the To day. Deliberately NOT <input type="date">: the native picker is
// locale-dependent (the TopBar J-35 precedent), and every literal in this block is scanned
// against the shipped goldens' pinned substrings — copy here says "day", never the pinned word.

const SCREEN_DAY_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

// There is deliberately NO per-click day ceiling. One existed (31 days) back when every day in a
// range paid for a full ~101-member walk, so a wide range was quietly an hours-long click. One
// snapshot per date changed that arithmetic: a day whose bars already reach it resolves as a reuse
// in tens of milliseconds without walking a single member (`desk_screen_decision.py`), so a long
// range over an already-covered stretch is nearly free and only the genuinely-missing days cost
// anything. The range is still bounded in the two ways that matter — a To day after the upcoming
// US session date is refused, and the chain's own Stop button ends a run between days — so an
// operator who asks for a year gets a year, and can stop it.

interface ResolvedScreenDayRange {
  from: string;
  to: string;
  days: string[];
}

function isRealUtcDay(value: string): boolean {
  if (!SCREEN_DAY_PATTERN.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

function enumerateUtcDays(from: string, to: string): string[] {
  const out: string[] = [];
  const cursor = new Date(`${from}T00:00:00Z`);
  const end = new Date(`${to}T00:00:00Z`);
  while (cursor.getTime() <= end.getTime()) {
    out.push(cursor.toISOString().slice(0, 10));
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }
  return out;
}

// null error = valid. Blank To resolves to the upcoming US session; blank From resolves to the To
// day. The ceiling is that same upcoming session rather than today's UTC date: after the close
// they differ, and the later of the two is the one an operator can still act on.
function validateScreenDayRange(
  fromRaw: string,
  toRaw: string,
): { error: string | null; range: ResolvedScreenDayRange | null } {
  const stamp = nextTradingStamp();
  const toValue = toRaw.trim() === "" ? stamp : toRaw.trim();
  if (!isRealUtcDay(toValue)) {
    return {
      error: "Enter the To day as a real YYYY-MM-DD, or leave it blank for the upcoming US session date.",
      range: null,
    };
  }
  if (toValue > stamp) {
    return {
      error: "The To day is after the upcoming US session date — a run can cover that day or any earlier day.",
      range: null,
    };
  }
  const fromValue = fromRaw.trim() === "" ? toValue : fromRaw.trim();
  if (!isRealUtcDay(fromValue)) {
    return {
      error: "Enter the From day as a real YYYY-MM-DD, or leave it blank to run one day.",
      range: null,
    };
  }
  if (fromValue > toValue) {
    return { error: "The From day is after the To day.", range: null };
  }
  return {
    error: null,
    range: { from: fromValue, to: toValue, days: enumerateUtcDays(fromValue, toValue) },
  };
}

// Step labels follow the day(s) a RUN actually submitted — a copy choice only, never a derived
// backend fact. A single-day run for today keeps the shipped label byte-identical.
function refreshChainStepLabel(key: RefreshChainStepKey, run: RefreshChainRun): string {
  if (key !== "screen") return REFRESH_CHAIN_STEP_LABELS[key];
  if (run.runDayCount <= 1) {
    return run.runTo === todayUtcDate()
      ? REFRESH_CHAIN_STEP_LABELS.screen
      : `Screen for ${run.runTo}`;
  }
  return `Screens for ${run.runFrom} → ${run.runTo}`;
}

// `noop` is a genuine fourth outcome, not a flavour of `done`: a 409 from the membership fetch
// means the content is identical to a snapshot already registered, so there was nothing to
// register. Calling that "done" would imply a write that never happened.
type RefreshChainStepState =
  | "queued"
  | "running"
  | "done"
  | "noop"
  | "cancelled"
  | "failed"
  | "skipped";

interface RefreshChainStep {
  key: RefreshChainStepKey;
  state: RefreshChainStepState;
  message: string;
}

interface RefreshChainRun {
  steps: RefreshChainStep[];
  outcome: "running" | "done" | "halted" | "cancelled";
  // The as-of day range this run was clicked with — frozen at click time (a later input edit
  // never rewrites a run's own account of itself). Single-day runs have runFrom === runTo.
  runFrom: string;
  runTo: string;
  runDayCount: number;
}

// Literal class strings, never interpolated, so Tailwind's scanner emits them — the
// FETCH_RESULT_COLOR precedent on /structure, in this page's own palette.
const REFRESH_CHAIN_STEP_COLOR: Record<RefreshChainStepState, string> = {
  queued: "text-slate-600",
  running: "text-amber-200/70",
  done: "text-emerald-300",
  noop: "text-slate-500",
  cancelled: "text-amber-200/70",
  failed: "text-red-300",
  skipped: "text-slate-600",
};

// The cancelled wording each step already ships in its own control, reused verbatim so the chain
// and the control beside it can never disagree about what a cancel left behind.
const REFRESH_CHAIN_CANCELLED: Record<RefreshChainStepKey, string> = {
  universe: "stopped on request",
  topup: "cancelled — pairs already recorded before the cancel stay stored",
  reconcile: "cancelled — the index was not repaired this run",
  screen: "cancelled — nothing was recorded this run",
  // Deliberately the top-up's wording rather than the screen's: this step is N jobs, not one, and
  // the forward ledger is append-only per snapshot — so whatever finished before the cancel is
  // genuinely on disk. Only the partial walk is discarded.
  forward: "cancelled — results already recorded before the cancel stay stored",
};

// What each compute trigger hands back. Identical across all three managers.
type ChainTriggerResult<T> = {
  ok: boolean;
  data?: { started: boolean; compute: T };
  error?: string;
};

// The three snapshot shapes agree on exactly these fields, which is all the waiter needs.
type ChainJobSnapshot = { id: string; state: string; error: string | null };

const REFRESH_CHAIN_WAIT_TICK_MS = 250;

function refreshChainSleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

// Wait for the job this chain just started — or ADOPTED — to reach a terminal state. Issues ZERO
// requests: it re-reads the snapshot the step's own existing poll effect already maintains.
//
// Matching the job's own `id` is load-bearing, not defensive. All three managers publish
// `state: "running"` BEFORE their trigger returns, so the POST response is always `running`; and
// when this wait begins React has not re-rendered yet, so `read()` still returns the PREVIOUS
// run's snapshot — which, after a page load that seeded a finished job, is very often already
// terminal. Advancing on the state alone would skip every step instantly.
//
// `onTick`, when given, is called with each running snapshot the waiter observes. It exists for
// the forward step, whose single job can walk ~101 members: without it that step shows one frozen
// line for the whole walk, which reads as a hang and invites a needless Stop. It piggybacks this
// same 250ms sleep — no new timer, no new request.
async function awaitRefreshChainJob<T extends ChainJobSnapshot>(
  read: () => T | null,
  jobId: string,
  stopped: () => boolean,
  onTick?: (snapshot: T) => void,
): Promise<T | null> {
  for (;;) {
    if (stopped()) return null;
    const snapshot = read();
    if (snapshot !== null && snapshot.id === jobId) {
      if (snapshot.state !== "running") return snapshot;
      onTick?.(snapshot);
    }
    await refreshChainSleep(REFRESH_CHAIN_WAIT_TICK_MS);
  }
}

// Terminal one-liners. Each is a re-format of what the compute snapshot already served — never a
// second read, never a derived number. The chain never reads a durable run ledger here: a step's
// poll publishes the terminal snapshot BEFORE refetching its ledger, so a ledger read at this
// instant would still hold the PREVIOUS run.
function describeTopupDone(snapshot: DeskTopupComputeSnapshot): string {
  const counts = topupOutcomeCounts(snapshot.progress.outcomes);
  return `reused ${counts.reused} · new ${counts.fetched} · unchanged ${counts.unchanged} · failed ${counts.failed}`;
}

function describeReconcileDone(_snapshot: DeskReconcileComputeSnapshot): string {
  // This manager's snapshot carries only `progress.phase` — it has no counts to re-render. The
  // run's own numbers live in its durable record, shown in the ledger further down the page.
  return "done — this run's own record is in the ledger below";
}

function describeScreenDone(snapshot: DeskScreenComputeSnapshot): string {
  if (snapshot.screen_id === null) return "done";
  return snapshot.reused
    ? `reused the snapshot already recorded for these pins — ${snapshot.screen_id}`
    : `recorded a new snapshot — ${snapshot.screen_id}`;
}

function describeForwardDone(snapshot: DeskForwardComputeSnapshot): string {
  if (snapshot.forward_id === null) return "done";
  return snapshot.reused
    ? `reused the result already recorded for these inputs — ${snapshot.forward_id}`
    : `recorded a new result — ${snapshot.forward_id}`;
}

interface RefreshChainControlProps {
  run: RefreshChainRun | null;
  onRefreshAll: () => void;
  onStop: () => void;
  stopRequested: boolean;
  fromDay: string;
  toDay: string;
  onFromDayChange: (value: string) => void;
  onToDayChange: (value: string) => void;
  dayRangeError: string | null;
  resolvedRange: ResolvedScreenDayRange | null;
}

function DeskRefreshChainControl({
  run,
  onRefreshAll,
  onStop,
  stopRequested,
  fromDay,
  toDay,
  onFromDayChange,
  onToDayChange,
  dayRangeError,
  resolvedRange,
}: RefreshChainControlProps) {
  const isRunning = run?.outcome === "running";
  const isHalted = run?.outcome === "halted";
  const buttonLabel = isRunning ? "Refreshing…" : isHalted ? "Retry Refresh Data" : "Refresh Data";
  const rangeCopy =
    resolvedRange === null
      ? "the chosen day"
      : resolvedRange.days.length > 1
        ? `every day from ${resolvedRange.from} to ${resolvedRange.to} (${resolvedRange.days.length} days)`
        : resolvedRange.to === todayUtcDate()
          ? "today"
          : resolvedRange.to;
  return (
    <div data-testid="desk-refresh-control" className="flex flex-col items-center gap-1">
      <div className="flex flex-wrap items-end justify-center gap-3">
        <label className="flex flex-col items-center gap-1">
          <span className="text-[11px] font-medium text-slate-500">
            From day — blank = the To day
          </span>
          <input
            type="text"
            inputMode="numeric"
            data-testid="desk-as-of-from-input"
            value={fromDay}
            onChange={(e) => onFromDayChange(e.target.value)}
            placeholder="YYYY-MM-DD"
            disabled={isRunning}
            aria-invalid={dayRangeError !== null}
            className={`${ASOF_INPUT_CLASS} ${dayRangeError !== null ? "border-amber-500" : ""}`}
          />
        </label>
        <label className="flex flex-col items-center gap-1">
          <span className="text-[11px] font-medium text-slate-500">
            To day — blank = upcoming US session
          </span>
          <input
            type="text"
            inputMode="numeric"
            data-testid="desk-as-of-to-input"
            value={toDay}
            onChange={(e) => onToDayChange(e.target.value)}
            placeholder="YYYY-MM-DD"
            disabled={isRunning}
            aria-invalid={dayRangeError !== null}
            className={`${ASOF_INPUT_CLASS} ${dayRangeError !== null ? "border-amber-500" : ""}`}
          />
        </label>
      </div>
      {dayRangeError !== null && (
        <p data-testid="desk-as-of-day-error" className="max-w-md text-center text-xs text-amber-300">
          {dayRangeError}
        </p>
      )}
      <button
        type="button"
        data-testid="desk-refresh-all-button"
        onClick={onRefreshAll}
        disabled={isRunning || dayRangeError !== null}
        className={PRIMARY_BUTTON_CLASS}
      >
        {buttonLabel}
      </button>
      <p data-testid="desk-refresh-note" className="max-w-md text-center text-[11px] text-slate-600">
        One click runs five steps in order: the universe membership, the bar top-up, the bar index,
        the screen for {rangeCopy}, then the forward returns for every snapshot this run recorded.
        Each step calls the same endpoint its own control here already calls; nothing runs without
        this click. A day whose bars already reach it is reused rather than re-walked, so a range
        over ground already covered is quick; every genuinely missing day is a full walk, and the
        forward step measures one snapshot at a time, so a wide range takes a while. Stop ends it
        between days. Run Screen below runs the To day only.
      </p>
      {run !== null && (
        <>
          <ol data-testid="desk-refresh-steps" className="mt-1 w-full max-w-md space-y-0.5">
            {run.steps.map((step, index) => (
              <li
                key={step.key}
                data-testid={`desk-refresh-step-${step.key}`}
                className={`flex flex-wrap items-baseline gap-x-2 text-[11px] ${REFRESH_CHAIN_STEP_COLOR[step.state]}`}
              >
                <span className="font-mono">{index + 1}.</span>
                <span className="font-medium">{refreshChainStepLabel(step.key, run)}</span>
                {step.state === "running" && (
                  <span
                    aria-hidden="true"
                    className="inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400 align-middle"
                  />
                )}
                <span>{step.message}</span>
              </li>
            ))}
          </ol>
          <p data-testid="desk-refresh-summary" className="text-[11px] text-slate-500">
            {refreshChainSummary(run)}
          </p>
          {isRunning && (
            <button
              type="button"
              data-testid="desk-refresh-stop"
              onClick={onStop}
              disabled={stopRequested}
              className={CANCEL_BUTTON_CLASS}
            >
              {stopRequested ? "Stopping — the current step is finishing…" : "Stop"}
            </button>
          )}
        </>
      )}
    </div>
  );
}

function refreshChainSummary(run: RefreshChainRun): string {
  const activeIndex = run.steps.findIndex((step) => step.state === "running");
  if (run.outcome === "running" && activeIndex >= 0) {
    return `Step ${activeIndex + 1} of ${REFRESH_CHAIN_STEP_KEYS.length} — ${refreshChainStepLabel(run.steps[activeIndex].key, run)}.`;
  }
  if (run.outcome === "done") return "All five steps finished.";
  if (run.outcome === "cancelled") return "Stopped on request — the later steps did not run.";
  const stoppedAt = run.steps.find(
    (step) => step.state === "failed" || step.state === "cancelled",
  );
  return stoppedAt
    ? `Stopped at ${refreshChainStepLabel(stoppedAt.key, run)} — the later steps did not run.`
    : "Stopped — the later steps did not run.";
}
// REFRESH-CHAIN-END

interface ScreenControlProps {
  compute: DeskScreenComputeSnapshot | null;
  onTrigger: () => void;
  triggering: boolean;
  triggerError: string | null;
  onCancel: () => void;
  cancelRequested: boolean;
  cancelError: string | null;
  pins: { ok: boolean; data: DeskScreenPinsResult | null; error?: string } | null;
  runDay: string | null;
}

interface TopupControlProps {
  compute: DeskTopupComputeSnapshot | null;
  onTrigger: () => void;
  triggering: boolean;
  triggerError: string | null;
  onCancel: () => void;
  cancelRequested: boolean;
  cancelError: string | null;
}

interface ReconcileControlProps {
  compute: DeskReconcileComputeSnapshot | null;
  onTrigger: () => void;
  triggering: boolean;
  triggerError: string | null;
  onCancel: () => void;
  cancelRequested: boolean;
  cancelError: string | null;
}

// The honest empty state (TC-1): rendered iff `latest === null` — no screen has EVER been
// computed. Doubles as the controls panel for a first-ever run (both Run Screen and Top-up live
// here since there is nothing else to show yet); once a screen exists, the SAME four controls move
// to a panel near the TOP of the populated page — its second section, directly under Screen
// History (see DeskPopulatedScreen below).
function DeskNotComputedPanel({
  screen,
  topup,
  reconcile,
  refreshChain,
}: {
  screen: ScreenControlProps;
  topup: TopupControlProps;
  reconcile: ReconcileControlProps;
  refreshChain: RefreshChainControlProps;
}) {
  return (
    <div
      data-testid="desk-screen-not-computed"
      className="rounded-lg border border-amber-800/60 bg-amber-900/20 px-4 py-6 text-center"
    >
      <p className="text-sm font-medium text-amber-300">Desk screen not computed yet.</p>
      <p className="mt-1 text-xs text-amber-200/70">
        No screen has been recorded yet for the registered universe.
      </p>
      {/* The chained control sits above the three individual ones it drives — this is the
          first-ever-run panel, where running all four in the right order matters most. The three
          stay exactly as they were, and stay enabled: a hand-click on a step the chain has not
          reached yet is harmless, since the chain adopts whatever is already running. */}
      <div className="mt-3 flex flex-col items-center gap-4">
        <DeskRefreshChainControl {...refreshChain} />
        <div className="w-full border-t border-amber-800/40 pt-4">
          <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start sm:justify-center sm:gap-12">
            <ScreenComputeControl {...screen} />
            <TopupComputeControl {...topup} />
            <ReconcileIndexControl {...reconcile} />
          </div>
        </div>
      </div>
    </div>
  );
}

// The latest session any ranked row's map consumed — a plain SELECTION of the served rows' own
// `basis_as_of` values (the `topupWindowBasisCounts` "plain tally, nothing derived" precedent), so
// the header below states a date the snapshot itself recorded rather than one the browser worked
// out. Never a recomputation of any basis, never a re-sort of `rows`: a `for` loop, because the
// page is allowed exactly one `rows`-slice expression file-wide (`test_desk_ui_guards.py`).
//
// A screen dated D is marked up from sessions strictly BEFORE D (`tradability._resolve_basis`), so
// this date is D's PREDECESSOR, and stating it is the whole point — it is what makes the screen
// date read as the trade day rather than the data day. Rows can disagree when one symbol's series
// is staler than another's (each row's own `basis` cell already shows that); the latest is the
// honest screen-level statement, since no row consumed anything after it.
//
// `null` when NO ranked row carries the field: rows recorded before goal-desk-iter-9 omit the key
// entirely and are never backfilled (the established legacy-absence pattern), and a snapshot with
// no ranked rows has nothing to report.
function screenDataThroughDate(rows: DeskScreenRow[]): string | null {
  let latest: string | null = null;
  for (const row of rows) {
    const value = row.basis_as_of;
    if (value == null) continue;
    if (latest === null || value > latest) latest = value;
  }
  return latest === null ? null : latest.substring(0, 10);
}

// The populated view — a real snapshot exists (`latest !== null`), whether it is the latest one
// or a history row the operator selected. `snapshot` is the ONE displayed record; the Forward
// Returns/Briefing/Skipped sections read it verbatim — only the SOURCE of `snapshot` (latest vs. a
// selected history entry) ever varies.
//
// Section order here is the page's first five, in the order an operator actually reads them:
// Screen History (pick what you are looking at), Forward Returns (what the selected snapshot's own
// screen-date session did at each recorded wall — same-session, touch-anchored, never a later
// session), the controls (act on it), the ranked Briefing (the detail, one page at a time), then
// Skipped Members. Forward Returns sat below the controls until the calendar landed;
// it describes the DISPLAYED snapshot, so it now reads directly beneath the cell that selected it,
// and the controls — which act rather than describe — follow. The provenance line used to sit
// first; it is reference material and now renders dead last, out in `DeskPage`. The whole
// registered ten-section order is pinned by
// `test_desk_forward_ui_guard.py::test_the_page_renders_its_sections_in_the_registered_order`.
function DeskPopulatedScreen({
  snapshot,
  screens,
  screenIntegrityErrors,
  isViewingLatest,
  historyFetchError,
  onSelectHistory,
  onShowLatest,
  selectedHistoryId,
  shownYear,
  onShowYear,
  screenControlProps,
  topupControlProps,
  reconcileControlProps,
  refreshChainControlProps,
  forwardResult,
  forwardControlProps,
  selectedForwardSymbol,
  onSelectForwardSymbol,
}: {
  snapshot: DeskScreenSnapshot;
  screens: DeskScreenMeta[];
  screenIntegrityErrors: { file: string; error: string }[];
  isViewingLatest: boolean;
  historyFetchError: string | null;
  onSelectHistory: (id: string) => void;
  onShowLatest: () => void;
  selectedHistoryId: string | null;
  shownYear: number;
  onShowYear: (year: number) => void;
  screenControlProps: ScreenControlProps;
  topupControlProps: TopupControlProps;
  reconcileControlProps: ReconcileControlProps;
  refreshChainControlProps: RefreshChainControlProps;
  forwardResult: { ok: boolean; data: DeskForwardReadResult | null; error?: string } | null;
  forwardControlProps: ForwardControlProps;
  selectedForwardSymbol: string | null;
  onSelectForwardSymbol: (symbol: string) => void;
}) {
  const dataThrough = screenDataThroughDate(snapshot.rows);
  return (
    <div className="space-y-6">
      <p data-testid="desk-screen-basis-note" className="text-xs text-slate-500">
        {dataThrough === null
          ? `Screen for ${snapshot.screen_date} — the sessions its map was built from are not recorded in this snapshot's rows.`
          : `Screen for ${snapshot.screen_date} — built from data through ${dataThrough} close (each ranked row's basis cell names its own session).`}
      </p>
      {!isViewingLatest && (
        <div
          data-testid="desk-viewing-indicator"
          className="flex flex-wrap items-center gap-3 rounded-md border border-slate-700 bg-slate-800/40 px-3 py-2 text-xs text-slate-400"
        >
          <span>Viewing the recorded screen for {snapshot.screen_date} — not the latest.</span>
          <button
            type="button"
            data-testid="desk-history-latest-button"
            onClick={onShowLatest}
            className={SECONDARY_BUTTON_CLASS}
          >
            Latest
          </button>
        </div>
      )}
      {historyFetchError && (
        <p data-testid="desk-history-fetch-error" className="text-xs text-amber-300">
          {historyFetchError}
        </p>
      )}

      <section aria-label="Screen history">
        <Panel title="Screen History">
          <DeskHistoryCalendar
            screens={screens}
            onSelect={onSelectHistory}
            selectedId={selectedHistoryId}
            shownYear={shownYear}
            onShowYear={onShowYear}
          />
          <IntegrityErrorsNote
            errors={screenIntegrityErrors}
            testid="desk-screen-history-integrity-errors"
          />
        </Panel>
      </section>

      {/* Rendered here rather than at the page foot: the forward measurement describes whichever
          snapshot is DISPLAYED, so it belongs directly beneath the calendar cell that selected it —
          read what that same screen-date session did, then act. It needs no `latest !== null`
          wrapper of its own —
          being inside this component already guarantees a snapshot exists. No `mt-6` either: the
          `space-y-6` parent owns the spacing between these five sections. */}
      <section aria-label="Forward Returns">
        <Panel title="Forward Returns">
          <DeskForwardSection
            result={forwardResult}
            control={forwardControlProps}
            selectedSymbol={selectedForwardSymbol}
            onSelectSymbol={onSelectForwardSymbol}
          />
        </Panel>
      </section>

      <section aria-label="Run Screen, Top-up and Reconcile Index controls">
        <Panel title="Run Screen / Top-up / Reconcile Index">
          <div className="flex flex-col items-center gap-4">
            <DeskRefreshChainControl {...refreshChainControlProps} />
            <div className="w-full border-t border-slate-800 pt-4">
              <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start sm:justify-center sm:gap-12">
                <ScreenComputeControl {...screenControlProps} />
                <TopupComputeControl {...topupControlProps} />
                <ReconcileIndexControl {...reconcileControlProps} />
              </div>
            </div>
          </div>
        </Panel>
      </section>

      <section aria-label="Briefing">
        <Panel title="Briefing">
          {snapshot.rows.length === 0 ? (
            <EmptyState testid="desk-rows-empty" title="No members ranked in this screen." />
          ) : (
            // `key={snapshot.id}` is the page-window reset: selecting a different snapshot
            // remounts the table, so its page state returns to 1 instead of stranding the operator
            // on a page the new snapshot may not have. A remount, deliberately — not a twelfth
            // effect (the chain guard pins this page at exactly 11).
            <DeskRowsTable key={snapshot.id} rows={snapshot.rows} asOf={snapshot.as_of} />
          )}
        </Panel>
      </section>

      <section aria-label="Skipped members">
        <Panel title="Skipped Members">
          {snapshot.skipped.length === 0 ? (
            <EmptyState testid="desk-skipped-empty" title="No members were skipped in this screen." />
          ) : (
            <DeskSkippedSection skipped={snapshot.skipped} asOf={snapshot.as_of} />
          )}
        </Panel>
      </section>
    </div>
  );
}

// --- The page --------------------------------------------------------------------------------------

export default function DeskPage() {
  const [screenResult, setScreenResult] = useState<{
    ok: boolean;
    data: DeskScreenListResult | null;
    error?: string;
  } | null>(null);

  const [screenCompute, setScreenCompute] = useState<DeskScreenComputeSnapshot | null>(null);
  const [screenTriggering, setScreenTriggering] = useState(false);
  const [screenTriggerError, setScreenTriggerError] = useState<string | null>(null);
  const [screenCancelRequested, setScreenCancelRequested] = useState(false);
  const [screenCancelError, setScreenCancelError] = useState<string | null>(null);

  const [topupCompute, setTopupCompute] = useState<DeskTopupComputeSnapshot | null>(null);
  const [topupTriggering, setTopupTriggering] = useState(false);
  const [topupTriggerError, setTopupTriggerError] = useState<string | null>(null);
  const [topupCancelRequested, setTopupCancelRequested] = useState(false);
  const [topupCancelError, setTopupCancelError] = useState<string | null>(null);

  // era-desk-iter-11 (J-09): the durable top-up run log — independent of `screenResult`/
  // `topupCompute` above (the latter is the CURRENT/last in-flight job's process-scoped progress;
  // this is every COMPLETED run's persisted terminal outcome).
  const [topupRunsResult, setTopupRunsResult] = useState<{
    ok: boolean;
    data: DeskTopupRunsListResult | null;
    error?: string;
  } | null>(null);

  // era-desk-iter-14 (J-10): the coverage-index reconciliation compute + its durable run log —
  // mirrors the topup* hooks immediately above exactly, one pair per compute manager.
  const [reconcileCompute, setReconcileCompute] = useState<DeskReconcileComputeSnapshot | null>(null);
  const [reconcileTriggering, setReconcileTriggering] = useState(false);
  const [reconcileTriggerError, setReconcileTriggerError] = useState<string | null>(null);
  const [reconcileCancelRequested, setReconcileCancelRequested] = useState(false);
  const [reconcileCancelError, setReconcileCancelError] = useState<string | null>(null);
  const [reconcileRunsResult, setReconcileRunsResult] = useState<{
    ok: boolean;
    data: DeskReconcileRunsListResult | null;
    error?: string;
  } | null>(null);

  // goal-desk-iter-29 (J-18): the durable, append-only SCREEN-run log — independent of
  // `screenResult`/`screenCompute` above (the latter is the CURRENT/last in-flight job's
  // process-scoped progress; this is every COMPLETED run's persisted terminal outcome, including
  // reused/cancelled/failed ones) — mirrors the `topupRunsResult`/`reconcileRunsResult` hooks
  // exactly.
  const [screenRunsResult, setScreenRunsResult] = useState<{
    ok: boolean;
    data: DeskScreenRunsListResult | null;
    error?: string;
  } | null>(null);

  // era-desk-iter-6 (J-05): the screen-history click-through. `viewingSnapshot` is `null` while
  // showing the top-level `latest` snapshot already held in `screenResult` (no refetch needed to
  // return to it — TC-2); once a history row is selected, it holds THAT row's own full snapshot,
  // fetched via the `?id=` read (`fetchDeskScreenById`, goal-desk-iter-16/J-12 — switched from the
  // date-keyed variant so an earlier same-`screen_date` recording is individually reachable).
  // `historyFetchError` surfaces a failed/no-match click WITHOUT disturbing whatever is currently
  // displayed (no crash, no blank state — the plan's own error-case requirement).
  const [viewingSnapshot, setViewingSnapshot] = useState<DeskScreenSnapshot | null>(null);
  const [historyFetchError, setHistoryFetchError] = useState<string | null>(null);

  // The Screen History calendar's visible year. `null` means "follow whatever is displayed" — the
  // year is then DERIVED from the displayed snapshot's own `screen_date` below, so the grid lands on
  // the right year the moment the mount fetch resolves WITHOUT an effect of its own (the page's
  // effect census is pinned; see test_desk_refresh_chain_guard.py). Clicking an arrow pins an
  // explicit year so paging back through a quiet year is not yanked away by a re-render.
  const [viewYear, setViewYear] = useState<number | null>(null);

  // goal-desk-iter-35 (J-20): the Screen Comparison section's own fetch result, keyed off
  // WHICHEVER screen is currently displayed (`viewingSnapshot ?? latest`, the SAME
  // `displayedSnapshot` value computed below) — refetched by its own effect whenever that id
  // changes, independent of the seven mount-time GETs above.
  const [screenCompareResult, setScreenCompareResult] = useState<{
    ok: boolean;
    data: DeskScreenCompareResult | null;
    error?: string;
  } | null>(null);

  // goal-desk-iter-36 (J-21): the screen-pin disclosure's two independent fetches.
  // `runPinsResult` (forward-test era rename of `todayPinsResult`) answers "would a run RIGHT NOW
  // reuse or walk?" for the RESOLVED To day — the SAME value the Run Screen trigger submits
  // (blank inputs resolve to the upcoming US session date) — and is rendered
  // beside that control. `displayedPins` answers the SAME question for the currently DISPLAYED
  // snapshot's own `screen_date` and is refetched by its own effect below whenever the displayed
  // snapshot changes (mirrors `screenCompareResult`'s own effect).
  const [runPinsResult, setRunPinsResult] = useState<{
    ok: boolean;
    data: DeskScreenPinsResult | null;
    error?: string;
  } | null>(null);
  const [displayedPinsResult, setDisplayedPinsResult] = useState<{
    ok: boolean;
    data: DeskScreenPinsResult | null;
    error?: string;
  } | null>(null);

  // Forward-test era: the as-of day range governing the screen compute — the ONE date source.
  // Blank To = today; blank From = the To day. Validated by `validateScreenDayRange` (a derived
  // value, never an effect); invalid input disables BOTH Run Screen and Refresh Data.
  const [fromDayInput, setFromDayInput] = useState("");
  const [toDayInput, setToDayInput] = useState("");
  const dayRange = validateScreenDayRange(fromDayInput, toDayInput);
  const resolvedRange = dayRange.range;

  // Forward-test era: the forward panel's own state — the displayed snapshot's newest recorded
  // forward result (read-keyed on the displayed id, the `screenCompareResult` shape) plus the
  // fourth compute manager's five-variable tuple (the screen/topup/reconcile convention).
  const [forwardResult, setForwardResult] = useState<{
    ok: boolean;
    data: DeskForwardReadResult | null;
    error?: string;
  } | null>(null);
  const [forwardCompute, setForwardCompute] = useState<DeskForwardComputeSnapshot | null>(null);
  const [forwardTriggering, setForwardTriggering] = useState(false);
  const [forwardTriggerError, setForwardTriggerError] = useState<string | null>(null);
  const [forwardCancelRequested, setForwardCancelRequested] = useState(false);
  const [forwardCancelError, setForwardCancelError] = useState<string | null>(null);
  // The forward drill-in selection — plain client state over the ALREADY-loaded record (no
  // effect, no fetch; the census stays at eleven effects). Reset inside the forward GET effect.
  const [selectedForwardSymbol, setSelectedForwardSymbol] = useState<string | null>(null);

  // The chained refresh (see the REFRESH-CHAIN block above). `refreshChain` is plain state and is
  // deliberately NOT persisted: a reload clears it and nothing resumes, which is what keeps "every
  // run is an explicit operator act" true structurally rather than by convention. Whatever job was
  // in flight still shows in its own control after the reload — the mount seed and that step's own
  // poll effect re-attach to it exactly as they always did.
  const [refreshChain, setRefreshChain] = useState<RefreshChainRun | null>(null);
  const [refreshChainStopRequested, setRefreshChainStopRequested] = useState(false);
  const refreshChainStopRef = useRef(false);
  const refreshChainActiveRef = useRef(false);

  // Mirrors of the four compute snapshots, so the plain async driver below can read the newest
  // value (a closure cannot). NOT a second source of truth: each holds exactly what its own
  // useState already holds, and nothing ever writes to these except this one effect. The forward
  // mirror joins THIS effect deliberately rather than opening its own — the page's effect census
  // is pinned at eleven, and a fifth chain step is not a reason to spend the twelfth.
  const topupComputeRef = useRef(topupCompute);
  const reconcileComputeRef = useRef(reconcileCompute);
  const screenComputeRef = useRef(screenCompute);
  const forwardComputeRef = useRef(forwardCompute);
  useEffect(() => {
    topupComputeRef.current = topupCompute;
    reconcileComputeRef.current = reconcileCompute;
    screenComputeRef.current = screenCompute;
    forwardComputeRef.current = forwardCompute;
  }, [topupCompute, reconcileCompute, screenCompute, forwardCompute]);

  // Unmounting (a nav away mid-chain) stops the driver at its next check — no POST after the page
  // is gone, no setState on an unmounted component, no orphaned wait loop.
  useEffect(
    () => () => {
      refreshChainStopRef.current = true;
    },
    [],
  );

  // Mount: eight GETs, zero POSTs (TC-19/TC-8, extended era-desk-iter-14/goal-desk-iter-29/
  // goal-desk-iter-36/forward-test era) — the screen list/latest, ALL FOUR compute managers'
  // current/last snapshot (seeds a page load mid-job or post-terminal without a spurious extra
  // click — the /structure edge-report mount-seeding precedent), the top-up run log's list +
  // latest full record (era-desk-iter-11, J-09), the reconciliation run log's list + latest full
  // record (era-desk-iter-14, J-10), and the screen run log's list + latest full record
  // (goal-desk-iter-29, J-18). The J-21 screen-pin GET moved OUT of this effect into its own
  // as-of-keyed effect immediately below (it must follow the operator's resolved To day, which
  // on a fresh mount is today — byte-identical behavior).
  useEffect(() => {
    let alive = true;
    fetchDeskScreen().then((result) => {
      if (alive) setScreenResult(result);
    });
    fetchDeskScreenCompute().then((result) => {
      if (alive && result.ok) setScreenCompute(result.data);
    });
    fetchDeskScreenRuns().then((result) => {
      if (alive) setScreenRunsResult(result);
    });
    fetchDeskTopupCompute().then((result) => {
      if (alive && result.ok) setTopupCompute(result.data);
    });
    fetchDeskTopupRuns().then((result) => {
      if (alive) setTopupRunsResult(result);
    });
    fetchDeskReconcileCompute().then((result) => {
      if (alive && result.ok) setReconcileCompute(result.data);
    });
    fetchDeskReconcileRuns().then((result) => {
      if (alive) setReconcileRunsResult(result);
    });
    fetchDeskForwardCompute().then((result) => {
      if (alive && result.ok) setForwardCompute(result.data);
    });
    return () => {
      alive = false;
    };
  }, []);

  // goal-desk-iter-36 (J-21) + forward-test era: the screen-pins disclosure follows the resolved
  // To day. Fires on mount (blank inputs -> today, identical to the GET this replaced in the
  // mount effect) and again only when a COMPLETE valid day is entered; while the fields are
  // mid-edit/invalid it holds the last answer (the payload's own `screen_date` names which day it
  // answers for). A GET only — never a trigger, never a timer.
  useEffect(() => {
    const check = validateScreenDayRange(fromDayInput, toDayInput);
    if (check.range === null) return;
    const day = check.range.to;
    let alive = true;
    fetchDeskScreenPins(day).then((result) => {
      if (alive) setRunPinsResult(result);
    });
    return () => {
      alive = false;
    };
  }, [fromDayInput, toDayInput]);

  // Poll the screen compute job while running (mirrors /structure's edge-report poll pattern —
  // reusing the PATTERN, not the endpoint). The instant a tick observes a terminal state, the
  // screen list is re-fetched exactly once so the briefing swaps in — zero new report-rendering
  // logic, the same "read verbatim, recompute nothing" discipline every section here follows.
  // goal-desk-iter-29 (J-18): the SAME terminal tick also re-fetches the screen run log exactly
  // once, so the just-finished run's own record appears in Screen Runs without a manual reload —
  // the SAME "on terminal, refresh the durable list" precedent `topupRunsResult`/
  // `reconcileRunsResult`'s own polls below already establish.
  useEffect(() => {
    if (screenCompute?.state !== "running") return;
    const handle = setInterval(async () => {
      const next = await fetchDeskScreenCompute();
      if (!next.ok) return; // an honest "couldn't reach the backend this tick" — keep polling
      setScreenCompute(next.data);
      if (next.data && next.data.state !== "running") {
        const refreshed = await fetchDeskScreen();
        // TC-21's "keep the last known state, never fabricate one" applied to THIS refetch too, not
        // just to the poll above (audit F4): a single failed GET here must not replace a populated
        // briefing with the amber unavailable panel. When nothing good was ever loaded, the honest
        // failure IS the new state and is adopted.
        setScreenResult((previous) =>
          refreshed.ok || previous === null || !previous.ok ? refreshed : previous,
        );
        const refreshedRuns = await fetchDeskScreenRuns();
        setScreenRunsResult((previous) =>
          refreshedRuns.ok || previous === null || !previous.ok ? refreshedRuns : previous,
        );
        // goal-desk-iter-36 (J-21): a just-finished run changes whether the RESOLVED To day's
        // pins would now reuse or walk — the SAME "on terminal, refresh once" precedent the two
        // refetches above already establish (never a timer/poll of its own). Skipped while the
        // inputs are mid-edit/invalid — the as-of-keyed effect refetches when they become valid.
        const check = validateScreenDayRange(fromDayInput, toDayInput);
        if (check.range !== null) {
          const refreshedRunPins = await fetchDeskScreenPins(check.range.to);
          setRunPinsResult((previous) =>
            refreshedRunPins.ok || previous === null || !previous.ok ? refreshedRunPins : previous,
          );
        }
      }
    }, 700);
    return () => clearInterval(handle);
    // The as-of inputs join the deps so the terminal-tick refetch always reads the CURRENT
    // resolved day (the interval only exists while a job runs, so re-registration is cheap).
  }, [screenCompute, fromDayInput, toDayInput]);

  // Poll the top-up job while running — independent of the screen compute poll above (the two
  // compute managers are separate processes-scoped jobs). era-desk-iter-11 (J-09): the instant a
  // tick observes a terminal state, the run log is re-fetched exactly once — the SAME "on
  // terminal, refresh the durable list" precedent the screen compute poll above already
  // establishes — so the just-finished run's own record appears in Top-up Runs without a manual
  // page reload. The SAME "keep the last known state, never fabricate one" discipline applies: a
  // failed refetch here leaves whatever was already displayed untouched.
  useEffect(() => {
    if (topupCompute?.state !== "running") return;
    const handle = setInterval(async () => {
      const next = await fetchDeskTopupCompute();
      if (next.ok) setTopupCompute(next.data);
      if (next.ok && next.data && next.data.state !== "running") {
        const refreshed = await fetchDeskTopupRuns();
        setTopupRunsResult((previous) =>
          refreshed.ok || previous === null || !previous.ok ? refreshed : previous,
        );
      }
    }, 700);
    return () => clearInterval(handle);
  }, [topupCompute]);

  // Poll the reconciliation job while running — independent of the other two polls above (three
  // separate process-scoped jobs). era-desk-iter-14 (J-10): the SAME "on terminal, refresh the
  // durable list once" precedent the other two polls already establish, and the SAME "keep the
  // last known state, never fabricate one" discipline on a failed refetch.
  useEffect(() => {
    if (reconcileCompute?.state !== "running") return;
    const handle = setInterval(async () => {
      const next = await fetchDeskReconcileCompute();
      if (next.ok) setReconcileCompute(next.data);
      if (next.ok && next.data && next.data.state !== "running") {
        const refreshed = await fetchDeskReconcileRuns();
        setReconcileRunsResult((previous) =>
          refreshed.ok || previous === null || !previous.ok ? refreshed : previous,
        );
      }
    }, 700);
    return () => clearInterval(handle);
  }, [reconcileCompute]);

  // The three trigger handlers below each end with `return result;` (added for the refresh chain)
  // so the chain can read the job's own id, the `started` flag and any verbatim error WITHOUT
  // duplicating the per-control state bookkeeping each one already does. Their bodies are
  // otherwise unchanged, and a value-returning function is still assignable to the `onTrigger: ()
  // => void` prop the three controls declare, so those components and their props interfaces are
  // untouched.
  // Forward-test era: `day` is the chain's per-day loop parameter; the no-arg form (the Run
  // Screen button's own `onTrigger`) runs the RESOLVED To day. Both buttons disable while the
  // range is invalid, so the guard return below is a belt-and-braces rail, not a reachable path.
  async function handleTriggerScreen(
    day?: string,
  ): Promise<ChainTriggerResult<DeskScreenComputeSnapshot>> {
    const runDay = typeof day === "string" ? day : resolvedRange?.to;
    if (runDay === undefined) {
      return { ok: false, error: "The as-of day is not valid." };
    }
    setScreenTriggering(true);
    setScreenTriggerError(null);
    setScreenCancelRequested(false);
    setScreenCancelError(null);
    const result = await triggerDeskScreenCompute(runDay);
    setScreenTriggering(false);
    if (result.ok && result.data) {
      setScreenCompute(result.data.compute);
    } else {
      setScreenTriggerError(result.error ?? "The screen compute could not be started.");
    }
    return result;
  }

  async function handleCancelScreen() {
    setScreenCancelRequested(true);
    setScreenCancelError(null);
    const result = await cancelDeskScreenCompute();
    if (!result.ok) {
      setScreenCancelRequested(false);
      setScreenCancelError(result.error ?? "The screen compute could not be cancelled.");
    }
  }

  async function handleTriggerTopup(): Promise<ChainTriggerResult<DeskTopupComputeSnapshot>> {
    setTopupTriggering(true);
    setTopupTriggerError(null);
    setTopupCancelRequested(false);
    setTopupCancelError(null);
    const result = await triggerDeskTopupCompute();
    setTopupTriggering(false);
    if (result.ok && result.data) {
      setTopupCompute(result.data.compute);
    } else {
      setTopupTriggerError(result.error ?? "The bar top-up could not be started.");
    }
    return result;
  }

  async function handleCancelTopup() {
    setTopupCancelRequested(true);
    setTopupCancelError(null);
    const result = await cancelDeskTopupCompute();
    if (!result.ok) {
      setTopupCancelRequested(false);
      setTopupCancelError(result.error ?? "The bar top-up could not be cancelled.");
    }
  }

  async function handleTriggerReconcile(): Promise<
    ChainTriggerResult<DeskReconcileComputeSnapshot>
  > {
    setReconcileTriggering(true);
    setReconcileTriggerError(null);
    setReconcileCancelRequested(false);
    setReconcileCancelError(null);
    const result = await triggerDeskReconcileCompute();
    setReconcileTriggering(false);
    if (result.ok && result.data) {
      setReconcileCompute(result.data.compute);
    } else {
      setReconcileTriggerError(result.error ?? "The index reconciliation could not be started.");
    }
    return result;
  }

  async function handleCancelReconcile() {
    setReconcileCancelRequested(true);
    setReconcileCancelError(null);
    const result = await cancelDeskReconcileCompute();
    if (!result.ok) {
      setReconcileCancelRequested(false);
      setReconcileCancelError(result.error ?? "The index reconciliation could not be cancelled.");
    }
  }

  // The chained refresh driver. Reachable from the Refresh Data button's onClick and NOTHING else
  // — never an effect, never a timer, never a resume. Structure mirrors /structure's own
  // `handleFetchYahoo`: a mutable step array republished after every transition so each outcome
  // lands live rather than all at once at the end.
  async function handleRefreshAll() {
    if (refreshChainActiveRef.current) return;
    // The as-of range is captured ONCE, at click time — a later input edit never changes what a
    // running (or finished) chain reports about itself. The button disables while the range is
    // invalid, so this guard is a belt-and-braces rail, not a reachable path.
    if (resolvedRange === null) return;
    const range = resolvedRange;
    refreshChainActiveRef.current = true;
    refreshChainStopRef.current = false;
    setRefreshChainStopRequested(false);

    const steps: RefreshChainStep[] = REFRESH_CHAIN_STEP_KEYS.map((key) => ({
      key,
      state: "queued" as RefreshChainStepState,
      message: "queued",
    }));
    const publish = (outcome: RefreshChainRun["outcome"]) =>
      setRefreshChain({
        steps: steps.map((step) => ({ ...step })),
        outcome,
        runFrom: range.from,
        runTo: range.to,
        runDayCount: range.days.length,
      });

    // Halt: mark this step's own terminal outcome, mark every later step honestly un-run, and
    // stop. A halted chain never issues another POST.
    const halt = (index: number, state: RefreshChainStepState, message: string) => {
      steps[index] = { key: steps[index].key, state, message };
      for (let i = index + 1; i < steps.length; i += 1) {
        steps[i] = {
          key: steps[i].key,
          state: "skipped",
          message: "not run — the sequence stopped earlier",
        };
      }
      publish(state === "cancelled" ? "cancelled" : "halted");
      refreshChainActiveRef.current = false;
    };

    // Step 1 — the membership. Synchronous: no compute manager, no poll, no cancel route.
    steps[0] = { key: "universe", state: "running", message: "reading the membership source…" };
    publish("running");
    const universe = await triggerDeskUniverseFetch();
    if (refreshChainStopRef.current) {
      halt(0, "cancelled", REFRESH_CHAIN_CANCELLED.universe);
      return;
    }
    if (universe.ok && universe.data !== null) {
      steps[0] = {
        key: "universe",
        state: "done",
        message: `registered ${universe.data.member_count} members — ${universe.data.id}`,
      };
      // A NEW membership changes which snapshot the run's pins resolve against, so refresh that
      // ONE read here for the captured To day — the same "on a terminal outcome, refetch once"
      // precedent the screen poll already uses for this exact endpoint. Never a timer/poll.
      const pins = await fetchDeskScreenPins(range.to);
      setRunPinsResult((previous) =>
        pins.ok || previous === null || !previous.ok ? pins : previous,
      );
    } else if (universe.status === 409) {
      // Content identical to a snapshot already registered — there was nothing to register. A
      // normal outcome, not a failure. The backend's own `detail` already names the existing
      // snapshot and says why nothing was written, so it is surfaced VERBATIM after a one-word
      // marker rather than re-wrapped in a sentence that repeats it.
      steps[0] = {
        key: "universe",
        state: "noop",
        message: `unchanged — ${universe.error ?? "this membership is already registered"}`,
      };
    } else {
      halt(0, "failed", universe.error ?? "The universe membership could not be read.");
      return;
    }
    publish("running");

    // Steps 2-4 — three pollable jobs, each started through its OWN existing handler.
    const runJob = async <T extends ChainJobSnapshot>(
      index: number,
      trigger: () => Promise<ChainTriggerResult<T>>,
      read: () => T | null,
      describeDone: (snapshot: T) => string,
    ): Promise<boolean> => {
      const key = steps[index].key;
      if (refreshChainStopRef.current) {
        halt(index, "cancelled", REFRESH_CHAIN_CANCELLED[key]);
        return false;
      }
      steps[index] = { key, state: "running", message: "starting…" };
      publish("running");

      const started = await trigger();
      if (!started.ok || !started.data) {
        halt(index, "failed", started.error ?? "This step could not be started.");
        return false;
      }
      // Single-flight adoption: `started: false` means a job was already running and the manager
      // handed THAT job back unchanged. The chain waits on it — never treats it as an error, and
      // never starts a second one.
      const adopted = started.data.started === false;
      steps[index] = {
        key,
        state: "running",
        message: adopted ? "joined a job already running" : "running",
      };
      publish("running");

      const settled = await awaitRefreshChainJob(
        read,
        started.data.compute.id,
        () => refreshChainStopRef.current,
      );
      if (settled === null) {
        halt(index, "cancelled", REFRESH_CHAIN_CANCELLED[key]);
        return false;
      }
      if (settled.state === "done") {
        const detail = describeDone(settled);
        steps[index] = {
          key,
          state: "done",
          message: adopted ? `joined a job already running — ${detail}` : detail,
        };
        publish("running");
        return true;
      }
      if (settled.state === "cancelled") {
        halt(index, "cancelled", REFRESH_CHAIN_CANCELLED[key]);
        return false;
      }
      halt(index, "failed", settled.error ?? "This step failed.");
      return false;
    };

    if (!(await runJob(1, handleTriggerTopup, () => topupComputeRef.current, describeTopupDone))) {
      return;
    }
    if (
      !(await runJob(
        2,
        handleTriggerReconcile,
        () => reconcileComputeRef.current,
        describeReconcileDone,
      ))
    ) {
      return;
    }

    // Step 4 — the screen, once PER DAY of the captured range, oldest first (forward-test era).
    // Each day is its own single-flight job through the SAME handler the Run Screen button uses;
    // each is awaited to terminal before the next starts, so two walks never overlap. A day whose
    // pins are already recorded resolves as an honest reuse. The first failed or cancelled day
    // halts the chain there — later days are honestly un-run.
    // The ids the screen step ACTUALLY recorded, oldest first — step 5's whole input. Taken from
    // each day's own settled snapshot, never re-read from a ledger and never re-derived from the
    // day string. A REUSED day yields the pre-existing record's id, which is exactly the snapshot
    // that day now stands on, so it is measured like any other. Deduped because a day's trigger
    // can ADOPT a job the manager was already running for a DIFFERENT day, whose snapshot then
    // names that other day's id — measuring it twice would be a second walk over one input.
    const recordedScreenIds: string[] = [];
    const seenScreenIds = new Set<string>();

    {
      const screenIndex = 3;
      let recordedCount = 0;
      let reusedCount = 0;
      let lastSettled: DeskScreenComputeSnapshot | null = null;
      for (let dayIndex = 0; dayIndex < range.days.length; dayIndex += 1) {
        const day = range.days[dayIndex];
        if (refreshChainStopRef.current) {
          halt(screenIndex, "cancelled", REFRESH_CHAIN_CANCELLED.screen);
          return;
        }
        steps[screenIndex] = {
          key: "screen",
          state: "running",
          message: `day ${dayIndex + 1} of ${range.days.length} — ${day}`,
        };
        publish("running");

        const started = await handleTriggerScreen(day);
        if (!started.ok || !started.data) {
          halt(
            screenIndex,
            "failed",
            `${day}: ${started.error ?? "this day's run could not be started"}`,
          );
          return;
        }
        const adopted = started.data.started === false;
        if (adopted) {
          steps[screenIndex] = {
            key: "screen",
            state: "running",
            message: `day ${dayIndex + 1} of ${range.days.length} — ${day} · joined a job already running`,
          };
          publish("running");
        }
        const settled = await awaitRefreshChainJob(
          () => screenComputeRef.current,
          started.data.compute.id,
          () => refreshChainStopRef.current,
        );
        if (settled === null) {
          halt(screenIndex, "cancelled", `${day}: ${REFRESH_CHAIN_CANCELLED.screen}`);
          return;
        }
        if (settled.state === "cancelled") {
          halt(screenIndex, "cancelled", `${day}: ${REFRESH_CHAIN_CANCELLED.screen}`);
          return;
        }
        if (settled.state !== "done") {
          halt(screenIndex, "failed", `${day}: ${settled.error ?? "this day's run failed"}`);
          return;
        }
        lastSettled = settled;
        if (settled.screen_id !== null && !seenScreenIds.has(settled.screen_id)) {
          seenScreenIds.add(settled.screen_id);
          recordedScreenIds.push(settled.screen_id);
        }
        if (settled.reused) {
          reusedCount += 1;
        } else {
          recordedCount += 1;
        }
      }
      const dayCount = range.days.length;
      steps[screenIndex] = {
        key: "screen",
        state: "done",
        message:
          dayCount === 1 && lastSettled !== null
            ? describeScreenDone(lastSettled)
            : `${dayCount} days — ${recordedCount} recorded · ${reusedCount} reused`,
      };
    }

    // Step 5 — the forward returns, once per snapshot THIS run recorded, oldest first. Serialized
    // against a manager whose single-flight slot is process-wide: each job is awaited to terminal
    // before the next starts, so two walks never overlap and the chain never queues behind itself.
    // Every job goes through the SAME handler the Compute Forward button uses, so that panel's own
    // state stays the single owner of the trigger state.
    {
      const forwardIndex = 4;
      const total = recordedScreenIds.length;
      if (total === 0) {
        // A genuine no-op, not a `done`: the screen step recorded nothing to measure, and calling
        // that "done" would imply a measurement that never happened (the membership-409 precedent).
        steps[forwardIndex] = {
          key: "forward",
          state: "noop",
          message: "nothing to measure — no snapshot was recorded",
        };
        publish("done");
        refreshChainActiveRef.current = false;
        return;
      }

      let newCount = 0;
      let reusedForwardCount = 0;
      let lastForward: DeskForwardComputeSnapshot | null = null;

      for (let idIndex = 0; idIndex < total; idIndex += 1) {
        const screenId = recordedScreenIds[idIndex];
        const head = `measuring ${idIndex + 1} of ${total} — ${screenId}`;
        let measured: DeskForwardComputeSnapshot | null = null;

        // At most TWO attempts, through ONE call site. This manager's single-flight slot is
        // process-wide rather than per-snapshot — its trigger hands back whatever job is running
        // whatever id was asked for — so an adopted job may be measuring a DIFFERENT snapshot.
        // Waiting on it is still right (never start a second walk), but it did not measure THIS
        // id, so the chain asks once more now that the slot is free. A second mismatch is
        // reported, never looped on.
        for (let attempt = 0; attempt < 2; attempt += 1) {
          if (refreshChainStopRef.current) {
            halt(forwardIndex, "cancelled", REFRESH_CHAIN_CANCELLED.forward);
            return;
          }
          steps[forwardIndex] = { key: "forward", state: "running", message: head };
          publish("running");

          const started = await handleTriggerForward(screenId);
          if (!started.ok || !started.data) {
            halt(
              forwardIndex,
              "failed",
              `${screenId}: ${started.error ?? "this snapshot could not be measured"}`,
            );
            return;
          }
          const adopted = started.data.started === false;
          const base = adopted ? `${head} · joined a job already running` : head;
          let ticked = "";

          const job = await awaitRefreshChainJob(
            () => forwardComputeRef.current,
            started.data.compute.id,
            () => refreshChainStopRef.current,
            (tick) => {
              // "of", never a slash: a rendered "101 of 101" is inert, where "101 / 101" is a
              // string a shipped golden pins against a table this control renders above.
              const message = `${base} · ${tick.progress.rows_done} of ${tick.progress.rows_total} rows`;
              if (message === ticked) return;
              ticked = message;
              steps[forwardIndex] = { key: "forward", state: "running", message };
              publish("running");
            },
          );
          if (job === null || job.state === "cancelled") {
            halt(forwardIndex, "cancelled", `${screenId}: ${REFRESH_CHAIN_CANCELLED.forward}`);
            return;
          }
          if (job.state !== "done") {
            halt(
              forwardIndex,
              "failed",
              `${screenId}: ${job.error ?? "this snapshot could not be measured"}`,
            );
            return;
          }
          if (job.screen_id === screenId) {
            measured = job;
            break;
          }
        }

        if (measured === null) {
          halt(
            forwardIndex,
            "failed",
            `${screenId}: a job already running measured another snapshot`,
          );
          return;
        }
        lastForward = measured;
        if (measured.reused) {
          reusedForwardCount += 1;
        } else {
          newCount += 1;
        }
      }

      steps[forwardIndex] = {
        key: "forward",
        state: "done",
        message:
          total === 1 && lastForward !== null
            ? describeForwardDone(lastForward)
            : `${total} snapshots — ${newCount} recorded · ${reusedForwardCount} reused`,
      };
    }

    publish("done");
    refreshChainActiveRef.current = false;
  }

  // Stopping does two independent things, both required: it stops the chain from advancing (the
  // ref is read synchronously by the driver's next check), AND it cancels the step's own job
  // through the cancel endpoint that step already ships. The membership fetch has no cancel route
  // — a single synchronous POST — so the chain still stops, and the call already sent finishes
  // server-side either way.
  //
  // The reverse path needs no code at all: a per-control Cancel drives that job to `cancelled`,
  // which the waiter observes and the driver halts on.
  async function handleStopRefreshChain() {
    refreshChainStopRef.current = true;
    setRefreshChainStopRequested(true);
    const active = refreshChain?.steps.find((step) => step.state === "running") ?? null;
    if (active === null) return;
    if (active.key === "topup") await handleCancelTopup();
    else if (active.key === "reconcile") await handleCancelReconcile();
    else if (active.key === "screen") await handleCancelScreen();
    else if (active.key === "forward") await handleCancelForward();
  }

  // era-desk-iter-6 (J-05): select a past history row — fetch-and-swap, no POST, no recompute
  // (TC-1). goal-desk-iter-16 (J-12): switched from `?date=` to `?id=` — a `screen_date`-keyed
  // fetch could only ever resolve the NEWER of two same-date recordings (`?date=`'s own
  // `matching[-1]` convention), so it structurally could not reach an earlier same-date entry;
  // `?id=` addresses each recording individually. An unknown id (`{"screen": null}`) or an
  // unreachable backend both leave the currently-displayed snapshot exactly as it was — only the
  // error note changes.
  async function handleSelectHistoryScreen(id: string) {
    setHistoryFetchError(null);
    const result = await fetchDeskScreenById(id);
    if (result.ok && result.data !== null) {
      setViewingSnapshot(result.data);
      return;
    }
    setHistoryFetchError(
      result.ok
        ? "No recorded screen matches that entry — still showing the previously displayed screen."
        : result.error ?? "That recorded screen could not be loaded.",
    );
  }

  // Revert to the top-level `latest` snapshot already held in `screenResult` state (TC-2) — no
  // refetch, since the page already has it.
  function handleShowLatest() {
    setViewingSnapshot(null);
    setHistoryFetchError(null);
  }

  const screenControlProps: ScreenControlProps = {
    compute: screenCompute,
    onTrigger: handleTriggerScreen,
    triggering: screenTriggering,
    triggerError: screenTriggerError,
    onCancel: handleCancelScreen,
    cancelRequested: screenCancelRequested,
    cancelError: screenCancelError,
    pins: runPinsResult,
    runDay: resolvedRange?.to ?? null,
  };
  const topupControlProps: TopupControlProps = {
    compute: topupCompute,
    onTrigger: handleTriggerTopup,
    triggering: topupTriggering,
    triggerError: topupTriggerError,
    onCancel: handleCancelTopup,
    cancelRequested: topupCancelRequested,
    cancelError: topupCancelError,
  };
  const reconcileControlProps: ReconcileControlProps = {
    compute: reconcileCompute,
    onTrigger: handleTriggerReconcile,
    triggering: reconcileTriggering,
    triggerError: reconcileTriggerError,
    onCancel: handleCancelReconcile,
    cancelRequested: reconcileCancelRequested,
    cancelError: reconcileCancelError,
  };
  const refreshChainControlProps: RefreshChainControlProps = {
    run: refreshChain,
    onRefreshAll: handleRefreshAll,
    onStop: handleStopRefreshChain,
    stopRequested: refreshChainStopRequested,
    fromDay: fromDayInput,
    toDay: toDayInput,
    onFromDayChange: setFromDayInput,
    onToDayChange: setToDayInput,
    dayRangeError: dayRange.error,
    resolvedRange,
  };

  const latest = screenResult?.ok ? screenResult.data?.latest ?? null : null;
  const screens = screenResult?.ok ? screenResult.data?.screens ?? [] : [];
  const screenIntegrityErrors = screenResult?.ok ? screenResult.data?.integrity_errors ?? [] : [];
  // The snapshot actually on screen: a selected history entry, or `latest` when none is selected.
  // `latest === null` (never `displayedSnapshot === null`) stays the ONE discriminator for the
  // honest "Desk screen not computed yet." empty state — with no screen ever recorded there is
  // nothing in `screens` to have selected in the first place, so the two states cannot diverge.
  const displayedSnapshot = viewingSnapshot ?? latest;
  // Whether what is ON SCREEN is the newest recorded screen — a comparison of the displayed
  // snapshot's own id against `latest`'s, NOT merely "no history row was clicked" (audit F1): the
  // newest screen is itself a row in the history list, so selecting it displays exactly `latest`,
  // and a banner claiming "not the latest" there would state something false about the very
  // snapshot it is describing.
  const isViewingLatest = viewingSnapshot === null || viewingSnapshot.id === latest?.id;
  // goal-desk-iter-16 (J-12): the id-based highlight for `DeskHistoryCalendar` — the SAME id the
  // above `isViewingLatest` check already compares against, so the currently-displayed snapshot
  // (a selected history entry OR the default `latest`) is always the one highlighted row, even
  // when it shares its `screen_date` with another recorded entry.
  const selectedHistoryId = viewingSnapshot?.id ?? latest?.id ?? null;
  // The calendar's visible year: an explicitly-paged one, else the displayed snapshot's own year,
  // else today's. A pure derivation — never an effect, never a fetch.
  const shownYear =
    viewYear ?? Number((displayedSnapshot?.screen_date ?? todayUtcDate()).slice(0, 4));

  // goal-desk-iter-35 (J-20): fetch the Screen Comparison payload for whichever screen is
  // currently DISPLAYED (`displayedSnapshot`'s own id, the SAME snapshot the Briefing/Provenance
  // sections above already render) — a page-load/id-change GET only, never triggered by a click
  // (no new control ships this iteration). Re-fetches whenever the displayed screen changes (a
  // history row selected, or reverting to Latest); `alive` guards against a stale response landing
  // after a fast second switch, mirroring every other mount-time fetch effect on this page.
  useEffect(() => {
    const id = displayedSnapshot?.id ?? null;
    if (id === null) {
      setScreenCompareResult(null);
      return;
    }
    let alive = true;
    fetchDeskScreenCompare(id).then((result) => {
      if (alive) setScreenCompareResult(result);
    });
    return () => {
      alive = false;
    };
  }, [displayedSnapshot]);

  // goal-desk-iter-36 (J-21): fetch the screen-pin resolution for the DISPLAYED snapshot's own
  // `screen_date` — the SAME `displayedSnapshot` dependency the Screen Comparison effect above
  // uses, since `DeskProvenance` (which renders this) describes that same snapshot. A page-load/
  // selection-change GET only, never a timer or a click.
  useEffect(() => {
    const screenDate = displayedSnapshot?.screen_date ?? null;
    if (screenDate === null) {
      setDisplayedPinsResult(null);
      return;
    }
    let alive = true;
    fetchDeskScreenPins(screenDate).then((result) => {
      if (alive) setDisplayedPinsResult(result);
    });
    return () => {
      alive = false;
    };
  }, [displayedSnapshot]);

  // Forward-test era: the displayed snapshot's newest recorded forward result — id-keyed, the
  // `screenCompareResult` effect's exact shape. A GET only, never a trigger. The drill-in
  // selection resets here too (plain state, no effect of its own): a different snapshot means a
  // different record, so a stale selection must not carry across.
  useEffect(() => {
    const id = displayedSnapshot?.id ?? null;
    setSelectedForwardSymbol(null);
    if (id === null) {
      setForwardResult(null);
      return;
    }
    let alive = true;
    fetchDeskForward(id).then((result) => {
      if (alive) setForwardResult(result);
    });
    return () => {
      alive = false;
    };
  }, [displayedSnapshot]);

  // Poll the forward compute job while running — the fourth manager's poll, mirroring the
  // topup-poll shape with ONE terminal refetch: the displayed snapshot's own forward read
  // (keep-last-known on failure). If the operator switched the displayed screen mid-compute, the
  // refetch targets the NEWLY displayed id — the computed screen's record appears when it is
  // displayed again, via the id-keyed read effect above. Honest, and stated here on purpose.
  useEffect(() => {
    if (forwardCompute?.state !== "running") return;
    const handle = setInterval(async () => {
      const next = await fetchDeskForwardCompute();
      if (!next.ok) return;
      setForwardCompute(next.data);
      if (next.data && next.data.state !== "running") {
        const id = displayedSnapshot?.id ?? null;
        if (id !== null) {
          const refreshed = await fetchDeskForward(id);
          setForwardResult((previous) =>
            refreshed.ok || previous === null || !previous.ok ? refreshed : previous,
          );
        }
      }
    }, 700);
    return () => clearInterval(handle);
  }, [forwardCompute, displayedSnapshot]);

  // Forward-test era: the compute trigger/cancel pair — exact mirrors of the screen pair above,
  // placed here (after `displayedSnapshot`) because the no-argument form submits the DISPLAYED
  // snapshot's own id. Reachable from the panel's buttons and from the refresh chain's fifth
  // step, which passes the id of each snapshot IT recorded — never the displayed one.
  //
  // The `typeof` test is load-bearing, not stylistic: `ForwardControlProps.onTrigger` is typed
  // `() => void` and the button binds it straight to `onClick`, so React hands this function a
  // MouseEvent as its first argument. Without the test that event would be POSTed as a screen id.
  // The `handleTriggerScreen(day?)` precedent above, verbatim.
  async function handleTriggerForward(
    screenId?: string,
  ): Promise<ChainTriggerResult<DeskForwardComputeSnapshot>> {
    const runId = typeof screenId === "string" ? screenId : displayedSnapshot?.id;
    if (runId === undefined) {
      return { ok: false, error: "There is no recorded snapshot to measure." };
    }
    setForwardTriggering(true);
    setForwardTriggerError(null);
    setForwardCancelRequested(false);
    setForwardCancelError(null);
    const result = await triggerDeskForwardCompute(runId);
    setForwardTriggering(false);
    if (result.ok && result.data) {
      setForwardCompute(result.data.compute);
    } else {
      setForwardTriggerError(result.error ?? "The forward compute could not be started.");
    }
    return result;
  }

  async function handleCancelForward() {
    setForwardCancelRequested(true);
    setForwardCancelError(null);
    const result = await cancelDeskForwardCompute();
    if (!result.ok) {
      setForwardCancelRequested(false);
      setForwardCancelError(result.error ?? "The forward compute could not be cancelled.");
    }
  }

  const forwardControlProps: ForwardControlProps = {
    compute: forwardCompute,
    onTrigger: handleTriggerForward,
    triggering: forwardTriggering,
    triggerError: forwardTriggerError,
    onCancel: handleCancelForward,
    cancelRequested: forwardCancelRequested,
    cancelError: forwardCancelError,
    screenId: displayedSnapshot?.id ?? null,
  };

  return (
    <div className="min-h-screen">
      <main className="mx-auto max-w-7xl px-4 py-6">
        <header className="mb-4">
          <h1 data-testid="desk-title" className="text-lg font-semibold text-slate-200">
            Desk
          </h1>
          <p className="mt-1 max-w-3xl text-sm text-slate-500">
            The latest screen over the registered universe — ranked tradable walls, read verbatim
            from GET /research/desk/screen. Run Screen walks the pinned universe as of the To day —
            blank resolves to the upcoming US session date; nothing here is recomputed in the
            browser.
          </p>
        </header>

        {screenResult === null ? (
          <LoadingPanel testid="desk-screen-loading" />
        ) : !screenResult.ok || screenResult.data === null ? (
          <UnavailablePanel
            testid="desk-screen-unavailable"
            message={screenResult.error ?? "The desk screen could not be loaded."}
          />
        ) : latest === null ? (
          <DeskNotComputedPanel
            screen={screenControlProps}
            topup={topupControlProps}
            reconcile={reconcileControlProps}
            refreshChain={refreshChainControlProps}
          />
        ) : (
          // `latest` is narrowed non-null by this ternary's own condition, so `displayedSnapshot ??
          // latest` re-establishes a non-null type for the prop below without an unsafe assertion —
          // the VALUE is unchanged (`displayedSnapshot` already equals `viewingSnapshot ?? latest`).
          <DeskPopulatedScreen
            snapshot={displayedSnapshot ?? latest}
            screens={screens}
            screenIntegrityErrors={screenIntegrityErrors}
            isViewingLatest={isViewingLatest}
            historyFetchError={historyFetchError}
            onSelectHistory={handleSelectHistoryScreen}
            onShowLatest={handleShowLatest}
            selectedHistoryId={selectedHistoryId}
            shownYear={shownYear}
            onShowYear={setViewYear}
            screenControlProps={screenControlProps}
            topupControlProps={topupControlProps}
            reconcileControlProps={reconcileControlProps}
            refreshChainControlProps={refreshChainControlProps}
            forwardResult={forwardResult}
            forwardControlProps={forwardControlProps}
            selectedForwardSymbol={selectedForwardSymbol}
            onSelectForwardSymbol={setSelectedForwardSymbol}
          />
        )}

        {/* era-desk-iter-11 (J-09): rendered independent of the screen conditional above — a
            top-up run's durable history exists (or honestly doesn't) regardless of whether a
            screen has ever been computed; see this file's own top-of-file comment for why this
            placement deliberately differs from the plan's "immediately after Screen History"
            suggestion. */}
        <section aria-label="Top-up runs" className="mt-6">
          <Panel title="Top-up Runs">
            <TopupRunsSection result={topupRunsResult} />
          </Panel>
        </section>

        {/* era-desk-iter-14 (J-10): the SAME "always rendered, independent of screen state"
            placement precedent immediately above, applied to the reconciliation history —
            reconciliation touches only the bar store/index, never a screen. */}
        <section aria-label="Index Reconciliation" className="mt-6">
          <Panel title="Index Reconciliation">
            <ReconciliationSection result={reconcileRunsResult} />
          </Panel>
        </section>

        {/* goal-desk-iter-29 (J-18): a fourth ledger section, the SAME "always rendered,
            independent of screen state" placement precedent as its two siblings above — a screen
            run's durable history (including reused/cancelled/failed runs) exists, or honestly
            doesn't, regardless of whether the ranked briefing above is currently populated. */}
        <section aria-label="Screen Runs" className="mt-6">
          <Panel title="Screen Runs">
            <ScreenRunsSection result={screenRunsResult} />
          </Panel>
        </section>

        {/* goal-desk-iter-35 (J-20): rendered after the ranked briefing table (inside
            DeskPopulatedScreen, far above) and after the three always-on ledger sections. Unlike
            Top-up Runs/Index Reconciliation/Screen Runs above, this section describes a SPECIFIC
            screen (whichever one is currently displayed), so it only renders once a screen exists
            at all (`latest !== null`) — mirroring the Briefing section's own precondition instead
            of those three's "always rendered" one. */}
        {latest !== null && (
          <section aria-label="Screen Comparison" className="mt-6">
            <Panel title="Screen Comparison">
              <ScreenComparisonSection result={screenCompareResult} />
            </Panel>
          </section>
        )}

        {/* The provenance line, rendered DEAD LAST. It used to open the populated view; it is
            reference material — the pins a snapshot was recorded under — and it reads better as
            the footnote to everything above it than as the first thing between the operator and
            the briefing. Same `latest !== null` precondition (and the same non-null
            re-establishment) as the Screen Comparison section directly above. Its own copy points
            BACKWARDS up the page now: "opened from Screen History above". */}
        {latest !== null && (
          <section aria-label="Provenance" className="mt-6">
            <Panel title="Provenance">
              <DeskProvenance
                snapshot={displayedSnapshot ?? latest}
                isViewingLatest={isViewingLatest}
                pins={displayedPinsResult}
              />
            </Panel>
          </section>
        )}
      </main>
    </div>
  );
}
