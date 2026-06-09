"""Alpaca market-data adapter — the SINGLE module where Alpaca specifics live.

This is the one concrete adapter behind the vendor-neutral ``MarketDataAdapter`` seam, and the
ONLY module permitted to import the ``alpaca-py`` SDK or name "Alpaca". It does four things:

  * ``is_available()`` — credential detection from the ENVIRONMENT ONLY (never committed
    source, never the engine ``Config``); ``True`` iff both key and secret are present.
  * ``fetch_historical()`` — fetch one symbol's REAL trades + quotes for a past window and
    translate them into vendor-neutral ``RawTrade`` / ``RawQuote`` records. Unknown/untradable
    symbol → ``SymbolNotTradable``; a window with no trades → ``NoDataForWindow``. No vendor
    exception type leaks outward.
  * ``search_symbols()`` — read-only tradable-symbol *reference* lookup for the search box
    (symbol + name). This uses Alpaca's asset reference list only; it places/echoes NO orders
    and integrates no execution/brokerage capability (the no-execution anti-goal holds).
  * ``stream_live()`` — open Alpaca's real-time market-data socket
    (``alpaca.data.live.StockDataStream``) for ONE symbol, subscribe to its **trades + quotes**,
    and yield vendor-neutral ``RawTrade`` / ``RawQuote`` records as they arrive. It subscribes to
    market data only — it never calls any order/account/position API — and on cancel/close it
    unsubscribes and **closes the socket** so no vendor connection is leaked.

The SDK is imported lazily inside the methods so the no-credentials / simulated / test paths
never pay its (pandas/numpy) import cost. Blocking network calls are synchronous here; the API
runs them off the event loop (``asyncio.to_thread``) so the watch gate stays responsive.

Vendor responsiveness (J-28/J-29/J-30) lives entirely behind this seam:
  * A **real call-level HTTP deadline** (``_with_http_timeout`` + ``_mapped_vendor_timeout``)
    cuts off a slow/large vendor response at the SDK client's ``requests.Session`` — the true
    bound, distinct from the API's outer ``asyncio.wait_for`` wrapper — surfaced as the neutral
    ``VendorTimeout`` the API maps to ``provider_timeout``.
  * The historical fetch is **fast by design**: trades + quotes are fetched **concurrently**, the
    tradable pre-flight is **folded** (a second round-trip only on an empty result), and a bounded
    **window cache** makes a re-watch of the same (symbol, window, feed) near-instant.
  * ``warm_symbol_universe`` lets the API **warm** the tradable-symbol cache at startup so the
    first search is not a cold stall — through the neutral seam, with no SDK name in ``main.py``.
All of these are performance/honesty properties only — they never reorder, drop, or fabricate a
trade/quote, and a cache hit replays the SAME real window.

Anti-goals served: *no secrets in source* (env-only; names documented with empty values in
``.env.example``), *provider-agnostic engine* (vendor names + SDK confined here), *no fabricated
data* (every failure is an explicit neutral outcome, never a synthesized read), *bounded, honest,
performant vendor calls* (a real HTTP deadline + concurrent/cached/warmed fast paths).
"""

from __future__ import annotations

import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, suppress
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator

from ...config import CONFIG
from .base import (
    HistoricalWindow,
    LiveRecord,
    MarketClock,
    NoDataForWindow,
    RawQuote,
    RawTrade,
    SymbolMatch,
    SymbolNotTradable,
    VendorTimeout,
)

# Environment variable NAMES (never values). Documented with empty values in
# apps/backend/.env.example — the only committable env file.
ENV_API_KEY = "ALPACA_API_KEY"
ENV_API_SECRET = "ALPACA_API_SECRET"
# The market-data feed is configuration, not a secret. Alpaca's free feed is IEX.
ENV_FEED = "ALPACA_FEED"
DEFAULT_FEED = "iex"

