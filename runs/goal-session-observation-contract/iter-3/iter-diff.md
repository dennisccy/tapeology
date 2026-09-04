# Iteration diff (bounded)

Files changed: 37. Shown in full: 33.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_tape_observation_lifecycle_feed.py` (281 lines not shown)
- `incredible_auto_dev/.claude/hooks/lib/read_path_hygiene.py` (330 lines not shown)
- `incredible_auto_dev/hooks/lib/read_path_hygiene.py` (330 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/analyze_transcripts.py` (223 lines not shown)

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
diff --git a/incredible_auto_dev/.claude/anti-patterns/28-styled-verdict-cells-unparsed.md b/incredible_auto_dev/.claude/anti-patterns/28-styled-verdict-cells-unparsed.md
new file mode 100644
index 00000000..6ff27703
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/28-styled-verdict-cells-unparsed.md
@@ -0,0 +1,11 @@
+## 28. Markdown-styled verdict cells vanish from the machine parser and launder FAIL into PASS
+
+**Applies to:** any parser that extracts machine verdicts (PASS/FAIL/SKIP) from agent-written markdown, and any gate that consumes the parsed result.
+
+**Pattern:** `merge_ui_test_results.py` matched verdict cells with `cell.strip().upper() in ("PASS","FAIL",...)`. Agents legitimately write `**FAIL**`, `` `SKIPPED` ``, or `PASS (with caveat)` — none of which match, so the cell parsed as NO verdict and silently dropped out of `compute_overall()`. With the FAIL rows invisible, the surviving PASS rows made the merged headline PASS while the raw lane file said FAIL — observed live twice (ops-hardening iter-9: 2 bold FAILs → merged PASS handed to the achievement gate; iter-12: header undercount). Auditors caught it both times only by re-reading the raw files.
+
+**Why it fails:** The parser treated "doesn't match my exact format" as "carries no information" at exactly the layer where a dropped FAIL flips a gate outcome. Absence-of-verdict and PASS must never be conflated by a downstream `any(FAIL)` reduction; and agent output formats drift (bold, backticks, annotations) faster than parsers pin them.
+
+**Prevention:** Normalize markdown emphasis (`c.strip().strip("*_`~")`) before matching; accept annotated verdicts via a word-boundary prefix match (`^(PASS|FAIL|SKIPPED|SKIP)\b`) scanned in REVERSE cell order so the verdict column outranks free-prose columns; keep bare-word prose non-matching. Every such parser carries a self-test case with bold/backtick/annotated verdicts wired into `run-evals.sh` (`merge_ui_test_results.py self-test`, cases `bold_verdicts` / `annotated_verdicts`). Rule: a verdict parser change ships with a fixture of REAL agent output that previously mis-parsed.
+
+**Detection:** merged headline disagrees with a raw lane file's headline; `compute_overall` counter shows empty-string verdicts (`Counter({'PASS': n, '': k})`) for rows that visibly carry verdicts.
diff --git a/incredible_auto_dev/.claude/anti-patterns/29-plan-line-suppresses-lane.md b/incredible_auto_dev/.claude/anti-patterns/29-plan-line-suppresses-lane.md
new file mode 100644
index 00000000..3cad7ad2
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/29-plan-line-suppresses-lane.md
@@ -0,0 +1,11 @@
+## 29. A plan metadata line can silently suppress an entire verification lane
+
+**Applies to:** goal mode; any pipeline step whose execution is gated on a model-written metadata line rather than on the work the spec demands.
+
+**Pattern:** The browser-QA lane ran only when the orchestrator's plan contained `Frontend Present: yes` (`detect_frontend_in_plan`). In ops-hardening iter-8 the spec itself mis-wrote `Frontend Present: no` while its own DoD named browser journeys to verify — so the ENTIRE browser lane (browser-qa, ui artifacts) was skipped, journeys J-01/J-03/J-04 fell to `unknown`, J-05 stayed `regressed` unverified, and the iteration closed CLOSURE-FAIL. Every later iteration worked around it by hand-writing `Frontend Present: yes` into specs whose diffs contained zero frontend files — a standing landmine had anyone written the honest-looking "no".
+
+**Why it fails:** The gate keyed on a MODEL-authored line (twice removed from ground truth) instead of the engine's own knowledge that this iteration names user journeys — which are user-visible by contract and therefore always need browser evidence. One wrong word in generated prose disabled a verification lane with no error, no log line, and downstream artifacts (`N/A stubs`) that look intentional.
+
+**Prevention:** The engine exports its parsed journey list (`CHAIN_GOAL_TARGET_JOURNEYS`, run-goal.sh) and `detect_frontend_in_plan` (lib/common.sh) force-returns frontend-present whenever it is non-empty, logging the override (`forcing browser lane despite plan`). Phase mode is untouched (the variable is only set by run-goal.sh). Rule: a lane that produces required evidence must be gated on engine-parsed facts (journey list, diff contents), never solely on model-written plan prose; when prose and facts disagree, run the lane and log the contradiction.
+
+**Detection:** a goal iteration whose spec/DoD names `J-` journeys but whose reports directory has `N/A` browser stubs; journeys dropping to `unknown` after an iteration that claimed completion.
diff --git a/incredible_auto_dev/.claude/anti-patterns/30-process-identity-by-cmdline-substring.md b/incredible_auto_dev/.claude/anti-patterns/30-process-identity-by-cmdline-substring.md
new file mode 100644
index 00000000..d78e9bc8
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/30-process-identity-by-cmdline-substring.md
@@ -0,0 +1,17 @@
+## 30. Process identity resolved by substring-matching a whole command line
+
+**Pattern:** `goal-await-dispatch.sh` resolved the pump's long-lived `claude` session binary by walking `/proc` ancestry and taking the first process whose **entire** `/proc/<pid>/cmdline` contained the substring `claude`. Some CLI harnesses run every Bash tool call as `bash -c 'source ~/.claude/shell-snapshots/snapshot-bash-<n>.sh …'`. That wrapper's cmdline contains `claude` — from the `.claude` **path component**, not from the program — and it lives for exactly one tool call. So the helper stamped the wrapper's pid into `.pump-alive` and `<req>.started`, the wrapper exited the instant the helper returned, and the engine's protocol-v3 fast-pause correctly concluded "pump pid is dead" and halted the session `AWAITING_PUMP` — **on the first dispatch of every run**, before any developer mutation. The failure looked like a pump/session problem, so the standing workaround was to hand-export `CHAIN_PUMP_PID` per session.
+
+**Why it fails:** A command line is not an identity. It is a haystack containing the program, its arguments, config paths, snapshot paths and env-setup boilerplate — any of which may embed the tool's own name. The identity lives in exactly two places: `/proc/<pid>/comm` and the basename of `argv[0]`. Matching the haystack turns every ancestor that merely *mentions* the tool into a candidate, and the shortest-lived candidate wins because the walk stops at the first hit — the wrapper is always nearer than the real binary. The bug was invisible on hosts whose wrapper cmdline happened not to contain the string, which is why it shipped.
+
+**Prevention:** Applies to any code that identifies a process by inspecting `/proc`, `ps` output, or a process table.
+- Match the **program**: `comm`, or `${argv0##*/}`. Never grep a whole cmdline for a name that could appear as a path component.
+- When a legacy whole-cmdline scan must be kept for coverage (e.g. `node …/cli.js` installs where `comm` is `node`), run it as a **second** pass and exclude shells (`bash|sh|dash|zsh|ksh|busybox`) — a shell is a transient wrapper, never the long-lived binary you are looking for.
+- Make the failure asymmetric on purpose: a **miss** must degrade to the safe default (here: no ident → contentless protocol-v2 files → the engine keeps both timeout nets). A false **positive** breaks the run, so bias every rule toward precision.
+- A liveness anchor must outlive what it anchors. Before recording a pid as "this work is alive", check that the process you picked is not shorter-lived than the work.
+
+**Example (bad):** `grep -qa 'claude' "/proc/$anc/cmdline" && PUMP=$anc` — matches `bash -c 'source ~/.claude/…'`.
+**Example (good):** `comm=$(tr -d '\n' < /proc/$anc/comm); a0=$(tr '\0' '\n' < /proc/$anc/cmdline | head -1); a0=${a0##*/}; [[ "$comm" == *claude* || "$a0" == *claude* ]] && PUMP=$anc`
+
+**Detection:** `[interactive-dispatch] pump is gone: pump pid <N> is dead … (claimed dispatch)` within seconds of the first dispatch, while the session is plainly still open; `pid=` in `<dispatch-dir>/.pump-alive` naming a pid that no longer exists and was never the CLI. 30-second repro: `bash -c '# ~/.claude/x.sh
+echo $$; grep -c claude /proc/$$/cmdline'` — a shell that matches while owning nothing. Regression test: `goal-await-dispatch.sh --self-test`, scenario 6b.
diff --git a/incredible_auto_dev/.claude/anti-patterns/31-rule-documented-where-nobody-reads-it.md b/incredible_auto_dev/.claude/anti-patterns/31-rule-documented-where-nobody-reads-it.md
new file mode 100644
index 00000000..67c0acca
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/31-rule-documented-where-nobody-reads-it.md
@@ -0,0 +1,17 @@
+## 31. A rule written where the agent never reads it
+
+**Pattern:** `.claude/core.md` § "File Paths in Bash" tells every agent never to root a recursive search at the repo root, precisely so dispatches do not stall on a human approval prompt. The rule was correct, current, and had shipped one commit earlier. The very next dispatch, the developer agent ran `grep -rl "…" --include="*.md" .` and the run stopped dead waiting on a human. The agent's body reached the rule only through one line — "Apply `.claude/core.md` strictly" — at **line 142 of 144**, and following it required a separate `Read` the agent never performed before its first search.
+
+**Why it fails:** Authoring a rule and delivering a rule are different jobs, and finishing the first feels like finishing both. A pointer to another file is a *request* that the agent spend a turn and a chunk of context to fetch guidance whose value it cannot assess before fetching — so under a token policy that says "read the curated inputs your agent file lists", skipping it is the locally rational choice. The failure is silent from the authoring side: the rule is in the repo, greppable, and reviewers confirm it exists. Worse, the cost lands on the human, not the agent: the agent blocks, and someone has to notice and click.
+
+**Prevention:** Applies to any rule whose violation blocks or corrupts a run rather than merely degrading quality.
+- Classify by consequence, not by topic. A rule that can **stall or break** a dispatch belongs in guaranteed-delivery context; a rule that shapes quality can live behind a pointer.
+- Guaranteed delivery means the text is in the prompt or the system prompt when the agent takes its first action — not one Read away. In this framework the delivery seam is the dispatch preamble built by `lib/interactive-dispatch.sh` (where the TMPDIR bridge already lives): it reaches every agent on the backend, needs no agent cooperation, and costs no prompt-cache prefix invalidation the way editing `CLAUDE.md` does.
+- Gate injected text on a marker that identifies a real agent dispatch (here: the `Agent instructions: .claude/agents/` pointer line) so two-key confirms, ad-hoc dispatches and byte-exact self-tests pass through untouched.
+- Keep both copies: the full rule stays in `core.md` as the authority, the preamble carries a one-line operational form that names it. Do not let the short form become the only statement of the rule.
+- After writing any process rule, ask the delivery question out loud: *which file is in the agent's context at the moment it would break this rule?* If the answer is "none", the rule is not deployed yet.
+
+**Example (bad):** `.claude/core.md` holds the rule; `agents/<name>/body.md` says "Apply `.claude/core.md` strictly" on its second-to-last line.
+**Example (good):** the authority stays in `core.md`, and the dispatch preamble appends `Path-safety note: root every recursive read at concrete subdirectories … Full rule: .claude/core.md § File Paths in Bash.` to every agent prompt.
+
+**Detection:** An agent violates a rule that demonstrably exists in the repo, and its transcript contains no Read of the file holding it. Audit sweep: for each rule whose breach halts a run, grep the dispatch preamble and the agent's rendered `.claude/agents/*.md` frontmatter+body for the rule's own words — a hit only in `core.md` means undelivered. Regression test: `lib/interactive-dispatch.sh --self-test`, test 24.
diff --git a/incredible_auto_dev/.claude/anti-patterns/32-guard-modelled-on-prose-not-the-enforcer.md b/incredible_auto_dev/.claude/anti-patterns/32-guard-modelled-on-prose-not-the-enforcer.md
new file mode 100644
index 00000000..eba5e8f3
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/32-guard-modelled-on-prose-not-the-enforcer.md
@@ -0,0 +1,39 @@
+## 32. A guard or allowlist modelled on prose instead of the enforcer's own rules
+
+**Pattern:** six allow entries were added to silence prompts nobody had observed
+(`Bash(nohup *)` cannot match anything — the checker strips `nohup` before rule matching;
+`Bash(setsid *)` cannot pre-approve an exec wrapper by documented design), and `core.md`
+listed `tee`/`install` as hard-gated after a `cd` (they are not path-restricted at all)
+while omitting `rmdir`, redirects and `git` (which are) — and the first guard denied
+absolute-path reads, `ag`/`less` after a `cd`, and any "Nth non-flag argument" as a path
+(`head -n 20`), none of which the checker gates.
+
+**Why it fails:** the enforcer (Claude Code's permission checker) has a fixed
+path-restricted command table, a fixed wrapper list and fixed compound rules. A rule
+written from a symptom or from memory either never matches (a dead entry that only
+weakens review — the classifier was correctly blocking `nohup uvicorn --host 0.0.0.0`) or
+misdescribes the gate, so agents avoid harmless shapes and walk into gated ones. Both
+cost a human click or a retry turn, and neither was visible in any metric.
+
+**Prevention:** Applies to any framework rule that mirrors an external enforcer
+(permission allowlist entries, PreToolUse guards, prompt rules about what prompts).
+Derive the rule set from the enforcer's documented or observed behaviour (docs § Bash
+permission rules; the installed bundle's path-restricted table; a sandboxed native-oracle
+probe), record the evidence tier next to each rule, keep unverified shapes in a
+non-enforcing oracle manifest that the probe script reads, and enforce only commands whose
+operand grammar the guard actually models. Deterministic denial rules stay aligned with
+demonstrated native behaviour; advisory style rules may be broader. An allow entry with no
+demonstrated prompt it removes is removed. After a Claude Code upgrade re-verify that the
+bundle still contains `cd-compound-write`, `cd-compound-redirect`, `cd-git-compound`, then
+re-run `scripts/automation/permission-oracle.sh`.
+
+**Example (bad):** `- Bash(setsid *)  # detached engine prompts without it` — the engine
+is launched with `run_in_background`, never with setsid; 221 direct `setsid` calls
+succeeded before the entry existed.
+
+**Example (good):** `WRITE_COMMANDS = {"mkdir","touch","rm","rmdir","mv","cp"}  # bundle
+2.1.260 NH table, create/write class` with an evidence-tagged fixture per member.
+
+**Detection:** `python3 hooks/lib/read_path_hygiene.py --self-test` (evidence-tagged
+deny/allow/unknown matrix + oracle manifest); the acceptance run's `permission_request`
+event log. Regression test: `run-evals.sh` §2d.
diff --git a/incredible_auto_dev/.claude/anti-patterns/README.md b/incredible_auto_dev/.claude/anti-patterns/README.md
index 02ec6267..55868367 100644
--- a/incredible_auto_dev/.claude/anti-patterns/README.md
+++ b/incredible_auto_dev/.claude/anti-patterns/README.md
@@ -3,7 +3,7 @@
 One file per numbered entry, split from the former monolith (CTX-12) so a reader loads
 only what matches the situation: scan this index, open the matching `<NN>-<slug>.md`,
 nothing else. Numbering is FROZEN forever — files keep their original `## <N>. <title>`
-headings; the next new entry takes the next free number (28) as `<NN>-<slug>.md` plus a
+headings; the next new entry takes the next free number (33) as `<NN>-<slug>.md` plus a
 row here (maintenance protocol §2).
 
 | # | Entry | Applies when | Rule (one line) |
@@ -35,3 +35,8 @@ row here (maintenance protocol §2).
 | 25 | [25-self-justifying-governor-bypass.md](25-self-justifying-governor-bypass.md) | gates on agent behavior | A governor must validate against signals the governed agent cannot author; a self-written justification line is a suggestion, not a gate |
 | 26 | [26-per-scope-caps-no-machine-aggregate.md](26-per-scope-caps-no-machine-aggregate.md) | resource caps on shared hardware | Per-scope ceilings need a machine-level aggregate over a registry of live consumers, plus verification of every host assumption they rest on |
 | 27 | [27-software-guards-without-reset-reason.md](27-software-guards-without-reset-reason.md) | a machine resets, freezes, or reboots itself | Read the platform's own postmortem registers (reset reason, pstore, RAS) BEFORE building another software guard; "unreadable" is never "clean" |
+| 28 | [28-styled-verdict-cells-unparsed.md](28-styled-verdict-cells-unparsed.md) | parsing machine verdicts out of agent-written markdown | Match verdict cells tolerantly (bold/backticks/annotations); an unparseable cell is UNKNOWN, never an implicit PASS |
+| 29 | [29-plan-line-suppresses-lane.md](29-plan-line-suppresses-lane.md) | gating a verification lane on model-written plan metadata | Gate lanes on what the spec demands (named user journeys), not on a model-authored `Frontend Present:` line |
+| 30 | [30-process-identity-by-cmdline-substring.md](30-process-identity-by-cmdline-substring.md) | identifying a process from /proc or ps | Match the program (`comm` / `argv[0]` basename), never a substring of the whole cmdline — a path component is not an identity |
+| 31 | [31-rule-documented-where-nobody-reads-it.md](31-rule-documented-where-nobody-reads-it.md) | authoring rules for agents | A rule whose breach halts a run must ship in guaranteed-delivery context, not behind a pointer to another file |
+| 32 | [32-guard-modelled-on-prose-not-the-enforcer.md](32-guard-modelled-on-prose-not-the-enforcer.md) | writing any rule/allowlist that mirrors an external enforcer | Derive it from the enforcer's own rules, tag each rule with its evidence, keep unverified shapes non-enforcing and probed; delete entries with no demonstrated effect. |
diff --git a/incredible_auto_dev/.claude/architecture/README.md b/incredible_auto_dev/.claude/architecture/README.md
index e9b41126..b62b12a7 100644
--- a/incredible_auto_dev/.claude/architecture/README.md
+++ b/incredible_auto_dev/.claude/architecture/README.md
@@ -11,7 +11,7 @@ This directory contains the framework's architecture documentation. These docs d
 | [goal-mode.md](goal-mode.md) | Goal-mode architecture: outer loop, halt logic, decomposer + evaluator, state |
 | [agents.md](agents.md) | All 19 agents: role, model tier, inputs, outputs |
 | [artifacts.md](artifacts.md) | Complete artifact map with paths, producers, and consumers (phase + goal modes) |
-| [skills-and-hooks.md](skills-and-hooks.md) | 15 skills and 5 hooks: purpose, consuming agent, trigger |
+| [skills-and-hooks.md](skills-and-hooks.md) | 15 skills and 7 hooks: purpose, consuming agent, trigger |
 | [configuration.md](configuration.md) | All config surfaces: project-template, agent-models, security policy |
 | [adoption-guide.md](adoption-guide.md) | Step-by-step guide to adopting this framework in a project (phase and goal modes) |
 
diff --git a/incredible_auto_dev/.claude/architecture/adoption-guide.md b/incredible_auto_dev/.claude/architecture/adoption-guide.md
index 201060e8..614f456b 100644
--- a/incredible_auto_dev/.claude/architecture/adoption-guide.md
+++ b/incredible_auto_dev/.claude/architecture/adoption-guide.md
@@ -185,7 +185,7 @@ your-project/
     anti-patterns/                   # Failure modes (README index + per-entry files)
     agents/                          # agent definitions (rendered from agents/<name>/)
     skills/                          # 15 skills
-    hooks/                           # 5 hooks
+    hooks/                           # 7 hooks
     architecture/                    # Framework architecture docs (incl. goal-mode.md)
   scripts/automation/                # automation scripts (incl. run-goal.sh, goal-iter-lean.sh)
     lib/                             # quota-retry.sh, common.sh, telemetry.sh
diff --git a/incredible_auto_dev/.claude/architecture/skills-and-hooks.md b/incredible_auto_dev/.claude/architecture/skills-and-hooks.md
index ad3060ad..aba3d9c8 100644
--- a/incredible_auto_dev/.claude/architecture/skills-and-hooks.md
+++ b/incredible_auto_dev/.claude/architecture/skills-and-hooks.md
@@ -17,7 +17,7 @@ Skills are reusable instruction files that agents read during their workflow. Th
 | Phase Closure Gate | `phase-closure-gate.md` | phase-closure-auditor | Evaluate phase completion criteria (artifact existence, quality, consistency) |
 | Architecture Doc Updater | `architecture-doc-updater.md` | update-docs.sh | Update framework or project architecture docs when source files drift |
 
-## Hooks (5 total, in `.claude/hooks/`)
+## Hooks (7 total, in `.claude/hooks/`)
 
 Hooks are shell scripts triggered by Claude Code at specific lifecycle points. They are configured in `.claude/settings.json`.
 
@@ -26,6 +26,11 @@ Hooks are shell scripts triggered by Claude Code at specific lifecycle points. T
 - **Purpose:** Secondary safety layer for dangerous command patterns (rm -rf, dd, force-push main, credential reads). Primary protection is deny rules in `.claude/settings.json`.
 - **Behavior (SEC-7 two-mode):** argv mode (command as `$1` — test harness/Codex): GUARD lines on stderr + exit 1. Claude mode (PreToolUse JSON on stdin, `.tool_input.command`): emits `permissionDecision:"deny"` JSON on stdout with exit 0 — the settings wrapper is `|| true`, so the stdout JSON is the enforcement channel and the exit code carries no signal.
 
+### guard-read-path-hygiene.sh
+- **Trigger:** PreToolUse (Bash tool)
+- **Purpose:** Enforces `.claude/core.md` § "File Paths in Bash" so a dispatch never stalls on a human approval prompt it cannot get. Denies (a) a `cd` in a compound whose later segment is a CONTENT READ with a path argument, and (b) a recursive content search rooted at `.`, `~` or an absolute path. Both forms leave the search root unresolvable or unbounded, and since `Read(**/.env)` and friends are deny rules the checker cannot prove the read misses them — so it escalates to the human. Carve-outs match core.md: `cd` before a non-read (pytest/npm/tsc) and a piped read with no path argument stay legal, and redirect targets (`2>/dev/null`) are not read arguments.
+- **Behavior (SEC-7 two-mode):** same contract as `guard-dangerous-commands.sh`. Detection lives in `hooks/lib/read_path_hygiene.py`; the deny reason names the rewrite so the agent self-corrects instead of waiting. Fail-open on unparseable input or a missing `python3`.
+
 ### install-security-gate.sh
 - **Trigger:** PreToolUse (Bash tool)
 - **Purpose:** Supply-chain security gate. Intercepts `pip install`, `npm install`, `git clone`, and real (unquoted) `curl | bash` commands before execution.
@@ -48,3 +53,8 @@ Hooks are shell scripts triggered by Claude Code at specific lifecycle points. T
 - **Trigger:** Stop (session end)
 - **Purpose:** Reminds the operator to check artifacts if a phase run is in progress.
 - **Behavior:** Scans `runs/*/status.json` for in-progress phases and prints notices.
+
+### permission-request-log.sh
+- **Trigger:** PermissionRequest (Claude Code is about to need a human permission decision)
+- **Purpose:** Stage-1, log-only recorder for the permission-economics telemetry (TOKEN-12 extension) — records that a human prompt was about to happen so `lib/analyze_transcripts.py` can count them deterministically. A deny mode (stage 2) is a separate roadmap experiment (CAND-PERM-1), not implemented here.
+- **Behavior:** Pipes the PermissionRequest JSON on stdin into `hooks/lib/hook_events.py` (`--event permission_request`), which appends a privacy-safe event (suggestion count/types/hash only — never command or suggestion text). No stdout, no decision, exit 0 always — the native flow proceeds unchanged.
diff --git a/incredible_auto_dev/.claude/architecture/system-overview.md b/incredible_auto_dev/.claude/architecture/system-overview.md
index 3501190e..cc01935e 100644
--- a/incredible_auto_dev/.claude/architecture/system-overview.md
+++ b/incredible_auto_dev/.claude/architecture/system-overview.md
@@ -71,7 +71,7 @@ CLAUDE.md (constitution)
     |       |
     |       +-- read .claude/skills/*.md (15 skills)
     |
-    +-- .claude/hooks/*.sh (5 hooks, triggered by Claude Code)
+    +-- .claude/hooks/*.sh (7 hooks, triggered by Claude Code)
     |
     +-- scripts/automation/*.sh (16 scripts)
     |       |
diff --git a/incredible_auto_dev/.claude/core.md b/incredible_auto_dev/.claude/core.md
index 7e4eed2f..d942f01a 100644
--- a/incredible_auto_dev/.claude/core.md
+++ b/incredible_auto_dev/.claude/core.md
@@ -73,6 +73,58 @@ only removes temp dirs proven dead or stale (`.claude/anti-patterns/21-shared-tm
 
 ---
 
+## File Paths in Bash
+
+Run every command with paths the permission checker can resolve, so dispatches never
+stall waiting on a human:
+
+- NO `cd` before a read command. The Bash tool's working directory is already the
+  repo root and persists between calls. Write `grep -n "x" apps/backend/app/main.py`,
+  never `cd apps/backend && grep -n "x" app/main.py`.
+- Never root a recursive search at the repo root or an absolute machine path. Name
+  concrete subdirectories: `grep -rn PATTERN apps/backend/app/ apps/frontend/src/`,
+  not `grep -rn PATTERN .`.
+- Keep paths repo-relative. Absolute machine paths leak into committed handoffs.
+- `--exclude-dir` / `--include` do not help — the checker reads the path argument,
+  not the filter flags.
+- After a `cd` in the same command, NEVER read a relative path, mutate a file, redirect
+  output to a file, or run `git`. Claude Code hard-gates these shapes and NO allow rule can
+  pre-approve them: `cd` then `sed -i`, `cp`, `mv`, `rm`, `rmdir`, `mkdir` or `touch`
+  ("compound command contains cd with write operation — manual approval required to prevent
+  path resolution bypass"); `cd` then a redirect to any file but `/dev/null`; `cd` then `git`;
+  `cd` then a content read of a relative path (`grep`, `cat`, `find`, `sed -n`, and likewise
+  `rg`, `head`, `tail`, `wc`, `awk`). Edit files with the Edit/Write tools, or run from the
+  repo root with a repo-relative path: `sed -i 's/OLD/NEW/g' apps/backend/tests/test_x.py`,
+  never `cd apps/backend/tests && sed -i 's/OLD/NEW/g' test_x.py`. (`tee` and `install` are
+  not gated by this rule; they remain discouraged after a `cd` only because the target path is
+  unresolvable to a reader of the handoff. Prefer one `cd` per command.)
+- A backslash-newline continuation or a plain newline does not make a new command for the
+  checker: `cd x && \` on one line and `sed -i …` on the next is the gated shape.
+- Commands that must run from a subdirectory (pytest, npm, tsc) may still `cd`, as long as
+  nothing after the `cd` reads a relative path, mutates a file, redirects output to a file,
+  or runs git.
+
+Why: `Read(**/.env)` and similar are deny rules, and deny beats every allow. When the
+checker cannot prove a read misses them, it asks the human. Do not narrow those deny
+rules to silence the prompt — they keep real secrets out of agent context.
+
+ENFORCED, not advisory: `.claude/hooks/guard-read-path-hygiene.sh` (a PreToolUse Bash
+matcher) denies, with a message naming the rewrite: (A) `cd` then `grep`/`cat`/`find`/read-only
+`sed` with a relative path operand — the commands whose paths can be extracted exactly and
+that appear in observed stalls; (B) a recursive `grep`/`rg` rooted at `.` / `~` / `..` / an
+absolute path; (C1) `cd` then `sed -i`/`cp`/`mv`/`rm`/`rmdir`/`mkdir`/`touch`; (C2) `cd` then
+an output redirect to a file; (C3) `cd` then `git`. If it fires, rewrite the command as the
+message says — do not retry it verbatim and do not route around it. Legal by construction:
+`cd` before a non-read that does none of those (pytest/npm/tsc), a piped read with no path,
+option values (`grep -m 1`, `head -n 20`), `cd … && ls`, absolute paths after a `cd`, heredoc
+bodies, redirects to `/dev/null`. The bullets above recommend more than the guard enforces
+(`rg`/`head`/`tail`/`wc`/`awk` after a `cd` are style, pending native-oracle evidence). The
+guard is not a shell parser: loops, conditionals, subshells, command substitution and
+unparseable quoting are passed to Claude Code's own checker unchanged and logged — a stall
+there is evidence for a new rule, not a reason to widen the allowlist.
+
+---
+
 ## Visual Quality Checklist
 
 Every UI change MUST meet all of the following (applies when `Frontend Present: yes`):
diff --git a/incredible_auto_dev/.claude/hooks/guard-dangerous-commands.sh b/incredible_auto_dev/.claude/hooks/guard-dangerous-commands.sh
index f4769244..f8f892e3 100644
--- a/incredible_auto_dev/.claude/hooks/guard-dangerous-commands.sh
+++ b/incredible_auto_dev/.claude/hooks/guard-dangerous-commands.sh
@@ -72,7 +72,6 @@ DANGEROUS_PATTERNS=(
   "mkfs"
   "fdisk"
   "parted"
-  "> /dev/"
   # Secrets
   "cat ~/.ssh/id_rsa"
   "cat ~/.ssh/id_ed25519"
@@ -134,6 +133,9 @@ DANGEROUS_REGEXES=(
   "^(sudo )?chown .+ /(etc|usr|home|root|var|boot)"
   # docker run mounting host filesystem sensitive directories
   "docker run .*(-v|--volume) /(etc|usr|root|home|var|boot|lib|sys|proc)"
+  # Output redirection onto a device node. /dev/null, /dev/stdout, /dev/stderr and /dev/tty
+  # are the shell's ordinary sinks, not disk writes.
+  '>\s*/dev/(?!null\b|stdout\b|stderr\b|tty\b)'
 )
 
 for regex in "${DANGEROUS_REGEXES[@]}"; do
diff --git a/incredible_auto_dev/.claude/hooks/guard-read-path-hygiene.sh b/incredible_auto_dev/.claude/hooks/guard-read-path-hygiene.sh
new file mode 100755
index 00000000..85697993
--- /dev/null
+++ b/incredible_auto_dev/.claude/hooks/guard-read-path-hygiene.sh
@@ -0,0 +1,97 @@
+#!/usr/bin/env bash
+# Guard hook: read-path hygiene (PreToolUse / Bash).
+#
+# Turns `.claude/core.md` § "File Paths in Bash" from advisory prose into a
+# machine-enforced rule, so a dispatched agent never stalls the pipeline on a
+# human approval prompt it cannot get. Prose alone did not hold: goal session
+# contract-pack-v0 iter 1 stalled on
+# `cd .../contracts && grep -rn "book_snapshot" workstation_contracts/*.py`
+# with the rule already in core.md AND in the dispatch prompt's search-path note.
+#
+# Acceptance philosophy: deny only a shape PROVEN to stall approval -- an
+# observed incident, Claude Code's own hard-gate table, or documented core.md
+# behaviour -- and fail open on every shape this cannot parse or does not
+# recognize. Rules A (relative-path content read after `cd`), B (recursive
+# search rooted unbounded) and C1-C3 (write / output-redirect / git after a
+# `cd`) live in lib/read_path_hygiene.py; read its docstring for the full
+# breakdown and the unknown/fail-open reasons it prints to stderr.
+#
+# On match this DENIES with a rule-tagged corrective message -- e.g.
+# `guard-read-path-hygiene: [C1] ...` -- so the agent self-corrects on its next
+# turn instead of waiting for a human, and a log reader can group denials by
+# rule id without the command text ever being stored. The detection logic (and
+# its stdout header protocol) lives in lib/read_path_hygiene.py; the event
+# writer lives in lib/hook_events.py.
+#
+# I/O modes mirror guard-dangerous-commands.sh (SEC-7):
+#   argv mode  — command as $1 (run-evals, test harness, Codex): GUARD lines on
+#     stderr + exit 1 on match.
+#   stdin mode — the Claude Code PreToolUse protocol: JSON on stdin
+#     (.tool_input.command). On match emit permissionDecision "deny" JSON on
+#     stdout and exit 0 — the settings wrapper is `|| true`, so the exit code
+#     carries no signal on Claude and the stdout JSON is the enforcement channel.
+# Fail-open on missing/unparseable input or a missing python3.
+#
+# Privacy: every DENY, and every fail-open on syntax this module genuinely
+# cannot classify, is logged as one privacy-safe JSON event -- no raw command
+# text, no command hash, no raw permission-suggestion text -- to a
+# session-scoped file under $XDG_CACHE_HOME/iad/hook-events/<project-slug>/
+# (or $IAD_HOOK_EVENTS_FILE, if set); see lib/hook_events.py's docstring for
+# the event schema and the directory/file privacy modes (0700/0600). Logging
+# is best-effort and silent: it never blocks or fails the guard.
+
+CMD="${1:-}"
+INPUT_MODE="argv"
+if [ -z "$CMD" ] && [ ! -t 0 ]; then
+  _payload=$(cat 2>/dev/null || true)
+  if [ -n "$_payload" ]; then
+    if command -v jq >/dev/null 2>&1; then
+      CMD=$(printf '%s' "$_payload" | jq -r '.tool_input.command // empty' 2>/dev/null) || CMD=""
+    else
+      CMD=$(printf '%s' "$_payload" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command") or "")' 2>/dev/null) || CMD=""
+    fi
+    if [ -n "$CMD" ]; then INPUT_MODE="stdin"; fi
+  fi
+fi
+[ -z "$CMD" ] && exit 0
+command -v python3 >/dev/null 2>&1 || exit 0
+
+_HOOK_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
+_DETECTOR="$_HOOK_DIR/lib/read_path_hygiene.py"
+_EVENTS="$_HOOK_DIR/lib/hook_events.py"
+[ -f "$_DETECTOR" ] || exit 0
+_PAYLOAD_JSON="${_payload:-{\}}"      # "{}" in argv mode (tests, Codex)
+
+_event() {   # $1 event name, $2 extra JSON object — never fails, never prints to stdout
+  [ -f "$_EVENTS" ] || return 0
+  printf '%s' "$_PAYLOAD_JSON" | python3 "$_EVENTS" --hook guard-read-path-hygiene --event "$1" --extra "$2" >/dev/null 2>&1 || true
+}
+
+_deny() {   # $1 rule id, $2 header JSON, $3 message
+  echo "GUARD: [$1] $3" >&2
+  echo "GUARD: command was: $CMD" >&2
+  _event hygiene_deny "$2"
+  if [ "$INPUT_MODE" = "stdin" ]; then
+    _reason="guard-read-path-hygiene: [$1] $3"
+    if command -v jq >/dev/null 2>&1; then
+      jq -cn --arg r "$_reason" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
+    else
+      python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":sys.argv[1]}}, separators=(",",":")))' "$_reason"
+    fi
+    exit 0
+  fi
+  exit 1
+}
+
+_err_file="$(mktemp 2>/dev/null || echo /dev/null)"
+_verdict=$(printf '%s' "$CMD" | python3 "$_DETECTOR" 2>"$_err_file") || _verdict=""
+if [ -n "$_verdict" ]; then
+  _hdr="${_verdict%%$'\n'*}"
+  _msg="${_verdict#*$'\n'}"
+  _rule="${_hdr#*\"rule\":\"}"; _rule="${_rule%%\"*}"
+  _deny "$_rule" "$_hdr" "$_msg"
+fi
+_fo="$(grep -o 'FAILOPEN reason=[^ ]*' "$_err_file" 2>/dev/null | head -1 | cut -d= -f2)"
+[ "$_err_file" != /dev/null ] && rm -f "$_err_file" 2>/dev/null
+[ -n "$_fo" ] && _event hygiene_fail_open "{\"reason\":\"$_fo\"}"
+exit 0
diff --git a/incredible_auto_dev/.claude/hooks/lib/hook_events.py b/incredible_auto_dev/.claude/hooks/lib/hook_events.py
new file mode 100644
index 00000000..cadb9aeb
--- /dev/null
+++ b/incredible_auto_dev/.claude/hooks/lib/hook_events.py
@@ -0,0 +1,201 @@
+#!/usr/bin/env python3
+"""Append one JSON event line for a Claude Code hook decision.
+
+Session-scoped: <cache>/iad/hook-events/<project-slug>/<session-id>.jsonl — one session per
+file. Private: directories 0700, files 0600 (explicit modes, not the caller's umask; existing
+wider modes are tightened best-effort — only inside hook-events/). Append-safe: one fully
+built line per write on an O_APPEND descriptor under flock, so parallel subagent hooks never
+interleave rows. Privacy-safe: never stores raw command text, command hashes or raw
+permission suggestions; IAD_HOOK_EVENTS_RAW=1 is the explicit default-off diagnostic that
+adds cmd_raw. Never fails the caller: any error exits 0 silently.
+    python3 hook_events.py --hook <name> --event <event> [--extra '<json object>']   (hook input JSON on stdin)
+    python3 hook_events.py --self-test
+"""
+import datetime
+import fcntl
+import hashlib
+import json
+import os
+import re
+import stat
+import sys
+
+KEEP = ("session_id", "agent_id", "agent_type", "tool_use_id", "tool_name", "permission_mode")
+DIR_MODE, FILE_MODE = 0o700, 0o600
+
+
+def events_file(session_id):
+    explicit = os.environ.get("IAD_HOOK_EVENTS_FILE")
+    if explicit:
+        return explicit
+    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
+    slug = re.sub(r"[^A-Za-z0-9]", "-", root)
+    sid = re.sub(r"[^A-Za-z0-9._-]", "", session_id or "") or "_no-session"
+    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
+    return os.path.join(base, "iad", "hook-events", slug, sid + ".jsonl")
+
+
+def _private_dir(path):
+    """mkdir -p with 0700; tighten an existing wider dir (best effort)."""
+    os.makedirs(path, mode=DIR_MODE, exist_ok=True)
+    try:
+        if stat.S_IMODE(os.stat(path).st_mode) != DIR_MODE:
+            os.chmod(path, DIR_MODE)
+    except OSError:
+        pass
+
+
+def sha16(text):
+    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]
+
+
+def build_event(args, payload):
+    try:
+        extra = json.loads(args.get("--extra") or "{}")
+    except ValueError:
+        extra = {}
+    event = {"ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
+             "event": args.get("--event", ""), "hook": args.get("--hook", "")}
+    for key in KEEP:
+        event[key] = str(payload.get(key, "") or "")
+    if event["event"] == "permission_request":
+        sugg = payload.get("permission_suggestions") or []
+        event["suggestion_count"] = len(sugg)
+        event["suggestion_types"] = sorted({str(s.get("type", "?")) for s in sugg if isinstance(s, dict)})
+        event["suggestions_sha"] = sha16(json.dumps(sugg, sort_keys=True)) if sugg else ""
+    event.update(extra)
+    if os.environ.get("IAD_HOOK_EVENTS_RAW") == "1":      # explicit, default-off diagnostic
+        tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
+        event["cmd_raw"] = str(tool_input.get("command", "") or "")[:2000]
+    return event
+
+
+def append_event(path, event):
+    parent = os.path.dirname(path)
+    if not os.environ.get("IAD_HOOK_EVENTS_FILE"):
+        base = os.path.dirname(parent)               # …/hook-events
+        _private_dir(base)
+        _private_dir(parent)                          # …/hook-events/<slug>
+    else:
+        os.makedirs(parent, exist_ok=True)
+    line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
+    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, FILE_MODE)
+    try:
+        if stat.S_IMODE(os.fstat(fd).st_mode) != FILE_MODE:
+            try:
+                os.fchmod(fd, FILE_MODE)
+            except OSError:
+                pass
+        fcntl.flock(fd, fcntl.LOCK_EX)
+        try:
+            os.write(fd, line.encode("utf-8"))
+        finally:
+            fcntl.flock(fd, fcntl.LOCK_UN)
+    finally:
+        os.close(fd)
+
+
+def main():
+    args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
+    try:
+        payload = json.load(sys.stdin)
+    except Exception:
+        payload = {}
+    if not isinstance(payload, dict):
+        payload = {}
+    event = build_event(args, payload)
+    append_event(events_file(event["session_id"]), event)
+
+
+def _self_test():
+    import subprocess
+    import tempfile
+    fails = []
+    with tempfile.TemporaryDirectory() as tmp:
+        env = dict(os.environ, XDG_CACHE_HOME=tmp, CLAUDE_PROJECT_DIR="/home/u/Git/incredible_auto_dev")
+        env.pop("IAD_HOOK_EVENTS_FILE", None)
+        env.pop("IAD_HOOK_EVENTS_RAW", None)
+        payload = json.dumps({"session_id": "sess-1", "agent_id": "a1", "agent_type": "developer",
+                              "tool_use_id": "t1", "tool_name": "Bash", "permission_mode": "auto",
+                              "tool_input": {"command": "cd apps && sed -i s/a/b/ x.py SECRET=1"},
+                              "permission_suggestions": [{"type": "addRules", "rules": [{"ruleContent": "sed *"}]}]})
+        run = lambda ev: subprocess.run([sys.executable, __file__, "--hook", "t", "--event", ev, "--extra", '{"rule":"C1"}'],
+                                        input=payload, text=True, env=env, capture_output=True)
+        r = run("hygiene_deny")
+        f = os.path.join(tmp, "iad", "hook-events", "-home-u-Git-incredible-auto-dev", "sess-1.jsonl")
+        if r.returncode != 0 or r.stdout:
+            fails.append("writer must exit 0 with empty stdout: rc=%s out=%r" % (r.returncode, r.stdout))
+        if not os.path.isfile(f):
+            fails.append("session file not created at %s" % f)
+        else:
+            for d in (os.path.dirname(os.path.dirname(f)), os.path.dirname(f)):
+                if stat.S_IMODE(os.stat(d).st_mode) != DIR_MODE:
+                    fails.append("dir mode %o != 0700 for %s" % (stat.S_IMODE(os.stat(d).st_mode), d))
+            if stat.S_IMODE(os.stat(f).st_mode) != FILE_MODE:
+                fails.append("file mode %o != 0600" % stat.S_IMODE(os.stat(f).st_mode))
+            row = json.loads(open(f, encoding="utf-8").read().splitlines()[0])
+            for forbidden in ("cmd_sha", "cmd_raw"):
+                if forbidden in row:
+                    fails.append("default schema must not contain %s" % forbidden)
+            if "SECRET" in json.dumps(row) or "ruleContent" in json.dumps(row):
+                fails.append("event leaks command or suggestion text: %r" % row)
+            if row.get("rule") != "C1" or row.get("agent_type") != "developer":
+                fails.append("extra/attribution fields missing: %r" % row)
+        run("permission_request")
+        row = json.loads(open(f, encoding="utf-8").read().splitlines()[1])
+        if row.get("suggestion_count") != 1 or row.get("suggestion_types") != ["addRules"] or not row.get("suggestions_sha"):
+            fails.append("permission_request summary fields wrong: %r" % row)
+        # widened file/dir get tightened best-effort
+        os.chmod(f, 0o644)
+        os.chmod(os.path.dirname(f), 0o755)
+        run("hygiene_fail_open")
+        if stat.S_IMODE(os.stat(f).st_mode) != FILE_MODE or stat.S_IMODE(os.stat(os.path.dirname(f)).st_mode) != DIR_MODE:
+            fails.append("existing wider modes were not tightened")
+        # concurrent appends: 8 processes x 50 events, every row must parse, none interleaved
+        procs = [subprocess.Popen([sys.executable, __file__, "--stress", "50", "--event", "hygiene_deny"],
+                                  stdin=subprocess.PIPE, text=True, env=env) for _ in range(8)]
+        for p in procs:
+            p.communicate(payload)
+        lines = open(f, encoding="utf-8").read().splitlines()
+        bad = sum(1 for l in lines if not l.startswith("{") or not l.endswith("}") or _bad_json(l))
+        if len(lines) != 3 + 400 or bad:
+            fails.append("concurrent append: %d lines (expected 403), %d malformed" % (len(lines), bad))
+        # explicit override + no-session fallback
+        env2 = dict(env, IAD_HOOK_EVENTS_FILE=os.path.join(tmp, "override.jsonl"))
+        subprocess.run([sys.executable, __file__, "--hook", "t", "--event", "hygiene_deny"], input="{}", text=True, env=env2)
+        if not os.path.isfile(os.path.join(tmp, "override.jsonl")):
+            fails.append("IAD_HOOK_EVENTS_FILE override not honoured")
+        subprocess.run([sys.executable, __file__, "--hook", "t", "--event", "hygiene_deny"], input="{}", text=True, env=env)
+        if not os.path.isfile(os.path.join(tmp, "iad", "hook-events", "-home-u-Git-incredible-auto-dev", "_no-session.jsonl")):
+            fails.append("_no-session fallback file not created")
+    for x in fails:
+        print("FAIL " + x)
+    print("hook_events self-test: %d failures" % len(fails))
+    return 1 if fails else 0
+
+
+def _bad_json(line):
+    try:
+        json.loads(line)
+        return False
+    except ValueError:
+        return True
+
+
+if __name__ == "__main__":
+    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
+        sys.exit(_self_test())
+    if len(sys.argv) > 2 and sys.argv[1] == "--stress":       # self-test helper: N sequential events
+        try:
+            payload = json.load(sys.stdin)
+            args = dict(zip(sys.argv[3::2], sys.argv[4::2]))
+            for _ in range(int(sys.argv[2])):
+                append_event(events_file(payload.get("session_id", "")), build_event(args, payload))
+        except Exception:
+            pass
+        sys.exit(0)
+    try:
+        main()
+    except Exception:
+        pass
+    sys.exit(0)
diff --git a/incredible_auto_dev/.claude/hooks/lib/read_path_hygiene.py b/incredible_auto_dev/.claude/hooks/lib/read_path_hygiene.py
new file mode 100644
index 00000000..b647ce77
--- /dev/null
+++ b/incredible_auto_dev/.claude/hooks/lib/read_path_hygiene.py
@@ -0,0 +1,724 @@
+#!/usr/bin/env python3
+"""Detect Bash command shapes that would stall a headless dispatch on a human
+approval prompt, and deny them with a corrective message before they run.
+
+Acceptance philosophy, in one sentence: DENY a shape only when it is PROVEN --
+by an observed incident, by Claude Code's own hard-gate table, or by
+documented `.claude/core.md` behaviour -- to stall on a human, and FAIL OPEN
+on every shape this module cannot parse or does not recognize, because a
+false ALLOW merely defers to the native permission checker (where the
+decision belongs by default) while a false DENY blocks real work.
+
+Why the approval prompt happens at all: `Read(**/.env)`, `Read(~/.ssh/**)` and
+friends are DENY rules, and deny beats every allow. Before a read the
+permission checker must prove the read cannot touch a denied path. It cannot
+prove that when the search root is unresolvable (a `cd` first) or unbounded
+(`.`, an absolute path), so it escalates to a human -- a hang inside a
+headless or pump dispatch. Narrowing the deny rules to silence it is
+explicitly forbidden by core.md; they keep real secrets out of agent context.
+
+Rules -- A and C1-C3 fire only on a segment AFTER a `cd` in the same command;
+B fires regardless of `cd` (an unbounded root is unbounded either way):
+
+  A  -- the hard-enforced content-read set (grep/egrep/fgrep, cat, find,
+        read-only sed -n) carries a RELATIVE path operand. Evidence tier:
+        observed (E3 -- the goal-session contract-pack-v0 iter 1 stall) plus
+        the per-command operand tables below; rg/head/tail/wc/awk/... are
+        deliberately left oracle-gated, not enforced.
+  B  -- a recursive content search (grep/egrep/fgrep -r, rg always) is rooted
+        at `.`, `./`, `..`, `~` or an absolute path -- unbounded regardless of
+        `cd`. Evidence tier: observed regressions (b422b6e, b6ae4d2).
+  C1 -- a write/create-class command (sed -i, cp, mv, rm, rmdir, mkdir, touch)
+        runs after the `cd`. Evidence tier: Claude Code's own hard gate
+        ("compound command contains cd with write operation ... manual
+        approval required") -- no allow rule can ever pre-approve this shape,
+        so it is enforced unconditionally. Also observed (E2 verbatim).
+  C2 -- an output redirect (`>`, `>>`, `&>`, ...) to a real file (not
+        /dev/null) follows the `cd`. Evidence tier: Claude Code's own hard
+        gate ("compound command contains cd with output redirection ...
+        manual approval required"), documented in core.md.
+  C3 -- `git` runs after the `cd`. Evidence tier: documented in core.md (git
+        run from a changed directory can execute that directory's hooks).
+
+Unknown / fail-open: a command this module cannot safely reason about passes
+through UNCHANGED to the native checker -- never denied on a guess. One
+stderr line names why: `FAILOPEN reason=tokenize` (shell syntax the tokenizer
+rejects, e.g. an unbalanced quote), `FAILOPEN reason=complex:<kind>` (control
+flow, subshell/brace/command-substitution/process-substitution grouping, or a
+backtick substitution -- `<kind>` is `control-flow`, `grouping` or
+`backtick`), or `FAILOPEN reason=exception:<ClassName>` (an unexpected bug in
+this module itself, caught so the guard never becomes the hang it prevents).
+The one exception is `coarse_check()`: when the tokenizer itself fails, a
+command still matching an unmistakable `cd ... <write word>` shape is denied
+as rule "coarse" instead of failing open, because that shape does not need a
+clean parse to be certain.
+
+Header protocol (read by guard-read-path-hygiene.sh): on a DENY, stdout line 1
+is a single-line JSON header -- `{"rule": "...", "command_class": "...",
+"has_cd": bool, "has_output_redirect": bool}` -- followed by the corrective
+message (everything after the first newline). Nothing is written to stdout
+when the command is clean or unknown.
+
+`--self-test` runs the fixture suite at the bottom of this file and exits
+0/1. `--oracle-manifest` prints one `id<TAB>command` line per ORACLE_MANIFEST
+case (`{SB}` = sandbox root placeholder) -- the single source consumed by
+scripts/automation/permission-oracle.sh, so the native-checker probe list and
+this module's pinned expectations can never drift apart.
+"""
+
+import json
+import re
+import shlex
+import sys
+from collections import namedtuple
+
+# Prefixes the native checker strips before matching (docs § Wrappers) plus sudo/exec/!.
+WRAPPERS = {"sudo", "env", "nohup", "nice", "command", "builtin", "exec", "time", "stdbuf", "!"}
+# The checker's create/write-class commands (bundle NH table). tee/install are absent on purpose.
+WRITE_COMMANDS = {"mkdir", "touch", "rm", "rmdir", "mv", "cp"}
+# Syntax the guard deliberately does not interpret (D3): fail open, log, let the checker decide.
+CONTROL_FLOW = {"for", "while", "until", "if", "case", "select", "function", "eval"}
+GROUPING = {"(", ")", "{", "}"}
+PUNCT = "();<>|&\n"                      # shlex punctuation + newline (a separator in the shell)
+SEPARATORS = {";", "&&", "||", "|", "&", "|&", "\n"}
+OUTPUT_REDIRECTS = {">", ">>", ">|", "&>", "&>>"}
+OTHER_REDIRECTS = {">&", "<", "<<<", "<&", "<>"}
+SAFE_REDIRECT_TARGETS = {"/dev/" + "null"}
+UNRESOLVABLE_ROOTS = {".", "./", "..", "../", "~", "~/"}
+COARSE_CD = re.compile(r"(?:^|[;&|\n]\s*)cd\s")
+COARSE_WRITE = re.compile(r"(?:^|[;&|\s])(?:sed\s+(?:-[A-Za-z]*i|--in-place)|rm|rmdir|mv|cp|mkdir|touch)\s")
+
+Verdict = namedtuple("Verdict", "rule command_class has_cd has_output_redirect message")
+RULE_DOC = "See .claude/core.md -> File Paths in Bash."
+MSG = {
+    "A": ("`%s` reads a relative path in a command that also runs `cd`, so the permission checker "
+          "cannot resolve the file and MUST ask a human -- which hangs this dispatch. Drop the `cd` "
+          "and use a repo-relative path from the repo root (e.g. `grep -n \"x\" apps/backend/app/main.py`, "
+          "not `cd apps/backend && grep -n \"x\" app/main.py`). `cd` stays legal for a command that "
+          "needs the cwd and reads no path, writes nothing, redirects nothing and does not run git "
+          "(pytest, npm, tsc). " + RULE_DOC),
+    "B": ("`%s` roots a recursive search at `%s`. An unbounded root cannot be proven to miss the "
+          "`Read(**/.env)` deny rules, so the checker MUST ask a human -- which hangs this dispatch. "
+          "Name concrete repo-relative subdirectories instead (e.g. `grep -rn PATTERN apps/backend/app/ "
+          "apps/frontend/src/`). `--include`/`--exclude-dir` do NOT help: the checker reads the path "
+          "argument, not the filter flags. " + RULE_DOC),
+    "C1": ("`%s` mutates a file after a `cd` in the same command. Claude Code hard-gates that shape "
+           "('compound command contains cd with write operation - manual approval required'); NO allow "
+           "rule can pre-approve it, so this dispatch would hang on a human. Edit files with the "
+           "Edit/Write tools, or drop the `cd` and use a repo-relative path from the repo root (e.g. "
+           "`sed -i 's/OLD/NEW/g' apps/backend/tests/test_x.py`, not `cd apps/backend/tests && sed -i "
+           "'s/OLD/NEW/g' test_x.py`). " + RULE_DOC),
+    "C2": ("The output redirect to `%s` follows a `cd` in the same command. Claude Code hard-gates "
+           "that shape ('compound command contains cd with output redirection - manual approval "
+           "required'), so this dispatch would hang on a human. Redirect to /dev/null, or drop the "
+           "`cd` and name the file repo-relative from the repo root (e.g. `pytest -q apps/backend > "
+           "apps/backend/test-output.log`), or capture the output with the Write tool. " + RULE_DOC),
+    "C3": ("`git` after a `cd` prompts a human (Claude Code treats git run from a changed directory "
+           "as able to execute that directory's hooks), which hangs this dispatch. Run git from the "
+           "repo root: `git status`, `git -C apps/backend log -3`, `git add apps/backend/app/x.py`. "
+           + RULE_DOC),
+}
+
+
+# ── Per-command operand extraction (tiny tables; not a general getopt) ─────────
+def operand_paths(args, value_short, value_long, pattern_short, pattern_long):
+    """Operands of a grep/sed/rg-style command line. Options in value_short/value_long consume a
+    value (attached or the next token); the first operand is the pattern/script unless one of
+    the pattern_* options supplied it. Table-driven per command; nothing else is interpreted."""
+    paths, i, pattern_given, opts_done = [], 0, False, False
+    while i < len(args):
+        a = args[i]
+        i += 1
+        if a == "-":
+            continue                                    # stdin marker, never a path (like cat_paths)
+        if opts_done or not a.startswith("-"):
+            paths.append(a)
+            continue
+        if a == "--":
+            opts_done = True
+            continue
+        if a.startswith("--"):
+            name = a.split("=", 1)[0]
+            pattern_given = pattern_given or name in pattern_long
+            if "=" not in a and name in value_long:
+                i += 1                                  # separate value token
+            continue
+        for j, ch in enumerate(a[1:], 1):
+            if ch in value_short:
+                pattern_given = pattern_given or ch in pattern_short
+                if j == len(a) - 1:
+                    i += 1                              # value is the next token
+                break                                   # otherwise the rest of the cluster is the value
+    if not pattern_given and paths:
+        paths = paths[1:]
+    return paths
+
+
+GREP_VALUE_SHORT = set("efmABCdD")
+GREP_VALUE_LONG = {"--regexp", "--file", "--max-count", "--after-context", "--before-context", "--context",
+                   "--include", "--exclude", "--exclude-dir", "--exclude-from", "--label", "--devices",
+                   "--directories", "--binary-files", "--color", "--colour", "--group-separator"}
+SED_VALUE_SHORT = set("efl")
+SED_VALUE_LONG = {"--expression", "--file", "--line-length"}
+RG_VALUE_SHORT = set("efgtTmABCMjdrE")
+RG_VALUE_LONG = {"--regexp", "--file", "--glob", "--iglob", "--type", "--type-not", "--type-add", "--max-count",
+                 "--after-context", "--before-context", "--context", "--max-columns", "--max-depth",
+                 "--max-filesize", "--threads", "--replace", "--encoding", "--color", "--colors", "--sort",
+                 "--sortr", "--context-separator", "--path-separator", "--pre", "--pre-glob", "--ignore-file",
+                 "--engine"}
+
+
+def grep_paths(args):
+    return operand_paths(args, GREP_VALUE_SHORT, GREP_VALUE_LONG, set("ef"), {"--regexp", "--file"})
+
+
+def sed_paths(args):
+    return operand_paths(args, SED_VALUE_SHORT, SED_VALUE_LONG, set("ef"), {"--expression", "--file"})
+
+
+def rg_paths(args):
+    return operand_paths(args, RG_VALUE_SHORT, RG_VALUE_LONG, set("ef"), {"--regexp", "--file"})
+
+
+def cat_paths(args):
+    return [a for a in args if a != "-" and not a.startswith("-")]
+
+
+def find_paths(args):
+    """Explicit starting points only: leading operands after -H/-L/-P/-Olevel/-D opts and before
+    the first expression. The implicit `.` when none is given is oracle-gated (O19), not enforced."""
+    i = 0
+    while i < len(args) and (args[i] in ("-H", "-L", "-P") or args[i].startswith("-O")):
+        i += 1
+    if i < len(args) and args[i] == "-D":
+        i += 2
+    paths = []
+    while i < len(args) and not args[i].startswith("-") and args[i] not in ("(", "!"):
+        paths.append(args[i])
+        i += 1
+    return paths
+
+
+# Rule A hard set: content-read commands whose operand grammar is simple enough to extract
+# deterministically AND that appear in observed stalls / the native read table (D2). `ls`
+# stays out (docs: `cd packages/api && ls` runs without a prompt); rg/head/tail/wc/awk/…
+# are oracle-gated, not enforced.
+READ_EXTRACTORS = {"grep": grep_paths, "egrep": grep_paths, "fgrep": grep_paths,
+                   "cat": cat_paths, "find": find_paths, "sed": sed_paths}
+# Rule B recursive searchers (the shipped b422b6e set) with their root extractors.
+ROOT_EXTRACTORS = {"grep": grep_paths, "egrep": grep_paths, "fgrep": grep_paths, "rg": rg_paths}
+ALWAYS_RECURSIVE = {"rg"}
+
+
+def normalize(cmd):
+    """Fold backslash-newline continuations (the shell joins them into one line), then blank
+    `#`-comments to end-of-line so they never reach the tokenizer."""
+    cmd = cmd.replace("\\\r\n", " ").replace("\\\n", " ")
+    return _strip_line_comments(cmd)
+
+
+def _strip_line_comments(cmd):
+    """Blank a `#...` comment to end-of-line, but keep the `\\n` itself. Only a `#` that
+    starts a word (preceded by whitespace or the start of the string) outside single/double
+    quotes is a comment marker -- `grep -n '#include' f` and `echo 'a#b' # trailing` must not
+    lose their quoted `#`. shlex's own default `commenters='#'` handling is not reused here
+    because it calls `instream.readline()`, which consumes the trailing newline TOO and
+    silently merges the next shell command into the commented-out segment (F1)."""
+    out = []
+    quote = None                      # None, "'" or '"'
+    i, n = 0, len(cmd)
+    while i < n:
+        ch = cmd[i]
+        if quote:
+            out.append(ch)
+            if quote == '"' and ch == "\\" and i + 1 < n:
+                out.append(cmd[i + 1])
+                i += 2
+                continue
+            if ch == quote:
+                quote = None
+            i += 1
+            continue
+        if ch in "'\"":
+            quote = ch
+            out.append(ch)
+            i += 1
+            continue
+        if ch == "#" and (i == 0 or cmd[i - 1] in " \t\r\n"):
+            while i < n and cmd[i] != "\n":
+                i += 1
+            continue
+        out.append(ch)
+        i += 1
+    return "".join(out)
+
+
+def tokenize(cmd):
+    lexer = shlex.shlex(cmd, posix=True, punctuation_chars=PUNCT)
+    lexer.whitespace = " \t\r"          # newline is a separator token, not whitespace
+    lexer.whitespace_split = True
+    lexer.commenters = ""               # comments are pre-stripped by _strip_line_comments();
+                                         # shlex must never again consume a newline via '#'
+    out = []
+    for tok in lexer:
+        if "\n" in tok and set(tok) <= set(PUNCT):   # shlex glues "&&\n" — split newlines back out
+            out.extend(re.findall(r"\n|[^\n]+", tok))
+        else:
+            out.append(tok)
+    return out
+
+
+def drop_heredocs(tokens):
+    """Remove `<<`/`<<-`, the delimiter and the body lines: the body is data, never commands."""
+    out, i = [], 0
+    while i < len(tokens):
+        tok = tokens[i]
+        if tok in ("<<", "<<-") and i + 1 < len(tokens):
+            if tokens[i + 1] == "-" and i + 2 < len(tokens):
+                delim = tokens[i + 2]          # `<<- DELIM` (space form): tokenizer splits the `-`
+                i += 3
+            else:
+                delim = tokens[i + 1].lstrip("-")   # `<<-DELIM` / `<< DELIM` (attached / no dash)
+                i += 2
+            while i < len(tokens) and tokens[i] != "\n":   # the rest of the command line stays
+                out.append(tokens[i])
+                i += 1
+            i += 1
+            while i < len(tokens):
+                if tokens[i] == delim and (i + 1 == len(tokens) or tokens[i + 1] == "\n"):
+                    i += 1
+                    break
+                i += 1
+            continue
+        out.append(tok)
+        i += 1
+    return out
+
+
+def split_redirects(tokens):
+    """Drop redirect operators (+ fd digit) and targets; return (tokens, [(position, target)])
+    for OUTPUT redirects, position = index in the returned token stream."""
+    out, targets, i = [], [], 0
+    while i < len(tokens):
+        tok = tokens[i]
+        if tok in OUTPUT_REDIRECTS or tok in OTHER_REDIRECTS:
+            if out and out[-1].isdigit():
+                out.pop()
+            target = tokens[i + 1] if i + 1 < len(tokens) else ""
+            if tok in OUTPUT_REDIRECTS and target and not target.startswith("&"):
+                targets.append((len(out), target))
+            i += 2
+            continue
+        out.append(tok)
+        i += 1
+    return out, targets
+
+
+def split_segments(tokens):
+    """[(start_index, [tokens])] split on shell separators."""
+    segments, current, start = [], [], 0
+    for i, tok in enumerate(tokens):
+        if tok in SEPARATORS:
+            if current:
+                segments.append((start, current))
+            current, start = [], i + 1
+        else:
+            current.append(tok)
+    if current:
+        segments.append((start, current))
+    return segments
+
+
+def head_of(segment):
+    """(command name, argument tokens) with env assignments and wrappers stripped."""
+    i = 0
+    while i < len(segment):
+        tok = segment[i]
+        if "=" in tok and not tok.startswith("-") and tok.split("=", 1)[0].isidentifier():
+            i += 1
+            continue
+        if tok in WRAPPERS:
+            i += 1
+            continue
+        if tok == "timeout" and i + 1 < len(segment):
+            i += 2
+            continue
+        break
+    if i >= len(segment):
+        return None, []
+    return segment[i].rsplit("/", 1)[-1], segment[i + 1:]
+
+
+def complex_syntax(tokens):
+    """Name the first construct the guard does not interpret, or None."""
+    for tok in tokens:
+        if tok in GROUPING:
+            return "grouping"            # subshell, brace group, $( ), <( ), >( ) all
+                                          # tokenize into single "(" or ")" tokens; (( / )) from
+                                          # arithmetic expansion are ordinary tokens — arithmetic is not
+                                          # command substitution
+        if "`" in tok:
+            return "backtick"
+    for _start, seg in split_segments(tokens):
+        name, _ = head_of(seg)
+        if name in CONTROL_FLOW:
+            return "control-flow"
+    return None
+
+
+def sed_writes(args):
+    for a in args:
+        if a == "--":
+            break
+        if a.startswith("--in-place"):
+            return True
+        if a.startswith("-") and not a.startswith("--"):
+            for ch in a[1:]:
+                if ch == "i":
+                    return True
+                if ch in "efl":          # value-taking short option: the rest of the cluster
+                    break                # is that option's value, not more flag letters
+    return False
+
+
+def is_relative(path):
+    return not (path.startswith("/") or path.startswith("~"))
+
+
+def has_recursive_flag(args):
+    for a in args:
+        if not a.startswith("-"):
+            continue
+        if a.startswith("--"):
+            if a in ("--recursive", "--dereference-recursive"):
+                return True
... [diff_bound] incredible_auto_dev/.claude/hooks/lib/read_path_hygiene.py: 330 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/.claude/hooks/permission-request-log.sh b/incredible_auto_dev/.claude/hooks/permission-request-log.sh
new file mode 100644
index 00000000..cdf76165
--- /dev/null
+++ b/incredible_auto_dev/.claude/hooks/permission-request-log.sh
@@ -0,0 +1,16 @@
+#!/usr/bin/env bash
+# PermissionRequest recorder — STAGE 1, LOG-ONLY. Fires when Claude Code is about to
+# need a permission decision from a human: the exact event the autonomous pipeline can
+# never answer. It emits NO decision (stdout stays empty; the native flow proceeds
+# unchanged) and only appends a privacy-safe permission_request event (Task 2 schema:
+# suggestion count/types/hash — never command or suggestion text) so
+# lib/analyze_transcripts.py can count human prompts deterministically. A deny mode is a
+# separate roadmap experiment (CAND-PERM-1 stage 2), not implemented here. Exit 0 always.
+[ -t 0 ] && exit 0
+_payload=$(cat 2>/dev/null || true)
+[ -n "$_payload" ] || exit 0
+_HOOK_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
+[ -f "$_HOOK_DIR/lib/hook_events.py" ] || exit 0
+command -v python3 >/dev/null 2>&1 || exit 0
+printf '%s' "$_payload" | python3 "$_HOOK_DIR/lib/hook_events.py" --hook permission-request-log --event permission_request >/dev/null 2>&1 || true
+exit 0
diff --git a/incredible_auto_dev/.claude/settings.json b/incredible_auto_dev/.claude/settings.json
index 6b806499..b2a32125 100644
--- a/incredible_auto_dev/.claude/settings.json
+++ b/incredible_auto_dev/.claude/settings.json
@@ -51,6 +51,12 @@
       "Bash(./scripts/*)",
       "Bash(scripts/*)",
       "Bash(bash .claude/*)",
