"""Observation Contract v1 -- Binding Execution Order step 3 (J-03; docs/goal.md).

Covers this iteration's MANAGER-side machinery: the per-watch source/session descriptor
(``WatchManager._record_source`` / ``SourceDescriptor``, recorded once at each ``watch*``
constructor and returned alongside the atomic settled pair by ``get_observation_source``), the
``_settle`` identity-check fix (the reviewer's carried-forward MINOR -- a stale/superseded
engine's late write must never clobber a fresher watch's settled pair), and the honesty of the
seven ``lifecycle.stream_status`` values plus the three feed bases. TC references below match
the iteration spec (``docs/phases/goal-observation-contract-iter-3.md``) and goal.md's J-03
Steps.6 list. Every guard/law test ships a named ``test_counterexample_*`` proving it can fail.
No test needs a running uvicorn server or network access -- the route
(``GET /tape/{ticker}/observation``, proven separately by ``test_tape_observation_route.py``) is
not exercised here, and no test contacts Alpaca (only ``HistoricalProvider``/``LiveProvider``/
``FakeAdapter`` over committed fixtures and monkeypatched/fake harnesses).
"""

from __future__ import annotations

import ast
import asyncio
import json
import time
from pathlib import Path

import pytest

from app import main as main_module
from app import watch_manager
from app.config import CONFIG
from app.observation_contract import build_tape_observation, resolve_implementation_provenance
from app.providers.adapters.base import HistoricalWindow, RawQuote, RawTrade
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.providers.historical import HistoricalProvider
from app.providers.simulated import SimulatedProvider
from app.research.datasets import DatasetStore
from app.research.feed_basis import data_feed_for_scenario
from app.watch_manager import SourceDescriptor, WatchManager
from fakes import FakeAdapter, FakeLiveProvider

import dataclasses

FIXTURE_DATASETS_J03_DIR = Path(__file__).parent / "fixtures" / "datasets_j03"

# A small stale-gap so the live "waiting"->"stale" watchdog fires in milliseconds (mirrors
# test_stream_lifecycle.py / test_watch_manager.py's own FAST_STALE).
FAST_STALE = dataclasses.replace(CONFIG, stale_gap_seconds=0.05)

ACTIONABILITY_TOKENS = ("READY", "NO_TRADE", "NO_VERDICT", "trade_allowed", "PENDING_CONDITION")


# --- Small helpers (self-contained -- no cross-import of another test module's private doubles) --


async def _until(predicate, timeout: float = 3.0, step: float = 0.005) -> None:
    elapsed = 0.0
    while elapsed < timeout:
        if predicate():
            return
        await asyncio.sleep(step)
        elapsed += step
    raise AssertionError("condition not met within timeout")


def _seed_live(provider: FakeLiveProvider) -> None:
    provider.feed_nowait(QuoteEvent(provider.ticker, 0.0, 100.0, 100.02, 100, 100))
    provider.feed_nowait(TradeEvent(provider.ticker, 0.0, 100.02, 100, Side.UNKNOWN))


def _hist_provider(ticker: str = "F", n: int = 300) -> HistoricalProvider:
    # Dense, small-gap synthetic window so the paced feeder flips to "live"/exhausts quickly.
    quotes = tuple(RawQuote(i * 0.001, 16.0, 16.01, 100, 100) for i in range(n))
    trades = tuple(RawTrade(i * 0.001 + 0.0005, 16.0, 100) for i in range(n))
    window = HistoricalWindow(ticker, trades, quotes)
    return HistoricalProvider(ticker, window, f"historical {ticker} test-window")


class _RaisingProvider:
    """A sync ``Provider`` whose stream RAISES after yielding ``before`` events."""

    def __init__(self, before: int = 0, ticker: str = "FAILT") -> None:
        self.ticker = ticker
        self.scenario = f"historical {ticker} test-window"

    def stream(self):
        if False:
            yield  # never yields -- an immediate-raise double is all TC-7/TC-8's `failed` case needs
        raise RuntimeError("simulated paced-feeder failure")


