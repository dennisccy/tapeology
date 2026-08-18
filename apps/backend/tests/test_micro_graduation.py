"""``micro_graduation.py`` (Era "The Rapid Microscope" J-07) -- test-first contract: TC-1 through
TC-9, per ``docs/phases/goal-rapid-microscope-iter-10.md``. Fixture-only throughout (no real
sealed shard exists this era; J-06 step 4 is human-blocked) -- every scenario builds its OWN
ledgered evidence directly through the sibling modules' existing public functions
(``walkforward_ledger.append_fold_result``, ``vault.seal_shard``/``assign_shard``/``expose_shard``,
``scout_ledger.ScoutLedger.append_row``) and then exercises ``micro_graduation.py``'s own
evaluation functions against it -- mirroring ``test_walkforward.py``'s own "hand-built,
ledgered-but-not-re-deriving-the-producer's-own-machinery" style for testing a CONSUMER's logic in
isolation."""

from __future__ import annotations

import ast
import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.research import micro_graduation as g
from app.research import scout_ledger
from app.research import vault
from app.research import walkforward as wf
from app.research import walkforward_ledger as wl
from app.research.micro_routes import get_micro_graduation_dir
from app.research.scout_ledger import ScoutLedger
from test_copy_discipline import find_violations

# === helpers ==========================================================================================

_ECON_FLOOR = {"floor_bps": 5.0}
_FIXTURE_VAULT_SECRET = b"a-graduation-fixture-vault-secret"


def _append_sufficient_fold(
    wf_ledger: wl.WalkForwardLedger,
    *,
    fold_index: int,
    sequence_id: str,
    corpus_id: str,
    spec_hash: str = "spec-fixture-hash-1",
    sidedness: str = "long",
    econ_floor: dict | None = _ECON_FLOOR,
    evidence_class: str = wf.EVIDENCE_CLASS_HISTORICAL_OOS,
    process_label: str = wf.PROCESS_LABEL_RULE,
    effect: float = 10.0,
    sign: str = "positive",
    registered_at: str = "2026-01-01T00:00:00.000000Z",
) -> dict:
    """A hand-built, already-SUFFICIENT ``fold_result``-shaped row, appended through the REAL
    ``walkforward_ledger.append_fold_result`` (so it is genuinely retrievable via
    ``walkforward.fold_results_for_sequence``, the same door ``micro_graduation.py`` itself reads
    through) -- the exact field shape ``walkforward.evaluate_mode_b_fold`` produces, without
    re-deriving ITS OWN exposure-registry/observation-crunching machinery (already covered by
    ``test_walkforward.py``'s own suite; this file tests graduation's consumption of the result,
    not walk-forward's own production of it)."""
    fields = {
        "sequence_id": sequence_id, "corpus_id": corpus_id, "mode": "B", "rule_id": "fixture-rule",
        "spec_hash": spec_hash, "fold_index": fold_index, "sidedness": sidedness, "econ_floor": econ_floor,
        "evidence_class": evidence_class, "process_label": process_label, "registered_at": registered_at,
        "status": wf.FOLD_STATUS_SUFFICIENT, "n": 40, "n_sessions": 10, "n_symbols": 3,
        "effect": effect, "sign": sign, "missing": {},
    }
    return wl.append_fold_result(wf_ledger, fields)


def _three_survivor_folds(wf_ledger: wl.WalkForwardLedger, *, sequence_id: str, corpus_id: str, **overrides) -> None:
    for i in range(3):  # exactly WF_MIN_SUFFICIENT_FOLDS
        _append_sufficient_fold(wf_ledger, fold_index=i, sequence_id=sequence_id, corpus_id=corpus_id, **overrides)


