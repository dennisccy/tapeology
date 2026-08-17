# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

```diff
diff --git a/apps/backend/app/research/datasets.py b/apps/backend/app/research/datasets.py
index a38b3dc..76f7861 100644
--- a/apps/backend/app/research/datasets.py
+++ b/apps/backend/app/research/datasets.py
@@ -373,16 +373,29 @@ class DatasetStore:
         symbol = loaded.meta["symbol"]
         return [_row_to_event(symbol, row) for row in loaded.rows]
 
-    def replay(self, dataset_id: str, config: Config) -> Iterator[EngineSnapshot]:
+    def replay(
+        self, dataset_id: str, config: Config, *, observer: object | None = None
+    ) -> Iterator[EngineSnapshot]:
         """Replay the stored dataset UNPACED through a FRESH ``TapeEngine``, yielding every
         per-event snapshot. Deterministic: the stored stream, the stored
         source descriptor, and the stored epoch anchor fully determine the output — re-runs are
-        byte-identical, and both match replaying the original source stream."""
+        byte-identical, and both match replaying the original source stream.
+
+        ``observer`` (era "The Rapid Microscope" J-02, spec section 2.1) is an ADDITIVE,
+        default-``None`` kwarg: when given, it is registered on the fresh engine via the EXISTING
+        ``TapeEngine.add_observer`` seam (capability 20) once, before the event loop starts.
+        ``observer=None`` is byte-identical to before this kwarg existed — every pre-existing call
+        site (none of which pass it) is unaffected, and ``tests/test_observer_equivalence.py``
+        already proves attaching an observer never perturbs a single yielded snapshot. This is the
+        ONE replay entry point; no second replay implementation exists anywhere for research code
+        to attach to."""
         loaded = self._load_by_id(dataset_id)
         meta = loaded.meta
         engine = TapeEngine(
             meta["symbol"], meta["source"], config, epoch_anchor=meta["epoch_anchor"]
         )
+        if observer is not None:
+            engine.add_observer(observer)
         for row in loaded.rows:
             yield engine.process_event(_row_to_event(meta["symbol"], row))
 
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index b5d34af..7fdf083 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -1,28 +1,36 @@
-"""``/research/desk/micro/*`` -- Era "The Rapid Microscope": J-01's readiness fold, the era's
-first route. A fresh router/file mounted separately in ``main.py``, mirroring
+"""``/research/desk/micro/*`` -- Era "The Rapid Microscope": J-01's readiness fold plus J-02's
+three snapshot routes. A fresh router/file mounted separately in ``main.py``, mirroring
 ``referee_routes.py``'s own precedent and rationale (that file's own docstring: "the SAME
 rationale desk_routes.py itself gives for splitting off routes.py"). The era's own Data Contract
-table (``docs/goal.md``'s Product Shape) names six MORE micro routes landing in later iterations
-(snapshots, scout, walkforward, vault, recorder, graduation) under this SAME
-``/research/desk/micro`` prefix -- a dedicated file is the right home from the start.
+table (``docs/goal.md``'s Product Shape) names four MORE micro routes landing in later iterations
+(scout, walkforward, vault, recorder, graduation) under this SAME ``/research/desk/micro`` prefix
+-- a dedicated file is the right home from the start.
 
 Depends on a store this route does NOT own: the dataset store dependency is imported verbatim
-from ``routes.get_dataset_store`` (never a second, redefined provider). The readiness cache is
-this module's OWN wiring (the ``referee_routes.py`` precedent: "this module owns its own wiring
-end to end") -- a config-derived, env-overridable path exactly like every sibling durable cache's
-own FastAPI dependency (``get_edge_report_cache``/``get_bar_index`` in ``routes.py``).
+from ``routes.get_dataset_store`` (never a second, redefined provider). The readiness cache and
+the snapshot-compute manager are this module's OWN wiring (the ``referee_routes.py`` precedent:
+"this module owns its own wiring end to end") -- the manager lives as a module-level singleton
+behind a ``Depends``-able accessor (the ``desk_routes.py`` ``get_desk_playbook_compute_manager``
+precedent, so a test overrides the DEPENDENCY with a fresh manager, never reaches into the
+module-level singleton directly).
 
-``GET /readiness`` is a plain read: it triggers nothing but the readiness fold's own documented
-one-time-then-cached per-shard classification (page-load GETs never compute a SECOND time, T-8;
-the module itself is the ONE place, this route only wires it)."""
+``GET /readiness`` and ``GET /snapshots``/``GET /snapshots/runs`` are plain reads: page-load GETs
+never compute (T-8) -- a snapshot BUILD is an explicit operator act through
+``POST /snapshots/compute``, exactly like the desk's own compute-manager pattern."""
 
 from __future__ import annotations
 
-from fastapi import APIRouter, Depends
+from fastapi import APIRouter, Depends, HTTPException
 
 from ..config import CONFIG
 from .datasets import DatasetStore
 from .micro_readiness import MicroReadinessCache, build_readiness, resolve_micro_readiness_cache_db_path
+from .micro_snapshots import (
+    MicroSnapshotComputeManager,
+    list_snapshot_meta,
+    read_run_log,
+    resolve_micro_snapshots_dir,
+)
 from .routes import get_dataset_store
 
 router = APIRouter(prefix="/research/desk/micro", tags=["micro"])
@@ -50,3 +58,88 @@ def get_micro_readiness(
     ``shards`` list (``study_floors`` still carries its 3 rows, each read against a 0-session
     corpus) at HTTP 200."""
     return build_readiness(dataset_store, cache, dataset_dir=CONFIG.dataset_dir_resolved())
+
+
+def get_micro_snapshots_dir() -> str:
+    """The snapshot store's directory -- ``TAPEOLOGY_MICRO_SNAPSHOTS_DIR`` if set, else a
+    SIBLING of the config-owned dataset directory (``micro_snapshots.resolve_micro_snapshots_dir``
+    -- see that function's own docstring)."""
+    return resolve_micro_snapshots_dir(CONFIG.dataset_dir_resolved())
+
+
+# The single in-flight (or last-terminal) snapshot-build job for THIS process -- the
+# ``desk_routes.py`` module-singleton-behind-a-Depends-accessor precedent (module docstring), never
+# per-request-constructed (a fresh manager per request could never observe a job it just started).
+_micro_snapshot_compute_manager = MicroSnapshotComputeManager()
+
+
+def get_micro_snapshot_compute_manager() -> MicroSnapshotComputeManager:
+    """A FastAPI dependency so a test overrides it outright with a fresh, isolated manager (the
+    ``get_desk_playbook_compute_manager`` precedent) -- never reaches into the module-level
+    singleton directly."""
+    return _micro_snapshot_compute_manager
+
+
+@router.get("/snapshots")
+def get_micro_snapshots(
+    dataset_store: DatasetStore = Depends(get_dataset_store),
+    snapshots_dir: str = Depends(get_micro_snapshots_dir),
+) -> dict:
+    """BUILD METADATA only -- the identity tuple, ``row_count``, ``quote_size_unit``, timestamps
+    -- for every CURRENTLY VALID (identity re-verified) snapshot; never raw per-event feature
+    rows (the boundary note: an origin-fenced, event-level read is ``micro_accessor.py``'s
+    exclusive door, J-05, not this route). Never 404/500 on zero built snapshots -- an honest
+    empty list, the desk router's established convention."""
+    return {"snapshots": list_snapshot_meta(snapshots_dir, dataset_store, CONFIG)}
+
+
+@router.post("/snapshots/compute")
+def trigger_micro_snapshots_compute(
+    dataset_store: DatasetStore = Depends(get_dataset_store),
+    snapshots_dir: str = Depends(get_micro_snapshots_dir),
+    manager: MicroSnapshotComputeManager = Depends(get_micro_snapshot_compute_manager),
+) -> dict:
+    """Start a snapshot build for every dataset currently in the store (reusing any already-valid
+    snapshot -- ``run_snapshot_build_and_record``'s own reuse-or-build discipline), or refuse
+    (single-flight) if one is already running."""
+    result = manager.trigger(dataset_store, CONFIG, snapshots_dir)
+    if result["state"] == "refused":
+        return result
+    return {"state": result["state"], "run_id": result["run_id"]}
+
+
+@router.get("/snapshots/compute")
+def get_micro_snapshots_compute(
+    manager: MicroSnapshotComputeManager = Depends(get_micro_snapshot_compute_manager),
+) -> dict:
+    """The current (or last-terminal) build job's progress -- never 404 (the ``_IDLE_SNAPSHOT``
+    default before any job has ever run this process)."""
+    snap = manager.snapshot()
+    return {
+        "state": snap["state"],
+        "progress": snap["progress"],
+        "started_utc": snap["started_utc"],
+        "finished_utc": snap["finished_utc"],
+        "error": snap["error"],
+    }
+
+
+@router.post("/snapshots/compute/cancel")
+def cancel_micro_snapshots_compute(
+    manager: MicroSnapshotComputeManager = Depends(get_micro_snapshot_compute_manager),
+) -> dict:
+    """Signal cooperative cancellation for the in-flight job -- a 409 for an idle manager (the
+    ``desk_playbook`` "the ROUTE is the one that rejects an idle cancel with a 409" precedent),
+    else ``{"state": "cancelled"}`` acknowledging the REQUEST (the worker itself settles at the
+    next dataset boundary -- ``MicroSnapshotComputeManager.cancel``'s own docstring)."""
+    if manager.snapshot()["state"] != "running":
+        raise HTTPException(status_code=409, detail="no snapshot build is currently running")
+    manager.cancel()
+    return {"state": "cancelled"}
+
+
+@router.get("/snapshots/runs")
+def get_micro_snapshots_runs(snapshots_dir: str = Depends(get_micro_snapshots_dir)) -> dict:
+    """The durable build-run history, newest first -- never 404 on zero runs (an honest empty
+    list)."""
+    return {"runs": read_run_log(snapshots_dir)}
diff --git a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
index bc02591..a9c445b 100644
--- a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
+++ b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
@@ -36,6 +36,17 @@
 # (read-only) so J-10's /structure step measures the kept product, not a fixture. See that script's
 # own docstring for the nineteen-member universe and the two computes it records.
 #
+# goal-rapid-microscope-iter-2 (J-01's browser gap + J-02 test infra) extends it once more, again
+# in place (never rewritten — this file's own long-standing rule): stages the two ALREADY-COMMITTED
+# PG SIP tick-dataset fixtures (tests/fixtures/datasets/*.json — the exact on-disk DatasetStore file
+# shape, so a plain copy suffices; never a pointer at, or copy of, the real .data/datasets store)
+# into this rig's own throwaway $ROOT/datasets before backend start, mirroring how the datasets dir
+# was already exported (TAPEOLOGY_DATASET_DIR) but left with zero tick shards. This closes the gap
+# iteration 1 left open: the Microscope Readiness panel could only be proven via API/text-extract
+# through this mandated rig, never a real non-empty screenshot (T-10). Real, non-fabricated, but
+# deliberately small — seeding the full 18-dataset/12-symbol-day corpus is deferred to whichever
+# LATER iteration first needs it (J-06/J-08/J-09), per the rubric's "smallest fix that unblocks now."
+#
 # The default root name changes to playbook-iter8-replay-fixture-qa (a genuinely FRESH root, never
 # an earlier one reused) — the universe/signature composition is wider again, and the script's own
 # long-standing rule ("use a fresh root whenever the seeded composition changed") applies to this
@@ -75,6 +86,13 @@ JOURNAL_DB="$ROOT/journal.db"
 mkdir -p "$BAR_DIR" "$UNIVERSE_DIR" "$PLAYBOOK_DIR" "$PLAYBOOK_LOG_DIR" \
          "$PLAYBOOK_BACKSCAN_LOG_DIR" "$SCREEN_DIR" "$DATASET_DIR"
 
+# goal-rapid-microscope-iter-2: seed the two already-committed PG SIP tick-dataset fixtures (a
+# plain file copy — the fixture IS the on-disk DatasetStore shape already) so J-01's Microscope
+# Readiness panel finally photographs a real, non-empty shard table through this rig instead of an
+# empty corpus (see the header comment above).
+cp "$BACKEND_DIR/tests/fixtures/datasets/6c9bf2c700d749e0993efd92c5807de3.json" "$DATASET_DIR/"
+cp "$BACKEND_DIR/tests/fixtures/datasets/d9f9dbe04fb24a7caccc53f0c6805412.json" "$DATASET_DIR/"
+
 export TAPEOLOGY_BAR_DIR="$BAR_DIR"
 export TAPEOLOGY_DESK_UNIVERSE_DIR="$UNIVERSE_DIR"
 export TAPEOLOGY_DESK_PLAYBOOK_DIR="$PLAYBOOK_DIR"
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index c7d8b12..5a5177b 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -517,6 +517,21 @@ def test_desk_page_price_arithmetic_guard_catches_evidence_basis_field_arithmeti
     seeded_signal_unmeasured = "const measured = cell.signal.n - cell.signal.n_unmeasured;"
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_signal_unmeasured) is not None
 
+    seeded_signal_sessions = "const perSession = cell.signal.n / cell.signal.n_sessions;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_signal_sessions) is not None
+
+    seeded_baseline_truncated = "const clean = cell.baseline.n_baseline - cell.baseline.n_truncated;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_truncated) is not None
+
+    seeded_baseline_unmeasured = "const total = cell.baseline.n_baseline + cell.baseline.n_unmeasured;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_unmeasured) is not None
+
+    seeded_baseline_sessions = "const perSession = cell.baseline.n_baseline / cell.baseline.n_sessions;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_sessions) is not None
+
+    seeded_basis = "const perDate = basis.n_records / basis.dates.length;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_basis) is not None
+
 
 def test_desk_page_price_arithmetic_guard_catches_micro_readiness_field_arithmetic():
     """goal-rapid-microscope-iter-1 (J-01) TC-9 counter-test: the extended guard catches
@@ -538,21 +553,6 @@ def test_desk_page_price_arithmetic_guard_catches_micro_readiness_field_arithmet
     seeded_shortfall = "const shortfall = floor.required_sessions - floor.available_sessions;"
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_shortfall) is not None
 
-    seeded_signal_sessions = "const perSession = cell.signal.n / cell.signal.n_sessions;"
-    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_signal_sessions) is not None
-
-    seeded_baseline_truncated = "const clean = cell.baseline.n_baseline - cell.baseline.n_truncated;"
-    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_truncated) is not None
-
-    seeded_baseline_unmeasured = "const total = cell.baseline.n_baseline + cell.baseline.n_unmeasured;"
-    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_unmeasured) is not None
-
-    seeded_baseline_sessions = "const perSession = cell.baseline.n_baseline / cell.baseline.n_sessions;"
-    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_sessions) is not None
-
-    seeded_basis = "const perDate = basis.n_records / basis.dates.length;"
-    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_basis) is not None
-
     # And the pattern does NOT over-match: the real page's own guard test below still finds zero
     # hits, so this new coverage does not accidentally flag legitimate, non-arithmetic JSX.
     assert _PRICE_ARITHMETIC_PATTERN.search("const label = `${basis.n_records} records`;") is None
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 18 ++++++++++++++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl |  4 ++++
 2 files changed, 22 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
