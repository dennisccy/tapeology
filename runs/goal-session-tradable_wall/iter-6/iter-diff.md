# Iteration diff (bounded)

Files changed: 7. Shown in full: 6.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/frontend/app/structure/page.tsx` (917 lines not shown)

```diff
diff --git a/README.md b/README.md
index 5624626..8a3c105 100644
--- a/README.md
+++ b/README.md
@@ -79,7 +79,7 @@ Current capabilities:
 - **Strategy registry and champion panel on the Structure page** — beneath the confluence-zones table, a Registry section shows the two trading strategies the system knows about, `v1` and `structure_tape`, each as a card listing its entry rule and its exit rules — stop distance, a reward target where the strategy defines one (only `structure_tape` does), the tape-state-flip exit, the time horizon, and the dataset-end exit. The `structure_tape` card additionally shows three small tables — stop distance, reward target, and simulated position size — each broken out by A/B/C confluence class. A Champion panel above the two cards names the strategy/profile pair currently favored (today `v1` on the `default` profile) and a caption confirms this agrees with the same champion shown on the Performance page. The section loads automatically as soon as the Structure page opens — no symbol or as-of time is required — every value is read verbatim from the backend with nothing calculated in the browser, and an explicit "registry unavailable" message replaces the whole section, with no guessed fallback, if the backend can't be reached.
 - **structure_tape-vs-v1 comparison on the Structure page** — beneath the Registry section, a Comparison section lets you choose a registered dataset and run both `structure_tape` and the champion strategy `v1` over it as an offline research job (it places nothing and never touches an order path); each side's progress is shown independently as it moves from Queued to Running (with a live count of events processed) to Done, and the two result cards populate automatically once both finish, with no manual refresh. It then shows both strategies' results side by side: trade count, net return in R and dollars, win rate, and maximum drawdown — a strategy that took zero trades shows an honest "no trades (n=0)" instead of a misleading zero — plus a per-class A/B/C breakdown of the same figures with an explicit "insufficient sample" label wherever a class has too few trades to trust. The always-visible "simulated — assumed fees/slippage — not indicative of live results" register is shown exactly as the backend serves it, never a rephrased copy. A read-only Champion panel beside the results confirms the champion is unaffected — this comparison never promotes a strategy or writes to the PnL ledger, no matter what it finds — and a Founding baseline panel shows the ledger's first recorded row for reference. Every number is read verbatim from the same backtest report the research API and command-line tool already serve. On the committed keyless sample data this honestly shows `structure_tape` arming too few (or zero) trades to trust a result, exactly the "not enough evidence yet" finding the underlying research tool already reports — the champion stays `v1` on `default`. No datasets registered, a comparison still running, a failed or cancelled run, and the backend being unreachable each show their own distinct, explicit message rather than a blank or guessed result.
 - **Tradable level map (research API)** — distills a symbol's raw support/resistance levels (which can number in the thousands for a heavily traded stock) down to at most 10 price "bands" total — the handful of price zones actually worth marking on a chart. Each band carries its price range, whether it is support or resistance, a quality score, how many underlying levels back it up, whether it sits on a psychologically "round" price, and an inherited A/B/C conviction class where one applies. The map for any given day is built using only data fully available before that trading day started — mirroring how a trader marks up charts before the open — with weekends and market holidays handled automatically by falling back to whichever trading day actually closed last. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
-- **Touch-event scanner and case-study registry (research API)** — walks every stored trading session in a 12-symbol panel's recorded price history and checks each session's actual price action against that session's own tradable level map, built strictly from data available before the session opened, so a later session's data can never change an earlier one's already-recorded result. Every genuine touch of a band is logged with its outcome — rejected and turned away, broken straight through, or chopped near the wall with no clear outcome — together with how far price moved by two later checkpoints. Run against real, freshly fetched price history for the full panel, the registry already holds several hundred touch events across all 12 symbols, a healthy mix of breakouts, rejections, and chops, with identical requests always returning byte-identical results. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
+- **Touch-event scanner and case-study registry (research API)** — walks every stored trading session in a 12-symbol panel's recorded price history and checks each session's actual price action against that session's own tradable level map, built strictly from data available before the session opened, so a later session's data can never change an earlier one's already-recorded result. Every genuine touch of a band is logged with its outcome — rejected and turned away, broken straight through, or chopped near the wall with no clear outcome — together with how far price moved by two later checkpoints; a touch too recent to have built up the usual follow-up window is honestly labeled with exactly how much less time its verdict is based on, rather than being shown as an ordinary result. Run against real, freshly fetched price history for the full panel, the registry already holds several hundred touch events across all 12 symbols, a healthy mix of breakouts, rejections, and chops, with identical requests always returning byte-identical results; because scanning the full panel is expensive, the scan result is remembered after the first request, so repeat lookups return in a fraction of a second instead of re-scanning every time. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
 - **Real tape recorded and joined at wall-touch events (command-line research tool + research API)** — with market-data vendor credentials configured, a dedicated recording tool captures a real trade-by-trade market-data window (an hour before through 90 minutes after) around the best-scoring touch events from the case-study registry, spreading its picks across as many different stocks as possible and always including the project's pinned reference example. Once a touch event has a matching real recording, opening that event's detail view replays the frozen tape-reading engine over the recording and attaches a timeline of what buyers and sellers were actually doing around the touch — for example, sellers absorbing at the ask right before a rejection, or buyers in control through a break. Events with no matching recording show an honestly empty timeline rather than an invented one. A committed real-data sample keeps this timeline check running with no credentials required. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
 - **A third registered strategy, `structure_tape_map` (research API)** — the app now has three registered ways of simulating trades against historical data: the original `v1`, the frozen `structure_tape` (which trades off the raw list of thousands of individual price levels), and this new one, which trades off the same small handful of tradable bands the level map produces instead. It reuses the exact same class-scaled stop/target/position-sizing rules as `structure_tape` — only which levels it watches differs. Registering it changes nothing about `v1`, `structure_tape`, or their past results. It is runnable through the existing backtest API; today it is only exercised automatically as part of the 3-way edge report below, and there is no button yet to pick it directly in the browser.
 - **The 3-way profit edge report (research API)** — a new endpoint runs `v1`, `structure_tape`, and `structure_tape_map` over every recorded practice-tape window and reports, honestly, how each one actually did — broken down by price-level quality (A/B/C), which side of the market it traded (support or resistance), how price reacted at the touch (rejected, broke, or chopped), and which data feed the window came from. Every dollar figure carries its sample size, a comparison against a random-entry baseline, and the same "simulated — not indicative of live results" register used everywhere else in the app. With only the small practice dataset available today the report is honestly empty — no strategy yet has enough recorded real-world touches to report a result — rather than a manufactured one; once real trading windows are recorded it will start showing real, if still small-sample, numbers. The same comparison is available to AI tools through the machine-readable connection, byte-for-byte identical to what a person sees calling the endpoint directly. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
diff --git a/apps/backend/app/research/setups.py b/apps/backend/app/research/setups.py
index 7e39887..ebaeb46 100644
--- a/apps/backend/app/research/setups.py
+++ b/apps/backend/app/research/setups.py
@@ -109,13 +109,17 @@ than silently pairing a definitive ``reaction`` label with a horizon-0 ``forward
 exactly when it did not). Neither field ever changes ``reaction`` itself or excludes the event --
 see ``_reaction_and_forward_returns``'s own docstring for the exact boundary condition.
 
