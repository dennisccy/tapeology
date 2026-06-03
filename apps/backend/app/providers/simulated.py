"""Deterministic, seedable simulated provider (Phase-1 data source).

``SIM-BUYER`` / ``SIM-SELLER`` (directional control) and ``SIM-BIDABS`` / ``SIM-ASKABS``
(absorption) are driven to their target states; ``SIM-CHOP`` is reserved in the registry (so
it is *known*, not fabricated) but not driven to its state yet (J-06). Same seed => identical
stream (determinism anti-goal): all randomness comes from a seeded ``random.Random`` and every
event carries a logical timestamp, never wall-clock. Wall-clock is used only by the feeder to
*pace delivery* in live mode.

The numbers below are scenario *shape* (the data the simulator emits), not engine
thresholds — engine/classifier thresholds live in ``app.config``.
"""

from __future__ import annotations

import random
from typing import Iterator

from .base import Event, QuoteEvent, Side, TradeEvent

# Reserved sim tickers -> target tape state. SIM-BUYER and SIM-SELLER resolve this iteration.
SIM_SCENARIOS: dict[str, str] = {
    "SIM-BUYER": "buyer_control",
    "SIM-SELLER": "seller_control",
    "SIM-BIDABS": "bid_absorption",
    "SIM-ASKABS": "ask_absorption",
    "SIM-CHOP": "unclear_chop",
}

DEFAULT_SEED = 7

# --- Directional-control scenario shape (SIM-BUYER and its SIM-SELLER mirror share it) ---
# These are side-neutral magnitudes; the seller stream reuses them so buyer/seller confidence
# stay calibrated identically (see _seller_control_stream for the role mapping).
_START_BID = 100.00
_START_ASK = 100.02          # spread held at 0.02 (narrow / stable)
_PRICE_TICK = 0.01
_LOGICAL_DT = 0.5            # logical seconds between ticks
_QUOTE_SIZE = 800
_P_MINORITY = 0.12         # minority share of prints (the non-controlling side)
_P_QUOTE_MOVE = 0.5        # chance a controlling-side tick moves the quote (=> price progress)
_MAJORITY_SIZES = (100, 200, 300, 600)   # controlling side; 600 >= large_print_size
_MINORITY_SIZES = (100, 200)
_MAX_TICKS = 5000          # bounded stream

# --- Absorption scenario shape (SIM-BIDABS and its SIM-ASKABS mirror share it) ------------
# The quote HOLDS at a fixed level under heavy one-sided aggression, so the matching price
# impact stays flat (~0) — the defining contrast with the directional streams, where the
# quote walks. Every print lands at the held bid (BIDABS) / ask (ASKABS) at ONE price, so the
# cumulative price impact is exactly zero: any off-price print would reintroduce tick-to-tick
# impact and corrupt the keystone "no price progress" signal. Sizes vary (incl. 600 >=
# large_print_size) so a large print is genuinely absorbed.
_ABS_BID = 100.00
_ABS_ASK = 100.02          # spread 0.02 (narrow / stable); the quote never moves


