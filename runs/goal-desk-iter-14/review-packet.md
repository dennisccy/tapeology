# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 13. Shown in full: 12.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/frontend/app/desk/page.tsx` (148 lines not shown)

```diff
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index dd834da..d65bbe3 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -21,22 +21,32 @@ routes (``POST``/``GET /research/desk/screen/compute``, ``POST
 (mirroring the plan's stated preference) rather than folding into ``routes.py``, which is already
 large; mounted separately in ``app/main.py``.
 
-J-09 (this iteration) adds ONE new read: ``GET /research/desk/topup/runs`` (the durable, append-only
-top-up run log — ``desk_topup_log.py``'s lightweight run-meta list + the latest full record; honest-
-empty ``{"runs": [], "latest": null}`` before any run, never a 404). No new compute manager, no new
-POST — the log is written by the ALREADY-existing top-up trigger/CLI paths (``desk_topup_compute.py``
-threads the write through internally); this route is a pure read, mirroring ``GET
-/research/desk/universe``'s single-synchronous-read shape exactly.
-
-**Both compute managers are module-level singletons here, NOT ``ResearchRegistry`` properties.**
+J-09 (unmodified this iteration) adds ONE new read: ``GET /research/desk/topup/runs`` (the durable,
+append-only top-up run log — ``desk_topup_log.py``'s lightweight run-meta list + the latest full
+record; honest-empty ``{"runs": [], "latest": null}`` before any run, never a 404). No new compute
+manager, no new POST — the log is written by the ALREADY-existing top-up trigger/CLI paths
+(``desk_topup_compute.py`` threads the write through internally); this route is a pure read,
+mirroring ``GET /research/desk/universe``'s single-synchronous-read shape exactly.
+
+J-10 (this iteration, goal-desk-iter-14) adds the coverage-index reconciliation: a trigger/poll/
+cancel trio (``POST``/``GET /research/desk/coverage/reconcile/compute``,
+``POST /research/desk/coverage/reconcile/compute/cancel`` — mirrors the top-up trio exactly) plus
+ONE durable read (``GET /research/desk/coverage/reconcile/runs`` — mirrors ``GET
+/research/desk/topup/runs``'s exact honest-empty/meta-only-list/full-latest shape). All four routes
+are pure wiring over ``desk_index_reconcile.py`` — see that module's own docstring for the
+classify/repair/record mechanics. No new MCP tool (``get_endpoint``'s existing ``/research/``
+allowlist already reaches the new GET path); no new router, no ``main.py`` change.
+
+**Compute managers are module-level singletons here, NOT ``ResearchRegistry`` properties.**
 ``DeskTopupComputeManager`` (``desk_topup_compute.py``) reuses ``routes.record_bar_series``
 in-process, so it must import FROM ``routes.py`` — if ``ResearchRegistry`` held the manager (the
 ``EdgeReportComputeManager`` precedent), ``routes.py`` would need to import IT back, a circular
-import. ``DeskScreenComputeManager`` (``desk_screen_compute.py``) has no such constraint (it needs
-nothing from ``routes.py``), but is placed here anyway for consistency with its sibling — there is
-no functional reason to prefer the registry either. Both are FastAPI dependencies instead (the
-``get_universe_fetcher`` seam), test-overridable via ``app.dependency_overrides`` exactly like
-every other store/seam in this module."""
+import. ``DeskScreenComputeManager`` (``desk_screen_compute.py``) and
+``DeskIndexReconcileComputeManager`` (``desk_index_reconcile.py``, J-10) have no such constraint
+(neither needs anything from ``routes.py``), but are placed here anyway for consistency with their
+sibling — there is no functional reason to prefer the registry either. All three are FastAPI
+dependencies instead (the ``get_universe_fetcher`` seam), test-overridable via
+``app.dependency_overrides`` exactly like every other store/seam in this module."""
 
 from __future__ import annotations
 
@@ -50,6 +60,11 @@ from .bar_index import BarIndex
 from .bars import BarStore
 from .datasets import DatasetStore
 from .desk_coverage import get_desk_coverage
+from .desk_index_reconcile import (
+    DeskIndexReconcileComputeManager,
+    ReconcileRunStore,
+    resolve_desk_index_reconcile_dir,
+)
 from .desk_screen import ScreenStore, resolve_desk_screen_dir
 from .desk_screen_compute import DeskScreenComputeManager
 from .desk_topup_compute import DeskTopupComputeManager
@@ -77,6 +92,10 @@ _desk_topup_manager = DeskTopupComputeManager()
 # shape as ``_desk_topup_manager`` immediately above.
 _desk_screen_compute_manager = DeskScreenComputeManager()
 
+# The desk coverage-index reconciliation compute manager (J-10) — the SAME process-wide-singleton-
+# behind-a-dependency shape as its two siblings above.
+_desk_index_reconcile_manager = DeskIndexReconcileComputeManager()
+
 
 def get_universe_store() -> UniverseStore:
     """The universe store rooted at the config-owned directory (``TAPEOLOGY_DESK_UNIVERSE_DIR``
@@ -396,3 +415,95 @@ def cancel_desk_screen_compute(
         raise HTTPException(status_code=409, detail="no desk screen compute is currently running")
     manager.cancel()
     return {"cancelling": True}
+
+
+# --- Coverage-index reconciliation (J-10, goal-desk-iter-14) — a trigger/poll/cancel trio mirroring
+# the top-up compute trio exactly, plus ONE durable read mirroring ``GET /research/desk/topup/runs``.
+# See ``desk_index_reconcile.py`` for the classify/repair/record mechanics this only wires up. -------
+
+
+def get_reconcile_run_store() -> ReconcileRunStore:
+    """The reconciliation run log store rooted at a bare env-var-or-sibling-of-the-universe-dir
+    default (zero new ``Config`` field — see ``desk_index_reconcile.resolve_desk_index_reconcile_dir``)
+    — the ``get_topup_run_store`` pattern. A FastAPI dependency so tests can point it at a temp dir
+    via the env var or override it outright."""
+    return ReconcileRunStore(resolve_desk_index_reconcile_dir(CONFIG.desk_universe_dir_resolved()))
+
+
+def get_desk_reconcile_manager() -> DeskIndexReconcileComputeManager:
+    """The desk coverage-index reconciliation compute manager — a FastAPI dependency (the
+    ``get_desk_topup_manager`` pattern) so a test overrides it outright via
+    ``app.dependency_overrides`` for complete test-to-test isolation. The default resolves the
+    process-wide singleton constructed at module import time."""
+    return _desk_index_reconcile_manager
+
+
+@router.post("/coverage/reconcile/compute")
+def trigger_desk_index_reconcile_compute(
+    bar_store: BarStore = Depends(get_bar_store),
+    bar_index: BarIndex = Depends(get_bar_index),
+    manager: DeskIndexReconcileComputeManager = Depends(get_desk_reconcile_manager),
+    reconcile_run_store: ReconcileRunStore = Depends(get_reconcile_run_store),
+) -> dict:
+    """Start the single-flight coverage-index reconciliation job, or — if one is already running —
+    return it UNCHANGED (``started: False``, never a second concurrent job). Returns
+    ``{"started": bool, "compute": <snapshot>}``; the actual classify-repair-verify walk runs on a
+    background worker thread, off this request, so this route returns immediately. The job's
+    terminal outcome is durably recorded into ``reconcile_run_store`` once it resolves (inside
+    ``DeskIndexReconcileComputeManager.trigger`` itself) — this route only threads the store
+    dependency through. Needs no ``UniverseStore``/``ResearchRegistry`` — reconciliation never
+    touches universe membership or the bar-fetch path."""
+    return manager.trigger(bar_store, bar_index, reconcile_run_store)
+
+
+@router.get("/coverage/reconcile/compute")
+def get_desk_index_reconcile_compute(
+    manager: DeskIndexReconcileComputeManager = Depends(get_desk_reconcile_manager),
+) -> dict | None:
+    """The reconciliation job's current/last snapshot, served VERBATIM — or ``null`` if no
+    reconciliation has ever run this process. A plain read: never triggers a compute as a side
+    effect (GET-never-computes)."""
+    return manager.snapshot()
+
+
+@router.post("/coverage/reconcile/compute/cancel")
+def cancel_desk_index_reconcile_compute(
+    manager: DeskIndexReconcileComputeManager = Depends(get_desk_reconcile_manager),
+) -> dict:
+    """Cancel the in-flight reconciliation (cooperative — observed once, before the repair phase
+    starts). ``409`` when idle (no job has ever run, or the last job already reached a terminal
+    state) — mirrors ``cancel_desk_topup_compute``'s own 409-when-terminal shape."""
+    snapshot = manager.snapshot()
+    if snapshot is None or snapshot["state"] != "running":
+        raise HTTPException(
+            status_code=409, detail="no desk index reconciliation compute is currently running"
+        )
+    manager.cancel()
+    return {"cancelling": True}
+
+
+def _reconcile_run_meta_only(record: dict) -> dict:
+    """The lightweight projection ``GET /research/desk/coverage/reconcile/runs``'s bulk list serves
+    — every field EXCEPT ``drift_before``/``drift_after``/``store_errors`` (mirrors
+    ``_topup_run_meta_only``'s identical convention: a run record carrying full before/after drift
+    detail is materially larger than its own summary, so the list call never returns the full detail
+    for every historical run)."""
+    heavy_keys = ("drift_before", "drift_after", "store_errors")
+    return {key: value for key, value in record.items() if key not in heavy_keys}
+
+
+@router.get("/coverage/reconcile/runs")
+def get_desk_index_reconcile_runs(store: ReconcileRunStore = Depends(get_reconcile_run_store)) -> dict:
+    """``{"runs": [...meta-only...], "latest": <full record>|null}`` — an explicit HTTP 200
+    honest-empty payload (``{"runs": [], "latest": null}``) before any reconciliation has ever
+    reached its terminal state, never a 404 (the ``GET /research/desk/topup/runs`` convention).
+    ``latest`` is the most recently STARTED run, verbatim from disk — never recomputed on the GET. A
+    corrupted run-record file is excluded from ``runs``/``latest`` (never fabricated, never crashes
+    this route) — ``ReconcileRunStore.list()``'s own ``errors`` return already surfaces it
+    explicitly at the store layer (mirrors ``get_topup_runs``'s identical choice not to duplicate
+    that channel into this response body)."""
+    records, _errors = store.list()
+    return {
+        "runs": [_reconcile_run_meta_only(r) for r in records],
+        "latest": records[-1] if records else None,
+    }
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 93a493b..270edba 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -3,17 +3,26 @@
 import Link from "next/link";
 import { useEffect, useState } from "react";
 import {
+  cancelDeskReconcileCompute,
   cancelDeskScreenCompute,
   cancelDeskTopupCompute,
+  fetchDeskReconcileCompute,
+  fetchDeskReconcileRuns,
   fetchDeskScreen,
   fetchDeskScreenByDate,
   fetchDeskScreenCompute,
   fetchDeskTopupCompute,
   fetchDeskTopupRuns,
+  triggerDeskReconcileCompute,
   triggerDeskScreenCompute,
   triggerDeskTopupCompute,
 } from "@/lib/api";
 import type {
+  DeskReconcileComputeSnapshot,
+  DeskReconcileDrift,
+  DeskReconcileRun,
+  DeskReconcileRunMeta,
+  DeskReconcileRunsListResult,
   DeskScreenComputeSnapshot,
   DeskScreenListResult,
   DeskScreenMeta,
@@ -72,6 +81,16 @@ import { fmt } from "@/lib/format";
 // a screen exists. This is a deliberate placement choice logged in
 // `runs/goal-session-desk/state/assumptions.md` (iter-11 entry), not the plan's own literal
 // "immediately after Screen History" suggestion (which that same plan text marks as non-binding).
+//
+// era-desk-iter-14 (J-10): a THIRD compute manager + a THIRD durable, append-only history section —
+// "Index Reconciliation" — repairing the derived `bar_index` against the frozen `BarStore` through
+// the existing `BarIndex.reindex()`. A 5th/6th mount-time GET (`/research/desk/coverage/
+// reconcile/compute` + `/research/desk/coverage/reconcile/runs`); `ReconcileIndexControl` sits
+// beside `ScreenComputeControl`/`TopupComputeControl` in the shared trigger panel (same UX pattern,
+// same live-progress-with-cancel shape); the read-only "Index Reconciliation" section is rendered
+// unconditionally, immediately after "Top-up runs" — the SAME "independent of screen state"
+// placement precedent iter-11 established, since reconciliation touches only the bar store/index,
+// never a screen. Page-load GETs still trigger nothing (T-4/5C, unchanged).
 
 const NUMERIC_CELL = "px-2 py-1.5 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
 const HEADER_CELL = "px-2 py-1 text-right text-[11px] font-medium text-slate-500";
