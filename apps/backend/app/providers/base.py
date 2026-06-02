"""The provider interface the engine and API depend on (provider-agnostic anti-goal).

The engine consumes an ordered stream of ``TradeEvent`` / ``QuoteEvent`` and never knows
the source. Swapping the Phase-1 simulator for a real feed means implementing ``Provider``
— it requires no change to the engine or API. ``BookLevelEvent`` is reserved for a later
iteration (Level 2 book); the interface does not preclude adding it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Protocol, Union, runtime_checkable


class Side(str, Enum):
    """Aggressor side of a trade."""

    BUY = "buy"
    SELL = "sell"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TradeEvent:
    """A single executed trade.

    ``side`` is whatever the provider reports (often ``unknown`` for a raw feed); the
    engine re-derives the authoritative aggressor side from the quote in effect at
    ``timestamp`` via the aggressor classifier. ``timestamp`` is a logical second offset
    — never wall-clock — so the engine stays deterministic.
    """

    ticker: str
    timestamp: float
    price: float
    size: int
    side: Side = Side.UNKNOWN


@dataclass(frozen=True)
class QuoteEvent:
    """Top-of-book quote (best bid / best ask and their sizes)."""

    ticker: str
    timestamp: float
    bid: float
    ask: float
    bid_size: int
    ask_size: int


# Reserved for a later iteration (Level 2). Declared so the union/interface can grow
# without an engine/API change, but not produced or consumed this iteration.
# @dataclass(frozen=True)
# class BookLevelEvent: ...

Event = Union[TradeEvent, QuoteEvent]


@runtime_checkable
class Provider(Protocol):
    """Yields an ordered (by logical timestamp) stream of market events for one ticker."""

    ticker: str
    scenario: str

    def stream(self) -> Iterable[Event]:
        ...
