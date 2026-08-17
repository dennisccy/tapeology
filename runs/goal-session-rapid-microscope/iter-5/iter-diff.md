# Iteration diff (bounded)

Files changed: 13. Shown in full: 11.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/walkforward.py` (776 lines not shown)
- `apps/backend/tests/test_walkforward.py` (488 lines not shown)

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
index da201b2..b4ac635 100644
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
 
@@ -247,3 +255,117 @@ def cancel_scout_compute(manager: ScoutComputeManager = Depends(get_scout_comput
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
+            # Disclosed beside the count above so a repeat trigger's run-log entry reads honestly:
+            # a re-run replays the SAME folds' existing ledger rows rather than recording the same
+            # evidence twice (``walkforward_ledger.append_fold_result``'s own docstring).
+            "folds_replayed": result["folds_replayed"],
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
diff --git a/apps/backend/app/research/micro_accessor.py b/apps/backend/app/research/micro_accessor.py
new file mode 100644
index 0000000..165f300
--- /dev/null
+++ b/apps/backend/app/research/micro_accessor.py
@@ -0,0 +1,269 @@
+"""``micro_accessor.py`` -- Era "The Rapid Microscope" J-05: the origin-fenced accessor
+
+(``docs/rapid-validation-spec.md`` section 6.1) -- the sole legal door onto the micro snapshot
+corpus (and, generically, future vault event data, J-06). Two independent disciplines live here:
+
+**1. The origin fence (TR-3).** ``MicroAccessor(dataset_store, snapshots_dir, config, origin=T)``
+refuses -- with a typed error, never an empty result -- any read of a dataset whose OWN session
+date (spec section 0: "a session is an ET RTH trading date") falls strictly after ``T``. A dataset
+is fenced as a WHOLE unit: a recorded RTH window never spans an ET midnight (the
+``micro_readiness.py``/``scout.py`` precedent), so "the dataset's session date" is unambiguous.
+``origin=None`` (the DEFAULT) is an explicit, disclosed UNFENCED mode -- see "Two callers, two
+disciplines" below.
+
+**2. Sealed-shard invisibility (TR-2 in spirit; the vault itself does not exist until J-06).** A
+caller MAY pass ``sealed_dataset_ids`` (a frozenset of dataset ids currently sealed) -- a read of
+one of those ids raises ``MicroAccessorSealedShardError`` carrying only the section 7.5 OPAQUE
+metadata (``shard_id``, a coarse size bucket, never symbol/date/rows), never the underlying rows.
+Empty by default (no vault exists yet), so every EXISTING call site behaves exactly as before this
+module existed -- this is the "generic hook a J-06 vault can extend without re-deriving the
+discipline" the goal.md IN SCOPE names, proven now on a fixture (TC-2) rather than left unbuilt
+and unproven until J-06 lands.
+
+**Two callers, two disciplines (a disclosed interpretation call, T-1).** ``micro_join.py`` and
+``scout.py`` are re-pointed THROUGH this module this iteration (TR-3's import-ban), but their own
+served/ledgered values must stay BYTE-IDENTICAL (TC-4, TC-5) -- they have never been
+chronologically fenced, and the corpus they read (the legacy tick corpus) is r2-pre-marked
+EXPOSED for its entire span regardless. Fencing them now would be a silent, unrequested behavior
+change smuggled into a "just move the import" iteration. So: ``origin=None`` is the UNFENCED mode
+those two callers construct (every read passes, exactly today's behavior) and it does NOT log to
+the exposure registry either -- appending a hash-chained row on every one of ``scout.
+extract_anchors``'s thousands-of-anchors-per-dataset calls would reintroduce exactly the O(n)-
+per-read cost the iter-4 audit's perf fixes eliminated, for a registry entry that would be
+redundant with r2's own initialization (every window of the legacy/playbook corpus is ALREADY
+marked exposed from the moment the registry exists -- see ``ExposureRegistry`` below). Only
+``walkforward.py``'s OWN origin-fenced reads (an ``origin`` given, an ``ExposureRegistry`` given)
+participate in exposure logging -- the one path where "was this window ever served before?" is an
+actual, load-bearing question this era asks.
+
+**The exposure registry (section 6.7, r2).** ``ExposureRegistry`` is a corpus-scoped, hash-chained
+ledger (``micro_chain_ledger.HashChainedLedger``) of ``{surface, window, corpus_id, logged_at}``
+entries. ``initialize_r2_exposure_registry`` seeds it, ONCE, with every window this era already
+knows is exposed -- every session-date of the 155-session playbook corpus and of the 12 legacy
+tick symbol-days (TC-14) -- stamped at the r2 revision instant
+(``R2_REVISION_INSTANT``, 2026-08-16, this spec revision's own date), so a FRESH walk-forward spec
+registered any time after that instant reads those windows as already-exposed with no serving act
+required in the current run. A registry for a genuinely NEW corpus_id (e.g. this iteration's own
+TR-16 synthetic oracle fixtures) starts EMPTY -- nothing pre-marks a corpus this module has never
+heard of, so a spec registered against a freshly-built synthetic corpus can legitimately classify
+``historical_oos`` (TC-21, TC-22)."""
+
+from __future__ import annotations
+
+import os
+from datetime import datetime, timezone
+from pathlib import Path
+from zoneinfo import ZoneInfo
+
+from ..config import Config
+from .datasets import DatasetNotFound, DatasetStore
+from .micro_chain_ledger import HashChainedLedger
+from .micro_snapshots import read_snapshot_rows as _raw_read_snapshot_rows
+
+__all__ = [
+    "R2_REVISION_INSTANT",
+    "MicroAccessorOriginFenceError",
+    "MicroAccessorSealedShardError",
+    "MicroAccessor",
+    "ExposureRegistry",
+    "resolve_micro_exposure_registry_dir",
+    "initialize_r2_exposure_registry",
+    "has_any_exposure_entries",
+]
+
+# The r2 spec revision's own date (docs/rapid-validation-spec.md's revision header) -- the instant
+# every legacy-corpus/playbook-corpus window is honestly treated as "already exposed" from,
+# because their aggregates have in fact been served (readiness, evidence, forward reports) for
+# months before this era's spec was even written. Never a wall-clock read at call time -- a fixed,
+# named instant, exactly like every other frozen constant in this era.
+R2_REVISION_INSTANT = "2026-08-16T00:00:00.000000Z"
+
+_ET_ZONE = ZoneInfo("America/New_York")
+
+_EXPOSURE_REGISTRY_DIR_ENV = "TAPEOLOGY_MICRO_EXPOSURE_REGISTRY_DIR"
+_EXPOSURE_LEDGER_FILENAME = "exposure_registry.jsonl"
+
+
+class MicroAccessorOriginFenceError(Exception):
+    """A read was requested for a dataset whose own session date falls strictly after this
+    accessor's ``origin`` -- refused, never an empty or silently-truncated result (TC-1)."""
+
+
+class MicroAccessorSealedShardError(Exception):
+    """A read was requested for a dataset id this accessor's view marks ``sealed`` -- refused;
+    only section 7.5's opaque metadata is ever attached to this error, never the underlying rows
+    (TC-2). Carries ``shard_id`` for a caller that wants to report which shard, never a row."""
+
+    def __init__(self, dataset_id: str) -> None:
+        self.opaque_metadata = {"shard_id": dataset_id, "status": "sealed"}
+        super().__init__(
+            f"dataset {dataset_id!r} is sealed -- only opaque metadata is servable pre-exposure "
+            "(section 7.5); the underlying rows are refused"
+        )
+
+
+def _session_date_for_dataset(dataset_meta: dict) -> str:
+    """The dataset's own ET session date (spec section 0: "a session is an ET RTH trading date"),
+    from ``window_start_utc`` -- the identical small technique ``scout.py``'s own private
+    ``_session_date_for_dataset`` and ``micro_readiness.py``'s own ``_et_datetime`` already use
+    (mirrored, not imported -- the established "small technical helper, not a measurement rail"
+    class of interpretation call those modules' own docstrings already log)."""
+    parsed = datetime.fromisoformat(dataset_meta["window_start_utc"].replace("Z", "+00:00"))
+    if parsed.tzinfo is None:
+        parsed = parsed.replace(tzinfo=timezone.utc)
+    return parsed.astimezone(_ET_ZONE).date().isoformat()
+
+
+def resolve_micro_exposure_registry_dir(dataset_dir_resolved: str) -> str:
+    """``TAPEOLOGY_MICRO_EXPOSURE_REGISTRY_DIR`` if set, else a ``micro_exposure_registry``
+    SIBLING of the caller's already-resolved dataset directory -- the ``resolve_micro_snapshots_
+    dir``/``resolve_scout_ledger_dir`` pattern verbatim (the ``TAPEOLOGY_MICRO_*`` family, goal.md
+    Constraints; deliberately NOT a ``Config`` field)."""
+    override = os.environ.get(_EXPOSURE_REGISTRY_DIR_ENV)
+    if override:
+        return override
+    return str(Path(dataset_dir_resolved).parent / "micro_exposure_registry")
+
+
+class ExposureRegistry:
+    """A corpus-scoped, hash-chained ledger of exposure entries (spec section 6.7). One physical
+    ledger file serves every corpus this process ever touches -- ``corpus_id`` is a field on each
+    row, not a separate file per corpus (the ``scout_ledger.py`` "one global chain" precedent) --
+    so ``verify_chain()`` proves the WHOLE registry's tamper-evidence in one pass."""
+
+    def __init__(self, root_dir: str) -> None:
+        self._ledger = HashChainedLedger(root_dir, _EXPOSURE_LEDGER_FILENAME)
+
+    def verify_chain(self) -> dict:
+        return self._ledger.verify_chain()
+
+    def all_rows(self) -> list[dict]:
+        return self._ledger.all_rows()
+
+    def log_exposure(self, *, corpus_id: str, window: str, surface: str, logged_at: str) -> dict:
+        """Append ONE exposure entry: ``corpus_id`` scopes it, ``window`` is a session-date string
+        (spec section 6.2's own ``clustering_unit``), ``surface`` names what served it (a route, a
+        CLI, a fold evaluation), ``logged_at`` is the instant it was served -- passed explicitly
+        (never read from the wall clock inside this method) so a deterministic caller (a test, or
+        the r2 initializer below) reproduces byte-identical rows."""
+        return self._ledger.append_row(
+            {
+                "corpus_id": corpus_id,
+                "window": window,
+                "surface": surface,
+                "logged_at": logged_at,
+            }
+        )
+
+    def is_exposed_before(self, *, corpus_id: str, window: str, instant: str) -> bool:
+        """spec section 6.7's mechanical rule: ``True`` iff SOME exposure entry for
+        ``(corpus_id, window)`` carries a ``logged_at`` strictly before ``instant``. A spec's own
+        ``registered_at`` is exactly the ``instant`` a caller (``walkforward.py``) passes here to
+        decide ``historical_oos`` vs ``historical_exposed_diagnostic`` (TC-13)."""
+        for row in self._ledger.all_rows():
+            if row.get("corpus_id") == corpus_id and row.get("window") == window and row.get("logged_at") < instant:
+                return True
+        return False
+
+
+def initialize_r2_exposure_registry(
+    registry: ExposureRegistry,
+    *,
+    corpus_id: str,
+    windows: list[str],
+    surface: str = "r2_initialization",
+    logged_at: str = R2_REVISION_INSTANT,
+) -> int:
+    """Seeds ``registry`` with one exposure entry per (already-sorted-by-caller) window of
+    ``corpus_id``, stamped at ``logged_at`` (default: the r2 revision instant) -- spec section
+    6.7's own r2 initialization: "every window of the playbook bar corpus and of the 12 legacy
+    tick symbol-days is pre-marked exposed" (TC-14). Idempotent-in-spirit but NOT content-deduped
+    (the ``HashChainedLedger`` primitive's own "no dedup, ever" rule) -- a caller runs this exactly
+    ONCE per fresh registry (the compute-manager/CLI wiring's own job, not this function's).
+    Returns the count of rows appended."""
+    for window in windows:
+        registry.log_exposure(corpus_id=corpus_id, window=window, surface=surface, logged_at=logged_at)
+    return len(windows)
+
+
+def has_any_exposure_entries(registry: ExposureRegistry, corpus_id: str) -> bool:
+    """``True`` iff ``registry`` already carries at least one exposure entry for ``corpus_id`` --
+    the guard a production caller (``walkforward.run_diagnostic_walkforward``) uses to run
+    ``initialize_r2_exposure_registry`` exactly ONCE per corpus per registry: without it, every
+    repeated compute-manager trigger against the SAME durable registry would append the whole
+    playbook corpus's own window list again, growing the exposure ledger unboundedly on an
+    append-only store that (correctly) offers no dedup at the primitive level."""
+    return any(row.get("corpus_id") == corpus_id for row in registry.all_rows())
+
+
+class MicroAccessor:
+    """Constructed per-call (or per-run) with an explicit ``origin`` (a session date, or ``None``
+    for the disclosed unfenced mode -- module docstring) and an optional sealed-dataset view.
+    Owns ONE method this iteration: ``read_snapshot_rows`` -- the sole legal path onto
+    ``micro_snapshots.read_snapshot_rows`` (TR-3's import-ban; ``tests/test_micro_accessor.py``'s
+    AST source-scan proves no other module imports that name)."""
+
+    def __init__(
+        self,
+        dataset_store: DatasetStore,
+        snapshots_dir: str,
+        config: Config,
+        *,
+        origin: str | None = None,
+        sealed_dataset_ids: frozenset[str] = frozenset(),
+        exposure_registry: ExposureRegistry | None = None,
+        corpus_id: str | None = None,
+        surface: str = "micro_accessor",
+    ) -> None:
+        self._dataset_store = dataset_store
+        self._snapshots_dir = snapshots_dir
+        self._config = config
+        self._origin = origin
+        self._sealed_dataset_ids = sealed_dataset_ids
+        self._exposure_registry = exposure_registry
+        self._corpus_id = corpus_id
+        self._surface = surface
+
+    @property
+    def origin(self) -> str | None:
+        return self._origin
+
+    def read_snapshot_rows(self, dataset_id: str, *, logged_at: str | None = None) -> list[dict]:
+        """The origin-fenced, sealed-aware read: raises ``MicroAccessorSealedShardError`` for a
+        sealed id (never rows); raises ``MicroAccessorOriginFenceError`` when ``self.origin`` is
+        set AND the dataset's own session date falls strictly after it (TC-1); else returns the
+        SAME rows ``micro_snapshots.read_snapshot_rows`` always has, unmodified.
+
+        Exposure logging fires ONLY when this accessor was constructed with BOTH ``origin`` and
+        ``exposure_registry`` set (module docstring's "two callers, two disciplines") -- the
+        unfenced ``micro_join.py``/``scout.py`` re-point never logs, by construction, never by a
+        runtime branch a caller could get wrong."""
+        if dataset_id in self._sealed_dataset_ids:
+            raise MicroAccessorSealedShardError(dataset_id)
+
+        try:
+            dataset_meta = self._dataset_store.get(dataset_id)
+        except DatasetNotFound:
+            raise  # an honest absence -- never fabricated, never silently caught here
+
+        if self._origin is not None:
+            session_date = _session_date_for_dataset(dataset_meta)
+            if session_date > self._origin:
+                raise MicroAccessorOriginFenceError(
+                    f"dataset {dataset_id!r} has session_date {session_date!r}, strictly after "
+                    f"this accessor's origin {self._origin!r} -- refused (TR-3), never an empty "
+                    "or truncated result"
+                )
+            if self._exposure_registry is not None and self._corpus_id is not None:
+                self._exposure_registry.log_exposure(
+                    corpus_id=self._corpus_id,
+                    window=session_date,
+                    surface=self._surface,
+                    logged_at=logged_at if logged_at is not None else _iso_utc_now(),
+                )
+
+        return _raw_read_snapshot_rows(self._snapshots_dir, dataset_id)
+
+
+def _iso_utc_now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
diff --git a/apps/backend/app/research/micro_chain_ledger.py b/apps/backend/app/research/micro_chain_ledger.py
new file mode 100644
index 0000000..d214e31
--- /dev/null
+++ b/apps/backend/app/research/micro_chain_ledger.py
@@ -0,0 +1,161 @@
+"""``micro_chain_ledger.py`` -- Era "The Rapid Microscope" J-05: the ONE hash-chained,
+
+append-only, tail-anchored ledger primitive shared by this iteration's TWO new ledgers
+(``micro_accessor.ExposureRegistry`` and ``walkforward_ledger.WalkForwardLedger``).
+
+**Why a shared primitive now, when ``scout_ledger.py`` already has this exact pattern.**
+``scout_ledger.py``'s own hash-chain-plus-tail-anchor mechanics (iter-4 audit fix B2) are a
+Do-Not-Redo module this iteration must not touch. But THIS iteration needs the identical
+tamper-evident discipline TWICE more -- the §6.7 exposure registry and the fold/sequence/voiding
+ledger -- and duplicating the ~60-line mechanic a second AND third time inside two unrelated
+files would be the exact "second, independently-valued copy" anti-pattern this codebase's own
+conventions warn against elsewhere (e.g. ``micro_readiness.py``'s docstring on
+``WF_TRAIN_MIN_SESSIONS``). Factoring ONE shared primitive for these two NEW, same-iteration call
+sites is the "third occurrence" the simplicity bar allows -- ``scout_ledger.py`` stays byte-
+untouched and does not import this module; this module does not import ``scout_ledger.py`` either
+(no coupling introduced between them).
+
+**The mechanic, copied faithfully from ``scout_ledger.py``'s own iter-4-audited design (not
+imported, since that module is Do-Not-Redo and deliberately un-generic -- it stamps a
+Scout-specific ``variants_tried`` onto every row, which this shared primitive must NOT do):** each
+row's ``row_hash`` commits to its own content AND the previous row's own ``row_hash`` (a genuine
+link -- content-hash mismatch is caught directly at the tampered row; a prev_hash mismatch is
+caught at the first row whose predecessor no longer matches, also directly). A durable
+``chain_head.json`` tail anchor (``{"row_count", "head_hash"}``), written AFTER the row it commits
+to, closes the chain's own blind spot -- a hash chain by itself cannot see rows simply MISSING
+from its own end (iter-4 audit fix B2's own lesson, applied here from day one rather than
+retrofitted after an audit finds it a second time)."""
+
+from __future__ import annotations
+
+import hashlib
+import json
+from pathlib import Path
+
+__all__ = ["HashChainedLedgerIntegrityError", "HashChainedLedger"]
+
+_HEAD_ANCHOR_NAME = "chain_head.json"
+
+
+def _canonical(obj: object) -> bytes:
+    """The one canonical JSON encoding this module hashes -- the identical sorted-keys,
+    no-whitespace shape every sibling store/ledger in this codebase hashes (``scout_ledger.py``,
+    ``desk_playbook_log.py``, ``micro_features.py``, ...)."""
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+class HashChainedLedgerIntegrityError(Exception):
+    """A ledger line failed to parse as JSON -- corrupted or tampered at the file level (distinct
+    from a ``verify_chain()`` content/link mismatch, which is a well-formed-but-tampered row)."""
+
+
+class HashChainedLedger:
+    """File-based store rooted at ``root_dir / filename`` -- the ONE reader/writer of that one
+    JSONL file. Enforces no business rule of its own (the ``scout_ledger.ScoutLedger`` split):
+    ``append_row`` hash-chains and persists whatever content dict it is given; a caller wanting a
+    domain-specific derived field (e.g. a running denominator) stamps it onto ``fields`` itself,
+    BEFORE calling ``append_row`` -- this primitive never inspects field content beyond the
+    ``row_hash``/``prev_hash``/``row_index`` it manages."""
+
+    def __init__(self, root_dir: str | Path, filename: str) -> None:
+        self._root = Path(root_dir)
+        self._path = self._root / filename
+        self._head_path = self._root / f"{filename}.{_HEAD_ANCHOR_NAME}"
+
+    @property
+    def path(self) -> Path:
+        return self._path
+
+    def _read_raw(self) -> list[dict]:
+        """Every row, append order, parsed but NOT chain-verified -- ``verify_chain()`` is the
+        explicit tamper check; a caller just wanting the data reads this (or ``all_rows``)
+        directly, exactly like ``micro_snapshots.read_snapshot_rows``'s "plain reader" precedent."""
+        if not self._path.exists():
+            return []
+        rows: list[dict] = []
+        text = self._path.read_text(encoding="utf-8")
+        for line_no, line in enumerate(text.splitlines()):
+            line = line.strip()
+            if not line:
+                continue
+            try:
+                rows.append(json.loads(line))
+            except ValueError as exc:
+                raise HashChainedLedgerIntegrityError(
+                    f"ledger line {line_no} of '{self._path}' is not parseable JSON ({exc}) -- "
+                    "corrupted or tampered"
+                ) from exc
+        return rows
+
+    def all_rows(self) -> list[dict]:
+        """Every permanent row ever appended, in append order -- never filtered, never deleted."""
+        return self._read_raw()
+
+    def append_row(self, fields: dict) -> dict:
+        """Persist ONE new permanent row: hash-chains ``fields`` onto whatever is currently on
+        disk (``prev_hash`` = the CURRENT last row's own ``row_hash``, or ``None`` for the very
+        first row) and stamps ``row_index``. ALWAYS a genuinely new row -- no content-keyed dedup
+        exists in this store, so identical ``fields`` appended twice yields two permanent rows with
+        two distinct ``row_hash``es (their ``row_index``/``prev_hash`` differ)."""
+        existing = self._read_raw()
+        prev_hash = existing[-1]["row_hash"] if existing else None
+        content = {**fields, "row_index": len(existing), "prev_hash": prev_hash}
+        row_hash = _sha256(_canonical(content))
+        row = {**content, "row_hash": row_hash}
+        self._root.mkdir(parents=True, exist_ok=True)
+        with self._path.open("a", encoding="utf-8") as fh:
+            fh.write(json.dumps(row, sort_keys=True))
+            fh.write("\n")
+        # The tail anchor, written AFTER the row it commits to (module docstring): a crash between
+        # the two leaves the ledger LONGER than the anchor -- benign -- never falsely short.
+        self._head_path.write_text(
+            json.dumps({"row_count": len(existing) + 1, "head_hash": row_hash}, sort_keys=True),
+            encoding="utf-8",
+        )
+        return dict(row)
+
+    def verify_chain(self) -> dict:
+        """Walks every row in append order, recomputing each row's own content hash (catches an
+        in-place edit AT that row) and re-checking its ``prev_hash`` against the PRECEDING row's
+        actually-stored ``row_hash`` (catches a deletion/reordering at the first row whose link no
+        longer resolves), THEN checks the durable tail anchor (catches a tail truncation the chain
+        walk alone cannot see). Returns ``{"ok": True, "failed_at_row": None, "reason": None}`` on
+        a clean, complete chain, else ``{"ok": False, "failed_at_row": <int|None>, "reason": <str>}``
+        -- never raises, so a caller can report the failure rather than crash on it."""
+        rows = self._read_raw()
+        prev_stored: str | None = None
+        for i, row in enumerate(rows):
+            content = {k: v for k, v in row.items() if k != "row_hash"}
+            recomputed = _sha256(_canonical(content))
+            if recomputed != row.get("row_hash"):
+                return {"ok": False, "failed_at_row": i, "reason": "content_hash_mismatch"}
+            if row.get("prev_hash") != prev_stored:
+                return {"ok": False, "failed_at_row": i, "reason": "prev_hash_mismatch"}
+            prev_stored = row["row_hash"]
+        return self._verify_tail(rows)
+
+    def _verify_tail(self, rows: list[dict]) -> dict:
+        anchor = self._read_head_anchor()
+        if anchor is None:
+            if not rows:
+                return {"ok": True, "failed_at_row": None, "reason": None}
+            return {"ok": False, "failed_at_row": None, "reason": "head_anchor_missing"}
+        anchored_count = anchor.get("row_count", 0)
+        if len(rows) < anchored_count:
+            return {"ok": False, "failed_at_row": len(rows), "reason": "tail_truncated"}
+        if anchored_count > 0 and rows[anchored_count - 1].get("row_hash") != anchor.get("head_hash"):
+            return {"ok": False, "failed_at_row": anchored_count - 1, "reason": "head_hash_mismatch"}
+        return {"ok": True, "failed_at_row": None, "reason": None}
+
+    def _read_head_anchor(self) -> dict | None:
+        if not self._head_path.exists():
+            return None
+        try:
+            parsed = json.loads(self._head_path.read_text(encoding="utf-8"))
+        except (OSError, ValueError):
+            return None
+        return parsed if isinstance(parsed, dict) else None
diff --git a/apps/backend/app/research/walkforward.py b/apps/backend/app/research/walkforward.py
new file mode 100644
index 0000000..0415e06
--- /dev/null
+++ b/apps/backend/app/research/walkforward.py
@@ -0,0 +1,1170 @@
+"""``walkforward.py`` -- Era "The Rapid Microscope" J-05: the chronological walk-forward engine
+
+(``docs/rapid-validation-spec.md`` section 6). Fold-spec geometry (frozen, corpus-scoped, voidable
+only by a recorded event -- ``walkforward_ledger.py``), purge-by-construction (session-truncated
+observations, asserted every fold), Mode A rolling-origin discovery (the frozen fitting RULE is
+the sequence identity, never a realized value), Mode B fixed-hypothesis evaluation (registered
+first, evaluated after -- the exposure registry mechanically decides ``historical_oos`` vs
+``historical_exposed_diagnostic``), the discretion-free ``WF_SURVIVOR_RULE_V1`` predicate, the
+per-sequence temporal-stability (decay) view, the single-flight compute manager + CLI, and the
+diagnostic acceptance run over the real 155-session playbook corpus.
+
+**Observations are the engine's one abstract input.** Every caller -- the TR-16 synthetic
+oracles, the diagnostic run's playbook-setup reader, a future J-09 pilot study -- reduces its own
+corpus to a flat list of ``{session_date, symbol, value}`` dicts (``value`` already signed for the
+candidate's registered direction, exactly the playbook rail's own ``side_relative`` convention)
+BEFORE calling into this module's fold machinery. This mirrors ``scout.py``'s own
+``extract_anchors`` -> ``compute_p_screen`` split (a corpus-specific reader feeds a corpus-
+agnostic statistical core) and is what lets the TR-16 oracle proofs run entirely on hand-built
+fixtures, with no real tick dataset or engine replay required (TR-16 exercises the SAME production
+``screen_candidate``/fold functions Scout and this module already ship, over synthetic input --
+the identical style ``test_scout.py``'s own TR-8 calibration fixture already established).
+
+**Econ floor for a non-tick corpus (a disclosed interpretation call, T-1).** WF_SURVIVOR_RULE_V1's
+condition 3 needs an economic-relevance floor (spec section 5.5), which Scout derives from quoted
+SPREAD -- a quantity the PLAYBOOK BAR corpus (the diagnostic run's own source) does not carry at
+all. Rather than inventing a spread proxy the spec never authorizes for bar data, a sequence's
+``econ_floor`` is EXPLICITLY ``None`` when no spread-based floor applies (the diagnostic run's own
+case) and condition 3 evaluates FALSE whenever ``econ_floor`` is ``None`` -- fail-closed, never a
+silently-satisfied gate. A caller that DOES have a tick-corpus econ floor (a TR-16 oracle fixture,
+a future J-09 study reusing Scout's own registered floor) supplies a concrete ``{floor_bps: ...}``
+dict instead.
+
+**Condition 4's own fold-level "opposite-direction screen" (a second disclosed interpretation
+call).** Spec section 6.6 condition 4 says "no sufficient fold passes the section 5.3 screen in
+the OPPOSITE direction" -- section 5.3 is Scout's own CANDIDATE-level, many-session block-
+permutation screen; running a second full copy of that machinery per FOLD, for a rule that (unlike
+a Scout candidate) may not even be tick-anchored, is out of this iteration's scope and unspecified
+by name. This module reads "passes the screen in the opposite direction" as "a sufficient fold's
+own effect is opposite in sign to the registered direction AND clears the SAME economic-relevance
+magnitude condition 3 already uses" -- a defensible, internally-consistent reading (a large,
+countervailing fold is exactly what this condition exists to catch) that invents no new
+statistical apparatus and no new threshold family."""
+
+from __future__ import annotations
+
+import argparse
+import hashlib
+import json
+import os
+import random
+import re
+import statistics
+import threading
+import uuid
+from datetime import datetime, timezone
+from pathlib import Path
+from typing import Callable
+
+from ..config import CONFIG, Config
+from .bars import BarStore
+from .desk_playbook import PlaybookStore, compute_playbook_input_signature, resolve_desk_playbook_dir
+from .desk_universe import UniverseStore
+from .micro_accessor import (
+    ExposureRegistry,
+    has_any_exposure_entries,
+    initialize_r2_exposure_registry,
+    resolve_micro_exposure_registry_dir,
+)
+from .micro_readiness import WF_TEST_MIN_SESSIONS, WF_TRAIN_MIN_SESSIONS
+from .micro_snapshots import append_run_log
+from .walkforward_ledger import (
+    ROW_KIND_FOLD_RESULT,
+    ROW_KIND_FOLD_SPEC,
+    FoldGeometryFrozenError,
+    FoldStepTooSmallError,
+    WalkForwardLedger,
+    append_fold_result,
+    compute_geometry_hash,
+    fold_results_for_sequence,
+    is_corpus_era_voided,
+    latest_fold_spec,
+    record_mode_b_predeclaration,
+    record_voiding_event,
+    register_fold_spec,
+    sequence_ids_for_corpus,
+)
+
+__all__ = [
+    "WF_TRAIN_MIN_SESSIONS",
+    "WF_TEST_MIN_SESSIONS",
+    "WF_MIN_SUFFICIENT_FOLDS",
+    "WF_FOLD_MIN_SIGNAL_SESSIONS",
+    "WF_FOLD_MIN_OBSERVATIONS",
+    "WF_FOLD_MIN_SYMBOLS",
+    "WF_SURVIVOR_SIGN_CONSISTENCY",
+    "DIAGNOSTIC_GEOMETRY",
+    "WF_SURVIVOR_RULE_V1",
+    "WF_VERDICT_SURVIVOR",
+    "WF_VERDICT_NOT_SURVIVOR",
+    "EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC",
+    "EVIDENCE_CLASS_HISTORICAL_OOS",
+    "EVIDENCE_CLASS_LIVE_CONFIRMATORY",
+    "PROCESS_LABEL_RULE",
+    "PROCESS_LABEL_OPERATOR",
+    "FOLD_STATUS_SUFFICIENT",
+    "FOLD_STATUS_INSUFFICIENT",
+    "PurgeExactnessError",
+    "UnknownFittingRuleError",
+    "FoldGeometryFrozenError",
+    "FoldStepTooSmallError",
+    "WalkForwardLedger",
+    "register_fold_spec",
+    "record_voiding_event",
+    "record_mode_b_predeclaration",
+    "latest_fold_spec",
+    "is_corpus_era_voided",
+    "sequence_ids_for_corpus",
+    "fold_results_for_sequence",
+    "resolve_walkforward_ledger_dir",
+    "wf_stream",
+    "walkforward_parameters",
+    "walkforward_parameters_hash",
+    "build_folds",
+    "minimum_sessions_for_sufficient_folds",
+    "InsufficientSessionsForFoldsError",
+    "require_sufficient_sessions_for_folds",
+    "assert_purge_exact",
+    "observations_in_sessions",
+    "summarize_fold_observations",
+    "classify_evidence_class",
+    "sequence_id_for",
+    "compute_spec_hash",
+    "parse_fitting_rule",
+    "fit_training_quantile",
+    "register_mode_a_origin",
+    "register_mode_b_spec",
+    "evaluate_mode_b_fold",
+    "evaluate_survivor_rule",
+    "sequence_verdict",
+    "decay_view",
+    "list_fold_specs",
+    "list_walkforward_sequences",
+    "WalkForwardComputeManager",
+    "TR16_KNOWN_NULL_CORPUS_ID",
+    "TR16_PLANTED_EFFECT_CORPUS_ID",
+    "PLAYBOOK_DIAGNOSTIC_CORPUS_ID",
+    "PLAYBOOK_DIAGNOSTIC_SETUP_IDS",
+    "PLAYBOOK_DIAGNOSTIC_HORIZON_LABEL",
+    "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE",
+    "playbook_observations",
+    "run_diagnostic_walkforward",
+    "main",
+]
+
+# === docs/rapid-validation-spec.md section 1 -- transcribed verbatim, narrowed to this module's =====
+# === own consumption (the micro_features.py/scout.py precedent for narrowing the shared table). =====
+
+# WF_TRAIN_MIN_SESSIONS/WF_TEST_MIN_SESSIONS are imported verbatim from micro_readiness.py, which
+# transcribed them FIRST (that module's own docstring: "a future J-05 dev should import these two
+# names from here ... never mint a second, independently-valued copy").
+WF_MIN_SUFFICIENT_FOLDS = 3
+WF_FOLD_MIN_SIGNAL_SESSIONS = 8
+WF_FOLD_MIN_OBSERVATIONS = 30
+WF_FOLD_MIN_SYMBOLS = 2
+WF_SURVIVOR_SIGN_CONSISTENCY = 0.7
+
+# The diagnostic acceptance run's OWN predeclared geometry (spec section 6.6) -- pinned exactly at
+# the WF_TRAIN_MIN_SESSIONS/WF_TEST_MIN_SESSIONS floors; embargo_sessions=5 is THIS run's own
+# predeclared choice, never a universal default (spec section 6.3).
+DIAGNOSTIC_GEOMETRY: dict = {
+    "train_sessions": 40,
+    "embargo_sessions": 5,
+    "test_sessions": 20,
+    "step_sessions": 20,
+    "embargo_derivation": (
+        "this run's own predeclared choice (spec section 6.6), not derived from an identified "
+        "cross-boundary dependency -- never treated as a universal rule for any other corpus"
+    ),
+}
+
+# T-2's vocabulary minefield, precisely: `WF_SURVIVOR_RULE_V1` NAMES the frozen predicate itself
+# (served as `rule_name`, so a reader can tell which frozen rule version produced a verdict -- a
+# future WF_SURVIVOR_RULE_V2 would be a named revision, never a silent redefinition); the sequence
+# STATE the predicate produces is the SEPARATE, spec-literal token `walkforward_survivor` -- this
+# era's full-token vocabulary rule ("'survivor' alone belongs to pnl_scan"), never the rule's own
+# name serving double duty as the verdict value.
+WF_SURVIVOR_RULE_V1 = "WF_SURVIVOR_RULE_V1"
+WF_VERDICT_SURVIVOR = "walkforward_survivor"
+WF_VERDICT_NOT_SURVIVOR = "not_survivor"
+
+EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC = "historical_exposed_diagnostic"
+EVIDENCE_CLASS_HISTORICAL_OOS = "historical_oos"
+EVIDENCE_CLASS_LIVE_CONFIRMATORY = "live_confirmatory"
+
+PROCESS_LABEL_RULE = "rule_process"
+PROCESS_LABEL_OPERATOR = "operator_process"
+
+FOLD_STATUS_SUFFICIENT = "sufficient"
+FOLD_STATUS_INSUFFICIENT = "insufficient"
+
+# spec section 0's ONE stream-constructor recipe, verbatim -- the scout.py `scout_stream`/
+# referee_stats.py `referee_stream` precedent, mirrored (this module imports neither).
+WF_STREAM_RECIPE = "{MICRO_SEED}:{scope_id}:{purpose}[:{fold_or_origin}[:{i}]]"
+_MICRO_SEED = 314159
+_WF_STREAM_PURPOSES = frozenset({"mode-a-fit"})
+
+
+class PurgeExactnessError(Exception):
+    """TR-6: an observation's own ``session_date`` is not a member of the fold-window session set
+    it was handed under -- refused, so purge is ASSERTED, not merely assumed from a filter step
+    that could silently drift."""
+
+
+class UnknownFittingRuleError(Exception):
+    """A Mode A fitting-rule string does not match any rule family this module knows how to fit
+    (the closed vocabulary of ``_FITTING_RULE_PATTERN``) -- refused rather than guessed."""
+
+
+def _iso_utc_now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
+
+
+def _canonical(obj: object) -> bytes:
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def wf_stream(scope_id: str, purpose: str, fold_or_origin: str | None = None, i: int | str | None = None) -> random.Random:
+    """The ONE stream constructor (``WF_STREAM_RECIPE``, implemented verbatim -- the
+    ``scout.scout_stream`` precedent)."""
+    if purpose not in _WF_STREAM_PURPOSES:
+        raise ValueError(f"wf_stream: unknown purpose {purpose!r}, expected one of {sorted(_WF_STREAM_PURPOSES)}")
+    if i is not None and fold_or_origin is None:
+        raise ValueError("wf_stream: `i` requires `fold_or_origin` (the recipe's own nesting)")
+    key = f"{_MICRO_SEED}:{scope_id}:{purpose}"
+    if fold_or_origin is not None:
+        key += f":{fold_or_origin}"
+        if i is not None:
+            key += f":{i}"
+    return random.Random(key)
+
+
+def walkforward_parameters() -> dict:
+    """Every module constant a served walk-forward result depends on, embedded verbatim (the
+    ``scout.scout_parameters`` pattern) -- keyed on its hash by every persisted ledger row's
+    ``params_hash``."""
+    return {
+        "micro_seed": _MICRO_SEED,
+        "wf_train_min_sessions": WF_TRAIN_MIN_SESSIONS,
+        "wf_test_min_sessions": WF_TEST_MIN_SESSIONS,
+        "wf_min_sufficient_folds": WF_MIN_SUFFICIENT_FOLDS,
+        "wf_fold_min_signal_sessions": WF_FOLD_MIN_SIGNAL_SESSIONS,
+        "wf_fold_min_observations": WF_FOLD_MIN_OBSERVATIONS,
+        "wf_fold_min_symbols": WF_FOLD_MIN_SYMBOLS,
+        "wf_survivor_sign_consistency": WF_SURVIVOR_SIGN_CONSISTENCY,
+    }
+
+
+def walkforward_parameters_hash() -> str:
+    return _sha256(_canonical(walkforward_parameters()))
+
+
+def compute_spec_hash(spec_fields: dict) -> str:
+    """A pure content hash over a Mode A/B spec's own frozen fields -- excludes any wall-clock-
+    derived value (the ``scout_ledger.compute_spec_hash`` precedent)."""
+    return _sha256(_canonical(spec_fields))
+
+
+def sequence_id_for(corpus_id: str, rule_identity: str) -> str:
+    """A constant-rule SEQUENCE's own identity key (TR-14): a pure function of ``(corpus_id,
+    rule_identity)`` -- ``rule_identity`` is a Mode A fitting-rule STRING (never a realized value)
+    or a Mode B ``rule_id`` string. Calling this twice with the SAME two inputs always returns the
+    SAME sequence id, so re-running an origin under an unchanged rule stays in one sequence
+    (TC-11)."""
+    return f"seq-{_sha256(_canonical([corpus_id, rule_identity]))[:16]}"
+
+
+# === fold geometry + purge (spec section 6.2/6.3) ====================================================
+
+
+def build_folds(session_dates: list[str], geometry: dict) -> list[dict]:
+    """Pure, deterministic rolling-window fold construction over an ALREADY-SORTED-ASCENDING
+    ``session_dates`` list -- fold boundaries fall ONLY on session-date boundaries (spec section
+    6.2), so purge is exact BY CONSTRUCTION: train/embargo/test never overlap (``step_sessions >=
+    test_sessions`` is enforced at REGISTRATION time, ``register_fold_spec``'s own TC-7 refusal,
+    never re-checked here). Returns one dict per fold: ``{fold_index, origin_index, train_sessions,
+    embargo_sessions, test_sessions}``; stops the instant a fold's own ``test_sessions`` window
+    would run past the end of ``session_dates`` -- a below-floor remainder is simply not a fold,
+    never a fabricated short one."""
+    train_n = geometry["train_sessions"]
+    embargo_n = geometry["embargo_sessions"]
+    test_n = geometry["test_sessions"]
+    step_n = geometry["step_sessions"]
+    folds: list[dict] = []
+    start = 0
+    fold_index = 0
+    while True:
+        train_end = start + train_n
+        embargo_end = train_end + embargo_n
+        test_end = embargo_end + test_n
+        if test_end > len(session_dates):
+            break
+        folds.append(
+            {
+                "fold_index": fold_index,
+                "origin_index": start,
+                "train_sessions": list(session_dates[start:train_end]),
+                "embargo_sessions": list(session_dates[train_end:embargo_end]),
+                "test_sessions": list(session_dates[embargo_end:test_end]),
+            }
+        )
+        start += step_n
+        fold_index += 1
+    return folds
+
+
+def minimum_sessions_for_sufficient_folds(geometry: dict) -> int:
+    """The fewest total sessions a corpus must carry for ``build_folds`` to ever produce
+    ``WF_MIN_SUFFICIENT_FOLDS`` folds under ``geometry`` -- fold 1's own span
+    (``train+embargo+test``) plus ``WF_MIN_SUFFICIENT_FOLDS - 1`` further steps (TC-20's own "11 <
+    105" arithmetic: ``DIAGNOSTIC_GEOMETRY``'s 40+5+20 + 2*20 = 105)."""
+    fold_one_span = geometry["train_sessions"] + geometry["embargo_sessions"] + geometry["test_sessions"]
+    return fold_one_span + (WF_MIN_SUFFICIENT_FOLDS - 1) * geometry["step_sessions"]
+
+
+class InsufficientSessionsForFoldsError(Exception):
+    """TR-15: a corpus does not carry enough sessions to ever produce ``WF_MIN_SUFFICIENT_FOLDS``
+    folds under a given geometry -- a typed refusal (TC-20: "the 18-dataset/11-session tick corpus
+    ... a typed floor-refusal naming 11 < 105"), never an empty fold report standing in for one."""
+
+
+def require_sufficient_sessions_for_folds(session_dates: list[str], geometry: dict) -> None:
+    """Raises ``InsufficientSessionsForFoldsError`` (naming the exact shortfall) when
+    ``session_dates`` cannot possibly support ``WF_MIN_SUFFICIENT_FOLDS`` folds under ``geometry``
+    -- the check a caller makes BEFORE ``build_folds`` when it wants a typed refusal rather than a
+    merely-empty fold list (TC-20)."""
+    minimum = minimum_sessions_for_sufficient_folds(geometry)
+    if len(session_dates) < minimum:
+        raise InsufficientSessionsForFoldsError(
+            f"{len(session_dates)} < {minimum} -- refused (TR-15): this corpus cannot produce "
+            f"WF_MIN_SUFFICIENT_FOLDS({WF_MIN_SUFFICIENT_FOLDS}) folds under this geometry"
+        )
+
+
+def assert_purge_exact(observations: list[dict], allowed_sessions: set[str] | list[str], *, boundary_name: str) -> None:
+    """TR-6: every observation's own ``session_date`` must be a member of ``allowed_sessions`` --
+    an ACTIVE assertion (not merely an assumed consequence of whatever filter produced the list),
+    so a planted observation whose session crosses a fold boundary is caught, never silently
+    pooled (TC-8)."""
+    allowed = set(allowed_sessions)
+    for observation in observations:
+        session_date = observation.get("session_date")
+        if session_date not in allowed:
+            raise PurgeExactnessError(
+                f"observation with session_date={session_date!r} is not a member of the "
+                f"{boundary_name!r} session set -- refused (TR-6): a label crossing a fold "
+                "boundary is never silently included"
+            )
+
+
+def observations_in_sessions(observations: list[dict], sessions: list[str], *, boundary_name: str) -> list[dict]:
+    """Filters ``observations`` to those whose ``session_date`` is a member of ``sessions``, THEN
+    asserts the result (TR-6, called for EVERY fold this module ever evaluates -- module docstring,
+    "session-truncation is asserted... for every fold in the run")."""
+    allowed = set(sessions)
+    selected = [o for o in observations if o.get("session_date") in allowed]
+    assert_purge_exact(selected, allowed, boundary_name=boundary_name)
+    return selected
+
+
+# === per-fold summary statistics (session-cluster mean, spec section 5.3's aggregation mirrored) ===
+
+
+def summarize_fold_observations(observations: list[dict], floors: dict) -> dict:
+    """One fold's own effect/n/sessions/symbols/sign -- spec section 6.6's own per-fold reporting
+    fields. Effect = mean of session-cluster means (the SAME "mean of session-cluster mean deltas"
+    aggregation spec section 5.3 and ``scout._observed_effect`` already use, adapted to a
+    ONE-SAMPLE pool since a walk-forward fold evaluates a single already-hypothesized rule, not a
+    two-cell candidate-vs-comparator screen). Below ANY of the three per-fold floors
+    (``WF_FOLD_MIN_OBSERVATIONS``/``WF_FOLD_MIN_SIGNAL_SESSIONS``/``WF_FOLD_MIN_SYMBOLS``) reads
+    ``insufficient`` with the failed arithmetic attached (TC-16), never a fabricated verdict."""
+    n = len(observations)
+    sessions: dict[str, list[float]] = {}
+    symbols: set[str] = set()
+    for o in observations:
+        sessions.setdefault(o["session_date"], []).append(o["value"])
+        symbols.add(o["symbol"])
+    n_sessions = len(sessions)
+    n_symbols = len(symbols)
+
+    min_observations = floors.get("wf_fold_min_observations", WF_FOLD_MIN_OBSERVATIONS)
... [diff_bound] apps/backend/app/research/walkforward.py: 776 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/research/walkforward_ledger.py b/apps/backend/app/research/walkforward_ledger.py
new file mode 100644
index 0000000..cb2491e
--- /dev/null
+++ b/apps/backend/app/research/walkforward_ledger.py
@@ -0,0 +1,296 @@
+"""``walkforward_ledger.py`` -- Era "The Rapid Microscope" J-05: the fold-spec registry plus the
+
+hash-chained, append-only fold-result/sequence/voiding-event ledger (``docs/rapid-validation-
+spec.md`` section 6.2-6.8). Built on ``micro_chain_ledger.HashChainedLedger`` (the SAME shared
+primitive ``micro_accessor.ExposureRegistry`` uses -- see that module's own docstring for why a
+shared primitive is the right call this iteration, not a duplication of
+``scout_ledger.py``'s own, untouched, Scout-specific mechanic).
+
+**One global chain, three row kinds (the ``scout_ledger.py`` "one global chain, not one per
+family" precedent, mirrored).** ``fold_spec`` rows (frozen geometry registrations), ``fold_result``
+rows (one per constant-rule sequence's per-fold evaluation -- Mode A per-origin refits and Mode B
+per-window evaluations alike), and ``voiding_event`` rows (TR-13) all land in ONE physical ledger
+file, discriminated by their own ``row_kind`` field -- so ``verify_chain()`` proves the WHOLE
+ledger's tamper-evidence (every fold, every kill, every voiding) in a single pass, exactly the
+"the denominator never shrinks" guarantee spec section 6 exists to make mechanical.
+
+**Fold-spec freeze (TR-13, TC-6, TC-7, TC-10).** ``register_fold_spec`` computes ``geometry_hash``
+(a pure content hash, wall-clock-excluded -- the ``scout_ledger.compute_spec_hash`` precedent) and
+refuses ``step_sessions < test_sessions`` (TC-7: pooled statistics over overlapping validation
+windows are never constructed) BEFORE writing anything. A corpus_id's fold spec is FROZEN at its
+first registration: a second registration with a DIFFERENT geometry is refused
+(``FoldGeometryFrozenError``) unless a voiding event for that ``corpus_id`` was recorded first
+(TC-10) -- checked by walking the ledger's own append order, never a second, independently-kept
+"current geometry" cache."""
+
+from __future__ import annotations
+
+import hashlib
+import json
+from datetime import datetime, timezone
+
+from .micro_chain_ledger import HashChainedLedger
+
+__all__ = [
+    "ROW_KIND_FOLD_SPEC",
+    "ROW_KIND_FOLD_RESULT",
+    "ROW_KIND_VOIDING_EVENT",
+    "ROW_KIND_MODE_B_SPEC",
+    "FoldStepTooSmallError",
+    "FoldGeometryFrozenError",
+    "WalkForwardLedger",
+    "compute_geometry_hash",
+    "register_fold_spec",
+    "record_voiding_event",
+    "record_mode_b_predeclaration",
+    "mode_b_predeclarations_for_sequence",
+    "latest_fold_spec",
+    "voiding_events_for_corpus",
+    "is_corpus_era_voided",
+    "existing_fold_result",
+    "append_fold_result",
+    "fold_results_for_sequence",
+    "sequence_ids_for_corpus",
+]
+
+_LEDGER_FILENAME = "walkforward_ledger.jsonl"
+
+ROW_KIND_FOLD_SPEC = "fold_spec"
+ROW_KIND_FOLD_RESULT = "fold_result"
+ROW_KIND_VOIDING_EVENT = "voiding_event"
+ROW_KIND_MODE_B_SPEC = "mode_b_spec"
+
+_GEOMETRY_KEYS = ("train_sessions", "test_sessions", "step_sessions", "embargo_sessions")
+
+
+def _canonical(obj: object) -> bytes:
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def _iso_utc_now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
+
+
+class FoldStepTooSmallError(Exception):
+    """TC-7: ``step_sessions < test_sessions`` -- refused before any ledger row is written, so
+    pooled statistics over overlapping validation windows are never constructed (spec section
+    6.2)."""
+
+
+class FoldGeometryFrozenError(Exception):
+    """TC-10 (first half): a corpus_id already carries a registered fold spec with a DIFFERENT
+    geometry, and no voiding event has been recorded for it since -- refused (TR-13)."""
+
+
+class WalkForwardLedger:
+    """A thin domain wrapper over ONE ``HashChainedLedger`` -- the module docstring's "one global
+    chain, three row kinds" ledger."""
+
+    def __init__(self, root_dir: str) -> None:
+        self._chain = HashChainedLedger(root_dir, _LEDGER_FILENAME)
+
+    def verify_chain(self) -> dict:
+        return self._chain.verify_chain()
+
+    def all_rows(self) -> list[dict]:
+        return self._chain.all_rows()
+
+    def rows_of_kind(self, row_kind: str) -> list[dict]:
+        return [row for row in self._chain.all_rows() if row.get("row_kind") == row_kind]
+
+    def append_row(self, fields: dict) -> dict:
+        """The pure storage primitive (the ``scout_ledger.ScoutLedger.append_row`` precedent --
+        enforces no business rule of its own; ``register_fold_spec``/``record_voiding_event``/
+        ``append_fold_result`` below are the validated entry points every production caller uses)."""
+        return self._chain.append_row(fields)
+
+
+def compute_geometry_hash(geometry: dict) -> str:
+    """A pure content hash over the geometry's own frozen fields (``_GEOMETRY_KEYS`` -- NOT
+    ``embargo_derivation``, a free-text disclosure rather than a numeric geometry component) --
+    excludes any wall-clock-derived value, so two genuinely separate registration acts of the
+    IDENTICAL geometry (a re-run of the same CLI invocation, TC-6-style) compute the identical
+    hash (the ``scout_ledger.compute_spec_hash`` precedent)."""
+    return _sha256(_canonical({key: geometry[key] for key in _GEOMETRY_KEYS}))
+
+
+def latest_fold_spec(ledger: WalkForwardLedger, corpus_id: str) -> dict | None:
+    """The most recently registered ``fold_spec`` row for ``corpus_id``, or ``None`` -- append
+    order IS registration order (the ledger's own invariant), so the last matching row is the
+    latest."""
+    matches = [row for row in ledger.rows_of_kind(ROW_KIND_FOLD_SPEC) if row.get("corpus_id") == corpus_id]
+    return matches[-1] if matches else None
+
+
+def voiding_events_for_corpus(ledger: WalkForwardLedger, corpus_id: str) -> list[dict]:
+    return [row for row in ledger.rows_of_kind(ROW_KIND_VOIDING_EVENT) if row.get("corpus_id") == corpus_id]
+
+
+def is_corpus_era_voided(ledger: WalkForwardLedger, corpus_id: str, *, since_registered_at: str | None = None) -> bool:
+    """``True`` iff ANY voiding event exists for ``corpus_id`` -- optionally restricted to those
+    recorded AT OR AFTER ``since_registered_at`` (a sequence's own ``registered_at``, so a sequence
+    frozen and evaluated entirely BEFORE a later voiding event can still be judged on its own
+    un-voided history if a caller ever needs that finer question; the coarse "any voiding event on
+    this corpus-era at all" -- WF_SURVIVOR_RULE_V1's own condition 5 -- is the ``since_registered_
+    at=None`` default)."""
+    events = voiding_events_for_corpus(ledger, corpus_id)
+    if since_registered_at is None:
+        return bool(events)
+    return any(event["voided_at"] >= since_registered_at for event in events)
+
+
+def register_fold_spec(
+    ledger: WalkForwardLedger,
+    *,
+    corpus_id: str,
+    corpus_manifest_hash: str,
+    geometry: dict,
+    clustering_unit: str = "session_date",
+    floors: dict,
+    registered_at: str | None = None,
+) -> dict:
+    """Freezes a fold spec for ``corpus_id`` (spec section 6.2): ``{corpus_id,
+    corpus_manifest_hash, geometry, clustering_unit, floors, registered_at, geometry_hash}``.
+    Refuses ``step_sessions < test_sessions`` (TC-7) and a SECOND, DIFFERENT geometry registered
+    for a corpus_id that already carries one without an intervening voiding event (TC-10) --
+    BEFORE writing anything either way. Re-registering the IDENTICAL geometry (byte-equal
+    ``geometry_hash``) is treated as an idempotent replay: the EXISTING fold spec is returned
+    unchanged rather than appending a redundant row (the ``PlaybookStore``/``ForwardStore``
+    "an identical key is refused as a NEW registration, but reading back what already exists is
+    always fine" spirit, adapted here since a fold spec has no separate `.get()` accessor of its
+    own)."""
+    if geometry["step_sessions"] < geometry["test_sessions"]:
+        raise FoldStepTooSmallError(
+            f"step_sessions={geometry['step_sessions']!r} < test_sessions="
+            f"{geometry['test_sessions']!r} -- refused (spec section 6.2): pooled statistics over "
+            "overlapping validation windows are never constructed"
+        )
+    geometry_hash = compute_geometry_hash(geometry)
+
+    existing = latest_fold_spec(ledger, corpus_id)
+    if existing is not None:
+        if existing["geometry_hash"] == geometry_hash:
+            return dict(existing)
+        if not is_corpus_era_voided(ledger, corpus_id, since_registered_at=existing["registered_at"]):
+            raise FoldGeometryFrozenError(
+                f"corpus_id {corpus_id!r} already carries a registered fold spec with geometry_hash "
+                f"{existing['geometry_hash']!r} (registered {existing['registered_at']!r}); a "
+                f"DIFFERENT geometry (hash {geometry_hash!r}) is refused without a recorded voiding "
+                "event for this corpus-era (TR-13)"
+            )
+
+    fields = {
+        "row_kind": ROW_KIND_FOLD_SPEC,
+        "corpus_id": corpus_id,
+        "corpus_manifest_hash": corpus_manifest_hash,
+        "geometry": dict(geometry),
+        "clustering_unit": clustering_unit,
+        "floors": dict(floors),
+        "registered_at": registered_at if registered_at is not None else _iso_utc_now(),
+        "geometry_hash": geometry_hash,
+    }
+    return ledger.append_row(fields)
+
+
+def record_voiding_event(
+    ledger: WalkForwardLedger, *, corpus_id: str, reason: str, voided_at: str | None = None
+) -> dict:
+    """TC-10 (second half): a permanent, append-only voiding event for ``corpus_id`` -- after this,
+    ``is_corpus_era_voided`` reads ``True`` for the corpus-era, which
+    WF_SURVIVOR_RULE_V1's own condition 5 makes fatal to EVERY existing survivor state of that
+    corpus-era (never a deletion or edit of any prior row -- the voiding is itself permanent
+    history, spec section 6.2's own closing sentence)."""
+    fields = {
+        "row_kind": ROW_KIND_VOIDING_EVENT,
+        "corpus_id": corpus_id,
+        "reason": reason,
+        "voided_at": voided_at if voided_at is not None else _iso_utc_now(),
+    }
+    return ledger.append_row(fields)
+
+
+def existing_fold_result(ledger: WalkForwardLedger, *, sequence_id: str, fold_index: int, spec_hash: str) -> dict | None:
+    """The already-recorded ``fold_result`` row for this exact ``(sequence_id, fold_index,
+    spec_hash)``, or ``None`` -- the identity of ONE evaluation act (a sequence's own fold, under
+    one frozen spec). Two rows sharing all three are the SAME evaluation re-executed, never two
+    independent pieces of evidence."""
+    for row in ledger.rows_of_kind(ROW_KIND_FOLD_RESULT):
+        if (
+            row.get("sequence_id") == sequence_id
+            and row.get("fold_index") == fold_index
+            and row.get("spec_hash") == spec_hash
+        ):
+            return row
+    return None
+
+
+def mode_b_predeclarations_for_sequence(ledger: WalkForwardLedger, sequence_id: str) -> list[dict]:
+    return [row for row in ledger.rows_of_kind(ROW_KIND_MODE_B_SPEC) if row.get("sequence_id") == sequence_id]
+
+
+def record_mode_b_predeclaration(ledger: WalkForwardLedger, spec: dict) -> dict:
+    """spec section 6.5's own "a human-authored spec is registered (LEDGER ROW, spec hash,
+    timestamp) FIRST; evaluation then runs on later windows": persists ONE permanent
+    ``mode_b_spec`` row for a ``register_mode_b_spec`` result, so the predeclaration is a
+    hash-chained, timestamped fact on disk written BEFORE any outcome is read -- not merely an
+    ordering the caller asserts in a docstring. A re-registration of the byte-identical spec
+    (same ``sequence_id`` AND ``spec_hash``) is an idempotent replay returning the FIRST
+    predeclaration row (the ``register_fold_spec`` precedent), so a repeat operator run neither
+    grows the ledger nor back-dates -- or forward-dates -- the original registration instant that
+    spec section 6.7's ``historical_oos`` rule reads."""
+    for row in mode_b_predeclarations_for_sequence(ledger, spec["sequence_id"]):
+        if row.get("spec_hash") == spec["spec_hash"]:
+            return dict(row)
+    return ledger.append_row({"row_kind": ROW_KIND_MODE_B_SPEC, **spec})
+
+
+def append_fold_result(ledger: WalkForwardLedger, fields: dict) -> dict:
+    """Persist ONE permanent ``fold_result`` row -- a thin, explicit entry point (the
+    ``scout.register_and_screen_candidate`` -> ``ScoutLedger.append_row`` precedent) so every
+    caller (Mode A's per-origin refit, Mode B's per-window evaluation, the diagnostic run, the
+    TR-16 oracle proofs) writes through the SAME one function, never a second implementation of
+    "what a fold-result row looks like on disk". ``fields`` must already carry ``row_kind`` unset
+    -- this function stamps it, refusing to silently overwrite a caller-supplied one that might
+    diverge.
+
+    **Re-evaluating the SAME (sequence_id, fold_index, spec_hash) is an idempotent replay** (the
+    ``register_fold_spec`` precedent directly above): the EXISTING row is returned unchanged rather
+    than appended a second time. Without this, a benign repeat of an operator act -- pressing
+    ``POST /research/desk/micro/walkforward/compute`` twice, or re-running the CLI warmer -- would
+    append a second physical row per fold, and every downstream consumer that counts rows
+    (``sequence_verdict``'s own ``WF_MIN_SUFFICIENT_FOLDS`` floor, ``_pooled_sign_agreement``,
+    ``decay_view``'s older-vs-recent split) would silently pool the SAME fold twice: two real
+    sufficient folds would read as four, turning an honest "2 < 3 sufficient folds -- refused" into
+    a COMPUTED verdict over duplicated evidence. The denominator never shrinks (spec section 6) --
+    it must not spuriously GROW either."""
+    if "row_kind" in fields:
+        raise ValueError("append_fold_result stamps row_kind itself -- do not pass one")
+    sequence_id, fold_index, spec_hash = fields.get("sequence_id"), fields.get("fold_index"), fields.get("spec_hash")
+    if sequence_id is not None and fold_index is not None and spec_hash is not None:
+        already = existing_fold_result(ledger, sequence_id=sequence_id, fold_index=fold_index, spec_hash=spec_hash)
+        if already is not None:
+            return dict(already)
+    return ledger.append_row({"row_kind": ROW_KIND_FOLD_RESULT, **fields})
+
+
+def fold_results_for_sequence(ledger: WalkForwardLedger, sequence_id: str) -> list[dict]:
+    return [row for row in ledger.rows_of_kind(ROW_KIND_FOLD_RESULT) if row.get("sequence_id") == sequence_id]
+
+
+def sequence_ids_for_corpus(ledger: WalkForwardLedger, corpus_id: str) -> list[str]:
+    """Every DISTINCT ``sequence_id`` ever recorded for ``corpus_id``, in first-seen (append)
+    order."""
+    seen: list[str] = []
+    seen_set: set[str] = set()
+    for row in ledger.rows_of_kind(ROW_KIND_FOLD_RESULT):
+        if row.get("corpus_id") != corpus_id:
+            continue
+        sequence_id = row["sequence_id"]
+        if sequence_id not in seen_set:
+            seen_set.add(sequence_id)
+            seen.append(sequence_id)
+    return seen
diff --git a/apps/backend/tests/test_micro_accessor.py b/apps/backend/tests/test_micro_accessor.py
new file mode 100644
index 0000000..93376ad
--- /dev/null
+++ b/apps/backend/tests/test_micro_accessor.py
@@ -0,0 +1,356 @@
+"""``micro_accessor.py`` (Era "The Rapid Microscope" J-05) -- the origin-fenced accessor. Test-
+first contract: TC-1, TC-2, TC-3, TC-14 in ``docs/phases/goal-rapid-microscope-iter-5.md``."""
+
+from __future__ import annotations
+
+import ast
+import pathlib
+
+import pytest
+
+from app.config import CONFIG
+from app.research import micro_accessor as ma
+from app.research.datasets import DatasetNotFound, DatasetStore
+from app.research.micro_snapshots import build_snapshot_rows, resolve_micro_snapshots_dir, write_snapshot, snapshot_identity
+from tests.test_micro_observer import _events_for_store
+
+REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
+_APP_DIR = pathlib.Path(__file__).resolve().parent.parent / "app"
+_RESEARCH_DIR = _APP_DIR / "research"
+
+
+def _plant_dataset_and_snapshot(
+    dataset_store: DatasetStore, snapshots_dir: str, *, symbol: str, window_start_utc: str, window_end_utc: str
+) -> dict:
+    """A tiny, REAL dataset (via ``DatasetStore.record``, the ``test_micro_snapshots.py`` ``_plant``
+    precedent) plus its already-built snapshot on disk -- so ``MicroAccessor.read_snapshot_rows``
+    has real rows to serve on the un-fenced-out path."""
+    dataset_meta = dataset_store.record(
+        symbol=symbol, source="fixture", source_kind="fixture", source_id="fixture",
+        split="train", window_start_utc=window_start_utc, window_end_utc=window_end_utc,
+        data_feed="sip", epoch_anchor=0.0, events=_events_for_store(),
+    )
+    rows = build_snapshot_rows(dataset_store, dataset_meta["id"], CONFIG, quote_size_unit="unverified")
+    identity = snapshot_identity(dataset_meta, CONFIG)
+    write_snapshot(snapshots_dir, dataset_meta["id"], rows, {**identity, "quote_size_unit": "unverified"})
+    return dataset_meta
+
+
+@pytest.fixture
+def rig(tmp_path):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    snapshots_dir = resolve_micro_snapshots_dir(str(tmp_path / "datasets"))
+    return dataset_store, snapshots_dir
+
+
+# === TC-1: the origin fence ==========================================================================
+
+
+def test_tc1_a_read_at_or_before_origin_succeeds(rig):
+    dataset_store, snapshots_dir = rig
+    before = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="AAA",
+        window_start_utc="2026-06-08T13:00:00Z", window_end_utc="2026-06-08T13:01:00Z",
+    )
+    accessor = ma.MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin="2026-06-09")
+    rows = accessor.read_snapshot_rows(before["id"])
+    assert len(rows) > 0
+
+
+def test_tc1_a_read_strictly_after_origin_raises_a_typed_error_never_empty(rig):
+    dataset_store, snapshots_dir = rig
+    _before = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="AAA",
+        window_start_utc="2026-06-08T13:00:00Z", window_end_utc="2026-06-08T13:01:00Z",
+    )
+    after = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="BBB",
+        window_start_utc="2026-06-10T13:00:00Z", window_end_utc="2026-06-10T13:01:00Z",
+    )
+    accessor = ma.MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin="2026-06-09")
+    with pytest.raises(ma.MicroAccessorOriginFenceError):
+        accessor.read_snapshot_rows(after["id"])
+
+
+def test_tc1_origin_equal_to_the_dataset_session_date_is_visible_the_fence_is_inclusive(rig):
+    dataset_store, snapshots_dir = rig
+    same_day = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="CCC",
+        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
+    )
+    accessor = ma.MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin="2026-06-09")
+    rows = accessor.read_snapshot_rows(same_day["id"])
+    assert len(rows) > 0
+
+
+def test_tc1_unfenced_mode_origin_none_serves_every_session_date(rig):
+    """The disclosed unfenced mode (``micro_join.py``/``scout.py``'s own re-point) -- ``origin=None``
+    is the explicit default, never a silent no-op."""
+    dataset_store, snapshots_dir = rig
+    after = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="DDD",
+        window_start_utc="2026-06-10T13:00:00Z", window_end_utc="2026-06-10T13:01:00Z",
+    )
+    accessor = ma.MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    rows = accessor.read_snapshot_rows(after["id"])
+    assert len(rows) > 0
+
+
+def test_tc1_a_dataset_id_that_does_not_exist_raises_dataset_not_found_never_swallowed(rig):
+    dataset_store, snapshots_dir = rig
+    accessor = ma.MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin="2026-06-09")
+    with pytest.raises(DatasetNotFound):
+        accessor.read_snapshot_rows("does-not-exist")
+
+
+# === TC-2: sealed-shard invisibility =================================================================
+
+
+def test_tc2_a_sealed_dataset_id_raises_and_carries_only_opaque_metadata_never_rows(rig):
+    dataset_store, snapshots_dir = rig
+    sealed = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="EEE",
+        window_start_utc="2026-06-08T13:00:00Z", window_end_utc="2026-06-08T13:01:00Z",
+    )
+    accessor = ma.MicroAccessor(
+        dataset_store, snapshots_dir, CONFIG, sealed_dataset_ids=frozenset({sealed["id"]})
+    )
+    with pytest.raises(ma.MicroAccessorSealedShardError) as excinfo:
+        accessor.read_snapshot_rows(sealed["id"])
+    assert excinfo.value.opaque_metadata == {"shard_id": sealed["id"], "status": "sealed"}
+    assert "rows" not in vars(excinfo.value) and not hasattr(excinfo.value, "rows")
+
+
+def test_tc2_an_unsealed_dataset_is_unaffected_by_an_unrelated_sealed_id(rig):
+    dataset_store, snapshots_dir = rig
+    open_one = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="FFF",
+        window_start_utc="2026-06-08T13:00:00Z", window_end_utc="2026-06-08T13:01:00Z",
+    )
+    accessor = ma.MicroAccessor(
+        dataset_store, snapshots_dir, CONFIG, sealed_dataset_ids=frozenset({"some-other-id"})
+    )
+    rows = accessor.read_snapshot_rows(open_one["id"])
+    assert len(rows) > 0
+
+
+def test_tc2_sealed_check_takes_priority_over_the_origin_fence(rig):
+    """A sealed dataset dated BEFORE origin is still refused as sealed, not silently let through
+    because it would have passed the fence -- sealed invisibility is unconditional."""
+    dataset_store, snapshots_dir = rig
+    sealed = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="GGG",
+        window_start_utc="2026-06-01T13:00:00Z", window_end_utc="2026-06-01T13:01:00Z",
+    )
+    accessor = ma.MicroAccessor(
+        dataset_store, snapshots_dir, CONFIG, origin="2026-06-09",
+        sealed_dataset_ids=frozenset({sealed["id"]}),
+    )
+    with pytest.raises(ma.MicroAccessorSealedShardError):
+        accessor.read_snapshot_rows(sealed["id"])
+
+
+# === TC-3: the import-ban source-scan (the test_referee_guards.py AST precedent) ====================
+
+
+def _imported_module_names(path: pathlib.Path) -> set[str]:
+    tree = ast.parse(path.read_text())
+    names: set[str] = set()
+    for node in ast.walk(tree):
+        if isinstance(node, ast.Import):
+            for alias in node.names:
+                names.add(alias.name)
+        elif isinstance(node, ast.ImportFrom):
+            if node.module:
+                names.add(node.module)
+            for alias in node.names:
+                names.add(alias.name)
+                if node.module:
+                    names.add(f"{node.module}.{alias.name}")
+    return names
+
+
+def _dotted_source(node: ast.AST) -> str | None:
+    """``micro_snapshots.read_snapshot_rows`` -> ``"micro_snapshots"`` for the attribute's OWN
+    value; ``None`` when the value is not a plain dotted name (e.g. ``MicroAccessor(...).read_
+    snapshot_rows(...)``, whose value is a Call -- the LEGAL door, never a raw-opener reference)."""
+    parts: list[str] = []
+    while isinstance(node, ast.Attribute):
+        parts.append(node.attr)
+        node = node.value
+    if isinstance(node, ast.Name):
+        parts.append(node.id)
+        return ".".join(reversed(parts))
+    return None
+
+
+def _raw_opener_references(path: pathlib.Path) -> set[str]:
+    """Every reference to the RAW snapshot-row opener in one source file: an import of the name
+    itself (``from .micro_snapshots import read_snapshot_rows``, ``import ...read_snapshot_rows``)
+    OR a module-qualified attribute call on the module that defines it
+    (``micro_snapshots.read_snapshot_rows(...)`` -- the bypass a pure import-scan misses, since
+    ``from . import micro_snapshots`` imports no banned NAME at all)."""
+    references = {name for banned in _BANNED_RAW_OPENERS for name in _imported_module_names(path) if name.split(".")[-1] == banned}
+    tree = ast.parse(path.read_text())
+    for node in ast.walk(tree):
+        if isinstance(node, ast.Attribute) and node.attr in _BANNED_RAW_OPENERS:
+            source = _dotted_source(node.value)
+            if source is not None and source.split(".")[-1] == _RAW_OPENER_DEFINER:
+                references.add(f"{source}.{node.attr}")
+    return references
+
+
+_BANNED_RAW_OPENERS = ("read_snapshot_rows",)
+_RAW_OPENER_DEFINER = "micro_snapshots"
+_ALLOWED_IMPORTER = "micro_accessor.py"
+
+
+def test_tc3_no_module_other_than_micro_accessor_imports_read_snapshot_rows():
+    """TC-3, verbatim: "given the FULL BACKEND SOURCE TREE ... no module other than
+    ``micro_accessor.py`` contains an import of ``read_snapshot_rows``". Scanned over ALL of
+    ``app/`` recursively (``engine/``, ``mcp/``, ``providers/``, ``research/``, and the package
+    root alike) -- not ``app/research/*.py`` alone, which would leave every other package free to
+    open the raw reader with the guard still green."""
+    app_files = sorted(p for p in _APP_DIR.rglob("*.py") if "__pycache__" not in p.parts)
+    assert len(app_files) > 50, f"only {len(app_files)} app modules scanned -- has the tree moved?"
+    assert any(p.parent.name == "engine" for p in app_files), "app/engine not covered -- scan is too narrow"
+    checked_the_allowed_importer = False
+    violations: dict[str, set[str]] = {}
+    for path in app_files:
+        references = _raw_opener_references(path)
+        if path.name == _ALLOWED_IMPORTER:
+            checked_the_allowed_importer = True
+            continue
+        if references:
+            violations[str(path.relative_to(_APP_DIR))] = references
+    assert not violations, f"raw snapshot-row opener referenced outside micro_accessor.py: {violations}"
+    assert checked_the_allowed_importer, f"{_ALLOWED_IMPORTER} not found -- has it moved?"
+
+
+def test_tc3_the_guard_also_catches_a_module_qualified_call_that_imports_no_banned_name(tmp_path):
+    """The bypass a pure import-scan cannot see: ``from . import micro_snapshots`` imports only the
+    MODULE name (never ``read_snapshot_rows``), then calls the raw opener as an attribute. The
+    guard must flag it -- and must NOT flag the LEGAL ``MicroAccessor(...).read_snapshot_rows(...)``
+    call ``micro_join.py``/``scout.py`` now make."""
+    bypass = tmp_path / "bypass.py"
+    bypass.write_text(
+        "from . import micro_snapshots\n"
+        "def read(d, i):\n"
+        "    return micro_snapshots.read_snapshot_rows(d, i)\n"
+    )
+    assert _raw_opener_references(bypass) == {"micro_snapshots.read_snapshot_rows"}
+
+    legal = tmp_path / "legal.py"
+    legal.write_text(
+        "from .micro_accessor import MicroAccessor\n"
+        "def read(store, d, cfg, i):\n"
+        "    return MicroAccessor(store, d, cfg).read_snapshot_rows(i)\n"
+    )
+    assert _raw_opener_references(legal) == set()
+
+
+def test_tc3_micro_join_and_scout_no_longer_import_read_snapshot_rows_directly():
+    """The concrete re-point this iteration performs (TC-4/TC-5's own precondition) -- named
+    explicitly so a reviewer sees the two call sites the plan identified are actually gone,
+    not merely covered by the generic glob above."""
+    for filename in ("micro_join.py", "scout.py"):
+        path = _RESEARCH_DIR / filename
+        imported = _imported_module_names(path)
+        hit = {name for name in imported if name.split(".")[-1] == "read_snapshot_rows"}
+        assert not hit, f"{filename} still imports read_snapshot_rows directly: {hit}"
+
+
+def test_tc3_import_ban_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing (the test_referee_guards.py
+    precedent, this codebase's own established per-guard pattern)."""
+    seeded_imports = {"app.research.micro_snapshots.read_snapshot_rows", "app.research.other"}
+    hits = {name for banned in _BANNED_RAW_OPENERS for name in seeded_imports if name.split(".")[-1] == banned}
+    assert hits == {"app.research.micro_snapshots.read_snapshot_rows"}
+
+
+# === ExposureRegistry: log/query + r2 initialization (TC-14) ========================================
+
+
+def test_exposure_registry_log_and_query_roundtrip(tmp_path):
+    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
+    registry.log_exposure(
+        corpus_id="legacy_tick", window="2026-06-08", surface="test",
+        logged_at="2026-06-09T00:00:00.000000Z",
+    )
+    assert registry.is_exposed_before(
+        corpus_id="legacy_tick", window="2026-06-08", instant="2026-06-10T00:00:00.000000Z"
+    )
+    assert not registry.is_exposed_before(
+        corpus_id="legacy_tick", window="2026-06-08", instant="2026-06-08T00:00:00.000000Z"
+    )
+    assert not registry.is_exposed_before(
+        corpus_id="OTHER_CORPUS", window="2026-06-08", instant="2026-06-10T00:00:00.000000Z"
+    )
+
+
+def test_exposure_registry_chain_is_verified(tmp_path):
+    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
+    registry.log_exposure(corpus_id="c", window="2026-06-08", surface="s", logged_at="2026-06-09T00:00:00Z")
+    assert registry.verify_chain()["ok"] is True
+
+
+def test_tc14_r2_initialization_pre_marks_every_named_window_exposed_before_any_serving_act(tmp_path):
+    """given a freshly initialized exposure registry, when any window of the (here, a small
+    stand-in) corpus is queried for its exposure state, then it reads already-exposed from r2
+    initialization, before any explicit serving act in this run."""
+    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
+    windows = ["2026-06-08", "2026-06-09", "2026-06-10"]
+    n = ma.initialize_r2_exposure_registry(registry, corpus_id="legacy_tick", windows=windows)
+    assert n == 3
+    for window in windows:
+        # ANY later instant reads already-exposed -- no explicit log_exposure call happened this run.
+        assert registry.is_exposed_before(
+            corpus_id="legacy_tick", window=window, instant="2026-08-17T00:00:00.000000Z"
+        )
+    # A window this corpus never named is honestly NOT pre-marked.
+    assert not registry.is_exposed_before(
+        corpus_id="legacy_tick", window="2099-01-01", instant="2026-08-17T00:00:00.000000Z"
+    )
+    # A genuinely new corpus_id this run never initialized starts clean.
+    assert not registry.is_exposed_before(
+        corpus_id="brand_new_synthetic_corpus", window="2026-06-08",
+        instant="2026-08-17T00:00:00.000000Z",
+    )
+
+
+# === the "two callers, two disciplines" exposure-logging boundary (module docstring) ================
+
+
+def test_unfenced_mode_never_logs_exposure_even_when_a_registry_is_supplied(rig, tmp_path):
+    dataset_store, snapshots_dir = rig
+    dataset_meta = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="HHH",
+        window_start_utc="2026-06-08T13:00:00Z", window_end_utc="2026-06-08T13:01:00Z",
+    )
+    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
+    accessor = ma.MicroAccessor(
+        dataset_store, snapshots_dir, CONFIG, origin=None,
+        exposure_registry=registry, corpus_id="legacy_tick",
+    )
+    accessor.read_snapshot_rows(dataset_meta["id"])
+    assert registry.all_rows() == []
+
+
+def test_origin_fenced_mode_with_a_registry_logs_exactly_one_exposure_entry(rig, tmp_path):
+    dataset_store, snapshots_dir = rig
+    dataset_meta = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="III",
+        window_start_utc="2026-06-08T13:00:00Z", window_end_utc="2026-06-08T13:01:00Z",
+    )
+    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
+    accessor = ma.MicroAccessor(
+        dataset_store, snapshots_dir, CONFIG, origin="2026-06-09",
+        exposure_registry=registry, corpus_id="a_corpus", surface="walkforward_test",
+    )
+    accessor.read_snapshot_rows(dataset_meta["id"], logged_at="2026-06-09T05:00:00.000000Z")
+    rows = registry.all_rows()
+    assert len(rows) == 1
+    assert rows[0]["corpus_id"] == "a_corpus"
+    assert rows[0]["window"] == "2026-06-08"
+    assert rows[0]["surface"] == "walkforward_test"
+    assert rows[0]["logged_at"] == "2026-06-09T05:00:00.000000Z"
diff --git a/apps/backend/tests/test_micro_chain_ledger.py b/apps/backend/tests/test_micro_chain_ledger.py
new file mode 100644
index 0000000..75c1f9e
--- /dev/null
+++ b/apps/backend/tests/test_micro_chain_ledger.py
@@ -0,0 +1,115 @@
+"""``micro_chain_ledger.py`` (Era "The Rapid Microscope" J-05) -- the shared hash-chain +
+tail-anchor primitive ``micro_accessor.ExposureRegistry`` and ``walkforward_ledger.
+WalkForwardLedger`` both build on. Tested directly, once, here -- the iter-4 audit's own lesson
+(``scout_ledger.py``'s B2 fix) applied to a NEW primitive from day one rather than re-discovered
+per ledger that uses it."""
+
+from __future__ import annotations
+
+import json
+
+from app.research.micro_chain_ledger import HashChainedLedger
+
+
+def test_append_row_chains_and_stamps_row_index(tmp_path):
+    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
+    row0 = ledger.append_row({"value": "a"})
+    row1 = ledger.append_row({"value": "b"})
+    assert row0["row_index"] == 0
+    assert row0["prev_hash"] is None
+    assert row1["row_index"] == 1
+    assert row1["prev_hash"] == row0["row_hash"]
+    assert row0["row_hash"] != row1["row_hash"]
+
+
+def test_identical_fields_appended_twice_yield_two_distinct_permanent_rows(tmp_path):
+    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
+    first = ledger.append_row({"value": "same"})
+    second = ledger.append_row({"value": "same"})
+    assert first["row_hash"] != second["row_hash"]
+    assert len(ledger.all_rows()) == 2
+
+
+def test_verify_chain_ok_on_a_clean_chain(tmp_path):
+    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
+    ledger.append_row({"value": "a"})
+    ledger.append_row({"value": "b"})
+    ledger.append_row({"value": "c"})
+    assert ledger.verify_chain() == {"ok": True, "failed_at_row": None, "reason": None}
+
+
+def test_verify_chain_ok_on_an_empty_ledger(tmp_path):
+    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
+    assert ledger.verify_chain() == {"ok": True, "failed_at_row": None, "reason": None}
+
+
+def test_in_place_edit_of_a_row_is_caught_at_that_row(tmp_path):
+    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
+    ledger.append_row({"value": "a"})
+    ledger.append_row({"value": "b"})
+    ledger.append_row({"value": "c"})
+    lines = ledger.path.read_text(encoding="utf-8").splitlines()
+    tampered = json.loads(lines[1])
+    tampered["value"] = "TAMPERED"
+    lines[1] = json.dumps(tampered, sort_keys=True)
+    ledger.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
+    result = ledger.verify_chain()
+    assert result == {"ok": False, "failed_at_row": 1, "reason": "content_hash_mismatch"}
+
+
+def test_mid_file_deletion_is_caught_at_the_first_row_whose_link_breaks(tmp_path):
+    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
+    ledger.append_row({"value": "a"})
+    ledger.append_row({"value": "b"})
+    ledger.append_row({"value": "c"})
+    lines = ledger.path.read_text(encoding="utf-8").splitlines()
+    del lines[1]  # delete the middle row -- row 2's prev_hash no longer resolves
+    ledger.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
+    result = ledger.verify_chain()
+    assert result["ok"] is False
+    assert result["reason"] == "prev_hash_mismatch"
+
+
+def test_tail_truncation_is_caught_by_the_durable_anchor_even_though_the_chain_still_verifies(tmp_path):
+    """The iter-4 audit's own B2 lesson: a hash chain alone cannot see rows simply MISSING from
+    its own end -- every surviving row stays perfectly self-consistent. The durable tail anchor
+    (written AFTER each row it commits to) is what catches it."""
+    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
+    ledger.append_row({"value": "a"})
+    ledger.append_row({"value": "b"})
+    ledger.append_row({"value": "c"})
+    lines = ledger.path.read_text(encoding="utf-8").splitlines()
+    del lines[-1]  # delete the LAST row -- the remaining chain is perfectly self-consistent
+    ledger.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
+    result = ledger.verify_chain()
+    assert result == {"ok": False, "failed_at_row": 2, "reason": "tail_truncated"}
+
+
+def test_a_ledger_with_rows_but_no_anchor_file_reports_head_anchor_missing(tmp_path):
+    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
+    ledger.append_row({"value": "a"})
+    ledger._head_path.unlink()  # simulate a ledger whose anchor file was never written/lost
+    result = ledger.verify_chain()
+    assert result == {"ok": False, "failed_at_row": None, "reason": "head_anchor_missing"}
+
+
+def test_anchor_written_after_the_row_it_commits_to_a_shorter_chain_than_the_anchor_is_the_only_bad_state(tmp_path):
+    """A crash BETWEEN writing the row and writing the anchor leaves the ledger LONGER than the
+    anchor claims -- benign, and still verified against the anchored prefix (module docstring)."""
+    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
+    ledger.append_row({"value": "a"})
+    anchor_after_one = json.loads(ledger._head_path.read_text(encoding="utf-8"))
+    ledger.append_row({"value": "b"})  # a "crash" here would leave the ledger 2 rows, anchor at 1
+    ledger._head_path.write_text(json.dumps(anchor_after_one, sort_keys=True), encoding="utf-8")
+    result = ledger.verify_chain()
+    assert result == {"ok": True, "failed_at_row": None, "reason": None}
+
+
+def test_two_independent_ledgers_in_the_same_root_dir_do_not_collide(tmp_path):
+    a = HashChainedLedger(tmp_path, "a.jsonl")
+    b = HashChainedLedger(tmp_path, "b.jsonl")
+    a.append_row({"who": "a"})
+    b.append_row({"who": "b"})
+    b.append_row({"who": "b2"})
+    assert len(a.all_rows()) == 1
+    assert len(b.all_rows()) == 2
diff --git a/apps/backend/tests/test_walkforward.py b/apps/backend/tests/test_walkforward.py
new file mode 100644
index 0000000..89fef79
--- /dev/null
+++ b/apps/backend/tests/test_walkforward.py
@@ -0,0 +1,882 @@
+"""``walkforward.py`` + ``walkforward_ledger.py`` (Era "The Rapid Microscope" J-05) -- the
+
+chronological walk-forward engine. Test-first contract: TC-6 through TC-19, TC-23 through TC-26 in
+``docs/phases/goal-rapid-microscope-iter-5.md`` (TC-21/TC-22, the TR-16 end-to-end oracles, live in
+``test_walkforward_oracles.py`` -- see that file's own module docstring). TC-1/TC-2/TC-3 live in
+``test_micro_accessor.py``; TC-4/TC-5 in ``test_micro_join.py``/``test_scout.py``."""
+
+from __future__ import annotations
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.main import app
+from app.research import walkforward as wf
+from app.research import walkforward_ledger as wl
+from app.research.micro_accessor import ExposureRegistry, initialize_r2_exposure_registry
+from app.research.micro_routes import (
+    get_micro_exposure_registry_dir,
+    get_walkforward_compute_manager,
+    get_walkforward_ledger_dir,
+)
+from app.research.desk_routes import get_playbook_store, get_universe_store
+from app.research.routes import get_bar_store
+
+
+# === helpers ==========================================================================================
+
+_ECON_FLOOR = {"floor_bps": 5.0}
+
+
+def _observation(session_date: str, symbol: str, value: float) -> dict:
+    return {"session_date": session_date, "symbol": symbol, "value": value}
+
+
+def _sufficient_fold_row(
+    *, fold_index: int, sequence_id: str = "seq-x", corpus_id: str = "corpus-x",
+    evidence_class: str = wf.EVIDENCE_CLASS_HISTORICAL_OOS, process_label: str = wf.PROCESS_LABEL_RULE,
+    effect: float = 10.0, sign: str = "positive", n: int = 40, n_sessions: int = 10, n_symbols: int = 3,
+) -> dict:
+    """A hand-built, already-SUFFICIENT fold_result-shaped dict -- the direct
+    ``evaluate_survivor_rule``/``sequence_verdict`` unit-testing style (never routed through the
+    ledger for these pure-function tests)."""
+    return {
+        "fold_index": fold_index, "sequence_id": sequence_id, "corpus_id": corpus_id,
+        "status": wf.FOLD_STATUS_SUFFICIENT, "evidence_class": evidence_class, "process_label": process_label,
+        "effect": effect, "sign": sign, "n": n, "n_sessions": n_sessions, "n_symbols": n_symbols, "missing": {},
+    }
+
+
+def _five_sufficient_oos_rule_process_folds(**overrides) -> list[dict]:
+    return [_sufficient_fold_row(fold_index=i, **overrides) for i in range(5)]
+
+
+# === TC-6: fold-spec registration is frozen verbatim; clustering_unit is corpus-size-invariant ======
+
+
+def test_tc6_fold_spec_fields_are_frozen_exactly_as_registered(tmp_path):
+    ledger = wl.WalkForwardLedger(str(tmp_path))
+    geometry = {"train_sessions": 40, "test_sessions": 20, "step_sessions": 20, "embargo_sessions": 0, "embargo_derivation": "no cross-boundary dependency identified"}
+    row = wl.register_fold_spec(
+        ledger, corpus_id="big-corpus", corpus_manifest_hash="abc123", geometry=geometry,
+        floors={"wf_fold_min_observations": 30},
+    )
+    reread = wl.latest_fold_spec(ledger, "big-corpus")
+    assert reread["geometry"] == geometry
+    assert reread["clustering_unit"] == "session_date"
+    assert reread["corpus_manifest_hash"] == "abc123"
+    assert reread["geometry_hash"] == row["geometry_hash"]
+
+
+def test_tc6_clustering_unit_is_session_date_regardless_of_corpus_size():
+    """clustering_unit stays session_date whether the corpus is the 155-session playbook corpus
+    or the 11-session tick corpus -- no corpus-size-dependent switching, ever (spec section 5.3's
+    r2 rule)."""
+    ledger_big = wl.WalkForwardLedger(str(__import__("tempfile").mkdtemp()))
+    ledger_small = wl.WalkForwardLedger(str(__import__("tempfile").mkdtemp()))
+    geometry = {"train_sessions": 5, "test_sessions": 2, "step_sessions": 2, "embargo_sessions": 0, "embargo_derivation": "n/a"}
+    big = wl.register_fold_spec(ledger_big, corpus_id="big", corpus_manifest_hash="h1", geometry=geometry, floors={})
+    small = wl.register_fold_spec(ledger_small, corpus_id="small", corpus_manifest_hash="h2", geometry=geometry, floors={})
+    assert big["clustering_unit"] == "session_date"
+    assert small["clustering_unit"] == "session_date"
+
+
+# === TC-7: step < test is refused =====================================================================
+
+
+def test_tc7_step_less_than_test_is_refused(tmp_path):
+    ledger = wl.WalkForwardLedger(str(tmp_path))
+    geometry = {"train_sessions": 40, "test_sessions": 20, "step_sessions": 10, "embargo_sessions": 0, "embargo_derivation": "n/a"}
+    with pytest.raises(wl.FoldStepTooSmallError):
+        wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=geometry, floors={})
+    assert ledger.all_rows() == []  # refused BEFORE any row is written
+
+
+# === TC-8: purge exactness is asserted, not assumed ===================================================
+
+
+def test_tc8_a_label_planted_to_cross_a_fold_boundary_fails_with_a_named_error():
+    fold_test_sessions = ["2026-01-05", "2026-01-06", "2026-01-07"]
+    crossing = [
+        _observation("2026-01-05", "AAA", 1.0),
+        _observation("2026-01-08", "BBB", 2.0),  # NOT a member of fold_test_sessions -- the plant
+    ]
+    with pytest.raises(wf.PurgeExactnessError, match="2026-01-08"):
+        wf.assert_purge_exact(crossing, fold_test_sessions, boundary_name="test_sessions")
+
+
+def test_tc8_observations_in_sessions_filters_to_the_allowed_set_with_the_assertion_wired_in():
+    """The production filter every fold-evaluation call site uses: an observation outside the
+    allowed session set is excluded, never fabricated into the fold's own pool -- with TR-6's
+    assertion (proven directly above to raise on a genuinely malformed/pre-filtered input) wired in
+    as an always-on safety net over the filtered result."""
+    observations = [_observation("2026-01-05", "AAA", 1.0), _observation("2099-01-01", "ZZZ", 9.0)]
+    result = wf.observations_in_sessions(observations, ["2026-01-05"], boundary_name="test_sessions")
+    assert result == [_observation("2026-01-05", "AAA", 1.0)]
+
+
+def test_tc8_well_formed_observations_never_raise():
+    observations = [_observation("2026-01-05", "AAA", 1.0), _observation("2026-01-06", "BBB", 2.0)]
+    result = wf.observations_in_sessions(observations, ["2026-01-05", "2026-01-06", "2026-01-07"], boundary_name="test_sessions")
+    assert len(result) == 2
+
+
+# === TC-9: embargo derivation -- E=0 legitimate; the diagnostic run's own E=5 is not universal =======
+
+
+def test_tc9_embargo_sessions_zero_is_accepted_with_its_derivation_recorded(tmp_path):
+    ledger = wl.WalkForwardLedger(str(tmp_path))
+    geometry = {
+        "train_sessions": 10, "test_sessions": 5, "step_sessions": 5, "embargo_sessions": 0,
+        "embargo_derivation": "session-truncated labels + prefix-only features + session-date "
+        "boundaries leave no identified cross-boundary dependency",
+    }
+    row = wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=geometry, floors={})
+    assert row["geometry"]["embargo_sessions"] == 0
+    assert "no identified cross-boundary dependency" in row["geometry"]["embargo_derivation"]
+
+
+def test_tc9_diagnostic_geometry_embargo_is_its_own_predeclared_choice_not_a_universal_default():
+    assert wf.DIAGNOSTIC_GEOMETRY["embargo_sessions"] == 5
+    derivation = wf.DIAGNOSTIC_GEOMETRY["embargo_derivation"]
+    assert "predeclared choice" in derivation
+    assert "universal" in derivation  # explicitly disclaims being a universal rule
+
+
+# === TC-10: geometry freeze (TR-13) + voiding clears survivor states =================================
+
+
+def test_tc10_a_second_different_geometry_without_a_voiding_event_is_refused(tmp_path):
+    ledger = wl.WalkForwardLedger(str(tmp_path))
+    first = {"train_sessions": 40, "test_sessions": 20, "step_sessions": 20, "embargo_sessions": 0, "embargo_derivation": "n/a"}
+    second = {"train_sessions": 30, "test_sessions": 15, "step_sessions": 15, "embargo_sessions": 0, "embargo_derivation": "n/a"}
+    wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=first, floors={})
+    with pytest.raises(wl.FoldGeometryFrozenError):
+        wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=second, floors={})
+
+
+def test_tc10_re_registering_the_identical_geometry_is_an_idempotent_replay_not_a_refusal(tmp_path):
+    ledger = wl.WalkForwardLedger(str(tmp_path))
+    geometry = {"train_sessions": 40, "test_sessions": 20, "step_sessions": 20, "embargo_sessions": 0, "embargo_derivation": "n/a"}
+    first = wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=geometry, floors={})
+    second = wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=geometry, floors={})
+    assert first == second
+    assert len(ledger.rows_of_kind(wl.ROW_KIND_FOLD_SPEC)) == 1
+
+
+def test_tc10_a_voiding_event_permits_a_new_geometry_and_survivor_states_read_void_afterward(tmp_path):
+    ledger = wl.WalkForwardLedger(str(tmp_path))
+    first = {"train_sessions": 40, "test_sessions": 20, "step_sessions": 20, "embargo_sessions": 0, "embargo_derivation": "n/a"}
+    second = {"train_sessions": 30, "test_sessions": 15, "step_sessions": 15, "embargo_sessions": 0, "embargo_derivation": "n/a"}
+    wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=first, floors={})
+    assert wl.is_corpus_era_voided(ledger, "c") is False
+
+    wl.record_voiding_event(ledger, corpus_id="c", reason="geometry change after fold 1")
+    assert wl.is_corpus_era_voided(ledger, "c") is True
+
+    # now a DIFFERENT geometry is accepted
+    new_spec = wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=second, floors={})
+    assert new_spec["geometry"] == second
+
+    # WF_SURVIVOR_RULE_V1's own condition 5 reads this corpus-era as voided regardless of stats
+    folds = _five_sufficient_oos_rule_process_folds()
+    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=True)
+    assert result["verdict"] == "not_survivor"
+    assert result["conditions"]["zero_voiding_events"] is False
+
+
+def test_tc10_voiding_events_are_permanent_never_deleted_or_edited(tmp_path):
+    ledger = wl.WalkForwardLedger(str(tmp_path))
+    wl.record_voiding_event(ledger, corpus_id="c", reason="r1")
+    wl.record_voiding_event(ledger, corpus_id="c", reason="r2")
+    events = wl.voiding_events_for_corpus(ledger, "c")
+    assert len(events) == 2
+    assert [e["reason"] for e in events] == ["r1", "r2"]
+    assert ledger.verify_chain()["ok"] is True
+
+
+# === TC-11/TC-14: Mode A rule identity (TR-14) ========================================================
+
+
+def test_tc11_same_fitting_rule_across_origins_stays_in_the_same_sequence(tmp_path):
+    ledger = wl.WalkForwardLedger(str(tmp_path))
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+    corpus_id = "tc11-corpus"
+    sessions = [f"2026-02-{d:02d}" for d in range(1, 21)]  # 20 sessions
+    geometry = {"train_sessions": 8, "test_sessions": 4, "step_sessions": 4, "embargo_sessions": 0, "embargo_derivation": "n/a"}
+    folds = wf.build_folds(sessions, geometry)
+    assert len(folds) >= 2
+
+    observations = [_observation(s, "AAPL", 1.0) for s in sessions]
+
+    row0 = wf.register_mode_a_origin(
+        ledger, registry, corpus_id=corpus_id, fitting_rule="training_quantile(0.90)", fold=folds[0],
+        train_observations_provider=lambda: observations, test_observations_provider=lambda: observations,
+        floors={}, sidedness="long", econ_floor=None,
+    )
+    row1 = wf.register_mode_a_origin(
+        ledger, registry, corpus_id=corpus_id, fitting_rule="training_quantile(0.90)", fold=folds[1],
+        train_observations_provider=lambda: observations, test_observations_provider=lambda: observations,
+        floors={}, sidedness="long", econ_floor=None,
+    )
+    assert row0["sequence_id"] == row1["sequence_id"]
+
+    row2 = wf.register_mode_a_origin(
+        ledger, registry, corpus_id=corpus_id, fitting_rule="training_quantile(0.95)", fold=folds[0],
+        train_observations_provider=lambda: observations, test_observations_provider=lambda: observations,
+        floors={}, sidedness="long", econ_floor=None,
+    )
+    assert row2["sequence_id"] != row0["sequence_id"]
+
+
+def test_tc11_unknown_fitting_rule_is_refused():
+    with pytest.raises(wf.UnknownFittingRuleError):
+        wf.parse_fitting_rule("not_a_real_rule(1.0)")
+
+
+# === TC-12: spec-hash-then-reveal freeze order ========================================================
+
+
+def test_tc12_the_validation_window_is_not_read_until_after_the_spec_hash_is_frozen(tmp_path):
+    ledger = wl.WalkForwardLedger(str(tmp_path))
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+    sessions = ["2026-03-01", "2026-03-02", "2026-03-03", "2026-03-04"]
+    geometry = {"train_sessions": 2, "test_sessions": 2, "step_sessions": 2, "embargo_sessions": 0, "embargo_derivation": "n/a"}
+    folds = wf.build_folds(sessions, geometry)
+    observations = [_observation(s, "AAPL", 1.0) for s in sessions]
+
+    call_order: list[str] = []
+
+    def _train_provider():
+        call_order.append("train")
+        return observations
+
+    def _test_provider():
+        call_order.append("test")
+        return observations
+
+    row = wf.register_mode_a_origin(
+        ledger, registry, corpus_id="tc12", fitting_rule="training_quantile(0.5)", fold=folds[0],
+        train_observations_provider=_train_provider, test_observations_provider=_test_provider,
+        floors={}, sidedness="long", econ_floor=None,
+    )
+    assert call_order == ["train", "test"]  # train fit -> spec freeze -> ONLY THEN test reveal
+    assert row["spec_hash_recorded_at"] <= row["validation_revealed_at"]
+    # the frozen spec identity excludes the realized fitted value (TR-14): two origins with
+    # different realized values (proven by TC-11's own same-sequence test) still share ONE rule.
+    assert row["realized_fitted_value"] is not None
+
+
+# === TC-13: Mode B registration-first + the mechanical exposure classing rule ========================
+
+
+def test_tc13_a_mode_b_spec_registered_after_a_logged_exposure_is_auto_classed_diagnostic(tmp_path):
+    ledger = wl.WalkForwardLedger(str(tmp_path))
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+    corpus_id = "tc13-corpus"
+    registry.log_exposure(corpus_id=corpus_id, window="2026-04-05", surface="prior-serving", logged_at="2026-04-06T00:00:00.000000Z")
+
+    spec = wf.register_mode_b_spec(
+        corpus_id=corpus_id, rule_id="rule-x", sidedness="long", econ_floor=None,
+        registered_at="2026-04-10T00:00:00.000000Z",  # AFTER the logged exposure entry
+    )
+    fold = {"fold_index": 0, "origin_index": 0, "train_sessions": [], "embargo_sessions": [], "test_sessions": ["2026-04-05"]}
+    observations = [_observation("2026-04-05", "AAPL", 1.0)] * 40
+    row = wf.evaluate_mode_b_fold(ledger, registry, spec=spec, fold=fold, observations=observations, floors={"wf_fold_min_observations": 1, "wf_fold_min_signal_sessions": 1, "wf_fold_min_symbols": 1})
+    assert row["evidence_class"] == wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
+
+
+def test_tc13_a_mode_b_spec_registered_before_any_exposure_of_its_window_classes_historical_oos(tmp_path):
+    ledger = wl.WalkForwardLedger(str(tmp_path))
+    registry = ExposureRegistry(str(tmp_path / "exposure"))  # a genuinely fresh registry -- nothing pre-marked
+    corpus_id = "tc13-fresh-corpus"
+
+    spec = wf.register_mode_b_spec(
+        corpus_id=corpus_id, rule_id="rule-y", sidedness="long", econ_floor=None,
+        registered_at="2026-04-01T00:00:00.000000Z",
+    )
+    fold = {"fold_index": 0, "origin_index": 0, "train_sessions": [], "embargo_sessions": [], "test_sessions": ["2026-04-05"]}
+    observations = [_observation("2026-04-05", "AAPL", 1.0)] * 40
+    row = wf.evaluate_mode_b_fold(ledger, registry, spec=spec, fold=fold, observations=observations, floors={"wf_fold_min_observations": 1, "wf_fold_min_signal_sessions": 1, "wf_fold_min_symbols": 1})
+    assert row["evidence_class"] == wf.EVIDENCE_CLASS_HISTORICAL_OOS
+
+
+def test_tc14_freshly_initialized_registry_reads_every_named_window_exposed_before_any_serving_act(tmp_path):
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+    windows = [f"2026-01-{d:02d}" for d in range(1, 6)]
+    initialize_r2_exposure_registry(registry, corpus_id="legacy_tick", windows=windows)
+    for window in windows:
+        assert registry.is_exposed_before(corpus_id="legacy_tick", window=window, instant="2026-08-17T00:00:00.000000Z")
+
+
+# === TC-15: WF_SURVIVOR_RULE_V1 -- all five conditions, individually violated =========================
+
+
+def test_tc15_all_five_conditions_hold_returns_walkforward_survivor():
+    folds = _five_sufficient_oos_rule_process_folds(effect=10.0, sign="positive")
+    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
+    assert result["verdict"] == wf.WF_VERDICT_SURVIVOR
+    assert result["rule_name"] == wf.WF_SURVIVOR_RULE_V1
+    assert all(result["conditions"].values())
+
+
+def test_tc15_violating_condition_1_class_mix_prevents_survivor():
+    folds = _five_sufficient_oos_rule_process_folds(effect=10.0, sign="positive")
+    folds[0]["evidence_class"] = wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
+    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
+    assert result["verdict"] == "not_survivor"
+    assert result["conditions"]["sufficient_oos_rule_process_folds"] is False
+
+
+def test_tc15_violating_condition_2_sign_agreement_prevents_survivor():
+    # 5 folds, 2 with an opposing sign -> agreement 3/5 = 0.6 < 0.7
+    folds = _five_sufficient_oos_rule_process_folds(effect=10.0, sign="positive")
+    folds[0]["sign"], folds[0]["effect"] = "negative", -10.0
+    folds[1]["sign"], folds[1]["effect"] = "negative", -10.0
+    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
+    assert result["verdict"] == "not_survivor"
+    assert result["conditions"]["sign_agreement"] is False
+    assert result["sign_agreement"] == pytest.approx(0.6)
+
+
+def test_tc15_violating_condition_3_pooled_effect_below_econ_floor_prevents_survivor():
+    folds = _five_sufficient_oos_rule_process_folds(effect=1.0, sign="positive")  # below floor_bps=5.0
+    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
+    assert result["verdict"] == "not_survivor"
+    assert result["conditions"]["pooled_effect_clears_econ_floor"] is False
+
+
+def test_tc15_violating_condition_3_via_missing_econ_floor_prevents_survivor_fail_closed():
+    folds = _five_sufficient_oos_rule_process_folds(effect=10.0, sign="positive")
+    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=None, voided=False)
+    assert result["verdict"] == "not_survivor"
+    assert result["conditions"]["pooled_effect_clears_econ_floor"] is False
+
+
+def test_tc15_violating_condition_4_an_opposite_direction_sufficient_fold_prevents_survivor():
+    folds = _five_sufficient_oos_rule_process_folds(effect=10.0, sign="positive")
+    # a 6th, strongly opposite-direction, econ-floor-clearing fold
+    folds.append(_sufficient_fold_row(fold_index=5, effect=-20.0, sign="negative"))
+    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
+    assert result["verdict"] == "not_survivor"
+    assert result["conditions"]["no_opposite_direction_sufficient_fold"] is False
+
+
+def test_tc15_violating_condition_5_a_voided_corpus_era_prevents_survivor():
+    folds = _five_sufficient_oos_rule_process_folds(effect=10.0, sign="positive")
+    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=True)
+    assert result["verdict"] == "not_survivor"
+    assert result["conditions"]["zero_voiding_events"] is False
+
+
+# === TC-16: below-floor folds serve insufficient with the failed arithmetic ==========================
+
+
+def test_tc16_a_fold_below_min_observations_reads_insufficient_with_the_arithmetic():
+    observations = [_observation(f"2026-05-{(i % 8) + 1:02d}", f"SYM{i % 3}", 1.0) for i in range(10)]  # only 10 < 30
+    result = wf.summarize_fold_observations(observations, {})
+    assert result["status"] == wf.FOLD_STATUS_INSUFFICIENT
+    assert result["missing"]["observations"] == "10 < 30"
+
+
+def test_tc16_a_fold_below_min_signal_sessions_reads_insufficient():
+    observations = [_observation("2026-05-01", f"SYM{i % 3}", 1.0) for i in range(40)]  # 40 obs, 1 session
+    result = wf.summarize_fold_observations(observations, {})
+    assert result["status"] == wf.FOLD_STATUS_INSUFFICIENT
+    assert "signal_sessions" in result["missing"]
+    assert result["missing"]["signal_sessions"] == "1 < 8"
+
+
+def test_tc16_a_fold_below_min_symbols_reads_insufficient():
+    observations = [_observation(f"2026-05-{(i % 10) + 1:02d}", "ONLY_SYMBOL", 1.0) for i in range(40)]
+    result = wf.summarize_fold_observations(observations, {})
+    assert result["status"] == wf.FOLD_STATUS_INSUFFICIENT
+    assert result["missing"]["symbols"] == "1 < 2"
... [diff_bound] apps/backend/tests/test_walkforward.py: 488 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_walkforward_oracles.py b/apps/backend/tests/test_walkforward_oracles.py
new file mode 100644
index 0000000..bf6a50b
--- /dev/null
+++ b/apps/backend/tests/test_walkforward_oracles.py
@@ -0,0 +1,183 @@
+"""TR-16 -- the end-to-end known-null / planted-effect oracles (``docs/rapid-validation-spec.md``
+
+section 9's own TR-16 row: "A synthetic known-null corpus survives nothing end-to-end (Scout +
+folds); a synthetic planted-effect corpus is recovered with the planted sign and magnitude within
+tolerance (mid-basis primary); byte-identical rerun"). Test-first contract: TC-21, TC-22 in
+``docs/phases/goal-rapid-microscope-iter-5.md``.
+
+**Synthetic, keyless, hand-built -- no real tick dataset or engine replay (a disclosed design
+choice, ``walkforward.py``'s own module docstring).** Both fixtures are flat, session-clustered
+``{session_date, symbol, feature_value, outcome_value}`` corpora built directly in Python (the
+``test_scout.py`` TR-8 calibration-fixture style), run through the SAME two production entry
+points this era ships: ``scout.compute_p_screen`` (Scout's own descriptive screen -- proving the
+corpus's OWN ground truth is honestly detectable/undetectable at that stage) and
+``walkforward.build_folds`` / ``walkforward.evaluate_mode_b_fold`` / ``walkforward.sequence_verdict``
+(the walk-forward engine's own fold machinery, evaluating a Mode B spec over the SAME candidate
+cell's own outcome values as its observations). Nothing here re-implements either statistical
+core a second way.
+
+**Corpus shape (both fixtures, identical structure, different outcome-generating rule).** 70
+sessions x 2 symbols x 4 anchors/symbol/session = 560 anchors; ``feature_value`` is a seeded
+standard-normal draw deciding Scout's candidate/comparator split (``>= 0.0``); ``outcome_value``
+(bps) is ``planted_effect_bps + Uniform(-2, 2)`` for a candidate-cell anchor, ``Uniform(-2, 2)``
+alone (mean 0) for a comparator-cell one -- ``planted_effect_bps = 0.0`` for the known-null corpus
+(candidate and comparator are drawn from the IDENTICAL distribution: no true relationship exists
+between ``feature_value`` and ``outcome_value`` at all) and ``20.0`` for the planted-effect corpus
+(a clearly recoverable, deterministic-by-construction mean shift). Walk-forward's own
+``observations`` are the candidate cell's ``outcome_value``s alone (``feature_value >= 0.0``) --
+the "already selected rule, does it hold out of sample" question Mode B asks, mirrored from the
+diagnostic run's own ``playbook_observations`` design.
+
+Geometry: ``train=20, test=10, step=10, embargo=0`` (embargo=0 legitimate here -- each anchor is an
+independent per-print draw with no cross-session memory, so no cross-boundary dependency exists to
+name) over the 70 sessions produces exactly 5 folds, comfortably clearing every WF_FOLD_MIN_*
+floor per fold (~37-43 observations, ~10 signal-carrying sessions, 2 symbols)."""
+
+from __future__ import annotations
+
+import random
+
+import pytest
+
+from app.research import scout
+from app.research import walkforward as wf
+from app.research.micro_accessor import ExposureRegistry
+from app.research.walkforward_ledger import WalkForwardLedger
+
+N_SESSIONS = 70
+SYMBOLS = ("AAA", "BBB")
+ANCHORS_PER_SYMBOL_PER_SESSION = 4
+GEOMETRY = {"train_sessions": 20, "test_sessions": 10, "step_sessions": 10, "embargo_sessions": 0, "embargo_derivation": "each anchor is an independent per-print draw with no cross-session memory -- no cross-boundary dependency identified"}
+ECON_FLOOR = {"floor_bps": 5.0}
+
+PLANTED_EFFECT_BPS = 20.0
+PLANTED_TOLERANCE_BPS = 2.0
+
+
+def _build_synthetic_corpus(*, planted_effect_bps: float, seed_key: str) -> list[dict]:
+    rng = random.Random(seed_key)
+    anchors: list[dict] = []
+    for s in range(N_SESSIONS):
+        session_date = f"2026-01-{s + 1:03d}"
+        for symbol in SYMBOLS:
+            for _ in range(ANCHORS_PER_SYMBOL_PER_SESSION):
+                feature_value = rng.gauss(0.0, 1.0)
+                if feature_value >= 0.0:
+                    outcome_value = planted_effect_bps + rng.uniform(-2.0, 2.0)
+                else:
+                    outcome_value = rng.uniform(-2.0, 2.0)
+                anchors.append(
+                    {
+                        "session_date": session_date, "symbol": symbol,
+                        "feature_value": feature_value, "outcome_value": outcome_value,
+                        "tod_bucket": "mid", "fallback_frac": 0.3,
+                    }
+                )
+    return anchors
+
+
+def _run_scout_screen(anchors: list[dict], *, seed_scope: str) -> tuple[float | None, float | None]:
+    """The REAL production statistical core (``scout.compute_p_screen``), over the synthetic
+    corpus directly -- no second implementation, the ``test_scout.py`` TR-8 precedent."""
+    return scout.compute_p_screen(
+        anchors, transform="threshold", params={"op": "ge", "value": 0.0}, seed_scope=seed_scope, block_length=1
+    )
+
+
+def _run_walkforward(anchors: list[dict], *, corpus_id: str, tmp_path) -> tuple[list[dict], dict]:
+    """The REAL production fold machinery, over the SAME corpus's candidate-cell outcomes. A
+    genuinely fresh ``ExposureRegistry`` (never r2-initialized for this made-up corpus_id) means
+    every fold's window classifies ``historical_oos`` from the mechanical exposure rule alone --
+    proving TR-16's oracles can legitimately reach a survivor verdict, unlike the real
+    legacy/playbook corpora this era otherwise reads."""
+    sessions = sorted({a["session_date"] for a in anchors})
+    folds = wf.build_folds(sessions, GEOMETRY)
+    observations = [
+        {"session_date": a["session_date"], "symbol": a["symbol"], "value": a["outcome_value"]}
+        for a in anchors if a["feature_value"] >= 0.0
+    ]
+    ledger = WalkForwardLedger(str(tmp_path / f"{corpus_id}_ledger"))
+    registry = ExposureRegistry(str(tmp_path / f"{corpus_id}_exposure"))
+    spec = wf.register_mode_b_spec(
+        corpus_id=corpus_id, rule_id="tr16_oracle_rule", sidedness="long", econ_floor=ECON_FLOOR,
+        registered_at="2026-08-17T00:00:00.000000Z",
+    )
+    rows = [wf.evaluate_mode_b_fold(ledger, registry, spec=spec, fold=fold, observations=observations, floors={}) for fold in folds]
+    verdict = wf.sequence_verdict(rows, sidedness="long", econ_floor=ECON_FLOOR, voided=False)
+    return rows, verdict
+
+
+# === TC-21: the known-null corpus survives nothing end to end =========================================
+
+
+def test_tc21_the_known_null_corpus_survives_nothing_through_scout_screening():
+    anchors = _build_synthetic_corpus(planted_effect_bps=0.0, seed_key="tr16-known-null")
+    effect_bps, p_screen = _run_scout_screen(anchors, seed_scope="tr16-known-null-scope")
+    assert p_screen is not None and p_screen >= scout.SCOUT_SCREEN_ALPHA  # never falsely significant
+
+
+def test_tc21_the_known_null_corpus_survives_nothing_through_walkforward_folds(tmp_path):
+    anchors = _build_synthetic_corpus(planted_effect_bps=0.0, seed_key="tr16-known-null")
+    rows, verdict = _run_walkforward(anchors, corpus_id=wf.TR16_KNOWN_NULL_CORPUS_ID, tmp_path=tmp_path)
+    assert len(rows) == 5
+    assert all(row["status"] == wf.FOLD_STATUS_SUFFICIENT for row in rows)
+    assert all(row["evidence_class"] == wf.EVIDENCE_CLASS_HISTORICAL_OOS for row in rows)
+    assert verdict["refused"] is False
+    assert verdict["verdict"] == "not_survivor"  # NEVER walkforward_survivor
+
+
+def test_tc21_the_known_null_corpus_reproduces_byte_identically_on_rerun(tmp_path):
+    anchors_first = _build_synthetic_corpus(planted_effect_bps=0.0, seed_key="tr16-known-null")
+    anchors_second = _build_synthetic_corpus(planted_effect_bps=0.0, seed_key="tr16-known-null")
+    assert anchors_first == anchors_second  # the fixture itself is deterministic
+
+    effect1, p1 = _run_scout_screen(anchors_first, seed_scope="tr16-known-null-scope")
+    effect2, p2 = _run_scout_screen(anchors_second, seed_scope="tr16-known-null-scope")
+    assert (effect1, p1) == (effect2, p2)
+
+    (tmp_path / "a").mkdir()
+    (tmp_path / "b").mkdir()
+    rows1, verdict1 = _run_walkforward(anchors_first, corpus_id="rerun-null-a", tmp_path=tmp_path / "a")
+    rows2, verdict2 = _run_walkforward(anchors_second, corpus_id="rerun-null-b", tmp_path=tmp_path / "b")
+    effects1 = [(r["fold_index"], r["effect"], r["sign"], r["n"]) for r in rows1]
+    effects2 = [(r["fold_index"], r["effect"], r["sign"], r["n"]) for r in rows2]
+    assert effects1 == effects2
+    assert verdict1["verdict"] == verdict2["verdict"] == "not_survivor"
+
+
+# === TC-22: the planted-effect corpus is recovered with the planted sign and magnitude ===============
+
+
+def test_tc22_the_planted_effect_corpus_is_significant_through_scout_screening():
+    anchors = _build_synthetic_corpus(planted_effect_bps=PLANTED_EFFECT_BPS, seed_key="tr16-planted-effect")
+    effect_bps, p_screen = _run_scout_screen(anchors, seed_scope="tr16-planted-effect-scope")
+    assert effect_bps == pytest.approx(PLANTED_EFFECT_BPS, abs=PLANTED_TOLERANCE_BPS)
+    assert p_screen is not None and p_screen < scout.SCOUT_SCREEN_ALPHA
+
+
+def test_tc22_the_planted_effect_corpus_recovers_the_planted_sign_and_magnitude_through_walkforward(tmp_path):
+    anchors = _build_synthetic_corpus(planted_effect_bps=PLANTED_EFFECT_BPS, seed_key="tr16-planted-effect")
+    rows, verdict = _run_walkforward(anchors, corpus_id=wf.TR16_PLANTED_EFFECT_CORPUS_ID, tmp_path=tmp_path)
+    assert len(rows) == 5
+    assert all(row["sign"] == "positive" for row in rows)  # the planted sign, every fold
+    assert verdict["refused"] is False
+    assert verdict["verdict"] == wf.WF_VERDICT_SURVIVOR
+    assert verdict["rule_name"] == wf.WF_SURVIVOR_RULE_V1
+    # mid-basis primary: the RECOVERED pooled effect matches the planted magnitude within tolerance
+    assert verdict["pooled_effect"] == pytest.approx(PLANTED_EFFECT_BPS, abs=PLANTED_TOLERANCE_BPS)
+
+
+def test_tc22_the_planted_effect_corpus_reproduces_byte_identically_on_rerun(tmp_path):
+    anchors_first = _build_synthetic_corpus(planted_effect_bps=PLANTED_EFFECT_BPS, seed_key="tr16-planted-effect")
+    anchors_second = _build_synthetic_corpus(planted_effect_bps=PLANTED_EFFECT_BPS, seed_key="tr16-planted-effect")
+    assert anchors_first == anchors_second
+
+    (tmp_path / "a").mkdir()
+    (tmp_path / "b").mkdir()
+    rows1, verdict1 = _run_walkforward(anchors_first, corpus_id="rerun-planted-a", tmp_path=tmp_path / "a")
+    rows2, verdict2 = _run_walkforward(anchors_second, corpus_id="rerun-planted-b", tmp_path=tmp_path / "b")
+    effects1 = [(r["fold_index"], r["effect"], r["sign"], r["n"]) for r in rows1]
+    effects2 = [(r["fold_index"], r["effect"], r["sign"], r["n"]) for r in rows2]
+    assert effects1 == effects2
+    assert verdict1["pooled_effect"] == verdict2["pooled_effect"]
+    assert verdict1["verdict"] == verdict2["verdict"] == wf.WF_VERDICT_SURVIVOR
```
