"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  cancelDeskReconcileCompute,
  cancelDeskScreenCompute,
  cancelDeskTopupCompute,
  fetchDeskReconcileCompute,
  fetchDeskReconcileRuns,
  fetchDeskScreen,
  fetchDeskScreenById,
  fetchDeskScreenCompare,
  fetchDeskScreenCompute,
  fetchDeskScreenRuns,
  fetchDeskTopupCompute,
  fetchDeskTopupRuns,
  triggerDeskReconcileCompute,
  triggerDeskScreenCompute,
  triggerDeskTopupCompute,
} from "@/lib/api";
import type {
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

// The secondary (quieter) button styling for the "Latest" history control — mirrors
// structure/page.tsx's own `SECONDARY_BUTTON_CLASS` byte-for-byte (each page owns its own copy of
// this tiny constant per this project's established convention — see this file's own
// LoadingPanel/UnavailablePanel comment above).
const SECONDARY_BUTTON_CLASS =
  "rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm font-medium text-slate-400 transition-colors hover:border-slate-600 hover:bg-slate-800 hover:text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-950";

// Today's UTC calendar date (YYYY-MM-DD) — the value "Run Screen" submits as `screen_date`.
// Mirrors /structure's own `todayUtcDate()` helper byte-for-byte (this project's own convention:
// each module owns its tiny formatting helper rather than sharing one — see desk_screen.py's
// `_iso` docstring). UTC, never the browser's local date, so the submitted date always matches
// what the backend's own session-close basis resolves.
function todayUtcDate(): string {
  return new Date().toISOString().slice(0, 10);
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

function DeskRowsTable({ rows, asOf }: { rows: DeskScreenRow[]; asOf: string }) {
  const uncoveredRanked = rows.filter((row) => hasNoCoverageAtAll(row.coverage)).length;
  return (
    <div className="overflow-x-auto">
      {uncoveredRanked > 0 && (
        <p data-testid="desk-coverage-divergence-note" className="mb-2 text-[11px] text-slate-600">
          {uncoveredRanked} ranked row(s) below show every timeframe badge dark. A row&apos;s rank
          comes from the bar store the screen read directly; its coverage badges come from the
          derived bar index — two independent reads, each rendered as served. A dark badge set beside
          a ranked row therefore means the index holds no entry for that pair, not that the screen
          ranked a symbol whose bars it never read.
        </p>
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
          `scrollWidth === clientWidth` and no horizontal scrollbar can appear. */}
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
          {rows.map((row, index) => (
            <DeskRow key={row.symbol} row={row} asOf={asOf} rank={index + 1} />
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

// --- Screen history — date + rows/skipped counts + provenance summary, from the meta-only
// `screens` list. era-desk-iter-6 (J-05): now CLICKABLE — selecting a row fetches that exact
// date's persisted snapshot (`GET /research/desk/screen?date=`) and swaps it into the page's
// display in place; the click-through itself is a same-page state swap, never a navigation, so it
// stays a plain `onClick` (not a `Link` — the `Link`/drill-in requirement below is only for
// jumping to `/structure`).
//
// goal-desk-iter-16 (J-12): selection/highlighting switches from `screen_date`-keyed to
// `id`-keyed — the store's own 5-pin key already allows two recordings under the SAME
// `screen_date` (a pre-/post-repair pair, e.g.), and a `screen_date`-keyed select/highlight could
// only ever reach or distinguish one of the two. Each row now also shows its own `created_utc`
// beside `screen_date` so two same-date rows read distinctly without opening either. `selectedId`
// highlights the currently-displayed row's own id (see `DeskPage`'s `displayedSnapshot?.id`, which
// covers BOTH a selected history entry and the default latest view). ------------------------------

function DeskHistoryRow({
  meta,
  onSelect,
  selected,
}: {
  meta: DeskScreenMeta;
  onSelect: (id: string) => void;
  selected: boolean;
}) {
  return (
    <tr
      data-testid="desk-history-row"
      data-screen-id={meta.id}
      data-screen-date={meta.screen_date}
      data-selected={selected}
      onClick={() => onSelect(meta.id)}
      className={`cursor-pointer border-b border-slate-800/60 transition-colors last:border-b-0 hover:bg-slate-900/40 ${
        selected ? "bg-slate-800/60" : ""
      }`}
    >
      <td className={LABEL_CELL}>{meta.screen_date}</td>
      <td className={LABEL_CELL} data-testid="desk-history-created-utc">
        {meta.created_utc}
      </td>
      <td className={NUMERIC_CELL}>{meta.counts.rows}</td>
      <td className={NUMERIC_CELL}>{meta.counts.skipped}</td>
      <td className={LABEL_CELL} data-testid="desk-history-provenance">
        {meta.universe_snapshot_id ?? "—"} · {meta.config_fingerprint} · {meta.bar_store_signature}
      </td>
    </tr>
  );
}

function DeskHistoryTable({
  screens,
  onSelect,
  selectedId,
}: {
  screens: DeskScreenMeta[];
  onSelect: (id: string) => void;
  selectedId: string | null;
}) {
  if (screens.length === 0) {
    return <EmptyState testid="desk-history-empty" title="No screens recorded yet." />;
  }
  return (
    <div className="overflow-x-auto">
      <table data-testid="desk-history-table" className="w-full border-collapse">
        <thead>
          <tr className="border-b border-slate-800">
            <th className={HEADER_CELL_LEFT}>date</th>
            <th className={HEADER_CELL_LEFT}>recorded</th>
            <th className={HEADER_CELL}>rows</th>
            <th className={HEADER_CELL}>skipped</th>
            <th className={HEADER_CELL_LEFT}>provenance</th>
          </tr>
        </thead>
        <tbody>
          {screens.map((meta) => (
            <DeskHistoryRow
              key={meta.id}
              meta={meta}
              onSelect={onSelect}
              selected={meta.id === selectedId}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

// --- Top-up run history (era-desk-iter-11, J-09) — a durable, append-only record of every top-up
// run's outcome, read verbatim from `GET /research/desk/topup/runs` and nothing recomputed. Two
// tiers, mirroring the meta-only-list / full-latest split the backend itself serves (the SAME
// split `DeskHistoryTable` above uses for screens): `TopupRunsTable` renders every recorded run's
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
// and be reachable from Screen History below.
function DeskProvenance({
  snapshot,
  isViewingLatest,
}: {
  snapshot: DeskScreenSnapshot;
  isViewingLatest: boolean;
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
          Screen History below.
        </p>
      )}
      <p data-testid="desk-provenance-signature-note" className="mt-1 text-[11px] text-slate-600">
        The bar-store signature is a checksum over every member&apos;s window-last-requested
        timestamp at the moment this screen was computed — a pin, never a time. Each coverage
        badge&apos;s tooltip carries that member&apos;s own window-last-requested value.
      </p>
    </div>
  );
}

// --- Run Screen / Top-up controls — mirrors /structure's NotComputedPanel Compute-button UX
// pattern (live progress with a pulsing dot, a Cancel control while running, error/cancelled
// copy) applied to two independent compute managers. Kept as two separate, non-generic
// components (rather than one shared abstraction) since their progress shapes genuinely differ
// (members vs pairs+outcomes) — this project's own simplicity convention. --------------------------

function ScreenComputeControl({
  compute,
  onTrigger,
  triggering,
  triggerError,
  onCancel,
  cancelRequested,
  cancelError,
}: {
  compute: DeskScreenComputeSnapshot | null;
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
      <button
        type="button"
        data-testid="desk-run-screen-button"
        onClick={onTrigger}
        disabled={triggering || isRunning}
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

interface ScreenControlProps {
  compute: DeskScreenComputeSnapshot | null;
  onTrigger: () => void;
  triggering: boolean;
  triggerError: string | null;
  onCancel: () => void;
  cancelRequested: boolean;
  cancelError: string | null;
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
// here since there is nothing else to show yet); once a screen exists, the SAME two controls move
// to a plain panel at the foot of the populated page (see DeskPage below).
function DeskNotComputedPanel({
  screen,
  topup,
  reconcile,
}: {
  screen: ScreenControlProps;
  topup: TopupControlProps;
  reconcile: ReconcileControlProps;
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
      <div className="mt-3 flex flex-col items-center gap-6 sm:flex-row sm:items-start sm:justify-center sm:gap-12">
        <ScreenComputeControl {...screen} />
        <TopupComputeControl {...topup} />
        <ReconcileIndexControl {...reconcile} />
      </div>
    </div>
  );
}

// The populated view — a real snapshot exists (`latest !== null`), whether it is the latest one
// or a history row the operator selected. `snapshot` is the ONE displayed record; the Provenance/
// Briefing/Skipped sections read it verbatim, same as before this iteration — only the SOURCE of
// `snapshot` (latest vs. a selected history entry) is new.
function DeskPopulatedScreen({
  snapshot,
  screens,
  screenIntegrityErrors,
  isViewingLatest,
  historyFetchError,
  onSelectHistory,
  onShowLatest,
  selectedHistoryId,
  screenControlProps,
  topupControlProps,
  reconcileControlProps,
}: {
  snapshot: DeskScreenSnapshot;
  screens: DeskScreenMeta[];
  screenIntegrityErrors: { file: string; error: string }[];
  isViewingLatest: boolean;
  historyFetchError: string | null;
  onSelectHistory: (id: string) => void;
  onShowLatest: () => void;
  selectedHistoryId: string | null;
  screenControlProps: ScreenControlProps;
  topupControlProps: TopupControlProps;
  reconcileControlProps: ReconcileControlProps;
}) {
  return (
    <div className="space-y-6">
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

      <section aria-label="Provenance">
        <Panel title="Provenance">
          <DeskProvenance snapshot={snapshot} isViewingLatest={isViewingLatest} />
        </Panel>
      </section>

      <section aria-label="Briefing">
        <Panel title="Briefing">
          {snapshot.rows.length === 0 ? (
            <EmptyState testid="desk-rows-empty" title="No members ranked in this screen." />
          ) : (
            <DeskRowsTable rows={snapshot.rows} asOf={snapshot.as_of} />
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

      <section aria-label="Screen history">
        <Panel title="Screen History">
          <DeskHistoryTable
            screens={screens}
            onSelect={onSelectHistory}
            selectedId={selectedHistoryId}
          />
          <IntegrityErrorsNote
            errors={screenIntegrityErrors}
            testid="desk-screen-history-integrity-errors"
          />
        </Panel>
      </section>

      <section aria-label="Run Screen, Top-up and Reconcile Index controls">
        <Panel title="Run Screen / Top-up / Reconcile Index">
          <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start sm:justify-center sm:gap-12">
            <ScreenComputeControl {...screenControlProps} />
            <TopupComputeControl {...topupControlProps} />
            <ReconcileIndexControl {...reconcileControlProps} />
          </div>
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

  // goal-desk-iter-35 (J-20): the Screen Comparison section's own fetch result, keyed off
  // WHICHEVER screen is currently displayed (`viewingSnapshot ?? latest`, the SAME
  // `displayedSnapshot` value computed below) — refetched by its own effect whenever that id
  // changes, independent of the seven mount-time GETs above.
  const [screenCompareResult, setScreenCompareResult] = useState<{
    ok: boolean;
    data: DeskScreenCompareResult | null;
    error?: string;
  } | null>(null);

  // Mount: seven GETs, zero POSTs (TC-19/TC-8, extended era-desk-iter-14/goal-desk-iter-29) — the
  // screen list/latest, ALL THREE compute managers' current/last snapshot (seeds a page load
  // mid-job or post-terminal without a spurious extra click — the /structure edge-report
  // mount-seeding precedent), the top-up run log's list + latest full record (era-desk-iter-11,
  // J-09), the reconciliation run log's list + latest full record (era-desk-iter-14, J-10), and
  // (goal-desk-iter-29, J-18) the screen run log's list + latest full record.
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
    return () => {
      alive = false;
    };
  }, []);

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
      }
    }, 700);
    return () => clearInterval(handle);
  }, [screenCompute]);

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

  async function handleTriggerScreen() {
    setScreenTriggering(true);
    setScreenTriggerError(null);
    setScreenCancelRequested(false);
    setScreenCancelError(null);
    const result = await triggerDeskScreenCompute(todayUtcDate());
    setScreenTriggering(false);
    if (result.ok && result.data) {
      setScreenCompute(result.data.compute);
    } else {
      setScreenTriggerError(result.error ?? "The screen compute could not be started.");
    }
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

  async function handleTriggerTopup() {
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

  async function handleTriggerReconcile() {
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
  // goal-desk-iter-16 (J-12): the id-based highlight for `DeskHistoryTable` — the SAME id the
  // above `isViewingLatest` check already compares against, so the currently-displayed snapshot
  // (a selected history entry OR the default `latest`) is always the one highlighted row, even
  // when it shares its `screen_date` with another recorded entry.
  const selectedHistoryId = viewingSnapshot?.id ?? latest?.id ?? null;

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

  return (
    <div className="min-h-screen">
      <main className="mx-auto max-w-7xl px-4 py-6">
        <header className="mb-4">
          <h1 data-testid="desk-title" className="text-lg font-semibold text-slate-200">
            Desk
          </h1>
          <p className="mt-1 max-w-3xl text-sm text-slate-500">
            The latest screen over the registered universe — ranked tradable walls, read verbatim
            from GET /research/desk/screen. Run Screen walks the pinned universe as of today;
            nothing here is recomputed in the browser.
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
            screenControlProps={screenControlProps}
            topupControlProps={topupControlProps}
            reconcileControlProps={reconcileControlProps}
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

        {/* goal-desk-iter-35 (J-20): rendered LAST on the page — after the ranked briefing table
            (inside DeskPopulatedScreen, far above) and after every other existing section — so no
            shipped golden's own first-visible-match text search can resolve into it (goal.md step
            6). Unlike Top-up Runs/Index Reconciliation/Screen Runs above, this section describes a
            SPECIFIC screen (whichever one is currently displayed), so it only renders once a
            screen exists at all (`latest !== null`) — mirroring the Briefing/Provenance sections'
            own precondition instead of those three's "always rendered" one. */}
        {latest !== null && (
          <section aria-label="Screen Comparison" className="mt-6">
            <Panel title="Screen Comparison">
              <ScreenComparisonSection result={screenCompareResult} />
            </Panel>
          </section>
        )}
      </main>
    </div>
  );
}