class SimulatedProvider:
    def __init__(self, ticker: str, scenario: str, seed: int = DEFAULT_SEED) -> None:
        self.ticker = ticker
        self.scenario = scenario
        self.seed = seed

    def stream(self) -> Iterator[Event]:
        if self.ticker == "SIM-BUYER":
            yield from self._buyer_control_stream()
        elif self.ticker == "SIM-SELLER":
            yield from self._seller_control_stream()
        elif self.ticker == "SIM-BIDABS":
            yield from self._bid_absorption_stream()
        elif self.ticker == "SIM-ASKABS":
            yield from self._ask_absorption_stream()
        # SIM-CHOP still produces no events this iteration: the engine stays an honest
        # cold-start `unclear` rather than fabricating a resolved state (J-06 builds it).

    def _buyer_control_stream(self) -> Iterator[Event]:
        rng = random.Random(self.seed)
        bid, ask = _START_BID, _START_ASK
        t = 0.0
        for _ in range(_MAX_TICKS):
            is_buy = rng.random() >= _P_MINORITY
            if is_buy and rng.random() < _P_QUOTE_MOVE:
                # Aggressive buyers consume the offer and lift the quote one tick.
                bid = round(bid + _PRICE_TICK, 2)
                ask = round(ask + _PRICE_TICK, 2)

            yield QuoteEvent(self.ticker, t, bid, ask, _QUOTE_SIZE, _QUOTE_SIZE)
            if is_buy:
                yield TradeEvent(self.ticker, t, ask, rng.choice(_MAJORITY_SIZES), Side.UNKNOWN)
            else:
                yield TradeEvent(self.ticker, t, bid, rng.choice(_MINORITY_SIZES), Side.UNKNOWN)
            t += _LOGICAL_DT

    def _seller_control_stream(self) -> Iterator[Event]:
        # Strict mirror of _buyer_control_stream: the MAJORITY of prints are aggressive sells
        # that hit the bid, and on a controlling-side tick (same probability the buyer stream
        # lifts) the quote drops one tick — so sell_price_impact is genuinely NEGATIVE (real
        # downward price progress, what separates seller_control from bid_absorption). Same
        # seed + shared shape => the price path is the buyer's reflection, so seller confidence
        # lands the same comfortable margin above reasonable_confidence.
        rng = random.Random(self.seed)
        bid, ask = _START_BID, _START_ASK
        t = 0.0
        for _ in range(_MAX_TICKS):
            is_sell = rng.random() >= _P_MINORITY
            if is_sell and rng.random() < _P_QUOTE_MOVE:
                # Aggressive sellers hit the bid and drop the quote one tick.
                bid = round(bid - _PRICE_TICK, 2)
                ask = round(ask - _PRICE_TICK, 2)

            yield QuoteEvent(self.ticker, t, bid, ask, _QUOTE_SIZE, _QUOTE_SIZE)
            if is_sell:
                # Prints at the bid => engine tags it Side.SELL; the falling bid makes the
                # cumulative sell_price_impact negative.
                yield TradeEvent(self.ticker, t, bid, rng.choice(_MAJORITY_SIZES), Side.UNKNOWN)
            else:
                yield TradeEvent(self.ticker, t, ask, rng.choice(_MINORITY_SIZES), Side.UNKNOWN)
            t += _LOGICAL_DT

    def _bid_absorption_stream(self) -> Iterator[Event]:
        # Heavy aggressive SELLING into a bid that HOLDS at the same price: every print hits
        # the bid (=> Side.SELL) but the bid is re-quoted at the SAME level (refreshes, never
        # drops), so cumulative sell_price_impact stays ~0 — no real downward progress. The
        # strict contrast with _seller_control_stream, where the bid walks DOWN (impact
        # strongly negative). The absorption read is EARNED by real refresh evidence + flat
        # impact, never by the sell ratio alone (the keystone anti-goal).
        rng = random.Random(self.seed)
        bid, ask = _ABS_BID, _ABS_ASK
        t = 0.0
        for _ in range(_MAX_TICKS):
            yield QuoteEvent(self.ticker, t, bid, ask, _QUOTE_SIZE, _QUOTE_SIZE)
            yield TradeEvent(self.ticker, t, bid, rng.choice(_MAJORITY_SIZES), Side.UNKNOWN)
            t += _LOGICAL_DT

    def _ask_absorption_stream(self) -> Iterator[Event]:
        # Strict mirror: heavy aggressive BUYING into an ask that HOLDS. Every print lifts the
        # offer price (=> Side.BUY) but the ask is re-quoted at the SAME level, so cumulative
        # buy_price_impact stays ~0 (no real upward progress) while ask_refresh_score is high.
        rng = random.Random(self.seed)
        bid, ask = _ABS_BID, _ABS_ASK
        t = 0.0
        for _ in range(_MAX_TICKS):
            yield QuoteEvent(self.ticker, t, bid, ask, _QUOTE_SIZE, _QUOTE_SIZE)
            yield TradeEvent(self.ticker, t, ask, rng.choice(_MAJORITY_SIZES), Side.UNKNOWN)
            t += _LOGICAL_DT


def is_sim_ticker(ticker: str) -> bool:
    return ticker in SIM_SCENARIOS


def build_provider(ticker: str, seed: int = DEFAULT_SEED) -> SimulatedProvider | None:
    """Return a provider for a known sim ticker, or ``None`` (never fabricate one)."""
    scenario = SIM_SCENARIOS.get(ticker)
    if scenario is None:
        return None
    return SimulatedProvider(ticker, scenario, seed)
