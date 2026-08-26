# Iteration diff (bounded)

Files changed: 7. Shown in full: 6.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_foundry_hermetic_epoch.py` (285 lines not shown)

```diff
diff --git a/apps/backend/app/research/foundry_runner.py b/apps/backend/app/research/foundry_runner.py
index ce9f3bdc..564106e2 100644
--- a/apps/backend/app/research/foundry_runner.py
+++ b/apps/backend/app/research/foundry_runner.py
@@ -3,14 +3,18 @@ built by the other four ``foundry_*.py`` modules over one hermetic manifest in c
 Foundry family order, then variant ordinal within family (§9.1) -- never reordered by effect,
 p-value, n, or a sibling's own verdict.
 
-**Scope this iteration (goal-hypothesis-foundry-iter-2).** This module operates on hermetic
-fixture epoch ids only (module docstring convention shared with every sibling ``foundry_*.py``
-this iteration) -- there is no real freeze/manifest wiring yet, so the post-first-read-lock
-science-hash verification this module will eventually need before EVERY resumed candidate
-(``foundry_freeze.verify_freeze_set_unchanged``) is not yet called from here; that wiring is real-
-epoch (J-06/J-07) territory. What IS in scope and proven here is the one identity this era's
-hermetic runner already has something meaningful to verify on resume: the pinned intent row's own
-economic-floor pin (§6/TC-51) -- see ``FoundryResumeIdentityMismatch`` below."""
+**Scope this iteration (goal-hypothesis-foundry-iter-2/iter-3).** This module operates on
+hermetic fixture epoch ids only (module docstring convention shared with every sibling
+``foundry_*.py`` this iteration) -- there is no real freeze/manifest wiring yet, so the
+post-first-read-lock science-hash verification this module will eventually need before EVERY
+resumed candidate (``foundry_freeze.verify_freeze_set_unchanged``) is not yet called from here;
+that wiring is real-epoch (J-06/J-07) territory. What IS in scope and proven here is the identity
+this era's hermetic runner already has something meaningful to verify on resume: BOTH the
+already-terminal fast path (``manifest_hash`` off the stored terminal row itself,
+``econ_floor_bps`` off its own pinned intent row) and the intent-without-terminal/crash path
+(``econ_floor_bps`` off the pinned intent row) -- see ``FoundryResumeIdentityMismatch`` below
+(§6/TC-51 in iter-2; the already-terminal half closed in iter-3 per the carried resume-identity
+gap the iter-2 review/coherence-audit flagged)."""
 
 from __future__ import annotations
 
@@ -73,8 +77,10 @@ def run_one_candidate(
 ) -> dict:
     """One candidate's full §9.2 resume-aware lifecycle:
 
-    - already-terminal (a prior run, or THIS run's own already-appended row) -> verify identity and
-      return the existing row WITHOUT re-executing the screen (TC-14's "verify and skip");
+    - already-terminal (a prior run, or THIS run's own already-appended row) -> verify identity
+      (``manifest_hash`` off the terminal row itself, ``econ_floor_bps`` off its own pinned intent
+      row -- TC-9, iter-3's closed resume-identity gap) and return the existing row WITHOUT
+      re-executing the screen (TC-14's "verify and skip");
     - an intent row exists with no terminal result (a simulated crash) -> verify the intent row's
       own pinned econ-floor identity against what THIS invocation was given (halting on mismatch --
       TC-51), then deterministically re-execute the exact same screen and append exactly one
@@ -88,6 +94,19 @@ def run_one_candidate(
     alone, exactly as §9.2 requires."""
     existing_terminal = ledger.terminal_row_for(spec.candidate_spec_hash)
     if existing_terminal is not None:
+        if existing_terminal["manifest_hash"] != manifest_hash:
+            raise FoundryResumeIdentityMismatch(
+                f"resume manifest_hash mismatch for candidate_spec_hash="
+                f"{spec.candidate_spec_hash!r}: terminal={existing_terminal['manifest_hash']!r}, "
+                f"resumed with={manifest_hash!r}"
+            )
+        pinned_intent = ledger.intent_row_for(spec.candidate_spec_hash)
+        if pinned_intent is not None and pinned_intent["econ_floor_bps"] != econ_floor.get("floor_bps"):
+            raise FoundryResumeIdentityMismatch(
+                f"resume econ_floor_bps mismatch for candidate_spec_hash="
+                f"{spec.candidate_spec_hash!r}: pinned intent={pinned_intent['econ_floor_bps']!r}, "
+                f"resumed with={econ_floor.get('floor_bps')!r}"
+            )
         return existing_terminal
 
     existing_intent = ledger.intent_row_for(spec.candidate_spec_hash)
diff --git a/apps/backend/app/research/foundry_source_registry.py b/apps/backend/app/research/foundry_source_registry.py
index 3dde0c6c..efa15bfb 100644
--- a/apps/backend/app/research/foundry_source_registry.py
+++ b/apps/backend/app/research/foundry_source_registry.py
@@ -186,6 +186,18 @@ class SourceRecord:
     # fixture field lives here and provably cannot move a disposition or a CandidateSpec hash,
     # because nothing below ever looks at this mapping.
     extra: Mapping[str, object] = field(default_factory=dict)
