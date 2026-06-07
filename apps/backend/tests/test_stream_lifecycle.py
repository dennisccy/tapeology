"""Post-connect stream lifecycle (J-25 / J-26 / J-27): the engine/feeder ALWAYS resolves a
connected watch to an honest non-idle terminal `stream_status` — never a frozen `connecting`,
never a confident `live` over an empty tape, never a swallowed feeder failure.

These tests prove the two engine-owned post-connect statuses added this iteration, both written
ONCE by the engine/feeder (no second status writer, no fabricated data):

  * `waiting` — the stream is OPEN but no first event has arrived yet (between `connecting` and
    `live`). A connected-but-quiet feed reads `waiting`, not a frozen `connecting` and never a
    confident `live`; for the live feeder it then bounds out to `stale` after `stale_gap_seconds`
    with NO trade fabricated during the wait.
  * `failed` — the background feeder raised (a non-`CancelledError` `Exception`). It is LOGGED
    server-side (naming the ticker, asserted via `caplog`) and the status flips to `failed` — the
    failure is surfaced, never swallowed, and the engine is not left frozen at cold-start nor faked
    to `live`. A clean stop/switch (`CancelledError`) stays `closed` and is NOT reported as failed.

Both the paced/sim feeder (`_feed` / `_feed_paced`) and the live feeder (`_feed_live`) are status
owners, so each rung is proven on both. The provider doubles live behind the provider seam
(`tests/fakes.py` + the small sync doubles here) — never the production vendor path.
"""

from __future__ import annotations

import asyncio
import dataclasses
import itertools
import logging

import pytest

from app.config import CONFIG
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.providers.simulated import SimulatedProvider
from app.watch_manager import WatchManager
from fakes import FakeLiveProvider

pytestmark = pytest.mark.anyio  # every test here drives an async feeder

# A tiny stale-gap so the live `waiting`->`stale` watchdog fires in milliseconds (mirrors the
# existing live/pause tests). No new config literal — this reuses the registered field.
FAST_STALE = dataclasses.replace(CONFIG, stale_gap_seconds=0.05)


async def _until(predicate, timeout: float = 3.0, step: float = 0.005) -> None:
    elapsed = 0.0
    while elapsed < timeout:
        if predicate():
            return
        await asyncio.sleep(step)
        elapsed += step
    raise AssertionError("condition not met within timeout")


def _buyer_events(n: int):
    return list(itertools.islice(SimulatedProvider("SIM-BUYER", "buyer_control").stream(), n))


# --- Sync provider doubles behind the seam (the paced/sim feeder path) -----------------------


class _StatusRecordingProvider:
    """A finite sync ``Provider`` that records the engine status at the moment its stream is first
    pulled — the exact "stream open, first event not yet applied" instant the `waiting` rung must
    cover. It yields a few buyer events so the feeder then promotes `waiting`->`live`."""

    def __init__(self, engine_box: list, ticker: str = "SIM-BUYER") -> None:
        self.ticker = ticker
        self.scenario = "buyer_control"
        self._engine_box = engine_box  # filled with the engine after construction
        self.status_at_first_pull: str | None = None
        self._events = _buyer_events(60)

    def stream(self):
        first = True
        for event in self._events:
            if first:
                # The feeder has opened the stream and is pulling the FIRST event but has not yet
                # applied it — the status must already read `waiting` here (not `connecting`).
                self.status_at_first_pull = self._engine_box[0].snapshot().stream_status
                first = False
            yield event


class _RaisingProvider:
    """A sync ``Provider`` whose stream RAISES after yielding ``before`` events — models a feeder
    that fails mid-stream (or, with ``before=0``, before any event)."""

    def __init__(self, before: int = 0, ticker: str = "SIM-BUYER") -> None:
        self.ticker = ticker
        self.scenario = "buyer_control"
        self._before = before

    def stream(self):
        for event in _buyer_events(self._before):
            yield event
        raise RuntimeError("simulated paced-feeder failure")


# === waiting rung — paced/sim feeder =========================================================


