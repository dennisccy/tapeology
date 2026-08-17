# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/apps/backend/app/research/micro_join.py b/apps/backend/app/research/micro_join.py
index 3aa169a..9d54966 100644
--- a/apps/backend/app/research/micro_join.py
+++ b/apps/backend/app/research/micro_join.py
@@ -70,10 +70,13 @@ caller conditioning on a DEFERRED feature (whose ``available_at`` is later than
 not this module -- this join's own outcome rows are unconditioned.
 
 **Never a second replay, never a second parse.** Feature rows are read through
-``micro_snapshots.read_snapshot_rows`` (this module's ONLY door onto a snapshot's persisted rows,
-never a raw ``open()``) after ``load_snapshot_meta`` confirms the snapshot is CURRENT (TR-7); a
-dataset with no covering window, or a covering dataset with no currently-valid snapshot, is an
-honest ``no_covering_snapshot`` -- never a fabricated join."""
+``micro_accessor.MicroAccessor`` (J-05 re-point -- the sole legal door onto a snapshot's persisted
+rows, TR-3's import-ban; this module constructs it unfenced, ``origin=None``, since this call site
+has never been chronologically fenced and the legacy corpus it reads is r2-pre-marked exposed for
+its entire span regardless -- see ``micro_accessor.py``'s own module docstring, "Two callers, two
+disciplines") after ``load_snapshot_meta`` confirms the snapshot is CURRENT (TR-7); a dataset with
+no covering window, or a covering dataset with no currently-valid snapshot, is an honest
+``no_covering_snapshot`` -- never a fabricated join."""
 
 from __future__ import annotations
 
@@ -81,7 +84,8 @@ from typing import TYPE_CHECKING, Sequence
 
 from . import micro_features as mf
 from .datasets import DatasetStore, parse_utc_epoch
-from .micro_snapshots import load_snapshot_meta, read_snapshot_rows
+from .micro_accessor import MicroAccessor
+from .micro_snapshots import load_snapshot_meta
 
 if TYPE_CHECKING:  # pragma: no cover -- type-checking only, never a runtime import (no cycle risk)
     from ..config import Config
@@ -413,7 +417,13 @@ def _join_core(
     if found is None:
         return {"status": JOIN_STATUS_NO_COVERING_SNAPSHOT, **_ABSENT_JOIN}
     dataset_meta, _snapshot_meta = found
-    rows = read_snapshot_rows(snapshots_dir, dataset_meta["id"])
+    # J-05 re-point (TR-3's import-ban): the ONLY door onto a snapshot's persisted rows is now
+    # micro_accessor.py. `origin=None` is the disclosed UNFENCED mode -- this call site has never
+    # been chronologically fenced and the legacy corpus it reads is r2-pre-marked exposed for its
+    # entire span regardless (micro_accessor.py's own module docstring, "Two callers, two
+    # disciplines"); output is byte-identical to the direct `read_snapshot_rows` call it replaces
+    # (TC-4).
+    rows = MicroAccessor(dataset_store, snapshots_dir, config).read_snapshot_rows(dataset_meta["id"])
     trade_rows = _trade_rows(rows)
     trigger_logical_ts = _logical_ts(dataset_meta, at_epoch)
     i = _locate_at_or_before(trade_rows, trigger_logical_ts)
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index da201b2..205d0ed 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -1,31 +1,37 @@
-"""``/research/desk/micro/*`` -- Era "The Rapid Microscope": J-01's readiness fold plus J-02's
-three snapshot routes. A fresh router/file mounted separately in ``main.py``, mirroring
-``referee_routes.py``'s own precedent and rationale (that file's own docstring: "the SAME
-rationale desk_routes.py itself gives for splitting off routes.py"). The era's own Data Contract
-table (``docs/goal.md``'s Product Shape) names four MORE micro routes landing in later iterations
-(scout, walkforward, vault, recorder, graduation) under this SAME ``/research/desk/micro`` prefix
--- a dedicated file is the right home from the start.
-
-Depends on a store this route does NOT own: the dataset store dependency is imported verbatim
-from ``routes.get_dataset_store`` (never a second, redefined provider). The readiness cache and
-the snapshot-compute manager are this module's OWN wiring (the ``referee_routes.py`` precedent:
-"this module owns its own wiring end to end") -- the manager lives as a module-level singleton
+"""``/research/desk/micro/*`` -- Era "The Rapid Microscope": J-01's readiness fold, J-02's three
+snapshot routes, J-04's Scout routes, and J-05's three walk-forward routes. A fresh router/file
+mounted separately in ``main.py``, mirroring ``referee_routes.py``'s own precedent and rationale
+(that file's own docstring: "the SAME rationale desk_routes.py itself gives for splitting off
+routes.py"). The era's own Data Contract table (``docs/goal.md``'s Product Shape) names THREE more
+micro routes landing in later iterations (vault, recorder, graduation) under this SAME
+``/research/desk/micro`` prefix -- a dedicated file is the right home from the start.
+
+Depends on stores this route does NOT own: the dataset store dependency is imported verbatim from
+``routes.get_dataset_store``, the universe/bar-store dependencies from ``desk_routes.
+get_universe_store``/``routes.get_bar_store`` (never a second, redefined provider). The readiness
+cache and every compute manager are this module's OWN wiring (the ``referee_routes.py`` precedent:
+"this module owns its own wiring end to end") -- each manager lives as a module-level singleton
 behind a ``Depends``-able accessor (the ``desk_routes.py`` ``get_desk_playbook_compute_manager``
 precedent, so a test overrides the DEPENDENCY with a fresh manager, never reaches into the
 module-level singleton directly).
 
-``GET /readiness`` and ``GET /snapshots``/``GET /snapshots/runs`` are plain reads: page-load GETs
-never compute (T-8) -- a snapshot BUILD is an explicit operator act through
-``POST /snapshots/compute``, exactly like the desk's own compute-manager pattern."""
+``GET /readiness``, ``GET /snapshots``/``GET /snapshots/runs``, ``GET /scout``/``GET
+/scout/runs``, and ``GET /walkforward``/``GET /walkforward/runs`` are all plain reads: page-load
+GETs never compute (T-8) -- a build/screen/fold-evaluation RUN is always an explicit operator act
+through its own ``POST .../compute``, exactly the same desk compute-manager pattern three times
+over."""
 
 from __future__ import annotations
 
 from fastapi import APIRouter, Depends, HTTPException
 
 from ..config import CONFIG
+from .bars import BarStore
 from .datasets import DatasetStore
 from .desk_playbook import PlaybookStore
-from .desk_routes import get_playbook_store
+from .desk_routes import get_playbook_store, get_universe_store
+from .desk_universe import UniverseStore
+from .micro_accessor import ExposureRegistry, resolve_micro_exposure_registry_dir
 from .micro_readiness import MicroReadinessCache, build_readiness, resolve_micro_readiness_cache_db_path
 from .micro_snapshots import (
     MicroSnapshotComputeManager,
@@ -33,9 +39,11 @@ from .micro_snapshots import (
     read_run_log,
     resolve_micro_snapshots_dir,
 )
-from .routes import get_dataset_store
+from .routes import get_bar_store, get_dataset_store
 from .scout import ScoutComputeManager, list_scout_families
 from .scout_ledger import ScoutLedger, resolve_scout_ledger_dir
+from . import walkforward as wf
+from .walkforward_ledger import WalkForwardLedger
 
 router = APIRouter(prefix="/research/desk/micro", tags=["micro"])
 
@@ -247,3 +255,113 @@ def cancel_scout_compute(manager: ScoutComputeManager = Depends(get_scout_comput
 def get_scout_runs(ledger_dir: str = Depends(get_scout_ledger_dir)) -> dict:
     """The durable run history, newest first -- never 404 on zero runs (an honest empty list)."""
     return {"runs": read_run_log(ledger_dir)}
+
+
+# --- J-05: the chronological walk-forward engine (walkforward.py, walkforward_ledger.py) --------
+
+
+def get_walkforward_ledger_dir() -> str:
+    """The walk-forward ledger's directory -- ``TAPEOLOGY_MICRO_WALKFORWARD_DIR`` if set, else a
+    SIBLING of the config-owned dataset directory (``walkforward.resolve_walkforward_ledger_dir``
+    -- see that function's own docstring)."""
+    return wf.resolve_walkforward_ledger_dir(CONFIG.dataset_dir_resolved())
+
+
+def get_micro_exposure_registry_dir() -> str:
+    """The exposure registry's directory -- ``TAPEOLOGY_MICRO_EXPOSURE_REGISTRY_DIR`` if set, else
+    a SIBLING of the config-owned dataset directory (``micro_accessor.resolve_micro_exposure_
+    registry_dir`` -- see that function's own docstring). Shared by every J-05 caller that logs or
+    reads exposure state, not owned exclusively by this route file."""
+    return resolve_micro_exposure_registry_dir(CONFIG.dataset_dir_resolved())
+
+
+# The single in-flight (or last-terminal) walk-forward job for THIS process -- the same
+# module-singleton-behind-a-Depends-accessor precedent as the snapshot/scout managers above.
+_walkforward_compute_manager = wf.WalkForwardComputeManager()
+
+
+def get_walkforward_compute_manager() -> "wf.WalkForwardComputeManager":
+    """A FastAPI dependency so a test overrides it outright with a fresh, isolated manager (the
+    ``get_scout_compute_manager`` precedent) -- never reaches into the module-level singleton
+    directly."""
+    return _walkforward_compute_manager
+
+
+@router.get("/walkforward")
+def get_walkforward(ledger_dir: str = Depends(get_walkforward_ledger_dir)) -> dict:
+    """Every registered fold spec plus every sequence's fold results, decay view, and sequence
+    verdict (``wf.list_fold_specs``/``wf.list_walkforward_sequences`` -- see those functions' own
+    docstrings), BESIDE the ledger's own chain-verification verdict (the ``GET /scout`` precedent:
+    surfaced beside the data rather than refused, never silently accepted if tampered). Never
+    404/500 on an empty ledger -- an honest empty ``fold_specs``/``sequences``, the desk router's
+    established never-404-on-absence convention. Page-load GETs never compute (T-8): a fold-
+    evaluation RUN is an explicit operator act through ``POST /walkforward/compute``."""
+    ledger = WalkForwardLedger(ledger_dir)
+    return {
+        "fold_specs": wf.list_fold_specs(ledger),
+        "sequences": wf.list_walkforward_sequences(ledger),
+        "chain_verification": ledger.verify_chain(),
+    }
+
+
+@router.post("/walkforward/compute")
+def trigger_walkforward_compute(
+    ledger_dir: str = Depends(get_walkforward_ledger_dir),
+    exposure_registry_dir: str = Depends(get_micro_exposure_registry_dir),
+    universe_store: UniverseStore = Depends(get_universe_store),
+    bar_store: BarStore = Depends(get_bar_store),
+    playbook_store: PlaybookStore = Depends(get_playbook_store),
+    manager: "wf.WalkForwardComputeManager" = Depends(get_walkforward_compute_manager),
+) -> dict:
+    """Start the diagnostic acceptance run (goal.md J-05 IN SCOPE item 8) against the operator's
+    REAL playbook/universe/bar stores, or refuse (single-flight) if one is already running. The
+    ONLY mode this iteration wires -- Mode A/pilot-study registrations are J-09's own scope."""
+    ledger = WalkForwardLedger(ledger_dir)
+    exposure_registry = ExposureRegistry(exposure_registry_dir)
+
+    def _work(publish, should_abort) -> dict:
+        result = wf.run_diagnostic_walkforward(
+            ledger, exposure_registry, playbook_store, universe_store, bar_store, CONFIG,
+            progress=publish, should_abort=should_abort,
+        )
+        return {
+            "folds_evaluated": result["folds_evaluated"],
+            "validation_sessions": result["validation_sessions"],
+            "session_count": result["session_count"],
+        }
+
+    result = manager.trigger(_work, run_log_dir=ledger_dir, steps_total=1)
+    if result["state"] == "refused":
+        return result
+    return {"state": result["state"], "run_id": result["run_id"]}
+
+
+@router.get("/walkforward/compute")
+def get_walkforward_compute(manager: "wf.WalkForwardComputeManager" = Depends(get_walkforward_compute_manager)) -> dict:
+    """The current (or last-terminal) run's progress -- never 404 (the idle default before any job
+    has ever run this process)."""
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
+@router.post("/walkforward/compute/cancel")
+def cancel_walkforward_compute(manager: "wf.WalkForwardComputeManager" = Depends(get_walkforward_compute_manager)) -> dict:
+    """Signal cooperative cancellation for the in-flight job -- a 409 for an idle manager (the
+    snapshot/scout-compute-cancel routes' own precedent), else ``{"state": "cancelled"}``
+    acknowledging the REQUEST (the worker itself settles at the next fold boundary)."""
+    if manager.snapshot()["state"] != "running":
+        raise HTTPException(status_code=409, detail="no walk-forward run is currently running")
+    manager.cancel()
+    return {"state": "cancelled"}
+
+
+@router.get("/walkforward/runs")
+def get_walkforward_runs(ledger_dir: str = Depends(get_walkforward_ledger_dir)) -> dict:
+    """The durable run history, newest first -- never 404 on zero runs (an honest empty list)."""
+    return {"runs": read_run_log(ledger_dir)}
diff --git a/apps/backend/app/research/scout.py b/apps/backend/app/research/scout.py
index 4d9409f..5c4c748 100644
--- a/apps/backend/app/research/scout.py
+++ b/apps/backend/app/research/scout.py
@@ -17,8 +17,9 @@ only builds and proves the generic screening machinery, and runs it on a bounded
 values yet.
 
 **Read-side law: no second outcome implementation.** Anchor extraction reads snapshot rows through
-``micro_snapshots.read_snapshot_rows`` (after ``load_snapshot_meta`` confirms currency, TR-7) and
-computes each anchor's outcome through ``micro_join.outcome_rows_after_trigger`` -- the SAME closed
+``micro_accessor.MicroAccessor`` (J-05 re-point, unfenced -- TR-3's import-ban; after
+``load_snapshot_meta`` confirms currency, TR-7) and computes each anchor's outcome through
+``micro_join.outcome_rows_after_trigger`` -- the SAME closed
 outcome set ``micro_join.py`` already proved end to end. This module adds no new outcome math, only
 the STATISTICAL SCREEN over outcomes ``micro_join.py`` already knows how to compute.
 
@@ -78,10 +79,10 @@ from ..config import CONFIG, Config
 from . import micro_features as mf
 from . import micro_join as mj
 from .datasets import DatasetNotFound, DatasetStore, parse_utc_epoch
+from .micro_accessor import MicroAccessor
 from .micro_snapshots import (
     append_run_log,
     load_snapshot_meta,
-    read_snapshot_rows,
     resolve_micro_snapshots_dir,
     run_snapshot_build_and_record,
 )
@@ -340,7 +341,15 @@ def _cached_dataset_rows(
         return None, None
     if rows_cache is not None and dataset_id in rows_cache:
         return dataset_meta, rows_cache[dataset_id]
-    rows = read_snapshot_rows(snapshots_dir, dataset_id)
+    # J-05 re-point (TR-3's import-ban): the ONLY door onto a snapshot's persisted rows is now
+    # micro_accessor.py. `origin=None` is the disclosed UNFENCED mode (micro_accessor.py's own
+    # module docstring, "Two callers, two disciplines") -- this call site has never been
+    # chronologically fenced, the legacy corpus it reads is r2-pre-marked exposed regardless, and
+    # fencing/exposure-logging it now would reintroduce exactly the O(n)-per-anchor cost the iter-4
+    # audit's perf fixes eliminated for a registry entry that would be redundant with r2's own
+    # initialization. Output is byte-identical to the direct `read_snapshot_rows` call it replaces
+    # (TC-5).
+    rows = MicroAccessor(dataset_store, snapshots_dir, config).read_snapshot_rows(dataset_id)
     if rows_cache is not None:
         rows_cache[dataset_id] = rows
     return dataset_meta, rows
diff --git a/apps/backend/tests/test_micro_join.py b/apps/backend/tests/test_micro_join.py
index 3104817..7c9c2f1 100644
--- a/apps/backend/tests/test_micro_join.py
+++ b/apps/backend/tests/test_micro_join.py
@@ -34,7 +34,7 @@ from app.research import micro_join
 from app.research.datasets import DatasetStore
 from app.research.desk_playbook import PlaybookStore, playbook_parameters
 from app.research.desk_playbook_context import BandMapResolver
-from app.research.micro_snapshots import read_snapshot_rows, run_snapshot_build_and_record
+from app.research.micro_snapshots import read_snapshot_rows, resolve_micro_snapshots_dir, run_snapshot_build_and_record
 from app.research.tradability_cache import TradabilityCache
 
 FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "datasets_j03"
@@ -628,6 +628,40 @@ def test_tc16_real_corpus_joinable_corpus_arithmetic_is_unchanged_by_the_passeng
     assert counts["band_touch_count"] == {"status": micro_join.BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None}
 
 
+# --- J-05 TC-4: the accessor re-point (micro_accessor.MicroAccessor, unfenced) serves the SAME ------
+# --- real-corpus join result as the pre-re-point direct micro_snapshots.read_snapshot_rows call. ----
+
+
+def test_tc4_real_corpus_join_playbook_signal_is_unaffected_by_the_accessor_re_point():
+    """The ONE real recorded playbook signal whose window falls inside a recorded tick dataset AND
+    already carries a currently-valid built snapshot on disk (verified live, not assumed) --
+    ``_join_core``'s re-pointed ``MicroAccessor(...).read_snapshot_rows(...)`` call (J-05) must
+    still resolve this join exactly as the pre-re-point direct call did: ``status == "joined"``, a
+    non-``None`` ``feature_at_trigger``, and a full closed outcome set."""
+    from app.research.desk_playbook import resolve_desk_playbook_dir
+
+    dataset_store = DatasetStore(CONFIG.dataset_dir_resolved())
+    playbook_store = PlaybookStore(resolve_desk_playbook_dir(CONFIG.desk_universe_dir_resolved()))
+    snapshots_dir = resolve_micro_snapshots_dir(CONFIG.dataset_dir_resolved())
+
+    playbook_records, _errors = playbook_store.list()
+    signal = None
+    for record in playbook_records:
+        for candidate in record.get("signals") or []:
+            if candidate.get("symbol") == "AMZN" and candidate.get("trigger_ts") == "2026-06-26T16:20:00.000000Z":
+                signal = candidate
+                break
+        if signal is not None:
+            break
+    assert signal is not None, "the fixed real-corpus signal this test pins is no longer on disk"
+
+    result = micro_join.join_playbook_signal(signal, dataset_store, snapshots_dir, CONFIG)
+    assert result["status"] == micro_join.JOIN_STATUS_JOINED
+    assert result["feature_at_trigger"] is not None
+    assert result["dataset_id"] == "60e0cd6613804fdaa87d549dcef38d31"
+    assert len(result["outcomes"]) == 7  # the closed outcome set: 2 trades + 2 shares + 3 clock
+
+
 # --- iter-4 perf fix: outcome_rows_at_position / outcome_row_at_single_horizon are byte-identical
 # to outcome_rows_after_trigger's own output -- added when a live Scout run against the real
 # 18-dataset corpus (J-04) exposed an O(n^2) cost in the O(n) `.index()` lookup + a per-call
diff --git a/apps/backend/tests/test_scout.py b/apps/backend/tests/test_scout.py
index 8b10016..6d31072 100644
--- a/apps/backend/tests/test_scout.py
+++ b/apps/backend/tests/test_scout.py
@@ -645,6 +645,29 @@ def test_tc10_a_failed_run_never_writes_a_silently_short_ledger(tmp_path, monkey
 # === TC-11: manager-triggered and CLI-triggered runs produce identical ledger content ================
 
 
+# === J-05 TC-5: the accessor re-point (micro_accessor.MicroAccessor, unfenced) is byte-identical ===
+
+
+def test_tc5_the_iteration_4_bounded_fixture_grid_still_reads_killed_insufficient_n_after_the_re_point(tmp_path):
+    """``_cached_dataset_rows``'s re-pointed ``MicroAccessor(...).read_snapshot_rows(...)`` call
+    (J-05) must reproduce the EXACT documented iteration-4 baseline for the default fixture grid --
+    every one of its 6 candidates over the committed ``datasets``/``datasets_j03`` fixtures (all
+    one session date) honestly reads ``killed_insufficient_n`` (the iter-4 dev handoff's own
+    finding: "zero survivors is a passing grade")."""
+    store = _combined_fixture_store(tmp_path)
+    snapshots_dir = str(tmp_path / "snapshots")
+    run_snapshot_build_and_record(store, CONFIG, snapshots_dir, None)
+    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
+    grid = scout.default_fixture_grid(store, grid_version=1)
+
+    rows = scout.run_scout_grid_and_record(grid, ledger, store, snapshots_dir, CONFIG)
+
+    assert len(rows) == 6
+    for row in rows:
+        assert row["decision"] == "killed_insufficient_n"
+        assert row["reason"] == "killed_insufficient_n"
+
+
 def test_tc11_manager_and_cli_produce_byte_identical_spec_hash_and_decision_per_candidate(tmp_path):
     store = _combined_fixture_store(tmp_path)
     snapshots_dir = str(tmp_path / "snapshots")
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 9 +++++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl | 2 ++
 2 files changed, 11 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
