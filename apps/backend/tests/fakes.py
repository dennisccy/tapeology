"""Test seam: a fake market-data adapter + a loader for the committed REAL fixture.

The historical/search tests inject ``FakeAdapter`` via FastAPI ``dependency_overrides`` (a
standard DI seam) so the suite stays hermetic — no real network call, no prod env-var backdoor
in the live code path. ``load_fixture_window`` loads the committed REAL captured Alpaca window
into the same vendor-neutral ``HistoricalWindow`` the production adapter returns.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.providers.adapters.base import (
    HistoricalWindow,
    NoDataForWindow,
    RawQuote,
    RawTrade,
    SymbolMatch,
    SymbolNotTradable,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "alpaca" / "F_20260602_150000_20260602_150200.json"
)


def load_fixture_window(path: Path = FIXTURE_PATH) -> tuple[HistoricalWindow, dict]:
    """Load the committed REAL fixture into a ``HistoricalWindow`` (and return the raw dict)."""
    data = json.loads(path.read_text())
    trades = tuple(RawTrade(t["epoch"], t["price"], t["size"]) for t in data["trades"])
    quotes = tuple(
        RawQuote(q["epoch"], q["bid"], q["ask"], q["bid_size"], q["ask_size"])
        for q in data["quotes"]
    )
    return HistoricalWindow(data["symbol"], trades, quotes), data


class FakeAdapter:
    """A ``MarketDataAdapter`` stand-in driven entirely by constructor flags."""

    name = "fake"

    def __init__(
        self,
        *,
        available: bool = True,
        window: HistoricalWindow | None = None,
        not_tradable: bool = False,
        no_data: bool = False,
        matches: list[SymbolMatch] | None = None,
        search_raises: bool = False,
    ) -> None:
        self._available = available
        self._window = window
        self._not_tradable = not_tradable
        self._no_data = no_data
        self._matches = matches or []
        self._search_raises = search_raises
        self.fetch_calls: list[tuple] = []
        self.search_calls: list[str] = []

    def is_available(self) -> bool:
        return self._available

    def fetch_historical(self, symbol: str, start, end) -> HistoricalWindow:
        self.fetch_calls.append((symbol, start, end))
        if self._not_tradable:
            raise SymbolNotTradable(symbol)
        if self._no_data:
            raise NoDataForWindow(symbol)
        assert self._window is not None, "FakeAdapter needs a window for a successful fetch"
        return self._window

    def search_symbols(self, query: str) -> list[SymbolMatch]:
        self.search_calls.append(query)
        if self._search_raises:
            raise RuntimeError("simulated adapter failure")
        q = query.strip().upper()
        return [m for m in self._matches if q in m.symbol.upper() or q in m.name.upper()]
