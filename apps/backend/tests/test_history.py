"""Engine price-history buffer (J-17 / J-18): OHLC candles + tape-state-transition markers.

These assert the buffer is computed ONCE, deterministically, off the engine's logical timeline:
  * exact OHLC bin boundaries at each configured bar size (10 / 30 / 60 s);
  * markers ONLY at meaningful state transitions, carrying the engine's OWN state/confidence;
  * candle prices derive from the SAME price the snapshot exposes (single source of truth);
  * replaying the same ordered stream yields byte-identical bars + markers (determinism).

Candle/marker math is independent of the classifier thresholds, so most tests drive the engine
with a hand-built ordered stream (precise control of timestamps + prices). A couple of tests run
a real sim scenario to prove the marker reuses the live snapshot state/confidence.
"""

from __future__ import annotations

import itertools

from app.config import CONFIG
from app.engine.history import HistoryBuffer, OhlcBar
from app.engine.tape_engine import TapeEngine
from app.providers.base import QuoteEvent, TradeEvent
from app.providers.simulated import SimulatedProvider

TICKER = "SIM-BUYER"


def _engine() -> TapeEngine:
    return TapeEngine(TICKER, "buyer_control", CONFIG)


def _quote(ts: float, bid: float = 100.00, ask: float = 100.02) -> QuoteEvent:
    return QuoteEvent(TICKER, ts, bid, ask, 800, 800)


def _trade(ts: float, price: float, size: int = 100) -> TradeEvent:
    return TradeEvent(TICKER, ts, price, size)


def _feed(engine: TapeEngine, events) -> None:
    for event in events:
        engine.process_event(event)


# --- OHLC binning by LOGICAL timestamp, at each configured bar size -----------------------

def test_bar_sizes_come_from_config():
    assert _engine().history.bar_sizes == CONFIG.history_bar_sizes == (10, 30, 60)


def test_ohlc_bins_trades_by_logical_timestamp_at_10s():
    engine = _engine()
    # Two 10s bins: [0,10) gets three trades, [10,20) gets two.
    _feed(
        engine,
        [
            _trade(0.0, 100.0),
            _trade(3.0, 101.0),   # high of bin 0
            _trade(9.999, 99.0),  # low of bin 0; close of bin 0
            _trade(10.0, 100.5),  # opens bin 10 (left edge is inclusive)
            _trade(15.0, 100.7),
        ],
    )
    bars = engine.history.bars(10)
    assert bars == (
        OhlcBar(start=0.0, open=100.0, high=101.0, low=99.0, close=99.0),
        OhlcBar(start=10.0, open=100.5, high=100.7, low=100.5, close=100.7),
    )


def test_ohlc_bins_at_30s_and_60s_for_same_stream():
    engine = _engine()
    _feed(
        engine,
        [
            _trade(0.0, 100.0),
            _trade(29.0, 102.0),   # still bin [0,30)
            _trade(30.0, 101.0),   # bin [30,60) at 30s; bin [0,60) at 60s
            _trade(59.0, 103.0),
            _trade(60.0, 100.0),   # opens the next bin at both 30s and 60s
        ],
    )
    bars30 = engine.history.bars(30)
    assert bars30 == (
        OhlcBar(0.0, 100.0, 102.0, 100.0, 102.0),
        OhlcBar(30.0, 101.0, 103.0, 101.0, 103.0),
        OhlcBar(60.0, 100.0, 100.0, 100.0, 100.0),
    )
    bars60 = engine.history.bars(60)
    assert bars60 == (
        OhlcBar(0.0, 100.0, 103.0, 100.0, 103.0),
        OhlcBar(60.0, 100.0, 100.0, 100.0, 100.0),
    )


def test_quotes_do_not_create_candles_only_trades_do():
    engine = _engine()
    # A quote alone (no trade) must not open a bar; only the trade does.
    _feed(engine, [_quote(2.0), _quote(5.0)])
    assert engine.history.bars(10) == ()
    engine.process_event(_trade(7.0, 100.0))
    assert engine.history.bars(10) == (OhlcBar(0.0, 100.0, 100.0, 100.0, 100.0),)


