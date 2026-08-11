# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 6.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/frontend/app/desk/page.tsx` (65 lines not shown)

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
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-playbook/telemetry.jsonl   | 7 +++++++
 runs/goal-session-playbook/trace/trace.jsonl | 1 +
 2 files changed, 8 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