def _exposed_shard(
    tmp_path, *, family_root_id: str, dataset_id: str = "dataset-1", symbol: str = "PG",
    session_date: str = "2026-06-09",
) -> tuple["vault.VaultShardLedger", "vault.VaultUniverseLedger"]:
    """seal -> assign -> expose ONE fixture shard to ``family_root_id`` -- the ``test_vault.py``
    ``_sealed_shard_ledger``/assign/expose sequence, mirrored (no universe registration needed:
    shard serialization does not depend on it, exactly as ``test_vault.py``'s own helper omits
    it)."""
    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    vault.seal_shard(
        shard_ledger, dataset_id=dataset_id, universe_id="u1", content_checksum="a" * 64,
        event_count=12_345, vault_secret=_FIXTURE_VAULT_SECRET,
    )
    vault.assign_shard(shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id, symbol=symbol, session_date=session_date)
    vault.expose_shard(shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id)
    return shard_ledger, universe_ledger


def _scout_row(*, family_root_id: str, family_id: str, candidate_id: str, decision: str) -> dict:
    return {
        "family_id": family_id, "family_root_id": family_root_id, "candidate_id": candidate_id,
        "decision": decision, "reason": None, "notes": "",
    }


# === TC-1: exploratory -> walkforward_survivor =======================================================


def test_tc1_all_five_conditions_hold_advances_to_walkforward_survivor(tmp_path):
    family_root_id = scout_ledger.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    corpus_id = "graduation-fixture-corpus-1"
    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    _three_survivor_folds(wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id)

    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
    result = g.evaluate_walkforward_survivor_transition(
        grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id,
    )

    assert result["transition"] == g.TRANSITION_APPENDED
    assert result["state"] == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR
    row = result["row"]
    assert row["rule_name"] == wf.WF_SURVIVOR_RULE_V1
    assert all(row["conditions"].values())
    assert g.current_graduation_state(grad_ledger, family_root_id) == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR


# === TC-5: a diagnostic-only twin is refused at the first transition =================================


def test_tc5_a_diagnostic_only_twin_is_refused_and_state_stays_exploratory(tmp_path):
    family_root_id = scout_ledger.compute_family_root_id("cumulative_delta_divergence", "level_test", "clock_60s")
    corpus_id = "graduation-fixture-corpus-diagnostic"
    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    # every fold is historical_exposed_diagnostic -- never eligible, so condition 1 fails.
    _three_survivor_folds(
        wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id,
        evidence_class=wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC,
    )

    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
    with pytest.raises(g.GraduationTransitionRefusedError) as exc_info:
        g.evaluate_walkforward_survivor_transition(
            grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id,
        )
    assert exc_info.value.family_root_id == family_root_id
    assert exc_info.value.target_state == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR
    # never silently advanced -- and no row was ever appended for the refused attempt.
    assert g.current_graduation_state(grad_ledger, family_root_id) == g.GRADUATION_STATE_EXPLORATORY
    assert g.state_transitions_for_family(grad_ledger, family_root_id) == []


def test_a_below_floor_candidate_with_zero_ledgered_folds_is_also_refused_never_a_fabricated_verdict(tmp_path):
    """The OTHER refusal path ``sequence_verdict`` itself owns (below ``WF_MIN_SUFFICIENT_FOLDS``,
    here zero) -- exercised directly so this module's own refusal wiring covers both of
    ``sequence_verdict``'s ways of saying no, not just the "five conditions evaluated and failed"
    one TC-5 already covers."""
    family_root_id = scout_ledger.compute_family_root_id("burst_intensity", "playbook_signal", "trades_20")
    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
    with pytest.raises(g.GraduationTransitionRefusedError, match="sufficient folds"):
        g.evaluate_walkforward_survivor_transition(
            grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id="seq-never-evaluated",
        )
    assert g.current_graduation_state(grad_ledger, family_root_id) == g.GRADUATION_STATE_EXPLORATORY


# === TC-7: replay idempotency -- a repeated advancement check never appends a duplicate row ==========


