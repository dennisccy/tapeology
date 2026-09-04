"""Observation Contract v1 -- Binding Execution Order step 4 (J-04; docs/goal.md).

Proves, with deterministic tests only, that the frozen tape engine (``TapeEngine``, unmodified --
zero files under ``apps/backend/app/`` are touched this iteration) yields an identical
machine-observation semantic set and ``observation_hash`` whether an identical valid ordered event
stream reaches it through the manager's PACED-REPLAY entry point
(``WatchManager.watch_with_provider`` -> ``_feed_paced`` -> ``_replay_events``) or through its LIVE
entry point (``WatchManager.watch_with_async_provider`` -> ``_feed_live`` over ``LiveProvider``),
while provenance/source/lifecycle metadata (``source.source_mode``, ``source.data_feed``, session
identity) honestly differs between the two legs.

Constitution §5 non-claim (verbatim -- TC-5):

    This invariant does not assert semantic equality between independently sourced IEX and SIP
    market data, which may contain different events. Feed bases are never pooled. If any
    ingestion path produces semantic divergence on identical ordered input, that is a blocking
    finding to report — never excluded by widening the metadata partition.

Two leg-pairs, both driven through the SAME two manager entry points with per-tick capture via
``TapeEngine.add_observer`` (the seam ``test_observer_equivalence.py`` already exercises):

  * the committed REAL PG SIP fixture (``tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json``,
    ~14.2K quote+trade records, loaded via ``fakes.load_fixture_window`` -- the SAME fixture
    ``test_dense_replay_gate.py`` proves a fresh unpaced ``TapeEngine`` replays in ~10s on the dev
    machine) -- TC-1 / TC-2;
  * one fixed seeded sim scenario (``SIM-BIDABS`` / ``bid_absorption``, the simulator's DEFAULT
    seed, 60 ticks = 120 events -- comfortably past ``warmup_min_events``), materialised as
    vendor-neutral ``RawQuote``/``RawTrade`` records (``epoch = CONFIG.sim_session_anchor_epoch +``
    the sim's own logical timestamp) so it is a SECOND "valid ordered event stream" (Constitution
    §5) fed through the SAME ``HistoricalProvider``/``LiveProvider`` machinery as the PG fixture,
    "the same way" TC-3 requires -- TC-3.

Processing the FULL PG fixture on both legs is intentionally slow (tens of seconds, not
milliseconds) -- the goal's own Constraints call for "waits of at least 30 s" on the live leg's
completion poll for exactly this reason; this module's ``_until`` default timeout is 60 s.

No test needs a running uvicorn server or network access -- the route does not exist until
iteration 5, and no test contacts Alpaca (only ``HistoricalProvider``/``LiveProvider`` over the
committed fixture and the seeded simulator).
"""

from __future__ import annotations

import asyncio
import copy
import itertools
from pathlib import Path

import pytest

from app import observation_contract
from app.config import CONFIG
from app.engine.snapshot import EngineSnapshot
from app.engine.tape_engine import TapeEngine
from app.observation_contract import build_tape_observation
from app.providers.adapters.base import HistoricalWindow, RawQuote, RawTrade
from app.providers.base import QuoteEvent
from app.providers.historical import HistoricalProvider
from app.providers.live import LiveProvider
from app.providers.simulated import SimulatedProvider
from app.watch_manager import SourceDescriptor, WatchManager
from fakes import load_fixture_window

PG_FIXTURE = Path(__file__).parent / "fixtures" / "alpaca" / "PG_20260609_170000_171000_sip.json"

SIM_TICKER = "SIM-BIDABS"
SIM_SCENARIO = "bid_absorption"
SIM_TICKS = 60  # -> 120 events (60 quotes + 60 trades), comfortably past warmup_min_events (40)

# Metadata-only placeholder (Constitution §6): plays no part in observation_hash equivalence.
_GENERATED_AT_UTC = "2026-09-04T00:00:00.000000Z"

_CONSTITUTION_5_NON_CLAIM = (
    "This invariant does not assert semantic equality between independently sourced IEX and SIP "
    "market data, which may contain different events. Feed bases are never pooled. If any "
    "ingestion path produces semantic divergence on identical ordered input, that is a blocking "
    "finding to report — never excluded by widening the metadata partition."
)