def _build_observation_from_source(
    snapshot, settled_at_utc, end_reason, descriptor: SourceDescriptor, *, generated_at_utc: str
) -> dict:
    """Bridges this iteration's manager output into the already-existing (iteration 1) pure
    builder -- proves the descriptor is genuinely usable by ``build_tape_observation``, not just
    shaped like its parameters."""
    return build_tape_observation(
        snapshot=snapshot,
        source_mode=descriptor.source_mode,
        data_feed=descriptor.data_feed,
        window_start_utc=descriptor.window_start_utc,
        window_end_utc=descriptor.window_end_utc,
        dataset_id=descriptor.dataset_id,
        dataset_checksum=descriptor.dataset_checksum,
        session_id=descriptor.session_id,
        session_started_at_utc=descriptor.session_started_at_utc,
        settled_at_utc=settled_at_utc,
        end_reason=end_reason,
        generated_at_utc=generated_at_utc,
        profile_id=descriptor.profile_id,
        config=CONFIG,
        provenance=resolve_implementation_provenance(),
    )


def _scan_for_actionability_tokens(obj: object) -> list[str]:
    text = json.dumps(obj, sort_keys=True).lower()
    return [token for token in ACTIONABILITY_TOKENS if token.lower() in text]


# === TC-1: fresh sim watch descriptor =========================================================


def test_fresh_sim_watch_descriptor_shows_honest_defaults():
    manager = WatchManager(CONFIG)
    manager.watch("SIM-BIDABS")  # sync context: cold engine, no feeder task
    result = manager.get_observation_source("SIM-BIDABS")
    assert result is not None
    _, _, _, descriptor = result
    assert descriptor.source_mode == "sim"
    assert descriptor.data_feed == "sim"
    assert descriptor.window_start_utc is None
    assert descriptor.window_end_utc is None
    assert descriptor.dataset_id is None
    assert descriptor.dataset_checksum is None
    assert descriptor.session_id  # non-empty
    assert descriptor.session_started_at_utc.endswith("Z")
    assert descriptor.profile_id == "default"


# === TC-2: historical watch descriptor with the real parsed window ============================


def test_historical_watch_descriptor_carries_the_real_parsed_window():
    manager = WatchManager(CONFIG)
    provider = _hist_provider("HISTF")
    manager.watch_with_provider(
        "HISTF",
        provider,
        speed=1.0,
        window_start_utc="2026-06-09T17:00:00.000000Z",
        window_end_utc="2026-06-09T17:10:00.000000Z",
    )
    _, _, _, descriptor = manager.get_observation_source("HISTF")
    assert descriptor.source_mode == "historical"
    assert descriptor.data_feed == data_feed_for_scenario(provider.scenario, CONFIG)
    assert descriptor.data_feed == "sip"  # the default config's historical_feed
    assert descriptor.window_start_utc == "2026-06-09T17:00:00.000000Z"
    assert descriptor.window_end_utc == "2026-06-09T17:10:00.000000Z"


def test_progressive_historical_watch_descriptor_carries_the_shared_window():
    manager = WatchManager(CONFIG)
    first = _hist_provider("PROGF", n=5)
    manager.watch_with_progressive_historical(
        "PROGF",
        first,
        lambda: [],
        speed=1.0,
        window_start_utc="2026-06-09T17:00:00.000000Z",
        window_end_utc="2026-06-09T18:00:00.000000Z",
    )
    _, _, _, descriptor = manager.get_observation_source("PROGF")
    assert descriptor.source_mode == "historical"
    assert descriptor.window_start_utc == "2026-06-09T17:00:00.000000Z"
    assert descriptor.window_end_utc == "2026-06-09T18:00:00.000000Z"


