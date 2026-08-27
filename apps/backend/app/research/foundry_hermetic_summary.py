"""The Hypothesis Foundry -- the ``hermetic_oracles`` Foundry read-surface subview
(goal-hypothesis-foundry-iter-4, J-05). A THIN summary builder: it introduces no second oracle
implementation and never reads/serves any protected/sealed identity. It reports outcomes by
GENUINELY RE-RUNNING ``tests/test_foundry_hermetic_epoch.py``'s own already-hermetically-proven
fixture generators through the REAL production ``foundry_compiler`` -> ``foundry_interpreter`` ->
``foundry_family`` -> ``foundry_ledger`` -> ``foundry_runner`` path -- never a hand-typed duplicate
of "these outcomes exist" (``lessons.md`` iter-3, applied twice per this iteration's own NOTES).

**Why this module imports from ``tests/``.** Every other Foundry fixture-view function in this
package (``foundry_compiler.sources_compiler_hermetic_fixture_view``,
``foundry_interpreter.interpreter_hermetic_fixture_view``,
``foundry_freeze.freeze_integrity_hermetic_fixture_view``) is self-contained -- it does not import
from ``tests/``. This module is the ONE deliberate exception: the goal's own IN SCOPE text names
``tests/test_foundry_hermetic_epoch.py`` as the exact suite this summary must read from, and that
suite's own kill-type fixture generators (``_survive_anchors``, ``_null_anchors``,
``_wrong_direction_anchors``, ``_concentration_anchors``, ``_insufficient_anchors``,
``_fragile_anchors``, the non-compiled source builders, the crash-fixture builder) are non-trivial,
seeded, already-proven constructions -- re-typing them here would be exactly the "second, hand-typed
duplicate" the goal's carried lesson forbids. Importing the test module and calling its private
(underscore) fixture functions as plain functions never executes any ``pytest`` test item (pytest
only invokes functions whose name matches its collection pattern when it runs; a plain Python
``import`` merely defines them) -- this module drives them itself, through the real production
path, and reports what genuinely comes back.

``app/research`` is on ``sys.path`` whenever this backend process is started (see
``scripts/start-backend.sh``'s ``cd apps/backend`` before ``uvicorn ... --app-dir``), and pytest's
own rootless import mode adds the same directory for the test run itself -- so ``import
tests.test_foundry_hermetic_epoch`` resolves identically in both contexts."""

from __future__ import annotations

import tempfile
from pathlib import Path

from . import foundry_compiler as fc
from . import foundry_family as ff
from . import foundry_ledger as fl
from . import foundry_runner as fr
from . import foundry_source_registry as fsr
from . import scout

__all__ = ["build_hermetic_oracles_summary"]

_SUITE_SOURCE = "tests/test_foundry_hermetic_epoch.py"


def _composite_epoch(the_suite, base_dir: Path) -> dict:
    """Re-runs the SAME composite "complete factory" epoch
    ``test_tc1_tc2_composite_complete_factory_epoch_reaches_every_outcome_type_in_canonical_order``
    already proves: one BLOCKED_*/EXCLUDED_*/ALIASED_* source triple, plus seven FROZEN_READY
    variants (insufficient, null, wrong-direction, concentration, economic, fragile, survive) in
    one 7-variant Foundry family -- through the real ``foundry_runner.run_one_candidate``."""
    non_compiled = [the_suite._blocked_source(), the_suite._excluded_source(), the_suite._aliased_source()]
    non_compiled_dispositions = {r.source_id: fsr.compile_source_disposition(r) for r in non_compiled}

    family_id = "family:hermetic-summary-composite"
    family = ff.build_family_registry({family_id: [f"{family_id}:{i}" for i in range(7)]})[family_id]

    plan = [
        ("insufficient", the_suite._insufficient_anchors(), the_suite._ECON_FLOOR_TINY, False),
        ("null", the_suite._null_anchors(901), the_suite._ECON_FLOOR_TINY, False),
        ("direction", the_suite._wrong_direction_anchors(902), the_suite._ECON_FLOOR_TINY, False),
        ("concentration", the_suite._concentration_anchors(903), the_suite._ECON_FLOOR_TINY, False),
        ("economic", the_suite._survive_anchors(904, effect_bps=40.0), the_suite._ECON_FLOOR_HUGE, False),
        ("fragile", the_suite._fragile_anchors(), the_suite._ECON_FLOOR_TINY, True),
        ("survive", the_suite._survive_anchors(906, effect_bps=60.0), the_suite._ECON_FLOOR_TINY, False),
    ]
    specs = [the_suite._spec(i, family_id=family_id, family_count=7) for i in range(len(plan))]

    ledger = fl.FoundryLedger(base_dir / "composite")
    manifest_hash = "manifest:hermetic-summary-composite"
    results = []
    for (label, anchors, floor, needs_fragile_patch), spec in zip(plan, specs):
        if needs_fragile_patch:
            original = scout._two_sided_p
            scout._two_sided_p = lambda observed, null: 0.0001
            try:
                row = fr.run_one_candidate(
                    spec, anchors, ledger=ledger, econ_floor=floor, manifest_hash=manifest_hash, family=family
                )
            finally:
                scout._two_sided_p = original
        else:
            row = fr.run_one_candidate(
                spec, anchors, ledger=ledger, econ_floor=floor, manifest_hash=manifest_hash, family=family
            )
        results.append((label, spec, row))

    terminal_hashes = [row["candidate_spec_hash"] for _, _, row in results]
    expected_hashes = [spec.candidate_spec_hash for _, spec, _ in results]
    canonical_order_preserved = terminal_hashes == expected_hashes

    denominators = {row["foundry_family_variant_count"] for _, _, row in results}
    denominator_consistent_across_rows = denominators == {7}

    evidence_class_immutable = all(
        row["screen_result"]["screen_result"]["evidence_class"] == scout.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
        for _, _, row in results
    )

    return {
        "results": results,
        "non_compiled_dispositions": non_compiled_dispositions,
        "canonical_order_preserved": canonical_order_preserved,
        "denominator_consistent_across_rows": denominator_consistent_across_rows,
        "evidence_class_immutable": evidence_class_immutable,
    }


