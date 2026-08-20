"""``micro_sealed_evaluation.py`` (Era "The Rapid Microscope" J-07/TR-23, r6 owner ruling,
``docs/rapid-validation-spec.md`` section 8.1) -- test-first contract: TC-1 through TC-9, per
``docs/phases/goal-rapid-microscope-iter-17.md``.

Fixture-only throughout (goal.md's own "do not seed/mutate/expose real Vault data" instruction;
zero real sealed shards exist this era) -- every scenario plants a REAL dataset + snapshot on disk
(the ``test_micro_accessor.py`` ``_plant_dataset_and_snapshot`` precedent, so the evaluator's own
accessor read is genuine, never mocked), a real seal->assign->expose vault shard sequence (the
``test_micro_graduation.py`` ``_exposed_shard`` precedent), and a hand-built ``observations`` list
(the ``test_walkforward.py`` ``_observation``/small-floors-override precedent) -- mirroring, never
re-deriving, this codebase's own established fixture conventions.

**The governing acceptance rule for this trap (iteration-17 phase spec, "the round's central
risk").** Two consecutive prior rounds shipped a brand-new trap that was structurally unable to
fail. TC-8 below is the mutation-proof (a deliberately weakened ``_derive_verdict`` makes the
corrected assertion fail, naming the specific wrong verdict; restoring makes it pass again). TC-9
is the fixture-discrimination proof (the correct and corrupted recomputed effects are DIFFERENT
numeric values -- 10.0 vs 1.0 -- never coincidentally equal), run independently of the mutation
test so the fixture's own soundness does not rely on the mutation succeeding."""

from __future__ import annotations

import re

import pytest

from app.config import CONFIG
from app.research import micro_graduation as g
from app.research import micro_sealed_evaluation as sealed_eval
from app.research import scout_ledger
from app.research import vault
from app.research import walkforward as wf
from app.research.datasets import DatasetStore
from app.research.micro_accessor import MicroAccessor, MicroAccessorOriginFenceError
from app.research.micro_snapshots import resolve_micro_snapshots_dir
from tests.test_micro_accessor import _plant_dataset_and_snapshot

# === helpers ==========================================================================================

_FIXTURE_VAULT_SECRET = b"a-sealed-evaluation-fixture-vault-secret"
_SEALED_AT = "2026-01-01T00:00:00.000000Z"
_SPEC_REGISTERED_AT = "2026-01-02T00:00:00.000000Z"  # strictly before assigned_at, below
_ASSIGNED_AT = "2026-01-05T00:00:00.000000Z"
_EXPOSED_AT = "2026-01-06T00:00:00.000000Z"
_EVALUATED_AT = "2026-06-10T00:00:00.000000Z"

# Tiny floors so a 3-observation hand-built fixture clears the "sufficient" status without needing
# 30 real observations -- the test_walkforward.py `floors={"wf_fold_min_observations": 1, ...}`
# precedent, mirrored exactly.
_TINY_FLOORS = {"wf_fold_min_observations": 3, "wf_fold_min_signal_sessions": 1, "wf_fold_min_symbols": 1}
_ECON_FLOOR = {"floor_bps": 5.0}


def _observation(session_date: str, symbol: str, value: float) -> dict:
    return {"session_date": session_date, "symbol": symbol, "value": value}


def _passing_observations() -> list[dict]:
    """Mean effect = 10.0 -- clears ``_ECON_FLOOR``'s 5.0 bps floor in the "long"/positive
    direction. THE "correct" fixture TC-9 discriminates against."""
    return [
        _observation("2026-06-08", "PG", 10.0),
        _observation("2026-06-08", "PG", 12.0),
        _observation("2026-06-08", "PG", 8.0),
    ]


def _below_floor_observations() -> list[dict]:
    """Mean effect = 1.0 -- POSITIVE (correct direction) but strictly below the 5.0 bps econ floor,
    so it FAILS on magnitude alone, never on direction. Deliberately a DIFFERENT numeric value from
    ``_passing_observations``'s own 10.0 (TC-9: never coincidentally equal)."""
    return [
        _observation("2026-06-08", "PG", 1.0),
        _observation("2026-06-08", "PG", 1.2),
        _observation("2026-06-08", "PG", 0.8),
    ]


