"""Honest pause/resume — freeze a watched session WITHOUT teardown or fabrication (J-19).

Pause is deliberately the opposite of stop (test_watch_manager.py): it MUST NOT cancel the
feeder task, MUST NOT close a live socket, and MUST NOT synthesize any catch-up trades on
resume. The engine, its latest snapshot, and the history buffer survive a pause; the status
reads the canonical "paused" (never a fabricated "live"); on resume the prior pre-pause status
is restored and feeding continues from where it left off.

Two layers are covered:
  * the engine primitive (``TapeEngine.pause`` / ``resume`` — flag + status, idempotent), and
  * the feeder-level freeze (``WatchManager.pause`` / ``resume`` — alive task, frozen feeding,
    honest no-backfill, stop-after-pause still tears down).
"""

import asyncio
import dataclasses
import itertools

import pytest

from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.providers.base import Side, TradeEvent
from app.providers.simulated import SimulatedProvider
from app.watch_manager import WatchManager
from fakes import FakeLiveProvider

# A small stale-gap override so the live watchdog fires in milliseconds (mirrors the live tests).
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
    from app.providers.base import QuoteEvent

    provider.feed_nowait(QuoteEvent(provider.ticker, 0.0, 100.0, 100.02, 100, 100))
    provider.feed_nowait(TradeEvent(provider.ticker, 0.0, 100.02, 100, Side.UNKNOWN))


def _buyer_events(n: int):
    return list(itertools.islice(SimulatedProvider("SIM-BUYER", "buyer_control").stream(), n))


# --- Engine primitive: paused flag + canonical status, idempotent ------------------------

def test_engine_pause_sets_flag_and_paused_status():
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    for event in _buyer_events(120):
        engine.process_event(event)
    assert engine.snapshot().stream_status == "live"
    assert engine.snapshot().paused is False  # the new canonical field, default False

    engine.pause()
    snap = engine.snapshot()
    assert snap.paused is True
    assert snap.stream_status == "paused"  # row-6 status value, owned once by the engine


def test_engine_resume_restores_prior_status_and_clears_paused():
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    for event in _buyer_events(120):
        engine.process_event(event)
    prior = engine.snapshot().stream_status
    assert prior == "live"

    engine.pause()
    assert engine.snapshot().stream_status == "paused"

    engine.resume()
    snap = engine.snapshot()
    assert snap.paused is False
    assert snap.stream_status == prior  # restored, NEVER a fabricated "live"


def test_engine_resume_from_connecting_does_not_fabricate_live():
    # Honest pause: a cold engine paused before any event must resume to "connecting", not "live".
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    assert engine.snapshot().stream_status == "connecting"

    engine.pause()
    assert engine.snapshot().stream_status == "paused"
    assert engine.snapshot().paused is True

    engine.resume()
    assert engine.snapshot().stream_status == "connecting"  # NOT fabricated "live"
    assert engine.snapshot().paused is False


def test_engine_resume_from_stale_restores_stale():
    # If the feed was stale at pause time, resume restores "stale" — never an upgraded "live".
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    for event in _buyer_events(120):
        engine.process_event(event)
    engine.set_stream_status("stale")
    assert engine.snapshot().stream_status == "stale"

    engine.pause()
    assert engine.snapshot().stream_status == "paused"
    engine.resume()
    assert engine.snapshot().stream_status == "stale"  # restored honestly


def test_engine_pause_is_idempotent():
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    for event in _buyer_events(120):
        engine.process_event(event)
    engine.pause()
    engine.pause()  # second pause must be a no-op (no crash, no clobbered pre-pause status)
    assert engine.snapshot().stream_status == "paused"
    engine.resume()
    assert engine.snapshot().stream_status == "live"  # the original pre-pause status, not "paused"


def test_engine_resume_when_not_paused_is_noop():
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    for event in _buyer_events(120):
        engine.process_event(event)
    assert engine.snapshot().paused is False
    engine.resume()  # resume-when-not-paused: a quiet no-op
    assert engine.snapshot().paused is False
    assert engine.snapshot().stream_status == "live"


