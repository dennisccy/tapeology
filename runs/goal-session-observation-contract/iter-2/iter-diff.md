# Iteration diff (bounded)

Files changed: 2. Shown in full: 1.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_tape_observation_time.py` (238 lines not shown)

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
diff --git a/apps/backend/tests/test_tape_observation_time.py b/apps/backend/tests/test_tape_observation_time.py
new file mode 100644
index 00000000..4d22c4c5
--- /dev/null
+++ b/apps/backend/tests/test_tape_observation_time.py
@@ -0,0 +1,632 @@
+"""Observation Contract v1 -- Binding Execution Order step 2 (J-02; docs/goal.md).
+
+Covers the time law's MANAGER-side machinery added this iteration -- ``WatchManager``'s
+per-ticker atomic settled pair (``_settle`` / ``get_observation_source``) -- proven atomic under
+a deterministic interleaving harness, plus the already-implemented (iter-1)
+``app/observation_contract.py`` time projections (``_observed_at_utc`` / ``_availability`` / the
+pinned ISO function), proven honest against real sim, historical-fixture, dataset-replay and
+live-fixture data. TC references below match the iteration spec
+(``docs/phases/goal-observation-contract-iter-2.md``) and goal.md's J-02 Steps.2 list. Every
+guard/law test ships a named ``test_counterexample_*`` proving it can fail. No test needs a
+running uvicorn server or network access -- the route does not exist until iteration 5, and no
+test contacts Alpaca (only ``HistoricalProvider``/``LiveProvider`` over committed fixtures).
+
+TC-1..TC-4 (the atomic-read interleaving proof) use a deterministic SYNC harness:
+``WatchManager.watch()``/``watch_with_provider()`` called from a plain (non-async) test function
+finds no running event loop and leaves the engine COLD with no feeder task (its own documented
+"the caller feeds the engine itself" contract -- see ``test_watch_manager.py``'s
+``test_watch_with_provider_does_not_touch_sim_registry``). That gives full, race-free control
+over exactly when each event is processed and exactly when the settle helper fires -- the only
+way to construct "event N settled, event N+1 processed but not yet settled" deterministically
+(a real running feeder settles both back-to-back with no await point between them, so no outside
+coroutine could ever observe that interleaving). ``manager._settle(...)`` is called directly in
+those tests for the same reason.
+"""
+
+from __future__ import annotations
+
+import ast
+import asyncio
+import itertools
+from datetime import datetime, timezone
+from pathlib import Path
+
+import pytest
+
+from app import observation_contract, watch_manager
+from app.config import CONFIG
+from app.engine.snapshot import EngineSnapshot
+from app.engine.tape_engine import TapeEngine
+from app.observation_contract import build_tape_observation
+from app.providers.adapters.base import RawQuote, RawTrade
+from app.providers.historical import HistoricalProvider
+from app.providers.live import LiveProvider
+from app.providers.simulated import SimulatedProvider
+from app.research.datasets import DatasetStore
+from app.watch_manager import WatchManager
+from fakes import load_fixture_window
+
+PG_FIXTURE = Path(__file__).parent / "fixtures" / "alpaca" / "PG_20260609_170000_171000_sip.json"
+FIXTURE_DATASETS_J03_DIR = Path(__file__).parent / "fixtures" / "datasets_j03"
+DATASETS_J03_ID = "5232fa672b7b4077a5117d34b14c807d"
+
+
+# --- Small builders / helpers ---------------------------------------------------------------
+
+
+def _iso(epoch: float) -> str:
+    return (
+        datetime.fromtimestamp(epoch, tz=timezone.utc)
+        .isoformat(timespec="microseconds")
+        .replace("+00:00", "Z")
+    )
+
+
+def _parse_iso(value: str) -> float:
+    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
+
+
+def _make_snapshot(**overrides: object) -> EngineSnapshot:
+    defaults: dict = dict(
+        ticker="SIM-BIDABS",
+        scenario="bid_absorption",
+        timestamp=12.5,
+        event_count=3,
+        warm=False,
+        stream_status="live",
+        bid=100.0,
+        ask=100.02,
+        spread=0.02,
+        last=100.01,
+        features={"30s": {"aggressive_sell_ratio": 0.6}},
+        primary_window="30s",
+        tape_state="bid_absorption",
+        confidence=0.5,
+        observations=(),
+        paused=False,
+        epoch_anchor=CONFIG.sim_session_anchor_epoch,
+        delivery_lag_seconds=None,
+    )
+    defaults.update(overrides)
+    return EngineSnapshot(**defaults)
+
+
+def _valid_provenance() -> tuple[str, str | None, bool | None]:
+    return ("b" * 64, "abc123def456", False)
+
+
+def _build_for_snapshot(snapshot: EngineSnapshot, *, source_mode: str, data_feed: str, **overrides: object) -> dict:
+    kwargs: dict = dict(
+        snapshot=snapshot,
+        source_mode=source_mode,
+        data_feed=data_feed,
+        window_start_utc=None,
+        window_end_utc=None,
+        dataset_id=None,
+        dataset_checksum=None,
+        session_id="session-test-abc",
+        session_started_at_utc="2026-09-03T00:00:00.000000Z",
+        settled_at_utc=None,
+        end_reason=None,
+        generated_at_utc="2026-09-03T00:00:01.000000Z",
+        profile_id="default",
+        config=CONFIG,
+        provenance=_valid_provenance(),
+    )
+    kwargs.update(overrides)
+    return build_tape_observation(**kwargs)
+
+
+async def _aiter(records):
+    for r in records:
+        yield r
+
+
+async def _until(predicate, timeout: float = 3.0, step: float = 0.005) -> None:
+    elapsed = 0.0
+    while elapsed < timeout:
+        if predicate():
+            return
+        await asyncio.sleep(step)
+        elapsed += step
+    raise AssertionError("condition not met within timeout")
+
+
+# --- TC-1 / TC-2 / TC-3 / TC-4: the atomic-read interleaving proof (Constitution §2) ---------
+
+
+def test_get_observation_source_pairs_snapshot_with_its_own_settled_time(monkeypatch):
+    """TC-1: SIM-BIDABS watched with >=1 event processed -- get_observation_source returns the
+    settled EngineSnapshot paired with the settled_at_utc stamped by THAT SAME settle call,
+    under a deterministic interleaving harness with a monkeypatched watch_manager clock."""
+    clock = [1_700_000_000.0]
+    monkeypatch.setattr(watch_manager.time, "time", lambda: clock[0])
+    manager = WatchManager(CONFIG)
+    engine = manager.watch("SIM-BIDABS")  # sync context: cold engine, no feeder task
+    event = next(SimulatedProvider("SIM-BIDABS", "bid_absorption").stream())
+
+    engine.process_event(event)
+    manager._settle(engine, new_event=True)
+
+    result = manager.get_observation_source("SIM-BIDABS")
+    assert result is not None
+    snapshot, settled_at_utc, end_reason = result
+    assert snapshot.timestamp == event.timestamp
+    assert settled_at_utc == watch_manager._iso_utc(clock[0])
+    assert end_reason is None
+
+
+def test_atomic_read_never_mispairs_snapshot_n_plus_1_with_settled_time_n(monkeypatch):
+    """TC-2: event N settled, event N+1 process_event-applied but the settle helper has NOT yet
+    run for it -- the read still pairs snapshot N with settled-time N (never N+1 with N, nor the
+    reverse); after settling N+1 the pair becomes N+1 / settled-time-N+1."""
+    clock = [1_700_000_000.0]
+    monkeypatch.setattr(watch_manager.time, "time", lambda: clock[0])
+    manager = WatchManager(CONFIG)
+    engine = manager.watch("SIM-BIDABS")
+    stream = SimulatedProvider("SIM-BIDABS", "bid_absorption").stream()
+
+    event_n = next(stream)
+    engine.process_event(event_n)
+    manager._settle(engine, new_event=True)
+    snapshot_n, settled_n, _ = manager.get_observation_source("SIM-BIDABS")
+    assert snapshot_n.timestamp == event_n.timestamp
+
+    clock[0] += 5.0  # wall clock advances -- but N+1 has not been settled yet
+    event_n1 = next(stream)
+    engine.process_event(event_n1)  # the engine's OWN internal snapshot now reflects N+1
+
+    still_snapshot, still_settled, _ = manager.get_observation_source("SIM-BIDABS")
+    assert still_snapshot is snapshot_n  # STILL the exact N object, never a fresher N+1 read
+    assert still_settled == settled_n  # STILL settled-time N, never re-stamped early
+    assert engine.snapshot() is not still_snapshot  # the LIVE engine has already moved to N+1
+
+    manager._settle(engine, new_event=True)  # now settle N+1
+    snapshot_n1, settled_n1, _ = manager.get_observation_source("SIM-BIDABS")
+    assert snapshot_n1 is engine.snapshot()
+    assert snapshot_n1.timestamp == event_n1.timestamp
+    assert settled_n1 != settled_n
+
+
+def test_counterexample_naive_read_mispairs_snapshot_and_settled_time(monkeypatch):
+    """TC-3: constructing the NAIVE read ``(engine.snapshot(), <last recorded settled_at>)``
+    instead of the atomic helper mis-pairs snapshot N+1 with settled-time N -- the counter-example
+    proving the atomic read is required, not decorative."""
+    clock = [1_700_000_000.0]
+    monkeypatch.setattr(watch_manager.time, "time", lambda: clock[0])
+    manager = WatchManager(CONFIG)
+    engine = manager.watch("SIM-BIDABS")
+    stream = SimulatedProvider("SIM-BIDABS", "bid_absorption").stream()
+
+    event_n = next(stream)
+    engine.process_event(event_n)
+    manager._settle(engine, new_event=True)
+    settled_snapshot_n, settled_n, _ = manager.get_observation_source("SIM-BIDABS")
+
+    event_n1 = next(stream)
+    engine.process_event(event_n1)  # engine.snapshot() now reflects N+1; settle NOT yet called
+
+    # The NAIVE read a non-atomic implementation would construct: the engine's CURRENT live
+    # snapshot object, paired with the LAST recorded settled_at (settled_n, from N).
+    naive_snapshot, naive_settled_at = engine.snapshot(), settled_n
+
+    # Mis-pair, proven by object identity (robust even when N and N+1 share a logical
+    # timestamp, e.g. a quote immediately followed by a trade): the naive read's snapshot is NOT
+    # the same object ``settled_n`` was atomically recorded together with.
+    assert naive_snapshot is not settled_snapshot_n
+    with pytest.raises(AssertionError):
+        assert naive_snapshot is settled_snapshot_n
+
+    # The atomic manager read, in contrast, NEVER exhibits this: it always returns the exact
+    # settled snapshot object paired with its own settled_at -- never engine.snapshot()'s
+    # current, possibly-fresher object.
+    atomic_snapshot, atomic_settled_at, _ = manager.get_observation_source("SIM-BIDABS")
+    assert atomic_snapshot is settled_snapshot_n
+    assert atomic_settled_at == naive_settled_at
+    assert atomic_snapshot is not naive_snapshot  # the concrete mis-pair the naive tuple carries
+
+
+def test_pause_carries_forward_settled_time_unchanged(monkeypatch):
+    """TC-4: given a watch with one settled event, pause() then get_observation_source() shows
+    settled_at_utc identical to its pre-pause value (carried forward, never re-stamped to
+    "now") -- Constitution §2: "no new event, same availability"."""
+    clock = [1_700_000_000.0]
+    monkeypatch.setattr(watch_manager.time, "time", lambda: clock[0])
+    manager = WatchManager(CONFIG)
+    engine = manager.watch("SIM-BIDABS")
+    event = next(SimulatedProvider("SIM-BIDABS", "bid_absorption").stream())
+    engine.process_event(event)
+    manager._settle(engine, new_event=True)
+    pre_pause_snapshot, pre_pause_settled, _ = manager.get_observation_source("SIM-BIDABS")
+
+    clock[0] += 120.0  # wall clock advances well past the pause
+    assert manager.pause("SIM-BIDABS") is True
+    post_pause_snapshot, post_pause_settled, _ = manager.get_observation_source("SIM-BIDABS")
+    assert post_pause_settled == pre_pause_settled
+    assert post_pause_snapshot.tape_state == pre_pause_snapshot.tape_state
+
+
+def test_get_observation_source_on_an_unwatched_ticker_returns_none():
+    # Error case (TESTING REQUIREMENTS): mirrors get()/pause()/resume()'s "no fabricated engine"
+    # idiom -- never synthesizes a pair for a ticker that was never watched.
+    manager = WatchManager(CONFIG)
+    assert manager.get_observation_source("SIM-BIDABS") is None
+
+
+def test_get_observation_source_returns_none_after_stop():
+    manager = WatchManager(CONFIG)
+    manager.watch("SIM-BIDABS")
+    assert manager.get_observation_source("SIM-BIDABS") is not None
+    assert manager.stop("SIM-BIDABS") is True
+    assert manager.get_observation_source("SIM-BIDABS") is None
+
+
+def test_rewatch_before_first_settle_never_returns_a_prior_watchs_stale_pair(monkeypatch):
+    # Guards the cold-reset at each watch* constructor: a re-watched ticker must never read a
+    # PRIOR (now-stopped) watch's settled snapshot/settled_at_utc before its own first tick.
+    clock = [1_700_000_000.0]
+    monkeypatch.setattr(watch_manager.time, "time", lambda: clock[0])
+    manager = WatchManager(CONFIG)
+    first_engine = manager.watch("SIM-BIDABS")
+    event = next(SimulatedProvider("SIM-BIDABS", "bid_absorption").stream())
+    first_engine.process_event(event)
+    manager._settle(first_engine, new_event=True)
+    first_snapshot, first_settled, _ = manager.get_observation_source("SIM-BIDABS")
+    assert first_settled is not None
+
+    assert manager.stop("SIM-BIDABS") is True
+    clock[0] += 999.0
+    second_engine = manager.watch("SIM-BIDABS")  # a fresh, cold engine
+    assert second_engine is not first_engine
+
+    # BEFORE the fresh engine has processed any event, the settled pair must be a COLD read for
+    # THIS engine -- never the prior watch's stale settled snapshot/time.
+    second_snapshot, second_settled, _ = manager.get_observation_source("SIM-BIDABS")
+    assert second_snapshot is second_engine.snapshot()
+    assert second_snapshot is not first_snapshot
+    assert second_settled is None  # nothing has settled yet on the fresh engine
+
+
+# --- TC-5: observed_at_utc equals the latest processed event, across all four sources --------
+
+
+def test_observed_at_utc_equals_latest_event_for_sim_provider():
+    engine = TapeEngine(
+        "SIM-BIDABS", "bid_absorption", CONFIG, epoch_anchor=CONFIG.sim_session_anchor_epoch
+    )
+    for event in itertools.islice(SimulatedProvider("SIM-BIDABS", "bid_absorption").stream(), 5):
+        engine.process_event(event)
+    snapshot = engine.snapshot()
+    observation = _build_for_snapshot(snapshot, source_mode="sim", data_feed="sim")
+    assert observation["observed_at_utc"] == _iso(snapshot.epoch_anchor + snapshot.timestamp)
+
+
+def test_observed_at_utc_equals_latest_event_for_historical_provider():
+    window, _raw = load_fixture_window(PG_FIXTURE)
+    provider = HistoricalProvider("PG", window, "historical PG 2026-06-09T17:00:00Z-17:10:00Z")
+    engine = TapeEngine("PG", provider.scenario, CONFIG, epoch_anchor=provider.epoch_anchor)
+    for event in itertools.islice(provider.stream(), 50):
+        engine.process_event(event)
+    snapshot = engine.snapshot()
+    observation = _build_for_snapshot(snapshot, source_mode="historical", data_feed="sip")
+    assert observation["observed_at_utc"] == _iso(snapshot.epoch_anchor + snapshot.timestamp)
+
+
+def test_observed_at_utc_equals_latest_event_for_dataset_replay():
+    store = DatasetStore(FIXTURE_DATASETS_J03_DIR)
+    last_snapshot = None
+    for snapshot in store.replay(DATASETS_J03_ID, CONFIG):
+        last_snapshot = snapshot
+    assert last_snapshot is not None
+    observation = _build_for_snapshot(last_snapshot, source_mode="dataset_replay", data_feed="sip")
+    assert observation["observed_at_utc"] == _iso(
+        last_snapshot.epoch_anchor + last_snapshot.timestamp
+    )
+
+
+@pytest.mark.anyio
+async def test_observed_at_utc_equals_latest_event_for_live_provider():
+    window, _raw = load_fixture_window(PG_FIXTURE)
+    # Merge quotes+trades into arrival order the way a live socket delivers them (epoch order).
+    records = sorted(list(window.quotes) + list(window.trades), key=lambda r: r.epoch)
+    provider = LiveProvider("PG", _aiter(records[:50]), "live PG")
+    engine = TapeEngine("PG", provider.scenario, CONFIG)
+    async for event in provider.stream():
+        if engine.epoch_anchor is None and provider.epoch_anchor is not None:
+            engine.set_epoch_anchor(provider.epoch_anchor)
+        engine.process_event(event)
+    snapshot = engine.snapshot()
+    observation = _build_for_snapshot(
+        snapshot, source_mode="live", data_feed="iex", settled_at_utc="2026-09-03T00:00:02.000000Z"
+    )
+    assert observation["observed_at_utc"] == _iso(snapshot.epoch_anchor + snapshot.timestamp)
+
+
+# --- TC-6: both observed_at_utc null clauses --------------------------------------------------
+
+
+def test_observed_at_utc_null_when_epoch_anchor_is_none():
+    snapshot = _make_snapshot(epoch_anchor=None)
+    observation = _build_for_snapshot(snapshot, source_mode="sim", data_feed="sim")
+    assert observation["observed_at_utc"] is None
+
+
+def test_observed_at_utc_null_when_no_event_processed():
+    snapshot = _make_snapshot(bid=None, ask=None, last=None)
+    observation = _build_for_snapshot(snapshot, source_mode="sim", data_feed="sim")
+    assert observation["observed_at_utc"] is None
+
+
+# --- TC-7: historical / dataset_replay availability is always honestly unknown ---------------
+
+
+@pytest.mark.parametrize("source_mode", ["historical", "dataset_replay"])
+def test_historical_and_dataset_replay_availability_is_always_null_and_unknown(source_mode):
+    snapshot = _make_snapshot()
+    observation = _build_for_snapshot(
+        snapshot,
+        source_mode=source_mode,
+        data_feed="sip",
+        settled_at_utc="2026-09-03T00:00:05.000000Z",  # even if a settled_at_utc IS supplied
+    )
+    assert observation["available_at_utc"] is None
+    assert observation["availability_basis"] == "historical_arrival_unknown"
+
+
+@pytest.mark.parametrize("source_mode", ["historical", "dataset_replay"])
+def test_counterexample_copying_event_time_into_available_at_utc_is_caught(source_mode):
+    snapshot = _make_snapshot()
+    observation = _build_for_snapshot(snapshot, source_mode=source_mode, data_feed="sip")
+    # A wrong builder would copy observed_at_utc verbatim into available_at_utc; prove that
+    # assertion FAILS against the real (honest-null) builder output.
+    with pytest.raises(AssertionError):
+        assert observation["available_at_utc"] == observation["observed_at_utc"]
+
+
+# --- TC-8: live availability is MEASURED (== settled_at_utc), never derived ------------------
+
+
+@pytest.mark.anyio
+async def test_live_available_at_utc_equals_settled_at_utc_from_manager_clock(monkeypatch):
+    record_epoch = 1_800_000_000.0
+    fixed_now = record_epoch + 2.5  # a known, fixed, unclamped delivery lag of 2.5s
+    monkeypatch.setattr(watch_manager.time, "time", lambda: fixed_now)
+
... [diff_bound] apps/backend/tests/test_tape_observation_time.py: 238 more diff lines omitted — Read the file for full detail
```
