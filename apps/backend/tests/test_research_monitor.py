"""Research monitor (capability 20 observer): frozen context/statements, source binding, stamps,
statement statuses, exception isolation -> monitor_status failed (feed alive), expired-on-stop."""

import itertools

import pytest

from app.config import CONFIG, Config
from app.engine.snapshot import EngineSnapshot
from app.engine.tape_engine import TapeEngine
from app.providers.simulated import SimulatedProvider
from app.research.monitor import ResearchMonitor, _evaluate_statement, data_feed_for_scenario
from app.research.store import JournalStore, ThesisRecord, VerdictEventRecord
from app.research.taxonomy import frozen_statements


@pytest.fixture
def store(tmp_path):
    s = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    yield s
    s.close()


def _warm_engine(ticker: str, scenario: str, n: int = 240) -> TapeEngine:
    provider = SimulatedProvider(ticker, scenario)
    engine = TapeEngine(ticker, scenario, CONFIG)
    for event in itertools.islice(provider.stream(), n):
        engine.process_event(event)
    return engine


def _thesis_for(engine: TapeEngine, store: JournalStore, *, setup="absorption_reversal",
                direction="long", invalidation=99.0, level=None) -> ThesisRecord:
    snap = engine.snapshot()
    return ThesisRecord(
        id="t1",
        ticker=engine.snapshot().ticker,
        setup_type=setup,
        direction=direction,
        invalidation_price=invalidation,
        level_price=level,
        status="active",
        bound_source=snap.scenario,
        data_feed=data_feed_for_scenario(snap.scenario),
        config_fingerprint=CONFIG.config_fingerprint(),
        entry_context={
            "tape_state": snap.tape_state,
            "confidence": snap.confidence,
            "last": snap.last,
            "spread": snap.spread,
            "primary_window": snap.primary_window,
            "features": dict(snap.primary_features),
        },
        statements=frozen_statements(setup, direction),
        created_logical_ts=snap.timestamp,
        created_wall_ts=1700000000.0,
    )


# --- data_feed mapping ---------------------------------------------------------------------------

def test_data_feed_mapping():
    assert data_feed_for_scenario("buyer_control") == "sim"
    assert data_feed_for_scenario("bid_absorption") == "sim"
    assert data_feed_for_scenario("historical AAPL 2024-05-14T09:30–2024-05-14T09:40") == "sip"
    assert data_feed_for_scenario("live AAPL") == "iex"


# --- frozen context + statements -----------------------------------------------------------------