+      "Bash(setsid *)",
+      "Bash(nohup *)",
+      "Bash(disown)",
+      "Bash(disown *)",
+      "Bash(google-chrome *)",
+      "Bash(/usr/bin/google-chrome *)",
       "Bash(for *)",
       "Bash(while *)",
       "Bash(until *)",
@@ -362,6 +368,15 @@
             "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/guard-dangerous-commands.sh\" 2>/dev/null || true"
           }
         ]
+      },
+      {
+        "matcher": "Bash",
+        "hooks": [
+          {
+            "type": "command",
+            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/guard-read-path-hygiene.sh\" 2>/dev/null || true"
+          }
+        ]
       }
     ],
     "PostToolUse": [
@@ -394,6 +409,17 @@
           }
         ]
       }
+    ],
+    "PermissionRequest": [
+      {
+        "matcher": ".*",
+        "hooks": [
+          {
+            "type": "command",
+            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/permission-request-log.sh\" 2>/dev/null || true"
+          }
+        ]
+      }
     ]
   }
 }
diff --git a/incredible_auto_dev/.claude/settings.local.json.example b/incredible_auto_dev/.claude/settings.local.json.example
index 5667f32b..d5271d91 100644
--- a/incredible_auto_dev/.claude/settings.local.json.example
+++ b/incredible_auto_dev/.claude/settings.local.json.example
@@ -1,6 +1,6 @@
 {
   "_comment": "Local overrides for .claude/settings.json. Copy to settings.local.json (not committed).",
-  "_doc": "Add machine-specific permissions here (this file is gitignored). Shell control flow (for/do/...), common dev binaries, venv/pytest paths, and scoped rm -rf live in the SHARED policy now - edit policy/permissions.yaml and re-render instead of adding them here. Broad curl belongs in the user-global ~/.claude/settings.json (already set on the reference machine).",
+  "_doc": "Add machine-specific permissions here (this file is gitignored). Shell control flow (for/do/...), common dev binaries, venv/pytest paths, and scoped rm -rf live in the SHARED policy now - edit policy/permissions.yaml and re-render instead of adding them here. Broad curl belongs in the user-global ~/.claude/settings.json (already set on the reference machine). Operator-specific grants (a personal headless-Chrome debugging command; exact-match rules for detached launch strings, since prefix rules cannot approve `setsid`) belong in this gitignored local file, never in policy/permissions.yaml.",
 
   "permissions": {
     "allow": [
diff --git a/incredible_auto_dev/docs/goal-mode-telemetry.md b/incredible_auto_dev/docs/goal-mode-telemetry.md
index a4dd378c..20212e23 100644
--- a/incredible_auto_dev/docs/goal-mode-telemetry.md
+++ b/incredible_auto_dev/docs/goal-mode-telemetry.md
@@ -324,3 +324,86 @@ Recorded PRE (2026-09-01, tapeology, largest session): pump 1,751 turns, 890M ca
 (~508K/turn), 1.41M output, 325 dispatches, 5.4 pump turns per dispatch; developer 124
 turns/inv, 39M cache_read/inv; evaluator 52 turns/inv; browser-qa 64 turns/inv with 13
 screenshot read-backs.
+
+## Permission economics (2026-09-04)
+
+Every human permission prompt is a stall the autonomous pipeline cannot resolve on its own.
+Two pieces close the loop: a log-only `PermissionRequest` recorder hook
+(`hooks/permission-request-log.sh`, stage 1 of CAND-PERM-1 — no decision, no deny mode) and
+a deterministic extension of the TOKEN-12 transcript analyzer
+(`lib/analyze_transcripts.py`) that classifies every Bash tool-use result and derives
+retry/stall/prompt metrics from it. A stage-2 deny mode is a separate, not-yet-built roadmap
+experiment.
+
+**Classification** (deterministic, from the transcript's `toolDenialKind` / `toolUseResult` /
+gap between issue and result):
+
+| class | rule |
+|---|---|
+| `hook_deny` (+ rule id) | `toolDenialKind == "permission-rule"` and content starts with `guard-`; rule id parsed from `guard-<name>: [<id>]`, `?` for pre-tag transcripts |
+| `settings_deny` | `toolDenialKind == "permission-rule"` and content starts with `Permission to use` |
+| `other_deny` | `toolDenialKind == "permission-rule"` but content matches neither `hook_deny` nor `settings_deny` (e.g. the install-gate's own "[install-gate] APPROVAL REQUIRED" denials) |
+| `automode_deny` | `toolDenialKind in {"automode-blocked","automode-unavailable"}` |
+| `user_deny` | `toolDenialKind == "user-rejected"` |
+| `stall` | no `toolDenialKind`, `toolUseResult` has none of `timedOutAfterMs`/`backgroundTaskId`/`interrupted`, gap ≥ 600 s (the result's error flag is irrelevant: a human-approved command that then fails is still a stall) |
+| `ambiguous_gap` | same shape, 120 s ≤ gap < 600 s — reported, never counted as a stall |
+
+**Metrics.** The sequence-dependent Bash metrics (`identical_command_retries`,
+`same_rule_retries`, `retry_loops`) are derived **after the whole transcript is parsed**, from
+Bash tool-uses in **issue order** (the order the assistant emitted them) joined with each
+use's final classification — never from result-arrival order, which differs whenever one
+turn issues several Bash calls or results land out of sequence. Bash commands are normalized
+by collapsing whitespace before comparison.
+
+| metric | definition | role |
+|---|---|---|
+| `post_denial_tool_turns` | denials (any class) whose next COMPLETE assistant message — has_tool accumulated across every row sharing that message's `message.id`, never a single row of it (a real transcript often starts a message with a text row before its tool_use row) — contains any tool_use | economics/behaviour only — a Read after a denied `sed` is recovery, not failure |
+| `immediate_bash_retries` | Bash denials whose next complete assistant message (same accumulation) contains a Bash tool_use | economics |
+| `identical_command_retries` | denied Bash uses followed, within the next 3 Bash uses in issue order, by the identical normalized command (once per denial) | hard tripwire (0) |
+| `same_rule_retries` | hook-denied Bash uses whose next Bash use in issue order is again hook-denied with the same rule id | tripwire (warn > 0) |
+| `retry_loops` | maximal runs of ≥ 3 consecutive denied Bash uses in issue order (any denial class) | hard tripwire (0) |
+| `human_prompts` / `prompt_outcomes` | count of `permission_request` events; outcome of the matching `tool_use_id`: `user_deny`, `allowed_after_wait` (gap ≥ 120 s), `allowed_fast`, `unmatched` | hard gate (0) once the recorder is proven live |
+| `stalls`, `stall_seconds`, `ambiguous_gaps` | as classified above | hard gate (`stalls == 0`) |
+| `fail_opens` (by reason), `malformed_event_rows` | tallied from the events file | diagnostics |
+| `unresolved_tool_uses` | Bash tool_uses with no `tool_result` row at all (e.g. the session was killed on a native dialog before the result ever arrived) | diagnostic |
+
+`analyze_pump`'s report also carries a top-level `permissions_total` dict — the pump's own
+`permissions` plus every subagent type's, summed field-by-field (`hook_denies` merged as
+counters) — so a `--compare` run and the `permission.*` metric rows reflect the whole
+session's economics, not just the pump's own turns.
+
+**The PermissionRequest recorder.** `hooks/permission-request-log.sh` is bound to Claude
+Code's `PermissionRequest` event (log-only, stage 1 — see `.claude/architecture/skills-and-hooks.md`).
+It pipes the hook's stdin JSON into `hooks/lib/hook_events.py --event permission_request`,
+which appends one line to a session-scoped events file:
+
+```
+<cache>/iad/hook-events/<project-slug>/<session-id>.jsonl
+```
+
+Directories are created `0700` and files `0600` (explicit modes, tightened best-effort if
+found wider). Each row is privacy-safe by construction: `session_id`, `agent_id`,
+`agent_type`, `tool_use_id`, `tool_name`, `permission_mode`, plus (`permission_request` rows
+only) `suggestion_count`, `suggestion_types`, and `suggestions_sha` (a hash of the raw
+suggestion list, never the list itself). **No raw command text and no command hash are ever
+recorded by default.** `IAD_HOOK_EVENTS_RAW=1` is an explicit, default-off diagnostic switch
+that additionally records `cmd_raw` (the first 2000 chars of the Bash command) — opt-in only,
+never set by the pipeline itself.
+
+The analyzer reads that same file to compute `human_prompts` and `prompt_outcomes`:
+
+```bash
+python3 scripts/automation/lib/analyze_transcripts.py <pump-session.jsonl> \
+  --events <cache>/iad/hook-events/<slug>/<session>.jsonl   # default: derived from the transcript path
+python3 scripts/automation/lib/analyze_transcripts.py <pump-session.jsonl> --stall-gap 300  # override the 600s stall floor
+```
+
+`--events` defaults to one direct `open()` of the derived path above (never a directory
+scan); a missing events file makes `human_prompts` / `malformed_event_rows` report `null`
+rather than `0`, so a PRE session recorded before the recorder existed is never mistaken for
+a session with zero prompts. `--stall-gap` overrides the 600 s `stall` floor only; the 120 s
+`ambiguous_gap` lower bound is fixed.
+
+Permission metrics are reported separately from token metrics on purpose: a session can be
+token-cheap and permission-expensive (a human sitting on a dialog) or the reverse, and
+conflating the two would hide either failure mode.
diff --git a/incredible_auto_dev/docs/improvement-roadmap.md b/incredible_auto_dev/docs/improvement-roadmap.md
index c295d390..1da42318 100644
--- a/incredible_auto_dev/docs/improvement-roadmap.md
+++ b/incredible_auto_dev/docs/improvement-roadmap.md
@@ -4459,6 +4459,159 @@ but appreciated.
   the vendored copies (tapeology, trendora) and an explicit decision on whether `post-goal`
   should ever be re-attached to a lifecycle point. "No in-repo caller" is not sufficient.
 
+### CAND-PERM-1 · Zero-human-prompt interactive goal mode (IN-PROGRESS — commits 1–7 landed, oracle + acceptance run owed)
+- **Proposed:** P1 · Effort L · Risk MED · **Status:** IN-PROGRESS on branch `perm-stall-closure`
+  (commits 1–7 landed, `b422b6e..HEAD`, including the whole-branch-review fix wave — comment-safe
+  tokenizer, restored policy rationale, stall-definition docs, per-message retry counters,
+  unresolved-use diagnostic, false-deny fixes; no deny-rule change). Task 10 (native-oracle
+  probe, then one real interactive acceptance iteration) is operator-gated — spends tokens
+  (G9) — and not started; that run is still owed.
+- **Problem (verified against Claude Code 2.1.260, 2,236 session transcripts, repo @ `b422b6e`):**
+  interactive goal-mode Bash dispatches occasionally reach a native approval dialog no autonomous
+  agent can answer — observed shape: `cd <dir> && \`-newline-continued `sed -i ...` then `grep`,
+  which the old tokenizer misread as one escaped word (a live tapeology stall). A hook deny
+  resolves in ~0.1s; the median human-rejection gap is 216s; 161 corpus Bash calls showed a
+  >600s tool_use→tool_result gap with no timeout/background marker (one
+  `source .venv/bin/activate` compound stalled 15,174s).
+- **Root causes:**
+
+  | # | Root cause | Closed by |
+  |---|---|---|
+  | R1 | Guard has no rule for the native cd + write / redirect / git asks | Task 1 (Rule C) |
+  | R2 | Tokenizer: `\`-newline continuation joins the next word; bare newline is whitespace; heredoc bodies parse as commands | Task 1 |
+  | R3 | Prompt note is read-only wording | Task 4 |
+  | R4 | `core.md` misdescribes the gate (lists `tee`/`install`; omits `rmdir`, redirects, git, newlines) | Task 5 |
+  | R5 | Six shared allow entries with no demonstrated effect; two provably inert; wrong-commit comment | Task 6 |
+  | R6 | No deterministic measurement of prompts/stalls/retry loops; old analyzer ignored `is_error`, `toolDenialKind`, timestamps | Tasks 7–8 |
+  | R7 | Fail-open is silent | Tasks 1–2 |
+  | R8 | `> /dev/` pattern denies `> /dev/null` | Task 3 |
+  | R9 | Rule A denied broader than the native gate and misread option values (`head -n 20`, `grep -m 1 foo`) as paths — each false deny cost a retry turn | Task 1 |
+
+- **Design decisions (one line each):**
+  - **D1** Mirror the native enforcer, tiered by evidence (observed / documented / bundle-code); unproven bundle shapes live in one oracle manifest, never enforced until probed.
+  - **D2** Rule scope tracks only the proven shape: Rule A denies a relative-path content read after `cd` for `grep/egrep/fgrep/cat/find`/read-only `sed` (per-command operand tables); Rule B keeps the unchanged b422b6e recursive-root shapes; Rule C1–C3 deny only the write/redirect/git segment that comes after the `cd`.
+  - **D3** Parser ambition is capped to `&& || ; | |& &`, bare/backslash-newline, redirects, minimal heredoc shielding, checker wrappers; everything else (subshells, loops, `eval`, backticks, substitution, unbalanced quoting) is **unknown** → bounded fail-open, pass-through to the native checker — except a coarse deny when tokenization fails and the raw text still shows `cd` then a write word (a bash syntax error regardless).
+  - **D4** Extend the existing detector/guard rather than add files; the sole new hook is the log-only PermissionRequest recorder, sharing the one event writer.
+  - **D5** The dispatch prompt note is prevention, the hook is enforcement, the log is proof — one concise rewrite, no new pump turn.
+  - **D6** Measurement is deterministic, session-scoped, private (`~/.cache/iad/hook-events/<slug>/<session-id>.jsonl`, 0700/0600, append+flock, no raw command text/hash); sequence-dependent retry metrics come from Bash **issue order**, never result-arrival order.
+  - **D7** `dontAsk` stays out entirely; the only fallback is a roadmap-only PermissionRequest deny-with-correction mode (Stage-2 below), promoted only on evidence.
+  - **D8** Evidence-only permissions: all six allow entries removed from `policy/permissions.yaml`; no deny-rule changes; operator grants go in gitignored `settings.local.json`.
+  - **D9** Acceptance gates are decoupled from stochastic thresholds: permission/reliability facts plus the normal Goal Mode quality contract are hard gates; token/turn economics are single-run warnings, budgets only after several comparable sessions.
+
+- **Guard semantics** (`hooks/lib/read_path_hygiene.py`; ids are what the guard, the events and the analyzer report):
+
+  | Rule | Denies | Notably does NOT deny | Evidence |
+  |---|---|---|---|
+  | **A** cd-compound-read | `cd`, then `grep/egrep/fgrep/cat/find`/read-only `sed` with ≥1 relative-path operand | absolute path after cd, no-path-operand reads, `ls`; `rg/head/tail/wc/awk/...` (oracle-gated) | E3 (grep); bundle `cd-compound-read` |
+  | **B** unbounded recursive root | `grep -r/-R/--recursive` or `rg`, rooted at `. ./ .. ../ ~ ~/` or a `./`, `../`, `~/`, `/` operand (b422b6e shapes, unchanged) | non-recursive/bounded-subdir searches; `ag`/`ack` | b6ae4d2 observed |
+  | **C1** cd-compound-write | `cd`, then `mkdir/touch/rm/rmdir/mv/cp` or `sed -i` | `tee`/`install` (not path-restricted); write before the cd (oracle) | E2; bundle table |
+  | **C2** cd-compound-redirect | `cd`, then a redirect whose target is not `/dev/null` | `2>/dev/null`, `>/dev/null 2>&1`, fd dups | docs; bundle |
+  | **C3** cd-git-compound | `cd`, then any `git` segment | `git -C dir ...` (no cd) | docs |
+  | **coarse** | tokenizer failure **and** raw text shows `cd` then a write word | every other tokenizer failure → fail-open | D3 |
+  | **unknown** (fail-open, logged) | — | grouping, control flow, `eval`, backticks, substitution, other tokenizer failures | D3; measured by the recorder |
+  | **oracle** (pinned, not enforced) | — | 18 boundary ids (O1…O19, `--oracle-manifest`) — the single probe list Task 9's script consumes | D1; Task 10 Step 1 |
+
+- **Six shared allow entries removed (commit 5, evidence-only — D8):**
+
+  | Entry | Transcript evidence | Why it cannot help | Disposition |
+  |---|---|---|---|
+  | `Bash(nohup *)` | 393 pipeline-agent calls, all pre-entry successes (classifier-approved) | `nohup` is stripped before rule matching (docs § Wrappers) | REMOVE |
+  | `Bash(setsid *)` | 221 pipeline-agent calls, all pre-entry successes | exec wrapper — "can't be auto-approved by a prefix rule" | REMOVE |
+  | `Bash(disown)` / `Bash(disown *)` | 284 pipeline-agent calls, all pre-entry successes | shell builtin, classifier-approved in auto mode regardless | REMOVE |
+  | `Bash(google-chrome *)` | 2 agent uses, both a `qa`-agent rule violation; Chrome is spawned only by the superpowers-chrome MCP node process | grants an unmanaged, unconfined browser outside engine teardown ownership | REMOVE (operator's own use → local `settings.local.json`) |
+  | `Bash(/usr/bin/google-chrome *)` | 0 agent uses, 1 operator use | same | REMOVE |
+
+  Deny block byte-identical before/after; `additionalDirectories` unchanged (Task 6 Step 4).
+
+- **Permission economics (commit 6 — `analyze_transcripts.py`, issue-order Bash metrics):**
+
+  Classification:
+
+  | class | rule |
+  |---|---|
+  | `hook_deny` (+rule id) | `toolDenialKind=="permission-rule"`, content starts `guard-`; id parsed from `guard-<name>: [<id>]` |
+  | `settings_deny` | same kind, content starts `Permission to use` |
+  | `automode_deny` | `toolDenialKind` in `{automode-blocked, automode-unavailable}` |
+  | `user_deny` | `toolDenialKind=="user-rejected"` |
+  | `stall` | no denial kind, `toolUseResult` has none of the timeout/background/interrupted markers, gap ≥600s (the result's error flag is irrelevant: a human-approved command that then fails is still a stall) |
+  | `ambiguous_gap` | same but 120s ≤ gap < 600s (reported, never counted as a stall) |
+
+  Metrics (sequence-dependent ones from Bash **issue order**, never result-arrival order):
+
+  | metric | role |
+  |---|---|
+  | `post_denial_tool_turns` / `immediate_bash_retries` | economics — recovery vs failure |
+  | `identical_command_retries` | hard tripwire (0) |
+  | `same_rule_retries` | tripwire (warn > 0) |
+  | `retry_loops` (≥3 consecutive denied Bash uses) | hard tripwire (0) |
+  | `human_prompts` / `prompt_outcomes` | hard gate (0) once the recorder is proven |
+  | `stalls`, `stall_seconds`, `ambiguous_gaps` | hard gate (`stalls == 0`) |
+  | `fail_opens` (by reason), `malformed_event_rows` | diagnostics |
+  | `unresolved_tool_uses` (Bash tool_use with no `tool_result` row at all) | diagnostic |
+
+- **DoD / Acceptance criteria (D9, Task 10 — the operator-gated run):**
+  - *Hard permission/reliability gates:* `human_prompts == 0` once the recorder is proven (else `stalls == 0` AND no observed dialog); `identical_command_retries == 0`; `retry_loops == 0`; no permission-induced `AWAITING_PUMP`/inflight timeout; existing reviewer/QA/closure gates pass with no failure attributable to the permission changes; `run-evals.sh` + detector/event-writer self-tests green; no security regression; no deny-rule weakening.
+  - *TOKEN-11a health:* `pump_turns_per_dispatch` does not materially regress vs the immediate PRE (`≤ 2.2` is the established target only where the compared configuration already meets it).
+  - *Reviewer/QA quality:* verdict counts are diagnostics, never PRE-equality gates. *Economics warnings (one run, not gates):* post-denial/immediate-Bash-retry rate, developer turns/inv, or cache-read materially higher (>10–15%); any `same_rule_retries`.
+
+- **Stage-2 experiment (roadmap-only — NOT implemented, D7):** if Task 10's acceptance run still
+  shows significant unpredictable prompts after the deterministic rules land,
+  `permission-request-log.sh` may gain a deny-with-correction mode read from a default-off
+  marker file `<cache>/iad/hook-events/<slug>/.deny-mode` (never `.claude/`), returning
+  `decision.behavior:"deny"` with a corrective message **only when `agent_id` is present**
+  (subagent calls — the operator's own calls still see a normal dialog). Tripwire: any
+  `identical_command_retries > 0`, `retry_loops > 0`, or post-denial activity up >15% deletes
+  the marker. Per-agent/pump-wide `dontAsk` (ignored under this host's auto-mode parent / would
+  auto-deny hundreds of classifier-approved calls) and `bypassPermissions` (no confirmation
+  ever) are explicitly rejected.
+
+- **Rollback (per commit):** each of the seven commits reverts independently with `git revert` +
+  `sync-cli-assets.py --cli claude`. Emergency: drop `guard-read-path-hygiene.sh` from
+  `policy/hook-bindings.yaml` and resync (drops Rules A–C at once), or a one-session
+  `--settings '{"disableAllHooks":true}'` (never in a pump run — also disables the security
+  gates). Commit 5 (allow-entry removal) rolls back by re-adding the six lines. The recorder is
+  log-only; a future deny mode rolls back by deleting its marker file. Vendored repos receive
+  changes only through the operator's per-file sync.
+
+- **Stop-and-ask:** (i) an oracle probe shows a guard-DENY control shape (O1/O5/O11) as
+  `native_allow` → narrow the rule, never the allowlist; (ii) an oracle shape shows `NATIVE_ASK`
+  for a path-resolution reason → extend the rule set with a fixture, never loosen the guard;
+  (iii) the recorder writes nothing on a real dialog; (iv) any need to touch a deny rule;
+  (v) `run-evals.sh` goes red.
+
+- **PRE/POST ledger template.** Kept HERE rather than in `benchmarks/experiments.md`: that file
+  is an append-only ledger whose block format is pinned by
+  `tests/automation/test-benchmark-runner.sh`, and an unfilled template committed there would
+  read as a fake entry. The operator copies this block into `benchmarks/experiments.md`, fills
+  in `<...>`, and runs Task 10:
+
+  ```markdown
+  ## PRE <session-id>
+  framework: <sha of commit 7> (clean)   fixture: <repo>/<branch> resume of <goal session>
+  hypothesis: with Rules A/B/C1–C3, newline-aware tokenization and the path-safety note, no
+    subagent Bash call reaches a human dialog; denials are corrective, not looping.
+  hard gates: permission.human_prompts == 0 (or stalls == 0 + no observed dialog if the recorder
+    is unproven); identical_command_retries == 0; retry_loops == 0; no permission-induced
+    AWAITING_PUMP or inflight timeout; the iteration completes its normal reviewer/QA/closure
+    gates with no failure attributable to permission routing; no security regression; no
+    deny-rule change.
+  TOKEN-11a health: pump_turns_per_dispatch does not materially regress vs the immediate PRE
+    (<= 2.2 is the established TOKEN-11a target only where the compared configuration already
+    meets it).
+  warnings (one-session noise, not gates): post_denial_tool_turns or immediate_bash_retries per
+    Agent dispatch > +15 % vs PRE; developer turns/inv > +15 %; pump+subagent cache_read
+    > +15 %; same_rule_retries > 0; prompt bytes per dispatch delta ~= +200 B.
+  diagnostics reported, not gated: reviewer/QA verdict counts; ambiguous_gaps; fail_opens by
+    reason.
+  baseline (historical, analyze_transcripts.py on f99ab8e4 + c6453615): <numbers from Task 8
+    Step 4 PRE baseline run>
+  oracle: <path to the permission-oracle.sh output table — one row per manifest id>
+  ```
+
+- **Verify:** `bash -n scripts/automation/permission-oracle.sh` ·
+  `python3 hooks/lib/read_path_hygiene.py --oracle-manifest | wc -l` (18) ·
+  `./scripts/automation/run-evals.sh` · `bash tests/automation/test-doc-drift.sh`.
+
 ---
 
 ## 17. Absorbed-from-README ledger (traceability)
diff --git a/incredible_auto_dev/hooks/guard-dangerous-commands.sh b/incredible_auto_dev/hooks/guard-dangerous-commands.sh
index f4769244..f8f892e3 100644
--- a/incredible_auto_dev/hooks/guard-dangerous-commands.sh
+++ b/incredible_auto_dev/hooks/guard-dangerous-commands.sh
@@ -72,7 +72,6 @@ DANGEROUS_PATTERNS=(
   "mkfs"
   "fdisk"
   "parted"
-  "> /dev/"
   # Secrets
   "cat ~/.ssh/id_rsa"
   "cat ~/.ssh/id_ed25519"
@@ -134,6 +133,9 @@ DANGEROUS_REGEXES=(
   "^(sudo )?chown .+ /(etc|usr|home|root|var|boot)"
   # docker run mounting host filesystem sensitive directories
   "docker run .*(-v|--volume) /(etc|usr|root|home|var|boot|lib|sys|proc)"
+  # Output redirection onto a device node. /dev/null, /dev/stdout, /dev/stderr and /dev/tty
+  # are the shell's ordinary sinks, not disk writes.
+  '>\s*/dev/(?!null\b|stdout\b|stderr\b|tty\b)'
 )
 
 for regex in "${DANGEROUS_REGEXES[@]}"; do
diff --git a/incredible_auto_dev/hooks/guard-read-path-hygiene.sh b/incredible_auto_dev/hooks/guard-read-path-hygiene.sh
new file mode 100755
index 00000000..85697993
--- /dev/null
+++ b/incredible_auto_dev/hooks/guard-read-path-hygiene.sh
@@ -0,0 +1,97 @@
+#!/usr/bin/env bash
+# Guard hook: read-path hygiene (PreToolUse / Bash).
+#
+# Turns `.claude/core.md` § "File Paths in Bash" from advisory prose into a
+# machine-enforced rule, so a dispatched agent never stalls the pipeline on a
+# human approval prompt it cannot get. Prose alone did not hold: goal session
+# contract-pack-v0 iter 1 stalled on
+# `cd .../contracts && grep -rn "book_snapshot" workstation_contracts/*.py`
+# with the rule already in core.md AND in the dispatch prompt's search-path note.
+#
+# Acceptance philosophy: deny only a shape PROVEN to stall approval -- an
+# observed incident, Claude Code's own hard-gate table, or documented core.md
+# behaviour -- and fail open on every shape this cannot parse or does not
+# recognize. Rules A (relative-path content read after `cd`), B (recursive
+# search rooted unbounded) and C1-C3 (write / output-redirect / git after a
+# `cd`) live in lib/read_path_hygiene.py; read its docstring for the full
+# breakdown and the unknown/fail-open reasons it prints to stderr.
+#
+# On match this DENIES with a rule-tagged corrective message -- e.g.
+# `guard-read-path-hygiene: [C1] ...` -- so the agent self-corrects on its next
+# turn instead of waiting for a human, and a log reader can group denials by
+# rule id without the command text ever being stored. The detection logic (and
+# its stdout header protocol) lives in lib/read_path_hygiene.py; the event
+# writer lives in lib/hook_events.py.
+#
+# I/O modes mirror guard-dangerous-commands.sh (SEC-7):
+#   argv mode  — command as $1 (run-evals, test harness, Codex): GUARD lines on
+#     stderr + exit 1 on match.
+#   stdin mode — the Claude Code PreToolUse protocol: JSON on stdin
+#     (.tool_input.command). On match emit permissionDecision "deny" JSON on
+#     stdout and exit 0 — the settings wrapper is `|| true`, so the exit code
+#     carries no signal on Claude and the stdout JSON is the enforcement channel.
+# Fail-open on missing/unparseable input or a missing python3.
+#
+# Privacy: every DENY, and every fail-open on syntax this module genuinely
+# cannot classify, is logged as one privacy-safe JSON event -- no raw command
+# text, no command hash, no raw permission-suggestion text -- to a
+# session-scoped file under $XDG_CACHE_HOME/iad/hook-events/<project-slug>/
+# (or $IAD_HOOK_EVENTS_FILE, if set); see lib/hook_events.py's docstring for
+# the event schema and the directory/file privacy modes (0700/0600). Logging
+# is best-effort and silent: it never blocks or fails the guard.
+
+CMD="${1:-}"
+INPUT_MODE="argv"
+if [ -z "$CMD" ] && [ ! -t 0 ]; then
+  _payload=$(cat 2>/dev/null || true)
+  if [ -n "$_payload" ]; then
+    if command -v jq >/dev/null 2>&1; then
+      CMD=$(printf '%s' "$_payload" | jq -r '.tool_input.command // empty' 2>/dev/null) || CMD=""
+    else
+      CMD=$(printf '%s' "$_payload" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command") or "")' 2>/dev/null) || CMD=""
+    fi
+    if [ -n "$CMD" ]; then INPUT_MODE="stdin"; fi
+  fi
+fi
+[ -z "$CMD" ] && exit 0
+command -v python3 >/dev/null 2>&1 || exit 0
+
+_HOOK_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
+_DETECTOR="$_HOOK_DIR/lib/read_path_hygiene.py"
+_EVENTS="$_HOOK_DIR/lib/hook_events.py"
+[ -f "$_DETECTOR" ] || exit 0
+_PAYLOAD_JSON="${_payload:-{\}}"      # "{}" in argv mode (tests, Codex)
+
+_event() {   # $1 event name, $2 extra JSON object — never fails, never prints to stdout
+  [ -f "$_EVENTS" ] || return 0
+  printf '%s' "$_PAYLOAD_JSON" | python3 "$_EVENTS" --hook guard-read-path-hygiene --event "$1" --extra "$2" >/dev/null 2>&1 || true
+}
+
+_deny() {   # $1 rule id, $2 header JSON, $3 message
+  echo "GUARD: [$1] $3" >&2
+  echo "GUARD: command was: $CMD" >&2
+  _event hygiene_deny "$2"
+  if [ "$INPUT_MODE" = "stdin" ]; then
+    _reason="guard-read-path-hygiene: [$1] $3"
+    if command -v jq >/dev/null 2>&1; then
+      jq -cn --arg r "$_reason" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
+    else
+      python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":sys.argv[1]}}, separators=(",",":")))' "$_reason"
+    fi
+    exit 0
+  fi
+  exit 1
+}
+
+_err_file="$(mktemp 2>/dev/null || echo /dev/null)"
+_verdict=$(printf '%s' "$CMD" | python3 "$_DETECTOR" 2>"$_err_file") || _verdict=""
+if [ -n "$_verdict" ]; then
+  _hdr="${_verdict%%$'\n'*}"
+  _msg="${_verdict#*$'\n'}"
+  _rule="${_hdr#*\"rule\":\"}"; _rule="${_rule%%\"*}"
+  _deny "$_rule" "$_hdr" "$_msg"
+fi
+_fo="$(grep -o 'FAILOPEN reason=[^ ]*' "$_err_file" 2>/dev/null | head -1 | cut -d= -f2)"
+[ "$_err_file" != /dev/null ] && rm -f "$_err_file" 2>/dev/null
+[ -n "$_fo" ] && _event hygiene_fail_open "{\"reason\":\"$_fo\"}"
+exit 0
diff --git a/incredible_auto_dev/hooks/lib/hook_events.py b/incredible_auto_dev/hooks/lib/hook_events.py
new file mode 100644
index 00000000..cadb9aeb
--- /dev/null
+++ b/incredible_auto_dev/hooks/lib/hook_events.py
@@ -0,0 +1,201 @@
+#!/usr/bin/env python3
+"""Append one JSON event line for a Claude Code hook decision.
+
+Session-scoped: <cache>/iad/hook-events/<project-slug>/<session-id>.jsonl — one session per
+file. Private: directories 0700, files 0600 (explicit modes, not the caller's umask; existing
+wider modes are tightened best-effort — only inside hook-events/). Append-safe: one fully
+built line per write on an O_APPEND descriptor under flock, so parallel subagent hooks never
+interleave rows. Privacy-safe: never stores raw command text, command hashes or raw
+permission suggestions; IAD_HOOK_EVENTS_RAW=1 is the explicit default-off diagnostic that
+adds cmd_raw. Never fails the caller: any error exits 0 silently.
+    python3 hook_events.py --hook <name> --event <event> [--extra '<json object>']   (hook input JSON on stdin)
+    python3 hook_events.py --self-test
+"""
+import datetime
+import fcntl
+import hashlib
+import json
+import os
+import re
+import stat
+import sys
+
+KEEP = ("session_id", "agent_id", "agent_type", "tool_use_id", "tool_name", "permission_mode")
+DIR_MODE, FILE_MODE = 0o700, 0o600
+
+
+def events_file(session_id):
+    explicit = os.environ.get("IAD_HOOK_EVENTS_FILE")
+    if explicit:
+        return explicit
+    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
+    slug = re.sub(r"[^A-Za-z0-9]", "-", root)
+    sid = re.sub(r"[^A-Za-z0-9._-]", "", session_id or "") or "_no-session"
+    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
+    return os.path.join(base, "iad", "hook-events", slug, sid + ".jsonl")
+
+
+def _private_dir(path):
+    """mkdir -p with 0700; tighten an existing wider dir (best effort)."""
+    os.makedirs(path, mode=DIR_MODE, exist_ok=True)
+    try:
+        if stat.S_IMODE(os.stat(path).st_mode) != DIR_MODE:
+            os.chmod(path, DIR_MODE)
+    except OSError:
+        pass
+
+
+def sha16(text):
+    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]
+
+
+def build_event(args, payload):
+    try:
+        extra = json.loads(args.get("--extra") or "{}")
+    except ValueError:
+        extra = {}
+    event = {"ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
+             "event": args.get("--event", ""), "hook": args.get("--hook", "")}
+    for key in KEEP:
+        event[key] = str(payload.get(key, "") or "")
+    if event["event"] == "permission_request":
+        sugg = payload.get("permission_suggestions") or []
+        event["suggestion_count"] = len(sugg)
+        event["suggestion_types"] = sorted({str(s.get("type", "?")) for s in sugg if isinstance(s, dict)})
+        event["suggestions_sha"] = sha16(json.dumps(sugg, sort_keys=True)) if sugg else ""
+    event.update(extra)
+    if os.environ.get("IAD_HOOK_EVENTS_RAW") == "1":      # explicit, default-off diagnostic
+        tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
+        event["cmd_raw"] = str(tool_input.get("command", "") or "")[:2000]
+    return event
+
+
+def append_event(path, event):
+    parent = os.path.dirname(path)
+    if not os.environ.get("IAD_HOOK_EVENTS_FILE"):
+        base = os.path.dirname(parent)               # …/hook-events
+        _private_dir(base)
+        _private_dir(parent)                          # …/hook-events/<slug>
+    else:
+        os.makedirs(parent, exist_ok=True)
+    line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
+    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, FILE_MODE)
+    try:
+        if stat.S_IMODE(os.fstat(fd).st_mode) != FILE_MODE:
+            try:
+                os.fchmod(fd, FILE_MODE)
+            except OSError:
+                pass
+        fcntl.flock(fd, fcntl.LOCK_EX)
+        try:
+            os.write(fd, line.encode("utf-8"))
+        finally:
+            fcntl.flock(fd, fcntl.LOCK_UN)
+    finally:
+        os.close(fd)
+
+
+def main():
+    args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
+    try:
+        payload = json.load(sys.stdin)
+    except Exception:
+        payload = {}
+    if not isinstance(payload, dict):
+        payload = {}
+    event = build_event(args, payload)
+    append_event(events_file(event["session_id"]), event)
+
+
+def _self_test():
+    import subprocess
+    import tempfile
+    fails = []
+    with tempfile.TemporaryDirectory() as tmp:
+        env = dict(os.environ, XDG_CACHE_HOME=tmp, CLAUDE_PROJECT_DIR="/home/u/Git/incredible_auto_dev")
+        env.pop("IAD_HOOK_EVENTS_FILE", None)
+        env.pop("IAD_HOOK_EVENTS_RAW", None)
+        payload = json.dumps({"session_id": "sess-1", "agent_id": "a1", "agent_type": "developer",
+                              "tool_use_id": "t1", "tool_name": "Bash", "permission_mode": "auto",
+                              "tool_input": {"command": "cd apps && sed -i s/a/b/ x.py SECRET=1"},
+                              "permission_suggestions": [{"type": "addRules", "rules": [{"ruleContent": "sed *"}]}]})
+        run = lambda ev: subprocess.run([sys.executable, __file__, "--hook", "t", "--event", ev, "--extra", '{"rule":"C1"}'],
+                                        input=payload, text=True, env=env, capture_output=True)
+        r = run("hygiene_deny")
+        f = os.path.join(tmp, "iad", "hook-events", "-home-u-Git-incredible-auto-dev", "sess-1.jsonl")
+        if r.returncode != 0 or r.stdout:
+            fails.append("writer must exit 0 with empty stdout: rc=%s out=%r" % (r.returncode, r.stdout))
+        if not os.path.isfile(f):
+            fails.append("session file not created at %s" % f)
+        else:
+            for d in (os.path.dirname(os.path.dirname(f)), os.path.dirname(f)):
+                if stat.S_IMODE(os.stat(d).st_mode) != DIR_MODE:
+                    fails.append("dir mode %o != 0700 for %s" % (stat.S_IMODE(os.stat(d).st_mode), d))
+            if stat.S_IMODE(os.stat(f).st_mode) != FILE_MODE:
+                fails.append("file mode %o != 0600" % stat.S_IMODE(os.stat(f).st_mode))
+            row = json.loads(open(f, encoding="utf-8").read().splitlines()[0])
+            for forbidden in ("cmd_sha", "cmd_raw"):
+                if forbidden in row:
+                    fails.append("default schema must not contain %s" % forbidden)
+            if "SECRET" in json.dumps(row) or "ruleContent" in json.dumps(row):
+                fails.append("event leaks command or suggestion text: %r" % row)
+            if row.get("rule") != "C1" or row.get("agent_type") != "developer":
+                fails.append("extra/attribution fields missing: %r" % row)
+        run("permission_request")
+        row = json.loads(open(f, encoding="utf-8").read().splitlines()[1])
+        if row.get("suggestion_count") != 1 or row.get("suggestion_types") != ["addRules"] or not row.get("suggestions_sha"):
+            fails.append("permission_request summary fields wrong: %r" % row)
+        # widened file/dir get tightened best-effort
+        os.chmod(f, 0o644)
+        os.chmod(os.path.dirname(f), 0o755)
+        run("hygiene_fail_open")
+        if stat.S_IMODE(os.stat(f).st_mode) != FILE_MODE or stat.S_IMODE(os.stat(os.path.dirname(f)).st_mode) != DIR_MODE:
+            fails.append("existing wider modes were not tightened")
+        # concurrent appends: 8 processes x 50 events, every row must parse, none interleaved
+        procs = [subprocess.Popen([sys.executable, __file__, "--stress", "50", "--event", "hygiene_deny"],
+                                  stdin=subprocess.PIPE, text=True, env=env) for _ in range(8)]
+        for p in procs:
+            p.communicate(payload)
+        lines = open(f, encoding="utf-8").read().splitlines()
+        bad = sum(1 for l in lines if not l.startswith("{") or not l.endswith("}") or _bad_json(l))
+        if len(lines) != 3 + 400 or bad:
+            fails.append("concurrent append: %d lines (expected 403), %d malformed" % (len(lines), bad))
+        # explicit override + no-session fallback
+        env2 = dict(env, IAD_HOOK_EVENTS_FILE=os.path.join(tmp, "override.jsonl"))
+        subprocess.run([sys.executable, __file__, "--hook", "t", "--event", "hygiene_deny"], input="{}", text=True, env=env2)
+        if not os.path.isfile(os.path.join(tmp, "override.jsonl")):
+            fails.append("IAD_HOOK_EVENTS_FILE override not honoured")
+        subprocess.run([sys.executable, __file__, "--hook", "t", "--event", "hygiene_deny"], input="{}", text=True, env=env)
+        if not os.path.isfile(os.path.join(tmp, "iad", "hook-events", "-home-u-Git-incredible-auto-dev", "_no-session.jsonl")):
+            fails.append("_no-session fallback file not created")
+    for x in fails:
+        print("FAIL " + x)
+    print("hook_events self-test: %d failures" % len(fails))
+    return 1 if fails else 0
+
+
+def _bad_json(line):
+    try:
+        json.loads(line)
+        return False
+    except ValueError:
+        return True
+
+
+if __name__ == "__main__":
+    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
+        sys.exit(_self_test())
+    if len(sys.argv) > 2 and sys.argv[1] == "--stress":       # self-test helper: N sequential events
+        try:
+            payload = json.load(sys.stdin)
+            args = dict(zip(sys.argv[3::2], sys.argv[4::2]))
+            for _ in range(int(sys.argv[2])):
+                append_event(events_file(payload.get("session_id", "")), build_event(args, payload))
+        except Exception:
+            pass
+        sys.exit(0)
+    try:
+        main()
+    except Exception:
+        pass
+    sys.exit(0)
diff --git a/incredible_auto_dev/hooks/lib/read_path_hygiene.py b/incredible_auto_dev/hooks/lib/read_path_hygiene.py
new file mode 100644
index 00000000..b647ce77
--- /dev/null
+++ b/incredible_auto_dev/hooks/lib/read_path_hygiene.py
@@ -0,0 +1,724 @@
+#!/usr/bin/env python3
+"""Detect Bash command shapes that would stall a headless dispatch on a human
+approval prompt, and deny them with a corrective message before they run.
+
+Acceptance philosophy, in one sentence: DENY a shape only when it is PROVEN --
+by an observed incident, by Claude Code's own hard-gate table, or by
+documented `.claude/core.md` behaviour -- to stall on a human, and FAIL OPEN
+on every shape this module cannot parse or does not recognize, because a
+false ALLOW merely defers to the native permission checker (where the
+decision belongs by default) while a false DENY blocks real work.
+
+Why the approval prompt happens at all: `Read(**/.env)`, `Read(~/.ssh/**)` and
+friends are DENY rules, and deny beats every allow. Before a read the
+permission checker must prove the read cannot touch a denied path. It cannot
+prove that when the search root is unresolvable (a `cd` first) or unbounded
+(`.`, an absolute path), so it escalates to a human -- a hang inside a
+headless or pump dispatch. Narrowing the deny rules to silence it is
+explicitly forbidden by core.md; they keep real secrets out of agent context.
+
+Rules -- A and C1-C3 fire only on a segment AFTER a `cd` in the same command;
+B fires regardless of `cd` (an unbounded root is unbounded either way):
+
+  A  -- the hard-enforced content-read set (grep/egrep/fgrep, cat, find,
+        read-only sed -n) carries a RELATIVE path operand. Evidence tier:
+        observed (E3 -- the goal-session contract-pack-v0 iter 1 stall) plus
+        the per-command operand tables below; rg/head/tail/wc/awk/... are
+        deliberately left oracle-gated, not enforced.
+  B  -- a recursive content search (grep/egrep/fgrep -r, rg always) is rooted
+        at `.`, `./`, `..`, `~` or an absolute path -- unbounded regardless of
+        `cd`. Evidence tier: observed regressions (b422b6e, b6ae4d2).
+  C1 -- a write/create-class command (sed -i, cp, mv, rm, rmdir, mkdir, touch)
+        runs after the `cd`. Evidence tier: Claude Code's own hard gate
+        ("compound command contains cd with write operation ... manual
+        approval required") -- no allow rule can ever pre-approve this shape,
+        so it is enforced unconditionally. Also observed (E2 verbatim).
+  C2 -- an output redirect (`>`, `>>`, `&>`, ...) to a real file (not
+        /dev/null) follows the `cd`. Evidence tier: Claude Code's own hard
+        gate ("compound command contains cd with output redirection ...
+        manual approval required"), documented in core.md.
+  C3 -- `git` runs after the `cd`. Evidence tier: documented in core.md (git
+        run from a changed directory can execute that directory's hooks).
+
+Unknown / fail-open: a command this module cannot safely reason about passes
+through UNCHANGED to the native checker -- never denied on a guess. One
+stderr line names why: `FAILOPEN reason=tokenize` (shell syntax the tokenizer
+rejects, e.g. an unbalanced quote), `FAILOPEN reason=complex:<kind>` (control
+flow, subshell/brace/command-substitution/process-substitution grouping, or a
+backtick substitution -- `<kind>` is `control-flow`, `grouping` or
+`backtick`), or `FAILOPEN reason=exception:<ClassName>` (an unexpected bug in
+this module itself, caught so the guard never becomes the hang it prevents).
+The one exception is `coarse_check()`: when the tokenizer itself fails, a
+command still matching an unmistakable `cd ... <write word>` shape is denied
+as rule "coarse" instead of failing open, because that shape does not need a
+clean parse to be certain.
+
+Header protocol (read by guard-read-path-hygiene.sh): on a DENY, stdout line 1
+is a single-line JSON header -- `{"rule": "...", "command_class": "...",
+"has_cd": bool, "has_output_redirect": bool}` -- followed by the corrective
+message (everything after the first newline). Nothing is written to stdout
+when the command is clean or unknown.
+
+`--self-test` runs the fixture suite at the bottom of this file and exits
+0/1. `--oracle-manifest` prints one `id<TAB>command` line per ORACLE_MANIFEST
+case (`{SB}` = sandbox root placeholder) -- the single source consumed by
+scripts/automation/permission-oracle.sh, so the native-checker probe list and
+this module's pinned expectations can never drift apart.
+"""
+
+import json
+import re
+import shlex
+import sys
+from collections import namedtuple
+
+# Prefixes the native checker strips before matching (docs § Wrappers) plus sudo/exec/!.
+WRAPPERS = {"sudo", "env", "nohup", "nice", "command", "builtin", "exec", "time", "stdbuf", "!"}
+# The checker's create/write-class commands (bundle NH table). tee/install are absent on purpose.
+WRITE_COMMANDS = {"mkdir", "touch", "rm", "rmdir", "mv", "cp"}
+# Syntax the guard deliberately does not interpret (D3): fail open, log, let the checker decide.
+CONTROL_FLOW = {"for", "while", "until", "if", "case", "select", "function", "eval"}
+GROUPING = {"(", ")", "{", "}"}
+PUNCT = "();<>|&\n"                      # shlex punctuation + newline (a separator in the shell)
+SEPARATORS = {";", "&&", "||", "|", "&", "|&", "\n"}
+OUTPUT_REDIRECTS = {">", ">>", ">|", "&>", "&>>"}
+OTHER_REDIRECTS = {">&", "<", "<<<", "<&", "<>"}
+SAFE_REDIRECT_TARGETS = {"/dev/" + "null"}
+UNRESOLVABLE_ROOTS = {".", "./", "..", "../", "~", "~/"}
+COARSE_CD = re.compile(r"(?:^|[;&|\n]\s*)cd\s")
+COARSE_WRITE = re.compile(r"(?:^|[;&|\s])(?:sed\s+(?:-[A-Za-z]*i|--in-place)|rm|rmdir|mv|cp|mkdir|touch)\s")
+
+Verdict = namedtuple("Verdict", "rule command_class has_cd has_output_redirect message")
+RULE_DOC = "See .claude/core.md -> File Paths in Bash."
+MSG = {
+    "A": ("`%s` reads a relative path in a command that also runs `cd`, so the permission checker "
+          "cannot resolve the file and MUST ask a human -- which hangs this dispatch. Drop the `cd` "
+          "and use a repo-relative path from the repo root (e.g. `grep -n \"x\" apps/backend/app/main.py`, "
+          "not `cd apps/backend && grep -n \"x\" app/main.py`). `cd` stays legal for a command that "
+          "needs the cwd and reads no path, writes nothing, redirects nothing and does not run git "
+          "(pytest, npm, tsc). " + RULE_DOC),
+    "B": ("`%s` roots a recursive search at `%s`. An unbounded root cannot be proven to miss the "
+          "`Read(**/.env)` deny rules, so the checker MUST ask a human -- which hangs this dispatch. "
+          "Name concrete repo-relative subdirectories instead (e.g. `grep -rn PATTERN apps/backend/app/ "
+          "apps/frontend/src/`). `--include`/`--exclude-dir` do NOT help: the checker reads the path "
+          "argument, not the filter flags. " + RULE_DOC),
+    "C1": ("`%s` mutates a file after a `cd` in the same command. Claude Code hard-gates that shape "
+           "('compound command contains cd with write operation - manual approval required'); NO allow "
+           "rule can pre-approve it, so this dispatch would hang on a human. Edit files with the "
+           "Edit/Write tools, or drop the `cd` and use a repo-relative path from the repo root (e.g. "
+           "`sed -i 's/OLD/NEW/g' apps/backend/tests/test_x.py`, not `cd apps/backend/tests && sed -i "
+           "'s/OLD/NEW/g' test_x.py`). " + RULE_DOC),
+    "C2": ("The output redirect to `%s` follows a `cd` in the same command. Claude Code hard-gates "
+           "that shape ('compound command contains cd with output redirection - manual approval "
+           "required'), so this dispatch would hang on a human. Redirect to /dev/null, or drop the "
+           "`cd` and name the file repo-relative from the repo root (e.g. `pytest -q apps/backend > "
+           "apps/backend/test-output.log`), or capture the output with the Write tool. " + RULE_DOC),
+    "C3": ("`git` after a `cd` prompts a human (Claude Code treats git run from a changed directory "
+           "as able to execute that directory's hooks), which hangs this dispatch. Run git from the "
+           "repo root: `git status`, `git -C apps/backend log -3`, `git add apps/backend/app/x.py`. "
+           + RULE_DOC),
+}
+
+
+# ── Per-command operand extraction (tiny tables; not a general getopt) ─────────
+def operand_paths(args, value_short, value_long, pattern_short, pattern_long):
+    """Operands of a grep/sed/rg-style command line. Options in value_short/value_long consume a
+    value (attached or the next token); the first operand is the pattern/script unless one of
+    the pattern_* options supplied it. Table-driven per command; nothing else is interpreted."""
+    paths, i, pattern_given, opts_done = [], 0, False, False
+    while i < len(args):
+        a = args[i]
+        i += 1
+        if a == "-":
+            continue                                    # stdin marker, never a path (like cat_paths)
+        if opts_done or not a.startswith("-"):
+            paths.append(a)
+            continue
+        if a == "--":
+            opts_done = True
+            continue
+        if a.startswith("--"):
+            name = a.split("=", 1)[0]
+            pattern_given = pattern_given or name in pattern_long
+            if "=" not in a and name in value_long:
+                i += 1                                  # separate value token
+            continue
+        for j, ch in enumerate(a[1:], 1):
+            if ch in value_short:
+                pattern_given = pattern_given or ch in pattern_short
+                if j == len(a) - 1:
+                    i += 1                              # value is the next token
+                break                                   # otherwise the rest of the cluster is the value
+    if not pattern_given and paths:
+        paths = paths[1:]
+    return paths
+
+
+GREP_VALUE_SHORT = set("efmABCdD")
+GREP_VALUE_LONG = {"--regexp", "--file", "--max-count", "--after-context", "--before-context", "--context",
+                   "--include", "--exclude", "--exclude-dir", "--exclude-from", "--label", "--devices",
+                   "--directories", "--binary-files", "--color", "--colour", "--group-separator"}
+SED_VALUE_SHORT = set("efl")
+SED_VALUE_LONG = {"--expression", "--file", "--line-length"}
+RG_VALUE_SHORT = set("efgtTmABCMjdrE")
+RG_VALUE_LONG = {"--regexp", "--file", "--glob", "--iglob", "--type", "--type-not", "--type-add", "--max-count",
+                 "--after-context", "--before-context", "--context", "--max-columns", "--max-depth",
+                 "--max-filesize", "--threads", "--replace", "--encoding", "--color", "--colors", "--sort",
+                 "--sortr", "--context-separator", "--path-separator", "--pre", "--pre-glob", "--ignore-file",
+                 "--engine"}
+
+
+def grep_paths(args):
+    return operand_paths(args, GREP_VALUE_SHORT, GREP_VALUE_LONG, set("ef"), {"--regexp", "--file"})
+
+
+def sed_paths(args):
+    return operand_paths(args, SED_VALUE_SHORT, SED_VALUE_LONG, set("ef"), {"--expression", "--file"})
+
+
+def rg_paths(args):
+    return operand_paths(args, RG_VALUE_SHORT, RG_VALUE_LONG, set("ef"), {"--regexp", "--file"})
+
+
+def cat_paths(args):
+    return [a for a in args if a != "-" and not a.startswith("-")]
+
+
+def find_paths(args):
+    """Explicit starting points only: leading operands after -H/-L/-P/-Olevel/-D opts and before
+    the first expression. The implicit `.` when none is given is oracle-gated (O19), not enforced."""
+    i = 0
+    while i < len(args) and (args[i] in ("-H", "-L", "-P") or args[i].startswith("-O")):
+        i += 1
+    if i < len(args) and args[i] == "-D":
+        i += 2
+    paths = []
+    while i < len(args) and not args[i].startswith("-") and args[i] not in ("(", "!"):
+        paths.append(args[i])
+        i += 1
+    return paths
+
+
+# Rule A hard set: content-read commands whose operand grammar is simple enough to extract
+# deterministically AND that appear in observed stalls / the native read table (D2). `ls`
+# stays out (docs: `cd packages/api && ls` runs without a prompt); rg/head/tail/wc/awk/…
+# are oracle-gated, not enforced.
+READ_EXTRACTORS = {"grep": grep_paths, "egrep": grep_paths, "fgrep": grep_paths,
+                   "cat": cat_paths, "find": find_paths, "sed": sed_paths}
+# Rule B recursive searchers (the shipped b422b6e set) with their root extractors.
+ROOT_EXTRACTORS = {"grep": grep_paths, "egrep": grep_paths, "fgrep": grep_paths, "rg": rg_paths}
+ALWAYS_RECURSIVE = {"rg"}
+
+
+def normalize(cmd):
+    """Fold backslash-newline continuations (the shell joins them into one line), then blank
+    `#`-comments to end-of-line so they never reach the tokenizer."""
+    cmd = cmd.replace("\\\r\n", " ").replace("\\\n", " ")
+    return _strip_line_comments(cmd)
+
+
+def _strip_line_comments(cmd):
+    """Blank a `#...` comment to end-of-line, but keep the `\\n` itself. Only a `#` that
+    starts a word (preceded by whitespace or the start of the string) outside single/double
+    quotes is a comment marker -- `grep -n '#include' f` and `echo 'a#b' # trailing` must not
+    lose their quoted `#`. shlex's own default `commenters='#'` handling is not reused here
+    because it calls `instream.readline()`, which consumes the trailing newline TOO and
+    silently merges the next shell command into the commented-out segment (F1)."""
+    out = []
+    quote = None                      # None, "'" or '"'
+    i, n = 0, len(cmd)
+    while i < n:
+        ch = cmd[i]
+        if quote:
+            out.append(ch)
+            if quote == '"' and ch == "\\" and i + 1 < n:
+                out.append(cmd[i + 1])
+                i += 2
+                continue
+            if ch == quote:
+                quote = None
+            i += 1
+            continue
+        if ch in "'\"":
+            quote = ch
+            out.append(ch)
+            i += 1
+            continue
+        if ch == "#" and (i == 0 or cmd[i - 1] in " \t\r\n"):
+            while i < n and cmd[i] != "\n":
+                i += 1
+            continue
+        out.append(ch)
+        i += 1
+    return "".join(out)
+
+
+def tokenize(cmd):
+    lexer = shlex.shlex(cmd, posix=True, punctuation_chars=PUNCT)
+    lexer.whitespace = " \t\r"          # newline is a separator token, not whitespace
+    lexer.whitespace_split = True
+    lexer.commenters = ""               # comments are pre-stripped by _strip_line_comments();
+                                         # shlex must never again consume a newline via '#'
+    out = []
+    for tok in lexer:
+        if "\n" in tok and set(tok) <= set(PUNCT):   # shlex glues "&&\n" — split newlines back out
+            out.extend(re.findall(r"\n|[^\n]+", tok))
+        else:
+            out.append(tok)
+    return out
+
+
+def drop_heredocs(tokens):
+    """Remove `<<`/`<<-`, the delimiter and the body lines: the body is data, never commands."""
+    out, i = [], 0
+    while i < len(tokens):
+        tok = tokens[i]
+        if tok in ("<<", "<<-") and i + 1 < len(tokens):
+            if tokens[i + 1] == "-" and i + 2 < len(tokens):
+                delim = tokens[i + 2]          # `<<- DELIM` (space form): tokenizer splits the `-`
+                i += 3
+            else:
+                delim = tokens[i + 1].lstrip("-")   # `<<-DELIM` / `<< DELIM` (attached / no dash)
+                i += 2
+            while i < len(tokens) and tokens[i] != "\n":   # the rest of the command line stays
+                out.append(tokens[i])
+                i += 1
+            i += 1
+            while i < len(tokens):
+                if tokens[i] == delim and (i + 1 == len(tokens) or tokens[i + 1] == "\n"):
+                    i += 1
+                    break
+                i += 1
+            continue
+        out.append(tok)
+        i += 1
+    return out
+
+
+def split_redirects(tokens):
+    """Drop redirect operators (+ fd digit) and targets; return (tokens, [(position, target)])
+    for OUTPUT redirects, position = index in the returned token stream."""
+    out, targets, i = [], [], 0
+    while i < len(tokens):
+        tok = tokens[i]
+        if tok in OUTPUT_REDIRECTS or tok in OTHER_REDIRECTS:
+            if out and out[-1].isdigit():
+                out.pop()
+            target = tokens[i + 1] if i + 1 < len(tokens) else ""
+            if tok in OUTPUT_REDIRECTS and target and not target.startswith("&"):
+                targets.append((len(out), target))
+            i += 2
+            continue
+        out.append(tok)
+        i += 1
+    return out, targets
+
+
+def split_segments(tokens):
+    """[(start_index, [tokens])] split on shell separators."""
+    segments, current, start = [], [], 0
+    for i, tok in enumerate(tokens):
+        if tok in SEPARATORS:
+            if current:
+                segments.append((start, current))
+            current, start = [], i + 1
+        else:
+            current.append(tok)
+    if current:
+        segments.append((start, current))
+    return segments
+
+
+def head_of(segment):
+    """(command name, argument tokens) with env assignments and wrappers stripped."""
+    i = 0
+    while i < len(segment):
+        tok = segment[i]
+        if "=" in tok and not tok.startswith("-") and tok.split("=", 1)[0].isidentifier():
+            i += 1
+            continue
+        if tok in WRAPPERS:
+            i += 1
+            continue
+        if tok == "timeout" and i + 1 < len(segment):
+            i += 2
+            continue
+        break
+    if i >= len(segment):
+        return None, []
+    return segment[i].rsplit("/", 1)[-1], segment[i + 1:]
+
+
+def complex_syntax(tokens):
+    """Name the first construct the guard does not interpret, or None."""
+    for tok in tokens:
+        if tok in GROUPING:
+            return "grouping"            # subshell, brace group, $( ), <( ), >( ) all
+                                          # tokenize into single "(" or ")" tokens; (( / )) from
+                                          # arithmetic expansion are ordinary tokens — arithmetic is not
+                                          # command substitution
+        if "`" in tok:
+            return "backtick"
+    for _start, seg in split_segments(tokens):
+        name, _ = head_of(seg)
+        if name in CONTROL_FLOW:
+            return "control-flow"
+    return None
+
+
+def sed_writes(args):
+    for a in args:
+        if a == "--":
+            break
+        if a.startswith("--in-place"):
+            return True
+        if a.startswith("-") and not a.startswith("--"):
+            for ch in a[1:]:
+                if ch == "i":
+                    return True
+                if ch in "efl":          # value-taking short option: the rest of the cluster
+                    break                # is that option's value, not more flag letters
+    return False
+
+
+def is_relative(path):
+    return not (path.startswith("/") or path.startswith("~"))
+
+
+def has_recursive_flag(args):
+    for a in args:
+        if not a.startswith("-"):
+            continue
+        if a.startswith("--"):
+            if a in ("--recursive", "--dereference-recursive"):
+                return True
... [diff_bound] incredible_auto_dev/hooks/lib/read_path_hygiene.py: 330 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/hooks/permission-request-log.sh b/incredible_auto_dev/hooks/permission-request-log.sh
new file mode 100755
index 00000000..cdf76165
--- /dev/null
+++ b/incredible_auto_dev/hooks/permission-request-log.sh
@@ -0,0 +1,16 @@
+#!/usr/bin/env bash
+# PermissionRequest recorder — STAGE 1, LOG-ONLY. Fires when Claude Code is about to
+# need a permission decision from a human: the exact event the autonomous pipeline can
+# never answer. It emits NO decision (stdout stays empty; the native flow proceeds
+# unchanged) and only appends a privacy-safe permission_request event (Task 2 schema:
+# suggestion count/types/hash — never command or suggestion text) so
+# lib/analyze_transcripts.py can count human prompts deterministically. A deny mode is a
+# separate roadmap experiment (CAND-PERM-1 stage 2), not implemented here. Exit 0 always.
+[ -t 0 ] && exit 0
+_payload=$(cat 2>/dev/null || true)
+[ -n "$_payload" ] || exit 0
+_HOOK_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
+[ -f "$_HOOK_DIR/lib/hook_events.py" ] || exit 0
+command -v python3 >/dev/null 2>&1 || exit 0
+printf '%s' "$_payload" | python3 "$_HOOK_DIR/lib/hook_events.py" --hook permission-request-log --event permission_request >/dev/null 2>&1 || true
+exit 0
diff --git a/incredible_auto_dev/policy/hook-bindings.yaml b/incredible_auto_dev/policy/hook-bindings.yaml
index 8ca09121..312b24c1 100644
--- a/incredible_auto_dev/policy/hook-bindings.yaml
+++ b/incredible_auto_dev/policy/hook-bindings.yaml
@@ -10,6 +10,12 @@ guard-dangerous-commands.sh:
   codex:
   - PreToolUse
   - PermissionRequest
+guard-read-path-hygiene.sh:
+  claude:
+  - PreToolUse:Bash
+  codex:
+  - PreToolUse
+  - PermissionRequest
 post-edit-lint.sh:
   claude:
   - PostToolUse:Write|Edit
@@ -25,3 +31,7 @@ on-stop-check-artifacts.sh:
   - Stop
   codex:
   - Stop
+permission-request-log.sh:
+  claude:
+  - PermissionRequest
+  codex: []
diff --git a/incredible_auto_dev/policy/permissions.yaml b/incredible_auto_dev/policy/permissions.yaml
index 52a69223..0ce82bbf 100644
--- a/incredible_auto_dev/policy/permissions.yaml
+++ b/incredible_auto_dev/policy/permissions.yaml
@@ -78,8 +78,11 @@ allow:
 # `timeout *` and `make *` are command wrappers / arbitrary-target runners —
 # same accepted class as `env *` and `xargs *`; the embedded deny entries below
 # and the built-in rm containment bound the damage. Deliberately excluded:
-# nc, nohup, watch, yes, bare `command *` (wrapper/exfil/interactive risk with
-# no pipeline need).
+# nc, nohup, setsid, disown, watch, yes, bare `command *` (wrapper/exfil/interactive
+# risk with no pipeline need — and per Claude Code's docs `nohup`/`nice`/`timeout` are
+# stripped before rule matching, while `setsid`/`watch`/`flock` cannot be prefix-approved
+# at all; 2026-09-04 audit, .claude/anti-patterns/32). The browser is launched by the
+# Chrome MCP server, never by an agent's Bash tool, so no google-chrome entry belongs here.
 - Bash(make)
 - Bash(make *)
 - Bash(timeout *)
diff --git a/incredible_auto_dev/scripts/automation/goal-await-dispatch.sh b/incredible_auto_dev/scripts/automation/goal-await-dispatch.sh
index f268871f..19af2d2d 100755
--- a/incredible_auto_dev/scripts/automation/goal-await-dispatch.sh
+++ b/incredible_auto_dev/scripts/automation/goal-await-dispatch.sh
@@ -88,6 +88,28 @@ if [[ "${1:-}" == "--self-test" ]]; then
   fi
   rm -rf "$t6"
 
+  # Scenario 6b (2026-09-03): a transient shell wrapper whose CMDLINE contains
+  # 'claude' must NOT be resolved as the pump. Some harnesses run every Bash
+  # tool call as `bash -c 'source ~/.claude/shell-snapshots/snapshot-*.sh ...'`;
+  # that wrapper dies with the tool call, so resolving to it made the engine see
+  # a dead pump and fast-pause AWAITING_PUMP on the first dispatch of every run.
+  # The inner -c string below carries a `.claude` path on purpose — it is what
+  # the resolver must now decline to match.
+  t6b=$(mktemp -d)
+  r6b="$t6b/req.eeeeee.ready"; printf '{"agent":"developer","prompt":"v"}\n' > "$r6b"
+  bash -c "# ~/.claude/shell-snapshots/snapshot-bash-1788470053000-polm5i.sh
+echo \$\$ > '$t6b/wrapper.pid'
+'$0' --dispatch-dir '$t6b' --engine-pid $$ --poll 1 >/dev/null 2>&1
+:" </dev/null >/dev/null 2>&1 || true
+  _wpid="$(cat "$t6b/wrapper.pid" 2>/dev/null || echo '')"
+  _got="$(sed -n 's/^pid=//p' "${r6b%.ready}.started" 2>/dev/null || true)"
+  if [[ -f "${r6b%.ready}.started" && -n "$_wpid" && "$_got" != "$_wpid" ]]; then
+    echo "  PASS await: shell wrapper carrying 'claude' in its cmdline is not resolved as the pump"
+  else
+    echo "  FAIL await: wrapper pid '${_wpid:-unset}' resolved as pump (recorded pid='${_got:-none}')"; fails=1
+  fi
+  rm -rf "$t6b"
+
   # Scenario 7 (REL-3): resolution DISABLED (CHAIN_PUMP_PID set empty — the
   # old-format seam): claim marker and heartbeat stay contentless, exactly the
   # pre-v3 files an old engine expects.
@@ -203,11 +225,39 @@ _PUMP_PID=""
 if [[ -n "${CHAIN_PUMP_PID+set}" ]]; then
   _PUMP_PID="$(printf '%s' "$CHAIN_PUMP_PID" | tr -dc 0-9)"
 else
-  _anc="$PPID"
-  for _ in $(seq 1 15); do
-    { [[ -n "$_anc" ]] && [[ "$_anc" -gt 1 ]]; } 2>/dev/null || break
-    if grep -qa 'claude' "/proc/$_anc/cmdline" 2>/dev/null; then _PUMP_PID="$_anc"; break; fi
-    _anc="$(sed 's/.*) //' "/proc/$_anc/stat" 2>/dev/null | awk '{print $2}')"
+  # Two passes, precision first. Pass 1 matches the ancestor's EXECUTABLE name
+  # (comm / argv[0] basename); pass 2 is the historical whole-cmdline substring
+  # scan, minus shell wrappers.
+  #
+  # Why shells are excluded (2026-09-03): some harnesses run every Bash tool
+  # call as `bash -c 'source ~/.claude/shell-snapshots/snapshot-bash-*.sh ...'`.
+  # That wrapper's CMDLINE contains the substring 'claude' (from the `.claude`
+  # path) and it lives for exactly ONE tool call, so the old whole-cmdline scan
+  # resolved the pump to it. The engine then found that pid dead the instant the
+  # helper returned and fast-paused the session AWAITING_PUMP on the FIRST
+  # dispatch of every run. Match the program, never a path component.
+  #
+  # A miss is safe and is the designed fallback: _PUMP_PID stays empty, the
+  # ident files revert to the contentless protocol-v2 format, and the engine
+  # keeps both timeout nets. A false POSITIVE is not — it breaks the run.
+  for _pass in strict legacy; do
+    _anc="$PPID"
+    for _ in $(seq 1 15); do
+      { [[ -n "$_anc" ]] && [[ "$_anc" -gt 1 ]]; } 2>/dev/null || break
+      _comm="$(tr -d '\n' < "/proc/$_anc/comm" 2>/dev/null || true)"
+      _argv0="$(tr '\0' '\n' < "/proc/$_anc/cmdline" 2>/dev/null | head -1 || true)"
+      _argv0="${_argv0##*/}"
+      if [[ "$_pass" == strict ]]; then
+        if [[ "$_comm" == *claude* || "$_argv0" == *claude* ]]; then _PUMP_PID="$_anc"; break; fi
+      else
+        case "$_argv0" in
+          bash|sh|dash|zsh|ksh|busybox) ;;  # transient tool-call wrapper — never the pump
+          *) if grep -qa 'claude' "/proc/$_anc/cmdline" 2>/dev/null; then _PUMP_PID="$_anc"; break; fi ;;
+        esac
+      fi
+      _anc="$(sed 's/.*) //' "/proc/$_anc/stat" 2>/dev/null | awk '{print $2}' || true)"
+    done
+    if [[ -n "$_PUMP_PID" ]]; then break; fi
   done
 fi
 _PUMP_HOST=""; _PUMP_STT=""