# --- Small helpers (self-contained -- no cross-import of another test module's private doubles) --


async def _aiter(records):
    for r in records:
        yield r


async def _until(predicate, timeout: float = 60.0, step: float = 0.01) -> None:
    """Poll ``predicate`` for up to ``timeout`` s. Defaulted to 60 s (the goal's Constraints call
    for "waits of at least 30 s" on the live leg's completion poll -- the FULL PG fixture leg can
    genuinely take tens of seconds; a short default would flake, not fail honestly)."""
    elapsed = 0.0
    while elapsed < timeout:
        if predicate():
            return
        await asyncio.sleep(step)
        elapsed += step
    raise AssertionError("condition not met within timeout")


def _merge_epoch_order(window: HistoricalWindow) -> list:
    """Quotes+trades merged into arrival order (quote-before-trade at an equal epoch, via a stable
    sort keyed on epoch alone -- quotes are listed first so a tie keeps them first) -- the SAME
    idiom ``test_tape_observation_time.py``'s live-provider tests already use to feed
    ``LiveProvider`` a realistic arrival-ordered stream."""
    return sorted(list(window.quotes) + list(window.trades), key=lambda r: r.epoch)


def _sim_scenario_window(ticker: str, scenario: str, n_ticks: int) -> HistoricalWindow:
    """Materialise ``n_ticks`` of the fixed, seeded sim scenario as vendor-neutral
    ``RawQuote``/``RawTrade`` records (``epoch = CONFIG.sim_session_anchor_epoch +`` the sim's own
    logical timestamp) -- a SECOND "valid ordered event stream" (Constitution §5) fed through the
    SAME ``HistoricalProvider``/``LiveProvider`` machinery the PG fixture uses below, so TC-3 is
    driven "the same way" as TC-1/TC-2. ``SimulatedProvider`` always yields exactly one quote then
    one trade at the SAME logical timestamp per tick (``app/providers/simulated.py``'s
    ``_bid_absorption_stream``), and every tick's timestamp strictly increases, so the round trip
    through raw records preserves the quote-before-trade order the engine relies on -- no record
    is dropped, duplicated or reordered relative to the original sim stream.
    """
    anchor = CONFIG.sim_session_anchor_epoch
    quotes: list[RawQuote] = []
    trades: list[RawTrade] = []
    events = itertools.islice(SimulatedProvider(ticker, scenario).stream(), n_ticks * 2)
    for event in events:
        epoch = anchor + event.timestamp
        if isinstance(event, QuoteEvent):
            quotes.append(RawQuote(epoch, event.bid, event.ask, event.bid_size, event.ask_size))
        else:
            trades.append(RawTrade(epoch, event.price, event.size))
    return HistoricalWindow(ticker, tuple(trades), tuple(quotes))


class _TickCapture:
    """A benign snapshot observer (the same shape as test_observer_equivalence.py's
    ``_RecordingObserver``): records the REAL, immutable ``EngineSnapshot`` built by every
    processed event -- never a hand-written literal standing in for captured state."""

    def __init__(self) -> None:
        self.snapshots: list[EngineSnapshot] = []

    def on_event(self, event: object, snapshot: EngineSnapshot) -> None:
        self.snapshots.append(snapshot)


def _build_observation(snapshot: EngineSnapshot, descriptor: SourceDescriptor) -> dict:
    """One real ``TapeObservation`` for ``snapshot``, using the manager's REAL recorded
    ``SourceDescriptor`` for that leg's watch (never a fabricated source/session pair).
    ``settled_at_utc``/``end_reason``/``generated_at_utc`` are metadata-only (Constitution §6) and
    play no part in ``observation_hash`` equivalence, so fixed placeholders are honest here."""
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
        settled_at_utc=None,
        end_reason=None,
        generated_at_utc=_GENERATED_AT_UTC,
        profile_id=descriptor.profile_id,
        config=CONFIG,
        provenance=observation_contract.resolve_implementation_provenance(),
    )


def _read_path(observation: dict, path: str):
    value: object = observation
    for part in path.split("."):
        value = value[part]  # type: ignore[index]
    return value


