"""Observation Contract v1 -- Binding Execution Order step 2 (J-02; docs/goal.md).

Covers the time law's MANAGER-side machinery added this iteration -- ``WatchManager``'s
per-ticker atomic settled pair (``_settle`` / ``get_observation_source``) -- proven atomic under
a deterministic interleaving harness, plus the already-implemented (iter-1)
``app/observation_contract.py`` time projections (``_observed_at_utc`` / ``_availability`` / the
pinned ISO function), proven honest against real sim, historical-fixture, dataset-replay and
live-fixture data. TC references below match the iteration spec
(``docs/phases/goal-observation-contract-iter-2.md``) and goal.md's J-02 Steps.2 list. Every
guard/law test ships a named ``test_counterexample_*`` proving it can fail. No test needs a
running uvicorn server or network access -- the route does not exist until iteration 5, and no
test contacts Alpaca (only ``HistoricalProvider``/``LiveProvider`` over committed fixtures).

TC-1..TC-4 (the atomic-read interleaving proof) use a deterministic SYNC harness:
``WatchManager.watch()``/``watch_with_provider()`` called from a plain (non-async) test function
finds no running event loop and leaves the engine COLD with no feeder task (its own documented
"the caller feeds the engine itself" contract -- see ``test_watch_manager.py``'s
``test_watch_with_provider_does_not_touch_sim_registry``). That gives full, race-free control
over exactly when each event is processed and exactly when the settle helper fires -- the only
way to construct "event N settled, event N+1 processed but not yet settled" deterministically
(a real running feeder settles both back-to-back with no await point between them, so no outside
coroutine could ever observe that interleaving). ``manager._settle(...)`` is called directly in
those tests for the same reason.
"""

from __future__ import annotations

import ast
import asyncio
import itertools
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app import observation_contract, watch_manager
from app.config import CONFIG
from app.engine.snapshot import EngineSnapshot
from app.engine.tape_engine import TapeEngine
from app.observation_contract import build_tape_observation
from app.providers.adapters.base import RawQuote, RawTrade
from app.providers.historical import HistoricalProvider
from app.providers.live import LiveProvider
from app.providers.simulated import SimulatedProvider
from app.research.datasets import DatasetStore
from app.watch_manager import WatchManager
from fakes import load_fixture_window

PG_FIXTURE = Path(__file__).parent / "fixtures" / "alpaca" / "PG_20260609_170000_171000_sip.json"
FIXTURE_DATASETS_J03_DIR = Path(__file__).parent / "fixtures" / "datasets_j03"
DATASETS_J03_ID = "5232fa672b7b4077a5117d34b14c807d"


# --- Small builders / helpers ---------------------------------------------------------------


