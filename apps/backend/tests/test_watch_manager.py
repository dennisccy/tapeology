"""WatchManager.stop() — per-ticker teardown and the re-watch-is-fresh guarantee (J-09).

Stop must (1) cancel the running feeder task, (2) set the engine's stream status to the
truthful "closed", and (3) REMOVE the engine from the registry so a later watch() builds a
genuinely fresh, cold engine instead of returning the exhausted/closed one. No state may leak
across the stop boundary.
"""

import asyncio
import dataclasses
import itertools

import pytest

from app.config import CONFIG
from app.providers.adapters.base import HistoricalWindow, RawQuote, RawTrade
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.providers.historical import HistoricalProvider
from app.providers.simulated import SimulatedProvider
from app.watch_manager import WatchManager
from fakes import FakeLiveProvider

# A small stale-gap override so the live watchdog fires in milliseconds, not the 10s default.
FAST_STALE = dataclasses.replace(CONFIG, stale_gap_seconds=0.05)


async def _until(predicate, timeout: float = 3.0, step: float = 0.005) -> None:
    elapsed = 0.0
    while elapsed < timeout:
        if predicate():
            return
        await asyncio.sleep(step)
        elapsed += step
    raise AssertionError("condition not met within timeout")


def _seed_live(provider: FakeLiveProvider) -> None:
    """Enqueue one quote + one trade so the engine has data and the status can reach `live`."""
    provider.feed_nowait(QuoteEvent(provider.ticker, 0.0, 100.0, 100.02, 100, 100))
    provider.feed_nowait(TradeEvent(provider.ticker, 0.0, 100.02, 100, Side.UNKNOWN))


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


# --- Live async feeder + stale watchdog (J-12 / J-15): no sim registry, stale-recover, no leak --

@pytest.mark.anyio
async def test_live_feeder_flips_live_then_stale_then_recovers_without_fabricating_trades():
    # J-15 core, hermetic: with a small stale gap, the live feeder reads `live`, flips to `stale`
    # after a feed lull (fabricating NO trades during the gap), and recovers to `live` on resume.
    manager = WatchManager(FAST_STALE)
    provider = FakeLiveProvider("LIVE")
    _seed_live(provider)
    engine = manager.watch_with_async_provider("LIVE", provider)
    try:
        await _until(lambda: engine.snapshot().stream_status == "live")
        count_before = engine.snapshot().event_count
        assert count_before == 1  # exactly the one seeded trade

        # Lull: no event within stale_gap_seconds -> `stale`, and NOTHING is synthesized.
        await _until(lambda: engine.snapshot().stream_status == "stale")
        assert engine.snapshot().event_count == count_before  # no fabricated trades during the gap
        assert len(engine.snapshot().recent_trades) == count_before  # recent-trades unchanged

        # Resume: the next real event flips the status back to `live` (the feeder owns this flip;
        # the engine only auto-flips connecting->live, not stale->live).
        provider.feed_nowait(TradeEvent("LIVE", 1.0, 100.02, 100, Side.UNKNOWN))
        await _until(lambda: engine.snapshot().stream_status == "live")
        assert engine.snapshot().event_count == count_before + 1
    finally:
        assert manager.stop("LIVE") is True
        await _until(lambda: provider.socket.closed)


@pytest.mark.anyio
async def test_stop_cancels_live_feeder_and_closes_socket_no_leak():
    # Load-bearing iter-0 lesson: a live socket leak is a real vendor connection leak. stop() must
    # cancel the feeder, set `closed`, AND close + unsubscribe the vendor socket — no orphan.
    manager = WatchManager(FAST_STALE)
    provider = FakeLiveProvider("LIVE")
    _seed_live(provider)
    engine = manager.watch_with_async_provider("LIVE", provider)
    task = manager._tasks["LIVE"]
    await _until(lambda: engine.snapshot().stream_status == "live")

    assert manager.stop("LIVE") is True
    assert "LIVE" not in manager._tasks  # feeder de-registered
    assert manager.get("LIVE") is None
    assert engine.snapshot().stream_status == "closed"

    await _until(lambda: provider.socket.closed)
    assert provider.socket.closed and provider.socket.unsubscribed  # socket closed (no leak)
    await _until(lambda: task.cancelled())
    assert task.cancelled()


@pytest.mark.anyio
async def test_switch_tears_down_prior_live_feeder_and_closes_prior_socket():
    # A source/symbol switch (a fresh watch_with_async_provider for the same ticker) must tear down
    # the prior live feeder AND close its socket — no orphaned watch, no leaked vendor connection.
    manager = WatchManager(FAST_STALE)
    first = FakeLiveProvider("LIVE", "live LIVE-1")
    _seed_live(first)
    first_engine = manager.watch_with_async_provider("LIVE", first)
    first_task = manager._tasks["LIVE"]
    await _until(lambda: first_engine.snapshot().stream_status == "live")

    second = FakeLiveProvider("LIVE", "live LIVE-2")
    second_engine = manager.watch_with_async_provider("LIVE", second)  # the switch
    assert second_engine is not first_engine
    assert manager._tasks["LIVE"] is not first_task

    await _until(lambda: first.socket.closed)
    assert first.socket.closed and first.socket.unsubscribed  # prior socket closed on switch
    await _until(lambda: first_task.cancelled())
    assert first_task.cancelled()

    assert manager.stop("LIVE") is True  # clean up the second feeder
    await _until(lambda: second.socket.closed)


@pytest.mark.anyio
async def test_live_feeder_does_not_touch_sim_registry():
    # The live path never consults the simulated registry (a live symbol is not a sim ticker).
    manager = WatchManager(FAST_STALE)
    assert manager.is_known("AAPL") is False
    provider = FakeLiveProvider("AAPL", "live AAPL")
    _seed_live(provider)
    engine = manager.watch_with_async_provider("AAPL", provider)
    try:
        assert manager.get("AAPL") is engine
        assert engine.scenario == "live AAPL"  # row-6 source label carried through
        await _until(lambda: engine.snapshot().stream_status == "live")  # feeder ran (socket open)
    finally:
        assert manager.stop("AAPL") is True
        await _until(lambda: provider.socket.closed)
