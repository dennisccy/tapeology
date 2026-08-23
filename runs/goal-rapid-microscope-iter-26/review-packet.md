# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/app/research/micro_join.py b/apps/backend/app/research/micro_join.py
index 471090d0..f1037037 100644
--- a/apps/backend/app/research/micro_join.py
+++ b/apps/backend/app/research/micro_join.py
@@ -584,7 +584,11 @@ def _band_touch_not_enumerated() -> dict:
 
 
 def joinable_corpus_counts(
-    dataset_store: DatasetStore, playbook_store, *, resolver: "BandMapResolver | None" = None
+    dataset_store: DatasetStore,
+    playbook_store,
+    *,
+    resolver: "BandMapResolver | None" = None,
+    band_touch_cache=None,
 ) -> dict:
     """``total``/``playbook_signal_count``/``band_touch_count``/``by_setup_id``/
     ``playbook_integrity_errors`` -- every recorded playbook signal whose ``(symbol, trigger_ts)``
@@ -610,7 +614,21 @@ def joinable_corpus_counts(
     available evidence, so counting its window as joinable would make this number disagree with
     ``micro_readiness``' own ``totals.distinct_datasets`` (which already excludes it) inside one
     payload. ``withheld_excluded`` carries the COUNT -- never the ids -- so the shrink is never
-    silent. Byte-identical (``0``) while nothing is sealed."""
+    silent. Byte-identical (``0``) while nothing is sealed.
+
+    ``band_touch_cache`` (iter-26, ``micro_readiness.MicroBandTouchCache``) is OPTIONAL and
+    defaults to ``None`` -- byte-identical to today's uncached compute (every existing caller)
+    when omitted. When given (and ``resolver`` is also given -- band touches are only ever
+    enumerated with a resolver in hand), each record's touch count is looked up, or computed once
+    and published, keyed on the COMPOSITE ``(dataset_meta["checksum"], resolver.map_key(symbol,
+    window_start_epoch))`` -- never the checksum alone, so a re-warmed/changed band map (a new
+    ``map_key``) is a genuine miss, never a stale hit under the old map (this module's own
+    ``enumerate_band_touches`` already resolves the SAME map at the SAME instant internally, so the
+    externally-computed ``map_key`` here can never disagree with what that function's own
+    ``resolver.resolve`` call would key on). A cache miss still computes through
+    ``enumerate_band_touches`` -- this never fabricates a placeholder count -- and the resolved
+    value is published before moving to the next record. Only warm-path LATENCY changes; the
+    summed ``total_band_touches`` is unaffected (TC-2/TC-3/TC-4)."""
     records, _errors = dataset_store.list()
     records, withheld_excluded = exclude_withheld(records, dataset_store)
     total_playbook = 0
@@ -636,9 +654,19 @@ def joinable_corpus_counts(
     if resolver is None:
         band_touch_count = _band_touch_not_enumerated()
     else:
-        total_band_touches = sum(
-            len(enumerate_band_touches(meta, dataset_store, resolver)) for meta in records
-        )
+        total_band_touches = 0
+        for meta in records:
+            symbol = meta.get("symbol")
+            if band_touch_cache is not None and symbol:
+                checksum = meta["checksum"]
+                map_key = resolver.map_key(symbol, parse_utc_epoch(meta["window_start_utc"]))
+                touch_count = band_touch_cache.lookup(checksum, map_key)
+                if touch_count is None:
+                    touch_count = len(enumerate_band_touches(meta, dataset_store, resolver))
+                    band_touch_cache.publish(checksum, map_key, touch_count)
+            else:
+                touch_count = len(enumerate_band_touches(meta, dataset_store, resolver))
+            total_band_touches += touch_count
         band_touch_count = {"status": BAND_TOUCH_STATUS_ENUMERATED, "count": total_band_touches}
 
     return {
diff --git a/apps/backend/app/research/micro_readiness.py b/apps/backend/app/research/micro_readiness.py
index 40c47509..704e2a71 100644
--- a/apps/backend/app/research/micro_readiness.py
+++ b/apps/backend/app/research/micro_readiness.py
@@ -91,6 +91,8 @@ __all__ = [
     "EXPOSURE_STATE_EXPLORATORY",
     "MicroReadinessCache",
     "resolve_micro_readiness_cache_db_path",
+    "MicroBandTouchCache",
+    "resolve_micro_band_touch_cache_db_path",
     "build_readiness",
 ]
 
@@ -290,6 +292,111 @@ class MicroReadinessCache:
             pass
 
 
+# --- the band-touch count cache (iter-26): the SAME durable-cache contract as MicroReadinessCache
+# above, applied to `micro_join.enumerate_band_touches`'s per-dataset touch count instead of
+# `fallback_frac` -- that walk over every record's own event stream is the ~22s-and-growing
+# uncached cost `joinable_corpus_counts` pays on every warm GET once a resolver is supplied
+# (`micro_join.py`'s own `enumerate_band_touches` docstring: "the expensive event load"). Keyed on
+# the COMPOSITE `(dataset checksum, resolver.map_key(symbol, window_start_epoch))` -- never the
+# checksum alone -- because a dataset's own bytes never change (immutability, rail 9) but the BAND
+# MAP a resolver serves for it can (a re-warmed tradability cache under a new store signature), and
+# a stale hit under the old map would silently under/over-count touches against bands that no
+# longer describe that basis day. Deliberately its own env var, distinct from every sibling durable
+# cache's (the `MicroReadinessCache` docstring above: "the TAPEOLOGY_MICRO_* family").
+_BAND_TOUCH_CACHE_DB_ENV = "TAPEOLOGY_MICRO_BAND_TOUCH_CACHE_DB"
+
+_BAND_TOUCH_SCHEMA = """
+CREATE TABLE IF NOT EXISTS micro_band_touch_cache (
+    checksum     TEXT NOT NULL,
+    map_key      TEXT NOT NULL,
+    touch_count  INTEGER NOT NULL,
+    created_utc  TEXT NOT NULL,
+    PRIMARY KEY (checksum, map_key)
+)
+"""
+
+
+def resolve_micro_band_touch_cache_db_path(dataset_dir: str) -> str:
+    """The band-touch cache DB path resolution policy -- the IDENTICAL env-else-sibling shape
+    ``resolve_micro_readiness_cache_db_path`` above uses, under its own env var:
+    ``TAPEOLOGY_MICRO_BAND_TOUCH_CACHE_DB`` if set, else ``micro_band_touch_cache.db`` co-located as
+    a SIBLING of the caller's dataset-store directory."""
+    override = os.environ.get(_BAND_TOUCH_CACHE_DB_ENV)
+    if override:
+        return override
+    return str(Path(dataset_dir).parent / "micro_band_touch_cache.db")
+
+
+class MicroBandTouchCache:
+    """One durable SQLite row per ``(dataset checksum, resolver.map_key(symbol,
+    window_start_epoch))`` composite key -> its enumerated band-touch COUNT --
+    ``MicroReadinessCache``'s own contract (this module's docstring, above class), applied to a
+    per-record touch count instead of a per-shard ``fallback_frac``. A miss NEVER computes --
+    ``lookup`` has no ``compute_fn``; a corrupted/unreadable DB is a full miss, never a crash; a
+    ``publish`` failure is swallowed, never propagated -- the caller is still holding its own
+    freshly-computed count. Publishes ONLY a resolved count, never a placeholder (goal.md IN SCOPE
+    item 1)."""
+
+    def __init__(self, db_path: str) -> None:
+        self._db_path = str(db_path)
+        if self._db_path != ":memory:":
+            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
+        try:
+            conn = self._connect()
+            try:
+                with conn:
+                    conn.execute(_BAND_TOUCH_SCHEMA)
+            finally:
+                conn.close()
+        except sqlite3.Error:
+            pass  # self-heals: every subsequent lookup/publish independently re-attempts
+
+    @property
+    def db_path(self) -> str:
+        return self._db_path
+
+    def _connect(self) -> sqlite3.Connection:
+        """A FRESH, short-lived connection per call (the ``MicroReadinessCache._connect``/
+        ``TradabilityCache._connect`` precedent)."""
+        conn = sqlite3.connect(
+            self._db_path, check_same_thread=False, timeout=_BUSY_TIMEOUT_MS / 1000.0
+        )
+        conn.row_factory = sqlite3.Row
+        if self._db_path != ":memory:":
+            conn.execute("PRAGMA journal_mode=WAL")
+        conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
+        return conn
+
+    def lookup(self, checksum: str, map_key: str) -> int | None:
+        try:
+            conn = self._connect()
+            try:
+                row = conn.execute(
+                    "SELECT touch_count FROM micro_band_touch_cache WHERE checksum=? AND map_key=?",
+                    (checksum, map_key),
+                ).fetchone()
+            finally:
+                conn.close()
+        except sqlite3.Error:
+            return None
+        return None if row is None else int(row["touch_count"])
+
+    def publish(self, checksum: str, map_key: str, touch_count: int) -> None:
+        try:
+            conn = self._connect()
+            try:
+                with conn:
+                    conn.execute(
+                        "INSERT OR REPLACE INTO micro_band_touch_cache "
+                        "(checksum, map_key, touch_count, created_utc) VALUES (?,?,?,?)",
+                        (checksum, map_key, touch_count, _iso_utc_now()),
+                    )
+            finally:
+                conn.close()
+        except sqlite3.Error:
+            pass
+
+
 # --- the whole readiness aggregation -----------------------------------------------------------------
 
 