diff --git a/incredible_auto_dev/scripts/automation/lib/analyze_transcripts.py b/incredible_auto_dev/scripts/automation/lib/analyze_transcripts.py
index cfc0f27a..7b15ed6c 100755
--- a/incredible_auto_dev/scripts/automation/lib/analyze_transcripts.py
+++ b/incredible_auto_dev/scripts/automation/lib/analyze_transcripts.py
@@ -10,8 +10,8 @@ Code session transcript(s) directly:
   <pump-session>/subagents/agent-<id>.jsonl every subagent it dispatched
 
 Usage:
-  analyze_transcripts.py <pump-session.jsonl> [--json]
-  analyze_transcripts.py --compare <A.jsonl> <B.jsonl> [--json]
+  analyze_transcripts.py <pump-session.jsonl> [--json] [--events <file>] [--stall-gap <seconds>]
+  analyze_transcripts.py --compare <A.jsonl> <B.jsonl> [--json] [--events <file>] [--stall-gap <seconds>]
   analyze_transcripts.py --self-test
 
 Pump side: usage-bearing turns (assistant messages carrying `usage`, deduped by
@@ -78,6 +78,118 @@ def _result_len(block):
     return total, image
 
 
+import datetime as _dt
+import re as _re
+
+STALL_GAP_SECONDS = 600.0
+AMBIGUOUS_GAP_SECONDS = 120.0
+_RULE_TAG = _re.compile(r"^guard-[\w-]+: \[(\w+)\]")
+
+
+def _secs(ts):
+    if not ts:
+        return None
+    for fmt, n in (("%Y-%m-%dT%H:%M:%S.%f", 23), ("%Y-%m-%dT%H:%M:%S", 19)):
+        try:
+            return _dt.datetime.strptime(ts[:n], fmt).timestamp()
+        except ValueError:
+            continue
+    return None
+
+
+def classify_result(block, row, gap, stall_gap=STALL_GAP_SECONDS):
+    """Deterministic permission-economics classification (E3/E6). Returns (class, rule_id)."""
+    kind = row.get("toolDenialKind")
+    text = block.get("content") if isinstance(block.get("content"), str) else ""
+    if kind == "permission-rule":
+        if text.startswith("guard-"):
+            m = _RULE_TAG.match(text)
+            return ("hook_deny", m.group(1) if m else "?")
+        if text.startswith("Permission to use"):
+            return ("settings_deny", None)
+        return ("other_deny", None)
+    if kind in ("automode-blocked", "automode-unavailable"):
+        return ("automode_deny", None)
+    if kind == "user-rejected":
+        return ("user_deny", None)
+    tur = row.get("toolUseResult")
+    if isinstance(tur, dict) and (tur.get("timedOutAfterMs") or tur.get("backgroundTaskId") or tur.get("interrupted")):
+        return ("ok_long", None)
+    if gap is not None and gap >= stall_gap:
+        return ("stall", None)
+    if gap is not None and gap >= AMBIGUOUS_GAP_SECONDS:
+        return ("ambiguous_gap", None)
+    return ("ok", None)
+
+
+def _collapse(inp):
+    """Normalize a Bash tool_use input (JSON string) to its whitespace-collapsed command."""
+    try:
+        return " ".join(str(json.loads(inp).get("command", "")).split())
+    except ValueError:
+        return inp
+
+
+def bash_sequence_metrics(bash_seq, bash_verdict):
+    """Sequence-dependent Bash metrics from ISSUE order, after the whole transcript is parsed.
+    Never from result-arrival order, which differs when one turn issues several calls or
+    results land out of order."""
+    out = {"identical_command_retries": 0, "same_rule_retries": 0, "retry_loops": 0}
+    run_len = 0
+    for i, (tid, cmd) in enumerate(bash_seq):
+        cls, rule = bash_verdict.get(tid, ("ok", None))
+        denied = cls.endswith("_deny")
+        run_len = run_len + 1 if denied else 0
+        if run_len == 3:
+            out["retry_loops"] += 1
+        if not denied:
+            continue
+        if cmd and any(c == cmd for _t, c in bash_seq[i + 1:i + 4]):
+            out["identical_command_retries"] += 1
+        if cls == "hook_deny" and i + 1 < len(bash_seq):
+            ncls, nrule = bash_verdict.get(bash_seq[i + 1][0], ("ok", None))
+            if ncls == "hook_deny" and nrule == rule:
+                out["same_rule_retries"] += 1
+    return out
+
+
+def _merge_permissions(dst, src):
+    """Sum every numeric field of a session `permissions` dict into an aggregate,
+    merging `hook_denies` as a rule-id → count Counter."""
+    for k, v in src.items():
+        if k == "hook_denies":
+            c = Counter(dst.get("hook_denies") or {})
+            c.update(v)
+            dst["hook_denies"] = dict(c)
+        else:
+            dst[k] = dst.get(k, 0) + v
+
+
+def default_events_path(transcript_path):
+    """<cache>/iad/hook-events/<project-slug>/<session-id>.jsonl for one transcript — one
+    direct open, never a directory scan."""
+    base = os.path.basename(transcript_path)
+    sid = base[:-6] if base.endswith(".jsonl") else base
+    slug = os.path.basename(os.path.dirname(os.path.abspath(transcript_path)))
+    cache = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
+    return os.path.join(cache, "iad", "hook-events", slug, sid + ".jsonl")
+
+
+def load_events(events_path):
+    """{event: [rows]} + malformed count from ONE session file; None when the file is absent."""
+    if not events_path or not os.path.isfile(events_path):
+        return None
+    out = {"permission_request": [], "hygiene_deny": [], "hygiene_fail_open": [], "malformed": 0}
+    with open(events_path, encoding="utf-8", errors="replace") as fh:
+        for line in fh:
+            try:
+                ev = json.loads(line)
+                out.setdefault(ev.get("event", "?"), []).append(ev)
+            except (ValueError, AttributeError):
+                out["malformed"] += 1
+    return out
+
+
 def _is_compaction(row):
     if row.get("type") == "summary" or row.get("isCompactSummary"):
         return True
@@ -87,7 +199,7 @@ def _is_compaction(row):
     return "This session is being continued from a previous conversation" in text
 
 
-def analyze_session(path):
+def analyze_session(path, stall_gap=STALL_GAP_SECONDS):
     """One transcript file (pump or subagent) → per-message usage + tool stats."""
     seen = {}            # message.id → last usage snapshot (+ model)
     order = []           # message ids in first-seen order
@@ -102,15 +214,69 @@ def analyze_session(path):
     agent_ids = {}       # agentId → agentType
     agent_turn_marks = []  # index (in order) of the turn that issued each Agent call
     compactions = 0
+    # ── permission economics (Task 8 + fix round 1) ──────────────────────────
+    perm = {"hook_denies": Counter(), "settings_denies": 0, "automode_denies": 0, "user_denies": 0,
+            "other_denies": 0, "stalls": 0, "stall_seconds": 0.0, "ambiguous_gaps": 0,
+            "post_denial_tool_turns": 0, "immediate_bash_retries": 0}
+    use_ts, outcomes = {}, {}          # tool_use id → timestamp; tool_use id → (class, gap)
+    bash_seq = []                      # (tool_use id, normalized command) in ISSUE order
+    bash_verdict = {}                  # tool_use id → (class, rule) once its result is seen
+    pending = []                       # tool names of denials awaiting the NEXT COMPLETE assistant
+                                        # message's has_tool/has_bash -- never a single row of it:
+                                        # a real transcript often splits one message (one
+                                        # message.id) across several rows, e.g. text before tool_use
+    cur_mid = None                     # message.id currently being accumulated
+    cur_has_tool = cur_has_bash = False
+    cur_open = False                   # True until `pending` has been resolved against cur_mid
     for row in _rows(path):
         if _is_compaction(row):
             compactions += 1
-        tur = row.get("toolUseResult")
-        if isinstance(tur, dict) and tur.get("agentId") and tur.get("agentType"):
-            agent_ids[str(tur["agentId"])] = str(tur["agentType"])
         msg = row.get("message") or {}
+        tur = row.get("toolUseResult")
+        if isinstance(tur, dict) and tur.get("agentId"):
+            atype = tur.get("agentType")
+            if not atype:
+                # Async/background dispatches often return agentId with no agentType
+                # (confirmed on real transcripts) — derive it from the dispatching
+                # Agent tool_use's own input rather than dropping the subagent.
+                for blk in _blocks(msg):
+                    if isinstance(blk, dict) and blk.get("type") == "tool_result":
+                        tu_name, tu_inp = uses.get(blk.get("tool_use_id"), ("?", ""))
+                        if tu_name == "Agent":
+                            try:
+                                atype = json.loads(tu_inp).get("subagent_type")
+                            except ValueError:
+                                atype = None
+                            break
+                atype = atype or "unknown"
+            agent_ids[str(tur["agentId"])] = str(atype)
         if row.get("type") == "assistant":
+            # Permission economics: does the NEXT COMPLETE assistant message recover from the
+            # pending denial(s)? "Complete" matters -- real transcripts write one content block
+            # per row, and a message often starts with a text row before its tool_use row (same
+            # message.id), so has_tool/has_bash must accumulate across every row of a message,
+            # never rely on a single row of it (fix round 2, finding 4).
             mid = msg.get("id")
+            row_has_tool = any(isinstance(b, dict) and b.get("type") == "tool_use" for b in _blocks(msg))
+            row_has_bash = any(isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Bash"
+                                for b in _blocks(msg))
+            if mid != cur_mid:
+                # A different message.id has appeared, so cur_mid's message is now complete --
+                # resolve `pending` (denials from BEFORE cur_mid started) against its FULL
+                # accumulated flags, never a single row's. Skip if already resolved (cur_open
+                # False): that happens when a "user" row closed cur_mid first (the common case,
+                # whenever cur_mid issued at least one tool call) -- resolving again here would
+                # wrongly score cur_mid's OWN just-issued denial against cur_mid's OWN flags,
+                # which trivially always "recovers" (cur_mid obviously contains a tool_use).
+                if cur_open:
+                    for entry in pending:
+                        perm["post_denial_tool_turns"] += cur_has_tool
+                        if entry == "Bash":
+                            perm["immediate_bash_retries"] += cur_has_bash
+                    pending = []
+                cur_mid, cur_has_tool, cur_has_bash, cur_open = mid, False, False, True
+            cur_has_tool = cur_has_tool or row_has_tool
+            cur_has_bash = cur_has_bash or row_has_bash
             usage = msg.get("usage")
             if mid and isinstance(usage, dict):
                 if mid not in seen:
@@ -125,12 +291,44 @@ def analyze_session(path):
                     uses[b.get("id")] = (name, inp)
                     tool_calls[name] += 1
                     tool_in_bytes[name] += len(inp)
+                    use_ts[b["id"]] = row.get("timestamp")
+                    if name == "Bash":
+                        bash_seq.append((b["id"], _collapse(inp)))
                     if name == "Agent" and mid:
                         agent_turn_marks.append(len(order) - 1 if mid in seen else len(order))
         elif row.get("type") == "user":
+            # A "user" row (a tool_result) proves cur_mid's assistant rows are done arriving --
+            # this is the earliest point cur_mid's flags are final, so resolve `pending` here
+            # too (a message with a tool call almost always gets its result before the next
+            # assistant message begins, so this fires before the mid-change branch above does).
+            if cur_open:
+                for entry in pending:
+                    perm["post_denial_tool_turns"] += cur_has_tool
+                    if entry == "Bash":
+                        perm["immediate_bash_retries"] += cur_has_bash
+                pending = []
+                cur_open = False
             for b in _blocks(msg):
                 if isinstance(b, dict) and b.get("type") == "tool_result":
                     name, inp = uses.get(b.get("tool_use_id"), ("?", ""))
+                    t0, t1 = _secs(use_ts.get(b.get("tool_use_id"))), _secs(row.get("timestamp"))
+                    gap = (t1 - t0) if (t0 is not None and t1 is not None) else None
+                    cls, rule = classify_result(b, row, gap, stall_gap)
+                    outcomes[b.get("tool_use_id")] = (cls, gap)
+                    denied = cls.endswith("_deny")
+                    if cls == "hook_deny":
+                        perm["hook_denies"][rule] += 1
+                    elif denied:
+                        perm[cls.replace("deny", "denies")] += 1
+                    elif cls == "stall":
+                        perm["stalls"] += 1
+                        perm["stall_seconds"] += gap
+                    elif cls == "ambiguous_gap":
+                        perm["ambiguous_gaps"] += 1
+                    if name == "Bash":
+                        bash_verdict[b.get("tool_use_id")] = (cls, rule)
+                    if denied:
+                        pending.append(name)
                     length, image = _result_len(b)
                     if not image and name == "Read":
                         try:
@@ -145,6 +343,14 @@ def analyze_session(path):
                         res_bytes[name] += length
                         res_count[name] += 1
                     top.append((length, name, inp[:80]))
+    if cur_open:
+        # End of transcript with cur_mid's message fully accumulated but never "closed" by a
+        # user row or a later message (e.g. the transcript ends right after a multi-row message
+        # whose only tool_use sits in a later row -- see the split-message fixture below).
+        for entry in pending:
+            perm["post_denial_tool_turns"] += cur_has_tool
+            if entry == "Bash":
+                perm["immediate_bash_retries"] += cur_has_bash
     usage_tot = Counter()
     models = Counter()
     for mid in order:
@@ -158,6 +364,11 @@ def analyze_session(path):
     gaps = [b - a for a, b in zip(agent_turn_marks, agent_turn_marks[1:])]
     turns_per_dispatch = (sum(gaps) / len(gaps)) if gaps else (turns / dispatches if dispatches else 0.0)
     top.sort(key=lambda t: -t[0])
+    # Diagnostic (fix round 2, finding 5): a Bash tool_use with no tool_result row at all (the
+    # session was killed on a dialog before the result ever arrived) previously counted as
+    # nothing -- surface it instead of letting it vanish.
+    perm["unresolved_tool_uses"] = sum(1 for tid, _cmd in bash_seq if tid not in bash_verdict)
+    perm.update(bash_sequence_metrics(bash_seq, bash_verdict))
     return {
         "path": path,
         "turns": turns,
@@ -174,23 +385,25 @@ def analyze_session(path):
         "agent_dispatches": dispatches,
         "turns_per_dispatch": round(turns_per_dispatch, 2),
         "agent_ids": agent_ids,
+        "permissions": {**perm, "hook_denies": dict(perm["hook_denies"])},
+        "outcomes": outcomes,
     }
 
 
-def analyze_pump(path):
-    pump = analyze_session(path)
+def analyze_pump(path, events_path=None, stall_gap=STALL_GAP_SECONDS):
+    pump = analyze_session(path, stall_gap=stall_gap)
     sub_dir = os.path.join(path[:-6] if path.endswith(".jsonl") else path, "subagents")
     per_type = {}
     for aid, atype in pump["agent_ids"].items():
         sp = os.path.join(sub_dir, f"agent-{aid}.jsonl")
         if not os.path.isfile(sp):
             continue
-        s = analyze_session(sp)
+        s = analyze_session(sp, stall_gap=stall_gap)
         d = per_type.setdefault(atype, {"invocations": 0, "turns": 0, "output_tokens": 0,
                                         "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                                         "result_bytes": Counter(), "result_count": Counter(),
                                         "tool_calls": Counter(), "image_results": 0, "image_bytes": 0,
-                                        "top_results": []})
+                                        "top_results": [], "permissions": {}, "outcomes": {}})
         d["invocations"] += 1
         d["turns"] += s["turns"]
         d["output_tokens"] += s["usage"].get("output_tokens", 0)
