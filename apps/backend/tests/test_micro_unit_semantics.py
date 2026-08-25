"""Measurement-semantics guards for the Rapid Microscope (spec revision r13).

These are the tests that would have caught the r13 defect immediately: the primary outcome was
an absolute mid-price DIFFERENCE (dollars) that was renamed ``effect_bps`` on the way into an
economic-relevance gate whose floor is genuinely expressed in basis points, so the gate compared
dollars against basis points; and a parallel percent-against-basis-points comparison sat dormant
in the walk-forward and sealed-evaluation survivor rules.

The invariant every test here defends: **anything named or interpreted as ``*_bps`` is actually
basis points**, at every stage of the pipeline, and a price-scale change must not move a
scientific conclusion.

The second family of guards covers the two side vocabularies -- aggressor side (``buy``/``sell``)
and candidate direction (``long``/``short``) -- which previously collided at
``micro_features._signed``, where a ``"short"`` candidate silently failed to sign-flip because
the helper only recognized ``"sell"``.
"""

from __future__ import annotations

import pytest

from app.research import micro_features as mf
from app.research import micro_sealed_evaluation as mse
from app.research import scout
from app.research import walkforward as wf


# === helpers ======================================================================================

_SESSION_END = 10_000.0


def _mid(start: float | None, horizon: float | None, *, direction: str | None = None) -> dict:
    return mf.mid_outcome(
        mid_at_start=start, mid_at_horizon=horizon, outcome_start=0.0, horizon_ts=30.0,
        session_end_ts=_SESSION_END, direction=direction,
    )


def _bps_floor(floor_bps: float) -> dict:
    return {
        "multiple": 1.0,
        "family_median_spread_bps": floor_bps,
        "floor_bps": floor_bps,
        "unit": mf.BPS_UNIT,
        "proxy_sentence": scout.ECON_PROXY_SENTENCE,
    }


# === 1. price-scale invariance ====================================================================


def test_price_scale_invariance_same_bps_from_different_price_levels():
    """$10.00 -> $10.05 and $100.00 -> $100.50 are BOTH +50 bps. Under the pre-r13 dollar
    semantics they read 0.05 and 0.50 -- a tenfold difference for the identical move."""
    cheap = _mid(10.00, 10.05)
    dear = _mid(100.00, 100.50)

    assert cheap["return_bps"] == pytest.approx(50.0)
    assert dear["return_bps"] == pytest.approx(50.0)
    assert cheap["return_bps"] == pytest.approx(dear["return_bps"])

    # The raw dollar move is retained as a DIAGNOSTIC and is genuinely different for the two.
    assert cheap["delta_price"] == pytest.approx(0.05)
    assert dear["delta_price"] == pytest.approx(0.50)
    assert cheap["delta_price"] != pytest.approx(dear["delta_price"])


def test_unequal_raw_dollar_moves_are_not_treated_as_equal():
    """$10.00 -> $10.05 is +50 bps; $100.00 -> $100.05 is +5 bps. The pre-r13 semantics called
    both 0.05 and would have gated them identically."""
    small_price = _mid(10.00, 10.05)
    large_price = _mid(100.00, 100.05)

    assert small_price["return_bps"] == pytest.approx(50.0)
    assert large_price["return_bps"] == pytest.approx(5.0)
    assert small_price["return_bps"] != pytest.approx(large_price["return_bps"])

    # ... while their raw dollar deltas are identical -- the exact collision that hid the bug.
    assert small_price["delta_price"] == pytest.approx(large_price["delta_price"])


@pytest.mark.parametrize("factor", [0.1, 2.0, 7.5, 1000.0])
def test_split_like_rescaling_leaves_the_bps_outcome_unchanged(factor: float):
    """Multiplying BOTH prices by the same positive factor (a split, a currency redenomination,
    a different listing) must not move the scientific outcome by even a rounding step."""
    base = _mid(250.00, 251.25)
    scaled = _mid(250.00 * factor, 251.25 * factor)
    assert scaled["return_bps"] == pytest.approx(base["return_bps"])