@pytest.mark.anyio
async def test_main_watch_historical_route_threads_the_real_parsed_window_into_the_descriptor():
    """The genuine end-to-end wiring proof for ``app/main.py``'s ``_watch_historical`` (iter-3 IN
    SCOPE: thread the already-parsed start/end into the manager)."""
    from fastapi.testclient import TestClient

    quotes = (RawQuote(0.0, 16.0, 16.01, 100, 100),)
    trades = (RawTrade(0.0005, 16.0, 100),)
    window = HistoricalWindow("HROUTE", trades, quotes)
    main_module.app.dependency_overrides[main_module.get_market_adapter] = lambda: FakeAdapter(
        available=True, window=window
    )
    client = TestClient(main_module.app)
    try:
        resp = client.post(
            "/watch/HROUTE",
            json={
                "mode": "historical",
                "start": "2026-06-02T15:00:00",
                "end": "2026-06-02T15:02:00",
                "speed": 1,
            },
        )
        assert resp.status_code == 200
        _, _, _, descriptor = main_module.manager.get_observation_source("HROUTE")
        assert descriptor.window_start_utc == "2026-06-02T15:00:00.000000Z"
        assert descriptor.window_end_utc == "2026-06-02T15:02:00.000000Z"
    finally:
        main_module.manager.stop("HROUTE")
        main_module.app.dependency_overrides.pop(main_module.get_market_adapter, None)
        await asyncio.sleep(0.02)


# === TC-3: live watch descriptor ================================================================


@pytest.mark.anyio
async def test_live_watch_descriptor_shows_the_config_owned_live_feed():
    manager = WatchManager(FAST_STALE)
    provider = FakeLiveProvider("LIVEF", "live LIVEF")
    _seed_live(provider)
    manager.watch_with_async_provider("LIVEF", provider)
    try:
        await _until(lambda: manager.get("LIVEF").snapshot().event_count >= 1)
        _, _, _, descriptor = manager.get_observation_source("LIVEF")
        assert descriptor.source_mode == "live"
        assert descriptor.data_feed == CONFIG.live_feed == "iex"
        assert descriptor.window_start_utc is None
        assert descriptor.window_end_utc is None
    finally:
        manager.stop("LIVEF")
        await _until(lambda: provider.socket.closed)


# === TC-4: stop + re-watch mints a new session_id; mode/feed recomputed fresh, never carried ===


def test_rewatch_mints_a_new_session_id_and_recomputes_mode_and_feed_fresh():
    manager = WatchManager(CONFIG)
    manager.watch("SIM-BUYER")
    _, _, _, first_descriptor = manager.get_observation_source("SIM-BUYER")
    assert first_descriptor.source_mode == "sim"
    assert first_descriptor.data_feed == "sim"

    assert manager.stop("SIM-BUYER") is True
    manager.watch_with_provider("SIM-BUYER", _hist_provider("SIM-BUYER"), speed=1.0)
    _, _, _, second_descriptor = manager.get_observation_source("SIM-BUYER")

    assert second_descriptor.session_id != first_descriptor.session_id
    # NEVER carried over from the old watch's mode/feed -- recomputed fresh for the new watch.
    assert second_descriptor.source_mode == "historical"
    assert second_descriptor.data_feed == "sip"
    manager.stop("SIM-BUYER")


# === TC-5: session identity stable across repeated reads of one watch =========================


def test_session_identity_stable_across_repeated_reads():
    manager = WatchManager(CONFIG)
    manager.watch("SIM-SELLER")
    _, _, _, first_read = manager.get_observation_source("SIM-SELLER")
    _, _, _, second_read = manager.get_observation_source("SIM-SELLER")
    assert first_read.session_id == second_read.session_id
    assert first_read.session_started_at_utc == second_read.session_started_at_utc


# === TC-6: the real running-task-switch clobber proof + counter-example =======================


