"""Research monitor (capability 20 observer): frozen context/statements, source binding, stamps,
statement statuses, exception isolation -> monitor_status failed (feed alive), expired-on-stop."""

import dataclasses
import itertools

import pytest

from app.config import CONFIG, Config
from app.engine.snapshot import EngineSnapshot
from app.engine.tape_engine import TapeEngine
from app.providers.simulated import SimulatedProvider
from app.research.monitor import (
    ResearchMonitor,
    _evaluate_statement,
    build_projection,
    data_feed_for_scenario,
)
from app.research.stance import StanceEvaluator
from app.research.store import ActionRecord, JournalStore, ThesisRecord, VerdictEventRecord
from app.research.taxonomy import STANCE_PENDING_EVIDENCE, frozen_statements


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
        data_feed=data_feed_for_scenario(snap.scenario, CONFIG),
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
    # Re-exported from the ONE owner (feed_basis); defaults byte-identical to the prior literals.
    assert data_feed_for_scenario("buyer_control", CONFIG) == "sim"
    assert data_feed_for_scenario("bid_absorption", CONFIG) == "sim"
    assert data_feed_for_scenario("historical AAPL 2024-05-14T09:30–2024-05-14T09:40", CONFIG) == "sip"
    assert data_feed_for_scenario("live AAPL", CONFIG) == "iex"


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


# =================================================================================================
# Management stance (capability 27, J-53; data-contract row 25 stance half) — presence rules + flow
# =================================================================================================

def _stance_thesis(store, *, direction="long", invalidation=98.0):
    """A trend_continuation thesis on SIM-SHIFT (the J-53 scenario), declared + persisted."""
    engine = _warm_engine("SIM-SHIFT", "shift_buyer_then_unclear", n=40)
    snap = engine.snapshot()
    thesis = ThesisRecord(
        id="t-stance",
        ticker="SIM-SHIFT",
        setup_type="trend_continuation",
        direction=direction,
        invalidation_price=invalidation,
        level_price=None,
        status="active",
        bound_source=snap.scenario,
        data_feed="sim",
        config_fingerprint=CONFIG.config_fingerprint(),
        entry_context={},
        statements=frozen_statements("trend_continuation", direction),
        created_logical_ts=snap.timestamp,
        created_wall_ts=1700000000.0,
    )
    store.insert_thesis(thesis)
    store.append_verdict_event(
        VerdictEventRecord(thesis.id, 0.0, 1.0, "pending", "declared", None, None, None)
    )
    return engine, thesis


def _mark_entry(store, thesis, price, spread=0.02):
    store.insert_action(
        ActionRecord(id="entry-1", thesis_id=thesis.id, kind="entry", price=price,
                     logical_ts=5.0, wall_ts=1700000005.0, spread_at_mark=spread)
    )