def test_tc7_a_second_advancement_check_with_no_new_evidence_is_replayed_not_duplicated(tmp_path):
    family_root_id = scout_ledger.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_60")
    corpus_id = "graduation-fixture-corpus-replay"
    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    _three_survivor_folds(wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id)
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))

    first = g.evaluate_walkforward_survivor_transition(grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id)
    assert first["transition"] == g.TRANSITION_APPENDED
    rows_after_first = len(grad_ledger.rows_of_kind(g.ROW_KIND_STATE_TRANSITION))

    second = g.evaluate_walkforward_survivor_transition(grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id)
    assert second["transition"] == g.TRANSITION_REPLAYED
    assert second["row"] == first["row"]
    assert len(grad_ledger.rows_of_kind(g.ROW_KIND_STATE_TRANSITION)) == rows_after_first  # unchanged


# === TC-2: walkforward_survivor -> sealed_survivor ====================================================


def test_tc2_a_passing_sealed_evaluation_advances_to_sealed_survivor(tmp_path):
    family_root_id = scout_ledger.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    corpus_id = "graduation-fixture-corpus-sealed-pass"
    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    _three_survivor_folds(wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id)
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
    g.evaluate_walkforward_survivor_transition(grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id)

    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id, dataset_id="dataset-pass")
    eval_result = g.record_sealed_evaluation(
        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-pass",
        spec_hash="spec-fixture-hash-1", passed=True,
    )
    assert eval_result["transition"] == g.TRANSITION_APPENDED
    assert eval_result["row"]["passed"] is True

    result = g.evaluate_sealed_survivor_transition(grad_ledger, family_root_id=family_root_id, dataset_id="dataset-pass")
    assert result["transition"] == g.TRANSITION_APPENDED
    assert result["state"] == g.GRADUATION_STATE_SEALED_SURVIVOR
    assert g.current_graduation_state(grad_ledger, family_root_id) == g.GRADUATION_STATE_SEALED_SURVIVOR


def test_sealed_evaluation_is_refused_against_a_shard_never_exposed_to_this_family(tmp_path):
    family_root_id = scout_ledger.compute_family_root_id("a", "b", "c")
    other_family_root_id = scout_ledger.compute_family_root_id("x", "y", "z")
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
    # the shard is exposed, but to a DIFFERENT family entirely.
    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=other_family_root_id)

    with pytest.raises(g.GraduationTransitionRefusedError, match="not an EXPOSED vault shard"):
        g.record_sealed_evaluation(
            grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
            spec_hash="spec-x", passed=True,
        )
    assert g.sealed_evaluations_for_family(grad_ledger, family_root_id) == []


def test_a_second_identical_sealed_evaluation_call_is_replayed_a_second_different_one_is_refused(tmp_path):
    family_root_id = scout_ledger.compute_family_root_id("microprice_drift", "band_wall_touch", "trades_20")
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id)

    first = g.record_sealed_evaluation(
        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
        spec_hash="spec-x", passed=True,
    )
    assert first["transition"] == g.TRANSITION_APPENDED

    replay = g.record_sealed_evaluation(
        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
        spec_hash="spec-x", passed=True,
    )
    assert replay["transition"] == g.TRANSITION_REPLAYED
    assert replay["row"] == first["row"]
    assert len(g.sealed_evaluations_for_family(grad_ledger, family_root_id)) == 1  # never a duplicate row

    with pytest.raises(g.GraduationTransitionRefusedError, match="never a second draw"):
        g.record_sealed_evaluation(
            grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
            spec_hash="spec-x", passed=False,  # a genuinely DIFFERENT verdict for the same pair
        )
    assert len(g.sealed_evaluations_for_family(grad_ledger, family_root_id)) == 1  # still never a duplicate


def test_sealed_survivor_transition_is_refused_before_walkforward_survivor_is_reached(tmp_path):
    """States are strictly ordered (spec section 8) -- a candidate that never earned
    ``walkforward_survivor`` cannot skip straight to ``sealed_survivor`` even with a passing sealed
    evaluation on record."""
    family_root_id = scout_ledger.compute_family_root_id("spread_change", "band_wall_touch", "trades_20")
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id)
    g.record_sealed_evaluation(
        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
        spec_hash="spec-x", passed=True,
    )
    with pytest.raises(g.GraduationTransitionRefusedError, match="strictly ordered"):
        g.evaluate_sealed_survivor_transition(grad_ledger, family_root_id=family_root_id, dataset_id="dataset-1")