@pytest.mark.anyio
async def test_settle_identity_check_prevents_a_stale_feeders_late_settle_from_clobbering_a_switch():
    """TC-6: a live feeder GENUINELY still mid-flight (blocked on ``FakeLiveProvider``'s own
    internal ``queue.get()`` inside the puller -- a real still-in-flight awaitable, never a
    synthetic delay) when a switch/re-watch for the SAME ticker fires. Advancing the loop lets the
    OLD feeder's ``CancelledError`` handler run its late ``_settle(old_engine, new_event=False)``
    call -- the identity check makes that write a silent no-op, so ``get_observation_source``
    still returns the NEW engine's settled pair and descriptor, never the old engine's."""
    manager = WatchManager(FAST_STALE)
    first = FakeLiveProvider("SWITCHT", "live SWITCHT-1")
    _seed_live(first)  # a genuine settled event, so a would-be clobber is a real, visible one
    first_engine = manager.watch_with_async_provider("SWITCHT", first)
    first_task = manager._tasks["SWITCHT"]
    await _until(lambda: first_engine.snapshot().event_count >= 1)
    _, _, _, first_descriptor = manager.get_observation_source("SWITCHT")
    # `first`'s internal queue is never fed again: the puller (and therefore the whole feeder) is
    # now genuinely blocked awaiting it -- not a timer, a real pending awaitable.

    second = FakeLiveProvider("SWITCHT", "live SWITCHT-2")
    second_engine = manager.watch_with_async_provider("SWITCHT", second)  # the switch
    assert second_engine is not first_engine

    # Advance the loop enough for the OLD task's cancellation to be delivered and its
    # `except asyncio.CancelledError` branch (and its late `_settle` call) to run to completion.
    await _until(lambda: first_task.done())

    result = manager.get_observation_source("SWITCHT")
    assert result is not None
    snapshot, _, _, descriptor = result
    assert snapshot is second_engine.snapshot()  # NEVER the old engine's stale write
    assert snapshot is not first_engine.snapshot()
    assert descriptor.session_id != first_descriptor.session_id

    manager.stop("SWITCHT")
    await _until(lambda: second.socket.closed)


def _naive_settle_without_identity_check(self, engine, *, new_event):
    """The PRE-FIX ``_settle`` reproduced verbatim (no identity check) -- the reviewer's
    carried-forward MINOR. Used ONLY by the counter-example below to prove the identity check is
    load-bearing, not decorative."""
    ticker = engine.snapshot().ticker
    if new_event:
        settled_at_epoch = time.time()
    else:
        prior = self._settled.get(ticker)
        settled_at_epoch = prior[1] if prior is not None else None
    self._settled[ticker] = (engine.snapshot(), settled_at_epoch)


@pytest.mark.anyio
async def test_counterexample_settle_without_identity_check_reproduces_the_clobber(monkeypatch):
    """TC-6 counter-example: reverting ``_settle`` to the naive pre-fix version (no identity
    check) reproduces the EXACT clobber the reviewer flagged -- a stale engine's late settle
    write (the exact call ``_feed_live``'s ``except asyncio.CancelledError`` branch makes)
    overwrites the fresh watch's settled pair with the OLD engine's stale snapshot.

    ``first``'s feeder is left GENUINELY mid-flight (blocked on its own internal queue, a real
    pending awaitable -- never a timer) when the switch fires, exactly as in the fix proof above.
    The late write is then invoked DIRECTLY here (mirroring precisely what the cancellation
    handler executes) rather than by waiting on ``first_task.done()``: with ``FAST_STALE``'s tiny
    stale-gap, waiting for the old task's full async unwind lets the NEW engine's own periodic
    stale-flip settle (which fires every ~50ms while ``second`` is never fed) repair the clobber
    before the test can observe it, making that checkpoint non-deterministic. Asserting
    immediately after the direct late write keeps this test's outcome deterministic while
    exercising the identical code path and the identical stale/fresh-engine identities."""
    monkeypatch.setattr(WatchManager, "_settle", _naive_settle_without_identity_check)
    manager = WatchManager(FAST_STALE)
    first = FakeLiveProvider("SWITCHC", "live SWITCHC-1")
    _seed_live(first)
    first_engine = manager.watch_with_async_provider("SWITCHC", first)
    first_task = manager._tasks["SWITCHC"]
    await _until(lambda: first_engine.snapshot().event_count >= 1)
    # `first`'s internal queue is never fed again: its feeder is now genuinely blocked awaiting
    # it -- a real pending awaitable, not a timer.

    second = FakeLiveProvider("SWITCHC", "live SWITCHC-2")
    second_engine = manager.watch_with_async_provider("SWITCHC", second)  # the switch
    assert second_engine is not first_engine
    snapshot, _, _, _ = manager.get_observation_source("SWITCHC")
    assert snapshot is second_engine.snapshot()  # cold-reset pair, before any late write arrives

    # Simulate the OLD feeder's late CancelledError-handler settle (the exact call
    # `_feed_live`'s except branch makes) arriving AFTER the switch. Without the identity check
    # (monkeypatched above), this naive write clobbers the fresh pair unconditionally.
    manager._settle(first_engine, new_event=False)
    snapshot, _, _, _ = manager.get_observation_source("SWITCHC")
    assert snapshot is first_engine.snapshot()  # CLOBBERED: the OLD engine's stale write won
    assert snapshot is not second_engine.snapshot()

    # Cleanup only, no longer load-bearing for the assertion above: let `second`'s freshly
    # created task actually start (reach its first await point) before cancelling it, so its
    # `finally` block runs and closes the socket -- avoids a "cancelled before ever starting"
    # no-op teardown that would otherwise hang the socket-closed wait below.
    await asyncio.sleep(0.01)
    manager.stop("SWITCHC")
    await _until(lambda: first_task.done())  # let the old feeder's real cancellation unwind too
    await _until(lambda: second.socket.closed)


