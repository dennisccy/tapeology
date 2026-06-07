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
import logging
import os

from .config import Config
from .engine.tape_engine import TapeEngine
from .providers.base import AsyncProvider, Provider
from .providers.simulated import build_provider

# Wall-clock seconds between delivered events in live mode (delivery pacing only).
FEED_PACE_SECONDS = float(os.environ.get("TAPEOLOGY_FEED_PACE", "0.04"))

# Server-side logger for feeder lifecycle. A background-feeder failure MUST be LOGGED (a real,
# inspectable line naming the ticker), never swallowed in the task — the no-mute-cockpit / no-
# silent-dead-clicks anti-goal. The status flip to "failed" is what surfaces it to the UI.
logger = logging.getLogger(__name__)


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

    def pause(self, ticker: str) -> bool:
        """Freeze the watch WITHOUT tearing it down (J-19) — the deliberate opposite of stop().

        Sets the engine's canonical paused flag (which flips stream_status to "paused"); the feeder
        task is left ALIVE and the engine stays registered. The paced feeders then poll the paused
        flag and stop applying events (consuming nothing, so replay resumes where it left off); the
        live feeder keeps its socket OPEN but stops applying events. NO catch-up is fabricated on
        resume. Idempotent: a second pause is a no-op (returns True). Returns False (no exception)
        when the ticker is not being watched (the route turns this into a 404) — no fabricated engine.
        """
        engine = self._engines.get(ticker)
        if engine is None:
            return False
        engine.pause()
        return True

    def resume(self, ticker: str) -> bool:
        """Continue a paused watch (J-19): clear paused and restore the prior pre-pause status.

        The feeder (still alive) resumes applying the next real events; nothing is synthesized to
        cover the pause. Idempotent: resume-when-not-paused is a no-op (returns True). Returns False
        for a not-watched ticker (-> 404), never fabricating an engine.
        """
        engine = self._engines.get(ticker)
        if engine is None:
            return False
        engine.resume()
        return True

    async def _wait_while_paused(self, engine: TapeEngine) -> None:
        """Block (without consuming the provider stream) while the engine is paused.

        Polling the paused flag here — rather than letting the loop pull-and-discard events —
        is what makes a paused paced/sim replay resume EXACTLY where it left off (it consumes
        nothing while frozen) and a paused live feed stop applying without closing the socket.
        Cancellation still propagates (asyncio.sleep is a cancel point), so stop() during a pause
        tears down normally.
        """
        while engine.paused:
            await asyncio.sleep(self._config.pause_poll_seconds)

    async def _feed(self, engine: TapeEngine, provider: Provider) -> None:
        # Stream is open but no event applied yet -> `waiting` (not a frozen `connecting`); the
        # first process_event promotes it to `live`. A finite sim stream then resolves to
        # `live`-or-`closed` by exhaustion, so no extra timer is needed here.
        engine.set_stream_status("waiting")
        try:
            for event in provider.stream():
                await self._wait_while_paused(engine)  # freeze in place while paused (no consume)
                engine.process_event(event)
                await asyncio.sleep(self._pace)
            engine.set_stream_status("closed")
        except asyncio.CancelledError:
            engine.set_stream_status("closed")  # a clean stop/switch — NOT a failure
            raise
        except Exception:
            # A real feeder failure: log it server-side (naming the ticker) and surface it as
            # `failed` so the cockpit shows an explicit error instead of freezing at cold-start.
            # Never swallowed; the engine is left at `failed`, never a fabricated `live`.
            logger.exception("paced/sim feeder for %s failed", engine.snapshot().ticker)
            engine.set_stream_status("failed")

    async def _feed_paced(
        self, engine: TapeEngine, provider: Provider, speed: float
    ) -> None:
        """Feed a provider's stream pacing delivery by each event's logical gap / ``speed``.

        The wall-clock delay between two events is their logical-timestamp gap divided by the
        replay speed, clamped to ``config.replay_pacing_cap_seconds`` so a large quiet gap never
        stalls the cockpit. Pacing is delivery-only; the engine still computes purely from the
        logical timestamps, so the replay stays deterministic. Cancellable like the sim feeder.

        WARM-UP FAST-FORWARD (J-29): the first up-to-``warmup_min_events`` events are delivered with
        a tiny fixed pace (``config.warmup_fast_forward_pace_seconds``) instead of their logical
        gaps, so the cockpit reaches a WARM read quickly rather than waiting out the real timeline
        of the warm-up window; normal logical-gap pacing resumes once warmed. This changes ONLY the
        wall-clock sleep between deliveries — every event still enters the engine in the same order
        with its same logical timestamp, so the resulting features/state/confidence are IDENTICAL
        to an un-fast-forwarded replay (the engine never reads wall-clock; determinism preserved).
        """
        cap = self._config.replay_pacing_cap_seconds
        divisor = speed if speed > 0 else 1.0
        warmup_count = self._config.warmup_min_events
        ff_pace = self._config.warmup_fast_forward_pace_seconds
        # Stream open, no event applied yet -> `waiting`; the first process_event promotes to
        # `live`. A finite historical window resolves to `live`-or-`closed` by exhaustion.
        engine.set_stream_status("waiting")
        try:
            prev_ts: float | None = None
            delivered = 0
            for event in provider.stream():
                # Freeze in place while paused BEFORE consuming this event, so a paused historical
                # replay resumes from exactly here (the next event), with no fabricated catch-up.
                await self._wait_while_paused(engine)
                if prev_ts is not None:
                    if delivered < warmup_count:
                        # Warm-up fast-forward: deliver promptly (delivery pacing only — the event's
                        # logical timestamp below is unchanged, so engine math is identical).
                        delay = ff_pace
                    else:
                        delay = min((event.timestamp - prev_ts) / divisor, cap)
                    if delay > 0:
                        await asyncio.sleep(delay)
                prev_ts = event.timestamp
                engine.process_event(event)
                delivered += 1
            engine.set_stream_status("closed")
        except asyncio.CancelledError:
            engine.set_stream_status("closed")  # a clean stop/switch — NOT a failure
            raise
        except Exception:
            # A real replay-feeder failure: log it (naming the ticker) and surface `failed` — never
            # swallowed, never left frozen at cold-start, never a fabricated `live`.
            logger.exception("historical replay feeder for %s failed", engine.snapshot().ticker)
            engine.set_stream_status("failed")

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

        class _Failure:
            """Sentinel carrying a provider/stream exception from the puller to the main loop.

            The provider may raise inside the puller's ``async for`` (a live-feed failure), which
            would otherwise die silently in the puller task. Wrapping it and enqueuing it lets the
            main loop surface it as ``failed`` + log it — never swallowed (the no-mute-cockpit
            anti-goal). A ``CancelledError`` is NOT wrapped here — it is re-raised so a clean
            teardown stays a cancel, not a failure.
            """

            def __init__(self, error: BaseException) -> None:
                self.error = error

        async def _pull() -> None:
            try:
                async for event in stream:
                    await queue.put(event)
            except asyncio.CancelledError:
                raise  # clean teardown — let the cancel propagate (not a failure)
            except Exception as exc:  # a real provider/stream failure
                await queue.put(_Failure(exc))
                return
            await queue.put(done)  # reached only on natural exhaustion (skipped on cancel)

        puller = asyncio.create_task(_pull())
        # Stream is open and the puller is draining it, but no event has been applied yet ->
        # `waiting` (not a frozen `connecting`, and never a confident `live` over an empty tape).
        # The first event promotes it to `live`; the stale watchdog below bounds it to `stale` if no
        # event ever arrives (off-hours / quiet feed), so it never sits on `waiting` forever.
        engine.set_stream_status("waiting")
        try:
            while True:
                # Honest pause for LIVE: the puller keeps draining the socket (socket stays OPEN,
                # no unsubscribe/close — the iter-4 deadlock lesson), but while paused we apply
                # NOTHING and DISCARD anything that queued during the gap. Resume therefore rejoins
                # CURRENT real data with no synthesized catch-up (a replay of the gap would be a
                # fabricated backfill). The engine owns the "paused" status; we do not touch it here.
                if engine.paused:
                    while not queue.empty():
                        discarded = queue.get_nowait()
                        if discarded is done:
                            # The stream ended while paused: stop discarding, fall through so the
                            # loop sees `done` after resume and closes honestly.
                            queue.put_nowait(done)
                            break
                        if isinstance(discarded, _Failure):
                            # A feeder failure during pause must NOT be discarded/swallowed: re-queue
                            # it so the loop surfaces `failed` after resume (no-swallow anti-goal).
                            queue.put_nowait(discarded)
                            break
                    await asyncio.sleep(self._config.pause_poll_seconds)
                    continue
                try:
                    event = await asyncio.wait_for(queue.get(), stale_gap)
                except asyncio.TimeoutError:
                    if engine.paused:
                        continue  # paused mid-wait: loop back into the freeze branch
                    # Honest stale — bounds BOTH a `waiting` (no first event ever, off-hours/quiet
                    # feed) and a `live` gap; fabricates no trade. Never sits on `waiting` forever.
                    engine.set_stream_status("stale")
                    continue
                if event is done:
                    break
                if isinstance(event, _Failure):
                    # The provider/stream raised in the puller: surface it as `failed` + log it
                    # (naming the ticker). Re-raised below so the failure path runs the bounded
                    # `aclose()` teardown (no synchronous unsubscribe — the iter-4 deadlock lesson).
                    raise event.error
                if engine.paused:
                    continue  # raced into pause after dequeue: drop this event (no backfill)
                engine.process_event(event)
                if engine.snapshot().stream_status != "live":
                    engine.set_stream_status("live")  # owns the stale->live recovery flip
            engine.set_stream_status("closed")
        except asyncio.CancelledError:
            engine.set_stream_status("closed")  # a clean stop/switch — NOT a failure
            raise
        except Exception:
            # A real live-feeder failure (the provider raised, or the loop body failed): log it
            # server-side (naming the ticker) and surface `failed` — never swallowed, never frozen
            # at cold-start, never a fabricated `live`. The `finally` below still tears the socket
            # down via the bounded `aclose()` path (no synchronous unsubscribe in this branch).
            logger.exception("live feeder for %s failed", engine.snapshot().ticker)
            engine.set_stream_status("failed")
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
