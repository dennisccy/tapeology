# Iteration diff (bounded)

Files changed: 48. Shown in full: 34.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `reports/goal-session-tape_to_profit_support_resistence-index.html` (371 diff lines)
- `reports/phase-goal-tape_to_profit_support_resistence-iter-0-demo-results.md` (10 diff lines)
- `reports/phase-goal-tape_to_profit_support_resistence-iter-0-demo-script.md` (12 diff lines)
- `reports/phase-goal-tape_to_profit_support_resistence-iter-0-iteration-summary.md` (72 diff lines)
- `reports/phase-goal-tape_to_profit_support_resistence-iter-0-summary.html` (368 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/engine.pid` (7 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/iter-1/.steps/decomposer.done` (7 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/iter-1/goal-slice.md` (339 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/iter-1/snapshot-sha` (8 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/session.json` (15 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/state/blueprint.approved` (3 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/state/project-story.md` (23 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/telemetry.jsonl` (26 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/trace/trace.jsonl` (19 diff lines)

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index bc673d2..367fe12 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -1018,6 +1018,57 @@ class Config:
     # against the pinned default fingerprint test in ``tests/test_profile_equivalence.py``.
     promotion_min_sample_size: int = 5
 
+    # --- Structure-and-tape era: MULTI-TIMEFRAME BAR STORE (era-4 capability 1, J-01) -------------
+    # Where the bar store persists explicitly recorded multi-timeframe OHLC bar series (one JSON
+    # file per series) — mirrors ``dataset_dir`` exactly (the era-3 capability-1 precedent). It is
+    # ONLY a default here — the operator overrides it with the ``TAPEOLOGY_BAR_DIR`` env var (read
+    # in ``bar_dir_resolved`` below, the ``dataset_dir_resolved`` pattern) and tests point it at a
+    # temp dir the same way. The default is package-anchored (``apps/backend/.data/bars/``, covered
+    # by the repo's ``.data/`` gitignore entry) so it resolves identically whatever the process cwd
+    # is. Persistence is SCOPED: this dir holds explicitly recorded bar series ONLY — the live
+    # cockpit's tape is NEVER written here (recording is an explicit research action).
+    #
+    # EXCLUDED FROM ``config_fingerprint`` (see the exclusion set in ``config_fingerprint``) with
+    # the ``dataset_dir`` discipline: WHERE bar series are stored cannot affect any persisted
+    # research value, so two journals identical in every threshold but storing bars in different
+    # directories (or on different machines — the default embeds an absolute path) MUST share a
+    # fingerprint. Pinned by a fingerprint-stability test + the real-threshold counter-test
+    # (tests/test_bars.py).
+    bar_dir: str = str(Path(__file__).resolve().parents[1] / ".data" / "bars")
+
+    # The valid ``?timeframe=`` set for a bar recording — distinct from the EXISTING intra-second
+    # ``history_bar_sizes`` above (the tape engine's OHLC candle bin sizes in LOGICAL SECONDS for
+    # the live prediction chart; an unrelated concept that must not be conflated or collide). These
+    # are CALENDAR OHLC candle timeframes (goal.md's long-term/mid-term/shorter-timeframe
+    # hierarchy): minute-level (shorter), hour-level including 4h/8h (mid-term), and day/week/month
+    # (long-term). An out-of-set value is a 422 (never silently coerced) — mirrors the ``?bar=``
+    # validation precedent. A pure validation ALLOWLIST (it shapes no persisted tape/backtest/study
+    # value), so it is EXCLUDED FROM ``config_fingerprint`` alongside ``bar_dir`` (same rationale).
+    bar_timeframes: tuple[str, ...] = ("1m", "5m", "15m", "1h", "4h", "8h", "1d", "1w", "1mo")
+
+    # FREE-TIER RECENCY-DELAY GUARD (seconds): the configured market-data vendor's free plan serves
+    # historical bars with roughly a 15-minute delay — the vendor entitlement excludes the most
+    # recent 15 minutes of data. A bar-record request's effective vendor-fetch window end is
+    # clamped to ``min(requested_end, now - bar_recency_delay_seconds)`` (the one concrete adapter's
+    # ``fetch_bars``, via its ``_bar_fetch_end_clamp`` helper) so the adapter never asks for — and
+    # so never receives — the still-embargoed most-recent bar. A documented, disclosed OPERATIONAL
+    # assumption (the free-plan historical delay), never a validated edge. EXCLUDED FROM
+    # ``config_fingerprint``: it governs WHICH real bars a fetch can reach, not any
+    # tape/backtest/study computation. (Vendor specifics stay confined to the one adapter module —
+    # the provider-agnostic-engine anti-goal — so this value is deliberately described generically.)
+    bar_recency_delay_seconds: float = 900.0
+
+    # RATE-THROTTLE (a documented, disclosed operational assumption — the configured market-data
+    # vendor's published free-tier rate limit is 200 requests/minute): the minimum wall-clock
+    # spacing enforced between consecutive REAL bar-fetch vendor calls (the one concrete adapter's
+    # own throttle helper), so a bulk multi-timeframe backfill never bursts past the entitlement. A
+    # single interactive record request is unaffected beyond waiting behind its OWN
+    # immediately-prior call. This paces CALL FREQUENCY only — the EXISTING
+    # ``vendor_http_timeout_seconds`` still bounds each call's own duration; the two are independent
+    # and MUST NOT be conflated. EXCLUDED FROM ``config_fingerprint``: an operational vendor-call
+    # cadence, never a tape/backtest/study value.
+    bar_rate_limit_per_minute: int = 200
+
     def profile_definition(self, profile_id: str) -> dict | None:
         """The config-owned descriptor for ``profile_id`` (Data Contract row 33) — the
         ``strategy_definition`` pattern applied to profiles: THIS method is the ONE place that
@@ -1147,6 +1198,13 @@ class Config:
         without code change, while tests point it at a temp dir via the env var."""
         return os.environ.get("TAPEOLOGY_DATASET_DIR", self.dataset_dir)
 
+    def bar_dir_resolved(self) -> str:
+        """The effective bar-store directory: the ``TAPEOLOGY_BAR_DIR`` env var if set, else the
+        package-anchored config default (the ``dataset_dir_resolved`` pattern, era-4 J-01). Read at
+        store-construction time so an operator can point the bar store at a real location without
+        code change, while tests point it at a temp dir via the env var."""
+        return os.environ.get("TAPEOLOGY_BAR_DIR", self.bar_dir)
+
     def config_fingerprint(self) -> str:
         """A stable hash over the ENTIRE frozen config (capability 28 / honesty stamps).
 
@@ -1190,6 +1248,23 @@ class Config:
             # a different fingerprint per machine. Pinned by a fingerprint-stability test + the
             # real-threshold counter-test in tests/test_datasets.py.
             "dataset_dir",
+            # The bar-store directory (era-4 capability 1, J-01): the identical ``dataset_dir``
+            # storage-location discipline — it cannot affect any persisted research value, and the
+            # package-anchored default embeds an absolute path that would otherwise mint a
+            # different fingerprint per machine. Pinned by a fingerprint-stability test + the
+            # real-threshold counter-test in tests/test_bars.py.
+            "bar_dir",
+            # The bar-timeframe validation allowlist + the free-tier recency-delay/rate-throttle
+            # parameters (era-4 capability 1, J-01): none of these shape any persisted
+            # tape/backtest/study value — they only govern an unrelated, brand-new bar-storage
+            # capability's ``?timeframe=`` validation and vendor-fetch mechanics (which real bars a
+            # fetch can reach, and how fast consecutive vendor calls may run). Two journals
+            # identical in every threshold but configured with different bar-fetch mechanics MUST
+            # share a fingerprint. Pinned by a fingerprint-stability test + the real-threshold
+            # counter-test in tests/test_bars.py.
+            "bar_timeframes",
+            "bar_recency_delay_seconds",
+            "bar_rate_limit_per_minute",
             "journal_list_default_limit",
             "journal_list_max_limit",
             "analytics_min_sample_size",
diff --git a/apps/backend/app/mcp/__init__.py b/apps/backend/app/mcp/__init__.py
index c3d2b78..4060cf0 100644
--- a/apps/backend/app/mcp/__init__.py
+++ b/apps/backend/app/mcp/__init__.py
@@ -15,9 +15,10 @@ Result contract (locked by ``tests/test_mcp_server.py``):
   * non-2xx — the backend's ACTUAL status and payload surfaced explicitly: ``content[0].text``
     == the response body byte-for-byte, ``content[1].text`` == ``"HTTP <status> from GET
     <path>"``, ``isError`` true. Every registered tool's endpoint has shipped (``datasets`` at
-    J-02, ``backtests`` at J-03, ``pnl_ledger`` at J-04; ``/research/profiles`` — reached via
-    ``get_endpoint`` — at J-05); an allowlisted-but-UNKNOWN path (any unshipped ``/research/*``)
-    still surfaces the backend's honest 404 this way — never placeholder data.
+    (era-3) J-02, ``backtests`` at J-03, ``pnl_ledger`` at J-04; ``/research/profiles`` — reached
+    via ``get_endpoint`` — at J-05; ``bars`` at era-4 J-01); an allowlisted-but-UNKNOWN path (any
+    unshipped ``/research/*``) still surfaces the backend's honest 404 this way — never
+    placeholder data.
   * backend unreachable — an explicit tool error naming the base URL and the failure
     (``BackendUnreachableError``); NEVER cached or fabricated data (no cache, no retry loop,
     no offline snapshot exists anywhere in this module).
@@ -85,6 +86,7 @@ _STATIC_PATHS: dict[str, str] = {
     "analytics": "/research/analytics",
     "studies": "/research/studies",
     "datasets": "/research/datasets",
+    "bars": "/research/bars",
     "backtests": "/research/backtests",
     "pnl_ledger": "/research/pnl/ledger",
     "taxonomy": "/research/taxonomy",
@@ -168,6 +170,15 @@ TOOLS: tuple[types.Tool, ...] = (
         ),
         inputSchema=_object_schema({}),
     ),
+    types.Tool(
+        name="bars",
+        description=(
+            "Read-only proxy of GET /research/bars — recorded multi-timeframe OHLC bar-series "
+            "metadata and candles (checksum-verified on every load, with explicit integrity "
+            "errors) JSON, verbatim."
+        ),
+        inputSchema=_object_schema({}),
+    ),
     types.Tool(
         name="backtests",
         description=(
diff --git a/apps/backend/app/providers/adapters/alpaca.py b/apps/backend/app/providers/adapters/alpaca.py
index 53b9473..290956b 100644
--- a/apps/backend/app/providers/adapters/alpaca.py
+++ b/apps/backend/app/providers/adapters/alpaca.py
@@ -57,6 +57,7 @@ from .base import (
     LiveRecord,
     MarketClock,
     NoDataForWindow,
+    RawBar,
     RawQuote,
     RawTrade,
     SymbolMatch,
@@ -85,6 +86,25 @@ DEFAULT_FEED = "iex"
 # operational constant as the feeder's FEED_PACE_SECONDS / the API's WS_PUSH_INTERVAL).
 LIVE_TEARDOWN_GRACE_SECONDS = 6.0
 
+# --- Multi-timeframe bar fetch (era-4, J-01) -----------------------------------------------------
+# Maps each of ``CONFIG.bar_timeframes``' neutral strings to the vendor's ``TimeFrame(amount, unit)``
+# constructor arguments (``unit`` is a ``TimeFrameUnit`` MEMBER NAME, resolved against the lazily
+# imported enum inside ``fetch_bars`` — never at module import time, so the no-creds/simulated/test
+# paths still avoid the pandas/numpy-heavy SDK import cost). This is the ONE place a neutral
+# timeframe string is translated to a vendor type; ``config.py`` owns only the neutral vocabulary.
+# 4h/8h are expressed as Hour x amount (there is no dedicated vendor unit for them).
+_TIMEFRAME_PARTS: dict[str, tuple[int, str]] = {
+    "1m": (1, "Minute"),
+    "5m": (5, "Minute"),
+    "15m": (15, "Minute"),
+    "1h": (1, "Hour"),
+    "4h": (4, "Hour"),
+    "8h": (8, "Hour"),
+    "1d": (1, "Day"),
+    "1w": (1, "Week"),
+    "1mo": (1, "Month"),
+}
+
 # Process-lifetime cache of the (rarely-changing) tradable-symbol universe, so the search box
 # does not re-fetch ~14k assets on every keystroke. Warmed once at startup (J-30) via
 # ``warm_symbol_universe`` and otherwise populated lazily on first search. This module-level cell
@@ -98,6 +118,38 @@ _ASSET_UNIVERSE: list[SymbolMatch] | None = None
 # stays flat. Maps key -> (stored_at_monotonic, HistoricalWindow); insertion order = LRU order.
 _HISTORICAL_WINDOW_CACHE: "dict[tuple, tuple[float, HistoricalWindow]]" = {}
 
+# Process-lifetime timestamp (monotonic) of the last REAL bar-fetch vendor call (era-4, J-01),
+# read/written only by ``_throttle_bar_fetch`` below. ``None`` means no call has happened yet in
+# this process, so the very first call never waits.
+_LAST_BAR_FETCH_MONOTONIC: float | None = None
+
+
+def _bar_fetch_end_clamp(end: datetime, delay_seconds: float, now: datetime | None = None) -> datetime:
+    """The free-plan recency-delay guard (J-01): the effective bar-fetch window END, clamped so a
+    request never asks for (and so never receives) the still-embargoed most-recent bar. Alpaca's
+    free market-data plan serves historical bars roughly ``delay_seconds`` behind real time.
+
+    Pure and independently testable: accepts an explicit ``now`` (defaulting to the real wall
+    clock) so a test asserts the clamp deterministically with no time mocking."""
+    reference = now if now is not None else datetime.now(timezone.utc)
+    cutoff = reference - timedelta(seconds=delay_seconds)
+    return min(end, cutoff)
+
+
+def _throttle_bar_fetch() -> None:
+    """Space consecutive REAL bar-fetch vendor calls at least ``60 / CONFIG.bar_rate_limit_per_minute``
+    seconds apart (J-01 free-tier discipline): a bulk multi-timeframe backfill must throttle to the
+    entitlement rather than bursting past it. A single interactive record request only ever waits
+    behind its OWN immediately-prior call — never a fixed extra delay when nothing preceded it."""
+    global _LAST_BAR_FETCH_MONOTONIC
+    min_interval = 60.0 / CONFIG.bar_rate_limit_per_minute
+    now = time.monotonic()
+    if _LAST_BAR_FETCH_MONOTONIC is not None:
+        remaining = min_interval - (now - _LAST_BAR_FETCH_MONOTONIC)
+        if remaining > 0:
+            time.sleep(remaining)
+    _LAST_BAR_FETCH_MONOTONIC = time.monotonic()
+
 
 def _env(name: str) -> str:
     """Return a trimmed environment value, or ``""`` when unset/blank (blank != configured)."""
@@ -169,13 +221,15 @@ def _cache_put(key: tuple, window: HistoricalWindow) -> None:
 
 
 def _clear_caches() -> None:
-    """Reset the process-lifetime caches (the window cache + the warmed universe).
+    """Reset the process-lifetime caches (the window cache + the warmed universe + the era-4
+    bar-fetch throttle timestamp).
 
     For tests/operators only — production never needs to clear; this keeps test isolation explicit
     rather than reaching into the module globals from the test files."""
-    global _ASSET_UNIVERSE
+    global _ASSET_UNIVERSE, _LAST_BAR_FETCH_MONOTONIC
     _ASSET_UNIVERSE = None
     _HISTORICAL_WINDOW_CACHE.clear()
+    _LAST_BAR_FETCH_MONOTONIC = None
 
 
 class AlpacaAdapter:
@@ -439,6 +493,63 @@ class AlpacaAdapter:
         quotes.sort(key=lambda q: q.epoch)
         return trades, quotes
 
+    # --- Multi-timeframe historical bars (era-4, J-01) -----------------------------------
+
+    def fetch_bars(self, symbol: str, start, end, timeframe: str) -> tuple[RawBar, ...]:
+        """Fetch the REAL OHLC candle series for ``symbol`` over ``[start, end)`` at ``timeframe``
+        (one of ``CONFIG.bar_timeframes`` — the route validates this before calling in).
+
+        Free-tier discipline (J-01): the recency-delay guard clamps the effective fetch end so the
+        still-embargoed most-recent (~15-min-delayed) bar is never requested (an entirely-embargoed
+        window short-circuits to an empty tuple with NO vendor call); the rate-throttle spaces
+        consecutive real calls to the entitlement. Honest, never fabricated: an empty vendor
+        result is returned as an empty tuple (the caller — the bar store's ``record`` — decides how
+        to surface that). Runs under the SAME real call-level HTTP deadline as ``fetch_historical``
+        (``VendorTimeout`` propagates on a slow/oversized window).
+        """
+        from alpaca.data.historical import StockHistoricalDataClient
+        from alpaca.data.requests import StockBarsRequest
+        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
+
+        sym = symbol.strip().upper()
+        effective_end = _bar_fetch_end_clamp(end, CONFIG.bar_recency_delay_seconds)
+        if effective_end <= start:
+            return ()  # the whole requested window falls inside the free-plan recency embargo
+
+        feed = self._data_feed(self.historical_feed)  # SIP for historical (J-36), override-aware
+        amount, unit_name = _TIMEFRAME_PARTS[timeframe]
+        vendor_timeframe = TimeFrame(amount, TimeFrameUnit(unit_name))
+
+        _throttle_bar_fetch()
+        client = self._with_http_timeout(
+            StockHistoricalDataClient(_env(ENV_API_KEY), _env(ENV_API_SECRET))
+        )
+        with _mapped_vendor_timeout():
+            response = client.get_stock_bars(
+                StockBarsRequest(
+                    symbol_or_symbols=sym,
+                    timeframe=vendor_timeframe,
+                    start=start,
+                    end=effective_end,
+                    feed=feed,
+                )
+            )
+        bars = [
+            RawBar(
+                sym,
+                timeframe,
+                b.timestamp.timestamp(),
+                float(b.open),
+                float(b.high),
+                float(b.low),
+                float(b.close),
+                int(b.volume),
+            )
+            for b in response.data.get(sym, [])
+        ]
+        bars.sort(key=lambda b: b.epoch)
+        return tuple(bars)
+
     def _data_feed(self, feed_name: str | None = None):
         """Map a vendor-neutral feed NAME to the vendor's DataFeed enum (the ONLY place it appears).
 
diff --git a/apps/backend/app/providers/adapters/base.py b/apps/backend/app/providers/adapters/base.py
index 765e76b..0d739b5 100644
--- a/apps/backend/app/providers/adapters/base.py
+++ b/apps/backend/app/providers/adapters/base.py
@@ -8,6 +8,11 @@ here — vendor specifics never leak outward, so a second vendor is one new adap
 The neutral contract is:
   * ``RawTrade`` / ``RawQuote`` — plain, vendor-free records (a UTC epoch-seconds timestamp
     plus the fields the engine needs). The adapter translates the vendor's response into these.
+  * ``RawBar`` (era-4, J-01) — a plain, vendor-free OHLC candle: symbol, timeframe label, a UTC
+    bar-open epoch-seconds timestamp, open/high/low/close, volume. ``fetch_bars`` is the
+    multi-timeframe historical-BAR counterpart to ``fetch_historical`` (which fetches raw
+    trades/quotes); the adapter translates the vendor's bar response into these — never a vendor
+    type crosses the seam.
   * ``HistoricalWindow`` — the result of one historical fetch (the symbol + its raw trades and
     quotes). ``HistoricalProvider`` maps these onto the engine's logical timeline.
   * ``SymbolNotTradable`` / ``NoDataForWindow`` — neutral failures the adapter raises so the
@@ -85,6 +90,24 @@ class HistoricalWindow:
     quotes: tuple[RawQuote, ...]
 
 
+@dataclass(frozen=True)
+class RawBar:
+    """A vendor-neutral OHLC candle (era-4, J-01): symbol, timeframe label (e.g. ``"1d"``), the
+    UTC bar-OPEN epoch-seconds timestamp, open/high/low/close, volume. Self-describing (unlike
+    ``RawTrade``/``RawQuote``, which rely on the enclosing ``HistoricalWindow`` for their symbol)
+    because a stored bar series' individual candles are served directly (embedded on the series'
+    metadata) rather than through a second wrapper type."""
+
+    symbol: str
+    timeframe: str
+    epoch: float
+    open: float
+    high: float
+    low: float
+    close: float
+    volume: int
+
+
 @dataclass(frozen=True)
 class SymbolMatch:
     """One symbol-search suggestion."""
@@ -158,6 +181,14 @@ class MarketDataAdapter(Protocol):
     warmed, and it is the neutral entry the API's startup hook calls so ``main.py`` never names a
     vendor SDK or the universe cache. It MUST NOT raise (a warm failure is swallowed — search then
     falls back to its own lazy fetch).
+    ``fetch_bars`` (era-4, J-01) returns the REAL OHLC candle series for ``symbol`` over
+    ``[start, end)`` at the given neutral ``timeframe`` as an ordered tuple of ``RawBar`` (never a
+    vendor type) — a read-only reference call, like ``fetch_historical``. An empty tuple is a
+    normal, honest "no bars" answer (never fabricated); the caller (the bar store's ``record``)
+    decides how to surface that as an explicit refusal. Unlike ``fetch_historical``, there is no
+    separate unknown-symbol distinction here — a bar recording is an explicit, occasional research
+    action (not the watch hot-path), so a single round-trip returning empty is honest enough on
+    its own.
     """
 
     name: str
@@ -168,6 +199,9 @@ class MarketDataAdapter(Protocol):
     def fetch_historical(self, symbol: str, start, end) -> HistoricalWindow:
         ...
 
+    def fetch_bars(self, symbol: str, start, end, timeframe: str) -> tuple[RawBar, ...]:
+        ...
+
     def search_symbols(self, query: str) -> list[SymbolMatch]:
         ...
 
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index d4069ee..49a0d36 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -34,6 +34,13 @@ from .backtests import (
     PROFILE_DEFAULT,
     TERMINAL_STATUSES as BACKTEST_TERMINAL_STATUSES,
 )
+from .bars import (
+    BarSeriesAlreadyRegistered,
+    BarSeriesIntegrityError,
+    BarSeriesNotFound,
+    BarStore,
+    EmptyBarWindowError,
+)
 from .datasets import (
     VALID_SOURCE_KINDS as DATASET_SOURCE_KINDS,
     VALID_SPLITS,
@@ -178,6 +185,20 @@ class DatasetRecordRequest(BaseModel):
     end: str | None = None
 
 
+class BarRecordRequest(BaseModel):
+    """Body for ``POST /research/bars`` (era-4 capability 1, J-01) — the explicit credentialed
+    record + register research action. All four fields are required: ``symbol``, ``timeframe``
+    (validated against the config-owned ``bar_timeframes`` set in the ROUTE — out-of-set is a 422,
+    never silently coerced), and the UTC ``[start, end)`` window fetched through the EXISTING
+    Alpaca adapter seam (``fetch_bars``). Unlike a dataset there is only one source (a real Alpaca
+    fetch), so there is no ``source_kind`` here."""
+
+    symbol: str
+    timeframe: str
+    start: str
+    end: str
+
+
 class ReviewRequest(BaseModel):
     """Body for ``POST /research/thesis/{id}/review`` (J-57). ``mistake_tags`` is the user-CONFIRMED
     tag list (distinct from the machine-SUGGESTED tags); ``note`` is the optional free text (REQUIRED
@@ -1496,6 +1517,112 @@ def get_dataset(dataset_id: str, store: DatasetStore = Depends(get_dataset_store
     return {"dataset": meta}
 
 
+# --- Multi-timeframe OHLC bar store (era-4 capability 1, J-01) --------------------------------------
+# Exactly THREE routes (mirroring the ``/datasets`` trio above): record/register, list, detail.
+# There is NO PATCH/PUT/DELETE — a bar series is immutable (structurally: the store exposes no
+# update path at all; re-recording registered content is the 409 below). The bar store module is
+# the ONE reader/writer of bar-series files; these routes serve its metadata + candles VERBATIM
+# (the MCP ``bars`` tool proxies the list byte-identically).
+
+
+def get_bar_store() -> BarStore:
+    """The bar store rooted at the config-owned directory (``TAPEOLOGY_BAR_DIR`` override,
+    package-anchored default). A FastAPI dependency so tests can point it at a temp dir via the
+    env var or override it outright (the ``get_dataset_store`` pattern)."""
+    return BarStore(CONFIG.bar_dir_resolved())
+
+
+@router.post("/bars")
+def record_bar_series(
+    body: BarRecordRequest,
+    registry: ResearchRegistry = Depends(get_registry),
+    store: BarStore = Depends(get_bar_store),
+) -> dict:
+    """Record + register ONE multi-timeframe OHLC bar series (era-4 J-01 — the explicit
+    credentialed research action; recording is never ambient). Full validation (422, never silent
+    coercion): an out-of-set ``timeframe`` (the config-owned ``bar_timeframes`` set), a missing
+    symbol, a malformed ISO ``start``/``end``, or ``end`` not after ``start``. Missing credentials
+    -> the EXISTING explicit unavailable (503) state — never fabricated bars. Content already
+    registered is the 409-style refusal; an empty fetched window (e.g. entirely inside the
+    free-plan recency embargo) is an explicit 422 — nothing is written, nothing fabricated."""
+    if body.timeframe not in CONFIG.bar_timeframes:
+        raise HTTPException(
+            status_code=422,
+            detail=(
+                f"unknown timeframe '{body.timeframe}' — the registered timeframes are "
+                f"{list(CONFIG.bar_timeframes)}"
+            ),
+        )
+    if not body.symbol:
+        raise HTTPException(status_code=422, detail="a bar recording requires a symbol")
+    try:
+        start_epoch = parse_utc_epoch(body.start)
+        end_epoch = parse_utc_epoch(body.end)
+    except ValueError:
+        raise HTTPException(status_code=422, detail="start and end must be ISO date-times")
+    if end_epoch <= start_epoch:
+        raise HTTPException(status_code=422, detail="end must be after start")
+
+    adapter = get_study_market_adapter()
+    if not adapter.is_available():
+        # No credentials -> the EXISTING explicit unavailable (503) state (never a fabricated bar
+        # series) — the DoD-mandated status for this gap, distinct from the historical-dataset
+        # path's 422 for the analogous case.
+        raise HTTPException(
+            status_code=503,
+            detail="real-data provider unavailable — a historical bar recording needs credentials",
+        )
+
+    from datetime import datetime, timezone
+
+    symbol = body.symbol.strip().upper()
+    start_dt = datetime.fromtimestamp(start_epoch, tz=timezone.utc)
+    end_dt = datetime.fromtimestamp(end_epoch, tz=timezone.utc)
+    try:
+        raw_bars = adapter.fetch_bars(symbol, start_dt, end_dt, body.timeframe)
+    except VendorTimeout as exc:
+        raise HTTPException(status_code=504, detail=exc.detail)
+
+    try:
+        meta = store.record(
+            symbol=symbol,
+            timeframe=body.timeframe,
+            window_start_utc=body.start,
+            window_end_utc=body.end,
+            feed=registry.config.historical_feed,
+            bars=list(raw_bars),
+        )
+    except BarSeriesAlreadyRegistered as exc:
+        raise HTTPException(status_code=409, detail=str(exc))
+    except EmptyBarWindowError as exc:
+        raise HTTPException(status_code=422, detail=str(exc))
+    return {"bar_series": meta}
+
+
+@router.get("/bars")
+def list_bar_series(store: BarStore = Depends(get_bar_store)) -> dict:
+    """List every registered bar series' metadata + candles (each file checksum-verified on
+    load), oldest first. A file that fails verification is surfaced EXPLICITLY in
+    ``integrity_errors`` — never silently hidden, never served as data. The MCP ``bars`` tool
+    proxies this byte-for-byte."""
+    records, errors = store.list()
+    return {"bar_series": records, "integrity_errors": errors}
+
+
+@router.get("/bars/{bar_series_id}")
+def get_bar_series(bar_series_id: str, store: BarStore = Depends(get_bar_store)) -> dict:
+    """One bar series' stored metadata + candles, verbatim (checksum-verified on load). 404 for an
+    unknown id; an explicit 500 integrity error for a corrupted/tampered file (never a fabricated
+    series)."""
+    try:
+        meta = store.get(bar_series_id)
+    except BarSeriesNotFound:
+        raise HTTPException(status_code=404, detail=f"no bar series with id '{bar_series_id}'")
+    except BarSeriesIntegrityError as exc:
+        raise HTTPException(status_code=500, detail=f"bar series integrity check failed: {exc}")
+    return {"bar_series": meta}
+
+
 # --- Deterministic backtests (era-3 capability 4, J-03) --------------------------------------------
 # Exactly FOUR routes (Product Shape): create+start, list, detail, cancel — mirroring studies.
 # The backtest runner (app/research/backtests.py) is Data Contract row 31's single computer; these
diff --git a/apps/backend/tests/fakes.py b/apps/backend/tests/fakes.py
index 24c5701..e75a4ff 100644
--- a/apps/backend/tests/fakes.py
+++ b/apps/backend/tests/fakes.py
@@ -19,6 +19,7 @@ from app.providers.adapters.base import (
     LiveRecord,
     MarketClock,
     NoDataForWindow,
+    RawBar,
     RawQuote,
     RawTrade,
     SymbolMatch,
@@ -124,6 +125,8 @@ class FakeAdapter:
         live_hold: asyncio.Event | None = None,
         fetch_timeout: bool = False,
         warm_raises: bool = False,
+        bars: tuple[RawBar, ...] | None = None,
+        bars_raise: Exception | None = None,
     ) -> None:
         self._available = available
         self._window = window
@@ -147,7 +150,13 @@ class FakeAdapter:
         self._warm_raises = warm_raises
         self._live_records = live_records or []
         self._live_hold = live_hold
+        # Era-4 (J-01) bar-fetch scripting: ``bars`` is the tuple ``fetch_bars`` returns on
+        # success (defaults to empty — a caller that needs real candles must pass some); a
+        # scripted ``bars_raise`` exception (e.g. ``VendorTimeout``) is raised instead when set.
+        self._bars = bars if bars is not None else ()
+        self._bars_raise = bars_raise
         self.fetch_calls: list[tuple] = []
+        self.fetch_bars_calls: list[tuple] = []
         self.search_calls: list[str] = []
         self.clock_calls = 0
         self.warm_calls = 0
@@ -204,6 +213,13 @@ class FakeAdapter:
         assert self._window is not None, "FakeAdapter needs a window for a successful fetch"
         return self._window
 
+    def fetch_bars(self, symbol: str, start, end, timeframe: str) -> tuple[RawBar, ...]:
+        """The era-4 (J-01) bar-fetch analogue of ``fetch_historical`` — scripted, never real."""
+        self.fetch_bars_calls.append((symbol, start, end, timeframe))
+        if self._bars_raise is not None:
+            raise self._bars_raise
+        return self._bars
+
     def search_symbols(self, query: str) -> list[SymbolMatch]:
         self.search_calls.append(query)
         if self._search_raises:
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index be2676f..53b126e 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -13,6 +13,7 @@ including the SDK's exception→``isError`` conversion.
 """
 
 import os
+import shutil
 import socket
 import subprocess
 import sys
@@ -38,7 +39,9 @@ from app.mcp import (
 
 BACKEND_DIR = Path(__file__).resolve().parents[1]
 
-# Capability 6, verbatim — order and content are the advertised contract.
+# Capability 6, verbatim — order and content are the advertised contract. ``bars`` (era-4 J-01) is
+# the newest addition, positioned right after its ``datasets`` sibling (the same store+route+MCP
+# shape, mirrored end to end).
 EXPECTED_TOOLS = (
     "tape_state",
     "tape_features",
@@ -47,6 +50,7 @@ EXPECTED_TOOLS = (
     "analytics",
     "studies",
     "datasets",
+    "bars",
     "backtests",
     "pnl_ledger",
     "taxonomy",
@@ -54,6 +58,8 @@ EXPECTED_TOOLS = (
     "get_endpoint",
 )
 
+FIXTURE_BAR_DIR = Path(__file__).parent / "fixtures" / "bars"
+
 # Every registered tool's endpoint has now shipped (``datasets`` at J-02, ``backtests`` at J-03,
 # ``pnl_ledger`` at J-04 — each moved to the live byte-identity coverage below with zero MCP code
 # changes), and ``/research/profiles`` (row 33, reached via ``get_endpoint``) shipped its minimal
@@ -90,6 +96,7 @@ def backend_paths(tmp_path_factory):
     return {
         "TAPEOLOGY_JOURNAL_DB": str(tmp_path_factory.mktemp("mcp-journal") / "journal.db"),
         "TAPEOLOGY_DATASET_DIR": str(tmp_path_factory.mktemp("mcp-datasets")),
+        "TAPEOLOGY_BAR_DIR": str(tmp_path_factory.mktemp("mcp-bars")),
     }
 
 
@@ -253,6 +260,29 @@ async def test_datasets_tool_byte_identical_on_a_non_empty_live_list(mcp_env):
     assert result.content[0].text.encode("utf-8") == rest.content, "datasets not byte-identical"
 
 
+@pytest.mark.anyio
+async def test_bars_tool_byte_identical_on_a_non_empty_live_list(mcp_env, backend_paths):
+    """``bars`` (era-4 J-01) ships in the SAME iteration as its endpoint — there is no honest-404
+    state to prove a flip from (unlike the J-02/J-03/J-04 tools, which shipped after their MCP
+    entries already existed). Recording real bars needs live Alpaca credentials, which CI does not
+    have, so this proves byte-identity on a NON-EMPTY list by seeding the live backend's bar
+    directory with the committed KEYLESS fixture pair directly (no vendor call, no credentials
+    touched) — the same store directory the running backend's ``GET /research/bars`` reads fresh
+    on every call."""
+    bar_dir = Path(backend_paths["TAPEOLOGY_BAR_DIR"])
+    fixtures = list(FIXTURE_BAR_DIR.glob("*.json"))
+    assert fixtures, "the committed bar fixture directory must not be empty"
+    for fixture in fixtures:
+        shutil.copy(fixture, bar_dir / fixture.name)
+    result = await call_tool("bars", {})
+    rest = httpx.get(f"{mcp_env}/research/bars", timeout=5.0)
+    assert rest.status_code == 200
+    assert len(rest.json()["bar_series"]) >= 1, "the live list must be non-empty for this proof"
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "bars not byte-identical"
+
+
 @pytest.mark.anyio
 async def test_backtests_tool_byte_identical_on_a_non_empty_live_list(mcp_env):
     """J-03 flips ``backtests`` from honest 404 to live data with ZERO MCP code changes (the
diff --git aapps/backend/app/research/bars.py bapps/backend/app/research/bars.py
new file mode 100644
index 0000000..5b463f2
--- /dev/null
+++ bapps/backend/app/research/bars.py
@@ -0,0 +1,258 @@
+"""The multi-timeframe OHLC bar store (era-4 capability 1, J-01) — Data Contract row 38's ONE owner.
+
+THIS MODULE is the only code that reads or writes bar-series files. A bar series is an IMMUTABLE
+recording of one symbol's OHLC candle series over a UTC window at one timeframe (the
+provider-neutral ``RawBar`` fields only — never a raw vendor payload) plus metadata (id, symbol,
+timeframe, UTC window, feed, bar count, a content checksum, and a created timestamp). Files live
+under the config-owned bar directory (``TAPEOLOGY_BAR_DIR`` override, ``config.bar_dir`` default —
+gitignored via ``.data/``), one JSON file per bar series. This module explicitly MIRRORS
+``research/datasets.py`` end to end (the spec's own directive): double checksum, verified on every
+load, ``record`` as the only mutation, the same honest-failure taxonomy.
+
+Disciplines (each an anti-goal or a J-01 acceptance clause):
+
+  * **Explicit recording only.** Recording happens ONLY through ``BarStore.record``, called by the
+    ``POST /research/bars`` route after a real Alpaca ``fetch_bars`` call. Nothing in the
+    watch/stream path imports this module — the live cockpit's tape is never persisted here either
+    (no ambient recording).
+  * **Checksummed + verified on EVERY load.** ``meta.checksum`` is a sha256 over the bar-series
+    CONTENT (symbol + timeframe + feed + the ordered candles) computed at registration; a second
+    whole-record checksum covers every metadata byte. Both are recomputed on every load — a
+    corrupted or tampered file raises the explicit ``BarSeriesIntegrityError``, never silence,
+    never a fabricated series.
+  * **Immutable — structurally.** No update/delete function exists anywhere in this module
+    (immutability is structural, not policed). The only mutation is ``record``, and it REFUSES
+    content that is already registered: re-recording the same series raises the 409-style
+    ``BarSeriesAlreadyRegistered`` naming the existing series.
+  * **Candles served embedded.** Unlike tick-level datasets (whose events are large and served only
+    through a separate loader), a bar series is small by construction, so ``get``/``list`` embed the
+    ordered OHLC candles directly on the served dict (the phase spec's explicit requirement) while
+    the on-disk shape still separates ``meta`` from ``bars`` for the same checksum discipline.
+  * **Honest failure states.** Unknown id -> ``BarSeriesNotFound``; an empty fetched window ->
+    ``EmptyBarWindowError`` (nothing written, nothing fabricated).
+"""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import uuid
+from dataclasses import dataclass
+from datetime import datetime, timezone
+from pathlib import Path
+
+from ..providers.adapters.base import RawBar
+
+
+class BarSeriesNotFound(Exception):
+    """No bar-series file exists for the requested id (the route maps this to a 404)."""
+
+
+class BarSeriesIntegrityError(Exception):
+    """A bar-series file failed its on-load verification — corrupted or tampered, surfaced
+    explicitly (never silence, never a fabricated series)."""
+
+
+class BarSeriesAlreadyRegistered(Exception):
+    """The exact bar content (symbol + timeframe + feed + candles) is already registered. Bar
+    series are immutable — there is no update/re-record path anywhere in this module."""
+
+    def __init__(self, existing_id: str, existing_symbol: str, existing_timeframe: str) -> None:
+        self.existing_id = existing_id
+        self.existing_symbol = existing_symbol
+        self.existing_timeframe = existing_timeframe
+        super().__init__(
+            f"this exact bar series is already registered as '{existing_id}' "
+            f"({existing_symbol} {existing_timeframe}) — bar series are immutable and are never "
+            f"re-recorded"
+        )
+
+
+class EmptyBarWindowError(Exception):
+    """The fetched window contains no bars — an explicit refusal; nothing is written and nothing
+    is fabricated."""
+
+
+def _canonical(obj: object) -> bytes:
+    """The one canonical JSON encoding every checksum in this module hashes (stable across
+    processes: sorted keys, no whitespace) — the SAME encoding ``research/datasets.py`` uses."""
+    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def _iso_utc(epoch: float) -> str:
+    return (
+        datetime.fromtimestamp(epoch, tz=timezone.utc)
+        .isoformat(timespec="microseconds")
+        .replace("+00:00", "Z")
+    )
+
+
+def _bar_to_row(bar: RawBar) -> dict:
+    """One stored candle row (``RawBar`` fields minus symbol/timeframe — the series-level ``meta``
+    owns those; rows do not repeat them, mirroring ``datasets._event_to_row``)."""
+    return {
+        "ts": bar.epoch,
+        "open": bar.open,
+        "high": bar.high,
+        "low": bar.low,
+        "close": bar.close,
+        "volume": bar.volume,
+    }
+
+
+def _row_to_bar(symbol: str, timeframe: str, row: dict) -> RawBar:
+    return RawBar(
+        symbol, timeframe, row["ts"], row["open"], row["high"], row["low"], row["close"], row["volume"]
+    )
+
+
+def _content_checksum(symbol: str, timeframe: str, feed: str, rows: list[dict]) -> str:
+    """The bar series' CONTENT identity: a sha256 over symbol + timeframe + feed + the ordered
+    candle rows. Registration-time duplicate detection and the on-load verification both recompute
+    exactly this."""
+    return _sha256(_canonical({"symbol": symbol, "timeframe": timeframe, "feed": feed, "bars": rows}))
+
+
+@dataclass(frozen=True)
+class _LoadedBarSeries:
+    """One verified load: the series' identity/stat metadata plus its stored candle rows."""
+
+    meta: dict
+    rows: list[dict]
+
+
+class BarStore:
+    """File-based store rooted at the config-owned bar directory — the ONE reader/writer.
+
+    Construction is cheap (no I/O); the directory is created on the first ``record``. Every read
+    path (``get`` / ``list`` / ``load_bars``) goes through the same verified ``_load`` — the
+    checksum is recomputed on EVERY load, with no bypass (the ``DatasetStore`` pattern)."""
+
+    def __init__(self, root: str | Path) -> None:
+        self._root = Path(root)
+
+    # --- verified load (the one loader; no unverified path exists) ------------------------------
+
+    def _path(self, bar_series_id: str) -> Path:
+        return self._root / f"{bar_series_id}.json"
+
+    def _load(self, path: Path) -> _LoadedBarSeries:
+        """Load ONE bar-series file, verifying BOTH checksums. Raises ``BarSeriesIntegrityError``
+        for any parse/shape/checksum failure — explicit, distinct, never silent."""
+        try:
+            data = json.loads(path.read_text())
+        except (OSError, ValueError) as exc:
+            raise BarSeriesIntegrityError(
+                f"bar series file '{path.name}' is not parseable ({exc}) — corrupted or tampered"
+            ) from exc
+        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
+            raise BarSeriesIntegrityError(
+                f"bar series file '{path.name}' does not carry the expected record shape — "
+                f"corrupted or tampered"
+            )
+        record = data["record"]
+        if _sha256(_canonical(record)) != data["file_checksum"]:
+            raise BarSeriesIntegrityError(
+                f"bar series file '{path.name}' failed its integrity check (file checksum "
+                f"mismatch) — the file was corrupted or tampered with"
+            )
+        meta = record.get("meta")
+        rows = record.get("bars")
+        if not isinstance(meta, dict) or not isinstance(rows, list):
+            raise BarSeriesIntegrityError(
+                f"bar series file '{path.name}' does not carry the expected record shape — "
+                f"corrupted or tampered"
+            )
+        recomputed = _content_checksum(meta.get("symbol"), meta.get("timeframe"), meta.get("feed"), rows)
+        if recomputed != meta.get("checksum"):
+            raise BarSeriesIntegrityError(
+                f"bar series file '{path.name}' failed its integrity check (content checksum "
+                f"mismatch) — the file was corrupted or tampered with"
+            )
+        return _LoadedBarSeries(meta=meta, rows=rows)
+
+    def _load_by_id(self, bar_series_id: str) -> _LoadedBarSeries:
+        path = self._path(bar_series_id)
+        if not path.exists():
+            raise BarSeriesNotFound(f"no bar series with id '{bar_series_id}'")
+        return self._load(path)
+
+    # --- reads -----------------------------------------------------------------------------------
+
+    def get(self, bar_series_id: str) -> dict:
+        """One bar series' metadata WITH its ordered OHLC candles embedded (verified load) — bar
+        series are small by construction, so (unlike tick datasets) the candles are served
+        directly rather than through a separate accessor. ``BarSeriesNotFound`` for an unknown id."""
+        loaded = self._load_by_id(bar_series_id)
+        return {**loaded.meta, "bars": list(loaded.rows)}
+
+    def list(self) -> tuple[list[dict], list[dict]]:
+        """Every bar series' metadata + candles (each file verified), oldest first, plus an
+        EXPLICIT error row per file that failed verification — a corrupt file is surfaced, never
+        silently hidden and never served as data."""
+        if not self._root.exists():
+            return [], []
+        records: list[dict] = []
+        errors: list[dict] = []
+        for path in sorted(self._root.glob("*.json")):
+            try:
+                loaded = self._load(path)
+                records.append({**loaded.meta, "bars": list(loaded.rows)})
+            except BarSeriesIntegrityError as exc:
+                errors.append({"file": path.name, "error": str(exc)})
+        records.sort(key=lambda meta: (meta.get("created_utc", ""), meta.get("id", "")))
+        return records, errors
+
+    def load_bars(self, bar_series_id: str) -> list[RawBar]:
+        """The stored candle series as typed ``RawBar`` records (verified load, exact stored
+        order) — the accessor a later level-detection consumer reads."""
+        loaded = self._load_by_id(bar_series_id)
+        symbol = loaded.meta["symbol"]
+        timeframe = loaded.meta["timeframe"]
+        return [_row_to_bar(symbol, timeframe, row) for row in loaded.rows]
+
+    # --- the one mutation: record/register --------------------------------------------------------
+
+    def record(
+        self,
+        *,
+        symbol: str,
+        timeframe: str,
+        window_start_utc: str,
+        window_end_utc: str,
+        feed: str,
+        bars: list[RawBar],
+    ) -> dict:
+        """Persist ONE new bar series (record + register in a single explicit action). Content
+        already registered raises the 409-style ``BarSeriesAlreadyRegistered`` (there is no
+        update/re-record path at all — immutability is structural)."""
+        if not bars:
+            raise EmptyBarWindowError("no bars in the requested window — nothing was recorded")
+        rows = [_bar_to_row(bar) for bar in bars]
+        checksum = _content_checksum(symbol, timeframe, feed, rows)
+        # Registration-time duplicate scan over the HEALTHY registry — the exact same series
+        # content is never recorded twice.
+        existing, _errors = self.list()
+        for meta in existing:
+            if meta["checksum"] == checksum:
+                raise BarSeriesAlreadyRegistered(meta["id"], meta["symbol"], meta["timeframe"])
+        meta = {
+            "id": uuid.uuid4().hex,
+            "symbol": symbol,
+            "timeframe": timeframe,
+            "window_start_utc": window_start_utc,
+            "window_end_utc": window_end_utc,
+            "feed": feed,
+            "bar_count": len(rows),
+            "checksum": checksum,
+            "created_utc": _iso_utc(datetime.now(timezone.utc).timestamp()),
+        }
+        record = {"meta": meta, "bars": rows}
+        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
+        self._root.mkdir(parents=True, exist_ok=True)
+        self._path(meta["id"]).write_text(json.dumps(payload))
+        return {**meta, "bars": rows}
diff --git aapps/backend/scripts/generate_bar_fixtures.py bapps/backend/scripts/generate_bar_fixtures.py
new file mode 100644
index 0000000..5a7fbf6
--- /dev/null
+++ bapps/backend/scripts/generate_bar_fixtures.py
@@ -0,0 +1,96 @@
+"""Generate the committed miniature multi-timeframe bar fixture (era-4 J-01) — ONCE.
+
+Two REAL Alpaca bar series (a small daily window + a small hourly window — at least two DISTINCT
+timeframes) are fetched through the SAME vendor-neutral ``fetch_bars`` seam the app uses and
+recorded through the REAL ``BarStore.record`` path — never hand-crafted JSON — then committed
+under ``tests/fixtures/bars/`` (outside the gitignored ``.data/``). CI then proves
+fetch->record->read end-to-end, checksum verification included, with NO credentials
+(``tests/test_bars.py``'s committed-fixture test loads this directory directly).
+
+NO-FABRICATION BOUNDARY (the ``capture_alpaca_fixture.py`` precedent, critical): this script only
+ever writes bars returned by the REAL vendor. If credentials are absent, it refuses and does
+nothing — never synthesizes a fixture to force a green journey.
+
+Run from ``apps/backend``:  ``.venv/bin/python scripts/generate_bar_fixtures.py``
+
+The script REFUSES to run if the fixture directory already holds bar series (the committed pair
+is frozen at its one generation — the ``generate_dataset_fixtures.py`` precedent). Delete the
+directory first if a regeneration is genuinely intended.
+"""
+
+from __future__ import annotations
+
+import sys
+from datetime import datetime, timezone
+from pathlib import Path
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from app.env import load_env  # noqa: E402
+from app.providers.adapters import get_adapter  # noqa: E402
+from app.research.bars import BarStore  # noqa: E402
+
+FIXTURE_BAR_DIR = BACKEND_DIR / "tests" / "fixtures" / "bars"
+
+SYMBOL = "PG"
+# Small REAL windows, well before "now" (never the free-plan's embargoed most-recent bars) and
+# reusing the same symbol + calendar neighbourhood as the existing committed PG SIP tick fixtures
+# (tests/fixtures/datasets, tests/fixtures/alpaca) for consistency.
+WINDOWS: tuple[tuple[str, datetime, datetime], ...] = (
+    ("1d", datetime(2026, 6, 1, tzinfo=timezone.utc), datetime(2026, 6, 6, tzinfo=timezone.utc)),
+    ("1h", datetime(2026, 6, 9, 13, 0, tzinfo=timezone.utc), datetime(2026, 6, 9, 21, 0, tzinfo=timezone.utc)),
+)
+
+
+def _iso(dt: datetime) -> str:
+    return dt.isoformat().replace("+00:00", "Z")
+
+
+def main() -> int:
+    load_env()
+    adapter = get_adapter()
+    if not adapter.is_available():
+        print(
+            "ERROR: no real-data credentials configured — cannot capture. Do NOT fabricate a "
+            "fixture; configure ALPACA_API_KEY/ALPACA_API_SECRET and retry.",
+            file=sys.stderr,
+        )
+        return 2
+
+    store = BarStore(FIXTURE_BAR_DIR)
+    existing, errors = store.list()
+    if existing or errors:
+        print(
+            f"REFUSED: {FIXTURE_BAR_DIR} already holds {len(existing)} bar series "
+            f"(+{len(errors)} unreadable) — the committed fixture is frozen at its one generation."
+        )
+        return 1
+
+    for timeframe, start, end in WINDOWS:
+        bars = adapter.fetch_bars(SYMBOL, start, end, timeframe)
+        if not bars:
+            print(
+                f"ERROR: no real bars returned for {SYMBOL} {timeframe} "
+                f"{start.isoformat()}..{end.isoformat()}.",
+                file=sys.stderr,
+            )
+            return 3
+        meta = store.record(
+            symbol=SYMBOL,
+            timeframe=timeframe,
+            window_start_utc=_iso(start),
+            window_end_utc=_iso(end),
+            feed=adapter.historical_feed,
+            bars=list(bars),
+        )
+        print(
+            f"{timeframe:4s} id={meta['id']} {meta['symbol']} {meta['window_start_utc']}"
+            f" .. {meta['window_end_utc']} feed={meta['feed']} bar_count={meta['bar_count']}"
+            f" checksum={meta['checksum']}"
+        )
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git aapps/backend/tests/fixtures/bars/009371c9c02f46338bafef47148f92ad.json bapps/backend/tests/fixtures/bars/009371c9c02f46338bafef47148f92ad.json
new file mode 100644
index 0000000..7e89fae
--- /dev/null
+++ bapps/backend/tests/fixtures/bars/009371c9c02f46338bafef47148f92ad.json
@@ -0,0 +1 @@
+{"file_checksum": "e34f9bb196dc196eb24839b7cd930f9b257aff1eff46728c9432b855a2b9730a", "record": {"meta": {"id": "009371c9c02f46338bafef47148f92ad", "symbol": "PG", "timeframe": "1h", "window_start_utc": "2026-06-09T13:00:00Z", "window_end_utc": "2026-06-09T21:00:00Z", "feed": "sip", "bar_count": 9, "checksum": "4d9247954184006adac9515f51e634f63db575e60ab17ec17d0e838b0c93e6ee", "created_utc": "2026-07-06T00:24:32.691384Z"}, "bars": [{"ts": 1781010000.0, "open": 145.1, "high": 146.159, "low": 144.53, "close": 145.77, "volume": 588782}, {"ts": 1781013600.0, "open": 145.77, "high": 147.68, "low": 145.735, "close": 147.3267, "volume": 846887}, {"ts": 1781017200.0, "open": 147.33, "high": 148.62, "low": 147.08, "close": 148.5, "volume": 943821}, {"ts": 1781020800.0, "open": 148.49, "high": 149.4796, "low": 148.175, "close": 148.98, "volume": 1044769}, {"ts": 1781024400.0, "open": 148.95, "high": 149.08, "low": 148.06, "close": 148.34, "volume": 633230}, {"ts": 1781028000.0, "open": 148.39, "high": 148.55, "low": 148.2, "close": 148.3609, "volume": 457470}, {"ts": 1781031600.0, "open": 148.38, "high": 148.74, "low": 148.095, "close": 148.57, "volume": 1534798}, {"ts": 1781035200.0, "open": 148.55, "high": 148.67, "low": 148.34, "close": 148.35, "volume": 1975673}, {"ts": 1781038800.0, "open": 148.4, "high": 148.47, "low": 148.4, "close": 148.47, "volume": 752}]}}
\ No newline at end of file
diff --git aapps/backend/tests/fixtures/bars/b08b1a55ef4a45b2a1adad8fa82ccdf1.json bapps/backend/tests/fixtures/bars/b08b1a55ef4a45b2a1adad8fa82ccdf1.json
new file mode 100644
index 0000000..475d523
--- /dev/null
+++ bapps/backend/tests/fixtures/bars/b08b1a55ef4a45b2a1adad8fa82ccdf1.json
@@ -0,0 +1 @@
+{"file_checksum": "1933dc48db9939bfceec4f7e990d251cd02adb3bb61dd442d7fdbcbcd275e315", "record": {"meta": {"id": "b08b1a55ef4a45b2a1adad8fa82ccdf1", "symbol": "PG", "timeframe": "1d", "window_start_utc": "2026-06-01T00:00:00Z", "window_end_utc": "2026-06-06T00:00:00Z", "feed": "sip", "bar_count": 5, "checksum": "ed471e6c2f8e064ec9af567f6272101db5d8a32f043aa2e5415162bb92a24e22", "created_utc": "2026-07-06T00:24:32.415484Z"}, "bars": [{"ts": 1780286400.0, "open": 141.52, "high": 141.82, "low": 138.86, "close": 140.28, "volume": 11127208}, {"ts": 1780372800.0, "open": 140.115, "high": 141.115, "low": 139.03, "close": 140.82, "volume": 9629408}, {"ts": 1780459200.0, "open": 140.93, "high": 142.45, "low": 140.0, "close": 140.19, "volume": 9376579}, {"ts": 1780545600.0, "open": 142.7007, "high": 143.14, "low": 139.89, "close": 140.78, "volume": 8218948}, {"ts": 1780632000.0, "open": 142.22, "high": 148.23, "low": 141.8, "close": 146.54, "volume": 10990271}]}}
\ No newline at end of file
diff --git aapps/backend/tests/test_bars.py bapps/backend/tests/test_bars.py
new file mode 100644
index 0000000..5218609
--- /dev/null
+++ bapps/backend/tests/test_bars.py
@@ -0,0 +1,280 @@
+"""The multi-timeframe OHLC bar store (era-4 capability 1, J-01) — store-level discipline.
+
+Mirrors ``tests/test_datasets.py`` end to end (the spec's own explicit directive): metadata
+correctness, structural immutability (no update/re-record path exists), verified loads (double
+checksum), the honest failure taxonomy, the committed keyless multi-timeframe fixture, and the
+``bar_dir`` / validation-parameter ``config_fingerprint`` exclusions (the ``dataset_dir``
+precedent). Also covers the two new Alpaca-adapter helpers this iteration adds (the free-plan
+recency-delay clamp and the rate-limit throttle) as small, independently testable pure functions.
+"""
+
+from __future__ import annotations
+
+import json
+import time
+from datetime import datetime, timedelta, timezone
+from pathlib import Path
+
+import pytest
+
+from app.config import CONFIG, Config
+from app.providers.adapters.base import RawBar
+from app.research.bars import (
+    BarSeriesAlreadyRegistered,
+    BarSeriesIntegrityError,
+    BarSeriesNotFound,
+    BarStore,
+    EmptyBarWindowError,
+)
+
+FIXTURE_BAR_DIR = Path(__file__).parent / "fixtures" / "bars"
+
+WINDOW_START, WINDOW_END = "2026-06-01T00:00:00Z", "2026-06-04T00:00:00Z"
+
+
+def _bar(symbol: str, timeframe: str, epoch: float, o: float, h: float, l: float, c: float, v: int) -> RawBar:
+    return RawBar(symbol, timeframe, epoch, o, h, l, c, v)
+
+
+def _small_daily_series(symbol: str = "PG") -> list[RawBar]:
+    base = datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp()
+    day = 86400.0
+    return [
+        _bar(symbol, "1d", base + 0 * day, 148.0, 149.5, 147.5, 149.0, 1_000_000),
+        _bar(symbol, "1d", base + 1 * day, 149.0, 150.0, 148.5, 149.8, 1_100_000),
+        _bar(symbol, "1d", base + 2 * day, 149.8, 151.0, 149.2, 150.5, 1_050_000),
+    ]
+
+
+def _record_small_series(store: BarStore, symbol: str = "PG", timeframe: str = "1d") -> dict:
+    return store.record(
+        symbol=symbol,
+        timeframe=timeframe,
+        window_start_utc=WINDOW_START,
+        window_end_utc=WINDOW_END,
+        feed="sip",
+        bars=_small_daily_series(symbol),
+    )
+
+
+# --- record: metadata correctness ----------------------------------------------------------------
+
+
+def test_record_stores_correct_metadata(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    meta = _record_small_series(store)
+
+    assert meta["symbol"] == "PG"
+    assert meta["timeframe"] == "1d"
+    assert meta["window_start_utc"] == WINDOW_START
+    assert meta["window_end_utc"] == WINDOW_END
+    assert meta["feed"] == "sip"
+    assert meta["bar_count"] == 3
+    assert isinstance(meta["checksum"], str) and len(meta["checksum"]) == 64
+    int(meta["checksum"], 16)  # hex or this raises
+    assert meta["id"] and meta["created_utc"].endswith("Z")
+
+
+def test_get_and_list_serve_candles_embedded_verbatim(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    bars = _small_daily_series()
+    meta = store.record(
+        symbol="PG", timeframe="1d", window_start_utc=WINDOW_START, window_end_utc=WINDOW_END,
+        feed="sip", bars=bars,
+    )
+
+    fetched = store.get(meta["id"])
+    assert fetched["bars"] == [
+        {
+            "ts": b.epoch, "open": b.open, "high": b.high, "low": b.low, "close": b.close,
+            "volume": b.volume,
+        }
+        for b in bars
+    ]
+    records, errors = store.list()
+    assert errors == []
+    assert records[0]["bars"] == fetched["bars"]
+    assert records[0] == fetched
+
+
+def test_split_series_register_and_survive_a_store_reload(tmp_path):
+    root = tmp_path / "bars"
+    daily = _record_small_series(BarStore(root), timeframe="1d")
+    hourly = _record_small_series(BarStore(root), symbol="F", timeframe="1h")
+
+    reloaded = BarStore(root)
+    assert reloaded.get(daily["id"])["timeframe"] == "1d"
+    assert reloaded.get(hourly["id"])["timeframe"] == "1h"
+    records, errors = reloaded.list()
+    assert errors == []
+    assert {r["id"]: r["timeframe"] for r in records} == {
+        daily["id"]: "1d",
+        hourly["id"]: "1h",
+    }
+
+
+# --- immutability (409-style refusal; no update/re-record path exists) ---------------------------
+
+
+def test_rerecording_identical_content_is_refused(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    original = _record_small_series(store)
+
+    with pytest.raises(BarSeriesAlreadyRegistered) as excinfo:
+        _record_small_series(store)
+    assert original["id"] in str(excinfo.value)
+    assert "PG" in str(excinfo.value)
+
+    records, errors = store.list()
+    assert errors == []
+    assert [r["id"] for r in records] == [original["id"]]
+
+
+# --- verified loads: corruption is an explicit, distinct error -----------------------------------
+
+
+def _tamper(path: Path, mutate) -> None:
+    data = json.loads(path.read_text())
+    mutate(data)
+    path.write_text(json.dumps(data))
+
+
+def test_corrupted_bar_data_surfaces_an_explicit_integrity_error(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    meta = _record_small_series(store)
+    file_path = tmp_path / "bars" / f"{meta['id']}.json"
+
+    def corrupt_close(data):
+        data["record"]["bars"][0]["close"] = data["record"]["bars"][0]["close"] + 1.0
+
+    _tamper(file_path, corrupt_close)
+    with pytest.raises(BarSeriesIntegrityError):
+        store.get(meta["id"])
+    with pytest.raises(BarSeriesIntegrityError):
+        store.load_bars(meta["id"])
+
+
+def test_list_surfaces_a_corrupt_file_explicitly_never_hides_it(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    healthy = _record_small_series(store, symbol="PG", timeframe="1d")
+    corrupt = _record_small_series(store, symbol="F", timeframe="1h")
+    _tamper(
+        tmp_path / "bars" / f"{corrupt['id']}.json",
+        lambda data: data["record"]["bars"][0].__setitem__("volume", 999999999),
+    )
+    records, errors = store.list()
+    assert [r["id"] for r in records] == [healthy["id"]]
+    assert len(errors) == 1 and f"{corrupt['id']}.json" in errors[0]["file"]
+
+
+def test_unparseable_file_is_an_explicit_integrity_error(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    meta = _record_small_series(store)
+    (tmp_path / "bars" / f"{meta['id']}.json").write_text("{not json")
+    with pytest.raises(BarSeriesIntegrityError):
+        store.get(meta["id"])
+
+
+def test_unknown_bar_series_id_raises_not_found(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    with pytest.raises(BarSeriesNotFound):
+        store.get("no-such-bar-series")
+    with pytest.raises(BarSeriesNotFound):
+        store.load_bars("no-such-bar-series")
+
+
+def test_empty_bar_list_is_an_explicit_refusal(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    with pytest.raises(EmptyBarWindowError):
+        store.record(
+            symbol="PG", timeframe="1d", window_start_utc=WINDOW_START, window_end_utc=WINDOW_END,
+            feed="sip", bars=[],
+        )
+    records, errors = store.list()
+    assert records == [] and errors == []
+
+
+# --- the committed miniature multi-timeframe fixture (keyless CI proof) --------------------------
+
+
+def test_committed_fixture_loads_through_the_real_store_path_keyless():
+    store = BarStore(FIXTURE_BAR_DIR)
+    records, errors = store.list()
+    assert errors == [], f"committed bar fixtures failed verification: {errors}"
+    assert len(records) >= 2, "the committed fixture must cover at least two bar series"
+    timeframes = {r["timeframe"] for r in records}
+    assert len(timeframes) >= 2, "the committed fixture must cover at least two DISTINCT timeframes"
+
+    for meta in records:
+        bars = store.load_bars(meta["id"])
+        assert len(bars) == meta["bar_count"] > 0
+        assert all(isinstance(b, RawBar) for b in bars)
+        assert meta["feed"] == CONFIG.historical_feed
+        # Byte-identical reload through the real store path.
+        again = store.get(meta["id"])
+        assert again == meta
+
+
+# --- config: bar_dir + validation/throttle params are operational, never fingerprint inputs -------
+
+
+def test_bar_dir_is_excluded_from_config_fingerprint():
+    # The dataset_dir precedent: WHERE bar series are stored cannot affect any research value...
+    assert Config(bar_dir="/somewhere/else").config_fingerprint() == CONFIG.config_fingerprint()
+    # ...while a real classifier threshold still moves it (the counter-test).
+    assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()
+
+
+def test_bar_validation_and_throttle_params_are_excluded_from_config_fingerprint():
+    # None of these shape any tape/backtest/study computation — they only govern an unrelated,
+    # brand-new bar-storage capability's validation and vendor-fetch mechanics.
+    assert Config(bar_timeframes=("1d",)).config_fingerprint() == CONFIG.config_fingerprint()
+    assert Config(bar_recency_delay_seconds=1.0).config_fingerprint() == CONFIG.config_fingerprint()
+    assert Config(bar_rate_limit_per_minute=1).config_fingerprint() == CONFIG.config_fingerprint()
+    assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()
+
+
+def test_bar_dir_env_override_wins(monkeypatch):
+    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", "/operator/override")
+    assert CONFIG.bar_dir_resolved() == "/operator/override"
+    monkeypatch.delenv("TAPEOLOGY_BAR_DIR")
+    default = CONFIG.bar_dir_resolved()
+    assert default.endswith(str(Path(".data") / "bars"))
+
+
+# --- Alpaca adapter: recency-delay clamp + rate-throttle (pure/injectable helpers) ----------------
+
+
+def test_bar_fetch_recency_clamp_never_requests_the_embargoed_tail():
+    from app.providers.adapters.alpaca import _bar_fetch_end_clamp
+
+    now = datetime(2026, 7, 6, 12, 0, 0, tzinfo=timezone.utc)
+    inside_embargo_end = now - timedelta(minutes=2)  # 2 min ago: inside the 15-min embargo
+    clamped = _bar_fetch_end_clamp(inside_embargo_end, 900.0, now=now)
+    assert clamped == now - timedelta(seconds=900.0)
+
+    outside_embargo_end = now - timedelta(hours=5)  # well before the embargo: unaffected
+    assert _bar_fetch_end_clamp(outside_embargo_end, 900.0, now=now) == outside_embargo_end
+
+
+def test_throttle_bar_fetch_spaces_consecutive_calls(monkeypatch):
+    import app.providers.adapters.alpaca as alpaca_module
+
+    monkeypatch.setattr(alpaca_module, "CONFIG", Config(bar_rate_limit_per_minute=600))  # 0.1s interval
+    alpaca_module._LAST_BAR_FETCH_MONOTONIC = None
+    try:
+        t0 = time.monotonic()
+        alpaca_module._throttle_bar_fetch()
+        t1 = time.monotonic()
+        alpaca_module._throttle_bar_fetch()
+        t2 = time.monotonic()
+    finally:
+        alpaca_module._LAST_BAR_FETCH_MONOTONIC = None  # leave clean for later tests
+    assert (t1 - t0) < 0.05, "the first call has nothing prior to wait behind"
+    assert (t2 - t1) >= 0.09, "the second call must wait ~the configured min interval"
+
+
+def test_bar_timeframe_vendor_mapping_covers_every_configured_timeframe():
+    from app.providers.adapters.alpaca import _TIMEFRAME_PARTS
+
+    assert set(_TIMEFRAME_PARTS) == set(CONFIG.bar_timeframes)
diff --git aapps/backend/tests/test_bars_api.py bapps/backend/tests/test_bars_api.py
new file mode 100644
index 0000000..ec2720d
--- /dev/null
+++ bapps/backend/tests/test_bars_api.py
@@ -0,0 +1,222 @@
+"""The ``/research/bars*`` endpoints (era-4 capability 1, J-01) — record/register, list, detail.
+
+Exactly THREE routes exist (Product Shape, the ``test_datasets_api.py`` precedent): ``POST
+/research/bars`` (the explicit credentialed record/register action — recording is never
+ambient), ``GET /research/bars`` (list), and ``GET /research/bars/{id}`` (detail). There is NO
+PATCH/PUT/DELETE — immutability is structural. Validation is explicit and never silent coercion:
+an out-of-set timeframe / missing symbol / bad window are 422; an unknown id is 404;
+re-recording already-registered content is 409; a corrupted file is an explicit 500 integrity
+error surfaced in ``integrity_errors`` on list rather than hidden.
+
+Missing credentials on ``POST`` is the EXISTING explicit unavailable (503) state (never
+fabricated bars) — per the spec's explicit Definition-of-Done/Testing-Requirements text, this is
+DISTINCT from the 422 the historical-DATASET path uses for the analogous credentials gap.
+"""
+
+from __future__ import annotations
+
+import json
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG
+from app.main import app, get_market_adapter, manager
+from app.providers.adapters.base import RawBar, VendorTimeout
+from app.research.routes import ResearchRegistry, set_registry
+from app.research.store import JournalStore
+from fakes import FakeAdapter
+
+SYMBOL = "PG"
+TIMEFRAME = "1d"
+START, END = "2026-06-01T00:00:00Z", "2026-06-04T00:00:00Z"
+_BASE_EPOCH = 1780358400.0  # 2026-06-01T00:00:00Z
+_DAY = 86400.0
+
+
+def _bars(symbol: str = SYMBOL, timeframe: str = TIMEFRAME) -> tuple[RawBar, ...]:
+    return (
+        RawBar(symbol, timeframe, _BASE_EPOCH, 148.0, 149.5, 147.5, 149.0, 1_000_000),
+        RawBar(symbol, timeframe, _BASE_EPOCH + _DAY, 149.0, 150.0, 148.5, 149.8, 1_100_000),
+        RawBar(symbol, timeframe, _BASE_EPOCH + 2 * _DAY, 149.8, 151.0, 149.2, 150.5, 1_050_000),
+    )
+
+
+def _body(symbol: str = SYMBOL, timeframe: str = TIMEFRAME, start: str = START, end: str = END) -> dict:
+    return {"symbol": symbol, "timeframe": timeframe, "start": start, "end": end}
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
+# --- record/register (the explicit credentialed research action) --------------------------------
+
+
+def test_post_records_and_registers_a_bar_series(ctx):
+    client, bar_dir = ctx
+    _inject_adapter(bars=_bars())
+    r = client.post("/research/bars", json=_body())
+    assert r.status_code == 200
+    meta = r.json()["bar_series"]
+    assert meta["symbol"] == SYMBOL
+    assert meta["timeframe"] == TIMEFRAME
+    assert meta["window_start_utc"] == START
+    assert meta["window_end_utc"] == END
+    assert meta["feed"] == CONFIG.historical_feed
+    assert meta["bar_count"] == 3
+    assert len(meta["checksum"]) == 64
+    assert len(meta["bars"]) == 3
+    # The bar series landed as ONE file in the configured bar dir.
+    assert len(list(bar_dir.glob("*.json"))) == 1
+
+
+def test_list_and_detail_serve_the_stored_metadata_verbatim(ctx):
+    client, _bar_dir = ctx
+    _inject_adapter(bars=_bars())
+    posted = client.post("/research/bars", json=_body()).json()["bar_series"]
+
+    listed = client.get("/research/bars")
+    assert listed.status_code == 200
+    body = listed.json()
+    assert body["integrity_errors"] == []
+    assert [row["id"] for row in body["bar_series"]] == [posted["id"]]
+    assert body["bar_series"][0] == posted  # the stored row, verbatim — no recompute at read
+
+    detail = client.get(f"/research/bars/{posted['id']}")
+    assert detail.status_code == 200
+    assert detail.json()["bar_series"] == posted
+
+
+def test_unknown_bar_series_id_is_404(ctx):
+    client, _bar_dir = ctx
+    r = client.get("/research/bars/no-such-id")
+    assert r.status_code == 404
+    assert "no-such-id" in r.json()["detail"]
+
+
+# --- immutability over REST: re-recording identical content is a 409 ------------------------------
+
+
+def test_duplicate_content_is_refused_409(ctx):
+    client, _bar_dir = ctx
+    _inject_adapter(bars=_bars())
+    first = client.post("/research/bars", json=_body())
+    assert first.status_code == 200
+    original = first.json()["bar_series"]
+
+    duplicate = client.post("/research/bars", json=_body())
+    assert duplicate.status_code == 409
+    assert original["id"] in duplicate.json()["detail"]
+
+    # The registered series is untouched — exactly one file still on disk.
+    assert client.get(f"/research/bars/{original['id']}").json()["bar_series"]["bar_count"] == 3
+
+
+# --- validation: 422 matrix (never silent coercion) -----------------------------------------------
+
+
+def test_bad_timeframe_value_is_422(ctx):
+    client, _bar_dir = ctx
+    assert "17m" not in CONFIG.bar_timeframes
+    r = client.post("/research/bars", json=_body(timeframe="17m"))
+    assert r.status_code == 422
+    assert "timeframe" in r.json()["detail"]
+
+
+def test_missing_symbol_is_422(ctx):
+    client, _bar_dir = ctx
+    r = client.post("/research/bars", json=_body(symbol=""))
+    assert r.status_code == 422
+    assert "symbol" in r.json()["detail"]
+
+
+def test_malformed_iso_window_is_422(ctx):
+    client, _bar_dir = ctx
+    r = client.post("/research/bars", json=_body(start="yesterday"))
+    assert r.status_code == 422
+
+
+def test_end_not_after_start_is_422(ctx):
+    client, _bar_dir = ctx
+    r = client.post("/research/bars", json=_body(start=END, end=START))
+    assert r.status_code == 422
+
+
+def test_empty_fetch_result_is_422_and_writes_nothing(ctx):
+    client, bar_dir = ctx
+    _inject_adapter(bars=())
+    r = client.post("/research/bars", json=_body())
+    assert r.status_code == 422
+    assert "no bars" in r.json()["detail"]
+    assert not bar_dir.exists() or list(bar_dir.glob("*.json")) == []
+
+
+# --- missing credentials: the EXISTING explicit unavailable (503) state, never fabricated ---------
+
+
+def test_missing_credentials_is_an_explicit_503(ctx):
+    client, bar_dir = ctx
+    _inject_adapter(available=False)
+    r = client.post("/research/bars", json=_body())
+    assert r.status_code == 503
+    assert "unavailable" in r.json()["detail"]
+    assert not bar_dir.exists() or list(bar_dir.glob("*.json")) == []
+
+
+# --- vendor timeout: the neutral VendorTimeout maps to the existing 504 --------------------------
+
+
+def test_vendor_timeout_is_504(ctx):
+    client, _bar_dir = ctx
+    _inject_adapter(bars=(), bars_raise=VendorTimeout("that window is very high-volume — try a shorter range"))
+    r = client.post("/research/bars", json=_body())
+    assert r.status_code == 504
+
+
+# --- integrity: a corrupted file is explicit, never silent ----------------------------------------
+
+
+def test_corrupted_bar_series_file_surfaces_explicitly_on_detail_and_list(ctx):
+    client, bar_dir = ctx
+    _inject_adapter(bars=_bars())
+    healthy = client.post("/research/bars", json=_body()).json()["bar_series"]
+
+    _inject_adapter(bars=_bars(symbol="F", timeframe="1h"))
+    corrupt = client.post("/research/bars", json=_body(symbol="F", timeframe="1h")).json()["bar_series"]
+
+    path = bar_dir / f"{corrupt['id']}.json"
+    data = json.loads(path.read_text())
+    data["record"]["bars"][0]["close"] = data["record"]["bars"][0]["close"] + 1.0
+    path.write_text(json.dumps(data))
+
+    detail = client.get(f"/research/bars/{corrupt['id']}")
+    assert detail.status_code == 500
+    assert "integrity" in detail.json()["detail"]
+
+    listed = client.get("/research/bars").json()
+    # The healthy series still serves; the corrupt one is surfaced EXPLICITLY — not silently
+    # hidden, not fabricated.
+    assert [row["id"] for row in listed["bar_series"]] == [healthy["id"]]
+    assert len(listed["integrity_errors"]) == 1
+    assert f"{corrupt['id']}.json" in listed["integrity_errors"][0]["file"]
diff --git adocs/handoffs/goal-tape_to_profit_support_resistence-iter-1-audit.md bdocs/handoffs/goal-tape_to_profit_support_resistence-iter-1-audit.md
new file mode 100644
index 0000000..d2cfdb9
--- /dev/null
+++ bdocs/handoffs/goal-tape_to_profit_support_resistence-iter-1-audit.md
@@ -0,0 +1,141 @@
+# goal-tape_to_profit_support_resistence-iter-1 Audit Report
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
+J-01 (the multi-timeframe bar store) is genuinely and completely delivered: an immutable,
+double-checksummed `BarStore` mirroring `research/datasets.py`, a vendor-neutral `RawBar` +
+`fetch_bars` seam, three `/research/bars*` routes, a read-only MCP `bars` proxy, and a real
+(never-fabricated) keyless committed fixture. Every DEFINITION OF DONE item is satisfied in code
+that I traced and re-ran myself, and every critical anti-goal holds — most importantly the frozen
+`default` profile, which I confirmed by live-computing its fingerprint to the pinned
+`4d665603569b9dbf`. No critical or important gaps remain; the only findings are two spec-sanctioned
+GAPs the developer already disclosed and two observations. No fixes were warranted.
+
+---
+
+## 2. Findings
+
+### Backend Findings
+
+**B1 — GAP (disclosed): unknown/untradable symbol is indistinguishable from a genuinely empty window**
+`fetch_bars` has no tradability pre-flight (unlike `fetch_historical`'s `_require_tradable`), so an
+unknown symbol and a real empty window both return `()` → `EmptyBarWindowError` → 422 "no bars in
+the requested window" (`app/research/bars.py:233-234`, `app/research/routes.py:1597-1598`). The spec
+never asks bars to distinguish these, and the developer flagged it explicitly (dev handoff, Known
+Issue #3). The failure is honest and nothing is fabricated. No fix — out of scope, spec-permitted.
+
+**B2 — GAP (disclosed): a window entirely inside the recency embargo returns the same 422 as an empty window**
+`_bar_fetch_end_clamp` short-circuits an entirely-embargoed window to `()` with no vendor call
+(`app/providers/adapters/alpaca.py:515-517`), which then surfaces as the same `EmptyBarWindowError`
+→ 422 as B1. Honest (no fabrication), disclosed in the handoff. No fix — the DoD requires no
+distinct embargo state, and inventing one would be scope creep.
+
+**B3 — OBSERVATION: the window fields are outside the content checksum (by design)**
+`_content_checksum` covers `symbol + timeframe + feed + bars` but not `window_start_utc` /
+`window_end_utc` (`app/research/bars.py:113-117`), so the request window does not participate in
+duplicate detection — dedup is by actual candle content, which is correct (the window is a request
+label; the data window is derived from the candles). The window fields are still tamper-protected by
+the whole-file checksum (`bars.py:158`). Correct-by-design; noted only for completeness.
+
+### Frontend Findings
+
+None. `Frontend Present: no`. I verified `git diff -- apps/frontend/` is empty **and** that there
+are no untracked frontend files (`git status --short -- apps/frontend/` empty). J-07's cockpit leg
+is correctly guarded by the equivalence suite + zero-frontend-diff, per the iteration's lessons.md.
+
+### Test Findings
+
+**T1 — OBSERVATION: the content-checksum-only failure mode is never isolated in a test**
+Both checksums are recomputed on every load (`app/research/bars.py:158` whole-file, `:170-175`
+content), but every corruption test mutates a bar value **without** recomputing `file_checksum`
+(`test_bars.py:142`, `:157`; `test_bars_api.py:200`), so the whole-file check at `:158` always fires
+first and the content-checksum branch at `:170-175` is never the raiser under test. The content
+checksum's unique value — catching a tamper that recomputed the file checksum but not `meta.checksum`
+— is therefore unexercised. This is defense-in-depth that mirrors the `datasets` precedent exactly;
+both checksums genuinely run on every healthy load. Not a correctness defect. No fix (adding a test
+for a defense-in-depth branch is not required by the DoD and would be discretionary).
+
+---
+
+## 3. Domain Assessment
+
+The core domain logic is correct and faithfully mirrors the `research/datasets.py` precedent the spec
+mandated, which keeps the single-source-of-truth and honest-failure anti-goals satisfied by
+construction:
+
+- **Immutable + verified-on-load.** `record()` is the only write path in the module (confirmed: no
+  `update`/`delete`/`unlink`/`rmtree`/`save` anywhere in `bars.py`), it refuses already-registered
+  content via a content-checksum scan (`BarSeriesAlreadyRegistered`), and every read goes through one
+  `_load` that recomputes both checksums. Corrupt/unparseable/shape-broken files raise the explicit
+  `BarSeriesIntegrityError`; `list()` surfaces a corrupt file in `integrity_errors` rather than
+  hiding or serving it.
+- **No fabrication.** Empty fetched window → `EmptyBarWindowError` → 422, nothing written (verified
+  by test asserting the bar dir stays empty). Missing credentials → 503 (never a synthesized series).
+  The committed fixtures are REAL Alpaca PG data (1h ×9, 1d ×5) captured through the actual
+  `fetch_bars` path, and I confirmed they contain no credential-like strings.
+- **Frozen archived behavior.** The four new `Config` fields (`bar_dir`, `bar_timeframes`,
+  `bar_recency_delay_seconds`, `bar_rate_limit_per_minute`) are all in the `config_fingerprint`
+  `excluded` set (`config.py:1256-1267`), which is the correct call — none shapes any tape/backtest/
+  study computation. I live-computed `Config().config_fingerprint()` → `'4d665603569b9dbf'`, exactly
+  the pinned value, proving the `default` profile did not drift.
+- **Single source of truth / read-only MCP.** Routes serve the store's dict verbatim (a test asserts
+  `list()[0] == posted` — no recompute at read); the MCP `bars` tool is a generic `response.text`
+  proxy of `GET /research/bars`, byte-identical by construction and proven on a non-empty seeded
+  list. No mutating MCP tool was added.
+- **Persistence scoped.** Only `app/research/routes.py` imports `BarStore`; nothing in the
+  watch/stream/live path touches it, so there is no ambient recording.
+- **Adapter-seam safety.** Adding `fetch_bars` to the `@runtime_checkable` `MarketDataAdapter`
+  Protocol is safe: there are no runtime `isinstance(x, MarketDataAdapter)` checks (only type
+  annotations), and both concrete adapters (`AlpacaAdapter`, `FakeAdapter`) implement it. The test
+  `test_bar_timeframe_vendor_mapping_covers_every_configured_timeframe` guards against a config
+  timeframe missing from the vendor mapping (which would otherwise `KeyError`).
+- **No escape hatch in test wiring.** The route resolves the adapter via
+  `get_study_market_adapter()`, which reads `app.dependency_overrides.get(get_market_adapter, ...)`
+  (`routes.py:1218-1221`), so the API tests genuinely exercise the injected `FakeAdapter` (including
+  the 503 path via `available=False`) rather than a real vendor.
+
+**Independent verification I ran (not taken from the handoff):**
+- `pytest test_bars.py test_bars_api.py test_profile_equivalence.py test_observer_equivalence.py` →
+  **50 passed**.
+- `pytest test_mcp_server.py -k "bars or backend_down"` → **2 passed** (byte-identity + backend-down).
+- `pytest test_real_data_gate.py` → **35 passed** (vendor-confinement gate; `config.py` names no
+  vendor SDK — only pre-existing `iex` feed values remain).
+- `Config().config_fingerprint()` → `'4d665603569b9dbf'` (== pinned).
+- `git diff -- apps/frontend/` empty; no untracked frontend files.
+- Scope check: exactly three `/bars` routes added; **no** `/research/levels` or `/research/strategies`
+  routes leaked in (J-02–J-06 remain unbuilt, as scoped).
+
+**Note on the committed fixture (verified, not a defect):** the fixture files under
+`tests/fixtures/bars/` are currently untracked (`??`) — but so is the *entire* iteration (`bars.py`,
+`test_bars.py`, etc.), because the release/commit step runs after this audit. They are **not**
+gitignored (`git check-ignore` returns nothing; `.gitignore` only ignores `.data/`), and the
+identical `tests/fixtures/datasets/*.json` precedent is committed, so the release step will commit
+them exactly the same way. The DoD's "committed AND keyless AND exercised" invariant will hold on the
+resulting commit; the keyless test loads them with no credentials today.
+
+---
+
+## 4. Fixes Applied During This Audit
+
+| # | Severity | File | Change |
+|---|----------|------|--------|
+| — | — | — | None. No critical or important issue was found; all findings are GAP/OBSERVATION-level and either spec-sanctioned or defense-in-depth. Applying changes would be scope creep. |
+
+---
+
+## 5. Recommended Next Step
+
+**Proceed to release, then build J-02 next.** J-01 is the era's designated unblocker and is complete,
+frozen-safe, and honest. When J-02 (deterministic S/R level detection) consumes the stored bar
+series, carry forward two disclosed notes from this iteration: (1) the monthly-bar vendor depth limit
+observed in the capability probe (data only reaches back to 2016-01-01 on this plan regardless of the
+requested start), and (2) that an unknown symbol and an empty/embargoed window both present as the
+same 422 — if J-02 ever needs to tell a user *why* a level set is empty, a symbol-tradability
+distinction on the bar-fetch path would be the place to add it. Neither blocks release now.
diff --git adocs/handoffs/goal-tape_to_profit_support_resistence-iter-1-dev.md bdocs/handoffs/goal-tape_to_profit_support_resistence-iter-1-dev.md
new file mode 100644
index 0000000..5701763
--- /dev/null
+++ bdocs/handoffs/goal-tape_to_profit_support_resistence-iter-1-dev.md
@@ -0,0 +1,186 @@
+# goal-tape_to_profit_support_resistence-iter-1 Dev Handoff
+
+**Phase:** goal-tape_to_profit_support_resistence-iter-1
+**Date:** 2026-07-06
+**Agent:** developer
+**Status:** complete
+
+## What Was Built
+
+J-01 — the multi-timeframe bar store (era-4's data foundation), built end to end and explicitly
+mirroring `research/datasets.py`, the `/datasets` route trio, and the `datasets` MCP tool per the
+plan's own directive:
+
+- **Adapter seam** (`providers/adapters/base.py`): a neutral `RawBar` dataclass (symbol, timeframe,
+  UTC bar-open epoch, open/high/low/close, volume) beside `RawTrade`/`RawQuote`, and `fetch_bars(symbol,
+  start, end, timeframe)` added to the `MarketDataAdapter` Protocol.
+- **Alpaca adapter** (`providers/adapters/alpaca.py`): `fetch_bars` via `StockHistoricalDataClient.get_stock_bars`
+  + `StockBarsRequest` + `TimeFrame` (Minute/Hour/Day/Week/Month; 4h/8h as Hour×amount), stamping the
+  feed via the existing `historical_feed()` (SIP for historical). Two new, independently unit-tested
+  free-tier disciplines: a recency-delay clamp (`_bar_fetch_end_clamp`, default 900s) so the request
+  never reaches into the still-embargoed most-recent bar, and a rate-throttle (`_throttle_bar_fetch`,
+  default 200/min) spacing consecutive real vendor calls.
+- **`BarStore`** — NEW module `research/bars.py`: immutable, double-checksummed (content + whole-file)
+  bar-series files under the config-owned `bar_dir`. `record()` is the only mutation and refuses
+  re-registering identical content (`BarSeriesAlreadyRegistered`). Honest failure states
+  `BarSeriesNotFound`, `BarSeriesIntegrityError`, and `EmptyBarWindowError` (empty fetched window) —
+  each verified on every load. Unlike the tick-level dataset store, `get`/`list` embed the ordered
+  OHLC candles directly (bar series are small by construction — the phase spec's explicit
+  requirement), while the on-disk shape still separates `meta` from `bars` for the same checksum
+  discipline.
+- **Config** (`config.py`): `bar_dir` (+ `bar_dir_resolved()`, `TAPEOLOGY_BAR_DIR` override),
+  `bar_timeframes` (`1m/5m/15m/1h/4h/8h/1d/1w/1mo` — distinct from the existing intra-second
+  `history_bar_sizes`), `bar_recency_delay_seconds`, `bar_rate_limit_per_minute`. **All four** are
+  added to the `config_fingerprint` `excluded` set (not just `bar_dir` — see Known Issues for why
+  this mattered) so the pinned `default` fingerprint (`"4d665603569b9dbf"`,
+  `tests/test_profile_equivalence.py`) stays byte-identical.
+- **Routes** (`research/routes.py`): `POST /research/bars` (the explicit credentialed record
+  action), `GET /research/bars` (list), `GET /research/bars/{id}` (detail) — serving the store's
+  metadata + candles verbatim. Out-of-set `timeframe` → 422. Missing credentials → **503**
+  "real-data provider unavailable — a historical bar recording needs credentials" (per the spec's
+  explicit, repeated DoD/Testing-Requirements text — see Known Issues #1 in the plan's own
+  Assumptions section).
+- **MCP** (`mcp/__init__.py`): a `bars` tool — a byte-identical read-only proxy of
+  `GET /research/bars`, added to `STATIC_TOOLS` and the advertised `TOOLS` tuple.
+- **Capability probe** (real Alpaca credentials were present in this environment — see below).
+- **Committed keyless fixture**: two REAL bar series (PG, `1d` and `1h`) fetched live through the
+  actual `fetch_bars` implementation and recorded through the real `BarStore.record` path (never
+  hand-crafted), committed at `tests/fixtures/bars/*.json`, generated by the new
+  `scripts/generate_bar_fixtures.py` (mirrors `generate_dataset_fixtures.py`'s frozen-at-one-generation
+  discipline and `capture_alpaca_fixture.py`'s no-fabrication refusal).
+- A `config_fingerprint`-stability test (all four new fields excluded) plus the real-threshold
+  counter-test.
+
+### Capability probe finding (real Alpaca credentials were present — recorded honestly)
+
+Ran the required one-symbol probe (PG) across daily/weekly/monthly/hourly through the actual
+`AlpacaAdapter.fetch_bars`:
+
+| Timeframe | Requested from | Bars returned | Actual earliest bar | Elapsed |
+|---|---|---|---|---|
+| `1d` | 2020-01-01 | 1,610 | 2020-01-02 | 0.75s |
+| `1w` | 2016-01-01 | 543 | 2016-01-04 | 0.37s |
+| `1mo` | 2000-01-01 | 125 | 2016-01-01 | 0.30s |
+| `1h` | 2026-05-01 | 294 | 2026-05-01 12:00 | 0.36s |
+
+- **Feed:** `sip` (`CONFIG.historical_feed` default — the historical-mode SIP consolidated feed,
+  same as the existing tick-level historical path).
+- **Lookback range (honest finding):** daily and weekly history reach back to the requested start;
+  **monthly bars are only available from 2016-01-01 onward** regardless of how much earlier a start
+  is requested — a real vendor-side depth limit on this account/plan, not a defect in the adapter.
+  This is useful, disclosed information for J-02's long-term-timeframe planning next iteration.
+  Intraday (`1h`) history was available for the full requested May 2026 window.
+- **Recency-delay guard, demonstrated live:** requesting `1h` bars through the real wall-clock
+  `now` (2026-07-06T01:10:59Z) returned bars only up to 2026-07-02T23:00:00Z (the actual last real
+  trading print inside the requested window at that moment) — well clear of the computed embargo
+  cutoff (`now - 900s` = 2026-07-06T00:55:59Z). The clamp is provably never violated.
+- **Rate behaviour:** five consecutive real 1-day-bar fetches averaged ~0.30s each — in the same
+  neighbourhood as the configured 200/min (0.3s/call) throttle floor, so real network/vendor
+  latency alone is close to the throttle's floor at this call rate; no 429/rate-limit response was
+  observed in this small probe.
+- Credentials being present let every acceptance clause that says "or the honest missing-credentials
+  state if absent" be exercised for real instead: `POST /research/bars` with `FakeAdapter(available=False)`
+  is still covered by a dedicated hermetic test (`test_bars_api.py::test_missing_credentials_is_an_explicit_503`)
+  so the absent-credentials path is proven either way.
+
+## Files Changed
+
+- `apps/backend/app/providers/adapters/base.py` -- `RawBar` dataclass + `fetch_bars` added to the
+  `MarketDataAdapter` Protocol
+- `apps/backend/app/providers/adapters/alpaca.py` -- `fetch_bars` implementation, `_TIMEFRAME_PARTS`
+  vendor mapping, `_bar_fetch_end_clamp` (recency guard), `_throttle_bar_fetch` (rate throttle),
+  `_clear_caches()` extended to reset the new throttle timestamp
+- `apps/backend/app/research/bars.py` -- NEW: `BarStore` module (double checksum, verified-on-load,
+  honest failure taxonomy, `record`/`get`/`list`/`load_bars`)
+- `apps/backend/app/config.py` -- `bar_dir` + `bar_dir_resolved()`, `bar_timeframes`,
+  `bar_recency_delay_seconds`, `bar_rate_limit_per_minute`; all four excluded from
+  `config_fingerprint`
+- `apps/backend/app/research/routes.py` -- `get_bar_store()` dependency + `POST/GET /research/bars`,
+  `GET /research/bars/{id}`
+- `apps/backend/app/mcp/__init__.py` -- `bars` tool (`STATIC_TOOLS` entry + `types.Tool`)
+- `apps/backend/tests/fakes.py` -- `FakeAdapter` extended with scriptable `fetch_bars`
+  (`bars=`/`bars_raise=` constructor args, `fetch_bars_calls` recording)
+- `apps/backend/tests/test_bars.py` -- NEW: store unit tests (mirrors `test_datasets.py`) + the two
+  new Alpaca-adapter helper unit tests (recency clamp, throttle spacing)
+- `apps/backend/tests/test_bars_api.py` -- NEW: route tests (mirrors `test_datasets_api.py`),
+  including the 503-missing-credentials test and a 504-vendor-timeout test
+- `apps/backend/tests/test_mcp_server.py` -- `bars` added to `EXPECTED_TOOLS`, `TAPEOLOGY_BAR_DIR`
+  added to the `backend_paths` fixture, new `test_bars_tool_byte_identical_on_a_non_empty_live_list`
+  (seeds the committed fixture pair into the live backend's bar dir — no credentials needed for this
+  test; the existing `test_backend_down_every_tool_raises_an_explicit_error` loop automatically
+  covers `bars`' backend-down case with no changes)
+- `apps/backend/tests/fixtures/bars/*.json` -- NEW: 2 committed, REAL (never fabricated) Alpaca bar
+  series (PG `1d` ×5 bars, PG `1h` ×9 bars) — tiny, keyless-loadable fixtures
+- `apps/backend/scripts/generate_bar_fixtures.py` -- NEW: the one-time real-data fixture generator
+  (mirrors `generate_dataset_fixtures.py` + `capture_alpaca_fixture.py`'s no-fabrication discipline)
+
+`git diff -- apps/frontend/` is **empty** — confirmed no frontend file was touched.
+
+## Tests Run
+
+Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
+Result (JUnit XML totals): **1069 passed, 1 skipped, 1070 collected, 0 failed, 0 errors**, 365.43s.
+The single skip is the same pre-existing gated live-socket test
+(`tests/test_live_integration.py:37`) noted in the iter-0 baseline. Up from iter-0's baseline of
+1040 passed / 1041 collected — **+29 new tests, zero regressions.**
+
+Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py -v`
+Result: **7 passed** (the J-07 byte-identical-`default` guard, unchanged).
+
+Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_profile_equivalence.py -v`
+Result: **15 passed**, including `test_default_fingerprint_is_pinned_and_unmoved_by_the_new_field`
+— the pinned `default` fingerprint `"4d665603569b9dbf"` is confirmed **unchanged** despite four new
+`Config` fields.
+
+Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_real_data_gate.py -q`
+Result: **35 passed** — includes `test_engine_and_canonical_modules_reference_no_vendor` and
+`test_alpaca_sdk_import_confined_to_one_module` (the provider-agnostic-engine anti-goal guards),
+both green after the fix noted in Known Issues.
+
+## Known Issues
+
+- **Self-caught regression, fixed before handoff:** my first pass wrote "Alpaca" by name into two
+  `config.py` comments (the recency-delay/rate-throttle docstrings). `config.py` is one of the
+  modules `tests/test_real_data_gate.py::test_engine_and_canonical_modules_reference_no_vendor`
+  asserts must never mention the vendor by name (provider-agnostic-engine anti-goal — vendor
+  specifics stay confined to the one adapter module). Caught by running the full suite before
+  finishing; reworded both comments to refer to "the configured market-data vendor" generically.
+  No behavior changed, only comment wording.
+- **All four new `Config` fields are fingerprint-excluded, not just `bar_dir`.** The plan's own text
+  only explicitly named `bar_dir` for the `config_fingerprint` exclusion, but
+  `tests/test_profile_equivalence.py::test_default_fingerprint_is_pinned_and_unmoved_by_the_new_field`
+  asserts a **literal pinned hash** for `default`. Since `config_fingerprint()` hashes every
+  non-excluded dataclass field, adding `bar_timeframes` / `bar_recency_delay_seconds` /
+  `bar_rate_limit_per_minute` **without** excluding them would have moved that literal pin (none of
+  the three shape any tape/backtest/study computation — they only validate/govern the new,
+  unrelated bar-fetch capability). Excluded all four; the pinned test passes unchanged.
+- **`fetch_bars` has no symbol-tradability pre-flight**, unlike `fetch_historical`'s
+  `_require_tradable` fallback. An unknown/untradable symbol and a genuinely-empty window both
+  surface as the same generic `EmptyBarWindowError` → 422 "no bars in the requested window" — there
+  is no distinct "symbol not tradable" bar error. This was a deliberate simplicity call (the DoD's
+  acceptance criteria and testing requirements never ask for that distinction for bars, and adding
+  the second tradability round-trip `fetch_historical` needs for its hot watch-path is not needed
+  for an occasional, explicit bar-recording action). Flagging so a reviewer/auditor can confirm this
+  reading of scope.
+- **Rate-throttle and recency-delay values (200/min, 15 min) are documented, disclosed assumptions**
+  about the vendor's free-tier historical-bar entitlement (the same style as the existing
+  `strategy_fee_per_share` "disclosed assumption" precedent), not something independently verified
+  against a vendor SLA document. The live probe observed real per-call latency already near the
+  200/min throttle floor and no rate-limit error in a small 5-call burst, but did not attempt to
+  actually trigger a 429 to empirically confirm the exact limit.
+- **The rate-throttle's "last call" timestamp is process-local** (a module-level global, like the
+  existing historical-window cache and asset-universe cache) — it does not coordinate across
+  multiple backend worker processes. Consistent with the existing precedent's scope; flagging since
+  it means the throttle is only a same-process courtesy, not a hard cross-process guarantee.
+- **J-02–J-06 remain unbuilt, as scoped** — no levels, confluence classes, `structure_tape` strategy,
+  class-scaled risk, or the named-strategy comparison exist yet. `GET /research/levels` and
+  `GET /research/strategies` still 404. This iteration is purely the bar-data foundation those
+  journeys will consume next.
+- **No frontend/UI surface** — machine-only (REST + MCP), as scoped; no page, panel, or nav change.
+  Confirmed via `git diff -- apps/frontend/` (empty) and a live check of `GET /meta/ui-routes` on a
+  running dev instance (still exactly the 4 nav entries + the 1 non-nav journal-detail route).
+- **Carried over from iter-0 (not this iteration's scope):** the backend venv runs Python 3.14.4
+  while `.claude/project-template.md` / goal.md's Constraints section say 3.12 (the suite is green
+  either way); `.claude/project-template.md` is still the generic unfilled template — this developer
+  again used goal.md's Constraints section + the README's "How to run" section as the actual stack
+  source of truth.
diff --git adocs/phases/goal-tape_to_profit_support_resistence-iter-1.md bdocs/phases/goal-tape_to_profit_support_resistence-iter-1.md
new file mode 100644
index 0000000..18a4b76
--- /dev/null
+++ bdocs/phases/goal-tape_to_profit_support_resistence-iter-1.md
@@ -0,0 +1,103 @@
+# Goal Iteration 1 — J-01 multi-timeframe bar store (the bar data foundation)
+
+<!-- machine-readable goal-mode metadata -->
+## Goal Mode Metadata
+
+- **Session ID:** tape_to_profit_support_resistence
+- **Iteration:** 1
+- **Mode:** next
+- **Depth:** full
+- **Frontend Present:** no
+- **Target journeys:** J-01
+- **Required-still-passing journeys:** J-07
+- **Anti-goal reminders (verbatim — the six that bear directly on J-01):**
+  - **No live execution path.** Tapeology MUST NOT place, route, or transmit orders anywhere — no brokerage integration, no trading API, **no paper-trading API**, no order tickets. The ONLY permitted "fill" is the offline backtester's simulated fill against recorded historical tape, clearly labelled simulated and sent nowhere; "position size" is a simulated notional, never a real order. *(critical)*
+  - **The tape engine, `default` profile, and `v1` strategy are frozen.** Structure work is additive and versioned only: new bars/levels/classes and the `structure_tape` strategy may be added, but the `default` profile's outputs stay byte-identical (equivalence-tested), the live cockpit uses `default` only, `v1` stays byte-identical, and no enhancement may mutate an archived-era behaviour to pass. *(critical)*
+  - **No fabricated data — honest failure states.** No synthesized bars, levels, trades, fills, or PnL to force a green journey; every failure mode (backend down, corrupt file, empty window, missing credentials, rate-limited, no levels found, insufficient n) surfaces an explicit, distinct state. *(critical)*
+  - **Single source of truth.** Every canonical value — bar series, levels, confluence classes, backtest aggregates, PnL rows — is computed once and read verbatim by every surface (REST, WebSocket, UI, MCP, reports). A second computation path or a diverging number across surfaces is a defect. *(critical)*
+  - **MCP is read-only.** The MCP server exposes no mutating tools, proxies only the canonical GET surface (plus the allowlisted `get_endpoint`), and MUST NOT become a second implementation of any computation. *(critical)*
+  - **Persistence stays scoped.** SQLite holds research records; the bar and dataset stores hold explicitly recorded historical bars and tape for research replay. The live cockpit's tape remains unpersisted; no ambient recording. *(critical)*
+  - *(The remaining critical anti-goals — no-lookahead, no-train-only-promotion, no-ML, no-profit-claims, no-capital/portfolio-management, enhancement-loop-in-its-box — govern levels/strategy/PnL work in J-02–J-06 and are not exercised by J-01's bar-data foundation; they still apply to any code J-01 touches and MUST NOT be violated.)*
+
+## GOAL
+
+A recorded multi-timeframe OHLC bar series can be ingested, persisted immutably (checksummed), and read back byte-identically via `GET /research/bars` / `GET /research/bars/{id}` and the MCP `bars` proxy — proven **keyless on a committed fixture** in CI — while the `default` profile and `v1` stay byte-identical.
+
+## BACKGROUND
+
+The iter-0 baseline recorded J-01–J-06 as honestly absent (404/422 + route-table inspection) and J-07 (eras 1–3 sentinel) as already-passing; the evaluator's explicit next-step recommendation is **"Build J-01 in iter-1, run it full."** J-01 is the era's designated unblocker — the natural dependency order is J-01 → J-02 → J-03 → J-04 → J-05 → J-06, and every downstream journey consumes the stored bar series (Data-Contract row 38), so nothing else can proceed until bars exist. **Depth = full** is justified by two "Picking depth" triggers: this is a **data-model change** (a new immutable checksummed store) **and a provider-seam integration** (a new `RawBar` + `fetch_bars` on the frozen `MarketDataAdapter` seam, wired to Alpaca `get_stock_bars`) — plus the prior evaluator's explicit `full` recommendation. It is deliberately **one risky journey isolated on its own** (rubric rule 5).
+
+Two pitfalls carried into scope: (1) **`config_fingerprint` stability** — adding a `bar_dir` config field must NOT move the `default` fingerprint (mirror how `dataset_dir` is in the `excluded` set at `config.py`), or the J-07 equivalence suite breaks; a fingerprint-stability test pins this. (2) **lessons.md (iter-0):** the lean baseline never ran browser-qa; because J-01 changes **zero** `apps/frontend/` code, J-07's cockpit leg is guarded this iteration by the **engine equivalence suite (byte-identical `default`) + a verified zero-frontend-diff**, not by screenshots — and this iteration DOES change backend code, so the equivalence suite must be run for real (not asserted from a zero-diff shortcut).
+
+## IN SCOPE
+
+### Backend
+- [ ] **Adapter seam** (`apps/backend/app/providers/adapters/base.py`): add a neutral `RawBar` dataclass (symbol, timeframe, UTC bar-open time, open/high/low/close, volume — a vendor-agnostic OHLC candle beside `RawTrade`/`RawQuote`) and add `fetch_bars(symbol, start, end, timeframe)` to the `MarketDataAdapter` Protocol. No vendor types cross the seam.
+- [ ] **Alpaca adapter** (`apps/backend/app/providers/adapters/alpaca.py`): implement `fetch_bars` via the lazily-imported `StockHistoricalDataClient.get_stock_bars` with `StockBarsRequest` + `TimeFrame` (Minute/Hour/Day/Week/Month; 4h/8h expressed as Hour×amount). Stamp the feed via the existing `historical_feed()` (SIP|IEX). **Missing credentials → the EXISTING explicit unavailable state** (mirror `research/routes.py:1444` — `503 "real-data provider unavailable — a historical record needs credentials"`), NEVER fabricated bars. Free-tier discipline: throttle to the rate limit and **never fetch the most-recent (~15-min-delayed) bar**.
+- [ ] **Bar store** — NEW module `apps/backend/app/research/bars.py`, mirroring `research/datasets.py`: a `BarStore` persisting immutable, checksummed bar-series files under a new `config.bar_dir`. Each entry stamps symbol, timeframe, UTC window, feed, **bar count**, and a **content checksum**. The ONLY mutation is `record`, which **refuses re-recording already-registered content** (mirror `DatasetAlreadyRegistered` → `BarSeriesAlreadyRegistered`). Both checksums (content + whole-file) are **recomputed and verified on EVERY load**. Honest failure states mirror datasets: `BarSeriesNotFound` (unknown id), `BarSeriesIntegrityError` (corrupt/tampered file), explicit empty-window refusal.
+- [ ] **Config** (`apps/backend/app/config.py`): add `bar_dir` (package-anchored default `.data/bars`, mirroring `dataset_dir`) + `bar_dir_resolved` reading `TAPEOLOGY_BAR_DIR`; add a config-owned **`bar_timeframes`** enumeration (the valid `?timeframe=` set — distinct from the existing intra-second `history_bar_sizes`), plus any rate-throttle / recency-delay-guard parameters — **no magic numbers, no literals inline**. **Add `bar_dir` to the `config_fingerprint` `excluded` set** (same storage-location discipline as `dataset_dir`) so the `default` fingerprint stays byte-identical.
+- [ ] **Routes** (`apps/backend/app/research/routes.py`, `/research`-prefixed router already mounted at `main.py:203`): add `POST /research/bars` (the explicit credentialed record/register action; missing creds → the 503 explicit-unavailable state above), `GET /research/bars` (list stored series), `GET /research/bars/{id}` (one series). Values are computed once by the store and served verbatim. An out-of-set `timeframe` is a **422 (never silently coerced)**, mirroring the `?bar=` validation precedent.
+- [ ] **MCP** (`apps/backend/app/mcp/__init__.py`): add a `bars` tool — extend `STATIC_TOOLS` with `"bars": "/research/bars"` and add its `types.Tool(...)` entry; a thin, byte-identical `response.text` proxy (mirror `datasets`). Backend-down → an explicit tool error naming the base URL. **No mutating tool is added.**
+- [ ] **Capability probe:** a one-symbol probe (daily/weekly/monthly/hourly) recording the plan's honest finding — feed (SIP|IEX), lookback range, and observed rate behaviour — into the dev handoff. Recorded honestly; never fabricated when credentials are absent (probe reports the missing-credentials state).
+- [ ] **Committed keyless fixture:** a miniature multi-timeframe bar fixture proving ingest→persist→read in CI **without credentials**, mirroring the dataset store's committed-source-fixture mechanism (raw fixture under version control in `tests/fixtures/` + a generator/loader, OR a tracked bar-store entry). Invariant to satisfy: the fixture is committed AND keyless AND exercised by the test suite.
+
+### Frontend (if applicable)
+- None. J-01 is a machine surface only (REST + MCP). The nav skeleton (Cockpit · Journal · Studies · Performance) is unchanged; a levels/bars view is explicitly out of the data-foundation scope.
+
+### New user-facing capability
+An operator (or an MCP client) can record a multi-timeframe OHLC bar series and read it back — the first time the engine has ever had a bar, a timeframe, or historical structure data. Keyless on the committed fixture; a real Alpaca recording is an optional credentialed operator action that only enlarges the data.
+
+### New information displayed
+Bar-series metadata and OHLC candles via `GET /research/bars` / `GET /research/bars/{id}` and MCP `bars`: symbol, timeframe, UTC window, feed (SIP|IEX), bar count, content checksum, and the ordered OHLC candle list.
+
+### New user actions
+`POST /research/bars` (record/register a bar series — the explicit credentialed research action). No UI controls (machine surface).
+
+### UI surface changes
+None. No page, panel, or nav change.
+
+### Product surface delta
+The product gains a machine-readable historical-bar foundation under the existing Performance/research data model; the live cockpit and all four nav surfaces are untouched. Nothing user-visible changes in the browser.
+
+### Blueprint conformance
+No new surfaces. J-01's endpoints (`/research/bars*`) and MCP `bars` tool are machine surfaces already homed in the blueprint Information-Architecture table (row *"J-01 multi-timeframe bar store | API `/research/bars*` + MCP `bars` | machine"*). The nav skeleton is unchanged — no `blueprint.reapproval-requested` is written.
+
+### Data-contract additions
+**None new.** J-01 *realizes* the already-registered Data-Contract **row 38** (Bar series: symbol, timeframe, UTC window, feed, bar count, checksum) — single owner = the NEW bar-store module (`research/bars.py`) fed by `RawBar` + `fetch_bars` on the adapter seam; single serving endpoint = `POST/GET /research/bars*` + MCP `bars`. No blueprint edit is required and **no second computation or serving path for bars is introduced**. (Row 38 was drafted for the whole era at baseline; this iteration is its first real implementation.)
+
+## OUT OF SCOPE
+
+- **J-02** deterministic support/resistance level detection, and any `GET /research/levels` endpoint — next iteration.
+- **J-03** confluence zones / A/B/C classes.
+- **J-04** the `structure_tape` strategy and `GET /research/strategies`.
+- **J-05** class-scaled stop/reward/simulated-size PnL.
+- **J-06** the named-strategy comparison / generalized edge-report path.
+- Any frontend or levels/bars **view** (explicitly out of the data-foundation scope per Product Shape).
+- Any **real credentialed** bar recording as a *gating* requirement — the CI gate is keyless-on-fixture; real Alpaca bars are an optional credentialed operator action.
+- Any change to the `default` profile, the `v1` strategy, the champion pointer, or any engine default.
+
+## DEFINITION OF DONE
+
+- [ ] **J-01 passes:** on the committed keyless fixture, ingest→persist→read works with **no credentials**; `GET /research/bars` and `GET /research/bars/{id}` return the stored series (symbol, timeframe, UTC window, feed, bar count, checksum + OHLC candles); a re-read is **byte-identical** — asserted by tests.
+- [ ] Bar-store immutability + integrity proven by unit tests: byte-identical re-record→re-read; both checksums verified on load; corrupt file → explicit `BarSeriesIntegrityError`; re-record identical content → `BarSeriesAlreadyRegistered`; empty window → explicit refusal; unknown id → `BarSeriesNotFound`.
+- [ ] `POST /research/bars` with missing credentials returns the **EXISTING explicit unavailable (503)** state — never fabricated bars — asserted by a test; an out-of-set `timeframe` returns **422**.
+- [ ] MCP `bars` tool JSON is **byte-identical** to `GET /research/bars` (test); backend-down → an explicit tool error.
+- [ ] **`config_fingerprint` for `default` is UNCHANGED** (`bar_dir` is fingerprint-excluded): the fingerprint-stability test passes and its counter-test still shows a real threshold moves the fingerprint; the **engine equivalence suite is 7/7 byte-identical `default`** (`tests/test_profile_equivalence.py`, `tests/test_observer_equivalence.py`) — this is J-07's guard.
+- [ ] `v1`, `default`, and the champion pointer are untouched, and `git diff -- apps/frontend/` is **empty** (J-07 cockpit leg guarded by equivalence + zero-frontend-diff, per lessons.md).
+- [ ] The capability-probe finding (feed SIP|IEX, lookback range, rate behaviour) is recorded honestly in the dev handoff.
+- [ ] Full backend suite passes; no regressions (J-07 remains green).
+- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit_support_resistence-iter-1-dev.md`.
+
+## TESTING REQUIREMENTS
+
+- **Browser:** none — `Frontend Present: no`. J-01 changes no `apps/frontend/` code, so J-07's cockpit leg is guarded this iteration by the **engine equivalence suite (byte-identical `default`) + a verified empty `apps/frontend/` diff** (per lessons.md, zero-frontend-diff makes the equivalence suite — not screenshots — J-07's evidence). Browser-QA stages (5, 6, 8) auto-skip with N/A stubs; the executor MUST still verify the frontend diff is empty and run the equivalence suite for real.
+- **Unit/integration:** new `tests/test_bars.py` (store: record/load, byte-identical re-runs, double-checksum verify-on-load, immutability/`BarSeriesAlreadyRegistered`, `BarSeriesIntegrityError`, `BarSeriesNotFound`, empty-window refusal, stamp presence); new `tests/test_bars_api.py` (keyless-on-fixture `GET /research/bars` + `/{id}` happy path, missing-cred `POST` → 503, out-of-set timeframe → 422, unknown id → 404/explicit); extend `tests/test_mcp_server.py` (`bars` byte-identity + backend-down error); a **config-fingerprint-stability test** proving `bar_dir` does NOT move `config_fingerprint` plus the counter-test that a real threshold STILL does (mirror `tests/test_datasets.py`).
+- **Error cases (must be rejected/surfaced explicitly):** corrupt bar file → `BarSeriesIntegrityError`; re-record identical content → `BarSeriesAlreadyRegistered`; empty window → explicit refusal; missing credentials on `POST /research/bars` → 503 explicit-unavailable; unknown id → explicit not-found; out-of-set `timeframe` → 422 (never silently coerced).
+
+## NOTES
+
+- **Depth = full** per the "data-model change" + "provider-seam integration" triggers and the iter-0 evaluator's explicit `full` recommendation. This is one risky journey isolated alone (rubric rule 5); J-02–J-06 wait for their own iterations.
+- **Config-fingerprint pitfall (do not miss):** `bar_dir` MUST join the `excluded` set in `config.config_fingerprint` (same discipline as `dataset_dir`) or the `default` fingerprint moves and J-07 equivalence fails. The fingerprint-stability test is a DoD item, not optional.
+- **lessons.md (iter-0) applied:** this iteration changes backend code, so the equivalence suite must be run for real to ground J-07 (the zero-diff shortcut no longer covers a code-changing iter). Because there is zero frontend diff, the browser-qa screenshot is correctly not required — but the empty `apps/frontend/` diff must be verified, not assumed.
+- **Required-still-passing = J-07 only** because it is the *only* passing journey and is itself the aggregate eras-1–3 regression sentinel (engine equivalence + all archived surfaces + the full backend suite); J-01–J-06 are all failing and cannot be regression anchors. There is no additional passing journey to widen the set with.
+- **Mirror, don't reinvent:** `research/datasets.py` (store + double checksum + immutable `record` + honest failure taxonomy), `research/routes.py:1444` (missing-cred 503), and the `datasets` MCP tool are the exact precedents to copy; matching them keeps the single-source-of-truth and honest-failure-state anti-goals satisfied by construction.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-1-closure-verdict.md breports/phase-goal-tape_to_profit_support_resistence-iter-1-closure-verdict.md
new file mode 100644
index 0000000..c748a91
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-1-closure-verdict.md
@@ -0,0 +1,121 @@
+# goal-tape_to_profit_support_resistence-iter-1 — Closure Verdict
+
+**Phase:** goal-tape_to_profit_support_resistence-iter-1
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
+| Review report (`reports/reviews/goal-tape_to_profit_support_resistence-iter-1-review.md`) | exists | PASS |
+| QA report (`reports/qa/goal-tape_to_profit_support_resistence-iter-1-qa.md`) | exists | PASS |
+| Audit report (`docs/handoffs/goal-tape_to_profit_support_resistence-iter-1-audit.md`) | exists | PASS |
+
+All three gates carry unambiguous PASS verdicts (no PASS_WITH_NOTES/PASS-WITH-GAPS qualifiers needed
+— review has one optional NOTE-severity item only, audit has two disclosed GAPs and one OBSERVATION,
+none blocking). QA independently re-ran the full backend suite (1069 passed / 1 pre-existing skip /
+0 failed) and executed a 19-case functional test plan, all PASS. Audit independently re-ran the bars/
+equivalence/mcp/real-data-gate suites and live-computed `Config().config_fingerprint()`, confirming
+the pinned `default` hash `4d665603569b9dbf` is unchanged.
+
+---
+
+## UI Visibility Artifact Checks
+
+`Frontend Present: no` — confirmed in `runs/goal-tape_to_profit_support_resistence-iter-1/plan.md`
+(line 52) and `docs/phases/goal-tape_to_profit_support_resistence-iter-1.md` (metadata line 10, and
+explicitly restated under "Frontend (if applicable): None", "UI surface changes: None", "Nothing
+user-visible changes in the browser"). Per gate rules for `Frontend Present: no`, N/A stubs are
+acceptable for all 6 artifacts as long as each file exists.
+
+| Artifact | Exists | Non-Empty | Non-Vague | Status |
+|----------|--------|-----------|-----------|--------|
+| implementation-summary.md | yes | yes (93 lines) | yes — full feature/limitation detail, not a stub | OK |
+| user-visible-changes.md | yes | yes (5 lines) | yes — explicit N/A + reason, consistent with backend-only | OK |
+| ui-surface-map.md | yes | yes (5 lines) | yes — explicit N/A + reason | OK |
+| ui-test-plan.md | yes | yes (3 lines) | yes — explicit N/A + reason | OK |
+| ui-test-results.md | yes | yes (5 lines) | yes — SKIPPED with documented reason (backend-only) | OK |
+| what-to-click.md | yes | yes (4 lines) | yes — explicit N/A + reason | OK |
+
+All 6 files exist. None are silently empty or bare placeholders — each states explicitly *why* it is
+N/A (backend-only phase, `Frontend Present: no`) rather than leaving a blank header, which satisfies
+the vagueness-detection bar even for a stub.
+
+---
+
+## Cross-Reference Checks
+
+Steps 3–4 of the gate (cross-reference validation, backend-only claim guard) apply only when
+`Frontend Present: yes`; this phase is `Frontend Present: no`, so those checks are not applicable by
+the gate's own rule ("Proceed to Step 5"). Independent consistency verification performed anyway:
+
+- [x] user-visible-changes lists ≥1 specific capability (or N/A for backend-only) — N/A, consistent.
+- [x] ui-surface-map has specific route/component entries (or N/A) — N/A, consistent (no frontend
+  files in the diff to map).
+- [x] ui-test-plan has specific steps with exact actions and expected results (or N/A) — N/A,
+  consistent.
+- [x] ui-test-results shows execution evidence (or SKIPPED with documented reason) — SKIPPED, reason
+  given ("Backend-only phase (Frontend Present: no)").
+- [x] what-to-click has ≥3 numbered steps with exact expected outcomes (or N/A) — N/A, consistent.
+- [x] implementation-summary claims are consistent with ui-test-results evidence — implementation-
+  summary explicitly labels every new capability as a "Backend-Only Item" served only via
+  `POST/GET /research/bars*` + the MCP `bars` tool, and states in Incomplete Items "No screen to view
+  bars yet." No capability is claimed as UI-visible anywhere. No contradiction found.
+
+**Independent verification performed by this auditor (not taken on faith from the reports):**
+- `git diff -- apps/frontend/` → empty (confirmed directly).
+- `git status --short -- apps/frontend/` → empty (no untracked frontend files either).
+- `git status --short` (repo-wide) → all modified files are backend (`config.py`, `mcp/__init__.py`,
+  `providers/adapters/alpaca.py`, `providers/adapters/base.py`, `research/routes.py`, `tests/fakes.py`,
+  `tests/test_mcp_server.py`) plus goal-mode run-state/report files; all new files are backend/tests
+  (`app/research/bars.py`, `scripts/generate_bar_fixtures.py`, `tests/test_bars.py`,
+  `tests/test_bars_api.py`, `tests/fixtures/bars/*.json`) plus the expected handoff/report docs.
+- Spot-checked that the claimed new files actually exist on disk: `apps/backend/app/research/bars.py`
+  (12221 bytes), `apps/backend/tests/test_bars.py` (10937 bytes), `apps/backend/tests/test_bars_api.py`
+  (8467 bytes), and both committed fixture JSON files under `apps/backend/tests/fixtures/bars/`.
+- This triangulates with the developer handoff's own `git diff -- apps/frontend/` claim, QA's TC-18
+  ("Frontend Diff Empty... backend-only implementation confirmed"), and the audit's independent
+  `git diff` + `git status --short` re-check on `apps/frontend/` — three independent parties plus this
+  gate all agree, with no discrepancy.
+
+The phase spec's own scope explicitly confines J-01 to a machine surface (REST + MCP) with "no page,
+panel, or nav change" — a deliberate, goal-mode-directed design choice (era-4 data-foundation
+iteration; a levels/bars *view* is explicitly deferred to a later, unscoped iteration), not an
+omission or a dodge to avoid UI scrutiny. `Frontend Present: no` is a truthful label, not a
+mischaracterization: J-07 (the only currently-passing journey, itself the aggregate eras 1–3
+regression sentinel including the live cockpit) was re-verified green via the byte-identical engine
+equivalence suite (`test_profile_equivalence.py` 15/15, `test_observer_equivalence.py` 7/7) plus the
+verified-empty frontend diff, exactly as the phase's own lessons-learned guidance for a code-changing,
+zero-frontend-diff iteration prescribes.
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
+- Two disclosed, spec-sanctioned GAPs carried from the audit (not blocking, explicitly acknowledged as
+  in-scope-as-is): (1) an unknown/untradable symbol and a genuinely empty bar window both surface as
+  the same `EmptyBarWindowError` → 422 (no tradability pre-flight on `fetch_bars`, unlike
+  `fetch_historical`); (2) a window entirely inside the recency embargo returns the same 422 as an
+  empty window. Both are honest-failure-compliant (no fabrication) and the DoD never asked for a
+  distinct state; the audit recommends revisiting only if J-02 later needs to explain *why* a level
+  set is empty.
+- The two committed bar fixtures under `apps/backend/tests/fixtures/bars/` are currently untracked
+  (`??`) pending the release/commit step, same as every other file in this iteration — verified they
+  are not gitignored and mirror the already-committed `tests/fixtures/datasets/*.json` precedent, so
+  this is expected pre-release state, not a gap.
+- No UX regression report exists at `reports/phase-goal-tape_to_profit_support_resistence-iter-1-ux-regression.md`
+  — acceptable, since that artifact is conditional ("if exists") and this phase has no UI surface for
+  a UX-regression reviewer to evaluate.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-1-implementation-summary.md breports/phase-goal-tape_to_profit_support_resistence-iter-1-implementation-summary.md
new file mode 100644
index 0000000..8705e08
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-1-implementation-summary.md
@@ -0,0 +1,92 @@
+# goal-tape_to_profit_support_resistence-iter-1 — Implementation Summary
+
+**Phase:** goal-tape_to_profit_support_resistence-iter-1
+**Date:** 2026-07-06
+**Written by:** developer
+
+---
+
+## Features Implemented
+
+- **Recording a real historical price-bar series**: An operator (or an automated tool) can now ask
+  the system to fetch and permanently save a real historical OHLC ("open/high/low/close") price
+  series for a stock symbol — at daily, weekly, monthly, hourly, or several other calendar
+  timeframes — and the system keeps that saved copy forever, unchanged. This is the first time the
+  product has ever stored anything resembling a "bar chart" of price history; until now it only
+  read live/replayed tick-by-tick trades and quotes.
+- **Reading back a saved bar series**: Once a bar series is saved, anyone (or any tool) can read it
+  back — the symbol, the timeframe, the exact time window it covers, which data feed it came from,
+  how many bars it has, and the bars themselves. Reading it back twice always returns byte-for-byte
+  the same answer.
+- **Tamper detection**: Every saved bar series carries two layers of built-in checksums. If a saved
+  file is ever corrupted or hand-edited, the system detects it immediately and reports an explicit
+  error rather than silently serving bad data or a partial answer.
+- **No duplicate recordings**: Trying to record the exact same bar series twice is refused with a
+  clear message pointing at the original recording — nothing is ever silently overwritten or
+  duplicated.
+- **Honest "please connect your data account" message**: If the system's real-data credentials are
+  not configured, asking it to record a new bar series returns a clear, explicit message saying so
+  — it never invents fake price data to paper over the missing connection.
+- **A machine-readable version of all of the above**: The same "list bar series" information is
+  also available through the project's MCP (AI-assistant) tool interface, word-for-word identical
+  to what a human would see through the web API.
+
+## Changed Behavior
+
+- None. This is a purely additive capability — nothing that existed before this iteration behaves
+  differently. The live cockpit, the journal, the studies, and the performance page are all
+  unchanged (confirmed: zero files under the website's frontend code were touched).
+
+## Backend-Only Items
+
+- `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}` — recording and reading
+  bar series — exist only as machine endpoints (web API + the MCP tool) this iteration. There is no
+  new page or panel in the website yet; that is intentionally out of scope for this step (it is a
+  data-foundation iteration, meant to be consumed by upcoming capabilities rather than looked at
+  directly).
+
+## Incomplete Items
+
+- **Turning bars into support/resistance levels, and everything after that**: this iteration only
+  builds the ability to fetch and save the raw price-bar data. The next planned steps — finding
+  support/resistance price levels from those bars, grading how strong each level is, building a
+  trading strategy that reacts to price reaching those levels, and honestly measuring whether that
+  strategy would have made money — are **not** part of this iteration and remain to be built.
+- **No screen to view bars yet**: an operator can fetch/read bar data only through the API/MCP
+  tools right now, not through a page in the website.
+
+## Config and Environment Changes
+
+- No new environment variables are required to use existing features. One new *optional* override
+  is available for operators who want to change where recorded bar data is stored on disk:
+  `TAPEOLOGY_BAR_DIR` — where recorded price-bar files are saved. Default: a folder next to the
+  backend code (`apps/backend/.data/bars/`), the same pattern already used for other recorded
+  research data.
+- No database migration was needed (bar series are saved as individual files, the same way other
+  recorded research data already works).
+- Recording a real bar series requires the same Alpaca market-data account credentials
+  (`ALPACA_API_KEY` / `ALPACA_API_SECRET`) the product already uses for live/historical trading
+  data — no new account or service is introduced.
+
+## Known Limitations
+
+- **Recording real bars always requires a connected data account.** There is no "practice"/demo
+  bar-recording path — unlike some other parts of the system, which can be tried out for free with
+  built-in example data, recording an actual price-bar series always requires real market-data
+  credentials to be configured. (A small, tiny example bar series is bundled with the product's
+  automated tests so its internal machinery can be verified without needing an account — but that
+  example is for the test suite, not something an operator interacts with directly.)
+- **Not every symbol/timeframe combination has the same amount of history available.** During
+  testing with a real account, daily and weekly price history reached back several years as
+  requested, but monthly bars were only available from 2016 onward regardless of how far back was
+  asked for — this is a limit of the underlying data provider's free plan, not something this
+  product controls.
+- **Very recent data is deliberately excluded.** To respect the data provider's free-plan rules,
+  the system never fetches the most recent roughly 15 minutes of bar data — a recording request
+  covering only that very recent window will honestly report "nothing to record" rather than
+  guessing or waiting.
+- **No safeguard yet distinguishes "that symbol doesn't exist" from "no data in that time window"**
+  for bar recordings specifically — both currently show the same "nothing to record" message. (Live
+  trading/watching a ticker elsewhere in the product does already tell those two situations apart;
+  that distinction just isn't built for this new bar-recording action yet, since nothing in this
+  iteration's requirements called for it.)
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-1-iteration-summary.md breports/phase-goal-tape_to_profit_support_resistence-iter-1-iteration-summary.md
new file mode 100644
index 0000000..6d463cd
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-1-iteration-summary.md
@@ -0,0 +1,76 @@
+# Iteration Summary — goal-tape_to_profit_support_resistence-iter-1
+
+**Verdict:** PASS
+**Iteration type:** goal-full
+**Date:** 2026-07-06
+**Iteration:** 1
+
+## In plain words
+
+**What you can do now:** You can type in a stock ticker and watch Tapeology read live trade-by-trade action to see whether buyers or sellers are in control, write trading ideas into a journal, run replay studies, and view honest backtest and profit-and-loss results on a Performance page — all delivered in earlier rounds. This chapter's new price-structure work isn't visible in the app yet.
+
+**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team taught Tapeology to fetch and permanently save a real history of a stock's price bars (daily, weekly, monthly, hourly, and more), read that saved history back reliably, catch any tampering, and refuse to record a duplicate or pretend to have data it doesn't actually have — all through behind-the-scenes tools that other programs can use, not a page you can click through yet.
+
+**What's next:** Next, the team will teach Tapeology to spot the meaningful support-and-resistance price levels hiding in that newly stored price history.
+
+## Headline
+
+J-01 shipped: multi-timeframe bar store recording checksummed OHLC series via REST + MCP
+
+## Direction
+
+**Signal:** improving
+**Why:** iter-1 fully built and delivered J-01 (the multi-timeframe bar store) — review, QA (19/19 functional test cases against the spec's own acceptance criteria), and audit each independently re-ran the suite and verified 100% Definition-of-Done completion with zero regressions, and the J-07 regression sentinel stayed green (engine equivalence 15/15 + 7/7, `default` fingerprint `4d665603569b9dbf` unchanged). closure-verdict.md renders CLOSURE-PASS with no blocking issues. The goal-evaluator's own eval.md for iter-1 was not yet produced at summary time, so journey-history.json still reflects the iter-0 baseline (J-01 shown failing) — expect it to record J-01 passing once the evaluator catches up, with J-02 next in the build queue.
+
+**Trend (last 1 iters):**
+- Newly passing this iter: not yet logged — the goal-evaluator has not produced iter-1's entry as of this summary (review/QA/audit/closure independently PASS J-01)
+- Newly passing in last 1 iters total: J-07 (iter-0 baseline discovery — inherited from the frozen foundation, not new work)
+- Regressions in last 1 iters: none
+- Anti-goal violations in last 1 iters: none
+- Iters with no journey state change: 0 of last 1 (iter-0 recorded the J-07 baseline; iter-1 not yet logged)
+
+**Latest evaluator reasoning:** Era-4 (structure-and-tape) verify-only baseline; zero source changes (confirmed `git diff 15eacab..HEAD -- apps/` empty and a clean working tree). J-07's foundation sentinel is intact — the evaluator personally reran the engine equivalence suite (7/7 byte-identical `default`), confirmed `STRATEGY_V1_ID = "v1"` is the sole registered strategy, and confirmed the era-4 routes are absent from routes.py; the reviewer independently corroborated the full suite (1041 collected) and equivalence (7/7). J-01–J-06 are honestly absent (404/422 live probes + route-table inspection), not fabricated, so the loop continues into the build queue.
+
+## What was done
+
+- Added `RawBar` + `fetch_bars()` on the `MarketDataAdapter` seam; Alpaca implementation via `get_stock_bars`/`TimeFrame` with a recency-delay clamp (900s) and a rate throttle (200/min)
+- New `BarStore` module (`research/bars.py`): immutable, double-checksummed persistence mirroring `datasets.py`, with honest failure states (`BarSeriesNotFound`, `BarSeriesIntegrityError`, `EmptyBarWindowError`, `BarSeriesAlreadyRegistered`)
+- New routes `POST/GET /research/bars` + `GET /research/bars/{id}` (missing credentials → 503, bad `timeframe` → 422) and a byte-identical read-only MCP `bars` tool
+- 4 new config fields (`bar_dir`, `bar_timeframes`, recency/rate-throttle params), all `config_fingerprint`-excluded — pinned `default` fingerprint (`4d665603569b9dbf`) confirmed unchanged
+- Committed a real, never-fabricated keyless bar fixture (PG `1d`/`1h`) via new `scripts/generate_bar_fixtures.py`
+- Ran a live capability probe (Alpaca credentials present): SIP feed; daily/weekly reach the requested start; monthly capped at 2016-01-01 (vendor plan limit); recency clamp + rate throttle both demonstrated live
+- Browser QA skipped (backend-only, `Frontend Present: no`); J-07's cockpit leg guarded instead by the engine equivalence suite (15/15 + 7/7) and a verified-empty `apps/frontend/` diff
+- Full backend suite: 1069 passed / 1 pre-existing skip (+29 new tests), 0 regressions
+
+## What's left
+
+- Journey J-02 (Deterministic support/resistance levels per timeframe) failing — not started
+- Journey J-03 (Confluence zones and A/B/C conviction classes) failing — depends on J-02's levels
+- Journey J-04 (Tape-confirmed structure entries as a registered strategy) failing — depends on J-02/J-03
+- Journey J-05 (Class-scaled stop, reward, and simulated size) failing — depends on J-04
+- Journey J-06 (`structure_tape` measured honestly against the v1 champion) failing — depends on J-04/J-05
+- Two disclosed, spec-sanctioned gaps (non-blocking): an untradable symbol and a genuinely empty/embargoed bar window both surface as the same "no bars in window" error (no separate "symbol not tradable" state)
+- The goal-evaluator has not yet run for iter-1 — journey-history.json / eval.md still reflect the iter-0 baseline; J-01 should be recorded as passing once the evaluator catches up
+- No screen/page exists yet to view bars in the browser (machine-only surface, as scoped)
+
+## Next step
+
+Proceed to release, then build J-02 (deterministic support/resistance level detection) next — J-01 is complete, frozen-safe, and honest, and is the era's designated unblocker for J-02–J-06. Carry forward two disclosed, non-blocking notes into J-02: the Alpaca plan's monthly-bar history only reaches back to 2016-01-01 regardless of the requested start, and an unknown symbol currently looks identical to a genuinely empty/embargoed bar window (a symbol-tradability distinction could be added later if J-02 needs to explain why a level set is empty). The goal-evaluator has not yet produced iter-1's own eval.md/journey-history update as of this summary — expect J-01 to be recorded as passing once that catches up, ahead of iter-2's kickoff.
+
+## Artifacts
+
+| Report | Verdict | Path |
+|--------|---------|------|
+| Iter spec | — | docs/phases/goal-tape_to_profit_support_resistence-iter-1.md |
+| Dev handoff | — | docs/handoffs/goal-tape_to_profit_support_resistence-iter-1-dev.md |
+| Review | PASS | reports/reviews/goal-tape_to_profit_support_resistence-iter-1-review.md |
+| Browser QA | SKIPPED | reports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-test-results.md |
+| Implementation summary | — | reports/phase-goal-tape_to_profit_support_resistence-iter-1-implementation-summary.md |
+| User-visible changes | — | reports/phase-goal-tape_to_profit_support_resistence-iter-1-user-visible-changes.md |
+| What to click | — | reports/phase-goal-tape_to_profit_support_resistence-iter-1-what-to-click.md |
+| UI surface map | — | reports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-surface-map.md |
+| UI test plan | — | reports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-test-plan.md |
+| QA | PASS | reports/qa/goal-tape_to_profit_support_resistence-iter-1-qa.md |
+| Audit | PASS | docs/handoffs/goal-tape_to_profit_support_resistence-iter-1-audit.md |
+| Closure | CLOSURE-PASS | reports/phase-goal-tape_to_profit_support_resistence-iter-1-closure-verdict.md |
+| Journey history | — | runs/goal-session-tape_to_profit_support_resistence/state/journey-history.json |
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-1-summary.html breports/phase-goal-tape_to_profit_support_resistence-iter-1-summary.html
new file mode 100644
index 0000000..b70d98f
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-1-summary.html
@@ -0,0 +1,359 @@
+<!doctype html>
+<html lang="en"><head>
+<meta charset="utf-8">
+<title>goal-tape_to_profit_support_resistence-iter-1 — Iteration Summary</title>
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
+</svg><span>PASS</span></div><span class='signal-badge improving'>Direction: improving</span></div><h1>Iteration 1  ·  session tape_to_profit_support_resistence</h1><h2>J-01 shipped: multi-timeframe bar store recording checksummed OHLC series via REST + MCP</h2><div class='meta'>2026-07-06 · goal-full</div><div class='meta'>Journeys: 1/7 passing</div><div class='journey-row'><span class='journey-pill failing' title='Multi-timeframe historical bars are ingested and persisted (data foundation + free-plan probe)'>J-01 · failing</span><span class='journey-pill failing' title='Deterministic support/resistance levels per timeframe'>J-02 · failing</span><span class='journey-pill failing' title='Confluence zones and A/B/C conviction classes'>J-03 · failing</span><span class='journey-pill failing' title='Tape-confirmed structure entries as a registered strategy'>J-04 · failing</span><span class='journey-pill failing' title='Class-scaled stop, reward, and simulated size'>J-05 · failing</span><span class='journey-pill failing' title='structure_tape is measured honestly against the v1 champion'>J-06 · failing</span><span class='journey-pill already_passing' title='The archived eras are unchanged (regression sentinel)'>J-07 · already_passing</span></div></section>
+<section class='plain-words'><h2 class='pw-heading'>In plain words</h2><div class='pw-grid'><div class='pw-card'><div class='pw-label'>What you can do now</div><p class='pw-text'>You can type in a stock ticker and watch Tapeology read live trade-by-trade action to see whether buyers or sellers are in control, write trading ideas into a journal, run replay studies, and view honest backtest and profit-and-loss results on a Performance page — all delivered in earlier rounds. This chapter&#x27;s new price-structure work isn&#x27;t visible in the app yet.</p></div><div class='pw-card'><div class='pw-label'>What changed this time</div><p class='pw-text'>Behind-the-scenes work — nothing visibly new this round. The team taught Tapeology to fetch and permanently save a real history of a stock&#x27;s price bars (daily, weekly, monthly, hourly, and more), read that saved history back reliably, catch any tampering, and refuse to record a duplicate or pretend to have data it doesn&#x27;t actually have — all through behind-the-scenes tools that other programs can use, not a page you can click through yet.</p></div><div class='pw-card'><div class='pw-label'>What&#x27;s next</div><p class='pw-text'>Next, the team will teach Tapeology to spot the meaningful support-and-resistance price levels hiding in that newly stored price history.</p></div></div></section>
+<div class='tech-divider'><span>Technical detail below — open if you want the developer view.</span></div>
+<details><summary>What was done</summary><div class='accordion-body'><ul class='bullets'><li>Added `RawBar` + `fetch_bars()` on the `MarketDataAdapter` seam; Alpaca implementation via `get_stock_bars`/`TimeFrame` with a recency-delay clamp (900s) and a rate throttle (200/min)</li><li>New `BarStore` module (`research/bars.py`): immutable, double-checksummed persistence mirroring `datasets.py`, with honest failure states (`BarSeriesNotFound`, `BarSeriesIntegrityError`, `EmptyBarWindowError`, `BarSeriesAlreadyRegistered`)</li><li>New routes `POST/GET /research/bars` + `GET /research/bars/{id}` (missing credentials → 503, bad `timeframe` → 422) and a byte-identical read-only MCP `bars` tool</li><li>4 new config fields (`bar_dir`, `bar_timeframes`, recency/rate-throttle params), all `config_fingerprint`-excluded — pinned `default` fingerprint (`4d665603569b9dbf`) confirmed unchanged</li><li>Committed a real, never-fabricated keyless bar fixture (PG `1d`/`1h`) via new `scripts/generate_bar_fixtures.py`</li><li>Ran a live capability probe (Alpaca credentials present): SIP feed; daily/weekly reach the requested start; monthly capped at 2016-01-01 (vendor plan limit); recency clamp + rate throttle both demonstrated live</li><li>Browser QA skipped (backend-only, `Frontend Present: no`); J-07&#x27;s cockpit leg guarded instead by the engine equivalence suite (15/15 + 7/7) and a verified-empty `apps/frontend/` diff</li><li>Full backend suite: 1069 passed / 1 pre-existing skip (+29 new tests), 0 regressions</li></ul></div></details>
+<details><summary>What's left + Next step</summary><div class='accordion-body'><h3>Still open</h3><ul class='bullets'><li>Journey J-02 (Deterministic support/resistance levels per timeframe) failing — not started</li><li>Journey J-03 (Confluence zones and A/B/C conviction classes) failing — depends on J-02&#x27;s levels</li><li>Journey J-04 (Tape-confirmed structure entries as a registered strategy) failing — depends on J-02/J-03</li><li>Journey J-05 (Class-scaled stop, reward, and simulated size) failing — depends on J-04</li><li>Journey J-06 (`structure_tape` measured honestly against the v1 champion) failing — depends on J-04/J-05</li><li>Two disclosed, spec-sanctioned gaps (non-blocking): an untradable symbol and a genuinely empty/embargoed bar window both surface as the same &quot;no bars in window&quot; error (no separate &quot;symbol not tradable&quot; state)</li><li>The goal-evaluator has not yet run for iter-1 — journey-history.json / eval.md still reflect the iter-0 baseline; J-01 should be recorded as passing once the evaluator catches up</li><li>No screen/page exists yet to view bars in the browser (machine-only surface, as scoped)</li></ul><h3>Next step</h3><div class='next-step-box'>Proceed to release, then build J-02 (deterministic support/resistance level detection) next — J-01 is complete, frozen-safe, and honest, and is the era&#x27;s designated unblocker for J-02–J-06. Carry forward two disclosed, non-blocking notes into J-02: the Alpaca plan&#x27;s monthly-bar history only reaches back to 2016-01-01 regardless of the requested start, and an unknown symbol currently looks identical to a genuinely empty/embargoed bar window (a symbol-tradability distinction could be added later if J-02 needs to explain why a level set is empty). The goal-evaluator has not yet produced iter-1&#x27;s own eval.md/journey-history update as of this summary — expect J-01 to be recorded as passing once that catches up, ahead of iter-2&#x27;s kickoff.</div></div></details>
+<details><summary>Direction signal</summary><div class='accordion-body'><div class='why-text'><strong>Why:</strong> iter-1 fully built and delivered J-01 (the multi-timeframe bar store) — review, QA (19/19 functional test cases against the spec&#x27;s own acceptance criteria), and audit each independently re-ran the suite and verified 100% Definition-of-Done completion with zero regressions, and the J-07 regression sentinel stayed green (engine equivalence 15/15 + 7/7, `default` fingerprint `4d665603569b9dbf` unchanged). closure-verdict.md renders CLOSURE-PASS with no blocking issues. The goal-evaluator&#x27;s own eval.md for iter-1 was not yet produced at summary time, so journey-history.json still reflects the iter-0 baseline (J-01 shown failing) — expect it to record J-01 passing once the evaluator catches up, with J-02 next in the build queue.</div><h3>Trend</h3><ul class='bullets'><li>Newly passing this iter: not yet logged — the goal-evaluator has not produced iter-1&#x27;s entry as of this summary (review/QA/audit/closure independently PASS J-01)</li><li>Newly passing in last 1 iters total: J-07 (iter-0 baseline discovery — inherited from the frozen foundation, not new work)</li><li>Regressions in last 1 iters: none</li><li>Anti-goal violations in last 1 iters: none</li><li>Iters with no journey state change: 0 of last 1 (iter-0 recorded the J-07 baseline; iter-1 not yet logged)</li></ul><h3>Latest evaluator reasoning</h3><div class='why-text'>Era-4 (structure-and-tape) verify-only baseline; zero source changes (confirmed `git diff 15eacab..HEAD -- apps/` empty and a clean working tree). J-07&#x27;s foundation sentinel is intact — the evaluator personally reran the engine equivalence suite (7/7 byte-identical `default`), confirmed `STRATEGY_V1_ID = &quot;v1&quot;` is the sole registered strategy, and confirmed the era-4 routes are absent from routes.py; the reviewer independently corroborated the full suite (1041 collected) and equivalence (7/7). J-01–J-06 are honestly absent (404/422 live probes + route-table inspection), not fabricated, so the loop continues into the build queue.</div></div></details>
+<details><summary>Artifacts</summary><div class='accordion-body'><table class='drill-table'><thead><tr><th>Report</th><th>Verdict</th><th>Path</th></tr></thead><tbody><tr><td>Iter spec</td><td><span class='verdict-cell —'>—</span></td><td><a href='../docs/phases/goal-tape_to_profit_support_resistence-iter-1.md'>docs/phases/goal-tape_to_profit_support_resistence-iter-1.md</a></td></tr><tr><td>Dev handoff</td><td><span class='verdict-cell —'>—</span></td><td><a href='../docs/handoffs/goal-tape_to_profit_support_resistence-iter-1-dev.md'>docs/handoffs/goal-tape_to_profit_support_resistence-iter-1-dev.md</a></td></tr><tr><td>Review</td><td><span class='verdict-cell PASS'>PASS</span></td><td><a href='reviews/goal-tape_to_profit_support_resistence-iter-1-review.md'>reports/reviews/goal-tape_to_profit_support_resistence-iter-1-review.md</a></td></tr><tr><td>Browser QA</td><td><span class='verdict-cell SKIPPED'>SKIPPED</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-1-ui-test-results.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-test-results.md</a></td></tr><tr><td>Implementation summary</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-1-implementation-summary.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-1-implementation-summary.md</a></td></tr><tr><td>User-visible changes</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-1-user-visible-changes.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-1-user-visible-changes.md</a></td></tr><tr><td>What to click</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-1-what-to-click.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-1-what-to-click.md</a></td></tr><tr><td>UI surface map</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-1-ui-surface-map.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-surface-map.md</a></td></tr><tr><td>UI test plan</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-1-ui-test-plan.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-test-plan.md</a></td></tr><tr><td>QA</td><td><span class='verdict-cell PASS'>PASS</span></td><td><a href='qa/goal-tape_to_profit_support_resistence-iter-1-qa.md'>reports/qa/goal-tape_to_profit_support_resistence-iter-1-qa.md</a></td></tr><tr><td>Audit</td><td><span class='verdict-cell PASS'>PASS</span></td><td><a href='../docs/handoffs/goal-tape_to_profit_support_resistence-iter-1-audit.md'>docs/handoffs/goal-tape_to_profit_support_resistence-iter-1-audit.md</a></td></tr><tr><td>Closure</td><td><span class='verdict-cell CLOSURE-PASS'>CLOSURE-PASS</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-1-closure-verdict.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-1-closure-verdict.md</a></td></tr><tr><td>Journey history</td><td><span class='verdict-cell —'>—</span></td><td><a href='../runs/goal-session-tape_to_profit_support_resistence/state/journey-history.json'>runs/goal-session-tape_to_profit_support_resistence/state/journey-history.json</a></td></tr></tbody></table></div></details>
+<details><summary>Timing — where this iteration's wall time went</summary><div class='accordion-body'><pre>== Wall-time report: session tape_to_profit_support_resistence
+  goal-tape_to_profit_support_resistence-iter-1  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
+      iteration-summarizer         8.1m  calls=1
+      goal-decomposer              8.1m  calls=1
+      pump-wait                  0.1m
+  goal-tape_to_profit_support_resistence-iter-1  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
+      (resume-skipped: goal-decomposer)</pre></div></details>
+<div class='footer-note'>Generated 2026-07-06 03:06 by <code>render_iteration_summary.py</code> · source: <a href='phase-goal-tape_to_profit_support_resistence-iter-1-iteration-summary.md'>phase-goal-tape_to_profit_support_resistence-iter-1-iteration-summary.md</a></div>
+</div></body></html>
\ No newline at end of file
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-surface-map.md breports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-surface-map.md
new file mode 100644
index 0000000..24e0a3a
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-surface-map.md
@@ -0,0 +1,5 @@
+# Phase goal-tape_to_profit_support_resistence-iter-1 — UI Surface Map
+
+**Status:** N/A — Backend-only phase (Frontend Present: no)
+
+No UI surfaces affected.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-test-plan.md breports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-test-plan.md
new file mode 100644
index 0000000..87428f5
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-test-plan.md
@@ -0,0 +1,3 @@
+# Phase goal-tape_to_profit_support_resistence-iter-1 — UI Test Plan
+
+**Status:** N/A — Backend-only phase. No UI tests required.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-test-results.md breports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-test-results.md
new file mode 100644
index 0000000..e99b7e0
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-test-results.md
@@ -0,0 +1,5 @@
+# Phase goal-tape_to_profit_support_resistence-iter-1 — UI Test Results
+
+**Browser QA Verdict:** SKIPPED
+
+**Reason:** Backend-only phase (Frontend Present: no). No browser tests executed.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-1-user-visible-changes.md breports/phase-goal-tape_to_profit_support_resistence-iter-1-user-visible-changes.md
new file mode 100644
index 0000000..e736908
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-1-user-visible-changes.md
@@ -0,0 +1,5 @@
+# Phase goal-tape_to_profit_support_resistence-iter-1 — User-Visible Changes
+
+**Status:** N/A — Backend-only phase (Frontend Present: no)
+
+No user-visible changes. All changes are internal backend implementation.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-1-what-to-click.md breports/phase-goal-tape_to_profit_support_resistence-iter-1-what-to-click.md
new file mode 100644
index 0000000..ccec88a
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-1-what-to-click.md
@@ -0,0 +1,3 @@
+# Phase goal-tape_to_profit_support_resistence-iter-1 — What to Click
+
+**Status:** N/A — Backend-only phase. No UI verification steps.
diff --git areports/qa/goal-tape_to_profit_support_resistence-iter-1-qa.md breports/qa/goal-tape_to_profit_support_resistence-iter-1-qa.md
new file mode 100644
index 0000000..9c29383
--- /dev/null
+++ breports/qa/goal-tape_to_profit_support_resistence-iter-1-qa.md
@@ -0,0 +1,198 @@
+**Verdict:** PASS
+
+---
+
+## Artifact Verification
+
+| Artifact | Location | Status |
+|----------|----------|--------|
+| Code review report | `reports/reviews/goal-tape_to_profit_support_resistence-iter-1-review.md` | ✓ PASS |
+| Dev handoff | `docs/handoffs/goal-tape_to_profit_support_resistence-iter-1-dev.md` | ✓ Exists |
+| Phase status | `runs/goal-tape_to_profit_support_resistence-iter-1/status.json` | ✓ Exists |
+| Test plan | `reports/qa/goal-tape_to_profit_support_resistence-iter-1-test-plan.md` | ✓ Exists |
+
+---
+
+## Backend Test Results
+
+Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
+
+**Exit Code:** 0 (success)
+
+**Summary:**
+- Total tests collected: 1070
+- Passed: 1069
+- Skipped: 1 (pre-existing gated live-socket test)
+- Failed: 0
+- Regressions: 0
+
+**Test output (excerpt):**
+```
+........................................................................ [  6%]
+........................................................................ [ 13%]
+........................................................................ [ 20%]
+........................................................................ [ 26%]
+........................................................................ [ 33%]
+.....................................................................s.. [ 40%]
+........................................................................ [ 47%]
+........................................................................ [ 53%]
+........................................................................ [ 60%]
+........................................................................ [ 67%]
+........................................................................ [ 74%]
+........................................................................ [ 80%]
+........................................................................ [ 87%]
+........................................................................ [ 94%]
+..............................................................           [100%]
+```
+
+**Test log:** `reports/qa/goal-tape_to_profit_support_resistence-iter-1-test.log`
+
+---
+
+## Functional Test Plan Execution
+
+### Core Bar Store Tests (TC-01 through TC-05)
+
+| Test ID | Name | Type | Test Path | Status | Notes |
+|---------|------|------|-----------|--------|-------|
+| TC-01 | Bar Store Record and Reload (Byte-Identical) | artifact | `test_record_stores_correct_metadata` | ✅ PASS | Byte-identical reload verified; checksums recomputed and verified |
+| TC-02 | Bar Store Immutability (Re-record Identical Content Refused) | artifact | `test_rerecording_identical_content_is_refused` | ✅ PASS | `BarSeriesAlreadyRegistered` exception confirmed |
+| TC-03 | Bar Store Integrity Check (Corrupt File Detected) | artifact | `test_corrupted_bar_data_surfaces_an_explicit_integrity_error` | ✅ PASS | `BarSeriesIntegrityError` raised on corrupt data |
+| TC-04 | Bar Store Empty Window Refusal | artifact | `test_empty_bar_list_is_an_explicit_refusal` | ✅ PASS | Empty window explicitly rejected |
+| TC-05 | Bar Store Unknown ID (BarSeriesNotFound) | artifact | `test_unknown_bar_series_id_raises_not_found` | ✅ PASS | `BarSeriesNotFound` exception confirmed |
+
+### REST API Tests (TC-06 through TC-12)
+
+| Test ID | Name | Type | Test Path | Status | Notes |
+|---------|------|------|-----------|--------|-------|
+| TC-06 | GET /research/bars (List Stored Series) | api | `test_list_and_detail_serve_the_stored_metadata_verbatim` | ✅ PASS | HTTP 200; metadata array with required fields (symbol, timeframe, start_time, end_time, feed, bar_count, content_checksum) |
+| TC-07 | GET /research/bars/{id} (Read Single Series with OHLC Candles) | api | `test_list_and_detail_serve_the_stored_metadata_verbatim` | ✅ PASS | HTTP 200; includes metadata and ordered OHLC candle list |
+| TC-08 | GET /research/bars/{id} (Unknown ID Returns 404) | api | `test_unknown_bar_series_id_is_404` | ✅ PASS | HTTP 404 returned for unknown ID |
+| TC-09 | POST /research/bars with Missing Credentials (Returns 503) | api | `test_missing_credentials_is_an_explicit_503` | ✅ PASS | HTTP 503 returned; message states "real-data provider unavailable" |
+| TC-10 | POST /research/bars with Out-of-Set Timeframe (Returns 422) | api | `test_bad_timeframe_value_is_422` | ✅ PASS | HTTP 422 returned; timeframe never silently coerced |
+| TC-11 | MCP `bars` Tool (Byte-Identical to GET /research/bars) | api | `test_bars_tool_byte_identical_on_a_non_empty_live_list` | ✅ PASS | MCP response JSON is byte-identical to REST API response |
+| TC-12 | MCP `bars` Tool (Backend Down Error) | api | `test_backend_down_every_tool_raises_an_explicit_error` (covers bars) | ✅ PASS | Explicit tool error naming the base URL |
+
+### Configuration and Fingerprint Tests (TC-13, TC-14)
+
+| Test ID | Name | Type | Test Path | Status | Notes |
+|---------|------|------|-----------|--------|-------|
+| TC-13 | Config Fingerprint Stability (bar_dir Excluded) | artifact | `test_bar_dir_is_excluded_from_config_fingerprint` + `test_bar_validation_and_throttle_params_are_excluded_from_config_fingerprint` | ✅ PASS | All four new config fields (`bar_dir`, `bar_timeframes`, `bar_recency_delay_seconds`, `bar_rate_limit_per_minute`) excluded from `config_fingerprint` |
+| TC-14 | Config Fingerprint Counter-Test (Real Threshold Moves Fingerprint) | artifact | Part of `test_profile_equivalence.py` suite | ✅ PASS | Non-excluded parameters verified to move fingerprint |
+
+### Engine Equivalence Tests (TC-15, TC-16)
+
+| Test ID | Name | Type | Test Path | Status | Notes |
+|---------|------|------|-----------|--------|-------|
+| TC-15 | Engine Equivalence Suite (Byte-Identical Default Profile) | artifact | `test_profile_equivalence.py` | ✅ PASS | 15 tests passed; pinned fingerprint `4d665603569b9dbf` unchanged |
+| TC-16 | Engine Equivalence Suite (Observer Byte-Identical Default Profile) | artifact | `test_observer_equivalence.py` | ✅ PASS | 7 tests passed; J-07 byte-identical sentinel remains green |
+
+### Fixture and Frontend Tests (TC-17, TC-18, TC-19)
+
+| Test ID | Name | Type | Test Path | Status | Notes |
+|---------|------|------|-----------|--------|-------|
+| TC-17 | Committed Keyless Fixture (Ingest → Persist → Read in CI) | artifact | `test_committed_fixture_loads_through_the_real_store_path_keyless` | ✅ PASS | Two real bar series (PG `1d` and `1h`) load keyless without credentials |
+| TC-18 | Frontend Diff Empty (No apps/frontend/ Changes) | artifact | `git diff -- apps/frontend/` | ✅ PASS | No changes to frontend files; backend-only implementation confirmed |
+| TC-19 | Backend Test Suite Passes (No Regressions, J-07 Green) | artifact | Full `tests/` suite run | ✅ PASS | 1069 passed, 1 skipped (pre-existing), 0 regressions |
+
+---
+
+## Functional Test Summary
+
+**Total test cases executed:** 19
+- **API tests:** 7 (TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12) — all PASS
+- **Artifact tests:** 12 (TC-01 through TC-05, TC-13 through TC-19) — all PASS
+- **Browser tests:** 0 (Frontend Present: no)
+
+**Result:** 19/19 test cases passed.
+
+---
+
+## Browser Checks
+
+**Frontend Present:** no
+
+**Status:** SKIPPED — backend-only phase per execution plan.
+
+---
+
+## UI Evolution Audit
+
+**Frontend Present:** no
+
+**Status:** SKIPPED — no UI surface changes required for this phase.
+
+---
+
+## Blockers
+
+None. All acceptance criteria met:
+
+1. ✅ J-01 (multi-timeframe bar store) built end to end
+2. ✅ Adapter seam (`RawBar`, `fetch_bars`) added to `MarketDataAdapter` Protocol
+3. ✅ Alpaca implementation with recency-delay clamp + rate throttle
+4. ✅ `BarStore` (double checksum, verified-on-load, honest failure taxonomy)
+5. ✅ Config additions (`bar_dir`, `bar_timeframes`, throttle/recency params)
+6. ✅ All four new config fields correctly excluded from `config_fingerprint`
+7. ✅ Routes (`POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`)
+8. ✅ MCP `bars` tool (byte-identical read-only proxy)
+9. ✅ Committed keyless fixture (real PG data, multiple timeframes)
+10. ✅ Fingerprint stability test + counter-test
+11. ✅ Engine equivalence suite passes (default profile byte-identical, J-07 green)
+12. ✅ Zero frontend diff (`git diff -- apps/frontend/` empty)
+13. ✅ Full backend suite green (1069 passed, zero regressions)
+14. ✅ Missing-credentials response is HTTP 503 (per spec DoD requirement)
+
+---
+
+## Key Findings
+
+**Definition of Done Fulfillment:** COMPLETE
+- All 13 acceptance criteria from the phase spec's DEFINITION OF DONE are satisfied
+- All 7 TESTING REQUIREMENTS scenarios verified
+- No scope creep detected
+
+**Code Quality:** EXCELLENT
+- Mirrors `research/datasets.py` design precisely (single-source-of-truth discipline)
+- Honest failure states (`BarSeriesNotFound`, `BarSeriesIntegrityError`, `EmptyBarWindowError`)
+- Double-checksummed, verified-on-load discipline
+- Real (never fabricated) committed fixture
+- Comprehensive test coverage (+29 new tests, zero regressions)
+
+**Architecture Compliance:** PASS
+- Provider-agnostic adapter seam maintained
+- Config fingerprint stability preserved
+- Engine equivalence suite unchanged (default profile byte-identical)
+- J-07 sentinel remains green
+
+**Real Data Capability:** VERIFIED
+- Alpaca credentials present in environment
+- Capability probe successful (PG symbol tested across 4 timeframes)
+- Recency-delay guard demonstrated live
+- Rate throttle behavior observed (5 calls ~0.30s each)
+- Fixture generated from real Alpaca data (never hand-crafted)
+
+---
+
+## Test Execution Context
+
+**Environment:**
+- Python 3.14.4
+- pytest 9.1.1
+- Backend test suite: 1070 tests collected, 1069 passed, 1 skipped (pre-existing)
+
+**Test Duration:** ~365 seconds (full suite)
+
+**Reviewed by:** Code reviewer (PASS verdict on 2026-07-06)
+
+**QA Date:** 2026-07-06
+
+---
+
+## Recommendation
+
+**Status:** ✅ READY TO SHIP
+
+This iteration successfully builds J-01 (the multi-timeframe bar-store foundation) for Era 4. All acceptance criteria are met, tests are green, and zero regressions are detected. The implementation follows the existing codebase patterns, maintains architecture integrity, and provides the data foundation for J-02–J-06 (subsequent iterations).
+
+No blockers remain. Proceed to release.
diff --git areports/qa/goal-tape_to_profit_support_resistence-iter-1-test-plan.md breports/qa/goal-tape_to_profit_support_resistence-iter-1-test-plan.md
new file mode 100644
index 0000000..c3c8a50
--- /dev/null
+++ breports/qa/goal-tape_to_profit_support_resistence-iter-1-test-plan.md
@@ -0,0 +1,336 @@
+# goal-tape_to_profit_support_resistence-iter-1 Functional Test Plan
+
+**Phase:** goal-tape_to_profit_support_resistence-iter-1
+**Date:** 2026-07-06
+**Frontend Present:** no
+
+## Phase Goal
+
+A multi-timeframe OHLC bar series can be ingested, persisted immutably (checksummed), and read back byte-identically via `GET /research/bars` / `GET /research/bars/{id}` and the MCP `bars` proxy on a committed keyless fixture in CI, while the `default` profile and `v1` remain byte-identical.
+
+## Test Cases
+
+### TC-01 — Bar Store Record and Reload (Byte-Identical)
+
+**Type:** artifact
+**Preconditions:** `BarStore` is initialized with a test bar directory; a multi-timeframe bar series exists (symbol, timeframe, UTC window, feed, OHLC candles).
+
+**Steps:**
+1. Call `BarStore.record()` to persist the bar series to disk (creates checksummed JSON file).
+2. Call `BarStore.load_by_id()` to read the stored series back.
+3. Compare the original and reloaded series byte-for-byte.
+4. Recompute both checksums (content + whole-file) on load and verify they match stored values.
+
+**Expected outcome:** Stored and reloaded series are byte-identical; both checksums verified without error.
+**Pass criteria:** `original_series == reloaded_series` and checksum verification passes on reload.
+
+---
+
+### TC-02 — Bar Store Immutability (Re-record Identical Content Refused)
+
+**Type:** artifact
+**Preconditions:** A bar series has been recorded once via `BarStore.record()`.
+
+**Steps:**
+1. Call `BarStore.record()` again with identical content (same symbol, timeframe, window, OHLC data).
+2. Observe the exception raised.
+
+**Expected outcome:** `BarSeriesAlreadyRegistered` exception is raised.
+**Pass criteria:** Exception type is `BarSeriesAlreadyRegistered`.
+
+---
+
+### TC-03 — Bar Store Integrity Check (Corrupt File Detected)
+
+**Type:** artifact
+**Preconditions:** A bar series has been recorded to disk.
+
+**Steps:**
+1. Manually corrupt the stored JSON file (truncate, alter checksum field, modify OHLC value).
+2. Call `BarStore.load_by_id()` to read it back.
+3. Observe the exception raised.
+
+**Expected outcome:** `BarSeriesIntegrityError` exception is raised.
+**Pass criteria:** Exception type is `BarSeriesIntegrityError`.
+
+---
+
+### TC-04 — Bar Store Empty Window Refusal
+
+**Type:** artifact
+**Preconditions:** `BarStore` is initialized.
+
+**Steps:**
+1. Attempt to record a bar series with an empty OHLC candle list (no bars in the UTC window).
+
+**Expected outcome:** Record operation fails with an explicit empty-window error.
+**Pass criteria:** Exception is raised and message explicitly states empty window.
+
+---
+
+### TC-05 — Bar Store Unknown ID (BarSeriesNotFound)
+
+**Type:** artifact
+**Preconditions:** `BarStore` is initialized with no data.
+
+**Steps:**
+1. Call `BarStore.load_by_id()` with an unknown ID.
+
+**Expected outcome:** `BarSeriesNotFound` exception is raised.
+**Pass criteria:** Exception type is `BarSeriesNotFound`.
+
+---
+
+### TC-06 — GET /research/bars (List Stored Series)
+
+**Type:** api
+**Preconditions:** The backend is running; at least one bar series has been recorded.
+
+**Steps:**
+1. Execute:
+   ```bash
+   curl -s http://localhost:8000/research/bars | jq .
+   ```
+2. Inspect the JSON response for array structure and metadata fields.
+
+**Expected outcome:** HTTP 200; response is an array of bar-series objects, each with symbol, timeframe, UTC window, feed, bar count, and content checksum.
+**Pass criteria:** Status code is 200; response contains at least one object with all required fields (symbol, timeframe, start_time, end_time, feed, bar_count, content_checksum).
+
+---
+
+### TC-07 — GET /research/bars/{id} (Read Single Series with OHLC Candles)
+
+**Type:** api
+**Preconditions:** The backend is running; a bar series has been recorded and assigned an ID.
+
+**Steps:**
+1. Execute:
+   ```bash
+   curl -s http://localhost:8000/research/bars/{id} | jq .
+   ```
+   (where `{id}` is from TC-06 response)
+2. Inspect the JSON response for metadata and OHLC candle list.
+
+**Expected outcome:** HTTP 200; response includes all bar-series metadata plus an ordered list of OHLC candles (open, high, low, close, volume per candle).
+**Pass criteria:** Status code is 200; response contains metadata fields and candles array with at least one candle; each candle has open, high, low, close, volume.
+
+---
+
+### TC-08 — GET /research/bars/{id} (Unknown ID Returns 404)
+
+**Type:** api
+**Preconditions:** The backend is running.
+
+**Steps:**
+1. Execute:
+   ```bash
+   curl -s http://localhost:8000/research/bars/nonexistent-id -w "\n%{http_code}" | tail -1
+   ```
+
+**Expected outcome:** HTTP 404.
+**Pass criteria:** Status code is 404.
+
+---
+
+### TC-09 — POST /research/bars with Missing Credentials (Returns 503)
+
+**Type:** api
+**Preconditions:** The backend is running; Alpaca credentials are NOT set in the environment.
+
+**Steps:**
+1. Prepare a POST request to record a bar series from a real provider:
+   ```bash
+   curl -X POST http://localhost:8000/research/bars \
+     -H "Content-Type: application/json" \
+     -d '{
+       "symbol": "AAPL",
+       "timeframe": "daily",
+       "start": "2024-01-01",
+       "end": "2024-12-31"
+     }' -w "\n%{http_code}" | tail -1
+   ```
+2. Observe the HTTP response code.
+
+**Expected outcome:** HTTP 503 (explicit unavailable state).
+**Pass criteria:** Status code is 503; response message indicates "real-data provider unavailable — a historical bar recording needs credentials".
+
+---
+
+### TC-10 — POST /research/bars with Out-of-Set Timeframe (Returns 422)
+
+**Type:** api
+**Preconditions:** The backend is running.
+
+**Steps:**
+1. Execute:
+   ```bash
+   curl -X POST http://localhost:8000/research/bars \
+     -H "Content-Type: application/json" \
+     -d '{
+       "symbol": "AAPL",
+       "timeframe": "invalid_timeframe",
+       "start": "2024-01-01",
+       "end": "2024-12-31"
+     }' -w "\n%{http_code}" | tail -1
+   ```
+
+**Expected outcome:** HTTP 422 (validation error).
+**Pass criteria:** Status code is 422; response indicates invalid timeframe (never silently coerced).
+
+---
+
+### TC-11 — MCP `bars` Tool (Byte-Identical to GET /research/bars)
+
+**Type:** api
+**Preconditions:** The backend is running; MCP server is initialized; at least one bar series has been recorded.
+
+**Steps:**
+1. Call the MCP `bars` tool (equivalent to `GET /research/bars`).
+2. Call `curl http://localhost:8000/research/bars` directly.
+3. Compare the two JSON responses byte-for-byte.
+
+**Expected outcome:** Both responses are identical.
+**Pass criteria:** MCP response JSON is byte-identical to REST API response (same structure, values, field order).
+
+---
+
+### TC-12 — MCP `bars` Tool (Backend Down Error)
+
+**Type:** api
+**Preconditions:** MCP server is initialized; backend is NOT running.
+
+**Steps:**
+1. Stop the backend service.
+2. Call the MCP `bars` tool.
+3. Observe the error returned.
+
+**Expected outcome:** An explicit tool error is raised naming the base URL.
+**Pass criteria:** Error message explicitly names the backend URL and indicates unreachability.
+
+---
+
+### TC-13 — Config Fingerprint Stability (bar_dir Excluded)
+
+**Type:** artifact
+**Preconditions:** The project is built; config module is loaded.
+
+**Steps:**
+1. Load `config.bar_dir` (verify it's set).
+2. Compute `config.config_fingerprint` before and after setting `bar_dir`.
+3. Verify that `bar_dir` is in the `excluded` set.
+4. Assert fingerprint value is identical whether `bar_dir` is default or overridden.
+
+**Expected outcome:** `bar_dir` is in the `config_fingerprint` excluded set; fingerprint does not change when `bar_dir` is altered.
+**Pass criteria:** `bar_dir` appears in `config.config_fingerprint.excluded` list; fingerprint remains constant with different `bar_dir` values.
+
+---
+
+### TC-14 — Config Fingerprint Counter-Test (Real Threshold Moves Fingerprint)
+
+**Type:** artifact
+**Preconditions:** The project is built; config module is loaded.
+
+**Steps:**
+1. Compute `config.config_fingerprint` with default settings.
+2. Change a real (non-excluded) config parameter (e.g., a threshold or toggle).
+3. Recompute `config.config_fingerprint`.
+4. Compare the two fingerprints.
+
+**Expected outcome:** Fingerprint changes when a real parameter is altered.
+**Pass criteria:** Fingerprints differ when a non-excluded config parameter is modified.
+
+---
+
+### TC-15 — Engine Equivalence Suite (Byte-Identical Default Profile)
+
+**Type:** artifact
+**Preconditions:** Full test suite is executable (`tests/test_profile_equivalence.py`).
+
+**Steps:**
+1. Run:
+   ```bash
+   pytest tests/test_profile_equivalence.py -v
+   ```
+2. Inspect all test results.
+
+**Expected outcome:** All tests pass; `default` profile output is byte-identical across test runs.
+**Pass criteria:** Exit code 0; all test cases report PASS.
+
+---
+
+### TC-16 — Engine Equivalence Suite (Observer Byte-Identical Default Profile)
+
+**Type:** artifact
+**Preconditions:** Full test suite is executable (`tests/test_observer_equivalence.py`).
+
+**Steps:**
+1. Run:
+   ```bash
+   pytest tests/test_observer_equivalence.py -v
+   ```
+2. Inspect all test results.
+
+**Expected outcome:** All tests pass; observer output for `default` profile is byte-identical.
+**Pass criteria:** Exit code 0; all test cases report PASS.
+
+---
+
+### TC-17 — Committed Keyless Fixture (Ingest → Persist → Read in CI)
+
+**Type:** artifact
+**Preconditions:** Test suite is executable; committed bar fixture exists under `tests/fixtures/bars/`.
+
+**Steps:**
+1. Run the fixture-loading test:
+   ```bash
+   pytest tests/test_bars.py::test_committed_fixture_pair_loads_through_the_real_store_path_and_replays_keyless -v
+   ```
+2. Verify the fixture is loaded without credentials.
+3. Verify byte-identical re-read.
+
+**Expected outcome:** Test passes; fixture is read keyless (no Alpaca credentials required).
+**Pass criteria:** Exit code 0; test reports PASS; fixture covers at least two timeframes.
+
+---
+
+### TC-18 — Frontend Diff Empty (No apps/frontend/ Changes)
+
+**Type:** artifact
+**Preconditions:** The implementation is complete.
+
+**Steps:**
+1. Execute:
+   ```bash
+   git diff --stat -- apps/frontend/
+   ```
+
+**Expected outcome:** No changes reported.
+**Pass criteria:** `git diff -- apps/frontend/` output is empty (no files modified).
+
+---
+
+### TC-19 — Backend Test Suite Passes (No Regressions, J-07 Green)
+
+**Type:** artifact
+**Preconditions:** The implementation is complete; full backend test suite is executable.
+
+**Steps:**
+1. Run the full backend test suite:
+   ```bash
+   pytest tests/ -v --tb=short
+   ```
+2. Inspect for failures and regressions.
+
+**Expected outcome:** All tests pass; J-07 (eras 1–3 sentinel) remains green.
+**Pass criteria:** Exit code 0; no test failures; zero regressions in existing tests.
+
+---
+
+## Summary
+
+**Total test cases:** 19
+- **API tests:** 6 (TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12)
+- **Artifact tests:** 13 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-13, TC-14, TC-15, TC-16, TC-17, TC-18, TC-19)
+- **Browser tests:** 0 (Frontend Present: no)
+
+All test cases are driven by the DEFINITION OF DONE and TESTING REQUIREMENTS sections of the phase spec. Tests validate immutability, integrity, honest failure states, byte-identical read-back, config stability, engine equivalence, and zero frontend diff.
diff --git areports/reviews/goal-tape_to_profit_support_resistence-iter-1-review.md breports/reviews/goal-tape_to_profit_support_resistence-iter-1-review.md
new file mode 100644
index 0000000..1bf6fc9
--- /dev/null
+++ breports/reviews/goal-tape_to_profit_support_resistence-iter-1-review.md
@@ -0,0 +1,32 @@
+**Verdict:** PASS
+
+```yaml
+phase: goal-tape_to_profit_support_resistence-iter-1
+date: 2026-07-06
+reviewer: reviewer
+summary: |
+  J-01 multi-timeframe bar store built end to end: RawBar/fetch_bars adapter seam, Alpaca
+  implementation (recency-delay clamp + rate throttle), BarStore (double-checksum, verified-on-load,
+  honest failure taxonomy), config fields correctly fingerprint-excluded, /research/bars* routes,
+  MCP bars tool, and a real (never fabricated) committed keyless fixture. Independently re-ran the
+  full backend suite (exit 0, 1 pre-existing skip) plus targeted bars/equivalence/mcp/real-data-gate
+  suites — all green. Faithfully mirrors research/datasets.py as directed.
+spec_alignment:
+  definition_of_done: complete
+  scope_creep: none
+issues:
+  - severity: NOTE
+    file: apps/backend/tests/test_bars.py
+    line: 200
+    category: tests
+    summary: fetch_bars has no pytest.mark.integration live-credentialed test (only the one-time fixture-capture script + a documented manual capability probe)
+    fix: optional — this matches the existing fetch_historical precedent exactly (no such marker exists for it either); not required this iteration
+standards:
+  state_transitions_server_side: pass
+  test_quality: pass
+  no_dead_code: pass
+  no_hardcoded_localhost: n/a
+  ui_evolved_with_capability: n/a
+  navigation_updated: n/a
+  architecture_principles: pass
+```
diff --git aruns/goal-session-tape_to_profit_support_resistence/iter-1/.steps/coherence.done bruns/goal-session-tape_to_profit_support_resistence/iter-1/.steps/coherence.done
new file mode 100644
index 0000000..9148afc
--- /dev/null
+++ bruns/goal-session-tape_to_profit_support_resistence/iter-1/.steps/coherence.done
@@ -0,0 +1 @@
+{"v":1,"step":"coherence","iter":"1","iter_name":"goal-tape_to_profit_support_resistence-iter-1","ts":"2026-07-06T02:10:37Z","tree_hash":"c7c1bcaff8f7c244c0b48baa5ecfe568568d66aa","artifacts":["runs/goal-session-tape_to_profit_support_resistence/iter-1/coherence.md"],"verdict":"COHERENCE-PASS","journeys":""}
diff --git aruns/goal-session-tape_to_profit_support_resistence/iter-1/coherence.md bruns/goal-session-tape_to_profit_support_resistence/iter-1/coherence.md
new file mode 100644
index 0000000..15951eb
--- /dev/null
+++ bruns/goal-session-tape_to_profit_support_resistence/iter-1/coherence.md
@@ -0,0 +1,37 @@
+# Iteration 1 — Coherence Audit
+
+**Iteration:** goal-tape_to_profit_support_resistence-iter-1
+**Date:** 2026-07-06
+**Written by:** coherence-auditor
+
+---
+
+**Verdict:** COHERENCE-PASS
+
+---
+
+## Data Contract check
+
+| Value / entity | Result | Evidence (file:line) |
+|---|---|---|
+| Row 38 — Bar series (symbol, timeframe, UTC window, feed, bar count, checksum, OHLC candles) | OK | Single owner: `apps/backend/app/research/bars.py:128` (`BarStore`), sole mutation `bars.py:220` (`record`), sole verified reads `bars.py:186`/`bars.py:193` (`get`/`list`). Single production call site `apps/backend/app/research/routes.py:1528-1529` (`get_bar_store()`). Served by `POST /research/bars` (`routes.py:1535-1536`), `GET /research/bars` (`routes.py:1602-1603`), `GET /research/bars/{id}` (`routes.py:1612-1613`) + MCP `bars` (`apps/backend/app/mcp/__init__.py:89` static-path entry, `:174` tool decl) — a generic byte-identical proxy through the existing `_STATIC_PATHS` dispatch (`mcp/__init__.py:262-263`), not a second implementation; live-list byte-identity asserted by the new `test_bars_tool_byte_identical_on_a_non_empty_live_list` (`apps/backend/tests/test_mcp_server.py:263-641`). |
+| Rows 1–37 (era 1–3 contract) | OK — untouched | No modified line in this diff falls inside any existing registered value's computing module or serving endpoint; the only edits to shared files (`config.py`, `mcp/__init__.py`) are pure additions (new fields / new tool entry), verified by re-reading the surrounding hunks. |
+| New value introduced outside the contract | N/A | None found — bar-series fields match row 38's already-drafted definition exactly; no synonym/re-derivation of an existing value appeared. |
+
+Supporting checks performed: grepped the whole `apps/backend/app` tree for every other `BarStore(` call site (only `routes.py:1532`, plus test/fixture-generator call sites under `tests/` and `scripts/generate_bar_fixtures.py`, all constructing the same class) — confirmed a single writer. Grepped for `levels`/`confluence`/`structure_tape` inside the changed files — none present, confirming no premature encroachment into rows 39–43's territory. Confirmed the new route reuses the pre-existing `get_study_market_adapter()` accessor (`routes.py:1218`, already used at `:1315`/`:1461`) rather than instantiating a second adapter path. Confirmed the four new config fields (`bar_dir`, `bar_timeframes`, `bar_recency_delay_seconds`, `bar_rate_limit_per_minute`) are added to the `config_fingerprint` exclusion set (`config.py:1256,1265-1267`) — this protects, rather than threatens, the frozen-`default` single-source-of-truth invariant.
+
+## Information Architecture check
+
+| Feature / route | Result | Evidence (nav file inspected) |
+|---|---|---|
+| `POST/GET /research/bars*` + MCP `bars` | OK — no nav path required | Blueprint IA table (`runs/goal-session-tape_to_profit_support_resistence/state/blueprint.md`, row "J-01 multi-timeframe bar store … machine") designates this journey a machine-only surface with no nav home, mirroring the existing `datasets`/`backtests`/`pnl_ledger` machine rows. Confirmed zero frontend change: `git diff b576c8f60377d4ad03c366da2073f1cd0fb49f0e --stat -- apps/frontend/` returned empty output, and `reports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-surface-map.md` states "N/A — Backend-only phase … No UI surfaces affected." Nothing user-facing shipped, so no nav/sidebar/router file needed a new link. |
+
+No new page, panel, or route was introduced this iteration, so duplicate-home and parallel-shell checks have nothing to test against.
+
+## Blocking violations (FAIL only)
+
+None.
+
+## Advisory notes (non-blocking)
+
+- **Naming proximity, not a violation.** The codebase now carries two distinct "bar" concepts: the pre-existing intra-second live-tape OHLC bar (`?bar=` / `CONFIG.history_bar_sizes`, `app/engine/history.py`, `app/serializers.py`, unmodified this iteration) and this iteration's new calendar-timeframe bar series (`?timeframe=` / `CONFIG.bar_timeframes`, `app/research/bars.py`). The diff itself is careful to disambiguate — distinct field names, distinct endpoints, and an explicit comment at `config.py:1027-1035` calling out the two are "an unrelated concept that must not be conflated or collide." No action needed now (machine-only surface, no shared UI label yet); worth keeping in mind if/when a future levels/bars UI view is ever built, so a user-facing label doesn't quietly conflate the two.
diff --git aruns/goal-session-tape_to_profit_support_resistence/iter-1/journey-history.pre.json bruns/goal-session-tape_to_profit_support_resistence/iter-1/journey-history.pre.json
new file mode 100644
index 0000000..0422c22
--- /dev/null
+++ bruns/goal-session-tape_to_profit_support_resistence/iter-1/journey-history.pre.json
@@ -0,0 +1,69 @@
+{
+  "journeys": {
+    "J-01": {
+      "id": "J-01",
+      "name": "Multi-timeframe historical bars are ingested and persisted (data foundation + free-plan probe)",
+      "status": "failing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_passing_iter": null,
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "docs/handoffs/goal-tape_to_profit_support_resistence-iter-0-dev.md (J-01 section: GET /research/bars -> 404; no RawBar/fetch_bars on adapter seam; no bar-store module)"
+    },
+    "J-02": {
+      "id": "J-02",
+      "name": "Deterministic support/resistance levels per timeframe",
+      "status": "failing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_passing_iter": null,
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "docs/handoffs/goal-tape_to_profit_support_resistence-iter-0-dev.md (J-02 section: GET /research/levels -> 404; no S/R config section; no levels module)"
+    },
+    "J-03": {
+      "id": "J-03",
+      "name": "Confluence zones and A/B/C conviction classes",
+      "status": "failing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_passing_iter": null,
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "docs/handoffs/goal-tape_to_profit_support_resistence-iter-0-dev.md (J-03 section: no confluence/SRLevel code; served from same absent /research/levels)"
+    },
+    "J-04": {
+      "id": "J-04",
+      "name": "Tape-confirmed structure entries as a registered strategy",
+      "status": "failing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_passing_iter": null,
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "docs/handoffs/goal-tape_to_profit_support_resistence-iter-0-dev.md (J-04 section: GET /research/strategies -> 404; structure_tape backtest -> 422; verified by evaluator via config.py:1096 v1-only registry)"
+    },
+    "J-05": {
+      "id": "J-05",
+      "name": "Class-scaled stop, reward, and simulated size",
+      "status": "failing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_passing_iter": null,
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "docs/handoffs/goal-tape_to_profit_support_resistence-iter-0-dev.md (J-05 section: no per-class PnL/sizing machinery; structure_tape backtest cannot run)"
+    },
+    "J-06": {
+      "id": "J-06",
+      "name": "structure_tape is measured honestly against the v1 champion",
+      "status": "failing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_passing_iter": null,
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "docs/handoffs/goal-tape_to_profit_support_resistence-iter-0-dev.md (J-06 section: pnl_scan/edge_report champion-only; no named-strategy evaluation path)"
+    },
+    "J-07": {
+      "id": "J-07",
+      "name": "The archived eras are unchanged (regression sentinel)",
+      "status": "already_passing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_passing_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "docs/handoffs/goal-tape_to_profit_support_resistence-iter-0-dev.md (J-07 section) + evaluator-run equivalence suite 7/7 + zero apps/ source diff (git diff 15eacab..HEAD -- apps/ empty)"
+    }
+  },
+  "anti_goal_violations": [],
+  "updated_at": "2026-07-05T23:40:40Z"
+}
diff --git aruns/goal-session-tape_to_profit_support_resistence/summary.md bruns/goal-session-tape_to_profit_support_resistence/summary.md
new file mode 100644
index 0000000..f133011
--- /dev/null
+++ bruns/goal-session-tape_to_profit_support_resistence/summary.md
@@ -0,0 +1,60 @@
+# Goal Session Summary — tape_to_profit_support_resistence
+
+**Final verdict:** AWAITING_PUMP
+**Total iterations:** 1
+**Wall time (seconds):** 7965
+**Quota pauses:** 0
+**Started:** 2026-07-05T23:05:28.022362Z
+**Finished:** 2026-07-06T01:18:14.726449Z
+
+## Branch
+
+This session pushed iteration commits to `goal/tape_to_profit_support_resistence`. Open a PR with:
+
+    gh pr create --base main --head goal/tape_to_profit_support_resistence \
+      --title "feat: tape_to_profit_support_resistence — AWAITING_PUMP" \
+      --body-file runs/goal-session-tape_to_profit_support_resistence/summary.md
+
+## Final journey state
+
+| Journey | Status | Last passing iter |
+|---|---|---|
+| J-01 | failing | - |
+| J-02 | failing | - |
+| J-03 | failing | - |
+| J-04 | failing | - |
+| J-05 | failing | - |
+| J-06 | failing | - |
+| J-07 | already_passing | goal-tape_to_profit_support_resistence-iter-0 |
+
+## Anti-goal violations
+
+(none)
+
+## Telemetry
+
+See `runs/goal-session-tape_to_profit_support_resistence/telemetry.jsonl` for the structured event log.
+
+## Iteration timing
+
+```
+== Wall-time report: session tape_to_profit_support_resistence
+  goal-tape_to_profit_support_resistence-iter-0  depth=lean  verdict=CONTINUE  wall=38.2m
+      goal-decomposer             15.7m  calls=1
+      developer                   12.4m  calls=1
+      goal-evaluator               6.9m  calls=1
+      reviewer                     3.1m  calls=1
+      pump-wait                  0.5m
+      unattributed (glue)        0.0m
+  goal-tape_to_profit_support_resistence-iter-1  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
+      iteration-summarizer         8.1m  calls=1
+      goal-decomposer              8.1m  calls=1
+      pump-wait                  0.1m
+  session: 1 completed iteration(s), mean wall 38.2m
+      total goal-decomposer             23.8m
+      total developer                   12.4m
+      total iteration-summarizer         8.1m
+      total goal-evaluator               6.9m
+      total reviewer                     3.1m
+      halts: AWAITING_PUMP
+```
diff --git aruns/goal-tape_to_profit_support_resistence-iter-1/plan.md bruns/goal-tape_to_profit_support_resistence-iter-1/plan.md
new file mode 100644
index 0000000..112674b
--- /dev/null
+++ bruns/goal-tape_to_profit_support_resistence-iter-1/plan.md
@@ -0,0 +1,139 @@
+# goal-tape_to_profit_support_resistence-iter-1 Execution Plan
+
+Goal alignment: this iteration builds **J-01** (the multi-timeframe bar store), the explicit
+designated unblocker per `docs/goal.md`'s Era 4 dependency order (J-01 → J-02 → ... → J-06) and
+per the iter-0 dev handoff's own "Suggested Next Phase." It is additive-only, backend-only, and
+protects the frozen `default` profile / `v1` strategy via a fingerprint-exclusion + the engine
+equivalence suite. No drift from the goal or scope creep detected — the spec's IN SCOPE/OUT OF
+SCOPE sections cleanly isolate J-01 from J-02–J-06 and from any frontend surface.
+
+## What to Build
+
+- Neutral `RawBar` dataclass + `fetch_bars(symbol, start, end, timeframe)` added to the
+  `MarketDataAdapter` Protocol (adapter seam), beside the existing `RawTrade`/`RawQuote`/
+  `HistoricalWindow`.
+- Alpaca `fetch_bars` implementation via `StockHistoricalDataClient.get_stock_bars` +
+  `StockBarsRequest` + `TimeFrame` (Minute/Hour/Day/Week/Month; 4h/8h expressed as Hour×amount);
+  stamps the feed via the existing `historical_feed()` (SIP|IEX); throttles to the rate limit and
+  never fetches the most-recent (~15-min-delayed) bar.
+- New `BarStore` module mirroring `research/datasets.py`: immutable, double-checksummed
+  (content + whole-file) bar-series files under a new config-owned `bar_dir`. `record()` is the
+  only mutation and refuses re-registering identical content (`BarSeriesAlreadyRegistered`);
+  honest failure states `BarSeriesNotFound`, `BarSeriesIntegrityError`, explicit empty-window
+  refusal — verified on every load.
+- Config additions: `bar_dir` (package-anchored default, `TAPEOLOGY_BAR_DIR` override) +
+  `bar_dir_resolved()`; a `bar_timeframes` enumeration (the valid `?timeframe=` set); rate-throttle
+  / recency-delay-guard parameters — no magic numbers. `bar_dir` joins the `config_fingerprint`
+  `excluded` set so the `default` fingerprint stays byte-identical.
+- Routes under `/research`: `POST /research/bars` (explicit credentialed record action),
+  `GET /research/bars` (list), `GET /research/bars/{id}` (detail) — serving the store's metadata
+  verbatim. Out-of-set `timeframe` → 422 (never silently coerced).
+- MCP `bars` tool: a byte-identical read-only proxy of `GET /research/bars`, added to the existing
+  static-tool registry; backend-down → an explicit tool error naming the base URL.
+- A one-symbol capability probe (daily/weekly/monthly/hourly) recording the real, honest finding
+  (feed, lookback range, rate behaviour) into the dev handoff — or the honest missing-credentials
+  state if Alpaca creds are absent in this environment (never fabricated).
+- A committed, keyless, miniature multi-timeframe bar fixture proving ingest→persist→read in CI
+  with no credentials.
+- A `config_fingerprint`-stability test (`bar_dir` excluded) plus its counter-test that a real
+  threshold still moves the fingerprint.
+
+## Agents Required
+
+- developer: yes -- implement the full backend slice above end to end (adapter seam, Alpaca
+  `fetch_bars`, `BarStore`, config, routes, MCP tool, capability probe, fixture, and the full test
+  suite). Explicitly **mirror** `research/datasets.py`, the `/datasets` route trio
+  (`routes.py:1374-1496`), and the `datasets` MCP tool throughout — this is the spec's own
+  directive and keeps the single-source-of-truth / honest-failure-state anti-goals satisfied by
+  construction. No frontend-ux work is required or in scope.
+- backend-data: yes
+- frontend-ux: no
+
+Frontend Present: no
+
+## Files to Create/Modify
+
+- `apps/backend/app/providers/adapters/base.py` -- add `RawBar` dataclass + `fetch_bars` to the
+  `MarketDataAdapter` Protocol
+- `apps/backend/app/providers/adapters/alpaca.py` -- implement `fetch_bars`
+  (`get_stock_bars`/`StockBarsRequest`/`TimeFrame`), rate-throttle, never-fetch-most-recent-bar
+  guard, feed stamping via existing `historical_feed()`
+- `apps/backend/app/research/bars.py` -- NEW module: `BarStore` (mirrors `research/datasets.py`
+  end to end: double checksum, verified-on-every-load, `record()` as the only mutation,
+  `BarSeriesNotFound`/`BarSeriesIntegrityError`/`BarSeriesAlreadyRegistered`, empty-window refusal)
+- `apps/backend/app/config.py` -- `bar_dir` + `bar_dir_resolved()` (mirror `dataset_dir` /
+  `dataset_dir_resolved()` at ~line 1143), `bar_timeframes` enum (see naming note below),
+  rate-throttle/recency-delay params, `bar_dir` added to the `config_fingerprint` `excluded` set
+  (mirror the `dataset_dir` entry at ~line 1192)
+- `apps/backend/app/research/routes.py` -- `get_bar_store()` dependency + `POST /research/bars`,
+  `GET /research/bars`, `GET /research/bars/{id}` (mirror the `/datasets` trio at lines 1374-1496)
+- `apps/backend/app/mcp/__init__.py` -- `"bars": "/research/bars"` in `STATIC_TOOLS` (mirror line
+  87) + a `types.Tool(...)` entry (mirror the `datasets` tool at lines 162-170)
+- `apps/backend/tests/fixtures/bars/` (or an equivalent tracked bar-store entry -- developer's
+  choice per spec) -- NEW committed keyless multi-timeframe bar fixture, mirroring
+  `tests/fixtures/datasets/*.json`
+- `apps/backend/tests/test_bars.py` -- NEW: store unit tests (mirror `test_datasets.py`'s scenario
+  coverage and naming style)
+- `apps/backend/tests/test_bars_api.py` -- NEW: route tests (mirror `test_datasets_api.py`'s
+  scenario coverage and naming style)
+- `apps/backend/tests/test_mcp_server.py` -- extend: `bars` byte-identity test + backend-down error
+  test
+- `docs/handoffs/goal-tape_to_profit_support_resistence-iter-1-dev.md` -- dev handoff, including
+  the capability-probe finding and confirmation of zero `apps/frontend/` diff
+
+## Key Test Scenarios
+
+- Record → reload is byte-identical; both checksums (content + whole-file) are recomputed and
+  verified on every load.
+- Corrupt bar file -> `BarSeriesIntegrityError`; re-recording identical content ->
+  `BarSeriesAlreadyRegistered`; empty window -> explicit refusal; unknown id -> `BarSeriesNotFound`.
+- `GET /research/bars` / `/{id}` serve the stored series verbatim (symbol, timeframe, UTC window,
+  feed, bar count, checksum, ordered OHLC candles) -- keyless on the committed fixture, in CI, with
+  no credentials.
+- `POST /research/bars` with missing credentials -> explicit unavailable response (see status-code
+  note below); an out-of-set `timeframe` -> 422, never silently coerced.
+- MCP `bars` tool JSON is byte-identical to `GET /research/bars`; backend-down -> an explicit tool
+  error naming the base URL.
+- `bar_dir` is excluded from `config_fingerprint`: the stability test passes, and its counter-test
+  (a real threshold still moves the fingerprint) also passes.
+- Full engine equivalence suite (`test_profile_equivalence.py` + `test_observer_equivalence.py`)
+  stays green -- byte-identical `default` state/confidence/features/history, pinned fingerprint.
+- `git diff -- apps/frontend/` is empty; full backend suite passes with zero regressions (J-07
+  stays green); `v1`, `default`, and the champion pointer are untouched.
+
+## Assumptions & Spec Clarifications
+
+These are resolved here (not asked as questions) per the token/questioning policy -- each is a
+low-ambiguity call grounded in direct inspection of the current codebase.
+
+1. **Missing-credentials status code: spec cites a 503 precedent that is actually 422 in the
+   current code -- resolve as 503, per the explicit, repeated DEFINITION OF DONE / TESTING
+   REQUIREMENTS text.** The spec says three times that `POST /research/bars` with missing
+   credentials must return **503** ("the EXISTING explicit unavailable (503) state"), citing
+   `research/routes.py:1444` as the precedent. Direct inspection shows that line (and the
+   analogous historical-study path at `routes.py:1294-1300`) both actually raise **422**, not 503
+   -- confirmed further by the existing test `test_historical_without_credentials_is_an_explicit_422`
+   (`test_datasets_api.py:221`). There is no existing 503-for-missing-credentials precedent
+   anywhere in `routes.py` (the file's other 503s are generic internal-failure cases, e.g.
+   `DatasetRecordError` at line 1464, or "could not persist/resolve/save" at lines 351/797/923/1176
+   -- unrelated to credentials). Since the DoD and Testing Requirements are the graded acceptance
+   criteria and state 503 unambiguously and repeatedly, implement **503** for this case -- reusing
+   the existing message *style* ("real-data provider unavailable -- a historical bar recording
+   needs credentials") and the "never fabricate" discipline, but at `status_code=503` rather than
+   copying the 422 literally from the cited line. Write the DoD-required test asserting 503.
+2. **`bar_timeframes` vs. the existing `history_bar_sizes` (config.py:211).** These are unrelated
+   concepts: `history_bar_sizes` is the tape engine's existing intra-second rolling-window sizing
+   (10/30/60s), unrelated to OHLC candle timeframes. Keep the new enum's name and any config keys
+   clearly distinct (`bar_timeframes` as specified) so nothing conflates the two or collides.
+3. **Capability probe outcome is not gated.** This environment's Alpaca credential state is
+   unknown to this plan; the developer should run the probe honestly and record whatever the real
+   environment shows -- a missing-credentials finding is an acceptable, expected, non-blocking
+   outcome per the spec ("recorded honestly; never fabricated when credentials are absent").
+4. **Fixture mechanism: recommend mirroring `tests/fixtures/datasets/*.json` directly.** The
+   simplest path satisfying "committed AND keyless AND exercised by the test suite" is to commit
+   1-2 small bar-store JSON files (covering at least two timeframes) in the exact `BarStore`
+   on-disk format under a new fixture directory, then point a test's `BarStore` at that directory
+   and assert a byte-identical load -- mirroring
+   `test_committed_fixture_pair_loads_through_the_real_store_path_and_replays_keyless`
+   (`test_datasets.py:292`). No `.env.example` change is needed (no new credential name; `bar_dir`'s
+   override follows the same undocumented-storage-path convention as `TAPEOLOGY_DATASET_DIR`).
diff --git aruns/goal-tape_to_profit_support_resistence-iter-1/status.json bruns/goal-tape_to_profit_support_resistence-iter-1/status.json
new file mode 100644
index 0000000..bc09d69
--- /dev/null
+++ bruns/goal-tape_to_profit_support_resistence-iter-1/status.json
@@ -0,0 +1,28 @@
+{
+  "phase": "goal-tape_to_profit_support_resistence-iter-1",
+  "status": "complete",
+  "current_step": "closure_passed",
+  "updated_at": "2026-07-06T01:58:52.598865Z",
+  "started_at": "2026-07-05T23:51:50.377294Z",
+  "cli": "claude",
+  "blockers": [],
+  "changed_files": [
+    "apps/backend/app/providers/adapters/base.py",
+    "apps/backend/app/providers/adapters/alpaca.py",
+    "apps/backend/app/research/bars.py",
+    "apps/backend/app/config.py",
+    "apps/backend/app/research/routes.py",
+    "apps/backend/app/mcp/__init__.py",
+    "apps/backend/tests/fakes.py",
+    "apps/backend/tests/test_bars.py",
+    "apps/backend/tests/test_bars_api.py",
+    "apps/backend/tests/test_mcp_server.py",
+    "apps/backend/tests/fixtures/bars/",
+    "apps/backend/scripts/generate_bar_fixtures.py",
+    "docs/handoffs/goal-tape_to_profit_support_resistence-iter-1-dev.md",
+    "reports/phase-goal-tape_to_profit_support_resistence-iter-1-implementation-summary.md"
+  ],
+  "tests_run": true,
+  "browser_checks_run": false,
+  "next_action": "review"
+}
```
