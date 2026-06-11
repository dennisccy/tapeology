"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchJournalDetail, fetchTaxonomy } from "@/lib/api";
import type { JournalDetail, ResearchTaxonomy } from "@/lib/types";
import { JournalDetailView } from "@/components/JournalDetailView";

// The /journal/[id] review-detail page (J-54 / J-55): the per-thesis honest review surface under the
// Journal home. Rendered ENTIRELY from the single GET /research/journal/{id} response + taxonomy
// labels — the frontend recomputes NOTHING (every value is a verbatim read of the persisted record).
//
// What it shows (all from the one response): the frozen expected-behaviour statements with their
// final statuses, the append-only verdict timeline at TRUE clock time (each transition carrying its
// evidence verbatim, gap events explicit), the frozen entry risk-flag chips (absent => honest "not
// assessed"), the action marks (price + time + spread-at-mark, realized R only when both marks
// exist), the machine-derived execution checks with evidence, and the suggested mistake tags
// pre-selected + toggleable in a (not-yet-savable) picker. An unknown id renders an explicit honest
// error state (never a blank page).
//
// Copy register (J-66): descriptive, thesis-attributed; "Descriptive only — not trading advice"
// extends here verbatim. No imperative or predictive wording. Dark instrument-panel style.

export default function JournalDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  // Next 15 passes route params as a Promise to client pages — unwrap with `use`.
  const { id } = use(params);

  const [taxonomy, setTaxonomy] = useState<ResearchTaxonomy | null>(null);
  const [detail, setDetail] = useState<JournalDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let alive = true;
    fetchTaxonomy().then((t) => {
      if (alive) setTaxonomy(t);
    });
    return () => {
      alive = false;
    };
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setNotFound(false);
    const result = await fetchJournalDetail(id);
    if (result.ok && result.detail) {
      setDetail(result.detail);
    } else {
      setDetail(null);
      setNotFound(!!result.notFound);
      setError(result.error ?? "The thesis could not be loaded.");
    }
    setLoading(false);
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="min-h-screen">
      <main className="mx-auto max-w-5xl px-4 py-6">
        <header className="mb-4">
          <Link
            href="/journal"
            data-testid="back-to-journal"
            className="inline-flex items-center gap-1 rounded px-1 text-sm text-slate-400 transition-colors hover:text-emerald-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <span aria-hidden="true">←</span> Back to journal
          </Link>
          <h1 className="mt-2 text-lg font-semibold text-slate-200">Review</h1>
          <p className="mt-1 text-sm text-slate-500">
            What you expected, what the tape did, what you did, and what the execution checks found.
            Descriptive only — not trading advice.
          </p>
        </header>

        {/* Loading skeleton. */}
        {loading && (
          <div
            data-testid="detail-loading"
            className="flex min-h-[30vh] items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40"
          >
            <div className="h-3 w-3 animate-pulse rounded-full bg-slate-600" />
            <span className="ml-2 text-sm text-slate-500">Loading the review…</span>
          </div>
        )}

        {/* Unknown id / error — an explicit honest error state, never a blank page. */}
        {!loading && (notFound || (error && !detail)) && (
          <div
            data-testid="detail-error"
            role="alert"
            className="rounded-lg border border-rose-700/70 bg-rose-900/30 px-4 py-6 text-center"
          >
            <p className="text-sm font-medium text-rose-200">
              {notFound ? "This thesis was not found." : error}
            </p>
            <p className="mt-1 text-xs text-rose-300/80">
              It may have been removed, or the id is wrong.
            </p>
            <Link
              href="/journal"
              className="mt-3 inline-block rounded border border-slate-600 px-3 py-1.5 text-sm text-slate-300 transition-colors hover:bg-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              Return to the journal
            </Link>
          </div>
        )}

        {!loading && detail && (
          <JournalDetailView detail={detail} taxonomy={taxonomy} onSaved={load} />
        )}
      </main>
    </div>
  );
}
