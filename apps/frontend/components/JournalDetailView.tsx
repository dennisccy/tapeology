"use client";

import { useEffect, useMemo, useState } from "react";
import type {
  ExecutionCheck,
  ExcursionHorizon,
  ExcursionPopulation,
  JournalDetail,
  JournalTimelineRow,
  ResearchTaxonomy,
  StatementFinalStatus,
} from "@/lib/types";
import { formatDateTimeDMY, localOffsetLabel } from "@/lib/datetime";
import { saveReview } from "@/lib/api";

// The per-thesis review-detail body (J-55). Renders the single GET /research/journal/{id} response
// + taxonomy labels VERBATIM — it recomputes NOTHING. Sections, top to bottom: the thesis header,
// the frozen expected-behaviour statements (with their final status), the entry risk flags (or an
// honest "not assessed"), the action marks (price + true clock time + spread-at-mark, realized R
// only when both marks exist), the machine-derived execution checks with evidence + the suggested
// mistake-tag picker (pre-selected, toggleable, disabled Save), and the append-only verdict timeline
// at TRUE clock time. Dark instrument-panel style, consistent with the cockpit + journal list.

// --- shared display helpers ----------------------------------------------------------------------

// The taxonomy-owned label for a setup/direction/status/tag id (the frontend hardcodes none of them).
function labelFrom(
  list: { id: string; name: string }[] | undefined,
  id: string,
): string {
  const found = list?.find((e) => e.id === id);
  return found ? found.name : id.replace(/_/g, " ");
}

// Verdict VISUAL semantics (the design direction): confirming emerald, weakening amber,
// rejecting/invalidated rose (invalidated terminal), pending slate, expired/lifecycle slate. The
// LABEL text comes from the taxonomy; the COLOR is a frontend visual concern keyed off the id.
function verdictClass(verdict: string): string {
  switch (verdict) {
    case "confirming":
      return "border-emerald-700 bg-emerald-900/40 text-emerald-300";
    case "weakening":
      return "border-amber-700 bg-amber-900/40 text-amber-300";
    case "rejecting":
      return "border-rose-700 bg-rose-900/40 text-rose-300";
    case "invalidated":
      return "border-rose-500 bg-rose-950 text-rose-200 ring-1 ring-rose-500/50";
    case "played_out":
    case "abandoned":
      return "border-slate-600 bg-slate-800 text-slate-300";
    case "expired":
    case "watch_restarted":
    case "paused":
      return "border-slate-700 bg-slate-900/60 text-slate-400";
    default:
      // pending + any other
      return "border-slate-600 bg-slate-800 text-slate-300";
  }
}

// Execution-check status VISUAL semantics: failed rose (a flagged execution finding), passed
// emerald, not_applicable slate. These are LABELS, never numeric scores.
const CHECK_STATUS_STYLE: Record<
  ExecutionCheck["status"],
  { chip: string; label: string }
> = {
  failed: {
    chip: "border-rose-700 bg-rose-900/40 text-rose-300",
    label: "Flagged",
  },
  passed: {
    chip: "border-emerald-700 bg-emerald-900/30 text-emerald-300",
    label: "Clean",
  },
  not_applicable: {
    chip: "border-slate-700 bg-slate-800 text-slate-400",
    label: "Not applicable",
  },
};

// A timeline row whose verdict is a GAP/segment delimiter (not a published verdict transition) —
// rendered with a muted, distinct treatment so a gap reads explicitly as an interruption.
const GAP_VERDICTS = new Set(["watch_restarted", "paused", "expired"]);

// Statement FINAL-status VISUAL semantics (J-55): met emerald (the premise resolved true), violated
// rose (the read contradicted it), not_yet/not_evaluated slate (no contradicting read / no read at
// the terminal moment). These are LABELS read verbatim — the page never re-derives them.
const STATEMENT_STATUS_STYLE: Record<
  StatementFinalStatus["status"],
  { chip: string; label: string }
> = {
  met: { chip: "border-emerald-700 bg-emerald-900/30 text-emerald-300", label: "Met" },
  violated: { chip: "border-rose-700 bg-rose-900/40 text-rose-300", label: "Violated" },
  not_yet: { chip: "border-slate-700 bg-slate-800 text-slate-400", label: "Not met" },
  not_evaluated: {
    chip: "border-slate-700 bg-slate-800 text-slate-400",
    label: "Not evaluated",
  },
};

