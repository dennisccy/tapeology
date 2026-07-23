"""Engine price-history buffer: OHLC candles (per bar size) + tape-state-transition markers.

This is the ONE place price candles and tape-state markers are computed (anti-goal: one focused
chart, computed once). It is owned by ``TapeEngine`` and fed only from ``process_event`` — never
from a status flip or construction — so a ``set_stream_status`` call cannot mutate the series.

It introduces **no** second classifier and **no** second price source:
  * Candles bin the SAME trade ``price`` the engine already derives (the value the snapshot
    exposes as ``last``); quotes do not create candles, and an empty bin is never invented.
  * Markers carry the SAME ``state`` / ``confidence`` the ``TapeStateClassifier`` already produced
    for that tick (passed in from the engine) — the buffer re-classifies nothing.

The logical-second candles (``bars(bar_size)``) bin by the engine's **logical** timestamp
(wall-clock never enters there), so replaying the same ordered event stream yields byte-identical
bars + markers (determinism anti-goal). The ``GET /tape/{ticker}/history?bar=`` projection is a
pure read of that buffer.

Additively (the cockpit's "history" chart mode), the buffer ALSO bins each trade into wall-clock
aligned **timeframe** candles (``timeframe_bars(tf)``) with volume — the SAME live moving bars the
recorded store carries, so a replay's live bars line up on the store's real-epoch grid. Those need
the display ``epoch_anchor`` to map a logical ts to a real instant; while the anchor is unset the
timeframe series stays empty (honest absence, no fabricated backfill). Timeframe binning is display
metadata only — it never enters ``classify(...)``; the logical candles/markers/classification are
byte-identical whether or not an anchor is attached.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Config

# The wall-clock timeframes the tape can honestly bin its live moving bars into: fixed-DURATION
# buckets only, so ``floor(real_epoch / seconds) * seconds`` is a real grid edge. ``1w``/``1mo``
# are deliberately ABSENT — an epoch-week floor is Thursday-anchored (it disagrees with the store's
# Monday-anchored weekly rows) and a month is calendar-irregular, so a fixed-seconds floor would
# fabricate a boundary; a tape session never spans either anyway. The buffer accumulates the subset
# of these that the store also records (``config.bar_timeframes``), so a new bar-timeframe knob adds
# no field here and mints no new fingerprint (``bar_timeframes`` is fingerprint-excluded).
TIMEFRAME_SECONDS: dict[str, int] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "8h": 28800,
    "1d": 86400,
}


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


@dataclass(frozen=True)
class TimeframeBar:
    """One wall-clock candle: OHLC + volume of the watched price over a real-epoch timeframe bucket.

    ``ts`` is the bucket's left edge in REAL UTC epoch seconds (``floor((anchor + logical_ts) /
    tf_seconds) * tf_seconds``) — the SAME grid the recorded bar store uses, so a replay's live
    bars align with the store's candles. ``volume`` sums the ``TradeEvent.size`` of every trade in
    the bucket. A bar exists only for a bucket that contained at least one trade.
    """

    ts: float
    open: float
    high: float
    low: float
    close: float
    volume: int


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


class _TimeframeAccumulator:
    """Mutable OHLC+volume accumulator for a single wall-clock timeframe.

    Mirrors ``_BarAccumulator`` (same oldest-drop bound, insertion-order-is-time-order) but keys on
    the REAL-epoch bucket left edge and accrues per-bucket volume; frozen ``TimeframeBar``s are
    read off it.
    """

    def __init__(self, tf_seconds: int, max_bars: int) -> None:
        self._tf_seconds = tf_seconds
        self._max_bars = max_bars
        # Bucket left-edge (real UTC epoch) -> mutable [open, high, low, close, volume]; insertion
        # order is time order because real timestamps (anchor + a non-decreasing logical ts) arrive
        # monotonically non-decreasing.
        self._bars: dict[float, list[float]] = {}

    def add(self, real_ts: float, price: float, size: int) -> None:
        start = (real_ts // self._tf_seconds) * self._tf_seconds
        existing = self._bars.get(start)
        if existing is None:
            self._bars[start] = [price, price, price, price, float(size)]
            # Bound retained candles (Phase-1 in-memory): drop the oldest buckets.
            while len(self._bars) > self._max_bars:
                oldest = next(iter(self._bars))
                del self._bars[oldest]
        else:
            existing[1] = max(existing[1], price)  # high
            existing[2] = min(existing[2], price)  # low
            existing[3] = price                    # close (latest trade in the bucket)
            existing[4] += float(size)             # volume (sum of trade sizes)

    def bars(self) -> tuple[TimeframeBar, ...]:
        return tuple(
            TimeframeBar(ts=start, open=o, high=h, low=lo, close=c, volume=int(v))
            for start, (o, h, lo, c, v) in self._bars.items()
        )


class HistoryBuffer:
    """Accumulates OHLC candles at every configured bar size + meaningful-transition markers."""

    def __init__(self, config: Config, epoch_anchor: float | None = None) -> None:
        self._config = config
        # The real-epoch display anchor (row 13, J-31): the wall clock that logical-time 0 maps to.
        # Needed ONLY by the wall-clock timeframe accumulators (the logical-second bars never use
        # it). ``None`` until known (live mode learns it at the first record via set_epoch_anchor).
        self._epoch_anchor = epoch_anchor
        self._meaningful = frozenset(config.history_marker_states)
        self._accumulators: dict[int, _BarAccumulator] = {
            size: _BarAccumulator(size, config.history_max_bars)
            for size in config.history_bar_sizes
        }
        # Wall-clock timeframe accumulators (the cockpit "history" mode): the subset of
        # TIMEFRAME_SECONDS the store also records (config.bar_timeframes), in config order. No new
        # Config field — the set derives from the fingerprint-excluded ``bar_timeframes`` and reuses
        # the ``history_max_bars`` bound, so the config fingerprint is unchanged.
        self._tf_accumulators: dict[str, _TimeframeAccumulator] = {
            tf: _TimeframeAccumulator(TIMEFRAME_SECONDS[tf], config.history_max_bars)
            for tf in config.bar_timeframes
            if tf in TIMEFRAME_SECONDS
        }
        self._markers: list[TapeMarker] = []
        # The previously classified state, to detect a transition. Seeded None so the FIRST
        # classified meaningful state is itself a transition that earns a marker.
        self._prev_state: str | None = None

    @property
    def bar_sizes(self) -> tuple[int, ...]:
        return self._config.history_bar_sizes

    @property
    def timeframes(self) -> tuple[str, ...]:
        """The wall-clock timeframes this buffer accumulates, in config order — the
        ``?timeframe=`` endpoint's validation source (an out-of-set value is a 422)."""
        return tuple(self._tf_accumulators.keys())

    def set_epoch_anchor(self, anchor: float) -> None:
        """Stamp the real-epoch display anchor ONCE (live mode learns it at the first record).

        Set-once: a second call is a no-op (the anchor never changes mid-watch). Only trades added
        AFTER this stamp bin into the timeframe accumulators — there is no retro-binning of trades
        that arrived while anchorless (an honest "we did not know the wall clock yet", never a
        fabricated backfill). The logical-second ``bars(...)`` series is unaffected by the anchor.
        """
        if self._epoch_anchor is not None:
            return
        self._epoch_anchor = anchor

    def add_trade(self, timestamp: float, price: float, size: int = 0) -> None:
        """Bin one trade into every logical-second bar size AND, once a real-epoch anchor is known,
        into every wall-clock timeframe (with volume).

        The logical-second binning runs FIRST and is byte-identical to before this capability. The
        wall-clock timeframe binning is additive: it maps the logical ts to a real instant
        (``anchor + timestamp``), so it is skipped entirely while the anchor is unset (an anchorless
        engine accumulates no timeframe bars — honest absence). ``size`` defaults to 0 so every
        pre-existing caller is unchanged (its timeframe volume, when an anchor is later set, is 0).
        """
        for accumulator in self._accumulators.values():
            accumulator.add(timestamp, price)
        if self._epoch_anchor is not None and self._tf_accumulators:
            real = self._epoch_anchor + timestamp
            for tf_acc in self._tf_accumulators.values():
                tf_acc.add(real, price, size)

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

    def timeframe_bars(self, timeframe: str) -> tuple[TimeframeBar, ...]:
        """The wall-clock OHLC+volume series for one supported timeframe (empty until a trade lands
        with an anchor set). Raises ``ValueError`` for an unsupported timeframe (mirrors ``bars``)."""
        accumulator = self._tf_accumulators.get(timeframe)
        if accumulator is None:
            raise ValueError(f"unsupported timeframe: {timeframe}")
        return accumulator.bars()

    def anchor_bucket_start(self, timeframe: str) -> float | None:
        """The real-epoch left edge of the bucket the anchor falls in, for one supported timeframe:
        ``floor(anchor / tf_seconds) * tf_seconds``. ``None`` when there is no anchor.

        This is the NO-LOOKAHEAD boundary the cockpit chart clamps its recorded-bar window against:
        store bars strictly before it are context; the anchor bucket and everything after it are the
        live tape's own moving bars (drawing the store's anchor-bucket bar would embed
        post-replay-start ticks). Raises ``ValueError`` for an unsupported timeframe.
        """
        if timeframe not in self._tf_accumulators:
            raise ValueError(f"unsupported timeframe: {timeframe}")
        if self._epoch_anchor is None:
            return None
        secs = TIMEFRAME_SECONDS[timeframe]
        return (self._epoch_anchor // secs) * secs

    def markers(self) -> tuple[TapeMarker, ...]:
        """The meaningful tape-state-transition markers (shared across bar sizes)."""
        return tuple(self._markers)
