"use client";

import type {
  Analytics,
  AnalyticsGroup,
  AnalyticsHorizonRow,
  AnalyticsPartition,
  AnalyticsTaxonomy,
  ResearchTaxonomy,
} from "@/lib/types";

// The segregated journal analytics view (capability 31, J-59). Renders the GET /research/analytics
// payload VERBATIM — the frontend recomputes NOTHING (display rounding only, no client-side
// arithmetic, no percentages). Partition blocks are keyed by (data_feed, config_fingerprint) and are
// NEVER pooled (two fingerprints => two separate blocks); within each, groups are per setup × direction.
//
// Honesty discipline baked into the render (the anti-goals this rides):
//   * the abandonment bucket is ALWAYS shown (even 0) and counted in n (no survivorship pruning);
//   * a group below the min sample shows the explicit insufficient-sample marker WITH its n;
//   * truncated horizon counts are a SEPARATE chip, never folded into the resolved ternary buckets;
//   * the acted-trade block is VISUALLY SEPARATE from the confirmation-anchored block;
//   * median spread/R sits beside every +1R figure (the no-cost caveat as a number);
//   * R units only — no currency symbol, no equity curve, no win-rate-as-edge presentation anywhere.
// All labels/captions/framing come from the taxonomy (the frontend hardcodes none); a pre-J-59
// taxonomy falls back to a minimal local copy register so the view never blocks render.

// A small helper: read an analytics copy key from the taxonomy, falling back to a provided default.
function copyOf(
  copy: AnalyticsTaxonomy | undefined,
  key: string,
  fallback: string,
): string {
  const v = copy?.[key];
  return typeof v === "string" && v.length > 0 ? v : fallback;
}

// The taxonomy-owned display label for a setup / direction id (the frontend hardcodes none of them).
function labelFrom(
  list: { id: string; name: string }[] | undefined,
  id: string,
): string {
  return list?.find((e) => e.id === id)?.name ?? id.replace(/_/g, " ");
}

// Display rounding ONLY (no arithmetic): an R figure to 2 dp, a spread/R to 4 dp (it is a tiny ratio),
// seconds to 1 dp. `null` reads as an explicit em-dash (honest absence, never a fabricated 0).
function fmtR(value: number | null): string {
  return value === null ? "—" : value.toFixed(2);
}
function fmtSpreadR(value: number | null): string {
  return value === null ? "—" : value.toFixed(4);
}
function fmtSeconds(value: number | null): string {
  return value === null ? "—" : value.toFixed(1);
}

export function AnalyticsView({
  analytics,
  taxonomy,
}: {
  analytics: Analytics;
  taxonomy: ResearchTaxonomy | null;
}) {
  const copy = taxonomy?.analytics;
  const framing = copyOf(
    copy,
    "measurement_framing",
    "Journaled measurements of your own theses — not a profitability claim, an edge, or a forecast. Never pooled across feeds or config fingerprints.",
  );

  return (
    <section data-testid="analytics-view" className="space-y-6">
      {/* The honesty framing line — always one line away from every figure (anti-goal). */}
      <p data-testid="analytics-framing" className="text-xs text-slate-500">
        {framing}
      </p>

      {analytics.partitions.length === 0 ? (
        <div
          data-testid="analytics-empty"
          className="flex min-h-[20vh] flex-col items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-10 text-center"
        >
          <span className="text-2xl text-slate-700">∅</span>
          <p className="mt-2 text-sm text-slate-500">
            {copyOf(
              copy,
              "empty",
              "No theses recorded yet — declare and resolve a thesis to populate the analytics.",
            )}
          </p>
        </div>
      ) : (
        analytics.partitions.map((partition) => (
          <PartitionBlock
            key={`${partition.data_feed}:${partition.config_fingerprint}`}
            partition={partition}
            copy={copy}
            minSample={analytics.min_sample_size}
            taxonomy={taxonomy}
          />
        ))
      )}
    </section>
  );
}

