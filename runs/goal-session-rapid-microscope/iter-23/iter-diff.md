# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/tests/test_scout.py b/apps/backend/tests/test_scout.py
index 4bf3704..172f6fb 100644
--- a/apps/backend/tests/test_scout.py
+++ b/apps/backend/tests/test_scout.py
@@ -1708,6 +1708,10 @@ def test_iter22_study3_capitulation_screens_with_real_playbook_signal_anchor(pg_
     screen_row = result["screen_row"]
     assert screen_row["structure_context"] == {"kind": "playbook_signal", "setup_id": "capitulation"}
     assert screen_row["decision"] in scout_ledger.CLOSED_DECISIONS
+    # Non-vacuous: the planted capitulation signal actually anchored the screen (never a hollow
+    # zero-anchor pass-through) -- mirrors Study 1's twin assertion above.
+    screen_result = screen_row["screen_result"]
+    assert screen_result["n_candidate"] + screen_result["n_comparator"] > 0
 
     wf_row = result["walkforward_row"]
     assert wf_row["candidate_id"] == screen_row["candidate_id"]
diff --git a/apps/frontend/tsconfig.json b/apps/frontend/tsconfig.json
index 424abf1..a7370e9 100644
--- a/apps/frontend/tsconfig.json
+++ b/apps/frontend/tsconfig.json
@@ -32,9 +32,10 @@
     "**/*.ts",
     "**/*.tsx",
     ".next-eval-iter10/types/**/*.ts",
+    ".next-qa/types/**/*.ts",
     ".next/types/**/*.ts",
     "next-env.d.ts",
-    ".next-qa/types/**/*.ts"
+    ".next-iter23-j06/types/**/*.ts"
   ],
   "exclude": [
     "node_modules"
```
