"""HistoricalProvider (J-11): logical timestamp mapping + deterministic REAL-fixture replay.

The committed fixture is REAL captured Alpaca data (Ford, a fixed 2-minute past window). It is
NOT synthesized — replaying it through the SAME engine the simulator uses populates every
cockpit value and is reproducible run-to-run, which is the in-loop evidence for J-11.
"""

import pytest

from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.providers.adapters.base import HistoricalWindow, RawQuote, RawTrade
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.providers.historical import HistoricalProvider
from app.serializers import HEADLINE_FEATURES
from fakes import load_fixture_window

VALID_STATES = {
    "buyer_control",
    "seller_control",
    "bid_absorption",
    "ask_absorption",
    "unclear",
}


def _replay(window: HistoricalWindow, scenario: str = "historical TEST") -> TapeEngine:
    provider = HistoricalProvider(window.symbol, window, scenario)
    engine = TapeEngine(window.symbol, provider.scenario, CONFIG)
    for event in provider.stream():
        engine.process_event(event)
    return engine


# --- Timestamp mapping: logical, monotonic non-decreasing, from window start ----------------

def test_timestamps_are_logical_offsets_from_window_start():
    # Raw epochs deliberately out of order and far from zero; the provider must emit logical
    # offsets from the EARLIEST event (first event at 0.0), monotonic non-decreasing.
    quotes = (RawQuote(1000.0, 1.0, 1.02, 10, 10), RawQuote(1002.0, 1.0, 1.02, 10, 10))
    trades = (RawTrade(1001.0, 1.01, 100), RawTrade(1003.0, 1.02, 100))
    events = list(HistoricalProvider("X", HistoricalWindow("X", trades, quotes), "s").stream())

    timestamps = [e.timestamp for e in events]
    assert timestamps[0] == 0.0
    assert timestamps == sorted(timestamps)  # monotonic non-decreasing
    assert timestamps == [0.0, 1.0, 2.0, 3.0]  # epoch - 1000.0
    # No wall-clock leaked in: every timestamp is a small logical offset, not an epoch.
    assert all(0.0 <= t <= 3.0 for t in timestamps)


def test_quote_is_delivered_before_trade_at_the_same_instant():
    # A trade and a quote share the exact epoch; the quote MUST come first so the in-effect
    # quote is set before the engine classifies the trade.
    window = HistoricalWindow(
        "X", trades=(RawTrade(5.0, 1.0, 100),), quotes=(RawQuote(5.0, 0.99, 1.01, 10, 10),)
    )
    events = list(HistoricalProvider("X", window, "s").stream())
    assert isinstance(events[0], QuoteEvent)
    assert isinstance(events[1], TradeEvent)
    assert events[0].timestamp == events[1].timestamp == 0.0


def test_trades_are_yielded_as_unknown_side():
    window = HistoricalWindow(
        "X", trades=(RawTrade(0.0, 1.0, 100), RawTrade(1.0, 1.0, 100)),
        quotes=(RawQuote(0.0, 0.99, 1.01, 10, 10),),
    )
    trades = [e for e in HistoricalProvider("X", window, "s").stream() if isinstance(e, TradeEvent)]
    assert trades and all(t.side is Side.UNKNOWN for t in trades)


def test_scenario_label_is_carried_through():
    window, _ = load_fixture_window()
    provider = HistoricalProvider("F", window, "historical F 2026-06-02T15:00–15:02")
    assert provider.scenario == "historical F 2026-06-02T15:00–15:02"


def test_empty_window_streams_nothing():
    window = HistoricalWindow("X", trades=(), quotes=())
    assert list(HistoricalProvider("X", window, "s").stream()) == []


# --- Deterministic REAL-fixture replay: every cockpit value populated, reproducible ---------

def test_real_fixture_replay_populates_every_cockpit_value():
    window, raw = load_fixture_window()
    assert raw["source"] == "alpaca" and raw["trades"], "fixture must be real captured data"

    snap = _replay(window).snapshot()

    # Market: bid/ask/spread/last all real numbers; spread == ask - bid (single source).
    assert snap.bid is not None and snap.ask is not None and snap.last is not None
    assert snap.spread == pytest.approx(snap.ask - snap.bid)

    # Recent trades populated with price/size/side.
    assert snap.recent_trades
    row = snap.recent_trades[0]
    assert row.price > 0 and row.size > 0 and row.side in {"buy", "sell", "unknown"}

    # Every headline feature is a real number.
    primary = snap.primary_features
    for name in HEADLINE_FEATURES:
        assert isinstance(primary[name], float)

    # A real tape state + confidence. This fixed real window resolves to bid_absorption (heavy
    # selling absorbed at a holding bid) at high confidence — the keystone price-impact case.
    assert snap.warm is True
    assert snap.tape_state in VALID_STATES
    assert snap.tape_state == "bid_absorption"
    assert snap.confidence >= CONFIG.reasonable_confidence

    # Observations + an event log with at least one real state transition.
    assert snap.observations
    assert snap.event_log
    assert any(m.startswith("Tape state changed to") for m in snap.event_log)


def test_real_fixture_replay_is_reproducible():
    window, _ = load_fixture_window()
    first = _replay(window).snapshot()
    second = _replay(window).snapshot()  # independent engine, same window

    assert first.tape_state == second.tape_state
    assert first.confidence == second.confidence
    assert first.event_count == second.event_count
    assert first.bid == second.bid and first.ask == second.ask and first.last == second.last
    assert first.features == second.features  # identical per-window feature values
    assert first.event_log == second.event_log