# === TC-7 / TC-8: every lifecycle status is distinguishable; tape_state/confidence never nulled ==


def test_lifecycle_connecting_distinguishable_when_no_feeder_started():
    # Sync (non-async) test function: no running event loop, so watch() leaves the engine COLD
    # with no feeder task -- the honest "connecting" read (established pattern, see
    # test_tape_observation_time.py's module docstring).
    manager = WatchManager(CONFIG)
    manager.watch("SIM-BUYER")
    snapshot, settled_at_utc, end_reason, _ = manager.get_observation_source("SIM-BUYER")
    assert snapshot.stream_status == "connecting"
    assert settled_at_utc is None
    assert end_reason is None


@pytest.mark.anyio
async def test_lifecycle_waiting_distinguishable_before_first_event():
    manager = WatchManager(FAST_STALE)
    provider = FakeLiveProvider("LIVEWAIT")
    manager.watch_with_async_provider("LIVEWAIT", provider)
    try:
        await _until(lambda: manager.get("LIVEWAIT").snapshot().stream_status == "waiting")
        snapshot, settled_at_utc, _, _ = manager.get_observation_source("LIVEWAIT")
        assert snapshot.stream_status == "waiting"
        assert settled_at_utc is None  # lifecycle-only mutation, no event settled yet
        assert snapshot.bid is None and snapshot.ask is None and snapshot.last is None
    finally:
        manager.stop("LIVEWAIT")
        await _until(lambda: provider.socket.closed)


@pytest.mark.anyio
async def test_lifecycle_live_distinguishable_after_first_event():
    manager = WatchManager(FAST_STALE)
    provider = FakeLiveProvider("LIVELIVE")
    _seed_live(provider)
    manager.watch_with_async_provider("LIVELIVE", provider)
    try:
        await _until(lambda: manager.get("LIVELIVE").snapshot().stream_status == "live")
        snapshot, settled_at_utc, _, _ = manager.get_observation_source("LIVELIVE")
        assert snapshot.stream_status == "live"
        assert settled_at_utc is not None
    finally:
        manager.stop("LIVELIVE")
        await _until(lambda: provider.socket.closed)


