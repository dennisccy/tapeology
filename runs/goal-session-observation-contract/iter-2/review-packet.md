# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/apps/backend/app/watch_manager.py b/apps/backend/app/watch_manager.py
index 49ca840f..dd62cc76 100644
--- a/apps/backend/app/watch_manager.py
+++ b/apps/backend/app/watch_manager.py
@@ -14,9 +14,11 @@ import contextlib
 import logging
 import os
 import time
+from datetime import datetime, timezone
 from typing import Callable
 
 from .config import Config
+from .engine.snapshot import EngineSnapshot
 from .engine.tape_engine import TapeEngine
 from .providers.base import AsyncProvider, Provider
 from .providers.simulated import build_provider
@@ -61,6 +63,24 @@ def _paced_delivery_lag(scheduled_elapsed: float, replay_start_wall: float) -> f
     lag = actual_elapsed - scheduled_elapsed
     return lag if lag > 0.0 else 0.0
 
+
+def _iso_utc(epoch: float) -> str:
+    """The repository's pinned ISO instant format (Observation Contract v1 Constitution §2) --
+    matches ``observation_contract.py``'s own ``_iso_utc`` / ``research/bars.py``'s ``_iso_utc``
+    byte-for-byte: UTC, microseconds, a ``Z`` suffix, never a hand-formatted string. Duplicated
+    here (this module's own private helper) per this repository's established convention of each
+    module owning its own small ISO formatter rather than importing a private cross-module name
+    (``research/bars.py``, ``research/datasets.py``, ``research/pnl_ledger.py`` and roughly two
+    dozen ``_iso_utc_now`` siblings already do this) -- the format string itself is the single
+    source of truth, pinned by Constitution §2 and cross-checked against
+    ``observation_contract._iso_utc`` by ``tests/test_tape_observation_time.py``."""
+    return (
+        datetime.fromtimestamp(epoch, tz=timezone.utc)
+        .isoformat(timespec="microseconds")
+        .replace("+00:00", "Z")
+    )
+
+
 # Server-side logger for feeder lifecycle. A background-feeder failure MUST be LOGGED (a real,
 # inspectable line naming the ticker), never swallowed in the task — the no-mute-cockpit / no-
 # silent-dead-clicks anti-goal. The status flip to "failed" is what surfaces it to the UI.
@@ -106,6 +126,15 @@ class WatchManager:
         # same logical timestamps, so features/state/confidence are byte-identical at any speed
         # (determinism preserved). Cleared in ``stop()``.
         self._speeds: dict[str, list[float]] = {}
+        # Per-ticker ATOMIC settled pair (Observation Contract v1 Constitution §2, iter-2 IN
+        # SCOPE): ``{ticker: (EngineSnapshot, settled_at_epoch | None)}``. Written EXCLUSIVELY by
+        # ``_settle`` (after every processed event and every lifecycle-only status mutation) as a
+        # single dict-item assignment, so ``get_observation_source`` never observes a torn
+        # snapshot/settled-time pair -- the settled time always belongs to the EXACT snapshot
+        # stored alongside it. Reset to a cold ``(snapshot, None)`` pair at each fresh engine
+        # construction (below) so a re-watched ticker can never read a PRIOR watch's stale
+        # settled pair before its own first tick.
+        self._settled: dict[str, "tuple[EngineSnapshot, float | None]"] = {}
 
     def set_on_engine_created(
         self, hook: "Callable[[str, TapeEngine], None] | None"
@@ -142,6 +171,9 @@ class WatchManager:
             ticker, provider.scenario, self._config, epoch_anchor=_provider_anchor(provider)
         )
         self._engines[ticker] = engine
+        # Cold-reset the settled pair for THIS fresh engine (never a prior watch's stale pair --
+        # see the ``_settled`` docstring in ``__init__``). Nothing has settled yet.
+        self._settled[ticker] = (engine.snapshot(), None)
         # Attach research observers (if any) BEFORE the feeder starts so the monitor sees the first
         # event/status. Exception-isolated — a hook failure never breaks the watch.
         self._announce_engine(ticker, engine)
@@ -168,6 +200,7 @@ class WatchManager:
             ticker, provider.scenario, self._config, epoch_anchor=_provider_anchor(provider)
         )
         self._engines[ticker] = engine
+        self._settled[ticker] = (engine.snapshot(), None)  # cold-reset (see __init__ docstring)
         self._announce_engine(ticker, engine)  # attach research observers before the feeder starts
         # Register the per-ticker mutable speed cell BEFORE the feeder starts so ``set_speed`` (and
         # the feeder's per-iteration read) share the one holder. A non-positive speed is normalised
