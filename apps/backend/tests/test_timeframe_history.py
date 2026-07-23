"""Wall-clock timeframe candles in the engine history buffer (cockpit "history" chart mode).

The buffer bins each trade into wall-clock-aligned OHLC+volume candles at the fixed-duration
timeframes the store also records — the SAME live moving bars a recorded series carries, so a
replay's live bars line up on the store's real-epoch grid. These assert the binning is honest:

  * the supported set is the fixed-duration subset of ``config.bar_timeframes`` (1w/1mo excluded);
  * buckets are ``floor((anchor + logical_ts) / tf_seconds) * tf_seconds`` (real-epoch aligned,
    correct even for an anchor that is not a bucket multiple — the sim 14:30 anchor);
  * volume sums the trade sizes, OHLC is the first/max/min/last price in the bucket;
  * an anchorless buffer accumulates NO timeframe bars (honest absence) while its logical-second
    ``bars(...)`` series is entirely unchanged (the anchor never touches the logical timeline);
  * ``set_epoch_anchor`` is set-once and bins only trades that arrive AFTER it (no retro-binning);
  * the additive size/anchor wiring perturbs neither the logical bars nor the markers (determinism).
"""

from __future__ import annotations

from app.config import CONFIG
from app.engine.history import TIMEFRAME_SECONDS, HistoryBuffer

# 2024-01-02T14:30:00Z — the config sim session-start. mod 3600 == 1800 and mod 300 == 0: an
# "odd" anchor that is NOT an hour multiple, so a naive logical-second fold would misplace OHLC.
SIM_ANCHOR = 1704205800.0


def _buffer(anchor: float | None = SIM_ANCHOR) -> HistoryBuffer:
    return HistoryBuffer(CONFIG, epoch_anchor=anchor)


# --- The supported timeframe set ----------------------------------------------------------

def test_timeframe_set_is_fixed_duration_subset_of_bar_timeframes():
    # Only fixed-DURATION timeframes are honestly floorable; 1w (Thursday-anchored epoch weeks) and
    # 1mo (calendar-irregular) are deliberately absent even though they are valid bar_timeframes.
    hb = _buffer()
    assert set(hb.timeframes) == set(TIMEFRAME_SECONDS)
    assert "1w" not in hb.timeframes and "1mo" not in hb.timeframes
    # Config order preserved (the intersection walks config.bar_timeframes), shortest-first here.
    expected = tuple(tf for tf in CONFIG.bar_timeframes if tf in TIMEFRAME_SECONDS)
    assert hb.timeframes == expected


def test_supported_seconds_are_the_canonical_durations():
    assert TIMEFRAME_SECONDS == {
        "1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "8h": 28800, "1d": 86400,
    }


# --- Wall-clock bucketing (real-epoch aligned) --------------------------------------------

def test_wall_aligned_bucketing_with_half_hour_anchor():
    # anchor 14:30:00Z. At 1h, logical 0 and 1799 fall in the HONEST partial 14:00 bucket; logical
    # 1800 opens the 15:00 bucket. The bucket edges are real-clock hour boundaries, not anchor+N*3600.
    hb = _buffer()
    hb.add_trade(0.0, 100.0, 1)
    hb.add_trade(1799.0, 101.0, 1)
    hb.add_trade(1800.0, 102.0, 1)
    bars = hb.timeframe_bars("1h")
    starts = [b.ts for b in bars]
    assert starts == [1704204000.0, 1704207600.0]  # 14:00:00Z, 15:00:00Z
    # The anchor's own bucket is the 14:00 one (floor(anchor/3600)*3600).
    assert hb.anchor_bucket_start("1h") == 1704204000.0


def test_ohlc_within_bucket():
    hb = _buffer()
    # Four trades in the same 1m bucket (anchor is on a 5m/1m boundary: mod 60 == 0).
    for ts, px in [(0.0, 100.0), (10.0, 103.0), (20.0, 99.0), (30.0, 101.0)]:
        hb.add_trade(ts, px, 1)
    (bar,) = hb.timeframe_bars("1m")
    assert (bar.open, bar.high, bar.low, bar.close) == (100.0, 103.0, 99.0, 101.0)
    assert bar.ts == SIM_ANCHOR  # 14:30:00Z is itself a 1m boundary


def test_volume_sums_trade_sizes_per_bucket():
    hb = _buffer()
    hb.add_trade(0.0, 100.0, 5)
    hb.add_trade(30.0, 101.0, 7)   # same 1m bucket
    hb.add_trade(60.0, 102.0, 11)  # next 1m bucket
    bars = hb.timeframe_bars("1m")
    assert [b.volume for b in bars] == [12, 11]
    # Volume is a plain int (a sum of integer trade sizes), not a float.
    assert all(isinstance(b.volume, int) for b in bars)


def test_default_size_is_zero_volume():
    # The size arg defaults to 0 so pre-existing callers stay valid; their timeframe volume is 0.
    hb = _buffer()
    hb.add_trade(0.0, 100.0)  # no size
    (bar,) = hb.timeframe_bars("1m")
    assert bar.volume == 0


