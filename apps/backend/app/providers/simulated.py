"""Deterministic, seedable simulated provider (Phase-1 data source).

Only ``SIM-BUYER`` is driven to its target state this iteration; the other sim tickers are
reserved in the registry (so they are *known*, not fabricated) but are not driven to their
states yet. Same seed => identical stream (determinism anti-goal): all randomness comes
from a seeded ``random.Random`` and every event carries a logical timestamp, never
wall-clock. Wall-clock is used only by the feeder to *pace delivery* in live mode.

The numbers below are scenario *shape* (the data the simulator emits), not engine
thresholds — engine/classifier thresholds live in ``app.config``.
"""

from __future__ import annotations

import random
from typing import Iterator

from .base import Event, QuoteEvent, Side, TradeEvent

# Reserved sim tickers -> target tape state. Only SIM-BUYER resolves this iteration.
SIM_SCENARIOS: dict[str, str] = {
    "SIM-BUYER": "buyer_control",
    "SIM-SELLER": "seller_control",
    "SIM-BIDABS": "bid_absorption",
    "SIM-ASKABS": "ask_absorption",
    "SIM-CHOP": "unclear_chop",
}

DEFAULT_SEED = 7

# --- SIM-BUYER scenario shape -----------------------------------------------------------
_START_BID = 100.00
_START_ASK = 100.02          # spread held at 0.02 (narrow / stable)
_PRICE_TICK = 0.01
_LOGICAL_DT = 0.5            # logical seconds between ticks
_QUOTE_SIZE = 800
_P_SELL = 0.12              # minority of prints are aggressive sells
_P_LIFT_ON_BUY = 0.5       # chance a buy tick lifts the offer (=> price progress)
_BUY_SIZES = (100, 200, 300, 600)   # 600 >= large_print_size
_SELL_SIZES = (100, 200)
_MAX_TICKS = 5000          # bounded stream


class SimulatedProvider:
    def __init__(self, ticker: str, scenario: str, seed: int = DEFAULT_SEED) -> None:
        self.ticker = ticker
        self.scenario = scenario
        self.seed = seed

    def stream(self) -> Iterator[Event]:
        if self.ticker == "SIM-BUYER":
            yield from self._buyer_control_stream()
        # Reserved scenarios produce no events this iteration: the engine stays an honest
        # cold-start `unclear` rather than fabricating a resolved state.

    def _buyer_control_stream(self) -> Iterator[Event]:
        rng = random.Random(self.seed)
        bid, ask = _START_BID, _START_ASK
        t = 0.0
        for _ in range(_MAX_TICKS):
            is_buy = rng.random() >= _P_SELL
            if is_buy and rng.random() < _P_LIFT_ON_BUY:
                # Aggressive buyers consume the offer and lift the quote one tick.
                bid = round(bid + _PRICE_TICK, 2)
                ask = round(ask + _PRICE_TICK, 2)

            yield QuoteEvent(self.ticker, t, bid, ask, _QUOTE_SIZE, _QUOTE_SIZE)
            if is_buy:
                yield TradeEvent(self.ticker, t, ask, rng.choice(_BUY_SIZES), Side.UNKNOWN)
            else:
                yield TradeEvent(self.ticker, t, bid, rng.choice(_SELL_SIZES), Side.UNKNOWN)
            t += _LOGICAL_DT


def is_sim_ticker(ticker: str) -> bool:
    return ticker in SIM_SCENARIOS


def build_provider(ticker: str, seed: int = DEFAULT_SEED) -> SimulatedProvider | None:
    """Return a provider for a known sim ticker, or ``None`` (never fabricate one)."""
    scenario = SIM_SCENARIOS.get(ticker)
    if scenario is None:
        return None
    return SimulatedProvider(ticker, scenario, seed)
