"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  cancelDeskScreenCompute,
  cancelDeskTopupCompute,
  fetchDeskScreen,
  fetchDeskScreenByDate,
  fetchDeskScreenCompute,
  fetchDeskTopupCompute,
  triggerDeskScreenCompute,
  triggerDeskTopupCompute,
} from "@/lib/api";
import type {
  DeskScreenComputeSnapshot,
  DeskScreenListResult,
  DeskScreenMeta,
  DeskScreenRow,
  DeskScreenSkip,
  DeskScreenSnapshot,
  DeskTopupComputeSnapshot,
} from "@/lib/types";
import { Metric, Panel } from "@/components/Panel";
import { fmt } from "@/lib/format";

// The /desk page (Era B "The Desk" J-04) — the third top-nav page, reached from the persistent
// NavBar (data-driven from GET /meta/ui-routes; no client hardcoding, see apps/backend/app/meta.py
// UI_ROUTES). Renders the LATEST screen snapshot as a dense, descriptive briefing: ranked rows
// (band class/distance/score/coverage/tick-evidence, all read verbatim), an honestly-grouped
// skipped-members section, a provenance line, and a read-only screen-history list. "Run Screen"
// and "Top-up" wire the J-03/J-02 compute managers with live progress + cancel — mirrors the
// Edge Report Compute button UX pattern already shipped on /structure (NotComputedPanel/poll-loop).
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

// One ranked row: symbol, side, band-class chip, distance-bps chip, band score, per-timeframe
// coverage badges, tick-evidence badge — the DoD's exact column list, every value read verbatim
// from the snapshot. Distance and score are DISPLAYED to two decimals (a `0.33523150389608725 bps`
// cell defeated the scanability the briefing exists for — audit F3); each cell's `title` carries the
// served value in full, so nothing is lost, only formatted. The band-class chip carries the
// "nearest same-class band" caption
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

// The honest empty state (TC-1): rendered iff `latest === null` — no screen has EVER been
// computed. Doubles as the controls panel for a first-ever run (both Run Screen and Top-up live
// here since there is nothing else to show yet); once a screen exists, the SAME two controls move
// to a plain panel at the foot of the populated page (see DeskPage below).
function DeskNotComputedPanel({
  screen,
  topup,
}: {
  screen: ScreenControlProps;
  topup: TopupControlProps;
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

      <section aria-label="Run Screen and Top-up controls">
        <Panel title="Run Screen / Top-up">
          <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start sm:justify-center sm:gap-12">
            <ScreenComputeControl {...screenControlProps} />
            <TopupComputeControl {...topupControlProps} />
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

  // era-desk-iter-6 (J-05): the screen-history click-through. `viewingSnapshot` is `null` while
  // showing the top-level `latest` snapshot already held in `screenResult` (no refetch needed to
  // return to it — TC-2); once a history row is selected, it holds THAT date's own full snapshot,
  // fetched via the already-shipped `?date=` read (`fetchDeskScreenByDate`, zero new backend
  // route). `historyFetchError` surfaces a failed/no-match click WITHOUT disturbing whatever is
  // currently displayed (no crash, no blank state — the plan's own error-case requirement).
  const [viewingSnapshot, setViewingSnapshot] = useState<DeskScreenSnapshot | null>(null);
  const [historyFetchError, setHistoryFetchError] = useState<string | null>(null);

  // Mount: exactly three GETs, zero POSTs (TC-19) — the screen list/latest, and BOTH compute
  // managers' current/last snapshot (seeds a page load mid-job or post-terminal without a
  // spurious extra click — the /structure edge-report mount-seeding precedent).
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
  // compute managers are separate processes-scoped jobs).
  useEffect(() => {
    if (topupCompute?.state !== "running") return;
    const handle = setInterval(async () => {
      const next = await fetchDeskTopupCompute();
      if (next.ok) setTopupCompute(next.data);
    }, 700);
    return () => clearInterval(handle);
  }, [topupCompute]);

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
          <DeskNotComputedPanel screen={screenControlProps} topup={topupControlProps} />
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
          />
        )}
      </main>
    </div>
  );
}