# Wall-clock seconds to let the live socket's run loop unwind on teardown before forcing it (an
# operational SDK-close grace period, not an engine/classifier threshold — same kind of named
# operational constant as the feeder's FEED_PACE_SECONDS / the API's WS_PUSH_INTERVAL).
LIVE_TEARDOWN_GRACE_SECONDS = 6.0

# Process-lifetime cache of the (rarely-changing) tradable-symbol universe, so the search box
# does not re-fetch ~14k assets on every keystroke. Warmed once at startup (J-30) via
# ``warm_symbol_universe`` and otherwise populated lazily on first search. This module-level cell
# is the SINGLE owner of the universe — there is no second store.
_ASSET_UNIVERSE: list[SymbolMatch] | None = None

# Bounded in-process cache of fetched REAL historical windows keyed by (symbol, start, end, feed)
# so re-watching the same symbol+window is near-instant (J-29): a cache hit skips the vendor
# round-trip and replays the SAME real ``HistoricalWindow`` (never a fabricated one). Bounded by
# CONFIG.historical_cache_max_entries (LRU) + CONFIG.historical_cache_ttl_seconds (TTL) so memory
# stays flat. Maps key -> (stored_at_monotonic, HistoricalWindow); insertion order = LRU order.
_HISTORICAL_WINDOW_CACHE: "dict[tuple, tuple[float, HistoricalWindow]]" = {}


def _env(name: str) -> str:
    """Return a trimmed environment value, or ``""`` when unset/blank (blank != configured)."""
    value = os.environ.get(name)
    return value.strip() if value else ""


def _to_iso_utc(value) -> str | None:
    """Serialize a (tz-aware) vendor datetime to an ISO-8601 UTC string (``…Z``); ``None`` passes
    through. Alpaca returns tz-aware datetimes, so converting to UTC is unambiguous — an operator
    is never misled about "next open"."""
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@contextmanager
def _mapped_vendor_timeout(detail: str = "market data provider timed out"):
    """Map the vendor SDK's HTTP timeout to the NEUTRAL ``VendorTimeout`` (J-28).

    The real call-level deadline is a ``requests`` timeout on the SDK client session; when it
    fires the SDK raises ``requests.exceptions.Timeout``. We translate it here to a vendor-neutral
    ``VendorTimeout`` so no vendor exception type leaks outside this module (provider-agnostic
    anti-goal) and the API maps it to the existing row-9 ``provider_timeout`` reason. ``detail``
    lets a caller supply a more actionable message for an oversized window. ``requests`` is
    imported lazily so the no-creds / simulated / test paths never pay the import cost.
    """
    try:
        from requests.exceptions import Timeout as _RequestsTimeout
    except Exception:  # requests unavailable for some reason — treat nothing as a timeout
        _RequestsTimeout = ()  # type: ignore[assignment]
    try:
        yield
    except _RequestsTimeout:
        raise VendorTimeout(detail) from None


def _cache_get(key: tuple) -> HistoricalWindow | None:
    """Return a non-expired cached window for ``key`` (refreshing LRU order), else ``None``.

    Honours the TTL (``CONFIG.historical_cache_ttl_seconds``): an expired entry is dropped and
    treated as a miss. A hit is moved to the most-recently-used position so the LRU eviction in
    ``_cache_put`` discards the genuinely coldest window.
    """
    entry = _HISTORICAL_WINDOW_CACHE.get(key)
    if entry is None:
        return None
    stored_at, window = entry
    if (time.monotonic() - stored_at) > CONFIG.historical_cache_ttl_seconds:
        _HISTORICAL_WINDOW_CACHE.pop(key, None)
        return None
    # Refresh recency (move to the end = most-recently-used).
    _HISTORICAL_WINDOW_CACHE.pop(key, None)
    _HISTORICAL_WINDOW_CACHE[key] = (stored_at, window)
    return window


