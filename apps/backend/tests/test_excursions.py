"""Excursion calculator (capability 30, J-58) — the PURE tracker + persist-seam unit matrix.

Covers the iteration spec's unit list for the SINGLE-owner ``app/research/excursions.py``:
  * determinism — the identical seeded scenario + arming sequence yields a byte-identical record;
  * first-touch ordering — a synthetic path crossing -1R then +1R inside one horizon resolves
    ``-1R_first`` (and the mirror crossing +1R first resolves ``+1R_first``);
  * truncation — stream end (``truncate_open``) marks an open horizon ``truncated``; nothing
    extrapolated, nothing bridged;
  * segregation — the confirmation- and entry-anchored populations hold INDEPENDENT anchors / R bases
    and are never merged in the persisted record;
  * honest absence — never-armed populations are simply absent; the ``not_tracked`` marker is explicit;
  * R-basis reuse — the calculator's R basis equals ``marks.r_basis`` (one shared formula);
  * degenerate basis — a reference exactly at the invalidation yields no measurable move (no
    divide-by-zero, no fabricated infinity).

The tracker is pure (no I/O); these tests feed it synthetic snapshots directly, exactly as the
research-monitor observer would on the hot path.
"""

import dataclasses

from app.config import CONFIG
from app.engine.snapshot import EngineSnapshot
from app.research import excursions
from app.research.excursions import (
    CONFIRMATION,
    ENTRY,
    TERNARY_MINUS,
    TERNARY_NEITHER,
    TERNARY_PLUS,
    ExcursionTracker,
    not_tracked_record,
)
from app.research.marks import r_basis


# --- helpers -------------------------------------------------------------------------------------

def _snap(ts: float, last: float, *, spread: float | None = 0.02) -> EngineSnapshot:
    """A minimal snapshot carrying only what the tracker reads (logical ts, last, spread)."""
    return EngineSnapshot(
        ticker="SIM-BUYER",
        scenario="buyer_control",
        timestamp=ts,
        event_count=1,
        warm=True,
        stream_status="live",
        bid=last - (spread or 0.0) / 2 if last is not None else None,
        ask=last + (spread or 0.0) / 2 if last is not None else None,
        spread=spread,
        last=last,
        features={"30s": {}},
        primary_window="30s",
        tape_state="buyer_control",
        confidence=0.85,
        observations=(),
    )


def _horizon(record: dict, population: str, horizon: float) -> dict:
    pop = record["populations"][population]
    return next(h for h in pop["horizons"] if h["horizon"] == horizon)


# --- first-touch ordering ------------------------------------------------------------------------

def test_first_touch_minus_before_plus_inside_one_horizon():
    # A LONG thesis, reference 100.00, invalidation 99.00 => R = 1.00. Inside the 30s horizon the
    # price dips to 99.00 (-1R) BEFORE rising to 101.00 (+1R). First touch is -1R => -1R_first.
    tracker = ExcursionTracker(invalidation_price=99.0, direction="long", config=CONFIG)
    tracker.arm_confirmation(_snap(0.0, 100.0), reference_price=100.0)
    tracker.on_event(_snap(5.0, 99.0))    # -1R touched first (move = -1.0R)
    tracker.on_event(_snap(10.0, 101.0))  # +1R later (would be +1.0R) — but -1R already won
    # Elapse past the 30s horizon so it is fully resolved (not truncated).
    tracker.on_event(_snap(31.0, 101.0))
    record = tracker.to_record()
    h30 = _horizon(record, CONFIRMATION, 30.0)
    assert h30["outcome"] == TERNARY_MINUS
    assert h30["truncated"] is False
    # MAE reached -1.0R; MFE reached at least +1.0R afterwards (running extremes both captured).
    assert h30["mae_r"] == -1.0
    assert h30["mfe_r"] == 1.0