@pytest.mark.anyio
async def test_lifecycle_stale_distinguishable_with_zero_events():
    manager = WatchManager(FAST_STALE)
    provider = FakeLiveProvider("LIVESTALE0")  # never fed: waiting -> stale with zero events
    manager.watch_with_async_provider("LIVESTALE0", provider)
    try:
        await _until(lambda: manager.get("LIVESTALE0").snapshot().stream_status == "stale")
        snapshot, settled_at_utc, _, _ = manager.get_observation_source("LIVESTALE0")
        assert snapshot.stream_status == "stale"
        assert snapshot.event_count == 0
        assert settled_at_utc is None  # zero events -- never settled
    finally:
        manager.stop("LIVESTALE0")
        await _until(lambda: provider.socket.closed)


@pytest.mark.anyio
async def test_lifecycle_stale_after_events_retains_tape_state_and_confidence():
    """TC-8: a `stale` transition AFTER at least one processed event retains `tape_state` and
    `confidence` EXACTLY -- never null, never rewritten."""
    manager = WatchManager(FAST_STALE)
    provider = FakeLiveProvider("LIVESTALE1")
    _seed_live(provider)
    manager.watch_with_async_provider("LIVESTALE1", provider)
    try:
        await _until(lambda: manager.get("LIVESTALE1").snapshot().stream_status == "live")
        pre_stale_snapshot, _, _, _ = manager.get_observation_source("LIVESTALE1")
        pre_tape_state, pre_confidence = pre_stale_snapshot.tape_state, pre_stale_snapshot.confidence

        await _until(lambda: manager.get("LIVESTALE1").snapshot().stream_status == "stale")
        stale_snapshot, _, _, _ = manager.get_observation_source("LIVESTALE1")
        assert stale_snapshot.stream_status == "stale"
        assert stale_snapshot.tape_state == pre_tape_state
        assert stale_snapshot.confidence == pre_confidence
        assert stale_snapshot.tape_state is not None
        assert stale_snapshot.confidence is not None
    finally:
        manager.stop("LIVESTALE1")
        await _until(lambda: provider.socket.closed)


def test_counterexample_a_build_that_nulls_tape_state_on_stale_fails_the_assertion():
    # The counter-example proving TC-8's assertion is non-vacuous: a WRONG artifact that nulls
    # tape_state/confidence on `stale` must fail the real-value comparison.
    real_tape_state, real_confidence = "bid_absorption", 0.62
    wrong_artifact = {"tape_state": None, "confidence": None}
    with pytest.raises(AssertionError):
        assert wrong_artifact["tape_state"] == real_tape_state
    with pytest.raises(AssertionError):
        assert wrong_artifact["confidence"] == real_confidence


def test_lifecycle_paused_distinguishable_and_retains_settled_time():
    manager = WatchManager(CONFIG)
    engine = manager.watch("SIM-BIDABS")
    event = next(SimulatedProvider("SIM-BIDABS", "bid_absorption").stream())
    engine.process_event(event)
    manager._settle(engine, new_event=True)
    _, pre_pause_settled, _, _ = manager.get_observation_source("SIM-BIDABS")

    assert manager.pause("SIM-BIDABS") is True
    snapshot, settled_at_utc, _, _ = manager.get_observation_source("SIM-BIDABS")
    assert snapshot.stream_status == "paused"
    assert snapshot.paused is True
    assert settled_at_utc == pre_pause_settled  # no new event -- carried forward unchanged


@pytest.mark.anyio
async def test_lifecycle_closed_natural_exhaustion_carries_stream_closed_end_reason():
    manager = WatchManager(CONFIG, pace=0.001)
    provider = _hist_provider("NATCLOSE", n=5)
    manager.watch_with_provider("NATCLOSE", provider, speed=1.0)
    await _until(lambda: manager.get("NATCLOSE").snapshot().stream_status == "closed")
    snapshot, _, end_reason, _ = manager.get_observation_source("NATCLOSE")
    assert snapshot.stream_status == "closed"
    assert end_reason == "stream_closed"


def test_lifecycle_watch_stopped_returns_none_from_get_observation_source():
    manager = WatchManager(CONFIG)
    manager.watch("SIM-BIDABS")
    assert manager.get_observation_source("SIM-BIDABS") is not None
    assert manager.stop("SIM-BIDABS") is True
    assert manager.get_observation_source("SIM-BIDABS") is None  # distinguishable: no dict, None


