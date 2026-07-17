# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

```diff
diff --git a/apps/backend/app/research/setups.py b/apps/backend/app/research/setups.py
index ebaeb46..23318cd 100644
--- a/apps/backend/app/research/setups.py
+++ b/apps/backend/app/research/setups.py
@@ -109,17 +109,21 @@ than silently pairing a definitive ``reaction`` label with a horizon-0 ``forward
 exactly when it did not). Neither field ever changes ``reaction`` itself or excludes the event --
 see ``_reaction_and_forward_returns``'s own docstring for the exact boundary condition.
 
-**B3 -- a process-local memoized scan (era-5B iter-5; made atomic in iter-6).** ``GET
-/research/setups``, ``GET /research/setups/{id}``, and
+**B3 -- a process-local memoized scan (era-5B iter-5; made atomic in iter-6; gained a durable
+sibling tier at era-fast_wall J-06).** ``GET /research/setups``, ``GET /research/setups/{id}``, and
 ``edge_report.run_strategy_comparison_report`` each call ``compute_setups(store, config)``
 independently; on the populated 12-symbol panel the underlying scan takes minutes, so without a
 cache a single page load could trigger it multiple times over. The PUBLIC ``compute_setups`` below
-is now a thin, byte-identical memoizing wrapper around the real scan (renamed
-``_run_full_panel_scan``) -- see its own docstring for the caching contract (process-local,
-store-content-keyed, rebuildable, never a second source of truth -- the ``bar_index.py`` precedent).
-iter-6 hardened the publish to a single atomic ``(key, result)`` tuple rebind (see the ``_SCAN_CACHE``
-block comment below) once this iteration became the first caller to fire all three consumers
-concurrently from one browser page load.
+is now a two-tier, byte-identical memoizing wrapper around the real scan (renamed
+``_run_full_panel_scan``) -- see its own docstring for the full caching contract (content-keyed,
+rebuildable, never a second source of truth -- the ``bar_index.py`` precedent). iter-6 (era-5B)
+hardened the in-process hot-slot publish to a single atomic ``(key, result)`` tuple rebind (see the
+``_SCAN_CACHE`` block comment below) once that iteration became the first caller to fire all three
+consumers concurrently from one browser page load. era-fast_wall J-06 additionally gave
+``compute_setups`` a DURABLE sibling tier (``setups_scan_cache.py``'s ``SetupsScanCache``, consulted
+only on a hot-slot miss) so a backend restart -- or simply a freshly-constructed but content-equal
+``Config`` object -- never re-pays the scan either; see ``compute_setups``'s own docstring below for
+the exact three-tier order.
 """
 
 from __future__ import annotations
@@ -131,6 +135,8 @@ from ..config import Config
 from ..providers.adapters.base import RawBar
 from .bars import BarStore
 from .datasets import DatasetStore, parse_utc_epoch
+from .edge_report_cache import _config_content_hash
+from .setups_scan_cache import SetupsScanCache, resolve_scan_cache_db_path, scan_cache_key
 from .tradability import RESISTANCE, SUPPORT, compute_tradability
 
 REJECTED = "rejected"
@@ -329,31 +335,42 @@ def _event_sort_key(event: dict) -> tuple:
 # `run_strategy_comparison_report`); on the populated 12-symbol store the underlying scan takes
 # minutes, so without this layer a single page load could trigger it several times over, well past
 # browser-QA timeouts. This is the SAME "rebuildable accelerator, never a second source of truth"
-# contract `bar_index.py` lives under (see that module's own docstring), but PROCESS-LOCAL and
-# in-memory only -- never SQLite/disk-persisted, and never itself read by anything outside this
-# module. `compute_setups`'s own signature is UNCHANGED, so every caller (routes.py, edge_report.py)
-# needs zero changes -- only ITS body differs (a cache check wrapping the real scan, renamed
-# `_run_full_panel_scan` below).
+# contract `bar_index.py` lives under (see that module's own docstring). THIS slot itself stays
+# PROCESS-LOCAL and in-memory only -- never SQLite/disk-persisted, and never itself read by anything
+# outside this module -- but era-fast_wall J-06 gave `compute_setups` a DURABLE sibling tier
+# (`setups_scan_cache.py`'s `SetupsScanCache`, consulted only on a miss here) so a process restart
+# no longer loses everything this slot remembered; see `compute_setups`'s own docstring below for
+# the full three-tier order. `compute_setups`'s own signature is UNCHANGED, so every caller
+# (routes.py, edge_report.py) needs zero changes -- only ITS body differs (a cache check wrapping
+# the real scan, renamed `_run_full_panel_scan` below).
 #
-# Keyed on (a) the config object's OWN identity -- every production caller shares the ONE imported
-# `CONFIG` singleton (routes.py, edge_report.py), so this is stable for the life of the process;
-# a test constructing its own `Config(...)` keeps it alive for that call's duration (referenced
-# locally), so a fresh id is never reused mid-call -- and (b) a deterministic content signature over
+# Keyed on (a) a deterministic hash of the config's ENTIRE field CONTENT (era-fast_wall J-06 --
+# `edge_report_cache._config_content_hash`, imported and reused verbatim, never re-derived a second
+# time; NOT `config.config_fingerprint()` alone, whose own documented exclusion set drops exactly the
+# `setups_*`/`tradability_*`/`sr_*` families this scan and `compute_tradability` read -- see
+# `edge_report_cache.py`'s "why it is FOUR parts" docstring section for the identical reasoning
+# proven necessary for the sibling report cache) and (b) a deterministic content signature over
 # `store.list()` (sorted `(symbol, timeframe, id, checksum)` tuples -- `bars.py` already exposes a
 # per-series `checksum` in every list record, so this reuses an existing value rather than hashing
-# raw bars). `Config` cannot be used as a key directly (it carries plain `dict` fields, e.g.
-# `tradability_quality_weights`, so it is not hashable). Any change to the store's registered series
-# set -- a new recording, a symbol's series replaced -- changes the signature and busts the cache;
-# an untouched store always replays the identical cached result. A single most-recent SLOT (not an
-# unbounded dict) is intentional: this codebase runs ONE bar store behind ONE process, so there is
-# never more than one "current" scan worth remembering, and a single slot cannot grow unbounded
-# across a long-lived process or an entire test suite's run.
+# raw bars). Content-hashing `config` (rather than the OLD `id(config)` identity key, which never
+# survived a restart and never recognised a freshly-constructed but content-equal `Config` as the
+# SAME scan) is itself now possible because `_config_content_hash` uses `dataclasses.asdict` + a
+# canonical-JSON encoding rather than hashing `Config` directly (`Config` carries plain `dict`
+# fields, e.g. `tradability_quality_weights`, so it is not hashable on its own). Any change to
+# EITHER component -- a config field genuinely read by this scan, or the store's registered series
+# set -- changes the key and busts BOTH tiers; an untouched (config content, store content) pair
+# always replays the identical cached result, hot-slot or durable. A single most-recent SLOT (not an
+# unbounded dict) remains intentional for the IN-PROCESS tier: this codebase runs ONE bar store
+# behind ONE process, so there is never more than one "current" scan worth remembering in-process,
+# and a single slot cannot grow unbounded across a long-lived process or an entire test suite's run
+# -- the DURABLE tier (unlike this slot) can and does hold more than one row, one per distinct key
+# ever published.
 #
-# --- Atomic publish (era-5B iter-6 B3 hardening) ------------------------------------------------
+# --- Atomic publish (era-5B iter-6 B3 hardening; both tiers covered since era-fast_wall J-06) ----
 # The slot is ONE immutable ``(key, result)`` tuple (or ``None`` before anything is ever cached) --
-# NEVER a two-key mutable dict written in two separate statements. iter-6 is the first caller to
-# fire ``/setups`` + ``/setups/{id}`` + ``/edge-report`` concurrently from a single page load (a
-# FastAPI sync route handler runs in a thread pool), and the PRIOR two-write dict form
+# NEVER a two-key mutable dict written in two separate statements. iter-6 (era-5B) is the first
+# caller to fire ``/setups`` + ``/setups/{id}`` + ``/edge-report`` concurrently from a single page
+# load (a FastAPI sync route handler runs in a thread pool), and the PRIOR two-write dict form
 # (``_SCAN_CACHE["key"] = key`` THEN ``_SCAN_CACHE["result"] = result``) had a genuine torn-read
 # window: a late-arriving reader could observe a freshly-published ``key`` paired with the SLOT'S
 # STILL-STALE (possibly ``None``, on a first-ever cold cache) ``result``, since the two writes are
@@ -362,13 +379,29 @@ def _event_sort_key(event: dict) -> tuple:
 # reader always observes EITHER the entire previous publish (fully paired) or nothing yet (a safe
 # cache miss that recomputes) -- never a half-written pairing. Readers likewise take exactly ONE
 # local reference to the slot (`cached = _SCAN_CACHE`) before inspecting it, so a rebind by another
-# thread mid-check can never be observed as two different values within the same read. See
+# thread mid-check can never be observed as two different values within the same read. era-fast_wall
+# J-06 preserves this exactly: `compute_setups` still rebinds `_SCAN_CACHE` via ONE single statement
+# regardless of WHICH tier answered (a durable hit republished to the hot slot, or a full miss
+# freshly scanned and published to both layers) -- see
+# ``tests/test_setups.py``'s ``test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes``
+# structural guard, unmodified and still passing. See
 # ``tests/test_setups.py``'s
 # ``test_concurrent_cold_cache_reads_never_observe_a_torn_key_result_pair`` for the regression
 # proof.
 _SCAN_CACHE: tuple[tuple, dict] | None = None
 
 
+def _reset_scan_cache_for_tests() -> None:
+    """Test-only: clears the module-level in-process hot slot (`_SCAN_CACHE`) -- mirrors
+    `bars.py`/`datasets.py`'s own `_reset_verified_cache_for_tests` precedent (era-fast_wall J-06).
+    Never called from any production code path; exists so a test can genuinely simulate "hot slot
+    cleared, as if the process had just restarted" (`SetupsScanCache`'s own durable tier is already
+    isolated per-test by its stat/path-derived location -- this only ever needs to reset the
+    in-process half)."""
+    global _SCAN_CACHE
+    _SCAN_CACHE = None
+
+
 def _store_signature(store: BarStore) -> tuple:
     """A deterministic fingerprint of everything ``compute_setups`` can possibly read from
     ``store``: every HEALTHY series' ``(symbol, timeframe, id, checksum)``, sorted for
@@ -388,23 +421,40 @@ def compute_setups(store: BarStore, config: Config) -> dict:
     truth) -- see module docstring for the full algorithm. Returns ``{"events": [...]}``; an empty
     list is an honest "nothing scanned yet / nothing touched", never an error.
 
-    Served from the B3 process-local scan cache (see the block comment above) whenever ``store``'s
-    content signature and ``config``'s identity match the last computed call; otherwise this runs
-    the real scan (``_run_full_panel_scan``) once and remembers it. Byte-identical either way -- the
-    cache changes nothing about WHAT is returned, only whether it is recomputed.
-
-    Atomic against concurrent callers (era-5B iter-6 B3 hardening): ``cached`` is read ONCE into a
-    local (never re-read mid-function, so a concurrent rebind by another thread cannot be observed
-    as two different values here), and a cache miss publishes the freshly computed ``(key, result)``
-    as a SINGLE rebind of the module-level slot -- never two separate writes a reader could observe
-    half-done. A racing cache miss on another thread only ever costs redundant, harmless recompute
-    (the scan is a pure function of its inputs); it can never produce a torn key/result pairing."""
+    era-fast_wall J-06 -- a three-tier lookup: the in-process hot slot (below; unchanged atomic
+    discipline) -> the durable ``SetupsScanCache`` (``setups_scan_cache.py``, a restart-surviving
+    sibling of this slot) -> the real scan (``_run_full_panel_scan``), run at most once per
+    genuinely new key. Keyed on ``config``'s CONTENT (a hash over every field, reused verbatim from
+    ``edge_report_cache._config_content_hash`` -- never re-derived a second time -- rather than its
+    object identity, so a freshly-constructed but content-equal ``Config`` is a genuine cache HIT)
+    together with a deterministic content signature over the store (``_store_signature`` below).
+    Byte-identical whichever tier answers -- caching changes only whether/where the scan is
+    recomputed, never what is returned.
+
+    Atomic against concurrent callers (era-5B iter-6 B3 hardening, preserved): ``cached`` is read
+    ONCE into a local (never re-read mid-function, so a concurrent rebind by another thread cannot
+    be observed as two different values here), and every path below -- a durable hit republished to
+    the hot slot, or a full miss freshly scanned and published to BOTH layers -- funnels through the
+    SAME single rebind of the module-level slot, never two separate writes a reader could observe
+    half-done. A racing miss on another thread only ever costs redundant, harmless recompute (the
+    scan is a pure function of its inputs); it can never produce a torn key/result pairing."""
     global _SCAN_CACHE
-    key = (id(config), _store_signature(store))
+    content_hash = _config_content_hash(config)
+    store_signature = _store_signature(store)
+    key = (content_hash, store_signature)
+
     cached = _SCAN_CACHE
     if cached is not None and cached[0] == key:
         return cached[1]
-    result = _run_full_panel_scan(store, config)
+
+    durable = SetupsScanCache(resolve_scan_cache_db_path(str(store.root)))
+    durable_key = scan_cache_key(config_content_hash=content_hash, store_signature=store_signature)
+    persisted = durable.lookup(durable_key)
+    if persisted is not None:
+        result = persisted
+    else:
+        result = _run_full_panel_scan(store, config)
+        durable.publish(durable_key, result)
     _SCAN_CACHE = (key, result)
     return result
 
diff --git a/apps/backend/tests/conftest.py b/apps/backend/tests/conftest.py
index ebada0e..2df1969 100644
--- a/apps/backend/tests/conftest.py
+++ b/apps/backend/tests/conftest.py
@@ -23,10 +23,22 @@ def _reset_store_verified_caches():
     test session (harmless for correctness — the cache key is the absolute file path, and
     distinct ``tmp_path`` roots never collide — but unbounded growth over a long suite run is
     still worth avoiding), and any test that intentionally wants a genuinely cold cache can now
-    rely on that being the default starting state rather than re-deriving it itself."""
+    rely on that being the default starting state rather than re-deriving it itself.
+
+    era-fast_wall J-06 additionally resets ``setups.py``'s own in-process hot slot
+    (``_SCAN_CACHE``) via its identical ``_reset_scan_cache_for_tests`` helper. Unlike the two
+    caches above (keyed by absolute file path, so distinct ``tmp_path`` roots never collide), J-06
+    rekeyed that slot on config CONTENT rather than ``id(config)`` — so two unrelated tests using
+    genuinely equal config content against a genuinely equal (e.g. both-empty) store signature could
+    otherwise observe each other's leftover hot-slot entry. Resetting it here, alongside its two
+    siblings, makes every test start from a guaranteed-cold hot slot regardless of ordering (the
+    durable ``SetupsScanCache`` tier needs no such reset — its DB path is derived from each test's
+    own ``tmp_path``-scoped bar store root, so it is already naturally test-isolated)."""
     import app.research.bars as bars_module
     import app.research.datasets as datasets_module
+    import app.research.setups as setups_module
 
     bars_module._reset_verified_cache_for_tests()
     datasets_module._reset_verified_cache_for_tests()
+    setups_module._reset_scan_cache_for_tests()
     yield
diff --git a/apps/backend/tests/test_setups.py b/apps/backend/tests/test_setups.py
index 1cf3057..1076be8 100644
--- a/apps/backend/tests/test_setups.py
+++ b/apps/backend/tests/test_setups.py
@@ -22,6 +22,7 @@ module's central risk)."""
 
 from __future__ import annotations
 
+import dataclasses
 import inspect
 import json
 from datetime import datetime, timezone
@@ -1072,3 +1073,221 @@ def test_concurrent_cold_cache_reads_never_observe_a_torn_key_result_pair(tmp_pa
         "mean some reader saw a torn/partial key-result pairing"
     )
     assert len(results[0]["events"]) >= 1, "the proof must exercise at least one real event"
+
+
+# --- era-fast_wall J-06: the durable setups scan cache (three-tier lookup: hot slot -> durable ->
+# real scan). ``setups_scan_cache.py``'s own module docstring/test file
+# (``test_setups_scan_cache.py``) cover the cache's own mechanics (key composition, byte-identity,
+# corrupted-DB tolerance) in isolation; this section proves ``compute_setups``'s OWN wiring of that
+# cache into its three-tier lookup -- restart simulation, content-hash equality, cache-busting, and
+# the non-vacuous mutation probe (iter-3's lesson, named for exactly this journey in
+# `docs/goal.md`'s BACKGROUND section). --------------------------------------------------------------
+
+
+def test_tc1_hot_slot_cleared_simulating_a_restart_serves_the_durable_cache_with_zero_rescans(
+    tmp_path, monkeypatch,
+):
+    """TC-1: a call-counting spy proves the durable cache -- not a fresh rescan -- answers once the
+    in-process hot slot is cleared (simulating a process restart), and the served result is
+    byte-identical to the original scan."""
+    import app.research.setups as setups_module
+
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    config = _syn_config()
+    original = compute_setups(store, config)  # populates BOTH the hot slot and the durable cache
+
+    setups_module._reset_scan_cache_for_tests()  # simulate a process restart -- hot slot cleared
+
+    calls: list[int] = []
+    real_scan = setups_module._run_full_panel_scan
+
+    def _counting_scan(*args, **kwargs):
+        calls.append(1)
+        return real_scan(*args, **kwargs)
+
+    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _counting_scan)
+
+    restarted = compute_setups(store, config)
+
+    assert calls == [], "a durable-cache hit must cost ZERO calls to the real scan"
+    assert json.dumps(restarted, sort_keys=True) == json.dumps(original, sort_keys=True)
+
+
+def test_tc2_equal_content_but_distinct_config_object_is_a_cache_hit_identity_fragility_gone(
+    tmp_path, monkeypatch,
+):
+    """TC-2: the ``id(config)`` fragility is gone -- a SECOND, freshly-constructed ``Config`` with
+    IDENTICAL field values (a different ``id()``) is a genuine cache hit, served WITHOUT even
+    needing to clear the (still-warm) hot slot -- proving the key itself is content-derived."""
+    import app.research.setups as setups_module
+
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    config = _syn_config()
+    original = compute_setups(store, config)
+
+    second_config = dataclasses.replace(config)
+    assert second_config is not config, "the proof requires a genuinely distinct object"
+
+    calls: list[int] = []
+    real_scan = setups_module._run_full_panel_scan
+
+    def _counting_scan(*args, **kwargs):
+        calls.append(1)
+        return real_scan(*args, **kwargs)
+
+    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _counting_scan)
+
+    second = compute_setups(store, second_config)
+
+    assert calls == [], "a content-equal Config object must be a genuine cache HIT, never id()-keyed"
+    assert json.dumps(second, sort_keys=True) == json.dumps(original, sort_keys=True)
+
+
+def test_tc3_a_setups_family_field_change_busts_the_cache_content_hash_not_fingerprint_alone(
+    tmp_path, monkeypatch,
+):
+    """TC-3: ``config_fingerprint()`` EXCLUDES the ``setups_*``/``tradability_*``/``sr_*`` families
+    (see ``test_setups_config_fields_are_excluded_from_config_fingerprint`` above), so a cache keyed
+    on the fingerprint alone would silently under-invalidate here. The full CONTENT hash must not."""
+    import app.research.setups as setups_module
+
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    config = _syn_config()
+    compute_setups(store, config)
+
+    changed = _syn_config(setups_reaction_threshold_bps=config.setups_reaction_threshold_bps + 5.0)
+    assert changed.config_fingerprint() == config.config_fingerprint(), (
+        "sanity: setups_reaction_threshold_bps is excluded from config_fingerprint"
+    )
+
+    calls: list[int] = []
+    real_scan = setups_module._run_full_panel_scan
+
+    def _counting_scan(*args, **kwargs):
+        calls.append(1)
+        return real_scan(*args, **kwargs)
+
+    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _counting_scan)
+
+    compute_setups(store, changed)
+
+    assert len(calls) == 1, "the CONTENT hash (not config_fingerprint alone) must drive the key"
+
+
+def test_tc4_recording_a_new_5m_series_into_the_store_busts_the_durable_cache_key(tmp_path, monkeypatch):
+    """TC-4: a store-content change (a newly recorded '5m' series) must bust the key even though
+    ``config`` itself is unchanged."""
+    import app.research.setups as setups_module
+
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    config = _syn_config()
+    compute_setups(store, config)
+
+    calls: list[int] = []
+    real_scan = setups_module._run_full_panel_scan
+
+    def _counting_scan(*args, **kwargs):
+        calls.append(1)
+        return real_scan(*args, **kwargs)
+
+    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _counting_scan)
+
+    store.record(
+        symbol="SYN-SETUPS-NEW", timeframe="5m", window_start_utc="2026-03-01T00:00:00Z",
+        window_end_utc="2026-03-01T00:05:00Z", feed="sip",
+        bars=[_bar5m("SYN-SETUPS-NEW", 60, 0, 100, 105, 95, 100, 1_000)],
+    )
+    compute_setups(store, config)
+
+    assert len(calls) == 1, "a newly recorded series must bust the cache and re-run the scan"
+
+
+def test_tc5_deleting_the_durable_db_file_is_harmless_recomputes_once_byte_identical(tmp_path, monkeypatch):
+    """TC-5: deleting the durable cache DB (plus its WAL/SHM sidecars) and clearing the hot slot
+    costs exactly one recompute, byte-identical to the pre-deletion result -- proving the durable
+    layer is a rebuildable accelerator, never a source of truth."""
+    import app.research.setups as setups_module
+    from app.research.setups_scan_cache import resolve_scan_cache_db_path
+
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    config = _syn_config()
+    original = compute_setups(store, config)
+
+    db_path = Path(resolve_scan_cache_db_path(str(store.root)))
+    assert db_path.exists(), "the durable cache DB must exist after a real publish"
+    for suffix in ("", "-wal", "-shm"):
+        sidecar = db_path.parent / (db_path.name + suffix)
+        if sidecar.exists():
+            sidecar.unlink()
+    assert not db_path.exists()
+
+    setups_module._reset_scan_cache_for_tests()  # simulate a restart too -- hot slot cleared
+
+    calls: list[int] = []
+    real_scan = setups_module._run_full_panel_scan
+
+    def _counting_scan(*args, **kwargs):
+        calls.append(1)
+        return real_scan(*args, **kwargs)
+
+    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _counting_scan)
+
+    recomputed = compute_setups(store, config)
+
+    assert len(calls) == 1, "deleting the durable DB must cost exactly one recompute, never a crash"
+    assert json.dumps(recomputed, sort_keys=True) == json.dumps(original, sort_keys=True)
+
+
+def test_tc6_mutation_probe_a_durable_hit_is_returned_verbatim_never_silently_rescanned(tmp_path):
+    """TC-6 (non-vacuous -- iter-3's lesson, named explicitly for J-06 in `docs/goal.md`'s
+    BACKGROUND section): a durable row pre-seeded under the EXACT current key with a DELIBERATELY
+    WRONG payload must be returned VERBATIM -- proving the durable-hit branch is genuinely read, not
+    dead code a naive byte-identity assertion could pass vacuously (a bug that silently fell through
+    to a fresh, CORRECT rescan would otherwise look identical to success)."""
+    import app.research.setups as setups_module
+    from app.research.edge_report_cache import _config_content_hash
+    from app.research.setups import _store_signature
+    from app.research.setups_scan_cache import SetupsScanCache, resolve_scan_cache_db_path, scan_cache_key
+
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    config = _syn_config()
+
+    key = scan_cache_key(
+        config_content_hash=_config_content_hash(config), store_signature=_store_signature(store),
+    )
+    wrong_payload = {"events": [{"id": "deliberately-wrong-fabricated-event", "fabricated": True}]}
+    cache = SetupsScanCache(resolve_scan_cache_db_path(str(store.root)))
+    cache.publish(key, wrong_payload)
+
+    setups_module._reset_scan_cache_for_tests()  # force the durable tier to be the one that answers
+
+    result = compute_setups(store, config)
+
+    assert result == wrong_payload, (
+        "a durable HIT must be served verbatim, never silently replaced by a fresh (correct) rescan"
+    )
+
+
+def test_tc8_durable_publish_failure_never_blocks_compute_setups_from_serving_the_fresh_scan(tmp_path):
+    """TC-8: a corrupted/unusable durable cache DB file never raises out of ``compute_setups`` -- the
+    publish failure is swallowed (``setups_scan_cache.py``'s own discipline) and the freshly-scanned
+    (correct) result is still returned."""
+    from app.research.setups_scan_cache import resolve_scan_cache_db_path
+
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    config = _syn_config()
+
+    db_path = Path(resolve_scan_cache_db_path(str(store.root)))
+    db_path.parent.mkdir(parents=True, exist_ok=True)
+    db_path.write_bytes(b"not a real sqlite database, just garbage bytes " * 20)
+
+    result = compute_setups(store, config)  # must not raise
+
+    assert len(result["events"]) >= 1, "the freshly-scanned (correct) result must still be served"
diff --git a/apps/backend/tests/test_setups_api.py b/apps/backend/tests/test_setups_api.py
index c5d796f..1a9eb83 100644
--- a/apps/backend/tests/test_setups_api.py
+++ b/apps/backend/tests/test_setups_api.py
@@ -126,6 +126,30 @@ def test_no_bar_series_at_all_is_an_honest_empty_registry(ctx):
     assert r.json() == {"events": []}
 
 
+# --- era-fast_wall J-06 (TC-8's HTTP leg): a corrupted durable scan-cache DB never blocks the
+# route -- the publish-failure-swallowed discipline observed through the REAL request path, not
+# just the direct `compute_setups` call `test_setups.py`'s own TC-8 already proves. The route
+# (`list_setups`) wires through to `compute_setups` with zero extra error handling (routes.py's own
+# source), so this is a genuine end-to-end confirmation, not a restatement. ------------------------
+
+
+def test_corrupted_durable_scan_cache_db_never_blocks_the_route_still_200s_with_the_fresh_scan(ctx):
+    from app.research.setups_scan_cache import resolve_scan_cache_db_path
+
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+
+    db_path = Path(resolve_scan_cache_db_path(str(BarStore(bar_dir).root)))
+    db_path.parent.mkdir(parents=True, exist_ok=True)
+    db_path.write_bytes(b"not a real sqlite database, just garbage bytes " * 20)
+
+    r = client.get("/research/setups")
+
+    assert r.status_code == 200
+    body = r.json()
+    assert isinstance(body["events"], list) and len(body["events"]) >= 1
+
+
 # --- The committed real AAPL fixture: J-02's pinned acceptance through the REAL route -----------
 
 
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-fast_wall/telemetry.jsonl   | 6 ++++++
 runs/goal-session-fast_wall/trace/trace.jsonl | 3 +++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
