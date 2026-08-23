# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/tests/test_micro_join.py b/apps/backend/tests/test_micro_join.py
index f5b313f7..acb7e300 100644
--- a/apps/backend/tests/test_micro_join.py
+++ b/apps/backend/tests/test_micro_join.py
@@ -21,6 +21,7 @@ from __future__ import annotations
 
 import hashlib
 import inspect
+import os
 import sqlite3
 from datetime import datetime, timezone
 from pathlib import Path
@@ -50,6 +51,20 @@ def _iso(epoch: float) -> str:
     )
 
 
+def _real_corpus_dataset_store() -> DatasetStore:
+    """iter-28: a ``DatasetStore`` over the real ``.data/datasets`` corpus wired with the SAME
+    durable ``index_db_path=`` primitive the live backend's own ``get_dataset_store()``
+    (``routes.py``) already uses -- ``TAPEOLOGY_DATASET_INDEX_DB`` env-or-sibling
+    ``dataset_index.db``. Without this, the two real-corpus tests below re-parsed and
+    re-checksummed the whole real corpus from scratch on every single test run; the index is a
+    content-checksum-keyed, "owns nothing" derived cache, so sharing it with the running backend
+    is the intended reuse, never a new mechanism."""
+    dataset_dir = CONFIG.dataset_dir_resolved()
+    override = os.environ.get("TAPEOLOGY_DATASET_INDEX_DB")
+    index_db_path = override or os.path.join(os.path.dirname(dataset_dir), "dataset_index.db")
+    return DatasetStore(dataset_dir, index_db_path=index_db_path)
+
+
 # --- shared fixture: the real PG snapshot, built once per module (577 trades -- cheap) -------------
 
 
@@ -948,7 +963,7 @@ def test_tc16_real_corpus_joinable_corpus_arithmetic_is_unchanged_by_the_passeng
     enumerated arithmetic itself."""
     from app.research.desk_playbook import resolve_desk_playbook_dir
 
-    dataset_store = DatasetStore(CONFIG.dataset_dir_resolved())
+    dataset_store = _real_corpus_dataset_store()
     playbook_store = PlaybookStore(resolve_desk_playbook_dir(CONFIG.desk_universe_dir_resolved()))
 
     counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
@@ -972,7 +987,7 @@ def test_tc4_real_corpus_join_playbook_signal_is_unaffected_by_the_accessor_re_p
     non-``None`` ``feature_at_trigger``, and a full closed outcome set."""
     from app.research.desk_playbook import resolve_desk_playbook_dir
 
-    dataset_store = DatasetStore(CONFIG.dataset_dir_resolved())
+    dataset_store = _real_corpus_dataset_store()
     playbook_store = PlaybookStore(resolve_desk_playbook_dir(CONFIG.desk_universe_dir_resolved()))
     snapshots_dir = resolve_micro_snapshots_dir(CONFIG.dataset_dir_resolved())
 
diff --git a/apps/backend/tests/test_micro_readiness.py b/apps/backend/tests/test_micro_readiness.py
index de124d52..d7334ddb 100644
--- a/apps/backend/tests/test_micro_readiness.py
+++ b/apps/backend/tests/test_micro_readiness.py
@@ -14,6 +14,7 @@ cost is paid once for the whole file. Every OTHER test builds its own small, her
 from __future__ import annotations
 
 import json
+import os
 from datetime import date, datetime
 from zoneinfo import ZoneInfo
 
@@ -384,6 +385,42 @@ def test_corrupted_dataset_surfaces_through_the_route_too(client, tmp_path):
     assert [s["dataset_id"] for s in body["shards"]] == [healthy["id"]]
 
 
+# --- iter-28 TC-10: a warm durable index shared with a DIFFERENT store's content must never mask
+# a checksum failure in a brand-new store's own files -- ``DatasetIndex.lookup`` keys on the
+# absolute file path (``dataset_index.py``), so a scratch copy's never-before-seen path is always
+# a genuine miss regardless of what else is warm in the shared index db.
+
+
+def test_tc10_corrupted_dataset_surfaces_with_a_warm_durable_index_from_a_different_store(tmp_path):
+    shared_index_db = str(tmp_path / "shared_dataset_index.db")
+
+    # Warm the shared index db against a FIRST, unrelated, healthy store.
+    other_store = DatasetStore(tmp_path / "other_datasets", index_db_path=shared_index_db)
+    _plant_dataset(other_store, symbol="GOOG")
+    other_store.list()  # populate the durable index for the OTHER store's own paths
+
+    # A brand-new scratch store (a distinct root -> distinct absolute paths) pointed at the SAME
+    # now-warm index db.
+    store = DatasetStore(tmp_path / "scratch_datasets", index_db_path=shared_index_db)
+    healthy = _plant_dataset(store, symbol="AAPL")
+    corrupted = _plant_dataset(
+        store, symbol="MSFT",
+        window_start_utc="2026-06-10T13:00:00Z", window_end_utc="2026-06-10T13:01:00Z",
+    )
+    path = tmp_path / "scratch_datasets" / f"{corrupted['id']}.json"
+    payload = json.loads(path.read_text())
+    payload["record"]["meta"]["checksum"] = "deadbeef" * 8
+    path.write_text(json.dumps(payload))
+
+    cache = MicroReadinessCache(str(tmp_path / "readiness_cache.db"))
+    result = build_readiness(store, cache, dataset_dir=str(tmp_path / "scratch_datasets"))
+
+    assert len(result["integrity_errors"]) == 1
+    assert result["integrity_errors"][0]["file"] == f"{corrupted['id']}.json"
+    assert result["totals"]["distinct_datasets"] == 1
+    assert [s["dataset_id"] for s in result["shards"]] == [healthy["id"]]
+
+
 # --- TC-7: a repeat call/GET never re-classifies, and the response is byte-identical ----------------
 
 
