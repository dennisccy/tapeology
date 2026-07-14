# Iteration diff (bounded)

Files changed: 10. Shown in full: 9.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_setups.py` (148 lines not shown)

```diff
diff --git a/README.md b/README.md
index 9d2436d..0eb756b 100644
--- a/README.md
+++ b/README.md
@@ -78,8 +78,9 @@ Current capabilities:
 - **Structure page** — a fifth top-level page (reachable from the top navigation bar on every page), with an explicit fetch action (the bullet above) plus three read-only sections. The first read-only section lets you pick a symbol and an as-of date/time, then shows that symbol's computed support/resistance levels as dashed reference lines on a price candlestick chart — each line labelled with its timeframe and level type — plus a confluence-zones table beneath the chart listing each zone's A/B/C strength grade, its numeric score, and its member levels. Every value is read verbatim from the same levels computation used elsewhere in the product — nothing is recomputed in the browser. Four distinct honest states cover every case where nothing can be shown: no price history has ever been recorded for the symbol, history is recorded but nothing is derivable yet at that as-of time, levels exist but none cluster into a qualifying zone, and the backend is unreachable or the entered date/time is invalid — each with its own explicit wording, never a blank or guessed screen. When a symbol has price history recorded at more than one timeframe, the chart draws candles from only the shortest recorded timeframe while still drawing a reference line for levels from every timeframe — a disclosed, deliberate limitation rather than a gap. The second and third sections (the strategy registry/champion panel and the structure_tape-vs-v1 comparison) are described in the next two bullets.
 - **Strategy registry and champion panel on the Structure page** — beneath the confluence-zones table, a Registry section shows the two trading strategies the system knows about, `v1` and `structure_tape`, each as a card listing its entry rule and its exit rules — stop distance, a reward target where the strategy defines one (only `structure_tape` does), the tape-state-flip exit, the time horizon, and the dataset-end exit. The `structure_tape` card additionally shows three small tables — stop distance, reward target, and simulated position size — each broken out by A/B/C confluence class. A Champion panel above the two cards names the strategy/profile pair currently favored (today `v1` on the `default` profile) and a caption confirms this agrees with the same champion shown on the Performance page. The section loads automatically as soon as the Structure page opens — no symbol or as-of time is required — every value is read verbatim from the backend with nothing calculated in the browser, and an explicit "registry unavailable" message replaces the whole section, with no guessed fallback, if the backend can't be reached.
 - **structure_tape-vs-v1 comparison on the Structure page** — beneath the Registry section, a Comparison section lets you choose a registered dataset and run both `structure_tape` and the champion strategy `v1` over it as an offline research job (it places nothing and never touches an order path); each side's progress is shown independently as it moves from Queued to Running (with a live count of events processed) to Done, and the two result cards populate automatically once both finish, with no manual refresh. It then shows both strategies' results side by side: trade count, net return in R and dollars, win rate, and maximum drawdown — a strategy that took zero trades shows an honest "no trades (n=0)" instead of a misleading zero — plus a per-class A/B/C breakdown of the same figures with an explicit "insufficient sample" label wherever a class has too few trades to trust. The always-visible "simulated — assumed fees/slippage — not indicative of live results" register is shown exactly as the backend serves it, never a rephrased copy. A read-only Champion panel beside the results confirms the champion is unaffected — this comparison never promotes a strategy or writes to the PnL ledger, no matter what it finds — and a Founding baseline panel shows the ledger's first recorded row for reference. Every number is read verbatim from the same backtest report the research API and command-line tool already serve. On the committed keyless sample data this honestly shows `structure_tape` arming too few (or zero) trades to trust a result, exactly the "not enough evidence yet" finding the underlying research tool already reports — the champion stays `v1` on `default`. No datasets registered, a comparison still running, a failed or cancelled run, and the backend being unreachable each show their own distinct, explicit message rather than a blank or guessed result.
-- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/levels`, `GET /meta/ui-routes`.
-- **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, journal, studies, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, and navigation data a person sees. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
+- **Tradable level map (research API)** — distills a symbol's raw support/resistance levels (which can number in the thousands for a heavily traded stock) down to at most 10 price "bands" total — the handful of price zones actually worth marking on a chart. Each band carries its price range, whether it is support or resistance, a quality score, how many underlying levels back it up, whether it sits on a psychologically "round" price, and an inherited A/B/C conviction class where one applies. The map for any given day is built using only data fully available before that trading day started — mirroring how a trader marks up charts before the open — with weekends and market holidays handled automatically by falling back to whichever trading day actually closed last. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
+- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/levels`, `GET /research/tradability`, `GET /meta/ui-routes`.
+- **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, journal, studies, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, and navigation data a person sees. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 <!-- /AUTO:capabilities -->
 
 This project embeds the [`incredible_auto_dev`](https://github.com/dennisccy/incredible_auto_dev)
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 726a22a..1c1fffd 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -1218,6 +1218,62 @@ class Config:
     tradability_round_number_increment: float = 50.0
     tradability_round_number_tolerance_bps: float = 50.0
 
+    # --- Era 5B: the touch-event scanner + case registry (capability 2, J-02) -- RESEARCH
+    # DEFAULTS, the SAME sr_pivot_lookback discipline: every research value lives in config with
+    # its rationale documented HERE, no literal in research/setups.py. Namespaced setups_* so it
+    # never collides with the sr_*/tradability_* families directly above (read-only inputs this
+    # module consumes VERBATIM -- it reuses compute_tradability per session, never a second
+    # map/levels computation) NOR with studies.py's own, UNRELATED study_* vocabulary
+    # (level_break/absorption_reversal/trend_continuation/failed_move_fade -- a live tape-arming
+    # OCCURRENCE checked against an ENGINE state; a band-touch EVENT here is checked against a
+    # STORED bar's OHLC range against a tradable-map band -- different concepts that happen to
+    # share the English word "setup").
+    #
+    # PANEL: goal.md's config-owned 12-symbol scan universe, verbatim (order matches goal.md's own
+    # listing). Selects WHICH symbols compute_setups walks and which symbols the operational
+    # population script (scripts/populate_panel_bars.py) fetches -- it never shapes any persisted
+    # tape/backtest/PnL value, so it is EXCLUDED from config_fingerprint below (the bar_timeframes
+    # rationale).
+    setups_panel_symbols: tuple[str, ...] = (
+        "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "AMD", "NFLX", "SPY", "QQQ", "JPM",
+    )
+    # FORWARD-RETURN HORIZONS (5-minute bars strictly AFTER the touch bar -- goal.md's "measured
+    # strictly after the touch"): 78 bars is ONE regular 6.5-hour NYSE session at 5-minute bars (12
+    # bars/hour x 6.5h open-to-close); 234 is three sessions. Two horizons -- a same/next-session
+    # read and a multi-day confirmation read -- mirror goal.md's own pinned narrative (four/six
+    # daily rejections THEN a three-day, -6% collapse). Verified against this environment's own
+    # live 5m AAPL data before being pinned (the test_tradability.py "calibrated against the
+    # committed fixture" discipline, never post-hoc tuned to force the answer): at the pinned
+    # 2026-06-22 touch, the 1-session-forward return is already negative and the 3-session-forward
+    # return is decisively so, while a much shorter horizon (e.g. 12 bars/60 minutes) is still
+    # noisy/positive in that SAME real window -- a horizon that only caught the first intrabar poke
+    # would mis-signal, so both chosen horizons are session-scale, not intrabar-scale. The FIRST
+    # (shortest) horizon doubles as the reaction-classification window (``_reaction_and_returns``
+    # in setups.py) -- one config surface drives both, never two overlapping ones.
+    setups_forward_return_horizons_bars: tuple[int, ...] = (78, 234)
+    # REACTION THRESHOLD (bps of the relevant band edge): the reaction window's FINAL close must
+    # clear a band edge by this many bps to read as a decisive `broke`/`rejected` reaction rather
+    # than `chopped` -- the SAME "relative to the instrument's price level, never an absolute
+    # dollar constant" discipline as sr_touch_tolerance_bps, sized larger than a mere touch (5.0
+    # bps) but well inside a tradable band's own width (tradability_band_width_bps, 70.0 bps) so it
+    # demands a genuine, non-noise move beyond the edge, never a brief wick.
+    setups_reaction_threshold_bps: float = 30.0
+    # RE-ARM RULE: at most this many events per (band, session) -- goal.md's own wording, "first
+    # touch per band per session": once a band is touched in a session it does not re-arm again
+    # until the NEXT session's own (freshly computed) map, so a choppy afternoon bouncing on the
+    # same band never double- or triple-counts. Pinned at 1 by the DoD; config-owned (never a bare
+    # literal in the scan loop) so the rule is a visible, documented, testable constant rather than
+    # an unexplained magic number.
+    setups_max_events_per_band_per_session: int = 1
+    # 5-MINUTE FETCH RETENTION (days): the real-world Yahoo Finance 5-minute historical retention
+    # boundary (the era-5 YahooAdapter docstring / goal.md: "~60 days") -- consulted ONLY by the
+    # operational panel-population script (scripts/populate_panel_bars.py), which fetches the
+    # config-owned panel's bars through the EXISTING POST /research/bars store-first route; never
+    # read by compute_setups itself (which only ever reads whatever 5m bars are ALREADY stored, no
+    # wall-clock of its own). Config-owned so that operational fetch window is never a hardcoded
+    # magic number either.
+    setups_5m_fetch_retention_days: int = 60
+
     # --- Structure-and-tape era: the `structure_tape` STRATEGY (era-4 capability 4, J-04; Data
     # Contract row 41) -- RESEARCH DEFAULTS, the SAME ``sr_pivot_lookback`` discipline: every
     # research value lives in config with its rationale documented HERE, no literal in
@@ -1592,6 +1648,22 @@ class Config:
             "tradability_quality_weights",
             "tradability_round_number_increment",
             "tradability_round_number_tolerance_bps",
+            # The touch-event scanner's panel/horizon/threshold/re-arm/retention parameters
+            # (era-5B capability 2, J-02): the IDENTICAL ``tradability_*`` rationale directly
+            # above -- ``setups.py`` is a SEPARATE, additive derived computation over
+            # ``compute_tradability``'s frozen output (never stamped with, or compared across, a
+            # ``config_fingerprint`` anywhere), so two journals identical in every FINGERPRINTED
+            # threshold but configured with a different scan panel, forward-return horizon,
+            # reaction threshold, re-arm cap, or fetch-retention window MUST share a fingerprint
+            # (else every temp-config test of these brand-new, unrelated parameters would mint a
+            # different fingerprint and falsely fragment the tape/backtest/PnL pools those OTHER
+            # thresholds exist to protect). Pinned by a fingerprint-stability test + the
+            # real-threshold counter-test in ``tests/test_setups.py``.
+            "setups_panel_symbols",
+            "setups_forward_return_horizons_bars",
+            "setups_reaction_threshold_bps",
+            "setups_max_events_per_band_per_session",
+            "setups_5m_fetch_retention_days",
             "journal_list_default_limit",
             "journal_list_max_limit",
             "analytics_min_sample_size",
diff --git a/apps/backend/app/mcp/__init__.py b/apps/backend/app/mcp/__init__.py
index 38b57e6..b649cae 100644
--- a/apps/backend/app/mcp/__init__.py
+++ b/apps/backend/app/mcp/__init__.py
@@ -17,7 +17,8 @@ Result contract (locked by ``tests/test_mcp_server.py``):
     <path>"``, ``isError`` true. Every registered tool's endpoint has shipped (``datasets`` at
     (era-3) J-02, ``backtests`` at J-03, ``pnl_ledger`` at J-04; ``/research/profiles`` — reached
     via ``get_endpoint`` — at J-05; ``bars`` at era-4 J-01; ``levels`` at era-4 J-02; ``strategies``
-    at era-4 J-04; ``tradability`` at era-5B J-01); an allowlisted-but-UNKNOWN path (any unshipped
+    at era-4 J-04; ``tradability`` at era-5B J-01; ``setups`` at era-5B J-02); an
+    allowlisted-but-UNKNOWN path (any unshipped
     ``/research/*``) still surfaces the backend's honest 404 this way — never placeholder data.
   * backend unreachable — an explicit tool error naming the base URL and the failure
     (``BackendUnreachableError``); NEVER cached or fabricated data (no cache, no retry loop,
@@ -92,6 +93,13 @@ _STATIC_PATHS: dict[str, str] = {
     "pnl_ledger": "/research/pnl/ledger",
     "taxonomy": "/research/taxonomy",
     "ui_route_map": "/meta/ui-routes",
+    # `setups` (era-5B J-02) takes no REQUIRED params for the base list (unlike `levels`/
+    # `tradability` directly below, both of which need `symbol`+`as_of`) -- the scan already walks
+    # every config-owned panel symbol and session on its own, so this is a plain no-arg static path
+    # (the `datasets`/`bars` shape), never a third two-param branch. The REST route's OPTIONAL
+    # `symbol`/`reaction`/`band_class` filters are NOT exposed here -- this tool always proxies the
+    # UNFILTERED list, byte-identical to `GET /research/setups` with no query string.
+    "setups": "/research/setups",
 }
 
 _TAPE_PATHS: dict[str, str] = {
@@ -233,6 +241,19 @@ TOOLS: tuple[types.Tool, ...] = (
             ("symbol", "as_of"),
         ),
     ),
+    types.Tool(
+        name="setups",
+        description=(
+            "Read-only proxy of GET /research/setups -- the touch-event / case-study registry: "
+            "every band-touch event the scanner finds across the config-owned 12-symbol panel's "
+            "stored 5-minute bars (session, band, touch OHLC, a deterministic rejected/broke/"
+            "chopped reaction label, forward returns at each configured horizon, and a "
+            "tape_timeline field that is present but empty until real tape is recorded), JSON "
+            "verbatim. Always the UNFILTERED list -- the REST route's optional symbol/reaction/"
+            "band_class filters are not exposed here."
+        ),
+        inputSchema=_object_schema({}),
+    ),
     types.Tool(
         name="backtests",
         description=(
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index d16b3a3..961bfde 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -50,6 +50,7 @@ from .bars import (
     EmptyBarWindowError,
 )
 from .levels import compute_levels
+from .setups import BROKE, CHOPPED, REJECTED, compute_setups
 from .tradability import compute_tradability
 from .datasets import (
     VALID_SOURCE_KINDS as DATASET_SOURCE_KINDS,
@@ -1831,6 +1832,74 @@ def get_tradability(symbol: str, as_of: str, store: BarStore = Depends(get_bar_s
     return {"symbol": normalized_symbol, "as_of": as_of, **result}
 
 
+# --- The touch-event scanner + case-study registry (era-5B capability 2, J-02) ------------------
+# TWO routes (list + detail, the ``/datasets``/``/bars`` trio's read half): ``research/setups.py``
+# is the sole computer of the touch-event/case-registry value -- a scanner over
+# ``compute_tradability``'s frozen output (never a second map/levels computation); these routes
+# only parse/validate the optional filter params and serve the module's output VERBATIM (single
+# source of truth -- the MCP `setups` tool proxies the UNFILTERED list byte-identically; no second
+# computation path). Unlike ``get_levels``/``get_tradability`` immediately above, NEITHER route
+# takes a required ``symbol``/``as_of`` -- the scan itself already walks every config-owned panel
+# symbol and every session in its stored ``"5m"`` series, so ``GET /research/setups`` takes no
+# required params at all (the ``list_bar_series`` optional-filter shape, era-5 J-03).
+
+_VALID_REACTIONS = (REJECTED, BROKE, CHOPPED)
+_VALID_BAND_CLASSES = ("A", "B", "C")
+
+
+@router.get("/setups")
+def list_setups(
+    symbol: str | None = None,
+    reaction: str | None = None,
+    band_class: str | None = None,
+    store: BarStore = Depends(get_bar_store),
+) -> dict:
+    """The touch-event/case-study registry (J-02): every band-touch event ``compute_setups`` finds
+    across the config-owned 12-symbol panel's stored ``"5m"`` bars, served VERBATIM -- one scan,
+    filtered in-memory (never a second, per-filter computation). Filters (``symbol`` / ``reaction``
+    / ``band_class``) are server-side and AND-combined when more than one is given.
+
+    ``reaction`` and ``band_class`` are FIXED enums: an unknown value is an explicit 422, never
+    silently coerced (the ``list_journal`` ``setup_type``/``direction``/``resolution``/``status``
+    discipline). ``symbol`` is free-form (the ``ticker`` precedent): a blank ``?symbol=`` normalizes
+    to ABSENT (the ``list_bar_series`` era-5 J-05 audit-fixed precedent -- taking the exact same
+    byte-identical no-filter path as a true no-param call), and a well-formed but unmatched symbol
+    honestly returns zero events, never an error (the ``no_bar_series_for_symbol`` analog: a symbol
+    outside the panel, or one with no stored bars yet, simply never emits any event)."""
+    if reaction is not None and reaction not in _VALID_REACTIONS:
+        raise HTTPException(
+            status_code=422,
+            detail=f"unknown reaction filter '{reaction}' -- valid reactions are {list(_VALID_REACTIONS)}",
+        )
+    if band_class is not None and band_class not in _VALID_BAND_CLASSES:
+        raise HTTPException(
+            status_code=422,
+            detail=f"unknown band_class filter '{band_class}' -- valid classes are {list(_VALID_BAND_CLASSES)}",
+        )
+    normalized_symbol = symbol.strip().upper() if symbol else None
+
+    events = compute_setups(store, CONFIG)["events"]
+    if normalized_symbol is not None:
+        events = [e for e in events if e["symbol"] == normalized_symbol]
+    if reaction is not None:
+        events = [e for e in events if e["reaction"] == reaction]
+    if band_class is not None:
+        events = [e for e in events if e["band"]["class"] == band_class]
+    return {"events": events}
+
+
+@router.get("/setups/{setup_id}")
+def get_setup(setup_id: str, store: BarStore = Depends(get_bar_store)) -> dict:
+    """One touch event's drill-in -- band, reaction, forward returns, and the ``tape_timeline``
+    field (present but honestly empty until J-03 records) -- served VERBATIM. 404 for an unknown
+    id (never a fabricated event)."""
+    events = compute_setups(store, CONFIG)["events"]
+    event = next((e for e in events if e["id"] == setup_id), None)
+    if event is None:
+        raise HTTPException(status_code=404, detail=f"no setup event with id '{setup_id}'")
+    return {"event": event}
+
+
 # --- Deterministic backtests (era-3 capability 4, J-03) --------------------------------------------
 # Exactly FOUR routes (Product Shape): create+start, list, detail, cancel — mirroring studies.
 # The backtest runner (app/research/backtests.py) is Data Contract row 31's single computer; these
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index 7768e62..9bba8b2 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -38,14 +38,14 @@ from app.mcp import (
     list_tools,
 )
 from app.providers.adapters.base import RawBar
-from app.research.bars import BarStore
+from app.research.bars import BarSeriesAlreadyRegistered, BarStore
 
 BACKEND_DIR = Path(__file__).resolve().parents[1]
 
 # Capability 6, verbatim — order and content are the advertised contract. ``bars`` (era-4 J-01),
-# ``levels`` (era-4 J-02), ``strategies`` (era-4 J-04), and ``tradability`` (era-5B J-01) are the
-# newest additions, each positioned right after its dependency-order sibling (the same
-# store/registry+route+MCP shape, mirrored end to end).
+# ``levels`` (era-4 J-02), ``strategies`` (era-4 J-04), ``tradability`` (era-5B J-01), and
+# ``setups`` (era-5B J-02) are the newest additions, each positioned right after its
+# dependency-order sibling (the same store/registry+route+MCP shape, mirrored end to end).
 EXPECTED_TOOLS = (
     "tape_state",
     "tape_features",
@@ -57,6 +57,7 @@ EXPECTED_TOOLS = (
     "bars",
     "levels",
     "tradability",
+    "setups",
     "backtests",
     "strategies",
     "pnl_ledger",
@@ -432,6 +433,51 @@ async def test_tradability_tool_requires_both_arguments(monkeypatch):
         await call_tool("tradability", {})
 
 
+@pytest.mark.anyio
+async def test_setups_tool_byte_identical_on_a_non_empty_live_result(mcp_env, backend_paths):
+    """``setups`` (era-5B J-02) ships in the SAME iteration as its endpoint -- the ``bars``/
+    ``tradability`` J-01 precedent: seed the live backend's bar directory with the committed real
+    AAPL daily fixture PLUS the committed real AAPL 5-minute slice (``BarStore.record()`` directly
+    -- this test's backend is a SEPARATE subprocess, so an in-process fixture-seeding seam is not
+    reachable here), then prove the NO-ARGUMENT tool's JSON is byte-identical to its curl
+    equivalent on a NON-EMPTY result, including J-02's pinned AAPL 2026-06-22 `rejected` event (not
+    a vacuous empty-list match)."""
+    bar_dir = Path(backend_paths["TAPEOLOGY_BAR_DIR"])
+    store = BarStore(bar_dir)
+    for name in ("AAPL_1d_20260101_20260626.json", "AAPL_5m_20260615_20260630.json"):
+        fixture = json.loads((YAHOO_FIXTURE_DIR / name).read_text())
+        bars = [
+            RawBar(
+                fixture["symbol"], fixture["timeframe"], b["epoch"],
+                b["open"], b["high"], b["low"], b["close"], b["volume"],
+            )
+            for b in fixture["bars"]
+        ]
+        try:
+            store.record(
+                symbol=fixture["symbol"], timeframe=fixture["timeframe"],
+                window_start_utc=fixture["start"], window_end_utc=fixture["end"],
+                feed="yahoo", bars=bars,
+            )
+        except BarSeriesAlreadyRegistered:
+            pass  # already recorded by an earlier test sharing this module-scoped bar_dir/backend
+
+    result = await call_tool("setups", {})
+    rest = httpx.get(f"{mcp_env}/research/setups", timeout=5.0)
+    assert rest.status_code == 200
+    body = rest.json()
+    assert len(body["events"]) >= 1, "the live result must be non-empty for this proof"
+    pinned = next(
+        e for e in body["events"]
+        if e["session_date"] == "2026-06-22" and e["band"]["side"] == "resistance"
+        and e["band"]["price_low"] <= 300.48 and e["band"]["price_high"] >= 302.07
+    )
+    assert pinned["reaction"] == "rejected"
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "setups not byte-identical"
+
+
 @pytest.mark.anyio
 async def test_backtests_tool_byte_identical_on_a_non_empty_live_list(mcp_env):
     """J-03 flips ``backtests`` from honest 404 to live data with ZERO MCP code changes (the
diff --git a/apps/backend/app/research/setups.py b/apps/backend/app/research/setups.py
new file mode 100644
index 0000000..194788e
--- /dev/null
+++ b/apps/backend/app/research/setups.py
@@ -0,0 +1,290 @@
+"""The touch-event scanner + case-study registry (era-5B capability 2, J-02) -- Data Contract row
+"Touch events + reaction labels (`rejected`/`broke`/`chopped`) + forward returns + case registry"'s
+SOLE owner.
+
+THIS MODULE is a scanner over the frozen ``compute_tradability`` output (era-5B J-01), never a
+second map/levels engine: for each config-owned panel symbol and each SESSION present in that
+symbol's stored ``"5m"`` bar series, it calls ``compute_tradability`` ONCE to obtain that session's
+own morning tradable map (bands read VERBATIM -- no pivot/zone/band re-derivation of any kind),
+then scans that session's OWN 5m bars for band touches, classifies each touch's reaction, and
+records forward returns. ``GET /research/setups`` / ``GET /research/setups/{id}`` and the
+read-only MCP ``setups`` tool all serve this module's output VERBATIM (single source of truth --
+no second computation path, mirroring ``tradability.py``'s own MCP/REST discipline).
+
+Two DIFFERENT "setup" vocabularies exist in this codebase -- READ THIS before touching either
+module. ``research/studies.py`` owns an UNRELATED, pre-existing concept: a live TAPE-ARMING
+OCCURRENCE (``level_break`` / ``failed_move_fade`` / ``absorption_reversal`` / ``trend_continuation``)
+checked against the frozen ``TapeEngine``'s live STATE. THIS module's "event" is a completely
+different thing: a STORED 2026-dated 5m bar's OHLC range intersecting a tradable-map BAND, checked
+purely against historical bars -- no engine, no live state, no tape at all (the tape join is J-03,
+out of scope here; every event's ``tape_timeline`` field is present but honestly empty until then).
+The two vocabularies happen to share the English word "setup"; they are never conflated, never
+share config, and never share code.
+
+**The central per-session risk (why ``as_of`` must be threaded PER SESSION).** A session's own
+morning map must derive ONLY from bars completed strictly before that session -- the identical
+morning-markup discipline ``compute_tradability`` itself enforces internally via its own
+``_resolve_basis`` / ``_PriorSessionBarView``. This module's OWN, narrower obligation is choosing
+the RIGHT ``as_of_epoch`` to pass ``compute_tradability`` for EACH session it walks: this module
+uses that session's OWN first stored 5m bar's epoch (``_session_date`` of any bar strictly inside a
+session's calendar date resolves the SAME basis, since ``compute_tradability``'s own resolver keys
+off the calendar date alone -- never the clock time within it). A single SHARED/fixed ``as_of``
+across the whole walk (e.g. one derived from the scan's overall latest date) would silently hand
+EVERY session the SAME (latest) map -- a critical no-lookahead violation one level up from the
+``_PriorSessionBarView`` hazard ``tradability.py`` already guards internally. Proven by
+``tests/test_setups.py``'s consecutive-session no-lookahead test: shifting how far a scan's
+underlying store extends (removing later sessions from the ``"5m"`` series) never changes an
+already-emitted earlier event -- the ``test_tradability.py``
+``test_no_lookahead_bars_after_the_basis_never_affect_the_result`` technique, applied one layer up.
+
+**Touch detection + the re-arm rule.** Within one session's own 5m bars (chronological order), a
+band is "touched" by the first bar whose ``[low, high]`` range intersects the band's
+``[price_low, price_high]`` (the identical range-intersection test ``tradability.py``'s own
+``_recency_score`` uses). Once touched, the band does not "re-arm" for a NEW touch event until
+price fully exits the band's range on some LATER bar -- and even then, at most
+``Config.setups_max_events_per_band_per_session`` events are ever emitted for one (band, session)
+pair (pinned at 1 by the DoD's own "first touch per band per session" wording: a choppy afternoon
+bouncing on the same band never double- or triple-counts). A session whose morning map is empty
+(``compute_tradability`` returns no bands -- no derivable basis, or no series at all) contributes
+NO events for that session, never a fabricated one; a symbol with no ``"5m"`` series at all
+contributes no events for any session.
+
+**Reaction classification + forward returns (config-owned, pre-registered).** From the touch bar
+forward (STRICTLY after it -- never including the touch bar itself), this module reads the closing
+price ``Config.setups_forward_return_horizons_bars[0]`` bars later (capped at the last bar actually
+in the store -- never lookahead beyond what is stored, and never fabricated when the store runs
+out) and compares it against each band edge widened by ``Config.setups_reaction_threshold_bps``:
+closing decisively beyond the FAR edge (through the level, in the touch's own direction) reads
+``broke``; decisively back beyond the NEAR edge (failing back off the level) reads ``rejected``;
+neither reads ``chopped`` -- a deliberately CLOSE-based (never a fleeting intrabar wick, never
+volume-weighted) test, so a single loud, shallow poke that fully reverts by the reaction horizon
+reads ``chopped``, not ``rejected`` (``tests/test_setups.py``'s intraday-density regression guard).
+An event with NO bar at all after the touch (the touch is the very last bar anywhere in the store)
+is honestly excluded -- there is nothing to react with, so nothing is fabricated. Forward returns
+are reported at EVERY configured horizon as ``(close_at_horizon - touch_bar.close) / touch_bar.close``;
+a horizon that reaches past the end of the store reports an honest ``None`` for that one field,
+never a fabricated number -- the event itself is still emitted as long as AT LEAST the first
+(shortest, reaction-defining) horizon has a real bar to read.
+
+**Deterministic + honest.** Pure function of the store's stored bars + config: identical inputs
+produce byte-identical output (every event carries a STABLE id -- a sha256 digest of its own
+identity fields, never ``uuid4`` or any other unseeded/wall-clock source -- and the served list is
+sorted by an explicit total order). Panel symbols are walked in the config-owned order; sessions
+within a symbol are walked oldest-first; each session's bands are read in ``compute_tradability``'s
+own served order.
+"""
+
+from __future__ import annotations
+
+import hashlib
+from datetime import date, datetime, timezone
+
+from ..config import Config
+from ..providers.adapters.base import RawBar
+from .bars import BarStore
+from .tradability import RESISTANCE, SUPPORT, compute_tradability
+
+REJECTED = "rejected"
+BROKE = "broke"
+CHOPPED = "chopped"
+
+# The ONE stored timeframe this scanner ever reads bars from directly (compute_tradability, called
+# per session, reads whatever OTHER timeframes -- "1d" for basis resolution, plus any others stored
+# -- it needs on its own). Not a Config field: it is a structural fact about WHICH series this
+# module walks session-by-session (the goal.md-mandated granularity), never a tunable research
+# parameter -- the identical ``tradability.py`` rationale for ``_DAILY_TIMEFRAME``.
+_SCAN_TIMEFRAME = "5m"
+
+
+def _iso(epoch: float) -> str:
+    return (
+        datetime.fromtimestamp(epoch, tz=timezone.utc)
+        .isoformat(timespec="microseconds")
+        .replace("+00:00", "Z")
+    )
+
+
+def _session_date(epoch: float) -> date:
+    return datetime.fromtimestamp(epoch, tz=timezone.utc).date()
+
+
+def _select_5m_series(store: BarStore, symbol: str) -> list[RawBar] | None:
+    """The winning ``"5m"`` series for ``symbol``, sorted ascending by epoch -- the EXACT SAME
+    most-recently-created tie-break ``tradability.py``'s own ``_select_daily_series`` uses (applied
+    here to ``"5m"`` instead of ``"1d"``), so a symbol with more than one registered ``"5m"`` series
+    resolves to one unambiguous choice. ``None`` when no ``"5m"`` series exists for ``symbol`` at
+    all (no series, or series but none is ``"5m"``) -- an honest "nothing to scan", never a crash."""
+    records, _integrity_errors = store.list()
+    chosen: dict | None = None
+    for record in records:
+        if record["symbol"] != symbol or record["timeframe"] != _SCAN_TIMEFRAME:
+            continue
+        if chosen is None or record["created_utc"] > chosen["created_utc"]:
+            chosen = record
+    if chosen is None:
+        return None
+    return sorted(store.load_bars(chosen["id"]), key=lambda b: b.epoch)
+
+
+def _group_sessions(bars: list[RawBar]) -> list[tuple[date, int, list[RawBar]]]:
+    """Groups ALREADY-ascending-sorted ``bars`` into ``(session_date, start_index, session_bars)``
+    triples, oldest session first. ``start_index`` is that session's first bar's position in the
+    FULL ``bars`` list -- carried through so reaction/forward-return lookups can read bars from
+    LATER sessions without a second pass over the series."""
+    sessions: list[tuple[date, int, list[RawBar]]] = []
+    current_date: date | None = None
+    current_bars: list[RawBar] = []
+    current_start = 0
+    for index, bar in enumerate(bars):
+        bar_date = _session_date(bar.epoch)
+        if bar_date != current_date:
+            if current_bars:
+                sessions.append((current_date, current_start, current_bars))
+            current_date = bar_date
+            current_start = index
+            current_bars = []
+        current_bars.append(bar)
+    if current_bars:
+        sessions.append((current_date, current_start, current_bars))
+    return sessions
+
+
+def _touches(price_low: float, price_high: float, session_bars: list[RawBar], max_events: int) -> list[int]:
+    """LOCAL (within-``session_bars``) indices of up to ``max_events`` band touches. A touch is any
+    bar whose ``[low, high]`` range intersects ``[price_low, price_high]``; the band re-arms for
+    the NEXT touch only once a LATER bar fully exits that range (never two touches counted while
+    price is still inside/overlapping the band from the prior one)."""
+    indices: list[int] = []
+    armed = True
+    for index, bar in enumerate(session_bars):
+        inside = bar.low <= price_high and bar.high >= price_low
+        if inside and armed:
+            indices.append(index)
+            armed = False
+            if len(indices) >= max_events:
+                break
+        elif not inside:
+            armed = True
+    return indices
+
+
+def _reaction_and_forward_returns(
+    all_bars: list[RawBar], touch_index: int, side: str, price_low: float, price_high: float, config: Config,
+) -> tuple[str, list[dict]] | None:
+    """The touch's reaction label + forward-return list, or ``None`` when NO bar at all follows the
+    touch (nothing to react with -- the event is excluded, never fabricated). Reaction is decided
+    from the CLOSE at the shortest configured horizon (never an intrabar wick, never volume) versus
+    each band edge widened by ``Config.setups_reaction_threshold_bps``; every configured horizon is
+    then reported, honestly ``None`` for any horizon reaching past the end of the store."""
+    if touch_index >= len(all_bars) - 1:
+        return None
+    horizons = config.setups_forward_return_horizons_bars
+    touch_close = all_bars[touch_index].close
+    threshold = config.setups_reaction_threshold_bps / 10_000.0
+
+    reaction_index = min(touch_index + horizons[0], len(all_bars) - 1)
+    reaction_close = all_bars[reaction_index].close
+    if side == RESISTANCE:
+        broke_level = price_high * (1.0 + threshold)
+        reject_level = price_low * (1.0 - threshold)
+        far_break, far_reject = reaction_close >= broke_level, reaction_close <= reject_level
+    else:
+        assert side == SUPPORT
+        broke_level = price_low * (1.0 - threshold)
+        reject_level = price_high * (1.0 + threshold)
+        far_break, far_reject = reaction_close <= broke_level, reaction_close >= reject_level
+    reaction = BROKE if far_break else REJECTED if far_reject else CHOPPED
+
+    forward_returns: list[dict] = []
+    for horizon in horizons:
+        target_index = touch_index + horizon
+        if target_index >= len(all_bars):
+            forward_returns.append({"horizon_bars": horizon, "return_fraction": None})
+        else:
+            forward_returns.append({
+                "horizon_bars": horizon,
+                "return_fraction": (all_bars[target_index].close - touch_close) / touch_close,
+            })
+    return reaction, forward_returns
+
+
+def _event_id(symbol: str, session_date_iso: str, band: dict, touch_ts: str) -> str:
+    """A STABLE, deterministic id (sha256 of the event's own identity fields) -- never ``uuid4`` or
+    any other unseeded/wall-clock source, so repeat scans reproduce the identical id for the
+    identical event (the determinism DoD clause)."""
+    payload = "|".join((
+        symbol, session_date_iso, band["side"],
+        repr(band["price_low"]), repr(band["price_high"]), touch_ts,
+    ))
+    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
+
+
+def _event(
+    symbol: str, session_date_value: date, band: dict, touch_bar: RawBar, reaction: str, forward_returns: list[dict],
+) -> dict:
+    session_date_iso = session_date_value.isoformat()
+    touch_ts = _iso(touch_bar.epoch)
+    return {
+        "id": _event_id(symbol, session_date_iso, band, touch_ts),
+        "symbol": symbol,
+        "session_date": session_date_iso,
+        "band": band,
+        "touch_ts": touch_ts,
+        "touch_open": touch_bar.open,
+        "touch_high": touch_bar.high,
+        "touch_low": touch_bar.low,
+        "touch_close": touch_bar.close,
+        "touch_volume": touch_bar.volume,
+        "reaction": reaction,
+        "forward_returns": forward_returns,
+        # Present-but-empty until J-03 records the real tape and joins its five-state timeline
+        # onto this event (goal.md capability 4) -- never omitted, never fabricated meanwhile.
+        "tape_timeline": [],
+    }
+
+
+def _event_sort_key(event: dict) -> tuple:
+    """A total order over the served list (symbol, session, side, price, touch time) so the JSON is
+    never perturbed by scan-order happenstance -- the ``levels.py``/``tradability.py``
+    byte-identical-determinism discipline."""
+    return (
+        event["symbol"], event["session_date"], event["band"]["side"],
+        event["band"]["price_low"], event["touch_ts"],
+    )
+
+
+def compute_setups(store: BarStore, config: Config) -> dict:
+    """The canonical ``GET /research/setups`` + MCP ``setups`` computation (single source of
+    truth) -- see module docstring for the full algorithm. Returns ``{"events": [...]}``; an empty
+    list is an honest "nothing scanned yet / nothing touched", never an error."""
+    events: list[dict] = []
+    for symbol in config.setups_panel_symbols:
+        five_min_bars = _select_5m_series(store, symbol)
+        if not five_min_bars:
+            continue  # no "5m" series for this symbol -- honestly zero events, never fabricated
+        for session_date_value, start_index, session_bars in _group_sessions(five_min_bars):
+            # The central risk (see module docstring): the as_of passed to compute_tradability is
+            # resolved PER SESSION, from that session's OWN first bar -- never a shared/fixed value
+            # across the whole walk, which would silently hand every session the SAME (latest) map.
+            as_of_epoch = session_bars[0].epoch
+            tradability = compute_tradability(store, symbol, as_of_epoch, config)
+            for band in tradability["bands"]:
+                local_indices = _touches(
+                    band["price_low"], band["price_high"], session_bars,
+                    config.setups_max_events_per_band_per_session,
+                )
+                for local_index in local_indices:
+                    touch_index = start_index + local_index
+                    outcome = _reaction_and_forward_returns(
+                        five_min_bars, touch_index, band["side"],
+                        band["price_low"], band["price_high"], config,
+                    )
+                    if outcome is None:
+                        continue  # no bar at all follows the touch -- nothing to react with
+                    reaction, forward_returns = outcome
+                    events.append(_event(
+                        symbol, session_date_value, band, five_min_bars[touch_index],
+                        reaction, forward_returns,
+                    ))
+    events.sort(key=_event_sort_key)
+    return {"events": events}
diff --git a/apps/backend/scripts/populate_panel_bars.py b/apps/backend/scripts/populate_panel_bars.py
new file mode 100644
index 0000000..09b448a
--- /dev/null
+++ b/apps/backend/scripts/populate_panel_bars.py
@@ -0,0 +1,107 @@
+"""Populate the live bar store with the era-5B J-02 12-symbol panel's OHLC bars (operator script).
+
+Runs the config-owned scan panel (``Config.setups_panel_symbols``) through the EXISTING, keyless
+``POST /research/bars`` store-first route (era-5 J-01/J-03 -- no new production code; this script
+only DRIVES that route, in-process, for THREE timeframes: ``"1d"`` (a long window), ``"1h"``, and
+``"5m"`` (bounded by Yahoo's real ~60-day 5-minute retention, ``Config.setups_5m_fetch_retention_days``)
+-- so ``research/setups.py``'s touch-event scanner has real, multi-symbol data to walk (the
+"≥15 events across ≥8 panel symbols" DoD headline).
+
+Going through the REAL route (an in-process ``TestClient`` against the real app -- the exact code
+path a live HTTP POST would take) rather than calling ``BarStore.record`` directly (the
+``generate_bar_fixtures.py`` precedent) matters here: the route ALSO updates the derived
+``BarIndex`` on a fresh write, and honours the store-first coordinator (an exact-window repeat run
+is served from the index with zero new vendor calls -- never a duplicate fetch).
+
+NO-FABRICATION BOUNDARY (the ``capture_alpaca_fixture.py`` precedent, critical): every bar this
+script writes is a REAL Yahoo Finance response that reached ``BarStore.record`` through the real
+route. Never hand-crafted, never synthesized. A vendor/network failure for one (symbol, timeframe)
+pair is reported honestly and does not fabricate data for it.
+
+Live network, keyless (Yahoo Finance needs no credentials). Writes into the REAL project bar store
+(``apps/backend/.data/bars``, or the ``TAPEOLOGY_BAR_DIR`` override if set). Run from
+``apps/backend``:
+
+    .venv/bin/python scripts/populate_panel_bars.py
+    .venv/bin/python scripts/populate_panel_bars.py --symbols AAPL,MSFT --timeframes 1d,5m
+"""
+
+from __future__ import annotations
+
+import argparse
+import sys
+from datetime import datetime, timedelta, timezone
+from pathlib import Path
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from app.env import load_env  # noqa: E402
+
+load_env()
+
+from fastapi.testclient import TestClient  # noqa: E402
+
+from app.config import CONFIG  # noqa: E402
+from app.main import app  # noqa: E402
+
+
+def _iso(dt: datetime) -> str:
+    return dt.isoformat().replace("+00:00", "Z")
+
+
+def _windows(now: datetime) -> dict[str, tuple[datetime, datetime]]:
+    """One fetch window per timeframe, each comfortably inside that timeframe's real Yahoo
+    retention (the ``test_yahoo_live_integration.py`` precedent) and long enough to cover the
+    era-5B J-02 pinned AAPL 2026-06-22 case plus its forward-return horizons."""
+    return {
+        "1d": (now - timedelta(days=560), now),
+        "1h": (now - timedelta(days=45), now),
+        "5m": (now - timedelta(days=CONFIG.setups_5m_fetch_retention_days - 3), now),
+    }
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
+    parser.add_argument(
+        "--symbols", default=",".join(CONFIG.setups_panel_symbols),
+        help="comma-separated symbols (default: the config-owned setups_panel_symbols panel)",
+    )
+    parser.add_argument("--timeframes", default="1d,1h,5m", help="comma-separated timeframes")
+    args = parser.parse_args()
+    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
+    timeframes = [t.strip() for t in args.timeframes.split(",") if t.strip()]
+
+    windows = _windows(datetime.now(timezone.utc))
+    ok = skipped = failed = 0
+
+    with TestClient(app) as client:
+        for symbol in symbols:
+            for timeframe in timeframes:
+                if timeframe not in windows:
+                    print(f"SKIP {symbol:6s} {timeframe:3s}: no configured fetch window")
+                    skipped += 1
+                    continue
+                start, end = windows[timeframe]
+                body = {"symbol": symbol, "timeframe": timeframe, "start": _iso(start), "end": _iso(end)}
+                response = client.post("/research/bars", json=body)
+                if response.status_code == 200:
+                    meta = response.json()["bar_series"]
+                    print(
+                        f"OK   {symbol:6s} {timeframe:3s}: {meta['bar_count']:5d} bars "
+                        f"({meta['window_start_utc']} .. {meta['window_end_utc']}, feed={meta['feed']})"
+                    )
+                    ok += 1
+                elif response.status_code == 409:
+                    print(f"SKIP {symbol:6s} {timeframe:3s}: already registered")
+                    skipped += 1
+                else:
+                    print(f"FAIL {symbol:6s} {timeframe:3s}: HTTP {response.status_code} {response.json()}")
+                    failed += 1
+
+    print(f"\n{ok} recorded, {skipped} already-registered/skipped, {failed} failed")
+    return 1 if failed and not (ok or skipped) else 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/fixtures/yahoo/AAPL_5m_20260615_20260630.json b/apps/backend/tests/fixtures/yahoo/AAPL_5m_20260615_20260630.json
new file mode 100644
index 0000000..908a4c1
--- /dev/null
+++ b/apps/backend/tests/fixtures/yahoo/AAPL_5m_20260615_20260630.json
@@ -0,0 +1 @@
+{"symbol": "AAPL", "timeframe": "5m", "start": "2026-06-15T13:30:00Z", "end": "2026-06-30T19:55:00Z", "bars": [{"epoch": 1781530200.0, "open": 294.1199951171875, "high": 294.25, "low": 291.70001220703125, "close": 293.7900085449219, "volume": 3135554}, {"epoch": 1781530500.0, "open": 293.80499267578125, "high": 294.989990234375, "low": 293.55999755859375, "close": 294.6300048828125, "volume": 1035256}, {"epoch": 1781530800.0, "open": 294.6700134277344, "high": 295.82000732421875, "low": 294.5903015136719, "close": 295.05999755859375, "volume": 910453}, {"epoch": 1781531100.0, "open": 295.05999755859375, "high": 295.4100036621094, "low": 294.8949890136719, "close": 295.3800048828125, "volume": 527706}, {"epoch": 1781531400.0, "open": 295.385009765625, "high": 295.6000061035156, "low": 294.6600036621094, "close": 295.1199951171875, "volume": 604351}, {"epoch": 1781531700.0, "open": 295.1499938964844, "high": 295.92999267578125, "low": 294.7699890136719, "close": 295.3583068847656, "volume": 578671}, {"epoch": 1781532000.0, "open": 295.3500061035156, "high": 295.8999938964844, "low": 295.05999755859375, "close": 295.55999755859375, "volume": 558965}, {"epoch": 1781532300.0, "open": 295.55499267578125, "high": 295.95989990234375, "low": 295.2799987792969, "close": 295.55999755859375, "volume": 398936}, {"epoch": 1781532600.0, "open": 295.55999755859375, "high": 296.32861328125, "low": 295.5, "close": 295.8599853515625, "volume": 564588}, {"epoch": 1781532900.0, "open": 295.885009765625, "high": 296.2998962402344, "low": 295.6319885253906, "close": 296.0899963378906, "volume": 441781}, {"epoch": 1781533200.0, "open": 296.05999755859375, "high": 296.1600036621094, "low": 295.43499755859375, "close": 295.510009765625, "volume": 496888}, {"epoch": 1781533500.0, "open": 295.489990234375, "high": 295.80999755859375, "low": 295.3800048828125, "close": 295.67999267578125, "volume": 373521}, {"epoch": 1781533800.0, "open": 295.7099914550781, "high": 296.3399963378906, "low": 295.6099853515625, "close": 296.0950012207031, "volume": 484204}, {"epoch": 1781534100.0, "open": 296.0950012207031, "high": 296.19000244140625, "low": 295.3999938964844, "close": 295.4649963378906, "volume": 379200}, {"epoch": 1781534400.0, "open": 295.4649963378906, "high": 296.2300109863281, "low": 295.4049987792969, "close": 296.20001220703125, "volume": 337551}, {"epoch": 1781534700.0, "open": 296.2200012207031, "high": 296.70001220703125, "low": 296.1600036621094, "close": 296.5350036621094, "volume": 381197}, {"epoch": 1781535000.0, "open": 296.5350036621094, "high": 296.70001220703125, "low": 296.2200012207031, "close": 296.639892578125, "volume": 312054}, {"epoch": 1781535300.0, "open": 296.6300048828125, "high": 296.6499938964844, "low": 296.2900085449219, "close": 296.4830017089844, "volume": 295564}, {"epoch": 1781535600.0, "open": 296.5, "high": 296.8999938964844, "low": 296.4100036621094, "close": 296.7349853515625, "volume": 352338}, {"epoch": 1781535900.0, "open": 296.760009765625, "high": 296.7799987792969, "low": 296.17010498046875, "close": 296.30999755859375, "volume": 340727}, {"epoch": 1781536200.0, "open": 296.30999755859375, "high": 296.489990234375, "low": 296.1700134277344, "close": 296.30999755859375, "volume": 263922}, {"epoch": 1781536500.0, "open": 296.32000732421875, "high": 296.57000732421875, "low": 296.2900085449219, "close": 296.3699951171875, "volume": 249570}, {"epoch": 1781536800.0, "open": 296.3599853515625, "high": 296.57000732421875, "low": 296.3500061035156, "close": 296.5400085449219, "volume": 240465}, {"epoch": 1781537100.0, "open": 296.54998779296875, "high": 296.8500061035156, "low": 296.4700012207031, "close": 296.5299987792969, "volume": 411544}, {"epoch": 1781537400.0, "open": 296.5400085449219, "high": 296.7349853515625, "low": 296.2200012207031, "close": 296.47088623046875, "volume": 429350}, {"epoch": 1781537700.0, "open": 296.4750061035156, "high": 296.7799987792969, "low": 296.3699951171875, "close": 296.71490478515625, "volume": 272495}, {"epoch": 1781538000.0, "open": 296.7099914550781, "high": 297.2099914550781, "low": 296.69000244140625, "close": 297.0299987792969, "volume": 381052}, {"epoch": 1781538300.0, "open": 297.0299987792969, "high": 297.543701171875, "low": 297.0299987792969, "close": 297.5350036621094, "volume": 428226}, {"epoch": 1781538600.0, "open": 297.5299987792969, "high": 297.6000061035156, "low": 297.2099914550781, "close": 297.30999755859375, "volume": 455765}, {"epoch": 1781538900.0, "open": 297.3197937011719, "high": 297.7799987792969, "low": 297.2099914550781, "close": 297.4800109863281, "volume": 267685}, {"epoch": 1781539200.0, "open": 297.4800109863281, "high": 297.7699890136719, "low": 297.3399963378906, "close": 297.4800109863281, "volume": 331563}, {"epoch": 1781539500.0, "open": 297.489990234375, "high": 297.57989501953125, "low": 297.260009765625, "close": 297.2699890136719, "volume": 217944}, {"epoch": 1781539800.0, "open": 297.2749938964844, "high": 297.3599853515625, "low": 296.8901062011719, "close": 297.07501220703125, "volume": 354453}, {"epoch": 1781540100.0, "open": 297.07501220703125, "high": 297.1199951171875, "low": 296.8700866699219, "close": 297.06500244140625, "volume": 215086}, {"epoch": 1781540400.0, "open": 297.0707092285156, "high": 297.3500061035156, "low": 297.0199890136719, "close": 297.239990234375, "volume": 230001}, {"epoch": 1781540700.0, "open": 297.25, "high": 297.3550109863281, "low": 297.114990234375, "close": 297.239990234375, "volume": 184174}, {"epoch": 1781541000.0, "open": 297.2300109863281, "high": 297.364990234375, "low": 297.07000732421875, "close": 297.2099914550781, "volume": 190034}, {"epoch": 1781541300.0, "open": 297.2200012207031, "high": 297.2550048828125, "low": 296.94000244140625, "close": 297.05999755859375, "volume": 191642}, {"epoch": 1781541600.0, "open": 297.05999755859375, "high": 297.1099853515625, "low": 296.8500061035156, "close": 296.9599914550781, "volume": 172751}, {"epoch": 1781541900.0, "open": 296.9700012207031, "high": 296.9800109863281, "low": 296.69000244140625, "close": 296.7099914550781, "volume": 233895}, {"epoch": 1781542200.0, "open": 296.70001220703125, "high": 296.8999938964844, "low": 296.55999755859375, "close": 296.69000244140625, "volume": 182820}, {"epoch": 1781542500.0, "open": 296.69000244140625, "high": 296.9700012207031, "low": 296.56500244140625, "close": 296.94500732421875, "volume": 154680}, {"epoch": 1781542800.0, "open": 296.9200134277344, "high": 296.9200134277344, "low": 296.25, "close": 296.5799865722656, "volume": 270666}, {"epoch": 1781543100.0, "open": 296.5899963378906, "high": 296.70001220703125, "low": 296.25, "close": 296.5950012207031, "volume": 264458}, {"epoch": 1781543400.0, "open": 296.5950012207031, "high": 296.7799987792969, "low": 296.56500244140625, "close": 296.70001220703125, "volume": 213945}, {"epoch": 1781543700.0, "open": 296.69000244140625, "high": 297.1199951171875, "low": 296.6007080078125, "close": 296.7950134277344, "volume": 372039}, {"epoch": 1781544000.0, "open": 296.7950134277344, "high": 297.2099914550781, "low": 296.7650146484375, "close": 296.8555908203125, "volume": 319994}, {"epoch": 1781544300.0, "open": 296.8399963378906, "high": 296.95001220703125, "low": 296.54998779296875, "close": 296.6600036621094, "volume": 254209}, {"epoch": 1781544600.0, "open": 296.6600036621094, "high": 296.79998779296875, "low": 296.3900146484375, "close": 296.5799865722656, "volume": 278145}, {"epoch": 1781544900.0, "open": 296.5950012207031, "high": 297.0, "low": 296.5950012207031, "close": 296.92999267578125, "volume": 252645}, {"epoch": 1781545200.0, "open": 296.92999267578125, "high": 296.9800109863281, "low": 296.5199890136719, "close": 296.5899963378906, "volume": 252042}, {"epoch": 1781545500.0, "open": 296.5799865722656, "high": 296.6199951171875, "low": 296.2799987792969, "close": 296.3900146484375, "volume": 241487}, {"epoch": 1781545800.0, "open": 296.3900146484375, "high": 296.3900146484375, "low": 295.95001220703125, "close": 295.9549865722656, "volume": 211749}, {"epoch": 1781546100.0, "open": 295.94000244140625, "high": 296.0, "low": 295.6300048828125, "close": 295.760009765625, "volume": 287708}, {"epoch": 1781546400.0, "open": 295.75, "high": 295.8263854980469, "low": 295.1600036621094, "close": 295.2301025390625, "volume": 448128}, {"epoch": 1781546700.0, "open": 295.239990234375, "high": 295.80999755859375, "low": 295.17999267578125, "close": 295.75, "volume": 381524}, {"epoch": 1781547000.0, "open": 295.7099914550781, "high": 295.75, "low": 295.54998779296875, "close": 295.6400146484375, "volume": 175171}, {"epoch": 1781547300.0, "open": 295.6400146484375, "high": 295.739990234375, "low": 295.1099853515625, "close": 295.1700134277344, "volume": 238798}, {"epoch": 1781547600.0, "open": 295.1650085449219, "high": 295.5899963378906, "low": 295.1600036621094, "close": 295.20001220703125, "volume": 358379}, {"epoch": 1781547900.0, "open": 295.19000244140625, "high": 295.2200012207031, "low": 294.9599914550781, "close": 295.07000732421875, "volume": 308690}, {"epoch": 1781548200.0, "open": 295.07501220703125, "high": 295.6099853515625, "low": 295.010009765625, "close": 295.54998779296875, "volume": 272134}, {"epoch": 1781548500.0, "open": 295.5404968261719, "high": 295.8599853515625, "low": 295.3450012207031, "close": 295.8500061035156, "volume": 287116}, {"epoch": 1781548800.0, "open": 295.8550109863281, "high": 296.2900085449219, "low": 295.80999755859375, "close": 296.2099914550781, "volume": 450407}, {"epoch": 1781549100.0, "open": 296.20001220703125, "high": 296.34991455078125, "low": 296.16009521484375, "close": 296.2139892578125, "volume": 251798}, {"epoch": 1781549400.0, "open": 296.2300109863281, "high": 296.3599853515625, "low": 296.1600036621094, "close": 296.1700134277344, "volume": 192994}, {"epoch": 1781549700.0, "open": 296.1600036621094, "high": 296.4049987792969, "low": 296.1549987792969, "close": 296.3949890136719, "volume": 236271}, {"epoch": 1781550000.0, "open": 296.3900146484375, "high": 296.4200134277344, "low": 296.239990234375, "close": 296.375, "volume": 252423}, {"epoch": 1781550300.0, "open": 296.360107421875, "high": 296.4649963378906, "low": 296.1600036621094, "close": 296.29058837890625, "volume": 202104}, {"epoch": 1781550600.0, "open": 296.30999755859375, "high": 296.45001220703125, "low": 296.2099914550781, "close": 296.3949890136719, "volume": 211848}, {"epoch": 1781550900.0, "open": 296.3807067871094, "high": 296.489990234375, "low": 295.9700012207031, "close": 296.0199890136719, "volume": 236914}, {"epoch": 1781551200.0, "open": 296.0299987792969, "high": 296.2049865722656, "low": 295.9800109863281, "close": 296.18011474609375, "volume": 246209}, {"epoch": 1781551500.0, "open": 296.19000244140625, "high": 296.6099853515625, "low": 296.1400146484375, "close": 296.5, "volume": 367813}, {"epoch": 1781551800.0, "open": 296.4949951171875, "high": 296.6700134277344, "low": 296.3399963378906, "close": 296.3800048828125, "volume": 449598}, {"epoch": 1781552100.0, "open": 296.3800048828125, "high": 296.4100036621094, "low": 295.8700866699219, "close": 296.1600036621094, "volume": 377890}, {"epoch": 1781552400.0, "open": 296.1499938964844, "high": 296.3949890136719, "low": 296.0, "close": 296.3200988769531, "volume": 334037}, {"epoch": 1781552700.0, "open": 296.3299865722656, "high": 296.43499755859375, "low": 296.1549987792969, "close": 296.3599853515625, "volume": 492679}, {"epoch": 1781553000.0, "open": 296.3500061035156, "high": 296.3900146484375, "low": 295.6700134277344, "close": 295.80999755859375, "volume": 1008353}, {"epoch": 1781553300.0, "open": 295.80999755859375, "high": 296.5299987792969, "low": 295.6099853515625, "close": 296.4200134277344, "volume": 15539827}, {"epoch": 1781616600.0, "open": 295.2449951171875, "high": 296.2799987792969, "low": 294.32000732421875, "close": 296.260009765625, "volume": 1602940}, {"epoch": 1781616900.0, "open": 296.2650146484375, "high": 296.4800109863281, "low": 294.6199951171875, "close": 294.63189697265625, "volume": 485631}, {"epoch": 1781617200.0, "open": 294.625, "high": 295.3999938964844, "low": 293.9700012207031, "close": 295.3999938964844, "volume": 582233}, {"epoch": 1781617500.0, "open": 295.40008544921875, "high": 295.9596862792969, "low": 295.25, "close": 295.7699890136719, "volume": 381292}, {"epoch": 1781617800.0, "open": 295.7900085449219, "high": 297.5199890136719, "low": 295.7401123046875, "close": 297.4750061035156, "volume": 566454}, {"epoch": 1781618100.0, "open": 297.4750061035156, "high": 297.95001220703125, "low": 297.07000732421875, "close": 297.0799865722656, "volume": 530131}, {"epoch": 1781618400.0, "open": 297.0849914550781, "high": 297.7799987792969, "low": 296.864990234375, "close": 297.4898986816406, "volume": 476918}, {"epoch": 1781618700.0, "open": 297.489990234375, "high": 297.5398864746094, "low": 297.1000061035156, "close": 297.25, "volume": 260208}, {"epoch": 1781619000.0, "open": 297.25, "high": 297.79998779296875, "low": 297.19000244140625, "close": 297.4200134277344, "volume": 530169}, {"epoch": 1781619300.0, "open": 297.43499755859375, "high": 298.0, "low": 297.36090087890625, "close": 297.6549987792969, "volume": 401151}, {"epoch": 1781619600.0, "open": 297.6400146484375, "high": 297.95001220703125, "low": 297.1600036621094, "close": 297.5, "volume": 477366}, {"epoch": 1781619900.0, "open": 297.56500244140625, "high": 297.659912109375, "low": 296.7099914550781, "close": 297.5350036621094, "volume": 453527}, {"epoch": 1781620200.0, "open": 297.5350036621094, "high": 297.8900146484375, "low": 297.1178894042969, "close": 297.1499938964844, "volume": 527017}, {"epoch": 1781620500.0, "open": 297.1650085449219, "high": 297.5199890136719, "low": 296.95001220703125, "close": 297.42999267578125, "volume": 366712}, {"epoch": 1781620800.0, "open": 297.4100036621094, "high": 297.7300109863281, "low": 297.2099914550781, "close": 297.3299865722656, "volume": 412720}, {"epoch": 1781621100.0, "open": 297.2699890136719, "high": 297.9599914550781, "low": 297.2699890136719, "close": 297.7699890136719, "volume": 411774}, {"epoch": 1781621400.0, "open": 297.7262878417969, "high": 297.9700012207031, "low": 297.4700927734375, "close": 297.8699951171875, "volume": 335388}, {"epoch": 1781621700.0, "open": 297.8800048828125, "high": 298.0, "low": 297.4599914550781, "close": 297.54998779296875, "volume": 351919}, {"epoch": 1781622000.0, "open": 297.5400085449219, "high": 297.8599853515625, "low": 297.489990234375, "close": 297.7799987792969, "volume": 226362}, {"epoch": 1781622300.0, "open": 297.7749938964844, "high": 298.2300109863281, "low": 297.67999267578125, "close": 298.1199951171875, "volume": 482993}, {"epoch": 1781622600.0, "open": 298.114990234375, "high": 298.19000244140625, "low": 297.82501220703125, "close": 298.1300048828125, "volume": 302532}, {"epoch": 1781622900.0, "open": 298.1099853515625, "high": 298.1099853515625, "low": 297.4949951171875, "close": 297.5, "volume": 258936}, {"epoch": 1781623200.0, "open": 297.5, "high": 298.1000061035156, "low": 297.2049865722656, "close": 298.07501220703125, "volume": 545222}, {"epoch": 1781623500.0, "open": 298.0899963378906, "high": 298.45001220703125, "low": 297.95001220703125, "close": 298.20001220703125, "volume": 376093}, {"epoch": 1781623800.0, "open": 298.2200012207031, "high": 298.2799987792969, "low": 297.57000732421875, "close": 297.7900085449219, "volume": 246844}, {"epoch": 1781624100.0, "open": 297.79998779296875, "high": 298.43701171875, "low": 297.5, "close": 298.42498779296875, "volume": 243446}, {"epoch": 1781624400.0, "open": 298.4100036621094, "high": 298.42999267578125, "low": 298.0, "close": 298.0849914550781, "volume": 323358}, {"epoch": 1781624700.0, "open": 298.0849914550781, "high": 298.3949890136719, "low": 298.0, "close": 298.3949890136719, "volume": 374748}, {"epoch": 1781625000.0, "open": 298.3949890136719, "high": 298.57000732421875, "low": 298.0299987792969, "close": 298.239990234375, "volume": 325830}, {"epoch": 1781625300.0, "open": 298.25, "high": 298.3949890136719, "low": 298.0400085449219, "close": 298.1700134277344, "volume": 269489}, {"epoch": 1781625600.0, "open": 298.1700134277344, "high": 298.739990234375, "low": 298.05999755859375, "close": 298.2799987792969, "volume": 535345}, {"epoch": 1781625900.0, "open": 298.2699890136719, "high": 298.53009033203125, "low": 298.0400085449219, "close": 298.510009765625, "volume": 208311}, {"epoch": 1781626200.0, "open": 298.510009765625, "high": 299.20001220703125, "low": 298.4700012207031, "close": 299.0950012207031, "volume": 679063}, {"epoch": 1781626500.0, "open": 299.090087890625, "high": 299.2749938964844, "low": 298.8900146484375, "close": 299.0264892578125, "volume": 311694}, {"epoch": 1781626800.0, "open": 299.0400085449219, "high": 299.1700134277344, "low": 298.875, "close": 299.04998779296875, "volume": 239508}, {"epoch": 1781627100.0, "open": 299.04998779296875, "high": 299.18499755859375, "low": 298.7300109863281, "close": 298.94000244140625, "volume": 188443}, {"epoch": 1781627400.0, "open": 298.94000244140625, "high": 299.260009765625, "low": 298.8041076660156, "close": 298.9599914550781, "volume": 279778}, {"epoch": 1781627700.0, "open": 298.9700012207031, "high": 299.20001220703125, "low": 298.92010498046875, "close": 299.1199035644531, "volume": 220607}, {"epoch": 1781628000.0, "open": 299.1199951171875, "high": 299.1499938964844, "low": 298.81500244140625, "close": 299.0799865722656, "volume": 314529}, {"epoch": 1781628300.0, "open": 299.06500244140625, "high": 299.6499938964844, "low": 299.0299987792969, "close": 299.5899963378906, "volume": 297894}, {"epoch": 1781628600.0, "open": 299.5899963378906, "high": 299.7699890136719, "low": 299.239990234375, "close": 299.3699951171875, "volume": 262559}, {"epoch": 1781628900.0, "open": 299.3599853515625, "high": 299.55999755859375, "low": 299.239990234375, "close": 299.4700012207031, "volume": 218359}, {"epoch": 1781629200.0, "open": 299.45001220703125, "high": 299.4800109863281, "low": 299.0899963378906, "close": 299.2099914550781, "volume": 178554}, {"epoch": 1781629500.0, "open": 299.18011474609375, "high": 299.5199890136719, "low": 299.1600036621094, "close": 299.4800109863281, "volume": 226791}, {"epoch": 1781629800.0, "open": 299.489990234375, "high": 299.70001220703125, "low": 299.4700012207031, "close": 299.6650085449219, "volume": 205421}, {"epoch": 1781630100.0, "open": 299.6700134277344, "high": 300.4800109863281, "low": 299.6700134277344, "close": 300.1600036621094, "volume": 1090696}, {"epoch": 1781630400.0, "open": 300.1600036621094, "high": 300.3500061035156, "low": 300.0150146484375, "close": 300.1549987792969, "volume": 313326}, {"epoch": 1781630700.0, "open": 300.1600036621094, "high": 300.3800048828125, "low": 300.1449890136719, "close": 300.2749938964844, "volume": 190110}, {"epoch": 1781631000.0, "open": 300.260009765625, "high": 300.4599914550781, "low": 300.1300048828125, "close": 300.17999267578125, "volume": 197115}, {"epoch": 1781631300.0, "open": 300.17999267578125, "high": 300.2699890136719, "low": 299.82000732421875, "close": 299.8999938964844, "volume": 245800}, {"epoch": 1781631600.0, "open": 299.9049987792969, "high": 300.0799865722656, "low": 299.8399963378906, "close": 299.8399963378906, "volume": 256579}, {"epoch": 1781631900.0, "open": 299.8399963378906, "high": 299.9200134277344, "low": 299.6300048828125, "close": 299.8999938964844, "volume": 238850}, {"epoch": 1781632200.0, "open": 299.8999938964844, "high": 299.95001220703125, "low": 299.3500061035156, "close": 299.6549987792969, "volume": 214535}, {"epoch": 1781632500.0, "open": 299.6449890136719, "high": 299.7799987792969, "low": 299.5400085449219, "close": 299.6000061035156, "volume": 202289}, {"epoch": 1781632800.0, "open": 299.5899963378906, "high": 299.6300048828125, "low": 299.3999938964844, "close": 299.5101013183594, "volume": 216365}, {"epoch": 1781633100.0, "open": 299.5249938964844, "high": 299.760009765625, "low": 299.2250061035156, "close": 299.2799987792969, "volume": 225237}, {"epoch": 1781633400.0, "open": 299.2749938964844, "high": 299.29998779296875, "low": 298.9100036621094, "close": 298.9901123046875, "volume": 212017}, {"epoch": 1781633700.0, "open": 298.9700012207031, "high": 299.07989501953125, "low": 298.8299865722656, "close": 298.8599853515625, "volume": 223658}, {"epoch": 1781634000.0, "open": 298.8500061035156, "high": 298.89599609375, "low": 298.5679931640625, "close": 298.67999267578125, "volume": 164418}, {"epoch": 1781634300.0, "open": 298.6700134277344, "high": 298.9798889160156, "low": 298.6300048828125, "close": 298.7250061035156, "volume": 181832}, {"epoch": 1781634600.0, "open": 298.7200927734375, "high": 298.79998779296875, "low": 298.6300048828125, "close": 298.7149963378906, "volume": 189418}, {"epoch": 1781634900.0, "open": 298.7099914550781, "high": 299.4999084472656, "low": 298.70001220703125, "close": 299.45001220703125, "volume": 266390}, {"epoch": 1781635200.0, "open": 299.45001220703125, "high": 299.63031005859375, "low": 299.4100036621094, "close": 299.53509521484375, "volume": 293517}, {"epoch": 1781635500.0, "open": 299.5400085449219, "high": 299.57000732421875, "low": 299.364990234375, "close": 299.4100036621094, "volume": 181727}, {"epoch": 1781635800.0, "open": 299.4200134277344, "high": 299.5400085449219, "low": 299.2799987792969, "close": 299.30499267578125, "volume": 492783}, {"epoch": 1781636100.0, "open": 299.29998779296875, "high": 299.5199890136719, "low": 299.1650085449219, "close": 299.17559814453125, "volume": 216555}, {"epoch": 1781636400.0, "open": 299.17498779296875, "high": 299.25, "low": 298.8299865722656, "close": 298.8699035644531, "volume": 269817}, {"epoch": 1781636700.0, "open": 298.8599853515625, "high": 299.0, "low": 298.7200012207031, "close": 298.9725036621094, "volume": 249903}, {"epoch": 1781637000.0, "open": 298.989990234375, "high": 299.05999755859375, "low": 298.8399963378906, "close": 298.9200134277344, "volume": 256948}, {"epoch": 1781637300.0, "open": 298.92999267578125, "high": 299.1300048828125, "low": 298.67498779296875, "close": 298.9200134277344, "volume": 375244}, {"epoch": 1781637600.0, "open": 298.9200134277344, "high": 298.92999267578125, "low": 298.4700012207031, "close": 298.47369384765625, "volume": 348196}, {"epoch": 1781637900.0, "open": 298.4750061035156, "high": 298.739990234375, "low": 298.2200012207031, "close": 298.3399963378906, "volume": 287039}, {"epoch": 1781638200.0, "open": 298.3299865722656, "high": 298.54998779296875, "low": 298.2300109863281, "close": 298.3949890136719, "volume": 275311}, {"epoch": 1781638500.0, "open": 298.3999938964844, "high": 298.59991455078125, "low": 298.3500061035156, "close": 298.56500244140625, "volume": 262941}, {"epoch": 1781638800.0, "open": 298.55999755859375, "high": 298.7149963378906, "low": 298.489990234375, "close": 298.57000732421875, "volume": 264710}, {"epoch": 1781639100.0, "open": 298.57000732421875, "high": 299.010009765625, "low": 298.54998779296875, "close": 299.010009765625, "volume": 717068}, {"epoch": 1781639400.0, "open": 299.010009765625, "high": 299.30999755859375, "low": 298.69500732421875, "close": 299.2799987792969, "volume": 769361}, {"epoch": 1781639700.0, "open": 299.260009765625, "high": 299.489990234375, "low": 298.8999938964844, "close": 299.25, "volume": 2173131}, {"epoch": 1781703000.0, "open": 300.8450012207031, "high": 302.07000732421875, "low": 299.5201110839844, "close": 300.3399963378906, "volume": 1784592}, {"epoch": 1781703300.0, "open": 300.3399963378906, "high": 300.8900146484375, "low": 299.8999938964844, "close": 300.75, "volume": 559876}, {"epoch": 1781703600.0, "open": 300.78021240234375, "high": 301.7900085449219, "low": 300.4750061035156, "close": 301.25, "volume": 559855}, {"epoch": 1781703900.0, "open": 301.2300109863281, "high": 301.32000732421875, "low": 299.80999755859375, "close": 299.8500061035156, "volume": 517263}, {"epoch": 1781704200.0, "open": 299.79998779296875, "high": 300.625, "low": 299.22198486328125, "close": 300.55499267578125, "volume": 594356}, {"epoch": 1781704500.0, "open": 300.55999755859375, "high": 300.739990234375, "low": 300.29998779296875, "close": 300.29998779296875, "volume": 416864}, {"epoch": 1781704800.0, "open": 300.3399963378906, "high": 300.5150146484375, "low": 299.3700866699219, "close": 299.614990234375, "volume": 380132}, {"epoch": 1781705100.0, "open": 299.5799865722656, "high": 300.3599853515625, "low": 299.54998779296875, "close": 300.25, "volume": 429479}, {"epoch": 1781705400.0, "open": 300.2300109863281, "high": 300.4599914550781, "low": 300.0, "close": 300.45001220703125, "volume": 252705}, {"epoch": 1781705700.0, "open": 300.45001220703125, "high": 300.6000061035156, "low": 299.92999267578125, "close": 300.3599853515625, "volume": 321724}, {"epoch": 1781706000.0, "open": 300.3599853515625, "high": 300.6700134277344, "low": 299.989990234375, "close": 300.6099853515625, "volume": 352078}, {"epoch": 1781706300.0, "open": 300.6199951171875, "high": 300.9674987792969, "low": 300.4049987792969, "close": 300.45001220703125, "volume": 267172}, {"epoch": 1781706600.0, "open": 300.45001220703125, "high": 300.53948974609375, "low": 299.6499938964844, "close": 299.793212890625, "volume": 349113}, {"epoch": 1781706900.0, "open": 299.76190185546875, "high": 299.7799987792969, "low": 298.8599853515625, "close": 298.9200134277344, "volume": 396092}, {"epoch": 1781707200.0, "open": 298.9100036621094, "high": 299.7398986816406, "low": 298.67999267578125, "close": 299.6000061035156, "volume": 534585}, {"epoch": 1781707500.0, "open": 299.5799865722656, "high": 299.8500061035156, "low": 298.760009765625, "close": 299.3299865722656, "volume": 418255}, {"epoch": 1781707800.0, "open": 299.32501220703125, "high": 299.32501220703125, "low": 298.5849914550781, "close": 298.6300048828125, "volume": 353178}, {"epoch": 1781708100.0, "open": 298.6099853515625, "high": 298.7799987792969, "low": 298.3500061035156, "close": 298.5400085449219, "volume": 302524}, {"epoch": 1781708400.0, "open": 298.54998779296875, "high": 298.69000244140625, "low": 297.4800109863281, "close": 297.5199890136719, "volume": 413809}, {"epoch": 1781708700.0, "open": 297.54998779296875, "high": 297.6700134277344, "low": 297.239990234375, "close": 297.2699890136719, "volume": 332477}, {"epoch": 1781709000.0, "open": 297.2799987792969, "high": 297.6000061035156, "low": 297.0899963378906, "close": 297.45001220703125, "volume": 242592}, {"epoch": 1781709300.0, "open": 297.44500732421875, "high": 298.1400146484375, "low": 297.44500732421875, "close": 297.80999755859375, "volume": 321187}, {"epoch": 1781709600.0, "open": 297.82000732421875, "high": 298.0199890136719, "low": 297.69000244140625, "close": 298.0050048828125, "volume": 180300}, {"epoch": 1781709900.0, "open": 297.989990234375, "high": 298.010009765625, "low": 297.20001220703125, "close": 297.42999267578125, "volume": 212682}, {"epoch": 1781710200.0, "open": 297.42999267578125, "high": 297.44000244140625, "low": 297.1000061035156, "close": 297.3999938964844, "volume": 278832}, {"epoch": 1781710500.0, "open": 297.3949890136719, "high": 297.4599914550781, "low": 297.0, "close": 297.0799865722656, "volume": 260733}, {"epoch": 1781710800.0, "open": 297.0849914550781, "high": 297.2699890136719, "low": 296.6700134277344, "close": 296.82000732421875, "volume": 353522}, {"epoch": 1781711100.0, "open": 296.8330078125, "high": 297.4049987792969, "low": 296.6400146484375, "close": 297.31500244140625, "volume": 305255}, {"epoch": 1781711400.0, "open": 297.32000732421875, "high": 297.8599853515625, "low": 297.30999755859375, "close": 297.8599853515625, "volume": 314759}, {"epoch": 1781711700.0, "open": 297.864990234375, "high": 298.7699890136719, "low": 297.80999755859375, "close": 298.55499267578125, "volume": 298511}, {"epoch": 1781712000.0, "open": 298.55999755859375, "high": 299.1600036621094, "low": 298.5400085449219, "close": 298.9150085449219, "volume": 313427}, {"epoch": 1781712300.0, "open": 298.9100036621094, "high": 299.0299987792969, "low": 298.2300109863281, "close": 298.25750732421875, "volume": 859454}, {"epoch": 1781712600.0, "open": 298.2550048828125, "high": 298.55999755859375, "low": 298.1499938964844, "close": 298.42999267578125, "volume": 343032}, {"epoch": 1781712900.0, "open": 298.44000244140625, "high": 298.7489929199219, "low": 298.4093017578125, "close": 298.7300109863281, "volume": 145790}, {"epoch": 1781713200.0, "open": 298.7200927734375, "high": 298.7699890136719, "low": 298.33099365234375, "close": 298.66009521484375, "volume": 145897}, {"epoch": 1781713500.0, "open": 298.6700134277344, "high": 298.8760070800781, "low": 298.6000061035156, "close": 298.614990234375, "volume": 131032}, {"epoch": 1781713800.0, "open": 298.6297912597656, "high": 298.69989013671875, "low": 298.41009521484375, "close": 298.6300048828125, "volume": 195264}, {"epoch": 1781714100.0, "open": 298.625, "high": 298.7449951171875, "low": 298.2300109863281, "close": 298.4200134277344, "volume": 193981}, {"epoch": 1781714400.0, "open": 298.4200134277344, "high": 298.55999755859375, "low": 298.260009765625, "close": 298.4599914550781, "volume": 187683}, {"epoch": 1781714700.0, "open": 298.4700012207031, "high": 298.4700012207031, "low": 298.1321105957031, "close": 298.3999938964844, "volume": 149360}, {"epoch": 1781715000.0, "open": 298.3999938964844, "high": 298.489990234375, "low": 298.2200012207031, "close": 298.4100036621094, "volume": 155009}, {"epoch": 1781715300.0, "open": 298.3999938964844, "high": 298.5299987792969, "low": 298.0950012207031, "close": 298.20001220703125, "volume": 159946}, {"epoch": 1781715600.0, "open": 298.2099914550781, "high": 298.2099914550781, "low": 297.2300109863281, "close": 297.2699890136719, "volume": 334978}, {"epoch": 1781715900.0, "open": 297.25, "high": 297.2850036621094, "low": 296.5899963378906, "close": 296.8699951171875, "volume": 322300}, {"epoch": 1781716200.0, "open": 296.8599853515625, "high": 297.0994873046875, "low": 296.6449890136719, "close": 296.7049865722656, "volume": 288685}, {"epoch": 1781716500.0, "open": 296.70001220703125, "high": 297.0400085449219, "low": 296.5719909667969, "close": 297.0199890136719, "volume": 248136}, {"epoch": 1781716800.0, "open": 297.0199890136719, "high": 297.239990234375, "low": 296.8100891113281, "close": 296.8100891113281, "volume": 191325}, {"epoch": 1781717100.0, "open": 296.82501220703125, "high": 296.9700012207031, "low": 296.57000732421875, "close": 296.80999755859375, "volume": 186534}, {"epoch": 1781717400.0, "open": 296.79998779296875, "high": 296.79998779296875, "low": 296.42999267578125, "close": 296.4750061035156, "volume": 216496}, {"epoch": 1781717700.0, "open": 296.4800109863281, "high": 297.1099853515625, "low": 296.4599914550781, "close": 297.0400085449219, "volume": 172260}, {"epoch": 1781718000.0, "open": 297.07000732421875, "high": 297.1050109863281, "low": 296.8299865722656, "close": 296.8500061035156, "volume": 150954}, {"epoch": 1781718300.0, "open": 296.8599853515625, "high": 297.2300109863281, "low": 296.8500061035156, "close": 297.2101135253906, "volume": 132348}, {"epoch": 1781718600.0, "open": 297.2099914550781, "high": 297.6000061035156, "low": 297.1600036621094, "close": 297.45001220703125, "volume": 187748}, {"epoch": 1781718900.0, "open": 297.44000244140625, "high": 297.54998779296875, "low": 297.2200012207031, "close": 297.54998779296875, "volume": 141405}, {"epoch": 1781719200.0, "open": 297.5299987792969, "high": 297.5299987792969, "low": 296.25, "close": 296.2850036621094, "volume": 530052}, {"epoch": 1781719500.0, "open": 296.260009765625, "high": 296.5400085449219, "low": 295.69000244140625, "close": 296.2550048828125, "volume": 508804}, {"epoch": 1781719800.0, "open": 296.260009765625, "high": 296.3800048828125, "low": 295.6499938964844, "close": 295.8299865722656, "volume": 535079}, {"epoch": 1781720100.0, "open": 295.8599853515625, "high": 296.5299987792969, "low": 295.8599853515625, "close": 296.3599853515625, "volume": 264960}, {"epoch": 1781720400.0, "open": 296.3500061035156, "high": 296.3800048828125, "low": 295.6000061035156, "close": 295.6700134277344, "volume": 233115}, {"epoch": 1781720700.0, "open": 295.6400146484375, "high": 295.8699951171875, "low": 295.3299865722656, "close": 295.8349914550781, "volume": 266660}, {"epoch": 1781721000.0, "open": 295.82000732421875, "high": 296.3299865722656, "low": 295.2073059082031, "close": 295.2900085449219, "volume": 483458}, {"epoch": 1781721300.0, "open": 295.2900085449219, "high": 295.989990234375, "low": 295.20001220703125, "close": 295.55999755859375, "volume": 313201}, {"epoch": 1781721600.0, "open": 295.5799865722656, "high": 296.4200134277344, "low": 295.5, "close": 296.29998779296875, "volume": 371508}, {"epoch": 1781721900.0, "open": 296.2799987792969, "high": 296.32000732421875, "low": 295.5, "close": 295.510009765625, "volume": 317015}, {"epoch": 1781722200.0, "open": 295.5050048828125, "high": 295.6499938964844, "low": 295.2500915527344, "close": 295.2699890136719, "volume": 279333}, {"epoch": 1781722500.0, "open": 295.2699890136719, "high": 295.2699890136719, "low": 294.3800048828125, "close": 294.5899963378906, "volume": 418722}, {"epoch": 1781722800.0, "open": 294.5899963378906, "high": 295.0899963378906, "low": 294.3900146484375, "close": 294.9649963378906, "volume": 434234}, {"epoch": 1781723100.0, "open": 294.9549865722656, "high": 295.32000732421875, "low": 294.8900146484375, "close": 295.00579833984375, "volume": 346443}, {"epoch": 1781723400.0, "open": 295.0, "high": 295.8399963378906, "low": 294.7799987792969, "close": 295.5400085449219, "volume": 371119}, {"epoch": 1781723700.0, "open": 295.5299987792969, "high": 295.6549987792969, "low": 295.0899963378906, "close": 295.090087890625, "volume": 285053}, {"epoch": 1781724000.0, "open": 295.1199951171875, "high": 295.3800048828125, "low": 294.82501220703125, "close": 295.0799865722656, "volume": 339972}, {"epoch": 1781724300.0, "open": 295.0799865722656, "high": 295.45001220703125, "low": 295.0199890136719, "close": 295.18499755859375, "volume": 355738}, {"epoch": 1781724600.0, "open": 295.1600036621094, "high": 295.3500061035156, "low": 294.86749267578125, "close": 295.1199951171875, "volume": 560180}, {"epoch": 1781724900.0, "open": 295.12298583984375, "high": 295.44000244140625, "low": 294.885009765625, "close": 295.05999755859375, "volume": 385182}, {"epoch": 1781725200.0, "open": 295.04998779296875, "high": 295.25, "low": 294.6000061035156, "close": 294.94000244140625, "volume": 592494}, {"epoch": 1781725500.0, "open": 294.92999267578125, "high": 295.2900085449219, "low": 294.79998779296875, "close": 295.1499938964844, "volume": 397795}, {"epoch": 1781725800.0, "open": 295.0899963378906, "high": 295.739990234375, "low": 294.5899963378906, "close": 295.385009765625, "volume": 820852}, {"epoch": 1781726100.0, "open": 295.3970031738281, "high": 296.2200012207031, "low": 295.3399963378906, "close": 295.8800048828125, "volume": 1680932}, {"epoch": 1781789400.0, "open": 298.44000244140625, "high": 300.45989990234375, "low": 298.07000732421875, "close": 298.0899963378906, "volume": 12767171}, {"epoch": 1781789700.0, "open": 298.0899963378906, "high": 298.1799011230469, "low": 295.6199951171875, "close": 296.364990234375, "volume": 1237649}, {"epoch": 1781790000.0, "open": 296.4100036621094, "high": 297.6979064941406, "low": 295.6900939941406, "close": 297.69000244140625, "volume": 944313}, {"epoch": 1781790300.0, "open": 297.70001220703125, "high": 298.04998779296875, "low": 297.1499938964844, "close": 298.0299072265625, "volume": 578365}, {"epoch": 1781790600.0, "open": 297.9800109863281, "high": 298.625, "low": 297.56500244140625, "close": 298.1099853515625, "volume": 2463222}, {"epoch": 1781790900.0, "open": 298.1499938964844, "high": 298.70001220703125, "low": 297.8599853515625, "close": 298.2749938964844, "volume": 558458}, {"epoch": 1781791200.0, "open": 298.30999755859375, "high": 299.159912109375, "low": 298.0199890136719, "close": 298.8900146484375, "volume": 993202}, {"epoch": 1781791500.0, "open": 298.8299865722656, "high": 299.42999267578125, "low": 298.4800109863281, "close": 299.2699890136719, "volume": 4306661}, {"epoch": 1781791800.0, "open": 299.2699890136719, "high": 299.3900146484375, "low": 298.75, "close": 298.989990234375, "volume": 546734}, {"epoch": 1781792100.0, "open": 298.9649963378906, "high": 299.4700012207031, "low": 298.54998779296875, "close": 299.2650146484375, "volume": 765304}, {"epoch": 1781792400.0, "open": 299.2900085449219, "high": 299.30999755859375, "low": 298.2200012207031, "close": 299.1400146484375, "volume": 466066}, {"epoch": 1781792700.0, "open": 299.1499938964844, "high": 299.6300048828125, "low": 298.6700134277344, "close": 299.6099853515625, "volume": 562550}, {"epoch": 1781793000.0, "open": 299.614990234375, "high": 299.75, "low": 298.5, "close": 298.8699951171875, "volume": 617625}, {"epoch": 1781793300.0, "open": 298.8900146484375, "high": 299.4549865722656, "low": 298.67999267578125, "close": 299.4200134277344, "volume": 352174}, {"epoch": 1781793600.0, "open": 299.42999267578125, "high": 299.760009765625, "low": 299.1642150878906, "close": 299.7099914550781, "volume": 328007}, {"epoch": 1781793900.0, "open": 299.69000244140625, "high": 300.57000732421875, "low": 299.6099853515625, "close": 300.3800048828125, "volume": 730320}, {"epoch": 1781794200.0, "open": 300.3900146484375, "high": 300.3900146484375, "low": 299.3800048828125, "close": 299.4599914550781, "volume": 1056478}, {"epoch": 1781794500.0, "open": 299.4599914550781, "high": 299.8599853515625, "low": 299.13018798828125, "close": 299.17999267578125, "volume": 786590}, {"epoch": 1781794800.0, "open": 299.2300109863281, "high": 299.2300109863281, "low": 297.92999267578125, "close": 298.2701110839844, "volume": 569476}, {"epoch": 1781795100.0, "open": 298.29998779296875, "high": 298.57000732421875, "low": 297.8699951171875, "close": 298.3500061035156, "volume": 400227}, {"epoch": 1781795400.0, "open": 298.3800048828125, "high": 298.7200012207031, "low": 298.0400085449219, "close": 298.07000732421875, "volume": 818621}, {"epoch": 1781795700.0, "open": 298.0899963378906, "high": 298.1600036621094, "low": 297.2300109863281, "close": 297.3699951171875, "volume": 801245}, {"epoch": 1781796000.0, "open": 297.3700866699219, "high": 297.5299987792969, "low": 297.1400146484375, "close": 297.2749938964844, "volume": 269364}, {"epoch": 1781796300.0, "open": 297.2900085449219, "high": 297.489990234375, "low": 296.9599914550781, "close": 297.1099853515625, "volume": 1410520}, {"epoch": 1781796600.0, "open": 297.1000061035156, "high": 297.2799987792969, "low": 296.8500061035156, "close": 297.17498779296875, "volume": 0}, {"epoch": 1781796900.0, "open": 297.1650085449219, "high": 297.3900146484375, "low": 296.75, "close": 297.0799865722656, "volume": 350700}, {"epoch": 1781797200.0, "open": 297.0400085449219, "high": 297.0400085449219, "low": 296.1400146484375, "close": 296.19000244140625, "volume": 371785}, {"epoch": 1781797500.0, "open": 296.19000244140625, "high": 296.32000732421875, "low": 295.95001220703125, "close": 296.2950134277344, "volume": 643314}, {"epoch": 1781797800.0, "open": 296.28009033203125, "high": 297.32000732421875, "low": 296.2699890136719, "close": 297.30999755859375, "volume": 374887}, {"epoch": 1781798100.0, "open": 297.29998779296875, "high": 297.6199951171875, "low": 297.260009765625, "close": 297.3800048828125, "volume": 589681}, {"epoch": 1781798400.0, "open": 297.3999938964844, "high": 297.7300109863281, "low": 296.94000244140625, "close": 297.0, "volume": 294726}, {"epoch": 1781798700.0, "open": 297.010009765625, "high": 297.2499084472656, "low": 296.739990234375, "close": 296.79998779296875, "volume": 265444}, {"epoch": 1781799000.0, "open": 296.82000732421875, "high": 297.1400146484375, "low": 296.69000244140625, "close": 297.0849914550781, "volume": 1188851}, {"epoch": 1781799300.0, "open": 297.0849914550781, "high": 297.4200134277344, "low": 296.94000244140625, "close": 297.3299865722656, "volume": 692055}, {"epoch": 1781799600.0, "open": 297.3399963378906, "high": 297.5198974609375, "low": 297.1400146484375, "close": 297.20001220703125, "volume": 156108}, {"epoch": 1781799900.0, "open": 297.19500732421875, "high": 297.5199890136719, "low": 297.0450134277344, "close": 297.489990234375, "volume": 209581}, {"epoch": 1781800200.0, "open": 297.4849853515625, "high": 297.489990234375, "low": 297.0306091308594, "close": 297.17999267578125, "volume": 230499}, {"epoch": 1781800500.0, "open": 297.1700134277344, "high": 297.69000244140625, "low": 297.1099853515625, "close": 297.6099853515625, "volume": 481667}, {"epoch": 1781800800.0, "open": 297.6050109863281, "high": 297.6199951171875, "low": 297.1300048828125, "close": 297.489990234375, "volume": 199108}, {"epoch": 1781801100.0, "open": 297.4949951171875, "high": 297.5, "low": 297.1300048828125, "close": 297.29998779296875, "volume": 288166}, {"epoch": 1781801400.0, "open": 297.2900085449219, "high": 297.29998779296875, "low": 297.0199890136719, "close": 297.05499267578125, "volume": 185066}, {"epoch": 1781801700.0, "open": 297.05999755859375, "high": 297.1600036621094, "low": 296.8399963378906, "close": 297.1300048828125, "volume": 219814}, {"epoch": 1781802000.0, "open": 297.1300048828125, "high": 297.92999267578125, "low": 297.0299987792969, "close": 297.864990234375, "volume": 231955}, {"epoch": 1781802300.0, "open": 297.875, "high": 298.10919189453125, "low": 297.79998779296875, "close": 297.82000732421875, "volume": 231546}, {"epoch": 1781802600.0, "open": 297.81500244140625, "high": 298.23199462890625, "low": 297.79998779296875, "close": 298.19500732421875, "volume": 152726}, {"epoch": 1781802900.0, "open": 298.20001220703125, "high": 298.3598937988281, "low": 298.05108642578125, "close": 298.2200012207031, "volume": 403388}, {"epoch": 1781803200.0, "open": 298.2300109863281, "high": 298.25, "low": 297.7200012207031, "close": 297.7200012207031, "volume": 532852}, {"epoch": 1781803500.0, "open": 297.7300109863281, "high": 297.8999938964844, "low": 297.5799865722656, "close": 297.82000732421875, "volume": 162842}, {"epoch": 1781803800.0, "open": 297.82501220703125, "high": 297.9849853515625, "low": 297.79180908203125, "close": 297.81988525390625, "volume": 273892}, {"epoch": 1781804100.0, "open": 297.80999755859375, "high": 297.9295959472656, "low": 297.6910095214844, "close": 297.79998779296875, "volume": 164403}, {"epoch": 1781804400.0, "open": 297.7900085449219, "high": 297.8299865722656, "low": 297.5, "close": 297.55999755859375, "volume": 175400}, {"epoch": 1781804700.0, "open": 297.56048583984375, "high": 297.7550048828125, "low": 297.3500061035156, "close": 297.69500732421875, "volume": 261735}, {"epoch": 1781805000.0, "open": 297.7149963378906, "high": 297.8599853515625, "low": 297.5799865722656, "close": 297.7349853515625, "volume": 130944}, {"epoch": 1781805300.0, "open": 297.739990234375, "high": 297.739990234375, "low": 297.3699951171875, "close": 297.5700988769531, "volume": 166187}, {"epoch": 1781805600.0, "open": 297.57501220703125, "high": 297.6199951171875, "low": 297.25, "close": 297.29998779296875, "volume": 162139}, {"epoch": 1781805900.0, "open": 297.2900085449219, "high": 297.489990234375, "low": 297.1499938964844, "close": 297.1600036621094, "volume": 192556}, {"epoch": 1781806200.0, "open": 297.1700134277344, "high": 297.6300048828125, "low": 297.0199890136719, "close": 297.55999755859375, "volume": 269497}, {"epoch": 1781806500.0, "open": 297.55999755859375, "high": 297.67999267578125, "low": 297.29998779296875, "close": 297.6000061035156, "volume": 153111}, {"epoch": 1781806800.0, "open": 297.5849914550781, "high": 297.6199951171875, "low": 297.2959899902344, "close": 297.3299865722656, "volume": 148988}, {"epoch": 1781807100.0, "open": 297.3200988769531, "high": 297.375, "low": 297.010009765625, "close": 297.1099853515625, "volume": 285861}, {"epoch": 1781807400.0, "open": 297.1400146484375, "high": 297.5799865722656, "low": 297.0600891113281, "close": 297.3900146484375, "volume": 386519}, {"epoch": 1781807700.0, "open": 297.3450012207031, "high": 297.6199951171875, "low": 297.31060791015625, "close": 297.3999938964844, "volume": 211191}, {"epoch": 1781808000.0, "open": 297.3800048828125, "high": 297.6499938964844, "low": 297.32000732421875, "close": 297.6449890136719, "volume": 153924}, {"epoch": 1781808300.0, "open": 297.6449890136719, "high": 298.05999755859375, "low": 297.6449890136719, "close": 297.9750061035156, "volume": 237922}, {"epoch": 1781808600.0, "open": 297.97100830078125, "high": 298.07000732421875, "low": 297.8800048828125, "close": 297.92999267578125, "volume": 186565}, {"epoch": 1781808900.0, "open": 297.9150085449219, "high": 297.989990234375, "low": 297.5899963378906, "close": 297.70001220703125, "volume": 165235}, {"epoch": 1781809200.0, "open": 297.7099914550781, "high": 297.760009765625, "low": 297.510009765625, "close": 297.5899963378906, "volume": 226339}, {"epoch": 1781809500.0, "open": 297.5849914550781, "high": 297.70001220703125, "low": 297.3399963378906, "close": 297.3399963378906, "volume": 34117}, {"epoch": 1781809800.0, "open": 297.3500061035156, "high": 297.3500061035156, "low": 297.05999755859375, "close": 297.1099853515625, "volume": 224844}, {"epoch": 1781810100.0, "open": 297.1099853515625, "high": 297.30999755859375, "low": 297.04010009765625, "close": 297.29998779296875, "volume": 482029}, {"epoch": 1781810400.0, "open": 297.2799987792969, "high": 297.4100036621094, "low": 297.1700134277344, "close": 297.2049865722656, "volume": 229810}, {"epoch": 1781810700.0, "open": 297.2099914550781, "high": 297.5, "low": 297.2004089355469, "close": 297.3800048828125, "volume": 234836}, {"epoch": 1781811000.0, "open": 297.3599853515625, "high": 297.3599853515625, "low": 297.05999755859375, "close": 297.2799987792969, "volume": 331765}, {"epoch": 1781811300.0, "open": 297.2699890136719, "high": 297.5400085449219, "low": 297.239990234375, "close": 297.4649963378906, "volume": 249239}, {"epoch": 1781811600.0, "open": 297.4800109863281, "high": 297.68499755859375, "low": 297.3500061035156, "close": 297.54998779296875, "volume": 314704}, {"epoch": 1781811900.0, "open": 297.5400085449219, "high": 297.8299865722656, "low": 297.5199890136719, "close": 297.6499938964844, "volume": 350930}, {"epoch": 1781812200.0, "open": 297.6600036621094, "high": 299.2394104003906, "low": 297.5201110839844, "close": 298.05999755859375, "volume": 1743167}, {"epoch": 1781812500.0, "open": 298.0, "high": 298.5400085449219, "low": 297.8800048828125, "close": 297.8900146484375, "volume": 2260716}, {"epoch": 1782135000.0, "open": 297.5, "high": 300.3299865722656, "low": 297.42999267578125, "close": 298.42999267578125, "volume": 2285365}, {"epoch": 1782135300.0, "open": 298.42999267578125, "high": 301.2799987792969, "low": 298.2699890136719, "close": 301.2101135253906, "volume": 844690}, {"epoch": 1782135600.0, "open": 301.24029541015625, "high": 301.9800109863281, "low": 300.84600830078125, "close": 301.5899963378906, "volume": 863434}, {"epoch": 1782135900.0, "open": 301.625, "high": 301.75, "low": 300.5899963378906, "close": 301.3699951171875, "volume": 541992}, {"epoch": 1782136200.0, "open": 301.3399963378906, "high": 302.05999755859375, "low": 300.57000732421875, "close": 301.2250061035156, "volume": 682478}, {"epoch": 1782136500.0, "open": 301.25, "high": 301.79998779296875, "low": 300.5, "close": 301.739990234375, "volume": 314352}, {"epoch": 1782136800.0, "open": 301.7449951171875, "high": 302.0899963378906, "low": 301.6400146484375, "close": 301.8399963378906, "volume": 573442}, {"epoch": 1782137100.0, "open": 301.8399963378906, "high": 302.4200134277344, "low": 301.5199890136719, "close": 302.3699951171875, "volume": 426371}, {"epoch": 1782137400.0, "open": 302.3500061035156, "high": 302.4100036621094, "low": 301.7340087890625, "close": 301.8500061035156, "volume": 926062}, {"epoch": 1782137700.0, "open": 301.8500061035156, "high": 301.92498779296875, "low": 300.8800048828125, "close": 301.5098876953125, "volume": 451777}, {"epoch": 1782138000.0, "open": 301.4949951171875, "high": 301.5400085449219, "low": 301.0199890136719, "close": 301.30499267578125, "volume": 366888}, {"epoch": 1782138300.0, "open": 301.2900085449219, "high": 301.6499938964844, "low": 301.05999755859375, "close": 301.20001220703125, "volume": 391916}, {"epoch": 1782138600.0, "open": 301.2099914550781, "high": 301.2300109863281, "low": 300.43499755859375, "close": 300.4800109863281, "volume": 545103}, {"epoch": 1782138900.0, "open": 300.4599914550781, "high": 300.4750061035156, "low": 299.55999755859375, "close": 300.0400085449219, "volume": 484821}, {"epoch": 1782139200.0, "open": 300.05999755859375, "high": 300.3080139160156, "low": 299.6199951171875, "close": 299.70001220703125, "volume": 306676}, {"epoch": 1782139500.0, "open": 299.6700134277344, "high": 300.1300048828125, "low": 299.6400146484375, "close": 299.8450012207031, "volume": 346071}, {"epoch": 1782139800.0, "open": 299.8299865722656, "high": 299.9700012207031, "low": 299.3699951171875, "close": 299.6400146484375, "volume": 315633}, {"epoch": 1782140100.0, "open": 299.635009765625, "high": 300.07000732421875, "low": 299.4100036621094, "close": 299.79998779296875, "volume": 283247}, {"epoch": 1782140400.0, "open": 299.80499267578125, "high": 300.389892578125, "low": 299.760009765625, "close": 299.82000732421875, "volume": 356466}, {"epoch": 1782140700.0, "open": 299.8299865722656, "high": 299.8599853515625, "low": 299.0350036621094, "close": 299.18499755859375, "volume": 293300}, {"epoch": 1782141000.0, "open": 299.18499755859375, "high": 300.2300109863281, "low": 299.1499938964844, "close": 300.1098937988281, "volume": 291313}, {"epoch": 1782141300.0, "open": 300.0950012207031, "high": 300.235107421875, "low": 299.7900085449219, "close": 299.94500732421875, "volume": 385350}, {"epoch": 1782141600.0, "open": 299.94000244140625, "high": 300.1400146484375, "low": 299.20001220703125, "close": 300.125, "volume": 462169}, {"epoch": 1782141900.0, "open": 300.125, "high": 300.2300109863281, "low": 299.6000061035156, "close": 299.94000244140625, "volume": 241497}, {"epoch": 1782142200.0, "open": 299.94000244140625, "high": 300.3099060058594, "low": 299.75, "close": 300.1700134277344, "volume": 265292}, {"epoch": 1782142500.0, "open": 300.20989990234375, "high": 300.7398986816406, "low": 300.18499755859375, "close": 300.7149963378906, "volume": 201457}, {"epoch": 1782142800.0, "open": 300.7200012207031, "high": 301.260009765625, "low": 300.70001220703125, "close": 301.04998779296875, "volume": 305190}, {"epoch": 1782143100.0, "open": 301.0899963378906, "high": 301.4299011230469, "low": 300.260009765625, "close": 300.29998779296875, "volume": 271094}, {"epoch": 1782143400.0, "open": 300.3599853515625, "high": 300.7377014160156, "low": 300.3500061035156, "close": 300.5799865722656, "volume": 192750}, {"epoch": 1782143700.0, "open": 300.6000061035156, "high": 300.92999267578125, "low": 300.5299987792969, "close": 300.8900146484375, "volume": 247584}, {"epoch": 1782144000.0, "open": 300.885009765625, "high": 300.9590148925781, "low": 300.32000732421875, "close": 300.4068908691406, "volume": 250177}, {"epoch": 1782144300.0, "open": 300.3949890136719, "high": 300.92999267578125, "low": 300.3800048828125, "close": 300.760009765625, "volume": 305104}, {"epoch": 1782144600.0, "open": 300.760009765625, "high": 300.8500061035156, "low": 300.5, "close": 300.7903137207031, "volume": 255846}, {"epoch": 1782144900.0, "open": 300.7900085449219, "high": 300.82000732421875, "low": 300.5199890136719, "close": 300.69500732421875, "volume": 178816}, {"epoch": 1782145200.0, "open": 300.70001220703125, "high": 300.95001220703125, "low": 300.42999267578125, "close": 300.510009765625, "volume": 273287}, {"epoch": 1782145500.0, "open": 300.5177001953125, "high": 300.6199951171875, "low": 300.1499938964844, "close": 300.5398864746094, "volume": 204625}, {"epoch": 1782145800.0, "open": 300.5199890136719, "high": 300.67999267578125, "low": 300.2699890136719, "close": 300.3299865722656, "volume": 194652}, {"epoch": 1782146100.0, "open": 300.3299865722656, "high": 300.3999938964844, "low": 300.114990234375, "close": 300.17999267578125, "volume": 216044}, {"epoch": 1782146400.0, "open": 300.19000244140625, "high": 300.3900146484375, "low": 299.9100036621094, "close": 300.17498779296875, "volume": 405209}, {"epoch": 1782146700.0, "open": 300.19000244140625, "high": 300.4700012207031, "low": 300.0199890136719, "close": 300.2499084472656, "volume": 273528}, {"epoch": 1782147000.0, "open": 300.2200012207031, "high": 300.4800109863281, "low": 300.090087890625, "close": 300.2099914550781, "volume": 194652}, {"epoch": 1782147300.0, "open": 300.2099914550781, "high": 300.3500061035156, "low": 299.9150085449219, "close": 299.9200134277344, "volume": 190077}, {"epoch": 1782147600.0, "open": 299.92999267578125, "high": 300.04998779296875, "low": 299.65008544921875, "close": 299.93499755859375, "volume": 219393}, {"epoch": 1782147900.0, "open": 299.94000244140625, "high": 299.9599914550781, "low": 299.56500244140625, "close": 299.67999267578125, "volume": 180689}, {"epoch": 1782148200.0, "open": 299.69000244140625, "high": 299.7699890136719, "low": 299.45001220703125, "close": 299.6050109863281, "volume": 252227}, {"epoch": 1782148500.0, "open": 299.6199951171875, "high": 299.89990234375, "low": 299.6199951171875, "close": 299.8599853515625, "volume": 156955}, {"epoch": 1782148800.0, "open": 299.875, "high": 300.1300048828125, "low": 299.80999755859375, "close": 299.8999938964844, "volume": 195575}, {"epoch": 1782149100.0, "open": 299.8949890136719, "high": 299.95001220703125, "low": 299.67498779296875, "close": 299.80999755859375, "volume": 211788}, {"epoch": 1782149400.0, "open": 299.81500244140625, "high": 299.82000732421875, "low": 299.5199890136719, "close": 299.6700134277344, "volume": 153066}, {"epoch": 1782149700.0, "open": 299.6600036621094, "high": 299.6600036621094, "low": 299.30499267578125, "close": 299.5199890136719, "volume": 206940}, {"epoch": 1782150000.0, "open": 299.5, "high": 299.8599853515625, "low": 299.25, "close": 299.3301086425781, "volume": 323656}, {"epoch": 1782150300.0, "open": 299.3299865722656, "high": 299.7300109863281, "low": 299.25, "close": 299.6300048828125, "volume": 220110}, {"epoch": 1782150600.0, "open": 299.6199951171875, "high": 299.81988525390625, "low": 299.32501220703125, "close": 299.3550109863281, "volume": 167635}, {"epoch": 1782150900.0, "open": 299.3399963378906, "high": 299.54998779296875, "low": 299.30499267578125, "close": 299.30999755859375, "volume": 164408}, {"epoch": 1782151200.0, "open": 299.30999755859375, "high": 299.3265075683594, "low": 298.6600036621094, "close": 298.70001220703125, "volume": 259698}, {"epoch": 1782151500.0, "open": 298.67999267578125, "high": 298.8500061035156, "low": 298.6099853515625, "close": 298.75, "volume": 191438}, {"epoch": 1782151800.0, "open": 298.75, "high": 298.760009765625, "low": 298.5830078125, "close": 298.69500732421875, "volume": 174668}, {"epoch": 1782152100.0, "open": 298.697509765625, "high": 298.9750061035156, "low": 298.6300048828125, "close": 298.864990234375, "volume": 209707}, {"epoch": 1782152400.0, "open": 298.8599853515625, "high": 299.20001220703125, "low": 298.8599853515625, "close": 298.94720458984375, "volume": 243399}, {"epoch": 1782152700.0, "open": 298.95001220703125, "high": 299.010009765625, "low": 298.8299865722656, "close": 298.9200134277344, "volume": 140666}, {"epoch": 1782153000.0, "open": 298.9200134277344, "high": 299.0199890136719, "low": 298.590087890625, "close": 298.7449951171875, "volume": 176685}, {"epoch": 1782153300.0, "open": 298.760009765625, "high": 298.92999267578125, "low": 298.7099914550781, "close": 298.8399963378906, "volume": 149654}, {"epoch": 1782153600.0, "open": 298.8500061035156, "high": 299.0400085449219, "low": 298.82000732421875, "close": 298.8599853515625, "volume": 176342}, {"epoch": 1782153900.0, "open": 298.875, "high": 299.239990234375, "low": 298.8399963378906, "close": 299.1050109863281, "volume": 212928}, {"epoch": 1782154200.0, "open": 299.1050109863281, "high": 299.1401062011719, "low": 298.660400390625, "close": 298.8999938964844, "volume": 186192}, {"epoch": 1782154500.0, "open": 298.8800048828125, "high": 299.1000061035156, "low": 298.8399963378906, "close": 299.07000732421875, "volume": 179270}, {"epoch": 1782154800.0, "open": 299.0899963378906, "high": 299.3399963378906, "low": 298.92999267578125, "close": 299.1499938964844, "volume": 274850}, {"epoch": 1782155100.0, "open": 299.1600036621094, "high": 299.2001037597656, "low": 298.885009765625, "close": 299.0299987792969, "volume": 390693}, {"epoch": 1782155400.0, "open": 299.0299987792969, "high": 299.239990234375, "low": 298.9700012207031, "close": 299.0899963378906, "volume": 214477}, {"epoch": 1782155700.0, "open": 299.0899963378906, "high": 299.2699890136719, "low": 299.0799865722656, "close": 299.1000061035156, "volume": 330840}, {"epoch": 1782156000.0, "open": 299.114990234375, "high": 299.29998779296875, "low": 298.9100036621094, "close": 299.0450134277344, "volume": 373072}, {"epoch": 1782156300.0, "open": 299.05999755859375, "high": 299.1300048828125, "low": 298.9599914550781, "close": 299.05999755859375, "volume": 261455}, {"epoch": 1782156600.0, "open": 299.05999755859375, "high": 299.0899963378906, "low": 297.44000244140625, "close": 297.69000244140625, "volume": 843724}, {"epoch": 1782156900.0, "open": 297.67498779296875, "high": 297.70001220703125, "low": 296.9599914550781, "close": 297.1600036621094, "volume": 673681}, {"epoch": 1782157200.0, "open": 297.1600036621094, "high": 297.32000732421875, "low": 296.989990234375, "close": 297.2699890136719, "volume": 598907}, {"epoch": 1782157500.0, "open": 297.2799987792969, "high": 297.5400085449219, "low": 296.8399963378906, "close": 297.0849914550781, "volume": 619667}, {"epoch": 1782157800.0, "open": 297.1099853515625, "high": 297.6099853515625, "low": 296.9100036621094, "close": 297.55499267578125, "volume": 1002574}, {"epoch": 1782158100.0, "open": 297.57501220703125, "high": 297.67999267578125, "low": 296.7900085449219, "close": 296.7900085449219, "volume": 2360538}, {"epoch": 1782221400.0, "open": 297.5379943847656, "high": 298.30999755859375, "low": 295.17999267578125, "close": 297.04998779296875, "volume": 2685201}, {"epoch": 1782221700.0, "open": 296.9800109863281, "high": 299.19000244140625, "low": 296.20001220703125, "close": 298.9150085449219, "volume": 869374}, {"epoch": 1782222000.0, "open": 298.9324951171875, "high": 300.5776062011719, "low": 298.7300109863281, "close": 300.510009765625, "volume": 857998}, {"epoch": 1782222300.0, "open": 300.4700012207031, "high": 301.6400146484375, "low": 300.1700134277344, "close": 300.4049987792969, "volume": 785038}, {"epoch": 1782222600.0, "open": 300.3599853515625, "high": 300.5299987792969, "low": 298.1600036621094, "close": 298.3699951171875, "volume": 737700}, {"epoch": 1782222900.0, "open": 298.3599853515625, "high": 299.3299865722656, "low": 298.15850830078125, "close": 299.1099853515625, "volume": 454203}, {"epoch": 1782223200.0, "open": 299.0849914550781, "high": 299.6499938964844, "low": 298.7950134277344, "close": 299.385009765625, "volume": 434804}, {"epoch": 1782223500.0, "open": 299.3500061035156, "high": 299.75, "low": 298.8599853515625, "close": 299.6300048828125, "volume": 563973}, {"epoch": 1782223800.0, "open": 299.6300048828125, "high": 299.989990234375, "low": 299.3800048828125, "close": 299.42999267578125, "volume": 475005}, {"epoch": 1782224100.0, "open": 299.42999267578125, "high": 299.8699951171875, "low": 299.30999755859375, "close": 299.5400085449219, "volume": 383251}, {"epoch": 1782224400.0, "open": 299.5199890136719, "high": 299.7099914550781, "low": 298.8999938964844, "close": 299.5799865722656, "volume": 477630}, {"epoch": 1782224700.0, "open": 299.54998779296875, "high": 300.55999755859375, "low": 299.4200134277344, "close": 300.506591796875, "volume": 536304}, {"epoch": 1782225000.0, "open": 300.5199890136719, "high": 300.8800048828125, "low": 300.010009765625, "close": 300.4200134277344, "volume": 512859}, {"epoch": 1782225300.0, "open": 300.44000244140625, "high": 300.5, "low": 299.60430908203125, "close": 299.6499938964844, "volume": 400633}, {"epoch": 1782225600.0, "open": 299.6499938964844, "high": 300.4599914550781, "low": 299.55999755859375, "close": 300.3500061035156, "volume": 297843}, {"epoch": 1782225900.0, "open": 300.3699951171875, "high": 300.4800109863281, "low": 299.8450012207031, "close": 300.0398864746094, "volume": 373941}, {"epoch": 1782226200.0, "open": 300.010009765625, "high": 300.239990234375, "low": 299.614990234375, "close": 300.1000061035156, "volume": 334302}, {"epoch": 1782226500.0, "open": 300.0950012207031, "high": 300.2499084472656, "low": 299.5400085449219, "close": 300.0899963378906, "volume": 358393}, {"epoch": 1782226800.0, "open": 300.0899963378906, "high": 300.32000732421875, "low": 299.45001220703125, "close": 299.7300109863281, "volume": 370644}, {"epoch": 1782227100.0, "open": 299.7200012207031, "high": 299.739990234375, "low": 299.2200012207031, "close": 299.70001220703125, "volume": 377127}, {"epoch": 1782227400.0, "open": 299.69000244140625, "high": 299.9800109863281, "low": 299.1000061035156, "close": 299.1477966308594, "volume": 402198}, {"epoch": 1782227700.0, "open": 299.1300048828125, "high": 299.2900085449219, "low": 298.5199890136719, "close": 298.6465148925781, "volume": 357196}, {"epoch": 1782228000.0, "open": 298.6700134277344, "high": 298.9700012207031, "low": 298.5201110839844, "close": 298.6600036621094, "volume": 317002}, {"epoch": 1782228300.0, "open": 298.625, "high": 298.80999755859375, "low": 298.3999938964844, "close": 298.54998779296875, "volume": 386468}, {"epoch": 1782228600.0, "open": 298.5450134277344, "high": 298.5899963378906, "low": 297.8299865722656, "close": 297.8999938964844, "volume": 405688}, {"epoch": 1782228900.0, "open": 297.95001220703125, "high": 298.2799987792969, "low": 297.3500061035156, "close": 297.55999755859375, "volume": 375897}, {"epoch": 1782229200.0, "open": 297.57000732421875, "high": 297.8900146484375, "low": 297.5, "close": 297.760009765625, "volume": 301152}, {"epoch": 1782229500.0, "open": 297.7699890136719, "high": 297.9800109863281, "low": 297.4599914550781, "close": 297.8699951171875, "volume": 240707}, {"epoch": 1782229800.0, "open": 297.875, "high": 298.0950012207031, "low": 297.7300109863281, "close": 297.9150085449219, "volume": 409022}, {"epoch": 1782230100.0, "open": 297.9150085449219, "high": 298.2349853515625, "low": 297.70001220703125, "close": 298.06500244140625, "volume": 269370}, {"epoch": 1782230400.0, "open": 298.07000732421875, "high": 298.3999938964844, "low": 297.95001220703125, "close": 298.3351135253906, "volume": 354356}, {"epoch": 1782230700.0, "open": 298.3399963378906, "high": 298.6300048828125, "low": 298.30999755859375, "close": 298.5439147949219, "volume": 251455}, {"epoch": 1782231000.0, "open": 298.55999755859375, "high": 298.7699890136719, "low": 298.1300048828125, "close": 298.17999267578125, "volume": 294714}, {"epoch": 1782231300.0, "open": 298.19000244140625, "high": 298.885009765625, "low": 298.19000244140625, "close": 298.8599853515625, "volume": 287754}, {"epoch": 1782231600.0, "open": 298.8500061035156, "high": 298.8500061035156, "low": 298.5199890136719, "close": 298.67999267578125, "volume": 328618}, {"epoch": 1782231900.0, "open": 298.67999267578125, "high": 298.875, "low": 298.5199890136719, "close": 298.6199035644531, "volume": 313397}, {"epoch": 1782232200.0, "open": 298.5849914550781, "high": 298.6600036621094, "low": 298.19500732421875, "close": 298.45001220703125, "volume": 269817}, {"epoch": 1782232500.0, "open": 298.45001220703125, "high": 298.6400146484375, "low": 298.2300109863281, "close": 298.635009765625, "volume": 231490}, {"epoch": 1782232800.0, "open": 298.635009765625, "high": 298.8500061035156, "low": 298.54998779296875, "close": 298.5799865722656, "volume": 292888}, {"epoch": 1782233100.0, "open": 298.5799865722656, "high": 298.8599853515625, "low": 298.4200134277344, "close": 298.67999267578125, "volume": 278635}, {"epoch": 1782233400.0, "open": 298.68499755859375, "high": 298.9800109863281, "low": 298.5, "close": 298.8900146484375, "volume": 358271}, {"epoch": 1782233700.0, "open": 298.8999938964844, "high": 299.2799987792969, "low": 298.8500061035156, "close": 298.989990234375, "volume": 286158}, {"epoch": 1782234000.0, "open": 299.010009765625, "high": 299.010009765625, "low": 297.8800048828125, "close": 298.0249938964844, "volume": 409947}, {"epoch": 1782234300.0, "open": 298.0299987792969, "high": 298.7699890136719, "low": 298.02410888671875, "close": 298.760009765625, "volume": 272427}, {"epoch": 1782234600.0, "open": 298.7699890136719, "high": 299.3949890136719, "low": 298.7650146484375, "close": 299.0400085449219, "volume": 256080}, {"epoch": 1782234900.0, "open": 299.04998779296875, "high": 299.1199951171875, "low": 298.9100036621094, "close": 299.0, "volume": 195497}, {"epoch": 1782235200.0, "open": 299.010009765625, "high": 299.3900146484375, "low": 299.0050048828125, "close": 299.32501220703125, "volume": 252659}, {"epoch": 1782235500.0, "open": 299.32501220703125, "high": 299.4700012207031, "low": 299.20001220703125, "close": 299.3949890136719, "volume": 260809}, {"epoch": 1782235800.0, "open": 299.3949890136719, "high": 299.7300109863281, "low": 299.2799987792969, "close": 299.69000244140625, "volume": 294987}, {"epoch": 1782236100.0, "open": 299.70001220703125, "high": 299.79998779296875, "low": 299.2449951171875, "close": 299.43499755859375, "volume": 252258}, {"epoch": 1782236400.0, "open": 299.42498779296875, "high": 299.4599914550781, "low": 299.0400085449219, "close": 299.3399963378906, "volume": 215888}, {"epoch": 1782236700.0, "open": 299.3299865722656, "high": 300.0849914550781, "low": 299.2900085449219, "close": 299.9150085449219, "volume": 374641}, {"epoch": 1782237000.0, "open": 299.9150085449219, "high": 299.94000244140625, "low": 299.3299865722656, "close": 299.3500061035156, "volume": 305353}, {"epoch": 1782237300.0, "open": 299.3500061035156, "high": 299.46990966796875, "low": 298.8900146484375, "close": 298.9599914550781, "volume": 237533}, {"epoch": 1782237600.0, "open": 298.989990234375, "high": 299.3800048828125, "low": 298.8900146484375, "close": 298.9599914550781, "volume": 281170}, {"epoch": 1782237900.0, "open": 298.9700012207031, "high": 299.0199890136719, "low": 298.55999755859375, "close": 298.739990234375, "volume": 275459}, {"epoch": 1782238200.0, "open": 298.739990234375, "high": 298.86981201171875, "low": 298.45001220703125, "close": 298.760009765625, "volume": 248897}, {"epoch": 1782238500.0, "open": 298.7699890136719, "high": 298.8599853515625, "low": 298.3399963378906, "close": 298.510009765625, "volume": 285090}, {"epoch": 1782238800.0, "open": 298.5050048828125, "high": 298.8599853515625, "low": 298.4049987792969, "close": 298.5199890136719, "volume": 291885}, {"epoch": 1782239100.0, "open": 298.5400085449219, "high": 298.6300048828125, "low": 298.3699951171875, "close": 298.5199890136719, "volume": 284912}, {"epoch": 1782239400.0, "open": 298.5249938964844, "high": 298.635009765625, "low": 298.1449890136719, "close": 298.2300109863281, "volume": 335772}, {"epoch": 1782239700.0, "open": 298.2250061035156, "high": 298.2803955078125, "low": 297.7250061035156, "close": 298.05010986328125, "volume": 294721}, {"epoch": 1782240000.0, "open": 298.07000732421875, "high": 298.1000061035156, "low": 297.75, "close": 297.8999938964844, "volume": 285186}, {"epoch": 1782240300.0, "open": 297.8949890136719, "high": 298.0299987792969, "low": 297.7349853515625, "close": 297.8999938964844, "volume": 374748}, {"epoch": 1782240600.0, "open": 297.9100036621094, "high": 298.2200012207031, "low": 297.45001220703125, "close": 297.6099853515625, "volume": 341540}, {"epoch": 1782240900.0, "open": 297.6199951171875, "high": 297.8349914550781, "low": 297.4750061035156, "close": 297.5199890136719, "volume": 358820}, {"epoch": 1782241200.0, "open": 297.5199890136719, "high": 298.86761474609375, "low": 297.3999938964844, "close": 297.5799865722656, "volume": 387228}, {"epoch": 1782241500.0, "open": 297.6099853515625, "high": 297.8800048828125, "low": 296.8900146484375, "close": 297.17498779296875, "volume": 429779}, {"epoch": 1782241800.0, "open": 297.17999267578125, "high": 297.5799865722656, "low": 296.7900085449219, "close": 296.8689880371094, "volume": 463500}, {"epoch": 1782242100.0, "open": 296.8599853515625, "high": 296.8800048828125, "low": 295.30999755859375, "close": 295.6700134277344, "volume": 791202}, {"epoch": 1782242400.0, "open": 295.6400146484375, "high": 296.239990234375, "low": 295.6099853515625, "close": 296.2349853515625, "volume": 541932}, {"epoch": 1782242700.0, "open": 296.239990234375, "high": 296.4800109863281, "low": 295.8399963378906, "close": 295.840087890625, "volume": 492539}, {"epoch": 1782243000.0, "open": 295.8399963378906, "high": 296.0400085449219, "low": 295.6199951171875, "close": 296.010009765625, "volume": 421545}, {"epoch": 1782243300.0, "open": 296.0199890136719, "high": 296.4200134277344, "low": 295.7099914550781, "close": 296.11749267578125, "volume": 502012}, {"epoch": 1782243600.0, "open": 296.1099853515625, "high": 296.2099914550781, "low": 295.4849853515625, "close": 295.70001220703125, "volume": 709819}, {"epoch": 1782243900.0, "open": 295.7300109863281, "high": 296.1400146484375, "low": 295.45001220703125, "close": 295.8330078125, "volume": 743259}, {"epoch": 1782244200.0, "open": 295.8500061035156, "high": 296.5, "low": 295.7900085449219, "close": 296.4200134277344, "volume": 1110473}, {"epoch": 1782244500.0, "open": 296.42999267578125, "high": 296.4599914550781, "low": 294.2120056152344, "close": 294.2799987792969, "volume": 4318239}, {"epoch": 1782307800.0, "open": 295.375, "high": 296.4599914550781, "low": 293.20001220703125, "close": 295.7300109863281, "volume": 1881418}, {"epoch": 1782308100.0, "open": 295.7200012207031, "high": 296.1499938964844, "low": 294.8299865722656, "close": 295.44500732421875, "volume": 427621}, {"epoch": 1782308400.0, "open": 295.4700012207031, "high": 295.989990234375, "low": 294.9800109863281, "close": 295.67999267578125, "volume": 572260}, {"epoch": 1782308700.0, "open": 295.69000244140625, "high": 296.2799987792969, "low": 295.3500061035156, "close": 295.82501220703125, "volume": 438433}, {"epoch": 1782309000.0, "open": 295.82000732421875, "high": 296.2300109863281, "low": 295.55999755859375, "close": 296.0801086425781, "volume": 413123}, {"epoch": 1782309300.0, "open": 296.07000732421875, "high": 296.072509765625, "low": 294.4800109863281, "close": 294.7699890136719, "volume": 461018}, {"epoch": 1782309600.0, "open": 294.7200012207031, "high": 295.0, "low": 294.2300109863281, "close": 294.5899963378906, "volume": 345954}, {"epoch": 1782309900.0, "open": 294.5849914550781, "high": 294.94000244140625, "low": 294.44000244140625, "close": 294.79998779296875, "volume": 272847}, {"epoch": 1782310200.0, "open": 294.7850036621094, "high": 295.5, "low": 294.55499267578125, "close": 294.875, "volume": 414204}, {"epoch": 1782310500.0, "open": 294.8999938964844, "high": 295.489990234375, "low": 294.7250061035156, "close": 295.29998779296875, "volume": 297171}, {"epoch": 1782310800.0, "open": 295.2699890136719, "high": 296.20941162109375, "low": 295.1099853515625, "close": 295.56500244140625, "volume": 341931}, {"epoch": 1782311100.0, "open": 295.56500244140625, "high": 295.82000732421875, "low": 295.2200012207031, "close": 295.4649963378906, "volume": 252467}, {"epoch": 1782311400.0, "open": 295.4599914550781, "high": 295.8099060058594, "low": 295.3399963378906, "close": 295.6000061035156, "volume": 272661}, {"epoch": 1782311700.0, "open": 295.6000061035156, "high": 295.6899108886719, "low": 295.1099853515625, "close": 295.54998779296875, "volume": 308197}, {"epoch": 1782312000.0, "open": 295.54998779296875, "high": 296.6000061035156, "low": 295.54998779296875, "close": 296.4849853515625, "volume": 255673}, {"epoch": 1782312300.0, "open": 296.4700012207031, "high": 297.0799865722656, "low": 296.45001220703125, "close": 296.9049987792969, "volume": 341116}, {"epoch": 1782312600.0, "open": 296.9200134277344, "high": 297.260009765625, "low": 296.8599853515625, "close": 296.8999938964844, "volume": 307796}, {"epoch": 1782312900.0, "open": 296.9049987792969, "high": 297.1400146484375, "low": 296.8599853515625, "close": 297.0799865722656, "volume": 279283}, {"epoch": 1782313200.0, "open": 297.1099853515625, "high": 297.510009765625, "low": 296.8500061035156, "close": 297.2349853515625, "volume": 327864}, {"epoch": 1782313500.0, "open": 297.2349853515625, "high": 297.42999267578125, "low": 296.7300109863281, "close": 296.7449951171875, "volume": 317141}, {"epoch": 1782313800.0, "open": 296.75, "high": 297.5899963378906, "low": 296.6499938964844, "close": 297.4800109863281, "volume": 324439}, {"epoch": 1782314100.0, "open": 297.4700012207031, "high": 297.6000061035156, "low": 297.1129150390625, "close": 297.4849853515625, "volume": 198761}, {"epoch": 1782314400.0, "open": 297.4849853515625, "high": 298.3500061035156, "low": 297.2300109863281, "close": 297.93499755859375, "volume": 532365}, {"epoch": 1782314700.0, "open": 297.93499755859375, "high": 298.8800048828125, "low": 297.510009765625, "close": 298.7850036621094, "volume": 636118}, {"epoch": 1782315000.0, "open": 298.760009765625, "high": 299.25, "low": 298.7099914550781, "close": 299.0799865722656, "volume": 493137}, {"epoch": 1782315300.0, "open": 299.0882873535156, "high": 299.5, "low": 298.92999267578125, "close": 299.07000732421875, "volume": 304970}, {"epoch": 1782315600.0, "open": 299.05999755859375, "high": 299.1199951171875, "low": 298.1610107421875, "close": 298.1700134277344, "volume": 519323}, {"epoch": 1782315900.0, "open": 298.2300109863281, "high": 299.08990478515625, "low": 298.0799865722656, "close": 299.0050048828125, "volume": 301524}, {"epoch": 1782316200.0, "open": 299.0199890136719, "high": 299.6600036621094, "low": 299.0199890136719, "close": 299.4549865722656, "volume": 341932}, {"epoch": 1782316500.0, "open": 299.44500732421875, "high": 299.70001220703125, "low": 299.2799987792969, "close": 299.4750061035156, "volume": 212454}, {"epoch": 1782316800.0, "open": 299.4649963378906, "high": 299.5, "low": 298.7699890136719, "close": 298.8999938964844, "volume": 258079}, {"epoch": 1782317100.0, "open": 298.8999938964844, "high": 299.0400085449219, "low": 298.7200012207031, "close": 298.8599853515625, "volume": 217141}, {"epoch": 1782317400.0, "open": 298.8450012207031, "high": 299.04998779296875, "low": 298.5899963378906, "close": 298.7300109863281, "volume": 302119}, {"epoch": 1782317700.0, "open": 298.75, "high": 298.8999938964844, "low": 298.3699951171875, "close": 298.3703918457031, "volume": 236272}, {"epoch": 1782318000.0, "open": 298.3699951171875, "high": 298.42999267578125, "low": 297.839599609375, "close": 298.3550109863281, "volume": 400770}, {"epoch": 1782318300.0, "open": 298.3399963378906, "high": 298.3399963378906, "low": 298.0002136230469, "close": 298.07000732421875, "volume": 203751}, {"epoch": 1782318600.0, "open": 298.04998779296875, "high": 298.04998779296875, "low": 297.5199890136719, "close": 297.7300109863281, "volume": 291456}, {"epoch": 1782318900.0, "open": 297.7301025390625, "high": 297.9649963378906, "low": 297.3200988769531, "close": 297.55999755859375, "volume": 287013}, {"epoch": 1782319200.0, "open": 297.5400085449219, "high": 297.6700134277344, "low": 297.2200012207031, "close": 297.31500244140625, "volume": 298306}, {"epoch": 1782319500.0, "open": 297.2749938964844, "high": 297.53179931640625, "low": 297.0108947753906, "close": 297.4700012207031, "volume": 242328}, {"epoch": 1782319800.0, "open": 297.44000244140625, "high": 297.6000061035156, "low": 297.0, "close": 297.0199890136719, "volume": 245001}, {"epoch": 1782320100.0, "open": 297.0199890136719, "high": 297.45001220703125, "low": 296.8699951171875, "close": 297.3450012207031, "volume": 293613}, {"epoch": 1782320400.0, "open": 297.3599853515625, "high": 297.385009765625, "low": 297.1499938964844, "close": 297.32501220703125, "volume": 168902}, {"epoch": 1782320700.0, "open": 297.31500244140625, "high": 297.31500244140625, "low": 296.3121032714844, "close": 296.45001220703125, "volume": 264746}, {"epoch": 1782321000.0, "open": 296.45001220703125, "high": 296.8500061035156, "low": 296.45001220703125, "close": 296.6099853515625, "volume": 243818}, {"epoch": 1782321300.0, "open": 296.6099853515625, "high": 296.6600036621094, "low": 295.94000244140625, "close": 296.29998779296875, "volume": 351825}, {"epoch": 1782321600.0, "open": 296.29998779296875, "high": 296.4798889160156, "low": 295.79998779296875, "close": 296.3699951171875, "volume": 338871}, {"epoch": 1782321900.0, "open": 296.375, "high": 296.94000244140625, "low": 296.17999267578125, "close": 296.4200134277344, "volume": 378009}, {"epoch": 1782322200.0, "open": 296.4100036621094, "high": 296.6300048828125, "low": 295.8399963378906, "close": 296.3349914550781, "volume": 326139}, {"epoch": 1782322500.0, "open": 296.3450012207031, "high": 296.8644104003906, "low": 296.32000732421875, "close": 296.6099853515625, "volume": 473940}, {"epoch": 1782322800.0, "open": 296.626708984375, "high": 296.7049865722656, "low": 295.760009765625, "close": 295.8999938964844, "volume": 274679}, {"epoch": 1782323100.0, "open": 295.9161071777344, "high": 296.32000732421875, "low": 295.7699890136719, "close": 296.2099914550781, "volume": 283147}, {"epoch": 1782323400.0, "open": 296.19000244140625, "high": 296.29998779296875, "low": 295.92999267578125, "close": 296.0400085449219, "volume": 261850}, {"epoch": 1782323700.0, "open": 296.04998779296875, "high": 296.24249267578125, "low": 295.5899963378906, "close": 295.6099853515625, "volume": 275578}, {"epoch": 1782324000.0, "open": 295.6099853515625, "high": 296.4700012207031, "low": 295.590087890625, "close": 296.30999755859375, "volume": 419590}, {"epoch": 1782324300.0, "open": 296.2950134277344, "high": 296.4949951171875, "low": 295.8399963378906, "close": 295.93499755859375, "volume": 391655}, {"epoch": 1782324600.0, "open": 295.92999267578125, "high": 295.9399108886719, "low": 295.3800048828125, "close": 295.57000732421875, "volume": 306178}, {"epoch": 1782324900.0, "open": 295.57000732421875, "high": 296.2099914550781, "low": 295.56500244140625, "close": 295.92999267578125, "volume": 329000}, {"epoch": 1782325200.0, "open": 295.9200134277344, "high": 296.1099853515625, "low": 295.7799987792969, "close": 296.1099853515625, "volume": 256033}, {"epoch": 1782325500.0, "open": 296.1099853515625, "high": 296.2099914550781, "low": 295.8500061035156, "close": 296.0, "volume": 371324}, {"epoch": 1782325800.0, "open": 296.0, "high": 296.17999267578125, "low": 295.8900146484375, "close": 296.125, "volume": 395006}, {"epoch": 1782326100.0, "open": 296.1000061035156, "high": 296.1099853515625, "low": 295.2900085449219, "close": 295.42999267578125, "volume": 418865}, {"epoch": 1782326400.0, "open": 295.43499755859375, "high": 295.5299987792969, "low": 294.8800048828125, "close": 295.20001220703125, "volume": 494502}, {"epoch": 1782326700.0, "open": 295.19000244140625, "high": 295.25, "low": 294.4200134277344, "close": 294.5299987792969, "volume": 486710}, {"epoch": 1782327000.0, "open": 294.5350036621094, "high": 294.57501220703125, "low": 294.1600036621094, "close": 294.45001220703125, "volume": 538740}, {"epoch": 1782327300.0, "open": 294.45001220703125, "high": 295.19000244140625, "low": 294.26611328125, "close": 295.1700134277344, "volume": 523658}, {"epoch": 1782327600.0, "open": 295.19000244140625, "high": 295.42999267578125, "low": 294.8399963378906, "close": 295.3900146484375, "volume": 426481}, {"epoch": 1782327900.0, "open": 295.4049987792969, "high": 295.44000244140625, "low": 294.7900085449219, "close": 295.2149963378906, "volume": 390843}, {"epoch": 1782328200.0, "open": 295.2149963378906, "high": 295.2369079589844, "low": 294.94000244140625, "close": 295.0400085449219, "volume": 408929}, {"epoch": 1782328500.0, "open": 295.0299987792969, "high": 295.2200012207031, "low": 294.80999755859375, "close": 295.05999755859375, "volume": 380163}, {"epoch": 1782328800.0, "open": 295.05999755859375, "high": 295.1600036621094, "low": 294.9100036621094, "close": 294.9800109863281, "volume": 381534}, {"epoch": 1782329100.0, "open": 294.989990234375, "high": 295.239990234375, "low": 294.8999938964844, "close": 294.9400939941406, "volume": 339984}, {"epoch": 1782329400.0, "open": 294.92999267578125, "high": 295.1300048828125, "low": 294.7300109863281, "close": 294.9599914550781, "volume": 526138}, {"epoch": 1782329700.0, "open": 294.9519958496094, "high": 294.9800109863281, "low": 294.4700012207031, "close": 294.6499938964844, "volume": 801265}, {"epoch": 1782330000.0, "open": 294.6400146484375, "high": 295.1400146484375, "low": 294.5199890136719, "close": 295.0350036621094, "volume": 573362}, {"epoch": 1782330300.0, "open": 295.04998779296875, "high": 295.3699951171875, "low": 294.82000732421875, "close": 294.9700012207031, "volume": 567818}, {"epoch": 1782330600.0, "open": 294.989990234375, "high": 295.2900085449219, "low": 294.0799865722656, "close": 295.25, "volume": 1283560}, {"epoch": 1782330900.0, "open": 295.239990234375, "high": 295.25, "low": 292.94000244140625, "close": 293.260009765625, "volume": 3863726}, {"epoch": 1782394200.0, "open": 287.510009765625, "high": 288.79998779296875, "low": 284.7300109863281, "close": 285.69000244140625, "volume": 3957272}, {"epoch": 1782394500.0, "open": 285.6199951171875, "high": 285.8399963378906, "low": 281.0799865722656, "close": 281.1499938964844, "volume": 2546987}, {"epoch": 1782394800.0, "open": 281.1199951171875, "high": 281.2799987792969, "low": 277.8800048828125, "close": 278.1600036621094, "volume": 3073932}, {"epoch": 1782395100.0, "open": 278.1199951171875, "high": 279.92999267578125, "low": 278.07000732421875, "close": 279.760009765625, "volume": 2379377}, {"epoch": 1782395400.0, "open": 279.7799987792969, "high": 279.94000244140625, "low": 278.1199951171875, "close": 278.1300048828125, "volume": 1869356}, {"epoch": 1782395700.0, "open": 278.1400146484375, "high": 279.3399963378906, "low": 277.6700134277344, "close": 278.9700012207031, "volume": 1319750}, {"epoch": 1782396000.0, "open": 278.94500732421875, "high": 280.1798095703125, "low": 278.8299865722656, "close": 279.95001220703125, "volume": 1486808}, {"epoch": 1782396300.0, "open": 279.95001220703125, "high": 280.06988525390625, "low": 279.010009765625, "close": 279.57000732421875, "volume": 974399}, {"epoch": 1782396600.0, "open": 279.5799865722656, "high": 279.92498779296875, "low": 277.9599914550781, "close": 278.4599914550781, "volume": 1408253}, {"epoch": 1782396900.0, "open": 278.44500732421875, "high": 279.19000244140625, "low": 277.4599914550781, "close": 279.1449890136719, "volume": 1345736}, {"epoch": 1782397200.0, "open": 279.1549987792969, "high": 279.7799987792969, "low": 277.92999267578125, "close": 278.04998779296875, "volume": 1336111}, {"epoch": 1782397500.0, "open": 278.0350036621094, "high": 279.739990234375, "low": 278.0350036621094, "close": 279.6300048828125, "volume": 1045861}, {"epoch": 1782397800.0, "open": 279.635009765625, "high": 280.0899963378906, "low": 279.0199890136719, "close": 279.54998779296875, "volume": 856979}, {"epoch": 1782398100.0, "open": 279.5350036621094, "high": 280.0, "low": 279.05499267578125, "close": 279.75, "volume": 642344}, {"epoch": 1782398400.0, "open": 279.7550048828125, "high": 280.0899963378906, "low": 278.5899963378906, "close": 279.7300109863281, "volume": 971805}, {"epoch": 1782398700.0, "open": 279.7300109863281, "high": 279.989990234375, "low": 278.93499755859375, "close": 279.0299987792969, "volume": 892981}, {"epoch": 1782399000.0, "open": 279.0199890136719, "high": 279.5, "low": 278.4100036621094, "close": 279.02850341796875, "volume": 740451}, {"epoch": 1782399300.0, "open": 279.0, "high": 279.2099914550781, "low": 277.4599914550781, "close": 277.6050109863281, "volume": 843606}, {"epoch": 1782399600.0, "open": 277.6099853515625, "high": 278.1000061035156, "low": 277.239990234375, "close": 277.55999755859375, "volume": 816258}, {"epoch": 1782399900.0, "open": 277.55999755859375, "high": 277.8299865722656, "low": 276.779296875, "close": 277.82501220703125, "volume": 918053}, {"epoch": 1782400200.0, "open": 277.79998779296875, "high": 277.81988525390625, "low": 276.80999755859375, "close": 277.0199890136719, "volume": 745947}, {"epoch": 1782400500.0, "open": 277.0199890136719, "high": 277.1000061035156, "low": 276.5199890136719, "close": 276.8550109863281, "volume": 949002}, {"epoch": 1782400800.0, "open": 276.8599853515625, "high": 277.17999267578125, "low": 276.44000244140625, "close": 276.8699951171875, "volume": 984169}, {"epoch": 1782401100.0, "open": 276.8599853515625, "high": 278.0, "low": 276.44000244140625, "close": 277.6400146484375, "volume": 751906}, {"epoch": 1782401400.0, "open": 277.6600036621094, "high": 278.8699951171875, "low": 277.5899963378906, "close": 278.42999267578125, "volume": 753522}, {"epoch": 1782401700.0, "open": 278.44000244140625, "high": 279.25, "low": 278.44000244140625, "close": 278.5849914550781, "volume": 670606}, {"epoch": 1782402000.0, "open": 278.5801086425781, "high": 279.4700012207031, "low": 278.1300048828125, "close": 279.25, "volume": 666354}, {"epoch": 1782402300.0, "open": 279.25, "high": 279.6449890136719, "low": 278.989990234375, "close": 279.13958740234375, "volume": 560601}, {"epoch": 1782402600.0, "open": 279.1199951171875, "high": 279.1499938964844, "low": 278.1099853515625, "close": 278.3900146484375, "volume": 504493}, {"epoch": 1782402900.0, "open": 278.3800048828125, "high": 278.7699890136719, "low": 277.6300048828125, "close": 277.8550109863281, "volume": 714375}, {"epoch": 1782403200.0, "open": 277.8900146484375, "high": 278.19000244140625, "low": 277.6000061035156, "close": 277.9800109863281, "volume": 530324}, {"epoch": 1782403500.0, "open": 277.989990234375, "high": 278.1369934082031, "low": 277.4700012207031, "close": 277.69000244140625, "volume": 505230}, {"epoch": 1782403800.0, "open": 277.7049865722656, "high": 277.9200134277344, "low": 276.30450439453125, "close": 276.4750061035156, "volume": 1135641}, {"epoch": 1782404100.0, "open": 276.4800109863281, "high": 276.6499938964844, "low": 275.5400085449219, "close": 275.56500244140625, "volume": 1037055}, {"epoch": 1782404400.0, "open": 275.56500244140625, "high": 276.20001220703125, "low": 274.8599853515625, "close": 275.0950012207031, "volume": 1266710}, {"epoch": 1782404700.0, "open": 275.1050109863281, "high": 275.3900146484375, "low": 274.4599914550781, "close": 274.56500244140625, "volume": 813395}, {"epoch": 1782405000.0, "open": 274.56500244140625, "high": 274.79998779296875, "low": 274.1300048828125, "close": 274.6600036621094, "volume": 995586}, {"epoch": 1782405300.0, "open": 274.6650085449219, "high": 275.0, "low": 273.75, "close": 274.2850036621094, "volume": 1193426}, {"epoch": 1782405600.0, "open": 274.2850036621094, "high": 275.0, "low": 273.9700012207031, "close": 274.7449951171875, "volume": 854933}, {"epoch": 1782405900.0, "open": 274.7749938964844, "high": 274.8699951171875, "low": 274.1199951171875, "close": 274.510009765625, "volume": 1143185}, {"epoch": 1782406200.0, "open": 274.5, "high": 275.0799865722656, "low": 274.1700134277344, "close": 274.6449890136719, "volume": 848692}, {"epoch": 1782406500.0, "open": 274.6600036621094, "high": 275.1600036621094, "low": 274.4599914550781, "close": 275.1199951171875, "volume": 1148503}, {"epoch": 1782406800.0, "open": 275.135009765625, "high": 276.7149963378906, "low": 275.1099853515625, "close": 276.44000244140625, "volume": 1134982}, {"epoch": 1782407100.0, "open": 276.4599914550781, "high": 277.1991882324219, "low": 276.239990234375, "close": 277.07000732421875, "volume": 1980351}, {"epoch": 1782407400.0, "open": 277.09991455078125, "high": 277.5398864746094, "low": 277.010009765625, "close": 277.1700134277344, "volume": 845625}, {"epoch": 1782407700.0, "open": 277.1899108886719, "high": 277.989990234375, "low": 277.1899108886719, "close": 277.44000244140625, "volume": 902159}, {"epoch": 1782408000.0, "open": 277.44000244140625, "high": 277.7699890136719, "low": 277.239990234375, "close": 277.2799072265625, "volume": 745405}, {"epoch": 1782408300.0, "open": 277.2701110839844, "high": 278.3900146484375, "low": 277.0199890136719, "close": 278.0400085449219, "volume": 1791318}, {"epoch": 1782408600.0, "open": 278.04998779296875, "high": 278.1099853515625, "low": 277.70001220703125, "close": 277.7799987792969, "volume": 527201}, {"epoch": 1782408900.0, "open": 277.7900085449219, "high": 277.906005859375, "low": 276.9800109863281, "close": 277.23150634765625, "volume": 509984}, {"epoch": 1782409200.0, "open": 277.2300109863281, "high": 277.6300048828125, "low": 277.02099609375, "close": 277.06500244140625, "volume": 591826}, {"epoch": 1782409500.0, "open": 277.05999755859375, "high": 277.07000732421875, "low": 276.239990234375, "close": 276.75, "volume": 922689}, {"epoch": 1782409800.0, "open": 276.739990234375, "high": 276.7900085449219, "low": 276.19000244140625, "close": 276.2449951171875, "volume": 646395}, {"epoch": 1782410100.0, "open": 276.239990234375, "high": 276.79998779296875, "low": 276.2300109863281, "close": 276.7882080078125, "volume": 861509}, {"epoch": 1782410400.0, "open": 276.7950134277344, "high": 276.92999267578125, "low": 276.2200012207031, "close": 276.760009765625, "volume": 706216}, {"epoch": 1782410700.0, "open": 276.760009765625, "high": 278.5, "low": 276.6199951171875, "close": 278.42999267578125, "volume": 728324}, {"epoch": 1782411000.0, "open": 278.42999267578125, "high": 278.8599853515625, "low": 278.1099853515625, "close": 278.2900085449219, "volume": 752863}, {"epoch": 1782411300.0, "open": 278.2799987792969, "high": 280.0400085449219, "low": 278.07000732421875, "close": 279.94000244140625, "volume": 746643}, {"epoch": 1782411600.0, "open": 279.94500732421875, "high": 280.17999267578125, "low": 279.40008544921875, "close": 279.69000244140625, "volume": 750304}, {"epoch": 1782411900.0, "open": 279.6600036621094, "high": 279.67999267578125, "low": 279.0173034667969, "close": 279.3450012207031, "volume": 699538}, {"epoch": 1782412200.0, "open": 279.3500061035156, "high": 279.6499938964844, "low": 278.80999755859375, "close": 279.5799865722656, "volume": 768276}, {"epoch": 1782412500.0, "open": 279.55999755859375, "high": 280.2200927734375, "low": 279.3599853515625, "close": 279.8699951171875, "volume": 676647}, {"epoch": 1782412800.0, "open": 279.8800048828125, "high": 280.20001220703125, "low": 279.7099914550781, "close": 279.7699890136719, "volume": 445580}, {"epoch": 1782413100.0, "open": 279.739990234375, "high": 279.75, "low": 279.2799987792969, "close": 279.5557861328125, "volume": 451135}, {"epoch": 1782413400.0, "open": 279.5400085449219, "high": 279.58990478515625, "low": 279.0299987792969, "close": 279.3699951171875, "volume": 439693}, {"epoch": 1782413700.0, "open": 279.3699951171875, "high": 279.4949951171875, "low": 279.1199951171875, "close": 279.42498779296875, "volume": 505875}, {"epoch": 1782414000.0, "open": 279.42999267578125, "high": 279.42999267578125, "low": 278.8399963378906, "close": 279.0, "volume": 764896}, {"epoch": 1782414300.0, "open": 279.0, "high": 279.0199890136719, "low": 278.1499938964844, "close": 278.5299987792969, "volume": 847629}, {"epoch": 1782414600.0, "open": 278.5400085449219, "high": 278.5400085449219, "low": 276.29998779296875, "close": 276.5299987792969, "volume": 1369196}, {"epoch": 1782414900.0, "open": 276.5299987792969, "high": 277.18798828125, "low": 276.30999755859375, "close": 276.739990234375, "volume": 1250966}, {"epoch": 1782415200.0, "open": 276.7300109863281, "high": 278.07000732421875, "low": 276.0400085449219, "close": 277.5799865722656, "volume": 1031366}, {"epoch": 1782415500.0, "open": 277.5299987792969, "high": 277.8550109863281, "low": 276.7099914550781, "close": 276.7250061035156, "volume": 819936}, {"epoch": 1782415800.0, "open": 276.70001220703125, "high": 277.05999755859375, "low": 276.0400085449219, "close": 276.5899963378906, "volume": 1810840}, {"epoch": 1782416100.0, "open": 276.5899963378906, "high": 276.6000061035156, "low": 275.61199951171875, "close": 275.8599853515625, "volume": 1415978}, {"epoch": 1782416400.0, "open": 275.8599853515625, "high": 275.9700012207031, "low": 275.3299865722656, "close": 275.375, "volume": 1205106}, {"epoch": 1782416700.0, "open": 275.3599853515625, "high": 275.6099853515625, "low": 274.57000732421875, "close": 275.1700134277344, "volume": 1715887}, {"epoch": 1782417000.0, "open": 275.260009765625, "high": 277.45001220703125, "low": 275.20001220703125, "close": 276.8900146484375, "volume": 2770461}, {"epoch": 1782417300.0, "open": 276.94000244140625, "high": 276.95001220703125, "low": 273.8999938964844, "close": 275.04998779296875, "volume": 6706736}, {"epoch": 1782480600.0, "open": 275.0, "high": 278.0, "low": 274.2099914550781, "close": 276.92999267578125, "volume": 4456818}, {"epoch": 1782480900.0, "open": 276.94000244140625, "high": 277.5799865722656, "low": 276.1499938964844, "close": 276.80999755859375, "volume": 1398066}, {"epoch": 1782481200.0, "open": 276.82940673828125, "high": 278.17999267578125, "low": 276.25, "close": 276.8999938964844, "volume": 1528109}, {"epoch": 1782481500.0, "open": 276.9200134277344, "high": 277.0199890136719, "low": 276.0199890136719, "close": 276.3800048828125, "volume": 1197907}, {"epoch": 1782481800.0, "open": 276.375, "high": 276.82000732421875, "low": 275.6449890136719, "close": 276.3900146484375, "volume": 1340998}, {"epoch": 1782482100.0, "open": 276.3999938964844, "high": 277.25, "low": 275.44000244140625, "close": 275.70001220703125, "volume": 1291954}, {"epoch": 1782482400.0, "open": 275.7369079589844, "high": 277.24969482421875, "low": 275.4599914550781, "close": 277.1000061035156, "volume": 1218079}, {"epoch": 1782482700.0, "open": 277.1099853515625, "high": 278.3500061035156, "low": 277.07000732421875, "close": 277.8900146484375, "volume": 1067058}, {"epoch": 1782483000.0, "open": 277.8800048828125, "high": 278.33990478515625, "low": 277.75, "close": 278.19000244140625, "volume": 853233}, {"epoch": 1782483300.0, "open": 278.2099914550781, "high": 278.3399963378906, "low": 277.4461975097656, "close": 277.4599914550781, "volume": 824821}, {"epoch": 1782483600.0, "open": 277.5, "high": 277.9049987792969, "low": 276.94000244140625, "close": 277.635009765625, "volume": 871730}, {"epoch": 1782483900.0, "open": 277.6449890136719, "high": 278.92999267578125, "low": 277.3599853515625, "close": 278.260009765625, "volume": 978031}, {"epoch": 1782484200.0, "open": 278.2799987792969, "high": 279.95001220703125, "low": 278.0799865722656, "close": 279.6899108886719, "volume": 1281905}, {"epoch": 1782484500.0, "open": 279.69000244140625, "high": 279.79998779296875, "low": 278.5, "close": 279.3299865722656, "volume": 1036036}, {"epoch": 1782484800.0, "open": 279.30999755859375, "high": 280.0, "low": 278.6400146484375, "close": 279.3550109863281, "volume": 919266}, {"epoch": 1782485100.0, "open": 279.3699951171875, "high": 279.8999938964844, "low": 278.9200134277344, "close": 279.739990234375, "volume": 652614}, {"epoch": 1782485400.0, "open": 279.760009765625, "high": 279.9200134277344, "low": 279.20001220703125, "close": 279.7349853515625, "volume": 605372}, {"epoch": 1782485700.0, "open": 279.739990234375, "high": 280.2200012207031, "low": 279.635009765625, "close": 279.849609375, "volume": 1163529}, {"epoch": 1782486000.0, "open": 279.8500061035156, "high": 280.4700012207031, "low": 279.7900085449219, "close": 280.32000732421875, "volume": 757695}, {"epoch": 1782486300.0, "open": 280.32000732421875, "high": 280.4100036621094, "low": 279.67120361328125, "close": 279.8699951171875, "volume": 780251}, {"epoch": 1782486600.0, "open": 279.8800048828125, "high": 280.0299987792969, "low": 279.1700134277344, "close": 279.5899963378906, "volume": 773154}, {"epoch": 1782486900.0, "open": 279.5899963378906, "high": 279.9200134277344, "low": 279.2300109863281, "close": 279.9200134277344, "volume": 694379}, {"epoch": 1782487200.0, "open": 279.9200134277344, "high": 280.0, "low": 278.3599853515625, "close": 279.2699890136719, "volume": 921397}, {"epoch": 1782487500.0, "open": 279.260009765625, "high": 279.277099609375, "low": 278.6499938964844, "close": 279.0299987792969, "volume": 798892}, {"epoch": 1782487800.0, "open": 279.0259094238281, "high": 279.45001220703125, "low": 277.760009765625, "close": 278.1099853515625, "volume": 2144170}, {"epoch": 1782488100.0, "open": 278.1050109863281, "high": 278.6600036621094, "low": 278.0799865722656, "close": 278.4800109863281, "volume": 677089}, {"epoch": 1782488400.0, "open": 278.5249938964844, "high": 278.6300048828125, "low": 277.56500244140625, "close": 278.125, "volume": 1201160}, {"epoch": 1782488700.0, "open": 278.1300048828125, "high": 278.2149963378906, "low": 277.6400146484375, "close": 278.125, "volume": 746742}, {"epoch": 1782489000.0, "open": 278.1300048828125, "high": 278.3699951171875, "low": 277.0, "close": 277.260009765625, "volume": 1335170}, {"epoch": 1782489300.0, "open": 277.2633056640625, "high": 277.6000061035156, "low": 277.0199890136719, "close": 277.1650085449219, "volume": 800889}, {"epoch": 1782489600.0, "open": 277.17999267578125, "high": 277.32000732421875, "low": 276.32000732421875, "close": 276.3999938964844, "volume": 894476}, {"epoch": 1782489900.0, "open": 276.4200134277344, "high": 276.54998779296875, "low": 275.82000732421875, "close": 275.8900146484375, "volume": 825793}, {"epoch": 1782490200.0, "open": 275.8900146484375, "high": 276.2799987792969, "low": 275.55999755859375, "close": 276.0050048828125, "volume": 946919}, {"epoch": 1782490500.0, "open": 276.0050048828125, "high": 276.1650085449219, "low": 275.42999267578125, "close": 275.6000061035156, "volume": 883655}, {"epoch": 1782490800.0, "open": 275.57000732421875, "high": 276.1099853515625, "low": 275.25, "close": 275.79998779296875, "volume": 1448845}, {"epoch": 1782491100.0, "open": 275.7900085449219, "high": 276.6000061035156, "low": 275.4200134277344, "close": 275.8999938964844, "volume": 1325345}, {"epoch": 1782491400.0, "open": 275.8999938964844, "high": 277.42999267578125, "low": 275.8999938964844, "close": 277.42999267578125, "volume": 559356}, {"epoch": 1782491700.0, "open": 277.42999267578125, "high": 277.54998779296875, "low": 276.80999755859375, "close": 277.2449951171875, "volume": 748812}, {"epoch": 1782492000.0, "open": 277.2449951171875, "high": 278.1600036621094, "low": 277.2449951171875, "close": 278.1199951171875, "volume": 738813}, {"epoch": 1782492300.0, "open": 278.1050109863281, "high": 278.8371887207031, "low": 277.92999267578125, "close": 278.635009765625, "volume": 1189062}, {"epoch": 1782492600.0, "open": 278.6400146484375, "high": 279.3699951171875, "low": 278.54998779296875, "close": 278.95001220703125, "volume": 615561}, {"epoch": 1782492900.0, "open": 278.94000244140625, "high": 279.1099853515625, "low": 278.69000244140625, "close": 278.9100036621094, "volume": 640455}, {"epoch": 1782493200.0, "open": 278.9100036621094, "high": 279.05999755859375, "low": 278.42999267578125, "close": 278.53009033203125, "volume": 588458}, {"epoch": 1782493500.0, "open": 278.5249938964844, "high": 279.1700134277344, "low": 278.510009765625, "close": 279.1300964355469, "volume": 549097}, {"epoch": 1782493800.0, "open": 279.1300048828125, "high": 279.3699951171875, "low": 278.60009765625, "close": 278.8599853515625, "volume": 536817}, {"epoch": 1782494100.0, "open": 278.8699951171875, "high": 279.1000061035156, "low": 278.5, "close": 278.68499755859375, "volume": 626486}, {"epoch": 1782494400.0, "open": 278.70001220703125, "high": 279.07000732421875, "low": 278.6000061035156, "close": 278.8800048828125, "volume": 591618}, {"epoch": 1782494700.0, "open": 278.885009765625, "high": 279.29998779296875, "low": 278.7900085449219, "close": 279.19500732421875, "volume": 586834}, {"epoch": 1782495000.0, "open": 279.17999267578125, "high": 279.5899963378906, "low": 279.0199890136719, "close": 279.5, "volume": 546051}, {"epoch": 1782495300.0, "open": 279.4700012207031, "high": 279.5199890136719, "low": 279.1099853515625, "close": 279.3349914550781, "volume": 486851}, {"epoch": 1782495600.0, "open": 279.3500061035156, "high": 279.8599853515625, "low": 279.2217102050781, "close": 279.4200134277344, "volume": 452952}, {"epoch": 1782495900.0, "open": 279.4371032714844, "high": 279.7200012207031, "low": 278.75, "close": 278.7799987792969, "volume": 524595}, {"epoch": 1782496200.0, "open": 278.760009765625, "high": 279.1050109863281, "low": 278.64080810546875, "close": 279.0299987792969, "volume": 532148}, {"epoch": 1782496500.0, "open": 279.0400085449219, "high": 279.29998779296875, "low": 278.75, "close": 279.19500732421875, "volume": 512502}, {"epoch": 1782496800.0, "open": 279.2099914550781, "high": 280.3299865722656, "low": 278.8900146484375, "close": 280.29998779296875, "volume": 1063735}, {"epoch": 1782497100.0, "open": 280.2799987792969, "high": 280.67999267578125, "low": 280.010009765625, "close": 280.6000061035156, "volume": 1097182}, {"epoch": 1782497400.0, "open": 280.6000061035156, "high": 281.29998779296875, "low": 280.6000061035156, "close": 281.05010986328125, "volume": 679402}, {"epoch": 1782497700.0, "open": 281.05999755859375, "high": 281.2998962402344, "low": 280.6499938964844, "close": 280.8599853515625, "volume": 656073}, {"epoch": 1782498000.0, "open": 280.8599853515625, "high": 280.9657897949219, "low": 279.92999267578125, "close": 280.17999267578125, "volume": 930771}, {"epoch": 1782498300.0, "open": 280.1449890136719, "high": 280.29998779296875, "low": 279.5, "close": 280.19000244140625, "volume": 774986}, {"epoch": 1782498600.0, "open": 280.19500732421875, "high": 281.80999755859375, "low": 280.0899963378906, "close": 281.7193908691406, "volume": 1113070}, {"epoch": 1782498900.0, "open": 281.7200012207031, "high": 281.82000732421875, "low": 280.7799987792969, "close": 280.8500061035156, "volume": 1072544}, {"epoch": 1782499200.0, "open": 280.8299865722656, "high": 281.55999755859375, "low": 280.82000732421875, "close": 281.1700134277344, "volume": 1033655}, {"epoch": 1782499500.0, "open": 281.1650085449219, "high": 281.3299865722656, "low": 280.57000732421875, "close": 280.7900085449219, "volume": 1390553}, {"epoch": 1782499800.0, "open": 280.7850036621094, "high": 280.90008544921875, "low": 280.260009765625, "close": 280.4700012207031, "volume": 1072312}, {"epoch": 1782500100.0, "open": 280.4700012207031, "high": 280.8299865722656, "low": 280.3599853515625, "close": 280.7200012207031, "volume": 821833}, {"epoch": 1782500400.0, "open": 280.7149963378906, "high": 281.3999938964844, "low": 280.6300048828125, "close": 280.9599914550781, "volume": 1289053}, {"epoch": 1782500700.0, "open": 280.9700012207031, "high": 281.32000732421875, "low": 280.3699951171875, "close": 281.1393127441406, "volume": 1255384}, {"epoch": 1782501000.0, "open": 281.1449890136719, "high": 281.8299865722656, "low": 280.95001220703125, "close": 281.45001220703125, "volume": 1289345}, {"epoch": 1782501300.0, "open": 281.44500732421875, "high": 281.82000732421875, "low": 281.0, "close": 281.69500732421875, "volume": 1429564}, {"epoch": 1782501600.0, "open": 281.69000244140625, "high": 281.69000244140625, "low": 279.4100036621094, "close": 280.45001220703125, "volume": 2387878}, {"epoch": 1782501900.0, "open": 280.5, "high": 280.8900146484375, "low": 280.010009765625, "close": 280.1499938964844, "volume": 1414879}, {"epoch": 1782502200.0, "open": 280.1499938964844, "high": 281.35101318359375, "low": 280.1199951171875, "close": 281.1650085449219, "volume": 1826604}, {"epoch": 1782502500.0, "open": 281.1650085449219, "high": 281.2550048828125, "low": 280.0799865722656, "close": 280.6000061035156, "volume": 1685233}, {"epoch": 1782502800.0, "open": 280.6000061035156, "high": 281.4200134277344, "low": 280.0, "close": 281.260009765625, "volume": 2002831}, {"epoch": 1782503100.0, "open": 281.25, "high": 281.6700134277344, "low": 281.010009765625, "close": 281.25, "volume": 2068421}, {"epoch": 1782503400.0, "open": 281.260009765625, "high": 285.82000732421875, "low": 281.2300109863281, "close": 285.2598876953125, "volume": 6064315}, {"epoch": 1782503700.0, "open": 285.2149963378906, "high": 285.95001220703125, "low": 281.20001220703125, "close": 281.20001220703125, "volume": 9875623}, {"epoch": 1782739800.0, "open": 286.8599853515625, "high": 288.36968994140625, "low": 285.79998779296875, "close": 286.260009765625, "volume": 2674869}, {"epoch": 1782740100.0, "open": 286.260009765625, "high": 286.29998779296875, "low": 284.4049987792969, "close": 285.68499755859375, "volume": 778379}, {"epoch": 1782740400.0, "open": 285.739990234375, "high": 286.0199890136719, "low": 283.7349853515625, "close": 284.0150146484375, "volume": 753369}, {"epoch": 1782740700.0, "open": 284.0400085449219, "high": 285.19000244140625, "low": 283.55999755859375, "close": 283.9849853515625, "volume": 1064055}, {"epoch": 1782741000.0, "open": 284.010009765625, "high": 285.239990234375, "low": 283.7799987792969, "close": 284.2950134277344, "volume": 893189}, {"epoch": 1782741300.0, "open": 284.3500061035156, "high": 284.5, "low": 283.5220031738281, "close": 283.9599914550781, "volume": 695507}, {"epoch": 1782741600.0, "open": 283.9750061035156, "high": 284.0400085449219, "low": 283.4800109863281, "close": 283.7449951171875, "volume": 540497}, {"epoch": 1782741900.0, "open": 283.739990234375, "high": 283.94000244140625, "low": 282.5, "close": 282.69000244140625, "volume": 614220}, {"epoch": 1782742200.0, "open": 282.70001220703125, "high": 282.8399963378906, "low": 281.7250061035156, "close": 281.82501220703125, "volume": 718953}, {"epoch": 1782742500.0, "open": 281.79998779296875, "high": 282.375, "low": 281.6600036621094, "close": 282.05999755859375, "volume": 626694}, {"epoch": 1782742800.0, "open": 282.0899963378906, "high": 282.0899963378906, "low": 281.30999755859375, "close": 281.3349914550781, "volume": 550364}, {"epoch": 1782743100.0, "open": 281.3399963378906, "high": 281.5299987792969, "low": 280.45001220703125, "close": 280.8699951171875, "volume": 719363}, {"epoch": 1782743400.0, "open": 280.8800048828125, "high": 281.80999755859375, "low": 280.3299865722656, "close": 281.79998779296875, "volume": 1223753}, {"epoch": 1782743700.0, "open": 281.7699890136719, "high": 282.2900085449219, "low": 281.3399963378906, "close": 281.4800109863281, "volume": 985375}, {"epoch": 1782744000.0, "open": 281.4649963378906, "high": 281.7799987792969, "low": 280.9750061035156, "close": 281.5249938964844, "volume": 662451}, {"epoch": 1782744300.0, "open": 281.5400085449219, "high": 282.1400146484375, "low": 281.2699890136719, "close": 281.94000244140625, "volume": 644771}, {"epoch": 1782744600.0, "open": 281.92999267578125, "high": 282.8299865722656, "low": 281.8999938964844, "close": 282.5199890136719, "volume": 561241}, {"epoch": 1782744900.0, "open": 282.510009765625, "high": 282.5150146484375, "low": 281.81500244140625, "close": 281.81500244140625, "volume": 602312}, {"epoch": 1782745200.0, "open": 281.82000732421875, "high": 282.1400146484375, "low": 281.57000732421875, "close": 281.69500732421875, "volume": 494674}, {"epoch": 1782745500.0, "open": 281.70001220703125, "high": 281.8399963378906, "low": 281.3500061035156, "close": 281.80499267578125, "volume": 566481}, {"epoch": 1782745800.0, "open": 281.80999755859375, "high": 282.19970703125, "low": 280.7099914550781, "close": 281.95001220703125, "volume": 1005906}, {"epoch": 1782746100.0, "open": 281.95001220703125, "high": 282.42498779296875, "low": 281.92498779296875, "close": 282.2799987792969, "volume": 355356}, {"epoch": 1782746400.0, "open": 282.2699890136719, "high": 282.3900146484375, "low": 281.5799865722656, "close": 281.7799987792969, "volume": 328907}, {"epoch": 1782746700.0, "open": 281.7799987792969, "high": 282.385009765625, "low": 281.7250061035156, "close": 282.3301086425781, "volume": 434747}, {"epoch": 1782747000.0, "open": 282.3424987792969, "high": 282.5498962402344, "low": 281.8500061035156, "close": 281.9100036621094, "volume": 558029}, {"epoch": 1782747300.0, "open": 281.94000244140625, "high": 282.45001220703125, "low": 281.8999938964844, "close": 282.25, "volume": 385002}, {"epoch": 1782747600.0, "open": 282.239990234375, "high": 282.75, "low": 281.8999938964844, "close": 282.67999267578125, "volume": 726498}, {"epoch": 1782747900.0, "open": 282.67999267578125, "high": 282.69500732421875, "low": 282.2250061035156, "close": 282.42999267578125, "volume": 907157}, {"epoch": 1782748200.0, "open": 282.42498779296875, "high": 283.03448486328125, "low": 282.3800048828125, "close": 282.494384765625, "volume": 607044}, {"epoch": 1782748500.0, "open": 282.4800109863281, "high": 282.489990234375, "low": 281.4700927734375, "close": 281.5050048828125, "volume": 532180}, {"epoch": 1782748800.0, "open": 281.5299987792969, "high": 281.54998779296875, "low": 280.8800964355469, "close": 281.29998779296875, "volume": 443817}, {"epoch": 1782749100.0, "open": 281.30999755859375, "high": 281.6199951171875, "low": 280.7601013183594, "close": 280.8800048828125, "volume": 539455}, {"epoch": 1782749400.0, "open": 280.875, "high": 281.0, "low": 280.3500061035156, "close": 280.4100036621094, "volume": 726199}, {"epoch": 1782749700.0, "open": 280.4200134277344, "high": 280.8500061035156, "low": 280.2200012207031, "close": 280.4800109863281, "volume": 1172810}, {"epoch": 1782750000.0, "open": 280.4700012207031, "high": 281.5, "low": 280.4224853515625, "close": 280.7699890136719, "volume": 427526}, {"epoch": 1782750300.0, "open": 280.760009765625, "high": 280.93499755859375, "low": 280.510009765625, "close": 280.55999755859375, "volume": 378412}, {"epoch": 1782750600.0, "open": 280.55999755859375, "high": 280.7598876953125, "low": 280.1499938964844, "close": 280.2799987792969, "volume": 353059}, {"epoch": 1782750900.0, "open": 280.2900085449219, "high": 280.5799865722656, "low": 279.92999267578125, "close": 280.5299987792969, "volume": 477212}, {"epoch": 1782751200.0, "open": 280.53009033203125, "high": 280.79998779296875, "low": 280.1300048828125, "close": 280.1600036621094, "volume": 358277}, {"epoch": 1782751500.0, "open": 280.17999267578125, "high": 280.32501220703125, "low": 279.875, "close": 279.989990234375, "volume": 513315}, {"epoch": 1782751800.0, "open": 279.9800109863281, "high": 280.760009765625, "low": 279.94000244140625, "close": 280.4700012207031, "volume": 481987}, {"epoch": 1782752100.0, "open": 280.4599914550781, "high": 280.4800109863281, "low": 280.1957092285156, "close": 280.30999755859375, "volume": 373728}, {"epoch": 1782752400.0, "open": 280.32000732421875, "high": 280.489990234375, "low": 280.1300048828125, "close": 280.20001220703125, "volume": 361157}, {"epoch": 1782752700.0, "open": 280.2099914550781, "high": 280.4700012207031, "low": 280.0350036621094, "close": 280.1099853515625, "volume": 405803}, {"epoch": 1782753000.0, "open": 280.1199951171875, "high": 280.2099914550781, "low": 279.8500061035156, "close": 280.1000061035156, "volume": 570942}, {"epoch": 1782753300.0, "open": 280.1099853515625, "high": 281.17999267578125, "low": 280.1099853515625, "close": 281.1499938964844, "volume": 549310}, {"epoch": 1782753600.0, "open": 281.1549987792969, "high": 281.5400085449219, "low": 281.05999755859375, "close": 281.489990234375, "volume": 329516}, {"epoch": 1782753900.0, "open": 281.489990234375, "high": 281.5400085449219, "low": 281.1199951171875, "close": 281.4800109863281, "volume": 450210}, {"epoch": 1782754200.0, "open": 281.4700012207031, "high": 281.8800048828125, "low": 281.32000732421875, "close": 281.78009033203125, "volume": 425172}, {"epoch": 1782754500.0, "open": 281.7850036621094, "high": 281.8900146484375, "low": 281.360107421875, "close": 281.5899963378906, "volume": 298866}, {"epoch": 1782754800.0, "open": 281.5799865722656, "high": 281.6400146484375, "low": 281.375, "close": 281.5, "volume": 315934}, {"epoch": 1782755100.0, "open": 281.5, "high": 282.2099914550781, "low": 281.45001220703125, "close": 282.1300048828125, "volume": 674571}, {"epoch": 1782755400.0, "open": 282.1300048828125, "high": 282.29998779296875, "low": 281.67999267578125, "close": 281.69000244140625, "volume": 377149}, {"epoch": 1782755700.0, "open": 281.69000244140625, "high": 282.17999267578125, "low": 281.5899963378906, "close": 282.0199890136719, "volume": 320148}, {"epoch": 1782756000.0, "open": 282.0299987792969, "high": 282.0299987792969, "low": 281.4200134277344, "close": 281.44500732421875, "volume": 332100}, {"epoch": 1782756300.0, "open": 281.44500732421875, "high": 281.5150146484375, "low": 281.0, "close": 281.1650085449219, "volume": 338439}, {"epoch": 1782756600.0, "open": 281.1700134277344, "high": 281.55999755859375, "low": 281.1099853515625, "close": 281.42999267578125, "volume": 216629}, {"epoch": 1782756900.0, "open": 281.42999267578125, "high": 281.67999267578125, "low": 281.2699890136719, "close": 281.42999267578125, "volume": 201027}, {"epoch": 1782757200.0, "open": 281.4200134277344, "high": 281.6199951171875, "low": 280.8599853515625, "close": 281.3078918457031, "volume": 327548}, {"epoch": 1782757500.0, "open": 281.30999755859375, "high": 281.6199951171875, "low": 281.25, "close": 281.54998779296875, "volume": 378940}, {"epoch": 1782757800.0, "open": 281.54998779296875, "high": 282.34991455078125, "low": 281.489990234375, "close": 282.135009765625, "volume": 620898}, {"epoch": 1782758100.0, "open": 282.135009765625, "high": 282.2699890136719, "low": 281.8699951171875, "close": 281.92999267578125, "volume": 371366}, {"epoch": 1782758400.0, "open": 281.94500732421875, "high": 282.19000244140625, "low": 281.67999267578125, "close": 282.1499938964844, "volume": 563503}, {"epoch": 1782758700.0, "open": 282.1499938964844, "high": 282.2622985839844, "low": 281.5006103515625, "close": 281.6400146484375, "volume": 378448}, {"epoch": 1782759000.0, "open": 281.6400146484375, "high": 281.7749938964844, "low": 281.4549865722656, "close": 281.67999267578125, "volume": 357873}, {"epoch": 1782759300.0, "open": 281.6700134277344, "high": 282.1099853515625, "low": 281.6700134277344, "close": 282.07000732421875, "volume": 449997}, {"epoch": 1782759600.0, "open": 282.07501220703125, "high": 283.0775146484375, "low": 281.94000244140625, "close": 282.80499267578125, "volume": 591002}, {"epoch": 1782759900.0, "open": 282.8200988769531, "high": 282.9100036621094, "low": 282.5, "close": 282.7799987792969, "volume": 443582}, {"epoch": 1782760200.0, "open": 282.7799987792969, "high": 282.8900146484375, "low": 282.55999755859375, "close": 282.6499938964844, "volume": 376149}, {"epoch": 1782760500.0, "open": 282.6499938964844, "high": 282.80999755859375, "low": 282.29998779296875, "close": 282.6050109863281, "volume": 542606}, {"epoch": 1782760800.0, "open": 282.5950012207031, "high": 282.68499755859375, "low": 282.44000244140625, "close": 282.56500244140625, "volume": 501272}, {"epoch": 1782761100.0, "open": 282.57000732421875, "high": 282.8900146484375, "low": 282.5, "close": 282.67999267578125, "volume": 457713}, {"epoch": 1782761400.0, "open": 282.7099914550781, "high": 282.739990234375, "low": 281.8599853515625, "close": 282.010009765625, "volume": 625017}, {"epoch": 1782761700.0, "open": 282.010009765625, "high": 282.32000732421875, "low": 281.7699890136719, "close": 282.2950134277344, "volume": 1488353}, {"epoch": 1782762000.0, "open": 282.2900085449219, "high": 282.3500061035156, "low": 281.6499938964844, "close": 281.7900085449219, "volume": 587718}, {"epoch": 1782762300.0, "open": 281.79998779296875, "high": 282.1499938964844, "low": 281.6000061035156, "close": 282.0400085449219, "volume": 698936}, {"epoch": 1782762600.0, "open": 282.04998779296875, "high": 282.4200134277344, "low": 281.79998779296875, "close": 282.1000061035156, "volume": 868875}, {"epoch": 1782762900.0, "open": 282.1050109863281, "high": 282.19000244140625, "low": 281.4700012207031, "close": 281.6300048828125, "volume": 2275852}, {"epoch": 1782826200.0, "open": 281.1700134277344, "high": 283.5, "low": 280.69500732421875, "close": 283.2099914550781, "volume": 2197293}, {"epoch": 1782826500.0, "open": 283.2300109863281, "high": 284.84930419921875, "low": 282.6099853515625, "close": 284.3450012207031, "volume": 1018938}, {"epoch": 1782826800.0, "open": 284.3450012207031, "high": 284.760009765625, "low": 283.1300048828125, "close": 283.2698974609375, "volume": 553198}, {"epoch": 1782827100.0, "open": 283.2699890136719, "high": 284.70001220703125, "low": 282.82000732421875, "close": 284.2900085449219, "volume": 791479}, {"epoch": 1782827400.0, "open": 284.29998779296875, "high": 285.239990234375, "low": 284.2149963378906, "close": 284.98919677734375, "volume": 741681}, {"epoch": 1782827700.0, "open": 285.0299987792969, "high": 285.34368896484375, "low": 284.75, "close": 285.30999755859375, "volume": 486377}, {"epoch": 1782828000.0, "open": 285.30999755859375, "high": 285.92498779296875, "low": 285.1099853515625, "close": 285.6510009765625, "volume": 630869}, {"epoch": 1782828300.0, "open": 285.6400146484375, "high": 285.9700012207031, "low": 285.0899963378906, "close": 285.17999267578125, "volume": 596533}, {"epoch": 1782828600.0, "open": 285.20001220703125, "high": 285.9800109863281, "low": 284.739990234375, "close": 285.8550109863281, "volume": 591817}, {"epoch": 1782828900.0, "open": 285.8500061035156, "high": 286.20001220703125, "low": 285.6199951171875, "close": 285.9800109863281, "volume": 514974}, {"epoch": 1782829200.0, "open": 285.9800109863281, "high": 286.239990234375, "low": 285.5, "close": 286.1400146484375, "volume": 525045}, {"epoch": 1782829500.0, "open": 286.1449890136719, "high": 286.2898864746094, "low": 285.79010009765625, "close": 286.0249938964844, "volume": 458393}, {"epoch": 1782829800.0, "open": 286.010009765625, "high": 286.260009765625, "low": 285.95001220703125, "close": 286.1499938964844, "volume": 331211}, {"epoch": 1782830100.0, "open": 286.1600036621094, "high": 286.20001220703125, "low": 285.57000732421875, "close": 285.80999755859375, "volume": 394884}, {"epoch": 1782830400.0, "open": 285.82000732421875, "high": 285.8450012207031, "low": 285.260009765625, "close": 285.5707092285156, "volume": 342191}, {"epoch": 1782830700.0, "open": 285.5899963378906, "high": 285.82000732421875, "low": 285.4100036621094, "close": 285.5299987792969, "volume": 339954}, {"epoch": 1782831000.0, "open": 285.53009033203125, "high": 286.9200134277344, "low": 285.4150085449219, "close": 286.57000732421875, "volume": 816642}, {"epoch": 1782831300.0, "open": 286.5799865722656, "high": 287.0799865722656, "low": 286.1311950683594, "close": 286.9700012207031, "volume": 858620}, {"epoch": 1782831600.0, "open": 286.9800109863281, "high": 287.3399963378906, "low": 286.6400146484375, "close": 287.3299865722656, "volume": 502972}, {"epoch": 1782831900.0, "open": 287.32501220703125, "high": 287.3299865722656, "low": 286.7300109863281, "close": 287.010009765625, "volume": 293578}, {"epoch": 1782832200.0, "open": 287.010009765625, "high": 287.34991455078125, "low": 286.82000732421875, "close": 286.9599914550781, "volume": 340089}, {"epoch": 1782832500.0, "open": 286.9599914550781, "high": 287.739990234375, "low": 286.6199035644531, "close": 287.67498779296875, "volume": 457395}, {"epoch": 1782832800.0, "open": 287.6700134277344, "high": 288.5849914550781, "low": 287.614990234375, "close": 288.4599914550781, "volume": 678030}, {"epoch": 1782833100.0, "open": 288.4750061035156, "high": 288.6600036621094, "low": 288.07000732421875, "close": 288.2699890136719, "volume": 414036}, {"epoch": 1782833400.0, "open": 288.2799987792969, "high": 288.8500061035156, "low": 288.1600036621094, "close": 288.75, "volume": 416604}, {"epoch": 1782833700.0, "open": 288.739990234375, "high": 289.05999755859375, "low": 288.510009765625, "close": 289.0450134277344, "volume": 403974}, {"epoch": 1782834000.0, "open": 289.0299987792969, "high": 289.159912109375, "low": 288.30999755859375, "close": 288.45001220703125, "volume": 507920}, {"epoch": 1782834300.0, "open": 288.45001220703125, "high": 289.3500061035156, "low": 288.45001220703125, "close": 289.31500244140625, "volume": 370887}, {"epoch": 1782834600.0, "open": 289.31500244140625, "high": 289.3800048828125, "low": 288.75, "close": 288.7699890136719, "volume": 582875}, {"epoch": 1782834900.0, "open": 288.7799987792969, "high": 288.9800109863281, "low": 288.5799865722656, "close": 288.73980712890625, "volume": 329727}, {"epoch": 1782835200.0, "open": 288.739990234375, "high": 289.20001220703125, "low": 288.739990234375, "close": 288.9599914550781, "volume": 346928}, {"epoch": 1782835500.0, "open": 288.9700012207031, "high": 288.989990234375, "low": 288.1700134277344, "close": 288.4599914550781, "volume": 362645}, {"epoch": 1782835800.0, "open": 288.4750061035156, "high": 288.6400146484375, "low": 287.80999755859375, "close": 288.260009765625, "volume": 378321}, {"epoch": 1782836100.0, "open": 288.260009765625, "high": 288.5, "low": 288.0799865722656, "close": 288.239990234375, "volume": 285544}, {"epoch": 1782836400.0, "open": 288.25, "high": 288.2799987792969, "low": 287.94171142578125, "close": 288.1400146484375, "volume": 203216}, {"epoch": 1782836700.0, "open": 288.1600036621094, "high": 288.45001220703125, "low": 287.947509765625, "close": 288.1449890136719, "volume": 235871}, {"epoch": 1782837000.0, "open": 288.1600036621094, "high": 288.5899963378906, "low": 288.125, "close": 288.44000244140625, "volume": 250322}, {"epoch": 1782837300.0, "open": 288.42999267578125, "high": 288.6199951171875, "low": 288.32000732421875, "close": 288.5799865722656, "volume": 231641}, {"epoch": 1782837600.0, "open": 288.55010986328125, "high": 288.75, "low": 288.3743896484375, "close": 288.7074890136719, "volume": 308281}, {"epoch": 1782837900.0, "open": 288.7099914550781, "high": 288.9800109863281, "low": 288.6199951171875, "close": 288.9200134277344, "volume": 283418}, {"epoch": 1782838200.0, "open": 288.9599914550781, "high": 289.1400146484375, "low": 288.69000244140625, "close": 289.07000732421875, "volume": 351632}, {"epoch": 1782838500.0, "open": 289.07000732421875, "high": 289.2200012207031, "low": 288.8399963378906, "close": 289.18499755859375, "volume": 284084}, {"epoch": 1782838800.0, "open": 289.20001220703125, "high": 289.6600036621094, "low": 289.1499938964844, "close": 289.5950012207031, "volume": 392067}, {"epoch": 1782839100.0, "open": 289.5950012207031, "high": 289.6000061035156, "low": 289.0404052734375, "close": 289.1549987792969, "volume": 227280}, {"epoch": 1782839400.0, "open": 289.1400146484375, "high": 289.45001220703125, "low": 288.9150085449219, "close": 289.0, "volume": 316862}, {"epoch": 1782839700.0, "open": 288.9800109863281, "high": 288.9800109863281, "low": 288.32000732421875, "close": 288.3999938964844, "volume": 254536}, {"epoch": 1782840000.0, "open": 288.3900146484375, "high": 288.8599853515625, "low": 288.3399963378906, "close": 288.79998779296875, "volume": 243109}, {"epoch": 1782840300.0, "open": 288.82000732421875, "high": 288.92498779296875, "low": 288.42041015625, "close": 288.42999267578125, "volume": 229837}, {"epoch": 1782840600.0, "open": 288.44500732421875, "high": 288.57501220703125, "low": 288.2250061035156, "close": 288.40008544921875, "volume": 260793}, {"epoch": 1782840900.0, "open": 288.4200134277344, "high": 288.54998779296875, "low": 288.2349853515625, "close": 288.3599853515625, "volume": 250089}, {"epoch": 1782841200.0, "open": 288.3599853515625, "high": 288.55999755859375, "low": 288.2900085449219, "close": 288.375, "volume": 246955}, {"epoch": 1782841500.0, "open": 288.3900146484375, "high": 288.5199890136719, "low": 288.2550048828125, "close": 288.5199890136719, "volume": 221980}, {"epoch": 1782841800.0, "open": 288.510009765625, "high": 288.7200012207031, "low": 288.2099914550781, "close": 288.3599853515625, "volume": 251869}, {"epoch": 1782842100.0, "open": 288.3599853515625, "high": 288.54998779296875, "low": 288.1600036621094, "close": 288.4200134277344, "volume": 219363}, {"epoch": 1782842400.0, "open": 288.4200134277344, "high": 289.19000244140625, "low": 288.0899963378906, "close": 288.8099060058594, "volume": 661493}, {"epoch": 1782842700.0, "open": 288.8125, "high": 288.92999267578125, "low": 288.4649963378906, "close": 288.5426025390625, "volume": 303949}, {"epoch": 1782843000.0, "open": 288.5400085449219, "high": 288.95001220703125, "low": 288.5400085449219, "close": 288.94000244140625, "volume": 233418}, {"epoch": 1782843300.0, "open": 288.92999267578125, "high": 288.9599914550781, "low": 288.6199951171875, "close": 288.8999938964844, "volume": 216779}, {"epoch": 1782843600.0, "open": 288.94000244140625, "high": 289.0, "low": 288.7449951171875, "close": 288.760009765625, "volume": 276892}, {"epoch": 1782843900.0, "open": 288.7650146484375, "high": 288.82000732421875, "low": 287.8550109863281, "close": 288.0899963378906, "volume": 356469}, {"epoch": 1782844200.0, "open": 288.0849914550781, "high": 288.17999267578125, "low": 287.2799987792969, "close": 287.30499267578125, "volume": 381744}, {"epoch": 1782844500.0, "open": 287.31988525390625, "high": 287.6400146484375, "low": 287.1400146484375, "close": 287.3900146484375, "volume": 406751}, {"epoch": 1782844800.0, "open": 287.3999938964844, "high": 287.56988525390625, "low": 287.29998779296875, "close": 287.4549865722656, "volume": 224188}, {"epoch": 1782845100.0, "open": 287.4501037597656, "high": 287.510009765625, "low": 287.085205078125, "close": 287.17999267578125, "volume": 234406}, {"epoch": 1782845400.0, "open": 287.17999267578125, "high": 287.17999267578125, "low": 286.739990234375, "close": 286.7699890136719, "volume": 297630}, {"epoch": 1782845700.0, "open": 286.7699890136719, "high": 287.0199890136719, "low": 286.67999267578125, "close": 286.9849853515625, "volume": 299872}, {"epoch": 1782846000.0, "open": 286.9700012207031, "high": 287.5799865722656, "low": 286.9700012207031, "close": 287.45001220703125, "volume": 392937}, {"epoch": 1782846300.0, "open": 287.44000244140625, "high": 287.55999755859375, "low": 287.05999755859375, "close": 287.5450134277344, "volume": 354152}, {"epoch": 1782846600.0, "open": 287.54998779296875, "high": 287.7099914550781, "low": 287.3999938964844, "close": 287.55059814453125, "volume": 428008}, {"epoch": 1782846900.0, "open": 287.55999755859375, "high": 287.67498779296875, "low": 287.32000732421875, "close": 287.364990234375, "volume": 398231}, {"epoch": 1782847200.0, "open": 287.364990234375, "high": 287.989990234375, "low": 287.2749938964844, "close": 287.69500732421875, "volume": 469801}, {"epoch": 1782847500.0, "open": 287.69000244140625, "high": 288.1400146484375, "low": 287.3800048828125, "close": 287.5299987792969, "volume": 456821}, {"epoch": 1782847800.0, "open": 287.5299987792969, "high": 287.989990234375, "low": 287.5, "close": 287.7900085449219, "volume": 440375}, {"epoch": 1782848100.0, "open": 287.7850036621094, "high": 287.9649963378906, "low": 287.6000061035156, "close": 287.8399963378906, "volume": 445272}, {"epoch": 1782848400.0, "open": 287.8399963378906, "high": 288.07000732421875, "low": 287.79998779296875, "close": 287.9100036621094, "volume": 552565}, {"epoch": 1782848700.0, "open": 287.9100036621094, "high": 287.9700012207031, "low": 287.5400085449219, "close": 287.57000732421875, "volume": 550936}, {"epoch": 1782849000.0, "open": 287.55999755859375, "high": 288.45001220703125, "low": 287.4200134277344, "close": 288.1199951171875, "volume": 985998}, {"epoch": 1782849300.0, "open": 288.1400146484375, "high": 289.9100036621094, "low": 288.1400146484375, "close": 289.0899963378906, "volume": 5399769}]}
\ No newline at end of file
diff --git a/apps/backend/tests/test_setups.py b/apps/backend/tests/test_setups.py
new file mode 100644
index 0000000..9da859d
--- /dev/null
+++ b/apps/backend/tests/test_setups.py
@@ -0,0 +1,542 @@
+"""The touch-event scanner + case-study registry (era-5B capability 2, J-02) --
+``research/setups.py`` unit + fixture coverage. Mirrors ``test_tradability.py``'s structure: a
+small synthetic multi-session, multi-symbol ``"5m"`` fixture gives full control over exact
+expected numbers (touch detection, reaction classification, forward returns, the re-arm rule, and
+-- critically -- per-session map scoping), then the real committed AAPL fixture proves the SAME
+mechanism holds end to end on real data and satisfies J-02's pinned acceptance (the 2026-06-22
+``rejected`` event with negative forward returns).
+
+The synthetic fixture (symbol ``SYN-SETUPS-A``, six daily bars + four ``"5m"`` sessions;
+``SYN-SETUPS-B``, two daily bars + one ``"5m"`` session) is engineered so ONE resistance level
+(anchored near 250) grows a new daily member each session (2026-01-04 through 2026-01-06) while its
+INTRADAY price action differs session to session -- a clean ``rejected`` example (2026-01-04, a
+1-member band), a clean ``broke`` example (2026-01-05, a 2-member band), and a ``chopped`` example
+(2026-01-06, a 4-member band) that doubles as the intraday-density regression guard (a huge-volume,
+big-wick touch bar that fully settles back near the band by the reaction horizon). All values below
+are VERIFIED BY DIRECT COMPUTATION (printed from a real ``compute_setups`` run against this exact
+fixture), never hand-derived -- the ``test_tradability.py`` precedent, because ``compute_tradability``
+also folds in ``"5m"``-timeframe swing pivots from EARLIER sessions' own bars once enough later bars
+confirm them (see ``test_2026_01_06_session_gains_a_swing_pivot_band_2026_01_05_did_not_have`` for
+exactly this -- itself a direct, positive proof of correct per-session ``as_of`` threading, the
+module's central risk)."""
+
+from __future__ import annotations
+
+import inspect
+import json
+from datetime import datetime, timezone
+from pathlib import Path
+
+import pytest
+
+from app.config import CONFIG, Config
+from app.providers.adapters.base import RawBar
+from app.research.bars import BarStore
+from app.research.setups import BROKE, CHOPPED, REJECTED, compute_setups
+
+FIXTURE_YAHOO_DIR = Path(__file__).parent / "fixtures" / "yahoo"
+
+_DAY = 86400.0
+_FIVE_MIN = 300.0
+_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()
+
+SYM_A = "SYN-SETUPS-A"
+SYM_B = "SYN-SETUPS-B"
+
+_SMALL_HORIZONS = (2, 5)  # bars -- small so a handful of engineered 5m bars per session suffice
+
+
+def _syn_config(**overrides) -> Config:
+    fields = {"setups_panel_symbols": (SYM_A, SYM_B), "setups_forward_return_horizons_bars": _SMALL_HORIZONS}
+    fields.update(overrides)
+    return Config(**fields)
+
+
+def _daily(symbol: str, day_index: int, high: float, low: float, close: float) -> RawBar:
+    return RawBar(symbol, "1d", _BASE + day_index * _DAY, close, high, low, close, 1_000)
+
+
+def _bar5m(symbol: str, day_index: int, bar_offset: int, o: float, h: float, l: float, c: float, v: int) -> RawBar:
+    epoch = _BASE + day_index * _DAY + bar_offset * _FIVE_MIN
+    return RawBar(symbol, "5m", epoch, o, h, l, c, v)
+
+
+# --- SYN-SETUPS-A: six daily bars (days 0..5). Days 0/1 are far-apart filler (no accidental
+# clustering with the 250-ish target). Days 2/3/4/5 each add ONE new high near 250 (within the
+# default 70 bps tradability_band_width_bps of each other, so they progressively join the SAME
+# band) and a mirrored low near 150 (unused by the resistance-side tests below). -----------------
+_DAILY_A: tuple[RawBar, ...] = (
+    _daily(SYM_A, 0, 210.00, 190.00, 200.00),
+    _daily(SYM_A, 1, 215.00, 185.00, 200.00),
+    _daily(SYM_A, 2, 250.10, 150.10, 200.00),
+    _daily(SYM_A, 3, 250.20, 150.20, 200.00),
+    _daily(SYM_A, 4, 250.30, 150.30, 200.00),
+    _daily(SYM_A, 5, 250.40, 150.40, 200.00),
+)
+
+# Session 2026-01-01 (day 0): NO prior daily bar precedes it in the store -> compute_tradability's
+# basis never resolves -> an honest empty map -> zero events, regardless of this bar's own price.
+_SESSION_DAY0: tuple[RawBar, ...] = (_bar5m(SYM_A, 0, 0, 200, 205, 195, 200, 1_000),)
+
+# Session 2026-01-04 (day 3, basis = day 2's close): the resistance band is a lone 250.10 level (a
+# singleton band -- day 2 is the ONLY prior daily bar visible). The touch bar's high (250.15)
+# reaches the band; by +2 bars the close has fallen decisively below price_low*(1-30bps) -> REJECTED.
+_SESSION_DAY3: tuple[RawBar, ...] = (
+    _bar5m(SYM_A, 3, 0, 249.80, 250.15, 249.70, 250.05, 5_000),  # touch
+    _bar5m(SYM_A, 3, 1, 250.05, 250.10, 249.00, 249.20, 4_000),
+    _bar5m(SYM_A, 3, 2, 249.20, 249.30, 248.50, 248.80, 3_000),  # +2 reaction close
+    _bar5m(SYM_A, 3, 3, 248.80, 249.00, 248.00, 248.30, 3_000),
+    _bar5m(SYM_A, 3, 4, 248.30, 248.50, 247.80, 248.00, 3_000),
+    _bar5m(SYM_A, 3, 5, 248.00, 248.20, 247.50, 247.70, 3_000),  # +5 forward-return bar
+)
+
+# Session 2026-01-05 (day 4, basis = day 3's close): the band has grown to [250.10, 250.20] (2
+# members). The touch bar's range reaches into the band; by +2 bars the close has pushed decisively
+# above price_high*(1+30bps) -> BROKE.
+_SESSION_DAY4: tuple[RawBar, ...] = (
+    _bar5m(SYM_A, 4, 0, 250.00, 250.15, 249.90, 250.10, 5_000),  # touch
+    _bar5m(SYM_A, 4, 1, 250.10, 250.80, 250.05, 250.70, 4_000),
+    _bar5m(SYM_A, 4, 2, 250.70, 251.20, 250.60, 251.10, 4_000),  # +2 reaction close
+    _bar5m(SYM_A, 4, 3, 251.10, 251.50, 251.00, 251.40, 3_000),
+    _bar5m(SYM_A, 4, 4, 251.40, 251.80, 251.30, 251.70, 3_000),
+    _bar5m(SYM_A, 4, 5, 251.70, 252.00, 251.60, 251.90, 3_000),  # +5 forward-return bar
+)
+
+# Session 2026-01-06 (day 5, basis = day 4's close): the band has grown to [250.10, 250.30] (now
+# ALSO picking up a genuine "5m"-timeframe swing-pivot member at 250.15 -- see the dedicated test
+# below). The touch bar is a huge-volume (50,000), big-wick (low 245.00, far below the band) bar
+# that nonetheless settles back near the band by the reaction horizon -- CHOPPED, proving neither
+# the wick nor the volume drove the classification (only the reaction-horizon CLOSE does).
+_SESSION_DAY5: tuple[RawBar, ...] = (
+    _bar5m(SYM_A, 5, 0, 250.20, 250.25, 245.00, 250.15, 50_000),  # touch: big wick + huge volume
+    _bar5m(SYM_A, 5, 1, 250.15, 250.40, 250.00, 250.20, 2_000),
+    _bar5m(SYM_A, 5, 2, 250.20, 250.35, 250.05, 250.25, 2_000),  # +2 reaction close
+    _bar5m(SYM_A, 5, 3, 250.25, 250.40, 250.10, 250.30, 2_000),
+    _bar5m(SYM_A, 5, 4, 250.30, 250.45, 250.15, 250.35, 2_000),
+    _bar5m(SYM_A, 5, 5, 250.35, 250.50, 250.20, 250.40, 2_000),  # +5 forward-return bar
+)
+
+_FIVE_MIN_A: tuple[RawBar, ...] = _SESSION_DAY0 + _SESSION_DAY3 + _SESSION_DAY4 + _SESSION_DAY5
+
+# --- SYN-SETUPS-B: an isolated second symbol proving (a) events never cross symbols and (b) the
+# SUPPORT-side reaction branch (mirrored from the resistance-side logic above). ------------------
+_DAILY_B: tuple[RawBar, ...] = (
+    _daily(SYM_B, 0, 110.00, 90.00, 100.00),
+    _daily(SYM_B, 1, 112.00, 88.10, 100.00),
+)
+_SESSION_B_DAY2: tuple[RawBar, ...] = (
+    _bar5m(SYM_B, 2, 0, 88.50, 88.60, 88.05, 88.20, 1_000),  # touch
+    _bar5m(SYM_B, 2, 1, 88.20, 88.90, 88.15, 88.70, 800),
+    _bar5m(SYM_B, 2, 2, 88.70, 89.50, 88.60, 89.30, 800),  # +2 reaction close
+    _bar5m(SYM_B, 2, 3, 89.30, 89.60, 89.20, 89.50, 800),
+    _bar5m(SYM_B, 2, 4, 89.50, 89.80, 89.40, 89.70, 800),
+    _bar5m(SYM_B, 2, 5, 89.70, 90.00, 89.60, 89.90, 800),  # +5 forward-return bar
+)
+
+
+def _seed_full(store: BarStore) -> None:
+    store.record(
+        symbol=SYM_A, timeframe="1d", window_start_utc="2026-01-01T00:00:00Z",
+        window_end_utc="2026-01-07T00:00:00Z", feed="sip", bars=list(_DAILY_A),
+    )
+    store.record(
+        symbol=SYM_A, timeframe="5m", window_start_utc="2026-01-01T00:00:00Z",
+        window_end_utc="2026-01-07T00:00:00Z", feed="sip", bars=list(_FIVE_MIN_A),
+    )
+    store.record(
+        symbol=SYM_B, timeframe="1d", window_start_utc="2026-01-01T00:00:00Z",
+        window_end_utc="2026-01-04T00:00:00Z", feed="sip", bars=list(_DAILY_B),
+    )
+    store.record(
+        symbol=SYM_B, timeframe="5m", window_start_utc="2026-01-01T00:00:00Z",
+        window_end_utc="2026-01-04T00:00:00Z", feed="sip", bars=list(_SESSION_B_DAY2),
+    )
+
+
+def _events_for(result: dict, symbol: str, session_date: str) -> list[dict]:
+    return [e for e in result["events"] if e["symbol"] == symbol and e["session_date"] == session_date]
+
+
+def _one_event(result: dict, symbol: str, session_date: str, price_low: float) -> dict:
+    matches = [e for e in _events_for(result, symbol, session_date) if e["band"]["price_low"] == price_low]
+    assert len(matches) == 1, f"expected exactly one {symbol}/{session_date}/{price_low} event"
+    return matches[0]
+
+
+# --- Exact-value reaction coverage: rejected / broke / chopped ---------------------------------
+
+
+def test_synthetic_2026_01_04_singleton_band_touch_is_rejected_with_negative_forward_returns(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    result = compute_setups(store, _syn_config())
+
+    event = _one_event(result, SYM_A, "2026-01-04", 250.10)
+    assert event["band"]["side"] == "resistance"
+    assert event["band"]["price_high"] == 250.10
+    assert event["band"]["member_count"] == 1
+    assert event["touch_ts"] == "2026-01-04T00:00:00.000000Z"
+    assert event["touch_open"] == 249.80
+    assert event["touch_high"] == 250.15
+    assert event["touch_low"] == 249.70
+    assert event["touch_close"] == 250.05
+    assert event["touch_volume"] == 5_000
+    assert event["reaction"] == REJECTED
+    assert event["forward_returns"] == [
+        {"horizon_bars": 2, "return_fraction": pytest.approx(-0.004999000199960008)},
+        {"horizon_bars": 5, "return_fraction": pytest.approx(-0.009398120375924905)},
+    ]
+    for fr in event["forward_returns"]:
+        assert fr["return_fraction"] < 0, "a rejected event must carry negative forward returns"
+    assert event["tape_timeline"] == [], "present-but-empty until J-03 records"
+
+
+def test_synthetic_2026_01_05_two_member_band_touch_is_broke_with_positive_forward_returns(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    result = compute_setups(store, _syn_config())
+
+    event = _one_event(result, SYM_A, "2026-01-05", 250.10)
+    assert event["band"]["price_high"] == 250.20
+    assert event["band"]["member_count"] == 2
+    assert event["reaction"] == BROKE
+    assert event["forward_returns"] == [
+        {"horizon_bars": 2, "return_fraction": pytest.approx(0.003998400639744102)},
+        {"horizon_bars": 5, "return_fraction": pytest.approx(0.00719712115153943)},
+    ]
+
+
+def test_synthetic_2026_01_06_four_member_band_touch_is_chopped_despite_a_huge_wick_and_volume(tmp_path):
+    """The intraday-density regression guard: the touch bar has a 5.15-point low-side wick (245.00
+    vs a 250.10-250.30 band) and 50,000 volume -- 25x every neighbouring bar's volume in this
+    fixture -- yet the reaction reads ``chopped``, never ``rejected``, because classification reads
+    ONLY the reaction-horizon CLOSE (250.25, which clears neither band edge by the configured
+    threshold), never the touch bar's own wick extent or its volume."""
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    result = compute_setups(store, _syn_config())
+
+    event = _one_event(result, SYM_A, "2026-01-06", 250.10)
+    assert event["band"]["price_high"] == 250.30
+    assert event["band"]["member_count"] == 4
+    assert event["touch_low"] == 245.00, "the touch bar's own wick reaches far below the band"
+    assert event["touch_volume"] == 50_000, "and carries far more volume than any neighbouring bar"
+    assert event["reaction"] == CHOPPED, "neither the wick nor the volume may drive the reaction"
+    assert event["forward_returns"] == [
+        {"horizon_bars": 2, "return_fraction": pytest.approx(0.0003997601439136291)},
+        {"horizon_bars": 5, "return_fraction": pytest.approx(0.0009994003597841295)},
+    ]
+
+
+def test_synthetic_support_side_rejected_and_symbol_isolation(tmp_path):
+    """SYN-SETUPS-B exercises the mirrored SUPPORT-side reaction branch (a failed breakdown that
+    bounces back above the band reads ``rejected``, the identical DoD wording applied to the other
+    side) AND proves symbol isolation: scanning the panel (A + B together) emits B's event with
+    symbol ``SYN-SETUPS-B`` only, never conflated with any of A's resistance events above."""
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    result = compute_setups(store, _syn_config())
+
+    b_events = [e for e in result["events"] if e["symbol"] == SYM_B]
+    assert len(b_events) == 1
+    event = b_events[0]
+    assert event["session_date"] == "2026-01-03"
+    assert event["band"]["side"] == "support"
+    assert event["band"]["price_low"] == 88.10
+    assert event["band"]["price_high"] == 88.10
+    assert event["reaction"] == REJECTED
+    assert event["forward_returns"] == [
+        {"horizon_bars": 2, "return_fraction": pytest.approx(0.01247165532879812)},
+        {"horizon_bars": 5, "return_fraction": pytest.approx(0.01927437641723359)},
+    ]
+    for fr in event["forward_returns"]:
+        assert fr["return_fraction"] > 0, "a rejected SUPPORT band bounces price back UP"
+
+    # No A-symbol event is ever misattributed to B, and vice versa.
+    assert all(e["symbol"] in (SYM_A, SYM_B) for e in result["events"])
+    a_events = [e for e in result["events"] if e["symbol"] == SYM_A]
+    assert len(a_events) == 4  # the three resistance events above, plus the 247.5 event below
+    assert all(e["symbol"] != SYM_B for e in a_events)
+
+
+# --- The central risk: per-session `as_of` threading (never a shared/fixed value) ---------------
+
+
+def test_2026_01_06_session_gains_a_swing_pivot_band_2026_01_05_did_not_have(tmp_path):
+    """A DIRECT, positive proof of correct per-session threading -- the exact bug class the module
+    docstring's "central risk" describes. 2026-01-04's session (2026-01-04 5m bar 5, low=247.50) is
+    visible to BOTH the 2026-01-05 and 2026-01-06 maps, but it only CONFIRMS as a "5m"-timeframe
+    swing-pivot low once its right-hand neighbour (2026-01-05's own bar 0) is ALSO visible -- which
+    happens for the 2026-01-06 map (basis = 2026-01-05's close, so ALL of 2026-01-05's bars are
+    visible) but NOT for the 2026-01-05 map (basis = 2026-01-04's close, so 2026-01-05's OWN bars
+    are correctly excluded). A buggy implementation sharing one fixed/latest `as_of` across the
+    whole walk would show this EXTRA 247.50 band on EVERY session alike; the correct, per-session
+    implementation shows it ONLY from 2026-01-06 onward."""
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    result = compute_setups(store, _syn_config())
+
+    day4_events = _events_for(result, SYM_A, "2026-01-05")
+    assert len(day4_events) == 1, "2026-01-05's map must NOT yet see the 247.50 pivot"
+    assert {e["band"]["price_low"] for e in day4_events} == {250.10}
+
+    day5_events = _events_for(result, SYM_A, "2026-01-06")
+    assert len(day5_events) == 2, "2026-01-06's map gains the newly-confirmed 247.50 pivot band"
+    assert {e["band"]["price_low"] for e in day5_events} == {247.50, 250.10}
+    pivot_event = _one_event(result, SYM_A, "2026-01-06", 247.50)
+    assert pivot_event["band"]["price_high"] == 247.50
+    assert pivot_event["band"]["member_count"] == 1
+    assert pivot_event["band"]["members"][0]["timeframe"] == "5m"
+    assert pivot_event["band"]["members"][0]["type"] == "swing-pivot"
+
+
+def test_no_lookahead_extending_the_5m_series_forward_never_changes_an_earlier_session_event(tmp_path):
+    """The ``test_tradability.py``
+    ``test_no_lookahead_bars_after_the_basis_never_affect_the_result`` technique, applied one layer
+    up: a store truncated to ONLY 2026-01-04's own session (plus the daily bars its OWN map needs)
+    must emit a BYTE-IDENTICAL 2026-01-04 event to a store that ALSO holds the later 2026-01-05 and
+    2026-01-06 sessions -- extending the scan forward never mutates an already-emitted event."""
+    full_store = BarStore(tmp_path / "full")
+    _seed_full(full_store)
+    full_result = compute_setups(full_store, _syn_config())
+    full_event = _one_event(full_result, SYM_A, "2026-01-04", 250.10)
+
+    truncated_store = BarStore(tmp_path / "truncated")
+    truncated_store.record(
+        symbol=SYM_A, timeframe="1d", window_start_utc="2026-01-01T00:00:00Z",
+        window_end_utc="2026-01-04T00:00:00Z", feed="sip", bars=list(_DAILY_A[:3]),
+    )
+    truncated_store.record(
+        symbol=SYM_A, timeframe="5m", window_start_utc="2026-01-01T00:00:00Z",
+        window_end_utc="2026-01-04T00:00:00Z", feed="sip", bars=list(_SESSION_DAY0 + _SESSION_DAY3),
+    )
+    truncated_config = Config(setups_panel_symbols=(SYM_A,), setups_forward_return_horizons_bars=_SMALL_HORIZONS)
+    truncated_result = compute_setups(truncated_store, truncated_config)
+    assert len(truncated_result["events"]) == 1, "the truncated store must only ever emit 2026-01-04's event"
+    truncated_event = _one_event(truncated_result, SYM_A, "2026-01-04", 250.10)
+
+    assert json.dumps(full_event, sort_keys=True) == json.dumps(truncated_event, sort_keys=True)
+
+
+def test_repeat_scan_determinism(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    config = _syn_config()
+    first = compute_setups(store, config)
+    second = compute_setups(BarStore(tmp_path / "bars"), config)
+    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
+    assert len(first["events"]) >= 1, "the proof must exercise at least one real event"
+
+
+# --- Honest, distinct empty states (never one fabricated event) --------------------------------
+
+
+def test_session_with_no_derivable_prior_basis_contributes_no_events(tmp_path):
+    """2026-01-01 (day 0) has NO daily bar strictly before it in the store -- compute_tradability's
+    basis never resolves, so its map is honestly empty and this session contributes ZERO events,
+    regardless of its own 5m bar's price."""
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)
+    result = compute_setups(store, _syn_config())
+    assert _events_for(result, SYM_A, "2026-01-01") == []
+
+
+def test_symbol_with_no_5m_series_at_all_contributes_no_events(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    _seed_full(store)  # never records anything for "SYN-SETUPS-NEVER-RECORDED"
+    result = compute_setups(store, _syn_config(setups_panel_symbols=(SYM_A, SYM_B, "SYN-SETUPS-NEVER-RECORDED")))
+    assert all(e["symbol"] != "SYN-SETUPS-NEVER-RECORDED" for e in result["events"])
+
+
+def test_symbol_with_5m_series_but_no_1d_series_contributes_no_events(tmp_path):
+    """A "5m" series with no companion "1d" series can never resolve a morning-markup basis
+    (compute_tradability's own honest-empty state) -- so it contributes no events, never a crash."""
+    store = BarStore(tmp_path / "bars")
+    store.record(
+        symbol="SYN-SETUPS-NO-DAILY", timeframe="5m", window_start_utc="2026-01-04T00:00:00Z",
+        window_end_utc="2026-01-04T01:00:00Z", feed="sip",
+        bars=[_bar5m("SYN-SETUPS-NO-DAILY", 3, 0, 100, 105, 95, 100, 1_000)],
+    )
+    result = compute_setups(store, _syn_config(setups_panel_symbols=("SYN-SETUPS-NO-DAILY",)))
+    assert result == {"events": []}
+
+
+def test_symbol_with_1d_series_but_no_5m_series_contributes_no_events(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    store.record(
+        symbol="SYN-SETUPS-NO-5M", timeframe="1d", window_start_utc="2026-01-01T00:00:00Z",
+        window_end_utc="2026-01-02T00:00:00Z", feed="sip",
+        bars=[_daily("SYN-SETUPS-NO-5M", 0, 100, 90, 95)],
+    )
+    result = compute_setups(store, _syn_config(setups_panel_symbols=("SYN-SETUPS-NO-5M",)))
+    assert result == {"events": []}
+
+
+def test_empty_bar_store_is_an_honest_empty_registry(tmp_path):
+    store = BarStore(tmp_path / "bars")  # never recorded anything at all
+    result = compute_setups(store, _syn_config())
+    assert result == {"events": []}
+
+
+# --- No magic numbers: every setups parameter is config-sourced --------------------------------
+
+
+def test_setups_parameters_are_config_sourced_no_magic_numbers():
+    assert isinstance(CONFIG.setups_panel_symbols, tuple) and len(CONFIG.setups_panel_symbols) == 12
+    assert CONFIG.setups_panel_symbols == (
+        "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "AMD", "NFLX", "SPY", "QQQ", "JPM",
+    )
+    assert isinstance(CONFIG.setups_forward_return_horizons_bars, tuple)
+    assert len(CONFIG.setups_forward_return_horizons_bars) >= 1
+    assert all(isinstance(h, int) and h > 0 for h in CONFIG.setups_forward_return_horizons_bars)
+    assert isinstance(CONFIG.setups_reaction_threshold_bps, float) and CONFIG.setups_reaction_threshold_bps > 0
+    assert isinstance(CONFIG.setups_max_events_per_band_per_session, int)
+    assert CONFIG.setups_max_events_per_band_per_session >= 1
... [diff_bound] apps/backend/tests/test_setups.py: 148 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_setups_api.py b/apps/backend/tests/test_setups_api.py
new file mode 100644
index 0000000..3e59af3
--- /dev/null
+++ b/apps/backend/tests/test_setups_api.py
@@ -0,0 +1,258 @@
+"""The ``GET /research/setups`` + ``GET /research/setups/{id}`` endpoints (era-5B capability 2,
+J-02) -- route-level integration. Mirrors ``test_tradability_api.py``'s ``ctx`` fixture (TestClient
++ temp bar dir): the committed real AAPL fixtures are seeded directly into the temp bar dir (the
+``test_tradability_api.py`` / ``test_mcp_server.py`` technique), then the REAL routes are read --
+the full request path, not a direct module call (``test_setups.py`` covers the pure computation's
+exact values in isolation, including the SAME pinned 2026-06-22 event this file re-proves through
+HTTP). Routes read the process-global ``CONFIG`` (never a per-request override, mirroring
+``get_tradability``/``get_levels``), so every route-level fixture here must work with the SHIPPED
+default ``setups_panel_symbols`` (the real 12-symbol panel) -- AAPL is the only panel symbol with
+bars seeded, so every other panel symbol honestly contributes zero events.
+"""
+
+from __future__ import annotations
+
+import json
+from datetime import datetime
+from pathlib import Path
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG
+from app.main import app, get_market_adapter, manager
+from app.providers.adapters.base import RawBar
+from app.research.bars import BarStore
+from app.research.routes import ResearchRegistry, set_registry
+from app.research.setups import compute_setups
+from app.research.store import JournalStore
+
+YAHOO_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "yahoo"
+AAPL_DAILY_FIXTURE = "AAPL_1d_20260101_20260626.json"
+AAPL_5M_SETUPS_FIXTURE = "AAPL_5m_20260615_20260630.json"
+
+
+@pytest.fixture
+def ctx(tmp_path, monkeypatch):
+    bar_dir = tmp_path / "bars"
+    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(bar_dir))
+    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    registry = ResearchRegistry(store, CONFIG)
+    set_registry(registry)
+    manager.set_on_engine_created(registry.on_engine_created)
+    with TestClient(app) as client:
+        yield client, bar_dir
+    for ticker in list(manager._engines.keys()):
+        manager.stop(ticker)
+    manager.set_on_engine_created(None)
+    set_registry(None)
+    app.dependency_overrides.pop(get_market_adapter, None)
+    store.close()
+
+
+def _seed_yahoo_fixture_into_bar_dir(bar_dir: Path, fixture_name: str) -> None:
+    bar_dir.mkdir(parents=True, exist_ok=True)  # BarStore only creates it lazily inside `record()`
+    fixture = json.loads((YAHOO_FIXTURE_DIR / fixture_name).read_text())
+    bars = [
+        RawBar(
+            fixture["symbol"], fixture["timeframe"], b["epoch"],
+            b["open"], b["high"], b["low"], b["close"], b["volume"],
+        )
+        for b in fixture["bars"]
+    ]
+    BarStore(bar_dir).record(
+        symbol=fixture["symbol"], timeframe=fixture["timeframe"],
+        window_start_utc=fixture["start"], window_end_utc=fixture["end"],
+        feed="yahoo", bars=bars,
+    )
+
+
+def _seed_aapl(bar_dir: Path) -> None:
+    _seed_yahoo_fixture_into_bar_dir(bar_dir, AAPL_DAILY_FIXTURE)
+    _seed_yahoo_fixture_into_bar_dir(bar_dir, AAPL_5M_SETUPS_FIXTURE)
+
+
+_EVENT_FIELDS = {
+    "id", "symbol", "session_date", "band", "touch_ts", "touch_open", "touch_high",
+    "touch_low", "touch_close", "touch_volume", "reaction", "forward_returns", "tape_timeline",
+}
+
+
+# --- Happy path: the real route wires through to compute_setups verbatim -----------------------
+
+
+def test_list_setups_happy_path_through_the_real_route(ctx):
+    client, _bar_dir = ctx
+    _seed_aapl(_bar_dir)
+
+    r = client.get("/research/setups")
+    assert r.status_code == 200
+    body = r.json()
+    assert isinstance(body["events"], list) and len(body["events"]) >= 1
+    for event in body["events"]:
+        assert set(event) == _EVENT_FIELDS
+        assert event["symbol"] == "AAPL"  # only panel symbol with bars seeded
+        assert event["reaction"] in ("rejected", "broke", "chopped")
+        assert event["tape_timeline"] == []
+
+
+def test_list_setups_rest_matches_module_output_byte_for_byte(ctx):
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+
+    r = client.get("/research/setups")
+    assert r.status_code == 200
+
+    direct = compute_setups(BarStore(bar_dir), CONFIG)
+    assert r.json() == direct
+
+
+def test_no_bar_series_at_all_is_an_honest_empty_registry(ctx):
+    client, _bar_dir = ctx  # nothing seeded this run
+    r = client.get("/research/setups")
+    assert r.status_code == 200
+    assert r.json() == {"events": []}
+
+
+# --- The committed real AAPL fixture: J-02's pinned acceptance through the REAL route -----------
+
+
+def test_get_setups_aapl_pinned_2026_06_22_event_through_the_real_route(ctx):
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+
+    r = client.get("/research/setups", params={"symbol": "AAPL", "reaction": "rejected"})
+    assert r.status_code == 200
+    day_events = [e for e in r.json()["events"] if e["session_date"] == "2026-06-22"]
+    assert day_events, "the pinned 2026-06-22 rejected event must be present"
+
+    pinned = next(
+        e for e in day_events
+        if e["band"]["side"] == "resistance"
+        and e["band"]["price_low"] <= 300.48 and e["band"]["price_high"] >= 302.07
+    )
+    assert pinned["reaction"] == "rejected"
+    assert len(pinned["forward_returns"]) == 2
+    for fr in pinned["forward_returns"]:
+        assert fr["return_fraction"] is not None and fr["return_fraction"] < 0
+
+
+# --- Filters: symbol (free-form) / reaction (enum) / band_class (enum), AND-combined ------------
+
+
+def test_filter_by_symbol_matches_only_that_symbol(ctx):
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+
+    matched = client.get("/research/setups", params={"symbol": "AAPL"})
+    assert matched.status_code == 200
+    assert len(matched.json()["events"]) >= 1
+
+    unmatched = client.get("/research/setups", params={"symbol": "MSFT"})
+    assert unmatched.status_code == 200
+    assert unmatched.json()["events"] == [], "a well-formed but unmatched symbol is honest empty, never an error"
+
+
+def test_filter_by_symbol_is_case_insensitive(ctx):
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+    lower = client.get("/research/setups", params={"symbol": "aapl"})
+    upper = client.get("/research/setups", params={"symbol": "AAPL"})
+    assert lower.status_code == upper.status_code == 200
+    assert lower.json() == upper.json()
+
+
+def test_blank_symbol_normalizes_to_absent_same_as_no_param(ctx):
+    """The ``list_bar_series`` era-5 J-05 audit-fixed precedent: a present-but-blank ``?symbol=``
+    takes the EXACT SAME path as a true no-param call -- never a silently-different filtered (and
+    in this case empty) result."""
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+    blank = client.get("/research/setups", params={"symbol": ""})
+    absent = client.get("/research/setups")
+    assert blank.status_code == absent.status_code == 200
+    assert blank.json() == absent.json()
+
+
+def test_filter_by_reaction_unknown_value_is_422(ctx):
+    client, _bar_dir = ctx
+    r = client.get("/research/setups", params={"reaction": "bullish"})
+    assert r.status_code == 422
+    assert "reaction" in r.json()["detail"]
+
+
+def test_filter_by_reaction_valid_value_narrows_results(ctx):
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+    all_events = client.get("/research/setups").json()["events"]
+    reactions_present = {e["reaction"] for e in all_events}
+    assert reactions_present, "the seeded fixture must produce at least one event"
+    target = next(iter(reactions_present))
+
+    r = client.get("/research/setups", params={"reaction": target})
+    assert r.status_code == 200
+    filtered = r.json()["events"]
+    assert filtered and all(e["reaction"] == target for e in filtered)
+    assert len(filtered) == len([e for e in all_events if e["reaction"] == target])
+
+
+def test_filter_by_band_class_unknown_value_is_422(ctx):
+    client, _bar_dir = ctx
+    r = client.get("/research/setups", params={"band_class": "Z"})
+    assert r.status_code == 422
+    assert "band_class" in r.json()["detail"]
+
+
+def test_filter_by_band_class_valid_value_narrows_results(ctx):
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+    all_events = client.get("/research/setups").json()["events"]
+    classes_present = {e["band"]["class"] for e in all_events if e["band"]["class"] is not None}
+    assert classes_present, "the seeded fixture must produce at least one classified band"
+    target = next(iter(classes_present))
+
+    r = client.get("/research/setups", params={"band_class": target})
+    assert r.status_code == 200
+    filtered = r.json()["events"]
+    assert filtered and all(e["band"]["class"] == target for e in filtered)
+
+
+def test_combined_filters_are_and_combined(ctx):
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+    r = client.get("/research/setups", params={"symbol": "AAPL", "reaction": "rejected"})
+    assert r.status_code == 200
+    assert all(e["symbol"] == "AAPL" and e["reaction"] == "rejected" for e in r.json()["events"])
+
+    r2 = client.get("/research/setups", params={"symbol": "MSFT", "reaction": "rejected"})
+    assert r2.status_code == 200
+    assert r2.json()["events"] == []
+
+
+# --- Detail: GET /research/setups/{id} -----------------------------------------------------------
+
+
+def test_get_setup_detail_matches_the_list_entry(ctx):
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+    listed = client.get("/research/setups").json()["events"]
+    assert listed
+    target = listed[0]
+
+    r = client.get(f"/research/setups/{target['id']}")
+    assert r.status_code == 200
+    assert r.json() == {"event": target}
+
+
+def test_get_setup_unknown_id_is_404(ctx):
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+    r = client.get("/research/setups/does-not-exist")
+    assert r.status_code == 404
+    assert "does-not-exist" in r.json()["detail"]
+
+
+def test_get_setup_unknown_id_on_an_empty_store_is_still_404_never_an_error(ctx):
+    client, _bar_dir = ctx  # nothing seeded
+    r = client.get("/research/setups/anything")
+    assert r.status_code == 404
```