# === TC-6: a failed-sealed twin's permanent failed verdict is carried into its own bundle =============


def test_tc6_a_failed_sealed_evaluation_never_advances_and_is_carried_into_the_bundle(tmp_path):
    family_root_id = scout_ledger.compute_family_root_id("response_asymmetry", "band_wall_touch", "trades_20")
    corpus_id = "graduation-fixture-corpus-sealed-fail"
    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    _three_survivor_folds(wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id)
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
    g.evaluate_walkforward_survivor_transition(grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id)

    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id, dataset_id="dataset-fail")
    eval_result = g.record_sealed_evaluation(
        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-fail",
        spec_hash="spec-fixture-hash-1", passed=False, detail={"reason": "fixture: sealed effect below floor"},
    )
    assert eval_result["row"]["passed"] is False

    with pytest.raises(g.GraduationTransitionRefusedError, match="permanent"):
        g.evaluate_sealed_survivor_transition(grad_ledger, family_root_id=family_root_id, dataset_id="dataset-fail")
    # the state never advanced past walkforward_survivor.
    assert g.current_graduation_state(grad_ledger, family_root_id) == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR

    scout = ScoutLedger(str(tmp_path / "scout"))
    bundle = g.build_export_bundle(
        grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
        family_root_id=family_root_id, sequence_id=sequence_id,
    )
    assert bundle["state"] == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR
    failed_verdicts = [e for e in bundle["sealed_evaluations"] if e["passed"] is False]
    assert len(failed_verdicts) == 1
    assert failed_verdicts[0]["dataset_id"] == "dataset-fail"
    assert bundle["family_multiplicity"]["prior_sealed_verdicts"] == bundle["sealed_evaluations"]


# === TC-3/TC-4: sealed_survivor -> referee_handoff_ready, and the bundle's own content ================


