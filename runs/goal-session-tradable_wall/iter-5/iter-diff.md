# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

```diff
diff --git a/README.md b/README.md
index 1a5781f..5624626 100644
--- a/README.md
+++ b/README.md
@@ -81,8 +81,10 @@ Current capabilities:
 - **Tradable level map (research API)** — distills a symbol's raw support/resistance levels (which can number in the thousands for a heavily traded stock) down to at most 10 price "bands" total — the handful of price zones actually worth marking on a chart. Each band carries its price range, whether it is support or resistance, a quality score, how many underlying levels back it up, whether it sits on a psychologically "round" price, and an inherited A/B/C conviction class where one applies. The map for any given day is built using only data fully available before that trading day started — mirroring how a trader marks up charts before the open — with weekends and market holidays handled automatically by falling back to whichever trading day actually closed last. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
 - **Touch-event scanner and case-study registry (research API)** — walks every stored trading session in a 12-symbol panel's recorded price history and checks each session's actual price action against that session's own tradable level map, built strictly from data available before the session opened, so a later session's data can never change an earlier one's already-recorded result. Every genuine touch of a band is logged with its outcome — rejected and turned away, broken straight through, or chopped near the wall with no clear outcome — together with how far price moved by two later checkpoints. Run against real, freshly fetched price history for the full panel, the registry already holds several hundred touch events across all 12 symbols, a healthy mix of breakouts, rejections, and chops, with identical requests always returning byte-identical results. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
 - **Real tape recorded and joined at wall-touch events (command-line research tool + research API)** — with market-data vendor credentials configured, a dedicated recording tool captures a real trade-by-trade market-data window (an hour before through 90 minutes after) around the best-scoring touch events from the case-study registry, spreading its picks across as many different stocks as possible and always including the project's pinned reference example. Once a touch event has a matching real recording, opening that event's detail view replays the frozen tape-reading engine over the recording and attaches a timeline of what buyers and sellers were actually doing around the touch — for example, sellers absorbing at the ask right before a rejection, or buyers in control through a break. Events with no matching recording show an honestly empty timeline rather than an invented one. A committed real-data sample keeps this timeline check running with no credentials required. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
-- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /meta/ui-routes`.
-- **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, journal, studies, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, and navigation data a person sees. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
+- **A third registered strategy, `structure_tape_map` (research API)** — the app now has three registered ways of simulating trades against historical data: the original `v1`, the frozen `structure_tape` (which trades off the raw list of thousands of individual price levels), and this new one, which trades off the same small handful of tradable bands the level map produces instead. It reuses the exact same class-scaled stop/target/position-sizing rules as `structure_tape` — only which levels it watches differs. Registering it changes nothing about `v1`, `structure_tape`, or their past results. It is runnable through the existing backtest API; today it is only exercised automatically as part of the 3-way edge report below, and there is no button yet to pick it directly in the browser.
+- **The 3-way profit edge report (research API)** — a new endpoint runs `v1`, `structure_tape`, and `structure_tape_map` over every recorded practice-tape window and reports, honestly, how each one actually did — broken down by price-level quality (A/B/C), which side of the market it traded (support or resistance), how price reacted at the touch (rejected, broke, or chopped), and which data feed the window came from. Every dollar figure carries its sample size, a comparison against a random-entry baseline, and the same "simulated — not indicative of live results" register used everywhere else in the app. With only the small practice dataset available today the report is honestly empty — no strategy yet has enough recorded real-world touches to report a result — rather than a manufactured one; once real trading windows are recorded it will start showing real, if still small-sample, numbers. The same comparison is available to AI tools through the machine-readable connection, byte-for-byte identical to what a person sees calling the endpoint directly. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
+- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `GET /meta/ui-routes`.
+- **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, journal, studies, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, profit edge reports, and navigation data a person sees. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 <!-- /AUTO:capabilities -->
 
 This project embeds the [`incredible_auto_dev`](https://github.com/dennisccy/incredible_auto_dev)
diff --git a/apps/backend/app/research/setups.py b/apps/backend/app/research/setups.py
index 8ffc759..7e39887 100644
--- a/apps/backend/app/research/setups.py
+++ b/apps/backend/app/research/setups.py
@@ -97,6 +97,25 @@ dataset's OWN stamped ``epoch_anchor`` plus the snapshot's logical timestamp --
 ``epoch_anchor + logical_ts`` reconstruction ``serializers.serialize_history``'s chart projection
 already uses, never a raw logical offset (which would misread as a bogus near-1970 date). An event
 with no matching recorded dataset keeps its honestly empty ``tape_timeline`` -- never fabricated.
+
+**B1 -- additive recency-boundary disclosure (era-5B iter-5).** A touch inside the store's MOST
+RECENT stored session may not yet have ``Config.setups_forward_return_horizons_bars[0]`` bars of
+history past it -- the store simply has not accumulated that much real data yet, the SAME shape
+every freshly-fetched panel symbol's latest session is in until enough later bars arrive. Rather
+than silently pairing a definitive ``reaction`` label with a horizon-0 ``forward_returns`` entry of
+``None`` with no explanation, every event additively carries ``effective_reaction_horizon_bars``
+(the bar count the reaction close was ACTUALLY read at -- equal to the full configured
+``horizons[0]`` whenever the store held enough bars) and ``reaction_boundary_truncated`` (``True``
+exactly when it did not). Neither field ever changes ``reaction`` itself or excludes the event --
+see ``_reaction_and_forward_returns``'s own docstring for the exact boundary condition.
+
+**B3 -- a process-local memoized scan (era-5B iter-5).** ``GET /research/setups``,
+``GET /research/setups/{id}``, and ``edge_report.run_strategy_comparison_report`` each call
+``compute_setups(store, config)`` independently; on the populated 12-symbol panel the underlying
+scan takes minutes, so without a cache a single page load could trigger it multiple times over. The
+PUBLIC ``compute_setups`` below is now a thin, byte-identical memoizing wrapper around the real scan
+(renamed ``_run_full_panel_scan``) -- see its own docstring for the caching contract (process-local,
+store-content-keyed, rebuildable, never a second source of truth -- the ``bar_index.py`` precedent).
 """
 
 from __future__ import annotations
@@ -196,12 +215,23 @@ def _touches(price_low: float, price_high: float, session_bars: list[RawBar], ma
 
 def _reaction_and_forward_returns(
     all_bars: list[RawBar], touch_index: int, side: str, price_low: float, price_high: float, config: Config,
-) -> tuple[str, list[dict]] | None:
-    """The touch's reaction label + forward-return list, or ``None`` when NO bar at all follows the
-    touch (nothing to react with -- the event is excluded, never fabricated). Reaction is decided
-    from the CLOSE at the shortest configured horizon (never an intrabar wick, never volume) versus
-    each band edge widened by ``Config.setups_reaction_threshold_bps``; every configured horizon is
-    then reported, honestly ``None`` for any horizon reaching past the end of the store."""
+) -> tuple[str, list[dict], int, bool] | None:
+    """The touch's reaction label + forward-return list + the B1 recency-boundary disclosure, or
+    ``None`` when NO bar at all follows the touch (nothing to react with -- the event is excluded,
+    never fabricated). Reaction is decided from the CLOSE at the shortest configured horizon (never
+    an intrabar wick, never volume) versus each band edge widened by
+    ``Config.setups_reaction_threshold_bps``; every configured horizon is then reported, honestly
+    ``None`` for any horizon reaching past the end of the store.
+
+    **B1 -- additive recency-boundary disclosure (era-5B iter-5).** When the store does not YET
+    hold ``horizons[0]`` bars past the touch (a touch inside the most-recent stored session), the
+    reaction is still read from whatever close IS available -- honest, never suppressed -- but its
+    horizon is a TRUNCATED sub-horizon of the configured one. This is disclosed, never hidden: the
+    returned ``effective_reaction_horizon_bars`` is the bar count the reaction close was ACTUALLY
+    read at (``== horizons[0]`` whenever untruncated), and ``reaction_boundary_truncated`` is
+    ``True`` exactly when ``touch_index + horizons[0] >= len(all_bars)``. Neither value ever
+    changes the ``reaction`` label itself -- a caller decides how to present a truncated-horizon
+    label; this function only discloses the truncation honestly."""
     if touch_index >= len(all_bars) - 1:
         return None
     horizons = config.setups_forward_return_horizons_bars
@@ -209,6 +239,8 @@ def _reaction_and_forward_returns(
     threshold = config.setups_reaction_threshold_bps / 10_000.0
 
     reaction_index = min(touch_index + horizons[0], len(all_bars) - 1)
+    effective_reaction_horizon_bars = reaction_index - touch_index
+    reaction_boundary_truncated = touch_index + horizons[0] >= len(all_bars)
     reaction_close = all_bars[reaction_index].close
     if side == RESISTANCE:
         broke_level = price_high * (1.0 + threshold)
@@ -231,7 +263,7 @@ def _reaction_and_forward_returns(
                 "horizon_bars": horizon,
                 "return_fraction": (all_bars[target_index].close - touch_close) / touch_close,
             })
-    return reaction, forward_returns
+    return reaction, forward_returns, effective_reaction_horizon_bars, reaction_boundary_truncated
 
 
 def _event_id(symbol: str, session_date_iso: str, band: dict, touch_ts: str) -> str:
@@ -247,6 +279,7 @@ def _event_id(symbol: str, session_date_iso: str, band: dict, touch_ts: str) ->
 
 def _event(
     symbol: str, session_date_value: date, band: dict, touch_bar: RawBar, reaction: str, forward_returns: list[dict],
+    effective_reaction_horizon_bars: int, reaction_boundary_truncated: bool,
 ) -> dict:
     session_date_iso = session_date_value.isoformat()
     touch_ts = _iso(touch_bar.epoch)
@@ -263,6 +296,11 @@ def _event(
         "touch_volume": touch_bar.volume,
         "reaction": reaction,
         "forward_returns": forward_returns,
+        # B1 (era-5B iter-5): additive recency-boundary disclosure -- see
+        # `_reaction_and_forward_returns`'s own docstring. Never mutates `reaction` above, never
+        # excludes an event -- a truncated-horizon label is disclosed, not suppressed.
+        "effective_reaction_horizon_bars": effective_reaction_horizon_bars,
+        "reaction_boundary_truncated": reaction_boundary_truncated,
         # Present-but-empty until J-03 records the real tape and joins its five-state timeline
         # onto this event (goal.md capability 4) -- never omitted, never fabricated meanwhile.
         "tape_timeline": [],
@@ -279,10 +317,73 @@ def _event_sort_key(event: dict) -> tuple:
     )
 
 
+# --- B3 (era-5B iter-5): a process-local, rebuildable, byte-identical memoization of the ONE
+# full-panel scan `compute_setups` performs -- see the module docstring's own B3 note.
+# `GET /research/setups`, `GET /research/setups/{id}`, and
+# `edge_report.run_strategy_comparison_report` each call `compute_setups(store, config)`
+# independently (routes.py's `list_setups`/`get_setup`, `edge_report.py`'s
+# `run_strategy_comparison_report`); on the populated 12-symbol store the underlying scan takes
+# minutes, so without this layer a single page load could trigger it several times over, well past
+# browser-QA timeouts. This is the SAME "rebuildable accelerator, never a second source of truth"
+# contract `bar_index.py` lives under (see that module's own docstring), but PROCESS-LOCAL and
+# in-memory only -- never SQLite/disk-persisted, and never itself read by anything outside this
+# module. `compute_setups`'s own signature is UNCHANGED, so every caller (routes.py, edge_report.py)
+# needs zero changes -- only ITS body differs (a cache check wrapping the real scan, renamed
+# `_run_full_panel_scan` below).
+#
+# Keyed on (a) the config object's OWN identity -- every production caller shares the ONE imported
+# `CONFIG` singleton (routes.py, edge_report.py), so this is stable for the life of the process;
+# a test constructing its own `Config(...)` keeps it alive for that call's duration (referenced
+# locally), so a fresh id is never reused mid-call -- and (b) a deterministic content signature over
+# `store.list()` (sorted `(symbol, timeframe, id, checksum)` tuples -- `bars.py` already exposes a
+# per-series `checksum` in every list record, so this reuses an existing value rather than hashing
+# raw bars). `Config` cannot be used as a key directly (it carries plain `dict` fields, e.g.
+# `tradability_quality_weights`, so it is not hashable). Any change to the store's registered series
+# set -- a new recording, a symbol's series replaced -- changes the signature and busts the cache;
+# an untouched store always replays the identical cached result. A single most-recent SLOT (not an
+# unbounded dict) is intentional: this codebase runs ONE bar store behind ONE process, so there is
+# never more than one "current" scan worth remembering, and a single slot cannot grow unbounded
+# across a long-lived process or an entire test suite's run.
+_SCAN_CACHE: dict[str, object] = {"key": None, "result": None}
+
+
+def _store_signature(store: BarStore) -> tuple:
+    """A deterministic fingerprint of everything ``compute_setups`` can possibly read from
+    ``store``: every HEALTHY series' ``(symbol, timeframe, id, checksum)``, sorted for
+    order-independence. A corrupt file (``store.list()``'s own ``errors`` return) is excluded --
+    ``compute_setups`` itself never reads a corrupt file's content either (``_select_5m_series``
+    only ever sees ``records``), so a corrupt file's mere presence/absence can never change the
+    scan's OWN output and is rightly left out of what busts the cache."""
+    records, _errors = store.list()
+    return tuple(sorted(
+        (record["symbol"], record["timeframe"], record["id"], record["checksum"])
+        for record in records
+    ))
+
+
 def compute_setups(store: BarStore, config: Config) -> dict:
     """The canonical ``GET /research/setups`` + MCP ``setups`` computation (single source of
     truth) -- see module docstring for the full algorithm. Returns ``{"events": [...]}``; an empty
-    list is an honest "nothing scanned yet / nothing touched", never an error."""
+    list is an honest "nothing scanned yet / nothing touched", never an error.
+
+    Served from the B3 process-local scan cache (see the block comment above) whenever ``store``'s
+    content signature and ``config``'s identity match the last computed call; otherwise this runs
+    the real scan (``_run_full_panel_scan``) once and remembers it. Byte-identical either way -- the
+    cache changes nothing about WHAT is returned, only whether it is recomputed."""
+    key = (id(config), _store_signature(store))
+    if _SCAN_CACHE["key"] == key:
+        return _SCAN_CACHE["result"]
+    result = _run_full_panel_scan(store, config)
+    _SCAN_CACHE["key"] = key
+    _SCAN_CACHE["result"] = result
+    return result
+
+
+def _run_full_panel_scan(store: BarStore, config: Config) -> dict:
+    """The real, uncached full-panel scan -- unchanged algorithm from before B3, only renamed so
+    the public ``compute_setups`` above can wrap it with the process-local cache. See the module
+    docstring for the full algorithm; never called directly by any route or report -- only through
+    ``compute_setups``."""
     events: list[dict] = []
     for symbol in config.setups_panel_symbols:
         five_min_bars = _select_5m_series(store, symbol)
@@ -307,10 +408,10 @@ def compute_setups(store: BarStore, config: Config) -> dict:
                     )
                     if outcome is None:
                         continue  # no bar at all follows the touch -- nothing to react with
-                    reaction, forward_returns = outcome
+                    reaction, forward_returns, effective_horizon, boundary_truncated = outcome
                     events.append(_event(
                         symbol, session_date_value, band, five_min_bars[touch_index],
-                        reaction, forward_returns,
+                        reaction, forward_returns, effective_horizon, boundary_truncated,
                     ))
     events.sort(key=_event_sort_key)
     return {"events": events}
diff --git a/apps/backend/tests/test_setups.py b/apps/backend/tests/test_setups.py
index 9997213..aaa47c2 100644
--- a/apps/backend/tests/test_setups.py
+++ b/apps/backend/tests/test_setups.py
@@ -492,7 +492,8 @@ def test_aapl_pinned_2026_06_22_event_is_rejected_with_negative_forward_returns(
     _seed_yahoo_fixture(store, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
     _seed_yahoo_fixture(store, _load_yahoo_fixture(AAPL_5M_SETUPS_FIXTURE))
 
-    result = compute_setups(store, Config(setups_panel_symbols=("AAPL",)))
+    config = Config(setups_panel_symbols=("AAPL",))
+    result = compute_setups(store, config)
     day_events = _events_for(result, "AAPL", "2026-06-22")
     assert day_events, "the pinned 2026-06-22 session must emit at least one event"
 
@@ -509,6 +510,10 @@ def test_aapl_pinned_2026_06_22_event_is_rejected_with_negative_forward_returns(
     assert pinned["touch_ts"] == "2026-06-22T13:30:00.000000Z"
     assert pinned["band"]["round_number"] is True
     assert pinned["tape_timeline"] == []
+    # B1 (era-5B iter-5): the pinned event is nowhere near the store's recency boundary -- byte-
+    # identical to before, plus the two new additive fields at their honest "untruncated" values.
+    assert pinned["reaction_boundary_truncated"] is False
+    assert pinned["effective_reaction_horizon_bars"] == config.setups_forward_return_horizons_bars[0] == 78
 
 
 def test_aapl_repeat_scan_determinism(tmp_path):
@@ -752,12 +757,18 @@ def test_setups_join_reuses_dataset_store_replay_never_a_second_tape_engine():
 
 def test_compute_setups_itself_never_touches_the_dataset_store():
     """Architecture guard: the join lives ONLY in ``enrich_with_tape_timeline``, called ONLY from
-    the ``GET /research/setups/{id}`` route -- ``compute_setups``'s own shared scan loop (used by
-    BOTH the list and detail routes) must stay completely free of any ``DatasetStore`` reference,
-    so the join never adds an O(events) dataset-store scan to the already-slow full-panel list
-    route."""
-    src = inspect.getsource(compute_setups)
-    assert "dataset" not in src.lower(), "compute_setups must never reference the dataset store"
+    the ``GET /research/setups/{id}`` route -- neither the public ``compute_setups`` (the B3 cache
+    wrapper, era-5B iter-5) nor its internal ``_run_full_panel_scan`` (the actual shared scan loop
+    used by BOTH the list and detail routes) may ever reference the ``DatasetStore``, so the join
+    never adds an O(events) dataset-store scan to the already-slow full-panel list route."""
+    from app.research.setups import _run_full_panel_scan
+
+    assert "dataset" not in inspect.getsource(compute_setups).lower(), (
+        "compute_setups must never reference the dataset store"
+    )
+    assert "dataset" not in inspect.getsource(_run_full_panel_scan).lower(), (
+        "_run_full_panel_scan must never reference the dataset store"
+    )
 
 
 # --- Config: the recording constants are excluded from config_fingerprint -----------------------
