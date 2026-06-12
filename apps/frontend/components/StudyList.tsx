"use client";

import type { ResearchTaxonomy, Study } from "@/lib/types";

// The study job list (J-60/J-61): every created study, most-recent-first, with its status / progress
// and a Cancel control while it is queued/running. Each row is read VERBATIM from the persisted
// payload. Selecting a row opens its results. Status COLORS stay within the existing semantics — slate
// for queued/cancelled, amber for running (and partial), rose for failed, a NEUTRAL slate for done so
// it never reads as an "edge win". All labels come from the taxonomy.

const STATUS_LABEL_FALLBACK: Record<string, string> = {
  queued: "Queued",
  running: "Running",
  done: "Done",
  cancelled: "Cancelled",
  failed: "Failed",
};

function statusClasses(status: string): string {
  switch (status) {
    case "running":
      return "border-amber-700/60 bg-amber-900/20 text-amber-300";
    case "failed":
      return "border-rose-700/60 bg-rose-900/20 text-rose-300";
    case "done":
      // Deliberately NEUTRAL slate — never green (a green "success" would read as an edge claim).
      return "border-slate-600 bg-slate-800 text-slate-200";
    case "cancelled":
    case "queued":
    default:
      return "border-slate-700 bg-slate-800/60 text-slate-400";
  }
}

export function StudyList({
  studies,
  loading,
  error,
  taxonomy,
  selectedId,
  onSelect,
  onCancel,
}: {
  studies: Study[];
  loading: boolean;
  error: string | null;
  taxonomy: ResearchTaxonomy | null;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCancel: (id: string) => void;
}) {
  const copy = taxonomy?.studies?.copy ?? {};
  const statusLabel = (id: string) =>
    taxonomy?.studies?.statuses?.find((s) => s.id === id)?.name ??
    STATUS_LABEL_FALLBACK[id] ??
    id;
  const setupLabel = (id: string) =>
    taxonomy?.setups?.find((s) => s.id === id)?.name ?? id.replace(/_/g, " ");

  return (
    <section
      data-testid="study-list"
      className="rounded-lg border border-slate-800 bg-slate-900/40"
    >
      <h2 className="border-b border-slate-800 px-4 py-3 text-sm font-semibold text-slate-200">
        {copy.jobs_title ?? "Studies"}
      </h2>

      {error && (
        <div
          data-testid="study-list-error"
          role="alert"
          className="m-3 rounded-md border border-rose-700/70 bg-rose-900/30 px-3 py-2 text-xs text-rose-200"
        >
          {error}
        </div>
      )}

      {loading && studies.length === 0 && !error ? (
        <div
          data-testid="study-list-loading"
          className="flex min-h-[12vh] items-center justify-center"
        >
          <div className="h-3 w-3 animate-pulse rounded-full bg-slate-600" />
          <span className="ml-2 text-sm text-slate-500">Loading studies…</span>
        </div>
      ) : studies.length === 0 ? (
        <p data-testid="study-list-empty" className="px-4 py-6 text-sm text-slate-500">
          {copy.jobs_empty ??
            "No studies yet — create one above to run your setup grammar over a chosen window."}
        </p>
      ) : (
        <ul className="divide-y divide-slate-800/70">
          {studies.map((study) => {
            const active = study.status === "queued" || study.status === "running";
            return (
              <li key={study.id}>
                <div
                  data-testid="study-row"
                  data-status={study.status}
                  data-study-id={study.id}
                  className={`flex items-center gap-3 px-4 py-3 ${
                    selectedId === study.id ? "bg-slate-800/40" : ""
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => onSelect(study.id)}
                    className="flex flex-1 flex-col items-start gap-1 text-left focus:outline-none"
                  >
                    <span className="flex items-center gap-2">
                      <span
                        data-testid="study-status"
                        className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${statusClasses(
                          study.status,
                        )}`}
                      >
                        {statusLabel(study.status)}
                      </span>
                      <span className="text-sm text-slate-200">
                        {setupLabel(study.setup_type)} · {study.direction}
                      </span>
                    </span>
                    <span className="flex items-center gap-2 text-[11px] text-slate-500">
                      <span className="font-mono">{study.source}</span>
                      <span className="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 font-mono uppercase text-slate-400">
                        {study.data_feed}
                      </span>
                      {study.hindsight_level && (
                        <span className="rounded border border-amber-800/60 bg-amber-900/20 px-1.5 py-0.5 text-amber-300">
                          {copy.hindsight_level_label ?? "Hindsight level"}
                        </span>
                      )}
                      {study.status === "running" && study.events_processed != null && (
                        <span className="font-mono text-amber-300">
                          {study.events_processed} {copy.progress_label ?? "events processed"}
                        </span>
                      )}
                    </span>
                  </button>

                  {active && (
                    <button
                      type="button"
                      data-testid="study-cancel-button"
                      onClick={() => onCancel(study.id)}
                      className="rounded-md border border-slate-700 bg-slate-800/60 px-2.5 py-1 text-xs text-slate-300 transition-colors hover:border-rose-700/60 hover:bg-rose-900/20 hover:text-rose-200 focus:outline-none focus-visible:ring-1 focus-visible:ring-rose-500 active:bg-slate-800"
                    >
                      {copy.cancel_button ?? "Cancel"}
                    </button>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
