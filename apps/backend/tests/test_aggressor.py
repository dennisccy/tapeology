"""Aggressor classification boundaries, using the quote in effect at the trade timestamp."""

from app.engine.aggressor import classify_aggressor
from app.providers.base import QuoteEvent, Side, TradeEvent

QUOTE = QuoteEvent("SIM-BUYER", 1.0, bid=100.00, ask=100.02, bid_size=10, ask_size=10)


def _trade(price: float) -> TradeEvent:
    return TradeEvent("SIM-BUYER", 1.0, price, 100)


def test_price_above_ask_is_buy():
    assert classify_aggressor(_trade(100.03), QUOTE) is Side.BUY


def test_price_equal_ask_is_buy():
    # Edge: price == ask => aggressive buy.
    assert classify_aggressor(_trade(100.02), QUOTE) is Side.BUY


def test_price_below_bid_is_sell():
    assert classify_aggressor(_trade(99.99), QUOTE) is Side.SELL


def test_price_equal_bid_is_sell():
    # Edge: price == bid => aggressive sell.
    assert classify_aggressor(_trade(100.00), QUOTE) is Side.SELL


def test_price_strictly_between_is_unknown():
    assert classify_aggressor(_trade(100.01), QUOTE) is Side.UNKNOWN


def test_no_prior_quote_is_unknown():
    # Edge: no quote in effect yet => unknown (never fabricate a side).
    assert classify_aggressor(_trade(100.01), None) is Side.UNKNOWN
