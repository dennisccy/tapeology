"""Machine-derived execution checks (capability 27, J-54) — the SINGLE-owner pure function.

``compute_execution_checks`` maps the persisted action marks + the append-only verdict timeline +
the frozen thesis fields ONLY to the four named checks, each an enum status (``failed | passed |
not_applicable`` — labels, NEVER numeric scores) + plain-language evidence quoting the measured
values, plus the backend-owned suggested mistake tags for the failed checks.

These are PURE unit tests over hand-built ThesisRecord / ActionRecord / VerdictEventRecord fixtures
(no engine, no DB) — deterministic by construction. Each test asserts the EXACT status, the measured
values inside the evidence string, and the suggested-tag mapping.
"""

from __future__ import annotations

import dataclasses

from app.config import CONFIG
from app.research.execution_checks import compute_execution_checks
from app.research.store import ActionRecord, ThesisRecord, VerdictEventRecord


def _thesis(direction: str = "long", invalidation_price: float = 99.0) -> ThesisRecord:
    return ThesisRecord(
        id="t1",
        ticker="SIM-REVERSAL",
        setup_type="absorption_reversal",
        direction=direction,
        invalidation_price=invalidation_price,
        level_price=None,
        status="played_out",
        bound_source="bid_absorption",
        data_feed="sim",
        config_fingerprint="fp",
        entry_context={"last": 100.0},
        statements=[],
        created_logical_ts=10.0,
        created_wall_ts=1700000000.0,
    )


def _event(verdict: str, logical_ts: float, *, last: float | None = None,
           rule_first_true_price: float | None = None,
           rule_first_true_ts: float | None = None) -> VerdictEventRecord:
    return VerdictEventRecord(
        thesis_id="t1",
        logical_ts=logical_ts,
        wall_ts=1700000000.0 + logical_ts,
        verdict=verdict,
        evidence=f"{verdict} evidence",
        tape_state="buyer_control",
        confidence=0.8,
        last=last,
        rule_first_true_ts=rule_first_true_ts,
        rule_first_true_price=rule_first_true_price,
    )


def _entry(price: float, logical_ts: float) -> ActionRecord:
    return ActionRecord("a-entry", "t1", "entry", price, logical_ts, 1700000000.0 + logical_ts, 0.02)


def _exit(price: float, logical_ts: float) -> ActionRecord:
    return ActionRecord("a-exit", "t1", "exit", price, logical_ts, 1700000000.0 + logical_ts, 0.02)


def _by_name(result: dict) -> dict[str, dict]:
    return {c["check"]: c for c in result["checks"]}


# --- shape / no-marks -----------------------------------------------------------------------------

def test_no_marks_all_mark_dependent_checks_not_applicable(self_check=None):
    thesis = _thesis()
    timeline = [_event("pending", 10.0), _event("confirming", 18.0, last=100.5)]
    result = compute_execution_checks(thesis, actions=[], timeline=timeline, config=CONFIG)
    checks = _by_name(result)
    # All four checks are present and read not_applicable when there are NO marks (never a fabricated
    # pass/fail).
    for name in (
        "entered_before_confirmation",
        "chased_entry",
        "exited_beyond_invalidation",
        "cut_confirming_early",
    ):
        assert checks[name]["status"] == "not_applicable", name
        assert isinstance(checks[name]["evidence"], str) and checks[name]["evidence"]
        # No numeric SCORE anywhere — statuses are labels only.
        assert "score" not in checks[name]
    # No failed checks ⇒ no suggested tags.
    assert result["suggested_mistake_tags"] == []


# --- entered_before_confirmation ------------------------------------------------------------------

def test_entered_before_confirmation_failed_when_entry_precedes_first_confirming(self_check=None):
    thesis = _thesis()
    # entry at 14.0 precedes the FIRST confirming publish at 18.0 → failed.
    timeline = [
        _event("pending", 10.0),
        _event("confirming", 18.0, last=100.5, rule_first_true_price=100.2, rule_first_true_ts=15.0),
    ]
    actions = [_entry(100.0, 14.0)]
    result = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    check = _by_name(result)["entered_before_confirmation"]
    assert check["status"] == "failed"
    # Evidence quotes BOTH measured timestamps.
    assert "14.0" in check["evidence"]
    assert "18.0" in check["evidence"]
    # The failed check suggests the matching backend-owned tag.
    assert "entered_before_confirmation" in result["suggested_mistake_tags"]


