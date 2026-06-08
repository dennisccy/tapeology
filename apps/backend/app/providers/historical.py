"""Historical-replay provider: a fetched real window -> the engine's event stream (J-11).

``HistoricalProvider`` implements the same ``Provider`` Protocol the simulator does, so the
engine and API never know the source. Given a ``HistoricalWindow`` of vendor-neutral
``RawTrade`` / ``RawQuote`` records (from the one Alpaca adapter), it yields an ordered
``QuoteEvent`` / ``TradeEvent`` stream:

  * **Logical, not wall-clock, timestamps.** Each record's real UTC epoch is mapped to a
    logical second offset from the window's first event, so the offsets are monotonic
    non-decreasing and the engine stays deterministic (same window => identical features /
    state / confidence). Wall-clock is used only by the feeder to *pace* delivery, never here.
  * **Quote-before-trade at the same instant.** At equal epochs a quote sorts before a trade
    (stable order otherwise preserved), so the in-effect quote is set in ``MarketState`` before
    the trade is classified — exactly what the aggressor classifier relies on.
  * **Trades carry ``Side.UNKNOWN``.** The real feed does not label the aggressor; the engine
    re-derives it from the interleaved quotes (trade price vs. the quote in effect).

``scenario`` is the ``historical <SYM> <window>`` source label, so the row-6 watched-source
descriptor renders verbatim from the canonical snapshot (no client recompute).
"""

from __future__ import annotations

from typing import Iterator

from .adapters.base import HistoricalWindow
from .base import Event, QuoteEvent, Side, TradeEvent

# Sort keys for the merge: at equal epoch, a quote (0) is delivered before a trade (1).
_QUOTE_ORDER = 0
_TRADE_ORDER = 1


class HistoricalProvider:
    """Replays a fetched real window as an ordered, logical-timestamp engine event stream."""

    def __init__(self, ticker: str, window: HistoricalWindow, scenario: str) -> None:
        self.ticker = ticker
        self.scenario = scenario
        self._window = window
        # Canonical display/epoch anchor (row 13, J-31): the first real record's UTC epoch — exactly
        # the ``t0`` ``stream()`` subtracts to build the logical timeline, so the chart maps a logical
        # bin time back to true market clock time as ``epoch_anchor + logical_ts``. Computed ONCE here
        # (the same min-epoch the stream uses) so it is the canonical anchor; ``None`` for an empty
        # window (no first record => no anchor => an empty chart with no fabricated timestamps).
        epochs = [q.epoch for q in window.quotes] + [t.epoch for t in window.trades]
        self.epoch_anchor: float | None = min(epochs) if epochs else None

    def stream(self) -> Iterator[Event]:
        window = self._window
        # (epoch, kind_order, builder) — a stable sort on (epoch, kind_order) keeps quotes
        # before trades at the same instant and preserves input order within each group.
        items: list[tuple[float, int, object]] = []
        for q in window.quotes:
            items.append((q.epoch, _QUOTE_ORDER, q))
        for t in window.trades:
            items.append((t.epoch, _TRADE_ORDER, t))
        if not items:
            return
        items.sort(key=lambda item: (item[0], item[1]))

        t0 = items[0][0]  # window start -> logical zero
        for epoch, kind, record in items:
            ts = epoch - t0  # logical seconds, monotonic non-decreasing
            if kind == _QUOTE_ORDER:
                yield QuoteEvent(
                    self.ticker, ts, record.bid, record.ask, record.bid_size, record.ask_size
                )
            else:
                yield TradeEvent(self.ticker, ts, record.price, record.size, Side.UNKNOWN)