def _insufficient_observations() -> list[dict]:
    """Only 2 observations -- below ``_TINY_FLOORS``'s own ``wf_fold_min_observations: 3`` floor."""
    return [_observation("2026-06-08", "PG", 10.0), _observation("2026-06-08", "PG", 12.0)]


def _rig(tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    snapshots_dir = resolve_micro_snapshots_dir(str(tmp_path / "datasets"))
    dataset_meta = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol="PG",
        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
    )
    return dataset_store, snapshots_dir, dataset_meta


def _exposed_shard_for(
    tmp_path, *, family_root_id: str, dataset_id: str,
    assigned_at: str = _ASSIGNED_AT, exposed_at: str = _EXPOSED_AT,
) -> tuple["vault.VaultShardLedger", "vault.VaultUniverseLedger"]:
    """seal -> assign -> expose ONE fixture shard, with EXPLICIT, controllable
    ``assigned_at``/``exposed_at`` timestamps (the ``test_micro_graduation.py`` ``_exposed_shard``
    precedent, extended: step 1 of the mandatory sequence needs a spec ``registered_at`` strictly
    BEFORE the shard's own ``assigned_at``, so the fixture must be able to pin that instant)."""
    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    vault.seal_shard(
        shard_ledger, dataset_id=dataset_id, universe_id="u1", content_checksum="c" * 64,
        event_count=500, vault_secret=_FIXTURE_VAULT_SECRET, sealed_at=_SEALED_AT,
    )
    vault.assign_shard(
        shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id, symbol="PG",
        session_date="2026-06-09", assigned_at=assigned_at,
    )
    vault.expose_shard(shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id, exposed_at=exposed_at)
    return shard_ledger, universe_ledger


def _candidate_spec(
    *, family_root_id: str, candidate_id: str = "cand-1", family_id: str = "fam-a",
    spec_hash: str = "spec-hash-1", sidedness: str = "long", econ_floor: dict | None = _ECON_FLOOR,
    evidence_class: str = wf.EVIDENCE_CLASS_HISTORICAL_OOS, process_label: str = wf.PROCESS_LABEL_RULE,
    registered_at: str = _SPEC_REGISTERED_AT, rule_hash: str | None = None, floors: dict | None = _TINY_FLOORS,
) -> dict:
    return {
        "family_root_id": family_root_id, "candidate_id": candidate_id, "family_id": family_id,
        "spec_hash": spec_hash, "sidedness": sidedness, "econ_floor": econ_floor,
        "evidence_class": evidence_class, "process_label": process_label, "registered_at": registered_at,
        "sealed_pass_rule_hash": rule_hash if rule_hash is not None else sealed_eval.sealed_pass_rule_hash(),
        "floors": floors,
    }


def _family_root_id(seed: str) -> str:
    return scout_ledger.compute_family_root_id(f"impact_efficiency_trend_{seed}", "band_wall_touch", "trades_20")


# === TC-1: the old caller-supplied `passed: bool` shape is structurally impossible ====================


def test_tc1_the_old_passed_bool_call_shape_is_structurally_refused(tmp_path):
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
    with pytest.raises(TypeError):
        g.record_sealed_evaluation(  # the OLD call shape, verbatim
            grad_ledger, family_root_id="f", dataset_id="d", spec_hash="s", passed=True,
        )


# === TC-2: the full seven-step sequence, positive path =================================================


