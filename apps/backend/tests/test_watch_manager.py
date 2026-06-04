"""WatchManager.stop() — per-ticker teardown and the re-watch-is-fresh guarantee (J-09).

Stop must (1) cancel the running feeder task, (2) set the engine's stream status to the
truthful "closed", and (3) REMOVE the engine from the registry so a later watch() builds a
genuinely fresh, cold engine instead of returning the exhausted/closed one. No state may leak
across the stop boundary.
"""

import asyncio
import itertools

import pytest

from app.config import CONFIG
from app.providers.adapters.base import HistoricalWindow, RawQuote, RawTrade
from app.providers.historical import HistoricalProvider
from app.providers.simulated import SimulatedProvider
from app.watch_manager import WatchManager


def _buyer_events(n: int):
    return list(itertools.islice(SimulatedProvider("SIM-BUYER", "buyer_control").stream(), n))


def _hist_provider(ticker: str = "F", n: int = 300) -> HistoricalProvider:
    # Dense, small-gap synthetic window so the feeder flips to "live" within a short sleep.
    quotes = tuple(RawQuote(i * 0.001, 16.0, 16.01, 100, 100) for i in range(n))
    trades = tuple(RawTrade(i * 0.001 + 0.0005, 16.0, 100) for i in range(n))
    window = HistoricalWindow(ticker, trades, quotes)
    return HistoricalProvider(ticker, window, f"historical {ticker} test-window")


def test_stop_unwatched_ticker_returns_false_and_raises_nothing():
    manager = WatchManager(CONFIG)
    # SIM-SELLER is a known reserved ticker but was never watched here.
    assert manager.stop("SIM-SELLER") is False
    # Idempotent: a second stop is still a quiet False, never an exception.
    assert manager.stop("SIM-SELLER") is False


def test_stop_removes_engine_and_sets_closed():
    manager = WatchManager(CONFIG)
    engine = manager.watch("SIM-BUYER")  # sync context: no running loop, so no feeder task
    assert manager.get("SIM-BUYER") is engine

    assert manager.stop("SIM-BUYER") is True
    assert manager.get("SIM-BUYER") is None  # removed from the registry (re-watch = fresh)
    assert engine.snapshot().stream_status == "closed"  # truthful closed status on the old ref
    # Now that it is gone, stopping again is the idempotent not-watched False.
    assert manager.stop("SIM-BUYER") is False


@pytest.mark.anyio
async def test_stop_cancels_the_running_feeder_task():
    # A running loop => watch() starts a background feeder; stop() must cancel it.
    manager = WatchManager(CONFIG, pace=0.001)
    engine = manager.watch("SIM-BUYER")
    task = manager._tasks["SIM-BUYER"]
    await asyncio.sleep(0.05)  # let the feeder process events and flip the status to live
    assert engine.snapshot().stream_status == "live"

    assert manager.stop("SIM-BUYER") is True
    assert "SIM-BUYER" not in manager._tasks  # feeder de-registered
    assert manager.get("SIM-BUYER") is None
    assert engine.snapshot().stream_status == "closed"

    await asyncio.sleep(0.02)  # let the cancellation propagate
    assert task.cancelled()  # the feeder is no longer running


def test_rewatch_after_stop_builds_a_fresh_cold_engine():
    manager = WatchManager(CONFIG)
    first = manager.watch("SIM-BUYER")
    for event in _buyer_events(240):  # warm the first engine so it is decidedly NOT cold
        first.process_event(event)
    assert first.snapshot().event_count > 0

    assert manager.stop("SIM-BUYER") is True

    second = manager.watch("SIM-BUYER")
    assert second is not first  # a genuinely new instance, not the exhausted one
    assert second.snapshot().event_count == 0  # starts cold — no carried-over events
    assert second.snapshot().tape_state == "unclear"  # cold start is the honest non-call


def test_rewatch_yields_identical_snapshot_to_first_ever_watch():
    # Reference: a first-ever watch warmed by a fixed 240-event prefix.
    ref_mgr = WatchManager(CONFIG)
    ref_engine = ref_mgr.watch("SIM-BUYER")
    for event in _buyer_events(240):
        ref_engine.process_event(event)
    ref = ref_engine.snapshot()

    # Subject: watch, warm with a DIFFERENT (longer) prefix, stop, re-watch, then warm with the
    # SAME fixed 240-event prefix. If any state leaked across the stop boundary, the resolved
    # read would diverge from the reference.
    mgr = WatchManager(CONFIG)
    first = mgr.watch("SIM-BUYER")
    for event in _buyer_events(500):
        first.process_event(event)
    assert mgr.stop("SIM-BUYER") is True
    rewatched = mgr.watch("SIM-BUYER")
    assert rewatched is not first
    assert rewatched.snapshot().event_count == 0  # genuinely cold before re-warming
    for event in _buyer_events(240):
        rewatched.process_event(event)
    new = rewatched.snapshot()

    # Identical resolved read after the same event prefix — deterministic, no leakage.
    assert new.tape_state == ref.tape_state == "buyer_control"
    assert new.confidence == ref.confidence
    assert new.event_count == ref.event_count
    assert new.bid == ref.bid
    assert new.ask == ref.ask
    assert new.last == ref.last


# --- Historical-provider lifecycle (J-11): no sim registry, cancellable, switch-safe --------

def test_watch_with_provider_does_not_touch_sim_registry():
    manager = WatchManager(CONFIG)
    provider = _hist_provider("F")  # "F" is NOT a known sim ticker
    assert manager.is_known("F") is False

    engine = manager.watch_with_provider("F", provider)  # sync context: no feeder task
    assert manager.get("F") is engine
    assert engine.scenario == "historical F test-window"  # row-6 source label carried through


@pytest.mark.anyio
async def test_historical_feeder_is_cancellable_via_stop():
    manager = WatchManager(CONFIG)
    engine = manager.watch_with_provider("F", _hist_provider("F"), speed=1.0)
    task = manager._tasks["F"]
    await asyncio.sleep(0.05)  # let the feeder process events and flip the status to live
    assert engine.snapshot().stream_status == "live"

    assert manager.stop("F") is True
    assert "F" not in manager._tasks  # feeder de-registered
    assert manager.get("F") is None
    assert engine.snapshot().stream_status == "closed"

    await asyncio.sleep(0.02)  # let cancellation propagate
    assert task.cancelled()


@pytest.mark.anyio
async def test_switch_tears_down_prior_historical_feeder_no_orphan():
    manager = WatchManager(CONFIG)
    first_engine = manager.watch_with_provider("F", _hist_provider("F"), speed=1.0)
    first_task = manager._tasks["F"]
    await asyncio.sleep(0.03)

    # A switch (re-watch of the same ticker) must cancel the prior feeder — no orphaned task.
    second_engine = manager.watch_with_provider("F", _hist_provider("F"), speed=1.0)
    assert second_engine is not first_engine
    assert manager._tasks["F"] is not first_task

    await asyncio.sleep(0.02)
    assert first_task.cancelled()  # the prior replay feeder was torn down

    assert manager.stop("F") is True  # clean up the second feeder
    await asyncio.sleep(0.02)