def test_tc3_and_tc4_the_full_pipeline_produces_a_validating_bundle_and_referee_handoff_ready(tmp_path):
    family_root_id = scout_ledger.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    corpus_id = "graduation-fixture-corpus-e2e"
    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    _three_survivor_folds(wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id)

    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
    g.evaluate_walkforward_survivor_transition(grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id)

    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id, dataset_id="dataset-e2e")
    g.record_sealed_evaluation(
        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-e2e",
        spec_hash="spec-fixture-hash-1", passed=True,
    )
    g.evaluate_sealed_survivor_transition(grad_ledger, family_root_id=family_root_id, dataset_id="dataset-e2e")

    # every ledgered trial for the family, including a kill -- across two SIBLING family_ids that
    # share the SAME family_root_id (TC-3: "every ledgered trial ... including kills").
    scout = ScoutLedger(str(tmp_path / "scout"))
    scout.append_row(_scout_row(family_root_id=family_root_id, family_id="fam-a", candidate_id="cand-1", decision="survive"))
    scout.append_row(_scout_row(family_root_id=family_root_id, family_id="fam-b", candidate_id="cand-2", decision="killed_null"))
    # an unrelated family's trial must NEVER leak into this bundle.
    scout.append_row(_scout_row(family_root_id="unrelated-root", family_id="fam-c", candidate_id="cand-3", decision="survive"))

    result = g.evaluate_referee_handoff_ready_transition(
        grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
        family_root_id=family_root_id, sequence_id=sequence_id,
    )
    assert result["transition"] == g.TRANSITION_APPENDED
    assert result["state"] == g.GRADUATION_STATE_REFEREE_HANDOFF_READY
    assert g.current_graduation_state(grad_ledger, family_root_id) == g.GRADUATION_STATE_REFEREE_HANDOFF_READY

    bundle = result["bundle"]
    assert g.bundle_validates(bundle)
    # TC-3: frozen spec hash; family_root_id lineage; every ledgered trial including kills
    # (union-N); every fold with its evidence_class and process_label; every shard touched; the
    # proposed confirmation boundary; family/multiplicity metadata.
    assert bundle["family_root_id"] == family_root_id
    assert bundle["spec_hash"] == "spec-fixture-hash-1"
    assert bundle["union_n_variants_tried"] == scout_ledger.distinct_variant_count(
        [row for row in scout.all_rows() if row["family_root_id"] == family_root_id]
    )
    assert bundle["union_n_variants_tried"] == 2  # cand-1 survives, cand-2 is killed -- both counted
    decisions = {row["candidate_id"]: row["decision"] for row in bundle["scout_trials"]}
    assert decisions == {"cand-1": "survive", "cand-2": "killed_null"}  # the kill IS present
    assert all("unrelated" not in row["candidate_id"] for row in bundle["scout_trials"])
    assert {row["evidence_class"] for row in bundle["fold_results"]} == {wf.EVIDENCE_CLASS_HISTORICAL_OOS}
    assert {row["process_label"] for row in bundle["fold_results"]} == {wf.PROCESS_LABEL_RULE}
    assert len(bundle["fold_results"]) == 3
    assert [s["dataset_id"] for s in bundle["shards_touched"]] == ["dataset-e2e"]
    assert bundle["proposed_confirmation_boundary"] is not None
    assert bundle["family_multiplicity"]["sibling_family_ids"] == ["fam-a", "fam-b"]

    # TC-4: the bundle's own copy states, verbatim, that this does not imply current-Referee
    # registrability of a flow predicate.
    assert bundle["referee_registration_note"] == g.REFEREE_FUTURE_REVISION_SENTENCE
    assert "future named revision" in bundle["referee_registration_note"]
    assert "docs/referee-statistical-spec.md" in bundle["referee_registration_note"]

    # replay: a second call re-derives the SAME live bundle rather than appending a duplicate row.
    rows_after_first = len(grad_ledger.rows_of_kind(g.ROW_KIND_STATE_TRANSITION))
    replay = g.evaluate_referee_handoff_ready_transition(
        grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
        family_root_id=family_root_id, sequence_id=sequence_id,
    )
    assert replay["transition"] == g.TRANSITION_REPLAYED
    assert g.bundle_validates(replay["bundle"])
    assert len(grad_ledger.rows_of_kind(g.ROW_KIND_STATE_TRANSITION)) == rows_after_first


def test_referee_handoff_ready_is_refused_before_sealed_survivor_is_reached(tmp_path):
    family_root_id = scout_ledger.compute_family_root_id("quote_imbalance", "band_wall_touch", "trades_20")
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    scout = ScoutLedger(str(tmp_path / "scout"))
    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    with pytest.raises(g.GraduationTransitionRefusedError, match="strictly ordered"):
        g.evaluate_referee_handoff_ready_transition(
            grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
            family_root_id=family_root_id, sequence_id="seq-never-evaluated",
        )


def test_bundle_is_buildable_and_honestly_partial_for_a_family_with_no_evidence_at_all(tmp_path):
    """The export bundle is never gated to sealed_survivor+ candidates -- buildable for ANY
    ledgered family_root_id, always carrying its OWN current state (module docstring)."""
    family_root_id = scout_ledger.compute_family_root_id("never_evaluated", "band_wall_touch", "trades_20")
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    scout = ScoutLedger(str(tmp_path / "scout"))
    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))

    bundle = g.build_export_bundle(grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id)
    assert bundle["state"] == g.GRADUATION_STATE_EXPLORATORY
    assert bundle["scout_trials"] == []
    assert bundle["fold_results"] == []
    assert bundle["shards_touched"] == []
    assert bundle["sealed_evaluations"] == []
    assert bundle["proposed_confirmation_boundary"] is None
    assert g.bundle_validates(bundle)  # honestly EMPTY fields still validate -- nothing is MISSING