def test_engine_paused_blocks_event_application_and_resume_does_not_backfill():
    # Honest pause at the engine layer: process_event while paused applies NOTHING (the feeder
    # is the gate, but the engine must also refuse to advance so a stray event cannot leak in),
    # and resume fabricates no backfill — the exact pre/post counts are equal.
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    events = _buyer_events(200)
    for event in events[:120]:
        engine.process_event(event)
    count_before = engine.snapshot().event_count
    last_ts_before = engine.snapshot().timestamp

    engine.pause()
    # Feeding events while paused must not advance the engine (no applied trades, no new ts).
    for event in events[120:160]:
        engine.process_event(event)
    assert engine.snapshot().event_count == count_before  # nothing applied while paused
    assert engine.snapshot().timestamp == last_ts_before
    assert engine.snapshot().stream_status == "paused"

    engine.resume()
    # Resume fabricates no catch-up: the count is still exactly what it was before the pause.
    assert engine.snapshot().event_count == count_before
    # And feeding resumes normally afterwards (the gate is lifted) — an explicit TradeEvent (the
    # provider stream interleaves quotes, which don't bump event_count) advances the count by one.
    engine.process_event(
        TradeEvent("SIM-BUYER", last_ts_before + 1.0, 100.20, 100, Side.UNKNOWN)
    )
    assert engine.snapshot().event_count == count_before + 1


# --- Feeder-level freeze (WatchManager.pause/resume): alive task, frozen, honest ----------

@pytest.mark.anyio
async def test_pause_freezes_feeder_without_cancelling_task():
    # The load-bearing distinction from stop(): pause leaves the feeder task ALIVE and the engine
    # in the registry; only the canonical status flips to "paused".
    manager = WatchManager(CONFIG, pace=0.001)
    engine = manager.watch("SIM-BUYER")
    task = manager._tasks["SIM-BUYER"]
    await _until(lambda: engine.snapshot().stream_status == "live")

    assert manager.pause("SIM-BUYER") is True
    await _until(lambda: engine.snapshot().stream_status == "paused")
    assert engine.snapshot().paused is True

    # The feeder task is STILL ALIVE (not cancelled) and the engine is STILL registered.
    assert task.cancelled() is False
    assert task.done() is False
    assert manager.get("SIM-BUYER") is engine  # snapshot still readable, …/state would be 200

    assert manager.stop("SIM-BUYER") is True  # cleanup
    await _until(lambda: task.cancelled())


@pytest.mark.anyio
async def test_pause_then_resume_continues_without_fabricated_backfill():
    # Honest pause over the live feeder (J-19 / J-15 standard): while paused NO new trades are
    # applied; on resume the count does NOT jump by a fabricated backfill — feeding simply
    # continues from where it left off. Hermetic via FakeLiveProvider so the test owns timing.
    manager = WatchManager(FAST_STALE)
    provider = FakeLiveProvider("LIVE")
    _seed_live(provider)
    engine = manager.watch_with_async_provider("LIVE", provider)
    try:
        await _until(lambda: engine.snapshot().stream_status == "live")
        count_before = engine.snapshot().event_count
        assert count_before == 1  # exactly the one seeded trade

        assert manager.pause("LIVE") is True
        await _until(lambda: engine.snapshot().stream_status == "paused")
        assert engine.snapshot().paused is True

        # Feed events WHILE PAUSED: they must NOT be applied (no fabricated catch-up later).
        provider.feed_nowait(TradeEvent("LIVE", 1.0, 100.02, 100, Side.UNKNOWN))
        provider.feed_nowait(TradeEvent("LIVE", 2.0, 100.03, 100, Side.UNKNOWN))
        await asyncio.sleep(0.1)  # give the feeder a chance to (wrongly) apply — it must not
        assert engine.snapshot().event_count == count_before  # frozen: nothing applied
        assert engine.snapshot().stream_status == "paused"  # never reads "live" while paused

        # Resume: status restored to the pre-pause "live"; NO backfill jump in the count.
        assert manager.resume("LIVE") is True
        await _until(lambda: engine.snapshot().stream_status == "live")
        assert engine.snapshot().paused is False
        # The count did not leap by the 2 events fed during the pause (honest, no catch-up).
        assert engine.snapshot().event_count == count_before

        # A NEW event after resume is applied normally (feeding genuinely continued).
        provider.feed_nowait(TradeEvent("LIVE", 3.0, 100.04, 100, Side.UNKNOWN))
        await _until(lambda: engine.snapshot().event_count == count_before + 1)
    finally:
        assert manager.stop("LIVE") is True
        await _until(lambda: provider.socket.closed)


