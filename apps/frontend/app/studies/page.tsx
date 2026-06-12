"use client";

import { useCallback, useEffect, useState } from "react";
import {
  cancelStudy,
  createStudy,
  fetchStudies,
  fetchStudy,
  fetchTaxonomy,
} from "@/lib/api";
import type { CreateStudyParams, ResearchTaxonomy, Study } from "@/lib/types";
import { StudyCreateForm } from "@/components/StudyCreateForm";
import { StudyList } from "@/components/StudyList";
import { StudyResultsView } from "@/components/StudyResultsView";

// The /studies page (J-60/J-61/J-62): create, monitor, cancel, re-run, and read deterministic replay
// studies of the setup grammar over a chosen window — occurrence outcomes side-by-side with a seeded
// random-arm-time null baseline. The page does NO business logic: it POSTs the create form, polls the
// running job's status, and renders the runner's persisted results VERBATIM (display rounding only).
//
// All copy/labels come from the taxonomy (the frontend hardcodes none); a pre-J-60 taxonomy falls back
// to a minimal local register so the page never blocks render. Dark instrument-panel style, consistent
// with /journal: slate surfaces, restrained borders, mono numerics. Loading / empty / error states are
// all handled. Status colors stay within the existing semantics — slate (queued/cancelled), amber
// (running/partial/truncated), rose (failed) — NEVER a green "success" that reads as an edge.

export default function StudiesPage() {
  const [taxonomy, setTaxonomy] = useState<ResearchTaxonomy | null>(null);
  const [studies, setStudies] = useState<Study[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

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

  const loadStudies = useCallback(async () => {
    const result = await fetchStudies();
    setStudies(result.studies);
    setListError(result.ok ? null : result.error ?? "The studies could not be loaded.");
    setLoading(false);
  }, []);

  // Initial load.
  useEffect(() => {
    loadStudies();
  }, [loadStudies]);

  // Poll while any study is running/queued (status/progress flips queued → running → done). Stops
  // polling once everything is terminal so the page is quiet when idle.
  useEffect(() => {
    const anyActive = studies.some((s) => s.status === "queued" || s.status === "running");
    if (!anyActive) return;
    const handle = setInterval(loadStudies, 700);
    return () => clearInterval(handle);
  }, [studies, loadStudies]);

  const onCreate = useCallback(
    async (params: CreateStudyParams) => {
      setCreating(true);
      setCreateError(null);
      const result = await createStudy(params);
      setCreating(false);
      if (result.ok && result.study) {
        setSelectedId(result.study.id);
        await loadStudies();
      } else {
        setCreateError(result.error ?? "The study could not be created.");
      }
    },
    [loadStudies],
  );

  const onCancel = useCallback(
    async (studyId: string) => {
      await cancelStudy(studyId);
      await loadStudies();
    },
    [loadStudies],
  );

  // The selected study for the results view (re-read fresh so the latest persisted result shows).
  const [selected, setSelected] = useState<Study | null>(null);
  useEffect(() => {
    if (!selectedId) {
      setSelected(null);
      return;
    }
    // Prefer the freshest copy from the list (it polls); fall back to a direct fetch.
    const fromList = studies.find((s) => s.id === selectedId);
    if (fromList) {
      setSelected(fromList);
    } else {
      fetchStudy(selectedId).then((s) => setSelected(s));
    }
  }, [selectedId, studies]);

  const copy = taxonomy?.studies?.copy ?? {};

  return (
    <div className="min-h-screen">
      <main className="mx-auto max-w-7xl px-4 py-6">
        <header className="mb-4">
          <h1 data-testid="studies-title" className="text-lg font-semibold text-slate-200">
            {copy.title ?? "Replay studies"}
          </h1>
          <p className="mt-1 max-w-3xl text-sm text-slate-500">
            {copy.intro ??
              "Run your setup grammar over a chosen past window and read the occurrence outcomes side-by-side with a seeded random-arm-time baseline."}
          </p>
          <p data-testid="studies-framing" className="mt-2 max-w-3xl text-xs text-slate-600">
            {copy.measurement_framing ??
              "These are journaled measurements of a replay over recorded data — not a profitability claim, an edge, a win rate, or a forecast. Descriptive only — not trading advice."}
          </p>
        </header>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,360px)_minmax(0,1fr)]">
          {/* Create form + job list (left column on wide). */}
          <div className="space-y-6">
            <StudyCreateForm
              taxonomy={taxonomy}
              onCreate={onCreate}
              creating={creating}
              error={createError}
            />
            <StudyList
              studies={studies}
              loading={loading}
              error={listError}
              taxonomy={taxonomy}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onCancel={onCancel}
            />
          </div>

          {/* Results view (right column on wide). */}
          <div>
            {selected ? (
              <StudyResultsView
                study={selected}
                taxonomy={taxonomy}
                onRerun={onCreate}
              />
            ) : (
              <div
                data-testid="studies-no-selection"
                className="flex min-h-[40vh] flex-col items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-10 text-center"
              >
                <span className="text-2xl text-slate-700">∅</span>
                <p className="mt-2 text-sm text-slate-500">
                  Create a study, or select one from the list, to read its results.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
