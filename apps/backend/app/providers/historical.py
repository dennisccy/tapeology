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

from typing import Iterable, Iterator

from .adapters.base import HistoricalWindow
from .base import Event, QuoteEvent, Side, TradeEvent

# Sort keys for the merge: at equal epoch, a quote (0) is delivered before a trade (1).
_QUOTE_ORDER = 0
_TRADE_ORDER = 1


def _ordered_items(window: HistoricalWindow) -> list[tuple[float, int, object]]:
    """(epoch, kind_order, record) for one window, stably sorted (quote-before-trade at equal epoch)."""
    items: list[tuple[float, int, object]] = []
    for q in window.quotes:
        items.append((q.epoch, _QUOTE_ORDER, q))
    for t in window.trades:
        items.append((t.epoch, _TRADE_ORDER, t))
    items.sort(key=lambda item: (item[0], item[1]))
    return items


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
        # (epoch, kind_order, record) — a stable sort on (epoch, kind_order) keeps quotes before
        # trades at the same instant and preserves input order within each group.
        items = _ordered_items(self._window)
        if not items:
            return
        t0 = items[0][0]  # window start -> logical zero
        for epoch, kind, record in items:
            ts = epoch - t0  # logical seconds, monotonic non-decreasing
            if kind == _QUOTE_ORDER:
                yield QuoteEvent(
                    self.ticker, ts, record.bid, record.ask, record.bid_size, record.ask_size
                )
            else:
                yield TradeEvent(self.ticker, ts, record.price, record.size, Side.UNKNOWN)


class ProgressiveHistoricalProvider:
    """Replays a LONG window as an ordered engine stream consuming epoch-ordered CHUNKS lazily (J-37).

    Same ``Provider`` Protocol as ``HistoricalProvider`` (the engine/API never know the source), but
    fed by an ITERABLE of ``HistoricalWindow`` sub-windows in epoch order (from the adapter's lazy
    ``iter_historical_chunks``) instead of one materialised window. ``stream()`` pulls one chunk at a
    time and yields its events, so the feeder begins replaying the FIRST chunk after only that chunk's
    fetch latency while later chunks are fetched as the iterator advances — time-to-first-data is
    decoupled from total-window load (the iter-13 stall fixed).

    CORRECTNESS = a single-shot fetch (single source of truth + determinism preserved):
      * The first chunk's first record fixes ``t0`` (the canonical epoch anchor, row 13), exactly as
        the single-window provider's window-start; every later event maps to ``epoch - t0``.
      * Each chunk is internally epoch-sorted (quote-before-trade at equal epoch). Because the
        adapter's sub-windows PARTITION ``[start, end)`` with no overlap and no gap, every record in
        chunk k has an epoch < every record in chunk k+1 (a quiet boundary), so concatenating chunks
        in order yields the SAME globally epoch-ordered, monotonic-ts stream a single-window fetch of
        the same records would — nothing fabricated, dropped, reordered, or de-duplicated. The engine
        bins on its logical timeline, so progressive vs. single-shot yields identical features/state.

    The first chunk is peeked eagerly in ``__init__`` so the epoch anchor is known the moment the
    watch is created (the chart/anchor is correct from the first frame); remaining chunks stay lazy.
    """

    def __init__(self, ticker: str, chunks: Iterable[HistoricalWindow], scenario: str) -> None:
        self.ticker = ticker
        self.scenario = scenario
        self._iter = iter(chunks)
        # Peek the first NON-EMPTY chunk so the epoch anchor (row 13) is set up front; buffer it for
        # stream(). An all-empty window leaves the anchor None (an empty chart, no fabricated stamp).
        self._first: HistoricalWindow | None = None
        self._t0: float | None = None
        for chunk in self._iter:
            items = _ordered_items(chunk)
            if items:
                self._first = chunk
                self._t0 = items[0][0]
                break
        self.epoch_anchor: float | None = self._t0

    def stream(self) -> Iterator[Event]:
        if self._t0 is None:
            return  # all chunks empty — nothing to replay (no fabricated record)
        t0 = self._t0
        # Yield the already-peeked first chunk, then continue pulling remaining chunks lazily. Each
        # chunk is internally ordered; chunks are globally ordered by the partition, so the merged
        # stream is monotonic in ts without re-sorting across the boundary.
        first = self._first
        if first is not None:
            yield from self._emit(first, t0)
        for chunk in self._iter:
            yield from self._emit(chunk, t0)

    def _emit(self, window: HistoricalWindow, t0: float) -> Iterator[Event]:
        for epoch, kind, record in _ordered_items(window):
            ts = epoch - t0  # logical seconds, monotonic non-decreasing across the whole window
            if kind == _QUOTE_ORDER:
                yield QuoteEvent(
                    self.ticker, ts, record.bid, record.ask, record.bid_size, record.ask_size
                )
            else:
                yield TradeEvent(self.ticker, ts, record.price, record.size, Side.UNKNOWN)
