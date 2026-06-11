"use client";

import type { JournalRow, ResearchTaxonomy } from "@/lib/types";
import { formatDateDMY } from "@/lib/datetime";

// The journal table (J-51): renders GET /research/journal rows VERBATIM. The frontend recomputes
// NOTHING — every value (status, resolution, reason, stamps) is a read of the backend row; the only
// presentation transforms are the shared dd-MM-yyyy date formatter and taxonomy-owned display labels.
//
// Columns (goal.md Journal IA): declared date (dd-MM-yyyy), ticker, bound source, data feed, setup,
// direction, status/resolution (expired rows show the verbatim interruption reason; terminal
// resolutions get the established terminal treatment).
//
// Rows are NOT yet links — /journal/[id] (review detail) ships with J-54/J-55. No dead link.

// Map a status/resolution id to its design-direction COLOR class (a visual concern owned by the
// frontend; the LABEL text always comes from the taxonomy). Per the design direction:
// invalidated/expired = terminal red; played_out/abandoned = resolved slate; active = live emerald.
function statusClass(status: string): string {
  switch (status) {
    case "active":
      return "border-emerald-700/60 bg-emerald-900/20 text-emerald-300";
    case "invalidated":
    case "expired":
      // Terminal treatment — a ringed rose chip so a terminal resolution reads as final.
      return "border-rose-700/70 bg-rose-900/30 text-rose-300 ring-1 ring-rose-800/50";
    case "played_out":
    case "abandoned":
    default:
      return "border-slate-600 bg-slate-800 text-slate-300";
  }
}

// The taxonomy-owned display label for a status / setup / direction id (the frontend hardcodes none
// of them). Falls back to a humanised id if the taxonomy is not loaded yet (it never blocks render).
function labelFrom(
  list: { id: string; name: string }[] | undefined,
  id: string,
): string {
  const found = list?.find((e) => e.id === id);
  if (found) return found.name;
  return id.replace(/_/g, " ");
}

interface Props {
  rows: JournalRow[];
  taxonomy: ResearchTaxonomy | null;
}

export function JournalTable({ rows, taxonomy }: Props) {
  if (rows.length === 0) {
    // Honest empty state — never a fabricated row.
    return (
      <div
        data-testid="journal-empty"
        className="flex min-h-[30vh] flex-col items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40 text-center"
      >
        <div className="mb-2 text-4xl text-slate-700" aria-hidden="true">
          ▤
        </div>
        <p className="text-sm font-medium text-slate-300">No theses journaled yet</p>
        <p className="mt-1 max-w-sm text-xs text-slate-500">
          Declare a thesis on a watched ticker in the cockpit — every thesis you declare, resolve,
          abandon, or that expires is recorded here and survives a restart.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900/40">
      <table data-testid="journal-table" className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-slate-800 text-left text-xs uppercase tracking-wider text-slate-500">
            <th className="px-3 py-2.5 font-semibold">Declared</th>
            <th className="px-3 py-2.5 font-semibold">Ticker</th>
            <th className="px-3 py-2.5 font-semibold">Bound source</th>
            <th className="px-3 py-2.5 font-semibold">Feed</th>
            <th className="px-3 py-2.5 font-semibold">Setup</th>
            <th className="px-3 py-2.5 font-semibold">Direction</th>
            <th className="px-3 py-2.5 font-semibold">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const directionColor =
              row.direction === "long" ? "text-emerald-400" : "text-rose-400";
            // The displayed lifecycle id: the resolution once terminal, else the status (active).
            const lifecycleId = row.resolution ?? row.status;
            return (
              <tr
                key={row.id}
                data-testid="journal-row"
                data-thesis-id={row.id}
                data-status={lifecycleId}
                className="border-b border-slate-800/60 last:border-b-0 hover:bg-slate-900/60"
              >
                {/* Declared date — dd-MM-yyyy via the ONE shared formatter. created_wall_ts is unix
                    seconds, so convert to ms for the Date. */}
                <td className="whitespace-nowrap px-3 py-2.5 font-mono text-xs text-slate-300">
                  {formatDateDMY(row.created_wall_ts * 1000)}
                </td>
                <td className="whitespace-nowrap px-3 py-2.5 font-mono text-slate-200">
                  {row.ticker}
                </td>
                <td className="px-3 py-2.5 font-mono text-xs text-slate-400">
                  {row.bound_source}
                </td>
                {/* The data-feed stamp (honesty stamp) — uppercased id, read verbatim. */}
                <td className="whitespace-nowrap px-3 py-2.5">
                  <span
                    data-testid="journal-feed"
                    className="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 font-mono text-[11px] uppercase text-slate-400"
                  >
                    {row.data_feed}
                  </span>
                </td>
                <td className="whitespace-nowrap px-3 py-2.5 text-slate-300">
                  {labelFrom(taxonomy?.setups, row.setup_type)}
                </td>
                <td
                  className={`whitespace-nowrap px-3 py-2.5 text-xs font-semibold uppercase ${directionColor}`}
                >
                  {labelFrom(taxonomy?.directions, row.direction)}
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex flex-col gap-1">
                    <span
                      data-testid="journal-status-chip"
                      data-lifecycle={lifecycleId}
                      className={`inline-flex w-fit rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${statusClass(
                        lifecycleId,
                      )}`}
                    >
                      {labelFrom(taxonomy?.statuses, lifecycleId)}
                    </span>
                    {/* The verbatim persisted expired/interruption/resolution reason (never
                        recomputed). Shown for any terminal row that carries one — most visibly the
                        expired rows' explicit interruption reason. */}
                    {row.resolution_reason && (
                      <span
                        data-testid="journal-resolution-reason"
                        className="max-w-md text-xs text-slate-500"
                      >
                        {row.resolution_reason}
                      </span>
                    )}
                    {/* Entry-mark presence — a real position is shown honestly (the journal never
                        infers a fill; this is the persisted mark fact). */}
                    {row.has_entry && (
                      <span
                        data-testid="journal-entry-mark"
                        className="w-fit rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[11px] uppercase tracking-wide text-slate-400"
                      >
                        entry marked
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