+    # §1.4 (goal.md): "every finite alternative the compiler is allowed to enumerate" -- a
+    # per-record disclosure naming the source_id(s) of the sibling representation(s) this record
+    # legally alternates with. Additive on top of, never a replacement for, `foundry_family_key`
+    # membership (the mechanism that actually lets the compiler enumerate them, spec §2.1) -- an
+    # auditor reading ONE record in isolation should not have to reconstruct family membership
+    # elsewhere to see what its legal alternatives are. Empty when no ratified alternative exists.
+    alternatives: tuple[str, ...] = ()
+    # `sha256(source_excerpt)` -- `init=False` so it can never be caller-supplied (and therefore
+    # never drift from `source_excerpt`): `__post_init__` below recomputes it fresh on every
+    # construction, mirroring `source_registry_hash`'s own "always recomputed, never cached"
+    # determinism discipline one level up (spec §1.4).
+    source_hash: str = field(init=False, default="")
 
     def __post_init__(self) -> None:
         if self.threshold_provenance is not None and self.threshold_provenance not in LEGAL_THRESHOLD_PROVENANCES:
@@ -204,6 +216,7 @@ class SourceRecord:
             DISPOSITION_EXCLUDED_GATE_CLOSED,
         ):
             raise ValueError(f"{self.source_id}: explicit_exclusion must be one of the three EXCLUDED_* dispositions")
+        object.__setattr__(self, "source_hash", hashlib.sha256(self.source_excerpt.encode("utf-8")).hexdigest())
 
 
 class QuoteMismatch(Exception):
@@ -279,6 +292,11 @@ def _canonical_source_record(record: SourceRecord) -> dict:
         ),
         "explicit_exclusion": record.explicit_exclusion,
         "aliases_lineage_ids": list(record.aliases_lineage_ids),
+        "alternatives": list(record.alternatives),
+        # `source_hash` is deliberately EXCLUDED here -- it is a pure derivation of
+        # `source_excerpt` (already present above), so including it would only echo information
+        # this projection already carries, exactly like `CandidateSpec._canonical_fields` excludes
+        # `candidate_spec_hash` from its own hash input one level down.
     }
 
 
diff --git a/apps/backend/tests/test_foundry_compiler.py b/apps/backend/tests/test_foundry_compiler.py
index fdba6f9b..f3716fbc 100644
--- a/apps/backend/tests/test_foundry_compiler.py
+++ b/apps/backend/tests/test_foundry_compiler.py
@@ -1,7 +1,11 @@
 """``foundry_compiler.py`` -- the Hypothesis Foundry's ``CandidateSpec`` schema and batch compiler
 (goal-hypothesis-foundry-iter-1). Test-first contract: TC-3, TC-4, TC-10, TC-11 in
 ``docs/phases/goal-hypothesis-foundry-iter-1.md``. TC-5 through TC-9/TC-12 (the blocked/aliased/
-lint cases) live in ``test_foundry_source_registry.py`` -- those need no ``CandidateBlueprint``."""
+lint cases) live in ``test_foundry_source_registry.py`` -- those need no ``CandidateBlueprint``.
+
+TC-11 in ``docs/phases/goal-hypothesis-foundry-iter-3.md`` (a distinct, later TC-11 -- the
+``alternatives`` field) extends the SAME two-frozen-legal-variant fixture pair this file's own
+iter-1 TC-4 already uses, below."""
 
 from __future__ import annotations
 
@@ -79,7 +83,7 @@ def test_tc3_natural_boundary_scalar_compiles_to_a_candidate_spec_with_a_hash():
 # foundry_family_variant_count == 2, and have distinct variant_ordinal values. --------------------
 
 
-def _variant_record(source_id: str, ordinal: int) -> fsr.SourceRecord:
+def _variant_record(source_id: str, ordinal: int, *, alternatives: tuple[str, ...] = ()) -> fsr.SourceRecord:
     excerpt = f"{source_id}: trades_20 and trades_100 are both already-legal outcome horizons."
     span_text = "trades_20 and trades_100 are both already-legal outcome horizons"
     return fsr.SourceRecord(
@@ -95,6 +99,7 @@ def _variant_record(source_id: str, ordinal: int) -> fsr.SourceRecord:
         audit_note="two already-defined legal outcome horizons enumerated per the frozen vocabulary, §2.1",
         foundry_family_key="fixture-family-horizon-variants",
         variant_ordinal=ordinal,
+        alternatives=alternatives,
     )
 
 
@@ -119,6 +124,34 @@ def test_tc4_two_legal_variants_share_family_and_have_distinct_ordinals():
     assert {spec_a.variant_ordinal, spec_b.variant_ordinal} == {0, 1}
 
 
+# --- TC-11 (goal-hypothesis-foundry-iter-3): the SAME two-frozen-legal-variant fixture pair
+# populates `alternatives` naming each other as the sibling representation; a fixture with no
+# ratified alternative (the natural-boundary-scalar record used by TC-3, above) shows an empty
+# tuple -- confirmed already by test_foundry_source_registry.py's own default-empty-tuple test. ---
+
+
+def test_tc11_two_legal_variants_name_each_other_as_their_alternative():
+    record_a = _variant_record("fixture-variant-alt-a", 0, alternatives=("fixture-variant-alt-b",))
+    record_b = _variant_record("fixture-variant-alt-b", 1, alternatives=("fixture-variant-alt-a",))
+    assert record_a.alternatives == ("fixture-variant-alt-b",)
+    assert record_b.alternatives == ("fixture-variant-alt-a",)
+
+    # additive, not a replacement: BOTH the family-key mechanism and the alternatives disclosure
+    # agree about the same two siblings.
+    result = fc.compile_sources(
+        [record_a, record_b],
+        foundry_spec_version="v1",
+        epoch_id="hermetic-fixture-epoch",
+        blueprints={
+            "fixture-variant-alt-a": _blueprint(horizon="trades_20"),
+            "fixture-variant-alt-b": _blueprint(horizon="trades_100"),
+        },
+    )
+    spec_a = result.candidate_specs["fixture-variant-alt-a"]
+    spec_b = result.candidate_specs["fixture-variant-alt-b"]
+    assert spec_a.foundry_family_id == spec_b.foundry_family_id  # same family the alternatives agree with
+
+
 def test_family_ordinal_collision_is_refused():
     record_a = _variant_record("fixture-collide-a", 0)
     record_b = _variant_record("fixture-collide-b", 0)  # SAME ordinal, same family -- illegal
diff --git a/apps/backend/tests/test_foundry_runner.py b/apps/backend/tests/test_foundry_runner.py
index 90ab2851..872fa304 100644
--- a/apps/backend/tests/test_foundry_runner.py
+++ b/apps/backend/tests/test_foundry_runner.py
@@ -1,7 +1,9 @@
 """``foundry_runner.py`` (goal-hypothesis-foundry-iter-2, J-04/J-03 integration): canonical-order
 exhaustion, mechanical Scout-verdict mapping, and checkpoint/resume/single-flight (spec §7.2/§9).
 TC-14 (runner-level parts)/TC-15/TC-16/TC-17 in