def _cache_put(key: tuple, window: HistoricalWindow) -> None:
    """Store ``window`` for ``key`` under the bounded LRU+TTL cache (J-29).

    Bounded to ``CONFIG.historical_cache_max_entries``: when full, the least-recently-used entry
    (the first key in insertion order) is evicted so memory stays flat. Stores the REAL window
    only — a cache hit later replays the same real trades/quotes (never fabricated)."""
    _HISTORICAL_WINDOW_CACHE.pop(key, None)
    while len(_HISTORICAL_WINDOW_CACHE) >= CONFIG.historical_cache_max_entries:
        oldest = next(iter(_HISTORICAL_WINDOW_CACHE))
        _HISTORICAL_WINDOW_CACHE.pop(oldest, None)
    _HISTORICAL_WINDOW_CACHE[key] = (time.monotonic(), window)


def _clear_caches() -> None:
    """Reset the process-lifetime caches (the window cache + the warmed universe).

    For tests/operators only — production never needs to clear; this keeps test isolation explicit
    rather than reaching into the module globals from the test files."""
    global _ASSET_UNIVERSE
    _ASSET_UNIVERSE = None
    _HISTORICAL_WINDOW_CACHE.clear()


def _split_window(start, end, chunk_seconds: float) -> list[tuple]:
    """Split ``[start, end)`` into bounded contiguous sub-windows of at most ``chunk_seconds`` (J-34).

    Pure and deterministic (no network): returns a list of ``(sub_start, sub_end)`` tuples that
    PARTITION ``[start, end)`` with NO overlap and NO gap (each sub-window's end is the next one's
    start; the last ends exactly at ``end``), so stitching the sub-windows' real prints reconstructs
    the full real window with nothing fabricated, dropped, reordered, or de-duplicated. A window
    at/under ``chunk_seconds`` (or with a non-datetime / non-positive chunk) returns a single
    ``[(start, end)]`` — the prior single-call fast path, unchanged. ``start``/``end`` are the
    tz-aware datetimes the API parsed; arithmetic uses ``timedelta`` so DST/zone correctness is the
    datetimes' own (the API already resolved the exact local instants).
    """
    # Only datetimes can be chunked by timedelta; anything else (e.g. the test fakes that pass
    # strings/None) is fetched as a single call — the split is a fetch optimization, never a
    # correctness dependency.
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        return [(start, end)]
    if chunk_seconds <= 0:
        return [(start, end)]
    span = (end - start).total_seconds()
    if span <= chunk_seconds:
        return [(start, end)]
    step = timedelta(seconds=chunk_seconds)
    ranges: list[tuple] = []
    cursor = start
    while cursor < end:
        nxt = min(cursor + step, end)
        ranges.append((cursor, nxt))
        cursor = nxt
    return ranges