@@ -202,6 +415,8 @@ def analyze_pump(path):
         d["image_results"] += s["image_results"]
         d["image_bytes"] += s["image_bytes"]
         d["top_results"] = sorted(d["top_results"] + s["top_results"], key=lambda t: -t["bytes"])[:5]
+        _merge_permissions(d["permissions"], s["permissions"])
+        d["outcomes"].update(s["outcomes"])
     for d in per_type.values():
         n = d["invocations"] or 1
         d["turns_per_inv"] = round(d["turns"] / n, 1)
@@ -211,10 +426,48 @@ def analyze_pump(path):
         d["result_count"] = dict(d["result_count"])
         d["tool_calls"] = dict(d["tool_calls"])
     del pump["agent_ids"]
-    return {"pump": pump, "subagents": per_type}
-
-
-def render_text(rep):
+    per_type_reports = list(per_type.values())
+    all_outcomes = dict(pump["outcomes"])
+    for d in per_type_reports:
+        all_outcomes.update(d["outcomes"])
+    ev = load_events(events_path or default_events_path(path))
+    prompts = ev["permission_request"] if ev else []
+    outc = Counter()
+    for e in prompts:
+        cls, gap = all_outcomes.get(e.get("tool_use_id"), ("unmatched", None))
+        outc["user_deny" if cls == "user_deny" else "unmatched" if cls == "unmatched"
+             else "allowed_after_wait" if (gap or 0) >= AMBIGUOUS_GAP_SECONDS else "allowed_fast"] += 1
+    fo = Counter(e.get("reason", "?") for e in (ev["hygiene_fail_open"] if ev else []))
+    pump["permissions"].update({"human_prompts": (len(prompts) if ev else None), "prompt_outcomes": dict(outc),
+                                "fail_opens": dict(fo), "malformed_event_rows": (ev["malformed"] if ev else None)})
+    for r in [pump] + per_type_reports:
+        r.pop("outcomes", None)
+    # Session-wide totals (fix round 1, finding 3): pump + every subagent type, summed
+    # field-by-field (hook_denies merged as a Counter); human_prompts/prompt_outcomes/
+    # fail_opens/malformed_event_rows are pump-only and simply carried through, since no
+    # subagent-level `permissions` dict ever carries those keys.
+    permissions_total = dict(pump["permissions"])
+    for d in per_type_reports:
+        _merge_permissions(permissions_total, d["permissions"])
+    return {"pump": pump, "subagents": per_type, "permissions_total": permissions_total}
+
+
+def _perm_line(perm, label="permissions", stall_gap=STALL_GAP_SECONDS):
+    return ("  %s: human_prompts=%s stalls>%ds=%d stall_seconds=%.0f hook_denies=%s "
+            "identical_command_retries=%d retry_loops=%d same_rule_retries=%d "
+            "post_denial_tool_turns=%d immediate_bash_retries=%d unresolved_tool_uses=%d "
+            "settings_denies=%d automode_denies=%d user_denies=%d other_denies=%d "
+            "fail_opens=%s malformed_event_rows=%s") % (
+        label, perm.get("human_prompts"), int(stall_gap), perm.get("stalls", 0), perm.get("stall_seconds", 0.0),
+        perm.get("hook_denies", {}), perm.get("identical_command_retries", 0), perm.get("retry_loops", 0),
+        perm.get("same_rule_retries", 0), perm.get("post_denial_tool_turns", 0),
+        perm.get("immediate_bash_retries", 0), perm.get("unresolved_tool_uses", 0),
+        perm.get("settings_denies", 0), perm.get("automode_denies", 0),
+        perm.get("user_denies", 0), perm.get("other_denies", 0), perm.get("fail_opens", {}),
+        perm.get("malformed_event_rows"))
+
+
+def render_text(rep, stall_gap=STALL_GAP_SECONDS):
     p = rep["pump"]
     u = p["usage"]
     out = []
