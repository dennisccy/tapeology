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
  fetchDeskScreenByDate,
  fetchDeskScreenCompute,
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
  DeskScreenComputeSnapshot,
  DeskScreenListResult,
  DeskScreenMeta,
  DeskScreenRow,
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

const NUMERIC_CELL = "px-2 py-1.5 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
const HEADER_CELL = "px-2 py-1 text-right text-[11px] font-medium text-slate-500";
const HEADER_CELL_LEFT = "px-2 py-1 text-left text-[11px] font-medium text-slate-500";
const LABEL_CELL = "px-2 py-1.5 text-left text-xs text-slate-400 whitespace-nowrap";

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
    <span data-testid="desk-coverage-badges" className="flex flex-wrap gap-1">
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
  return `distance ${row.distance_bps} bps · score ${row.band_score} · ${basisLine} · ${historyLine}${
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
// a per-cell `title` (iter-7 audit F1: this comment used to claim the opposite). The basis and
// history columns follow the SAME split: a rounded, date-only display with the full-precision
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
function DeskRow({ row, asOf }: { row: DeskScreenRow; asOf: string }) {
  return (
    <tr
      data-testid="desk-screen-row"
      data-symbol={row.symbol}
      data-band-class={row.band_class ?? "none"}
      className="relative border-b border-slate-800/60 last:border-b-0 hover:bg-slate-900/40"
    >
      <td className={LABEL_CELL} data-testid="desk-row-symbol">
        <Link
          href={`/structure?symbol=${encodeURIComponent(row.symbol)}&asof=${encodeURIComponent(asOf)}`}
          data-testid="desk-row-drill-in"
          aria-label={`Open ${row.symbol} in Structure as of ${asOf}`}
          title={deskRowDrillInTitle(row)}
          className="absolute inset-0"
        />
        {row.symbol}
      </td>
      <td className={LABEL_CELL} data-testid="desk-row-side">
        {row.side}
      </td>
      <td className={LABEL_CELL} data-testid="desk-row-band-class">
        {row.band_class !== null ? (
          <>
            <span>{`Class ${row.band_class}`}</span>
            <span className="block text-[11px] text-slate-500">nearest same-class band</span>
          </>
        ) : (
          "Unclassified"
        )}
      </td>
      <td className={NUMERIC_CELL} data-testid="desk-row-distance" title={String(row.distance_bps)}>
        {fmt(row.distance_bps)} bps
      </td>
      <td className={NUMERIC_CELL} data-testid="desk-row-score" title={String(row.band_score)}>
        {fmt(row.band_score)}
      </td>
      <td className="px-2 py-1.5 text-left" data-testid="desk-row-coverage">
        <DeskCoverageBadges coverage={row.coverage} />
      </td>
      <td className="px-2 py-1.5 text-left">
        {row.tick_evidence && <TickEvidenceBadge testid="desk-row-tick-evidence" />}
      </td>
      {/* era-desk-iter-9 (J-08): descriptive only, date portion of `basis_as_of` (full precision
          lives in the row anchor's own composite `title` above -- NEVER a per-cell `title` here,
          the iter-6/iter-7 F2 lesson applied proactively: a per-cell title under the stretched
          `absolute inset-0` anchor is pointer-unreachable). `== null` catches a legacy row's
          ENTIRELY ABSENT keys (`undefined`), not just an explicit `null`. */}
      <td className={LABEL_CELL} data-testid="desk-row-basis">
        {row.basis_as_of == null || row.basis_age_days == null
          ? "basis not recorded in this snapshot"
          : `basis ${row.basis_as_of.slice(0, 10)} · ${row.basis_age_days} d before as-of`}
      </td>
      {/* era-desk-iter-15 (J-11): descriptive only, session count + start date (full precision --
          the untruncated `history_start` -- lives in the row anchor's own composite `title` above,
          NEVER a per-cell `title` here, the same F2 lesson the basis column above already applies).
          `== null` catches a legacy row's ENTIRELY ABSENT keys (`undefined`), not just `null`. */}
      <td className={LABEL_CELL} data-testid="desk-row-history">
        {row.history_sessions == null || row.history_start == null
          ? "history not recorded in this snapshot"
          : `history ${row.history_sessions} sessions · from ${row.history_start.slice(0, 10)}`}
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
      <table data-testid="desk-screen-rows-table" className="w-full border-collapse">
        <thead>
          <tr className="border-b border-slate-800">
            <th className={HEADER_CELL_LEFT}>symbol</th>
            <th className={HEADER_CELL_LEFT}>side</th>
            <th className={HEADER_CELL_LEFT}>class</th>
            <th className={HEADER_CELL}>distance</th>
            <th className={HEADER_CELL}>score</th>
            <th className={HEADER_CELL_LEFT}>coverage</th>
            <th className={HEADER_CELL_LEFT}>tick evidence</th>
            <th className={HEADER_CELL_LEFT}>basis</th>
            <th className={HEADER_CELL_LEFT}>history</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <DeskRow key={row.symbol} row={row} asOf={asOf} />
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
// jumping to `/structure`). `selectedDate` highlights the currently-displayed row (`null` while
// viewing the latest screen, since the latest need not be one of the listed historical rows). -----

function DeskHistoryRow({
  meta,
  onSelect,
  selected,
}: {
  meta: DeskScreenMeta;
  onSelect: (date: string) => void;
  selected: boolean;
}) {
  return (
    <tr
      data-testid="desk-history-row"
      data-screen-date={meta.screen_date}
      data-selected={selected}
      onClick={() => onSelect(meta.screen_date)}
      className={`cursor-pointer border-b border-slate-800/60 transition-colors last:border-b-0 hover:bg-slate-900/40 ${
        selected ? "bg-slate-800/60" : ""
      }`}
    >
      <td className={LABEL_CELL}>{meta.screen_date}</td>
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
  selectedDate,
}: {
  screens: DeskScreenMeta[];
  onSelect: (date: string) => void;
  selectedDate: string | null;
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
              selected={meta.screen_date === selectedDate}
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

function topupOutcomeCounts(outcomes: DeskTopupOutcome[]): {
  reused: number;
  fetched: number;
  failed: number;
} {
  return {
    reused: outcomes.filter((o) => o.outcome === "reused").length,
    fetched: outcomes.filter((o) => o.outcome === "fetched").length,
    failed: outcomes.filter((o) => o.outcome === "failed").length,
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
          {counts.reused} reused · {counts.fetched} fetched · {counts.failed} failed
        </span>
        {unreached > 0 && (
          <span data-testid="desk-topup-run-latest-unreached" className="text-amber-200/70">
            {unreached} pair{unreached === 1 ? "" : "s"} not reached
          </span>
        )}
      </div>
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
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
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
    </div>
  );
}

// --- Provenance line — universe snapshot id + date, as_of, config_fingerprint, and the pinned
// bar-store signature. --------------------------------------------------------------------------
//
// The signature's LABEL (era-desk-iter-4 audit F1): `bar_store_signature` is a checksum —
// `sha256(sorted (symbol, timeframe, latest_window_end_utc) tuples)[:16]` (desk_screen.py) — not a
// timestamp. Labelling it "Window last requested" (as this line first shipped, following the spec
// and blueprint wording verbatim) put a false claim on a hex digest: the operator read
// "Window last requested  d7bc8f8127904d0a". The freshness LABEL belongs to the value that really
// is a window end — each coverage badge's own `latest_window_end_utc` tooltip, which keeps it. Here
// the honest name is the signature's own, with a caption saying what it summarizes. The blueprint's
// registered wording is amended in the same commit.
function DeskProvenance({ snapshot }: { snapshot: DeskScreenSnapshot }) {
  return (
    <div data-testid="desk-provenance">
      <Metric label="Universe snapshot" value={snapshot.universe_snapshot_id ?? "—"} />
      <Metric label="Screen date" value={snapshot.screen_date} />
      <Metric label="As of" value={snapshot.as_of} />
      <Metric label="Config fingerprint" value={snapshot.config_fingerprint} />
      <Metric label="Bar-store signature" value={snapshot.bar_store_signature} />
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
  isViewingLatest,
  historyFetchError,
  onSelectHistory,
  onShowLatest,
  selectedHistoryDate,
  screenControlProps,
  topupControlProps,
  reconcileControlProps,
}: {
  snapshot: DeskScreenSnapshot;
  screens: DeskScreenMeta[];
  isViewingLatest: boolean;
  historyFetchError: string | null;
  onSelectHistory: (date: string) => void;
  onShowLatest: () => void;
  selectedHistoryDate: string | null;
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
          <DeskProvenance snapshot={snapshot} />
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
            selectedDate={selectedHistoryDate}
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

  // era-desk-iter-6 (J-05): the screen-history click-through. `viewingSnapshot` is `null` while
  // showing the top-level `latest` snapshot already held in `screenResult` (no refetch needed to
  // return to it — TC-2); once a history row is selected, it holds THAT date's own full snapshot,
  // fetched via the already-shipped `?date=` read (`fetchDeskScreenByDate`, zero new backend
  // route). `historyFetchError` surfaces a failed/no-match click WITHOUT disturbing whatever is
  // currently displayed (no crash, no blank state — the plan's own error-case requirement).
  const [viewingSnapshot, setViewingSnapshot] = useState<DeskScreenSnapshot | null>(null);
  const [historyFetchError, setHistoryFetchError] = useState<string | null>(null);

  // Mount: six GETs, zero POSTs (TC-19/TC-8, extended era-desk-iter-14) — the screen list/latest,
  // ALL THREE compute managers' current/last snapshot (seeds a page load mid-job or post-terminal
  // without a spurious extra click — the /structure edge-report mount-seeding precedent), the
  // top-up run log's list + latest full record (era-desk-iter-11, J-09), and (era-desk-iter-14,
  // J-10) the reconciliation run log's list + latest full record.
  useEffect(() => {
    let alive = true;
    fetchDeskScreen().then((result) => {
      if (alive) setScreenResult(result);
    });
    fetchDeskScreenCompute().then((result) => {
      if (alive && result.ok) setScreenCompute(result.data);
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
  // (TC-1). A date with no matching recorded screen (`{"screen": null}`) or an unreachable backend
  // both leave the currently-displayed snapshot exactly as it was — only the error note changes.
  async function handleSelectHistoryScreen(date: string) {
    setHistoryFetchError(null);
    const result = await fetchDeskScreenByDate(date);
    if (result.ok && result.data !== null) {
      setViewingSnapshot(result.data);
      return;
    }
    setHistoryFetchError(
      result.ok
        ? `No recorded screen matches ${date} — still showing the previously displayed screen.`
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
            isViewingLatest={isViewingLatest}
            historyFetchError={historyFetchError}
            onSelectHistory={handleSelectHistoryScreen}
            onShowLatest={handleShowLatest}
            selectedHistoryDate={viewingSnapshot?.screen_date ?? null}
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
      </main>
    </div>
  );
}