async def test_paced_feeder_sets_waiting_on_stream_open_before_first_event():
    """The paced/sim feeder sets `stream_status == "waiting"` once the provider stream is open but
    BEFORE the first event is applied (it must NOT be a frozen `connecting`, and NOT yet `live`)."""
    manager = WatchManager(CONFIG, pace=0.001)
    box: list = []
    provider = _StatusRecordingProvider(box)
    engine = manager.watch_with_provider("SIM-BUYER", provider, speed=1.0)
    box.append(engine)

    # The very first pull of the stream observed `waiting` (open, first event not yet applied).
    await _until(lambda: provider.status_at_first_pull is not None)
    assert provider.status_at_first_pull == "waiting"
    manager.stop("SIM-BUYER")


async def test_paced_feeder_promotes_waiting_to_live_on_first_event():
    """The first real event flips `waiting`->`live` (rung order holds; J-01 behaviour unchanged)."""
    manager = WatchManager(CONFIG, pace=0.001)
    box: list = []
    provider = _StatusRecordingProvider(box)
    engine = manager.watch_with_provider("SIM-BUYER", provider, speed=1.0)
    box.append(engine)

    await _until(lambda: engine.snapshot().stream_status == "live")
    assert engine.snapshot().event_count > 0  # a real event drove the promotion
    manager.stop("SIM-BUYER")


# === failed rung — paced/sim feeder ==========================================================


async def test_paced_feeder_failure_flips_failed_and_is_logged(caplog):
    """A paced feeder whose provider RAISES ends `stream_status == "failed"` AND logs a server-side
    record naming the ticker — the failure is surfaced, not swallowed, and the engine is neither
    frozen at cold-start nor fabricated to `live`."""
    manager = WatchManager(CONFIG, pace=0.001)
    provider = _RaisingProvider(before=0, ticker="SIM-BUYER")
    with caplog.at_level(logging.ERROR):
        engine = manager.watch_with_provider("SIM-BUYER", provider, speed=1.0)
        await _until(lambda: engine.snapshot().stream_status == "failed")

    snap = engine.snapshot()
    assert snap.stream_status == "failed"
    assert snap.stream_status not in ("connecting", "live")  # not frozen, not faked
    assert snap.event_count == 0  # raised before any event => no fabricated trade
    # The failure was LOGGED server-side, naming the ticker (assert via caplog) — never swallowed.
    assert any(
        rec.levelno >= logging.ERROR and "SIM-BUYER" in rec.getMessage() for rec in caplog.records
    ), f"expected a logged feeder failure naming the ticker; got {[r.getMessage() for r in caplog.records]}"


async def test_paced_feeder_failure_mid_stream_flips_failed(caplog):
    """A paced feeder that raises AFTER some events still ends `failed` (post-frame failure path)."""
    manager = WatchManager(CONFIG, pace=0.001)
    # 10 interleaved quote+trade events (event_count tracks TRADES, ~half of these) precede the
    # raise; we assert the pre-failure trades applied and that NONE were fabricated past them.
    provider = _RaisingProvider(before=10, ticker="SIM-BUYER")
    with caplog.at_level(logging.ERROR):
        engine = manager.watch_with_provider("SIM-BUYER", provider, speed=1.0)
        await _until(lambda: engine.snapshot().stream_status == "failed")
    snap = engine.snapshot()
    assert snap.stream_status == "failed"
    # Some pre-failure trades applied; never more trades than the events the provider yielded
    # (no fabricated catch-up past the failure point).
    assert 0 < snap.event_count <= 10


# === cancel is NOT a failure — paced/sim feeder ==============================================


async def test_paced_feeder_cancel_ends_closed_not_failed():
    """A clean stop/switch (cancel) still ends `closed` — a cancel is NOT reported as `failed`."""
    manager = WatchManager(CONFIG, pace=0.05)
    # A long buyer stream so the feeder is mid-flight (not exhausted) when we stop it.
    provider = SimulatedProvider("SIM-BUYER", "buyer_control")
    engine = manager.watch_with_provider("SIM-BUYER", provider, speed=1.0)
    await asyncio.sleep(0.02)  # let the feeder open the stream / process a beat
    assert manager.stop("SIM-BUYER") is True
    await asyncio.sleep(0.02)  # let the cancellation propagate through the feeder
    assert engine.snapshot().stream_status == "closed"  # clean teardown, never `failed`


