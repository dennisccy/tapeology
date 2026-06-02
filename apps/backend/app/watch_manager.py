"""WatchManager — one in-memory engine instance per watched ticker, fed by the provider.

``watch`` validates the ticker against the simulated registry (never fabricates a provider
for an unknown ticker) and, when an event loop is running, starts a background feeder that
paces the provider's stream into the engine on wall-clock so the scenario resolves within
seconds in the browser. The feeder is the ONLY place wall-clock is used; the engine still
computes purely from logical event timestamps.
"""

from __future__ import annotations

import asyncio
import os

from .config import Config
from .engine.tape_engine import TapeEngine
from .providers.base import Provider
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

    def get(self, ticker: str) -> TapeEngine | None:
        return self._engines.get(ticker)

    async def _feed(self, engine: TapeEngine, provider: Provider) -> None:
        try:
            for event in provider.stream():
                engine.process_event(event)
                await asyncio.sleep(self._pace)
            engine.set_stream_status("closed")
        except asyncio.CancelledError:
            engine.set_stream_status("closed")
            raise

    async def shutdown(self) -> None:
        for task in self._tasks.values():
            task.cancel()