def test_first_touch_plus_before_minus_resolves_plus():
    # Mirror: +1R touched before -1R => +1R_first.
    tracker = ExcursionTracker(invalidation_price=99.0, direction="long", config=CONFIG)
    tracker.arm_confirmation(_snap(0.0, 100.0), reference_price=100.0)
    tracker.on_event(_snap(5.0, 101.0))   # +1R first
    tracker.on_event(_snap(10.0, 99.0))   # -1R later — but +1R already won
    tracker.on_event(_snap(31.0, 99.0))
    h30 = _horizon(tracker.to_record(), CONFIRMATION, 30.0)
    assert h30["outcome"] == TERNARY_PLUS
    assert h30["mfe_r"] == 1.0


def test_short_direction_favorable_is_downward():
    # A SHORT thesis: favorable = price DOWN. Reference 100, invalidation 101 => R = 1.0. A drop to
    # 99.0 is +1.0R favorable for a short.
    tracker = ExcursionTracker(invalidation_price=101.0, direction="short", config=CONFIG)
    tracker.arm_entry(logical_ts=0.0, wall_ts=1.7e9, reference_price=100.0, spread_at_mark=0.02)
    tracker.on_event(_snap(5.0, 99.0))    # +1R favorable for a short
    tracker.on_event(_snap(31.0, 99.0))
    h30 = _horizon(tracker.to_record(), ENTRY, 30.0)
    assert h30["outcome"] == TERNARY_PLUS
    assert h30["mfe_r"] == 1.0


# --- neither within horizon ----------------------------------------------------------------------

def test_neither_within_horizon_when_no_target_touched_before_elapse():
    # Reference 100, invalidation 99 => R = 1.0. Price drifts to 100.50 (+0.5R) and the horizon
    # elapses without touching +1R or -1R => neither_within_horizon, MFE 0.5R, not truncated.
    tracker = ExcursionTracker(invalidation_price=99.0, direction="long", config=CONFIG)
    tracker.arm_confirmation(_snap(0.0, 100.0), reference_price=100.0)
    tracker.on_event(_snap(5.0, 100.5))
    tracker.on_event(_snap(11.0, 100.5))  # past the 10s horizon
    h10 = _horizon(tracker.to_record(), CONFIRMATION, 10.0)
    assert h10["outcome"] == TERNARY_NEITHER
    assert h10["truncated"] is False
    assert h10["mfe_r"] == 0.5
    assert h10["mae_r"] == 0.0


# --- truncation ----------------------------------------------------------------------------------

def test_truncate_open_marks_open_horizons_truncated_without_extrapolation():
    # Reference 100, invalidation 99 => R = 1.0. Price reaches +0.4R then the STREAM ENDS at dt=8s,
    # before any horizon elapses. truncate_open() flags every open horizon truncated; the partial
    # MFE/MAE so far are KEPT (never extrapolated, never bridged), outcome stays None.
    tracker = ExcursionTracker(invalidation_price=99.0, direction="long", config=CONFIG)
    tracker.arm_confirmation(_snap(0.0, 100.0), reference_price=100.0)
    tracker.on_event(_snap(8.0, 100.4))
    tracker.truncate_open()
    record = tracker.to_record()
    for h in (10.0, 30.0, 60.0, 120.0):
        row = _horizon(record, CONFIRMATION, h)
        assert row["truncated"] is True, h
        assert row["outcome"] is None, h
        assert row["mfe_r"] == 0.4, h  # partial excursion kept, never extrapolated


def test_done_horizon_not_truncated_after_stream_end():
    # A horizon resolved by first touch BEFORE the stream end is NOT re-flagged truncated; only still-
    # open horizons truncate.
    tracker = ExcursionTracker(invalidation_price=99.0, direction="long", config=CONFIG)
    tracker.arm_confirmation(_snap(0.0, 100.0), reference_price=100.0)
    tracker.on_event(_snap(3.0, 101.0))   # +1R within the 10s horizon => resolved +1R_first
    tracker.truncate_open()               # stream ends
    record = tracker.to_record()
    h10 = _horizon(record, CONFIRMATION, 10.0)
    assert h10["outcome"] == TERNARY_PLUS
    assert h10["truncated"] is False
    # The longer horizons were still open at +1R touch time, so they ALSO resolved +1R_first by first
    # touch (the touch happened within them too) — not truncated.
    h120 = _horizon(record, CONFIRMATION, 120.0)
    assert h120["outcome"] == TERNARY_PLUS
    assert h120["truncated"] is False