def test_outcome_row_declares_its_own_unit():
    """The row names its unit, so no downstream reader has to infer it from a variable name --
    the failure mode that produced r13."""
    assert _mid(100.0, 100.5)["unit"] == mf.OUTCOME_UNIT
    assert mf.OUTCOME_UNIT == "return_bps"


def test_non_positive_or_missing_start_price_is_unmeasured_never_a_fabricated_return():
    for start in (None, 0.0, -1.0):
        row = _mid(start, 100.5)
        assert row["unmeasured"] is True
        assert row["return_bps"] is None
        assert row["delta_price"] is None


def test_last_trade_sensitivity_basis_uses_the_same_unit_and_stays_separately_named():
    row = mf.last_trade_outcome(
        price_at_start=10.00, price_at_horizon=10.05, outcome_start=0.0, horizon_ts=30.0,
        session_end_ts=_SESSION_END, direction=None,
    )
    assert row["basis"] == "last_trade"
    assert row["unit"] == mf.OUTCOME_UNIT
    assert row["return_bps"] == pytest.approx(50.0)


# === 2. direction semantics =======================================================================


def test_long_short_symmetry_on_the_same_price_move():
    """A +10 bps move is +10 bps for a long candidate and -10 bps for a short one."""
    up_long = _mid(100.00, 100.10, direction="long")
    up_short = _mid(100.00, 100.10, direction="short")

    assert up_long["return_bps"] == pytest.approx(10.0)
    assert up_short["return_bps"] == pytest.approx(-10.0)


def test_inverse_price_move_behaves_symmetrically():
    down_long = _mid(100.00, 99.90, direction="long")
    down_short = _mid(100.00, 99.90, direction="short")

    assert down_long["return_bps"] == pytest.approx(-9.99, abs=0.02)
    assert down_short["return_bps"] == pytest.approx(9.99, abs=0.02)
    assert down_short["return_bps"] == pytest.approx(-down_long["return_bps"])


def test_unsided_candidate_is_not_flipped():
    assert _mid(100.00, 100.10, direction=None)["return_bps"] == pytest.approx(10.0)


@pytest.mark.parametrize("bogus", ["sell", "buy", "SHORT", "Long", "flat", "", "1", "positive"])
def test_unknown_direction_vocabulary_fails_loudly_never_silently_positive(bogus: str):
    """The r13 side defect exactly: ``_signed`` flipped only on ``"sell"``, so a ``"short"``
    candidate was silently treated as long. Unknown vocabulary must raise, and it must raise even
    when the row would have been unmeasured anyway -- validation before short-circuits."""
    with pytest.raises(mf.UnknownSideVocabularyError):
        _mid(100.0, 100.5, direction=bogus)
    with pytest.raises(mf.UnknownSideVocabularyError):
        _mid(None, None, direction=bogus)  # unmeasured must NOT excuse a bad vocabulary


def test_the_two_side_vocabularies_are_explicit_and_disjoint():
    assert mf.AGGRESSOR_SIDES == ("buy", "sell")
    assert mf.CANDIDATE_DIRECTIONS == ("long", "short")
    assert not set(mf.AGGRESSOR_SIDES) & set(mf.CANDIDATE_DIRECTIONS)


def test_side_sign_helpers_validate_their_own_vocabulary():
    assert mf.aggressor_sign("buy") == 1
    assert mf.aggressor_sign("sell") == -1
    assert mf.direction_sign("long") == 1
    assert mf.direction_sign("short") == -1

    with pytest.raises(mf.UnknownSideVocabularyError):
        mf.aggressor_sign("long")          # a direction is not an aggressor side
    with pytest.raises(mf.UnknownSideVocabularyError):
        mf.direction_sign("sell")          # an aggressor side is not a direction


