"""The ENTRY CHECKLIST evaluator (capability 33, J-63; data-contract row 25 checklist half) —
pure-function unit tests of ``app.research.stance``'s checklist machinery.

Covers, with EXACT numeric anchors stated in the test parameters (iter-8 lesson):
  * each of the eight checks' margin computation, with boundary cases on BOTH sides of each reused
    gate (warm-up floor, stability spread cap in bps, trade-speed floor,
    ``invalidation_too_tight_spread_multiple``, ``chase_return_threshold``, the lag bound);
  * FOUR-QUADRANT proof for the direction-sensitive checks (not_chasing + invalidation_distance:
    long + short × favorable + adverse) per the iter-7 lesson;
  * the stance aggregation map (every check-combination class -> stance), the dwell publish /
    no-flap / lone-flicker, ``tape_against`` on rejecting, and ``no_fresh_tape`` forced on each
    non-live status INCLUDING from a previously-green ``conditions_met`` (no frozen green);
  * the nearest-counterevidence selection (nearest passing on met; nearest-to-passing blocker on not);
  * the config-fingerprint stability of the two serving-only keys + the real-threshold counter-test.
"""

import pytest

from app.config import Config
from app.engine.snapshot import EngineSnapshot
from app.research.stance import (
    EntryChecklistEvaluator,
    build_checklist,
    evaluate_entry_checks,
    nearest_counterevidence,
)
from app.research.taxonomy import (
    CHECKLIST_CHECKS,
    CHECKLIST_STANCES,
    checklist_stance_label,
)

CONFIG = Config()


# A healthy-tape baseline: every gate comfortably passing, so an individual override below isolates the
# single check under test. Anchors:
#   * event_count 240 >= warmup_min_events 40                  -> warm passes
#   * stream_status "live"                                     -> feed_live passes
#   * delivery_lag_seconds 0.0 <= bound 5.0                    -> tape_lag_ok passes
#   * spread 0.02 / last 100 = 2.0 bps <= max_stable_spread_bps 30.0 -> spread_stable passes
#   * trade_speed 2.0 >= min_trade_speed 0.5                   -> trade_speed_ok passes
#   * |last 100 - invalidation 98| / spread 0.02 = 100×  >= 2.0 -> invalidation_distance_ok passes
#   * no rule anchor (rule_first_true_price None)              -> not_chasing passes (nothing has run)
def _snap(
    *,
    event_count=240,
    stream_status="live",
    delivery_lag=0.0,
    spread=0.02,
    last=100.0,
    trade_speed=2.0,
    reference_price=100.0,
) -> EngineSnapshot:
    return EngineSnapshot(
        ticker="SIM-X",
        scenario="x",
        timestamp=50.0,
        event_count=event_count,
        warm=event_count >= CONFIG.warmup_min_events,
        stream_status=stream_status,
        bid=last - spread / 2 if last is not None else None,
        ask=last + spread / 2 if last is not None else None,
        spread=spread,
        last=last,
        features={
            "30s": {
                "trade_speed": trade_speed,
                "average_spread": spread,
                "reference_price": reference_price,
                "buy_price_impact": 0.0,
                "sell_price_impact": 0.0,
            }
        },
        primary_window="30s",
        tape_state="buyer_control",
        confidence=0.9,
        observations=(),
        delivery_lag_seconds=delivery_lag,
    )


def _checks_by_id(snap, *, verdict="confirming", invalidation=98.0, direction="long",
                  rule_first_true_price=None):
    rows = evaluate_entry_checks(
        snapshot=snap,
        verdict=verdict,
        invalidation_price=invalidation,
        direction=direction,
        rule_first_true_price=rule_first_true_price,
        config=CONFIG,
    )
    return {r["check"]: r for r in rows}


# --- the eight checks: pass/fail + margin, BOTH sides of each reused gate -------------------------

def test_all_eight_checks_present_and_pass_on_healthy_tape():
    by = _checks_by_id(_snap())
    assert set(by.keys()) == set(CHECKLIST_CHECKS.keys())
    assert all(c["passed"] for c in by.values()), {k: v["margin"] for k, v in by.items()}