@@ -771,3 +782,196 @@ def test_recording_config_fields_are_excluded_from_config_fingerprint():
     assert Config(recording_holdout_fraction=0.99).config_fingerprint() == CONFIG.config_fingerprint()
     # ...while a real classifier threshold still moves it (the counter-test).
     assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()
+
+
+# --- B1 (era-5B iter-5): the recency-boundary regression -- a purpose-built fixture whose final
+# touch has FEWER than the shipped ``setups_forward_return_horizons_bars[0]`` (78) bars remaining
+# anywhere in the store, mirroring SYN-SETUPS-A's proven ``_DAILY_A``/``_SESSION_DAY3`` shape (a
+# singleton 250.10 resistance level, a touch that decisively fails back off it) but with only 5
+# total "5m" bars in the WHOLE store -- so the store runs out of bars LONG before the real 78-bar
+# horizon elapses, the exact shape a freshly-fetched panel symbol's latest session is in every day
+# until enough later bars accumulate. The committed AAPL fixtures (`AAPL_5m_20260615_20260630.json`)
+# stop 2026-06-30 -- comfortably far from any recency boundary -- so they cannot exercise this path
+# (iter-2 + iter-4 lesson): this dedicated symbol/fixture is required. -------------------------------
+
+SYM_BOUNDARY = "SYN-SETUPS-BOUNDARY"
+
+_DAILY_BOUNDARY: tuple[RawBar, ...] = (
+    _daily(SYM_BOUNDARY, 0, 210.00, 190.00, 200.00),  # filler -- far from the target level
+    _daily(SYM_BOUNDARY, 1, 215.00, 185.00, 200.00),  # filler -- far from the target level
+    _daily(SYM_BOUNDARY, 2, 250.10, 150.10, 200.00),  # the ONE level-forming daily bar
+)
+
+# Day 3's own (and ONLY) "5m" session: deliberately just 5 bars -- the exact SYN-SETUPS-A
+# ``_SESSION_DAY3`` touch/price shape (a clean REJECTED example), truncated after its former +2
+# reaction-close bar so the WHOLE store ends there. With the real horizons[0]=78, the reaction
+# close for the touch at index 0 is capped at index 4 (the last bar in the store) -- an
+# effective horizon of 4 bars, not 78.
+_SESSION_BOUNDARY: tuple[RawBar, ...] = (
+    _bar5m(SYM_BOUNDARY, 3, 0, 249.80, 250.15, 249.70, 250.05, 5_000),  # touch (index 0)
+    _bar5m(SYM_BOUNDARY, 3, 1, 250.05, 250.10, 249.00, 249.20, 4_000),
+    _bar5m(SYM_BOUNDARY, 3, 2, 249.20, 249.30, 248.50, 248.80, 3_000),
+    _bar5m(SYM_BOUNDARY, 3, 3, 248.80, 249.00, 248.00, 248.30, 3_000),
+    _bar5m(SYM_BOUNDARY, 3, 4, 248.30, 248.50, 247.80, 248.00, 3_000),  # last bar in the store
+)
+
+
+def _seed_boundary(store: BarStore) -> None:
+    store.record(
+        symbol=SYM_BOUNDARY, timeframe="1d", window_start_utc="2026-01-01T00:00:00Z",
+        window_end_utc="2026-01-04T00:00:00Z", feed="sip", bars=list(_DAILY_BOUNDARY),
+    )
+    store.record(
+        symbol=SYM_BOUNDARY, timeframe="5m", window_start_utc="2026-01-04T00:00:00Z",
+        window_end_utc="2026-01-04T00:25:00Z", feed="sip", bars=list(_SESSION_BOUNDARY),
+    )
+
+
+def test_boundary_touch_discloses_truncated_horizon_with_a_definitive_reaction(tmp_path):
+    """B1 (era-5B iter-5) headline regression: a touch inside the store's MOST RECENT (and only)
+    session, with fewer than the shipped ``setups_forward_return_horizons_bars[0]`` (78) bars
+    remaining anywhere in the store, still gets a DEFINITIVE reaction label -- but the event now
+    additively discloses that the horizon was truncated, rather than silently pairing a definitive
+    label with a bare ``None`` horizon-0 return. All values verified by direct computation against
+    this exact fixture (never hand-derived): touch at index 0 of a 5-bar store, reaction read at
+    the last available bar (index 4, close 248.00) -- decisively below the 30bps-widened reject
+    level of a singleton 250.10 resistance band -> REJECTED, effective horizon 4 (not 78)."""
+    store = BarStore(tmp_path / "bars")
+    _seed_boundary(store)
+    config = Config(setups_panel_symbols=(SYM_BOUNDARY,))
+    assert config.setups_forward_return_horizons_bars[0] == 78, (
+        "this regression must exercise the REAL shipped horizon, never a small test-only override"
+    )
+
+    result = compute_setups(store, config)
+    events = result["events"]
+    assert len(events) == 1, "the engineered fixture emits exactly one boundary touch event"
+    event = events[0]
+
+    assert event["band"]["side"] == "resistance"
+    assert event["band"]["price_low"] == event["band"]["price_high"] == 250.10
+    assert event["touch_ts"] == "2026-01-04T00:00:00.000000Z"
+    assert event["reaction"] in (REJECTED, BROKE, CHOPPED), "a definitive label, never suppressed"
+    assert event["reaction"] == REJECTED
+    assert event["forward_returns"][0] == {"horizon_bars": 78, "return_fraction": None}
+    assert event["reaction_boundary_truncated"] is True
+    assert event["effective_reaction_horizon_bars"] == 4
+    assert event["effective_reaction_horizon_bars"] < config.setups_forward_return_horizons_bars[0]
+
+
+def test_boundary_regression_is_deterministic_across_repeat_scans(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    _seed_boundary(store)
+    config = Config(setups_panel_symbols=(SYM_BOUNDARY,))
+    first = compute_setups(store, config)
+    second = compute_setups(BarStore(tmp_path / "bars"), config)
+    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
+
+
+# --- B3 (era-5B iter-5): the process-local memoized scan cache ----------------------------------
+# `compute_setups` is now a thin cache wrapper around the real scan (`_run_full_panel_scan`,
+# exercised directly here to prove cache vs. fresh byte-identity). All four tests below use the
+# SYN-SETUPS-A/B fixtures (`_seed_full`) except the immutable-safety test, which reuses the PG
+# tape-join fixtures below (a real, non-empty ``tape_timeline`` is the only genuine proof that an
+# enriched read could corrupt the shared cache if it were not copy-on-write).
+
+
+def test_cache_hit_is_byte_identical_to_a_fresh_uncached_scan(tmp_path):
+    """A cache HIT (the second ``compute_setups`` call) must be byte-identical to a genuinely
+    fresh, uncached scan (``_run_full_panel_scan``, called directly, bypassing the cache entirely)
+    -- the cache changes only WHETHER the scan runs, never WHAT it returns."""
+    from app.research.setups import _run_full_panel_scan
+
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    config = _syn_config()
+
+    first = compute_setups(store, config)  # populates the cache
+    cached = compute_setups(store, config)  # a cache HIT
+    fresh = _run_full_panel_scan(store, config)  # bypasses the cache entirely
+
+    first_json = json.dumps(first, sort_keys=True)
+    assert first_json == json.dumps(cached, sort_keys=True) == json.dumps(fresh, sort_keys=True)
+    assert len(fresh["events"]) >= 1, "the proof must exercise at least one real event"
+
+
+def test_scan_runs_at_most_once_across_repeated_reads_of_an_unchanged_store(tmp_path, monkeypatch):
+    """The underlying scan body runs exactly ONCE across repeated ``compute_setups`` calls against
+    an unchanged store/config (a call-count spy, never wall-clock) -- the
+    ``test_compute_setups_runs_at_most_once_per_report_call`` precedent in
+    ``test_edge_report.py``, applied one layer down to the scan itself."""
+    import app.research.setups as setups_module
+
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    config = _syn_config()
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
+    for _ in range(4):
+        compute_setups(store, config)
+    assert len(calls) == 1, "an unchanged store/config must only ever trigger ONE real scan"
+
+
+def test_cache_busts_and_rescans_when_the_store_gains_a_new_series(tmp_path, monkeypatch):
+    """Mutating the store (registering a brand-new series) must bust the cache and re-run the
+    scan on the VERY NEXT read -- never serve a stale result computed before the mutation."""
+    import app.research.setups as setups_module
+
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    config = _syn_config()
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
+    compute_setups(store, config)
+    compute_setups(store, config)
+    assert len(calls) == 1, "unchanged store so far -- still just the one real scan"
+
+    # A brand-new registered series -- any content -- changes the store's own content signature.
+    store.record(
+        symbol=SYM_B, timeframe="1d", window_start_utc="2026-03-01T00:00:00Z",
+        window_end_utc="2026-03-02T00:00:00Z", feed="sip",
+        bars=[_daily(SYM_B, 60, 999.0, 998.0, 998.5)],
+    )
+    compute_setups(store, config)
+    assert len(calls) == 2, "a newly registered series must bust the cache and re-run the scan"
+
+
+def test_enriched_detail_read_never_leaks_into_the_shared_cached_list(tmp_path):
+    """The B3 immutable-safety guard: a ``/setups/{id}``-style enriched read
+    (``enrich_with_tape_timeline``, already copy-on-write per its own docstring) must never
+    corrupt the SHARED cached list a subsequent ``/setups``-style list read serves. Uses the real
+    committed J-03 tape-join fixture so the enrichment is genuinely non-empty -- an empty-to-empty
+    enrichment would prove nothing."""
+    store = BarStore(tmp_path / "bars")
+    _seed_pg_join_bars(store)
+    config = _pg_join_config()
+
+    listed_before = compute_setups(store, config)
+    event = listed_before["events"][0]
+    assert event["tape_timeline"] == [], "unenriched, exactly like every fresh scan result"
+
+    dataset_store = DatasetStore(FIXTURE_DATASETS_J03_DIR)
+    enriched = enrich_with_tape_timeline(event, dataset_store, config)
+    assert enriched["tape_timeline"], "the join must have actually attached a real, non-empty timeline"
+
+    listed_after = compute_setups(store, config)  # a cache HIT -- the SAME shared object
+    assert listed_after["events"][0]["tape_timeline"] == [], (
+        "the enriched read must never leak into the shared cached list"
+    )
+    assert json.dumps(listed_before, sort_keys=True) == json.dumps(listed_after, sort_keys=True)
diff --git a/apps/backend/tests/test_setups_api.py b/apps/backend/tests/test_setups_api.py
index 2c3a7ac..c5d796f 100644
--- a/apps/backend/tests/test_setups_api.py
+++ b/apps/backend/tests/test_setups_api.py
@@ -85,6 +85,8 @@ def _seed_aapl(bar_dir: Path) -> None:
 _EVENT_FIELDS = {
     "id", "symbol", "session_date", "band", "touch_ts", "touch_open", "touch_high",
     "touch_low", "touch_close", "touch_volume", "reaction", "forward_returns", "tape_timeline",
+    # B1 (era-5B iter-5): additive recency-boundary disclosure fields.
+    "effective_reaction_horizon_bars", "reaction_boundary_truncated",
 }
 
 
```
