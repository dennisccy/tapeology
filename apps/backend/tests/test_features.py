"""FeatureEngine: exact values for a known stream, determinism, and event-time windowing."""

import pytest

from app.config import CONFIG
from app.engine.features import FeatureEngine
from app.providers.base import Side


def _known_engine() -> FeatureEngine:
    """A small hand-checkable stream (all events fit inside the 60s window).

    ``add_quote`` now threads bid/ask (for the refresh scores) in addition to spread; the
    existing nine feature values must remain byte-identical (asserted below)."""
    fe = FeatureEngine(CONFIG)
    fe.add_quote(0.0, 100.00, 100.02, 0.02)
    fe.add_quote(3.0, 100.00, 100.02, 0.02)
    fe.add_trade(1.0, 100.02, 100, Side.BUY)
    fe.add_trade(2.0, 100.03, 200, Side.BUY)
    fe.add_trade(3.0, 100.02, 100, Side.SELL)
    fe.add_trade(4.0, 100.04, 600, Side.BUY)  # large print (>= 500)
    return fe


def test_exact_feature_values_for_60s_window():
    out = _known_engine().compute(4.0)["60s"]

    assert out["trade_speed"] == pytest.approx(4 / 60)
    assert out["volume_speed"] == pytest.approx(1000 / 60)
    assert out["aggressive_buy_ratio"] == pytest.approx(0.9)   # 900 / 1000
    assert out["aggressive_sell_ratio"] == pytest.approx(0.1)  # 100 / 1000
    assert out["net_aggressive_volume"] == 800.0               # 900 - 100
    # Price impact accrues only on the matching aggressor prints, vs the previous trade:
    #   buys: (100.03-100.02) + (100.04-100.02) = 0.03 ; sell: (100.02-100.03) = -0.01
    assert out["buy_price_impact"] == pytest.approx(0.03)
    assert out["sell_price_impact"] == pytest.approx(-0.01)
    assert out["average_spread"] == pytest.approx(0.02)
    assert out["large_print_count"] == 1.0


def test_features_are_deterministic():
    a = _known_engine().compute(4.0)
    b = _known_engine().compute(4.0)
    assert a == b  # identical stream => identical features, exactly


def test_windowing_keyed_on_event_timestamps():
    fe = FeatureEngine(CONFIG)
    fe.add_trade(0.0, 100.00, 100, Side.BUY)
    fe.add_trade(100.0, 101.00, 100, Side.BUY)
    result = fe.compute(100.0)

    # 60s window is (40, 100]: the ts=0 trade has aged out, only ts=100 remains.
    assert result["60s"]["trade_speed"] == pytest.approx(1 / 60)
    # 300s window still holds both.
    assert result["300s"]["trade_speed"] == pytest.approx(2 / 300)


# --- Refresh scores: did the quote hold under aggression? (price impact, not aggression) ---

def _sell_into_bid(holds: bool, n: int = 5) -> FeatureEngine:
    """n aggressive-SELL prints hitting the bid; the bid either holds or walks down."""
    fe = FeatureEngine(CONFIG)
    bid = 100.00
    for i in range(n):
        ts = float(i)
        fe.add_quote(ts, bid, round(bid + 0.02, 2), 0.02)
        fe.add_trade(ts, bid, 100, Side.SELL)
        if not holds:
            bid = round(bid - 0.01, 2)  # bid walks DOWN (real downward progress)
    return fe


def test_bid_refresh_high_when_bid_holds():
    out = _sell_into_bid(holds=True).compute(4.0)["60s"]
    assert out["bid_refresh_score"] == pytest.approx(1.0)


def test_bid_refresh_low_when_bid_walks_down():
    out = _sell_into_bid(holds=False).compute(4.0)["60s"]
    # Only the first print sits at the high-water bid; the four below it do not refresh => 1/5.
    assert out["bid_refresh_score"] == pytest.approx(0.2)


def _buy_into_ask(holds: bool, n: int = 5) -> FeatureEngine:
    """n aggressive-BUY prints lifting the ask; the ask either holds or walks up."""
    fe = FeatureEngine(CONFIG)
    ask = 100.02
    for i in range(n):
        ts = float(i)
        fe.add_quote(ts, round(ask - 0.02, 2), ask, 0.02)
        fe.add_trade(ts, ask, 100, Side.BUY)
        if not holds:
            ask = round(ask + 0.01, 2)  # ask walks UP (real upward progress)
    return fe


def test_ask_refresh_high_when_ask_holds():
    out = _buy_into_ask(holds=True).compute(4.0)["60s"]
    assert out["ask_refresh_score"] == pytest.approx(1.0)


def test_ask_refresh_low_when_ask_walks_up():
    out = _buy_into_ask(holds=False).compute(4.0)["60s"]
    assert out["ask_refresh_score"] == pytest.approx(0.2)


# --- absorption_score: high one-sided aggression with little/no price progress -------------

def test_absorption_score_high_on_flat_impact_high_ratio():
    # 10 aggressive sells, all at one held price => ratio 1.0, impact exactly flat.
    fe = FeatureEngine(CONFIG)
    for i in range(10):
        ts = float(i)
        fe.add_quote(ts, 100.00, 100.02, 0.02)
        fe.add_trade(ts, 100.00, 100, Side.SELL)
    out = fe.compute(9.0)["60s"]
    assert out["aggressive_sell_ratio"] == pytest.approx(1.0)
    assert out["sell_price_impact"] == pytest.approx(0.0)
    assert out["absorption_score"] == pytest.approx(1.0)


def test_absorption_score_low_on_real_impact():
    # Same high sell ratio but the bid walks down (real negative impact) => not absorbing.
    fe = FeatureEngine(CONFIG)
    bid = 100.00
    for i in range(10):
        ts = float(i)
        fe.add_quote(ts, bid, round(bid + 0.02, 2), 0.02)
        fe.add_trade(ts, bid, 100, Side.SELL)
        bid = round(bid - 0.02, 2)
    out = fe.compute(9.0)["60s"]
    assert out["sell_price_impact"] < CONFIG.max_sell_price_impact   # a real drop
    assert out["absorption_score"] == pytest.approx(0.0)


def test_no_directional_volume_has_zero_absorption():
    # Cold / silent provider: no aggressive prints => no fabricated absorption signal.
    fe = FeatureEngine(CONFIG)
    fe.add_quote(0.0, 100.00, 100.02, 0.02)
    out = fe.compute(0.0)["60s"]
    assert out["absorption_score"] == pytest.approx(0.0)
    assert out["bid_refresh_score"] == pytest.approx(0.0)
    assert out["ask_refresh_score"] == pytest.approx(0.0)
