"""Latest quote + last trade, and the single derivation of bid / ask / spread / last.

``spread`` is computed exactly once, here (``ask - bid``). No other module — and never the
API or UI — recomputes it (anti-goal: single source of truth).
"""

from __future__ import annotations

from ..providers.base import QuoteEvent, TradeEvent


class MarketState:
    def __init__(self) -> None:
        self._quote: QuoteEvent | None = None
        self._last_trade: TradeEvent | None = None

    def update_quote(self, quote: QuoteEvent) -> None:
        self._quote = quote

    def update_trade(self, trade: TradeEvent) -> None:
        self._last_trade = trade

    @property
    def quote(self) -> QuoteEvent | None:
        """The quote currently in effect (used by the aggressor classifier)."""
        return self._quote

    @property
    def bid(self) -> float | None:
        return self._quote.bid if self._quote is not None else None

    @property
    def ask(self) -> float | None:
        return self._quote.ask if self._quote is not None else None

    @property
    def spread(self) -> float | None:
        if self._quote is None:
            return None
        return self._quote.ask - self._quote.bid

    @property
    def last(self) -> float | None:
        return self._last_trade.price if self._last_trade is not None else None
