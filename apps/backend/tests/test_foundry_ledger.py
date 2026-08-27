"""``foundry_ledger.py`` (goal-hypothesis-foundry-iter-2, J-04): the hash-chained append-only
Foundry trial ledger (spec §4.2.1/§9.2). TC-14 (ledger-level parts)/TC-18/TC-19 in
``docs/phases/goal-hypothesis-foundry-iter-2.md``."""

from __future__ import annotations

import pytest

from app.research import foundry_ledger as fl


def _screen(decision="survive", effect_bps=42.0, p_screen=0.01):
    return {
        "decision": decision, "reason": decision, "notes": "x",
        "screen_result": {"effect_bps": effect_bps, "p_screen": p_screen, "n_candidate": 20, "n_comparator": 20},
    }


def test_ledger_starts_empty_and_verifies_clean(tmp_path):
    ledger = fl.FoundryLedger(tmp_path)
    assert ledger.all_rows() == []
    assert ledger.verify_chain()["ok"] is True


def test_intent_then_terminal_round_trip(tmp_path):
    ledger = fl.FoundryLedger(tmp_path)
    intent = ledger.record_intent(
        candidate_spec_hash="h1", manifest_hash="m1", econ_floor_bps=1.5, econ_floor_provenance="scout_quoted_spread_floor",
    )
    assert intent["row_kind"] == fl.ROW_KIND_INTENT
    assert ledger.intent_row_for("h1") is not None
    assert ledger.terminal_row_for("h1") is None

    terminal = ledger.record_terminal(
        candidate_spec_hash="h1", manifest_hash="m1", foundry_family_id="family:x",
        foundry_family_variant_count=3, screen_result=_screen(), rule_id="foundry:epoch:h1",
        prospective_root_status="family:x", foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
    )
    assert terminal["row_kind"] == fl.ROW_KIND_TERMINAL
    assert ledger.terminal_row_for("h1") == terminal
    assert ledger.verify_chain()["ok"] is True


def test_tc18_terminal_row_embeds_the_complete_screen_payload_and_frozen_hashes():
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        ledger = fl.FoundryLedger(d)
        ledger.record_intent(candidate_spec_hash="h2", manifest_hash="m1", econ_floor_bps=0.0, econ_floor_provenance="p")
        screen = _screen(decision="killed_null", effect_bps=1.0, p_screen=0.5)
        row = ledger.record_terminal(
            candidate_spec_hash="h2", manifest_hash="m1", foundry_family_id="family:y",
            foundry_family_variant_count=1, screen_result=screen, rule_id="foundry:epoch:h2",
            prospective_root_status="root_deferred_composite", foundry_state="EVALUATED_KILLED",
        )
        assert row["screen_result"] == screen
        assert row["candidate_spec_hash"] == "h2"
        assert row["manifest_hash"] == "m1"
        assert row["foundry_family_id"] == "family:y"
        assert row["foundry_family_variant_count"] == 1
        # This is the ONLY place the trial is ever recorded -- no Scout-ledger row is written by
        # anything in this module (it never imports/touches `scout_ledger.py`).
        assert "scout_ledger" not in dir(fl)


def test_tc14_idempotent_exact_duplicate_terminal_replay_returns_existing_row(tmp_path):
    ledger = fl.FoundryLedger(tmp_path)
    ledger.record_intent(candidate_spec_hash="h3", manifest_hash="m1", econ_floor_bps=0.0, econ_floor_provenance="p")
    screen = _screen()
    first = ledger.record_terminal(
        candidate_spec_hash="h3", manifest_hash="m1", foundry_family_id="family:z",
        foundry_family_variant_count=2, screen_result=screen, rule_id="foundry:epoch:h3",
        prospective_root_status="family:z", foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
    )
    second = ledger.record_terminal(
        candidate_spec_hash="h3", manifest_hash="m1", foundry_family_id="family:z",
        foundry_family_variant_count=2, screen_result=screen, rule_id="foundry:epoch:h3",
        prospective_root_status="family:z", foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
    )
    assert first == second
    assert len(ledger.all_rows()) == 2  # one intent + one terminal, never a duplicate terminal


def test_tc14_conflicting_replay_is_refused(tmp_path):
    ledger = fl.FoundryLedger(tmp_path)
    ledger.record_intent(candidate_spec_hash="h4", manifest_hash="m1", econ_floor_bps=0.0, econ_floor_provenance="p")
    ledger.record_terminal(
        candidate_spec_hash="h4", manifest_hash="m1", foundry_family_id="family:c",
        foundry_family_variant_count=1, screen_result=_screen(decision="killed_null"), rule_id="foundry:epoch:h4",
        prospective_root_status="family:c", foundry_state="EVALUATED_KILLED",
    )
    with pytest.raises(fl.ConflictingReplayRefused):
        ledger.record_terminal(
            candidate_spec_hash="h4", manifest_hash="m1", foundry_family_id="family:c",
            foundry_family_variant_count=1, screen_result=_screen(decision="survive"), rule_id="foundry:epoch:h4",
            prospective_root_status="family:c", foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
        )


def test_tc19_deterministic_rule_id_and_cannot_be_renamed(tmp_path):
    assert fl.deterministic_rule_id("epoch:abc", "spechash123") == "foundry:epoch:abc:spechash123"

    ledger = fl.FoundryLedger(tmp_path)
    ledger.record_intent(candidate_spec_hash="h5", manifest_hash="m1", econ_floor_bps=0.0, econ_floor_provenance="p")
    rule_id = fl.deterministic_rule_id("epoch:e1", "h5")
    row = ledger.record_terminal(
        candidate_spec_hash="h5", manifest_hash="m1", foundry_family_id="family:d",
        foundry_family_variant_count=1, screen_result=_screen(), rule_id=rule_id,
        prospective_root_status="family:d", foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
    )
    assert row["rule_id"] == "foundry:epoch:e1:h5"

    # Replaying with a DIFFERENT rule_id for the same candidate_spec_hash is a conflicting replay,
    # never a silent rename.
    with pytest.raises(fl.ConflictingReplayRefused):
        ledger.record_terminal(
            candidate_spec_hash="h5", manifest_hash="m1", foundry_family_id="family:d",
            foundry_family_variant_count=1, screen_result=_screen(), rule_id="foundry:epoch:e1:RENAMED",
            prospective_root_status="family:d", foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
        )


