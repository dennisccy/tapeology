"""Thesis chart-geometry projection (capability 25, J-48) — the additive ``geometry`` key on the
ONE row-15 thesis projection (``build_projection``).

Geometry is a PURE projection of canonical owners:
  * price-lines    — the declared invalidation (always) + level (only when ``level_price`` is set),
                     verbatim prices, backend-owned labels;
  * markers        — one per published verdict transition from the append-only timeline (row 16),
                     the entry/exit marks (row 18), and the first-confirmation marker — never
                     recomputed, never edited, never fabricated;
  * segment rule   — only events placeable on the CURRENT watch's logical timeline (at/after the
                     latest ``watch_restarted`` gap) are drawn; price-lines are always served.

These tests assert EXACT values (prices, logical_ts, marker kinds), never just "something
returned". The engine is untouched — geometry reads the persisted rows only.
"""

import itertools

import pytest

from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.providers.simulated import SimulatedProvider
from app.research.monitor import ResearchMonitor, build_projection, data_feed_for_scenario
from app.research.store import (
    ActionRecord,
    JournalStore,
    ThesisRecord,
    VerdictEventRecord,
)
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


def _thesis(store, *, setup="level_break", direction="long",
            invalidation=99.0, level=101.0, scenario="buyer_control",
            ticker="SIM-BUYER", tid="t1") -> ThesisRecord:
    record = ThesisRecord(
        id=tid,
        ticker=ticker,
        setup_type=setup,
        direction=direction,
        invalidation_price=invalidation,
        level_price=level,
        status="active",
        bound_source=scenario,
        data_feed=data_feed_for_scenario(scenario),
        config_fingerprint=CONFIG.config_fingerprint(),
        entry_context={"tape_state": "unclear", "confidence": 0.0, "last": 100.0,
                       "spread": 0.02, "primary_window": "30s", "features": {}},
        statements=frozen_statements(setup, direction),
        created_logical_ts=0.0,
        created_wall_ts=1700000000.0,
    )
    store.insert_thesis(record)
    return record


def _proj(store, thesis, *, snapshot=None, status=None, verdict="pending",
          verdict_evidence="ev", monitor_status="ok"):
    """Call the ONE builder exactly the way the monitor does (timeline + actions from the store)."""
    return build_projection(
        thesis,
        store.get_actions(thesis.id),
        config=CONFIG,
        snapshot=snapshot,
        status=status if status is not None else thesis.status,
        verdict=verdict,
        verdict_evidence=verdict_evidence,
        monitor_status=monitor_status,
        verdict_events=store.verdict_events(thesis.id),
    )


# --- price-lines ---------------------------------------------------------------------------------

def test_level_break_serves_both_invalidation_and_level_lines_verbatim(store):
    thesis = _thesis(store, setup="level_break", invalidation=99.0, level=101.0)
    geo = _proj(store, thesis)["geometry"]
    lines = {pl["kind"]: pl for pl in geo["price_lines"]}
    assert set(lines) == {"invalidation", "level"}
    assert lines["invalidation"]["price"] == 99.0
    assert lines["level"]["price"] == 101.0
    # Backend-owned labels (frontend hardcodes none).
    assert lines["invalidation"]["label"] == "Invalidation"
    assert lines["level"]["label"] == "Level"


def test_non_level_setup_has_no_level_line(store):
    thesis = _thesis(store, setup="absorption_reversal", invalidation=99.0,
                     level=None)
    geo = _proj(store, thesis)["geometry"]
    kinds = {pl["kind"] for pl in geo["price_lines"]}
    assert kinds == {"invalidation"}
    assert geo["price_lines"][0]["price"] == 99.0


# --- verdict-transition markers (pure projection of the appended timeline) -----------------------

def _append(store, thesis, verdict, logical_ts, *, last=None, wall=1700000000.0):
    store.append_verdict_event(
        VerdictEventRecord(
            thesis_id=thesis.id, logical_ts=logical_ts, wall_ts=wall,
            verdict=verdict, evidence=f"{verdict} ev", tape_state="buyer_control",
            confidence=0.8, last=last,
        )
    )