def _iso(epoch: float) -> str:
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _parse_iso(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def _make_snapshot(**overrides: object) -> EngineSnapshot:
    defaults: dict = dict(
        ticker="SIM-BIDABS",
        scenario="bid_absorption",
        timestamp=12.5,
        event_count=3,
        warm=False,
        stream_status="live",
        bid=100.0,
        ask=100.02,
        spread=0.02,
        last=100.01,
        features={"30s": {"aggressive_sell_ratio": 0.6}},
        primary_window="30s",
        tape_state="bid_absorption",
        confidence=0.5,
        observations=(),
        paused=False,
        epoch_anchor=CONFIG.sim_session_anchor_epoch,
        delivery_lag_seconds=None,
    )
    defaults.update(overrides)
    return EngineSnapshot(**defaults)


def _valid_provenance() -> tuple[str, str | None, bool | None]:
    return ("b" * 64, "abc123def456", False)


def _build_for_snapshot(snapshot: EngineSnapshot, *, source_mode: str, data_feed: str, **overrides: object) -> dict:
    kwargs: dict = dict(
        snapshot=snapshot,
        source_mode=source_mode,
        data_feed=data_feed,
        window_start_utc=None,
        window_end_utc=None,
        dataset_id=None,
        dataset_checksum=None,
        session_id="session-test-abc",
        session_started_at_utc="2026-09-03T00:00:00.000000Z",
        settled_at_utc=None,
        end_reason=None,
        generated_at_utc="2026-09-03T00:00:01.000000Z",
        profile_id="default",
        config=CONFIG,
        provenance=_valid_provenance(),
    )
    kwargs.update(overrides)
    return build_tape_observation(**kwargs)


async def _aiter(records):
    for r in records:
        yield r


async def _until(predicate, timeout: float = 3.0, step: float = 0.005) -> None:
    elapsed = 0.0
    while elapsed < timeout:
        if predicate():
            return
        await asyncio.sleep(step)
        elapsed += step
    raise AssertionError("condition not met within timeout")


# --- TC-1 / TC-2 / TC-3 / TC-4: the atomic-read interleaving proof (Constitution §2) ---------


def test_get_observation_source_pairs_snapshot_with_its_own_settled_time(monkeypatch):
    """TC-1: SIM-BIDABS watched with >=1 event processed -- get_observation_source returns the
    settled EngineSnapshot paired with the settled_at_utc stamped by THAT SAME settle call,
    under a deterministic interleaving harness with a monkeypatched watch_manager clock."""
    clock = [1_700_000_000.0]
    monkeypatch.setattr(watch_manager.time, "time", lambda: clock[0])
    manager = WatchManager(CONFIG)
    engine = manager.watch("SIM-BIDABS")  # sync context: cold engine, no feeder task
    event = next(SimulatedProvider("SIM-BIDABS", "bid_absorption").stream())

    engine.process_event(event)
    manager._settle(engine, new_event=True)

    result = manager.get_observation_source("SIM-BIDABS")
    assert result is not None
    snapshot, settled_at_utc, end_reason = result
    assert snapshot.timestamp == event.timestamp
    assert settled_at_utc == watch_manager._iso_utc(clock[0])
    assert end_reason is None


def test_atomic_read_never_mispairs_snapshot_n_plus_1_with_settled_time_n(monkeypatch):
    """TC-2: event N settled, event N+1 process_event-applied but the settle helper has NOT yet
    run for it -- the read still pairs snapshot N with settled-time N (never N+1 with N, nor the
    reverse); after settling N+1 the pair becomes N+1 / settled-time-N+1."""
    clock = [1_700_000_000.0]
    monkeypatch.setattr(watch_manager.time, "time", lambda: clock[0])
    manager = WatchManager(CONFIG)
    engine = manager.watch("SIM-BIDABS")
    stream = SimulatedProvider("SIM-BIDABS", "bid_absorption").stream()

    event_n = next(stream)
    engine.process_event(event_n)
    manager._settle(engine, new_event=True)
    snapshot_n, settled_n, _ = manager.get_observation_source("SIM-BIDABS")
    assert snapshot_n.timestamp == event_n.timestamp

    clock[0] += 5.0  # wall clock advances -- but N+1 has not been settled yet
    event_n1 = next(stream)
    engine.process_event(event_n1)  # the engine's OWN internal snapshot now reflects N+1

    still_snapshot, still_settled, _ = manager.get_observation_source("SIM-BIDABS")
    assert still_snapshot is snapshot_n  # STILL the exact N object, never a fresher N+1 read
    assert still_settled == settled_n  # STILL settled-time N, never re-stamped early
    assert engine.snapshot() is not still_snapshot  # the LIVE engine has already moved to N+1

    manager._settle(engine, new_event=True)  # now settle N+1
    snapshot_n1, settled_n1, _ = manager.get_observation_source("SIM-BIDABS")
    assert snapshot_n1 is engine.snapshot()
    assert snapshot_n1.timestamp == event_n1.timestamp
    assert settled_n1 != settled_n


def test_counterexample_naive_read_mispairs_snapshot_and_settled_time(monkeypatch):
    """TC-3: constructing the NAIVE read ``(engine.snapshot(), <last recorded settled_at>)``
    instead of the atomic helper mis-pairs snapshot N+1 with settled-time N -- the counter-example
    proving the atomic read is required, not decorative."""
    clock = [1_700_000_000.0]
    monkeypatch.setattr(watch_manager.time, "time", lambda: clock[0])
    manager = WatchManager(CONFIG)
    engine = manager.watch("SIM-BIDABS")
    stream = SimulatedProvider("SIM-BIDABS", "bid_absorption").stream()

    event_n = next(stream)
    engine.process_event(event_n)
    manager._settle(engine, new_event=True)
    settled_snapshot_n, settled_n, _ = manager.get_observation_source("SIM-BIDABS")

    event_n1 = next(stream)
    engine.process_event(event_n1)  # engine.snapshot() now reflects N+1; settle NOT yet called

    # The NAIVE read a non-atomic implementation would construct: the engine's CURRENT live
    # snapshot object, paired with the LAST recorded settled_at (settled_n, from N).
    naive_snapshot, naive_settled_at = engine.snapshot(), settled_n

    # Mis-pair, proven by object identity (robust even when N and N+1 share a logical
    # timestamp, e.g. a quote immediately followed by a trade): the naive read's snapshot is NOT
    # the same object ``settled_n`` was atomically recorded together with.
    assert naive_snapshot is not settled_snapshot_n
    with pytest.raises(AssertionError):
        assert naive_snapshot is settled_snapshot_n

    # The atomic manager read, in contrast, NEVER exhibits this: it always returns the exact
    # settled snapshot object paired with its own settled_at -- never engine.snapshot()'s
    # current, possibly-fresher object.
    atomic_snapshot, atomic_settled_at, _ = manager.get_observation_source("SIM-BIDABS")
    assert atomic_snapshot is settled_snapshot_n
    assert atomic_settled_at == naive_settled_at
    assert atomic_snapshot is not naive_snapshot  # the concrete mis-pair the naive tuple carries


def test_pause_carries_forward_settled_time_unchanged(monkeypatch):
    """TC-4: given a watch with one settled event, pause() then get_observation_source() shows
    settled_at_utc identical to its pre-pause value (carried forward, never re-stamped to
    "now") -- Constitution §2: "no new event, same availability"."""
    clock = [1_700_000_000.0]
    monkeypatch.setattr(watch_manager.time, "time", lambda: clock[0])
    manager = WatchManager(CONFIG)
    engine = manager.watch("SIM-BIDABS")
    event = next(SimulatedProvider("SIM-BIDABS", "bid_absorption").stream())
    engine.process_event(event)
    manager._settle(engine, new_event=True)
    pre_pause_snapshot, pre_pause_settled, _ = manager.get_observation_source("SIM-BIDABS")

    clock[0] += 120.0  # wall clock advances well past the pause
    assert manager.pause("SIM-BIDABS") is True
    post_pause_snapshot, post_pause_settled, _ = manager.get_observation_source("SIM-BIDABS")
    assert post_pause_settled == pre_pause_settled
    assert post_pause_snapshot.tape_state == pre_pause_snapshot.tape_state


def test_get_observation_source_on_an_unwatched_ticker_returns_none():
    # Error case (TESTING REQUIREMENTS): mirrors get()/pause()/resume()'s "no fabricated engine"
    # idiom -- never synthesizes a pair for a ticker that was never watched.
    manager = WatchManager(CONFIG)
    assert manager.get_observation_source("SIM-BIDABS") is None


def test_get_observation_source_returns_none_after_stop():
    manager = WatchManager(CONFIG)
    manager.watch("SIM-BIDABS")
    assert manager.get_observation_source("SIM-BIDABS") is not None
    assert manager.stop("SIM-BIDABS") is True
    assert manager.get_observation_source("SIM-BIDABS") is None


def test_rewatch_before_first_settle_never_returns_a_prior_watchs_stale_pair(monkeypatch):
    # Guards the cold-reset at each watch* constructor: a re-watched ticker must never read a
    # PRIOR (now-stopped) watch's settled snapshot/settled_at_utc before its own first tick.
    clock = [1_700_000_000.0]
    monkeypatch.setattr(watch_manager.time, "time", lambda: clock[0])
    manager = WatchManager(CONFIG)
    first_engine = manager.watch("SIM-BIDABS")
    event = next(SimulatedProvider("SIM-BIDABS", "bid_absorption").stream())
    first_engine.process_event(event)
    manager._settle(first_engine, new_event=True)
    first_snapshot, first_settled, _ = manager.get_observation_source("SIM-BIDABS")
    assert first_settled is not None

    assert manager.stop("SIM-BIDABS") is True
    clock[0] += 999.0
    second_engine = manager.watch("SIM-BIDABS")  # a fresh, cold engine
    assert second_engine is not first_engine

    # BEFORE the fresh engine has processed any event, the settled pair must be a COLD read for
    # THIS engine -- never the prior watch's stale settled snapshot/time.
    second_snapshot, second_settled, _ = manager.get_observation_source("SIM-BIDABS")
    assert second_snapshot is second_engine.snapshot()
    assert second_snapshot is not first_snapshot
    assert second_settled is None  # nothing has settled yet on the fresh engine


# --- TC-5: observed_at_utc equals the latest processed event, across all four sources --------


def test_observed_at_utc_equals_latest_event_for_sim_provider():
    engine = TapeEngine(
        "SIM-BIDABS", "bid_absorption", CONFIG, epoch_anchor=CONFIG.sim_session_anchor_epoch
    )
    for event in itertools.islice(SimulatedProvider("SIM-BIDABS", "bid_absorption").stream(), 5):
        engine.process_event(event)
    snapshot = engine.snapshot()
    observation = _build_for_snapshot(snapshot, source_mode="sim", data_feed="sim")
    assert observation["observed_at_utc"] == _iso(snapshot.epoch_anchor + snapshot.timestamp)


def test_observed_at_utc_equals_latest_event_for_historical_provider():
    window, _raw = load_fixture_window(PG_FIXTURE)
    provider = HistoricalProvider("PG", window, "historical PG 2026-06-09T17:00:00Z-17:10:00Z")
    engine = TapeEngine("PG", provider.scenario, CONFIG, epoch_anchor=provider.epoch_anchor)
    for event in itertools.islice(provider.stream(), 50):
        engine.process_event(event)
    snapshot = engine.snapshot()
    observation = _build_for_snapshot(snapshot, source_mode="historical", data_feed="sip")
    assert observation["observed_at_utc"] == _iso(snapshot.epoch_anchor + snapshot.timestamp)


def test_observed_at_utc_equals_latest_event_for_dataset_replay():
    store = DatasetStore(FIXTURE_DATASETS_J03_DIR)
    last_snapshot = None
    for snapshot in store.replay(DATASETS_J03_ID, CONFIG):
        last_snapshot = snapshot
    assert last_snapshot is not None
    observation = _build_for_snapshot(last_snapshot, source_mode="dataset_replay", data_feed="sip")
    assert observation["observed_at_utc"] == _iso(
        last_snapshot.epoch_anchor + last_snapshot.timestamp
    )


@pytest.mark.anyio
async def test_observed_at_utc_equals_latest_event_for_live_provider():
    window, _raw = load_fixture_window(PG_FIXTURE)
    # Merge quotes+trades into arrival order the way a live socket delivers them (epoch order).
    records = sorted(list(window.quotes) + list(window.trades), key=lambda r: r.epoch)
    provider = LiveProvider("PG", _aiter(records[:50]), "live PG")
    engine = TapeEngine("PG", provider.scenario, CONFIG)
    async for event in provider.stream():
        if engine.epoch_anchor is None and provider.epoch_anchor is not None:
            engine.set_epoch_anchor(provider.epoch_anchor)
        engine.process_event(event)
    snapshot = engine.snapshot()
    observation = _build_for_snapshot(
        snapshot, source_mode="live", data_feed="iex", settled_at_utc="2026-09-03T00:00:02.000000Z"
    )
    assert observation["observed_at_utc"] == _iso(snapshot.epoch_anchor + snapshot.timestamp)


# --- TC-6: both observed_at_utc null clauses --------------------------------------------------


def test_observed_at_utc_null_when_epoch_anchor_is_none():
    snapshot = _make_snapshot(epoch_anchor=None)
    observation = _build_for_snapshot(snapshot, source_mode="sim", data_feed="sim")
    assert observation["observed_at_utc"] is None


def test_observed_at_utc_null_when_no_event_processed():
    snapshot = _make_snapshot(bid=None, ask=None, last=None)
    observation = _build_for_snapshot(snapshot, source_mode="sim", data_feed="sim")
    assert observation["observed_at_utc"] is None


# --- TC-7: historical / dataset_replay availability is always honestly unknown ---------------


@pytest.mark.parametrize("source_mode", ["historical", "dataset_replay"])
def test_historical_and_dataset_replay_availability_is_always_null_and_unknown(source_mode):
    snapshot = _make_snapshot()
    observation = _build_for_snapshot(
        snapshot,
        source_mode=source_mode,
        data_feed="sip",
        settled_at_utc="2026-09-03T00:00:05.000000Z",  # even if a settled_at_utc IS supplied
    )
    assert observation["available_at_utc"] is None
    assert observation["availability_basis"] == "historical_arrival_unknown"


@pytest.mark.parametrize("source_mode", ["historical", "dataset_replay"])
def test_counterexample_copying_event_time_into_available_at_utc_is_caught(source_mode):
    snapshot = _make_snapshot()
    observation = _build_for_snapshot(snapshot, source_mode=source_mode, data_feed="sip")
    # A wrong builder would copy observed_at_utc verbatim into available_at_utc; prove that
    # assertion FAILS against the real (honest-null) builder output.
    with pytest.raises(AssertionError):
        assert observation["available_at_utc"] == observation["observed_at_utc"]


# --- TC-8: live availability is MEASURED (== settled_at_utc), never derived ------------------


@pytest.mark.anyio
async def test_live_available_at_utc_equals_settled_at_utc_from_manager_clock(monkeypatch):
    record_epoch = 1_800_000_000.0
    fixed_now = record_epoch + 2.5  # a known, fixed, unclamped delivery lag of 2.5s
    monkeypatch.setattr(watch_manager.time, "time", lambda: fixed_now)

    records = [
        RawQuote(record_epoch, 100.0, 100.02, 100, 100),
        RawTrade(record_epoch, 100.01, 50),
    ]
    provider = LiveProvider("PGLIVE1", _aiter(records), "live PGLIVE1")
    manager = WatchManager(CONFIG)
    engine = manager.watch_with_async_provider("PGLIVE1", provider)
    try:
        await _until(lambda: engine.snapshot().event_count >= 1)
        snapshot, settled_at_utc, _ = manager.get_observation_source("PGLIVE1")
        assert settled_at_utc == watch_manager._iso_utc(fixed_now)

        observation = _build_for_snapshot(
            snapshot, source_mode="live", data_feed="iex", settled_at_utc=settled_at_utc
        )
        assert observation["available_at_utc"] == settled_at_utc
        assert observation["availability_basis"] == "live_settled_wall_clock"
    finally:
        manager.stop("PGLIVE1")
        await asyncio.sleep(0.02)


@pytest.mark.anyio
async def test_counterexample_deriving_available_at_utc_from_observed_plus_lag_is_caught(monkeypatch):
    """TC-8 counter-example: under vendor clock skew (the settled wall-clock instant PRECEDES
    the record's own event time, Constitution §2's explicit "MAY precede observed_at_utc" case)
    ``_live_delivery_lag`` clamps at zero, so ``observed_at_utc + delivery_lag_seconds`` collapses
    to ``observed_at_utc`` itself -- provably DIFFERENT from the real, measured
    ``available_at_utc``. Proves the derive-from-lag shortcut is wrong, not merely unused."""
    record_epoch = 1_800_000_500.0
    fixed_now = record_epoch - 100.0  # settlement wall-clock reads BEFORE the record's own epoch
    monkeypatch.setattr(watch_manager.time, "time", lambda: fixed_now)

    records = [
        RawQuote(record_epoch, 50.0, 50.02, 10, 10),
        RawTrade(record_epoch, 50.01, 20),
    ]
    provider = LiveProvider("PGLIVE2", _aiter(records), "live PGLIVE2")
    manager = WatchManager(CONFIG)
    engine = manager.watch_with_async_provider("PGLIVE2", provider)
    try:
        await _until(lambda: engine.snapshot().event_count >= 1)
        snapshot, settled_at_utc, _ = manager.get_observation_source("PGLIVE2")
        assert snapshot.delivery_lag_seconds == 0.0  # clamped -- never a fabricated negative lag

        observation = _build_for_snapshot(
            snapshot, source_mode="live", data_feed="iex", settled_at_utc=settled_at_utc
        )
        wrong_available_at_utc = _iso(
            (snapshot.epoch_anchor + snapshot.timestamp) + snapshot.delivery_lag_seconds
        )
        with pytest.raises(AssertionError):
            assert observation["available_at_utc"] == wrong_available_at_utc
        # The real (measured, never-clamped) value genuinely precedes observed_at_utc.
        assert observation["available_at_utc"] == settled_at_utc
        assert _parse_iso(observation["available_at_utc"]) < _parse_iso(observation["observed_at_utc"])
    finally:
        manager.stop("PGLIVE2")
        await asyncio.sleep(0.02)


# --- TC-9: settled - observed agrees with delivery_lag_seconds (telemetry cross-check only) ---


@pytest.mark.anyio
async def test_settled_minus_observed_agrees_with_delivery_lag_seconds_telemetry_only(monkeypatch):
    record_epoch = 1_800_001_000.0
    fixed_now = record_epoch + 3.25
    monkeypatch.setattr(watch_manager.time, "time", lambda: fixed_now)

    records = [
        RawQuote(record_epoch, 60.0, 60.02, 10, 10),
        RawTrade(record_epoch, 60.01, 20),
    ]
    provider = LiveProvider("PGLAG", _aiter(records), "live PGLAG")
    manager = WatchManager(CONFIG)
    engine = manager.watch_with_async_provider("PGLAG", provider)
    try:
        await _until(lambda: engine.snapshot().event_count >= 1)
        snapshot, settled_at_utc, _ = manager.get_observation_source("PGLAG")
        observed_epoch = snapshot.epoch_anchor + snapshot.timestamp
        settled_epoch = _parse_iso(settled_at_utc)
        assert snapshot.delivery_lag_seconds is not None
        assert settled_epoch - observed_epoch == pytest.approx(
            snapshot.delivery_lag_seconds, abs=1e-6
        )
    finally:
        manager.stop("PGLAG")
        await asyncio.sleep(0.02)


# --- TC-10: availability_basis exhaustive per source_mode; unrecognized mode raises ------------


def test_availability_basis_defined_for_every_recognized_source_mode():
    for source_mode in ("live", "historical", "dataset_replay", "sim"):
        snapshot = _make_snapshot()
        settled = "2026-09-03T00:00:10.000000Z" if source_mode == "live" else None
        observation = _build_for_snapshot(
            snapshot, source_mode=source_mode, data_feed="sim", settled_at_utc=settled
        )
        assert observation["availability_basis"] is not None


def test_availability_basis_matches_the_constitution_table_exactly():
    # Constitution §2's table: `historical` and `dataset_replay` legitimately SHARE
    # `historical_arrival_unknown` (both are "arrival time was never recorded"); `live` and `sim`
    # each own a distinct basis. "Exhaustive per source_mode" means every source_mode resolves to
    # its OWN table-defined value -- not that all four strings are pairwise distinct (they are
    # not, by design).
    def _basis(source_mode: str) -> str:
        settled = "2026-09-03T00:00:10.000000Z" if source_mode == "live" else None
        return _build_for_snapshot(
            _make_snapshot(), source_mode=source_mode, data_feed="sim", settled_at_utc=settled
        )["availability_basis"]

    assert _basis("live") == "live_settled_wall_clock"
    assert _basis("historical") == "historical_arrival_unknown"
    assert _basis("dataset_replay") == "historical_arrival_unknown"
    assert _basis("sim") == "simulated_not_applicable"
    # live and sim are each unique; historical/dataset_replay are the one legitimate pair.
    assert len({_basis("live"), _basis("historical"), _basis("dataset_replay"), _basis("sim")}) == 3


def test_unrecognized_source_mode_raises():
    with pytest.raises(ValueError):
        _build_for_snapshot(_make_snapshot(), source_mode="bogus_mode", data_feed="sim")


# --- TC-11: the pinned ISO function round-trips to the microsecond ---------------------------


def test_pinned_iso_function_round_trips_to_the_microsecond():
    epoch = 1_725_000_000.123456
    formatted = observation_contract._iso_utc(epoch)
    assert formatted.endswith("Z")
    parsed = datetime.fromisoformat(formatted.replace("Z", "+00:00"))
    assert parsed.timestamp() == pytest.approx(epoch, abs=1e-6)


def test_watch_manager_iso_helper_matches_observation_contract_byte_for_byte():
    # This module necessarily duplicates the pinned ISO formatter (this repo's established
    # convention -- see watch_manager._iso_utc's own docstring); cross-check it never drifts
    # from the canonical Constitution §2 format (the TAPE_STATE_VOCABULARY iter-1 precedent).
    for epoch in (1_725_000_000.654321, 0.0, 1_800_000_500.5):
        assert watch_manager._iso_utc(epoch) == observation_contract._iso_utc(epoch)


def test_counterexample_iso_round_trip_detects_a_hand_formatted_string():
    # A hand-formatted string (no microseconds, no "Z"/offset) never equals the pinned function's
    # own output for the same instant -- proving the round-trip equality check is non-vacuous.
    epoch = 1_725_000_000.123456
    hand_formatted = datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    with pytest.raises(AssertionError):
        assert hand_formatted == observation_contract._iso_utc(epoch)


# --- TC-12: two independent DatasetStore.replay reruns yield identical observation_hash ------


def test_dataset_replay_reruns_yield_identical_observation_hash_at_every_tick():
    store = DatasetStore(FIXTURE_DATASETS_J03_DIR)
    first_hashes = [
        _build_for_snapshot(snap, source_mode="dataset_replay", data_feed="sip")["observation_hash"]
        for snap in store.replay(DATASETS_J03_ID, CONFIG)
    ]
    second_hashes = [
        _build_for_snapshot(snap, source_mode="dataset_replay", data_feed="sip")["observation_hash"]
        for snap in store.replay(DATASETS_J03_ID, CONFIG)
    ]
    assert len(first_hashes) == len(second_hashes) > 0
    assert first_hashes == second_hashes


def test_counterexample_replay_hash_comparison_detects_a_mutated_tick():
    store = DatasetStore(FIXTURE_DATASETS_J03_DIR)
    hashes = [
        _build_for_snapshot(snap, source_mode="dataset_replay", data_feed="sip")["observation_hash"]
        for snap in store.replay(DATASETS_J03_ID, CONFIG)
    ]
    mutated = list(hashes)
    mutated[-1] = "0" * 64  # corrupt the last tick's hash
    with pytest.raises(AssertionError):
        assert hashes == mutated


# --- TC-13: app/engine/*.py is free of wall-clock reads, randomness, and git access -----------

_FORBIDDEN_TIME_ATTRS = {("time", "time"), ("datetime", "now"), ("datetime", "utcnow")}


def _engine_clock_randomness_git_violations(source: str) -> list[str]:
    violations: list[str] = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            base, attr = node.value.id, node.attr
            if (base, attr) in _FORBIDDEN_TIME_ATTRS:
                violations.append(f"{base}.{attr}")
            elif base == "random":
                violations.append(f"random.{attr}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in ("subprocess", "random"):
                    violations.append(f"import {alias.name}")
        if isinstance(node, ast.ImportFrom) and node.module in ("subprocess", "random"):
            violations.append(f"from {node.module} import ...")
    return violations


def test_engine_modules_are_free_of_clock_randomness_and_git_access():
    violations: dict[str, list[str]] = {}
    for name in observation_contract.ENGINE_SOURCE_MODULES:
        path = observation_contract._ENGINE_DIR / name
        found = _engine_clock_randomness_git_violations(path.read_text())
        if found:
            violations[name] = found
    assert violations == {}


def test_counterexample_scan_detects_injected_time_time_call():
    fixture_source = "import time\n\ndef f():\n    return time.time()\n"
    assert _engine_clock_randomness_git_violations(fixture_source) != []


def test_counterexample_scan_detects_injected_datetime_now_call():
    fixture_source = "import datetime\n\ndef f():\n    return datetime.now()\n"
    assert _engine_clock_randomness_git_violations(fixture_source) != []


def test_counterexample_scan_detects_injected_random_call():
    fixture_source = "import random\n\ndef f():\n    return random.random()\n"
    assert _engine_clock_randomness_git_violations(fixture_source) != []


def test_counterexample_scan_detects_injected_subprocess_import():
    fixture_source = "import subprocess\n"
    assert _engine_clock_randomness_git_violations(fixture_source) != []