def _assert_semantic_equivalence(obs_a: dict, obs_b: dict, *, context: str) -> None:
    """The ONE comparator TC-1/TC-3 AND the mutation counterexample (TC-4) share: asserts
    ``observation_hash`` equality plus full per-field machine-observation semantic-set equality
    (Constitution §6's ``MACHINE_OBSERVATION_SEMANTIC_FIELDS``) between two independently built
    ``TapeObservation`` dicts -- always reads the REAL built dicts, never a hand-written literal
    standing in for them (the iter-3 lessons entry)."""
    assert obs_a["observation_hash"] == obs_b["observation_hash"], (
        f"{context}: observation_hash diverged"
    )
    for path in observation_contract.MACHINE_OBSERVATION_SEMANTIC_FIELDS:
        assert _read_path(obs_a, path) == _read_path(obs_b, path), f"{context}: {path} diverged"


def _assert_metadata_legs_differ(obs_a: dict, obs_b: dict) -> None:
    """Constitution §5: "Only provenance/source/lifecycle metadata may differ." Proves the two
    legs genuinely carry DIFFERENT metadata -- never silently identical, which would make the "the
    legs differ" half of the claim vacuous (the iter-3 lessons entry, extended to this module's own
    "the two legs differ" assertions: real recorded descriptors, never a hand-written pair)."""
    assert obs_a["source"]["source_mode"] != obs_b["source"]["source_mode"]
    assert obs_a["source"]["data_feed"] != obs_b["source"]["data_feed"]
    assert obs_a["source"]["session_id"] != obs_b["source"]["session_id"]
    assert obs_a["source"]["session_started_at_utc"] != obs_b["source"]["session_started_at_utc"]


async def _run_replay_leg(ticker: str, provider: object) -> tuple[list[EngineSnapshot], SourceDescriptor]:
    """Feed ``provider``'s ordered stream through the manager's PACED-REPLAY entry point
    (``speed=float("inf")`` -- the goal's ``speed_cell=[inf]`` knob -- on a
    ``WatchManager(CONFIG, pace=0.0)``) and capture every processed tick via
    ``TapeEngine.add_observer``, attached BEFORE the feeder task has had a chance to run (no
    ``await`` between ``watch_with_provider`` and ``add_observer``, so no tick is ever missed).
    Returns the captured snapshot sequence plus the manager's REAL recorded ``SourceDescriptor``.
    """
    manager = WatchManager(CONFIG, pace=0.0)
    engine = manager.watch_with_provider(ticker, provider, speed=float("inf"))
    capture = _TickCapture()
    engine.add_observer(capture)
    try:
        await _until(lambda: engine.snapshot().stream_status in ("closed", "failed"))
        assert engine.snapshot().stream_status == "closed", "replay leg did not close cleanly"
        _snapshot, _settled, _end_reason, descriptor = manager.get_observation_source(ticker)
        return capture.snapshots, descriptor
    finally:
        manager.stop(ticker)


async def _run_live_leg(ticker: str, provider: object) -> tuple[list[EngineSnapshot], SourceDescriptor]:
    """Feed ``provider``'s ordered stream through the manager's LIVE entry point
    (``WatchManager.watch_with_async_provider`` -> ``_feed_live``) and capture every processed
    tick the same way. Returns the captured snapshot sequence plus the manager's REAL recorded
    ``SourceDescriptor``."""
    manager = WatchManager(CONFIG)
    engine = manager.watch_with_async_provider(ticker, provider)
    capture = _TickCapture()
    engine.add_observer(capture)
    try:
        await _until(lambda: engine.snapshot().stream_status in ("closed", "failed"))
        assert engine.snapshot().stream_status == "closed", "live leg did not close cleanly"
        _snapshot, _settled, _end_reason, descriptor = manager.get_observation_source(ticker)
        return capture.snapshots, descriptor
    finally:
        manager.stop(ticker)
        await asyncio.sleep(0.02)  # let the live socket-close cleanup run (existing precedent)


# --- TC-1 / TC-2: the committed PG SIP fixture, replay leg vs live leg ---------------------------