# === TC-8: tail-anchor truncation detection ===========================================================


def test_tc8_a_truncated_tail_is_caught_by_the_durable_head_anchor(tmp_path):
    ledger = g.GraduationLedger(str(tmp_path / "grad"))
    ledger.append_row({"row_kind": g.ROW_KIND_STATE_TRANSITION, "family_root_id": "f1", "to_state": "walkforward_survivor"})
    ledger.append_row({"row_kind": g.ROW_KIND_SEALED_EVALUATION, "family_root_id": "f1", "dataset_id": "d1", "passed": True})
    ledger.append_row({"row_kind": g.ROW_KIND_STATE_TRANSITION, "family_root_id": "f1", "to_state": "sealed_survivor"})

    lines = ledger._chain.path.read_text(encoding="utf-8").splitlines()
    del lines[-1]  # erase the most recent row -- the remaining chain is perfectly self-consistent
    ledger._chain.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assert ledger.verify_chain() == {"ok": False, "failed_at_row": 2, "reason": "tail_truncated"}


# === TC-9: the real, currently-empty ledger route serves an honest empty state ========================


def test_tc9_get_graduation_route_serves_an_honest_empty_state_never_a_500(tmp_path):
    def _override_dir() -> str:
        return str(tmp_path / "grad")

    app.dependency_overrides[get_micro_graduation_dir] = _override_dir
    try:
        with TestClient(app) as client:
            response = client.get("/research/desk/micro/graduation")
    finally:
        del app.dependency_overrides[get_micro_graduation_dir]

    assert response.status_code == 200
    body = response.json()
    assert body["families"] == []
    assert body["message"] == "No candidates ledgered."
    assert body["message"] == g.EMPTY_LEDGER_MESSAGE
    assert body["chain_verification"] == {"ok": True, "failed_at_row": None, "reason": None}


def test_get_graduation_route_serves_recorded_families_with_no_message(tmp_path):
    def _override_dir() -> str:
        return str(tmp_path / "grad")

    family_root_id = scout_ledger.compute_family_root_id("burst_intensity", "band_wall_touch", "trades_20")
    corpus_id = "graduation-fixture-corpus-route"
    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    _three_survivor_folds(wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id)
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
    g.evaluate_walkforward_survivor_transition(grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id)

    app.dependency_overrides[get_micro_graduation_dir] = _override_dir
    try:
        with TestClient(app) as client:
            response = client.get("/research/desk/micro/graduation")
    finally:
        del app.dependency_overrides[get_micro_graduation_dir]

    assert response.status_code == 200
    body = response.json()
    assert body["message"] is None
    assert len(body["families"]) == 1
    assert body["families"][0]["family_root_id"] == family_root_id
    assert body["families"][0]["state"] == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR


# === guard: the accessor import-ban (test_micro_accessor.py's generic app/**.py sweep already
# covers this module automatically -- micro_graduation.py opens no snapshot/vault event data at
# all, so it needs no accessor door in the first place; asserted directly below rather than left
# implicit). ===========================================================================================


def test_micro_graduation_module_imports_nothing_from_micro_accessor():
    """This module reads only ledger METADATA (states, transitions, sealed pass/fail verdicts) via
    ``walkforward.py``/``vault.py``'s own existing functions -- never raw snapshot or vault EVENT
    data, so it has no reason to import ``micro_accessor`` at all (the door J-05/J-06's own guard
    tests already police for every other module in ``app/``)."""
    source = open(g.__file__, encoding="utf-8").read()
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.rsplit(".", 1)[-1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.rsplit(".", 1)[-1])
    assert "micro_accessor" not in imported