-**B3 -- a process-local memoized scan (era-5B iter-5).** ``GET /research/setups``,
-``GET /research/setups/{id}``, and ``edge_report.run_strategy_comparison_report`` each call
-``compute_setups(store, config)`` independently; on the populated 12-symbol panel the underlying
-scan takes minutes, so without a cache a single page load could trigger it multiple times over. The
-PUBLIC ``compute_setups`` below is now a thin, byte-identical memoizing wrapper around the real scan
-(renamed ``_run_full_panel_scan``) -- see its own docstring for the caching contract (process-local,
+**B3 -- a process-local memoized scan (era-5B iter-5; made atomic in iter-6).** ``GET
+/research/setups``, ``GET /research/setups/{id}``, and
+``edge_report.run_strategy_comparison_report`` each call ``compute_setups(store, config)``
+independently; on the populated 12-symbol panel the underlying scan takes minutes, so without a
+cache a single page load could trigger it multiple times over. The PUBLIC ``compute_setups`` below
+is now a thin, byte-identical memoizing wrapper around the real scan (renamed
+``_run_full_panel_scan``) -- see its own docstring for the caching contract (process-local,
 store-content-keyed, rebuildable, never a second source of truth -- the ``bar_index.py`` precedent).
+iter-6 hardened the publish to a single atomic ``(key, result)`` tuple rebind (see the ``_SCAN_CACHE``
+block comment below) once this iteration became the first caller to fire all three consumers
+concurrently from one browser page load.
 """
 
 from __future__ import annotations
@@ -344,7 +348,25 @@ def _event_sort_key(event: dict) -> tuple:
 # unbounded dict) is intentional: this codebase runs ONE bar store behind ONE process, so there is
 # never more than one "current" scan worth remembering, and a single slot cannot grow unbounded
 # across a long-lived process or an entire test suite's run.
-_SCAN_CACHE: dict[str, object] = {"key": None, "result": None}
+#
+# --- Atomic publish (era-5B iter-6 B3 hardening) ------------------------------------------------
+# The slot is ONE immutable ``(key, result)`` tuple (or ``None`` before anything is ever cached) --
+# NEVER a two-key mutable dict written in two separate statements. iter-6 is the first caller to
+# fire ``/setups`` + ``/setups/{id}`` + ``/edge-report`` concurrently from a single page load (a
+# FastAPI sync route handler runs in a thread pool), and the PRIOR two-write dict form
+# (``_SCAN_CACHE["key"] = key`` THEN ``_SCAN_CACHE["result"] = result``) had a genuine torn-read
+# window: a late-arriving reader could observe a freshly-published ``key`` paired with the SLOT'S
+# STILL-STALE (possibly ``None``, on a first-ever cold cache) ``result``, since the two writes are
+# not one atomic step. Publishing a single already-built ``(key, result)`` tuple removes that window
+# by construction: CPython rebinds a module-level name via one bytecode store, so a concurrent
+# reader always observes EITHER the entire previous publish (fully paired) or nothing yet (a safe
+# cache miss that recomputes) -- never a half-written pairing. Readers likewise take exactly ONE
+# local reference to the slot (`cached = _SCAN_CACHE`) before inspecting it, so a rebind by another
+# thread mid-check can never be observed as two different values within the same read. See
+# ``tests/test_setups.py``'s
+# ``test_concurrent_cold_cache_reads_never_observe_a_torn_key_result_pair`` for the regression
+# proof.
+_SCAN_CACHE: tuple[tuple, dict] | None = None
 
 
 def _store_signature(store: BarStore) -> tuple:
@@ -369,13 +391,21 @@ def compute_setups(store: BarStore, config: Config) -> dict:
     Served from the B3 process-local scan cache (see the block comment above) whenever ``store``'s
     content signature and ``config``'s identity match the last computed call; otherwise this runs
     the real scan (``_run_full_panel_scan``) once and remembers it. Byte-identical either way -- the
-    cache changes nothing about WHAT is returned, only whether it is recomputed."""
+    cache changes nothing about WHAT is returned, only whether it is recomputed.
+
+    Atomic against concurrent callers (era-5B iter-6 B3 hardening): ``cached`` is read ONCE into a
+    local (never re-read mid-function, so a concurrent rebind by another thread cannot be observed
+    as two different values here), and a cache miss publishes the freshly computed ``(key, result)``
+    as a SINGLE rebind of the module-level slot -- never two separate writes a reader could observe
+    half-done. A racing cache miss on another thread only ever costs redundant, harmless recompute
+    (the scan is a pure function of its inputs); it can never produce a torn key/result pairing."""
+    global _SCAN_CACHE
     key = (id(config), _store_signature(store))
-    if _SCAN_CACHE["key"] == key:
-        return _SCAN_CACHE["result"]
+    cached = _SCAN_CACHE
+    if cached is not None and cached[0] == key:
+        return cached[1]
     result = _run_full_panel_scan(store, config)
-    _SCAN_CACHE["key"] = key
-    _SCAN_CACHE["result"] = result
+    _SCAN_CACHE = (key, result)
     return result
 
 
diff --git a/apps/backend/tests/test_setups.py b/apps/backend/tests/test_setups.py
index aaa47c2..1cf3057 100644
--- a/apps/backend/tests/test_setups.py
+++ b/apps/backend/tests/test_setups.py
@@ -975,3 +975,100 @@ def test_enriched_detail_read_never_leaks_into_the_shared_cached_list(tmp_path):
         "the enriched read must never leak into the shared cached list"
     )
     assert json.dumps(listed_before, sort_keys=True) == json.dumps(listed_after, sort_keys=True)
+
+
+# --- B3 atomicity hardening (era-5B iter-6) ------------------------------------------------------
+# iter-6 is the first caller to fire `/setups` + `/setups/{id}` + `/edge-report` concurrently from
+# one browser page load against a possibly-cold scan cache -- see the `_SCAN_CACHE` block comment
+# in setups.py for the exact torn-read hazard the prior two-key dict form had. TWO tests, each
+# covering a different failure mode:
+#   * the STRUCTURAL guard below proves the fix DETERMINISTICALLY (never relies on winning a GIL
+#     timing race): the historical bug was two SEPARATE writes to two dict keys, and the narrow
+#     window between them is far too small for any wall-clock trick in a test to land on reliably
+#     (confirmed empirically while developing this test: the behavioral test below passed 5/5 runs
+#     against the deliberately-reverted OLD two-key-dict implementation -- a real proof that a
+#     purely behavioral/timing-based test alone would give false confidence here);
+#   * the BEHAVIORAL test after it proves the CURRENT implementation genuinely tolerates concurrent
+#     callers under real thread contention -- no crash, no None, byte-identical results everywhere.
+
+
+def test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes():
+    """The DETERMINISTIC half of the B3 atomicity proof (see the section comment above for why a
+    timing-based test alone cannot be trusted here): ``compute_setups`` must publish the cache via
+    EXACTLY ONE assignment to the shared module-level slot -- never the old two-key-dict shape
+    (``_SCAN_CACHE["key"] = ...`` THEN ``_SCAN_CACHE["result"] = ...``), which is the literal
+    torn-read hazard this iteration closes. Mirrors this file's own established
+    ``inspect.getsource``-based architecture guards (e.g.
+    ``test_setups_module_reuses_compute_tradability_verbatim_never_a_second_map_engine``,
+    ``test_compute_setups_itself_never_touches_the_dataset_store``)."""
+    src = inspect.getsource(compute_setups)
+
+    # The exact historical bug shape must never reappear.
+    assert '_SCAN_CACHE["key"]' not in src, "the old two-key dict publish must not return"
+    assert '_SCAN_CACHE["result"]' not in src, "the old two-key dict publish must not return"
+    assert "_SCAN_CACHE.update(" not in src, "an in-place dict update is the identical hazard"
+
+    # Exactly one publish, and it is a single rebind of the whole slot (`global` + one `= (` on the
+    # module-level name) -- never two statements that could be observed half-done.
+    rebinds = [line for line in src.splitlines() if line.strip().startswith("_SCAN_CACHE = ")]
+    assert len(rebinds) == 1, (
+        f"expected exactly ONE atomic rebind of _SCAN_CACHE, found {len(rebinds)}: {rebinds}"
+    )
+    assert "global _SCAN_CACHE" in src, "a module-level rebind from inside the function needs `global`"
+
+
+def test_concurrent_cold_cache_reads_never_observe_a_torn_key_result_pair(tmp_path, monkeypatch):
+    """Many threads racing a COLD cache (nothing published yet) with a deliberately widened publish
+    window (a small sleep injected into the scan, forcing genuine overlap around the moment the
+    winning thread's result would be published) must ALL return a real, non-`None`,
+    byte-identical result -- never a crash and never a torn key/result pairing (a result that is
+    `None`, or one that fails to match every other thread's own result). Uses a fresh `Config(...)`
+    (never previously cached, per the module's own `id(config)` keying) so this test can never
+    accidentally observe a DIFFERENT test's leftover cache entry."""
+    import threading
+    import time
+
+    import app.research.setups as setups_module
+
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    config = _syn_config()
+
+    real_scan = setups_module._run_full_panel_scan
+
+    def _slow_scan(*args, **kwargs):
+        result = real_scan(*args, **kwargs)
+        time.sleep(0.05)  # widen the window so concurrent callers genuinely overlap the publish
+        return result
+
+    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _slow_scan)
+
+    thread_count = 16
+    results: list[dict | None] = [None] * thread_count
+    errors: list[BaseException] = []
+    start_barrier = threading.Barrier(thread_count)
+
+    def _call(index: int) -> None:
+        start_barrier.wait()  # every thread reaches compute_setups at roughly the same instant
+        try:
+            results[index] = compute_setups(store, config)
+        except BaseException as exc:  # pragma: no cover -- failure path only
+            errors.append(exc)
+
+    threads = [threading.Thread(target=_call, args=(i,)) for i in range(thread_count)]
+    for t in threads:
+        t.start()
+    for t in threads:
+        t.join(timeout=10.0)
+
+    assert errors == [], f"a concurrent cold-cache read raised (never a torn read, never a crash): {errors}"
+    assert all(r is not None for r in results), (
+        "every concurrent caller must return a real result -- a None here IS the torn-read bug "
+        "(a published key paired with the slot's still-stale/None result)"
+    )
+    expected = json.dumps(results[0], sort_keys=True)
+    assert all(json.dumps(r, sort_keys=True) == expected for r in results), (
+        "every concurrent caller must observe the SAME byte-identical result -- a mismatch would "
+        "mean some reader saw a torn/partial key-result pairing"
+    )
+    assert len(results[0]["events"]) >= 1, "the proof must exercise at least one real event"
diff --git a/apps/frontend/app/structure/page.tsx b/apps/frontend/app/structure/page.tsx
index 9a07823..f3539f1 100644
--- a/apps/frontend/app/structure/page.tsx
+++ b/apps/frontend/app/structure/page.tsx
@@ -6,14 +6,19 @@ import {
   fetchBacktest,
   fetchBarSeriesList,
   fetchDatasets,
+  fetchEdgeReport,
   fetchLevels,
   fetchPnlLedger,
   fetchProfiles,
+  fetchSetupDetail,
+  fetchSetups,
   fetchStrategies,
+  fetchTradability,
   recordBarSeries,
 } from "@/lib/api";
 import type {
   Backtest,
+  BacktestAggregate,
   BacktestClassAggregate,
   BacktestResult,
   BarSeriesListResult,
@@ -21,38 +26,56 @@ import type {
   ConfluenceZone,
   Dataset,
   DatasetsListResult,
+  EdgeReportCell,
+  EdgeReportResponse,
+  EdgeReportSurvivingCell,
   LevelsResponse,
   PnlLedger,
   ProfilesPayload,
+  SetupEvent,
   Strategy,
   StrategiesPayload,
+  TradabilityBand,
+  TradabilityResponse,
 } from "@/lib/types";
 import { SymbolSearch } from "@/components/SymbolSearch";
 import { StructureChart } from "@/components/StructureChart";
 import { Panel } from "@/components/Panel";
 import { FeedBasisBadge } from "@/components/FeedBasisBadge";
 
-// The /structure page (J-01 + J-02 + J-03 + J-05) — the era-4 structure stack's browser home, now
-// complete. For a chosen symbol + as-of time it renders a price chart with one dashed line per S/R
-// level plus a confluence-zones table badged A/B/C (J-01); below that, a read-only Registry section
-// shows the two registered strategies plus the current champion (J-02); below THAT, a Comparison
-// section runs `structure_tape` against the champion `v1` over a chosen dataset and renders both
-// strategies' aggregates + per-class A/B/C breakdown side by side, beside the champion pointer and
-// the founding PnL-ledger baseline row (J-03). Reached from the top-bar link, served by
+// The /structure page — the era-4/5/5B structure stack's browser home. For a chosen symbol +
+// as-of time it renders a price chart with one dashed line per S/R level plus a confluence-zones
+// table badged A/B/C (era-4 J-01); below that, a read-only Registry section shows the registered
+// strategies plus the current champion (era-4 J-02); below THAT, a Comparison section runs
+// `structure_tape` against the champion `v1` over a chosen dataset and renders both strategies'
+// aggregates + per-class A/B/C breakdown side by side, beside the champion pointer and the
+// founding PnL-ledger baseline row (era-4 J-03). Reached from the top-bar link, served by
 // GET /meta/ui-routes (data-driven NavBar — no client hardcoding; see apps/backend/app/meta.py
 // UI_ROUTES). Follows the /performance page pattern: client component, no business logic,
 // canonical endpoints read verbatim, `{ok, data, error}`-shaped fetch results.
 //
-// Era-5 J-05 adds the page's ONE new explicit write action: a fetch-control section (symbol +
-// timeframe + UTC date range + a "Fetch from Yahoo Finance" button) above the Levels & Zones form.
-// Submitting POSTs `/research/bars` (keyless; store-first — an already-fetched window is served
-// from storage with zero network calls, never a `409`), then loads the fetched symbol/window-end
-// through the EXISTING Levels & Zones read path (`handleLoad` — zero new rendering code, zero
-// client recomputation). A "Yahoo Finance" provenance badge (the SAME `FeedBasisBadge` the cockpit
-// uses, keyed off the charted series' own `feed` field) renders beside the chart. The fetch
-// control computes no level/zone/PnL/champion value and never promotes.
+// Era-5 J-05 added the page's first explicit write action: a fetch-control section (symbol +
+// timeframe + UTC date range + a "Fetch from Yahoo Finance" button). Submitting POSTs
+// `/research/bars` (keyless; store-first — an already-fetched window is served from storage with
+// zero network calls, never a `409`), then loads the fetched symbol/window-end through the
+// EXISTING Load path (`handleLoad`). A "Yahoo Finance" provenance badge (the SAME `FeedBasisBadge`
+// the cockpit uses, keyed off the charted series' own `feed` field) renders beside the raw-levels
+// chart. The fetch control computes no level/zone/PnL/champion value and never promotes.
 //
-// NINE canonical endpoints (eight read, one write), rendered VERBATIM and nothing else:
+// Era-5B J-05 (this iteration) DECLUTTERS the page: **Tradable Map** (era-5B J-01's ≤10
+// quality-scored bands) is now the default view the Load form drives, with the prior raw
+// levels/confluence-zones rendering moved behind an explicit, off-by-default "Show raw levels"
+// toggle (byte-identical when on — zero change to that code path). Two new sections follow:
+// **Case Studies** (era-5B J-02's touch-event registry, filterable by symbol/reaction, with a
+// row drill-in showing the era-5B J-03 tape-at-the-wall timeline when a dataset was recorded) and
+// **Edge Report** (era-5B J-04's 3-way `v1` / `structure_tape` / `structure_tape_map` comparison,
+// register-carrying, honest even when every cell is `insufficient_sample`). The era-5 fetch
+// control, provenance badge, Registry, and Comparison sections are unchanged, only repositioned
+// below the three new sections (Foundation invariant — nothing existing regresses). Every new
+// value is read VERBATIM from its owning endpoint; this iteration recomputes nothing (the
+// coherence-auditor's central rail for J-05).
+//
+// THIRTEEN canonical endpoints (twelve read, one write), rendered VERBATIM and nothing else:
 //   * GET /research/levels?symbol=&as_of=  (Data Contract row 39) — levels + confluence zones +
 //     the `no_bar_series_for_symbol` honesty flag. The A/B/C badge is `zone.class`, the score is
 //     `zone.score` — neither is ever recomputed from breadth or member strength.
@@ -61,36 +84,56 @@ import { FeedBasisBadge } from "@/components/FeedBasisBadge";
 //     the already-served `symbol` field to find candles for the chart — the SAME filtering
 //     discipline NavBar already applies to `nav: true` (filtering already-served rows is not a
 //     recomputation of any value).
-//   * POST /research/bars  (Data Contract row 38, J-05) — the fetch control's one write action:
-//     fetch-or-store-first-serve a real Yahoo bar series for {symbol, timeframe, start, end}. The
-//     response's own `feed`/`symbol`/`window_end_utc` seed the existing read path above; nothing
-//     from this response is rendered directly.
-//   * GET /research/strategies  (Data Contract row 40/41, J-02) — the strategy registry (`v1` +
-//     `structure_tape`) + the champion pointer. Fetched on mount, independent of the Levels & Zones
-//     Load button (the registry and champion are populated even keyless).
+//   * POST /research/bars  (Data Contract row 38, era-5 J-05) — the fetch control's one write
+//     action: fetch-or-store-first-serve a real Yahoo bar series for {symbol, timeframe, start,
+//     end}. The response's own `feed`/`symbol`/`window_end_utc` seed the existing read path above;
+//     nothing from this response is rendered directly.
+//   * GET /research/strategies  (Data Contract row 40/41, era-4 J-02) — the strategy registry
+//     (`v1` + `structure_tape` + `structure_tape_map`) + the champion pointer. Fetched on mount,
+//     independent of the Load button (the registry and champion are populated even keyless).
 //   * GET /research/profiles  (Data Contract row 33) — read ONLY to cross-check its `champion`
 //     against `/research/strategies`'s own `champion` (both read the SAME store pointer — never a
 //     second champion source).
-//   * GET /research/datasets  (Data Contract row 30, J-03) — every registered dataset, fetched on
-//     mount to populate the Comparison section's dataset selector.
-//   * POST /research/backtests + GET /research/backtests/{id}  (Data Contract row 31, J-03) — the
-//     Comparison section's "Run comparison" starts TWO backtests (`v1` + `structure_tape`, both
-//     `profile=default`) on the chosen dataset and polls both to a terminal status, reusing the
-//     Studies job/poll PATTERN (not its endpoint). Every aggregate, per-class value, and the
+//   * GET /research/datasets  (Data Contract row 30, era-4 J-03) — every registered dataset,
+//     fetched on mount to populate the Comparison section's dataset selector.
+//   * POST /research/backtests + GET /research/backtests/{id}  (Data Contract row 31, era-4 J-03)
+//     — the Comparison section's "Run comparison" starts TWO backtests (`v1` + `structure_tape`,
+//     both `profile=default`) on the chosen dataset and polls both to a terminal status, reusing
+//     the Studies job/poll PATTERN (not its endpoint). Every aggregate, per-class value, and the
 //     register line is read verbatim from the terminal payload — zero recomputation.
-//   * GET /research/pnl/ledger  (Data Contract row 32, J-03) — read ONLY for the founding baseline
-//     row (`rows.find(r => r.founding)`) shown beside the comparison; the champion badge reuses the
-//     ALREADY-fetched `/research/strategies` champion (no second champion fetch).
+//   * GET /research/pnl/ledger  (Data Contract row 32, era-4 J-03) — read ONLY for the founding
+//     baseline row (`rows.find(r => r.founding)`) shown beside the comparison; the champion badge
+//     reuses the ALREADY-fetched `/research/strategies` champion (no second champion fetch).
+//   * GET /research/tradability?symbol=&as_of=  (era-5B J-01, THIS iteration) — the tradable
+//     level map (bands: range, side, quality score, inherited class, member count, round-number
+//     flag, `basis_as_of`), driven by the SAME Load form as the raw-levels read above. Every band
+//     field is `String(...)`-rendered verbatim — never recomputed, clustered, or re-scored here.
+//   * GET /research/setups (optionally `?symbol=&reaction=`) + GET /research/setups/{id}  (era-5B
+//     J-02/J-03, THIS iteration) — the case-study registry, fetched once on mount and filtered
+//     client-side (the SAME `bar_series.filter` display-filter precedent above — never a second
+//     computation); a row click fetches the drill-in, whose `tape_timeline` is present-but-empty
+//     until a recorded dataset covers the touch.
+//   * GET /research/edge-report  (era-5B J-04, THIS iteration) — the 3-way strategy-comparison
+//     report, fetched once on mount and rendered verbatim, including the honest empty /
+//     all-`insufficient_sample` shape on the keyless PG-only-dataset fixture.
 //
-// The fetch control (J-05) has its own distinct honest states — see `fetch-yahoo-*` testids: idle
-// (fields unset, button disabled), fetching (button disabled, "Fetching…" label), success (folds
-// into the Levels & Zones states below via `handleLoad`), and a POST error surfaced VERBATIM via
-// `UnavailablePanel` (distinct backend `detail` text per 422/503/504/409 — never one generic
+// The fetch control (era-5 J-05) has its own distinct honest states — see `fetch-yahoo-*`
+// testids: idle (fields unset, button disabled), fetching (button disabled, "Fetching…" label),
+// success (folds into the Load states below via `handleLoad`), and a POST error surfaced VERBATIM
+// via `UnavailablePanel` (distinct backend `detail` text per 422/503/504/409 — never one generic
 // message). The provenance badge is absent whenever no series is charted (honest absence, the SAME
 // rule `FeedBasisBadge` already enforces for the cockpit).
 //
-// Four distinct honest states for the Levels & Zones section (never share copy, never fabricate a
-// chart/level/zone):
+// The Tradable Map section (era-5B J-01, THIS iteration's new default view) has its own distinct
+// honest states — see `tradable-map-*` testids — mirroring the raw-levels section's own four-state
+// shape: idle, loading, `no_bar_series_for_symbol` (needs provider credentials), a resolved basis
+// with zero bands is not a reachable state per `tradability.py`'s own docstring so no such empty
+// copy exists, an UNRESOLVED basis (`basis_as_of: null`, `bands: []` — "nothing derivable yet"),
+// and backend-unreachable/any non-200 (folded into the shared degraded state, the SAME
+// validation-refusal-folding precedent immediately below).
+//
+// Four distinct honest states for the raw-levels section (toggle-gated, off by default; never
+// share copy, never fabricate a chart/level/zone):
 //   1. no_bar_series_for_symbol: true            -> explicit "needs provider credentials" state
 //   2. no_bar_series_for_symbol: false, levels: []  -> distinct "no levels found" state
 //   3. levels non-empty, confluence_zones: []     -> distinct "no qualifying confluence zone"
@@ -101,16 +144,31 @@ import { FeedBasisBadge } from "@/components/FeedBasisBadge";
 //      verbatim — folding a validation refusal into the same honest "couldn't load" treatment
 //      satisfies the "never crash, never fabricate" bar without inventing a fifth copy.
 //
-// The Registry section (J-02) has its own distinct honest states — loading, registry-unavailable
-// (`/research/strategies` unreachable/non-200), and populated — see `structure-registry-*` testids.
+// The Registry section (era-4 J-02) has its own distinct honest states — loading,
+// registry-unavailable (`/research/strategies` unreachable/non-200), and populated — see
+// `structure-registry-*` testids.
+//
+// The Comparison section (era-4 J-03) has several distinct honest states — see `comparison-*`
+// testids: no datasets registered, the dataset list unreachable, idle (a dataset list is
+// populated but Run has not been clicked), a backtest queued/running (per side, independently), a
+// backtest failed (per side), a backtest cancelled (per side, carrying NO result — never a
+// partial simulated PnL), a poll-time backend-unreachable notice, and done (aggregates + per-class
+// table, `insufficient_sample` shown inline — never a separate "insufficient" state). The section
+// NEVER moves the champion pointer and writes NOTHING to the PnL ledger.
 //
-// The Comparison section (J-03) has several distinct honest states — see `comparison-*` testids:
-// no datasets registered, the dataset list unreachable, idle (a dataset list is populated but Run
-// has not been clicked), a backtest queued/running (per side, independently), a backtest failed
-// (per side), a backtest cancelled (per side, carrying NO result — never a partial simulated PnL),
-// a poll-time backend-unreachable notice, and done (aggregates + per-class table,
-// `insufficient_sample` shown inline — never a separate "insufficient" state). The section NEVER
-// moves the champion pointer and writes NOTHING to the PnL ledger.
+// The Case Studies section (era-5B J-02/J-03, THIS iteration) has its own distinct honest states —
+// see `case-studies-*` testids: loading, unavailable, a true-empty registry (zero events scanned
+// anywhere), a filtered-to-zero result (distinct from true-empty — the registry has rows, this
+// filter combination simply matches none), and populated. The drill-in (`case-drillin-*` testids)
+// adds its own loading/unavailable states plus two more: a recency-boundary disclosure
+// (`reaction_boundary_truncated: true` — never presented as a full-horizon reaction) and an
+// honest "no recorded tape" state (`tape_timeline: []`, distinct from a populated timeline list).
+//
+// The Edge Report section (era-5B J-04, THIS iteration) has its own distinct honest states — see
+// `edge-report-*` testids: loading, unavailable, and an honest empty/all-`insufficient_sample`
+// report (a valid, first-class, never-hidden outcome per goal.md's own "no gate bending for a
+// headline" anti-goal) versus a populated report — `insufficient_sample` renders INLINE on each
+// cell's real numbers, the SAME `BacktestClassTable` precedent the Comparison section established.
 //
 // Dark instrument-panel style consistent with /journal, /studies, /performance: slate surfaces,
 // restrained borders, font-mono numerics, amber for the honest-empty/degraded states.
@@ -176,6 +234,14 @@ function pickRepresentativeSeries(seriesForSymbol: BarSeriesRecord[]): BarSeries
 // checks remain the sole enforcement (an out-of-set value still 422s server-side either way).
 const YAHOO_TIMEFRAMES = ["1w", "1d", "4h", "1h", "5m", "1m"];
 
+// era-5B J-05 (THIS iteration): the Case Studies reaction filter's <select> options — mirrors
+// `research/setups.py`'s own config-owned, pre-registered `REJECTED`/`BROKE`/`CHOPPED` constants
+// (route-level enforced by `routes.py`'s `_VALID_REACTIONS`). The SAME `YAHOO_TIMEFRAMES` display-
+// choice precedent immediately above: a courtesy option list, never a second validation authority
+// — an out-of-set value would still 422 server-side (this page never sends one; the filter is
+// applied client-side over the already-served, unfiltered event list — see `handleSetupsFilter*`).
+const SETUP_REACTIONS = ["rejected", "broke", "chopped"];
+
 type LoadState<T> =
   | { phase: "idle" }
   | { phase: "loading" }
@@ -288,6 +354,439 @@ function ZoneRow({ zone, index }: { zone: ConfluenceZone; index: number }) {
   );
 }
 
+// --- Tradable Map section (era-5B J-01, THIS iteration's new default view) ----------------------
+
+// One tradable band row: side, range, inherited class, quality score, member count, round-number
+// flag — every value `String(...)`-rendered verbatim off the prop (the `ZoneRow` precedent).
+// `class: null` renders an honest "Unclassified" label — never a fabricated grade (a band with no
+// overlapping confluence zone genuinely has none; `levels.py` alone owns A/B/C).
+function BandRow({ band }: { band: TradabilityBand }) {
+  return (
+    <tr
+      data-testid="tradable-band-row"
+      data-band-side={band.side}
+      className="border-b border-slate-800/60 last:border-b-0"
+    >
+      <td className={LABEL_CELL}>{band.side}</td>
+      <td className={NUMERIC_CELL} data-testid="tradable-band-range">
+        {String(band.price_low)}–{String(band.price_high)}
+      </td>
+      <td className={LABEL_CELL} data-testid="tradable-band-class">
+        {band.class !== null ? `Class ${band.class}` : "Unclassified"}
+      </td>
+      <td className={NUMERIC_CELL} data-testid="tradable-band-score">
+        {String(band.quality_score)}
+      </td>
+      <td className={NUMERIC_CELL}>{String(band.member_count)}</td>
+      <td className="px-2 py-1.5 text-left">
+        {band.round_number && (
+          <span
+            data-testid="tradable-band-round-number"
+            className="inline-block whitespace-nowrap rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[11px] text-slate-300"
+          >
+            round number
+          </span>
+        )}
+      </td>
+    </tr>
+  );
+}
+
+// The bands table (range/side/quality-score/class/member-count/round-number — the DoD's exact
+// column list). `bands` is rendered in the endpoint's OWN served order (side, then descending
+// quality score — never re-sorted here).
+function BandsTable({ bands }: { bands: TradabilityBand[] }) {
+  return (
+    <div className="overflow-x-auto">
+      <table data-testid="tradable-map-table" className="w-full border-collapse">
+        <thead>
+          <tr className="border-b border-slate-800">
+            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">side</th>
+            <th className={HEADER_CELL}>range</th>
+            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">class</th>
+            <th className={HEADER_CELL}>score</th>
+            <th className={HEADER_CELL}>members</th>
+            <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500" />
+          </tr>
+        </thead>
+        <tbody>
+          {bands.map((band, i) => (
+            <BandRow key={i} band={band} />
+          ))}
+        </tbody>
+      </table>
+    </div>
+  );
+}
+
+// --- Case Studies section (era-5B J-02/J-03, THIS iteration) -------------------------------------
+
+// Every configured forward-return horizon rendered verbatim (horizon_bars + the RAW
+// return_fraction — never a client-side percentage conversion or rounding). `return_fraction:
+// null` renders an honest "—" (that horizon reaches past the end of the stored series; never a
+// fabricated number).
+function ForwardReturnsList({ forwardReturns }: { forwardReturns: SetupEvent["forward_returns"] }) {
+  return (
+    <span data-testid="case-forward-returns" className="font-mono text-xs text-slate-300">
+      {forwardReturns.map((fr, i) => (
+        <span key={fr.horizon_bars} className="whitespace-nowrap">
+          {i > 0 && " · "}
+          {String(fr.horizon_bars)}b: {fr.return_fraction === null ? "—" : String(fr.return_fraction)}
+        </span>
+      ))}
+    </span>
+  );
+}
+
+// One case-registry row: symbol, session date, band range/side/class, reaction, forward returns —
+// the DoD's exact column list. Clicking anywhere on the row opens the drill-in below the table.
+function SetupRow({
+  event,
+  selected,
+  onSelect,
+}: {
+  event: SetupEvent;
+  selected: boolean;
+  onSelect: () => void;
+}) {
+  return (
+    <tr
+      data-testid="case-studies-row"
+      data-reaction={event.reaction}
+      onClick={onSelect}
+      aria-selected={selected}
+      className={`cursor-pointer border-b border-slate-800/60 last:border-b-0 hover:bg-slate-800/40 ${
+        selected ? "bg-slate-800/60" : ""
+      }`}
+    >
+      <td className={LABEL_CELL}>{event.symbol}</td>
+      <td className={LABEL_CELL}>{event.session_date}</td>
+      <td className={LABEL_CELL}>
+        {event.band.side} · {String(event.band.price_low)}–{String(event.band.price_high)} ·{" "}
+        {event.band.class !== null ? `Class ${event.band.class}` : "Unclassified"}
+      </td>
+      <td className={LABEL_CELL} data-testid="case-studies-row-reaction">
+        {event.reaction}
+        {event.reaction_boundary_truncated && (
+          <span
+            data-testid="case-studies-row-boundary-flag"
+            className="ml-1 inline-block whitespace-nowrap rounded border border-amber-800/60 bg-amber-900/20 px-1 py-0.5 text-[10px] text-amber-300"
+          >
+            truncated horizon
+          </span>
+        )}
+      </td>
+      <td className="px-2 py-1.5 text-left">
+        <ForwardReturnsList forwardReturns={event.forward_returns} />
+      </td>
+    </tr>
+  );
+}
+
+// The tape-at-the-wall timeline (era-5B J-03) — a list of state-transition entries, or an honest
+// "no recorded tape" empty state (distinct from a populated list — never silently omitted).
+function TapeTimelineList({ timeline }: { timeline: SetupEvent["tape_timeline"] }) {
+  if (timeline.length === 0) {
+    return (
+      <p data-testid="case-drillin-tape-timeline-empty" className="text-xs text-slate-600">
+        No recorded tape for this event.
+      </p>
+    );
+  }
+  return (
+    <ol data-testid="case-drillin-tape-timeline" className="space-y-1">
+      {timeline.map((entry, i) => (
+        <li
+          key={i}
+          data-testid="case-drillin-tape-timeline-entry"
+          className="flex items-baseline justify-between gap-2 font-mono text-xs text-slate-300"
+        >
+          <span className="text-slate-500">{entry.timestamp ?? "—"}</span>
+          <span>{entry.state}</span>
+          <span className="text-slate-500">{String(entry.confidence)}</span>
+        </li>
+      ))}
+    </ol>
+  );
+}
+
+// The row drill-in: band, reaction (+ the honest recency-boundary disclosure), forward returns,
+// and the tape timeline. Renders whichever `LoadState<SetupEvent>` phase is current — its own
+// distinct loading/unavailable states, the page's established `LoadState<T>` pattern.
+function SetupDrillIn({ state }: { state: LoadState<SetupEvent> }) {
+  return (
+    <Panel title="Case Studies — drill-in" className="mt-3">
+      {state.phase === "loading" && <LoadingPanel testid="case-drillin-loading" />}
+      {state.phase === "error" && (
... [diff_bound] apps/frontend/app/structure/page.tsx: 917 more diff lines omitted — Read the file for full detail
diff --git a/apps/frontend/components/StructureChart.tsx b/apps/frontend/components/StructureChart.tsx
index 6d1e316..594c507 100644
--- a/apps/frontend/components/StructureChart.tsx
+++ b/apps/frontend/components/StructureChart.tsx
@@ -1,7 +1,7 @@
 "use client";
 
 import { useEffect, useRef } from "react";
-import type { BarRow, SrLevel } from "@/lib/types";
+import type { BarRow, SrLevel, TradabilityBand } from "@/lib/types";
 import { EmptyHint } from "./Panel";
 
 // The /structure page's price chart (J-01): candles from ONE representative recorded bar series
@@ -15,7 +15,20 @@ import { EmptyHint } from "./Panel";
 // PriceChart.tsx polls the tape engine's `/tape/{ticker}/history` (logical-second candles + live
 // tape-state markers); this component renders ONE already-fetched query result from
 // `/research/bars` (real UTC-epoch-seconds candles, no polling, no markers).
-export function StructureChart({ bars, levels }: { bars: BarRow[]; levels: SrLevel[] }) {
+//
+// era-5B J-05 (additive): an optional `bands` prop overlays the tradable map's price bands
+// (GET /research/tradability, read verbatim by the page) beside the existing level lines. Default
+// `[]` means every EXISTING caller (the raw-levels toggle's "on" render) draws byte-identically to
+// before this iteration — this is a pure additive prop, never a rewrite of the level-line path.
+export function StructureChart({
+  bars,
+  levels,
+  bands = [],
+}: {
+  bars: BarRow[];
+  levels: SrLevel[];
+  bands?: TradabilityBand[];
+}) {
   const containerRef = useRef<HTMLDivElement | null>(null);
 
   useEffect(() => {
@@ -81,6 +94,31 @@ export function StructureChart({ bars, levels }: { bars: BarRow[]; levels: SrLev
         });
       }
 
+      // era-5B J-05: one SOLID price line per tradable-band edge (visually distinct from the
+      // dashed raw-level lines above), colored by side — the SAME up/down palette the candle
+      // series itself uses, so resistance/support read as one visual family with the candles.
+      // price_low/price_high/side/class/quality_score/round_number are read verbatim off the
+      // prop; this component performs no scoring or clustering of its own. A single-price band
+      // (price_low === price_high) draws one line, never a duplicate.
+      for (const band of bands) {
+        const color = band.side === "resistance" ? "#fb7185" : "#34d399"; // rose-400 / emerald-400
+        const sideLabel = band.side === "resistance" ? "R" : "S";
+        const classLabel = band.class ? ` class ${band.class}` : "";
+        const title = `${sideLabel}${classLabel} · score ${band.quality_score}${band.round_number ? " · round" : ""}`;
+        const edges =
+          band.price_low === band.price_high ? [band.price_low] : [band.price_low, band.price_high];
+        for (const price of edges) {
+          series.createPriceLine({
+            price,
+            color,
+            lineWidth: 2,
+            lineStyle: 0, // LineStyle.Solid — distinct from the dashed raw-level lines
+            axisLabelVisible: true,
+            title,
+          });
+        }
+      }
+
       if (candles.length > 0) chart.timeScale().fitContent();
     })();
 
@@ -88,7 +126,7 @@ export function StructureChart({ bars, levels }: { bars: BarRow[]; levels: SrLev
       disposed = true;
       if (chart) chart.remove();
     };
-  }, [bars, levels]);
+  }, [bars, levels, bands]);
 
   const hasBars = bars.length > 0;
 
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 72820fc..2d9b082 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -10,6 +10,7 @@ import type {
   CreateStudyResult,
   DatasetsListResult,
   DeclareResult,
+  EdgeReportResponse,
   Hint,
   JournalDetail,
   JournalFilters,
@@ -20,12 +21,15 @@ import type {
   ProfilesPayload,
   RecordBarSeriesResult,
   ResearchTaxonomy,
+  SetupDetailResult,
+  SetupsListResult,
   StrategiesPayload,
   Study,
   SymbolMatch,
   TapeHistory,
   TapeSnapshot,
   ThesisProjection,
+  TradabilityResponse,
   WatchParams,
 } from "./types";
 
@@ -1038,3 +1042,124 @@ export async function fetchBacktest(backtestId: string): Promise<Backtest | null
     return null;
   }
 }
+
+// --- Era-5B: tradable map, case-study setups, and the 3-way edge report (capabilities 1/2/6,
+// J-01/J-02/J-04), wired to the browser this iteration (J-05) at /structure's three new sections.
+// All four functions follow `fetchLevels`/`fetchStrategies` immediately above byte-for-byte: the
+// `{ok, data, error}` shape, the backend's own `detail` surfaced verbatim on a non-200 (folding a
+// validation refusal — e.g. a malformed `as_of` 422 — into the SAME degraded-state treatment as an
+// unreachable backend), and `data: null` on any failure so the caller never shows a stale or
+// fabricated view in its place.
+
+// GET /research/tradability?symbol=&as_of= — the tradable level map, served VERBATIM. Mirrors
+// `fetchLevels` exactly (same required params, same 422/unreachable folding).
+export async function fetchTradability(
+  symbol: string,
+  asOf: string,
+): Promise<{ ok: boolean; data: TradabilityResponse | null; error?: string; status?: number }> {
+  try {
+    const res = await fetch(
+      `${API_BASE}/research/tradability?symbol=${encodeURIComponent(symbol)}&as_of=${encodeURIComponent(asOf)}`,
+    );
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as TradabilityResponse, status: res.status };
+    }
+    let error = "The tradable map could not be loaded.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, data: null, error, status: res.status };
+  } catch {
+    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// GET /research/setups (optionally filtered by symbol/reaction/band_class — server-side,
+// AND-combined; an unknown enum `reaction`/`band_class` is a backend 422) — the touch-event
+// case-study registry, served VERBATIM. `filters` mirrors `fetchJournal`'s optional-filter-params
+// pattern; an omitted filter is left off the query string entirely (never sent as an empty param).
+export async function fetchSetups(filters?: {
+  symbol?: string;
+  reaction?: string;
+  band_class?: string;
+}): Promise<{ ok: boolean; data: SetupsListResult | null; error?: string }> {
+  const params = new URLSearchParams();
+  if (filters?.symbol) params.set("symbol", filters.symbol);
+  if (filters?.reaction) params.set("reaction", filters.reaction);
+  if (filters?.band_class) params.set("band_class", filters.band_class);
+  const qs = params.toString();
+  try {
+    const res = await fetch(`${API_BASE}/research/setups${qs ? `?${qs}` : ""}`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as SetupsListResult };
+    }
+    let error = "The case-study registry could not be loaded.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, data: null, error };
+  } catch {
+    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// GET /research/setups/{id} — one event's drill-in (band, reaction, forward returns, and the J-03
+// `tape_timeline` — present-but-empty when no recorded dataset covers the touch), served VERBATIM.
+// A 404 (unknown id) folds into the same `ok:false` degraded result as any other failure — the
+// backend's own `detail` ("no setup event with id '…'") is surfaced verbatim, so the caller never
+// needs a separate not-found branch (mirrors `fetchLevels`'s "fold validation refusals into the
+// shared degraded state" precedent, applied to a 404 instead of a 422).
+export async function fetchSetupDetail(
+  id: string,
+): Promise<{ ok: boolean; data: SetupDetailResult | null; error?: string; status?: number }> {
+  try {
+    const res = await fetch(`${API_BASE}/research/setups/${encodeURIComponent(id)}`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as SetupDetailResult, status: res.status };
+    }
+    let error = "The case-study event could not be loaded.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, data: null, error, status: res.status };
+  } catch {
+    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// GET /research/edge-report — the 3-way strategy-comparison report (`v1` / `structure_tape` /
+// `structure_tape_map`), served VERBATIM. Mirrors `fetchDatasets`/`fetchBarSeriesList` (a LIST-
+// shaped endpoint with no query params). An all-empty or all-`insufficient_sample` report is a
+// valid `ok:true` result — the caller renders it as an honest first-class state, never as a
+// failure; `data: null` is reserved for a genuine non-200 / unreachable backend.
+export async function fetchEdgeReport(): Promise<{
+  ok: boolean;
+  data: EdgeReportResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/edge-report`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as EdgeReportResponse };
+    }
+    let error = "The edge report could not be loaded.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, data: null, error };
+  } catch {
+    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
+  }
+}
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 0e08f23..b1faf36 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1191,3 +1191,154 @@ export interface CreateBacktestParams {
   strategy_id: string;
   profile: string;
 }
+
+// --- Era-5B: the tradable level map (capability 1, J-01), surfaced this iteration (J-05) at
+// /structure's new default Tradable Map view. Every field below is read VERBATIM from
+// GET /research/tradability (app/research/tradability.py's `compute_tradability` — a LENS over
+// the frozen `compute_levels` output, never a second levels engine) — the page recomputes no
+// price, class, or score.
+
+// One tradable band (GET /research/tradability's `bands[]`). `class` is a PROJECTION of the
+// band's best overlapping confluence zone (owned by levels.py) — `null` is an honest "no
+// overlapping zone", never a fabricated/defaulted grade. `members` reuses the EXISTING
+// `SrLevel`-shaped entry byte-for-byte (the backend's own band member IS a levels.py level dict).
+export interface TradabilityBand {
+  side: "support" | "resistance";
+  price_low: number;
+  price_high: number;
+  class: "A" | "B" | "C" | null;
+  quality_score: number;
+  round_number: boolean;
+  member_count: number;
+  members: SrLevel[];
+}
+
+// GET /research/tradability?symbol=&as_of= — the full served projection, read VERBATIM. Two
+// fields together carry the SAME three honest, distinct states `LevelsResponse` already
+// established: `no_bar_series_for_symbol: true` (no recorded series at all) vs. `false` with an
+// empty `bands` + `basis_as_of: null` (series exist, no basis derivable at `as_of`) vs. a
+// resolved `basis_as_of` with non-empty `bands` (once a basis resolves, at least one band always
+// exists — the module's own docstring: a resolved basis with zero bands is not a reachable state).
+export interface TradabilityResponse {
+  symbol: string;
+  as_of: string;
+  bands: TradabilityBand[];
+  no_bar_series_for_symbol: boolean;
+  basis_as_of: string | null;
+}
+
+// --- Era-5B: the touch-event scanner + case-study registry (capability 2, J-02) + the
+// tape-at-the-wall join (capability 4, J-03), surfaced this iteration (J-05) at /structure's new
+// Case Studies section. Every field is read VERBATIM from GET /research/setups /
+// GET /research/setups/{id} (app/research/setups.py's `compute_setups` /
+// `enrich_with_tape_timeline`) — the page recomputes no reaction, forward return, or tape state.
+
+// One forward-return reading at a config-owned horizon. `return_fraction` is honestly `null` when
+// that horizon reaches past the end of the stored series — never a fabricated number.
+export interface SetupForwardReturn {
+  horizon_bars: number;
+  return_fraction: number | null;
+}
+
+// One meaningful tape-state-transition entry in an event's `tape_timeline` (J-03's tape-at-the-
+// wall join). `timestamp` is honestly `null` only when the joined dataset carries no
+// `epoch_anchor` (the identical `epoch_anchor + logical_ts` reconstruction the chart already
+// uses) — state/confidence are the FROZEN engine's own classifier values, reused verbatim.
+export interface SetupTapeTimelineEntry {
+  timestamp: string | null;
+  state: string;
+  confidence: number;
+}
+
+// The three config-owned, pre-registered reaction labels (`setups.py`'s own `REJECTED` / `BROKE`
+// / `CHOPPED` constants, mirrored — never re-derived). Kept as `string` (not a narrowed literal
+// union) on the served event below, the SAME `SrLevel.type` tolerance already established on this
+// page: an unrecognized future value still renders rather than silently vanishing at a guard.
+export type SetupReaction = "rejected" | "broke" | "chopped";
+
+// One band-touch event (GET /research/setups' `events[]`, and GET /research/setups/{id}'s
+// `event`). `tape_timeline` is present-but-empty until a recorded dataset's window covers the
+// touch (J-03) — an honest absence, never fabricated. `effective_reaction_horizon_bars` /
+// `reaction_boundary_truncated` are the iter-5 B1 additive recency-boundary disclosure: a touch
+// inside the store's most-recent session may have its `reaction` read from a TRUNCATED
+// sub-horizon (the store simply has not accumulated `horizons[0]` bars past it yet) — disclosed
+// here, never silently presented as a full-horizon reaction.
+export interface SetupEvent {
+  id: string;
+  symbol: string;
+  session_date: string;
+  band: TradabilityBand;
+  touch_ts: string;
+  touch_open: number;
+  touch_high: number;
+  touch_low: number;
+  touch_close: number;
+  touch_volume: number;
+  reaction: SetupReaction;
+  forward_returns: SetupForwardReturn[];
+  effective_reaction_horizon_bars: number;
+  reaction_boundary_truncated: boolean;
+  tape_timeline: SetupTapeTimelineEntry[];
+}
+
+// GET /research/setups (optionally filtered by symbol/reaction/band_class — server-side,
+// AND-combined) — read VERBATIM. An empty list is an honest "nothing scanned/touched yet", never
+// an error.
+export interface SetupsListResult {
+  events: SetupEvent[];
+}
+
+// GET /research/setups/{id} — the SAME event shape as a list row, plus the J-03 tape join applied
+// (list rows never carry a non-empty `tape_timeline`; only this detail read does).
+export interface SetupDetailResult {
+  event: SetupEvent;
+}
+
+// --- Era-5B: the 3-way strategy-comparison edge report (capability 6, J-04), surfaced this
+// iteration (J-05) at /structure's new Edge Report section. Every field is read VERBATIM from
+// GET /research/edge-report (app/research/edge_report.py's `run_strategy_comparison_report`) —
+// the page recomputes no R, $, win-rate, or class/side/reaction partition. `measurement` /
+// `null_baseline` reuse the EXISTING `BacktestAggregate` shape byte-for-byte (both are built by
+// the SAME `_aggregate()` the Comparison section's own backtest results already render).
+
+// One strategy x class x side x reaction x feed cell (never pooled across feeds — the
+// never-pool-across-feeds anti-goal). `dataset_ids` are the recorded windows this cell pooled
+// trades from (sorted); `insufficient_sample` gates DISPLAY only — the real measurement is always
+// shown alongside it (the `BacktestClassTable` precedent: never a separate hidden state).
+export interface EdgeReportCell {
+  strategy_id: string;
+  band_class: "A" | "B" | "C";
+  band_side: "support" | "resistance";
+  reaction: SetupReaction;
+  feed: string;
+  dataset_ids: string[];
+  measurement: BacktestAggregate;
+  null_baseline: BacktestAggregate;
+  insufficient_sample: boolean;
+}
+
+// One ranked, informational TRAIN cell that clears the positivity gate, paired with its own
+// matching hold-out cell's status. `holdout_cell` is honestly `null` when no hold-out data exists
+// yet for that exact (strategy, class, side, reaction, feed) key — never a fabricated verdict.
+// This list promotes nothing (the champion pointer is untouched by this report — see
+// edge_report.py's own module docstring); it is purely informational ranking.
+export interface EdgeReportSurvivingCell {
+  train_cell: EdgeReportCell;
+  holdout_cell: EdgeReportCell | null;
+  holdout_positive_edge: boolean;
+}
+
+// GET /research/edge-report — the full served projection, read VERBATIM. `register` is the
+// backend's ONE simulated-PnL disclosure string (the page renders THIS string, never a frontend
+// copy — mirrors `PnlLedger.register` / `BacktestResult.register`). An all-empty
+// (`train.cells: []` and `holdout.cells: []`) or all-`insufficient_sample` report is a valid,
+// honest outcome — never hidden, never a fabricated survivor. No `champion` key exists on this
+// report (it is never about a single champion pointer — unlike the era-3 champion-only CLI
+// report this module also computes).
+export interface EdgeReportResponse {
+  register: string;
+  pnl_min_sample_size: number;
+  train: { cells: EdgeReportCell[] };
+  holdout: { cells: EdgeReportCell[] };
+  surviving_train_cells: EdgeReportSurvivingCell[];
+}
```
