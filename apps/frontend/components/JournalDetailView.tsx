"use client";

import { useEffect, useMemo, useState } from "react";
import type {
  ExecutionCheck,
  JournalDetail,
  JournalTimelineRow,
  ResearchTaxonomy,
} from "@/lib/types";
import { formatDateTimeDMY, localOffsetLabel } from "@/lib/datetime";

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

interface Props {
  detail: JournalDetail;
  taxonomy: ResearchTaxonomy | null;
}

export function JournalDetailView({ detail, taxonomy }: Props) {
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

      {/* --- Expected behaviour (frozen statements) ----------------------------------------- */}
      <Section title="What you expected" testid="detail-statements">
        {thesis.statements.length === 0 ? (
          <p className="text-sm text-slate-500">No expected-behaviour statements were frozen.</p>
        ) : (
          <ul className="space-y-2">
            {thesis.statements.map((s, i) => (
              <li
                key={i}
                data-testid="detail-statement"
                className="flex items-start gap-2 text-sm text-slate-300"
              >
                <span aria-hidden="true" className="mt-1 text-slate-600">
                  •
                </span>
                <span>{s.text}</span>
              </li>
            ))}
          </ul>
        )}
        <p className="mt-2 text-xs text-slate-500">
          The final status of each statement is read from the verdict timeline below — the timeline
          is the canonical record.
        </p>
      </Section>

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

      {/* --- Execution checks + suggested mistake-tag picker -------------------------------- */}
      <ExecutionChecksSection detail={detail} taxonomy={taxonomy} />

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

// --- execution checks + suggested mistake-tag picker ---------------------------------------------

function ExecutionChecksSection({
  detail,
  taxonomy,
}: {
  detail: JournalDetail;
  taxonomy: ResearchTaxonomy | null;
}) {
  const checks = detail.execution_checks;
  const suggested = useMemo(
    () => detail.suggested_mistake_tags ?? [],
    [detail.suggested_mistake_tags],
  );

  // The picker is pre-selected with the backend's SUGGESTED tags and toggleable — but NOT yet
  // savable (the J-57 review save flow lands next iteration). The local toggle state seeds from the
  // suggestions; the system never records a confirmed tag on its own. Re-seed if the thesis changes.
  const [selected, setSelected] = useState<Set<string>>(() => new Set(suggested));
  useEffect(() => {
    setSelected(new Set(suggested));
  }, [suggested]);

  function toggle(tag: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) next.delete(tag);
      else next.add(tag);
      return next;
    });
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

          {/* Suggested mistake tags — pre-selected + toggleable; the tag labels come ONLY from the
              taxonomy. The Save affordance is present but DISABLED with honest copy (the review save
              flow lands with J-57 — mirrors the approved Studies-disabled no-dead-control pattern). */}
          <div data-testid="mistake-tag-picker" className="mt-4 border-t border-slate-800 pt-3">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Suggested mistake tags
            </p>
            {(taxonomy?.mistake_tags ?? []).length === 0 ? (
              <p className="text-xs text-slate-500">The tag catalog could not be loaded.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {(taxonomy?.mistake_tags ?? []).map((tag) => {
                  const isSelected = selected.has(tag.id);
                  return (
                    <button
                      key={tag.id}
                      type="button"
                      data-testid="mistake-tag"
                      data-tag={tag.id}
                      data-selected={isSelected}
                      aria-pressed={isSelected}
                      onClick={() => toggle(tag.id)}
                      className={
                        "rounded-full border px-2.5 py-1 text-xs font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-emerald-500 " +
                        (isSelected
                          ? "border-amber-600 bg-amber-900/40 text-amber-200 hover:bg-amber-900/60"
                          : "border-slate-700 bg-slate-800/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200")
                      }
                    >
                      {tag.name}
                    </button>
                  );
                })}
              </div>
            )}
            <p className="mt-2 text-xs text-slate-500">
              These are suggested from the execution checks — toggle any that apply. You confirm
              them when saving a review.
            </p>
            <div className="mt-3">
              <button
                type="button"
                data-testid="save-review-disabled"
                disabled
                aria-disabled="true"
                title="Saving a review lands with the review flow"
                className="cursor-not-allowed rounded border border-slate-700 bg-slate-800/50 px-3 py-1.5 text-sm font-medium text-slate-500"
              >
                Save review
              </button>
              <span className="ml-2 text-xs text-slate-600">
                Saving a review is coming with the review flow.
              </span>
            </div>
          </div>
        </>
      )}
    </Section>
  );
}
