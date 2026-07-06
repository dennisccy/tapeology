# Iteration diff (bounded)

Files changed: 33. Shown in full: 23.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `reports/goal-session-tape_to_profit_support_resistence-index.html` (47 diff lines)
- `reports/phase-goal-tape_to_profit_support_resistence-iter-5-iteration-summary.md` (78 diff lines)
- `reports/phase-goal-tape_to_profit_support_resistence-iter-5-summary.html` (42 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/iter-6/.steps/decomposer.done` (7 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/iter-6/goal-slice.md` (273 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/iter-6/snapshot-sha` (8 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/state/project-story.md` (27 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/telemetry.jsonl` (22 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/trace/trace.jsonl` (20 diff lines)

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `diff --git areports/qa/goal-tape_to_profit_support_resistence-iter-6-test-plan.md breports/qa/goal-tape_to_profit_support_resistence-iter-6-test-plan.md` (89 lines not shown)

```diff
diff --git a/README.md b/README.md
index 5757b63..a70fb84 100644
--- a/README.md
+++ b/README.md
@@ -66,12 +66,13 @@ Current capabilities:
 - **Deterministic strategy backtesting (research API)** — run a rules-based trading strategy against a registered historical dataset and get back a full report: simulated per-trade entries and exits (fees and slippage applied), aggregate results (net and gross return in both R-multiples and dollars, win rate, maximum drawdown, and trade count), and a seeded random-entry baseline computed on the same data so a result is always judged against fair chance rather than in isolation. Every report is stamped with exactly which dataset, strategy, and indicator configuration produced it, and re-running the identical request reproduces a byte-identical report. Results always carry an explicit "simulated" label and are never shown as a profit forecast, an edge claim, or a reason to trade. Runs as a cancellable background job, the same pattern as a replay study. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
 - **Versioned indicator profiles (research API)** — a config-owned registry of named indicator configurations: the frozen `default` profile that the live cockpit and every other feature always run on, proven byte-identical against pinned reference outputs, plus one additive candidate profile that adjusts an engine feature threshold. A candidate can only be selected when running a backtest — never by the live cockpit or any other surface — to compare a hypothetical adjustment against `default` on the same historical data; requesting an unregistered profile is refused with a message listing the valid ids. Every backtest and PnL-ledger row is stamped with exactly which profile produced it. The full registry — each entry flagged frozen/candidate and default/alternate — is visible on the Performance page alongside the current champion strategy and indicator profile.
 - **PnL ledger (research API)** — an append-only, honest record of profit-and-loss for the trading strategy after every enhancement to it: one row per enhancement recording net return in both R-multiples and dollars on the train and hold-out data splits, kept separate and never pooled, each with its own trade count and full provenance (which dataset, strategy, and indicator configuration produced it) and a timestamp; rows can never be updated or deleted once written. The founding baseline row is already recorded, with splits below the minimum trade count honestly labeled "insufficient sample" rather than shown as a real result. A committed markdown report renders the same rows verbatim, matching the REST API and the machine-readable tool exactly. It is rendered in full on the Performance page in the browser, and is also reachable through the research API and the matching machine-readable tool.
-- **Candidate validation sweep (command-line research tool)** — checks every registered candidate strategy or indicator profile against the current champion: first how it performs on the training data, then — only if it looks better there — whether that win holds up on a hold-out set it was never tuned on. A candidate is promoted only when it genuinely beats the champion on that untouched hold-out data with enough trades to trust the result; a promotion appends one honest row to the PnL ledger and moves the champion, so the Performance page and the machine-readable connection reflect it immediately. Safe to run at any time — with nothing worth promoting, it changes nothing and reports that honestly rather than forcing a result.
+- **Candidate validation sweep (command-line research tool)** — checks every registered candidate indicator profile against the current champion, or — given a named strategy on the command line — checks ONE named candidate trading strategy (such as `structure_tape`) against the champion strategy instead, on the same terms: first how it performs on the training data, then — only if it looks better there — whether that win holds up on a hold-out set it was never tuned on. A candidate is promoted only when it genuinely beats the champion on that untouched hold-out data with enough trades to trust the result; a promotion appends one honest row to the PnL ledger and moves the champion (to the new strategy, or the new profile, whichever was being checked), so the Performance page and the machine-readable connection reflect it immediately. Every report also discloses a known measurement caveat for the structure strategy's "follow-through" reading, which is a looser check than a strict instant-by-instant crossing test — disclosed plainly rather than silently tightened. Safe to run at any time — with nothing worth promoting, it changes nothing and reports that honestly rather than forcing a result. Checked today against the committed sample data, `structure_tape` honestly turns up too few hold-out trades to trust a result yet — no promotion, champion unchanged — exactly the "not enough evidence either way" finding this tool exists to surface rather than paper over.
 - **Baseline-edge report (command-line research tool)** — measures the current champion strategy across every dataset ever recorded, then ranks the results best-to-worst separately within the training data and within the held-out data (the two are never mixed together). Each dataset's result is shown in R-multiples and dollars, with its trade count, beside a random-entry comparison line. A dataset only earns a "positive edge" mark on its held-out side, and only when the result is genuinely profitable, has enough trades to trust, and beats the random comparison — not merely because the sign looks favorable. When nothing clears that bar — including when no datasets have been recorded yet — the report says so plainly ("no positive-edge dataset") instead of manufacturing a favorable result; it changes nothing else in the product (no promotion, no ledger write, no champion change) and produces a byte-identical report on repeated runs.
 - **Performance page** — a fourth top-level page (reachable from the top navigation bar on every page) renders the profit-and-loss ledger and the current champion strategy and indicator profile verbatim from their canonical endpoints — nothing is recalculated or rounded for display. Each ledger row shows net return in both R-multiples and dollars for the train and hold-out splits, kept strictly separate with their own trade counts; a split with too few trades to draw a conclusion from is labeled "insufficient sample" rather than shown as a real result, and a missing prior baseline (the founding row) is shown as explicitly absent rather than a fabricated zero. Every figure carries the same "simulated — assumed fees/slippage — not indicative of live results" register used elsewhere in the product.
 - **Multi-timeframe historical bar store (research API)** — record a real historical OHLC (open/high/low/close) price-bar series for a symbol at daily, weekly, monthly, hourly, and other calendar timeframes, and keep the saved copy — its symbol, timeframe, exact time window, source feed, and bar count — forever, unchanged. Every recorded series carries two layers of built-in checksums, re-verified on every read; a corrupted file surfaces an explicit error rather than silently serving bad data, and recording the exact same series twice is refused with a message pointing at the original rather than silently duplicating it. Reading a saved series back returns byte-identical results run after run. Missing market-data credentials produce a clear, explicit message rather than invented price data. Watching a ticker in the live cockpit never records a bar series — recording is a separate, explicit research action. A committed fixture proves the full record-then-read round trip with no credentials. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
 - **Support/resistance levels and confluence zones (research API)** — from any recorded bar series, compute the horizontal price levels where a symbol has structurally turned: swing pivots (a bar's high or low that is the extreme among its surrounding neighbours) and prior-period extremes (the prior day/week/month's high, low, or close), each stamped with its timeframe, how it was derived, its touch count, and an overall strength score that weights longer timeframes and more touches higher. Levels that sit close together in price across different timeframes are grouped into a confluence zone carrying a combined strength score and an honest A/B/C conviction class: A when several distinct timeframes agree and at least one is longer-term (daily/weekly/monthly), B when two distinct timeframes agree, and C when the zone only ever shows up within a single timeframe — a grade is never inflated to look more convincing than the evidence supports. Every one of those parameters — pivot lookback, confluence tolerance, and the class thresholds — comes from one central config; nothing is hard-coded, fitted, or invented on the fly. Levels and zones computed "as of" a given time use only bars recorded at or before that moment; a bar recorded later can never change an earlier answer — proven directly by comparing the same query against a store with and without the later bars physically removed, for both levels and zones. Identical requests always return byte-identical results. A symbol with no bar history at all gets an explicitly different message than a symbol that has history but no notable levels or zones yet — the "nothing to show" cases are never conflated. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
 - **Strategy registry and a tape-confirmed structure strategy (research API)** — a named list of the trading strategies a backtest can be run under: the original `v1` strategy, plus an additive second one, `structure_tape`, that only opens a simulated trade where price sits at (or has just moved through) one of the support/resistance levels above AND the live tape agrees — either the tape shows that level being defended (a fade back the other way) or shows real, sustained price impact carrying straight through it (a follow-through in that direction). Every simulated entry records exactly which level — its price, timeframe, and A/B/C conviction class — triggered it, reported with the same simulated return-in-R-and-dollars figures beside the same random-entry comparison every backtest already shows. Registering `structure_tape` never changes the frozen `v1` strategy or any of its past results, and `structure_tape` only ever becomes the shown "champion" strategy through the same honest hold-out comparison every candidate goes through — never automatically. The current registry and today's champion strategy are reachable through the research API and the matching machine-readable tool.
+- **Class-scaled risk, reward, and size for structure_tape, with a per-class PnL breakdown (research API)** — every `structure_tape` simulated trade sets its stop distance, take-profit target, and simulated position size from the A/B/C conviction class of the level it entered at: an A-class level (the strongest cross-timeframe agreement) gets a tight stop (about 1 basis point beyond the level) and the largest simulated size, while B and C levels get progressively wider stops and smaller size. The take-profit target is a class-scaled multiple of the trade's own risk, capped at the next already-detected opposing level rather than an arbitrary distance. Every stop distance, target multiple, and size factor is a named configuration value, never a number buried in code. Backtest reports for any registered strategy show, alongside the existing blended total, a per-class A/B/C breakdown of trade count and net return in both R-multiples and dollars — a strategy that does not use support/resistance levels (such as `v1`) honestly shows all three classes empty rather than omitting the section.
 - **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/levels`, `GET /meta/ui-routes`.
 - **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, journal, studies, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, and navigation data a person sees. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 <!-- /AUTO:capabilities -->
diff --git a/apps/backend/app/research/pnl_scan.py b/apps/backend/app/research/pnl_scan.py
index d950bf6..7b78f4d 100644
--- a/apps/backend/app/research/pnl_scan.py
+++ b/apps/backend/app/research/pnl_scan.py
@@ -77,6 +77,42 @@ Disciplines, clause by clause:
     partial report is a misleading report. A backtest that ends anything other than ``done``
     (e.g. a corrupt dataset caught at replay time) is the same explicit refusal. No trade, fill,
     dataset, or PnL figure is ever synthesized to force a result either way.
+
+era-4 J-06 — the STRATEGY axis (Data Contract row 43, ``structure_tape`` vs ``v1``): an ADDITIVE
+branch alongside the profile axis above, never a refactor of it.
+
+  * **``run_sweep(..., candidate_strategy_id=None)``.** With no named strategy (the default), the
+    profile axis behaves BYTE-IDENTICALLY to before this iteration: exactly one candidate per
+    registered non-default profile, strategy held at the champion's own current ``strategy_id``.
+    Given ``candidate_strategy_id`` (the CLI's ``--strategy``), the sweep instead evaluates EXACTLY
+    ONE candidate — the named strategy — backtest at ``strategy_id=<named>``,
+    ``profile=PROFILE_DEFAULT``, compared against the champion's CURRENT ``strategy_id`` (read
+    verbatim from ``store.get_champion_pointer()`` — never hardcoded ``"v1"``), also at
+    ``profile=PROFILE_DEFAULT``. The two axes never mix: a strategy-axis run holds profile fixed at
+    ``default``; a profile-axis run holds strategy fixed at the champion's own.
+  * **Same machinery, generalized.** ``_dataset_rows`` / ``_split_summary`` / ``_is_positive`` /
+    ``_promote`` are reused VERBATIM — they operate on ``(report_id, result)`` pairs, not on
+    "profile" specifically, so they are already axis-agnostic. A promoted strategy-axis survivor
+    moves the champion pointer to ``strategy_id=<named candidate>``, ``profile=PROFILE_DEFAULT`` —
+    still the ONE pointer, still a pointer write only, never touching ``default``/``v1``/any engine
+    default.
+  * **Unknown candidate strategy id: an explicit refusal, no new validation code.**
+    ``BacktestJobManager.create`` stamps ``strategy_id`` verbatim with no registry check; an
+    unregistered id is caught at RUN time (``BacktestRunner.run`` -> ``strategy_definition`` is
+    ``None`` -> persisted ``failed``, never raised out), which this module's EXISTING
+    ``_run_backtest`` status check already turns into an explicit ``ScanError`` — no new lookup or
+    allowlist needed here.
+  * **``bar_store`` (era-4 J-04's row-39 level source) is threaded through unconditionally**, exactly
+    like ``dataset_store`` — the SAME optional, call-time-only parameter ``BacktestRunner.run``
+    already accepts. ``v1`` ignores it entirely (byte-identical whether ``None`` or a real store),
+    so passing it through the profile axis too is harmless; only a ``structure_tape`` candidate/
+    champion backtest ever reads it, and honestly arms nothing without one (never a fabricated arm).
+  * **Audit B1, disclosed not re-armed.** The returned report's ``provenance.assumptions`` names the
+    ``structure_tape`` breakthrough arm's loose, sanctioned static-price-position anchor (a single
+    at-event position test, not a fresh event-to-event level cross) so a reader can never mistake the
+    reported edge for one measured under a tighter crossing rule. A static, config-independent string
+    — present on every report, on every axis — so it never perturbs the byte-identical-rerun
+    guarantee.
 """
 
 from __future__ import annotations
@@ -87,14 +123,32 @@ import sys
 import time
 from pathlib import Path
 
-from ..config import CONFIG, Config
+from ..config import CONFIG, Config, PROFILE_DEFAULT
 from .backtests import BacktestJobManager, REGISTER, STATUS_DONE
+from .bars import BarStore
 from .datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
 from .pnl_ledger import LedgerCompositionError, append_validation_row
 from .store import DuplicateEnhancementError, JournalStore
 
 __all__ = ["ScanError", "run_sweep", "main"]
 
+# era-4 J-06 (audit item B1, carried from iter-4/iter-5): the structure_tape breakthrough arm
+# confirms via a STATIC price-position test (price already beyond the level at the read instant —
+# the studies' level-cross technique), not a FRESH event-to-event cross of the level. A sanctioned
+# but loose anchor that can inflate the measured breakthrough-arm frequency (and so the reported
+# edge) relative to a tighter crossing rule. Disclosed here rather than tightened: re-arming risks
+# perturbing the frozen J-04/J-05 arming, a second risky change this goal-completing iteration does
+# not make. A static, config-independent string (never wall-clock or per-run-random) so it never
+# perturbs the byte-identical-rerun guarantee.
+BREAKTHROUGH_ANCHOR_CAVEAT = (
+    "the structure_tape breakthrough arm confirms a STATIC price-position test (price already "
+    "beyond the level, read once at the event) rather than a FRESH event-to-event cross of the "
+    "level -- a sanctioned but loose anchor that can inflate the measured breakthrough-arm "
+    "frequency, and so the reported edge, relative to a tighter crossing rule. Disclosed rather "
+    "than tightened this iteration to avoid a second risky change to the frozen J-04/J-05 arming "
+    "(see docs/goal.md iter-6 NOTES, audit item B1)."
+)
+
 
 class ScanError(Exception):
     """The sweep could not complete honestly — a dataset failed integrity verification, a
@@ -113,13 +167,21 @@ def _run_backtest(
     *,
     strategy_id: str,
     profile: str,
+    bar_store: BarStore | None = None,
 ) -> tuple[str, dict]:
     """Run ONE backtest synchronously through the EXISTING public job API (the
     ``pnl_baseline._run_backtest`` pattern) and return ``(report_id, result_block)`` — refusing
     explicitly unless it completed ``done`` (a failed/cancelled report carries no served
-    aggregates, so nothing could be honestly compared against it)."""
+    aggregates, so nothing could be honestly compared against it).
+
+    ``bar_store`` (era-4 J-06) is threaded straight through to ``run_sync`` — the SAME optional,
+    call-time-only parameter the route already passes. ``v1`` ignores it (byte-identical either
+    way); only a ``structure_tape`` run ever reads it, honestly arming nothing without one. An
+    unregistered ``strategy_id`` needs no dedicated check here: ``BacktestRunner.run`` persists it
+    as an explicit ``failed`` record (never raises out), which the status check below already
+    turns into this same explicit ``ScanError``."""
     payload = jobs.create({"dataset_id": dataset_id, "strategy_id": strategy_id, "profile": profile})
-    jobs.run_sync(payload["id"], dataset_store=dataset_store)
+    jobs.run_sync(payload["id"], dataset_store=dataset_store, bar_store=bar_store)
     final = store.get_backtest(payload["id"]).payload
     if final.get("status") != STATUS_DONE:
         raise ScanError(
@@ -207,6 +269,8 @@ def _promote(
     *,
     champion: dict,
     candidate_id: str,
+    new_strategy_id: str,
+    new_profile: str,
     train_datasets: list[dict],
     holdout_datasets: list[dict],
     train_rows: list[dict],
@@ -217,7 +281,13 @@ def _promote(
     docstring). Requires EXACTLY one train and one hold-out dataset registered
     (``append_validation_row``'s structural shape, reused verbatim, never modified); with more of
     either, promotion is explicitly skipped with an honest note — the SCAN still evaluated and
-    reported every dataset."""
+    reported every dataset.
+
+    ``new_strategy_id`` / ``new_profile`` (era-4 J-06) are the exact ``(strategy_id, profile)``
+    pair the winning candidate's OWN backtests ran at — the profile axis passes
+    ``(champion['strategy_id'], candidate_id)`` (unchanged); the strategy axis passes
+    ``(candidate_id, PROFILE_DEFAULT)``. Either way the pointer moves to precisely what was
+    measured — never a third, re-derived pair."""
     if len(train_datasets) != 1 or len(holdout_datasets) != 1:
         return {
             "candidate_id": candidate_id,
@@ -253,28 +323,53 @@ def _promote(
         ) from exc
     # The ledger row is now durably committed — safe to move the pointer. A crash AFTER this
     # point leaves a correctly-attributed ledger row and a moved pointer: fully consistent.
-    store.set_champion_pointer(
-        strategy_id=champion["strategy_id"], profile=candidate_id, wall_ts=time.time()
-    )
+    store.set_champion_pointer(strategy_id=new_strategy_id, profile=new_profile, wall_ts=time.time())
     return {"candidate_id": candidate_id, "promoted": True, "enhancement_id": enhancement_id}
 
 
 # --- the ONE computer of Data Contract row 36 --------------------------------------------------
 
 
-def run_sweep(store: JournalStore, dataset_store: DatasetStore, config: Config) -> dict:
+def run_sweep(
+    store: JournalStore,
+    dataset_store: DatasetStore,
+    config: Config,
+    *,
+    candidate_strategy_id: str | None = None,
+    bar_store: BarStore | None = None,
+) -> dict:
     """Run the full candidate sweep ONCE. Returns the complete report dict — the SAME shape
     persisted to ``--out`` (the CLI is a thin wrapper). A genuine hold-out survivor is promoted
     INLINE (ledger row + champion-pointer move) before this returns, so the returned report
     already reflects the promotion outcome (``champion_after``). Raises ``ScanError`` for a
-    dishonest state — nothing is written, nothing promoted."""
+    dishonest state — nothing is written, nothing promoted.
+
+    ``candidate_strategy_id`` (era-4 J-06, the CLI's ``--strategy``) selects the axis this run
+    varies — an ADDITIVE branch, never a refactor of the other:
+
+      * ``None`` (the default): the PROFILE axis, UNCHANGED from before this iteration — every
+        registered non-default profile, one candidate each, strategy held at the champion's own
+        current ``strategy_id``.
+      * a strategy id: the STRATEGY axis — exactly ONE candidate (the named strategy), backtest at
+        ``strategy_id=candidate_strategy_id``, ``profile=PROFILE_DEFAULT``, compared against the
+        champion's CURRENT ``strategy_id`` (never hardcoded), also at ``profile=PROFILE_DEFAULT``.
+
+    ``bar_store`` (era-4 J-04's row-39 level source) is threaded through every backtest this run
+    makes, on either axis — ``v1`` ignores it; only a ``structure_tape`` run ever reads it."""
     champion = store.get_champion_pointer()
     jobs = BacktestJobManager(store, config)
 
-    # Candidate enumeration reads the ONE registry FIRST: zero registered candidates is an honest
-    # empty sweep, and skipping straight to the report avoids running the champion's own backtests
-    # for nothing (they exist only to be compared against a candidate).
-    candidates = [p for p in config.profile_registry() if not p["is_default"]]
+    if candidate_strategy_id is not None:
+        # STRATEGY axis (era-4 J-06): exactly one named candidate; profile held fixed at default.
+        candidates: list[dict] = [{"id": candidate_strategy_id}]
+        champion_strategy_id, champion_profile = champion["strategy_id"], PROFILE_DEFAULT
+    else:
+        # PROFILE axis (era-3 J-07, unchanged): candidate enumeration reads the ONE registry
+        # FIRST — zero registered candidates is an honest empty sweep, and skipping straight to
+        # the report avoids running the champion's own backtests for nothing (they exist only to
+        # be compared against a candidate).
+        candidates = [p for p in config.profile_registry() if not p["is_default"]]
+        champion_strategy_id, champion_profile = champion["strategy_id"], champion["profile"]
 
     train_datasets = _split_datasets(dataset_store, SPLIT_TRAIN)
     holdout_datasets = _split_datasets(dataset_store, SPLIT_HOLDOUT)
@@ -288,14 +383,14 @@ def run_sweep(store: JournalStore, dataset_store: DatasetStore, config: Config)
         champion_train = [
             _run_backtest(
                 jobs, store, dataset_store, ds["id"],
-                strategy_id=champion["strategy_id"], profile=champion["profile"],
+                strategy_id=champion_strategy_id, profile=champion_profile, bar_store=bar_store,
             )
             for ds in train_datasets
         ]
         champion_holdout = [
             _run_backtest(
                 jobs, store, dataset_store, ds["id"],
-                strategy_id=champion["strategy_id"], profile=champion["profile"],
+                strategy_id=champion_strategy_id, profile=champion_profile, bar_store=bar_store,
             )
             for ds in holdout_datasets
         ]
@@ -304,17 +399,21 @@ def run_sweep(store: JournalStore, dataset_store: DatasetStore, config: Config)
     promotion: dict | None = None
     for candidate in candidates:
         candidate_id = candidate["id"]
+        if candidate_strategy_id is not None:
+            cand_strategy_id, cand_profile = candidate_id, PROFILE_DEFAULT
+        else:
+            cand_strategy_id, cand_profile = champion_strategy_id, candidate_id
         candidate_train = [
             _run_backtest(
                 jobs, store, dataset_store, ds["id"],
-                strategy_id=champion["strategy_id"], profile=candidate_id,
+                strategy_id=cand_strategy_id, profile=cand_profile, bar_store=bar_store,
             )
             for ds in train_datasets
         ]
         candidate_holdout = [
             _run_backtest(
                 jobs, store, dataset_store, ds["id"],
-                strategy_id=champion["strategy_id"], profile=candidate_id,
+                strategy_id=cand_strategy_id, profile=cand_profile, bar_store=bar_store,
             )
             for ds in holdout_datasets
         ]
@@ -353,6 +452,8 @@ def run_sweep(store: JournalStore, dataset_store: DatasetStore, config: Config)
                 config,
                 champion=champion,
                 candidate_id=candidate_id,
+                new_strategy_id=cand_strategy_id,
+                new_profile=cand_profile,
                 train_datasets=train_datasets,
                 holdout_datasets=holdout_datasets,
                 train_rows=train_rows,
@@ -366,6 +467,9 @@ def run_sweep(store: JournalStore, dataset_store: DatasetStore, config: Config)
         "champion_after": store.get_champion_pointer(),
         "candidates": candidate_entries,
         "promotion": promotion,
+        # era-4 J-06 (audit item B1): disclosed, never re-armed this iteration — see the constant's
+        # own docstring. Static and config-independent, so it never perturbs byte-identical reruns.
+        "provenance": {"assumptions": [BREAKTHROUGH_ANCHOR_CAVEAT]},
     }
 
 
@@ -379,24 +483,42 @@ def _render_report(report: dict) -> str:
 
 
 def main() -> int:
-    """The CLI entry: sweep against the operator's journal DB + dataset dir (the SAME
-    ``TAPEOLOGY_JOURNAL_DB`` / ``TAPEOLOGY_DATASET_DIR`` resolution seams the backend and
-    ``pnl_baseline`` read), writing the report to ``--out``. Zero candidates or zero survivors is
-    an honest, exit-0 outcome; a ``ScanError`` prints an explicit message to stderr and exits 1
-    with NOTHING written."""
+    """The CLI entry: sweep against the operator's journal DB + dataset dir + bar dir (the SAME
+    ``TAPEOLOGY_JOURNAL_DB`` / ``TAPEOLOGY_DATASET_DIR`` / ``TAPEOLOGY_BAR_DIR`` resolution seams
+    the backend and ``pnl_baseline`` read), writing the report to ``--out``. Zero candidates or
+    zero survivors is an honest, exit-0 outcome; a ``ScanError`` prints an explicit message to
+    stderr and exits 1 with NOTHING written.
+
+    ``--strategy`` (era-4 J-06) selects the strategy axis (see ``run_sweep``); omitted, the
+    profile sweep runs exactly as before this iteration. The bar store is constructed
+    unconditionally (the route's own precedent) — ``v1`` ignores it either way, so this is a no-op
+    for the profile axis and lets a named ``structure_tape`` candidate read real recorded levels."""
     parser = argparse.ArgumentParser(
         description="J-07 candidate-sweep harness — evaluate every registered candidate profile "
-        "against the current champion, validated on the frozen hold-out set."
+        "(or, with --strategy, ONE named candidate strategy) against the current champion, "
+        "validated on the frozen hold-out set."
     )
     parser.add_argument("--out", required=True, help="path to write the scan report JSON")
+    parser.add_argument(
+        "--strategy",
+        default=None,
+        metavar="STRATEGY_ID",
+        help="evaluate ONE named candidate strategy (e.g. structure_tape) against the champion's "
+        "current strategy at profile=default (era-4 J-06), instead of sweeping every registered "
+        "candidate profile (the default behaviour when this is omitted)",
+    )
     args = parser.parse_args()
 
     config = CONFIG
     store = JournalStore(config.journal_db_path_resolved(), config)
     try:
         dataset_store = DatasetStore(config.dataset_dir_resolved())
+        bar_store = BarStore(config.bar_dir_resolved())
         try:
-            report = run_sweep(store, dataset_store, config)
+            report = run_sweep(
+                store, dataset_store, config,
+                candidate_strategy_id=args.strategy, bar_store=bar_store,
+            )
         except ScanError as exc:
             print(f"error: {exc}", file=sys.stderr)
             return 1
diff --git a/apps/backend/tests/test_no_execution_path.py b/apps/backend/tests/test_no_execution_path.py
index ce36c97..d9e3ea3 100644
--- a/apps/backend/tests/test_no_execution_path.py
+++ b/apps/backend/tests/test_no_execution_path.py
@@ -172,3 +172,20 @@ def test_class_scaled_sizing_and_reward_target_code_carries_no_execution_vocabul
     assert "structure_tape_stop_bps_by_class" in text
     for pattern in TIER1_PATTERNS + TIER2_PATTERNS:
         assert pattern not in text, f"{pattern!r} found in the class-scaled sizing/exit code"
+
+
+def test_named_strategy_comparison_and_promotion_code_carries_no_execution_vocabulary():
+    """era-4 J-06: the named-strategy comparison (the ``--strategy`` CLI axis) and its promotion
+    path are new code in ``research/pnl_scan.py`` -- the champion move is a POINTER WRITE
+    (``JournalStore.set_champion_pointer``), never an order/route/broker call. The repo-wide sweeps
+    above already cover this file, but this test names the new capability explicitly, so the guard
+    is traceable to J-06, not merely inherited by accident."""
+    path = REPO_APPS / "backend" / "app" / "research" / "pnl_scan.py"
+    text = path.read_text()
+    # Confirm the scan actually sees the new axis code (a path/rename bug must never silently pass).
+    assert "candidate_strategy_id" in text
+    assert "set_champion_pointer" in text
+    for pattern in TIER1_PATTERNS + TIER2_PATTERNS:
+        assert pattern not in text, (
+            f"{pattern!r} found in the named-strategy comparison/promotion code"
+        )
diff --git a/apps/backend/tests/test_pnl_scan.py b/apps/backend/tests/test_pnl_scan.py
index 96eb71a..fef6833 100644
--- a/apps/backend/tests/test_pnl_scan.py
+++ b/apps/backend/tests/test_pnl_scan.py
@@ -48,20 +48,31 @@ from app.config import (
     Config,
     PROFILE_CANDIDATE_FASTER_WARMUP,
     PROFILE_DEFAULT,
+    STRATEGY_TAPE_ID,
     STRATEGY_V1_ID,
 )
 from app.providers.base import QuoteEvent, Side, TradeEvent
+from app.providers.simulated import SIM_SCENARIOS, SimulatedProvider
 from app.research import pnl_scan
+from app.research.bars import BarStore
 from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN, record_from_source
 from app.research.pnl_baseline import seed_founding_row
 from app.research.pnl_scan import ScanError, run_sweep
 from app.research.profiles import profiles_projection
 from app.research.store import JournalStore
 
+# The SAME synthetic three-timeframe confluence fixture test_backtests.py reuses (its own directive:
+# the committed real PG bar fixture stores only two timeframes and can never produce a class-A
+# zone, so any structure_tape test that needs one must use THIS fixture, not a second copy of it).
+from test_levels import _BASE as _CONFLUENCE_BASE, _CONFLUENCE_SYMBOL, _DAY, _confluence_fixture
+
 BACKEND_DIR = Path(__file__).resolve().parents[1]
 # The committed miniature train + hold-out dataset pair (the SAME fixture test_backtests.py's
 # ``test_committed_fixture_pair_backtests_keyless_end_to_end`` uses) — the keyless CI substrate.
 FIXTURE_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets"
+# The committed multi-timeframe PG bar fixture (era-4 J-01, 1h + 1d only — test_backtests.py's own
+# proof that it can never yield a class-A zone) — the keyless CI level source for the strategy axis.
+FIXTURE_BAR_DIR = Path(__file__).parent / "fixtures" / "bars"
 
 # The SAME founding windows the PnL ledger's founding row measures (config-owned; the
 # ``test_profile_equivalence.py`` precedent) — used ONLY for the "overfit" scenario below, where a
@@ -454,3 +465,343 @@ def test_cli_main_writes_a_report_and_exits_zero_on_the_fixture_pair(tmp_path, m
     payload = json.loads(out_path.read_text())
     assert payload["candidates"][0]["candidate_id"] == PROFILE_CANDIDATE_FASTER_WARMUP
     assert payload["promotion"] is None
+
+
+# --- era-4 J-06: the STRATEGY axis (``structure_tape`` vs ``v1``, Data Contract row 43) -----------
+# The synthetic three-timeframe confluence fixture puts a class-A zone at ~100.00 -- test_backtests.py's
+# OWN PROVEN, PINNED SIM-BUYER breakthrough-long arm (entry 19.5s @ 100.18, exit at dataset_end @
+# whatever the window's last price is) -- so every delta sign asserted below comes from a LIVE run
+# through the real sweep path, never a hand-derived number (mirroring this file's own "asserted, not
+# merely assumed" discipline for the profile axis above).
+
+_STRUCTURE_TAPE_ANCHOR = _CONFLUENCE_BASE + 8 * _DAY
+
+
+@pytest.fixture
+def confluence_bar_store(tmp_path):
+    bar_store = BarStore(tmp_path / "structure-bars")
+    _confluence_fixture(bar_store)
+    return bar_store
+
+
+def _sim_buyer_events(max_logical: float) -> list:
+    provider = SimulatedProvider("SIM-BUYER", SIM_SCENARIOS["SIM-BUYER"])
+    events: list = []
+    for event in provider.stream():
+        if event.timestamp > max_logical:
+            break
+        events.append(event)
+    return events
+
+
+def _record_structure_tape_dataset(
+    dataset_store: DatasetStore, *, symbol: str, split: str, max_logical: float
+) -> dict:
+    """Record the SAME canned SIM-BUYER stream test_backtests.py's own structure_tape tests use,
+    stamped with ``symbol`` (so the runner's ``compute_levels`` call finds -- or, for a symbol with
+    no recorded bar series, honestly does not find -- a matching level) and the shared
+    ``_STRUCTURE_TAPE_ANCHOR``. ``max_logical`` truncates the stream -- a longer window gives both
+    strategies more room to run without changing which reading first confirms."""
+    return dataset_store.record(
+        symbol=symbol,
+        source="SIM-BUYER",
+        source_kind="reference",
+        source_id=symbol,
+        split=split,
+        window_start_utc="2026-01-02T14:30:00Z",
+        window_end_utc="2026-01-02T14:45:00Z",
+        data_feed="sim",
+        epoch_anchor=_STRUCTURE_TAPE_ANCHOR,
+        events=_sim_buyer_events(max_logical),
+    )
+
+
+def test_strategy_axis_fixture_sweep_matches_shape_and_is_honestly_no_survivor(store):
+    """``--strategy structure_tape`` (via ``run_sweep``) on the COMMITTED PG train/hold-out fixture
+    pair, with the COMMITTED PG bar fixture (only 1h/1d -- test_backtests.py's own proof it can
+    never yield a class-A zone) as the level source. Per split the report carries the SAME shape
+    the profile axis does (champion + candidate measurements, deltas, dataset breakdown) -- and,
+    honestly, ``structure_tape`` trades NOTHING on train (no qualifying level ever reached in that
+    window) and exactly one class-C trade on hold-out, whose n sits below the promotion minimum --
+    the iter-3 lesson (2-timeframe fixture -> mostly class-C, few trades), proven here, not
+    assumed."""
+    dataset_store = DatasetStore(FIXTURE_DATASET_DIR)
+    bar_store = BarStore(FIXTURE_BAR_DIR)
+
+    report = run_sweep(
+        store, dataset_store, CONFIG, candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=bar_store
+    )
+
+    assert report["champion_before"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
+    assert report["champion_after"] == report["champion_before"]
+    assert report["promotion"] is None
+    (candidate,) = report["candidates"]
+    assert candidate["candidate_id"] == STRATEGY_TAPE_ID
+
+    # Shape: per split (never pooled), one dataset row carrying both sides' verbatim measurements
+    # plus the deltas -- the SAME shape the profile axis produces.
+    assert len(candidate["train"]["datasets"]) == 1
+    assert len(candidate["holdout"]["datasets"]) == 1
+    for split_summary in (candidate["train"], candidate["holdout"]):
+        row = split_summary["datasets"][0]
+        assert row.keys() >= {"dataset_id", "dataset_checksum", "champion", "candidate", "delta_net_r", "delta_net_usd"}
+        assert row["champion"].keys() == {"net_r", "net_usd", "n"}
+        assert row["candidate"].keys() == {"net_r", "net_usd", "n"}
+
+    # Honest fixture outcome (iter-3 lesson): zero structure_tape trades on train, exactly one on
+    # hold-out, below the promotion minimum -- champion (v1) genuinely lost money on this same train
+    # window (the era-3 finding), so the train delta reads positive even though structure_tape did
+    # nothing there; a real, non-fabricated mechanical consequence of the existing formula, not a
+    # bug -- but the hold-out gate is what actually decides promotion, and it honestly fails.
+    assert candidate["train"]["aggregate"]["candidate_n"] == 0
+    assert candidate["holdout"]["aggregate"]["candidate_n"] == 1
+    assert candidate["holdout"]["aggregate"]["candidate_n"] < CONFIG.promotion_min_sample_size
+    assert candidate["survivor"] is False
+
+    # Audit B1: disclosed in provenance/assumptions on every report (this axis included).
+    assert any(
+        "structure_tape" in note and "breakthrough" in note
+        for note in report["provenance"]["assumptions"]
+    )
+
+    # Nothing written, nothing moved, foundation untouched.
+    assert len(store.list_pnl_ledger()) == 0
+    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+
+
+def test_strategy_axis_determinism_two_independent_fresh_state_runs_are_byte_identical(tmp_path, monkeypatch):
+    """The SAME determinism guarantee as the profile axis (Key Test Scenario 4), proven for
+    ``--strategy structure_tape`` end to end through the REAL CLI, against the committed PG
+    dataset AND bar fixtures."""
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(FIXTURE_DATASET_DIR))
+    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(FIXTURE_BAR_DIR))
+
+    def _run_once(label: str) -> bytes:
+        monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / f"journal-strategy-{label}.db"))
+        out_path = tmp_path / f"scan-strategy-{label}.json"
+        monkeypatch.setattr(
+            sys, "argv", ["pnl_scan", "--out", str(out_path), "--strategy", STRATEGY_TAPE_ID]
+        )
+        exit_code = pnl_scan.main()
+        assert exit_code == 0
+        return out_path.read_bytes()
+
+    first = _run_once("a")
+    second = _run_once("b")
+    assert first == second
+    assert len(first) > 200
+
+
+def test_strategy_axis_controlled_survivor_moves_champion_and_appends_exactly_one_ledger_row(
+    store, tmp_path, confluence_bar_store
+):
+    """An ISOLATED synthetic train + hold-out pair (never the shipped PG fixture) on which
+    ``structure_tape`` legitimately beats ``v1`` on BOTH splits (the class-A breakthrough-long arm,
+    with a test-LOCAL lowered promotion minimum -- the shipped default of 5 is never touched):
+    promotes for real -- the pointer moves to ``{structure_tape, default}``, exactly one
+    provenance-stamped ledger row is appended -- while ``default``/``v1``/every engine default stay
+    byte-identical."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    train_meta = _record_structure_tape_dataset(
+        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=25.0
+    )
+    holdout_meta = _record_structure_tape_dataset(
+        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_HOLDOUT, max_logical=40.0
+    )
+    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)
+
+    report = run_sweep(
+        store, dataset_store, test_config,
+        candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
+    )
+
+    (candidate,) = report["candidates"]
+    assert candidate["candidate_id"] == STRATEGY_TAPE_ID
+    # The win is asserted, not merely assumed (both R and $, on both splits).
+    assert candidate["train"]["aggregate"]["delta_net_r"] > 0
+    assert candidate["train"]["aggregate"]["delta_net_usd"] > 0
+    assert candidate["holdout"]["aggregate"]["delta_net_r"] > 0
+    assert candidate["holdout"]["aggregate"]["delta_net_usd"] > 0
+    assert candidate["survivor"] is True
+    assert candidate["overfit"] is False
+
+    assert report["champion_before"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
+    assert report["champion_after"] == {"strategy_id": STRATEGY_TAPE_ID, "profile": PROFILE_DEFAULT}
+    assert report["promotion"] == {
+        "candidate_id": STRATEGY_TAPE_ID,
+        "promoted": True,
+        "enhancement_id": f"{STRATEGY_TAPE_ID}-over-{STRATEGY_V1_ID}-{PROFILE_DEFAULT}",
+    }
+
+    rows = store.list_pnl_ledger()
+    assert len(rows) == 1
+    row = rows[0].payload
+    assert row["founding"] is False
+    assert row["provenance"]["strategy_id"] == STRATEGY_TAPE_ID
+    assert row["provenance"]["profile"] == PROFILE_DEFAULT
+    assert row["provenance"]["train"]["dataset_id"] == train_meta["id"]
+    assert row["provenance"]["holdout"]["dataset_id"] == holdout_meta["id"]
+
+    # Frozen foundation AFTER a STRATEGY-axis promotion too: fingerprint unmoved.
+    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    # Single-source: the projection reflects the SAME moved pointer, verbatim.
+    assert profiles_projection(store, test_config)["champion"] == report["champion_after"]
+
+
+def test_strategy_axis_mid_promotion_crash_leaves_no_orphan_and_no_silent_double_append(
+    store, tmp_path, confluence_bar_store
+):
+    """The SAME crash-safety guarantee as the profile axis (Key Test Scenario 4), reverting JUST
+    the pointer after a real strategy-axis promotion and re-running -- must refuse explicitly, never
+    silently re-promote (a second ledger row) or silently do nothing."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_structure_tape_dataset(
+        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=25.0
+    )
+    _record_structure_tape_dataset(
+        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_HOLDOUT, max_logical=40.0
+    )
+    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)
+
+    first = run_sweep(
+        store, dataset_store, test_config,
+        candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
+    )
+    assert first["promotion"]["promoted"] is True
+    assert len(store.list_pnl_ledger()) == 1
+
+    store.set_champion_pointer(strategy_id=STRATEGY_V1_ID, profile=PROFILE_DEFAULT, wall_ts=0.0)
+
+    with pytest.raises(ScanError, match="already exists"):
+        run_sweep(
+            store, dataset_store, test_config,
+            candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
+        )
+    assert len(store.list_pnl_ledger()) == 1  # never a second row
+
+
+def test_strategy_axis_min_n_gate_rejects_below_minimum_despite_positive_holdout(
+    store, tmp_path, confluence_bar_store
+):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_structure_tape_dataset(
+        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=25.0
+    )
+    _record_structure_tape_dataset(
+        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_HOLDOUT, max_logical=40.0
+    )
+    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=2)  # candidate n=1 < 2
+
+    report = run_sweep(
+        store, dataset_store, test_config,
+        candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
+    )
+
+    (candidate,) = report["candidates"]
+    assert candidate["holdout"]["aggregate"]["delta_net_r"] > 0
+    assert candidate["holdout"]["aggregate"]["delta_net_usd"] > 0
+    assert candidate["holdout"]["aggregate"]["candidate_n"] == 1
+    assert candidate["survivor"] is False
+    assert report["promotion"] is None
+    assert len(store.list_pnl_ledger()) == 0
+    assert report["champion_after"] == report["champion_before"]
+
+
+def test_strategy_axis_min_n_gate_promotes_at_or_above_minimum(store, tmp_path, confluence_bar_store):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_structure_tape_dataset(
+        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=25.0
+    )
+    _record_structure_tape_dataset(
+        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_HOLDOUT, max_logical=40.0
+    )
+    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)  # candidate n=1 >= 1
+
+    report = run_sweep(
+        store, dataset_store, test_config,
+        candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
+    )
+
+    (candidate,) = report["candidates"]
+    assert candidate["survivor"] is True
+    assert report["promotion"]["promoted"] is True
+    assert len(store.list_pnl_ledger()) == 1
+
+
+def test_strategy_axis_overfit_is_positive_train_failing_holdout_and_is_never_promoted(
+    store, tmp_path, confluence_bar_store
+):
+    """Train: ``structure_tape`` genuinely beats ``v1`` (the real class-A breakthrough win, over
+    ``_CONFLUENCE_SYMBOL``, which HAS a recorded bar series). Hold-out: a DIFFERENT symbol with NO
+    recorded bar series in the SAME bar store -- ``structure_tape`` honestly arms nothing there
+    (n=0) while ``v1`` still profits on the identical underlying tape shape, so the hold-out delta
+    is NEGATIVE. Positive train + a failed hold-out gate = ``overfit`` by the module's own
+    definition -- and an overfit candidate is never promoted, whatever train looked like."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_structure_tape_dataset(
+        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=25.0
+    )
+    _record_structure_tape_dataset(
+        dataset_store, symbol="SYN-NO-LEVELS", split=SPLIT_HOLDOUT, max_logical=40.0
+    )
+    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)
+
+    report = run_sweep(
+        store, dataset_store, test_config,
+        candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
+    )
+
+    (candidate,) = report["candidates"]
+    assert candidate["train"]["aggregate"]["delta_net_r"] > 0
+    assert candidate["train"]["aggregate"]["delta_net_usd"] > 0
+    assert candidate["holdout"]["aggregate"]["candidate_n"] == 0  # no recorded levels for this symbol
+    assert candidate["holdout"]["aggregate"]["delta_net_r"] < 0
+    assert candidate["overfit"] is True
+    assert candidate["survivor"] is False
+    assert report["promotion"] is None
+    assert len(store.list_pnl_ledger()) == 0
+    assert report["champion_after"] == report["champion_before"]
+
+
+def test_strategy_axis_more_than_one_dataset_per_split_skips_promotion_with_honest_note(
+    store, tmp_path, confluence_bar_store
+):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_structure_tape_dataset(
+        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=25.0
+    )
+    _record_structure_tape_dataset(  # a SECOND registered train dataset
+        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=30.0
+    )
+    _record_structure_tape_dataset(
+        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_HOLDOUT, max_logical=40.0
+    )
+    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)
+
+    report = run_sweep(
+        store, dataset_store, test_config,
+        candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
+    )
+
+    (candidate,) = report["candidates"]
+    assert len(candidate["train"]["datasets"]) == 2
+    assert len(candidate["holdout"]["datasets"]) == 1
+    assert candidate["survivor"] is True  # the hold-out gate itself still passes...
+    assert report["promotion"]["promoted"] is False  # ...but promotion is explicitly skipped
+    assert "2 train" in report["promotion"]["note"]
+    assert len(store.list_pnl_ledger()) == 0
+    assert report["champion_after"] == report["champion_before"]
+
+
+def test_strategy_axis_unknown_candidate_strategy_id_is_an_explicit_refusal(store):
+    """No new validation code exists for this -- ``BacktestJobManager.create`` stamps
+    ``strategy_id`` verbatim, and ``BacktestRunner.run`` persists an unregistered id as an explicit
+    ``failed`` record (never raises out), which ``_run_backtest``'s EXISTING status check turns
+    into this same ``ScanError``. Never a coerced/fabricated comparison."""
+    dataset_store = DatasetStore(FIXTURE_DATASET_DIR)
+
+    with pytest.raises(ScanError):
+        run_sweep(store, dataset_store, CONFIG, candidate_strategy_id="not-a-real-strategy")
+
+    assert len(store.list_pnl_ledger()) == 0
+    assert store.get_champion_pointer() == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
diff --git adocs/handoffs/goal-tape_to_profit_support_resistence-iter-6-audit.md bdocs/handoffs/goal-tape_to_profit_support_resistence-iter-6-audit.md
new file mode 100644
index 0000000..d3b44ba
--- /dev/null
+++ bdocs/handoffs/goal-tape_to_profit_support_resistence-iter-6-audit.md
@@ -0,0 +1,149 @@
+# goal-tape_to_profit_support_resistence-iter-6 Audit Report
+
+**Date:** 2026-07-06
+**Auditor:** Hard audit pass — skeptical, evidence-based
+
+---
+
+## 1. Executive Verdict
+
+**Verdict:** PASS
+
+J-06 — the final Must-have of Era 4 — is genuinely realized. `pnl_scan.py` gains an additive
+STRATEGY axis (`--strategy structure_tape`) that reuses the existing per-split comparison and
+crash-safe promotion machinery verbatim; the load-bearing "no train-only promotion" gate is
+enforced in backend logic, the frozen `default`/`v1`/engine foundation is verifiably untouched
+(I confirmed `v1`/`default` aggregates are byte-identical with vs without a `bar_store`, and the
+config fingerprint `4d665603569b9dbf` is unmoved), and the committed fixtures honestly yield
+"no survivor" at exit 0 with byte-identical determinism. No CRITICAL or IMPORTANT issue found;
+no fix required. Three OBSERVATION-level notes are recorded below.
+
+---
+
+## 2. Findings
+
+### Backend Findings
+
+**B1 — OBSERVATION (observation): `overfit=true` on the committed fixtures where `structure_tape` abstained (n=0 on train)**
+`apps/backend/app/research/pnl_scan.py:436` (`overfit = train_positive and not survivor`). On the
+committed PG fixtures, `structure_tape` trades **zero** times on the train window (`candidate_n=0`,
+confirmed live). The train delta reads *positive* only because champion `v1` itself lost money on
+that exact window (the era-3 finding) while `structure_tape` did nothing — so `train_positive=True`
+and, with `survivor=False`, the derived flag reads `overfit=True`. Semantically this is a loose
+label (the strategy abstained; it did not "overfit" a spurious train edge), but it is **not a
+defect**: (a) the label uses the era-3, spec-mandated, reused-verbatim formula the plan explicitly
+forbids modifying; (b) it is a *derived, non-gating* field — the promotion decision hinges only on
+`survivor`, which is correctly `False`; (c) the underlying honest datum (`candidate_n=0` on train)
+is fully present in the per-dataset breakdown, so nothing is concealed; and (d) the anti-goal
+"train-only wins are labelled overfit and rejected" is literally satisfied. Disclosed by the dev in
+the handoff's Known Issues. **Not fixed** — changing the formula would be scope creep explicitly
+prohibited by the spec and would risk perturbing the frozen profile axis.
+
+**B2 — OBSERVATION (observation): strategy axis compares against the champion at `profile=default`, not `champion["profile"]`**
+`apps/backend/app/research/pnl_scan.py:365` (`champion_strategy_id, champion_profile = champion["strategy_id"], PROFILE_DEFAULT`).
+The strategy axis holds the champion's profile fixed at `default` rather than reading
+`champion["profile"]`. This is **exactly what the spec prescribes** ("compared against the
+champion's CURRENT `strategy_id` … also at `profile=PROFILE_DEFAULT`") and is correct on the
+foundation store where the champion is `{v1, default}`. It would only diverge from the "true"
+champion after a *prior* profile-axis promotion to a **non-default** profile — a state that cannot
+arise on the committed fixtures (no survivor) and is outside the Era-4 hypothesis. Recorded as a
+documented design assumption, not a gap.
+
+### Frontend Findings
+
+None. Frontend Present: no. `git status --porcelain apps/frontend/` returns empty — the zero
+frontend diff that keeps J-07's cockpit leg green without a new screenshot (iter-0 lesson) is
+confirmed.
+
+### Test Findings
+
+**T1 — OBSERVATION (observation): the pre-written QA test plan speculates a CLI/JSON shape that the implementation deliberately does not match**
+`reports/qa/goal-tape_to_profit_support_resistence-iter-6-test-plan.md` (authored before the code)
+assumes `--splits train`/`--splits hold_out` flags, field names `strategy_tape_R`/`v1_R`/`delta_R`,
+and `overfit=false` for a below-min-n hold-out. None of these match the reused-verbatim
+implementation (single invocation reports both splits; `champion`/`candidate` field names;
+`overfit` per the reused formula). This is a **plan-vs-implementation divergence, not a code
+defect** — the implementation correctly follows the spec's "reuse the machinery verbatim"
+instruction, and the dev/reviewer/QA all triaged it. The real acceptance is the 9 new code tests,
+which use **tight** assertions (exact `champion_after` dicts, exact `promotion`/`enhancement_id`,
+exact `candidate_n` 0/1, exact ledger-row counts, `pytest.raises(ScanError, match="already
+exists")`). Verified independently.
+
+---
+
+## 3. Domain Assessment
+
+The core domain logic — the promotion gate — is correct and honestly enforced:
+
+- **"No train-only promotion" (the critical anti-goal) holds.** `survivor` is true iff the summed
+  hold-out delta is positive on **both** net R and net $ **and** the summed hold-out candidate `n`
+  ≥ `promotion_min_sample_size` (`pnl_scan.py:430-433`), and promotion runs only `if survivor`
+  (`:449`). A positive-train / failing-hold-out synthetic fixture yields `overfit=true`,
+  `survivor=false`, no ledger row, no pointer move
+  (`test_strategy_axis_overfit_…`, run green). The gate lives entirely in backend logic; there is
+  no frontend to bypass it.
+- **Crash-safe promotion order verified.** `_promote` appends the ledger row **then** moves the
+  pointer (`pnl_scan.py:307-326`); a mid-promotion crash leaves a durable ledger row + unmoved
+  pointer, and a re-run hits the ledger's `DuplicateEnhancementError` → explicit `ScanError`
+  (`test_strategy_axis_mid_promotion_crash_…`, green; asserts no second row).
+- **Frozen foundation genuinely intact.** I directly re-ran a `v1`/`default` backtest with
+  `bar_store=None` and with a real `BarStore` and got **byte-identical aggregates** — so threading
+  `bar_store` through the profile axis (the one non-trivial change to the existing path) does not
+  perturb `v1`/`default`. `config_fingerprint()` returns `4d665603569b9dbf` (unmoved);
+  `test_profile_equivalence.py` is 13/13 green; `config.py`, `store.py`, `pnl_ledger.py`,
+  `edge_report.py` are untouched (`git status` clean).
+- **Single source of truth preserved.** Every backtest goes through the one
+  `BacktestJobManager.create` + `run_sync`; `_measurement`/`_dataset_rows`/`_split_summary` are
+  reused verbatim (the removed-lines diff shows no new R/$/edge arithmetic); `set_champion_pointer`
+  is called from exactly one file (`test_champion_pointer_setter_is_called_from_exactly_one_source_file`,
+  green). The ledger provenance `strategy_id`/`profile` is derived from the winning candidate's own
+  report (`pnl_ledger.py:178-179`), so a promoted `structure_tape` row correctly stamps
+  `strategy_id=structure_tape`, `profile=default`.
+- **Honest fixture outcome + determinism, verified live.** Two independent fresh-state
+  `--strategy structure_tape` CLI runs produced **byte-identical** `--out` bytes; exit 0;
+  `survivor=false`; `train_n=0`, `holdout_n=1` (below the minimum of 5); `holdout_delta_r ≈ -0.343`
+  (a genuine hold-out loss); `champion_before == champion_after == {v1, default}`; `promotion=null`;
+  nothing written to the ledger. `get_champion_pointer()` returns only `{strategy_id, profile}`
+  (no timestamp), which is why the report is byte-stable across runs.
+- **Audit B1 resolved by disclosure, not re-arming.** Every report carries
+  `provenance.assumptions` naming the breakthrough arm's loose static-price-position anchor — a
+  static, config-independent string that does not perturb byte-identical reruns
+  (`pnl_scan.py:143-150, 472`), confirmed present in the live report.
+- **No live execution path.** The new grep-guard test is non-vacuous — it positively asserts the
+  new axis code (`candidate_strategy_id`, `set_champion_pointer`) is scanned, then asserts none of
+  the comprehensive TIER1/TIER2 order/broker/routing/paper-trading patterns appear
+  (`test_no_execution_path.py`, 6/6 green). The champion move is a pointer write, not an order.
+
+**Independent test verification (not trusting the handoff):**
+- `test_pnl_scan.py` + `test_no_execution_path.py` + `test_profile_equivalence.py`: 42 passed.
+- Full backend suite (`.venv/bin/python -m pytest tests/ -q`): **exit code 0** (pytest returns 0
+  only when every collected test passes) — reproducing QA's 1146 passed / 1 skipped / 0 failed.
+- `grep -c "def test_strategy_axis"` = 9 new tests; 21 total in the file (12 pre-existing
+  **unmodified** — the removed-lines diff of `test_pnl_scan.py` is empty, confirming backward
+  compatibility).
+
+---
+
+## 4. Fixes Applied During This Audit
+
+None. No CRITICAL or IMPORTANT finding was identified. All three findings are OBSERVATION-level and
+either spec-conformant by design (B2), a disclosed cosmetic quirk of a spec-mandated reused formula
+(B1), or a plan-vs-implementation divergence rather than a code defect (T1). Applying a "fix" to any
+of them would be scope creep — B1 in particular would require editing the reused-verbatim `overfit`
+formula, which the spec explicitly forbids and which would risk the frozen profile axis.
+
+| # | Severity | File | Change |
+|---|----------|------|--------|
+| — | — | — | No fixes applied (no critical/important findings). |
+
+---
+
+## 5. Recommended Next Step
+
+**Proceed.** J-06 is genuinely complete: the named-strategy comparison, the hold-out-only promotion
+gate, crash-safe promotion, the frozen-foundation guarantee, B1 disclosure, backward compatibility,
+and the honest "no survivor at exit 0" fixture outcome are all implemented and independently
+verified. As the final Must-have, this iteration is ready for the **goal-evaluator** to run its
+deterministic gates and two-key confirm for a GOAL_ACHIEVED decision (only the evaluator may declare
+it). The two OBSERVATIONs (B1's loose `overfit` label when a strategy abstains; B2's `profile=default`
+assumption on the strategy axis) are informational and need no action this iteration.
diff --git adocs/handoffs/goal-tape_to_profit_support_resistence-iter-6-dev.md bdocs/handoffs/goal-tape_to_profit_support_resistence-iter-6-dev.md
new file mode 100644
index 0000000..62de5c3
--- /dev/null
+++ bdocs/handoffs/goal-tape_to_profit_support_resistence-iter-6-dev.md
@@ -0,0 +1,201 @@
+# goal-tape_to_profit_support_resistence-iter-6 Dev Handoff
+
+**Phase:** goal-tape_to_profit_support_resistence-iter-6
+**Date:** 2026-07-06
+**Agent:** developer
+**Status:** complete
+
+## IMPORTANT — Note on exact CLI usage and field naming (for QA/reviewer alignment)
+
+`reports/qa/goal-tape_to_profit_support_resistence-iter-6-test-plan.md` was written before this
+implementation existed and speculates a CLI invocation and JSON shape that differ from what was
+actually built. The choices below were made because the phase spec/plan explicitly said to
+**reuse the existing sweep's machinery verbatim** (`_dataset_rows` / `_split_summary` /
+`_is_positive` / `_promote`) — inventing new field names or a new report shape for the strategy
+axis would have violated that instruction. Please re-read the test plan against this section
+before running it literally.
+
+1. **Invocation is `python -m app.research.pnl_scan`, not a bare script path.** The module uses
+   package-relative imports (`from ..config import ...`), exactly like every other module under
+   `app/research/` — it has NEVER been runnable as `python apps/backend/app/research/pnl_scan.py`
+   (that predates this iteration; running it that way raises `ImportError: attempted relative
+   import with no known parent package` regardless of this change). The correct command (matching
+   the module's own long-standing docstring):
+   ```
+   cd apps/backend && .venv/bin/python -m app.research.pnl_scan --strategy structure_tape --out /tmp/report.json
+   ```
+2. **There is no `--splits train` / `--splits hold_out` flag** (the test plan's TC-01/TC-02/TC-09
+   assume one) — none was asked for by the phase spec, and adding one would have been scope creep.
+   A single invocation ALWAYS reports both splits together (per-split, never pooled) — this is the
+   SAME "one report, two split sections" shape the profile axis has always used, carried forward
+   verbatim, per the iter-5 lesson recorded in this iteration's own plan ("the DoD's 'per
+   train/hold-out split' is satisfied by dataset provenance... NOT a second split axis inside a
+   single report — don't over-build a two-axis breakdown"). Passing `--splits` would be an
+   `argparse` "unrecognized arguments" error, not a functional defect.
+3. **The split key is `"holdout"` (no underscore)**, matching the existing `SPLIT_HOLDOUT`
+   constant (`app/research/datasets.py`) — not `"hold_out"`.
+4. **Per-dataset row field names reuse the EXISTING shape verbatim** (`_dataset_rows` /
+   `_split_summary`, unchanged), not the test plan's speculated
+   `strategy_tape_R`/`v1_R`/`delta_R`/`dataset` names. A real report's shape (confirmed via a live
+   CLI run against the committed fixtures, not merely inferred):
+   ```
+   report = {
+     "register": "...", "promotion_min_sample_size": 5,
+     "champion_before": {"strategy_id": "v1", "profile": "default"},
+     "champion_after": {...}, "promotion": null | {...},
+     "provenance": {"assumptions": ["...B1 disclosure..."]},
+     "candidates": [{
+       "candidate_id": "structure_tape", "survivor": bool, "overfit": bool,
+       "robustness": "robust" | "speculative",
+       "train": {
+         "aggregate": {"delta_net_r": ..., "delta_net_usd": ..., "candidate_n": ..., "champion_n": ...},
+         "datasets": [{
+           "dataset_id": ..., "dataset_checksum": ...,
+           "champion": {"net_r": ..., "net_usd": ..., "n": ...},
+           "candidate": {"net_r": ..., "net_usd": ..., "n": ...},
+           "delta_net_r": ..., "delta_net_usd": ...
+         }]
+       },
+       "holdout": { ...same shape as "train"... }
+     }]
+   }
+   ```
+   `"champion"` (not `"v1_*"`) is intentional: the champion's identity is data (read from
+   `store.get_champion_pointer()`), never hardcoded to `v1` in the report shape, so the SAME shape
+   stays correct if `v1` is ever displaced by a genuine promotion.
+5. **The promoted enhancement id is `"structure_tape-over-v1-default"`** (test plan TC-06 example
+   says `"structure_tape-over-v1"`, omitting the profile suffix) — this reuses the EXISTING
+   `f"{candidate_id}-over-{champion['strategy_id']}-{champion['profile']}"` composition verbatim
+   (unchanged from the profile axis), never a shortened id invented just for this axis.
+6. **TC-03's expectation that a positive-but-below-min-n hold-out yields `overfit=false` does not
+   match the EXISTING, REUSED-VERBATIM formula.** `overfit = train_positive and not survivor`, and
+   `survivor` already folds in BOTH the sign check and the n-gate — there is no third state in the
+   pre-existing (era-3, unmodified) formula that exempts "positive but insufficient n" from the
+   `overfit` label. This is not a regression introduced by J-06: the PRE-EXISTING profile-axis test
+   `test_min_n_gate_rejects_below_minimum_despite_positive_holdout` exercises the identical
+   scenario shape and (correctly, deliberately) never asserts `overfit`'s value either, for exactly
+   this reason. My new strategy-axis min-n tests follow the same deliberate omission. Changing this
+   would mean modifying `_is_positive`/`overfit`'s formula, which the plan explicitly says to reuse
+   verbatim — flagging for the auditor/evaluator to triage rather than silently reinterpreting it.
+
+## What Was Built
+
+- **A STRATEGY axis on the existing sweep** (`apps/backend/app/research/pnl_scan.py`,
+  `run_sweep(..., candidate_strategy_id=None, bar_store=None)`) — an ADDITIVE branch beside the
+  existing PROFILE axis, never a refactor of it:
+  - CLI gains `--strategy STRATEGY_ID` (optional). Given, the sweep evaluates EXACTLY ONE
+    candidate — backtest at `strategy_id=<given>`, `profile=default` — compared against the
+    champion's CURRENT `strategy_id` (read verbatim from `store.get_champion_pointer()`, never
+    hardcoded `"v1"`), also at `profile=default`.
+  - Omitted (the default, `None`): the profile axis behaves **byte-identically** to before this
+    iteration — proven by all 12 pre-existing `test_pnl_scan.py` tests passing completely
+    unmodified.
+- **`bar_store` (era-4 J-04's row-39 level source) threaded through every backtest call, on both
+  axes** — `_run_backtest` now accepts and forwards it to `jobs.run_sync(...)`; `main()`
+  unconditionally constructs `BarStore(config.bar_dir_resolved())` (the route's own precedent).
+  `v1` ignores it entirely (byte-identical whether `None` or real), so this is a no-op for the
+  profile axis; only a `structure_tape` backtest ever reads it, and honestly arms nothing without
+  one.
+- **`_promote` generalized** to accept explicit `new_strategy_id` / `new_profile` — the exact pair
+  the winning candidate's own backtests ran at — instead of hardcoding the profile-axis assumption
+  (`strategy_id=champion['strategy_id'], profile=candidate_id`). The profile axis's resulting
+  pointer move is unchanged; a strategy-axis promotion moves the pointer to
+  `{strategy_id: <candidate>, profile: "default"}`.
+- **Audit item B1 disclosed, not re-armed**: every report (both axes) now carries a top-level
+  `provenance.assumptions` list naming the `structure_tape` breakthrough arm's loose,
+  sanctioned static-price-position anchor (a single at-event position test, not a fresh
+  event-to-event level cross). A static, config-independent string (`BREAKTHROUGH_ANCHOR_CAVEAT`
+  module constant) — present on every report regardless of axis, so it never perturbs the
+  byte-identical-rerun guarantee.
+- **`tests/test_no_execution_path.py`** — one new test
+  (`test_named_strategy_comparison_and_promotion_code_carries_no_execution_vocabulary`) naming the
+  new axis code explicitly (the iter-5 precedent for
+  `test_class_scaled_sizing_and_reward_target_code_carries_no_execution_vocabulary`).
+- **9 new tests in `tests/test_pnl_scan.py`** covering: comparison shape + fixture honesty on the
+  committed PG dataset+bar fixtures (structure_tape trades 0 on train, 1 on hold-out — below the
+  promotion minimum, the iter-3 lesson proven empirically); determinism of the `--strategy` CLI
+  path; a genuine hold-out survivor promoting correctly (pointer move + exactly one ledger row +
+  frozen-foundation fingerprint check); the same mid-promotion crash-safety guarantee as the
+  profile axis; the min-n gate both ways; overfit labelling (positive train, failing hold-out,
+  never promoted); >1-dataset-per-split honest promotion skip; and an unknown-strategy-id explicit
+  refusal. Every asserted delta sign was verified empirically via a scratch probe against the real
+  code before being written into an assertion — never hand-derived.
+- **README.md doc-parity**: the existing "Candidate validation sweep" bullet now describes the
+  named-strategy comparison capability and honestly states today's finding on the committed sample
+  data (too few hold-out trades to trust a result yet — no promotion). The iter-5 doc-parity rider
+  (the class-scaled-risk bullet) was already present — confirmed via `git blame`/reading, not
+  duplicated.
+
+## Files Changed
+
+- `apps/backend/app/research/pnl_scan.py` -- added the `--strategy` CLI option, the
+  `candidate_strategy_id`/`bar_store` params on `run_sweep`, the strategy-axis branch, generalized
+  `_promote`'s pointer-move params, and the B1 disclosure constant + `provenance` report field.
+- `apps/backend/tests/test_pnl_scan.py` -- 9 new tests for the strategy axis (see What Was Built);
+  zero existing tests modified.
+- `apps/backend/tests/test_no_execution_path.py` -- 1 new test naming the strategy-axis code
+  explicitly.
+- `README.md` -- doc-parity: the "Candidate validation sweep" bullet updated.
+- `runs/goal-tape_to_profit_support_resistence-iter-6/status.json` -- `current_step: dev_complete`.
+
+No changes to `apps/backend/app/config.py`, `app/research/store.py`, `app/research/pnl_ledger.py`,
+or `app/research/edge_report.py` (all "expected no changes" per the plan; confirmed via
+`git status`/`git diff --stat`). No changes anywhere under `apps/frontend/` (confirmed via
+`git status --porcelain apps/frontend` returning empty — Frontend Present: no, per the plan).
+
+## Tests Run
+
+Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
+
+Result (after this iteration's changes): **1146 passed, 1 skipped, 0 failed.**
+Baseline (immediately before touching any code this iteration, same command): 1136 passed, 1
+skipped, 0 failed. The 1 skip is pre-existing and unrelated to this iteration. Delta: +10 tests
+(9 in `test_pnl_scan.py`, 1 in `test_no_execution_path.py`), **zero regressions**.
+
+Narrower confirms also run:
+- `pytest tests/test_pnl_scan.py -v` -- 21 passed (12 pre-existing unmodified + 9 new).
+- `pytest tests/test_no_execution_path.py -v` -- 6 passed (5 pre-existing + 1 new).
+- `pytest tests/test_profile_equivalence.py -v` -- all green (engine/`default`/`v1` byte-identity
+  untouched; `config_fingerprint() == "4d665603569b9dbf"` still pinned, verified again inside the
+  new survivor test after a real strategy-axis promotion).
+
+Live (non-mocked) verification, beyond pytest:
+- Ran the real CLI end-to-end against the committed fixtures via env vars
+  (`TAPEOLOGY_DATASET_DIR=tests/fixtures/datasets`, `TAPEOLOGY_BAR_DIR=tests/fixtures/bars`):
+  `python -m app.research.pnl_scan --strategy structure_tape --out <path>` -- exit 0, output
+  matched the pytest-asserted numbers exactly (train candidate n=0, hold-out candidate n=1,
+  `survivor=false`, champion unmoved, `provenance.assumptions` present).
+  Also ran the backward-compatible no-flag path live -- exit 0.
+- Service startup (`scripts/dev.sh`): started cleanly, stopped, and restarted a second time with no
+  port conflicts -- backend `:8301` (`/health`) and frontend `:3301` (`/`) both returned HTTP 200
+  both times. No startup errors from this iteration's changes (expected: no route or frontend code
+  was touched).
+
+## Known Issues
+
+- **TC-03/QA-plan `overfit` expectation mismatch** -- see the "Note on exact CLI usage and field
+  naming" section above. Not a regression; the reused-verbatim `overfit` formula has no third state
+  for "positive train, hold-out positive-but-below-min-n" -- it reads `overfit=true` in that case,
+  identically on both axes, and pre-dates this iteration.
+- **`structure_tape` trades ZERO times on the committed PG TRAIN window**, not merely "few" -- the
+  2-timeframe PG bar fixture's zones never fall inside that window's price path. The HOLD-OUT
+  window does reach one class-C zone (n=1, still below the promotion minimum of 5). Both splits
+  honestly fail the gate; the train delta reads *positive* only because champion `v1` itself lost
+  money on that exact window (the era-3 finding, `docs/goal.md`) while `structure_tape` traded
+  nothing there -- a real, non-fabricated mechanical consequence of the (unmodified) `overfit`
+  formula, asserted directly in the new fixture test rather than concealed.
+- **The genuine-survivor / overfit / min-n synthetic tests never touch the committed PG fixture**
+  (per the iter-3 lesson, explicit in this iteration's plan) -- they reuse the existing synthetic
+  three-timeframe confluence fixture (`test_levels._confluence_fixture`, imported directly rather
+  than duplicated) paired with the canned `SIM-BUYER` scenario at varying window lengths. Every
+  asserted delta sign was verified empirically via a scratch probe first.
+- **`edge_report.py` was not touched** -- explicitly optional per the plan and not required for the
+  DoD; it still evaluates only the champion strategy, unchanged from before this iteration.
+- **Pre-existing operational finding, unrelated to this iteration's code** (surfaced only because
+  the mandatory pre-handoff service-startup check runs `scripts/dev.sh` twice): a plain
+  `pkill -f "next dev"` / `pkill -f "uvicorn main:app"` does not reliably reap every child process
+  -- `next dev`'s spawned `next-server` (node) process, and uvicorn `--reload`'s multiprocessing
+  worker (whose command line is a bare `python -c "from multiprocessing.spawn import
+  spawn_main..."`, containing no `"uvicorn"` substring at all), can outlive a parent-only kill and
+  keep holding the port. Had to kill by explicit PID during this iteration's verification.
+  `scripts/dev.sh` is untouched (out of scope) -- flagging for operator awareness only.
diff --git adocs/phases/goal-tape_to_profit_support_resistence-iter-6.md bdocs/phases/goal-tape_to_profit_support_resistence-iter-6.md
new file mode 100644
index 0000000..90a9405
--- /dev/null
+++ bdocs/phases/goal-tape_to_profit_support_resistence-iter-6.md
@@ -0,0 +1,128 @@
+# Goal Iteration 6 — J-06: `structure_tape` measured honestly against the `v1` champion (named-strategy comparison + hold-out promotion gate)
+
+<!-- machine-readable goal-mode metadata -->
+## Goal Mode Metadata
+
+- **Session ID:** tape_to_profit_support_resistence
+- **Iteration:** 6
+- **Mode:** next
+- **Depth:** full
+- **Frontend Present:** no
+- **Target journeys:** J-06
+- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-07 (full regression — final journey; touches the champion pointer + PnL ledger)
+- **Anti-goal reminders (verbatim from `docs/goal.md`):**
+  - **No live execution path.** Tapeology MUST NOT place, route, or transmit orders anywhere — no brokerage integration, no trading API, **no paper-trading API**, no order tickets. The ONLY permitted "fill" is the offline backtester's simulated fill against recorded historical tape, clearly labelled simulated and sent nowhere; "position size" is a simulated notional, never a real order. *(critical)*
+  - **No profit claims and no advice.** Simulated PnL is a caveated measurement: it MUST always appear with its R counterpart, its n, its fee/slippage assumptions, its train-or-hold-out basis, and its null baseline — never presented as expected live results, an edge claim, or a reason to trade. No imperative cues, no prediction language. *(critical)*
+  - **The tape engine, `default` profile, and `v1` strategy are frozen.** Structure work is additive and versioned only: new bars/levels/classes and the `structure_tape` strategy may be added, but the `default` profile's outputs stay byte-identical (equivalence-tested), the live cockpit uses `default` only, `v1` stays byte-identical, and no enhancement may mutate an archived-era behaviour to pass. *(critical)*
+  - **No train-only promotion.** Nothing becomes the champion on train data alone: hold-out survival (net R AND net $, at the configured minimum n) is the only promotion gate; overfit results are labelled overfit. *(critical)*
+  - **No lookahead.** Levels and classes computed "as of" time T use only bars at or before T; a backtest may never see a level derived from data after the moment it is used. *(critical)*
+  - **No ML, no online tuning.** S/R detection, confluence scoring, class thresholds, and class-based risk are bounded, config-enumerated, offline, and deterministic; no fitted models, no optimizer loops in the engine, no thresholds that move at runtime.
+  - **No fabricated data — honest failure states.** No synthesized bars, levels, trades, fills, or PnL to force a green journey; every failure mode (backend down, corrupt file, empty window, missing credentials, rate-limited, no levels found, insufficient n) surfaces an explicit, distinct state. *(critical)*
+  - **Single source of truth.** Every canonical value — bar series, levels, confluence classes, backtest aggregates, PnL rows — is computed once and read verbatim by every surface (REST, WebSocket, UI, MCP, reports). A second computation path or a diverging number across surfaces is a defect. *(critical)*
+  - **No capital or portfolio management.** Class "position size" is a per-trade simulated notional only — no account, no equity curve, no compounding projection, no real position tracking. *(critical)*
+  - **MCP is read-only.** The MCP server exposes no mutating tools, proxies only the canonical GET surface (plus the allowlisted `get_endpoint`), and MUST NOT become a second implementation of any computation. *(critical)*
+  - **Persistence stays scoped.** SQLite holds research records; the bar and dataset stores hold explicitly recorded historical bars and tape for research replay. The live cockpit's tape remains unpersisted; no ambient recording. *(critical)*
+  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the AUTO:journeys marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a PnL-ledger acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a [NEW]-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*
+
+## GOAL
+
+The era-3 sweep/edge-report path is generalized to measure a **named** strategy — so `structure_tape` is backtested across every registered dataset and compared to the `v1` champion on train AND hold-out — producing a per-split, per-dataset comparison report with a `survivor` flag that is true only on a hold-out win at n ≥ the configured minimum, labelling train-only wins overfit, promoting a genuine survivor by appending exactly one PnL-ledger row and moving the one champion pointer WITHOUT modifying `default`/`v1`/any engine default, and honestly reporting **no survivor at exit 0** on the committed fixtures.
+
+## BACKGROUND
+
+J-06 is the **sole remaining failing journey and the final Must-have** — the goal-completing iteration. It is fully unblocked: iter-5 (evaluator PASS, coherence PASS) shipped J-05 so `structure_tape` now carries its class-scaled stop/reward/size math, and Data-Contract row 43 (named-strategy comparison report) was registered forward at baseline. The generalization rides an existing seam I verified in the code: `pnl_scan.run_sweep` already compares a candidate against the champion per split with a `survivor`/`overfit`/`robustness` gate and a crash-safe two-write promotion — but it pins `strategy_id` to the champion's and varies only `profile`; `BacktestJobManager.create` already accepts any registered `strategy_id` (so `structure_tape` needs no new backtest path); and the champion is seeded `{v1, default}`, so "vs the champion" IS "vs v1". Depth is **full**: J-06 is a new canonical computation that touches the **champion pointer (rows 33/40) and the PnL ledger (row 32)** — frozen-foundation artifacts — through a promotion path, its load-bearing correctness is the critical **"no train-only promotion"** anti-goal (a thorough audit is warranted before any GOAL_ACHIEVED), and as the pre-completion gate it warrants a full regression. This matches the iter-5 evaluator's explicit next-step recommendation.
+
+## IN SCOPE
+
+### Backend
+- [ ] **Generalize the ONE existing sweep (`apps/backend/app/research/pnl_scan.py`, Data-Contract row 43/36) to evaluate a NAMED candidate strategy** (`structure_tape`) against the current champion (`v1`/`default`) — reusing the SAME `BacktestJobManager.create` + `run_sync` computation path (never a second net R/$/edge computation) and the SAME `_dataset_rows`/`_split_summary`/`_is_positive`/`_promote` machinery. Add a **strategy axis** to the existing profile axis: the CLI gains a way to name the candidate strategy (e.g. `--strategy structure_tape`); the candidate backtest runs at `strategy_id=structure_tape`, `profile=default` and is compared to the champion at `strategy_id=v1`, `profile=default`. With NO named-strategy argument, the existing profile sweep (row 36 / J-07-adjacent) behaves **byte-identically** — backward compatible.
+- [ ] The comparison report records, **per split (train, hold-out), never pooled**: `structure_tape`'s and `v1`'s net R AND net $, n, the per-dataset breakdown, and the candidate-minus-champion deltas — the SAME `_split_summary` shape generalized to the strategy axis.
+- [ ] The **`survivor` flag reuses the existing gate verbatim**: true iff the summed hold-out delta is positive on BOTH net R AND net $ AND the summed hold-out candidate n ≥ `Config.promotion_min_sample_size` (**reuse the existing field — add NO new min-n field**). `overfit` = positive train AND NOT survivor. `robustness` (robust/speculative) unchanged.
+- [ ] **Promotion of a genuine hold-out survivor reuses the existing crash-safe two-write order**: append EXACTLY ONE PnL-ledger row via `pnl_ledger.append_validation_row` (the ONE writer, row 32) THEN move the ONE row-33/40 champion pointer via `store.set_champion_pointer` — **generalized to move the strategy axis** (`strategy_id=structure_tape`, keeping `profile=default`) rather than the profile axis. The move is a **pointer write only**: it MUST NOT modify `default`, `v1`, or any engine default. The `enhancement_id` distinctly names the named-strategy promotion (e.g. `structure_tape-over-v1`).
+- [ ] **Honest fixture outcome**: on the committed train/hold-out fixture pair, `structure_tape`'s hold-out n is below `promotion_min_sample_size` (2-timeframe bar fixture → mostly class-C, few trades — iter-3 lesson), so there is **no survivor** → no promotion → champion stays `{v1, default}` → the CLI exits 0 with an honest "no survivor" report. Nothing written to the ledger, pointer unmoved.
+- [ ] **Determinism**: the comparison report carries no wall-clock / per-run-random field (the existing `_render_report` sorted-key discipline); two independent fresh-state runs on the fixtures produce **byte-identical** `--out` bytes.
+- [ ] **Resolve audit item B1 by disclosure** (NOT by re-arming): the breakthrough arm is a static price-position test, not a fresh event-to-event cross — a sanctioned but loose anchor that inflates breakthrough-arm frequency. Because tightening it would perturb the frozen-ish J-04/J-05 arming (a second risky change in the goal-completing iteration), resolve B1 by **explicitly disclosing the loose-anchor caveat in the comparison report's provenance/assumptions** so the `structure_tape`-vs-`v1` edge number is not silently inflated. (Tightening the arm is allowed ONLY if it provably keeps J-04/J-05 byte-identical — otherwise disclose.)
+- [ ] Extend `tests/test_no_execution_path.py`'s grep-guard to cover any new comparison/promotion code — no broker/order/routing/execution/paper-trading identifier is introduced; the champion move is a pointer write, not an order.
+- [ ] **Prefer adding NO new `Config` field.** Reuse `promotion_min_sample_size`, `pnl_min_sample_size`, and `PROFILE_DEFAULT`. If a config-owned parameter is genuinely required, it MUST be added to the `config_fingerprint` `excluded` set (iter-1 lesson) so the pinned `default`/`v1` fingerprint `4d665603569b9dbf` does not move.
+
+### Frontend (if applicable)
+- None. This is a machine surface (CLI report + existing REST/MCP reads); `apps/frontend/` MUST NOT be touched (iter-0 lesson: a zero frontend diff is what keeps J-07's cockpit leg green without a new screenshot).
+
+### New user-facing capability
+An operator (or an agent, read-only via MCP) can run the sweep to measure whether `structure_tape` beats the `v1` champion on **held-out** data — and, only if it genuinely survives hold-out at n ≥ the minimum, promote it to champion with a full audit trail (one ledger row + a moved pointer). On the committed fixtures the honest answer is "no survivor," champion unmoved.
+
+### New information displayed
+A named-strategy comparison report (`structure_tape` vs `v1` per split: net R AND net $, n, per-dataset breakdown + deltas, `survivor`/`overfit`/`robustness`, `champion_before`/`champion_after`) written to the CLI `--out` file; and, only on a genuine promotion, one new row on the existing `GET /research/pnl/ledger` (row 32) plus a moved champion visible via the existing `GET /research/profiles` / `GET /research/strategies` (rows 33/40). On the fixtures: the report's honest "no survivor," champion `{v1, default}` unmoved.
+
+### New user actions
+None (CLI + read-only REST/MCP; no new buttons/forms/controls). The only "action" is invoking the generalized sweep CLI with the named strategy.
+
+### UI surface changes
+None (no nav/page change; blueprint Information Architecture unchanged — machine surface only).
+
+### Product surface delta
+The measurement machine — which in era 3 could only sweep candidate **profiles** at a fixed strategy — can now A/B a named **strategy** (`structure_tape`) against the champion (`v1`) on hold-out, under the same honesty guards and the same hold-out promotion gate. This is the era's final capability: it makes the founding question — *does the tape read become profitable when anchored to price structure?* — answerable honestly, with no thumb on the scale.
+
+### Blueprint conformance
+**No new surfaces.** The named-strategy comparison (row 43) lives at its already-registered canonical home — the CLI `pnl_scan`/`edge_report` `--out` report + the existing `GET /research/pnl/ledger` (row 32) + the one champion pointer (rows 33/40). Nav skeleton (Cockpit · Journal · Studies · Performance) unchanged; the report is a machine surface with no nav home, exactly as the blueprint lists it. No `blueprint.reapproval-requested` this iteration.
+
+### Data-contract additions
+**None new.** J-06 realizes **row 43** (Named-strategy comparison report), already registered at baseline in `blueprint.md`, whose owner (the SAME row-36 `pnl_scan` / row-37 `edge_report` path, *generalized to a named strategy* — reusing the ONE `BacktestJobManager`, never a second R/$/edge computation) and serving surface (`--out` report file + row-32 PnL-ledger row + row-33/40 champion pointer) are unchanged. No new displayed value, no new computing module, no new serving endpoint → **no `blueprint.md` edit this iteration**. Any config field (if genuinely required) is a parameter of row 43's existing owner, not a new served value.
+
+## OUT OF SCOPE
+
+- A NEW comparison/promotion module or a NEW endpoint — the named-strategy comparison EXTENDS the existing `pnl_scan` (single owner of the promotion path); a second computer of net R/$/edge is a single-source-of-truth violation and a coherence FAIL.
+- A SECOND champion pointer or a SECOND min-n field — reuse the ONE row-33/40 pointer and the existing `promotion_min_sample_size`.
+- Any change to `v1`, the `default` profile, the tape engine, the live cockpit, or any engine default (all frozen; byte-identical; the promotion is a pointer move only).
+- Tightening the breakthrough arm (audit B1) into a fresh event-to-event cross IF it would perturb J-04/J-05 arming — resolved by **disclosure** in the report provenance instead (see IN SCOPE; tightening allowed only if J-04/J-05 stay byte-identical).
+- Any REAL promotion on the committed fixtures — n is below the minimum, so the honest outcome is no-survivor; the promotion PATH is exercised only by synthetic ≥-min-n fixtures in tests.
+- A required generalization of `edge_report.py` — OPTIONAL and, if done, strictly read-only (no promotion). The survivor comparison + promotion IS the sweep (`pnl_scan`); the DoD does not depend on touching `edge_report`.
+- Any new REST endpoint, nav, or page; any UI change; any real position/account/portfolio/equity/compounding concept (the comparison measures simulated PnL only).
+
+## DEFINITION OF DONE
+
+- [ ] **J-06 passes:** running the generalized sweep with the named `structure_tape` strategy produces a report recording, per split (train + hold-out), `structure_tape`-vs-`v1` net R AND net $, n, and a per-dataset breakdown, with a `survivor` flag true iff `structure_tape` beats the champion on **hold-out** net R AND net $ at n ≥ `promotion_min_sample_size` — verified by the J-06 acceptance suite (exit 0).
+- [ ] **Overfit is labelled and never promoted:** a positive-train / failing-hold-out synthetic fixture yields `overfit=true`, `survivor=false`, and NO promotion (champion unmoved, no ledger row).
+- [ ] **A genuine hold-out survivor promotes correctly:** a synthetic ≥-min-n survivor fixture appends EXACTLY ONE PnL-ledger row (row 32) THEN moves the ONE row-33/40 champion pointer to `strategy_id=structure_tape` — and `default`, `v1`, and every engine default are byte-identical after (`config_fingerprint()=='4d665603569b9dbf'` unmoved; `tests/test_profile_equivalence.py` green; engine equivalence green).
+- [ ] **Honest fixture outcome:** on the committed fixtures (hold-out n below `promotion_min_sample_size`) the CLI reports "no survivor," champion stays `{v1, default}`, exits 0, and writes nothing to the ledger / moves no pointer.
+- [ ] **Deterministic re-runs:** two independent fresh-state runs on the fixtures produce byte-identical `--out` bytes.
+- [ ] **Single source of truth:** every backtest goes through the ONE `BacktestJobManager` (source-scan test — no second net R/$/edge computation); `store.set_champion_pointer` is still called from exactly one source file.
+- [ ] **No live execution path:** extended `tests/test_no_execution_path.py` green over the comparison/promotion code (no broker/order/routing/execution/paper-trading identifier; the champion move is a pointer write).
+- [ ] **Audit B1 resolved:** the breakthrough arm's loose-anchor assumption is explicitly disclosed in the comparison report's provenance/assumptions (or tightened only if J-04/J-05 stay byte-identical).
+- [ ] **Backward compatibility:** the existing profile sweep (no named strategy) behaves byte-identically (row 36 unchanged).
+- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-07 remain green (deterministic replay + full backend suite).
+- [ ] No anti-goal violation introduced (scan-report CLEAN; coherence PASS).
+- [ ] Unit tests pass; full backend suite green; no regressions.
+- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit_support_resistence-iter-6-dev.md`, listing ALL files changed (including any doc edits).
+
+## TESTING REQUIREMENTS
+
+- **Browser:** none required (machine surface; Frontend Present: no). J-07's cockpit/frozen-surface leg is covered by deterministic replay + engine equivalence because `apps/frontend/` is untouched (iter-0 lesson: zero frontend diff → no new screenshot owed).
+- **Unit/integration (this IS the acceptance for a machine surface):**
+  - **Named-strategy comparison shape:** per split, `structure_tape` and `v1` net R AND net $, n, per-dataset breakdown + deltas; train and hold-out never pooled.
+  - **Survivor gate on the strategy axis:** (a) a below-min-n hold-out win is NOT a survivor; (b) an at/above-min-n positive hold-out win IS a survivor — using synthetic fixtures (a controlled ≥-min-n survivor + a below-min-n case), mirroring the existing `tests/test_pnl_scan.py` min-n tests.
+  - **Overfit:** positive train + failing hold-out → labelled overfit, never promoted.
+  - **Promotion correctness + crash safety:** exactly ONE ledger row appended THEN the pointer moved to `strategy_id=structure_tape`; a mid-promotion re-run hits the existing `DuplicateEnhancementError` → explicit `ScanError` (no silent double-append, no orphan).
+  - **Frozen foundation AFTER a promotion:** fingerprint `4d665603569b9dbf` unmoved, `v1`/`default` byte-identical, engine equivalence green — a promotion moves the pointer only, mutating no strategy/profile/engine default.
+  - **Fixture honesty:** the committed train/hold-out fixture pair yields no survivor, champion unmoved, exit 0.
+  - **Determinism:** byte-identical `--out` re-run on the fixtures.
+  - **Backward compatibility:** the existing profile sweep (no named strategy) reproduces byte-identically.
+  - **Single-source scan:** champion-pointer setter called from exactly one source file; no second net R/$/edge computation path.
+- **Error cases / honest states:**
+  - Corrupt dataset / non-`done` backtest → explicit `ScanError`, nothing written, nothing promoted.
+  - Unknown candidate strategy id → explicit refusal (never a coerced/fabricated comparison).
+  - More than one train or one hold-out dataset registered → promotion explicitly skipped with an honest note (existing `append_validation_row` shape), the comparison still fully reported.
+  - Grep-guard: no broker/order/routing/execution/paper-trading identifier introduced.
+
+## NOTES
+
+- **Depth = full** justified by (Picking-depth triggers): J-06 touches the data model / sensitive foundation artifacts — the **champion pointer (rows 33/40) and PnL ledger (row 32)** — via a promotion path; its load-bearing correctness is the critical **"no train-only promotion"** anti-goal (needs a full audit); and as the **goal-completing** journey a full regression + audit is warranted before any GOAL_ACHIEVED. Prior verdict was CONTINUE (not ESCALATE); full is chosen by the data-model/champion-pointer trigger and matches the iter-5 evaluator's explicit recommendation.
+- **Lessons applied (surface to developer / reviewer / evaluator):**
+  - *iter-5:* (1) do NOT silently break `_class_scaled_invalidation`'s level-relative-vs-entry-relative fallback when re-backtesting `structure_tape` for the comparison; (2) the DoD's "per train/hold-out split" is satisfied by **dataset provenance** — one backtest = one dataset carrying one frozen `split` tag — so the cross-split comparison IS J-06 (comparing the train-summary vs hold-out-summary aggregates), NOT a second split axis inside a single backtest report. Don't over-build a two-axis breakdown.
+  - *iter-4 audit B1:* the breakthrough arm is a static price-position test, not a fresh event-to-event cross — a sanctioned but loose anchor that inflates breakthrough-arm frequency and materially affects the `structure_tape`-vs-`v1` edge number → resolve by **explicit disclosure** in the report provenance (tighten only if J-04/J-05 stay byte-identical).
+  - *iter-3:* the committed PG bar fixture holds only two timeframes (1h, 1d) → mostly class-C, few `structure_tape` trades → the fixture comparison honestly yields no survivor (n below the minimum). Class-A / above-min-n survivor cases MUST use **synthetic** fixtures, never the committed PG fixture.
+  - *iter-1:* `config.py` is vendor-name-forbidden even in comments; ANY new `Config` field must join the `config_fingerprint` `excluded` set or the pinned `4d665603569b9dbf` moves and J-07 breaks — **prefer reusing** `promotion_min_sample_size` / `pnl_min_sample_size` / `PROFILE_DEFAULT` and adding none.
+- The champion is seeded `{v1, default}` (`store.py::_ensure_champion_pointer_seeded`, idempotent — never overwrites a promoted pointer), so "`structure_tape` vs the champion" IS "`structure_tape` vs `v1`" on a fresh/foundation store. `v1` "loses money" on real tape (the era-3 finding), so a genuine hold-out win by `structure_tape` is precisely the era-4 hypothesis under honest test — with the fixtures honestly returning no survivor.
+- **Doc-parity rider (minor):** update the README / relevant docs so the shipped named-strategy comparison capability and the honest "no survivor on the fixtures" finding are documented, and ensure the iter-5 incidental README note plus all iter-6 doc edits are listed in the dev handoff's Files Changed.
+- **GOAL_ACHIEVED note:** J-06 is the FINAL Must-have; only the **evaluator** (not this planner, and only after the deterministic gates + two-key confirm) may declare GOAL_ACHIEVED. This spec marks no journey passing.
+- **Target selection followed the rubric with no deviation:** no regressions (rule 1 N/A); iter-5 coherence PASS so no consolidation owed (rule 2 N/A); J-06 is the SOLE remaining failing journey — the goal-completing pick — carried alone as ONE risky change (rule 5 respected: B1 resolved by disclosure to avoid a second risky arming change in the same diff).
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-6-closure-verdict.md breports/phase-goal-tape_to_profit_support_resistence-iter-6-closure-verdict.md
new file mode 100644
index 0000000..02b369c
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-6-closure-verdict.md
@@ -0,0 +1,72 @@
+# Phase goal-tape_to_profit_support_resistence-iter-6 — Closure Verdict
+
+**Phase:** goal-tape_to_profit_support_resistence-iter-6
+**Date:** 2026-07-06
+**Written by:** phase-closure-auditor
+
+---
+
+**Verdict:** CLOSURE-PASS
+
+---
+
+## Standard Pipeline Gate Checks
+
+| Artifact | Status | Verdict |
+|----------|--------|---------|
+| Review report (`reports/reviews/goal-tape_to_profit_support_resistence-iter-6-review.md`) | exists | PASS |
+| QA report (`reports/qa/goal-tape_to_profit_support_resistence-iter-6-qa.md`) | exists | PASS |
+| Audit report (`docs/handoffs/goal-tape_to_profit_support_resistence-iter-6-audit.md`) | exists | PASS |
+
+All three standard pipeline gates are present and carry an accepted verdict:
+- Review: `**Verdict:** PASS` — summary confirms 42/42 targeted tests green, full backend suite exit 0, two live CLI runs byte-identical, grep-guard clean, `config.py`/`store.py`/frontend untouched.
+- QA: `**Verdict:** PASS` — full backend suite 1146 passed / 1 skipped / 0 failed; 21 pnl_scan + 6 no_execution_path + 15 profile_equivalence subset all green; browser checks explicitly SKIPPED with documented reason (backend-only phase).
+- Audit: `**Verdict:** PASS` — independent re-verification of the promotion gate, crash-safety ordering, frozen-foundation byte-identity (`config_fingerprint() == "4d665603569b9dbf"` unmoved), and live CLI determinism. Three OBSERVATION-level notes recorded (none CRITICAL/IMPORTANT); no fixes required.
+
+---
+
+## UI Visibility Artifact Checks
+
+`Frontend Present: no` (confirmed in both `runs/goal-tape_to_profit_support_resistence-iter-6/plan.md` line 3 and the phase spec's Goal Mode Metadata). Per the phase-closure-gate skill, all 6 files must exist; N/A stubs are acceptable.
+
+| Artifact | Exists | Non-Empty | Non-Vague | Status |
+|----------|--------|-----------|-----------|--------|
+| implementation-summary.md | yes | yes (85 lines) | yes — real content | OK |
+| user-visible-changes.md | yes | yes (5 lines) | N/A stub, correctly labelled backend-only | OK |
+| ui-surface-map.md | yes | yes (5 lines) | N/A stub, correctly labelled | OK |
+| ui-test-plan.md | yes | yes (3 lines) | N/A stub, correctly labelled | OK |
+| ui-test-results.md | yes | yes (5 lines) | SKIPPED with documented reason | OK |
+| what-to-click.md | yes | yes (3 lines) | N/A stub, correctly labelled | OK |
+
+`implementation-summary.md` is not a bare stub — it documents Features Implemented, Changed Behavior, an explicit "Backend-Only Items" section, Incomplete Items (none), Config/Environment changes (none), and Known Limitations, all in plain (non-jargon) language consistent with the dev handoff and audit.
+
+---
+
+## Cross-Reference Checks
+
+- [x] user-visible-changes lists ≥1 specific capability (or N/A for backend-only) — correctly marked N/A, consistent with `Frontend Present: no`.
+- [x] ui-surface-map has specific route/component entries (or N/A) — correctly marked N/A ("No UI surfaces affected").
+- [x] ui-test-plan has specific steps with exact actions and expected results (or N/A) — correctly marked N/A.
+- [x] ui-test-results shows execution evidence (or SKIPPED with documented reason) — SKIPPED, reason given ("Backend-only phase (Frontend Present: no)").
+- [x] what-to-click has ≥3 numbered steps with exact expected outcomes (or N/A) — correctly marked N/A.
+- [x] implementation-summary claims are consistent with ui-test-results evidence — consistent; implementation-summary's own "Backend-Only Items" section independently states "there is no new screen or button, and none was planned for this iteration," matching the N/A/SKIPPED status of the other five artifacts.
+
+**Independent verification of the `Frontend Present: no` claim** (this gate does not take the label at face value):
+- `git status --porcelain apps/frontend/` → empty output, confirmed directly in this audit.
+- `git diff --stat HEAD -- apps/backend/app/research/pnl_scan.py apps/backend/tests/test_pnl_scan.py apps/backend/tests/test_no_execution_path.py README.md` → matches exactly the dev handoff's "Files Changed" list (4 files, no others).
+- `git diff --stat HEAD -- apps/backend/app/config.py apps/backend/app/research/store.py apps/backend/app/research/pnl_ledger.py apps/backend/app/research/edge_report.py` → empty, confirming the "expected no changes" claim for these frozen-adjacent files.
+- No inconsistency found: this is a genuine backend/CLI-only iteration, not a mislabeled frontend change. The Step 4 "backend-only claim guard" scenario (N/A artifacts hiding a real frontend diff) does not apply here.
+
+---
+
+## Blocking Issues
+
+None.
+
+---
+
+## Non-Blocking Notes
+
+- Three OBSERVATION-level findings recorded in the audit (B1: `overfit=true` on the committed fixture despite `structure_tape` abstaining with n=0 on train — a semantically loose but spec-mandated, non-gating, disclosed label; B2: strategy axis compares against champion at `profile=PROFILE_DEFAULT` rather than `champion["profile"]` — exactly as the spec prescribes; T1: the pre-written QA test plan speculates a CLI/JSON shape — `--splits` flags, `strategy_tape_R`/`v1_R` field names — that the implementation deliberately does not match, triaged consistently by dev/QA/audit as a plan-vs-implementation divergence, not a code defect). None of these block closure; all are disclosed and explained with reasoning that holds up under review.
+- `runs/goal-tape_to_profit_support_resistence-iter-6/status.json` shows `"next_action": "auditor"` with an `updated_at` timestamp (17:26:26Z) that predates the audit report's completion (audit file timestamp 18:24) — a stale status marker from before the audit ran, not a gate failure (the audit report itself, dated 2026-07-06, carries `**Verdict:** PASS`).
+- This iteration is goal-mode's final Must-have (J-06); only the goal-evaluator (a separate, later stage not in this gate's scope) may declare GOAL_ACHIEVED. This closure verdict certifies the standard dev pipeline (review/QA/audit) and UI-visibility artifacts only — it does not itself constitute a goal-achieved determination.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-6-implementation-summary.md breports/phase-goal-tape_to_profit_support_resistence-iter-6-implementation-summary.md
new file mode 100644
index 0000000..a95a79d
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-6-implementation-summary.md
@@ -0,0 +1,85 @@
+# Goal Iteration 6 (J-06) — Implementation Summary
+
+**Phase:** goal-tape_to_profit_support_resistence-iter-6
+**Date:** 2026-07-06
+**Written by:** developer
+
+---
+
+## Features Implemented
+
+- **Named-strategy comparison, run from the command line**: the existing "candidate check" tool
+  (which already compared alternate settings against the current champion) can now instead compare
+  a whole alternate trading strategy — specifically `structure_tape`, the tape-plus-structure
+  strategy built in earlier iterations — against the current champion strategy (`v1`). Ask for it
+  by adding `--strategy structure_tape` when running the tool; leave it off and the tool behaves
+  exactly as it always has, checking alternate settings instead.
+- **Same honesty rules, applied to a whole strategy**: the comparison shows, separately for the
+  training data and for data the strategy has never seen (the "held-out" data — never mixed
+  together), how many simulated trades each side made and what the combined simulated result was,
+  in both "R" (risk-multiple) and dollar terms. A strategy is only promoted to be the new champion
+  if it genuinely beats the current champion on the held-out data, with enough trades to trust the
+  result — a win on the training data alone is honestly labeled "overfit" and is never promoted.
+- **A disclosed measurement caveat**: every comparison report now plainly states a known limitation
+  of how `structure_tape` currently recognizes a "follow-through" (a price break through a level) —
+  it is a slightly looser check than watching for the exact moment of the break, which can make the
+  strategy look like it trades a bit more often than a stricter check would show. This is disclosed
+  in the report rather than silently left for a reader to discover, and it was not changed this
+  iteration (changing it risked disturbing already-tested, tape-confirmed behaviour from earlier
+  iterations).
+- **Honest result on today's sample data**: run against the one small sample dataset currently
+  committed to the project, the comparison honestly reports that `structure_tape` has not yet
+  produced enough held-out trades to trust a result either way — so nothing is promoted, and the
+  champion strategy stays `v1`. This is the correct, honest outcome for a small sample, not a
+  failure of the tool.
+
+## Changed Behavior
+
+- **The candidate-check command-line tool**: previously it could only compare alternate
+  "settings profiles" against the champion (holding the strategy fixed). It now ALSO supports
+  comparing an alternate strategy (holding the settings profile fixed), selected with the new
+  `--strategy` option. Nothing about the existing settings-profile comparison changed — every
+  pre-existing check for that behavior still passes unmodified, proving it is identical to before.
+- **The promotion record ("champion" pointer)**: previously, a promotion could only ever change
+  which settings profile was in use. It can now also change which STRATEGY is in use (if one
+  genuinely earns it via the same held-out test) — but only through this same one honest gate;
+  nothing else about how a promotion is recorded changed.
+
+## Backend-Only Items
+
+- This is entirely a command-line/machine-readable capability, matching how the era-3 measurement
+  tools already worked — there is no new screen or button, and none was planned for this
+  iteration. The result is visible today by reading the tool's output file, or (only if a genuine
+  promotion happens) via the existing Performance page and the existing "who's the champion"
+  API/machine-readable connection, exactly as any other promotion already surfaces.
+
+## Incomplete Items
+
+- None from this iteration's assigned scope. A full, credentialed real-world comparison (using a
+  larger, multi-symbol history rather than the one small committed sample) is a future operator
+  action once real market-data credentials and a bigger recorded history are available — this
+  iteration proves the comparison tool itself works honestly, not that `structure_tape` is (or
+  isn't) actually a better strategy in the real world.
+
+## Config and Environment Changes
+
+- No new environment variables and no new configuration settings were added — the iteration
+  reused every existing setting (the same "enough trades to trust it" threshold, the same
+  default settings profile) rather than inventing new ones, exactly as the plan required.
+- No database migration was needed.
+
+## Known Limitations
+
+- On the one small sample dataset already committed to the project, `structure_tape` makes zero
+  simulated trades on the training slice and exactly one on the held-out slice — both honestly
+  below the "enough trades to trust" floor. This is a known consequence of that sample being short
+  and covering only two price timeframes, carried over from an earlier iteration's finding, not a
+  new issue. A bigger, more realistic comparison needs a bigger recorded history.
+- The scenarios proving a genuine promotion actually works (and the "positive on training data but
+  fails on held-out data" honest-overfit case) were verified using small, purpose-built practice
+  data, not the single real sample already in the project — the same disclosed testing technique
+  used in earlier iterations. It does not change how the tool behaves on real data, only how the
+  behaviour was checked before shipping.
+- The disclosed "follow-through" measurement caveat (see Features Implemented) is a carried-over,
+  pre-existing simplification, not something introduced this iteration — it is now written down
+  plainly in every comparison report rather than left undocumented.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-6-iteration-summary.md breports/phase-goal-tape_to_profit_support_resistence-iter-6-iteration-summary.md
new file mode 100644
index 0000000..ebc5bc0
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-6-iteration-summary.md
@@ -0,0 +1,73 @@
+# Iteration Summary — goal-tape_to_profit_support_resistence-iter-6
+
+**Verdict:** PASS
+**Iteration type:** goal-full
+**Date:** 2026-07-06
+**Iteration:** 6
+
+## In plain words
+
+**What you can do now:** You can type in a stock ticker and watch Tapeology read live trade-by-trade order flow to see whether buyers or sellers are in control, write trading ideas into a journal, run replay studies, and view honest backtest and profit-and-loss results on a Performance page — all delivered in earlier rounds. Behind the scenes, Tapeology is also building a second, experimental way of trading that reacts to real support-and-resistance levels, but that part isn't ready to try in the app yet.
+
+**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The internal tool that checks whether a candidate trading rule beats the current one can now compare a whole alternate strategy — the new zone-aware rule built in recent rounds — against the original rule, honestly, using data the rule has never traded on before. Run against the one small sample of real data available today, it correctly found there isn't enough evidence yet to call a winner, so nothing changes for anyone using the app.
+
+**What's next:** Next, an independent, skeptical check will confirm whether this comparison was genuinely the last piece needed to call the zone-aware trading rule project complete.
+
+## Headline
+
+structure_tape can now be measured against the v1 champion; no survivor yet on the sample data
+
+## Direction
+
+**Signal:** improving
+**Why:** J-06 — the final Must-have journey (`structure_tape` measured honestly against the `v1` champion) — was built end to end this iteration and independently verified: review PASS, QA PASS (13/13 acceptance criteria via code tests, 1146 passed/1 skipped/0 failed), and a hard audit PASS with zero critical/important findings confirming the hold-out-only promotion gate, crash-safe promotion order, and frozen `v1`/`default` byte-identity all hold. The goal-evaluator's formal iter-6 confirmation (which flips journey status and would assess GOAL_ACHIEVED, since J-06 is the last Must-have) had not yet run as of this summary — `journey-history.json` still shows J-06 at its iter-5 "failing" snapshot — but every other gate this iteration passed cleanly with zero regressions and zero anti-goal violations, continuing the same one-journey-per-iteration cadence as the four iterations before it.
+
+**Trend (last 5 iters):**
+- Newly passing this iter: J-06 (build verified this iteration — review/QA/audit all PASS; not yet reflected in `journey-history.json`, goal-evaluator confirmation pending)
+- Newly passing in last 5 iters total: J-02, J-03, J-04, J-05, J-06 (J-06 pending goal-evaluator confirmation)
+- Regressions in last 5 iters: none
+- Anti-goal violations in last 5 iters: none
+- Iters with no journey state change: 0 of last 5
+
+**Latest evaluator reasoning:** (most recent available — iter-6's goal-evaluator entry had not yet been written as of this summary; quoting the iter-5 entry) "J-05 (class-scaled stop/reward/simulated size + per-class PnL breakdown) is newly passing, verified end to end on a machine surface (browser QA correctly SKIPPED; acceptance = backend suite). `structure_tape` now sizes and stops each simulated entry by its arming level's A/B/C class and exposes a per-class breakdown served verbatim by the existing `GET /research/backtests/{id}` + MCP — all config-owned, single-sourced, and with the frozen v1/`default` fingerprint `4d665603569b9dbf` proven unmoved. J-06 remains the sole failing journey (correctly out of scope this iter) and is now fully unblocked. No regressions, no anti-goal violations, coherence PASS → CONTINUE toward J-06."
+
+## What was done
+
+- Added a `--strategy` axis to `pnl_scan.py`'s existing candidate sweep — compares a NAMED strategy (`structure_tape`) against the champion (currently `v1`) at `profile=default`, reusing `_dataset_rows`/`_split_summary`/`_is_positive`/`_promote` verbatim; omitting the flag keeps the pre-existing profile-axis sweep byte-identical (all 12 prior tests pass unmodified)
+- Comparison report records net R and net $ per split (train, hold-out — never pooled), plus a per-dataset breakdown and deltas; `survivor` is true only on a hold-out win at n ≥ `promotion_min_sample_size`; train-only wins are labelled `overfit` and never promoted
+- Generalized `_promote` to move the champion pointer to `{strategy_id: structure_tape, profile: default}` on a genuine survivor, via the existing crash-safe two-write order (ledger row, then pointer) — verified `v1`/`default` byte-identical and the pinned fingerprint `4d665603569b9dbf` unmoved after a real promotion
+- Disclosed audit item B1 (the breakthrough arm's loose static-price-position anchor) as a `provenance.assumptions` note on every report, instead of re-arming the detector — avoiding a second risky change alongside the goal-completing iteration
+- On the committed fixtures: `structure_tape` trades 0 times on train, 1 on hold-out — both below the promotion minimum — so the CLI honestly reports "no survivor," exits 0, champion stays `{v1, default}`, nothing written to the ledger
+- Added 9 new tests to `test_pnl_scan.py` (comparison shape, survivor/overfit gating both ways, promotion + crash-safety, frozen-foundation check, determinism, backward compatibility, unknown-strategy refusal) and 1 new grep-guard test in `test_no_execution_path.py`; full backend suite 1146 passed / 1 skipped / 0 failed (+10 from baseline, zero regressions)
+- Browser QA correctly SKIPPED (backend-only iteration, zero `apps/frontend/` diff) — acceptance verified entirely via the backend test suite, matching this journey's machine-surface nature
+- Review PASS, QA PASS (13/13 acceptance criteria via code tests), Audit PASS (0 critical/important findings, 3 observation-level), Closure CLOSURE-PASS; README doc-parity updated for the new comparison capability
+
+## What's left
+
+- Journey J-06 (`structure_tape is measured honestly against the v1 champion`) still shows `failing` in `journey-history.json` (last refreshed at iter-5) — the build itself is independently verified complete this iteration (review PASS, QA PASS, audit PASS), but only the goal-evaluator's formal iter-6 pass can flip journey status and determine whether GOAL_ACHIEVED is reached, since J-06 is the final Must-have journey
+- On the committed fixtures, `structure_tape` trades below the promotion minimum on both splits (0 on train, 1 on hold-out) — a genuine edge verdict needs a credentialed, larger multi-symbol/multi-regime history, not yet available
+- `edge_report.py` remains unchanged (optional per spec) — it still evaluates only the champion strategy, not a named-strategy comparison
+- Minor: the pre-written QA test plan speculated a CLI/JSON shape (`--splits` flags, `strategy_tape_R` field names) that the shipped implementation deliberately does not match — a documentation-plan divergence already triaged by dev/QA/audit, not a code defect
+- Minor operational note (unrelated to this iteration's code): `scripts/dev.sh`'s process-kill step doesn't reliably reap every child process (Next.js's `next-server`, uvicorn's `--reload` worker) — flagged for operator awareness
+
+## Next step
+
+No `eval.md` exists yet for this iteration, so there is no goal-evaluator Next-Step Recommendation to carry forward verbatim, and the closure verdict is CLOSURE-PASS with no blocking issues to remediate. The most defensible next step, per the audit's own recommendation ("this iteration is ready for the goal-evaluator to run its deterministic gates and two-key confirm for a GOAL_ACHIEVED decision — only the evaluator may declare it"), is to run the goal-evaluator against this iteration's artifacts: confirm J-06 (`structure_tape` measured honestly against the `v1` champion), re-verify the pinned fingerprint `4d665603569b9dbf` and `v1`/`default` byte-identity one more time, and determine whether every Must-have journey — J-06 being the last — now passes.
+
+## Artifacts
+
+| Report | Verdict | Path |
+|--------|---------|------|
+| Iter spec | — | docs/phases/goal-tape_to_profit_support_resistence-iter-6.md |
+| Dev handoff | — | docs/handoffs/goal-tape_to_profit_support_resistence-iter-6-dev.md |
+| Review | PASS | reports/reviews/goal-tape_to_profit_support_resistence-iter-6-review.md |
+| Browser QA | SKIPPED | reports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-test-results.md |
+| Implementation summary | — | reports/phase-goal-tape_to_profit_support_resistence-iter-6-implementation-summary.md |
+| User-visible changes | — | reports/phase-goal-tape_to_profit_support_resistence-iter-6-user-visible-changes.md |
+| What to click | — | reports/phase-goal-tape_to_profit_support_resistence-iter-6-what-to-click.md |
+| UI surface map | — | reports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-surface-map.md |
+| UI test plan | — | reports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-test-plan.md |
+| QA | PASS | reports/qa/goal-tape_to_profit_support_resistence-iter-6-qa.md |
+| Audit | PASS | docs/handoffs/goal-tape_to_profit_support_resistence-iter-6-audit.md |
+| Closure | CLOSURE-PASS | reports/phase-goal-tape_to_profit_support_resistence-iter-6-closure-verdict.md |
+| Journey history | — | runs/goal-session-tape_to_profit_support_resistence/state/journey-history.json |
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-6-summary.html breports/phase-goal-tape_to_profit_support_resistence-iter-6-summary.html
new file mode 100644
index 0000000..ef50029
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-6-summary.html
@@ -0,0 +1,358 @@
+<!doctype html>
+<html lang="en"><head>
+<meta charset="utf-8">
+<title>goal-tape_to_profit_support_resistence-iter-6 — Iteration Summary</title>
+<style>
+*, *::before, *::after { box-sizing: border-box; }
+body {
+  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
+  margin: 0; padding: 0; color: #1f2328; background: #f6f8fa; line-height: 1.5;
+}
+.container { max-width: 880px; margin: 0 auto; padding: 24px 16px 80px; }
+.hero {
+  background: white; border: 1px solid #d0d7de; border-radius: 8px;
+  padding: 28px; margin-bottom: 16px; text-align: center;
+}
+.hero.pass { border-top: 6px solid #1a7f37; }
+.hero.fail { border-top: 6px solid #cf222e; }
+.hero.inprogress { border-top: 6px solid #d4a72c; }
+.hero h1 { margin: 0 0 6px 0; font-size: 1.6rem; }
+.hero h2 { margin: 0 0 14px 0; font-size: 1rem; color: #57606a; font-weight: 500; }
+.badge-row { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-bottom: 10px; }
+.badge {
+  display: inline-flex; align-items: center; gap: 8px;
+  padding: 6px 14px; border-radius: 999px; font-weight: 600; font-size: 0.95rem;
+}
+.badge.pass { background: #dafbe1; color: #1a7f37; }
+.badge.fail { background: #ffebe9; color: #cf222e; }
+.badge.inprogress { background: #fff8c5; color: #9a6700; }
+.signal-badge { padding: 6px 14px; border-radius: 999px; font-weight: 600; font-size: 0.9rem; }
+.signal-badge.improving { background: #dafbe1; color: #1a7f37; }
+.signal-badge.holding { background: #ddf4ff; color: #0969da; }
+.signal-badge.stalling { background: #fff8c5; color: #9a6700; }
+.signal-badge.regressing { background: #ffebe9; color: #cf222e; }
+.signal-badge.na { background: #f6f8fa; color: #57606a; }
+.meta { color: #57606a; font-size: 0.875rem; margin: 10px 0 16px; }
+.journey-row {
+  display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin: 12px 0 4px;
+}
+.journey-pill {
+  display: inline-flex; align-items: center; gap: 6px;
+  padding: 4px 10px; border-radius: 999px; font-size: 0.85rem;
+  background: #f6f8fa; border: 1px solid #d0d7de;
+}
+.journey-pill.passing, .journey-pill.already_passing { background: #dafbe1; color: #1a7f37; border-color: #b4e2c0; }
+.journey-pill.failing, .journey-pill.regressed { background: #ffebe9; color: #cf222e; border-color: #f1aeb0; }
+.journey-pill.partial { background: #fff8c5; color: #9a6700; border-color: #eed888; }
+.journey-pill.unknown { background: #f6f8fa; color: #57606a; }
+.hero-image { margin-top: 18px; }
+.hero-image img { max-width: 100%; height: auto; border-radius: 6px; border: 1px solid #d0d7de; }
+details {
+  background: white; border: 1px solid #d0d7de; border-radius: 8px;
+  margin-bottom: 12px;
+}
+details > summary {
+  cursor: pointer; padding: 14px 18px; font-weight: 600; font-size: 1.05rem;
+  list-style: none; user-select: none; display: flex; align-items: center; gap: 8px;
+}
+details > summary::-webkit-details-marker { display: none; }
+details > summary::before {
+  content: '▶'; transition: transform 0.15s; font-size: 0.75rem; color: #57606a;
+}
+details[open] > summary::before { transform: rotate(90deg); }
+.accordion-body { padding: 0 18px 18px; }
+.accordion-body h3 { font-size: 0.95rem; color: #57606a; margin: 16px 0 6px; }
+.why-text { background: #f6f8fa; padding: 10px 12px; border-radius: 6px; margin: 4px 0 12px; }
+ul.bullets { margin: 6px 0 14px; padding-left: 22px; }
+ul.bullets li { margin-bottom: 4px; }
+ol.steps { padding-left: 0; list-style: none; counter-reset: step; }
+ol.steps > li {
+  counter-increment: step; padding: 12px 0 12px 44px;
+  border-top: 1px solid #eaeef2; position: relative;
+}
+ol.steps > li:first-child { border-top: none; }
+ol.steps > li::before {
+  content: counter(step); position: absolute; left: 0; top: 14px;
+  width: 30px; height: 30px; border-radius: 50%;
+  background: #0969da; color: white; display: flex;
+  align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 600;
+}
+.step-shot { margin-top: 10px; }
+.step-shot img { max-width: 100%; height: auto; border-radius: 6px; border: 1px solid #d0d7de; }
+.next-step-box {
+  background: #ddf4ff; padding: 12px 16px; border-radius: 6px;
+  border-left: 4px solid #0969da; margin: 12px 0;
+}
+.drill-table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
+.drill-table th, .drill-table td {
+  text-align: left; padding: 8px 6px; border-bottom: 1px solid #eaeef2;
+}
+.drill-table th { background: #f6f8fa; }
+.verdict-cell.PASS, .verdict-cell.CLOSURE-PASS, .verdict-cell.GOAL_ACHIEVED { color: #1a7f37; font-weight: 600; }
+.verdict-cell.FAIL, .verdict-cell.CLOSURE-FAIL, .verdict-cell.REGRESSION { color: #cf222e; font-weight: 600; }
+.verdict-cell.CONTINUE, .verdict-cell.ESCALATE, .verdict-cell.STALLED { color: #9a6700; font-weight: 600; }
+.verdict-cell.SKIPPED, .verdict-cell.UNKNOWN, .verdict-cell.IN-PROGRESS { color: #57606a; }
+.footer-note { text-align: center; color: #6e7781; font-size: 0.8rem; margin-top: 24px; }
+.iter-card {
+  background: white; border: 1px solid #d0d7de; border-radius: 8px;
+  padding: 16px 18px; margin-bottom: 12px; display: flex; align-items: center; gap: 14px;
+}
+.iter-card .left { flex-shrink: 0; }
+.iter-card .body { flex: 1 1 auto; }
+.iter-card .body .title { font-weight: 600; }
+.iter-card .body .sub { color: #57606a; font-size: 0.88rem; margin-top: 2px; }
+.iter-card a.open { color: #0969da; text-decoration: none; font-weight: 500; }
+.iter-card a.open:hover { text-decoration: underline; }
+.matrix { width: 100%; border-collapse: collapse; margin: 12px 0 22px; font-size: 0.88rem; }
+.matrix th, .matrix td { padding: 6px 8px; border: 1px solid #d0d7de; text-align: center; }
+.matrix th:first-child, .matrix td:first-child { text-align: left; }
+.matrix .cell-passing, .matrix .cell-already_passing { background: #dafbe1; color: #1a7f37; }
+.matrix .cell-failing, .matrix .cell-regressed { background: #ffebe9; color: #cf222e; }
+.matrix .cell-partial { background: #fff8c5; color: #9a6700; }
+.matrix .cell-unknown { background: #f6f8fa; color: #57606a; }
+.no-summary {
+  background: #fff8c5; border: 1px solid #eed888; padding: 14px 18px;
+  border-radius: 8px; color: #9a6700; margin-bottom: 14px;
+}
+/* Plain-language layer — the primary, non-technical view. */
+.plain-words {
+  background: linear-gradient(180deg, #ffffff 0%, #f6fbff 100%);
+  border: 1px solid #d6e4f0; border-radius: 10px;
+  padding: 22px 24px; margin: 18px 0 6px;
+  box-shadow: 0 1px 2px rgba(20, 40, 80, 0.04);
+}
+.plain-words .pw-heading {
+  margin: 0 0 14px; font-size: 1.15rem; color: #0969da;
+  text-transform: uppercase; letter-spacing: 0.05em;
+}
+.pw-grid {
+  display: grid; gap: 14px;
+  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
+}
+.pw-card {
+  background: white; border-radius: 8px; padding: 14px 16px;
+  border: 1px solid #e3eaf3;
+}
+.pw-card .pw-label {
+  font-size: 0.78rem; font-weight: 600; color: #57606a;
+  text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 6px;
+}
+.pw-card .pw-text {
+  margin: 0; font-size: 1rem; color: #1f2328; line-height: 1.45;
+}
+.pw-empty { color: #8c959f; font-style: italic; font-size: 0.95rem; }
+.tech-divider {
+  margin: 18px 0 8px; text-align: center;
+  color: #6e7781; font-size: 0.82rem; font-style: italic;
+  border-top: 1px dashed #d0d7de; padding-top: 12px;
+}
+/* Watch-it-work — narrated screenshot gallery from demo-narrator. */
+.watch-it-work {
+  background: white; border: 1px solid #d6e4f0; border-radius: 10px;
+  padding: 18px 22px; margin: 10px 0 6px;
+}
+.wiw-head {
+  display: flex; align-items: center; justify-content: space-between;
+  gap: 12px; margin-bottom: 14px; flex-wrap: wrap;
+}
+.wiw-heading {
+  margin: 0; font-size: 1.05rem; color: #0969da;
+  text-transform: uppercase; letter-spacing: 0.05em;
+}
+.demo-badge {
+  font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 12px;
+  border: 1px solid transparent; letter-spacing: 0.04em;
+}
+.demo-badge.demo-recorded { background: #dafbe1; color: #1a7f37; border-color: #aceebb; }
+.demo-badge.demo-notes    { background: #fff8c5; color: #9a6700; border-color: #e8d97e; }
+.demo-badge.demo-skipped  { background: #f6f8fa; color: #57606a; border-color: #d0d7de; }
+.demo-badge.demo-pending  { background: #ddf4ff; color: #0969da; border-color: #b6e3ff; }
+.demo-grid {
+  display: grid; gap: 14px;
+  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
+}
+.demo-step {
+  margin: 0; padding: 12px; background: #f6f8fa;
+  border: 1px solid #d0d7de; border-radius: 8px;
+}
+.demo-step-head {
+  display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
+  font-size: 0.9rem;
+}
+.demo-step-num {
+  font-weight: 600; color: #57606a; font-variant-numeric: tabular-nums;
+}
+.demo-step-title { color: #1f2328; font-weight: 500; }
+.demo-new {
+  background: #ddf4ff; color: #0969da; font-size: 0.7rem; font-weight: 700;
+  padding: 2px 6px; border-radius: 4px; letter-spacing: 0.06em;
+}
+.demo-shot { margin-bottom: 8px; }
+.demo-shot img {
+  width: 100%; height: auto; border-radius: 4px; border: 1px solid #d0d7de;
+  display: block;
+}
+.demo-narration {
+  margin: 0; color: #1f2328; font-size: 0.92rem; line-height: 1.4;
+}
+.demo-empty {
+  margin: 8px 0 0; color: #57606a; font-style: italic;
+  white-space: pre-wrap; overflow-wrap: anywhere;
+}
+.demo-notes-wrap { margin-top: 14px; }
+.demo-notes-wrap summary {
+  cursor: pointer; color: #9a6700; font-weight: 500; font-size: 0.9rem;
+}
+.demo-notes-wrap[open] summary { margin-bottom: 6px; }
+/* Story so far + latest demo (session index plain-language top). */
+.story-so-far {
+  background: linear-gradient(180deg, #ffffff 0%, #f6fbff 100%);
+  border: 1px solid #d6e4f0; border-radius: 10px;
+  padding: 22px 26px; margin: 14px 0 6px;
+  box-shadow: 0 1px 2px rgba(20, 40, 80, 0.04);
+}
+.story-heading {
+  margin: 0 0 12px; font-size: 1.1rem; color: #0969da;
+  text-transform: uppercase; letter-spacing: 0.05em;
+}
+.story-body { font-size: 1rem; color: #1f2328; line-height: 1.55; }
+.story-body .story-h { margin: 14px 0 6px; color: #1f2328; }
+.story-body p { margin: 0 0 10px; }
+.session-demo {
+  background: white; border: 1px solid #d6e4f0; border-radius: 10px;
+  padding: 0; margin: 8px 0 6px; overflow: hidden;
+}
+.session-demo-head {
+  display: flex; align-items: center; justify-content: space-between;
+  gap: 10px; padding: 12px 22px;
+  background: #f6f8fa; border-bottom: 1px solid #d6e4f0;
+  font-weight: 600; color: #1f2328; font-size: 0.95rem;
+}
+.session-demo-head a.open { color: #0969da; text-decoration: none; font-weight: 500; font-size: 0.9rem; }
+.session-demo-head a.open:hover { text-decoration: underline; }
+.session-demo .watch-it-work {
+  border: none; border-radius: 0; box-shadow: none; margin: 0;
+}
+/* Delivered link banner — sits on the session index when GOAL_ACHIEVED. */
+.delivered-link {
+  margin: 14px 0; padding: 14px 22px;
+  background: #dafbe1; border: 1px solid #aceebb; border-radius: 10px;
+  color: #1a7f37; font-size: 1rem;
+}
+.delivered-link a {
+  color: #1a7f37; font-weight: 600; text-decoration: none; margin-left: 8px;
+}
+.delivered-link a:hover { text-decoration: underline; }
+.delivered-back {
+  margin: 8px 0 14px; padding: 0; font-size: 0.9rem;
+}
+.delivered-back a { color: #0969da; text-decoration: none; }
+.delivered-back a:hover { text-decoration: underline; }
+.delivered-body {
+  background: white; border: 1px solid #d6e4f0; border-radius: 10px;
+  padding: 22px 28px; margin: 12px 0;
+}
+.delivered-body h2.story-h { margin-top: 0; }
+/* Feature manual (session index, top of page). */
+.cover-vision {
+  margin: 8px 0 14px; color: #57606a; font-size: 1.02rem;
+  font-style: italic; max-width: 60ch;
+}
+.feature-toc {
+  background: white; border: 1px solid #d6e4f0; border-radius: 10px;
+  padding: 20px 26px; margin: 14px 0;
+  box-shadow: 0 1px 2px rgba(20, 40, 80, 0.04);
+}
+.feature-toc-heading {
+  margin: 0 0 14px; font-size: 1.05rem; color: #0969da;
+  text-transform: uppercase; letter-spacing: 0.05em;
+}
+.feature-toc-list {
+  margin: 0; padding-left: 22px; font-size: 1rem; line-height: 1.7;
+}
+.feature-toc-list li { padding: 2px 0; }
+.feature-toc-list a {
+  color: #1f2328; text-decoration: none; font-weight: 500;
+}
+.feature-toc-list a:hover { color: #0969da; text-decoration: underline; }
+.toc-extra-header {
+  list-style: none; margin: 10px 0 4px -22px;
+  font-size: 0.82rem; color: #57606a; font-weight: 600;
+  text-transform: uppercase; letter-spacing: 0.04em;
+}
+.feature-manual { margin: 14px 0; }
+.feature-section {
+  background: white; border: 1px solid #d6e4f0; border-radius: 10px;
+  padding: 22px 26px; margin: 16px 0;
+  box-shadow: 0 1px 2px rgba(20, 40, 80, 0.04);
+  scroll-margin-top: 12px;
+}
+.feature-heading {
+  margin: 0 0 10px; font-size: 1.2rem; color: #1f2328;
+  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
+}
+.feature-description {
+  margin: 0 0 16px; color: #1f2328; font-size: 1rem; line-height: 1.55;
+}
+.feature-description-label {
+  font-weight: 600; color: #57606a; margin-right: 4px;
+}
+.feature-note {
+  margin: 8px 0 12px; padding: 8px 12px;
+  background: #fff8c5; border: 1px solid #eed888; border-radius: 6px;
+  color: #9a6700; font-size: 0.88rem;
+}
+.feature-source {
+  margin: 12px 0 0; font-size: 0.88rem; color: #57606a;
+}
+.feature-source a { color: #0969da; text-decoration: none; }
+.feature-source a:hover { text-decoration: underline; }
+.feature-empty {
+  margin: 10px 0; padding: 12px 16px;
+  background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px;
+  color: #57606a; font-style: italic;
+}
+.status-pill {
+  font-size: 0.78rem; font-weight: 600; padding: 3px 10px; border-radius: 12px;
+  letter-spacing: 0.04em; white-space: nowrap; display: inline-block;
+}
+.status-pill-passing { background: #dafbe1; color: #1a7f37; border: 1px solid #aceebb; }
+.status-pill-failing { background: #ffebe9; color: #cf222e; border: 1px solid #f2b8b5; }
+.status-pill-regressed { background: #ffebe9; color: #cf222e; border: 1px solid #f2b8b5; }
+.status-pill-partial { background: #fff8c5; color: #9a6700; border: 1px solid #e8d97e; }
+.status-pill-unknown { background: #f6f8fa; color: #57606a; border: 1px solid #d0d7de; }
+.status-pill-coming-soon { background: #f6f8fa; color: #57606a; border: 1px solid #d0d7de; }
+.developer-view {
+  margin: 28px 0 6px;
+  border: 1px dashed #d0d7de; border-radius: 8px;
+}
+.developer-view > summary {
+  cursor: pointer; padding: 12px 16px;
+  color: #57606a; font-size: 0.92rem; font-weight: 500;
+  background: #f6f8fa; border-radius: 8px;
+}
+.developer-view[open] > summary {
+  border-bottom: 1px dashed #d0d7de;
+  border-radius: 8px 8px 0 0;
+}
+.developer-view-body { padding: 12px 18px; }
+</style>
+</head><body><div class='container'>
+<section class='hero pass'><div class='badge-row'><div class='badge pass'><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
+<circle cx="12" cy="12" r="11" fill="#1a7f37"/>
+<path d="M7 12.5l3 3 7-7" stroke="white" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
+</svg><span>PASS</span></div><span class='signal-badge improving'>Direction: improving</span></div><h1>Iteration 6  ·  session tape_to_profit_support_resistence</h1><h2>structure_tape can now be measured against the v1 champion; no survivor yet on the sample data</h2><div class='meta'>2026-07-06 · goal-full</div><div class='meta'>Journeys: 6/7 passing</div><div class='journey-row'><span class='journey-pill passing' title='Multi-timeframe historical bars are ingested and persisted (data foundation + free-plan probe)'>J-01 · passing</span><span class='journey-pill passing' title='Deterministic support/resistance levels per timeframe'>J-02 · passing</span><span class='journey-pill passing' title='Confluence zones and A/B/C conviction classes'>J-03 · passing</span><span class='journey-pill passing' title='Tape-confirmed structure entries as a registered strategy'>J-04 · passing</span><span class='journey-pill passing' title='Class-scaled stop, reward, and simulated size'>J-05 · passing</span><span class='journey-pill failing' title='structure_tape is measured honestly against the v1 champion'>J-06 · failing</span><span class='journey-pill already_passing' title='The archived eras are unchanged (regression sentinel)'>J-07 · already_passing</span></div></section>
+<section class='plain-words'><h2 class='pw-heading'>In plain words</h2><div class='pw-grid'><div class='pw-card'><div class='pw-label'>What you can do now</div><p class='pw-text'>You can type in a stock ticker and watch Tapeology read live trade-by-trade order flow to see whether buyers or sellers are in control, write trading ideas into a journal, run replay studies, and view honest backtest and profit-and-loss results on a Performance page — all delivered in earlier rounds. Behind the scenes, Tapeology is also building a second, experimental way of trading that reacts to real support-and-resistance levels, but that part isn&#x27;t ready to try in the app yet.</p></div><div class='pw-card'><div class='pw-label'>What changed this time</div><p class='pw-text'>Behind-the-scenes work — nothing visibly new this round. The internal tool that checks whether a candidate trading rule beats the current one can now compare a whole alternate strategy — the new zone-aware rule built in recent rounds — against the original rule, honestly, using data the rule has never traded on before. Run against the one small sample of real data available today, it correctly found there isn&#x27;t enough evidence yet to call a winner, so nothing changes for anyone using the app.</p></div><div class='pw-card'><div class='pw-label'>What&#x27;s next</div><p class='pw-text'>Next, an independent, skeptical check will confirm whether this comparison was genuinely the last piece needed to call the zone-aware trading rule project complete.</p></div></div></section>
+<div class='tech-divider'><span>Technical detail below — open if you want the developer view.</span></div>
+<details><summary>What was done</summary><div class='accordion-body'><ul class='bullets'><li>Added a `--strategy` axis to `pnl_scan.py`&#x27;s existing candidate sweep — compares a NAMED strategy (`structure_tape`) against the champion (currently `v1`) at `profile=default`, reusing `_dataset_rows`/`_split_summary`/`_is_positive`/`_promote` verbatim; omitting the flag keeps the pre-existing profile-axis sweep byte-identical (all 12 prior tests pass unmodified)</li><li>Comparison report records net R and net $ per split (train, hold-out — never pooled), plus a per-dataset breakdown and deltas; `survivor` is true only on a hold-out win at n ≥ `promotion_min_sample_size`; train-only wins are labelled `overfit` and never promoted</li><li>Generalized `_promote` to move the champion pointer to `{strategy_id: structure_tape, profile: default}` on a genuine survivor, via the existing crash-safe two-write order (ledger row, then pointer) — verified `v1`/`default` byte-identical and the pinned fingerprint `4d665603569b9dbf` unmoved after a real promotion</li><li>Disclosed audit item B1 (the breakthrough arm&#x27;s loose static-price-position anchor) as a `provenance.assumptions` note on every report, instead of re-arming the detector — avoiding a second risky change alongside the goal-completing iteration</li><li>On the committed fixtures: `structure_tape` trades 0 times on train, 1 on hold-out — both below the promotion minimum — so the CLI honestly reports &quot;no survivor,&quot; exits 0, champion stays `{v1, default}`, nothing written to the ledger</li><li>Added 9 new tests to `test_pnl_scan.py` (comparison shape, survivor/overfit gating both ways, promotion + crash-safety, frozen-foundation check, determinism, backward compatibility, unknown-strategy refusal) and 1 new grep-guard test in `test_no_execution_path.py`; full backend suite 1146 passed / 1 skipped / 0 failed (+10 from baseline, zero regressions)</li><li>Browser QA correctly SKIPPED (backend-only iteration, zero `apps/frontend/` diff) — acceptance verified entirely via the backend test suite, matching this journey&#x27;s machine-surface nature</li><li>Review PASS, QA PASS (13/13 acceptance criteria via code tests), Audit PASS (0 critical/important findings, 3 observation-level), Closure CLOSURE-PASS; README doc-parity updated for the new comparison capability</li></ul></div></details>
+<details><summary>What's left + Next step</summary><div class='accordion-body'><h3>Still open</h3><ul class='bullets'><li>Journey J-06 (`structure_tape is measured honestly against the v1 champion`) still shows `failing` in `journey-history.json` (last refreshed at iter-5) — the build itself is independently verified complete this iteration (review PASS, QA PASS, audit PASS), but only the goal-evaluator&#x27;s formal iter-6 pass can flip journey status and determine whether GOAL_ACHIEVED is reached, since J-06 is the final Must-have journey</li><li>On the committed fixtures, `structure_tape` trades below the promotion minimum on both splits (0 on train, 1 on hold-out) — a genuine edge verdict needs a credentialed, larger multi-symbol/multi-regime history, not yet available</li><li>`edge_report.py` remains unchanged (optional per spec) — it still evaluates only the champion strategy, not a named-strategy comparison</li><li>Minor: the pre-written QA test plan speculated a CLI/JSON shape (`--splits` flags, `strategy_tape_R` field names) that the shipped implementation deliberately does not match — a documentation-plan divergence already triaged by dev/QA/audit, not a code defect</li><li>Minor operational note (unrelated to this iteration&#x27;s code): `scripts/dev.sh`&#x27;s process-kill step doesn&#x27;t reliably reap every child process (Next.js&#x27;s `next-server`, uvicorn&#x27;s `--reload` worker) — flagged for operator awareness</li></ul><h3>Next step</h3><div class='next-step-box'>No `eval.md` exists yet for this iteration, so there is no goal-evaluator Next-Step Recommendation to carry forward verbatim, and the closure verdict is CLOSURE-PASS with no blocking issues to remediate. The most defensible next step, per the audit&#x27;s own recommendation (&quot;this iteration is ready for the goal-evaluator to run its deterministic gates and two-key confirm for a GOAL_ACHIEVED decision — only the evaluator may declare it&quot;), is to run the goal-evaluator against this iteration&#x27;s artifacts: confirm J-06 (`structure_tape` measured honestly against the `v1` champion), re-verify the pinned fingerprint `4d665603569b9dbf` and `v1`/`default` byte-identity one more time, and determine whether every Must-have journey — J-06 being the last — now passes.</div></div></details>
+<details><summary>Direction signal</summary><div class='accordion-body'><div class='why-text'><strong>Why:</strong> J-06 — the final Must-have journey (`structure_tape` measured honestly against the `v1` champion) — was built end to end this iteration and independently verified: review PASS, QA PASS (13/13 acceptance criteria via code tests, 1146 passed/1 skipped/0 failed), and a hard audit PASS with zero critical/important findings confirming the hold-out-only promotion gate, crash-safe promotion order, and frozen `v1`/`default` byte-identity all hold. The goal-evaluator&#x27;s formal iter-6 confirmation (which flips journey status and would assess GOAL_ACHIEVED, since J-06 is the last Must-have) had not yet run as of this summary — `journey-history.json` still shows J-06 at its iter-5 &quot;failing&quot; snapshot — but every other gate this iteration passed cleanly with zero regressions and zero anti-goal violations, continuing the same one-journey-per-iteration cadence as the four iterations before it.</div><h3>Trend</h3><ul class='bullets'><li>Newly passing this iter: J-06 (build verified this iteration — review/QA/audit all PASS; not yet reflected in `journey-history.json`, goal-evaluator confirmation pending)</li><li>Newly passing in last 5 iters total: J-02, J-03, J-04, J-05, J-06 (J-06 pending goal-evaluator confirmation)</li><li>Regressions in last 5 iters: none</li><li>Anti-goal violations in last 5 iters: none</li><li>Iters with no journey state change: 0 of last 5</li></ul><h3>Latest evaluator reasoning</h3><div class='why-text'>(most recent available — iter-6&#x27;s goal-evaluator entry had not yet been written as of this summary; quoting the iter-5 entry) &quot;J-05 (class-scaled stop/reward/simulated size + per-class PnL breakdown) is newly passing, verified end to end on a machine surface (browser QA correctly SKIPPED; acceptance = backend suite). `structure_tape` now sizes and stops each simulated entry by its arming level&#x27;s A/B/C class and exposes a per-class breakdown served verbatim by the existing `GET /research/backtests/{id}` + MCP — all config-owned, single-sourced, and with the frozen v1/`default` fingerprint `4d665603569b9dbf` proven unmoved. J-06 remains the sole failing journey (correctly out of scope this iter) and is now fully unblocked. No regressions, no anti-goal violations, coherence PASS → CONTINUE toward J-06.&quot;</div></div></details>
+<details><summary>Artifacts</summary><div class='accordion-body'><table class='drill-table'><thead><tr><th>Report</th><th>Verdict</th><th>Path</th></tr></thead><tbody><tr><td>Iter spec</td><td><span class='verdict-cell —'>—</span></td><td><a href='../docs/phases/goal-tape_to_profit_support_resistence-iter-6.md'>docs/phases/goal-tape_to_profit_support_resistence-iter-6.md</a></td></tr><tr><td>Dev handoff</td><td><span class='verdict-cell —'>—</span></td><td><a href='../docs/handoffs/goal-tape_to_profit_support_resistence-iter-6-dev.md'>docs/handoffs/goal-tape_to_profit_support_resistence-iter-6-dev.md</a></td></tr><tr><td>Review</td><td><span class='verdict-cell PASS'>PASS</span></td><td><a href='reviews/goal-tape_to_profit_support_resistence-iter-6-review.md'>reports/reviews/goal-tape_to_profit_support_resistence-iter-6-review.md</a></td></tr><tr><td>Browser QA</td><td><span class='verdict-cell SKIPPED'>SKIPPED</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-6-ui-test-results.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-test-results.md</a></td></tr><tr><td>Implementation summary</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-6-implementation-summary.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-6-implementation-summary.md</a></td></tr><tr><td>User-visible changes</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-6-user-visible-changes.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-6-user-visible-changes.md</a></td></tr><tr><td>What to click</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-6-what-to-click.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-6-what-to-click.md</a></td></tr><tr><td>UI surface map</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-6-ui-surface-map.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-surface-map.md</a></td></tr><tr><td>UI test plan</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-6-ui-test-plan.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-test-plan.md</a></td></tr><tr><td>QA</td><td><span class='verdict-cell PASS'>PASS</span></td><td><a href='qa/goal-tape_to_profit_support_resistence-iter-6-qa.md'>reports/qa/goal-tape_to_profit_support_resistence-iter-6-qa.md</a></td></tr><tr><td>Audit</td><td><span class='verdict-cell PASS'>PASS</span></td><td><a href='../docs/handoffs/goal-tape_to_profit_support_resistence-iter-6-audit.md'>docs/handoffs/goal-tape_to_profit_support_resistence-iter-6-audit.md</a></td></tr><tr><td>Closure</td><td><span class='verdict-cell CLOSURE-PASS'>CLOSURE-PASS</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-6-closure-verdict.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-6-closure-verdict.md</a></td></tr><tr><td>Journey history</td><td><span class='verdict-cell —'>—</span></td><td><a href='../runs/goal-session-tape_to_profit_support_resistence/state/journey-history.json'>runs/goal-session-tape_to_profit_support_resistence/state/journey-history.json</a></td></tr></tbody></table></div></details>
+<details><summary>Timing — where this iteration's wall time went</summary><div class='accordion-body'><pre>== Wall-time report: session tape_to_profit_support_resistence
+  goal-tape_to_profit_support_resistence-iter-6  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
+      iteration-summarizer        10.1m  calls=1
+      goal-decomposer             10.1m  calls=1
+      readme-maintainer            3.0m  calls=1
+      pump-wait                  0.3m</pre></div></details>
+<div class='footer-note'>Generated 2026-07-06 18:38 by <code>render_iteration_summary.py</code> · source: <a href='phase-goal-tape_to_profit_support_resistence-iter-6-iteration-summary.md'>phase-goal-tape_to_profit_support_resistence-iter-6-iteration-summary.md</a></div>
+</div></body></html>
\ No newline at end of file
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-surface-map.md breports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-surface-map.md
new file mode 100644
index 0000000..3961b5b
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-surface-map.md
@@ -0,0 +1,5 @@
+# Phase goal-tape_to_profit_support_resistence-iter-6 — UI Surface Map
+
+**Status:** N/A — Backend-only phase (Frontend Present: no)
+
+No UI surfaces affected.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-test-plan.md breports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-test-plan.md
new file mode 100644
index 0000000..6567e53
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-test-plan.md
@@ -0,0 +1,3 @@
+# Phase goal-tape_to_profit_support_resistence-iter-6 — UI Test Plan
+
+**Status:** N/A — Backend-only phase. No UI tests required.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-test-results.md breports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-test-results.md
new file mode 100644
index 0000000..de66d2f
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-test-results.md
@@ -0,0 +1,5 @@
+# Phase goal-tape_to_profit_support_resistence-iter-6 — UI Test Results
+
+**Browser QA Verdict:** SKIPPED
+
+**Reason:** Backend-only phase (Frontend Present: no). No browser tests executed.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-6-user-visible-changes.md breports/phase-goal-tape_to_profit_support_resistence-iter-6-user-visible-changes.md
new file mode 100644
index 0000000..b890e2b
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-6-user-visible-changes.md
@@ -0,0 +1,5 @@
+# Phase goal-tape_to_profit_support_resistence-iter-6 — User-Visible Changes
+
+**Status:** N/A — Backend-only phase (Frontend Present: no)
+
+No user-visible changes. All changes are internal backend implementation.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-6-what-to-click.md breports/phase-goal-tape_to_profit_support_resistence-iter-6-what-to-click.md
new file mode 100644
index 0000000..0b7be56
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-6-what-to-click.md
@@ -0,0 +1,3 @@
+# Phase goal-tape_to_profit_support_resistence-iter-6 — What to Click
+
+**Status:** N/A — Backend-only phase. No UI verification steps.
diff --git areports/qa/goal-tape_to_profit_support_resistence-iter-6-qa.md breports/qa/goal-tape_to_profit_support_resistence-iter-6-qa.md
new file mode 100644
index 0000000..34176f3
--- /dev/null
+++ breports/qa/goal-tape_to_profit_support_resistence-iter-6-qa.md
@@ -0,0 +1,139 @@
+# QA Report: goal-tape_to_profit_support_resistence-iter-6
+
+**Verdict:** PASS
+
+**Phase:** goal-tape_to_profit_support_resistence-iter-6
+**Date:** 2026-07-06
+**Frontend Present:** no
+
+---
+
+## Artifact Verification
+
+All required artifacts verified as present:
+
+- ✅ `docs/handoffs/goal-tape_to_profit_support_resistence-iter-6-dev.md` — exists, complete
+- ✅ `reports/reviews/goal-tape_to_profit_support_resistence-iter-6-review.md` — exists, verdict: **PASS**
+- ✅ `runs/goal-tape_to_profit_support_resistence-iter-6/status.json` — exists, status in_progress
+
+---
+
+## Backend Test Results
+
+**Command:** `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
+
+**Exit Code:** 0
+
+**Full Output:**
+```
+........................................................................ [  6%]
+........................................................................ [ 12%]
+........................................................................ [ 18%]
+........................................................................ [ 25%]
+........................................................................ [ 31%]
+........................................................................ [ 37%]
+....................................................s................... [ 43%]
+........................................................................ [ 50%]
+........................................................................ [ 56%]
+........................................................................ [ 62%]
+........................................................................ [ 69%]
+........................................................................ [ 75%]
+........................................................................ [ 81%]
+........................................................................ [ 87%]
+........................................................................ [ 94%]
+..................................................................       [100%]
+=============================== warnings summary ===============================
+.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
+  apps/backend/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
+    from starlette.testclient import TestClient as TestClient  # noqa
+
+tests/test_analytics_api.py::test_endpoint_serves_module_projection_verbatim
+  apps/backend/.venv/lib/python3.14/site-packages/websockets/legacy/__init__.py:6: DeprecationWarning: websockets.legacy is deprecated; see https://websockets.readthedocs.io/en/stable/upgrade.html for upgrade instructions
+    warnings.warn(  # deprecated in 14.0 - 2024-11-09
+
+-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
+```
+
+**Summary:** Full backend test suite executed successfully. 1146 tests passed, 1 skipped (pre-existing), 0 failed.
+
+**Subset Results:**
+- `test_pnl_scan.py` — 21 passed (12 pre-existing unmodified + 9 new strategy-axis tests)
+- `test_no_execution_path.py` — 6 passed (5 pre-existing + 1 new strategy-axis coverage)
+- `test_profile_equivalence.py` — 15 passed (frozen foundation: config fingerprint and v1/default equivalence intact)
+
+---
+
+## Functional Test Plan Execution
+
+**Status:** Test plan exists at `reports/qa/goal-tape_to_profit_support_resistence-iter-6-test-plan.md`
+
+**Note:** The test plan was written before implementation and speculates CLI/JSON shapes that differ from what was actually built. Per the dev handoff's "IMPORTANT — Note on exact CLI usage and field naming" section:
+- The plan assumes `--splits train`/`--splits hold_out` flags that do NOT exist
+- The plan assumes field names like `strategy_tape_R`/`v1_R` that do NOT match the actual reused shape
+- These are speculative mismatches, not regression defects — the implementation correctly reuses the existing sweep's machinery as specified
+
+**Functional Test Coverage (via pytest):**
+
+The 9 new tests in `test_pnl_scan.py` exercise the spec's acceptance criteria:
+
+| Test ID | Description | Type | Result | Evidence |
+|---------|-------------|------|--------|----------|
+| — | Named-strategy comparison report shape (per-split, never pooled) | code | PASS | test_pnl_scan.py line ~200+ (new fixture and assertion tests) |
+| — | Survivor gate: at/above-min-n positive hold-out IS survivor | code | PASS | test_min_n_gate_accepts_above_minimum_and_survivors_in_both_metrics |
+| — | Survivor gate: below-min-n hold-out IS NOT survivor despite positive | code | PASS | test_min_n_gate_rejects_below_minimum_despite_positive_holdout |
+| — | Overfit: positive train + failing hold-out labeled overfit, NOT promoted | code | PASS | test_overfit_positive_train_negative_holdout_rejects_promotion |
+| — | Promotion correctness: exactly one ledger row, pointer moves to strategy | code | PASS | test_named_strategy_survivor_promotion_writes_ledger_then_pointer |
+| — | Promotion crash-safety: mid-promotion re-run hits DuplicateEnhancementError | code | PASS | test_named_strategy_duplicate_promotion_raises_duplicate_error |
+| — | Frozen foundation: config fingerprint unmoved, v1/default byte-identical | code | PASS | test_profile_equivalence.py (15 passed); snapshot assertion in survivor test |
+| — | Fixture honesty: committed PG train/hold-out → no survivor, champion unchanged | code | PASS | test_named_strategy_vs_v1_on_committed_pg_fixtures_reports_no_survivor |
+| — | Deterministic re-runs: byte-identical output | code | PASS | test_named_strategy_determinism_two_runs_produce_identical_output |
+| — | Backward compatibility: no `--strategy` flag behaves identically | code | PASS | All 12 pre-existing test_pnl_scan.py tests pass unmodified |
+| — | Single-source scan: set_champion_pointer called from one file only | code | PASS | test_named_strategy_comparison_and_promotion_code_carries_no_execution_vocabulary (new grep-guard test in test_no_execution_path.py) |
+| — | No execution path: no broker/order/routing identifiers | code | PASS | test_no_execution_path.py green; new test naming strategy-axis paths explicitly |
+| — | Full regression: J-01–J-05, J-07 remain green | code | PASS | Full backend suite 1146 passed, 0 regressions; frontend diff empty (git status apps/frontend/ = 0 changes) |
+
+**Summary:** 13/13 specification acceptance criteria verified via code tests. All pre-existing tests pass unmodified, confirming backward compatibility. No regressions.
+
+---
+
+## Browser Checks
+
+**Status:** SKIPPED — backend-only phase (Frontend Present: no)
+
+Per the spec and execution plan, `apps/frontend/` MUST NOT be touched and no frontend surface changes are made. No browser QA required for this iteration.
+
+---
+
+## UI Evolution Audit
+
+**Status:** SKIPPED — backend-only phase (Frontend Present: no)
+
+No new UI capability, no navigation change, no frontend diff. Per the iteration's own out-of-scope list and the iter-0 lesson, `apps/frontend/` remains untouched to keep J-07's cockpit leg green without a new screenshot.
+
+---
+
+## Blockers
+
+None. All tests pass, all artifacts are present, review is PASS, and all functional requirements are met.
+
+---
+
+## Known Issues / Handoff Notes
+
+1. **Test plan field name mismatches** — The pre-written functional test plan speculates CLI `--splits` flags and JSON field names that differ from the actual reused-verbatim implementation. This is not a code defect but rather a documentation-plan vs. implementation divergence flagged in the dev handoff. The implementation correctly follows the spec's reuse instruction. QA validated the ACTUAL implementation via code tests (passing).
+
+2. **Fixture honesty finding** — The committed PG train/hold-out fixture pair yields no survivor (train candidate n=0, hold-out candidate n=1, below the minimum of 5). This is an HONEST finding, not a defect — the 2-timeframe bar fixture produces mostly class-C zones per the iter-3 lesson. The implementation correctly reports this and exits 0 with no promotion, as specified.
+
+3. **B1 disclosure** — The breakthrough arm is disclosed in `provenance.assumptions` as a static price-position test (loose anchor). This resolves the audit item B1 by transparency, not re-arming, as specified.
+
+---
+
+## Summary
+
+- **Backend Test Suite:** 1146 passed, 1 skipped, 0 failed ✅
+- **Iteration-Specific Tests:** 21 pnl_scan + 6 no_execution_path + 15 profile_equivalence all PASS ✅
+- **Review Verdict:** PASS ✅
+- **Frontend Changes:** 0 (correctly untouched per spec) ✅
+- **All Spec Acceptance Criteria:** Met and verified ✅
+
+**Verdict for Next Stage:** PASS — this phase is ready for auditor review and goal evaluation.
diff --git areports/qa/goal-tape_to_profit_support_resistence-iter-6-test-plan.md breports/qa/goal-tape_to_profit_support_resistence-iter-6-test-plan.md
new file mode 100644
index 0000000..3da2f79
--- /dev/null
+++ breports/qa/goal-tape_to_profit_support_resistence-iter-6-test-plan.md
@@ -0,0 +1,483 @@
+# Goal Iteration 6 (J-06): Named-Strategy Comparison Functional Test Plan
+
+**Phase:** goal-tape_to_profit_support_resistence-iter-6
+**Date:** 2026-07-06
+**Frontend Present:** no
+
+## Phase Goal
+
+Generalize the existing sweep (`pnl_scan.py`) to measure whether `structure_tape` beats the frozen `v1` champion on **held-out** data — and promote it to champion only if it survives hold-out at n ≥ minimum, while keeping the default profile and v1 strategy byte-identical and labelling train-only wins as overfit.
+
+## Test Cases
+
+### TC-01 — Named-strategy comparison report shape (train split)
+
+**Type:** api
+**Preconditions:** 
+- Backend running with at least one registered training dataset
+- `structure_tape` strategy registered
+- `v1` champion pointer seeded in store
+
+**Steps:**
+1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --splits train --out /tmp/test-report-train.json`
+2. Parse the JSON output file
+3. Inspect the train-split report section
+
+**Expected outcome:** 
+Report contains per-dataset breakdown with:
+- `structure_tape` net R, net $, n
+- `v1` net R, net $, n
+- Candidate-minus-champion deltas for net R and net $
+- Dataset name and window for each row
+- No pooling: each dataset is a separate row (never aggregated within train split)
+
+**Pass criteria:** 
+- JSON parses without error
+- Train split section has ≥1 per-dataset row
+- Each row has fields: `dataset`, `strategy_tape_R`, `strategy_tape_usd`, `strategy_tape_n`, `v1_R`, `v1_usd`, `v1_n`, `delta_R`, `delta_usd`
+- No null/missing values in any required field
+
+---
+
+### TC-02 — Named-strategy comparison report shape (hold-out split)
+
+**Type:** api
+**Preconditions:**
+- Backend running with at least one registered hold-out dataset
+- `structure_tape` strategy registered
+- `v1` champion pointer seeded in store
+
+**Steps:**
+1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --splits hold_out --out /tmp/test-report-holdout.json`
+2. Parse the JSON output file
+3. Inspect the hold-out-split report section
+
+**Expected outcome:**
+Report contains per-dataset breakdown with:
+- `structure_tape` net R, net $, n
+- `v1` net R, net $, n
+- Candidate-minus-champion deltas for net R and net $
+- Train and hold-out splits are separate (never pooled)
+
+**Pass criteria:**
+- JSON parses without error
+- Hold-out split section has ≥1 per-dataset row
+- Each row has all required fields (same as TC-01)
+- Train and hold-out sections are structurally distinct (not merged)
+
+---
+
+### TC-03 — Survivor gate: below-min-n hold-out win marked NOT survivor
+
+**Type:** api
+**Preconditions:**
+- Backend running with synthetic fixture that has:
+  - Train: positive `structure_tape` edge (cumulative delta > 0)
+  - Hold-out: `structure_tape` also positive but n < `Config.promotion_min_sample_size`
+
+**Steps:**
+1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-below-min.json`
+2. Parse output
+3. Check survivor flag and overfit flag in the report
+
+**Expected outcome:**
+- `survivor` = false
+- `overfit` = false (positive train AND failing hold-out would be true; positive train AND below-min n IS a non-survivor case, labeled clearly)
+- Report still fully rendered with all per-split data
+
+**Pass criteria:**
+- `survivor` field in report is exactly `false`
+- Comparison metrics are present and valid
+- Champion pointer remains unchanged (no write to store)
+- Exit code 0
+
+---
+
+### TC-04 — Survivor gate: at/above-min-n positive hold-out win IS survivor
+
+**Type:** api
+**Preconditions:**
+- Backend running with synthetic fixture that has:
+  - Train: positive `structure_tape` edge
+  - Hold-out: positive `structure_tape` edge AND n ≥ `Config.promotion_min_sample_size`
+
+**Steps:**
+1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-above-min.json`
+2. Parse output
+3. Check survivor flag
+
+**Expected outcome:**
+- `survivor` = true
+- `overfit` = false
+- Promotion occurs (ledger row appended, champion pointer moved to `strategy_id=structure_tape`)
+
+**Pass criteria:**
+- `survivor` field in report is exactly `true`
+- New row in `GET /research/pnl/ledger` with `enhancement_id` naming the strategy promotion
+- `GET /research/profiles` and `GET /research/strategies` show champion pointer moved to `strategy_tape`
+- Exit code 0
+
+---
+
+### TC-05 — Overfit: positive train + failing hold-out marked overfit, NOT promoted
+
+**Type:** api
+**Preconditions:**
+- Backend running with synthetic fixture that has:
+  - Train: positive `structure_tape` edge
+  - Hold-out: negative `structure_tape` edge (worse than `v1`)
+
+**Steps:**
+1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-overfit.json`
+2. Parse output
+3. Check survivor, overfit flags and store state
+
+**Expected outcome:**
+- `survivor` = false
+- `overfit` = true
+- Report labels this case as overfit
+- No promotion (champion unchanged, no ledger row)
+
+**Pass criteria:**
+- `survivor` is false, `overfit` is true (both explicit in report)
+- Champion pointer still points to `{v1, default}`
+- No new row in PnL ledger
+- Exit code 0
+
+---
+
+### TC-06 — Promotion correctness: exactly one ledger row, then pointer moves
+
+**Type:** api
+**Preconditions:**
+- Backend running with synthetic ≥-min-n survivor fixture
+- Store has clean state (champion at `{v1, default}`)
+- PnL ledger is empty or known state
+
+**Steps:**
+1. Record ledger row count: `curl -s http://localhost:8000/research/pnl/ledger | jq '.rows | length'`
+2. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-promotion.json`
+3. Re-check ledger row count
+4. Get champion pointer: `curl -s http://localhost:8000/research/profiles | jq '.champion_pointer'`
+
+**Expected outcome:**
+- Ledger row count increased by exactly 1
+- New ledger row has `enhancement_id` like `"structure_tape-over-v1"`
+- Champion pointer's `strategy_id` is now `"structure_tape"`
+- Champion pointer's `profile` is still `"default"` (only strategy axis moved)
+
+**Pass criteria:**
+- Ledger rows += 1
+- New row has all required fields (strategy, profile, dates, net R, net $, n, train/hold-out, survivor flag)
+- Champion pointer: `strategy_id == "structure_tape"` AND `profile == "default"`
+- Exit code 0
+
+---
+
+### TC-07 — Promotion crash-safety: mid-promotion re-run hits DuplicateEnhancementError
+
+**Type:** api
+**Preconditions:**
+- Backend running with synthetic ≥-min-n survivor fixture
+- Previous TC-06 promotion completed (champion now at `{structure_tape, default}`)
+
+**Steps:**
+1. Run the same sweep again: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-duplicate.json`
+2. Check exit code and error output
+
+**Expected outcome:**
+- CLI detects that an identical `enhancement_id` was already promoted
+- Raises explicit `ScanError` / `DuplicateEnhancementError`
+- Nothing is written a second time
+
+**Pass criteria:**
+- Exit code non-zero (error exit)
+- Error message names `DuplicateEnhancementError` or explicit duplicate-detection logic
+- No second row in ledger (still the same count as after TC-06)
+- No pointer move (still at `{structure_tape, default}`)
+
+---
+
+### TC-08 — Frozen foundation after promotion: fingerprint, v1, default byte-identical
+
+**Type:** api
+**Preconditions:**
+- Promotion completed (champion now at `{structure_tape, default}`)
+
+**Steps:**
+1. Get config fingerprint: `python -c "from app.config import Config; print(Config.config_fingerprint())"`
+2. Run engine equivalence test: `pytest apps/backend/tests/test_profile_equivalence.py -v`
+3. Verify `v1` strategy bytes: backtest `v1` on a fixture, record net R and $
+4. Verify `default` profile bytes: run two identical backtests, compare outputs byte-for-byte
+
+**Expected outcome:**
+- Config fingerprint is still `"4d665603569b9dbf"` (unchanged)
+- Engine equivalence test passes (v1 and default produce same results as baseline)
+- v1 strategy backtests are deterministic (two runs = identical bytes)
+- default profile produces no new fields or altered computations
+
+**Pass criteria:**
+- Fingerprint == `"4d665603569b9dbf"`
+- `test_profile_equivalence.py` exit code 0
+- Two v1 backtests produce identical `--out` JSON (byte-identical hashes)
+- No config mutations present
+
+---
+
+### TC-09 — Fixture honesty: committed train/hold-out pair → no survivor, champion unchanged
+
+**Type:** api
+**Preconditions:**
+- Backend running with committed PG train/hold-out fixture pair
+- Champion at `{v1, default}` (baseline state)
+
+**Steps:**
+1. Run the sweep on the committed fixtures: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-fixture-honest.json`
+2. Parse the report
+3. Check champion pointer: `curl -s http://localhost:8000/research/profiles | jq '.champion_pointer.strategy_id'`
+4. Check ledger row count (should be unchanged)
+
+**Expected outcome:**
+- Report's `survivor` flag = false
+- Report notes that hold-out n is below `promotion_min_sample_size`
+- Exit code 0
+- Champion pointer still at `strategy_id: "v1"`
+- No new ledger row
+
+**Pass criteria:**
+- `survivor` == false
+- Hold-out n < `Config.promotion_min_sample_size` (fixture detail visible in report or via inspection)
+- Exit code 0
+- Champion unchanged
+- Ledger unchanged
+
+---
+
+### TC-10 — Deterministic re-runs: byte-identical `--out` on committed fixtures
+
+**Type:** api
+**Preconditions:**
+- Backend running with committed fixtures
+- Both runs from clean state
+
+**Steps:**
+1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/run1.json`
+2. Capture hash: `sha256sum /tmp/run1.json`
+3. Run again: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/run2.json`
+4. Capture hash: `sha256sum /tmp/run2.json`
+5. Compare hashes
+
+**Expected outcome:**
+- Both hashes are identical
+- JSON content is byte-identical (same sort order, no timestamps, deterministic)
+
+**Pass criteria:**
+- sha256 hashes match exactly
+- No per-run randomness, no wall-clock fields in report
+
+---
+
+### TC-11 — Backward compatibility: no `--strategy` flag behaves byte-identically
+
+**Type:** api
+**Preconditions:**
+- Backend running with existing test fixtures
+- A pre-recorded baseline of the profile-only sweep output (from before this change)
+
+**Steps:**
+1. Run profile-only sweep (no `--strategy` flag): `python apps/backend/app/research/pnl_scan.py --out /tmp/profile-only.json`
+2. Compare to baseline output from before the generalization
+
+**Expected outcome:**
+- `--out` is byte-identical to the pre-change baseline
+- Profile axis behaves the same (loops over all profiles)
+- All per-split summaries match
+
+**Pass criteria:**
+- sha256 hash matches the baseline (or diff shows only whitespace/order changes that are immaterial)
+- All profile candidates in the report
+- Exit code 0
+
+---
+
+### TC-12 — Single-source scan: champion pointer setter called from one file only
+
+**Type:** artifact
+**Preconditions:**
+- Codebase checked out
+
+**Steps:**
+1. Grep for calls to `store.set_champion_pointer`: `grep -r "set_champion_pointer" apps/backend --include="*.py" | grep -v test | grep -v "def set_champion_pointer"`
+2. Identify all non-test, non-definition call sites
+
+**Expected outcome:**
+- Exactly one call site in production code (in `pnl_scan.py`'s promotion logic)
+- No second implementation path for moving the champion
+
+**Pass criteria:**
+- Only one production file calls `set_champion_pointer` (and it's `pnl_scan.py`)
+- No second net R/$/edge computation path introduced
+
+---
+
+### TC-13 — Unknown candidate strategy id → explicit refusal
+
+**Type:** api
+**Preconditions:**
+- Backend running
+
+**Steps:**
+1. Run with invalid strategy id: `python apps/backend/app/research/pnl_scan.py --strategy unknown_strategy --out /tmp/test-unknown.json`
+2. Check exit code and output
+
+**Expected outcome:**
+- CLI raises explicit error (not a coerced/fabricated comparison)
+- Error message names the unknown strategy
+- Exit code non-zero
+
+**Pass criteria:**
+- Exit code != 0
+- Error message contains strategy id or "strategy not found" or similar
+- No report file written (or empty report with error note)
+
+---
+
+### TC-14 — Error case: corrupt dataset → explicit ScanError, nothing written
+
+**Type:** api
+**Preconditions:**
+- Backend running with a dataset marked as corrupt or non-`done` status
+
+**Steps:**
+1. Manually mark a dataset as `status != done` in the research store
+2. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-corrupt.json`
+3. Check exit code and output
+
+**Expected outcome:**
+- CLI raises explicit `ScanError`
+- No promotion occurs
+- No ledger row written
+
+**Pass criteria:**
+- Exit code non-zero
+- Error message names the dataset or status issue
+- Champion unchanged
+- No ledger row added
+
+---
+
+### TC-15 — More than one train/hold-out dataset → promotion skipped, comparison reported
+
+**Type:** api
+**Preconditions:**
+- Backend running with ≥2 train datasets and/or ≥2 hold-out datasets
+- All datasets have valid backtests for both strategies
+
+**Steps:**
+1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-multi-dataset.json`
+2. Parse report
+
+**Expected outcome:**
+- Report includes per-dataset comparison for all datasets
+- But promotion is skipped (no ledger row, no pointer move)
+- Report explicitly notes "multiple train/hold-out datasets; promotion skipped"
+- Exit code 0
+
+**Pass criteria:**
+- Report is complete and per-dataset rows present
+- `survivor` == false (or explicit note)
+- Champion unchanged
+- No ledger row written
+
+---
+
+### TC-16 — Audit B1 disclosed: breakthrough arm assumptions in report provenance
... [diff_bound] diff --git areports/qa/goal-tape_to_profit_support_resistence-iter-6-test-plan.md breports/qa/goal-tape_to_profit_support_resistence-iter-6-test-plan.md: 89 more diff lines omitted — Read the file for full detail
diff --git areports/reviews/goal-tape_to_profit_support_resistence-iter-6-review.md breports/reviews/goal-tape_to_profit_support_resistence-iter-6-review.md
new file mode 100644
index 0000000..6aa195c
--- /dev/null
+++ breports/reviews/goal-tape_to_profit_support_resistence-iter-6-review.md
@@ -0,0 +1,25 @@
+**Verdict:** PASS
+
+```yaml
+phase: goal-tape_to_profit_support_resistence-iter-6
+date: 2026-07-06
+reviewer: reviewer
+summary: |
+  Generalizes pnl_scan.py with an additive STRATEGY axis (--strategy) alongside the unchanged
+  PROFILE axis, reusing _dataset_rows/_split_summary/_is_positive/_promote verbatim, per spec.
+  Independently re-verified: 42/42 targeted tests green, full backend suite exit 0, two live CLI
+  runs on the committed fixtures byte-identical and honestly report no survivor (champion
+  unmoved), grep-guard clean, config.py/store.py/frontend all untouched as required.
+spec_alignment:
+  definition_of_done: complete
+  scope_creep: none
+issues: []
+standards:
+  state_transitions_server_side: pass
+  test_quality: pass
+  no_dead_code: pass
+  no_hardcoded_localhost: n/a
+  ui_evolved_with_capability: n/a
+  navigation_updated: n/a
+  architecture_principles: pass
+```
diff --git aruns/goal-session-tape_to_profit_support_resistence/iter-6/.steps/coherence.done bruns/goal-session-tape_to_profit_support_resistence/iter-6/.steps/coherence.done
new file mode 100644
index 0000000..09514d1
--- /dev/null
+++ bruns/goal-session-tape_to_profit_support_resistence/iter-6/.steps/coherence.done
@@ -0,0 +1 @@
+{"v":1,"step":"coherence","iter":"6","iter_name":"goal-tape_to_profit_support_resistence-iter-6","ts":"2026-07-06T17:42:48Z","tree_hash":"88cc1e8940d422e52a8dbc8ed7e140b286a17401","artifacts":["runs/goal-session-tape_to_profit_support_resistence/iter-6/coherence.md"],"verdict":"COHERENCE-PASS","journeys":""}
diff --git aruns/goal-session-tape_to_profit_support_resistence/iter-6/coherence.md bruns/goal-session-tape_to_profit_support_resistence/iter-6/coherence.md
new file mode 100644
index 0000000..f06030b
--- /dev/null
+++ bruns/goal-session-tape_to_profit_support_resistence/iter-6/coherence.md
@@ -0,0 +1,63 @@
+# Iteration 6 — Coherence Audit
+
+**Iteration:** goal-tape_to_profit_support_resistence-iter-6
+**Date:** 2026-07-06
+**Written by:** coherence-auditor
+
+---
+
+**Verdict:** COHERENCE-PASS
+
+<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->
+
+---
+
+## Scope of this iteration
+
+Backend-only, machine-surface generalization of Data Contract row 43 (Named-strategy comparison
+report). Files touched (per `git diff 0fb570480aa7c87e33e8bcbb38816d5d0dc1e6ee`, noise-excluded):
+`apps/backend/app/research/pnl_scan.py`, `apps/backend/tests/test_no_execution_path.py`,
+`apps/backend/tests/test_pnl_scan.py`, `README.md`. No frontend files touched (confirmed via diff
+and via `reports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-surface-map.md`, which
+states "N/A — Backend-only phase"). No `runs/*`/`reports/*` churn outside harness bookkeeping; the
+excluded-paths `--stat` shows only session-bookkeeping files (`goal-slice.md`, `snapshot-sha`,
+`.steps/`, `telemetry.jsonl`, `trace.jsonl`, `project-story.md`) — no lockfile changed. `blueprint.md`
+itself was not touched, matching the iter spec's "no blueprint.md edit this iteration" claim (row 43
+was already registered at baseline).
+
+## Data Contract check
+
+| Value / entity | Result | Evidence (file:line) |
+|---|---|---|
+| Row 43 — Named-strategy comparison report (`structure_tape` vs `v1`, per-split net R/net $/n/deltas, `survivor`/`overfit`/`robustness`) | OK | `apps/backend/app/research/pnl_scan.py:333-473` (`run_sweep`, generalized in place, same function — not a new module) |
+| Row 43 — promotion (one ledger row + moved champion pointer) | OK | `pnl_scan.py:308-326` (`_promote`) calls the EXISTING single writer `append_validation_row` then the EXISTING single writer `store.set_champion_pointer`; verified only ONE call site of `set_champion_pointer` repo-wide (`apps/backend/app/research/store.py:1407` defines it, `apps/backend/app/research/pnl_scan.py:326` is its only caller) |
+| Row 36 — profile-axis sweep (pre-existing, era-3) | OK | Unchanged behavior confirmed by reading the diff: `candidate_strategy_id=None` branch (`pnl_scan.py:366-372`) reproduces the exact pre-iteration call shape; `_promote`'s new `new_strategy_id`/`new_profile` params resolve to `(champion["strategy_id"], candidate_id)` for this axis — byte-identical to the prior hardcoded `store.set_champion_pointer(strategy_id=champion["strategy_id"], profile=candidate_id, ...)` |
+| Net R / net $ / n measurement | OK — re-read, not recomputed | `_measurement()` (`pnl_scan.py:208-212`, untouched by this diff) still copies `result["aggregates"]` verbatim from the ONE `BacktestJobManager`/`BacktestRunner` computation (row 31); the new strategy axis reuses this same function for both champion and candidate — no second net R/$/edge computation path introduced |
+| `provenance.assumptions` (audit-B1 disclosure string) | OK — not a new contract value | A static, config-independent caveat string (`BREAKTHROUGH_ANCHOR_CAVEAT`, `pnl_scan.py:143-150`) attached to the existing "provenance" field pattern already established for backtest reports (row 41: "echoed verbatim in each report's provenance"); disclosure prose, not a computed numeric value requiring its own owner/endpoint — matches DoD item "Audit B1 resolved... disclosed in the comparison report's provenance/assumptions" |
+| Config (`promotion_min_sample_size`, `PROFILE_DEFAULT`, `STRATEGY_TAPE_ID`) | OK — reused, none added | `config.py` does not appear in the diff at all — confirms no new `Config` field was added (iter-1 lesson honored); `run_sweep`'s survivor gate (`pnl_scan.py:430-433`) reuses `config.promotion_min_sample_size` verbatim |
+
+No duplicate computation, no non-canonical source, no unregistered value found.
+
+## Information Architecture check
+
+| Feature / route | Result | Evidence (nav file inspected) |
+|---|---|---|
+| (none — no new page/route this iteration) | OK | Diff contains no `apps/frontend/*` changes; iter spec §"UI surface changes" states "None (no nav/page change...)"; `reports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-surface-map.md` confirms "N/A — Backend-only phase" |
+
+The `--strategy` CLI flag and the `provenance.assumptions` report field are machine-surface additions
+to an existing CLI (`python -m app.research.pnl_scan`), which the blueprint IA already lists as a
+"machine surface — no nav home." Nothing new needed a navigation path.
+
+## Blocking violations (FAIL only)
+
+None.
+
+## Advisory notes (non-blocking)
+
+- The README's new "Class-scaled risk, reward, and size..." bullet (README.md, capabilities list)
+  documents a capability actually shipped in iter-5, not iter-6 — the iter-6 spec's own "Doc-parity
+  rider" flags this as a deliberate catch-up of a missed iter-5 README edit, not new iter-6 scope.
+  Noted for completeness; not a coherence defect (no code/computation/endpoint implication).
+- None otherwise. This is a tightly-scoped, single-function generalization (`run_sweep`/`_promote`
+  in the one row-36/43 owner module) with no new surfaces, no new config, and no new writers —
+  the cleanest kind of iteration for this gate to audit.
diff --git aruns/goal-session-tape_to_profit_support_resistence/iter-6/journey-history.pre.json bruns/goal-session-tape_to_profit_support_resistence/iter-6/journey-history.pre.json
new file mode 100644
index 0000000..0f46aed
--- /dev/null
+++ bruns/goal-session-tape_to_profit_support_resistence/iter-6/journey-history.pre.json
@@ -0,0 +1,69 @@
+{
+  "journeys": {
+    "J-01": {
+      "id": "J-01",
+      "name": "Multi-timeframe historical bars are ingested and persisted (data foundation + free-plan probe)",
+      "status": "passing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-5",
+      "last_passing_iter": "goal-tape_to_profit_support_resistence-iter-5",
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "Required-still-passing (machine surface). evaluator independently re-ran tests/test_bars.py + tests/test_bars_api.py green this iter (all dots, 100%, no F/E). Bar store is the row-39 level source structure_tape consumes; bars.py untouched this iter (git diff a51313ce empty for it)."
+    },
+    "J-02": {
+      "id": "J-02",
+      "name": "Deterministic support/resistance levels per timeframe",
+      "status": "passing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-5",
+      "last_passing_iter": "goal-tape_to_profit_support_resistence-iter-5",
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "Required-still-passing (machine surface; browser QA correctly SKIPPED). evaluator re-ran tests/test_levels.py + tests/test_levels_api.py green this iter. research/levels.py has EMPTY diff (a51313ce..working tree) -> compute_levels remains the ONE owner structure_tape reads (coherence.md Row-39 OK)."
+    },
+    "J-03": {
+      "id": "J-03",
+      "name": "Confluence zones and A/B/C conviction classes",
+      "status": "passing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-5",
+      "last_passing_iter": "goal-tape_to_profit_support_resistence-iter-5",
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "Required-still-passing (machine surface). evaluator re-ran tests/test_levels.py green (confluence + A/B/C grading + no-lookahead). The A/B/C class is consumed verbatim by structure_tape's trade['level']['class'] and now drives the class-scaled stop/reward/size; levels.py diff EMPTY (class owner unchanged)."
+    },
+    "J-04": {
+      "id": "J-04",
+      "name": "Tape-confirmed structure entries as a registered strategy",
+      "status": "passing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-5",
+      "last_passing_iter": "goal-tape_to_profit_support_resistence-iter-5",
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "Required-still-passing (machine surface). evaluator live-dumped Config().strategy_registry() == ['v1','structure_tape'] (v1 exits byte-identical: synthetic_invalidation_at_arm/spread_multiple 10.0, NO class-scaling keys leaked; structure_tape additively carries class-scaled grammar); unknown strategy -> None (route 422). Re-ran tests/test_backtests.py + tests/test_strategies_api.py + tests/test_mcp_server.py green."
+    },
+    "J-05": {
+      "id": "J-05",
+      "name": "Class-scaled stop, reward, and simulated size",
+      "status": "passing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-5",
+      "last_passing_iter": "goal-tape_to_profit_support_resistence-iter-5",
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "NEWLY PASSING (machine surface; acceptance = backend suite per spec DoD). evaluator live-verified structure_tape now carries class_scaled_invalidation_beyond_level (stop_bps A=1/B=5/C=10), reward_target (r_mult A=3/B=2/C=1), size_multiple_by_class (A=2/B=1/C=0.5) -- all read by name from config (no magic numbers). Per-class breakdown 'aggregates_by_class' computed ONCE (backtests.py:418), served verbatim by the EXISTING GET /research/backtests/{id} + MCP (routes.py/mcp EMPTY diff). Re-ran tests/test_backtests.py green (class-scaled stop/size/reward-target + per-class partition-sum + honest empty/insufficient_sample + v1 byte-identity); tests/test_no_execution_path.py green (size is simulated notional). No-lookahead: opposing level from the same as-of compute_levels read. reports/qa/goal-tape_to_profit_support_resistence-iter-5-qa.md (12/12 TC PASS). Review PASS / QA PASS / Audit PASS / Coherence PASS."
+    },
+    "J-06": {
+      "id": "J-06",
+      "name": "structure_tape is measured honestly against the v1 champion",
+      "status": "failing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-5",
+      "last_passing_iter": null,
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "Out of scope this iter (correctly, per iter-5 spec). evaluator confirmed git diff a51313ce -- research/pnl_scan.py research/edge_report.py EMPTY (no named-strategy evaluation path added); no set_champion_pointer / champion-pointer write in the added lines. Now the SOLE remaining failing journey and fully UNBLOCKED: structure_tape carries its class-scaled risk math (J-05), so the generalized edge-report can name it and compare vs v1 on hold-out."
+    },
+    "J-07": {
+      "id": "J-07",
+      "name": "The archived eras are unchanged (regression sentinel)",
+      "status": "already_passing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-5",
+      "last_passing_iter": "goal-tape_to_profit_support_resistence-iter-5",
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "evaluator live-computed Config().config_fingerprint()=='4d665603569b9dbf' (pinned) AND proved it is INVARIANT when all 3 new structure_tape_*_by_class fields are mutated (dataclasses.replace) -> genuinely in the excluded set. tests/test_profile_equivalence.py + tests/test_no_execution_path.py green; v1 strategy_definition exits dict byte-identical (live dump). git diff a51313ce EMPTY for apps/frontend/, app/engine/, research/levels.py, routes.py, mcp/."
+    }
+  },
+  "anti_goal_violations": [],
+  "updated_at": "2026-07-06T15:15:00Z"
+}
diff --git aruns/goal-tape_to_profit_support_resistence-iter-6/plan.md bruns/goal-tape_to_profit_support_resistence-iter-6/plan.md
new file mode 100644
index 0000000..36b0b9d
--- /dev/null
+++ bruns/goal-tape_to_profit_support_resistence-iter-6/plan.md
@@ -0,0 +1,168 @@
+# goal-tape_to_profit_support_resistence-iter-6 Execution Plan
+
+Frontend Present: no
+
+## Context (why this iteration, and why it's safe)
+
+J-06 is the **sole remaining failing Must-have journey** of Era 4 (`docs/goal.md`) — the
+goal-completing iteration. iter-4 shipped `structure_tape` as a registered strategy; iter-5
+(evaluator PASS, audit PASS) added its class-scaled stop/reward/size math. J-06 asks: is
+`structure_tape` honestly better than the frozen `v1` champion on **hold-out** data? This plan
+generalizes the ONE existing sweep (`pnl_scan.py`) rather than building anything new. I
+independently verified the phase spec's reuse claims against the actual code before writing this:
+
+- `BacktestJobManager.create()` (`app/research/backtests.py:871`) stamps `params["strategy_id"]`
+  verbatim with no registry check at create-time — the check lives in `BacktestRunner.run()`
+  (line 388: `strategy = self._config.strategy_definition(params["strategy_id"]); if strategy is
+  None: raise ValueError(...)`), and `run()` **never raises out** — every failure, including an
+  unknown strategy id, is persisted as an explicit `failed` record (docstring, line 356). So
+  `pnl_scan._run_backtest`'s existing `if final.get("status") != STATUS_DONE: raise ScanError(...)`
+  already turns an unknown `--strategy` value into a clean, explicit refusal with **zero new
+  validation code required** — confirms the BACKGROUND section's claim that no new backtest path
+  is needed.
+- `store.set_champion_pointer(*, strategy_id, profile, wall_ts)` and
+  `pnl_ledger.append_validation_row(...)` already accept arbitrary strategy ids / report ids —
+  neither needs a signature change. **`store.py` and `pnl_ledger.py` should need NO code changes.**
+- `config.py` already has everything the spec says to reuse: `STRATEGY_V1_ID = "v1"`,
+  `STRATEGY_TAPE_ID = "structure_tape"`, `PROFILE_DEFAULT = "default"`,
+  `promotion_min_sample_size`, `pnl_min_sample_size`. **No new `Config` field should be needed.**
+
+This matches `docs/goal.md`'s Success Criterion 4 (`structure_tape` "judged only by the era-3
+machine and promoted only by beating the champion on the frozen hold-out set... train-only wins
+are labelled overfit and rejected") with no drift. No scope creep found in the phase spec — its own
+OUT OF SCOPE list already excludes a second module/endpoint, a second champion pointer, any
+`v1`/`default`/engine mutation, and a required `edge_report.py` generalization.
+
+## What to Build
+
+- **A strategy axis on the ONE existing sweep** (`apps/backend/app/research/pnl_scan.py`): the CLI
+  gains a `--strategy <id>` option (e.g. `--strategy structure_tape`). When given, `run_sweep()`
+  evaluates exactly ONE named-strategy candidate — backtest at `strategy_id=<named>`,
+  `profile=PROFILE_DEFAULT` — compared against the champion's **current** strategy id (read
+  verbatim from `store.get_champion_pointer()["strategy_id"]`, never hardcoded `"v1"`) also at
+  `profile=PROFILE_DEFAULT`. **With no `--strategy` given, the sweep must behave byte-identically
+  to today** (the existing profile-only candidate loop over `config.profile_registry()`) —
+  implement the new axis as an additive branch, not a refactor of the existing path, and prove it
+  with the pre-existing `test_pnl_scan.py` tests passing unmodified.
+- Reuse `_dataset_rows` / `_split_summary` / `_is_positive` / `_promote` verbatim — these are
+  already axis-agnostic (they operate on `(report_id, result)` pairs, not on "profile" per se).
+- Per-split (train, hold-out — never pooled) report: `structure_tape`'s and `v1`'s net R AND net
+  $, n, per-dataset breakdown, and candidate-minus-champion deltas.
+- `survivor` reuses the existing gate verbatim (summed hold-out delta positive on BOTH net R and
+  net $ AND summed hold-out candidate n ≥ `Config.promotion_min_sample_size` — no new min-n
+  field). `overfit` = positive train AND NOT survivor (unchanged definition).
+- Promotion of a genuine hold-out survivor reuses the existing crash-safe two-write order
+  (`append_validation_row` THEN `store.set_champion_pointer`), generalized to move the strategy
+  axis: `strategy_id=<named candidate>`, `profile=PROFILE_DEFAULT`. Pointer write only — never
+  touches `default`, `v1`, or any engine default.
+- Honest fixture outcome: on the committed train/hold-out fixture pair, `structure_tape`'s
+  hold-out n is below `promotion_min_sample_size` (2-timeframe PG fixture → mostly class-C, per
+  the iter-3 lesson) → no survivor → no promotion → champion stays `{v1, default}` → CLI exits 0.
+- Determinism: the report keeps the existing sorted-key, no-wall-clock render discipline — two
+  fresh-state runs on the fixtures produce byte-identical `--out` bytes.
+- **Disclose audit item B1** (carried from iter-4/iter-5: the breakthrough arm is a static
+  price-position test, not a fresh event-to-event cross) explicitly in the comparison report's
+  provenance/assumptions — do NOT re-arm it. Tightening it is permitted only if J-04/J-05 stay
+  provably byte-identical, which is a second risky change this plan does not ask for.
+- Extend `tests/test_no_execution_path.py`'s grep-guard to explicitly name the new comparison
+  code path (mirroring the iter-5 precedent of a dedicated test, on top of the pre-existing
+  repo-wide sweep).
+- Doc-parity: update `README.md` to describe the named-strategy comparison capability and the
+  honest "no survivor on the fixtures" finding (and verify the iter-5 rider was already applied
+  before adding a duplicate note — check `git blame`/existing bullets first).
+
+**Explicitly out of scope this iteration** (per the phase spec's own OUT OF SCOPE list — do not
+build): a new comparison/promotion module or new REST endpoint; a second champion pointer or a
+second min-n `Config` field; any change to `v1`, `default`, the tape engine, the live cockpit, or
+any engine default; a required `edge_report.py` generalization (optional, read-only only, not
+DoD-gated); any real promotion on the committed fixtures (n is honestly below the minimum — the
+promotion *path* is exercised only via synthetic ≥-min-n test fixtures); any new REST endpoint,
+nav, page, or UI change.
+
+## Agents Required
+
+- developer: yes -- generalize `pnl_scan.py`'s sweep with the named-strategy axis described above
+  (CLI `--strategy` flag, per-split comparison report, survivor/overfit gate, crash-safe
+  promotion), extend `test_pnl_scan.py` and `test_no_execution_path.py`, update `README.md`, and
+  write the dev handoff. Backend-only; no frontend agent needed.
+- backend-data: yes
+- frontend-ux: no
+
+## Frontend Present
+
+no
+
+(Frontend Present: no — machine surface only, CLI + existing REST/MCP reads. `apps/frontend/`
+MUST NOT be touched this iteration — confirm a zero frontend diff in the dev handoff, per the
+iter-0 lesson that this is what keeps J-07's cockpit leg green without a new screenshot. No browser
+QA required.)
+
+## Files to Create/Modify
+
+- `apps/backend/app/research/pnl_scan.py` -- add the `--strategy` CLI option and the strategy-axis
+  candidate path in `run_sweep()`; keep the no-flag path byte-identical to today.
+- `apps/backend/app/config.py` -- expected **no changes**; touch only if a genuinely new
+  config-owned parameter proves necessary, and then only by adding it to `config_fingerprint()`'s
+  `excluded` set (the pinned `v1`/`default` fingerprint `4d665603569b9dbf` must not move).
+- `apps/backend/app/research/store.py`, `apps/backend/app/research/pnl_ledger.py` -- expected
+  **no changes** (both already accept arbitrary strategy ids / report ids verbatim).
+- `apps/backend/tests/test_pnl_scan.py` -- extend with: named-strategy comparison shape; survivor
+  gate on the strategy axis (below-min-n vs at/above-min-n, via synthetic fixtures mirroring the
+  existing min-n tests); overfit labelling; promotion correctness + crash safety (exactly one
+  ledger row then the pointer moves to `strategy_id=structure_tape`); frozen-foundation check
+  after a promotion (fingerprint unmoved, `v1`/`default` byte-identical, engine equivalence green);
+  fixture honesty (no survivor on the committed pair); determinism; backward compatibility (the
+  existing profile-only sweep tests pass unmodified); single-source scan (pointer setter still
+  called from exactly one file); unknown-candidate-strategy-id refusal; >1 train/hold-out dataset
+  registered → promotion skipped with an honest note.
+- `apps/backend/tests/test_no_execution_path.py` -- one new test naming the strategy-axis
+  comparison/promotion code explicitly (iter-5 precedent).
+- `README.md` -- doc-parity bullet(s) for the named-strategy comparison + honest fixture finding.
+- `docs/handoffs/goal-tape_to_profit_support_resistence-iter-6-dev.md` -- dev handoff (required by
+  DoD), listing every file changed including doc edits.
+- `apps/backend/app/research/edge_report.py` -- optional, NOT required for DoD; touch only if
+  trivial and strictly read-only (no `_promote`, no ledger write, no pointer move).
+
+## Key Test Scenarios
+
+1. Named-strategy comparison shape: per split (train, hold-out, never pooled) —
+   `structure_tape` vs `v1` net R AND net $, n, per-dataset breakdown + deltas.
+2. Survivor gate on the strategy axis: a below-min-n hold-out win is NOT a survivor; an
+   at/above-min-n positive hold-out win IS a survivor (synthetic fixtures).
+3. Overfit: positive train + failing hold-out → `overfit=true`, `survivor=false`, never promoted.
+4. Promotion correctness + crash safety: exactly ONE ledger row appended THEN the pointer moves to
+   `strategy_id=structure_tape`, `profile=default`; a mid-promotion re-run hits the existing
+   `DuplicateEnhancementError` → explicit `ScanError` (no silent double-append, no orphan).
+5. Frozen foundation after a promotion: `config_fingerprint() == "4d665603569b9dbf"` unmoved,
+   `v1`/`default` byte-identical (`test_profile_equivalence.py` green), engine equivalence green.
+6. Fixture honesty: the committed train/hold-out fixture pair yields no survivor, champion stays
+   `{v1, default}`, exit 0, nothing written to the ledger, no pointer move.
+7. Determinism: two independent fresh-state runs on the fixtures produce byte-identical `--out`.
+8. Backward compatibility: the existing profile-only sweep (no `--strategy`) reproduces
+   byte-identically — every pre-existing `test_pnl_scan.py` test passes unmodified.
+9. Single-source scan: `store.set_champion_pointer` still called from exactly one source file; no
+   second net R/$/edge computation path introduced.
+10. Honest error states: corrupt dataset → explicit `ScanError`, nothing written; unknown
+    candidate strategy id → explicit refusal, never a coerced/fabricated comparison; more than one
+    train or one hold-out dataset registered → promotion explicitly skipped with an honest note,
+    comparison still fully reported.
+11. Audit B1 disclosed: the comparison report's provenance/assumptions section explicitly names
+    the breakthrough arm's loose static-price-position anchor.
+12. Grep-guard: no broker/order/routing/execution/paper-trading identifier introduced anywhere in
+    the new code (`test_no_execution_path.py` extended and green).
+13. Full regression: required-still-passing journeys J-01–J-05 and J-07 stay green — full backend
+    suite passes, engine equivalence test passes, `apps/frontend/` diff stays empty.
+
+## Notes for reviewer / QA / auditor
+
+- This is a **full-depth, goal-completing** iteration touching the champion pointer and PnL
+  ledger — expect the auditor to specifically re-verify (not just trust) the crash-safety ordering
+  and the "no train-only promotion" gate, per the phase spec's own NOTES.
+- Only the goal-evaluator (not this plan, not the developer) may declare GOAL_ACHIEVED, and only
+  after the deterministic gates and a two-key confirm. This plan marks no journey as passing.
+- Lessons carried forward (surface to developer): don't silently break
+  `_class_scaled_invalidation`'s level-relative-vs-entry-relative fallback when re-backtesting
+  `structure_tape` for the comparison (iter-5); the committed PG fixture only ever yields class-C
+  / below-min-n trades, so any ≥-min-n survivor test must use a **synthetic** fixture, never the
+  shipped PG fixture (iter-3); any new `Config` field must join the `config_fingerprint` excluded
+  set or J-07 breaks (iter-1) — prefer adding none.
diff --git aruns/goal-tape_to_profit_support_resistence-iter-6/status.json bruns/goal-tape_to_profit_support_resistence-iter-6/status.json
new file mode 100644
index 0000000..f2e3703
--- /dev/null
+++ bruns/goal-tape_to_profit_support_resistence-iter-6/status.json
@@ -0,0 +1,19 @@
+{
+  "phase": "goal-tape_to_profit_support_resistence-iter-6",
+  "status": "complete",
+  "current_step": "closure_passed",
+  "updated_at": "2026-07-06T17:29:51.917093Z",
+  "started_at": "2026-07-06T15:16:18.669768Z",
+  "cli": "claude",
+  "blockers": [],
+  "changed_files": [
+    "apps/backend/app/research/pnl_scan.py",
+    "apps/backend/tests/test_pnl_scan.py",
+    "apps/backend/tests/test_no_execution_path.py",
+    "README.md"
+  ],
+  "tests_run": true,
+  "browser_checks_run": false,
+  "qa_complete": true,
+  "next_action": "auditor"
+}
```
