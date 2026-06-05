"""Engine price-history buffer: OHLC candles (per bar size) + tape-state-transition markers.

This is the ONE place price candles and tape-state markers are computed (anti-goal: one focused
chart, computed once). It is owned by ``TapeEngine`` and fed only from ``process_event`` — never
from a status flip or construction — so a ``set_stream_status`` call cannot mutate the series.

It introduces **no** second classifier and **no** second price source:
  * Candles bin the SAME trade ``price`` the engine already derives (the value the snapshot
    exposes as ``last``); quotes do not create candles, and an empty bin is never invented.
  * Markers carry the SAME ``state`` / ``confidence`` the ``TapeStateClassifier`` already produced
    for that tick (passed in from the engine) — the buffer re-classifies nothing.

Binning is by the engine's **logical** timestamp (wall-clock never enters here), so replaying the
same ordered event stream yields byte-identical bars + markers (determinism anti-goal). The
``GET /tape/{ticker}/history?bar=`` projection is a pure read of this buffer.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Config


@dataclass(frozen=True)
class OhlcBar:
    """One candle: open/high/low/close of the watched price over a logical-time bin.

    ``start`` is the bin's left edge in LOGICAL seconds (``floor(ts / bar) * bar``); a bar is
    emitted only for a bin that contained at least one trade.
    """

    start: float
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class TapeMarker:
    """A meaningful tape-state-transition marker: state + confidence at a logical timestamp.

    ``state`` / ``confidence`` are the classifier's own values for that tick (re-used verbatim,
    never recomputed). A marker exists only for a transition INTO a meaningful state; a transition
    into ``unclear`` is not marked.
    """

    timestamp: float
    state: str
    confidence: float


class _BarAccumulator:
    """Mutable OHLC accumulator for a single bar size; frozen ``OhlcBar``s are read off it."""

    def __init__(self, bar_size: int, max_bars: int) -> None:
        self._bar_size = bar_size
        self._max_bars = max_bars
        # Bin left-edge -> mutable [open, high, low, close]; insertion order is time order
        # because logical timestamps arrive monotonically non-decreasing.
        self._bars: dict[float, list[float]] = {}

    def add(self, timestamp: float, price: float) -> None:
        start = (timestamp // self._bar_size) * self._bar_size
        existing = self._bars.get(start)
        if existing is None:
            self._bars[start] = [price, price, price, price]
            # Bound retained candles (Phase-1 in-memory): drop the oldest bins.
            while len(self._bars) > self._max_bars:
                oldest = next(iter(self._bars))
                del self._bars[oldest]
        else:
            existing[1] = max(existing[1], price)  # high
            existing[2] = min(existing[2], price)  # low
            existing[3] = price                    # close (latest trade in the bin)

    def bars(self) -> tuple[OhlcBar, ...]:
        return tuple(
            OhlcBar(start=start, open=o, high=h, low=lo, close=c)
            for start, (o, h, lo, c) in self._bars.items()
        )


class HistoryBuffer:
    """Accumulates OHLC candles at every configured bar size + meaningful-transition markers."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._meaningful = frozenset(config.history_marker_states)
        self._accumulators: dict[int, _BarAccumulator] = {
            size: _BarAccumulator(size, config.history_max_bars)
            for size in config.history_bar_sizes
        }
        self._markers: list[TapeMarker] = []
        # The previously classified state, to detect a transition. Seeded None so the FIRST
        # classified meaningful state is itself a transition that earns a marker.
        self._prev_state: str | None = None

    @property
    def bar_sizes(self) -> tuple[int, ...]:
        return self._config.history_bar_sizes

    def add_trade(self, timestamp: float, price: float) -> None:
        """Bin one trade price into every concurrent bar size (logical-ts bucketing)."""
        for accumulator in self._accumulators.values():
            accumulator.add(timestamp, price)

    def note_state(self, timestamp: float, state: str, confidence: float) -> None:
        """Record a marker iff the classified state CHANGED to a meaningful state.

        ``state`` / ``confidence`` are the classifier's own values for this tick — stored
        verbatim (single source of truth). A transition into ``unclear`` (or no change) records
        nothing; a transition into a meaningful state appends one marker.
        """
        if state != self._prev_state:
            if state in self._meaningful:
                self._markers.append(TapeMarker(timestamp, state, confidence))
                # Bound retained markers (Phase-1 in-memory): drop the oldest.
                if len(self._markers) > self._config.history_max_markers:
                    del self._markers[0]
            self._prev_state = state

    def bars(self, bar_size: int) -> tuple[OhlcBar, ...]:
        """The OHLC series for one configured bar size (empty until a trade lands)."""
        accumulator = self._accumulators.get(bar_size)
        if accumulator is None:
            raise ValueError(f"unsupported bar size: {bar_size}")
        return accumulator.bars()

    def markers(self) -> tuple[TapeMarker, ...]:
        """The meaningful tape-state-transition markers (shared across bar sizes)."""
        return tuple(self._markers)