@pytest.mark.anyio
async def test_lifecycle_failed_distinguishable_null_end_reason_and_retained_state():
    manager = WatchManager(CONFIG, pace=0.001)
    provider = _RaisingProvider(before=0, ticker="FAILT")
    manager.watch_with_provider("FAILT", provider, speed=1.0)
    await _until(lambda: manager.get("FAILT").snapshot().stream_status == "failed")
    snapshot, settled_at_utc, end_reason, _ = manager.get_observation_source("FAILT")
    assert snapshot.stream_status == "failed"
    assert end_reason is None  # Constitution §4: "end_reason null in v1"
    assert settled_at_utc is None  # zero events -- never settled
    assert snapshot.event_count == 0  # no fabricated trade past the raise


# NOTE (iter-4 fixup, reviewer's carried-forward MINOR): a prior
# ``test_seven_lifecycle_statuses_plus_watch_stopped_are_pairwise_distinguishable`` asserted only
# ``len({seven hand-written literals}) == 7`` and never called ``WatchManager`` -- a vacuous
# summary disconnected from real captured state (the iter-3 lessons entry: "a spec item phrased
# 'all N values are pairwise distinguishable' invites a tautological summary test"). It is REMOVED
# here rather than rewritten: the nine tests directly above (lines 370-510) already exercise every
# one of the seven ``lifecycle.stream_status`` values plus the in-process ``watch_stopped`` case
# non-vacuously, each via a real ``WatchManager``/``TapeEngine`` call and a real
# ``assert snapshot.stream_status == "<value>"`` -- the "all seven are distinguishable" coverage
# this test wanted to represent already exists, honestly, without a second literal-only copy.


# === TC-9: (data_feed, availability_basis) pairs are pairwise distinct, never pooled ===========


_AVAILABILITY_BASIS_BY_SOURCE_MODE = {
    "live": "live_settled_wall_clock",
    "historical": "historical_arrival_unknown",
    "sim": "simulated_not_applicable",
}


@pytest.mark.anyio
async def test_feed_basis_pairs_are_pairwise_distinct_across_sim_historical_live():
    manager = WatchManager(CONFIG)
    manager.watch("SIM-CHOP")
    _, _, _, sim_descriptor = manager.get_observation_source("SIM-CHOP")

    manager.watch_with_provider("PAIRHIST", _hist_provider("PAIRHIST"), speed=1.0)
    _, _, _, hist_descriptor = manager.get_observation_source("PAIRHIST")

    live_provider = FakeLiveProvider("PAIRLIVE", "live PAIRLIVE")
    manager.watch_with_async_provider("PAIRLIVE", live_provider)
    _, _, _, live_descriptor = manager.get_observation_source("PAIRLIVE")

    pairs = {
        "sim": (sim_descriptor.data_feed, _AVAILABILITY_BASIS_BY_SOURCE_MODE[sim_descriptor.source_mode]),
        "historical": (
            hist_descriptor.data_feed,
            _AVAILABILITY_BASIS_BY_SOURCE_MODE[hist_descriptor.source_mode],
        ),
        "live": (live_descriptor.data_feed, _AVAILABILITY_BASIS_BY_SOURCE_MODE[live_descriptor.source_mode]),
    }
    assert pairs["sim"] == ("sim", "simulated_not_applicable")
    assert pairs["historical"] == ("sip", "historical_arrival_unknown")
    assert pairs["live"] == ("iex", "live_settled_wall_clock")
    assert len(set(pairs.values())) == 3  # pairwise distinct, never pooled/equated

    manager.stop("PAIRHIST")
    manager.stop("PAIRLIVE")
    await asyncio.sleep(0.02)


def test_counterexample_pooling_sim_and_historical_feed_is_caught():
    with pytest.raises(AssertionError):
        assert data_feed_for_scenario("bid_absorption", CONFIG) == data_feed_for_scenario(
            "historical F test-window", CONFIG
        )


