"""The management-stance evaluator (capability 27, J-53; data-contract row 25 stance half) —
pure-function unit tests of ``app.research.stance``.

Covers: the full five-verdict stance map (incl. the honest ``pending`` case that never reads intact);
the stance dwell (no per-tick flap) with ``thesis_invalidated`` dwell-exempt; the live position
readouts (distance-to-invalidation in $ and R, open R) computed via the ONE ``marks.r_basis()`` helper
with FOUR-QUADRANT sign proof (long + short × favorable + adverse last) asserting exact values; the
config-fingerprint stability of the serving-only stance dwell + its real-threshold counter-test.
"""

import pytest

from app.config import Config
from app.research.stance import StanceEvaluator, compute_position_readouts
from app.research.taxonomy import (
    STANCE_PENDING_EVIDENCE,
    management_stance_label,
    stance_for_verdict,
)


# --- the verdict -> stance map (all five published verdicts) -------------------------------------

def test_stance_for_verdict_full_five_verdict_map():
    assert stance_for_verdict("confirming") == "thesis_intact"
    assert stance_for_verdict("weakening") == "thesis_weakening"
    assert stance_for_verdict("rejecting") == "thesis_weakening"
    # The HONEST pending case (J-54): an entry while pending never reads thesis_intact.
    assert stance_for_verdict("pending") == "thesis_weakening"
    assert stance_for_verdict("invalidated") == "thesis_invalidated"
    # An unmapped verdict (e.g. expired — never reaches the stance) is the conservative NOT-intact read.
    assert stance_for_verdict("expired") == "thesis_weakening"
    assert stance_for_verdict("nonsense") == "thesis_weakening"


def test_management_stance_labels():
    assert management_stance_label("thesis_intact") == "Thesis intact"
    assert management_stance_label("thesis_weakening") == "Thesis weakening"
    assert management_stance_label("thesis_invalidated") == "Thesis invalidated"
    assert management_stance_label("unknown") == "unknown"  # fallback, never fabricated


# --- the stance dwell -----------------------------------------------------------------------------

def test_entry_while_pending_never_reads_intact_and_names_the_verdict():
    # A fresh evaluator starts at the NOT-confirmed (pending) reading with the honest pending evidence.
    ev = StanceEvaluator(dwell_seconds=3.0)
    assert ev.published_stance == "thesis_weakening"
    assert ev.published_evidence == STANCE_PENDING_EVIDENCE
    # A pending verdict over time keeps it NOT intact (no published confirmation backs it).
    for t in (0.0, 1.0, 2.0, 5.0, 10.0):
        ev.advance(verdict="pending", verdict_evidence="", logical_ts=t)
    assert ev.published_stance == "thesis_weakening"
    assert ev.published_evidence == STANCE_PENDING_EVIDENCE


def test_confirming_publishes_intact_only_after_its_dwell_no_per_tick_flap():
    ev = StanceEvaluator(dwell_seconds=3.0)
    # The raw confirming stance must HOLD continuously for the dwell before thesis_intact publishes.
    ev.advance(verdict="confirming", verdict_evidence="ev0", logical_ts=10.0)  # dwell clock starts
    assert ev.published_stance == "thesis_weakening"  # not yet — a single tick never flaps
    ev.advance(verdict="confirming", verdict_evidence="ev1", logical_ts=11.0)
    assert ev.published_stance == "thesis_weakening"  # 1.0s < 3.0s dwell
    ev.advance(verdict="confirming", verdict_evidence="ev2", logical_ts=12.9)
    assert ev.published_stance == "thesis_weakening"  # 2.9s < 3.0s dwell
    ev.advance(verdict="confirming", verdict_evidence="ev3", logical_ts=13.0)
    assert ev.published_stance == "thesis_intact"  # 3.0s >= dwell — publishes
    # The evidence is the published verdict's OWN evidence verbatim (no naked stance).
    assert ev.published_evidence == "ev3"


def test_a_lone_flicker_does_not_publish_the_stance():
    ev = StanceEvaluator(dwell_seconds=3.0)
    ev.advance(verdict="confirming", verdict_evidence="c", logical_ts=10.0)
    # A single confirming tick, then back to pending well before the dwell — the stance never flips.
    ev.advance(verdict="pending", verdict_evidence="", logical_ts=10.4)
    assert ev.published_stance == "thesis_weakening"


def test_confirmed_then_weakening_publishes_after_dwell():
    ev = StanceEvaluator(dwell_seconds=3.0)
    # First confirm.
    for t in (10.0, 13.0):
        ev.advance(verdict="confirming", verdict_evidence="conf", logical_ts=t)
    assert ev.published_stance == "thesis_intact"
    # Then weakening must hold the dwell before the stance flips to thesis_weakening.
    ev.advance(verdict="weakening", verdict_evidence="wk0", logical_ts=20.0)  # clock restarts
    assert ev.published_stance == "thesis_intact"  # not yet
    ev.advance(verdict="weakening", verdict_evidence="wk1", logical_ts=23.0)
    assert ev.published_stance == "thesis_weakening"
    assert ev.published_evidence == "wk1"  # the weakening verdict's own evidence verbatim


def test_invalidated_is_dwell_exempt_and_terminal():
    ev = StanceEvaluator(dwell_seconds=3.0)
    for t in (10.0, 13.0):
        ev.advance(verdict="confirming", verdict_evidence="conf", logical_ts=t)
    assert ev.published_stance == "thesis_intact"
    # A single invalidated verdict publishes IMMEDIATELY (no dwell) and freezes terminal.
    ev.advance(
        verdict="invalidated",
        verdict_evidence="invalidation level traded",
        logical_ts=13.1,
        invalidation_evidence="A print ran through your invalidation — the thesis is invalidated.",
    )
    assert ev.published_stance == "thesis_invalidated"
    assert "invalidation" in ev.published_evidence.lower()
    # Terminal: no later verdict ever moves it off thesis_invalidated.
    ev.advance(verdict="confirming", verdict_evidence="conf", logical_ts=99.0)
    assert ev.published_stance == "thesis_invalidated"


