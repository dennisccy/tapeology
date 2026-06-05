"""Aggressor classification: which side initiated a trade — a two-stage rule.

**Stage 1 — the quote rule (takes precedence).** Using the quote in effect at the trade's
timestamp:

    trade price >= current ask  => aggressive BUY  (someone lifted the offer)
    trade price <= current bid  => aggressive SELL (someone hit the bid)

**Stage 2 — the Lee-Ready tick-test fallback (fires ONLY when stage 1 yields no decision:
no quote in effect, OR the print is strictly between bid and ask).** Compare to the *prior*
trade price:

    price > prior  => BUY   (uptick)
    price < prior  => SELL  (downtick)
    price == prior => carry the last non-zero tick direction (zero-tick)

The one genuinely undecidable case — **no quote AND no prior trade** (or a zero-tick before any
non-zero direction exists) — stays ``UNKNOWN``. The classifier MUST NOT fabricate a side there
(honest-side-inference anti-goal): it never invents a quote or a trade; it reads only the prior
trade price and the carried direction the caller passes in.

The quote passed in MUST be the one in effect at the trade's timestamp, and ``prior_trade_price``
MUST be the price of the immediately preceding trade (not yet overwritten by this one); the engine
guarantees both by processing events in logical-timestamp order (quote before trade) and by
classifying *before* it records the new trade. The function is **pure and deterministic** — its
result depends only on its arguments, with no wall-clock and no randomness — so the same ordered
stream yields identical sides (determinism anti-goal). It operates only on ``TradeEvent`` /
``QuoteEvent`` / ``Side`` and never on a vendor type (provider-agnostic anti-goal).
"""

from __future__ import annotations

from ..providers.base import QuoteEvent, Side, TradeEvent


def classify_aggressor(
    trade: TradeEvent,
    quote: QuoteEvent | None,
    prior_trade_price: float | None = None,
    last_tick_dir: Side | None = None,
) -> Side:
    # --- Stage 1: the quote rule (precedence) ---
    if quote is not None:
        if trade.price >= quote.ask:
            return Side.BUY
        if trade.price <= quote.bid:
            return Side.SELL
        # Strictly between bid and ask -> fall through to the tick test.

    # --- Stage 2: the Lee-Ready tick-test fallback ---
    # Reached only when stage 1 was undecided: no quote in effect, or a strictly mid-spread print.
    if prior_trade_price is None:
        return Side.UNKNOWN  # no quote AND no prior trade: the one honest-undecidable case
    if trade.price > prior_trade_price:
        return Side.BUY
    if trade.price < prior_trade_price:
        return Side.SELL
    # Zero-tick: carry the last non-zero tick direction (UNKNOWN if none exists yet).
    return last_tick_dir if last_tick_dir is not None else Side.UNKNOWN