def test_tc2_the_full_mandatory_sequence_derives_a_deterministic_pass_verdict_and_persists_it(tmp_path):
    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
    family_root_id = _family_root_id("tc2")
    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
    candidate_spec = _candidate_spec(family_root_id=family_root_id)
    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))

    result = sealed_eval.evaluate_sealed_verdict(
        grad_ledger, shard_ledger, universe_ledger, accessor,
        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
        observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
    )

    assert result["transition"] == g.TRANSITION_APPENDED
    row = result["row"]
    assert row["verdict"] == sealed_eval.SEALED_VERDICT_PASS
    assert row["failure_reason"] is None
    assert row["family_root_id"] == family_root_id
    assert row["dataset_id"] == dataset_meta["id"]
    assert row["candidate_id"] == "cand-1"
    assert row["family_id"] == "fam-a"
    assert row["spec_hash"] == "spec-hash-1"
    assert row["shard_checksum"] == "c" * 64
    assert row["evidence_class"] == wf.EVIDENCE_CLASS_HISTORICAL_OOS
    assert row["process_label"] == wf.PROCESS_LABEL_RULE
    assert row["outcome_basis"] == "mid"
    assert row["n"] == 3
    assert row["n_sessions"] == 1
    assert row["n_symbols"] == 1
    assert row["effect"] == pytest.approx(10.0)
    assert row["sign"] == "positive"
    assert row["econ_floor"] == _ECON_FLOOR
    assert row["registered_direction"] == "long"
    assert row["rule_id"] == sealed_eval.SEALED_PASS_RULE_V1
    assert row["rule_version"] == sealed_eval.SEALED_PASS_RULE_VERSION
    assert row["rule_hash"] == sealed_eval.sealed_pass_rule_hash()
    assert row["evaluated_at"] == _EVALUATED_AT
    assert row["observed_through"] is not None  # a genuine, real accessor read happened
    assert "row_hash" in row  # step 7: the id+hash a transition needs

    # persisted permanently, readable back via the single source of truth.
    persisted = g.sealed_evaluations_for_family(grad_ledger, family_root_id)
    assert len(persisted) == 1
    assert persisted[0]["dataset_id"] == dataset_meta["id"]


# === step 1/3 (migrated from test_micro_graduation.py -- this refusal moved here with the vault
# confirmation itself): a shard exposed to a DIFFERENT family is refused, never trusted ===============


def test_a_shard_exposed_to_a_different_family_is_refused(tmp_path):
    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
    family_root_id = _family_root_id("wrong-family")
    other_family_root_id = _family_root_id("the-actual-owner")
    # the shard is exposed, but to a DIFFERENT family entirely.
    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=other_family_root_id, dataset_id=dataset_meta["id"])
    candidate_spec = _candidate_spec(family_root_id=family_root_id)
    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))

    with pytest.raises(sealed_eval.SealedEvaluationRefusedError, match="not an EXPOSED vault shard"):
        sealed_eval.evaluate_sealed_verdict(
            grad_ledger, shard_ledger, universe_ledger, accessor,
            candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
            observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
        )
    assert g.sealed_evaluations_for_family(grad_ledger, family_root_id) == []


def test_a_spec_registered_after_shard_assignment_is_refused(tmp_path):
    """Step 1's OTHER half: "frozen BEFORE that assignment" -- a candidate spec whose own
    ``registered_at`` is AFTER the shard's own ``assigned_at`` is refused, never evaluated."""
    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
    family_root_id = _family_root_id("late-registration")
    shard_ledger, universe_ledger = _exposed_shard_for(
        tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"], assigned_at=_ASSIGNED_AT,
    )
    late_spec = _candidate_spec(family_root_id=family_root_id, registered_at="2026-06-01T00:00:00.000000Z")  # AFTER _ASSIGNED_AT
    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))

    with pytest.raises(sealed_eval.SealedEvaluationRefusedError, match="STRICTLY BEFORE"):
        sealed_eval.evaluate_sealed_verdict(
            grad_ledger, shard_ledger, universe_ledger, accessor,
            candidate_spec=late_spec, dataset_id=dataset_meta["id"],
            observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
        )
    assert g.sealed_evaluations_for_family(grad_ledger, family_root_id) == []


# === TC-3: a rule changed (or never registered) after assignment fails CLOSED, never a pass ===========


def test_tc3_a_rule_identity_mismatch_fails_closed_and_persists_nothing(tmp_path):
    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
    family_root_id = _family_root_id("tc3")
    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
    candidate_spec = _candidate_spec(family_root_id=family_root_id, rule_hash="a-stale-or-never-registered-rule-hash")
    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))

    with pytest.raises(sealed_eval.SealedEvaluationRefusedError, match="rule-identity|condition 4"):
        sealed_eval.evaluate_sealed_verdict(
            grad_ledger, shard_ledger, universe_ledger, accessor,
            candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
            observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
        )
    # never a pass, never ANY verdict -- no artifact persisted at all.
    assert g.sealed_evaluations_for_family(grad_ledger, family_root_id) == []


