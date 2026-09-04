# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/tests/test_tape_observation_lifecycle_feed.py b/apps/backend/tests/test_tape_observation_lifecycle_feed.py
index 30eb6fa5..9e940503 100644
--- a/apps/backend/tests/test_tape_observation_lifecycle_feed.py
+++ b/apps/backend/tests/test_tape_observation_lifecycle_feed.py
@@ -510,13 +510,16 @@ async def test_lifecycle_failed_distinguishable_null_end_reason_and_retained_sta
     assert snapshot.event_count == 0  # no fabricated trade past the raise
 
 
-def test_seven_lifecycle_statuses_plus_watch_stopped_are_pairwise_distinguishable():
-    # The closed vocabulary this iteration's scenarios above actually exercise (Constitution §4).
-    statuses = {"connecting", "waiting", "live", "stale", "paused", "closed", "failed"}
-    assert len(statuses) == 7
-    # `watch_stopped` is the in-process 8th case: `get_observation_source` returns `None`, never a
-    # dict carrying any of the seven strings -- distinguishable by TYPE, not just by value.
-    assert None not in statuses
+# NOTE (iter-4 fixup, reviewer's carried-forward MINOR): a prior
+# ``test_seven_lifecycle_statuses_plus_watch_stopped_are_pairwise_distinguishable`` asserted only
+# ``len({seven hand-written literals}) == 7`` and never called ``WatchManager`` -- a vacuous
+# summary disconnected from real captured state (the iter-3 lessons entry: "a spec item phrased
+# 'all N values are pairwise distinguishable' invites a tautological summary test"). It is REMOVED
+# here rather than rewritten: the nine tests directly above (lines 370-510) already exercise every
+# one of the seven ``lifecycle.stream_status`` values plus the in-process ``watch_stopped`` case
+# non-vacuously, each via a real ``WatchManager``/``TapeEngine`` call and a real
+# ``assert snapshot.stream_status == "<value>"`` -- the "all seven are distinguishable" coverage
+# this test wanted to represent already exists, honestly, without a second literal-only copy.
 
 
 # === TC-9: (data_feed, availability_basis) pairs are pairwise distinct, never pooled ===========
diff --git a/apps/backend/tests/test_tape_observation_time.py b/apps/backend/tests/test_tape_observation_time.py
index 3d1d168f..61d68205 100644
--- a/apps/backend/tests/test_tape_observation_time.py
+++ b/apps/backend/tests/test_tape_observation_time.py
@@ -33,7 +33,7 @@ from pathlib import Path
 
 import pytest
 
-from app import observation_contract, watch_manager
+from app import main, observation_contract, watch_manager
 from app.config import CONFIG
 from app.engine.snapshot import EngineSnapshot
 from app.engine.tape_engine import TapeEngine
@@ -536,17 +536,32 @@ def test_watch_manager_iso_helper_matches_observation_contract_byte_for_byte():
     # This module necessarily duplicates the pinned ISO formatter (this repo's established
     # convention -- see watch_manager._iso_utc's own docstring); cross-check it never drifts
     # from the canonical Constitution §2 format (the TAPE_STATE_VOCABULARY iter-1 precedent).
+    # THREE-WAY (iter-4 IN SCOPE / coherence-auditor advisory): also cross-checks
+    # ``app.main._iso_utc`` -- its signature takes a ``datetime`` (unlike the other two's
+    # ``epoch: float``), so the same representative epochs are converted with
+    # ``datetime.fromtimestamp(epoch, timezone.utc)`` before calling it, per main._iso_utc's own
+    # docstring claim that it matches the other two byte-for-byte -- now actually tested.
     for epoch in (1_725_000_000.654321, 0.0, 1_800_000_500.5):
-        assert watch_manager._iso_utc(epoch) == observation_contract._iso_utc(epoch)
+        watch_manager_iso = watch_manager._iso_utc(epoch)
+        observation_contract_iso = observation_contract._iso_utc(epoch)
+        main_iso = main._iso_utc(datetime.fromtimestamp(epoch, tz=timezone.utc))
+        assert watch_manager_iso == observation_contract_iso
+        assert main_iso == observation_contract_iso
+        assert main_iso == watch_manager_iso
 
 
 def test_counterexample_iso_round_trip_detects_a_hand_formatted_string():
-    # A hand-formatted string (no microseconds, no "Z"/offset) never equals the pinned function's
-    # own output for the same instant -- proving the round-trip equality check is non-vacuous.
+    # A hand-formatted string (no microseconds, no "Z"/offset) never equals any of the THREE
+    # pinned functions' own output for the same instant -- proving the round-trip equality check
+    # is non-vacuous for the full three-way comparison (iter-4 IN SCOPE).
     epoch = 1_725_000_000.123456
     hand_formatted = datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
     with pytest.raises(AssertionError):
         assert hand_formatted == observation_contract._iso_utc(epoch)
+    with pytest.raises(AssertionError):
+        assert hand_formatted == watch_manager._iso_utc(epoch)
+    with pytest.raises(AssertionError):
+        assert hand_formatted == main._iso_utc(datetime.fromtimestamp(epoch, tz=timezone.utc))
 
 
 # --- TC-12: two independent DatasetStore.replay reruns yield identical observation_hash ------
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-observation-contract/telemetry.jsonl   | 6 ++++++
 runs/goal-session-observation-contract/trace/trace.jsonl | 1 +
 2 files changed, 7 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