def test_all_supported_timeframes_accumulate_concurrently_from_one_stream():
    hb = _buffer()
    for ts in range(0, 600, 30):  # 20 trades across 10 minutes
        hb.add_trade(float(ts), 100.0 + ts / 100.0, 2)
    # Every supported timeframe produced at least one bar from the same stream; coarser timeframes
    # fold into fewer bars. Each bar's volume totals to the same grand total (all 20 trades × 2).
    total = 20 * 2
    for tf in hb.timeframes:
        bars = hb.timeframe_bars(tf)
        assert bars, f"{tf} accumulated no bars"
        assert sum(b.volume for b in bars) == total
    assert len(hb.timeframe_bars("1m")) == 10   # 10 one-minute buckets
    assert len(hb.timeframe_bars("5m")) == 2    # 10 minutes -> 2 five-minute buckets


# --- Anchorless behavior (honest absence, logical series unchanged) -----------------------

def test_anchorless_buffer_accumulates_no_timeframe_bars_but_logical_bars_unchanged():
    anchored = _buffer(SIM_ANCHOR)
    anchorless = _buffer(None)
    for ts, px in [(0.0, 100.0), (5.0, 101.0), (12.0, 99.0)]:
        anchored.add_trade(ts, px, 3)
        anchorless.add_trade(ts, px, 3)
    # Anchorless: no wall-clock bars at all.
    for tf in anchorless.timeframes:
        assert anchorless.timeframe_bars(tf) == ()
    assert anchorless.anchor_bucket_start("1h") is None
    # But the logical-second candles are byte-identical to the anchored buffer's (the anchor never
    # touches the logical timeline).
    for size in CONFIG.history_bar_sizes:
        assert anchorless.bars(size) == anchored.bars(size)


def test_set_epoch_anchor_is_set_once_and_bins_only_subsequent_trades():
    hb = _buffer(None)
    hb.add_trade(0.0, 100.0, 5)      # anchorless -> NOT binned into timeframe bars
    assert hb.timeframe_bars("1m") == ()
    hb.set_epoch_anchor(SIM_ANCHOR)
    hb.add_trade(60.0, 101.0, 7)     # now binned
    bars = hb.timeframe_bars("1m")
    assert len(bars) == 1 and bars[0].volume == 7  # only the post-anchor trade
    # Set-once: a second stamp is a no-op (the anchor never changes mid-watch).
    hb.set_epoch_anchor(SIM_ANCHOR + 999999.0)
    assert hb.anchor_bucket_start("1m") == (SIM_ANCHOR // 60) * 60


def test_timeframe_bars_bounded_by_history_max_bars():
    hb = _buffer()
    n = CONFIG.history_max_bars + 25
    # One trade per distinct 1m bucket -> n buckets, capped to history_max_bars (oldest dropped).
    for i in range(n):
        hb.add_trade(float(i * 60), 100.0 + i, 1)
    bars = hb.timeframe_bars("1m")
    assert len(bars) == CONFIG.history_max_bars
    # The retained window is the newest max_bars buckets (the oldest were dropped, ascending kept).
    assert bars[0].ts < bars[-1].ts
    assert bars[-1].ts == SIM_ANCHOR + (n - 1) * 60


# --- Validation + boundary -----------------------------------------------------------------

def test_unsupported_timeframe_raises_value_error():
    hb = _buffer()
    for bad in ("1w", "1mo", "3m", "", "1h "):
        try:
            hb.timeframe_bars(bad)
        except ValueError:
            pass
        else:  # pragma: no cover - defensive
            raise AssertionError(f"{bad!r} did not raise")
        try:
            hb.anchor_bucket_start(bad)
        except ValueError:
            pass
        else:  # pragma: no cover - defensive
            raise AssertionError(f"anchor_bucket_start({bad!r}) did not raise")


def test_anchor_bucket_start_floors_the_anchor():
    hb = _buffer()
    assert hb.anchor_bucket_start("5m") == (SIM_ANCHOR // 300) * 300
    assert hb.anchor_bucket_start("1h") == (SIM_ANCHOR // 3600) * 3600
    assert hb.anchor_bucket_start("1d") == (SIM_ANCHOR // 86400) * 86400
    assert _buffer(None).anchor_bucket_start("1h") is None


# --- Determinism: the size/anchor wiring is additive --------------------------------------

def test_logical_bars_and_markers_are_identical_with_and_without_anchor():
    # The logical-second candles + tape-state markers must be byte-identical whether or not an
    # anchor (and thus the timeframe accumulators) is attached — the timeframe binning is a pure
    # side channel that never feeds the logical series or the markers.
    stream = [(float(i), 100.0 + (i % 7), i % 5) for i in range(300)]
    states = ["unclear", "buyer_control", "buyer_control", "seller_control"]
    with_anchor = _buffer(SIM_ANCHOR)
    without_anchor = _buffer(None)
    for i, (ts, px, size) in enumerate(stream):
        with_anchor.add_trade(ts, px, size)
        without_anchor.add_trade(ts, px, size)
        state = states[i % len(states)]
        with_anchor.note_state(ts, state, 0.9)
        without_anchor.note_state(ts, state, 0.9)
    for size in CONFIG.history_bar_sizes:
        assert with_anchor.bars(size) == without_anchor.bars(size)
    assert with_anchor.markers() == without_anchor.markers()