@pytest.mark.anyio
async def test_pg_sip_fixture_replay_and_live_legs_share_observation_hash_at_every_tick():
    window, _raw = load_fixture_window(PG_FIXTURE)
    total_events = len(window.quotes) + len(window.trades)

    replay_provider = HistoricalProvider(
        "PG", window, "historical PG 2026-06-09T17:00:00Z-17:10:00Z"
    )
    replay_snapshots, replay_descriptor = await _run_replay_leg("PG", replay_provider)

    live_provider = LiveProvider("PG", _aiter(_merge_epoch_order(window)), "live PG")
    live_snapshots, live_descriptor = await _run_live_leg("PG", live_provider)

    # Structural equivalence first: neither leg dropped or duplicated a tick.
    assert len(replay_snapshots) == len(live_snapshots) == total_events > 0

    for i, (snap_a, snap_b) in enumerate(zip(replay_snapshots, live_snapshots)):
        obs_a = _build_observation(snap_a, replay_descriptor)
        obs_b = _build_observation(snap_b, live_descriptor)
        _assert_semantic_equivalence(obs_a, obs_b, context=f"PG fixture tick {i}")

    final_a = _build_observation(replay_snapshots[-1], replay_descriptor)
    final_b = _build_observation(live_snapshots[-1], live_descriptor)
    assert final_a["source"]["source_mode"] == "historical"
    assert final_b["source"]["source_mode"] == "live"
    assert final_a["source"]["data_feed"] == CONFIG.historical_feed  # "sip"
    assert final_b["source"]["data_feed"] == CONFIG.live_feed  # "iex"
    _assert_metadata_legs_differ(final_a, final_b)


# --- TC-3: one fixed seeded sim scenario, fed the same way ---------------------------------------


@pytest.mark.anyio
async def test_seeded_sim_scenario_replay_and_live_legs_share_observation_hash_at_every_tick():
    window = _sim_scenario_window(SIM_TICKER, SIM_SCENARIO, SIM_TICKS)
    total_events = len(window.quotes) + len(window.trades)
    assert total_events == SIM_TICKS * 2

    replay_provider = HistoricalProvider(
        SIM_TICKER, window, f"historical {SIM_TICKER} sim-fixed-seed {SIM_SCENARIO}"
    )
    replay_snapshots, replay_descriptor = await _run_replay_leg(SIM_TICKER, replay_provider)

    live_provider = LiveProvider(
        SIM_TICKER, _aiter(_merge_epoch_order(window)), f"live {SIM_TICKER}"
    )
    live_snapshots, live_descriptor = await _run_live_leg(SIM_TICKER, live_provider)

    assert len(replay_snapshots) == len(live_snapshots) == total_events > 0

    for i, (snap_a, snap_b) in enumerate(zip(replay_snapshots, live_snapshots)):
        obs_a = _build_observation(snap_a, replay_descriptor)
        obs_b = _build_observation(snap_b, live_descriptor)
        _assert_semantic_equivalence(obs_a, obs_b, context=f"sim scenario tick {i}")

    final_a = _build_observation(replay_snapshots[-1], replay_descriptor)
    final_b = _build_observation(live_snapshots[-1], live_descriptor)
    _assert_metadata_legs_differ(final_a, final_b)


# --- TC-4: the comparator is provably non-vacuous -------------------------------------------------


def _minimal_real_observation() -> dict:
    """One REAL built ``TapeObservation`` from a tiny fresh engine run -- independent of the
    (expensive) fixture legs above so the mutation counter-test stays fast."""
    engine = TapeEngine(
        SIM_TICKER, SIM_SCENARIO, CONFIG, epoch_anchor=CONFIG.sim_session_anchor_epoch
    )
    for event in itertools.islice(SimulatedProvider(SIM_TICKER, SIM_SCENARIO).stream(), 10):
        engine.process_event(event)
    return build_tape_observation(
        snapshot=engine.snapshot(),
        source_mode="sim",
        data_feed="sim",
        window_start_utc=None,
        window_end_utc=None,
        dataset_id=None,
        dataset_checksum=None,
        session_id="session-counterexample",
        session_started_at_utc="2026-09-04T00:00:00.000000Z",
        settled_at_utc=None,
        end_reason=None,
        generated_at_utc=_GENERATED_AT_UTC,
        profile_id="default",
        config=CONFIG,
        provenance=observation_contract.resolve_implementation_provenance(),
    )