# === TC-4: re-running on identical inputs yields a byte-identical artifact and verdict =================


def test_tc4_rerunning_on_identical_inputs_is_byte_identical(tmp_path):
    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
    family_root_id = _family_root_id("tc4")
    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
    candidate_spec = _candidate_spec(family_root_id=family_root_id)
    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))

    first = sealed_eval.evaluate_sealed_verdict(
        grad_ledger, shard_ledger, universe_ledger, accessor,
        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
        observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
    )
    assert first["transition"] == g.TRANSITION_APPENDED

    second = sealed_eval.evaluate_sealed_verdict(
        grad_ledger, shard_ledger, universe_ledger, accessor,
        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
        observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
    )
    assert second["transition"] == g.TRANSITION_REPLAYED
    assert second["row"] == first["row"]
    assert len(g.sealed_evaluations_for_family(grad_ledger, family_root_id)) == 1  # never a duplicate row


# === TC-5: a second, DIFFERENT evaluation attempt for the SAME pair is refused, never a second draw ===


def test_tc5_a_second_different_evaluation_attempt_is_refused(tmp_path):
    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
    family_root_id = _family_root_id("tc5")
    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
    candidate_spec = _candidate_spec(family_root_id=family_root_id)
    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))

    first = sealed_eval.evaluate_sealed_verdict(
        grad_ledger, shard_ledger, universe_ledger, accessor,
        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
        observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
    )
    assert first["row"]["verdict"] == sealed_eval.SEALED_VERDICT_PASS

    # A genuinely DIFFERENT re-evaluation attempt (different observations -> a different recomputed
    # effect, a different verdict) for the identical (family_root_id, dataset_id) pair.
    with pytest.raises(g.GraduationTransitionRefusedError, match="never a second draw"):
        sealed_eval.evaluate_sealed_verdict(
            grad_ledger, shard_ledger, universe_ledger, accessor,
            candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
            observations=_below_floor_observations(), evaluated_at="2026-06-11T00:00:00.000000Z",
        )
    # still exactly the FIRST verdict on permanent record -- never overwritten.
    persisted = g.sealed_evaluations_for_family(grad_ledger, family_root_id)
    assert len(persisted) == 1
    assert persisted[0]["verdict"] == sealed_eval.SEALED_VERDICT_PASS


# === TC-6: below any per-fold floor -> insufficient, distinct from FAIL, single shot still consumed ===


def test_tc6_below_floor_observations_verdict_is_insufficient_and_consumes_the_single_shot(tmp_path):
    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
    family_root_id = _family_root_id("tc6")
    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
    candidate_spec = _candidate_spec(family_root_id=family_root_id)
    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))

    result = sealed_eval.evaluate_sealed_verdict(
        grad_ledger, shard_ledger, universe_ledger, accessor,
        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
        observations=_insufficient_observations(), evaluated_at=_EVALUATED_AT,
    )
    row = result["row"]
    assert row["verdict"] == sealed_eval.SEALED_VERDICT_INSUFFICIENT
    assert row["verdict"] != sealed_eval.SEALED_VERDICT_PASS
    assert row["verdict"] != sealed_eval.SEALED_VERDICT_FAIL  # tri-state -- never coerced to a boolean
    assert row["failure_reason"] is None
    assert row["missing"]  # the exact arithmetic (e.g. "2 < 3") is carried, never silently dropped

    # the single evaluation shot was genuinely consumed (the shard WAS exposed) -- a second attempt,
    # even with now-sufficient observations, is refused, never a second draw.
    with pytest.raises(g.GraduationTransitionRefusedError, match="never a second draw"):
        sealed_eval.evaluate_sealed_verdict(
            grad_ledger, shard_ledger, universe_ledger, accessor,
            candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
            observations=_passing_observations(), evaluated_at="2026-06-11T00:00:00.000000Z",
        )


