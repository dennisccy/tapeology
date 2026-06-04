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
  * ``MarketClock`` — the market session status (open/closed + next open/close as ISO-8601 UTC
    strings). Read by the Live market-status indicator and the live-watch pre-flight gate; the
    adapter only ever builds it from a real vendor reply (a credential/network failure surfaces
    as an explicit unavailable or an exception, never a fabricated session).

This seam carries no network call by itself and never fabricates an answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Protocol, Union, runtime_checkable


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


@dataclass(frozen=True)
class MarketClock:
    """Vendor-neutral market session status: open/closed + next open/close.

    ``is_open`` is the authoritative open/closed flag from the vendor. ``next_open`` and
    ``next_close`` are ISO-8601 **UTC** strings (e.g. ``2026-06-05T13:30:00Z``) or ``None`` when
    the vendor omits them. The adapter constructs this ONLY from a successful vendor reply, so an
    instance always carries a real ``is_open``; a missing credential or an unreachable vendor is
    surfaced as an explicit unavailable (at the API) or an exception — never a fabricated session.
    """

    is_open: bool
    next_open: str | None
    next_close: str | None


# A single live-stream record: a vendor-neutral trade or quote (the live ``stream_live`` yields
# these; ``LiveProvider`` maps each onto the engine's logical timeline).
LiveRecord = Union[RawTrade, RawQuote]


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
    empty list — never an error — when there is nothing to suggest). ``get_market_clock`` returns
    the real ``MarketClock`` (read-only reference call — it places/echoes no order); a vendor or
    network failure propagates as an exception the API degrades to an explicit unavailable.
    ``stream_live`` opens the vendor's real-time trade+quote socket for ONE symbol and yields
    vendor-neutral ``LiveRecord``s (market data only — no order/account/position call); on
    cancel/close it MUST unsubscribe and close the socket (no leaked connection).
    """

    name: str

    def is_available(self) -> bool:
        ...

    def fetch_historical(self, symbol: str, start, end) -> HistoricalWindow:
        ...

    def search_symbols(self, query: str) -> list[SymbolMatch]:
        ...

    def get_market_clock(self) -> MarketClock:
        ...

    def stream_live(self, symbol: str) -> AsyncIterator[LiveRecord]:
        ...