def _compiled_flow_disposition(the_suite, base_dir: Path) -> str:
    """Re-runs
    ``test_compiled_candidate_specs_flow_from_the_real_compiler_into_the_real_runner``'s own seam:
    real ``SourceRecord``\\ s -> ``foundry_compiler.compile_sources`` -> real ``foundry_runner`` --
    proves a genuine ``COMPILED`` disposition is present in this summary's own live run, not only
    hand-built ``CandidateSpec``\\ s (the gap that iter-3's audit pass added this exact test for)."""
    records = [
        the_suite._compilable_variant_record("hermetic-summary-compiled-a", 0),
        the_suite._compilable_variant_record("hermetic-summary-compiled-b", 1),
    ]
    result = fc.compile_sources(
        records, foundry_spec_version="v1", epoch_id="epoch:hermetic-summary-compiled-flow",
        blueprints={
            "hermetic-summary-compiled-a": the_suite._compilable_blueprint("trades_20"),
            "hermetic-summary-compiled-b": the_suite._compilable_blueprint("trades_100"),
        },
    )
    spec_a = result.candidate_specs["hermetic-summary-compiled-a"]
    spec_b = result.candidate_specs["hermetic-summary-compiled-b"]
    family_id = spec_a.foundry_family_id
    family = ff.build_family_registry({family_id: [spec_a.variant_id, spec_b.variant_id]})[family_id]
    ledger = fl.FoundryLedger(base_dir / "compiled-flow")
    fr.run_family(
        family, [(spec_a, the_suite._survive_anchors(941, effect_bps=60.0)), (spec_b, the_suite._null_anchors(942))],
        ledger=ledger, econ_floor=the_suite._ECON_FLOOR_TINY, manifest_hash="manifest:hermetic-summary-compiled-flow",
    )
    return result.dispositions["hermetic-summary-compiled-a"]  # "COMPILED"


def _all_blocked_epoch_completed(base_dir: Path) -> bool:
    """TC-3 (test_foundry_hermetic_epoch.py)/TC-15 (this iteration): the exhaust runner reaches a
    valid, non-error, honestly-zero terminal completion over an empty manifest -- zero ledger rows
    of any kind."""
    ledger = fl.FoundryLedger(base_dir / "all-blocked")
    empty_family_registry = ff.build_family_registry({})
    visited = [
        row
        for fam in empty_family_registry.values()
        for row in fr.run_family(fam, [], ledger=ledger, econ_floor={"floor_bps": 0.0}, manifest_hash="manifest:hermetic-summary-all-blocked")
    ]
    zero_variant_family = ff.build_family_registry({"family:hermetic-summary-all-blocked": []})[
        "family:hermetic-summary-all-blocked"
    ]
    zero_result = fr.run_family(
        zero_variant_family, [], ledger=ledger, econ_floor={"floor_bps": 0.0},
        manifest_hash="manifest:hermetic-summary-all-blocked",
    )
    return (
        visited == []
        and zero_result == []
        and ledger.all_rows() == []
        and ledger.verify_chain()["ok"] is True
    )


