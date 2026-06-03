"""TapeStateClassifier: buyer_control, seller_control, cold-start unclear, and the
price-impact guards (the critical anti-goal surface) on both sides."""

import pytest

from app.config import CONFIG
from app.engine.classifier import (
    STATE_BUYER_CONTROL,
    STATE_SELLER_CONTROL,
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


def _seller_features(**overrides) -> dict[str, float]:
    """The mirror of ``_features``: high sell aggression with real downward price progress.

    A symmetric input (sell-ratio 0.90, sell-impact −0.40, spread 0.02, speed 2.0) must, by
    construction, score the SAME confidence the buyer test pins (0.8542) — buyer and seller
    read the identical reused scales/weights.
    """
    seller_base = {
        "aggressive_buy_ratio": 0.10,
        "aggressive_sell_ratio": 0.90,
        "buy_price_impact": 0.01,
        "sell_price_impact": -0.40,
    }
    seller_base.update(overrides)
    return _features(**seller_base)


def test_seller_control_with_reasonable_confidence():
    result = clf.classify(_seller_features(), trade_count=60)
    assert result.state == STATE_SELLER_CONTROL
    assert result.confidence >= CONFIG.reasonable_confidence
    # Exact transparent confidence — identical to the symmetric buyer case (same scales/weights).
    assert result.confidence == pytest.approx(0.8542, abs=1e-3)


def test_price_impact_guard_zero_impact_is_not_seller_control():
    # CRITICAL: high aggressive_sell_ratio but NO price progress must NOT be seller_control.
    # (Sell aggression without a price drop is bid-absorption-in-spirit — J-04, not control.)
    result = clf.classify(_seller_features(sell_price_impact=0.0), trade_count=60)
    assert result.state == STATE_UNCLEAR
    assert result.state != STATE_SELLER_CONTROL


def test_price_impact_guard_positive_impact_is_not_seller_control():
    # Price actually ROSE on the sell prints => the opposite of downward progress.
    result = clf.classify(_seller_features(sell_price_impact=0.05), trade_count=60)
    assert result.state != STATE_SELLER_CONTROL


def test_wide_spread_blocks_seller_control():
    result = clf.classify(_seller_features(average_spread=0.50), trade_count=60)
    assert result.state != STATE_SELLER_CONTROL


def test_default_buyer_features_do_not_trip_seller_gate():
    # The buyer fixture (aggressive_sell_ratio=0.10) must never read as seller_control:
    # the new seller branch must not perturb the existing buyer/unclear results.
    result = clf.classify(_features(), trade_count=60)
    assert result.state == STATE_BUYER_CONTROL
    assert result.state != STATE_SELLER_CONTROL
