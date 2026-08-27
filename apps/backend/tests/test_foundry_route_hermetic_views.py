"""``GET /research/desk/micro/foundry``'s four consolidated read-surface subviews
(goal-hypothesis-foundry-iter-4, J-02/J-03/J-04/J-05): ``sources_compiler``, ``interpreter_
fixtures``, ``freeze_integrity``, ``hermetic_oracles``. Test-first contract: TC-1 through TC-15 and
TC-19 in ``docs/phases/goal-hypothesis-foundry-iter-4.md`` (TC-16/TC-17 -- the two carried repairs
-- live in ``test_foundry_source_registry.py``/``test_foundry_compiler.py``/
``test_foundry_runner.py``; TC-18 is a browser-only check, covered by the browser-qa lane)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.research import foundry_compiler as fc
from app.research import foundry_freeze as fz
from app.research import foundry_source_registry as fsr


def _foundry_body() -> dict:
    with TestClient(app) as client:
        response = client.get("/research/desk/micro/foundry")
    assert response.status_code == 200
    return response.json()


# === sources_compiler (J-02): TC-1, TC-2, TC-3 ======================================================


def test_tc1_sources_compiler_has_exactly_eight_entries_matching_the_registry_dispositions():
    """goal-hypothesis-foundry-iter-5: the count changed from 7 to 8 -- both alias-family sibling
    records (`fixture-variant-a`/`fixture-variant-b`) now each surface as their own entry, per two
    consecutive evaluator verdicts asking to show both records of the two-variant family (J-02
    step 2's own plain text: "two explicitly-frozen legal variants", plural)."""
    body = _foundry_body()
    fixtures = body["sources_compiler"]["fixtures"]
    assert len(fixtures) == 8
    expected = {
        "fixture-natural-boundary": fsr.DISPOSITION_COMPILED,
        "fixture-variant-a": fsr.DISPOSITION_COMPILED,
        "fixture-variant-b": fsr.DISPOSITION_COMPILED,
        "fixture-magnitude-word": fsr.DISPOSITION_BLOCKED_SPEC_GAP,
        "fixture-proxy": fsr.DISPOSITION_ALIASED_PROXY_ONLY,
        "fixture-unsupported-stat": fsr.DISPOSITION_BLOCKED_UNSUPPORTED_STUDY_FORM,
        "fixture-alias-older": fsr.DISPOSITION_ALIASED_VARIANT_VOCABULARY,
        "fixture-directionless": fsr.DISPOSITION_BLOCKED_DIRECTION,
    }
    by_id = {f["source_id"]: f for f in fixtures}
    assert set(by_id) == set(expected)
    for source_id, disposition in expected.items():
        assert by_id[source_id]["disposition"] == disposition
    # each entry carries the full §1.4 field set plus disposition/candidate_spec/block_reason.
    for entry in fixtures:
        for field in (
            "source_id", "source_path", "section_ref", "quoted_spans", "source_excerpt",
            "mechanism_statement", "operative_formula_refs", "direction_derivation",
            "comparator_derivation", "threshold_provenance", "alternatives", "disposition",
            "candidate_spec", "block_reason",
        ):
            assert field in entry


def test_iter5_both_alias_family_siblings_visible_with_full_field_set():
    """TC-11: both `fixture-variant-a` and `fixture-variant-b` appear as their own visible record
    rows, each showing its `operative_formula_refs`, `superseded_fields`, and
    `aliases_lineage_ids` values, and each other's id in `alternatives`."""
    body = _foundry_body()
    by_id = {f["source_id"]: f for f in body["sources_compiler"]["fixtures"]}
    variant_a = by_id["fixture-variant-a"]
    variant_b = by_id["fixture-variant-b"]
    assert variant_a["operative_formula_refs"] == ["cumulative_delta"]
    assert variant_b["operative_formula_refs"] == ["cumulative_delta"]
    assert variant_a["alternatives"] == ["fixture-variant-b"]
    assert variant_b["alternatives"] == ["fixture-variant-a"]
    assert variant_a["candidate_spec"] is not None and variant_b["candidate_spec"] is not None
    assert variant_a["candidate_spec"]["foundry_family_variant_count"] == 2
    assert variant_b["candidate_spec"]["foundry_family_variant_count"] == 2
    for field in ("superseded_fields", "aliases_lineage_ids"):
        assert field in variant_a and field in variant_b


def test_iter5_every_sources_compiler_fixture_shows_the_three_additive_fields_with_explicit_empty_states():
    """TC-12: every fixture record shows `operative_formula_refs`/`superseded_fields`/
    `aliases_lineage_ids`, with an empty array/object rendered as an explicit empty state rather
    than omitted -- verified at the API layer (an empty list/dict is present as `[]`/`{}`, not a
    missing key) since the frontend renders whatever this response serves verbatim."""
    body = _foundry_body()
    for fixture in body["sources_compiler"]["fixtures"]:
        for field in ("operative_formula_refs", "superseded_fields", "aliases_lineage_ids"):
            assert field in fixture, f"{fixture['source_id']} missing {field}"
            assert fixture[field] is not None, f"{fixture['source_id']}.{field} is None, not an explicit empty value"


def test_tc2_natural_boundary_candidate_spec_every_science_field_populated_and_hash_reproducible():
    body = _foundry_body()
    entry = next(f for f in body["sources_compiler"]["fixtures"] if f["source_id"] == "fixture-natural-boundary")
    assert entry["disposition"] == fsr.DISPOSITION_COMPILED
    spec = entry["candidate_spec"]
    for field in ("population", "coordinates", "relation", "outcome", "economic_floor_rule", "foundry_family_variant_count"):
        assert spec[field] is not None
    assert spec["candidate_spec_hash"]

    fresh = fc.sources_compiler_hermetic_fixture_view()
    fresh_entry = next(f for f in fresh["fixtures"] if f["source_id"] == "fixture-natural-boundary")
    assert fresh_entry["candidate_spec"]["candidate_spec_hash"] == spec["candidate_spec_hash"]


def test_tc3_immutability_proof_hashes_equal_despite_different_injected_extra():
    body = _foundry_body()
    proof = body["sources_compiler"]["immutability_proof"]
    assert proof["injected_extra_a"] != proof["injected_extra_b"]
    assert proof["candidate_spec_hash_a"] == proof["candidate_spec_hash_b"]
    assert proof["hashes_equal"] is True


# === interpreter_fixtures (J-03): TC-4, TC-5, TC-6, TC-7 ============================================


def _scenario(body: dict, kind: str) -> dict:
    return next(s for s in body["interpreter_fixtures"]["scenarios"] if s["kind"] == kind)


def test_tc4_immediate_scalar_equivalence_is_byte_identical_to_direct_scout():
    body = _foundry_body()
    scenario = _scenario(body, "immediate_scalar_equivalence")
    assert scenario["foundry_screen"] == scenario["direct_scout_screen"]
    assert scenario["screens_equal"] is True
    assert scenario["foundry_screen"]["decision"] not in ("killed_insufficient_n",)


def test_tc5_deferred_refill_consistent_excludes_unresolved_and_symmetric_timing():
    body = _foundry_body()
    scenario = _scenario(body, "deferred_refill_consistent")
    assert scenario["unresolved_excluded_count"] > 0
    assert scenario["outcome_start_candidate"] == scenario["outcome_start_comparator"]


def test_tc6_mirrored_pair_shows_predeclared_sidedness():
    body = _foundry_body()
    scenario = _scenario(body, "mirrored_direction")
    assert scenario["predeclared_sidedness"]["support_long"] == "long"
    assert scenario["predeclared_sidedness"]["resistance_short"] == "short"
    assert scenario["foundry_screen"]["support_long"]["decision"] == "killed_direction"
    assert scenario["foundry_screen"]["resistance_short"]["decision"] == "survive"


def test_tc7_unsupported_ordered_relation_typed_block_no_screen():
    body = _foundry_body()
    scenario = _scenario(body, "unsupported_ordered_relation")
    assert scenario["block_reason"] == "BLOCKED_UNSUPPORTED_RELATION"
    assert scenario["foundry_screen"] is None


def test_interpreter_fixtures_has_exactly_five_scenarios_of_the_five_named_kinds():
    body = _foundry_body()
    kinds = {s["kind"] for s in body["interpreter_fixtures"]["scenarios"]}
    assert kinds == {
        "immediate_scalar_equivalence", "conjunction", "deferred_refill_consistent",
        "mirrored_direction", "unsupported_ordered_relation",
    }
    assert len(body["interpreter_fixtures"]["scenarios"]) == 5


# === freeze_integrity (J-04): TC-8 through TC-13 ====================================================


def test_tc8_family_denominator_fixtures_over_cap_blocked_whole_denominator_visible():
    body = _foundry_body()
    fixtures = body["freeze_integrity"]["family_denominator_fixtures"]
    assert len(fixtures) == 4
    by_kind = {f["family_kind"]: f for f in fixtures}
    assert set(by_kind) == {"single", "multiple", "at_cap", "over_cap"}
    assert by_kind["over_cap"]["over_cap_blocked_whole"] is True
    assert by_kind["over_cap"]["variant_count"] == 25  # SCOUT_MAX_VARIANTS_PER_FAMILY + 1
    assert by_kind["at_cap"]["over_cap_blocked_whole"] is False
    assert all(f["denominator_visible_before_result"] is True for f in fixtures)


def test_tc9_late_insertion_refused():
    body = _foundry_body()
    assert body["freeze_integrity"]["late_insertion_refused"] is True


def test_tc10_generation_replay_idempotent_and_drift_refused():
    body = _foundry_body()
    replay = body["freeze_integrity"]["generation_replay"]
    assert replay["identical_rerun_verified"] is True
    assert replay["drifted_rerun_refused"] is True


def test_tc11_freeze_record_target_path_and_hash_matches_a_fresh_recomputation():
    body = _foundry_body()
    record = body["freeze_integrity"]["freeze_record"]
    assert record["freeze_set_target_path"] == "docs/hypothesis-foundry/freeze-set.json"
    assert record["transitive_dependency_coverage_complete"] is True
    fresh = fz.generate_freeze_set(fz.freeze_integrity_fixture_dir())
    assert fresh["freeze_set_hash"] == record["freeze_set_hash"]


def test_tc12_first_read_lock_three_outcomes():
    body = _foundry_body()
    lock = body["freeze_integrity"]["first_read_lock"]
    assert lock["hash_drift_refused"] is True
    assert lock["session_dirt_ignored"] is True
    assert lock["non_science_file_exempted"] is True


def test_tc13_replay_idempotent_conflicting_and_concurrent_refused():
    body = _foundry_body()
    replay = body["freeze_integrity"]["replay"]
    assert replay["idempotent"] is True
    assert replay["conflicting_replay_refused"] is True
    assert replay["concurrent_runner_refused"] is True


# === hermetic_oracles (J-05): TC-14, TC-15 ==========================================================


def test_tc14_outcome_types_present_covers_every_named_j05_step1_type_and_consistent_denominator():
    body = _foundry_body()
    oracles = body["hermetic_oracles"]
    required = {
        "compiled", "blocked_spec_gap", "insufficient", "null_killed", "wrong_direction_killed",
        "concentration_killed", "economic_killed", "fragility_killed", "survivor",
    }
    assert required <= set(oracles["outcome_types_present"])
    assert oracles["denominator_consistent_across_rows"] is True
    assert oracles["canonical_order_preserved"] is True
    assert oracles["suite_source"] == "tests/test_foundry_hermetic_epoch.py"


def test_tc15_five_named_oracle_fixtures_all_pass():
    body = _foundry_body()
    oracles = body["hermetic_oracles"]
    for field in (
        "all_blocked_epoch_completed", "all_killed_epoch_completed", "multi_survivor_preserved_all",
        "crash_resume_at_scale_verified", "protected_data_trip_fails_closed", "evidence_class_immutable",
    ):
        assert oracles[field] is True, field


# === goal-hypothesis-foundry-iter-5 (J-05 repairs): kill_type_mapping, best_of_n_disclosure, ========
# and outcome_types_present row-derivation. =============================================================


def test_iter5_kill_type_mapping_has_seven_rows_each_with_its_own_real_foundry_state():
    body = _foundry_body()
    mapping = body["hermetic_oracles"]["kill_type_mapping"]
    assert len(mapping) == 7
    expected_states = {
        "insufficient": "EVALUATED_INSUFFICIENT",
        "null": "EVALUATED_KILLED",
        "direction": "EVALUATED_KILLED",
        "concentration": "EVALUATED_KILLED",
        "economic": "EVALUATED_KILLED",
        "fragile": "EVALUATED_KILLED",
        "survive": "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
    }
    by_label = {row["outcome_label"]: row["foundry_state"] for row in mapping}
    assert by_label == expected_states


def test_iter5_best_of_n_disclosure_present_and_n_variants_tried_identical_across_all_seven_rows():
    """``n_variants_tried`` (the frozen family denominator) is genuinely identical across every
    composite row -- verified directly against the raw per-row disclosures, not assumed.
    ``threshold_bps`` is a real, non-fabricated value off one of those same rows, but is NOT
    asserted identical across all seven: `scout._best_of_n_disclosure`'s own `corrected_threshold_
    bps` is a function of each candidate's OWN null-permutation draws (confirmed empirically to
    differ row to row even within one shared family, and `None` for the `killed_insufficient_n`
    row, whose null draws are never computed) -- only `n` is a true family-level constant."""
    body = _foundry_body()
    oracles = body["hermetic_oracles"]
    disclosure = oracles["best_of_n_disclosure"]
    assert disclosure["n_variants_tried"] == 7
    assert isinstance(disclosure["threshold_bps"], float)

    import tempfile
    from pathlib import Path as _Path

    import tests.test_foundry_hermetic_epoch as the_suite
    from app.research import foundry_hermetic_summary as fhs

    with tempfile.TemporaryDirectory() as d:
        composite = fhs._composite_epoch(the_suite, _Path(d))
    raw_disclosures = [
        row["screen_result"]["screen_result"]["best_of_n_disclosure"] for _, _, row in composite["results"]
    ]
    assert len(raw_disclosures) == 7
    assert {raw["n"] for raw in raw_disclosures} == {7}
    non_none_thresholds = {raw["corrected_threshold_bps"] for raw in raw_disclosures if raw["corrected_threshold_bps"] is not None}
    assert disclosure["threshold_bps"] in non_none_thresholds


def test_iter5_outcome_types_present_is_row_derived_not_hardcoded():
    """TC-14: mutating one composite-epoch row's terminal outcome changes the returned
    `outcome_types_present` set -- proving it is derived by reading each row's actual state, not
    returned from a hard-coded dict keyed on anything else."""
    from app.research.foundry_hermetic_summary import _derive_outcome_types_present

    rows = [
        ("insufficient", None, {"screen_result": {"decision": "killed_insufficient_n"}}),
        ("null", None, {"screen_result": {"decision": "killed_null"}}),
        ("survive", None, {"screen_result": {"decision": "survive"}}),
    ]
    before = _derive_outcome_types_present("compiled", {}, rows)
    assert before == ["compiled", "insufficient", "null_killed", "survivor"]

    # mutate ONE row's real terminal outcome (the "null" row now genuinely survives instead).
    mutated_rows = list(rows)
    mutated_rows[1] = ("null", None, {"screen_result": {"decision": "survive"}})
    after = _derive_outcome_types_present("compiled", {}, mutated_rows)
    assert after == ["compiled", "insufficient", "survivor"]
    assert after != before


# === TC-19: the GET route never recomputes; served payloads are byte-identical across calls ========


def test_tc19_repeated_get_calls_serve_byte_identical_new_subview_payloads():
    with TestClient(app) as client:
        first = client.get("/research/desk/micro/foundry").json()
        second = client.get("/research/desk/micro/foundry").json()
    for key in ("sources_compiler", "interpreter_fixtures", "freeze_integrity", "hermetic_oracles"):
        assert first[key] == second[key]


def test_tc19_get_route_never_invokes_the_fixture_builders_per_request(monkeypatch):
    """A monkeypatch/spy proof (TC-19's own suggested method): even if every one of the four
    builder functions is replaced with one that raises, the route -- which only ever reads the
    module-level cached views built once at import time -- keeps serving the SAME unaffected data,
    proving it never calls these functions per request."""
    import app.research.micro_routes as micro_routes_module

    def _boom(*args, **kwargs):
        raise AssertionError("the GET route recomputed a Foundry fixture view per request")

    monkeypatch.setattr(micro_routes_module, "sources_compiler_hermetic_fixture_view", _boom)
    monkeypatch.setattr(micro_routes_module, "interpreter_hermetic_fixture_view", _boom)
    monkeypatch.setattr(micro_routes_module, "freeze_integrity_hermetic_fixture_view", _boom)
    monkeypatch.setattr(micro_routes_module, "build_hermetic_oracles_summary", _boom)

    with TestClient(app) as client:
        response = client.get("/research/desk/micro/foundry")
    assert response.status_code == 200
    body = response.json()
    assert len(body["sources_compiler"]["fixtures"]) == 8
    assert len(body["interpreter_fixtures"]["scenarios"]) == 5


def test_tc19_the_served_subviews_are_the_same_cached_object_across_two_in_process_calls():
    """The strongest form of "never recomputed": calling the route FUNCTION directly (bypassing
    HTTP/JSON serialization) twice returns the identical (``is``) Python object both times."""
    import app.research.micro_routes as micro_routes_module

    first = micro_routes_module.get_foundry(foundry_dir="/tmp/does-not-exist-tc19")
    second = micro_routes_module.get_foundry(foundry_dir="/tmp/does-not-exist-tc19")
    assert first["sources_compiler"] is second["sources_compiler"]
    assert first["interpreter_fixtures"] is second["interpreter_fixtures"]
    assert first["freeze_integrity"] is second["freeze_integrity"]
    assert first["hermetic_oracles"] is second["hermetic_oracles"]


def test_tc19_config_fingerprint_stays_pinned():
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