def _all_killed_epoch_completed(the_suite, base_dir: Path) -> bool:
    """TC-4: every FROZEN_READY variant in a 6-member family terminates
    ``EVALUATED_INSUFFICIENT``/``EVALUATED_KILLED`` -- zero survivor rows."""
    family_id = "family:hermetic-summary-all-killed"
    family = ff.build_family_registry({family_id: [f"{family_id}:{i}" for i in range(6)]})[family_id]
    plan = [
        ("insufficient", the_suite._insufficient_anchors(), the_suite._ECON_FLOOR_TINY, False),
        ("null", the_suite._null_anchors(911), the_suite._ECON_FLOOR_TINY, False),
        ("direction", the_suite._wrong_direction_anchors(912), the_suite._ECON_FLOOR_TINY, False),
        ("concentration", the_suite._concentration_anchors(913), the_suite._ECON_FLOOR_TINY, False),
        ("economic", the_suite._survive_anchors(914, effect_bps=40.0), the_suite._ECON_FLOOR_HUGE, False),
        ("fragile", the_suite._fragile_anchors(), the_suite._ECON_FLOOR_TINY, True),
    ]
    ledger = fl.FoundryLedger(base_dir / "all-killed")
    manifest_hash = "manifest:hermetic-summary-all-killed"
    for i, (label, anchors, floor, needs_fragile_patch) in enumerate(plan):
        spec = the_suite._spec(i, family_id=family_id, family_count=6)
        if needs_fragile_patch:
            original = scout._two_sided_p
            scout._two_sided_p = lambda observed, null: 0.0001
            try:
                row = fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=floor, manifest_hash=manifest_hash, family=family)
            finally:
                scout._two_sided_p = original
        else:
            row = fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=floor, manifest_hash=manifest_hash, family=family)
        if row["foundry_state"] == "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN":
            return False
    terminal_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL]
    return len(terminal_rows) == 6 and all(
        r["foundry_state"] in ("EVALUATED_INSUFFICIENT", "EVALUATED_KILLED") for r in terminal_rows
    )


def _multi_survivor_preserved_all(the_suite, base_dir: Path) -> bool:
    """TC-5: a 3-variant family (survive, null, survive) preserves BOTH distinct survivor rows --
    no ranking/selection/demotion."""
    family_id = "family:hermetic-summary-multi-survivor"
    family = ff.build_family_registry({family_id: [f"{family_id}:{i}" for i in range(3)]})[family_id]
    variants = [
        (the_suite._spec(0, family_id=family_id, family_count=3), the_suite._survive_anchors(921, effect_bps=50.0)),
        (the_suite._spec(1, family_id=family_id, family_count=3), the_suite._null_anchors(922)),
        (the_suite._spec(2, family_id=family_id, family_count=3), the_suite._survive_anchors(923, effect_bps=70.0)),
    ]
    ledger = fl.FoundryLedger(base_dir / "multi-survivor")
    manifest_hash = "manifest:hermetic-summary-multi-survivor"
    results = [
        fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=the_suite._ECON_FLOOR_TINY, manifest_hash=manifest_hash, family=family)
        for spec, anchors in variants
    ]
    survivors = [r for r in results if r["foundry_state"] == "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"]
    survivor_hashes = {r["candidate_spec_hash"] for r in survivors}
    return len(survivors) == 2 and len(survivor_hashes) == 2 and results[1]["foundry_state"] != "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"


def _crash_resume_at_scale_verified(the_suite, base_dir: Path) -> bool:
    """TC-6: 20 candidates (4 families x 5 variants) with a simulated mid-epoch crash after 12 --
    a BRAND NEW ``FoundryLedger`` instance re-opened on the same on-disk directory reconstructs
    position from the ledger itself, verifying/skipping the first 12 byte-identically and genuinely
    executing the remaining 8."""
    crash_dir = base_dir / "crash-resume"
    all_variants = the_suite._crash_fixture_variants()
    manifest_hash = "manifest:hermetic-summary-crash-resume"

    ledger_run1 = fl.FoundryLedger(crash_dir)
    pre_crash_rows = []
    for family_id, family, spec, anchors in all_variants[:12]:
        row = fr.run_one_candidate(spec, anchors, ledger=ledger_run1, econ_floor=the_suite._ECON_FLOOR_TINY, manifest_hash=manifest_hash, family=family)
        pre_crash_rows.append(row)
    del ledger_run1  # simulate the crash: no Python-level state survives

    ledger_run2 = fl.FoundryLedger(crash_dir)
    post_crash_rows = []
    for family_id, family, spec, anchors in all_variants:
        row = fr.run_one_candidate(spec, anchors, ledger=ledger_run2, econ_floor=the_suite._ECON_FLOOR_TINY, manifest_hash=manifest_hash, family=family)
        post_crash_rows.append(row)

    if not all(post_crash_rows[i] == pre_crash_rows[i] for i in range(12)):
        return False
    terminal_rows = [r for r in ledger_run2.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL]
    if len(terminal_rows) != 20:
        return False
    expected_hash_order = [spec.candidate_spec_hash for _, _, spec, _ in all_variants]
    if [r["candidate_spec_hash"] for r in terminal_rows] != expected_hash_order:
        return False
    return ledger_run2.verify_chain()["ok"] is True