def test_empty_bins_are_not_invented():
    engine = _engine()
    # Trades only in bin [0,10) and bin [30,40) — the gap bins ([10,30)) are NOT emitted.
    _feed(engine, [_trade(1.0, 100.0), _trade(35.0, 101.0)])
    starts = [b.start for b in engine.history.bars(10)]
    assert starts == [0.0, 30.0]  # no invented 10.0 / 20.0 candle


# --- Markers: only at meaningful transitions, reusing the engine's own state/confidence ----

def test_marker_appended_only_on_meaningful_transition_and_reuses_snapshot():
    # Real sim scenario: SIM-BUYER warms up (unclear) then settles on buyer_control. There must
    # be exactly one marker (the transition INTO buyer_control), and its state + confidence must
    # equal the engine snapshot's at that moment — no second classification.
    provider = SimulatedProvider(TICKER, "buyer_control")
    engine = _engine()
    marker_state_at_first: str | None = None
    marker_conf_at_first: float | None = None
    for event in itertools.islice(provider.stream(), 400):
        snap = engine.process_event(event)
        markers = engine.history.markers()
        if markers and marker_state_at_first is None:
            # Capture the snapshot the instant the first marker appeared.
            marker_state_at_first = snap.tape_state
            marker_conf_at_first = snap.confidence

    markers = engine.history.markers()
    assert len(markers) == 1
    marker = markers[0]
    assert marker.state == "buyer_control"
    # Single source of truth: the marker carries the classifier's own state + confidence at the
    # transition tick (exactly the snapshot value), not a recomputed number.
    assert marker.state == marker_state_at_first
    assert marker.confidence == marker_conf_at_first


def test_transition_into_unclear_is_not_marked():
    # SIM-CHOP warms up and stays unclear the whole way — a transition INTO unclear is NOT a
    # meaningful marker, so the marker list is empty.
    provider = SimulatedProvider("SIM-CHOP", "unclear_chop")
    engine = TapeEngine("SIM-CHOP", "unclear_chop", CONFIG)
    for event in itertools.islice(provider.stream(), 600):
        engine.process_event(event)
    assert engine.history.markers() == ()


def test_marker_states_set_comes_from_config():
    # The "meaningful" set is config-owned (no inline literal): unclear is excluded; the four
    # directional/absorption states are included.
    meaningful = set(CONFIG.history_marker_states)
    assert meaningful == {
        "buyer_control",
        "seller_control",
        "bid_absorption",
        "ask_absorption",
    }
    assert "unclear" not in meaningful


# --- Candle close == the snapshot's `last` price (single source of truth) -----------------

def test_candle_close_equals_snapshot_last_price():
    engine = _engine()
    snap = None
    for ts, price in [(0.0, 100.0), (1.0, 100.5), (2.0, 100.3)]:
        snap = engine.process_event(_trade(ts, price))
    # The last bin's close is the most recent trade price — exactly the snapshot's `last`.
    bars = engine.history.bars(10)
    assert bars[-1].close == snap.last == 100.3


# --- Determinism: same ordered stream => identical bars + markers --------------------------

def _run_scenario_history(ticker: str, scenario: str, n: int = 400):
    provider = SimulatedProvider(ticker, scenario)
    engine = TapeEngine(ticker, scenario, CONFIG)
    for event in itertools.islice(provider.stream(), n):
        engine.process_event(event)
    return engine.history


def test_replay_is_deterministic_bars_and_markers():
    a = _run_scenario_history(TICKER, "buyer_control")
    b = _run_scenario_history(TICKER, "buyer_control")
    for size in CONFIG.history_bar_sizes:
        assert a.bars(size) == b.bars(size)
    assert a.markers() == b.markers()


# --- A status flip must NOT mutate the series (accrual is process_event-only) --------------

def test_set_stream_status_does_not_mutate_history():
    engine = _engine()
    _feed(engine, [_trade(0.0, 100.0), _trade(5.0, 101.0)])
    bars_before = engine.history.bars(10)
    markers_before = engine.history.markers()
    engine.set_stream_status("stale")
    engine.set_stream_status("live")
    assert engine.history.bars(10) == bars_before
    assert engine.history.markers() == markers_before


# --- Unsupported bar size at the buffer level is a hard error (route maps it to 422) -------

def test_buffer_rejects_unsupported_bar_size():
    buffer = HistoryBuffer(CONFIG)
    try:
        buffer.bars(7)
    except ValueError:
        return
    raise AssertionError("expected ValueError for an unsupported bar size")
