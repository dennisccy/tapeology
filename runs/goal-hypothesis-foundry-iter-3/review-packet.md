# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

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
 
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-hypothesis-foundry/telemetry.jsonl   | 7 +++++++
 runs/goal-session-hypothesis-foundry/trace/trace.jsonl | 2 ++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
