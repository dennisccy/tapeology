"use client";

import type { JournalFilters, ResearchTaxonomy } from "@/lib/types";

// The journal filter bar (J-51): ticker / setup / direction / resolution-status controls that drive
// a SERVER-side re-fetch (the frontend does NO client-side filtering/derivation — the server is the
// only filter authority). All option labels come from GET /research/taxonomy (the frontend hardcodes
// none of them). A blank/All option clears the filter.
//
// The single "Status / resolution" select merges the lifecycle statuses (active + the four terminal
// resolutions) so the user picks any lifecycle bucket from one control; "active" maps to the
// `status` param, the four terminal values map to the `resolution` param (both are server-side
// filters over the same persisted status column).

const SELECT_CLASS =
  "rounded border border-slate-700 bg-slate-950 px-2.5 py-1.5 font-mono text-xs text-slate-200 transition-colors focus:border-emerald-500 focus:outline-none";

const INPUT_CLASS =
  "rounded border border-slate-700 bg-slate-950 px-2.5 py-1.5 font-mono text-xs text-slate-200 placeholder-slate-600 transition-colors focus:border-emerald-500 focus:outline-none";

interface Props {
  filters: JournalFilters;
  taxonomy: ResearchTaxonomy | null;
  onChange: (next: JournalFilters) => void;
}

export function JournalFilterBar({ filters, taxonomy, onChange }: Props) {
  // The merged lifecycle value the single status/resolution select shows: the resolution if set,
  // else the status (active). Empty = All.
  const lifecycleValue = filters.resolution ?? filters.status ?? "";

  function setLifecycle(value: string) {
    if (value === "") {
      onChange({ ...filters, status: undefined, resolution: undefined });
    } else if (value === "active") {
      onChange({ ...filters, status: "active", resolution: undefined });
    } else {
      // A terminal value is a resolution filter (clears any status filter to avoid an AND that
      // matches nothing — a resolution already pins the terminal status).
      onChange({ ...filters, status: undefined, resolution: value });
    }
  }

  return (
    <div
      data-testid="journal-filters"
      className="mb-4 flex flex-wrap items-center gap-2"
    >
      <input
        data-testid="filter-ticker"
        type="text"
        placeholder="ticker"
        value={filters.ticker ?? ""}
        onChange={(e) =>
          onChange({ ...filters, ticker: e.target.value.toUpperCase() || undefined })
        }
        className={`${INPUT_CLASS} w-28`}
        aria-label="Filter by ticker"
      />

      <select
        data-testid="filter-setup"
        value={filters.setup_type ?? ""}
        onChange={(e) => onChange({ ...filters, setup_type: e.target.value || undefined })}
        className={SELECT_CLASS}
        aria-label="Filter by setup"
      >
        <option value="">All setups</option>
        {taxonomy?.setups.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </select>

      <select
        data-testid="filter-direction"
        value={filters.direction ?? ""}
        onChange={(e) => onChange({ ...filters, direction: e.target.value || undefined })}
        className={SELECT_CLASS}
        aria-label="Filter by direction"
      >
        <option value="">Long & short</option>
        {taxonomy?.directions.map((d) => (
          <option key={d.id} value={d.id}>
            {d.name}
          </option>
        ))}
      </select>

      <select
        data-testid="filter-status"
        value={lifecycleValue}
        onChange={(e) => setLifecycle(e.target.value)}
        className={SELECT_CLASS}
        aria-label="Filter by status or resolution"
      >
        <option value="">Any status</option>
        {/* Active + the four resolutions, all taxonomy-labelled (the frontend hardcodes no label). */}
        {(taxonomy?.statuses ?? []).map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </select>

      {/* Clear all — only shown when at least one filter is active, so the empty default has no
          dangling control. */}
      {(filters.ticker ||
        filters.setup_type ||
        filters.direction ||
        filters.status ||
        filters.resolution) && (
        <button
          type="button"
          data-testid="filter-clear"
          onClick={() => onChange({})}
          className="rounded border border-slate-700 px-2.5 py-1.5 text-xs text-slate-400 transition-colors hover:border-slate-500 hover:text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
        >
          Clear
        </button>
      )}
    </div>
  );
}