# --- the live position readouts (FOUR-QUADRANT sign proof, exact values) -------------------------
# R basis comes from the ONE marks.r_basis() helper (row 27, fifth registered consumer): a thesis with
# entry 100 and invalidation 98 (long) / 102 (short) gives R = 2.0 throughout. The readouts are signed
# so a POSITIVE distance = the safe side of the invalidation, and open_r is signed in the thesis's favor.

def test_long_favorable_last_positive_open_r_and_distance():
    # long: entry 100, invalidation 98 (R=2). last 101 (FAVORABLE — up): open +0.5R, distance from
    # invalidation = 101 - 98 = +3.0 ($), +1.5R (safe side).
    r = compute_position_readouts(entry_price=100.0, invalidation_price=98.0, direction="long", last=101.0)
    assert r["r_basis"] == pytest.approx(2.0)
    assert r["open_r"] == pytest.approx(0.5)
    assert r["distance_to_invalidation"]["dollars"] == pytest.approx(3.0)
    assert r["distance_to_invalidation"]["r"] == pytest.approx(1.5)


def test_long_adverse_last_negative_open_r_shrinking_distance():
    # long: entry 100, invalidation 98 (R=2). last 99 (ADVERSE — down toward the stop): open -0.5R,
    # distance from invalidation = 99 - 98 = +1.0 ($) = +0.5R (still safe side, but shrinking).
    r = compute_position_readouts(entry_price=100.0, invalidation_price=98.0, direction="long", last=99.0)
    assert r["open_r"] == pytest.approx(-0.5)
    assert r["distance_to_invalidation"]["dollars"] == pytest.approx(1.0)
    assert r["distance_to_invalidation"]["r"] == pytest.approx(0.5)


def test_short_favorable_last_positive_open_r_and_distance():
    # short: entry 100, invalidation 102 (R=2). last 99 (FAVORABLE — down): open +0.5R, distance from
    # invalidation = 102 - 99 = +3.0 ($), +1.5R (safe side, price below the stop).
    r = compute_position_readouts(entry_price=100.0, invalidation_price=102.0, direction="short", last=99.0)
    assert r["r_basis"] == pytest.approx(2.0)
    assert r["open_r"] == pytest.approx(0.5)
    assert r["distance_to_invalidation"]["dollars"] == pytest.approx(3.0)
    assert r["distance_to_invalidation"]["r"] == pytest.approx(1.5)


def test_short_adverse_last_negative_open_r_shrinking_distance():
    # short: entry 100, invalidation 102 (R=2). last 101 (ADVERSE — up toward the stop): open -0.5R,
    # distance from invalidation = 102 - 101 = +1.0 ($) = +0.5R.
    r = compute_position_readouts(entry_price=100.0, invalidation_price=102.0, direction="short", last=101.0)
    assert r["open_r"] == pytest.approx(-0.5)
    assert r["distance_to_invalidation"]["dollars"] == pytest.approx(1.0)
    assert r["distance_to_invalidation"]["r"] == pytest.approx(0.5)


def test_price_through_invalidation_gives_negative_distance():
    # long: entry 100, invalidation 98. last 97 (PAST the stop): distance goes NEGATIVE (wrong side).
    r = compute_position_readouts(entry_price=100.0, invalidation_price=98.0, direction="long", last=97.0)
    assert r["distance_to_invalidation"]["dollars"] == pytest.approx(-1.0)
    assert r["distance_to_invalidation"]["r"] == pytest.approx(-0.5)
    assert r["open_r"] == pytest.approx(-1.5)  # (97 - 100) / 2


def test_no_last_yet_gives_none_readouts_but_keeps_r_basis():
    r = compute_position_readouts(entry_price=100.0, invalidation_price=98.0, direction="long", last=None)
    assert r["r_basis"] == pytest.approx(2.0)
    assert r["open_r"] is None
    assert r["distance_to_invalidation"]["dollars"] is None
    assert r["distance_to_invalidation"]["r"] is None


def test_degenerate_zero_r_basis_gives_none_r_units_but_keeps_dollar_distance():
    # entry exactly at invalidation => R == 0: the R-unit figures are None (never inf/NaN), while the
    # dollar distance still reads honestly.
    r = compute_position_readouts(entry_price=100.0, invalidation_price=100.0, direction="long", last=101.0)
    assert r["r_basis"] is None
    assert r["open_r"] is None
    assert r["distance_to_invalidation"]["r"] is None
    assert r["distance_to_invalidation"]["dollars"] == pytest.approx(1.0)


# --- config fingerprint: the serving-only stance dwell is excluded + the counter-test ------------

def test_stance_dwell_is_serving_only_excluded_from_fingerprint():
    # The stance is NEVER persisted (schema v7), so its dwell is serving-only — changing it must NOT
    # fragment analytics pools (iter-12/iter-16 precedent).
    base = Config().config_fingerprint()
    assert base == Config(management_stance_dwell_seconds=9.0).config_fingerprint()


def test_a_real_threshold_still_changes_fingerprint():
    # The paired counter-test: a genuine classifier threshold STILL moves the fingerprint, so the
    # exclusion above is a deliberate scope decision, not a blanket hole.
    base = Config().config_fingerprint()
    assert base != Config(min_buy_price_impact=0.99).config_fingerprint()
