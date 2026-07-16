# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

```diff
diff --git a/README.md b/README.md
index 38de2d5..c644726 100644
--- a/README.md
+++ b/README.md
@@ -83,6 +83,7 @@ Current capabilities:
 - **Real tape recorded and joined at wall-touch events (command-line research tool + research API)** — with market-data vendor credentials configured, a dedicated recording tool captures a real trade-by-trade market-data window (an hour before through 90 minutes after) around the best-scoring touch events from the case-study registry, spreading its picks across as many different stocks as possible and always including the project's pinned reference example. Once a touch event has a matching real recording, opening that event's detail view replays the frozen tape-reading engine over the recording and attaches a timeline of what buyers and sellers were actually doing around the touch — for example, sellers absorbing at the ask right before a rejection, or buyers in control through a break. Events with no matching recording show an honestly empty timeline rather than an invented one. Real recordings today span a broad slice of the panel, including the pinned reference example, whose drill-in now shows a real, second-by-second tape reading in place of the earlier empty placeholder. Each drill-in replays its recorded window fresh on every open rather than caching the result, so a large window can take several minutes to load. A committed real-data sample keeps this timeline check running with no credentials required. This timeline is now visible in the browser inside each event's Case Studies drill-in on the Structure page, and remains reachable through the research API and the matching machine-readable tool.
 - **A third registered strategy, `structure_tape_map` (research API)** — the app now has three registered ways of simulating trades against historical data: the original `v1`, the frozen `structure_tape` (which trades off the raw list of thousands of individual price levels), and this new one, which trades off the same small handful of tradable bands the level map produces instead. It reuses the exact same class-scaled stop/target/position-sizing rules as `structure_tape` — only which levels it watches differs. Registering it changes nothing about `v1`, `structure_tape`, or their past results. It appears as its own card in the Structure page's strategy Registry section and is exercised automatically as part of the 3-way edge report below (now also visible on the Structure page); it is runnable through the existing backtest API, but there is no button yet to pick it directly for a standalone ad hoc backtest in the browser.
 - **The 3-way profit edge report (research API)** — a new endpoint runs `v1`, `structure_tape`, and `structure_tape_map` over every recorded practice-tape window and reports, honestly, how each one actually did — broken down by price-level quality (A/B/C), which side of the market it traded (support or resistance), how price reacted at the touch (rejected, broke, or chopped), and which data feed the window came from. Every dollar figure carries its sample size, a comparison against a random-entry baseline, and the same "simulated — not indicative of live results" register used everywhere else in the app. Real recorded trading windows now exist across a broad slice of the panel, giving the report real touches to measure instead of only the small practice dataset; any cell still short of enough trades honestly labels itself "insufficient sample" rather than manufacturing a result, and an entirely empty report remains a valid, honest outcome whenever nothing yet clears the bar. Computing the full report over the currently recorded data is slow and can take a long time to finish on a first run, showing a loading state throughout rather than a fabricated interim result. The same comparison is available to AI tools through the machine-readable connection, byte-for-byte identical to what a person sees calling the endpoint directly. This report is now visible on the Structure page in the browser as the Edge Report, and remains reachable through the research API and the matching machine-readable tool.
+- **Edge report caching and a permanent record of its findings (research API)** — once the 3-way profit edge report's full computation over recorded data has completed a single time, the result is now remembered in a durable, disk-backed cache and served back within an interactive few seconds on every later request — through the REST API, the machine-readable connection, and the Structure page's Edge Report panel alike — including after a full backend restart. Nothing about what the report measures, how it is computed, or the shape of its response changes; any change to the underlying recorded datasets, registered strategies, or configuration automatically invalidates the cached answer, so the next request recomputes it byte-identically rather than serving something stale. A finished report's findings can also now be permanently appended, as a deliberate one-time step, to the same append-only profit-and-loss record described above — its own dedicated entry, with every data feed and the train/hold-out split kept fully separate from every entry recorded before it. As of today the very first full computation over the currently recorded real data, and its permanent recording, have not yet been run, so the report still shows its honest loading state until an operator lets that first computation finish.
 - **Cockpit price-chart tradable bands and a descriptive confluence chip** — the tradable support/resistance bands from the Structure page's map now also draw directly on the live cockpit price chart while watching a symbol in Simulated or Historical mode: one or two solid price lines per band (rose for resistance, emerald for support), each labeled with side, class, quality score, and whether it sits on a round number — alongside the existing tape-state markers and any declared-thesis lines, without changing how those render. A small descriptive banner appears beneath the chart only when the last traded price sits inside one of those bands AND the live tape reading matches that band's configured rejection-or-breakthrough state — for example "Inside R-band 300.05–300.17 (class A) · tape: Ask Absorption (rejection) · measured history: edge report." The banner states the current condition and points to the edge report as measured history; it never tells you to buy or sell and never predicts an outcome. A simulated ticker with no real recorded price history shows an honest "No tradable map for TICKER" note instead of a fabricated band. Live mode is unchanged — the price chart, and therefore the bands and banner, stay hidden there exactly as before.
 - **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `GET /meta/ui-routes`.
 - **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, journal, studies, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, profit edge reports, and navigation data a person sees. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
diff --git a/apps/backend/app/research/pnl_ledger.py b/apps/backend/app/research/pnl_ledger.py
index 9331ce2..ab72b2b 100644
--- a/apps/backend/app/research/pnl_ledger.py
+++ b/apps/backend/app/research/pnl_ledger.py
@@ -333,11 +333,15 @@ def _ddmmyyyy(created_utc: str) -> str:
 
 def _render_strategy_comparison_row_lines(row: dict, index: int) -> list[str]:
     """The era-5B J-08 rendering branch for a ``_KIND_STRATEGY_COMPARISON`` row — a per-cell
-    table (strategy x class x side x reaction x feed) for each split, mirroring the EXISTING
+    table (strategy x class x band side x reaction x feed) for each split, mirroring the EXISTING
     two-way row's table shape (one line per measurement, net R beside net $ beside n beside its
-    sample label) but WITHOUT a ``side`` column (there is no baseline/candidate distinction here —
-    ``strategy_id`` already carries that role, comparing all three registered strategies
-    side-by-side)."""
+    sample label) WITH a ``band side`` column (iter-10 rename — the column holds
+    ``cell["band_side"]``, i.e. ``support``/``resistance``). It is labelled ``band side`` rather
+    than the pre-existing two-way row's own ``side`` column (below) specifically to avoid
+    collision: THAT column holds the baseline/candidate role, while THIS column holds a band's
+    support/resistance side — two different meanings that would otherwise share one ambiguous
+    header. ``strategy_id`` carries the three-way comparison role, comparing all three registered
+    strategies side-by-side."""
     lines = [
         f"## {index}. {row['title']}",
         "",
@@ -361,8 +365,8 @@ def _render_strategy_comparison_row_lines(row: dict, index: int) -> list[str]:
             lines += ["No cells for this split.", ""]
             continue
         lines += [
-            "| strategy | class | side | reaction | feed | net R | net $ | n | sample |",
-            "|----------|-------|------|----------|------|------:|------:|--:|--------|",
+            "| strategy | class | band side | reaction | feed | net R | net $ | n | sample |",
+            "|----------|-------|-----------|----------|------|------:|------:|--:|--------|",
         ]
         for cell in cells:
             measurement = cell["measurement"]
diff --git a/apps/backend/tests/test_pnl_history.py b/apps/backend/tests/test_pnl_history.py
index d22293c..ac82ea6 100644
--- a/apps/backend/tests/test_pnl_history.py
+++ b/apps/backend/tests/test_pnl_history.py
@@ -77,7 +77,7 @@ def test_append_and_render_writes_the_new_row_and_regenerates_markdown(tmp_path)
     text = out_path.read_text()
     assert "cli append test" in text
     assert "e-cli-1" in text
-    assert "strategy | class | side | reaction | feed" in text
+    assert "strategy | class | band side | reaction | feed" in text
 
 
 def test_append_and_render_raises_and_writes_nothing_on_a_malformed_report(tmp_path):
diff --git a/apps/backend/tests/test_pnl_ledger.py b/apps/backend/tests/test_pnl_ledger.py
index 29c2875..0f621fc 100644
--- a/apps/backend/tests/test_pnl_ledger.py
+++ b/apps/backend/tests/test_pnl_ledger.py
@@ -734,7 +734,7 @@ def test_existing_two_way_rows_render_unchanged_alongside_a_new_3way_row(fresh_s
     # (2) The NEW row's own section follows, with its own distinct per-cell table shape.
     assert "## 2. new 3way" in combined_md
     assert "e-new" in combined_md
-    assert "strategy | class | side | reaction | feed" in combined_md
+    assert "strategy | class | band side | reaction | feed" in combined_md
 
 
 def test_committed_pnl_history_file_is_not_a_default_target_of_these_tests(fresh_store):
```
