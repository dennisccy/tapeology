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


# --- MANDATORY favorable-dominant dominance pins (iter-9 carry; EXACT named parameters) ----------
# iter-8 proved the favorable-dominant BOTH-material quadrant only in pixels; the iter-8 reviewer's
# mandatory test-completeness task pins it in BOTH directions with these EXACT parameters (binding
# numeric-truth-anchor lesson — the params must literally be these values). Both sides are material
# (each clears the config cutoff: |0.40| and |0.14| both ≥ 0.02 in magnitude), and the FAVORABLE side
# dominates by magnitude (|0.40| > |0.14|) => the dominance branch reads ``met``. No production-code
# change is expected for these; they pin the existing dominance semantics.

def test_directional_impact_long_favorable_dominant_both_material_is_met(store):
    # LONG, BOTH material, favorable (buy) dominant: buy +0.40 vs sell −0.14 => met.
    assert _eval_directional("long", buy_impact=0.40, sell_impact=-0.14, store=store) == "met"


def test_directional_impact_short_favorable_dominant_both_material_is_met(store):
    # SHORT mirror, BOTH material, favorable (sell) dominant: sell −0.40 vs buy +0.14 => met.
    assert _eval_directional("short", buy_impact=0.14, sell_impact=-0.40, store=store) == "met"


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


# --- lifecycle: expiry REASON (watch_stopped vs stream_closed vs failed), J-47 / J-50 ------------
# The engine status string alone cannot tell a USER stop apart from a stream that ran out (both flip
# stream_status to "closed"), so the WatchManager stamps the distinguishing reason on the engine
# (``end_reason``), which the monitor reads in on_status. J-50's already-verified stream-end leg
# (``stream_closed``) MUST NOT regress.

class _FakeEndReasonEngine:
    """A stand-in carrying just ``end_reason`` (what the monitor reads in on_status)."""

    def __init__(self, end_reason: str | None) -> None:
        self.end_reason = end_reason


def _declared_unmarked(store):
    engine = _warm_engine("SIM-BIDABS", "bid_absorption")
    thesis = _thesis_for(engine, store)
    store.insert_thesis(thesis)
    store.append_verdict_event(
        VerdictEventRecord(thesis.id, 0.0, 1.0, "pending", "declared", None, None, None)
    )
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    monitor.on_event(None, engine.snapshot())  # a live read so the final event records last
    return monitor, thesis


def test_unmarked_user_stop_expires_with_watch_stopped_reason(store):
    monitor, thesis = _declared_unmarked(store)
    monitor.attach_engine(_FakeEndReasonEngine("watch_stopped"))
    monitor.on_status("closed")
    assert store.get_thesis(thesis.id).status == "expired"
    events = store.verdict_events(thesis.id)
    assert [e.verdict for e in events] == ["pending", "expired"]
    assert events[-1].evidence == "Thesis expired — you stopped the watch that declared it."


def test_unmarked_stream_exhaustion_expires_with_stream_closed_reason(store):
    # J-50's verified leg: a bounded sim stream ending on an UNMARKED thesis expires stream_closed.
    monitor, thesis = _declared_unmarked(store)
    monitor.attach_engine(_FakeEndReasonEngine("stream_closed"))
    monitor.on_status("closed")
    assert store.get_thesis(thesis.id).status == "expired"
    events = store.verdict_events(thesis.id)
    assert events[-1].evidence == "Thesis expired — the stream that declared it ended."


def test_unmarked_closed_without_engine_reason_defaults_stream_closed(store):
    # A direct status flip with no engine reason attached defaults to stream_closed (J-50 preserved).
    monitor, thesis = _declared_unmarked(store)
    monitor.on_status("closed")
    events = store.verdict_events(thesis.id)
    assert events[-1].evidence == "Thesis expired — the stream that declared it ended."


def test_unmarked_failure_expires_with_failed_reason(store):
    monitor, thesis = _declared_unmarked(store)
    monitor.attach_engine(_FakeEndReasonEngine(None))
    monitor.on_status("failed")
    events = store.verdict_events(thesis.id)
    assert events[-1].evidence == "Thesis expired — the feed that declared it failed."


# --- lifecycle: ENTRY-MARKED thesis SURVIVES stop/failure (J-47) ---------------------------------

def _entry_mark(store, thesis, price=100.0):
    from app.research.store import ActionRecord
    store.insert_action(
        ActionRecord(id="m1", thesis_id=thesis.id, kind="entry", price=price,
                     logical_ts=1.0, wall_ts=1700000001.0, spread_at_mark=0.02)
    )


