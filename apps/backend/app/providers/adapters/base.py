"""The vendor-neutral market-data adapter seam (provider-agnostic anti-goal).

A ``MarketDataAdapter`` is the single seam behind which a concrete vendor (its SDK, its
credential names, its response shapes, its error types) is allowed to live. The engine, API,
providers, and the historical replay layer depend only on the *neutral* contract declared
here — vendor specifics never leak outward, so a second vendor is one new adapter module.

The neutral contract is:
  * ``RawTrade`` / ``RawQuote`` — plain, vendor-free records (a UTC epoch-seconds timestamp
    plus the fields the engine needs). The adapter translates the vendor's response into these.
  * ``HistoricalWindow`` — the result of one historical fetch (the symbol + its raw trades and
    quotes). ``HistoricalProvider`` maps these onto the engine's logical timeline.
  * ``SymbolNotTradable`` / ``NoDataForWindow`` — neutral failures the adapter raises so the
    API can map them to explicit, distinct HTTP errors WITHOUT importing any vendor type. They
    are the *honest* real-data failure modes (no fabricated tape ever takes their place).
  * ``SymbolMatch`` — one symbol-search suggestion (symbol + name).

This seam carries no network call by itself and never fabricates an answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class RawTrade:
    """A vendor-neutral executed trade: UTC epoch seconds, price, size."""

    epoch: float
    price: float
    size: int


@dataclass(frozen=True)
class RawQuote:
    """A vendor-neutral top-of-book quote: UTC epoch seconds, bid/ask and their sizes."""

    epoch: float
    bid: float
    ask: float
    bid_size: int
    ask_size: int


@dataclass(frozen=True)
class HistoricalWindow:
    """One historical fetch: the symbol plus its raw trades and quotes (ascending epoch)."""

    symbol: str
    trades: tuple[RawTrade, ...]
    quotes: tuple[RawQuote, ...]


@dataclass(frozen=True)
class SymbolMatch:
    """One symbol-search suggestion."""

    symbol: str
    name: str


class SymbolNotTradable(Exception):
    """The requested symbol is unknown / not a tradable symbol (neutral; no vendor type)."""


class NoDataForWindow(Exception):
    """The symbol is tradable but the requested window returned no trades/quotes (neutral)."""


@runtime_checkable
class MarketDataAdapter(Protocol):
    """Vendor-neutral seam the API reads for availability, history, and symbol search.

    ``name`` identifies the vendor for diagnostics. ``is_available()`` is ``True`` only when the
    vendor's credentials are present in the environment (no network, no fabrication).
    ``fetch_historical`` returns a ``HistoricalWindow`` or raises ``SymbolNotTradable`` /
    ``NoDataForWindow``. ``search_symbols`` returns matching tradable ``SymbolMatch`` rows (an
    empty list — never an error — when there is nothing to suggest).
    """

    name: str

    def is_available(self) -> bool:
        ...

    def fetch_historical(self, symbol: str, start, end) -> HistoricalWindow:
        ...

    def search_symbols(self, query: str) -> list[SymbolMatch]:
        ...