# === waiting / stale / failed / cancel — LIVE feeder =========================================


async def test_live_feeder_sets_waiting_then_bounds_to_stale_with_no_fabrication():
    """A connected LIVE feeder with NO first event reads `waiting` (never a confident `live`), then
    bounds out to `stale` after `stale_gap_seconds` — and fabricates NO trade during the wait."""
    manager = WatchManager(FAST_STALE)
    provider = FakeLiveProvider("AAPL", "live AAPL")  # queue empty: no event ever arrives
    engine = manager.watch_with_async_provider("AAPL", provider)
    try:
        # Before the stale gap elapses the connected-but-empty stream reads `waiting`, not `live`
        # and not a frozen `connecting`.
        await _until(lambda: engine.snapshot().stream_status == "waiting")
        assert engine.snapshot().stream_status == "waiting"
        assert engine.snapshot().event_count == 0
        assert engine.snapshot().tape_state == "unclear"  # honest cold read, never a fake call

        # After stale_gap_seconds with still no event it bounds to `stale` (the no-mute-cockpit
        # bound). No trade/quote was fabricated during the wait.
        await _until(lambda: engine.snapshot().stream_status == "stale")
        assert engine.snapshot().stream_status == "stale"
        assert engine.snapshot().event_count == 0
        assert not engine.snapshot().recent_trades
    finally:
        manager.stop("AAPL")


async def test_live_feeder_promotes_waiting_to_live_on_first_event():
    """The first real LIVE event flips `waiting`->`live` (rung order holds; J-12 unchanged)."""
    manager = WatchManager(FAST_STALE)
    provider = FakeLiveProvider("AAPL", "live AAPL")
    engine = manager.watch_with_async_provider("AAPL", provider)
    try:
        await _until(lambda: engine.snapshot().stream_status == "waiting")
        await provider.feed(QuoteEvent("AAPL", 0.0, 100.0, 100.02, 100, 100))
        await provider.feed(TradeEvent("AAPL", 0.0, 100.02, 100, Side.UNKNOWN))
        await _until(lambda: engine.snapshot().stream_status == "live")
        assert engine.snapshot().event_count >= 1
    finally:
        manager.stop("AAPL")


async def test_live_feeder_failure_flips_failed_and_is_logged(caplog):
    """A LIVE feeder whose provider RAISES mid-stream ends `stream_status == "failed"` AND logs a
    server-side record naming the ticker; the engine is not frozen at cold-start / faked to live."""

    class _RaisingLiveProvider:
        ticker = "AAPL"
        scenario = "live AAPL"

        async def stream(self):
            if False:
                yield  # make this an async generator
            raise RuntimeError("simulated live-feeder failure")

    manager = WatchManager(FAST_STALE)
    provider = _RaisingLiveProvider()
    with caplog.at_level(logging.ERROR):
        engine = manager.watch_with_async_provider("AAPL", provider)
        await _until(lambda: engine.snapshot().stream_status == "failed")

    snap = engine.snapshot()
    assert snap.stream_status == "failed"
    assert snap.stream_status not in ("connecting", "live")
    assert snap.event_count == 0  # raised before any event => no fabricated trade
    assert any(
        rec.levelno >= logging.ERROR and "AAPL" in rec.getMessage() for rec in caplog.records
    ), f"expected a logged live-feeder failure naming the ticker; got {[r.getMessage() for r in caplog.records]}"


async def test_live_feeder_cancel_during_waiting_ends_closed_not_failed():
    """Cancel/stop during the live `waiting` phase ends `closed` (clean teardown, socket closed) —
    a cancel is NEVER reported as `failed`."""
    manager = WatchManager(FAST_STALE)
    provider = FakeLiveProvider("AAPL", "live AAPL")  # never feeds: stays in waiting
    engine = manager.watch_with_async_provider("AAPL", provider)
    await _until(lambda: engine.snapshot().stream_status == "waiting")
    assert manager.stop("AAPL") is True
    assert engine.snapshot().stream_status == "closed"  # clean stop, not `failed`
    await _until(lambda: provider.socket.closed)
    assert provider.socket.closed  # no leaked socket on teardown
