# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
index 73862342..4f380045 100644
--- a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
+++ b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
@@ -120,6 +120,29 @@ mkdir -p "$BAR_DIR" "$UNIVERSE_DIR" "$PLAYBOOK_DIR" "$PLAYBOOK_LOG_DIR" \
 cp "$BACKEND_DIR/tests/fixtures/datasets/6c9bf2c700d749e0993efd92c5807de3.json" "$DATASET_DIR/"
 cp "$BACKEND_DIR/tests/fixtures/datasets/d9f9dbe04fb24a7caccc53f0c6805412.json" "$DATASET_DIR/"
 
+# goal-hypothesis-foundry-iter-2 (J-01 step 5 / TC-1/TC-2/TC-3): close the QA-rig visibility gap
+# `lessons.md` iter-1 named — `foundry_source_registry.resolve_foundry_dir()` derives the Foundry
+# directory as a `foundry` SIBLING of `TAPEOLOGY_DATASET_DIR` when `TAPEOLOGY_FOUNDRY_DIR` is
+# unset, which this rig's own `$DATASET_DIR=$ROOT/datasets` resolves to `$ROOT/foundry` — a fresh,
+# never-recorded directory, so `GET /research/desk/micro/foundry` served `era_open_baseline: null`
+# here even though the real recorded artifact
+# (`apps/backend/.data/foundry/era_open_baseline.json`) is genuine. Fix: copy that REAL artifact
+# (read-only source, never written to) into this rig's own scoped `$ROOT/foundry/` before backend
+# start — the exact same "plain file copy of an already-committed/recorded real artifact into the
+# scoped root" pattern the two `cp` lines above already use for the PG tick-dataset fixtures, so
+# `GET /research/desk/micro/foundry` on THIS rig now serves the genuine recorded values, never an
+# invented one (the anti-goal `lessons.md` explicitly warns against). Honest-absence fallback: if
+# the operator has never run the one-time recording script
+# (`scripts/record_foundry_era_open_baseline.py`), there is nothing genuine to copy — the rig then
+# correctly falls back to the pre-existing honest `era_open_baseline: null` state, exactly like a
+# fresh install (never fabricated).
+FOUNDRY_DIR="$ROOT/foundry"
+REAL_FOUNDRY_BASELINE="$BACKEND_DIR/.data/foundry/era_open_baseline.json"
+if [[ -f "$REAL_FOUNDRY_BASELINE" ]]; then
+  mkdir -p "$FOUNDRY_DIR"
+  cp "$REAL_FOUNDRY_BASELINE" "$FOUNDRY_DIR/"
+fi
+
 export TAPEOLOGY_BAR_DIR="$BAR_DIR"
 export TAPEOLOGY_DESK_UNIVERSE_DIR="$UNIVERSE_DIR"
 export TAPEOLOGY_DESK_PLAYBOOK_DIR="$PLAYBOOK_DIR"
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-hypothesis-foundry/telemetry.jsonl   | 6 ++++++
 runs/goal-session-hypothesis-foundry/trace/trace.jsonl | 1 +
 2 files changed, 7 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