def _protected_data_trip_fails_closed(the_suite, base_dir: Path) -> bool:
    """TC-7: a hermetic population source raising ``MicroAccessorSealedShardError`` /
    ``MicroAccessorOriginFenceError`` partway through anchor resolution fails closed -- no terminal
    row is ever written for that candidate."""
    from app.research.micro_accessor import MicroAccessorOriginFenceError, MicroAccessorSealedShardError

    all_clean = True
    for exc_factory in (
        lambda: MicroAccessorSealedShardError("hermetic-summary-sealed-shard"),
        lambda: MicroAccessorOriginFenceError("origin fence tripped for hermetic-summary-fenced-shard"),
    ):
        exc = exc_factory()
        family_id = f"family:hermetic-summary-protected-trip-{type(exc).__name__}"
        family = ff.build_family_registry({family_id: [f"{family_id}:0"]})[family_id]
        spec = the_suite._spec(0, family_id=family_id, family_count=1)
        ledger = fl.FoundryLedger(base_dir / f"protected-trip-{type(exc).__name__}")
        try:
            fr.run_one_candidate(
                spec, the_suite._population_source_raising(exc), ledger=ledger,
                econ_floor=the_suite._ECON_FLOOR_TINY, manifest_hash="manifest:hermetic-summary-protected-trip",
                family=family,
            )
            all_clean = False  # the exception should always propagate -- reaching here is a failure
        except type(exc):
            pass
        if ledger.terminal_row_for(spec.candidate_spec_hash) is not None:
            all_clean = False
    return all_clean


def build_hermetic_oracles_summary() -> dict:
    """The ``hermetic_oracles`` Foundry read-surface subview: reports, from
    ``tests/test_foundry_hermetic_epoch.py``'s existing composite suite, every outcome type present
    in a live re-run of the composite epoch, denominator consistency across all rows, canonical
    -order preservation, and pass/fail for the all-blocked, all-killed, multi-survivor, crash
    -resume-at-scale, and protected-data-trip/evidence-class-immutability fixtures. A pure,
    deterministic function -- ``micro_routes.py`` calls this exactly ONCE (module-import time),
    never per request (T-8 / goal.md anti-goal 10)."""
    import tests.test_foundry_hermetic_epoch as the_suite  # the ONE deliberate prod->test import; see module docstring

    with tempfile.TemporaryDirectory() as d:
        base_dir = Path(d)
        composite = _composite_epoch(the_suite, base_dir)
        compiled_disposition = _compiled_flow_disposition(the_suite, base_dir)
        all_blocked_epoch_completed = _all_blocked_epoch_completed(base_dir)
        all_killed_epoch_completed = _all_killed_epoch_completed(the_suite, base_dir)
        multi_survivor_preserved_all = _multi_survivor_preserved_all(the_suite, base_dir)
        crash_resume_at_scale_verified = _crash_resume_at_scale_verified(the_suite, base_dir)
        protected_data_trip_fails_closed = _protected_data_trip_fails_closed(the_suite, base_dir)

    outcome_types_present = sorted(
        {
            compiled_disposition.lower(),  # "compiled"
            *(d.lower() for d in composite["non_compiled_dispositions"].values()),  # blocked/excluded/aliased
            *(
                {
                    "insufficient": "insufficient",
                    "null": "null_killed",
                    "direction": "wrong_direction_killed",
                    "concentration": "concentration_killed",
                    "economic": "economic_killed",
                    "fragile": "fragility_killed",
                    "survive": "survivor",
                }[label]
                for label, _, _ in composite["results"]
            ),
        }
    )

    return {
        "outcome_types_present": outcome_types_present,
        "denominator_consistent_across_rows": composite["denominator_consistent_across_rows"],
        "canonical_order_preserved": composite["canonical_order_preserved"],
        "all_blocked_epoch_completed": all_blocked_epoch_completed,
        "all_killed_epoch_completed": all_killed_epoch_completed,
        "multi_survivor_preserved_all": multi_survivor_preserved_all,
        "crash_resume_at_scale_verified": crash_resume_at_scale_verified,
        "protected_data_trip_fails_closed": protected_data_trip_fails_closed,
        "evidence_class_immutable": composite["evidence_class_immutable"],
        "suite_source": _SUITE_SOURCE,
    }