@@ -458,20 +495,38 @@ def test_zero_corpus_is_an_honest_200_with_three_unmet_floor_rows(client):
 
 
 @pytest.fixture(scope="module")
-def real_readiness(tmp_path_factory):
+def real_readiness():
     # CONFIG.dataset_dir (never `_resolved()`) is the un-overridden package default -- the
     # committed real corpus, independent of any ambient TAPEOLOGY_DATASET_DIR the environment
     # might carry.
+    #
+    # iter-28: a fresh `tmp_path_factory` dir every pytest invocation forced a full re-parse +
+    # re-checksum of the whole real store (26 GB / 98 files at this era's corpus size) on every
+    # single run. Point BOTH the `MicroReadinessCache` DB and the `DatasetStore`'s own metadata
+    # index at their PRODUCTION durable-cache paths instead of a throwaway dir -- the exact same
+    # `resolve_micro_readiness_cache_db_path` / `TAPEOLOGY_DATASET_INDEX_DB`-env-or-sibling
+    # primitives `get_dataset_store()` already wires in `routes.py` for the live backend. Both
+    # caches are content-checksum-keyed (`Store discipline`: "no second mutable input to go
+    # stale") -- sharing them with the running backend is exactly the intended reuse, not a new
+    # cache mechanism, and both files already live under the gitignored `.data/` tree.
     dataset_dir = CONFIG.dataset_dir
-    store = DatasetStore(dataset_dir)
-    cache_dir = tmp_path_factory.mktemp("micro_readiness_real_cache")
-    cache = MicroReadinessCache(str(cache_dir / "cache.db"))
+    index_db_override = os.environ.get("TAPEOLOGY_DATASET_INDEX_DB")
+    index_db_path = index_db_override or os.path.join(
+        os.path.dirname(dataset_dir), "dataset_index.db"
+    )
+    store = DatasetStore(dataset_dir, index_db_path=index_db_path)
+    cache = MicroReadinessCache(resolve_micro_readiness_cache_db_path(dataset_dir))
     return build_readiness(store, cache, dataset_dir=dataset_dir)
 
 
 @pytest.fixture(scope="module")
 def real_dataset_records():
-    store = DatasetStore(CONFIG.dataset_dir)
+    dataset_dir = CONFIG.dataset_dir
+    index_db_override = os.environ.get("TAPEOLOGY_DATASET_INDEX_DB")
+    index_db_path = index_db_override or os.path.join(
+        os.path.dirname(dataset_dir), "dataset_index.db"
+    )
+    store = DatasetStore(dataset_dir, index_db_path=index_db_path)
     records, errors = store.list()
     assert errors == []  # the committed corpus is healthy -- a real integrity error here would
     # be a repo-hygiene regression, not something this iteration's tests should silently paper
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 7069436d..652cc174 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -5017,6 +5017,17 @@ function RefereeHypothesesTable({
   );
 }
 
+// goal-rapid-microscope-iter-28 (J-01/J-10, spec section 10.7 r5 owner ruling): the ONE
+// deliberate, owner-authorized exception to Foundation invariant 5 -- static disclosure copy
+// only, never a computed value, never a behavior change. `referee_evidence.strategy_trade_
+// readiness` counts dataset FILES through its own enumeration and may include withheld/unexposed
+// Rapid-Microscope shards; `referee_evidence.py`/`referee_routes.py` stay byte-frozen this era
+// (never edited, never intercepted), so the caveat can ONLY be served here, at the rendering
+// layer, verbatim beside the served `strategy_trade` figures. Defined ONCE as a shared constant
+// (never duplicated ad hoc -- TC-4) so a single edit keeps every render site in sync.
+const REFEREE_EVIDENCE_SEAL_UNAWARE_CAVEAT =
+  "Legacy Referee readiness metric — seal-unaware in the Rapid Microscope era. It may include withheld/unexposed Rapid-Microscope shards and must not be used as the canonical Rapid-Microscope readiness count.";
+
 // goal-referee-iter-13 (J-12): the readiness-fold blocks -- GET /research/desk/referee/evidence's
 // FIRST direct UI reader (registered since J-01/iteration-1; previously curl/tests-only). Rendered
 // directly BELOW the shipped Registered Hypotheses table above, inside the SAME "Referee Registry"
@@ -5196,6 +5207,12 @@ function RefereeEvidenceReadinessSection({
         >
           {evidence.strategy_trade.tick_gate_statement}
         </p>
+        <p
+          data-testid="referee-evidence-strategy-seal-unaware-caveat"
+          className="mt-2 text-[11px] text-slate-500"
+        >
+          {REFEREE_EVIDENCE_SEAL_UNAWARE_CAVEAT}
+        </p>
         <ul
           data-testid="referee-evidence-strategy-basis-caveats"
           className="mt-2 space-y-1 text-[11px] text-slate-500"
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 7 +++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl | 2 ++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
