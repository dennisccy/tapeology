"""Rule/threshold tape-state classifier — transparent, no ML (anti-goal: No ML in v1).

This iteration resolves two states:
  * ``buyer_control`` — requires, over the primary window, ALL of: high aggressive_buy_ratio
    AND positive buy_price_impact AND a stable (narrow) spread AND elevated trade_speed,
    and a resulting confidence at/above the directional floor.
  * ``unclear`` — cold-start (before warm-up), or warmed-up-but-no-clean-control.

The buyer_control gate REQUIRES positive ``buy_price_impact``: high buy aggression with no
price progress does NOT qualify (anti-goal: price impact, not raw aggression). The structure
extends to the other four states in later iterations. Every threshold/boundary comes from
``Config`` — no literal numbers here.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Config

STATE_BUYER_CONTROL = "buyer_control"
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
        spread = primary_features["average_spread"]
        speed = primary_features["trade_speed"]

        gate = (
            buy_ratio >= c.min_aggressive_buy_ratio
            and buy_impact >= c.min_buy_price_impact      # price impact, not aggression
            and spread <= c.max_stable_spread
            and speed >= c.min_trade_speed
        )
        if gate:
            confidence = self._buyer_confidence(buy_ratio, buy_impact, spread, speed)
            # Only call a direction once we're at least reasonably confident; a weaker
            # read stays unclear rather than manufacturing a low-confidence directional call.
            if confidence >= c.reasonable_confidence:
                return Classification(
                    STATE_BUYER_CONTROL,
                    confidence,
                    self._buyer_observations(buy_ratio, buy_impact, spread),
                )

        # Warmed up but no clean control => honestly unclear.
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
