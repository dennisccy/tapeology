# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 11. Shown in full: 10.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/frontend/app/desk/page.tsx` (27 lines not shown)

```diff
diff --git a/apps/backend/app/research/foundry_compiler.py b/apps/backend/app/research/foundry_compiler.py
index ae730e09..9a3dbf0a 100644
--- a/apps/backend/app/research/foundry_compiler.py
+++ b/apps/backend/app/research/foundry_compiler.py
@@ -21,15 +21,24 @@ from __future__ import annotations
 import hashlib
 import json
 from collections import defaultdict
-from dataclasses import asdict, dataclass, field
+from dataclasses import asdict, dataclass, field, replace as _dataclasses_replace
 from pathlib import Path
 from typing import Mapping, Sequence
 
 from . import scout
 from .foundry_source_registry import (
     DISPOSITION_COMPILED,
+    QuotedSpan,
+    ProxyDeclaration,
     SourceRecord,
+    SupersessionDeclaration,
+    THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
+    BLOCKED_DIRECTION_SENTINEL,
+    BLOCKED_UNSUPPORTED_STUDY_FORM_SENTINEL,
+    DISPOSITION_ALIASED_VARIANT_VOCABULARY,
+    _canonical_source_record,
     compile_source_disposition,
+    lint_alternatives,
     lint_quoted_spans,
     source_registry_hash as _registry_hash,
 )
@@ -50,6 +59,8 @@ __all__ = [
     "FamilyOrdinalCollision",
     "compile_sources",
     "compiler_hash",
+    "candidate_spec_view",
+    "sources_compiler_hermetic_fixture_view",
 ]
 
 # --- §3 frozen literal-valued fields -- named constants so a caller/test never re-types the
@@ -241,8 +252,14 @@ def compile_sources(
     (``foundry_source_registry.SourceRecord``) and the §3 ``CandidateSpec`` schema this module
     owns are deliberately two separate schemas (goal.md itself lists them as two distinct
     sections); keeping ``CandidateBlueprint`` out of ``SourceRecord`` avoids a needless import
-    cycle between the two modules and keeps each module's own schema self-contained."""
+    cycle between the two modules and keeps each module's own schema self-contained.
+
+    Repair 1 (auditor B7, iter-4): ``lint_alternatives`` runs alongside ``lint_quoted_spans``,
+    both BEFORE any ``CandidateSpec`` is built -- a stray/self-referential/wrong-family
+    ``alternatives`` entry fails the whole batch closed exactly like a mismatched quoted span
+    does, never silently compiling around it."""
     lint_quoted_spans(records)
+    lint_alternatives(records)
     blueprints = blueprints or {}
     registry_hash = _registry_hash(records)
     this_compiler_hash = compiler_hash()
@@ -307,3 +324,265 @@ def compile_sources(
         specs[record.source_id] = spec
 
     return CompilationResult(source_registry_hash=registry_hash, dispositions=dispositions, candidate_specs=specs)
+
+
+def candidate_spec_view(spec: CandidateSpec) -> dict:
+    """A canonical, plain-dict, JSON-safe projection of a WHOLE ``CandidateSpec`` -- every field
+    the dataclass carries (§3's own schema), rendered once here so every Foundry read-surface
+    caller that needs to serve a compiled spec (Sources/Compiler and Interpreter subviews alike,
+    goal-hypothesis-foundry-iter-4) shares the ONE canonical rendering rather than each hand-rolling
+    its own subset (goal.md anti-goal 6: "single source of truth... REST/UI/MCP never independently
+    recompute it")."""
+    return {
+        "foundry_spec_version": spec.foundry_spec_version,
+        "epoch_id": spec.epoch_id,
+        "source_ids": list(spec.source_ids),
+        "lineage_id": spec.lineage_id,
+        "foundry_family_id": spec.foundry_family_id,
+        "variant_id": spec.variant_id,
+        "variant_ordinal": spec.variant_ordinal,
+        "population": {
+            "structure_context_kind": spec.population.structure_context_kind,
+            "side_filter": spec.population.side_filter,
+            "setup_context_id": spec.population.setup_context_id,
+        },
+        "coordinates": [
+            {
+                "feature_construct_id": c.feature_construct_id,
+                "semantic_role": c.semantic_role,
+                "transform_orientation": c.transform_orientation,
+                "threshold_corner_predicate": c.threshold_corner_predicate,
+                "threshold_provenance": c.threshold_provenance,
+                "aggressor_derived": c.aggressor_derived,
+                "unit_basis": c.unit_basis,
+                "anchor_at": c.anchor_at,
+                "available_at": c.available_at,
+                "resolution_join_rule": c.resolution_join_rule,
+            }
+            for c in spec.coordinates
+        ],
+        "relation": {"kind": spec.relation.kind, "parameters": dict(spec.relation.parameters)},
+        "membership_corner": spec.membership_corner,
+        "outcome": {
+            "horizon_key": spec.outcome.horizon_key,
+            "sidedness": spec.outcome.sidedness,
+            "measure": spec.outcome.measure,
+        },
+        "economic_floor_rule": {
+            "rule": spec.economic_floor_rule.rule,
+            "multiple": spec.economic_floor_rule.multiple,
+            "numeric_floor_bps": spec.economic_floor_rule.numeric_floor_bps,
+        },
+        "foundry_family_variant_count": spec.foundry_family_variant_count,
+        "availability_rule": spec.availability_rule,
+        "unresolved_component_policy": spec.unresolved_component_policy,
+        "comparator": spec.comparator,
+        "manifest_hash": spec.manifest_hash,
+        "source_registry_hash": spec.source_registry_hash,
+        "compiler_hash": spec.compiler_hash,
+        "candidate_spec_hash": spec.candidate_spec_hash,
+    }
+
+
+def _hermetic_fixture_blueprint(horizon: str = "trades_20", sidedness: str = "long") -> CandidateBlueprint:
+    """The SAME one-coordinate ``band_wall_touch``/``quote_imbalance`` blueprint shape
+    ``test_foundry_compiler.py``'s own ``_blueprint`` builds -- copied rather than imported so this
+    module stays self-contained (production code does not import from ``tests/``, unlike the
+    ``hermetic_oracles`` summary's own deliberate exception -- see ``foundry_hermetic_summary.py``)."""
+    return CandidateBlueprint(
+        population=CandidatePopulation(
+            structure_context_kind="band_wall_touch", side_filter=None, setup_context_id=None
+        ),
+        coordinates=(
+            CandidateCoordinate(
+                feature_construct_id="quote_imbalance", semantic_role="primary",
+                transform_orientation="positive_zero_boundary",
+                threshold_corner_predicate="quote_imbalance > 0",
+                threshold_provenance=THRESHOLD_NATURAL_SEMANTIC_BOUNDARY, aggressor_derived=False,
+                unit_basis="ratio", anchor_at="touch", available_at="touch",
+            ),
+        ),
+        relation=CandidateRelation(kind="direct_scalar_membership"),
+        membership_corner="quote_imbalance > 0",
+        outcome=CandidateOutcome(horizon_key=horizon, sidedness=sidedness),
+    )
+
+
+def sources_compiler_hermetic_fixture_view() -> dict:
+    """The ``sources_compiler`` Foundry read-surface subview (goal-hypothesis-foundry-iter-4, J-02):
+    reuses the EXACT 7 hermetic source-fixture archetypes already proven in
+    ``test_foundry_source_registry.py``/``test_foundry_compiler.py`` -- every ``source_excerpt``/
+    ``quoted_spans`` string below is copied verbatim from those tests, never re-invented -- compiled
+    through the REAL ``compile_sources`` batch call (never a second, hand-typed disposition table).
+    A pure, deterministic function of hermetic literals -- ``micro_routes.py`` calls this exactly
+    ONCE (module-import time), never per request (T-8 / goal.md anti-goal 10).
+
+    **Why the array holds exactly 7 entries despite 8 physical ``SourceRecord``s.** J-02 step 2's
+    "two explicitly-frozen legal variants" archetype is a FAMILY of two sibling records. Both are
+    compiled here (so the surfaced record's own ``foundry_family_variant_count`` genuinely reads 2,
+    per §5's own family bookkeeping -- never a fabricated count), but only ONE sibling
+    (``fixture-variant-a``) is surfaced as its own array entry: its ``alternatives`` field already
+    names the other by id (spec §1.4: "an auditor reading ONE record in isolation should not have
+    to reconstruct family membership elsewhere to see legal alternatives"). This is what keeps
+    ``fixtures[]`` at the Data-contract's own "exactly 7 entries" (TC-1) while still faithfully
+    compiling the pair as one real two-variant family."""
+    natural_excerpt = "A signed variable's zero boundary is bid-heavy when quote_imbalance is positive."
+    natural_span = "signed variable's zero boundary is bid-heavy when quote_imbalance is positive"
+    natural_boundary = SourceRecord(
+        source_id="fixture-natural-boundary", source_path="docs/fixtures/mechanism.md", section_ref="2.3",
+        quoted_spans=(QuotedSpan(text=natural_span, location=natural_excerpt.index(natural_span)),),
+        source_excerpt=natural_excerpt,
+        mechanism_statement="quote imbalance zero-crossing implies bid-heavy",
+        operative_formula_refs=("quote_imbalance",),
+        direction_derivation="positive quote_imbalance implies bid-heavy -> long",
+        comparator_derivation="complement_within_same_eligible_population",
+        audit_note="zero boundary intrinsic to the signed variable's own definition, per quoted text",
+        threshold_provenance=THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
+    )
+
+    def _variant_record(source_id: str, ordinal: int, alternatives: tuple) -> SourceRecord:
+        excerpt = f"{source_id}: trades_20 and trades_100 are both already-legal outcome horizons."
+        span_text = "trades_20 and trades_100 are both already-legal outcome horizons"
+        return SourceRecord(
+            source_id=source_id, source_path="docs/fixtures/mechanism.md", section_ref="4.1",
+            quoted_spans=(QuotedSpan(text=span_text, location=excerpt.index(span_text)),),
+            source_excerpt=excerpt,
+            mechanism_statement="two legal horizon variants of one mechanism",
+            operative_formula_refs=("cumulative_delta",),
+            direction_derivation="positive cumulative_delta -> long",
+            comparator_derivation="complement_within_same_eligible_population",
+            audit_note="two already-defined legal outcome horizons enumerated per the frozen vocabulary, §2.1",
+            foundry_family_key="fixture-family-horizon-variants", variant_ordinal=ordinal,
+            alternatives=alternatives,
+        )
+
+    variant_a = _variant_record("fixture-variant-a", 0, alternatives=("fixture-variant-b",))
+    variant_b = _variant_record("fixture-variant-b", 1, alternatives=("fixture-variant-a",))
+
+    magnitude_excerpt = "A collapse in impact defines a high-aggression signal at the wall."
+    magnitude_span = "collapse in impact defines a high-aggression signal"
+    magnitude_word = SourceRecord(
+        source_id="fixture-magnitude-word", source_path="docs/fixtures/mechanism.md", section_ref="1.9",
+        quoted_spans=(QuotedSpan(text=magnitude_span, location=magnitude_excerpt.index(magnitude_span)),),
+        source_excerpt=magnitude_excerpt,
+        mechanism_statement="impact collapse at the wall implies reversal",
+        operative_formula_refs=("impact_efficiency",),
+        direction_derivation="collapse implies reversal -> long",
+        comparator_derivation="complement_within_same_eligible_population",
+        audit_note="'collapse'/'high' are undefined magnitude words -- no ratified numeric meaning exists",
+        unresolved_magnitude_words=("collapse", "high"),
+    )
+
+    proxy_excerpt = "The frozen pilot proxy stands in for Study 1's impact_efficiency mechanism."
+    proxy_span = "frozen pilot proxy stands in for Study 1's impact_efficiency mechanism"
+    proxy_only = SourceRecord(
+        source_id="fixture-proxy", source_path="docs/fixtures/mechanism.md", section_ref="1.1-proxy",
+        quoted_spans=(QuotedSpan(text=proxy_span, location=proxy_excerpt.index(proxy_span)),),
+        source_excerpt=proxy_excerpt,
+        mechanism_statement="pilot proxy candidate request for Study 1",
+        operative_formula_refs=("impact_efficiency_pilot_proxy",),
+        direction_derivation="long", comparator_derivation="complement_within_same_eligible_population",
+        audit_note="a frozen pilot proxy is provenance only, never the full mechanism",
+        proxy_of=ProxyDeclaration(
+            parked_study_source_id="study-1-range-wall-failed-aggression",
+            do_not="do_not_claim_full_study_1_mechanism",
+        ),
+    )
+
+    unsupported_excerpt = "A shuffled-side persistence statistic is not a supported Scout study form here."
+    unsupported_span = "shuffled-side persistence statistic is not a supported Scout study form"
+    unsupported_stat = SourceRecord(
+        source_id="fixture-unsupported-stat", source_path="docs/fixtures/mechanism.md", section_ref="9.6",
+        quoted_spans=(QuotedSpan(text=unsupported_span, location=unsupported_excerpt.index(unsupported_span)),),
+        source_excerpt=unsupported_excerpt,
+        mechanism_statement="shuffled-side persistence statistic", operative_formula_refs=(),
+        direction_derivation="long", comparator_derivation=BLOCKED_UNSUPPORTED_STUDY_FORM_SENTINEL,
+        audit_note="the existing Scout screen has no shuffled-side permutation null; unsupported study form",
+    )
+
+    alias_excerpt = "Card 9.7 event-time windows are now embodied by the current frozen feature windows."
+    alias_span = "event-time windows are now embodied by the current frozen feature windows"
+    alias_supersession = SourceRecord(
+        source_id="fixture-alias-older", source_path="docs/fixtures/mechanism.md", section_ref="9.7",
+        quoted_spans=(QuotedSpan(text=alias_span, location=alias_excerpt.index(alias_span)),),
+        source_excerpt=alias_excerpt,
+        mechanism_statement="event-time feature windows", operative_formula_refs=("event_time_window",),
+        direction_derivation="long", comparator_derivation="complement_within_same_eligible_population",
+        audit_note="Card 9.7 is variant vocabulary for an already-frozen current feature window, per §1.3",
+        superseded_fields={"event_time_window": "docs/rapid-validation-spec.md#feature-windows"},
+        supersession=SupersessionDeclaration(
+            newer_source_ref="docs/rapid-validation-spec.md#feature-windows",
+            alias_kind=DISPOSITION_ALIASED_VARIANT_VOCABULARY,
+        ),
+    )
+
+    directionless_excerpt = "The mechanism describes co-occurrence with no stated directional implication."
+    directionless_span = "co-occurrence with no stated directional implication"
+    directionless = SourceRecord(
+        source_id="fixture-directionless", source_path="docs/fixtures/mechanism.md", section_ref="9.5",
+        quoted_spans=(QuotedSpan(text=directionless_span, location=directionless_excerpt.index(directionless_span)),),
+        source_excerpt=directionless_excerpt,
+        mechanism_statement="spread-dynamics regime co-occurrence", operative_formula_refs=("spread_regime",),
+        direction_derivation=BLOCKED_DIRECTION_SENTINEL,
+        comparator_derivation="complement_within_same_eligible_population",
+        audit_note="the quoted text states co-occurrence only; no mechanical long/short implication exists",
+    )
+
+    epoch_id = "epoch:hermetic-fixture-sources-compiler"
+    all_records = [
+        natural_boundary, variant_a, variant_b, magnitude_word, proxy_only, unsupported_stat,
+        alias_supersession, directionless,
+    ]
+    result = compile_sources(
+        all_records, foundry_spec_version="v1", epoch_id=epoch_id,
+        blueprints={
+            "fixture-natural-boundary": _hermetic_fixture_blueprint(),
+            "fixture-variant-a": _hermetic_fixture_blueprint(horizon="trades_20"),
+            "fixture-variant-b": _hermetic_fixture_blueprint(horizon="trades_100"),
+        },
+    )
+
+    surfaced = [
+        natural_boundary, variant_a, magnitude_word, proxy_only, unsupported_stat,
+        alias_supersession, directionless,
+    ]
+    fixtures = []
+    for record in surfaced:
+        disposition = result.dispositions[record.source_id]
+        spec = result.candidate_specs.get(record.source_id)
+        fixtures.append(
+            {
+                **_canonical_source_record(record),
+                "disposition": disposition,
+                "candidate_spec": candidate_spec_view(spec) if spec is not None else None,
+                "block_reason": None if disposition == DISPOSITION_COMPILED else disposition,
+            }
+        )
+
+    # --- immutability_proof (TC-3): the SAME compileable fixture, compiled twice with two
+    # different injected `extra` effect/p-value/n values -- `extra` is outside every source input
+    # `compile_source_disposition`/the compiler ever reads, so both hashes must agree. -------------
+    injected_extra_a = {"effect_bps": 12.0, "p_value": 0.5, "n": 40}
+    injected_extra_b = {"effect_bps": 99.0, "p_value": 0.0001, "n": 500}
+    proof_a = compile_sources(
+        [_dataclasses_replace(natural_boundary, extra=injected_extra_a)], foundry_spec_version="v1",
+        epoch_id=epoch_id, blueprints={"fixture-natural-boundary": _hermetic_fixture_blueprint()},
+    )
+    proof_b = compile_sources(
+        [_dataclasses_replace(natural_boundary, extra=injected_extra_b)], foundry_spec_version="v1",
+        epoch_id=epoch_id, blueprints={"fixture-natural-boundary": _hermetic_fixture_blueprint()},
+    )
+    hash_a = proof_a.candidate_specs["fixture-natural-boundary"].candidate_spec_hash
+    hash_b = proof_b.candidate_specs["fixture-natural-boundary"].candidate_spec_hash
+
+    return {
+        "fixtures": fixtures,
+        "immutability_proof": {
+            "source_id": "fixture-natural-boundary",
+            "candidate_spec_hash_a": hash_a,
+            "candidate_spec_hash_b": hash_b,
+            "injected_extra_a": injected_extra_a,
+            "injected_extra_b": injected_extra_b,
+            "hashes_equal": hash_a == hash_b,
+        },
+    }
diff --git a/apps/backend/app/research/foundry_freeze.py b/apps/backend/app/research/foundry_freeze.py
index 6ab6984a..46aa4039 100644
--- a/apps/backend/app/research/foundry_freeze.py
+++ b/apps/backend/app/research/foundry_freeze.py
@@ -15,10 +15,15 @@ import ast
 import hashlib
 import json
 import subprocess
+import tempfile
 from dataclasses import dataclass
 from pathlib import Path
 from typing import Mapping, Sequence
 
+from . import foundry_family as _ffam
+from . import foundry_ledger as _fl
+from . import foundry_runner as _frun
+
 __all__ = [
     "FREEZE_SET_REQUIRED_MODULES",
     "ManifestRecord",
@@ -31,6 +36,8 @@ __all__ = [
     "verify_commit_is_ancestor",
     "FreezeIntegrityHalt",
     "verify_freeze_set_unchanged",
+    "freeze_integrity_fixture_dir",
+    "freeze_integrity_hermetic_fixture_view",
 ]
 
 
@@ -274,3 +281,234 @@ def verify_freeze_set_unchanged(freeze_set: Mapping[str, object]) -> None:
         actual_hash = _sha256_file(path)
         if actual_hash != expected_hash:
             raise FreezeIntegrityHalt(f"freeze-set path changed after first-read lock: {path}")
+
+
+# === goal-hypothesis-foundry-iter-4 (J-04): the `freeze_integrity` Foundry read-surface subview ===
+# -- reuses the EXACT hermetic fixtures already proven in `test_foundry_family.py`/
+# `test_foundry_freeze.py`/`test_foundry_ledger.py`, run through the REAL production functions
+# (`foundry_family.build_family_registry`, this module's own generation/freeze-set/first-read-lock
+# machinery, `foundry_ledger.FoundryLedger`, `foundry_runner.SingleFlightLock`) -- never a second,
+# hand-typed disposition table. A pure, deterministic function -- `micro_routes.py` calls this
+# exactly ONCE (module-import time), never per request (T-8 / goal.md anti-goal 10).
+
+_FREEZE_SET_FIXTURE_DIR_NAME = "tapeology_foundry_freeze_integrity_fixture"
+
+
+def freeze_integrity_fixture_dir() -> Path:
+    """A STABLE (non-random) directory under the platform temp root -- deliberately NOT a
+    ``tempfile.TemporaryDirectory()`` (whose randomized name would make TC-11's "a fresh
+    recomputation... over the SAME fixture module set" unreproducible, since
+    ``generate_freeze_set``'s own ``freeze_set_hash`` is sensitive to the full absolute path
+    string, not just file content). Every one of the ``FREEZE_SET_REQUIRED_MODULES`` stub files is
+    (re)written idempotently on every call with fixed content, so any caller resolving this SAME
+    path (this module's own cached fixture view, or a later verifying test) always sees
+    byte-identical files and therefore recomputes the identical ``freeze_set_hash``. Exported (not
+    private) precisely so a route-level/unit test can call it directly to prove that equality."""
+    fixture_dir = Path(tempfile.gettempdir()) / _FREEZE_SET_FIXTURE_DIR_NAME
+    fixture_dir.mkdir(parents=True, exist_ok=True)
+    for name in FREEZE_SET_REQUIRED_MODULES:
+        (fixture_dir / name).write_text("# hermetic freeze-set fixture stub -- not a real module\n", encoding="utf-8")
+    return fixture_dir
+
+
+def _family_denominator_fixtures() -> list[dict]:
+    """TC-8 (goal-hypothesis-foundry-iter-4): the exact 1/multiple/at-cap/over-cap family fixtures
+    ``test_foundry_family.py`` already proves, through the REAL ``build_family_registry``."""
+    cap = _ffam.SCOUT_MAX_VARIANTS_PER_FAMILY
+    kinds = (("single", 1), ("multiple", 5), ("at_cap", cap), ("over_cap", cap + 1))
+    out = []
+    for kind, count in kinds:
+        family_id = f"family:fixture-denominator-{kind}"
+        variants = [f"{family_id}:{i}" for i in range(count)]
+        family = _ffam.build_family_registry({family_id: variants})[family_id]
+        out.append(
+            {
+                "family_kind": kind,
+                "variant_count": family.variant_count,
+                "denominator_visible_before_result": True,
+                "over_cap_blocked_whole": family.blocked,
+            }
+        )
+    return out
+
+
+def _late_insertion_refused() -> bool:
+    """TC-9: a fixture family already frozen at variant_count=2 refuses a late-insertion attempt
+    and its denominator stays unchanged."""
+    family_id = "family:fixture-late-insertion"
+    family = _ffam.build_family_registry({family_id: [f"{family_id}:0", f"{family_id}:1"]})[family_id]
+    before = family.variant_count
+    try:
+        _ffam.attempt_late_insertion(family, new_variant_ordinal=2)
+    except _ffam.LateInsertionRefused:
+        return family.variant_count == before == 2
+    return False  # pragma: no cover -- attempt_late_insertion always refuses
+
+
+def _generation_replay() -> dict:
+    """TC-10: identical fixture generation inputs run twice verify-idempotently; a changed input
+    is refused rather than silently minting a second epoch."""
+    store: dict = {}
+    inputs = {
+        "source_registry_hash": "fixture-generation-replay-source-registry-hash",
+        "compiler_hash": "fixture-generation-replay-compiler-hash",
+        "config_fingerprint": "fixture-generation-replay-config-fingerprint",
+    }
+    first = generate_or_verify_manifest(store, inputs)
+    second = generate_or_verify_manifest(store, dict(inputs))
+    identical_rerun_verified = first.epoch_id == second.epoch_id and first.manifest_hash == second.manifest_hash
+
+    drifted_rerun_refused = False
+    drifted = {**inputs, "source_registry_hash": "CHANGED"}
+    try:
+        generate_or_verify_manifest(store, drifted)
+    except ManifestDriftRefused:
+        drifted_rerun_refused = True
+
+    return {"identical_rerun_verified": identical_rerun_verified, "drifted_rerun_refused": drifted_rerun_refused}
+
+
+def _freeze_record() -> dict:
+    """TC-11: a fixture freeze record naming the real future target path
+    ``docs/hypothesis-foundry/freeze-set.json`` (visibly fixture-scoped -- no such file is created
+    this iteration, per ``state/assumptions.md`` iter-4) whose ``freeze_set_hash`` is a genuine
+    ``generate_freeze_set`` output over the deterministic fixture module set."""
+    fixture_dir = freeze_integrity_fixture_dir()
+    result = generate_freeze_set(fixture_dir)
+    pinned_hashes = {Path(p).name: h for p, h in result["entries"].items()}
+    transitive_dependency_coverage_complete = set(FREEZE_SET_REQUIRED_MODULES) <= set(pinned_hashes)
+    record = build_freeze_record(
+        freeze_commit="fixture-freeze-commit", manifest_hash="fixture-manifest-hash",
+        source_registry_hash="fixture-source-registry-hash", spec_hash="fixture-spec-hash",
+        candidate_spec_schema_hash="fixture-candidate-spec-schema-hash",
+        compiler_hash="fixture-compiler-hash", interpreter_hash="fixture-interpreter-hash",
+        runner_hash="fixture-runner-hash", scout_screen_source_hash="fixture-scout-screen-source-hash",
+        config_fingerprint="fixture-config-fingerprint", freeze_set_hash=result["freeze_set_hash"],
+    )
+    return {
+        "freeze_set_target_path": "docs/hypothesis-foundry/freeze-set.json",
+        "freeze_set_hash": record.freeze_set_hash,
+        "pinned_hashes": pinned_hashes,
+        "transitive_dependency_coverage_complete": transitive_dependency_coverage_complete,
+    }
+
+
+def _first_read_lock() -> dict:
+    """TC-12: a simulated first-read lock followed by (a) a pinned path's content changing --
+    refused; (b) unrelated Goal Mode session/handoff dirt outside the freeze set -- ignored; and
+    (c) a changed non-scientific UI-only file outside the freeze set -- exempted. Each check runs
+    in its OWN ephemeral directory (never a randomized-name conflict with ``freeze_integrity_
+    fixture_dir`` above -- this function needs no reproducible hash, only the three booleans)."""
+    with tempfile.TemporaryDirectory() as d:
+        pinned = Path(d) / "pinned_module.py"
+        pinned.write_text("original\n", encoding="utf-8")
+        freeze_set = generate_freeze_set(d, required_names=("pinned_module.py",))
+        verify_freeze_set_unchanged(freeze_set)  # clean before drift -- must not raise
+        pinned.write_text("tampered\n", encoding="utf-8")
+        try:
+            verify_freeze_set_unchanged(freeze_set)
+            hash_drift_refused = False
+        except FreezeIntegrityHalt:
+            hash_drift_refused = True
+
+    with tempfile.TemporaryDirectory() as d:
+        pinned = Path(d) / "pinned_module.py"
+        pinned.write_text("original\n", encoding="utf-8")
+        freeze_set = generate_freeze_set(d, required_names=("pinned_module.py",))
+        (Path(d) / "iteration-state.md").write_text("dirty session notes\n", encoding="utf-8")
+        try:
+            verify_freeze_set_unchanged(freeze_set)
+            session_dirt_ignored = True
+        except FreezeIntegrityHalt:
+            session_dirt_ignored = False
+
+    with tempfile.TemporaryDirectory() as d:
+        pinned = Path(d) / "pinned_module.py"
+        pinned.write_text("original\n", encoding="utf-8")
+        freeze_set = generate_freeze_set(d, required_names=("pinned_module.py",))
+        ui_only = Path(d) / "page.tsx"
+        ui_only.write_text("export default function Page() {}\n", encoding="utf-8")
+        try:
+            verify_freeze_set_unchanged(freeze_set)
+            ui_only.write_text("export default function Page() { /* changed */ }\n", encoding="utf-8")
+            verify_freeze_set_unchanged(freeze_set)
+            non_science_file_exempted = True
+        except FreezeIntegrityHalt:
+            non_science_file_exempted = False
+
+    return {
+        "hash_drift_refused": hash_drift_refused,
+        "session_dirt_ignored": session_dirt_ignored,
+        "non_science_file_exempted": non_science_file_exempted,
+    }
+
+
+def _replay() -> dict:
+    """TC-13: a completed fixture terminal row's exact-duplicate replay is idempotent, a
+    conflicting replay is refused, and a concurrent second single-flight acquire is refused."""
+    with tempfile.TemporaryDirectory() as d:
+        ledger = _fl.FoundryLedger(d)
+        ledger.record_intent(
+            candidate_spec_hash="fixture-replay-h1", manifest_hash="fixture-replay-m1",
+            econ_floor_bps=0.0, econ_floor_provenance="scout_quoted_spread_floor",
+        )
+        screen = {
+            "decision": "survive", "reason": "survive", "notes": "hermetic fixture",
+            "screen_result": {"effect_bps": 42.0, "p_screen": 0.01, "n_candidate": 20, "n_comparator": 20},
+        }
+        first = ledger.record_terminal(
+            candidate_spec_hash="fixture-replay-h1", manifest_hash="fixture-replay-m1",
+            foundry_family_id="family:fixture-replay", foundry_family_variant_count=1,
+            screen_result=screen, rule_id="foundry:epoch:fixture-replay:fixture-replay-h1",
+            prospective_root_status="family:fixture-replay", foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
+        )
+        second = ledger.record_terminal(
+            candidate_spec_hash="fixture-replay-h1", manifest_hash="fixture-replay-m1",
+            foundry_family_id="family:fixture-replay", foundry_family_variant_count=1,
+            screen_result=screen, rule_id="foundry:epoch:fixture-replay:fixture-replay-h1",
+            prospective_root_status="family:fixture-replay", foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
+        )
+        idempotent = first == second
+
+        conflicting_screen = {**screen, "decision": "killed_null"}
+        try:
+            ledger.record_terminal(
+                candidate_spec_hash="fixture-replay-h1", manifest_hash="fixture-replay-m1",
+                foundry_family_id="family:fixture-replay", foundry_family_variant_count=1,
+                screen_result=conflicting_screen, rule_id="foundry:epoch:fixture-replay:fixture-replay-h1",
+                prospective_root_status="family:fixture-replay", foundry_state="EVALUATED_KILLED",
+            )
+            conflicting_replay_refused = False
+        except _fl.ConflictingReplayRefused:
+            conflicting_replay_refused = True
+
+    with tempfile.TemporaryDirectory() as d:
+        lock_path = Path(d) / "foundry_runner.lock"
+        lock = _frun.SingleFlightLock(lock_path)
+        with lock.acquire():
+            second_lock = _frun.SingleFlightLock(lock_path)
+            try:
+                with second_lock.acquire():
+                    pass  # pragma: no cover -- must never be reached
+                concurrent_runner_refused = False
+            except _frun.ConcurrentRunnerRefused:
+                concurrent_runner_refused = True
+
+    return {
+        "idempotent": idempotent,
+        "conflicting_replay_refused": conflicting_replay_refused,
+        "concurrent_runner_refused": concurrent_runner_refused,
+    }
+
+
+def freeze_integrity_hermetic_fixture_view() -> dict:
+    """The ``freeze_integrity`` Foundry read-surface subview (goal-hypothesis-foundry-iter-4, J-04)
+    -- see the module-level comment above this function group for the shared rationale."""
+    return {
+        "family_denominator_fixtures": _family_denominator_fixtures(),
+        "late_insertion_refused": _late_insertion_refused(),
+        "generation_replay": _generation_replay(),
+        "freeze_record": _freeze_record(),
+        "first_read_lock": _first_read_lock(),
+        "replay": _replay(),
+    }
diff --git a/apps/backend/app/research/foundry_interpreter.py b/apps/backend/app/research/foundry_interpreter.py
index 92b3f7b4..3a3f7f28 100644
--- a/apps/backend/app/research/foundry_interpreter.py
+++ b/apps/backend/app/research/foundry_interpreter.py
@@ -38,6 +38,7 @@ raises (goal.md §12) -- is not one of these two closed forms and interpretation
 
 from __future__ import annotations
 
+import random
 from collections import defaultdict
 from dataclasses import dataclass
 from typing import Mapping, Sequence
@@ -61,6 +62,7 @@ __all__ = [
     "project_boolean_membership",
     "read_model",
     "interpret_candidate",
+    "interpreter_hermetic_fixture_view",
 ]
 
 # --- §4.1's two closed relation forms this era's compiled sources can ever need (goal.md §12: "Do
@@ -301,3 +303,307 @@ def interpret_candidate(
         n_variants_tried=n_variants_tried,
     )
     return InterpretationResult(read_model=read_model(resolution), screen=screen)
+
+
+_FIXTURE_ECON_FLOOR: Mapping[str, object] = {
+    "floor_bps": 0.0, "unit": "bps", "rule": "scout_quoted_spread_floor", "multiple": 0.0,
+}
+
+
+def _fixture_spec(*, relation_kind: str, coordinates: tuple, membership_corner: str, sidedness: str = "long"):
+    """A minimal, self-contained ``CandidateSpec`` builder for this module's own hermetic fixture
+    view -- the SAME shape ``test_foundry_interpreter.py``'s own ``_spec`` helper builds, but
+    defined here (not imported from ``tests/``) so this production subview stays self-contained.
+    Local import avoids a module-load-time cycle (``foundry_compiler`` never imports THIS module,
+    so this is safe at any point, but importing lazily keeps the cycle direction obviously one-way
+    to a future reader)."""
+    from . import foundry_compiler as fc
+
+    return fc.CandidateSpec(
+        foundry_spec_version="v1", epoch_id="epoch:hermetic-fixture-interpreter",
+        source_ids=("fixture-interpreter-src",), lineage_id="fixture-interpreter-src",
+        foundry_family_id="family:fixture-interpreter-src", variant_id="family:fixture-interpreter-src:0",
+        variant_ordinal=0,
+        population=fc.CandidatePopulation(structure_context_kind="none", side_filter=None, setup_context_id=None),
+        coordinates=coordinates, relation=fc.CandidateRelation(kind=relation_kind),
+        membership_corner=membership_corner,
+        outcome=fc.CandidateOutcome(horizon_key="trades_20", sidedness=sidedness),
+        economic_floor_rule=fc.EconomicFloorRule(), foundry_family_variant_count=1,
+    ).with_hash()
+
+
+def interpreter_hermetic_fixture_view() -> dict:
+    """The ``interpreter_fixtures`` Foundry read-surface subview (goal-hypothesis-foundry-iter-4,
+    J-03): the SAME 5 hermetic scenario shapes already proven in ``test_foundry_interpreter.py``
+    (immediate-scalar Foundry-vs-direct-Scout equivalence, conjunction, deferred
+    ``refill_consistent``, mirrored support-long/resistance-short, unsupported ordered relation),
+    run through the REAL ``resolve_population``/``interpret_candidate`` pipeline -- never a
+    hand-typed expected screen. A pure, deterministic function (fixed random seeds) --
+    ``micro_routes.py`` calls this exactly ONCE (module-import time), never per request."""
+    from . import foundry_compiler as fc
+
+    scenarios: list[dict] = []
+
+    # --- 1. immediate_scalar_equivalence: byte-identical Foundry-adapter vs. direct-Scout path. ---
+    threshold = 1.0
+    scalar_anchors: list[PopulationAnchor] = []
+    for s in range(2):
+        session = f"2026-08-{10 + s:02d}"
+        for i in range(20):
+            is_member = i % 2 == 0
+            raw_value = 2.0 if is_member else 0.0
+            outcome = 12.0 + (i % 5) if is_member else -1.0 + (i % 5) * 0.1
+            comp = ComponentResolution("q_imbalance", True, float(i), raw_value, raw_value >= threshold)
+            scalar_anchors.append(
+                PopulationAnchor(f"ds-{session}", "AAPL", session, i, "mid", None, outcome, "return_bps", (comp,))
+            )
+    direct_anchors = [
+        {
+            "dataset_id": a.dataset_id, "symbol": a.symbol, "session_date": a.session_date,
+            "anchor_at": a.components[0].available_at, "trade_index": a.trade_index,
+            "feature_value": a.components[0].raw_value, "outcome_bps": a.outcome_bps,
+            "outcome_unit": a.outcome_unit, "tod_bucket": a.tod_bucket, "fallback_frac": a.fallback_frac,
+        }
+        for a in scalar_anchors
+    ]
+    direct_result = scout.screen_candidate(
+        feature_name="foundry_fixture_scalar_q_imbalance", transform="threshold",
+        params={"op": "ge", "value": threshold}, sidedness="long", horizon_key="trades_20",
+        econ_floor=_FIXTURE_ECON_FLOOR, anchors=direct_anchors,
+        family_id="fixture-family-interpreter-scalar", n_variants_tried=1,
+    )
+    scalar_spec = _fixture_spec(
+        relation_kind=RELATION_DIRECT_SCALAR,
+        coordinates=(
+            fc.CandidateCoordinate(
+                feature_construct_id="q_imbalance", semantic_role="candidate_signal",
+                transform_orientation="ge", threshold_corner_predicate="q_imbalance >= 1.0",
+                threshold_provenance="literal_ratified_threshold", aggressor_derived=False,
+                unit_basis="ratio", anchor_at="anchor_at", available_at="anchor_at",
+            ),
+        ),
+        membership_corner="q_imbalance >= 1.0",
+    )
+    scalar_interpretation = interpret_candidate(
+        scalar_spec, scalar_anchors, econ_floor=_FIXTURE_ECON_FLOOR,
+        family_id="fixture-family-interpreter-scalar", n_variants_tried=1,
+    )
+    scenarios.append(
+        {
+            "scenario_id": "fixture-immediate-scalar-equivalence",
+            "kind": "immediate_scalar_equivalence",
+            "foundry_screen": scalar_interpretation.screen,
+            "direct_scout_screen": direct_result,
+            "screens_equal": scalar_interpretation.screen == direct_result,
+            "unresolved_excluded_count": 0,
+            "outcome_start_candidate": None,
+            "outcome_start_comparator": None,
+            "block_reason": None,
+            "predeclared_sidedness": None,
+        }
+    )
+
+    # --- 2. conjunction: only boolean membership crosses the Scout boundary. -----------------------
+    conj_anchors: list[PopulationAnchor] = []
+    for s in range(2):
+        session = f"2026-08-{10 + s:02d}"
+        for i in range(24):
+            both_true = i % 3 == 0
+            c1 = ComponentResolution("c1", True, float(i), 5.0 if both_true else 0.0, both_true)
+            c2 = ComponentResolution("c2", True, float(i) + 0.5, 9.0 if both_true else 1.0, both_true)
+            outcome = 15.0 if both_true else -0.5
+            conj_anchors.append(
+                PopulationAnchor(f"ds-{session}", "AAPL", session, i, "mid", None, outcome, "return_bps", (c1, c2))
+            )
+    conjunction_spec = _fixture_spec(
+        relation_kind=RELATION_CONJUNCTION,
+        coordinates=(
+            fc.CandidateCoordinate(
+                feature_construct_id="c1", semantic_role="candidate_signal", transform_orientation="gt",
+                threshold_corner_predicate="c1 > 0", threshold_provenance="natural_semantic_boundary",
+                aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
+            ),
+            fc.CandidateCoordinate(
+                feature_construct_id="c2", semantic_role="candidate_signal", transform_orientation="gt",
+                threshold_corner_predicate="c2 > 5", threshold_provenance="literal_ratified_threshold",
+                aggressor_derived=False, unit_basis="ratio", anchor_at="anchor_at", available_at="anchor_at",
+            ),
+        ),
+        membership_corner="c1 > 0 and c2 > 5",
+    )
+    conjunction_interpretation = interpret_candidate(
+        conjunction_spec, conj_anchors, econ_floor=_FIXTURE_ECON_FLOOR,
+        family_id="fixture-family-interpreter-conjunction", n_variants_tried=1,
+    )
+    scenarios.append(
+        {
+            "scenario_id": "fixture-conjunction",
+            "kind": "conjunction",
+            "foundry_screen": conjunction_interpretation.screen,
+            "direct_scout_screen": None,
+            "screens_equal": None,
+            "unresolved_excluded_count": sum(conjunction_interpretation.read_model["unavailable_by_reason"].values()),
+            "outcome_start_candidate": None,
+            "outcome_start_comparator": None,
+            "block_reason": None,
+            "predeclared_sidedness": None,
+        }
+    )
+
+    # --- 3. deferred_refill_consistent: unresolved anchors excluded from both cells; symmetric ------
+    # outcome_start timing law. -----------------------------------------------------------------
+    deferred_anchors: list[PopulationAnchor] = []
+    deferred_session = "2026-08-10"
+    for i in range(30):
+        unresolved = i % 5 == 0
+        member = i % 2 == 0
+        if unresolved:
+            comp = ComponentResolution("refill_consistent", False, None, None, None, unavailable_reason="refill_unresolved")
+        else:
+            comp = ComponentResolution("refill_consistent", True, float(i) + 3.0, 1.0 if member else 0.0, member)
+        outcome = 10.0 if member else -2.0
+        deferred_anchors.append(
+            PopulationAnchor(f"ds-{deferred_session}", "AAPL", deferred_session, i, "mid", None, outcome, "return_bps", (comp,))
+        )
+    deferred_spec = _fixture_spec(
+        relation_kind=RELATION_DIRECT_SCALAR,
+        coordinates=(
+            fc.CandidateCoordinate(
+                feature_construct_id="refill_consistent", semantic_role="deferred_conjunct",
+                transform_orientation="boolean", threshold_corner_predicate="refill_consistent == True",
+                threshold_provenance="natural_semantic_boundary", aggressor_derived=False,
+                unit_basis="boolean", anchor_at="touch", available_at="resolution",
+                resolution_join_rule="deferred_via_observer_provenance_id",
+            ),
+        ),
+        membership_corner="refill_consistent == True",
+    )
+    deferred_interpretation = interpret_candidate(
+        deferred_spec, deferred_anchors, econ_floor=_FIXTURE_ECON_FLOOR,
+        family_id="fixture-family-interpreter-deferred", n_variants_tried=1,
+    )
+    scenarios.append(
+        {
+            "scenario_id": "fixture-deferred-refill-consistent",
+            "kind": "deferred_refill_consistent",
+            "foundry_screen": deferred_interpretation.screen,
+            "direct_scout_screen": None,
+            "screens_equal": None,
+            "unresolved_excluded_count": sum(deferred_interpretation.read_model["unavailable_by_reason"].values()),
+            # §4.1: both cells share the SAME `outcome_start = max(component.available_at)` rule --
+            # rendered as the one shared literal both sides use (`foundry_compiler.AVAILABILITY_
+            # RULE`), never a divergent per-side formula.
+            "outcome_start_candidate": fc.AVAILABILITY_RULE,
+            "outcome_start_comparator": fc.AVAILABILITY_RULE,
+            "block_reason": None,
+            "predeclared_sidedness": None,
+        }
+    )
+
+    # --- 4. mirrored_direction: predeclared sidedness on BOTH sides, shown before any outcome. ------
+    mirrored_anchors: list[PopulationAnchor] = []
+    for s in range(4):
+        session = f"2026-08-{10 + s:02d}"
+        order = list(range(40))
+        random.Random(s).shuffle(order)
+        members = set(order[:20])
+        for i in range(40):
+            member = i in members
+            comp = ComponentResolution("wall_reject", True, float(i), 1.0 if member else 0.0, member)
+            outcome = -80.0 + (i % 5) * 0.1 if member else 0.05 * (i % 5)
+            mirrored_anchors.append(
+                PopulationAnchor(f"ds-{session}", "AAPL", session, i, "mid", None, outcome, "return_bps", (comp,))
+            )
+    # A resistance/short thesis realizes a POSITIVE thesis-relative return exactly when the raw
+    # canonical `return_bps` (Constraints: `(mid_horizon - mid_start) / mid_start * 10_000`) is
+    # negative -- shorting profits from a price fall. The support/long side below uses the raw
+    # anchors verbatim; the resistance/short side uses the SAME membership/timing but the sign-
+    # negated outcome a short position would realize on that same market (goal §3.2: "aggression-
+    # toward-wall signing is mechanically buy->resistance / sell->support") -- never a second
+    # statistical rail, only the thesis-relative sign a real short extraction step would already
+    # apply before this era's unchanged Scout direction gate (`effect_bps > 0`) ever runs.
+    mirrored_coord = fc.CandidateCoordinate(
+        feature_construct_id="wall_reject", semantic_role="candidate_signal", transform_orientation="ge",
+        threshold_corner_predicate="wall_reject >= 1", threshold_provenance="natural_semantic_boundary",
+        aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
+    )
+    short_anchors = [
+        PopulationAnchor(
+            a.dataset_id, a.symbol, a.session_date, a.trade_index, a.tod_bucket, a.fallback_frac,
+            -a.outcome_bps, a.outcome_unit, a.components,
+        )
+        for a in mirrored_anchors
+    ]
+    support_long_spec = _fixture_spec(
+        relation_kind=RELATION_DIRECT_SCALAR, coordinates=(mirrored_coord,),
+        membership_corner="wall_reject >= 1", sidedness="long",
+    )
+    resistance_short_spec = _fixture_spec(
+        relation_kind=RELATION_DIRECT_SCALAR, coordinates=(mirrored_coord,),
+        membership_corner="wall_reject >= 1", sidedness="short",
+    )
+    support_long_result = interpret_candidate(
+        support_long_spec, mirrored_anchors, econ_floor=_FIXTURE_ECON_FLOOR,
+        family_id="fixture-family-interpreter-mirrored-long", n_variants_tried=1,
+    )
+    resistance_short_result = interpret_candidate(
+        resistance_short_spec, short_anchors, econ_floor=_FIXTURE_ECON_FLOOR,
+        family_id="fixture-family-interpreter-mirrored-short", n_variants_tried=1,
+    )
+    scenarios.append(
+        {
+            "scenario_id": "fixture-mirrored-support-long-resistance-short",
+            "kind": "mirrored_direction",
+            "foundry_screen": {
+                "support_long": support_long_result.screen,
+                "resistance_short": resistance_short_result.screen,
+            },
+            "direct_scout_screen": None,
+            "screens_equal": None,
+            "unresolved_excluded_count": 0,
+            "outcome_start_candidate": None,
+            "outcome_start_comparator": None,
+            "block_reason": None,
+            # Additive (goal.md's own "canonical values" lists are floors, not ceilings): the
+            # predeclared `long`/`short` sidedness is already fixed on each CandidateSpec BEFORE
+            # either screen above ever ran -- J-03 step 4's own acceptance ("predeclared sidedness
+            # is inside CandidateSpec before the outcome").
+            "predeclared_sidedness": {
+                "support_long": support_long_spec.outcome.sidedness,
+                "resistance_short": resistance_short_spec.outcome.sidedness,
+            },
+        }
+    )
+
+    # --- 5. unsupported_ordered_relation: typed block, never a guessed window/lag. -------------------
+    ordered_coord = fc.CandidateCoordinate(
+        feature_construct_id="thin_then_refill", semantic_role="candidate_signal", transform_orientation="ge",
+        threshold_corner_predicate="ordered lag unresolved", threshold_provenance=None, aggressor_derived=False,
+        unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
+    )
+    ordered_spec = _fixture_spec(
+        relation_kind="ordered_sequence_lag", coordinates=(ordered_coord,),
+        membership_corner="ordered_lag_unresolved",
+    )
+    try:
+        interpret_candidate(ordered_spec, [], econ_floor=_FIXTURE_ECON_FLOOR, family_id="f", n_variants_tried=1)
+    except UnsupportedRelationBlocked as exc:
+        block_reason = exc.disposition
+    else:  # pragma: no cover -- this relation kind is never supported
+        block_reason = None
+    scenarios.append(
+        {
+            "scenario_id": "fixture-unsupported-ordered-relation",
+            "kind": "unsupported_ordered_relation",
+            "foundry_screen": None,
+            "direct_scout_screen": None,
+            "screens_equal": None,
+            "unresolved_excluded_count": None,
+            "outcome_start_candidate": None,
+            "outcome_start_comparator": None,
+            "block_reason": block_reason,
+            "predeclared_sidedness": None,
+        }
+    )
+
+    return {"scenarios": scenarios}
diff --git a/apps/backend/app/research/foundry_runner.py b/apps/backend/app/research/foundry_runner.py
index 564106e2..e2df19dd 100644
--- a/apps/backend/app/research/foundry_runner.py
+++ b/apps/backend/app/research/foundry_runner.py
@@ -111,6 +111,19 @@ def run_one_candidate(
 
     existing_intent = ledger.intent_row_for(spec.candidate_spec_hash)
     if existing_intent is not None:
+        # Repair 2 (auditor B4, iter-4): mirrors the already-terminal fast path's own
+        # `manifest_hash` check three lines above (in the ``existing_terminal`` branch) -- the
+        # intent-without-terminal ("crash") branch previously verified ONLY `econ_floor_bps`,
+        # leaving a resumed candidate whose `manifest_hash` had drifted since the pinned intent row
+        # to re-execute silently under the wrong science identity. Checked FIRST, before the
+        # econ-floor check, for the same reason the terminal branch checks manifest identity before
+        # econ-floor identity: manifest drift is the coarser, more fundamental integrity failure.
+        if existing_intent["manifest_hash"] != manifest_hash:
+            raise FoundryResumeIdentityMismatch(
+                f"resume manifest_hash mismatch for candidate_spec_hash="
+                f"{spec.candidate_spec_hash!r}: pinned intent={existing_intent['manifest_hash']!r}, "
+                f"resumed with={manifest_hash!r}"
+            )
         if existing_intent["econ_floor_bps"] != econ_floor.get("floor_bps"):
             raise FoundryResumeIdentityMismatch(
                 f"resume econ_floor_bps mismatch for candidate_spec_hash="
diff --git a/apps/backend/app/research/foundry_source_registry.py b/apps/backend/app/research/foundry_source_registry.py
index efa15bfb..05e4516a 100644
--- a/apps/backend/app/research/foundry_source_registry.py
+++ b/apps/backend/app/research/foundry_source_registry.py
@@ -54,8 +54,10 @@ __all__ = [
     "SupersessionDeclaration",
     "SourceRecord",
     "QuoteMismatch",
+    "AlternativeReferenceInvalid",
     "compile_source_disposition",
     "lint_quoted_spans",
+    "lint_alternatives",
     "source_registry_hash",
     "resolve_foundry_dir",
     "record_era_open_baseline",
@@ -239,6 +241,51 @@ def lint_quoted_spans(records: Sequence[SourceRecord]) -> None:
                 )
 
 
+class AlternativeReferenceInvalid(Exception):
+    """Raised by ``lint_alternatives`` (never swallowed -- fail closed, spec §1.4). auditor B7
+    (carried from iter-3): the §1.4 ``alternatives`` disclosure is a scientific claim ("this
+    sibling is a legal alternative representation of the same mechanism") -- a stray id (typo,
+    stale rename, or a reference into an unrelated family) would silently misrepresent that claim
+    if nothing ever checked it, exactly like an unchecked ``QuotedSpan`` would misrepresent a
+    citation."""
+
+
+def lint_alternatives(records: Sequence[SourceRecord]) -> None:
+    """Fail-closed batch lint over ``SourceRecord.alternatives`` (spec §1.4's "every finite
+    alternative the compiler is allowed to enumerate"), alongside ``lint_quoted_spans`` above.
+    Every alternative a record names must:
+
+    1. exist as a ``source_id`` somewhere in THIS SAME batch of ``records`` -- an alternative
+       naming a record that isn't even being compiled cannot be a legal enumerated sibling;
+    2. share the naming record's own ``foundry_family_key`` -- a record with no family key at all
+       (``None``) has no family for a sibling to be "a member of", so ANY alternative it names is
+       invalid;
+    3. not equal the naming record's own ``source_id`` -- a record cannot be its own alternative.
+
+    Raises ``AlternativeReferenceInvalid`` on the first violation found (never silently drops or
+    ignores a bad reference) -- the same fail-closed discipline ``lint_quoted_spans`` already
+    applies to citations."""
+    by_id = {r.source_id: r for r in records}
+    for record in records:
+        for alt_id in record.alternatives:
+            if alt_id == record.source_id:
+                raise AlternativeReferenceInvalid(
+                    f"{record.source_id}: alternatives names its own source_id ({alt_id!r}) -- a "
+                    "record cannot be its own alternative"
+                )
+            alt_record = by_id.get(alt_id)
+            if alt_record is None:
+                raise AlternativeReferenceInvalid(
+                    f"{record.source_id}: alternatives names {alt_id!r}, which does not exist in "
+                    "this registry batch"
+                )
+            if record.foundry_family_key is None or alt_record.foundry_family_key != record.foundry_family_key:
+                raise AlternativeReferenceInvalid(
+                    f"{record.source_id}: alternatives names {alt_id!r}, which is not a member of "
+                    f"the same foundry_family_key ({record.foundry_family_key!r})"
+                )
+
+
 def compile_source_disposition(record: SourceRecord) -> str:
     """The §2 owner meta-policy, as one fixed precedence -- no branch below is keyed on which
     fixture archetype a caller thinks it is building; every decision reads only the record's own
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index c912ab05..bc20c47d 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -46,6 +46,10 @@ from .desk_playbook import PlaybookStore
 from .desk_playbook_context import BandMapResolver
 from .desk_routes import get_playbook_store, get_universe_store
 from .desk_universe import UniverseStore
+from .foundry_compiler import sources_compiler_hermetic_fixture_view
+from .foundry_freeze import freeze_integrity_hermetic_fixture_view
+from .foundry_hermetic_summary import build_hermetic_oracles_summary
+from .foundry_interpreter import interpreter_hermetic_fixture_view
 from .foundry_source_registry import (
     foundry_era_identity,
     read_era_open_baseline,
@@ -757,6 +761,19 @@ def get_foundry_dir() -> str:
     return resolve_foundry_dir(CONFIG.dataset_dir_resolved())
 
 
+# goal-hypothesis-foundry-iter-4 (J-02/J-03/J-04/J-05): the four consolidated Foundry read-surface
+# subviews -- computed EXACTLY ONCE, here, at module import time, from purely hermetic literals
+# (never real dataset/session state), and served verbatim on every request thereafter. This is
+# what keeps the route itself GET-never-computes (T-8 / goal.md anti-goal 10): the compiler/
+# interpreter/family/freeze/ledger/runner machinery those four builders invoke runs ONCE per
+# process, not once per request -- TC-19's own "two GET responses are byte-identical" proof holds
+# structurally (the same frozen dict object is returned both times), not by chance.
+_SOURCES_COMPILER_VIEW = sources_compiler_hermetic_fixture_view()
+_INTERPRETER_FIXTURES_VIEW = interpreter_hermetic_fixture_view()
+_FREEZE_INTEGRITY_VIEW = freeze_integrity_hermetic_fixture_view()
+_HERMETIC_ORACLES_VIEW = build_hermetic_oracles_summary()
+
+
 @router.get("/foundry")
 def get_foundry(foundry_dir: str = Depends(get_foundry_dir)) -> dict:
     """Serves era/session identity (``foundry_source_registry.foundry_era_identity`` -- a static
@@ -765,10 +782,19 @@ def get_foundry(foundry_dir: str = Depends(get_foundry_dir)) -> dict:
     never fabricated), and the explicit not-yet-generated `source_registry_hash` state. Never
     404/500 before that recording act runs -- the desk router's own never-404-on-absence
     convention: an honest ``era_open_baseline: null`` on a fresh install, exactly like ``GET
-    /vault``'s honest empty ``shards``/``universes`` before the first registration."""
+    /vault``'s honest empty ``shards``/``universes`` before the first registration.
+
+    goal-hypothesis-foundry-iter-4: four ADDITIVE top-level keys -- ``sources_compiler``,
+    ``interpreter_fixtures``, ``freeze_integrity``, ``hermetic_oracles`` -- each served VERBATIM
+    from the module-level frozen views built once above; this handler never calls any compiler/
+    interpreter/family/freeze/runner function itself."""
     return {
         "era": foundry_era_identity(),
         "era_open_baseline": read_era_open_baseline(foundry_dir),
         "source_registry_hash": None,
         "source_registry_status": "not_yet_generated",
+        "sources_compiler": _SOURCES_COMPILER_VIEW,
+        "interpreter_fixtures": _INTERPRETER_FIXTURES_VIEW,
+        "freeze_integrity": _FREEZE_INTEGRITY_VIEW,
+        "hermetic_oracles": _HERMETIC_ORACLES_VIEW,
     }
diff --git a/apps/backend/tests/test_foundry_compiler.py b/apps/backend/tests/test_foundry_compiler.py
index f3716fbc..3abb61a0 100644
--- a/apps/backend/tests/test_foundry_compiler.py
+++ b/apps/backend/tests/test_foundry_compiler.py
@@ -339,6 +339,24 @@ def test_compiled_record_with_a_deferred_coordinate_produces_no_candidate_spec_t
     assert "fixture-deferred" not in result.candidate_specs
 
 
+# --- TC-16 (goal-hypothesis-foundry-iter-4, Repair 1): `compile_sources` runs the alternatives
+# lint alongside the quoted-span lint, BEFORE building any CandidateSpec. ---------------------------
+
+
+def test_tc16_compile_sources_fails_closed_on_a_self_referential_alternative():
+    excerpt = "one self-referential alternatives fixture"
+    record = fsr.SourceRecord(
+        source_id="fixture-self-alt", source_path="docs/fixtures/mechanism.md", section_ref="3.1",
+        quoted_spans=(), source_excerpt=excerpt, mechanism_statement="m", operative_formula_refs=(),
+        direction_derivation="long", comparator_derivation="complement", audit_note="note",
+        foundry_family_key="fixture-self-alt-family", variant_ordinal=0, alternatives=("fixture-self-alt",),
+    )
+    with pytest.raises(fsr.AlternativeReferenceInvalid):
+        fc.compile_sources(
+            [record], foundry_spec_version="v1", epoch_id="e", blueprints={"fixture-self-alt": _blueprint()}
+        )
+
+
 def test_compiler_hash_is_stable_and_non_empty():
     h1 = fc.compiler_hash()
     h2 = fc.compiler_hash()
diff --git a/apps/backend/tests/test_foundry_runner.py b/apps/backend/tests/test_foundry_runner.py
index 872fa304..20330a7b 100644
--- a/apps/backend/tests/test_foundry_runner.py
+++ b/apps/backend/tests/test_foundry_runner.py
@@ -170,6 +170,35 @@ def test_tc9_already_terminal_fast_path_raises_on_econ_floor_drift(tmp_path):
         fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=drifted_floor, manifest_hash="m1", family=family)
 
 
+def test_tc17_intent_without_terminal_crash_path_raises_on_manifest_hash_drift(tmp_path):
+    """goal-hypothesis-foundry-iter-4 Repair 2 (auditor B4): the intent-without-terminal ("crash")
+    branch must ALSO verify the pinned intent row's own `manifest_hash` against the current
+    invocation's `manifest_hash` -- mirroring the already-terminal fast path's own check -- and
+    raise even when `econ_floor_bps` matches exactly."""
+    family = ff.build_family_registry({"family:crash-manifest-drift": ["family:crash-manifest-drift:0"]})[
+        "family:crash-manifest-drift"
+    ]
+    spec = _scalar_spec(0, family_id="family:crash-manifest-drift", family_count=1)
+    anchors = _anchors(10, effect_bps=45.0)
+    ledger = fl.FoundryLedger(tmp_path)
+
+    # Simulate the crash: an intent row pinned under manifest_hash="m1", no terminal row yet.
+    ledger.record_intent(
+        candidate_spec_hash=spec.candidate_spec_hash, manifest_hash="m1",
+        econ_floor_bps=_ECON_FLOOR["floor_bps"], econ_floor_provenance=_ECON_FLOOR["rule"],
+    )
+    assert ledger.terminal_row_for(spec.candidate_spec_hash) is None
+
+    # Resume with a DIFFERENT manifest_hash but the SAME (matching) econ_floor_bps -- must still
+    # halt on the manifest identity mismatch alone.
+    with pytest.raises(fr.FoundryResumeIdentityMismatch):
+        fr.run_one_candidate(
+            spec, anchors, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m2-drifted", family=family
+        )
+    # fail-closed: no terminal row was ever written for the mismatched resume attempt.
+    assert ledger.terminal_row_for(spec.candidate_spec_hash) is None
+
+
 def test_tc14_single_flight_lock_rejects_a_concurrent_second_runner(tmp_path):
     lock_path = tmp_path / "foundry_runner.lock"
     lock = fr.SingleFlightLock(lock_path)
diff --git a/apps/backend/tests/test_foundry_source_registry.py b/apps/backend/tests/test_foundry_source_registry.py
index 56b40edd..cca9befd 100644
--- a/apps/backend/tests/test_foundry_source_registry.py
+++ b/apps/backend/tests/test_foundry_source_registry.py
@@ -459,3 +459,61 @@ def test_source_registry_hash_changes_when_alternatives_changes():
     record = _good_record("alt-hash")
     with_alt = dataclasses.replace(record, alternatives=("some-sibling-source-id",))
     assert fsr.source_registry_hash([record]) != fsr.source_registry_hash([with_alt])
+
+
+# --- TC-16 (goal-hypothesis-foundry-iter-4, Repair 1 / auditor B7): `lint_alternatives` fails
+# closed on a nonexistent, wrong-family, or self-referential `alternatives` reference. -------------
+
+
+def _family_pair(alt_a: tuple[str, ...] = (), alt_b: tuple[str, ...] = ()) -> tuple[fsr.SourceRecord, fsr.SourceRecord]:
+    excerpt = "two already-defined legal outcome horizons enumerated per the frozen vocabulary."
+    span_text = "two already-defined legal outcome horizons"
+    record_a = fsr.SourceRecord(
+        source_id="lint-alt-a", source_path="docs/fixtures/mechanism.md", section_ref="4.1",
+        quoted_spans=(_span(span_text, excerpt),), source_excerpt=excerpt,
+        mechanism_statement="m", operative_formula_refs=(), direction_derivation="long",
+        comparator_derivation="complement", audit_note="note",
+        foundry_family_key="lint-alt-family", variant_ordinal=0, alternatives=alt_a,
+    )
+    record_b = fsr.SourceRecord(
+        source_id="lint-alt-b", source_path="docs/fixtures/mechanism.md", section_ref="4.1",
+        quoted_spans=(_span(span_text, excerpt),), source_excerpt=excerpt,
+        mechanism_statement="m", operative_formula_refs=(), direction_derivation="long",
+        comparator_derivation="complement", audit_note="note",
+        foundry_family_key="lint-alt-family", variant_ordinal=1, alternatives=alt_b,
+    )
+    return record_a, record_b
+
+
+def test_tc16_lint_alternatives_passes_over_a_legal_same_family_reference():
+    record_a, record_b = _family_pair(alt_a=("lint-alt-b",), alt_b=("lint-alt-a",))
+    fsr.lint_alternatives([record_a, record_b])  # must not raise
+
+
+def test_tc16_lint_alternatives_fails_closed_on_a_nonexistent_sibling():
+    record_a, record_b = _family_pair(alt_a=("does-not-exist",))
+    with pytest.raises(fsr.AlternativeReferenceInvalid):
+        fsr.lint_alternatives([record_a, record_b])
+
+
+def test_tc16_lint_alternatives_fails_closed_on_a_wrong_family_sibling():
+    outsider = _good_record("lint-alt-outsider")  # no foundry_family_key at all
+    record_a, record_b = _family_pair(alt_a=("lint-alt-outsider",))
+    with pytest.raises(fsr.AlternativeReferenceInvalid):
+        fsr.lint_alternatives([record_a, record_b, outsider])
+
+
+def test_tc16_lint_alternatives_fails_closed_on_a_self_reference():
+    record_a, record_b = _family_pair(alt_a=("lint-alt-a",))
+    with pytest.raises(fsr.AlternativeReferenceInvalid):
+        fsr.lint_alternatives([record_a, record_b])
+
+
+def test_tc16_lint_alternatives_rejects_any_alternative_when_naming_record_has_no_family_key():
+    solo = _good_record("lint-alt-no-family")
+    import dataclasses
+
+    with_alt = dataclasses.replace(solo, alternatives=("some-other-id",))
+    other = _good_record("some-other-id")
+    with pytest.raises(fsr.AlternativeReferenceInvalid):
+        fsr.lint_alternatives([with_alt, other])
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index eb9c00e9..b900d7ad 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -88,6 +88,10 @@ import type {
   DeskForwardTouch,
   DeskFoundryResponse,
   DeskGraduationResponse,
+  FoundryFreezeIntegrity,
+  FoundryHermeticOracles,
+  FoundryInterpreterFixtures,
+  FoundrySourcesCompiler,
   DeskMicroSnapshotRunsResponse,
   DeskMicroSnapshotsResponse,
   DeskPlaybookAbsence,
@@ -7364,17 +7368,360 @@ function FeatureSnapshotsSection({
   );
 }
 
+// goal-hypothesis-foundry-iter-4 (J-02/J-03/J-04/J-05): shared visual marker for every one of the
+// four new fixture subsections below -- visually distinct from the header's real
+// `foundry-era-open-baseline` block (Design Direction: audit-first, no promotional language;
+// anti-goal: "fixture and real views must be visibly distinguished").
+function HermeticFixtureBanner({ testid }: { testid: string }) {
+  return (
+    <p
+      data-testid={testid}
+      className="mb-3 inline-block rounded border border-amber-700/60 bg-amber-950/40 px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-amber-400"
+    >
+      Hermetic Fixture — not the real epoch
+    </p>
+  );
+}
+
+// goal-hypothesis-foundry-iter-4 (J-02): Sources/Compiler -- the 7 hermetic source-fixture
+// archetypes plus the immutability proof, rendered VERBATIM from `sources_compiler` (no
+// client-side recomputation).
+function SourcesCompilerSubsection({ data }: { data: FoundrySourcesCompiler }) {
+  return (
+    <div data-testid="foundry-sources-compiler">
+      <HermeticFixtureBanner testid="foundry-sources-compiler-hermetic-banner" />
+      <p className="mb-3 text-[11px] text-slate-500">
+        {data.fixtures.length} hermetic source fixtures compiled through the real{" "}
+        <span className="font-mono text-slate-400">foundry_compiler.compile_sources</span> — no
+        candidate outcome ever participates in compilation.
+      </p>
+
+      <div
+        data-testid="foundry-immutability-proof"
+        className="mb-4 grid grid-cols-1 gap-2 rounded border border-slate-800 bg-slate-950/40 p-2 sm:grid-cols-2"
+      >
+        <div>
+          <p className="mb-1 text-[10px] uppercase tracking-wider text-slate-600">Compiled with extra A</p>
+          <pre className="mb-1 overflow-x-auto whitespace-pre-wrap break-all text-[10px] text-slate-500">
+            {JSON.stringify(data.immutability_proof.injected_extra_a, null, 2)}
+          </pre>
+          <p className="break-all font-mono text-[10px] text-slate-400">
+            {data.immutability_proof.candidate_spec_hash_a}
+          </p>
+        </div>
+        <div>
+          <p className="mb-1 text-[10px] uppercase tracking-wider text-slate-600">Compiled with extra B</p>
+          <pre className="mb-1 overflow-x-auto whitespace-pre-wrap break-all text-[10px] text-slate-500">
+            {JSON.stringify(data.immutability_proof.injected_extra_b, null, 2)}
+          </pre>
+          <p className="break-all font-mono text-[10px] text-slate-400">
+            {data.immutability_proof.candidate_spec_hash_b}
+          </p>
+        </div>
+        <p
+          data-testid="foundry-immutability-proof-hashes-equal"
+          className={`text-[11px] font-semibold sm:col-span-2 ${
+            data.immutability_proof.hashes_equal ? "text-emerald-400" : "text-rose-400"
+          }`}
+        >
+          {data.immutability_proof.hashes_equal
+            ? "Hashes match — outcome-blind compilation proven."
+            : "Hashes differ — integrity violation."}
+        </p>
+      </div>
+
+      <ul data-testid="foundry-source-fixture-rows" className="space-y-2">
+        {data.fixtures.map((fixture) => (
+          <li key={fixture.source_id} className="rounded border border-slate-800 p-2">
+            <div className="mb-1 flex flex-wrap items-center gap-2 text-[11px]">
+              <span className="font-mono text-slate-300">{fixture.source_id}</span>
+              <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-400">
+                {fixture.disposition}
+              </span>
+            </div>
+            <p className="mb-1 text-[10px] text-slate-500">
+              {fixture.source_path}#{fixture.section_ref} — {fixture.mechanism_statement}
+            </p>
+            {fixture.quoted_spans.map((span, i) => (
+              <p key={i} className="mb-1 font-mono text-[10px] text-slate-600">
+                &ldquo;{span.text}&rdquo; @ {span.location}
+              </p>
+            ))}
+            <p className="mb-1 text-[10px] text-slate-500">
+              Direction: <span className="font-mono text-slate-400">{fixture.direction_derivation}</span>
+              {" · "}Threshold provenance:{" "}
+              <span className="font-mono text-slate-400">{fixture.threshold_provenance ?? "—"}</span>
+            </p>
+            {fixture.alternatives.length > 0 && (
+              <p className="mb-1 text-[10px] text-slate-500">
+                Alternatives: <span className="font-mono text-slate-400">{fixture.alternatives.join(", ")}</span>
+              </p>
+            )}
+            {fixture.block_reason && (
+              <p className="mb-1 text-[10px] text-amber-500">
+                Block reason: <span className="font-mono">{fixture.block_reason}</span>
+              </p>
+            )}
+            {fixture.candidate_spec && (
+              <details>
+                <summary className="cursor-pointer text-[10px] text-slate-600">CandidateSpec detail</summary>
+                <pre className="mt-1 max-w-[640px] overflow-x-auto whitespace-pre-wrap break-all text-[10px] text-slate-500">
+                  {JSON.stringify(fixture.candidate_spec, null, 2)}
+                </pre>
+              </details>
+            )}
+          </li>
+        ))}
+      </ul>
+    </div>
+  );
+}
+
+// goal-hypothesis-foundry-iter-4 (J-03): Interpreter fixtures -- the 5 hermetic interpretation
+// scenarios, rendered VERBATIM from `interpreter_fixtures`.
+function InterpreterFixturesSubsection({ data }: { data: FoundryInterpreterFixtures }) {
+  return (
+    <div data-testid="foundry-interpreter-fixtures">
+      <HermeticFixtureBanner testid="foundry-interpreter-fixtures-hermetic-banner" />
+      <ul data-testid="foundry-interpreter-scenario-rows" className="space-y-2">
+        {data.scenarios.map((scenario) => (
+          <li key={scenario.scenario_id} className="rounded border border-slate-800 p-2">
+            <div className="mb-1 flex flex-wrap items-center gap-2 text-[11px]">
+              <span className="font-mono text-slate-300">{scenario.scenario_id}</span>
+              <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-400">
+                {scenario.kind}
+              </span>
+            </div>
+            {scenario.screens_equal !== null && (
+              <p className="mb-1 text-[10px] text-slate-500">
+                Foundry vs. direct-Scout screens equal:{" "}
+                <span className={scenario.screens_equal ? "text-emerald-400" : "text-rose-400"}>
+                  {String(scenario.screens_equal)}
+                </span>
+              </p>
+            )}
+            {scenario.unresolved_excluded_count !== null && (
+              <p className="mb-1 text-[10px] text-slate-500">
+                Unresolved anchors excluded:{" "}
+                <span className="font-mono text-slate-400">{scenario.unresolved_excluded_count}</span>
+              </p>
+            )}
+            {scenario.outcome_start_candidate !== null && (
+              <p className="mb-1 text-[10px] text-slate-500">
+                outcome_start (candidate):{" "}
+                <span className="font-mono text-slate-400">{scenario.outcome_start_candidate}</span>
+                {" · "}(comparator):{" "}
+                <span className="font-mono text-slate-400">{scenario.outcome_start_comparator}</span>
+              </p>
+            )}
+            {scenario.predeclared_sidedness && (
+              <p className="mb-1 text-[10px] text-slate-500">
+                Predeclared sidedness — support/long:{" "}
+                <span className="font-mono text-emerald-400">{scenario.predeclared_sidedness.support_long}</span>
+                {" · "}resistance/short:{" "}
+                <span className="font-mono text-rose-400">{scenario.predeclared_sidedness.resistance_short}</span>
+              </p>
+            )}
+            {scenario.block_reason && (
+              <p className="mb-1 text-[10px] text-amber-500">
+                Typed block: <span className="font-mono">{scenario.block_reason}</span>
+              </p>
+            )}
+            {scenario.foundry_screen !== null && (
+              <details>
+                <summary className="cursor-pointer text-[10px] text-slate-600">Screen detail</summary>
+                <pre className="mt-1 max-w-[640px] overflow-x-auto whitespace-pre-wrap break-all text-[10px] text-slate-500">
+                  {JSON.stringify(scenario.foundry_screen, null, 2)}
+                </pre>
+              </details>
+            )}
+          </li>
+        ))}
+      </ul>
+    </div>
+  );
+}
+
+// goal-hypothesis-foundry-iter-4 (J-04): Freeze/Integrity -- the family denominator/late-insertion/
+// generation-replay/freeze-record/first-read-lock/replay fixture proofs, rendered VERBATIM from
+// `freeze_integrity`.
+function FreezeIntegritySubsection({ data }: { data: FoundryFreezeIntegrity }) {
+  return (
+    <div data-testid="foundry-freeze-integrity">
+      <HermeticFixtureBanner testid="foundry-freeze-integrity-hermetic-banner" />
+
+      <h5 className="mb-1 text-[11px] font-semibold text-slate-400">Family Denominator</h5>
+      <div className="mb-3 overflow-x-auto">
+        <table
+          data-testid="foundry-family-denominator-table"
+          className="w-full min-w-[420px] border-collapse text-[11px]"
+        >
+          <thead>
+            <tr className="border-b border-slate-800 text-left text-slate-500">
+              <th className="px-1.5 py-1">Family kind</th>
+              <th className="px-1.5 py-1">Variant count</th>
+              <th className="px-1.5 py-1">Denominator visible</th>
+              <th className="px-1.5 py-1">Over-cap blocked whole</th>
+            </tr>
+          </thead>
+          <tbody>
+            {data.family_denominator_fixtures.map((f) => (
+              <tr
+                key={f.family_kind}
+                className={`border-b border-slate-900 ${f.family_kind === "over_cap" ? "bg-rose-950/30" : ""}`}
+              >
+                <td className="px-1.5 py-1 font-mono text-slate-300">{f.family_kind}</td>
+                <td className="px-1.5 py-1 font-mono text-slate-400">{f.variant_count}</td>
+                <td className="px-1.5 py-1 font-mono text-slate-400">
+                  {String(f.denominator_visible_before_result)}
+                </td>
+                <td
+                  className={`px-1.5 py-1 font-mono ${
+                    f.over_cap_blocked_whole ? "text-rose-400" : "text-slate-500"
+                  }`}
+                >
+                  {String(f.over_cap_blocked_whole)}
+                </td>
+              </tr>
+            ))}
+          </tbody>
+        </table>
+      </div>
+
+      <p data-testid="foundry-late-insertion-refused" className="mb-1 text-[11px] text-slate-500">
+        Late insertion refused:{" "}
+        <span className="font-mono text-slate-300">{String(data.late_insertion_refused)}</span>
+      </p>
+      <p data-testid="foundry-generation-replay" className="mb-3 text-[11px] text-slate-500">
+        Generation replay — identical rerun verified:{" "}
+        <span className="font-mono text-slate-300">{String(data.generation_replay.identical_rerun_verified)}</span>
+        {" · "}drifted rerun refused:{" "}
+        <span className="font-mono text-slate-300">{String(data.generation_replay.drifted_rerun_refused)}</span>
+      </p>
+
+      <div
+        data-testid="foundry-freeze-record"
+        className="mb-3 rounded border border-slate-800 p-2 text-[11px] text-slate-500"
+      >
+        <p className="mb-1">
+          Freeze-set target path (fixture-scoped; not yet the real committed file):{" "}
+          <span className="font-mono text-amber-400">{data.freeze_record.freeze_set_target_path}</span>
+        </p>
+        <p className="mb-1 break-all">
+          Freeze-set hash:{" "}
+          <span className="font-mono text-[10px] text-slate-400">{data.freeze_record.freeze_set_hash}</span>
+        </p>
+        <p className="mb-1">
+          Transitive dependency coverage complete:{" "}
+          <span className="font-mono text-slate-300">
+            {String(data.freeze_record.transitive_dependency_coverage_complete)}
+          </span>
+        </p>
+        <details>
+          <summary className="cursor-pointer text-[10px] text-slate-600">Pinned module hashes</summary>
+          <pre className="mt-1 max-w-[640px] overflow-x-auto whitespace-pre-wrap break-all text-[10px] text-slate-500">
+            {JSON.stringify(data.freeze_record.pinned_hashes, null, 2)}
+          </pre>
+        </details>
+      </div>
+
+      <p data-testid="foundry-first-read-lock" className="mb-1 text-[11px] text-slate-500">
+        First-read lock — hash drift refused:{" "}
+        <span className="font-mono text-slate-300">{String(data.first_read_lock.hash_drift_refused)}</span>
+        {" · "}session dirt ignored:{" "}
+        <span className="font-mono text-slate-300">{String(data.first_read_lock.session_dirt_ignored)}</span>
+        {" · "}non-science file exempted:{" "}
+        <span className="font-mono text-slate-300">{String(data.first_read_lock.non_science_file_exempted)}</span>
+      </p>
+      <p data-testid="foundry-replay-integrity" className="text-[11px] text-slate-500">
+        Replay — idempotent:{" "}
+        <span className="font-mono text-slate-300">{String(data.replay.idempotent)}</span>
+        {" · "}conflicting replay refused:{" "}
+        <span className="font-mono text-slate-300">{String(data.replay.conflicting_replay_refused)}</span>
+        {" · "}concurrent runner refused:{" "}
+        <span className="font-mono text-slate-300">{String(data.replay.concurrent_runner_refused)}</span>
+      </p>
+    </div>
+  );
+}
+
+// goal-hypothesis-foundry-iter-4 (J-05): Hermetic Oracles -- the outcome-type coverage, denominator
+// -consistency/canonical-order flags, and the five named oracle pass/fail results, rendered
+// VERBATIM from `hermetic_oracles`.
+function HermeticOraclesSubsection({ data }: { data: FoundryHermeticOracles }) {
+  const namedOracles: { label: string; ok: boolean }[] = [
+    { label: "All-blocked epoch completed", ok: data.all_blocked_epoch_completed },
+    { label: "All-killed epoch completed", ok: data.all_killed_epoch_completed },
+    { label: "Multi-survivor preserved all", ok: data.multi_survivor_preserved_all },
+    { label: "Crash-resume at scale verified", ok: data.crash_resume_at_scale_verified },
+    {
+      label: "Protected-data trip fails closed / evidence class immutable",
+      ok: data.protected_data_trip_fails_closed && data.evidence_class_immutable,
+    },
+  ];
+  return (
+    <div data-testid="foundry-hermetic-oracles">
+      <HermeticFixtureBanner testid="foundry-hermetic-oracles-hermetic-banner" />
+      <p className="mb-2 text-[11px] text-slate-500">
+        Reads genuine outcomes from{" "}
+        <span className="font-mono text-slate-400">{data.suite_source}</span>&apos;s already
+        -hermetically-proven composite suite — never a second, hand-typed oracle.
+      </p>
+      <p data-testid="foundry-outcome-types-present" className="mb-2 text-[11px] text-slate-500">
+        Outcome types present:{" "}
+        <span className="font-mono text-slate-300">{data.outcome_types_present.join(", ")}</span>
+      </p>
+      <p data-testid="foundry-hermetic-oracle-flags" className="mb-3 text-[11px] text-slate-500">
+        Denominator consistent across rows:{" "}
+        <span className="font-mono text-slate-300">{String(data.denominator_consistent_across_rows)}</span>
+        {" · "}Canonical order preserved:{" "}
+        <span className="font-mono text-slate-300">{String(data.canonical_order_preserved)}</span>
+      </p>
+      <ul data-testid="foundry-named-oracle-rows" className="space-y-1">
+        {namedOracles.map((oracle) => (
+          <li key={oracle.label} className="flex items-center gap-2 text-[11px]">
+            <span className={`font-mono ${oracle.ok ? "text-emerald-400" : "text-rose-400"}`}>
+              {oracle.ok ? "PASS" : "FAIL"}
+            </span>
+            <span className="text-slate-400">{oracle.label}</span>
+          </li>
+        ))}
+      </ul>
+    </div>
+  );
+}
+
 // goal-hypothesis-foundry-iter-1 (J-01): the Hypothesis Foundry panel header -- era/session
 // identity + the era-open baseline, rendered VERBATIM from `GET /research/desk/micro/foundry`
 // (no client-side recomputation, per the goal's own Product Shape). The `foundry-panel`
-// data-testid family this iteration's IN SCOPE names; every other Foundry subview (Sources/
-// Compiler, Interpreter, Freeze/Integrity, ...) is deferred to a later, consolidated
-// read-surface iteration (Binding Execution Order step 5).
+// data-testid family this iteration's IN SCOPE names.
+//
+// goal-hypothesis-foundry-iter-4 (J-02/J-03/J-04/J-05): grows to render the four new subsections
+// below the era-open baseline -- Sources/Compiler, Interpreter fixtures, Freeze/Integrity, and
+// Hermetic Oracles -- each its own nested `CollapsibleSection` reusing the sibling pattern already
+// used for `hypothesisFoundry` and every other desk section. Local `useState` toggle state (never
+// lifted to the page-level `expandedSections`/`DeskCollapsibleSection` union, which only tracks
+// TOP-LEVEL desk sections) since these are nested, deferred-body sub-toggles scoped entirely to
+// this one component.
 function HypothesisFoundrySection({
   foundryResult,
 }: {
   foundryResult: { ok: boolean; data: DeskFoundryResponse | null; error?: string } | null;
 }) {
+  // Hooks run unconditionally, before the early returns below (Rules of Hooks) -- four
+  // independent nested-subsection toggles, all starting closed.
+  const [openSubsections, setOpenSubsections] = useState<ReadonlySet<string>>(new Set());
+  function toggleSubsection(id: string) {
+    setOpenSubsections((prev) => {
+      const next = new Set(prev);
+      if (next.has(id)) {
+        next.delete(id);
+      } else {
+        next.add(id);
+      }
+      return next;
+    });
+  }
   if (foundryResult === null) {
     return (
       <div data-testid="foundry-panel">
@@ -7477,6 +7824,47 @@ function HypothesisFoundrySection({
           </div>
         )}
       </div>
+
+      {/* goal-hypothesis-foundry-iter-4 (J-02/J-03/J-04/J-05): the four new fixture subsections --
+          nested CollapsibleSections, each its own GET-never-computes read of an ADDITIVE key on
+          the SAME already-fetched `foundry` payload (no second fetch). */}
+      <div className="mt-4 space-y-3">
+        <CollapsibleSection
+          id="foundry-sources-compiler-section"
+          title="Sources / Compiler"
+          open={openSubsections.has("sources-compiler")}
+          onToggle={() => toggleSubsection("sources-compiler")}
+        >
+          <SourcesCompilerSubsection data={foundry.sources_compiler} />
+        </CollapsibleSection>
+
+        <CollapsibleSection
+          id="foundry-interpreter-fixtures-section"
+          title="Interpreter Fixtures"
... [diff_bound] apps/frontend/app/desk/page.tsx: 27 more diff lines omitted — Read the file for full detail
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 1d7403f0..2f1a969e 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -2983,6 +2983,145 @@ export interface FoundryEraOpenBaseline {
   referee_module_sha256: Record<string, string>;
 }
 
+// goal-hypothesis-foundry-iter-4 (J-02): one §1.4 source-record fixture entry -- the full
+// `_canonical_source_record` field set plus `disposition` and either `candidate_spec` (compiled)
+// or `block_reason` (every other disposition).
+export interface FoundrySourceFixture {
+  source_id: string;
+  source_path: string;
+  section_ref: string;
+  quoted_spans: { text: string; location: number }[];
+  source_excerpt: string;
+  mechanism_statement: string;
+  operative_formula_refs: string[];
+  direction_derivation: string;
+  comparator_derivation: string;
+  lineage_id: string | null;
+  foundry_family_key: string | null;
+  variant_ordinal: number | null;
+  threshold_provenance: string | null;
+  unresolved_magnitude_words: string[];
+  superseded_fields: Record<string, string>;
+  proxy_of: { parked_study_source_id: string; do_not: string } | null;
+  supersession: { newer_source_ref: string; alias_kind: string } | null;
+  explicit_exclusion: string | null;
+  aliases_lineage_ids: string[];
+  alternatives: string[];
+  source_hash: string;
+  disposition: string;
+  candidate_spec: FoundryCandidateSpecView | null;
+  block_reason: string | null;
+}
+
+// The existing `CandidateSpec` dataclass's own field set, rendered verbatim (§3).
+export interface FoundryCandidateSpecView {
+  foundry_spec_version: string;
+  epoch_id: string;
+  source_ids: string[];
+  lineage_id: string;
+  foundry_family_id: string;
+  variant_id: string;
+  variant_ordinal: number;
+  population: { structure_context_kind: string; side_filter: string | null; setup_context_id: string | null };
+  coordinates: {
+    feature_construct_id: string;
+    semantic_role: string;
+    transform_orientation: string;
+    threshold_corner_predicate: string;
+    threshold_provenance: string | null;
+    aggressor_derived: boolean;
+    unit_basis: string;
+    anchor_at: string;
+    available_at: string;
+    resolution_join_rule: string;
+  }[];
+  relation: { kind: string; parameters: Record<string, unknown> };
+  membership_corner: string;
+  outcome: { horizon_key: string; sidedness: string; measure: string };
+  economic_floor_rule: { rule: string; multiple: number; numeric_floor_bps: number | null };
+  foundry_family_variant_count: number;
+  availability_rule: string;
+  unresolved_component_policy: string;
+  comparator: string;
+  manifest_hash: string | null;
+  source_registry_hash: string;
+  compiler_hash: string;
+  candidate_spec_hash: string;
+}
+
+export interface FoundrySourcesCompiler {
+  fixtures: FoundrySourceFixture[];
+  immutability_proof: {
+    source_id: string;
+    candidate_spec_hash_a: string;
+    candidate_spec_hash_b: string;
+    injected_extra_a: Record<string, unknown>;
+    injected_extra_b: Record<string, unknown>;
+    hashes_equal: boolean;
+  };
+}
+
+// goal-hypothesis-foundry-iter-4 (J-03): one interpreter fixture scenario.
+export interface FoundryInterpreterScenario {
+  scenario_id: string;
+  kind:
+    | "immediate_scalar_equivalence"
+    | "conjunction"
+    | "deferred_refill_consistent"
+    | "mirrored_direction"
+    | "unsupported_ordered_relation";
+  foundry_screen: Record<string, unknown> | null;
+  direct_scout_screen: Record<string, unknown> | null;
+  screens_equal: boolean | null;
+  unresolved_excluded_count: number | null;
+  outcome_start_candidate: string | null;
+  outcome_start_comparator: string | null;
+  block_reason: string | null;
+  predeclared_sidedness: { support_long: string; resistance_short: string } | null;
+}
+
+export interface FoundryInterpreterFixtures {
+  scenarios: FoundryInterpreterScenario[];
+}
+
+// goal-hypothesis-foundry-iter-4 (J-04): the freeze/family/integrity fixture summary.
+export interface FoundryFreezeIntegrity {
+  family_denominator_fixtures: {
+    family_kind: "single" | "multiple" | "at_cap" | "over_cap";
+    variant_count: number;
+    denominator_visible_before_result: boolean;
+    over_cap_blocked_whole: boolean | null;
+  }[];
+  late_insertion_refused: boolean;
+  generation_replay: { identical_rerun_verified: boolean; drifted_rerun_refused: boolean };
+  freeze_record: {
+    freeze_set_target_path: string;
+    freeze_set_hash: string;
+    pinned_hashes: Record<string, string>;
+    transitive_dependency_coverage_complete: boolean;
+  };
+  first_read_lock: {
+    hash_drift_refused: boolean;
+    session_dirt_ignored: boolean;
+    non_science_file_exempted: boolean;
+  };
+  replay: { idempotent: boolean; conflicting_replay_refused: boolean; concurrent_runner_refused: boolean };
+}
+
+// goal-hypothesis-foundry-iter-4 (J-05): the hermetic oracle-suite summary.
+export interface FoundryHermeticOracles {
+  outcome_types_present: string[];
+  denominator_consistent_across_rows: boolean;
+  canonical_order_preserved: boolean;
+  all_blocked_epoch_completed: boolean;
+  all_killed_epoch_completed: boolean;
+  multi_survivor_preserved_all: boolean;
+  crash_resume_at_scale_verified: boolean;
+  protected_data_trip_fails_closed: boolean;
+  evidence_class_immutable: boolean;
+  suite_source: string;
+}
+
 export interface DeskFoundryResponse {
   era: FoundryEraIdentity;
   // `null` on a fresh install before the operator's one-time recording act has run -- never
@@ -2990,4 +3129,11 @@ export interface DeskFoundryResponse {
   era_open_baseline: FoundryEraOpenBaseline | null;
   source_registry_hash: string | null;
   source_registry_status: string;
+  // goal-hypothesis-foundry-iter-4: four additive read-surface subviews -- all HERMETIC FIXTURE
+  // proofs of the compiler/interpreter/freeze/family/ledger/hermetic-oracle machinery; never real
+  // epoch/candidate data (that remains J-06/J-07).
+  sources_compiler: FoundrySourcesCompiler;
+  interpreter_fixtures: FoundryInterpreterFixtures;
+  freeze_integrity: FoundryFreezeIntegrity;
+  hermetic_oracles: FoundryHermeticOracles;
 }
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-hypothesis-foundry/telemetry.jsonl   | 6 ++++++
 runs/goal-session-hypothesis-foundry/trace/trace.jsonl | 1 +
 2 files changed, 7 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