@@ -232,11 +485,14 @@ def render_text(rep):
         rc = p["result_count"].get(name, 0)
         ar = p["result_bytes"].get(name, 0) // max(1, rc)
         out.append(f"    {name:34s} {n:5d}  {ai:7d}  {ar:8d}")
+    out.append(_perm_line(p.get("permissions", {}), stall_gap=stall_gap))
+    out.append(_perm_line(rep.get("permissions_total", {}), "permissions_total", stall_gap=stall_gap))
     out.append("SUBAGENTS")
     for atype, d in sorted(rep["subagents"].items(), key=lambda kv: -kv[1]["cache_read_input_tokens"]):
         out.append(f"  {atype}: inv={d['invocations']} turns/inv={d['turns_per_inv']} "
                    f"output/inv={d['output_per_inv']:,} cache_read/inv={d['cache_read_per_inv']:,} "
                    f"image reads={d['image_results']} ({d['image_bytes']//1024} KB)")
+        out.append(_perm_line(d.get("permissions", {}), stall_gap=stall_gap))
         tot = sum(d["result_bytes"].values()) or 1
         for name, b in sorted(d["result_bytes"].items(), key=lambda kv: -kv[1])[:6]:
             out.append(f"      {name:30s} calls/inv={d['tool_calls'].get(name,0)/d['invocations']:6.1f} "
@@ -254,10 +510,28 @@ def compare(a, b):
                "pump_output": p["usage"].get("output_tokens", 0),
                "pump_cache_read_per_dispatch": (p["usage"].get("cache_read_input_tokens", 0) // p["agent_dispatches"]) if p["agent_dispatches"] else 0,
                "compactions": p["compactions"]}
+        # Session-wide (pump + every subagent type), not pump-only — a --compare run
... [diff_bound] incredible_auto_dev/scripts/automation/lib/analyze_transcripts.py: 223 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh b/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh
index 0381fad9..fecadbd2 100644
--- a/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh
+++ b/incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh
@@ -279,13 +279,17 @@ _interactive_invoke() {
     prompt+=$'\n\n'"Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR=\"$CHAIN_TMPDIR\" TMP=\"$CHAIN_TMPDIR\" TEMP=\"$CHAIN_TMPDIR\""
   fi
 
-  # CTX-8: on this backend the subagent's system prompt IS its rendered
-  # .claude/agents/<name>.md definition — stop it re-Reading its own 8-20 KB
-  # file every dispatch. Conditional on the pointer line being present so
-  # non-agent prompts (two-key confirms, ad-hoc dispatches — and the
-  # self-test's byte-exact round-trips) pass through untouched. Headless
-  # prompts keep the pointer as-is (there the file is NOT pre-loaded).
+  # Path-safety bridge (2026-09-04, supersedes the 2026-09-03 search-path note):
+  # interactive subagents run under the PUMP session's permission checker, where a
+  # few command shapes escalate to a human approval nobody can answer (see
+  # .claude/core.md § File Paths in Bash and hooks/lib/read_path_hygiene.py).
+  # The hook is the deterministic backstop; this note is first-line prevention,
+  # costs no pump turn, and travels inside the prompt file on the >8 KB path.
+  # Gated on the agent-pointer line so two-key confirms, ad-hoc dispatches and
+  # the self-test's byte-exact round-trips pass through untouched. CTX-8 rides
+  # the same gate.
   if [[ "$prompt" == *"Agent instructions: .claude/agents/"* ]]; then
+    prompt+=$'\n\n'"Path-safety note (machine-enforced — a denied command returns the rewrite; rewrite it, never retry it verbatim): use repo-relative paths from the repo root. Never root a recursive read at \`.\`, \`~\` or an absolute directory (\`grep -rn P apps/backend/app/ docs/\`, not \`grep -rn P .\`; filter flags do not help). After a \`cd\` in the same command, never read a relative path, mutate a file (\`sed -i\`/\`cp\`/\`mv\`/\`rm\`/\`mkdir\`/\`touch\`), redirect output to a file, or run \`git\`: edit files with the Edit/Write tools and run everything else from the repo root. \`cd\` only for a command that needs the cwd and does none of those (pytest/npm/tsc). Each of these shapes stalls this dispatch on a human approval it cannot get. Full rule: \`.claude/core.md\` § File Paths in Bash."
     prompt+=$'\n\n'"Note: your agent definition (the .claude/agents/*.md file named above) is already loaded as your system prompt — do not Read it again; treat its 'read this first' pointer as satisfied."
   fi
 
@@ -1174,6 +1178,42 @@ _interactive_dispatch_self_test() {
   fi
   rm -rf "$d"
 
+  # Test 24 (2026-09-03) — path-safety note: a prompt carrying the
+  # `Agent instructions: .claude/agents/` pointer gets the path-safety note
+  # appended; every other prompt (two-key confirms, ad-hoc dispatches) passes
+  # through untouched. The note now covers every hook-enforced shape after a
+  # `cd`: a relative read, `sed -i`, an output redirect, and `git` -- each of
+  # which would otherwise stall the dispatch on a human approval prompt.
+  _sp_seen() {   # round-trip one prompt, echo how many times the note appears
+    local dd pp pr; dd="$(mktemp -d)"; pr="$1"
+    export CHAIN_DISPATCH_DIR="$dd"
+    ( for _ in $(seq 1 60); do
+        local rr; rr="$(find "$dd" -maxdepth 1 -name 'req.*.ready' 2>/dev/null | head -1)"
+        if [[ -n "$rr" ]]; then
+          _n=$(grep -c 'Path-safety note' "$rr" 2>/dev/null)
+          if [[ "$_n" == "1" ]] && ! { grep -q 'sed -i' "$rr" && grep -q 'redirect output' "$rr" && grep -q 'relative path' "$rr"; }; then _n=incomplete; fi
+          grep -q 'Search-path note:' "$rr" 2>/dev/null && _n=stale
+          echo "$_n" > "$dd/count"
+          echo 0 > "${rr%.ready}.res"; break
+        fi
+        sleep 0.1
+      done ) &
+    pp=$!
+    CHAIN_DISPATCH_POLL_SECONDS=0.2 CHAIN_PUMP_HEARTBEAT_TIMEOUT=3600 \
+      _interactive_invoke -p "$pr" >/dev/null 2>&1 || true
+    wait "$pp" 2>/dev/null || true
+    cat "$dd/count" 2>/dev/null || echo missing
+    rm -rf "$dd"
+  }
+  _sp_agent="$(_sp_seen "do the work. Agent instructions: .claude/agents/developer.md")"
+  _sp_plain="$(_sp_seen "two-key confirm: is this really GOAL_ACHIEVED?")"
+  unset -f _sp_seen
+  if [[ "$_sp_agent" == "1" && "$_sp_plain" == "0" ]]; then
+    echo "  PASS interactive-dispatch: path-safety note reaches agent dispatches only (agent=$_sp_agent, plain=$_sp_plain)"
+  else
+    echo "  FAIL interactive-dispatch: path-safety note (agent=$_sp_agent expected 1, plain=$_sp_plain expected 0)"; fails=1
+  fi
+
   if [[ "$fails" -eq 0 ]]; then echo "interactive-dispatch self-test: OK"; else echo "interactive-dispatch self-test: FAILED"; fi
   return "$fails"
 }
diff --git a/incredible_auto_dev/scripts/automation/permission-oracle.sh b/incredible_auto_dev/scripts/automation/permission-oracle.sh
new file mode 100755
index 00000000..c6c91a82
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/permission-oracle.sh
@@ -0,0 +1,29 @@
+#!/usr/bin/env bash
+# permission-oracle.sh — native-alignment probe for hooks/lib/read_path_hygiene.py.
+# Operator-run; spends one small Haiku call per manifest entry (G9). Runs ONLY inside a
+# throwaway sandbox tree of dummy files; mutation fixtures are safe if they unexpectedly
+# execute. The probe list is `read_path_hygiene.py --oracle-manifest` (one source, no drift).
+set -euo pipefail
+REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
+SB="$(mktemp -d "${TMPDIR:-/tmp}/iad-oracle.XXXXXX")"
+trap 'rm -rf "$SB"' EXIT
+mkdir -p "$SB/apps/backend/tests" "$SB/apps/backend/app" "$SB/docs"
+printf 'a = 1\n' > "$SB/apps/backend/app/main.py"
+printf 'a = 1\n' > "$SB/apps/backend/tests/test_x.py"
+printf 'scratch\n' > "$SB/apps/backend/tests/scratch.txt"
+printf '# goal\n' > "$SB/docs/goal.md"
+printf 'DUMMY=1\n' > "$SB/.env"                      # lets the user-level Read(**/.env) deny rule apply
+git -C "$SB" init -q && git -C "$SB" add -A && git -C "$SB" -c user.email=o@x -c user.name=o commit -qm init
+mapfile -t ALLOW < <(jq -r '.permissions.allow[]' "$REPO_ROOT/.claude/settings.json")
+probe() {   # $1 id  $2 command  → "<id> NATIVE_ASK|native_allow|INCONCLUSIVE <command>"
+  local out
+  out=$(cd "$SB" && claude -p --model haiku --max-turns 2 --permission-mode dontAsk \
+        --settings '{"disableAllHooks":true}' --allowedTools "${ALLOW[@]}" --output-format json \
+        "Run exactly this Bash command once, then stop. Do not modify it and do not run anything else: $2" 2>/dev/null || true)
+  if printf '%s' "$out" | jq -e '(.permission_denials // []) | length > 0' >/dev/null 2>&1; then echo "$1 NATIVE_ASK   $2"
+  elif printf '%s' "$out" | jq -e '.num_turns' >/dev/null 2>&1; then echo "$1 native_allow $2"
+  else echo "$1 INCONCLUSIVE $2"; fi
+}
+while IFS=$'\t' read -r oid cmd; do
+  probe "$oid" "${cmd//\{SB\}/$SB}"
+done < <(python3 "$REPO_ROOT/hooks/lib/read_path_hygiene.py" --oracle-manifest)
diff --git a/incredible_auto_dev/scripts/automation/run-evals.sh b/incredible_auto_dev/scripts/automation/run-evals.sh
index 744c7701..42337649 100755
--- a/incredible_auto_dev/scripts/automation/run-evals.sh
+++ b/incredible_auto_dev/scripts/automation/run-evals.sh
@@ -22,6 +22,10 @@ set -euo pipefail
 REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
 cd "$REPO_ROOT"
 
+# A __pycache__ under hooks/lib/ would be mirrored into .claude/hooks/ by
+# sync-cli-assets.py and trip the drift gate — never let a plain eval run leave one behind.
+export PYTHONDONTWRITEBYTECODE=1
+
 # Keep the suite out of the MACHINE's forensic state. Several tests drive real
 # dispatch paths, and hg_event writes to a machine-global ledger by design — so
 # an unredirected eval run buries the record of what the machine was actually
@@ -29,7 +33,10 @@ cd "$REPO_ROOT"
 # postmortem reader is only as useful as that ledger is honest.
 export HOST_GUARD_EVENTS_FILE="${TMPDIR:-/tmp}/iad-evals-events.$$.jsonl"
 export HOST_GUARD_POSTMORTEM_DIR="${TMPDIR:-/tmp}/iad-evals-postmortems.$$"
-trap 'rm -rf "$HOST_GUARD_EVENTS_FILE" "$HOST_GUARD_EVENTS_FILE.1" "$HOST_GUARD_POSTMORTEM_DIR" 2>/dev/null || true' EXIT
+# Same isolation for the hook-events writer (hook_events.py): a real eval run must not bury
+# per-session hygiene_deny/hygiene_fail_open records under synthetic test events either.
+export IAD_HOOK_EVENTS_FILE="${TMPDIR:-/tmp}/iad-evals-hook-events.$$.jsonl"
+trap 'rm -rf "$HOST_GUARD_EVENTS_FILE" "$HOST_GUARD_EVENTS_FILE.1" "$HOST_GUARD_POSTMORTEM_DIR" "$IAD_HOOK_EVENTS_FILE" 2>/dev/null || true' EXIT
 
 VERBOSE=false
 [[ "${1:-}" == "--verbose" ]] && VERBOSE=true
@@ -174,6 +181,10 @@ _run_self_test scripts/automation/lib/goal_gate.py self-test
 _run_self_test scripts/automation/lib/browser_tabs.py --self-test
 # Pump-side economics + subagent context composition from Claude Code transcripts (TOKEN-12).
 _run_self_test scripts/automation/lib/analyze_transcripts.py --self-test
+# Path-hygiene detector brain (Rules A/B/C, operand tables, tokenizer normalization, unknown/fail-open, oracle manifest).
+_run_self_test hooks/lib/read_path_hygiene.py --self-test
+# Session-scoped hook-event writer (privacy-safe schema, append-safe under flock, concurrent-writer stress).
+_run_self_test hooks/lib/hook_events.py --self-test
 _run_self_test scripts/automation/lib/goal_lint.py self-test
 _run_self_test scripts/automation/lib/scan_diff.py self-test
 _run_self_test scripts/automation/lib/diff_bound.py self-test
@@ -236,6 +247,16 @@ if bash .claude/hooks/guard-dangerous-commands.sh "for d in x; do rm -rf /tmp/ia
 else
   _fail "hook: guard-dangerous-commands wrongly blocks loop-wrapped /tmp cleanup"
 fi
+if bash .claude/hooks/guard-dangerous-commands.sh 'pytest -q > /dev/null 2>&1' >/dev/null 2>&1; then
+  _pass "hook: guard-dangerous-commands allows '> /dev/null' (space before the target)"
+else
+  _fail "hook: guard-dangerous-commands false-positives on '> /dev/null'"
+fi
+if bash .claude/hooks/guard-dangerous-commands.sh 'cat image.img > /dev/sda' >/dev/null 2>&1; then
+  _fail "hook: guard-dangerous-commands let a device write through"
+else
+  _pass "hook: guard-dangerous-commands still blocks a device write ('> /dev/sda')"
+fi
 # SEC-7 Claude-backend protocol: the command arrives as PreToolUse JSON on
 # stdin (argv empty — $CLAUDE_TOOL_INPUT_COMMAND never existed) and the
 # decision returns as hookSpecificOutput deny-JSON on stdout with exit 0.
@@ -255,6 +276,115 @@ if [[ $_g_rc -eq 0 && -z "$_g_out" ]]; then
 else
   _fail "hook: guard-dangerous-commands (stdin/Claude) noisy or non-zero on benign command (rc=$_g_rc)"
 fi
+# guard-read-path-hygiene: enforces core.md § "File Paths in Bash" so a dispatch
+# never stalls on an approval prompt it cannot get. The two DENY cases are the
+# verbatim commands that stalled goal session contract-pack-v0 iter 1 (developer)
+# and a tapeology reviewer. The ALLOW cases are the carve-outs core.md keeps
+# legal — `cd` before a non-read (pytest/npm/tsc), a piped read with no path
+# argument, and a recursive search already rooted at concrete subdirectories.
+_rp_deny=(
+  'cd /home/x/contracts && grep -rn "book_snapshot" workstation_contracts/*.py | head -30'
+  'cd /home/x/apps/backend && grep -n "PROFILE_DEFAULT" app/config.py | head -5'
+  'grep -rn PATTERN .'
+  'cd docs && sed -n "1,50p" goal.md'
+  $'cd /home/x/apps/backend/tests && \\\nsed -i "s/a/b/" test_x.py\ngrep -n b test_x.py'
+  'cd apps/backend && cp a.py b.py'
+  'cd apps/backend && pytest -q > /tmp/out.log'
+  'cd apps/backend && git status'
+  $'cd apps/backend\ngrep -n foo app/main.py'
+  # Rule C3 is unconditional on the git subcommand (docs: even a read-only `git
+  # diff` after `cd` can execute that directory's hooks) -- this used to allow
+  # under Rule A alone (piped read, no path operand) but now correctly denies.
+  'cd x && git diff | grep foo'
+)
+_rp_allow=(
+  'cd apps/backend && pytest -q'
+  'cd apps/frontend && npm run build'
+  'git diff | grep foo'
+  'grep -rn PATTERN apps/backend/app/ apps/frontend/src/'
+  'grep -n "x" apps/backend/app/main.py'
+  'cd x && ls -la'
+  # Redirections are not read arguments. `2>/dev/null` on almost every command
+  # in this repo tokenized as a path and false-positived the guard on its first
+  # live call; strip_redirects() fixes it and these lock the regression in.
+  'grep -rln PATTERN incredible_auto_dev/policy/ incredible_auto_dev/hooks/ 2>/dev/null'
+  'grep -rn PATTERN apps/ >/dev/null 2>&1'
+  'cat docs/goal.md > /tmp/copy.md'
+  'python3 x.py > /tmp/out.txt 2>&1'
+  'cd apps/backend && pytest -q | tee /tmp/out.log'
+  'cd apps/backend && ls'
+  'cd apps/backend && grep -n foo /home/x/apps/backend/app/main.py'
+  'cd apps/backend && grep -m 1 foo'
+  'cd apps/backend && head -n 20 app/main.py'
+  $'cd apps/backend && python3 - <<\'EOF\'\nimport os\nEOF'
+)
+_rp_bad=0
+for _c in "${_rp_deny[@]}"; do
+  bash .claude/hooks/guard-read-path-hygiene.sh "$_c" >/dev/null 2>&1 && { _rp_bad=1; echo "    missed deny: $_c"; }
+done
+if [[ $_rp_bad -eq 0 ]]; then
+  _pass "hook: guard-read-path-hygiene blocks all ${#_rp_deny[@]} approval-stalling read patterns"
+else
+  _fail "hook: guard-read-path-hygiene let an approval-stalling read through"
+fi
+_rp_bad=0
+for _c in "${_rp_allow[@]}"; do
+  bash .claude/hooks/guard-read-path-hygiene.sh "$_c" >/dev/null 2>&1 || { _rp_bad=1; echo "    false positive: $_c"; }
+done
+if [[ $_rp_bad -eq 0 ]]; then
+  _pass "hook: guard-read-path-hygiene allows all ${#_rp_allow[@]} legitimate cd/read forms"
+else
+  _fail "hook: guard-read-path-hygiene false-positives on a legitimate command"
+fi
+_rp_rc=0
+_rp_out=$(printf '%s' '{"tool_input":{"command":"cd apps/backend && grep -n \"X\" app/config.py"}}' | bash .claude/hooks/guard-read-path-hygiene.sh 2>/dev/null) || _rp_rc=$?
+if [[ $_rp_rc -eq 0 ]] && grep -q '"permissionDecision":"deny"' <<<"$_rp_out"; then
+  _pass "hook: guard-read-path-hygiene (stdin/Claude) denies cd+read via JSON, exit 0"
+else
+  _fail "hook: guard-read-path-hygiene (stdin/Claude) missing deny JSON for cd+read (rc=$_rp_rc)"
+fi
+_rp_rc=0
+_rp_out=$(printf '%s' '{"tool_input":{"command":"pytest -q apps/backend/tests/"}}' | bash .claude/hooks/guard-read-path-hygiene.sh 2>/dev/null) || _rp_rc=$?
+if [[ $_rp_rc -eq 0 && -z "$_rp_out" ]]; then
+  _pass "hook: guard-read-path-hygiene (stdin/Claude) passes a benign command silently"
+else
+  _fail "hook: guard-read-path-hygiene (stdin/Claude) noisy or non-zero on benign command (rc=$_rp_rc)"
+fi
+# Rule C over the stdin/Claude protocol: the deny JSON carries a rule-tagged reason.
+_rp_rc=0
+_rp_out=$(printf '%s' '{"session_id":"evals","agent_id":"a1","agent_type":"developer","tool_use_id":"t1","tool_name":"Bash","tool_input":{"command":"cd apps/backend && sed -i \"s/a/b/\" x.py"}}' | bash .claude/hooks/guard-read-path-hygiene.sh 2>/dev/null) || _rp_rc=$?
+if [[ $_rp_rc -eq 0 ]] && grep -q '"permissionDecision":"deny"' <<<"$_rp_out" && grep -q 'guard-read-path-hygiene: \[C1\]' <<<"$_rp_out"; then
+  _pass "hook: guard-read-path-hygiene (stdin/Claude) denies cd+sed -i with a rule-tagged reason"
+else
+  _fail "hook: guard-read-path-hygiene (stdin/Claude) Rule C deny JSON missing (rc=$_rp_rc out=${_rp_out:0:80})"
+fi
+# The deny is recorded as an attributed, privacy-safe hygiene_deny event (no command text, no hash).
+if [[ -s "$IAD_HOOK_EVENTS_FILE" ]] && grep -q '"event":"hygiene_deny"' "$IAD_HOOK_EVENTS_FILE" && grep -q '"agent_type":"developer"' "$IAD_HOOK_EVENTS_FILE" && grep -q '"rule":"C1"' "$IAD_HOOK_EVENTS_FILE" && ! grep -q 's/a/b/\|cmd_sha\|cmd_raw' "$IAD_HOOK_EVENTS_FILE"; then
+  _pass "hook: guard-read-path-hygiene appends an attributed hygiene_deny event without command text"
+else
+  _fail "hook: guard-read-path-hygiene hygiene_deny event missing or leaks the command ($IAD_HOOK_EVENTS_FILE)"
+fi
+# Unknown syntax fails open AND is logged: a loop passes silently with a complex:control-flow event.
+_rp_rc=0
+_rp_out=$(printf '%s' '{"session_id":"evals","tool_input":{"command":"for d in a; do cd $d && grep -n x y.py; done"}}' | bash .claude/hooks/guard-read-path-hygiene.sh 2>/dev/null) || _rp_rc=$?
+if [[ $_rp_rc -eq 0 && -z "$_rp_out" ]] && grep -q '"reason":"complex:control-flow"' "$IAD_HOOK_EVENTS_FILE"; then
+  _pass "hook: guard-read-path-hygiene passes unknown syntax to the native checker and logs hygiene_fail_open"
+else
+  _fail "hook: guard-read-path-hygiene unknown-syntax fail-open not instrumented (rc=$_rp_rc out=${_rp_out:0:60})"
+fi
+# Registration must verify EVENT and MATCHER, not just the basename.
+if jq -e '.hooks.PreToolUse[] | select(.matcher=="Bash") | .hooks[] | select(.command|contains("guard-read-path-hygiene.sh"))' .claude/settings.json >/dev/null 2>&1; then
+  _pass "hook: guard-read-path-hygiene is registered as a PreToolUse Bash matcher"
+else
+  _fail "hook: guard-read-path-hygiene is NOT registered as PreToolUse/Bash in .claude/settings.json"
+fi
+# permission-oracle.sh must stay wired to the detector's oracle manifest (Task 1
+# --oracle-manifest is the single source; the oracle script carries no probe list of its own).
+if grep -q -- '--oracle-manifest' scripts/automation/permission-oracle.sh && [[ "$(python3 hooks/lib/read_path_hygiene.py --oracle-manifest | cut -f1 | sort | uniq -d | wc -l)" == "0" ]] && [[ "$(python3 hooks/lib/read_path_hygiene.py --oracle-manifest | wc -l)" -ge 15 ]]; then
+  _pass "oracle: permission-oracle.sh probes the detector's manifest (unique ids, >= 15 entries)"
+else
+  _fail "oracle: permission-oracle.sh and the detector's oracle manifest have drifted"
+fi
 # Install gate, Claude path. NOTE: the deny case appends a real record to
 # reports/security/install-decisions.jsonl per eval run (the hook path never
 # passes --dry-run) — accepted audit-trail noise.
@@ -305,6 +435,21 @@ if (cd "$(mktemp -d)" && bash "$OLDPWD/.claude/hooks/on-stop-check-artifacts.sh"
 else
   _fail "hook: on-stop-check-artifacts errored with no runs/"
 fi
+# PermissionRequest recorder (Task 7, log-only stage 1): no decision, no raw
+# command or suggestion text — just an attributed permission_request event so
+# lib/analyze_transcripts.py can count human prompts deterministically.
+_pr_rc=0
+_pr_out=$(printf '%s' '{"hook_event_name":"PermissionRequest","session_id":"evals","agent_id":"a2","agent_type":"qa","tool_use_id":"t9","tool_name":"Bash","permission_mode":"auto","tool_input":{"command":"cd apps && install -m 755 a secret-token-123"},"permission_suggestions":[{"type":"addRules","rules":[{"toolName":"Bash","ruleContent":"install *"}]}]}' | bash .claude/hooks/permission-request-log.sh 2>/dev/null) || _pr_rc=$?
+if [[ $_pr_rc -eq 0 && -z "$_pr_out" ]] && grep -q '"event":"permission_request"' "$IAD_HOOK_EVENTS_FILE" && grep -q '"agent_type":"qa"' "$IAD_HOOK_EVENTS_FILE" && grep -q '"suggestion_types":\["addRules"\]' "$IAD_HOOK_EVENTS_FILE" && ! grep -q 'secret-token-123\|ruleContent\|cmd_sha' "$IAD_HOOK_EVENTS_FILE"; then
+  _pass "hook: permission-request-log records a would-be prompt (no decision, no raw command, no raw suggestions)"
+else
+  _fail "hook: permission-request-log (rc=$_pr_rc out=${_pr_out:0:60})"
+fi
+if jq -e '.hooks.PermissionRequest[] | .hooks[] | select(.command|contains("permission-request-log.sh"))' .claude/settings.json >/dev/null 2>&1; then
+  _pass "hook: permission-request-log is registered on PermissionRequest"
+else
+  _fail "hook: permission-request-log is NOT registered on PermissionRequest"
+fi
 
 # Model config has ONE source: model_tier in agent.yaml → config/model-tiers.yaml.
 # A model_override reappearing means someone re-pinned a concrete id — allowed
diff --git a/incredible_auto_dev/scripts/automation/tmp-doctor.sh b/incredible_auto_dev/scripts/automation/tmp-doctor.sh
index 00ac04a8..3f50c932 100755
--- a/incredible_auto_dev/scripts/automation/tmp-doctor.sh
+++ b/incredible_auto_dev/scripts/automation/tmp-doctor.sh
@@ -137,6 +137,11 @@ case "$MODE" in
       rm -rf -- "$RETIRED_BENCH_ROOT" 2>/dev/null || true
       echo "[tmp-doctor] purged retired root $RETIRED_BENCH_ROOT"
     fi
+    # Retention sweep for the permission-economics events ledger (see
+    # docs/goal-mode-telemetry.md "Permission economics" section): session-scoped
+    # hook-events files older than 30 days are stale by construction (the session
+    # is long over), so age them out here rather than let them accumulate forever.
+    find "${XDG_CACHE_HOME:-$HOME/.cache}/iad/hook-events" -name '*.jsonl' -mtime +30 -delete 2>/dev/null || true
     rc=0
     chain_tmp_disk_guard --enforce || rc=$?
     echo "[tmp-doctor] aggressive sweep done."
```