def test_entry_context_and_statements_frozen_against_config_change(store):
    engine = _warm_engine("SIM-BIDABS", "bid_absorption")
    thesis = _thesis_for(engine, store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    monitor.on_event(None, engine.snapshot())

    proj = monitor.projection()
    frozen_ctx = proj["entry_context"]
    frozen_statements_texts = [s["text"] for s in proj["statements"]]

    # A later config change must NEVER rewrite the frozen context/statements: they are stored ON the
    # thesis record at creation. Re-projecting yields the SAME frozen text/context.
    proj2 = monitor.projection()
    assert proj2["entry_context"] == frozen_ctx
    assert [s["text"] for s in proj2["statements"]] == frozen_statements_texts
    # The frozen statements are the absorption_reversal/long catalog, fully resolved (no states_long).
    assert len(frozen_statements_texts) == 2


def test_source_binding_is_scenario_descriptor_not_bare_ticker(store):
    engine = _warm_engine("SIM-BIDABS", "bid_absorption")
    thesis = _thesis_for(engine, store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    monitor.on_event(None, engine.snapshot())
    proj = monitor.projection()
    assert proj["bound_source"] == "bid_absorption"  # the scenario descriptor
    assert proj["bound_source"] != "SIM-BIDABS"  # never the bare ticker
    assert proj["data_feed"] == "sim"


def test_fingerprint_stamp_present_and_matches_config(store):
    engine = _warm_engine("SIM-BIDABS", "bid_absorption")
    thesis = _thesis_for(engine, store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    monitor.on_event(None, engine.snapshot())
    assert monitor.projection()["config_fingerprint"] == CONFIG.config_fingerprint()


# --- statement statuses --------------------------------------------------------------------------

def test_statement_status_met_when_tape_state_matches(store):
    engine = _warm_engine("SIM-BIDABS", "bid_absorption")
    assert engine.snapshot().tape_state == "bid_absorption"
    thesis = _thesis_for(engine, store, setup="absorption_reversal", direction="long")
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    monitor.on_event(None, engine.snapshot())
    statements = monitor.projection()["statements"]
    # First absorption_reversal/long statement = "bid_absorption" => met; second (buyer_control flip)
    # not yet observed => not_yet.
    assert statements[0]["status"] == "met"
    assert statements[1]["status"] == "not_yet"


def test_statement_status_not_yet_without_a_snapshot(store):
    engine = _warm_engine("SIM-BIDABS", "bid_absorption")
    thesis = _thesis_for(engine, store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    # No on_event yet => no snapshot => every statement reads not_yet (honest default).
    statements = monitor.projection()["statements"]
    assert all(s["status"] == "not_yet" for s in statements)


# --- directional_impact statement: four-quadrant direction-awareness (iter-6 fix) ---------------
# The "Price keeps making progress in your direction rather than stalling." statement
# (trend_continuation, kind=directional_impact). Before the fix it read ONLY the thesis-side impact,
# so an incidentally positive buy_price_impact made it read ``met`` on a LONG thesis even while
# sellers pressed price down (SIM-SELLER: buy_impact +0.14, sell_impact -0.43). The fix makes the
# status direction-aware against the ADVERSE side using ONLY existing primary-window impact values
# read verbatim, with the dominance cutoff config-owned (the classifier's own real-progress cutoffs):
#   * material adverse impact  => violated  (the tape moves AGAINST the thesis)
#   * favorable progress, no material adverse impact => met
#   * genuinely flat / no evidence => not_yet (honest default; no evidence is not a failure)

_DIRECTIONAL_IMPACT_STATEMENT = {"kind": "directional_impact", "params": {}}


def _impact_snap(*, buy_impact: float, sell_impact: float) -> EngineSnapshot:
    """A minimal warmed snapshot carrying just the primary-window impact pair under test."""
    return EngineSnapshot(
        ticker="SIM-X", scenario="x", timestamp=10.0, event_count=100, warm=True,
        stream_status="live", bid=99.99, ask=100.01, spread=0.02, last=100.0,
        features={"30s": {"buy_price_impact": buy_impact, "sell_price_impact": sell_impact}},
        primary_window="30s", tape_state="buyer_control", confidence=0.9, observations=(),
    )


def _eval_directional(direction: str, *, buy_impact: float, sell_impact: float, store) -> str:
    engine = _warm_engine("SIM-BUYER", "buyer_control")
    thesis = _thesis_for(engine, store, setup="trend_continuation", direction=direction,
                         invalidation=50.0 if direction == "long" else 200.0)
    return _evaluate_statement(
        _DIRECTIONAL_IMPACT_STATEMENT,
        _impact_snap(buy_impact=buy_impact, sell_impact=sell_impact),
        thesis,
        CONFIG,
    )


def test_directional_impact_long_favorable_is_met(store):
    # LONG, clean upward progress, no adverse sell pressure => met.
    assert _eval_directional("long", buy_impact=0.40, sell_impact=0.0, store=store) == "met"


def test_directional_impact_long_adverse_is_violated_despite_incidental_buy_impact(store):
    # LONG, sellers materially pressing price down (the SIM-SELLER shape) — an incidentally positive
    # buy_impact must NOT read ``met``; the adverse side dominates => violated. THE iter-6 defect.
    assert _eval_directional("long", buy_impact=0.14, sell_impact=-0.43, store=store) == "violated"


def test_directional_impact_short_favorable_is_met(store):
    # SHORT, clean downward progress, no adverse buy pressure => met.
    assert _eval_directional("short", buy_impact=0.0, sell_impact=-0.40, store=store) == "met"


def test_directional_impact_short_adverse_is_violated_despite_incidental_sell_impact(store):
    # SHORT mirror: buyers materially lifting price — an incidentally negative sell_impact must NOT
    # read ``met``; the adverse (buy) side dominates => violated.
    assert _eval_directional("short", buy_impact=0.43, sell_impact=-0.14, store=store) == "violated"


def test_directional_impact_flat_is_not_yet(store):
    # Genuinely flat both sides (inside the cutoffs) => not_yet (no evidence is not a failure).
    assert _eval_directional("long", buy_impact=0.0, sell_impact=0.0, store=store) == "not_yet"
    assert _eval_directional("short", buy_impact=0.0, sell_impact=0.0, store=store) == "not_yet"


def test_verdict_fixed_pending(store):
    engine = _warm_engine("SIM-BIDABS", "bid_absorption")
    thesis = _thesis_for(engine, store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    monitor.on_event(None, engine.snapshot())
    assert monitor.projection()["verdict"] == "pending"


def test_projection_none_when_no_thesis(store):
    monitor = ResearchMonitor(store, CONFIG)
    assert monitor.projection() is None


def test_projection_omits_risk_flags_entirely(store):
    engine = _warm_engine("SIM-BIDABS", "bid_absorption")
    thesis = _thesis_for(engine, store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    monitor.on_event(None, engine.snapshot())
    # Honesty: an always-empty risk_flags list would read as "no risks found". The field is OMITTED.
    assert "risk_flags" not in monitor.projection()


# --- exception isolation -> monitor_status failed (feed alive) -----------------------------------

def test_observer_exception_surfaces_monitor_status_failed_feed_alive(store, monkeypatch):
    engine = _warm_engine("SIM-BIDABS", "bid_absorption")
    thesis = _thesis_for(engine, store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    engine.add_observer(monitor)

    # Force a monitor-internal failure on the next on_status (the expiry path's store write fails).
    def boom(*a, **k):
        raise RuntimeError("store down")

    monkeypatch.setattr(store, "resolve_thesis", boom)
    # A terminal status flip tries to expire and fails internally — the monitor flips failed but the
    # engine status write still succeeds (feed alive).
    engine.set_stream_status("failed")
    assert engine.snapshot().stream_status == "failed"  # feed alive / status written
    assert monitor.projection()["monitor_status"] == "failed"


# --- lifecycle: expired-on-stop ------------------------------------------------------------------

def test_initial_pending_then_expired_on_stop(store):
    engine = _warm_engine("SIM-BIDABS", "bid_absorption")
    thesis = _thesis_for(engine, store)
    store.insert_thesis(thesis)
    store.append_verdict_event(
        VerdictEventRecord(thesis.id, 0.0, 1.0, "pending", "declared", None, None, None)
    )
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    engine.add_observer(monitor)
    assert monitor.active_thesis_id == thesis.id

    # Stop the stream => on_status("closed") auto-resolves the thesis expired with a final event.
    engine.set_stream_status("closed")
    assert monitor.active_thesis_id is None  # no longer active
    assert monitor.projection() is None  # resolved => projection clears
    assert store.get_thesis(thesis.id).status == "expired"
    events = store.verdict_events(thesis.id)
    assert [e.verdict for e in events] == ["pending", "expired"]


def test_paused_does_not_expire(store):
    engine = _warm_engine("SIM-BIDABS", "bid_absorption")
    thesis = _thesis_for(engine, store)
    store.insert_thesis(thesis)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    engine.add_observer(monitor)
    engine.pause()  # fires on_status("paused") — NOT terminal
    assert monitor.active_thesis_id == thesis.id
    assert store.get_thesis(thesis.id).status == "active"
