# Iteration diff (bounded)

Files changed: 8. Shown in full: 8.

```diff
diff --git a/README.md b/README.md
index 2082d13..2610c11 100644
--- a/README.md
+++ b/README.md
@@ -84,9 +84,10 @@ Current capabilities:
 - **A third registered strategy, `structure_tape_map` (research API)** — the app now has three registered ways of simulating trades against historical data: the original `v1`, the frozen `structure_tape` (which trades off the raw list of thousands of individual price levels), and this new one, which trades off the same small handful of tradable bands the level map produces instead. It reuses the exact same class-scaled stop/target/position-sizing rules as `structure_tape` — only which levels it watches differs. Registering it changes nothing about `v1`, `structure_tape`, or their past results. It appears as its own card in the Structure page's strategy Registry section and is exercised automatically as part of the 3-way edge report below (now also visible on the Structure page); it is runnable through the existing backtest API, but there is no button yet to pick it directly for a standalone ad hoc backtest in the browser.
 - **The 3-way profit edge report (research API)** — a new endpoint runs `v1`, `structure_tape`, and `structure_tape_map` over every recorded practice-tape window and reports, honestly, how each one actually did — broken down by price-level quality (A/B/C), which side of the market it traded (support or resistance), how price reacted at the touch (rejected, broke, or chopped), and which data feed the window came from. Every dollar figure carries its sample size, a comparison against a random-entry baseline, and the same "simulated — not indicative of live results" register used everywhere else in the app. Real recorded trading windows now exist across a broad slice of the panel, giving the report real touches to measure instead of only the small practice dataset; any cell still short of enough trades honestly labels itself "insufficient sample" rather than manufacturing a result, and an entirely empty report remains a valid, honest outcome whenever nothing yet clears the bar. Computing the full report over the currently recorded data is slow and can take a long time to finish on a first run, showing a loading state throughout rather than a fabricated interim result. The same comparison is available to AI tools through the machine-readable connection, byte-for-byte identical to what a person sees calling the endpoint directly. This report is now visible on the Structure page in the browser as the Edge Report, and remains reachable through the research API and the matching machine-readable tool.
 - **Edge report caching and a permanent record of its findings (research API)** — once the 3-way profit edge report's full computation over recorded data has completed a single time, the result is now remembered in a durable, disk-backed cache and served back within an interactive few seconds on every later request — through the REST API, the machine-readable connection, and the Structure page's Edge Report panel alike — including after a full backend restart. Nothing about what the report measures, how it is computed, or the shape of its response changes; any change to the underlying recorded datasets, registered strategies, or configuration automatically invalidates the cached answer, so the next request recomputes it byte-identically rather than serving something stale. A finished report's findings can also now be permanently appended, as a deliberate one-time step, to the same append-only profit-and-loss record described above — its own dedicated entry, with every data feed and the train/hold-out split kept fully separate from every entry recorded before it. As of today the very first full computation over the currently recorded real data, and its permanent recording, have not yet been run — see the next capability for exactly what the Edge Report panel honestly shows in the meantime.
-- **Safe-by-default Edge Report** — opening the Structure page's Edge Report section, or asking the underlying research endpoint for the report directly, never risks silently starting that full computation as a side effect of simply loading a page — before this update, doing so could pin the backend near 100% CPU for hours with no warning shown anywhere. If a report has already been computed, it — or the honest "No edge-report cells yet." empty state — is shown exactly as before. If nothing has been computed yet, the panel instead shows a plain, prompt "Edge report not computed yet." message with a short explanation of why, answering promptly rather than spinning indefinitely or silently starting work in the background. There is no button or control anywhere in the app yet for actually starting that computation — an operator-triggered "compute now" action is planned for an upcoming update.
+- **Safe-by-default Edge Report** — opening the Structure page's Edge Report section, or asking the underlying research endpoint for the report directly, never risks silently starting that full computation as a side effect of simply loading a page — before this update, doing so could pin the backend near 100% CPU for hours with no warning shown anywhere. If a report has already been computed, it — or the honest "No edge-report cells yet." empty state — is shown exactly as before. If nothing has been computed yet, the panel instead shows a plain, prompt "Edge report not computed yet." message with a short explanation of why, answering promptly rather than spinning indefinitely or silently starting work in the background. Starting that computation is now a separate, explicit action — see the next capability.
+- **Operator-run edge report compute** — beneath the "Edge report not computed yet." message, a "Compute edge report" button starts the full three-strategy comparison as a background job without leaving the page. While it runs, a live counter shows how many of the comparison's individual backtests have finished so far, updating automatically with no manual refresh needed. When the computation completes, the finished report renders in place automatically, using the same table already shown for a previously-computed report. If the computation fails partway through, the panel shows the specific error message instead of a generic failure, and the button relabels itself so a fresh attempt is one more click away. Reloading the page, or landing on it, while a compute is running, or after one has already finished or failed, immediately shows the matching state rather than resetting to idle. The same computation can also be started, unattended, from the command line for long background runs.
 - **Cockpit price-chart tradable bands and a descriptive confluence chip** — the tradable support/resistance bands from the Structure page's map now also draw directly on the live cockpit price chart while watching a symbol in Simulated or Historical mode: one or two solid price lines per band (rose for resistance, emerald for support), each labeled with side, class, quality score, and whether it sits on a round number — alongside the existing tape-state markers and any declared-thesis lines, without changing how those render. A small descriptive banner appears beneath the chart only when the last traded price sits inside one of those bands AND the live tape reading matches that band's configured rejection-or-breakthrough state — for example "Inside R-band 300.05–300.17 (class A) · tape: Ask Absorption (rejection) · measured history: edge report." The banner states the current condition and points to the edge report as measured history; it never tells you to buy or sell and never predicts an outcome. A simulated ticker with no real recorded price history shows an honest "No tradable map for TICKER" note instead of a fabricated band. Live mode is unchanged — the price chart, and therefore the bands and banner, stay hidden there exactly as before.
-- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `GET /meta/ui-routes`.
+- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `POST /research/edge-report/compute`, `GET /research/edge-report/compute`, `POST /research/edge-report/compute/cancel`, `GET /meta/ui-routes`.
 - **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, journal, studies, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, profit edge reports, and navigation data a person sees. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 <!-- /AUTO:capabilities -->
 
diff --git a/apps/backend/app/research/edge_report.py b/apps/backend/app/research/edge_report.py
index c532175..133ee1b 100644
--- a/apps/backend/app/research/edge_report.py
+++ b/apps/backend/app/research/edge_report.py
@@ -53,7 +53,11 @@ from __future__ import annotations
 
 import argparse
 import json
+import multiprocessing
+import os
 import sys
+import tempfile
+from concurrent.futures import ProcessPoolExecutor, as_completed
 from pathlib import Path
 
 from ..config import (
@@ -72,8 +76,15 @@ from .bars import BarStore
 # second R/$/edge formula.
 from .backtests import BacktestJobManager, REGISTER, STATUS_DONE, _aggregate
 from .datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN, parse_utc_epoch
-from .edge_report_cache import EdgeReportCache
-from .setups import compute_setups
+# era-fast_wall J-05: ``pair_cache_key``/``EdgeReportBacktestCache`` for the per-pair sub-cache;
+# ``_config_content_hash`` reused VERBATIM from ``edge_report_cache.py`` (never re-derived a
+# second time -- see ``edge_report_backtest_cache.py``'s own module docstring for the full "why").
+from .edge_report_backtest_cache import EdgeReportBacktestCache, pair_cache_key
+from .edge_report_cache import EdgeReportCache, _config_content_hash
+# ``_store_signature`` imported PRIVATE (the identical ``_aggregate`` precedent above, and the
+# phase plan's own explicit suggestion): the ONE bar-store-signature tuple shape ``setups.py``
+# already computes for its OWN scan cache, reused verbatim here rather than duplicated.
+from .setups import _store_signature, compute_setups
 from .store import JournalStore
 
 __all__ = [
@@ -394,6 +405,16 @@ class _ProgressReporter:
             "current": {"dataset_id": dataset_id, "strategy_id": strategy_id},
         })
 
+    def note_cache_hit(self) -> None:
+        """era-fast_wall J-05: bumps the running from-cache count WITHOUT emitting a sink patch of
+        its own. Called by the caching ``run_pair`` closure (``_build_caching_run_pair``, below)
+        the INSTANT it serves a sub-cache hit -- strictly BEFORE this pair's own ``pair_done()``
+        (UNCHANGED) fires. ``pair_done()``'s EXISTING patch already reads ``self._from_cache``, so
+        this single additive method is enough to make ``backtests_from_cache`` genuinely increment
+        without widening ``run_pair``'s own 2-arg-in/1-dict-out shape (the NOTES' own
+        implementation hint)."""
+        self._from_cache += 1
+
     def pair_done(self) -> None:
         self._done += 1
         self._sink({
@@ -413,6 +434,7 @@ def _split_cells(
     *,
     reporter: "_ProgressReporter | None" = None,
     should_abort=None,
+    run_pair=None,
 ) -> list[dict]:
     """One split's (train or hold-out) cells: for every dataset that resolves an owning event with
     a genuinely inherited class (an unclassified ``class: null`` band is honestly excluded — there
@@ -427,12 +449,21 @@ def _split_cells(
     numbers cannot recover that without the raw, correctly-ordered trade list).
 
     era-fast_wall J-04: ``reporter``/``should_abort`` (both optional, default ``None`` — the exact
-    pre-J-04 loop when omitted) are the ONLY additions to this loop's body — the pooling/ordering/
+    pre-J-04 loop when omitted) are additions to this loop's body — the pooling/ordering/
     aggregation code below is byte-for-byte untouched. ``should_abort`` (a zero-arg callable) is
-    checked ONCE per pair, strictly BEFORE that pair's ``_run_backtest`` call — cooperative
+    checked ONCE per pair, strictly BEFORE that pair's backtest call — cooperative
     cancellation observed BETWEEN dataset x strategy pairs, never mid-backtest — and raises
     ``EdgeReportComputeCancelled`` the instant it returns ``True``, so an already-completed pair's
-    trades are never discarded and a not-yet-started pair never begins."""
+    trades are never discarded and a not-yet-started pair never begins.
+
+    era-fast_wall J-05: ``run_pair`` (optional, default ``None`` — the EXACT pre-J-05 inline
+    ``_run_backtest`` call when omitted, so this stays BYTE-IDENTICAL to before whenever a caller
+    does not supply one) is a ``(dataset_meta, strategy_id) -> dict`` callable (the SAME return
+    shape ``_run_backtest`` itself returns) built by ``_build_caching_run_pair`` whenever a
+    ``sub_cache`` is threaded in from ``_compute_strategy_comparison_report``. This is the ONLY
+    other change to this loop's body — a cache hit notifies ``reporter`` from INSIDE that closure
+    (see ``_ProgressReporter.note_cache_hit``), so this call site's own ``reporter.pair_done()``
+    below stays textually unchanged."""
     pools: dict[tuple, dict] = {}
     for dataset_meta in datasets:
         event = _dataset_event(dataset_meta, events)
@@ -444,10 +475,13 @@ def _split_cells(
                 raise EdgeReportComputeCancelled()
             if reporter is not None:
                 reporter.start_pair(dataset_meta["id"], strategy_id)
-            result = _run_backtest(
-                jobs, store, dataset_store, dataset_meta["id"],
-                strategy_id=strategy_id, profile=PROFILE_DEFAULT, bar_store=bar_store,
-            )
+            if run_pair is not None:
+                result = run_pair(dataset_meta, strategy_id)
+            else:
+                result = _run_backtest(
+                    jobs, store, dataset_store, dataset_meta["id"],
+                    strategy_id=strategy_id, profile=PROFILE_DEFAULT, bar_store=bar_store,
+                )
             if reporter is not None:
                 reporter.pair_done()
             key = (strategy_id, event["band"]["class"], event["band"]["side"], event["reaction"], feed)
@@ -481,6 +515,196 @@ def _split_cells(
     return cells
 
 
+# --- era-fast_wall J-05: the resumable sub-cache's run_pair provider + the CLI-only parallel
+# pre-warm. See ``EdgeReportBacktestCache``'s own module docstring for the durable cache's
+# discipline; the functions below are the ONLY code that ever keys/consults it. -----------------
+
+
+def _build_caching_run_pair(
+    jobs: BacktestJobManager,
+    store: JournalStore,
+    dataset_store: DatasetStore,
+    bar_store: BarStore,
+    config: Config,
+    sub_cache: EdgeReportBacktestCache,
+    reporter: "_ProgressReporter | None",
+):
+    """Builds the caching ``run_pair(dataset_meta, strategy_id)`` closure ``_split_cells`` calls in
+    place of its inline ``_run_backtest`` when a ``sub_cache`` is supplied. Every key component
+    that is constant across the WHOLE sweep (``bar_store_signature``, ``config_fingerprint``,
+    ``config_content_hash``, ``strategy_registry``) is computed EXACTLY ONCE here, outside the pair
+    loop, and closed over — never once per pair (the exact wasteful-recomputation pattern this
+    whole interlude exists to remove; the NOTES' own implementation hint). A cache hit notifies
+    ``reporter`` (if any) via ``note_cache_hit()`` BEFORE returning, so the caller's UNCHANGED
+    ``reporter.pair_done()`` call picks up the incremented ``backtests_from_cache`` count — without
+    widening ``run_pair``'s own 2-arg-in/1-dict-out return shape. A cache MISS runs the SAME
+    ``_run_backtest`` every uncached caller uses (single source of truth) and publishes the result
+    — ``EdgeReportBacktestCache.publish`` itself swallows a persistence failure (see its own
+    docstring), so a sub-cache write hiccup never blocks this pair's already-computed result from
+    being returned and pooled normally."""
+    bar_store_signature = _store_signature(bar_store)
+    config_fingerprint = config.config_fingerprint()
+    config_content_hash = _config_content_hash(config)
+    strategy_registry = config.strategy_registry()
+
+    def run_pair(dataset_meta: dict, strategy_id: str) -> dict:
+        key = pair_cache_key(
+            dataset_id=dataset_meta["id"],
+            dataset_checksum=dataset_meta["checksum"],
+            strategy_id=strategy_id,
+            profile=PROFILE_DEFAULT,
+            config_fingerprint=config_fingerprint,
+            config_content_hash=config_content_hash,
+            strategy_registry=strategy_registry,
+            bar_store_signature=bar_store_signature,
+        )
+        cached = sub_cache.lookup(key)
+        if cached is not None:
+            if reporter is not None:
+                reporter.note_cache_hit()
+            return cached
+        result = _run_backtest(
+            jobs, store, dataset_store, dataset_meta["id"],
+            strategy_id=strategy_id, profile=PROFILE_DEFAULT, bar_store=bar_store,
+        )
+        sub_cache.publish(key, result)
+        return result
+
+    return run_pair
+
+
+def _eligible_datasets(dataset_store: DatasetStore, bar_store: BarStore, config: Config) -> list[dict]:
+    """Every registered dataset (both splits, combined) that resolves an owning, classified scan
+    event — the IDENTICAL eligibility test ``_split_cells``'s own loop applies per pair, reused
+    here to determine the parallel pre-warm's task set BEFORE any worker process starts (never a
+    second eligibility rule)."""
+    records = _verified_records(dataset_store)
+    events = compute_setups(bar_store, config)["events"] if records else []
+    return [
+        r for r in records
+        if (lambda e: e is not None and e["band"]["class"] is not None)(_dataset_event(r, events))
+    ]
+
+
+def _run_dataset_pairs_in_worker(
+    *,
+    dataset_id: str,
+    dataset_dir: str,
+    bar_dir: str,
+    sub_cache_db_path: str,
+    config: Config,
+    profile: str,
+    bar_store_signature: tuple,
+    config_fingerprint: str,
+    config_content_hash: str,
+    strategy_registry: list[dict],
+) -> dict:
+    """era-fast_wall J-05 — ONE ``ProcessPoolExecutor`` task: runs ALL THREE registered strategies'
+    backtests for ONE dataset in a FRESH worker process. Builds its own ``DatasetStore``/
+    ``BarStore`` from the EXPLICIT paths given (never a shared object across the process boundary —
+    these cannot be usefully pickled anyway) and its own THROWAWAY temp ``JournalStore`` for job
+    bookkeeping ONLY (discarded on return; the report never references backtest ids — goal.md's own
+    wording). Publishes each completed pair to the durable ``sub_cache`` (a FRESH connection —
+    SQLite/WAL tolerates many concurrent writer processes) the INSTANT it finishes, and SKIPS any
+    pair the cache already holds (so a resumed sweep — e.g. re-running the CLI after a prior
+    partial parallel run — never redoes already-published work even inside the parallel path
+    itself). MUST be a MODULE-LEVEL function (picklable by reference) for the ``spawn`` context.
+    Returns ``{"dataset_id", "pid"}`` — bookkeeping/test-observability ONLY; the actual report is
+    reassembled by the orchestrator afterward via the untouched sequential ``_split_cells``/
+    ``run_pair`` sub-cache-hit path."""
+    with tempfile.TemporaryDirectory(prefix="edge-report-sweep-worker-") as tmp_dir:
+        store = JournalStore(os.path.join(tmp_dir, "journal.db"), config)
+        try:
+            dataset_store = DatasetStore(dataset_dir)
+            bar_store = BarStore(bar_dir)
+            jobs = BacktestJobManager(store, config)
+            sub_cache = EdgeReportBacktestCache(sub_cache_db_path)
+            dataset_meta = dataset_store.get(dataset_id)
+            for strategy_id in _ALL_STRATEGY_IDS:
+                key = pair_cache_key(
+                    dataset_id=dataset_meta["id"],
+                    dataset_checksum=dataset_meta["checksum"],
+                    strategy_id=strategy_id,
+                    profile=profile,
+                    config_fingerprint=config_fingerprint,
+                    config_content_hash=config_content_hash,
+                    strategy_registry=strategy_registry,
+                    bar_store_signature=bar_store_signature,
+                )
+                if sub_cache.lookup(key) is not None:
+                    continue  # already durable -- resumable even inside the parallel path itself
+                result = _run_backtest(
+                    jobs, store, dataset_store, dataset_meta["id"],
+                    strategy_id=strategy_id, profile=profile, bar_store=bar_store,
+                )
+                sub_cache.publish(key, result)
+        finally:
+            store.close()
+    return {"dataset_id": dataset_id, "pid": os.getpid()}
+
+
+def _parallel_prewarm_sub_cache(
+    dataset_store: DatasetStore,
+    bar_store: BarStore,
+    config: Config,
+    *,
+    sub_cache: EdgeReportBacktestCache,
+    workers: int,
+    should_abort=None,
+) -> list[dict]:
+    """era-fast_wall J-05 — CLI-ONLY parallel pre-warm (see ``EdgeReportComputeManager.trigger``'s
+    own ``workers<=1`` guard/test — this branch is never reachable from a request thread in this
+    iteration's shipped callers; ``run_strategy_comparison_report``'s own ``compute()`` dispatch is
+    the ONLY call site). Determines the ELIGIBLE (dataset, all 3 strategies) task set with the SAME
+    eligibility test ``_split_cells`` itself uses (``_eligible_datasets``, above), schedules
+    eligible datasets LARGEST-FIRST (LPT) by their own recorded ``event_counts.total``, and runs
+    them across ``workers`` worker PROCESSES (``ProcessPoolExecutor``, ``spawn`` context) — task =
+    ONE dataset (its three strategies) each, so peak memory is bounded to ~one parsed dataset per
+    worker. Each worker builds its OWN stores from EXPLICIT paths — derived here from
+    ``config.dataset_dir_resolved()``/``bar_store.root`` (the CLI's own construction invariant:
+    this path is CLI-only, and the CLI's ``dataset_store``/``bar_store`` are ALWAYS built from
+    exactly those resolved paths — see ``edge_report_compute.main``) — and a THROWAWAY temp journal
+    DB for job bookkeeping, publishing each completed pair to the durable ``sub_cache`` the INSTANT
+    it finishes. Returns the raw per-task ``{"dataset_id", "pid"}`` results (bookkeeping/test-
+    observability only) — the caller (``run_strategy_comparison_report``) reassembles the ACTUAL
+    report afterward through the UNTOUCHED sequential ``_split_cells``/``run_pair`` sub-cache-hit
+    path, byte-identical to a fresh sequential run BY CONSTRUCTION (the pooling/aggregation code
+    never changed). A registry with ZERO eligible pairs never spins up a process pool at all
+    (returns ``[]`` immediately) — no wasted worker-startup cost for nothing to do. Cooperative
+    cancellation (``should_abort``) is checked before EACH new task submission — an already-
+    in-flight task always finishes and persists its own pairs (goal.md's own wording)."""
+    eligible = _eligible_datasets(dataset_store, bar_store, config)
+    if not eligible:
+        return []
+    eligible.sort(key=lambda r: r["event_counts"]["total"], reverse=True)  # LPT: largest first
+
+    bar_store_signature = _store_signature(bar_store)
+    config_fingerprint = config.config_fingerprint()
+    config_content_hash = _config_content_hash(config)
+    strategy_registry = config.strategy_registry()
+    dataset_dir = config.dataset_dir_resolved()
+    bar_dir = str(bar_store.root)
+
+    results: list[dict] = []
+    ctx = multiprocessing.get_context("spawn")
+    with ProcessPoolExecutor(max_workers=max(1, workers), mp_context=ctx) as executor:
+        futures: dict = {}
+        for dataset_meta in eligible:
+            if should_abort is not None and should_abort():
+                break  # stop SUBMITTING -- already-submitted futures below still finish/persist
+            future = executor.submit(
+                _run_dataset_pairs_in_worker,
+                dataset_id=dataset_meta["id"], dataset_dir=dataset_dir, bar_dir=bar_dir,
+                sub_cache_db_path=sub_cache.db_path, config=config, profile=PROFILE_DEFAULT,
+                bar_store_signature=bar_store_signature, config_fingerprint=config_fingerprint,
+                config_content_hash=config_content_hash, strategy_registry=strategy_registry,
+            )
+            futures[future] = dataset_meta["id"]
+        for future in as_completed(futures):
+            results.append(future.result())
+    return results
+
+
 def _cell_beats_null(cell: dict) -> bool:
     """"Beats its own null baseline" — the ``_beats_null`` gate, applied to a strategy-comparison
     CELL instead of a per-dataset champion row (a genuine twin, not a re-derived formula: BOTH net
@@ -541,8 +765,8 @@ def run_strategy_comparison_report(
     force: bool = False,
     progress=None,
     should_abort=None,
-    sub_cache=None,
-    workers=None,
+    sub_cache: "EdgeReportBacktestCache | None" = None,
+    workers: int | None = None,
 ) -> dict:
     """The always-recompute-or-serve-through-a-cache entry point for the 3-way strategy-comparison
     report (era-5B J-04). See ``_compute_strategy_comparison_report`` below for the full algorithm
@@ -580,16 +804,31 @@ def run_strategy_comparison_report(
         which propagates UNCHANGED through ``cache.get_or_compute``/``compute_and_publish``
         (both publish ONLY after ``compute_fn`` returns normally) — a cancelled run publishes
         NOTHING, by construction, with zero change to either cache method's body.
-      * ``sub_cache``/``workers`` are ACCEPTED this iteration but currently INERT (a logged
-        assumption — see the dev handoff): every compute this iteration triggers runs strictly
-        sequentially regardless of their value. J-05's resumable/parallel sweep (the
-        ``EdgeReportBacktestCache`` per-pair sub-cache + the ``ProcessPoolExecutor`` provider)
-        gives them real effect; their signature exists NOW so J-05 adds no further parameter
-        churn to this function."""
+      * ``sub_cache`` (era-fast_wall J-05, real effect now — see ``_build_caching_run_pair``):
+        the durable per-(dataset x strategy)-pair ``EdgeReportBacktestCache``. Threaded straight
+        into ``_compute_strategy_comparison_report`` so every backtest pair is served/published
+        through it — a killed-and-retriggered sweep with the SAME ``sub_cache`` skips every
+        already-published pair (resumable).
+      * ``workers`` (era-fast_wall J-05, real effect now): when ``sub_cache`` is ALSO supplied and
+        ``workers`` resolves to more than one, this function FIRST pre-warms ``sub_cache`` via
+        ``_parallel_prewarm_sub_cache`` (a ``ProcessPoolExecutor``, CLI-only — see that function's
+        own docstring for why this is safe to call from ANY caller: the manager's own ``trigger()``
+        never supplies ``workers > 1``, a logged, tested assumption) BEFORE calling
+        ``_compute_strategy_comparison_report`` — which then finds every eligible pair already
+        cached and simply reassembles the report sequentially, byte-identical to a wholly
+        sequential run BY CONSTRUCTION (the pooling/aggregation code never changed). ``workers in
+        (None, 0, 1)`` (the default, and every caller before this iteration) skips the pre-warm
+        entirely — byte-identical to the pre-J-05 body."""
 
     def compute() -> dict:
+        if sub_cache is not None and workers is not None and workers > 1:
+            _parallel_prewarm_sub_cache(
+                dataset_store, bar_store, config,
+                sub_cache=sub_cache, workers=workers, should_abort=should_abort,
+            )
         return _compute_strategy_comparison_report(
-            store, dataset_store, bar_store, config, progress=progress, should_abort=should_abort,
+            store, dataset_store, bar_store, config,
+            progress=progress, should_abort=should_abort, sub_cache=sub_cache,
         )
 
     if cache is None:
@@ -655,6 +894,7 @@ def _compute_strategy_comparison_report(
     *,
     progress=None,
     should_abort=None,
+    sub_cache: "EdgeReportBacktestCache | None" = None,
 ) -> dict:
     """The ONE computer of the 3-way strategy-comparison report (era-5B J-04; renamed from
     ``run_strategy_comparison_report`` at era-5B J-08 — see that function's own docstring for why:
@@ -671,7 +911,14 @@ def _compute_strategy_comparison_report(
     ``_ProgressReporter`` (never a separate reporter per split — its running totals must span both
     splits). ``backtests_total`` is sized ONCE, right after ``events`` resolves (the earliest point
     both splits' eligible-pair counts are knowable), via ``_count_eligible_pairs`` — never inside
-    ``_split_cells`` itself, so that function's own loop stays untouched."""
+    ``_split_cells`` itself, so that function's own loop stays untouched.
+
+    era-fast_wall J-05: ``sub_cache`` (optional, default ``None`` — byte-identical to the pre-J-05
+    body when omitted) is the durable per-pair ``EdgeReportBacktestCache``. When supplied, ONE
+    caching ``run_pair`` provider (``_build_caching_run_pair``) is built HERE — after ``reporter``
+    resolves, so a cache hit can notify it — and threaded into BOTH the train and hold-out
+    ``_split_cells`` calls below: the SAME provider/cache instance serves both splits (goal.md's
+    own wording), never a second cache/provider per split."""
     jobs = BacktestJobManager(store, config)
     train_datasets = _split_datasets(dataset_store, SPLIT_TRAIN)
     holdout_datasets = _split_datasets(dataset_store, SPLIT_HOLDOUT)
@@ -689,13 +936,17 @@ def _compute_strategy_comparison_report(
         total = _count_eligible_pairs(train_datasets, events) + _count_eligible_pairs(holdout_datasets, events)
         reporter = _ProgressReporter(progress, total)
 
+    run_pair = None
+    if sub_cache is not None:
+        run_pair = _build_caching_run_pair(jobs, store, dataset_store, bar_store, config, sub_cache, reporter)
+
     train_cells = _split_cells(
         jobs, store, dataset_store, bar_store, train_datasets, events, config,
-        reporter=reporter, should_abort=should_abort,
+        reporter=reporter, should_abort=should_abort, run_pair=run_pair,
     )
     holdout_cells = _split_cells(
         jobs, store, dataset_store, bar_store, holdout_datasets, events, config,
-        reporter=reporter, should_abort=should_abort,
+        reporter=reporter, should_abort=should_abort, run_pair=run_pair,
     )
 
     return {
diff --git a/apps/backend/app/research/edge_report_compute.py b/apps/backend/app/research/edge_report_compute.py
index 1c4ce59..fe43ed1 100644
--- a/apps/backend/app/research/edge_report_compute.py
+++ b/apps/backend/app/research/edge_report_compute.py
@@ -1,7 +1,17 @@
-"""era-fast_wall J-04 — the operator-run compute: a single-flight, cancellable, progress-reporting
-background job around ``edge_report.run_strategy_comparison_report``'s five additive keyword-only
-hooks (``force``/``progress``/``should_abort``/``sub_cache``/``workers`` — see that function's own
-docstring), plus a CLI warmer that drives the SAME hooks synchronously, in-process.
+"""era-fast_wall J-04/J-05 — the operator-run compute: a single-flight, cancellable, progress-
+reporting background job around ``edge_report.run_strategy_comparison_report``'s five additive
+keyword-only hooks (``force``/``progress``/``should_abort``/``sub_cache``/``workers`` — see that
+function's own docstring), plus a CLI warmer that drives the SAME hooks synchronously, in-process.
+
+era-fast_wall J-05 gives ``sub_cache``/``workers`` their real effect (J-04 forward-declared them,
+accepted-but-INERT). ``EdgeReportComputeManager.trigger()`` now threads a real, durable
+``EdgeReportBacktestCache`` into its own compute call (``sub_cache=``) — a browser-triggered
+compute is resumable too — but NEVER passes ``workers`` above ``1``/``None`` (a logged, tested
+assumption: process-pool parallelism stays CLI-only this iteration, never inside the always-on
+FastAPI/uvicorn process). The CLI warmer's ``main()`` passes BOTH ``sub_cache=`` and
+``workers=args.workers`` (the CLI's own arg, default read from ``TAPEOLOGY_EDGE_SWEEP_WORKERS``
+else 4) — a value above 1 genuinely parallelizes via ``edge_report.py``'s own
+``_parallel_prewarm_sub_cache``/``ProcessPoolExecutor`` provider.
 
 THIS MODULE computes NOTHING itself — ``run_strategy_comparison_report`` (and, through it,
 ``EdgeReportCache.get_or_compute``/``compute_and_publish``, both already shipped at J-01) stay the
@@ -40,6 +50,7 @@ from __future__ import annotations
 
 import argparse
 import json
+import os
 import sys
 import threading
 import uuid
@@ -51,14 +62,17 @@ from ..config import CONFIG, Config
 from .bars import BarStore
 from .datasets import DatasetStore
 from .edge_report import EdgeReportComputeCancelled, EdgeReportError, run_strategy_comparison_report
+from .edge_report_backtest_cache import EdgeReportBacktestCache, resolve_backtest_cache_db_path
 from .edge_report_cache import EdgeReportCache, resolve_cache_db_path
 from .store import JournalStore
 
 __all__ = ["EdgeReportComputeManager"]
 
-# Mirrors goal.md's own CLI usage string (``--workers N``, default 4) — accepted this iteration,
-# currently INERT (see ``run_strategy_comparison_report``'s own docstring; J-05 gives it effect).
+# Mirrors goal.md's own CLI usage string (``--workers N``, default 4) — the CLI's OWN fallback
+# default when neither ``--workers`` nor ``TAPEOLOGY_EDGE_SWEEP_WORKERS`` is set (era-fast_wall
+# J-05 gives ``workers`` real effect via ``run_strategy_comparison_report``'s own dispatch).
 _DEFAULT_WORKERS = 4
+_WORKERS_ENV = "TAPEOLOGY_EDGE_SWEEP_WORKERS"
 
 
 def _iso_utc_now() -> str:
@@ -122,6 +136,7 @@ class EdgeReportComputeManager:
         cache: EdgeReportCache,
         *,
         force: bool = False,
+        sub_cache: "EdgeReportBacktestCache | None" = None,
     ) -> dict:
         """Start a NEW compute job, or — if one is already ``state == "running"`` — return it
         UNCHANGED (``started: False``, the SAME job's own ``force``, never the just-requested one).
@@ -129,7 +144,15 @@ class EdgeReportComputeManager:
         call always starts a genuinely new job (a fresh id), discarding the prior snapshot. Never
         blocks on the compute itself — the actual sweep runs on a dedicated worker thread, OFF the
         caller's thread (the ``BacktestJobManager.start`` precedent), so an HTTP route calling this
-        returns immediately."""
+        returns immediately.
+
+        era-fast_wall J-05: ``sub_cache`` (optional, default ``None`` — preserves every existing
+        caller's exact behavior byte-for-byte) is threaded straight into the compute call's own
+        ``sub_cache=`` hook (making a browser-triggered compute resumable too — a killed-and-
+        retriggered job skips already-published pairs). NEVER passes ``workers`` to
+        ``run_strategy_comparison_report`` — process-pool parallelism stays CLI-only this iteration
+        (a logged, tested assumption; see ``test_trigger_never_passes_a_workers_value_greater_
+        than_one`` in ``tests/test_edge_report_compute.py``)."""
         with self._lock:
             current = self._snapshot
             if current is not None and current["state"] == "running":
@@ -165,7 +188,7 @@ class EdgeReportComputeManager:
                 run_strategy_comparison_report(
                     store, dataset_store, bar_store, config,
                     cache=cache, force=force, progress=_publish_progress,
-                    should_abort=cancel_event.is_set,
+                    should_abort=cancel_event.is_set, sub_cache=sub_cache,
                 )
             except EdgeReportComputeCancelled:
                 self._resolve(job_id, "cancelled", error=None)
@@ -248,16 +271,24 @@ def main() -> int:
     ``GET /research/edge-report`` serves (``resolve_cache_db_path`` — the identical resolver the
     route's own dependency uses). An ``EdgeReportError`` (a corrupt dataset) prints an explicit
     message to stderr and exits 1 with nothing published — the existing ``get_or_compute``/
-    ``compute_and_publish`` discipline (nothing is ever cached on an exception)."""
+    ``compute_and_publish`` discipline (nothing is ever cached on an exception).
+
+    era-fast_wall J-05: also constructs a real ``EdgeReportBacktestCache`` (via the shared
+    ``resolve_backtest_cache_db_path`` resolver — the ``resolve_cache_db_path`` pattern, a
+    DIFFERENT env var/sibling filename) and passes it as ``sub_cache=`` alongside the already-
+    passed ``workers=args.workers`` — giving both hooks their real, resumable/parallel effect (see
+    ``run_strategy_comparison_report``'s own docstring)."""
     parser = argparse.ArgumentParser(
-        description="era-fast_wall J-04 CLI warmer -- run the 3-way v1/structure_tape/"
+        description="era-fast_wall J-04/J-05 CLI warmer -- run the 3-way v1/structure_tape/"
         "structure_tape_map edge-report sweep to completion, publishing to the SAME durable "
-        "cache GET /research/edge-report serves."
+        "caches GET /research/edge-report serves (resumable, and genuinely parallel above 1)."
     )
     parser.add_argument(
-        "--workers", type=int, default=_DEFAULT_WORKERS,
-        help="accepted for the future parallel sweep (J-05); INERT this iteration -- every "
-        "compute runs strictly sequentially regardless of this value.",
+        "--workers", type=int,
+        default=int(os.environ.get(_WORKERS_ENV, str(_DEFAULT_WORKERS))),
+        help="number of worker PROCESSES for the parallel sweep (documented ceiling ~6). Values "
+        "above 1 genuinely parallelize via a ProcessPoolExecutor -- CLI-only, never the button/"
+        f"manager path. Defaults to ${_WORKERS_ENV} if set, else {_DEFAULT_WORKERS}.",
     )
     parser.add_argument(
         "--force", action="store_true",
@@ -272,12 +303,13 @@ def main() -> int:
         dataset_store = DatasetStore(config.dataset_dir_resolved())
         bar_store = BarStore(config.bar_dir_resolved())
         cache = EdgeReportCache(resolve_cache_db_path(config.dataset_dir_resolved()))
+        sub_cache = EdgeReportBacktestCache(resolve_backtest_cache_db_path(config.dataset_dir_resolved()))
 
         try:
             report = run_strategy_comparison_report(
                 store, dataset_store, bar_store, config,
                 cache=cache, force=args.force, progress=_cli_progress_printer(),
-                workers=args.workers,
+                workers=args.workers, sub_cache=sub_cache,
             )
         except EdgeReportError as exc:
             print(f"error: {exc}", file=sys.stderr)
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index e6c25fc..c285ef7 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -50,6 +50,7 @@ from .bars import (
     EmptyBarWindowError,
 )
 from .edge_report import EdgeReportError, peek_strategy_comparison_report
+from .edge_report_backtest_cache import EdgeReportBacktestCache, resolve_backtest_cache_db_path
 from .edge_report_cache import EdgeReportCache, resolve_cache_db_path
 from .edge_report_compute import EdgeReportComputeManager
 from .levels import compute_levels
@@ -1612,6 +1613,16 @@ def get_edge_report_cache() -> EdgeReportCache:
     return EdgeReportCache(resolve_cache_db_path(CONFIG.dataset_dir_resolved()))
 
 
+def get_edge_report_backtest_cache() -> EdgeReportBacktestCache:
+    """The persisted, rebuildable per-(dataset x strategy)-pair backtest sub-cache (era-fast_wall
+    J-05) — the ``get_edge_report_cache`` precedent, mirrored for a DIFFERENT durable file: the
+    ``TAPEOLOGY_EDGE_SWEEP_CACHE_DB`` env var if set, else a file co-located as a SIBLING of the
+    config-owned dataset directory (``resolve_backtest_cache_db_path`` — the shared resolver, the
+    ``resolve_cache_db_path`` pattern). A FastAPI dependency so tests can override it outright or
+    point it at a temp path via the env var."""
+    return EdgeReportBacktestCache(resolve_backtest_cache_db_path(CONFIG.dataset_dir_resolved()))
+
+
 def get_bar_fetch_adapter():
     """The market adapter for the BAR-FETCH path ONLY (``POST /research/bars`` — era-5 J-01).
 
@@ -2180,15 +2191,21 @@ def trigger_edge_report_compute(
     dataset_store: DatasetStore = Depends(get_dataset_store),
     bar_store: BarStore = Depends(get_bar_store),
     cache: EdgeReportCache = Depends(get_edge_report_cache),
+    sub_cache: EdgeReportBacktestCache = Depends(get_edge_report_backtest_cache),
 ) -> dict:
     """Start the single-flight edge-report compute job, or — if one is already running — return it
     UNCHANGED (``started: False``, never a second concurrent job). Returns
     ``{"started": bool, "compute": <snapshot>}``; the actual sweep runs on a background worker
     thread, off this request (``EdgeReportComputeManager.trigger`` — the ``create_backtest``/
     ``jobs.start`` precedent), so this route returns immediately regardless of how long the sweep
-    takes."""
+    takes.
+
+    era-fast_wall J-05: also injects the durable per-pair sub-cache
+    (``get_edge_report_backtest_cache``), threaded into ``trigger()`` so a browser-triggered
+    compute is resumable too — a killed-and-retriggered job skips already-published pairs."""
     return registry.edge_report_compute.trigger(
-        registry.store, dataset_store, bar_store, registry.config, cache, force=body.force,
+        registry.store, dataset_store, bar_store, registry.config, cache,
+        force=body.force, sub_cache=sub_cache,
     )
 
 
diff --git a/apps/backend/tests/test_edge_report.py b/apps/backend/tests/test_edge_report.py
index 525e9c5..eb0c2e4 100644
--- a/apps/backend/tests/test_edge_report.py
+++ b/apps/backend/tests/test_edge_report.py
@@ -838,6 +838,7 @@ def test_3way_report_source_reuses_the_shared_aggregate_and_never_a_second_edge_
 # ==================================================================================================
 
 from app.research.edge_report_cache import EdgeReportCache  # noqa: E402
+from app.research.edge_report_backtest_cache import EdgeReportBacktestCache  # noqa: E402
 
 
 def test_cache_none_default_is_byte_identical_to_the_pre_j08_uncached_call(
@@ -1104,13 +1105,21 @@ from app.research.edge_report import EdgeReportComputeCancelled  # noqa: E402
 def test_progress_and_should_abort_supplied_but_unused_is_byte_identical_to_the_default_path(
     tmp_path, store, scan_bar_store, scan_config
 ):
-    """TC-14a: the hooked path (every new kwarg actively supplied but never triggered to abort)
-    produces a report byte-identical to the pre-existing default path — on the REAL, non-degenerate
-    3-cell synthetic-scan-join shape (the iter-4 lesson: never merely the vacuous empty case)."""
+    """TC-14a: the hooked path (every new kwarg actively supplied, ``should_abort`` never firing,
+    ``workers`` never resolving above 1 so the parallel branch never triggers) produces a report
+    byte-identical to the pre-existing default path — on the REAL, non-degenerate 3-cell
+    synthetic-scan-join shape (the iter-4 lesson: never merely the vacuous empty case).
+
+    era-fast_wall J-05: ``sub_cache`` is now threaded through as a REAL ``EdgeReportBacktestCache``
+    (no longer the J-04 placeholder sentinel ``object()`` — J-05 gives it genuine caching effect,
+    still producing byte-identical output; the dedicated ``sub_cache=None``-vs-warm claim is proven
+    in isolation by ``test_sub_cache_supplied_report_is_byte_identical_to_the_default_path``,
+    below the J-05 marker)."""
     dataset_store = DatasetStore(tmp_path / "datasets")
     _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
     cache_a = EdgeReportCache(str(tmp_path / "cache-a.db"))
     cache_b = EdgeReportCache(str(tmp_path / "cache-b.db"))
+    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))
 
     progress_events: list[dict] = []
 
@@ -1122,7 +1131,7 @@ def test_progress_and_should_abort_supplied_but_unused_is_byte_identical_to_the_
     )
     hooked_path = run_strategy_comparison_report(
         store, dataset_store, scan_bar_store, scan_config, cache=cache_b,
-        progress=_progress, should_abort=lambda: False, sub_cache=object(), workers=7,
+        progress=_progress, should_abort=lambda: False, sub_cache=sub_cache, workers=1,
     )
 
     assert json.dumps(default_path, sort_keys=True) == json.dumps(hooked_path, sort_keys=True)
@@ -1320,9 +1329,326 @@ def test_peek_compute_field_embeds_whatever_is_passed_verbatim(
 
 def test_run_strategy_comparison_report_source_documents_the_five_new_hooks():
     """A coherence guard: the five new keyword-only params exist textually on the function's OWN
-    signature (never silently absorbed into ``**kwargs`` or dropped)."""
+    signature (never silently absorbed into ``**kwargs`` or dropped). era-fast_wall J-05: ``sub_
+    cache``/``workers`` now carry real type hints (``EdgeReportBacktestCache | None`` / ``int |
+    None``) since they gained real effect — the literal substrings below are updated to match."""
     import inspect
 
     src = inspect.getsource(edge_report.run_strategy_comparison_report)
-    for hook in ("force: bool = False", "progress=None", "should_abort=None", "sub_cache=None", "workers=None"):
+    for hook in (
+        "force: bool = False",
+        "progress=None",
+        "should_abort=None",
+        'sub_cache: "EdgeReportBacktestCache | None" = None',
+        "workers: int | None = None",
+    ):
         assert hook in src
+
+
+# ==================================================================================================
+# The resumable + parallel sweep (era-fast_wall J-05) — ``EdgeReportBacktestCache`` given real
+# effect: ``_split_cells``'s ``run_pair`` seam, ``_build_caching_run_pair``, and the CLI-only
+# ``_parallel_prewarm_sub_cache``. ``EdgeReportBacktestCache``'s OWN mechanics (keying, durability,
+# corrupted-DB tolerance, concurrency) are unit-tested in isolation in
+# ``tests/test_edge_report_backtest_cache.py`` against a cheap counting stub — this section proves
+# the WIRING into the real ``_split_cells``/``_run_backtest``/``run_strategy_comparison_report``
+# path (byte-identity, kill-and-resume, new-dataset-costs-three, cache-loss recompute, the
+# non-vacuous multi-process parallel proof).
+# ==================================================================================================
+
+
+def test_build_caching_run_pair_computes_signature_and_config_hashes_once_per_sweep_not_per_pair():
+    """Coherence guard (the NOTES' own implementation hint): ``bar_store_signature``/
+    ``config_fingerprint``/``config_content_hash``/``strategy_registry`` are computed OUTSIDE the
+    ``run_pair`` closure — textually BEFORE ``def run_pair(`` — so they run ONCE per sweep, never
+    once per pair (the exact wasteful-recomputation pattern this whole interlude exists to
+    remove)."""
+    import inspect
+
+    src = inspect.getsource(edge_report._build_caching_run_pair)
+    closure_start = src.index("def run_pair(")
+    setup, closure_body = src[:closure_start], src[closure_start:]
+
+    assert "_store_signature(bar_store)" in setup
+    assert "config.config_fingerprint()" in setup
+    assert "_config_content_hash(config)" in setup
+    assert "config.strategy_registry()" in setup
+    for forbidden in (
+        "_store_signature(", "config.config_fingerprint(",
+        "_config_content_hash(", "config.strategy_registry(",
+    ):
+        assert forbidden not in closure_body, f"{forbidden} must not be recomputed per pair"
+
+
+def test_sub_cache_supplied_report_is_byte_identical_to_the_default_path(
+    tmp_path, store, scan_bar_store, scan_config
+):
+    """TC-13: ``sub_cache=None`` (today's pre-J-05 shape) vs a genuinely warm ``sub_cache``
+    produce byte-identical reports for the SAME inputs."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))
+
+    without_sub_cache = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)
+    with_sub_cache = run_strategy_comparison_report(
+        store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache,
+    )
+
+    assert json.dumps(without_sub_cache, sort_keys=True) == json.dumps(with_sub_cache, sort_keys=True)
+    assert len(without_sub_cache["train"]["cells"]) == 3  # non-degenerate: the real 3-cell shape
+
+
+def test_a_fully_cached_sweep_publishes_every_eligible_pair_and_is_byte_identical(
+    tmp_path, store, scan_bar_store, scan_config
+):
+    """TC-4: given the fixture dataset registry and a fresh, empty ``EdgeReportBacktestCache`` DB,
+    a full sweep publishes a durable row for EVERY eligible (dataset, strategy) pair, and the
+    returned report is byte-identical to the SAME inputs computed with ``sub_cache=None``."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    sub_cache_db_path = tmp_path / "sub-cache.db"
+    sub_cache = EdgeReportBacktestCache(str(sub_cache_db_path))
+
+    warm = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache)
+    fresh = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)  # sub_cache=None
+
+    assert json.dumps(warm, sort_keys=True) == json.dumps(fresh, sort_keys=True)
+
+    import sqlite3
+
+    conn = sqlite3.connect(str(sub_cache_db_path))
+    try:
+        (count,) = conn.execute("SELECT COUNT(*) FROM edge_report_backtest_cache").fetchone()
+    finally:
+        conn.close()
+    assert count == 3  # one row per (dataset, strategy) pair -- 1 dataset x 3 registered strategies
+
+
+def test_kill_and_resume_recomputes_only_the_missing_pairs(
+    tmp_path, store, scan_bar_store, scan_config, monkeypatch
+):
+    """TC-6: a sweep aborted (via ``should_abort``) after publishing N pairs, re-triggered with the
+    SAME ``sub_cache``, makes fresh ``_run_backtest`` calls for ONLY the remaining pairs, and the
+    progress snapshot's ``backtests_from_cache`` equals N."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))
+
+    should_abort_calls = {"n": 0}
+
+    def _should_abort() -> bool:
+        should_abort_calls["n"] += 1
+        return should_abort_calls["n"] > 1  # fires at the top of the 2nd pair -- never before the 1st
+
+    with pytest.raises(EdgeReportComputeCancelled):
+        run_strategy_comparison_report(
+            store, dataset_store, scan_bar_store, scan_config,
+            sub_cache=sub_cache, should_abort=_should_abort,
+        )
+
+    import sqlite3
+
+    conn = sqlite3.connect(sub_cache.db_path)
+    try:
+        (published_before_resume,) = conn.execute("SELECT COUNT(*) FROM edge_report_backtest_cache").fetchone()
+    finally:
+        conn.close()
+    assert published_before_resume == 1  # exactly the first (v1) pair persisted before the abort
+
+    calls = []
+    real_run_backtest = edge_report._run_backtest
+
+    def _counting_run_backtest(*args, **kwargs):
+        calls.append(1)
+        return real_run_backtest(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report, "_run_backtest", _counting_run_backtest)
+
+    progress_events: list[dict] = []
+    result = run_strategy_comparison_report(
+        store, dataset_store, scan_bar_store, scan_config,
+        sub_cache=sub_cache, progress=progress_events.append,
+    )
+
+    assert len(calls) == 2  # only the 2 REMAINING (of 3 total) pairs recomputed
+    pair_done_events = [e for e in progress_events if e.get("event") == "pair_done"]
+    assert pair_done_events[-1]["backtests_from_cache"] == 1  # the ONE pair served from cache
+    assert len(result["train"]["cells"]) == 3  # the reassembled report is still complete/correct
+
+
+def test_a_new_dataset_costs_exactly_three_fresh_backtests_on_a_warm_sub_cache(
+    tmp_path, store, scan_bar_store, scan_config, monkeypatch
+):
+    """TC-7: given a fully-warm sub-cache for the existing fixture registry, registering ONE
+    additional dataset and re-triggering the sweep costs EXACTLY three new ``_run_backtest`` calls
+    (one per registered strategy), zero for the pre-existing dataset."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))
+    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache)
+
+    _record_v1_arming_dataset(dataset_store, max_logical=200.0, split=SPLIT_TRAIN, feed="sim", label="b")
+
+    calls = []
+    real_run_backtest = edge_report._run_backtest
+
+    def _counting_run_backtest(*args, **kwargs):
+        calls.append(1)
+        return real_run_backtest(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report, "_run_backtest", _counting_run_backtest)
+
+    result = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache)
+
+    assert len(calls) == 3  # exactly 3 fresh backtests for the ONE new dataset, 0 for the pre-existing one
+    v1_cell = next(c for c in result["train"]["cells"] if c["strategy_id"] == STRATEGY_V1_ID)
+    assert v1_cell["measurement"]["n"] == 2  # both datasets pooled into the recomputed cell
+
+
+def test_deleting_the_sub_cache_db_triggers_a_full_recompute_byte_identical_to_the_original(
+    tmp_path, store, scan_bar_store, scan_config, monkeypatch
+):
+    """TC-9: deleting the sub-cache DB file loses nothing — the next sweep fully recomputes every
+    pair (a call-counting spy confirms it, never merely inferred from the output alone) and
+    republishes, producing a report byte-identical to the original warm-cache report."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    sub_cache_db_path = tmp_path / "sub-cache.db"
+    sub_cache = EdgeReportBacktestCache(str(sub_cache_db_path))
+
+    original = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache)
+
+    for suffix in ("", "-wal", "-shm"):
+        sidecar = Path(str(sub_cache_db_path) + suffix)
+        if sidecar.exists():
+            sidecar.unlink()
+
+    calls = []
+    real_run_backtest = edge_report._run_backtest
+
+    def _counting_run_backtest(*args, **kwargs):
+        calls.append(1)
+        return real_run_backtest(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report, "_run_backtest", _counting_run_backtest)
+
+    fresh_sub_cache = EdgeReportBacktestCache(str(sub_cache_db_path))
+    store2 = JournalStore(str(tmp_path / "journal-2.db"), scan_config)
+    try:
+        recomputed = run_strategy_comparison_report(
+            store2, dataset_store, scan_bar_store, scan_config, sub_cache=fresh_sub_cache,
+        )
+    finally:
+        store2.close()
+
+    assert len(calls) == 3  # every pair genuinely re-run, never silently served from stale state
+    assert json.dumps(recomputed, sort_keys=True) == json.dumps(original, sort_keys=True)
+
+
+def test_a_corrupted_sub_cache_db_is_treated_as_a_full_miss_never_a_crash(
+    tmp_path, store, scan_bar_store, scan_config
+):
+    """Error case: a corrupted/unreadable sub-cache DB is treated as a full miss (recompute), never
+    a crash — proven through the REAL sweep end to end, not merely ``EdgeReportBacktestCache`` in
+    isolation (see ``test_edge_report_backtest_cache.py`` for that isolated proof)."""
+    garbage_path = tmp_path / "garbage.db"
+    garbage_path.write_bytes(b"not a real sqlite file, just garbage bytes " * 20)
+    sub_cache = EdgeReportBacktestCache(str(garbage_path))
+
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+
+    result = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache)
+
+    assert len(result["train"]["cells"]) == 3  # a full, correct recompute despite the corrupt DB
+
+
+def test_a_worker_side_backtest_failure_propagates_as_a_genuine_sweep_failure(
+    tmp_path, store, scan_bar_store, scan_config, monkeypatch
+):
+    """Error case: a pair's ``_run_backtest`` raising propagates as a genuine sweep failure — never
+    a silently-dropped pair, and nothing is published for that pair."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))
+
+    def _boom(*args, **kwargs):
+        raise RuntimeError("synthetic backtest failure")
+
+    monkeypatch.setattr(edge_report, "_run_backtest", _boom)
+
+    with pytest.raises(RuntimeError, match="synthetic backtest failure"):
+        run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache)
+
+    assert sub_cache.lookup("anything") is None  # sanity: cache is still genuinely empty (no crash-loop artifact)
+
+
+# --- The parallel provider (CLI-only) — a non-vacuous, genuinely multi-process proof (TC-8) -------
+
+
+def test_parallel_prewarm_uses_at_least_two_distinct_worker_processes_and_reassembles_byte_identically(
+    tmp_path, store, scan_bar_store, scan_config, monkeypatch
+):
+    """TC-8 (non-vacuous): two datasets, each resolving the SAME real classified scan event,
+    pre-warmed via ``_parallel_prewarm_sub_cache(..., workers=2)`` — the RETURNED per-task
+    ``{"dataset_id", "pid"}`` bookkeeping proves at least two DISTINCT worker process ids were
+    genuinely used (never a silent sequential fallback: pids can only cross a process boundary via
+    a real child process's own ``os.getpid()``, pickled back through the future's result — this
+    could not be faked by a same-process shortcut), and the reassembled report (via the SAME
+    untouched sequential ``run_strategy_comparison_report`` call, now 100% cache hits) is
+    byte-identical to an INDEPENDENT, wholly sequential compute of the SAME inputs.
+
+    ``_parallel_prewarm_sub_cache`` derives its workers' dataset directory from
+    ``config.dataset_dir_resolved()`` (the CLI's OWN construction invariant — see that function's
+    own docstring), so this test sets ``TAPEOLOGY_DATASET_DIR`` to match ``dataset_store``'s actual
+    root, exactly as the real CLI's ``main()`` always does."""
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    _record_v1_arming_dataset(dataset_store, max_logical=200.0, split=SPLIT_TRAIN, feed="sim", label="b")
+
+    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache-parallel.db"))
+    task_results = edge_report._parallel_prewarm_sub_cache(
+        dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache, workers=2,
+    )
+
+    assert len(task_results) == 2  # one task per dataset -- "task = one dataset, all 3 strategies"
+    pids = {r["pid"] for r in task_results}
+    assert len(pids) >= 2, f"expected >=2 distinct worker pids, got {pids}"
+
+    parallel_report = run_strategy_comparison_report(
+        store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache,
+    )  # 100% cache hits -- pure sequential reassembly, never a fresh backtest
+
+    sequential_store = JournalStore(str(tmp_path / "journal-seq.db"), scan_config)
+    try:
+        sequential_report = run_strategy_comparison_report(
+            sequential_store, dataset_store, scan_bar_store, scan_config,
+        )  # sub_cache=None -- a wholly independent fresh compute
+    finally:
+        sequential_store.close()
+
+    assert json.dumps(parallel_report, sort_keys=True) == json.dumps(sequential_report, sort_keys=True)
+    assert len(parallel_report["train"]["cells"]) == 3  # non-degenerate: the real 3-cell shape
+
+
+def test_parallel_prewarm_with_zero_eligible_datasets_never_spins_up_a_process_pool(
+    tmp_path, store, monkeypatch
+):
+    """A registry with zero eligible pairs (the committed J-03 fixture's own PG symbol, not a
+    config-owned panel symbol) returns immediately without ever constructing a
+    ``ProcessPoolExecutor`` — no wasted worker-startup cost for nothing to do."""
+    dataset_store = DatasetStore(FIXTURE_J03_DATASET_DIR)
+    bar_store = BarStore(tmp_path / "empty-bars")
+    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))
+
+    def _boom(*args, **kwargs):
+        raise AssertionError("ProcessPoolExecutor must never be constructed with zero eligible tasks")
+
+    monkeypatch.setattr(edge_report, "ProcessPoolExecutor", _boom)
+
+    results = edge_report._parallel_prewarm_sub_cache(
+        dataset_store, bar_store, CONFIG, sub_cache=sub_cache, workers=4,
+    )
+
+    assert results == []
diff --git a/apps/backend/tests/test_edge_report_compute.py b/apps/backend/tests/test_edge_report_compute.py
index d5e8eec..7928da1 100644
--- a/apps/backend/tests/test_edge_report_compute.py
+++ b/apps/backend/tests/test_edge_report_compute.py
@@ -270,6 +270,113 @@ def test_cache_kwarg_is_threaded_through_unchanged(tmp_path, store, monkeypatch)
     manager.join_all(timeout=5)
 
 
+# === era-fast_wall J-05: sub_cache resumability wiring + the never-workers>1 guard ================
+
+
+def test_trigger_sub_cache_default_is_none_unchanged_for_every_pre_j05_caller(
+    tmp_path, store, monkeypatch
+):
+    """Every EXISTING test above this marker calls ``trigger()`` without ``sub_cache`` and stays
+    green unmodified — proof by construction that the default preserves byte-identical behavior.
+    This test makes the claim explicit: the omitted kwarg reaches the compute call as ``None``."""
+    manager = EdgeReportComputeManager()
+    seen = {}
+    _, dataset_store, bar_store, config, cache = _trigger_args(tmp_path, store)
+
+    def fake_run(*args, **kwargs):
+        seen["sub_cache"] = kwargs.get("sub_cache")
+        return _EMPTY_REPORT
+
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)
+
+    manager.trigger(store, dataset_store, bar_store, config, cache)
+    _wait_for_terminal(manager)
+
+    assert seen["sub_cache"] is None
+    manager.join_all(timeout=5)
+
+
+def test_trigger_sub_cache_kwarg_is_threaded_through_to_the_compute_call(tmp_path, store, monkeypatch):
+    """era-fast_wall J-05: a REAL ``sub_cache`` supplied to ``trigger()`` reaches ``run_strategy_
+    comparison_report`` verbatim (never re-derived, never dropped)."""
+    from app.research.edge_report_backtest_cache import EdgeReportBacktestCache
+
+    manager = EdgeReportComputeManager()
+    seen = {}
+    _, dataset_store, bar_store, config, cache = _trigger_args(tmp_path, store)
+    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))
+
+    def fake_run(*args, **kwargs):
+        seen["sub_cache"] = kwargs.get("sub_cache")
+        return _EMPTY_REPORT
+
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)
+
+    manager.trigger(store, dataset_store, bar_store, config, cache, sub_cache=sub_cache)
+    _wait_for_terminal(manager)
+
+    assert seen["sub_cache"] is sub_cache
+    manager.join_all(timeout=5)
+
+
+def test_trigger_never_passes_a_workers_value_greater_than_one(tmp_path, store, monkeypatch):
+    """TC-12: ``trigger()`` must never supply ``workers > 1`` to ``run_strategy_comparison_report``
+    -- process-pool parallelism stays CLI-only this iteration (a logged, tested assumption)."""
+    manager = EdgeReportComputeManager()
+    seen = {}
+
+    def fake_run(*args, **kwargs):
+        seen.update(kwargs)
+        return _EMPTY_REPORT
+
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)
+
+    manager.trigger(*_trigger_args(tmp_path, store))
+    _wait_for_terminal(manager)
+
+    workers = seen.get("workers")
+    assert workers is None or workers <= 1
+    manager.join_all(timeout=5)
+
+
+def test_trigger_resumability_end_to_end_via_a_real_sub_cache(tmp_path, store):
+    """TC-11 (manager resumability wiring, end to end — NOT monkeypatched this time, the real
+    ``run_strategy_comparison_report``): ``trigger()`` completing once over a real, non-degenerate
+    2-eligible-pair-strategy fixture (via an injected ``sub_cache``) publishes durable rows for
+    every pair; a SECOND ``trigger()`` call over the SAME dataset/bar stores and the SAME
+    ``sub_cache`` (``force=True``, bypassing the now-warm WHOLE-report cache so the compute genuinely
+    re-enters) resolves with ``backtests_from_cache > 0`` — proving ``trigger()`` genuinely threads
+    a REAL cache through to ``run_strategy_comparison_report``, not the ``None`` default (which
+    would leave ``backtests_from_cache`` permanently 0, as J-04 shipped it)."""
+    from app.research.bars import BarStore
+    from app.research.datasets import DatasetStore, SPLIT_TRAIN
+    from app.research.edge_report_backtest_cache import EdgeReportBacktestCache
+    from test_edge_report import _record_v1_arming_dataset
+    from test_setups import _seed_full, _syn_config
+
+    config = _syn_config()
+    bar_store = BarStore(tmp_path / "bars")
+    _seed_full(bar_store)
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))
+
+    manager = EdgeReportComputeManager()
+    manager.trigger(store, dataset_store, bar_store, config, cache, sub_cache=sub_cache)
+    first_snap = _wait_for_terminal(manager)
+    assert first_snap["state"] == "done"
+    assert first_snap["progress"]["backtests_from_cache"] == 0  # cold -- nothing cached yet
+    manager.join_all(timeout=5)
+
+    manager.trigger(store, dataset_store, bar_store, config, cache, force=True, sub_cache=sub_cache)
+    second_snap = _wait_for_terminal(manager)
+
+    assert second_snap["state"] == "done"
+    assert second_snap["progress"]["backtests_from_cache"] > 0
+    manager.join_all(timeout=5)
+
+
 def test_cancel_while_idle_is_a_harmless_no_op_the_route_owns_the_409():
     """The manager itself never raises on an idle cancel -- ``cancel_edge_report_compute`` (the
     ROUTE) is the one that checks idle-vs-running and raises the 409, mirroring
@@ -319,6 +426,10 @@ def _set_cli_env(monkeypatch, tmp_path):
     # The explicit override keeps every CLI test hermetic, exactly like every other test in this
     # suite that touches a cache.
     monkeypatch.setenv("TAPEOLOGY_EDGE_REPORT_CACHE_DB", str(tmp_path / "edge_report_cache.db"))
+    # era-fast_wall J-05: the SAME hazard/fix, for the NEW per-pair sub-cache the CLI's main() now
+    # ALSO constructs (resolve_backtest_cache_db_path's own env-else-sibling-of-dataset-dir default
+    # would otherwise ALSO land beside the committed fixture dir).
+    monkeypatch.setenv("TAPEOLOGY_EDGE_SWEEP_CACHE_DB", str(tmp_path / "edge_report_backtests.db"))
 
 
 def test_cli_completes_on_the_fixture_and_a_subsequent_get_path_serves_it_byte_identically(
@@ -411,15 +522,129 @@ def test_cli_out_flag_writes_the_report_json(tmp_path, monkeypatch):
     assert payload["holdout"]["cells"] == []
 
 
-def test_cli_workers_flag_is_accepted_and_inert_this_iteration(tmp_path, monkeypatch):
-    """The CLI's own usage string documents ``--workers N`` (goal.md's J-04 step 3); this
-    iteration's IN SCOPE / OUT OF SCOPE explicitly logs it as accepted-but-inert (J-05 gives it
-    real effect) -- a non-default value must still exit 0 and change nothing observable."""
+def test_cli_workers_flag_on_a_zero_eligible_fixture_still_exits_zero_and_changes_nothing(
+    tmp_path, monkeypatch
+):
+    """The CLI's own usage string documents ``--workers N`` (goal.md's J-04 step 3); era-fast_wall
+    J-05 gives it real effect, but the committed ``datasets_j03`` fixture (symbol PG, not a
+    config-owned panel symbol) always resolves ZERO eligible pairs under the real ``CONFIG`` --
+    ``--workers 2`` must still exit 0 and produce the SAME honest empty report, since
+    ``_parallel_prewarm_sub_cache`` never spins up a process pool with nothing to submit (see
+    ``test_edge_report.py``'s own
+    ``test_parallel_prewarm_with_zero_eligible_datasets_never_spins_up_a_process_pool`` for that
+    guarantee proven directly). The GENUINE multi-process, non-degenerate proof (real worker pids,
+    byte-identical parallel-vs-sequential reports) lives in ``test_edge_report.py``'s
+    ``test_parallel_prewarm_uses_at_least_two_distinct_worker_processes_and_reassembles_byte_
+    identically`` -- this CLI-level test is deliberately the FAST, degenerate-fixture sanity leg."""
     _set_cli_env(monkeypatch, tmp_path)
     monkeypatch.setattr(sys, "argv", ["edge_report_compute", "--workers", "2"])
     assert edge_report_compute.main() == 0
 
 
+def test_cli_workers_default_reads_the_env_override(tmp_path, monkeypatch):
+    """``--workers``'s default is read from ``TAPEOLOGY_EDGE_SWEEP_WORKERS`` if set, else the
+    ``_DEFAULT_WORKERS = 4`` constant -- proven via a kwarg-capturing spy on ``run_strategy_
+    comparison_report`` rather than any observable side effect (the degenerate fixture makes every
+    ``workers`` value behaviorally silent)."""
+    _set_cli_env(monkeypatch, tmp_path)
+    monkeypatch.setenv("TAPEOLOGY_EDGE_SWEEP_WORKERS", "6")
+    seen = {}
+    real = edge_report_compute.run_strategy_comparison_report
+
+    def _spy(*args, **kwargs):
+        seen.update(kwargs)
+        return real(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", _spy)
+    monkeypatch.setattr(sys, "argv", ["edge_report_compute"])  # no --workers flag at all
+
+    assert edge_report_compute.main() == 0
+    assert seen["workers"] == 6
+
+
+def test_cli_workers_and_sub_cache_are_wired_into_run_strategy_comparison_report(tmp_path, monkeypatch):
+    """era-fast_wall J-05: the CLI's ``main()`` wires BOTH a real ``EdgeReportBacktestCache`` and
+    the resolved ``--workers`` int into ``run_strategy_comparison_report`` -- a kwarg-capturing
+    spy (the ``test_force_flag_is_threaded_through...`` precedent, applied to the two NEW hooks),
+    proving neither is silently dropped or left at its old J-04 placeholder."""
+    from app.research.edge_report_backtest_cache import EdgeReportBacktestCache
+
+    _set_cli_env(monkeypatch, tmp_path)
+    seen = {}
+    real = edge_report_compute.run_strategy_comparison_report
+
+    def _spy(*args, **kwargs):
+        seen.update(kwargs)
+        return real(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", _spy)
+    monkeypatch.setattr(sys, "argv", ["edge_report_compute", "--workers", "2"])
+
+    assert edge_report_compute.main() == 0
+
+    assert seen["workers"] == 2
+    assert isinstance(seen["sub_cache"], EdgeReportBacktestCache)
+
+
+def test_cli_published_sub_cache_rows_are_reused_by_a_subsequent_bare_call_with_zero_fresh_backtests(
+    tmp_path, monkeypatch,
+):
+    """TC-10 (non-vacuous): runs the CLI warmer against a genuinely NON-degenerate scan fixture
+    (``edge_report_compute.CONFIG`` monkeypatched to the SAME panel-scoped synthetic config
+    ``test_edge_report.py``'s own synthetic-scan-join tests use — the exact mechanism this file's
+    own manager tests already use, e.g. ``fake_run`` swaps — applied here to the module's imported
+    ``CONFIG`` name instead of a whole function), then proves a SUBSEQUENT bare
+    ``run_strategy_comparison_report(..., sub_cache=<the same cache>)`` call serves 100% cache
+    hits — zero fresh ``_run_backtest`` calls."""
+    from app.research.bars import BarStore
+    from app.research.datasets import DatasetStore, SPLIT_TRAIN
+    from app.research.edge_report_backtest_cache import EdgeReportBacktestCache
+    from app.research import edge_report as edge_report_module
+    from test_edge_report import _record_v1_arming_dataset
+    from test_setups import _seed_full, _syn_config
+
+    test_config = _syn_config()
+    monkeypatch.setattr(edge_report_compute, "CONFIG", test_config)
+
+    bar_dir = tmp_path / "bars"
+    dataset_dir = tmp_path / "datasets"
+    bar_store = BarStore(bar_dir)
+    _seed_full(bar_store)
+    dataset_store = DatasetStore(dataset_dir)
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+
+    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(dataset_dir))
+    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(bar_dir))
+    monkeypatch.setenv("TAPEOLOGY_EDGE_REPORT_CACHE_DB", str(tmp_path / "cache.db"))
+    sub_cache_db = str(tmp_path / "sub-cache.db")
+    monkeypatch.setenv("TAPEOLOGY_EDGE_SWEEP_CACHE_DB", sub_cache_db)
+    monkeypatch.setattr(sys, "argv", ["edge_report_compute", "--workers", "1"])
+
+    assert edge_report_compute.main() == 0
+
+    sub_cache = EdgeReportBacktestCache(sub_cache_db)
+    calls = []
+    real_run_backtest = edge_report_module._run_backtest
+
+    def _counting_run_backtest(*args, **kwargs):
+        calls.append(1)
+        return real_run_backtest(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report_module, "_run_backtest", _counting_run_backtest)
+
+    served_store = JournalStore(str(tmp_path / "served-journal.db"), test_config)
+    try:
+        served = edge_report_module.run_strategy_comparison_report(
+            served_store, dataset_store, bar_store, test_config, sub_cache=sub_cache,
+        )
+    finally:
+        served_store.close()
+
+    assert calls == []  # zero fresh backtests -- entirely served from the CLI-published cache
+    assert len(served["train"]["cells"]) == 3  # non-degenerate: the real 3-cell shape
+
+
 def test_cli_missing_dataset_dir_env_falls_back_to_default_seams_without_crashing(tmp_path, monkeypatch):
     """A malformed/absent dataset dir env resolves to the config default (never crashes at
     argument-parsing time) -- exercised here by simply confirming the parser accepts a bare
diff --git a/apps/backend/app/research/edge_report_backtest_cache.py b/apps/backend/app/research/edge_report_backtest_cache.py
new file mode 100644
index 0000000..560b75e
--- /dev/null
+++ b/apps/backend/app/research/edge_report_backtest_cache.py
@@ -0,0 +1,207 @@
+"""``EdgeReportBacktestCache`` (era-fast_wall J-05) — a durable, rebuildable SQLite cache of ONE
+row per (dataset x strategy) backtest PAIR: the per-pair ``result`` block ``edge_report.py``'s
+``_split_cells`` loop pools into cells, cached BESIDE the whole-REPORT ``EdgeReportCache``
+(``edge_report_cache.py``, untouched) rather than instead of it. Makes the 3-way sweep genuinely
+RESUMABLE (a killed-and-retriggered run skips every already-published pair) and safely
+PARALLELIZABLE (many worker PROCESSES publish concurrently; each publish is one atomic SQLite
+transaction, safe under WAL + busy_timeout).
+
+THIS MODULE stores a REBUILDABLE RESULT ONLY and OWNS NOTHING — the identical ``EdgeReportCache``/
+``bar_index.py`` discipline (see ``edge_report_cache.py``'s own module docstring), applied to a
+per-PAIR row instead of a whole-report row: ``edge_report.py`` stays the SOLE computer of a pair's
+``result`` (via ``_run_backtest``, unchanged); a cache miss always recomputes byte-identically
+through that ONE function. Deleting the persisted DB file loses nothing and fabricates nothing —
+the very next sweep simply re-runs every pair's backtest and republishes it.
+
+**Durable-only — no in-process hot slot.** Unlike ``EdgeReportCache`` (one key per WHOLE report,
+so a hot in-process slot serves REPEATED reads of the SAME report cheaply), a single sweep touches
+MANY DISTINCT pair keys in sequence and never the SAME key twice within one run — an instance-
+scoped single-slot fast path would never actually serve a hit inside one sweep, so this class stays
+exactly as large as its job needs to be (the developer-agent "no abstraction until it earns its
+keep" discipline). Every read/write opens its OWN short-lived connection (the
+``JournalStore._read_conn`` precedent, mirrored by ``EdgeReportCache`` too) — safe across MANY
+worker PROCESSES (not merely threads) publishing concurrently, since each process holds no
+long-lived shared connection object to begin with.
+
+**Key — eight parts, sha256 of canonical JSON (goal.md's own named shape).** ``dataset_id``,
+``dataset_checksum``, ``strategy_id``, ``profile``, ``config_fingerprint``, ``config_content_hash``,
+``strategy_registry``, ``bar_store_signature``. The bar-store term is REQUIRED (not merely one more
+component among equals): the structure strategies (``structure_tape``/``structure_tape_map``) read
+bar content per event, so a bar-series change must bust every pair that reads bars, and the
+EXISTING persisted backtest journal rows are NOT a safe resume source precisely because their own
+``config_fingerprint`` excludes the ``sr_*``/``tradability_*``/``setups_*`` families and records no
+bar content at all (goal.md's own words) — never consulted here. ``pair_cache_key`` accepts every
+component as an explicit literal (never derived internally from an opaque ``Config``/``BarStore``
+object) so each of the eight can be independently varied and tested — the REAL caller
+(``edge_report._build_caching_run_pair``) derives ``config_fingerprint``/``config_content_hash``/
+``strategy_registry``/``bar_store_signature`` from the SAME ``Config``/``BarStore`` ONCE per sweep
+(never once per pair) and closes over them; this function itself stays a pure function of its eight
+named inputs alone. Reuses ``edge_report_cache.py``'s ``_canonical``/``_config_content_hash``
+VERBATIM (never re-derived a second time) — the identical byte-stable canonical-JSON hashing idiom.
+
+**Values stored WITHOUT ``sort_keys``** — the ``EdgeReportCache._insert`` byte-identity discipline
+(see that method's own docstring for the full "why"), applied to a per-pair row: a pair's cached
+``result`` block, once round-tripped through this cache, must be usable identically to a freshly
+computed one wherever a caller inspects its fields.
+
+**Error handling — never a crash, an accelerator's own failure never blocks the sweep.** Every
+method independently guards against ``sqlite3.Error`` (covering both connection/pragma failures
+and query failures against a corrupted/unreadable DB file): ``lookup`` treats any such failure as a
+full miss (``None``, forcing a fresh compute through the caller's own canonical path); ``publish``
+SWALLOWS any such failure entirely (never raises) — the ``setups_scan_cache.py`` "publish failures
+swallowed, an accelerator never blocks serving" discipline (goal.md's own wording for a sibling
+cache), applied uniformly here regardless of caller (both the sequential ``run_pair`` closure and
+every parallel worker process call this SAME method): the sweep's own correctness never depends on
+every pair's cache write succeeding — a lost row merely costs one recompute on the next sweep.
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
+from .edge_report_cache import _canonical, _config_content_hash
+
+__all__ = ["EdgeReportBacktestCache", "pair_cache_key", "resolve_backtest_cache_db_path"]
+
+# A DIFFERENT env var from EdgeReportCache's own TAPEOLOGY_EDGE_REPORT_CACHE_DB — the two durable
+# caches never collide, never share a path, never share a table.
+_CACHE_DB_ENV = "TAPEOLOGY_EDGE_SWEEP_CACHE_DB"
+
+# Mirrors edge_report_cache.py's identical brief writer-contention tolerance.
+_BUSY_TIMEOUT_MS = 5000
+
+_SCHEMA = """
+CREATE TABLE IF NOT EXISTS edge_report_backtest_cache (
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
+def pair_cache_key(
+    *,
+    dataset_id: str,
+    dataset_checksum: str,
+    strategy_id: str,
+    profile: str,
+    config_fingerprint: str,
+    config_content_hash: str,
+    strategy_registry: list[dict],
+    bar_store_signature: tuple,
+) -> str:
+    """The full eight-part key material for ONE (dataset x strategy) backtest pair — sha256 of the
+    canonical JSON of every component (see module docstring). A pure function of its eight named
+    inputs alone: every component is independently controllable, so mutating exactly one (holding
+    the other seven fixed) always yields a different key — see
+    ``tests/test_edge_report_backtest_cache.py``'s key-busting matrix for the non-vacuous proof."""
+    payload = {
+        "dataset_id": dataset_id,
+        "dataset_checksum": dataset_checksum,
+        "strategy_id": strategy_id,
+        "profile": profile,
+        "config_fingerprint": config_fingerprint,
+        "config_content_hash": config_content_hash,
+        "strategy_registry": strategy_registry,
+        "bar_store_signature": list(bar_store_signature),
+    }
+    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
+
+
+def resolve_backtest_cache_db_path(dataset_dir_resolved: str) -> str:
+    """The sub-cache DB path resolution policy — mirrors ``edge_report_cache.resolve_cache_db_path``
+    exactly (env-else-sibling-of-the-dataset-dir), for a DIFFERENT env var and a DIFFERENT sibling
+    filename, so the two durable caches never collide: the ``TAPEOLOGY_EDGE_SWEEP_CACHE_DB`` env
+    var if set, else ``edge_report_backtests.db`` co-located beside the caller's own resolved
+    dataset directory (the SAME ``.data/`` directory ``edge_report_cache.db`` already lives in)."""
+    override = os.environ.get(_CACHE_DB_ENV)
+    if override:
+        return override
+    return os.path.join(os.path.dirname(dataset_dir_resolved), "edge_report_backtests.db")
+
+
+class EdgeReportBacktestCache:
+    """One durable SQLite row per (dataset x strategy) pair's backtest ``result`` block — beside
+    ``EdgeReportCache``, the SAME durable discipline (WAL + busy_timeout, a hermetic dependency-
+    injected DB path), never a modification of that existing whole-report cache. See the module
+    docstring for the full "rebuildable, never a source of truth" contract and the error-handling
+    discipline."""
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
+        long-lived connection shared across threads OR processes)."""
+        conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=_BUSY_TIMEOUT_MS / 1000.0)
+        conn.row_factory = sqlite3.Row
+        conn.execute("PRAGMA journal_mode=WAL")
+        conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
+        return conn
+
+    def lookup(self, key: str) -> dict | None:
+        """The durable row for ``key``, or ``None`` on a genuine miss — NEVER computes (there is no
+        ``compute_fn`` parameter; a miss is mechanically incapable of running a backtest). A
+        corrupted/unreadable DB is treated as a full miss, never a crash (module docstring)."""
+        try:
+            conn = self._connect()
+            try:
+                row = conn.execute(
+                    "SELECT result_json FROM edge_report_backtest_cache WHERE cache_key=?", (key,)
+                ).fetchone()
+            finally:
+                conn.close()
+        except sqlite3.Error:
+            return None
+        return None if row is None else json.loads(row["result_json"])
+
+    def publish(self, key: str, result: dict) -> None:
+        """Durably persist ONE pair's ``result`` block — one atomic ``INSERT OR REPLACE``
+        transaction (safe across many worker PROCESSES publishing concurrently; WAL + busy_timeout
+        tolerate brief writer contention). Stored WITHOUT ``sort_keys`` (see module docstring). A
+        publish failure of ANY kind is SWALLOWED here, never propagated (module docstring) — never
+        blocks the sweep that is still holding this pair's own already-computed ``result``."""
+        try:
+            conn = self._connect()
+            try:
+                with conn:
+                    conn.execute(
+                        "INSERT OR REPLACE INTO edge_report_backtest_cache "
+                        "(cache_key, result_json, created_utc) VALUES (?,?,?)",
+                        (key, json.dumps(result), _iso_utc_now()),
+                    )
+            finally:
+                conn.close()
+        except sqlite3.Error:
+            pass
diff --git a/apps/backend/tests/test_edge_report_backtest_cache.py b/apps/backend/tests/test_edge_report_backtest_cache.py
new file mode 100644
index 0000000..0299c72
--- /dev/null
+++ b/apps/backend/tests/test_edge_report_backtest_cache.py
@@ -0,0 +1,314 @@
+"""``EdgeReportBacktestCache`` (era-fast_wall J-05) — store-level discipline, tested standalone (no
+FastAPI, no real backtests). Mirrors ``tests/test_edge_report_cache.py``'s own directness: every
+test here feeds the cache a CHEAP counting stub instead of a real ``_run_backtest`` call — the
+cache mechanics (keying, durability, concurrency, corrupted-DB tolerance) are independent of what a
+real backtest actually computes, so proving them against a fast stub is both faster and a purer
+isolation than routing every case through a real multi-strategy sweep. The WIRING into
+``edge_report.py`` (byte-identity, kill-and-resume, new-dataset-costs-three, parallel equivalence)
+is covered separately in ``tests/test_edge_report.py``; the CLI/manager wiring is covered in
+``tests/test_edge_report_compute.py``.
+"""
+
+from __future__ import annotations
+
+import json
+import sqlite3
+import threading
+
+from app.research.edge_report_backtest_cache import (
+    EdgeReportBacktestCache,
+    pair_cache_key,
+    resolve_backtest_cache_db_path,
+)
+
+
+def _base_kwargs() -> dict:
+    return dict(
+        dataset_id="ds-1",
+        dataset_checksum="checksum-1",
+        strategy_id="v1",
+        profile="default",
+        config_fingerprint="fp-1",
+        config_content_hash="hash-1",
+        strategy_registry=[{"id": "v1"}],
+        bar_store_signature=(("AAPL", "5m", "series-1", "chk-1"),),
+    )
+
+
+# One replacement value per key component — used both to prove the key CHANGES (pure function)
+# and to prove a call-counting spy sees a fresh call for EVERY one of the eight (TC-5).
+_MUTATIONS: dict[str, object] = {
+    "dataset_id": "ds-2",
+    "dataset_checksum": "checksum-2",
+    "strategy_id": "structure_tape",
+    "profile": "candidate",
+    "config_fingerprint": "fp-2",
+    "config_content_hash": "hash-2",
+    "strategy_registry": [{"id": "v1"}, {"id": "structure_tape"}],
+    "bar_store_signature": (("AAPL", "5m", "series-2", "chk-2"),),
+}
+
+
+# --- pair_cache_key: a pure function, non-vacuous key-busting matrix (TC-5) -----------------------
+
+
+def test_pair_cache_key_is_stable_for_identical_inputs():
+    assert pair_cache_key(**_base_kwargs()) == pair_cache_key(**_base_kwargs())
+
+
+def test_pair_cache_key_changes_when_any_one_of_the_eight_components_changes():
+    base_key = pair_cache_key(**_base_kwargs())
+    for component, new_value in _MUTATIONS.items():
+        mutated = _base_kwargs()
+        mutated[component] = new_value
+        mutated_key = pair_cache_key(**mutated)
+        assert mutated_key != base_key, f"mutating {component!r} alone must change the key"
+
+
+def test_pair_cache_key_mutations_are_all_pairwise_distinct():
+    """A stronger non-vacuous guard than base-vs-mutated alone: no two DIFFERENT single-component
+    mutations may collide with each other either (would silently mean two distinct pairs share one
+    cached row)."""
+    keys = [pair_cache_key(**_base_kwargs())]
+    for component, new_value in _MUTATIONS.items():
+        mutated = _base_kwargs()
+        mutated[component] = new_value
+        keys.append(pair_cache_key(**mutated))
+    assert len(keys) == len(set(keys)), "every one of the 9 scenarios must produce a distinct key"
+
+
+class _CountingBacktest:
+    """A stub standing in for ``edge_report._run_backtest`` (mirrors ``test_edge_report_cache.py``'s
+    own ``_CountingCompute`` precedent) — proving the CACHE's mechanics against a cheap stub,
+    independent of what a real backtest actually computes."""
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
+    """TC-5, non-vacuous: a warm row for the base pair, then EACH of the eight components mutated
+    in turn (holding the other seven fixed) forces a fresh 'backtest' call — proving each component
+    independently busts the key (a cache silently ignoring one component would fail exactly that
+    row)."""
+    cache = EdgeReportBacktestCache(str(tmp_path / "sub_cache.db"))
+    compute = _CountingBacktest()
+
+    def _lookup_or_compute(kwargs: dict) -> dict:
+        key = pair_cache_key(**kwargs)
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
+        _lookup_or_compute(mutated)  # a second request for the SAME mutated pair -- must NOT recompute
+        assert compute.calls == expected_calls
+
+
+# --- lookup / publish mechanics -------------------------------------------------------------------
+
+
+def test_cold_lookup_is_none(tmp_path):
+    cache = EdgeReportBacktestCache(str(tmp_path / "cache.db"))
+    assert cache.lookup(pair_cache_key(**_base_kwargs())) is None
+
+
+def test_publish_then_lookup_returns_the_result_verbatim(tmp_path):
+    cache = EdgeReportBacktestCache(str(tmp_path / "cache.db"))
+    key = pair_cache_key(**_base_kwargs())
+    result = {"trades": [{"a": 1}], "aggregates": {"net_r": 1.5}}
+
+    cache.publish(key, result)
+
+    assert cache.lookup(key) == result
+
+
+def test_result_round_trips_byte_identically_through_json_persistence(tmp_path):
+    """Floats, nested lists/dicts, and ``None`` all survive a JSON round-trip through the durable
+    layer byte-identically (structural equality on the round-tripped dict)."""
+    cache = EdgeReportBacktestCache(str(tmp_path / "cache.db"))
+    key = pair_cache_key(**_base_kwargs())
+    result = {
+        "trades": [{"entry": {"price": 100.245, "logical_ts": 19.5}, "exit": None}],
+        "aggregates": {"net_r": -0.16000000000001136, "n": 1, "win_rate": None},
+    }
+
+    cache.publish(key, result)
+
+    assert cache.lookup(key) == result
+
+
+def test_second_publish_under_the_same_key_replaces_the_row(tmp_path):
+    cache = EdgeReportBacktestCache(str(tmp_path / "cache.db"))
+    key = pair_cache_key(**_base_kwargs())
+
+    cache.publish(key, {"version": 1})
+    cache.publish(key, {"version": 2})
+
+    assert cache.lookup(key) == {"version": 2}
+
+    conn = sqlite3.connect(str(tmp_path / "cache.db"))
+    try:
+        (count,) = conn.execute(
+            "SELECT COUNT(*) FROM edge_report_backtest_cache WHERE cache_key=?", (key,)
+        ).fetchone()
+    finally:
+        conn.close()
+    assert count == 1  # INSERT OR REPLACE -- never a duplicate row under one key
+
+
+def test_stored_value_is_not_sort_keys_serialized(tmp_path):
+    """The ``EdgeReportCache._insert`` byte-identity discipline, applied here: storage preserves
+    the dict's OWN insertion order rather than alphabetizing it (``json.dumps`` default, never
+    ``sort_keys=True``) — a stored row's raw bytes reflect the caller's own field order."""
+    cache = EdgeReportBacktestCache(str(tmp_path / "cache.db"))
+    key = pair_cache_key(**_base_kwargs())
+    # A dict whose insertion order is deliberately NOT alphabetical.
+    result = {"zeta": 1, "alpha": 2, "middle": 3}
+
+    cache.publish(key, result)
+
+    conn = sqlite3.connect(str(tmp_path / "cache.db"))
+    try:
+        (raw,) = conn.execute(
+            "SELECT result_json FROM edge_report_backtest_cache WHERE cache_key=?", (key,)
+        ).fetchone()
+    finally:
+        conn.close()
+    assert raw == json.dumps(result)  # NOT json.dumps(result, sort_keys=True)
+
+
+# --- durability across a simulated backend/worker restart -----------------------------------------
+
+
+def test_durability_across_a_simulated_restart_serves_the_prior_row(tmp_path):
+    db_path = str(tmp_path / "cache.db")
+    key = pair_cache_key(**_base_kwargs())
+    original = EdgeReportBacktestCache(db_path)
+    original.publish(key, {"shape": "real"})
+
+    restarted = EdgeReportBacktestCache(db_path)  # a brand-new instance, no in-process state at all
+
+    assert restarted.lookup(key) == {"shape": "real"}
+
+
+def test_deleting_the_db_file_is_harmless_a_fresh_instance_starts_cold(tmp_path):
+    db_path = tmp_path / "cache.db"
+    key = pair_cache_key(**_base_kwargs())
+    cache = EdgeReportBacktestCache(str(db_path))
+    cache.publish(key, {"shape": "real"})
+    assert cache.lookup(key) == {"shape": "real"}
+
+    for suffix in ("", "-wal", "-shm"):
+        sidecar = db_path.parent / (db_path.name + suffix)
+        if sidecar.exists():
+            sidecar.unlink()
+
+    fresh = EdgeReportBacktestCache(str(db_path))
+    assert fresh.lookup(key) is None  # loses nothing it shouldn't -- an honest cold miss
+
+
+# --- error handling: never a crash, never blocks the sweep (goal.md's own error-cases clause) -----
+
+
+def test_construction_against_a_corrupted_file_never_raises(tmp_path):
+    db_path = tmp_path / "garbage.db"
+    db_path.write_bytes(b"not a real sqlite file, just garbage bytes " * 20)
+
+    EdgeReportBacktestCache(str(db_path))  # must not raise
+
+
+def test_lookup_on_a_corrupted_db_file_returns_none_never_crashes(tmp_path):
+    db_path = tmp_path / "garbage.db"
+    db_path.write_bytes(b"not a real sqlite file, just garbage bytes " * 20)
+    cache = EdgeReportBacktestCache(str(db_path))
+
+    assert cache.lookup("any-key") is None
+
+
+def test_publish_on_a_corrupted_db_file_is_swallowed_never_crashes(tmp_path):
+    db_path = tmp_path / "garbage.db"
+    db_path.write_bytes(b"not a real sqlite file, just garbage bytes " * 20)
+    cache = EdgeReportBacktestCache(str(db_path))
+
+    cache.publish("some-key", {"n": 1})  # must not raise, whether or not it actually persisted
+
+
+# --- concurrency: many THREADS publishing distinct keys never crash or corrupt each other ---------
+# (Mirrors test_edge_report_cache.py's own concurrency test shape — the genuine multi-PROCESS
+# proof, via a real ProcessPoolExecutor, lives in test_edge_report.py's parallel-sweep test, since
+# it needs the real _run_backtest/dataset/bar-store machinery this module intentionally stays
+# ignorant of.)
+
+
+def test_many_threads_publishing_distinct_keys_concurrently_never_lose_or_corrupt_a_row(tmp_path):
+    cache = EdgeReportBacktestCache(str(tmp_path / "cache.db"))
+    n_threads = 16
+
+    def _publish_one(i: int) -> None:
+        kwargs = _base_kwargs()
+        kwargs["dataset_id"] = f"ds-{i}"
+        key = pair_cache_key(**kwargs)
+        cache.publish(key, {"i": i})
+
+    threads = [threading.Thread(target=_publish_one, args=(i,)) for i in range(n_threads)]
+    for t in threads:
+        t.start()
+    for t in threads:
+        t.join(timeout=10)
+
+    for i in range(n_threads):
+        kwargs = _base_kwargs()
+        kwargs["dataset_id"] = f"ds-{i}"
+        key = pair_cache_key(**kwargs)
+        assert cache.lookup(key) == {"i": i}
+
+
+# --- resolve_backtest_cache_db_path: env-else-sibling-of-dataset-dir (mirrors resolve_cache_db_path)
+
+
+def test_resolve_backtest_cache_db_path_defaults_to_a_sibling_of_the_dataset_dir(tmp_path, monkeypatch):
+    monkeypatch.delenv("TAPEOLOGY_EDGE_SWEEP_CACHE_DB", raising=False)
+    dataset_dir = str(tmp_path / "datasets")
+
+    resolved = resolve_backtest_cache_db_path(dataset_dir)
+
+    assert resolved == str(tmp_path / "edge_report_backtests.db")
+
+
+def test_resolve_backtest_cache_db_path_honors_the_env_override(tmp_path, monkeypatch):
+    override = str(tmp_path / "custom" / "sub_cache.db")
+    monkeypatch.setenv("TAPEOLOGY_EDGE_SWEEP_CACHE_DB", override)
+
+    resolved = resolve_backtest_cache_db_path(str(tmp_path / "datasets"))
+
+    assert resolved == override
+
+
+def test_resolve_backtest_cache_db_path_never_collides_with_the_whole_report_cache_path(tmp_path, monkeypatch):
+    """The two durable caches must resolve to DIFFERENT default sibling filenames — a real
+    regression this test would catch (accidentally reusing edge_report_cache.py's own filename)."""
+    monkeypatch.delenv("TAPEOLOGY_EDGE_SWEEP_CACHE_DB", raising=False)
+    monkeypatch.delenv("TAPEOLOGY_EDGE_REPORT_CACHE_DB", raising=False)
+    from app.research.edge_report_cache import resolve_cache_db_path
+
+    dataset_dir = str(tmp_path / "datasets")
+    assert resolve_backtest_cache_db_path(dataset_dir) != resolve_cache_db_path(dataset_dir)
```