-``docs/phases/goal-hypothesis-foundry-iter-2.md``."""
+``docs/phases/goal-hypothesis-foundry-iter-2.md``. TC-9 in
+``docs/phases/goal-hypothesis-foundry-iter-3.md`` (the already-terminal fast path's resume-identity
+re-verification, closing the gap iter-2's own review/coherence-audit carried forward)."""
 
 from __future__ import annotations
 
@@ -140,6 +142,34 @@ def test_tc51_resume_econ_floor_mismatch_halts(tmp_path):
         fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m1", family=family)
 
 
+def test_tc9_already_terminal_fast_path_raises_on_manifest_hash_drift(tmp_path):
+    """iter-3's closed resume-identity gap: a resumed already-terminal candidate whose caller now
+    supplies a DIFFERENT ``manifest_hash`` than the one stored on its own terminal row must halt,
+    never silently return the stale row."""
+    family = ff.build_family_registry({"family:drift-manifest": ["family:drift-manifest:0"]})["family:drift-manifest"]
+    spec = _scalar_spec(0, family_id="family:drift-manifest", family_count=1)
+    anchors = _anchors(8, effect_bps=50.0)
+    ledger = fl.FoundryLedger(tmp_path)
+    fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m1", family=family)
+
+    with pytest.raises(fr.FoundryResumeIdentityMismatch):
+        fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m2-drifted", family=family)
+
+
+def test_tc9_already_terminal_fast_path_raises_on_econ_floor_drift(tmp_path):
+    """Same gap, the other pinned identity: a resumed already-terminal candidate whose caller now
+    supplies a DIFFERENT ``econ_floor_bps`` than the one pinned on its own intent row must halt."""
+    family = ff.build_family_registry({"family:drift-floor": ["family:drift-floor:0"]})["family:drift-floor"]
+    spec = _scalar_spec(0, family_id="family:drift-floor", family_count=1)
+    anchors = _anchors(9, effect_bps=50.0)
+    ledger = fl.FoundryLedger(tmp_path)
+    fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m1", family=family)
+
+    drifted_floor = {**_ECON_FLOOR, "floor_bps": 999.0}
+    with pytest.raises(fr.FoundryResumeIdentityMismatch):
+        fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=drifted_floor, manifest_hash="m1", family=family)
+
+
 def test_tc14_single_flight_lock_rejects_a_concurrent_second_runner(tmp_path):
     lock_path = tmp_path / "foundry_runner.lock"
     lock = fr.SingleFlightLock(lock_path)
diff --git a/apps/backend/tests/test_foundry_source_registry.py b/apps/backend/tests/test_foundry_source_registry.py
index 8316d6c8..56b40edd 100644
--- a/apps/backend/tests/test_foundry_source_registry.py
+++ b/apps/backend/tests/test_foundry_source_registry.py
@@ -8,7 +8,11 @@ Fixtures cover exactly the seven hermetic source archetypes ``docs/goal.md`` J-0
 Each fixture's ``source_excerpt``/``quoted_spans`` are deliberately synthetic sentences invented
 for this test -- never real ratified repository text -- since J-02 step 2 explicitly scopes this
 iteration to compiler-RULE machinery proven on hermetic fixtures, not the real 11 required source
-objects (that is J-06)."""
+objects (that is J-06).
+
+TC-10 (``docs/phases/goal-hypothesis-foundry-iter-3.md``) covers the ``source_hash``/
+``alternatives`` fields added this iteration; the two-frozen-legal-variant ``alternatives`` case
+(TC-11) lives in ``test_foundry_compiler.py`` beside the fixture pair it extends."""
 
 from __future__ import annotations
 
