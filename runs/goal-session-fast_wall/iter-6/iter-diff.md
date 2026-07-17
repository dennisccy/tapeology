# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/README.md b/README.md
index 2610c11..cead3b5 100644
--- a/README.md
+++ b/README.md
@@ -85,7 +85,7 @@ Current capabilities:
 - **The 3-way profit edge report (research API)** — a new endpoint runs `v1`, `structure_tape`, and `structure_tape_map` over every recorded practice-tape window and reports, honestly, how each one actually did — broken down by price-level quality (A/B/C), which side of the market it traded (support or resistance), how price reacted at the touch (rejected, broke, or chopped), and which data feed the window came from. Every dollar figure carries its sample size, a comparison against a random-entry baseline, and the same "simulated — not indicative of live results" register used everywhere else in the app. Real recorded trading windows now exist across a broad slice of the panel, giving the report real touches to measure instead of only the small practice dataset; any cell still short of enough trades honestly labels itself "insufficient sample" rather than manufacturing a result, and an entirely empty report remains a valid, honest outcome whenever nothing yet clears the bar. Computing the full report over the currently recorded data is slow and can take a long time to finish on a first run, showing a loading state throughout rather than a fabricated interim result. The same comparison is available to AI tools through the machine-readable connection, byte-for-byte identical to what a person sees calling the endpoint directly. This report is now visible on the Structure page in the browser as the Edge Report, and remains reachable through the research API and the matching machine-readable tool.
 - **Edge report caching and a permanent record of its findings (research API)** — once the 3-way profit edge report's full computation over recorded data has completed a single time, the result is now remembered in a durable, disk-backed cache and served back within an interactive few seconds on every later request — through the REST API, the machine-readable connection, and the Structure page's Edge Report panel alike — including after a full backend restart. Nothing about what the report measures, how it is computed, or the shape of its response changes; any change to the underlying recorded datasets, registered strategies, or configuration automatically invalidates the cached answer, so the next request recomputes it byte-identically rather than serving something stale. A finished report's findings can also now be permanently appended, as a deliberate one-time step, to the same append-only profit-and-loss record described above — its own dedicated entry, with every data feed and the train/hold-out split kept fully separate from every entry recorded before it. As of today the very first full computation over the currently recorded real data, and its permanent recording, have not yet been run — see the next capability for exactly what the Edge Report panel honestly shows in the meantime.
 - **Safe-by-default Edge Report** — opening the Structure page's Edge Report section, or asking the underlying research endpoint for the report directly, never risks silently starting that full computation as a side effect of simply loading a page — before this update, doing so could pin the backend near 100% CPU for hours with no warning shown anywhere. If a report has already been computed, it — or the honest "No edge-report cells yet." empty state — is shown exactly as before. If nothing has been computed yet, the panel instead shows a plain, prompt "Edge report not computed yet." message with a short explanation of why, answering promptly rather than spinning indefinitely or silently starting work in the background. Starting that computation is now a separate, explicit action — see the next capability.