# === goal-hypothesis-foundry-iter-6 (J-07): the epoch-opening / first-read-lock row -- §8.5 ======


def _epoch_open_kwargs(**overrides):
    kwargs = dict(
        epoch_id="epoch:fixture-e1", freeze_commit="fixture-commit-abc",
        manifest_hash="fixture-manifest-hash", source_registry_hash="fixture-source-registry-hash",
        spec_hash="fixture-spec-hash", candidate_spec_schema_hash="fixture-schema-hash",
        compiler_hash="fixture-compiler-hash", interpreter_hash="fixture-interpreter-hash",
        runner_hash="fixture-runner-hash", scout_screen_source_hash="fixture-scout-screen-hash",
        config_fingerprint="fixture-config-fingerprint", freeze_set_hash="fixture-freeze-set-hash",
        era_open_evidence_class_contract="historical_exposed_diagnostic",
        eligible_corpus_manifest_hash="fixture-eligible-corpus-manifest-hash",
    )
    kwargs.update(overrides)
    return kwargs


def test_epoch_open_row_round_trips(tmp_path):
    ledger = fl.FoundryLedger(tmp_path)
    assert ledger.epoch_open_row() is None  # honest pre-lock state

    row = ledger.record_epoch_open(**_epoch_open_kwargs())
    assert row["row_kind"] == fl.ROW_KIND_EPOCH_OPEN
    assert row["epoch_id"] == "epoch:fixture-e1"
    assert row["eligible_corpus_manifest_hash"] == "fixture-eligible-corpus-manifest-hash"
    assert ledger.epoch_open_row() == row
    assert ledger.verify_chain()["ok"] is True


def test_epoch_open_row_replay_is_idempotent_no_second_row_appended(tmp_path):
    ledger = fl.FoundryLedger(tmp_path)
    first = ledger.record_epoch_open(**_epoch_open_kwargs())
    second = ledger.record_epoch_open(**_epoch_open_kwargs())
    assert first == second
    epoch_open_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_EPOCH_OPEN]
    assert len(epoch_open_rows) == 1  # never a duplicate first-read-lock row


def test_epoch_open_row_conflicting_replay_is_refused(tmp_path):
    ledger = fl.FoundryLedger(tmp_path)
    ledger.record_epoch_open(**_epoch_open_kwargs())
    with pytest.raises(fl.ConflictingReplayRefused):
        ledger.record_epoch_open(**_epoch_open_kwargs(eligible_corpus_manifest_hash="DIFFERENT"))
    # the refused attempt appended nothing
    epoch_open_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_EPOCH_OPEN]
    assert len(epoch_open_rows) == 1


def test_tc19_prospective_root_status_scalar_vs_composite():
    from app.research import foundry_compiler as fc

    scalar_spec = fc.CandidateSpec(
        foundry_spec_version="v1", epoch_id="epoch:e1", source_ids=("s1",), lineage_id="s1",
        foundry_family_id="family:scalar", variant_id="family:scalar:0", variant_ordinal=0,
        population=fc.CandidatePopulation(structure_context_kind="none", side_filter=None, setup_context_id=None),
        coordinates=(
            fc.CandidateCoordinate(
                feature_construct_id="q", semantic_role="candidate_signal", transform_orientation="ge",
                threshold_corner_predicate="q >= 1", threshold_provenance="natural_semantic_boundary",
                aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
            ),
        ),
        relation=fc.CandidateRelation(kind="direct_scalar_membership"), membership_corner="q >= 1",
        outcome=fc.CandidateOutcome(horizon_key="trades_20", sidedness="long"),
        economic_floor_rule=fc.EconomicFloorRule(), foundry_family_variant_count=1,
    ).with_hash()
    assert fl.prospective_root_status(scalar_spec) == "family:scalar"

    composite_spec = fc.CandidateSpec(
        foundry_spec_version="v1", epoch_id="epoch:e1", source_ids=("s2",), lineage_id="s2",
        foundry_family_id="family:composite", variant_id="family:composite:0", variant_ordinal=0,
        population=fc.CandidatePopulation(structure_context_kind="none", side_filter=None, setup_context_id=None),
        coordinates=(
            fc.CandidateCoordinate(
                feature_construct_id="c1", semantic_role="candidate_signal", transform_orientation="gt",
                threshold_corner_predicate="c1 > 0", threshold_provenance="natural_semantic_boundary",
                aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
            ),
            fc.CandidateCoordinate(
                feature_construct_id="c2", semantic_role="candidate_signal", transform_orientation="gt",
                threshold_corner_predicate="c2 > 0", threshold_provenance="natural_semantic_boundary",
                aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
            ),
        ),
        relation=fc.CandidateRelation(kind="conjunction"), membership_corner="c1 > 0 and c2 > 0",
        outcome=fc.CandidateOutcome(horizon_key="trades_20", sidedness="long"),
        economic_floor_rule=fc.EconomicFloorRule(), foundry_family_variant_count=1,
    ).with_hash()
    assert fl.prospective_root_status(composite_spec) == fl.ROOT_DEFERRED_COMPOSITE == "root_deferred_composite"
