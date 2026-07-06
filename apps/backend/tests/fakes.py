"""Test seam: a fake market-data adapter + a loader for the committed REAL fixture.

The historical/search tests inject ``FakeAdapter`` via FastAPI ``dependency_overrides`` (a
standard DI seam) so the suite stays hermetic — no real network call, no prod env-var backdoor
in the live code path. ``load_fixture_window`` loads the committed REAL captured Alpaca window
into the same vendor-neutral ``HistoricalWindow`` the production adapter returns.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import AsyncIterator

from app.providers.adapters.base import (
    HistoricalWindow,
    LiveRecord,
    MarketClock,
    NoDataForWindow,
    RawBar,
    RawQuote,
    RawTrade,
    SymbolMatch,
    SymbolNotTradable,
    VendorTimeout,
)
from app.providers.base import Event

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "alpaca" / "F_20260602_150000_20260602_150200.json"
)


def load_fixture_window(path: Path = FIXTURE_PATH) -> tuple[HistoricalWindow, dict]:
    """Load the committed REAL fixture into a ``HistoricalWindow`` (and return the raw dict)."""
    data = json.loads(path.read_text())
    trades = tuple(RawTrade(t["epoch"], t["price"], t["size"]) for t in data["trades"])
    quotes = tuple(
        RawQuote(q["epoch"], q["bid"], q["ask"], q["bid_size"], q["ask_size"])
        for q in data["quotes"]
    )
    return HistoricalWindow(data["symbol"], trades, quotes), data


class FakeLiveSocket:
    """A stand-in vendor live socket that records its unsubscribe + close (no leak assertions).

    The live tests assert the feeder closes the socket on stop/switch/shutdown. A real leaked
    socket is an actual vendor connection leak (the iter-0 lesson), so ``closed`` /
    ``unsubscribed`` being set on teardown is the in-loop proof the cleanup path ran.
    """

    def __init__(self) -> None:
        self.closed = False
        self.unsubscribed = False

    def unsubscribe(self) -> None:
        self.unsubscribed = True

    def close(self) -> None:
        self.closed = True


class FakeLiveProvider:
    """An async (live) ``AsyncProvider`` double with full timing control over event arrival.

    Plays the role of ``LiveProvider`` behind the seam: ``stream()`` yields engine ``Event``s the
    test enqueues via ``feed``/``feed_nowait`` (so the test controls exactly when — and whether —
    the next event arrives, the lever the stale-watchdog test needs) and closes a ``FakeLiveSocket``
    in its ``finally`` so the lifecycle tests can assert the socket was closed. It is a legitimate
    test double behind the provider seam — NEVER wired into the production live path.
    """

    def __init__(self, ticker: str = "FAKE", scenario: str = "live FAKE") -> None:
        self.ticker = ticker
        self.scenario = scenario
        self.socket = FakeLiveSocket()
        self._queue: asyncio.Queue = asyncio.Queue()
        self._end = object()

    def feed_nowait(self, event: Event) -> None:
        """Enqueue an event for ``stream`` to yield next (non-blocking; for use inside a loop)."""
        self._queue.put_nowait(event)

    async def feed(self, event: Event) -> None:
        await self._queue.put(event)

    def end(self) -> None:
        """Signal natural end-of-stream (the feeder then flips the engine to ``closed``)."""
        self._queue.put_nowait(self._end)

    async def stream(self) -> AsyncIterator[Event]:
        try:
            while True:
                event = await self._queue.get()
                if event is self._end:
                    return
                yield event
        finally:
            self.socket.unsubscribe()
            self.socket.close()


class FakeAdapter:
    """A ``MarketDataAdapter`` stand-in driven entirely by constructor flags."""

    name = "fake"

    def __init__(
        self,
        *,
        available: bool = True,
        window: HistoricalWindow | None = None,
        not_tradable: bool = False,
        no_data: bool = False,
        matches: list[SymbolMatch] | None = None,
        search_raises: bool = False,
        clock: MarketClock | None = None,
        clock_raises: bool = False,
        fetch_hang_seconds: float = 0.0,
        clock_hang_seconds: float = 0.0,
        live_records: list[LiveRecord] | None = None,
        live_hold: asyncio.Event | None = None,
        fetch_timeout: bool = False,
        warm_raises: bool = False,
        bars: tuple[RawBar, ...] | None = None,
        bars_raise: Exception | None = None,
    ) -> None:
        self._available = available
        self._window = window
        self._not_tradable = not_tradable
        self._no_data = no_data
        self._matches = matches or []
        self._search_raises = search_raises
        self._clock = clock
        self._clock_raises = clock_raises
        # A slow/hung vendor: block the worker thread this many wall-clock seconds before
        # returning, so the per-call `asyncio.wait_for` bound (set tiny in the test) fires first
        # and the Watch is refused with `provider_timeout` — proving the no-unbounded-waits bound.
        self._fetch_hang_seconds = fetch_hang_seconds
        self._clock_hang_seconds = clock_hang_seconds
        # A REAL call-level timeout: raise the neutral VendorTimeout (the analogue of the real
        # adapter mapping a requests.Timeout) so the historical path's actionable-oversize message
        # is exercised end-to-end without a wall-clock block (J-28).
        self._fetch_timeout = fetch_timeout
        # `warm_symbol_universe` must NEVER raise (a warm failure is swallowed); this lets a test
        # assert that contract even when the underlying load would fail.
        self._warm_raises = warm_raises
        self._live_records = live_records or []
        self._live_hold = live_hold
        # Era-4 (J-01) bar-fetch scripting: ``bars`` is the tuple ``fetch_bars`` returns on
        # success (defaults to empty — a caller that needs real candles must pass some); a
        # scripted ``bars_raise`` exception (e.g. ``VendorTimeout``) is raised instead when set.
        self._bars = bars if bars is not None else ()
        self._bars_raise = bars_raise
        self.fetch_calls: list[tuple] = []
        self.fetch_bars_calls: list[tuple] = []
        self.search_calls: list[str] = []
        self.clock_calls = 0
        self.warm_calls = 0
        self.stream_live_calls: list[str] = []
        self.live_socket = FakeLiveSocket()

    def is_available(self) -> bool:
        return self._available

    def warm_symbol_universe(self) -> None:
        """Record a warm call (J-30). MUST NOT raise — a warm failure is swallowed so startup is
        never crashed; ``warm_raises`` proves that contract (the swallow happens in the adapter)."""
        self.warm_calls += 1
        if self._warm_raises:
            raise RuntimeError("simulated universe-warm failure")

    async def stream_live(self, symbol: str) -> AsyncIterator[LiveRecord]:
        """Yield the scripted neutral records, then (optionally) hold the stream open until
        released, closing the fake socket on teardown — the neutral-record analogue of the real
        adapter's ``stream_live`` (records close/unsubscribe so the no-leak path is asserted)."""
        self.stream_live_calls.append(symbol)
        try:
            for rec in self._live_records:
                yield rec
            if self._live_hold is not None:
                await self._live_hold.wait()  # keep the socket open (status stays live) until released
        finally:
            self.live_socket.unsubscribe()
            self.live_socket.close()

    def get_market_clock(self) -> MarketClock:
        # ``clock_raises`` models a degraded/unreachable vendor (the API must degrade to an
        # explicit unavailable, never fabricate a session); otherwise return the configured clock.
        self.clock_calls += 1
        if self._clock_hang_seconds:
            time.sleep(self._clock_hang_seconds)  # block the worker thread (simulated hung vendor)
        if self._clock_raises:
            raise RuntimeError("simulated market-clock failure")
        assert self._clock is not None, "FakeAdapter needs a clock for get_market_clock"
        return self._clock

    def fetch_historical(self, symbol: str, start, end) -> HistoricalWindow:
        self.fetch_calls.append((symbol, start, end))
        if self._fetch_hang_seconds:
            time.sleep(self._fetch_hang_seconds)  # block the worker thread (simulated hung vendor)
        if self._fetch_timeout:
            # The real call-level deadline fired inside the adapter: surface the NEUTRAL
            # VendorTimeout the API maps to provider_timeout (with the actionable oversize message).
            raise VendorTimeout("that window is very high-volume — try a shorter range")
        if self._not_tradable:
            raise SymbolNotTradable(symbol)
        if self._no_data:
            raise NoDataForWindow(symbol)
        assert self._window is not None, "FakeAdapter needs a window for a successful fetch"
        return self._window

    def fetch_bars(self, symbol: str, start, end, timeframe: str) -> tuple[RawBar, ...]:
        """The era-4 (J-01) bar-fetch analogue of ``fetch_historical`` — scripted, never real."""
        self.fetch_bars_calls.append((symbol, start, end, timeframe))
        if self._bars_raise is not None:
            raise self._bars_raise
        return self._bars

    def search_symbols(self, query: str) -> list[SymbolMatch]:
        self.search_calls.append(query)
        if self._search_raises:
            raise RuntimeError("simulated adapter failure")
        q = query.strip().upper()
        return [m for m in self._matches if q in m.symbol.upper() or q in m.name.upper()]
