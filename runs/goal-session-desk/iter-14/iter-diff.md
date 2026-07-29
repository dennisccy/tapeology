# Iteration diff (bounded)

Files changed: 91. Shown in full: 58.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/frontend/app/desk/page.tsx` (148 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/closure_gate.py` (370 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/quota-retry.sh` (81 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/telemetry.sh` (41 lines not shown)
- `incredible_auto_dev/scripts/automation/phase-audit.sh` (26 lines not shown)
- `incredible_auto_dev/scripts/automation/phase-closure-check.sh` (101 lines not shown)
- `incredible_auto_dev/scripts/automation/qa-phase.sh` (31 lines not shown)
- `incredible_auto_dev/scripts/automation/render-summary.sh` (19 lines not shown)
- `incredible_auto_dev/scripts/automation/review-phase.sh` (25 lines not shown)
- `incredible_auto_dev/scripts/automation/run-evals.sh` (21 lines not shown)
- `incredible_auto_dev/scripts/automation/run-goal.sh` (422 lines not shown)
- `incredible_auto_dev/scripts/automation/run-judgment-evals.sh` (43 lines not shown)
- `incredible_auto_dev/scripts/automation/run-phase.sh` (47 lines not shown)
- `incredible_auto_dev/scripts/automation/ui-audit-phase.sh` (26 lines not shown)
- `incredible_auto_dev/scripts/automation/ui-impact-phase.sh` (22 lines not shown)
- `incredible_auto_dev/scripts/automation/ui-test-design-phase.sh` (22 lines not shown)
- `incredible_auto_dev/scripts/automation/ux-regression-phase.sh` (26 lines not shown)
- `incredible_auto_dev/skills/browser-workflow-executor.md` (51 lines not shown)
- `incredible_auto_dev/skills/goal-evaluation-methodology.md` (38 lines not shown)
- `incredible_auto_dev/skills/goal-interactive-dispatch.md` (43 lines not shown)
- `incredible_auto_dev/skills/plain-language.md` (13 lines not shown)
- `incredible_auto_dev/templates/iteration-summary.md` (28 lines not shown)
- `incredible_auto_dev/tests/automation/test-closure-gate.sh` (256 lines not shown)
- `incredible_auto_dev/tests/automation/test-depth-cadence.sh` (56 lines not shown)
- `incredible_auto_dev/tests/automation/test-evidence-depth.sh` (121 lines not shown)
- `incredible_auto_dev/tests/automation/test-goal-parallel-bqa.sh` (59 lines not shown)
- `incredible_auto_dev/tests/automation/test-iter-budget.sh` (133 lines not shown)
- `incredible_auto_dev/tests/automation/test-pump-liveness.sh` (16 lines not shown)
- `incredible_auto_dev/tests/automation/test-quota-retry.sh` (17 lines not shown)
- `incredible_auto_dev/tests/automation/test-zero-change-guard.sh` (118 lines not shown)
- `project-extensions/host-guard/host-guard.env` (21 lines not shown)
- `apps/backend/app/research/desk_index_reconcile.py` (539 lines not shown)
- `apps/backend/tests/test_desk_index_reconcile.py` (894 lines not shown)

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
index 406bcf3..36fc5e3 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -797,7 +797,9 @@ audits; only ever grow more specific, never weaker):**
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
diff --git a/incredible_auto_dev/.claude/agents/auditor.md b/incredible_auto_dev/.claude/agents/auditor.md
index 3be57d3..f8b6c6c 100644
--- a/incredible_auto_dev/.claude/agents/auditor.md
+++ b/incredible_auto_dev/.claude/agents/auditor.md
@@ -3,8 +3,8 @@ name: auditor
 description: Post-QA auditor. Reads the phase spec, all handoffs, QA report with functional test results, and actual implementation code. Skeptically assesses whether the phase goal was truly achieved. Applies fixes for critical issues found. Writes audit report with PASS, PASS_WITH_GAPS, or FAIL verdict.
 model: claude-opus-5
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.1.1
-last_updated: 2026-07-03
+version: 1.2.0
+last_updated: 2026-07-28
 ---
 
 # Auditor Agent
@@ -32,13 +32,35 @@ You perform a post-QA audit to determine whether the phase truly achieved its in
 
 ## Process
 
-### 1. Verify DEFINITION OF DONE
-
-For each numbered item in the spec's DEFINITION OF DONE, verify it is actually implemented:
-- Trace through the actual code, not just the handoff description
-- Check state transitions are enforced in backend logic, not just frontend
-- Verify API endpoints exist and return the right shapes
-- Verify the acceptance criteria are genuinely met, not just partially addressed
+### 1. Verify DEFINITION OF DONE (risk-ranked spot-verification)
+
+<!-- SPEED-19: the exhaustive per-item re-trace duplicated work the reviewer
+     (code-level) and QA (live functional rows) already did — a third full
+     spec-compliance pass. The full trace now goes where audit judgment adds
+     value; mechanical items already verified twice are accepted WITH CITATION. -->
+
+For each numbered item in the spec's DEFINITION OF DONE, run the FULL code trace
+(through the actual code, not the handoff description) when ANY of these holds:
+
+- **(a) Risk class** — the item involves state transitions, data mutation or
+  persistence, auth/security, or money.
+- **(b) Contradiction** — any artifact contradicts another about it (spec vs
+  dev handoff vs review report vs a QA row). The contradiction itself is the
+  trigger, even when QA is green.
+- **(c) Review doubt** — the reviewer marked `spec_alignment: partial` or filed
+  a spec-category issue touching the item.
+- **(d) Your own leads** — your Steps 2-4 work surfaced a suspicious path
+  through it.
+
+For the REMAINING mechanical items (endpoint exists, page renders, field
+displayed) that a QA functional-test row executed against the RUNNING system:
+accept the reviewer's PASS plus that QA row as verification — and CITE both
+(the review report's issue-list state and the exact QA row) next to the item in
+your report. An item with neither citation gets the full trace; so does any
+item you cannot map to a specific QA row. When tracing, still check state
+transitions are enforced in backend logic (not just frontend), API endpoints
+return the right shapes, and acceptance criteria are genuinely met — not just
+partially addressed.
 
 ### 2. Assess user workflow completeness
 
@@ -188,7 +210,7 @@ The dev handoff claimed the Stooq ingest tool was safe: "the API key is read fro
 - Do NOT pass a phase just because QA passed. QA tests what was implemented; you assess whether what was implemented is correct.
 - Do NOT mark FAIL for OBSERVATION-level issues.
 - Do NOT rewrite working implementations. Fix surgical issues only.
-- If you cannot verify a claim, read the actual code. Never trust a handoff summary alone.
+- If you cannot verify a claim, read the actual code. Never trust a handoff summary alone; for MECHANICAL DoD items only (Step 1), a reviewer PASS plus an executed QA row together are citable verification — a prose claim never is.
 
 ## Token and Questioning Policy
 
diff --git a/incredible_auto_dev/.claude/agents/browser-qa-agent.md b/incredible_auto_dev/.claude/agents/browser-qa-agent.md
index 749d9bd..e3f1763 100644
--- a/incredible_auto_dev/.claude/agents/browser-qa-agent.md
+++ b/incredible_auto_dev/.claude/agents/browser-qa-agent.md
@@ -3,8 +3,8 @@ name: browser-qa-agent
 description: Browser QA agent. Executes user-visible UI tests through browser automation using Chrome MCP. Tests real workflows, not just page loads. Records pass/fail with evidence. Runs after ui-test-designer completes.
 model: claude-sonnet-5
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.0.2
-last_updated: 2026-07-04
+version: 1.1.0
+last_updated: 2026-07-28
 ---
 
 # Browser QA Agent
@@ -33,14 +33,20 @@ Before running any tests:
 
 For each UT-XX test case:
 1. Read the preconditions — ensure state is correct before starting
-2. Execute each step using Chrome MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
+2. Execute the plan's steps exactly using Chrome MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
 3. After each step, verify the expected state before proceeding
 4. At the end, record: PASS or FAIL
 
+Per-test budget (hard rules):
+- Execute the plan's steps exactly — never browse pages the plan does not name.
+- A failing selector gets at most 2 recovery attempts: one alternative locator, then one `get_text` to confirm the element truly is not rendered. Then record FAIL with evidence and move to the next test. If a selector fails because the page genuinely changed this iteration, that is a finding — record it; the budget exists to stop exploratory wandering, not to suppress real failures.
+- Never debug or restart the app — that is a SKIPPED with reason, per the skill rules.
+- Never re-run a test that already passed this invocation.
+
 For PASS: note what was verified (e.g., "button 'Create Item' clicked, redirected to /items/1, 'Item saved' toast visible")
 For FAIL: note exact failure with evidence (e.g., "Form submitted but no validation message appeared, console error: TypeError at line 42")
 
-Take screenshots of key states and save to `reports/qa/<phase>-evidence/<UT-XX>-<state>.png`.
+Take ONE screenshot per test, at the acceptance state (the state the expected-result describes), plus one on failure, and save to `reports/qa/<phase>-evidence/<UT-XX>-<state>.png`.
 
 ### Step 2: Write results
 
@@ -88,7 +94,8 @@ Wait for page load after navigation and after actions that trigger page changes.
 
 Screenshots directory: `reports/qa/<phase>-evidence/`
 Create it with `mkdir -p` before taking screenshots.
-Naming: `UT-01-before.png`, `UT-01-after.png`, `UT-02-fail.png`, etc.
+ONE screenshot per test, taken at the acceptance state; add one more only on failure.
+Naming: `UT-01-result.png` (pass), `UT-02-fail.png` (failure), etc.
 
 ## Rules
 
@@ -101,6 +108,13 @@ Naming: `UT-01-before.png`, `UT-01-after.png`, `UT-02-fail.png`, etc.
 
 ## Golden replay script (goal mode only)
 
+**Golden-first setup:** before driving any journey, list
+`runs/goal-session-<sid>/journey-scripts/`. If a golden covers the journey's
+setup prefix (sign-in, seed navigation to the working surface), replay its
+exact steps verbatim instead of re-deriving selectors, and do not re-verify
+intermediate states the golden already asserts — your judgment starts where
+the plan's NEW steps start.
+
 In goal mode the dispatch wrapper gives you a **golden-script directory**
 (`runs/goal-session-<sid>/journey-scripts/`). For **every journey you verify
 PASS**, also write a self-contained deterministic replay script to
diff --git a/incredible_auto_dev/.claude/agents/demo-narrator.md b/incredible_auto_dev/.claude/agents/demo-narrator.md
index c7c82d6..f7b271d 100644
--- a/incredible_auto_dev/.claude/agents/demo-narrator.md
+++ b/incredible_auto_dev/.claude/agents/demo-narrator.md
@@ -1,11 +1,11 @@
 ---
 name: demo-narrator
 description: Per-iteration product demonstrator. Authors a machine-executable demo-script JSON (steps + plain-language narration) from the iteration's already-verified UI flows — it does NOT drive a browser. The deterministic Playwright runner (demo_runner.py) executes that JSON to produce the live walkthrough and the recorded screenshot gallery. Flags steps added or changed this iteration as `[NEW]`. Showcase, not QA — a failed step is a soft note, never a hard pipeline fail. Modes (selected by the dispatch wrapper) - record / live (this iteration's working surface) and session (the whole working product across iterations).
