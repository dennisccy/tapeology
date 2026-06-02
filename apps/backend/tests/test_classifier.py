"""TapeStateClassifier: buyer_control, cold-start unclear, and the price-impact guard."""

import pytest

from app.config import CONFIG
from app.engine.classifier import (
    STATE_BUYER_CONTROL,
    STATE_UNCLEAR,
    TapeStateClassifier,
)

clf = TapeStateClassifier(CONFIG)


def _features(**overrides) -> dict[str, float]:
    base = {
        "trade_speed": 2.0,
        "volume_speed": 400.0,
        "aggressive_buy_ratio": 0.90,
        "aggressive_sell_ratio": 0.10,
        "net_aggressive_volume": 800.0,
        "buy_price_impact": 0.40,
        "sell_price_impact": -0.01,
        "average_spread": 0.02,
        "large_print_count": 2.0,
    }
    base.update(overrides)
    return base


def test_cold_start_is_unclear_low_confidence():
    result = clf.classify(_features(), trade_count=CONFIG.warmup_min_events - 1)
    assert result.state == STATE_UNCLEAR
    assert result.confidence == CONFIG.cold_start_confidence
    assert result.confidence < CONFIG.reasonable_confidence


def test_buyer_control_with_reasonable_confidence():
    result = clf.classify(_features(), trade_count=60)
    assert result.state == STATE_BUYER_CONTROL
    assert result.confidence >= CONFIG.reasonable_confidence
    # Exact transparent confidence: weighted mean of the four margin scores.
    assert result.confidence == pytest.approx(0.8542, abs=1e-3)


def test_price_impact_guard_zero_impact_is_not_buyer_control():
    # CRITICAL: high aggressive_buy_ratio but NO price progress must NOT be buyer_control.
    result = clf.classify(_features(buy_price_impact=0.0), trade_count=60)
    assert result.state == STATE_UNCLEAR
    assert result.state != STATE_BUYER_CONTROL


def test_price_impact_guard_negative_impact_is_not_buyer_control():
    result = clf.classify(_features(buy_price_impact=-0.05), trade_count=60)
    assert result.state != STATE_BUYER_CONTROL


def test_wide_spread_blocks_buyer_control():
    result = clf.classify(_features(average_spread=0.50), trade_count=60)
    assert result.state != STATE_BUYER_CONTROL