@pytest.mark.anyio
async def test_pause_does_not_close_live_socket():
    # Honest pause for LIVE: the vendor socket stays OPEN while paused (pause = stop applying
    # events, NOT unsubscribe/close — the iter-4 deadlock lesson). Only stop() closes it.
    manager = WatchManager(FAST_STALE)
    provider = FakeLiveProvider("LIVE")
    _seed_live(provider)
    engine = manager.watch_with_async_provider("LIVE", provider)
    try:
        await _until(lambda: engine.snapshot().stream_status == "live")
        assert manager.pause("LIVE") is True
        await _until(lambda: engine.snapshot().stream_status == "paused")
        await asyncio.sleep(0.1)
        assert provider.socket.closed is False  # socket NOT closed by a pause
        assert provider.socket.unsubscribed is False
    finally:
        assert manager.stop("LIVE") is True
        await _until(lambda: provider.socket.closed)
    # Only stop closed it.
    assert provider.socket.closed and provider.socket.unsubscribed


@pytest.mark.anyio
async def test_stop_after_pause_still_fully_tears_down():
    # Pause must not break teardown: stop() after a pause still cancels the feeder, sets "closed",
    # and removes the engine (…/state would 404). Pause is additive, not a replacement for stop.
    manager = WatchManager(CONFIG, pace=0.001)
    engine = manager.watch("SIM-BUYER")
    task = manager._tasks["SIM-BUYER"]
    await _until(lambda: engine.snapshot().stream_status == "live")

    assert manager.pause("SIM-BUYER") is True
    await _until(lambda: engine.snapshot().stream_status == "paused")

    assert manager.stop("SIM-BUYER") is True
    assert "SIM-BUYER" not in manager._tasks  # feeder de-registered
    assert manager.get("SIM-BUYER") is None  # engine removed -> reads 404
    assert engine.snapshot().stream_status == "closed"  # truthful closed, not "paused"
    await _until(lambda: task.cancelled())
    assert task.cancelled()


@pytest.mark.anyio
async def test_pause_resume_unwatched_ticker_returns_false():
    # Idempotency / honesty at the manager layer: pause/resume of a not-watched ticker is a quiet
    # False (the route turns this into a 404) — never a fabricated engine.
    manager = WatchManager(CONFIG)
    assert manager.pause("SIM-SELLER") is False
    assert manager.resume("SIM-SELLER") is False


@pytest.mark.anyio
async def test_double_pause_and_resume_when_not_paused_no_duplicate_feeder():
    # Idempotency over the feeder: a second pause does not spawn a second task or a second status
    # owner, and resume-when-not-paused is a quiet no-op.
    manager = WatchManager(CONFIG, pace=0.001)
    engine = manager.watch("SIM-BUYER")
    task = manager._tasks["SIM-BUYER"]
    await _until(lambda: engine.snapshot().stream_status == "live")

    assert manager.pause("SIM-BUYER") is True
    assert manager.pause("SIM-BUYER") is True  # second pause: no-op, still True (idempotent)
    assert manager._tasks["SIM-BUYER"] is task  # NO duplicate feeder task
    await _until(lambda: engine.snapshot().stream_status == "paused")

    assert manager.resume("SIM-BUYER") is True
    await _until(lambda: engine.snapshot().stream_status == "live")
    assert manager.resume("SIM-BUYER") is True  # resume-when-not-paused: quiet no-op, still True
    assert engine.snapshot().paused is False
    assert manager._tasks["SIM-BUYER"] is task  # still the one feeder

    assert manager.stop("SIM-BUYER") is True
    await _until(lambda: task.cancelled())


@pytest.mark.anyio
async def test_paused_sim_feeder_resumes_from_where_it_left_off():
    # Paced sim replay: pause freezes feeding; resume continues the SAME stream from where it left
    # off (no restart, no skip) and the count climbs again — deterministic continuation.
    manager = WatchManager(CONFIG, pace=0.002)
    engine = manager.watch("SIM-BUYER")
    await _until(lambda: engine.snapshot().event_count >= 20)

    assert manager.pause("SIM-BUYER") is True
    await _until(lambda: engine.snapshot().stream_status == "paused")
    frozen = engine.snapshot().event_count
    await asyncio.sleep(0.1)  # while paused the count must not advance
    assert engine.snapshot().event_count == frozen

    assert manager.resume("SIM-BUYER") is True
    await _until(lambda: engine.snapshot().event_count > frozen)  # feeding continued
    assert engine.snapshot().stream_status == "live"

    assert manager.stop("SIM-BUYER") is True
