"""J-68 (automated core) — the engine snapshot-observer seam is byte-identical when attached.

The research evolution attaches everything (the future verdict monitor) to ONE place: the
``TapeEngine`` observer seam (capability 20). This iteration builds only the inert seam and proves
its keystone anti-goal: the SAME ordered event stream yields **byte-identical** engine outputs with
observers attached or absent. "Byte-identical" means the *serialized projections* — the exact dicts
``app.serializers`` feeds REST/WS, plus the history projection — compare equal, not Python object
identity (that is the form the anti-goal and J-68 specify and the form later research must preserve).

The three legs:
  * a clean no-observer run vs a clean recording-observer run — projections equal at every assertion
    point including the final;
  * a deliberately-throwing observer leg — processing still COMPLETES, the outputs stay byte-identical
    to the no-observer run, and the failure is RECORDED (per-observer failed flag) and LOGGED, never
    silently swallowed;
  * ``on_status`` fires for EVERY status writer (``set_stream_status``, ``pause``, ``resume``, and the
    internal ``connecting/waiting -> live`` promotion inside ``process_event``) — status flips do not
    pass through ``on_event``, so the future stale/closed/failed handling REQUIRES this hook.
"""

import itertools
import logging

from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.providers.simulated import SimulatedProvider
from app.serializers import serialize_history, serialize_stream

# A fixed, seeded scenario stream (the existing convention in test_scenario.py). Long enough to
# warm up, resolve a meaningful state (so markers/observations/event-log all populate), and exercise
# the chart history buffer.
_SCENARIO_TICKER = "SIM-BUYER"
_SCENARIO = "buyer_control"
_N_EVENTS = 240
# Assertion points sampled DURING the stream plus the final — equivalence must hold throughout,
# not merely at the end (a research observer that only corrupted mid-stream must still be caught).
_ASSERT_AT = (40, 80, 160, _N_EVENTS)
_BAR = CONFIG.history_bar_sizes[0]


class _RecordingObserver:
    """A benign observer: records every callback. It MUST NOT influence engine output."""

    def __init__(self) -> None:
        self.events: list = []
        self.statuses: list[str] = []

    def on_event(self, event, snapshot) -> None:
        self.events.append((event, snapshot))

    def on_status(self, status: str) -> None:
        self.statuses.append(status)


class _ThrowingObserver:
    """An observer that raises in BOTH callbacks — must be isolated, recorded, and logged."""

    def __init__(self) -> None:
        self.on_event_calls = 0
        self.on_status_calls = 0

    def on_event(self, event, snapshot) -> None:
        self.on_event_calls += 1
        raise RuntimeError("boom in on_event")

    def on_status(self, status: str) -> None:
        self.on_status_calls += 1
        raise RuntimeError("boom in on_status")


def _events(n: int = _N_EVENTS):
    provider = SimulatedProvider(_SCENARIO_TICKER, _SCENARIO)
    return list(itertools.islice(provider.stream(), n))


def _projections(engine: TapeEngine) -> tuple[dict, dict]:
    """The two serialized projections used as the byte-identical comparison surface."""
    return (
        serialize_stream(engine.snapshot()),
        serialize_history(engine.history, _BAR, engine.epoch_anchor),
    )


def test_outputs_byte_identical_with_recording_observer_attached():
    events = _events()
    plain = TapeEngine(_SCENARIO_TICKER, _SCENARIO, CONFIG)
    observed = TapeEngine(_SCENARIO_TICKER, _SCENARIO, CONFIG)
    obs = _RecordingObserver()
    observed.add_observer(obs)

    for i, event in enumerate(events, start=1):
        plain.process_event(event)
        observed.process_event(event)
        if i in _ASSERT_AT:
            assert _projections(plain) == _projections(observed), f"diverged at event {i}"

    # Final equivalence (redundant with the last _ASSERT_AT entry, asserted explicitly).
    assert _projections(plain) == _projections(observed)
    # The observer genuinely saw every processed event (it was actually attached, not a no-op test).
    assert len(obs.events) == len(events)


def test_throwing_observer_does_not_alter_outputs_and_is_recorded_and_logged(caplog):
    events = _events()
    plain = TapeEngine(_SCENARIO_TICKER, _SCENARIO, CONFIG)
    observed = TapeEngine(_SCENARIO_TICKER, _SCENARIO, CONFIG)
    thrower = _ThrowingObserver()
    handle = observed.add_observer(thrower)

    with caplog.at_level(logging.ERROR):
        for i, event in enumerate(events, start=1):
            # (a) processing COMPLETES — the throwing observer never propagates out of process_event.
            plain.process_event(event)
            observed.process_event(event)
            if i in _ASSERT_AT:
                # (b) outputs remain byte-identical to the no-observer run.
                assert _projections(plain) == _projections(observed), f"diverged at event {i}"

    assert _projections(plain) == _projections(observed)
    # The observer was actually invoked (it really threw, the test is not vacuous).
    assert thrower.on_event_calls == len(events)
    # (c) the failure is RECORDED on a per-observer failed flag the future research monitor reads...
    assert observed.observer_failed(handle) is True
    # ...and LOGGED, never silently swallowed.
    assert any("observer" in r.getMessage().lower() for r in caplog.records)