# === TC-7: a permanent FAILED verdict travels in every later export bundle =============================


def test_tc7_a_failed_verdict_travels_permanently_in_the_export_bundle(tmp_path):
    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
    family_root_id = _family_root_id("tc7")
    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
    candidate_spec = _candidate_spec(family_root_id=family_root_id)
    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))

    result = sealed_eval.evaluate_sealed_verdict(
        grad_ledger, shard_ledger, universe_ledger, accessor,
        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
        observations=_below_floor_observations(), evaluated_at=_EVALUATED_AT,
    )
    assert result["row"]["verdict"] == sealed_eval.SEALED_VERDICT_FAIL
    assert result["row"]["failure_reason"] == "below_economic_floor"

    from app.research.scout_ledger import ScoutLedger
    from app.research import walkforward_ledger as wl
    scout = ScoutLedger(str(tmp_path / "scout"))
    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    bundle = g.build_export_bundle(
        grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
        family_root_id=family_root_id, handoff_created_at="2026-06-12T00:00:00.000000Z",
    )
    failed = [e for e in bundle["sealed_evaluations"] if e["verdict"] == sealed_eval.SEALED_VERDICT_FAIL]
    assert len(failed) == 1
    assert failed[0]["dataset_id"] == dataset_meta["id"]
    assert bundle["family_multiplicity"]["prior_sealed_verdicts"] == bundle["sealed_evaluations"]


# === TC-8 (mutation evidence): a deliberately weakened _derive_verdict makes the corrected assertion
# fail, naming the specific wrong verdict; restoring makes it pass again. ==============================


def test_tc8_weakening_the_economic_floor_condition_makes_the_below_floor_case_wrongly_pass(monkeypatch, tmp_path):
    """The established, already-praised pattern (``test_micro_observer.py``'s TR-26 fix,
    ``test_tc12_tr26_reverting_the_fix_makes_the_corrected_assertion_fail_restoring_it_passes``),
    mirrored exactly: ``monkeypatch.setattr`` installs a deliberately-weakened ``_derive_verdict``
    that DROPS the magnitude condition entirely (treats ANY correctly-signed effect as clearing the
    floor, regardless of size) -- proves the SPECIFIC wrong verdict (``"pass"``) the corrupted code
    produces on a fixture that should FAIL, then ``monkeypatch.undo()`` restores the correct
    (``"fail"``) verdict on the identical fixture."""
    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
    family_root_id = _family_root_id("tc8")
    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
    candidate_spec = _candidate_spec(family_root_id=family_root_id)
    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))

    def _weakened_derive_verdict(summary, *, sidedness, econ_floor, evidence_class, process_label):
        # BUG: the magnitude condition (condition 3) is dropped entirely -- ANY correctly-signed
        # effect, however small, is treated as clearing the economic floor.
        if summary["status"] != wf.FOLD_STATUS_SUFFICIENT:
            return sealed_eval.SEALED_VERDICT_INSUFFICIENT, None, {"sufficient_observations": False}
        expected_sign = "positive" if sidedness == "long" else "negative"
        if summary["sign"] == expected_sign:
            return sealed_eval.SEALED_VERDICT_PASS, None, {"registered_direction": True}
        return sealed_eval.SEALED_VERDICT_FAIL, "wrong_direction", {"registered_direction": False}

    monkeypatch.setattr(sealed_eval, "_derive_verdict", _weakened_derive_verdict)
    corrupted = sealed_eval.evaluate_sealed_verdict(
        grad_ledger, shard_ledger, universe_ledger, accessor,
        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
        observations=_below_floor_observations(), evaluated_at=_EVALUATED_AT,
    )
    # The exact wrong value the weakened code produces -- a below-floor case that should FAIL is
    # instead recorded as a PASS. Proves the corrected assertion (verdict == "fail") WOULD fail
    # against this weakened code.
    assert corrupted["row"]["verdict"] == sealed_eval.SEALED_VERDICT_PASS
    assert corrupted["row"]["verdict"] != sealed_eval.SEALED_VERDICT_FAIL

    monkeypatch.undo()
    dataset_store2, snapshots_dir2, dataset_meta2 = _rig(tmp_path / "restored")
    family_root_id2 = _family_root_id("tc8-restored")
    shard_ledger2, universe_ledger2 = _exposed_shard_for(tmp_path / "restored", family_root_id=family_root_id2, dataset_id=dataset_meta2["id"])
    candidate_spec2 = _candidate_spec(family_root_id=family_root_id2)
    accessor2 = MicroAccessor(dataset_store2, snapshots_dir2, CONFIG, origin=None)
    grad_ledger2 = g.GraduationLedger(str(tmp_path / "restored" / "grad"))
    restored = sealed_eval.evaluate_sealed_verdict(
        grad_ledger2, shard_ledger2, universe_ledger2, accessor2,
        candidate_spec=candidate_spec2, dataset_id=dataset_meta2["id"],
        observations=_below_floor_observations(), evaluated_at=_EVALUATED_AT,
    )
    assert restored["row"]["verdict"] == sealed_eval.SEALED_VERDICT_FAIL
    assert restored["row"]["failure_reason"] == "below_economic_floor"


