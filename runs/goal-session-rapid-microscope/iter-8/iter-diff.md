# Iteration diff (bounded)

Files changed: 9. Shown in full: 7.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/tick_recorder.py` (431 lines not shown)
- `apps/backend/tests/test_tick_recorder.py` (424 lines not shown)

```diff
diff --git a/apps/backend/app/providers/base.py b/apps/backend/app/providers/base.py
index e85b82e..9bd6d50 100644
--- a/apps/backend/app/providers/base.py
+++ b/apps/backend/app/providers/base.py
@@ -8,7 +8,7 @@ iteration (Level 2 book); the interface does not preclude adding it.
 
 from __future__ import annotations
 
-from dataclasses import dataclass
+from dataclasses import dataclass, field
 from enum import Enum
 from typing import AsyncIterator, Iterable, Protocol, Union, runtime_checkable
 
@@ -35,6 +35,15 @@ class TradeEvent:
     straight through from the historical provider's ``RawTrade`` when present. The engine ignores
     them entirely (``FEATURE_NAMES`` and the classifier read only ``price``/``size``/``side``);
     they exist for research consumers (the dataset store's stored rows) only.
+
+    ``conditions`` is projected OUT of the auto-generated ``__hash__`` (era iter-8, closing
+    iter-7 audit finding B5): a frozen dataclass with a ``list`` field raises
+    ``TypeError: unhashable type: 'list'`` the instant that field is populated with a real value
+    — untested until this iteration's recorder became the first caller to actually populate it.
+    ``field(hash=False)`` excludes ONLY ``conditions`` from the hash computation while leaving it
+    in ``__eq__`` unchanged (a hash coarser than equality is legal Python semantics: the hash
+    contract requires only that equal objects hash equal, never the converse) — every other
+    field's role, the engine's byte output, and the golden trace are untouched.
     """
 
     ticker: str
@@ -42,7 +51,7 @@ class TradeEvent:
     price: float
     size: int
     side: Side = Side.UNKNOWN
-    conditions: list[str] | None = None
+    conditions: list[str] | None = field(default=None, hash=False)
     exchange: str | None = None
     tape: str | None = None
     trade_id: int | None = None
@@ -54,6 +63,9 @@ class QuoteEvent:
 
     The four trailing fields mirror ``RawQuote``'s own Card-5.1 preservation fields (see
     ``TradeEvent``'s docstring) — optional, default-``None``, engine-ignored, research-only.
+
+    ``conditions`` is projected out of the auto-generated ``__hash__`` the same way and for the
+    same reason as ``TradeEvent.conditions`` — see that class's docstring.
     """
 
     ticker: str
@@ -62,7 +74,7 @@ class QuoteEvent:
     ask: float
     bid_size: int
     ask_size: int
-    conditions: list[str] | None = None
+    conditions: list[str] | None = field(default=None, hash=False)
     tape: str | None = None
     bid_exchange: str | None = None
     ask_exchange: str | None = None
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index b4ac635..7d72d7c 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -24,8 +24,10 @@ over."""
 from __future__ import annotations
 
 from fastapi import APIRouter, Depends, HTTPException
+from pydantic import BaseModel
 
 from ..config import CONFIG
+from .bar_index import BarIndex
 from .bars import BarStore
 from .datasets import DatasetStore
 from .desk_playbook import PlaybookStore
@@ -39,9 +41,15 @@ from .micro_snapshots import (
     read_run_log,
     resolve_micro_snapshots_dir,
 )
-from .routes import get_bar_store, get_dataset_store
+from .routes import get_bar_index, get_bar_store, get_dataset_store, get_registry, get_study_market_adapter
 from .scout import ScoutComputeManager, list_scout_families
 from .scout_ledger import ScoutLedger, resolve_scout_ledger_dir
+from .tick_recorder import (
+    RecorderCheckpointStore,
+    TickRecorderComputeManager,
+    resolve_tick_recorder_checkpoint_dir,
+    resolve_tick_recorder_log_dir,
+)
 from . import walkforward as wf
 from .walkforward_ledger import WalkForwardLedger
 
@@ -369,3 +377,119 @@ def cancel_walkforward_compute(manager: "wf.WalkForwardComputeManager" = Depends
 def get_walkforward_runs(ledger_dir: str = Depends(get_walkforward_ledger_dir)) -> dict:
     """The durable run history, newest first -- never 404 on zero runs (an honest empty list)."""
     return {"runs": read_run_log(ledger_dir)}
+
+
+# --- J-06 step 2: the tick recorder (tick_recorder.py) --------------------------------------------
+
+
+def get_tick_recorder_checkpoint_dir() -> str:
+    """The recorder's per-chunk checkpoint cache directory -- ``TAPEOLOGY_MICRO_RECORDER_
+    CHECKPOINT_DIR`` if set, else a SIBLING of the config-owned dataset directory
+    (``tick_recorder.resolve_tick_recorder_checkpoint_dir`` -- see that function's own
+    docstring)."""
+    return resolve_tick_recorder_checkpoint_dir(CONFIG.dataset_dir_resolved())
+
+
+def get_tick_recorder_checkpoint_store() -> RecorderCheckpointStore:
+    """A FastAPI dependency so a test overrides it outright or points it at a temp path via the
+    env var -- the ``get_micro_snapshots_dir``-style pattern, one level up (the STORE itself,
+    since the checkpoint cache has no other public accessor)."""
+    return RecorderCheckpointStore(get_tick_recorder_checkpoint_dir())
+
+
+def get_tick_recorder_log_dir() -> str:
+    """The recorder's run-log directory -- ``TAPEOLOGY_MICRO_RECORDER_LOG_DIR`` if set, else a
+    SIBLING of the config-owned dataset directory (``tick_recorder.resolve_tick_recorder_log_dir``
+    -- see that function's own docstring). The run log persists through the SAME
+    ``micro_snapshots.append_run_log``/``read_run_log`` the scout/walk-forward sections above
+    already reuse (no second run-log implementation)."""
+    return resolve_tick_recorder_log_dir(CONFIG.dataset_dir_resolved())
+
+
+# The single in-flight (or last-terminal) recording job for THIS process -- the same
+# module-singleton-behind-a-Depends-accessor precedent as the snapshot/scout/walk-forward managers
+# above.
+_tick_recorder_compute_manager = TickRecorderComputeManager()
+
+
+def get_tick_recorder_compute_manager() -> TickRecorderComputeManager:
+    """A FastAPI dependency so a test overrides it outright with a fresh, isolated manager (the
+    ``get_walkforward_compute_manager`` precedent) -- never reaches into the module-level
+    singleton directly."""
+    return _tick_recorder_compute_manager
+
+
+class TickRecorderComputeRequest(BaseModel):
+    """Body for ``POST /research/desk/micro/recorder/compute``. Both fields are REQUIRED -- this
+    endpoint never defaults to an implicit universe, because exactly which symbols/dates to record
+    is what an operator is deciding (the ``DeepBackfillComputeRequest`` precedent)."""
+
+    symbols: list[str]
+    dates: list[str]
+
+
+@router.post("/recorder/compute")
+def trigger_tick_recorder_compute(
+    body: TickRecorderComputeRequest,
+    dataset_store: DatasetStore = Depends(get_dataset_store),
+    checkpoint_store: RecorderCheckpointStore = Depends(get_tick_recorder_checkpoint_store),
+    adapter=Depends(get_study_market_adapter),
+    bar_store: BarStore = Depends(get_bar_store),
+    bar_index: BarIndex = Depends(get_bar_index),
+    registry=Depends(get_registry),
+    run_log_dir: str = Depends(get_tick_recorder_log_dir),
+    manager: TickRecorderComputeManager = Depends(get_tick_recorder_compute_manager),
+) -> dict:
+    """Start a NEW tick recording over ``body.symbols`` x ``body.dates`` -- chunked, throttled,
+    resumable (``tick_recorder.run_tick_recording``, TR-19 first), writing through the unchanged
+    ``DatasetStore.record`` and pairing a 1m/5m bar backfill for every symbol-day actually
+    recorded -- or, if one is already running, return it UNCHANGED (``started: False``,
+    single-flight, never a second job). Refuses -- 422, before starting anything -- when
+    ``symbols`` or ``dates`` is empty (the ``trigger_desk_deep_backfill_compute`` precedent: a
+    recording's scope is exactly what an operator is deciding, never an implicit default)."""
+    if not body.symbols or not body.dates:
+        raise HTTPException(
+            status_code=422,
+            detail="both symbols and dates are required and must be non-empty -- an operator "
+            "names exactly which symbol-days to record, never an implicit universe",
+        )
+    return manager.trigger(
+        dataset_store, checkpoint_store, adapter, bar_store, bar_index, registry, CONFIG, run_log_dir,
+        symbols=body.symbols, dates=body.dates,
+    )
+
+
+@router.get("/recorder/compute")
+def get_tick_recorder_compute(
+    manager: TickRecorderComputeManager = Depends(get_tick_recorder_compute_manager),
+) -> dict:
+    """The current (or last-terminal) recording job's progress -- never 404 (the idle default
+    before any job has ever run this process)."""
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
+@router.post("/recorder/compute/cancel")
+def cancel_tick_recorder_compute(
+    manager: TickRecorderComputeManager = Depends(get_tick_recorder_compute_manager),
+) -> dict:
+    """Signal cooperative cancellation for the in-flight recording -- a 409 for an idle manager
+    (the snapshot/scout/walk-forward-compute-cancel routes' own precedent), else
+    ``{"state": "cancelled"}`` acknowledging the REQUEST (the worker itself settles once the
+    in-flight chunk finishes)."""
+    if manager.snapshot()["state"] != "running":
+        raise HTTPException(status_code=409, detail="no tick recording is currently running")
+    manager.cancel()
+    return {"state": "cancelled"}
+
+
+@router.get("/recorder/runs")
+def get_tick_recorder_runs(run_log_dir: str = Depends(get_tick_recorder_log_dir)) -> dict:
+    """The durable run history, newest first -- never 404 on zero runs (an honest empty list)."""
+    return {"runs": read_run_log(run_log_dir)}
diff --git a/apps/backend/app/research/walkforward.py b/apps/backend/app/research/walkforward.py
index c2f14fc..9587311 100644
--- a/apps/backend/app/research/walkforward.py
+++ b/apps/backend/app/research/walkforward.py
@@ -982,7 +982,7 @@ TICK_LEGACY_CORPUS_ID = "tick_legacy_symbol_days_v1"
 _ET_ZONE = ZoneInfo("America/New_York")
 
 
-def _tick_dataset_session_dates(dataset_store: DatasetStore) -> list[str]:
+def _tick_dataset_session_dates(dataset_store: DatasetStore) -> tuple[list[str], list[dict]]:
     """Every currently-registered tick dataset's own ET session date (spec section 0: "a session
     is an ET RTH trading date"), one entry per DISTINCT date -- the SAME ET-conversion technique
     ``micro_readiness.py``'s own ``_et_datetime`` and ``micro_accessor.py``'s own
@@ -991,15 +991,23 @@ def _tick_dataset_session_dates(dataset_store: DatasetStore) -> list[str]:
     off ``DatasetStore.list()``'s own already-checksum-verified metadata -- no second inventory
     mechanism, no hardcoded date list (iter-6 plan). Cheap: ``list()`` is metadata-only (no event
     replay), the identical cost ``micro_readiness.py``'s own per-shard ``session_date`` derivation
-    already pays."""
-    records, _errors = dataset_store.list()
+    already pays.
+
+    Returns ``(session_dates, errors)`` (iter-8, closing a gap the iter-8 spec named directly):
+    ``DatasetStore.list()``'s own ``errors`` half — one entry per file that failed its integrity
+    check — is now surfaced to the caller instead of silently discarded (the pre-iteration-8 body
+    bound it to ``_errors`` and dropped it), so a damaged tick recording is REPORTED rather than
+    quietly excluded from the known-session-dates count. The healthy records' dates are computed
+    exactly as before; a corrupt file simply contributes no date (its own session, if any, is
+    honestly absent from the count) while every other healthy shard is unaffected."""
+    records, errors = dataset_store.list()
     session_dates: set[str] = set()
     for meta in records:
         parsed = datetime.fromisoformat(meta["window_start_utc"].replace("Z", "+00:00"))
         if parsed.tzinfo is None:
             parsed = parsed.replace(tzinfo=timezone.utc)
         session_dates.add(parsed.astimezone(_ET_ZONE).date().isoformat())
-    return sorted(session_dates)
+    return sorted(session_dates), errors
 
 
 def run_tick_family_fold_request(ledger: WalkForwardLedger, config: Config) -> dict:
@@ -1012,13 +1020,16 @@ def run_tick_family_fold_request(ledger: WalkForwardLedger, config: Config) -> d
 
     Resolves the REAL legacy tick corpus's session dates via the EXISTING
     ``_tick_dataset_session_dates`` helper (no second inventory mechanism) against a fresh
-    ``DatasetStore`` pointed at ``config.dataset_dir_resolved()``, registers
-    ``DIAGNOSTIC_GEOMETRY`` for ``TICK_LEGACY_CORPUS_ID`` (mirroring
-    ``run_diagnostic_walkforward``'s own register-then-check ordering immediately above its
-    ``build_folds`` call, so the frozen geometry is committed to the ledger even for a
-    below-floor corpus — idempotent on repeat calls via ``register_fold_spec``'s own "identical
-    geometry replays the existing row" contract), then calls the ALREADY-WIRED
-    ``require_sufficient_sessions_for_folds`` (TR-15).
+    ``DatasetStore`` pointed at ``config.dataset_dir_resolved()``, then calls the ALREADY-WIRED
+    ``require_sufficient_sessions_for_folds`` (TR-15) — BEFORE ``register_fold_spec`` (iter-8,
+    closing iter-7 audit finding B2). The pre-iter-8 ordering registered the frozen geometry even
+    for a request that never actually ran, which permanently pinned ``DIAGNOSTIC_GEOMETRY`` and a
+    ``corpus_manifest_hash`` of TODAY'S below-floor corpus as ``TICK_LEGACY_CORPUS_ID``'s ONE
+    fold spec (``register_fold_spec``'s own idempotency keys ONLY on ``geometry_hash``, not the
+    manifest hash, so a later, genuinely sufficient corpus would silently replay that stale row
+    forever). Reordered so a below-floor request writes NOTHING to the fold ledger — a request
+    that never ran leaves no trace — while a genuinely sufficient corpus still registers exactly
+    as before (TC-13).
 
     At today's real corpus (11 distinct ET session dates, far under the 105-session
     ``WF_MIN_SUFFICIENT_FOLDS`` floor) this ALWAYS raises ``InsufficientSessionsForFoldsError``
@@ -1027,23 +1038,34 @@ def run_tick_family_fold_request(ledger: WalkForwardLedger, config: Config) -> d
     the tick corpus (a tick-level "observations" reader, evidence-class classification,
     ``evaluate_mode_b_fold``) is J-06/J-09 scope — the corpus cannot clear this floor until the
     recorder (J-06) grows it, so that machinery is deliberately NOT built here (T-1: never invent
-    a code path this iteration's diff cannot exercise or verify)."""
+    a code path this iteration's diff cannot exercise or verify).
+
+    The returned dict's ``integrity_errors`` (iter-8, TC-14) is ``_tick_dataset_session_dates``'s
+    own ``errors`` half, surfaced verbatim — the SAME key ``micro_readiness.py``'s
+    ``build_readiness`` already serves (no second error-reporting convention), so a damaged tick
+    recording is reported to this function's caller rather than quietly excluded from the
+    known-session-dates count."""
     tick_dataset_store = DatasetStore(config.dataset_dir_resolved())
-    session_dates = _tick_dataset_session_dates(tick_dataset_store)
+    session_dates, errors = _tick_dataset_session_dates(tick_dataset_store)
     corpus_manifest_hash = _sha256(_canonical(session_dates))
     floors = {
         "wf_fold_min_observations": WF_FOLD_MIN_OBSERVATIONS,
         "wf_fold_min_signal_sessions": WF_FOLD_MIN_SIGNAL_SESSIONS,
         "wf_fold_min_symbols": WF_FOLD_MIN_SYMBOLS,
     }
+    require_sufficient_sessions_for_folds(session_dates, DIAGNOSTIC_GEOMETRY)
+    # Reached only by a corpus that genuinely clears the floor -- registers exactly as the
+    # pre-iter-8 ordering did for this same case (idempotent on repeat calls via
+    # `register_fold_spec`'s own "identical geometry replays the existing row" contract).
     register_fold_spec(
         ledger, corpus_id=TICK_LEGACY_CORPUS_ID, corpus_manifest_hash=corpus_manifest_hash,
         geometry=DIAGNOSTIC_GEOMETRY, floors=floors,
     )
-    require_sufficient_sessions_for_folds(session_dates, DIAGNOSTIC_GEOMETRY)
-    # Unreachable at today's 11-session corpus (the line above always raises first); kept minimal
-    # (no `build_folds`/fold-evaluation call) rather than a speculative branch nothing can test.
-    return {"corpus_id": TICK_LEGACY_CORPUS_ID, "session_count": len(session_dates)}
+    return {
+        "corpus_id": TICK_LEGACY_CORPUS_ID,
+        "session_count": len(session_dates),
+        "integrity_errors": errors,
+    }
 
 
 def playbook_observations(
@@ -1171,7 +1193,11 @@ def run_diagnostic_walkforward(
     # entry point -- never a GET route (era Non-Goal: "No scheduling").
     if not has_any_exposure_entries(exposure_registry, TICK_LEGACY_CORPUS_ID):
         tick_dataset_store = DatasetStore(config.dataset_dir_resolved())
-        tick_session_dates = _tick_dataset_session_dates(tick_dataset_store)
+        # iter-8: `_tick_dataset_session_dates` now returns `(dates, errors)` -- this call site
+        # only ever needed the dates (a corrupt file simply contributes no exposure-seed window,
+        # exactly as it always contributed no session date), so the errors half is intentionally
+        # unused here, unlike `run_tick_family_fold_request`'s own call site which SERVES them.
+        tick_session_dates, _tick_dataset_errors = _tick_dataset_session_dates(tick_dataset_store)
         initialize_r2_exposure_registry(exposure_registry, corpus_id=TICK_LEGACY_CORPUS_ID, windows=tick_session_dates)
 
     corpus_manifest_hash = _sha256(_canonical(session_dates))
diff --git a/apps/backend/tests/test_datasets.py b/apps/backend/tests/test_datasets.py
index 5919569..49473e4 100644
--- a/apps/backend/tests/test_datasets.py
+++ b/apps/backend/tests/test_datasets.py
@@ -602,15 +602,16 @@ def test_tc3_schema_basis_and_quote_size_unit_are_stamped_verbatim_when_supplied
         )
 
 
-def test_tc9_no_second_quote_size_unit_vocabulary_or_early_dated_rule_constant_exists():
-    """TC-9: ``micro_features.QUOTE_SIZE_UNITS`` stays the SOLE unit-vocabulary tuple in the repo
-    (this iteration validates against it, never defines a second copy), and
-    ``ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE`` -- the dated-vendor-rule constant the assumption ledger's
-    iter-7 entry explicitly reserves for a future ``tick_recorder.py`` -- is not yet defined
-    anywhere. This iteration ships storage CAPABILITY only (a caller-supplied
-    ``schema_basis``/``quote_size_unit``), never the date-to-unit DECISION rule."""
+def test_tc9_the_dated_rule_constant_lives_exactly_once_in_tick_recorder_never_duplicated():
+    """TC-9 (iter-7) updated to its own anticipated iter-8 shape, not silently dropped:
+    ``micro_features.QUOTE_SIZE_UNITS`` stays the SOLE unit-vocabulary tuple in the repo (this
+    module validates against it, never defines a second copy). ``ALPACA_QUOTE_SIZE_UNIT_
+    EFFECTIVE`` -- the dated-vendor-rule constant the assumption ledger's iter-7 entry explicitly
+    reserved for a future ``tick_recorder.py`` -- now lives EXACTLY there (iter-8, J-06 step 2,
+    closing that reservation) and NOWHERE else; a second, independently-valued copy anywhere
+    (including a second one inside ``tick_recorder.py`` itself) still fails this test."""
     app_dir = Path(__file__).resolve().parents[1] / "app"
-    offending_effective: list[str] = []
+    effective_locations: list[str] = []
     offending_second_tuple: list[str] = []
     py_files = sorted(p for p in app_dir.rglob("*.py") if "__pycache__" not in p.parts)
     assert len(py_files) > 50, f"only {len(py_files)} app modules scanned -- has the tree moved?"
@@ -624,8 +625,11 @@ def test_tc9_no_second_quote_size_unit_vocabulary_or_early_dated_rule_constant_e
             else:
                 continue
             if "ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE" in targets:
-                offending_effective.append(str(path.relative_to(app_dir)))
+                effective_locations.append(str(path.relative_to(app_dir)))
             if "QUOTE_SIZE_UNITS" in targets and path.name != "micro_features.py":
                 offending_second_tuple.append(str(path.relative_to(app_dir)))
-    assert offending_effective == [], f"ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE defined early: {offending_effective}"
+    assert effective_locations == ["research/tick_recorder.py"], (
+        "ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE must be defined exactly once, in tick_recorder.py "
+        f"(the module micro_features.py's own docstring reserves it for): found at {effective_locations}"
+    )
     assert offending_second_tuple == [], f"a second QUOTE_SIZE_UNITS assignment exists: {offending_second_tuple}"
diff --git a/apps/backend/tests/test_real_data_gate.py b/apps/backend/tests/test_real_data_gate.py
index a5b98d3..ae51ff9 100644
--- a/apps/backend/tests/test_real_data_gate.py
+++ b/apps/backend/tests/test_real_data_gate.py
@@ -329,6 +329,22 @@ def test_alpaca_sdk_import_confined_to_one_module():
     assert hits == ["providers/adapters/alpaca.py"]
 
 
+def test_tick_recorder_names_no_credential_and_imports_no_vendor_sdk():
+    # iter-8, J-06 step 2 (TC-15): tick_recorder.py mirrors desk_deep_backfill.py's own
+    # confinement -- it resolves its adapter through the EXISTING routes.get_study_market_adapter
+    # seam and passes real requests through the vendor-neutral MarketDataAdapter interface only,
+    # never naming a credential env var or importing the SDK directly. The two broad rglob scans
+    # above already sweep this file (it lives under app/research/); this pins the specific module
+    # explicitly rather than relying on it being incidentally caught by a repo-wide sweep.
+    source = (APP_DIR / "research" / "tick_recorder.py").read_text()
+    for banned in ("ALPACA_API_KEY", "ALPACA_API_SECRET", "from alpaca", "import alpaca"):
+        assert banned not in source, (
+            f"tick_recorder.py names {banned!r} -- credentials and the SDK are confined to "
+            "providers/adapters/alpaca.py, and this module only ever passes real requests "
+            "through the vendor-neutral MarketDataAdapter interface"
+        )
+
+
 def test_live_sdk_symbols_confined_to_one_module():
     # The live socket class name appears in EXACTLY one module: the live wiring (LiveProvider,
     # the async feeder, the live POST branch) is vendor-neutral; only the adapter names the SDK.
diff --git a/apps/backend/tests/test_walkforward.py b/apps/backend/tests/test_walkforward.py
index 681510a..b3bf83a 100644
--- a/apps/backend/tests/test_walkforward.py
+++ b/apps/backend/tests/test_walkforward.py
@@ -1059,12 +1059,104 @@ def test_tc6_the_family_flag_prints_the_typed_refusal_naming_the_real_shortfall(
 
     ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
     assert ledger.rows_of_kind(wl.ROW_KIND_FOLD_RESULT) == []
-    # The fold spec IS registered (`register_fold_spec` fires before
-    # `require_sufficient_sessions_for_folds`, mirroring the diagnostic path's own ordering) --
-    # provenance even for a below-floor corpus, this iteration's own developer-call.
+    # iter-8 (closing iter-7 audit finding B2): `require_sufficient_sessions_for_folds` now runs
+    # BEFORE `register_fold_spec`, so a below-floor request writes NOTHING to the fold ledger --
+    # no fold spec, no fold result. A request that never actually ran must leave zero trace,
+    # never a frozen geometry + a manifest hash the corpus can outgrow but the ledger can't
+    # update (TC-13).
     fold_spec = wl.latest_fold_spec(ledger, wf.TICK_LEGACY_CORPUS_ID)
-    assert fold_spec is not None
-    assert fold_spec["geometry"] == wf.DIAGNOSTIC_GEOMETRY
+    assert fold_spec is None
+
+
+def test_tc13_a_below_floor_tick_family_request_leaves_the_ledger_completely_unchanged(tmp_path):
+    """iter-8 TC-13, called directly (not through the CLI): ``run_tick_family_fold_request``
+    against the real 11-session corpus raises BEFORE ``register_fold_spec`` runs, so the ledger
+    holds ZERO new rows for ``TICK_LEGACY_CORPUS_ID`` afterward -- not just zero fold results (the
+    pre-fix behaviour already had that), but zero fold SPEC too."""
+    tick_store = DatasetStore(str(tmp_path / "datasets"))
+    for day in range(1, 12):  # 11 distinct ET session dates -> 11 < 105
+        _plant_tick_dataset(
+            tick_store, symbol="AAPL",
+            window_start_utc=f"2026-06-{day:02d}T13:30:00Z",
+            window_end_utc=f"2026-06-{day:02d}T20:00:00Z",
+            price=100.00 + day,
+        )
+    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    config = _FakeConfig(dataset_dir=str(tmp_path / "datasets"))
+
+    with pytest.raises(wf.InsufficientSessionsForFoldsError, match=r"11 < 105"):
+        wf.run_tick_family_fold_request(ledger, config)
+
+    assert wl.latest_fold_spec(ledger, wf.TICK_LEGACY_CORPUS_ID) is None
+    assert ledger.rows_of_kind(wl.ROW_KIND_FOLD_RESULT) == []
+    assert ledger.rows_of_kind(wl.ROW_KIND_FOLD_SPEC) == []
+
+
+def _corrupt_json_file(path) -> None:
+    import json as _json
+
+    data = _json.loads(path.read_text())
+    data["record"]["meta"]["split"] = "not-a-real-split-value"  # breaks the whole-record checksum
+    path.write_text(_json.dumps(data))
+
+
+def test_tc14_a_corrupt_tick_dataset_is_surfaced_via_integrity_errors_never_silently_excluded(tmp_path):
+    """iter-8 TC-14: ``_tick_dataset_session_dates`` no longer discards ``DatasetStore.list()``'s
+    ``_errors`` half -- its caller (``run_tick_family_fold_request``) surfaces a damaged tick
+    recording through the SAME ``integrity_errors`` shape ``micro_readiness.py`` already uses
+    (no second error-reporting convention), while the healthy recordings' session dates are still
+    counted correctly (a floor call still sees 11 sessions, not 10 -- the corrupt file's dates are
+    excluded from the COUNT, but never silently invisible from the RESPONSE)."""
+    tick_dir = tmp_path / "datasets"
+    tick_store = DatasetStore(str(tick_dir))
+    good_meta = []
+    for day in range(1, 12):
+        meta = _plant_tick_dataset(
+            tick_store, symbol="AAPL",
+            window_start_utc=f"2026-06-{day:02d}T13:30:00Z",
+            window_end_utc=f"2026-06-{day:02d}T20:00:00Z",
+            price=100.00 + day,
+        )
+        good_meta.append(meta)
+
+    # Corrupt exactly one of the 11 healthy files -- its own session date is EXCLUDED from the
+    # returned dates (the file cannot be trusted), but every other healthy file's date survives.
+    corrupt_path = tick_dir / f"{good_meta[0]['id']}.json"
+    _corrupt_json_file(corrupt_path)
+
+    session_dates, errors = wf._tick_dataset_session_dates(tick_store)
+    assert len(errors) == 1
+    assert errors[0]["file"] == f"{good_meta[0]['id']}.json"
+    assert session_dates == sorted(f"2026-06-{day:02d}" for day in range(2, 12))  # 10 healthy dates
+
+    # The below-floor refusal still fires off the (now 10-session) healthy count -- the corrupt
+    # file's date is honestly excluded from the ARITHMETIC, never silently invisible from the
+    # response (proven separately below).
+    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    config = _FakeConfig(dataset_dir=str(tick_dir))
+    with pytest.raises(wf.InsufficientSessionsForFoldsError, match=r"10 < 105"):
+        wf.run_tick_family_fold_request(ledger, config)
+
+
+def test_tc14_run_tick_family_fold_request_surfaces_integrity_errors_on_its_success_return(tmp_path, monkeypatch):
+    """The wiring half of TC-14, isolated with a monkeypatch so it stays fast and hermetic rather
+    than planting a real 105+-session corpus: ``run_tick_family_fold_request``'s SUCCESS return
+    dict carries whatever ``_tick_dataset_session_dates`` reports as ``integrity_errors`` --
+    the SAME key ``micro_readiness.py``'s ``build_readiness`` already serves (no second
+    error-reporting convention), never silently dropped on the floor-CLEARING path either."""
+    fake_errors = [{"file": "corrupt-shard.json", "error": "checksum mismatch"}]
+    # 110 distinct labels clear the WF_MIN_SUFFICIENT_FOLDS floor (105) under DIAGNOSTIC_GEOMETRY;
+    # never parsed as real calendar dates by the function under test, only counted and hashed.
+    fake_dates = [f"session-{i:04d}" for i in range(110)]
+    monkeypatch.setattr(wf, "_tick_dataset_session_dates", lambda store: (fake_dates, fake_errors))
+
+    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    config = _FakeConfig(dataset_dir=str(tmp_path / "unused-datasets"))
+
+    result = wf.run_tick_family_fold_request(ledger, config)
+
+    assert result["integrity_errors"] == fake_errors
+    assert result["session_count"] == len(fake_dates)
 
 
 def test_tc6_an_unknown_family_value_is_refused_by_argparse_itself(monkeypatch, capsys):
diff --git a/apps/backend/app/research/tick_recorder.py b/apps/backend/app/research/tick_recorder.py
new file mode 100644
index 0000000..f110d45
--- /dev/null
+++ b/apps/backend/app/research/tick_recorder.py
@@ -0,0 +1,825 @@
+"""The tick recorder (Card 5.2, brought forward) -- era "The Rapid Microscope" J-06 step 2,
+``docs/rapid-validation-spec.md`` section 7.1.
+
+**What this closes.** Iteration 7 shipped the Card-5.1 storage CAPABILITY (optional preservation
+fields on the event pipeline, ``schema_basis``/``quote_size_unit`` kwargs on ``DatasetStore.
+record``) but built no caller that actually populates them. This module is that caller: a chunked,
+throttled, resumable fetch through the EXISTING, UNCHANGED ``AlpacaAdapter.iter_historical_chunks``
+generator, writing through the EXISTING, UNCHANGED ``DatasetStore.record``/``record_from_source``
+under the same store discipline (append-only, checksummed, split frozen at registration).
+
+**Chunk planning (mirrors ``desk_deep_backfill.plan_deep_windows``).** ``plan_recorder_chunks``
+computes every 900s-scale sub-window a recording WOULD fetch, over an explicit ``(symbols, dates)``
+universe, with ZERO store or vendor calls -- the SAME neutral ``split_window`` function
+``iter_historical_chunks`` uses internally, applied to each date's 09:30-16:00 ET RTH session
+window (this module's own private ``ZoneInfo`` constant, the ``micro_readiness.py``/
+``referee_null.py`` per-module idiom -- mirrored, not imported).
+
+**The walk (mirrors ``desk_deep_backfill._run_one_chunk``'s FOUR-value vocabulary, no second
+one).** Chunks are walked in ``(symbol, date)`` groups. A day whose dataset already exists is
+short-circuited entirely (every chunk reports ``"reused"``, zero store or vendor calls -- TC-3). A
+day not yet recorded walks its own chunks in order: a checkpointed chunk (a PRIOR run's raw fetch,
+persisted so a restart never re-pays a vendor call for a chunk that already succeeded) reports
+``"reused"``; a fresh vendor pull reports ``"fetched"`` (checkpointed immediately, throttled to
+``RECORDER_PAGE_BUDGET_PER_MINUTE``); a raised exception reports ``"failed"`` with its detail
+preserved verbatim and marks the WHOLE day unfinalizable THIS run -- but the walk continues to
+every remaining chunk (desk_deep_backfill's own "never aborts" discipline), and a future run
+resumes only the missing chunk(s) via the checkpoint (TC-4/TC-5). Once every chunk of a
+not-yet-recorded day has content in hand, its chunks are assembled (chronological, non-overlapping
+by construction) into ONE dataset via ``record_from_source`` -- ``"unchanged"`` is reserved for the
+rare race where that assembled content is already registered (``DatasetAlreadyRegistered``, caught
+never propagated, mirroring the bar path's own 409 handling).
+
+**TR-19 (spec section 7.1 r2) -- a HARD structural gate.** ``verify_preservation_capability``
+inspects (``dataclasses.fields``) whether ``TradeEvent``/``QuoteEvent`` actually carry the Card-5.1
+preservation field names, called as the FIRST thing ``run_tick_recording`` does -- before a single
+chunk is planned into a fetch or a byte is read from any store. Simulating the capability absent
+(a test passes a deliberately incomplete stand-in dataclass via the ``_trade_cls``/``_quote_cls``
+override) proves the refusal fires; the real, already-shipped classes always satisfy it today.
+
+**Section 2.6 -- the dated vendor-rule stamping.** ``ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE`` (the
+constant ``micro_features.py``'s own docstring reserves for this module) and
+``quote_size_unit_for_session_date`` implement the frozen rule verbatim: Alpaca CTA/UTP displayed
+quote sizes are SHARES for sessions on/after ``2025-11-03``, ROUND LOTS before -- validated (by
+``DatasetStore.record`` itself) against the single existing ``micro_features.QUOTE_SIZE_UNITS``
+tuple, never a second vocabulary.
+
+**The split rule (spec section 7.3, Card 5.2 -- published, frozen, NOT this module's invention).**
+``DatasetStore.record`` requires a split tag; ``recorder_split_for`` computes the EXISTING published
+sha256 rule directly (holdout iff the last hex digit of ``sha256(f"{symbol}:{date}")`` in
+``{0,1,2}``) so this iteration's recorder can call it. This is a DIFFERENT, older, already-public
+axis from ``vault.py``'s NEW opaque HMAC seal assignment (J-06 step 3, out of scope this
+iteration) -- computing the published split here is not vault.py scope creep, it is simply what
+every dataset registration has always required.
+
+**Bar pairing (unchanged machinery).** ``pair_bar_backfill_for_recorded_days`` calls the EXISTING,
+UNCHANGED ``desk_deep_backfill.plan_deep_windows``/``run_deep_backfill`` for every symbol that got a
+dataset this run, over exactly that symbol's own recorded date range -- no second bar-fetch
+implementation.
+
+**The recorder's own throttle.** ``RECORDER_PAGE_BUDGET_PER_MINUTE`` (spec section 1 table) paces
+consecutive real vendor pulls the SAME way ``alpaca.py``'s own ``_throttle_bar_fetch`` paces the bar
+path (a module-level last-call timestamp + ``time.sleep``), applied to the tick path for the first
+time. Deliberately INDEPENDENT of ``Config.historical_chunk_seconds``/
+``historical_chunk_max_concurrency`` -- those govern the cockpit's own on-demand historical replay,
+a different caller; this module reads them nowhere.
+
+**Confinement (the ``desk_deep_backfill.py`` precedent, mirrored).** This module never names an
+Alpaca credential and never imports the Alpaca SDK -- it resolves its adapter through the EXISTING
+``routes.get_study_market_adapter`` seam (test ``dependency_overrides``-aware) and passes real
+requests through the vendor-neutral ``MarketDataAdapter`` interface only.
+
+**No new ``Config`` field.** Every constant here (``RECORDER_PAGE_BUDGET_PER_MINUTE``,
+``RECORDER_CHUNK_SECONDS``, ``ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE``, ``RECORDER_SCHEMA_BASIS``) is a
+plain module constant; storage dirs are bare env-var-or-sibling defaults (the
+``TAPEOLOGY_MICRO_RECORDER_*`` family) -- ``config_fingerprint()`` is untouched.
+"""
+
+from __future__ import annotations
+
+import argparse
+import dataclasses
+import hashlib
+import json
+import os
+import threading
+import time
+import uuid
+from datetime import date, datetime, time as dt_time, timezone
+from pathlib import Path
+from typing import Callable
+from zoneinfo import ZoneInfo
+
+from ..config import CONFIG, Config
+from ..providers.adapters.base import HistoricalWindow, RawQuote, RawTrade, split_window
+from ..providers.base import QuoteEvent, TradeEvent
+from .datasets import (
+    DatasetAlreadyRegistered,
+    DatasetStore,
+    SOURCE_HISTORICAL,
+    SPLIT_HOLDOUT,
+    SPLIT_TRAIN,
+    record_from_source,
+)
+from .desk_deep_backfill import (
+    DESK_DEEP_TIMEFRAMES,
+    plan_deep_windows,
+    run_deep_backfill,
+)
+from .micro_features import QUOTE_SIZE_UNITS
+from .micro_snapshots import append_run_log
+
+__all__ = [
+    "RecorderPreservationCapabilityMissing",
+    "ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE",
+    "RECORDER_SCHEMA_BASIS",
+    "RECORDER_PAGE_BUDGET_PER_MINUTE",
+    "RECORDER_CHUNK_SECONDS",
+    "verify_preservation_capability",
+    "quote_size_unit_for_session_date",
+    "recorder_split_for",
+    "plan_recorder_chunks",
+    "RecorderCheckpointStore",
+    "run_tick_recording",
+    "pair_bar_backfill_for_recorded_days",
+    "TickRecorderComputeManager",
+    "resolve_tick_recorder_checkpoint_dir",
+    "resolve_tick_recorder_log_dir",
+    "main",
+]
+
+
+# --- TR-19: the Card-5.1 preservation-field structural gate (spec section 7.1 r2) -----------------
+
+_TRADE_PRESERVATION_FIELDS = frozenset({"conditions", "exchange", "tape", "trade_id"})
+_QUOTE_PRESERVATION_FIELDS = frozenset({"conditions", "tape", "bid_exchange", "ask_exchange"})
+
+
+class RecorderPreservationCapabilityMissing(Exception):
+    """TR-19: the recorder refuses to record ANY chunk unless the Card-5.1 preservation fields
+    are structurally present on the event dataclasses -- a typed, named refusal, never a silent
+    recording of an under-specified schema."""
+
+
+def verify_preservation_capability(
+    *, trade_cls: type = TradeEvent, quote_cls: type = QuoteEvent
+) -> None:
+    """The TR-19 check itself: pure introspection (``dataclasses.fields``), zero I/O. Callers
+    override ``trade_cls``/``quote_cls`` ONLY to simulate the capability's absence in a test --
+    the real, already-shipped classes (the defaults) always satisfy this today."""
+    trade_fields = {f.name for f in dataclasses.fields(trade_cls)}
+    quote_fields = {f.name for f in dataclasses.fields(quote_cls)}
+    missing_trade = sorted(_TRADE_PRESERVATION_FIELDS - trade_fields)
+    missing_quote = sorted(_QUOTE_PRESERVATION_FIELDS - quote_fields)
+    if missing_trade or missing_quote:
+        raise RecorderPreservationCapabilityMissing(
+            f"Card-5.1 preservation prerequisite missing (TR-19, spec section 7.1 r2): "
+            f"{trade_cls.__name__} lacks {missing_trade}, {quote_cls.__name__} lacks "
+            f"{missing_quote} -- recording refused until the preservation fields ship"
+        )
+
+
+# --- spec section 2.6: the dated vendor-rule stamping ----------------------------------------------
+
+# Reserved by micro_features.py's own docstring for "the module that actually reads it"
+# (tick_recorder.py) -- frozen verbatim from docs/rapid-validation-spec.md section 1's table.
+ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE = "2025-11-03"
+
+# Names that a recorded row's schema carries the Card-5.1 preservation fields (spec section 2.6's
+# "schema_basis -- the event-row schema version, including whether the optional Card-5.1
+# preservation fields ... are present"). A single frozen string -- every row this module ever
+# writes ships WITH the fields (TR-19 refuses otherwise), so there is exactly one basis value.
+RECORDER_SCHEMA_BASIS = "tick_recorder_v1_card_5_1_preservation_present"
+
+
+def quote_size_unit_for_session_date(session_date: str) -> str:
+    """Stamps ``quote_size_unit`` per the dated Alpaca CTA/UTP vendor rule (spec section 2.6):
+    displayed quote sizes are SHARES for sessions on/after ``ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE``,
+    ROUND LOTS before. ``session_date`` is an ISO ``YYYY-MM-DD`` string -- lexicographic comparison
+    is chronological comparison for that format, so no date parsing is needed. Drawn from (and
+    re-validated by ``DatasetStore.record`` against) the single existing
+    ``micro_features.QUOTE_SIZE_UNITS`` tuple -- never a second vocabulary (TC-10)."""
+    unit = "shares" if session_date >= ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE else "round_lots"
+    assert unit in QUOTE_SIZE_UNITS  # sanity only -- DatasetStore.record re-validates regardless
+    return unit
+
+
+# --- spec section 7.3: the published sha256 split rule (Card 5.2, frozen, unchanged) --------------
+
+
+def recorder_split_for(symbol: str, session_date: str) -> str:
+    """The PUBLISHED split rule ``docs/rapid-validation-spec.md`` section 7.3 fixes (Card 5.2,
+    unchanged): ``holdout`` iff the last hex digit of ``sha256(f"{symbol}:{YYYY-MM-DD}")`` is in
+    ``{0, 1, 2}``, else ``train``. ``DatasetStore.record`` requires a split tag on every call; this
+    is that PRE-EXISTING, already-public rule computed directly -- a DIFFERENT, older axis from
+    ``vault.py``'s NEW opaque HMAC seal assignment (J-06 step 3, out of scope this iteration)."""
+    digest = hashlib.sha256(f"{symbol}:{session_date}".encode("utf-8")).hexdigest()
+    return SPLIT_HOLDOUT if int(digest[-1], 16) in (0, 1, 2) else SPLIT_TRAIN
+
+
+# --- the recorder's own throttle (spec section 1: RECORDER_PAGE_BUDGET_PER_MINUTE = 200) ----------
+
+RECORDER_PAGE_BUDGET_PER_MINUTE = 200
+
+# Process-lifetime timestamp (monotonic) of the last REAL recorder vendor call, read/written only
+# by ``_throttle_recorder_fetch`` -- the ``alpaca.py`` ``_LAST_BAR_FETCH_MONOTONIC`` pattern,
+# applied to the tick path for the first time (this module never touches that bar-path global).
+_LAST_RECORDER_FETCH_MONOTONIC: float | None = None
+
+
+def _throttle_recorder_fetch() -> None:
+    """Space consecutive REAL recorder vendor calls at least ``60 / RECORDER_PAGE_BUDGET_PER_
+    MINUTE`` seconds apart -- the ``alpaca._throttle_bar_fetch`` shape verbatim, independent
+    constant. The very first call in a process never waits."""
+    global _LAST_RECORDER_FETCH_MONOTONIC
+    min_interval = 60.0 / RECORDER_PAGE_BUDGET_PER_MINUTE
+    now = time.monotonic()
+    if _LAST_RECORDER_FETCH_MONOTONIC is not None:
+        remaining = min_interval - (now - _LAST_RECORDER_FETCH_MONOTONIC)
+        if remaining > 0:
+            time.sleep(remaining)
+    _LAST_RECORDER_FETCH_MONOTONIC = time.monotonic()
+
+
+def _reset_recorder_throttle_for_tests() -> None:
+    """Test-only: resets the throttle's process-lifetime clock so tests never wait behind a PRIOR
+    test's last call (the ``alpaca._clear_caches`` precedent, narrowed to this one global)."""
+    global _LAST_RECORDER_FETCH_MONOTONIC
+    _LAST_RECORDER_FETCH_MONOTONIC = None
+
+
+# --- chunk planning (mirrors desk_deep_backfill.plan_deep_windows) --------------------------------
+
+# This module's own private ZoneInfo/RTH constants -- the micro_readiness.py/referee_null.py
+# per-module idiom (mirrored, not imported: "each module that needs ET wall-clock resolution owns
+# a private ZoneInfo constant"). RTH bounds are the spec's own "09:30-16:00 ET" (section 0).
+_ET_ZONE = ZoneInfo("America/New_York")
+_RTH_OPEN = dt_time(9, 30)
+_RTH_CLOSE = dt_time(16, 0)
+
+# The recorder's OWN page-size constant -- deliberately INDEPENDENT of
+# Config.historical_chunk_seconds/historical_chunk_max_concurrency (module docstring: "a different
+# caller"). Matches the vendor's own natural page size so a planned chunk ordinarily corresponds
+# to exactly one real iter_historical_chunks page.
+RECORDER_CHUNK_SECONDS = 900.0
+
+
+def _session_window_utc(session_date: str) -> tuple[datetime, datetime]:
+    """The 09:30-16:00 ET RTH window for one session date, in UTC -- the SAME conversion
+    ``micro_readiness.py``'s own ``_et_datetime``/``_rth_overlap`` use, applied in the other
+    direction (ET wall-clock -> UTC instants) so the planner never touches a store to learn what a
+    session's clock bounds are."""
+    day = date.fromisoformat(session_date)
+    open_et = datetime.combine(day, _RTH_OPEN, tzinfo=_ET_ZONE)
+    close_et = datetime.combine(day, _RTH_CLOSE, tzinfo=_ET_ZONE)
+    return open_et.astimezone(timezone.utc), close_et.astimezone(timezone.utc)
+
+
+def _iso_utc(value: datetime) -> str:
+    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
+
+
+def plan_recorder_chunks(
+    symbols: list[str], dates: list[str], *, chunk_seconds: float = RECORDER_CHUNK_SECONDS
+) -> list[dict]:
+    """Every chunk a recording WOULD fetch, computed WITHOUT touching a store or a vendor (TC-1):
+    ``[{"symbol", "date", "start", "end"}, ...]`` in ``(symbol, date, start)`` order -- symbol
+    outer, date inner, matching ``plan_deep_windows``'s own nesting shape. Sub-window boundaries
+    within each date's RTH session come from the SAME neutral ``split_window`` function
+    ``iter_historical_chunks`` uses internally (imported from the adapter base, never
+    re-implemented), so this planner's own chunk count matches exactly what the walker will later
+    pull."""
+    plan: list[dict] = []
+    for symbol in symbols:
+        for session_date in dates:
+            start_utc, end_utc = _session_window_utc(session_date)
+            for sub_start, sub_end in split_window(start_utc, end_utc, chunk_seconds):
+                plan.append(
+                    {
+                        "symbol": symbol,
+                        "date": session_date,
+                        "start": _iso_utc(sub_start),
+                        "end": _iso_utc(sub_end),
+                    }
+                )
+    return plan
+
+
+# --- per-chunk checkpoint persistence (resumability plumbing, NOT a dataset) -----------------------
+
+
+class RecorderCheckpointStore:
+    """A per-chunk raw-fetch cache keyed on a chunk's own ``(symbol, date, start, end)`` -- purely
+    resumability plumbing, never a dataset and never research evidence: losing a checkpoint just
+    means the next run re-fetches it (a mild cost, never a correctness problem, since a dataset is
+    ONLY ever finalized from a day whose every chunk succeeded THIS run's walk or a prior one). A
+    checkpoint that fails to parse is treated as a MISS, never a hard crash -- nothing permanent
+    depends on it, unlike a registered dataset."""
+
+    def __init__(self, root: str | Path) -> None:
+        self._root = Path(root)
+
+    @property
+    def root(self) -> Path:
+        return self._root
+
+    def _path(self, symbol: str, session_date: str, start: str, end: str) -> Path:
+        key = hashlib.sha256(f"{symbol}:{session_date}:{start}:{end}".encode("utf-8")).hexdigest()
+        return self._root / f"{key}.json"
+
+    def get(self, symbol: str, session_date: str, start: str, end: str) -> HistoricalWindow | None:
+        path = self._path(symbol, session_date, start, end)
+        if not path.exists():
+            return None
+        try:
+            data = json.loads(path.read_text())
+            trades = tuple(RawTrade(**t) for t in data["trades"])
+            quotes = tuple(RawQuote(**q) for q in data["quotes"])
+            return HistoricalWindow(data["symbol"], trades, quotes)
+        except (OSError, ValueError, TypeError, KeyError):
+            return None  # a bad checkpoint is a MISS -- the chunk is simply re-fetched
+
+    def put(self, symbol: str, session_date: str, start: str, end: str, window: HistoricalWindow) -> None:
+        path = self._path(symbol, session_date, start, end)
+        path.parent.mkdir(parents=True, exist_ok=True)
+        payload = {
+            "symbol": window.symbol,
+            "trades": [dataclasses.asdict(t) for t in window.trades],
+            "quotes": [dataclasses.asdict(q) for q in window.quotes],
+        }
+        path.write_text(json.dumps(payload))
+
+
+def resolve_tick_recorder_checkpoint_dir(dataset_dir_resolved: str) -> str:
+    """``TAPEOLOGY_MICRO_RECORDER_CHECKPOINT_DIR`` if set, else a SIBLING of the caller's
+    already-resolved dataset directory -- the ``resolve_desk_deep_backfill_log_dir``/
+    ``TAPEOLOGY_MICRO_*`` family pattern (goal.md Constraints; deliberately NOT a ``Config``
+    field)."""
+    override = os.environ.get("TAPEOLOGY_MICRO_RECORDER_CHECKPOINT_DIR")
+    if override:
+        return override
+    return str(Path(dataset_dir_resolved).parent / "micro_recorder_checkpoints")
+
+
+def resolve_tick_recorder_log_dir(dataset_dir_resolved: str) -> str:
+    """``TAPEOLOGY_MICRO_RECORDER_LOG_DIR`` if set, else a SIBLING of the caller's already-resolved
+    dataset directory -- the same ``TAPEOLOGY_MICRO_*`` family pattern. The run log persists
+    through ``micro_snapshots.append_run_log``/``read_run_log`` (the SAME shared, non-hash-chained
+    build-run-history utility ``micro_routes.py`` already reuses for the scout/walk-forward
+    sections' own run logs) -- convenience bookkeeping, never a claim of record (that role belongs
+    to the datasets themselves and, for a run's raw fetched content, the checkpoint store above)."""
+    override = os.environ.get("TAPEOLOGY_MICRO_RECORDER_LOG_DIR")
+    if override:
+        return override
+    return str(Path(dataset_dir_resolved).parent / "micro_recorder_runs")
+
+
+# --- the shared walker (mirrors desk_deep_backfill._run_one_chunk's outcome vocabulary) -----------
+
+
+def _group_chunks_by_symbol_day(chunks: list[dict]) -> list[tuple[str, str, list[dict]]]:
+    """Groups an ALREADY-(symbol, date, start)-ordered chunk plan into consecutive
+    ``(symbol, date, [chunks])`` runs -- pure grouping, no I/O. Correct only when fed a plan in
+    ``plan_recorder_chunks``'s own emitted order (its contract, documented there)."""
+    groups: list[tuple[str, str, list[dict]]] = []
+    for chunk in chunks:
+        if groups and (groups[-1][0], groups[-1][1]) == (chunk["symbol"], chunk["date"]):
+            groups[-1][2].append(chunk)
+        else:
+            groups.append((chunk["symbol"], chunk["date"], [chunk]))
+    return groups
+
+
+def _existing_dataset_for_day(
+    dataset_store: DatasetStore, symbol: str, window_start_iso: str, window_end_iso: str
+) -> dict | None:
+    """Whether a dataset already covers this EXACT (symbol, day-window) -- the day-level
+    short-circuit (TC-3): checked BEFORE any chunk of the day is even looked at, so a
+    fully-recorded day costs zero ``DatasetStore.record`` calls, zero vendor calls, and zero
+    checkpoint reads."""
+    records, _errors = dataset_store.list()
+    for meta in records:
+        if (
+            meta["symbol"] == symbol
+            and meta["window_start_utc"] == window_start_iso
+            and meta["window_end_utc"] == window_end_iso
+        ):
+            return meta
+    return None
+
+
+def _fetch_one_planned_chunk(adapter, symbol: str, start_iso: str, end_iso: str) -> HistoricalWindow:
+    """ONE real vendor pull for a single planned chunk, throttled to
+    ``RECORDER_PAGE_BUDGET_PER_MINUTE``. Drains ``iter_historical_chunks`` fully and concatenates
+    whatever it yields into one ``HistoricalWindow`` -- ordinarily exactly one internal sub-window
... [diff_bound] apps/backend/app/research/tick_recorder.py: 431 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_provider_events.py b/apps/backend/tests/test_provider_events.py
new file mode 100644
index 0000000..3f5a7e5
--- /dev/null
+++ b/apps/backend/tests/test_provider_events.py
@@ -0,0 +1,69 @@
+"""``providers/base.py`` -- ``TradeEvent``/``QuoteEvent`` hash-safety (era "The Rapid Microscope"
+iter-8, closing iter-7 audit finding B5).
+
+Both are ``frozen=True`` dataclasses, so Python auto-generates ``__hash__`` over every
+comparable field. With ``conditions`` typed ``list[str] | None``, ``hash(event)`` raised
+``TypeError: unhashable type: 'list'`` the moment a caller populated it with a real value --
+untested until this iteration, because no code path before ``tick_recorder.py`` (this same
+iteration) ever built an event carrying real Card-5.1 preservation data. TC-12."""
+
+from __future__ import annotations
+
+from app.providers.base import QuoteEvent, Side, TradeEvent
+
+
+def test_a_trade_event_with_populated_conditions_stays_hashable():
+    event = TradeEvent(
+        "AAPL", 1.0, 100.0, 10, Side.BUY,
+        conditions=["@", "F"], exchange="Q", tape="C", trade_id=12345,
+    )
+    hash(event)  # must not raise TypeError
+
+
+def test_a_quote_event_with_populated_conditions_stays_hashable():
+    event = QuoteEvent(
+        "AAPL", 1.0, 100.0, 100.05, 200, 300,
+        conditions=["R"], tape="C", bid_exchange="Q", ask_exchange="K",
+    )
+    hash(event)  # must not raise TypeError
+
+
+def test_a_legacy_trade_event_with_conditions_none_hashes_the_same_as_before_this_fix():
+    """TC-12's second half: a legacy (``conditions=None``) event's hash is UNCHANGED by this fix
+    -- proven by constructing the identical event twice and comparing hashes, the behaviour every
+    pre-iteration call site already relied on."""
+    a = TradeEvent("AAPL", 1.0, 100.0, 10, Side.BUY)
+    b = TradeEvent("AAPL", 1.0, 100.0, 10, Side.BUY)
+    assert hash(a) == hash(b)
+
+
+def test_a_legacy_quote_event_with_conditions_none_hashes_consistently():
+    a = QuoteEvent("AAPL", 1.0, 100.0, 100.05, 200, 300)
+    b = QuoteEvent("AAPL", 1.0, 100.0, 100.05, 200, 300)
+    assert hash(a) == hash(b)
+
+
+def test_two_trade_events_differing_only_in_conditions_are_unequal_but_both_hashable():
+    """Hash coarser than equality is legal: excluding ``conditions`` from the hash while keeping
+    it in ``__eq__`` never breaks the hash contract (equal objects must hash equal; the converse
+    is not required)."""
+    a = TradeEvent("AAPL", 1.0, 100.0, 10, Side.BUY, conditions=["@"])
+    b = TradeEvent("AAPL", 1.0, 100.0, 10, Side.BUY, conditions=["F"])
+    assert a != b
+    hash(a)
+    hash(b)
+
+
+def test_trade_event_hash_does_not_depend_on_which_conditions_value_is_carried():
+    """Pins the chosen fix mechanism (project ``conditions`` out of the generated hash, per the
+    iter-8 spec's own wording) rather than e.g. converting it to a hashable tuple: two otherwise-
+    identical events with DIFFERENT conditions lists still hash equal."""
+    a = TradeEvent("AAPL", 1.0, 100.0, 10, Side.BUY, conditions=["@"])
+    b = TradeEvent("AAPL", 1.0, 100.0, 10, Side.BUY, conditions=["F", "K"])
+    assert hash(a) == hash(b)
+
+
+def test_quote_event_hash_does_not_depend_on_which_conditions_value_is_carried():
+    a = QuoteEvent("AAPL", 1.0, 100.0, 100.05, 200, 300, conditions=["R"])
+    b = QuoteEvent("AAPL", 1.0, 100.0, 100.05, 200, 300, conditions=["A", "B"])
+    assert hash(a) == hash(b)
diff --git a/apps/backend/tests/test_tick_recorder.py b/apps/backend/tests/test_tick_recorder.py
new file mode 100644
index 0000000..ac6a4a8
--- /dev/null
+++ b/apps/backend/tests/test_tick_recorder.py
@@ -0,0 +1,818 @@
+"""``tick_recorder.py`` -- Card 5.2, brought forward: the chunked, throttled, resumable tick
+recorder (era "The Rapid Microscope" J-06 step 2, ``docs/rapid-validation-spec.md`` section 7.1).
+
+Everything here runs against planted, scoped stores under ``tmp_path`` with a FAKE adapter --
+never ``apps/backend/.data``, never a real vendor call, never a real credential (100% hermetic
+per this iteration's own scope note). Covers, in order:
+
+  1. Chunk planning purity (TC-1).
+  2. The walk: four-outcome classification, resumability, no-partial-dataset-on-failure
+     (TC-2/TC-3/TC-4/TC-5).
+  3. TR-19 -- the Card-5.1 preservation-field structural gate (TC-8).
+  4. Preservation-field round-trip + content-checksum independence (TC-9).
+  5. The dated ``quote_size_unit`` vendor-rule stamping (TC-10/TC-11).
+  6. The recorder's own throttle (spec section 1: ``RECORDER_PAGE_BUDGET_PER_MINUTE``).
+  7. The published sha256 split rule (spec section 7.3, unchanged -- NOT vault.py's new seal
+     axis, which stays out of scope this iteration).
+  8. Bar pairing through the EXISTING, UNCHANGED ``desk_deep_backfill`` machinery.
+"""
+
+from __future__ import annotations
+
+import hashlib
+import threading
+import time
+from datetime import date, timezone
+from pathlib import Path
+
+import pytest
+
+from app.config import CONFIG
+from app.providers.adapters.base import HistoricalWindow, RawQuote, RawTrade
+from app.providers.base import QuoteEvent, TradeEvent
+from app.research import tick_recorder as tr
+from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
+from app.research.micro_snapshots import read_run_log
+
+
+# --- a hermetic fake adapter -- never the real SDK, never a real vendor call ----------------------
+
+
+class _FakeTickAdapter:
+    """Serves one trade + one quote per requested chunk window, content DERIVED from the chunk's
+    own start epoch so distinct chunks never collide (each recorded dataset gets genuinely
+    distinct content, never an accidental duplicate-content 409). Counts every call -- the seam
+    that proves a reused/checkpointed chunk costs ZERO vendor calls. ``raise_for`` makes
+    ``iter_historical_chunks`` raise for exactly the named ``(symbol, start_iso)`` chunks (TC-4's
+    targeted single-chunk failure)."""
+
+    name = "fake"
+
+    def __init__(self) -> None:
+        self.calls: list[tuple[str, str, str]] = []
+        self.raise_for: set[tuple[str, str]] = set()
+
+    def is_available(self) -> bool:
+        return True
+
+    def warm_symbol_universe(self) -> None:
+        pass
+
+    def iter_historical_chunks(self, symbol, start, end):
+        # Normalized to the SAME "...Z" shape `tick_recorder._iso_utc` emits (a bare tz-aware
+        # `.isoformat()` would print "+00:00" instead, silently missing every `raise_for` lookup).
+        start_iso = start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
+        end_iso = end.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
+        self.calls.append((symbol, start_iso, end_iso))
+        if (symbol, start_iso) in self.raise_for:
+            raise RuntimeError(f"the vendor said no for {symbol} at {start_iso}")
+        epoch = start.timestamp() + 1.0
+        trade = RawTrade(
+            epoch, 100.0 + (epoch % 50), 10,
+            conditions=["@"], exchange="Q", tape="C", trade_id=int(epoch),
+        )
+        quote = RawQuote(
+            epoch, 99.9, 100.1, 200, 300,
+            conditions=["R"], tape="C", bid_exchange="Q", ask_exchange="K",
+        )
+        yield HistoricalWindow(symbol, (trade,), (quote,))
+
+
+@pytest.fixture
+def rec_ctx(tmp_path):
+    tr._reset_recorder_throttle_for_tests()
+    adapter = _FakeTickAdapter()
+    dataset_store = DatasetStore(str(tmp_path / "datasets"))
+    checkpoint_store = tr.RecorderCheckpointStore(str(tmp_path / "checkpoints"))
+    yield adapter, dataset_store, checkpoint_store
+    tr._reset_recorder_throttle_for_tests()
+
+
+# ==================================================================================================
+# 1. Chunk planning: pure, zero I/O (TC-1).
+# ==================================================================================================
+
+
+def test_tc1_the_planner_returns_the_right_count_in_symbol_date_start_order_with_zero_io(tmp_path):
+    # 09:30-16:00 ET = 23400s; chunk_seconds=7800 -> exactly 3 chunks/session -> "3 per symbol-day".
+    plan = tr.plan_recorder_chunks(
+        ["AAPL", "MSFT"], ["2026-06-01", "2026-06-02"], chunk_seconds=7800.0
+    )
+    assert len(plan) == 12  # 2 symbols x 2 dates x 3 chunks/day
+    # Precise (symbol, date, start) ordering: symbol outer, date inner, start ascending within a
+    # day -- exactly the order TC-1 requires, and the same order the walker groups on.
+    seen = [(c["symbol"], c["date"], c["start"]) for c in plan]
+    assert seen == sorted(seen)
+    assert {c["symbol"] for c in plan} == {"AAPL", "MSFT"}
+    assert {c["date"] for c in plan} == {"2026-06-01", "2026-06-02"}
+    from collections import Counter
+
+    counts = Counter((c["symbol"], c["date"]) for c in plan)
+    assert set(counts.values()) == {3}  # each symbol-day contributes exactly 3 chunks
+    assert len(counts) == 4  # 2 symbols x 2 dates
+
+
+def test_tc1_two_symbol_days_yield_exactly_six_chunks_the_literal_tc1_fixture_shape():
+    plan = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01", "2026-06-02"], chunk_seconds=7800.0)
+    assert len(plan) == 6  # 1 symbol x 2 dates x 3 chunks/day = TC-1's own "2 symbol-days ... 6 total"
+
+
+def test_tc1_planning_touches_no_store_and_no_adapter(tmp_path, rec_ctx):
+    adapter, dataset_store, _checkpoint_store = rec_ctx
+    tr.plan_recorder_chunks(["AAPL"], ["2026-06-01"], chunk_seconds=7800.0)
+    assert adapter.calls == []
+    records, _errors = dataset_store.list()
+    assert records == []
+
+
+def test_the_plan_is_clock_free_and_reproducible():
+    first = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01"], chunk_seconds=7800.0)
+    second = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01"], chunk_seconds=7800.0)
+    assert first == second
+
+
+def test_a_short_window_yields_exactly_one_chunk_the_default_recorder_chunk_seconds():
+    # Default RECORDER_CHUNK_SECONDS (900s) against a full 23400s RTH session -> 26 chunks, never 1
+    # -- but a single-day, coarse chunk_seconds proves the "one chunk for a window at/under the
+    # chunk size" boundary the same way `split_window`'s own docstring states.
+    plan = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01"], chunk_seconds=100_000.0)
+    assert len(plan) == 1
+
+
+# ==================================================================================================
+# 2. The walk: outcome classification, resumability, no-partial-dataset-on-failure.
+# ==================================================================================================
+
+
+def test_tc2_a_first_walk_fetches_every_chunk_and_records_one_dataset_per_symbol_day(rec_ctx):
+    adapter, dataset_store, checkpoint_store = rec_ctx
+    chunks = tr.plan_recorder_chunks(
+        ["AAPL", "MSFT"], ["2026-06-01"], chunk_seconds=7800.0
+    )
+    assert len(chunks) == 6
+
+    outcomes = tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)
+
+    assert len(outcomes) == 6
+    assert {o["outcome"] for o in outcomes} == {"fetched"}
+    records, errors = dataset_store.list()
+    assert errors == []
+    assert len(records) == 2  # one per symbol-day
+    assert {r["symbol"] for r in records} == {"AAPL", "MSFT"}
+    for record in records:
+        assert record["checksum"]  # verifying, non-empty
+    # Exactly one outcome row per symbol-day carries the finalizing dataset_id.
+    finalized = [o for o in outcomes if o["dataset_id"]]
+    assert len(finalized) == 2
+    assert {o["dataset_outcome"] for o in finalized} == {"recorded"}
+
+
+def test_tc3_a_second_walk_over_the_same_plan_costs_zero_vendor_calls_and_zero_new_records(rec_ctx):
+    adapter, dataset_store, checkpoint_store = rec_ctx
+    chunks = tr.plan_recorder_chunks(["AAPL", "MSFT"], ["2026-06-01"], chunk_seconds=7800.0)
+    tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)
+    calls_after_first = len(adapter.calls)
+    records_after_first, _ = dataset_store.list()
+
+    outcomes = tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)
+
+    assert {o["outcome"] for o in outcomes} == {"reused"}
+    assert len(adapter.calls) == calls_after_first  # zero new vendor calls
+    records_after_second, _ = dataset_store.list()
+    assert len(records_after_second) == len(records_after_first)  # zero new DatasetStore.record calls
+    assert all(o["dataset_id"] is None for o in outcomes)  # the day short-circuit never finalizes
+
+
+def test_tc4_one_failing_chunk_never_aborts_the_walk_and_leaves_no_partial_dataset(rec_ctx):
+    adapter, dataset_store, checkpoint_store = rec_ctx
+    chunks = tr.plan_recorder_chunks(["AAPL", "MSFT"], ["2026-06-01"], chunk_seconds=7800.0)
+    assert len(chunks) == 6
+    failing_chunk = chunks[3]  # MSFT's first chunk -- "chunk 4 of 6"
+    assert failing_chunk["symbol"] == "MSFT"
+    adapter.raise_for.add((failing_chunk["symbol"], failing_chunk["start"]))
+
+    outcomes = tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)
+
+    assert len(outcomes) == 6  # the walk never aborts -- every planned chunk gets an outcome
+    failed = [o for o in outcomes if o["outcome"] == "failed"]
+    assert len(failed) == 1
+    assert failed[0]["symbol"] == "MSFT" and failed[0]["start"] == failing_chunk["start"]
+    assert "the vendor said no" in failed[0]["detail"]
+    # Chunks 1-3 (AAPL) and 5-6 (MSFT, after the failed one) still complete.
+    msft_outcomes = [o for o in outcomes if o["symbol"] == "MSFT"]
+    assert {o["outcome"] for o in msft_outcomes} == {"failed", "fetched"}
+    assert sum(1 for o in msft_outcomes if o["outcome"] == "fetched") == 2
+
+    records, _errors = dataset_store.list()
+    assert len(records) == 1  # ONLY AAPL's day finalized -- MSFT's has no partial record
+    assert records[0]["symbol"] == "AAPL"
+
+
+def test_tc5_a_resumed_run_only_refetches_the_previously_failed_chunk_and_registers_once(rec_ctx):
+    adapter, dataset_store, checkpoint_store = rec_ctx
+    chunks = tr.plan_recorder_chunks(["AAPL", "MSFT"], ["2026-06-01"], chunk_seconds=7800.0)
+    failing_chunk = chunks[3]
+    adapter.raise_for.add((failing_chunk["symbol"], failing_chunk["start"]))
+    tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)
+    calls_after_first = len(adapter.calls)
+    assert calls_after_first == 6
+
+    adapter.raise_for.clear()  # the transient vendor condition is gone by the time of the retry
+    outcomes = tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)
+
+    # AAPL's day short-circuits entirely (already fully recorded); MSFT's previously-completed
+    # chunks (5, 6) report reused from the checkpoint; only chunk 4 is genuinely re-fetched.
+    aapl_outcomes = [o for o in outcomes if o["symbol"] == "AAPL"]
+    msft_outcomes = [o for o in outcomes if o["symbol"] == "MSFT"]
+    assert {o["outcome"] for o in aapl_outcomes} == {"reused"}
+    assert [o["outcome"] for o in msft_outcomes] == ["fetched", "reused", "reused"]
+    assert len(adapter.calls) == calls_after_first + 1  # exactly one new vendor call
+
+    records, _errors = dataset_store.list()
+    assert len(records) == 2  # MSFT's day is now registered exactly once, alongside AAPL's
+    assert sorted(r["symbol"] for r in records) == ["AAPL", "MSFT"]
+    # A second resume attempt over the now-fully-recorded plan costs zero further vendor calls.
+    tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)
+    assert len(adapter.calls) == calls_after_first + 1
+
+
+def test_an_abort_stops_the_walk_and_keeps_what_it_finished(rec_ctx):
+    adapter, dataset_store, checkpoint_store = rec_ctx
+    chunks = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01", "2026-06-02"], chunk_seconds=7800.0)
+    assert len(chunks) == 6
+    seen = 0
+
+    def _abort() -> bool:
+        return seen >= 2
+
+    def _count(_entry) -> None:
+        nonlocal seen
+        seen += 1
+
+    outcomes = tr.run_tick_recording(
+        chunks, dataset_store, checkpoint_store, adapter, CONFIG,
+        progress=_count, should_abort=_abort,
+    )
+
+    assert len(outcomes) == 2
+    records, _errors = dataset_store.list()
+    assert records == []  # day 1 (2026-06-01) never reached its 3rd chunk -- never finalized
+
+
+def test_events_recorded_carry_the_card_5_1_preservation_fields_verbatim(rec_ctx):
+    adapter, dataset_store, checkpoint_store = rec_ctx
+    chunks = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01"], chunk_seconds=7800.0)
+    tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)
+    records, _errors = dataset_store.list()
+    events = dataset_store.load_events(records[0]["id"])
+    trades = [e for e in events if isinstance(e, TradeEvent)]
+    quotes = [e for e in events if isinstance(e, QuoteEvent)]
+    assert trades and all(t.conditions == ["@"] and t.exchange == "Q" and t.tape == "C" and t.trade_id for t in trades)
+    assert quotes and all(
+        q.conditions == ["R"] and q.tape == "C" and q.bid_exchange == "Q" and q.ask_exchange == "K"
+        for q in quotes
+    )
+
+
+# ==================================================================================================
+# 3. TR-19 -- the Card-5.1 preservation-field structural gate (TC-8).
+# ==================================================================================================
+
+
+class _StrippedTradeEventMissingConditions:
+    """A deliberately-incomplete stand-in dataclass -- SIMULATES the preservation prerequisite
+    being absent without needing to monkeypatch the real, already-shipped ``TradeEvent`` (which
+    would be a fiction: the real class already carries these fields as of iter-7)."""
+
+    __dataclass_fields__ = {
+        name: None for name in ("ticker", "timestamp", "price", "size", "side", "exchange", "tape", "trade_id")
+    }  # deliberately missing "conditions"
+
+
+def test_tc8_the_recorder_refuses_to_record_anything_when_the_preservation_capability_is_absent(rec_ctx):
+    import dataclasses as _dc
+
+    adapter, dataset_store, checkpoint_store = rec_ctx
+    chunks = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01"], chunk_seconds=7800.0)
+
+    # Build a genuinely field-incomplete dataclass (rather than hand-rolling __dataclass_fields__)
+    # so `dataclasses.fields()` -- the real introspection the production check calls -- works.
+    IncompleteTrade = _dc.make_dataclass(
+        "IncompleteTrade",
+        [("ticker", str), ("timestamp", float), ("price", float), ("size", int)],
+    )
+    with pytest.raises(tr.RecorderPreservationCapabilityMissing, match="conditions"):
+        tr.verify_preservation_capability(trade_cls=IncompleteTrade)
+
+    with pytest.raises(tr.RecorderPreservationCapabilityMissing):
+        tr.run_tick_recording(
+            chunks, dataset_store, checkpoint_store, adapter, CONFIG,
+            _trade_cls=IncompleteTrade,
+        )
+    assert adapter.calls == []
+    records, _errors = dataset_store.list()
+    assert records == []
+
+
+def test_tc8_the_real_trade_and_quote_event_classes_satisfy_the_capability_check():
+    tr.verify_preservation_capability()  # must not raise -- the real classes ship the fields
+
+
+# ==================================================================================================
+# 4. Preservation-field round-trip + content-checksum independence (TC-9).
+# ==================================================================================================
+
+
+def test_tc9_preservation_values_round_trip_and_never_perturb_content_identity(rec_ctx):
+    adapter, dataset_store, checkpoint_store = rec_ctx
+    chunks = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01"], chunk_seconds=7800.0)
+    tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)
+    records, _errors = dataset_store.list()
+    meta = records[0]
+
+    # A second, INDEPENDENT store instance re-verifies the SAME checksum on load (the checksum is
+    # unaffected by which preservation values are present -- iter-7 audit finding B1's own proof,
+    # re-exercised here against genuinely recorder-produced content).
+    reloaded = DatasetStore(str(Path(checkpoint_store._root).parent / "datasets")).get(meta["id"])
+    assert reloaded["checksum"] == meta["checksum"]
+
+
+# ==================================================================================================
+# 5. The dated quote_size_unit vendor-rule stamping (TC-10/TC-11).
+# ==================================================================================================
+
+
+def test_tc10_the_dated_rule_stamps_round_lots_before_and_shares_on_or_after_the_cutover():
+    assert tr.quote_size_unit_for_session_date("2025-10-15") == "round_lots"
+    assert tr.quote_size_unit_for_session_date("2025-11-03") == "shares"  # the cutover date itself
+    assert tr.quote_size_unit_for_session_date("2025-11-10") == "shares"
+    assert tr.ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE == "2025-11-03"
+
+
+def test_tc10_recorded_datasets_carry_the_stamped_quote_size_unit_from_the_single_existing_tuple(rec_ctx):
+    from app.research.micro_features import QUOTE_SIZE_UNITS
+
+    adapter, dataset_store, checkpoint_store = rec_ctx
+    pre_chunks = tr.plan_recorder_chunks(["AAPL"], ["2025-10-15"], chunk_seconds=7800.0)
+    post_chunks = tr.plan_recorder_chunks(["MSFT"], ["2025-11-10"], chunk_seconds=7800.0)
+    tr.run_tick_recording(pre_chunks, dataset_store, checkpoint_store, adapter, CONFIG)
+    tr.run_tick_recording(post_chunks, dataset_store, checkpoint_store, adapter, CONFIG)
+
+    records, _errors = dataset_store.list()
+    by_symbol = {r["symbol"]: r for r in records}
+    assert by_symbol["AAPL"]["quote_size_unit"] == "round_lots"
+    assert by_symbol["MSFT"]["quote_size_unit"] == "shares"
+    assert by_symbol["AAPL"]["quote_size_unit"] in QUOTE_SIZE_UNITS
+    assert by_symbol["AAPL"]["schema_basis"] == tr.RECORDER_SCHEMA_BASIS
+
+
+def test_tc11_an_out_of_vocabulary_quote_size_unit_is_still_rejected_by_the_existing_guard(rec_ctx):
+    _adapter, dataset_store, _checkpoint_store = rec_ctx
+    with pytest.raises(ValueError, match="unknown quote_size_unit"):
+        dataset_store.record(
+            symbol="AAPL", source="fixture", source_kind="fixture", source_id="x", split=SPLIT_TRAIN,
+            window_start_utc="2026-06-01T13:30:00Z", window_end_utc="2026-06-01T20:00:00Z",
+            data_feed="sip", epoch_anchor=0.0,
+            events=[TradeEvent("AAPL", 0.0, 100.0, 10)],
+            quote_size_unit="not-a-real-unit",
+        )
+
+
+# ==================================================================================================
+# 6. The recorder's own throttle (spec section 1: RECORDER_PAGE_BUDGET_PER_MINUTE).
+# ==================================================================================================
+
+
+def test_throttle_recorder_fetch_spaces_consecutive_calls(monkeypatch):
+    monkeypatch.setattr(tr, "RECORDER_PAGE_BUDGET_PER_MINUTE", 600)  # 0.1s interval
+    tr._reset_recorder_throttle_for_tests()
+    try:
+        t0 = time.monotonic()
+        tr._throttle_recorder_fetch()
+        t1 = time.monotonic()
+        tr._throttle_recorder_fetch()
+        t2 = time.monotonic()
... [diff_bound] apps/backend/tests/test_tick_recorder.py: 424 more diff lines omitted — Read the file for full detail
```
