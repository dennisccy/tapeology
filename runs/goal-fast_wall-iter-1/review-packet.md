# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 10. Shown in full: 10.

```diff
diff --git a/apps/backend/app/research/edge_report.py b/apps/backend/app/research/edge_report.py
index 6c34063..c066ef3 100644
--- a/apps/backend/app/research/edge_report.py
+++ b/apps/backend/app/research/edge_report.py
@@ -76,7 +76,13 @@ from .edge_report_cache import EdgeReportCache
 from .setups import compute_setups
 from .store import JournalStore
 
-__all__ = ["EdgeReportError", "run_edge_report", "run_strategy_comparison_report", "main"]
+__all__ = [
+    "EdgeReportError",
+    "run_edge_report",
+    "run_strategy_comparison_report",
+    "peek_strategy_comparison_report",
+    "main",
+]
 
 # era-5B J-04: the three registered strategies a comparison cell may ever carry, in the SAME
 # registration order ``Config.strategy_registry()`` serves -- read here so a cell's own
@@ -87,6 +93,14 @@ _ALL_STRATEGY_IDS: tuple[str, ...] = (STRATEGY_V1_ID, STRATEGY_TAPE_ID, STRATEGY
 # datasets clear the positive-edge gate, including the true-empty-registry case.
 NO_POSITIVE_EDGE_FINDING = "no positive-edge dataset"
 
+# era-fast_wall J-01: the not-computed payload's own explanatory ``detail`` string (DoD: "a detail
+# naming the trigger") — ONE canonical literal, never restated inline at ``peek_strategy_
+# comparison_report``'s own call site.
+EDGE_REPORT_NOT_COMPUTED_DETAIL = (
+    "The 3-way strategy-comparison sweep has not been run for the current dataset registry and "
+    "configuration. It never runs automatically on a GET -- an operator must trigger the compute."
+)
+
 
 class EdgeReportError(Exception):
     """The report could not complete honestly — a dataset failed integrity verification or a
@@ -96,17 +110,26 @@ class EdgeReportError(Exception):
 # --- reused computation: ONE backtest per dataset, via the EXISTING runner ----------------------
 
 
-def _split_datasets(dataset_store: DatasetStore, split: str) -> list[dict]:
-    """Every registered dataset metadata row for ``split`` (checksum-verified on load, the ONE
-    ``DatasetStore.list`` read). A file that fails integrity verification anywhere in the store
-    aborts the whole report explicitly — a partial report is a misleading report."""
+def _verified_records(dataset_store: DatasetStore) -> list[dict]:
+    """Every registered dataset metadata row, checksum-verified (the ONE ``DatasetStore.list``
+    read). A file that fails integrity verification anywhere in the store aborts explicitly — a
+    partial report is a misleading report. Shared by ``_split_datasets`` (below, filtered to one
+    split) and ``peek_strategy_comparison_report`` (era-fast_wall J-01, which needs the FULL,
+    unfiltered registry to key the cache and report ``dataset_count``) — ONE list-and-verify call
+    site, never a second copy of this error-formatting."""
     records, errors = dataset_store.list()
     if errors:
         raise EdgeReportError(
             f"{len(errors)} dataset file(s) failed integrity verification "
             f"({[e['file'] for e in errors]}) — the report stops with nothing written"
         )
-    return [r for r in records if r["split"] == split]
+    return records
+
+
+def _split_datasets(dataset_store: DatasetStore, split: str) -> list[dict]:
+    """Every registered dataset metadata row for ``split`` — see ``_verified_records`` for the
+    integrity discipline."""
+    return [r for r in _verified_records(dataset_store) if r["split"] == split]
 
 
 def _run_backtest(
@@ -432,21 +455,26 @@ def run_strategy_comparison_report(
     *,
     cache: EdgeReportCache | None = None,
 ) -> dict:
-    """The public entry point for the 3-way strategy-comparison report (era-5B J-04; ``GET
-    /research/edge-report`` + the MCP ``edge_report`` proxy serve this VERBATIM). See
-    ``_compute_strategy_comparison_report`` below for the full algorithm docstring — this function
-    is now a thin dispatcher over that ONE computation, never a second copy of it.
+    """The always-recompute-or-serve-through-a-cache entry point for the 3-way strategy-comparison
+    report (era-5B J-04). See ``_compute_strategy_comparison_report`` below for the full algorithm
+    docstring — this function is a thin dispatcher over that ONE computation, never a second copy
+    of it.
+
+    era-fast_wall J-01: ``GET /research/edge-report`` calls ``peek_strategy_comparison_report``
+    (below) instead of this function — ``peek_...`` NEVER computes on a cold cache key. This
+    function remains the module's ONE optionally-cached compute dispatcher: every direct test in
+    ``tests/test_edge_report.py`` still exercises it unmodified, and it is the exact shape
+    ``EdgeReportCache.compute_and_publish``'s future operator/CLI "force" callers (J-04) wrap.
 
     era-5B J-08: ``cache`` is an OPTIONAL rebuildable result cache
     (``edge_report_cache.EdgeReportCache``). ``cache=None`` (the default) is the EXACT pre-J-08
     behaviour — always calls ``_compute_strategy_comparison_report`` directly, byte-for-byte
     identical to before — so every EXISTING call site (every test in ``test_edge_report.py``, and
     any future caller with no cache to offer) is untouched and stays uncached. When a cache IS
-    supplied (the route's DI-wired path — see ``routes.get_edge_report``), this function serves
-    ``_compute_strategy_comparison_report``'s output VERBATIM through it: the cache never
-    re-derives a cell, a measurement, or a null baseline — a miss recomputes byte-identically
-    through the SAME one function below (single source of truth; no second computation path,
-    anywhere)."""
+    supplied, this function serves ``_compute_strategy_comparison_report``'s output VERBATIM
+    through it: the cache never re-derives a cell, a measurement, or a null baseline — a miss
+    recomputes byte-identically through the SAME one function below (single source of truth; no
+    second computation path, anywhere)."""
 
     def compute() -> dict:
         return _compute_strategy_comparison_report(store, dataset_store, bar_store, config)
@@ -456,6 +484,47 @@ def run_strategy_comparison_report(
     return cache.get_or_compute(dataset_store, config, compute)
 
 
+def peek_strategy_comparison_report(
+    store: JournalStore,
+    dataset_store: DatasetStore,
+    bar_store: BarStore,
+    config: Config,
+    *,
+    cache: EdgeReportCache,
+) -> dict:
+    """The GET-path's EXCLUSIVE entry point (era-fast_wall J-01) — ``routes.get_edge_report`` calls
+    ONLY this, never ``run_strategy_comparison_report``, so opening ``/structure`` (or any GET, or
+    the MCP ``edge_report`` proxy) can NEVER start the sweep (the interlude's headline CRITICAL
+    anti-goal — "no compute on page load, operator-run only"). Three branches:
+
+      * A store-integrity failure raises ``EdgeReportError`` exactly as today (``_verified_
+        records``, above) — the route's existing explicit 500; the cache is never even keyed.
+      * An EMPTY dataset registry still computes inline — the pre-J-01 O(1), zero-backtest shape
+        (``_compute_strategy_comparison_report`` skips the whole scan/backtest path when both
+        splits are empty; see that function's own docstring) — the response carries no ``status``
+        key, byte-identical to before J-01 shipped.
+      * A NON-EMPTY registry consults the cache's READ-ONLY ``lookup`` — NEVER ``get_or_compute``
+        or ``compute_and_publish`` (pinned by ``tests/test_edge_report.py``'s ``test_peek_source_
+        never_calls_a_compute_triggering_cache_method``): a warm key returns the cached report
+        VERBATIM; a cold key returns the honest not-computed payload (``status: "not_computed"``,
+        the canonical ``EDGE_REPORT_NOT_COMPUTED_DETAIL``, ``dataset_count``, ``register`` read
+        from ``backtests.REGISTER`` — never a restated literal — and ``compute: null``, since no
+        compute manager exists until J-04)."""
+    records = _verified_records(dataset_store)
+    if not records:
+        return _compute_strategy_comparison_report(store, dataset_store, bar_store, config)
+    cached = cache.lookup(records, config)
+    if cached is not None:
+        return cached
+    return {
+        "status": "not_computed",
+        "detail": EDGE_REPORT_NOT_COMPUTED_DETAIL,
+        "dataset_count": len(records),
+        "register": REGISTER,
+        "compute": None,
+    }
+
+
 def _compute_strategy_comparison_report(
     store: JournalStore, dataset_store: DatasetStore, bar_store: BarStore, config: Config
 ) -> dict:
diff --git a/apps/backend/app/research/edge_report_cache.py b/apps/backend/app/research/edge_report_cache.py
index 38f7f6e..e5dee22 100644
--- a/apps/backend/app/research/edge_report_cache.py
+++ b/apps/backend/app/research/edge_report_cache.py
@@ -81,6 +81,19 @@ the signature (the ``setups.py`` ``_store_signature`` precedent) would otherwise
 file that is NOT part of any previously-cached healthy subset coincidentally matching a stale
 cached key and silently serving a result that never saw the corruption — never worth the risk for
 what is already the rare, explicit-failure path.
+
+**era-fast_wall J-01 additions — ``lookup``/``compute_and_publish`` beside ``get_or_compute``.**
+``get_or_compute`` stays UNTOUCHED (byte-identical, every one of its own tests unmodified). Two
+new methods split its "check cache, else compute" behaviour into its two named halves, for the
+interlude's headline "no compute on a GET, ever" anti-goal: ``lookup(records, config)`` is the
+READ-ONLY half (hot slot then durable row, returns ``None`` on a miss, NEVER calls a compute
+function) — the sole method the route now calls; ``compute_and_publish(dataset_store, config,
+compute_fn)`` is the WRITE half (always recomputes unconditionally, republishes to both layers) —
+the future operator/CLI "force" path (J-04). Both share the identical key derivation
+(``_cache_key``) and store-integrity-bypass discipline ``get_or_compute`` already established
+above. ``resolve_cache_db_path`` (module-level, not a method) is the DB-path resolution policy
+itself, extracted from ``routes.py``'s inline dependency body so a future CLI caller resolves the
+IDENTICAL path with zero duplicated logic.
 """
 
 from __future__ import annotations
@@ -88,6 +101,7 @@ from __future__ import annotations
 import dataclasses
 import hashlib
 import json
+import os
 import sqlite3
 from datetime import datetime, timezone
 from pathlib import Path
@@ -96,7 +110,11 @@ from typing import Callable
 from ..config import Config
 from .datasets import DatasetStore
 
-__all__ = ["EdgeReportCache"]
+__all__ = ["EdgeReportCache", "resolve_cache_db_path"]
+
+# The env var this cache's DB path resolution checks first (era-5B J-08, extracted to a shared
+# resolver at era-fast_wall J-01 — see ``resolve_cache_db_path`` below).
+_CACHE_DB_ENV = "TAPEOLOGY_EDGE_REPORT_CACHE_DB"
 
 # Mirrors ``bar_index.py``'s ``_BUSY_TIMEOUT_MS`` (5000ms) — the identical brief writer-contention
 # tolerance a low-frequency, small-payload cache needs.
@@ -154,6 +172,22 @@ def _cache_key(records: list[dict], config: Config) -> str:
     return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
 
 
+def resolve_cache_db_path(dataset_dir_resolved: str) -> str:
+    """The cache DB path resolution policy (era-fast_wall J-01) — extracted from ``routes.py``'s
+    inline ``get_edge_report_cache()`` body into ONE shared function (the ``get_bar_index``
+    env-else-sibling shape) so a future CLI caller (J-04's warmer) resolves the IDENTICAL path with
+    zero duplicated logic: the ``TAPEOLOGY_EDGE_REPORT_CACHE_DB`` env var if set, else a file
+    co-located as a SIBLING of the caller's OWN already-resolved dataset directory. Takes the
+    resolved dataset directory as a plain string rather than a ``Config`` — this module never
+    imports ``config.py``'s singleton or its resolution helpers, only the ``Config`` dataclass type
+    (unchanged import list) — so the caller (``routes.py``, and later the CLI) resolves its own
+    dataset directory first, exactly as it already does today."""
+    override = os.environ.get(_CACHE_DB_ENV)
+    if override:
+        return override
+    return os.path.join(os.path.dirname(dataset_dir_resolved), "edge_report_cache.db")
+
+
 class EdgeReportCache:
     """The persisted, rebuildable edge-report result cache — construct with an explicit, hermetic
     DB path (the ``BarIndex``/``DatasetStore``/``BarStore`` dependency-injection precedent)."""
@@ -264,3 +298,53 @@ class EdgeReportCache:
         self._insert(key, result)
         self._hot = (key, result)  # single atomic rebind, published AFTER the durable write
         return result
+
+    def lookup(self, records: list[dict], config: Config) -> dict | None:
+        """era-fast_wall J-01 — the GET-path's EXCLUSIVE read method: serve the CURRENT
+        ``(records, config)`` key's cached result (hot slot then durable row), or ``None`` on a
+        genuine miss. NEVER calls a compute function (unlike ``get_or_compute``) — there is no
+        ``compute_fn`` parameter to call, so a miss is mechanically incapable of starting the
+        sweep. Callers MUST have already confirmed ``records`` came from an error-free
+        ``dataset_store.list()`` call — the identical ``get_or_compute``/``_cache_key`` contract
+        (see that method's own docstring and the module docstring's key-derivation section).
+
+        Atomic against concurrent callers, the identical ``get_or_compute`` discipline: ``self.
+        _hot`` is read ONCE into a local before any inspection, and a durable hit republishes it to
+        the hot slot in one atomic rebind (harmless if raced — the republished value is always the
+        SAME already-persisted row)."""
+        key = _cache_key(records, config)
+
+        hot = self._hot  # read-local-reference-before-inspect
+        if hot is not None and hot[0] == key:
+            return hot[1]
+
+        persisted = self._select(key)
+        if persisted is not None:
+            self._hot = (key, persisted)  # single atomic rebind
+        return persisted
+
+    def compute_and_publish(
+        self,
+        dataset_store: DatasetStore,
+        config: Config,
+        compute_fn: Callable[[], dict],
+    ) -> dict:
+        """era-fast_wall J-01 — the operator/CLI "force" half (J-04's future compute manager and
+        CLI warmer both republish through this exact method; this iteration exercises it directly
+        since no route calls it yet — see the module docstring). Always calls ``compute_fn``
+        exactly once — UNCONDITIONALLY, never checking the cache first, unlike ``get_or_compute``
+        — and republishes its result to both layers under the CURRENT ``(dataset_store, config)``
+        key, so a subsequent ``lookup`` for the same key returns it verbatim.
+
+        A store-integrity failure still bypasses the cache and calls ``compute_fn`` directly,
+        propagating its exception unchanged — the identical ``get_or_compute`` discipline (see the
+        module docstring's own "store-integrity failures bypass the cache entirely" section)."""
+        records, errors = dataset_store.list()
+        if errors:
+            return compute_fn()
+        key = _cache_key(records, config)
+
+        result = compute_fn()
+        self._insert(key, result)
+        self._hot = (key, result)  # single atomic rebind, published AFTER the durable write
+        return result
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index 8fd1fb6..63706cc 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -49,8 +49,8 @@ from .bars import (
     BarStore,
     EmptyBarWindowError,
 )
-from .edge_report import EdgeReportError, run_strategy_comparison_report
-from .edge_report_cache import EdgeReportCache
+from .edge_report import EdgeReportError, peek_strategy_comparison_report
+from .edge_report_cache import EdgeReportCache, resolve_cache_db_path
 from .levels import compute_levels
 from .setups import BROKE, CHOPPED, REJECTED, compute_setups, enrich_with_tape_timeline
 from .tradability import compute_tradability
@@ -1569,12 +1569,13 @@ def get_edge_report_cache() -> EdgeReportCache:
     config-owned dataset directory (``get_dataset_store``'s own ``dataset_dir_resolved()``, e.g.
     ``.data/datasets`` -> ``.data/edge_report_cache.db`` — the SAME ``.data/`` directory
     ``bar_index.db`` already lives in). A FastAPI dependency so tests can override it outright or
-    point it at a temp path via the env var — the ``get_bar_index`` pattern, exactly."""
-    override = os.environ.get("TAPEOLOGY_EDGE_REPORT_CACHE_DB")
-    db_path = override if override else os.path.join(
-        os.path.dirname(CONFIG.dataset_dir_resolved()), "edge_report_cache.db"
-    )
-    return EdgeReportCache(db_path)
+    point it at a temp path via the env var — the ``get_bar_index`` pattern, exactly.
+
+    era-fast_wall J-01: the path policy itself now lives in ONE shared ``edge_report_cache.
+    resolve_cache_db_path`` function — this dependency's whole body is just resolving-then-
+    constructing — so a future CLI caller (J-04's warmer) resolves the IDENTICAL path with zero
+    duplicated logic. This function's own resolved path is unchanged for every existing test."""
+    return EdgeReportCache(resolve_cache_db_path(CONFIG.dataset_dir_resolved()))
 
 
 def get_bar_fetch_adapter():
@@ -2082,12 +2083,15 @@ def get_strategies(registry: ResearchRegistry = Depends(get_registry)) -> dict:
 # --- The 3-way strategy-comparison edge report (era-5B capability 6, J-04; Data Contract row
 # "edge-report cells") ---------------------------------------------------------------------------
 # Exactly ONE route, GET only, mirroring ``GET /research/strategies`` immediately above in shape:
-# ``research/edge_report.py``'s ``run_strategy_comparison_report`` is the SOLE computer of this
-# value; this route only wires the three existing dependency seams (journal store, dataset store,
-# bar store — the identical ``create_backtest`` seam trio) and serves the module's output VERBATIM
-# (the MCP ``edge_report`` tool proxies this byte-identically; no second computation path). No
-# write surface exists on this route — any non-GET verb is FastAPI's default 405. This route never
-# reads or moves the champion pointer — see the module's own "no champion, no promotion" docstring.
+# ``research/edge_report.py``'s ``peek_strategy_comparison_report`` (era-fast_wall J-01) is the
+# SOLE computer this route calls; this route only wires the four existing dependency seams
+# (journal store, dataset store, bar store, cache) and serves the module's output VERBATIM (the
+# MCP ``edge_report`` tool proxies this byte-identically; no second computation path). J-01: a GET
+# NEVER computes the sweep — a cold cache key on a non-empty registry returns the honest
+# ``status: "not_computed"`` payload instead of starting it; only the future operator/CLI compute
+# (J-04) ever calls ``run_strategy_comparison_report``'s always-compute path. No write surface
+# exists on this route — any non-GET verb is FastAPI's default 405. This route never reads or
+# moves the champion pointer — see the module's own "no champion, no promotion" docstring.
 
 
 @router.get("/edge-report")
@@ -2100,17 +2104,17 @@ def get_edge_report(
     """The 3-way strategy-comparison report (``v1`` / ``structure_tape`` / ``structure_tape_map``)
     aggregated into per strategy x class x side x reaction x feed cells over every registered
     event-window dataset that resolves an owning, classified scan event — served VERBATIM from
-    ``run_strategy_comparison_report`` (era-5B J-04), through the rebuildable result cache
-    (era-5B J-08 — ``edge_report_cache.get_edge_report_cache``, the SAME DI-overridable seam
-    ``get_bar_index`` uses) so a warm cache answers within an interactive budget instead of the
-    documented ~10+h sweep. The cache is an accelerator only: a miss recomputes byte-identically
-    through the SAME one function; this route's response shape is UNCHANGED either way. A dataset
-    failing integrity verification aborts the whole report with an explicit 500 (the
-    ``create_backtest``/``EdgeReportError`` precedent) — partial results are never served, and
-    never cached. An all-empty or all-``insufficient_sample`` report (the expected shape on a
-    keyless, single-fixture registry) is a valid 200, never an error."""
+    ``peek_strategy_comparison_report`` (era-fast_wall J-01; the rebuildable result cache DI-wired
+    through the SAME seam shape ``get_bar_index`` uses). era-fast_wall J-01: this GET NEVER
+    computes the sweep — a warm cache key answers instantly with the report; a cold key on a
+    non-empty registry answers instantly too, with the honest ``status: "not_computed"`` payload,
+    rather than starting the multi-hour compute inside this request. An empty dataset registry
+    keeps the pre-J-01 O(1), zero-backtest full-report shape. A dataset failing integrity
+    verification aborts the whole report with an explicit 500 (the ``create_backtest``/
+    ``EdgeReportError`` precedent) — partial results are never served, and never cached. An
+    all-empty or all-``insufficient_sample`` WARM report is a valid 200, never an error."""
     try:
-        return run_strategy_comparison_report(
+        return peek_strategy_comparison_report(
             registry.store, dataset_store, bar_store, registry.config, cache=cache
         )
     except EdgeReportError as exc:
diff --git a/apps/backend/tests/test_edge_report.py b/apps/backend/tests/test_edge_report.py
index 8704506..9ae30f5 100644
--- a/apps/backend/tests/test_edge_report.py
+++ b/apps/backend/tests/test_edge_report.py
@@ -979,3 +979,110 @@ def test_cache_wiring_source_never_duplicates_the_computation():
     # Exactly ONE definition of each — never a second copy under a different name.
     assert src.count("def run_strategy_comparison_report(") == 1
     assert src.count("def _compute_strategy_comparison_report(") == 1
+
+
+# ==================================================================================================
+# The honest not-computed peek (era-fast_wall J-01) — ``peek_strategy_comparison_report``, the
+# GET-path's EXCLUSIVE entry point from this iteration on (``routes.get_edge_report`` calls ONLY
+# this, never ``run_strategy_comparison_report`` — see ``routes.py``). Proves the three branches
+# named in the function's own docstring: a cold key on a non-empty registry returns the honest
+# not-computed payload and NEVER calls the compute path; a warm key (published via
+# ``EdgeReportCache.compute_and_publish`` — the future operator/CLI path, J-04) returns THAT exact
+# result verbatim; an empty registry keeps the pre-J-01 O(1) full-report shape untouched.
+# ==================================================================================================
+
+from app.research.edge_report import peek_strategy_comparison_report  # noqa: E402
+
+
+def test_peek_on_a_cold_key_returns_the_not_computed_payload_and_never_computes(
+    tmp_path, store, scan_bar_store, scan_config, monkeypatch
+):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
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
+    result = peek_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
+
+    assert calls == []  # a cold GET-path call NEVER computes -- the whole point of J-01
+    assert result["status"] == "not_computed"
+    assert isinstance(result["detail"], str) and result["detail"] != ""
+    assert result["dataset_count"] == 1
+    assert result["register"] == REGISTER
+    assert result["compute"] is None
+
+
+def test_peek_on_a_warm_key_returns_the_published_result_verbatim(
+    tmp_path, store, scan_bar_store, scan_config
+):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    published = cache.compute_and_publish(
+        dataset_store, scan_config,
+        lambda: edge_report._compute_strategy_comparison_report(
+            store, dataset_store, scan_bar_store, scan_config
+        ),
+    )
+
+    result = peek_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
+
+    assert json.dumps(result, sort_keys=True) == json.dumps(published, sort_keys=True)
+    assert "status" not in result
+    assert len(result["train"]["cells"]) == 3  # non-degenerate, the real 3-cell shape
+
+
+def test_peek_on_an_empty_registry_keeps_the_pre_j01_full_report_shape(tmp_path, store):
+    dataset_store = DatasetStore(tmp_path / "datasets")  # never populated
+    bar_store = BarStore(tmp_path / "empty-bars")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+
+    result = peek_strategy_comparison_report(store, dataset_store, bar_store, CONFIG, cache=cache)
+
+    assert "status" not in result
+    assert result["train"]["cells"] == []
+    assert result["holdout"]["cells"] == []
+    assert result["surviving_train_cells"] == []
+
+
+def test_peek_raises_on_a_dataset_integrity_error_before_ever_touching_the_cache(
+    tmp_path, store, scan_bar_store, scan_config, monkeypatch
+):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    meta = _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    path = tmp_path / "datasets" / f"{meta['id']}.json"
+    data = json.loads(path.read_text())
+    data["record"]["meta"]["checksum"] = "0" * 64  # tamper
+    path.write_text(json.dumps(data))
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+
+    def _boom(*args, **kwargs):
+        raise AssertionError("cache.lookup must never be called on an integrity-error path")
+
+    monkeypatch.setattr(cache, "lookup", _boom)
+
+    with pytest.raises(EdgeReportError, match="integrity"):
+        peek_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
+
+
+def test_peek_source_never_calls_a_compute_triggering_cache_method():
+    """A coherence guard, mechanically pinning the GET-path's central promise: ``peek_strategy_
+    comparison_report``'s OWN source never calls a cache method that could compute and persist a
+    fresh report (``cache.get_or_compute``/``cache.compute_and_publish``) — only the read-only
+    ``cache.lookup``. The one legitimate direct call to ``_compute_strategy_comparison_report`` is
+    the documented empty-registry O(1) branch (see the function's own docstring), not a cache
+    method at all."""
+    import inspect
+
+    src = inspect.getsource(edge_report.peek_strategy_comparison_report)
+    assert "cache.lookup(" in src
+    for forbidden in ("cache.get_or_compute(", "cache.compute_and_publish("):
+        assert forbidden not in src
diff --git a/apps/backend/tests/test_edge_report_api.py b/apps/backend/tests/test_edge_report_api.py
index 6b8ea69..3b475b4 100644
--- a/apps/backend/tests/test_edge_report_api.py
+++ b/apps/backend/tests/test_edge_report_api.py
@@ -18,6 +18,7 @@ from app.main import app, manager
 from app.research.bars import BarStore
 from app.research.datasets import DatasetStore
 from app.research.edge_report import REGISTER, run_strategy_comparison_report
+from app.research.edge_report_cache import EdgeReportCache
 from app.research.routes import ResearchRegistry, get_bar_store, set_registry
 from app.research.store import JournalStore
 
@@ -52,9 +53,13 @@ def test_edge_report_empty_registry_is_an_honest_200(ctx):
 
 
 def test_edge_report_matches_the_module_function_byte_for_byte(ctx):
-    """Single source of truth: the route's JSON is a VERBATIM serving of
-    ``run_strategy_comparison_report`` — never a second computation. Recording one dataset
-    through the real API first proves this on a genuinely non-trivial (if still
+    """Single source of truth (TC-4): a WARM route response is a VERBATIM serving of
+    ``run_strategy_comparison_report``'s own output — never a second computation. era-fast_wall
+    J-01: a cold GET no longer computes at all (see the not-computed tests below), so this test
+    now pre-warms the cache directly via ``EdgeReportCache.compute_and_publish`` — standing in for
+    the future operator/CLI trigger (J-04) — at the SAME hermetic path the route's own dependency
+    resolves to (see ``test_edge_report_route_cache_db_lives_hermetically_beside_the_test_dataset_
+    dir`` below), before asserting byte-identity on a genuinely non-trivial (if still
     ``insufficient_sample``-shaped) payload, not merely the vacuous empty case."""
     client, store, tmp_path = ctx
     recorded = client.post(
@@ -68,10 +73,14 @@ def test_edge_report_matches_the_module_function_byte_for_byte(ctx):
     )
     assert recorded.status_code == 200, recorded.text
 
-    route_payload = client.get("/research/edge-report").json()
     dataset_store = DatasetStore(tmp_path / "datasets")
     bar_store = BarStore(tmp_path / "bars")
     direct = run_strategy_comparison_report(store, dataset_store, bar_store, CONFIG)
+    EdgeReportCache(str(tmp_path / "edge_report_cache.db")).compute_and_publish(
+        dataset_store, CONFIG, lambda: direct
+    )
+
+    route_payload = client.get("/research/edge-report").json()
     assert json.dumps(route_payload, sort_keys=True) == json.dumps(direct, sort_keys=True)
     # PG (the reference fixture's own symbol) is not a config-owned panel symbol, so this
     # recording honestly resolves no owning scan event -- still an empty, valid cell list.
@@ -140,12 +149,15 @@ def test_edge_report_route_wired_through_the_new_cache_dependency():
     assert "cache=cache" in src
 
 
-def test_edge_report_route_serves_a_warm_result_on_the_second_call_without_recomputing(ctx, monkeypatch):
-    """The end-to-end proof J-08 exists for: TWO real HTTP requests against the SAME running
-    backend, the second of which must never re-enter the expensive computation — proven by
-    counting calls to ``_compute_strategy_comparison_report`` (the ONE real computer), not merely
-    inferring it from response shape."""
-    client, _store, _tmp_path = ctx
+def test_edge_report_route_serves_a_warm_result_on_repeated_calls_without_recomputing(ctx, monkeypatch):
+    """The end-to-end proof J-08 exists for, updated for era-fast_wall J-01's new contract: a GET
+    itself no longer WARMS the cache (see the not-computed tests below), so this pre-warms directly
+    via ``EdgeReportCache.compute_and_publish`` — standing in for the future operator/CLI trigger
+    (J-04) — at the SAME hermetic path the route's own dependency resolves to, then proves TWO real
+    HTTP requests against the SAME running backend never re-enter the expensive computation —
+    proven by counting calls to ``_compute_strategy_comparison_report`` (the ONE real computer),
+    not merely inferring it from response shape."""
+    client, store, tmp_path = ctx
     recorded = client.post(
         "/research/datasets",
         json={
@@ -157,6 +169,13 @@ def test_edge_report_route_serves_a_warm_result_on_the_second_call_without_recom
     )
     assert recorded.status_code == 200, recorded.text
 
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    bar_store = BarStore(tmp_path / "bars")
+    EdgeReportCache(str(tmp_path / "edge_report_cache.db")).compute_and_publish(
+        dataset_store, CONFIG,
+        lambda: run_strategy_comparison_report(store, dataset_store, bar_store, CONFIG),
+    )
+
     from app.research import edge_report as edge_report_module
 
     calls = []
@@ -172,11 +191,18 @@ def test_edge_report_route_serves_a_warm_result_on_the_second_call_without_recom
     second = client.get("/research/edge-report")
 
     assert first.status_code == 200 and second.status_code == 200
-    assert len(calls) == 1  # the SECOND request served entirely from the warm cache
+    assert len(calls) == 0  # already warm BEFORE either request -- neither recomputes
     assert first.json() == second.json()
+    assert "status" not in first.json()  # the genuine warm report shape, never not-computed
 
 
-def test_edge_report_route_response_is_byte_identical_whether_cache_is_cold_or_warm(ctx):
+def test_edge_report_route_cold_response_is_byte_identical_across_repeated_calls(ctx):
+    """era-fast_wall J-01 retires this test's ORIGINAL claim (a cold GET used to compute-and-cache,
+    so cold and warm bytes matched by construction) — a cold GET now returns the intentionally
+    DIFFERENT not-computed shape (TC-1/TC-4 above), so cold-vs-warm byte-identity is no longer the
+    right property. What's still genuinely true and worth proving: the not-computed payload itself
+    is STABLE — repeated cold GETs (nothing here ever warms the cache) return byte-identical
+    responses, never a flapping ``dataset_count``/``detail``."""
     client, _store, _tmp_path = ctx
     recorded = client.post(
         "/research/datasets",
@@ -189,11 +215,53 @@ def test_edge_report_route_response_is_byte_identical_whether_cache_is_cold_or_w
     )
     assert recorded.status_code == 200, recorded.text
 
-    cold = client.get("/research/edge-report")
-    warm = client.get("/research/edge-report")
+    first = client.get("/research/edge-report")
+    second = client.get("/research/edge-report")
+
+    assert first.status_code == 200 and second.status_code == 200
+    assert first.json()["status"] == "not_computed"
+    assert json.dumps(first.json(), sort_keys=True) == json.dumps(second.json(), sort_keys=True)
+
 
-    assert cold.status_code == 200 and warm.status_code == 200
-    assert json.dumps(cold.json(), sort_keys=True) == json.dumps(warm.json(), sort_keys=True)
+def test_edge_report_cold_cache_returns_the_not_computed_payload_and_never_computes(ctx, monkeypatch):
+    """TC-1 + TC-2: a cold cache with a non-empty registry answers instantly with the honest
+    not-computed shape, and a counting spy proves the expensive sweep is NEVER entered — the
+    mechanical proof era-fast_wall J-01 exists to deliver."""
+    client, _store, _tmp_path = ctx
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
+    dataset_count = client.get("/research/datasets").json()
+    assert len(dataset_count["datasets"]) == 1
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
+    response = client.get("/research/edge-report")
+
+    assert response.status_code == 200
+    payload = response.json()
+    assert payload["status"] == "not_computed"
+    assert isinstance(payload["detail"], str) and payload["detail"] != ""
+    assert payload["dataset_count"] == 1
+    assert payload["register"] == REGISTER
+    assert payload["compute"] is None
+    assert calls == []  # the GET path never enters the sweep
 
 
 def test_edge_report_route_cache_db_lives_hermetically_beside_the_test_dataset_dir(ctx):
diff --git a/apps/backend/tests/test_edge_report_cache.py b/apps/backend/tests/test_edge_report_cache.py
index 7505c94..12203ed 100644
--- a/apps/backend/tests/test_edge_report_cache.py
+++ b/apps/backend/tests/test_edge_report_cache.py
@@ -21,7 +21,7 @@ import pytest
 from app.config import CONFIG
 from app.providers.base import QuoteEvent, Side, TradeEvent
 from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
-from app.research.edge_report_cache import EdgeReportCache
+from app.research.edge_report_cache import EdgeReportCache, resolve_cache_db_path
 
 WINDOW_START, WINDOW_END = "2026-01-02T14:30:00Z", "2026-01-02T14:30:05Z"
 
@@ -419,3 +419,178 @@ def test_cache_source_never_computes_a_research_value_itself():
         assert forbidden_import not in src, (
             f"a second computation path leaked into edge_report_cache.py: {forbidden_import}"
         )
+
+
+# ==================================================================================================
+# era-fast_wall J-01: ``lookup`` (the GET-path's read-only half) and ``compute_and_publish`` (the
+# operator/CLI "force" half, J-04's future path) beside the untouched ``get_or_compute`` above —
+# every test above this marker is UNMODIFIED, proof by construction that ``get_or_compute``'s own
+# behaviour stays byte-for-byte identical.
+# ==================================================================================================
+
+
+# --- lookup: never computes, hot slot then durable row, None on a genuine miss -----------------
+
+
+def test_lookup_returns_none_on_a_genuine_miss_and_persists_nothing(tmp_path):
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    db_path = str(tmp_path / "cache.db")
+    cache = EdgeReportCache(db_path)
+    records, errors = dstore.list()
+    assert errors == []
+
+    result = cache.lookup(records, CONFIG)
+
+    assert result is None
+    import sqlite3
+
+    conn = sqlite3.connect(db_path)
+    try:
+        rows = conn.execute("SELECT * FROM edge_report_cache").fetchall()
+    finally:
+        conn.close()
+    assert rows == []  # a miss never persists anything -- lookup never computes, never writes a row
+
+
+def test_lookup_never_calls_any_compute_function(tmp_path):
+    """TC-8, literally: ``lookup`` has no ``compute_fn`` parameter at all, so nothing could ever be
+    called even on a miss. Pinned against an EXTERNAL counting stub standing in for 'the real
+    sweep', proving no such function is reachable from ``lookup``'s own call graph."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    compute = _CountingCompute()
+    records, errors = dstore.list()
+    assert errors == []
+
+    result = cache.lookup(records, CONFIG)
+
+    assert result is None
+    assert compute.calls == 0  # never invoked -- lookup was never given a way to call it
+
+
+def test_lookup_serves_a_value_published_via_compute_and_publish_from_the_durable_row(tmp_path):
+    """The DoD's literal restart scenario, for ``lookup`` specifically: a FRESH ``EdgeReportCache``
+    instance (no in-process state carried over) still serves a value an EARLIER instance published
+    via ``compute_and_publish`` — proof ``lookup`` reads the durable row, not merely its own hot
+    slot."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    db_path = str(tmp_path / "cache.db")
+    published = EdgeReportCache(db_path).compute_and_publish(
+        dstore, CONFIG, _CountingCompute({"train": {"cells": ["warm"]}, "holdout": {"cells": []}})
+    )
+
+    records, errors = dstore.list()
+    assert errors == []
+    restarted = EdgeReportCache(db_path)  # no in-process state carried over
+    result = restarted.lookup(records, CONFIG)
+
+    assert result == published == {"train": {"cells": ["warm"]}, "holdout": {"cells": []}}
+
+
+def test_lookup_serves_the_in_process_hot_slot_without_a_second_durable_read(tmp_path):
+    """The identical ``get_or_compute`` hot-slot discipline, proven for ``lookup``: a SECOND
+    ``lookup`` on the SAME instance must be servable even if the durable file is deleted out from
+    under it in between — proof the second call never re-touches the durable row at all."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    db_path = str(tmp_path / "cache.db")
+    cache = EdgeReportCache(db_path)
+    cache.compute_and_publish(dstore, CONFIG, _CountingCompute({"v": "hot"}))
+    records, errors = dstore.list()
+    assert errors == []
+    first = cache.lookup(records, CONFIG)
+    assert first == {"v": "hot"}
+
+    import os as _os
+
+    _os.remove(db_path)  # the durable file is now gone -- a durable re-read would raise/miss
+
+    second = cache.lookup(records, CONFIG)
+
+    assert second == {"v": "hot"}  # served from the hot slot alone
+
+
+# --- compute_and_publish: always recomputes, republishes both layers ---------------------------
+
+
+def test_compute_and_publish_calls_compute_fn_exactly_once_and_publishes_both_layers(tmp_path):
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    db_path = str(tmp_path / "cache.db")
+    cache = EdgeReportCache(db_path)
+    compute = _CountingCompute({"train": {"cells": ["fresh"]}, "holdout": {"cells": []}})
+
+    result = cache.compute_and_publish(dstore, CONFIG, compute)
+
+    assert compute.calls == 1
+    assert result == {"train": {"cells": ["fresh"]}, "holdout": {"cells": []}}
+    records, errors = dstore.list()
+    assert errors == []
+    assert cache.lookup(records, CONFIG) == result  # TC-9's own follow-up lookup
+
+
+def test_compute_and_publish_always_recomputes_even_over_an_already_warm_key(tmp_path):
+    """The defining difference from ``get_or_compute``: ``compute_and_publish`` is the FORCE path —
+    it recomputes UNCONDITIONALLY, even when a value is already cached, and republishes the new
+    result over the old one (the future operator/CLI J-04 "force" semantics)."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    cache.compute_and_publish(dstore, CONFIG, _CountingCompute({"v": 1}))
+
+    second = _CountingCompute({"v": 2})
+    result = cache.compute_and_publish(dstore, CONFIG, second)
+
+    assert second.calls == 1  # recomputed despite an already-warm key
+    assert result == {"v": 2}
+    records, errors = dstore.list()
+    assert cache.lookup(records, CONFIG) == {"v": 2}  # the NEW result, not the stale one
+
+
+def test_compute_and_publish_bypasses_the_cache_on_a_store_integrity_error(tmp_path):
+    dstore = DatasetStore(tmp_path / "datasets")
+    meta = _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    path = tmp_path / "datasets" / f"{meta['id']}.json"
+    data = json.loads(path.read_text())
+    data["record"]["meta"]["checksum"] = "0" * 64  # tamper
+    path.write_text(json.dumps(data))
+    db_path = str(tmp_path / "cache.db")
+    cache = EdgeReportCache(db_path)
+
+    class _Boom(Exception):
+        pass
+
+    def _raising_compute():
+        raise _Boom("the real EdgeReportError path, standing in for it here")
+
+    with pytest.raises(_Boom):
+        cache.compute_and_publish(dstore, CONFIG, _raising_compute)
+
+    import sqlite3
+
+    conn = sqlite3.connect(db_path)
+    try:
+        rows = conn.execute("SELECT * FROM edge_report_cache").fetchall()
+    finally:
+        conn.close()
+    assert rows == []  # nothing persisted on the integrity-error bypass path
+
+
+# --- the shared cache-DB-path resolver (era-fast_wall J-01) -------------------------------------
+
+
+def test_resolve_cache_db_path_uses_the_env_override_when_set(monkeypatch, tmp_path):
+    override = str(tmp_path / "custom" / "cache.db")
+    monkeypatch.setenv("TAPEOLOGY_EDGE_REPORT_CACHE_DB", override)
+
+    assert resolve_cache_db_path(str(tmp_path / "anything" / "datasets")) == override
+
+
+def test_resolve_cache_db_path_defaults_to_a_sibling_of_the_dataset_dir(monkeypatch, tmp_path):
+    monkeypatch.delenv("TAPEOLOGY_EDGE_REPORT_CACHE_DB", raising=False)
+    dataset_dir = str(tmp_path / "datasets")
+
+    assert resolve_cache_db_path(dataset_dir) == str(tmp_path / "edge_report_cache.db")
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index e362c92..c595719 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -538,15 +538,25 @@ async def test_strategies_tool_byte_identical_on_a_non_empty_live_result(mcp_env
 
 @pytest.mark.anyio
 async def test_edge_report_tool_byte_identical_to_rest(mcp_env):
-    """``edge_report`` (era-5B J-04) ships in the SAME iteration as its endpoint — the report
-    dict (``register``/``pnl_min_sample_size``/``train``/``holdout``/``surviving_train_cells``)
-    is ALWAYS present (an empty dataset registry is an honest, well-formed 200 — never an error),
-    so this proves byte-identity with no seeding at all, the ``strategies`` tool's own precedent."""
+    """``edge_report`` (era-5B J-04) ships in the SAME iteration as its endpoint. era-fast_wall
+    J-01 (TC-6): by this point in the module, an earlier test
+    (``test_datasets_tool_byte_identical_on_a_non_empty_live_list``) has already registered a
+    dataset against this SAME shared backend, and nothing in this module has called
+    ``/research/edge-report`` before now — so the registry is genuinely non-empty and the cache is
+    genuinely cold, and this GET naturally returns the not-computed payload rather than the
+    era-5B full-report shape. Proves REST<->MCP byte-identity in exactly that new state, with no
+    seeding of this test's own."""
+    datasets = httpx.get(f"{mcp_env}/research/datasets", timeout=5.0).json()["datasets"]
+    assert len(datasets) >= 1, "an earlier test in this module must have already registered one"
+
     result = await call_tool("edge_report", {})
     rest = httpx.get(f"{mcp_env}/research/edge-report", timeout=5.0)
     assert rest.status_code == 200
     payload = rest.json()
-    assert set(payload) >= {"register", "pnl_min_sample_size", "train", "holdout", "surviving_train_cells"}
+    assert payload.get("status") == "not_computed", (
+        "expected the not-computed shape: registry is non-empty and nothing has warmed the cache"
+    )
+    assert set(payload) == {"status", "detail", "dataset_count", "register", "compute"}
     assert result.isError is False
     assert len(result.content) == 1
     assert result.content[0].text.encode("utf-8") == rest.content, "edge_report not byte-identical"
@@ -555,10 +565,11 @@ async def test_edge_report_tool_byte_identical_to_rest(mcp_env):
 @pytest.mark.anyio
 async def test_edge_report_tool_byte_identical_after_recording_a_real_dataset(mcp_env):
     """The IDENTICAL ``datasets``/``backtests`` "flips from empty to a real state with ZERO MCP
-    code changes" precedent: after recording a real dataset through the live backend, the tool's
-    JSON is still byte-identical to its curl equivalent (still an honest empty ``cells`` list here
-    — PG, the reference fixture's symbol, is not a config-owned panel symbol — but the byte-proxy
-    discipline itself is what this test exists to prove, on a request that now does real work)."""
+    code changes" precedent: after recording ANOTHER real dataset through the live backend, the
+    tool's JSON is still byte-identical to its curl equivalent — still the not-computed shape here
+    (era-fast_wall J-01: nothing in this module ever warms the cache, so the cache stays cold for
+    the rest of the module too) — but the byte-proxy discipline itself is what this test exists to
+    prove, on a request whose ``dataset_count`` has now genuinely changed."""
     recorded = httpx.post(
         f"{mcp_env}/research/datasets",
         json={
diff --git a/apps/frontend/app/structure/page.tsx b/apps/frontend/app/structure/page.tsx
index f3539f1..6c4b671 100644
--- a/apps/frontend/app/structure/page.tsx
+++ b/apps/frontend/app/structure/page.tsx
@@ -27,6 +27,7 @@ import type {
   Dataset,
   DatasetsListResult,
   EdgeReportCell,
+  EdgeReportPayload,
   EdgeReportResponse,
   EdgeReportSurvivingCell,
   LevelsResponse,
@@ -278,6 +279,23 @@ function LoadingPanel({ testid }: { testid: string }) {
   );
 }
 
+// The honest not-computed state (era-fast_wall J-01): a cold cache with a non-empty registry —
+// distinct from `UnavailablePanel` (a fetch/backend failure) and `EmptyState` (a genuinely
+// computed, empty result). Reuses `UnavailablePanel`'s amber degraded-state treatment (no new
+// visual language) with its own testid + its own headline/detail copy; `detail` is the backend's
+// OWN trigger explanation, rendered verbatim — never a frontend-authored string.
+function NotComputedPanel({ detail }: { detail: string }) {
+  return (
+    <div
+      data-testid="edge-report-not-computed"
+      className="rounded-lg border border-amber-800/60 bg-amber-900/20 px-4 py-6 text-center"
+    >
+      <p className="text-sm font-medium text-amber-300">Edge report not computed yet.</p>
+      <p className="mt-1 text-xs text-amber-200/70">{detail}</p>
+    </div>
+  );
+}
+
 // A distinct, honest empty state — its own testid + its own copy every time (never shared, per
 // the interlude's honest-state anti-goal).
 function EmptyState({
@@ -1172,9 +1190,11 @@ export default function StructurePage() {
   const [setupDetailState, setSetupDetailState] = useState<LoadState<SetupEvent>>({ phase: "idle" });
 
   // era-5B J-04 Edge Report state — fetched once on mount, the SAME null-then-resolved pattern.
+  // era-fast_wall J-01: `data` is now the discriminated `EdgeReportPayload` union (a real report
+  // or the honest not-computed shape) -- see the render branch below.
   const [edgeReportResult, setEdgeReportResult] = useState<{
     ok: boolean;
-    data: EdgeReportResponse | null;
+    data: EdgeReportPayload | null;
     error?: string;
   } | null>(null);
 
@@ -1857,6 +1877,8 @@ export default function StructurePage() {
                 testid="edge-report-unavailable"
                 message={edgeReportResult.error ?? "The edge report could not be loaded."}
               />
+            ) : edgeReport.status === "not_computed" ? (
+              <NotComputedPanel detail={edgeReport.detail} />
             ) : (
               <EdgeReportBody report={edgeReport} />
             )}
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 2d9b082..d697e9f 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -10,7 +10,7 @@ import type {
   CreateStudyResult,
   DatasetsListResult,
   DeclareResult,
-  EdgeReportResponse,
+  EdgeReportPayload,
   Hint,
   JournalDetail,
   JournalFilters,
@@ -1143,13 +1143,13 @@ export async function fetchSetupDetail(
 // failure; `data: null` is reserved for a genuine non-200 / unreachable backend.
 export async function fetchEdgeReport(): Promise<{
   ok: boolean;
-  data: EdgeReportResponse | null;
+  data: EdgeReportPayload | null;
   error?: string;
 }> {
   try {
     const res = await fetch(`${API_BASE}/research/edge-report`);
     if (res.ok) {
-      return { ok: true, data: (await res.json()) as EdgeReportResponse };
+      return { ok: true, data: (await res.json()) as EdgeReportPayload };
     }
     let error = "The edge report could not be loaded.";
     try {
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 3b13410..183270a 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1357,4 +1357,24 @@ export interface EdgeReportResponse {
   train: { cells: EdgeReportCell[] };
   holdout: { cells: EdgeReportCell[] };
   surviving_train_cells: EdgeReportSurvivingCell[];
+  status?: undefined;
+}
+
+// GET /research/edge-report — the honest not-computed payload (era-fast_wall J-01): a cold cache
+// key with a non-empty dataset registry. `status` is the sole discriminator against
+// `EdgeReportResponse` above (absent -- `undefined` -- on a real report). `detail` is the
+// backend's OWN trigger explanation, rendered verbatim, never a frontend-authored string.
+// `compute` is always `null` this iteration (no compute manager exists until J-04 -- see
+// `peek_strategy_comparison_report`'s own docstring).
+export interface EdgeReportNotComputed {
+  status: "not_computed";
+  detail: string;
+  dataset_count: number;
+  register: string;
+  compute: null;
 }
+
+// The discriminated union `fetchEdgeReport()` actually returns -- a real report or the
+// not-computed payload. `payload.status === "not_computed"` is the render branch's discriminator
+// (see `structure/page.tsx`'s Edge Report section).
+export type EdgeReportPayload = EdgeReportResponse | EdgeReportNotComputed;
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-fast_wall/telemetry.jsonl   | 6 ++++++
 runs/goal-session-fast_wall/trace/trace.jsonl | 3 +++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