# === guard: the micro_*/scout*/walkforward* no-threshold-sweep ban, extended to micro_graduation.py
# (the ``test_desk_playbook_guards.py`` AST-source-scan pattern, scoped to this new module: no
# existing shared "micro sweep ban" helper exists yet for scout.py/walkforward.py to extend, so this
# module gains its own copy of the pattern, exactly as goal.md's Constraints describe -- "new micro
# modules add their own guards"). =====================================================================

_SWEEP_OVER_NAMED_CONSTANT = re.compile(r"for\s+\w+(?:\s*,\s*\w+)*\s+in\s+[^\n:]*(?:WF_|SCOUT_|MICRO_|GRADUATION_)[A-Z_]*_CANDIDATES\b")
_SWEEP_OVER_LITERAL_SEQUENCE = re.compile(r"for\s+\w+\s+in\s+[\(\[]\s*-?\d+(?:\.\d+)?\s*(?:,\s*-?\d+(?:\.\d+)?\s*){1,}[\)\]]")


def _strip_comments_and_docstrings(source: str) -> str:
    without_triple_double = re.sub(r'"""(?:.|\n)*?"""', "", source)
    without_triple_single = re.sub(r"'''(?:.|\n)*?'''", "", without_triple_double)
    return re.sub(r"#[^\n]*", "", without_triple_single)


def test_micro_graduation_contains_no_threshold_sweep_loop():
    """The concrete, module-scoped form of the era's anti-goal: no code path in
    ``micro_graduation.py`` may iterate over a named threshold-candidate constant or a literal
    numeric candidate sequence to select a threshold -- this module has no thresholds of its own
    (module docstring: it delegates the entire WF_SURVIVOR_RULE_V1 predicate to ``walkforward.py``
    and never computes a statistic), so the guard is expected to find nothing, permanently."""
    source = _strip_comments_and_docstrings(open(g.__file__, encoding="utf-8").read())
    named_hits = _SWEEP_OVER_NAMED_CONSTANT.findall(source)
    literal_hits = _SWEEP_OVER_LITERAL_SEQUENCE.findall(source)
    assert not named_hits, f"micro_graduation.py sweeps a named threshold-candidate constant: {named_hits}"
    assert not literal_hits, f"micro_graduation.py sweeps a literal numeric candidate sequence: {literal_hits}"


def test_no_threshold_sweep_guard_can_fail_on_seeded_violations():
    """The lint CAN fail -- a lint that cannot fail proves nothing (the ``test_copy_discipline.py``
    precedent)."""
    seeded_named = "for candidate in GRADUATION_FIXTURE_THRESHOLD_CANDIDATES:\n    pass\n"
    assert _SWEEP_OVER_NAMED_CONSTANT.search(seeded_named) is not None

    seeded_literal = "for mult in [0.5, 1.0, 1.5]:\n    pass\n"
    assert _SWEEP_OVER_LITERAL_SEQUENCE.search(seeded_literal) is not None

    # real loops this module actually uses -- must NOT be flagged.
    benign_loops = [
        "for row in ledger.rows_of_kind(ROW_KIND_STATE_TRANSITION):\n    pass\n",
        "for family_root_id in order:\n    pass\n",
        "for fold in fold_results:\n    pass\n",
        "for field in _REQUIRED_BUNDLE_FIELDS:\n    pass\n",
    ]
    for benign in benign_loops:
        assert _SWEEP_OVER_NAMED_CONSTANT.search(benign) is None, benign
        assert _SWEEP_OVER_LITERAL_SEQUENCE.search(benign) is None, benign


# === guard: the copy-discipline lint, extended to micro_graduation.py's own served copy ==============


def test_graduation_served_copy_clears_the_copy_discipline_lexicon():
    """The ``test_copy_discipline.py`` precedent, reused (not reimplemented) directly: this
    module's own served strings -- the empty-ledger message and the referee-registration
    disclaimer -- carry no imperative/predictive/certainty-claim language."""
    assert find_violations(g.EMPTY_LEDGER_MESSAGE) == []
    assert find_violations(g.REFEREE_FUTURE_REVISION_SENTENCE) == []
