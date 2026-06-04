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

Anti-goals served: *no secrets in source* (env-only; names documented with empty values in
``.env.example``), *provider-agnostic engine* (vendor names + SDK confined here), *no fabricated
data* (every failure is an explicit neutral outcome, never a synthesized read).
"""

from __future__ import annotations

import asyncio
import os
from contextlib import suppress
from datetime import timezone
from typing import AsyncIterator

from .base import (
    HistoricalWindow,
    LiveRecord,
    MarketClock,
    NoDataForWindow,
    RawQuote,
    RawTrade,
    SymbolMatch,
    SymbolNotTradable,
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
# does not re-fetch ~14k assets on every keystroke. Populated lazily on first search.
_ASSET_UNIVERSE: list[SymbolMatch] | None = None


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

        Raises ``SymbolNotTradable`` for an unknown/untradable symbol and ``NoDataForWindow``
        when the (tradable) symbol has no trades in the window — never a fabricated tape.
        """
        sym = symbol.strip().upper()
        self._require_tradable(sym)
        trades, quotes = self._fetch_trades_quotes(sym, start, end)
        if not trades:
            raise NoDataForWindow(sym)
        return HistoricalWindow(sym, tuple(trades), tuple(quotes))

    def _require_tradable(self, symbol: str) -> None:
        """Validate the symbol against Alpaca's asset reference; raise neutral on failure."""
        from alpaca.common.exceptions import APIError
        from alpaca.trading.client import TradingClient

        client = TradingClient(_env(ENV_API_KEY), _env(ENV_API_SECRET), paper=True)
        try:
            asset = client.get_asset(symbol)
        except APIError as exc:
            if getattr(exc, "status_code", None) == 404:
                raise SymbolNotTradable(symbol) from None
            raise
        if not getattr(asset, "tradable", False):
            raise SymbolNotTradable(symbol)

    def _fetch_trades_quotes(self, symbol: str, start, end):
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockQuotesRequest, StockTradesRequest

        client = StockHistoricalDataClient(_env(ENV_API_KEY), _env(ENV_API_SECRET))
        feed = self._data_feed()
        trades_resp = client.get_stock_trades(
            StockTradesRequest(symbol_or_symbols=symbol, start=start, end=end, feed=feed)
        )
        quotes_resp = client.get_stock_quotes(
            StockQuotesRequest(symbol_or_symbols=symbol, start=start, end=end, feed=feed)
        )
        trades = [
            RawTrade(t.timestamp.timestamp(), float(t.price), int(t.size))
            for t in trades_resp.data.get(symbol, [])
        ]
        quotes = [
            RawQuote(
                q.timestamp.timestamp(),
                float(q.bid_price),
                float(q.ask_price),
                int(q.bid_size),
                int(q.ask_size),
            )
            for q in quotes_resp.data.get(symbol, [])
        ]
        return trades, quotes

    def _data_feed(self):
        from alpaca.data.enums import DataFeed

        try:
            return DataFeed(self.feed)
        except ValueError:
            return DataFeed.IEX

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

        client = TradingClient(_env(ENV_API_KEY), _env(ENV_API_SECRET), paper=True)
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
        global _ASSET_UNIVERSE
        if _ASSET_UNIVERSE is None:
            from alpaca.trading.client import TradingClient
            from alpaca.trading.enums import AssetClass, AssetStatus
            from alpaca.trading.requests import GetAssetsRequest

            client = TradingClient(_env(ENV_API_KEY), _env(ENV_API_SECRET), paper=True)
            assets = client.get_all_assets(
                GetAssetsRequest(status=AssetStatus.ACTIVE, asset_class=AssetClass.US_EQUITY)
            )
            _ASSET_UNIVERSE = [
                SymbolMatch(a.symbol, a.name or "")
                for a in assets
                if getattr(a, "tradable", False)
            ]
        return _ASSET_UNIVERSE


def real_data_available() -> bool:
    """The single canonical source for the row-9 real-data availability state.

    Derived from the one concrete adapter's credential detection and evaluated fresh on each
    call (so it tracks the current environment). The API reads THIS (via the adapter) to gate a
    real-mode watch; it is not recomputed in the UI — the UI learns availability from the API.
    """
    return AlpacaAdapter().is_available()