# === TC-9 (fixture discrimination): correct vs corrupted recomputed effects are DIFFERENT numbers,
# never coincidentally equal -- and they produce DIFFERENT verdicts. ====================================


def test_tc9_the_correct_and_corrupted_recomputed_effects_are_different_numbers_and_verdicts(tmp_path):
    """Run BOTH fixtures through the REAL, unmutated ``_derive_verdict`` (via ``summarize_fold_
    observations``, the SAME canonical statistical core the production evaluator itself consults):
    ``_passing_observations()`` recomputes to effect=10.0 (clears the 5.0 bps floor -> PASS);
    ``_below_floor_observations()`` recomputes to effect=1.0 (correct direction, below floor ->
    FAIL). 10.0 != 1.0 -- the two paths' own recomputed numbers are never coincidentally equal, so
    this assertion cannot pass for the wrong reason (iteration-16's own named lesson)."""
    floors = _TINY_FLOORS
    passing_summary = wf.summarize_fold_observations(_passing_observations(), floors)
    below_floor_summary = wf.summarize_fold_observations(_below_floor_observations(), floors)

    assert passing_summary["effect"] == pytest.approx(10.0)
    assert below_floor_summary["effect"] == pytest.approx(1.0)
    assert passing_summary["effect"] != pytest.approx(below_floor_summary["effect"])  # never coincidentally equal

    pass_verdict, _, _ = sealed_eval._derive_verdict(
        passing_summary, sidedness="long", econ_floor=_ECON_FLOOR,
        evidence_class=wf.EVIDENCE_CLASS_HISTORICAL_OOS, process_label=wf.PROCESS_LABEL_RULE,
    )
    fail_verdict, fail_reason, _ = sealed_eval._derive_verdict(
        below_floor_summary, sidedness="long", econ_floor=_ECON_FLOOR,
        evidence_class=wf.EVIDENCE_CLASS_HISTORICAL_OOS, process_label=wf.PROCESS_LABEL_RULE,
    )
    assert pass_verdict == sealed_eval.SEALED_VERDICT_PASS
    assert fail_verdict == sealed_eval.SEALED_VERDICT_FAIL
    assert fail_reason == "below_economic_floor"
    assert fail_reason in sealed_eval.SEALED_FAIL_REASONS  # the closed vocabulary, never free text
    assert pass_verdict != fail_verdict  # the two DIFFERENT recomputed numbers drive DIFFERENT verdicts


