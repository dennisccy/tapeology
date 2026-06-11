"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchJournal, fetchTaxonomy } from "@/lib/api";
import type { JournalFilters, JournalRow, ResearchTaxonomy } from "@/lib/types";
import { JournalTable } from "@/components/JournalTable";
import { JournalFilterBar } from "@/components/JournalFilterBar";

// The /journal page (J-51): the research record. A filterable table of every thesis ever declared —
// resolved, expired, abandoned, and active alike — read VERBATIM from the persisted store via
// GET /research/journal (the ONLY serving path). Survives a backend restart with history intact.
//
// The frontend does NO business logic: filters drive a SERVER-side re-fetch (no client-side
// filtering/derivation), and every value is rendered verbatim. Loading / error / empty states are
// all handled (not just the happy path). Dark instrument-panel style, consistent with the cockpit.

export default function JournalPage() {
  const [taxonomy, setTaxonomy] = useState<ResearchTaxonomy | null>(null);
  const [rows, setRows] = useState<JournalRow[]>([]);
  const [filters, setFilters] = useState<JournalFilters>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load the taxonomy once (display labels for setup/direction/status — the frontend hardcodes none).
  useEffect(() => {
    let alive = true;
    fetchTaxonomy().then((t) => {
      if (alive) setTaxonomy(t);
    });
    return () => {
      alive = false;
    };
  }, []);

  const load = useCallback(async (active: JournalFilters) => {
    setLoading(true);
    setError(null);
    const result = await fetchJournal(active);
    setRows(result.rows);
    if (!result.ok) setError(result.error ?? "The journal could not be loaded.");
    setLoading(false);
  }, []);

  // Re-fetch whenever a filter changes (server-side). A small debounce on the ticker text avoids a
  // request per keystroke while keeping every filter purely server-driven.
  useEffect(() => {
    const handle = setTimeout(() => {
      load(filters);
    }, 200);
    return () => clearTimeout(handle);
  }, [filters, load]);

  return (
    <div className="min-h-screen">
      <main className="mx-auto max-w-7xl px-4 py-6">
        <header className="mb-4">
          <h1 className="text-lg font-semibold text-slate-200">Journal</h1>
          <p className="mt-1 text-sm text-slate-500">
            Every thesis you declared — resolved, expired, abandoned, or active — recorded and
            restart-proof. Descriptive only — not trading advice.
          </p>
        </header>

        <JournalFilterBar filters={filters} taxonomy={taxonomy} onChange={setFilters} />

        {/* Error — a styled alert (never a blank/fabricated table). */}
        {error && (
          <div
            data-testid="journal-error"
            role="alert"
            className="mb-4 rounded-lg border border-rose-700/70 bg-rose-900/30 px-4 py-3 text-sm text-rose-200"
          >
            {error}
          </div>
        )}

        {/* Loading skeleton — shown only on the first load (a filter re-fetch keeps the prior rows
            visible to avoid a flash). */}
        {loading && rows.length === 0 && !error ? (
          <div
            data-testid="journal-loading"
            className="flex min-h-[30vh] items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40"
          >
            <div className="h-3 w-3 animate-pulse rounded-full bg-slate-600" />
            <span className="ml-2 text-sm text-slate-500">Loading the journal…</span>
          </div>
        ) : (
          <JournalTable rows={rows} taxonomy={taxonomy} />
        )}
      </main>
    </div>
  );
}
