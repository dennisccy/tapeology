# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
index 4171ac6..c1d3ee4 100644
--- a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
+++ b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
@@ -120,13 +120,41 @@ export TAPEOLOGY_JOURNAL_DB="$JOURNAL_DB"
 # own docstring for the full seven-step sequence this exercises for real.
 "$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_micro_graduation_iter18_fixture.py" "$ROOT"
 
+# goal-rapid-microscope-iter-19 (TC-9): the ONE list of store-root vars this launch bound the
+# backend to -- shared by the stderr echo below AND the durable manifest file, so the two can never
+# silently diverge. Closes iteration 18's evaluator finding ("the quality report states that the
+# browser lane used your real data store. It did not.") by giving a QA/reviewer/auditor report a
+# FIXED-PATH file to cite, independent of whether this launch's own stdout/stderr was captured.
+_TAPEOLOGY_SCOPED_VARS=(
+  TAPEOLOGY_BAR_DIR TAPEOLOGY_DESK_UNIVERSE_DIR TAPEOLOGY_DESK_PLAYBOOK_DIR
+  TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR
+  TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB
+  TAPEOLOGY_DESK_SCREEN_DIR TAPEOLOGY_DATASET_DIR TAPEOLOGY_BAR_INDEX_DB
+  TAPEOLOGY_DATASET_INDEX_DB TAPEOLOGY_JOURNAL_DB
+)
+
 echo "[playbook-iter8-replay-fixture-scoped-backend] root=$ROOT port=$PORT" >&2
-for var in TAPEOLOGY_BAR_DIR TAPEOLOGY_DESK_UNIVERSE_DIR TAPEOLOGY_DESK_PLAYBOOK_DIR \
-           TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR \
-           TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB \
-           TAPEOLOGY_DESK_SCREEN_DIR TAPEOLOGY_DATASET_DIR TAPEOLOGY_BAR_INDEX_DB \
-           TAPEOLOGY_DATASET_INDEX_DB TAPEOLOGY_JOURNAL_DB; do
+for var in "${_TAPEOLOGY_SCOPED_VARS[@]}"; do
   echo "[playbook-iter8-replay-fixture-scoped-backend] $var=${!var}" >&2
 done
 
+MANIFEST_PATH="$REPO_ROOT/reports/qa-scoped-backend-store-manifest.md"
+mkdir -p "$(dirname "$MANIFEST_PATH")"
+{
+  echo "# QA fixture-scoped backend store manifest"
+  echo
+  echo "Written by \`qa_playbook_iter7_fixture_scoped_backend.sh\` at launch (goal-rapid-microscope-"
+  echo "iter-19, TC-9) -- the durable record of which store roots THIS launch's backend process is"
+  echo "bound to. A quality/QA report describing what the browser/replay lane exercised MUST cite"
+  echo "this file (never assert \"real data store\" for a pass launched through this script)."
+  echo
+  echo "- launched_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
+  echo "- root: $ROOT"
+  echo "- port: $PORT"
+  for var in "${_TAPEOLOGY_SCOPED_VARS[@]}"; do
+    echo "- $var: ${!var}"
+  done
+} > "$MANIFEST_PATH"
+echo "[playbook-iter8-replay-fixture-scoped-backend] manifest written to $MANIFEST_PATH" >&2
+
 exec env CHAIN_BACKEND_PORT="$PORT" bash "$REPO_ROOT/scripts/start-backend.sh"
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/journey-scripts/J-02.json | 3 ++-
 runs/goal-session-rapid-microscope/journey-scripts/J-03.json | 3 ++-
 runs/goal-session-rapid-microscope/journey-scripts/J-04.json | 3 ++-
 runs/goal-session-rapid-microscope/journey-scripts/J-05.json | 3 ++-
 runs/goal-session-rapid-microscope/telemetry.jsonl           | 7 +++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl         | 2 ++
 6 files changed, 17 insertions(+), 4 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
