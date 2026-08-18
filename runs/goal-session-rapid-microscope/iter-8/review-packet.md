# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

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
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 7 +++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl | 1 +
 2 files changed, 8 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