// Outcome-grade VISUAL semantics (J-56): held emerald, failed rose, no_read slate. Process-grade
// VISUAL semantics: clean emerald, flagged amber, violated rose. The LABEL text comes from the
// taxonomy; the COLOR is a frontend visual concern keyed off the id.
function outcomeGradeClass(grade: string): string {
  switch (grade) {
    case "thesis_held":
      return "border-emerald-700 bg-emerald-900/40 text-emerald-300";
    case "thesis_failed":
      return "border-rose-700 bg-rose-900/40 text-rose-300";
    default:
      return "border-slate-600 bg-slate-800 text-slate-300";
  }
}
function processGradeClass(grade: string): string {
  switch (grade) {
    case "clean":
      return "border-emerald-700 bg-emerald-900/40 text-emerald-300";
    case "flagged":
      return "border-amber-700 bg-amber-900/40 text-amber-300";
    case "violated":
      return "border-rose-700 bg-rose-900/40 text-rose-300";
    default:
      return "border-slate-600 bg-slate-800 text-slate-300";
  }
}

// Ternary excursion-outcome chip COLOR (J-58): +1R_first emerald (the tape reached +1R first),
// -1R_first rose (adverse first), neither slate (no R target touched within the horizon). The LABEL
// text comes from the taxonomy; the COLOR is a frontend visual concern keyed off the id. These are
// descriptive outcome LABELS in R units — never a prediction, never currency, never a numeric score.
function excursionOutcomeClass(outcome: string | null): string {
  switch (outcome) {
    case "+1R_first":
      return "border-emerald-700 bg-emerald-900/40 text-emerald-300";
    case "-1R_first":
      return "border-rose-700 bg-rose-900/40 text-rose-300";
    default:
      // neither_within_horizon + null (open/undetermined)
      return "border-slate-600 bg-slate-800 text-slate-400";
  }
}