def test_the_adapter_between_the_vocabularies_is_explicit():
    assert mf.direction_for_aggressor("buy") == "long"
    assert mf.direction_for_aggressor("sell") == "short"
    with pytest.raises(mf.UnknownSideVocabularyError):
        mf.direction_for_aggressor("short")


# === 3. economic-floor correctness ================================================================


def test_economic_floor_compares_bps_against_bps():
    assert mf.clears_economic_floor(5.0, _bps_floor(2.0)) is True
    assert mf.clears_economic_floor(1.0, _bps_floor(2.0)) is False
    assert mf.clears_economic_floor(-5.0, _bps_floor(2.0)) is True    # magnitude, not sign
    assert mf.clears_economic_floor(2.0, _bps_floor(2.0)) is True     # >= is inclusive


def test_a_floor_that_does_not_declare_bps_is_refused_never_silently_compared():
    """Pre-r13 persisted floors carry no ``unit``. Comparing against one would silently
    reinterpret old-semantics evidence under the new convention -- refused."""
    unlabelled = {"multiple": 1.0, "family_median_spread_bps": 2.0, "floor_bps": 2.0}
    with pytest.raises(mf.UnitMismatchError):
        mf.clears_economic_floor(5.0, unlabelled)

    wrong_unit = {**unlabelled, "unit": "usd"}
    with pytest.raises(mf.UnitMismatchError):
        mf.clears_economic_floor(5.0, wrong_unit)


# === 4. propagation through every scientific stage ================================================


def _anchors(effect_bps: float) -> list[dict]:
    """Two sessions x two symbols, candidate cell offset from the comparator by exactly
    ``effect_bps`` -- a hand-built corpus whose true effect is known by construction."""
    rows: list[dict] = []
    for session in ("2026-06-01", "2026-06-02"):
        for symbol in ("AAA", "BBB"):
            for i in range(8):
                rows.append({
                    "session_date": session, "symbol": symbol, "feature_value": 1.0,
                    "outcome_bps": effect_bps + (0.01 * i), "tod_bucket": "mid", "fallback_frac": 0.1,
                })
                rows.append({
                    "session_date": session, "symbol": symbol, "feature_value": -1.0,
                    "outcome_bps": 0.0 + (0.01 * i), "tod_bucket": "mid", "fallback_frac": 0.1,
                })
    return rows


def test_scout_propagation_the_cell_effect_reaching_the_economic_gate_is_bps():
    """A corpus built with a known +5 bps candidate-cell effect must screen at +5 bps and clear a
    2 bps floor; the same corpus at +1 bps must die ``killed_economic`` against that floor."""
    clears = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness=None, horizon_key="trades_20", econ_floor=_bps_floor(2.0),
        anchors=_anchors(5.0), family_id="unit-semantics-test", n_variants_tried=1,
    )
    assert clears["screen_result"]["effect_bps"] == pytest.approx(5.0, abs=0.01)
    assert clears["screen_result"]["econ_interesting"] is True
    assert clears["decision"] != "killed_economic"

    dies = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness=None, horizon_key="trades_20", econ_floor=_bps_floor(2.0),
        anchors=_anchors(1.0), family_id="unit-semantics-test", n_variants_tried=1,
    )
    assert dies["screen_result"]["effect_bps"] == pytest.approx(1.0, abs=0.01)
    assert dies["screen_result"]["econ_interesting"] is False
    assert dies["decision"] == "killed_economic"


def test_scout_screen_result_declares_its_own_outcome_unit():
    result = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness=None, horizon_key="trades_20", econ_floor=_bps_floor(2.0),
        anchors=_anchors(5.0), family_id="unit-semantics-test", n_variants_tried=1,
    )
    assert result["screen_result"]["outcome_unit"] == mf.OUTCOME_UNIT


def _observations(value_bps: float, *, n: int = 40) -> list[dict]:
    return [
        {"session_date": f"2026-06-{(i % 10) + 1:02d}", "symbol": f"S{i % 4}", "value": value_bps}
        for i in range(n)
    ]