def test_completed_short_horizon_and_truncated_long_horizon_coexist():
    # The J-58 shape in miniature: a +1R touch at dt=12s resolves the 30s/60s/120s horizons +1R_first,
    # but the 10s horizon ELAPSED at neither (touch was after 10s) and then the stream ends at dt=40s
    # — so 60s/120s would still be open were they not already resolved. Build a case where one horizon
    # COMPLETES and one is TRUNCATED: target touched at dt=40s resolves 60s/120s, 10s/30s elapsed at
    # neither (completed), and we cut the stream BEFORE 120s with the 120s still resolved by touch.
    tracker = ExcursionTracker(invalidation_price=99.0, direction="long", config=CONFIG)
    tracker.arm_confirmation(_snap(0.0, 100.0), reference_price=100.0)
    tracker.on_event(_snap(11.0, 100.5))  # 10s horizon elapses at +0.5R => neither (completed)
    tracker.on_event(_snap(40.0, 101.0))  # +1R touched at dt=40s: 60s/120s resolve +1R_first;
                                          #   30s already elapsed at neither before this
    tracker.truncate_open()               # stream ends at dt=40s
    record = tracker.to_record()
    assert _horizon(record, CONFIRMATION, 10.0)["outcome"] == TERNARY_NEITHER
    assert _horizon(record, CONFIRMATION, 10.0)["truncated"] is False
    assert _horizon(record, CONFIRMATION, 30.0)["outcome"] == TERNARY_NEITHER
    assert _horizon(record, CONFIRMATION, 60.0)["outcome"] == TERNARY_PLUS
    assert _horizon(record, CONFIRMATION, 120.0)["outcome"] == TERNARY_PLUS
    # None should be truncated here (all resolved by first touch or full elapse before/at the end).
    assert all(not _horizon(record, CONFIRMATION, h)["truncated"] for h in (10, 30, 60, 120))


# --- segregation ---------------------------------------------------------------------------------

def test_two_populations_segregated_independent_anchors_and_r_bases():
    # Confirmation anchored at last=100.21, entry anchored at price=100.30. Independent anchors,
    # independent R bases (invalidation 100.00 => R_conf=0.21, R_entry=0.30). The persisted record
    # holds them under separate keys; nothing is pooled.
    tracker = ExcursionTracker(invalidation_price=100.0, direction="long", config=CONFIG)
    tracker.arm_confirmation(_snap(5.0, 100.21, spread=0.02), reference_price=100.21)
    tracker.arm_entry(logical_ts=8.0, wall_ts=1.7e9, reference_price=100.30, spread_at_mark=0.03)
    tracker.on_event(_snap(40.0, 100.60))
    record = tracker.to_record()
    conf = record["populations"][CONFIRMATION]
    entry = record["populations"][ENTRY]
    assert conf["reference_price"] == 100.21
    assert entry["reference_price"] == 100.30
    assert abs(conf["r_basis"] - 0.21) < 1e-9
    assert abs(entry["r_basis"] - 0.30) < 1e-9
    # Spread-at-anchor is segregated and a moment value (confirmation from the snapshot, entry reused
    # from the mark's stamped spread).
    assert conf["spread_at_anchor"] == 0.02
    assert entry["spread_at_anchor"] == 0.03
    # Independent anchors.
    assert conf["anchor_logical_ts"] == 5.0
    assert entry["anchor_logical_ts"] == 8.0


def test_confirmation_arms_only_once_no_re_arm_after_weakening():
    # Re-confirmation after weakening must NEVER re-arm — the FIRST confirmation owns the population.
    tracker = ExcursionTracker(invalidation_price=99.0, direction="long", config=CONFIG)
    tracker.arm_confirmation(_snap(5.0, 100.0), reference_price=100.0)
    tracker.arm_confirmation(_snap(50.0, 102.0), reference_price=102.0)  # ignored
    conf = tracker.to_record()["populations"][CONFIRMATION]
    assert conf["anchor_logical_ts"] == 5.0
    assert conf["reference_price"] == 100.0


