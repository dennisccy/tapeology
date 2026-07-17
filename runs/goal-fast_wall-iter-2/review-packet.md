# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 9. Shown in full: 9.

```diff
diff --git a/apps/backend/app/research/bars.py b/apps/backend/app/research/bars.py
index 5b463f2..eba6d0b 100644
--- a/apps/backend/app/research/bars.py
+++ b/apps/backend/app/research/bars.py
@@ -15,11 +15,15 @@ Disciplines (each an anti-goal or a J-01 acceptance clause):
     ``POST /research/bars`` route after a real Alpaca ``fetch_bars`` call. Nothing in the
     watch/stream path imports this module — the live cockpit's tape is never persisted here either
     (no ambient recording).
-  * **Checksummed + verified on EVERY load.** ``meta.checksum`` is a sha256 over the bar-series
-    CONTENT (symbol + timeframe + feed + the ordered candles) computed at registration; a second
-    whole-record checksum covers every metadata byte. Both are recomputed on every load — a
-    corrupted or tampered file raises the explicit ``BarSeriesIntegrityError``, never silence,
-    never a fabricated series.
+  * **Checksummed + re-verified on every content change (stat-keyed).** ``meta.checksum`` is a
+    sha256 over the bar-series CONTENT (symbol + timeframe + feed + the ordered candles) computed
+    at registration; a second whole-record checksum covers every metadata byte. era-fast_wall J-02:
+    a module-level, stat-keyed (``path``, ``st_size``, ``st_mtime_ns``) cache serves an ALREADY
+    fully-verified record with zero I/O while a file's stat is unchanged; ANY stat mismatch — the
+    only way "unchanged" can be honestly claimed — re-runs the full verifier, recomputing BOTH
+    checksums exactly as before caching existed. A corrupted or tampered file raises the explicit
+    ``BarSeriesIntegrityError`` on that re-verify — never silence, never a fabricated series, and
+    never cached (only a successful verify is ever published).
   * **Immutable — structurally.** No update/delete function exists anywhere in this module
     (immutability is structural, not policed). The only mutation is ``record``, and it REFUSES
     content that is already registered: re-recording the same series raises the 409-style
@@ -36,6 +40,7 @@ from __future__ import annotations
 
 import hashlib
 import json
+import time
 import uuid
 from dataclasses import dataclass
 from datetime import datetime, timezone
@@ -125,16 +130,59 @@ class _LoadedBarSeries:
     rows: list[dict]
 
 
+# --- era-fast_wall J-02: the module-level stat-keyed verified-record cache ----------------------
+# Mirrors ``setups.py``'s ``_SCAN_CACHE`` atomic-publish + read-local-reference-before-inspect
+# discipline (see that module's own block comment for the full torn-read rationale), adapted from
+# ONE remembered slot to a per-file dict: a module global, not an instance attribute, because
+# ``BarStore`` is constructed fresh per FastAPI dependency call and has no natural long-lived
+# instance to hang a cache off. Each entry is an immutable tuple ``(st_size, st_mtime_ns,
+# _LoadedBarSeries)`` published via a SINGLE dict-key assignment — CPython's GIL makes that one
+# bytecode op atomic, so a concurrent reader (``_VERIFIED_CACHE.get(path)``, read into a local
+# ONCE before inspection) always observes either the complete prior entry or the complete new one,
+# never a torn value. A concurrent miss on multiple threads only ever costs a redundant, harmless
+# recompute (``_load`` is a pure function of the file's bytes) — never a corrupted cache.
+#
+# Key: the absolute file path (``str(Path)``) -- distinct roots (e.g. different ``tmp_path``
+# test directories) can never collide. Value: ``(st_size, st_mtime_ns, _LoadedBarSeries)`` — ANY
+# stat mismatch on a later read is treated as a miss and re-verifies in full; an integrity error
+# is never cached (only a SUCCESSFUL ``_load`` result is ever published). See ``_cached_load``
+# below for the ~2s racy-write guard that additionally refuses to publish a just-written file.
+_VERIFIED_CACHE: dict[str, tuple[int, int, _LoadedBarSeries]] = {}
+
+# A file whose mtime is within this many seconds of "now" (at read time) is never published to the
+# cache — the guard against a same-granularity rewrite being served stale (two writes landing
+# within one mtime-resolution tick could otherwise be indistinguishable by stat alone).
+_RACY_WRITE_GUARD_SECONDS = 2.0
+
+
+def _reset_verified_cache_for_tests() -> None:
+    """Test-only: clears the module-level verified-record cache. Never called from any production
+    code path — exists solely so tests (and the autouse ``conftest.py`` fixture) can guarantee no
+    cross-test cache leakage (TC-12)."""
+    _VERIFIED_CACHE.clear()
+
+
 class BarStore:
     """File-based store rooted at the config-owned bar directory — the ONE reader/writer.
 
     Construction is cheap (no I/O); the directory is created on the first ``record``. Every read
-    path (``get`` / ``list`` / ``load_bars``) goes through the same verified ``_load`` — the
-    checksum is recomputed on EVERY load, with no bypass (the ``DatasetStore`` pattern)."""
+    path (``get`` / ``list`` / ``load_bars``) goes through the same verified ``_load`` via the
+    stat-keyed cache (``_cached_load``, era-fast_wall J-02) — a stat match serves an already
+    fully-verified record with zero I/O; ANY stat mismatch re-runs ``_load`` in full, recomputing
+    both checksums with no bypass (the ``DatasetStore`` pattern)."""
 
     def __init__(self, root: str | Path) -> None:
         self._root = Path(root)
 
+    @property
+    def root(self) -> Path:
+        """The resolved root directory this store reads/writes (era-fast_wall J-02, TC-11) —
+        public and read-only; no prior public accessor existed for this (only the private
+        ``self._root``). Exposed so a future sibling-path consumer (e.g. a durable cache rooted
+        beside the bar directory) can derive its own path without reaching into a private
+        attribute."""
+        return self._root
+
     # --- verified load (the one loader; no unverified path exists) ------------------------------
 
     def _path(self, bar_series_id: str) -> Path:
@@ -175,33 +223,67 @@ class BarStore:
             )
         return _LoadedBarSeries(meta=meta, rows=rows)
 
+    def _cached_load(self, path: Path) -> _LoadedBarSeries:
+        """era-fast_wall J-02 — the stat-keyed cache-or-verify wrapper around ``_load``, consulted
+        by every reader (``get``/``list``/``load_bars``, via ``_load_by_id`` and ``list`` below).
+        A stat match (``st_size`` AND ``st_mtime_ns`` both unchanged since the cached publish)
+        serves the already-verified record with ZERO additional I/O; any mismatch — including a
+        first-ever read — re-runs the full ``_load`` verifier unchanged. An integrity error is
+        NEVER cached (only a successful ``_load`` result is ever published), so a corrupted file
+        re-verifies — and re-fails — on every subsequent call until it is fixed. A file whose
+        mtime is within ``_RACY_WRITE_GUARD_SECONDS`` of "now" is never published (nor served from
+        a stale earlier publish, since the mismatch check already forces a fresh verify) — the
+        guard against a same-mtime-granularity rewrite being served stale."""
+        try:
+            st = path.stat()
+        except OSError:
+            # Let the real loader raise its own explicit, typed error for a vanished/unreadable
+            # file — the identical failure this call would have hit uncached.
+            return self._load(path)
+
+        key = str(path)
+        cached = _VERIFIED_CACHE.get(key)  # read-local-reference-before-inspect
+        if cached is not None and cached[0] == st.st_size and cached[1] == st.st_mtime_ns:
+            return cached[2]
+
+        loaded = self._load(path)  # the full verifier — unchanged, never bypassed
+
+        now_ns = time.time_ns()
+        if (now_ns - st.st_mtime_ns) >= _RACY_WRITE_GUARD_SECONDS * 1_000_000_000:
+            _VERIFIED_CACHE[key] = (st.st_size, st.st_mtime_ns, loaded)  # single atomic rebind
+        return loaded
+
     def _load_by_id(self, bar_series_id: str) -> _LoadedBarSeries:
         path = self._path(bar_series_id)
         if not path.exists():
             raise BarSeriesNotFound(f"no bar series with id '{bar_series_id}'")
-        return self._load(path)
+        return self._cached_load(path)
 
     # --- reads -----------------------------------------------------------------------------------
 
     def get(self, bar_series_id: str) -> dict:
         """One bar series' metadata WITH its ordered OHLC candles embedded (verified load) — bar
         series are small by construction, so (unlike tick datasets) the candles are served
-        directly rather than through a separate accessor. ``BarSeriesNotFound`` for an unknown id."""
+        directly rather than through a separate accessor. ``BarSeriesNotFound`` for an unknown id.
+        era-fast_wall J-02: ``bars`` is a fresh list of fresh per-row dict COPIES on every call
+        (never the cached list/dicts themselves), so a caller mutating the returned structure can
+        never poison a later cached read (TC-6)."""
         loaded = self._load_by_id(bar_series_id)
-        return {**loaded.meta, "bars": list(loaded.rows)}
+        return {**loaded.meta, "bars": [dict(row) for row in loaded.rows]}
 
     def list(self) -> tuple[list[dict], list[dict]]:
         """Every bar series' metadata + candles (each file verified), oldest first, plus an
         EXPLICIT error row per file that failed verification — a corrupt file is surfaced, never
-        silently hidden and never served as data."""
+        silently hidden and never served as data. era-fast_wall J-02: routed through the same
+        stat-keyed cache as ``get`` (per-row copies here too — see ``get``'s docstring)."""
         if not self._root.exists():
             return [], []
         records: list[dict] = []
         errors: list[dict] = []
         for path in sorted(self._root.glob("*.json")):
             try:
-                loaded = self._load(path)
-                records.append({**loaded.meta, "bars": list(loaded.rows)})
+                loaded = self._cached_load(path)
+                records.append({**loaded.meta, "bars": [dict(row) for row in loaded.rows]})
             except BarSeriesIntegrityError as exc:
                 errors.append({"file": path.name, "error": str(exc)})
         records.sort(key=lambda meta: (meta.get("created_utc", ""), meta.get("id", "")))
diff --git a/apps/backend/app/research/datasets.py b/apps/backend/app/research/datasets.py
index ea6f15f..35d5f7d 100644
--- a/apps/backend/app/research/datasets.py
+++ b/apps/backend/app/research/datasets.py
@@ -14,11 +14,19 @@ Disciplines (each an anti-goal or a J-02 acceptance clause):
     (the same source resolution studies use: the committed keyless reference window, or an
     arbitrary window through the EXISTING adapter fetch seam). Nothing in the watch/stream path
     imports this module — the live cockpit's tape is never persisted (no ambient recording).
-  * **Checksummed + verified on EVERY load.** ``meta.checksum`` is a sha256 over the tape
+  * **Checksummed + re-verified on every content change (stat-keyed) for ``get``/``list`` — every
+    load, forever, for ``load_events``/``replay``.** ``meta.checksum`` is a sha256 over the tape
     CONTENT (symbol + feed + anchor + events) computed at registration; a second whole-record
-    checksum covers every metadata byte INCLUDING the split tag. Both are recomputed on every
-    load — a corrupted or tampered file (even a hand-edited split) raises the explicit
-    ``DatasetIntegrityError``, never silence, never a fabricated dataset.
+    checksum covers every metadata byte INCLUDING the split tag. era-fast_wall J-02:
+    ``get``/``list`` are the ONLY readers routed through a module-level, stat-keyed (``path``,
+    ``st_size``, ``st_mtime_ns``) METADATA-ONLY cache — a stat match serves already-verified
+    metadata with zero I/O, and ANY stat mismatch re-runs the full verifier (both checksums,
+    exactly as before caching existed). ``load_events`` and ``replay`` — the paths that feed
+    research values — are DELIBERATELY untouched by this cache and keep calling the full verifier
+    unconditionally on EVERY call, forever (the verification trust boundary this interlude's
+    critical anti-goal protects). A corrupted or tampered file (even a hand-edited split) raises
+    the explicit ``DatasetIntegrityError`` on re-verify — never silence, never a fabricated
+    dataset, and never cached (only a successful verify's metadata is ever published).
   * **The split tag is frozen at registration — structurally.** No update/re-tag/delete function
     exists anywhere in this module (immutability is structural, not policed). The only mutation
     is ``record``, and it REFUSES content that is already registered: re-recording the same tape
@@ -37,6 +45,7 @@ from __future__ import annotations
 
 import hashlib
 import json
+import time
 import uuid
 from dataclasses import dataclass
 from datetime import datetime, timezone
@@ -49,6 +58,7 @@ from ..engine.tape_engine import TapeEngine
 from ..providers.adapters.base import HistoricalWindow
 from ..providers.base import Event, QuoteEvent, Side, TradeEvent
 from ..providers.historical import HistoricalProvider
+from .dataset_index import DatasetIndex
 from .feed_basis import data_feed_for_scenario
 
 # The dataset source vocabulary REUSES the studies module's source-resolution names (one owner
@@ -179,15 +189,53 @@ class _LoadedDataset:
     rows: list[dict]
 
 
+# --- era-fast_wall J-02: the module-level stat-keyed METADATA-ONLY verified cache ----------------
+# Mirrors ``bars.py``'s identical ``_VERIFIED_CACHE`` discipline (see that module's block comment
+# for the full torn-read/atomic-publish rationale) — a module global, not an instance attribute,
+# since ``DatasetStore`` is constructed fresh per FastAPI dependency call. The ONLY difference from
+# ``bars.py``: this cache holds METADATA ONLY, never a dataset's (potentially huge) event rows —
+# ``load_events``/``replay`` never consult it and keep calling the full verifier on every call
+# (the verification trust boundary this interlude's critical anti-goal protects; see the module
+# docstring). Key: the absolute file path. Value: ``(st_size, st_mtime_ns, meta_dict)``.
+_VERIFIED_META_CACHE: dict[str, tuple[int, int, dict]] = {}
+
+# Identical guard to ``bars.py``'s — a file whose mtime is within this many seconds of "now" (at
+# read time) is never published (see that module's constant docstring for the rationale).
+_RACY_WRITE_GUARD_SECONDS = 2.0
+
+
+def _reset_verified_cache_for_tests() -> None:
+    """Test-only: clears the module-level metadata cache. Never called from any production code
+    path — exists solely so tests (and the autouse ``conftest.py`` fixture) can guarantee no
+    cross-test cache leakage (TC-12)."""
+    _VERIFIED_META_CACHE.clear()
+
+
 class DatasetStore:
     """File-based store rooted at the config-owned dataset directory — the ONE reader/writer.
 
-    Construction is cheap (no I/O); the directory is created on the first ``record``. Every read
-    path (``get`` / ``list`` / ``load_events`` / ``replay``) goes through the same verified
-    ``_load`` — the checksum is recomputed on EVERY load, with no bypass."""
+    Construction is cheap (no I/O); the directory is created on the first ``record``.
+    era-fast_wall J-02: ``get``/``list`` are served from a stat-keyed, metadata-only verified
+    cache (see the module docstring's re-verification contract); ``load_events``/``replay`` go
+    through the same verified ``_load`` as always — the checksum is recomputed on EVERY call for
+    those two, with no bypass, ever."""
 
-    def __init__(self, root: str | Path) -> None:
+    def __init__(self, root: str | Path, *, index_db_path: str | None = None) -> None:
         self._root = Path(root)
+        # era-fast_wall J-02: the OPTIONAL durable sibling index (``dataset_index.py``). ``None``
+        # (the default) preserves today's exact in-process-only behavior for every existing
+        # caller — none pass this today. Lazily constructed on first actual use (never in
+        # ``__init__``) so construction itself stays I/O-free, the same convention this class
+        # already documents ("Construction is cheap (no I/O)").
+        self._index_db_path = index_db_path
+        self._index: DatasetIndex | None = None
+
+    def _durable_index(self) -> DatasetIndex | None:
+        if self._index_db_path is None:
+            return None
+        if self._index is None:
+            self._index = DatasetIndex(self._index_db_path)
+        return self._index
 
     # --- verified load (the one loader; no unverified path exists) ------------------------------
 
@@ -232,28 +280,81 @@ class DatasetStore:
         return _LoadedDataset(meta=meta, rows=rows)
 
     def _load_by_id(self, dataset_id: str) -> _LoadedDataset:
+        """The UNCACHED full-verify load path — used ONLY by ``load_events``/``replay`` (never by
+        ``get``/``list``, which route through ``_cached_meta`` below). era-fast_wall J-02: this
+        method is DELIBERATELY untouched by the new cache — the verification trust boundary the
+        interlude's critical anti-goal protects."""
         path = self._path(dataset_id)
         if not path.exists():
             raise DatasetNotFound(f"no dataset with id '{dataset_id}'")
         return self._load(path)
 
+    def _cached_meta(self, path: Path) -> dict:
+        """era-fast_wall J-02 — the metadata-ONLY stat-keyed cache-or-verify wrapper, consulted
+        EXCLUSIVELY by ``get``/``list``. Three layers, checked in order: (1) the in-process stat
+        cache — a stat match serves already-verified metadata with zero I/O; (2) the OPTIONAL
+        durable sibling index (``dataset_index.py``), consulted only on an in-process miss — a
+        ``(path, size, mtime_ns)`` hit there is ALSO zero-I/O (no ``_load`` call), since a durable
+        row is only ever written from a value ``_load`` itself already verified; (3) the full
+        ``_load`` verifier — always ``rows`` included (checksum verification needs them), but only
+        ``meta`` is ever cached at either layer, so dataset CONTENT never lives in either cache
+        (the 882MB-of-rows-never-cached discipline). An integrity error is never cached at any
+        layer. A file whose mtime is within ``_RACY_WRITE_GUARD_SECONDS`` of "now" is never
+        published to either layer — the identical ``bars.py`` racy-write guard."""
+        try:
+            st = path.stat()
+        except OSError:
+            # Let the real loader raise its own explicit, typed error for a vanished/unreadable
+            # file — the identical failure this call would have hit uncached.
+            return self._load(path).meta
+
+        key = str(path)
+        cached = _VERIFIED_META_CACHE.get(key)  # read-local-reference-before-inspect
+        if cached is not None and cached[0] == st.st_size and cached[1] == st.st_mtime_ns:
+            return cached[2]
+
+        index = self._durable_index()
+        if index is not None:
+            indexed = index.lookup(key, st.st_size, st.st_mtime_ns)
+            if indexed is not None:
+                if (time.time_ns() - st.st_mtime_ns) >= _RACY_WRITE_GUARD_SECONDS * 1_000_000_000:
+                    _VERIFIED_META_CACHE[key] = (st.st_size, st.st_mtime_ns, indexed)
+                return indexed
+
+        meta = self._load(path).meta  # the full verifier — unchanged, both checksums recomputed
+
+        if (time.time_ns() - st.st_mtime_ns) >= _RACY_WRITE_GUARD_SECONDS * 1_000_000_000:
+            _VERIFIED_META_CACHE[key] = (st.st_size, st.st_mtime_ns, meta)  # single atomic rebind
+            if index is not None:
+                index.insert(key, st.st_size, st.st_mtime_ns, meta)
+        return meta
+
     # --- reads -----------------------------------------------------------------------------------
 
     def get(self, dataset_id: str) -> dict:
-        """One dataset's metadata (verified load). ``DatasetNotFound`` for an unknown id."""
-        return dict(self._load_by_id(dataset_id).meta)
+        """One dataset's metadata (verified load, cached — see ``_cached_meta``).
+        ``DatasetNotFound`` for an unknown id. era-fast_wall J-02: ``event_counts`` (the one
+        nested mutable field in ``meta``) is copied fresh on every call so a caller mutating the
+        returned dict in place can never poison a later cached read — the ``bars.py`` per-row-copy
+        discipline (TC-6), applied to this store's one nested field."""
+        path = self._path(dataset_id)
+        if not path.exists():
+            raise DatasetNotFound(f"no dataset with id '{dataset_id}'")
+        meta = self._cached_meta(path)
+        return {**meta, "event_counts": dict(meta["event_counts"])}
 
     def list(self) -> tuple[list[dict], list[dict]]:
-        """All datasets' metadata (each file verified), oldest first, plus an EXPLICIT error row
-        per file that failed verification — a corrupt file is surfaced, never silently hidden and
-        never served as data."""
+        """All datasets' metadata (each file verified, cached — see ``_cached_meta``), oldest
+        first, plus an EXPLICIT error row per file that failed verification — a corrupt file is
+        surfaced, never silently hidden and never served as data."""
         if not self._root.exists():
             return [], []
         records: list[dict] = []
         errors: list[dict] = []
         for path in sorted(self._root.glob("*.json")):
             try:
-                records.append(dict(self._load(path).meta))
+                meta = self._cached_meta(path)
+                records.append({**meta, "event_counts": dict(meta["event_counts"])})
             except DatasetIntegrityError as exc:
                 errors.append({"file": path.name, "error": str(exc)})
         records.sort(key=lambda meta: (meta.get("created_utc", ""), meta.get("id", "")))
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index 63706cc..dc09e44 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -1410,8 +1410,20 @@ def cancel_study(
 def get_dataset_store() -> DatasetStore:
     """The dataset store rooted at the config-owned directory (``TAPEOLOGY_DATASET_DIR``
     override, package-anchored default). A FastAPI dependency so tests can point it at a temp
-    dir via the env var or override it outright (the adapter-seam pattern)."""
-    return DatasetStore(CONFIG.dataset_dir_resolved())
+    dir via the env var or override it outright (the adapter-seam pattern).
+
+    era-fast_wall J-02: also wires the durable metadata index (``dataset_index.py``) — a
+    config-DERIVED, env-overridable path so ``config.py`` stays byte-identical
+    (``config_fingerprint`` unaffected, the identical ``get_bar_index`` rationale): the
+    ``TAPEOLOGY_DATASET_INDEX_DB`` env var if set, else a file co-located as a SIBLING of the
+    resolved dataset directory (``.data/datasets`` -> ``.data/dataset_index.db`` — the SAME
+    ``get_bar_index`` env-else-sibling shape, mirrored exactly). Every existing test keeps this
+    hermetically for free, since the derived default lives right beside whatever
+    ``TAPEOLOGY_DATASET_DIR`` a test points at."""
+    dataset_dir = CONFIG.dataset_dir_resolved()
+    override = os.environ.get("TAPEOLOGY_DATASET_INDEX_DB")
+    index_db_path = override if override else os.path.join(os.path.dirname(dataset_dir), "dataset_index.db")
+    return DatasetStore(dataset_dir, index_db_path=index_db_path)
 
 
 @router.post("/datasets")
diff --git a/apps/backend/tests/conftest.py b/apps/backend/tests/conftest.py
index 1ff554a..ebada0e 100644
--- a/apps/backend/tests/conftest.py
+++ b/apps/backend/tests/conftest.py
@@ -12,3 +12,21 @@ load_env()
 @pytest.fixture
 def anyio_backend() -> str:
     return "asyncio"
+
+
+@pytest.fixture(autouse=True)
+def _reset_store_verified_caches():
+    """era-fast_wall J-02 (TC-12) — this file's FIRST autouse fixture. Resets BOTH new
+    module-level, stat-keyed verified-content caches (``bars.py``'s ``_VERIFIED_CACHE``,
+    ``datasets.py``'s ``_VERIFIED_META_CACHE``) before every test, via each module's own
+    test-only reset helper. Without this, the caches would accumulate entries across the ENTIRE
+    test session (harmless for correctness — the cache key is the absolute file path, and
+    distinct ``tmp_path`` roots never collide — but unbounded growth over a long suite run is
+    still worth avoiding), and any test that intentionally wants a genuinely cold cache can now
+    rely on that being the default starting state rather than re-deriving it itself."""
+    import app.research.bars as bars_module
+    import app.research.datasets as datasets_module
+
+    bars_module._reset_verified_cache_for_tests()
+    datasets_module._reset_verified_cache_for_tests()
+    yield
diff --git a/apps/backend/tests/test_bars.py b/apps/backend/tests/test_bars.py
index 5218609..dfdc774 100644
--- a/apps/backend/tests/test_bars.py
+++ b/apps/backend/tests/test_bars.py
@@ -11,6 +11,7 @@ recency-delay clamp and the rate-limit throttle) as small, independently testabl
 from __future__ import annotations
 
 import json
+import os
 import time
 from datetime import datetime, timedelta, timezone
 from pathlib import Path
@@ -215,6 +216,159 @@ def test_committed_fixture_loads_through_the_real_store_path_keyless():
         assert again == meta
 
 
+# --- era-fast_wall J-02: the stat-keyed verified-record cache -------------------------------------
+
+
+def _age(path: Path, seconds: float = 5.0) -> None:
+    """Backdates a file's mtime past the ~2s racy-write guard window, so a test can
+    deterministically exercise the WARM-cache path without a real sleep."""
+    past = time.time() - seconds
+    os.utime(path, (past, past))
+
+
+def _spy_on_load(monkeypatch):
+    """Installs a counting spy around ``BarStore._load`` (the ONE full verifier) and returns the
+    call-count list — the ``test_setups.py`` ``_counting_scan`` precedent (a monkeypatched
+    counting wrapper around the real function), applied to this module's own verifier. A "read" in
+    every TC below means exactly one call recorded here."""
+    import app.research.bars as bars_module
+
+    calls: list[int] = []
+    real_load = bars_module.BarStore._load
+
+    def _counting_load(self, path):
+        calls.append(1)
+        return real_load(self, path)
+
+    monkeypatch.setattr(bars_module.BarStore, "_load", _counting_load)
+    return calls
+
+
+def test_get_serves_zero_reads_on_a_warm_cache_hit(tmp_path, monkeypatch):
+    """TC-1."""
+    store = BarStore(tmp_path / "bars")
+    meta = _record_small_series(store)
+    _age(tmp_path / "bars" / f"{meta['id']}.json")
+    calls = _spy_on_load(monkeypatch)
+
+    first = store.get(meta["id"])
+    assert len(calls) == 1, "the first read must be a real verify"
+
+    second = store.get(meta["id"])
+    assert len(calls) == 1, "a warm-cache hit must add ZERO additional reads"
+    assert second == first
+
+
+def test_list_serves_zero_reads_across_all_files_on_a_warm_cache_hit(tmp_path, monkeypatch):
+    """TC-2."""
+    store = BarStore(tmp_path / "bars")
+    a = _record_small_series(store, symbol="PG")
+    b = _record_small_series(store, symbol="F")
+    for meta in (a, b):
+        _age(tmp_path / "bars" / f"{meta['id']}.json")
+    calls = _spy_on_load(monkeypatch)
+
+    first_records, first_errors = store.list()
+    assert len(calls) == 2, "the first list() must verify every healthy file exactly once"
+    assert first_errors == []
+
+    second_records, second_errors = store.list()
+    assert len(calls) == 2, "a warm list() must add ZERO additional reads across ALL files"
+    assert second_records == first_records
+    assert second_errors == []
+
+
+def test_get_reverifies_and_raises_after_a_warm_read_is_tampered(tmp_path):
+    """TC-3."""
+    store = BarStore(tmp_path / "bars")
+    meta = _record_small_series(store)
+    path = tmp_path / "bars" / f"{meta['id']}.json"
+    _age(path)
+
+    warm = store.get(meta["id"])  # populate the cache
+    assert warm["symbol"] == "PG"
+
+    _tamper(path, lambda data: data["record"]["bars"][0].__setitem__("close", 999.0))
+    with pytest.raises(BarSeriesIntegrityError):
+        store.get(meta["id"])  # the tamper's stat change must force a fresh (failing) re-verify —
+        # never the stale-good cached value, never a silently-served tampered value.
+
+
+def test_racy_write_guard_refuses_to_cache_a_freshly_written_bar_series(tmp_path, monkeypatch):
+    """TC-5 (bars leg)."""
+    store = BarStore(tmp_path / "bars")
+    calls = _spy_on_load(monkeypatch)
+
+    meta = _record_small_series(store)  # freshly written -- inside the ~2s racy window
+    store.get(meta["id"])
+    assert len(calls) == 1
+
+    store.get(meta["id"])  # still inside the window -- must be a real read again, never cached
+    assert len(calls) == 2, "the racy-write guard must refuse to cache a just-written file"
+
+
+def test_get_and_list_return_row_copies_a_caller_mutation_never_poisons_the_cache(tmp_path):
+    """TC-6."""
+    store = BarStore(tmp_path / "bars")
+    meta = _record_small_series(store)
+    _age(tmp_path / "bars" / f"{meta['id']}.json")
+
+    fetched = store.get(meta["id"])
+    original_close = fetched["bars"][0]["close"]
+    fetched["bars"][0]["close"] = -1.0  # caller mutation, in place
+    fetched["bars"].append(
+        {"ts": 0.0, "open": 0.0, "high": 0.0, "low": 0.0, "close": 0.0, "volume": 0}
+    )
+
+    again = store.get(meta["id"])  # a warm-cache hit
+    assert again["bars"][0]["close"] == original_close
+    assert len(again["bars"]) == 3
+
+    records, _errors = store.list()
+    listed = next(r for r in records if r["id"] == meta["id"])
+    assert listed["bars"][0]["close"] == original_close
+    assert len(listed["bars"]) == 3
+
+
+def test_bar_store_root_is_a_public_read_only_property(tmp_path):
+    """TC-11."""
+    root = tmp_path / "bars"
+    store = BarStore(root)
+    assert store.root == root
+    with pytest.raises(AttributeError):
+        store.root = tmp_path / "elsewhere"
+
+
+def test_reset_helper_clears_the_cache_and_prevents_cross_root_leakage(tmp_path_factory, monkeypatch):
+    """TC-12 — the autouse conftest fixture's own reset action, exercised directly: after a
+    reset, BOTH module-level caches are empty, and a genuinely fresh root's first read is a real
+    cache miss — no state survives from an earlier root's warm cache."""
+    import app.research.bars as bars_module
+    import app.research.datasets as datasets_module
+
+    calls = _spy_on_load(monkeypatch)
+
+    root_a = tmp_path_factory.mktemp("bars_a")
+    store_a = BarStore(root_a)
+    meta_a = _record_small_series(store_a, symbol="PG")
+    _age(root_a / f"{meta_a['id']}.json")
+    store_a.get(meta_a["id"])
+    assert len(calls) == 1
+    assert bars_module._VERIFIED_CACHE, "sanity: the cache must have genuinely warmed"
+
+    bars_module._reset_verified_cache_for_tests()
+    datasets_module._reset_verified_cache_for_tests()
+    assert bars_module._VERIFIED_CACHE == {}
+    assert datasets_module._VERIFIED_META_CACHE == {}
+
+    root_b = tmp_path_factory.mktemp("bars_b")
+    store_b = BarStore(root_b)
+    meta_b = _record_small_series(store_b, symbol="F")
+    _age(root_b / f"{meta_b['id']}.json")
+    store_b.get(meta_b["id"])
+    assert len(calls) == 2, "a genuinely fresh root's first read must be a real cache miss"
+
+
 # --- config: bar_dir + validation/throttle params are operational, never fingerprint inputs -------
 
 
diff --git a/apps/backend/tests/test_datasets.py b/apps/backend/tests/test_datasets.py
index e931bae..2cf6c1d 100644
--- a/apps/backend/tests/test_datasets.py
+++ b/apps/backend/tests/test_datasets.py
@@ -28,6 +28,8 @@ Locked disciplines (each an anti-goal or a J-02 acceptance clause):
 from __future__ import annotations
 
 import json
+import os
+import time
 from datetime import datetime, timezone
 from pathlib import Path
 
@@ -328,6 +330,112 @@ def test_committed_fixture_pair_windows_are_disjoint():
     assert train["checksum"] != holdout["checksum"]
 
 
+# --- era-fast_wall J-02: the metadata-only stat-keyed verified cache ------------------------------
+
+
+def _age(path: Path, seconds: float = 5.0) -> None:
+    """Backdates a file's mtime past the ~2s racy-write guard window, so a test can
+    deterministically exercise the WARM-cache path without a real sleep (the ``test_bars.py``
+    identical helper)."""
+    past = time.time() - seconds
+    os.utime(path, (past, past))
+
+
+def _spy_on_load(monkeypatch):
+    """Installs a counting spy around ``DatasetStore._load`` (the ONE full verifier) and returns
+    the call-count list — the ``test_bars.py``/``test_setups.py`` identical technique."""
+    import app.research.datasets as datasets_module
+
+    calls: list[int] = []
+    real_load = datasets_module.DatasetStore._load
+
+    def _counting_load(self, path):
+        calls.append(1)
+        return real_load(self, path)
+
+    monkeypatch.setattr(datasets_module.DatasetStore, "_load", _counting_load)
+    return calls
+
+
+def test_list_surfaces_a_tampered_file_as_an_error_after_a_warm_read(tmp_path):
+    """TC-4."""
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)
+    path = tmp_path / "datasets" / f"{meta['id']}.json"
+    _age(path)
+
+    warm_records, warm_errors = store.list()
+    assert warm_errors == []
+    assert warm_records[0]["id"] == meta["id"]
+
+    def _corrupt(data):
+        for row in data["record"]["events"]:
+            if row["type"] == "trade":
+                row["price"] += 1.0
+                return
+
+    _tamper(path, _corrupt)
+
+    records, errors = store.list()
+    assert records == [], "the tampered dataset must never be served as healthy metadata"
+    assert len(errors) == 1 and f"{meta['id']}.json" in errors[0]["file"]
+
+
+def test_racy_write_guard_refuses_to_cache_a_freshly_recorded_dataset(tmp_path, monkeypatch):
+    """TC-5 (datasets leg)."""
+    store = DatasetStore(tmp_path / "datasets")
+    calls = _spy_on_load(monkeypatch)
+
+    meta = _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)  # freshly written
+    store.get(meta["id"])
+    assert len(calls) == 1
+
+    store.get(meta["id"])  # still inside the ~2s racy window
+    assert len(calls) == 2, "the racy-write guard must refuse to cache a just-written file"
+
+
+def test_load_events_and_replay_fully_reverify_even_when_the_metadata_cache_is_warm(tmp_path, monkeypatch):
+    """TC-7 — the mechanical proof of the critical "verification trust boundary never weakens"
+    anti-goal: ``load_events``/``replay`` must fully re-verify on every call, even once
+    ``get``/``list`` have warm-cached this exact dataset's metadata."""
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)
+    path = tmp_path / "datasets" / f"{meta['id']}.json"
+    _age(path)
+
+    store.get(meta["id"])  # warm the metadata cache
+    store.list()
+
+    calls = _spy_on_load(monkeypatch)  # installed AFTER warming -- isolates what happens next
+
+    events = store.load_events(meta["id"])
+    assert len(events) == meta["event_counts"]["total"] > 0
+    assert len(calls) == 1, "load_events must fully re-verify even with a warm metadata cache"
+
+    list(store.replay(meta["id"], CONFIG))
+    assert len(calls) == 2, "replay must fully re-verify even with a warm metadata cache"
+
+
+def test_get_and_list_return_event_counts_copies_a_caller_mutation_never_poisons_the_cache(tmp_path):
+    """Extends ``test_bars.py``'s TC-6 per-row-copy discipline to this store's one nested
+    mutable metadata field (``event_counts``) — not itself a numbered TC, but the identical
+    caller-mutation hazard the new cache introduces for this store too."""
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)
+    _age(tmp_path / "datasets" / f"{meta['id']}.json")
+
+    fetched = store.get(meta["id"])
+    original_total = fetched["event_counts"]["total"]
+    fetched["event_counts"]["total"] = -999  # caller mutation, in place
+
+    again = store.get(meta["id"])  # a warm-cache hit
+    assert again["event_counts"]["total"] == original_total
+
+    records, _errors = store.list()
+    listed = next(r for r in records if r["id"] == meta["id"])
+    assert listed["event_counts"]["total"] == original_total
+
+
 # --- config: the dataset dir is operational, never a fingerprint input ----------------------------
 
 
diff --git a/apps/backend/tests/test_datasets_api.py b/apps/backend/tests/test_datasets_api.py
index 52f66da..b668182 100644
--- a/apps/backend/tests/test_datasets_api.py
+++ b/apps/backend/tests/test_datasets_api.py
@@ -15,6 +15,7 @@ explicit research action — the no-ambient-recording anti-goal).
 from __future__ import annotations
 
 import json
+import os
 import time
 from pathlib import Path
 
@@ -292,6 +293,41 @@ def test_corrupted_dataset_file_surfaces_explicitly_on_detail_and_list(ctx):
     assert f"{corrupt['id']}.json" in listed["integrity_errors"][0]["file"]
 
 
+# --- era-fast_wall J-02: warm-cache byte-identity (TC-8, REST leg) --------------------------------
+
+
+def test_warm_cache_response_is_byte_identical_to_a_forced_fresh_verify(ctx):
+    """TC-8 (REST leg): a warm-cache response byte-equals a response served after BOTH the
+    in-process stat cache AND the durable sibling ``dataset_index.db`` are forced cold (the
+    test-only reset helper, plus deleting the durable index DB) — a genuinely fresh full-verify
+    pass. The cache changes only WHETHER the file is re-read, never a single byte of what is
+    served."""
+    client, dataset_dir = ctx
+    client.post("/research/datasets", json=_reference_body("train"))
+    client.post("/research/datasets", json=_reference_body("holdout", HOLDOUT_START, HOLDOUT_END))
+
+    for f in dataset_dir.glob("*.json"):
+        past = time.time() - 5.0
+        os.utime(f, (past, past))
+
+    warm = client.get("/research/datasets")
+    assert warm.status_code == 200
+    assert warm.json()["integrity_errors"] == []
+    assert len(warm.json()["datasets"]) == 2
+
+    import app.research.datasets as datasets_module
+
+    datasets_module._reset_verified_cache_for_tests()
+    index_db = Path(dataset_dir).parent / "dataset_index.db"
+    if index_db.exists():
+        index_db.unlink()
+
+    fresh = client.get("/research/datasets")
+    assert fresh.status_code == 200
+
+    assert warm.content == fresh.content, "a warm response must be byte-identical to a fresh one"
+
+
 # --- no ambient recording ---------------------------------------------------------------------------
 
 
diff --git a/apps/backend/tests/test_edge_report_api.py b/apps/backend/tests/test_edge_report_api.py
index 3b475b4..abe5637 100644
--- a/apps/backend/tests/test_edge_report_api.py
+++ b/apps/backend/tests/test_edge_report_api.py
@@ -9,6 +9,8 @@ computation's exact cell values and gate logic in isolation).
 from __future__ import annotations
 
 import json
+import os
+import time
 
 import pytest
 from fastapi.testclient import TestClient
@@ -113,6 +115,41 @@ def test_edge_report_integrity_failure_is_an_explicit_500_never_a_partial_report
     assert "integrity" in response.json()["detail"].lower()
 
 
+def test_integrity_failure_after_a_warm_datasets_list_read_is_still_a_500(ctx):
+    """TC-14 — era-fast_wall J-02: proves the new ``datasets.py`` metadata cache never masks an
+    integrity error inside ``peek_strategy_comparison_report``'s ``_verified_records`` call, even
+    when ``GET /research/datasets`` ALREADY warm-cached this exact dataset's metadata before it
+    was tampered. The tamper changes the file's stat, so the cache's next lookup is an honest
+    miss that forces a full re-verify — never a stale-good served value."""
+    client, _store, tmp_path = ctx
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
+    dataset_id = recorded.json()["dataset"]["id"]
+    path = tmp_path / "datasets" / f"{dataset_id}.json"
+    past = time.time() - 5.0
+    os.utime(path, (past, past))  # past the ~2s racy-write guard, so the warm read below actually caches
+
+    warm = client.get("/research/datasets")
+    assert warm.status_code == 200
+    assert warm.json()["integrity_errors"] == [], "sanity: genuinely warm-cached as healthy"
+
+    data = json.loads(path.read_text())
+    data["record"]["meta"]["checksum"] = "0" * 64  # tamper AFTER the warm read
+    path.write_text(json.dumps(data))
+
+    response = client.get("/research/edge-report")
+    assert response.status_code == 500
+    assert "integrity" in response.json()["detail"].lower()
+
+
 def test_non_get_verbs_are_405_no_write_surface_exists(ctx):
     client, _store, _tmp_path = ctx
     for method in ("post", "put", "patch", "delete"):
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index c595719..4391010 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -248,10 +248,21 @@ async def test_static_live_tools_json_byte_identical_to_rest(mcp_env):
 
 
 @pytest.mark.anyio
-async def test_datasets_tool_byte_identical_on_a_non_empty_live_list(mcp_env):
+async def test_datasets_tool_byte_identical_on_a_non_empty_live_list(mcp_env, backend_paths):
     """J-02 flips ``datasets`` from honest 404 to live data with ZERO MCP code changes: after
     recording a dataset (the committed reference window, keyless), the tool's JSON is
-    byte-identical to its curl equivalent on a NON-EMPTY 200 list."""
+    byte-identical to its curl equivalent on a NON-EMPTY 200 list.
+
+    era-fast_wall J-02 (TC-8, MCP leg): every recorded dataset file's mtime is pushed past the
+    ~2s racy-write guard via a direct disk ``os.utime`` call BEFORE the byte-identity calls below
+    (the SAME filesystem the subprocess backend itself reads — there is no in-process reset
+    possible against a separate OS process, unlike the same-process proof in
+    ``test_datasets_api.py``). Without this, a freshly-recorded file's own racy-write guard would
+    force every read cold for this short-lived test, silently never exercising the WARM-cache
+    path the datasets.py metadata cache adds — the extension the iter-1-applied lesson calls for
+    (this exact test previously depended on module-scoped shared-backend state; the fix here must
+    hold both standalone and inside the full module, so it deliberately ages EVERY file in the
+    dataset dir rather than just the one this call may or may not have just recorded)."""
     recorded = httpx.post(
         f"{mcp_env}/research/datasets",
         json={
@@ -263,6 +274,15 @@ async def test_datasets_tool_byte_identical_on_a_non_empty_live_list(mcp_env):
         timeout=15.0,
     )
     assert recorded.status_code in (200, 409)  # 409 = already recorded by an earlier run/test
+
+    dataset_dir = Path(backend_paths["TAPEOLOGY_DATASET_DIR"])
+    past = time.time() - 5.0
+    for f in dataset_dir.glob("*.json"):
+        os.utime(f, (past, past))
+
+    warm_up = httpx.get(f"{mcp_env}/research/datasets", timeout=5.0)  # populate the warm cache
+    assert warm_up.status_code == 200
+
     result = await call_tool("datasets", {})
     rest = httpx.get(f"{mcp_env}/research/datasets", timeout=5.0)
     assert rest.status_code == 200
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-fast_wall/telemetry.jsonl   | 6 ++++++
 runs/goal-session-fast_wall/trace/trace.jsonl | 3 +++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
