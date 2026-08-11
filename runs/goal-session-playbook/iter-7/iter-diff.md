# Iteration diff (bounded)

Files changed: 11. Shown in full: 8.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/frontend/app/desk/page.tsx` (65 lines not shown)
- `apps/backend/app/research/desk_playbook_backscan.py` (168 lines not shown)
- `apps/backend/tests/test_desk_playbook_backscan.py` (193 lines not shown)

```diff
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index 4bd17a3..f2c22aa 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -98,7 +98,7 @@ import os
 from datetime import date, datetime, timedelta, timezone
 from typing import Callable
 
-from fastapi import APIRouter, Depends, HTTPException
+from fastapi import APIRouter, Depends, HTTPException, Query
 from pydantic import BaseModel
 
 from ..config import CONFIG
@@ -124,6 +124,12 @@ from .desk_forward_compute import DeskForwardComputeManager
 from .desk_forward_log import ForwardRunStore, resolve_desk_forward_log_dir
 from .desk_forward_pins import resolve_desk_forward_pins
 from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
+from .desk_playbook_backscan import (
+    BackscanRunStore,
+    DeskPlaybookBackscanComputeManager,
+    plan_backscan,
+    resolve_desk_playbook_backscan_log_dir,
+)
 from .desk_playbook_compute import DeskPlaybookComputeManager
 from .desk_playbook_log import PlaybookRunStore, resolve_desk_playbook_log_dir
 from .desk_screen import ScreenStore, resolve_desk_screen_dir
@@ -177,6 +183,10 @@ _desk_deep_backfill_manager = DeskDeepBackfillComputeManager()
 # dependency shape as its five siblings above.
 _desk_playbook_compute_manager = DeskPlaybookComputeManager()
 
