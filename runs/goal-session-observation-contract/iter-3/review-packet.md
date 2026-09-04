# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 4.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_tape_observation_lifecycle_feed.py` (281 lines not shown)

```diff
diff --git a/apps/backend/app/main.py b/apps/backend/app/main.py
index 68f2650d..4082e32b 100644
--- a/apps/backend/app/main.py
+++ b/apps/backend/app/main.py
@@ -263,6 +263,16 @@ def _parse_window_dt(value: str) -> datetime:
     return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
 
 
+def _iso_utc(dt: datetime) -> str:
+    """The repository's pinned ISO instant format (Observation Contract v1 Constitution §2),
+    matching ``watch_manager._iso_utc`` / ``observation_contract._iso_utc`` byte-for-byte -- this
+    module's own small formatter per the established per-module convention (each module owns its
+    own tiny ISO formatter rather than importing a private cross-module name). Used ONLY to thread
+    the already-parsed real historical request window into the manager's source descriptor
+    (iter-3 IN SCOPE) -- no other route behavior changes."""
+    return dt.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
+
+
 @app.get("/health")
 def health() -> dict:
     return {"status": "ok"}
@@ -391,7 +401,13 @@ async def _watch_historical(
                 timeout=CONFIG.vendor_call_timeout_seconds,
             )
             provider = HistoricalProvider(ticker, window, scenario)
-            engine = manager.watch_with_provider(ticker, provider, speed)
+            engine = manager.watch_with_provider(
+                ticker,
+                provider,
+                speed,
+                window_start_utc=_iso_utc(start),
+                window_end_utc=_iso_utc(end),
+            )
         else:
             # Long window: fetch ONLY the first chunk under the budget (decoupled first-data), then
             # background-fetch the rest. The first chunk is fetched via the same lazy generator the
@@ -411,7 +427,12 @@ async def _watch_historical(
                 ]
 
             engine = manager.watch_with_progressive_historical(
-                ticker, first_provider, _fetch_remaining, speed
+                ticker,
+                first_provider,
+                _fetch_remaining,
+                speed,
+                window_start_utc=_iso_utc(start),
+                window_end_utc=_iso_utc(end),
             )
     except (asyncio.TimeoutError, VendorTimeout):
         # Only the FIRST chunk's load is gated here; a genuinely un-loadable first chunk -> the
diff --git a/apps/backend/app/watch_manager.py b/apps/backend/app/watch_manager.py
index dd62cc76..7e4f8417 100644
--- a/apps/backend/app/watch_manager.py
+++ b/apps/backend/app/watch_manager.py
@@ -11,17 +11,20 @@ from __future__ import annotations
 
 import asyncio
 import contextlib
+import dataclasses
 import logging
 import os
 import time
+import uuid
 from datetime import datetime, timezone
 from typing import Callable
 
-from .config import Config
+from .config import Config, PROFILE_DEFAULT
 from .engine.snapshot import EngineSnapshot
 from .engine.tape_engine import TapeEngine
 from .providers.base import AsyncProvider, Provider
 from .providers.simulated import build_provider
+from .research.feed_basis import data_feed_for_scenario
 
 # Wall-clock seconds between delivered events in live mode (delivery pacing only).
 FEED_PACE_SECONDS = float(os.environ.get("TAPEOLOGY_FEED_PACE", "0.04"))
@@ -102,6 +105,33 @@ def _provider_anchor(provider: object) -> float | None:
     return getattr(provider, "epoch_anchor", None)
 
 
+@dataclasses.dataclass(frozen=True)
+class SourceDescriptor:
+    """The manager-recorded per-watch source/session descriptor (Observation Contract v1
+    Constitution §1/§3, iter-3 IN SCOPE) -- every caller-resolved parameter
+    ``build_tape_observation`` (iteration 1) already accepts, now genuinely populated at watch
+    creation instead of a placeholder the (still-unbuilt) route would have to invent. Recorded
+    ONCE per ``watch*`` constructor call using the SAME "cold reset for a fresh engine" pattern
+    already used for ``WatchManager._settled`` (see its ``__init__`` docstring) -- a re-watched
+    ticker never reads a PRIOR watch's stale descriptor. Read verbatim by
+    ``get_observation_source`` -- never re-derived, never re-parsed from the scenario string a
+    second time (Constitution §3: "never re-derived by a second scenario-prefix parser").
+
+    ``source.scenario`` is NOT a field here -- its single owner stays ``EngineSnapshot.scenario``
+    (Constitution §1), never a second, possibly-divergent copy.
+    """
+
+    source_mode: str
+    data_feed: str
+    window_start_utc: "str | None"
+    window_end_utc: "str | None"
+    dataset_id: "str | None"
+    dataset_checksum: "str | None"
+    session_id: str
+    session_started_at_utc: str
+    profile_id: str
+
+
 class WatchManager:
     def __init__(
         self,
@@ -135,6 +165,12 @@ class WatchManager:
         # construction (below) so a re-watched ticker can never read a PRIOR watch's stale
         # settled pair before its own first tick.
         self._settled: dict[str, "tuple[EngineSnapshot, float | None]"] = {}
+        # Per-ticker source/session descriptor (Observation Contract v1 Constitution §1/§3,
+        # iter-3 IN SCOPE): ``{ticker: SourceDescriptor}``. Recorded ONCE at each fresh engine
+        # construction (below), the SAME cold-reset-per-fresh-engine pattern as ``_settled`` --
+        # a re-watched ticker never reads a PRIOR watch's stale descriptor. Read verbatim by
+        # ``get_observation_source`` (no re-fetch, no second read).
+        self._sources: dict[str, SourceDescriptor] = {}
 
     def set_on_engine_created(
         self, hook: "Callable[[str, TapeEngine], None] | None"
@@ -155,6 +191,35 @@ class WatchManager:
         except Exception:
             logger.exception("on_engine_created hook failed for %s", ticker)
 
+    def _record_source(
+        self,
+        ticker: str,
+        *,
+        source_mode: str,
+        scenario: str,
+        window_start_utc: "str | None" = None,
+        window_end_utc: "str | None" = None,
+    ) -> None:
+        """Record THIS fresh engine's source/session descriptor (Constitution §1/§3, iter-3 IN
+        SCOPE) -- called once per ``watch*`` constructor, right alongside the ``_settled``
+        cold-reset above it. Mints a fresh ``session_id``/``session_started_at_utc`` (no existing
+        per-watch identifier to reuse, confirmed by direct inspection) and resolves ``data_feed``
+        via the ONE existing ``data_feed_for_scenario`` -- never a second scenario-prefix parser.
+        ``dataset_id``/``dataset_checksum`` are always ``None`` here: ``dataset_replay`` is a
+        distinct in-process caller outside the manager (Constitution §3), never a managed watch.
+        """
+        self._sources[ticker] = SourceDescriptor(
+            source_mode=source_mode,
+            data_feed=data_feed_for_scenario(scenario, self._config),
+            window_start_utc=window_start_utc,
+            window_end_utc=window_end_utc,
+            dataset_id=None,
+            dataset_checksum=None,
+            session_id=uuid.uuid4().hex,
+            session_started_at_utc=_iso_utc(time.time()),
+            profile_id=PROFILE_DEFAULT,
+        )
+
     def is_known(self, ticker: str) -> bool:
         return build_provider(ticker) is not None
 
@@ -174,6 +239,7 @@ class WatchManager:
         # Cold-reset the settled pair for THIS fresh engine (never a prior watch's stale pair --
         # see the ``_settled`` docstring in ``__init__``). Nothing has settled yet.
         self._settled[ticker] = (engine.snapshot(), None)
+        self._record_source(ticker, source_mode="sim", scenario=provider.scenario)
         # Attach research observers (if any) BEFORE the feeder starts so the monitor sees the first
         # event/status. Exception-isolated — a hook failure never breaks the watch.
         self._announce_engine(ticker, engine)
@@ -186,7 +252,13 @@ class WatchManager:
         return engine
 
     def watch_with_provider(
-        self, ticker: str, provider: Provider, speed: float = 1.0
+        self,
+        ticker: str,
+        provider: Provider,
+        speed: float = 1.0,
+        *,
+        window_start_utc: "str | None" = None,
+        window_end_utc: "str | None" = None,
     ) -> TapeEngine:
         """Watch ``ticker`` fed by an arbitrary ``Provider`` (e.g. the historical replay),
         WITHOUT touching the simulated registry.
@@ -194,6 +266,12 @@ class WatchManager:
         Any existing watch for the ticker is torn down first (a switch/re-watch cancels the
         prior feeder and starts a fresh, cold engine — the orphaned-watch lesson). The replay
         feeder is registered in ``self._tasks`` so ``stop()`` and a switch already cancel it.
+
+        ``window_start_utc`` / ``window_end_utc`` (iter-3 IN SCOPE, optional, pinned-ISO) are the
+        caller's already-parsed real request window -- recorded verbatim into the source
+        descriptor (Constitution §3: "request identity, distinct from the observed extent");
+        ``None`` (the default) preserves the exact prior signature/behavior for every existing
+        caller that does not pass them.
         """
         self.stop(ticker)  # tear down any prior watch for this ticker (no orphaned feeder)
         engine = TapeEngine(
@@ -201,6 +279,13 @@ class WatchManager:
         )
         self._engines[ticker] = engine
         self._settled[ticker] = (engine.snapshot(), None)  # cold-reset (see __init__ docstring)
+        self._record_source(
+            ticker,
+            source_mode="historical",
+            scenario=provider.scenario,
+            window_start_utc=window_start_utc,
+            window_end_utc=window_end_utc,
+        )
         self._announce_engine(ticker, engine)  # attach research observers before the feeder starts
         # Register the per-ticker mutable speed cell BEFORE the feeder starts so ``set_speed`` (and
         # the feeder's per-iteration read) share the one holder. A non-positive speed is normalised
@@ -223,6 +308,9 @@ class WatchManager:
         first_chunk_provider: Provider,
         fetch_remaining,
         speed: float = 1.0,
+        *,
+        window_start_utc: "str | None" = None,
+        window_end_utc: "str | None" = None,
     ) -> TapeEngine:
         """Watch a LONG historical window progressively (J-37): replay the FIRST chunk immediately
         while the REMAINING chunks are fetched in the background and appended in epoch order.
@@ -236,6 +324,10 @@ class WatchManager:
         single-source-of-truth preserved (the engine bins on its logical timeline regardless of chunk
         boundaries). Any existing watch is torn down first (orphaned-watch lesson); the feeder is
         registered so stop()/switch/shutdown cancel it.
+
+        ``window_start_utc`` / ``window_end_utc`` (iter-3 IN SCOPE, optional, pinned-ISO): see
+        ``watch_with_provider``'s docstring -- the SAME whole-request window, shared by every
+        stitched chunk (Constitution §3).
         """
         self.stop(ticker)
         engine = TapeEngine(
@@ -246,6 +338,13 @@ class WatchManager:
         )
         self._engines[ticker] = engine
         self._settled[ticker] = (engine.snapshot(), None)  # cold-reset (see __init__ docstring)
+        self._record_source(
+            ticker,
+            source_mode="historical",
+            scenario=first_chunk_provider.scenario,
+            window_start_utc=window_start_utc,
+            window_end_utc=window_end_utc,
+        )
         self._announce_engine(ticker, engine)  # attach research observers before the feeder starts
         speed_cell = [speed if speed > 0 else 1.0]
         self._speeds[ticker] = speed_cell
@@ -276,6 +375,7 @@ class WatchManager:
         )
         self._engines[ticker] = engine
         self._settled[ticker] = (engine.snapshot(), None)  # cold-reset (see __init__ docstring)
+        self._record_source(ticker, source_mode="live", scenario=provider.scenario)
         self._announce_engine(ticker, engine)  # attach research observers before the feeder starts
         try:
             loop = asyncio.get_running_loop()
@@ -292,10 +392,12 @@ class WatchManager:
 
     def get_observation_source(
         self, ticker: str
-    ) -> "tuple[EngineSnapshot, str | None, str | None] | None":
-        """The ONE atomic managed-observation read (Observation Contract v1 Constitution §1/§2,
-        iter-2 IN SCOPE): returns ``(settled EngineSnapshot, pinned-ISO settled_at_utc-or-None,
-        end_reason)`` from the ONE manager-held settled pair for ``ticker``.
+    ) -> "tuple[EngineSnapshot, str | None, str | None, SourceDescriptor] | None":
+        """The ONE atomic managed-observation read (Observation Contract v1 Constitution §1/§2/§3,
+        iter-2/iter-3 IN SCOPE): returns ``(settled EngineSnapshot, pinned-ISO
+        settled_at_utc-or-None, end_reason, SourceDescriptor)`` -- the settled pair PLUS the
+        source/session descriptor recorded once at watch creation, both read from the SAME
+        per-ticker state (no re-fetch, no second read of the settled pair, iter-3 IN SCOPE).
 
         This NEVER calls ``engine.snapshot()`` (never re-snapshots the engine at read time) --
         it returns exactly what ``_settle`` captured together in ONE dict-item write, so the
@@ -315,7 +417,7 @@ class WatchManager:
             return None
         snapshot, settled_at_epoch = self._settled[ticker]
         settled_at_utc = _iso_utc(settled_at_epoch) if settled_at_epoch is not None else None
-        return snapshot, settled_at_utc, engine.end_reason
+        return snapshot, settled_at_utc, engine.end_reason, self._sources[ticker]
 
     def _settle(self, engine: TapeEngine, *, new_event: bool) -> None:
         """The ONE helper that writes the manager-held atomic settled pair (Constitution §2,
@@ -337,8 +439,20 @@ class WatchManager:
         "now". Stays ``None`` until the first-ever settle (an honest "nothing settled yet"),
         exactly the pre-existing "no fabricated engine" idiom extended to "no fabricated
         settlement".
+
+        IDENTITY CHECK (iter-3 IN SCOPE, the reviewer's carried-forward MINOR): a stale/superseded
+        engine's write is a silent no-op, never an exception, never a state mutation. Every
+        feeder's ``except asyncio.CancelledError`` branch calls this on the OLD engine object,
+        and that branch only actually runs when the cancelled task next reaches an await point --
+        which can happen AFTER a switch/re-watch has already cold-reset ``self._settled[ticker]``
+        (and ``self._sources[ticker]``) for a FRESH engine. Without this check the late write would
+        silently clobber the new watch's settled pair with the old engine's stale snapshot (proven
+        reproducible by ``tests/test_tape_observation_lifecycle_feed.py``'s
+        ``test_counterexample_*`` that reverts this check).
         """
         ticker = engine.snapshot().ticker
+        if self._engines.get(ticker) is not engine:
+            return  # stale/superseded engine (already stopped, or replaced by a switch) -- no-op
         if new_event:
             settled_at_epoch = time.time()
         else:
diff --git a/apps/backend/tests/test_tape_observation_lifecycle_feed.py b/apps/backend/tests/test_tape_observation_lifecycle_feed.py
new file mode 100644
index 00000000..30eb6fa5
--- /dev/null
+++ b/apps/backend/tests/test_tape_observation_lifecycle_feed.py
@@ -0,0 +1,675 @@
+"""Observation Contract v1 -- Binding Execution Order step 3 (J-03; docs/goal.md).
+
+Covers this iteration's MANAGER-side machinery: the per-watch source/session descriptor
+(``WatchManager._record_source`` / ``SourceDescriptor``, recorded once at each ``watch*``
+constructor and returned alongside the atomic settled pair by ``get_observation_source``), the
+``_settle`` identity-check fix (the reviewer's carried-forward MINOR -- a stale/superseded
+engine's late write must never clobber a fresher watch's settled pair), and the honesty of the
+seven ``lifecycle.stream_status`` values plus the three feed bases. TC references below match
+the iteration spec (``docs/phases/goal-observation-contract-iter-3.md``) and goal.md's J-03
+Steps.6 list. Every guard/law test ships a named ``test_counterexample_*`` proving it can fail.
+No test needs a running uvicorn server or network access -- the route does not exist until
+iteration 5, and no test contacts Alpaca (only ``HistoricalProvider``/``LiveProvider``/
+``FakeAdapter`` over committed fixtures and monkeypatched/fake harnesses).
+"""
+
+from __future__ import annotations
+
+import ast
+import asyncio
+import json
+import time
+from pathlib import Path
+
+import pytest
+
+from app import main as main_module
+from app import watch_manager
+from app.config import CONFIG
+from app.observation_contract import build_tape_observation, resolve_implementation_provenance
+from app.providers.adapters.base import HistoricalWindow, RawQuote, RawTrade
+from app.providers.base import QuoteEvent, Side, TradeEvent
+from app.providers.historical import HistoricalProvider
+from app.providers.simulated import SimulatedProvider
+from app.research.datasets import DatasetStore
+from app.research.feed_basis import data_feed_for_scenario
+from app.watch_manager import SourceDescriptor, WatchManager
+from fakes import FakeAdapter, FakeLiveProvider
+
+import dataclasses
+
+FIXTURE_DATASETS_J03_DIR = Path(__file__).parent / "fixtures" / "datasets_j03"
+
+# A small stale-gap so the live "waiting"->"stale" watchdog fires in milliseconds (mirrors
+# test_stream_lifecycle.py / test_watch_manager.py's own FAST_STALE).
+FAST_STALE = dataclasses.replace(CONFIG, stale_gap_seconds=0.05)
+
+ACTIONABILITY_TOKENS = ("READY", "NO_TRADE", "NO_VERDICT", "trade_allowed", "PENDING_CONDITION")
+
+
+# --- Small helpers (self-contained -- no cross-import of another test module's private doubles) --
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
+def _seed_live(provider: FakeLiveProvider) -> None:
+    provider.feed_nowait(QuoteEvent(provider.ticker, 0.0, 100.0, 100.02, 100, 100))
+    provider.feed_nowait(TradeEvent(provider.ticker, 0.0, 100.02, 100, Side.UNKNOWN))
+
+
+def _hist_provider(ticker: str = "F", n: int = 300) -> HistoricalProvider:
+    # Dense, small-gap synthetic window so the paced feeder flips to "live"/exhausts quickly.
+    quotes = tuple(RawQuote(i * 0.001, 16.0, 16.01, 100, 100) for i in range(n))
+    trades = tuple(RawTrade(i * 0.001 + 0.0005, 16.0, 100) for i in range(n))
+    window = HistoricalWindow(ticker, trades, quotes)
+    return HistoricalProvider(ticker, window, f"historical {ticker} test-window")
+
+
+class _RaisingProvider:
+    """A sync ``Provider`` whose stream RAISES after yielding ``before`` events."""
+
+    def __init__(self, before: int = 0, ticker: str = "FAILT") -> None:
+        self.ticker = ticker
+        self.scenario = f"historical {ticker} test-window"
+
+    def stream(self):
+        if False:
+            yield  # never yields -- an immediate-raise double is all TC-7/TC-8's `failed` case needs
+        raise RuntimeError("simulated paced-feeder failure")
+
+
+def _build_observation_from_source(
+    snapshot, settled_at_utc, end_reason, descriptor: SourceDescriptor, *, generated_at_utc: str
+) -> dict:
+    """Bridges this iteration's manager output into the already-existing (iteration 1) pure
+    builder -- proves the descriptor is genuinely usable by ``build_tape_observation``, not just
+    shaped like its parameters."""
+    return build_tape_observation(
+        snapshot=snapshot,
+        source_mode=descriptor.source_mode,
+        data_feed=descriptor.data_feed,
+        window_start_utc=descriptor.window_start_utc,
+        window_end_utc=descriptor.window_end_utc,
+        dataset_id=descriptor.dataset_id,
+        dataset_checksum=descriptor.dataset_checksum,
+        session_id=descriptor.session_id,
+        session_started_at_utc=descriptor.session_started_at_utc,
+        settled_at_utc=settled_at_utc,
+        end_reason=end_reason,
+        generated_at_utc=generated_at_utc,
+        profile_id=descriptor.profile_id,
+        config=CONFIG,
+        provenance=resolve_implementation_provenance(),
+    )
+
+
+def _scan_for_actionability_tokens(obj: object) -> list[str]:
+    text = json.dumps(obj, sort_keys=True).lower()
+    return [token for token in ACTIONABILITY_TOKENS if token.lower() in text]
+
+
+# === TC-1: fresh sim watch descriptor =========================================================
+
+
+def test_fresh_sim_watch_descriptor_shows_honest_defaults():
+    manager = WatchManager(CONFIG)
+    manager.watch("SIM-BIDABS")  # sync context: cold engine, no feeder task
+    result = manager.get_observation_source("SIM-BIDABS")
+    assert result is not None
+    _, _, _, descriptor = result
+    assert descriptor.source_mode == "sim"
+    assert descriptor.data_feed == "sim"
+    assert descriptor.window_start_utc is None
+    assert descriptor.window_end_utc is None
+    assert descriptor.dataset_id is None
+    assert descriptor.dataset_checksum is None
+    assert descriptor.session_id  # non-empty
+    assert descriptor.session_started_at_utc.endswith("Z")
+    assert descriptor.profile_id == "default"
+
+
+# === TC-2: historical watch descriptor with the real parsed window ============================
+
+
+def test_historical_watch_descriptor_carries_the_real_parsed_window():
+    manager = WatchManager(CONFIG)
+    provider = _hist_provider("HISTF")
+    manager.watch_with_provider(
+        "HISTF",
+        provider,
+        speed=1.0,
+        window_start_utc="2026-06-09T17:00:00.000000Z",
+        window_end_utc="2026-06-09T17:10:00.000000Z",
+    )
+    _, _, _, descriptor = manager.get_observation_source("HISTF")
+    assert descriptor.source_mode == "historical"
+    assert descriptor.data_feed == data_feed_for_scenario(provider.scenario, CONFIG)
+    assert descriptor.data_feed == "sip"  # the default config's historical_feed
+    assert descriptor.window_start_utc == "2026-06-09T17:00:00.000000Z"
+    assert descriptor.window_end_utc == "2026-06-09T17:10:00.000000Z"
+
+
+def test_progressive_historical_watch_descriptor_carries_the_shared_window():
+    manager = WatchManager(CONFIG)
+    first = _hist_provider("PROGF", n=5)
+    manager.watch_with_progressive_historical(
+        "PROGF",
+        first,
+        lambda: [],
+        speed=1.0,
+        window_start_utc="2026-06-09T17:00:00.000000Z",
+        window_end_utc="2026-06-09T18:00:00.000000Z",
+    )
+    _, _, _, descriptor = manager.get_observation_source("PROGF")
+    assert descriptor.source_mode == "historical"
+    assert descriptor.window_start_utc == "2026-06-09T17:00:00.000000Z"
+    assert descriptor.window_end_utc == "2026-06-09T18:00:00.000000Z"
+
+
+@pytest.mark.anyio
+async def test_main_watch_historical_route_threads_the_real_parsed_window_into_the_descriptor():
+    """The genuine end-to-end wiring proof for ``app/main.py``'s ``_watch_historical`` (iter-3 IN
+    SCOPE: thread the already-parsed start/end into the manager)."""
+    from fastapi.testclient import TestClient
+
+    quotes = (RawQuote(0.0, 16.0, 16.01, 100, 100),)
+    trades = (RawTrade(0.0005, 16.0, 100),)
+    window = HistoricalWindow("HROUTE", trades, quotes)
+    main_module.app.dependency_overrides[main_module.get_market_adapter] = lambda: FakeAdapter(
+        available=True, window=window
+    )
+    client = TestClient(main_module.app)
+    try:
+        resp = client.post(
+            "/watch/HROUTE",
+            json={
+                "mode": "historical",
+                "start": "2026-06-02T15:00:00",
+                "end": "2026-06-02T15:02:00",
+                "speed": 1,
+            },
+        )
+        assert resp.status_code == 200
+        _, _, _, descriptor = main_module.manager.get_observation_source("HROUTE")
+        assert descriptor.window_start_utc == "2026-06-02T15:00:00.000000Z"
+        assert descriptor.window_end_utc == "2026-06-02T15:02:00.000000Z"
+    finally:
+        main_module.manager.stop("HROUTE")
+        main_module.app.dependency_overrides.pop(main_module.get_market_adapter, None)
+        await asyncio.sleep(0.02)
+
+
+# === TC-3: live watch descriptor ================================================================
+
+
+@pytest.mark.anyio
+async def test_live_watch_descriptor_shows_the_config_owned_live_feed():
+    manager = WatchManager(FAST_STALE)
+    provider = FakeLiveProvider("LIVEF", "live LIVEF")
+    _seed_live(provider)
+    manager.watch_with_async_provider("LIVEF", provider)
+    try:
+        await _until(lambda: manager.get("LIVEF").snapshot().event_count >= 1)
+        _, _, _, descriptor = manager.get_observation_source("LIVEF")
+        assert descriptor.source_mode == "live"
+        assert descriptor.data_feed == CONFIG.live_feed == "iex"
+        assert descriptor.window_start_utc is None
+        assert descriptor.window_end_utc is None
+    finally:
+        manager.stop("LIVEF")
+        await _until(lambda: provider.socket.closed)
+
+
+# === TC-4: stop + re-watch mints a new session_id; mode/feed recomputed fresh, never carried ===
+
+
+def test_rewatch_mints_a_new_session_id_and_recomputes_mode_and_feed_fresh():
+    manager = WatchManager(CONFIG)
+    manager.watch("SIM-BUYER")
+    _, _, _, first_descriptor = manager.get_observation_source("SIM-BUYER")
+    assert first_descriptor.source_mode == "sim"
+    assert first_descriptor.data_feed == "sim"
+
+    assert manager.stop("SIM-BUYER") is True
+    manager.watch_with_provider("SIM-BUYER", _hist_provider("SIM-BUYER"), speed=1.0)
+    _, _, _, second_descriptor = manager.get_observation_source("SIM-BUYER")
+
+    assert second_descriptor.session_id != first_descriptor.session_id
+    # NEVER carried over from the old watch's mode/feed -- recomputed fresh for the new watch.
+    assert second_descriptor.source_mode == "historical"
+    assert second_descriptor.data_feed == "sip"
+    manager.stop("SIM-BUYER")
+
+
+# === TC-5: session identity stable across repeated reads of one watch =========================
+
+
+def test_session_identity_stable_across_repeated_reads():
+    manager = WatchManager(CONFIG)
+    manager.watch("SIM-SELLER")
+    _, _, _, first_read = manager.get_observation_source("SIM-SELLER")
+    _, _, _, second_read = manager.get_observation_source("SIM-SELLER")
+    assert first_read.session_id == second_read.session_id
+    assert first_read.session_started_at_utc == second_read.session_started_at_utc
+
+
+# === TC-6: the real running-task-switch clobber proof + counter-example =======================
+
+
+@pytest.mark.anyio
+async def test_settle_identity_check_prevents_a_stale_feeders_late_settle_from_clobbering_a_switch():
+    """TC-6: a live feeder GENUINELY still mid-flight (blocked on ``FakeLiveProvider``'s own
+    internal ``queue.get()`` inside the puller -- a real still-in-flight awaitable, never a
+    synthetic delay) when a switch/re-watch for the SAME ticker fires. Advancing the loop lets the
+    OLD feeder's ``CancelledError`` handler run its late ``_settle(old_engine, new_event=False)``
+    call -- the identity check makes that write a silent no-op, so ``get_observation_source``
+    still returns the NEW engine's settled pair and descriptor, never the old engine's."""
+    manager = WatchManager(FAST_STALE)
+    first = FakeLiveProvider("SWITCHT", "live SWITCHT-1")
+    _seed_live(first)  # a genuine settled event, so a would-be clobber is a real, visible one
+    first_engine = manager.watch_with_async_provider("SWITCHT", first)
+    first_task = manager._tasks["SWITCHT"]
+    await _until(lambda: first_engine.snapshot().event_count >= 1)
+    _, _, _, first_descriptor = manager.get_observation_source("SWITCHT")
+    # `first`'s internal queue is never fed again: the puller (and therefore the whole feeder) is
+    # now genuinely blocked awaiting it -- not a timer, a real pending awaitable.
+
+    second = FakeLiveProvider("SWITCHT", "live SWITCHT-2")
+    second_engine = manager.watch_with_async_provider("SWITCHT", second)  # the switch
+    assert second_engine is not first_engine
+
+    # Advance the loop enough for the OLD task's cancellation to be delivered and its
+    # `except asyncio.CancelledError` branch (and its late `_settle` call) to run to completion.
+    await _until(lambda: first_task.done())
+
+    result = manager.get_observation_source("SWITCHT")
+    assert result is not None
+    snapshot, _, _, descriptor = result
+    assert snapshot is second_engine.snapshot()  # NEVER the old engine's stale write
+    assert snapshot is not first_engine.snapshot()
+    assert descriptor.session_id != first_descriptor.session_id
+
+    manager.stop("SWITCHT")
+    await _until(lambda: second.socket.closed)
+
+
+def _naive_settle_without_identity_check(self, engine, *, new_event):
+    """The PRE-FIX ``_settle`` reproduced verbatim (no identity check) -- the reviewer's
+    carried-forward MINOR. Used ONLY by the counter-example below to prove the identity check is
+    load-bearing, not decorative."""
+    ticker = engine.snapshot().ticker
+    if new_event:
+        settled_at_epoch = time.time()
+    else:
+        prior = self._settled.get(ticker)
+        settled_at_epoch = prior[1] if prior is not None else None
+    self._settled[ticker] = (engine.snapshot(), settled_at_epoch)
+
+
+@pytest.mark.anyio
+async def test_counterexample_settle_without_identity_check_reproduces_the_clobber(monkeypatch):
+    """TC-6 counter-example: reverting ``_settle`` to the naive pre-fix version (no identity
+    check) reproduces the EXACT clobber the reviewer flagged -- a stale engine's late settle
+    write (the exact call ``_feed_live``'s ``except asyncio.CancelledError`` branch makes)
+    overwrites the fresh watch's settled pair with the OLD engine's stale snapshot.
+
+    ``first``'s feeder is left GENUINELY mid-flight (blocked on its own internal queue, a real
+    pending awaitable -- never a timer) when the switch fires, exactly as in the fix proof above.
+    The late write is then invoked DIRECTLY here (mirroring precisely what the cancellation
+    handler executes) rather than by waiting on ``first_task.done()``: with ``FAST_STALE``'s tiny
+    stale-gap, waiting for the old task's full async unwind lets the NEW engine's own periodic
+    stale-flip settle (which fires every ~50ms while ``second`` is never fed) repair the clobber
+    before the test can observe it, making that checkpoint non-deterministic. Asserting
+    immediately after the direct late write keeps this test's outcome deterministic while
+    exercising the identical code path and the identical stale/fresh-engine identities."""
+    monkeypatch.setattr(WatchManager, "_settle", _naive_settle_without_identity_check)
+    manager = WatchManager(FAST_STALE)
+    first = FakeLiveProvider("SWITCHC", "live SWITCHC-1")
+    _seed_live(first)
+    first_engine = manager.watch_with_async_provider("SWITCHC", first)
+    first_task = manager._tasks["SWITCHC"]
+    await _until(lambda: first_engine.snapshot().event_count >= 1)
+    # `first`'s internal queue is never fed again: its feeder is now genuinely blocked awaiting
+    # it -- a real pending awaitable, not a timer.
+
+    second = FakeLiveProvider("SWITCHC", "live SWITCHC-2")
+    second_engine = manager.watch_with_async_provider("SWITCHC", second)  # the switch
+    assert second_engine is not first_engine
+    snapshot, _, _, _ = manager.get_observation_source("SWITCHC")
+    assert snapshot is second_engine.snapshot()  # cold-reset pair, before any late write arrives
+
+    # Simulate the OLD feeder's late CancelledError-handler settle (the exact call
+    # `_feed_live`'s except branch makes) arriving AFTER the switch. Without the identity check
+    # (monkeypatched above), this naive write clobbers the fresh pair unconditionally.
+    manager._settle(first_engine, new_event=False)
+    snapshot, _, _, _ = manager.get_observation_source("SWITCHC")
+    assert snapshot is first_engine.snapshot()  # CLOBBERED: the OLD engine's stale write won
+    assert snapshot is not second_engine.snapshot()
+
+    # Cleanup only, no longer load-bearing for the assertion above: let `second`'s freshly
+    # created task actually start (reach its first await point) before cancelling it, so its
+    # `finally` block runs and closes the socket -- avoids a "cancelled before ever starting"
+    # no-op teardown that would otherwise hang the socket-closed wait below.
+    await asyncio.sleep(0.01)
+    manager.stop("SWITCHC")
+    await _until(lambda: first_task.done())  # let the old feeder's real cancellation unwind too
+    await _until(lambda: second.socket.closed)
+
+
+# === TC-7 / TC-8: every lifecycle status is distinguishable; tape_state/confidence never nulled ==
+
+
+def test_lifecycle_connecting_distinguishable_when_no_feeder_started():
+    # Sync (non-async) test function: no running event loop, so watch() leaves the engine COLD
+    # with no feeder task -- the honest "connecting" read (established pattern, see
+    # test_tape_observation_time.py's module docstring).
+    manager = WatchManager(CONFIG)
+    manager.watch("SIM-BUYER")
+    snapshot, settled_at_utc, end_reason, _ = manager.get_observation_source("SIM-BUYER")
+    assert snapshot.stream_status == "connecting"
+    assert settled_at_utc is None
+    assert end_reason is None
+
+
+@pytest.mark.anyio
+async def test_lifecycle_waiting_distinguishable_before_first_event():
+    manager = WatchManager(FAST_STALE)
+    provider = FakeLiveProvider("LIVEWAIT")
+    manager.watch_with_async_provider("LIVEWAIT", provider)
+    try:
+        await _until(lambda: manager.get("LIVEWAIT").snapshot().stream_status == "waiting")
+        snapshot, settled_at_utc, _, _ = manager.get_observation_source("LIVEWAIT")
+        assert snapshot.stream_status == "waiting"
+        assert settled_at_utc is None  # lifecycle-only mutation, no event settled yet
+        assert snapshot.bid is None and snapshot.ask is None and snapshot.last is None
+    finally:
+        manager.stop("LIVEWAIT")
... [diff_bound] apps/backend/tests/test_tape_observation_lifecycle_feed.py: 281 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_tape_observation_time.py b/apps/backend/tests/test_tape_observation_time.py
index 4d22c4c5..3d1d168f 100644
--- a/apps/backend/tests/test_tape_observation_time.py
+++ b/apps/backend/tests/test_tape_observation_time.py
@@ -150,7 +150,7 @@ def test_get_observation_source_pairs_snapshot_with_its_own_settled_time(monkeyp
 
     result = manager.get_observation_source("SIM-BIDABS")
     assert result is not None
-    snapshot, settled_at_utc, end_reason = result
+    snapshot, settled_at_utc, end_reason, _descriptor = result
     assert snapshot.timestamp == event.timestamp
     assert settled_at_utc == watch_manager._iso_utc(clock[0])
     assert end_reason is None
@@ -169,20 +169,20 @@ def test_atomic_read_never_mispairs_snapshot_n_plus_1_with_settled_time_n(monkey
     event_n = next(stream)
     engine.process_event(event_n)
     manager._settle(engine, new_event=True)
-    snapshot_n, settled_n, _ = manager.get_observation_source("SIM-BIDABS")
+    snapshot_n, settled_n, _, _ = manager.get_observation_source("SIM-BIDABS")
     assert snapshot_n.timestamp == event_n.timestamp
 
     clock[0] += 5.0  # wall clock advances -- but N+1 has not been settled yet
     event_n1 = next(stream)
     engine.process_event(event_n1)  # the engine's OWN internal snapshot now reflects N+1
 
-    still_snapshot, still_settled, _ = manager.get_observation_source("SIM-BIDABS")
+    still_snapshot, still_settled, _, _ = manager.get_observation_source("SIM-BIDABS")
     assert still_snapshot is snapshot_n  # STILL the exact N object, never a fresher N+1 read
     assert still_settled == settled_n  # STILL settled-time N, never re-stamped early
     assert engine.snapshot() is not still_snapshot  # the LIVE engine has already moved to N+1
 
     manager._settle(engine, new_event=True)  # now settle N+1
-    snapshot_n1, settled_n1, _ = manager.get_observation_source("SIM-BIDABS")
+    snapshot_n1, settled_n1, _, _ = manager.get_observation_source("SIM-BIDABS")
     assert snapshot_n1 is engine.snapshot()
     assert snapshot_n1.timestamp == event_n1.timestamp
     assert settled_n1 != settled_n
@@ -201,7 +201,7 @@ def test_counterexample_naive_read_mispairs_snapshot_and_settled_time(monkeypatc
     event_n = next(stream)
     engine.process_event(event_n)
     manager._settle(engine, new_event=True)
-    settled_snapshot_n, settled_n, _ = manager.get_observation_source("SIM-BIDABS")
+    settled_snapshot_n, settled_n, _, _ = manager.get_observation_source("SIM-BIDABS")
 
     event_n1 = next(stream)
     engine.process_event(event_n1)  # engine.snapshot() now reflects N+1; settle NOT yet called
@@ -220,7 +220,7 @@ def test_counterexample_naive_read_mispairs_snapshot_and_settled_time(monkeypatc
     # The atomic manager read, in contrast, NEVER exhibits this: it always returns the exact
     # settled snapshot object paired with its own settled_at -- never engine.snapshot()'s
     # current, possibly-fresher object.
-    atomic_snapshot, atomic_settled_at, _ = manager.get_observation_source("SIM-BIDABS")
+    atomic_snapshot, atomic_settled_at, _, _ = manager.get_observation_source("SIM-BIDABS")
     assert atomic_snapshot is settled_snapshot_n
     assert atomic_settled_at == naive_settled_at
     assert atomic_snapshot is not naive_snapshot  # the concrete mis-pair the naive tuple carries
@@ -237,11 +237,11 @@ def test_pause_carries_forward_settled_time_unchanged(monkeypatch):
     event = next(SimulatedProvider("SIM-BIDABS", "bid_absorption").stream())
     engine.process_event(event)
     manager._settle(engine, new_event=True)
-    pre_pause_snapshot, pre_pause_settled, _ = manager.get_observation_source("SIM-BIDABS")
+    pre_pause_snapshot, pre_pause_settled, _, _ = manager.get_observation_source("SIM-BIDABS")
 
     clock[0] += 120.0  # wall clock advances well past the pause
     assert manager.pause("SIM-BIDABS") is True
-    post_pause_snapshot, post_pause_settled, _ = manager.get_observation_source("SIM-BIDABS")
+    post_pause_snapshot, post_pause_settled, _, _ = manager.get_observation_source("SIM-BIDABS")
     assert post_pause_settled == pre_pause_settled
     assert post_pause_snapshot.tape_state == pre_pause_snapshot.tape_state
 
@@ -271,7 +271,7 @@ def test_rewatch_before_first_settle_never_returns_a_prior_watchs_stale_pair(mon
     event = next(SimulatedProvider("SIM-BIDABS", "bid_absorption").stream())
     first_engine.process_event(event)
     manager._settle(first_engine, new_event=True)
-    first_snapshot, first_settled, _ = manager.get_observation_source("SIM-BIDABS")
+    first_snapshot, first_settled, _, _ = manager.get_observation_source("SIM-BIDABS")
     assert first_settled is not None
 
     assert manager.stop("SIM-BIDABS") is True
@@ -281,7 +281,7 @@ def test_rewatch_before_first_settle_never_returns_a_prior_watchs_stale_pair(mon
 
     # BEFORE the fresh engine has processed any event, the settled pair must be a COLD read for
     # THIS engine -- never the prior watch's stale settled snapshot/time.
-    second_snapshot, second_settled, _ = manager.get_observation_source("SIM-BIDABS")
+    second_snapshot, second_settled, _, _ = manager.get_observation_source("SIM-BIDABS")
     assert second_snapshot is second_engine.snapshot()
     assert second_snapshot is not first_snapshot
     assert second_settled is None  # nothing has settled yet on the fresh engine
@@ -401,7 +401,7 @@ async def test_live_available_at_utc_equals_settled_at_utc_from_manager_clock(mo
     engine = manager.watch_with_async_provider("PGLIVE1", provider)
     try:
         await _until(lambda: engine.snapshot().event_count >= 1)
-        snapshot, settled_at_utc, _ = manager.get_observation_source("PGLIVE1")
+        snapshot, settled_at_utc, _, _ = manager.get_observation_source("PGLIVE1")
         assert settled_at_utc == watch_manager._iso_utc(fixed_now)
 
         observation = _build_for_snapshot(
@@ -434,7 +434,7 @@ async def test_counterexample_deriving_available_at_utc_from_observed_plus_lag_i
     engine = manager.watch_with_async_provider("PGLIVE2", provider)
     try:
         await _until(lambda: engine.snapshot().event_count >= 1)
-        snapshot, settled_at_utc, _ = manager.get_observation_source("PGLIVE2")
+        snapshot, settled_at_utc, _, _ = manager.get_observation_source("PGLIVE2")
         assert snapshot.delivery_lag_seconds == 0.0  # clamped -- never a fabricated negative lag
 
         observation = _build_for_snapshot(
@@ -471,7 +471,7 @@ async def test_settled_minus_observed_agrees_with_delivery_lag_seconds_telemetry
     engine = manager.watch_with_async_provider("PGLAG", provider)
     try:
         await _until(lambda: engine.snapshot().event_count >= 1)
-        snapshot, settled_at_utc, _ = manager.get_observation_source("PGLAG")
+        snapshot, settled_at_utc, _, _ = manager.get_observation_source("PGLAG")
         observed_epoch = snapshot.epoch_anchor + snapshot.timestamp
         settled_epoch = _parse_iso(settled_at_utc)
         assert snapshot.delivery_lag_seconds is not None
diff --git a/docs/phases/goal-observation-contract-iter-3.md b/docs/phases/goal-observation-contract-iter-3.md
new file mode 100644
index 00000000..1d5fa430
--- /dev/null
+++ b/docs/phases/goal-observation-contract-iter-3.md
@@ -0,0 +1,322 @@
+# Goal Iteration 3 — Source/session descriptor and lifecycle honesty (J-03, block 3 of the Binding Execution Order)
+
+<!-- machine-readable goal-mode metadata -->
+## Goal Mode Metadata
+
+- **Session ID:** observation-contract
+- **Iteration:** 3
+- **Mode:** next
+- **Depth:** lean
+- **Frontend Present:** no
+- **Target journeys:** J-03
+- **Required-still-passing journeys:** none (0 journeys are recorded passing this session as of
+  iter-2: 3 failing — J-03, J-04, J-05 — and 3 partial — J-01, J-02, J-06. This iteration is
+  backend-only and touches zero served/UI surface, so there is nothing `passing` to regress. Because
+  it edits `watch_manager.py`'s watch-creation and cancellation paths and `main.py`'s historical-watch
+  call sites, the foundation invariants that matter here are re-verified as TC scenarios below instead:
+  the full backend suite including `test_stream_lifecycle.py`, `test_feed_basis.py` and
+  `test_watch_manager.py` (all on the guard no-weaken / directly-touched-surface list),
+  `config_fingerprint = 08e471b10130e1e2`, `tsc --noEmit` 0 errors, and a Cockpit
+  Watch/Pause/Resume/Stop smoke check).
+- **Anti-goal reminders:**
+  - **Rail 3 (frozen foundations):** "the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, and archived-era behavior stay byte-identical. New work is additive and versioned beside them, never a mutation of them."
+  - **Rail 6 (single source of truth):** "each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations."
+  - **Rail 7 (deterministic and seeded):** "every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact."
+  - **Era-specific:** "No pooling, equating or silent conversion between `sim`, `iex` and `sip`."
+  - **Era-specific:** "No field, token or copy that reads as a trading action, readiness or verdict (READY, NO_TRADE, NO_VERDICT, `trade_allowed`, PENDING_CONDITION or any equivalent) anywhere in the artifact, the module, its tests or the spec's served surface."
+  - **Era-specific:** "No recomputation of any tape feature, state, confidence, freshness or feed basis outside the engine and the one existing `data_feed_for_scenario`; no second scenario-prefix parser."
+  - **Era-specific:** "No mandatory journey or test that requires Alpaca, the network, credentials or market hours."
+  - **Era-specific:** "No weakening of any existing guard: `test_no_execution_path.py`, `test_feed_basis.py`, `test_copy_discipline.py`, `test_profile_equivalence.py`, `test_fingerprint_epoch_retirement.py`, `test_mcp_server.py`, `test_stream_lifecycle.py`, `test_observer_equivalence.py` and `test_epoch_anchor.py` stay green and unedited except for additive registrations."
+
+## GOAL
+
+Give every managed watch (sim, live, historical) a real, manager-recorded source/session descriptor
+(mode, feed, window, session identity, profile) and prove the seven lifecycle statuses stay honest and
+the three feed bases stay distinct — step 3 of the Binding Execution Order — with zero visible product
+change.
+
+## BACKGROUND
+
+The evaluator's iter-2 next-step recommendation is explicit and binding: build J-03 — "give each watch a
+real source and session description (mode, scenario, window, session id, session start, data feed), keep
+the lifecycle wording honest across the seven statuses, and add
+`apps/backend/tests/test_tape_observation_lifecycle_feed.py`" — and fold in the reviewer's carried-forward
+MINOR finding first: `_settle` (`apps/backend/app/watch_manager.py:320`) keys its write off
+`engine.snapshot().ticker` alone, with no check that `engine` is still the CURRENTLY REGISTERED engine
+for that ticker. Direct inspection confirms the exact race: every feeder's `except asyncio.CancelledError`
+branch (for example `_feed_live`'s, `apps/backend/app/watch_manager.py:774-777`) calls
+`self._settle(engine, new_event=False)` on the OLD engine object, and that branch only actually runs when
+the cancelled task next reaches an `await` — which can happen AFTER a switch/re-watch has already reset
+`self._settled[ticker]` for the fresh engine (every `watch*` constructor does `self.stop(ticker)` then
+immediately `self._settled[ticker] = (new_engine.snapshot(), None)`). The late write silently clobbers the
+new watch's pair with the old engine's stale snapshot. The all-sync no-feeder harness in
+`test_stream_lifecycle.py` cannot exercise this because nothing is ever genuinely still in flight when a
+switch happens; this iteration adds a real async test that keeps a feeder mid-flight across the switch.
+
+Direct repo inspection also confirms `build_tape_observation` (iteration 1) already accepts every
+descriptor field this iteration must populate as caller-resolved parameters (`source_mode`, `data_feed`,
+`window_start_utc`, `window_end_utc`, `dataset_id`, `dataset_checksum`, `session_id`,
+`session_started_at_utc`, `profile_id`) — no change to `observation_contract.py` is in scope. What is
+genuinely missing is the manager-side machinery that resolves those values honestly: none of the four
+`watch*` constructors in `watch_manager.py` record a source/session descriptor today, `main.py`'s
+`_watch_historical` never threads its already-parsed `start`/`end` window into the manager, and
+`data_feed_for_scenario` (the single existing feed-basis function, `apps/backend/app/research/feed_basis.py`)
+is never called from the watch path. This narrows the iteration to `watch_manager.py` plus `main.py`'s two
+historical call sites plus one new test module — no change to `observation_contract.py`.
+
+Per the iter-0 lessons entry (applies through iteration 4): a flat journey table remains the expected
+signal — J-03's Acceptance is a conjunction that includes the served JSON, which does not exist until
+iteration 5. Do not move the route earlier. The iter-1 lessons entry flagged the import-guard tension
+(a guard forbids importing what a contract needs the value of) as likely to recur for "lifecycle/feed-basis
+vocabularies" at iteration 3. Checked directly: it does NOT recur here — `lifecycle.stream_status` and
+`source.data_feed` are free-form pass-through strings from `EngineSnapshot`/`data_feed_for_scenario`, not
+a closed vocabulary constant `observation_contract.py` itself must embed and cross-check (unlike
+`TAPE_STATE_VOCABULARY` at iteration 1), so nothing needs duplicating this iteration.
+
+## IN SCOPE
+
+### Backend
+- [ ] `WatchManager`: record a per-ticker source/session descriptor ONCE at each of the four `watch*`
+      constructor call sites (the same "cold reset per fresh engine" pattern already used for
+      `self._settled`) — `source_mode` (`"sim"` for `watch()`; `"historical"` for `watch_with_provider()`
+      and `watch_with_progressive_historical()`; `"live"` for `watch_with_async_provider()`), `data_feed`
+      (`data_feed_for_scenario(scenario, config)` — the one existing function), `window_start_utc` /
+      `window_end_utc` (pinned-ISO parsed UTC window for the two historical constructors, `None`
+      otherwise), `dataset_id` / `dataset_checksum` (`None` for every WatchManager-managed watch —
+      `dataset_replay` is a distinct in-process path outside the manager), `session_id` (`uuid.uuid4().hex`
+      minted fresh at construction — confirmed no existing per-watch identifier to reuse), and
+      `session_started_at_utc` (pinned-ISO wall clock at construction). Include `profile_id =
+      PROFILE_DEFAULT` as a constant field of the same descriptor (see NOTES assumption entry).
+- [ ] `watch_with_provider(...)` and `watch_with_progressive_historical(...)`: add optional
+      `window_start_utc: str | None = None, window_end_utc: str | None = None` parameters (backward
+      compatible defaults) so the manager can record the real request window.
+- [ ] `apps/backend/app/main.py`'s `_watch_historical`: thread the already-parsed `start`/`end` datetimes
+      (pinned-ISO formatted) into `manager.watch_with_provider(...)` / `manager.watch_with_progressive_historical(...)`
+      as the new `window_start_utc` / `window_end_utc` arguments. No other route change.
+- [ ] `WatchManager.get_observation_source(ticker)`: extend its return to also carry the source/session
+      descriptor recorded at watch creation, read from the SAME per-ticker state (no re-fetch, no second
+      read of the settled pair). Exact return shape (tuple/dataclass) is an implementation choice, as
+      iteration 2 already deferred.
+- [ ] Fix the reviewer's carried-forward MINOR: `_settle` (`watch_manager.py:320`) must skip its write
+      (silent no-op, no exception) whenever `self._engines.get(ticker) is not engine` — i.e. the engine
+      calling `_settle` is no longer the currently-registered engine for that ticker (already stopped, or
+      superseded by a switch/re-watch). This is the identity check the reviewer asked for before the
+      route becomes the first production reader of `get_observation_source` at iteration 5.
+- [ ] Create `apps/backend/tests/test_tape_observation_lifecycle_feed.py` covering, each as a named test
+      (Required Trap Coverage items 25-31): a table-driven pass over all seven `lifecycle.stream_status`
+      values using the existing `test_stream_lifecycle.py` harness (paced + live feeders), plus `paused`,
+      natural `closed` (`end_reason="stream_closed"`), in-process `watch_stopped` (post-`stop()`,
+      `get_observation_source` returns `None`), `failed` (`end_reason=None`), and live `waiting`/`stale`
+      with zero events (both times null) — every status distinguishable from the artifact/return value
+      alone; `tape_state`/`confidence` never nulled or rewritten by any lifecycle transition; feed-basis
+      distinctness across `LiveProvider` (`iex` / `live_settled_wall_clock`), the committed PG SIP
+      `HistoricalProvider` fixture (`sip` / `historical_arrival_unknown`) and sim (`sim` /
+      `simulated_not_applicable`) — pairwise distinct, never pooled; dataset-manifest feed-owner agreement
+      across every committed fixture dataset under `tests/fixtures/datasets_j03/`; an AST guard proving no
+      second scenario-prefix parser exists outside `data_feed_for_scenario` and the manager descriptor;
+      session identity present, stable across repeated reads of one watch, different across two successive
+      watches of the same ticker, and an AST guard proving no `app/engine/*.py` module references
+      `session_id` / `session_started_at_utc`; a scoped scan of one fully-built artifact dict for the fixed
+      actionability-token list (`READY`, `NO_TRADE`, `NO_VERDICT`, `trade_allowed`, `PENDING_CONDITION`),
+      case-insensitively, finding zero matches.
+- [ ] A REAL async running-task-switch test (not the existing sync no-feeder harness): start a live/paced
+      watch whose feeder is genuinely still mid-flight (an async provider blocked on an unresolved
+      awaitable), trigger a switch/re-watch for the SAME ticker, advance the event loop enough to run the
+      old feeder's cancellation handler, and assert `get_observation_source(ticker)` returns the NEW
+      engine's settled pair and descriptor — never the old engine's stale write.
+- [ ] Each item above ships a named `test_counterexample_*` proving it can fail (nulling `tape_state` on
+      `stale`; equating `iex`/`sip`; reusing a `session_id` across two watches; reverting the `_settle`
+      identity check to reproduce the clobber; injecting an actionability token).
+
+### Frontend (if applicable)
+None — zero frontend files touched this iteration (goal Product Shape: "No page, panel, link or
+component is added or modified").
+
+### New user-facing capability
+None. The source/session descriptor and the `_settle` identity fix are in-process manager state with no
+served, watched or visible surface.
+
+### New information displayed
+None — nothing is served by any endpoint, page or MCP tool yet (route is iteration 5).
+
+### New user actions
+None. The existing Watch / Pause / Resume / Stop controls on `/` are exercised only as regression
+coverage for the touched watch-creation and cancellation code paths — no new control, no visible
+behavior change.
+
+### UI surface changes
+None — Cockpit `/`, `/structure`, `/desk` are untouched.
+
+### Product surface delta
+None visible. The only artifacts of this iteration are changes inside `apps/backend/app/watch_manager.py`
+and `apps/backend/app/main.py`'s two historical call sites, plus one new test module; a user (or
+browser-qa) sees the exact same product as after iter-2.
+
+### Blueprint conformance
+No new surfaces. `runs/goal-session-observation-contract/state/blueprint.md`'s Information Architecture
+is unchanged (no page, no nav entry). This iteration completes the "Provenance / source / lifecycle
+metadata" Data Contract row's computing module (`WatchManager.get_observation_source`) with the
+source/session descriptor half; the row's registered future computing-module/serving-endpoint pairing
+does not change. `blueprint.md` has been updated in place (row + progress note) to reflect iter-3's
+completion — no nav-skeleton change, so no re-approval request was filed.
+
+### Data-contract additions
+None. The source/session descriptor exists as in-process `WatchManager` state only this iteration — it
+is not served by any endpoint, so no NEW displayed value exists to register. `blueprint.md`'s existing
+Provenance/source/lifecycle-metadata row already named `WatchManager.get_observation_source` as the
+eventual (partial) computing module; this iteration completes it (still unserved — the route lands
+iteration 5) without changing the registered future serving endpoint (`GET /tape/{ticker}/observation`).
+
+## OUT OF SCOPE
+
+- The route `/tape/{ticker}/observation` and any wiring into `apps/backend/app/main.py` beyond threading
+  `window_start_utc`/`window_end_utc` into the two historical watch call sites — the route itself is
+  Binding Execution Order step 5 (iteration 5, J-05); it still 404s for every ticker after this iteration.
+- Any change to `apps/backend/app/observation_contract.py` or `build_tape_observation` — the descriptor
+  parameters it already accepts (from iteration 1) need no change; this iteration only makes their VALUES
+  genuinely correct at the source.
+- `tests/test_tape_observation_path_equivalence.py`, `_route.py`, `_guards.py` — later iterations' own
+  modules (4, 5, 6); this iteration ships only `test_tape_observation_lifecycle_feed.py`.
+- The full copy-discipline / external-system-reference / English-only / real-provider-isolation /
+  mutator-call-site guard MODULE (`test_tape_observation_guards.py`, iteration 6, J-06). This iteration's
+  actionability-token check is a scoped grep serving J-03's own acceptance only.
+- `dataset_id`/`dataset_checksum` population for `dataset_replay` — out of the WatchManager's descriptor
+  scope; `dataset_replay` is a distinct in-process caller identified by its own manifest, never a managed
+  watch.
+- Any `Config` field addition (the era adds zero; module-level constants/helpers only).
+- Any frontend file, page, panel or nav change.
+- Real-provider (Alpaca) network calls — `LiveProvider` is exercised only over committed fixture/merged
+  records and monkeypatched/fake harnesses, never a live vendor connection.
+
+## DEFINITION OF DONE
+
+- [ ] Every `WatchManager` `watch*` constructor records a per-ticker source/session descriptor
+      (`source_mode`, `data_feed`, window bounds, `dataset_id`/`dataset_checksum=None`, `session_id`,
+      `session_started_at_utc`, `profile_id`) at creation, exposed by `get_observation_source(ticker)`
+      alongside the existing atomic settled pair, with no re-fetch.
+- [ ] `_settle` never overwrites a ticker's settled pair with a stale/superseded engine's write (identity
+      check in place); the real running-task-switch test proves the previously-reproducible clobber no
+      longer occurs, and its `test_counterexample_*` (reverting the check) shows the clobber reproduces.
+- [ ] `apps/backend/tests/test_tape_observation_lifecycle_feed.py` passes with 0 failures, and every
+      `test_counterexample_*` test it ships is present and passes.
+- [ ] Full backend suite still green — no fewer than iter-2's baseline of 4001 passed / 8 skipped / 0
+      failed, plus this iteration's new tests, 0 failed. `test_stream_lifecycle.py`, `test_feed_basis.py`
+      and `test_watch_manager.py` pass unedited except for any additive registration.
+- [ ] `Config.config_fingerprint()` unchanged (`08e471b10130e1e2`); `cd apps/frontend && npx tsc
+      --noEmit` reports 0 errors (unaffected — no frontend file touched).
+- [ ] Browser-qa confirms zero visible product change: `/`, `/structure`, `/desk` render exactly as at
+      iter-2; `/tape/SIM-BIDABS/observation` still 404s (route not yet built — expected, correct, not a
+      defect); Watch / Pause / Resume / Stop on `/` behave exactly as before.
+- [ ] No anti-goal violation introduced (scan-report CLEAN).
+- [ ] Dev handoff written at `docs/handoffs/goal-observation-contract-iter-3-dev.md`.
+
+Note on J-03's overall journey status: this iteration cannot make J-03 fully pass — its Acceptance
+requires the served JSON at `/tape/SIM-BIDABS/observation`, which needs the route (iteration 5). Expect
+the evaluator to record J-03 as still `failing` or move it to `partial` on the strength of the passing
+`test_tape_observation_lifecycle_feed.py` module, per the same convention applied to J-01/J-02; this is
+correct, not a regression.
+
+## TESTING REQUIREMENTS
+
+- Browser: no journey's Acceptance can be newly satisfied this iteration (route absent). Confirm
+  `/tape/SIM-BIDABS/observation` still answers "Not Found" after a live Sim watch; confirm `/structure`
+  and `/desk` render unchanged; confirm Watch → Pause → Resume → Stop on `/` still transition the status
+  dot through live → paused → live → closed in that order (regression smoke on the touched `watch_manager.py` code paths).
+- Unit/integration: `apps/backend/tests/test_tape_observation_lifecycle_feed.py` (new) — see TC-1..TC-16
+  below. No integration test needs a running uvicorn server or network access.
+- Error cases: an unrecognized lifecycle status is never produced by any code path (only the seven
+  defined values plus `watch_stopped` ever appear); a stale/superseded engine's `_settle` call is a silent
+  no-op, never an exception, never a state mutation.
+
+Test-first contract:
+
+- TC-1: given a fresh sim watch for `SIM-BIDABS`, when `get_observation_source("SIM-BIDABS")` is called
+  right after watch creation, then the returned descriptor shows `source_mode="sim"`, `data_feed="sim"`,
+  `window_start_utc=None`, `window_end_utc=None`, `dataset_id=None`, `dataset_checksum=None`, a
+  non-empty `session_id`, a pinned-ISO `session_started_at_utc`, and `profile_id="default"`.
+- TC-2: given a historical watch created with a parsed UTC start/end window, when
+  `get_observation_source(ticker)` is called, then `source_mode="historical"`, `data_feed` equals
+  `data_feed_for_scenario` for that scenario (`"sip"` by default config), and `window_start_utc` /
+  `window_end_utc` equal the pinned-ISO parsed request window exactly.
+- TC-3: given a live watch fed via `LiveProvider` over fixture/merged records, when
+  `get_observation_source(ticker)` is called, then `source_mode="live"` and `data_feed` equals the
+  config-owned `live_feed` value (`"iex"` by default).
+- TC-4: given the same ticker watched, stopped, and re-watched, when `session_id` is read at each watch,
+  then the two values differ, while `source_mode`/`data_feed` are recomputed fresh for the new watch's
+  mode (never carried over from the old watch's descriptor).
+- TC-5: given one watch left running, when `get_observation_source(ticker)` is called twice without any
+  intervening lifecycle change, then `session_id` and `session_started_at_utc` are identical across both
+  reads (stable within one watch).
+- TC-6: given a live/paced feeder task genuinely still executing (an async provider blocked mid-iteration
+  on an unresolved awaitable), when a switch/re-watch for the SAME ticker is issued and the event loop is
+  then advanced enough to run the old feeder's `CancelledError` handler, then `get_observation_source(ticker)`
+  returns the NEW engine's settled pair and descriptor, never the old engine's; `test_counterexample_*`
+  reverting the `_settle` identity check reproduces the old clobber (the new pair is overwritten).
+- TC-7: given each of the seven `lifecycle.stream_status` values (`connecting`, `waiting`, `live`,
+  `stale`, `paused`, `closed`, `failed`) plus the in-process `watch_stopped` case, when
+  `build_tape_observation(...)` is called for each (or `get_observation_source` is called after `stop()`
+  for `watch_stopped`), then every case is distinguishable from every other by `lifecycle.stream_status`
+  (or the `None` return) alone.
+- TC-8: given a `stale`, `closed` or `failed` transition after at least one processed event, when the
+  artifact is built, then `tape_state` and `confidence` equal their last-processed values exactly (never
+  null, never rewritten); `test_counterexample_*` shows a build that nulls them on `stale` fails the
+  assertion.
+- TC-9: given a sim watch, a `HistoricalProvider` watch over the committed PG SIP fixture, and a
+  `LiveProvider` watch, when each one's `(data_feed, availability_basis)` pair is read, then the three
+  pairs (`sim`/`simulated_not_applicable`, `sip`/`historical_arrival_unknown`, `iex`/`live_settled_wall_clock`)
+  are pairwise distinct and never equal to one another.
+- TC-10: given every committed fixture dataset under `tests/fixtures/datasets_j03/`, when its manifest
+  `data_feed` is compared against a fresh call to `data_feed_for_scenario(meta["scenario"], config)`, then
+  the two values are equal for every fixture; `test_counterexample_*` mutates one manifest's `data_feed`
+  in a loaded copy and shows the comparison fails on it.
+- TC-11: given `app/watch_manager.py` and `app/main.py`'s source, when an AST scan runs for a second
+  scenario-prefix parser (a bare scenario-string check computing a feed or source-mode value outside
+  `data_feed_for_scenario` and the manager's own descriptor recording), then zero occurrences are found;
+  given `app/engine/*.py`'s source, when scanned for `session_id` / `session_started_at_utc` references,
+  then zero occurrences are found.
+- TC-12: given a fully-built `TapeObservation` dict for a live watch, when it is scanned case-insensitively
+  for `READY`, `NO_TRADE`, `NO_VERDICT`, `trade_allowed`, `PENDING_CONDITION`, then zero matches are found;
+  `test_counterexample_*` injects one of those tokens into a copy of the dict and shows the scan catches it.
+- TC-13: given the full backend suite, when `cd apps/backend && .venv/bin/python -m pytest tests/ -q` is
+  run, then the pass count is >= 4001 (iter-2 baseline) plus the count of tests newly added in
+  `test_tape_observation_lifecycle_feed.py`, with 0 failed, and `Config.config_fingerprint()` still
+  returns `08e471b10130e1e2`.
+- TC-14: given `cd apps/frontend && npx tsc --noEmit` is run after this iteration's changes, then it
+  reports 0 errors (no frontend file was touched).
+- TC-15: given the goal-mode scan step over the diff restricted to `apps/`, `docs/`, `scripts/`, when it
+  runs, then the report is CLEAN with zero secret/dependency/license findings.
+- TC-16: given `SIM-BIDABS` watched live via the Cockpit, when `/tape/SIM-BIDABS/observation` is
+  requested over HTTP (browser-qa), then the response is still a 404 "Not Found" body, and
+  Pause / Resume / Stop on `/` behave exactly as before.
+
+## NOTES
+
+- Applying the iter-0 lessons entry (applies through iteration 4): a flat journey table this iteration
+  (J-03 not fully unlocked) is the expected, correct signal — do not read it as a stall and do not move
+  the route earlier. Score this iteration on `test_tape_observation_lifecycle_feed.py`'s pass/fail and
+  the honest absence of the route, not on J-03's merged verdict alone.
+- Applying the iter-1 lessons entry: it flagged `availability_basis`/lifecycle/feed-basis vocabularies as
+  candidates for the same guard-forbidden-import tension iter-1 hit with `TAPE_STATE_VOCABULARY`. Checked
+  directly this iteration (as iter-2 did for `availability_basis`): it does not recur — `lifecycle.stream_status`
+  and `source.data_feed` are free-form pass-through strings, not a closed vocabulary constant
+  `observation_contract.py` must embed and cross-check, so nothing needs duplicating here.
+- Applying the iter-2 lessons entry (the `_settle` clobber risk): this iteration is the fix — the
+  identity check plus the real running-task-switch test named there (TC-6 above).
+- The iter-2 lessons entry about `tests/test_tick_recorder.py::test_tr31_...` being a genuine
+  time-dependent flake applies here too: a single failure in that one unrelated test during the full-suite
+  re-run is not a regression signal — re-run before treating it as one.
+- Two interpretation calls logged to `runs/goal-session-observation-contract/state/assumptions.md`
+  (iter-3): (1) `profile_id=PROFILE_DEFAULT` is stored as a constant field of the per-watch descriptor
+  recorded at creation, per Key Capability 4's literal wording, rather than left for the iteration-5 route
+  to supply inline; (2) J-03's own test module ships a SCOPED actionability-token scan satisfying its own
+  acceptance step now, while the general-purpose, lexicon-driven guard module remains iteration 6's
+  (Required Trap Coverage item 31 is listed under both journeys by design, not duplicated work).
+- The pytest venv (9.1.1) prints no final "N passed" summary line; tally via `-q` progress characters or
+  `--collect-only -q` per-file counts, per the iter-0 lessons entry — do not grep for a summary line that
+  never appears.
+- No full-depth trigger holds: this iteration touches one already-incrementally-built manager module
+  (`watch_manager.py`) plus two call sites in an already-touched route module (`main.py`), is purely
+  additive to the ALREADY-registered "Provenance / source / lifecycle metadata" blueprint row (no
+  computing-module or serving-endpoint change to any value outside a still-unserved row), carries no
+  frontend work, and follows a CONTINUE verdict (not ESCALATE). The hardening cadence (6) is not yet due
+  (this is the 3rd consecutive lean iteration). Lean matches the evaluator's binding recommendation.
```

## Excluded-path stat (dependency/lockfile visibility)

 .../goal-session-observation-contract-index.html   |  28 +-
 ...bservation-contract-iter-2-iteration-summary.md |  75 ++
 reports/qa-scoped-backend-store-manifest.md        |  26 +-
 reports/security/install-decisions.jsonl           |   2 +
 .../.engine.lock/boot_id                           |   1 -
 .../.engine.lock/cmd                               |   1 -
 .../.engine.lock/epoch                             |   1 -
 .../.engine.lock/host                              |   1 -
 .../.engine.lock/pid                               |   1 -
 .../dispatch/.pump-alive                           |   4 +-
 .../dispatch/req.9-HHu8Ye.out                      |   1 -
 .../dispatch/req.9-HHu8Ye.ready                    |   1 -
 .../dispatch/req.9-HHu8Ye.res                      |   1 -
 .../dispatch/req.9-HHu8Ye.started                  |   3 -
 runs/goal-session-observation-contract/engine.pid  |   1 -
 .../iter-3/.steps/decomposer.done                  |   1 +
 .../iter-3/depth-dispatched                        |   1 +
 .../iter-3/goal-slice-exec.md                      | 949 +++++++++++++++++++++
 .../iter-3/goal-slice.md                           | 949 +++++++++++++++++++++
 .../iter-3/snapshot-sha                            |   1 +
 .../goal-session-observation-contract/session.json |   6 +-
 .../state/assumptions.md                           |  31 +
 .../state/blueprint.md                             |  13 +-
 .../state/project-story.md                         |  12 +-
 runs/goal-session-observation-contract/summary.md  |  67 +-
 .../telemetry.jsonl                                |  56 ++
 .../trace/trace.jsonl                              |   3 +
 27 files changed, 2167 insertions(+), 69 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
