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

THE DIRECTIONAL OVERRIDE (J-36: spread is a graded factor, not an absolute veto): the control
predicate has four terms — aggressive ratio, RELATIVE price impact, speed, and a stable spread.
On REAL data a momentarily wide or absent/crossed QUOTED spread (a single-venue IEX quote, or the
suppressed/crossed quotes around an LULD trading halt) must not by itself veto a move that is
otherwise CLEARLY directional. So when the override is enabled and the ratio + relative impact +
speed terms ALL pass (the control predicate MINUS the spread term), control fires even with a wide
spread; the spread then enters ONLY as a GRADED confidence factor (``_graded_spread_score``),
decaying from 1.0 at the stable cap toward ``override_spread_floor_score`` but never collapsing to
a confidence veto. The override is ADDITIVE and changes NOTHING on weak/mixed tape (the ratio /
impact / speed terms simply do not all pass — honest-uncertainty holds) and NOTHING on flat-impact
tape (the impact term fails — absorption, not control). The absorption gates KEEP the spread term,
so a wide-spread flat-impact tape stays honestly ``unclear`` and the keystone complement is intact.
With the override disabled the spread is a hard veto again — byte-identical to pre-J-36.
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
        # The price-relative basis (J-33), read VERBATIM from the canonical feature engine (single
        # source of truth — the classifier never recomputes price). When it is present and positive
        # the gates are judged RELATIVE to price (spread in bps, impact as a return); when absent or
        # zero (legacy unit-test fixtures that pass no reference_price, or a cold/empty window) the
        # gates fall back to the ABSOLUTE dollar constants, so the prior behavior is byte-identical.
        reference_price = primary_features.get("reference_price", 0.0)
        rel = reference_price > 0.0

        # Resolve the four impact/spread gate-boundaries into one comparison space (relative when a
        # basis exists, absolute otherwise) so each gate is a single readable predicate below and
        # the absorption gates stay the EXACT complement of the control impact condition (keystone).
        if rel:
            spread_metric = spread / reference_price * 10000.0  # basis points
            buy_impact_metric = buy_impact / reference_price    # a return
            sell_impact_metric = sell_impact / reference_price  # a return
            max_spread = c.max_stable_spread_bps
            min_buy_impact = c.min_buy_price_impact_return
            max_sell_impact = c.max_sell_price_impact_return
        else:
            spread_metric = spread
            buy_impact_metric = buy_impact
            sell_impact_metric = sell_impact
            max_spread = c.max_stable_spread
            min_buy_impact = c.min_buy_price_impact
            max_sell_impact = c.max_sell_price_impact

        # The DIRECTIONAL-OVERRIDE (J-36): a move is "clearly directional" when the aggressive ratio,
        # the RELATIVE price impact, and the speed ALL pass — i.e. the existing control predicate
        # MINUS the spread term. When the override is enabled and the move is clearly directional AND
        # the spread is within the OVERRIDE BAND (at most ``override_max_spread_multiple`` × the
        # stable-spread cap), the spread no longer VETOES control; it enters ONLY as a GRADED
        # confidence factor (``_graded_spread_score`` below). This is what lets a real directional
        # move (GME's open drop, whose SIP quote is moderately wide / momentarily halted) resolve to
        # control instead of a perpetual ``unclear``. The BAND is the artifact-vs-illiquid boundary:
        # a spread WIDER than the band still vetoes control, so genuinely illiquid / mixed tape (the
        # honest-uncertainty guards: ~8× the cap) stays ``unclear``. The override is ADDITIVE: on
        # weak/mixed tape the ratio/impact/speed terms do not all pass (honest-uncertainty holds), and
        # a flat-impact tape never satisfies the impact term (price-impact-over-aggression /
        # absorption unchanged). With the override DISABLED the spread is a hard veto again, so the
        # pre-override fixtures are byte-identical (keystone switch). The ratio/impact/speed floors are
        # the SAME control floors — the band multiple + graded floor are the only new constants.
        override = c.directional_override_enabled
        # The widest spread the override will admit (the band edge), in the active metric domain.
        override_spread_ceiling = max_spread * c.override_max_spread_multiple
        spread_in_band = spread_metric <= override_spread_ceiling

        # buyer_control — high buy aggression WITH real upward price progress. The buyer and
        # seller gates are mutually exclusive in practice (the aggressive ratios are
        # complementary shares of directional volume and cannot both reach the threshold);
        # precedence is made explicit and neither branch perturbs the other.
        buyer_directional = (
            buy_ratio >= c.min_aggressive_buy_ratio
            and buy_impact_metric >= min_buy_impact       # price impact (relative), not aggression
            and speed >= c.min_trade_speed
        )
        # Without the override the spread is a hard AND-term (pre-J-36, byte-identical); with it a
        # spread inside the override band passes the GATE and is graded into confidence instead.
        buyer_gate = buyer_directional and (
            spread_metric <= max_spread or (override and spread_in_band)
        )
        if buyer_gate:
            # The graded spread only differs from the in-gate spread score when the spread is WIDE
            # (override path); at/under the cap it is identical, so the narrow-spread confidence is
            # unchanged. ``spread_wide`` marks the override-engaged case for the graded scorer.
            spread_wide = spread_metric > max_spread
            confidence = self._buyer_confidence(
                buy_ratio, buy_impact_metric, spread_metric, speed, rel, spread_wide
            )
            # Only call a direction once we're at least reasonably confident; a weaker
            # read stays unclear rather than manufacturing a low-confidence directional call.
            if confidence >= c.reasonable_confidence:
                return Classification(
                    STATE_BUYER_CONTROL,
                    confidence,
                    self._buyer_observations(buy_ratio, buy_impact, spread, spread_wide),
                )

        # seller_control — the mirror: high sell aggression WITH real downward price progress
        # (sell_price_impact at/below the NEGATIVE cutoff). Sell aggression without the price
        # drop is absorption, not control (the bid_absorption case, J-04), and stays unclear
        # here rather than being mislabelled seller_control.
        seller_directional = (
            sell_ratio >= c.min_aggressive_sell_ratio
            and sell_impact_metric <= max_sell_impact     # negative (relative) — impact, not aggression
            and speed >= c.min_trade_speed
        )
        seller_gate = seller_directional and (
            spread_metric <= max_spread or (override and spread_in_band)
        )
        if seller_gate:
            spread_wide = spread_metric > max_spread
            confidence = self._seller_confidence(
                sell_ratio, sell_impact_metric, spread_metric, speed, rel, spread_wide
            )
            if confidence >= c.reasonable_confidence:
                return Classification(
                    STATE_SELLER_CONTROL,
                    confidence,
                    self._seller_observations(sell_ratio, sell_impact, spread, spread_wide),
                )

        # bid_absorption — high sell aggression but the bid HELD: impact FLAT (strictly the
        # complement of seller_control's condition, so the two never both fire) AND a
        # refreshing bid. Reached only because the seller gate above did not (no real drop).
        bid_absorption_gate = (
            sell_ratio >= c.min_aggressive_sell_ratio
            and sell_impact_metric > max_sell_impact       # NOT a real drop (flat) — complement
            and bid_refresh >= c.min_bid_refresh_score      # real refresh evidence
            and spread_metric <= max_spread
        )
        if bid_absorption_gate:
            confidence = self._absorption_confidence(
                sell_ratio, sell_impact_metric, spread_metric, bid_refresh,
                c.min_aggressive_sell_ratio, c.min_bid_refresh_score, rel,
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
            and buy_impact_metric < min_buy_impact          # NOT a real rise (flat) — complement
            and ask_refresh >= c.min_ask_refresh_score
            and spread_metric <= max_spread
        )
        if ask_absorption_gate:
            confidence = self._absorption_confidence(
                buy_ratio, buy_impact_metric, spread_metric, ask_refresh,
                c.min_aggressive_buy_ratio, c.min_ask_refresh_score, rel,
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

    def _impact_score(self, impact_metric: float, min_impact: float, rel: bool) -> float:
        """Reward the magnitude of (buy) impact past its cutoff — relative or absolute domain.

        ``impact_metric`` and ``min_impact`` are both already in the SAME domain (a return when
        ``rel``, dollars otherwise), so the difference and the scale are consistent. With ``rel``
        False the absolute ``impact_scale`` is used, byte-identical to the pre-J-33 computation."""
        c = self._c
        scale = c.impact_return_scale if rel else c.impact_scale
        return _clamp01((impact_metric - min_impact) / scale)

    def _spread_score(self, spread_metric: float, rel: bool) -> float:
        """Reward a narrow spread — judged in bps when ``rel`` (relative to price), else dollars.

        With ``rel`` False this is (max_stable_spread - spread)/max_stable_spread, exactly the
        pre-J-33 absolute spread component (so the legacy fixtures keep their pinned confidence)."""
        c = self._c
        cap = c.max_stable_spread_bps if rel else c.max_stable_spread
        return _clamp01((cap - spread_metric) / cap)

    def _graded_spread_score(self, spread_metric: float, rel: bool, spread_wide: bool) -> float:
        """The spread confidence component, GRADED (J-36) when the directional override engaged.

        When ``spread_wide`` is False (spread at/under the stable cap, the common case) this is
        EXACTLY ``_spread_score`` — so the narrow-spread directional confidence is byte-identical to
        pre-J-36. When ``spread_wide`` is True (the override admitted a clearly-directional move whose
        spread is wide but within the override band), the score does NOT collapse to 0 (which would
        veto via confidence what we deliberately did not veto via the gate); instead it decays
        LINEARLY from 1.0 at the cap down to ``override_spread_floor_score`` at the band edge
        (``override_max_spread_multiple`` × cap). So a wide-but-in-band quote still earns at least the
        floor, keeping a clearly-directional move at/above ``reasonable_confidence`` — while a WIDER
        in-band spread still LOWERS confidence (graded, honest), never asserting false certainty. A
        spread BEYOND the band never reaches here (the gate vetoes it). All boundaries config-owned."""
        if not spread_wide:
            return self._spread_score(spread_metric, rel)
        c = self._c
        cap = c.max_stable_spread_bps if rel else c.max_stable_spread
        floor = c.override_spread_floor_score
        # The band runs from the cap to override_max_spread_multiple × cap; the score decays across it.
        decay_span = cap * (c.override_max_spread_multiple - 1.0)
        # How far past the cap the spread is, as a fraction of the band (clamped to [0,1]).
        excess_frac = _clamp01((spread_metric - cap) / decay_span) if decay_span > 0 else 1.0
        return floor + (1.0 - floor) * (1.0 - excess_frac)

    def _buyer_confidence(
        self, buy_ratio: float, buy_impact_metric: float, spread_metric: float,
        speed: float, rel: bool, spread_wide: bool = False,
    ) -> float:
        c = self._c
        min_impact = c.min_buy_price_impact_return if rel else c.min_buy_price_impact
        ratio_score = _clamp01((buy_ratio - c.min_aggressive_buy_ratio) / c.ratio_scale)
        impact_score = self._impact_score(buy_impact_metric, min_impact, rel)
        spread_score = self._graded_spread_score(spread_metric, rel, spread_wide)
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
    def _buyer_observations(
        buy_ratio: float, buy_impact: float, spread: float, spread_wide: bool = False
    ) -> tuple[str, ...]:
        observations = ["Buyer aggression increasing"]
        if buy_impact > 0:
            observations.append("Price lifting on buy prints")
        # Honest spread line: when the directional override engaged the spread was WIDE (the move was
        # called on ratio + real impact + speed, with the spread graded into confidence, not vetoed),
        # so claiming "stable and narrow" would mislead. Surface the artifact honestly instead.
        observations.append(
            "Wide quoted spread — call on price impact" if spread_wide else "Spread stable and narrow"
        )
        return tuple(observations)

    def _seller_confidence(
        self, sell_ratio: float, sell_impact_metric: float, spread_metric: float,
        speed: float, rel: bool, spread_wide: bool = False,
    ) -> float:
        c = self._c
        max_sell_impact = c.max_sell_price_impact_return if rel else c.max_sell_price_impact
        scale = c.impact_return_scale if rel else c.impact_scale
        ratio_score = _clamp01((sell_ratio - c.min_aggressive_sell_ratio) / c.ratio_scale)
        # Mirror of the buyer impact score: reward the MAGNITUDE of the negative impact past
        # the negative cutoff, so a sharper drop earns higher confidence (same domain on both).
        impact_score = _clamp01((max_sell_impact - sell_impact_metric) / scale)
        spread_score = self._graded_spread_score(spread_metric, rel, spread_wide)
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
    def _seller_observations(
        sell_ratio: float, sell_impact: float, spread: float, spread_wide: bool = False
    ) -> tuple[str, ...]:
        observations = ["Seller aggression increasing"]
        if sell_impact < 0:
            observations.append("Price falling on sell prints")
        # Honest spread line on the override path — see ``_buyer_observations``: a wide-but-in-band
        # quote was graded into confidence, not vetoed, so it must NOT read "stable and narrow".
        observations.append(
            "Wide quoted spread — call on price impact" if spread_wide else "Spread stable and narrow"
        )
        return tuple(observations)

    def _absorption_confidence(
        self,
        ratio: float,
        impact_metric: float,
        spread_metric: float,
        refresh: float,
        ratio_floor: float,
        refresh_floor: float,
        rel: bool,
    ) -> float:
        """Side-neutral absorption confidence (bid and ask share it by symmetry).

        Four components, equally weighted (reusing ``confidence_weights`` so absorption stays
        calibrated alongside the directional states): aggression past its floor, FLATNESS of
        the matching impact (rewarding near-zero, the opposite of the directional impact
        component), a narrow spread, and the refresh past its floor. ``impact_metric`` /
        ``spread_metric`` are in the relative (return / bps) domain when ``rel``; with ``rel`` False
        this is byte-identical to the pre-J-33 absolute computation (legacy fixtures unchanged)."""
        c = self._c
        flat_band = c.absorption_flat_band_return if rel else c.absorption_flat_band
        ratio_score = _clamp01((ratio - ratio_floor) / c.ratio_scale)
        flatness_score = _clamp01(1.0 - abs(impact_metric) / flat_band)
        spread_score = self._spread_score(spread_metric, rel)
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