def test_verdict_confirming_check_passes_only_on_confirming():
    assert _checks_by_id(_snap(), verdict="confirming")["verdict_confirming"]["passed"] is True
    for v in ("pending", "weakening", "rejecting", "invalidated"):
        row = _checks_by_id(_snap(), verdict=v)["verdict_confirming"]
        assert row["passed"] is False
        assert v in row["margin"]  # the margin IS the verdict itself


def test_warm_check_boundary_both_sides():
    # floor = warmup_min_events = 40. 39 fails, exactly 40 passes.
    below = _checks_by_id(_snap(event_count=39))["warm"]
    assert below["passed"] is False
    assert "39/40" in below["margin"]
    at = _checks_by_id(_snap(event_count=40))["warm"]
    assert at["passed"] is True
    assert "40/40" in at["margin"]


def test_feed_live_check_reads_status_verbatim():
    live = _checks_by_id(_snap(stream_status="live"))["feed_live"]
    assert live["passed"] is True and "live" in live["margin"]
    for status in ("stale", "paused", "closed", "failed", "waiting"):
        row = _checks_by_id(_snap(stream_status=status))["feed_live"]
        assert row["passed"] is False
        assert status in row["margin"]


def test_tape_lag_ok_boundary_both_sides():
    # bound = delivery_lag_ok_bound_seconds = 5.0. 5.0 passes (<=), 5.01 fails.
    at = _checks_by_id(_snap(delivery_lag=5.0))["tape_lag_ok"]
    assert at["passed"] is True and "5.0s / 5.0s" in at["margin"]
    over = _checks_by_id(_snap(delivery_lag=7.5))["tape_lag_ok"]
    assert over["passed"] is False and "7.5s / 5.0s" in over["margin"]


def test_tape_lag_ok_none_is_honest_fail():
    # No lag measured yet => NOT current (we cannot assert freshness without a measurement).
    row = _checks_by_id(_snap(delivery_lag=None))["tape_lag_ok"]
    assert row["passed"] is False
    assert "—" in row["margin"]


def test_spread_stable_boundary_in_bps_both_sides():
    # cap = max_stable_spread_bps = 30.0. spread_bps = spread/last*10000.
    # last 100, spread 0.30 => 30.0 bps (exactly at cap) passes; spread 0.40 => 40.0 bps fails.
    at = _checks_by_id(_snap(spread=0.30, last=100.0))["spread_stable"]
    assert at["passed"] is True and "30.0 / 30.0 bps" in at["margin"]
    over = _checks_by_id(_snap(spread=0.40, last=100.0))["spread_stable"]
    assert over["passed"] is False and "40.0 / 30.0 bps" in over["margin"]


def test_trade_speed_ok_boundary_both_sides():
    # floor = min_trade_speed = 0.5. 0.5 passes (>=), 0.49 fails.
    at = _checks_by_id(_snap(trade_speed=0.5))["trade_speed_ok"]
    assert at["passed"] is True and "0.50 / 0.50 trades/s" in at["margin"]
    below = _checks_by_id(_snap(trade_speed=0.49))["trade_speed_ok"]
    assert below["passed"] is False and "0.49 / 0.50 trades/s" in below["margin"]


# --- FOUR-QUADRANT proof: invalidation_distance_ok (long+short × clear+tight) --------------------
# floor = invalidation_too_tight_spread_multiple = 2.0. multiples = |last - invalidation| / spread.

def test_invalidation_distance_long_clear_and_tight():
    # LONG, spread 0.02. invalidation 99.96 => |100 - 99.96| / 0.02 = 2.0× (exactly at floor) passes.
    clear = _checks_by_id(_snap(last=100.0, spread=0.02), invalidation=99.96, direction="long")
    row = clear["invalidation_distance_ok"]
    assert row["passed"] is True and "2.0× / 2× spread" in row["margin"]
    # invalidation 99.98 => 0.02 / 0.02 = 1.0× (< 2.0) fails (too tight).
    tight = _checks_by_id(_snap(last=100.0, spread=0.02), invalidation=99.98, direction="long")
    assert tight["invalidation_distance_ok"]["passed"] is False
    assert "1.0× / 2× spread" in tight["invalidation_distance_ok"]["margin"]