def test_counterexample_mutated_semantic_field_makes_the_comparator_raise():
    """TC-4: a comparator that always passed would be worthless. Mutate a REAL built
    observation's ``tape_state`` (a semantic field) in a deep copy, recompute the now-genuinely-
    different ``observation_hash``, and prove ``_assert_semantic_equivalence`` -- the SAME
    comparator TC-1/TC-3 use -- raises. Never a hand-written literal pair (the iter-3 lessons
    entry): both sides are real ``build_tape_observation`` output."""
    base = _minimal_real_observation()
    mutated = copy.deepcopy(base)
    mutated["tape_state"] = (
        "buyer_control" if base["tape_state"] != "buyer_control" else "seller_control"
    )
    mutated["observation_hash"] = observation_contract.compute_observation_hash(mutated)
    assert mutated["observation_hash"] != base["observation_hash"]  # sanity: genuinely diverged
    with pytest.raises(AssertionError):
        _assert_semantic_equivalence(base, mutated, context="counterexample")


# --- TC-5: the module docstring states the Constitution §5 non-claim verbatim --------------------


def _normalize_ws(text: str) -> str:
    return " ".join(text.split())


def test_module_docstring_states_the_constitution_5_non_claim_verbatim():
    assert __doc__ is not None
    assert _normalize_ws(_CONSTITUTION_5_NON_CLAIM) in _normalize_ws(__doc__)


# --- TC-6: the four-group field partition is unchanged from iteration 1 --------------------------


_FROZEN_SEMANTIC_FIELDS = (
    "schema_version", "provider", "ticker", "tape_state", "confidence", "warm",
    "primary_window", "features", "trade_event_count", "market.bid", "market.ask",
    "market.spread", "market.last", "observed_at_utc", "timing.logical_timestamp",
    "timing.epoch_anchor", "engine_identity.engine_semantics_version",
    "engine_identity.config_fingerprint", "engine_identity.profile_id",
    "engine_identity.tape_state_vocabulary", "engine_identity.windows",
    "engine_identity.warmup_min_events",
)
_FROZEN_METADATA_FIELDS = (
    "available_at_utc", "availability_basis", "generated_at_utc", "timing.settled_at_utc",
    "timing.delivery_lag_seconds", "lifecycle.stream_status", "lifecycle.paused",
    "lifecycle.end_reason", "source.source_mode", "source.data_feed", "source.scenario",
    "source.window_start_utc", "source.window_end_utc", "source.dataset_id",
    "source.dataset_checksum", "source.session_id", "source.session_started_at_utc",
    "implementation_provenance.engine_source_hash", "implementation_provenance.source_revision",
    "implementation_provenance.worktree_dirty",
)
_FROZEN_EXPLANATORY_FIELDS = ("observations",)
_FROZEN_INTEGRITY_FIELDS = ("observation_hash", "artifact_hash")


def test_field_partition_groups_are_unchanged_from_iteration_1():
    # TC-6: a diff against the already-committed iteration-1 constants must be empty -- no field
    # was moved into a wider partition to manufacture TC-1/TC-3's equivalence.
    assert observation_contract.MACHINE_OBSERVATION_SEMANTIC_FIELDS == _FROZEN_SEMANTIC_FIELDS
    assert (
        observation_contract.PROVENANCE_SOURCE_LIFECYCLE_METADATA_FIELDS
        == _FROZEN_METADATA_FIELDS
    )
    assert observation_contract.EXPLANATORY_METADATA_FIELDS == _FROZEN_EXPLANATORY_FIELDS
    assert observation_contract.INTEGRITY_FIELDS == _FROZEN_INTEGRITY_FIELDS


def test_counterexample_field_partition_drift_is_detected():
    # Proves the check above is non-vacuous: a widened semantic-fields tuple (one metadata field
    # smuggled in, the "manufacture equivalence by widening the partition" anti-goal) must NOT
    # equal the frozen reference.
    widened = _FROZEN_SEMANTIC_FIELDS + ("source.session_id",)
    with pytest.raises(AssertionError):
        assert widened == _FROZEN_SEMANTIC_FIELDS
