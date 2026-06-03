"""Rule/threshold tape-state classifier — transparent, no ML (anti-goal: No ML in v1).

This iteration resolves five states:
  * ``buyer_control`` — high aggressive_buy_ratio AND positive buy_price_impact AND a stable
    spread AND elevated trade_speed, confidence at/above the directional floor.
  * ``seller_control`` — the strict mirror: high aggressive_sell_ratio AND *negative*
    sell_price_impact (real downward progress) AND a stable spread AND elevated speed.
  * ``bid_absorption`` — high aggressive_sell_ratio but the bid HELD: sell_price_impact is
    FLAT (above the negative control cutoff — no real drop) AND the bid refreshed
    (bid_refresh_score high) AND a stable spread.
  * ``ask_absorption`` — the buy/ask mirror: high aggressive_buy_ratio but buy_price_impact
    FLAT (below the positive control cutoff — no real rise) AND the ask refreshed.
  * ``unclear`` — cold-start (before warm-up), or warmed-up-but-no-clean-read.

THE KEYSTONE (price impact, not aggression): the absorption gates use the EXACT complement of
the control impact condition (bid_absorption needs ``sell_price_impact > max_sell_price_impact``
where seller_control needs ``<=``), so control and absorption are mutually exclusive on impact
and cannot both fire. Identical high one-sided aggression therefore resolves to *control* when
price actually moved and to *absorption* when it did not — and never to a silent ``unclear``,
because absorption requires real refresh evidence, not the mere absence of impact. Every
threshold/boundary comes from ``Config`` — no literal numbers here.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Config

STATE_BUYER_CONTROL = "buyer_control"
STATE_SELLER_CONTROL = "seller_control"
STATE_BID_ABSORPTION = "bid_absorption"
STATE_ASK_ABSORPTION = "ask_absorption"
STATE_UNCLEAR = "unclear"


@dataclass(frozen=True)
class Classification:
    state: str
    confidence: float
    observations: tuple[str, ...]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


class TapeStateClassifier:
    def __init__(self, config: Config) -> None:
        self._c = config

    def classify(self, primary_features: dict[str, float], trade_count: int) -> Classification:
        c = self._c

        # Honest cold start: not enough evidence yet => unclear, very low confidence.
        if trade_count < c.warmup_min_events:
            return Classification(
                STATE_UNCLEAR,
                c.cold_start_confidence,
                ("Warming up — collecting tape data",),
            )

        buy_ratio = primary_features["aggressive_buy_ratio"]
        buy_impact = primary_features["buy_price_impact"]
        sell_ratio = primary_features["aggressive_sell_ratio"]
        sell_impact = primary_features["sell_price_impact"]
        spread = primary_features["average_spread"]
        speed = primary_features["trade_speed"]
        bid_refresh = primary_features["bid_refresh_score"]
        ask_refresh = primary_features["ask_refresh_score"]

        # buyer_control — high buy aggression WITH real upward price progress. The buyer and
        # seller gates are mutually exclusive in practice (the aggressive ratios are
        # complementary shares of directional volume and cannot both reach the threshold);
        # precedence is made explicit and neither branch perturbs the other.
        buyer_gate = (
            buy_ratio >= c.min_aggressive_buy_ratio
            and buy_impact >= c.min_buy_price_impact      # price impact, not aggression
            and spread <= c.max_stable_spread
            and speed >= c.min_trade_speed
        )
        if buyer_gate:
            confidence = self._buyer_confidence(buy_ratio, buy_impact, spread, speed)
            # Only call a direction once we're at least reasonably confident; a weaker
            # read stays unclear rather than manufacturing a low-confidence directional call.
            if confidence >= c.reasonable_confidence:
                return Classification(
                    STATE_BUYER_CONTROL,
                    confidence,
                    self._buyer_observations(buy_ratio, buy_impact, spread),
                )

        # seller_control — the mirror: high sell aggression WITH real downward price progress
        # (sell_price_impact at/below the NEGATIVE cutoff). Sell aggression without the price
        # drop is absorption, not control (the bid_absorption case, J-04), and stays unclear
        # here rather than being mislabelled seller_control.
        seller_gate = (
            sell_ratio >= c.min_aggressive_sell_ratio
            and sell_impact <= c.max_sell_price_impact    # negative — price impact, not aggression
            and spread <= c.max_stable_spread
            and speed >= c.min_trade_speed
        )
        if seller_gate:
            confidence = self._seller_confidence(sell_ratio, sell_impact, spread, speed)
            if confidence >= c.reasonable_confidence:
                return Classification(
                    STATE_SELLER_CONTROL,
                    confidence,
                    self._seller_observations(sell_ratio, sell_impact, spread),
                )

        # bid_absorption — high sell aggression but the bid HELD: impact FLAT (strictly the
        # complement of seller_control's condition, so the two never both fire) AND a
        # refreshing bid. Reached only because the seller gate above did not (no real drop).
        bid_absorption_gate = (
            sell_ratio >= c.min_aggressive_sell_ratio
            and sell_impact > c.max_sell_price_impact      # NOT a real drop (flat)
            and bid_refresh >= c.min_bid_refresh_score      # real refresh evidence
            and spread <= c.max_stable_spread
        )
        if bid_absorption_gate:
            confidence = self._absorption_confidence(
                sell_ratio, sell_impact, spread, bid_refresh, c.min_aggressive_sell_ratio,
                c.min_bid_refresh_score,
            )
            if confidence >= c.reasonable_confidence:
                return Classification(
                    STATE_BID_ABSORPTION,
                    confidence,
                    self._bid_absorption_observations(),
                )

        # ask_absorption — the buy/ask mirror: high buy aggression but the ask HELD (impact
        # flat — no real rise) AND a refreshing ask.
        ask_absorption_gate = (
            buy_ratio >= c.min_aggressive_buy_ratio
            and buy_impact < c.min_buy_price_impact         # NOT a real rise (flat)
            and ask_refresh >= c.min_ask_refresh_score
            and spread <= c.max_stable_spread
        )
        if ask_absorption_gate:
            confidence = self._absorption_confidence(
                buy_ratio, buy_impact, spread, ask_refresh, c.min_aggressive_buy_ratio,
                c.min_ask_refresh_score,
            )
            if confidence >= c.reasonable_confidence:
                return Classification(
                    STATE_ASK_ABSORPTION,
                    confidence,
                    self._ask_absorption_observations(),
                )

        # Warmed up but no clean control or absorption => honestly unclear.
        return Classification(
            STATE_UNCLEAR,
            c.unclear_confidence,
            ("Mixed or weak evidence — no clear side in control",),
        )

    def _buyer_confidence(
        self, buy_ratio: float, buy_impact: float, spread: float, speed: float
    ) -> float:
        c = self._c
        ratio_score = _clamp01((buy_ratio - c.min_aggressive_buy_ratio) / c.ratio_scale)
        impact_score = _clamp01((buy_impact - c.min_buy_price_impact) / c.impact_scale)
        spread_score = _clamp01((c.max_stable_spread - spread) / c.max_stable_spread)
        speed_score = _clamp01((speed - c.min_trade_speed) / c.speed_scale)

        w_ratio, w_impact, w_spread, w_speed = c.confidence_weights
        raw = (
            w_ratio * ratio_score
            + w_impact * impact_score
            + w_spread * spread_score
            + w_speed * speed_score
        )
        return min(raw, c.max_confidence)

    @staticmethod
    def _buyer_observations(buy_ratio: float, buy_impact: float, spread: float) -> tuple[str, ...]:
        observations = ["Buyer aggression increasing"]
        if buy_impact > 0:
            observations.append("Price lifting on buy prints")
        observations.append("Spread stable and narrow")
        return tuple(observations)

    def _seller_confidence(
        self, sell_ratio: float, sell_impact: float, spread: float, speed: float
    ) -> float:
        c = self._c
        ratio_score = _clamp01((sell_ratio - c.min_aggressive_sell_ratio) / c.ratio_scale)
        # Mirror of the buyer impact score: reward the MAGNITUDE of the negative impact past
        # the negative cutoff, so a sharper drop earns higher confidence. Reuses impact_scale.
        impact_score = _clamp01((c.max_sell_price_impact - sell_impact) / c.impact_scale)
        spread_score = _clamp01((c.max_stable_spread - spread) / c.max_stable_spread)
        speed_score = _clamp01((speed - c.min_trade_speed) / c.speed_scale)

        w_ratio, w_impact, w_spread, w_speed = c.confidence_weights
        raw = (
            w_ratio * ratio_score
            + w_impact * impact_score
            + w_spread * spread_score
            + w_speed * speed_score
        )
        return min(raw, c.max_confidence)

    @staticmethod
    def _seller_observations(sell_ratio: float, sell_impact: float, spread: float) -> tuple[str, ...]:
        observations = ["Seller aggression increasing"]
        if sell_impact < 0:
            observations.append("Price falling on sell prints")
        observations.append("Spread stable and narrow")
        return tuple(observations)

    def _absorption_confidence(
        self,
        ratio: float,
        impact: float,
        spread: float,
        refresh: float,
        ratio_floor: float,
        refresh_floor: float,
    ) -> float:
        """Side-neutral absorption confidence (bid and ask share it by symmetry).

        Four components, equally weighted (reusing ``confidence_weights`` so absorption stays
        calibrated alongside the directional states): aggression past its floor, FLATNESS of
        the matching impact (rewarding near-zero, the opposite of the directional impact
        component), a narrow spread, and the refresh past its floor."""
        c = self._c
        ratio_score = _clamp01((ratio - ratio_floor) / c.ratio_scale)
        flatness_score = _clamp01(1.0 - abs(impact) / c.absorption_flat_band)
        spread_score = _clamp01((c.max_stable_spread - spread) / c.max_stable_spread)
        refresh_score = _clamp01((refresh - refresh_floor) / c.refresh_scale)

        w_ratio, w_flat, w_spread, w_refresh = c.confidence_weights
        raw = (
            w_ratio * ratio_score
            + w_flat * flatness_score
            + w_spread * spread_score
            + w_refresh * refresh_score
        )
        return min(raw, c.max_confidence)

    @staticmethod
    def _bid_absorption_observations() -> tuple[str, ...]:
        return (
            "Heavy sell volume being absorbed",
            "Price holding despite sell prints",
            "Spread stable and narrow",
        )

    @staticmethod
    def _ask_absorption_observations() -> tuple[str, ...]:
        return (
            "Heavy buy volume being absorbed",
            "Price stalling despite buy prints",
            "Spread stable and narrow",
        )