def test_on_status_fires_for_every_status_writer():
    # Status flips do NOT pass through on_event, so on_status MUST fire from every writer.
    engine = TapeEngine(_SCENARIO_TICKER, _SCENARIO, CONFIG)
    obs = _RecordingObserver()
    engine.add_observer(obs)

    # 1) the internal connecting/waiting -> live promotion inside process_event (first event)...
    engine.set_stream_status("waiting")
    assert obs.statuses[-1] == "waiting"
    first_event = _events(1)[0]
    engine.process_event(first_event)
    assert "live" in obs.statuses  # the internal promotion fired on_status

    # 2) explicit set_stream_status...
    engine.set_stream_status("stale")
    assert obs.statuses[-1] == "stale"

    # 3) pause flips to "paused"...
    engine.pause()
    assert obs.statuses[-1] == "paused"

    # 4) resume restores the pre-pause status ("stale") and fires on_status with it.
    engine.resume()
    assert obs.statuses[-1] == "stale"


def test_throwing_observer_on_status_isolated_and_recorded(caplog):
    # A status-only failure (no events) must also be isolated + recorded + logged, and must not
    # break the status writer for the rest of the engine.
    engine = TapeEngine(_SCENARIO_TICKER, _SCENARIO, CONFIG)
    thrower = _ThrowingObserver()
    handle = engine.add_observer(thrower)
    with caplog.at_level(logging.ERROR):
        engine.set_stream_status("stale")  # fires on_status, which raises
    assert thrower.on_status_calls >= 1
    assert engine.observer_failed(handle) is True
    # The status write itself still succeeded despite the observer raising.
    assert engine.snapshot().stream_status == "stale"


def test_engine_is_research_agnostic_no_research_imports():
    # The engine module must import NOTHING research-shaped this iteration — observers are opaque.
    import app.engine.tape_engine as te

    source = open(te.__file__).read()
    for forbidden in ("import research", "from .research", "from ..research", "research."):
        assert forbidden not in source, f"engine leaked a research reference: {forbidden!r}"


# --- iter-2 extension: the REAL research monitor attached, no thesis declared --------------------
# The keystone anti-goal re-proven against the ACTUAL research monitor (not just the test double):
# attaching the real monitor with NO thesis declared must leave the engine's serialized projections
# byte-identical to a no-observer run. This is the equivalence the whole research layer rests on.

def test_real_monitor_attached_outputs_byte_identical(tmp_path):
    from app.research.monitor import ResearchMonitor
    from app.research.store import JournalStore

    store = JournalStore(str(tmp_path / "equiv.db"), CONFIG)
    try:
        events = _events()
        plain = TapeEngine(_SCENARIO_TICKER, _SCENARIO, CONFIG)
        observed = TapeEngine(_SCENARIO_TICKER, _SCENARIO, CONFIG)
        monitor = ResearchMonitor(store, CONFIG)
        observed.add_observer(monitor)

        for i, event in enumerate(events, start=1):
            plain.process_event(event)
            observed.process_event(event)
            if i in _ASSERT_AT:
                assert _projections(plain) == _projections(observed), f"diverged at event {i}"
        assert _projections(plain) == _projections(observed)
        # The monitor with no thesis serves a null projection — and never perturbed the engine.
        assert monitor.projection() is None
    finally:
        store.close()


def test_real_monitor_with_thesis_does_not_alter_engine_outputs(tmp_path):
    # Even with an ACTIVE thesis attached AND the verdict-transition engine evaluating every event
    # (capability 24), the engine's serialized projections stay byte-identical — the monitor +
    # evaluator are read-only over the engine (the iter-4 re-proof of the equivalence anti-goal).
    import itertools

    from app.providers.simulated import SimulatedProvider
    from app.research.monitor import ResearchMonitor, data_feed_for_scenario
    from app.research.store import JournalStore, ThesisRecord
    from app.research.taxonomy import frozen_statements

    store = JournalStore(str(tmp_path / "equiv2.db"), CONFIG)
    try:
        events = _events()
        plain = TapeEngine(_SCENARIO_TICKER, _SCENARIO, CONFIG)
        observed = TapeEngine(_SCENARIO_TICKER, _SCENARIO, CONFIG)
        monitor = ResearchMonitor(store, CONFIG)
        # Warm a separate engine to build a realistic frozen thesis, then attach + activate it.
        warm = TapeEngine(_SCENARIO_TICKER, _SCENARIO, CONFIG)
        for e in itertools.islice(SimulatedProvider(_SCENARIO_TICKER, _SCENARIO).stream(), 60):
            warm.process_event(e)
        snap = warm.snapshot()
        thesis = ThesisRecord(
            id="t1",
            ticker=_SCENARIO_TICKER,
            setup_type="trend_continuation",
            direction="long",
            invalidation_price=(snap.last or 100.0) - 1.0,
            level_price=None,
            status="active",
            bound_source=snap.scenario,
            data_feed=data_feed_for_scenario(snap.scenario, CONFIG),
            config_fingerprint=CONFIG.config_fingerprint(),
            entry_context={"last": snap.last},
            statements=frozen_statements("trend_continuation", "long"),
            created_logical_ts=snap.timestamp,
            created_wall_ts=0.0,
        )
        monitor.set_thesis(thesis)
        observed.add_observer(monitor)

        for i, event in enumerate(events, start=1):
            plain.process_event(event)
            observed.process_event(event)
            if i in _ASSERT_AT:
                assert _projections(plain) == _projections(observed), f"diverged at event {i}"
        assert _projections(plain) == _projections(observed)
        # The verdict engine REALLY ran (not a no-op): on SIM-BUYER trend_continuation/long it
        # published confirming during the run — yet the engine outputs above are still byte-identical
        # to the no-observer run, so the verdict evaluation is genuinely read-only over the engine.
        assert monitor.projection()["verdict"] == "confirming"
    finally:
        store.close()
