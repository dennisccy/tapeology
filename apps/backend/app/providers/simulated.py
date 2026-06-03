"""Deterministic, seedable simulated provider (Phase-1 data source).

All five reserved sim tickers are now driven to their target reads:
``SIM-BUYER`` / ``SIM-SELLER`` (directional control), ``SIM-BIDABS`` / ``SIM-ASKABS``
(absorption), and ``SIM-CHOP`` (the honest non-call: a genuinely choppy stream that warms
up and still reads ``unclear``). Same seed => identical stream (determinism anti-goal): all
randomness comes from a seeded ``random.Random`` and every event carries a logical timestamp,
never wall-clock. Wall-clock is used only by the feeder to *pace delivery* in live mode.

The numbers below are scenario *shape* (the data the simulator emits), not engine
thresholds — engine/classifier thresholds live in ``app.config``.
"""

from __future__ import annotations

import random
from typing import Iterator

from .base import Event, QuoteEvent, Side, TradeEvent

# Reserved sim tickers -> target tape state. All five are now driven to their read.
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

# --- Choppy / unclear scenario shape (SIM-CHOP) — the honest non-call ----------------------
# A genuinely choppy tape: balanced two-sided aggression at a WIDE, jittery spread, around a
# price that goes NOWHERE. By DEFENSE IN DEPTH every rolling window denies all four gates AT
# ONCE — each condition alone makes every gate impossible, so no single window's noise can trip
# one:
#   * the aggressive side strictly ALTERNATES at a CONSTANT size, so both aggressive_buy_ratio
#     and aggressive_sell_ratio stay ~0.50 (below their 0.60 floors) in every window;
#   * the spread is always >= _CHOP_SPREAD_MIN = 0.10 > max_stable_spread (0.06), so the
#     average spread is wide in every window;
#   * the QUOTE's near side jitters (the ask backs off BELOW the center on buy ticks, the bid
#     above it on sell ticks), so on the matching prints the bid keeps dropping below its prior
#     high and the ask rising above its prior low — both refresh scores stay below 0.55.
# Crucially EVERY aggressive print lands at exactly _CHOP_CENTER (the buy lifts an ask placed
# at/under the center; the sell hits a bid placed at/over it), so successive prints are at the
# SAME price and the per-side price impact is ~ZERO — no fabricated decisive progress on either
# side (a genuinely choppy tape shows smaller impact than even a real directional one). Because
# the impact is zero by construction regardless of trade density, the stream can be dense (small
# _CHOP_DT) so even the short 10s window stays well-populated and its refresh score stays low.
# The engine warms up on real data and still honestly declines to call a side: the inverse,
# equally-earned counterpart to the four resolved states (NOT the cold-start silence of an
# undriven ticker). These are scenario DATA (simulator shape), never engine thresholds.
_CHOP_CENTER = 100.00          # every aggressive print lands here; the price never progresses
_CHOP_QUOTE_JITTER = 0.10      # the near quote backs off from center by uniform(0, this) — wide
                               # enough that the matching side keeps failing to refresh (low
                               # refresh in EVERY window, even the noise-prone 10s)
_CHOP_SPREAD_MIN = 0.10        # min spread (> max_stable_spread 0.06) — hangs off the far side
_CHOP_SPREAD_MAX = 0.20        # max spread (wide and jittery)
_CHOP_SIZE = 200               # constant size => volume ratio == count ratio (robust balance)
_CHOP_P_MID_PRINT = 0.08       # share of prints landing mid-spread (Side.UNKNOWN, no clean aggressor)
_CHOP_DT = 0.2                 # logical seconds per tick — dense enough that even the short 10s
                               # window holds plenty of prints, so its refresh score stays low too


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
        elif self.ticker == "SIM-CHOP":
            yield from self._chop_stream()

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

    def _chop_stream(self) -> Iterator[Event]:
        # Genuinely choppy / unclear tape (see the _CHOP_* shape notes above). The aggressive
        # side strictly ALTERNATES (a deterministic toggle, not the RNG), so the buy/sell volume
        # stays balanced and BOTH ratios stay sub-floor in every window. Each tick the near side
        # of the quote backs off from the center by a jittery amount and the wide spread hangs
        # off the far side: on a BUY tick the ask sits at/under the center (spread below it), on
        # a SELL tick the bid sits at/over the center (spread above it). The aggressive print
        # lands at exactly the center, so it lifts that ask (=> BUY) or hits that bid (=> SELL)
        # while EVERY print is at the SAME price — per-side price impact is ~zero (no progress).
        # The jittering near side means the quote never holds a level, so neither bid nor ask
        # "refreshes". A mid-spread minority prints strictly inside the quote (Side.UNKNOWN — no
        # clean aggressor). Unclear by genuinely MIXED signals, not by an empty/cold stream.
        rng = random.Random(self.seed)
        t = 0.0
        next_aggressor = Side.BUY
        for _ in range(_MAX_TICKS):
            backoff = rng.uniform(0.0, _CHOP_QUOTE_JITTER)
            spread = rng.uniform(_CHOP_SPREAD_MIN, _CHOP_SPREAD_MAX)
            is_mid = rng.random() < _CHOP_P_MID_PRINT

            if is_mid:
                # Mid-spread tick: a WIDE quote straddling the center, print AT the center =>
                # strictly between bid and ask => Side.UNKNOWN (no clean aggressor). The print is
                # still at the center, so it adds no price impact; the pending side is untouched,
                # so the buy/sell alternation stays balanced.
                bid = round(_CHOP_CENTER - spread / 2, 2)
                ask = round(_CHOP_CENTER + spread / 2, 2)
                yield QuoteEvent(self.ticker, t, bid, ask, _QUOTE_SIZE, _QUOTE_SIZE)
                yield TradeEvent(self.ticker, t, _CHOP_CENTER, _CHOP_SIZE, Side.UNKNOWN)
            elif next_aggressor is Side.BUY:
                ask = round(_CHOP_CENTER - backoff, 2)   # near side at/under the center
                bid = round(ask - spread, 2)             # wide spread below
                yield QuoteEvent(self.ticker, t, bid, ask, _QUOTE_SIZE, _QUOTE_SIZE)
                # Lift the offer at the center: center >= ask => engine tags it Side.BUY.
                yield TradeEvent(self.ticker, t, _CHOP_CENTER, _CHOP_SIZE, Side.UNKNOWN)
                next_aggressor = Side.SELL
            else:
                bid = round(_CHOP_CENTER + backoff, 2)   # near side at/over the center
                ask = round(bid + spread, 2)             # wide spread above
                yield QuoteEvent(self.ticker, t, bid, ask, _QUOTE_SIZE, _QUOTE_SIZE)
                # Hit the bid at the center: center <= bid => engine tags it Side.SELL.
                yield TradeEvent(self.ticker, t, _CHOP_CENTER, _CHOP_SIZE, Side.UNKNOWN)
                next_aggressor = Side.BUY
            t += _CHOP_DT


def is_sim_ticker(ticker: str) -> bool:
    return ticker in SIM_SCENARIOS


def build_provider(ticker: str, seed: int = DEFAULT_SEED) -> SimulatedProvider | None:
    """Return a provider for a known sim ticker, or ``None`` (never fabricate one)."""
    scenario = SIM_SCENARIOS.get(ticker)
    if scenario is None:
        return None
    return SimulatedProvider(ticker, scenario, seed)