# --- honest absence --------------------------------------------------------------------------------

def test_never_armed_has_no_populations():
    tracker = ExcursionTracker(invalidation_price=99.0, direction="long", config=CONFIG)
    tracker.on_event(_snap(5.0, 100.0))
    record = tracker.to_record()
    assert record["tracked"] is True
    assert record["populations"] == {}


def test_entry_only_has_no_confirmation_population():
    tracker = ExcursionTracker(invalidation_price=99.0, direction="long", config=CONFIG)
    tracker.arm_entry(logical_ts=8.0, wall_ts=1.7e9, reference_price=100.0, spread_at_mark=0.02)
    tracker.on_event(_snap(40.0, 100.5))
    record = tracker.to_record()
    assert CONFIRMATION not in record["populations"]
    assert ENTRY in record["populations"]


def test_not_tracked_record_is_explicit():
    rec = not_tracked_record()
    assert rec == {"tracked": False, "populations": {}}


# --- R-basis reuse + degenerate basis ------------------------------------------------------------

def test_r_basis_matches_shared_marks_helper():
    # The calculator's R basis MUST equal marks.r_basis (one shared formula, never a second one).
    tracker = ExcursionTracker(invalidation_price=98.0, direction="long", config=CONFIG)
    tracker.arm_confirmation(_snap(0.0, 100.5), reference_price=100.5)
    conf = tracker.to_record()["populations"][CONFIRMATION]
    assert conf["r_basis"] == r_basis(100.5, 98.0)


def test_degenerate_zero_r_basis_yields_no_measurable_move():
    # Reference exactly at the invalidation => R = 0. No divide-by-zero, no fabricated infinity: every
    # horizon resolves neither_within_horizon with zero MFE/MAE.
    tracker = ExcursionTracker(invalidation_price=100.0, direction="long", config=CONFIG)
    tracker.arm_confirmation(_snap(0.0, 100.0), reference_price=100.0)
    tracker.on_event(_snap(5.0, 105.0))   # a big price move — but R is 0, so no measurable R move
    tracker.on_event(_snap(200.0, 105.0))  # elapse all horizons
    record = tracker.to_record()
    for h in (10.0, 30.0, 60.0, 120.0):
        row = _horizon(record, CONFIRMATION, h)
        assert row["mfe_r"] == 0.0
        assert row["mae_r"] == 0.0
        assert row["outcome"] == TERNARY_NEITHER


# --- determinism ---------------------------------------------------------------------------------

def test_identical_arming_and_path_yields_byte_identical_record():
    def run() -> dict:
        tracker = ExcursionTracker(invalidation_price=99.0, direction="long", config=CONFIG)
        tracker.arm_confirmation(_snap(0.0, 100.0), reference_price=100.0)
        tracker.arm_entry(logical_ts=2.0, wall_ts=1.7e9, reference_price=100.05, spread_at_mark=0.02)
        for ts, last in [(5.0, 100.2), (12.0, 100.5), (40.0, 101.1), (130.0, 101.8)]:
            tracker.on_event(_snap(ts, last))
        return tracker.to_record()

    import json
    a = json.dumps(run(), sort_keys=True)
    b = json.dumps(run(), sort_keys=True)
    assert a == b


# --- J-58 calibration against the REAL seeded SIM-BUYER stream -----------------------------------