@@ -408,3 +412,50 @@ def test_resolve_foundry_dir_defaults_to_a_sibling_of_dataset_dir(monkeypatch, t
     monkeypatch.delenv("TAPEOLOGY_FOUNDRY_DIR", raising=False)
     dataset_dir = str(tmp_path / "datasets")
     assert fsr.resolve_foundry_dir(dataset_dir) == str(tmp_path / "foundry")
+
+
+# --- TC-10 (goal-hypothesis-foundry-iter-3): source_hash == sha256(source_excerpt), recomputed --
+# never caller-supplied -- so it can never drift from source_excerpt. -----------------------------
+
+
+def test_tc10_source_hash_is_sha256_of_source_excerpt():
+    import hashlib
+
+    record = _good_record("hash-check")
+    assert record.source_hash == hashlib.sha256(record.source_excerpt.encode("utf-8")).hexdigest()
+
+
+def test_tc10_source_hash_changes_when_source_excerpt_changes():
+    import dataclasses
+    import hashlib
+
+    record = _good_record("hash-mutation")
+    original_hash = record.source_hash
+    mutated = dataclasses.replace(record, source_excerpt=record.source_excerpt + " (a mutated tail)")
+    assert mutated.source_hash != original_hash
+    assert mutated.source_hash == hashlib.sha256(mutated.source_excerpt.encode("utf-8")).hexdigest()
+
+
+def test_tc10_source_hash_is_not_a_constructor_parameter():
+    """`source_hash` is `init=False` -- a caller cannot pass a value for it at all (it can only be
+    derived), so a stale/forged hash can never be smuggled in at construction time."""
+    import inspect
+
+    assert "source_hash" not in inspect.signature(fsr.SourceRecord.__init__).parameters
+
+
+# --- `alternatives` (goal-hypothesis-foundry-iter-3): defaults to empty; participates in the
+# registry hash (real disclosure content, unlike the derived `source_hash`). --------------------
+
+
+def test_alternatives_defaults_to_an_empty_tuple_when_no_ratified_alternative_exists():
+    record = _good_record("no-alternative")
+    assert record.alternatives == ()
+
+
+def test_source_registry_hash_changes_when_alternatives_changes():
+    import dataclasses
+
+    record = _good_record("alt-hash")
+    with_alt = dataclasses.replace(record, alternatives=("some-sibling-source-id",))
+    assert fsr.source_registry_hash([record]) != fsr.source_registry_hash([with_alt])
diff --git a/docs/hypothesis-foundry-spec.md b/docs/hypothesis-foundry-spec.md
index f3cbc9b9..6c65da07 100644
--- a/docs/hypothesis-foundry-spec.md
+++ b/docs/hypothesis-foundry-spec.md
@@ -101,6 +101,7 @@ Every checked-in source record — real or hermetic-fixture — carries exactly
 | `proxy_of` | non-`None` only for a pilot-proxy record; carries the parked study it stands in for and its preserved `do_not` restriction |
 | `supersession` | non-`None` only for an older, formula-superseded record; carries the newer ref and the alias disposition it selects |
 | `aliases_lineage_ids` | lineage/alias ids this record is linked to |
+| `alternatives` | source_ids of the sibling representation(s) this record legally alternates with — a per-record disclosure of `§1.4`'s "every finite alternative the compiler is allowed to enumerate", additive alongside `foundry_family_key` membership and never a replacement for it (the family key is still what actually lets the compiler enumerate them, `§2.1`); empty when no ratified alternative exists |
 | `audit_note` | why each decision follows from the quoted rules — **never** citing a candidate outcome, p-value, effect, observation count, Scout verdict, or PnL result |
 | `extra` | caller-supplied metadata the compiler NEVER reads (proves TC-11: an injected `effect_bps`/`p_value`/`n` cannot move a disposition or hash) |
 
diff --git a/apps/backend/tests/test_foundry_hermetic_epoch.py b/apps/backend/tests/test_foundry_hermetic_epoch.py
new file mode 100644
index 00000000..6369d401
--- /dev/null
+++ b/apps/backend/tests/test_foundry_hermetic_epoch.py
@@ -0,0 +1,679 @@
+"""The Hypothesis Foundry -- the composite hermetic "complete factory" oracle suite
+(goal-hypothesis-foundry-iter-3, J-05). Test-first contract: TC-1 through TC-8 in
+``docs/phases/goal-hypothesis-foundry-iter-3.md``.
+
+**What this file proves that no single ``foundry_*.py`` module's own test file does.** Every prior
+Foundry test file (``test_foundry_compiler.py``, ``test_foundry_interpreter.py``,
+``test_foundry_family.py``, ``test_foundry_freeze.py``, ``test_foundry_ledger.py``,
+``test_foundry_runner.py``) exercises exactly one module in isolation, or two adjacent modules at
+most (``test_foundry_runner.py``'s own small fixtures). This file drives the REAL production
+``foundry_compiler`` -> ``foundry_interpreter`` -> ``foundry_family`` -> ``foundry_ledger`` ->
+``foundry_runner`` path together, over one composite epoch containing every possible outcome type
+at once (a ``BLOCKED_*`` source, an ``EXCLUDED_*`` source, an ``ALIASED_*`` source, and
+``FROZEN_READY`` variants terminating each of ``EVALUATED_INSUFFICIENT``/``EVALUATED_KILLED`` (via
+every one of the five kill reasons)/``DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN``), plus the all-blocked,
+all-killed, multi-survivor, large-scale checkpoint/resume, and protected-data-trip/
+evidence-class-immutability fixtures the goal's own Constraints demand before the real freeze
+("use large hermetic synthetic fixtures to prove performance/checkpoint behavior... before the real
+freeze"). No mock of any of the five modules under test appears anywhere below -- every fixture is a
+hermetic, synthetic ANCHOR list (never a real dataset/network read), fed through the real functions.
+
+**Kill-type fixture provenance.** Every per-outcome anchor generator below is a direct, deliberate
+translation of an ALREADY-hermetically-proven ``scout.py`` fixture from ``test_scout.py`` (the
+``killed_null``/``killed_direction``/``killed_concentration``/``killed_economic``/
+``killed_insufficient_n``/``killed_fragile``/``survive`` fixtures there) into the Foundry's own
+``PopulationAnchor``/``ComponentResolution`` shape (``is_candidate`` <-> the direct-scalar-corner
+boolean the scout fixtures express as ``feature_value >= 0``) -- never invented from scratch, so a
+kill-type reliably reaching its OWN decision branch through the REAL block-permutation null is
+already known-good production behavior, not a hand-tuned coincidence of this file."""
+
+from __future__ import annotations
+
+import random
+
+import pytest
+
+from app.research import foundry_compiler as fc
+from app.research import foundry_family as ff
+from app.research import foundry_interpreter as fi
+from app.research import foundry_ledger as fl
+from app.research import foundry_runner as fr
+from app.research import foundry_source_registry as fsr
+from app.research import micro_features as mf
+from app.research import scout
+from app.research.micro_accessor import MicroAccessorOriginFenceError, MicroAccessorSealedShardError
+
+# --- shared fixtures ------------------------------------------------------------------------------
+
+_ECON_FLOOR_TINY = {
+    "floor_bps": 0.001, "unit": "bps", "rule": "scout_quoted_spread_floor", "multiple": 1.0,
+}
+_ECON_FLOOR_HUGE = {
+    "floor_bps": 1000.0, "unit": "bps", "rule": "scout_quoted_spread_floor", "multiple": 1.0,
+}
+
+
+def _spec(ordinal: int, *, family_id: str, family_count: int, sidedness: str = "long") -> fc.CandidateSpec:
+    """One direct-scalar-membership ``CandidateSpec`` -- the SAME one-coordinate shape
+    ``test_foundry_runner.py``'s own ``_scalar_spec`` uses, so ``foundry_ledger.prospective_root_status``
+    resolves to the family id (never ``root_deferred_composite``) for every variant this file builds."""
+    coord = fc.CandidateCoordinate(
+        feature_construct_id="q", semantic_role="candidate_signal", transform_orientation="ge",
+        threshold_corner_predicate="q >= 1", threshold_provenance="natural_semantic_boundary",
+        aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
+    )
+    source_id = f"{family_id}:{ordinal}"
+    return fc.CandidateSpec(
+        foundry_spec_version="v1", epoch_id="epoch:hermetic-complete-factory", source_ids=(source_id,),
+        lineage_id=source_id, foundry_family_id=family_id,
+        variant_id=f"{family_id}:{ordinal}", variant_ordinal=ordinal,
+        population=fc.CandidatePopulation(structure_context_kind="none", side_filter=None, setup_context_id=None),
+        coordinates=(coord,), relation=fc.CandidateRelation(kind="direct_scalar_membership"),
+        membership_corner="q >= 1", outcome=fc.CandidateOutcome(horizon_key="trades_20", sidedness=sidedness),
+        economic_floor_rule=fc.EconomicFloorRule(), foundry_family_variant_count=family_count,
+    ).with_hash()
+
+
+def _anchor(session: str, idx: int, symbol: str, member: bool, outcome_bps: float, *, tod: str = "mid") -> fi.PopulationAnchor:
+    comp = fi.ComponentResolution("q", True, float(idx), 1.0 if member else 0.0, member)
+    return fi.PopulationAnchor(f"ds-{session}", symbol, session, idx, tod, None, outcome_bps, mf.OUTCOME_UNIT, (comp,))
+
+
+# --- per-kill-type anchor generators, each a direct translation of an already-proven test_scout.py
+# fixture (see module docstring) ---------------------------------------------------------------
+
+
+def _survive_anchors(seed: int, *, effect_bps: float = 60.0, n_sessions: int = 6, n_per_session: int = 40, symbol: str = "AAPL") -> list[fi.PopulationAnchor]:
+    """Translation of ``test_scout.py``'s ``_planted_effect_anchors``: a genuine planted effect,
+    single symbol, evenly spread across sessions -- reliably ``survive``s at ``effect_bps=60``."""
+    rng = random.Random(f"factory-survive:{seed}")
+    anchors = []
+    for s in range(n_sessions):
+        session = f"2026-08-{10 + s:02d}"
+        for i in range(n_per_session):
+            member = rng.random() < 0.5
+            outcome = rng.gauss(effect_bps if member else 0.0, 1.0)
+            anchors.append(_anchor(session, i, symbol, member, outcome))
+    return anchors
+
+
+def _wrong_direction_anchors(seed: int, *, effect_bps: float = 60.0) -> list[fi.PopulationAnchor]:
+    """Translation of ``test_scout.py``'s ``test_screen_candidate_kills_direction_on_a_wrong_signed_effect``:
+    the SAME planted-effect population, outcome sign flipped -- significant but wrong-signed."""
+    base = _survive_anchors(seed, effect_bps=effect_bps)
+    return [
+        fi.PopulationAnchor(a.dataset_id, a.symbol, a.session_date, a.trade_index, a.tod_bucket, a.fallback_frac, -a.outcome_bps, a.outcome_unit, a.components)
+        for a in base
+    ]
+
+
+def _null_anchors(seed: int, *, n_sessions: int = 6, n_per_session: int = 20, symbol: str = "PG") -> list[fi.PopulationAnchor]:
+    """Translation of ``test_scout.py``'s ``test_screen_candidate_kills_null_on_an_unrelated_feature``:
+    membership and outcome are independently drawn -- no true relationship."""
+    rng = random.Random(f"factory-null:{seed}")
+    anchors = []
+    for s in range(n_sessions):
+        session = f"2026-08-{s + 1:02d}"
+        for i in range(n_per_session):
+            member = rng.random() < 0.5
+            outcome = rng.gauss(0.0, 1.0)
+            anchors.append(_anchor(session, i, symbol, member, outcome))
+    return anchors
+
+
+def _concentration_anchors(seed: int, *, n_sessions: int = 6, n_per_session: int = 20) -> list[fi.PopulationAnchor]:
+    """Translation of ``test_scout.py``'s ``test_screen_candidate_kills_concentration_when_the_effect_is_symbol_skewed``:
+    a genuine, significant, positive effect whose candidate cell is symbol-skewed (>80% one symbol)."""
+    rng = random.Random(f"factory-concentration:{seed}")
+    anchors = []
+    for s in range(n_sessions):
+        session = f"2026-09-{s + 1:02d}"
+        for i in range(n_per_session):
+            member = rng.random() < 0.5
+            outcome = rng.gauss(3.0 if member else 0.0, 1.0)
+            symbol = "AAA" if (not member or rng.random() < 0.9) else "BBB"
+            anchors.append(_anchor(session, i, symbol, member, outcome))
+    return anchors
+
+
+def _insufficient_anchors() -> list[fi.PopulationAnchor]:
+    """Translation of ``test_scout.py``'s ``test_screen_candidate_kills_insufficient_n_on_a_single_session``:
+    a single session -- below ``SCOUT_MIN_SESSION_CLUSTERS`` regardless of per-cell counts."""
+    anchors = []
+    session = "2026-07-01"
+    for i in range(20):
+        member = i % 2 == 0
+        anchors.append(_anchor(session, i, "AAPL", member, 3.0 if member else -3.0))
+    return anchors
+
+
+def _fragile_anchors() -> list[fi.PopulationAnchor]:
+    """VERBATIM translation of ``test_scout.py``'s
+    ``test_screen_candidate_kills_fragile_when_the_sign_depends_on_one_dominant_session`` fixture:
+    three sessions where the WITH-all-sessions effect is positive but dropping session "B" (the
+    biggest candidate-cell contributor) flips the sign. Reaching ``killed_fragile`` still needs the
+    SAME ``scout._two_sided_p`` monkeypatch that production test uses (see its own docstring: forcing
+    significance in isolation is the only reliable way to reach this branch, since a genuinely tiny
+    p-value AND a session-count-driven sign flip at once is "hard to hand-tune reliably")."""
+    anchors = []
+    for i in range(8):
+        anchors.append(_anchor("A", 2 * i, "PG", True, -0.2))
+        anchors.append(_anchor("A", 2 * i + 1, "PG", False, 0.0))
+    for i in range(12):
+        anchors.append(_anchor("B", 2 * i, "PG", True, 2.0))
+        anchors.append(_anchor("B", 2 * i + 1, "PG", False, 0.0))
+    for i in range(8):
+        anchors.append(_anchor("C", 2 * i, "PG", True, -0.2))
+        anchors.append(_anchor("C", 2 * i + 1, "PG", False, 0.0))
+    return anchors
+
+
+# --- non-compiled source fixtures: one BLOCKED_*, one EXCLUDED_*, one ALIASED_* -- direct
+# translations of test_foundry_source_registry.py's own already-proven archetypes. --------------
+
+
+def _blocked_source() -> fsr.SourceRecord:
+    excerpt = "A collapse in impact defines a high-aggression signal at the wall."
+    span_text = "collapse in impact defines a high-aggression signal"
+    return fsr.SourceRecord(
+        source_id="factory-blocked-spec-gap", source_path="docs/fixtures/mechanism.md", section_ref="1.9",
+        quoted_spans=(fsr.QuotedSpan(text=span_text, location=excerpt.index(span_text)),), source_excerpt=excerpt,
+        mechanism_statement="impact collapse at the wall implies reversal", operative_formula_refs=("impact_efficiency",),
+        direction_derivation="collapse implies reversal -> long",
+        comparator_derivation="complement_within_same_eligible_population",
+        audit_note="'collapse'/'high' are undefined magnitude words -- no ratified numeric meaning exists",
+        unresolved_magnitude_words=("collapse", "high"),
+    )
+
+
+def _excluded_source() -> fsr.SourceRecord:
+    excerpt = "Card 9.1/Study 2 was previously killed and may not be recompiled."
+    span_text = "Card 9.1/Study 2 was previously killed and may not be recompiled"
+    return fsr.SourceRecord(
+        source_id="factory-excluded-previously-killed", source_path="docs/fixtures/mechanism.md", section_ref="9.1",
+        quoted_spans=(fsr.QuotedSpan(text=span_text, location=excerpt.index(span_text)),), source_excerpt=excerpt,
+        mechanism_statement="Card 9.1/Study 2 mechanism", operative_formula_refs=(),
+        direction_derivation=fsr.BLOCKED_DIRECTION_SENTINEL,
+        comparator_derivation="complement_within_same_eligible_population",
+        audit_note="Card 9.1/Study 2 was previously killed -- may not be recompiled, reversed, or rerun",
+        explicit_exclusion=fsr.DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED,
+    )
+
+
+def _aliased_source() -> fsr.SourceRecord:
+    excerpt = "Card 9.7 event-time windows are already embodied by the current frozen feature windows."
+    span_text = "event-time windows are already embodied by the current frozen feature windows"
+    return fsr.SourceRecord(
+        source_id="factory-aliased-variant-vocabulary", source_path="docs/fixtures/mechanism.md", section_ref="9.7",
+        quoted_spans=(fsr.QuotedSpan(text=span_text, location=excerpt.index(span_text)),), source_excerpt=excerpt,
+        mechanism_statement="event-time feature windows", operative_formula_refs=("event_time_window",),
+        direction_derivation="long", comparator_derivation="complement_within_same_eligible_population",
+        audit_note="Card 9.7 is variant vocabulary for an already-frozen current feature window, per §1.3",
+        superseded_fields={"event_time_window": "docs/rapid-validation-spec.md#feature-windows"},
+        supersession=fsr.SupersessionDeclaration(
+            newer_source_ref="docs/rapid-validation-spec.md#feature-windows",
+            alias_kind=fsr.DISPOSITION_ALIASED_VARIANT_VOCABULARY,
+        ),
+    )
+
+
+# === TC-1/TC-2: the composite "complete factory" epoch ==============================================
+
+
+def test_tc1_tc2_composite_complete_factory_epoch_reaches_every_outcome_type_in_canonical_order(monkeypatch, tmp_path):
+    # --- non-compiled sources: proven at the disposition layer, coexisting in the SAME epoch as the
+    # seven evaluable variants below (never interfering with each other). ---------------------------
+    non_compiled = [_blocked_source(), _excluded_source(), _aliased_source()]
+    dispositions = {r.source_id: fsr.compile_source_disposition(r) for r in non_compiled}
+    assert dispositions["factory-blocked-spec-gap"] == fsr.DISPOSITION_BLOCKED_SPEC_GAP
+    assert dispositions["factory-excluded-previously-killed"] == fsr.DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED
+    assert dispositions["factory-aliased-variant-vocabulary"] == fsr.DISPOSITION_ALIASED_VARIANT_VOCABULARY
+
+    # --- seven FROZEN_READY variants, one Foundry family, canonical ordinal order 0..6. -------------
+    family_id = "family:complete-factory"
+    family = ff.build_family_registry({family_id: [f"{family_id}:{i}" for i in range(7)]})[family_id]
+    assert family.blocked is False
+    assert family.variant_count == 7
+
+    plan = [
+        ("insufficient", _insufficient_anchors(), _ECON_FLOOR_TINY, False),
+        ("null", _null_anchors(1), _ECON_FLOOR_TINY, False),
+        ("direction", _wrong_direction_anchors(2), _ECON_FLOOR_TINY, False),
+        ("concentration", _concentration_anchors(3), _ECON_FLOOR_TINY, False),
+        ("economic", _survive_anchors(4, effect_bps=40.0), _ECON_FLOOR_HUGE, False),
+        ("fragile", _fragile_anchors(), _ECON_FLOOR_TINY, True),
+        ("survive", _survive_anchors(6, effect_bps=60.0), _ECON_FLOOR_TINY, False),
+    ]
+
+    ledger = fl.FoundryLedger(tmp_path)
+    manifest_hash = "manifest:complete-factory"
+    specs = [_spec(i, family_id=family_id, family_count=7) for i in range(len(plan))]
+    results = []
+    for (label, anchors, floor, needs_fragile_patch), spec in zip(plan, specs):
+        if needs_fragile_patch:
+            with monkeypatch.context() as m:
+                m.setattr(scout, "_two_sided_p", lambda observed, null: 0.0001)
+                row = fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=floor, manifest_hash=manifest_hash, family=family)
+        else:
+            row = fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=floor, manifest_hash=manifest_hash, family=family)
+        results.append((label, spec, row))
+
+    expected_states = {
+        "insufficient": "EVALUATED_INSUFFICIENT",
+        "null": "EVALUATED_KILLED",
+        "direction": "EVALUATED_KILLED",
+        "concentration": "EVALUATED_KILLED",
+        "economic": "EVALUATED_KILLED",
+        "fragile": "EVALUATED_KILLED",
+        "survive": "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
+    }
+    expected_reasons = {
+        "null": "killed_null", "direction": "killed_direction", "concentration": "killed_concentration",
+        "economic": "killed_economic", "fragile": "killed_fragile", "insufficient": "killed_insufficient_n",
+        "survive": "survive",
+    }
+    for label, spec, row in results:
+        assert row["foundry_state"] == expected_states[label], f"{label}: {row['foundry_state']}"
+        assert row["screen_result"]["reason"] == expected_reasons[label], f"{label}: {row['screen_result']}"
+        # TC-2: every terminal row carries the pre-frozen family denominator, regardless of
+        # execution progress, position, or verdict.
+        assert row["foundry_family_variant_count"] == 7, label
+        assert row["screen_result"]["screen_result"]["best_of_n_disclosure"]["n"] == 7, label
+
+    # TC-1: canonical-order visiting is unaffected by any kill/survivor encountered along the way --
+    # the ledger's terminal rows appear in EXACTLY the order the variants were given (ordinal 0..6).
+    terminal_hashes = [r["candidate_spec_hash"] for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL]
+    assert terminal_hashes == [spec.candidate_spec_hash for _, spec, _ in results]
+
+    # every non-compiled source keeps its declared disposition, unaffected by the seven terminal
+    # candidates that ran alongside it in the same epoch.
+    for record in non_compiled:
+        assert fsr.compile_source_disposition(record) == dispositions[record.source_id]
+
+    # ledger integrity holds after the full mixed-outcome sequence.
+    assert ledger.verify_chain()["ok"] is True
+
+
+# === TC-1 (compiler seam): the FROZEN_READY variants the runner evaluates are the ones the REAL ====
+# compiler produced from real SourceRecords -- not hand-built CandidateSpec objects. =================
+
+
+def _compilable_variant_record(source_id: str, ordinal: int) -> fsr.SourceRecord:
+    """A COMPILED-disposition source record (the natural-boundary-scalar archetype
+    ``test_foundry_compiler.py``'s own iter-1 TC-3/TC-4 fixtures use), carrying a shared
+    ``foundry_family_key`` so ``fc.compile_sources`` derives the family identity itself."""
+    excerpt = f"{source_id}: a signed variable's zero boundary is bid-heavy when quote_imbalance is positive."
+    span_text = "signed variable's zero boundary is bid-heavy when quote_imbalance is positive"
+    return fsr.SourceRecord(
+        source_id=source_id, source_path="docs/fixtures/mechanism.md", section_ref="2.3",
+        quoted_spans=(fsr.QuotedSpan(text=span_text, location=excerpt.index(span_text)),),
+        source_excerpt=excerpt,
+        mechanism_statement="quote imbalance zero-crossing implies bid-heavy",
+        operative_formula_refs=("quote_imbalance",),
+        direction_derivation="positive quote_imbalance implies bid-heavy -> long",
+        comparator_derivation="complement_within_same_eligible_population",
+        audit_note="zero boundary intrinsic to the signed variable's own definition, per quoted text",
+        threshold_provenance=fsr.THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
+        foundry_family_key="factory-compiled-family", variant_ordinal=ordinal,
+    )
+
+
+def _compilable_blueprint(horizon: str = "trades_20") -> fc.CandidateBlueprint:
+    """The same fully-immediate blueprint shape ``test_foundry_compiler.py``'s own ``_blueprint``
+    builds -- copied rather than imported so this oracle file stays self-contained."""
+    return fc.CandidateBlueprint(
+        population=fc.CandidatePopulation(
+            structure_context_kind="band_wall_touch", side_filter=None, setup_context_id=None
+        ),
+        coordinates=(
+            fc.CandidateCoordinate(
+                feature_construct_id="quote_imbalance", semantic_role="primary",
+                transform_orientation="positive_zero_boundary",
+                threshold_corner_predicate="quote_imbalance > 0",
+                threshold_provenance=fsr.THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
+                aggressor_derived=False, unit_basis="ratio", anchor_at="touch", available_at="touch",
+            ),
+        ),
+        relation=fc.CandidateRelation(kind="direct_scalar_membership"),
+        membership_corner="quote_imbalance > 0",
+        outcome=fc.CandidateOutcome(horizon_key=horizon, sidedness="long"),
+    )
+
+
+def test_compiled_candidate_specs_flow_from_the_real_compiler_into_the_real_runner(tmp_path):
+    """The one seam the rest of this file (and every other ``test_foundry_*.py``) leaves untested:
+    every other interpreter/runner fixture hand-builds its ``CandidateSpec``, so nothing proved
+    that the object ``fc.compile_sources`` ACTUALLY produces from a ``SourceRecord`` is directly
+    evaluable by ``foundry_interpreter``/``foundry_runner`` and lands its own frozen identities
+    (spec hash, family id, family denominator, deterministic rule_id) on the terminal ledger row
+    unchanged. Added by the iter-3 audit pass; this is the exact compiler -> runner handoff J-06's
+    real epoch will depend on."""
+    records = [_compilable_variant_record("factory-compiled-a", 0), _compilable_variant_record("factory-compiled-b", 1)]
+    result = fc.compile_sources(
+        records, foundry_spec_version="v1", epoch_id="epoch:hermetic-complete-factory",
+        blueprints={
+            "factory-compiled-a": _compilable_blueprint("trades_20"),
+            "factory-compiled-b": _compilable_blueprint("trades_100"),
+        },
+    )
+    assert result.dispositions == {
+        "factory-compiled-a": fsr.DISPOSITION_COMPILED, "factory-compiled-b": fsr.DISPOSITION_COMPILED,
+    }
+    spec_a = result.candidate_specs["factory-compiled-a"]
+    spec_b = result.candidate_specs["factory-compiled-b"]
+    assert spec_a.foundry_family_id == spec_b.foundry_family_id  # the COMPILER derived the family
+    assert spec_a.candidate_spec_hash != spec_b.candidate_spec_hash
+
+    family_id = spec_a.foundry_family_id
+    family = ff.build_family_registry({family_id: [spec_a.variant_id, spec_b.variant_id]})[family_id]
+    ledger = fl.FoundryLedger(tmp_path)
+    rows = fr.run_family(
+        family,
+        [(spec_a, _survive_anchors(41, effect_bps=60.0)), (spec_b, _null_anchors(42))],
+        ledger=ledger, econ_floor=_ECON_FLOOR_TINY, manifest_hash="manifest:compiled-flow",
+    )
+
+    # the compiled specs really evaluate: one survivor, one null kill, through the production path.
+    assert rows[0]["foundry_state"] == "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"
+    assert rows[1]["foundry_state"] == "EVALUATED_KILLED"
+    assert rows[1]["screen_result"]["reason"] == "killed_null"
+    # every identity on the terminal rows came from the COMPILER's own frozen objects, unchanged.
+    assert [r["candidate_spec_hash"] for r in rows] == [spec_a.candidate_spec_hash, spec_b.candidate_spec_hash]
+    assert [r["foundry_family_id"] for r in rows] == [family_id, family_id]
+    assert [r["foundry_family_variant_count"] for r in rows] == [2, 2]
+    assert rows[0]["rule_id"] == f"foundry:{spec_a.epoch_id}:{spec_a.candidate_spec_hash}"
+    assert rows[0]["screen_result"]["screen_result"]["evidence_class"] == scout.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
+    assert ledger.verify_chain()["ok"] is True
+
+
+# === TC-3: an all-BLOCKED_*/EXCLUDED_*/ALIASED_* epoch (zero FROZEN_READY variants) completes ======
+# honestly, not as an error. ==========================================================================
+
+
+def test_tc3_all_non_compiled_epoch_reaches_an_honest_zero_candidate_completion(tmp_path):
+    records = [_blocked_source(), _excluded_source(), _aliased_source()]
... [diff_bound] apps/backend/tests/test_foundry_hermetic_epoch.py: 285 more diff lines omitted — Read the file for full detail
```
