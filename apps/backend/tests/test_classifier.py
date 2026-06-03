"""TapeStateClassifier: buyer_control, seller_control, bid/ask_absorption, cold-start
unclear, and the price-impact guards (the critical anti-goal surface) on all sides.

The keystone of the whole product lives here: identical high one-sided aggression resolves
to *control* when price actually moved and to *absorption* when it did not — keying on price
impact, never on the aggression ratio alone."""

import pytest

from app.config import CONFIG
from app.engine.classifier import (
    STATE_ASK_ABSORPTION,
    STATE_BID_ABSORPTION,
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
        # Absorption features default to NO refresh evidence, so flat impact alone never
        # fabricates an absorption call — it requires positive *_refresh_score evidence.
        "absorption_score": 0.0,
        "bid_refresh_score": 0.0,
        "ask_refresh_score": 0.0,
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


# --- Absorption: bid_absorption (J-04) — high sell aggression, FLAT impact, bid refresh ----

def _bid_absorption_features(**overrides) -> dict[str, float]:
    """High aggressive SELL volume with FLAT impact (no real drop) + a refreshing bid.

    Symmetric (sell-ratio 0.90, flat impact, spread 0.02, bid_refresh 1.0) so it scores the
    SAME transparent confidence the symmetric buyer/seller cases pin (0.8542)."""
    base = _features(
        aggressive_buy_ratio=0.10,
        aggressive_sell_ratio=0.90,
        buy_price_impact=0.01,
        sell_price_impact=0.0,        # FLAT — above the negative cutoff: no real drop
        absorption_score=0.90,
        bid_refresh_score=1.0,        # the bid held / refreshed under selling
        ask_refresh_score=0.0,
    )
    base.update(overrides)
    return base


def test_bid_absorption_on_flat_impact_with_refresh():
    # The defining case: high sell aggression but the bid HELD (flat impact + refresh) =>
    # bid_absorption, NOT seller_control and NOT a silent unclear.
    result = clf.classify(_bid_absorption_features(), trade_count=60)
    assert result.state == STATE_BID_ABSORPTION
    assert result.state != STATE_SELLER_CONTROL
    assert result.state != STATE_UNCLEAR
    assert result.confidence >= CONFIG.reasonable_confidence
    assert result.confidence == pytest.approx(0.8542, abs=1e-3)


def test_high_sell_aggression_with_real_drop_is_seller_not_bid_absorption():
    # KEYSTONE precedence: identical high sell aggression but with a REAL negative impact
    # must resolve to seller_control — never bid_absorption. Price impact, not aggression.
    result = clf.classify(_bid_absorption_features(sell_price_impact=-0.40), trade_count=60)
    assert result.state == STATE_SELLER_CONTROL
    assert result.state != STATE_BID_ABSORPTION


def test_bid_absorption_requires_refresh_evidence_not_mere_flat_impact():
    # Flat impact but NO refresh evidence => honest unclear (no fabricated absorption).
    result = clf.classify(_bid_absorption_features(bid_refresh_score=0.0), trade_count=60)
    assert result.state == STATE_UNCLEAR
    assert result.state != STATE_BID_ABSORPTION


def test_wide_spread_blocks_bid_absorption():
    result = clf.classify(_bid_absorption_features(average_spread=0.50), trade_count=60)
    assert result.state == STATE_UNCLEAR
    assert result.state != STATE_BID_ABSORPTION


# --- Absorption: ask_absorption (J-05) — the strict buy/ask mirror -------------------------

def _ask_absorption_features(**overrides) -> dict[str, float]:
    """High aggressive BUY volume with FLAT impact (no real rise) + a refreshing ask."""
    base = _features(
        aggressive_buy_ratio=0.90,
        aggressive_sell_ratio=0.10,
        buy_price_impact=0.0,         # FLAT — below the positive cutoff: no real rise
        sell_price_impact=-0.01,
        absorption_score=0.90,
        bid_refresh_score=0.0,
        ask_refresh_score=1.0,        # the ask held / refreshed under buying
    )
    base.update(overrides)
    return base


def test_ask_absorption_on_flat_impact_with_refresh():
    result = clf.classify(_ask_absorption_features(), trade_count=60)
    assert result.state == STATE_ASK_ABSORPTION
    assert result.state != STATE_BUYER_CONTROL
    assert result.state != STATE_UNCLEAR
    assert result.confidence >= CONFIG.reasonable_confidence
    assert result.confidence == pytest.approx(0.8542, abs=1e-3)


def test_high_buy_aggression_with_real_rise_is_buyer_not_ask_absorption():
    # Mirror keystone: high buy aggression WITH real upward progress => buyer_control.
    result = clf.classify(_ask_absorption_features(buy_price_impact=0.40), trade_count=60)
    assert result.state == STATE_BUYER_CONTROL
    assert result.state != STATE_ASK_ABSORPTION


def test_ask_absorption_requires_refresh_evidence_not_mere_flat_impact():
    result = clf.classify(_ask_absorption_features(ask_refresh_score=0.0), trade_count=60)
    assert result.state == STATE_UNCLEAR
    assert result.state != STATE_ASK_ABSORPTION


def test_wide_spread_blocks_ask_absorption():
    result = clf.classify(_ask_absorption_features(average_spread=0.50), trade_count=60)
    assert result.state == STATE_UNCLEAR
    assert result.state != STATE_ASK_ABSORPTION


# --- Unclear / chop (J-06) — warmed-up but genuinely mixed two-sided, no clean read ---------

def _chop_features(**overrides) -> dict[str, float]:
    """Balanced two-sided aggression with a wide spread, no price progress, no refresh — the
    unit mirror of the SIM-CHOP stream: neither ratio reaches its floor, the spread is wide, the
    impacts are ~zero and the quote never refreshed."""
    base = _features(
        aggressive_buy_ratio=0.50,
        aggressive_sell_ratio=0.50,
        buy_price_impact=0.0,
        sell_price_impact=0.0,
        average_spread=0.20,          # wide — above max_stable_spread
        absorption_score=0.0,
        bid_refresh_score=0.0,
        ask_refresh_score=0.0,
    )
    base.update(overrides)
    return base


def test_chop_balanced_two_sided_is_warmed_unclear():
    # Warmed up (not cold start) but genuinely mixed => the honest warmed `unclear` at low
    # confidence, and explicitly NONE of the four resolved states.
    result = clf.classify(_chop_features(), trade_count=60)
    assert result.state == STATE_UNCLEAR
    assert result.confidence == CONFIG.unclear_confidence
    assert result.confidence < CONFIG.reasonable_confidence
    for resolved in (
        STATE_BUYER_CONTROL, STATE_SELLER_CONTROL, STATE_BID_ABSORPTION, STATE_ASK_ABSORPTION
    ):
        assert result.state != resolved


def test_chop_balanced_ratios_alone_deny_every_gate():
    # The load-bearing lever, isolated: mixed two-sided aggression (both ratios sub-floor) denies
    # every gate on its own — even handed a STABLE narrow spread AND full refresh on both sides,
    # the read is still unclear, because no gate's one-sided ratio precondition is met.
    result = clf.classify(
        _chop_features(average_spread=0.02, bid_refresh_score=1.0, ask_refresh_score=1.0),
        trade_count=60,
    )
    assert result.state == STATE_UNCLEAR
    assert result.state != STATE_BID_ABSORPTION
    assert result.state != STATE_ASK_ABSORPTION
