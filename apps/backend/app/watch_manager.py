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
from typing import Callable

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


def _provider_anchor(provider: object) -> float | None:
    """Read the provider's canonical display/epoch anchor (row 13, J-31), if it exposes one.

    Every Phase-1 provider (sim / historical / live) carries an ``epoch_anchor`` attribute; this
    reads it defensively (``None`` for any provider/double that does not) so the engine receives
    the anchor ONCE here and surfaces it through the history projection. It is additive DISPLAY
    metadata — it never enters the engine's logical timeline or classification.
    """
    return getattr(provider, "epoch_anchor", None)


class WatchManager:
    def __init__(
        self,
        config: Config,
        pace: float = FEED_PACE_SECONDS,
        on_engine_created: "Callable[[str, TapeEngine], None] | None" = None,
    ) -> None:
        self._config = config
        self._pace = pace
        # Optional engine-created hook (the research seam, capability 20). When set, it is called
        # with each freshly-built engine so the research layer can attach its observer (the monitor)
        # at the ONE sanctioned attachment point. The WatchManager stays research-agnostic — it knows
        # nothing about the hook's payload and never imports a research type. Exception-isolated so a
        # hook error can never break a watch; default None keeps every existing test unchanged.
        self._on_engine_created = on_engine_created
        self._engines: dict[str, TapeEngine] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        # Per-ticker MUTABLE replay-speed holder (J-32). A single-element list is the small mutable
        # cell ``_feed_paced`` reads each loop iteration, so ``set_speed`` changes the in-progress
        # replay's pacing within ~1s with NO re-fetch, engine restart, or teardown. Speed is a
        # delivery-pacing divisor ONLY — the engine still processes the same ordered events with the
        # same logical timestamps, so features/state/confidence are byte-identical at any speed
        # (determinism preserved). Cleared in ``stop()``.
        self._speeds: dict[str, list[float]] = {}

    def set_on_engine_created(
        self, hook: "Callable[[str, TapeEngine], None] | None"
    ) -> None:
        """Set/replace the engine-created hook (used by the app to wire the research registry)."""
        self._on_engine_created = hook

    def _announce_engine(self, ticker: str, engine: TapeEngine) -> None:
        """Fire the engine-created hook (the research seam), exception-isolated.

        A hook failure is logged and swallowed HERE so it can never break a watch — the research
        layer is strictly additive and must never take the engine down (anti-goal: an observer
        failure never kills the feed). Called at every engine-construction site below."""
        if self._on_engine_created is None:
            return
        try:
            self._on_engine_created(ticker, engine)
        except Exception:
            logger.exception("on_engine_created hook failed for %s", ticker)

    def is_known(self, ticker: str) -> bool:
        return build_provider(ticker) is not None

    def watch(self, ticker: str) -> TapeEngine:
        provider = build_provider(ticker)
        if provider is None:
            raise UnknownTickerError(ticker)

        existing = self._engines.get(ticker)
        if existing is not None:
            return existing

        engine = TapeEngine(
            ticker, provider.scenario, self._config, epoch_anchor=_provider_anchor(provider)
        )
        self._engines[ticker] = engine
        # Attach research observers (if any) BEFORE the feeder starts so the monitor sees the first
        # event/status. Exception-isolated — a hook failure never breaks the watch.
        self._announce_engine(ticker, engine)
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
        engine = TapeEngine(
            ticker, provider.scenario, self._config, epoch_anchor=_provider_anchor(provider)
        )
        self._engines[ticker] = engine
        self._announce_engine(ticker, engine)  # attach research observers before the feeder starts
        # Register the per-ticker mutable speed cell BEFORE the feeder starts so ``set_speed`` (and
        # the feeder's per-iteration read) share the one holder. A non-positive speed is normalised
        # to 1.0 here (defensive) — the route already validates against the allowed set.
        speed_cell = [speed if speed > 0 else 1.0]
        self._speeds[ticker] = speed_cell
        try:
            loop = asyncio.get_running_loop()
            self._tasks[ticker] = loop.create_task(
                self._feed_paced(engine, provider, speed_cell)
            )
        except RuntimeError:
            # No running loop (synchronous context): the caller feeds the engine itself.
            pass
        return engine

    def watch_with_progressive_historical(
        self,
        ticker: str,
        first_chunk_provider: Provider,
        fetch_remaining,
        speed: float = 1.0,
    ) -> TapeEngine:
        """Watch a LONG historical window progressively (J-37): replay the FIRST chunk immediately
        while the REMAINING chunks are fetched in the background and appended in epoch order.

        ``first_chunk_provider`` is a ready ``HistoricalProvider`` over the already-fetched FIRST
        sub-window (so replay + the canonical epoch anchor begin within budget). ``fetch_remaining``
        is a zero-arg BLOCKING callable returning the remaining sub-windows as an ordered list of
        ``HistoricalWindow`` (it runs OFF the event loop via ``asyncio.to_thread`` inside the feeder,
        so a slow later chunk never blocks the loop or the already-running replay). The remaining
        chunks are stitched after the first in epoch order — the same real records, determinism +
        single-source-of-truth preserved (the engine bins on its logical timeline regardless of chunk
        boundaries). Any existing watch is torn down first (orphaned-watch lesson); the feeder is
        registered so stop()/switch/shutdown cancel it.
        """
        self.stop(ticker)
        engine = TapeEngine(
            ticker,
            first_chunk_provider.scenario,
            self._config,
            epoch_anchor=_provider_anchor(first_chunk_provider),
        )
        self._engines[ticker] = engine
        self._announce_engine(ticker, engine)  # attach research observers before the feeder starts
        speed_cell = [speed if speed > 0 else 1.0]
        self._speeds[ticker] = speed_cell
        try:
            loop = asyncio.get_running_loop()
            self._tasks[ticker] = loop.create_task(
                self._feed_progressive(engine, first_chunk_provider, fetch_remaining, speed_cell)
            )
        except RuntimeError:
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
        engine = TapeEngine(
            ticker, provider.scenario, self._config, epoch_anchor=_provider_anchor(provider)
        )
        self._engines[ticker] = engine
        self._announce_engine(ticker, engine)  # attach research observers before the feeder starts
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
        # Flip the engine to ``closed`` with the ``watch_stopped`` reason BEFORE cancelling the
        # feeder task, so the research monitor's on_status hook sees a USER stop (distinct from a
        # stream that ran out). The cancel runs later on the loop and its own ``closed`` flip carries
        # no reason — it will not overwrite this one (the monitor has already resolved by then).
        engine.set_stream_status("closed", end_reason="watch_stopped")
        task = self._tasks.pop(ticker, None)
        if task is not None:
            task.cancel()
        self._speeds.pop(ticker, None)  # drop the mutable speed cell (no cross-watch residue)
        del self._engines[ticker]
        return True

    def set_speed(self, ticker: str, speed: float) -> bool:
        """Set the replay speed of a RUNNING watch (J-32) — delivery pacing only, no teardown.

        Mutates the per-ticker speed cell that ``_feed_paced`` reads each loop iteration, so the
        change applies to the in-progress replay within ~1s with NO re-fetch, engine restart, or
        teardown (a change made while paused applies on resume — the pause gate is unchanged).
        Because speed only scales the wall-clock delay between deliveries — never the events' order
        or their logical timestamps — the resulting features/state/confidence for the window are
        byte-identical at any speed (determinism preserved). Returns ``False`` (no exception) when
        the ticker is not being watched, mirroring pause/resume — the route turns that into a 404;
        the caller (route) validates ``speed`` against the allowed set BEFORE calling this."""
        cell = self._speeds.get(ticker)
        if cell is None:
            return False
        cell[0] = speed if speed > 0 else 1.0
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
            # Natural exhaustion (the stream ran out) — reason ``stream_closed`` (distinct from a
            # user Stop, which set ``watch_stopped`` before cancelling this task). J-50's stream-end
            # leg depends on this reason.
            engine.set_stream_status("closed", end_reason="stream_closed")
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
        self, engine: TapeEngine, provider: Provider, speed: "float | list[float]"
    ) -> None:
        """Feed a provider's stream pacing delivery by each event's logical gap / ``speed``.

        ``speed`` is the per-ticker MUTABLE speed cell (a single-element list) so a live
        ``set_speed`` (J-32) takes effect on the in-progress replay: the divisor is re-read from the
        cell EACH loop iteration, not captured once, so changing it re-paces subsequent deliveries
        within ~1s with no re-fetch / restart / teardown. (A bare float is still accepted for the
        unit tests / legacy callers that pass a fixed speed — it is read once into a local cell.)

        The wall-clock delay between two events is their logical-timestamp gap divided by the
        CURRENT replay speed, clamped to ``config.replay_pacing_cap_seconds`` so a large quiet gap
        never stalls the cockpit. Pacing is delivery-only; the engine still computes purely from the
        logical timestamps, so the replay stays deterministic at ANY speed (a change of speed
        re-paces delivery but never the events, their order, or their logical timestamps — so the
        resulting features/state/confidence are byte-identical). Cancellable like the sim feeder.

        WARM-UP FAST-FORWARD (J-29): the first up-to-``warmup_min_events`` events are delivered with
        a tiny fixed pace (``config.warmup_fast_forward_pace_seconds``) instead of their logical
        gaps, so the cockpit reaches a WARM read quickly rather than waiting out the real timeline
        of the warm-up window; normal logical-gap pacing resumes once warmed. This changes ONLY the
        wall-clock sleep between deliveries — every event still enters the engine in the same order
        with its same logical timestamp, so the resulting features/state/confidence are IDENTICAL
        to an un-fast-forwarded replay (the engine never reads wall-clock; determinism preserved).
        """
        cap = self._config.replay_pacing_cap_seconds
        # Accept either the mutable speed cell (live re-pacing, J-32) or a bare float (fixed speed,
        # used by the unit tests / legacy callers). Normalise to a one-element cell so the loop reads
        # ``speed_cell[0]`` uniformly each iteration.
        speed_cell = speed if isinstance(speed, list) else [speed]
        warmup_count = self._config.warmup_min_events
        ff_pace = self._config.warmup_fast_forward_pace_seconds
        # Stream open, no event applied yet -> `waiting`; the first process_event promotes to
        # `live`. A finite historical window resolves to `live`-or-`closed` by exhaustion.
        engine.set_stream_status("waiting")
        try:
            await self._replay_events(engine, provider.stream(), speed_cell, start_delivered=0)
            # Natural exhaustion — reason ``stream_closed`` (a user Stop set ``watch_stopped`` first).
            engine.set_stream_status("closed", end_reason="stream_closed")
        except asyncio.CancelledError:
            engine.set_stream_status("closed")  # a clean stop/switch — NOT a failure
            raise
        except Exception:
            # A real replay-feeder failure: log it (naming the ticker) and surface `failed` — never
            # swallowed, never left frozen at cold-start, never a fabricated `live`.
            logger.exception("historical replay feeder for %s failed", engine.snapshot().ticker)
            engine.set_stream_status("failed")

    async def _replay_events(
        self, engine: TapeEngine, events, speed_cell: "list[float]", start_delivered: int
    ) -> int:
        """Pace one event iterable into the engine (the shared replay loop for paced + progressive).

        ``start_delivered`` is the count of events ALREADY delivered (so warm-up fast-forward spans
        the whole replay across chunk boundaries, not per chunk). Returns the new delivered count.
        Pacing is delivery-only — the engine math is purely logical, so the result is deterministic
        and identical whether the events come from one window or several stitched chunks."""
        cap = self._config.replay_pacing_cap_seconds
        warmup_count = self._config.warmup_min_events
        ff_pace = self._config.warmup_fast_forward_pace_seconds
        delivered = start_delivered
        prev_ts = engine.snapshot().timestamp if start_delivered else None
        for event in events:
            # Freeze in place while paused BEFORE consuming this event (no fabricated catch-up).
            await self._wait_while_paused(engine)
            if prev_ts is not None:
                if delivered < warmup_count:
                    delay = ff_pace  # warm-up fast-forward (delivery pacing only)
                else:
                    current_speed = speed_cell[0]
                    divisor = current_speed if current_speed > 0 else 1.0
                    delay = min((event.timestamp - prev_ts) / divisor, cap)
                if delay > 0:
                    await asyncio.sleep(delay)
            prev_ts = event.timestamp
            engine.process_event(event)
            delivered += 1
        return delivered

    async def _feed_progressive(
        self,
        engine: TapeEngine,
        first_chunk_provider: Provider,
        fetch_remaining,
        speed_cell: "list[float]",
    ) -> None:
        """Replay the first chunk, then stitch the background-fetched remaining chunks (J-37).

        The first chunk is already in hand (fetched within budget by the route), so replay begins
        immediately. The remaining sub-windows are fetched OFF the event loop (``asyncio.to_thread``)
        concurrently with that first-chunk replay, so a slow later chunk neither blocks the loop nor
        the already-running replay (time-to-first-data decoupled from total-window load). Once
        fetched, each remaining chunk is replayed in epoch order through a ``ProgressiveHistorical
        provider`` seeded with the SAME canonical epoch anchor, so the stitched stream is identical to
        a single-shot fetch of all records (determinism + single-source-of-truth preserved). The
        background fetch is started before the first-chunk replay so it overlaps; a fetch failure is
        surfaced as ``failed`` (never swallowed, never a fabricated ``live``)."""
        from .providers.historical import ProgressiveHistoricalProvider

        engine.set_stream_status("waiting")
        # Kick off the remaining-chunk fetch BEFORE replaying the first chunk so it overlaps.
        remaining_task = asyncio.create_task(asyncio.to_thread(fetch_remaining))
        try:
            delivered = await self._replay_events(
                engine, first_chunk_provider.stream(), speed_cell, start_delivered=0
            )
            remaining_chunks = await remaining_task
            if remaining_chunks:
                anchor = first_chunk_provider.epoch_anchor
                # Stitch the remaining chunks after the first using the SAME epoch anchor, so logical
                # timestamps stay monotonic and identical to a single-shot fetch of all records.
                rest = ProgressiveHistoricalProvider(
                    engine.snapshot().ticker, remaining_chunks, first_chunk_provider.scenario
                )
                rest.epoch_anchor = anchor  # pin to the first chunk's anchor (single timeline)
                rest._t0 = anchor
                await self._replay_events(
                    engine, rest.stream(), speed_cell, start_delivered=delivered
                )
            # Natural exhaustion — reason ``stream_closed`` (a user Stop set ``watch_stopped`` first).
            engine.set_stream_status("closed", end_reason="stream_closed")
        except asyncio.CancelledError:
            engine.set_stream_status("closed")
            raise
        except Exception:
            logger.exception(
                "progressive historical feeder for %s failed", engine.snapshot().ticker
            )
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
            # Natural exhaustion (the live stream ended on its own) — reason ``stream_closed``.
            engine.set_stream_status("closed", end_reason="stream_closed")
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
