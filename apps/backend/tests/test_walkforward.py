"""``walkforward.py`` + ``walkforward_ledger.py`` (Era "The Rapid Microscope" J-05) -- the

chronological walk-forward engine. Test-first contract: TC-6 through TC-19, TC-23 through TC-26 in
``docs/phases/goal-rapid-microscope-iter-5.md`` (TC-21/TC-22, the TR-16 end-to-end oracles, live in
``test_walkforward_oracles.py`` -- see that file's own module docstring). TC-1/TC-2/TC-3 live in
``test_micro_accessor.py``; TC-4/TC-5 in ``test_micro_join.py``/``test_scout.py``."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.research import walkforward as wf
from app.research import walkforward_ledger as wl
from app.research.micro_accessor import ExposureRegistry, initialize_r2_exposure_registry
from app.research.micro_routes import (
    get_micro_exposure_registry_dir,
    get_walkforward_compute_manager,
    get_walkforward_ledger_dir,
)
from app.research.desk_routes import get_playbook_store, get_universe_store
from app.research.routes import get_bar_store


# === helpers ==========================================================================================

_ECON_FLOOR = {"floor_bps": 5.0}


def _observation(session_date: str, symbol: str, value: float) -> dict:
    return {"session_date": session_date, "symbol": symbol, "value": value}


def _sufficient_fold_row(
    *, fold_index: int, sequence_id: str = "seq-x", corpus_id: str = "corpus-x",
    evidence_class: str = wf.EVIDENCE_CLASS_HISTORICAL_OOS, process_label: str = wf.PROCESS_LABEL_RULE,
    effect: float = 10.0, sign: str = "positive", n: int = 40, n_sessions: int = 10, n_symbols: int = 3,
) -> dict:
    """A hand-built, already-SUFFICIENT fold_result-shaped dict -- the direct
    ``evaluate_survivor_rule``/``sequence_verdict`` unit-testing style (never routed through the
    ledger for these pure-function tests)."""
    return {
        "fold_index": fold_index, "sequence_id": sequence_id, "corpus_id": corpus_id,
        "status": wf.FOLD_STATUS_SUFFICIENT, "evidence_class": evidence_class, "process_label": process_label,
        "effect": effect, "sign": sign, "n": n, "n_sessions": n_sessions, "n_symbols": n_symbols, "missing": {},
    }


def _five_sufficient_oos_rule_process_folds(**overrides) -> list[dict]:
    return [_sufficient_fold_row(fold_index=i, **overrides) for i in range(5)]


# === TC-6: fold-spec registration is frozen verbatim; clustering_unit is corpus-size-invariant ======


def test_tc6_fold_spec_fields_are_frozen_exactly_as_registered(tmp_path):
    ledger = wl.WalkForwardLedger(str(tmp_path))
    geometry = {"train_sessions": 40, "test_sessions": 20, "step_sessions": 20, "embargo_sessions": 0, "embargo_derivation": "no cross-boundary dependency identified"}
    row = wl.register_fold_spec(
        ledger, corpus_id="big-corpus", corpus_manifest_hash="abc123", geometry=geometry,
        floors={"wf_fold_min_observations": 30},
    )
    reread = wl.latest_fold_spec(ledger, "big-corpus")
    assert reread["geometry"] == geometry
    assert reread["clustering_unit"] == "session_date"
    assert reread["corpus_manifest_hash"] == "abc123"
    assert reread["geometry_hash"] == row["geometry_hash"]


def test_tc6_clustering_unit_is_session_date_regardless_of_corpus_size():
    """clustering_unit stays session_date whether the corpus is the 155-session playbook corpus
    or the 11-session tick corpus -- no corpus-size-dependent switching, ever (spec section 5.3's
    r2 rule)."""
    ledger_big = wl.WalkForwardLedger(str(__import__("tempfile").mkdtemp()))
    ledger_small = wl.WalkForwardLedger(str(__import__("tempfile").mkdtemp()))
    geometry = {"train_sessions": 5, "test_sessions": 2, "step_sessions": 2, "embargo_sessions": 0, "embargo_derivation": "n/a"}
    big = wl.register_fold_spec(ledger_big, corpus_id="big", corpus_manifest_hash="h1", geometry=geometry, floors={})
    small = wl.register_fold_spec(ledger_small, corpus_id="small", corpus_manifest_hash="h2", geometry=geometry, floors={})
    assert big["clustering_unit"] == "session_date"
    assert small["clustering_unit"] == "session_date"


# === TC-7: step < test is refused =====================================================================


def test_tc7_step_less_than_test_is_refused(tmp_path):
    ledger = wl.WalkForwardLedger(str(tmp_path))
    geometry = {"train_sessions": 40, "test_sessions": 20, "step_sessions": 10, "embargo_sessions": 0, "embargo_derivation": "n/a"}
    with pytest.raises(wl.FoldStepTooSmallError):
        wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=geometry, floors={})
    assert ledger.all_rows() == []  # refused BEFORE any row is written


# === TC-8: purge exactness is asserted, not assumed ===================================================


def test_tc8_a_label_planted_to_cross_a_fold_boundary_fails_with_a_named_error():
    fold_test_sessions = ["2026-01-05", "2026-01-06", "2026-01-07"]
    crossing = [
        _observation("2026-01-05", "AAA", 1.0),
        _observation("2026-01-08", "BBB", 2.0),  # NOT a member of fold_test_sessions -- the plant
    ]
    with pytest.raises(wf.PurgeExactnessError, match="2026-01-08"):
        wf.assert_purge_exact(crossing, fold_test_sessions, boundary_name="test_sessions")


def test_tc8_observations_in_sessions_filters_to_the_allowed_set_with_the_assertion_wired_in():
    """The production filter every fold-evaluation call site uses: an observation outside the
    allowed session set is excluded, never fabricated into the fold's own pool -- with TR-6's
    assertion (proven directly above to raise on a genuinely malformed/pre-filtered input) wired in
    as an always-on safety net over the filtered result."""
    observations = [_observation("2026-01-05", "AAA", 1.0), _observation("2099-01-01", "ZZZ", 9.0)]
    result = wf.observations_in_sessions(observations, ["2026-01-05"], boundary_name="test_sessions")
    assert result == [_observation("2026-01-05", "AAA", 1.0)]


def test_tc8_well_formed_observations_never_raise():
    observations = [_observation("2026-01-05", "AAA", 1.0), _observation("2026-01-06", "BBB", 2.0)]
    result = wf.observations_in_sessions(observations, ["2026-01-05", "2026-01-06", "2026-01-07"], boundary_name="test_sessions")
    assert len(result) == 2


# === TC-9: embargo derivation -- E=0 legitimate; the diagnostic run's own E=5 is not universal =======


def test_tc9_embargo_sessions_zero_is_accepted_with_its_derivation_recorded(tmp_path):
    ledger = wl.WalkForwardLedger(str(tmp_path))
    geometry = {
        "train_sessions": 10, "test_sessions": 5, "step_sessions": 5, "embargo_sessions": 0,
        "embargo_derivation": "session-truncated labels + prefix-only features + session-date "
        "boundaries leave no identified cross-boundary dependency",
    }
    row = wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=geometry, floors={})
    assert row["geometry"]["embargo_sessions"] == 0
    assert "no identified cross-boundary dependency" in row["geometry"]["embargo_derivation"]


def test_tc9_diagnostic_geometry_embargo_is_its_own_predeclared_choice_not_a_universal_default():
    assert wf.DIAGNOSTIC_GEOMETRY["embargo_sessions"] == 5
    derivation = wf.DIAGNOSTIC_GEOMETRY["embargo_derivation"]
    assert "predeclared choice" in derivation
    assert "universal" in derivation  # explicitly disclaims being a universal rule


# === TC-10: geometry freeze (TR-13) + voiding clears survivor states =================================


def test_tc10_a_second_different_geometry_without_a_voiding_event_is_refused(tmp_path):
    ledger = wl.WalkForwardLedger(str(tmp_path))
    first = {"train_sessions": 40, "test_sessions": 20, "step_sessions": 20, "embargo_sessions": 0, "embargo_derivation": "n/a"}
    second = {"train_sessions": 30, "test_sessions": 15, "step_sessions": 15, "embargo_sessions": 0, "embargo_derivation": "n/a"}
    wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=first, floors={})
    with pytest.raises(wl.FoldGeometryFrozenError):
        wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=second, floors={})


def test_tc10_re_registering_the_identical_geometry_is_an_idempotent_replay_not_a_refusal(tmp_path):
    ledger = wl.WalkForwardLedger(str(tmp_path))
    geometry = {"train_sessions": 40, "test_sessions": 20, "step_sessions": 20, "embargo_sessions": 0, "embargo_derivation": "n/a"}
    first = wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=geometry, floors={})
    second = wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=geometry, floors={})
    assert first == second
    assert len(ledger.rows_of_kind(wl.ROW_KIND_FOLD_SPEC)) == 1


def test_tc10_a_voiding_event_permits_a_new_geometry_and_survivor_states_read_void_afterward(tmp_path):
    ledger = wl.WalkForwardLedger(str(tmp_path))
    first = {"train_sessions": 40, "test_sessions": 20, "step_sessions": 20, "embargo_sessions": 0, "embargo_derivation": "n/a"}
    second = {"train_sessions": 30, "test_sessions": 15, "step_sessions": 15, "embargo_sessions": 0, "embargo_derivation": "n/a"}
    wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=first, floors={})
    assert wl.is_corpus_era_voided(ledger, "c") is False

    wl.record_voiding_event(ledger, corpus_id="c", reason="geometry change after fold 1")
    assert wl.is_corpus_era_voided(ledger, "c") is True

    # now a DIFFERENT geometry is accepted
    new_spec = wl.register_fold_spec(ledger, corpus_id="c", corpus_manifest_hash="h", geometry=second, floors={})
    assert new_spec["geometry"] == second

    # WF_SURVIVOR_RULE_V1's own condition 5 reads this corpus-era as voided regardless of stats
    folds = _five_sufficient_oos_rule_process_folds()
    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=True)
    assert result["verdict"] == "not_survivor"
    assert result["conditions"]["zero_voiding_events"] is False


def test_tc10_voiding_events_are_permanent_never_deleted_or_edited(tmp_path):
    ledger = wl.WalkForwardLedger(str(tmp_path))
    wl.record_voiding_event(ledger, corpus_id="c", reason="r1")
    wl.record_voiding_event(ledger, corpus_id="c", reason="r2")
    events = wl.voiding_events_for_corpus(ledger, "c")
    assert len(events) == 2
    assert [e["reason"] for e in events] == ["r1", "r2"]
    assert ledger.verify_chain()["ok"] is True


# === TC-11/TC-14: Mode A rule identity (TR-14) ========================================================


def test_tc11_same_fitting_rule_across_origins_stays_in_the_same_sequence(tmp_path):
    ledger = wl.WalkForwardLedger(str(tmp_path))
    registry = ExposureRegistry(str(tmp_path / "exposure"))
    corpus_id = "tc11-corpus"
    sessions = [f"2026-02-{d:02d}" for d in range(1, 21)]  # 20 sessions
    geometry = {"train_sessions": 8, "test_sessions": 4, "step_sessions": 4, "embargo_sessions": 0, "embargo_derivation": "n/a"}
    folds = wf.build_folds(sessions, geometry)
    assert len(folds) >= 2

    observations = [_observation(s, "AAPL", 1.0) for s in sessions]

    row0 = wf.register_mode_a_origin(
        ledger, registry, corpus_id=corpus_id, fitting_rule="training_quantile(0.90)", fold=folds[0],
        train_observations_provider=lambda: observations, test_observations_provider=lambda: observations,
        floors={}, sidedness="long", econ_floor=None,
    )
    row1 = wf.register_mode_a_origin(
        ledger, registry, corpus_id=corpus_id, fitting_rule="training_quantile(0.90)", fold=folds[1],
        train_observations_provider=lambda: observations, test_observations_provider=lambda: observations,
        floors={}, sidedness="long", econ_floor=None,
    )
    assert row0["sequence_id"] == row1["sequence_id"]

    row2 = wf.register_mode_a_origin(
        ledger, registry, corpus_id=corpus_id, fitting_rule="training_quantile(0.95)", fold=folds[0],
        train_observations_provider=lambda: observations, test_observations_provider=lambda: observations,
        floors={}, sidedness="long", econ_floor=None,
    )
    assert row2["sequence_id"] != row0["sequence_id"]


def test_tc11_unknown_fitting_rule_is_refused():
    with pytest.raises(wf.UnknownFittingRuleError):
        wf.parse_fitting_rule("not_a_real_rule(1.0)")


# === TC-12: spec-hash-then-reveal freeze order ========================================================


def test_tc12_the_validation_window_is_not_read_until_after_the_spec_hash_is_frozen(tmp_path):
    ledger = wl.WalkForwardLedger(str(tmp_path))
    registry = ExposureRegistry(str(tmp_path / "exposure"))
    sessions = ["2026-03-01", "2026-03-02", "2026-03-03", "2026-03-04"]
    geometry = {"train_sessions": 2, "test_sessions": 2, "step_sessions": 2, "embargo_sessions": 0, "embargo_derivation": "n/a"}
    folds = wf.build_folds(sessions, geometry)
    observations = [_observation(s, "AAPL", 1.0) for s in sessions]

    call_order: list[str] = []

    def _train_provider():
        call_order.append("train")
        return observations

    def _test_provider():
        call_order.append("test")
        return observations

    row = wf.register_mode_a_origin(
        ledger, registry, corpus_id="tc12", fitting_rule="training_quantile(0.5)", fold=folds[0],
        train_observations_provider=_train_provider, test_observations_provider=_test_provider,
        floors={}, sidedness="long", econ_floor=None,
    )
    assert call_order == ["train", "test"]  # train fit -> spec freeze -> ONLY THEN test reveal
    assert row["spec_hash_recorded_at"] <= row["validation_revealed_at"]
    # the frozen spec identity excludes the realized fitted value (TR-14): two origins with
    # different realized values (proven by TC-11's own same-sequence test) still share ONE rule.
    assert row["realized_fitted_value"] is not None


# === TC-13: Mode B registration-first + the mechanical exposure classing rule ========================


def test_tc13_a_mode_b_spec_registered_after_a_logged_exposure_is_auto_classed_diagnostic(tmp_path):
    ledger = wl.WalkForwardLedger(str(tmp_path))
    registry = ExposureRegistry(str(tmp_path / "exposure"))
    corpus_id = "tc13-corpus"
    registry.log_exposure(corpus_id=corpus_id, window="2026-04-05", surface="prior-serving", logged_at="2026-04-06T00:00:00.000000Z")

    spec = wf.register_mode_b_spec(
        corpus_id=corpus_id, rule_id="rule-x", sidedness="long", econ_floor=None,
        registered_at="2026-04-10T00:00:00.000000Z",  # AFTER the logged exposure entry
    )
    fold = {"fold_index": 0, "origin_index": 0, "train_sessions": [], "embargo_sessions": [], "test_sessions": ["2026-04-05"]}
    observations = [_observation("2026-04-05", "AAPL", 1.0)] * 40
    row = wf.evaluate_mode_b_fold(ledger, registry, spec=spec, fold=fold, observations=observations, floors={"wf_fold_min_observations": 1, "wf_fold_min_signal_sessions": 1, "wf_fold_min_symbols": 1})
    assert row["evidence_class"] == wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC


def test_tc13_a_mode_b_spec_registered_before_any_exposure_of_its_window_classes_historical_oos(tmp_path):
    ledger = wl.WalkForwardLedger(str(tmp_path))
    registry = ExposureRegistry(str(tmp_path / "exposure"))  # a genuinely fresh registry -- nothing pre-marked
    corpus_id = "tc13-fresh-corpus"

    spec = wf.register_mode_b_spec(
        corpus_id=corpus_id, rule_id="rule-y", sidedness="long", econ_floor=None,
        registered_at="2026-04-01T00:00:00.000000Z",
    )
    fold = {"fold_index": 0, "origin_index": 0, "train_sessions": [], "embargo_sessions": [], "test_sessions": ["2026-04-05"]}
    observations = [_observation("2026-04-05", "AAPL", 1.0)] * 40
    row = wf.evaluate_mode_b_fold(ledger, registry, spec=spec, fold=fold, observations=observations, floors={"wf_fold_min_observations": 1, "wf_fold_min_signal_sessions": 1, "wf_fold_min_symbols": 1})
    assert row["evidence_class"] == wf.EVIDENCE_CLASS_HISTORICAL_OOS


def test_tc14_freshly_initialized_registry_reads_every_named_window_exposed_before_any_serving_act(tmp_path):
    registry = ExposureRegistry(str(tmp_path / "exposure"))
    windows = [f"2026-01-{d:02d}" for d in range(1, 6)]
    initialize_r2_exposure_registry(registry, corpus_id="legacy_tick", windows=windows)
    for window in windows:
        assert registry.is_exposed_before(corpus_id="legacy_tick", window=window, instant="2026-08-17T00:00:00.000000Z")


# === TC-15: WF_SURVIVOR_RULE_V1 -- all five conditions, individually violated =========================


def test_tc15_all_five_conditions_hold_returns_walkforward_survivor():
    folds = _five_sufficient_oos_rule_process_folds(effect=10.0, sign="positive")
    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
    assert result["verdict"] == wf.WF_VERDICT_SURVIVOR
    assert result["rule_name"] == wf.WF_SURVIVOR_RULE_V1
    assert all(result["conditions"].values())


def test_tc15_violating_condition_1_class_mix_prevents_survivor():
    folds = _five_sufficient_oos_rule_process_folds(effect=10.0, sign="positive")
    folds[0]["evidence_class"] = wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
    assert result["verdict"] == "not_survivor"
    assert result["conditions"]["sufficient_oos_rule_process_folds"] is False


def test_tc15_violating_condition_2_sign_agreement_prevents_survivor():
    # 5 folds, 2 with an opposing sign -> agreement 3/5 = 0.6 < 0.7
    folds = _five_sufficient_oos_rule_process_folds(effect=10.0, sign="positive")
    folds[0]["sign"], folds[0]["effect"] = "negative", -10.0
    folds[1]["sign"], folds[1]["effect"] = "negative", -10.0
    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
    assert result["verdict"] == "not_survivor"
    assert result["conditions"]["sign_agreement"] is False
    assert result["sign_agreement"] == pytest.approx(0.6)


def test_tc15_violating_condition_3_pooled_effect_below_econ_floor_prevents_survivor():
    folds = _five_sufficient_oos_rule_process_folds(effect=1.0, sign="positive")  # below floor_bps=5.0
    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
    assert result["verdict"] == "not_survivor"
    assert result["conditions"]["pooled_effect_clears_econ_floor"] is False


def test_tc15_violating_condition_3_via_missing_econ_floor_prevents_survivor_fail_closed():
    folds = _five_sufficient_oos_rule_process_folds(effect=10.0, sign="positive")
    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=None, voided=False)
    assert result["verdict"] == "not_survivor"
    assert result["conditions"]["pooled_effect_clears_econ_floor"] is False


def test_tc15_violating_condition_4_an_opposite_direction_sufficient_fold_prevents_survivor():
    folds = _five_sufficient_oos_rule_process_folds(effect=10.0, sign="positive")
    # a 6th, strongly opposite-direction, econ-floor-clearing fold
    folds.append(_sufficient_fold_row(fold_index=5, effect=-20.0, sign="negative"))
    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
    assert result["verdict"] == "not_survivor"
    assert result["conditions"]["no_opposite_direction_sufficient_fold"] is False


def test_tc15_violating_condition_5_a_voided_corpus_era_prevents_survivor():
    folds = _five_sufficient_oos_rule_process_folds(effect=10.0, sign="positive")
    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=True)
    assert result["verdict"] == "not_survivor"
    assert result["conditions"]["zero_voiding_events"] is False


# === TC-16: below-floor folds serve insufficient with the failed arithmetic ==========================


def test_tc16_a_fold_below_min_observations_reads_insufficient_with_the_arithmetic():
    observations = [_observation(f"2026-05-{(i % 8) + 1:02d}", f"SYM{i % 3}", 1.0) for i in range(10)]  # only 10 < 30
    result = wf.summarize_fold_observations(observations, {})
    assert result["status"] == wf.FOLD_STATUS_INSUFFICIENT
    assert result["missing"]["observations"] == "10 < 30"


def test_tc16_a_fold_below_min_signal_sessions_reads_insufficient():
    observations = [_observation("2026-05-01", f"SYM{i % 3}", 1.0) for i in range(40)]  # 40 obs, 1 session
    result = wf.summarize_fold_observations(observations, {})
    assert result["status"] == wf.FOLD_STATUS_INSUFFICIENT
    assert "signal_sessions" in result["missing"]
    assert result["missing"]["signal_sessions"] == "1 < 8"


def test_tc16_a_fold_below_min_symbols_reads_insufficient():
    observations = [_observation(f"2026-05-{(i % 10) + 1:02d}", "ONLY_SYMBOL", 1.0) for i in range(40)]
    result = wf.summarize_fold_observations(observations, {})
    assert result["status"] == wf.FOLD_STATUS_INSUFFICIENT
    assert result["missing"]["symbols"] == "1 < 2"


def test_tc16_a_sufficient_fold_never_reads_insufficient():
    observations = []
    for i in range(40):
        session = f"2026-05-{(i % 10) + 1:02d}"
        symbol = f"SYM{i % 3}"
        observations.append(_observation(session, symbol, 1.0 if i % 2 == 0 else -0.5))
    result = wf.summarize_fold_observations(observations, {})
    assert result["status"] == wf.FOLD_STATUS_SUFFICIENT
    assert result["missing"] == {}
    assert result["effect"] is not None
    assert result["sign"] in ("positive", "negative", "zero")


# === TC-17: below WF_MIN_SUFFICIENT_FOLDS refuses a sequence-level verdict ===========================


def test_tc17_fewer_than_min_sufficient_folds_refuses_rather_than_computes():
    folds = _five_sufficient_oos_rule_process_folds()[:2]  # only 2, < WF_MIN_SUFFICIENT_FOLDS(3)
    result = wf.sequence_verdict(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
    assert result["refused"] is True
    assert result["reason"] == "2 < 3 sufficient folds -- a sequence-level verdict is refused (spec section 6.6), never a fabricated result"


def test_tc17_at_the_floor_a_verdict_is_computed_not_refused():
    folds = _five_sufficient_oos_rule_process_folds()[:3]  # exactly WF_MIN_SUFFICIENT_FOLDS(3)
    result = wf.sequence_verdict(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
    assert result["refused"] is False
    assert result["verdict"] == wf.WF_VERDICT_SURVIVOR
    assert result["rule_name"] == wf.WF_SURVIVOR_RULE_V1


# === TC-18: class-mixing refusal (TR-5) -- a diagnostic fold contributes NOTHING to any tally ========


def test_tc18_pooling_a_diagnostic_fold_with_an_oos_fold_is_refused_at_condition_1():
    oos_fold = _sufficient_fold_row(fold_index=0, evidence_class=wf.EVIDENCE_CLASS_HISTORICAL_OOS, effect=10.0, sign="positive")
    diagnostic_fold = _sufficient_fold_row(fold_index=1, evidence_class=wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC, effect=999.0, sign="positive")
    result = wf.evaluate_survivor_rule([oos_fold, diagnostic_fold], sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
    assert result["conditions"]["sufficient_oos_rule_process_folds"] is False


def test_tc18_the_diagnostic_fold_independently_contributes_nothing_to_the_pooled_effect():
    """A diagnostic fold with an EXTREME effect value must not move the pooled_effect number AT
    ALL -- proven by comparing the pooled_effect against the OOS-only fold's own effect exactly,
    not merely observing that the overall verdict fails."""
    oos_fold = _sufficient_fold_row(fold_index=0, evidence_class=wf.EVIDENCE_CLASS_HISTORICAL_OOS, effect=10.0, sign="positive")
    diagnostic_fold = _sufficient_fold_row(fold_index=1, evidence_class=wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC, effect=999_999.0, sign="positive")
    result = wf.evaluate_survivor_rule([oos_fold, diagnostic_fold], sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
    assert result["pooled_effect"] == pytest.approx(10.0)  # NOT influenced by the diagnostic fold's 999,999.0
    assert result["n_eligible_folds"] == 1


# === TC-19: process-label discipline (TR-21) ==========================================================


def test_tc19_a_post_reveal_operator_selection_is_refused_at_walkforward_survivor():
    folds = _five_sufficient_oos_rule_process_folds(effect=10.0, sign="positive")
    folds[0]["process_label"] = wf.PROCESS_LABEL_OPERATOR
    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
    assert result["verdict"] == "not_survivor"
    assert result["conditions"]["sufficient_oos_rule_process_folds"] is False


def test_tc19_operator_process_fold_contributes_nothing_to_the_pooled_effect_either():
    rule_fold = _sufficient_fold_row(fold_index=0, process_label=wf.PROCESS_LABEL_RULE, effect=10.0, sign="positive")
    operator_fold = _sufficient_fold_row(fold_index=1, process_label=wf.PROCESS_LABEL_OPERATOR, effect=999_999.0, sign="positive")
    result = wf.evaluate_survivor_rule([rule_fold, operator_fold], sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
    assert result["pooled_effect"] == pytest.approx(10.0)


def test_tc19_a_pre_reveal_registered_shortlist_keeps_rule_process_and_stays_eligible():
    folds = _five_sufficient_oos_rule_process_folds(effect=10.0, sign="positive", process_label=wf.PROCESS_LABEL_RULE)
    result = wf.evaluate_survivor_rule(folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
    assert result["verdict"] == wf.WF_VERDICT_SURVIVOR
    assert result["rule_name"] == wf.WF_SURVIVOR_RULE_V1


# === TC-20: the tick-family typed floor-refusal (TR-15) ==============================================


def test_tc20_the_11_session_tick_corpus_returns_the_typed_floor_refusal_naming_11_lt_105():
    sessions = [f"2026-06-{d:02d}" for d in range(1, 12)]  # 11 sessions
    assert len(sessions) == 11
    minimum = wf.minimum_sessions_for_sufficient_folds(wf.DIAGNOSTIC_GEOMETRY)
    assert minimum == 105
    with pytest.raises(wf.InsufficientSessionsForFoldsError, match=r"11 < 105"):
        wf.require_sufficient_sessions_for_folds(sessions, wf.DIAGNOSTIC_GEOMETRY)
    # build_folds itself also never fabricates a fold from a below-floor session list -- an empty
    # fold REPORT is not the refusal (the typed error above is), but it must never be non-empty.
    assert wf.build_folds(sessions, wf.DIAGNOSTIC_GEOMETRY) == []


# === TC-23/TC-24: the diagnostic acceptance run (hermetic proof over a small synthetic corpus) =======
# Real 155-session corpus proof: run via CLI (`python -m app.research.walkforward --diagnostic`),
# never a blocking pytest recomputation (the Constraints' own iteration-hygiene rail) -- see the dev
# handoff for the actual recorded numbers from a live run against the real store.


class _FakePlaybookStore:
    def __init__(self, records: list[dict]) -> None:
        self._records = records

    def list(self):
        return list(self._records), []


class _FakeUniverseStore:
    def __init__(self, members: list[str]) -> None:
        self._members = members

    def list(self):
        return [{"members": self._members}], []


class _FakeConfig:
    """A stand-in for ``app.config.Config`` -- the ONLY method ``run_diagnostic_walkforward``'s
    own (monkeypatched-away in this test) ``compute_playbook_input_signature`` call needs."""

    def config_fingerprint(self) -> str:
        return "fake-fingerprint"


def _fake_signal(setup_id: str, symbol: str, return_pct: float) -> dict:
    return {
        "setup_id": setup_id, "symbol": symbol,
        "forward": {"horizons": {"1h": {"return_pct": return_pct, "truncated": False}}},
    }


def _fake_playbook_record(session_date: str, signature: str, signals: list[dict]) -> dict:
    return {"session_date": session_date, "playbook_input_signature": signature, "signals": signals}


def test_run_diagnostic_walkforward_self_initializes_a_never_before_seen_exposure_registry(tmp_path, monkeypatch):
    """The realistic first-ever-run scenario (the route/CLI's own production path): a FRESH,
    never-initialized ``ExposureRegistry`` must still classify the diagnostic run's folds
    ``historical_exposed_diagnostic`` -- the playbook corpus's aggregates have genuinely been
    served for months, and a registry that merely HAPPENS to be new must never let that honest
    fact accidentally read as `historical_oos`."""
    signature = "sig-fresh"
    sessions = [f"2026-02-{d:03d}" for d in range(1, 156)]
    records = [
        _fake_playbook_record(s, signature, [_fake_signal("range_trade", "AAPL", 0.3), _fake_signal("range_trade", "MSFT", 0.3)])
        for s in sessions
    ]
    monkeypatch.setattr(wf, "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE", "2020-01-01")
    monkeypatch.setattr(wf, "compute_playbook_input_signature", lambda bar_store, members, config_fingerprint: signature)

    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    registry = ExposureRegistry(str(tmp_path / "exposure"))  # NEVER initialized before this call
    assert registry.all_rows() == []

    result = wf.run_diagnostic_walkforward(
        ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), bar_store=None, config=_FakeConfig(),
    )
    assert result["folds_evaluated"] == 5
    for row in result["rows"]:
        assert row["evidence_class"] == wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC

    # a SECOND trigger against the SAME durable registry does not re-append the window list
    registry_rows_after_first_run = len(registry.all_rows())
    wf.run_diagnostic_walkforward(
        ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), bar_store=None, config=_FakeConfig(),
    )
    assert len(registry.all_rows()) == registry_rows_after_first_run  # unchanged -- no re-seeding


def test_tc23_and_tc24_the_diagnostic_run_over_a_small_synthetic_corpus(tmp_path, monkeypatch):
    """A hermetic, fast stand-in for TC-23/TC-24's own real-corpus acceptance: proves the
    orchestration logic (orphan exclusion, signature pooling, geometry math, evidence-class
    labeling, zero-credit counter-test) end to end without the real 155-session corpus."""
    signature = "sig-current"
    sessions = [f"2026-01-{d:03d}" for d in range(1, 156)]  # 155 well-formed sessions
    # 2 symbols per session (WF_FOLD_MIN_SYMBOLS=2) and 2 signals per session (so a 20-session
    # fold test window carries 40 observations >= WF_FOLD_MIN_OBSERVATIONS(30), 20 signal-carrying
    # sessions >= WF_FOLD_MIN_SIGNAL_SESSIONS(8)).
    records = [
        _fake_playbook_record(
            s, signature,
            [_fake_signal("range_trade", "AAPL", 0.3 if i % 2 == 0 else -0.1), _fake_signal("range_trade", "MSFT", 0.3 if i % 2 == 0 else -0.1)],
        )
        for i, s in enumerate(sessions)
    ]
    # the orphan: a session FAR outside this contiguous run, under the SAME signature
    records.append(_fake_playbook_record("2020-01-01", signature, [_fake_signal("range_trade", "AAPL", 5.0)]))
    # a stale-signature record for a session already covered -- must be excluded from pooling
    records.append(_fake_playbook_record(sessions[0], "sig-old", [_fake_signal("range_trade", "AAPL", -99.0)]))

    monkeypatch.setattr(wf, "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE", "2020-01-01")
    monkeypatch.setattr(
        wf, "compute_playbook_input_signature", lambda bar_store, members, config_fingerprint: signature
    )

    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    registry = ExposureRegistry(str(tmp_path / "exposure"))
    initialize_r2_exposure_registry(registry, corpus_id=wf.PLAYBOOK_DIAGNOSTIC_CORPUS_ID, windows=sessions)

    result = wf.run_diagnostic_walkforward(
        ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), bar_store=None, config=_FakeConfig(),
    )

    assert result["folds_evaluated"] == 5
    assert result["validation_sessions"] == 100
    assert result["session_count"] == 155

    rows = wl.fold_results_for_sequence(ledger, result["rows"][0]["sequence_id"])
    assert len(rows) == 5
    for row in rows:
        assert row["evidence_class"] == wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC

    # TC-24: every diagnostic fold AND a synthetic operator_process sequence evaluate to
    # not-a-survivor under WF_SURVIVOR_RULE_V1, regardless of statistics.
    verdict = wf.sequence_verdict(rows, sidedness="long", econ_floor=None, voided=False)
    assert verdict["refused"] is False
    assert verdict["verdict"] == "not_survivor"

    operator_folds = _five_sufficient_oos_rule_process_folds(process_label=wf.PROCESS_LABEL_OPERATOR, effect=1_000.0, sign="positive")
    operator_verdict = wf.sequence_verdict(operator_folds, sidedness="long", econ_floor=_ECON_FLOOR, voided=False)
    assert operator_verdict["verdict"] == "not_survivor"


# === audit regression: a REPEAT operator run never double-counts a sequence's own evidence =========
# (found by the iteration-5 audit against the REAL ledger: pressing POST /walkforward/compute -- or
# re-running the CLI warmer -- a second time appended a second physical fold_result row per fold, so
# the real sequence's honest "2 < 3 sufficient folds -- refused" became a COMPUTED verdict over
# n_sufficient_folds=4 built from the SAME 2 folds counted twice.)


def test_append_fold_result_replays_an_identical_evaluation_instead_of_recording_it_twice(tmp_path):
    ledger = wl.WalkForwardLedger(str(tmp_path))
    fields = {"sequence_id": "seq-a", "corpus_id": "c", "fold_index": 0, "spec_hash": "hash-1", "status": wf.FOLD_STATUS_SUFFICIENT}

    first = wl.append_fold_result(ledger, dict(fields))
    replay = wl.append_fold_result(ledger, dict(fields))

    assert replay == first  # the SAME permanent row, not a second copy of the same evidence
    assert len(ledger.rows_of_kind(wl.ROW_KIND_FOLD_RESULT)) == 1

    # a genuinely DIFFERENT evaluation act still appends: another fold of the same sequence...
    wl.append_fold_result(ledger, {**fields, "fold_index": 1})
    # ...and the same fold re-evaluated under a DIFFERENT frozen spec.
    wl.append_fold_result(ledger, {**fields, "spec_hash": "hash-2"})
    assert len(ledger.rows_of_kind(wl.ROW_KIND_FOLD_RESULT)) == 3


def test_a_repeat_run_never_turns_a_below_floor_refusal_into_a_computed_verdict(tmp_path):
    """The exact real-corpus failure the audit reproduced: 2 sufficient folds must keep refusing a
    sequence-level verdict no matter how many times the run is repeated."""
    ledger = wl.WalkForwardLedger(str(tmp_path))
    fields = [
        {"sequence_id": "seq-real", "corpus_id": "c", "fold_index": i, "spec_hash": "h",
         "status": wf.FOLD_STATUS_SUFFICIENT, "evidence_class": wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC,
         "process_label": wf.PROCESS_LABEL_RULE, "effect": 0.01, "sign": "positive", "n": 330,
         "n_sessions": 20, "n_symbols": 94, "missing": {}, "sidedness": "long", "econ_floor": None}
        for i in (3, 4)
    ]
    for _run in range(3):  # the operator presses Compute three times
        for row in fields:
            wl.append_fold_result(ledger, dict(row))

    rows = wl.fold_results_for_sequence(ledger, "seq-real")
    assert len(rows) == 2
    verdict = wf.sequence_verdict(rows, sidedness="long", econ_floor=None, voided=False)
    assert verdict["refused"] is True
    assert verdict["n_sufficient_folds"] == 2


def test_a_repeat_diagnostic_run_replays_every_fold_and_leaves_the_served_sequence_unchanged(tmp_path, monkeypatch):
    signature = "sig-repeat"
    sessions = [f"2026-04-{d:03d}" for d in range(1, 156)]
    records = [
        _fake_playbook_record(s, signature, [_fake_signal("range_trade", "AAPL", 0.3), _fake_signal("range_trade", "MSFT", 0.3)])
        for s in sessions
    ]
    monkeypatch.setattr(wf, "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE", "2020-01-01")
    monkeypatch.setattr(wf, "compute_playbook_input_signature", lambda bar_store, members, config_fingerprint: signature)

    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    registry = ExposureRegistry(str(tmp_path / "exposure"))

    first = wf.run_diagnostic_walkforward(ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), None, _FakeConfig())
    assert (first["folds_appended"], first["folds_replayed"]) == (5, 0)
    served_first = wf.list_walkforward_sequences(ledger)

    second = wf.run_diagnostic_walkforward(ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), None, _FakeConfig())
    assert (second["folds_appended"], second["folds_replayed"]) == (0, 5)

    served_second = wf.list_walkforward_sequences(ledger)
    assert len(served_second) == 1
    assert [f["fold_index"] for f in served_second[0]["fold_results"]] == [0, 1, 2, 3, 4]
    assert served_second[0]["sequence_verdict"] == served_first[0]["sequence_verdict"]
    assert served_second[0]["decay_view"] == served_first[0]["decay_view"]
    assert ledger.verify_chain()["ok"] is True


# === audit regression: the Mode B predeclaration is LEDGERED BEFORE any outcome is read =============


def test_the_mode_b_predeclaration_is_ledgered_before_the_first_outcome_read(tmp_path, monkeypatch):
    """goal.md J-05 IN SCOPE item 8 ("predeclare (ledgered, before any outcome read)") and spec
    section 6.5 ("registered (ledger row, spec hash, timestamp) FIRST") -- proven by observing the
    ledger's own contents AT the moment the run first touches outcome data, not by reading the
    source order."""
    signature = "sig-order"
    sessions = [f"2026-05-{d:03d}" for d in range(1, 156)]
    records = [
        _fake_playbook_record(s, signature, [_fake_signal("range_trade", "AAPL", 0.3), _fake_signal("range_trade", "MSFT", 0.3)])
        for s in sessions
    ]
    monkeypatch.setattr(wf, "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE", "2020-01-01")
    monkeypatch.setattr(wf, "compute_playbook_input_signature", lambda bar_store, members, config_fingerprint: signature)

    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    registry = ExposureRegistry(str(tmp_path / "exposure"))

    ledger_state_at_first_outcome_read: list[list[dict]] = []
    real_playbook_observations = wf.playbook_observations

    def _observing(*args, **kwargs):
        ledger_state_at_first_outcome_read.append(ledger.all_rows())
        return real_playbook_observations(*args, **kwargs)

    monkeypatch.setattr(wf, "playbook_observations", _observing)

    wf.run_diagnostic_walkforward(ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), None, _FakeConfig())

    assert len(ledger_state_at_first_outcome_read) == 1
    kinds_before_the_read = [r["row_kind"] for r in ledger_state_at_first_outcome_read[0]]
    assert wl.ROW_KIND_MODE_B_SPEC in kinds_before_the_read  # the predeclaration is already ON DISK
    assert wl.ROW_KIND_FOLD_RESULT not in kinds_before_the_read  # nothing evaluated yet

    predeclarations = ledger.rows_of_kind(wl.ROW_KIND_MODE_B_SPEC)
    assert len(predeclarations) == 1
    fold_rows = ledger.rows_of_kind(wl.ROW_KIND_FOLD_RESULT)
    assert fold_rows and all(row["registered_at"] == predeclarations[0]["registered_at"] for row in fold_rows)
    assert all(row["spec_hash"] == predeclarations[0]["spec_hash"] for row in fold_rows)

    # a repeat run reuses the FIRST predeclaration instant rather than minting a later one
    wf.run_diagnostic_walkforward(ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), None, _FakeConfig())
    assert len(ledger.rows_of_kind(wl.ROW_KIND_MODE_B_SPEC)) == 1


# === TC-25/TC-26: compute manager + ledger durability =================================================


def test_tc25_a_second_trigger_while_running_is_refused(tmp_path):
    import threading

    manager = wf.WalkForwardComputeManager()
    release = threading.Event()

    def _slow_work(publish, should_abort):
        release.wait(timeout=5)
        return {}

    first = manager.trigger(_slow_work, run_log_dir=str(tmp_path))
    assert first["state"] == "running"
    second = manager.trigger(_slow_work, run_log_dir=str(tmp_path))
    assert second == {"state": "refused", "reason": "already_running"}
    release.set()
    manager.join_all()


def test_tc25_a_mid_run_exception_resolves_to_a_terminal_failed_run_log_entry(tmp_path):
    from app.research.micro_snapshots import read_run_log

    manager = wf.WalkForwardComputeManager()

    def _raising_work(publish, should_abort):
        publish("step-1")
        raise RuntimeError("boom")

    manager.trigger(_raising_work, run_log_dir=str(tmp_path))
    manager.join_all()
    snap = manager.snapshot()
    assert snap["state"] == "failed"
    assert snap["error"] == "boom"
    runs = read_run_log(str(tmp_path))
    assert runs[0]["state"] == "failed"
    assert runs[0]["error"] == "boom"


def test_tc26_a_truncated_walkforward_ledger_tail_is_caught_even_though_the_chain_still_verifies(tmp_path):
    ledger = wl.WalkForwardLedger(str(tmp_path))
    wl.record_voiding_event(ledger, corpus_id="c", reason="r1")
    wl.record_voiding_event(ledger, corpus_id="c", reason="r2")
    wl.record_voiding_event(ledger, corpus_id="c", reason="r3")

    path = ledger._chain.path
    lines = path.read_text(encoding="utf-8").splitlines()
    del lines[-1]  # delete the newest committed row directly from the JSONL
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = ledger.verify_chain()
    assert result["ok"] is False
    assert result["reason"] == "tail_truncated"


# === the CLI is a thin wrapper, never a second implementation (the scout.py CLI-test precedent) ======


def test_the_cli_runs_the_same_run_diagnostic_walkforward_against_real_env_var_scoped_stores(tmp_path, monkeypatch):
    """``python -m app.research.walkforward --diagnostic`` -- points every store at ``tmp_path``
    via the SAME env-var overrides ``CONFIG.dataset_dir_resolved()``/``desk_universe_dir_resolved
    ()``/``bar_dir_resolved()`` already read, never touches the real ``.data`` corpus. An empty
    store tree is an honest 0-fold run, never a crash."""
    import sys

    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_MICRO_WALKFORWARD_DIR", str(tmp_path / "wf"))
    monkeypatch.setenv("TAPEOLOGY_MICRO_EXPOSURE_REGISTRY_DIR", str(tmp_path / "exposure"))
    monkeypatch.setattr(sys, "argv", ["walkforward.py", "--diagnostic"])

    exit_code = wf.main()
    assert exit_code == 0

    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    # an empty universe/playbook tree registers the fold spec but evaluates zero folds -- honest,
    # never a crash (build_folds([], ...) == []).
    fold_specs = wl.latest_fold_spec(ledger, wf.PLAYBOOK_DIAGNOSTIC_CORPUS_ID)
    assert fold_specs is not None
    assert fold_specs["geometry"] == wf.DIAGNOSTIC_GEOMETRY


def test_the_cli_with_no_flag_does_nothing(monkeypatch):
    import sys

    monkeypatch.setattr(sys, "argv", ["walkforward.py"])
    assert wf.main() == 0


# === route wiring: the 3 walkforward routes actually work end to end (micro_routes.py) ===============


def test_walkforward_routes_serve_empty_state_honestly_and_the_compute_trigger_round_trips(tmp_path, monkeypatch):
    signature = "sig-route-test"
    sessions = [f"2026-03-{d:03d}" for d in range(1, 156)]
    records = [
        _fake_playbook_record(s, signature, [_fake_signal("range_trade", "AAPL", 0.3), _fake_signal("range_trade", "MSFT", 0.3)])
        for s in sessions
    ]
    monkeypatch.setattr(wf, "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE", "2020-01-01")
    monkeypatch.setattr(wf, "compute_playbook_input_signature", lambda bar_store, members, config_fingerprint: signature)

    ledger_dir = str(tmp_path / "wf_ledger")
    exposure_dir = str(tmp_path / "wf_exposure")
    manager = wf.WalkForwardComputeManager()

    app.dependency_overrides[get_walkforward_ledger_dir] = lambda: ledger_dir
    app.dependency_overrides[get_micro_exposure_registry_dir] = lambda: exposure_dir
    app.dependency_overrides[get_walkforward_compute_manager] = lambda: manager
    app.dependency_overrides[get_universe_store] = lambda: _FakeUniverseStore(["AAPL"])
    app.dependency_overrides[get_bar_store] = lambda: None
    app.dependency_overrides[get_playbook_store] = lambda: _FakePlaybookStore(records)
    try:
        with TestClient(app) as client:
            empty = client.get("/research/desk/micro/walkforward")
            assert empty.status_code == 200
            assert empty.json() == {"fold_specs": [], "sequences": [], "chain_verification": {"ok": True, "failed_at_row": None, "reason": None}}

            triggered = client.post("/research/desk/micro/walkforward/compute")
            assert triggered.status_code == 200
            assert triggered.json()["state"] == "running"

            manager.join_all(timeout=30.0)
            polled = client.get("/research/desk/micro/walkforward/compute")
            assert polled.json()["state"] == "done"

            served = client.get("/research/desk/micro/walkforward")
            body = served.json()
            assert len(body["fold_specs"]) == 1
            assert body["fold_specs"][0]["corpus_id"] == wf.PLAYBOOK_DIAGNOSTIC_CORPUS_ID
            assert len(body["sequences"]) == 1
            assert len(body["sequences"][0]["fold_results"]) == 5
            assert body["chain_verification"]["ok"] is True

            runs = client.get("/research/desk/micro/walkforward/runs")
            assert runs.json()["runs"][0]["state"] == "done"

            refused = client.post("/research/desk/micro/walkforward/compute/cancel")
            assert refused.status_code == 409
    finally:
        for dep in (get_walkforward_ledger_dir, get_micro_exposure_registry_dir, get_walkforward_compute_manager, get_universe_store, get_bar_store, get_playbook_store):
            app.dependency_overrides.pop(dep, None)