# === TC-10: dataset-manifest feed-owner agreement on every committed fixture dataset ===========


def test_dataset_manifest_feed_owner_agrees_with_data_feed_for_scenario():
    store = DatasetStore(FIXTURE_DATASETS_J03_DIR)
    records, errors = store.list()
    assert errors == []
    assert len(records) > 0
    for meta in records:
        assert meta["data_feed"] == data_feed_for_scenario(meta["source"], CONFIG)


def test_counterexample_dataset_manifest_feed_mismatch_is_caught():
    store = DatasetStore(FIXTURE_DATASETS_J03_DIR)
    records, _ = store.list()
    mutated = dict(records[0])
    mutated["data_feed"] = "iex" if mutated["data_feed"] != "iex" else "sip"
    with pytest.raises(AssertionError):
        assert mutated["data_feed"] == data_feed_for_scenario(mutated["source"], CONFIG)


# === TC-11: AST guard -- no second scenario-prefix parser; no session identity in app/engine/* ==


def _find_bare_scenario_prefix_checks(source: str, filename: str) -> list[str]:
    """A second scenario-prefix parser: a literal ``.startswith("live ")`` /
    ``.startswith("historical ")`` string check OUTSIDE ``data_feed_for_scenario`` itself
    (``feed_basis.py`` is the one sanctioned owner and is deliberately never scanned)."""
    violations: list[str] = []
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "startswith"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
            and node.args[0].value in ("live ", "historical ")
        ):
            violations.append(f"{filename}: startswith({node.args[0].value!r})")
    return violations


def test_no_second_scenario_prefix_parser_outside_feed_basis():
    targets = [Path(watch_manager.__file__), Path(main_module.__file__)]
    violations: list[str] = []
    for path in targets:
        violations += _find_bare_scenario_prefix_checks(path.read_text(), path.name)
    assert violations == []


def test_counterexample_scenario_prefix_scan_detects_an_injected_second_parser():
    fixture_source = 'def f(scenario):\n    if scenario.startswith("live "):\n        return "iex"\n'
    assert _find_bare_scenario_prefix_checks(fixture_source, "fixture.py") != []


def _scan_for_session_identity_refs(text: str) -> list[str]:
    found = []
    if "session_id" in text:
        found.append("session_id")
    if "session_started_at_utc" in text:
        found.append("session_started_at_utc")
    return found


def test_no_engine_module_references_session_identity():
    from app.observation_contract import ENGINE_SOURCE_MODULES, _ENGINE_DIR

    violations: dict[str, list[str]] = {}
    for name in ENGINE_SOURCE_MODULES:
        found = _scan_for_session_identity_refs((_ENGINE_DIR / name).read_text())
        if found:
            violations[name] = found
    assert violations == {}


def test_counterexample_session_identity_scan_detects_an_injected_reference():
    fixture_source = "session_id = engine_context.session_id\n"
    assert _scan_for_session_identity_refs(fixture_source) != []


# === TC-12: no actionability token anywhere in a fully-built live observation =================


@pytest.mark.anyio
async def test_no_actionability_token_in_a_fully_built_live_observation():
    manager = WatchManager(FAST_STALE)
    provider = FakeLiveProvider("TOKCHK")
    _seed_live(provider)
    manager.watch_with_async_provider("TOKCHK", provider)
    try:
        await _until(lambda: manager.get("TOKCHK").snapshot().event_count >= 1)
        result = manager.get_observation_source("TOKCHK")
        observation = _build_observation_from_source(
            *result, generated_at_utc="2026-09-03T00:00:00.000000Z"
        )
        assert _scan_for_actionability_tokens(observation) == []
    finally:
        manager.stop("TOKCHK")
        await _until(lambda: provider.socket.closed)


def test_counterexample_actionability_scan_catches_an_injected_token():
    injected = {"lifecycle": {"stream_status": "live"}, "note": "trade_allowed=true"}
    assert _scan_for_actionability_tokens(injected) != []
