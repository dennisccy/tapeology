"""Aggressor classification: which side initiated a trade, from the quote in effect.

trade price >= current ask  => aggressive BUY (someone lifted the offer)
trade price <= current bid  => aggressive SELL (someone hit the bid)
strictly between            => UNKNOWN
no quote in effect yet       => UNKNOWN

The quote passed in MUST be the one in effect at the trade's timestamp; the engine
guarantees this by updating ``MarketState`` with each quote before classifying a trade
(events are processed in logical-timestamp order).
"""

from __future__ import annotations

from ..providers.base import QuoteEvent, Side, TradeEvent


def classify_aggressor(trade: TradeEvent, quote: QuoteEvent | None) -> Side:
    if quote is None:
        return Side.UNKNOWN
    if trade.price >= quote.ask:
        return Side.BUY
    if trade.price <= quote.bid:
        return Side.SELL
    return Side.UNKNOWN