@@ -212,6 +245,7 @@ class WatchManager:
             epoch_anchor=_provider_anchor(first_chunk_provider),
         )
         self._engines[ticker] = engine
+        self._settled[ticker] = (engine.snapshot(), None)  # cold-reset (see __init__ docstring)
         self._announce_engine(ticker, engine)  # attach research observers before the feeder starts
         speed_cell = [speed if speed > 0 else 1.0]
         self._speeds[ticker] = speed_cell
@@ -241,6 +275,7 @@ class WatchManager:
             ticker, provider.scenario, self._config, epoch_anchor=_provider_anchor(provider)
         )
         self._engines[ticker] = engine
+        self._settled[ticker] = (engine.snapshot(), None)  # cold-reset (see __init__ docstring)
         self._announce_engine(ticker, engine)  # attach research observers before the feeder starts
         try:
             loop = asyncio.get_running_loop()
@@ -255,6 +290,62 @@ class WatchManager:
     def get(self, ticker: str) -> TapeEngine | None:
         return self._engines.get(ticker)
 
+    def get_observation_source(
+        self, ticker: str
+    ) -> "tuple[EngineSnapshot, str | None, str | None] | None":
+        """The ONE atomic managed-observation read (Observation Contract v1 Constitution §1/§2,
+        iter-2 IN SCOPE): returns ``(settled EngineSnapshot, pinned-ISO settled_at_utc-or-None,
+        end_reason)`` from the ONE manager-held settled pair for ``ticker``.
+
+        This NEVER calls ``engine.snapshot()`` (never re-snapshots the engine at read time) --
+        it returns exactly what ``_settle`` captured together in ONE dict-item write, so the
+        returned ``settled_at_utc`` always belongs to the exact snapshot returned alongside it
+        (the atomic-read invariant; proven by the interleaving tests in
+        ``tests/test_tape_observation_time.py``). Returns ``None`` for a ticker not currently
+        watched -- mirrors ``get()``/``pause()``/``resume()``'s "no fabricated engine" idiom;
+        never synthesizes a pair.
+
+        ``end_reason`` is read from the live ``TapeEngine`` object, not stored in the pair
+        itself: it changes ONLY on a terminal ``closed``/``failed`` flip, and every such flip
+        already calls ``_settle`` in the very same statement sequence (see each feeder's
+        except/finally block below), so it is always in lockstep with the returned snapshot.
+        """
+        engine = self._engines.get(ticker)
+        if engine is None:
+            return None
+        snapshot, settled_at_epoch = self._settled[ticker]
+        settled_at_utc = _iso_utc(settled_at_epoch) if settled_at_epoch is not None else None
+        return snapshot, settled_at_utc, engine.end_reason
+
+    def _settle(self, engine: TapeEngine, *, new_event: bool) -> None:
+        """The ONE helper that writes the manager-held atomic settled pair (Constitution §2,
+        iter-2 IN SCOPE) -- the ONLY place ``self._settled[...]`` is mutated after a ticker's
+        cold-start reset (the four ``watch*`` constructors above). Keyed off the engine's own
+        ticker (``engine.snapshot().ticker``) so every feeder path can call this without
+        threading a separate ``ticker`` parameter through its call chain.
+
+        ``new_event=True`` -- called immediately after ``process_event`` (and any same-tick
+        ``set_delivery_lag``) in every feeder path -- stamps the wall clock NOW as the
+        newly-settled instant, paired with the snapshot this SAME tick just built. This single
+        dict-item assignment is what makes the pair atomic: a reader can never observe a NEWER
+        snapshot paired with an OLDER (or a not-yet-updated) settled time, or vice-versa.
+
+        ``new_event=False`` -- called after every lifecycle-only status mutation that carries NO
+        new event (the ``waiting``/``stale``/``closed``/``failed`` flips inside each feeder, and
+        ``pause()``/``resume()`` below) -- carries the PREVIOUS ``settled_at_epoch`` FORWARD
+        UNCHANGED (Constitution §2: "no new event, same availability"); it never re-stamps to
+        "now". Stays ``None`` until the first-ever settle (an honest "nothing settled yet"),
+        exactly the pre-existing "no fabricated engine" idiom extended to "no fabricated
+        settlement".
+        """
+        ticker = engine.snapshot().ticker
+        if new_event:
+            settled_at_epoch = time.time()
+        else:
+            prior = self._settled.get(ticker)
+            settled_at_epoch = prior[1] if prior is not None else None
+        self._settled[ticker] = (engine.snapshot(), settled_at_epoch)
+
     def stop(self, ticker: str) -> bool:
         """Stop watching ``ticker``: cancel its feeder, mark the engine closed, and remove it.
 
@@ -308,6 +399,9 @@ class WatchManager:
         if engine is None:
             return False
         engine.pause()
+        # Lifecycle-only mutation, no new event: carries the previous settled_at_epoch forward
+        # unchanged (Constitution §2, iter-2 IN SCOPE / TC-4).
+        self._settle(engine, new_event=False)
         return True
 
     def resume(self, ticker: str) -> bool:
@@ -321,6 +415,9 @@ class WatchManager:
         if engine is None:
             return False
         engine.resume()
+        # Lifecycle-only mutation, no new event: carries the previous settled_at_epoch forward
+        # unchanged (Constitution §2, iter-2 IN SCOPE).
+        self._settle(engine, new_event=False)
         return True
 
     async def _wait_while_paused(self, engine: TapeEngine) -> None:
@@ -340,6 +437,7 @@ class WatchManager:
         # first process_event promotes it to `live`. A finite sim stream then resolves to
         # `live`-or-`closed` by exhaustion, so no extra timer is needed here.
         engine.set_stream_status("waiting")
+        self._settle(engine, new_event=False)  # lifecycle-only: no event settled yet
         # Paced-delivery lag (Data Contract row 14, J-63): track the feeder's processing backlog
         # against its OWN fixed-pace schedule. ``scheduled`` accumulates the intended per-event pace;
         # the lag is how far actual wall-clock has fallen behind it. A healthy sim keeps up => ≈0.
@@ -352,14 +450,19 @@ class WatchManager:
                 # Stamp the lag AFTER processing so it reflects the just-applied event's backlog
                 # (feeder-owned; never read by classification — determinism unchanged).
                 engine.set_delivery_lag(_paced_delivery_lag(scheduled, replay_start))
+                # Atomic settle (Observation Contract v1 iter-2 IN SCOPE): the settled pair for
+                # THIS tick, written in the SAME statement that just finished building it.
+                self._settle(engine, new_event=True)
                 await asyncio.sleep(self._pace)
                 scheduled += self._pace
             # Natural exhaustion (the stream ran out) — reason ``stream_closed`` (distinct from a
             # user Stop, which set ``watch_stopped`` before cancelling this task). J-50's stream-end
             # leg depends on this reason.
             engine.set_stream_status("closed", end_reason="stream_closed")
+            self._settle(engine, new_event=False)  # lifecycle-only: no new event
         except asyncio.CancelledError:
             engine.set_stream_status("closed")  # a clean stop/switch — NOT a failure
+            self._settle(engine, new_event=False)
             raise
         except Exception:
             # A real feeder failure: log it server-side (naming the ticker) and surface it as
@@ -367,6 +470,7 @@ class WatchManager:
             # Never swallowed; the engine is left at `failed`, never a fabricated `live`.
             logger.exception("paced/sim feeder for %s failed", engine.snapshot().ticker)
             engine.set_stream_status("failed")
+            self._settle(engine, new_event=False)
 
     async def _feed_paced(
         self, engine: TapeEngine, provider: Provider, speed: "float | list[float]"
@@ -404,6 +508,7 @@ class WatchManager:
         # Stream open, no event applied yet -> `waiting`; the first process_event promotes to
         # `live`. A finite historical window resolves to `live`-or-`closed` by exhaustion.
         engine.set_stream_status("waiting")
+        self._settle(engine, new_event=False)  # lifecycle-only: no event settled yet
         # Row-14 paced-delivery-lag schedule (J-63): the feeder's start instant + a mutable cumulative
         # pacing-delay cell, threaded through ``_replay_events`` so the lag tracks the processing
         # backlog against the feeder's own schedule (a healthy replay keeps up => ≈0).
@@ -420,14 +525,17 @@ class WatchManager:
             )
             # Natural exhaustion — reason ``stream_closed`` (a user Stop set ``watch_stopped`` first).
             engine.set_stream_status("closed", end_reason="stream_closed")
+            self._settle(engine, new_event=False)  # lifecycle-only: no new event
         except asyncio.CancelledError:
             engine.set_stream_status("closed")  # a clean stop/switch — NOT a failure
+            self._settle(engine, new_event=False)
             raise
         except Exception:
             # A real replay-feeder failure: log it (naming the ticker) and surface `failed` — never
             # swallowed, never left frozen at cold-start, never a fabricated `live`.
             logger.exception("historical replay feeder for %s failed", engine.snapshot().ticker)
             engine.set_stream_status("failed")
+            self._settle(engine, new_event=False)
 
     async def _replay_events(
         self,
@@ -477,6 +585,10 @@ class WatchManager:
             # Stamp the paced-delivery lag AFTER processing (feeder-owned; never classification).
             if replay_start is not None and schedule is not None:
                 engine.set_delivery_lag(_paced_delivery_lag(schedule[0], replay_start))
+            # Atomic settle (Observation Contract v1 iter-2 IN SCOPE): every process_event in
+            # this shared replay loop (used by both `_feed_paced` and `_feed_progressive`) settles
+            # unconditionally, regardless of whether a lag was stamped this tick.
+            self._settle(engine, new_event=True)
             delivered += 1
         return delivered
 
@@ -501,6 +613,7 @@ class WatchManager:
         from .providers.historical import ProgressiveHistoricalProvider
 
         engine.set_stream_status("waiting")
+        self._settle(engine, new_event=False)  # lifecycle-only: no event settled yet
         # Kick off the remaining-chunk fetch BEFORE replaying the first chunk so it overlaps.
         remaining_task = asyncio.create_task(asyncio.to_thread(fetch_remaining))
         # Row-14 paced-delivery-lag schedule (J-63): ONE continuous start + cumulative-delay cell so
@@ -536,14 +649,17 @@ class WatchManager:
                 )
             # Natural exhaustion — reason ``stream_closed`` (a user Stop set ``watch_stopped`` first).
             engine.set_stream_status("closed", end_reason="stream_closed")
+            self._settle(engine, new_event=False)  # lifecycle-only: no new event
         except asyncio.CancelledError:
             engine.set_stream_status("closed")
+            self._settle(engine, new_event=False)
             raise
         except Exception:
             logger.exception(
                 "progressive historical feeder for %s failed", engine.snapshot().ticker
             )
             engine.set_stream_status("failed")
+            self._settle(engine, new_event=False)
 
     async def _feed_live(self, engine: TapeEngine, provider: AsyncProvider) -> None:
         """Feed an async (live) provider into the engine with a stale watchdog (J-12 / J-15).