// One signed R figure, formatted to 2 dp with an explicit sign and the R unit (never currency).
function formatR(value: number): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}R`;
}

interface Props {
  detail: JournalDetail;
  taxonomy: ResearchTaxonomy | null;
  // Called after a review is saved successfully so the page re-reads the detail (the saved tags +
  // note + reviewed status then render from the persisted record — never client-derived).
  onSaved?: () => void;
}

export function JournalDetailView({ detail, taxonomy, onSaved }: Props) {
  const { thesis, marks, timeline } = detail;
  const directionColor =
    thesis.direction === "long" ? "text-emerald-400" : "text-rose-400";
  const tz = localOffsetLabel();

  return (
    <div data-testid="journal-detail" data-thesis-id={thesis.id} className="space-y-5">
      {/* --- Thesis header ------------------------------------------------------------------- */}
      <section className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <span className="font-mono text-base font-semibold text-slate-100">
              {thesis.ticker}
            </span>
            <span className="text-sm text-slate-300">
              {labelFrom(taxonomy?.setups, thesis.setup_type)}
            </span>
            <span className={`text-xs font-semibold uppercase ${directionColor}`}>
              {labelFrom(taxonomy?.directions, thesis.direction)}
            </span>
          </div>
          <span
            data-testid="detail-status-chip"
            data-status={thesis.status}
            className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${verdictClass(
              thesis.status,
            )}`}
          >
            {labelFrom(taxonomy?.statuses, thesis.status)}
          </span>
        </div>
        <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs sm:grid-cols-3">
          <div>
            <dt className="text-slate-500">Invalidation</dt>
            <dd className="font-mono text-slate-200">
              {thesis.invalidation_price.toFixed(2)}
            </dd>
          </div>
          {thesis.level_price !== null && (
            <div>
              <dt className="text-slate-500">Level</dt>
              <dd className="font-mono text-slate-200">
                {thesis.level_price.toFixed(2)}
              </dd>
            </div>
          )}
          <div>
            <dt className="text-slate-500">Declared</dt>
            <dd className="font-mono text-slate-300">
              {formatDateTimeDMY(thesis.created_wall_ts * 1000, false)} {tz}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Bound source</dt>
            <dd className="font-mono text-slate-400">{thesis.bound_source}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Feed</dt>
            <dd className="font-mono uppercase text-slate-400">{thesis.data_feed}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Config fingerprint</dt>
            <dd className="font-mono text-slate-500">{thesis.config_fingerprint}</dd>
          </div>
        </dl>
      </section>

      {/* --- Expected behaviour (frozen statements + their persisted FINAL status, J-55) ------ */}
      <Section title="What you expected" testid="detail-statements">
        {thesis.statements.length === 0 ? (
          <p className="text-sm text-slate-500">No expected-behaviour statements were frozen.</p>
        ) : (
          <ul className="space-y-2">
            {thesis.statements.map((s, i) => {
              // The persisted FINAL status, positionally keyed to the frozen statement (J-55). The
              // page renders this verbatim — it NEVER re-derives a status from the timeline. Absent
              // (a pre-v6 resolution) => no badge (honest omission).
              const finalStatus = detail.statement_final_statuses?.[i]?.status;
              const style = finalStatus ? STATEMENT_STATUS_STYLE[finalStatus] : null;
              return (
                <li
                  key={i}
                  data-testid="detail-statement"
                  data-final-status={finalStatus ?? "absent"}
                  className="flex items-start justify-between gap-3 text-sm text-slate-300"
                >
                  <span className="flex items-start gap-2">
                    <span aria-hidden="true" className="mt-1 text-slate-600">
                      •
                    </span>
                    <span>{s.text}</span>
                  </span>
                  {style && (
                    <span
                      data-testid="detail-statement-final-status"
                      data-status={finalStatus}
                      className={`mt-0.5 inline-flex shrink-0 rounded-full border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${style.chip}`}
                    >
                      {style.label}
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        )}
        {detail.statement_final_statuses === undefined && (
          <p
            data-testid="statement-final-statuses-not-recorded"
            className="mt-2 text-xs text-slate-500"
          >
            Final statuses were not recorded for this thesis — it predates per-statement status
            tracking.
          </p>
        )}
      </Section>

      {/* --- Outcome × process grades (the review quadrant, J-56) --------------------------- */}
      <GradesQuadrant detail={detail} taxonomy={taxonomy} />

      {/* --- Entry risk flags (frozen) ------------------------------------------------------ */}
      <Section title="Entry risk flags" testid="detail-risk-flags">
        {thesis.risk_flags === undefined ? (
          <p data-testid="risk-flags-not-assessed" className="text-sm text-slate-500">
            Not assessed — this thesis predates entry-risk assessment.
          </p>
        ) : thesis.risk_flags.length === 0 ? (
          <p className="text-sm text-slate-500">
            Assessed at declaration — no entry risk flags fired.
          </p>
        ) : (
          <ul className="space-y-2">
            {thesis.risk_flags.map((f) => (
              <li
                key={f.flag}
                data-testid="detail-risk-flag-chip"
                data-flag={f.flag}
                className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 rounded-md border-l-2 border-amber-500 border-y border-r border-y-amber-700/60 border-r-amber-700/60 bg-amber-900/30 px-2.5 py-1.5"
              >
                <span className="text-xs font-semibold uppercase tracking-wide text-amber-300">
                  {f.label}
                </span>
                <span className="font-mono text-xs text-amber-200/90">{f.evidence}</span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      {/* --- Action marks ------------------------------------------------------------------- */}
      <Section title="What you did" testid="detail-marks">
        {!marks.entry && !marks.exit ? (
          <p className="text-sm text-slate-500">
            No entry or exit was journaled for this thesis.
          </p>
        ) : (
          <div className="space-y-2 text-sm">
            {marks.entry && (
              <div data-testid="detail-entry-mark" className="flex flex-wrap items-baseline gap-x-3">
                <span className="text-xs uppercase tracking-wide text-slate-500">Entry</span>
                <span className="font-mono text-slate-200">{marks.entry.price.toFixed(2)}</span>
                <span className="font-mono text-xs text-slate-500">
                  {formatDateTimeDMY(marks.entry.wall_ts * 1000, true)} {tz}
                </span>
                {marks.entry.spread_at_mark !== null && (
                  <span className="font-mono text-xs text-slate-500">
                    spread {marks.entry.spread_at_mark.toFixed(2)}
                  </span>
                )}
              </div>
            )}
            {marks.exit && (
              <div data-testid="detail-exit-mark" className="flex flex-wrap items-baseline gap-x-3">
                <span className="text-xs uppercase tracking-wide text-slate-500">Exit</span>
                <span className="font-mono text-slate-200">{marks.exit.price.toFixed(2)}</span>
                <span className="font-mono text-xs text-slate-500">
                  {formatDateTimeDMY(marks.exit.wall_ts * 1000, true)} {tz}
                </span>
                {marks.exit.spread_at_mark !== null && (
                  <span className="font-mono text-xs text-slate-500">
                    spread {marks.exit.spread_at_mark.toFixed(2)}
                  </span>
                )}
              </div>
            )}
            {/* Realized move in R — present ONLY when both marks exist (no marks, no realized
                metric; never a dishonest zero). A journaled MEASUREMENT in R units — never P&L. */}
            {marks.realized_r !== null && (
              <p data-testid="detail-realized-r" className="pt-1 text-sm text-slate-300">
                Realized move:{" "}
                <span
                  className={`font-mono font-semibold ${
                    marks.realized_r >= 0 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {marks.realized_r >= 0 ? "+" : ""}
                  {marks.realized_r.toFixed(2)}R
                </span>
                {marks.r_basis !== null && (
                  <span className="ml-2 font-mono text-xs text-slate-500">
                    (R = {marks.r_basis.toFixed(2)})
                  </span>
                )}
              </p>
            )}
          </div>
        )}
      </Section>

      {/* --- Execution checks + the review save flow ---------------------------------------- */}
      <ExecutionChecksSection detail={detail} taxonomy={taxonomy} onSaved={onSaved} />

      {/* --- Excursion outcomes (two segregated populations, J-58) -------------------------- */}
      <ExcursionsSection detail={detail} taxonomy={taxonomy} tz={tz} />

      {/* --- Verdict timeline (true clock time) --------------------------------------------- */}
      <Section title="What the tape did" testid="detail-timeline">
        {timeline.length === 0 ? (
          <p className="text-sm text-slate-500">No verdict timeline was recorded.</p>
        ) : (
          <ol className="space-y-2">
            {timeline.map((row, i) => (
              <TimelineRow key={i} row={row} taxonomy={taxonomy} tz={tz} />
            ))}
          </ol>
        )}
      </Section>

      <p data-testid="detail-disclaimer" className="pt-1 text-center text-xs text-slate-600">
        {taxonomy?.disclaimer ?? "Descriptive only — not trading advice."}
      </p>
    </div>
  );
}

// --- a labeled section card ----------------------------------------------------------------------

function Section({
  title,
  testid,
  children,
}: {
  title: string;
  testid: string;
  children: React.ReactNode;
}) {
  return (
    <section
      data-testid={testid}
      className="rounded-lg border border-slate-800 bg-slate-900/40 p-4"
    >
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
        {title}
      </h2>
      {children}
    </section>
  );
}

// --- one verdict-timeline row --------------------------------------------------------------------

function TimelineRow({
  row,
  taxonomy,
  tz,
}: {
  row: JournalTimelineRow;
  taxonomy: ResearchTaxonomy | null;
  tz: string;
}) {
  const isGap = GAP_VERDICTS.has(row.verdict);
  const label = labelFrom(taxonomy?.verdicts, row.verdict);
  return (
    <li
      data-testid="detail-timeline-row"
      data-verdict={row.verdict}
      className={`rounded-md border p-3 ${
        isGap ? "border-dashed border-slate-700 bg-slate-900/30" : "border-slate-800 bg-slate-900/50"
      }`}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span
          className={`inline-flex rounded-full border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${verdictClass(
            row.verdict,
          )}`}
        >
          {label}
        </span>
        {/* TRUE clock time from the persisted wall_ts (the ONE shared dd-MM-yyyy formatter) — never
            elapsed playback seconds, never client-side re-derivation. */}
        <span
          data-testid="detail-timeline-time"
          className="font-mono text-xs text-slate-500"
        >
          {formatDateTimeDMY(row.wall_ts * 1000, true)} {tz}
        </span>
      </div>
      {/* The verbatim evidence — every published verdict carries plain-language evidence (no naked
          outputs). */}
      <p className="mt-1.5 text-sm text-slate-300">{row.evidence}</p>
      <div className="mt-1 flex flex-wrap gap-x-4 text-xs text-slate-500">
        {row.last !== null && (
          <span className="font-mono">last {row.last.toFixed(2)}</span>
        )}
        {row.tape_state !== null && (
          <span className="font-mono">{row.tape_state.replace(/_/g, " ")}</span>
        )}
        {row.confidence !== null && (
          <span className="font-mono">conf {row.confidence.toFixed(2)}</span>
        )}
        {/* The dwell timing record (capability 24) — when the raw rule first held, distinct from the
            published instant. Present only on a published raw-rule transition. */}
        {row.rule_first_true_price !== null && (
          <span className="font-mono">
            rule first true @ {row.rule_first_true_price.toFixed(2)}
          </span>
        )}
      </div>
    </li>
  );
}

// --- outcome × process grade quadrant (J-56) -----------------------------------------------------

function GradesQuadrant({
  detail,
  taxonomy,
}: {
  detail: JournalDetail;
  taxonomy: ResearchTaxonomy | null;
}) {
  const grades = detail.grades;
  return (
    <Section title="How it graded" testid="detail-grades">
      {grades === undefined ? (
        // Honest omission: a pre-v6 resolution (or an unresolved thesis) was never graded — never an
        // invented grade, never a numeric score.
        <p data-testid="grades-not-graded" className="text-sm text-slate-500">
          Not graded — the outcome and process grades are computed once a thesis is resolved, and
          this thesis predates that.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {/* Outcome — 1:1 from the resolution. ENUM label from the taxonomy, never a number. */}
            <div
              data-testid="grade-outcome"
              data-grade={grades.outcome}
              className="rounded-md border border-slate-800 bg-slate-900/50 p-3"
            >
              <p className="text-xs uppercase tracking-wider text-slate-500">Outcome</p>
              <span
                className={`mt-1.5 inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${outcomeGradeClass(
                  grades.outcome,
                )}`}
              >
                {labelFrom(taxonomy?.outcome_grades, grades.outcome)}
              </span>
            </div>
            {/* Process — the config-owned rule over the named checks. ENUM label, never a number. */}
            <div
              data-testid="grade-process"
              data-grade={grades.process}
              className="rounded-md border border-slate-800 bg-slate-900/50 p-3"
            >
              <p className="text-xs uppercase tracking-wider text-slate-500">Process</p>
              <span
                className={`mt-1.5 inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${processGradeClass(
                  grades.process,
                )}`}
              >
                {labelFrom(taxonomy?.process_grades, grades.process)}
              </span>
            </div>
          </div>
          {/* The plain-language evidence naming the checks/flags that drove the PROCESS grade (no
              naked grade) — read verbatim. Being invalidated is never itself a process failure. */}
          <p data-testid="grade-process-evidence" className="mt-3 text-xs text-slate-400">
            {grades.process_evidence}
          </p>
        </>
      )}
    </Section>
  );
}

// --- excursion outcomes: two segregated populations (J-58) ---------------------------------------

// The R-units excursion review surface: two VISUALLY SEPARATE blocks — "From first confirmation" and
// "From entry mark" — each with its anchor (true-clock time, mono reference price, spread-at-anchor,
// R basis) and per-horizon rows (horizon, MFE/MAE in R, the ternary outcome chip, a TRUNCATED flag).
// Every value is read VERBATIM from the persisted record + taxonomy — the page derives nothing. R
// units only — no currency, no prediction. The two populations are never pooled (independent anchors,
// independent R bases, independent rows). Honest absence: a missing population reads its explicit
// not-applicable copy; the restart-sweep `tracked:false` reads the not-tracked copy; a pre-v7 thesis
// (no `excursions` key) reads the honest-omission copy.
const EXCURSION_POPULATION_ORDER = ["confirmation", "entry"] as const;

function ExcursionsSection({
  detail,
  taxonomy,
  tz,
}: {
  detail: JournalDetail;
  taxonomy: ResearchTaxonomy | null;
  tz: string;
}) {
  const excursions = detail.excursions;
  const copy = taxonomy?.excursions;
  return (
    <Section title="How far the tape went (R)" testid="detail-excursions">
      {excursions === undefined ? (
        // Honest omission: a pre-v7 resolution (or an unresolved thesis) never had excursions
        // measured — never fabricated numbers, never computed at read.
        <p data-testid="excursions-not-measured" className="text-sm text-slate-500">
          Not measured — excursions are computed once a thesis runs its course, and this thesis
          predates that.
        </p>
      ) : excursions.tracked === false ? (
        // The explicit restart-sweep marker: no live tape to measure from — no numbers, not a zero.
        <p data-testid="excursions-not-tracked" className="text-sm text-slate-500">
          {copy?.not_tracked ??
            "Excursions were not tracked for this thesis — it resolved with no live tape to measure against."}
        </p>
      ) : (
        <div className="space-y-4">
          {EXCURSION_POPULATION_ORDER.map((popId) => (
            <ExcursionPopulationBlock
              key={popId}
              popId={popId}
              population={excursions.populations[popId]}
              taxonomy={taxonomy}
              tz={tz}
            />
          ))}
          {/* The R-basis caption + the no-cost caveat: R is defined once, and the spread cost sits
              beside every figure (the no-cost caveat is always one line away). */}
          <p data-testid="excursions-r-basis-caption" className="text-xs text-slate-600">
            {copy?.r_basis_caption ?? "R = |reference − invalidation|"} · measured in R units only, never
            currency. The spread at each anchor is shown beside its reference as the round-trip cost.
          </p>
        </div>
      )}
    </Section>
  );
}

function ExcursionPopulationBlock({
  popId,
  population,
  taxonomy,
  tz,
}: {
  popId: string;
  population: ExcursionPopulation | undefined;
  taxonomy: ResearchTaxonomy | null;
  tz: string;
}) {
  const copy = taxonomy?.excursions;
  const title = labelFrom(copy?.populations, popId);
  // Honest absence: the population never armed (never-confirmed / no entry mark) — its explicit
  // not-applicable copy, never a dishonest zero row.
  if (!population) {
    return (
      <div
        data-testid="excursion-population"
        data-population={popId}
        data-present="false"
        className="rounded-md border border-dashed border-slate-700 bg-slate-900/30 p-3"
      >
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</p>
        <p
          data-testid="excursion-not-applicable"
          className="mt-1.5 text-sm text-slate-500"
        >
          {copy?.not_applicable?.[popId] ??
            "No anchor exists for this population, so there is no excursion to measure — no anchor, no metric."}
        </p>
      </div>
    );
  }
  return (
    <div
      data-testid="excursion-population"
      data-population={popId}
      data-present="true"
      className="rounded-md border border-slate-800 bg-slate-900/50 p-3"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-300">{title}</p>
        <span
          data-testid="excursion-anchor-time"
          className="font-mono text-xs text-slate-500"
        >
          {formatDateTimeDMY(population.anchor_wall_ts * 1000, true)} {tz}
        </span>
      </div>
      {/* The anchor detail line: reference price (mono), R basis, and the moment spread-at-anchor. */}
      <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-slate-500">
        <span className="font-mono">
          reference{" "}
          <span data-testid="excursion-reference-price" className="text-slate-300">
            {population.reference_price.toFixed(2)}
          </span>
        </span>
        <span className="font-mono">
          R ={" "}
          <span data-testid="excursion-r-basis" className="text-slate-300">
            {population.r_basis.toFixed(2)}
          </span>
        </span>
        <span className="font-mono" data-testid="excursion-spread-at-anchor">
          spread{" "}
          <span className="text-slate-300">
            {population.spread_at_anchor !== null
              ? population.spread_at_anchor.toFixed(2)
              : "—"}
          </span>
        </span>
      </div>
      {/* Per-horizon rows: horizon, MFE (R), MAE (R), the ternary outcome chip, and a TRUNCATED flag
          where set. Sorted by horizon ascending for a stable, glanceable read. */}
      <ul className="mt-2.5 space-y-1.5">
        {[...population.horizons]
          .sort((a, b) => a.horizon - b.horizon)
          .map((h) => (
            <ExcursionHorizonRow key={h.horizon} h={h} taxonomy={taxonomy} />
          ))}
      </ul>
    </div>
  );
}

function ExcursionHorizonRow({
  h,
  taxonomy,
}: {
  h: ExcursionHorizon;
  taxonomy: ResearchTaxonomy | null;
}) {
  const copy = taxonomy?.excursions;
  const outcomeLabel = labelFrom(copy?.ternary_outcomes, h.outcome ?? "");
  return (
    <li
      data-testid="excursion-horizon"
      data-horizon={h.horizon}
      data-outcome={h.outcome ?? "open"}
      data-truncated={h.truncated}
      className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 rounded border border-slate-800/80 bg-slate-900/40 px-2.5 py-1.5 text-xs"
    >
      <span className="font-mono font-semibold text-slate-300">{h.horizon}s</span>
      <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
        {/* MFE / MAE in R — descriptive measurements, never currency. */}
        <span className="font-mono text-emerald-400" data-testid="excursion-mfe">
          MFE {formatR(h.mfe_r)}
        </span>
        <span className="font-mono text-rose-400" data-testid="excursion-mae">
          MAE {formatR(h.mae_r)}
        </span>
        {/* The ternary outcome chip (by first touch). Absent (null) when the horizon was truncated
            before any first touch — the TRUNCATED flag then carries the meaning. */}
        {h.outcome !== null && (
          <span
            data-testid="excursion-outcome-chip"
            className={`inline-flex rounded-full border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${excursionOutcomeClass(
              h.outcome,
            )}`}
          >
            {outcomeLabel}
          </span>
        )}
        {/* TRUNCATED — the stream end / a gap cut this horizon short before its outcome resolved.
            Declared explicitly, never hidden, never extrapolated. */}
        {h.truncated && (
          <span
            data-testid="excursion-truncated"
            className="inline-flex rounded-full border border-amber-700 bg-amber-900/30 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-amber-300"
          >
            {copy?.truncated_label ?? "Truncated"}
          </span>
        )}
      </span>
    </li>
  );
}

// --- execution checks + the review save flow (J-54 / J-57) ---------------------------------------

function ExecutionChecksSection({
  detail,
  taxonomy,
  onSaved,
}: {
  detail: JournalDetail;
  taxonomy: ResearchTaxonomy | null;
  onSaved?: () => void;
}) {
  const checks = detail.execution_checks;
  const suggested = useMemo(
    () => detail.suggested_mistake_tags ?? [],
    [detail.suggested_mistake_tags],
  );
  const thesisId = detail.thesis.id;
  const alreadyReviewed = detail.reviewed;
  const savedReview = detail.review;

  // The picker seeds from the backend's SUGGESTED tags (the system suggests; the user confirms). On
  // an ALREADY-reviewed thesis it seeds from the user's CONFIRMED tags so the saved selection shows.
  // Re-seed whenever the underlying detail changes (a fresh load after save).
  const initialSelected = useMemo(
    () => (alreadyReviewed && savedReview ? savedReview.mistake_tags : suggested),
    [alreadyReviewed, savedReview, suggested],
  );
  const [selected, setSelected] = useState<Set<string>>(() => new Set(initialSelected));
  const [note, setNote] = useState<string>(() => savedReview?.note ?? "");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  useEffect(() => {
    setSelected(new Set(initialSelected));
    setNote(savedReview?.note ?? "");
    setSaveError(null);
  }, [initialSelected, savedReview]);

  function toggle(tag: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) next.delete(tag);
      else next.add(tag);
      return next;
    });
  }

  // The taxonomy owns which tags REQUIRE a note (the frontend hardcodes none). `other` is the one.
  const tagsRequiringNote = useMemo(
    () =>
      new Set(
        (taxonomy?.mistake_tags ?? []).filter((t) => t.requires_note).map((t) => t.id),
      ),
    [taxonomy?.mistake_tags],
  );
  const selectedTags = useMemo(() => Array.from(selected), [selected]);
  const needsNote = selectedTags.some((t) => tagsRequiringNote.has(t));
  const noteMissing = needsNote && note.trim() === "";
  const canSave = !saving && !noteMissing;

  async function onSave() {
    if (!canSave) return;
    setSaving(true);
    setSaveError(null);
    const result = await saveReview(thesisId, selectedTags, note.trim() === "" ? null : note);
    setSaving(false);
    if (result.ok) {
      onSaved?.();
    } else {
      setSaveError(result.error ?? "The review could not be saved.");
    }
  }

  return (
    <Section title="What the execution checks found" testid="detail-execution-checks">
      {checks === undefined ? (
        // Honest omission: a pre-v5 resolution (or an unresolved thesis) never had its checks
        // computed — never an invented clean state, never a fabricated pass/fail.
        <p data-testid="execution-checks-not-assessed" className="text-sm text-slate-500">
          Not assessed — execution checks are computed once a thesis is resolved, and this thesis
          predates that.
        </p>
      ) : (
        <>
          <ul className="space-y-2">
            {checks.map((c) => {
              const style = CHECK_STATUS_STYLE[c.status];
              return (
                <li
                  key={c.check}
                  data-testid="detail-execution-check"
                  data-check={c.check}
                  data-status={c.status}
                  className="rounded-md border border-slate-800 bg-slate-900/50 p-3"
                >
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <span className="text-sm font-medium text-slate-200">
                      {c.check.replace(/_/g, " ")}
                    </span>
                    <span
                      className={`inline-flex rounded-full border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${style.chip}`}
                    >
                      {style.label}
                    </span>
                  </div>
                  {/* Plain-language evidence quoting the measured values (no naked outputs). */}
                  <p className="mt-1.5 text-xs text-slate-400">{c.evidence}</p>
                </li>
              );
            })}
          </ul>

          {/* The review save flow (J-57). The picker seeds from the backend's SUGGESTED tags
              (system suggests) and the user CONFIRMS via Save (only the user records a confirmed
              tag). The suggested set stays visibly distinct from the user-confirmed set. */}
          <div data-testid="mistake-tag-picker" className="mt-4 border-t border-slate-800 pt-3">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Mistake tags
            </p>
            {suggested.length > 0 && (
              <p data-testid="suggested-tags-note" className="mb-2 text-xs text-slate-500">
                Suggested from the execution checks:{" "}
                <span className="text-slate-400">
                  {suggested.map((t) => labelFrom(taxonomy?.mistake_tags, t)).join(", ")}
                </span>
                . Toggle any that apply, then save to confirm.
              </p>
            )}
            {(taxonomy?.mistake_tags ?? []).length === 0 ? (
              <p className="text-xs text-slate-500">The tag catalog could not be loaded.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {(taxonomy?.mistake_tags ?? []).map((tag) => {
                  const isSelected = selected.has(tag.id);
                  const isSuggested = suggested.includes(tag.id);
                  return (
                    <button
                      key={tag.id}
                      type="button"
                      data-testid="mistake-tag"
                      data-tag={tag.id}
                      data-selected={isSelected}
                      data-suggested={isSuggested}
                      aria-pressed={isSelected}
                      disabled={alreadyReviewed}
                      onClick={() => toggle(tag.id)}
                      className={
                        "rounded-full border px-2.5 py-1 text-xs font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-emerald-500 " +
                        (alreadyReviewed ? "cursor-default " : "") +
                        (isSelected
                          ? "border-amber-600 bg-amber-900/40 text-amber-200 hover:bg-amber-900/60"
                          : "border-slate-700 bg-slate-800/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200")
                      }
                    >
                      {tag.name}
                      {isSuggested && (
                        <span className="ml-1 text-[10px] text-slate-500" aria-hidden="true">
                          ·sug
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            )}

            {/* The required-note input — shown (and required) only when a note-requiring tag (other)
                is selected. Inline validation copy is honest and descriptive. */}
            {needsNote && (
              <div className="mt-3" data-testid="review-note-field">
                <label
                  htmlFor="review-note"
                  className="mb-1 block text-xs font-medium text-slate-400"
                >
                  Note (required for “Other”)
                </label>
                <textarea
                  id="review-note"
                  data-testid="review-note-input"
                  value={note}
                  disabled={alreadyReviewed}
                  onChange={(e) => setNote(e.target.value)}
                  rows={2}
                  placeholder="Describe what happened in your own words."
                  className="w-full rounded border border-slate-700 bg-slate-900/60 px-2.5 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-500 disabled:opacity-60"
                />
                {noteMissing && (
                  <p data-testid="review-note-error" className="mt-1 text-xs text-rose-300">
                    A note is required when “Other” is selected.
                  </p>
                )}
              </div>
            )}

            {/* Save — enabled once a resolved, not-yet-reviewed thesis has a valid selection. After
                a save the thesis is reviewed: the control reports the reviewed state and the saved
                tags + note render from the re-read detail (never client-derived). */}
            {alreadyReviewed ? (
              <div className="mt-3" data-testid="review-saved">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-700 bg-emerald-900/30 px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide text-emerald-300">
                  Reviewed
                </span>
                <p className="mt-2 text-xs text-slate-400">
                  {savedReview && savedReview.mistake_tags.length > 0 ? (
                    <>
                      You confirmed:{" "}
                      <span data-testid="confirmed-tags" className="text-slate-300">
                        {savedReview.mistake_tags
                          .map((t) => labelFrom(taxonomy?.mistake_tags, t))
                          .join(", ")}
                      </span>
                      .
                    </>
                  ) : (
                    "You reviewed this thesis with no mistake tags."
                  )}
                </p>
                {savedReview?.note && (
                  <p data-testid="confirmed-note" className="mt-1 text-xs text-slate-400">
                    Note: <span className="text-slate-300">{savedReview.note}</span>
                  </p>
                )}
              </div>
            ) : (
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  data-testid="save-review"
                  disabled={!canSave}
                  aria-disabled={!canSave}
                  onClick={onSave}
                  className={
                    "rounded border px-3 py-1.5 text-sm font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-emerald-500 " +
                    (canSave
                      ? "border-emerald-600 bg-emerald-900/40 text-emerald-200 hover:bg-emerald-900/60"
                      : "cursor-not-allowed border-slate-700 bg-slate-800/50 text-slate-500")
                  }
                >
                  {saving ? "Saving…" : "Save review"}
                </button>
                {noteMissing && (
                  <span className="text-xs text-slate-500">
                    Add the required note to save.
                  </span>
                )}
                {saveError && (
                  <span data-testid="save-review-error" role="alert" className="text-xs text-rose-300">
                    {saveError}
                  </span>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </Section>
  );
}