@@ -300,6 +407,7 @@ def build_readiness(
     dataset_dir: str,
     playbook_store=None,
     resolver: "BandMapResolver | None" = None,
+    band_touch_cache: "MicroBandTouchCache | None" = None,
 ) -> dict:
     """The whole ``GET /research/desk/micro/readiness`` body -- a pure aggregation over
     ``DatasetStore.list()``'s already-verified records (module docstring). Deterministic and
@@ -321,6 +429,12 @@ def build_readiness(
     is also given -- the ``playbook_store is None`` branch below already answers "nothing was
     checked" honestly for BOTH counts at once, never a mixed state.
 
+    ``band_touch_cache`` (iter-26, ``MicroBandTouchCache`` above) is likewise OPTIONAL, passed
+    straight through to ``micro_join.joinable_corpus_counts`` -- omitting it (every pre-iter-26
+    caller) keeps today's uncached per-record ``enumerate_band_touches`` walk byte-identical;
+    supplying one only changes warm-path LATENCY, never the served ``band_touch_count`` value
+    (goal.md IN SCOPE item 1).
+
     **Sealed-tranche AGGREGATES only (iter-9, spec section 7.5 point 4, r3; widened iteration 11,
     point 7, r5).** A dataset that is part of an UNRESOLVED registered-universe pool gets NO
     per-shard row and NO per-shard ``exposure_state`` here -- its row would carry the symbol,
@@ -490,7 +604,9 @@ def build_readiness(
             "withheld_excluded": 0,
         }
     else:
-        joinable_corpus = joinable_corpus_counts(store, playbook_store, resolver=resolver)
+        joinable_corpus = joinable_corpus_counts(
+            store, playbook_store, resolver=resolver, band_touch_cache=band_touch_cache
+        )
 
     sealed_tranche = {
         "shard_count": sealed_shard_count,
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 8b369bc5..03fa0e1d 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -48,7 +48,13 @@ from .desk_routes import get_playbook_store, get_universe_store
 from .desk_universe import UniverseStore
 from .micro_accessor import ExposureRegistry, resolve_micro_exposure_registry_dir
 from .micro_graduation import EMPTY_LEDGER_MESSAGE, GraduationLedger, list_graduation_families, resolve_micro_graduation_dir
-from .micro_readiness import MicroReadinessCache, build_readiness, resolve_micro_readiness_cache_db_path
+from .micro_readiness import (
+    MicroBandTouchCache,
+    MicroReadinessCache,
+    build_readiness,
+    resolve_micro_band_touch_cache_db_path,
+    resolve_micro_readiness_cache_db_path,
+)
 from .micro_snapshots import (
     MicroSnapshotComputeManager,
     list_snapshot_meta,
@@ -57,11 +63,9 @@ from .micro_snapshots import (
 )
 from .routes import get_bar_index, get_bar_store, get_dataset_store, get_registry, get_study_market_adapter
 from .scout import (
-    GRID_SELECTOR_CAPITULATION_PILOT,
-    GRID_SELECTOR_DELTA_DIVERGENCE_PILOT,
-    GRID_SELECTOR_RANGE_WALL_PILOT,
     ScoutComputeManager,
     list_scout_families,
+    _PILOT_GRID_SELECTORS,
 )
 from .scout_ledger import ScoutLedger, resolve_scout_ledger_dir
 from .tick_recorder import (
@@ -87,10 +91,23 @@ def get_micro_readiness_cache() -> MicroReadinessCache:
     return MicroReadinessCache(resolve_micro_readiness_cache_db_path(CONFIG.dataset_dir_resolved()))
 
 
+def get_micro_band_touch_cache() -> MicroBandTouchCache:
+    """iter-26: the durable per-``(dataset checksum, resolver.map_key(...))`` band-touch-count
+    cache -- the SAME config-derived, env-overridable path shape as
+    ``get_micro_readiness_cache`` above, under its own ``TAPEOLOGY_MICRO_BAND_TOUCH_CACHE_DB`` env
+    var (never reusing that sibling's env var -- ``micro_readiness.py``'s own module docstring, the
+    ``TAPEOLOGY_MICRO_*`` family). A FastAPI dependency so tests can override it outright or point
+    it at a temp path via the env var -- the established pattern."""
+    return MicroBandTouchCache(
+        resolve_micro_band_touch_cache_db_path(CONFIG.dataset_dir_resolved())
+    )
+
+
 @router.get("/readiness")
 def get_micro_readiness(
     dataset_store: DatasetStore = Depends(get_dataset_store),
     cache: MicroReadinessCache = Depends(get_micro_readiness_cache),
+    band_touch_cache: MicroBandTouchCache = Depends(get_micro_band_touch_cache),
     playbook_store: PlaybookStore = Depends(get_playbook_store),
     bar_store: BarStore = Depends(get_bar_store),
 ) -> dict:
@@ -110,7 +127,12 @@ def get_micro_readiness(
     OWN construction call, verbatim (``BandMapResolver(bar_store, CONFIG)`` defaults to
     ``compute=False``, so this GET never computes a tradable map it does not already hold -- T-8).
     It materializes ``joinable_corpus.band_touch_count`` from the ``not_enumerated`` sentinel to a
-    real int (``micro_join.py``'s own docstring); nothing else in this payload changes shape."""
+    real int (``micro_join.py``'s own docstring); nothing else in this payload changes shape.
+
+    iter-26: ``band_touch_cache`` is threaded straight through to ``build_readiness`` -- only the
+    warm-path LATENCY of that materialization changes (the ~22s-and-growing uncached
+    ``enumerate_band_touches`` walk over every joinable dataset's raw event stream); the served
+    ``band_touch_count`` value is byte-identical either way."""
     resolver = BandMapResolver(bar_store, CONFIG)
     return build_readiness(
         dataset_store,
@@ -118,6 +140,7 @@ def get_micro_readiness(
         dataset_dir=CONFIG.dataset_dir_resolved(),
         playbook_store=playbook_store,
         resolver=resolver,
+        band_touch_cache=band_touch_cache,
     )
 
 
@@ -277,14 +300,25 @@ class ScoutComputeRequest(BaseModel):
 
 
 # grid_selector -> which of resolver/playbook_store this route must construct for it -- the SAME
-# structure_context.kind split ``scout._PILOT_GRID_SELECTORS`` already encodes, read here by VALUE
-# (never a second, independently-maintained selector->kind table) so the route stays selector-aware
-# rather than "any non-default selector gets a resolver", which stopped being true the moment a
-# playbook_signal-kind selector existed.
-_BAND_TOUCH_PILOT_SELECTORS = frozenset(
-    {GRID_SELECTOR_RANGE_WALL_PILOT, GRID_SELECTOR_DELTA_DIVERGENCE_PILOT}
-)
-_PLAYBOOK_SIGNAL_PILOT_SELECTORS = frozenset({GRID_SELECTOR_CAPITULATION_PILOT})
+# structure_context.kind split ``scout._PILOT_GRID_SELECTORS`` already encodes. iter-26: derived by
+# FILTERING that one canonical table (never a second, independently-maintained selector->kind
+# literal -- rail 6, single source of truth) so the route stays selector-aware rather than "any
+# non-default selector gets a resolver", which stopped being true the moment a playbook_signal-kind
+# selector existed.
+def _pilot_selectors_by_kind(
+    kind: str, source: "dict[str, tuple[str, str]] | None" = None
+) -> frozenset[str]:
+    """The selector set for one ``structure_context.kind``, filter-derived from ``source`` (default
+    ``None`` -- the LIVE ``scout._PILOT_GRID_SELECTORS`` table, the real route path) each time it
+    is called. Deliberately a function called at each use site, never a module-level literal
+    computed once at import -- a frozen-at-import constant would only happen to equal today's
+    values rather than genuinely tracking the source table (a test extending a LOCAL COPY of
+    ``scout._PILOT_GRID_SELECTORS`` and passing it as ``source`` proves this: the derived set grows
+    to include the synthetic entry, which a constant snapshot could never do)."""
+    table = _PILOT_GRID_SELECTORS if source is None else source
+    return frozenset(
+        selector for selector, (_study_id, selector_kind) in table.items() if selector_kind == kind
+    )
 
 
 @router.post("/scout/compute")
@@ -317,9 +351,13 @@ def trigger_scout_compute(
     goal.md IN SCOPE item 6 requires -- previously that stage existed in source but ran only inside
     a unit test."""
     grid_selector = body.grid if body is not None else None
-    resolver = BandMapResolver(bar_store, CONFIG) if grid_selector in _BAND_TOUCH_PILOT_SELECTORS else None
+    resolver = (
+        BandMapResolver(bar_store, CONFIG)
+        if grid_selector in _pilot_selectors_by_kind("band_touch")
+        else None
+    )
     playbook_store_for_trigger = (
-        playbook_store if grid_selector in _PLAYBOOK_SIGNAL_PILOT_SELECTORS else None
+        playbook_store if grid_selector in _pilot_selectors_by_kind("playbook_signal") else None
     )
     # iter-21 audit fix B1: the pilot run's walk-forward floor-check stage reads the SAME durable
     # exposure registry `POST /walkforward/compute` already depends on (never a second, differently
diff --git a/apps/backend/tests/test_micro_join.py b/apps/backend/tests/test_micro_join.py
index 86907faa..ed9cfe78 100644
--- a/apps/backend/tests/test_micro_join.py
+++ b/apps/backend/tests/test_micro_join.py
@@ -21,6 +21,7 @@ from __future__ import annotations
 
 import hashlib
 import inspect
+import sqlite3
 from datetime import datetime, timezone
 from pathlib import Path
 
@@ -31,6 +32,7 @@ from app.providers.base import QuoteEvent, Side, TradeEvent
 from app.research import desk_playbook as desk_playbook_module
 from app.research import desk_playbook_context as desk_playbook_context_module
 from app.research import micro_join
+from app.research import micro_readiness as micro_readiness_module
 from app.research import vault
 from app.research.datasets import DatasetStore, parse_utc_epoch
 from app.research.desk_playbook import PlaybookStore, playbook_parameters
@@ -546,6 +548,126 @@ def test_tc9_joinable_corpus_counts_excludes_a_withheld_shard_from_band_touch_co
     assert counts["withheld_excluded"] == 1
 
 
+# --- iter-26: the band-touch cache wired into joinable_corpus_counts (TC-2/TC-3/TC-4) ----------------
+
+
+class _StubBarStore:
+    """A ``BandMapResolver`` dependency stub whose ``list()`` output is fully caller-controlled --
+    lets a test construct TWO resolvers with genuinely different store signatures (hence genuinely
+    different ``map_key``s) without depending on ``BandMapResolver``'s own internal signature
+    formula (``_EmptyBarStore`` above is the degenerate, always-empty special case of this)."""
+
+    def __init__(self, records: list[dict]):
+        self.root = "/tmp/does-not-exist-micro-join-test"
+        self._records = records
+
+    def list(self):
+        return list(self._records), []
+
+
+def test_tc2_a_cold_lookup_computes_and_publishes_exactly_one_row_for_the_composite_key(tmp_path):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    meta = _plant_touch_timeline(dataset_store)
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    resolver = _resolver(tmp_path)
+    window_start_epoch = parse_utc_epoch(meta["window_start_utc"])
+    map_key = resolver.map_key("TQE", window_start_epoch)
+    resolver._cache.publish(map_key, {"basis_day": "2026-06-08", "bands": [_TOUCH_BAND]})
+    band_touch_cache = micro_readiness_module.MicroBandTouchCache(str(tmp_path / "band_touch_cache.db"))
+    assert band_touch_cache.lookup(meta["checksum"], map_key) is None  # cold
+
+    counts = micro_join.joinable_corpus_counts(
+        dataset_store, playbook_store, resolver=resolver, band_touch_cache=band_touch_cache
+    )
+
+    # The hand-computed touch count for this fixture's known band map (the SAME 3 touches
+    # ``test_tc9_joinable_corpus_counts_materializes_band_touch_count_with_a_resolver`` above
+    # asserts uncached).
+    assert counts["band_touch_count"] == {"status": micro_join.BAND_TOUCH_STATUS_ENUMERATED, "count": 3}
+    assert band_touch_cache.lookup(meta["checksum"], map_key) == 3
+
+    conn = sqlite3.connect(band_touch_cache.db_path)
+    try:
+        row_count = conn.execute("SELECT COUNT(*) FROM micro_band_touch_cache").fetchone()[0]
+    finally:
+        conn.close()
+    assert row_count == 1  # exactly one row for this single-dataset corpus
+
+
+def test_tc3_a_warm_second_call_skips_load_events_and_serves_the_unchanged_count(tmp_path, monkeypatch):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    meta = _plant_touch_timeline(dataset_store)
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    resolver = _resolver(tmp_path)
+    window_start_epoch = parse_utc_epoch(meta["window_start_utc"])
+    resolver._cache.publish(
+        resolver.map_key("TQE", window_start_epoch), {"basis_day": "2026-06-08", "bands": [_TOUCH_BAND]}
+    )
+    band_touch_cache = micro_readiness_module.MicroBandTouchCache(str(tmp_path / "band_touch_cache.db"))
+
+    original_load_events = dataset_store.load_events
+    call_count = {"n": 0}
+
+    def _spy_load_events(dataset_id):
+        call_count["n"] += 1
+        return original_load_events(dataset_id)
+
+    monkeypatch.setattr(dataset_store, "load_events", _spy_load_events)
+
+    first = micro_join.joinable_corpus_counts(
+        dataset_store, playbook_store, resolver=resolver, band_touch_cache=band_touch_cache
+    )
+    assert call_count["n"] == 1
+    assert first["band_touch_count"] == {"status": micro_join.BAND_TOUCH_STATUS_ENUMERATED, "count": 3}
+
+    second = micro_join.joinable_corpus_counts(
+        dataset_store, playbook_store, resolver=resolver, band_touch_cache=band_touch_cache
+    )
+    assert call_count["n"] == 1  # warm -- no second event read
+    assert second["band_touch_count"] == first["band_touch_count"]
+
+
+def test_tc4_a_re_warmed_map_key_is_a_genuine_miss_never_a_stale_serve(tmp_path):
+    """A dataset's band map re-warmed under a NEW ``resolver.map_key`` -- a genuinely different
+    bar-store signature, the same mechanism a real tradability re-warm produces -- is never served
+    the OLD key's stale cached count; the old key's own row stays intact and untouched."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    meta = _plant_touch_timeline(dataset_store)
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    shared_trad_cache = TradabilityCache(str(tmp_path / "trad.db"))
+    band_touch_cache = micro_readiness_module.MicroBandTouchCache(str(tmp_path / "band_touch_cache.db"))
+    window_start_epoch = parse_utc_epoch(meta["window_start_utc"])
+
+    resolver_v1 = BandMapResolver(_StubBarStore([]), CONFIG, cache=shared_trad_cache)
+    map_key_v1 = resolver_v1.map_key("TQE", window_start_epoch)
+    resolver_v1._cache.publish(map_key_v1, {"basis_day": "2026-06-08", "bands": [_TOUCH_BAND]})
+
+    first = micro_join.joinable_corpus_counts(
+        dataset_store, playbook_store, resolver=resolver_v1, band_touch_cache=band_touch_cache
+    )
+    assert first["band_touch_count"] == {"status": micro_join.BAND_TOUCH_STATUS_ENUMERATED, "count": 3}
+    assert band_touch_cache.lookup(meta["checksum"], map_key_v1) == 3
+
+    # Re-warm: a genuinely different bar-store signature for the SAME symbol -> a genuinely
+    # different map_key (never the checksum alone -- the dataset's own bytes never changed).
+    resolver_v2 = BandMapResolver(
+        _StubBarStore([{"symbol": "TQE", "timeframe": "1d", "id": "bar-1", "checksum": "c1"}]),
+        CONFIG, cache=shared_trad_cache,
+    )
+    map_key_v2 = resolver_v2.map_key("TQE", window_start_epoch)
+    assert map_key_v2 != map_key_v1
+    assert band_touch_cache.lookup(meta["checksum"], map_key_v2) is None  # a genuine miss
+
+    # Nothing published under the new key -- an honest re-resolve (never a fabricated wall).
+    second = micro_join.joinable_corpus_counts(
+        dataset_store, playbook_store, resolver=resolver_v2, band_touch_cache=band_touch_cache
+    )
+
+    assert second["band_touch_count"] == {"status": micro_join.BAND_TOUCH_STATUS_ENUMERATED, "count": 0}
+    assert band_touch_cache.lookup(meta["checksum"], map_key_v2) == 0
+    assert band_touch_cache.lookup(meta["checksum"], map_key_v1) == 3  # untouched, old key intact
+
+
 # --- joinable_corpus_counts (micro_readiness.py's new field; TC-5's own computation) -----------------
 
 
diff --git a/apps/backend/tests/test_micro_readiness.py b/apps/backend/tests/test_micro_readiness.py
index 482e3ba5..de124d52 100644
--- a/apps/backend/tests/test_micro_readiness.py
+++ b/apps/backend/tests/test_micro_readiness.py
@@ -32,8 +32,10 @@ from app.research.micro_readiness import (
     SPLIT_PROVENANCE_HAND_ASSIGNED,
     WF_TEST_MIN_SESSIONS,
     WF_TRAIN_MIN_SESSIONS,
+    MicroBandTouchCache,
     MicroReadinessCache,
     build_readiness,
+    resolve_micro_band_touch_cache_db_path,
     resolve_micro_readiness_cache_db_path,
 )
 from app.research.bars import BarStore
@@ -41,7 +43,7 @@ from app.research.desk_playbook import PlaybookStore, playbook_parameters
 from app.research.desk_playbook_context import BandMapResolver
 from app.research.desk_routes import get_playbook_store
 from app.research.micro_join import BAND_TOUCH_STATUS_ENUMERATED, joinable_corpus_counts
-from app.research.micro_routes import get_micro_readiness_cache
+from app.research.micro_routes import get_micro_band_touch_cache, get_micro_readiness_cache
 from app.research.referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS
 from app.research.routes import get_bar_store, get_dataset_store
 from app.research.tradability_cache import TradabilityCache, resolve_tradability_cache_db_path
@@ -91,6 +93,10 @@ def _plant_dataset(
 def client(tmp_path):
     dataset_store = DatasetStore(tmp_path / "datasets")
     cache = MicroReadinessCache(str(tmp_path / "cache.db"))
+    # iter-26: the route now also depends on the band-touch cache -- a tmp_path-scoped one, the
+    # SAME hermeticity discipline as every other override below (never the real, ambient
+    # `.data`-sibling `micro_band_touch_cache.db`).
+    band_touch_cache = MicroBandTouchCache(str(tmp_path / "band_touch_cache.db"))
     # J-03: the route now also depends on a playbook store (the joinable_corpus field) -- a
     # tmp_path-scoped, empty-by-default one, so this fixture's existing hermeticity contract is
     # unaffected (never the real, ambient .data/playbook directory).
@@ -102,12 +108,14 @@ def client(tmp_path):
     bar_store = BarStore(tmp_path / "bars")
     app.dependency_overrides[get_dataset_store] = lambda: dataset_store
     app.dependency_overrides[get_micro_readiness_cache] = lambda: cache
+    app.dependency_overrides[get_micro_band_touch_cache] = lambda: band_touch_cache
     app.dependency_overrides[get_playbook_store] = lambda: playbook_store
     app.dependency_overrides[get_bar_store] = lambda: bar_store
     with TestClient(app) as c:
         yield c, dataset_store, cache
     app.dependency_overrides.pop(get_dataset_store, None)
     app.dependency_overrides.pop(get_micro_readiness_cache, None)
+    app.dependency_overrides.pop(get_micro_band_touch_cache, None)
     app.dependency_overrides.pop(get_playbook_store, None)
     app.dependency_overrides.pop(get_bar_store, None)
 
@@ -259,6 +267,71 @@ def test_cache_survives_a_corrupted_db_file_as_a_full_miss(tmp_path):
     cache.publish("anything", 0.5)  # swallowed, never raises
 
 
+# --- iter-26: MicroBandTouchCache -- composite-key lookup/publish round trip (TC-2/TC-4/TC-5) --------
+
+
+def test_resolve_micro_band_touch_cache_db_path_defaults_to_a_sibling_file(tmp_path):
+    assert resolve_micro_band_touch_cache_db_path(str(tmp_path / "datasets")) == str(
+        tmp_path / "micro_band_touch_cache.db"
+    )
+
+
+def test_resolve_micro_band_touch_cache_db_path_honors_the_env_override(tmp_path, monkeypatch):
+    override = str(tmp_path / "elsewhere" / "band_touch_cache.db")
+    monkeypatch.setenv("TAPEOLOGY_MICRO_BAND_TOUCH_CACHE_DB", override)
+    assert resolve_micro_band_touch_cache_db_path(str(tmp_path / "datasets")) == override
+
+
+def test_band_touch_cache_lookup_is_none_on_a_genuine_miss(tmp_path):
+    cache = MicroBandTouchCache(str(tmp_path / "band_touch_cache.db"))
+    assert cache.lookup("no-such-checksum", "no-such-map-key") is None
+
+
+def test_band_touch_cache_publish_then_lookup_round_trips(tmp_path):
+    cache = MicroBandTouchCache(str(tmp_path / "band_touch_cache.db"))
+    cache.publish("checksum-a", "map-key-a", 3)
+    assert cache.lookup("checksum-a", "map-key-a") == 3
+
+
+def test_band_touch_cache_keys_on_the_composite_never_the_checksum_alone(tmp_path):
+    """TC-4's own claim, at the class level: a genuinely different ``map_key`` under the SAME
+    checksum is a fresh miss -- the whole reason this cache is keyed on the composite
+    ``(checksum, map_key)``, never the checksum alone (a dataset's own bytes never change, but the
+    band map a resolver serves for it can)."""
+    cache = MicroBandTouchCache(str(tmp_path / "band_touch_cache.db"))
+    cache.publish("checksum-a", "map-key-old", 3)
+    assert cache.lookup("checksum-a", "map-key-new") is None
+    cache.publish("checksum-a", "map-key-new", 7)
+    assert cache.lookup("checksum-a", "map-key-old") == 3  # untouched
+    assert cache.lookup("checksum-a", "map-key-new") == 7
+
+
+def test_band_touch_cache_survives_a_corrupted_db_file_as_a_full_miss(tmp_path):
+    db_path = tmp_path / "band_touch_cache.db"
+    db_path.write_text("not a sqlite file")
+    cache = MicroBandTouchCache(str(db_path))
+    assert cache.lookup("anything", "any-key") is None
+    cache.publish("anything", "any-key", 5)  # swallowed, never raises
+
+
+def test_readiness_route_survives_a_corrupted_band_touch_cache_db_as_a_full_miss(client, tmp_path):
+    """TC-5's route-level claim: a corrupted band-touch cache DB file never turns
+    ``GET /research/desk/micro/readiness`` into a 500 -- the request still returns HTTP 200 with a
+    freshly-computed ``band_touch_count`` (mirroring ``MicroReadinessCache``'s own self-heal
+    contract, proven at the route above for ``fallback_frac``)."""
+    c, store, _cache = client
+    _plant_dataset(store, symbol="AAPL")
+    db_path = tmp_path / "band_touch_cache.db"
+    db_path.write_text("not a sqlite file")
+
+    resp = c.get("/research/desk/micro/readiness")
+
+    assert resp.status_code == 200
+    body = resp.json()
+    assert body["joinable_corpus"]["band_touch_count"]["status"] == BAND_TOUCH_STATUS_ENUMERATED
+    assert body["joinable_corpus"]["band_touch_count"]["count"] == 0  # honest -- no band map published
+
+
 # --- TC-6: a hand-corrupted legacy dataset is surfaced, never dropped, never a crash -----------------
 
 
diff --git a/apps/backend/tests/test_scout.py b/apps/backend/tests/test_scout.py
index 172f6fb1..033027bd 100644
--- a/apps/backend/tests/test_scout.py
+++ b/apps/backend/tests/test_scout.py
@@ -10,6 +10,7 @@ codebase uses throughout (``test_micro_features.py``'s own precedent)."""
 
 from __future__ import annotations
 
+import inspect
 import json
 import shutil
 import tempfile
@@ -28,6 +29,7 @@ from app.research import scout, scout_ledger
 from app.research.datasets import DatasetStore, parse_utc_epoch
 from app.research.desk_playbook import PlaybookStore, playbook_parameters
 from app.research.desk_playbook_context import BandMapResolver
+from app.research import micro_routes
 from app.research.micro_routes import (
     get_scout_compute_manager,
     get_scout_ledger_dir,
@@ -1869,3 +1871,60 @@ def test_iter22_cli_range_wall_pilot_grid_produces_the_screen_and_floor_check_ro
     assert screen_row["structure_context"]["kind"] == "band_touch"
     assert wf_row["stage"] == "walkforward_floor_check"
     assert wf_row["candidate_id"] == screen_row["candidate_id"]
+
+
+# --- iter-26 TC-6: the pilot selector->kind table is derived, not restated -------------------------
+#
+# micro_routes.py used to hand-restate scout._PILOT_GRID_SELECTORS as two separate hand-written
+# frozensets (_BAND_TOUCH_PILOT_SELECTORS / _PLAYBOOK_SIGNAL_PILOT_SELECTORS). It now derives both
+# by filtering the ONE canonical table at call time via micro_routes._pilot_selectors_by_kind
+# (single source of truth, rail 6).
+
+
+def test_tc6a_derived_selector_sets_equal_todays_known_selector_sets():
+    """(a) the derived frozensets equal today's known selector sets."""
+    assert micro_routes._pilot_selectors_by_kind("band_touch") == {
+        scout.GRID_SELECTOR_RANGE_WALL_PILOT,
+        scout.GRID_SELECTOR_DELTA_DIVERGENCE_PILOT,
+    }
+    assert micro_routes._pilot_selectors_by_kind("playbook_signal") == {
+        scout.GRID_SELECTOR_CAPITULATION_PILOT,
+    }
+
+
+def test_tc6b_a_synthetic_third_entry_in_a_local_copy_grows_the_derived_set():
+    """(b) a synthetic third `kind="band_touch"` entry, added to a LOCAL COPY of
+    ``scout._PILOT_GRID_SELECTORS`` (never the real module table -- this test never monkeypatches
+    ``scout`` itself), is reflected in the derived frozenset when that copy is passed explicitly as
+    ``source`` -- proving genuine runtime derivation, not a frozen-at-import constant that only
+    happens to equal today's values."""
+    local_copy = dict(scout._PILOT_GRID_SELECTORS)
+    local_copy["synthetic_band_touch_pilot"] = ("synthetic_study", "band_touch")
+
+    derived = micro_routes._pilot_selectors_by_kind("band_touch", source=local_copy)
+
+    assert derived == {
+        scout.GRID_SELECTOR_RANGE_WALL_PILOT,
+        scout.GRID_SELECTOR_DELTA_DIVERGENCE_PILOT,
+        "synthetic_band_touch_pilot",
+    }
+    # The REAL route path (no explicit source) is untouched by the local copy above -- it still
+    # reads only the two genuine band_touch selectors.
+    assert micro_routes._pilot_selectors_by_kind("band_touch") == {
+        scout.GRID_SELECTOR_RANGE_WALL_PILOT,
+        scout.GRID_SELECTOR_DELTA_DIVERGENCE_PILOT,
+    }
+
+
+def test_tc6c_micro_routes_has_no_second_hand_written_selector_literal():
+    """(c) a source-scan guard: ``micro_routes.py`` never hardcodes a second copy of any pilot
+    selector's own string id -- the ONLY legitimate way this route module may know a selector's
+    identity is by reading it, at runtime, off the one canonical
+    ``scout._PILOT_GRID_SELECTORS`` table (via ``_pilot_selectors_by_kind``), never by restating
+    its literal value."""
+    source = Path(inspect.getsourcefile(micro_routes)).read_text()
+    for grid_selector_value in scout._PILOT_GRID_SELECTORS:
+        assert grid_selector_value not in source, (
+            f"micro_routes.py hand-restates the selector literal {grid_selector_value!r} -- it "
+            "must only ever be read off scout._PILOT_GRID_SELECTORS"
+        )
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 7 +++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl | 2 ++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