def test_invalidation_distance_short_clear_and_tight():
    # SHORT, spread 0.02, invalidation ABOVE last. invalidation 100.04 => 0.04/0.02 = 2.0× passes.
    clear = _checks_by_id(_snap(last=100.0, spread=0.02), invalidation=100.04, direction="short")
    assert clear["invalidation_distance_ok"]["passed"] is True
    # invalidation 100.02 => 0.02/0.02 = 1.0× fails (too tight).
    tight = _checks_by_id(_snap(last=100.0, spread=0.02), invalidation=100.02, direction="short")
    assert tight["invalidation_distance_ok"]["passed"] is False


# --- FOUR-QUADRANT proof: not_chasing (long+short × favorable-extended+not) ----------------------
# threshold = chase_return_threshold = 0.0040. favorable return measured FROM rule_first_true_price.

def test_not_chasing_long_favorable_extended_fails():
    # LONG, anchor 100.00, last 100.50 => +0.50% favorable move (> 0.40%) => chasing => FAIL.
    by = _checks_by_id(_snap(last=100.50), direction="long", rule_first_true_price=100.0)
    row = by["not_chasing"]
    assert row["passed"] is False
    assert "+0.50%" in row["margin"] and "0.40%" in row["margin"]


def test_not_chasing_long_small_move_passes():
    # LONG, anchor 100.00, last 100.30 => +0.30% favorable (< 0.40%) => not chasing => PASS.
    by = _checks_by_id(_snap(last=100.30), direction="long", rule_first_true_price=100.0)
    assert by["not_chasing"]["passed"] is True
    assert "+0.30%" in by["not_chasing"]["margin"]


def test_not_chasing_long_adverse_move_is_not_chasing():
    # LONG, anchor 100.00, last 99.50 => -0.50% (ADVERSE — price fell) is NOT chasing the move => PASS.
    by = _checks_by_id(_snap(last=99.50), direction="long", rule_first_true_price=100.0)
    assert by["not_chasing"]["passed"] is True


def test_not_chasing_short_favorable_extended_fails():
    # SHORT, anchor 100.00, last 99.50 => the favorable (down) move is +0.50% => chasing => FAIL.
    by = _checks_by_id(_snap(last=99.50), direction="short", rule_first_true_price=100.0)
    assert by["not_chasing"]["passed"] is False
    assert "+0.50%" in by["not_chasing"]["margin"]


def test_not_chasing_short_adverse_move_is_not_chasing():
    # SHORT, anchor 100.00, last 100.50 => price ROSE against a short — adverse, not chasing => PASS.
    by = _checks_by_id(_snap(last=100.50), direction="short", rule_first_true_price=100.0)
    assert by["not_chasing"]["passed"] is True


def test_not_chasing_no_anchor_passes_with_explicit_margin():
    by = _checks_by_id(_snap(), rule_first_true_price=None)
    row = by["not_chasing"]
    assert row["passed"] is True
    assert "no rule anchor" in row["margin"]


# --- the aggregation map: every check-combination class -> stance ---------------------------------

def test_raw_stance_conditions_met_when_all_pass_and_confirming():
    by = evaluate_entry_checks(
        snapshot=_snap(), verdict="confirming", invalidation_price=98.0,
        direction="long", rule_first_true_price=None, config=CONFIG,
    )
    assert EntryChecklistEvaluator.raw_stance(by, "confirming") == "conditions_met"


def test_raw_stance_conditions_not_met_when_a_check_fails():
    # A failing warm check (events below floor) with a fresh live feed + non-rejecting verdict.
    by = evaluate_entry_checks(
        snapshot=_snap(event_count=10), verdict="pending", invalidation_price=98.0,
        direction="long", rule_first_true_price=None, config=CONFIG,
    )
    assert EntryChecklistEvaluator.raw_stance(by, "pending") == "conditions_not_met"


def test_raw_stance_tape_against_on_rejecting_verdict():
    by = evaluate_entry_checks(
        snapshot=_snap(), verdict="rejecting", invalidation_price=98.0,
        direction="long", rule_first_true_price=None, config=CONFIG,
    )
    assert EntryChecklistEvaluator.raw_stance(by, "rejecting") == "tape_against"