def test_every_fail_reason_derive_verdict_can_produce_is_in_the_closed_vocabulary():
    """``SEALED_FAIL_REASONS`` is a documented closed set (the ``scout.KILL_REASONS`` convention)
    -- this proves it is not merely decorative by exercising all three FAIL branches of
    ``_derive_verdict`` directly and checking each one lands inside the tuple."""
    sufficient = {"status": wf.FOLD_STATUS_SUFFICIENT, "n": 3, "n_sessions": 1, "n_symbols": 1, "missing": {}}

    wrong_direction, reason1, _ = sealed_eval._derive_verdict(
        {**sufficient, "effect": -10.0, "sign": "negative"}, sidedness="long", econ_floor=_ECON_FLOOR,
        evidence_class=wf.EVIDENCE_CLASS_HISTORICAL_OOS, process_label=wf.PROCESS_LABEL_RULE,
    )
    below_floor, reason2, _ = sealed_eval._derive_verdict(
        {**sufficient, "effect": 1.0, "sign": "positive"}, sidedness="long", econ_floor=_ECON_FLOOR,
        evidence_class=wf.EVIDENCE_CLASS_HISTORICAL_OOS, process_label=wf.PROCESS_LABEL_RULE,
    )
    wrong_class, reason3, _ = sealed_eval._derive_verdict(
        {**sufficient, "effect": 10.0, "sign": "positive"}, sidedness="long", econ_floor=_ECON_FLOOR,
        evidence_class=wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC, process_label=wf.PROCESS_LABEL_RULE,
    )
    assert wrong_direction == below_floor == wrong_class == sealed_eval.SEALED_VERDICT_FAIL
    assert {reason1, reason2, reason3} == set(sealed_eval.SEALED_FAIL_REASONS)  # all three, each exactly once


# === error cases named in TESTING REQUIREMENTS: an insufficient verdict never silently coerced =========


def test_insufficient_verdict_is_never_coerced_to_fail_or_pass_in_the_graduation_transition(tmp_path):
    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
    family_root_id = _family_root_id("insufficient-coercion")
    corpus_id = "graduation-fixture-corpus-insufficient"
    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
    from app.research import walkforward_ledger as wl
    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
    for i in range(3):
        wl.append_fold_result(wf_ledger, {
            "sequence_id": sequence_id, "corpus_id": corpus_id, "mode": "B", "rule_id": "fixture-rule",
            "spec_hash": "spec-fixture-hash-1", "fold_index": i, "sidedness": "long",
            "econ_floor": _ECON_FLOOR, "evidence_class": wf.EVIDENCE_CLASS_HISTORICAL_OOS,
            "process_label": wf.PROCESS_LABEL_RULE, "registered_at": "2026-01-01T00:00:00.000000Z",
            "status": wf.FOLD_STATUS_SUFFICIENT, "n": 40, "n_sessions": 10, "n_symbols": 3,
            "effect": 10.0, "sign": "positive", "missing": {},
        })
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
    g.evaluate_walkforward_survivor_transition(grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id)

    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
    candidate_spec = _candidate_spec(family_root_id=family_root_id)
    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
    result = sealed_eval.evaluate_sealed_verdict(
        grad_ledger, shard_ledger, universe_ledger, accessor,
        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
        observations=_insufficient_observations(), evaluated_at=_EVALUATED_AT,
    )
    assert result["row"]["verdict"] == sealed_eval.SEALED_VERDICT_INSUFFICIENT

    with pytest.raises(g.GraduationTransitionRefusedError, match='not "pass"'):
        g.evaluate_sealed_survivor_transition(grad_ledger, family_root_id=family_root_id, dataset_id=dataset_meta["id"])


# === iteration-17 AUDIT finding B1: the floors condition 1 ACTUALLY applied are on the artifact ========


