"""Outcome × process grade computation (capability 29, J-56) — the pure single-owner functions.

Asserts the EXACT enum labels (never a numeric score) for:
  * outcome 1:1 from each of the four resolutions (played_out/invalidated/expired/abandoned);
  * the config-owned process rule over the named checks (clean / flagged / violated);
  * the CRITICAL invariant: an invalidated thesis with no failed execution check and no fired risk
    flag grades ``clean`` — being invalidated is never by itself a process failure.
"""

import dataclasses

from app.config import CONFIG
from app.research.grades import compute_grades
from app.research.store import ThesisRecord


def _thesis(**overrides) -> ThesisRecord:
    base = ThesisRecord(
        id="t1",
        ticker="SIM-BUYER",
        setup_type="trend_continuation",
        direction="long",
        invalidation_price=98.0,
        level_price=None,
        status="played_out",
        bound_source="buyer_control",
        data_feed="sim",
        config_fingerprint="abc",
        entry_context={"last": 100.0},
        statements=[{"text": "x", "kind": "tape_state_is", "params": {"states": ["buyer_control"]}}],
        created_logical_ts=12.5,
        created_wall_ts=1700000000.0,
        risk_flags=[],
        execution_checks={"checks": [], "suggested_mistake_tags": []},
    )
    return dataclasses.replace(base, **overrides)


def _checks(*statuses: str) -> dict:
    return {
        "checks": [
            {"check": f"check_{i}", "status": s, "evidence": "e"} for i, s in enumerate(statuses)
        ],
        "suggested_mistake_tags": [],
    }


# --- outcome is 1:1 from the resolution ----------------------------------------------------------

def test_outcome_played_out_is_thesis_held():
    g = compute_grades(_thesis(status="played_out"), "played_out", config=CONFIG)
    assert g["outcome"] == "thesis_held"


def test_outcome_invalidated_is_thesis_failed():
    g = compute_grades(_thesis(status="invalidated"), "invalidated", config=CONFIG)
    assert g["outcome"] == "thesis_failed"


def test_outcome_expired_is_no_read():
    g = compute_grades(_thesis(status="expired"), "expired", config=CONFIG)
    assert g["outcome"] == "no_read"


def test_outcome_abandoned_is_no_read():
    g = compute_grades(_thesis(status="abandoned"), "abandoned", config=CONFIG)
    assert g["outcome"] == "no_read"


# --- process rule over the named checks ----------------------------------------------------------

def test_process_clean_no_flags_no_failed_checks():
    g = compute_grades(
        _thesis(risk_flags=[], execution_checks=_checks("passed", "not_applicable")),
        "played_out",
        config=CONFIG,
    )
    assert g["process"] == "clean"
    assert "clean" in g["process_evidence"].lower()


def test_process_flagged_when_a_risk_flag_fired_but_no_failed_check():
    flags = [{"flag": "chasing_entry", "label": "Chasing", "evidence": "e", "measured": {}}]
    g = compute_grades(
        _thesis(risk_flags=flags, execution_checks=_checks("passed")),
        "played_out",
        config=CONFIG,
    )
    assert g["process"] == "flagged"
    # Evidence NAMES the fired flag (no naked grade).
    assert "chasing entry" in g["process_evidence"].lower()


def test_process_violated_when_an_execution_check_failed():
    flags = [{"flag": "chasing_entry", "label": "Chasing", "evidence": "e", "measured": {}}]
    g = compute_grades(
        _thesis(risk_flags=flags, execution_checks=_checks("failed", "passed")),
        "played_out",
        config=CONFIG,
    )
    # A failed execution check VIOLATES (worst named finding wins) even with a flag also present.
    assert g["process"] == "violated"
    # Evidence NAMES the failed check (humanized — underscores -> spaces) so the grade is auditable.
    assert "check 0" in g["process_evidence"]


# --- the CRITICAL invariant: invalidation is never itself a process failure ----------------------

def test_invalidated_clean_checks_no_flags_grades_clean_process():
    # An invalidated, no-flag, clean-checks thesis grades thesis_failed × CLEAN — being invalidated is
    # never by itself a process failure (the system enforces invalidation).
    g = compute_grades(
        _thesis(status="invalidated", risk_flags=[], execution_checks=_checks("passed", "not_applicable")),
        "invalidated",
        config=CONFIG,
    )
    assert g["outcome"] == "thesis_failed"
    assert g["process"] == "clean"


def test_grade_values_are_enum_labels_never_numeric():
    g = compute_grades(_thesis(), "played_out", config=CONFIG)
    assert g["outcome"] in {"thesis_held", "thesis_failed", "no_read"}
    assert g["process"] in {"clean", "flagged", "violated"}
    assert isinstance(g["process_evidence"], str) and g["process_evidence"]
