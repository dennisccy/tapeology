"""Aggressor classification: a two-stage rule.

Stage 1 — the **quote rule** (unchanged, takes precedence): using the quote in effect at the
trade's timestamp, ``price >= ask`` => aggressive BUY, ``price <= bid`` => aggressive SELL.

Stage 2 — the **Lee-Ready tick-test fallback** (fires only when stage 1 yields no decision: no
quote in effect, OR price strictly between bid and ask): compare to the **prior trade price** —
uptick => BUY, downtick => SELL, zero-tick => carry the **last non-zero tick direction**. With no
quote AND no prior trade (or a zero-tick before any direction exists) the print honestly stays
``UNKNOWN`` (no fabrication).
"""

from app.engine.aggressor import classify_aggressor
from app.providers.base import QuoteEvent, Side, TradeEvent

QUOTE = QuoteEvent("SIM-BUYER", 1.0, bid=100.00, ask=100.02, bid_size=10, ask_size=10)


def _trade(price: float) -> TradeEvent:
    return TradeEvent("SIM-BUYER", 1.0, price, 100)


# --- Stage 1: the quote rule (unchanged, takes precedence) ---------------------------------

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


def test_quote_rule_takes_precedence_over_tick_test():
    # A clean quote-rule classification MUST win even when the tick test would disagree:
    # price at/through the ask is BUY regardless of a downtick vs. the prior trade. This
    # protects J-04/J-05 (absorption keys on aggressive prints at/through the quote).
    assert classify_aggressor(_trade(100.02), QUOTE, prior_trade_price=100.50) is Side.BUY
    # ...and at/through the bid is SELL even on an uptick.
    assert classify_aggressor(_trade(100.00), QUOTE, prior_trade_price=99.50) is Side.SELL


# --- Stage 2: the tick-test fallback (no quote in effect) ----------------------------------

def test_no_quote_uptick_is_buy():
    assert (
        classify_aggressor(_trade(100.05), None, prior_trade_price=100.00) is Side.BUY
    )


def test_no_quote_downtick_is_sell():
    assert (
        classify_aggressor(_trade(99.95), None, prior_trade_price=100.00) is Side.SELL
    )


def test_no_quote_zero_tick_carries_last_nonzero_direction():
    # Zero-tick vs. the prior trade => carry the last non-zero tick direction.
    assert (
        classify_aggressor(
            _trade(100.00), None, prior_trade_price=100.00, last_tick_dir=Side.BUY
        )
        is Side.BUY
    )
    assert (
        classify_aggressor(
            _trade(100.00), None, prior_trade_price=100.00, last_tick_dir=Side.SELL
        )
        is Side.SELL
    )


# --- Stage 2: the tick-test fallback fires INSIDE the spread (quote present, mid-spread) ----

def test_strictly_mid_spread_uptick_is_buy():
    # Quote present but price strictly between bid and ask => stage 1 undecided => tick test.
    assert (
        classify_aggressor(_trade(100.01), QUOTE, prior_trade_price=100.005) is Side.BUY
    )


def test_strictly_mid_spread_downtick_is_sell():
    assert (
        classify_aggressor(_trade(100.01), QUOTE, prior_trade_price=100.015) is Side.SELL
    )


def test_strictly_mid_spread_zero_tick_carries_direction():
    assert (
        classify_aggressor(
            _trade(100.01), QUOTE, prior_trade_price=100.01, last_tick_dir=Side.SELL
        )
        is Side.SELL
    )


# --- The honest-undecidable cases (fabrication guards) -------------------------------------

def test_no_quote_and_no_prior_trade_is_unknown():
    # The one genuinely undecidable case: no quote in effect AND no prior trade => UNKNOWN.
    # The classifier MUST NOT fabricate a side here.
    assert classify_aggressor(_trade(100.01), None) is Side.UNKNOWN
    assert classify_aggressor(_trade(100.01), None, prior_trade_price=None) is Side.UNKNOWN


def test_mid_spread_with_no_prior_trade_is_unknown():
    # Quote present, price strictly mid-spread, but no prior trade to tick-test against.
    assert classify_aggressor(_trade(100.01), QUOTE, prior_trade_price=None) is Side.UNKNOWN


def test_zero_tick_before_any_direction_is_unknown():
    # A zero-tick (price == prior) before any non-zero tick has established a direction:
    # there is nothing to carry yet => UNKNOWN (no fabrication).
    assert (
        classify_aggressor(
            _trade(100.01), None, prior_trade_price=100.01, last_tick_dir=None
        )
        is Side.UNKNOWN
    )
