"use client";

import type {
  CreateStudyParams,
  ResearchTaxonomy,
  Study,
  StudyHorizonRow,
  StudyOccurrence,
  StudyPopulationAggregate,
} from "@/lib/types";

// The study results view (J-60/J-61/J-62). Renders the runner's persisted result VERBATIM (the page
// computes nothing): the setup occurrence distribution SIDE-BY-SIDE with the seeded random-arm-time
// null baseline, per-horizon ternary outcomes (truncated counted SEPARATELY), the occurrence rows,
// the honesty stamps (feed + config fingerprint + recorded seed), the hindsight label where it
// applies, n + caveats, and the "Descriptive only — not trading advice" register.
//
// Honesty discipline baked into the render: a non-terminal study shows its OWN explicit per-status
// absence sentence (iter-15 lesson — never a shared fallback); a cancelled study is marked PARTIAL; a
// failed study shows its explicit error (never an empty success). NEVER a green "success" framing.
// All copy comes from the taxonomy.

function copyOf(copy: Record<string, string> | undefined, key: string, fallback: string): string {
  const v = copy?.[key];
  return typeof v === "string" && v.length > 0 ? v : fallback;
}

export function StudyResultsView({
  study,
  taxonomy,
  onRerun,
}: {
  study: Study;
  taxonomy: ResearchTaxonomy | null;
  onRerun: (params: CreateStudyParams) => void;
}) {
  const copy = taxonomy?.studies?.copy;
  const absence = taxonomy?.studies?.status_absence ?? {};
  const setupLabel =
    taxonomy?.setups?.find((s) => s.id === study.setup_type)?.name ??
    study.setup_type.replace(/_/g, " ");

  const terminalWithResults = study.status === "done" || study.status === "cancelled";

  const rerun = () =>
    onRerun({
      source_kind: study.source_kind as CreateStudyParams["source_kind"],
      source_id: study.source_id,
      setup_type: study.setup_type,
      direction: study.direction,
      level_price: study.level_price ?? undefined,
      null_baseline_seed: study.null_baseline_seed,
    });

  return (
    <section
      data-testid="study-results"
      data-status={study.status}
      data-study-id={study.id}
      className="rounded-lg border border-slate-800 bg-slate-900/40"
    >
      {/* Header — setup × direction + the honesty stamps (feed + the FULL config fingerprint + seed). */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-slate-200">
            {setupLabel} · {study.direction}
          </h2>
          {study.hindsight_level && (
            <span
              data-testid="results-hindsight-label"
              className="rounded border border-amber-800/60 bg-amber-900/20 px-2 py-0.5 text-[11px] text-amber-300"
            >
              {copyOf(copy, "hindsight_level_label", "Level chosen with hindsight")}
            </span>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2 text-[11px]">
          <Stamp label={copyOf(copy, "feed_label", "Feed")} value={study.data_feed} testid="results-feed" />
          <Stamp
            label={copyOf(copy, "fingerprint_label", "Config fingerprint")}
            value={study.config_fingerprint}
            testid="results-fingerprint"
            title={study.config_fingerprint}
          />
          <Stamp
            label={copyOf(copy, "seed_label", "Baseline seed")}
            value={String(study.null_baseline_seed)}
            testid="results-seed"
          />
        </div>
      </div>

      <div className="space-y-5 px-4 py-4">
        {/* The framing line — always one line away from every figure (anti-goal). */}
        <p data-testid="results-framing" className="text-[11px] text-slate-600">
          {copyOf(
            copy,
            "measurement_framing",
            "Journaled measurements of a replay over recorded data — not a profitability claim, an edge, a win rate, or a forecast. Descriptive only — not trading advice.",
          )}
        </p>

        {/* Hindsight caption (when applicable). */}
        {study.hindsight_level && (
          <p
            data-testid="results-hindsight-caption"
            className="rounded-md border border-amber-800/60 bg-amber-900/20 px-3 py-2 text-xs text-amber-200"
          >
            {copyOf(
              copy,
              "hindsight_level_caption",
              "This level setup used a level supplied with hindsight — illustrative only and excluded from any cross-study comparison.",
            )}
          </p>
        )}

        {/* Failed — explicit error, never an empty success. */}
        {study.status === "failed" && (
          <div
            data-testid="results-failed"
            role="alert"
            className="rounded-md border border-rose-700/70 bg-rose-900/30 px-3 py-2 text-sm text-rose-200"
          >
            {absence.failed ??
              "This study could not produce a result. The explicit reason is shown — never an empty success."}
            {study.error && <p className="mt-1 font-mono text-xs text-rose-300/90">{study.error}</p>}
          </div>
        )}

        {/* Queued / running — each status its OWN explicit absence sentence (iter-15 lesson). */}
        {(study.status === "queued" || study.status === "running") && (
          <div
            data-testid="results-status-absence"
            className="rounded-md border border-slate-800 bg-slate-950/40 px-3 py-3 text-sm text-slate-400"
          >
            {absence[study.status] ??
              "This study has not produced results yet — they appear once the replay finishes."}
            {study.status === "running" && study.events_processed != null && (
              <span className="ml-2 font-mono text-amber-300">
                {study.events_processed} {copyOf(copy, "progress_label", "events processed")}
              </span>
            )}
          </div>
        )}

        {/* Cancelled — explicit partial marker over any partial results. */}
        {study.status === "cancelled" && (
          <div
            data-testid="results-cancelled"
            className="rounded-md border border-slate-700 bg-slate-800/40 px-3 py-2 text-xs text-slate-300"
          >
            {absence.cancelled ??
              "This study was cancelled before it finished. Any occurrences shown are PARTIAL — not a complete measurement."}
          </div>
        )}

        {/* The side-by-side distributions (done / cancelled-partial). */}
        {terminalWithResults && study.aggregates && (
          <>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              {copyOf(copy, "results_title", "Results")}
            </h3>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <DistributionBlock
                title={copyOf(copy, "setup_distribution_label", "Your setup")}
                aggregate={study.aggregates.setup}
                copy={copy}
                minSample={study.min_sample_size}
                testid="setup-distribution"
                accent="setup"
              />
              <DistributionBlock
                title={copyOf(copy, "null_baseline_label", "Random-time baseline")}
                caption={copyOf(
                  copy,
                  "null_baseline_caption",
                  "The same window, direction, R definition, and horizons — but arm times drawn at random from a recorded seed.",
                )}
                aggregate={study.aggregates.null_baseline}
                copy={copy}
                minSample={study.min_sample_size}
                testid="null-baseline-distribution"
                accent="null"
              />
            </div>

            {/* The occurrence rows (setup population). */}
            <OccurrencesTable occurrences={study.occurrences ?? []} copy={copy} />

            {/* The occurrence-R definition note (the named design decision, surfaced honestly). */}
            <p data-testid="results-r-caption" className="text-[11px] text-slate-600">
              {copyOf(
                copy,
                "occurrence_r_caption",
                "An auto-armed occurrence has no typed invalidation, so its R is a config-owned synthetic distance from the arm price (a spread multiple on the adverse side) — the same definition for your setup and the random-time baseline.",
              )}
            </p>

            {/* Re-run identical (the J-60 reproducibility affordance). */}
            <button
              type="button"
              data-testid="study-rerun-button"
              onClick={rerun}
              className="rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 transition-colors hover:bg-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 active:bg-slate-800"
            >
              {copyOf(copy, "rerun_button", "Re-run identical")}
            </button>
          </>
        )}

        <p className="text-[11px] text-slate-600">{taxonomy?.disclaimer ?? "Descriptive only — not trading advice."}</p>
      </div>
    </section>
  );
}

function Stamp({
  label,
  value,
  testid,
  title,
}: {
  label: string;
  value: string;
  testid: string;
  title?: string;
}) {
  return (
    <span className="inline-flex items-center gap-1">
      <span className="uppercase tracking-wider text-slate-500">{label}</span>
      <span
        data-testid={testid}
        title={title}
        className="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 font-mono text-slate-300"
      >
        {value}
      </span>
    </span>
  );
}

function DistributionBlock({
  title,
  caption,
  aggregate,
  copy,
  minSample,
  testid,
  accent,
}: {
  title: string;
  caption?: string;
  aggregate: StudyPopulationAggregate;
  copy: Record<string, string> | undefined;
  minSample?: number;
  testid: string;
  accent: "setup" | "null";
}) {
  const insufficient = minSample != null && aggregate.n < minSample;
  return (
    <div
      data-testid={testid}
      data-n={aggregate.n}
      className={`rounded-md border p-3 ${
        accent === "setup" ? "border-slate-700 bg-slate-800/30" : "border-slate-800 bg-slate-950/40"
      }`}
    >
      <div className="flex items-baseline justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-300">{title}</p>
        <span className="text-xs text-slate-400">
          {copyOf(copy, "n_label", "n")} <span className="font-mono text-slate-200">{aggregate.n}</span>
        </span>
      </div>
      {caption && <p className="mt-1 text-[11px] text-slate-600">{caption}</p>}
      {insufficient && (
        <div
          data-testid={`${testid}-insufficient`}
          className="mt-2 rounded border border-amber-800/60 bg-amber-900/20 px-2 py-1 text-[11px] text-amber-200"
        >
          {copyOf(copy, "insufficient_sample_label", "Insufficient sample")}{" "}
          <span className="font-mono">(n = {aggregate.n} &lt; {minSample})</span>
        </div>
      )}
      <div className="mt-2 space-y-1.5">
        {aggregate.horizons.map((row) => (
          <HorizonRow key={row.horizon} row={row} copy={copy} />
        ))}
      </div>
      <p className="mt-1.5 text-[11px] text-slate-600">
        {copyOf(
          copy,
          "truncated_caption",
          "Truncated horizons are counted separately, never folded into the resolved outcomes, never extrapolated.",
        )}
      </p>
    </div>
  );
}

function HorizonRow({ row, copy }: { row: StudyHorizonRow; copy: Record<string, string> | undefined }) {
  return (
    <div
      data-testid="study-horizon-row"
      data-horizon={row.horizon}
      className="flex flex-wrap items-center gap-x-2.5 gap-y-1 rounded border border-slate-800 bg-slate-900/50 px-2.5 py-1.5 text-xs"
    >
      <span className="w-10 font-mono text-slate-400">{row.horizon}s</span>
      <span
        data-testid="study-horizon-plus"
        className="inline-flex items-center gap-1 rounded border border-emerald-800/60 bg-emerald-900/20 px-1.5 py-0.5 text-emerald-300"
      >
        +1R <span className="font-mono">{row["+1R_first"]}</span>
      </span>
      <span
        data-testid="study-horizon-minus"
        className="inline-flex items-center gap-1 rounded border border-rose-800/60 bg-rose-900/20 px-1.5 py-0.5 text-rose-300"
      >
        −1R <span className="font-mono">{row["-1R_first"]}</span>
      </span>
      <span className="inline-flex items-center gap-1 rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-slate-400">
        neither <span className="font-mono">{row.neither_within_horizon}</span>
      </span>
      <span
        data-testid="study-horizon-truncated"
        className="inline-flex items-center gap-1 rounded border border-amber-800/60 bg-amber-900/20 px-1.5 py-0.5 text-amber-300"
      >
        {copyOf(copy, "truncated_label", "Truncated")} <span className="font-mono">{row.truncated}</span>
      </span>
    </div>
  );
}

function OccurrencesTable({
  occurrences,
  copy,
}: {
  occurrences: StudyOccurrence[];
  copy: Record<string, string> | undefined;
}) {
  if (occurrences.length === 0) {
    return (
      <p data-testid="study-occurrences-empty" className="text-xs text-slate-500">
        No setup occurrences armed in this window.
      </p>
    );
  }
  return (
    <div data-testid="study-occurrences">
      <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
        {copyOf(copy, "occurrences_title", "Occurrences")}
      </p>
      <div className="overflow-x-auto rounded-md border border-slate-800">
        <table className="min-w-full text-xs">
          <thead className="bg-slate-900/60 text-slate-500">
            <tr>
              <th className="px-2.5 py-1.5 text-left font-medium uppercase tracking-wider">
                {copyOf(copy, "occurrence_arm_label", "Arm time (logical s)")}
              </th>
              <th className="px-2.5 py-1.5 text-left font-medium uppercase tracking-wider">
                {copyOf(copy, "occurrence_verdict_label", "Verdict reached")}
              </th>
              <th className="px-2.5 py-1.5 text-left font-medium uppercase tracking-wider">
                {copyOf(copy, "occurrence_r_label", "R basis")}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/70">
            {occurrences.map((occ, i) => (
              <tr key={i} data-testid="study-occurrence-row">
                <td className="px-2.5 py-1.5 font-mono text-slate-300">
                  {occ.arm_logical_ts.toFixed(1)}
                </td>
                <td className="px-2.5 py-1.5 text-slate-300">{occ.verdict_summary ?? "—"}</td>
                <td className="px-2.5 py-1.5 font-mono text-slate-300">{occ.r_basis.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
