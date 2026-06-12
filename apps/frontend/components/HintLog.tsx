"use client";

import type { Hint, ResearchTaxonomy } from "@/lib/types";
import { formatDateDMY } from "@/lib/datetime";

// The hint log (J-65): the /journal "Hints" in-page view. Renders GET /research/hints rows VERBATIM —
// the frontend recomputes NOTHING (every hint's evidence + baseline citation are computed once on the
// backend; here they are read off the record). The only presentation transforms are the shared
// dd-MM-yyyy date formatter and taxonomy-owned column labels + empty-state copy.
//
// Columns: time (dd-MM-yyyy), ticker, pattern, evidence, baseline citation, declared-from. The
// declared-from cell shows the taxonomy-owned label once the user completed a declaration from the hint.

export function HintLog({
  rows,
  taxonomy,
}: {
  rows: Hint[];
  taxonomy: ResearchTaxonomy | null;
}) {
  const columns = taxonomy?.hints?.log_columns;
  const copy = taxonomy?.hints?.copy;
  const declaredFromLabel = copy?.declared_from_label ?? "Declared from this hint";

  if (rows.length === 0) {
    // Honest empty state — never a fabricated row. Copy is taxonomy-owned.
    return (
      <div
        data-testid="hint-log-empty"
        className="flex min-h-[30vh] flex-col items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40 text-center"
      >
        <div aria-hidden="true" className="mb-3 flex flex-col gap-1.5">
          <span className="block h-1 w-10 rounded-full bg-amber-800/70" />
          <span className="block h-1 w-7 rounded-full bg-slate-800" />
          <span className="block h-1 w-9 rounded-full bg-amber-800/70" />
        </div>
        <p className="text-sm font-medium text-slate-300">{copy?.log_title ?? "Hints"}</p>
        <p className="mt-1 max-w-sm text-xs text-slate-500">
          {copy?.log_empty ??
            "No hints logged yet — a setup-forming hint is recorded here each time a sustained pattern is described on a watched ticker."}
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900/40">
      <table data-testid="hint-log-table" className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-slate-800 text-left text-xs uppercase tracking-wider text-slate-500">
            <th className="px-3 py-2.5 font-semibold">{columns?.time ?? "Time"}</th>
            <th className="px-3 py-2.5 font-semibold">{columns?.ticker ?? "Ticker"}</th>
            <th className="px-3 py-2.5 font-semibold">{columns?.pattern ?? "Pattern"}</th>
            <th className="px-3 py-2.5 font-semibold">{columns?.evidence ?? "Evidence"}</th>
            <th className="px-3 py-2.5 font-semibold">{columns?.baseline ?? "Studied baseline"}</th>
            <th className="px-3 py-2.5 font-semibold">
              {columns?.declared_from ?? "Declared from"}
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.id}
              data-testid="hint-log-row"
              className="border-b border-slate-800/60 text-slate-300 last:border-0"
            >
              {/* wall_ts is unix SECONDS — the shared formatter takes ms. */}
              <td className="whitespace-nowrap px-3 py-2.5 font-mono text-xs text-slate-400">
                {formatDateDMY(row.wall_ts * 1000)}
              </td>
              <td className="whitespace-nowrap px-3 py-2.5 font-mono text-slate-200">
                {row.ticker}
              </td>
              <td className="whitespace-nowrap px-3 py-2.5">
                <span className="rounded-md border border-amber-700/60 bg-amber-900/20 px-2 py-0.5 text-xs text-amber-300">
                  {row.pattern_label}
                </span>
              </td>
              <td className="px-3 py-2.5 text-xs text-slate-300">{row.evidence}</td>
              <td className="px-3 py-2.5 font-mono text-xs text-amber-300/80">
                {row.baseline_citation}
              </td>
              <td className="whitespace-nowrap px-3 py-2.5 text-xs">
                {row.declared_from ? (
                  <span
                    data-testid="hint-log-declared-from"
                    className="rounded-md border border-emerald-700/60 bg-emerald-900/20 px-2 py-0.5 text-emerald-300"
                  >
                    {declaredFromLabel}
                  </span>
                ) : (
                  <span className="text-slate-600">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