def test_entered_before_confirmation_passed_when_entry_after_first_confirming(self_check=None):
    thesis = _thesis()
    timeline = [
        _event("pending", 10.0),
        _event("confirming", 18.0, last=100.5, rule_first_true_price=100.2, rule_first_true_ts=15.0),
    ]
    actions = [_entry(100.6, 20.0)]  # entry AFTER the first confirming publish
    result = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    check = _by_name(result)["entered_before_confirmation"]
    assert check["status"] == "passed"
    assert "entered_before_confirmation" not in result["suggested_mistake_tags"]


def test_entered_before_confirmation_failed_when_never_confirmed(self_check=None):
    # An entry-marked thesis where NO confirming was ever published while entry-marked → failed (the
    # user entered with no confirmation ever).
    thesis = _thesis()
    timeline = [_event("pending", 10.0), _event("weakening", 25.0, last=99.8)]
    actions = [_entry(100.0, 14.0)]
    result = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    check = _by_name(result)["entered_before_confirmation"]
    assert check["status"] == "failed"
    assert "no" in check["evidence"].lower() or "never" in check["evidence"].lower()
    assert "entered_before_confirmation" in result["suggested_mistake_tags"]


# --- chased_entry ---------------------------------------------------------------------------------

def test_chased_entry_failed_long_entry_beyond_rule_first_true_plus_threshold(self_check=None):
    thesis = _thesis(direction="long")
    # rule_first_true_price = 100.0; chase band (long) = 100.0 * (1 + 0.0040) = 100.4. An entry at
    # 101.0 is BEYOND the band → chased. Anchored at rule_first_true_price (NOT the publish last).
    timeline = [
        _event("pending", 10.0),
        _event("confirming", 18.0, last=102.0, rule_first_true_price=100.0, rule_first_true_ts=15.0),
    ]
    actions = [_entry(101.0, 20.0)]
    result = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    check = _by_name(result)["chased_entry"]
    assert check["status"] == "failed"
    # Evidence quotes the anchor price AND the entry price (NOT the publish last of 102.0).
    assert "100.0" in check["evidence"] or "100.00" in check["evidence"]
    assert "101.0" in check["evidence"] or "101.00" in check["evidence"]
    assert "chased" in result["suggested_mistake_tags"]


def test_chased_entry_passed_long_entry_within_band(self_check=None):
    thesis = _thesis(direction="long")
    # entry at 100.2 is INSIDE the 100.4 band → not chased.
    timeline = [
        _event("pending", 10.0),
        _event("confirming", 18.0, last=102.0, rule_first_true_price=100.0, rule_first_true_ts=15.0),
    ]
    actions = [_entry(100.2, 20.0)]
    result = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    check = _by_name(result)["chased_entry"]
    assert check["status"] == "passed"
    assert "chased" not in result["suggested_mistake_tags"]


def test_chased_entry_short_anchors_below(self_check=None):
    thesis = _thesis(direction="short", invalidation_price=101.0)
    # short chase band = 100.0 * (1 - 0.0040) = 99.6; an entry at 99.0 is BELOW it (the move already
    # ran down) → chased.
    timeline = [
        _event("pending", 10.0),
        _event("confirming", 18.0, last=98.0, rule_first_true_price=100.0, rule_first_true_ts=15.0),
    ]
    actions = [_entry(99.0, 20.0)]
    result = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    check = _by_name(result)["chased_entry"]
    assert check["status"] == "failed"
    assert "chased" in result["suggested_mistake_tags"]


def test_chased_entry_not_applicable_without_rule_first_true_anchor(self_check=None):
    # No confirming event ever carried a rule_first_true_price anchor → the chase check cannot be
    # measured; it reads not_applicable (never a fabricated pass/fail).
    thesis = _thesis(direction="long")
    timeline = [_event("pending", 10.0)]
    actions = [_entry(101.0, 20.0)]
    result = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    check = _by_name(result)["chased_entry"]
    assert check["status"] == "not_applicable"
    assert "chased" not in result["suggested_mistake_tags"]


# --- exited_beyond_invalidation -------------------------------------------------------------------

def test_exited_beyond_invalidation_failed_long_exit_below_invalidation(self_check=None):
    thesis = _thesis(direction="long", invalidation_price=99.0)
    timeline = [
        _event("pending", 10.0),
        _event("confirming", 18.0, last=100.5, rule_first_true_price=100.0, rule_first_true_ts=15.0),
    ]
    actions = [_entry(100.0, 14.0), _exit(98.5, 30.0)]  # exit BELOW the 99.0 invalidation (held through)
    result = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    check = _by_name(result)["exited_beyond_invalidation"]
    assert check["status"] == "failed"
    assert "98.5" in check["evidence"] or "98.50" in check["evidence"]
    assert "99.0" in check["evidence"] or "99.00" in check["evidence"]
    # The taxonomy maps this to ignored_rejection / held-through-stop; assert the documented tag.
    assert "ignored_rejection" in result["suggested_mistake_tags"]


