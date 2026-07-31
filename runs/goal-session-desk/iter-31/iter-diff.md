# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/apps/backend/app/research/desk_screen_compute.py b/apps/backend/app/research/desk_screen_compute.py
index e91e3c5..8c1c648 100644
--- a/apps/backend/app/research/desk_screen_compute.py
+++ b/apps/backend/app/research/desk_screen_compute.py
@@ -274,7 +274,7 @@ def run_screen_and_record(
         # `compute_screen`, or a `ScreenIntegrityError` from a damaged snapshot at this key) --
         # logged as "failed", then RE-RAISED verbatim so every existing caller's own crash-handling
         # (the manager's `_work` except-clause, an uncaught CLI crash) stays byte-unchanged.
-        failed_member = members[attempted] if attempted < len(members) else None
+        failed_member = members[attempted] if 0 < attempted < len(members) else None
         _log(
             state="failed", reused=False, members_attempted=attempted, ranked_count=0,
             skipped_by_reason=dict(_EMPTY_SKIPPED_BY_REASON), screen_id=None,
diff --git a/apps/backend/tests/test_desk_screen_compute.py b/apps/backend/tests/test_desk_screen_compute.py
index ed3ad4b..c9413b8 100644
--- a/apps/backend/tests/test_desk_screen_compute.py
+++ b/apps/backend/tests/test_desk_screen_compute.py
@@ -732,6 +732,39 @@ def test_cli_second_invocation_with_identical_pins_reuses_the_existing_snapshot(
     assert errors == [] and len(records) == 1  # no second file
 
 
+def test_tc3_cli_run_leaves_exactly_one_matching_screen_run_record(tmp_path, monkeypatch, capsys):
+    """TC-3 (goal-desk-iter-31): a CLI-triggered run leaves exactly ONE durable ``ScreenRunStore``
+    record whose ``state``/``screen_id``/``members_attempted`` match the ``ScreenStore`` snapshot it
+    produced -- the SAME single shared writer (``run_screen_and_record``) the HTTP route uses,
+    exercised here through the CLI's own ``main()`` entry point. ``_set_cli_env`` sets no
+    ``TAPEOLOGY_DESK_SCREEN_LOG_DIR`` override, so the run log resolves to the sibling-of-universe
+    default (``resolve_desk_screen_log_dir``) -- the same ``tmp_path / "screen_runs"`` this file's
+    other ``ScreenRunStore`` fixtures already point at."""
+    _set_cli_env(monkeypatch, tmp_path)
+    _register_fixture_universe(tmp_path / "universe")
+    bar_store = BarStore(tmp_path / "bars")
+    bar_index = BarIndex(str(tmp_path / "bar_index.db"))
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+    monkeypatch.setattr(sys, "argv", ["desk_screen_compute", "--date", SCREEN_DATE])
+
+    exit_code = desk_screen_compute.main()
+    assert exit_code == 0
+    capsys.readouterr()
+
+    screen_store = ScreenStore(tmp_path / "screen")
+    screen_records, screen_errors = screen_store.list()
+    assert screen_errors == [] and len(screen_records) == 1
+    snapshot = screen_records[0]
+
+    screen_run_store = ScreenRunStore(tmp_path / "screen_runs")
+    run_records, run_errors = screen_run_store.list()
+    assert run_errors == [] and len(run_records) == 1
+    run = run_records[0]
+    assert run["state"] == "done"
+    assert run["screen_id"] == snapshot["id"]
+    assert run["members_attempted"] == run["members_total"]
+
+
 # ==================================================================================================
 # goal-desk-iter-29 (J-18) -- the screen-run log: the five-pin pre-check reuse short-circuit, and
 # ONE durable run record per terminal outcome (done/cancelled/failed), written by
@@ -920,6 +953,41 @@ def test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_faile
     assert screen_records == []
 
 
+def test_tc1_a_crash_before_any_member_is_attempted_records_failed_member_null(
+    manager_env, monkeypatch, tmp_path,
+):
+    """TC-1 (goal-desk-iter-31): a run that crashes before ``_counting_progress`` ever fires
+    (``attempted == 0``) must never fabricate a ``failed_member`` -- it records ``null`` rather than
+    naming a symbol the walk never reached. Companion regression guard: TC-2, the test immediately
+    above (``test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_failed_member``,
+    unmodified), proves the ``attempted > 0`` case still names the genuinely in-progress member."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
+    screen_run_store = ScreenRunStore(tmp_path / "screen_runs")
+
+    def fake_compute_screen(_us, _bs, _bi, _ds, _cfg, _sd, *, progress=None, should_abort=None):
+        raise RuntimeError("synthetic raise before any member is attempted")
+
+    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
+
+    with pytest.raises(RuntimeError, match="synthetic raise before any member is attempted"):
+        run_screen_and_record(
+            universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+            screen_run_store=screen_run_store,
+        )
+
+    records, errors = screen_run_store.list()
+    assert errors == [] and len(records) == 1
+    run = records[0]
+    assert run["state"] == "failed"
+    assert run["error"] == "synthetic raise before any member is attempted"
+    assert run["failed_member"] is None
+    assert run["screen_id"] is None
+    assert run["reused"] is False
+
+    screen_records, _errors = screen_store.list()
+    assert screen_records == []
+
+
 def test_tc7_omitting_the_run_store_leaves_no_durable_record_for_that_run(real_ctx, tmp_path):
     """TC-7: a process that ends before the writer's terminal call (simulated here by simply never
     supplying a ``screen_run_store``) leaves the ledger with no entry for that run -- the SAME
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index aa75afe..3bcdb64 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -1328,13 +1328,13 @@ function LatestScreenRunDetail({ run }: { run: DeskScreenRun }) {
           {formatScreenRunElapsed(run.started_utc, run.finished_utc)} elapsed
         </span>
         <span data-testid="desk-screen-run-latest-outcome">{screenRunOutcomeText(run)}</span>
-        {unreached > 0 && (
+        {unreached > 0 && !(run.state === "done" && run.reused) && (
           <span data-testid="desk-screen-run-latest-unreached" className="text-amber-200/70">
             {unreached} member{unreached === 1 ? "" : "s"} not reached
           </span>
         )}
       </div>
-      {run.state === "done" && (
+      {run.state === "done" && !run.reused && (
         <div data-testid="desk-screen-run-latest-counts" className="text-xs text-slate-400">
           {run.ranked_count} ranked · {run.skipped_by_reason.no_bars} skipped (no bars) ·{" "}
           {run.skipped_by_reason.no_basis} skipped (no basis)
diff --git a/apps/frontend/next-env.d.ts b/apps/frontend/next-env.d.ts
index e61acc9..830fb59 100644
--- a/apps/frontend/next-env.d.ts
+++ b/apps/frontend/next-env.d.ts
@@ -1,6 +1,6 @@
 /// <reference types="next" />
 /// <reference types="next/image-types/global" />
-/// <reference path=".//home/dennis-chan/.cache/iad/shared/claude-1000/-home-dennis-chan-Git-tapeology/ed2eda9d-a300-40af-b7d9-38fc5240ab66/scratchpad/iter30-rig/frontend-dist/types/routes.d.ts" />
+/// <reference path="./.next/types/routes.d.ts" />
 
 // NOTE: This file should not be edited
 // see https://nextjs.org/docs/app/api-reference/config/typescript for more information.
diff --git a/apps/frontend/tsconfig.json b/apps/frontend/tsconfig.json
index 663e7bc..424abf1 100644
--- a/apps/frontend/tsconfig.json
+++ b/apps/frontend/tsconfig.json
@@ -32,10 +32,9 @@
     "**/*.ts",
     "**/*.tsx",
     ".next-eval-iter10/types/**/*.ts",
-    ".next-qa/types/**/*.ts",
     ".next/types/**/*.ts",
     "next-env.d.ts",
-    "/home/dennis-chan/.cache/iad/shared/claude-1000/-home-dennis-chan-Git-tapeology/ed2eda9d-a300-40af-b7d9-38fc5240ab66/scratchpad/iter30-rig/frontend-dist/types/**/*.ts"
+    ".next-qa/types/**/*.ts"
   ],
   "exclude": [
     "node_modules"
```