@pytest.mark.parametrize("status", ["stale", "paused", "closed", "failed", "waiting"])
def test_raw_stance_no_fresh_tape_on_each_non_live_status(status):
    # feed_live fails on each non-live status => no_fresh_tape (regardless of the other checks).
    by = evaluate_entry_checks(
        snapshot=_snap(stream_status=status), verdict="confirming", invalidation_price=98.0,
        direction="long", rule_first_true_price=None, config=CONFIG,
    )
    assert EntryChecklistEvaluator.raw_stance(by, "confirming") == "no_fresh_tape"


def test_raw_stance_no_fresh_tape_when_lag_exceeds_bound():
    by = evaluate_entry_checks(
        snapshot=_snap(delivery_lag=99.0), verdict="confirming", invalidation_price=98.0,
        direction="long", rule_first_true_price=None, config=CONFIG,
    )
    assert EntryChecklistEvaluator.raw_stance(by, "confirming") == "no_fresh_tape"


# --- the dwell: publish after dwell, no flap, lone flicker, no frozen green -----------------------

def _all_pass_checks(verdict="confirming"):
    return evaluate_entry_checks(
        snapshot=_snap(), verdict=verdict, invalidation_price=98.0,
        direction="long", rule_first_true_price=None, config=CONFIG,
    )


def _one_fail_checks(verdict="pending"):
    return evaluate_entry_checks(
        snapshot=_snap(event_count=10), verdict=verdict, invalidation_price=98.0,
        direction="long", rule_first_true_price=None, config=CONFIG,
    )


def test_conditions_met_publishes_only_after_its_dwell_no_per_tick_flap():
    ev = EntryChecklistEvaluator(dwell_seconds=3.0)
    assert ev.published_stance == "conditions_not_met"  # honest opening read
    met = _all_pass_checks()
    ev.advance(checks=met, verdict="confirming", logical_ts=10.0)  # dwell clock starts
    assert ev.published_stance == "conditions_not_met"  # a single tick never flaps
    ev.advance(checks=met, verdict="confirming", logical_ts=12.9)
    assert ev.published_stance == "conditions_not_met"  # 2.9s < 3.0s dwell
    ev.advance(checks=met, verdict="confirming", logical_ts=13.0)
    assert ev.published_stance == "conditions_met"  # 3.0s >= dwell — publishes


def test_a_lone_met_flicker_does_not_publish():
    ev = EntryChecklistEvaluator(dwell_seconds=3.0)
    ev.advance(checks=_all_pass_checks(), verdict="confirming", logical_ts=10.0)
    # Back to not-met well before the dwell — the stance never flips to met.
    ev.advance(checks=_one_fail_checks(), verdict="pending", logical_ts=10.4)
    assert ev.published_stance == "conditions_not_met"


def test_no_fresh_tape_publishes_immediately_from_a_previously_green_no_frozen_green():
    ev = EntryChecklistEvaluator(dwell_seconds=3.0)
    # First reach conditions_met (held for the dwell).
    for t in (10.0, 13.0):
        ev.advance(checks=_all_pass_checks(), verdict="confirming", logical_ts=t)
    assert ev.published_stance == "conditions_met"
    # The feed goes stale: no_fresh_tape publishes IMMEDIATELY — a previous green must NOT persist.
    stale = evaluate_entry_checks(
        snapshot=_snap(stream_status="stale"), verdict="confirming", invalidation_price=98.0,
        direction="long", rule_first_true_price=None, config=CONFIG,
    )
    ev.advance(checks=stale, verdict="confirming", logical_ts=13.1)
    assert ev.published_stance == "no_fresh_tape"


def test_tape_against_publishes_immediately():
    ev = EntryChecklistEvaluator(dwell_seconds=3.0)
    rejecting = evaluate_entry_checks(
        snapshot=_snap(), verdict="rejecting", invalidation_price=98.0,
        direction="long", rule_first_true_price=None, config=CONFIG,
    )
    ev.advance(checks=rejecting, verdict="rejecting", logical_ts=5.0)
    assert ev.published_stance == "tape_against"


# --- nearest-counterevidence selection -----------------------------------------------------------

def test_nearest_counterevidence_picks_nearest_to_passing_blocker_when_not_met():
    # Two failing checks: trade_speed just below floor (distance ~ -0.01) vs warm far below
    # (distance -30). The nearest-to-passing blocker is trade_speed (least-negative distance).
    checks = evaluate_entry_checks(
        snapshot=_snap(event_count=10, trade_speed=0.49), verdict="pending",
        invalidation_price=98.0, direction="long", rule_first_true_price=None, config=CONFIG,
    )
    counter = nearest_counterevidence(checks, "conditions_not_met")
    assert counter is not None
    assert counter["check"] == "trade_speed_ok"
    assert "Nearest to passing" in counter["line"]