// One (data_feed, config_fingerprint) partition — its own block. Two fingerprints render as two
// separate blocks (the never-pool guarantee, made visible). The FULL fingerprint is shown (mono) so
// records are never silently compared across fingerprints; the feed label sits beside it.
function PartitionBlock({
  partition,
  copy,
  minSample,
  taxonomy,
}: {
  partition: AnalyticsPartition;
  copy: AnalyticsTaxonomy | undefined;
  minSample: number;
  taxonomy: ResearchTaxonomy | null;
}) {
  return (
    <div
      data-testid="analytics-partition"
      data-feed={partition.data_feed}
      data-fingerprint={partition.config_fingerprint}
      className="rounded-lg border border-slate-800 bg-slate-900/40"
    >
      {/* Partition header — feed + the full config fingerprint (mono). The never-pool stamps. */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-slate-800 px-4 py-3">
        <span className="inline-flex items-center gap-1.5 text-sm">
          <span className="text-xs uppercase tracking-wider text-slate-500">
            {copyOf(copy, "data_feed_label", "Feed")}
          </span>
          <span
            data-testid="partition-feed"
            className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-xs uppercase text-slate-200"
          >
            {partition.data_feed}
          </span>
        </span>
        <span className="inline-flex items-center gap-1.5 text-sm">
          <span className="text-xs uppercase tracking-wider text-slate-500">
            {copyOf(copy, "fingerprint_label", "Config fingerprint")}
          </span>
          <span
            data-testid="partition-fingerprint"
            title={partition.config_fingerprint}
            className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-xs text-slate-400"
          >
            {partition.config_fingerprint}
          </span>
        </span>
      </div>

      {/* The per setup × direction groups. */}
      <div className="divide-y divide-slate-800/70">
        {partition.groups.map((group) => (
          <GroupBlock
            key={`${group.setup_type}:${group.direction}`}
            group={group}
            copy={copy}
            minSample={minSample}
            taxonomy={taxonomy}
          />
        ))}
      </div>
    </div>
  );
}

// One setup × direction group within a partition.
function GroupBlock({
  group,
  copy,
  minSample,
  taxonomy,
}: {
  group: AnalyticsGroup;
  copy: AnalyticsTaxonomy | undefined;
  minSample: number;
  taxonomy: ResearchTaxonomy | null;
}) {
  const directionClass =
    group.direction === "long"
      ? "border-emerald-700/60 bg-emerald-900/20 text-emerald-300"
      : "border-rose-700/60 bg-rose-900/20 text-rose-300";

  return (
    <div
      data-testid="analytics-group"
      data-setup={group.setup_type}
      data-direction={group.direction}
      className="px-4 py-4"
    >
      {/* Group header — setup × direction + the always-visible n and abandonment bucket. */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-200">
            {labelFrom(taxonomy?.setups, group.setup_type)}
          </span>
          <span
            className={`inline-flex rounded-full border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${directionClass}`}
          >
            {labelFrom(taxonomy?.directions, group.direction)}
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs">
          {/* n — always present (abandoned theses stay in it). */}
          <span data-testid="group-n" className="text-slate-400">
            {copyOf(copy, "n_label", "n")}{" "}
            <span className="font-mono text-slate-200">{group.n}</span>
          </span>
          {/* Abandonment bucket — ALWAYS shown (even 0); kept in n (no survivorship pruning). */}
          <span
            data-testid="group-abandonment"
            className="rounded border border-slate-700 bg-slate-800/60 px-2 py-0.5 text-slate-400"
          >
            {copyOf(copy, "abandonment_label", "Abandoned (kept in n)")}:{" "}
            <span className="font-mono text-slate-200">{group.abandonment}</span>
          </span>
        </div>
      </div>

      {group.insufficient_sample ? (
        // The explicit insufficient-sample marker WITH its n — never a bare percentage on a thin pool.
        <div
          data-testid="group-insufficient-sample"
          className="mt-3 rounded-md border border-amber-800/60 bg-amber-900/20 px-3 py-2 text-xs text-amber-200"
        >
          <span className="font-semibold uppercase tracking-wider">
            {copyOf(copy, "insufficient_sample_label", "Insufficient sample")}
          </span>{" "}
          <span className="font-mono">
            (n = {group.n} &lt; {minSample})
          </span>
          <p className="mt-1 text-amber-200/80">
            {copyOf(
              copy,
              "insufficient_sample_caption",
              "Below the minimum sample size — n is shown, but distributions are withheld rather than read as a measurement from too few theses.",
            )}
          </p>
        </div>
      ) : (
        <div className="mt-4 space-y-4">
          {/* --- confirmation-anchored excursion distribution (per horizon) ------------------- */}
          <div data-testid="group-confirmation-excursions">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              {copyOf(
                copy,
                "confirmation_excursions_title",
                "From first confirmation — per-horizon outcomes (R)",
              )}
            </p>
            <div className="space-y-1.5">
              {group.confirmation_excursions.horizons.map((row) => (
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

          {/* --- median time-to-confirm (honest omission when no confirmation) ---------------- */}
          <div
            data-testid="group-time-to-confirm"
            className="flex items-baseline gap-2 text-xs"
          >
            <span className="text-slate-400">
              {copyOf(copy, "time_to_confirm_label", "Median time to confirm")}:
            </span>
            {group.median_time_to_confirm === null ? (
              <span className="text-slate-500">
                {copyOf(
                  copy,
                  "time_to_confirm_absent",
                  "No confirmation recorded in this group.",
                )}
              </span>
            ) : (
              <span className="font-mono text-slate-200">
                {fmtSeconds(group.median_time_to_confirm)}{" "}
                {copyOf(copy, "time_to_confirm_unit", "s (logical)")}
              </span>
            )}
          </div>

          {/* --- mistake-tag frequencies (USER-confirmed reviews only) ------------------------ */}
          <div data-testid="group-tag-frequencies">
            <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
              {copyOf(copy, "tag_frequencies_title", "Mistake tags (your confirmed reviews)")}
            </p>
            {group.tag_frequencies.length === 0 ? (
              <p className="text-xs text-slate-500">
                {copyOf(
                  copy,
                  "tag_frequencies_absent",
                  "No confirmed review tags in this group yet.",
                )}
              </p>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {group.tag_frequencies.map((t) => (
                  <span
                    key={t.tag}
                    data-testid="tag-frequency"
                    data-tag={t.tag}
                    className="inline-flex items-center gap-1 rounded-full border border-slate-700 bg-slate-800/60 px-2 py-0.5 text-[11px] text-slate-300"
                  >
                    {labelFrom(taxonomy?.mistake_tags, t.tag)}
                    <span className="font-mono text-slate-400">×{t.count}</span>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* --- acted-trade block — VISUALLY SEPARATE from the confirmation-anchored block ---- */}
          <ActedTradeBlock group={group} copy={copy} />
        </div>
      )}
    </div>
  );
}

// One per-horizon ternary distribution row. The three resolved-outcome chips + a SEPARATE truncated
// chip (never folded in), with the median spread/R beside the row (the no-cost caveat as a number).
function HorizonRow({
  row,
  copy,
}: {
  row: AnalyticsHorizonRow;
  copy: AnalyticsTaxonomy | undefined;
}) {
  return (
    <div
      data-testid="horizon-row"
      data-horizon={row.horizon}
      className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-md border border-slate-800 bg-slate-900/50 px-3 py-1.5 text-xs"
    >
      <span className="w-12 font-mono text-slate-400">{row.horizon}s</span>
      <span
        data-testid="horizon-plus"
        className="inline-flex items-center gap-1 rounded border border-emerald-800/60 bg-emerald-900/20 px-1.5 py-0.5 text-emerald-300"
      >
        +1R <span className="font-mono">{row["+1R_first"]}</span>
      </span>
      <span
        data-testid="horizon-minus"
        className="inline-flex items-center gap-1 rounded border border-rose-800/60 bg-rose-900/20 px-1.5 py-0.5 text-rose-300"
      >
        −1R <span className="font-mono">{row["-1R_first"]}</span>
      </span>
      <span
        data-testid="horizon-neither"
        className="inline-flex items-center gap-1 rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-slate-400"
      >
        neither <span className="font-mono">{row.neither_within_horizon}</span>
      </span>
      <span
        data-testid="horizon-truncated"
        className="inline-flex items-center gap-1 rounded border border-amber-800/60 bg-amber-900/20 px-1.5 py-0.5 text-amber-300"
      >
        {copyOf(copy, "truncated_label", "Truncated")}{" "}
        <span className="font-mono">{row.truncated}</span>
      </span>
      {/* median spread / R — beside the +1R figure (the no-cost caveat as a number). */}
      <span
        data-testid="horizon-spread-per-r"
        className="ml-auto text-slate-500"
      >
        {copyOf(copy, "spread_per_r_caption", "median spread / R")}:{" "}
        <span className="font-mono text-slate-300">
          {fmtSpreadR(row.median_spread_per_r)}
        </span>
      </span>
    </div>
  );
}

// The acted-trade (entry+exit-marked) block — kept STRUCTURALLY apart from the confirmation-anchored
// figures (its own bordered card, its own n). Realized move in R only — never currency, never P&L.
function ActedTradeBlock({
  group,
  copy,
}: {
  group: AnalyticsGroup;
  copy: AnalyticsTaxonomy | undefined;
}) {
  const acted = group.acted_trade;
  return (
    <div
      data-testid="group-acted-trade"
      className="rounded-md border border-slate-700 bg-slate-800/30 p-3"
    >
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-300">
        {copyOf(copy, "acted_trade_title", "Acted trades — realized move (R)")}
      </p>
      <p className="mt-1 text-[11px] text-slate-500">
        {copyOf(
          copy,
          "acted_trade_caption",
          "Entry-and-exit-marked theses only, kept apart from the confirmation-anchored figures. Realized move in R units, never currency.",
        )}
      </p>
      {acted.n === 0 ? (
        <p data-testid="acted-trade-absent" className="mt-2 text-xs text-slate-500">
          {copyOf(
            copy,
            "acted_trade_absent",
            "No acted (entry-and-exit-marked) trades in this group.",
          )}
        </p>
      ) : (
        <div className="mt-2 flex flex-wrap items-center gap-4 text-xs">
          <span className="text-slate-400">
            {copyOf(copy, "n_label", "n")}{" "}
            <span className="font-mono text-slate-200">{acted.n}</span>
          </span>
          <span className="text-slate-400">
            {copyOf(copy, "median_realized_r_label", "Median realized R")}:{" "}
            <span className="font-mono text-slate-200">
              {fmtR(acted.median_realized_r)}
            </span>
          </span>
          <span className="text-slate-500">
            {copyOf(copy, "spread_per_r_caption", "median spread / R")}:{" "}
            <span className="font-mono text-slate-300">
              {fmtSpreadR(acted.median_spread_per_r)}
            </span>
          </span>
        </div>
      )}
    </div>
  );
}