def test_exited_beyond_invalidation_passed_long_exit_above_invalidation(self_check=None):
    thesis = _thesis(direction="long", invalidation_price=99.0)
    timeline = [_event("pending", 10.0), _event("confirming", 18.0, last=100.5,
                                                rule_first_true_price=100.0, rule_first_true_ts=15.0)]
    actions = [_entry(100.0, 14.0), _exit(100.8, 30.0)]  # exit comfortably above the invalidation
    result = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    check = _by_name(result)["exited_beyond_invalidation"]
    assert check["status"] == "passed"
    assert "ignored_rejection" not in result["suggested_mistake_tags"]


def test_exited_beyond_invalidation_not_applicable_without_exit(self_check=None):
    thesis = _thesis(direction="long", invalidation_price=99.0)
    timeline = [_event("pending", 10.0), _event("confirming", 18.0, last=100.5,
                                                rule_first_true_price=100.0, rule_first_true_ts=15.0)]
    actions = [_entry(100.0, 14.0)]  # NO exit
    result = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    check = _by_name(result)["exited_beyond_invalidation"]
    assert check["status"] == "not_applicable"


# --- cut_confirming_early -------------------------------------------------------------------------

def test_cut_confirming_early_failed_exit_while_latest_verdict_confirming(self_check=None):
    thesis = _thesis(direction="long")
    # latest published verdict at the exit's logical_ts is confirming → cut a confirming thesis early.
    timeline = [
        _event("pending", 10.0),
        _event("confirming", 18.0, last=100.5, rule_first_true_price=100.0, rule_first_true_ts=15.0),
    ]
    actions = [_entry(100.0, 14.0), _exit(100.6, 25.0)]  # exit while still confirming
    result = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    check = _by_name(result)["cut_confirming_early"]
    assert check["status"] == "failed"
    assert "confirming" in check["evidence"].lower()
    assert "overstayed" not in result["suggested_mistake_tags"]


def test_cut_confirming_early_passed_exit_after_weakening(self_check=None):
    thesis = _thesis(direction="long")
    timeline = [
        _event("pending", 10.0),
        _event("confirming", 18.0, last=100.5, rule_first_true_price=100.0, rule_first_true_ts=15.0),
        _event("weakening", 24.0, last=100.1),
    ]
    actions = [_entry(100.0, 14.0), _exit(100.0, 26.0)]  # exit AFTER it weakened → not "cut early"
    result = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    check = _by_name(result)["cut_confirming_early"]
    assert check["status"] == "passed"


def test_cut_confirming_early_not_applicable_without_exit(self_check=None):
    thesis = _thesis(direction="long")
    timeline = [_event("pending", 10.0), _event("confirming", 18.0, last=100.5,
                                                rule_first_true_price=100.0, rule_first_true_ts=15.0)]
    actions = [_entry(100.0, 14.0)]
    result = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    check = _by_name(result)["cut_confirming_early"]
    assert check["status"] == "not_applicable"


# --- determinism ----------------------------------------------------------------------------------

def test_compute_is_deterministic_same_inputs_same_result(self_check=None):
    thesis = _thesis()
    timeline = [_event("pending", 10.0), _event("confirming", 18.0, last=100.5,
                                                rule_first_true_price=100.0, rule_first_true_ts=15.0)]
    actions = [_entry(100.0, 14.0), _exit(100.6, 25.0)]
    r1 = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    r2 = compute_execution_checks(
        dataclasses.replace(thesis), actions=list(actions), timeline=list(timeline), config=CONFIG
    )
    assert r1 == r2


def test_suggested_tags_only_for_failed_checks(self_check=None):
    # The J-54 full-flow shape: entered before confirmation (failed) but everything else clean →
    # exactly the one suggested tag, in a stable order.
    thesis = _thesis(direction="long", invalidation_price=99.0)
    timeline = [
        _event("pending", 10.0),
        _event("confirming", 18.0, last=100.5, rule_first_true_price=100.0, rule_first_true_ts=15.0),
    ]
    actions = [_entry(100.1, 14.0), _exit(100.8, 30.0)]  # entry before confirm; clean otherwise
    result = compute_execution_checks(thesis, actions=actions, timeline=timeline, config=CONFIG)
    assert result["suggested_mistake_tags"] == ["entered_before_confirmation"]
