# Iteration diff (bounded)

Files changed: 12. Shown in full: 8.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/fixtures/yahoo/AAPL_1d_20260101_20260626.json` (583 lines not shown)
- `apps/backend/tests/fixtures/yahoo/AAPL_1h_20260601_20260618.json` (399 lines not shown)
- `apps/backend/tests/fixtures/yahoo/AAPL_5m_20260601_20260618.json` (8351 lines not shown)
- `apps/backend/tests/test_tradability.py` (208 lines not shown)

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 9a6f0a6..726a22a 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -1158,6 +1158,66 @@ class Config:
     # proximity (which each level's own ``touch_count`` already captures).
     sr_confluence_class_b_min_timeframes: int = 2
 
+    # --- Era 5B: the tradable level map (capability 1, J-01) -- RESEARCH DEFAULTS, the SAME
+    # ``sr_pivot_lookback`` discipline: every research value lives in config with its rationale
+    # documented HERE, no literal in ``research/tradability.py``. Namespaced ``tradability_*`` so
+    # it never collides with the ``sr_*`` family directly above (J-02/J-03 raw levels/zones --
+    # read-only inputs this NEW derived lens consumes VERBATIM, never mutates) or the unrelated
+    # ``structure_tape_*`` strategy namespace below.
+    #
+    # BAND CAP K (per side): goal.md's "cluster levels into at most K bands per side" -- K <= 5 so
+    # the served map is never more than 10 bands total (5 support + 5 resistance), the headline
+    # 1,800-levels -> handful-of-bands distillation this era exists to prove.
+    tradability_band_cap_per_side: int = 5
+    # BAND WIDTH (basis points of a band's ANCHOR price -- its first, lowest-priced member; the
+    # SAME anchor-fixed-scan TECHNIQUE ``sr_confluence_band_bps`` drives in ``levels.py``, reused
+    # only as a technique -- this is a SEPARATE, deliberately WIDER tolerance for this coarser
+    # lens): raw levels within ``price * tradability_band_width_bps / 10_000`` of a band's anchor
+    # join the SAME band. Wider than ``sr_confluence_band_bps`` (20.0) because a TRADABLE band
+    # exists to merge nearby REAL rejection highs into ONE wall a trader would mark -- the pinned
+    # AAPL cluster (300.48 / 302.07) sits ~53 bps apart, wider than a raw confluence zone would
+    # ever join. Calibrated against the committed AAPL fixture (verified by direct computation): at
+    # 70 bps the pinned cluster joins one band without smearing together the fixture's other,
+    # clearly distinct price levels into an uninformatively wide band.
+    tradability_band_width_bps: float = 70.0
+    # QUALITY-SCORE WEIGHTS: the four config-owned factors goal.md names (multi-timeframe breadth,
+    # DAILY touch count, recency, round-number confluence), combined as a weighted sum -- a
+    # dict (not four bare floats) so a weight lookup can never silently fall back to a fabricated
+    # default, the SAME ``sr_timeframe_weights`` discipline. TOUCH COUNT here is the DAILY (``"1d"``)
+    # touch count ONLY (see ``tradability.py._quality_score``) -- goal.md's "daily touch count",
+    # never a sum across every timeframe: on REAL multi-timeframe data it is the PRIMARY
+    # discriminator that lifts a genuine multi-day rejection wall (the pinned AAPL 300-302 band's
+    # daily series rejected it dozens of times) above the far more numerous but individually shallow
+    # intraday (5m/1h) levels clustered near the current price -- summing every member's touch_count
+    # instead inverts that, letting intraday VOLUME outscore the wall. ROUND NUMBER is weighted
+    # heavily (goal.md pins the psychological 300 level as a first-class signal, not a tiebreaker)
+    # and RECENCY meaningfully (a wall that rejected price last week matters more than one from
+    # January); TIMEFRAME BREADTH rewards cross-timeframe agreement (intraday members still count
+    # here even though they do not feed the daily touch total). Calibrated + regression-guarded
+    # against BOTH the committed daily-only AAPL fixture AND a committed multi-timeframe
+    # (1d/1h/4h/5m/1w) slice in ``tests/test_tradability.py`` (the ``levels.py`` class-A
+    # multi-timeframe-fixture precedent).
+    tradability_quality_weights: dict = field(
+        default_factory=lambda: {
+            "timeframe_breadth": 10.0,
+            "touch_count": 2.0,
+            "recency": 15.0,
+            "round_number": 20.0,
+        }
+    )
+    # ROUND-NUMBER RULE: a band is flagged iff either edge sits within
+    # ``tradability_round_number_tolerance_bps`` of a multiple of ``tradability_round_number_increment``
+    # -- goal.md's own example ("the 300 wall IS a round number") names $50 increments (300 is a
+    # multiple of 50, 100, AND 25 alike; 50 is the tightest of the common round increments that
+    # still flags 300, so it never over-flags nearby non-round bands). The tolerance is the SAME
+    # order of magnitude as ``sr_touch_tolerance_bps``'s "relative to the instrument's price level"
+    # discipline, wide enough that a band edge a few ticks off an exact round number (a real level
+    # rarely prints on the EXACT round price) still honestly flags -- calibrated against the
+    # committed AAPL fixture: the pinned band's low edge (300.48) is verified by direct computation
+    # to sit within tolerance of 300.
+    tradability_round_number_increment: float = 50.0
+    tradability_round_number_tolerance_bps: float = 50.0
+
     # --- Structure-and-tape era: the `structure_tape` STRATEGY (era-4 capability 4, J-04; Data
     # Contract row 41) -- RESEARCH DEFAULTS, the SAME ``sr_pivot_lookback`` discipline: every
     # research value lives in config with its rationale documented HERE, no literal in
@@ -1516,6 +1576,22 @@ class Config:
             "sr_confluence_band_bps",
             "sr_confluence_class_a_min_timeframes",
             "sr_confluence_class_b_min_timeframes",
+            # The tradable-level-map band cap / band width / quality weights / round-number rule
+            # (era-5B capability 1, J-01): the IDENTICAL ``sr_pivot_lookback`` rationale directly
+            # above -- the tradable map is a SEPARATE, additive derived-lens computation over
+            # ``levels.py``'s frozen output (never stamped with, or compared across, a
+            # ``config_fingerprint`` anywhere), so two journals identical in every FINGERPRINTED
+            # threshold but configured with a different band cap, band width, quality weight, or
+            # round-number rule MUST share a fingerprint (else every temp-config test of these
+            # brand-new, unrelated parameters would mint a different fingerprint and falsely
+            # fragment the tape/backtest/PnL pools those OTHER thresholds exist to protect).
+            # Pinned by a fingerprint-stability test + the real-threshold counter-test in
+            # ``tests/test_tradability.py``.
+            "tradability_band_cap_per_side",
+            "tradability_band_width_bps",
+            "tradability_quality_weights",
+            "tradability_round_number_increment",
+            "tradability_round_number_tolerance_bps",
             "journal_list_default_limit",
             "journal_list_max_limit",
             "analytics_min_sample_size",
diff --git a/apps/backend/app/mcp/__init__.py b/apps/backend/app/mcp/__init__.py
index 321865d..38b57e6 100644
--- a/apps/backend/app/mcp/__init__.py
+++ b/apps/backend/app/mcp/__init__.py
@@ -17,8 +17,8 @@ Result contract (locked by ``tests/test_mcp_server.py``):
     <path>"``, ``isError`` true. Every registered tool's endpoint has shipped (``datasets`` at
     (era-3) J-02, ``backtests`` at J-03, ``pnl_ledger`` at J-04; ``/research/profiles`` — reached
     via ``get_endpoint`` — at J-05; ``bars`` at era-4 J-01; ``levels`` at era-4 J-02; ``strategies``
-    at era-4 J-04); an allowlisted-but-UNKNOWN path (any unshipped ``/research/*``) still surfaces
-    the backend's honest 404 this way — never placeholder data.
+    at era-4 J-04; ``tradability`` at era-5B J-01); an allowlisted-but-UNKNOWN path (any unshipped
+    ``/research/*``) still surfaces the backend's honest 404 this way — never placeholder data.
   * backend unreachable — an explicit tool error naming the base URL and the failure
     (``BackendUnreachableError``); NEVER cached or fabricated data (no cache, no retry loop,
     no offline snapshot exists anywhere in this module).
@@ -107,6 +107,12 @@ _TAPE_PATHS: dict[str, str] = {
 _LEVELS_TOOL = "levels"
 _LEVELS_PATH = "/research/levels"
 
+# `tradability` (era-5B J-01) is the IDENTICAL two-required-param shape as `levels` directly above
+# (`symbol` + `as_of`) -- its own name + path constants, sharing the same dedicated branch in
+# `_request_path` (see below) rather than a third near-duplicate branch.
+_TRADABILITY_TOOL = "tradability"
+_TRADABILITY_PATH = "/research/tradability"
+
 _TICKER_PROPERTY = {
     "type": "string",
     "description": "Ticker symbol as watched on the backend, e.g. SIM-BUYER.",
@@ -207,6 +213,26 @@ TOOLS: tuple[types.Tool, ...] = (
             ("symbol", "as_of"),
         ),
     ),
+    types.Tool(
+        name="tradability",
+        description=(
+            "Read-only proxy of GET /research/tradability — the tradable level map (a lens over "
+            "the frozen levels/confluence-zone computation): at most a handful of quality-scored "
+            "support/resistance price bands per symbol, computed under morning-markup as-of "
+            "discipline (price range, side, quality score, member levels, round-number flag, "
+            "inherited A/B/C class) for one symbol as of one UTC instant, JSON verbatim."
+        ),
+        inputSchema=_object_schema(
+            {
+                "symbol": {"type": "string", "description": "Symbol, e.g. AAPL."},
+                "as_of": {
+                    "type": "string",
+                    "description": "UTC ISO-8601 instant, e.g. 2026-06-22T15:00:00Z.",
+                },
+            },
+            ("symbol", "as_of"),
+        ),
+    ),
     types.Tool(
         name="backtests",
         description=(
@@ -306,14 +332,15 @@ def _request_path(name: str, arguments: dict) -> str:
         if name == "tape_history" and arguments.get("bar") is not None:
             path += f"?bar={arguments['bar']}"
         return path
-    if name == _LEVELS_TOOL:
+    if name in (_LEVELS_TOOL, _TRADABILITY_TOOL):
         symbol = arguments.get("symbol")
         as_of = arguments.get("as_of")
         if not isinstance(symbol, str) or not symbol:
             raise ToolArgumentError(f"tool {name!r} requires a non-empty string 'symbol' argument")
         if not isinstance(as_of, str) or not as_of:
             raise ToolArgumentError(f"tool {name!r} requires a non-empty string 'as_of' argument")
-        return f"{_LEVELS_PATH}?symbol={quote(symbol, safe='')}&as_of={quote(as_of, safe='')}"
+        path = _LEVELS_PATH if name == _LEVELS_TOOL else _TRADABILITY_PATH
+        return f"{path}?symbol={quote(symbol, safe='')}&as_of={quote(as_of, safe='')}"
     if name == "get_endpoint":
         path = arguments.get("path")
         refusal = allowlist_refusal(path)
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index 6412e56..d16b3a3 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -50,6 +50,7 @@ from .bars import (
     EmptyBarWindowError,
 )
 from .levels import compute_levels
+from .tradability import compute_tradability
 from .datasets import (
     VALID_SOURCE_KINDS as DATASET_SOURCE_KINDS,
     VALID_SPLITS,
@@ -1798,6 +1799,38 @@ def get_levels(symbol: str, as_of: str, store: BarStore = Depends(get_bar_store)
     return {"symbol": normalized_symbol, "as_of": as_of, **result}
 
 
+# --- The tradable level map (era-5B capability 1, J-01) ----------------------------------------
+# ONE route: GET /research/tradability?symbol=<S>&as_of=<ISO-T>. ``research/tradability.py`` is the
+# sole computer of the tradable level map -- a LENS over ``compute_levels``' frozen output (never a
+# second levels engine); this route only parses/validates the query params and serves the module's
+# output VERBATIM (single source of truth -- the MCP `tradability` tool proxies this
+# byte-identically; no second computation path). Mirrors ``get_levels`` immediately above
+# byte-for-byte in structure (parse-ISO-once-then-return-verbatim).
+
+
+@router.get("/tradability")
+def get_tradability(symbol: str, as_of: str, store: BarStore = Depends(get_bar_store)) -> dict:
+    """The tradable level map (bands: price range, side, quality score, member levels,
+    round-number flag, inherited A/B/C class) for ``symbol`` as of ``as_of``, computed under
+    morning-markup as-of discipline from the frozen ``compute_levels`` output. ``symbol``/``as_of``
+    are both REQUIRED query params (FastAPI 422s a missing one before this body runs); an empty
+    ``symbol`` or a malformed ``as_of`` are explicit 422s here (never a silent "now" default, which
+    would leak lookahead) -- the identical ``get_levels`` discipline. A symbol with no recorded bar
+    series at all, and a symbol with series but nothing derivable (no daily series to resolve a
+    basis from, or no prior session yet), are honest distinct states -- see
+    ``compute_tradability``'s ``no_bar_series_for_symbol`` flag and ``basis_as_of`` (``null`` when
+    no basis could be resolved) -- never one ambiguous bare empty ``bands`` array."""
+    if not symbol:
+        raise HTTPException(status_code=422, detail="a tradability query requires a symbol")
+    try:
+        as_of_epoch = parse_utc_epoch(as_of)
+    except ValueError:
+        raise HTTPException(status_code=422, detail="as_of must be an ISO date-time")
+    normalized_symbol = symbol.strip().upper()
+    result = compute_tradability(store, normalized_symbol, as_of_epoch, CONFIG)
+    return {"symbol": normalized_symbol, "as_of": as_of, **result}
+
+
 # --- Deterministic backtests (era-3 capability 4, J-03) --------------------------------------------
 # Exactly FOUR routes (Product Shape): create+start, list, detail, cancel — mirroring studies.
 # The backtest runner (app/research/backtests.py) is Data Contract row 31's single computer; these
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index f75bdf8..7768e62 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -43,9 +43,9 @@ from app.research.bars import BarStore
 BACKEND_DIR = Path(__file__).resolve().parents[1]
 
 # Capability 6, verbatim — order and content are the advertised contract. ``bars`` (era-4 J-01),
-# ``levels`` (era-4 J-02), and ``strategies`` (era-4 J-04) are the newest additions, each
-# positioned right after its dependency-order sibling (the same store/registry+route+MCP shape,
-# mirrored end to end).
+# ``levels`` (era-4 J-02), ``strategies`` (era-4 J-04), and ``tradability`` (era-5B J-01) are the
+# newest additions, each positioned right after its dependency-order sibling (the same
+# store/registry+route+MCP shape, mirrored end to end).
 EXPECTED_TOOLS = (
     "tape_state",
     "tape_features",
@@ -56,6 +56,7 @@ EXPECTED_TOOLS = (
     "datasets",
     "bars",
     "levels",
+    "tradability",
     "backtests",
     "strategies",
     "pnl_ledger",
@@ -378,6 +379,59 @@ async def test_levels_tool_requires_both_arguments(monkeypatch):
         await call_tool("levels", {})
 
 
+@pytest.mark.anyio
+async def test_tradability_tool_byte_identical_on_a_non_empty_live_result(mcp_env, backend_paths):
+    """``tradability`` (era-5B J-01) ships in the SAME iteration as its endpoint -- the ``bars``
+    J-01 / ``levels`` J-02 precedent: seed the live backend's bar directory with the committed
+    real AAPL daily fixture (``BarStore.record()`` directly, the ``test_levels_tool_...
+    _on_the_yahoo_fixture`` technique -- this test's backend is a SEPARATE subprocess, so an
+    in-process ``yfinance.Ticker`` monkeypatch seam is not reachable here), then prove the
+    two-argument tool's JSON is byte-identical to its curl equivalent on a NON-EMPTY result,
+    including J-01's pinned AAPL 2026-06-22 acceptance (the top resistance band containing both
+    300.48 and 302.07), so this proxy proof meaningfully covers real bands (not a vacuous empty
+    match)."""
+    bar_dir = Path(backend_paths["TAPEOLOGY_BAR_DIR"])
+    store = BarStore(bar_dir)
+    fixture = json.loads((YAHOO_FIXTURE_DIR / "AAPL_1d_20260101_20260626.json").read_text())
+    bars = [
+        RawBar(
+            fixture["symbol"], fixture["timeframe"], b["epoch"],
+            b["open"], b["high"], b["low"], b["close"], b["volume"],
+        )
+        for b in fixture["bars"]
+    ]
+    store.record(
+        symbol=fixture["symbol"], timeframe=fixture["timeframe"],
+        window_start_utc=fixture["start"], window_end_utc=fixture["end"],
+        feed="yahoo", bars=bars,
+    )
+
+    as_of = "2026-06-22T15:00:00Z"
+    result = await call_tool("tradability", {"symbol": "AAPL", "as_of": as_of})
+    rest = httpx.get(f"{mcp_env}/research/tradability", params={"symbol": "AAPL", "as_of": as_of}, timeout=5.0)
+    assert rest.status_code == 200
+    body = rest.json()
+    assert body["no_bar_series_for_symbol"] is False
+    assert len(body["bands"]) >= 1, "the live result must be non-empty for this proof"
+    resistance = [b for b in body["bands"] if b["side"] == "resistance"]
+    pinned = next(b for b in resistance if b["price_low"] <= 300.48 and b["price_high"] >= 302.07)
+    assert resistance.index(pinned) in (0, 1)
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "tradability not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_tradability_tool_requires_both_arguments(monkeypatch):
+    monkeypatch.setenv("TAPEOLOGY_API_BASE", _dead_base())
+    with pytest.raises(ToolArgumentError):
+        await call_tool("tradability", {"as_of": "2026-06-22T15:00:00Z"})
+    with pytest.raises(ToolArgumentError):
+        await call_tool("tradability", {"symbol": "AAPL"})
+    with pytest.raises(ToolArgumentError):
+        await call_tool("tradability", {})
+
+
 @pytest.mark.anyio
 async def test_backtests_tool_byte_identical_on_a_non_empty_live_list(mcp_env):
     """J-03 flips ``backtests`` from honest 404 to live data with ZERO MCP code changes (the
@@ -584,6 +638,7 @@ async def test_backend_down_every_tool_raises_an_explicit_error(monkeypatch):
         "tape_features": {"ticker": "SIM-BUYER"},
         "tape_history": {"ticker": "SIM-BUYER"},
         "levels": {"symbol": "PG", "as_of": "2026-06-09T21:00:00Z"},
+        "tradability": {"symbol": "AAPL", "as_of": "2026-06-22T15:00:00Z"},
         "get_endpoint": {"path": "/meta/ui-routes"},
     }
     for name in EXPECTED_TOOLS:
diff --git a/apps/backend/app/research/tradability.py b/apps/backend/app/research/tradability.py
new file mode 100644
index 0000000..8a39087
--- /dev/null
+++ b/apps/backend/app/research/tradability.py
@@ -0,0 +1,382 @@
+"""The tradable level map (era-5B capability 1, J-01) -- Data Contract row "Tradable level map --
+bands"'s SOLE owner.
+
+THIS MODULE is a LENS over the frozen ``research/levels.py`` computation, never a second levels
+engine: it consumes ``compute_levels``'s output (the ``levels`` list AND ``confluence_zones``)
+VERBATIM -- no pivot/extreme re-detection, no second bar-windowing for level discovery, no touch
+to ``levels.py``'s 5 bps (``sr_touch_tolerance_bps``) / 20 bps (``sr_confluence_band_bps``)
+parameters. It reads stored bars itself for exactly two, narrowly-scoped reasons: (a)
+**morning-markup as-of resolution** (finding the prior completed session from the stored DAILY
+series) and (b) **price-scale context** (the current reference price for support/resistance side
+classification, plus a recency scan over the SAME daily series already read for (a) -- no new bar
+read is opened for recency).
+
+``GET /research/tradability`` and the read-only MCP ``tradability`` tool both serve this module's
+output VERBATIM (single source of truth -- no second computation path, mirroring ``levels.py``'s
+own MCP/REST discipline).
+
+**Morning-markup as-of resolution.** For a requested ``as_of`` inside a session, the basis is the
+last COMPLETED daily bar strictly before the requested session's own UTC calendar date (holidays
+and weekends are handled for free -- no hardcoded calendar, since a missing daily bar simply is
+not a candidate). ``compute_levels`` is handed TWO things: an as-of epoch of that prior bar's own
+epoch plus one calendar day (``_ONE_DAY_SECONDS`` -- the SAME structural period-closing convention
+``levels.py``'s own ``_prior_period_extremes`` uses for ``"1d"``), so the prior session's own
+high/low/close become usable levels (goal.md: "the 2026-06-18 close ... already contained
+rejection highs ... 300.57"); and a READ-ONLY view (``_PriorSessionBarView``) over the store that
+filters every loaded bar, on every timeframe, to ``epoch <= prior_bar.epoch``.
+
+That second part is NOT redundant with the first. Real daily bars from the SAME vendor are stamped
+at a consistent hour-of-day, so for any two CONSECUTIVE trading sessions, "the prior bar's epoch
+plus one day" lands EXACTLY on the requested session's own bar epoch, if one is already stored (the
+normal state for a fully-fetched historical series). ``levels.py``'s own ``_bars_as_of`` uses a
+single inclusive ``<=`` threshold for both "is this bar visible at all" and "has this bar's period
+closed" -- so an as-of value chosen to satisfy the second question can, unavoidably given that
+frozen, un-modifiable comparison, also satisfy the first for any bar sitting at that exact epoch.
+That bar can never itself become a fabricated level (a bar at the very end of the visible window
+still needs future confirmation on both sides to register as a swing pivot) -- but it CAN falsely
+unlock the bar just before it, letting THAT prior bar be checked as a swing-pivot centre using the
+requested session's own bar as its right-hand neighbour, silently changing the prior bar's own
+registered levels. ``_PriorSessionBarView`` closes that gap by bounding bar visibility itself, so
+the as-of epoch's only remaining job is closing ``prior_bar``'s own period -- this is this module's
+own SECOND, deliberate truncation surface, layered in front of ``levels.py``'s frozen one
+specifically to cover the case its single inclusive threshold cannot express on its own.
+
+**Band clustering.** The as-of-resolved ``levels`` list is split into two sides by the prior
+session's own CLOSE price (levels priced above it are resistance candidates, at-or-below are
+support candidates -- a plain comparison, never a re-detection of structure), then each side is
+clustered independently by an ANCHOR-FIXED scan over ascending price (the identical TECHNIQUE
+``levels.py``'s own ``_cluster_levels`` uses for confluence zones, reused as a technique only --
+this module imports no clustering code from ``levels.py``) at a config-owned, wider, price-scale-
+aware tolerance (``Config.tradability_band_width_bps``) than the raw confluence band: a tradable
+band is deliberately coarser, built to merge nearby REAL rejection highs (the pinned AAPL cluster
+spans 300.48 to 302.07, roughly 53 bps apart) into ONE wall a trader would mark, not several
+adjacent lines. Every level is assigned to exactly one band (no level is silently dropped before
+scoring); at most ``Config.tradability_band_cap_per_side`` bands per side survive, ranked by
+quality score -- so the served map is never more than ``2 * tradability_band_cap_per_side`` bands
+total (``<= 10`` at the config-owned default cap of 5).
+
+**Quality scoring** (config-owned weights, ``Config.tradability_quality_weights``) sums four
+factors: distinct-timeframe breadth among the band's member levels, the **daily** touch count (the
+sum of each ``"1d"`` member's own ``touch_count`` -- goal.md's factor is "daily touch count", never
+a sum across every timeframe: a band can hold dozens of intraday 5m/1h members whose combined touch
+volume near the current price would otherwise drown a genuine multi-day rejection wall; intraday
+members still count toward breadth but not toward this daily total -- all ``touch_count`` values are
+already computed by ``levels.py``, never re-counted from bars), a recency score (0..1, the position
+-- among the as-of-truncated daily bars already read for basis resolution -- of the MOST RECENT bar
+whose high/low range intersects the band, or 0.0 if none does), and a round-number flag
+(config-owned increment + tolerance, e.g. 300 flagged at the default 50-point increment). No factor
+re-derives a level or a zone; every input is either a member level's own field or a plain scan over
+bars already read for another named purpose.
+
+**Class inheritance.** A band's A/B/C ``class`` is a PROJECTION of its best overlapping confluence
+zone from ``compute_levels``'s ``confluence_zones`` (goal.md: "inherits the band class from its
+best member zone ... class stays owned by levels.py -- no re-grading") -- a zone "overlaps" a band
+when at least one zone member level's price falls inside the band's own ``[price_low, price_high]``
+range; "best" is the highest class (A > B > C), tie-broken by the zone's own score. A band with no
+overlapping zone honestly carries ``class: null`` -- never a fabricated/defaulted grade ``levels.py``
+itself never assigned.
+
+**Deterministic + honest.** Pure function of the store's stored bars + config: identical inputs
+produce byte-identical output (every collection is sorted by an explicit total order; no
+wall-clock, no unseeded randomness). Two honest empty states, mirroring ``levels.py``'s own
+``no_bar_series_for_symbol`` precedent: a symbol with NO recorded bar series at all (any timeframe)
+sets ``no_bar_series_for_symbol: true``; a symbol WITH series but nothing derivable at the resolved
+as-of (no daily series to resolve a basis from at all, or a daily series exists but no session
+strictly precedes the requested one) reports ``false`` with an empty ``bands`` list and
+``basis_as_of: null`` -- never a fabricated band. Once a basis DOES resolve, ``compute_levels``
+always contributes at least that prior session's own high/low/close, so a resolved basis with zero
+bands is not a state this module can reach -- no branch exists to fabricate one.
+"""
+
+from __future__ import annotations
+
+from datetime import datetime, timezone
+
+from ..config import Config
+from ..providers.adapters.base import RawBar
+from .bars import BarStore
+from .levels import compute_levels
+
+SUPPORT = "support"
+RESISTANCE = "resistance"
+
+# One calendar day in seconds -- a STRUCTURAL calendar fact (mirrors ``levels.py``'s own
+# ``_PERIOD_SECONDS["1d"]``), not a tunable research parameter, so it is deliberately NOT a
+# ``Config`` field (the identical ``levels.py`` rationale for its own period-length constant).
+_ONE_DAY_SECONDS = 86400.0
+
+# The DAILY timeframe identifier -- a STRUCTURAL identifier (mirrors ``levels.py``'s own literal
+# ``"1d"`` in ``PRIOR_PERIOD_TIMEFRAMES`` / ``_PERIOD_SECONDS``), not a tunable research parameter,
+# so it is deliberately NOT a ``Config`` field. It names the ONE timeframe whose touches the
+# ``touch_count`` quality factor counts -- goal.md's factor is "DAILY touch count", verbatim (see
+# ``_quality_score``), never a sum across every timeframe.
+_DAILY_TIMEFRAME = "1d"
+
+_CLASS_RANK: dict[str, int] = {"A": 3, "B": 2, "C": 1}
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
+def _session_date(epoch: float):
+    return datetime.fromtimestamp(epoch, tz=timezone.utc).date()
+
+
+class _PriorSessionBarView:
+    """A read-only, duck-typed view over a real ``BarStore`` (implements only the two methods
+    ``compute_levels`` calls: ``list()`` and ``load_bars()``) that filters every loaded bar series,
+    on EVERY timeframe, to ``epoch <= cutoff_epoch`` -- see the module docstring's "morning-markup
+    as-of resolution" section for why this second truncation surface is necessary alongside the
+    as-of epoch. ``list()`` is delegated unchanged (series SELECTION -- which series wins per
+    timeframe -- must stay identical to an unfiltered read; only bar CONTENT is bounded). Never
+    writes anything -- ``record`` is not implemented, so a coding error that tried to persist
+    through this view would fail loudly, never silently."""
+
+    def __init__(self, store: BarStore, cutoff_epoch: float) -> None:
+        self._store = store
+        self._cutoff_epoch = cutoff_epoch
+
+    def list(self) -> tuple[list[dict], list[dict]]:
+        return self._store.list()
+
+    def load_bars(self, bar_series_id: str) -> list[RawBar]:
+        return [b for b in self._store.load_bars(bar_series_id) if b.epoch <= self._cutoff_epoch]
+
+
+def _select_daily_series(store: BarStore, symbol: str) -> tuple[list[RawBar] | None, bool]:
+    """Returns ``(sorted_daily_bars_or_None, has_any_series_for_symbol)``. Selects the winning
+    ``"1d"`` series with the EXACT SAME scan + tie-break ``levels.py``'s own
+    ``_select_one_series_per_timeframe`` uses (first-seen-with-the-max-``created_utc`` wins, scanned
+    in ``store.list()``'s own oldest-first order) -- so when more than one ``"1d"`` series is ever
+    registered for ``symbol``, this module and ``compute_levels`` always agree on which one, and the
+    ``prior_bar`` this resolves is guaranteed to be a member of the SAME series ``compute_levels``
+    itself reads (never a second, independently-selected series)."""
+    records, _integrity_errors = store.list()
+    matching_any = [r for r in records if r["symbol"] == symbol]
+    if not matching_any:
+        return None, False
+    chosen: dict | None = None
+    for record in matching_any:
+        if record["timeframe"] != "1d":
+            continue
+        if chosen is None or record["created_utc"] > chosen["created_utc"]:
+            chosen = record
+    if chosen is None:
+        return None, True
+    bars = sorted(store.load_bars(chosen["id"]), key=lambda b: b.epoch)
+    return bars, True
+
+
+def _resolve_basis(daily_bars: list[RawBar], as_of_epoch: float) -> tuple[float, RawBar] | None:
+    """The morning-markup basis: the last COMPLETED daily bar strictly before the requested
+    session's own UTC calendar date, plus the resolved as-of epoch to feed ``compute_levels`` (that
+    bar's own epoch + one day -- see module docstring). ``None`` when no prior session exists in
+    the store (honest empty state, never a fabricated basis)."""
+    requested_date = _session_date(as_of_epoch)
+    candidates = [
+        b for b in daily_bars if b.epoch <= as_of_epoch and _session_date(b.epoch) < requested_date
+    ]
+    if not candidates:
+        return None
+    prior_bar = max(candidates, key=lambda b: b.epoch)
+    return prior_bar.epoch + _ONE_DAY_SECONDS, prior_bar
+
+
+def _cluster_side(levels: list[dict], band_width_bps: float) -> list[list[dict]]:
+    """Anchor-fixed scan over ascending price -- the identical TECHNIQUE ``levels.py``'s own
+    ``_cluster_levels`` uses for confluence zones (reused as a technique only; no import of, or
+    call into, that function), at this module's own wider, config-owned tolerance. Unlike
+    ``_cluster_levels`` (which drops singleton levels -- confluence requires >= 2 members), EVERY
+    level here joins exactly one band, including size-1 bands: this lens exists to distill via
+    scoring + the top-K cap below, never by silently discarding input before scoring."""
+    ordered = sorted(levels, key=lambda lvl: (lvl["price"], lvl["timeframe"], lvl["type"]))
+    bands: list[list[dict]] = []
+    current: list[dict] = []
+    anchor = 0.0
+    tolerance = 0.0
+    for level in ordered:
+        if current and abs(level["price"] - anchor) <= tolerance:
+            current.append(level)
+            continue
+        if current:
+            bands.append(current)
+        anchor = level["price"]
+        tolerance = anchor * (band_width_bps / 10_000.0)
+        current = [level]
+    if current:
+        bands.append(current)
+    return bands
+
+
+def _round_number_flag(price_low: float, price_high: float, increment: float, tolerance_bps: float) -> bool:
+    """True iff either band edge sits within ``tolerance_bps`` of a multiple of ``increment`` --
+    checking BOTH edges (never just the low, never just a computed midpoint that might itself not
+    be a real level) keeps this an honest read of the band's own real boundaries."""
+    for price in (price_low, price_high):
+        nearest_multiple = round(price / increment) * increment
+        tolerance = price * (tolerance_bps / 10_000.0)
+        if abs(price - nearest_multiple) <= tolerance:
+            return True
+    return False
+
+
+def _recency_score(daily_bars: list[RawBar], price_low: float, price_high: float) -> float:
+    """0.0..1.0: the position (1-indexed, normalized by total count) of the MOST RECENT bar (among
+    the already as-of-truncated ``daily_bars``) whose high/low range intersects
+    ``[price_low, price_high]``. 0.0 when no bar touches -- an honest "never recently touched",
+    never a fabricated score. A plain range-intersection scan over bars already read for basis
+    resolution -- not a re-detection of any level."""
+    if not daily_bars:
+        return 0.0
+    last_touch_index: int | None = None
+    for index, bar in enumerate(daily_bars):
+        if bar.low <= price_high and bar.high >= price_low:
+            last_touch_index = index
+    if last_touch_index is None:
+        return 0.0
+    return (last_touch_index + 1) / len(daily_bars)
+
+
+def _best_zone_class(zones: list[dict], price_low: float, price_high: float) -> str | None:
+    """The band's inherited class: the highest-graded (tie-broken by score) confluence zone with
+    at least one member level priced inside ``[price_low, price_high]`` -- ``None`` when no zone
+    overlaps (an honest absence; ``levels.py`` itself never graded anything here, so this module
+    never invents a grade)."""
+    best_class: str | None = None
+    best_key: tuple[int, float] | None = None
+    for zone in zones:
+        if not any(price_low <= member["price"] <= price_high for member in zone["levels"]):
+            continue
+        key = (_CLASS_RANK[zone["class"]], zone["score"])
+        if best_key is None or key > best_key:
+            best_key = key
+            best_class = zone["class"]
+    return best_class
+
+
+def _quality_score(
+    members: list[dict], daily_bars: list[RawBar], price_low: float, price_high: float,
+    round_number: bool, config: Config,
+) -> float:
+    weights = config.tradability_quality_weights
+    breadth = len({member["timeframe"] for member in members})
+    # goal.md's factor is the "DAILY touch count", NOT a sum across every timeframe: a real
+    # multi-day rejection wall is defined by how many times the DAILY series rejected it, so ONLY
+    # ``"1d"`` members contribute here. Summing the touch_count of the dozens of intraday (5m/1h)
+    # members a band can hold instead lets sheer intraday level VOLUME near the current price
+    # outscore that wall -- the exact miss a daily-only fixture cannot surface (reproduced, and
+    # guarded against, by the multi-timeframe regression in tests/test_tradability.py). Intraday
+    # members still count toward ``breadth`` above (cross-timeframe agreement is its own signal);
+    # they just do not inflate this per-band touch total. Every ``touch_count`` is a member level's
+    # own field already computed by ``levels.py`` -- never re-counted from bars here.
+    daily_touch_total = sum(
+        member["touch_count"] for member in members if member["timeframe"] == _DAILY_TIMEFRAME
+    )
+    recency = _recency_score(daily_bars, price_low, price_high)
+    return (
+        weights["timeframe_breadth"] * breadth
+        + weights["touch_count"] * daily_touch_total
+        + weights["recency"] * recency
+        + weights["round_number"] * (1.0 if round_number else 0.0)
+    )
+
+
+def _band(members: list[dict], side: str, daily_bars: list[RawBar], zones: list[dict], config: Config) -> dict:
+    price_low = min(member["price"] for member in members)
+    price_high = max(member["price"] for member in members)
+    round_number = _round_number_flag(
+        price_low, price_high,
+        config.tradability_round_number_increment, config.tradability_round_number_tolerance_bps,
+    )
+    return {
+        "side": side,
+        "price_low": price_low,
+        "price_high": price_high,
+        "class": _best_zone_class(zones, price_low, price_high),
+        "quality_score": _quality_score(members, daily_bars, price_low, price_high, round_number, config),
+        "round_number": round_number,
+        "member_count": len(members),
+        "members": sorted(members, key=lambda m: (m["price"], m["timeframe"], m["type"])),
+    }
+
+
+def _rank_sort_key(band: dict) -> tuple:
+    """Descending quality score, tie-broken ascending by price -- the total order used to pick the
+    top-K survivors per side (never a fabricated/arbitrary insertion-order tie-break)."""
+    return (-band["quality_score"], band["price_low"])
+
+
+def _served_sort_key(band: dict) -> tuple:
+    """A total order over the FINAL served list (side, then descending quality, then price) so the
+    served JSON is never perturbed by scan-order happenstance -- the ``levels.py`` byte-identical-
+    determinism discipline."""
+    return (band["side"], -band["quality_score"], band["price_low"])
+
+
+def compute_tradability(store: BarStore, symbol: str, as_of_epoch: float, config: Config) -> dict:
+    """The canonical ``GET /research/tradability`` + MCP ``tradability`` computation (single
+    source of truth) -- see module docstring for the full algorithm. Returns
+    ``{"bands": [...], "no_bar_series_for_symbol": bool, "basis_as_of": str | None}``."""
+    daily_bars, has_any_series = _select_daily_series(store, symbol)
+    if not has_any_series:
+        return {"bands": [], "no_bar_series_for_symbol": True, "basis_as_of": None}
+    if daily_bars is None:
+        # series exist for `symbol` but none is "1d" -- no basis is derivable (honest, not a
+        # fabricated flag flip: `levels.py`'s OWN `no_bar_series_for_symbol` stays scoped to "no
+        # series at all", so this module's flag mirrors that exact meaning).
+        return {"bands": [], "no_bar_series_for_symbol": False, "basis_as_of": None}
+
+    resolved = _resolve_basis(daily_bars, as_of_epoch)
+    if resolved is None:
+        return {"bands": [], "no_bar_series_for_symbol": False, "basis_as_of": None}
+    resolved_as_of_epoch, prior_bar = resolved
+    # The SERVED basis marker is the prior session's own bar timestamp (e.g. 2026-06-18T04:00Z for
+    # the pinned AAPL case) -- unambiguously dated to that session, never the internal
+    # period-closed instant `compute_levels` receives (`prior_bar.epoch + _ONE_DAY_SECONDS`, one
+    # calendar day later): the served field answers "which session is this map's basis", the
+    # internal epoch only exists to make that session's own high/low/close usable per
+    # `levels.py`'s period-closing convention (see module docstring).
+    basis_as_of = _iso(prior_bar.epoch)
+
+    # `compute_levels` reads through `_PriorSessionBarView` (bounded to `prior_bar.epoch`, EVERY
+    # timeframe -- see module docstring) rather than `store` directly: the as-of epoch alone cannot
+    # safely express "close `prior_bar`'s own period but admit nothing dated on/after the requested
+    # session" when a same-hour-of-day bar for that later session already exists (the normal state
+    # for consecutive trading sessions in a fully-fetched series).
+    #
+    # `raw_levels` is guaranteed non-empty here: `_resolve_basis` only returns non-None once
+    # `prior_bar`'s own daily period is closed as of `resolved_as_of_epoch` (by construction, one
+    # calendar day after its own epoch), and `prior_bar` is a member of the EXACT SAME "1d" series
+    # `compute_levels` itself selects (`_select_daily_series` mirrors its tie-break verbatim, and
+    # the view's `list()` is unfiltered) -- so `compute_levels`'s own `_prior_period_extremes`
+    # always emits at least that bar's high/low/close. No empty-`raw_levels` branch is reachable,
+    # so none is written (an untested dead branch is worse than no branch); the loop below already
+    # returns an honest `bands: []` for a side with no levels.
+    bounded_store = _PriorSessionBarView(store, prior_bar.epoch)
+    levels_result = compute_levels(bounded_store, symbol, resolved_as_of_epoch, config)
+    raw_levels = levels_result["levels"]
+    zones = levels_result["confluence_zones"]
+
+    current_price = prior_bar.close
+    truncated_daily_bars = [b for b in daily_bars if b.epoch <= prior_bar.epoch]
+    resistance_levels = [lvl for lvl in raw_levels if lvl["price"] > current_price]
+    support_levels = [lvl for lvl in raw_levels if lvl["price"] <= current_price]
+
+    bands: list[dict] = []
+    for side, side_levels in ((RESISTANCE, resistance_levels), (SUPPORT, support_levels)):
+        clusters = _cluster_side(side_levels, config.tradability_band_width_bps)
+        side_bands = [_band(members, side, truncated_daily_bars, zones, config) for members in clusters]
+        side_bands.sort(key=_rank_sort_key)
+        bands.extend(side_bands[: config.tradability_band_cap_per_side])
+
+    bands.sort(key=_served_sort_key)
+    return {
+        "bands": bands,
+        "no_bar_series_for_symbol": False,
+        "basis_as_of": basis_as_of,
+    }
diff --git a/apps/backend/tests/fixtures/yahoo/AAPL_1d_20260101_20260626.json b/apps/backend/tests/fixtures/yahoo/AAPL_1d_20260101_20260626.json
new file mode 100644
index 0000000..de14543
--- /dev/null
+++ b/apps/backend/tests/fixtures/yahoo/AAPL_1d_20260101_20260626.json
@@ -0,0 +1,976 @@
+{
+  "symbol": "AAPL",
+  "timeframe": "1d",
+  "start": "2026-01-01T00:00:00Z",
+  "end": "2026-06-26T04:00:00Z",
+  "bars": [
+    {
+      "epoch": 1767330000.0,
+      "open": 271.7551282774649,
+      "high": 277.32476727085935,
+      "low": 268.5011639041959,
+      "close": 270.5074462890625,
+      "volume": 37838100
+    },
+    {
+      "epoch": 1767589200.0,
+      "open": 270.1381413175191,
+      "high": 271.00652312062255,
+      "low": 265.64648609237463,
+      "close": 266.764404296875,
+      "volume": 45647200
+    },
+    {
+      "epoch": 1767675600.0,
+      "open": 266.5048844877732,
+      "high": 267.05385240251036,
+      "low": 261.63392891626114,
+      "close": 261.87347412109375,
+      "volume": 52352100
+    },
+    {
+      "epoch": 1767762000.0,
+      "open": 262.7119324450406,
+      "high": 263.1910228349833,
+      "low": 259.3282042611396,
+      "close": 259.84722900390625,
+      "volume": 48309800
+    },
+    {
+      "epoch": 1767848400.0,
+      "open": 256.5433578451618,
+      "high": 258.80916773471864,
+      "low": 255.22581364132833,
+      "close": 258.55963134765625,
+      "volume": 50419300
+    },
+    {
+      "epoch": 1767934800.0,
+      "open": 258.5995368285105,
+      "high": 259.7274461787287,
+      "low": 255.74485516422806,
+      "close": 258.8890075683594,
+      "volume": 39997000
+    },
+    {
+      "epoch": 1768194000.0,
+      "open": 258.679389570116,
+      "high": 260.81540508500296,
+      "low": 256.32375036738995,
+      "close": 259.7673645019531,
+      "volume": 45263800
+    },
+    {
+      "epoch": 1768280400.0,
+      "open": 258.24022168851656,
+      "high": 261.3244878277737,
+      "low": 257.9108470550362,
+      "close": 260.5658874511719,
+      "volume": 45730800
+    },
+    {
+      "epoch": 1768366800.0,
+      "open": 259.0087756526009,
+      "high": 261.33447181199796,
+      "low": 256.23393227813756,
+      "close": 259.4779052734375,
+      "volume": 40019400
+    },
+    {
+      "epoch": 1768453200.0,
+      "open": 260.16664839115424,
+      "high": 260.55593980217856,
+      "low": 256.57331808587395,
+      "close": 257.7311706542969,
+      "volume": 39388600
+    },
+    {
+      "epoch": 1768539600.0,
+      "open": 257.4217218192236,
+      "high": 258.41986733264514,
+      "low": 254.4572284259222,
+      "close": 255.05612182617188,
+      "volume": 72142800
+    },
+    {
+      "epoch": 1768885200.0,
+      "open": 252.26132447540706,
+      "high": 254.31750190322293,
+      "low": 242.9685916985444,
+      "close": 246.2425079345703,
+      "volume": 80267500
+    },
+    {
+      "epoch": 1768971600.0,
+      "open": 248.23880604127606,
+      "high": 251.09350304772093,
+      "low": 244.72532928784554,
+      "close": 247.1907501220703,
+      "volume": 54641700
+    },
+    {
+      "epoch": 1769058000.0,
+      "open": 248.737864640942,
+      "high": 250.53452965267718,
+      "low": 247.68980878155546,
+      "close": 247.8894500732422,
+      "volume": 39708300
+    },
+    {
+      "epoch": 1769144400.0,
+      "open": 246.86136630134166,
+      "high": 248.94748685874615,
+      "low": 244.22624741136653,
+      "close": 247.58001708984375,
+      "volume": 41689000
+    },
+    {
+      "epoch": 1769403600.0,
+      "open": 251.01365072947274,
+      "high": 256.08423219515316,
+      "low": 249.33677343540953,
+      "close": 254.93637084960938,
+      "volume": 55969200
+    },
+    {
+      "epoch": 1769490000.0,
+      "open": 258.6894015269614,
+      "high": 261.4642450011371,
+      "low": 257.73115984508394,
+      "close": 257.7910461425781,
+      "volume": 49648300
+    },
+    {
+      "epoch": 1769576400.0,
+      "open": 257.1721946066941,
+      "high": 258.3799421919039,
+      "low": 254.03801819206552,
+      "close": 255.96444702148438,
+      "volume": 41288000
+    },
+    {
+      "epoch": 1769662800.0,
+      "open": 257.52154586161765,
+      "high": 259.16847988830324,
+      "low": 253.93820707645818,
+      "close": 257.801025390625,
+      "volume": 67253000
+    },
+    {
+      "epoch": 1769749200.0,
+      "open": 254.6968198516284,
+      "high": 261.4143357105436,
+      "low": 251.71235892004358,
+      "close": 258.99884033203125,
+      "volume": 92443400
+    },
+    {
+      "epoch": 1770008400.0,
+      "open": 259.5477742456141,
+      "high": 269.98836769074944,
+      "low": 258.72928762151224,
+      "close": 269.50927734375,
+      "volume": 73913400
+    },
+    {
+      "epoch": 1770094800.0,
+      "open": 268.70080609664296,
+      "high": 271.3758289780004,
+      "low": 267.11372779647115,
+      "close": 268.98028564453125,
+      "volume": 64394700
+    },
+    {
+      "epoch": 1770181200.0,
+      "open": 271.7850411492978,
+      "high": 278.432693698261,
+      "low": 271.7850411492978,
+      "close": 275.97723388671875,
+      "volume": 90545700
+    },
+    {
+      "epoch": 1770267600.0,
+      "open": 277.6142303156022,
+      "high": 278.98168486317746,
+      "low": 272.72332314901723,
+      "close": 275.3983459472656,
+      "volume": 52977400
+    },
+    {
+      "epoch": 1770354000.0,
+      "open": 276.6060720438839,
+      "high": 280.3890519626743,
+      "low": 276.4164219647768,
+      "close": 277.6042175292969,
+      "volume": 50453400
+    },
+    {
+      "epoch": 1770613200.0,
+      "open": 277.6541982366954,
+      "high": 277.9439398399519,
+      "low": 271.4499228389202,
+      "close": 274.3672180175781,
+      "volume": 44623400
+    },
+    {
+      "epoch": 1770699600.0,
+      "open": 274.6369782150198,
+      "high": 275.11651686144285,
+      "low": 272.68876099546605,
+      "close": 273.4280700683594,
+      "volume": 34376900
+    },
+    {
+      "epoch": 1770786000.0,
+      "open": 274.44714753122867,
+      "high": 279.92208361183503,
+      "low": 274.1973776592452,
+      "close": 275.24639892578125,
+      "volume": 51931300
+    },
+    {
+      "epoch": 1770872400.0,
+      "open": 275.3363333447182,
+      "high": 275.46621856633783,
+      "low": 259.94051360693726,
+      "close": 261.4891052246094,
+      "volume": 81077200
+    },
+    {
+      "epoch": 1770958800.0,
+      "open": 261.7688319830923,
+      "high": 261.9886306947134,
+      "low": 255.21485759663088,
+      "close": 255.5445556640625,
+      "volume": 56290700
+    },
+    {
+      "epoch": 1771304400.0,
+      "open": 257.8124646511843,
+      "high": 266.0449008431299,
+      "low": 255.30478047881587,
+      "close": 263.6371154785156,
+      "volume": 58469100
+    },
+    {
+      "epoch": 1771390800.0,
+      "open": 263.35737977838915,
+      "high": 266.57441720150126,
+      "low": 262.20844437502524,
+      "close": 264.106689453125,
+      "volume": 34203300
+    },
+    {
+      "epoch": 1771477200.0,
+      "open": 262.35827847824623,
+      "high": 264.2365527856389,
+      "low": 259.81060750150084,
+      "close": 260.3401184082031,
+      "volume": 30845300
+    },
+    {
+      "epoch": 1771563600.0,
+      "open": 258.73163460792017,
+      "high": 264.5063132392292,
+      "low": 257.9223826043077,
+      "close": 264.3364562988281,
+      "volume": 42070500
+    },
+    {
+      "epoch": 1771822800.0,
+      "open": 263.24744081710827,
+      "high": 269.1819753311392,
+      "low": 263.13755670993424,
+      "close": 265.9349670410156,
+      "volume": 37308200
+    },
+    {
+      "epoch": 1771909200.0,
+      "open": 267.61343657617186,
+      "high": 274.6369951599546,
+      "low": 267.46358073991865,
+      "close": 271.8895263671875,
+      "volume": 47014600
+    },
+    {
+      "epoch": 1771995600.0,
+      "open": 271.5298429675081,
+      "high": 274.6869380517792,
+      "low": 270.8005039088116,
+      "close": 273.97760009765625,
+      "volume": 33714300
+    },
+    {
+      "epoch": 1772082000.0,
+      "open": 274.6969199809464,
+      "high": 275.8558253670768,
+      "low": 270.55071567552415,
+      "close": 272.6987609863281,
+      "volume": 32345100
+    },
+    {
+      "epoch": 1772168400.0,
+      "open": 272.5588900215503,
+      "high": 272.5588900215503,
+      "low": 262.6480379442022,
+      "close": 263.93682861328125,
+      "volume": 72366500
+    },
+    {
+      "epoch": 1772427600.0,
+      "open": 262.16844722421786,
+      "high": 266.2846497598317,
+      "low": 259.960490133898,
+      "close": 264.476318359375,
+      "volume": 41827900
+    },
+    {
+      "epoch": 1772514000.0,
+      "open": 263.23749216234586,
+      "high": 265.31556422164516,
+      "low": 259.8905695547566,
+      "close": 263.5072326660156,
+      "volume": 38568900
+    },
+    {
+      "epoch": 1772600400.0,
+      "open": 264.4063951364299,
+      "high": 265.9050144519466,
+      "low": 261.179387723623,
+      "close": 262.2783508300781,
+      "volume": 39803100
+    },
+    {
+      "epoch": 1772686800.0,
+      "open": 260.54995479568396,
+      "high": 261.3192350446657,
+      "low": 257.01320478174756,
+      "close": 260.0504150390625,
+      "volume": 49658600
+    },
+    {
+      "epoch": 1772773200.0,
+      "open": 258.39192833924307,
+      "high": 258.53178361058343,
+      "low": 254.13584003818684,
+      "close": 257.2229919433594,
+      "volume": 41120000
+    },
+    {
+      "epoch": 1773028800.0,
+      "open": 255.45463216869055,
+      "high": 260.9095975388004,
+      "low": 253.44647267699952,
+      "close": 259.6407775878906,
+      "volume": 38218500
+    },
+    {
+      "epoch": 1773115200.0,
+      "open": 257.4128391437035,
+      "high": 262.2384104290217,
+      "low": 256.71350175461305,
+      "close": 260.58990478515625,
+      "volume": 30590800
+    },
+    {
+      "epoch": 1773201600.0,
+      "open": 260.8496568052655,
+      "high": 261.888707997661,
+      "low": 259.3110658747261,
+      "close": 260.5699157714844,
+      "volume": 26218900
+    },
+    {
+      "epoch": 1773288000.0,
+      "open": 258.4219063383753,
+      "high": 258.71164792954545,
+      "low": 253.94601921584928,
+      "close": 255.52456665039062,
+      "volume": 40794000
+    },
+    {
+      "epoch": 1773374400.0,
+      "open": 255.24483747003174,
+      "high": 256.0940459350445,
... [diff_bound] apps/backend/tests/fixtures/yahoo/AAPL_1d_20260101_20260626.json: 583 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/fixtures/yahoo/AAPL_1h_20260601_20260618.json b/apps/backend/tests/fixtures/yahoo/AAPL_1h_20260601_20260618.json
new file mode 100644
index 0000000..8848150
--- /dev/null
+++ b/apps/backend/tests/fixtures/yahoo/AAPL_1h_20260601_20260618.json
@@ -0,0 +1,792 @@
+{
+  "symbol": "AAPL",
+  "timeframe": "1h",
+  "start": "2026-06-01T13:30:00Z",
+  "end": "2026-06-18T19:30:00Z",
+  "bars": [
+    {
+      "epoch": 1780320600.0,
+      "open": 309.5350036621094,
+      "high": 310.92999267578125,
+      "low": 307.79998779296875,
+      "close": 307.8399963378906,
+      "volume": 10175199
+    },
+    {
+      "epoch": 1780324200.0,
+      "open": 307.80999755859375,
+      "high": 308.4700012207031,
+      "low": 306.29998779296875,
+      "close": 306.5751037597656,
+      "volume": 5691006
+    },
+    {
+      "epoch": 1780327800.0,
+      "open": 306.55999755859375,
+      "high": 307.260009765625,
+      "low": 305.489990234375,
+      "close": 305.7200012207031,
+      "volume": 4171810
+    },
+    {
+      "epoch": 1780331400.0,
+      "open": 305.739990234375,
+      "high": 306.5299987792969,
+      "low": 305.0299987792969,
+      "close": 306.4700012207031,
+      "volume": 3705835
+    },
+    {
+      "epoch": 1780335000.0,
+      "open": 306.5199890136719,
+      "high": 308.3999938964844,
+      "low": 306.30999755859375,
+      "close": 307.8699951171875,
+      "volume": 3768496
+    },
+    {
+      "epoch": 1780338600.0,
+      "open": 307.864990234375,
+      "high": 308.32501220703125,
+      "low": 307.3299865722656,
+      "close": 307.42999267578125,
+      "volume": 3948458
+    },
+    {
+      "epoch": 1780342200.0,
+      "open": 307.43499755859375,
+      "high": 308.0400085449219,
+      "low": 305.909912109375,
+      "close": 306.32000732421875,
+      "volume": 5261936
+    },
+    {
+      "epoch": 1780407000.0,
+      "open": 307.4599914550781,
+      "high": 310.4700012207031,
+      "low": 306.7200012207031,
+      "close": 310.3399963378906,
+      "volume": 7411659
+    },
+    {
+      "epoch": 1780410600.0,
+      "open": 310.375,
+      "high": 312.92999267578125,
+      "low": 309.260009765625,
+      "close": 312.7099914550781,
+      "volume": 4895435
+    },
+    {
+      "epoch": 1780414200.0,
+      "open": 312.70001220703125,
+      "high": 313.1499938964844,
+      "low": 312.0400085449219,
+      "close": 312.489990234375,
+      "volume": 3617660
+    },
+    {
+      "epoch": 1780417800.0,
+      "open": 312.4800109863281,
+      "high": 315.1000061035156,
+      "low": 311.8999938964844,
+      "close": 314.67999267578125,
+      "volume": 5289704
+    },
+    {
+      "epoch": 1780421400.0,
+      "open": 314.67999267578125,
+      "high": 315.45001220703125,
+      "low": 313.7550048828125,
+      "close": 314.239990234375,
+      "volume": 3783245
+    },
+    {
+      "epoch": 1780425000.0,
+      "open": 314.2598876953125,
+      "high": 315.2200012207031,
+      "low": 314.19000244140625,
+      "close": 314.7650146484375,
+      "volume": 3482397
+    },
+    {
+      "epoch": 1780428600.0,
+      "open": 314.760009765625,
+      "high": 315.44000244140625,
+      "low": 314.0299987792969,
+      "close": 315.19000244140625,
+      "volume": 4596467
+    },
+    {
+      "epoch": 1780493400.0,
+      "open": 314.17498779296875,
+      "high": 316.94000244140625,
+      "low": 314.0,
+      "close": 314.3500061035156,
+      "volume": 9396189
+    },
+    {
+      "epoch": 1780497000.0,
+      "open": 314.3699951171875,
+      "high": 314.6499938964844,
+      "low": 310.30999755859375,
+      "close": 311.6600036621094,
+      "volume": 6549146
+    },
+    {
+      "epoch": 1780500600.0,
+      "open": 311.6400146484375,
+      "high": 312.19000244140625,
+      "low": 309.510009765625,
+      "close": 309.7601013183594,
+      "volume": 6552624
+    },
+    {
+      "epoch": 1780504200.0,
+      "open": 309.760009765625,
+      "high": 310.4649963378906,
+      "low": 308.8500061035156,
+      "close": 309.2099914550781,
+      "volume": 3649007
+    },
+    {
+      "epoch": 1780507800.0,
+      "open": 309.19500732421875,
+      "high": 309.9800109863281,
+      "low": 308.9800109863281,
+      "close": 309.8399963378906,
+      "volume": 2467933
+    },
+    {
+      "epoch": 1780511400.0,
+      "open": 309.8399963378906,
+      "high": 310.5400085449219,
+      "low": 309.2699890136719,
+      "close": 310.4150085449219,
+      "volume": 3123761
+    },
+    {
+      "epoch": 1780515000.0,
+      "open": 310.4150085449219,
+      "high": 311.1000061035156,
+      "low": 309.20001220703125,
+      "close": 310.3800048828125,
+      "volume": 6562646
+    },
+    {
+      "epoch": 1780579800.0,
+      "open": 313.30499267578125,
+      "high": 313.5400085449219,
+      "low": 309.90008544921875,
+      "close": 310.25,
+      "volume": 9640009
+    },
+    {
+      "epoch": 1780583400.0,
+      "open": 310.260009765625,
+      "high": 311.3500061035156,
+      "low": 309.79998779296875,
+      "close": 310.3999938964844,
+      "volume": 3601740
+    },
+    {
+      "epoch": 1780587000.0,
+      "open": 310.4100036621094,
+      "high": 311.1099853515625,
+      "low": 309.6499938964844,
+      "close": 310.6300048828125,
+      "volume": 3102831
+    },
+    {
+      "epoch": 1780590600.0,
+      "open": 310.6300048828125,
+      "high": 311.7900085449219,
+      "low": 310.4800109863281,
+      "close": 311.6650085449219,
+      "volume": 3514607
+    },
+    {
+      "epoch": 1780594200.0,
+      "open": 311.6700134277344,
+      "high": 311.9750061035156,
+      "low": 310.989990234375,
+      "close": 311.4200134277344,
+      "volume": 2206917
+    },
+    {
+      "epoch": 1780597800.0,
+      "open": 311.4100036621094,
+      "high": 312.07000732421875,
+      "low": 311.35919189453125,
+      "close": 311.94000244140625,
+      "volume": 2612939
+    },
+    {
+      "epoch": 1780601400.0,
+      "open": 311.94000244140625,
+      "high": 311.9599914550781,
+      "low": 310.260009765625,
+      "close": 311.1600036621094,
+      "volume": 4150477
+    },
+    {
+      "epoch": 1780666200.0,
+      "open": 312.989990234375,
+      "high": 315.1700134277344,
+      "low": 312.3999938964844,
+      "close": 313.42498779296875,
+      "volume": 10660699
+    },
+    {
+      "epoch": 1780669800.0,
+      "open": 313.4200134277344,
+      "high": 314.75,
+      "low": 312.239990234375,
+      "close": 313.42999267578125,
+      "volume": 4746478
+    },
+    {
+      "epoch": 1780673400.0,
+      "open": 313.4200134277344,
+      "high": 314.14990234375,
+      "low": 311.8500061035156,
+      "close": 312.0,
+      "volume": 4534835
+    },
+    {
+      "epoch": 1780677000.0,
+      "open": 312.0050048828125,
+      "high": 312.1499938964844,
+      "low": 309.5799865722656,
+      "close": 311.510009765625,
+      "volume": 7722107
+    },
+    {
+      "epoch": 1780680600.0,
+      "open": 311.4949951171875,
+      "high": 312.79998779296875,
+      "low": 311.3800048828125,
+      "close": 311.5260009765625,
+      "volume": 4435527
+    },
+    {
+      "epoch": 1780684200.0,
+      "open": 311.5400085449219,
+      "high": 312.0199890136719,
+      "low": 307.1499938964844,
+      "close": 308.9100036621094,
+      "volume": 11256615
+    },
+    {
+      "epoch": 1780687800.0,
+      "open": 308.8800048828125,
+      "high": 308.9800109863281,
+      "low": 307.3599853515625,
+      "close": 307.3900146484375,
+      "volume": 7276594
+    },
+    {
+      "epoch": 1780925400.0,
+      "open": 308.739013671875,
+      "high": 315.1700134277344,
+      "low": 308.5220031738281,
+      "close": 311.9750061035156,
+      "volume": 10861725
+    },
+    {
+      "epoch": 1780929000.0,
+      "open": 311.9599914550781,
+      "high": 315.3599853515625,
+      "low": 311.7799987792969,
+      "close": 313.92999267578125,
+      "volume": 5519448
+    },
+    {
+      "epoch": 1780932600.0,
+      "open": 313.92999267578125,
+      "high": 314.989990234375,
+      "low": 313.32000732421875,
+      "close": 313.6650085449219,
+      "volume": 4972235
+    },
+    {
+      "epoch": 1780936200.0,
+      "open": 313.67999267578125,
+      "high": 314.69000244140625,
+      "low": 312.2099914550781,
+      "close": 314.57000732421875,
+      "volume": 5529465
+    },
+    {
+      "epoch": 1780939800.0,
+      "open": 314.56500244140625,
+      "high": 317.3999938964844,
+      "low": 303.7099914550781,
+      "close": 304.8599853515625,
+      "volume": 19927828
+    },
+    {
+      "epoch": 1780943400.0,
+      "open": 304.8999938964844,
+      "high": 305.5299987792969,
+      "low": 302.05010986328125,
+      "close": 302.7049865722656,
+      "volume": 9894127
+    },
+    {
+      "epoch": 1780947000.0,
+      "open": 302.7099914550781,
+      "high": 303.2445068359375,
+      "low": 301.1700134277344,
+      "close": 301.57000732421875,
+      "volume": 7298835
+    },
+    {
+      "epoch": 1781011800.0,
+      "open": 300.2749938964844,
+      "high": 300.7200012207031,
+      "low": 292.2099914550781,
+      "close": 292.5299987792969,
+      "volume": 15558354
+    },
+    {
+      "epoch": 1781015400.0,
+      "open": 292.5191955566406,
+      "high": 293.8800048828125,
+      "low": 291.5,
+      "close": 291.5799865722656,
+      "volume": 9159006
+    },
+    {
+      "epoch": 1781019000.0,
+      "open": 291.55999755859375,
+      "high": 291.9800109863281,
+      "low": 289.4800109863281,
+      "close": 289.5,
+      "volume": 8529475
+    },
+    {
+      "epoch": 1781022600.0,
+      "open": 289.5,
+      "high": 291.1300048828125,
+      "low": 287.7799987792969,
+      "close": 290.4599914550781,
+      "volume": 8503325
+    },
+    {
+      "epoch": 1781026200.0,
+      "open": 290.44000244140625,
+      "high": 290.95001220703125,
+      "low": 289.3399963378906,
+      "close": 290.95001220703125,
+      "volume": 4788451
+    },
+    {
+      "epoch": 1781029800.0,
+      "open": 290.94000244140625,
+      "high": 291.9200134277344,
+      "low": 290.2900085449219,
+      "close": 291.1300048828125,
+      "volume": 5060332
+    },
+    {
+      "epoch": 1781033400.0,
+      "open": 291.1199951171875,
+      "high": 291.67999267578125,
... [diff_bound] apps/backend/tests/fixtures/yahoo/AAPL_1h_20260601_20260618.json: 399 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/fixtures/yahoo/AAPL_1w_20260601_20260615.json b/apps/backend/tests/fixtures/yahoo/AAPL_1w_20260601_20260615.json
new file mode 100644
index 0000000..b68de5b
--- /dev/null
+++ b/apps/backend/tests/fixtures/yahoo/AAPL_1w_20260601_20260615.json
@@ -0,0 +1,32 @@
+{
+  "symbol": "AAPL",
+  "timeframe": "1w",
+  "start": "2026-06-01T04:00:00Z",
+  "end": "2026-06-15T04:00:00Z",
+  "bars": [
+    {
+      "epoch": 1780286400.0,
+      "open": 309.6300048828125,
+      "high": 316.94000244140625,
+      "low": 305.0199890136719,
+      "close": 307.3399963378906,
+      "volume": 254400900
+    },
+    {
+      "epoch": 1780891200.0,
+      "open": 308.739990234375,
+      "high": 317.3999938964844,
+      "low": 287.3800048828125,
+      "close": 291.1300048828125,
+      "volume": 282165800
+    },
+    {
+      "epoch": 1781496000.0,
+      "open": 294.1199951171875,
+      "high": 302.07000732421875,
+      "low": 291.70001220703125,
+      "close": 298.010009765625,
+      "volume": 214314300
+    }
+  ]
+}
\ No newline at end of file
diff --git a/apps/backend/tests/fixtures/yahoo/AAPL_4h_20260601_20260618.json b/apps/backend/tests/fixtures/yahoo/AAPL_4h_20260601_20260618.json
new file mode 100644
index 0000000..3e88d9b
--- /dev/null
+++ b/apps/backend/tests/fixtures/yahoo/AAPL_4h_20260601_20260618.json
@@ -0,0 +1,232 @@
+{
+  "symbol": "AAPL",
+  "timeframe": "4h",
+  "start": "2026-06-01T13:30:00Z",
+  "end": "2026-06-18T17:30:00Z",
+  "bars": [
+    {
+      "epoch": 1780320600.0,
+      "open": 309.5350036621094,
+      "high": 310.92999267578125,
+      "low": 305.0299987792969,
+      "close": 306.4700012207031,
+      "volume": 23743850
+    },
+    {
+      "epoch": 1780335000.0,
+      "open": 306.5199890136719,
+      "high": 308.3999938964844,
+      "low": 305.909912109375,
+      "close": 306.32000732421875,
+      "volume": 12978890
+    },
+    {
+      "epoch": 1780407000.0,
+      "open": 307.4599914550781,
+      "high": 315.1000061035156,
+      "low": 306.7200012207031,
+      "close": 314.67999267578125,
+      "volume": 21214458
+    },
+    {
+      "epoch": 1780421400.0,
+      "open": 314.67999267578125,
+      "high": 315.45001220703125,
+      "low": 313.7550048828125,
+      "close": 315.19000244140625,
+      "volume": 11862109
+    },
+    {
+      "epoch": 1780493400.0,
+      "open": 314.17498779296875,
+      "high": 316.94000244140625,
+      "low": 308.8500061035156,
+      "close": 309.2099914550781,
+      "volume": 26146966
+    },
+    {
+      "epoch": 1780507800.0,
+      "open": 309.19500732421875,
+      "high": 311.1000061035156,
+      "low": 308.9800109863281,
+      "close": 310.3800048828125,
+      "volume": 12154340
+    },
+    {
+      "epoch": 1780579800.0,
+      "open": 313.30499267578125,
+      "high": 313.5400085449219,
+      "low": 309.6499938964844,
+      "close": 311.6650085449219,
+      "volume": 19859187
+    },
+    {
+      "epoch": 1780594200.0,
+      "open": 311.6700134277344,
+      "high": 312.07000732421875,
+      "low": 310.260009765625,
+      "close": 311.1600036621094,
+      "volume": 8970333
+    },
+    {
+      "epoch": 1780666200.0,
+      "open": 312.989990234375,
+      "high": 315.1700134277344,
+      "low": 309.5799865722656,
+      "close": 311.510009765625,
+      "volume": 27664119
+    },
+    {
+      "epoch": 1780680600.0,
+      "open": 311.4949951171875,
+      "high": 312.79998779296875,
+      "low": 307.1499938964844,
+      "close": 307.3900146484375,
+      "volume": 22968736
+    },
+    {
+      "epoch": 1780925400.0,
+      "open": 308.739013671875,
+      "high": 315.3599853515625,
+      "low": 308.5220031738281,
+      "close": 314.57000732421875,
+      "volume": 26882873
+    },
+    {
+      "epoch": 1780939800.0,
+      "open": 314.56500244140625,
+      "high": 317.3999938964844,
+      "low": 301.1700134277344,
+      "close": 301.57000732421875,
+      "volume": 37120790
+    },
+    {
+      "epoch": 1781011800.0,
+      "open": 300.2749938964844,
+      "high": 300.7200012207031,
+      "low": 287.7799987792969,
+      "close": 290.4599914550781,
+      "volume": 41750160
+    },
+    {
+      "epoch": 1781026200.0,
+      "open": 290.44000244140625,
+      "high": 291.9200134277344,
+      "low": 288.79998779296875,
+      "close": 290.3599853515625,
+      "volume": 16884603
+    },
+    {
+      "epoch": 1781098200.0,
+      "open": 290.7650146484375,
+      "high": 293.2294921875,
+      "low": 287.3800048828125,
+      "close": 293.15008544921875,
+      "volume": 26739292
+    },
+    {
+      "epoch": 1781112600.0,
+      "open": 293.1600036621094,
+      "high": 294.7449951171875,
+      "low": 291.3900146484375,
+      "close": 291.5,
+      "volume": 15912551
+    },
+    {
+      "epoch": 1781184600.0,
+      "open": 293.7200012207031,
+      "high": 296.0,
+      "low": 289.6000061035156,
+      "close": 295.9549865722656,
+      "volume": 18862006
+    },
+    {
+      "epoch": 1781199000.0,
+      "open": 295.989990234375,
+      "high": 297.0,
+      "low": 294.70001220703125,
+      "close": 295.3599853515625,
+      "volume": 12952821
+    },
+    {
+      "epoch": 1781271000.0,
+      "open": 296.0799865722656,
+      "high": 297.1400146484375,
+      "low": 290.010009765625,
+      "close": 291.4601135253906,
+      "volume": 20360323
+    },
+    {
+      "epoch": 1781285400.0,
+      "open": 291.4800109863281,
+      "high": 291.6400146484375,
+      "low": 289.6199951171875,
+      "close": 291.0799865722656,
+      "volume": 10149513
+    },
+    {
+      "epoch": 1781530200.0,
+      "open": 294.1199951171875,
+      "high": 297.7799987792969,
+      "low": 291.70001220703125,
+      "close": 296.6600036621094,
+      "volume": 20263933
+    },
+    {
+      "epoch": 1781544600.0,
+      "open": 296.6600036621094,
+      "high": 297.0,
+      "low": 294.9599914550781,
+      "close": 296.4200134277344,
+      "volume": 24844881
+    },
+    {
+      "epoch": 1781616600.0,
+      "open": 295.2449951171875,
+      "high": 300.4800109863281,
+      "low": 293.9700012207031,
+      "close": 300.2749938964844,
+      "volume": 19090391
+    },
+    {
+      "epoch": 1781631000.0,
+      "open": 300.260009765625,
+      "high": 300.4599914550781,
+      "low": 298.2200012207031,
+      "close": 299.25,
+      "volume": 10468754
+    },
+    {
+      "epoch": 1781703000.0,
+      "open": 300.8450012207031,
+      "high": 302.07000732421875,
+      "low": 296.57000732421875,
+      "close": 296.80999755859375,
+      "volume": 16856335
+    },
+    {
+      "epoch": 1781717400.0,
+      "open": 296.79998779296875,
+      "high": 297.6000061035156,
+      "low": 294.3800048828125,
+      "close": 295.8800048828125,
+      "volume": 12093112
+    },
+    {
+      "epoch": 1781789400.0,
+      "open": 298.44000244140625,
+      "high": 300.57000732421875,
+      "low": 295.6199951171875,
+      "close": 297.82000732421875,
+      "volume": 42636626
+    },
+    {
+      "epoch": 1781803800.0,
+      "open": 297.82501220703125,
+      "high": 299.2394104003906,
+      "low": 297.010009765625,
+      "close": 297.8900146484375,
+      "volume": 10408565
+    }
+  ]
+}
\ No newline at end of file
diff --git a/apps/backend/tests/fixtures/yahoo/AAPL_5m_20260601_20260618.json b/apps/backend/tests/fixtures/yahoo/AAPL_5m_20260601_20260618.json
new file mode 100644
index 0000000..c592284
--- /dev/null
+++ b/apps/backend/tests/fixtures/yahoo/AAPL_5m_20260601_20260618.json
@@ -0,0 +1,8744 @@
+{
+  "symbol": "AAPL",
+  "timeframe": "5m",
+  "start": "2026-06-01T13:30:00Z",
+  "end": "2026-06-18T19:55:00Z",
+  "bars": [
+    {
+      "epoch": 1780320600.0,
+      "open": 309.5350036621094,
+      "high": 310.67999267578125,
+      "low": 308.5,
+      "close": 310.0299987792969,
+      "volume": 3861073
+    },
+    {
+      "epoch": 1780320900.0,
+      "open": 310.010009765625,
+      "high": 310.92999267578125,
+      "low": 309.5899963378906,
+      "close": 309.8799133300781,
+      "volume": 717238
+    },
+    {
+      "epoch": 1780321200.0,
+      "open": 309.8500061035156,
+      "high": 310.1000061035156,
+      "low": 309.1600036621094,
+      "close": 309.5255126953125,
+      "volume": 633466
+    },
+    {
+      "epoch": 1780321500.0,
+      "open": 309.54998779296875,
+      "high": 310.29998779296875,
+      "low": 309.2799987792969,
+      "close": 310.1199951171875,
+      "volume": 575764
+    },
+    {
+      "epoch": 1780321800.0,
+      "open": 310.1499938964844,
+      "high": 310.6199951171875,
+      "low": 309.3399963378906,
+      "close": 309.3999938964844,
+      "volume": 631506
+    },
+    {
+      "epoch": 1780322100.0,
+      "open": 309.40008544921875,
+      "high": 310.4100036621094,
+      "low": 309.1499938964844,
+      "close": 310.0400085449219,
+      "volume": 523833
+    },
+    {
+      "epoch": 1780322400.0,
+      "open": 310.0799865722656,
+      "high": 310.25,
+      "low": 309.1199951171875,
+      "close": 309.19000244140625,
+      "volume": 623325
+    },
+    {
+      "epoch": 1780322700.0,
+      "open": 309.1899108886719,
+      "high": 310.1199951171875,
+      "low": 309.1449890136719,
+      "close": 309.7950134277344,
+      "volume": 580451
+    },
+    {
+      "epoch": 1780323000.0,
+      "open": 309.82000732421875,
+      "high": 309.82000732421875,
+      "low": 309.1700134277344,
+      "close": 309.7090148925781,
+      "volume": 445256
+    },
+    {
+      "epoch": 1780323300.0,
+      "open": 309.70001220703125,
+      "high": 310.1499938964844,
+      "low": 309.55999755859375,
+      "close": 309.6099853515625,
+      "volume": 507673
+    },
+    {
+      "epoch": 1780323600.0,
+      "open": 309.6199951171875,
+      "high": 309.94989013671875,
+      "low": 308.9599914550781,
+      "close": 308.9798889160156,
+      "volume": 498902
+    },
+    {
+      "epoch": 1780323900.0,
+      "open": 308.9750061035156,
+      "high": 308.9800109863281,
+      "low": 307.79998779296875,
+      "close": 307.8399963378906,
+      "volume": 576712
+    },
+    {
+      "epoch": 1780324200.0,
+      "open": 307.80999755859375,
+      "high": 308.4700012207031,
+      "low": 307.5899963378906,
+      "close": 307.5950012207031,
+      "volume": 662415
+    },
+    {
+      "epoch": 1780324500.0,
+      "open": 307.6000061035156,
+      "high": 308.0799865722656,
+      "low": 307.54998779296875,
+      "close": 307.6099853515625,
+      "volume": 565304
+    },
+    {
+      "epoch": 1780324800.0,
+      "open": 307.6099853515625,
+      "high": 307.80999755859375,
+      "low": 307.3500061035156,
+      "close": 307.79998779296875,
+      "volume": 469652
+    },
+    {
+      "epoch": 1780325100.0,
+      "open": 307.8299865722656,
+      "high": 307.8299865722656,
+      "low": 306.6099853515625,
+      "close": 306.84600830078125,
+      "volume": 600247
+    },
+    {
+      "epoch": 1780325400.0,
+      "open": 306.8114929199219,
+      "high": 306.9800109863281,
+      "low": 306.57000732421875,
+      "close": 306.8533935546875,
+      "volume": 721320
+    },
+    {
+      "epoch": 1780325700.0,
+      "open": 306.8500061035156,
+      "high": 307.125,
+      "low": 306.55999755859375,
+      "close": 306.9700012207031,
+      "volume": 415123
+    },
+    {
+      "epoch": 1780326000.0,
+      "open": 306.9700012207031,
+      "high": 307.42999267578125,
+      "low": 306.8900146484375,
+      "close": 307.260009765625,
+      "volume": 365586
+    },
+    {
+      "epoch": 1780326300.0,
+      "open": 307.239990234375,
+      "high": 307.5386047363281,
+      "low": 306.93499755859375,
+      "close": 306.94000244140625,
+      "volume": 389285
+    },
+    {
+      "epoch": 1780326600.0,
+      "open": 306.95001220703125,
+      "high": 306.9898986816406,
+      "low": 306.29998779296875,
+      "close": 306.80999755859375,
+      "volume": 561422
+    },
+    {
+      "epoch": 1780326900.0,
+      "open": 306.83990478515625,
+      "high": 307.0899963378906,
+      "low": 306.5199890136719,
+      "close": 306.6499938964844,
+      "volume": 339366
+    },
+    {
+      "epoch": 1780327200.0,
+      "open": 306.6499938964844,
+      "high": 306.7300109863281,
+      "low": 306.4700012207031,
+      "close": 306.57000732421875,
+      "volume": 295071
+    },
+    {
+      "epoch": 1780327500.0,
+      "open": 306.5899963378906,
+      "high": 306.73748779296875,
+      "low": 306.4700012207031,
+      "close": 306.5751037597656,
+      "volume": 306215
+    },
+    {
+      "epoch": 1780327800.0,
+      "open": 306.55999755859375,
+      "high": 307.1700134277344,
+      "low": 306.5199890136719,
+      "close": 307.0,
+      "volume": 527259
+    },
+    {
+      "epoch": 1780328100.0,
+      "open": 306.9901123046875,
+      "high": 307.17999267578125,
+      "low": 306.75,
+      "close": 306.9150085449219,
+      "volume": 576225
+    },
+    {
+      "epoch": 1780328400.0,
+      "open": 306.9100036621094,
+      "high": 307.260009765625,
+      "low": 306.7300109863281,
+      "close": 306.79998779296875,
+      "volume": 381863
+    },
+    {
+      "epoch": 1780328700.0,
+      "open": 306.80499267578125,
+      "high": 307.0400085449219,
+      "low": 306.4800109863281,
+      "close": 306.6499938964844,
+      "volume": 484422
+    },
+    {
+      "epoch": 1780329000.0,
+      "open": 306.6549987792969,
+      "high": 306.82000732421875,
+      "low": 306.45001220703125,
+      "close": 306.7699890136719,
+      "volume": 252118
+    },
+    {
+      "epoch": 1780329300.0,
+      "open": 306.7699890136719,
+      "high": 307.0,
+      "low": 306.760009765625,
+      "close": 306.8399963378906,
+      "volume": 219692
+    },
+    {
+      "epoch": 1780329600.0,
+      "open": 306.8299865722656,
+      "high": 306.9800109863281,
+      "low": 306.7900085449219,
+      "close": 306.8525085449219,
+      "volume": 202624
+    },
+    {
+      "epoch": 1780329900.0,
+      "open": 306.8500061035156,
+      "high": 306.8800048828125,
+      "low": 306.6099853515625,
+      "close": 306.7900085449219,
+      "volume": 305511
+    },
+    {
+      "epoch": 1780330200.0,
+      "open": 306.7900085449219,
+      "high": 306.7926940917969,
+      "low": 306.05999755859375,
+      "close": 306.0600891113281,
+      "volume": 311909
+    },
+    {
+      "epoch": 1780330500.0,
+      "open": 306.05999755859375,
+      "high": 306.2200012207031,
+      "low": 305.7250061035156,
+      "close": 305.9750061035156,
+      "volume": 402286
+    },
+    {
+      "epoch": 1780330800.0,
+      "open": 305.9750061035156,
+      "high": 306.0199890136719,
+      "low": 305.635009765625,
+      "close": 305.7850036621094,
+      "volume": 251600
+    },
+    {
+      "epoch": 1780331100.0,
+      "open": 305.7799987792969,
+      "high": 305.79998779296875,
+      "low": 305.489990234375,
+      "close": 305.7200012207031,
+      "volume": 256301
+    },
+    {
+      "epoch": 1780331400.0,
+      "open": 305.739990234375,
+      "high": 306.20001220703125,
+      "low": 305.6499938964844,
+      "close": 306.0198974609375,
+      "volume": 336029
+    },
+    {
+      "epoch": 1780331700.0,
+      "open": 306.0,
+      "high": 306.0299987792969,
+      "low": 305.7500915527344,
+      "close": 305.80999755859375,
+      "volume": 218309
+    },
+    {
+      "epoch": 1780332000.0,
+      "open": 305.8299865722656,
+      "high": 306.14898681640625,
+      "low": 305.8200988769531,
+      "close": 306.07000732421875,
+      "volume": 207425
+    },
+    {
+      "epoch": 1780332300.0,
+      "open": 306.07000732421875,
+      "high": 306.1199951171875,
+      "low": 305.8949890136719,
+      "close": 306.05999755859375,
+      "volume": 208326
+    },
+    {
+      "epoch": 1780332600.0,
+      "open": 306.05499267578125,
+      "high": 306.3800048828125,
+      "low": 306.0,
+      "close": 306.2449951171875,
+      "volume": 727557
+    },
+    {
+      "epoch": 1780332900.0,
+      "open": 306.2699890136719,
+      "high": 306.5299987792969,
+      "low": 306.010009765625,
+      "close": 306.19500732421875,
+      "volume": 284428
+    },
+    {
+      "epoch": 1780333200.0,
+      "open": 306.2200012207031,
+      "high": 306.25,
+      "low": 305.4700012207031,
+      "close": 305.70001220703125,
+      "volume": 290726
+    },
+    {
+      "epoch": 1780333500.0,
+      "open": 305.70001220703125,
+      "high": 305.760009765625,
+      "low": 305.0299987792969,
+      "close": 305.1099853515625,
+      "volume": 366159
+    },
+    {
+      "epoch": 1780333800.0,
+      "open": 305.106201171875,
+      "high": 305.7799987792969,
+      "low": 305.0899963378906,
+      "close": 305.7300109863281,
+      "volume": 270167
+    },
+    {
+      "epoch": 1780334100.0,
+      "open": 305.7300109863281,
+      "high": 305.739990234375,
+      "low": 305.25,
+      "close": 305.29998779296875,
+      "volume": 246051
+    },
+    {
+      "epoch": 1780334400.0,
+      "open": 305.2699890136719,
+      "high": 305.6600036621094,
+      "low": 305.25,
+      "close": 305.6400146484375,
+      "volume": 225760
+    },
+    {
+      "epoch": 1780334700.0,
+      "open": 305.6300048828125,
+      "high": 306.510009765625,
+      "low": 305.6199951171875,
+      "close": 306.4700012207031,
+      "volume": 324898
+    },
+    {
+      "epoch": 1780335000.0,
+      "open": 306.5199890136719,
+      "high": 306.6300048828125,
... [diff_bound] apps/backend/tests/fixtures/yahoo/AAPL_5m_20260601_20260618.json: 8351 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_tradability.py b/apps/backend/tests/test_tradability.py
new file mode 100644
index 0000000..e4f39ae
--- /dev/null
+++ b/apps/backend/tests/test_tradability.py
@@ -0,0 +1,602 @@
+"""The tradable level map (era-5B capability 1, J-01) -- ``research/tradability.py`` unit +
+fixture coverage. Mirrors ``test_levels.py``'s structure: a small synthetic fixture gives full
+control over exact expected numbers (band clustering, quality-score arithmetic, round-number
+flagging, class inheritance, and top-K capping all verified by direct computation, not
+hand-derived), then the real committed AAPL fixture proves the SAME mechanisms hold end to end on
+real data and satisfy J-01's pinned acceptance (the 2026-06-22 map's 300.48-302.07 resistance
+band).
+
+The synthetic ``SYN-TRADABILITY`` fixture (7 daily bars, symbol isolated from every other test)
+deliberately spaces every day's OHLC values far apart (>>20 bps, the raw confluence tolerance) so
+``compute_confluence_zones`` returns [] for every price EXCEPT four deliberately engineered
+same-day swing-pivot/prior-period-extreme coincidences (170, 190, 220, 250 -- each day's own
+extreme is ALSO a swing pivot), which each form a genuine 2-member, class-C zone. This gives one
+fixture that exercises BOTH ``class`` outcomes (a real inherited grade, and the honest ``None``
+absence) without needing a second, multi-timeframe fixture.
+"""
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
+from app.research.tradability import RESISTANCE, SUPPORT, compute_tradability
+
+FIXTURE_YAHOO_DIR = Path(__file__).parent / "fixtures" / "yahoo"
+
+_DAY = 86400.0
+_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()
+_SYN_SYMBOL = "SYN-TRADABILITY"
+
+
+def _epoch(iso: str) -> float:
+    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
+
+
+def _syn_bar(day_index: int, high: float, low: float, close: float) -> RawBar:
+    return RawBar(_SYN_SYMBOL, "1d", _BASE + day_index * _DAY, close, high, low, close, 1_000)
+
+
+# Eight days total (index 0..7): the CORE seven days every test in this file relies on, plus an
+# EIGHTH ("day 7", 2026-01-08) used only by the no-lookahead / basis-shift tests below -- kept as
+# ONE canonical sequence (never two independently-typed literals) so "truncated to N days" always
+# means an exact PREFIX of the same real values.
+#
+# Day 6 (2026-01-07) is the most recent CORE bar; every core test uses
+# ``as_of = _SYN_AS_OF`` (2026-01-08), so day 6 is the prior completed session and
+# ``current_price`` (day 6's own close) is exactly 100 -- everything above it is a resistance
+# candidate, everything at-or-below is a support candidate.
+#
+# Engineered swing pivots among days 0-6 (lookback=1, verified by direct computation): LOW @190
+# (day 2), HIGH @250 (day 3), LOW @170 (day 4), HIGH @220 (day 5) -- each price EXACTLY coincides
+# with that same day's own prior-period-extreme high/low, so ``compute_confluence_zones`` forms a
+# genuine (same-timeframe, class-C) 2-member zone at each of those four prices. Every other day's
+# OHLC values are pairwise >> 20 bps apart (no accidental confluence) and >> 70 bps apart across
+# days (no accidental tradability-band merging) -- so every OTHER resistance/support price ends up
+# its own singleton band with an honest ``class: None`` (no overlapping zone). Day 7's values
+# (999/998/998.5) are deliberately far outside every other day's range -- an unmissable canary for
+# "did a bar dated on/after the requested session leak into the result".
+_SYN_BAR_SEQUENCE: tuple[RawBar, ...] = (
+    _syn_bar(0, 500, 490, 495),
+    _syn_bar(1, 400, 390, 395),
+    _syn_bar(2, 200, 190, 195),
+    _syn_bar(3, 250, 240, 245),
+    _syn_bar(4, 180, 170, 175),
+    _syn_bar(5, 220, 210, 215),
+    _syn_bar(6, 105, 95, 100),
+    _syn_bar(7, 999, 998, 998.5),
+)
+
+
+def _seed_synthetic(store: BarStore, num_days: int = 7) -> None:
+    """Records the first ``num_days`` bars of ``_SYN_BAR_SEQUENCE`` as ONE ``"1d"`` series (a
+    single ``record()`` call, the ``test_levels.py`` lookahead-proof precedent -- never several
+    calls, which would register several INDEPENDENT series and silently change which one
+    ``_select_daily_series``'s most-recently-created tie-break picks)."""
+    bars = list(_SYN_BAR_SEQUENCE[:num_days])
+    window_end = datetime.fromtimestamp(_BASE + num_days * _DAY, tz=timezone.utc).isoformat().replace("+00:00", "Z")
+    store.record(
+        symbol=_SYN_SYMBOL, timeframe="1d",
+        window_start_utc="2026-01-01T00:00:00Z", window_end_utc=window_end,
+        feed="sip", bars=bars,
+    )
+
+
+_SYN_AS_OF = _BASE + 7 * _DAY  # 2026-01-08 -- one session after the last CORE (2026-01-07) bar
+
+
+def _by_price(bands: list[dict]) -> dict[float, dict]:
+    return {b["price_low"]: b for b in bands}
+
+
+# --- Band clustering + quality scoring: exact values on the synthetic fixture -----------------
+
+
+def test_synthetic_fixture_resistance_bands_exact_values(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    _seed_synthetic(store)
+    result = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
+
+    assert result["no_bar_series_for_symbol"] is False
+    assert result["basis_as_of"] == "2026-01-07T00:00:00.000000Z"
+
+    resistance = [b for b in result["bands"] if b["side"] == RESISTANCE]
+    assert len(resistance) == CONFIG.tradability_band_cap_per_side == 5
+    by_price = _by_price(resistance)
+    assert set(by_price) == {250.0, 200.0, 400.0, 500.0, 105.0}
+
+    # Served order is already descending by quality score (side, then -score, then price).
+    assert [b["price_low"] for b in resistance] == [250.0, 200.0, 400.0, 500.0, 105.0]
+
+    # Band @250: the ENGINEERED 2-member band (a real swing-pivot + prior-period-extreme
+    # coincidence) -- breadth=1 (both members are "1d"), touch_total=2 (touch_count 1 each),
+    # round_number=True (250 is an exact multiple of the 50-point increment), and an INHERITED
+    # class (a genuine class-C zone exists at this exact price -- never re-graded here).
+    band_250 = by_price[250.0]
+    assert band_250["price_high"] == 250.0
+    assert band_250["member_count"] == 2
+    assert {m["type"] for m in band_250["members"]} == {"prior-period-extreme", "swing-pivot"}
+    assert band_250["round_number"] is True
+    assert band_250["class"] == "C"
+    assert band_250["quality_score"] == pytest.approx(10 * 1 + 2 * 2 + 20 * 1 + 15 * (4 / 7))
+
+    # Bands @200/@400/@500: true singletons (no swing-pivot coincidence at these prices) --
+    # round_number=True (each an exact multiple of 50) but class=None: NO confluence zone
+    # overlaps a lone level with no confluence partner (levels.py's own honest absence,
+    # never re-graded/defaulted here).
+    for price, day_index in ((200.0, 2), (400.0, 1), (500.0, 0)):
+        band = by_price[price]
+        assert band["price_high"] == price
+        assert band["member_count"] == 1
+        assert band["round_number"] is True
+        assert band["class"] is None
+        expected = 10 * 1 + 2 * 1 + 20 * 1 + 15 * ((day_index + 1) / 7)
+        assert band["quality_score"] == pytest.approx(expected)
+
+    # Band @105 (day 6's own high): singleton, NOT a round number (105 is 5 away from the
+    # nearest 50-multiple, outside the default tolerance), most recent bar (recency == 1.0).
+    band_105 = by_price[105.0]
+    assert band_105["member_count"] == 1
+    assert band_105["round_number"] is False
+    assert band_105["class"] is None
+    assert band_105["quality_score"] == pytest.approx(10 * 1 + 2 * 1 + 0 + 15 * 1.0)
+
+
+def test_synthetic_fixture_support_bands_exact_values(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    _seed_synthetic(store)
+    result = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
+
+    support = [b for b in result["bands"] if b["side"] == SUPPORT]
+    assert len(support) == 2  # day 6's own low (95) and close (100) -- the only two candidates
+    by_price = _by_price(support)
+    assert set(by_price) == {100.0, 95.0}
+    assert [b["price_low"] for b in support] == [100.0, 95.0]  # already served by descending score
+
+    # 100 == current_price itself (side classification is price <= current_price -> support) AND
+    # an exact multiple of 50 -- the highest-scoring band in the whole fixture.
+    band_100 = by_price[100.0]
+    assert band_100["round_number"] is True
+    assert band_100["class"] is None
+    assert band_100["quality_score"] == pytest.approx(10 * 1 + 2 * 1 + 20 * 1 + 15 * 1.0)
+    assert band_100["quality_score"] == 47.0
+
+    band_95 = by_price[95.0]
+    assert band_95["round_number"] is False
+    assert band_95["quality_score"] == pytest.approx(10 * 1 + 2 * 1 + 0 + 15 * 1.0)
+    assert band_95["quality_score"] == 27.0
+
+    # current_price == 100.0 is itself in the SUPPORT bucket (side is `price <= current_price`,
+    # never a fabricated third "at the price" side) -- the class-A/B/C "side" concept stays binary.
+    assert band_100["price_high"] == 100.0
+
+
+# --- Top-K-per-side capping -----------------------------------------------------------------
+
+
+def test_band_cap_per_side_drops_lower_scoring_bands(tmp_path):
+    """The SAME synthetic fixture with ``tradability_band_cap_per_side=3`` keeps only the THREE
+    highest-scoring resistance bands (250, 200, 400) and drops the two lowest (500, 105) -- a
+    direct proof the cap is enforced by SCORE rank, not by insertion/price order (500 > 105 in
+    price, yet 500 survives and 105 does not; both are dropped to make room for 400, whose SCORE
+    beats both)."""
+    store = BarStore(tmp_path / "bars")
+    _seed_synthetic(store)
+    capped_config = Config(tradability_band_cap_per_side=3)
+    result = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, capped_config)
+
+    resistance = [b for b in result["bands"] if b["side"] == RESISTANCE]
+    assert len(resistance) == 3
+    assert [b["price_low"] for b in resistance] == [250.0, 200.0, 400.0]
+
+    # The support side (only 2 real candidates) is unaffected by a cap of 3 -- never padded.
+    support = [b for b in result["bands"] if b["side"] == SUPPORT]
+    assert len(support) == 2
+
+
+# --- Determinism + no-lookahead ---------------------------------------------------------------
+
+
+def test_repeat_call_determinism(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    _seed_synthetic(store)
+    first = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
+    second = compute_tradability(BarStore(tmp_path / "bars"), _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
+    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
+    assert len(first["bands"]) >= 1, "the proof must exercise at least one real band"
+
+
+def test_no_lookahead_shifting_as_of_within_the_same_session_is_unchanged(tmp_path):
+    """Every instant inside the SAME calendar session (2026-01-08) must resolve to the identical
+    basis and produce byte-identical output -- the morning-markup as-of resolution keys off the
+    calendar DATE, never the clock time within it."""
+    store = BarStore(tmp_path / "bars")
+    _seed_synthetic(store)
+    early = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)  # 2026-01-08T00:00:00Z
+    late = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF + 23 * 3600, CONFIG)  # same day, 23:00
+    assert json.dumps(early, sort_keys=True) == json.dumps(late, sort_keys=True)
+
+
+def test_no_lookahead_a_later_session_shifts_the_basis_forward(tmp_path):
+    """A request one session later (2026-01-09), against a store that ALSO has the eighth
+    (2026-01-08) bar recorded, resolves its basis to 2026-01-08 (the NEW prior session), never
+    staying pinned to 2026-01-07 -- proves the resolver tracks the requested session, not a
+    stale/cached prior answer."""
+    store = BarStore(tmp_path / "bars")
+    _seed_synthetic(store, num_days=8)
+    next_session = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF + _DAY, CONFIG)
+    assert next_session["basis_as_of"] == "2026-01-08T00:00:00.000000Z"
+
+
+def test_no_lookahead_bars_after_the_basis_never_affect_the_result(tmp_path):
+    """The definitive proof (the ``test_levels.py`` lookahead-free precedent): a store holding
+    ONLY the seven CORE bars (through the resolved basis) produces output IDENTICAL to a store
+    that ALSO holds the eighth bar (2026-01-08, dated strictly on/after the requested session,
+    with unmissable canary prices 999/998/998.5) -- the later bar can never leak into a request
+    still resolved to the day-6 basis. Both series are recorded as a SINGLE ``record()`` call each
+    (``_seed_synthetic``'s own discipline) so this is a true prefix-truncation, not two
+    independently-selected series."""
+    full_store = BarStore(tmp_path / "full")
+    _seed_synthetic(full_store, num_days=8)
+    truncated_store = BarStore(tmp_path / "truncated")
+    _seed_synthetic(truncated_store, num_days=7)
+
+    full_result = compute_tradability(full_store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
+    truncated_result = compute_tradability(truncated_store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
+    assert json.dumps(full_result, sort_keys=True) == json.dumps(truncated_result, sort_keys=True)
+    assert not any(m["price"] == 999.0 for b in full_result["bands"] for m in b["members"])
+
+
+# --- Honest, distinct failure states (never one bare ambiguous empty array) ------------------
+
+
+def test_symbol_with_no_recorded_bar_series_is_a_distinct_honest_state(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    _seed_synthetic(store)  # records ONLY `_SYN_SYMBOL` -- never the queried symbol below
+    result = compute_tradability(store, "NEVER-RECORDED", _SYN_AS_OF, CONFIG)
+    assert result == {"bands": [], "no_bar_series_for_symbol": True, "basis_as_of": None}
+
+
+def test_empty_bar_store_is_no_bar_series_for_symbol(tmp_path):
+    store = BarStore(tmp_path / "bars")  # never recorded anything at all
+    result = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
+    assert result == {"bands": [], "no_bar_series_for_symbol": True, "basis_as_of": None}
+
+
+def test_series_exist_but_none_is_daily_is_honest_empty_not_no_bar_series(tmp_path):
+    """A symbol WITH a recorded (non-daily) series is a DISTINCT honest state from "no series at
+    all": ``no_bar_series_for_symbol`` mirrors ``levels.py``'s exact meaning (true only when
+    NOTHING is recorded for the symbol), so this case reports ``False`` with an honest empty map
+    -- never a fabricated basis resolved from the wrong timeframe."""
+    store = BarStore(tmp_path / "bars")
+    store.record(
+        symbol=_SYN_SYMBOL, timeframe="1h", window_start_utc="2026-01-01T00:00:00Z",
+        window_end_utc="2026-01-02T00:00:00Z", feed="sip",
+        bars=[RawBar(_SYN_SYMBOL, "1h", _BASE, 100, 101, 99, 100.5, 1_000)],
+    )
+    result = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
+    assert result == {"bands": [], "no_bar_series_for_symbol": False, "basis_as_of": None}
+
+
+def test_as_of_before_any_prior_session_is_honest_empty(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    _seed_synthetic(store)
+    result = compute_tradability(store, _SYN_SYMBOL, _BASE - 1, CONFIG)  # before the series starts
+    assert result == {"bands": [], "no_bar_series_for_symbol": False, "basis_as_of": None}
+
+
+def test_as_of_on_the_first_recorded_session_has_no_prior_session_yet(tmp_path):
+    """``as_of`` inside day 0's OWN session: no session precedes it in the store, so no basis
+    resolves at all -- distinct from (but as honest as) the ``no_bar_series_for_symbol`` state."""
+    store = BarStore(tmp_path / "bars")
+    _seed_synthetic(store)
+    result = compute_tradability(store, _SYN_SYMBOL, _BASE, CONFIG)
+    assert result == {"bands": [], "no_bar_series_for_symbol": False, "basis_as_of": None}
+
+
+# --- No magic numbers: every tradability parameter is config-sourced -------------------------
+
+
+def test_tradability_parameters_are_config_sourced_no_magic_numbers():
+    assert isinstance(CONFIG.tradability_band_cap_per_side, int)
+    assert 1 <= CONFIG.tradability_band_cap_per_side <= 5  # goal.md: "K <= 5"
+    assert isinstance(CONFIG.tradability_band_width_bps, float) and CONFIG.tradability_band_width_bps > 0
+    assert isinstance(CONFIG.tradability_quality_weights, dict)
+    assert set(CONFIG.tradability_quality_weights) == {
+        "timeframe_breadth", "touch_count", "recency", "round_number",
+    }
+    assert all(isinstance(w, float) and w >= 0 for w in CONFIG.tradability_quality_weights.values())
+    assert isinstance(CONFIG.tradability_round_number_increment, float)
+    assert CONFIG.tradability_round_number_increment > 0
+    assert isinstance(CONFIG.tradability_round_number_tolerance_bps, float)
+    assert CONFIG.tradability_round_number_tolerance_bps > 0
+
+    from app.research import tradability as tradability_module
+
+    src = inspect.getsource(tradability_module)
+    assert "config.tradability_band_cap_per_side" in src
+    assert "config.tradability_band_width_bps" in src
+    assert "config.tradability_quality_weights" in src
+    assert "config.tradability_round_number_increment" in src
+    assert "config.tradability_round_number_tolerance_bps" in src
+
+
+def test_tradability_config_fields_are_excluded_from_config_fingerprint():
+    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    assert Config(tradability_band_cap_per_side=1).config_fingerprint() == CONFIG.config_fingerprint()
+    assert Config(tradability_band_width_bps=999.0).config_fingerprint() == CONFIG.config_fingerprint()
+    assert (
+        Config(tradability_quality_weights={"timeframe_breadth": 1.0}).config_fingerprint()
+        == CONFIG.config_fingerprint()
+    )
+    assert (
+        Config(tradability_round_number_increment=1.0).config_fingerprint() == CONFIG.config_fingerprint()
+    )
+    assert (
+        Config(tradability_round_number_tolerance_bps=1.0).config_fingerprint()
+        == CONFIG.config_fingerprint()
+    )
+    # ...while a real classifier threshold still moves it (the counter-test).
+    assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()
+
+
+# --- "Lens, not a second engine": tradability.py never re-detects structure ------------------
+
+
+def test_tradability_module_is_a_lens_never_a_second_levels_engine():
+    """Static-analysis guard for the era-5B critical anti-goal: ``tradability.py`` must consume
+    ``compute_levels`` output verbatim -- it must never import or CALL a pivot/prior-period
+    detection internal, and it must never read ``levels.py``'s frozen ``sr_pivot_lookback`` /
+    ``sr_touch_tolerance_bps`` parameters off ``config``. Checks actual imports/calls/attribute
+    reads specifically (never a bare substring match), so this survives the module's own docstring
+    prose NAMING those same precedents when explaining a mirrored technique or tie-break."""
+    from app.research import tradability as tradability_module
+
+    src = inspect.getsource(tradability_module)
+    assert "compute_levels(" in src
+
+    import_lines = [
+        line.strip() for line in src.splitlines() if line.strip().startswith(("import ", "from "))
+    ]
+    levels_imports = [line for line in import_lines if " .levels " in line or line.endswith(".levels")]
+    assert levels_imports == ["from .levels import compute_levels"], (
+        f"the ONLY symbol imported from levels.py must be compute_levels, got {levels_imports!r}"
+    )
+
+    # No CALL to a levels.py pivot/extreme/selection internal, and no READ of a frozen levels.py
+    # config threshold, appears anywhere in the module body.
+    for forbidden_call in (
+        "_swing_pivots(", "_prior_period_extremes(", "_bars_as_of(",
+        "_select_one_series_per_timeframe(", "_cluster_levels(", "_grade_zone(",
+    ):
+        assert forbidden_call not in src, f"tradability.py must not call levels.py internal {forbidden_call!r}"
+    for forbidden_config_read in ("config.sr_pivot_lookback", "config.sr_touch_tolerance_bps"):
+        assert forbidden_config_read not in src, (
+            f"tradability.py must not read the frozen levels.py threshold {forbidden_config_read!r}"
+        )
+
+
+# --- The committed real AAPL fixture: J-01's pinned acceptance -------------------------------
+
+
+def _load_yahoo_fixture(name: str) -> dict:
+    return json.loads((FIXTURE_YAHOO_DIR / name).read_text())
+
+
+def _seed_yahoo_fixture(store: BarStore, fixture: dict) -> None:
+    bars = [
... [diff_bound] apps/backend/tests/test_tradability.py: 208 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_tradability_api.py b/apps/backend/tests/test_tradability_api.py
new file mode 100644
index 0000000..a0d72f4
--- /dev/null
+++ b/apps/backend/tests/test_tradability_api.py
@@ -0,0 +1,268 @@
+"""The ``GET /research/tradability`` endpoint (era-5B capability 1, J-01) -- route-level
+integration. Mirrors ``test_levels_api.py``'s ``ctx`` fixture (TestClient + temp bar dir + injected
+``FakeAdapter``): a small ``"1d"`` series is recorded through the REAL ``POST /research/bars``
+route, then ``GET /research/tradability`` is read back -- the full request path, not a direct
+module call (``test_tradability.py`` covers the pure computation's exact values in isolation). The
+committed real AAPL fixture is seeded directly into the temp bar dir (the ``test_levels_api.py`` /
+``test_mcp_server.py`` technique) to prove J-01's pinned acceptance end to end through the real
+route.
+"""
+
+from __future__ import annotations
+
+import json
+from datetime import datetime, timedelta, timezone
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
+from app.research.store import JournalStore
+from fakes import FakeAdapter
+
+YAHOO_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "yahoo"
+AAPL_DAILY_FIXTURE = "AAPL_1d_20260101_20260626.json"
+
+SYMBOL = "TRDB"
+TIMEFRAME = "1d"
+_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)
+_DAY = 86400.0
+
+
+def _iso(day_index: int) -> str:
+    return (_BASE + timedelta(days=day_index)).isoformat().replace("+00:00", "Z")
+
+
+def _bar(day_index: int, high: float, low: float, close: float) -> RawBar:
+    return RawBar(SYMBOL, TIMEFRAME, _BASE.timestamp() + day_index * _DAY, close, high, low, close, 1_000)
+
+
+def _daily_bars() -> tuple[RawBar, ...]:
+    # A small 5-day series: day 4 (2026-01-05) is the most recent bar, so a request inside
+    # 2026-01-06 resolves its basis to day 4.
+    return (
+        _bar(0, 50.0, 40.0, 45.0),
+        _bar(1, 60.0, 42.0, 55.0),
+        _bar(2, 52.0, 41.0, 48.0),
+        _bar(3, 58.0, 44.0, 50.0),
+        _bar(4, 100.0, 90.0, 95.0),
+    )
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
+def _inject_adapter(**kwargs) -> FakeAdapter:
+    adapter = FakeAdapter(**kwargs)
+    app.dependency_overrides[get_market_adapter] = lambda: adapter
+    return adapter
+
+
+def _record_daily_bars(client) -> None:
+    _inject_adapter(bars=_daily_bars())
+    r = client.post(
+        "/research/bars",
+        json={"symbol": SYMBOL, "timeframe": TIMEFRAME, "start": _iso(0), "end": _iso(5)},
+    )
+    assert r.status_code == 200, r.text
+
+
+# --- Happy path: the real route wires symbol/as_of through to compute_tradability ------------
+
+
+def test_get_tradability_happy_path_through_the_real_route(ctx):
+    client, _bar_dir = ctx
+    _record_daily_bars(client)
+
+    as_of = _iso(5)  # inside 2026-01-06 -- one session after the last recorded (2026-01-05) bar
+    r = client.get("/research/tradability", params={"symbol": SYMBOL, "as_of": as_of})
+    assert r.status_code == 200
+    body = r.json()
+    assert body["symbol"] == SYMBOL
+    assert body["as_of"] == as_of  # echoed VERBATIM (the get_levels precedent) -- never re-derived
+    assert body["no_bar_series_for_symbol"] is False
+    assert body["basis_as_of"] == "2026-01-05T00:00:00.000000Z"
+    assert isinstance(body["bands"], list) and len(body["bands"]) >= 1
+    for band in body["bands"]:
+        assert set(band) == {
+            "side", "price_low", "price_high", "class", "quality_score",
+            "round_number", "member_count", "members",
+        }
+        assert band["side"] in ("support", "resistance")
+
+
+def test_get_tradability_lowercase_symbol_is_normalized_to_stored_uppercase(ctx):
+    client, _bar_dir = ctx
+    _record_daily_bars(client)
+    r = client.get("/research/tradability", params={"symbol": SYMBOL.lower(), "as_of": _iso(5)})
+    assert r.status_code == 200
+    body = r.json()
+    assert body["symbol"] == SYMBOL
+    assert len(body["bands"]) >= 1
+
+
+# --- The committed real AAPL fixture: J-01's pinned acceptance through the REAL route ----------
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
+def test_get_tradability_aapl_pinned_resistance_band_through_the_real_route(ctx):
+    """J-01's headline acceptance, through the REAL HTTP route (``test_tradability.py`` proves the
+    identical numbers via a direct module call) -- AAPL as of the 2026-06-22 session: <=10 bands
+    total, and the top resistance band contains both 300.48 and 302.07 with round_number=true and
+    an inherited (non-null) class."""
+    client, bar_dir = ctx
+    _seed_yahoo_fixture_into_bar_dir(bar_dir, AAPL_DAILY_FIXTURE)
+
+    as_of = "2026-06-22T15:00:00Z"
+    r = client.get("/research/tradability", params={"symbol": "AAPL", "as_of": as_of})
+    assert r.status_code == 200
+    body = r.json()
+    assert body["symbol"] == "AAPL"
+    assert body["as_of"] == as_of
+    assert body["no_bar_series_for_symbol"] is False
+    assert body["basis_as_of"] == "2026-06-18T04:00:00.000000Z"
+
+    bands = body["bands"]
+    assert len(bands) <= 10
+    resistance = [b for b in bands if b["side"] == "resistance"]
+    support = [b for b in bands if b["side"] == "support"]
+    assert len(resistance) <= 5
+    assert len(support) <= 5
+
+    pinned = next(
+        b for b in resistance if b["price_low"] <= 300.48 and b["price_high"] >= 302.07
+    )
+    pinned_rank = resistance.index(pinned)
+    assert pinned_rank in (0, 1), "the pinned resistance band must rank in the top 2 by quality score"
+    assert pinned["round_number"] is True
+    assert pinned["class"] is not None, "an inherited class must be present, never null"
+
+    # REST == the module's own output, byte-for-byte (single source of truth: the route only
+    # parses/echoes -- it recomputes nothing).
+    from app.research.tradability import compute_tradability
+
+    as_of_epoch = datetime.fromisoformat(as_of.replace("Z", "+00:00")).timestamp()
+    direct = compute_tradability(BarStore(bar_dir), "AAPL", as_of_epoch, CONFIG)
+    assert direct["bands"] == bands
+    assert direct["basis_as_of"] == body["basis_as_of"]
+    assert direct["no_bar_series_for_symbol"] == body["no_bar_series_for_symbol"]
+
+
+def test_frozen_levels_output_is_byte_identical_after_a_tradability_request(ctx):
+    """The critical single-source-of-truth guard, through the REAL routes: requesting the tradable
+    map must not perturb ``GET /research/levels``' own output on the SAME store/as_of."""
+    client, bar_dir = ctx
+    _seed_yahoo_fixture_into_bar_dir(bar_dir, AAPL_DAILY_FIXTURE)
+    levels_as_of = "2026-06-18T04:00:00Z"
+
+    before = client.get("/research/levels", params={"symbol": "AAPL", "as_of": levels_as_of})
+    assert before.status_code == 200
+
+    tradability = client.get(
+        "/research/tradability", params={"symbol": "AAPL", "as_of": "2026-06-22T15:00:00Z"}
+    )
+    assert tradability.status_code == 200
+
+    after = client.get("/research/levels", params={"symbol": "AAPL", "as_of": levels_as_of})
+    assert after.status_code == 200
+    assert before.content == after.content
+
+
+# --- Honest, distinct failure states -----------------------------------------------------------
+
+
+def test_unrecorded_symbol_is_a_distinct_honest_state(ctx):
+    client, _bar_dir = ctx
+    _record_daily_bars(client)  # records SYMBOL only
+    r = client.get("/research/tradability", params={"symbol": "NEVER-RECORDED", "as_of": _iso(5)})
+    assert r.status_code == 200
+    body = r.json()
+    assert body["bands"] == []
+    assert body["no_bar_series_for_symbol"] is True
+    assert body["basis_as_of"] is None
+
+
+def test_no_bar_series_recorded_at_all_is_the_same_distinct_state(ctx):
+    client, _bar_dir = ctx  # nothing recorded at all this run
+    r = client.get("/research/tradability", params={"symbol": SYMBOL, "as_of": _iso(5)})
+    assert r.status_code == 200
+    body = r.json()
+    assert body["bands"] == []
+    assert body["no_bar_series_for_symbol"] is True
+    assert body["basis_as_of"] is None
+
+
+def test_as_of_before_any_recorded_session_is_honest_empty_not_the_prior_state(ctx):
+    client, _bar_dir = ctx
+    _record_daily_bars(client)
+    r = client.get("/research/tradability", params={"symbol": SYMBOL, "as_of": "2020-01-01T00:00:00Z"})
+    assert r.status_code == 200
+    body = r.json()
+    assert body["bands"] == []
+    assert body["no_bar_series_for_symbol"] is False  # distinct from the unrecorded-symbol state
+    assert body["basis_as_of"] is None
+
+
+# --- 422s: never a silent coercion, never a lookahead-leaking "now" default -------------------
+
+
+def test_missing_as_of_is_422(ctx):
+    client, _bar_dir = ctx
+    r = client.get("/research/tradability", params={"symbol": SYMBOL})
+    assert r.status_code == 422
+
+
+def test_missing_symbol_is_422(ctx):
+    client, _bar_dir = ctx
+    r = client.get("/research/tradability", params={"as_of": _iso(5)})
+    assert r.status_code == 422
+
+
+def test_empty_symbol_is_422(ctx):
+    client, _bar_dir = ctx
+    r = client.get("/research/tradability", params={"symbol": "", "as_of": _iso(5)})
+    assert r.status_code == 422
+    assert "symbol" in r.json()["detail"]
+
+
+def test_malformed_as_of_is_422(ctx):
+    client, _bar_dir = ctx
+    r = client.get("/research/tradability", params={"symbol": SYMBOL, "as_of": "not-a-date"})
+    assert r.status_code == 422
+    assert "as_of" in r.json()["detail"]
```