@@ -659,6 +678,185 @@ function TopupRunsSection({
   );
 }
 
+// --- Index reconciliation history (era-desk-iter-14, J-10) — a durable, append-only record of
+// every coverage-index reconciliation, read verbatim from `GET /research/desk/coverage/
+// reconcile/runs` and nothing recomputed. Mirrors the Top-up Runs split exactly:
+// `IndexReconciliationTable` renders every recorded run's summary (date + id, state, series on
+// disk, rows indexed before → after — the ONLY fields the meta-only `runs` list carries), and
+// `LatestReconciliationDetail` renders the full before/after drift detail + store errors for the
+// latest run ONLY — the one entry the backend's `latest` field actually carries them for.
+// Read-only, no click-through, no new control beyond the trigger/cancel button (which lives in the
+// shared "Run Screen / Top-up / Reconcile Index" panel below, not here). --------------------------
+
+function driftEntryCount(drift: DeskReconcileDrift): number {
+  return drift.unindexed_series.length + drift.orphan_index_rows.length + drift.stale_checksum_rows.length;
+}
+
+// Every affected pair/row across the three honest buckets, rendered as one flat, labeled list — the
+// bucket a row came from is stated inline (never merged into a single unlabeled count) since the
+// three buckets mean genuinely different things (a series never indexed vs. an index row with
+// nothing on disk vs. an index row whose file the store can no longer verify).
+function DriftList({ drift, testid }: { drift: DeskReconcileDrift; testid: string }) {
+  const total = driftEntryCount(drift);
+  if (total === 0) {
+    return (
+      <p data-testid={`${testid}-empty`} className="text-xs text-slate-500">
+        no drift
+      </p>
+    );
+  }
+  return (
+    <ul data-testid={testid} className="space-y-0.5">
+      {drift.unindexed_series.map((entry) => (
+        <li key={`unindexed-${entry.series_id}`} data-testid={`${testid}-entry`} className="text-xs text-slate-400">
+          <span className="font-mono text-slate-300">
+            {entry.symbol} {entry.timeframe}
+          </span>{" "}
+          — series on disk, no index row ({entry.series_id})
+        </li>
+      ))}
+      {drift.orphan_index_rows.map((entry) => (
+        <li key={`orphan-${entry.series_id}`} data-testid={`${testid}-entry`} className="text-xs text-slate-400">
+          <span className="font-mono text-slate-300">{entry.series_id}</span> — index row, no file on disk
+        </li>
+      ))}
+      {drift.stale_checksum_rows.map((entry) => (
+        <li key={`stale-${entry.series_id}`} data-testid={`${testid}-entry`} className="text-xs text-slate-400">
+          <span className="font-mono text-slate-300">{entry.series_id}</span> — index row, file on disk
+          fails its checksum
+        </li>
+      ))}
+    </ul>
+  );
+}
+
+function IndexReconciliationRunRow({ meta }: { meta: DeskReconcileRunMeta }) {
+  return (
+    <tr data-testid="desk-reconcile-run-row" className="border-b border-slate-800/60 last:border-b-0">
+      <td className={LABEL_CELL}>{meta.started_utc.slice(0, 10)}</td>
+      <td className={LABEL_CELL} data-testid="desk-reconcile-run-id">
+        {meta.id}
+      </td>
+      <td className={LABEL_CELL} data-testid="desk-reconcile-run-state">
+        {meta.state}
+      </td>
+      <td className={NUMERIC_CELL} data-testid="desk-reconcile-run-series-on-disk">
+        {meta.series_on_disk}
+      </td>
+      <td className={NUMERIC_CELL} data-testid="desk-reconcile-run-rows-indexed">
+        {meta.rows_indexed_before} {"→"} {meta.rows_indexed_after}
+      </td>
+    </tr>
+  );
+}
+
+function IndexReconciliationTable({ runs }: { runs: DeskReconcileRunMeta[] }) {
+  if (runs.length === 0) {
+    return <EmptyState testid="desk-reconcile-runs-empty" title="No reconciliation run recorded yet." />;
+  }
+  return (
+    <div className="overflow-x-auto">
+      <table data-testid="desk-reconcile-runs-table" className="w-full border-collapse">
+        <thead>
+          <tr className="border-b border-slate-800">
+            <th className={HEADER_CELL_LEFT}>date</th>
+            <th className={HEADER_CELL_LEFT}>run</th>
+            <th className={HEADER_CELL_LEFT}>state</th>
+            <th className={HEADER_CELL}>series on disk</th>
+            <th className={HEADER_CELL}>rows indexed (before {"→"} after)</th>
+          </tr>
+        </thead>
+        <tbody>
+          {runs.map((meta) => (
+            <IndexReconciliationRunRow key={meta.id} meta={meta} />
+          ))}
+        </tbody>
+      </table>
+    </div>
+  );
+}
+
+// The latest run's own full detail — series on disk, rows indexed before/after, the affected pairs
+// in BOTH the before and after drift (after is expected empty for every pair this run repaired —
+// rendered as "no drift" when it genuinely is, never hidden), and any store errors (corrupt files)
+// verbatim and legible (never truncated).
+function LatestReconciliationDetail({ run }: { run: DeskReconcileRun }) {
+  return (
+    <div
+      data-testid="desk-reconcile-run-latest-detail"
+      className="mt-4 space-y-3 border-t border-slate-800 pt-4"
+    >
+      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
+        Latest run — {run.started_utc.slice(0, 10)} · {run.id}
+      </h3>
+      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
+        <span data-testid="desk-reconcile-run-latest-state">state: {run.state}</span>
+        <span data-testid="desk-reconcile-run-latest-series-on-disk">{run.series_on_disk} series on disk</span>
+        <span data-testid="desk-reconcile-run-latest-rows-indexed">
+          rows indexed: {run.rows_indexed_before} before, {run.rows_indexed_after} after
+        </span>
+      </div>
+      <div>
+        <h4 className="mb-1 text-[11px] font-medium text-slate-500">
+          Drift before ({driftEntryCount(run.drift_before)})
+        </h4>
+        <DriftList drift={run.drift_before} testid="desk-reconcile-run-latest-drift-before" />
+      </div>
+      <div>
+        <h4 className="mb-1 text-[11px] font-medium text-slate-500">
+          Drift after ({driftEntryCount(run.drift_after)})
+        </h4>
+        <DriftList drift={run.drift_after} testid="desk-reconcile-run-latest-drift-after" />
+      </div>
+      {run.store_errors.length > 0 && (
+        <div data-testid="desk-reconcile-run-latest-store-errors">
+          <h4 className="mb-1 text-[11px] font-medium text-slate-500">
+            Store errors ({run.store_errors.length})
+          </h4>
+          <ul className="space-y-1">
+            {run.store_errors.map((error, index) => (
+              <li
+                key={`${error.file}-${index}`}
+                data-testid="desk-reconcile-run-latest-store-error-row"
+                className="text-xs text-slate-400"
+              >
+                <span className="font-mono text-slate-300">{error.file}</span> —{" "}
+                <span data-testid="desk-reconcile-run-latest-store-error-detail">{error.error}</span>
+              </li>
+            ))}
+          </ul>
+        </div>
+      )}
+    </div>
+  );
+}
+
+// The section's own Loading/Unavailable/Populated states — mirrors `TopupRunsSection`'s identical
+// three-state shape, fed by its own mount-time GET.
+function ReconciliationSection({
+  result,
+}: {
+  result: { ok: boolean; data: DeskReconcileRunsListResult | null; error?: string } | null;
+}) {
+  if (result === null) {
+    return <LoadingPanel testid="desk-reconcile-runs-loading" />;
+  }
+  if (!result.ok || result.data === null) {
+    return (
+      <UnavailablePanel
+        testid="desk-reconcile-runs-unavailable"
+        message={result.error ?? "The index reconciliation history could not be loaded."}
+      />
+    );
+  }
+  return (
+    <div>
+      <IndexReconciliationTable runs={result.data.runs} />
+      {result.data.latest !== null && <LatestReconciliationDetail run={result.data.latest} />}
+    </div>
+  );
+}
+
 // --- Provenance line — universe snapshot id + date, as_of, config_fingerprint, and the pinned
 // bar-store signature. --------------------------------------------------------------------------
 //