def test_no_stance_keys_without_an_entry_mark(store):
    # A live, confirming thesis with NO entry mark carries NO stance/readout keys — the verdict view
    # stands on its own (the strip's "no entry mark yet" absence copy is taxonomy-owned, not here).
    engine, thesis = _stance_thesis(store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    provider = SimulatedProvider("SIM-SHIFT", "shift_buyer_then_unclear")
    for ev in itertools.islice(provider.stream(), 240):
        monitor.on_event(ev, engine.process_event(ev))
        if monitor._verdict == "confirming":
            break
    assert monitor._verdict == "confirming"  # precondition: the tape confirmed
    proj = monitor.projection()
    assert "management_stance" not in proj
    assert "distance_to_invalidation" not in proj
    assert "open_r" not in proj


def test_entry_marked_confirming_publishes_thesis_intact_with_readouts(store):
    # The J-53 happy leg: an entry-marked, confirming thesis shows thesis_intact (emerald) with the
    # live distance-to-invalidation ($ and R) and open R, all from the ONE r_basis() helper.
    engine, thesis = _stance_thesis(store, invalidation=98.0)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    provider = SimulatedProvider("SIM-SHIFT", "shift_buyer_then_unclear")
    stream = provider.stream()
    # Drive to a published confirming verdict.
    for ev in itertools.islice(stream, 240):
        monitor.on_event(ev, engine.process_event(ev))
        if monitor._verdict == "confirming":
            break
    assert monitor._verdict == "confirming"
    last_at_entry = engine.snapshot().last
    _mark_entry(store, thesis, price=last_at_entry)
    # Keep feeding the confirming tape so the stance's OWN dwell (its own config-owned logical-time
    # dwell, layered on the already-published verdict) elapses and thesis_intact publishes — the stance
    # never flaps on a single tick. Stop once the stance settles or the tape stops confirming.
    for ev in itertools.islice(stream, 240):
        monitor.on_event(ev, engine.process_event(ev))
        if monitor._verdict != "confirming":
            break
        if monitor.projection().get("management_stance", {}).get("value") == "thesis_intact":
            break

    proj = monitor.projection()
    assert proj["management_stance"]["value"] == "thesis_intact"
    assert proj["management_stance"]["label"] == "Thesis intact"
    assert proj["management_stance"]["evidence"]  # no naked stance — evidence always attached
    # Live readouts present, in $ and R, via the ONE r_basis() helper (entry far above 98 => safe side).
    dist = proj["distance_to_invalidation"]
    assert dist["dollars"] is not None and dist["dollars"] > 0
    assert dist["r"] is not None and dist["r"] > 0
    assert proj["open_r"] is not None  # an open move in R (signed by direction)


def test_entry_while_pending_never_reads_intact(store):
    # The honest J-54 case: an entry marked while the verdict is still pending must NOT read
    # thesis_intact — the stance is thesis_weakening with the explicit pending evidence.
    engine, thesis = _stance_thesis(store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    snap = engine.snapshot()
    monitor.on_event(None, snap)  # one live read, still pending
    assert monitor._verdict == "pending"
    _mark_entry(store, thesis, price=snap.last)
    monitor.on_event(None, engine.snapshot())
    proj = monitor.projection()
    assert proj["management_stance"]["value"] == "thesis_weakening"
    assert proj["management_stance"]["evidence"] == STANCE_PENDING_EVIDENCE


def test_invalidation_publishes_terminal_thesis_invalidated_stance(store):
    # The J-44 auto-resolve leg: a print through the invalidation flips the stance to the terminal
    # thesis_invalidated (rose), present at/after the auto-resolve moment, dwell-exempt.
    engine, thesis = _stance_thesis(store, invalidation=98.0)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    snap = engine.snapshot()
    _mark_entry(store, thesis, price=snap.last)
    monitor.on_event(None, snap)
    # Force an invalidation by feeding a synthetic snapshot whose last is far through the invalidation.
    bad = dataclasses.replace(snap, last=90.0, timestamp=snap.timestamp + 1.0)
    monitor.on_event(None, bad)
    proj = monitor.projection()
    assert proj is not None
    assert proj["verdict"] == "invalidated"
    assert proj["management_stance"]["value"] == "thesis_invalidated"
    assert proj["management_stance"]["evidence"]  # the offending-print facts, no naked stance


def test_surviving_not_evaluated_path_carries_no_stance_keys(store):
    # A surviving entry-marked thesis served as not-evaluated (the registry survivor path / mismatched
    # source) carries NO stance/readout keys — NO frozen-stale stance. Proven via build_projection
    # with no stance supplied (exactly how the survivor + mismatched paths call it).
    _, thesis = _stance_thesis(store)
    store.insert_action(
        ActionRecord(id="e1", thesis_id=thesis.id, kind="entry", price=100.0,
                     logical_ts=5.0, wall_ts=1700000005.0, spread_at_mark=0.02)
    )
    proj = build_projection(
        thesis,
        store.get_actions(thesis.id),
        config=CONFIG,
        snapshot=None,
        status=thesis.status,
        verdict="pending",
        verdict_evidence="not evaluated",
        monitor_status="not_evaluated",
        verdict_events=store.verdict_events(thesis.id),
        # No management_stance supplied — the survivor/not-evaluated path passes none.
    )
    assert "management_stance" not in proj
    assert "distance_to_invalidation" not in proj
    assert "open_r" not in proj


def test_monitor_failed_serves_no_stance(store):
    # A failed monitor read serves NO stance (the strip shows its honest failure notice instead).
    engine, thesis = _stance_thesis(store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    snap = engine.snapshot()
    _mark_entry(store, thesis, price=snap.last)
    monitor.on_event(None, snap)
    monitor._failed = True
    proj = monitor.projection()
    assert proj["monitor_status"] == "failed"
    assert "management_stance" not in proj


def test_build_projection_stance_requires_both_stance_and_entry_mark(store):
    # build_projection serves the stance keys ONLY when a stance is supplied AND an entry mark exists.
    _, thesis = _stance_thesis(store)
    # Entry mark present, but no stance supplied => keys absent.
    store.insert_action(
        ActionRecord(id="e2", thesis_id=thesis.id, kind="entry", price=100.0,
                     logical_ts=5.0, wall_ts=1700000005.0, spread_at_mark=0.02)
    )
    proj_no_stance = build_projection(
        thesis, store.get_actions(thesis.id), config=CONFIG, snapshot=None,
        status="active", verdict="confirming", verdict_evidence="ev",
        monitor_status="ok", verdict_events=store.verdict_events(thesis.id),
    )
    assert "management_stance" not in proj_no_stance
    # Stance supplied + entry mark => keys present.
    proj_with = build_projection(
        thesis, store.get_actions(thesis.id), config=CONFIG, snapshot=None,
        status="active", verdict="confirming", verdict_evidence="ev",
        monitor_status="ok", verdict_events=store.verdict_events(thesis.id),
        management_stance="thesis_intact", management_stance_evidence="ev",
    )
    assert proj_with["management_stance"]["value"] == "thesis_intact"


# =================================================================================================
# Entry checklist (capability 33, J-63; data-contract row 25 checklist half) — presence rules + flow
# =================================================================================================
# Mutual exclusion with the management stance: a PRE-entry-mark active thesis shows the checklist and
# NO management stance; an entry-marked thesis shows the management stance and NO checklist; the
# no-thesis / not-evaluated paths show NEITHER.


def _drive_to_confirming(monitor, engine, store, thesis, *, limit=480):
    provider = SimulatedProvider("SIM-SHIFT", "shift_buyer_then_unclear")
    for ev in itertools.islice(provider.stream(), limit):
        monitor.on_event(ev, engine.process_event(ev))
        if monitor._verdict == "confirming":
            return True
    return False


def test_checklist_served_on_pre_entry_mark_path(store):
    # An active, evaluated, NOT-yet-entry-marked thesis carries the entry_checklist key with the eight
    # checks + the aggregate stance + the nearest-counterevidence line — all computed once server-side.
    engine, thesis = _stance_thesis(store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    monitor.on_event(None, engine.snapshot())  # one live read, no entry mark
    proj = monitor.projection()
    assert "entry_checklist" in proj
    checklist = proj["entry_checklist"]
    assert len(checklist["checks"]) == 8
    assert checklist["stance"]["value"] in {
        "conditions_met", "conditions_not_met", "tape_against", "no_fresh_tape"
    }
    assert checklist["stance"]["evidence"]  # no naked stance
    assert "nearest_counterevidence" in checklist
    # Pre-confirmation: the verdict_confirming check is unmet, so the stance is not conditions_met and
    # the verdict_confirming check is among the blockers.
    assert "verdict_confirming" in checklist["blockers"]
    # Mutually exclusive: no management stance on the pre-entry-mark path.
    assert "management_stance" not in proj


def test_checklist_absent_once_entry_is_marked_management_stance_present(store):
    # Once the user marks an entry, the checklist is REPLACED by the management stance (mutual
    # exclusion) — the entry_checklist key disappears and the management_stance key appears.
    engine, thesis = _stance_thesis(store, invalidation=98.0)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    assert _drive_to_confirming(monitor, engine, store, thesis)
    # Pre-mark: checklist present, stance absent.
    pre = monitor.projection()
    assert "entry_checklist" in pre and "management_stance" not in pre
    # Mark entry => the management stance takes over, the checklist is gone.
    _mark_entry(store, thesis, price=engine.snapshot().last)
    monitor.on_event(None, engine.snapshot())
    post = monitor.projection()
    assert "management_stance" in post
    assert "entry_checklist" not in post


def test_no_checklist_without_a_thesis(store):
    # No thesis => projection is None (no checklist keys served at all).
    monitor = ResearchMonitor(store, CONFIG)
    assert monitor.projection() is None


def test_no_checklist_on_not_evaluated_survivor_path(store):
    # A surviving entry-marked thesis served as not-evaluated carries NEITHER the checklist NOR the
    # management stance (no live tape, no frozen-stale cue). Proven via build_projection with neither
    # supplied (exactly how the survivor / mismatched paths call it).
    _, thesis = _stance_thesis(store)
    store.insert_action(
        ActionRecord(id="e3", thesis_id=thesis.id, kind="entry", price=100.0,
                     logical_ts=5.0, wall_ts=1700000005.0, spread_at_mark=0.02)
    )
    proj = build_projection(
        thesis, store.get_actions(thesis.id), config=CONFIG, snapshot=None,
        status=thesis.status, verdict="pending", verdict_evidence="not evaluated",
        monitor_status="not_evaluated", verdict_events=store.verdict_events(thesis.id),
    )
    assert "entry_checklist" not in proj
    assert "management_stance" not in proj


def test_monitor_failed_serves_no_checklist(store):
    # A failed monitor read serves NO checklist (the strip shows its honest failure notice instead).
    engine, thesis = _stance_thesis(store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    monitor.on_event(None, engine.snapshot())
    assert "entry_checklist" in monitor.projection()  # precondition: served while ok
    monitor._failed = True
    proj = monitor.projection()
    assert proj["monitor_status"] == "failed"
    assert "entry_checklist" not in proj


def test_checklist_no_fresh_tape_when_feed_not_live(store):
    # The honest degradation: a non-live snapshot forces the aggregate stance to no_fresh_tape (a
    # previous green must never persist over non-live data).
    engine, thesis = _stance_thesis(store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    snap = engine.snapshot()
    stale = dataclasses.replace(snap, stream_status="stale", timestamp=snap.timestamp + 1.0)
    monitor.on_event(None, stale)
    checklist = monitor.projection()["entry_checklist"]
    assert checklist["stance"]["value"] == "no_fresh_tape"
    assert checklist["checks"]  # checks still rendered (with their margins), stance honestly degraded


# =================================================================================================
# Freshness WIRING across a status flip (iter-22 / J-64): on_status advances the checklist + serves
# the CURRENT canonical status/lag, so a status flip carrying NO event still degrades immediately.
# =================================================================================================


def _force_conditions_met(monitor, engine, store, thesis):
    """Drive the live monitor (through the real engine observer) until the checklist publishes
    ``conditions_met`` — the GREEN substrate a pause/stale flip must degrade. Returns once green.

    Stamps a healthy ``delivery_lag_seconds`` per event (the feeder owns this in production; a raw
    engine never sets it, leaving ``tape_lag_ok`` failing forever), so the green is actually reachable
    — exactly the ``tape_lag_ok`` reads the feeder serves the live integration test."""
    provider = SimulatedProvider("SIM-BUYER", "buyer_control")
    engine.add_observer(monitor)
    for ev in itertools.islice(provider.stream(), 1200):
        engine.process_event(ev)  # the observer (monitor) is fed via add_observer
        engine.set_delivery_lag(0.0)  # feeder-owned freshness stamp (healthy live tape)
        cl = monitor.projection()["entry_checklist"]
        if cl["stance"]["value"] == "conditions_met":
            return True
    return False


def _buyer_thesis(store, *, invalidation=98.0):
    """A trend_continuation/long thesis on SIM-BUYER (the proven conditions_met substrate)."""
    engine = _warm_engine("SIM-BUYER", "buyer_control", n=40)
    snap = engine.snapshot()
    thesis = ThesisRecord(
        id="t-fresh",
        ticker="SIM-BUYER",
        setup_type="trend_continuation",
        direction="long",
        invalidation_price=invalidation,
        level_price=None,
        status="active",
        bound_source=snap.scenario,
        data_feed="sim",
        config_fingerprint=CONFIG.config_fingerprint(),
        entry_context={},
        statements=frozen_statements("trend_continuation", "long"),
        created_logical_ts=snap.timestamp,
        created_wall_ts=1700000000.0,
    )
    store.insert_thesis(thesis)
    store.append_verdict_event(
        VerdictEventRecord(thesis.id, 0.0, 1.0, "pending", "declared", None, None, None)
    )
    return engine, thesis


def test_on_status_pause_degrades_checklist_immediately_no_frozen_green(store):
    # The core iter-22 wiring fix at the monitor level: a previously-green conditions_met must flip to
    # no_fresh_tape the instant the engine status goes "paused" — a flip that carries NO event. Before
    # the fix the projection kept serving the green from the last-event snapshot.
    engine, thesis = _buyer_thesis(store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.attach_engine(engine)
    monitor.set_thesis(thesis)
    assert _force_conditions_met(monitor, engine, store, thesis), "never reached conditions_met"

    engine.pause()  # fires on_status("paused"); the engine snapshot already reads stream_status=paused

    cl = monitor.projection()["entry_checklist"]
    assert cl["stance"]["value"] == "no_fresh_tape"
    feed_live = next(c for c in cl["checks"] if c["check"] == "feed_live")
    assert feed_live["passed"] is False
    assert "paused" in feed_live["margin"]  # serves the CURRENT status, not the stale last-event one


def test_on_status_stale_degrades_checklist_immediately(store):
    engine, thesis = _buyer_thesis(store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.attach_engine(engine)
    monitor.set_thesis(thesis)
    assert _force_conditions_met(monitor, engine, store, thesis)

    engine.set_stream_status("stale")  # the live-feeder watchdog seam — fires on_status("stale")

    cl = monitor.projection()["entry_checklist"]
    assert cl["stance"]["value"] == "no_fresh_tape"
    assert "stale" in next(c for c in cl["checks"] if c["check"] == "feed_live")["margin"]


def test_on_status_resume_restores_honest_live_evaluation(store):
    engine, thesis = _buyer_thesis(store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.attach_engine(engine)
    monitor.set_thesis(thesis)
    assert _force_conditions_met(monitor, engine, store, thesis)

    engine.pause()
    assert monitor.projection()["entry_checklist"]["stance"]["value"] == "no_fresh_tape"

    engine.resume()  # restores the pre-pause "live" status, fires on_status("live")
    # The per-check rows immediately reflect the restored live status (feed_live passes again); the
    # AGGREGATE stance is dwell-gated, so a re-green arrives only after the dwell elapses on fresh
    # post-resume events (never an instant restoration of the pre-pause green). Drive a few events.
    cl = monitor.projection()["entry_checklist"]
    assert next(c for c in cl["checks"] if c["check"] == "feed_live")["passed"] is True
    provider = SimulatedProvider("SIM-BUYER", "buyer_control")
    cleared = False
    for ev in itertools.islice(provider.stream(), 1200):
        engine.process_event(ev)
        engine.set_delivery_lag(0.0)
        if monitor.projection()["entry_checklist"]["stance"]["value"] != "no_fresh_tape":
            cleared = True
            break
    assert cleared, "no_fresh_tape never cleared after resume on fresh evidence"


def test_on_status_failure_surfaces_monitor_failed_not_dead_feed(store):
    # on_status stays exception-isolated: a failure inside the new wiring surfaces monitor_status
    # failed (the projection says so) and never propagates to kill the feeder.
    engine, thesis = _buyer_thesis(store)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.attach_engine(engine)
    monitor.set_thesis(thesis)
    engine.add_observer(monitor)  # so engine.pause() reaches the monitor's on_status hook
    monitor.on_event(None, engine.snapshot())

    # Poison the checklist advancement so the new on_status refresh path raises internally.
    class _Boom:
        def advance(self, **kwargs):  # noqa: D401 - test stub
            raise RuntimeError("boom")

        @property
        def published_stance(self):
            return "conditions_not_met"

    monitor._checklist = _Boom()
    engine.pause()  # the on_status refresh hits the poisoned evaluator — must be isolated

    proj = monitor.projection()
    assert proj["monitor_status"] == "failed"
