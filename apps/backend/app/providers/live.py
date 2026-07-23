"""Live-streaming provider: an adapter's async neutral feed -> the engine's event stream (J-12).

``LiveProvider`` is the async counterpart to ``HistoricalProvider``: it implements the
``AsyncProvider`` Protocol, so the engine and API never know the source. Given an async,
**unbounded** stream of vendor-neutral ``RawTrade`` / ``RawQuote`` records (from the one Alpaca
adapter's ``stream_live``), it yields an ordered ``QuoteEvent`` / ``TradeEvent`` stream:

  * **Logical, not wall-clock, timestamps.** The first record's real UTC epoch maps to logical
    zero; every later record maps to ``epoch - t0``, clamped to be **monotonic non-decreasing**
    so the engine stays deterministic (a real feed can deliver a trade and its quote a few
    milliseconds out of order — clamping keeps the engine's rolling windows well-formed). This is
    the same neutral->logical mapping ``HistoricalProvider`` does, but streaming/unbounded.
  * **Arrival order preserved (quote-before-trade at the same instant).** Unlike the historical
    window, an unbounded live stream cannot be globally sorted; the adapter delivers records in
    arrival order (the quote update ahead of the trade when both are present) and this provider
    preserves it, so the in-effect quote is set in ``MarketState`` before the trade is classified.
  * **Trades carry ``Side.UNKNOWN``.** The real feed does not label the aggressor; the engine
    re-derives it from the interleaved quotes (trade price vs. the quote in effect).

``scenario`` is the ``live <SYM>`` source label, rendered verbatim from the canonical snapshot
(row-6 watched-source descriptor; no client recompute). This module imports **no** vendor SDK —
the live socket lives solely behind the adapter's neutral ``stream_live``.
"""

from __future__ import annotations

from typing import AsyncIterator, Union

from .adapters.base import RawQuote, RawTrade
from .base import Event, QuoteEvent, Side, TradeEvent

RawRecord = Union[RawTrade, RawQuote]


class LiveProvider:
    """Maps an adapter's async neutral record stream onto the engine's logical event stream."""

    def __init__(
        self, ticker: str, raw_stream: AsyncIterator[RawRecord], scenario: str
    ) -> None:
        self.ticker = ticker
        self.scenario = scenario
        self._raw_stream = raw_stream
        # Canonical display/epoch anchor (row 13, J-31): a live feed's first real epoch is only
        # known once the first record arrives, so this starts None and is stamped ONCE in
        # ``stream`` from the first record's epoch (the SAME t0 the logical timeline subtracts, so
        # true_clock = anchor + logical_ts). The feeder reads it off the provider and stamps the
        # engine before the first event, so the cockpit chart renders live moving bars on the real
        # clock — the earlier "the chart is sim/historical-only" rationale no longer holds.
        self.epoch_anchor: float | None = None

    async def stream(self) -> AsyncIterator[Event]:
        raw = self._raw_stream
        t0: float | None = None
        last_ts = 0.0
        try:
            async for record in raw:
                if t0 is None:
                    t0 = record.epoch
                    # Stamp the display anchor from the first record's real epoch, BEFORE yielding
                    # it, so the feeder (draining this generator) sees the anchor by the time it
                    # dequeues the first event. Set-once (t0 is set-once per stream()).
                    self.epoch_anchor = t0
                ts = record.epoch - t0
                if ts < last_ts:
                    ts = last_ts  # monotonic non-decreasing (engine determinism)
                last_ts = ts
                if isinstance(record, RawQuote):
                    yield QuoteEvent(
                        self.ticker,
                        ts,
                        record.bid,
                        record.ask,
                        record.bid_size,
                        record.ask_size,
                    )
                else:
                    yield TradeEvent(self.ticker, ts, record.price, record.size, Side.UNKNOWN)
        finally:
            # Cascade close into the underlying adapter stream so its socket is closed even when
            # this generator is aclose()d/cancelled mid-iteration (no leaked vendor connection).
            aclose = getattr(raw, "aclose", None)
            if aclose is not None:
                await aclose()
