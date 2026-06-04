"""Alpaca market-data adapter — the SINGLE module where Alpaca specifics live.

This is the one concrete adapter behind the vendor-neutral ``MarketDataAdapter`` seam, and the
ONLY module permitted to import the ``alpaca-py`` SDK or name "Alpaca". It does three things:

  * ``is_available()`` — credential detection from the ENVIRONMENT ONLY (never committed
    source, never the engine ``Config``); ``True`` iff both key and secret are present.
  * ``fetch_historical()`` — fetch one symbol's REAL trades + quotes for a past window and
    translate them into vendor-neutral ``RawTrade`` / ``RawQuote`` records. Unknown/untradable
    symbol → ``SymbolNotTradable``; a window with no trades → ``NoDataForWindow``. No vendor
    exception type leaks outward.
  * ``search_symbols()`` — read-only tradable-symbol *reference* lookup for the search box
    (symbol + name). This uses Alpaca's asset reference list only; it places/echoes NO orders
    and integrates no execution/brokerage capability (the no-execution anti-goal holds).

The SDK is imported lazily inside the methods so the no-credentials / simulated / test paths
never pay its (pandas/numpy) import cost. Blocking network calls are synchronous here; the API
runs them off the event loop (``asyncio.to_thread``) so the watch gate stays responsive.

Anti-goals served: *no secrets in source* (env-only; names documented with empty values in
``.env.example``), *provider-agnostic engine* (vendor names + SDK confined here), *no fabricated
data* (every failure is an explicit neutral outcome, never a synthesized read).
"""

from __future__ import annotations

import os
from datetime import timezone

from .base import (
    HistoricalWindow,
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
