"""Canonical display/epoch anchor — Data Contract row 13 (J-31).

The chart's time axis must show TRUE clock time, not elapsed/logical playback seconds. The
engine bins on its deterministic LOGICAL timeline (unchanged), and an ADDITIVE display anchor —
the real UTC epoch that logical-time 0 maps to — is preserved ONCE in the engine/feeder and
exposed read-only through the history projection. The chart maps a logical bin ``start`` to a
true clock instant as ``anchor_epoch + start`` (a pure additive offset — it recomputes no
price/side/state).

These assert:
  * the providers expose the correct ``epoch_anchor`` (historical = the first real record's UTC
    epoch; simulated = a config-owned synthetic session-start; live = None until first event);
  * the engine carries the anchor on its snapshot and surfaces it via the history projection;
  * the anchor is ADDITIVE display metadata only — the SAME ordered event stream still yields
    byte-identical features/state/confidence whether or not an anchor is attached (determinism
    preserved; the anchor never enters classification).
"""

from __future__ import annotations

import asyncio
import itertools

import pytest

from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.providers.adapters.base import HistoricalWindow, RawQuote, RawTrade
from app.providers.historical import HistoricalProvider
from app.providers.live import LiveProvider
from app.providers.simulated import SimulatedProvider
from app.serializers import serialize_history
from app.watch_manager import WatchManager


# --- Providers expose the right anchor ----------------------------------------------------

def test_simulated_provider_anchor_is_config_session_start():
    # The sim anchor is the config-owned synthetic session-start (no inline literal); it is a
    # real UTC epoch (a real clock face), the same for every sim ticker / determinism preserved.
    p = SimulatedProvider("SIM-BUYER", "buyer_control")
    assert p.epoch_anchor == CONFIG.sim_session_anchor_epoch
    p2 = SimulatedProvider("SIM-SELLER", "seller_control")
    assert p2.epoch_anchor == CONFIG.sim_session_anchor_epoch


def test_historical_provider_anchor_is_first_real_record_epoch():
    # The historical anchor is the first real record's UTC epoch — exactly the t0 the provider
    # already subtracts to build its logical timeline (so true_clock = anchor + logical_ts).
    window = HistoricalWindow(
        symbol="F",
        trades=(RawTrade(epoch=1780412400.5, price=12.34, size=100),),
        quotes=(
            RawQuote(epoch=1780412400.0, bid=12.33, ask=12.35, bid_size=10, ask_size=10),
            RawQuote(epoch=1780412405.0, bid=12.34, ask=12.36, bid_size=10, ask_size=10),
        ),
    )
    p = HistoricalProvider("F", window, "historical F window")
    # The earliest of all records (the quote at 1780412400.0) is the window's logical zero.
    assert p.epoch_anchor == 1780412400.0


def test_historical_provider_empty_window_anchor_is_none():
    # An empty window has no first record, so there is no anchor — the chart stays empty and
    # fabricates no timestamps (no-fabricated-data).
    p = HistoricalProvider("F", HistoricalWindow("F", (), ()), "historical F window")
    assert p.epoch_anchor is None


# --- Engine carries the anchor and surfaces it via the history projection -----------------

def _warm_sim_engine(anchor: float | None, n: int = 400) -> TapeEngine:
    provider = SimulatedProvider("SIM-BUYER", "buyer_control")
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG, epoch_anchor=anchor)
    for event in itertools.islice(provider.stream(), n):
        engine.process_event(event)
    return engine


def test_engine_snapshot_carries_epoch_anchor():
    engine = _warm_sim_engine(CONFIG.sim_session_anchor_epoch)
    assert engine.snapshot().epoch_anchor == CONFIG.sim_session_anchor_epoch


def test_engine_defaults_anchor_to_none_for_backward_compatibility():
    # Additive field: an engine built without an anchor (every pre-J-31 construction) reads None.
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    assert engine.snapshot().epoch_anchor is None


def test_history_projection_exposes_anchor():
    anchor = CONFIG.sim_session_anchor_epoch
    engine = _warm_sim_engine(anchor)
    for bar in CONFIG.history_bar_sizes:
        out = serialize_history(engine.history, bar, epoch_anchor=engine.epoch_anchor)
        assert out["epoch_anchor"] == anchor
        # Bars/markers stay LOGICAL (the chart adds the anchor as a pure additive offset) so the
        # single source of truth — the engine's logical buffer — is read verbatim.
        for served, b in zip(out["bars"], engine.history.bars(bar)):
            assert served["time"] == b.start


