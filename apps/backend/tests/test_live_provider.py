"""LiveProvider (J-12): async neutral->logical mapping + the full hermetic live pipeline.

These tests are the in-loop proof for J-12's mechanism (the real Alpaca socket itself is the
operator/gated check). A test-only async fake behind the seam feeds real-shaped neutral records
through the SAME engine the simulator/historical paths use: the snapshot populates, the status
reads ``live``, the tape state classifies, and the REST/summary/stream projections agree (single
source of truth). The fakes are legitimate test doubles behind the provider seam — NEVER wired
into the production live path.
"""

import asyncio

import pytest

from app.config import CONFIG
from app.providers.adapters.base import RawQuote, RawTrade
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.providers.live import LiveProvider
from app.serializers import serialize_state, serialize_stream, serialize_summary
from app.watch_manager import WatchManager
from fakes import FakeAdapter, load_fixture_window

pytestmark = pytest.mark.anyio  # every test here is async


async def _aiter(records):
    for r in records:
        yield r


async def _collect(provider: LiveProvider):
    return [event async for event in provider.stream()]


async def _until(predicate, timeout: float = 3.0, step: float = 0.005) -> None:
    elapsed = 0.0
    while elapsed < timeout:
        if predicate():
            return
        await asyncio.sleep(step)
        elapsed += step
    raise AssertionError("condition not met within timeout")


def _merged_fixture_records():
    """The committed REAL fixture's trades + quotes interleaved in arrival order (quote before
    trade at equal epoch) — the shape a live socket delivers them in."""
    window, _ = load_fixture_window()
    items = [(q.epoch, 0, q) for q in window.quotes] + [(t.epoch, 1, t) for t in window.trades]
    items.sort(key=lambda x: (x[0], x[1]))
    return [rec for _, _, rec in items], window


# --- Neutral -> logical mapping (the async counterpart to HistoricalProvider) ----------------

async def test_live_provider_maps_epochs_to_logical_offsets_from_first_event():
    # Real-shaped neutral records with large, non-zero epochs -> logical offsets from the FIRST
    # event (first at 0.0), monotonic non-decreasing; quote/trade map to the right Event types.
    records = [
        RawQuote(1_700_000_000.0, 1.00, 1.02, 10, 12),
        RawTrade(1_700_000_001.0, 1.02, 100),
        RawQuote(1_700_000_002.5, 1.01, 1.03, 10, 10),
        RawTrade(1_700_000_002.5, 1.03, 200),
    ]
    events = await _collect(LiveProvider("X", _aiter(records), "live X"))
    timestamps = [e.timestamp for e in events]
    assert timestamps == [0.0, 1.0, 2.5, 2.5]
    assert timestamps == sorted(timestamps)  # monotonic non-decreasing
    assert isinstance(events[0], QuoteEvent) and isinstance(events[1], TradeEvent)
    assert events[0].bid == 1.00 and events[0].ask == 1.02 and events[0].bid_size == 10
    # Trades carry UNKNOWN — the engine re-derives the aggressor from the in-effect quote.
    assert all(e.side is Side.UNKNOWN for e in events if isinstance(e, TradeEvent))
    assert events[1].price == 1.02 and events[1].size == 100


async def test_live_provider_clamps_out_of_order_epoch_to_monotonic():
    # A live feed can deliver a trade a beat BEHIND a quote; the offset must be clamped to
    # non-decreasing so the engine's rolling windows stay well-formed (never a backwards stamp).
    records = [
        RawQuote(100.0, 1.0, 1.02, 10, 10),
        RawTrade(105.0, 1.02, 100),
        RawTrade(104.0, 1.02, 100),  # 1s behind the prior event
    ]
    timestamps = [e.timestamp for e in await _collect(LiveProvider("X", _aiter(records), "s"))]
    assert timestamps == [0.0, 5.0, 5.0]  # the late trade clamps up to 5.0, not 4.0


async def test_live_provider_scenario_carried_and_empty_stream_yields_nothing():
    provider = LiveProvider("AAPL", _aiter([]), "live AAPL")
    assert provider.scenario == "live AAPL"
    assert await _collect(provider) == []


# --- Full hermetic live pipeline: populate, classify, status live, SSOT, socket closed -------

async def test_live_pipeline_populates_classifies_is_live_and_ssot():
    # Feed the SAME real fixture records through the LIVE async path (adapter.stream_live ->
    # LiveProvider -> async feeder -> engine). It must reach the SAME read the historical sync
    # replay does (bid_absorption), with status `live`, and the REST/summary/stream projections
    # must agree — one engine value per metric (single source of truth).
    records, window = _merged_fixture_records()
    hold = asyncio.Event()  # keep the socket open so the status stays `live` while we assert
    adapter = FakeAdapter(available=True, live_records=records, live_hold=hold)
    manager = WatchManager(CONFIG)
    provider = LiveProvider("F", adapter.stream_live("F"), "live F")
    engine = manager.watch_with_async_provider("F", provider)
    try:
        await _until(lambda: engine.snapshot().event_count >= len(window.trades))
        snap = engine.snapshot()

        assert snap.event_count == len(window.trades)
        assert snap.stream_status == "live"  # held open, not exhausted/closed
        assert snap.scenario == "live F"  # row-6 watched-source label, verbatim
        # Market populated; spread == ask - bid (derived once).
        assert snap.bid is not None and snap.ask is not None and snap.last is not None
        assert snap.spread == pytest.approx(snap.ask - snap.bid)
        assert snap.recent_trades and snap.warm is True
        # Same real read as the historical replay of these exact records (the keystone case).
        assert snap.tape_state == "bid_absorption"
        assert snap.confidence >= CONFIG.reasonable_confidence
        assert any(m.startswith("Tape state changed to") for m in snap.event_log)

        # SSOT: canonical /state, /summary, and the WS /stream projections agree exactly.
        state, summary, stream = serialize_state(snap), serialize_summary(snap), serialize_stream(snap)
        assert state["tape_state"] == summary["tape_state"] == stream["tape_state"] == snap.tape_state
        assert state["confidence"] == summary["confidence"] == stream["confidence"] == snap.confidence
        assert state["stream_status"] == summary["stream_status"] == stream["stream_status"] == "live"
        assert summary["market"] == stream["market"]  # identical bid/ask/spread/last
        assert stream["headline_features"] == summary["headline_features"]
    finally:
        hold.set()
        assert manager.stop("F") is True
        await _until(lambda: adapter.live_socket.closed)
        assert adapter.live_socket.closed and adapter.live_socket.unsubscribed  # no leaked socket