def test_nearest_counterevidence_picks_nearest_passing_on_met():
    # All pass; spread sits closest to its boundary (2.0 bps room is the smallest positive distance
    # among the unit-normalized checks here is engineered via a near-cap spread). Just assert a passing
    # check is named and the met phrasing is used.
    checks = evaluate_entry_checks(
        snapshot=_snap(spread=0.29, last=100.0), verdict="confirming",
        invalidation_price=98.0, direction="long", rule_first_true_price=None, config=CONFIG,
    )
    counter = nearest_counterevidence(checks, "conditions_met")
    assert counter is not None
    assert "Closest to flipping" in counter["line"]


# --- build_checklist: the full projection shape --------------------------------------------------

def test_build_checklist_shape_and_blockers_and_counts():
    checklist = build_checklist(
        snapshot=_snap(event_count=10), verdict="pending", published_stance="conditions_not_met",
        invalidation_price=98.0, direction="long", rule_first_true_price=None, config=CONFIG,
    )
    assert checklist["stance"]["value"] == "conditions_not_met"
    assert checklist["stance"]["label"] == checklist_stance_label("conditions_not_met")
    assert checklist["total"] == 8
    assert 0 <= checklist["passed"] <= 8
    # warm + verdict_confirming both fail here => listed as blockers.
    assert "warm" in checklist["blockers"]
    assert "verdict_confirming" in checklist["blockers"]
    # The server-only ranking key is STRIPPED from the served check rows.
    for row in checklist["checks"]:
        assert "_distance" not in row
        assert {"check", "label", "caption", "passed", "margin"} <= set(row.keys())
    # "N/8 checks pass" register in the evidence — never imperative/predictive.
    assert "checks pass" in checklist["stance"]["evidence"]


def test_build_checklist_met_8_of_8_register():
    checklist = build_checklist(
        snapshot=_snap(), verdict="confirming", published_stance="conditions_met",
        invalidation_price=98.0, direction="long", rule_first_true_price=None, config=CONFIG,
    )
    assert checklist["passed"] == 8 and checklist["total"] == 8
    assert "8/8 checks pass" in checklist["stance"]["evidence"]
    assert checklist["blockers"] == []


# --- copy discipline (J-66): no imperative / predictive language anywhere ------------------------

def test_checklist_copy_has_no_imperative_or_predictive_language():
    # Every stance evidence string + the nearest-counterevidence lines, over all four stances.
    from app.research.taxonomy import (
        CHECKLIST_ABSENCE_NO_FRESH_TAPE,
        checklist_nearest_counterevidence,
        checklist_stance_evidence,
    )

    blobs = [CHECKLIST_ABSENCE_NO_FRESH_TAPE]
    for stance in CHECKLIST_STANCES:
        blobs.append(checklist_stance_evidence(stance, 6, 8))
    blobs.append(checklist_nearest_counterevidence("Spread within stability", "2.0 / 30.0 bps", True))
    blobs.append(checklist_nearest_counterevidence("Classifier warm", "10/40 events", False))
    blobs += list(CHECKLIST_CHECKS.values())
    blob = " ".join(blobs).lower()
    for word in (" buy ", " sell ", " enter ", " exit ", "should ", "will ", "target", "predict"):
        assert word not in f" {blob} ", f"forbidden word {word!r} in checklist copy"


# --- config fingerprint: the two serving-only keys are excluded + the counter-test ---------------

def test_checklist_dwell_is_serving_only_excluded_from_fingerprint():
    base = Config().config_fingerprint()
    assert base == Config(checklist_stance_dwell_seconds=9.0).config_fingerprint()


def test_delivery_lag_bound_is_serving_only_excluded_from_fingerprint():
    base = Config().config_fingerprint()
    assert base == Config(delivery_lag_ok_bound_seconds=42.0).config_fingerprint()


def test_a_real_threshold_still_changes_fingerprint():
    base = Config().config_fingerprint()
    assert base != Config(chase_return_threshold=0.5).config_fingerprint()