class AlpacaAdapter:
    """The concrete Alpaca adapter (availability, historical fetch, symbol search)."""

    name = "alpaca"

    def is_available(self) -> bool:
        """``True`` only when BOTH the Alpaca key and secret are present (non-blank) in env."""
        return bool(_env(ENV_API_KEY)) and bool(_env(ENV_API_SECRET))

    @property
    def feed(self) -> str:
        """The configured market-data feed (defaults to the free IEX feed)."""
        return _env(ENV_FEED) or DEFAULT_FEED

    # --- Historical fetch ---------------------------------------------------------------

    def fetch_historical(self, symbol: str, start, end) -> HistoricalWindow:
        """Fetch REAL trades + quotes for ``symbol`` over ``[start, end)`` as neutral records.

        FAST BY DESIGN (J-29), HONEST AND BOUNDED (J-28):
          * **Window cache** — a (symbol, start, end, feed) hit returns the SAME real window with
            NO vendor round-trip (near-instant re-watch); never a fabricated window.
          * **One round-trip on success** — the trades+quotes are fetched FIRST (concurrently);
            the tradable/unknown-symbol pre-flight is folded in so it costs a SECOND round-trip
            only when the data comes back empty (to decide unknown-symbol vs. empty-window). A
            successful fetch pays one round-trip's latency, not two.
          * **Concurrent fetch** — trades and quotes are fetched in parallel (total ≈ the slower
            of the two, not their sum). Ordering into the engine timeline is unchanged.
          * **Real call-level deadline** — every SDK HTTP call runs under
            ``CONFIG.vendor_http_timeout_seconds`` (set on the client session); a slow/large
            response is cut off as a neutral ``VendorTimeout`` (no vendor type leaks).

        Honest failures (no fabricated tape): ``SymbolNotTradable`` for an unknown/untradable
        symbol, ``NoDataForWindow`` when a tradable symbol has no trades in the window, and
        ``VendorTimeout`` (mapped to ``provider_timeout`` by the API) when the deadline fires.
        """
        sym = symbol.strip().upper()
        feed = self._data_feed()
        cache_key = (sym, start, end, getattr(feed, "value", str(feed)))

        cached = _cache_get(cache_key)
        if cached is not None:
            return cached  # near-instant re-watch: the SAME real window, no vendor round-trip

        trades, quotes = self._fetch_trades_quotes(sym, start, end, feed)
        if not trades:
            # Folded pre-flight: only on an EMPTY result do we pay a second round-trip to
            # distinguish an unknown/untradable symbol (-> SymbolNotTradable) from a tradable
            # symbol with no prints in the window (-> NoDataForWindow). A successful fetch above
            # already returned after ONE round-trip, so the common path is not penalized.
            self._require_tradable(sym)
            raise NoDataForWindow(sym)
        window = HistoricalWindow(sym, tuple(trades), tuple(quotes))
        _cache_put(cache_key, window)
        return window

    def _require_tradable(self, symbol: str) -> None:
        """Validate the symbol against Alpaca's asset reference; raise neutral on failure.

        Only invoked on the EMPTY-result path now (no longer a pre-flight on the hot path), to
        decide unknown-symbol vs. empty-window. Runs under the real call-level HTTP deadline.
        """
        from alpaca.common.exceptions import APIError
        from alpaca.trading.client import TradingClient

        client = self._with_http_timeout(
            TradingClient(_env(ENV_API_KEY), _env(ENV_API_SECRET), paper=True)
        )
        try:
            with _mapped_vendor_timeout():
                asset = client.get_asset(symbol)
        except APIError as exc:
            if getattr(exc, "status_code", None) == 404:
                raise SymbolNotTradable(symbol) from None
            raise
        if not getattr(asset, "tradable", False):
            raise SymbolNotTradable(symbol)

    def _fetch_trades_quotes(self, symbol: str, start, end, feed):
        """Fetch the window's trades + quotes, CHUNKED for a long span (J-34), CONCURRENT (J-29).

        FAST BY DESIGN, not a longer timeout:
          * **Chunked (J-34)** — a window longer than ``CONFIG.historical_chunk_seconds`` is split
            into bounded contiguous sub-windows (``_split_window``) fetched with BOUNDED concurrency
            (``CONFIG.historical_chunk_max_concurrency``), parallelizing the SDK's otherwise-
            sequential pagination so a multi-hour / Full-RTH window loads within budget instead of
            returning the "very high-volume" error. A window at/under the sub-window size is ONE
            fetch (the prior fast path, unchanged).
          * **Concurrent trades+quotes (J-29)** — within each sub-window the two vendor calls overlap
            (each in its own thread), so a sub-window costs ≈ max(t_trades, t_quotes), not their sum.

        Stitching is correctness-preserving: the sub-windows' real records are concatenated and
        SORTED by epoch (the canonical merge order ``HistoricalProvider`` already relies on), so the
        merged stream is epoch-ordered with NO fabricated, dropped, reordered (beyond the epoch
        sort), or de-duplicated prints — and because the sub-windows partition ``[start, end)`` with
        no overlap/gap, a chunked fetch yields the SAME real records a single fetch would. A timeout
        in any sub-window's call surfaces as the neutral ``VendorTimeout`` (the J-28 backstop).
        """
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockQuotesRequest, StockTradesRequest

        client = self._with_http_timeout(
            StockHistoricalDataClient(_env(ENV_API_KEY), _env(ENV_API_SECRET))
        )

        def _get_trades(sub_start, sub_end):
            with _mapped_vendor_timeout():
                return client.get_stock_trades(
                    StockTradesRequest(
                        symbol_or_symbols=symbol, start=sub_start, end=sub_end, feed=feed
                    )
                )

        def _get_quotes(sub_start, sub_end):
            with _mapped_vendor_timeout():
                return client.get_stock_quotes(
                    StockQuotesRequest(
                        symbol_or_symbols=symbol, start=sub_start, end=sub_end, feed=feed
                    )
                )

        ranges = _split_window(start, end, CONFIG.historical_chunk_seconds)
        trades: list[RawTrade] = []
        quotes: list[RawQuote] = []

        def _fetch_sub(sub_start, sub_end):
            # Each sub-window overlaps its own trades+quotes calls (J-29) in two threads.
            with ThreadPoolExecutor(max_workers=2) as pool:
                t_future = pool.submit(_get_trades, sub_start, sub_end)
                q_future = pool.submit(_get_quotes, sub_start, sub_end)
                return t_future.result(), q_future.result()

        if len(ranges) == 1:
            # Single-call fast path (a short window) — unchanged from the J-29 behavior.
            sub_results = [_fetch_sub(*ranges[0])]
        else:
            # Bounded-concurrency chunked fetch (J-34): at most historical_chunk_max_concurrency
            # sub-windows in flight at once; results collected in submission order so the stitch is
            # deterministic before the canonical epoch sort below.
            max_workers = max(1, CONFIG.historical_chunk_max_concurrency)
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                sub_results = list(pool.map(lambda r: _fetch_sub(*r), ranges))

        for trades_resp, quotes_resp in sub_results:
            trades.extend(
                RawTrade(t.timestamp.timestamp(), float(t.price), int(t.size))
                for t in trades_resp.data.get(symbol, [])
            )
            quotes.extend(
                RawQuote(
                    q.timestamp.timestamp(),
                    float(q.bid_price),
                    float(q.ask_price),
                    int(q.bid_size),
                    int(q.ask_size),
                )
                for q in quotes_resp.data.get(symbol, [])
            )

        # Stitch in epoch order (stable sort preserves intra-epoch input order). This is the SAME
        # canonical ordering HistoricalProvider applies; doing it here keeps a chunked fetch's merged
        # stream identical to a single fetch's — no fabricated/dropped/reordered/de-duplicated print.
        trades.sort(key=lambda t: t.epoch)
        quotes.sort(key=lambda q: q.epoch)
        return trades, quotes

    def _data_feed(self):
        from alpaca.data.enums import DataFeed

        try:
            return DataFeed(self.feed)
        except ValueError:
            return DataFeed.IEX

    @staticmethod
    def _with_http_timeout(client):
        """Apply the REAL call-level HTTP deadline to a constructed SDK client (J-28).

        The pinned alpaca-py 0.43.4 exposes NO per-request ``timeout`` kwarg on its client
        constructors; the base ``RESTClient`` builds ``self._session = requests.Session()`` and
        calls ``self._session.request(method, url, **opts)`` with no ``timeout`` in ``opts``. We
        therefore set a DEFAULT timeout at the ``requests.Session`` layer by wrapping the session's
        ``request`` to inject ``timeout=CONFIG.vendor_http_timeout_seconds`` whenever the caller
        (the SDK) does not pass one. This is the real call-level bound: the client itself aborts a
        slow/large/CPU-bound response (raising ``requests.exceptions.Timeout``), which we map to a
        neutral ``VendorTimeout`` — distinct from the API's outer ``asyncio.wait_for`` wrapper that
        only abandons the worker thread. The SDK stays confined to this module (no vendor specifics
        leak). Idempotent and defensive: if the SDK internals ever differ we leave the client
        unchanged (the outer wrapper still bounds the call) rather than guessing.
        """
        session = getattr(client, "_session", None)
        if session is None or not hasattr(session, "request"):
            return client  # SDK internals differ — fall back to the outer wrapper bound
        if getattr(session, "_tapeology_timeout_wrapped", False):
            return client  # already wrapped (idempotent)
        original_request = session.request
        deadline = CONFIG.vendor_http_timeout_seconds

        def _request_with_timeout(method, url, **kwargs):
            kwargs.setdefault("timeout", deadline)
            return original_request(method, url, **kwargs)

        session.request = _request_with_timeout  # type: ignore[method-assign]
        session._tapeology_timeout_wrapped = True  # type: ignore[attr-defined]
        return client

    # --- Symbol search (read-only asset reference) --------------------------------------

    def search_symbols(self, query: str) -> list[SymbolMatch]:
        """Return tradable symbols whose symbol/name matches ``query`` (empty list if none).

        Symbol-prefix matches rank first, then symbol/name substring matches. Never raises for
        an empty result and never fabricates a suggestion.
        """
        q = query.strip().upper()
        if not q:
            return []
        universe = self._asset_universe()
        prefix = sorted(
            (m for m in universe if m.symbol.startswith(q)), key=lambda m: m.symbol
        )
        seen = {m.symbol for m in prefix}
        substring = sorted(
            (
                m
                for m in universe
                if m.symbol not in seen and (q in m.symbol or q in m.name.upper())
            ),
            key=lambda m: m.symbol,
        )
        return prefix + substring

    # --- Market clock (read-only session reference) -------------------------------------

    def get_market_clock(self) -> MarketClock:
        """Fetch the REAL market session status via Alpaca's trading clock (J-14 / row 8).

        Read-only reference call: it reports open/closed + next open/close and places/echoes NO
        order (the no-execution anti-goal holds). Vendor tz-aware datetimes are serialized to
        ISO-8601 UTC. A credential/network failure propagates so the API degrades to an explicit
        ``available:false`` — this method never fabricates a session.
        """
        from alpaca.trading.client import TradingClient

        client = self._with_http_timeout(
            TradingClient(_env(ENV_API_KEY), _env(ENV_API_SECRET), paper=True)
        )
        with _mapped_vendor_timeout():
            clock = client.get_clock()
        return MarketClock(
            is_open=bool(clock.is_open),
            next_open=_to_iso_utc(clock.next_open),
            next_close=_to_iso_utc(clock.next_close),
        )

    # --- Live real-time stream (J-12 / J-15) --------------------------------------------

    async def stream_live(self, symbol: str) -> AsyncIterator[LiveRecord]:
        """Yield ONE symbol's REAL real-time trades + quotes as vendor-neutral records.

        Opens ``alpaca.data.live.StockDataStream`` (the SOLE place the live SDK is named, lazily
        imported), subscribes to the symbol's **trades + quotes** (market data only — NO order/
        account/position call), and bridges the SDK's async callbacks into this async iterator via
        a queue. On cancel/close (stop/switch/shutdown) the ``finally`` unsubscribes and **closes
        the socket** so no vendor WebSocket is leaked (the iter-0 socket-leak lesson). Imports of
        the vendor SDK stay confined to this method/module behind the neutral seam.
        """
        from alpaca.data.live import StockDataStream

        sym = symbol.strip().upper()
        queue: asyncio.Queue[LiveRecord] = asyncio.Queue()
        stream = StockDataStream(_env(ENV_API_KEY), _env(ENV_API_SECRET), feed=self._data_feed())

        async def _on_trade(t) -> None:
            await queue.put(RawTrade(t.timestamp.timestamp(), float(t.price), int(t.size)))

        async def _on_quote(q) -> None:
            await queue.put(
                RawQuote(
                    q.timestamp.timestamp(),
                    float(q.bid_price),
                    float(q.ask_price),
                    int(q.bid_size),
                    int(q.ask_size),
                )
            )

        stream.subscribe_trades(_on_trade, sym)
        stream.subscribe_quotes(_on_quote, sym)
        runner = asyncio.create_task(stream._run_forever())
        try:
            while True:
                yield await queue.get()
        finally:
            # BOUNDED graceful close so the vendor socket is actually CLOSED on teardown (the
            # iter-0 socket-leak lesson) and the close can NEVER hang (a hung close would itself
            # leak the connection). stop_ws() signals the SDK's consume loop to close the socket
            # and its run loop to return; we wait briefly (shielded so the timeout does not cancel
            # the runner mid-close), force-cancel if it is still running, then close() as a final
            # idempotent safety — every await time-bounded. (CancelledError is a BaseException, so
            # a hard cancel still propagates through these ``suppress(Exception)`` guards.)
            #
            # NOTE: we deliberately do NOT call unsubscribe_*(): closing the socket drops every
            # subscription anyway, and the SDK's sync unsubscribe runs
            # ``run_coroutine_threadsafe(...).result()`` which DEADLOCKS when (as here) it is
            # invoked from inside the event-loop thread.
            grace = LIVE_TEARDOWN_GRACE_SECONDS
            with suppress(Exception):
                await stream.stop_ws()
            with suppress(Exception):
                await asyncio.wait_for(asyncio.shield(runner), timeout=grace)
            if not runner.done():
                runner.cancel()
            with suppress(Exception):
                await asyncio.wait_for(stream.close(), timeout=grace)

    def _asset_universe(self) -> list[SymbolMatch]:
        """Return the cached tradable-symbol universe, fetching it once if not yet warmed.

        Lazy fallback for the case where the startup warm did not run (or finished after the first
        search). The fetch runs under the real call-level HTTP deadline. ``_ASSET_UNIVERSE`` is the
        SINGLE owner of the universe (warmed at startup OR here) — there is no second store."""
        global _ASSET_UNIVERSE
        if _ASSET_UNIVERSE is None:
            _ASSET_UNIVERSE = self._fetch_asset_universe()
        return _ASSET_UNIVERSE

    def _fetch_asset_universe(self) -> list[SymbolMatch]:
        """Fetch the active US-equity tradable universe from the vendor (one round-trip)."""
        from alpaca.trading.client import TradingClient
        from alpaca.trading.enums import AssetClass, AssetStatus
        from alpaca.trading.requests import GetAssetsRequest

        client = self._with_http_timeout(
            TradingClient(_env(ENV_API_KEY), _env(ENV_API_SECRET), paper=True)
        )
        with _mapped_vendor_timeout():
            assets = client.get_all_assets(
                GetAssetsRequest(status=AssetStatus.ACTIVE, asset_class=AssetClass.US_EQUITY)
            )
        return [
            SymbolMatch(a.symbol, a.name or "")
            for a in assets
            if getattr(a, "tradable", False)
        ]

    def warm_symbol_universe(self) -> None:
        """Warm the tradable-symbol universe cache so the FIRST search is not a cold stall (J-30).

        Called once (in the background) from the FastAPI ``lifespan`` startup via the neutral
        adapter seam — ``main.py`` never names the SDK or the universe cache. NO-OP without
        credentials (search then stays ``[]``, never an error) and a NO-OP when already warmed.
        Any vendor/network error is swallowed (logged by the caller's task wrapper if it surfaces)
        so a warm failure never crashes startup — search just falls back to its lazy fetch. Keeps
        ``_ASSET_UNIVERSE`` the single owner; populates the same cell ``_asset_universe`` reads.
        """
        global _ASSET_UNIVERSE
        if not self.is_available() or _ASSET_UNIVERSE is not None:
            return
        with suppress(Exception):
            _ASSET_UNIVERSE = self._fetch_asset_universe()


def real_data_available() -> bool:
    """The single canonical source for the row-9 real-data availability state.

    Derived from the one concrete adapter's credential detection and evaluated fresh on each
    call (so it tracks the current environment). The API reads THIS (via the adapter) to gate a
    real-mode watch; it is not recomputed in the UI — the UI learns availability from the API.
    """
    return AlpacaAdapter().is_available()
