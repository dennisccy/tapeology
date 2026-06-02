"""FeatureEngine: exact values for a known stream, determinism, and event-time windowing."""

import pytest

from app.config import CONFIG
from app.engine.features import FeatureEngine
from app.providers.base import Side


def _known_engine() -> FeatureEngine:
    """A small hand-checkable stream (all events fit inside the 60s window)."""
    fe = FeatureEngine(CONFIG)
    fe.add_quote(0.0, 0.02)
    fe.add_quote(3.0, 0.02)
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