def test_verdict_transition_markers_equal_appended_rows_exactly(store):
    thesis = _thesis(store)
    _append(store, thesis, "pending", 0.0, last=100.0)
    _append(store, thesis, "confirming", 12.0, last=101.5)
    _append(store, thesis, "weakening", 30.0, last=100.8)
    geo = _proj(store, thesis)["geometry"]
    verdicts = [m for m in geo["markers"] if m["kind"] == "verdict"]
    # One marker per published verdict transition, in timeline order, projection (not recomputation).
    assert [(m["verdict"], m["logical_ts"]) for m in verdicts] == [
        ("pending", 0.0),
        ("confirming", 12.0),
        ("weakening", 30.0),
    ]
    # Each carries the appended last verbatim and the backend-owned verdict label.
    confirming = next(m for m in verdicts if m["verdict"] == "confirming")
    assert confirming["last"] == 101.5
    assert confirming["label"] == "Confirming"


def test_first_confirmation_marker_is_first_confirming_event(store):
    thesis = _thesis(store)
    _append(store, thesis, "pending", 0.0, last=100.0)
    _append(store, thesis, "confirming", 12.0, last=101.5)
    _append(store, thesis, "weakening", 20.0, last=100.9)
    _append(store, thesis, "confirming", 28.0, last=101.9)  # a LATER confirming — not the first
    geo = _proj(store, thesis)["geometry"]
    fc = [m for m in geo["markers"] if m["kind"] == "first_confirmation"]
    assert len(fc) == 1
    assert fc[0]["logical_ts"] == 12.0  # the FIRST confirming, not the later one
    assert fc[0]["label"] == "First confirmation"


def test_no_confirmation_yields_no_first_confirmation_marker(store):
    thesis = _thesis(store)
    _append(store, thesis, "pending", 0.0, last=100.0)
    _append(store, thesis, "rejecting", 15.0, last=99.5)
    geo = _proj(store, thesis)["geometry"]
    assert [m for m in geo["markers"] if m["kind"] == "first_confirmation"] == []


# --- entry / exit mark markers (verbatim; absent when no marks) ----------------------------------

def test_entry_and_exit_marks_render_with_verbatim_price_and_logical_ts(store):
    thesis = _thesis(store)
    store.insert_action(ActionRecord(id="e1", thesis_id=thesis.id, kind="entry",
                                     price=100.25, logical_ts=8.0, wall_ts=1700000008.0,
                                     spread_at_mark=0.02))
    store.insert_action(ActionRecord(id="x1", thesis_id=thesis.id, kind="exit",
                                     price=102.10, logical_ts=40.0, wall_ts=1700000040.0,
                                     spread_at_mark=0.03))
    geo = _proj(store, thesis)["geometry"]
    entry = next(m for m in geo["markers"] if m["kind"] == "entry")
    exit_ = next(m for m in geo["markers"] if m["kind"] == "exit")
    assert (entry["price"], entry["logical_ts"], entry["label"]) == (100.25, 8.0, "Entry")
    assert (exit_["price"], exit_["logical_ts"], exit_["label"]) == (102.10, 40.0, "Exit")


def test_no_marks_yields_no_mark_markers(store):
    thesis = _thesis(store)
    _append(store, thesis, "pending", 0.0, last=100.0)
    geo = _proj(store, thesis)["geometry"]
    assert [m for m in geo["markers"] if m["kind"] in ("entry", "exit")] == []
    # Price-lines are still served (time-independent), no fabricated mark placement.
    assert {pl["kind"] for pl in geo["price_lines"]} == {"invalidation", "level"}


# --- segment rule: only CURRENT-watch events drawn (post-latest-watch_restarted) -----------------

