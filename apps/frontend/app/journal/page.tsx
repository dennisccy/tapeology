"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchAnalytics, fetchJournal, fetchTaxonomy } from "@/lib/api";
import type {
  Analytics,
  JournalFilters,
  JournalRow,
  ResearchTaxonomy,
} from "@/lib/types";
import { JournalTable } from "@/components/JournalTable";
import { JournalFilterBar } from "@/components/JournalFilterBar";
import { AnalyticsView } from "@/components/AnalyticsView";

// The /journal page (J-51 + J-59): the research record. Two VIEWS within the one page (no new route,
// no new nav entry — the blueprint-registered home for J-59):
//   * "Theses" (the DEFAULT) — the filterable table of every thesis ever declared (J-51), read
//     VERBATIM from GET /research/journal. The default is unchanged so existing J-50/J-51 captures
//     are unaffected.
//   * "Analytics" (J-59) — the segregated aggregates from GET /research/analytics, rendered VERBATIM:
//     per (data_feed, config_fingerprint) partition, per setup × direction group, never pooled.
//
// The frontend does NO business logic: filters drive a SERVER-side re-fetch; the analytics payload is
// computed server-side and rendered verbatim (display rounding only). Loading / error / empty states
// are all handled. Dark instrument-panel style, consistent with the cockpit.

type JournalViewMode = "theses" | "analytics";

export default function JournalPage() {
  const [taxonomy, setTaxonomy] = useState<ResearchTaxonomy | null>(null);
  const [view, setView] = useState<JournalViewMode>("theses");

  // --- theses view state (J-51) ---
  const [rows, setRows] = useState<JournalRow[]>([]);
  const [filters, setFilters] = useState<JournalFilters>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // --- analytics view state (J-59) ---
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  // Load the taxonomy once (display labels — the frontend hardcodes none).
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

  // Re-fetch the theses list whenever a filter changes (server-side). A small debounce on the ticker
  // text avoids a request per keystroke while keeping every filter purely server-driven.
  useEffect(() => {
    const handle = setTimeout(() => {
      load(filters);
    }, 200);
    return () => clearTimeout(handle);
  }, [filters, load]);

  // Load the analytics payload when the analytics view is opened (and refresh on each re-open so a
  // newly-resolved thesis shows up). Read-only server-side aggregation — the page renders it verbatim.
  const loadAnalytics = useCallback(async () => {
    setAnalyticsLoading(true);
    setAnalyticsError(null);
    const result = await fetchAnalytics();
    if (result.ok && result.analytics) {
      setAnalytics(result.analytics);
    } else {
      setAnalyticsError(result.error ?? "The analytics could not be loaded.");
    }
    setAnalyticsLoading(false);
  }, []);

  useEffect(() => {
    if (view === "analytics") loadAnalytics();
  }, [view, loadAnalytics]);

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

        {/* The view toggle (J-59) — one control, the thesis table is the default. */}
        <div
          data-testid="journal-view-toggle"
          role="tablist"
          aria-label="Journal view"
          className="mb-4 inline-flex rounded-lg border border-slate-800 bg-slate-900/40 p-0.5"
        >
          <ViewTab
            label="Theses"
            active={view === "theses"}
            onClick={() => setView("theses")}
            testid="journal-view-theses"
          />
          <ViewTab
            label="Analytics"
            active={view === "analytics"}
            onClick={() => setView("analytics")}
            testid="journal-view-analytics"
          />
        </div>

        {view === "theses" ? (
          <>
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

            {/* Loading skeleton — shown only on the first load (a filter re-fetch keeps the prior
                rows visible to avoid a flash). */}
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
          </>
        ) : (
          <>
            {/* Analytics error — a styled alert (never a blank/fabricated view). */}
            {analyticsError && (
              <div
                data-testid="analytics-error"
                role="alert"
                className="mb-4 rounded-lg border border-rose-700/70 bg-rose-900/30 px-4 py-3 text-sm text-rose-200"
              >
                {analyticsError}
              </div>
            )}

            {analyticsLoading && analytics === null && !analyticsError ? (
              <div
                data-testid="analytics-loading"
                className="flex min-h-[30vh] items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40"
              >
                <div className="h-3 w-3 animate-pulse rounded-full bg-slate-600" />
                <span className="ml-2 text-sm text-slate-500">Loading the analytics…</span>
              </div>
            ) : analytics ? (
              <AnalyticsView analytics={analytics} taxonomy={taxonomy} />
            ) : null}
          </>
        )}
      </main>
    </div>
  );
}

// One view-toggle tab — hover / focus / active states per the design discipline.
function ViewTab({
  label,
  active,
  onClick,
  testid,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  testid: string;
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      data-testid={testid}
      data-active={active}
      onClick={onClick}
      className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 ${
        active
          ? "bg-slate-800 text-slate-100"
          : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 active:bg-slate-800"
      }`}
    >
      {label}
    </button>
  );
}