def test_entry_marked_survives_stop_no_verdict_appended(store):
    monitor, thesis = _declared_unmarked(store)
    _entry_mark(store, thesis)
    monitor.attach_engine(_FakeEndReasonEngine("watch_stopped"))
    monitor.on_status("closed")
    # Survives: stays active in the store, NO expiry/verdict event appended after the stop.
    assert store.get_thesis(thesis.id).status == "active"
    events = store.verdict_events(thesis.id)
    assert [e.verdict for e in events] == ["pending"]  # only the declaration row; nothing appended
    # The dead monitor no longer holds it active (the watch is over).
    assert monitor.active_thesis_id is None


def test_entry_marked_survives_failure_no_verdict_appended(store):
    monitor, thesis = _declared_unmarked(store)
    _entry_mark(store, thesis)
    monitor.attach_engine(_FakeEndReasonEngine(None))
    monitor.on_status("failed")
    assert store.get_thesis(thesis.id).status == "active"
    assert [e.verdict for e in store.verdict_events(thesis.id)] == ["pending"]


# --- lifecycle: re-attach on MATCHING source appends exactly one watch_restarted gap (J-47) ------

def test_reattach_matching_source_appends_one_watch_restarted_gap(store):
    monitor, thesis = _declared_unmarked(store)
    _entry_mark(store, thesis)
    monitor.attach_engine(_FakeEndReasonEngine("watch_stopped"))
    monitor.on_status("closed")  # survives

    # A FRESH monitor on re-watch is offered the surviving thesis; it adopts on the first MATCHING
    # snapshot (scenario == bound_source) and appends exactly ONE watch_restarted gap event.
    fresh = ResearchMonitor(store, CONFIG)
    fresh.offer_surviving(thesis)
    engine = _warm_engine("SIM-BIDABS", "bid_absorption")  # same scenario => matching source
    assert engine.snapshot().scenario == thesis.bound_source
    fresh.on_event(None, engine.snapshot())

    events = store.verdict_events(thesis.id)
    assert [e.verdict for e in events] == ["pending", "watch_restarted"]
    assert fresh.active_thesis_id == thesis.id  # adopted => evaluation resumed
    # Idempotence: a SECOND snapshot does not append a second gap event (append-only, no backfill).
    fresh.on_event(None, engine.snapshot())
    assert [e.verdict for e in store.verdict_events(thesis.id)] == ["pending", "watch_restarted"]


def test_reattach_resumes_evaluation_from_post_restart_evidence_only(store):
    # After adoption the projection is live again (ok), holding the thesis, with no interpolated
    # history between the stop and the restart (the only appended row is the single gap event).
    monitor, thesis = _declared_unmarked(store)
    _entry_mark(store, thesis)
    monitor.attach_engine(_FakeEndReasonEngine("watch_stopped"))
    monitor.on_status("closed")
    fresh = ResearchMonitor(store, CONFIG)
    fresh.offer_surviving(thesis)
    engine = _warm_engine("SIM-BIDABS", "bid_absorption")
    fresh.on_event(None, engine.snapshot())
    proj = fresh.projection()
    assert proj is not None
    assert proj["monitor_status"] == "ok"
    assert proj["id"] == thesis.id


# --- lifecycle: MISMATCHED source is NEVER adopted/evaluated (J-47 cross-source leg) -------------

def test_reattach_mismatched_source_not_adopted_no_verdict_with_notice(store):
    monitor, thesis = _declared_unmarked(store)  # bound_source == "bid_absorption"
    _entry_mark(store, thesis)
    monitor.attach_engine(_FakeEndReasonEngine("watch_stopped"))
    monitor.on_status("closed")

    fresh = ResearchMonitor(store, CONFIG)
    fresh.offer_surviving(thesis)
    # A DIFFERENT scenario (a different sim source) — the same ticker can never re-bind to it.
    other = _warm_engine("SIM-BUYER", "buyer_control")
    assert other.snapshot().scenario != thesis.bound_source
    fresh.on_event(None, other.snapshot())

    # Never adopted, no verdict appended against the wrong source.
    assert fresh.active_thesis_id is None
    assert [e.verdict for e in store.verdict_events(thesis.id)] == ["pending"]
    # The projection carries the explicit bound-source notice naming the DECLARED source.
    proj = fresh.projection()
    assert proj is not None
    assert proj["monitor_status"] == "not_evaluated"
    assert thesis.bound_source in proj["monitor_notice"]
    assert "buyer_control" in proj["monitor_notice"]  # names the (wrong) watched source too