def _run_sim_buyer_confirmation_excursions(stop_after_events: int) -> dict:
    """Replay the seeded SIM-BUYER stream through a fresh engine + verdict evaluator + excursion
    tracker (exactly the monitor's hot path), arming the confirmation population at the first
    published ``confirming`` event, cutting the stream after ``stop_after_events`` and truncating —
    then return the persisted record. The J-58 substrate: trend_continuation / long, invalidation
    below price at 98.00 (the EXACT J-42 value), which gives R ≈ 2.21 at confirmation."""
    import itertools
    from app.engine.tape_engine import TapeEngine
    from app.providers.simulated import SimulatedProvider
    from app.research.store import ThesisRecord
    from app.research.taxonomy import frozen_statements
    from app.research.verdict import VerdictEvaluator

    thesis = ThesisRecord(
        id="t", ticker="SIM-BUYER", setup_type="trend_continuation", direction="long",
        invalidation_price=98.0, level_price=None, status="active", bound_source="buyer_control",
        data_feed="sim", config_fingerprint=CONFIG.config_fingerprint(), entry_context={},
        statements=frozen_statements("trend_continuation", "long"),
        created_logical_ts=0.0, created_wall_ts=1.7e9,
    )
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    evaluator = VerdictEvaluator(thesis, CONFIG)
    tracker = ExcursionTracker(invalidation_price=98.0, direction="long", config=CONFIG)
    for event in itertools.islice(SimulatedProvider("SIM-BUYER", "buyer_control").stream(), stop_after_events):
        snap = engine.process_event(event)
        decision = evaluator.evaluate(snap)
        if decision.changed and decision.verdict == "confirming":
            # Arm the confirmation population at the FIRST published confirming, reference = the
            # ``last`` recorded on that published event (the spec basis).
            tracker.arm_confirmation(snap, reference_price=decision.last)
        tracker.on_event(snap)
    tracker.truncate_open()  # stream end => truncate any open horizon
    return tracker.to_record()


def test_j58_sim_buyer_exercises_both_a_completed_and_a_truncated_horizon():
    # The config calibration the iter spec demands: the deterministic J-58 SIM-BUYER run exercises
    # BOTH at least one COMPLETED horizon and at least one STREAM-END-TRUNCATED horizon. Confirmation
    # lands ~22.5s logical in with R ≈ 2.21 (a far 98.00 invalidation); SIM-BUYER grinds up slowly so
    # +1R (a $2.21 move) is NOT reached within any short horizon. Cut the stream at 400 events
    # (~logical end 99.5s, dt 77s past confirmation): the 10/30/60s horizons fully ELAPSE at
    # ``neither_within_horizon`` (completed), the 120s horizon is still OPEN at the cut => truncated.
    record = _run_sim_buyer_confirmation_excursions(stop_after_events=400)
    conf = record["populations"][CONFIRMATION]
    by_h = {h["horizon"]: h for h in conf["horizons"]}
    # At least one completed (a resolved ternary, not truncated) AND at least one truncated.
    completed = [h for h in conf["horizons"] if not h["truncated"] and h["outcome"] is not None]
    truncated = [h for h in conf["horizons"] if h["truncated"]]
    assert completed, "expected at least one completed horizon"
    assert truncated, "expected at least one stream-end-truncated horizon"
    # Specifically: 10/30/60s complete at neither_within_horizon; 120s is truncated at the stream end.
    assert by_h[10.0]["outcome"] == TERNARY_NEITHER
    assert by_h[30.0]["outcome"] == TERNARY_NEITHER
    assert by_h[60.0]["outcome"] == TERNARY_NEITHER
    assert by_h[10.0]["truncated"] is False
    assert by_h[120.0]["truncated"] is True
    assert by_h[120.0]["outcome"] is None
    # R basis is the far invalidation (~2.21) via the shared helper; the partial favorable excursion
    # is honestly recorded (MFE > 0, well under +1R).
    assert 2.0 < conf["r_basis"] < 2.5
    assert 0.0 < by_h[120.0]["mfe_r"] < 1.0


def test_j58_sim_buyer_run_is_deterministic_byte_identical():
    # J-58's explicit determinism clause: the identical seeded scenario + arming sequence yields a
    # byte-identical persisted record.
    import json
    a = json.dumps(_run_sim_buyer_confirmation_excursions(400), sort_keys=True)
    b = json.dumps(_run_sim_buyer_confirmation_excursions(400), sort_keys=True)
    assert a == b
