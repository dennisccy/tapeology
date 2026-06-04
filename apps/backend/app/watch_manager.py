"""WatchManager — one in-memory engine instance per watched ticker, fed by the provider.

``watch`` validates the ticker against the simulated registry (never fabricates a provider
for an unknown ticker) and, when an event loop is running, starts a background feeder that
paces the provider's stream into the engine on wall-clock so the scenario resolves within
seconds in the browser. The feeder is the ONLY place wall-clock is used; the engine still
computes purely from logical event timestamps.
"""

from __future__ import annotations

import asyncio
import contextlib
import os

from .config import Config
from .engine.tape_engine import TapeEngine
from .providers.base import AsyncProvider, Provider
from .providers.simulated import build_provider

# Wall-clock seconds between delivered events in live mode (delivery pacing only).
FEED_PACE_SECONDS = float(os.environ.get("TAPEOLOGY_FEED_PACE", "0.04"))


class UnknownTickerError(Exception):
    """Raised when asked to watch a ticker that is not a known simulated ticker."""


class WatchManager:
    def __init__(self, config: Config, pace: float = FEED_PACE_SECONDS) -> None:
        self._config = config
        self._pace = pace
        self._engines: dict[str, TapeEngine] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def is_known(self, ticker: str) -> bool:
        return build_provider(ticker) is not None

    def watch(self, ticker: str) -> TapeEngine:
        provider = build_provider(ticker)
        if provider is None:
            raise UnknownTickerError(ticker)

        existing = self._engines.get(ticker)
        if existing is not None:
            return existing

        engine = TapeEngine(ticker, provider.scenario, self._config)
        self._engines[ticker] = engine
        try:
            loop = asyncio.get_running_loop()
            self._tasks[ticker] = loop.create_task(self._feed(engine, provider))
        except RuntimeError:
            # No running loop (synchronous context): the caller feeds the engine itself.
            pass
        return engine

    def watch_with_provider(
        self, ticker: str, provider: Provider, speed: float = 1.0
    ) -> TapeEngine:
        """Watch ``ticker`` fed by an arbitrary ``Provider`` (e.g. the historical replay),
        WITHOUT touching the simulated registry.

        Any existing watch for the ticker is torn down first (a switch/re-watch cancels the
        prior feeder and starts a fresh, cold engine — the orphaned-watch lesson). The replay
        feeder is registered in ``self._tasks`` so ``stop()`` and a switch already cancel it.
        """
        self.stop(ticker)  # tear down any prior watch for this ticker (no orphaned feeder)
        engine = TapeEngine(ticker, provider.scenario, self._config)
        self._engines[ticker] = engine
        try:
            loop = asyncio.get_running_loop()
            self._tasks[ticker] = loop.create_task(
                self._feed_paced(engine, provider, speed)
            )
        except RuntimeError:
            # No running loop (synchronous context): the caller feeds the engine itself.
            pass
        return engine

    def watch_with_async_provider(
        self, ticker: str, provider: AsyncProvider
    ) -> TapeEngine:
        """Watch ``ticker`` fed by an async (live) provider, WITHOUT touching the sim registry.

        Any existing watch for the ticker is torn down first (a switch/re-watch cancels the prior
        feeder — the orphaned-watch lesson; for a live socket that teardown is a genuine vendor
        connection close, not a sim no-op). The live feeder is registered in ``self._tasks`` so
        ``stop()`` / a switch / ``shutdown`` already cancel it, and the feeder additionally closes
        the vendor socket on cancel (see ``_feed_live``). A live watch is only ever started on the
        event loop (the ``POST /watch`` route is async).
        """
        self.stop(ticker)  # tear down any prior watch for this ticker (no orphaned feeder/socket)
        engine = TapeEngine(ticker, provider.scenario, self._config)
        self._engines[ticker] = engine
        try:
            loop = asyncio.get_running_loop()
            self._tasks[ticker] = loop.create_task(self._feed_live(engine, provider))
        except RuntimeError:
            # No running loop: an async live feed cannot run; leave the engine without a feeder
            # (it stays in its honest cold-start "connecting" read). In practice the route always
            # runs on the loop, so this branch is only hit by a synchronous caller.
            pass
        return engine

    def get(self, ticker: str) -> TapeEngine | None:
        return self._engines.get(ticker)

    def stop(self, ticker: str) -> bool:
        """Stop watching ``ticker``: cancel its feeder, mark the engine closed, and remove it.

        Removing the engine is what makes a later ``watch()`` build a fresh, cold engine
        (satisfying "re-watch starts a fresh read") instead of returning the exhausted one.
        Idempotent: returns ``False`` (no exception) when the ticker was not being watched.
        """
        engine = self._engines.get(ticker)
        if engine is None:
            return False
        task = self._tasks.pop(ticker, None)
        if task is not None:
            task.cancel()
        engine.set_stream_status("closed")
        del self._engines[ticker]
        return True

    async def _feed(self, engine: TapeEngine, provider: Provider) -> None:
        try:
            for event in provider.stream():
                engine.process_event(event)
                await asyncio.sleep(self._pace)
            engine.set_stream_status("closed")
        except asyncio.CancelledError:
            engine.set_stream_status("closed")
            raise

    async def _feed_paced(
        self, engine: TapeEngine, provider: Provider, speed: float
    ) -> None:
        """Feed a provider's stream pacing delivery by each event's logical gap / ``speed``.

        The wall-clock delay between two events is their logical-timestamp gap divided by the
        replay speed, clamped to ``config.replay_pacing_cap_seconds`` so a large quiet gap never
        stalls the cockpit. Pacing is delivery-only; the engine still computes purely from the
        logical timestamps, so the replay stays deterministic. Cancellable like the sim feeder.
        """
        cap = self._config.replay_pacing_cap_seconds
        divisor = speed if speed > 0 else 1.0
        try:
            prev_ts: float | None = None
            for event in provider.stream():
                if prev_ts is not None:
                    delay = min((event.timestamp - prev_ts) / divisor, cap)
                    if delay > 0:
                        await asyncio.sleep(delay)
                prev_ts = event.timestamp
                engine.process_event(event)
            engine.set_stream_status("closed")
        except asyncio.CancelledError:
            engine.set_stream_status("closed")
            raise

    async def _feed_live(self, engine: TapeEngine, provider: AsyncProvider) -> None:
        """Feed an async (live) provider into the engine with a stale watchdog (J-12 / J-15).

        Each arriving event is processed into the engine and the status is ensured ``live`` — the
        engine only auto-flips ``connecting``→``live``, NOT ``stale``→``live``, so the feeder owns
        the recovery flip. If NO event arrives within ``config.stale_gap_seconds`` the status flips
        to ``stale`` and **no trade is fabricated** during the lull; the next event flips it back
        to ``live``. On cancel (stop/switch/shutdown) the status is set ``closed`` and the
        provider stream is ``aclose()``d so the vendor socket is closed — no leaked connection.

        The provider's async generator is consumed by a single background *puller* task so the
        stale-gap ``wait_for`` times out on the queue (never on the generator itself) — timing out
        on ``__anext__`` directly would throw into the generator and could close the socket on a
        mere lull. On teardown the puller is cancelled and the stream is ``aclose()``d explicitly,
        which deterministically runs the generator's cleanup (socket close).
        """
        stale_gap = self._config.stale_gap_seconds
        stream = provider.stream()  # async iterator (unbounded)
        queue: asyncio.Queue = asyncio.Queue()
        done = object()  # sentinel: the stream ended on its own

        async def _pull() -> None:
            async for event in stream:
                await queue.put(event)
            await queue.put(done)  # reached only on natural exhaustion (skipped on cancel)

        puller = asyncio.create_task(_pull())
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), stale_gap)
                except asyncio.TimeoutError:
                    engine.set_stream_status("stale")  # honest stale — fabricates no trade
                    continue
                if event is done:
                    break
                engine.process_event(event)
                if engine.snapshot().stream_status != "live":
                    engine.set_stream_status("live")  # owns the stale->live recovery flip
            engine.set_stream_status("closed")
        except asyncio.CancelledError:
            engine.set_stream_status("closed")
            raise
        finally:
            puller.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await puller
            # Deterministically close the stream (and, via its cascade, the vendor socket) now
            # that the puller no longer touches the generator — no leaked connection.
            with contextlib.suppress(Exception):
                await stream.aclose()

    async def shutdown(self) -> None:
        for task in self._tasks.values():
            task.cancel()