def test_history_projection_anchor_none_when_unset():
    engine = _warm_sim_engine(None)
    out = serialize_history(engine.history, CONFIG.history_bar_sizes[0], epoch_anchor=None)
    assert out["epoch_anchor"] is None


# --- Determinism: the anchor is additive and does NOT perturb classification --------------

def _run_full_snapshot(anchor: float | None, n: int = 400) -> dict:
    """Run the SAME ordered SIM-BUYER stream and capture every classified value (no anchor field)."""
    provider = SimulatedProvider("SIM-BUYER", "buyer_control")
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG, epoch_anchor=anchor)
    snap = engine.snapshot()
    for event in itertools.islice(provider.stream(), n):
        snap = engine.process_event(event)
    return {
        "tape_state": snap.tape_state,
        "confidence": snap.confidence,
        "features": snap.features,
        "observations": snap.observations,
        "event_log": snap.event_log,
        "timestamp": snap.timestamp,
        "event_count": snap.event_count,
    }


def test_anchor_does_not_change_features_state_or_confidence():
    # The SAME ordered stream classified WITH an anchor and WITHOUT one must be byte-identical in
    # every classified value — the anchor is display metadata, never an input to the engine math.
    with_anchor = _run_full_snapshot(CONFIG.sim_session_anchor_epoch)
    without_anchor = _run_full_snapshot(None)
    assert with_anchor == without_anchor
    # And the directional read still lands (sanity: the stream genuinely classifies, not all-unclear).
    assert with_anchor["tape_state"] == "buyer_control"
    assert with_anchor["confidence"] >= CONFIG.reasonable_confidence


# --- Live mode learns the anchor at the first record (chart now renders live too) ---------


async def _first_stream_event_anchor(records) -> float | None:
    """The provider's ``epoch_anchor`` observed right after it yields its FIRST event."""
    async def _aiter():
        for r in records:
            yield r

    provider = LiveProvider("X", _aiter(), "live X")
    async for _ in provider.stream():
        return provider.epoch_anchor  # after the first yield, the anchor must already be stamped
    return provider.epoch_anchor


@pytest.mark.anyio
async def test_live_provider_anchor_set_on_first_record():
    # Unlike the old "live = None forever", the provider now stamps its anchor from the first
    # record's real epoch (the SAME t0 its logical timeline subtracts) — the moment the first event
    # is yielded, so the feeder can read it before processing that event.
    records = [
        RawTrade(epoch=1_700_000_000.0, price=12.34, size=100),
        RawTrade(epoch=1_700_000_030.0, price=12.35, size=50),
    ]
    assert await _first_stream_event_anchor(records) == 1_700_000_000.0
    # An empty stream never yields, so it never stamps an anchor (honest None — nothing to anchor to).
    assert await _first_stream_event_anchor([]) is None


@pytest.mark.anyio
async def test_live_feeder_stamps_engine_anchor_before_first_trade():
    # End-to-end: the live feeder reads the provider's first-record anchor and stamps the engine
    # BEFORE processing the first event, so that event bins into the wall-clock timeframe candles.
    async def _aiter():
        for r in (
            RawTrade(epoch=1_700_000_000.0, price=12.34, size=100),
            RawTrade(epoch=1_700_000_030.0, price=12.35, size=50),
        ):
            yield r

    manager = WatchManager(CONFIG)
    provider = LiveProvider("LIVEX", _aiter(), "live LIVEX")
    engine = manager.watch_with_async_provider("LIVEX", provider)
    try:
        # The engine starts anchorless (a live provider's epoch is unknown at construction) and is
        # stamped once the feeder applies the first event.
        await _until(lambda: engine.epoch_anchor is not None)
        assert engine.epoch_anchor == 1_700_000_000.0
        # And that first trade landed in a 1m wall-clock bucket (floored real epoch), with volume —
        # proof the stamp happened before process_event, not after.
        await _until(lambda: engine.history.timeframe_bars("1m"))
        bars = engine.history.timeframe_bars("1m")
        assert bars[0].ts == (1_700_000_000.0 // 60) * 60
        assert bars[0].volume >= 100  # at least the first trade's size
        assert engine.history.anchor_bucket_start("1m") == (1_700_000_000.0 // 60) * 60
    finally:
        await manager.shutdown()


async def _until(predicate, timeout: float = 3.0, step: float = 0.01) -> None:
    elapsed = 0.0
    while elapsed < timeout:
        if predicate():
            return
        await asyncio.sleep(step)
        elapsed += step
    raise AssertionError("condition not met within timeout")