def test_the_artifact_records_the_floors_condition_1_actually_applied(tmp_path):
    """spec section 8.1 requires the evaluation artifact to be "sufficient to reproduce the
    verdict". Condition 1 is decided by ``summarize_fold_observations``'s RESOLVED floors, which a
    candidate spec may NARROW below the section-1 constants ``sealed_pass_rule_hash()`` embeds --
    so the floors actually applied are recorded verbatim and a narrowed floor can never be silent
    in a permanent verdict (see the module docstring's own T-1 disclosure; owner-owed)."""
    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
    family_root_id = _family_root_id("floors-applied")
    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
    candidate_spec = _candidate_spec(family_root_id=family_root_id)  # carries _TINY_FLOORS
    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))

    row = sealed_eval.evaluate_sealed_verdict(
        grad_ledger, shard_ledger, universe_ledger, accessor,
        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
        observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
    )["row"]

    assert row["verdict"] == sealed_eval.SEALED_VERDICT_PASS
    # the RESOLVED triple this verdict was actually decided under -- the fixture's NARROWED floors.
    assert row["floors_applied"] == {
        "wf_fold_min_observations": 3, "wf_fold_min_signal_sessions": 1, "wf_fold_min_symbols": 1,
    }
    section_1_pinned = {
        "wf_fold_min_observations": wf.WF_FOLD_MIN_OBSERVATIONS,
        "wf_fold_min_signal_sessions": wf.WF_FOLD_MIN_SIGNAL_SESSIONS,
        "wf_fold_min_symbols": wf.WF_FOLD_MIN_SYMBOLS,
    }
    # 3/1/1 vs 30/8/2 -- deliberately different numbers, so the narrowing is VISIBLE on the
    # permanent record even though `rule_hash` (condition 4's identity check) pins section 1.
    assert row["floors_applied"] != section_1_pinned
    assert row["rule_hash"] == sealed_eval.sealed_pass_rule_hash()
    # a spec carrying NO override resolves to the section-1 constants verbatim.
    assert sealed_eval._resolved_floors({}) == section_1_pinned
    assert sealed_eval._resolved_floors({"floors": {"wf_fold_min_symbols": 5}})["wf_fold_min_symbols"] == 5


# === guard: no threshold-sweep loop in this new module (goal.md Constraints: "new micro modules add
# their own guards") =====================================================================================

_SWEEP_OVER_NAMED_CONSTANT = re.compile(r"for\s+\w+(?:\s*,\s*\w+)*\s+in\s+[^\n:]*(?:WF_|SCOUT_|MICRO_|SEALED_)[A-Z_]*_CANDIDATES\b")
_SWEEP_OVER_LITERAL_SEQUENCE = re.compile(r"for\s+\w+\s+in\s+[\(\[]\s*-?\d+(?:\.\d+)?\s*(?:,\s*-?\d+(?:\.\d+)?\s*){1,}[\)\]]")


def _strip_comments_and_docstrings(source: str) -> str:
    without_triple_double = re.sub(r'"""(?:.|\n)*?"""', "", source)
    without_triple_single = re.sub(r"'''(?:.|\n)*?'''", "", without_triple_double)
    return re.sub(r"#[^\n]*", "", without_triple_single)


def test_micro_sealed_evaluation_contains_no_threshold_sweep_loop():
    source = _strip_comments_and_docstrings(open(sealed_eval.__file__, encoding="utf-8").read())
    named_hits = _SWEEP_OVER_NAMED_CONSTANT.findall(source)
    literal_hits = _SWEEP_OVER_LITERAL_SEQUENCE.findall(source)
    assert not named_hits, f"micro_sealed_evaluation.py sweeps a named threshold-candidate constant: {named_hits}"
    assert not literal_hits, f"micro_sealed_evaluation.py sweeps a literal numeric candidate sequence: {literal_hits}"


def test_no_threshold_sweep_guard_can_fail_on_seeded_violations():
    """The lint CAN fail -- a lint that cannot fail proves nothing (the ``test_copy_discipline.py``
    precedent)."""
    seeded_named = "for candidate in SEALED_FIXTURE_THRESHOLD_CANDIDATES:\n    pass\n"
    assert _SWEEP_OVER_NAMED_CONSTANT.search(seeded_named) is not None
    seeded_literal = "for mult in [0.5, 1.0, 1.5]:\n    pass\n"
    assert _SWEEP_OVER_LITERAL_SEQUENCE.search(seeded_literal) is not None


# === TC-15 (this file's half): the accessor requires origin=None, never a fenced accessor ==============


def test_the_evaluator_refuses_a_fenced_accessor(tmp_path):
    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
    family_root_id = _family_root_id("fenced-refusal")
    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
    candidate_spec = _candidate_spec(family_root_id=family_root_id)
    fenced_accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin="2000-01-01")  # absurdly early -- would also origin-fence-error
    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))

    with pytest.raises(sealed_eval.SealedEvaluationRefusedError, match="UNFENCED"):
        sealed_eval.evaluate_sealed_verdict(
            grad_ledger, shard_ledger, universe_ledger, fenced_accessor,
            candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
            observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
        )
