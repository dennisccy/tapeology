# Iteration diff (bounded)

Files changed: 9. Shown in full: 8.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_edge_report_compute.py` (62 lines not shown)

```diff
diff --git a/apps/backend/app/research/edge_report.py b/apps/backend/app/research/edge_report.py
index c066ef3..c532175 100644
--- a/apps/backend/app/research/edge_report.py
+++ b/apps/backend/app/research/edge_report.py
@@ -78,6 +78,7 @@ from .store import JournalStore
 
 __all__ = [
     "EdgeReportError",
+    "EdgeReportComputeCancelled",
     "run_edge_report",
     "run_strategy_comparison_report",
     "peek_strategy_comparison_report",
@@ -107,6 +108,18 @@ class EdgeReportError(Exception):
     backtest ended non-``done``. Explicit; nothing is written to ``--out``."""
 
 
+class EdgeReportComputeCancelled(Exception):
+    """era-fast_wall J-04 — raised by ``_split_cells`` when an actively-supplied ``should_abort()``
+    hook returns ``True`` between dataset x strategy pairs (the cooperative-cancel seam
+    ``run_strategy_comparison_report`` threads down from an operator/CLI trigger). Propagates
+    UNCHANGED through ``EdgeReportCache.get_or_compute``/``compute_and_publish`` — both publish
+    ONLY after their ``compute_fn`` returns normally (see those methods' own docstrings), so a
+    cancelled run publishes NOTHING to the report cache, by construction, with no change needed to
+    either method's body. Caught by ``edge_report_compute.EdgeReportComputeManager``'s worker
+    thread at its outer boundary to resolve the job's snapshot to ``state: "cancelled"`` rather
+    than ``"failed"`` (the NOTES' suggested mechanism)."""
+
+
 # --- reused computation: ONE backtest per dataset, via the EXISTING runner ----------------------
 
 
@@ -335,6 +348,60 @@ def _cell_key(cell: dict) -> tuple:
     return (cell["strategy_id"], cell["band_class"], cell["band_side"], cell["reaction"], cell["feed"])
 
 
+# --- era-fast_wall J-04: the operator-run compute's progress/cancel seam --------------------------
+# ``_count_eligible_pairs`` and ``_ProgressReporter`` exist ONLY to report progress; neither
+# changes what ``_split_cells`` computes. ``_count_eligible_pairs`` reuses ``_dataset_event`` (the
+# SAME join ``_split_cells``'s own loop below re-checks per dataset — a one-line filter repeated,
+# never a second join) purely to pre-size the progress snapshot's ``backtests_total`` BEFORE the
+# loop starts (both splits' eligible-pair counts are known only once ``compute_setups`` has run).
+
+
+def _count_eligible_pairs(datasets: list[dict], events: list[dict]) -> int:
+    """The number of (dataset, strategy) backtest pairs ``_split_cells`` will actually run for
+    ``datasets`` — every dataset resolving an owning, classified event, times the three registered
+    strategies (``_ALL_STRATEGY_IDS``)."""
+    eligible = 0
+    for dataset_meta in datasets:
+        event = _dataset_event(dataset_meta, events)
+        if event is not None and event["band"]["class"] is not None:
+            eligible += len(_ALL_STRATEGY_IDS)
+    return eligible
+
+
+class _ProgressReporter:
+    """Wraps a caller-supplied ``progress`` dict-patch sink with running totals SHARED across both
+    the train and hold-out ``_split_cells`` calls (one instance is built once per
+    ``_compute_strategy_comparison_report`` call and threaded into both), so the whole run's
+    ``backtests_done``/``backtests_from_cache`` counts up monotonically across splits rather than
+    resetting when the SECOND ``_split_cells`` call starts. Each sink call carries an ``"event"``
+    key (``"total"``/``"pair_started"``/``"pair_done"``) so a consumer (the CLI printer, the compute
+    manager) can distinguish a start-of-run announcement from a per-pair update; the manager strips
+    the key before merging (the served snapshot's ``progress`` sub-dict never carries it — see
+    ``edge_report_compute.py``)."""
+
+    def __init__(self, sink, total: int) -> None:
+        self._sink = sink
+        self._done = 0
+        self._from_cache = 0
+        self._sink({
+            "event": "total", "phase": "backtests", "backtests_total": total,
+            "backtests_done": 0, "backtests_from_cache": 0, "current": None,
+        })
+
+    def start_pair(self, dataset_id: str, strategy_id: str) -> None:
+        self._sink({
+            "event": "pair_started",
+            "current": {"dataset_id": dataset_id, "strategy_id": strategy_id},
+        })
+
+    def pair_done(self) -> None:
+        self._done += 1
+        self._sink({
+            "event": "pair_done", "backtests_done": self._done,
+            "backtests_from_cache": self._from_cache, "current": None,
+        })
+
+
 def _split_cells(
     jobs: BacktestJobManager,
     store: JournalStore,
@@ -343,6 +410,9 @@ def _split_cells(
     datasets: list[dict],
     events: list[dict],
     config: Config,
+    *,
+    reporter: "_ProgressReporter | None" = None,
+    should_abort=None,
 ) -> list[dict]:
     """One split's (train or hold-out) cells: for every dataset that resolves an owning event with
     a genuinely inherited class (an unclassified ``class: null`` band is honestly excluded — there
@@ -354,7 +424,15 @@ def _split_cells(
     already use) before the ONE shared ``_aggregate`` call, so a pooled cell's ``win_rate``/
     ``max_drawdown_r`` reflect a genuine chronological trade sequence — never scan-order/dataset-id
     happenstance (max_drawdown_r is peak-to-trough IN TRADE ORDER; summing already-aggregated
-    numbers cannot recover that without the raw, correctly-ordered trade list)."""
+    numbers cannot recover that without the raw, correctly-ordered trade list).
+
+    era-fast_wall J-04: ``reporter``/``should_abort`` (both optional, default ``None`` — the exact
+    pre-J-04 loop when omitted) are the ONLY additions to this loop's body — the pooling/ordering/
+    aggregation code below is byte-for-byte untouched. ``should_abort`` (a zero-arg callable) is
+    checked ONCE per pair, strictly BEFORE that pair's ``_run_backtest`` call — cooperative
+    cancellation observed BETWEEN dataset x strategy pairs, never mid-backtest — and raises
+    ``EdgeReportComputeCancelled`` the instant it returns ``True``, so an already-completed pair's
+    trades are never discarded and a not-yet-started pair never begins."""
     pools: dict[tuple, dict] = {}
     for dataset_meta in datasets:
         event = _dataset_event(dataset_meta, events)
@@ -362,10 +440,16 @@ def _split_cells(
             continue
         feed = dataset_meta["data_feed"]
         for strategy_id in _ALL_STRATEGY_IDS:
+            if should_abort is not None and should_abort():
+                raise EdgeReportComputeCancelled()
+            if reporter is not None:
+                reporter.start_pair(dataset_meta["id"], strategy_id)
             result = _run_backtest(
                 jobs, store, dataset_store, dataset_meta["id"],
                 strategy_id=strategy_id, profile=PROFILE_DEFAULT, bar_store=bar_store,
             )
+            if reporter is not None:
+                reporter.pair_done()
             key = (strategy_id, event["band"]["class"], event["band"]["side"], event["reaction"], feed)
             pool = pools.setdefault(key, {"trades": [], "null_trades": [], "dataset_ids": []})
             anchor = dataset_meta.get("epoch_anchor") or 0.0
@@ -454,6 +538,11 @@ def run_strategy_comparison_report(
     config: Config,
     *,
     cache: EdgeReportCache | None = None,
+    force: bool = False,
+    progress=None,
+    should_abort=None,
+    sub_cache=None,
+    workers=None,
 ) -> dict:
     """The always-recompute-or-serve-through-a-cache entry point for the 3-way strategy-comparison
     report (era-5B J-04). See ``_compute_strategy_comparison_report`` below for the full algorithm
@@ -474,13 +563,39 @@ def run_strategy_comparison_report(
     supplied, this function serves ``_compute_strategy_comparison_report``'s output VERBATIM
     through it: the cache never re-derives a cell, a measurement, or a null baseline — a miss
     recomputes byte-identically through the SAME one function below (single source of truth; no
-    second computation path, anywhere)."""
+    second computation path, anywhere).
+
+    era-fast_wall J-04: five ADDITIVE keyword-only params for the operator-run compute
+    (``edge_report_compute.EdgeReportComputeManager`` and its CLI warmer are the first genuine
+    callers) — every default reproduces this function's EXACT pre-J-04 behaviour:
+
+      * ``force`` (default ``False``) — ``False`` keeps dispatching through ``cache.
+        get_or_compute`` exactly as today; ``True`` dispatches through the ALREADY-SHIPPED
+        ``cache.compute_and_publish`` (J-01) instead, always recomputing and republishing even
+        over a warm key. Irrelevant when ``cache is None`` (there is nothing to force through).
+      * ``progress``/``should_abort`` thread straight down to ``_split_cells``'s existing
+        per-dataset x strategy loop (see that function's own docstring) as an optional
+        reporting/cooperative-cancellation seam — the loop's own ordering/pooling/aggregation
+        code is untouched. A ``should_abort`` that fires raises ``EdgeReportComputeCancelled``,
+        which propagates UNCHANGED through ``cache.get_or_compute``/``compute_and_publish``
+        (both publish ONLY after ``compute_fn`` returns normally) — a cancelled run publishes
+        NOTHING, by construction, with zero change to either cache method's body.
+      * ``sub_cache``/``workers`` are ACCEPTED this iteration but currently INERT (a logged
+        assumption — see the dev handoff): every compute this iteration triggers runs strictly
+        sequentially regardless of their value. J-05's resumable/parallel sweep (the
+        ``EdgeReportBacktestCache`` per-pair sub-cache + the ``ProcessPoolExecutor`` provider)
+        gives them real effect; their signature exists NOW so J-05 adds no further parameter
+        churn to this function."""
 
     def compute() -> dict:
-        return _compute_strategy_comparison_report(store, dataset_store, bar_store, config)
+        return _compute_strategy_comparison_report(
+            store, dataset_store, bar_store, config, progress=progress, should_abort=should_abort,
+        )
 
     if cache is None:
         return compute()
+    if force:
+        return cache.compute_and_publish(dataset_store, config, compute)
     return cache.get_or_compute(dataset_store, config, compute)
 
 
@@ -491,6 +606,7 @@ def peek_strategy_comparison_report(
     config: Config,
     *,
     cache: EdgeReportCache,
+    compute=None,
 ) -> dict:
     """The GET-path's EXCLUSIVE entry point (era-fast_wall J-01) — ``routes.get_edge_report`` calls
     ONLY this, never ``run_strategy_comparison_report``, so opening ``/structure`` (or any GET, or
@@ -508,8 +624,14 @@ def peek_strategy_comparison_report(
         never_calls_a_compute_triggering_cache_method``): a warm key returns the cached report
         VERBATIM; a cold key returns the honest not-computed payload (``status: "not_computed"``,
         the canonical ``EDGE_REPORT_NOT_COMPUTED_DETAIL``, ``dataset_count``, ``register`` read
-        from ``backtests.REGISTER`` — never a restated literal — and ``compute: null``, since no
-        compute manager exists until J-04)."""
+        from ``backtests.REGISTER`` — never a restated literal — and ``compute``).
+
+    era-fast_wall J-04: ``compute`` (optional, default ``None`` — the EXACT J-01 placeholder every
+    existing caller still gets) is embedded VERBATIM as the payload's own ``compute`` field — this
+    function never re-derives or inspects it. The caller (``routes.get_edge_report``) passes
+    ``registry.edge_report_compute.snapshot()`` — the SAME snapshot ``GET /research/edge-report/
+    compute`` itself serves, so the two are byte-identical in shape by construction (one owner, one
+    read, two callers)."""
     records = _verified_records(dataset_store)
     if not records:
         return _compute_strategy_comparison_report(store, dataset_store, bar_store, config)
@@ -521,12 +643,18 @@ def peek_strategy_comparison_report(
         "detail": EDGE_REPORT_NOT_COMPUTED_DETAIL,
         "dataset_count": len(records),
         "register": REGISTER,
-        "compute": None,
+        "compute": compute,
     }
 
 
 def _compute_strategy_comparison_report(
-    store: JournalStore, dataset_store: DatasetStore, bar_store: BarStore, config: Config
+    store: JournalStore,
+    dataset_store: DatasetStore,
+    bar_store: BarStore,
+    config: Config,
+    *,
+    progress=None,
+    should_abort=None,
 ) -> dict:
     """The ONE computer of the 3-way strategy-comparison report (era-5B J-04; renamed from
     ``run_strategy_comparison_report`` at era-5B J-08 — see that function's own docstring for why:
@@ -536,7 +664,14 @@ def _compute_strategy_comparison_report(
     into per strategy x class x side x reaction x feed cells. Raises ``EdgeReportError`` for a
     dishonest state (the identical ``_split_datasets`` integrity discipline ``run_edge_report``
     uses) — nothing is written by the CALLER in that case. Strictly read-only: promotes nothing,
-    appends no ledger row, moves no champion pointer (see the module docstring)."""
+    appends no ledger row, moves no champion pointer (see the module docstring).
+
+    era-fast_wall J-04: ``progress``/``should_abort`` (both optional, default ``None`` — the exact
+    pre-J-04 body when omitted) thread into BOTH ``_split_cells`` calls below through ONE shared
+    ``_ProgressReporter`` (never a separate reporter per split — its running totals must span both
+    splits). ``backtests_total`` is sized ONCE, right after ``events`` resolves (the earliest point
+    both splits' eligible-pair counts are knowable), via ``_count_eligible_pairs`` — never inside
+    ``_split_cells`` itself, so that function's own loop stays untouched."""
     jobs = BacktestJobManager(store, config)
     train_datasets = _split_datasets(dataset_store, SPLIT_TRAIN)
     holdout_datasets = _split_datasets(dataset_store, SPLIT_HOLDOUT)
@@ -549,8 +684,19 @@ def _compute_strategy_comparison_report(
     if train_datasets or holdout_datasets:
         events = compute_setups(bar_store, config)["events"]
 
-    train_cells = _split_cells(jobs, store, dataset_store, bar_store, train_datasets, events, config)
-    holdout_cells = _split_cells(jobs, store, dataset_store, bar_store, holdout_datasets, events, config)
+    reporter = None
+    if progress is not None:
+        total = _count_eligible_pairs(train_datasets, events) + _count_eligible_pairs(holdout_datasets, events)
+        reporter = _ProgressReporter(progress, total)
+
+    train_cells = _split_cells(
+        jobs, store, dataset_store, bar_store, train_datasets, events, config,
+        reporter=reporter, should_abort=should_abort,
+    )
+    holdout_cells = _split_cells(
+        jobs, store, dataset_store, bar_store, holdout_datasets, events, config,
+        reporter=reporter, should_abort=should_abort,
+    )
 
     return {
         "register": REGISTER,
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index dc09e44..e6c25fc 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -51,6 +51,7 @@ from .bars import (
 )
 from .edge_report import EdgeReportError, peek_strategy_comparison_report
 from .edge_report_cache import EdgeReportCache, resolve_cache_db_path
+from .edge_report_compute import EdgeReportComputeManager
 from .levels import compute_levels
 from .setups import BROKE, CHOPPED, REJECTED, compute_setups, enrich_with_tape_timeline
 from .tradability import compute_tradability
@@ -214,6 +215,16 @@ class BarRecordRequest(BaseModel):
     end: str
 
 
+class EdgeReportComputeRequest(BaseModel):
+    """Body for ``POST /research/edge-report/compute`` (era-fast_wall J-04) — the operator/CLI
+    "run this now" trigger. ``force`` (default ``False``) recomputes even over an already-warm
+    cache key and republishes (``EdgeReportCache.compute_and_publish`` — J-01's already-shipped
+    write half); the default dispatches through the existing ``get_or_compute`` (a warm key serves
+    instantly with zero recompute; a cold key computes once)."""
+
+    force: bool = False
+
+
 class ReviewRequest(BaseModel):
     """Body for ``POST /research/thesis/{id}/review`` (J-57). ``mistake_tags`` is the user-CONFIRMED
     tag list (distinct from the machine-SUGGESTED tags); ``note`` is the optional free text (REQUIRED
@@ -248,6 +259,13 @@ class ResearchRegistry:
         # pattern verbatim: cancellable worker threads OFF the event loop, persistence through the
         # SAME single writer queue, in-flight jobs honestly lost on restart (never silently done).
         self._backtest_jobs = BacktestJobManager(store, config)
+        # The edge-report compute manager (era-fast_wall J-04) — a single-flight, cancellable,
+        # progress-reporting background job around ``run_strategy_comparison_report``. Unlike
+        # ``_study_jobs``/``_backtest_jobs`` it needs no ``store``/``config`` at construction time
+        # (every ``trigger()`` call takes its store/dataset_store/bar_store/config/cache
+        # explicitly) — process-scoped, in-memory-only bookkeeping, honestly lost on restart, never
+        # a research value.
+        self._edge_report_compute = EdgeReportComputeManager()
 
     @property
     def store(self) -> JournalStore:
@@ -261,6 +279,10 @@ class ResearchRegistry:
     def backtest_jobs(self) -> BacktestJobManager:
         return self._backtest_jobs
 
+    @property
+    def edge_report_compute(self) -> EdgeReportComputeManager:
+        return self._edge_report_compute
+
     @property
     def config(self) -> Config:
         return self._config
@@ -2124,10 +2146,70 @@ def get_edge_report(
     keeps the pre-J-01 O(1), zero-backtest full-report shape. A dataset failing integrity
     verification aborts the whole report with an explicit 500 (the ``create_backtest``/
     ``EdgeReportError`` precedent) — partial results are never served, and never cached. An
-    all-empty or all-``insufficient_sample`` WARM report is a valid 200, never an error."""
+    all-empty or all-``insufficient_sample`` WARM report is a valid 200, never an error.
+
+    era-fast_wall J-04: the not-computed payload's ``compute`` field is now the registry's compute
+    manager's OWN current/last snapshot (``registry.edge_report_compute.snapshot()`` — replacing
+    J-01's always-``None`` placeholder) — the SAME snapshot ``GET /research/edge-report/compute``
+    itself serves (TC-8), read here through the SAME already-injected ``registry``, no second
+    store/manager construction path."""
     try:
         return peek_strategy_comparison_report(
-            registry.store, dataset_store, bar_store, registry.config, cache=cache
+            registry.store, dataset_store, bar_store, registry.config, cache=cache,
+            compute=registry.edge_report_compute.snapshot(),
         )
     except EdgeReportError as exc:
         raise HTTPException(status_code=500, detail=f"edge report could not complete: {exc}")
+
+
+# --- The operator-run compute (era-fast_wall J-04) — three subpaths of the section above ---------
+# ``POST /research/edge-report/compute`` (single-flight trigger), ``GET /research/edge-report/
+# compute`` (poll the snapshot), ``POST /research/edge-report/compute/cancel`` (409 when idle).
+# Resolved through the SAME FOUR existing dependency seams ``get_edge_report`` above already uses
+# (``get_registry``/``get_dataset_store``/``get_bar_store``/``get_edge_report_cache``) — no second
+# store/cache construction path anywhere. These are SUBPATHS of ``/edge-report``, so non-GET verbs
+# on ``/research/edge-report`` itself remain structurally unaffected (FastAPI's default 405 stands
+# — no handler exists for them, exactly as before this iteration). No MCP tool is added for this
+# surface (the critical "No MCP write surface" anti-goal) — ``app/mcp/__init__.py`` is untouched.
+
+
+@router.post("/edge-report/compute")
+def trigger_edge_report_compute(
+    body: EdgeReportComputeRequest,
+    registry: ResearchRegistry = Depends(get_registry),
+    dataset_store: DatasetStore = Depends(get_dataset_store),
+    bar_store: BarStore = Depends(get_bar_store),
+    cache: EdgeReportCache = Depends(get_edge_report_cache),
+) -> dict:
+    """Start the single-flight edge-report compute job, or — if one is already running — return it
+    UNCHANGED (``started: False``, never a second concurrent job). Returns
+    ``{"started": bool, "compute": <snapshot>}``; the actual sweep runs on a background worker
+    thread, off this request (``EdgeReportComputeManager.trigger`` — the ``create_backtest``/
+    ``jobs.start`` precedent), so this route returns immediately regardless of how long the sweep
+    takes."""
+    return registry.edge_report_compute.trigger(
+        registry.store, dataset_store, bar_store, registry.config, cache, force=body.force,
+    )
+
+
+@router.get("/edge-report/compute")
+def get_edge_report_compute(registry: ResearchRegistry = Depends(get_registry)) -> dict | None:
+    """The compute job's current/last snapshot, served VERBATIM — or ``null`` if no compute has
+    ever run this process. The SAME snapshot embedded as the not-computed edge-report payload's
+    ``compute`` field (TC-8) — one owner (``EdgeReportComputeManager``), one read
+    (``registry.edge_report_compute.snapshot()``), two callers."""
+    return registry.edge_report_compute.snapshot()
+
+
+@router.post("/edge-report/compute/cancel")
+def cancel_edge_report_compute(registry: ResearchRegistry = Depends(get_registry)) -> dict:
+    """Cancel the in-flight edge-report compute (cooperative — observed between dataset x strategy
+    pairs; a cancelled run publishes NOTHING to the edge-report cache, by construction — see
+    ``EdgeReportComputeCancelled``'s own docstring). ``409`` when idle (no job has ever run, or the
+    last job already reached a terminal state) — mirrors ``cancel_backtest``'s own 409-when-
+    terminal shape."""
+    snapshot = registry.edge_report_compute.snapshot()
+    if snapshot is None or snapshot["state"] != "running":
+        raise HTTPException(status_code=409, detail="no edge-report compute is currently running")
+    registry.edge_report_compute.cancel()
+    return {"cancelling": True}
diff --git a/apps/backend/tests/test_edge_report.py b/apps/backend/tests/test_edge_report.py
index 9ae30f5..525e9c5 100644
--- a/apps/backend/tests/test_edge_report.py
+++ b/apps/backend/tests/test_edge_report.py
@@ -1086,3 +1086,243 @@ def test_peek_source_never_calls_a_compute_triggering_cache_method():
     assert "cache.lookup(" in src
     for forbidden in ("cache.get_or_compute(", "cache.compute_and_publish("):
         assert forbidden not in src
+
+
+# ==================================================================================================
+# era-fast_wall J-04 — the operator-run compute's five additive keyword-only hooks on
+# ``run_strategy_comparison_report`` (``force``/``progress``/``should_abort``/``sub_cache``/
+# ``workers``). Every test ABOVE this marker calls the function with every new kwarg left at its
+# default and stays green UNMODIFIED — proof by construction that the unused-default path is
+# byte-for-byte untouched (TC-14a's "default path" leg). This section proves the hooks are
+# genuinely wired, not decorative (TC-14), and ``peek_strategy_comparison_report``'s new
+# ``compute=`` passthrough.
+# ==================================================================================================
+
+from app.research.edge_report import EdgeReportComputeCancelled  # noqa: E402
+
+
+def test_progress_and_should_abort_supplied_but_unused_is_byte_identical_to_the_default_path(
+    tmp_path, store, scan_bar_store, scan_config
+):
+    """TC-14a: the hooked path (every new kwarg actively supplied but never triggered to abort)
+    produces a report byte-identical to the pre-existing default path — on the REAL, non-degenerate
+    3-cell synthetic-scan-join shape (the iter-4 lesson: never merely the vacuous empty case)."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache_a = EdgeReportCache(str(tmp_path / "cache-a.db"))
+    cache_b = EdgeReportCache(str(tmp_path / "cache-b.db"))
+
+    progress_events: list[dict] = []
+
+    def _progress(patch: dict) -> None:
+        progress_events.append(patch)
+
+    default_path = run_strategy_comparison_report(
+        store, dataset_store, scan_bar_store, scan_config, cache=cache_a,
+    )
+    hooked_path = run_strategy_comparison_report(
+        store, dataset_store, scan_bar_store, scan_config, cache=cache_b,
+        progress=_progress, should_abort=lambda: False, sub_cache=object(), workers=7,
+    )
+
+    assert json.dumps(default_path, sort_keys=True) == json.dumps(hooked_path, sort_keys=True)
+    assert len(default_path["train"]["cells"]) == 3  # non-degenerate: the real 3-cell shape
+    assert progress_events  # the hook was genuinely CALLED, not merely accepted and ignored
+
+
+def test_should_abort_that_fires_mid_run_is_observably_different_and_publishes_nothing(
+    tmp_path, store, scan_bar_store, scan_config
+):
+    """TC-14b — the non-vacuous proof (the iter-3 lesson): a ``should_abort`` that DOES fire
+    between pairs changes the observable outcome (raises, publishes nothing) versus one that never
+    fires (a normal report, proven above) — never a decorative no-op that would also pass if
+    silently ignored."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+
+    calls = {"n": 0}
+
+    def _should_abort() -> bool:
+        calls["n"] += 1
+        return calls["n"] > 1  # fires at the top of the 2nd pair — never before the 1st
+
+    with pytest.raises(EdgeReportComputeCancelled):
+        run_strategy_comparison_report(
+            store, dataset_store, scan_bar_store, scan_config, cache=cache, should_abort=_should_abort,
+        )
+
+    records, errors = dataset_store.list()
+    assert errors == []
+    assert cache.lookup(records, scan_config) is None  # nothing was EVER published (TC-3's premise)
+
+    # Cooperative — checked strictly BETWEEN pairs, never mid-backtest: the FIRST pair (v1, the
+    # registration order's first strategy) genuinely completed and was persisted as a real backtest
+    # record before the second should_abort() check stopped the loop before structure_tape.
+    backtests = store.list_backtests(limit=10)
+    assert len(backtests) == 1
+    assert backtests[0].payload["strategy_id"] == STRATEGY_V1_ID
+    assert backtests[0].payload["status"] == STATUS_DONE
+
+
+def test_force_true_dispatches_through_compute_and_publish(
+    tmp_path, store, scan_bar_store, scan_config, monkeypatch
+):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+
+    calls = []
+    real = cache.compute_and_publish
+
+    def _spy(*args, **kwargs):
+        calls.append(1)
+        return real(*args, **kwargs)
+
+    monkeypatch.setattr(cache, "compute_and_publish", _spy)
+
+    run_strategy_comparison_report(
+        store, dataset_store, scan_bar_store, scan_config, cache=cache, force=True,
+    )
+
+    assert len(calls) == 1
+
+
+def test_force_false_default_still_dispatches_through_get_or_compute(
+    tmp_path, store, scan_bar_store, scan_config, monkeypatch
+):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+
+    calls = []
+    real = cache.get_or_compute
+
+    def _spy(*args, **kwargs):
+        calls.append(1)
+        return real(*args, **kwargs)
+
+    monkeypatch.setattr(cache, "get_or_compute", _spy)
+
+    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
+
+    assert len(calls) == 1
+
+
+def test_force_true_recomputes_over_an_already_warm_key(
+    tmp_path, store, scan_bar_store, scan_config, monkeypatch
+):
+    """TC-5, at the module level: a call-counting spy on the underlying compute path records a
+    FRESH call even though the key is already warm."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
+
+    calls = []
+    real_compute = edge_report._compute_strategy_comparison_report
+
+    def _counting_compute(*args, **kwargs):
+        calls.append(1)
+        return real_compute(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report, "_compute_strategy_comparison_report", _counting_compute)
+
+    run_strategy_comparison_report(
+        store, dataset_store, scan_bar_store, scan_config, cache=cache, force=True,
+    )
+
+    assert len(calls) == 1
+
+
+def test_force_default_over_the_same_warm_key_never_recomputes(
+    tmp_path, store, scan_bar_store, scan_config, monkeypatch
+):
+    """TC-6, at the module level: the mirror of the test immediately above — zero additional calls
+    without ``force``."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
+
+    calls = []
+    real_compute = edge_report._compute_strategy_comparison_report
+
+    def _counting_compute(*args, **kwargs):
+        calls.append(1)
+        return real_compute(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report, "_compute_strategy_comparison_report", _counting_compute)
+
+    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
+
+    assert calls == []
+
+
+def test_a_dataset_integrity_error_still_raises_with_should_abort_and_progress_supplied(
+    tmp_path, store, scan_bar_store, scan_config
+):
+    """No new integrity-bypass path: supplying the new hooks changes nothing about the existing
+    store-integrity discipline — a corrupt dataset still aborts the WHOLE report explicitly."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    meta = _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    path = tmp_path / "datasets" / f"{meta['id']}.json"
+    data = json.loads(path.read_text())
+    data["record"]["meta"]["checksum"] = "0" * 64  # tamper
+    path.write_text(json.dumps(data))
+
+    with pytest.raises(EdgeReportError, match="integrity"):
+        run_strategy_comparison_report(
+            store, dataset_store, scan_bar_store, scan_config,
+            progress=lambda patch: None, should_abort=lambda: False,
+        )
+
+
+# --- ``peek_strategy_comparison_report``'s new ``compute=`` passthrough (era-fast_wall J-04) ------
+
+
+def test_peek_compute_field_defaults_to_none_exactly_as_before(
+    tmp_path, store, scan_bar_store, scan_config
+):
+    """No caller passes ``compute=`` yet reads a ``null`` — the unchanged J-01 behavior, still true
+    with the new keyword-only parameter merely ADDED (default-preserving)."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+
+    result = peek_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
+
+    assert result["compute"] is None
+
+
+def test_peek_compute_field_embeds_whatever_is_passed_verbatim(
+    tmp_path, store, scan_bar_store, scan_config
+):
+    """TC-8's shape: ``peek_strategy_comparison_report`` never re-derives the snapshot — it embeds
+    EXACTLY what its caller (the route, reading ``registry.edge_report_compute.snapshot()``) hands
+    it, byte-for-byte."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    snapshot = {
+        "id": "abc123", "state": "running", "force": False,
+        "started_utc": "2026-01-01T00:00:00.000000Z", "finished_utc": None, "error": None,
+        "progress": {"phase": "backtests", "backtests_total": 3, "backtests_done": 1,
+                     "backtests_from_cache": 0, "current": None},
+    }
+
+    result = peek_strategy_comparison_report(
+        store, dataset_store, scan_bar_store, scan_config, cache=cache, compute=snapshot,
+    )
+
+    assert result["compute"] == snapshot
+
+
+def test_run_strategy_comparison_report_source_documents_the_five_new_hooks():
+    """A coherence guard: the five new keyword-only params exist textually on the function's OWN
+    signature (never silently absorbed into ``**kwargs`` or dropped)."""
+    import inspect
+
+    src = inspect.getsource(edge_report.run_strategy_comparison_report)
+    for hook in ("force: bool = False", "progress=None", "should_abort=None", "sub_cache=None", "workers=None"):
+        assert hook in src
diff --git a/apps/backend/tests/test_edge_report_api.py b/apps/backend/tests/test_edge_report_api.py
index abe5637..f9c2b61 100644
--- a/apps/backend/tests/test_edge_report_api.py
+++ b/apps/backend/tests/test_edge_report_api.py
@@ -10,6 +10,7 @@ from __future__ import annotations
 
 import json
 import os
+import threading
 import time
 
 import pytest
@@ -19,7 +20,7 @@ from app.config import CONFIG
 from app.main import app, manager
 from app.research.bars import BarStore
 from app.research.datasets import DatasetStore
-from app.research.edge_report import REGISTER, run_strategy_comparison_report
+from app.research.edge_report import EdgeReportComputeCancelled, REGISTER, run_strategy_comparison_report
 from app.research.edge_report_cache import EdgeReportCache
 from app.research.routes import ResearchRegistry, get_bar_store, set_registry
 from app.research.store import JournalStore
@@ -34,6 +35,7 @@ def ctx(tmp_path, monkeypatch):
     set_registry(registry)
     with TestClient(app) as c:
         yield c, store, tmp_path
+    registry.edge_report_compute.join_all(timeout=10.0)
     registry.backtest_jobs.join_all(timeout=10.0)
     for ticker in list(manager._engines.keys()):
         manager.stop(ticker)
@@ -321,3 +323,289 @@ def test_edge_report_route_cache_db_lives_hermetically_beside_the_test_dataset_d
     response = client.get("/research/edge-report")
     assert response.status_code == 200
     assert (tmp_path / "edge_report_cache.db").exists()
+
+
+# ==================================================================================================
+# era-fast_wall J-04 — the operator-run compute: POST /research/edge-report/compute,
+# GET /research/edge-report/compute, POST /research/edge-report/compute/cancel. The manager's OWN
+# single-flight/cancel/progress/failed-state mechanics are unit-tested in isolation (a FAKE compute
+# function, threading-free determinism) in test_edge_report_compute.py; this section proves the
+# HTTP wiring — dependency injection, status codes, and the not-computed payload's ``compute``
+# field mirroring GET .../compute byte-for-byte (TC-8).
+# ==================================================================================================
+
+
+def _record_reference_dataset(client):
+    recorded = client.post(
+        "/research/datasets",
+        json={
+            "source_kind": "reference",
+            "split": "train",
+            "start": "2026-06-09T17:00:00Z",
+            "end": "2026-06-09T17:00:30Z",
+        },
+    )
+    assert recorded.status_code == 200, recorded.text
+    return recorded.json()["dataset"]
+
+
+def _poll_compute_until_terminal(client, attempts=400):
+    for _ in range(attempts):
+        payload = client.get("/research/edge-report/compute").json()
+        if payload is not None and payload["state"] != "running":
+            return payload
+        time.sleep(0.05)
+    raise AssertionError("edge-report compute never reached a terminal state")
+
+
+def test_get_compute_is_null_before_anything_has_ever_triggered(ctx):
+    client, _store, _tmp_path = ctx
+    assert client.get("/research/edge-report/compute").json() is None
+
+
+def test_cancel_while_idle_is_409(ctx):
+    """TC-4."""
+    client, _store, _tmp_path = ctx
+    response = client.post("/research/edge-report/compute/cancel")
+    assert response.status_code == 409
+
+
+def test_trigger_on_an_empty_registry_reaches_done_fast_and_get_compute_agrees(ctx):
+    """TC-1 — the O(1) empty-registry leg (zero backtests, deterministic and fast)."""
+    client, _store, _tmp_path = ctx
+    response = client.post("/research/edge-report/compute", json={})
+    assert response.status_code == 200
+    body = response.json()
+    assert body["started"] is True
+    assert body["compute"]["state"] == "running"
+    assert body["compute"]["force"] is False
+
+    terminal = _poll_compute_until_terminal(client)
+    assert terminal["state"] == "done"
+    assert terminal["error"] is None
+    assert terminal["finished_utc"] is not None
+
+    report = client.get("/research/edge-report").json()
+    assert "status" not in report  # now a genuine warm report, never the not-computed shape
+    assert report["train"]["cells"] == []
+
+
+def test_trigger_missing_body_field_defaults_force_to_false(ctx):
+    client, _store, _tmp_path = ctx
+    response = client.post("/research/edge-report/compute", json={})
+    assert response.status_code == 200
+    assert response.json()["compute"]["force"] is False
+    _poll_compute_until_terminal(client)
+
+
+def test_second_trigger_while_running_returns_the_same_job(ctx, monkeypatch):
+    """TC-2, at the route level."""
+    client, _store, _tmp_path = ctx
+    started = threading.Event()
+    release = threading.Event()
+
+    def fake_run(*args, **kwargs):
+        started.set()
+        release.wait(timeout=5)
+        return {"train": {"cells": []}, "holdout": {"cells": []}, "surviving_train_cells": []}
+
+    from app.research import edge_report_compute as edge_report_compute_module
+
+    monkeypatch.setattr(edge_report_compute_module, "run_strategy_comparison_report", fake_run)
+
+    first = client.post("/research/edge-report/compute", json={}).json()
+    assert started.wait(timeout=5)
+
+    second = client.post("/research/edge-report/compute", json={}).json()
+    assert second["started"] is False
+    assert second["compute"]["id"] == first["compute"]["id"]
+
+    release.set()
+    _poll_compute_until_terminal(client)
+
+
+def test_cancel_mid_run_resolves_cancelled_and_the_cache_holds_no_partial_report(ctx, monkeypatch):
+    """TC-3."""
+    client, _store, tmp_path = ctx
+    _record_reference_dataset(client)
+
+    before = client.get("/research/edge-report").json()
+    assert before["status"] == "not_computed"
+
+    started = threading.Event()
+
+    def fake_run(*args, **kwargs):
+        should_abort = kwargs["should_abort"]
+        started.set()
+        deadline = time.time() + 5
+        while time.time() < deadline:
+            if should_abort():
+                raise EdgeReportComputeCancelled()
+            time.sleep(0.005)
+        raise AssertionError("should_abort never fired")
+
+    from app.research import edge_report_compute as edge_report_compute_module
+
+    monkeypatch.setattr(edge_report_compute_module, "run_strategy_comparison_report", fake_run)
+
+    client.post("/research/edge-report/compute", json={})
+    assert started.wait(timeout=5)
+
+    cancel_response = client.post("/research/edge-report/compute/cancel")
+    assert cancel_response.status_code == 200
+
+    terminal = _poll_compute_until_terminal(client)
+    assert terminal["state"] == "cancelled"
+    assert terminal["error"] is None
+
+    after = client.get("/research/edge-report").json()
+    assert after["status"] == "not_computed"
+    assert after["dataset_count"] == before["dataset_count"]
+
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    records, errors = dataset_store.list()
+    assert errors == []
+    cache = EdgeReportCache(str(tmp_path / "edge_report_cache.db"))
+    assert cache.lookup(records, CONFIG) is None  # mechanical proof: no row was ever published
+
+
+def test_a_failed_compute_surfaces_error_verbatim_and_publishes_no_partial_report(ctx, monkeypatch):
+    """TC-13, at the route level."""
+    client, _store, tmp_path = ctx
+    _record_reference_dataset(client)
+
+    def fake_run(*args, **kwargs):
+        raise RuntimeError("synthetic mid-sweep failure")
+
+    from app.research import edge_report_compute as edge_report_compute_module
+
+    monkeypatch.setattr(edge_report_compute_module, "run_strategy_comparison_report", fake_run)
+
+    client.post("/research/edge-report/compute", json={})
+    terminal = _poll_compute_until_terminal(client)
+
+    assert terminal["state"] == "failed"
+    assert terminal["error"] == "synthetic mid-sweep failure"
+
+    after = client.get("/research/edge-report").json()
+    assert after["status"] == "not_computed"
+
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    records, errors = dataset_store.list()
+    assert errors == []
+    cache = EdgeReportCache(str(tmp_path / "edge_report_cache.db"))
+    assert cache.lookup(records, CONFIG) is None
+
+
+def test_force_true_recomputes_over_a_warm_key(ctx, monkeypatch):
+    """TC-5."""
+    client, _store, _tmp_path = ctx
+    _record_reference_dataset(client)
+
+    client.post("/research/edge-report/compute", json={})
+    _poll_compute_until_terminal(client)
+
+    from app.research import edge_report as edge_report_module
+
+    calls = []
+    real_compute = edge_report_module._compute_strategy_comparison_report
+
+    def _counting_compute(*args, **kwargs):
+        calls.append(1)
+        return real_compute(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report_module, "_compute_strategy_comparison_report", _counting_compute)
+
+    response = client.post("/research/edge-report/compute", json={"force": True})
+    assert response.json()["compute"]["force"] is True
+    terminal = _poll_compute_until_terminal(client)
+
+    assert terminal["state"] == "done"
+    assert len(calls) == 1  # a fresh call, even though the key was already warm
+
+
+def test_non_force_trigger_over_the_same_warm_key_does_not_recompute(ctx, monkeypatch):
+    """TC-6."""
+    client, _store, _tmp_path = ctx
+    _record_reference_dataset(client)
+
+    client.post("/research/edge-report/compute", json={})
+    _poll_compute_until_terminal(client)
+
+    from app.research import edge_report as edge_report_module
+
+    calls = []
+    real_compute = edge_report_module._compute_strategy_comparison_report
+
+    def _counting_compute(*args, **kwargs):
+        calls.append(1)
+        return real_compute(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report_module, "_compute_strategy_comparison_report", _counting_compute)
+
+    response = client.post("/research/edge-report/compute", json={})
+    assert response.json()["compute"]["force"] is False
+    terminal = _poll_compute_until_terminal(client)
+
+    assert terminal["state"] == "done"
+    assert calls == []  # zero recompute — served entirely from the warm cache
+
+
+def test_compute_field_on_the_edge_report_payload_mirrors_get_compute_byte_for_byte(ctx, monkeypatch):
+    """TC-8."""
+    client, _store, _tmp_path = ctx
+    _record_reference_dataset(client)
+
+    cold = client.get("/research/edge-report").json()
+    assert cold["status"] == "not_computed"
+    assert cold["compute"] is None  # unchanged J-01 behavior — nothing has ever triggered
+
+    started = threading.Event()
+    release = threading.Event()
+
+    def fake_run(*args, **kwargs):
+        started.set()
+        release.wait(timeout=5)
+        return {"train": {"cells": []}, "holdout": {"cells": []}, "surviving_train_cells": []}
+
+    from app.research import edge_report_compute as edge_report_compute_module
+
+    monkeypatch.setattr(edge_report_compute_module, "run_strategy_comparison_report", fake_run)
+
+    client.post("/research/edge-report/compute", json={})
+    assert started.wait(timeout=5)
+
+    while_running = client.get("/research/edge-report").json()
+    compute_endpoint_while_running = client.get("/research/edge-report/compute").json()
+    assert while_running["status"] == "not_computed"  # the fake never touches the real cache
+    assert while_running["compute"] == compute_endpoint_while_running
+    assert while_running["compute"]["state"] == "running"
+
+    release.set()
+    _poll_compute_until_terminal(client)
+
+
+def test_trigger_route_wired_through_the_registry_edge_report_compute_property():
+    """A coherence guard (never a second manager construction): the trigger route reads the SAME
+    ``registry.edge_report_compute`` property ``GET``/``cancel`` read."""
+    import inspect
+
+    from app.research import routes
+
+    for fn in (routes.trigger_edge_report_compute, routes.get_edge_report_compute, routes.cancel_edge_report_compute):
+        src = inspect.getsource(fn)
+        assert "registry.edge_report_compute" in src
+
+
+def test_edge_report_route_still_passes_the_pinned_depends_and_cache_kwarg_after_this_iteration():
+    """Re-runs the TWO pre-existing pinned guard tests' own assertions inline (never edited) to
+    confirm this iteration's ADDITIVE ``compute=`` kwarg on the SAME call did not disturb them."""
+    import inspect
+
+    from app.research import routes
+
+    src = inspect.getsource(routes.get_edge_report)
+    assert "Depends(get_bar_store)" in src
+    assert "Depends(get_dataset_store)" in src
+    assert "Depends(get_edge_report_cache)" in src
+    assert "cache=cache" in src
diff --git a/apps/frontend/app/structure/page.tsx b/apps/frontend/app/structure/page.tsx
index 6c4b671..f6179a4 100644
--- a/apps/frontend/app/structure/page.tsx
+++ b/apps/frontend/app/structure/page.tsx
@@ -7,6 +7,7 @@ import {
   fetchBarSeriesList,
   fetchDatasets,
   fetchEdgeReport,
+  fetchEdgeReportCompute,
   fetchLevels,
   fetchPnlLedger,
   fetchProfiles,
@@ -15,6 +16,7 @@ import {
   fetchStrategies,
   fetchTradability,
   recordBarSeries,
+  triggerEdgeReportCompute,
 } from "@/lib/api";
 import type {
   Backtest,
@@ -27,6 +29,7 @@ import type {
   Dataset,
   DatasetsListResult,
   EdgeReportCell,
+  EdgeReportComputeSnapshot,
   EdgeReportPayload,
   EdgeReportResponse,
   EdgeReportSurvivingCell,
@@ -284,7 +287,31 @@ function LoadingPanel({ testid }: { testid: string }) {
 // computed, empty result). Reuses `UnavailablePanel`'s amber degraded-state treatment (no new
 // visual language) with its own testid + its own headline/detail copy; `detail` is the backend's
 // OWN trigger explanation, rendered verbatim — never a frontend-authored string.
-function NotComputedPanel({ detail }: { detail: string }) {
+//
+// era-fast_wall J-04: gains the "Compute edge report" button + live progress line + failed-state
+// render. `compute` (the live/last snapshot, kept fresh by the poll effect in `StructurePage`)
+// drives four states: idle (button enabled, no progress line), running (button shows "Computing…"
+// and is disabled, progress counts render), done (this panel is no longer rendered — the parent
+// swaps to `EdgeReportBody` once the re-fetched report loses its `not_computed` status), and
+// failed (the snapshot's `error` renders verbatim, button re-enabled reading "Retry compute").
+// `triggerError` is a SEPARATE, POST-specific failure (e.g. backend unreachable at click time) —
+// distinct from a `failed` compute job, which is a server-side outcome of a job that DID start.
+function NotComputedPanel({
+  detail,
+  compute,
+  onTriggerCompute,
+  triggering,
+  triggerError,
+}: {
+  detail: string;
+  compute: EdgeReportComputeSnapshot | null;
+  onTriggerCompute: () => void;
+  triggering: boolean;
+  triggerError: string | null;
+}) {
+  const isRunning = compute?.state === "running";
+  const isFailed = compute?.state === "failed";
+  const buttonLabel = isRunning ? "Computing…" : isFailed ? "Retry compute" : "Compute edge report";
   return (
     <div
       data-testid="edge-report-not-computed"
@@ -292,6 +319,33 @@ function NotComputedPanel({ detail }: { detail: string }) {
     >
       <p className="text-sm font-medium text-amber-300">Edge report not computed yet.</p>
       <p className="mt-1 text-xs text-amber-200/70">{detail}</p>
+      {isFailed && compute?.error && (
+        <p data-testid="edge-report-compute-error" className="mt-2 text-xs text-red-300">
+          {compute.error}
+        </p>
+      )}
+      {triggerError && (
+        <p data-testid="edge-report-compute-trigger-error" className="mt-2 text-xs text-red-300">
+          {triggerError}
+        </p>
+      )}
+      <button
+        type="button"
+        data-testid="edge-report-compute-button"
+        onClick={onTriggerCompute}
+        disabled={triggering || isRunning}
+        className="mt-3 rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:border-slate-500 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-600 disabled:hover:bg-slate-800"
+      >
+        {buttonLabel}
+      </button>
+      {isRunning && (
+        <p data-testid="edge-report-compute-progress" className="mt-2 text-xs text-amber-200/70">
+          {compute.progress.backtests_done} / {compute.progress.backtests_total} backtests
+          {compute.progress.backtests_from_cache > 0
+            ? ` (${compute.progress.backtests_from_cache} from cache)`
+            : ""}
+        </p>
+      )}
     </div>
   );
 }
@@ -1198,6 +1252,15 @@ export default function StructurePage() {
     error?: string;
   } | null>(null);
 
+  // era-fast_wall J-04 — the operator-run edge-report compute. `computeSnapshot` is seeded from
+  // the not-computed payload's own `compute` field on mount (see the mount effect below), so a
+  // page load mid-job or post-terminal resumes the correct view without a spurious extra click;
+  // the poll effect then keeps it fresh while `state === "running"`. `computeTriggerError` is the
+  // POST's own failure (e.g. backend unreachable at click time) — distinct from a `failed` job.
+  const [computeSnapshot, setComputeSnapshot] = useState<EdgeReportComputeSnapshot | null>(null);
+  const [computeTriggering, setComputeTriggering] = useState(false);
+  const [computeTriggerError, setComputeTriggerError] = useState<string | null>(null);
+
   // J-05 fetch-control state — the page's ONE new explicit write action. Independent of
   // `symbolInput`/`asOfInput` above (the pre-existing read-only Load form) until a successful
   // fetch seeds them (see `handleFetchYahoo` below). `fetchError` carries the backend's own
@@ -1265,15 +1328,57 @@ export default function StructurePage() {
     fetchSetups().then((result) => {
       if (alive) setSetupsResult({ ok: result.ok, events: result.data?.events ?? [], error: result.error });
     });
-    // era-5B J-04: the 3-way edge report.
+    // era-5B J-04: the 3-way edge report. era-fast_wall J-04: the not-computed payload's own
+    // `compute` field seeds `computeSnapshot` on mount, so a page load mid-job or post-terminal
+    // resumes the correct view without a spurious extra click (the poll effect below then keeps
+    // it fresh while running).
     fetchEdgeReport().then((result) => {
-      if (alive) setEdgeReportResult(result);
+      if (!alive) return;
+      setEdgeReportResult(result);
+      if (result.ok && result.data && result.data.status === "not_computed") {
+        setComputeSnapshot(result.data.compute);
+      }
     });
     return () => {
       alive = false;
     };
   }, []);
 
+  // era-fast_wall J-04: poll the compute job's snapshot while it is running (mirrors the EXISTING
+  // `needsPolling`/`setInterval(..., 700)` backtest-poll pattern above — reusing the PATTERN, not
+  // the endpoint). Stops the moment `computeSnapshot.state` is no longer `"running"` (the effect
+  // re-runs on every `computeSnapshot` change and simply declines to schedule a new interval).
+  // The instant a tick observes `state === "done"`, the edge report is re-fetched exactly once so
+  // the panel falls through to the pre-existing `EdgeReportBody` render — zero new report-
+  // rendering code, the SAME "zero client recomputation" discipline every other section follows.
+  useEffect(() => {
+    if (computeSnapshot?.state !== "running") return;
+    const handle = setInterval(async () => {
+      const next = await fetchEdgeReportCompute();
+      if (!next.ok) return; // an honest "couldn't reach the backend this tick" — keep polling
+      setComputeSnapshot(next.data);
+      if (next.data && next.data.state === "done") {
+        const report = await fetchEdgeReport();
+        setEdgeReportResult(report);
+      }
+    }, 700);
+    return () => clearInterval(handle);
+  }, [computeSnapshot]);
+
+  // era-fast_wall J-04: POST the trigger, then seed the freshly-started (or already-running)
+  // snapshot from the response so the poll effect above picks it up immediately.
+  async function handleTriggerEdgeReportCompute() {
+    setComputeTriggering(true);
+    setComputeTriggerError(null);
+    const result = await triggerEdgeReportCompute();
+    setComputeTriggering(false);
+    if (result.ok && result.data) {
+      setComputeSnapshot(result.data.compute);
+    } else {
+      setComputeTriggerError(result.error ?? "The edge-report compute could not be started.");
+    }
+  }
+
   // era-5B J-02/J-03: fetch the drill-in whenever a Case Studies row is selected. Clears to
   // `{phase: "idle"}` when nothing is selected (e.g. never rendered — the drill-in Panel only
   // mounts once a row has been clicked, so "idle" is never actually shown, but keeps the state
@@ -1878,7 +1983,13 @@ export default function StructurePage() {
                 message={edgeReportResult.error ?? "The edge report could not be loaded."}
               />
             ) : edgeReport.status === "not_computed" ? (
-              <NotComputedPanel detail={edgeReport.detail} />
+              <NotComputedPanel
+                detail={edgeReport.detail}
+                compute={computeSnapshot}
+                onTriggerCompute={handleTriggerEdgeReportCompute}
+                triggering={computeTriggering}
+                triggerError={computeTriggerError}
+              />
             ) : (
               <EdgeReportBody report={edgeReport} />
             )}
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index d697e9f..dc48fd9 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -10,6 +10,7 @@ import type {
   CreateStudyResult,
   DatasetsListResult,
   DeclareResult,
+  EdgeReportComputeSnapshot,
   EdgeReportPayload,
   Hint,
   JournalDetail,
@@ -1163,3 +1164,79 @@ export async function fetchEdgeReport(): Promise<{
     return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// --- era-fast_wall J-04: the operator-run edge-report compute -- POST the single-flight trigger,
+// GET the poll-while-active snapshot, POST the cooperative cancel. All three mirror
+// `createBacktest`/`fetchBacktest`/`cancelStudy`'s exact `{ok, data/…, error}` shape and
+// 422/unreachable folding byte-for-byte (both immediately above and below in this file).
+
+// POST /research/edge-report/compute — start (or, while one is already running, observe) the
+// single-flight compute job. Mirrors `createBacktest`'s exact shape: `data` carries the full
+// `{started, compute}` body on success; the backend's own 422/unreachable `detail` is surfaced
+// VERBATIM on failure — never a client-fabricated message in its place.
+export async function triggerEdgeReportCompute(
+  force?: boolean,
+): Promise<{
+  ok: boolean;
+  data?: { started: boolean; compute: EdgeReportComputeSnapshot };
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/edge-report/compute`, {
+      method: "POST",
+      headers: { "Content-Type": "application/json" },
+      body: JSON.stringify({ force: force ?? false }),
+    });
+    if (res.ok) {
+      const data = await res.json();
+      return { ok: true, data };
+    }
+    let error = "The edge-report compute could not be started.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, error };
+  } catch {
+    return { ok: false, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// GET /research/edge-report/compute — the compute job's current/last snapshot, served VERBATIM,
+// or `null` if none has ever run. Mirrors `fetchBacktest`'s pattern: `ok:false, data:null` on any
+// failure so a poll tick's caller keeps the last known view — never fabricates a snapshot.
+export async function fetchEdgeReportCompute(): Promise<{
+  ok: boolean;
+  data: EdgeReportComputeSnapshot | null;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/edge-report/compute`);
+    if (!res.ok) return { ok: false, data: null };
+    const data = await res.json();
+    return { ok: true, data: (data as EdgeReportComputeSnapshot | null) ?? null };
+  } catch {
+    return { ok: false, data: null };
+  }
+}
+
+// POST /research/edge-report/compute/cancel — cancel the in-flight compute job. Mirrors
+// `cancelStudy`'s exact `{ok, error?}` shape; the backend's 409 (idle) `detail` is surfaced
+// VERBATIM.
+export async function cancelEdgeReportCompute(): Promise<{ ok: boolean; error?: string }> {
+  try {
+    const res = await fetch(`${API_BASE}/research/edge-report/compute/cancel`, { method: "POST" });
+    if (res.ok) return { ok: true };
+    let error = "The edge-report compute could not be cancelled.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, error };
+  } catch {
+    return { ok: false, error: "Backend unreachable — is the API running?" };
+  }
+}
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 183270a..dcbb126 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1360,18 +1360,43 @@ export interface EdgeReportResponse {
   status?: undefined;
 }
 
+// era-fast_wall J-04 -- the operator-run compute-job snapshot, owned by
+// app/research/edge_report_compute.py's `EdgeReportComputeManager`. Served VERBATIM by
+// GET /research/edge-report/compute (poll), started by POST /research/edge-report/compute,
+// cancelled by POST /research/edge-report/compute/cancel -- and embedded VERBATIM as the
+// not-computed edge-report payload's own `compute` field below (one owner, one read, two
+// callers -- never a second derivation).
+export interface EdgeReportComputeProgress {
+  phase: string;
+  backtests_total: number;
+  backtests_done: number;
+  backtests_from_cache: number;
+  current: { dataset_id: string; strategy_id: string } | null;
+}
+
+export interface EdgeReportComputeSnapshot {
+  id: string;
+  state: "running" | "done" | "cancelled" | "failed";
+  force: boolean;
+  started_utc: string | null;
+  finished_utc: string | null;
+  error: string | null;
+  progress: EdgeReportComputeProgress;
+}
+
 // GET /research/edge-report — the honest not-computed payload (era-fast_wall J-01): a cold cache
 // key with a non-empty dataset registry. `status` is the sole discriminator against
 // `EdgeReportResponse` above (absent -- `undefined` -- on a real report). `detail` is the
 // backend's OWN trigger explanation, rendered verbatim, never a frontend-authored string.
-// `compute` is always `null` this iteration (no compute manager exists until J-04 -- see
-// `peek_strategy_comparison_report`'s own docstring).
+// `compute` (era-fast_wall J-04: widened from its former `null`-only literal type) is the
+// compute manager's current/last snapshot, or `null` if no compute has ever been triggered --
+// read VERBATIM, never re-derived client-side.
 export interface EdgeReportNotComputed {
   status: "not_computed";
   detail: string;
   dataset_count: number;
   register: string;
-  compute: null;
+  compute: EdgeReportComputeSnapshot | null;
 }
 
 // The discriminated union `fetchEdgeReport()` actually returns -- a real report or the
diff --git a/apps/backend/app/research/edge_report_compute.py b/apps/backend/app/research/edge_report_compute.py
new file mode 100644
index 0000000..1c4ce59
--- /dev/null
+++ b/apps/backend/app/research/edge_report_compute.py
@@ -0,0 +1,303 @@
+"""era-fast_wall J-04 — the operator-run compute: a single-flight, cancellable, progress-reporting
+background job around ``edge_report.run_strategy_comparison_report``'s five additive keyword-only
+hooks (``force``/``progress``/``should_abort``/``sub_cache``/``workers`` — see that function's own
+docstring), plus a CLI warmer that drives the SAME hooks synchronously, in-process.
+
+THIS MODULE computes NOTHING itself — ``run_strategy_comparison_report`` (and, through it,
+``EdgeReportCache.get_or_compute``/``compute_and_publish``, both already shipped at J-01) stay the
+SOLE computer and the SOLE cache writer. ``EdgeReportComputeManager`` is pure job bookkeeping: it
+decides WHEN to call that one function (single-flight — never a second concurrent call), tracks
+WHETHER it is running/done/cancelled/failed, and republishes an atomic progress snapshot as the
+call's own ``progress``/``should_abort`` hooks fire. Process-scoped, in-memory-only state — a
+backend restart honestly loses it (the SAME "in-flight jobs lost on restart" contract
+``StudyJobManager``/``BacktestJobManager`` already carry); it is never a research value (goal.md's
+own Data Contract: "Job state is process-scoped bookkeeping... never a research value").
+
+**Single-flight, deliberately simpler than ``StudyJobManager``/``BacktestJobManager``'s per-id
+dict.** There is only ever ONE "the edge report compute" — one job slot (``self._snapshot``), not a
+dict keyed by id. A ``trigger()`` while the current job's ``state == "running"`` returns that SAME
+job unchanged (``started: False``); once terminal, the NEXT ``trigger()`` starts a genuinely NEW job
+(a fresh id), discarding the old snapshot.
+
+**Publish only after the compute function returns normally — true BY CONSTRUCTION, not by a special
+case here.** ``EdgeReportCache.get_or_compute``/``compute_and_publish`` (both UNTOUCHED, J-01) only
+ever call ``self._insert``/rebind ``self._hot`` AFTER their ``compute_fn`` argument returns — a
+``compute_fn`` that raises (whether ``edge_report.EdgeReportComputeCancelled`` from a fired
+``should_abort``, or any genuine failure) leaves BOTH cache layers exactly as they were. This
+module's worker thread simply distinguishes the TWO exception shapes at its own outer boundary:
+``EdgeReportComputeCancelled`` resolves ``state: "cancelled"``; anything else resolves
+``state: "failed"`` with the exception's message surfaced verbatim (never swallowed, never generic).
+
+**Atomic snapshot publish — the ``EdgeReportCache._hot`` / ``setups.py`` ``_SCAN_CACHE``
+discipline, applied to job bookkeeping instead of a computed result.** Every snapshot mutation
+(progress patch, terminal resolution) builds a FRESH dict and rebinds ``self._snapshot`` in ONE
+assignment under ``self._lock`` — a concurrent reader (``snapshot()``) takes ONE local reference
+before inspecting it and is handed its OWN shallow copy (so a caller mutating what it read can never
+poison the manager's own state — the ``BarStore.get``/``list`` "served rows are copies" precedent).
+"""
+
+from __future__ import annotations
+
+import argparse
+import json
+import sys
+import threading
+import uuid
+from datetime import datetime, timezone
+from pathlib import Path
+from typing import Callable
+
+from ..config import CONFIG, Config
+from .bars import BarStore
+from .datasets import DatasetStore
+from .edge_report import EdgeReportComputeCancelled, EdgeReportError, run_strategy_comparison_report
+from .edge_report_cache import EdgeReportCache, resolve_cache_db_path
+from .store import JournalStore
+
+__all__ = ["EdgeReportComputeManager"]
+
+# Mirrors goal.md's own CLI usage string (``--workers N``, default 4) — accepted this iteration,
+# currently INERT (see ``run_strategy_comparison_report``'s own docstring; J-05 gives it effect).
+_DEFAULT_WORKERS = 4
+
+
+def _iso_utc_now() -> str:
+    return (
+        datetime.now(timezone.utc)
+        .isoformat(timespec="microseconds")
+        .replace("+00:00", "Z")
+    )
+
+
+def _idle_progress() -> dict:
+    """The progress sub-dict a freshly-triggered job starts with, before ``_compute_strategy_
+    comparison_report`` has even resolved ``events`` (and therefore has no ``backtests_total`` to
+    report yet) — an honest ``0``, never a fabricated estimate."""
+    return {
+        "phase": "starting", "backtests_total": 0, "backtests_done": 0,
+        "backtests_from_cache": 0, "current": None,
+    }
+
+
+def _copy_snapshot(snapshot: dict) -> dict:
+    """A caller-safe copy (two levels deep — the ``progress`` sub-dict and its own ``current``
+    sub-dict, the full nesting this shape ever carries) so a reader mutating what ``snapshot()``
+    returns can never poison ``EdgeReportComputeManager``'s own internal state."""
+    progress = snapshot["progress"]
+    current = progress.get("current")
+    return {
+        **snapshot,
+        "progress": {**progress, "current": dict(current) if current is not None else None},
+    }
+
+
+class EdgeReportComputeManager:
+    """Owns the SINGLE in-flight (or last-terminal) edge-report compute job. Construct with no
+    arguments — unlike ``BacktestJobManager``/``StudyJobManager`` (which bind one ``store``/
+    ``config`` for their whole lifetime), every ``trigger()`` call takes its store/dataset_store/
+    bar_store/config/cache explicitly, the SAME per-call injection ``BacktestJobManager.start``
+    already uses for ``dataset_store``/``bar_store`` — so a test (or a future second registry)
+    points this at any hermetic store pair with zero constructor plumbing."""
+
+    def __init__(self) -> None:
+        self._lock = threading.Lock()
+        self._snapshot: dict | None = None
+        self._cancel_event: threading.Event | None = None
+        self._thread: threading.Thread | None = None
+
+    def snapshot(self) -> dict | None:
+        """The current/last job's snapshot, or ``None`` if none has ever run — a caller-safe copy
+        (see ``_copy_snapshot``), never a shared mutable reference."""
+        current = self._snapshot  # read-local-reference-before-inspect
+        if current is None:
+            return None
+        return _copy_snapshot(current)
+
+    def trigger(
+        self,
+        store: JournalStore,
+        dataset_store: DatasetStore,
+        bar_store: BarStore,
+        config: Config,
+        cache: EdgeReportCache,
+        *,
+        force: bool = False,
+    ) -> dict:
+        """Start a NEW compute job, or — if one is already ``state == "running"`` — return it
+        UNCHANGED (``started: False``, the SAME job's own ``force``, never the just-requested one).
+        Once the current job is terminal (done/cancelled/failed, or none has ever run), the NEXT
+        call always starts a genuinely new job (a fresh id), discarding the prior snapshot. Never
+        blocks on the compute itself — the actual sweep runs on a dedicated worker thread, OFF the
+        caller's thread (the ``BacktestJobManager.start`` precedent), so an HTTP route calling this
+        returns immediately."""
+        with self._lock:
+            current = self._snapshot
+            if current is not None and current["state"] == "running":
+                return {"started": False, "compute": _copy_snapshot(current)}
+
+            job_id = uuid.uuid4().hex
+            cancel_event = threading.Event()
+            self._cancel_event = cancel_event
+            snapshot = {
+                "id": job_id,
+                "state": "running",
+                "force": force,
+                "started_utc": _iso_utc_now(),
+                "finished_utc": None,
+                "error": None,
+                "progress": _idle_progress(),
+            }
+            self._snapshot = snapshot
+
+        def _publish_progress(patch: dict) -> None:
+            fields = {k: v for k, v in patch.items() if k != "event"}
+            with self._lock:
+                current = self._snapshot
+                if current is None or current["id"] != job_id:
+                    return  # a NEWER job already replaced this one -- a stale reporter, ignored
+                self._snapshot = {
+                    **current,
+                    "progress": {**current["progress"], **fields},
+                }
+
+        def _work() -> None:
+            try:
+                run_strategy_comparison_report(
+                    store, dataset_store, bar_store, config,
+                    cache=cache, force=force, progress=_publish_progress,
+                    should_abort=cancel_event.is_set,
+                )
+            except EdgeReportComputeCancelled:
+                self._resolve(job_id, "cancelled", error=None)
+            except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
+                self._resolve(job_id, "failed", error=str(exc))
+            else:
+                self._resolve(job_id, "done", error=None)
+
+        thread = threading.Thread(target=_work, name=f"edge-report-compute:{job_id}", daemon=True)
+        with self._lock:
+            self._thread = thread
+        thread.start()
+        return {"started": True, "compute": _copy_snapshot(snapshot)}
+
+    def _resolve(self, job_id: str, state: str, *, error: str | None) -> None:
+        with self._lock:
+            current = self._snapshot
+            if current is None or current["id"] != job_id:
+                return  # superseded -- never resolve a job that is no longer the current one
+            self._snapshot = {
+                **current,
+                "state": state,
+                "finished_utc": _iso_utc_now(),
+                "error": error,
+            }
+
+    def cancel(self) -> None:
+        """Signal cooperative cancellation for the in-flight job — a harmless no-op if idle (the
+        ROUTE is the one that rejects an idle cancel with a 409, mirroring ``cancel_backtest``'s
+        own check-then-call split; see ``routes.py``)."""
+        with self._lock:
+            cancel_event = self._cancel_event
+        if cancel_event is not None:
+            cancel_event.set()
+
+    def join_all(self, timeout: float = 30.0) -> None:
+        """Wait for the in-flight job thread, if any (test/shutdown hygiene — the
+        ``BacktestJobManager.join_all`` precedent, applied to this manager's single thread)."""
+        with self._lock:
+            thread = self._thread
+        if thread is not None:
+            thread.join(timeout=timeout)
+
+
+# --- The CLI warmer ---------------------------------------------------------------------------------
+# Mirrors ``edge_report.py``'s own ``main()`` CLI precedent: resolves the SAME env/config seams the
+# backend reads (journal, dataset dir, bar dir, the edge-report cache DB), runs to completion
+# SYNCHRONOUSLY in-process (no manager, no background thread — a CLI invocation IS the one caller;
+# there is nothing else to serialize against), and exits 0 with a summary. Deliberately does NOT go
+# through ``EdgeReportComputeManager`` (single-flight/cancel/progress-polling exist to serve
+# CONCURRENT HTTP callers; a one-shot CLI process has none) -- it calls the SAME ``run_strategy_
+# comparison_report`` hooks directly, exactly like the era-3 J-09 CLI calls ``run_edge_report``
+# directly. The existing era-3 J-09 ``edge_report.main()`` CLI stays byte-untouched.
+
+
+def _cli_progress_printer() -> Callable[[dict], None]:
+    """One progress LINE per completed backtest (TC-11), plus one summary line announcing the
+    total up front — a pure formatting closure over the SAME ``_ProgressReporter``-shaped patches
+    the compute manager consumes (the ``"event"`` key disambiguates a start-of-run announcement
+    from a per-pair update; see ``edge_report._ProgressReporter``)."""
+    state = {"total": 0}
+
+    def _printer(patch: dict) -> None:
+        event = patch.get("event")
+        if event == "total":
+            state["total"] = patch["backtests_total"]
+            print(f"edge-report compute: {state['total']} backtest(s) to run", flush=True)
+        elif event == "pair_done":
+            current = patch.get("current")  # already cleared back to None by _ProgressReporter
+            done = patch["backtests_done"]
+            print(f"[{done}/{state['total']}] backtest complete{'' if current is None else f' ({current})'}", flush=True)
+
+    return _printer
+
+
+def main() -> int:
+    """The CLI entry: ``python -m app.research.edge_report_compute --workers N [--force]
+    [--out report.json]``. Runs the 3-way strategy-comparison sweep to completion against the
+    operator's journal/dataset/bar dirs, publishing to the SAME durable edge-report cache
+    ``GET /research/edge-report`` serves (``resolve_cache_db_path`` — the identical resolver the
+    route's own dependency uses). An ``EdgeReportError`` (a corrupt dataset) prints an explicit
+    message to stderr and exits 1 with nothing published — the existing ``get_or_compute``/
+    ``compute_and_publish`` discipline (nothing is ever cached on an exception)."""
+    parser = argparse.ArgumentParser(
+        description="era-fast_wall J-04 CLI warmer -- run the 3-way v1/structure_tape/"
+        "structure_tape_map edge-report sweep to completion, publishing to the SAME durable "
+        "cache GET /research/edge-report serves."
+    )
+    parser.add_argument(
+        "--workers", type=int, default=_DEFAULT_WORKERS,
+        help="accepted for the future parallel sweep (J-05); INERT this iteration -- every "
+        "compute runs strictly sequentially regardless of this value.",
+    )
+    parser.add_argument(
+        "--force", action="store_true",
+        help="recompute even over an already-warm cache key and republish.",
+    )
+    parser.add_argument("--out", default=None, help="optional path to also write the report JSON")
+    args = parser.parse_args()
+
+    config = CONFIG
+    store = JournalStore(config.journal_db_path_resolved(), config)
+    try:
+        dataset_store = DatasetStore(config.dataset_dir_resolved())
+        bar_store = BarStore(config.bar_dir_resolved())
+        cache = EdgeReportCache(resolve_cache_db_path(config.dataset_dir_resolved()))
+
+        try:
+            report = run_strategy_comparison_report(
+                store, dataset_store, bar_store, config,
+                cache=cache, force=args.force, progress=_cli_progress_printer(),
+                workers=args.workers,
+            )
+        except EdgeReportError as exc:
+            print(f"error: {exc}", file=sys.stderr)
+            return 1
+    finally:
+        store.close()
+
+    n_train = len(report["train"]["cells"])
+    n_holdout = len(report["holdout"]["cells"])
+    print(
+        f"edge report compute complete: {n_train} train cell(s), {n_holdout} hold-out cell(s) "
+        f"published to the durable cache."
+    )
+    if args.out:
+        out_path = Path(args.out)
+        out_path.parent.mkdir(parents=True, exist_ok=True)
+        out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
+        print(f"report written to {out_path}")
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_edge_report_compute.py b/apps/backend/tests/test_edge_report_compute.py
new file mode 100644
index 0000000..d5e8eec
--- /dev/null
+++ b/apps/backend/tests/test_edge_report_compute.py
@@ -0,0 +1,456 @@
+"""era-fast_wall J-04 -- the operator-run compute: ``EdgeReportComputeManager`` (single-flight,
+cancel, atomic progress snapshot) plus the CLI warmer's ``main()``.
+
+Manager tests substitute a FAKE ``run_strategy_comparison_report`` (monkeypatched onto THIS
+module's own imported name -- the ``test_edge_report_api.py`` counting-spy precedent, applied to a
+full function swap instead of a wrapper) for deterministic, threading-free control over timing
+(started/release ``threading.Event`` pairs, a ``should_abort`` that genuinely loops until fired).
+End-to-end wiring against the REAL ``run_strategy_comparison_report`` (real cache, real fixtures) is
+proven in ``test_edge_report.py`` (the hooks themselves, TC-14) and ``test_edge_report_api.py`` (the
+HTTP routes, TC-1/2/3/5/6/8). CLI tests mirror ``edge_report.py``'s own
+``test_cli_main_writes_a_report_and_exits_zero_on_the_fixture_pair`` pattern exactly.
+"""
+
+from __future__ import annotations
+
+import json
+import sys
+import threading
+import time
+from pathlib import Path
+
+import pytest
+
+from app.config import CONFIG
+from app.research import edge_report_compute
+from app.research.bars import BarStore
+from app.research.datasets import DatasetStore
+from app.research.edge_report import EdgeReportComputeCancelled
+from app.research.edge_report_cache import EdgeReportCache, resolve_cache_db_path
+from app.research.edge_report_compute import EdgeReportComputeManager
+from app.research.store import JournalStore
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+FIXTURE_J03_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets_j03"
+
+_EMPTY_REPORT = {"train": {"cells": []}, "holdout": {"cells": []}, "surviving_train_cells": []}
+
+
+@pytest.fixture
+def store(tmp_path):
+    s = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    yield s
+    s.close()
+
+
+def _trigger_args(tmp_path, store):
+    """The five positional args every ``manager.trigger(...)`` call needs -- a fresh, hermetic
+    dataset/bar store pair + a fresh cache DB, all rooted under the test's own ``tmp_path`` (never
+    the package-anchored default)."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    bar_store = BarStore(tmp_path / "bars")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    return store, dataset_store, bar_store, CONFIG, cache
+
+
+def _wait_for_terminal(manager: EdgeReportComputeManager, timeout: float = 5.0) -> dict:
+    deadline = time.time() + timeout
+    while time.time() < deadline:
+        snap = manager.snapshot()
+        if snap is not None and snap["state"] != "running":
+            return snap
+        time.sleep(0.01)
+    raise AssertionError("edge-report compute job never reached a terminal state")
+
+
+# ==================================================================================================
+# The manager: single-flight, cancel, force, progress, failed-state -- every test here swaps out
+# ``run_strategy_comparison_report`` entirely (never the real multi-backtest sweep), so timing is
+# controlled by explicit ``threading.Event`` pairs, never wall-clock luck.
+# ==================================================================================================
+
+
+def test_no_job_has_ever_run_snapshot_is_none():
+    manager = EdgeReportComputeManager()
+    assert manager.snapshot() is None
+
+
+def test_trigger_starts_a_job_and_returns_the_data_contract_shape(tmp_path, store, monkeypatch):
+    manager = EdgeReportComputeManager()
+    started = threading.Event()
+    release = threading.Event()
+
+    def fake_run(*args, **kwargs):
+        started.set()
+        release.wait(timeout=5)
+        return _EMPTY_REPORT
+
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)
+
+    result = manager.trigger(*_trigger_args(tmp_path, store))
+
+    assert result["started"] is True
+    compute = result["compute"]
+    assert isinstance(compute["id"], str) and compute["id"] != ""
+    assert compute["state"] == "running"
+    assert compute["force"] is False
+    assert isinstance(compute["started_utc"], str) and compute["started_utc"] != ""
+    assert compute["finished_utc"] is None
+    assert compute["error"] is None
+    assert compute["progress"] == {
+        "phase": "starting", "backtests_total": 0, "backtests_done": 0,
+        "backtests_from_cache": 0, "current": None,
+    }
+    assert started.wait(timeout=5)
+    release.set()
+    manager.join_all(timeout=5)
+
+
+def test_second_trigger_while_running_returns_the_same_job_started_false(tmp_path, store, monkeypatch):
+    """TC-2."""
+    manager = EdgeReportComputeManager()
+    started = threading.Event()
+    release = threading.Event()
+
+    def fake_run(*args, **kwargs):
+        started.set()
+        release.wait(timeout=5)
+        return _EMPTY_REPORT
+
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)
+
+    first = manager.trigger(*_trigger_args(tmp_path, store))
+    assert started.wait(timeout=5)
+
+    second = manager.trigger(*_trigger_args(tmp_path, store), force=True)  # even force never bypasses
+
+    assert second["started"] is False
+    assert second["compute"]["id"] == first["compute"]["id"]
+    assert second["compute"]["force"] is False  # the ORIGINAL (non-force) job, unchanged
+
+    release.set()
+    manager.join_all(timeout=5)
+
+
+def test_trigger_after_a_terminal_job_starts_a_genuinely_new_job(tmp_path, store, monkeypatch):
+    manager = EdgeReportComputeManager()
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", lambda *a, **k: _EMPTY_REPORT)
+
+    first = manager.trigger(*_trigger_args(tmp_path, store))
+    _wait_for_terminal(manager)
+    manager.join_all(timeout=5)
+
+    second = manager.trigger(*_trigger_args(tmp_path, store))
+    assert second["started"] is True
+    assert second["compute"]["id"] != first["compute"]["id"]
+    manager.join_all(timeout=5)
+
+
+def test_a_normal_return_resolves_state_done(tmp_path, store, monkeypatch):
+    manager = EdgeReportComputeManager()
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", lambda *a, **k: _EMPTY_REPORT)
+
+    manager.trigger(*_trigger_args(tmp_path, store))
+    snap = _wait_for_terminal(manager)
+
+    assert snap["state"] == "done"
+    assert snap["error"] is None
+    assert isinstance(snap["finished_utc"], str) and snap["finished_utc"] != ""
+    manager.join_all(timeout=5)
+
+
+def test_a_cancellation_signal_resolves_state_cancelled_never_failed(tmp_path, store, monkeypatch):
+    """TC-3 (manager-level wiring): the SAME cancellation signal ``_split_cells`` raises when
+    ``should_abort`` fires (real proof in ``test_edge_report.py``'s TC-14b) is what the manager's
+    worker thread must distinguish from a genuine failure -- proven here with a fake that genuinely
+    observes the hook, mirroring the NOTES' suggested "raise a dedicated signal" mechanism."""
+    manager = EdgeReportComputeManager()
+    started = threading.Event()
+
+    def fake_run(*args, **kwargs):
+        should_abort = kwargs["should_abort"]
+        started.set()
+        deadline = time.time() + 5
+        while time.time() < deadline:
+            if should_abort():
+                raise EdgeReportComputeCancelled()
+            time.sleep(0.005)
+        raise AssertionError("should_abort never fired")
+
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)
+
+    manager.trigger(*_trigger_args(tmp_path, store))
+    assert started.wait(timeout=5)
+    manager.cancel()
+
+    snap = _wait_for_terminal(manager)
+    assert snap["state"] == "cancelled"
+    assert snap["error"] is None
+    manager.join_all(timeout=5)
+
+
+def test_a_raised_exception_resolves_state_failed_with_the_message_verbatim(tmp_path, store, monkeypatch):
+    """TC-13."""
+    manager = EdgeReportComputeManager()
+
+    def fake_run(*args, **kwargs):
+        raise RuntimeError("synthetic mid-sweep failure")
+
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)
+
+    manager.trigger(*_trigger_args(tmp_path, store))
+    snap = _wait_for_terminal(manager)
+
+    assert snap["state"] == "failed"
+    assert snap["error"] == "synthetic mid-sweep failure"
+    assert isinstance(snap["finished_utc"], str) and snap["finished_utc"] != ""
+    manager.join_all(timeout=5)
+
+
+def test_force_flag_is_threaded_through_to_the_compute_call_and_recorded_on_the_snapshot(
+    tmp_path, store, monkeypatch
+):
+    manager = EdgeReportComputeManager()
+    seen = {}
+
+    def fake_run(*args, **kwargs):
+        seen["force"] = kwargs["force"]
+        return _EMPTY_REPORT
+
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)
+
+    result = manager.trigger(*_trigger_args(tmp_path, store), force=True)
+    _wait_for_terminal(manager)
+
+    assert seen["force"] is True
+    assert result["compute"]["force"] is True
+    manager.join_all(timeout=5)
+
+
+def test_progress_patches_merge_atomically_into_the_snapshots_progress_subdict(tmp_path, store, monkeypatch):
+    manager = EdgeReportComputeManager()
+
+    def fake_run(*args, **kwargs):
+        progress = kwargs["progress"]
+        progress({"event": "total", "phase": "backtests", "backtests_total": 3, "backtests_done": 0,
+                   "backtests_from_cache": 0, "current": None})
+        progress({"event": "pair_started", "current": {"dataset_id": "d1", "strategy_id": "v1"}})
+        progress({"event": "pair_done", "backtests_done": 1, "backtests_from_cache": 0, "current": None})
+        return _EMPTY_REPORT
+
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)
+
+    manager.trigger(*_trigger_args(tmp_path, store))
+    snap = _wait_for_terminal(manager)
+
+    assert snap["progress"] == {
+        "phase": "backtests", "backtests_total": 3, "backtests_done": 1,
+        "backtests_from_cache": 0, "current": None,
+    }
+    # the transient "current" update mid-run was visible at SOME point too -- a stale reporter
+    # from an already-superseded job is never possible here since only one job ever ran.
+    manager.join_all(timeout=5)
+
+
+def test_cache_kwarg_is_threaded_through_unchanged(tmp_path, store, monkeypatch):
+    manager = EdgeReportComputeManager()
+    seen = {}
+    _, dataset_store, bar_store, config, cache = _trigger_args(tmp_path, store)
+
+    def fake_run(*args, **kwargs):
+        seen["cache"] = kwargs["cache"]
+        return _EMPTY_REPORT
+
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)
+
+    manager.trigger(store, dataset_store, bar_store, config, cache)
+    _wait_for_terminal(manager)
+
+    assert seen["cache"] is cache
+    manager.join_all(timeout=5)
+
+
+def test_cancel_while_idle_is_a_harmless_no_op_the_route_owns_the_409():
+    """The manager itself never raises on an idle cancel -- ``cancel_edge_report_compute`` (the
+    ROUTE) is the one that checks idle-vs-running and raises the 409, mirroring
+    ``cancel_backtest``'s own check-then-call split (``routes.py``)."""
+    manager = EdgeReportComputeManager()
+    manager.cancel()  # must not raise
+    assert manager.snapshot() is None
+
+
+def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_reference(tmp_path, store, monkeypatch):
+    """A caller mutating a snapshot dict it read must never poison the manager's own state (the
+    ``BarStore.get``/``list`` "served rows are copies" discipline, applied here)."""
+    manager = EdgeReportComputeManager()
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", lambda *a, **k: _EMPTY_REPORT)
+
+    result = manager.trigger(*_trigger_args(tmp_path, store))
+    _wait_for_terminal(manager)
+    snap = manager.snapshot()
+    snap["state"] = "tampered"
+    snap["progress"]["backtests_done"] = 999
+
+    fresh = manager.snapshot()
+    assert fresh["state"] == "done"
+    assert fresh["progress"]["backtests_done"] == 0
+    manager.join_all(timeout=5)
+
+
+# ==================================================================================================
+# The CLI warmer (TC-11, TC-12) -- mirrors ``edge_report.py``'s own
+# ``test_cli_main_writes_a_report_and_exits_zero_on_the_fixture_pair`` pattern. The committed
+# ``datasets_j03`` fixture is symbol PG -- NOT a config-owned panel symbol under the REAL shipped
+# ``CONFIG`` the CLI always resolves (mirrors ``edge_report.main()``'s own ``config = CONFIG``), so
+# every compute below is the honest, deterministic, all-empty-cells shape (zero eligible backtests)
+# -- the SAME finding ``test_keyless_committed_j03_fixture_with_the_real_panel_is_an_honest_empty_
+# report`` already proves for the direct-call path.
+# ==================================================================================================
+
+
+def _set_cli_env(monkeypatch, tmp_path):
+    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(FIXTURE_J03_DATASET_DIR))
+    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
+    # The cache DB path resolver's default (env-else-sibling-of-dataset-dir) would otherwise land
+    # beside the COMMITTED fixture directory itself (never a tmp_path) since TAPEOLOGY_DATASET_DIR
+    # above points DIRECTLY at it (the test_edge_report.py `test_keyless_committed_j03_fixture_...`
+    # precedent) — leaking state ACROSS test runs and making a "cold cache" test order-dependent.
+    # The explicit override keeps every CLI test hermetic, exactly like every other test in this
+    # suite that touches a cache.
+    monkeypatch.setenv("TAPEOLOGY_EDGE_REPORT_CACHE_DB", str(tmp_path / "edge_report_cache.db"))
+
+
+def test_cli_completes_on_the_fixture_and_a_subsequent_get_path_serves_it_byte_identically(
+    tmp_path, monkeypatch, capsys
+):
+    """TC-11."""
+    _set_cli_env(monkeypatch, tmp_path)
+    monkeypatch.setattr(sys, "argv", ["edge_report_compute"])
+
+    exit_code = edge_report_compute.main()
+
+    assert exit_code == 0
+    out = capsys.readouterr().out
+    assert out.strip() != ""  # at least the "N backtest(s) to run" summary line
+
+    from app.research.edge_report import peek_strategy_comparison_report
+
+    served_store = JournalStore(str(tmp_path / "served-journal.db"), CONFIG)
+    try:
+        dataset_store = DatasetStore(str(FIXTURE_J03_DATASET_DIR))
+        bar_store = BarStore(str(tmp_path / "bars"))
+        cache = EdgeReportCache(resolve_cache_db_path(str(FIXTURE_J03_DATASET_DIR)))
+        served = peek_strategy_comparison_report(
+            served_store, dataset_store, bar_store, CONFIG, cache=cache,
+        )
+    finally:
+        served_store.close()
+
+    assert "status" not in served  # a genuine warm report -- never the not-computed shape
+    assert served["train"]["cells"] == []
+    assert served["holdout"]["cells"] == []
+
+
+def test_cli_repeat_invocation_without_force_is_fast_and_reruns_nothing(tmp_path, monkeypatch):
+    """TC-12."""
+    _set_cli_env(monkeypatch, tmp_path)
+    monkeypatch.setattr(sys, "argv", ["edge_report_compute"])
+    assert edge_report_compute.main() == 0
+
+    from app.research import edge_report as edge_report_module
+
+    calls = []
+    real_compute = edge_report_module._compute_strategy_comparison_report
+
+    def _counting_compute(*args, **kwargs):
+        calls.append(1)
+        return real_compute(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report_module, "_compute_strategy_comparison_report", _counting_compute)
+    monkeypatch.setattr(sys, "argv", ["edge_report_compute"])
+
+    started = time.time()
+    exit_code = edge_report_compute.main()
+    elapsed = time.time() - started
+
+    assert exit_code == 0
+    assert elapsed < 5.0
+    assert calls == []  # zero backtests re-run -- served entirely from the warm durable cache
+
+
+def test_cli_force_flag_recomputes_over_an_already_warm_key(tmp_path, monkeypatch):
+    _set_cli_env(monkeypatch, tmp_path)
+    monkeypatch.setattr(sys, "argv", ["edge_report_compute"])
+    assert edge_report_compute.main() == 0
+
+    from app.research import edge_report as edge_report_module
+
+    calls = []
+    real_compute = edge_report_module._compute_strategy_comparison_report
+
+    def _counting_compute(*args, **kwargs):
+        calls.append(1)
+        return real_compute(*args, **kwargs)
... [diff_bound] apps/backend/tests/test_edge_report_compute.py: 62 more diff lines omitted — Read the file for full detail
```