+# The desk playbook back-scan compute manager (Era B2, J-07) — the SAME shape as its six siblings
+# above.
+_desk_playbook_backscan_manager = DeskPlaybookBackscanComputeManager()
+
 
 def get_universe_store() -> UniverseStore:
     """The universe store rooted at the config-owned directory (``TAPEOLOGY_DESK_UNIVERSE_DIR``
@@ -1146,6 +1156,114 @@ def get_playbook_runs(
     }
 
 
+# --- The playbook back-scan (Era B2, J-07) — a plan-preview GET plus a trigger/poll/cancel trio
+# mirroring the deep-backfill trio exactly, plus ONE durable read mirroring
+# `GET /research/desk/backfill/runs`. See `desk_playbook_backscan.py` for the plan/walker/manager/
+# ledger mechanics this only wires up. ---------------------------------------------------------------
+
+
+def get_desk_playbook_backscan_manager() -> DeskPlaybookBackscanComputeManager:
+    """The desk playbook back-scan compute manager — a FastAPI dependency (the
+    ``get_desk_deep_backfill_manager`` pattern) so a test overrides it outright via
+    ``app.dependency_overrides`` for complete test-to-test isolation."""
+    return _desk_playbook_backscan_manager
+
+
+def get_backscan_run_store() -> BackscanRunStore:
+    """The back-scan run log store rooted at a bare env-var-or-sibling-of-the-universe-dir default
+    (zero new ``Config`` field — see ``desk_playbook_backscan.resolve_desk_playbook_backscan_log_
+    dir``) — the ``get_deep_backfill_run_store`` pattern."""
+    return BackscanRunStore(resolve_desk_playbook_backscan_log_dir(CONFIG.desk_universe_dir_resolved()))
+
+
+@router.get("/playbook/backscan/plan")
+def get_desk_playbook_backscan_plan(
+    from_: str = Query(..., alias="from"),
+    to: str = Query(...),
+    universe_store: UniverseStore = Depends(get_universe_store),
+    bar_store: BarStore = Depends(get_bar_store),
+    playbook_store: PlaybookStore = Depends(get_playbook_store),
+) -> dict:
+    """What a back-scan over ``[from, to]`` would find, said before anything is clicked: every
+    calendar day classified ``recorded_at_current_signature`` or ``missing_at_current_signature``
+    against the playbook store's OWN already-recorded files at the CURRENT
+    ``playbook_input_signature``. A plain read: writes nothing, triggers nothing, and performs zero
+    ``BarStore`` bar-content reads (``plan_backscan``'s own metadata-only contract — T-7)."""
+    records, _errors = universe_store.list()
+    members = list(records[-1]["members"]) if records else []
+    return plan_backscan(from_, to, bar_store, members, CONFIG.config_fingerprint(), playbook_store)
+
+
+class BackscanComputeRequest(BaseModel):
+    """Body for ``POST /research/desk/playbook/backscan/compute`` — both dates are REQUIRED, the
+    ``DeepBackfillComputeRequest`` convention: a back-scan's range is exactly the thing an operator
+    is deciding, never a wall-clock-derived default."""
+
+    from_day: str
+    to_day: str
+
+
+@router.post("/playbook/backscan/compute")
+def trigger_desk_playbook_backscan_compute(
+    body: BackscanComputeRequest,
+    universe_store: UniverseStore = Depends(get_universe_store),
+    bar_store: BarStore = Depends(get_bar_store),
+    playbook_store: PlaybookStore = Depends(get_playbook_store),
+    manager: DeskPlaybookBackscanComputeManager = Depends(get_desk_playbook_backscan_manager),
+    run_store: BackscanRunStore = Depends(get_backscan_run_store),
+) -> dict:
+    """Start the single-flight back-scan job over ``[body.from_day, body.to_day]``, or — if one is
+    already running — return it UNCHANGED (``started: False``, never a second concurrent job).
+    Returns ``{"started": bool, "compute": <snapshot>}``; the walk runs on a background worker
+    thread, off this request, so this route returns immediately however long the scan takes. Every
+    planned date is walked through the ONE shared ``run_playbook_and_record`` entry point — a date
+    already recorded reuses with zero detector calls, so re-triggering the SAME range resumes
+    rather than restarting."""
+    return manager.trigger(
+        body.from_day, body.to_day, universe_store, bar_store, CONFIG, playbook_store, run_store,
+    )
+
+
+@router.get("/playbook/backscan/compute")
+def get_desk_playbook_backscan_compute(
+    manager: DeskPlaybookBackscanComputeManager = Depends(get_desk_playbook_backscan_manager),
+) -> dict:
+    """The back-scan job's current/last snapshot, served VERBATIM — ALWAYS a body (``status ==
+    "idle"`` before any compute has ever run this process). A plain read: never triggers a compute
+    as a side effect (GET-never-computes)."""
+    return manager.snapshot()
+
+
+@router.post("/playbook/backscan/compute/cancel")
+def cancel_desk_playbook_backscan_compute(
+    manager: DeskPlaybookBackscanComputeManager = Depends(get_desk_playbook_backscan_manager),
+) -> dict:
+    """Cancel the in-flight back-scan (cooperative — observed on a date boundary). ``409`` when
+    idle — mirrors ``cancel_desk_deep_backfill_compute``'s own 409-when-not-running shape. A date
+    already in flight finishes and is recorded before the walk stops."""
+    snapshot = manager.snapshot()
+    if snapshot["status"] != "running":
+        raise HTTPException(status_code=409, detail="no desk playbook back-scan is currently running")
+    manager.cancel()
+    return {"cancelling": True}
+
+
+@router.get("/playbook/backscan/runs")
+def get_desk_playbook_backscan_runs(store: BackscanRunStore = Depends(get_backscan_run_store)) -> dict:
+    """``{"runs": [...], "latest": <record>|null, "integrity_errors": [...]}`` — the durable log of
+    what every back-scan attempted, surviving the compute manager's process-scoped snapshot. An
+    explicit HTTP 200 honest-empty payload before any back-scan has ever reached a LOGGED terminal
+    state, never a 404. A cancel that measured nothing never appears here at all (the module
+    docstring's own terminal-state-only rule) — its absence looks identical to a run that never
+    happened, by design."""
+    records, errors = store.list()
+    return {
+        "runs": records,
+        "latest": records[-1] if records else None,
+        "integrity_errors": errors,
+    }
+
+
 # --- Coverage-index reconciliation (J-10, goal-desk-iter-14) — a trigger/poll/cancel trio mirroring
 # the top-up compute trio exactly, plus ONE durable read mirroring ``GET /research/desk/topup/runs``.
 # See ``desk_index_reconcile.py`` for the classify/repair/record mechanics this only wires up. -------
diff --git a/apps/backend/tests/test_desk_playbook_detect.py b/apps/backend/tests/test_desk_playbook_detect.py
index 9f37909..aa75178 100644
--- a/apps/backend/tests/test_desk_playbook_detect.py
+++ b/apps/backend/tests/test_desk_playbook_detect.py
@@ -1273,6 +1273,52 @@ def test_range_trade_degenerate_trigger_reference_below_the_range_low_fails_clos
     assert control[0]["invalidation_price"] < control[0]["entry"]
 
 
+def _range_trade_degenerate_reference_bars_short(reference_low: float) -> list[RawBar]:
+    """The SHORT-side mirror of ``_range_trade_degenerate_reference_bars`` (goal-playbook-iter-7,
+    TC-12): the canonical short arming (slots 0-6, `SH` = 205.0) followed by a reference bar whose
+    high (205.3) stays within the 0.50 hold tolerance of `SH` (205.3 <= 205.5) without itself
+    resetting the arming, then a lower-low reversal bar. ``reference_low`` is the ONLY value that
+    differs between the degenerate fixture (205.1, at/above `SH`) and its control (204.5, below
+    `SH`) -- the ``reference_high``-only-varies precedent, mirrored onto the field the SHORT side's
+    own trigger reference (`prev_bar.low`) actually reads."""
+    bars = _canonical_range_trade_short_bars("RTDS")[:7]
+    bars.append(_bar("RTDS", E_OPEN + 7 * 300.0, 205.2, 205.3, reference_low, 205.2, 1000))
+    bars.append(_bar("RTDS", E_OPEN + 8 * 300.0, 205.0, 205.2, 204.0, 204.2, 2000))
+    bars.append(_bar("RTDS", E_OPEN + 9 * 300.0, 204.2, 204.4, 203.9, 204.1, 1000))
+    return bars
+
+
+def test_range_trade_degenerate_trigger_reference_at_or_above_the_range_high_fails_closed_short():
+    """TC-12 (goal-playbook-iter-7): the SHORT-side mirror of
+    ``test_range_trade_degenerate_trigger_reference_below_the_range_low_fails_closed`` -- spec
+    §3.7's Edge cases "degenerate trigger reference" clause is symmetric (module source: ``T <= SL``
+    long / ``T >= SH`` short): a short whose structural invalidation would land AT OR BELOW its own
+    entry, i.e. recorded born-invalidated, is voided fail-closed. Control: the SAME bars with the
+    reference bar's low lowered from 205.1 to 204.5 (just below `SH`) fire exactly one coherent
+    short signal, proving the degeneracy clause specifically -- not the arming or the reversal
+    predicate -- is the rejecter (the fixture is byte-identical between the two calls except for
+    that one field, the iter-6 lesson: a bare `results == []` alone proves nothing)."""
+    degenerate = _range_trade_degenerate_reference_bars_short(205.1)
+    assert detect_range_trade(
+        degenerate, _RANGE_TRADE_BASELINE, "RTDS", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    ) == []
+    # What the spec's formula WOULD have produced there, computed here from the fixture itself:
+    # T = low[7] = 205.1 >= SH = 205.0 -> invalidation 204.97, i.e. at/below the entry.
+    would_be_trigger, session_high = degenerate[7].low, max(bar.high for bar in degenerate[:7])
+    assert would_be_trigger >= session_high
+    assert session_high + _PARAMS["stop_pad_frac"] * (session_high - would_be_trigger) < would_be_trigger
+
+    control = detect_range_trade(
+        _range_trade_degenerate_reference_bars_short(204.5), _RANGE_TRADE_BASELINE, "RTDS",
+        SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert len(control) == 1
+    assert control[0]["side"] == "short"
+    assert control[0]["trigger_price"] == pytest.approx(204.5)
+    assert control[0]["invalidation_price"] == pytest.approx(205.15)
+    assert control[0]["invalidation_price"] > control[0]["entry"]
+
+
 # --- TC-3: a strict break beyond the low zone by more than PLAYBOOK_RANGE_HOLD_TOL_MBR dissolves
 # range-mode -- no signal, PAIRED with a gate-relaxed control (range_hold_tol_mbr widened) proving
 # the hold-tolerance gate specifically is the rejecter (the iter-4 lesson: `results == []` alone
diff --git a/apps/backend/tests/test_desk_refresh_chain_guard.py b/apps/backend/tests/test_desk_refresh_chain_guard.py
index cecf3da..58365e9 100644
--- a/apps/backend/tests/test_desk_refresh_chain_guard.py
+++ b/apps/backend/tests/test_desk_refresh_chain_guard.py
@@ -118,8 +118,27 @@ _UNIVERSE_FETCH_PATH = "/research/desk/universe/fetch"
 # precedent). The timeout is untouched -- the playbook section has no wait-tick of its own; it is
 # not part of the chain. Neither new effect can reach a trigger, which is the property the scan
 # below actually polices; the counts are here so that scan stays provably complete.
-_EXPECTED_EFFECT_COUNT = 17
-_EXPECTED_INTERVAL_COUNT = 6
+#
+# 17 -> 19 and 6 -> 7 for the Backscan section (goal-playbook-iter-7, J-07) -- the SEVENTH compute
+# manager (`desk_playbook_backscan.py`), entirely independent of the refresh chain (a back-scan is
+# its own operator act over a From/To RANGE, never a sixth/seventh chain step) and independent of
+# the Playbook Signals section beside it (its own From/To state, never the single session-date
+# input). +1 effect: the plan-preview read keyed on [backscanFromDay, backscanToDay] -- the
+# `DeepBackfillControl` plan-effect precedent verbatim (a plain GET, issues no compute, performs
+# zero BarStore bar-content reads). +1 effect, +1 interval: the back-scan compute poll, mirroring
+# the RECONCILIATION poll's shape exactly (registered only while `status === "running"` -- this
+# manager's own snapshot enum has no distinct "cancelling" state either, matching the deep-backfill
+# shape rather than the playbook-compute one) and, on the SAME terminal tick, refreshing the durable
+# run ledger once (the reconciliation poll's own "keep the last known state, never fabricate one on
+# a failed refetch" discipline) -- this is also why the runs table needs no THIRD effect of its own.
+# The mount-time seed for this SEVENTH compute snapshot AND its run-ledger read both joined the
+# EXISTING mount effect (no new effect for either, the `forwardComputeRef` mirror precedent extended
+# to an un-keyed durable-log read, exactly as the top-up/reconcile/screen run-ledger reads above
+# already do). The timeout is untouched -- the Backscan section has no wait-tick of its own; it is
+# not part of the chain. Neither new effect can reach a trigger, which is the property the scan
+# below actually polices; the counts are here so that scan stays provably complete.
+_EXPECTED_EFFECT_COUNT = 19
+_EXPECTED_INTERVAL_COUNT = 7
 _EXPECTED_TIMEOUT_COUNT = 1
 
 # Everything that could start real work. The chain's own driver is included: an effect that calls
@@ -140,6 +159,10 @@ _TRIGGER_CALLS = (
     # mirrors the handleTriggerForward(/triggerDeskForwardCompute( pair immediately above exactly.
     "handleTriggerPlaybook(",
     "triggerDeskPlaybookCompute(",
+    # goal-playbook-iter-7 (J-07): the Backscan section's own handler/client pair -- the SAME
+    # mirror, one level down.
+    "handleTriggerBackscan(",
+    "triggerDeskPlaybookBackscanCompute(",
 )
 
 # Machinery that can invoke a handler without a user click. None of it is used by this page today;
@@ -392,8 +415,8 @@ def test_the_chain_adds_no_extra_poll_and_one_sleep():
     assert intervals == _EXPECTED_INTERVAL_COUNT, (
         f"apps/frontend/app/desk/page.tsx has {intervals} setInterval calls, expected "
         f"{_EXPECTED_INTERVAL_COUNT} (one per compute manager: screen, top-up, reconcile, "
-        "forward) -- the refresh chain must not poll the backend itself; it observes the state "
-        "those effects already keep current"
+        "forward, deep backfill, playbook, back-scan) -- the refresh chain must not poll the "
+        "backend itself; it observes the state those effects already keep current"
     )
     assert timeouts == _EXPECTED_TIMEOUT_COUNT, (
         f"apps/frontend/app/desk/page.tsx has {timeouts} setTimeout calls, expected "
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index 2f2714d..0c328bf 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -171,6 +171,14 @@ def test_structure_prefill_guard_can_fail_on_a_seeded_violation():
 # `nominal_risk_mbr`/`second_top_rvol_vs_first` verbatim. Bar-count/int-count fields
 # (`tops_separation_bars`, `low_zone_touches`, `high_zone_touches`) stay OUT of this list, following
 # the `base_bars`/`cup_bars`/`decline_bars` precedent -- a plain count is not a price.
+# goal-playbook-iter-7 (J-07): extended AGAIN for the new Backscan panel's own served numerics --
+# `BackscanPlanPreview` renders `plan.total`/`plan.missing` verbatim, `BackscanControl`'s running
+# indicator renders `compute.planned_total`/`compute.completed` verbatim, and
+# `BackscanOutcomeCounts` (shared by the live progress view AND every runs-table row) renders
+# `outcomes.reused`/`outcomes.recorded`/`outcomes.refused_non_session`/`outcomes.failed` verbatim --
+# none of these are prices, but the IN SCOPE contract for this panel is "no client-side arithmetic
+# on served numerics" full stop, so they are guarded here on the same footing as the price fields
+# above rather than left to convention.
 _PRICE_ARITHMETIC_FIELDS = (
     r"row\.(?:distance_bps|price_low|price_high|reference_close"
     r"|opposite_band\.(?:distance_bps|price_low|price_high|band_score)"
@@ -186,6 +194,9 @@ _PRICE_ARITHMETIC_FIELDS = (
     r"|handle_duration_frac|cup_middle_third_rvol_median|cup_outer_third_rvol_median"
     r"|handle_rvol_median|decline_mbr|climax_rvol|bars_from_climax_to_trigger"
     r"|range_width_mbr|tops_gap_mbr|valley_depth_mbr|nominal_risk_mbr|second_top_rvol_vs_first)"
+    r"|plan\.(?:total|missing)"
+    r"|compute\.(?:planned_total|completed)"
+    r"|outcomes\.(?:reused|recorded|refused_non_session|failed)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 16b8b5a..bddea2c 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -25,12 +25,17 @@ import {
   fetchDeskSessions,
   fetchDeskTopupCompute,
   fetchDeskTopupRuns,
+  cancelDeskPlaybookBackscanCompute,
   cancelDeskPlaybookCompute,
   fetchDeskPlaybook,
+  fetchDeskPlaybookBackscanCompute,
+  fetchDeskPlaybookBackscanPlan,
+  fetchDeskPlaybookBackscanRuns,
   fetchDeskPlaybookCompute,
   fetchDeskPlaybookRuns,
   triggerDeskDeepBackfillCompute,
   triggerDeskForwardCompute,
+  triggerDeskPlaybookBackscanCompute,
   triggerDeskPlaybookCompute,
   triggerDeskReconcileCompute,
   triggerDeskScreenCompute,
@@ -51,6 +56,11 @@ import type {
   DeskForwardRunsListResult,
   DeskForwardTouch,
   DeskPlaybookAbsence,
+  DeskPlaybookBackscanComputeSnapshot,
+  DeskPlaybookBackscanOutcomeCounts,
+  DeskPlaybookBackscanPlan,
+  DeskPlaybookBackscanRun,
+  DeskPlaybookBackscanRunsListResult,
   DeskPlaybookComputeSnapshot,
   DeskPlaybookReadResult,
   DeskPlaybookRecord,
@@ -3487,6 +3497,253 @@ function DeepBackfillControl({
   );
 }
 
+// --- The playbook back-scan (Era B2, J-07) ---------------------------------------------------------
+// A resumable, cancel-safe bulk compute over a From/To session-date range, walking every planned
+// date through the SAME "Run Playbook" entry point (`desk_playbook_compute.run_playbook_and_record`)
+// the Playbook Signals section above already drives one date at a time. Wired exactly like
+// `DeepBackfillControl` (plan preview + trigger + live progress + Cancel), plus a runs table (the
+// `TopupRunsTable` precedent) since a back-scan run's outcome mix is the whole point of the feature.
+
+function BackscanOutcomeCounts({ outcomes }: { outcomes: DeskPlaybookBackscanOutcomeCounts }) {
+  return (
+    <span data-testid="desk-backscan-outcome-counts">
+      {fmt(outcomes.reused, 0)} reused · {fmt(outcomes.recorded, 0)} recorded ·{" "}
+      {fmt(outcomes.refused_non_session, 0)} refused · {fmt(outcomes.failed, 0)} failed
+    </span>
+  );
+}
+
+function BackscanPlanPreview({
+  plan,
+}: {
+  plan: { ok: boolean; data: DeskPlaybookBackscanPlan | null; error?: string } | null;
+}) {
+  if (plan === null) return null;
+  if (!plan.ok || plan.data === null) {
+    return (
+      <p data-testid="desk-backscan-plan-error" className="text-xs text-red-300">
+        {plan.error ?? "The back-scan plan could not be loaded."}
+      </p>
+    );
+  }
+  const data = plan.data;
+  return (
+    <div data-testid="desk-backscan-plan" className="w-full max-w-md text-center text-[11px] text-slate-500">
+      <p>
+        {fmt(data.total, 0)} date{data.total === 1 ? "" : "s"} planned · {fmt(data.missing, 0)} missing
+        at the current signature.
+      </p>
+      {data.dates.length > 0 && (
+        <ul data-testid="desk-backscan-plan-dates" className="mt-1 flex flex-wrap justify-center gap-1">
+          {data.dates.map((entry) => (
+            <li
+              key={entry.session_date}
+              data-testid="desk-backscan-plan-date-row"
+              className={
+                entry.status === "recorded_at_current_signature"
+                  ? "rounded border border-emerald-800/60 bg-emerald-950/40 px-1.5 py-0.5 text-emerald-300"
+                  : "rounded border border-slate-700 bg-slate-900/60 px-1.5 py-0.5 text-slate-400"
+              }
+            >
+              {entry.session_date}
+            </li>
+          ))}
+        </ul>
+      )}
+    </div>
+  );
+}
+
+interface BackscanControlProps {
+  compute: DeskPlaybookBackscanComputeSnapshot | null;
+  plan: { ok: boolean; data: DeskPlaybookBackscanPlan | null; error?: string } | null;
+  fromDay: string;
+  toDay: string;
+  onFromDayChange: (value: string) => void;
+  onToDayChange: (value: string) => void;
+  onTrigger: () => void;
+  triggering: boolean;
+  triggerError: string | null;
+  onCancel: () => void;
+  cancelRequested: boolean;
+  cancelError: string | null;
+}
+
+function BackscanControl({
+  compute,
+  plan,
+  fromDay,
+  toDay,
+  onFromDayChange,
+  onToDayChange,
+  onTrigger,
+  triggering,
+  triggerError,
+  onCancel,
+  cancelRequested,
+  cancelError,
+}: BackscanControlProps) {
+  const isRunning = compute?.status === "running";
+  const isError = compute?.status === "error";
+  const isCancelled = compute?.status === "cancelled";
+  const buttonLabel = isRunning ? "Back-scanning…" : isError ? "Retry Backscan" : "Run Backscan";
+  return (
+    <div data-testid="desk-backscan-control" className="flex flex-col items-center gap-1">
+      <div className="flex flex-wrap items-end justify-center gap-3">
+        <label className="flex flex-col items-center gap-1">
+          <span className="text-[11px] font-medium text-slate-500">Backscan from day</span>
+          <input
+            type="text"
+            inputMode="numeric"
+            data-testid="desk-backscan-from-input"
+            value={fromDay}
+            onChange={(e) => onFromDayChange(e.target.value)}
+            placeholder="yyyy-MM-dd"
+            disabled={isRunning}
+            className={ASOF_INPUT_CLASS}
+          />
+        </label>
+        <label className="flex flex-col items-center gap-1">
+          <span className="text-[11px] font-medium text-slate-500">Backscan to day</span>
+          <input
+            type="text"
+            inputMode="numeric"
+            data-testid="desk-backscan-to-input"
+            value={toDay}
+            onChange={(e) => onToDayChange(e.target.value)}
+            placeholder="yyyy-MM-dd"
+            disabled={isRunning}
+            className={ASOF_INPUT_CLASS}
+          />
+        </label>
+      </div>
+      <BackscanPlanPreview plan={plan} />
+      {isError && compute?.error && (
+        <p data-testid="desk-backscan-error" className="text-xs text-red-300">
+          {compute.error}
+        </p>
+      )}
+      {triggerError && (
+        <p data-testid="desk-backscan-trigger-error" className="text-xs text-red-300">
+          {triggerError}
+        </p>
+      )}
+      {isCancelled && (
+        <p data-testid="desk-backscan-cancelled" className="text-xs text-amber-200/70">
+          Backscan cancelled — dates already recorded before the cancel stay stored, and a later run
+          reads them from the store rather than walking them again.
+        </p>
+      )}
+      <button
+        type="button"
+        data-testid="desk-backscan-button"
+        onClick={onTrigger}
+        disabled={triggering || isRunning}
+        className={PRIMARY_BUTTON_CLASS}
+      >
+        {buttonLabel}
+      </button>
+      {isRunning && (
+        <div data-testid="desk-backscan-running" className="mt-1 flex flex-col items-center gap-1">
+          <p data-testid="desk-backscan-progress" className="text-xs text-amber-200/70">
+            <span
+              aria-hidden="true"
+              className="mr-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400 align-middle"
+            />
+            {fmt(compute.completed, 0)} / {fmt(compute.planned_total, 0)} dates ·{" "}
+            <BackscanOutcomeCounts outcomes={compute.outcomes} />
+          </p>
+          {compute.current_date && (
+            <p data-testid="desk-backscan-current" className="text-xs text-amber-200/70">
+              current date: {compute.current_date}
+            </p>
+          )}
+          <button
+            type="button"
+            data-testid="desk-backscan-cancel"
+            onClick={onCancel}
+            disabled={cancelRequested}
+            className={CANCEL_BUTTON_CLASS}
+          >
+            {cancelRequested ? "Cancelling — finishing the current date…" : "Cancel"}
+          </button>
+          {cancelError && (
+            <p data-testid="desk-backscan-cancel-error" className="text-xs text-red-300">
+              {cancelError}
+            </p>
+          )}
+        </div>
+      )}
+    </div>
+  );
+}
+
+function BackscanRunRow({ run }: { run: DeskPlaybookBackscanRun }) {
+  return (
+    <tr data-testid="desk-backscan-run-row" className="border-b border-slate-900">
+      <td className="px-2 py-1 text-left text-xs text-slate-300">
+        {run.from} → {run.to}
+      </td>
+      <td data-testid="desk-backscan-run-status" className="px-2 py-1 text-left text-xs text-slate-300">
+        {run.status}
+      </td>
+      <td className={HEADER_CELL}>
+        <BackscanOutcomeCounts outcomes={run.outcomes} />
+      </td>
+      <td className="px-2 py-1 text-left text-xs text-slate-500">{formatDateTimeET(run.started_at)}</td>
+    </tr>
+  );
+}
+
+function BackscanRunsTable({ runs }: { runs: DeskPlaybookBackscanRun[] }) {
+  if (runs.length === 0) {
+    return <EmptyState testid="desk-backscan-runs-empty" title="No back-scan runs recorded yet." />;
+  }
+  return (
+    <div className="overflow-x-auto">
+      <table data-testid="desk-backscan-runs-table" className="w-full border-collapse">
+        <thead>
+          <tr className="border-b border-slate-800">
+            <th className={HEADER_CELL_LEFT}>range</th>
+            <th className={HEADER_CELL_LEFT}>status</th>
+            <th className={HEADER_CELL}>outcomes</th>
+            <th className={HEADER_CELL_LEFT}>started</th>
+          </tr>
+        </thead>
+        <tbody>
+          {runs.map((run) => (
+            <BackscanRunRow key={run.run_id} run={run} />
+          ))}
+        </tbody>
+      </table>
+    </div>
+  );
+}
+
+function BackscanRunsSection({
+  result,
+}: {
+  result: { ok: boolean; data: DeskPlaybookBackscanRunsListResult | null; error?: string } | null;
+}) {
+  if (result === null) {
+    return <LoadingPanel testid="desk-backscan-runs-loading" />;
+  }
+  if (!result.ok || result.data === null) {
+    return (
+      <UnavailablePanel
+        testid="desk-backscan-runs-unavailable"
+        message={result.error ?? "The back-scan run history could not be loaded."}
+      />
+    );
+  }
+  return (
+    <div>
+      <BackscanRunsTable runs={result.data.runs} />
+      <IntegrityErrorsNote errors={result.data.integrity_errors} testid="desk-backscan-runs-integrity-errors" />
+    </div>
+  );
+}
+
 // era-desk-iter-14 (J-10): a third compute control, wired exactly like `TopupComputeControl` — the
 // operation has no per-pair counters (it is a single classify-repair-verify walk, not a walk over
 // many pairs), so the running indicator shows the compute's own `progress.phase` label instead of
@@ -5356,6 +5613,29 @@ export default function DeskPage() {
   const [selectedPlaybookSignal, setSelectedPlaybookSignal] = useState<string | null>(null);
   const playbookValidated = validatePlaybookSessionDay(playbookDateInput, sessionsResult);
 
+  // goal-playbook-iter-7 (J-07): the Backscan section's own state — entirely independent of the
+  // Playbook Signals section above (a back-scan is its own operator act over a From/To RANGE,
+  // never a variant of the single-date Run Playbook control). Blank From/To is a valid, honest
+  // state (the plan effect below simply does not fire) rather than a client-authored default —
+  // the operator names the range, exactly like the deep fine-bar backfill control above.
+  const [backscanFromDay, setBackscanFromDay] = useState("");
+  const [backscanToDay, setBackscanToDay] = useState("");
+  const [backscanPlan, setBackscanPlan] = useState<{
+    ok: boolean;
+    data: DeskPlaybookBackscanPlan | null;
+    error?: string;
+  } | null>(null);
+  const [backscanCompute, setBackscanCompute] = useState<DeskPlaybookBackscanComputeSnapshot | null>(null);
+  const [backscanRunsResult, setBackscanRunsResult] = useState<{
+    ok: boolean;
+    data: DeskPlaybookBackscanRunsListResult | null;
+    error?: string;
+  } | null>(null);
+  const [backscanTriggering, setBackscanTriggering] = useState(false);
+  const [backscanTriggerError, setBackscanTriggerError] = useState<string | null>(null);
+  const [backscanCancelRequested, setBackscanCancelRequested] = useState(false);
+  const [backscanCancelError, setBackscanCancelError] = useState<string | null>(null);
+
   // The chained refresh (see the REFRESH-CHAIN block above). `refreshChain` is plain state and is
   // deliberately NOT persisted: a reload clears it and nothing resumes, which is what keeps "every
   // run is an explicit operator act" true structurally rather than by convention. Whatever job was
@@ -5441,6 +5721,18 @@ export default function DeskPage() {
     fetchDeskPlaybookCompute().then((result) => {
       if (alive && result.ok) setPlaybookCompute(result.data);
     });
+    // goal-playbook-iter-7 (J-07): seeds the Backscan section's compute control mid-job or
+    // post-terminal, plus its durable run ledger — the SAME mount-seed precedent every other
+    // compute manager's snapshot above already follows, joined into this SAME effect (the page's
+    // effect census is pinned; see test_desk_refresh_chain_guard.py). The runs read joins here
+    // rather than opening its own effect because it answers a fixed, un-keyed question ("every
+    // back-scan run ever logged"), exactly like the top-up/reconcile/screen run-ledger reads above.
+    fetchDeskPlaybookBackscanCompute().then((result) => {
+      if (alive && result.ok) setBackscanCompute(result.data);
+    });
+    fetchDeskPlaybookBackscanRuns().then((result) => {
+      if (alive) setBackscanRunsResult(result);
+    });
     return () => {
       alive = false;
     };
@@ -6460,6 +6752,44 @@ export default function DeskPage() {
     return () => clearInterval(handle);
   }, [playbookCompute, playbookValidated.date]);
 
+  // goal-playbook-iter-7 (J-07): the Backscan section's own pre-click plan, re-read whenever its
+  // own From/To range changes — the `DeepBackfillControl` plan-effect precedent verbatim. A plain
+  // GET that performs zero BarStore bar-content reads and triggers nothing; a failed read leaves
+  // the last known plan untouched rather than blanking it.
+  useEffect(() => {
+    if (backscanFromDay === "" || backscanToDay === "") return;
+    let alive = true;
+    (async () => {
+      const result = await fetchDeskPlaybookBackscanPlan(backscanFromDay, backscanToDay);
+      if (alive) {
+        setBackscanPlan((previous) => (result.ok || previous === null || !previous.ok ? result : previous));
+      }
+    })();
+    return () => {
+      alive = false;
+    };
+  }, [backscanFromDay, backscanToDay]);
+
+  // Poll the back-scan job while running — the SEVENTH compute manager, wired exactly like the
+  // reconciliation poll above (on terminal, refresh the durable run ledger once — the SAME "keep
+  // the last known state, never fabricate one" discipline on a failed refetch). This is also what
+  // makes the runs table update the moment a triggered scan finishes, without a second poll or
+  // effect of its own.
+  useEffect(() => {
+    if (backscanCompute?.status !== "running") return;
+    const handle = setInterval(async () => {
+      const next = await fetchDeskPlaybookBackscanCompute();
+      if (next.ok) setBackscanCompute(next.data);
+      if (next.ok && next.data && next.data.status !== "running") {
+        const refreshed = await fetchDeskPlaybookBackscanRuns();
+        setBackscanRunsResult((previous) =>
+          refreshed.ok || previous === null || !previous.ok ? refreshed : previous,
+        );
+      }
+    }, 700);
+    return () => clearInterval(handle);
+  }, [backscanCompute]);
+
   // Forward-test era: the compute trigger/cancel pair — exact mirrors of the screen pair above,
   // placed here (after `displayedSnapshot`) because the no-argument form submits the DISPLAYED
   // snapshot's own id. Reachable from the panel's buttons and from the refresh chain's fifth
@@ -6558,6 +6888,54 @@ export default function DeskPage() {
     sessionDate: playbookValidated.date,
   };
 
+  // goal-playbook-iter-7 (J-07): the Backscan section's own trigger/cancel pair — the
+  // `DeepBackfillControl` pattern verbatim (both dates read straight from state; no derived
+  // validation the way the single-date Playbook Signals section needs, since an inverted or
+  // partial range is an honest empty plan/walk rather than a client-refused one — TC-17).
+  async function handleTriggerBackscan() {
+    setBackscanTriggering(true);
+    setBackscanTriggerError(null);
+    setBackscanCancelRequested(false);
+    setBackscanCancelError(null);
+    const result = await triggerDeskPlaybookBackscanCompute(backscanFromDay, backscanToDay);
+    setBackscanTriggering(false);
+    if (!result.ok || result.data === undefined) {
+      setBackscanTriggerError(result.error ?? "The back-scan could not be started.");
+      return;
... [diff_bound] apps/frontend/app/desk/page.tsx: 65 more diff lines omitted — Read the file for full detail
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index fb31950..b521329 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -17,6 +17,9 @@ import type {
   DeskForwardPinsResult,
   DeskForwardReadResult,
   DeskForwardRunsListResult,
+  DeskPlaybookBackscanComputeSnapshot,
+  DeskPlaybookBackscanPlan,
+  DeskPlaybookBackscanRunsListResult,
   DeskPlaybookComputeSnapshot,
   DeskPlaybookReadResult,
   DeskPlaybookRunsListResult,
@@ -1852,3 +1855,124 @@ export async function fetchDeskPlaybookRuns(sessionDate?: string): Promise<{
     return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// --- The playbook back-scan (Era B2, J-07) — a plan-preview GET plus a trigger/poll/cancel trio
+// mirroring the deep-backfill clients exactly, plus a durable runs read. --------------------------
+
+// GET /research/desk/playbook/backscan/plan?from=&to= — what a back-scan over the range WOULD
+// find, said before anything is clicked. Issues no compute and writes nothing.
+export async function fetchDeskPlaybookBackscanPlan(
+  fromDay: string,
+  toDay: string,
+): Promise<{ ok: boolean; data: DeskPlaybookBackscanPlan | null; error?: string }> {
+  try {
+    const res = await fetch(
+      `${API_BASE}/research/desk/playbook/backscan/plan?from=${encodeURIComponent(fromDay)}` +
+        `&to=${encodeURIComponent(toDay)}`,
+    );
+    if (res.ok) return { ok: true, data: (await res.json()) as DeskPlaybookBackscanPlan };
+    let error = "The back-scan plan could not be loaded.";
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
+
+// POST /research/desk/playbook/backscan/compute — start the single-flight back-scan job.
+// `started: false` means one was already running and this call adopted it, never that anything
+// failed.
+export async function triggerDeskPlaybookBackscanCompute(
+  fromDay: string,
+  toDay: string,
+): Promise<{
+  ok: boolean;
+  data?: { started: boolean; compute: DeskPlaybookBackscanComputeSnapshot };
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/playbook/backscan/compute`, {
+      method: "POST",
+      headers: { "Content-Type": "application/json" },
+      body: JSON.stringify({ from_day: fromDay, to_day: toDay }),
+    });
+    if (res.ok) {
+      const data = await res.json();
+      return { ok: true, data };
+    }
+    let error = "The back-scan could not be started.";
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
+export async function fetchDeskPlaybookBackscanCompute(): Promise<{
+  ok: boolean;
+  data: DeskPlaybookBackscanComputeSnapshot | null;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/playbook/backscan/compute`);
+    if (!res.ok) return { ok: false, data: null };
+    const data = await res.json();
+    return { ok: true, data: (data as DeskPlaybookBackscanComputeSnapshot | null) ?? null };
+  } catch {
+    return { ok: false, data: null };
+  }
+}
+
+export async function cancelDeskPlaybookBackscanCompute(): Promise<{ ok: boolean; error?: string }> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/playbook/backscan/compute/cancel`, {
+      method: "POST",
+    });
+    if (res.ok) return { ok: true };
+    let error = "The back-scan could not be cancelled.";
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
+// GET /research/desk/playbook/backscan/runs — the durable, append-only BACK-SCAN run log, served
+// VERBATIM. An honest-empty result is a valid `ok: true` outcome: a cancel that measured nothing
+// leaves no row at all (the module's own terminal-state-only rule).
+export async function fetchDeskPlaybookBackscanRuns(): Promise<{
+  ok: boolean;
+  data: DeskPlaybookBackscanRunsListResult | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/playbook/backscan/runs`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskPlaybookBackscanRunsListResult };
+    }
+    let error = "The back-scan run history could not be loaded.";
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
index e2da4bb..8e1cb09 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1679,6 +1679,67 @@ export interface DeskPlaybookRunsListResult {
   integrity_errors: { file: string; error: string }[];
 }
 
+// --- The playbook back-scan (Era B2, J-07) -- a plan preview + resumable/cancel-safe compute over
+// a From/To range, walking every planned date through the ONE existing shared playbook
+// detect+measure+record entry point. -------------------------------------------------------------
+
+/** `GET /research/desk/playbook/backscan/plan` -- what a back-scan over `[from, to]` would find,
+ * said before anything is clicked. Every calendar day in range, classified against the playbook
+ * store's own already-recorded files at the CURRENT `playbook_input_signature` -- pure and
+ * metadata-only, writes/triggers nothing. */
+export interface DeskPlaybookBackscanPlanDate {
+  session_date: string;
+  status: "recorded_at_current_signature" | "missing_at_current_signature";
+}
+
+export interface DeskPlaybookBackscanPlan {
+  from: string;
+  to: string;
+  playbook_input_signature: string;
+  dates: DeskPlaybookBackscanPlanDate[];
+  total: number;
+  missing: number;
+}
+
+export interface DeskPlaybookBackscanOutcomeCounts {
+  reused: number;
+  recorded: number;
+  refused_non_session: number;
+  failed: number;
+}
+
+/** The process-scoped snapshot of the single in-flight (or last-terminal) back-scan job. */
+export interface DeskPlaybookBackscanComputeSnapshot {
+  status: "idle" | "running" | "done" | "cancelled" | "error";
+  from: string | null;
+  to: string | null;
+  planned_total: number;
+  completed: number;
+  outcomes: DeskPlaybookBackscanOutcomeCounts;
+  current_date: string | null;
+  error: string | null;
+}
+
+// One terminal back-scan attempt, from the durable append-only run log -- survives the compute
+// manager's process-scoped snapshot. A cancel that measured nothing is never logged at all (the
+// module's own terminal-state-only rule; a partial cancel that recorded at least one date IS
+// logged, unlike the single-date playbook run log's own cancel-is-never-logged contract).
+export interface DeskPlaybookBackscanRun {
+  run_id: string;
+  from: string;
+  to: string;
+  started_at: string;
+  finished_at: string;
+  status: "done" | "cancelled" | "error";
+  outcomes: DeskPlaybookBackscanOutcomeCounts;
+}
+
+export interface DeskPlaybookBackscanRunsListResult {
+  runs: DeskPlaybookBackscanRun[];
+  latest: DeskPlaybookBackscanRun | null;
+  integrity_errors: { file: string; error: string }[];
+}
+
 // ONE registered universe membership snapshot's own served meta -- `UniverseStore.record`'s return
 // value verbatim (desk_universe.py's `meta` dict), which `POST /research/desk/universe/fetch`
 // serves under its `universe` key. Every field is the store's own; nothing here is derived. The
diff --git a/apps/backend/app/research/desk_playbook_backscan.py b/apps/backend/app/research/desk_playbook_backscan.py
new file mode 100644
index 0000000..ddea881
--- /dev/null
+++ b/apps/backend/app/research/desk_playbook_backscan.py
@@ -0,0 +1,562 @@
+"""The playbook back-scan (Era B2, J-07) -- one resumable, cancel-safe operator act that walks a
+date range through the ONE existing shared ``run_playbook_and_record`` entry point
+(``desk_playbook_compute.py:90``), so the playbook's own store fills in for every recorded session
+instead of one date at a time via the existing Run Playbook control.
+
+**Three concepts, one module (mirrors ``desk_deep_backfill.py``'s plan/walker/manager/ledger
+quartet, re-chunked to one calendar day instead of one bar-window chunk):**
+
+  * ``plan_backscan`` -- a PURE, metadata-only preview: every calendar day in ``[from_day, to_day]``
+    classified ``recorded_at_current_signature`` (a playbook record already exists at THIS EXACT
+    ``(day, playbook_input_signature)`` key) or ``missing_at_current_signature`` (it does not).
+  * ``run_backscan`` -- the SOLE walker; the manager's worker thread and nothing else calls it. Per
+    date it calls ``run_playbook_and_record`` (never a second implementation of detect+measure+
+    record) and classifies the honest outcome -- ``reused`` / ``recorded`` / ``refused_non_session``
+    / ``failed`` -- never aborting the whole walk on one date's failure. Cancel is cooperative,
+    observed on a date boundary (a date already in flight finishes and is recorded -- it has already
+    paid for its walk).
+  * ``DeskPlaybookBackscanComputeManager`` + ``BackscanRunStore`` -- the single-flight, cancellable,
+    progress-publishing job (the ``DeskPlaybookComputeManager``/``DeskDeepBackfillComputeManager``
+    shape verbatim) and its durable, terminal-state-only run ledger.
+
+**Why the plan walks EVERY calendar day, never ``desk_sessions.recorded_session_dates``.** That
+function calls ``BarStore.merged_bars`` (real bar CONTENT reads, bounded to
+``DESK_SESSION_ANCHOR_LIMIT`` members but still real reads) to prove session-ness -- exactly the
+cost this plan promises never to pay (T-7: "the plan GET is metadata-only"). ``plan_backscan``
+therefore does not try to know in advance which calendar days are genuine trading sessions at all;
+it resolves ONE ``playbook_input_signature`` (``compute_playbook_input_signature`` -- itself
+``list(include_bars=False)``-only, so ``BarStore`` is touched for record METADATA and never for bar
+content) and then answers, for every calendar day in range, "does the playbook store already hold a
+record at this exact key" -- a pure ``PlaybookStore`` file lookup, zero ``BarStore`` content reads.
+Whether a "missing" day is a genuine trading session that has simply never been walked, or a
+weekend/holiday that never will be, is not this GET's question to answer -- ``run_backscan``'s own
+per-date call into ``run_playbook_and_record`` (which DOES call ``desk_sessions.
+refuse_if_not_a_session``) is the one and only place that gets decided, and ``refused_non_session``
+exists in the outcome vocabulary precisely because the plan does not pre-filter it away.
+
+**Cancellation, and why it differs from the single-date playbook run log.**
+``desk_playbook_log.PlaybookRunStore`` treats a cancelled run as though it never happened (no ledger
+row at all) because a SINGLE-date compute that is cancelled mid-walk records nothing -- there is no
+partial progress to disclose. A back-scan is different: it is N independent per-date attempts, so a
+cancel after some dates have already completed genuinely measured something worth keeping (TC-5).
+But a cancel BEFORE any date completes is, again, indistinguishable from a run that never started
+(TC-10) -- so this module's ``BackscanRunStore`` writes a ``"cancelled"`` row only when
+``completed >= 1``; ``"done"``/``"error"`` always write, mirroring
+``desk_deep_backfill.DeepBackfillRunStore``'s three-terminal-state set exactly (never a fourth
+``"cancelled-with-nothing"`` state -- it is simply not logged).
+
+**Host-guard confinement (T-12).** The walk runs sequentially on ONE background worker thread inside
+the already-running server process -- no new process, no worker pool -- so it automatically inherits
+the process's own CPU affinity mask exactly the way ``desk_screen.py``'s bounded worker pool already
+documents for its own children. There is nothing here for a host-guard wrapper to confine beyond
+what already confines the whole process.
+
+**No second implementation of the measurement rail, no second implementation of session honesty.**
+Every date is walked through ``run_playbook_and_record`` verbatim; this module detects nothing,
+measures nothing, and re-derives no threshold -- see that function's own docstring for the
+detect/measure/record contract this module only orchestrates across a range.
+
+**Storage dirs -- no new ``Config`` field.** ``resolve_desk_playbook_backscan_log_dir`` mirrors
+``resolve_desk_playbook_log_dir``/``resolve_desk_deep_backfill_log_dir`` exactly: a bare
+``TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR`` env-var override, else a directory co-located as a
+SIBLING of the caller's own already-resolved universe directory."""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import os
+import threading
+import uuid
+from datetime import date, datetime, timedelta, timezone
+from pathlib import Path
+from typing import Callable
+
+from .bars import BarStore
+from .desk_playbook import (
+    PlaybookSessionRefused,
+    PlaybookStore,
+    compute_playbook_input_signature,
+)
+from .desk_playbook_compute import run_playbook_and_record
+from .desk_universe import UniverseStore
+
+__all__ = [
+    "BackscanRunIntegrityError",
+    "BackscanRunStore",
+    "DeskPlaybookBackscanComputeManager",
+    "PlaybookNotScopedError",
+    "plan_backscan",
+    "record_backscan_run",
+    "resolve_desk_playbook_backscan_log_dir",
+    "run_backscan",
+]
+
+# The back-scan run log's own env-var override (the ``TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR`` pattern).
+_BACKSCAN_LOG_DIR_ENV = "TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR"
+
+# The COMPLETE terminal-state set a ledger row may ever be written under -- mirrors
+# ``DeepBackfillRunStore``'s own three-state set (never a fourth "cancelled-with-nothing" state;
+# see the module docstring's cancellation section for when "cancelled" is skipped entirely).
+_TERMINAL_STATES = ("done", "cancelled", "error")
+
+# The COMPLETE per-date outcome vocabulary -- matches the Data Contract's own ``outcomes`` keys
+# exactly (never a fifth value).
+_OUTCOME_KEYS = ("reused", "recorded", "refused_non_session", "failed")
+
+# TC-13's positive scoping guard: the FOUR env vars every playbook/back-scan test or browser-QA rig
+# must scope together (the session ledger's own lesson -- reading a raw ``config.*_dir`` field or
+# scoping the store dir without its log-dir siblings silently orphans writes into the real store).
+_SCOPING_ENV_VARS = (
+    "TAPEOLOGY_DESK_PLAYBOOK_DIR",
+    "TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR",
+    "TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR",
+    "TAPEOLOGY_DESK_UNIVERSE_DIR",
+)
+
+
+class PlaybookNotScopedError(Exception):
+    """Raised by ``_assert_scoped`` -- a test/browser-QA rig's environment does not carve out a
+    dedicated, scoped root for every playbook/back-scan store directory."""
+
+
+class BackscanRunIntegrityError(Exception):
+    """An on-disk back-scan run-record file failed its checksum verification on load -- corrupted
+    or tampered, surfaced explicitly (never silence, never a fabricated record)."""
+
+
+def resolve_desk_playbook_backscan_log_dir(desk_universe_dir_resolved: str) -> str:
+    """The back-scan run log's directory: the ``TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR`` env var
+    if set, else a ``playbook_backscan_runs`` SIBLING of the caller's own already-resolved universe
+    directory -- the ``resolve_desk_playbook_log_dir`` pattern verbatim. Deliberately NOT a
+    ``Config`` field (an operational storage-location knob, never a value that shapes a served
+    result -- ``config_fingerprint()`` stays untouched)."""
+    override = os.environ.get(_BACKSCAN_LOG_DIR_ENV)
+    if override:
+        return override
+    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "playbook_backscan_runs")
+
+
+def _canonical(obj: object) -> bytes:
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def _iso_utc_now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
+
+
+def _empty_outcomes() -> dict:
+    return {key: 0 for key in _OUTCOME_KEYS}
+
+
+# --- TC-13: the positive scoping guard ------------------------------------------------------------
+
+
+def _assert_scoped(root: str | Path) -> None:
+    """A TEST/BROWSER-QA-LANE-ONLY positive guard -- NEVER called from the live HTTP routes below.
+    An operator's REAL compute legitimately runs with none of the four ``_SCOPING_ENV_VARS`` set,
+    resolving to the ambient ``.data/`` store; wiring this into the route would wrongly refuse every
+    genuine production compute. Instead, a test fixture or browser-QA rig calls this BEFORE
+    triggering any playbook or back-scan compute against a scoped root, so a scoping mistake is
+    refused loudly, in the rig itself, before it ever reaches ``run_playbook_and_record``.
+
+    Raises ``PlaybookNotScopedError`` unless EVERY one of the four scoping env vars is set AND
+    resolves to a path rooted under ``root`` and outside any ``.data/`` directory. Mirrors
+    ``scripts/seed_playbook_fixture_rig.py``'s own ``_assert_scoped`` helper (that script's own,
+    narrower three-directory version predates this one and is left as-is); this module's version is
+    the one both this iteration's extended fixture script and the dedicated TC-13 unit test call, so
+    the exact rule under test is exercised directly rather than re-derived."""
+    root_resolved = Path(root).resolve()
+    problems: list[str] = []
+    for name in _SCOPING_ENV_VARS:
+        value = os.environ.get(name)
+        if not value:
+            problems.append(f"{name} is unset -- resolves to the ambient default store")
+            continue
+        path = Path(value).resolve()
+        if ".data" in path.parts:
+            problems.append(f"{name}={path} is inside a .data/ store")
+        elif root_resolved not in path.parents and path != root_resolved:
+            problems.append(f"{name}={path} is outside the scoped root {root_resolved}")
+    if problems:
+        raise PlaybookNotScopedError(
+            "playbook/back-scan compute REFUSED -- store directories are not scoped:\n  "
+            + "\n  ".join(problems)
+            + "\nExport TAPEOLOGY_DESK_PLAYBOOK_DIR / TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR / "
+              "TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR / TAPEOLOGY_DESK_UNIVERSE_DIR (all four) "
+              "at the scoped root first."
+        )
+
+
+# --- the plan (pure, metadata-only) ----------------------------------------------------------------
+
+
+def _planned_dates(from_day: str, to_day: str) -> list[str]:
+    """Every calendar day in ``[from_day, to_day]`` inclusive, ``yyyy-MM-dd`` ascending -- pure date
+    arithmetic, no store touched at all (the ``plan_deep_windows`` precedent). An inverted range
+    (``from_day > to_day``) is an honest empty list, never an error (TC-17)."""
+    start = date.fromisoformat(from_day)
+    end = date.fromisoformat(to_day)
+    if start > end:
+        return []
+    dates: list[str] = []
+    cursor = start
+    while cursor <= end:
+        dates.append(cursor.isoformat())
+        cursor += timedelta(days=1)
+    return dates
+
+
+def plan_backscan(
+    from_day: str,
+    to_day: str,
+    bar_store: BarStore,
+    members: list[str],
+    config_fingerprint: str,
+    playbook_store: PlaybookStore,
+) -> dict:
+    """What a back-scan over ``[from_day, to_day]`` would find, said before anything is clicked --
+    PURE and metadata-only (TC-9): ONE ``playbook_input_signature`` resolution
+    (``compute_playbook_input_signature`` -- ``list(include_bars=False)``-only, so this never reads
+    a single bar's CONTENT) plus a ``PlaybookStore`` file-stat lookup per calendar day. Every day in
+    range is classified ``"recorded_at_current_signature"`` (a record already exists at this exact
+    ``(day, signature)`` key) or ``"missing_at_current_signature"`` (it does not) -- see the module
+    docstring for why this never tries to pre-classify which days are genuine trading sessions.
+
+    Shape:: {"from", "to", "playbook_input_signature", "dates": [{"session_date", "status"}, ...],
+    "total", "missing"}."""
+    signature = compute_playbook_input_signature(bar_store, members, config_fingerprint)
+    dates: list[dict] = []
+    missing = 0
+    for day in _planned_dates(from_day, to_day):
+        recorded = playbook_store.find_by_key(day, signature) is not None
+        status = "recorded_at_current_signature" if recorded else "missing_at_current_signature"
+        if not recorded:
+            missing += 1
+        dates.append({"session_date": day, "status": status})
+    return {
+        "from": from_day,
+        "to": to_day,
+        "playbook_input_signature": signature,
+        "dates": dates,
+        "total": len(dates),
+        "missing": missing,
+    }
+
+
+# --- the shared walker -------------------------------------------------------------------------------
+
+
+def run_backscan(
+    planned_dates: list[str],
+    universe_store: UniverseStore,
+    bar_store: BarStore,
+    config,
+    playbook_store: PlaybookStore,
+    *,
+    progress: Callable[[dict], None] | None = None,
+    should_abort: Callable[[], bool] | None = None,
+) -> list[dict]:
+    """Walk ``planned_dates`` in order, calling ``run_playbook_and_record`` for EACH -- the SOLE
+    walker; the manager and nothing else calls this (the ``run_deep_backfill`` precedent). Returns
+    the per-date outcome dicts in walk order: ``{"session_date", "outcome", "detail"}``, where
+    ``outcome`` is one of ``reused`` / ``recorded`` / ``refused_non_session`` / ``failed`` -- the
+    COMPLETE vocabulary, never a fifth value.
+
+    A per-date failure (a refusal or any other exception) is classified and the walk CONTINUES to
+    the remaining dates -- one bad date never aborts the whole back-scan (the ``run_deep_backfill``
+    per-chunk catch-and-continue precedent). ``progress``, if given, is called after EACH date with
+    the entry just appended. ``should_abort``, if given and true BEFORE a date starts, stops the walk
+    early (cooperative -- a date already in flight finishes and is recorded; the returned list is
+    simply shorter than ``len(planned_dates)``)."""
+    outcomes: list[dict] = []
+    for session_date in planned_dates:
+        if should_abort is not None and should_abort():
+            return outcomes
+        try:
+            _record, reused = run_playbook_and_record(
+                universe_store, bar_store, config, playbook_store, session_date,
+            )
+        except PlaybookSessionRefused as exc:
+            entry = {"session_date": session_date, "outcome": "refused_non_session", "detail": str(exc)}
+        except Exception as exc:  # noqa: BLE001 -- classified per-date; the walk continues
+            entry = {"session_date": session_date, "outcome": "failed", "detail": str(exc)}
+        else:
+            entry = {
+                "session_date": session_date,
+                "outcome": "reused" if reused else "recorded",
+                "detail": None,
+            }
+        outcomes.append(entry)
+        if progress is not None:
+            progress(entry)
+    return outcomes
+
+
+# --- the durable run ledger --------------------------------------------------------------------------
+
+
+class BackscanRunStore:
+    """File-based store rooted at the back-scan run-log directory -- the ONE reader/writer. Mirrors
+    ``DeepBackfillRunStore``'s discipline: checksum-verified load on every read, ``record()`` the
+    only mutation, no update/delete anywhere, and NO content-keyed dedup (every terminal run is a
+    genuinely distinct event). See the module docstring's cancellation section for WHEN a
+    ``"cancelled"`` state is written at all -- ``record()`` itself performs no such filtering; that
+    decision is the caller's (``DeskPlaybookBackscanComputeManager``'s)."""
+
+    def __init__(self, root: str | Path) -> None:
+        self._root = Path(root)
+
+    @property
+    def root(self) -> Path:
+        return self._root
+
+    def _path(self, run_id: str) -> Path:
+        return self._root / f"{run_id}.json"
+
+    def _load(self, path: Path) -> dict:
+        try:
+            data = json.loads(path.read_text())
+        except (OSError, ValueError) as exc:
+            raise BackscanRunIntegrityError(
+                f"back-scan run record file '{path.name}' is not parseable ({exc}) -- corrupted or "
+                f"tampered"
+            ) from exc
+        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
+            raise BackscanRunIntegrityError(
+                f"back-scan run record file '{path.name}' does not carry the expected record shape "
+                f"-- corrupted or tampered"
+            )
+        record = data["record"]
+        if _sha256(_canonical(record)) != data["file_checksum"]:
+            raise BackscanRunIntegrityError(
+                f"back-scan run record file '{path.name}' failed its integrity check (checksum "
+                f"mismatch) -- the file was corrupted or tampered with"
+            )
+        meta = record.get("meta")
+        if not isinstance(meta, dict):
+            raise BackscanRunIntegrityError(
+                f"back-scan run record file '{path.name}' does not carry the expected record shape "
+                f"-- corrupted or tampered"
+            )
+        return meta
+
+    def list(self) -> tuple[list[dict], list[dict]]:
+        """Every registered run's full content (each file verified), oldest-started first, plus an
+        EXPLICIT error row per file that failed verification. A directory that was never created
+        (no run has ever reached a logged terminal state) returns ``([], [])`` -- the honest-empty
+        case."""
+        if not self._root.exists():
+            return [], []
+        records: list[dict] = []
+        errors: list[dict] = []
+        for path in sorted(self._root.glob("*.json")):
+            try:
+                records.append(dict(self._load(path)))
+            except BackscanRunIntegrityError as exc:
+                errors.append({"file": path.name, "error": str(exc)})
+        records.sort(key=lambda meta: (meta.get("started_at", ""), meta.get("run_id", "")))
+        return records, errors
+
+    def record(
+        self,
+        *,
+        from_day: str,
+        to_day: str,
+        config_fingerprint: str,
+        started_at: str,
+        finished_at: str,
+        status: str,
+        planned_total: int,
+        outcomes: dict,
+    ) -> dict:
+        """Persist ONE new back-scan run record -- ALWAYS a genuinely new file: no content-keyed
+        dedup exists in this store, so a second call with identical field values still appends a
+        second, distinct record."""
+        if status not in _TERMINAL_STATES:
+            raise ValueError(f"invalid terminal status {status!r} -- must be one of {_TERMINAL_STATES}")
+        run_date = started_at[:10]  # started_at is always an ISO-8601 UTC string
+        run_id = f"backscanrun-{run_date}-{uuid.uuid4().hex[:12]}"
+        while self._path(run_id).exists():
+            run_id = f"backscanrun-{run_date}-{uuid.uuid4().hex[:12]}"
+        meta = {
+            "run_id": run_id,
+            "from": from_day,
+            "to": to_day,
+            "config_fingerprint": config_fingerprint,
+            "started_at": started_at,
+            "finished_at": finished_at,
+            "status": status,
+            "planned_total": planned_total,
... [diff_bound] apps/backend/app/research/desk_playbook_backscan.py: 168 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
new file mode 100644
index 0000000..c332035
--- /dev/null
+++ b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
@@ -0,0 +1,84 @@
+#!/usr/bin/env bash
+# qa_playbook_iter7_fixture_scoped_backend.sh — Stand up a FIXTURE-SCOPED backend carrying the
+# iter-6 J-04/J-05/J-06 playbook rig PLUS two additional recorded session dates for the Backscan
+# panel (Era B2, J-07), for a browser-QA / golden-replay pass. Never touches the ambient
+# apps/backend/.data/ store: every bar/universe/playbook/run-ledger directory this backend reads or
+# writes lives under a fresh root, so a "Run Backscan" click in the browser can never land in the
+# operator's real store (the iter-3 lesson, restated by this session's own iter-6 audit findings for
+# the run-ledger siblings specifically — all FOUR playbook env vars are exported here, including
+# TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR).
+#
+# This is an iter-7 VARIANT of qa_playbook_iter6_fixture_scoped_backend.sh, not an edit of it —
+# both scripts stay usable; this one is the ONLY backend entry point for this iteration's test/
+# browser work (per the phase spec's own instruction). It reuses
+# seed_playbook_iter7_backscan_fixture.py, which itself reuses seed_playbook_fixture_rig.py's own
+# main() verbatim (never a second implementation of the DECOR/RTAAA/DTAAA fixtures).
+#
+# What it seeds, on top of the iter-6 rig's own 2026-06-22 (DECOR/RTAAA/DTAAA, one playbook record
+# already computed):
+#   - BSCAN — a plain canonical open_high_break firing session, planted on TWO new dates
+#     (2026-06-23, 2026-06-24), each with its own 10 prior baseline sessions, LEFT UNRECORDED in
+#     the playbook store.
+#   - a fourth, NEW universe snapshot naming all four members (universe registration is
+#     append-only — this never edits iter-6's own three-member snapshot). Registering BSCAN
+#     changes playbook_input_signature (it hashes members ∪ {SPY}), so 2026-06-22's own
+#     three-member record no longer matches the CURRENT signature either — a plan preview over
+#     [2026-06-22, 2026-06-24] honestly reports all THREE dates missing, and a real "Run Backscan"
+#     click has genuine, non-trivial work to do on all three (the old three-member record stays on
+#     disk, untouched — append-only, a new version is minted beside it, never over it).
+#
+# Usage:
+#   bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh [root_dir] [port]
+#
+#   root_dir  Fresh root to seed (default: ${TMPDIR:-/tmp}/playbook-iter7-fixture-qa). Use a
+#             FRESH one whenever detector logic OR the back-scan module changed: playbook records
+#             are append-only and keyed (session_date, playbook_input_signature), so a root seeded
+#             by an older build would keep serving that build's recorded signals at the same
+#             signature.
+#   port      Backend port (default: 8301, the era's browser-QA rig convention — pair with
+#             `CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh`).
+set -euo pipefail
+
+SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
+REPO_ROOT="$(cd "$BACKEND_DIR/../.." && pwd)"
+
+ROOT="${1:-${TMPDIR:-/tmp}/playbook-iter7-fixture-qa}"
+PORT="${2:-8301}"
+
+BAR_DIR="$ROOT/bars"
+UNIVERSE_DIR="$ROOT/universe"
+PLAYBOOK_DIR="$ROOT/playbook"
+PLAYBOOK_LOG_DIR="$ROOT/playbook_runs"
+PLAYBOOK_BACKSCAN_LOG_DIR="$ROOT/playbook_backscan_runs"
+SCREEN_DIR="$ROOT/screen"
+DATASET_DIR="$ROOT/datasets"
+BAR_INDEX_DB="$ROOT/bar_index.db"
+DATASET_INDEX_DB="$ROOT/dataset_index.db"
+JOURNAL_DB="$ROOT/journal.db"
+
+mkdir -p "$BAR_DIR" "$UNIVERSE_DIR" "$PLAYBOOK_DIR" "$PLAYBOOK_LOG_DIR" \
+         "$PLAYBOOK_BACKSCAN_LOG_DIR" "$SCREEN_DIR" "$DATASET_DIR"
+
+export TAPEOLOGY_BAR_DIR="$BAR_DIR"
+export TAPEOLOGY_DESK_UNIVERSE_DIR="$UNIVERSE_DIR"
+export TAPEOLOGY_DESK_PLAYBOOK_DIR="$PLAYBOOK_DIR"
+export TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR="$PLAYBOOK_LOG_DIR"
+export TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR="$PLAYBOOK_BACKSCAN_LOG_DIR"
+export TAPEOLOGY_DESK_SCREEN_DIR="$SCREEN_DIR"
+export TAPEOLOGY_DATASET_DIR="$DATASET_DIR"
+export TAPEOLOGY_BAR_INDEX_DB="$BAR_INDEX_DB"
+export TAPEOLOGY_DATASET_INDEX_DB="$DATASET_INDEX_DB"
+export TAPEOLOGY_JOURNAL_DB="$JOURNAL_DB"
+
+"$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_playbook_iter7_backscan_fixture.py" "$ROOT"
+
+echo "[playbook-iter7-fixture-scoped-backend] root=$ROOT port=$PORT" >&2
+for var in TAPEOLOGY_BAR_DIR TAPEOLOGY_DESK_UNIVERSE_DIR TAPEOLOGY_DESK_PLAYBOOK_DIR \
+           TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR \
+           TAPEOLOGY_DESK_SCREEN_DIR TAPEOLOGY_DATASET_DIR TAPEOLOGY_BAR_INDEX_DB \
+           TAPEOLOGY_DATASET_INDEX_DB TAPEOLOGY_JOURNAL_DB; do
+  echo "[playbook-iter7-fixture-scoped-backend] $var=${!var}" >&2
+done
+
+exec env CHAIN_BACKEND_PORT="$PORT" bash "$REPO_ROOT/scripts/start-backend.sh"
diff --git a/apps/backend/scripts/seed_playbook_iter7_backscan_fixture.py b/apps/backend/scripts/seed_playbook_iter7_backscan_fixture.py
new file mode 100644
index 0000000..7722e80
--- /dev/null
+++ b/apps/backend/scripts/seed_playbook_iter7_backscan_fixture.py
@@ -0,0 +1,136 @@
+"""Extend the J-04/J-05/J-06 playbook browser-QA rig (``seed_playbook_fixture_rig.py``) with TWO
+additional recorded session dates, for the Backscan panel's own browser-QA pass (Era B2, J-07).
+
+Reuses the iter-6 rig VERBATIM (calls its own ``main()`` -- never a second implementation of the
+DECOR/RTAAA/DTAAA fixtures or their compute) and adds:
+
+  * a fourth universe member, ``BSCAN`` -- a plain canonical open_high_break firing session (the
+    ``_plant_firing_session`` shape ``test_desk_playbook.py`` hand-computes), planted on TWO new
+    dates, 2026-06-23 and 2026-06-24, each with its own 10 prior baseline sessions;
+  * a NEW, fourth universe snapshot naming all four members (DECOR, RTAAA, DTAAA, BSCAN) -- universe
+    registration is append-only, so this is a genuinely new record, never an edit of iter-6's own
+    three-member one, and it becomes the LATEST snapshot every route reads.
+
+Deliberately leaves BSCAN's two new dates UNRECORDED in the playbook store -- the whole point of
+this rig is a Backscan panel with something genuine left to walk. A plan preview over
+[2026-06-22, 2026-06-24] shows all THREE dates as ``missing_at_current_signature``, including
+2026-06-22 (iter-6's own rig already recorded a playbook for it, under a THREE-member universe) --
+registering the fourth member here changes ``playbook_input_signature`` (it hashes
+``members ∪ {SPY}``), so the OLD three-member record no longer matches the CURRENT signature and is
+honestly reported missing (T-4, "re-key, never rewrite": a membership change is exactly the kind of
+input change this discipline exists to catch). A real "Run Backscan" click in the browser therefore
+has genuine, non-trivial work to do on all three dates and a real, non-trivial result to screenshot
+-- the OLD three-member record is untouched on disk (append-only; a fresh, four-member version is
+minted beside it, never over it).
+
+Usage (normally through ``qa_playbook_iter7_fixture_scoped_backend.sh``, which exports the store
+env vars first -- ALL FOUR playbook scoping vars, per this session's own iter-6 lesson):
+
+    TAPEOLOGY_BAR_DIR=... TAPEOLOGY_DESK_UNIVERSE_DIR=... TAPEOLOGY_DESK_PLAYBOOK_DIR=... \\
+    TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR=... TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR=... \\
+    .venv/bin/python scripts/seed_playbook_iter7_backscan_fixture.py ROOT
+"""
+
+from __future__ import annotations
+
+import sys
+from pathlib import Path
+
+_SCRIPTS_DIR = Path(__file__).resolve().parent
+sys.path.insert(0, str(_SCRIPTS_DIR))
+sys.path.insert(0, str(_SCRIPTS_DIR.parent))
+
+import seed_playbook_fixture_rig  # noqa: E402
+
+from app.config import Config  # noqa: E402
+from app.providers.adapters.base import RawBar  # noqa: E402
+from app.research.bars import BarStore  # noqa: E402
+from app.research.desk_playbook import resolve_desk_playbook_dir  # noqa: E402
+from app.research.desk_playbook_backscan import _assert_scoped  # noqa: E402
+from app.research.desk_universe import UniverseStore  # noqa: E402
+
+BSCAN_SYMBOL = "BSCAN"
+BSCAN_DATES = ("2026-06-23", "2026-06-24")
+_E_OPEN_BY_DATE = {
+    # 2026-06-22T13:30:00Z (== 09:30 ET) is the iter-6 rig's own E_OPEN; the two new dates are one
+    # and two calendar days later -- the SAME "day offset in seconds" arithmetic
+    # ``test_desk_playbook.py``'s own ``_plant_baseline_sessions`` uses.
+    "2026-06-23": 1782135000.0 + 86_400.0,
+    "2026-06-24": 1782135000.0 + 2 * 86_400.0,
+}
+_BASELINE_DAYS = 10
+
+
+def _bar(symbol: str, epoch: float, o: float, h: float, low: float, c: float, v: int) -> RawBar:
+    return RawBar(symbol, "5m", epoch, float(o), float(h), float(low), float(c), int(v))
+
+
+def _firing_session_bars(symbol: str, day_open: float) -> list[RawBar]:
+    """The canonical open_high_break session (``test_desk_playbook.py``'s ``_plant_firing_session``
+    shape, hand-copied so the rig and the goldens can never drift): a narrow opening range and a
+    slot-3 trigger that breaks only the high side -- fires exactly one signal."""
+    return [
+        _bar(symbol, day_open, 100.5, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, day_open + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, day_open + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, day_open + 900.0, 100.8, 101.5, 100.7, 101.2, 1000),
+        _bar(symbol, day_open + 1200.0, 101.2, 101.4, 101.0, 101.1, 800),
+        _bar(symbol, day_open + 1500.0, 101.1, 101.3, 100.9, 101.0, 800),
+    ]
+
+
+def _baseline_bars(symbol: str, day_open: float) -> list[RawBar]:
+    """10 prior RTH 5m sessions, identical flat bars -> MBR = 1.0 and a full slot-volume-median
+    vector (the ``_baseline_bars`` recipe ``seed_playbook_fixture_rig.py`` itself uses)."""
+    bars: list[RawBar] = []
+    for day in range(_BASELINE_DAYS):
+        prior_open = day_open - (day + 1) * 86_400.0
+        for slot in range(6):
+            bars.append(_bar(symbol, prior_open + slot * 300.0, 100.0, 100.5, 99.5, 100.0, 1000))
+    return bars
+
+
+def main(root: Path) -> int:
+    # Reuse the iter-6 rig VERBATIM first -- plants DECOR/RTAAA/DTAAA on 2026-06-22, registers the
+    # three-member universe, and records ONE real playbook compute for that date. Never a second
+    # implementation of any of that.
+    result = seed_playbook_fixture_rig.main(root)
+    if result != 0:
+        return result
+
+    config = Config()
+    bar_dir = config.bar_dir_resolved()
+    universe_dir = config.desk_universe_dir_resolved()
+    playbook_dir = resolve_desk_playbook_dir(universe_dir)
+    _assert_scoped(root)
+
+    bar_store = BarStore(bar_dir)
+    universe_store = UniverseStore(universe_dir)
+
+    for day, day_open in _E_OPEN_BY_DATE.items():
+        bars = _baseline_bars(BSCAN_SYMBOL, day_open) + _firing_session_bars(BSCAN_SYMBOL, day_open)
+        bar_store.record(
+            symbol=BSCAN_SYMBOL, timeframe="5m",
+            window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
+            feed="test", bars=bars,
+        )
+        print(f"[seed-playbook-iter7-backscan] planted {BSCAN_SYMBOL} {day}: {len(bars)} 5m bars", file=sys.stderr)
+
+    members = [*seed_playbook_fixture_rig.MEMBERS, BSCAN_SYMBOL]
+    universe_store.record(
+        members=members, raw_members={m: m for m in members},
+        source_url="fixture-rig-iter7", min_members=1, max_members=len(members),
+    )
+    print(f"[seed-playbook-iter7-backscan] universe snapshot: {members}", file=sys.stderr)
+    print(
+        f"[seed-playbook-iter7-backscan] {BSCAN_SYMBOL} left UNRECORDED on {list(BSCAN_DATES)}; "
+        "2026-06-22's own three-member record now sits at a different playbook_input_signature "
+        "(the fourth member re-keys it) -- a real Run Backscan click over "
+        f"[2026-06-22, 2026-06-24] has genuine work to do on all three dates (playbook_dir={playbook_dir})",
+        file=sys.stderr,
+    )
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
diff --git a/apps/backend/tests/test_desk_playbook_backscan.py b/apps/backend/tests/test_desk_playbook_backscan.py
new file mode 100644
index 0000000..1bc2d4f
--- /dev/null
+++ b/apps/backend/tests/test_desk_playbook_backscan.py
@@ -0,0 +1,587 @@
+"""``desk_playbook_backscan.py`` (Era B2, J-07) -- ``plan_backscan``'s purity, ``run_backscan``'s
+resumable/cancel-safe walk over the ONE shared ``run_playbook_and_record`` entry point,
+``DeskPlaybookBackscanComputeManager``'s single-flight + cancel mechanics, ``BackscanRunStore``'s
+terminal-state-only ledger discipline, the ``_assert_scoped`` positive scoping guard (TC-13), and
+the three wired routes end to end.
+
+Reuses ``test_desk_playbook``'s own bar/universe fixture helpers (the ``test_desk_playbook_compute``
+cross-file-import precedent) rather than duplicating them. Test-first contract: TC-1 through TC-17
+in ``docs/phases/goal-playbook-iter-7.md``."""
+
+from __future__ import annotations
+
+import threading
+import time
+from datetime import datetime, timezone
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG
+from app.main import app
+from app.research import desk_playbook_backscan
+from app.research.bars import BarStore
+from app.research.desk_playbook import PlaybookStore, compute_playbook_input_signature
+from app.research.desk_playbook_backscan import (
+    BackscanRunStore,
+    DeskPlaybookBackscanComputeManager,
+    PlaybookNotScopedError,
+    _assert_scoped,
+    plan_backscan,
+    resolve_desk_playbook_backscan_log_dir,
+    run_backscan,
+)
+from app.research.desk_routes import get_desk_playbook_backscan_manager
+from app.research.desk_universe import UniverseStore
+from app.research.routes import ResearchRegistry, set_registry
+from app.research.store import JournalStore
+from test_desk_playbook import E_OPEN, _bar, _plant, _plant_baseline_sessions, _register_universe
+
+D0 = "2026-06-22"
+D1 = "2026-06-23"
+D2 = "2026-06-24"
+DAY_SECONDS = 86_400.0
+
+
+def _plant_firing_session_at(bar_store: BarStore, symbol: str, day_open: float) -> None:
+    """The canonical open_high_break session (``test_desk_playbook``'s own ``_plant_firing_session``
+    shape), shifted to fire on ANY day open -- fires exactly one signal every time, so three calls
+    at three different day opens plant three independently-recordable sessions."""
+    bars_1m = [_bar(symbol, "1m", day_open + i * 60.0, 100.5, 101.0, 100.0, 100.5, 500) for i in range(15)]
+    bars_5m = [
+        _bar(symbol, "5m", day_open, 100.5, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", day_open + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", day_open + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", day_open + 900.0, 100.8, 101.5, 100.7, 101.2, 1000),
+        _bar(symbol, "5m", day_open + 1200.0, 101.2, 101.4, 101.0, 101.1, 800),
+        _bar(symbol, "5m", day_open + 1500.0, 101.1, 101.3, 100.9, 101.0, 800),
+    ]
+    _plant(bar_store, symbol, "1m", bars_1m)
+    _plant(bar_store, symbol, "5m", bars_5m)
+
+
+def _plant_three_firing_sessions(bar_store: BarStore, symbol: str = "AAA") -> None:
+    """10 prior baseline sessions (2026-06-08..17) plus three independently-firing sessions on
+    D0/D1/D2 (2026-06-22..24) -- each of D1/D2 also inherits the sessions before it as EXTRA prior
+    baseline (>= the 10-session floor either way)."""
+    _plant_baseline_sessions(bar_store, symbol)
+    _plant_firing_session_at(bar_store, symbol, E_OPEN)
+    _plant_firing_session_at(bar_store, symbol, E_OPEN + DAY_SECONDS)
+    _plant_firing_session_at(bar_store, symbol, E_OPEN + 2 * DAY_SECONDS)
+
+
+def _plant_daily_bar(bar_store: BarStore, symbol: str, day: str) -> None:
+    epoch = datetime.fromisoformat(f"{day}T00:00:00+00:00").timestamp()
+    _plant(bar_store, symbol, "1d", [_bar(symbol, "1d", epoch, 100.0, 101.0, 99.0, 100.0)])
+
+
+@pytest.fixture
+def env(tmp_path):
+    bar_store = BarStore(tmp_path / "bars")
+    universe_store = _register_universe(tmp_path, ["AAA"])
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    return bar_store, universe_store, playbook_store
+
+
+def _members(universe_store: UniverseStore) -> list[str]:
+    records, _errors = universe_store.list()
+    return list(records[-1]["members"]) if records else []
+
+
+# --- plan_backscan: TC-1, TC-3, TC-7, TC-9, TC-17 ---------------------------------------------------
+
+
+def test_tc1_three_recorded_session_dates_none_yet_in_the_playbook_store_are_all_missing(tmp_path, env):
+    bar_store, universe_store, playbook_store = env
+    _plant_three_firing_sessions(bar_store)
+
+    result = plan_backscan(D0, D2, bar_store, _members(universe_store), CONFIG.config_fingerprint(), playbook_store)
+
+    assert result["from"] == D0 and result["to"] == D2
+    assert result["total"] == 3 and result["missing"] == 3
+    assert [d["session_date"] for d in result["dates"]] == [D0, D1, D2]
+    assert all(d["status"] == "missing_at_current_signature" for d in result["dates"])
+
+
+def test_tc3_after_recording_all_three_the_plan_shows_zero_missing(tmp_path, env):
+    bar_store, universe_store, playbook_store = env
+    _plant_three_firing_sessions(bar_store)
+    run_backscan([D0, D1, D2], universe_store, bar_store, CONFIG, playbook_store)
+
+    result = plan_backscan(D0, D2, bar_store, _members(universe_store), CONFIG.config_fingerprint(), playbook_store)
+
+    assert result["missing"] == 0
+    assert all(d["status"] == "recorded_at_current_signature" for d in result["dates"])
+
+
+def test_tc7_a_monkeypatched_threshold_flips_every_recorded_date_back_to_missing(tmp_path, env, monkeypatch):
+    bar_store, universe_store, playbook_store = env
+    _plant_three_firing_sessions(bar_store)
+    run_backscan([D0, D1, D2], universe_store, bar_store, CONFIG, playbook_store)
+    before = plan_backscan(D0, D2, bar_store, _members(universe_store), CONFIG.config_fingerprint(), playbook_store)
+    assert before["missing"] == 0
+
+    from app.research import desk_playbook as desk_playbook_module
+
+    monkeypatch.setattr(desk_playbook_module, "PLAYBOOK_OR_MINUTES", 999)
+
+    after = plan_backscan(D0, D2, bar_store, _members(universe_store), CONFIG.config_fingerprint(), playbook_store)
+    assert after["missing"] == 3
+    assert all(d["status"] == "missing_at_current_signature" for d in after["dates"])
+
+
+def test_tc17_an_inverted_range_is_an_honest_empty_plan(tmp_path, env):
+    bar_store, universe_store, playbook_store = env
+    result = plan_backscan(D2, D0, bar_store, [], CONFIG.config_fingerprint(), playbook_store)
+    assert result == {
+        "from": D2, "to": D0,
+        "playbook_input_signature": compute_playbook_input_signature(bar_store, [], CONFIG.config_fingerprint()),
+        "dates": [], "total": 0, "missing": 0,
+    }
+
+
+class _RaisingBarStore:
+    """A stub proving ``plan_backscan`` performs ZERO ``BarStore`` bar-CONTENT reads (TC-9) --
+    every content-reading method raises; ``list`` (metadata-only, exactly what
+    ``compute_playbook_input_signature`` calls) is the one method delegated to a real store."""
+
+    def __init__(self, real: BarStore) -> None:
+        self._real = real
+
+    def list(self, *args, **kwargs):
+        return self._real.list(*args, **kwargs)
+
+    def get(self, *args, **kwargs):
+        raise AssertionError("plan_backscan must never call BarStore.get")
+
+    def merged_bars(self, *args, **kwargs):
+        raise AssertionError("plan_backscan must never call BarStore.merged_bars")
+
+    def candles(self, *args, **kwargs):
+        raise AssertionError("plan_backscan must never call BarStore.candles")
+
+    def merged_candles(self, *args, **kwargs):
+        raise AssertionError("plan_backscan must never call BarStore.merged_candles")
+
+    def load_bars(self, *args, **kwargs):
+        raise AssertionError("plan_backscan must never call BarStore.load_bars")
+
+    def record(self, *args, **kwargs):
+        raise AssertionError("plan_backscan must never call BarStore.record")
+
+
+def test_tc9_plan_backscan_performs_zero_bar_content_reads(tmp_path, env):
+    bar_store, universe_store, playbook_store = env
+    _plant_three_firing_sessions(bar_store)
+    stub = _RaisingBarStore(bar_store)
+
+    result = plan_backscan(D0, D2, stub, _members(universe_store), CONFIG.config_fingerprint(), playbook_store)
+
+    assert result["total"] == 3
+    assert len(result["dates"]) == 3
+
+
+def test_tc9_route_level_stub_barstore_returns_http_200_with_populated_dates(tmp_path, monkeypatch):
+    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
+    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
+    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
+    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
+    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    registry = ResearchRegistry(store, CONFIG)
+    set_registry(registry)
+
+    bar_store = BarStore(tmp_path / "bars")
+    _plant_three_firing_sessions(bar_store)
+    universe_store = _register_universe(tmp_path, ["AAA"])
+
+    def _boom(*_args, **_kwargs):
+        raise AssertionError("plan_backscan route must never call this BarStore method")
+
+    for name in ("get", "candles", "merged_candles", "merged_bars", "load_bars"):
+        monkeypatch.setattr(BarStore, name, _boom)
+
+    with TestClient(app) as client:
+        response = client.get("/research/desk/playbook/backscan/plan", params={"from": D0, "to": D2})
+    assert response.status_code == 200
+    body = response.json()
+    assert body["total"] == 3
+    assert len(body["dates"]) == 3
+
+    set_registry(None)
+    store.close()
+
+
+# --- run_backscan: TC-2, TC-4, TC-8, TC-12 (short-side is a separate test file) --------------------
+
+
+def test_tc2_a_fresh_backscan_records_all_three_dates(tmp_path, env):
+    bar_store, universe_store, playbook_store = env
+    _plant_three_firing_sessions(bar_store)
+
+    outcomes = run_backscan([D0, D1, D2], universe_store, bar_store, CONFIG, playbook_store)
+
+    assert [o["outcome"] for o in outcomes] == ["recorded", "recorded", "recorded"]
+    records, errors = playbook_store.list()
+    assert errors == [] and len(records) == 3
+
+
+def test_tc4_a_second_backscan_over_the_same_range_reuses_with_zero_detector_calls(tmp_path, env, monkeypatch):
+    bar_store, universe_store, playbook_store = env
+    _plant_three_firing_sessions(bar_store)
+    run_backscan([D0, D1, D2], universe_store, bar_store, CONFIG, playbook_store)
+
+    from app.research import desk_playbook_compute as desk_playbook_compute_module
+
+    calls = []
+
+    def _counting(*args, **kwargs):
+        calls.append(1)
+        raise AssertionError("compute_playbook must never be called on an all-reused re-run")
+
+    monkeypatch.setattr(desk_playbook_compute_module, "compute_playbook", _counting)
+
+    outcomes = run_backscan([D0, D1, D2], universe_store, bar_store, CONFIG, playbook_store)
+
+    assert [o["outcome"] for o in outcomes] == ["reused", "reused", "reused"]
+    assert calls == []
+
+
+def test_tc8_a_date_with_zero_bars_bracketed_by_daily_evidence_is_refused_non_session(tmp_path, env):
+    bar_store, universe_store, playbook_store = env
+    _plant_baseline_sessions(bar_store, "AAA", dates=[f"2026-06-{d:02d}" for d in range(1, 11)])
+    _plant_firing_session_at(bar_store, "AAA", E_OPEN)  # 2026-06-22 -- fires
+    _plant_firing_session_at(bar_store, "AAA", E_OPEN + DAY_SECONDS)  # 2026-06-23 -- fires
+    # A provable non-session gap: daily bars bracket 06-24 without recording it.
+    for day in (D0, D1, "2026-06-25"):
+        _plant_daily_bar(bar_store, "AAA", day)
+
+    outcomes = run_backscan([D0, D1, "2026-06-24"], universe_store, bar_store, CONFIG, playbook_store)
+
+    assert [o["outcome"] for o in outcomes] == ["recorded", "recorded", "refused_non_session"]
+    assert outcomes[2]["detail"] is not None
+    records, _errors = playbook_store.list()
+    assert {r["session_date"] for r in records} == {D0, D1}  # no file for the refused date
+
+
+def test_run_backscan_a_failing_date_is_classified_failed_and_the_walk_continues(tmp_path, env, monkeypatch):
+    bar_store, universe_store, playbook_store = env
+    _plant_three_firing_sessions(bar_store)
+
+    from app.research import desk_playbook_compute as desk_playbook_compute_module
+
+    real_compute = desk_playbook_compute_module.compute_playbook
+    call_count = {"n": 0}
+
+    def _boom_on_first(*args, **kwargs):
+        call_count["n"] += 1
+        if call_count["n"] == 1:
+            raise RuntimeError("the bar store went away mid-walk")
+        return real_compute(*args, **kwargs)
+
+    monkeypatch.setattr(desk_playbook_compute_module, "compute_playbook", _boom_on_first)
+
+    outcomes = run_backscan([D0, D1, D2], universe_store, bar_store, CONFIG, playbook_store)
+
+    assert [o["outcome"] for o in outcomes] == ["failed", "recorded", "recorded"]
+    assert "went away mid-walk" in outcomes[0]["detail"]
+
+
+def test_run_backscan_should_abort_stops_before_the_next_date_starts(tmp_path, env):
+    bar_store, universe_store, playbook_store = env
+    _plant_three_firing_sessions(bar_store)
+
+    calls = {"n": 0}
+
+    def _abort_after_first():
+        calls["n"] += 1
+        return calls["n"] > 1
+
+    outcomes = run_backscan(
+        [D0, D1, D2], universe_store, bar_store, CONFIG, playbook_store, should_abort=_abort_after_first,
+    )
+    assert [o["outcome"] for o in outcomes] == ["recorded"]
+
+
+# --- the manager: single-flight + cancel + terminal-state-only ledger (TC-5, TC-6, TC-10) ----------
+
+
+def _wait_for_terminal(manager: DeskPlaybookBackscanComputeManager, timeout: float = 5.0) -> dict:
+    deadline = time.monotonic() + timeout
+    while time.monotonic() < deadline:
+        snap = manager.snapshot()
+        if snap["status"] != "running":
+            return snap
+        time.sleep(0.01)
+    raise AssertionError("back-scan compute never reached a terminal state")
+
+
+def test_manager_snapshot_is_idle_before_any_job_has_ever_run():
+    manager = DeskPlaybookBackscanComputeManager()
+    assert manager.snapshot() == {
+        "status": "idle", "from": None, "to": None, "planned_total": 0, "completed": 0,
+        "outcomes": {"reused": 0, "recorded": 0, "refused_non_session": 0, "failed": 0},
+        "current_date": None, "error": None,
+    }
+
+
+def test_tc5_cancel_after_one_date_completes_logs_a_partial_row_and_the_next_plan_shows_the_split(
+    tmp_path, env, monkeypatch
+):
+    bar_store, universe_store, playbook_store = env
+    _plant_three_firing_sessions(bar_store)
+    run_store = BackscanRunStore(tmp_path / "backscan_runs")
+
+    # Pause INSIDE the FIRST date's own call, set cancel while it is in flight (it has already
+    # "paid for its walk" per the module docstring, so it completes regardless), then release --
+    # the walk observes the cancel at the boundary BEFORE the second date ever starts, landing
+    # exactly 1 completed date.
+    entered_first = threading.Event()
+    release = threading.Event()
+    from app.research import desk_playbook_compute as desk_playbook_compute_module
+
+    real_run_and_record = desk_playbook_compute_module.run_playbook_and_record
+    call_index = {"n": 0}
+
+    def _pausing_run_and_record(*args, **kwargs):
+        call_index["n"] += 1
+        if call_index["n"] == 1:
+            entered_first.set()
+            release.wait(timeout=5)
+        return real_run_and_record(*args, **kwargs)
+
+    monkeypatch.setattr(desk_playbook_backscan, "run_playbook_and_record", _pausing_run_and_record)
+
+    manager = DeskPlaybookBackscanComputeManager()
+    manager.trigger(D0, D2, universe_store, bar_store, CONFIG, playbook_store, run_store)
+    assert entered_first.wait(timeout=5)
+    manager.cancel()
+    release.set()
+
+    snap = _wait_for_terminal(manager)
+    assert snap["status"] == "cancelled"
+    assert snap["completed"] == 1
+    manager.join_all(timeout=5)
+
+    rows, errors = run_store.list()
+    assert errors == [] and len(rows) == 1
+    assert rows[0]["status"] == "cancelled"
+    assert rows[0]["outcomes"]["recorded"] == 1
+
+    plan = plan_backscan(D0, D2, bar_store, _members(universe_store), CONFIG.config_fingerprint(), playbook_store)
+    statuses = {d["session_date"]: d["status"] for d in plan["dates"]}
+    assert statuses[D0] == "recorded_at_current_signature"
+    assert statuses[D1] == "missing_at_current_signature"
+    assert statuses[D2] == "missing_at_current_signature"
+
+
+def test_tc6_re_triggering_after_a_partial_cancel_resumes_the_recorded_date_as_reused(tmp_path, env):
+    bar_store, universe_store, playbook_store = env
+    _plant_three_firing_sessions(bar_store)
+    run_store = BackscanRunStore(tmp_path / "backscan_runs")
+
+    # Simulate TC-5's cancel-after-one outcome directly via run_backscan (cheaper than re-driving
+    # the manager's own threads a second time in the same test).
+    run_backscan([D0], universe_store, bar_store, CONFIG, playbook_store)
+
+    manager = DeskPlaybookBackscanComputeManager()
+    manager.trigger(D0, D2, universe_store, bar_store, CONFIG, playbook_store, run_store)
+    snap = _wait_for_terminal(manager)
+    manager.join_all(timeout=5)
+
+    assert snap["status"] == "done"
+    assert snap["outcomes"]["reused"] == 1
+    assert snap["outcomes"]["recorded"] == 2
+
... [diff_bound] apps/backend/tests/test_desk_playbook_backscan.py: 193 more diff lines omitted — Read the file for full detail
```