def test_segment_rule_omits_pre_gap_markers_keeps_price_lines(store):
    thesis = _thesis(store)
    # A previous watch's timeline, then a watch_restarted gap, then the current watch's rows.
    _append(store, thesis, "pending", 0.0, last=100.0)        # pre-gap (previous watch)
    _append(store, thesis, "confirming", 10.0, last=101.0)    # pre-gap (previous watch)
    store.append_verdict_event(VerdictEventRecord(
        thesis_id=thesis.id, logical_ts=2.0, wall_ts=1700000100.0,
        verdict="watch_restarted", evidence="restart", tape_state="buyer_control",
        confidence=0.5, last=100.5,
    ))
    _append(store, thesis, "pending", 3.0, last=100.6)        # current watch
    _append(store, thesis, "confirming", 14.0, last=101.7)    # current watch
    # An entry mark recorded on the PREVIOUS watch (before the restart) is also omitted.
    store.insert_action(ActionRecord(id="e1", thesis_id=thesis.id, kind="entry",
                                     price=100.0, logical_ts=5.0, wall_ts=1700000005.0,
                                     spread_at_mark=0.02))
    geo = _proj(store, thesis)["geometry"]
    verdicts = [(m["verdict"], m["logical_ts"]) for m in geo["markers"] if m["kind"] == "verdict"]
    # Only the CURRENT-watch verdict rows (after the latest watch_restarted) are drawn.
    assert verdicts == [("pending", 3.0), ("confirming", 14.0)]
    # The pre-gap entry mark belongs to the previous watch's timeline — omitted from the chart.
    assert [m for m in geo["markers"] if m["kind"] == "entry"] == []
    # First-confirmation is resolved within the CURRENT segment (logical_ts 14.0, not 10.0).
    fc = [m for m in geo["markers"] if m["kind"] == "first_confirmation"]
    assert fc and fc[0]["logical_ts"] == 14.0
    # Price-lines are time-independent — always served regardless of the gap.
    assert {pl["kind"] for pl in geo["price_lines"]} == {"invalidation", "level"}


def test_no_gap_event_draws_all_rows(store):
    thesis = _thesis(store)
    _append(store, thesis, "pending", 0.0, last=100.0)
    _append(store, thesis, "confirming", 12.0, last=101.5)
    geo = _proj(store, thesis)["geometry"]
    verdicts = [(m["verdict"], m["logical_ts"]) for m in geo["markers"] if m["kind"] == "verdict"]
    assert verdicts == [("pending", 0.0), ("confirming", 12.0)]


# --- watch_restarted itself is a gap delimiter, NOT a verdict marker -----------------------------

def test_watch_restarted_row_is_not_drawn_as_a_verdict_marker(store):
    thesis = _thesis(store)
    store.append_verdict_event(VerdictEventRecord(
        thesis_id=thesis.id, logical_ts=0.0, wall_ts=1700000100.0,
        verdict="watch_restarted", evidence="restart", tape_state="buyer_control",
        confidence=0.5, last=100.5,
    ))
    _append(store, thesis, "pending", 1.0, last=100.6)
    geo = _proj(store, thesis)["geometry"]
    assert all(m["verdict"] != "watch_restarted" for m in geo["markers"] if m["kind"] == "verdict")
    assert [(m["verdict"], m["logical_ts"]) for m in geo["markers"] if m["kind"] == "verdict"] == [
        ("pending", 1.0)
    ]


# --- survivor (not-evaluated) projection still serves geometry from persisted rows ---------------

def test_survivor_projection_serves_geometry_without_error(store):
    thesis = _thesis(store, setup="level_break", invalidation=99.0, level=101.0)
    _append(store, thesis, "pending", 0.0, last=100.0)
    store.insert_action(ActionRecord(id="e1", thesis_id=thesis.id, kind="entry",
                                     price=100.25, logical_ts=8.0, wall_ts=1700000008.0,
                                     spread_at_mark=0.02))
    # The survivor path builds with snapshot=None and not_evaluated — geometry still computes.
    proj = build_projection(
        thesis,
        store.get_actions(thesis.id),
        config=CONFIG,
        snapshot=None,
        status="active",
        verdict="pending",
        verdict_evidence="survivor",
        monitor_status="not_evaluated",
        verdict_events=store.verdict_events(thesis.id),
    )
    geo = proj["geometry"]
    assert {pl["kind"] for pl in geo["price_lines"]} == {"invalidation", "level"}
    assert any(m["kind"] == "entry" and m["price"] == 100.25 for m in geo["markers"])


# --- live monitor projection carries geometry end-to-end (the single builder, both callers) ------

def test_monitor_projection_includes_geometry_for_active_thesis(store):
    engine = _warm_engine("SIM-BUYER", "buyer_control")
    snap = engine.snapshot()
    thesis = _thesis(store, scenario=snap.scenario, ticker=snap.ticker,
                     setup="level_break", invalidation=snap.last - 1.0,
                     level=snap.last + 1.0)
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    monitor.on_event(None, snap)
    proj = monitor.projection()
    assert "geometry" in proj
    assert {pl["kind"] for pl in proj["geometry"]["price_lines"]} == {"invalidation", "level"}