@@ -596,6 +712,7 @@ class WatchManager:
         # The first event promotes it to `live`; the stale watchdog below bounds it to `stale` if no
         # event ever arrives (off-hours / quiet feed), so it never sits on `waiting` forever.
         engine.set_stream_status("waiting")
+        self._settle(engine, new_event=False)  # lifecycle-only: no event settled yet
         try:
             while True:
                 # Honest pause for LIVE: the puller keeps draining the socket (socket stays OPEN,
@@ -626,6 +743,7 @@ class WatchManager:
                     # Honest stale — bounds BOTH a `waiting` (no first event ever, off-hours/quiet
                     # feed) and a `live` gap; fabricates no trade. Never sits on `waiting` forever.
                     engine.set_stream_status("stale")
+                    self._settle(engine, new_event=False)  # lifecycle-only: no new event
                     continue
                 if event is done:
                     break
@@ -653,10 +771,15 @@ class WatchManager:
                 # stamped AFTER processing so it reflects the just-applied event (feeder-owned; never
                 # read by classification). A dense tape that outruns processing reads a growing lag.
                 engine.set_delivery_lag(_live_delivery_lag(engine))
+                # Atomic settle (Observation Contract v1 iter-2 IN SCOPE): the settled pair for
+                # THIS tick, written in the SAME statement that just finished building it.
+                self._settle(engine, new_event=True)
             # Natural exhaustion (the live stream ended on its own) — reason ``stream_closed``.
             engine.set_stream_status("closed", end_reason="stream_closed")
+            self._settle(engine, new_event=False)  # lifecycle-only: no new event
         except asyncio.CancelledError:
             engine.set_stream_status("closed")  # a clean stop/switch — NOT a failure
+            self._settle(engine, new_event=False)
             raise
         except Exception:
             # A real live-feeder failure (the provider raised, or the loop body failed): log it
@@ -665,6 +788,7 @@ class WatchManager:
             # down via the bounded `aclose()` path (no synchronous unsubscribe in this branch).
             logger.exception("live feeder for %s failed", engine.snapshot().ticker)
             engine.set_stream_status("failed")
+            self._settle(engine, new_event=False)
         finally:
             puller.cancel()
             with contextlib.suppress(asyncio.CancelledError):
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-observation-contract/telemetry.jsonl   | 6 ++++++
 runs/goal-session-observation-contract/trace/trace.jsonl | 1 +
 2 files changed, 7 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
