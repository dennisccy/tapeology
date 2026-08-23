# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

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
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/j06-tranche/acceptance.json                |   2 +-
 reports/j06-tranche/tr2-disclosure-analysis.json   |   2 +-
 reports/security/install-decisions.jsonl           |   1 +
 runs/goal-session-rapid-microscope/session.json    |   3 +-
 .../state/assumptions.md                           | 514 +--------------------
 .../state/assumptions.md.archive.md                | 497 ++++++++++++++++++++
 .../goal-session-rapid-microscope/state/lessons.md | 143 +-----
 .../state/lessons.md.archive.md                    | 180 ++++++++
 runs/goal-session-rapid-microscope/telemetry.jsonl |  13 +
 .../trace/trace.jsonl                              |   2 +
 10 files changed, 728 insertions(+), 629 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