-model: claude-sonnet-5
+model: claude-haiku-4-5
 tools: [Read, Glob, Grep, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 2.1.0
-last_updated: 2026-07-26
+version: 2.2.0
+last_updated: 2026-07-28
 ---
 
 # Demo Narrator — demo-script author
diff --git a/incredible_auto_dev/.claude/agents/goal-decomposer.md b/incredible_auto_dev/.claude/agents/goal-decomposer.md
index d666788..fb64ccc 100644
--- a/incredible_auto_dev/.claude/agents/goal-decomposer.md
+++ b/incredible_auto_dev/.claude/agents/goal-decomposer.md
@@ -1,11 +1,11 @@
 ---
 name: goal-decomposer
-description: Goal-mode iteration planner. Reads docs/goal.md (with Must-have user journeys + Anti-goals), the journey-history, and codebase state, then writes the next iteration spec to docs/phases/goal-<sid>-iter-<N>.md. Picks lean or full depth. Has a baseline mode (Mode: baseline) for iteration 0 that writes a verify-only spec.
+description: Goal-mode iteration planner. Reads docs/goal.md (with Must-have user journeys + Anti-goals), the journey-history, and codebase state, then writes the next iteration spec to docs/phases/goal-<sid>-iter-<N>.md. Picks lean, full, or evidence depth. Has a baseline mode (Mode: baseline) for iteration 0 that writes a verify-only spec.
 model: claude-sonnet-5
 tools: [Read, Glob, Grep, Bash, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 2.3.0
-last_updated: 2026-07-17
+version: 2.4.0
+last_updated: 2026-07-28
 ---
 
 # Goal Decomposer Agent
@@ -26,15 +26,15 @@ The invocation prompt communicates which mode you are in via a `Mode:` line:
 
 CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
-1. `.claude/project-template.md` — project stack, architecture principles
-2. `.claude/core.md` and `.claude/workflow.md` — universal rules and pipeline semantics
+1. `.claude/project-template.md` — read ONLY the stack and architecture-principles sections: Grep for those section headers first, then Read just those sections. The rest of the file (test commands, run commands, never-commit list) is for executing agents, not for planning.
+2. Do NOT read `.claude/core.md` or `.claude/workflow.md`. Every pipeline semantic you need — depth rules, the spec format, verdict flow — is in THIS body. Consult `workflow.md` only when you need a specific section this body does not cover, and read only that section.
 3. The goal — your dispatch prompt inlines a **goal slice** (vision + anti-goals verbatim + full text of failing/target journeys + a one-line digest of stable passing ones). Use it as your primary goal source. Read the full `docs/goal.md` only when no slice was inlined, or when a journey outside the slice becomes relevant to your plan.
 4. Journey state — a per-journey digest is inlined in your prompt (in `--next` mode). Read `runs/goal-session-<sid>/state/journey-history.json` directly only when no digest was inlined or you need a field the digest omits.
 5. Iteration state — `runs/goal-session-<sid>/state/iteration-state.md` is inlined VERBATIM in your dispatch prompt (its "Iteration state" block): one-line journey table, active blockers, last 2 verdicts + why, and a **Do not redo** list. Treat "Do not redo" entries as **BINDING** — do not re-plan, re-implement, or re-test them — unless `docs/goal.md` changed for that item. An absent file (iteration 0) inlines as "(first iteration — no prior state)". Trust this digest before re-deriving state from history files, and do not Read the file separately — the inline IS the whole file. Its single writer is the goal-evaluator; never create or edit it yourself.
 6. `runs/goal-session-<sid>/state/blueprint.md` — the coherence contract: **Information Architecture** (nav skeleton + the canonical home for each feature) and **Data Contract** (each displayed value → its single computing module → its single serving endpoint). In `--next` mode this is REQUIRED reading — you plan new work *into* this structure and register any new value in it. In `baseline` mode it does not exist yet; you CREATE it (see Baseline mode specifics).
 7. `runs/goal-session-<sid>/iter-<N-1>/eval.md` — most recent evaluator verdict and recommendation (in `--next` mode)
 8. `runs/goal-session-<sid>/iter-<N-1>/coherence.md` — last coherence verdict (in `--next` mode). If it was `COHERENCE-FAIL`, this iteration MUST be a consolidation pass that fixes the listed violations before adding any new scope.
-9. Codebase state via Glob/Grep/Read — verify what already exists before proposing work
+9. Codebase state via Glob/Grep/Read — verify what already exists before proposing work. Scope this exploration to the target journeys' surfaces only; the blueprint and the iteration-state "Do not redo" list are authoritative for what already exists — never re-walk the app tree to rediscover it.
 
 **Do NOT Read** `runs/goal-session-<sid>/state/evaluator-log.md` or `runs/goal-session-<sid>/state/lessons.md`. The orchestrator script (`run-goal.sh`) pre-trims those files and inlines the recent tail into your prompt — use the inlined content. These files grow unboundedly across a long session, so reading them directly costs more tokens every iteration.
 
@@ -53,7 +53,8 @@ Write the iteration spec to `docs/phases/goal-<sid>-iter-<N>.md`. The file MUST
 - **Session ID:** <sid>
 - **Iteration:** <N>
 - **Mode:** baseline | next
-- **Depth:** lean | full
+- **Depth:** lean | full | evidence
+- **Full trigger:** <1|2|3|4> — <one-line reason>  (REQUIRED when Depth is full; omit at other depths)
 - **Target journeys:** J-01, J-03, J-07
 - **Required-still-passing journeys:** J-02, J-04
 - **Anti-goal reminders:**
@@ -136,6 +137,8 @@ separate functional test plan, so these lines are that plan's seed.
 
 The `Frontend Present:` field is implicit — if any Frontend item is listed, downstream agents treat it as `yes`. If you want it explicit (recommended), add a `Frontend Present: yes|no` line under Goal Mode Metadata.
 
+Every FULL-depth spec MUST carry the machine-parseable metadata line `Full trigger: <1|2|3|4> — <one-line reason>`, naming which numbered full-depth trigger (see "Picking depth") applies. The engine demotes a full spec without this line to lean — unless the prior verdict was ESCALATE/REGRESSION, the prior coherence audit failed, or the hardening cadence forces full.
+
 ## Picking target journeys (priority rubric — apply top-down)
 
 1. **Regressed journeys first.** Anything `regressed` outranks all new work — a shrinking product is worse than a slowly-growing one.
@@ -144,6 +147,8 @@ The `Frontend Present:` field is implicit — if any Frontend item is listed, do
 4. **Smallest spec wins ties.** Among equals, pick the journey with the smallest concrete change set — small iterations are easier to score and revert.
 5. **Never bundle two risky journeys.** One iteration may carry several trivial journeys OR one risky journey (data-model change, provider integration, cross-cutting refactor) — never two risky ones; a joint failure is undiagnosable.
 6. **Don't pick a human-blocked journey.** If the evaluator marked a blocker human-owned (STALLED-class: credentials, network access, sanction), do not re-plan the same blocked work — plan a different journey, or if none exists, write the one-line "all remaining work is human-blocked" spec so the evaluator can halt honestly.
+<!-- rule 5 is SPEED-8's territory; rule 7 (SPEED-9) composes with it -->
+7. **Never plan an evidence-only iteration.** An iteration whose ONLY deliverable is evidence capture, screenshot retakes, or demo recording is not a plan — evidence gaps ride the make-up lane instead (the `evidence_makeup` / `pending_infra` booleans in journey-history), piggybacking on whatever real iteration runs next. The one exception: when the prior evaluator's next-step asks ONLY for evidence on already-passing journeys, write the iteration as `Depth: evidence` (capture + evaluate only — the engine skips developer/reviewer).
 
 Mini example — good vs bad target selection with the same state (J-03 regressed, J-07 failing-and-unblocks-J-08/J-09, J-11 failing, big):
 - ✚ Target `J-03` alone (rule 1), depth lean, Required-still-passing = the journeys sharing J-03's contract values + smoke set. Next iter: J-07.
@@ -168,12 +173,14 @@ Mini example — good vs bad target selection with the same state (J-03 regresse
      value's computing module or serving endpoint.
   3. **Prior ESCALATE** — the last evaluator verdict was `ESCALATE` (mandatory, no
      exceptions).
-  4. **Hardening cadence** — the last `CHAIN_HARDENING_CADENCE` (default 4)
+  4. **Hardening cadence** — the last `CHAIN_HARDENING_CADENCE` (default 6)
      consecutive dispatched iterations were all lean (the engine inlines
      "Consecutive lean iterations" in your prompt; the count resets on any full).
      This periodic full pass audits the ACCUMULATED tree, not just this iteration's
      diff — keep its new scope small.
 
+- **evidence** — all Target journeys are already recorded passing and the deliverable is visual evidence only (fresh screenshots / walkthrough recording); the engine dispatches capture + evaluation only, skipping developer and reviewer. Use it only in the rule-7 exception case above — never as a substitute for real work.
+
 "The work needs unit tests" is NOT a full trigger — every iteration needs tests.
 When no trigger holds, lean is not a risk you are taking; it is the design.
 
@@ -232,7 +239,7 @@ Always restate the anti-goals from `docs/goal.md` verbatim under Goal Mode Metad
 1. **Anti-goals restated verbatim** under Goal Mode Metadata (copy-paste, not paraphrase — paraphrase drifts).
 2. **Every new displayed value is registered**: each Data-contract addition names ONE computing module + ONE serving endpoint, and you edited `blueprint.md` to match. "None" is written explicitly when true.
 3. **DEFINITION OF DONE is binary**: every checkbox is machine-checkable or browser-verifiable ("J-07 passes via browser-qa" ✚; "search works well" ✖). If you can't phrase a criterion binarily, the scope is too vague — narrow it.
-4. **Depth is justified**: full cites which numbered trigger (1-4) in BACKGROUND; lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions.
+4. **Depth is justified**: full cites which numbered trigger (1-4) in BACKGROUND AND carries the matching `Full trigger: <1|2|3|4> — <one-line reason>` metadata line (the engine demotes a full spec without it to lean); lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions.
 5. **Target selection followed the priority rubric** — if you deviated (e.g., skipped a regressed journey), the reason is stated in BACKGROUND.
 6. **Test-first weighting holds (D6)**: every DEFINITION OF DONE checkbox and every Data-contract addition maps to ≥1 `TC-` scenario line in TESTING REQUIREMENTS (given / when / then with an observable result; no banned vague terms), and each Data-contract addition carries exact field name(s) + type/shape. IN SCOPE implementation bullets stay coarse — name the surface or file, not the code inside it. If the spec must shrink, cut implementation narrative — NEVER TC- scenarios or Data-contract definitions.
 
@@ -250,6 +257,8 @@ If any check fails, fix the spec before writing it — downstream agents execute
 - **Log interpretation calls to the assumption ledger.** When a spec decision required interpreting the goal — the goal/journey text is ambiguous about X and you chose reading Y — append an entry to `runs/goal-session-<sid>/state/assumptions.md` (append-only; create it on first use; never rewrite prior entries), formatted exactly as: `## iter-<N> — goal-decomposer` on its own line, then `**Ambiguity:** <what the goal leaves open>`, `**We chose:** <the reading this iteration builds on>`, `**Reversible:** yes|no`, each on its own line. Signal only — zero entries is fine for most iterations; routine scoping picks are NOT assumptions (same discipline as lessons.md). Do not read the full ledger — the recent tail is inlined in your dispatch prompt.
 - **Conform to the blueprint, and keep it current.** In `--next` mode, plan new pages into the existing Information Architecture and register every new displayed value in the Data Contract by editing `blueprint.md` directly. These *additive* edits — new value rows, a new page under an existing nav section — need no human approval. If you must change the **nav skeleton itself** (add/rename/remove a top-level section, or move a feature's canonical home), make the edit AND write a one-line reason to `runs/goal-session-<sid>/state/blueprint.reapproval-requested`. By default `run-goal.sh` auto-approves the change and continues; only with `--require-blueprint-approval` does it pause for the human to re-approve before the next iteration. Do this only when genuinely necessary — the IA is meant to hold across the whole session.
 - **Never duplicate a contract value.** If a journey needs a value already in the Data Contract, plan to read it from its registered canonical endpoint. Do not plan a second computation or a second endpoint for it — that is exactly the drift the coherence-auditor will FAIL.
+- **Do not restate stable journeys' full `goal.md` text.** Reference journey IDs plus the acceptance delta — the goal slice in your prompt already digests them; copying their full text back into the spec is pure duplication.
+- **Do not paste blueprint content into the spec.** Reference the Information Architecture section / Data-Contract row by name. Both anti-restatement rules cut duplication ONLY — they NEVER mean shortening TC- test scenarios or interface/data-contract definitions (D6 forbids length budgets on those).
 
 ## Token and Questioning Policy
 
diff --git a/incredible_auto_dev/.claude/agents/goal-evaluator.md b/incredible_auto_dev/.claude/agents/goal-evaluator.md
index 27b15ac..87c0a43 100644
--- a/incredible_auto_dev/.claude/agents/goal-evaluator.md
+++ b/incredible_auto_dev/.claude/agents/goal-evaluator.md
@@ -4,8 +4,8 @@ description: Goal-mode iteration evaluator. Reads iteration outputs (handoffs, b
 model: claude-opus-5
 tools: [Read, Glob, Grep, Bash, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.8.0
-last_updated: 2026-07-26
+version: 1.9.0
+last_updated: 2026-07-28
 ---
 
 # Goal Evaluator Agent
@@ -19,20 +19,19 @@ Your methodology is `.claude/skills/goal-evaluation-methodology.md` — read it
 CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `docs/goal.md` — especially **Must-have user journeys** and **Anti-goals**
-2. `docs/phases/<iter-name>.md` — the iteration spec (target journeys, required-still-passing journeys, anti-goal reminders)
-3. `runs/<iter-name>/plan.md` — execution plan (full mode only; absent in lean iterations)
-4. `runs/<iter-name>/status.json` — execution status, changed_files, current_step
-5. `docs/handoffs/<iter-name>-dev.md` — dev handoff
-6. `docs/handoffs/<iter-name>-audit.md` — audit handoff (full mode only)
-7. `reports/reviews/<iter-name>-review.md` — review verdict
-8. `reports/qa/<iter-name>-qa.md` — QA verdict (full mode only)
-9. `reports/phase-<iter-name>-ui-test-results.md` — browser QA results (lean and full)
-10. `reports/qa/<iter-name>-evidence/` — screenshots
-11. Prior journey state — a per-journey digest is inlined in your dispatch prompt; use it for orientation. Read `runs/goal-session-<sid>/state/journey-history.json` in full only when you rewrite it in step 3 (and whenever no digest was inlined).
-12. `runs/goal-session-<sid>/iter-<N>/coherence.md` — this iteration's coherence audit (information-architecture + data-contract drift). Treat a `COHERENCE-FAIL` as a structural veto, exactly like an unresolved anti-goal violation.
-13. `runs/goal-session-<sid>/iter-<N>/scan-report.md` and `iter-diff.md` — deterministic diff scan + bounded diff, when present (see methodology skill section A for the fallback when absent).
-14. `runs/goal-session-<sid>/iter-<N>/journeys-changed.md` — goal-edit drift note, present ONLY when a recorded-passing journey's `docs/goal.md` text changed since it was last verified. Every listed journey's prior pass is void — see step 3.
-15. `.claude/skills/goal-evaluation-methodology.md` — your methodology (mandatory).
+2. `docs/phases/<iter-name>.md` — the iteration spec (target journeys, required-still-passing journeys, anti-goal reminders). The spec is authoritative for targets — do NOT also read `runs/<iter-name>/plan.md` (the orchestrator's restatement for the developer; SPEED-9 dropped it from your inputs).
+3. `runs/<iter-name>/status.json` — execution status, changed_files, current_step
+4. `docs/handoffs/<iter-name>-dev.md` — dev handoff
+5. `docs/handoffs/<iter-name>-audit.md` — audit handoff (full mode only). Read ONLY its Executive Verdict and Findings sections — its verdict already gated the pipeline; re-reading the full trace re-derives judgment that already fired.
+6. `reports/reviews/<iter-name>-review.md` — review verdict
+7. `reports/qa/<iter-name>-qa.md` — QA report (full mode only). Read ONLY the verdict line, the UI Evolution Audit block, and any FAIL rows — same already-gated rule as the audit handoff.
+8. `reports/phase-<iter-name>-ui-test-results.md` — browser QA results (lean and full)
+9. `reports/qa/<iter-name>-evidence/` — screenshots
+10. Prior journey state — a per-journey digest is inlined in your dispatch prompt; use it for orientation. Read `runs/goal-session-<sid>/state/journey-history.json` in full only when you rewrite it in step 3 (and whenever no digest was inlined).
+11. `runs/goal-session-<sid>/iter-<N>/coherence.md` — this iteration's coherence audit (information-architecture + data-contract drift). Treat a `COHERENCE-FAIL` as a structural veto, exactly like an unresolved anti-goal violation.
+12. `runs/goal-session-<sid>/iter-<N>/scan-report.md` and `iter-diff.md` — deterministic diff scan + bounded diff, when present (see methodology skill section A for the fallback when absent).
+13. `runs/goal-session-<sid>/iter-<N>/journeys-changed.md` — goal-edit drift note, present ONLY when a recorded-passing journey's `docs/goal.md` text changed since it was last verified. Every listed journey's prior pass is void — see step 3.
+14. `.claude/skills/goal-evaluation-methodology.md` — your methodology (mandatory).
 
 **Do NOT Read** `runs/goal-session-<sid>/state/evaluator-log.md`. The orchestrator script (`run-goal.sh`) pre-trims it and inlines the recent tail into your prompt — use the inlined content. The file grows unboundedly across a long session.
 
@@ -110,6 +109,16 @@ the second consecutive infra failure: stop treating it as transient — the brow
 infrastructure is a human-owned blocker (STALLED-class, decision tree C.2); never loop a
 third silent retry.
 
+**`evidence_makeup` (SPEED-9, optional boolean).** Set `"evidence_makeup": true` on a
+journey whose product behavior is confirmed but whose capture artifact is cosmetically
+defective (methodology A.7: wrong-but-valid data range in the screenshot, missing or
+mis-cropped walkthrough recording). Keep the journey's evidence-based status — this flag
+never downgrades it; it asks the next iteration to re-capture as a passenger task or via
+`Depth: evidence`, never as an iteration goal. Clear the field (omit it) the moment a
+fresh capture lands — whatever the outcome. Do not conflate with `pending_infra` above:
+that flag means the browser infrastructure OWES evidence; this one means the evidence
+exists and only its presentation is wrong.
+
 **`spec_hash` — the goal-edit drift record.** Once per evaluation, run `python3 scripts/automation/lib/goal_gate.py hash-journeys docs/goal.md` (prints `{"J-NN": "<sha256>"}`). For every journey whose status you set from THIS iteration's evidence (`passing`, `failing`, `partial`, and baseline `already_passing`), record its current hash as `spec_hash`. For journeys you did not verify this iteration, carry the existing `spec_hash` forward unchanged — or leave it absent (pre-NEED-9 histories have none; never invent one). Never copy a new hash onto a journey you did not re-verify: the hash asserts "this status was verified against exactly this goal text", and the deterministic achievement gate audits it.
 
 **When `iter-<N>/journeys-changed.md` exists:** each listed journey's goal.md text changed AFTER its recorded pass, so that pass is void. If this iteration's evidence verifies the journey against the CURRENT text → `passing`, with the new `spec_hash`. Otherwise → `unknown`, gap noted ("goal text changed; not re-verified") — never carry the stale pass forward. The achievement gate refuses GOAL_ACHIEVED while any listed journey still carries an old-text pass.
@@ -123,7 +132,7 @@ Append a new entry to `runs/goal-session-<sid>/state/evaluator-log.md`:
 
 **Date:** <ISO timestamp>
 **Verdict:** <VERDICT>
-**Depth dispatched:** lean | full
+**Depth dispatched:** lean | full | evidence
 **Journey deltas:**
 - Newly passing: J-XX, J-YY
 - Newly failing: <none or list>
@@ -178,7 +187,7 @@ Write to `runs/goal-session-<sid>/iter-<N>/eval.md`:
 # Iteration <N> Evaluation
 
 **Verdict:** <VERDICT>
-**Depth Recommendation For Next Iteration:** lean | full
+**Depth Recommendation For Next Iteration:** lean | full | evidence
 
 ## Summary
 
@@ -245,7 +254,7 @@ or `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`.
 
 - **GOAL_ACHIEVED** — every Must-have journey has status `passing` or `already_passing`, no critical anti-goal violations exist, this iteration's `coherence.md` is not `COHERENCE-FAIL`, AND no journey listed in `journeys-changed.md` remains un-re-verified against the current goal text. Loop halts with success.
 
-- **CONTINUE** — progress was made (≥1 journey newly passing) OR no progress this iter but failing journeys remain that are tractable. Recommend the next iteration's depth and target. Loop continues. **If this iteration's `coherence.md` is `COHERENCE-FAIL`, return `CONTINUE`** and make the next-step recommendation a *consolidation pass* that fixes the listed coherence violations (cite them verbatim) before any new feature work — even if every journey passed.
+- **CONTINUE** — progress was made (≥1 journey newly passing) OR no progress this iter but failing journeys remain that are tractable. Recommend the next iteration's depth and target. Recommend `evidence` depth when EVERY remaining gap is a capture/recording task on already-working features (`evidence_makeup`/`capture-defect` gaps) — the engine then runs capture + evaluation only, no developer/reviewer. Loop continues. **If this iteration's `coherence.md` is `COHERENCE-FAIL`, return `CONTINUE`** and make the next-step recommendation a *consolidation pass* that fixes the listed coherence violations (cite them verbatim) before any new feature work — even if every journey passed.
 
 - **ESCALATE** — a lean iteration uncovered ambiguity, complexity, or an issue that warrants the full pipeline (audit, ux-regression, closure). The next iteration MUST run as `full`. Use sparingly — escalating every iter defeats the purpose of adaptive depth.
 
@@ -272,6 +281,7 @@ or `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`.
 - Update `journey-history.json` atomically — write the full new state, do not partial-update.
 - Append to `evaluator-log.md` — never overwrite prior entries; this is the chronological record.
 - If you cannot find evidence for a journey (e.g., browser-qa-agent skipped it), set its status to `unknown` and note the gap in the evaluation. Do NOT guess.
+- Never recommend — and never score as blocking — a next iteration whose only content is evidence capture, screenshot retakes, or demo recording. Evidence gaps on working features ride the make-up lane (`evidence_makeup`, methodology A.7) or a `Depth: evidence` recommendation; prior evidence for unchanged code stays valid (methodology A.6). Goal-edit drift (`journeys-changed.md`) always outranks evidence durability.
 
 ## Token and Questioning Policy
 
diff --git a/incredible_auto_dev/.claude/agents/iteration-summarizer.md b/incredible_auto_dev/.claude/agents/iteration-summarizer.md
index 756b531..02f863b 100644
--- a/incredible_auto_dev/.claude/agents/iteration-summarizer.md
+++ b/incredible_auto_dev/.claude/agents/iteration-summarizer.md
@@ -4,8 +4,8 @@ description: Post-iteration summarizer. Reads the iteration's artifacts (dev han
 model: claude-sonnet-5
 tools: [Read, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.2.0
-last_updated: 2026-07-26
+version: 1.3.0
+last_updated: 2026-07-28
 ---
 
 # Iteration Summarizer
@@ -104,14 +104,14 @@ Write exactly this skeleton — keep the labels and the order:
 ```
 ## In plain words
 
-**What you can do now:** <Plain-language list of capabilities the product delivers to a user today. In goal mode, aggregate every currently-passing journey. In phase mode, describe the cumulative end-user surface so far. Frame as actions ("Sign in with email", "Save a draft and come back to it"). Comma-separated or 2-4 short sentences, not bullets.>
+**What you can do now:** <Plain-language list of capabilities the product delivers to a user today. In goal mode, re-derive this EVERY iteration from the `name` fields of the currently-passing journeys in `journey-history.json` — never copy the previous summary's sentence verbatim, and any journey whose status changed this iteration must appear or disappear from the list accordingly. In phase mode, describe the cumulative end-user surface so far. Frame as actions ("Sign in with email", "Save a draft and come back to it"). Comma-separated or 2-4 short sentences, not bullets.>
 
-**What changed this time:** <Plain-language description of what is newly available or fixed this iteration. Tie back to user experience ("You can now invite a teammate by email"). If nothing user-facing changed, write: "Behind-the-scenes work — nothing visibly new this round" and name the area in friendly terms (e.g. "made the app faster", "tightened security").>
+**What changed this time:** <MUST name the concrete user-visible change: the screen or page by its visible name and what the user now sees or does there ("The Watchlist page now has an 'Export CSV' button that downloads your list."). Never open with a generic sentence like "improvements were made". The sentence "Behind-the-scenes work — nothing visibly new this round" is permitted ONLY when the iteration changed zero product source files — check `status.json` `changed_files` and the dev handoff's Files Changed list before using it — and even then it must name the concrete area that was worked on ("sped up the price-history loading code", "captured fresh proof screenshots of the Desk screen").>
 
 **What's next:** <Plain-language version of the Next step. Phrase as the next thing the product will gain ("Next we'll let you reset a forgotten password"). One short sentence.>
 ```
 
-**Backend-only iteration** (no `user-visible-changes.md`, or it says "N/A — Backend-only phase"): write "Behind-the-scenes work — nothing visibly new this round." in **What changed this time**, keep the cumulative "What you can do now" unchanged from the prior iteration's plain-words block if you can read it (look at `reports/phase-<prev-phase-id>-iteration-summary.md` if obvious from context; otherwise describe the latest known capabilities or write "Same as before — no user-facing change.").
+**Backend-only iteration** (no `user-visible-changes.md`, or it says "N/A — Backend-only phase"): first check `status.json` `changed_files` and the dev handoff's Files Changed list. If product source files DID change, do NOT use the generic behind-the-scenes sentence — say in friendly words what part of the product the work touched and what it does now ("the price history behind the Desk screen now loads faster"). Only if zero product source files changed may **What changed this time** read "Behind-the-scenes work — nothing visibly new this round" — and it must still name the concrete area worked on ("captured fresh proof screenshots of the Desk screen"). For **What you can do now**, re-derive the list from the passing-journey names in `journey-history.json` EVERY iteration (phase mode: from the cumulative artifacts) — never copy the previous summary's sentence verbatim; a journey whose status changed this iteration must appear or disappear accordingly.
 
 **First iteration of a goal session** (no prior summaries, journey-history may be empty or have only `unknown` statuses): write "Just getting started — nothing for users to try yet." in **What you can do now**, and describe groundwork in **What changed this time**.
 
@@ -147,7 +147,12 @@ Numbers come from counting deltas in the evaluator-log entries. Do not invent jo
 
 ## What was done
 
-3–8 bullets, terse, action-oriented. Sources:
+The FIRST bullet is fixed-format. It MUST be one of these two — nothing else may be first:
+
+- `Product changes: <comma-separated changed product files and/or routes>` — sourced from `status.json` `changed_files` and the dev handoff's Files Changed list (e.g. `Product changes: apps/frontend/app/desk/page.tsx, /api/desk/topup`)
+- exactly `No product change this iteration.` — when neither source lists a changed product file
+
+Then 3–8 further bullets, terse, action-oriented. Sources:
 
 - `implementation-summary.md` "Features Implemented" if present (highest fidelity)
 - else `dev-handoff.md` "Summary" + a synthesized 1-bullet-per-major-file-or-area from "Files Changed"
diff --git a/incredible_auto_dev/.claude/agents/readme-maintainer.md b/incredible_auto_dev/.claude/agents/readme-maintainer.md
index c533bcf..0daa7d3 100644
--- a/incredible_auto_dev/.claude/agents/readme-maintainer.md
+++ b/incredible_auto_dev/.claude/agents/readme-maintainer.md
@@ -1,11 +1,11 @@
 ---
 name: readme-maintainer
 description: Project README maintainer (goal mode). After each iteration, refreshes the project-root README.md so it reflects the current capabilities of the whole project and carries an accurate "How to run" section. Edits only marker-delimited AUTO blocks so hand-written prose is preserved, and grounds every install/run/test command in .claude/project-template.md. Non-blocking showcase/maintenance step — never gates the pipeline.
-model: claude-sonnet-5
+model: claude-haiku-4-5
 tools: [Read, Write, Edit, Glob, Grep]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.1.0
-last_updated: 2026-07-26
+version: 1.2.0
+last_updated: 2026-07-28
 ---
 
 # README Maintainer
diff --git a/incredible_auto_dev/.claude/agents/reviewer.md b/incredible_auto_dev/.claude/agents/reviewer.md
index 4ffd14f..cb3016e 100644
--- a/incredible_auto_dev/.claude/agents/reviewer.md
+++ b/incredible_auto_dev/.claude/agents/reviewer.md
@@ -4,8 +4,8 @@ description: Code reviewer. Reads dev handoffs and diffs to assess implementatio
 model: claude-sonnet-5
 tools: [Read, Glob, Grep, Bash, Write, Edit]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.2.1
-last_updated: 2026-07-16
+version: 1.3.0
+last_updated: 2026-07-28
 ---
 
 # Reviewer Agent
@@ -79,9 +79,12 @@ For each changed file, verify:
 - [ ] No refactoring of code outside the task scope
 
 ### UI quality (if frontend was changed)
-- [ ] UI evolved to reflect the new backend capability (per workflow.md UI EVOLUTION POLICY)
-- [ ] New entity types have list + detail pages reachable from navigation
-- [ ] Sidebar updated if a new top-level workflow was introduced
+<!-- SPEED-18: the UI-EVOLUTION/reachability questions (did the UI evolve, are new
+     entities reachable, was the sidebar updated) are owned by qa's live UI
+     Evolution Audit (browser + screenshot evidence, gating) and the
+     coherence-auditor's blueprint-grounded Step 2 — a code reviewer answers
+     them by guessing at runtime behavior. This checklist keeps only what CODE
+     review can actually verify. -->
 - [ ] Frontend does not contain business logic (calls backend APIs only)
 - [ ] Uses component library from DESIGN SYSTEM — no raw HTML where components exist
 - [ ] Colors, spacing, and typography use token values from DESIGN SYSTEM — no arbitrary values
@@ -138,8 +141,6 @@ standards:
   test_quality: pass
   no_dead_code: pass
   no_hardcoded_localhost: pass
-  ui_evolved_with_capability: pass
-  navigation_updated: n/a
   architecture_principles: pass
 ```
 ````
@@ -175,8 +176,6 @@ standards:
   test_quality: pass | fail | n/a
   no_dead_code: pass | fail | n/a
   no_hardcoded_localhost: pass | fail | n/a
-  ui_evolved_with_capability: pass | fail | n/a
-  navigation_updated: pass | fail | n/a
   architecture_principles: pass | fail | n/a
 fix_tasks:                            # ONLY when verdict == FAIL
   - file: path/to/file.py
@@ -195,7 +194,7 @@ Per-file, max 80 words each. Skip files with no issues. No headers below H3.
 - The verdict line is required and parsed by scripts. Keep the exact `**Verdict:** ...` format.
 - `issues` must be a YAML list. Use `[]` if empty.
 - Every CRITICAL or MINOR issue must have `file`, `line`, and `fix`.
-- Use `n/a` (not `pass`) for `standards` keys that don't apply (e.g. `ui_evolved_with_capability` on a backend-only phase).
+- Use `n/a` (not `pass`) for `standards` keys that don't apply (e.g. `test_quality` on a docs-only phase).
 - Do NOT write a "## Standards Compliance" markdown checkbox section. The YAML `standards` field replaces it.
 - Do NOT write "## Issues Found" as a markdown table. The YAML `issues` field replaces it.
 - If verdict is PASS, omit `## Detailed Findings` entirely. No filler.
diff --git a/incredible_auto_dev/.claude/agents/ux-regression-reviewer.md b/incredible_auto_dev/.claude/agents/ux-regression-reviewer.md
index 9ffc6cc..46063f7 100644
--- a/incredible_auto_dev/.claude/agents/ux-regression-reviewer.md
+++ b/incredible_auto_dev/.claude/agents/ux-regression-reviewer.md
@@ -3,8 +3,8 @@ name: ux-regression-reviewer
 description: UX regression reviewer. Checks whether the UI evolved appropriately with the phase's new capabilities. Flags features that exist in backend but are invisible or undiscoverable in the UI. Flags existing user journeys that may have regressed. Runs after browser QA and before the main auditor.
 model: claude-sonnet-5
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.0.0
-last_updated: 2026-05-04
+version: 1.1.0
+last_updated: 2026-07-28
 ---
 
 # UX Regression Reviewer
@@ -20,27 +20,34 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 3. `reports/phase-{N}-user-visible-changes.md` — what changed for users
 4. `reports/phase-{N}-ui-surface-map.md` — affected surfaces
 5. `reports/phase-{N}-ui-test-results.md` — what was tested and found
-6. Prior phase handoffs in `docs/handoffs/` — what previous phases built (check for regressions)
-7. `.claude/skills/ui-regression-scout.md` — methodology
+6. `reports/qa/<phase>-qa.md` — qa's UI Evolution Audit block (live-browser reachability evidence — cite it, don't re-derive it)
+7. In goal mode: `runs/goal-session-<sid>/iter-<N>/coherence.md` — the blueprint-grounded navigation/duplicate-home audit (read when present)
+8. Prior phase handoffs in `docs/handoffs/` — what previous phases built (check for regressions)
+9. `.claude/skills/ui-regression-scout.md` — methodology
 
 ## Process
 
-### Step 1: Check UI evolution adequacy
+### Step 1: Check UI evolution adequacy (consume, don't re-derive)
 
-For each new capability listed in `user-visible-changes.md`:
-- Is there a navigation path to reach it? (Sidebar link, button, menu item)
-- Is it reachable within 2 clicks from the home page?
-- Is its label clear to a non-technical user?
-- Is there visual feedback when the capability is used?
+<!-- SPEED-18: reachability/click-depth/duplicate-home used to be asked FOUR
+     times per full iteration. The two best-evidenced askers own them now: qa's
+     live UI Evolution Audit (browser + screenshots, gating) and the
+     coherence-auditor's blueprint-grounded Step 2. Your Step 1 CONSUMES their
+     results and judges only what neither covers. -->
 
-Flag: "hidden capability" if it exists but has no navigation path.
-Flag: "undiscoverable capability" if it requires developer knowledge to find.
-Flag: "label confusion" if the UI label doesn't match what the feature does.
+Read qa's UI Evolution Audit result (and, in goal mode, `coherence.md`). Do NOT
+re-trace navigation paths or click-depth — cite their findings. Your own Step 1
+judgment covers what neither asker sees:
+- Is each new capability's label clear to a non-technical user?
+- Is there visual feedback when the capability is used?
 - Does the new UI follow the DESIGN SYSTEM tokens (colors, spacing, typography)?
-- Is the visual style consistent with pages from prior phases?
+- Is the rendered visual style consistent with pages from prior phases?
 - Are effects (glassmorphism, glows, gradients) applied consistently, not just on some pages?
 
+Flag: "label confusion" if the UI label doesn't match what the feature does.
 Flag: "visual inconsistency" if new pages deviate from the DESIGN SYSTEM or established style.
+Flag: "audit contradiction" if qa's UI audit or coherence.md flagged a reachability
+problem the other artifacts treat as resolved — quote both sides; do not re-test.
 
 ### Step 2: Check for regression in existing journeys
 
diff --git a/incredible_auto_dev/.claude/anti-patterns/24-evidence-chasing-iterations.md b/incredible_auto_dev/.claude/anti-patterns/24-evidence-chasing-iterations.md
new file mode 100644
index 0000000..2ef8974
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/24-evidence-chasing-iterations.md
@@ -0,0 +1,9 @@
+## 24. Whole iterations spent chasing evidence for already-working features
+
+**Pattern:** The evaluator withholds a pass because the *capture artifact* is imperfect — a screenshot shows a different-but-valid data range than the spec's example numbers, or the walkthrough recording is missing — while the code, tests, and replay all confirm the behavior. The decomposer then plans an entire iteration whose only deliverable is retaking the photo or re-recording the video, and the engine runs the full developer→reviewer→browser-qa→judges pipeline around a no-op change. Worse, in lean depth the walkthrough used to be recorded in the showcase tail AFTER scoring, so a lean spec whose deliverable was "record the walkthrough" was structurally unpassable — it could only ESCALATE into an even more expensive full pass. Observed: tapeology `desk` iterations 10, 12, 13 (~6h of agent time; one screenshot, one impossible lean, one 3h full re-record) — only 1 of the last 5 iterations shipped product code.
+
+**Why it fails:** Evidence demands recurse into pipeline runs, but the pipeline's cost is sized for CODE change, not capture. Each recapture iteration produces the full artifact set (~30-40 reports) around zero product change, burying the signal a human reads; the verification chain (54% of all agent minutes in the desk session) re-verifies journeys whose code is byte-identical; and the demo-after-scoring ordering turns one cosmetic gap into an unbounded ESCALATE loop.
+
+**Prevention:** Three rails, all landed in the SPEED-9 package (2026-07-28). (1) *Evidence expires with change, not time* — methodology A.6: unchanged product code keeps prior screenshots/results/recordings valid (the engine feeds the evaluator deterministic `Prior walkthrough recording` + `Product diff this iteration` lines); goal-edit drift always outranks durability, and the no-screenshot rail still demands a citation. (2) *Capture defect ≠ product failure* — methodology A.7: score from the evidence that exists, record gap `capture-defect`, set `evidence_makeup: true`; the make-up capture rides the next iteration as a passenger or a `Depth: evidence` dispatch — NEVER as an iteration goal (decomposer rubric rule 7 enforces the planning side). (3) *The `evidence` micro-path records BEFORE scoring* — `CHAIN_LEAN_EVIDENCE_ONLY` skips developer/reviewer, runs browser capture, then demo-phase.sh, then evaluation, so an evidence gap costs ~30-40 min, not a pipeline. If you see an iteration spec whose deliverable is a screenshot or recording, the answer is `Depth: evidence` or the make-up lane — never a lean/full dispatch.
+
+---
diff --git a/incredible_auto_dev/.claude/anti-patterns/README.md b/incredible_auto_dev/.claude/anti-patterns/README.md
index 1de890c..8355558 100644
--- a/incredible_auto_dev/.claude/anti-patterns/README.md
+++ b/incredible_auto_dev/.claude/anti-patterns/README.md
@@ -31,3 +31,4 @@ row here (maintenance protocol §2).
 | 21 | [21-shared-tmp-accumulation.md](21-shared-tmp-accumulation.md) | temp files | Per-run TMPDIR isolation via chain-tmp.sh; never raw shared /tmp |
 | 22 | [22-scanner-flags-own-output.md](22-scanner-flags-own-output.md) | scan scoping | Scan the product; exclude the pipeline's own bookkeeping paths |
 | 23 | [23-prompt-argv-execve.md](23-prompt-argv-execve.md) | passing prompts to child processes | Prompt-sized content goes via stdin or file, never argv/env |
+| 24 | [24-evidence-chasing-iterations.md](24-evidence-chasing-iterations.md) | evaluator/decomposer evidence demands | Evidence expires with change, not time; capture gaps ride the make-up lane or Depth: evidence — never an iteration goal |
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
diff --git a/incredible_auto_dev/.claude/model-orchestration.md b/incredible_auto_dev/.claude/model-orchestration.md
index 0222274..5137bb5 100644
--- a/incredible_auto_dev/.claude/model-orchestration.md
+++ b/incredible_auto_dev/.claude/model-orchestration.md
@@ -22,8 +22,8 @@ from it). Update this table in the same commit that changes the tier map.
 | Tier | Claude model | Used for | Why |
 |------|--------------|----------|-----|
 | strong | `claude-opus-5` | goal-evaluator, auditor, goal-proposer, two-key confirms, escalated retries | Judgment: verdicts, scoping, skeptical audit. Mistakes here mis-certify or mis-direct whole sessions |
-| standard | `claude-sonnet-5` | goal-decomposer (TOKEN-2 experiment 2026-07-15; effort stays max, D4 guard still covers it), developer, orchestrator, product-manager, reviewer, browser-qa, coherence-auditor, all showcase agents | Building and structured review. High volume — this tier dominates token spend |
-| light | `claude-haiku-4-5` | qa (procedural mode), release-manager | Fully proceduralized tasks with exact steps and output formats |
+| standard | `claude-sonnet-5` | goal-decomposer (TOKEN-2 experiment 2026-07-15; effort stays max, D4 guard still covers it), developer, orchestrator, product-manager, reviewer, browser-qa, coherence-auditor, iteration-summarizer | Building and structured review. High volume — this tier dominates token spend. The summarizer deliberately STAYS here: REP-4 raised its concreteness bar, and it is the human's primary reading surface |
+| light | `claude-haiku-4-5` | qa (procedural mode), release-manager, demo-narrator + readme-maintainer (TOKEN-9 experiment 2026-07-28: schema-constrained writers with deterministic safety nets — demo JSON is linted/executed by demo_runner.py, README edits are marker-scoped; revert per-agent on lint failures or AUTO-block corruption) | Fully proceduralized tasks with exact steps and output formats |
 
 Effort: headless dispatches get `--effort` from `scripts/automation/lib/agent_permissions.py`
 (`EFFORT_DEFAULT=max`). At `max`: goal-evaluator, goal-decomposer, auditor, goal-proposer,
diff --git a/incredible_auto_dev/.claude/skills/browser-workflow-executor.md b/incredible_auto_dev/.claude/skills/browser-workflow-executor.md
index 1c11b2c..a8293a9 100644
--- a/incredible_auto_dev/.claude/skills/browser-workflow-executor.md
+++ b/incredible_auto_dev/.claude/skills/browser-workflow-executor.md
@@ -41,7 +41,7 @@ First click the field, then type.
   "action": "screenshot"
 }
 ```
-Take screenshots at key states: before action, after action, on error.
+Take ONE screenshot per test, at the acceptance state (the state the expected-result describes), plus one on failure.
 
 ### Get page text content
 ```json
@@ -59,7 +59,7 @@ For each test case UT-XX:
 2. Execute each step from the test plan
 3. After each action, verify the expected intermediate state
 4. At the end, verify the expected final state
-5. Take a screenshot of the final state
+5. Take ONE screenshot at the acceptance state (add one more only on failure)
 6. Record: PASS or FAIL with evidence
 
 ## Evidence Collection
@@ -67,14 +67,16 @@ For each test case UT-XX:
 Screenshots directory: `reports/qa/<phase>-evidence/`
 Create before taking screenshots: `mkdir -p reports/qa/<phase>-evidence/`
 
+One screenshot per test, taken at the acceptance state; add one more only on failure.
+
 Naming convention:
-- `UT-01-initial.png` — state before test
-- `UT-01-action.png` — during the test (after key action)
-- `UT-01-result.png` — final state
+- `UT-01-result.png` — acceptance state (one per test)
 - `UT-02-fail.png` — failure state (for FAIL tests)
 
 ## Verification Techniques
 
+Batch assertions: verify ALL of a state's expected strings in ONE `get_text` call over the relevant container — never one call per assertion.
+
 ### Verify text is present
 Get page text and check for the expected string.
 
@@ -96,7 +98,7 @@ Navigate to list page, check that item name appears in the page text.
 Wait and retry the get_text action. If still not loaded after 3 attempts, mark as SKIPPED — timeout.
 
 ### Element not found
-Try alternative selectors. If still not found, mark specific step as failed with "element not found: <description>".
+A failing selector gets at most 2 recovery attempts: one alternative locator, then one `get_text` to confirm the element truly is not rendered. If still not found, mark specific step as failed with "element not found: <description>". If a selector fails because the page genuinely changed this iteration, that is a finding — record it; the budget exists to stop exploratory wandering, not to suppress real failures.
 
 ### Console error
 Note it as WARN in test results. Only mark as FAIL if it prevents the test from completing.
diff --git a/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md b/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
index 73598aa..c4a7c81 100644
--- a/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
+++ b/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
@@ -60,6 +60,33 @@ your overall impression of the iteration.
    The checkable fail-open signal: the review verdict is FAIL yet browser results exist for
    this iteration — the lean pipeline proceeded past the failing review. That is an
    ESCALATE signal (tree below).
+6. **Evidence durability (SPEED-9).** Evidence does not expire with time — it expires with
+   CHANGE. When a journey's product code is unchanged since the iteration where its passing
+   evidence was captured, that evidence remains valid: the `last_evidence_path` screenshot,
+   its results row, AND the prior iteration's walkthrough recording (your dispatch prompt's
+   "Prior walkthrough recording" line names the newest one). Check change against
+   `iter-diff.md`'s file list vs the journey's surfaces; when the prompt's "Product diff
+   this iteration" line says EMPTY, ALL prior evidence is automatically still valid. Do not
+   demand a re-capture, and never downgrade a status for evidence age alone.
+   Two precedence rails: (a) goal-edit drift ALWAYS wins over durability — a journey listed
+   in `journeys-changed.md` needs fresh evidence against the CURRENT goal text no matter how
+   unchanged the code is (A.1 rule, unchanged); (b) the no-screenshot rail (A.3) demands a
+   screenshot EXISTS with a citation — durability only relaxes WHICH iteration it may come
+   from, never whether one is needed.
+7. **Capture defect ≠ product failure (SPEED-9).** When the code, tests, and/or replay
+   confirm the behavior but the capture ARTIFACT itself is cosmetically defective — the
+   screenshot shows a different-but-equally-valid data range than the spec's example
+   numbers, the walkthrough recording is missing or badly cropped — score the journey from
+   the code/replay/screenshot evidence that does exist, record the gap as `capture-defect`,
+   and set `evidence_makeup: true` on the journey in journey-history (same shape and
+   clearing rule as `pending_infra`: any fresh capture, pass or fail, clears it). The
+   make-up capture rides the next iteration as a passenger task or a `Depth: evidence`
+   recommendation — NEVER as a new iteration's goal.
+   Distinction: `pending_infra` = the browser infrastructure failed and evidence is OWED;
+   `evidence_makeup` = evidence exists and the product works — only the artifact's
+   presentation is wrong. Rail: this never applies when the asserted BEHAVIOR is unmet — a
+   screenshot showing wrong behavior is a failure, not a capture defect; only presentation
+   (range choice, crop, missing recording) can be defective while the behavior is confirmed.
 
 ## B. Anti-goal checklist (per category — answer each with yes/no + citation)
 
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
 
diff --git a/incredible_auto_dev/.claude/skills/plain-language.md b/incredible_auto_dev/.claude/skills/plain-language.md
index 44f749c..d3312ac 100644
--- a/incredible_auto_dev/.claude/skills/plain-language.md
+++ b/incredible_auto_dev/.claude/skills/plain-language.md
@@ -28,6 +28,8 @@ recommendations). It does not change any machine-parsed format.
    correct password", not a function, class, endpoint, or stack trace.
 6. **End with an action.** Say what happens next, or what the owner should do,
    in one sentence a non-programmer could act on.
+7. **Concrete beats generic:** name the screen and the value the user sees, not
+   "improvements were made".
 
 ## Status words (single source)
 
diff --git a/incredible_auto_dev/.claude/workflow.md b/incredible_auto_dev/.claude/workflow.md
index 429e5ed..346308b 100644
--- a/incredible_auto_dev/.claude/workflow.md
+++ b/incredible_auto_dev/.claude/workflow.md
@@ -23,7 +23,7 @@ Plan → Test Plan → Dev+Review loop → QA loop → Audit loop → Finalize
 | 7. QA | `qa-phase.sh` | qa (mode: validate) | `reports/qa/<phase>-qa.md` |
 | 8. UX Regression Review | `ux-regression-phase.sh` | ux-regression-reviewer | `reports/phase-{N}-ux-regression.md` |
 | 9. Audit | `phase-audit.sh` | auditor | `docs/handoffs/<phase>-audit.md` |
-| 10. Phase Closure | `phase-closure-check.sh` | phase-closure-auditor | `reports/phase-{N}-closure-verdict.md` |
+| 10. Phase Closure | `phase-closure-check.sh` | phase-closure-auditor (deterministic since 2026-07-28 — `closure_gate.py`; `CHAIN_CLOSURE_LLM=true` restores the agent dispatch) | `reports/phase-{N}-closure-verdict.md` |
 | 11. Finalize | `finalize-phase.sh` | release-manager | `runs/<phase>/summary.json`, PR (then updates `docs/architecture/` via `update-docs.sh`, non-blocking) |
 
 *Stages 5, 6, 8 are skipped for backend-only phases (`Frontend Present: no`) — N/A stubs are written automatically.*
@@ -64,7 +64,7 @@ Agents ONLY communicate through filesystem artifacts. No free-form messages betw
 | UI test results | `reports/phase-{N}-ui-test-results.md` | browser-qa-agent | ux-regression-reviewer, phase-closure-auditor |
 | What to click | `reports/phase-{N}-what-to-click.md` | ui-test-designer | operator (human), phase-closure-auditor |
 | UX regression report | `reports/phase-{N}-ux-regression.md` | ux-regression-reviewer | phase-closure-auditor |
-| Closure verdict | `reports/phase-{N}-closure-verdict.md` | phase-closure-auditor | finalize-phase.sh |
+| Closure verdict | `reports/phase-{N}-closure-verdict.md` | closure_gate.py (phase-closure-auditor when `CHAIN_CLOSURE_LLM=true`) | finalize-phase.sh |
 | Project goal | `docs/goal.md` | Human | orchestrator, developer, reviewer, qa |
 | Project architecture | `docs/architecture/*.md` (if present; created after the first finalized phase — absence is normal early on) | update-docs.sh | orchestrator, developer |
 | Framework architecture | `.claude/architecture/*.md` | update-docs.sh | Framework maintainers (reference) |
diff --git a/incredible_auto_dev/agents/auditor/agent.yaml b/incredible_auto_dev/agents/auditor/agent.yaml
index 3309c59..4fb7bed 100644
--- a/incredible_auto_dev/agents/auditor/agent.yaml
+++ b/incredible_auto_dev/agents/auditor/agent.yaml
@@ -3,6 +3,6 @@ description: Post-QA auditor. Reads the phase spec, all handoffs, QA report with
   and actual implementation code. Skeptically assesses whether the phase goal was truly achieved. Applies
   fixes for critical issues found. Writes audit report with PASS, PASS_WITH_GAPS, or FAIL verdict.
 model_tier: strong
-version: 1.1.1
-last_updated: '2026-07-03'
+version: 1.2.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/auditor/body.md b/incredible_auto_dev/agents/auditor/body.md
index bf31980..e0a4fcb 100644
--- a/incredible_auto_dev/agents/auditor/body.md
+++ b/incredible_auto_dev/agents/auditor/body.md
@@ -24,13 +24,35 @@ You perform a post-QA audit to determine whether the phase truly achieved its in
 
 ## Process
 
-### 1. Verify DEFINITION OF DONE
-
-For each numbered item in the spec's DEFINITION OF DONE, verify it is actually implemented:
-- Trace through the actual code, not just the handoff description
-- Check state transitions are enforced in backend logic, not just frontend
-- Verify API endpoints exist and return the right shapes
-- Verify the acceptance criteria are genuinely met, not just partially addressed
+### 1. Verify DEFINITION OF DONE (risk-ranked spot-verification)
+
+<!-- SPEED-19: the exhaustive per-item re-trace duplicated work the reviewer
+     (code-level) and QA (live functional rows) already did — a third full
+     spec-compliance pass. The full trace now goes where audit judgment adds
+     value; mechanical items already verified twice are accepted WITH CITATION. -->
+
+For each numbered item in the spec's DEFINITION OF DONE, run the FULL code trace
+(through the actual code, not the handoff description) when ANY of these holds:
+
+- **(a) Risk class** — the item involves state transitions, data mutation or
+  persistence, auth/security, or money.
+- **(b) Contradiction** — any artifact contradicts another about it (spec vs
+  dev handoff vs review report vs a QA row). The contradiction itself is the
+  trigger, even when QA is green.
+- **(c) Review doubt** — the reviewer marked `spec_alignment: partial` or filed
+  a spec-category issue touching the item.
+- **(d) Your own leads** — your Steps 2-4 work surfaced a suspicious path
+  through it.
+
+For the REMAINING mechanical items (endpoint exists, page renders, field
+displayed) that a QA functional-test row executed against the RUNNING system:
+accept the reviewer's PASS plus that QA row as verification — and CITE both
+(the review report's issue-list state and the exact QA row) next to the item in
+your report. An item with neither citation gets the full trace; so does any
+item you cannot map to a specific QA row. When tracing, still check state
+transitions are enforced in backend logic (not just frontend), API endpoints
+return the right shapes, and acceptance criteria are genuinely met — not just
+partially addressed.
 
 ### 2. Assess user workflow completeness
 
@@ -180,7 +202,7 @@ The dev handoff claimed the Stooq ingest tool was safe: "the API key is read fro
 - Do NOT pass a phase just because QA passed. QA tests what was implemented; you assess whether what was implemented is correct.
 - Do NOT mark FAIL for OBSERVATION-level issues.
 - Do NOT rewrite working implementations. Fix surgical issues only.
-- If you cannot verify a claim, read the actual code. Never trust a handoff summary alone.
+- If you cannot verify a claim, read the actual code. Never trust a handoff summary alone; for MECHANICAL DoD items only (Step 1), a reviewer PASS plus an executed QA row together are citable verification — a prose claim never is.
 
 ## Token and Questioning Policy
 
diff --git a/incredible_auto_dev/agents/browser-qa-agent/agent.yaml b/incredible_auto_dev/agents/browser-qa-agent/agent.yaml
index 58aaad9..76d8051 100644
--- a/incredible_auto_dev/agents/browser-qa-agent/agent.yaml
+++ b/incredible_auto_dev/agents/browser-qa-agent/agent.yaml
@@ -3,6 +3,6 @@ description: Browser QA agent. Executes user-visible UI tests through browser au
   MCP. Tests real workflows, not just page loads. Records pass/fail with evidence. Runs after ui-test-designer
   completes.
 model_tier: standard
-version: 1.0.2
-last_updated: '2026-07-04'
+version: 1.1.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/browser-qa-agent/body.md b/incredible_auto_dev/agents/browser-qa-agent/body.md
index 344b6a0..16dd3a9 100644
--- a/incredible_auto_dev/agents/browser-qa-agent/body.md
+++ b/incredible_auto_dev/agents/browser-qa-agent/body.md
@@ -25,14 +25,20 @@ Before running any tests:
 
 For each UT-XX test case:
 1. Read the preconditions — ensure state is correct before starting
-2. Execute each step using Chrome MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
+2. Execute the plan's steps exactly using Chrome MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
 3. After each step, verify the expected state before proceeding
 4. At the end, record: PASS or FAIL
 
+Per-test budget (hard rules):
+- Execute the plan's steps exactly — never browse pages the plan does not name.
+- A failing selector gets at most 2 recovery attempts: one alternative locator, then one `get_text` to confirm the element truly is not rendered. Then record FAIL with evidence and move to the next test. If a selector fails because the page genuinely changed this iteration, that is a finding — record it; the budget exists to stop exploratory wandering, not to suppress real failures.
+- Never debug or restart the app — that is a SKIPPED with reason, per the skill rules.
+- Never re-run a test that already passed this invocation.
+
 For PASS: note what was verified (e.g., "button 'Create Item' clicked, redirected to /items/1, 'Item saved' toast visible")
 For FAIL: note exact failure with evidence (e.g., "Form submitted but no validation message appeared, console error: TypeError at line 42")
 
-Take screenshots of key states and save to `reports/qa/<phase>-evidence/<UT-XX>-<state>.png`.
+Take ONE screenshot per test, at the acceptance state (the state the expected-result describes), plus one on failure, and save to `reports/qa/<phase>-evidence/<UT-XX>-<state>.png`.
 
 ### Step 2: Write results
 
@@ -80,7 +86,8 @@ Wait for page load after navigation and after actions that trigger page changes.
 
 Screenshots directory: `reports/qa/<phase>-evidence/`
 Create it with `mkdir -p` before taking screenshots.
-Naming: `UT-01-before.png`, `UT-01-after.png`, `UT-02-fail.png`, etc.
+ONE screenshot per test, taken at the acceptance state; add one more only on failure.
+Naming: `UT-01-result.png` (pass), `UT-02-fail.png` (failure), etc.
 
 ## Rules
 
@@ -93,6 +100,13 @@ Naming: `UT-01-before.png`, `UT-01-after.png`, `UT-02-fail.png`, etc.
 
 ## Golden replay script (goal mode only)
 
+**Golden-first setup:** before driving any journey, list
+`runs/goal-session-<sid>/journey-scripts/`. If a golden covers the journey's
+setup prefix (sign-in, seed navigation to the working surface), replay its
+exact steps verbatim instead of re-deriving selectors, and do not re-verify
+intermediate states the golden already asserts — your judgment starts where
+the plan's NEW steps start.
+
 In goal mode the dispatch wrapper gives you a **golden-script directory**
 (`runs/goal-session-<sid>/journey-scripts/`). For **every journey you verify
 PASS**, also write a self-contained deterministic replay script to
diff --git a/incredible_auto_dev/agents/demo-narrator/agent.yaml b/incredible_auto_dev/agents/demo-narrator/agent.yaml
index 72280d6..f452833 100644
--- a/incredible_auto_dev/agents/demo-narrator/agent.yaml
+++ b/incredible_auto_dev/agents/demo-narrator/agent.yaml
@@ -6,12 +6,12 @@ description: Per-iteration product demonstrator. Authors a machine-executable de
   added or changed this iteration as `[NEW]`. Showcase, not QA — a failed step is a soft note,
   never a hard pipeline fail. Modes (selected by the dispatch wrapper) - record / live (this
   iteration's working surface) and session (the whole working product across iterations).
-model_tier: standard
+model_tier: light
 tools_allowed:
 - Read
 - Glob
 - Grep
 - Write
-version: 2.1.0
-last_updated: '2026-07-26'
+version: 2.2.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-decomposer/agent.yaml b/incredible_auto_dev/agents/goal-decomposer/agent.yaml
index 4a11dae..5d865aa 100644
--- a/incredible_auto_dev/agents/goal-decomposer/agent.yaml
+++ b/incredible_auto_dev/agents/goal-decomposer/agent.yaml
@@ -1,7 +1,7 @@
 name: goal-decomposer
 description: 'Goal-mode iteration planner. Reads docs/goal.md (with Must-have user journeys + Anti-goals),
   the journey-history, and codebase state, then writes the next iteration spec to docs/phases/goal-<sid>-iter-<N>.md.
-  Picks lean or full depth. Has a baseline mode (Mode: baseline) for iteration 0 that writes a verify-only
+  Picks lean, full, or evidence depth. Has a baseline mode (Mode: baseline) for iteration 0 that writes a verify-only
   spec.'
 model_tier: standard
 tools_allowed:
@@ -10,6 +10,6 @@ tools_allowed:
 - Grep
 - Bash
 - Write
-version: 2.3.0
-last_updated: '2026-07-17'
+version: 2.4.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-decomposer/body.md b/incredible_auto_dev/agents/goal-decomposer/body.md
index 7077811..917fc65 100644
--- a/incredible_auto_dev/agents/goal-decomposer/body.md
+++ b/incredible_auto_dev/agents/goal-decomposer/body.md
@@ -17,15 +17,15 @@ The invocation prompt communicates which mode you are in via a `Mode:` line:
 
 CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
-1. `.claude/project-template.md` — project stack, architecture principles
-2. `.claude/core.md` and `.claude/workflow.md` — universal rules and pipeline semantics
+1. `.claude/project-template.md` — read ONLY the stack and architecture-principles sections: Grep for those section headers first, then Read just those sections. The rest of the file (test commands, run commands, never-commit list) is for executing agents, not for planning.
+2. Do NOT read `.claude/core.md` or `.claude/workflow.md`. Every pipeline semantic you need — depth rules, the spec format, verdict flow — is in THIS body. Consult `workflow.md` only when you need a specific section this body does not cover, and read only that section.
 3. The goal — your dispatch prompt inlines a **goal slice** (vision + anti-goals verbatim + full text of failing/target journeys + a one-line digest of stable passing ones). Use it as your primary goal source. Read the full `docs/goal.md` only when no slice was inlined, or when a journey outside the slice becomes relevant to your plan.
 4. Journey state — a per-journey digest is inlined in your prompt (in `--next` mode). Read `runs/goal-session-<sid>/state/journey-history.json` directly only when no digest was inlined or you need a field the digest omits.
 5. Iteration state — `runs/goal-session-<sid>/state/iteration-state.md` is inlined VERBATIM in your dispatch prompt (its "Iteration state" block): one-line journey table, active blockers, last 2 verdicts + why, and a **Do not redo** list. Treat "Do not redo" entries as **BINDING** — do not re-plan, re-implement, or re-test them — unless `docs/goal.md` changed for that item. An absent file (iteration 0) inlines as "(first iteration — no prior state)". Trust this digest before re-deriving state from history files, and do not Read the file separately — the inline IS the whole file. Its single writer is the goal-evaluator; never create or edit it yourself.
 6. `runs/goal-session-<sid>/state/blueprint.md` — the coherence contract: **Information Architecture** (nav skeleton + the canonical home for each feature) and **Data Contract** (each displayed value → its single computing module → its single serving endpoint). In `--next` mode this is REQUIRED reading — you plan new work *into* this structure and register any new value in it. In `baseline` mode it does not exist yet; you CREATE it (see Baseline mode specifics).
 7. `runs/goal-session-<sid>/iter-<N-1>/eval.md` — most recent evaluator verdict and recommendation (in `--next` mode)
 8. `runs/goal-session-<sid>/iter-<N-1>/coherence.md` — last coherence verdict (in `--next` mode). If it was `COHERENCE-FAIL`, this iteration MUST be a consolidation pass that fixes the listed violations before adding any new scope.
-9. Codebase state via Glob/Grep/Read — verify what already exists before proposing work
+9. Codebase state via Glob/Grep/Read — verify what already exists before proposing work. Scope this exploration to the target journeys' surfaces only; the blueprint and the iteration-state "Do not redo" list are authoritative for what already exists — never re-walk the app tree to rediscover it.
 
 **Do NOT Read** `runs/goal-session-<sid>/state/evaluator-log.md` or `runs/goal-session-<sid>/state/lessons.md`. The orchestrator script (`run-goal.sh`) pre-trims those files and inlines the recent tail into your prompt — use the inlined content. These files grow unboundedly across a long session, so reading them directly costs more tokens every iteration.
 
@@ -44,7 +44,8 @@ Write the iteration spec to `docs/phases/goal-<sid>-iter-<N>.md`. The file MUST
 - **Session ID:** <sid>
 - **Iteration:** <N>
 - **Mode:** baseline | next
-- **Depth:** lean | full
+- **Depth:** lean | full | evidence
+- **Full trigger:** <1|2|3|4> — <one-line reason>  (REQUIRED when Depth is full; omit at other depths)
 - **Target journeys:** J-01, J-03, J-07
 - **Required-still-passing journeys:** J-02, J-04
 - **Anti-goal reminders:**
@@ -127,6 +128,8 @@ separate functional test plan, so these lines are that plan's seed.
 
 The `Frontend Present:` field is implicit — if any Frontend item is listed, downstream agents treat it as `yes`. If you want it explicit (recommended), add a `Frontend Present: yes|no` line under Goal Mode Metadata.
 
+Every FULL-depth spec MUST carry the machine-parseable metadata line `Full trigger: <1|2|3|4> — <one-line reason>`, naming which numbered full-depth trigger (see "Picking depth") applies. The engine demotes a full spec without this line to lean — unless the prior verdict was ESCALATE/REGRESSION, the prior coherence audit failed, or the hardening cadence forces full.
+
 ## Picking target journeys (priority rubric — apply top-down)
 
 1. **Regressed journeys first.** Anything `regressed` outranks all new work — a shrinking product is worse than a slowly-growing one.
@@ -135,6 +138,8 @@ The `Frontend Present:` field is implicit — if any Frontend item is listed, do
 4. **Smallest spec wins ties.** Among equals, pick the journey with the smallest concrete change set — small iterations are easier to score and revert.
 5. **Never bundle two risky journeys.** One iteration may carry several trivial journeys OR one risky journey (data-model change, provider integration, cross-cutting refactor) — never two risky ones; a joint failure is undiagnosable.
 6. **Don't pick a human-blocked journey.** If the evaluator marked a blocker human-owned (STALLED-class: credentials, network access, sanction), do not re-plan the same blocked work — plan a different journey, or if none exists, write the one-line "all remaining work is human-blocked" spec so the evaluator can halt honestly.
+<!-- rule 5 is SPEED-8's territory; rule 7 (SPEED-9) composes with it -->
+7. **Never plan an evidence-only iteration.** An iteration whose ONLY deliverable is evidence capture, screenshot retakes, or demo recording is not a plan — evidence gaps ride the make-up lane instead (the `evidence_makeup` / `pending_infra` booleans in journey-history), piggybacking on whatever real iteration runs next. The one exception: when the prior evaluator's next-step asks ONLY for evidence on already-passing journeys, write the iteration as `Depth: evidence` (capture + evaluate only — the engine skips developer/reviewer).
 
 Mini example — good vs bad target selection with the same state (J-03 regressed, J-07 failing-and-unblocks-J-08/J-09, J-11 failing, big):
 - ✚ Target `J-03` alone (rule 1), depth lean, Required-still-passing = the journeys sharing J-03's contract values + smoke set. Next iter: J-07.
@@ -159,12 +164,14 @@ Mini example — good vs bad target selection with the same state (J-03 regresse
      value's computing module or serving endpoint.
   3. **Prior ESCALATE** — the last evaluator verdict was `ESCALATE` (mandatory, no
      exceptions).
-  4. **Hardening cadence** — the last `CHAIN_HARDENING_CADENCE` (default 4)
+  4. **Hardening cadence** — the last `CHAIN_HARDENING_CADENCE` (default 6)
      consecutive dispatched iterations were all lean (the engine inlines
      "Consecutive lean iterations" in your prompt; the count resets on any full).
      This periodic full pass audits the ACCUMULATED tree, not just this iteration's
      diff — keep its new scope small.
 
+- **evidence** — all Target journeys are already recorded passing and the deliverable is visual evidence only (fresh screenshots / walkthrough recording); the engine dispatches capture + evaluation only, skipping developer and reviewer. Use it only in the rule-7 exception case above — never as a substitute for real work.
+
 "The work needs unit tests" is NOT a full trigger — every iteration needs tests.
 When no trigger holds, lean is not a risk you are taking; it is the design.
 
@@ -223,7 +230,7 @@ Always restate the anti-goals from `docs/goal.md` verbatim under Goal Mode Metad
 1. **Anti-goals restated verbatim** under Goal Mode Metadata (copy-paste, not paraphrase — paraphrase drifts).
 2. **Every new displayed value is registered**: each Data-contract addition names ONE computing module + ONE serving endpoint, and you edited `blueprint.md` to match. "None" is written explicitly when true.
 3. **DEFINITION OF DONE is binary**: every checkbox is machine-checkable or browser-verifiable ("J-07 passes via browser-qa" ✚; "search works well" ✖). If you can't phrase a criterion binarily, the scope is too vague — narrow it.
-4. **Depth is justified**: full cites which numbered trigger (1-4) in BACKGROUND; lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions.
+4. **Depth is justified**: full cites which numbered trigger (1-4) in BACKGROUND AND carries the matching `Full trigger: <1|2|3|4> — <one-line reason>` metadata line (the engine demotes a full spec without it to lean); lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions.
 5. **Target selection followed the priority rubric** — if you deviated (e.g., skipped a regressed journey), the reason is stated in BACKGROUND.
 6. **Test-first weighting holds (D6)**: every DEFINITION OF DONE checkbox and every Data-contract addition maps to ≥1 `TC-` scenario line in TESTING REQUIREMENTS (given / when / then with an observable result; no banned vague terms), and each Data-contract addition carries exact field name(s) + type/shape. IN SCOPE implementation bullets stay coarse — name the surface or file, not the code inside it. If the spec must shrink, cut implementation narrative — NEVER TC- scenarios or Data-contract definitions.
 
@@ -241,6 +248,8 @@ If any check fails, fix the spec before writing it — downstream agents execute
 - **Log interpretation calls to the assumption ledger.** When a spec decision required interpreting the goal — the goal/journey text is ambiguous about X and you chose reading Y — append an entry to `runs/goal-session-<sid>/state/assumptions.md` (append-only; create it on first use; never rewrite prior entries), formatted exactly as: `## iter-<N> — goal-decomposer` on its own line, then `**Ambiguity:** <what the goal leaves open>`, `**We chose:** <the reading this iteration builds on>`, `**Reversible:** yes|no`, each on its own line. Signal only — zero entries is fine for most iterations; routine scoping picks are NOT assumptions (same discipline as lessons.md). Do not read the full ledger — the recent tail is inlined in your dispatch prompt.
 - **Conform to the blueprint, and keep it current.** In `--next` mode, plan new pages into the existing Information Architecture and register every new displayed value in the Data Contract by editing `blueprint.md` directly. These *additive* edits — new value rows, a new page under an existing nav section — need no human approval. If you must change the **nav skeleton itself** (add/rename/remove a top-level section, or move a feature's canonical home), make the edit AND write a one-line reason to `runs/goal-session-<sid>/state/blueprint.reapproval-requested`. By default `run-goal.sh` auto-approves the change and continues; only with `--require-blueprint-approval` does it pause for the human to re-approve before the next iteration. Do this only when genuinely necessary — the IA is meant to hold across the whole session.
 - **Never duplicate a contract value.** If a journey needs a value already in the Data Contract, plan to read it from its registered canonical endpoint. Do not plan a second computation or a second endpoint for it — that is exactly the drift the coherence-auditor will FAIL.
+- **Do not restate stable journeys' full `goal.md` text.** Reference journey IDs plus the acceptance delta — the goal slice in your prompt already digests them; copying their full text back into the spec is pure duplication.
+- **Do not paste blueprint content into the spec.** Reference the Information Architecture section / Data-Contract row by name. Both anti-restatement rules cut duplication ONLY — they NEVER mean shortening TC- test scenarios or interface/data-contract definitions (D6 forbids length budgets on those).
 
 ## Token and Questioning Policy
 
diff --git a/incredible_auto_dev/agents/goal-evaluator/agent.yaml b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
index 7b81606..a20bbd1 100644
--- a/incredible_auto_dev/agents/goal-evaluator/agent.yaml
+++ b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Grep
 - Bash
 - Write
-version: 1.8.0
-last_updated: '2026-07-26'
+version: 1.9.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-evaluator/body.md b/incredible_auto_dev/agents/goal-evaluator/body.md
index ae726d5..bb57fa5 100644
--- a/incredible_auto_dev/agents/goal-evaluator/body.md
+++ b/incredible_auto_dev/agents/goal-evaluator/body.md
@@ -10,20 +10,19 @@ Your methodology is `.claude/skills/goal-evaluation-methodology.md` — read it
 CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `docs/goal.md` — especially **Must-have user journeys** and **Anti-goals**
-2. `docs/phases/<iter-name>.md` — the iteration spec (target journeys, required-still-passing journeys, anti-goal reminders)
-3. `runs/<iter-name>/plan.md` — execution plan (full mode only; absent in lean iterations)
-4. `runs/<iter-name>/status.json` — execution status, changed_files, current_step
-5. `docs/handoffs/<iter-name>-dev.md` — dev handoff
-6. `docs/handoffs/<iter-name>-audit.md` — audit handoff (full mode only)
-7. `reports/reviews/<iter-name>-review.md` — review verdict
-8. `reports/qa/<iter-name>-qa.md` — QA verdict (full mode only)
-9. `reports/phase-<iter-name>-ui-test-results.md` — browser QA results (lean and full)
-10. `reports/qa/<iter-name>-evidence/` — screenshots
-11. Prior journey state — a per-journey digest is inlined in your dispatch prompt; use it for orientation. Read `runs/goal-session-<sid>/state/journey-history.json` in full only when you rewrite it in step 3 (and whenever no digest was inlined).
-12. `runs/goal-session-<sid>/iter-<N>/coherence.md` — this iteration's coherence audit (information-architecture + data-contract drift). Treat a `COHERENCE-FAIL` as a structural veto, exactly like an unresolved anti-goal violation.
-13. `runs/goal-session-<sid>/iter-<N>/scan-report.md` and `iter-diff.md` — deterministic diff scan + bounded diff, when present (see methodology skill section A for the fallback when absent).
-14. `runs/goal-session-<sid>/iter-<N>/journeys-changed.md` — goal-edit drift note, present ONLY when a recorded-passing journey's `docs/goal.md` text changed since it was last verified. Every listed journey's prior pass is void — see step 3.
-15. `.claude/skills/goal-evaluation-methodology.md` — your methodology (mandatory).
+2. `docs/phases/<iter-name>.md` — the iteration spec (target journeys, required-still-passing journeys, anti-goal reminders). The spec is authoritative for targets — do NOT also read `runs/<iter-name>/plan.md` (the orchestrator's restatement for the developer; SPEED-9 dropped it from your inputs).
+3. `runs/<iter-name>/status.json` — execution status, changed_files, current_step
+4. `docs/handoffs/<iter-name>-dev.md` — dev handoff
+5. `docs/handoffs/<iter-name>-audit.md` — audit handoff (full mode only). Read ONLY its Executive Verdict and Findings sections — its verdict already gated the pipeline; re-reading the full trace re-derives judgment that already fired.
+6. `reports/reviews/<iter-name>-review.md` — review verdict
+7. `reports/qa/<iter-name>-qa.md` — QA report (full mode only). Read ONLY the verdict line, the UI Evolution Audit block, and any FAIL rows — same already-gated rule as the audit handoff.
+8. `reports/phase-<iter-name>-ui-test-results.md` — browser QA results (lean and full)
+9. `reports/qa/<iter-name>-evidence/` — screenshots
+10. Prior journey state — a per-journey digest is inlined in your dispatch prompt; use it for orientation. Read `runs/goal-session-<sid>/state/journey-history.json` in full only when you rewrite it in step 3 (and whenever no digest was inlined).
+11. `runs/goal-session-<sid>/iter-<N>/coherence.md` — this iteration's coherence audit (information-architecture + data-contract drift). Treat a `COHERENCE-FAIL` as a structural veto, exactly like an unresolved anti-goal violation.
+12. `runs/goal-session-<sid>/iter-<N>/scan-report.md` and `iter-diff.md` — deterministic diff scan + bounded diff, when present (see methodology skill section A for the fallback when absent).
+13. `runs/goal-session-<sid>/iter-<N>/journeys-changed.md` — goal-edit drift note, present ONLY when a recorded-passing journey's `docs/goal.md` text changed since it was last verified. Every listed journey's prior pass is void — see step 3.
+14. `.claude/skills/goal-evaluation-methodology.md` — your methodology (mandatory).
 
 **Do NOT Read** `runs/goal-session-<sid>/state/evaluator-log.md`. The orchestrator script (`run-goal.sh`) pre-trims it and inlines the recent tail into your prompt — use the inlined content. The file grows unboundedly across a long session.
 
@@ -101,6 +100,16 @@ the second consecutive infra failure: stop treating it as transient — the brow
 infrastructure is a human-owned blocker (STALLED-class, decision tree C.2); never loop a
 third silent retry.
 
+**`evidence_makeup` (SPEED-9, optional boolean).** Set `"evidence_makeup": true` on a
+journey whose product behavior is confirmed but whose capture artifact is cosmetically
+defective (methodology A.7: wrong-but-valid data range in the screenshot, missing or
+mis-cropped walkthrough recording). Keep the journey's evidence-based status — this flag
+never downgrades it; it asks the next iteration to re-capture as a passenger task or via
+`Depth: evidence`, never as an iteration goal. Clear the field (omit it) the moment a
+fresh capture lands — whatever the outcome. Do not conflate with `pending_infra` above:
+that flag means the browser infrastructure OWES evidence; this one means the evidence
+exists and only its presentation is wrong.
+
 **`spec_hash` — the goal-edit drift record.** Once per evaluation, run `python3 scripts/automation/lib/goal_gate.py hash-journeys docs/goal.md` (prints `{"J-NN": "<sha256>"}`). For every journey whose status you set from THIS iteration's evidence (`passing`, `failing`, `partial`, and baseline `already_passing`), record its current hash as `spec_hash`. For journeys you did not verify this iteration, carry the existing `spec_hash` forward unchanged — or leave it absent (pre-NEED-9 histories have none; never invent one). Never copy a new hash onto a journey you did not re-verify: the hash asserts "this status was verified against exactly this goal text", and the deterministic achievement gate audits it.
 
 **When `iter-<N>/journeys-changed.md` exists:** each listed journey's goal.md text changed AFTER its recorded pass, so that pass is void. If this iteration's evidence verifies the journey against the CURRENT text → `passing`, with the new `spec_hash`. Otherwise → `unknown`, gap noted ("goal text changed; not re-verified") — never carry the stale pass forward. The achievement gate refuses GOAL_ACHIEVED while any listed journey still carries an old-text pass.
@@ -114,7 +123,7 @@ Append a new entry to `runs/goal-session-<sid>/state/evaluator-log.md`:
 
 **Date:** <ISO timestamp>
 **Verdict:** <VERDICT>
-**Depth dispatched:** lean | full
+**Depth dispatched:** lean | full | evidence
 **Journey deltas:**
 - Newly passing: J-XX, J-YY
 - Newly failing: <none or list>
@@ -169,7 +178,7 @@ Write to `runs/goal-session-<sid>/iter-<N>/eval.md`:
 # Iteration <N> Evaluation
 
 **Verdict:** <VERDICT>
-**Depth Recommendation For Next Iteration:** lean | full
+**Depth Recommendation For Next Iteration:** lean | full | evidence
 
 ## Summary
 
@@ -236,7 +245,7 @@ or `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`.
 
 - **GOAL_ACHIEVED** — every Must-have journey has status `passing` or `already_passing`, no critical anti-goal violations exist, this iteration's `coherence.md` is not `COHERENCE-FAIL`, AND no journey listed in `journeys-changed.md` remains un-re-verified against the current goal text. Loop halts with success.
 
-- **CONTINUE** — progress was made (≥1 journey newly passing) OR no progress this iter but failing journeys remain that are tractable. Recommend the next iteration's depth and target. Loop continues. **If this iteration's `coherence.md` is `COHERENCE-FAIL`, return `CONTINUE`** and make the next-step recommendation a *consolidation pass* that fixes the listed coherence violations (cite them verbatim) before any new feature work — even if every journey passed.
+- **CONTINUE** — progress was made (≥1 journey newly passing) OR no progress this iter but failing journeys remain that are tractable. Recommend the next iteration's depth and target. Recommend `evidence` depth when EVERY remaining gap is a capture/recording task on already-working features (`evidence_makeup`/`capture-defect` gaps) — the engine then runs capture + evaluation only, no developer/reviewer. Loop continues. **If this iteration's `coherence.md` is `COHERENCE-FAIL`, return `CONTINUE`** and make the next-step recommendation a *consolidation pass* that fixes the listed coherence violations (cite them verbatim) before any new feature work — even if every journey passed.
 
 - **ESCALATE** — a lean iteration uncovered ambiguity, complexity, or an issue that warrants the full pipeline (audit, ux-regression, closure). The next iteration MUST run as `full`. Use sparingly — escalating every iter defeats the purpose of adaptive depth.
 
@@ -263,6 +272,7 @@ or `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`.
 - Update `journey-history.json` atomically — write the full new state, do not partial-update.
 - Append to `evaluator-log.md` — never overwrite prior entries; this is the chronological record.
 - If you cannot find evidence for a journey (e.g., browser-qa-agent skipped it), set its status to `unknown` and note the gap in the evaluation. Do NOT guess.
+- Never recommend — and never score as blocking — a next iteration whose only content is evidence capture, screenshot retakes, or demo recording. Evidence gaps on working features ride the make-up lane (`evidence_makeup`, methodology A.7) or a `Depth: evidence` recommendation; prior evidence for unchanged code stays valid (methodology A.6). Goal-edit drift (`journeys-changed.md`) always outranks evidence durability.
 
 ## Token and Questioning Policy
 
diff --git a/incredible_auto_dev/agents/iteration-summarizer/agent.yaml b/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
index f75428e..0a338bf 100644
--- a/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
+++ b/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
@@ -8,6 +8,6 @@ model_tier: standard
 tools_allowed:
 - Read
 - Write
-version: 1.2.0
-last_updated: '2026-07-26'
+version: 1.3.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/iteration-summarizer/body.md b/incredible_auto_dev/agents/iteration-summarizer/body.md
index b242f26..2aaeb76 100644
--- a/incredible_auto_dev/agents/iteration-summarizer/body.md
+++ b/incredible_auto_dev/agents/iteration-summarizer/body.md
@@ -95,14 +95,14 @@ Write exactly this skeleton — keep the labels and the order:
 ```
 ## In plain words
 
-**What you can do now:** <Plain-language list of capabilities the product delivers to a user today. In goal mode, aggregate every currently-passing journey. In phase mode, describe the cumulative end-user surface so far. Frame as actions ("Sign in with email", "Save a draft and come back to it"). Comma-separated or 2-4 short sentences, not bullets.>
+**What you can do now:** <Plain-language list of capabilities the product delivers to a user today. In goal mode, re-derive this EVERY iteration from the `name` fields of the currently-passing journeys in `journey-history.json` — never copy the previous summary's sentence verbatim, and any journey whose status changed this iteration must appear or disappear from the list accordingly. In phase mode, describe the cumulative end-user surface so far. Frame as actions ("Sign in with email", "Save a draft and come back to it"). Comma-separated or 2-4 short sentences, not bullets.>
 
-**What changed this time:** <Plain-language description of what is newly available or fixed this iteration. Tie back to user experience ("You can now invite a teammate by email"). If nothing user-facing changed, write: "Behind-the-scenes work — nothing visibly new this round" and name the area in friendly terms (e.g. "made the app faster", "tightened security").>
+**What changed this time:** <MUST name the concrete user-visible change: the screen or page by its visible name and what the user now sees or does there ("The Watchlist page now has an 'Export CSV' button that downloads your list."). Never open with a generic sentence like "improvements were made". The sentence "Behind-the-scenes work — nothing visibly new this round" is permitted ONLY when the iteration changed zero product source files — check `status.json` `changed_files` and the dev handoff's Files Changed list before using it — and even then it must name the concrete area that was worked on ("sped up the price-history loading code", "captured fresh proof screenshots of the Desk screen").>
 
 **What's next:** <Plain-language version of the Next step. Phrase as the next thing the product will gain ("Next we'll let you reset a forgotten password"). One short sentence.>
 ```
 
-**Backend-only iteration** (no `user-visible-changes.md`, or it says "N/A — Backend-only phase"): write "Behind-the-scenes work — nothing visibly new this round." in **What changed this time**, keep the cumulative "What you can do now" unchanged from the prior iteration's plain-words block if you can read it (look at `reports/phase-<prev-phase-id>-iteration-summary.md` if obvious from context; otherwise describe the latest known capabilities or write "Same as before — no user-facing change.").
+**Backend-only iteration** (no `user-visible-changes.md`, or it says "N/A — Backend-only phase"): first check `status.json` `changed_files` and the dev handoff's Files Changed list. If product source files DID change, do NOT use the generic behind-the-scenes sentence — say in friendly words what part of the product the work touched and what it does now ("the price history behind the Desk screen now loads faster"). Only if zero product source files changed may **What changed this time** read "Behind-the-scenes work — nothing visibly new this round" — and it must still name the concrete area worked on ("captured fresh proof screenshots of the Desk screen"). For **What you can do now**, re-derive the list from the passing-journey names in `journey-history.json` EVERY iteration (phase mode: from the cumulative artifacts) — never copy the previous summary's sentence verbatim; a journey whose status changed this iteration must appear or disappear accordingly.
 
 **First iteration of a goal session** (no prior summaries, journey-history may be empty or have only `unknown` statuses): write "Just getting started — nothing for users to try yet." in **What you can do now**, and describe groundwork in **What changed this time**.
 
@@ -138,7 +138,12 @@ Numbers come from counting deltas in the evaluator-log entries. Do not invent jo
 
 ## What was done
 
-3–8 bullets, terse, action-oriented. Sources:
+The FIRST bullet is fixed-format. It MUST be one of these two — nothing else may be first:
+
+- `Product changes: <comma-separated changed product files and/or routes>` — sourced from `status.json` `changed_files` and the dev handoff's Files Changed list (e.g. `Product changes: apps/frontend/app/desk/page.tsx, /api/desk/topup`)
+- exactly `No product change this iteration.` — when neither source lists a changed product file
+
+Then 3–8 further bullets, terse, action-oriented. Sources:
 
 - `implementation-summary.md` "Features Implemented" if present (highest fidelity)
 - else `dev-handoff.md` "Summary" + a synthesized 1-bullet-per-major-file-or-area from "Files Changed"
diff --git a/incredible_auto_dev/agents/readme-maintainer/agent.yaml b/incredible_auto_dev/agents/readme-maintainer/agent.yaml
index 57d070f..b70b9c3 100644
--- a/incredible_auto_dev/agents/readme-maintainer/agent.yaml
+++ b/incredible_auto_dev/agents/readme-maintainer/agent.yaml
@@ -3,13 +3,13 @@ description: Project README maintainer (goal mode). After each iteration, refres
   so it reflects the current capabilities of the whole project and carries an accurate "How to run" section.
   Edits only marker-delimited AUTO blocks so hand-written prose is preserved, and grounds every install/run/test
   command in .claude/project-template.md. Non-blocking showcase/maintenance step — never gates the pipeline.
-model_tier: standard
+model_tier: light
 tools_allowed:
 - Read
 - Write
 - Edit
 - Glob
 - Grep
-version: 1.1.0
-last_updated: '2026-07-26'
+version: 1.2.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/reviewer/agent.yaml b/incredible_auto_dev/agents/reviewer/agent.yaml
index f4c23ab..82128db 100644
--- a/incredible_auto_dev/agents/reviewer/agent.yaml
+++ b/incredible_auto_dev/agents/reviewer/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Bash
 - Write
 - Edit
-version: 1.2.1
-last_updated: '2026-07-16'
+version: 1.3.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/reviewer/body.md b/incredible_auto_dev/agents/reviewer/body.md
index 3fabff6..c78644f 100644
--- a/incredible_auto_dev/agents/reviewer/body.md
+++ b/incredible_auto_dev/agents/reviewer/body.md
@@ -70,9 +70,12 @@ For each changed file, verify:
 - [ ] No refactoring of code outside the task scope
 
 ### UI quality (if frontend was changed)
-- [ ] UI evolved to reflect the new backend capability (per workflow.md UI EVOLUTION POLICY)
-- [ ] New entity types have list + detail pages reachable from navigation
-- [ ] Sidebar updated if a new top-level workflow was introduced
+<!-- SPEED-18: the UI-EVOLUTION/reachability questions (did the UI evolve, are new
+     entities reachable, was the sidebar updated) are owned by qa's live UI
+     Evolution Audit (browser + screenshot evidence, gating) and the
+     coherence-auditor's blueprint-grounded Step 2 — a code reviewer answers
+     them by guessing at runtime behavior. This checklist keeps only what CODE
+     review can actually verify. -->
 - [ ] Frontend does not contain business logic (calls backend APIs only)
 - [ ] Uses component library from DESIGN SYSTEM — no raw HTML where components exist
 - [ ] Colors, spacing, and typography use token values from DESIGN SYSTEM — no arbitrary values
@@ -129,8 +132,6 @@ standards:
   test_quality: pass
   no_dead_code: pass
   no_hardcoded_localhost: pass
-  ui_evolved_with_capability: pass
-  navigation_updated: n/a
   architecture_principles: pass
 ```
 ````
@@ -166,8 +167,6 @@ standards:
   test_quality: pass | fail | n/a
   no_dead_code: pass | fail | n/a
   no_hardcoded_localhost: pass | fail | n/a
-  ui_evolved_with_capability: pass | fail | n/a
-  navigation_updated: pass | fail | n/a
   architecture_principles: pass | fail | n/a
 fix_tasks:                            # ONLY when verdict == FAIL
   - file: path/to/file.py
@@ -186,7 +185,7 @@ Per-file, max 80 words each. Skip files with no issues. No headers below H3.
 - The verdict line is required and parsed by scripts. Keep the exact `**Verdict:** ...` format.
 - `issues` must be a YAML list. Use `[]` if empty.
 - Every CRITICAL or MINOR issue must have `file`, `line`, and `fix`.
-- Use `n/a` (not `pass`) for `standards` keys that don't apply (e.g. `ui_evolved_with_capability` on a backend-only phase).
+- Use `n/a` (not `pass`) for `standards` keys that don't apply (e.g. `test_quality` on a docs-only phase).
 - Do NOT write a "## Standards Compliance" markdown checkbox section. The YAML `standards` field replaces it.
 - Do NOT write "## Issues Found" as a markdown table. The YAML `issues` field replaces it.
 - If verdict is PASS, omit `## Detailed Findings` entirely. No filler.
diff --git a/incredible_auto_dev/agents/ux-regression-reviewer/agent.yaml b/incredible_auto_dev/agents/ux-regression-reviewer/agent.yaml
index c0bb288..a598742 100644
--- a/incredible_auto_dev/agents/ux-regression-reviewer/agent.yaml
+++ b/incredible_auto_dev/agents/ux-regression-reviewer/agent.yaml
@@ -3,6 +3,6 @@ description: UX regression reviewer. Checks whether the UI evolved appropriately
   capabilities. Flags features that exist in backend but are invisible or undiscoverable in the UI. Flags
   existing user journeys that may have regressed. Runs after browser QA and before the main auditor.
 model_tier: standard
-version: 1.0.0
-last_updated: '2026-05-04'
+version: 1.1.0
+last_updated: '2026-07-28'
 body: body.md
diff --git a/incredible_auto_dev/agents/ux-regression-reviewer/body.md b/incredible_auto_dev/agents/ux-regression-reviewer/body.md
index 555f6e3..63789f8 100644
--- a/incredible_auto_dev/agents/ux-regression-reviewer/body.md
+++ b/incredible_auto_dev/agents/ux-regression-reviewer/body.md
@@ -12,27 +12,34 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 3. `reports/phase-{N}-user-visible-changes.md` — what changed for users
 4. `reports/phase-{N}-ui-surface-map.md` — affected surfaces
 5. `reports/phase-{N}-ui-test-results.md` — what was tested and found
-6. Prior phase handoffs in `docs/handoffs/` — what previous phases built (check for regressions)
-7. `.claude/skills/ui-regression-scout.md` — methodology
+6. `reports/qa/<phase>-qa.md` — qa's UI Evolution Audit block (live-browser reachability evidence — cite it, don't re-derive it)
+7. In goal mode: `runs/goal-session-<sid>/iter-<N>/coherence.md` — the blueprint-grounded navigation/duplicate-home audit (read when present)
+8. Prior phase handoffs in `docs/handoffs/` — what previous phases built (check for regressions)
+9. `.claude/skills/ui-regression-scout.md` — methodology
 
 ## Process
 
-### Step 1: Check UI evolution adequacy
+### Step 1: Check UI evolution adequacy (consume, don't re-derive)
 
-For each new capability listed in `user-visible-changes.md`:
-- Is there a navigation path to reach it? (Sidebar link, button, menu item)
-- Is it reachable within 2 clicks from the home page?
-- Is its label clear to a non-technical user?
-- Is there visual feedback when the capability is used?
+<!-- SPEED-18: reachability/click-depth/duplicate-home used to be asked FOUR
+     times per full iteration. The two best-evidenced askers own them now: qa's
+     live UI Evolution Audit (browser + screenshots, gating) and the
+     coherence-auditor's blueprint-grounded Step 2. Your Step 1 CONSUMES their
+     results and judges only what neither covers. -->
 
-Flag: "hidden capability" if it exists but has no navigation path.
-Flag: "undiscoverable capability" if it requires developer knowledge to find.
-Flag: "label confusion" if the UI label doesn't match what the feature does.
+Read qa's UI Evolution Audit result (and, in goal mode, `coherence.md`). Do NOT
+re-trace navigation paths or click-depth — cite their findings. Your own Step 1
+judgment covers what neither asker sees:
+- Is each new capability's label clear to a non-technical user?
+- Is there visual feedback when the capability is used?
 - Does the new UI follow the DESIGN SYSTEM tokens (colors, spacing, typography)?
-- Is the visual style consistent with pages from prior phases?
+- Is the rendered visual style consistent with pages from prior phases?
 - Are effects (glassmorphism, glows, gradients) applied consistently, not just on some pages?
 
+Flag: "label confusion" if the UI label doesn't match what the feature does.
 Flag: "visual inconsistency" if new pages deviate from the DESIGN SYSTEM or established style.
+Flag: "audit contradiction" if qa's UI audit or coherence.md flagged a reachability
+problem the other artifacts treat as resolved — quote both sides; do not re-test.
 
 ### Step 2: Check for regression in existing journeys
 
diff --git a/incredible_auto_dev/benchmarks/experiments.md b/incredible_auto_dev/benchmarks/experiments.md
index 9c379a1..9dbb672 100644
--- a/incredible_auto_dev/benchmarks/experiments.md
+++ b/incredible_auto_dev/benchmarks/experiments.md
@@ -937,3 +937,10 @@ Entry format contract (grep-able; pinned by
   framework-gap candidate as run E flagged: the forked/scripted browser-qa
   Chrome outlives the engine. Kept scratch:
   /home/dennis-chan/.cache/iad/shared/bench-bench-20260716-1436.dNHg0w
+
+## PRE speed-package-20260728 · 2026-07-28T15:30:00Z
+- framework-sha: e619138 (+ the SPEED-12/15/17/18/19/TOKEN-9 commits landing the same day; dirty during authoring)
+- fixture: next REAL tapeology goal session (or an EVO-3 benchmark rerun) vs the desk-session baseline recorded below
+- hypothesis: the SPEED-9..19 + REP-4 + TOKEN-9 package cuts typical goal-mode iteration wall time under 60 min without journey-quality regressions. Baseline (desk, 15 iters): ~153 agent-min/iter; verification = 54% of agent minutes; full depth 4 of last 6 iters; browser-qa >100 turns/invocation; 3 of last 5 iterations were evidence-only waste (~6h); zero quota-pause events recorded (attribution bug).
+- metrics + prediction (manual grading): median wall for lean/evidence/zero-change iterations < 60m; evidence-class gaps resolved in < 45m via the evidence micro-path (no developer dispatch); full-depth ratio <= 1 in 6; browser-qa <= 60 turns/invocation; demo-narrator+readme token cost ~1/3 of sonnet baseline; NO journey regressions or golden verdict-class flips attributable to the package; summaries name concrete files/screens (grep for 'Product changes:' rows).
+- note: pre-registered manually (G8) — the package is engine+contract work, not a run-benchmark.sh invocation; grade against the next session's telemetry with analyze_telemetry.py --wall.
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
diff --git a/incredible_auto_dev/docs/goal-mode-interactive.md b/incredible_auto_dev/docs/goal-mode-interactive.md
index 4d5d0c4..2456502 100644
--- a/incredible_auto_dev/docs/goal-mode-interactive.md
+++ b/incredible_auto_dev/docs/goal-mode-interactive.md
@@ -178,6 +178,8 @@ programmatic path with an API key** (`run-goal.sh` without `--interactive`).
 |---|---|---|
 | `CHAIN_PUMP_HEARTBEAT_TIMEOUT` | `1800` | PICKUP window only: seconds a *not-yet-claimed* request waits for the pump to take it before concluding the pump died. An alive idle pump refreshes the heartbeat every poll, so this no longer needs to cover a long agent's runtime — a claimed agent is governed by the inflight cap below. (Also how long an untouched orphan engine waits before self-aborting.) |
 | `CHAIN_DISPATCH_INFLIGHT_TIMEOUT` | `7200` (= `CHAIN_CLAUDE_MAX_RUNTIME_SECONDS`) | Hard cap on a single **claimed**, in-flight subagent, measured from when the pump took the request (`dispatch/req.*.started`). This is what lets a legitimately long agent — e.g. the developer's INITIAL BUILD, routinely > 30 min — run without being mistaken for a dead pump. `0` = unlimited. |
+| `CHAIN_DISPATCH_PICKUP_BUSY_TIMEOUT` | `= CHAIN_DISPATCH_INFLIGHT_TIMEOUT` (`7200`) | SPEED-12: bound on an **unclaimed** request's wait while the pump is alive but busy on another request. Before this, that wait was unbounded — one stale sibling claim from a dead pump could block the engine for 18 h. Provably-dead sibling claims are also cleared on the spot, and an iteration-boundary janitor sweeps stale claims. `0` = unlimited (old behavior). |
+| `CHAIN_DISPATCH_LANE` | `5` | SPEED-12 priority lane digit in the request filename (`req.<lane>-XXXXXX`). The pump serves the sorted glob, so lower lanes are picked up first; the background showcase tail dispatches on lane `9` so next-iteration spine work never queues behind it. |
 | `CHAIN_DISPATCH_POLL_SECONDS` | `1` | Channel poll interval. |
 
 The pump awaits work with a **single foreground** `goal-await-dispatch.sh
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
 
diff --git a/incredible_auto_dev/docs/goal-mode-telemetry.md b/incredible_auto_dev/docs/goal-mode-telemetry.md
index a7c26a1..38baf70 100644
--- a/incredible_auto_dev/docs/goal-mode-telemetry.md
+++ b/incredible_auto_dev/docs/goal-mode-telemetry.md
@@ -74,7 +74,9 @@ Wrap each agent call inside an iteration (developer, reviewer, browser-qa-agent,
 |---|---|---|
 | `agent` | string | Agent name |
 | `exit_status` | number | (end only) Process exit code |
-| `duration_seconds` | number | (end only) Wall time |
+| `duration_seconds` | number | (end only) Wall time, INCLUDING any quota-pause sleep |
+| `quota_sleep_seconds` | number | (end only) Seconds of that wall time spent in quota-pause sleeps (SPEED-13) |
+| `active_seconds` | number | (end only) `duration_seconds − quota_sleep_seconds` — the honest work time (SPEED-13) |
 | `retries` | number | (end only) Quota-retry count for this invocation |
 
 ### `quota_pause_start`, `quota_pause_end`
@@ -83,9 +85,13 @@ Recorded around quota-exhaustion sleeps inside `claude_with_quota_retry`.
 | Field | Type | Description |
 |---|---|---|
 | `agent` | string | Agent that triggered the pause |
+| `reset_epoch` | number | (start only) Epoch the sleep targets |
 | `sleep_seconds` | number | (end only) Total seconds slept |
 
-> Note: The quota-pause events are recorded by goal-mode wrapper logic in `run-goal.sh` and `goal-iter-lean.sh`, not by `lib/quota-retry.sh` directly (so phase mode is unaffected). The wrapper observes the script's exit/retry behavior and emits these events when the wrapper detects a quota-retry path was taken.
+> Note: These events are emitted directly by `lib/quota-retry.sh` at its sleep
+> sites (both claude and codex paths; SPEED-13). They no-op outside goal mode —
+> `record_telemetry_event` is disabled when no goal session is active. The same
+> path increments the session's `.quota-pause-count` file.
 
 ### `evaluator_start`, `evaluator_end`
 Wrap the goal-evaluator agent invocation.
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
 
diff --git a/incredible_auto_dev/docs/improvement-roadmap.md b/incredible_auto_dev/docs/improvement-roadmap.md
index 0e583ad..bf3cd80 100644
--- a/incredible_auto_dev/docs/improvement-roadmap.md
+++ b/incredible_auto_dev/docs/improvement-roadmap.md
@@ -140,6 +140,21 @@ signal that says "do this now").
 10. **PLAIN-1** — plain-language output (§19, promoted 2026-07-26 by direct user
     request; absorbs DOC-5). Shipped 2026-07-26 in one bundled session; judgment
     spot-run green; certified DONE per G8 same day.
+11. **SPEED-9…19 + REP-4 + TOKEN-9** — the iteration-speed package (promoted
+    2026-07-28 by direct user request after the tapeology desk-session diagnosis;
+    EVO-1 promotion + G6 multi-item exception, all three judge cuts and the
+    ask-first flips explicitly approved). Implemented 2026-07-28 in one bundled
+    session; judgment spot-run GREEN 2026-07-29 — 14/14 verdict classes
+    (auditor 4/4 incl. case-03 contradiction-still-FAILs, goal-evaluator 6/6
+    incl. case-04 drift-beats-durability and case-06 make-up-boolean
+    distinction, reviewer 4/4 with the SPEED-18 key removals). Still owed
+    before any item flips to DONE: G8 fresh-session certification and one real
+    session's before/after telemetry (PRE speed-package-20260728 in
+    benchmarks/experiments.md). SPEED-15 slice (b) (trim-mode browser
+    narrowing) stays TODO until a warn-mode session exists.
+    *G8 fresh-session certification 2026-07-29 (non-implementer): steps 1-5
+    verified green; items remain IN-PROGRESS pending the real-session
+    telemetry (PRE speed-package-20260728).*
 
 ---
 
@@ -1083,6 +1098,234 @@ benchmark (or a real session's telemetry) before AND after (G8).
 - **Depends on:** SPEED-4 (the sharpened rubric defines what "trivial" means in
   practice); synergizes with §16 CAND-TIER (same complexity vocabulary).
 
+<!-- ═══ SPEED-9…19 · the 2026-07-28 iteration-speed package (user-approved
+     promotion per EVO-1 + G6 multi-item exception, same mechanism as
+     SPEED-4..7 / CTX / PLAIN-1). Diagnosis basis: tapeology desk session
+     telemetry — 15 iterations, ~153 agent-min each; verification = 54% of all
+     agent minutes; of iters 10-14 only ONE shipped product code (the rest
+     chased screenshots/recordings); iter-7 blocked 18.3h on a dead pump's
+     claim; full depth ran 4 of the last 6 iterations. Target: typical
+     iterations < 60 min without giving up the judge chain's quality. ═══ -->
+
+### SPEED-9 · Evidence fast path — `evidence` depth + evaluator evidence durability
+- **Priority:** P0 · **Effort:** L (a: engine micro-path; b: evaluator contract;
+  c: decomposer rules) · **Risk:** MED · **Status:** IN-PROGRESS — implemented
+  2026-07-28 (commits 58b93be, 8bd513f, dc86b53); G8 fresh-session certification
+  + one real-session before/after pending.
+- **Problem:** 3 of the desk session's last 5 iterations (~6h) ran full/lean
+  pipelines solely to retake a screenshot or record a walkthrough for features
+  already verified working; lean specs whose deliverable was the walkthrough were
+  structurally unpassable (recording happened AFTER scoring — iter-12 ESCALATE).
+- **Change spec (landed):** (a) third depth token `evidence`
+  (`CHAIN_EVIDENCE_MICRO_PATH`, default on): goal-iter-lean.sh skips
+  developer/reviewer with honest stubs, runs browser-qa unchanged, and records
+  the demo BEFORE returning; engine backstop demotes lean→evidence when every
+  target journey is already recorded passing (telemetry
+  `depth_evidence_override`); evaluator prompt gains deterministic
+  `Prior walkthrough recording` + `Product diff this iteration` lines
+  (judgment-eval mirror updated byte-for-byte). (b) methodology A.6 (evidence
+  expires with CHANGE, not time; goal-edit drift always outranks durability;
+  the no-screenshot rail keeps demanding a citation) + A.7 (`capture-defect`
+  gap, `evidence_makeup` journey-history boolean mirroring `pending_infra`);
+  read-list diet (plan.md dropped; audit/QA reports scoped to verdict blocks).
+  (c) decomposer rubric rule 7: never plan an evidence-only iteration;
+  anti-restatement rules (D6-safe); read-list diet.
+- **DoD:** tests green (`test-evidence-depth.sh` 16 cases); judgment goldens
+  6/6 evaluator cases on the configured model; one real session shows an
+  evidence-class gap resolved in an `evidence` dispatch < 45 min.
+- **Verify:** `bash tests/automation/test-evidence-depth.sh` ·
+  `./scripts/automation/run-evals.sh` · judgment spot-run (G9).
+- **Files:** `scripts/automation/run-goal.sh`, `goal-iter-lean.sh`,
+  `lib/common.sh`, `run-judgment-evals.sh`, `agents/goal-evaluator/*`,
+  `agents/goal-decomposer/*`, `skills/goal-evaluation-methodology.md`, mirrors.
+- **Rollback:** `CHAIN_EVIDENCE_MICRO_PATH=false` (engine); body reverts + version.
+- **Stop-and-ask:** any evaluator golden verdict-class flip (drift-beats-durability
+  case-04 above all); a demo-less project needing more than the SKIPPED-stub path.
+
+### SPEED-10 · Depth discipline — full-trigger allowlist + cadence 4→6
+- **Priority:** P0 · **Effort:** M · **Risk:** LOW-MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-28 (58b93be); G8 certification pending.
+- **Problem:** full depth (~90-120 min over lean) ran on 4 of the desk session's
+  last 6 iterations; at most 2 were justified (one full pass existed to re-record
+  a video).
+- **Change spec (landed):** engine allowlist (`CHAIN_DEPTH_ALLOWLIST`, default
+  on): a full spec stays full only on prior ESCALATE/REGRESSION, prior-iteration
+  COHERENCE-FAIL, a machine-parseable `Full trigger: <1|2|3|4> — reason` line
+  (decomposer contract, dc86b53), or cadence-due; otherwise demoted with
+  `depth_demoted` telemetry. `CHAIN_HARDENING_CADENCE` default 4→6 (evidence
+  dispatches continue the streak).
+- **DoD:** `test-depth-cadence.sh` 23 cases green; first real session shows
+  full-ratio ≤ 1-in-6 with no ESCALATE caused by a demoted full.
+- **Verify:** `bash tests/automation/test-depth-cadence.sh` · run-evals.
+- **Files:** `scripts/automation/run-goal.sh`, `lib/common.sh`,
+  `agents/goal-decomposer/body.md`, tests.
+- **Rollback:** `CHAIN_DEPTH_ALLOWLIST=false`; `CHAIN_HARDENING_CADENCE=4`.
+- **Stop-and-ask:** a demoted-full iteration producing an ESCALATE in the first
+  real session — report before tuning anything.
+
+### SPEED-11 · Lean replay-fork default flip (off→replay)
+- **Priority:** P1 · **Effort:** S · **Risk:** LOW-MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-28 (58b93be); G8 certification pending.
+- **Change spec (landed):** `CHAIN_LEAN_PARALLEL_BROWSER_QA` default off→replay
+  (SPEED-2's fork: built, benchmarked, tripwired — 2-of-3 attempt-1 review FAILs
+  auto-disable per session). Test scenarios pin `off` explicitly now. Recorded
+  decisions: CAND-FULL-BQA-OVERLAP stays staged (post-SPEED-10 fulls too rare to
+  justify the port); decomposer-N+1 ∥ evaluator-N overlap REJECTED (the
+  decomposer consumes evaluator outputs).
+- **Verify:** `bash tests/automation/test-goal-parallel-bqa.sh` (92 cases).
+- **Rollback:** `CHAIN_LEAN_PARALLEL_BROWSER_QA=off`.
+- **Stop-and-ask:** tripwire firing immediately in the first post-flip session.
+
+### SPEED-12 · Dispatch/timeout hardening — busy cap, claim janitor, lanes, timeout table
+- **Priority:** P1 · **Effort:** M · **Risk:** LOW-MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-28; G8 certification pending.
+- **Problem:** iter-7 blocked 18h19m on an UNCLAIMED request while a dead pump's
+  stale sibling `.started` kept the Tier-A wait unbounded
+  (`lib/interactive-dispatch.sh` busy branch); 8 agents fell to the flat 7200s
+  cap; showcase dispatches queued ahead of spine work.
+- **Change spec (landed):** `_dispatch_claim_pump_dead` helper — provably-dead
+  sibling claims cleared on the spot; `CHAIN_DISPATCH_PICKUP_BUSY_TIMEOUT`
+  (default = flat inflight cap, 0=old unlimited) bounds the genuine-busy
+  unclaimed wait resumably (`pickup-busy-timeout` event);
+  `dispatch_channel_janitor` at the iteration boundary; per-agent timeout table
+  filled for the full-pipeline chain (each ≥2.5× observed desk maxima);
+  priority lanes — `req.<lane>-XXXXXX` filenames (`CHAIN_DISPATCH_LANE`,
+  default 5; showcase tail exports 9) ride the pump's sorted glob with zero
+  pump-side changes.
+- **Verify:** `bash scripts/automation/lib/interactive-dispatch.sh --self-test`
+  (23 cases incl. 4 new) · `goal-await-dispatch.sh --self-test` ·
+  `python3 scripts/automation/lib/agent_permissions.py self-test`.
+- **Files:** `lib/interactive-dispatch.sh`, `lib/agent_permissions.py`,
+  `run-goal.sh`, `docs/goal-mode-interactive.md`.
+- **Rollback:** `CHAIN_DISPATCH_PICKUP_BUSY_TIMEOUT=0`; unset
+  `CHAIN_DISPATCH_LANE` semantics revert by deleting the two call-site exports;
+  table rows are per-agent deletes.
+- **Stop-and-ask:** a pickup-busy-timeout pause on a HEALTHY long dispatch in a
+  real session (cap mis-sized) — report before raising it.
+
+### SPEED-13 · Telemetry honesty — quota pauses, active vs wall, full-pipeline attribution
+- **Priority:** P1 · **Effort:** M · **Risk:** LOW · **Status:** IN-PROGRESS —
+  implemented 2026-07-28 (adf5f22); G8 certification pending.
+- **Problem:** quota_pause_start/end documented + consumed but never emitted;
+  `.quota-pause-count` had no increment site; quota sleeps inflated agent
+  durations (the "18.7h evaluator"); full-depth iterations emitted zero
+  per-agent events and rendered as 130-190m "unattributed (glue)".
+- **Change spec (landed):** both events + counter bump at all four sleep sites in
+  `lib/quota-retry.sh`; `agent_invocation_end` gains additive
+  `quota_sleep_seconds`/`active_seconds`; all 16 phase-script dispatch sites
+  wrap with `record_agent_invocation_start/end`; analyzer consumes `engine_step`
+  events, prefers active seconds, renders an honest residual.
+- **Verify:** `bash scripts/automation/lib/telemetry.sh test` ·
+  `python3 scripts/automation/lib/analyze_telemetry.py --self-test`.
+- **Rollback:** revert (additive fields; no behavior change).
+- **Stop-and-ask:** none (measurement only).
+
+### SPEED-14 · Zero-change iteration guards
+- **Priority:** P1 · **Effort:** S · **Risk:** LOW · **Status:** IN-PROGRESS —
+  implemented 2026-07-28 (58b93be); G8 certification pending.
+- **Change spec (landed):** `goal_product_diff_empty` helper (fail-safe,
+  bookkeeping-excluded); readme-maintainer's empty-change hole fixed (a
+  zero-change iteration used to DISPATCH; the empty set now skips); coherence
+  zero-change deterministic PASS with text DISTINCT from the crash stub —
+  `goal_gate.py` certifies it (self-test pins both classifications); demo
+  recording reused on an empty product diff. Knob `CHAIN_ZERO_CHANGE_SKIPS`,
+  default on.
+- **Verify:** `bash tests/automation/test-zero-change-guard.sh` (13 cases) ·
+  `python3 scripts/automation/lib/goal_gate.py self-test`.
+- **Rollback:** `CHAIN_ZERO_CHANGE_SKIPS=false` (readme hole fix stays — bug fix;
+  its escape is the pre-existing `CHAIN_README_EVERY_ITER=true`).
+- **Stop-and-ask:** none.
+
+### SPEED-15 · Wall-clock iteration budget (warn-first)
+- **Priority:** P2 · **Effort:** M (slice a landed; slice b TODO) · **Risk:** LOW
+  (warn) / MED (trim) · **Status:** IN-PROGRESS — slice (a) implemented
+  2026-07-28: knobs `CHAIN_ITER_TIME_BUDGET_SECONDS` (default 0=off; suggest
+  5400) + `CHAIN_ITER_BUDGET_MODE` (warn|trim, default warn), step-boundary
+  checks (never mid-agent), one loud warn + `iter_budget` telemetry, trim ladder
+  for showcase-class steps only (defer demo+readme; summarizer kept; spine and
+  gates NEVER trimmed — grep-pinned by the test).
+- **Slice (b) TODO:** trim-mode browser-set narrowing — drop only the no-golden
+  regression re-drives with mandatory `DEFERRED-BUDGET` result rows + the
+  one-line evaluator contract ("a DEFERRED-BUDGET row keeps prior status;
+  schedule next iteration", pending_infra pattern). Requires one full warn-mode
+  session of telemetry FIRST (G8) — do not build trim-b before that exists.
+- **Verify:** `bash tests/automation/test-iter-budget.sh` (17 cases).
+- **Rollback:** default off — unset the env.
+- **Stop-and-ask:** before enabling trim as any default.
+
+### SPEED-16 · Browser-qa turn diet
+- **Priority:** P0 · **Effort:** S · **Risk:** LOW · **Status:** IN-PROGRESS —
+  implemented 2026-07-28 (b33e21d); G8 certification pending.
+- **Change spec (landed):** 2-attempt selector recovery budget then
+  FAIL-with-evidence (a page that genuinely changed stays a recorded finding);
+  ONE screenshot per test at the acceptance state (+1 on failure; triad
+  deleted); all expected strings verified in ONE get_text; golden-first setup
+  (replay `journey-scripts/` prefixes verbatim; judgment starts at NEW steps).
+- **DoD:** post-session telemetry shows browser-qa ≤ 60 turns/invocation with
+  no journey-status regressions vs the desk baseline.
+- **Verify:** sync `--check` · run-evals · next-session telemetry (TOKEN-8 rows).
+- **Rollback:** revert bodies + versions.
+- **Stop-and-ask:** journeys flipping PASS→FAIL on recovery exhaustion — raise
+  the cap to 3, never delete it.
+
+### SPEED-17 · Deterministic phase-closure gate (LLM retired to an escape hatch)
+- **Priority:** P1 · **Effort:** M · **Risk:** LOW-MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-28; G8 certification pending.
+- **Problem:** the phase-closure-auditor LLM added no new judgment — Step 1
+  re-read three already-gating verdicts; Steps 2-4 were existence/count/
+  consistency checks. ~5 min + one LLM flake source per full iteration on a
+  HARD gate.
+- **Change spec (landed):** `scripts/automation/lib/closure_gate.py` writes the
+  FROZEN CLOSURE-PASS/CLOSURE-FAIL format deterministically (verdict presence,
+  6-UI-artifact existence + substance, ≥3 numbered what-to-click steps,
+  all-SKIPPED with-reason ⇒ WARN / without ⇒ FAIL, backend-only inconsistency,
+  objective vagueness BLOCKING / subtle vagueness WARN — policed upstream by
+  qa's live audit and downstream by the evaluator's evidence walk);
+  `phase-closure-check.sh` calls it; the agent dispatch survives behind
+  `CHAIN_CLOSURE_LLM=true`.
+- **Verify:** `python3 scripts/automation/lib/closure_gate.py self-test` ·
+  `bash tests/automation/test-closure-gate.sh` · run-evals.
+- **Rollback:** `CHAIN_CLOSURE_LLM=true` (single env).
+- **Stop-and-ask:** a real session where the deterministic gate passes an
+  artifact set the LLM would have failed for a SUBSTANTIVE reason — bring the
+  case, don't widen the script silently.
+
+### SPEED-18 · UI-evolution question dedupe (4 askers → 2)
+- **Priority:** P1 · **Effort:** S · **Risk:** MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-28; G8 certification pending.
+- **Problem:** "did the UI evolve / is it reachable" was asked FOUR times per
+  full iteration (reviewer checklist, qa live audit, ux-regression Step 1,
+  coherence Step 2).
+- **Change spec (landed):** owners = qa's live UI Evolution Audit (browser +
+  screenshots, gating) and coherence-auditor Step 2 (blueprint-grounded,
+  objective FAIL, GOAL_ACHIEVED veto) — both UNCHANGED. Reviewer lost its three
+  runtime-guess checklist items + the `ui_evolved_with_capability`/
+  `navigation_updated` YAML keys (verified: no script parses them; auditor
+  golden fixtures carry them only as frozen inputs). Ux-regression Step 1 now
+  CONSUMES qa's audit + coherence.md and judges only what neither covers (label
+  clarity, visual feedback, rendered consistency) + flags audit contradictions.
+  D2 intact — all agents survive; only repeated questions were removed.
+- **Verify:** reviewer judgment goldens 4/4 · sync `--check` · run-evals.
+- **Rollback:** revert bodies + versions.
+- **Stop-and-ask:** a reviewer golden verdict-class flip; a real-session UI miss
+  only the deleted reviewer items would have caught ⇒ restore the first item only.
+
+### SPEED-19 · Auditor risk-ranked spot-verification
+- **Priority:** P1 · **Effort:** S-M · **Risk:** MED-HIGH · **Status:**
+  IN-PROGRESS — implemented 2026-07-28; G8 certification pending.
+- **Problem:** auditor Step 1 re-derived the full spec-compliance trace for
+  EVERY DoD item — the third full pass over ground the reviewer (code) and QA
+  (live rows) already covered (~202 min/session).
+- **Change spec (landed):** full code trace when ANY of: (a) state/data/auth/
+  money risk class; (b) artifact contradiction (the trigger even when QA is
+  green — golden case-03's shape); (c) reviewer `spec_alignment: partial` or a
+  spec-category issue; (d) the auditor's own Steps 2-4 leads. Mechanical items
+  with reviewer PASS + an executed QA row: accepted WITH double citation; no
+  citation ⇒ full trace. Steps 2-5, severity tree, fix authority untouched.
+- **Verify:** auditor judgment goldens 4/4 (case-03 MUST still FAIL) · run-evals.
+- **Rollback:** revert body + version (single hunk).
+- **Stop-and-ask:** any auditor golden verdict-class flip ⇒ revert immediately.
+
 ### TOKEN-1 · Per-agent project-template slicing
 - **Priority:** P1 · **Effort:** M · **Risk:** LOW · **Status:** DONE 2026-07-14 —
   release-manager/reviewer/qa converted; developer conversion deliberately LAST per this
@@ -1609,6 +1852,28 @@ benchmark (or a real session's telemetry) before AND after (G8).
   re-ran green same day (test-phase-telemetry.sh cases 1+2 inside run-evals
   116/116). Measurement chapter closed.
 
+### TOKEN-9 · Showcase tier demotion — demo-narrator + readme-maintainer → light
+- **Priority:** P2 · **Effort:** S · **Risk:** LOW · **Status:** IN-PROGRESS —
+  implemented 2026-07-28 (part of the SPEED-9..19 package); TOKEN-2-class
+  experiment, G8 before/after via the next real session's TOKEN-8 rows.
+- **Problem:** demo-narrator (373k output tokens/15 iters) and readme-maintainer
+  are schema-constrained procedural writers with deterministic safety nets
+  (demo JSON is linted/executed by `demo_runner.py`; README edits are
+  marker-scoped) — sonnet-priced tokens for haiku-shaped work. ~0 wall-clock
+  (both ride the forked showcase tail), pure token cost.
+- **Change spec (landed):** `model_tier: standard → light` on both agent.yamls
+  (demo-narrator 2.2.0, readme-maintainer 1.2.0); tier prose table in
+  `.claude/model-orchestration.md` updated. **iteration-summarizer deliberately
+  STAYS standard** — REP-4 raised its concreteness bar and it is the human's
+  primary reading surface; demoting it while fixing its top complaint would be
+  self-defeating.
+- **DoD:** after one real session: `demo_runner.py --mode lint` pass-rate
+  unchanged; README AUTO blocks intact; TOKEN-8 rows show the cost drop.
+- **Verify:** sync `--check` · run-evals · next-session artifact checks above.
+- **Rollback:** one-line tier revert per agent (TOKEN-2's watch-item pattern).
+- **Stop-and-ask:** haiku demo JSON failing lint more than occasionally, or ONE
+  README AUTO-block corruption of hand-written prose ⇒ revert that agent.
+
 ---
 
 ## 10. P1 — Reliability & weaker-model hardening
@@ -2814,6 +3079,28 @@ territory).
   docs (env var table).
 - **Rollback:** unset env (no-op by default).
 
+### REP-4 · Iteration summaries must name the concrete change
+- **Priority:** P0 (the user's top reporting complaint) · **Effort:** S ·
+  **Risk:** LOW · **Status:** IN-PROGRESS — implemented 2026-07-28 (e619138,
+  part of the SPEED-9..19 package); G8 certification pending.
+- **Problem:** desk-session summaries never named one source file/screen; the
+  "In plain words" opener was recycled filler ("Behind-the-scenes work —
+  nothing visibly new this round"); "What you can do now" was copied verbatim
+  from the prior summary BY INSTRUCTION.
+- **Change spec (landed):** the opener must name the screen/page and what the
+  user now sees (the generic sentence is allowed ONLY on zero-product-file
+  iterations, and must still name the concrete area); the FIRST "What was done"
+  bullet is fixed-format — `Product changes: <files/routes>` or exactly
+  `No product change this iteration.`; "What you can do now" is re-derived from
+  journey-history every iteration; plain-language skill hard rule 7 ("concrete
+  beats generic"). H2 set unchanged (schema-enforced).
+- **Verify:** run-evals (summary schema self-tests) · eyeball the next real
+  session's summary: named screen in the opener, product-change first bullet.
+- **Files:** `agents/iteration-summarizer/*`, `templates/iteration-summary.md`,
+  `skills/plain-language.md`, mirrors.
+- **Rollback:** revert three files + version.
+- **Stop-and-ask:** none.
+
 ---
 
 ## 14. P1 — Documentation & guides
diff --git a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
index 16f4b1a..f83e43b 100755
--- a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
@@ -313,13 +313,14 @@ fi
 
 # ── Run browser QA agent ───────────────────────────────────────────────────
 cd "$REPO_ROOT"
-export CHAIN_CURRENT_AGENT=browser-qa-agent
 # Guard against `set -e` so we can inspect the exit code and fall back to
 # writing a SKIPPED stub when the agent leaves no results file.
 _bqa_rc=0
 if [[ "$_bqa_infra_blocked" == "yes" ]]; then
-  : # REL-14: dispatch skipped — preflight failure recorded above
+  : # REL-14: dispatch skipped — preflight failure recorded above (no dispatch → no agent telemetry)
 else
+record_agent_invocation_start browser-qa-agent
+_agent_t0="$CHAIN_AGENT_START_EPOCH"
 claude_with_quota_retry -p "You are the browser-qa-agent for phased development.
 
 Phase: $PHASE
@@ -358,6 +359,7 @@ The report MUST contain a line at the top:
 **Browser QA Verdict:** SKIPPED
 
 Then STOP." || _bqa_rc=$?
+record_agent_invocation_end browser-qa-agent "$_agent_t0" "$_bqa_rc"
 fi
 
 # Signal-induced exit (Ctrl-C, SIGKILL, SIGTERM) → do NOT write SKIPPED stubs.
diff --git a/incredible_auto_dev/scripts/automation/demo-phase.sh b/incredible_auto_dev/scripts/automation/demo-phase.sh
index cd7f556..eac5f23 100755
--- a/incredible_auto_dev/scripts/automation/demo-phase.sh
+++ b/incredible_auto_dev/scripts/automation/demo-phase.sh
@@ -248,7 +248,8 @@ if [[ "$REAUTHOR" != "yes" ]] && _demo_json_fresh "$DEMO_JSON_OUT" "${AUTHOR_INP
   echo "[demo] Reusing cached demo script: $(basename "$DEMO_JSON_OUT") (pass --reauthor to rebuild)."
 else
   require_claude
-  export CHAIN_CURRENT_AGENT=demo-narrator
+  record_agent_invocation_start demo-narrator
+  _agent_t0="$CHAIN_AGENT_START_EPOCH"
   export CHAIN_CLAUDE_PRE_RETRY_HOOK="ensure_services_running"
   _author_rc=0
   if [[ "$MODE" == "session" ]]; then
@@ -287,6 +288,7 @@ Inputs (read only what exists):
 
 Write ONLY the JSON file at the output path. Do NOT open a browser. When done, STOP." || _author_rc=$?
   fi
+  record_agent_invocation_end demo-narrator "$_agent_t0" "$_author_rc"
 
   # Signal exit — propagate unchanged (resume logic re-runs). Do not stub.
   if [[ $_author_rc -eq 130 || $_author_rc -eq 137 || $_author_rc -eq 143 ]]; then
diff --git a/incredible_auto_dev/scripts/automation/dev-phase.sh b/incredible_auto_dev/scripts/automation/dev-phase.sh
index 9756b1a..23b1881 100755
--- a/incredible_auto_dev/scripts/automation/dev-phase.sh
+++ b/incredible_auto_dev/scripts/automation/dev-phase.sh
@@ -85,7 +85,9 @@ trap cleanup_dev_servers EXIT
 
 # ── Developer agent ──────────────────────────────────────────────────────
 cd "$REPO_ROOT"
-export CHAIN_CURRENT_AGENT=developer
+record_agent_invocation_start developer
+_agent_t0="$CHAIN_AGENT_START_EPOCH"
+_agent_rc=0
 claude_with_quota_retry -p "You are the developer agent for phased development.
 
 Phase: $PHASE
@@ -105,6 +107,8 @@ When complete:
   Use the template at templates/implementation-summary.md.
   Include: features implemented, changed behavior, backend-only items, incomplete items, config/env changes, known limitations.
   This report is for operators, not developers — write in plain language, not code.
-- Update runs/${PHASE}/status.json with current_step: dev_complete"
+- Update runs/${PHASE}/status.json with current_step: dev_complete" || _agent_rc=$?
+record_agent_invocation_end developer "$_agent_t0" "$_agent_rc"
+(( _agent_rc == 0 )) || exit "$_agent_rc"
 
 echo "[dev-phase] Done."
diff --git a/incredible_auto_dev/scripts/automation/finalize-phase.sh b/incredible_auto_dev/scripts/automation/finalize-phase.sh
index ecbcabe..2389d07 100755
--- a/incredible_auto_dev/scripts/automation/finalize-phase.sh
+++ b/incredible_auto_dev/scripts/automation/finalize-phase.sh
@@ -142,7 +142,9 @@ else
 fi
 
 cd "$REPO_ROOT"
-export CHAIN_CURRENT_AGENT=release-manager   # needed for the interactive dispatch backend to map this call to a subagent
+record_agent_invocation_start release-manager   # exports CHAIN_CURRENT_AGENT — needed for the interactive dispatch backend to map this call to a subagent
+_agent_t0="$CHAIN_AGENT_START_EPOCH"
+_agent_rc=0
 claude_with_quota_retry -p "You are the release-manager agent for phased development.
 
 Phase to finalize: $PHASE
@@ -166,7 +168,9 @@ Perform the release flow:
 4. If GH_AUTH_AVAILABLE is true: create PR with title: feat: $PHASE -- <one-line summary>
 5. If GH_AUTH_AVAILABLE is false: skip PR creation, print a clear message showing the
    manual command the user can run once they authenticate: gh pr create ...
-6. Report the PR URL (or the manual command if PR was skipped)"
+6. Report the PR URL (or the manual command if PR was skipped)" || _agent_rc=$?
+record_agent_invocation_end release-manager "$_agent_t0" "$_agent_rc"
+(( _agent_rc == 0 )) || exit "$_agent_rc"
 
 # Clean up transient agent-generated files before finalizing
 echo "[finalize] Cleanup: removing temp files..."
diff --git a/incredible_auto_dev/scripts/automation/generate-test-plan.sh b/incredible_auto_dev/scripts/automation/generate-test-plan.sh
index 5226efc..6605ab4 100755
--- a/incredible_auto_dev/scripts/automation/generate-test-plan.sh
+++ b/incredible_auto_dev/scripts/automation/generate-test-plan.sh
@@ -40,7 +40,9 @@ echo "[generate-test-plan] Generating test plan for: $PHASE (frontend: $FRONTEND
 mkdir -p "$REPO_ROOT/reports/qa"
 
 cd "$REPO_ROOT"
-export CHAIN_CURRENT_AGENT=qa
+record_agent_invocation_start qa
+_agent_t0="$CHAIN_AGENT_START_EPOCH"
+_agent_rc=0
 claude_with_quota_retry -p "You are the qa agent operating in TEST PLAN GENERATION mode for phased development.
 
 Phase: $PHASE
@@ -60,7 +62,9 @@ The plan must include:
 - For each test case: type, preconditions, steps, expected outcome, pass criteria
 - A summary of total test cases by type
 
-Keep it concise (1-3 pages). Write the plan and STOP."
+Keep it concise (1-3 pages). Write the plan and STOP." || _agent_rc=$?
+record_agent_invocation_end qa "$_agent_t0" "$_agent_rc"
+(( _agent_rc == 0 )) || exit "$_agent_rc"
 
 if [[ ! -f "$TEST_PLAN" ]]; then
   echo "[generate-test-plan] Warning: agent did not write test plan file." >&2
diff --git a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
index 4a5351a..6b31c2c 100755
--- a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
+++ b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
@@ -35,6 +35,9 @@ set -e
 
 SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
 source "$SCRIPT_DIR/lib/common.sh"
+# SPEED-15: wall-clock budget clock — measure from the engine's iteration start
+# (exported CHAIN_ITER_START_EPOCH), not this child process's start.
+if declare -F iter_budget_init >/dev/null 2>&1; then iter_budget_init; fi
 source "$SCRIPT_DIR/lib/telemetry.sh"
 # Deterministic regression-replay lane — ONE implementation shared with the
 # FULL pipeline's browser-qa step (browser-qa-phase.sh). The tag keeps this
@@ -545,13 +548,17 @@ _bqa_tripwire_active() {
   return 0
 }
 
-# Knob: CHAIN_LEAN_PARALLEL_BROWSER_QA=off|replay|full, default off (G4).
+# Knob: CHAIN_LEAN_PARALLEL_BROWSER_QA=off|replay|full, default replay
+# (SPEED-11 flipped off→replay: the fork shipped default-off per G4 in SPEED-2,
+# was benchmarked, and carries its own tripwire — 2-of-3 attempt-1 review FAILs
+# disable it for the session. The replay lane is model-free python, safe on
+# both backends; rollback = CHAIN_LEAN_PARALLEL_BROWSER_QA=off).
 # "full" (SPEED-3: fork the whole section, LLM lane included) is HEADLESS-ONLY:
 # on the interactive backend, killing the engine-side waiter would strand the
 # pump's subagent against a request nobody reads (stale req/res files are only
 # cleaned at engine start) — that cancellation gap is EXP-4's, so interactive
 # demotes full → replay with a logged warning. Unrecognized values fall to off.
-_BQA_REQUESTED="${CHAIN_LEAN_PARALLEL_BROWSER_QA:-off}"
+_BQA_REQUESTED="${CHAIN_LEAN_PARALLEL_BROWSER_QA:-replay}"
 _BQA_MODE="off"
 _BQA_OFF_REASON=""
 case "$_BQA_REQUESTED" in
@@ -579,6 +586,11 @@ if [[ "$_BQA_MODE" == "replay" || "$_BQA_MODE" == "full" ]]; then
     _BQA_MODE="off"; _BQA_OFF_REASON="no-jq"
   fi
 fi
+# SPEED-9 evidence micro-path: no review loop runs, so there is nothing for a
+# browser-qa fork to overlap — the section runs inline.
+if [[ "${CHAIN_LEAN_EVIDENCE_ONLY:-false}" == "true" && "$_BQA_MODE" != "off" ]]; then
+  _BQA_MODE="off"; _BQA_OFF_REASON="evidence-mode"
+fi
 # Name the knob state every iteration (mirrors run-goal.sh's iter_config event).
 record_telemetry_event "iter_config" "$(jq -cn --arg k "CHAIN_LEAN_PARALLEL_BROWSER_QA" --arg v "$_BQA_MODE" --arg req "$_BQA_REQUESTED" --arg r "$_BQA_OFF_REASON" '{key:$k, value:$v, requested:$req, reason:$r}' 2>/dev/null || printf '{"key":"CHAIN_LEAN_PARALLEL_BROWSER_QA","value":"%s"}' "$_BQA_MODE")"
 
@@ -854,7 +866,16 @@ The report MUST start with a line matching exactly:
 # aborts the iteration as before (set -e semantics, now with the code preserved).
 # Resume-skip: handoff on disk + the tree exactly where this iteration last
 # left it → the ~41-min build is already done, don't redo it.
-if step_done_valid developer --verify-tree --dir "$ITER_DIR" "$DEV_HANDOFF"; then
+if [[ "${CHAIN_LEAN_EVIDENCE_ONLY:-false}" == "true" ]]; then
+  # SPEED-9 evidence micro-path: the spec's only deliverable is visual evidence
+  # for already-working journeys — no build work. Stub the dev handoff so the
+  # evaluator's input set stays complete; re-runs are idempotent (no checkpoint).
+  echo "[goal-iter-lean] EVIDENCE mode: skipping developer (no code changes planned)."
+  if [[ ! -s "$DEV_HANDOFF" ]]; then
+    printf '# Dev Handoff — %s\n\nEvidence-only iteration: no code changes were planned or made.\nThe pipeline captured fresh visual evidence for the Target journeys instead;\nsee the browser test results and this iteration'"'"'s demo recording.\n' "$ITER_NAME" > "$DEV_HANDOFF"
+  fi
+  _step_skipped_event "developer"
+elif step_done_valid developer --verify-tree --dir "$ITER_DIR" "$DEV_HANDOFF"; then
   _step_skipped_event "developer"
 else
   step_invalidate_from developer "$ITER_DIR"
@@ -867,8 +888,9 @@ fi
 
 # TOKEN-7 build 1: the round-1 review packet. Ordering is load-bearing — this
 # sits BEFORE both fork spawn points below (same stale-write discipline as the
-# forks' own kill-then-invalidate rule).
-_build_review_packet_or_degrade
+# forks' own kill-then-invalidate rule). Evidence mode has no reviewer, so no
+# packet is built (SPEED-9).
+[[ "${CHAIN_LEAN_EVIDENCE_ONLY:-false}" == "true" ]] || _build_review_packet_or_degrade
 
 # ── SPEED-2 fork: service boot + deterministic replay ∥ review ────────────
 # Forked HERE — right after the developer step settles — because review and
@@ -950,7 +972,16 @@ fi
 # Resume-skip: the marker alone is never trusted — the report must live-parse
 # to a verdict (a FAIL report still routes into the fix branch below, exactly
 # as a freshly written FAIL would).
-if { step_done_valid review-1 --dir "$ITER_DIR" "$REVIEW_REPORT" \
+if [[ "${CHAIN_LEAN_EVIDENCE_ONLY:-false}" == "true" ]]; then
+  # SPEED-9 evidence micro-path: nothing was built, so there is nothing to
+  # review. The stub's PASS verdict line keeps every parser downstream honest
+  # about the shape while the body states no review occurred.
+  echo "[goal-iter-lean] EVIDENCE mode: skipping reviewer (no code changes to review)."
+  if [[ ! -s "$REVIEW_REPORT" ]]; then
+    printf '**Verdict:** PASS\n\nEvidence-only iteration: no code changes were made, so developer and reviewer were not dispatched. Nothing to review.\n' > "$REVIEW_REPORT"
+  fi
+  _step_skipped_event "reviewer"
+elif { step_done_valid review-1 --dir "$ITER_DIR" "$REVIEW_REPORT" \
      || step_done_valid review-2 --dir "$ITER_DIR" "$REVIEW_REPORT"; } && _review_parses; then
   _step_skipped_event "reviewer"
 else
@@ -1036,6 +1067,13 @@ if [[ "${CHAIN_LEAN_PARALLEL_COHERENCE:-true}" == "true" && -n "$ITER_DIR" \
   if step_done_valid coherence --verify-tree --dir "$ITER_DIR" "$COHERENCE_OUTPUT_LEAN" \
      && grep -qE '^\*\*Verdict:\*\* COHERENCE-(PASS|WARN|FAIL)' "$COHERENCE_OUTPUT_LEAN"; then
     _step_skipped_event "coherence-auditor"
+  elif [[ "${CHAIN_ZERO_CHANGE_SKIPS:-true}" == "true" ]] \
+       && { declare -F goal_product_diff_empty >/dev/null 2>&1 || source "$SCRIPT_DIR/lib/goal-gates.sh" 2>/dev/null; } \
+       && goal_product_diff_empty "$(cat "$ITER_DIR/snapshot-sha" 2>/dev/null || echo "")" "$REPO_ROOT"; then
+    # SPEED-14: empty product diff after the dev/review loop — nothing to
+    # audit, so don't burn a fork. run-goal.sh's sequential coherence step
+    # records the deterministic zero-change PASS for this case.
+    echo "[goal-iter-lean] coherence fork skipped — zero-change iteration (empty product diff); the engine records a deterministic PASS."
   else
     step_invalidate_from coherence "$ITER_DIR"
     rm -f "$_COH_RC_FILE"
@@ -1061,6 +1099,7 @@ if [[ "${CHAIN_LEAN_PARALLEL_COHERENCE:-true}" == "true" && -n "$ITER_DIR" \
   fi
 fi
 
+if declare -F iter_budget_check >/dev/null 2>&1; then iter_budget_check "browser-qa"; fi
 # ── Step 3: Browser QA ────────────────────────────────────────────────────
 # Determine if frontend work is implied. Lean iterations always test journeys,
 # so we always try to start the frontend; if it fails we mark all SKIPPED and
@@ -1131,6 +1170,17 @@ fi
 # never read demo artifacts, so its input set is unchanged. demo-phase.sh
 # boots its own services idempotently, so it no longer depends on this
 # script's still-warm ports.
+#
+# SPEED-9 exception — EVIDENCE mode records the walkthrough HERE, before the
+# evaluator reads. In plain lean the post-eval showcase ordering made a spec
+# whose deliverable was "record the walkthrough" structurally unpassable (the
+# desk-session iter-12 ESCALATE); the evidence micro-path exists for exactly
+# that deliverable, so the recording must precede evaluation.
+if [[ "${CHAIN_LEAN_EVIDENCE_ONLY:-false}" == "true" ]]; then
+  echo "[goal-iter-lean] EVIDENCE mode: recording the walkthrough BEFORE evaluation..."
+  bash "$SCRIPT_DIR/demo-phase.sh" "$ITER_NAME" \
+    || echo "[goal-iter-lean] demo-phase.sh exited non-zero — continuing (the evaluator scores from whatever evidence exists)."
+fi
 
 echo "[goal-iter-lean] Done. Iteration artifacts:"
 echo "  Dev handoff:   $DEV_HANDOFF"
diff --git a/incredible_auto_dev/scripts/automation/host-guard-adopt.sh b/incredible_auto_dev/scripts/automation/host-guard-adopt.sh
new file mode 100755
index 0000000..ce754e2
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/host-guard-adopt.sh
@@ -0,0 +1,121 @@
+#!/usr/bin/env bash
+# host-guard-adopt.sh — confine an ALREADY-RUNNING process tree to the
+# project's host-guard caps, in place, no relaunch required.
+#
+# WHY: interactive-pump dispatches run inside the foreground CLI session
+# (Claude Code / Codex). host-guard-exec.sh confines that session from birth,
+# but requiring a special launch command is a footgun — this script retrofits
+# the confinement onto the live session instead:
+#
+#   1. systemd scope adoption (busctl StartTransientUnit with the PIDs
+#      property + set-property): moves the process under a transient user
+#      scope carrying CPUQuota/MemoryHigh/TasksMax (and AllowedCPUs where the
+#      cpuset controller is delegated to user units — many distros delegate
+#      only cpu/memory/pids, in which case AllowedCPUs is a silent no-op).
+#   2. taskset -a -c -p on the target AND every existing descendant: the hard
+#      CPU mask — all threads, inherited by all future children. This is the
+#      layer that actually prevents power-transient resets, and it works with
+#      no systemd at all.
+#
+# Usage:
+#   host-guard-adopt.sh <pid>                confine this pid('s tree)
+#   host-guard-adopt.sh --cli-root-of <pid>  walk UP from <pid> to the
+#       outermost ancestor whose cmdline matches HOST_GUARD_CLI_PATTERN
+#       (default 'claude|codex') and confine THAT tree; falls back to <pid>
+#       itself when no ancestor matches.
+#
+# Idempotent: exits 0 immediately when the target is already confined.
+# Absent/disabled host-guard.env ⇒ no-op (framework stays project-neutral).
+# Limitation: BLAS/OMP thread-cap env vars cannot be injected into a running
+# process — only wrapper-launched (host-guard-exec.sh) sessions get those.
+set -euo pipefail
+
+MODE_ROOT=0
+if [[ "${1:-}" == "--cli-root-of" ]]; then MODE_ROOT=1; shift; fi
+PID="${1:?usage: host-guard-adopt.sh [--cli-root-of] <pid>}"
+[[ "$PID" =~ ^[0-9]+$ && -r "/proc/$PID/status" ]] \
+  || { echo "[host-guard-adopt] pid '$PID' is not a running process" >&2; exit 1; }
+
+ROOT="${HOST_GUARD_ROOT:-$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || pwd)}"
+ENV_FILE="$ROOT/project-extensions/host-guard/host-guard.env"
+# shellcheck disable=SC1090
+[[ -f "$ENV_FILE" ]] && source "$ENV_FILE" || true
+if [[ "${HOST_GUARD_ENABLED:-0}" != "1" || -z "${HOST_GUARD_CPU_LIST:-}" ]]; then
+  echo "[host-guard-adopt] no enabled host-guard.env under $ROOT — nothing to do."
+  exit 0
+fi
+command -v taskset >/dev/null 2>&1 \
+  || { echo "[host-guard-adopt] taskset not available" >&2; exit 1; }
+
+_width() { # "0-3,8-11" → 8; 0 when unparseable
+  local list="${1:-}" n=0 part a b
+  [[ -n "$list" ]] || { echo 0; return 0; }
+  local -a parts=()
+  IFS=',' read -ra parts <<< "$list"
+  for part in "${parts[@]}"; do
+    if [[ "$part" =~ ^[0-9]+-[0-9]+$ ]]; then
+      a="${part%-*}"; b="${part#*-}"
+      if (( b >= a )); then n=$(( n + b - a + 1 )); fi
+    elif [[ "$part" =~ ^[0-9]+$ ]]; then
+      n=$(( n + 1 ))
+    fi
+  done
+  echo "$n"
+}
+_ppid() { awk '/^PPid:/{print $2}' "/proc/$1/status" 2>/dev/null || true; }
+_allowed_n() { _width "$(awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$1/status" 2>/dev/null)"; }
+
+TARGET="$PID"
+if [[ "$MODE_ROOT" == "1" ]]; then
+  _pat="${HOST_GUARD_CLI_PATTERN:-claude|codex}" _p="$PID" _best=""
+  while [[ "$_p" =~ ^[0-9]+$ ]] && (( _p > 1 )); do
+    if tr '\0' ' ' < "/proc/$_p/cmdline" 2>/dev/null | grep -qE "$_pat"; then _best="$_p"; fi
+    _p="$(_ppid "$_p")"
+  done
+  if [[ -n "$_best" ]]; then
+    TARGET="$_best"
+  else
+    echo "[host-guard-adopt] no ancestor of $PID matches '$_pat' — confining $PID itself."
+  fi
+fi
+
+WIDTH="$(_width "$HOST_GUARD_CPU_LIST")"
+if (( WIDTH == 0 )); then
+  echo "[host-guard-adopt] unparseable HOST_GUARD_CPU_LIST='$HOST_GUARD_CPU_LIST'" >&2
+  exit 1
+fi
+if (( $(_allowed_n "$TARGET") <= WIDTH )); then
+  echo "[host-guard-adopt] pid $TARGET already confined ($(awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$TARGET/status"))."
+  exit 0
+fi
+
+# 1) Scope adoption — aggregate memory/task/quota ceilings for the whole tree.
+UNIT="chain-pump-hostguard-$TARGET.scope"
+if busctl call --user org.freedesktop.systemd1 /org/freedesktop/systemd1 \
+     org.freedesktop.systemd1.Manager StartTransientUnit 'ssa(sv)a(sa(sv))' \
+     "$UNIT" fail 1 PIDs au 1 "$TARGET" 0 >/dev/null 2>&1; then
+  systemctl --user set-property "$UNIT" \
+    "CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}" \
+    "MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G}" \
+    "TasksMax=${HOST_GUARD_TASKS_MAX:-2048}" 2>/dev/null || true
+  # Engages only where the cpuset controller is delegated to user units.
+  systemctl --user set-property "$UNIT" "AllowedCPUs=$HOST_GUARD_CPU_LIST" 2>/dev/null || true
+  echo "[host-guard-adopt] scope $UNIT adopted pid $TARGET (CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}, MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G}, TasksMax=${HOST_GUARD_TASKS_MAX:-2048})."
+else
+  echo "[host-guard-adopt] scope adoption unavailable — applying the CPU mask only."
+fi
+
+# 2) Hard CPU mask NOW — target + every existing descendant; future children
+# inherit. -a covers all threads of each process.
+_descendants() { local c; for c in $(pgrep -P "$1" 2>/dev/null); do echo "$c"; _descendants "$c"; done; }
+taskset -a -c -p "$HOST_GUARD_CPU_LIST" "$TARGET" >/dev/null 2>&1 || true
+for _c in $(_descendants "$TARGET"); do
+  taskset -a -c -p "$HOST_GUARD_CPU_LIST" "$_c" >/dev/null 2>&1 || true
+done
+
+if (( $(_allowed_n "$TARGET") <= WIDTH )); then
+  echo "[host-guard-adopt] confined pid $TARGET (and descendants) to CPUs $HOST_GUARD_CPU_LIST."
+  exit 0
+fi
+echo "[host-guard-adopt] FAILED to confine pid $TARGET (Cpus_allowed_list unchanged)." >&2
+exit 1
diff --git a/incredible_auto_dev/scripts/automation/lib/agent_permissions.py b/incredible_auto_dev/scripts/automation/lib/agent_permissions.py
index 8a4a2c8..f570566 100644
--- a/incredible_auto_dev/scripts/automation/lib/agent_permissions.py
+++ b/incredible_auto_dev/scripts/automation/lib/agent_permissions.py
@@ -104,28 +104,39 @@ EFFORT_OVERRIDES: dict[str, str] = {
 
 # Per-agent runtime caps (seconds), ~2.5-3x the typical durations measured from
 # goal-session telemetry (tape_to_profit: developer ~41m, reviewer ~21m,
-# browser-qa ~20m, evaluator ~17m, decomposer ~8m, coherence ~4m). One flat
-# 7200s cap previously let a hung 20-minute reviewer burn a full 2 hours before
-# the watchdog fired. Agents NOT listed here (the full-pipeline-only chain:
-# orchestrator, qa, ui-*, auditor, release-manager, ...) fall back to the flat
-# CHAIN_CLAUDE_MAX_RUNTIME_SECONDS / CHAIN_DISPATCH_INFLIGHT_TIMEOUT global —
-# zero behavior change for run-phase.sh.
+# browser-qa ~20m, evaluator ~17m, decomposer ~8m, coherence ~4m; desk session
+# maxima for the full-pipeline chain: orchestrator ~9.4m, qa ~18.2m,
+# ui-impact ~7.4m, ui-test-designer ~11.4m, ux-regression ~7.1m,
+# auditor ~17.7m, phase-closure ~4.8m). One flat 7200s cap previously let a
+# hung 20-minute reviewer burn a full 2 hours before the watchdog fired.
+# SPEED-12 filled the full-pipeline rows (each ≥2.5× its observed maximum);
+# any agent still absent falls back to the flat
+# CHAIN_CLAUDE_MAX_RUNTIME_SECONDS / CHAIN_DISPATCH_INFLIGHT_TIMEOUT global.
 #
 # Resolution precedence (implemented by the shell seam, lib/quota-retry.sh):
 #   CHAIN_TIMEOUT_<AGENT> env  >  agents/<name>/agent.yaml max_runtime_seconds
 #   >  this table  >  flat global. An EXPLICITLY exported flat global keeps
 #   today's meaning and disables the per-agent table entirely.
 AGENT_TIMEOUTS_SECONDS: dict[str, int] = {
-    "goal-decomposer":      1800,   # typical ~8m
-    "developer":            7200,   # typical ~41m; initial builds vary — keep 2h
-    "reviewer":             3600,   # typical ~21m (observed hang burned 7200s)
-    "browser-qa-agent":     4500,   # typical ~20m; grows with journey count
-    "coherence-auditor":    1200,   # typical ~4m
-    "goal-evaluator":       3600,   # typical ~17m
-    "goal-proposer":        3600,
-    "iteration-summarizer": 1800,
-    "readme-maintainer":    1800,
-    "demo-narrator":        1800,
+    "goal-decomposer":       1800,   # typical ~8m
+    "developer":             7200,   # typical ~41m; initial builds vary — keep 2h
+    "reviewer":              3600,   # typical ~21m (observed hang burned 7200s)
+    "browser-qa-agent":      4500,   # typical ~20m; grows with journey count
+    "coherence-auditor":     1200,   # typical ~4m
+    "goal-evaluator":        3600,   # typical ~17m
+    "goal-proposer":         3600,
+    "iteration-summarizer":  1800,
+    "readme-maintainer":     1800,
+    "demo-narrator":         1800,
+    # SPEED-12: full-pipeline chain (desk maxima in the comment above)
+    "orchestrator":          2700,   # max ~9.4m → ~4.8×
+    "qa":                    5400,   # max ~18.2m → ~4.9×
+    "ui-impact-analyst":     1800,   # max ~7.4m → ~4.1×
+    "ui-test-designer":      1800,   # max ~11.4m → ~2.6×
+    "ux-regression-reviewer": 1800,  # max ~7.1m → ~4.2×
+    "auditor":               3600,   # max ~17.7m → ~3.4×
+    "phase-closure-auditor": 1800,   # max ~4.8m → ~6.3×
+    "release-manager":       2700,   # no recent trace; procedural git/gh work
 }
 
 # Reads from the legacy `.claude/agents/<name>.md` (frontmatter) by default to
@@ -636,7 +647,11 @@ def _self_test() -> int:
         assert timeout_for("reviewer") == 3600, "reviewer cap from the builtin table"
         assert timeout_for("coherence-auditor") == 1200
         assert timeout_for("developer") == 7200
-        assert timeout_for("orchestrator") is None, "full-pipeline agents keep the flat global"
+        # SPEED-12 filled the full-pipeline rows (2.5x+ observed desk maxima);
+        # only agents absent from the table fall back to the flat global.
+        assert timeout_for("orchestrator") == 2700, "SPEED-12: orchestrator capped"
+        assert timeout_for("qa") == 5400, "SPEED-12: qa capped"
+        assert timeout_for("phase-closure-auditor") == 1800
         assert timeout_for("some-unknown-agent") is None
         neutral = d / "neutral-agents"
         (neutral / "reviewer").mkdir(parents=True)
diff --git a/incredible_auto_dev/scripts/automation/lib/analyze_telemetry.py b/incredible_auto_dev/scripts/automation/lib/analyze_telemetry.py
index 633aba7..a4146a0 100644
--- a/incredible_auto_dev/scripts/automation/lib/analyze_telemetry.py
+++ b/incredible_auto_dev/scripts/automation/lib/analyze_telemetry.py
@@ -261,12 +261,15 @@ def _new_iter_record(iter_name: str, ts: float | None) -> dict[str, Any]:
         "depth": None,
         "complete": False,
         "agents": {},          # name → {seconds, calls, retries, failures}
+        "engine_steps": {},    # step → seconds (non-agent engine work; NOT in agent totals —
+                               # the sub-pipeline steps CONTAIN agent invocations)
         "skipped_steps": [],
         "pump_wait_seconds": 0,
         "quota_sleep_seconds": 0,
         "review_verdicts": [], # [{verdict, attempt}]
         "knob_active": False,  # iter_config event seen (experiment running)
         "journey_deltas": {},
+        "budget_event": None,  # first iter_budget event (SPEED-15), if any
     }
 
 
@@ -301,7 +304,13 @@ def build_wall_report(paths: list[str]) -> dict[str, dict[str, Any]]:
                 a = event.get("agent") or "unattributed"
                 row = cur["agents"].setdefault(
                     a, {"seconds": 0, "calls": 0, "retries": 0, "failures": 0})
-                row["seconds"] += int(event.get("duration_seconds") or 0)
+                # SPEED-13: prefer active_seconds (duration minus quota sleeps)
+                # when the event carries it; quota sleep is reported separately
+                # via quota_pause_end so nothing is lost.
+                secs = event.get("active_seconds")
+                if secs is None:
+                    secs = event.get("duration_seconds")
+                row["seconds"] += int(secs or 0)
                 row["calls"] += 1
                 row["retries"] += int(event.get("retries") or 0)
                 if int(event.get("exit_status") or 0) != 0:
@@ -312,6 +321,18 @@ def build_wall_report(paths: list[str]) -> dict[str, dict[str, Any]]:
                 cur["pump_wait_seconds"] += int(event.get("wait_seconds") or 0)
             elif kind == "quota_pause_end" and cur is not None:
                 cur["quota_sleep_seconds"] += int(event.get("sleep_seconds") or 0)
+            elif kind == "engine_step" and cur is not None:
+                step = event.get("step") or "?"
+                cur["engine_steps"][step] = (
+                    cur["engine_steps"].get(step, 0)
+                    + int(event.get("duration_seconds") or 0))
+            elif kind == "iter_budget" and cur is not None:
+                if cur.get("budget_event") is None:
+                    cur["budget_event"] = {
+                        "budget": int(event.get("budget") or 0),
+                        "elapsed": int(event.get("elapsed") or 0),
+                        "mode": event.get("mode") or "warn",
+                        "at_step": event.get("at_step") or "?"}
             elif kind == "review_verdict" and cur is not None:
                 cur["review_verdicts"].append({
                     "verdict": event.get("verdict") or "?",
@@ -384,17 +405,27 @@ def render_wall_text(report: dict[str, dict[str, Any]],
                     extra += f"  retries={row['retries']}"
                 out.append(f"      {a:<24s} {_fmt_m(row['seconds']):>8s}  "
                            f"calls={row['calls']}{extra}")
+            for step, secs in sorted(rec.get("engine_steps", {}).items(),
+                                     key=lambda kv: -kv[1]):
+                out.append(f"      [engine] {step:<15s} {_fmt_m(secs):>8s}  (contains agent time above)")
             if rec["skipped_steps"]:
                 out.append(f"      (resume-skipped: {', '.join(rec['skipped_steps'])})")
             if rec["pump_wait_seconds"]:
                 out.append(f"      pump-wait              {_fmt_m(rec['pump_wait_seconds']):>8s}")
             if rec["quota_sleep_seconds"]:
                 out.append(f"      quota-pauses           {_fmt_m(rec['quota_sleep_seconds']):>8s}")
+            be = rec.get("budget_event")
+            if be:
+                out.append(f"      OVER BUDGET at {be['at_step']}: {be['elapsed']}s > {be['budget']}s (mode={be['mode']})")
             if wall is not None:
-                if agent_total > wall:
-                    out.append(f"      overlap saved          {_fmt_m(agent_total - wall):>8s}  (parallel steps)")
+                # SPEED-13: agent rows are active time (quota sleeps excluded),
+                # so the residual must exclude the quota-pause seconds too or
+                # every pause would be misread as glue.
+                accounted = agent_total + rec["quota_sleep_seconds"]
+                if accounted > wall:
+                    out.append(f"      overlap saved          {_fmt_m(accounted - wall):>8s}  (parallel steps)")
                 else:
-                    out.append(f"      unattributed (glue)    {_fmt_m(wall - agent_total):>8s}")
+                    out.append(f"      unattributed (glue)    {_fmt_m(wall - accounted):>8s}  (wall − agents(active) − quota)")
         completed = [i for i in s["iterations"] if i["complete"] and i["wall_seconds"]]
         if completed and iter_filter is None:
             mean = sum(i["wall_seconds"] for i in completed) / len(completed)
@@ -531,8 +562,15 @@ _WALL_FIXTURE = [
      "ts": "2026-07-01T10:08:00Z"},
     {"event": "agent_invocation_end", "session_id": "w-1", "agent": "goal-decomposer",
      "exit_status": 0, "duration_seconds": 480, "retries": 0, "ts": "2026-07-01T10:08:00Z"},
+    # SPEED-13: developer hit a quota pause — duration keeps wall meaning,
+    # active_seconds excludes the sleep, quota_pause_end reports it separately.
+    {"event": "quota_pause_end", "session_id": "w-1", "agent": "developer",
+     "sleep_seconds": 600, "ts": "2026-07-01T10:40:00Z"},
     {"event": "agent_invocation_end", "session_id": "w-1", "agent": "developer",
-     "exit_status": 0, "duration_seconds": 2400, "retries": 0, "ts": "2026-07-01T10:48:00Z"},
+     "exit_status": 0, "duration_seconds": 2400, "quota_sleep_seconds": 600,
+     "active_seconds": 1800, "retries": 0, "ts": "2026-07-01T10:48:00Z"},
+    {"event": "engine_step", "session_id": "w-1", "step": "lean-pipeline",
+     "duration_seconds": 3000, "ts": "2026-07-01T10:48:00Z"},
     {"event": "step_skipped", "session_id": "w-1", "step": "reviewer",
      "iter_name": "goal-w-iter-1", "ts": "2026-07-01T10:48:01Z"},
     {"event": "dispatch_wait", "session_id": "w-1", "agent": "browser-qa-agent",
@@ -626,8 +664,15 @@ def _self_test() -> int:
         if it1["wall_seconds"] != 5160:  # 10:00:00 → 11:26:00
             print(f"FAIL: iter-1 wall {it1['wall_seconds']} != 5160", file=sys.stderr)
             return 1
-        if it1["agents"]["developer"]["seconds"] != 2400:
-            print("FAIL: developer seconds attribution", file=sys.stderr)
+        # SPEED-13: active_seconds (1800) preferred over duration_seconds (2400)
+        if it1["agents"]["developer"]["seconds"] != 1800:
+            print("FAIL: developer active-seconds attribution", file=sys.stderr)
+            return 1
+        if it1["quota_sleep_seconds"] != 600:
+            print("FAIL: quota_pause_end attribution", file=sys.stderr)
+            return 1
+        if it1["engine_steps"].get("lean-pipeline") != 3000:
+            print(f"FAIL: engine_steps {it1['engine_steps']}", file=sys.stderr)
             return 1
         if it1["skipped_steps"] != ["reviewer"]:
             print(f"FAIL: skipped steps {it1['skipped_steps']}", file=sys.stderr)
@@ -643,7 +688,8 @@ def _self_test() -> int:
             return 1
         text = render_wall_text(report)
         for needle in ("goal-w-iter-1", "developer", "resume-skipped: reviewer",
-                       "pump-wait", "incomplete/interrupted"):
+                       "pump-wait", "incomplete/interrupted",
+                       "[engine] lean-pipeline", "quota-pauses"):
             if needle not in text:
                 print(f"FAIL: wall render missing '{needle}'", file=sys.stderr)
                 return 1
diff --git a/incredible_auto_dev/scripts/automation/lib/closure_gate.py b/incredible_auto_dev/scripts/automation/lib/closure_gate.py
new file mode 100644
index 0000000..d9329e2
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/lib/closure_gate.py
@@ -0,0 +1,764 @@
+#!/usr/bin/env python3
+"""closure_gate.py — deterministic phase-closure gate (SPEED-17).
+
+Replaces the phase-closure-auditor LLM dispatch for the default path. The
+agent's Steps 1-4 were re-reads and existence/count/cross-consistency checks
+over artifacts that already gated the pipeline upstream — no new judgment —
+so they are mechanized here. The agent stays on disk as the escape hatch:
+`CHAIN_CLOSURE_LLM=true` makes phase-closure-check.sh dispatch it instead.
+
+Checks (mirroring agents/phase-closure-auditor/body.md Steps 1-4 and
+.claude/skills/phase-closure-gate.md):
+  1. Pipeline gate verdicts — review / QA / audit reports must exist and carry
+     a passing verdict (same parser the pipeline itself uses: lib/verdicts.py).
+     FAIL or absent => CLOSURE-FAIL naming the report (they already gated
+     upstream; absence here means the pipeline is inconsistent).
+  2. UI artifact existence (all 6, both branches) and, when the plan says
+     `Frontend Present: yes`, content checks: >5 content lines, no N/A stubs,
+     no placeholder markers, what-to-click has >=3 numbered non-vague steps,
+     ui-test-results not all-SKIPPED-without-a-documented-reason.
+  3. Backend-only claim guard — port of common.sh check_backend_only_claim
+     (user-visible-changes claims "no visible changes" while frontend files
+     changed): blocking on a frontend phase, WARN on a backend-only one.
+  4. Vagueness — only OBJECTIVE vagueness blocks (placeholder markers and the
+     bare "Test the form"-class what-to-click steps). Anything subtler is a
+     WARN line: upstream QA live-audits and the downstream evaluator
+     evidence-walk cover subtle vagueness.
+
+Writes reports/phase-<phase>-closure-verdict.md in the frozen format the
+pipeline greps (`closure_verdict_passes` in lib/common.sh): the FIRST line is
+`**Verdict:** CLOSURE-PASS` or `**Verdict:** CLOSURE-FAIL`.
+
+Exit codes: 0 = CLOSURE-PASS, 1 = CLOSURE-FAIL (verdict file written in both
+cases), 2 = usage/environment error (no verdict written).
+
+Usage:
+  closure_gate.py <phase-name> --repo-root <path>
+  closure_gate.py self-test
+"""
+from __future__ import annotations
+
+import datetime
+import json
+import re
+import subprocess
+import sys
+from pathlib import Path
+
+sys.path.insert(0, str(Path(__file__).resolve().parent))
+
+import goal_lint  # noqa: E402  (vague-term list — single source, NEED-3)
+import verdicts  # noqa: E402  (same verdict parser the pipeline gates use)
+from merge_ui_test_results import parse_rows, file_top_verdict  # noqa: E402
+
+# The 6 UI visibility artifacts (agents/phase-closure-auditor/body.md Step 2).
+UI_ARTIFACTS = [
+    "implementation-summary",
+    "user-visible-changes",
+    "ui-surface-map",
+    "ui-test-plan",
+    "ui-test-results",
+    "what-to-click",
+]
+
+# Objective placeholder markers (skill "Vagueness Detection" + SPEED-17 list).
+_PLACEHOLDER_RE = re.compile(
+    r"\bTODO\b|\bTBD\b|<fill|\bFILL IN\b|\blorem\b|\bxxx+\b", re.IGNORECASE
+)
+
+# N/A-stub / backend-only claim markers — the same set check_backend_only_claim
+# greps (lib/common.sh) so both layers agree on what a backend-only claim is.
+_BACKEND_CLAIM_RE = re.compile(
+    r"backend-only|no user-visible|no visible changes|frontend present:\s*no",
+    re.IGNORECASE,
+)
+
+# Frontend file patterns — mirror of detect_frontend_changes (lib/common.sh).
+_FRONTEND_FILE_RE = re.compile(
+    r"(\.tsx$|\.jsx$|\.vue$|\.svelte$|/components/|/pages/|/views/|/screens/"
+    r"|\.module\.css$|\.module\.scss$)"
+)
+
+_NUMBERED_STEP_RE = re.compile(r"^\s*\d+[.)]")
+
+# A step is "objectively vague" only when it is a bare generic-verb +
+# generic-object phrase ("Test the form", "Verify it works", "Check the page
+# loads properly"). Steps that merely CONTAIN a vague term but also carry
+# specifics stay WARN — see the module docstring, point 4.
+_GENERIC_STEP_RE = re.compile(
+    r"^(?:please\s+)?(?:test|verify|check|try|open|click|use|run|ensure|confirm)\s+"
+    r"(?:that\s+)?(?:the\s+|a\s+|an\s+)?"
+    r"(?:forms?|pages?|apps?|applications?|buttons?|ui|sites?|websites?|"
+    r"features?|it|everything|stuff|things?|works?)"
+    r"(?:\s+(?:works?|loads?|functions?|renders?))?"
+    r"(?:\s+(?:well|properly|correctly|fine|as\s+expected))?\s*[.!]?$",
+    re.IGNORECASE,
+)
+
+# Tokens that make a step concrete enough to be beyond this gate's reach.
+_SPECIFIC_TOKEN_RE = re.compile(r"[\d\"'`/=$#§→]|->|https?:|expect", re.IGNORECASE)
+
+# A documented reason for an all-SKIPPED browser-QA file. Accepts the house
+# conventions: a `**Reason:**` line, a `## Reason` section, or the browser-infra
+# taxonomy strings bqa_results_infra_reason greps (lib/replay-lane.sh).
+_REASON_LINE_RE = re.compile(r"\*\*Reason:\*\*\s*(\S.*)$", re.MULTILINE)
+_REASON_SECTION_RE = re.compile(r"^##\s+Reason\s*\n+(\S.*)$", re.MULTILINE)
+_INFRA_REASON_RE = re.compile(
+    r"(browser infrastructure failure|chrome (?:mcp )?did not become ready"
+    r"|chrome (?:mcp )?(?:not |un)available|frontend (?:is )?not (?:running|available)"
+    r"|frontend not running)[^|\n]*",
+    re.IGNORECASE,
+)
+
+
+# ── pure helpers ──────────────────────────────────────────────────────────────
+
+def content_lines(text: str) -> int:
+    """Count content lines: non-blank, not a markdown header, not a bare
+    horizontal rule, not an HTML comment line."""
+    n = 0
+    for line in text.splitlines():
+        s = line.strip()
+        if not s or s.startswith("#") or s.startswith("<!--") or set(s) <= {"-"}:
+            continue
+        n += 1
+    return n
+
+
+def frontend_present(plan_text: str) -> bool:
+    """Mirror of detect_frontend_in_plan (lib/common.sh)."""
+    if re.search(r"frontend present:\s*yes", plan_text, re.IGNORECASE):
+        return True
+    return bool(re.search(r"frontend present\s*\n\s*yes", plan_text, re.IGNORECASE))
+
+
+def numbered_steps(text: str) -> list[str]:
+    return [ln for ln in text.splitlines() if _NUMBERED_STEP_RE.match(ln)]
+
+
+def step_text(line: str) -> str:
+    """Strip the leading number and markdown emphasis from a step line."""
+    s = re.sub(r"^\s*\d+[.)]\s*", "", line).strip()
+    return s.strip("*_ ").strip()
+
+
+def classify_step(line: str) -> str:
+    """'blocking' | 'warn' | 'ok' for one numbered what-to-click step."""
+    s = step_text(line)
+    if _GENERIC_STEP_RE.match(s):
+        return "blocking"
+    if goal_lint._VAGUE_RE.search(s) and not _SPECIFIC_TOKEN_RE.search(s):
+        return "blocking"
+    if goal_lint._VAGUE_RE.search(s):
+        return "warn"
+    return "ok"
+
+
+def all_skipped(results_text: str) -> bool:
+    """True when the ui-test-results file shows no PASS/FAIL execution at all."""
+    rows = parse_rows(results_text)
+    row_verdicts = [r["verdict"] for r in rows if r["verdict"]]
+    if row_verdicts:
+        return not any(v in ("PASS", "FAIL") for v in row_verdicts)
+    return file_top_verdict(results_text) == "SKIPPED"
+
+
+def skip_reason(results_text: str) -> str | None:
+    """Extract a documented reason for an all-SKIPPED run, if any."""
+    m = _REASON_LINE_RE.search(results_text)
+    if m:
+        return m.group(1).strip()
+    m = _REASON_SECTION_RE.search(results_text)
+    if m:
+        return m.group(1).strip()
+    m = _INFRA_REASON_RE.search(results_text)
+    if m:
+        return m.group(0).strip()
+    return None
+
+
+def placeholder_hits(text: str) -> list[str]:
+    """Placeholder markers on non-comment lines, as 'marker (line N)' strings."""
+    hits: list[str] = []
+    for i, line in enumerate(text.splitlines(), 1):
+        if line.strip().startswith("<!--"):
+            continue
+        for m in _PLACEHOLDER_RE.finditer(line):
+            hits.append(f"{m.group(0)} (line {i})")
+    return hits
+
+
+def frontend_files_changed(repo_root: Path, phase: str) -> bool:
+    """Port of detect_frontend_changes: status.json changed_files first,
+    git diff fallback. Errors conservatively mean 'no frontend change'."""
+    status_file = repo_root / "runs" / phase / "status.json"
+    if status_file.is_file():
+        try:
+            changed = json.loads(status_file.read_text(encoding="utf-8")).get(
+                "changed_files", []
+            )
+        except (json.JSONDecodeError, OSError):
+            changed = []
+        if changed:
+            return any(_FRONTEND_FILE_RE.search(f) for f in changed)
+    try:
+        out = subprocess.run(
+            ["git", "-C", str(repo_root), "diff", "--name-only", "HEAD"],
+            capture_output=True, text=True, timeout=30, check=False,
+        ).stdout
+    except (OSError, subprocess.SubprocessError):
+        return False
+    return any(_FRONTEND_FILE_RE.search(f) for f in out.splitlines())
+
+
+# ── the gate ──────────────────────────────────────────────────────────────────
+
+class GateResult:
+    def __init__(self) -> None:
+        self.blocking: list[tuple[str, str]] = []  # (issue, remediation)
+        self.warns: list[str] = []
+        self.gate_rows: list[tuple[str, str, str]] = []   # (artifact, status, verdict)
+        self.ui_rows: list[tuple[str, str, str, str, str]] = []
+        self.crossref: list[str] = []
+
+    @property
+    def verdict(self) -> str:
+        return "CLOSURE-FAIL" if self.blocking else "CLOSURE-PASS"
+
+
+def _read(path: Path) -> str | None:
+    try:
+        return path.read_text(encoding="utf-8")
+    except OSError:
+        return None
+
+
+def run_gate(phase: str, repo_root: Path) -> GateResult:
+    r = GateResult()
+    reports = repo_root / "reports"
+
+    # ── Step 1: pipeline gate verdicts (already gated upstream) ──────────────
+    gates = [
+        ("Review report", repo_root / "reports" / "reviews" / f"{phase}-review.md"),
+        ("QA report", repo_root / "reports" / "qa" / f"{phase}-qa.md"),
+        ("Audit report", repo_root / "docs" / "handoffs" / f"{phase}-audit.md"),
+    ]
+    for label, path in gates:
+        rel = path.relative_to(repo_root)
+        if not path.is_file():
+            r.gate_rows.append((f"{label} (`{rel}`)", "missing", "FAIL"))
+            r.blocking.append((
+                f"{label} missing: `{rel}`",
+                "Pipeline gates not passed — complete the upstream pipeline "
+                f"stage that writes `{rel}` before re-running closure.",
+            ))
+        elif not verdicts.check_verdict_file(str(path)):
+            r.gate_rows.append((f"{label} (`{rel}`)", "exists", "FAIL"))
+            r.blocking.append((
+                f"{label} does not carry a passing verdict: `{rel}`",
+                "Pipeline gates not passed — this report already gated the "
+                "pipeline upstream; a non-passing verdict here means the "
+                "pipeline is inconsistent. Re-run the failing stage.",
+            ))
+        else:
+            r.gate_rows.append((f"{label} (`{rel}`)", "exists", "PASS"))
+
+    # ── Frontend Present branch ──────────────────────────────────────────────
+    plan_path = repo_root / "runs" / phase / "plan.md"
+    plan_text = _read(plan_path)
+    if plan_text is None:
+        r.blocking.append((
+            f"Execution plan missing: `runs/{phase}/plan.md`",
+            f"Run `./scripts/automation/run-phase.sh {phase}` so the "
+            "orchestrator writes the plan (it carries `Frontend Present:`).",
+        ))
+        is_frontend = False
+    else:
+        is_frontend = frontend_present(plan_text)
+    r.crossref.append(
+        f"Frontend Present: {'yes' if is_frontend else 'no'}"
+        + ("" if plan_text is not None else " (plan missing — defaulted)")
+    )
+
+    # ── Step 2: UI artifact existence + content ──────────────────────────────
+    artifact_texts: dict[str, str | None] = {}
+    for name in UI_ARTIFACTS:
+        path = reports / f"phase-{phase}-{name}.md"
+        text = _read(path)
+        artifact_texts[name] = text
+        fname = f"{name}.md"
+        if text is None:
+            r.ui_rows.append((fname, "no", "-", "-", "MISSING"))
+            r.blocking.append((
+                f"UI artifact missing: `reports/phase-{phase}-{name}.md`",
+                "Re-run the pipeline step that writes it (ui-impact / "
+                "ui-test-design / browser-qa), or for a backend-only phase "
+                "let run-phase.sh write the N/A stubs (write_na_ui_artifacts).",
+            ))
+            continue
+        if not is_frontend:
+            # N/A stubs acceptable — existence is the whole requirement.
+            r.ui_rows.append((fname, "yes", "n/a (stub ok)", "n/a", "OK"))
+            continue
+
+        lines = content_lines(text)
+        nonempty = lines > 5
+        stub = bool(_BACKEND_CLAIM_RE.search(text)) and lines <= 5
+        holders = placeholder_hits(text)
+        status = "OK"
+        if stub:
+            status = "VAGUE"
+            r.blocking.append((
+                f"`phase-{phase}-{name}.md` is an N/A/backend-only stub but the "
+                "plan says Frontend Present: yes",
+                "Regenerate the artifact with real content for this frontend "
+                "phase (re-run the producing pipeline step).",
+            ))
+        elif not nonempty:
+            status = "VAGUE"
+            r.blocking.append((
+                f"`phase-{phase}-{name}.md` has ≤5 content lines "
+                f"({lines} non-blank, non-header) for a frontend phase",
+                "Regenerate the artifact with real content (re-run the "
+                "producing pipeline step).",
+            ))
+        if holders:
+            status = "VAGUE"
+            shown = ", ".join(holders[:3])
+            r.blocking.append((
+                f"`phase-{phase}-{name}.md` contains placeholder markers: {shown}",
+                "Replace placeholders with real content and re-run closure.",
+            ))
+        r.ui_rows.append((
+            fname, "yes", "yes" if nonempty else "no",
+            "no" if (holders or stub) else "yes", status,
+        ))
+
+    # ── Steps 3-4: cross-reference checks (frontend phases only) ─────────────
+    if is_frontend:
+        _crossref_frontend(phase, repo_root, artifact_texts, r)
+    else:
+        r.crossref.append(
+            "Backend-only phase: N/A stubs accepted; cross-reference checks "
+            "not applicable."
+        )
+        # Backend-only claim guard still worth a WARN if frontend files moved.
+        if frontend_files_changed(repo_root, phase):
+            r.warns.append(
+                "Plan says Frontend Present: no but frontend-looking files "
+                "changed this phase — check the plan flag (WARN only: the "
+                "evaluator evidence-walk covers this)."
+            )
+
+    # ── UX regression report (optional; FAIL already gated by run-phase.sh) ──
+    ux_path = reports / f"phase-{phase}-ux-regression.md"
+    ux_text = _read(ux_path)
+    if ux_text is None:
+        r.crossref.append("UX regression report: not present (acceptable).")
+    elif re.search(r"^\*\*Verdict:\*\* UX-REGRESSION-FAIL", ux_text, re.MULTILINE):
+        r.blocking.append((
+            f"UX regression report is UX-REGRESSION-FAIL: `reports/phase-{phase}-ux-regression.md`",
+            "This verdict already gates the pipeline (run-phase.sh) — a FAIL "
+            "surviving to closure means the pipeline is inconsistent. Fix the "
+            "flagged regressions and re-run ux-regression-phase.sh.",
+        ))
+        r.crossref.append("UX regression report: FAIL (blocking).")
+    elif re.search(r"^\*\*Verdict:\*\* UX-REGRESSION-WARN", ux_text, re.MULTILINE):
+        r.warns.append("UX regression report carries UX-REGRESSION-WARN (non-blocking).")
+        r.crossref.append("UX regression report: WARN (non-blocking).")
+    else:
+        r.crossref.append("UX regression report: present, not FAIL.")
+
+    return r
+
+
+def _crossref_frontend(
+    phase: str, repo_root: Path, texts: dict[str, str | None], r: GateResult
+) -> None:
+    # what-to-click: >=3 numbered steps, none objectively vague.
+    wtc = texts.get("what-to-click")
+    if wtc is not None:
+        steps = numbered_steps(wtc)
+        if len(steps) < 3:
+            r.blocking.append((
+                f"`phase-{phase}-what-to-click.md` has {len(steps)} numbered "
+                "step(s); ≥3 required",
+                "Re-run ui-test-design-phase.sh so the operator guide has at "
+                "least 3 concrete numbered steps with expected outcomes.",
+            ))
+        r.crossref.append(f"what-to-click numbered steps: {len(steps)} (≥3 required)")
+        vague_block = [step_text(s) for s in steps if classify_step(s) == "blocking"]
+        vague_warn = [step_text(s) for s in steps if classify_step(s) == "warn"]
+        if vague_block:
+            shown = "; ".join(f'"{s}"' for s in vague_block[:3])
+            r.blocking.append((
... [diff_bound] incredible_auto_dev/scripts/automation/lib/closure_gate.py: 370 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/scripts/automation/lib/common.sh b/incredible_auto_dev/scripts/automation/lib/common.sh
index 7a0206e..477c08e 100644
--- a/incredible_auto_dev/scripts/automation/lib/common.sh
+++ b/incredible_auto_dev/scripts/automation/lib/common.sh
@@ -878,6 +878,47 @@ escalate_model_off() {
   return 0
 }
 
+# ── Wall-clock iteration budget (SPEED-15, warn-first) ────────────────────────
+# CHAIN_ITER_TIME_BUDGET_SECONDS (default 0 = off; suggested operator value
+# 5400) + CHAIN_ITER_BUDGET_MODE (warn|trim, default warn). Checks run at step
+# boundaries ONLY — never mid-agent. warn: the first exceeded check logs loudly
+# and emits one iter_budget telemetry event per process. trim (opt-in): callers
+# may ALSO consult iter_budget_exceeded to skip showcase-class steps; the trim
+# ladder never touches developer/reviewer/evaluator/gates/confirm. The start
+# epoch crosses the engine→executor process boundary via CHAIN_ITER_START_EPOCH.
+
+iter_budget_init() {  # $1 = iteration start epoch (falls back to the exported one, then now)
+  _ITER_BUDGET_T0="${1:-${CHAIN_ITER_START_EPOCH:-$(date +%s)}}"
+  [[ "$_ITER_BUDGET_T0" =~ ^[0-9]+$ ]] || _ITER_BUDGET_T0="$(date +%s)"
+  _ITER_BUDGET_WARNED=""
+}
+
+iter_budget_exceeded() {
+  local budget="${CHAIN_ITER_TIME_BUDGET_SECONDS:-0}"
+  [[ "$budget" =~ ^[0-9]+$ && "$budget" -gt 0 && -n "${_ITER_BUDGET_T0:-}" ]] || return 1
+  (( $(date +%s) - _ITER_BUDGET_T0 > budget ))
+}
+
+iter_budget_check() {  # $1 = step label. Always returns 0 (a signal, never a gate).
+  iter_budget_exceeded || return 0
+  local elapsed=$(( $(date +%s) - ${_ITER_BUDGET_T0:-$(date +%s)} ))
+  if [[ -z "${_ITER_BUDGET_WARNED:-}" ]]; then
+    _ITER_BUDGET_WARNED=1
+    echo "[iter-budget] This iteration has run ${elapsed}s — over the ${CHAIN_ITER_TIME_BUDGET_SECONDS:-0}s budget (checked at: ${1:-?}; mode: ${CHAIN_ITER_BUDGET_MODE:-warn})." >&2
+    if declare -F record_telemetry_event >/dev/null 2>&1; then
+      record_telemetry_event "iter_budget" "$(printf '{"budget":%d,"elapsed":%d,"mode":"%s","at_step":"%s"}' \
+        "${CHAIN_ITER_TIME_BUDGET_SECONDS:-0}" "$elapsed" "${CHAIN_ITER_BUDGET_MODE:-warn}" "${1:-?}")" || true
+    fi
+  fi
+  return 0
+}
+
+# trim-mode consult: true only when the operator opted into trim AND the budget
+# is exceeded. Callers use it to skip showcase-class steps with a loud log.
+iter_budget_trim_active() {
+  [[ "${CHAIN_ITER_BUDGET_MODE:-warn}" == "trim" ]] && iter_budget_exceeded
+}
+
 # ── Hardening cadence (SPEED-4) ───────────────────────────────────────────────
 # The sharpened depth rubric makes lean the default; the cadence guarantees a
 # periodic full hardening pass so audit coverage cannot silently vanish on a
@@ -887,15 +928,18 @@ escalate_model_off() {
 # re-entry cannot double-count.
 
 # goal_lean_streak <session_dir> <current_iter>
-# Echoes the count of consecutive trailing `lean` dispatches over
-# iter-(N-1)..iter-1. A missing file or any non-lean value breaks the streak.
+# Echoes the count of consecutive trailing non-full dispatches over
+# iter-(N-1)..iter-1. A missing file or a `full` value breaks the streak.
 # iter-0 (baseline) is never counted — the loop floor is iter-1.
+# SPEED-9: `evidence` dispatches continue the streak like `lean` — they run no
+# audit either, so the hardening cadence must keep counting toward its next
+# full pass rather than resetting on an evidence hop.
 goal_lean_streak() {
   local session_dir="$1" current_iter="$2"
   local streak=0 i v
   for (( i = current_iter - 1; i >= 1; i-- )); do
     v="$(cat "$session_dir/iter-$i/depth-dispatched" 2>/dev/null || true)"
-    [[ "$v" == "lean" ]] || break
+    [[ "$v" == "lean" || "$v" == "evidence" ]] || break
     streak=$((streak + 1))
   done
   echo "$streak"
@@ -904,12 +948,15 @@ goal_lean_streak() {
 # goal_cadence_forces_full <streak> <current_iter>
 # True iff the hardening cadence demands a full pass now: K>0 AND
 # current_iter>K (never fires in a session's opening window, where iter-0 is
-# the baseline) AND streak>=K. K = CHAIN_HARDENING_CADENCE, default 4, 0
-# disables the cadence entirely.
+# the baseline) AND streak>=K. K = CHAIN_HARDENING_CADENCE, default 6, 0
+# disables the cadence entirely. (SPEED-10 raised the default 4→6: with the
+# full-trigger allowlist keeping the ESCALATE/REGRESSION/structural paths
+# always-full, the cadence is a periodic audit backstop, not the primary
+# trigger — at K=4 it materially drove the 4-of-6-full waste.)
 goal_cadence_forces_full() {
   local streak="$1" current_iter="$2"
-  local k="${CHAIN_HARDENING_CADENCE:-4}"
-  [[ "$k" =~ ^[0-9]+$ ]] || k=4
+  local k="${CHAIN_HARDENING_CADENCE:-6}"
+  [[ "$k" =~ ^[0-9]+$ ]] || k=6
   (( k > 0 && current_iter > k && streak >= k ))
 }
 
diff --git a/incredible_auto_dev/scripts/automation/lib/goal-gates.sh b/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
index 796a0ba..3e5b134 100644
--- a/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
+++ b/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
@@ -100,6 +100,27 @@ goal_gate_build_diff_artifacts() {
   return 0
 }
 
+# SPEED-14: deterministic "did this iteration change the product at all?" probe.
+# Same pathspec discipline as goal_gate_build_diff_artifacts above (bookkeeping
+# namespaces excluded, both layers: tracked diff + untracked enumeration).
+# Returns 0 ONLY when the tracked diff vs the snapshot is empty AND no untracked
+# product files exist. Missing snapshot or any git error → 1 (fail-safe: treat
+# as "changed" so nothing gets skipped on bad data).
+# $1 snapshot_sha   $2 repo_root
+goal_product_diff_empty() {
+  local snapshot_sha="$1" repo_root="$2"
+  [[ -n "$snapshot_sha" && -n "$repo_root" ]] || return 1
+  local _ex
+  local _scan_pathspec=(".")
+  for _ex in $CHAIN_SCAN_BOOKKEEPING_EXCLUDES; do
+    _scan_pathspec+=(":(exclude)$_ex")
+  done
+  local _tracked _untracked
+  _tracked=$(git -C "$repo_root" diff --name-only "$snapshot_sha" -- "${_scan_pathspec[@]}" 2>/dev/null) || return 1
+  _untracked=$(git -C "$repo_root" ls-files --others --exclude-standard -- "${_scan_pathspec[@]}" 2>/dev/null) || return 1
+  [[ -z "$_tracked" && -z "$_untracked" ]]
+}
+
 # Deterministic achievement gate. Writes $1/gate-report.md. Returns 0 iff every
 # check passes. Args:
 #   $1 iter_dir  $2 journey_history  $3 coherence_md  $4 coherence_expected(true|false)
diff --git a/incredible_auto_dev/scripts/automation/lib/goal_gate.py b/incredible_auto_dev/scripts/automation/lib/goal_gate.py
index 2da62d7..729c53a 100644
--- a/incredible_auto_dev/scripts/automation/lib/goal_gate.py
+++ b/incredible_auto_dev/scripts/automation/lib/goal_gate.py
@@ -421,6 +421,16 @@ def _self_test() -> int:
         assert cmd_coherence(str(coh_fail), False) == 1
         assert cmd_coherence(str(coh_stub), False) == 0, "stub PASS may gate CONTINUE"
         assert cmd_coherence(str(coh_stub), True) == 1, "stub PASS must not certify done"
+        # SPEED-14: the zero-change deterministic PASS is a reasoned verdict
+        # (empty product diff ⇒ no drift possible), NOT a crash stub — it stays
+        # valid for GOAL_ACHIEVED certification.
+        coh_zero = d / "c5.md"; coh_zero.write_text(
+            "**Verdict:** COHERENCE-PASS\n\n(Zero-change iteration: the product diff since the "
+            "iteration snapshot is empty — nothing to audit. Deterministic pass without dispatch; "
+            "set CHAIN_ZERO_CHANGE_SKIPS=false to always dispatch.)\n",
+            encoding="utf-8")
+        assert cmd_coherence(str(coh_zero), False) == 0, "zero-change PASS gates CONTINUE"
+        assert cmd_coherence(str(coh_zero), True) == 0, "zero-change PASS stays valid for certification (SPEED-14)"
         assert cmd_coherence(str(d / "nope.md"), True) == 2
 
         res_ok = d / "r1.md"; res_ok.write_text("| T1 | n | ui | P1 | e | a | PASS | x.png |\n", encoding="utf-8")
diff --git a/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh b/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh
index 30a3e74..86c354c 100644
--- a/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh
+++ b/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh
@@ -14,7 +14,9 @@
 # Requires CHAIN_DISPATCH_DIR (created + exported by run-goal.sh).
 #
 # Channel protocol (one request per agent call):
-#   _interactive_invoke writes   <dir>/req.XXXXXX.ready = {agent, prompt, cwd, res_path,
+#   _interactive_invoke writes   <dir>/req.<lane>-XXXXXX.ready = {agent, prompt, cwd, res_path,
+#     (lane digit = CHAIN_DISPATCH_LANE, default 5; showcase forks use 9 so the
+#      sorted pickup glob serves spine work first — SPEED-12)
 #                                out, usage_path, model?}
 #   the pump reads it, dispatches subagent_type=<agent> (passing `model` as the
 #   Agent tool's model param when present), writes the subagent's final message
@@ -98,6 +100,64 @@ _interactive_dispatch_wait_event() {
          "${agent:-unattributed}" "$_status" "$_wait" "$_run")"
 }
 
+# SPEED-12: is the pump that wrote this .started claim PROVABLY dead?
+# Returns 0 ONLY for a same-host claim whose pid is gone or was recycled
+# (echoing the human-readable reason); any missing field, foreign host, or
+# unprovable verdict returns 1 (assume alive — the timeout nets still apply).
+# Same protocol-v3 fields the own-claim REL-3 fast path reads.
+_dispatch_claim_pump_dead() {
+  local _cs="$1"
+  local _cpid _chost _cstt _clocal _cstt_now
+  _cpid="$(sed -n 's/^pid=//p' "$_cs" 2>/dev/null | head -n1 | tr -dc 0-9)"
+  _chost="$(sed -n 's/^host=//p' "$_cs" 2>/dev/null | head -n1)"
+  _cstt="$(sed -n 's/^starttime=//p' "$_cs" 2>/dev/null | head -n1 | tr -dc 0-9)"
+  [[ -n "$_cpid" && -n "$_chost" ]] || return 1
+  _clocal="$(hostname 2>/dev/null || uname -n 2>/dev/null || echo '?')"
+  [[ "$_chost" == "$_clocal" ]] || return 1
+  if ! kill -0 "$_cpid" 2>/dev/null && [[ ! -e "/proc/$_cpid" ]]; then
+    echo "pump pid $_cpid is dead"
+    return 0
+  fi
+  if [[ -n "$_cstt" && -r "/proc/$_cpid/stat" ]]; then
+    _cstt_now="$(sed 's/.*) //' "/proc/$_cpid/stat" 2>/dev/null | awk '{print $20}')"
+    if [[ -n "$_cstt_now" && "$_cstt_now" != "$_cstt" ]]; then
+      echo "pump pid $_cpid was recycled (proc starttime $_cstt_now != claimed $_cstt)"
+      return 0
+    fi
+  fi
+  return 1
+}
+
+# SPEED-12: iteration-boundary janitor for the dispatch channel. Deletes ONLY
+# provably-dead-pump .started claims and orphaned .started markers older than
+# the flat inflight cap whose request/result files are gone. Live claims (a
+# busy pump's, the forked showcase tail's) are never touched. Before this,
+# .started files were cleared only at engine start — one stale claim made
+# every later unclaimed dispatch wait unbounded (the 18h iter-7 class).
+dispatch_channel_janitor() {
+  local _jd="${CHAIN_DISPATCH_DIR:-}"
+  [[ -n "$_jd" && -d "$_jd" ]] || return 0
+  local _js _jreason _jage _jnow _jbase
+  _jnow="$(date +%s)"
+  for _js in "$_jd"/req.*.started; do
+    [[ -e "$_js" ]] || continue
+    if _jreason="$(_dispatch_claim_pump_dead "$_js")"; then
+      echo "[interactive-dispatch] janitor: clearing dead-pump claim $(basename "$_js") (${_jreason})." >&2
+      rm -f "$_js" 2>/dev/null || true
+      continue
+    fi
+    _jbase="${_js%.started}"
+    if [[ ! -e "$_jbase.ready" && ! -e "$_jbase.res" && ! -e "$_jbase" ]]; then
+      _jage=$(( _jnow - $(stat -c %Y "$_js" 2>/dev/null || stat -f %m "$_js" 2>/dev/null || echo "$_jnow") ))
+      if [[ "$_jage" -gt "${CHAIN_DISPATCH_INFLIGHT_TIMEOUT:-7200}" ]]; then
+        echo "[interactive-dispatch] janitor: clearing orphaned claim $(basename "$_js") (no request/result files, ${_jage}s old)." >&2
+        rm -f "$_js" 2>/dev/null || true
+      fi
+    fi
+  done
+  return 0
+}
+
 # A pump usage sidecar is valid when its `.usage` is an object whose four token
 # fields are ALL non-negative numbers (strings/negatives/missing keys, or a file
 # that isn't JSON at all, are invalid — the caller warns once and skips). Extra
@@ -216,7 +276,7 @@ _interactive_invoke() {
 
   local req res out usage_f pfile _built
   local _requeued=""
-  local _dispatch_start _claim_epoch hb started _now _ref _age _busy _s
+  local _dispatch_start _claim_epoch hb started _now _ref _age _busy _s _dead_reason _busy_cap
   # REL-3 (protocol v3): pump identity parsed once per claim from the .started
   # marker; liveness is then one kill -0 per poll. _local_host resolved once.
   local _pump_checked="" _pump_pid="" _pump_host="" _pump_stt="" _pump_gone _stt_now _local_host
@@ -227,7 +287,11 @@ _interactive_invoke() {
   while :; do
     _claim_epoch=""
     _pump_checked=""; _pump_pid=""; _pump_host=""; _pump_stt=""
-    req="$(mktemp "$dir/req.XXXXXX")"
+    # SPEED-12 priority lanes: bash glob expansion is lexicographically sorted,
+    # and the pump picks up req.*.ready in glob order — so a lane digit in the
+    # name gives spine dispatches (lane 5, the default) pickup priority over
+    # background showcase dispatches (lane 9) with ZERO pump-side changes.
+    req="$(mktemp "$dir/req.${CHAIN_DISPATCH_LANE:-5}-XXXXXX")"
     res="$req.res"
     out="$req.out"
     usage_f="$req.usage"
@@ -362,8 +426,20 @@ print(json.dumps(d))' < "$pfile" > "$req" || true
       elif [[ -f "$hb" ]]; then
         # Tier A: not yet claimed → pickup timeout against the heartbeat, UNLESS the
         # pump is demonstrably alive and busy on another request (a sibling .started).
+        # SPEED-12: a sibling claim only proves "busy" if the pump that wrote it
+        # still exists — a provably-dead sibling marker is deleted on the spot
+        # (it can never complete, and it used to make this wait UNBOUNDED: the
+        # 18h iter-7 stall was exactly a dead pump's stale sibling claim).
         _busy=""
-        for _s in "$dir"/req.*.started; do [[ -e "$_s" ]] && { _busy=1; break; }; done
+        for _s in "$dir"/req.*.started; do
+          [[ -e "$_s" ]] || continue
+          if _dead_reason="$(_dispatch_claim_pump_dead "$_s")"; then
+            echo "[interactive-dispatch] clearing stale sibling claim $(basename "$_s"): ${_dead_reason}." >&2
+            rm -f "$_s" 2>/dev/null || true
+            continue
+          fi
+          _busy=1; break
+        done
         if [[ -z "$_busy" ]]; then
           _ref="$(stat -c %Y "$hb" 2>/dev/null || stat -f %m "$hb" 2>/dev/null || echo "$_now")"
           _age=$(( _now - _ref ))
@@ -374,6 +450,21 @@ print(json.dumps(d))' < "$pfile" > "$req" || true
             _interactive_dispatch_wait_event "pickup-timeout" "${DISPATCH_UNAVAILABLE_EXIT_CODE:-70}"
             return "${DISPATCH_UNAVAILABLE_EXIT_CODE:-70}"
           fi
+        else
+          # SPEED-12: pump genuinely alive+busy elsewhere — still BOUND this
+          # unclaimed wait. Default = flat inflight cap; 0 = unlimited (the
+          # pre-SPEED-12 behavior). Abort is resumable (AWAITING_PUMP).
+          _busy_cap="${CHAIN_DISPATCH_PICKUP_BUSY_TIMEOUT:-${CHAIN_DISPATCH_INFLIGHT_TIMEOUT:-7200}}"
+          if [[ "$_busy_cap" =~ ^[0-9]+$ && "$_busy_cap" -gt 0 ]]; then
+            _age=$(( _now - _dispatch_start ))
+            if [[ "$_age" -gt "$_busy_cap" ]]; then
+              echo "[interactive-dispatch] request for agent '$agent' unclaimed for ${_age}s while the pump was busy elsewhere (> ${_busy_cap}s) — aborting resumably. Set CHAIN_DISPATCH_PICKUP_BUSY_TIMEOUT=0 to disable this cap." >&2
+              printf 'pickup-busy timeout: %ss unclaimed while pump busy (agent=%s)\n' "$_age" "$agent" > "$dir/.awaiting-pump"
+              rm -f "$req.ready" 2>/dev/null || true
+              _interactive_dispatch_wait_event "pickup-busy-timeout" "${DISPATCH_UNAVAILABLE_EXIT_CODE:-70}"
+              return "${DISPATCH_UNAVAILABLE_EXIT_CODE:-70}"
+            fi
+          fi
         fi
       fi
       sleep "$CHAIN_DISPATCH_POLL_SECONDS"
@@ -955,6 +1046,96 @@ _interactive_dispatch_self_test() {
   fi
   rm -rf "$d"
 
+  # Test 20 (SPEED-12) — DEAD sibling claim: an unclaimed dispatch must clear
+  # the provably-dead sibling .started on the spot and then complete normally
+  # once the (live) pump answers.
+  d="$(mktemp -d)"; export CHAIN_DISPATCH_DIR="$d"; rc=0
+  CHAIN_PUMP_HEARTBEAT_TIMEOUT=3600; CHAIN_DISPATCH_INFLIGHT_TIMEOUT=3600; CHAIN_DISPATCH_POLL_SECONDS=0.2
+  ( exit 0 ) & _vpid=$!; wait "$_vpid" 2>/dev/null || true
+  printf 'pid=%s\nhost=%s\n' "$_vpid" "$_lhost" > "$d/req.5-stale1.started"
+  ( for _ in $(seq 1 60); do
+      touch "$d/.pump-alive"
+      r="$(find "$d" -maxdepth 1 -name 'req.*.ready' 2>/dev/null | head -1)"
+      if [[ -n "$r" && ! -f "$d/req.5-stale1.started" ]]; then
+        touch "${r%.ready}.started"; sleep 0.3; echo 0 > "${r%.ready}.res"; break
+      fi
+      sleep 0.1
+    done ) &
+  pump=$!
+  _interactive_invoke -p "dead sibling cleared" 2>"$d/err" || rc=$?
+  wait "$pump" 2>/dev/null || true
+  if [[ "$rc" -eq 0 && ! -f "$d/req.5-stale1.started" ]] \
+     && grep -q 'clearing stale sibling claim' "$d/err"; then
+    echo "  PASS interactive-dispatch: dead sibling claim cleared, dispatch completes (SPEED-12)"
+  else
+    echo "  FAIL interactive-dispatch: dead-sibling clearing (rc=$rc stale-exists=$([[ -f "$d/req.5-stale1.started" ]] && echo yes || echo no) stderr=$(head -c 160 "$d/err" 2>/dev/null))"; fails=1
+  fi
+  rm -rf "$d"
+
+  # Test 21 (SPEED-12) — busy-pickup cap: a LIVE sibling claim keeps _busy
+  # honest, and the previously-unbounded wait now aborts resumably at the cap.
+  d="$(mktemp -d)"; export CHAIN_DISPATCH_DIR="$d"; rc=0
+  CHAIN_PUMP_HEARTBEAT_TIMEOUT=3600; CHAIN_DISPATCH_INFLIGHT_TIMEOUT=3600; CHAIN_DISPATCH_POLL_SECONDS=0.2
+  CHAIN_DISPATCH_PICKUP_BUSY_TIMEOUT=1
+  _vstt="$(sed 's/.*) //' "/proc/$$/stat" 2>/dev/null | awk '{print $20}')"
+  printf 'pid=%s\nhost=%s\nstarttime=%s\n' "$$" "$_lhost" "$_vstt" > "$d/req.5-live01.started"
+  ( for _ in $(seq 1 40); do touch "$d/.pump-alive"; sleep 0.1; done ) &
+  pump=$!
+  _interactive_invoke -p "busy pickup cap" 2>"$d/err" || rc=$?
+  kill "$pump" 2>/dev/null || true; wait "$pump" 2>/dev/null || true
+  unset CHAIN_DISPATCH_PICKUP_BUSY_TIMEOUT
+  if [[ "$rc" -eq "${DISPATCH_UNAVAILABLE_EXIT_CODE:-70}" && -f "$d/req.5-live01.started" ]] \
+     && grep -q 'busy elsewhere' "$d/err" && grep -q 'pickup-busy timeout' "$d/.awaiting-pump" 2>/dev/null; then
+    echo "  PASS interactive-dispatch: busy-pickup cap bounds the unclaimed wait, live sibling untouched (SPEED-12)"
+  else
+    echo "  FAIL interactive-dispatch: busy-pickup cap (rc=$rc stderr=$(head -c 160 "$d/err" 2>/dev/null))"; fails=1
+  fi
+  rm -rf "$d"
+
+  # Test 22 (SPEED-12) — priority lanes: default mints lane 5, CHAIN_DISPATCH_LANE=9
+  # mints lane 9, and the pickup glob orders lane 5 before lane 9.
+  d="$(mktemp -d)"
+  : > "$d/req.9-aaaaaa.ready"; : > "$d/req.5-aaaaaa.ready"
+  _first=""
+  for _s in "$d"/req.*.ready; do _first="$_s"; break; done
+  d2="$(mktemp -d)"; export CHAIN_DISPATCH_DIR="$d2"; rc=0
+  CHAIN_DISPATCH_POLL_SECONDS=0.2
+  ( for _ in $(seq 1 60); do
+      r="$(find "$d2" -maxdepth 1 -name 'req.*.ready' 2>/dev/null | head -1)"
+      if [[ -n "$r" ]]; then touch "${r%.ready}.started"; echo 0 > "${r%.ready}.res"; break; fi
+      sleep 0.1
+    done ) &
+  pump=$!
+  CHAIN_DISPATCH_LANE=9 _interactive_invoke -p "lane nine" 2>/dev/null || rc=$?
+  wait "$pump" 2>/dev/null || true
+  _lane9="$(find "$d2" -maxdepth 1 -name 'req.9-*.out' -o -maxdepth 1 -name 'req.9-*.res' 2>/dev/null | head -1)"
+  if [[ "$(basename "$_first")" == req.5-* && "$rc" -eq 0 ]]; then
+    echo "  PASS interactive-dispatch: lane 5 sorts before lane 9; CHAIN_DISPATCH_LANE=9 dispatch round-trips (SPEED-12)"
+  else
+    echo "  FAIL interactive-dispatch: priority lanes (first=$(basename "${_first:-none}") rc=$rc lane9=${_lane9:-?})"; fails=1
+  fi
+  rm -rf "$d" "$d2"
+
+  # Test 23 (SPEED-12) — janitor: dead-pid claim cleared, live claim kept,
+  # aged orphan cleared, fresh orphan kept.
+  d="$(mktemp -d)"; export CHAIN_DISPATCH_DIR="$d"
+  ( exit 0 ) & _vpid=$!; wait "$_vpid" 2>/dev/null || true
+  printf 'pid=%s\nhost=%s\n' "$_vpid" "$_lhost" > "$d/req.5-dead01.started"
+  _vstt="$(sed 's/.*) //' "/proc/$$/stat" 2>/dev/null | awk '{print $20}')"
+  printf 'pid=%s\nhost=%s\nstarttime=%s\n' "$$" "$_lhost" "$_vstt" > "$d/req.5-live02.started"
+  : > "$d/req.5-live02.ready"
+  : > "$d/req.5-orph01.started"
+  touch -d '3 hours ago' "$d/req.5-orph01.started" 2>/dev/null || true
+  : > "$d/req.5-orph02.started"
+  CHAIN_DISPATCH_INFLIGHT_TIMEOUT=7200 dispatch_channel_janitor 2>"$d/jlog" || true
+  if [[ ! -f "$d/req.5-dead01.started" && -f "$d/req.5-live02.started" \
+        && ! -f "$d/req.5-orph01.started" && -f "$d/req.5-orph02.started" ]]; then
+    echo "  PASS interactive-dispatch: janitor clears dead + aged-orphan claims, keeps live + fresh (SPEED-12)"
+  else
+    echo "  FAIL interactive-dispatch: janitor (dead=$([[ -f "$d/req.5-dead01.started" ]] && echo kept || echo cleared) live=$([[ -f "$d/req.5-live02.started" ]] && echo kept || echo cleared) orph-old=$([[ -f "$d/req.5-orph01.started" ]] && echo kept || echo cleared) orph-new=$([[ -f "$d/req.5-orph02.started" ]] && echo kept || echo cleared))"; fails=1
+  fi
+  rm -rf "$d"
+
   if [[ "$fails" -eq 0 ]]; then echo "interactive-dispatch self-test: OK"; else echo "interactive-dispatch self-test: FAILED"; fi
   return "$fails"
 }
```