def test_walkforward_propagation_fold_and_pooled_effects_stay_in_bps():
    floors = {"wf_fold_min_observations": 1, "wf_fold_min_signal_sessions": 1, "wf_fold_min_symbols": 1}
    summary = wf.summarize_fold_observations(_observations(5.0), floors)

    assert summary["effect"] == pytest.approx(5.0)
    assert summary["unit"] == mf.OUTCOME_UNIT

    folds = [
        {**wf.summarize_fold_observations(_observations(5.0), floors),
         "evidence_class": wf.EVIDENCE_CLASS_HISTORICAL_OOS,
         "process_label": wf.PROCESS_LABEL_RULE, "fold_index": i}
        for i in range(3)
    ]
    verdict = wf.evaluate_survivor_rule(
        folds, sidedness="long", econ_floor=_bps_floor(2.0), voided=False
    )
    assert verdict["pooled_effect"] == pytest.approx(5.0)
    assert verdict["conditions"]["pooled_effect_clears_econ_floor"] is True

    below = wf.evaluate_survivor_rule(
        [{**f, **wf.summarize_fold_observations(_observations(1.0), floors)} for f in folds],
        sidedness="long", econ_floor=_bps_floor(2.0), voided=False,
    )
    assert below["conditions"]["pooled_effect_clears_econ_floor"] is False


def test_walkforward_observation_feed_converts_percent_to_bps():
    """The playbook feed serves ``return_pct`` in PERCENT (desk_forward.py:40). Feeding it
    unconverted into a bps floor was a dormant 100x error."""
    assert wf.PCT_TO_BPS == 100.0
    assert wf.observation_value_bps(0.25) == pytest.approx(25.0)   # 0.25% == 25 bps


def test_sealed_evaluator_propagation_uses_the_same_bps_semantics():
    floors = {"wf_fold_min_observations": 1, "wf_fold_min_signal_sessions": 1, "wf_fold_min_symbols": 1}

    clears = mse._derive_verdict(
        wf.summarize_fold_observations(_observations(5.0), floors),
        sidedness="long", econ_floor=_bps_floor(2.0),
        evidence_class=wf.EVIDENCE_CLASS_HISTORICAL_OOS, process_label=wf.PROCESS_LABEL_RULE,
    )
    assert clears[2]["clears_economic_floor"] is True

    below = mse._derive_verdict(
        wf.summarize_fold_observations(_observations(1.0), floors),
        sidedness="long", econ_floor=_bps_floor(2.0),
        evidence_class=wf.EVIDENCE_CLASS_HISTORICAL_OOS, process_label=wf.PROCESS_LABEL_RULE,
    )
    assert below[2]["clears_economic_floor"] is False
    assert below[1] == "below_economic_floor"


# === 5. the registered spec carries the unit so old and new rows can never be confused ============


def test_the_frozen_candidate_spec_records_its_outcome_unit_and_rekeys_the_candidate_id():
    """The outcome unit is part of the frozen outcome definition, so an r13 row and a pre-r13 row
    for the 'same' candidate compute DIFFERENT ``candidate_id``s -- old evidence can never be
    silently reinterpreted under the new convention."""
    spec = scout.build_candidate_spec_fields(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        structure_context_kind="none", horizon_key="trades_20", sidedness=None, fitting_rule=None,
        family_median_spread_bps=1.5, corpus_manifest=[], grid_version=1,
    )
    assert spec["outcome"]["unit"] == mf.OUTCOME_UNIT
    assert spec["econ_floor"]["unit"] == mf.BPS_UNIT

    # The six pre-r13 rows on the real ledger carry these candidate_ids; the r13 recompute must
    # NOT collide with them.
    assert spec["candidate_id"] != "cand-e5dcfa1516c3c4f5"
    assert spec["candidate_id"] != "cand-4045a40f3ef2595a"
