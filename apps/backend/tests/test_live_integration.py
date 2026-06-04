"""Operator/gated REAL Alpaca live-socket check (J-12 / J-15) — out-of-loop, not hermetic.

Per `.claude/core.md` (External Integration Testing) the hermetic suite alone is NOT sufficient
evidence the real integration works. This is the runnable proof that the genuine Alpaca live
WebSocket streams real trades+quotes through the SAME engine and reads `live`. It is **gated**:
it requires real credentials, market hours, and an explicit opt-in, so it is SKIPPED in the
autonomous loop (off-hours / no opt-in) and never makes a network call by accident.

Run it (operator, during US market hours, creds in apps/backend/.env):

    TAPEOLOGY_LIVE_INTEGRATION=1 .venv/bin/python -m pytest tests/test_live_integration.py -v -s

Prefer a tight/penny-spread liquid name (iter-2 IEX lesson): TAPEOLOGY_LIVE_SYMBOL=F (default).
A high-priced name on the wide free IEX top-of-book may honestly read `unclear` — that is correct,
not a failure of this check (it asserts the live PIPELINE works, not a specific tape state).
"""

import asyncio
import contextlib
import os

import pytest

from app.config import CONFIG
from app.providers.adapters.alpaca import AlpacaAdapter
from app.providers.live import LiveProvider
from app.watch_manager import WatchManager

VALID_STATES = {"buyer_control", "seller_control", "bid_absorption", "ask_absorption", "unclear"}

pytestmark = pytest.mark.integration


@pytest.mark.anyio
async def test_real_alpaca_live_socket_streams_and_reads_live():
    if os.environ.get("TAPEOLOGY_LIVE_INTEGRATION") != "1":
        pytest.skip("gated: set TAPEOLOGY_LIVE_INTEGRATION=1 to run the real live-socket check")
    adapter = AlpacaAdapter()
    if not adapter.is_available():
        pytest.skip("gated: Alpaca credentials not configured in the environment")
    clock = adapter.get_market_clock()
    if not clock.is_open:
        pytest.skip(f"gated: market is closed (next open {clock.next_open})")

    symbol = os.environ.get("TAPEOLOGY_LIVE_SYMBOL", "F").upper()
    manager = WatchManager(CONFIG)
    provider = LiveProvider(symbol, adapter.stream_live(symbol), f"live {symbol}")
    engine = manager.watch_with_async_provider(symbol, provider)
    task = manager._tasks[symbol]  # capture the feeder so teardown can await its graceful close
    try:
        # Wait up to 45s for real events to arrive and the status to read `live`.
        deadline = 45.0
        elapsed = 0.0
        while elapsed < deadline and not (
            engine.snapshot().stream_status == "live" and engine.snapshot().event_count > 0
        ):
            await asyncio.sleep(0.5)
            elapsed += 0.5
        snap = engine.snapshot()
        assert snap.stream_status == "live", f"no live events within {deadline}s"
        assert snap.event_count > 0
        assert snap.bid is not None and snap.ask is not None
        assert snap.tape_state in VALID_STATES
        assert snap.scenario == f"live {symbol}"
    finally:
        assert manager.stop(symbol) is True  # cancels the feeder; its teardown closes the socket
        # Wait for the feeder to finish (it ends cancelled; its finally closes the real socket).
        # CancelledError is a BaseException, so suppress it explicitly alongside Exception.
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await task