-- **Operator-run edge report compute** — beneath the "Edge report not computed yet." message, a "Compute edge report" button starts the full three-strategy comparison as a background job without leaving the page. While it runs, a live counter shows how many of the comparison's individual backtests have finished so far, updating automatically with no manual refresh needed. When the computation completes, the finished report renders in place automatically, using the same table already shown for a previously-computed report. If the computation fails partway through, the panel shows the specific error message instead of a generic failure, and the button relabels itself so a fresh attempt is one more click away. Reloading the page, or landing on it, while a compute is running, or after one has already finished or failed, immediately shows the matching state rather than resetting to idle. The same computation can also be started, unattended, from the command line for long background runs.
+- **Operator-run edge report compute** — beneath the "Edge report not computed yet." message, a "Compute edge report" button starts the full three-strategy comparison as a background job without leaving the page. While it runs, a live counter shows how many of the comparison's individual backtests have finished so far — including how many were reused from already-completed work rather than recomputed — updating automatically with no manual refresh needed. When the computation completes, the finished report renders in place automatically, using the same table already shown for a previously-computed report. If the computation fails partway through, the panel shows the specific error message instead of a generic failure, and the button relabels itself so a fresh attempt is one more click away. Reloading the page, or landing on it, while a compute is running, or after one has already finished or failed, immediately shows the matching state rather than resetting to idle. A compute that is interrupted — by a server restart, a crash, or a cancellation — resumes cleanly when re-triggered: it skips every result already durably saved and computes only what's left, finishing far faster than starting over. The same computation can also be started, unattended, from the command line for long background runs, where it can be spread across several worker processes at once for a further speedup; the on-page button always runs single-process by design.
 - **Cockpit price-chart tradable bands and a descriptive confluence chip** — the tradable support/resistance bands from the Structure page's map now also draw directly on the live cockpit price chart while watching a symbol in Simulated or Historical mode: one or two solid price lines per band (rose for resistance, emerald for support), each labeled with side, class, quality score, and whether it sits on a round number — alongside the existing tape-state markers and any declared-thesis lines, without changing how those render. A small descriptive banner appears beneath the chart only when the last traded price sits inside one of those bands AND the live tape reading matches that band's configured rejection-or-breakthrough state — for example "Inside R-band 300.05–300.17 (class A) · tape: Ask Absorption (rejection) · measured history: edge report." The banner states the current condition and points to the edge report as measured history; it never tells you to buy or sell and never predicts an outcome. A simulated ticker with no real recorded price history shows an honest "No tradable map for TICKER" note instead of a fabricated band. Live mode is unchanged — the price chart, and therefore the bands and banner, stay hidden there exactly as before.
 - **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `POST /research/edge-report/compute`, `GET /research/edge-report/compute`, `POST /research/edge-report/compute/cancel`, `GET /meta/ui-routes`.
 - **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, journal, studies, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, profit edge reports, and navigation data a person sees. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
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
 
 
diff --git a/apps/backend/app/research/setups_scan_cache.py b/apps/backend/app/research/setups_scan_cache.py
new file mode 100644
index 0000000..81f4712
--- /dev/null
+++ b/apps/backend/app/research/setups_scan_cache.py
@@ -0,0 +1,176 @@
+"""``SetupsScanCache`` (era-fast_wall J-06) — a durable, rebuildable SQLite cache of ONE row per
+(config content x bar-store content) full-panel touch-event scan ``setups.compute_setups`` performs,
+kept BESIDE (never instead of) that module's own in-process hot slot (``_SCAN_CACHE``). Makes the
+multi-minute scan survive a backend restart -- or simply a freshly-constructed but content-equal
+``Config`` object -- instead of re-paying the full scan every time the hot slot happens to be cold.
+
+THIS MODULE stores a REBUILDABLE RESULT ONLY and OWNS NOTHING — the identical ``EdgeReportCache``/
+``EdgeReportBacktestCache``/``bar_index.py`` discipline (see those modules' own docstrings), applied
+to a full-panel scan result instead of a report or a backtest pair: ``setups._run_full_panel_scan``
+stays the SOLE computer of a scan's result; a cache miss always recomputes byte-identically through
+that ONE function. Deleting the persisted DB file loses nothing and fabricates nothing — the very
+next call simply re-runs the scan and republishes it.
+
+**Durable-only — no in-process hot slot of its own.** ``setups.py`` already owns its own in-process
+hot slot (``_SCAN_CACHE``) for repeated reads of the SAME key within one process's lifetime, so this
+class stays exactly as large as its job needs to be (the ``EdgeReportBacktestCache`` "no abstraction
+until it earns its keep" precedent, applied here since it is ``setups.py``'s hot slot -- not this
+module -- that already covers the repeated-read-within-one-process case). Every read/write opens its
+OWN short-lived connection (the ``JournalStore._read_conn`` precedent, mirrored by every sibling
+durable cache in this codebase) — safe across a future multi-process caller too, since no long-lived
+shared connection object is ever held.
+
+**Key — two parts, sha256 of canonical JSON.** ``config_content_hash`` (the config's ENTIRE field
+content, reused verbatim from ``edge_report_cache._config_content_hash`` by the caller -- never
+re-derived a second time -- rather than ``config.config_fingerprint()`` alone, whose own documented
+exclusion set drops exactly the ``setups_*``/``tradability_*``/``sr_*`` field families the scan
+reads) and ``store_signature`` (the sorted per-series ``(symbol, timeframe, id, checksum)`` tuples
+``setups._store_signature`` already computes). ``scan_cache_key`` accepts both as explicit literals
+(never derived internally from an opaque ``Config``/``BarStore`` object) — the
+``edge_report_backtest_cache.pair_cache_key`` precedent — so each component is independently
+controllable and testable.
+
+**Values stored WITHOUT ``sort_keys``** — the ``EdgeReportCache._insert`` byte-identity discipline: a
+cached scan result, once round-tripped through this cache, must be usable identically to a freshly
+computed one wherever a caller inspects its fields.
+
+**Error handling — never a crash, an accelerator's own failure never blocks serving.** Every method
+independently guards against ``sqlite3.Error`` (covering both connection/pragma failures and query
+failures against a corrupted/unreadable DB file): ``lookup`` treats any such failure as a full miss
+(``None``, forcing a fresh scan through the caller's own canonical path); ``publish`` SWALLOWS any
+such failure entirely (never raises) — the sweep/scan's own correctness never depends on the durable
+write succeeding; a lost row merely costs one recompute on the next call.
+"""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import os
+import sqlite3
+from datetime import datetime, timezone
+from pathlib import Path
+
+from .edge_report_cache import _canonical
+
+__all__ = ["SetupsScanCache", "resolve_scan_cache_db_path", "scan_cache_key"]
+
+# A DIFFERENT env var from EdgeReportCache's/EdgeReportBacktestCache's own -- the three durable
+# caches never collide, never share a path, never share a table.
+_CACHE_DB_ENV = "TAPEOLOGY_SETUPS_CACHE_DB"
+
+# Mirrors every sibling durable cache's identical brief writer-contention tolerance.
+_BUSY_TIMEOUT_MS = 5000
+
+_SCHEMA = """
+CREATE TABLE IF NOT EXISTS setups_scan_cache (
+    cache_key    TEXT PRIMARY KEY,
+    result_json  TEXT NOT NULL,
+    created_utc  TEXT NOT NULL
+)
+"""
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
+def scan_cache_key(*, config_content_hash: str, store_signature: tuple) -> str:
+    """The full key material for ONE full-panel scan (see module docstring) — sha256 of the
+    canonical JSON of both components. A pure function of its two named inputs alone: each is
+    independently controllable, so mutating either (holding the other fixed) always yields a
+    different key — see ``tests/test_setups_scan_cache.py``'s key-busting matrix for the
+    non-vacuous proof."""
+    payload = {
+        "config_content_hash": config_content_hash,
+        "store_signature": [list(item) for item in store_signature],
+    }
+    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
+
+
+def resolve_scan_cache_db_path(bar_dir_resolved: str) -> str:
+    """The cache DB path resolution policy — mirrors ``edge_report_cache.resolve_cache_db_path`` /
+    ``edge_report_backtest_cache.resolve_backtest_cache_db_path`` exactly (env-else-sibling), for a
+    DIFFERENT env var and a DIFFERENT sibling filename: the ``TAPEOLOGY_SETUPS_CACHE_DB`` env var if
+    set, else ``setups_scan_cache.db`` co-located as a SIBLING of the caller's own already-resolved
+    bar directory (e.g. ``.data/bars`` -> ``.data/setups_scan_cache.db`` — the ``get_bar_index``
+    env-else-sibling-of-``bar_dir_resolved()`` shape)."""
+    override = os.environ.get(_CACHE_DB_ENV)
+    if override:
+        return override
+    return os.path.join(os.path.dirname(bar_dir_resolved), "setups_scan_cache.db")
+
+
+class SetupsScanCache:
+    """One durable SQLite row per full-panel scan key — beside ``setups.py``'s own in-process hot
+    slot, never a modification of it. See the module docstring for the full "rebuildable, never a
+    source of truth" contract and the error-handling discipline."""
+
+    def __init__(self, db_path: str) -> None:
+        self._db_path = str(db_path)
+        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
+        try:
+            conn = self._connect()
+            try:
+                with conn:
+                    conn.execute(_SCHEMA)
+            finally:
+                conn.close()
+        except sqlite3.Error:
+            # A corrupted/unreadable file at this path -- never a crash (module docstring). Every
+            # subsequent lookup()/publish() independently re-attempts _connect()+query and hits the
+            # SAME failure mode, so this self-heals with no separate "usable" flag to maintain.
+            pass
+
+    @property
+    def db_path(self) -> str:
+        """The resolved DB file path this cache was constructed with (introspection/tests only)."""
+        return self._db_path
+
+    def _connect(self) -> sqlite3.Connection:
+        """A FRESH, short-lived connection (the ``JournalStore._read_conn`` precedent — never one
+        long-lived connection shared across callers)."""
+        conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=_BUSY_TIMEOUT_MS / 1000.0)
+        conn.row_factory = sqlite3.Row
+        conn.execute("PRAGMA journal_mode=WAL")
+        conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
+        return conn
+
+    def lookup(self, key: str) -> dict | None:
+        """The durable row for ``key``, or ``None`` on a genuine miss — NEVER computes (there is no
+        ``compute_fn`` parameter; a miss is mechanically incapable of running a scan). A
+        corrupted/unreadable DB is treated as a full miss, never a crash (module docstring)."""
+        try:
+            conn = self._connect()
+            try:
+                row = conn.execute(
+                    "SELECT result_json FROM setups_scan_cache WHERE cache_key=?", (key,)
+                ).fetchone()
+            finally:
+                conn.close()
+        except sqlite3.Error:
+            return None
+        return None if row is None else json.loads(row["result_json"])
+
+    def publish(self, key: str, result: dict) -> None:
+        """Durably persist ONE scan's result — one atomic ``INSERT OR REPLACE`` transaction. Stored
+        WITHOUT ``sort_keys`` (see module docstring). A publish failure of ANY kind is SWALLOWED
+        here, never propagated (module docstring) — never blocks the caller that is still holding
+        its own freshly-scanned result."""
+        try:
+            conn = self._connect()
+            try:
+                with conn:
+                    conn.execute(
+                        "INSERT OR REPLACE INTO setups_scan_cache "
+                        "(cache_key, result_json, created_utc) VALUES (?,?,?)",
+                        (key, json.dumps(result), _iso_utc_now()),
+                    )
+            finally:
+                conn.close()
+        except sqlite3.Error:
+            pass
diff --git a/apps/backend/tests/test_setups_scan_cache.py b/apps/backend/tests/test_setups_scan_cache.py
new file mode 100644
index 0000000..e38f066
--- /dev/null
+++ b/apps/backend/tests/test_setups_scan_cache.py
@@ -0,0 +1,321 @@
+"""``SetupsScanCache`` (era-fast_wall J-06) -- store-level discipline, tested standalone (no
+``compute_setups``, no real bar store/scan). Mirrors ``tests/test_edge_report_backtest_cache.py``'s
+own directness: every test here feeds the cache a CHEAP dict instead of a real scan result -- the
+cache mechanics (keying, durability, concurrency, corrupted-DB tolerance) are independent of what a
+real scan actually computes. The WIRING into ``setups.compute_setups`` (the three-tier lookup,
+byte-identity, restart simulation, the non-vacuous mutation probe) is covered separately in
+``tests/test_setups.py``.
+"""
+
+from __future__ import annotations
+
+import json
+import sqlite3
+import threading
+
+from app.research.setups_scan_cache import (
+    SetupsScanCache,
+    resolve_scan_cache_db_path,
+    scan_cache_key,
+)
+
+
+def _base_kwargs() -> dict:
+    return dict(
+        config_content_hash="hash-1",
+        store_signature=(("AAPL", "5m", "series-1", "chk-1"), ("AAPL", "1d", "series-2", "chk-2")),
+    )
+
+
+# One replacement value per key component -- used both to prove the key CHANGES (pure function) and
+# to prove a call-counting spy sees a fresh call for EVERY one of the two (the key-busting matrix).
+_MUTATIONS: dict[str, object] = {
+    "config_content_hash": "hash-2",
+    "store_signature": (("AAPL", "5m", "series-3", "chk-3"),),
+}
+
+
+# --- scan_cache_key: a pure function, non-vacuous key-busting matrix -----------------------------
+
+
+def test_scan_cache_key_is_stable_for_identical_inputs():
+    assert scan_cache_key(**_base_kwargs()) == scan_cache_key(**_base_kwargs())
+
+
+def test_scan_cache_key_changes_when_either_component_changes():
+    base_key = scan_cache_key(**_base_kwargs())
+    for component, new_value in _MUTATIONS.items():
+        mutated = _base_kwargs()
+        mutated[component] = new_value
+        mutated_key = scan_cache_key(**mutated)
+        assert mutated_key != base_key, f"mutating {component!r} alone must change the key"
+
+
+def test_scan_cache_key_mutations_are_pairwise_distinct():
+    """A stronger non-vacuous guard than base-vs-mutated alone: no two DIFFERENT single-component
+    mutations may collide with each other either (would silently mean two distinct scans share one
+    cached row)."""
+    keys = [scan_cache_key(**_base_kwargs())]
+    for component, new_value in _MUTATIONS.items():
+        mutated = _base_kwargs()
+        mutated[component] = new_value
+        keys.append(scan_cache_key(**mutated))
+    assert len(keys) == len(set(keys)), "every one of the 3 scenarios must produce a distinct key"
+
+
+def test_scan_cache_key_store_signature_order_independence_is_the_callers_job_not_this_functions():
+    """``scan_cache_key`` itself is a PURE, literal function of whatever tuple it is handed --
+    ordering stability is ``setups._store_signature``'s own contract (it already sorts), not
+    something this function re-derives. A differently-ORDERED tuple is a genuinely different literal
+    input and therefore correctly produces a different key here."""
+    ordered = (("AAPL", "5m", "a", "1"), ("AAPL", "1d", "b", "2"))
+    reordered = (("AAPL", "1d", "b", "2"), ("AAPL", "5m", "a", "1"))
+    key_a = scan_cache_key(config_content_hash="h", store_signature=ordered)
+    key_b = scan_cache_key(config_content_hash="h", store_signature=reordered)
+    assert key_a != key_b
+
+
+class _CountingScan:
+    """A stub standing in for ``setups._run_full_panel_scan`` (mirrors
+    ``test_edge_report_backtest_cache.py``'s own ``_CountingBacktest`` precedent) — proving the
+    CACHE's mechanics against a cheap stub, independent of what a real scan actually computes."""
+
+    def __init__(self) -> None:
+        self.calls = 0
+
+    def __call__(self) -> dict:
+        self.calls += 1
+        return {"call_number": self.calls}
+
+
+def test_key_busting_matrix_a_call_counting_spy_records_a_new_call_for_every_mutation(tmp_path):
+    """Non-vacuous: a warm row for the base scan, then EACH of the two components mutated in turn
+    (holding the other fixed) forces a fresh 'scan' call — proving each component independently
+    busts the key (a cache silently ignoring one component would fail exactly that case)."""
+    cache = SetupsScanCache(str(tmp_path / "scan_cache.db"))
+    compute = _CountingScan()
+
+    def _lookup_or_compute(kwargs: dict) -> dict:
+        key = scan_cache_key(**kwargs)
+        cached = cache.lookup(key)
+        if cached is not None:
+            return cached
+        result = compute()
+        cache.publish(key, result)
+        return result
+
+    _lookup_or_compute(_base_kwargs())
+    assert compute.calls == 1
+    _lookup_or_compute(_base_kwargs())  # a genuine warm hit -- no new call
+    assert compute.calls == 1
+
+    expected_calls = 1
+    for component, new_value in _MUTATIONS.items():
+        mutated = _base_kwargs()
+        mutated[component] = new_value
+        _lookup_or_compute(mutated)
+        expected_calls += 1
+        assert compute.calls == expected_calls, f"mutating {component!r} must trigger a fresh compute"
+        _lookup_or_compute(mutated)  # a second request for the SAME mutated scan -- must NOT recompute
+        assert compute.calls == expected_calls
+
+
+# --- lookup / publish mechanics -------------------------------------------------------------------
+
+
+def test_cold_lookup_is_none(tmp_path):
+    cache = SetupsScanCache(str(tmp_path / "cache.db"))
+    assert cache.lookup(scan_cache_key(**_base_kwargs())) is None
+
+
+def test_publish_then_lookup_returns_the_result_verbatim(tmp_path):
+    cache = SetupsScanCache(str(tmp_path / "cache.db"))
+    key = scan_cache_key(**_base_kwargs())
+    result = {"events": [{"id": "abc", "reaction": "rejected"}]}
+
+    cache.publish(key, result)
+
+    assert cache.lookup(key) == result
+
+
+def test_result_round_trips_byte_identically_through_json_persistence(tmp_path):
+    """Floats, nested lists/dicts, and ``None`` all survive a JSON round-trip through the durable
+    layer byte-identically (structural equality on the round-tripped dict)."""
+    cache = SetupsScanCache(str(tmp_path / "cache.db"))
+    key = scan_cache_key(**_base_kwargs())
+    result = {
+        "events": [
+            {
+                "id": "abc",
+                "forward_returns": [{"horizon_bars": 78, "return_fraction": -0.007453190329031024}],
+                "reaction_boundary_truncated": False,
+                "tape_timeline": [],
+            },
+        ],
+    }
+
+    cache.publish(key, result)
+
+    assert cache.lookup(key) == result
+
+
+def test_second_publish_under_the_same_key_replaces_the_row(tmp_path):
+    cache = SetupsScanCache(str(tmp_path / "cache.db"))
+    key = scan_cache_key(**_base_kwargs())
+
+    cache.publish(key, {"events": [], "version": 1})
+    cache.publish(key, {"events": [], "version": 2})
+
+    assert cache.lookup(key) == {"events": [], "version": 2}
+
+    conn = sqlite3.connect(str(tmp_path / "cache.db"))
+    try:
+        (count,) = conn.execute(
+            "SELECT COUNT(*) FROM setups_scan_cache WHERE cache_key=?", (key,)
+        ).fetchone()
+    finally:
+        conn.close()
+    assert count == 1  # INSERT OR REPLACE -- never a duplicate row under one key
+
+
+def test_stored_value_is_not_sort_keys_serialized(tmp_path):
+    """The ``EdgeReportCache._insert`` byte-identity discipline, applied here: storage preserves the
+    dict's OWN insertion order rather than alphabetizing it (``json.dumps`` default, never
+    ``sort_keys=True``) — a stored row's raw bytes reflect the caller's own field order."""
+    cache = SetupsScanCache(str(tmp_path / "cache.db"))
+    key = scan_cache_key(**_base_kwargs())
+    result = {"zeta": 1, "alpha": 2, "middle": 3}  # deliberately not alphabetical
+
+    cache.publish(key, result)
+
+    conn = sqlite3.connect(str(tmp_path / "cache.db"))
+    try:
+        (raw,) = conn.execute(
+            "SELECT result_json FROM setups_scan_cache WHERE cache_key=?", (key,)
+        ).fetchone()
+    finally:
+        conn.close()
+    assert raw == json.dumps(result)  # NOT json.dumps(result, sort_keys=True)
+
+
+# --- durability across a simulated backend restart -------------------------------------------------
+
+
+def test_durability_across_a_simulated_restart_serves_the_prior_row(tmp_path):
+    db_path = str(tmp_path / "cache.db")
+    key = scan_cache_key(**_base_kwargs())
+    original = SetupsScanCache(db_path)
+    original.publish(key, {"events": [{"id": "real"}]})
+
+    restarted = SetupsScanCache(db_path)  # a brand-new instance, no in-process state at all
+
+    assert restarted.lookup(key) == {"events": [{"id": "real"}]}
+
+
+def test_deleting_the_db_file_is_harmless_a_fresh_instance_starts_cold(tmp_path):
+    db_path = tmp_path / "cache.db"
+    key = scan_cache_key(**_base_kwargs())
+    cache = SetupsScanCache(str(db_path))
+    cache.publish(key, {"events": [{"id": "real"}]})
+    assert cache.lookup(key) == {"events": [{"id": "real"}]}
+
+    for suffix in ("", "-wal", "-shm"):
+        sidecar = db_path.parent / (db_path.name + suffix)
+        if sidecar.exists():
+            sidecar.unlink()
+
+    fresh = SetupsScanCache(str(db_path))
+    assert fresh.lookup(key) is None  # loses nothing it shouldn't -- an honest cold miss
+
+
+# --- error handling: never a crash, never blocks the caller (goal.md's own error-cases clause) -----
+
+
+def test_construction_against_a_corrupted_file_never_raises(tmp_path):
+    db_path = tmp_path / "garbage.db"
+    db_path.write_bytes(b"not a real sqlite file, just garbage bytes " * 20)
+
+    SetupsScanCache(str(db_path))  # must not raise
+
+
+def test_lookup_on_a_corrupted_db_file_returns_none_never_crashes(tmp_path):
+    db_path = tmp_path / "garbage.db"
+    db_path.write_bytes(b"not a real sqlite file, just garbage bytes " * 20)
+    cache = SetupsScanCache(str(db_path))
+
+    assert cache.lookup("any-key") is None
+
+
+def test_publish_on_a_corrupted_db_file_is_swallowed_never_crashes(tmp_path):
+    db_path = tmp_path / "garbage.db"
+    db_path.write_bytes(b"not a real sqlite file, just garbage bytes " * 20)
+    cache = SetupsScanCache(str(db_path))
+
+    cache.publish("some-key", {"events": []})  # must not raise, whether or not it actually persisted
+
+
+# --- concurrency: many THREADS publishing distinct keys never crash or corrupt each other ----------
+
+
+def test_many_threads_publishing_distinct_keys_concurrently_never_lose_or_corrupt_a_row(tmp_path):
+    cache = SetupsScanCache(str(tmp_path / "cache.db"))
+    n_threads = 16
+
+    def _publish_one(i: int) -> None:
+        kwargs = _base_kwargs()
+        kwargs["config_content_hash"] = f"hash-{i}"
+        key = scan_cache_key(**kwargs)
+        cache.publish(key, {"events": [{"i": i}]})
+
+    threads = [threading.Thread(target=_publish_one, args=(i,)) for i in range(n_threads)]
+    for t in threads:
+        t.start()
+    for t in threads:
+        t.join(timeout=10)
+
+    for i in range(n_threads):
+        kwargs = _base_kwargs()
+        kwargs["config_content_hash"] = f"hash-{i}"
+        key = scan_cache_key(**kwargs)
+        assert cache.lookup(key) == {"events": [{"i": i}]}
+
+
+# --- resolve_scan_cache_db_path: env-else-sibling-of-bar-dir (mirrors resolve_cache_db_path /
+# resolve_backtest_cache_db_path) --------------------------------------------------------------------
+
+
+def test_resolve_scan_cache_db_path_defaults_to_a_sibling_of_the_bar_dir(tmp_path, monkeypatch):
+    monkeypatch.delenv("TAPEOLOGY_SETUPS_CACHE_DB", raising=False)
+    bar_dir = str(tmp_path / "bars")
+
+    resolved = resolve_scan_cache_db_path(bar_dir)
+
+    assert resolved == str(tmp_path / "setups_scan_cache.db")
+
+
+def test_resolve_scan_cache_db_path_honors_the_env_override(tmp_path, monkeypatch):
+    override = str(tmp_path / "custom" / "scan_cache.db")
+    monkeypatch.setenv("TAPEOLOGY_SETUPS_CACHE_DB", override)
+
+    resolved = resolve_scan_cache_db_path(str(tmp_path / "bars"))
+
+    assert resolved == override
+
+
+def test_resolve_scan_cache_db_path_never_collides_with_sibling_cache_paths(tmp_path, monkeypatch):
+    """The three durable caches (whole-report, per-pair sub-results, setups scan) must resolve to
+    DIFFERENT default sibling filenames beside the SAME parent directory — a real regression this
+    test would catch (accidentally reusing a sibling cache's own filename)."""
+    monkeypatch.delenv("TAPEOLOGY_SETUPS_CACHE_DB", raising=False)
+    monkeypatch.delenv("TAPEOLOGY_EDGE_REPORT_CACHE_DB", raising=False)
+    monkeypatch.delenv("TAPEOLOGY_EDGE_SWEEP_CACHE_DB", raising=False)
+    from app.research.edge_report_backtest_cache import resolve_backtest_cache_db_path
+    from app.research.edge_report_cache import resolve_cache_db_path
+
+    parent = str(tmp_path / "bars")
+    resolved = {
+        resolve_scan_cache_db_path(parent),
+        resolve_cache_db_path(parent),
+        resolve_backtest_cache_db_path(parent),
+    }
+    assert len(resolved) == 3
```