@@ -870,6 +1068,86 @@ function TopupComputeControl({
   );
 }
 
+// era-desk-iter-14 (J-10): a third compute control, wired exactly like `TopupComputeControl` — the
+// operation has no per-pair counters (it is a single classify-repair-verify walk, not a walk over
+// many pairs), so the running indicator shows the compute's own `progress.phase` label instead of
+// an "N / M" count.
+function ReconcileIndexControl({
+  compute,
+  onTrigger,
+  triggering,
+  triggerError,
+  onCancel,
+  cancelRequested,
+  cancelError,
+}: {
+  compute: DeskReconcileComputeSnapshot | null;
+  onTrigger: () => void;
+  triggering: boolean;
+  triggerError: string | null;
+  onCancel: () => void;
+  cancelRequested: boolean;
+  cancelError: string | null;
+}) {
+  const isRunning = compute?.state === "running";
+  const isFailed = compute?.state === "failed";
+  const isCancelled = compute?.state === "cancelled";
+  const buttonLabel = isRunning ? "Reconciling…" : isFailed ? "Retry Reconcile Index" : "Reconcile Index";
+  return (
+    <div className="flex flex-col items-center gap-1">
+      {isFailed && compute?.error && (
+        <p data-testid="desk-reconcile-compute-error" className="text-xs text-red-300">
+          {compute.error}
+        </p>
+      )}
+      {triggerError && (
+        <p data-testid="desk-reconcile-compute-trigger-error" className="text-xs text-red-300">
+          {triggerError}
+        </p>
+      )}
+      {isCancelled && (
+        <p data-testid="desk-reconcile-compute-cancelled" className="text-xs text-amber-200/70">
+          Index reconciliation cancelled — the index was not repaired this run.
+        </p>
+      )}
+      <button
+        type="button"
+        data-testid="desk-reconcile-button"
+        onClick={onTrigger}
+        disabled={triggering || isRunning}
+        className={PRIMARY_BUTTON_CLASS}
+      >
+        {buttonLabel}
+      </button>
+      {isRunning && (
+        <div data-testid="desk-reconcile-compute-running" className="mt-1 flex flex-col items-center gap-1">
+          <p data-testid="desk-reconcile-compute-progress" className="text-xs text-amber-200/70">
+            <span
+              aria-hidden="true"
+              className="mr-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400 align-middle"
+            />
+            {compute.progress.phase}
+          </p>
+          <button
+            type="button"
+            data-testid="desk-reconcile-compute-cancel"
+            onClick={onCancel}
+            disabled={cancelRequested}
+            className={CANCEL_BUTTON_CLASS}
+          >
+            {cancelRequested ? "Cancelling…" : "Cancel"}
+          </button>
+          {cancelError && (
+            <p data-testid="desk-reconcile-compute-cancel-error" className="text-xs text-red-300">
+              {cancelError}
+            </p>
+          )}
+        </div>
+      )}
+    </div>
+  );
+}
+
 interface ScreenControlProps {
   compute: DeskScreenComputeSnapshot | null;
   onTrigger: () => void;
@@ -890,6 +1168,16 @@ interface TopupControlProps {
   cancelError: string | null;
 }
 
+interface ReconcileControlProps {
+  compute: DeskReconcileComputeSnapshot | null;
+  onTrigger: () => void;
+  triggering: boolean;
+  triggerError: string | null;
+  onCancel: () => void;
+  cancelRequested: boolean;
+  cancelError: string | null;
+}
+
 // The honest empty state (TC-1): rendered iff `latest === null` — no screen has EVER been
 // computed. Doubles as the controls panel for a first-ever run (both Run Screen and Top-up live
 // here since there is nothing else to show yet); once a screen exists, the SAME two controls move
@@ -897,9 +1185,11 @@ interface TopupControlProps {
 function DeskNotComputedPanel({
   screen,
   topup,
+  reconcile,
 }: {
   screen: ScreenControlProps;
   topup: TopupControlProps;
+  reconcile: ReconcileControlProps;
 }) {
   return (
     <div
@@ -913,6 +1203,7 @@ function DeskNotComputedPanel({
       <div className="mt-3 flex flex-col items-center gap-6 sm:flex-row sm:items-start sm:justify-center sm:gap-12">
         <ScreenComputeControl {...screen} />
         <TopupComputeControl {...topup} />
+        <ReconcileIndexControl {...reconcile} />
       </div>
     </div>
   );
@@ -932,6 +1223,7 @@ function DeskPopulatedScreen({
   selectedHistoryDate,
   screenControlProps,
   topupControlProps,
+  reconcileControlProps,
 }: {
   snapshot: DeskScreenSnapshot;
   screens: DeskScreenMeta[];
@@ -942,6 +1234,7 @@ function DeskPopulatedScreen({
   selectedHistoryDate: string | null;
   screenControlProps: ScreenControlProps;
   topupControlProps: TopupControlProps;
+  reconcileControlProps: ReconcileControlProps;
 }) {
   return (
     <div className="space-y-6">
@@ -1003,11 +1296,12 @@ function DeskPopulatedScreen({
         </Panel>
       </section>
 
-      <section aria-label="Run Screen and Top-up controls">
-        <Panel title="Run Screen / Top-up">
+      <section aria-label="Run Screen, Top-up and Reconcile Index controls">
+        <Panel title="Run Screen / Top-up / Reconcile Index">
           <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start sm:justify-center sm:gap-12">
             <ScreenComputeControl {...screenControlProps} />
             <TopupComputeControl {...topupControlProps} />
+            <ReconcileIndexControl {...reconcileControlProps} />
           </div>
         </Panel>
       </section>
@@ -1045,6 +1339,19 @@ export default function DeskPage() {
     error?: string;
   } | null>(null);
 
+  // era-desk-iter-14 (J-10): the coverage-index reconciliation compute + its durable run log —
+  // mirrors the topup* hooks immediately above exactly, one pair per compute manager.
+  const [reconcileCompute, setReconcileCompute] = useState<DeskReconcileComputeSnapshot | null>(null);
+  const [reconcileTriggering, setReconcileTriggering] = useState(false);
+  const [reconcileTriggerError, setReconcileTriggerError] = useState<string | null>(null);
+  const [reconcileCancelRequested, setReconcileCancelRequested] = useState(false);
+  const [reconcileCancelError, setReconcileCancelError] = useState<string | null>(null);
... [diff_bound] apps/frontend/app/desk/page.tsx: 148 more diff lines omitted — Read the file for full detail
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 2cecdca..29d5599 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -6,6 +6,8 @@ import type {
   BarSeriesRecord,
   CreateBacktestParams,
   DatasetsListResult,
+  DeskReconcileComputeSnapshot,
+  DeskReconcileRunsListResult,
   DeskScreenComputeSnapshot,
   DeskScreenListResult,
   DeskScreenSnapshot,
@@ -1138,3 +1140,96 @@ export async function fetchDeskTopupRuns(): Promise<{
     return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// era-desk-iter-14 (J-10): the coverage-index reconciliation trigger/poll/cancel trio, mirroring
+// `triggerDeskTopupCompute`/`fetchDeskTopupCompute`/`cancelDeskTopupCompute` byte-for-byte. No
+// request body (the backend needs nothing from the client to classify/repair the index).
+export async function triggerDeskReconcileCompute(): Promise<{
+  ok: boolean;
+  data?: { started: boolean; compute: DeskReconcileComputeSnapshot };
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/coverage/reconcile/compute`, { method: "POST" });
+    if (res.ok) {
+      const data = await res.json();
+      return { ok: true, data };
+    }
+    let error = "The index reconciliation could not be started.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, error };
+  } catch {
+    return { ok: false, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// GET /research/desk/coverage/reconcile/compute — the reconciliation job's current/last snapshot,
+// served VERBATIM, or `null` if none has ever run this process. Mirrors `fetchDeskTopupCompute`.
+export async function fetchDeskReconcileCompute(): Promise<{
+  ok: boolean;
+  data: DeskReconcileComputeSnapshot | null;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/coverage/reconcile/compute`);
+    if (!res.ok) return { ok: false, data: null };
+    const data = await res.json();
+    return { ok: true, data: (data as DeskReconcileComputeSnapshot | null) ?? null };
+  } catch {
+    return { ok: false, data: null };
+  }
+}
+
+// POST /research/desk/coverage/reconcile/compute/cancel — cancel the in-flight reconciliation job.
+// Mirrors `cancelDeskTopupCompute`; the backend's 409 (idle) `detail` is surfaced VERBATIM.
+export async function cancelDeskReconcileCompute(): Promise<{ ok: boolean; error?: string }> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/coverage/reconcile/compute/cancel`, {
+      method: "POST",
+    });
+    if (res.ok) return { ok: true };
+    let error = "The index reconciliation could not be cancelled.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, error };
+  } catch {
+    return { ok: false, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// era-desk-iter-14 (J-10): GET /research/desk/coverage/reconcile/runs — the durable, append-only
+// reconciliation run log's meta-only list + the latest full record, served VERBATIM. Mirrors
+// `fetchDeskTopupRuns`'s exact `{ok, data, error}` shape byte-for-byte. An honest-empty
+// (`{runs: [], latest: null}`) result is a valid `ok:true` outcome — the caller renders it as
+// "No reconciliation run recorded yet.", never a failure; `data: null` is reserved for a genuine
+// non-200 / unreachable backend.
+export async function fetchDeskReconcileRuns(): Promise<{
+  ok: boolean;
+  data: DeskReconcileRunsListResult | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/coverage/reconcile/runs`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskReconcileRunsListResult };
+    }
+    let error = "The index reconciliation run history could not be loaded.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, data: null, error };
+  } catch {
+    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
+  }
+}
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 2f808ab..f5b3763 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -948,3 +948,83 @@ export interface DeskTopupRunsListResult {
   runs: DeskTopupRunMeta[];
   latest: DeskTopupRun | null;
 }
+
+// era-desk-iter-14 (J-10) -- the coverage-index reconciliation: drift classification between the
+// frozen bar-series files and the derived `bar_index`, repaired through the existing
+// `BarIndex.reindex()` (never a second index-building path). Mirrors `app/research/
+// desk_index_reconcile.py`'s served shapes byte-for-byte. Three honest drift buckets: a healthy
+// series with no index row (attributed by symbol+timeframe), an index row whose series_id is on
+// disk nowhere (orphan, series_id alone), an index row whose series_id points at a corrupted file
+// (stale checksum, series_id alone) -- the two `series_id`-only shapes are structurally identical
+// but kept as distinct named types (never a shared alias) so a future field added to only one
+// bucket cannot silently leak onto the other.
+export interface DeskReconcileUnindexedSeries {
+  series_id: string;
+  symbol: string;
+  timeframe: string;
+}
+
+export interface DeskReconcileOrphanRow {
+  series_id: string;
+}
+
+export interface DeskReconcileStaleChecksumRow {
+  series_id: string;
+}
+
+export interface DeskReconcileDrift {
+  unindexed_series: DeskReconcileUnindexedSeries[];
+  orphan_index_rows: DeskReconcileOrphanRow[];
+  stale_checksum_rows: DeskReconcileStaleChecksumRow[];
+}
+
+export interface DeskReconcileStoreError {
+  file: string;
+  error: string;
+}
+
+export interface DeskReconcileRunMeta {
+  id: string;
+  config_fingerprint: string;
+  started_utc: string;
+  finished_utc: string;
+  state: "done" | "cancelled" | "failed";
+  series_on_disk: number;
+  rows_indexed_before: number;
+  rows_indexed_after: number;
+}
+
+// The full persisted record -- `DeskReconcileRunMeta` plus the before/after drift detail and any
+// store errors (corrupt files, surfaced verbatim). Only `latest` (below) ever carries this full
+// shape; the bulk `runs` list is meta-only (mirrors `DeskTopupRun`/`DeskTopupRunMeta`'s identical
+// split).
+export interface DeskReconcileRun extends DeskReconcileRunMeta {
+  drift_before: DeskReconcileDrift;
+  drift_after: DeskReconcileDrift;
+  store_errors: DeskReconcileStoreError[];
+}
+
+// `GET /research/desk/coverage/reconcile/runs` -- honest-empty-or-populated, HTTP 200 always,
+// never 404. `latest === null` iff no reconciliation has EVER reached a terminal state -- the
+// page's ONE discriminator for the "No reconciliation run recorded yet." empty state.
+export interface DeskReconcileRunsListResult {
+  runs: DeskReconcileRunMeta[];
+  latest: DeskReconcileRun | null;
+}
+
+// The reconciliation compute manager's job snapshot, served VERBATIM by GET/POST
+// `/research/desk/coverage/reconcile/compute`. Mirrors `DeskTopupComputeSnapshot`'s shape;
+// `progress` here carries only a `phase` label -- reconciliation is a single classify-repair-verify
+// walk, not a per-pair loop, so there is no pairs_total/pairs_done counter to report.
+export interface DeskReconcileComputeProgress {
+  phase: "classifying" | "reindexing" | "verifying";
+}
+
+export interface DeskReconcileComputeSnapshot {
+  id: string;
+  state: "running" | "done" | "cancelled" | "failed";
+  started_utc: string | null;
+  finished_utc: string | null;
+  error: string | null;
+  progress: DeskReconcileComputeProgress;
+}
diff --git a/docs/goal.md b/docs/goal.md
index b1c5879..36fc5e3 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -627,6 +627,92 @@ order: J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding con
     series the era-5 contract resamples from that same `1h` fetch, so whether a pair was attempted,
     refused, or never reached is unknowable today.)*
 
+- **J-10: The coverage the briefing shows is the coverage the frozen store can prove**
+  - Steps:
+    1. Classify the drift between the derived `bar_index` and the frozen `BarStore` using ONLY reads
+       that already exist — `BarStore.list(include_bars=False)`'s healthy records plus its own
+       `errors`, and `BarIndex.list()`'s indexed `series_id`s (`bar_index.py:178`) — into three
+       honest classes: a series on disk with no index row (attributed to its `symbol` × `timeframe`
+       from that record's own meta), an index row whose `series_id` is not on disk (reported by
+       `series_id` alone — never an invented meta), and a row indexed under a checksum the store no
+       longer reports. **Zero diff to `bar_index.py` and `bars.py`**: the drift is pure composition
+       of their existing public reads, no new accessor, no schema change, no new index.
+    2. Repair through the EXISTING `BarIndex.reindex(store)` (`bar_index.py:198`) and nothing else —
+       never a second index-building path — then re-run the identical comparison and record the
+       post-repair result together with `BarStore.list()`'s own `errors` **verbatim**, because
+       `reindex()` is DROP-and-repopulate over HEALTHY records only: a corrupt file that the rebuilt
+       index therefore cannot carry is disclosed on the record, never silently dropped.
+    3. Keep it an explicit operator act and never a page-load compute (T-4 and the 5C lesson):
+       trigger via `POST` through the established compute-manager pattern (`DeskTopupComputeManager`,
+       `desk_topup_compute.py` — single-flight, pollable progress, cancellable), and persist ONE
+       frozen, checksummed, append-only run record per run — run id, started/finished UTC, terminal
+       state (`done`/`cancelled`/`failed`), `config_fingerprint`, pre-repair drift counts + the
+       affected `symbol × timeframe` pairs, post-repair verification counts, and the store errors —
+       written EXACTLY ONCE at the run's terminal state by a SINGLE shared writer every caller uses
+       (the `desk_topup_log` J-09 discipline); a run whose process dies before that write records
+       NOTHING and the ledger never invents an entry for it.
+    4. Own it exactly once: a new desk module (name at build discretion, e.g.
+       `app/research/desk_index_reconcile.py`) as the ONLY owner and ONE serving endpoint (exact path
+       at build discretion, e.g. `GET /research/desk/coverage/reconcile/runs`) with an honest-empty
+       `{"runs": [], "latest": null}` HTTP 200 before any run — registered as a NEW row in the
+       blueprint's Data Contract BEFORE the code lands; storage dir a bare env-var-or-sibling default
+       (the `desk_screen`/`desk_topup_log` precedent — deliberately NOT a new `Config` field); NO MCP
+       tool added (J-06's exactly-17-tool contract stays green and `get_endpoint`'s `/research/`
+       allowlist already reaches the path). Coverage and freshness keep their single existing owner —
+       `desk_coverage.get_desk_coverage` over `bar_index` — and no second coverage path, cache, or
+       copy is created anywhere.
+    5. Surface it on `/desk`: a "Reconcile Index" trigger wired exactly like the existing Top-up
+       button (live progress + cancel, page-load GETs trigger nothing) and a read-only reconciliation
+       section beside Screen History and Top-up Runs showing the latest run's counts (series on disk,
+       rows indexed, drift before, drift after, affected pairs, store errors) with an honest
+       no-run-recorded empty state; copy = descriptive measurement only (no advice, imperative,
+       urgency, or prediction language).
+    6. Test fixture-scoped: a scoped store holding a series its scoped index has no row for →
+       `GET /research/desk/coverage` reports `has_bars: false` for that pair BEFORE the run and
+       `true` AFTER it, with the run record's pre/post counts matching that drift exactly; a planted
+       corrupt file is recorded verbatim as a store error and simply absent from the rebuilt index
+       (never fabricated); a second run appends a new record while every earlier record file stays
+       byte-identical; the GET is honest-empty before any run and triggers nothing.
+  - Acceptance: on the fixture-scoped rig, a pair whose series the frozen store holds but the derived
+    index has no row for reports `has_bars: false` from `GET /research/desk/coverage` before the run
+    and `true` after exactly one reconciliation run, and the recorded run states the same drift it
+    repaired (pre-repair count and affected pairs, post-repair verification, store errors verbatim)
+    (**single source of truth**: the run record is registered in the Data Contract with the new desk
+    module as its only owner and its one GET as its only serving endpoint; the index is rebuilt ONLY
+    through the existing `BarIndex.reindex()`; coverage and freshness still come solely from
+    `desk_coverage` over `bar_index`; and `bar_index.py`, `bars.py`, `tradability.py` and `levels.py`
+    take a ZERO diff — this SSOT criterion stands in place of a PnL-ledger append, which this era's
+    Non-Goals forbid); every `.data/bars/*.json` series file in the scoped root is proven
+    byte-identical before and after the run (SHA-256 listing) and every previously recorded universe,
+    screen and top-up record is proven byte-identical on disk (checksums unchanged, nothing
+    backfilled) — a reconciliation changes only the derived index, so the NEXT screen run is a NEW
+    append-only snapshot under a NEW `bar_store_signature` (`desk_screen.py`'s checksum over
+    `desk_coverage`'s reads), never a rewrite of an existing one; in a real browser after the T-9
+    clean rebuild, `/desk` shows the honest no-run-recorded state in one screenshot and, after a
+    fixture-scoped run, the reconciliation section with its drift counts plus a ranked row whose
+    coverage badge was dark before and is lit on a NEW screen run after — both legible (T-10: no
+    screenshot ⇒ `unknown`, never `passing`); a **`[NEW]`-flagged demo-narrator walkthrough** covers
+    the reconciliation end to end; and the full backend suite is green with
+    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the `default`
+    profile and `v1` byte-identical (engine equivalence green), the MCP surface still exactly 17
+    tools, zero diff to `StructureChart.tsx`, and `tests/test_copy_discipline.py` green unmodified.
+    *(Keyless core; browser-verifiable. Reconciling the AMBIENT index is an operator-run act, reported
+    honestly as run-or-not-run — never a CI gate. Why: measured 2026-07-28 directly from the frozen
+    store and the derived index — `apps/backend/.data/bars` holds 369 series files while
+    `.data/bar_index.db` holds 281 rows, so 88 recorded series carry no index row (and zero index rows
+    point at a series that is not on disk); intersected with the pinned universe
+    `universe-2026-07-25-49b33fa31680` and `desk_coverage.DESK_TOPUP_TIMEFRAMES` (`1h`,`4h`,`1d`,`1w`),
+    exactly 7 member × timeframe pairs are affected: META `1h`+`1d`, MSFT `4h`, NFLX `1h`+`1d`, NVDA
+    `1h`+`1d`. On `screen-2026-07-27-936543601e75` (63 ranked / 38 skipped) that renders as NFLX ranked
+    #5, META #48 and NVDA #57 with all four badges dark — covered by the page's own divergence note,
+    which fires only when EVERY badge in a row is dark (`app/desk/page.tsx:193/308`) — and MSFT #53 with
+    `4h` dark beside `1h`/`1d` lit and NO note at all: the store holds MSFT `4h` (that dark badge is
+    false) and holds no MSFT `1w` (that one is true), and nothing on the page distinguishes them.
+    `BarIndex.reindex()` is referenced only by `tests/test_bar_index.py` — zero call sites in `app/`
+    or `scripts/` — so no operator can reach the repair; and because `bar_store_signature` is a
+    checksum over `desk_coverage`'s index-backed reads, a series the index cannot see also cannot move
+    the pin the append-only screen ledger keys on.)*
+
 <!-- /AUTO:journeys -->
 
 ## Anti-goals
@@ -711,7 +797,9 @@ audits; only ever grow more specific, never weaker):**
   beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings
   (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and memory/task
   bounds), every heavy path respects them: headless engine runs self-wrap under the mask, and
-  interactive pump sessions are launched via `scripts/automation/host-guard-exec.sh claude`
-  (the engine pauses `AWAITING_HOST_GUARD`, resumable, on an unconfined pump). Never disable,
+  interactive pump sessions are auto-confined in place by the engine (`host-guard-adopt.sh`;
+  `scripts/automation/host-guard-exec.sh claude` is the optional from-birth wrapper) — the
+  engine pauses `AWAITING_HOST_GUARD` (resumable) only when confinement cannot be established.
+  Never disable,
   widen, or bypass these caps to make a run faster or a pause go away; widening the mask follows
   the verification ladder in `trendora/project-extensions/host-guard/README.md`. *(critical)*
diff --git a/incredible_auto_dev/.claude/commands/goal.md b/incredible_auto_dev/.claude/commands/goal.md
index 0c6f066..5d2834e 100644
--- a/incredible_auto_dev/.claude/commands/goal.md
+++ b/incredible_auto_dev/.claude/commands/goal.md
@@ -1,7 +1,7 @@
 ---
 description: Run Goal Mode until the goal is achieved or an existing rule halts/pauses it, inside this Claude Code session (interactive dispatch — bills to your interactive plan allowance).
 argument-hint: "[session-id] [extra run-goal.sh flags]"
-allowed-tools: Bash(./scripts/automation/run-goal.sh:*), Bash(scripts/automation/goal-await-dispatch.sh:*), Bash(jq:*), Bash(cat:*), Bash(ls:*), Bash(taskset:*), Read, Task, Write
+allowed-tools: Bash(./scripts/automation/run-goal.sh:*), Bash(scripts/automation/goal-await-dispatch.sh:*), Bash(scripts/automation/host-guard-adopt.sh:*), Bash(jq:*), Bash(cat:*), Bash(ls:*), Bash(taskset:*), Read, Task, Write
 ---
 You are the **pump** for goal mode. Run the EXISTING goal-mode engine until the
 goal is achieved, blocked, halted, or paused by its existing rules. Do NOT add
@@ -12,14 +12,15 @@ First read `.claude/skills/goal-interactive-dispatch.md` and follow it exactly.
 1. **Session id:** parse `$ARGUMENTS`. The first token is the session id; if there
    is no first token, generate one like `interactive-<YYYY-MM-DD>-<short>` and
    tell the user what you chose. Any remaining tokens are passthrough flags.
-2. **Host-guard check** (only when `project-extensions/host-guard/host-guard.env`
-   exists with `HOST_GUARD_ENABLED=1` and `HOST_GUARD_REQUIRE_PUMP_CONFINED=1`):
-   compare `taskset -cp $$` against `HOST_GUARD_CPU_LIST`. If this session's
-   affinity is wider than the mask, STOP and tell the user to relaunch Claude
-   Code via `scripts/automation/host-guard-exec.sh claude` — subagents and their
-   Bash children inherit THIS session's cpuset, confinement can only be applied
-   at launch, and the engine's iteration gate pauses (AWAITING_HOST_GUARD) on an
-   unconfined pump, so starting now would waste a session.
+2. **Host-guard confinement** (only when `project-extensions/host-guard/host-guard.env`
+   exists with `HOST_GUARD_ENABLED=1`): run
+   `scripts/automation/host-guard-adopt.sh --cli-root-of $$` — it confines THIS
+   already-running CLI session (and everything it will spawn) to the declared
+   caps, in place; instant and idempotent when already confined. No special
+   launch command is required. Only if it prints `FAILED`, tell the user to
+   relaunch via `scripts/automation/host-guard-exec.sh claude` (the from-birth
+   wrapper) — the engine's iteration gate re-verifies each iteration and would
+   pause (AWAITING_HOST_GUARD, resumable) on an unconfinable pump.
 3. **Launch the engine** in the background (Bash with run_in_background) and
    capture its PID:
    `./scripts/automation/run-goal.sh --session-id <sid> --interactive <passthrough flags>`
diff --git a/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md b/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md
index 5a38352..1e25ebb 100644
--- a/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md
+++ b/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md
@@ -151,19 +151,25 @@ concurrent requests never collide.
 The engine's own self-wrap (run-goal.sh) confines only the HEADLESS engine tree.
 Interactive dispatches — every subagent, and every `pytest`/build/browser those
 subagents run through Bash — execute as descendants of THIS foreground CLI
-session, so they inherit whatever CPU/memory confinement this session was
-launched with, and nothing can retrofit it afterwards. When the project declares
-host caps (`project-extensions/host-guard/host-guard.env`), the session must be
-launched through the wrapper:
-
-    scripts/automation/host-guard-exec.sh claude
-
-With `HOST_GUARD_REQUIRE_PUMP_CONFINED=1`, the engine verifies the pump's cpuset
-(via the `pid=` line in `.pump-alive`) at each iteration boundary and pauses the
-session (`AWAITING_HOST_GUARD`, resumable) if the pump is wider than
-`HOST_GUARD_CPU_LIST`. If that pause fires, relaunch the CLI via the wrapper and
-`/goal-resume` — do not disable the flag to make the pause go away; the caps
-exist because unconfined goal-mode load has hard-reset the host.
+session and inherit ITS confinement. When the project declares host caps
+(`project-extensions/host-guard/host-guard.env`), that confinement is applied
+automatically — no special launch command is required:
+
+- the `/goal` command runs `scripts/automation/host-guard-adopt.sh
+  --cli-root-of $$` at session start, which confines the RUNNING CLI process
+  tree in place (scope adoption for memory/task/quota ceilings + a hard
+  `taskset` CPU mask on the tree, inherited by all future children);
+- with `HOST_GUARD_REQUIRE_PUMP_CONFINED=1`, the engine re-verifies the pump at
+  every iteration boundary (via the `pid=` line in `.pump-alive` or the CLI
+  root it captured at launch) and auto-confines it again if needed, pausing
+  (`AWAITING_HOST_GUARD`, resumable) only when in-place confinement fails.
+
+Optional belt-and-braces: launching the CLI through
+`scripts/automation/host-guard-exec.sh claude` confines it from birth and also
+sets the BLAS/OMP thread-cap env vars (those cannot be injected into a running
+process). If the pause ever fires, relaunch via that wrapper and `/goal-resume`
+— do not disable the flag to make the pause go away; the caps exist because
+unconfined goal-mode load has hard-reset the host.
 
 ## Usage sidecar (token telemetry — protocol v2, optional, best-effort)
 
diff --git a/incredible_auto_dev/commands/goal.md b/incredible_auto_dev/commands/goal.md
index 0c6f066..5d2834e 100644
--- a/incredible_auto_dev/commands/goal.md
+++ b/incredible_auto_dev/commands/goal.md
@@ -1,7 +1,7 @@
 ---
 description: Run Goal Mode until the goal is achieved or an existing rule halts/pauses it, inside this Claude Code session (interactive dispatch — bills to your interactive plan allowance).
 argument-hint: "[session-id] [extra run-goal.sh flags]"
-allowed-tools: Bash(./scripts/automation/run-goal.sh:*), Bash(scripts/automation/goal-await-dispatch.sh:*), Bash(jq:*), Bash(cat:*), Bash(ls:*), Bash(taskset:*), Read, Task, Write
+allowed-tools: Bash(./scripts/automation/run-goal.sh:*), Bash(scripts/automation/goal-await-dispatch.sh:*), Bash(scripts/automation/host-guard-adopt.sh:*), Bash(jq:*), Bash(cat:*), Bash(ls:*), Bash(taskset:*), Read, Task, Write
 ---
 You are the **pump** for goal mode. Run the EXISTING goal-mode engine until the
 goal is achieved, blocked, halted, or paused by its existing rules. Do NOT add
@@ -12,14 +12,15 @@ First read `.claude/skills/goal-interactive-dispatch.md` and follow it exactly.
 1. **Session id:** parse `$ARGUMENTS`. The first token is the session id; if there
    is no first token, generate one like `interactive-<YYYY-MM-DD>-<short>` and
    tell the user what you chose. Any remaining tokens are passthrough flags.
-2. **Host-guard check** (only when `project-extensions/host-guard/host-guard.env`
-   exists with `HOST_GUARD_ENABLED=1` and `HOST_GUARD_REQUIRE_PUMP_CONFINED=1`):
-   compare `taskset -cp $$` against `HOST_GUARD_CPU_LIST`. If this session's
-   affinity is wider than the mask, STOP and tell the user to relaunch Claude
-   Code via `scripts/automation/host-guard-exec.sh claude` — subagents and their
-   Bash children inherit THIS session's cpuset, confinement can only be applied
-   at launch, and the engine's iteration gate pauses (AWAITING_HOST_GUARD) on an
-   unconfined pump, so starting now would waste a session.
+2. **Host-guard confinement** (only when `project-extensions/host-guard/host-guard.env`
+   exists with `HOST_GUARD_ENABLED=1`): run
+   `scripts/automation/host-guard-adopt.sh --cli-root-of $$` — it confines THIS
+   already-running CLI session (and everything it will spawn) to the declared
+   caps, in place; instant and idempotent when already confined. No special
+   launch command is required. Only if it prints `FAILED`, tell the user to
+   relaunch via `scripts/automation/host-guard-exec.sh claude` (the from-birth
+   wrapper) — the engine's iteration gate re-verifies each iteration and would
+   pause (AWAITING_HOST_GUARD, resumable) on an unconfinable pump.
 3. **Launch the engine** in the background (Bash with run_in_background) and
    capture its PID:
    `./scripts/automation/run-goal.sh --session-id <sid> --interactive <passthrough flags>`
diff --git a/incredible_auto_dev/docs/goal-mode-quickstart.md b/incredible_auto_dev/docs/goal-mode-quickstart.md
index f95bf60..3c9f0b2 100644
--- a/incredible_auto_dev/docs/goal-mode-quickstart.md
+++ b/incredible_auto_dev/docs/goal-mode-quickstart.md
@@ -109,7 +109,7 @@ Halt verdicts:
 - `AWAITING_BLUEPRINT_APPROVAL` — only when you ran with `--require-blueprint-approval`: paused after baseline (or after a structural blueprint change) for you to review `state/blueprint.md`; `--resume` to continue (counts as approval)
 - `AWAITING_INTENT_REVIEW` — only when you ran with `--intent-checkpoint` / `--intent-checkpoint-at N`: paused once mid-session for you to read `runs/goal-session-<sid>/intent-review.md` ("is this still the product you wanted?"); `--resume` to continue (counts as acknowledgment; fires once per session)
 - `AWAITING_GITHUB_AUTH` — paused at startup because per-iter push is on but a push to `origin` wouldn't authenticate (expired GitHub session, or no remote); fix auth (the run will offer to launch `gh auth login` for you when interactive) and `--resume`
-- `AWAITING_HOST_GUARD` — only on hosts that declare hardware caps (`project-extensions/host-guard/host-guard.env`): the hwmon forensics sampler could not be started, the engine's CPU-affinity wrap did not take effect, a declared launcher lost its HOST-GUARD cap block, or the interactive pump session is not confined to the declared CPU mask (relaunch the CLI via `scripts/automation/host-guard-exec.sh <cli>`); fix the printed reason and `--resume` — see `docs/host-guard.md`
+- `AWAITING_HOST_GUARD` — only on hosts that declare hardware caps (`project-extensions/host-guard/host-guard.env`): the hwmon forensics sampler could not be started, the engine's CPU-affinity wrap did not take effect, a declared launcher lost its HOST-GUARD cap block, or the interactive pump session could not be confined (the engine auto-confines a running pump in place first via `host-guard-adopt.sh`; relaunching through `scripts/automation/host-guard-exec.sh <cli>` is only needed if that fails); fix the printed reason and `--resume` — see `docs/host-guard.md`
 
 ## Common workflows
 
diff --git a/incredible_auto_dev/docs/host-guard.md b/incredible_auto_dev/docs/host-guard.md
index 47736fa..cd4d634 100644
--- a/incredible_auto_dev/docs/host-guard.md
+++ b/incredible_auto_dev/docs/host-guard.md
@@ -22,7 +22,9 @@ disables everything.
 | `HOST_GUARD_CPUQUOTA` | systemd scope average-CPU backstop | `"800%"` |
 | `HOST_GUARD_MEMORY_HIGH` | scope memory ceiling (reclaim/throttle, no OOM-kill) | `"14G"` |
 | `HOST_GUARD_TASKS_MAX` | fork-storm bound | `2048` |
-| `HOST_GUARD_REQUIRE_PUMP_CONFINED` | enforce cpuset on the interactive pump session | `1` |
+| `HOST_GUARD_REQUIRE_PUMP_CONFINED` | verify + auto-confine the interactive pump session each iteration | `1` |
+| `HOST_GUARD_ADOPT` | `0` disables the in-place auto-confine (pause immediately instead) | `1` (default) |
+| `HOST_GUARD_CLI_PATTERN` | regex matching the CLI process when walking up to the session root | `claude\|codex` (default) |
 | `HOST_GUARD_REQUIRE_MARKERS` + `HOST_GUARD_MARKER_FILES` | require HOST-GUARD cap blocks in listed launcher scripts | project-specific |
 | `HOST_GUARD_TCTL_PAUSE` / `_RESUME` / `_MAX_WAIT` | thermal gate thresholds (°C, °C, s) | `90` / `80` / `1800` |
 | `HOST_GUARD_SAMPLER_INTERVAL` / `_MAX_BYTES` | forensics sampler cadence / csv ring size | `1` / `10485760` |
@@ -38,18 +40,30 @@ never light every core, and size `MEMORY_HIGH` so the sum fits in RAM.
    inherited by every descendant, cannot be widened from inside) +
    CPUQuota/MemoryHigh/TasksMax, plus `taskset -c` (also the no-user-bus
    fallback). Covers **headless** runs completely.
-2. **Pump wrapper** (`host-guard-exec.sh`) — interactive dispatches run inside
-   the foreground CLI session, which the self-wrap cannot reach. Launch the CLI
-   through the wrapper so its whole subtree inherits the same confinement:
-   `scripts/automation/host-guard-exec.sh claude`
-3. **Preflight** (`preflight_host_guard`) — before the loop: forensics sampler
+2. **In-place adoption** (`host-guard-adopt.sh`) — interactive dispatches run
+   inside the foreground CLI session, which the self-wrap cannot reach; this
+   script retrofits the confinement onto the ALREADY-RUNNING session tree, so
+   no special launch command is needed. Mechanics: systemd scope adoption
+   (busctl `StartTransientUnit` with the `PIDs` property + `set-property`) for
+   the CPUQuota/MemoryHigh/TasksMax ceilings, plus `taskset -a -c -p` on the
+   root and every existing descendant for the hard CPU mask (all threads,
+   inherited by all future children — works with no systemd at all).
+   `--cli-root-of <pid>` walks up to the outermost ancestor matching
+   `HOST_GUARD_CLI_PATTERN`. Invoked automatically by the `/goal` command at
+   session start and by the iteration gate on an unconfined pump.
+3. **Pump wrapper** (`host-guard-exec.sh`) — optional belt-and-braces: launch
+   the CLI confined from birth (`scripts/automation/host-guard-exec.sh claude`),
+   which additionally sets the BLAS/OMP thread-cap env vars (impossible to
+   inject into a running process). The fallback when adoption fails.
+4. **Preflight** (`preflight_host_guard`) — before the loop: forensics sampler
    alive (auto-started if not), affinity wrap took effect, launcher marker
    blocks intact. Failure pauses the session `AWAITING_HOST_GUARD` (resumable).
-4. **Iteration gate** (`host_guard_iteration_gate`, top of loop) — thermal
-   cooldown between iterations (wait out heat-soak, bounded), and pump-cpuset
-   verification via the `pid=` line in `.pump-alive` when
-   `HOST_GUARD_REQUIRE_PUMP_CONFINED=1`.
-5. **Forensics sampler** (`host-guard/hwmon-log.sh`) — 1 Hz temps/power/
+5. **Iteration gate** (`host_guard_iteration_gate`, top of loop) — thermal
+   cooldown between iterations (wait out heat-soak, bounded), and — when
+   `HOST_GUARD_REQUIRE_PUMP_CONFINED=1` — pump-cpuset verification (via the
+   `pid=` line in `.pump-alive`, or the CLI root captured at engine launch)
+   with automatic in-place re-confinement; pauses only when that fails.
+6. **Forensics sampler** (`host-guard/hwmon-log.sh`) — 1 Hz temps/power/
    pressure/memory to `<repo>/logs/hwmon/hwmon.csv`, fsync per line, so the
    final pre-reset second survives a hard reset. `{run|start|stop|status|watch}`;
    `status`/`start` recognize an externally-run sampler (e.g. a systemd user
@@ -59,9 +73,11 @@ never light every core, and size `MEMORY_HIGH` so the sum fits in RAM.
 
 Read the printed reason, fix it, then
 `./scripts/automation/run-goal.sh --resume --session-id <sid>` (or
-`/goal-resume`). The common one: the pump session is unconfined — relaunch the
-CLI via `host-guard-exec.sh` and resume. Do not disable flags to silence the
-pause; the caps exist because unconfined load has hard-reset a host.
+`/goal-resume`). Pump-related pauses are rare by construction — the engine
+auto-confines a running pump in place before ever pausing — so a pause means
+adoption itself failed: relaunch the CLI via `host-guard-exec.sh` and resume.
+Do not disable flags to silence the pause; the caps exist because unconfined
+load has hard-reset a host.
 
 ## Origin
 
diff --git a/incredible_auto_dev/scripts/automation/run-goal.sh b/incredible_auto_dev/scripts/automation/run-goal.sh
index 6291321..a2fc8f1 100755
--- a/incredible_auto_dev/scripts/automation/run-goal.sh
+++ b/incredible_auto_dev/scripts/automation/run-goal.sh
@@ -107,6 +107,21 @@ if [[ -z "${HOST_GUARD_WRAPPED:-}" && -f "$_HOST_GUARD_ENV_FILE" ]] \
   source "$_HOST_GUARD_ENV_FILE"
   if [[ "${HOST_GUARD_ENABLED:-0}" == "1" && -n "${HOST_GUARD_CPU_LIST:-}" ]]; then
     export HOST_GUARD_WRAPPED=1
+    # Capture the interactive CLI session root (the pump) BEFORE the re-exec
+    # below reparents us: walk the ppid chain for the outermost process whose
+    # cmdline matches HOST_GUARD_CLI_PATTERN. The iteration gate verifies —
+    # and, if needed, confines in place via host-guard-adopt.sh — this pid.
+    if [[ -z "${HOST_GUARD_PUMP_ROOT_PID:-}" ]]; then
+      _hg_p="$PPID" _hg_root=""
+      while [[ "$_hg_p" =~ ^[0-9]+$ ]] && (( _hg_p > 1 )); do
+        if tr '\0' ' ' < "/proc/$_hg_p/cmdline" 2>/dev/null \
+             | grep -qE "${HOST_GUARD_CLI_PATTERN:-claude|codex}"; then
+          _hg_root="$_hg_p"
+        fi
+        _hg_p="$(awk '/^PPid:/{print $2}' "/proc/$_hg_p/status" 2>/dev/null || true)"
+      done
+      if [[ -n "$_hg_root" ]]; then export HOST_GUARD_PUMP_ROOT_PID="$_hg_root"; fi
+    fi
     _HG_PROPS=( -p "CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}"
                 -p "MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G}"
                 -p "TasksMax=${HOST_GUARD_TASKS_MAX:-2048}" )
@@ -992,24 +1007,45 @@ host_guard_iteration_gate() {
 
   if [[ "${HOST_GUARD_REQUIRE_PUMP_CONFINED:-0}" == "1" && "${AGENT_BACKEND:-}" == "interactive" ]]; then
     local hb="${CHAIN_DISPATCH_DIR:-$GOAL_SESSION_DIR_LOCAL/dispatch}/.pump-alive"
-    local pump_pid="" hb_age width allowed_list allowed_n
+    local pump_pid="" hb_age=999999 target="" width allowed_list allowed_n
     if [[ -f "$hb" ]]; then
       hb_age=$(( EPOCHSECONDS - $(stat -c %Y "$hb" 2>/dev/null || echo 0) ))
       pump_pid=$(sed -n 's/^pid=\([0-9][0-9]*\)$/\1/p' "$hb" 2>/dev/null | head -n 1)
-      # Heartbeat present but no pid line (ident disabled): confinement cannot be
-      # verified — that must be loud, not a silent bypass.
-      if [[ -z "$pump_pid" && "$hb_age" -le "${HOST_GUARD_PUMP_HB_FRESH:-180}" ]]; then
-        _host_guard_pause "cannot verify pump confinement: $hb has no pid= line (heartbeat ident disabled?) — re-enable the pump ident or set HOST_GUARD_REQUIRE_PUMP_CONFINED=0" "iteration_gate"
-      fi
     fi
-    if [[ -n "$pump_pid" && "$hb_age" -le "${HOST_GUARD_PUMP_HB_FRESH:-180}" && -r "/proc/$pump_pid/status" ]]; then
+    # Verification handle: the CLI session root captured at engine launch wins
+    # (it outlives short-lived heartbeat writers); else the live heartbeat pid.
+    if [[ -n "${HOST_GUARD_PUMP_ROOT_PID:-}" && -r "/proc/${HOST_GUARD_PUMP_ROOT_PID}/status" ]]; then
+      target="$HOST_GUARD_PUMP_ROOT_PID"
+    elif [[ -n "$pump_pid" && "$hb_age" -le "${HOST_GUARD_PUMP_HB_FRESH:-180}" && -r "/proc/$pump_pid/status" ]]; then
+      target="$pump_pid"
+    fi
+    if [[ -n "$target" ]]; then
       width=$(_host_guard_mask_width "${HOST_GUARD_CPU_LIST:-}")
-      allowed_list=$(awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$pump_pid/status" 2>/dev/null)
+      allowed_list=$(awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$target/status" 2>/dev/null)
       allowed_n=$(_host_guard_mask_width "$allowed_list")
       if (( width > 0 && allowed_n > width )); then
-        write_session_summary "AWAITING_HOST_GUARD" "$CURRENT_ITER"
-        _host_guard_pause "interactive pump (pid $pump_pid) is unconfined: Cpus_allowed_list=$allowed_list = $allowed_n CPUs > mask width $width — relaunch the pump CLI under the guard, e.g. scripts/automation/host-guard-exec.sh claude" "iteration_gate"
+        # Self-heal first: confine the RUNNING session in place — scope
+        # adoption for memory/task/quota ceilings + taskset for the hard CPU
+        # mask. No relaunch required; the host-guard-exec.sh wrapper remains
+        # the belt-and-braces option (adds BLAS env caps from birth).
+        # HOST_GUARD_ADOPT=0 skips the self-heal and pauses immediately.
+        if [[ "${HOST_GUARD_ADOPT:-1}" == "1" ]]; then
+          echo "[run-goal] host-guard: pump (pid $target) unconfined (Cpus_allowed_list=$allowed_list) — auto-confining in place."
+          HOST_GUARD_ROOT="$REPO_ROOT" bash "$SCRIPT_DIR/host-guard-adopt.sh" --cli-root-of "$target" || true
+          allowed_list=$(awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$target/status" 2>/dev/null)
+          allowed_n=$(_host_guard_mask_width "$allowed_list")
+        fi
+        if (( allowed_n > width )); then
+          write_session_summary "AWAITING_HOST_GUARD" "$CURRENT_ITER"
+          _host_guard_pause "interactive pump (pid $target) is unconfined (Cpus_allowed_list=$allowed_list = $allowed_n CPUs > mask width $width) and in-place auto-confinement did not take — relaunch the pump CLI via scripts/automation/host-guard-exec.sh (e.g. 'scripts/automation/host-guard-exec.sh claude'), or set HOST_GUARD_REQUIRE_PUMP_CONFINED=0" "iteration_gate"
+        fi
+        record_telemetry_event "host_guard_adopt" "$(printf '{"pid":%s,"cpus":"%s"}' "$target" "$allowed_list")"
+        echo "[run-goal] host-guard: pump (pid $target) confined to $allowed_list."
       fi
+    elif [[ "$hb_age" -le "${HOST_GUARD_PUMP_HB_FRESH:-180}" ]]; then
+      # A live pump we cannot even identify (no pid= line in the heartbeat AND
+      # no CLI root captured at launch): loud pause, never a silent bypass.
+      _host_guard_pause "cannot verify pump confinement: no usable pump pid ($hb has no pid= line and no CLI root was captured at engine launch) — re-enable the pump ident or set HOST_GUARD_REQUIRE_PUMP_CONFINED=0" "iteration_gate"
     fi
   fi
   return 0
diff --git a/incredible_auto_dev/skills/goal-interactive-dispatch.md b/incredible_auto_dev/skills/goal-interactive-dispatch.md
index 5a38352..1e25ebb 100644
--- a/incredible_auto_dev/skills/goal-interactive-dispatch.md
+++ b/incredible_auto_dev/skills/goal-interactive-dispatch.md
@@ -151,19 +151,25 @@ concurrent requests never collide.
 The engine's own self-wrap (run-goal.sh) confines only the HEADLESS engine tree.
 Interactive dispatches — every subagent, and every `pytest`/build/browser those
 subagents run through Bash — execute as descendants of THIS foreground CLI
-session, so they inherit whatever CPU/memory confinement this session was
-launched with, and nothing can retrofit it afterwards. When the project declares
-host caps (`project-extensions/host-guard/host-guard.env`), the session must be
-launched through the wrapper:
-
-    scripts/automation/host-guard-exec.sh claude
-
-With `HOST_GUARD_REQUIRE_PUMP_CONFINED=1`, the engine verifies the pump's cpuset
-(via the `pid=` line in `.pump-alive`) at each iteration boundary and pauses the
-session (`AWAITING_HOST_GUARD`, resumable) if the pump is wider than
-`HOST_GUARD_CPU_LIST`. If that pause fires, relaunch the CLI via the wrapper and
-`/goal-resume` — do not disable the flag to make the pause go away; the caps
-exist because unconfined goal-mode load has hard-reset the host.
+session and inherit ITS confinement. When the project declares host caps
+(`project-extensions/host-guard/host-guard.env`), that confinement is applied
+automatically — no special launch command is required:
+
+- the `/goal` command runs `scripts/automation/host-guard-adopt.sh
+  --cli-root-of $$` at session start, which confines the RUNNING CLI process
+  tree in place (scope adoption for memory/task/quota ceilings + a hard
+  `taskset` CPU mask on the tree, inherited by all future children);
+- with `HOST_GUARD_REQUIRE_PUMP_CONFINED=1`, the engine re-verifies the pump at
+  every iteration boundary (via the `pid=` line in `.pump-alive` or the CLI
+  root it captured at launch) and auto-confines it again if needed, pausing
+  (`AWAITING_HOST_GUARD`, resumable) only when in-place confinement fails.
+
+Optional belt-and-braces: launching the CLI through
+`scripts/automation/host-guard-exec.sh claude` confines it from birth and also
+sets the BLAS/OMP thread-cap env vars (those cannot be injected into a running
+process). If the pause ever fires, relaunch via that wrapper and `/goal-resume`
+— do not disable the flag to make the pause go away; the caps exist because
+unconfined goal-mode load has hard-reset the host.
 
 ## Usage sidecar (token telemetry — protocol v2, optional, best-effort)
 
diff --git a/project-extensions/host-guard/host-guard.env b/project-extensions/host-guard/host-guard.env
index 35697d5..162b815 100644
--- a/project-extensions/host-guard/host-guard.env
+++ b/project-extensions/host-guard/host-guard.env
@@ -55,9 +55,13 @@ HOST_GUARD_REQUIRE_MARKERS=0
 # Require the interactive pump (the foreground Claude/Codex session) to be
 # cpuset-confined — the engine self-wrap cannot cover agents dispatched inside
 # the foreground CLI (the gap behind resets #3-#5). The iteration gate verifies
-# the pump's Cpus_allowed_list against the mask and pauses (AWAITING_HOST_GUARD,
-# resumable) when unconfined. Launch the CLI through the wrapper:
-#   scripts/automation/host-guard-exec.sh claude
+# the pump's Cpus_allowed_list against the mask and — when too wide —
+# AUTO-CONFINES the running session in place (host-guard-adopt.sh: scope
+# adoption + taskset across the tree; no relaunch needed), pausing
+# (AWAITING_HOST_GUARD, resumable) only if that fails. Optional from-birth
+# wrapper (adds BLAS env caps): scripts/automation/host-guard-exec.sh claude
+# Related knobs (defaults): HOST_GUARD_ADOPT=1 (0 = pause instead of adopting),
+# HOST_GUARD_CLI_PATTERN="claude|codex" (session-root detection).
 HOST_GUARD_REQUIRE_PUMP_CONFINED=1
 
 # Thermal iteration gate (framework defaults shown; uncomment to tune).
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-desk/state/assumptions.md        | 31 ++++++++++++++++
 runs/goal-session-desk/state/blueprint.md          | 42 ++++++++++++++++++++--
 .../state/enhancement-proposals.jsonl              |  3 ++
 runs/goal-session-desk/state/proposer-result.json  |  8 ++++-
 runs/goal-session-desk/telemetry.jsonl             | 19 ++++++++++
 runs/goal-session-desk/trace/trace.jsonl           |  5 +++
 6 files changed, 104 insertions(+), 4 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
