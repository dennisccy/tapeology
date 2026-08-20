# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 2.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_micro_sealed_evaluation.py` (46 lines not shown)

```diff
diff --git a/apps/backend/app/research/micro_sealed_evaluation.py b/apps/backend/app/research/micro_sealed_evaluation.py
index 825eb86..8358de5 100644
--- a/apps/backend/app/research/micro_sealed_evaluation.py
+++ b/apps/backend/app/research/micro_sealed_evaluation.py
@@ -43,32 +43,33 @@ verdict):**
    sealed_evaluations_for_family`` (single source of truth: the persisted row, never a second
    in-memory copy this function hands back as if it were authoritative).
 
-**``SEALED_PASS_RULE_V1`` introduces NO new numeric constant** (spec section 8.1, r6 owner ruling
-point 1): it reuses ``walkforward.WF_FOLD_MIN_OBSERVATIONS``/``_SIGNAL_SESSIONS``/``_SYMBOLS``
-(the SAME per-fold sufficiency floors a walk-forward fold already enforces, via the SAME
-``summarize_fold_observations`` function) and the family's OWN pre-registered spec section 5.5
-economic floor (``candidate_spec["econ_floor"]`` -- never a second, independently-tuned floor).
-``rule_id``/``rule_version`` are IDENTITY metadata (mirroring ``walkforward.WF_SURVIVOR_RULE_V1``'s
-own "the rule's own name IS its identity" convention), not tunable thresholds.
-
-**Condition 1's floors are the section-1 defaults, but a candidate spec MAY NARROW them --
-disclosed, unresolved, OWNER-OWED (rule T-1; iteration-17 audit finding B1).**
-``summarize_fold_observations`` honours a per-spec ``floors`` override key-by-key (the
-``evaluate_mode_b_fold(floors=...)`` precedent this module reuses verbatim), so a candidate spec
-carrying its own ``floors`` -- not the section-1 constants ``sealed_pass_rule_hash()`` embeds --
-decides condition 1. This module does NOT silently pin the override away, because pinning it makes
-a PASS verdict structurally UNREACHABLE: a vault shard is ONE symbol-day (spec section 7.3's own
+**``SEALED_PASS_RULE_V1`` condition 1 is evaluator-owned and sealed-specific (spec section 8.1,
+r9 owner ruling 2026-08-20, TR-30) -- it introduces exactly ONE new pinned numeric constant,
+``SEALED_MIN_OBSERVATIONS`` (spec section 1), owned by THIS module alone.** The r6-era rule this
+replaces reused ``walkforward.WF_FOLD_MIN_OBSERVATIONS``/``_SIGNAL_SESSIONS``/``_SYMBOLS`` verbatim
+-- but the iteration-17 audit PROVED by execution that reusing those floors let a candidate spec's
+own ``floors`` override certify a permanent ``pass`` off a single observation (a spec carrying
+``floors={1,1,1}`` plus one observation produced ``verdict: "pass"`` under a ``rule_hash``
+certifying 30/8/2 the run never applied), and separately proved that mechanically PINNING those
+same floors was ALSO wrong: a vault shard is ONE symbol-day (spec section 7.3's own
 ``f"{symbol}:{YYYY-MM-DD}"`` seal key), so a single shard can never carry
 ``WF_FOLD_MIN_SIGNAL_SESSIONS`` = 8 signal-bearing SESSIONS or ``WF_FOLD_MIN_SYMBOLS`` = 2 SYMBOLS,
-and every evaluation would return ``insufficient`` forever (verified: pinning the floors turns all
-four of this module's own PASS/FAIL fixtures into ``insufficient``). Spec section 8.1 condition 1
-and section 7.3/7.4 are therefore in genuine tension over what "the shard's recomputed
-observations" spans -- ONE shard, or the family's whole exposed tranche -- and under rule T-1 that
-is an OWNER RULING, never a dev or auditor invention. Until it is ruled, the floors ACTUALLY
-applied are recorded verbatim on every persisted artifact as ``floors_applied``: spec section 8.1
-requires the artifact to be "sufficient to reproduce the verdict", and condition 1 is NOT
-reproducible from ``n``/``n_sessions``/``n_symbols`` alone -- so a narrowed floor can never be
-silent in a permanent verdict or in any later export bundle.
+making PASS structurally unreachable. **The owner resolved the section-8.1-vs-7.3 contradiction by
+separating the two stages scientifically rather than changing the sealing unit: the walk-forward
+stage owns BREADTH (``WF_SURVIVOR_RULE_V1`` already establishes it before a candidate reaches the
+sealed stage at all); the sealed stage owns UNTOUCHED REPLICATION on one hidden symbol-day.**
+Session and symbol breadth are therefore computed for DISCLOSURE only (``n_sessions``/``n_symbols``
+on the artifact) but never compared against any numeric floor at shard scope, and are recorded on
+the floor-labeled artifact fields as the literal string ``"not_applicable_single_shard"`` --
+never silently ``1``. **No sufficiency value may ever be sourced from the candidate or caller
+spec**: any ``candidate_spec`` carrying a ``floors`` key (the exact override mechanism this rule
+retires) is refused outright, BEFORE any verdict is derived (``SealedEvaluationRefusedError`` --
+mirrors the step-2/step-4 fail-closed ordering elsewhere in this sequence). The family's OWN
+pre-registered spec section 5.5 economic floor (``candidate_spec["econ_floor"]``) is unaffected by
+r9 -- it was never a per-fold breadth floor and stays exactly as it was. ``rule_id``/``rule_version``
+stay IDENTITY metadata (mirroring ``walkforward.WF_SURVIVOR_RULE_V1``'s own "the rule's own name IS
+its identity" convention) -- r9 replaces condition 1's CONTENT, never the rule's name or version
+(spec: "frozen; r9 replaces condition 1").
 
 **The rule-identity-at-assignment interpretation call (T-1, disclosed).** Spec condition 4 needs
 "the evaluation rule id/version/hash recorded AT ASSIGNMENT" to compare against "the one applied" --
@@ -106,6 +107,8 @@ from .micro_graduation import (
 __all__ = [
     "SEALED_PASS_RULE_V1",
     "SEALED_PASS_RULE_VERSION",
+    "SEALED_MIN_OBSERVATIONS",
+    "SEALED_BREADTH_NOT_APPLICABLE",
     "SEALED_VERDICT_PASS",
     "SEALED_VERDICT_FAIL",
     "SEALED_VERDICT_INSUFFICIENT",
@@ -122,6 +125,16 @@ __all__ = [
 SEALED_PASS_RULE_V1 = "SEALED_PASS_RULE_V1"
 SEALED_PASS_RULE_VERSION = 1
 
+# === spec section 1 (r9) -- the ONE sufficiency floor at sealed-shard scope. Pinned HERE, this
+# module's own constant, mirroring (never importing) ``walkforward.WF_FOLD_MIN_OBSERVATIONS``'s
+# pattern; never a ``Config`` field; never sourced from a candidate or caller spec. ===================
+SEALED_MIN_OBSERVATIONS = 30
+
+# session/symbol breadth are STRUCTURALLY inapplicable at shard scope (one shard = one symbol x one
+# session-date, spec section 7.3) -- this literal string, never a silent ``1``, is what the artifact's
+# floor-labeled breadth fields record (TC-4).
+SEALED_BREADTH_NOT_APPLICABLE = "not_applicable_single_shard"
+
 # The tri-state verdict vocabulary (spec section 8.1 point 1) -- OWNED here (the scientific answer's
 # own module), never redefined a second time elsewhere. ``micro_graduation.py`` compares against the
 # literal string "pass" directly (a disclosed, one-way-dependency interpretation call logged on
@@ -160,16 +173,21 @@ def _iso_utc_now() -> str:
 
 def sealed_pass_parameters() -> dict:
     """Every constant ``SEALED_PASS_RULE_V1`` depends on, embedded verbatim (the
-    ``walkforward.walkforward_parameters``/``scout.scout_parameters`` pattern) -- introduces NO new
-    numeric value (module docstring): the three floors are IMPORTED from ``walkforward.py``, never
-    re-declared. Hashed into ``sealed_pass_rule_hash()``, which a candidate spec must carry
-    (recorded before assignment) for condition 4's rule-identity check."""
+    ``walkforward.walkforward_parameters``/``scout.scout_parameters`` pattern) -- (r9) condition 1
+    is now SEALED-SPECIFIC: ``SEALED_MIN_OBSERVATIONS`` is this module's own pinned constant (never
+    imported from ``walkforward.py``), and the fixed breadth policy
+    (``SEALED_BREADTH_NOT_APPLICABLE``) is embedded too, so a future change to either one also
+    changes ``sealed_pass_rule_hash()``. The walk-forward per-fold breadth floors
+    (``WF_FOLD_MIN_SIGNAL_SESSIONS``/``WF_FOLD_MIN_SYMBOLS``) are DELIBERATELY absent -- they no
+    longer govern condition 1 at all (breadth is the walk-forward stage's own province). Hashed
+    into ``sealed_pass_rule_hash()``, which a candidate spec must carry (recorded before
+    assignment) for condition 4's rule-identity check."""
     return {
         "sealed_pass_rule_id": SEALED_PASS_RULE_V1,
         "sealed_pass_rule_version": SEALED_PASS_RULE_VERSION,
-        "wf_fold_min_observations": wf.WF_FOLD_MIN_OBSERVATIONS,
-        "wf_fold_min_signal_sessions": wf.WF_FOLD_MIN_SIGNAL_SESSIONS,
-        "wf_fold_min_symbols": wf.WF_FOLD_MIN_SYMBOLS,
+        "sealed_min_observations": SEALED_MIN_OBSERVATIONS,
+        "min_signal_sessions": SEALED_BREADTH_NOT_APPLICABLE,
+        "min_symbols": SEALED_BREADTH_NOT_APPLICABLE,
         "required_evidence_class": REQUIRED_EVIDENCE_CLASS,
         "required_process_label": REQUIRED_PROCESS_LABEL,
     }
@@ -200,18 +218,19 @@ def _expected_sign(sidedness: str) -> str:
     return "positive" if sidedness == "long" else "negative"
 
 
-def _resolved_floors(candidate_spec: dict) -> dict:
-    """The three per-fold sufficiency floors condition 1 ACTUALLY applies -- the section-1 pinned
-    constants, EXCEPT wherever the candidate's own registered spec carries a ``floors`` override
-    (which ``walkforward.summarize_fold_observations`` honours key-by-key; see the module
-    docstring's own T-1 disclosure for why this module surfaces that rather than pinning it away).
-    Returned fully RESOLVED, never the caller's partial dict, so the ``floors_applied`` field on
-    the persisted artifact is self-contained."""
-    override = candidate_spec.get("floors") or {}
+def _sealed_floors() -> dict:
+    """(r9) The per-fold floors dict this module hands to
+    ``walkforward.summarize_fold_observations`` -- FIXED, never candidate- or caller-controlled
+    (the exact mechanism r9 retires; there is no override parameter anywhere in this function's
+    signature, unlike the retired ``_resolved_floors(candidate_spec)`` it replaces). Only the
+    observation count is gated, at ``SEALED_MIN_OBSERVATIONS``; session/symbol breadth are pinned
+    to ``0`` so ``summarize_fold_observations``'s own per-fold status can never fail on breadth at
+    shard scope -- breadth is the walk-forward stage's province (spec section 8.1 condition 1's own
+    rationale), not this one's."""
     return {
-        "wf_fold_min_observations": override.get("wf_fold_min_observations", wf.WF_FOLD_MIN_OBSERVATIONS),
-        "wf_fold_min_signal_sessions": override.get("wf_fold_min_signal_sessions", wf.WF_FOLD_MIN_SIGNAL_SESSIONS),
-        "wf_fold_min_symbols": override.get("wf_fold_min_symbols", wf.WF_FOLD_MIN_SYMBOLS),
+        "wf_fold_min_observations": SEALED_MIN_OBSERVATIONS,
+        "wf_fold_min_signal_sessions": 0,
+        "wf_fold_min_symbols": 0,
     }
 
 
@@ -305,6 +324,19 @@ def evaluate_sealed_verdict(
             "evaluation is attempted",
         )
 
+    # --- step 2 (r9 sufficiency-ownership half, TR-30): a candidate_spec carrying a 'floors'
+    # override -- the exact caller-controlled mechanism r9 retires -- is refused OUTRIGHT, before
+    # any verdict is derived and before the shard/accessor read below. No sufficiency value may
+    # ever be sourced from the candidate or caller spec (spec section 8.1 condition 1): the sealed
+    # evaluator alone owns SEALED_MIN_OBSERVATIONS and the fixed breadth policy. -------------------
+    if "floors" in candidate_spec:
+        raise SealedEvaluationRefusedError(
+            family_root_id, dataset_id,
+            f"candidate_spec carries a 'floors' override ({candidate_spec['floors']!r}) -- refused "
+            "(spec section 8.1 condition 1, r9/TR-30): sealed-shard sufficiency is evaluator-owned; "
+            "no caller-supplied floor, threshold, or equivalent override is ever honoured",
+        )
+
     # --- step 2 (rule identity half): the rule recorded on the spec BEFORE assignment must be
     # byte-identical to the one this evaluator is ABOUT to apply -- a mismatch fails CLOSED, never
     # a computed verdict (TC-3). Checked BEFORE any shard read, so a rule change is caught even if
@@ -360,9 +392,9 @@ def evaluate_sealed_verdict(
 
     # --- step 4: RECOMPUTE via the canonical statistical core, never trust a caller-computed
     # effect -- summarize_fold_observations is the SAME function walk-forward folds themselves
-    # consult (never reimplemented; the per-fold sufficiency floors ARE SEALED_PASS_RULE_V1
-    # condition 1, reused verbatim, no new constant). ------------------------------------------------
-    floors = _resolved_floors(candidate_spec)
+    # consult (never reimplemented). (r9) The floors handed in are FIXED and evaluator-owned
+    # (SEALED_PASS_RULE_V1 condition 1's own sealed-specific rule, never the candidate spec's). -----
+    floors = _sealed_floors()
     summary = wf.summarize_fold_observations(observations, floors)
 
     evaluated_at_value = evaluated_at if evaluated_at is not None else _iso_utc_now()
@@ -389,11 +421,20 @@ def evaluate_sealed_verdict(
         "process_label": candidate_spec.get("process_label"),
         "outcome_basis": candidate_spec.get("outcome_basis", "mid"),
         "n": summary["n"],
+        # (r9) disclosure-only counts -- informational, never compared against a numeric floor at
+        # shard scope (see floors_applied below for the floor-labeled fields TC-4 targets).
         "n_sessions": summary["n_sessions"],
         "n_symbols": summary["n_symbols"],
-        # spec section 8.1: the artifact must be "sufficient to reproduce the verdict" -- condition 1
-        # is not reproducible from n/n_sessions/n_symbols alone (module docstring's T-1 disclosure).
-        "floors_applied": floors,
+        # spec section 8.1: the artifact must be "sufficient to reproduce the verdict". (r9) The
+        # ONLY sufficiency floor at shard scope is SEALED_MIN_OBSERVATIONS; session/symbol breadth
+        # are recorded as the literal string SEALED_BREADTH_NOT_APPLICABLE -- never a silent 1 --
+        # because they are structurally inapplicable to a one-symbol-day shard, never because they
+        # were unmet (TC-4).
+        "floors_applied": {
+            "min_observations": SEALED_MIN_OBSERVATIONS,
+            "min_signal_sessions": SEALED_BREADTH_NOT_APPLICABLE,
+            "min_symbols": SEALED_BREADTH_NOT_APPLICABLE,
+        },
         "effect": summary["effect"],
         "sign": summary["sign"],
         "missing": summary["missing"],
diff --git a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
index a9c445b..4171ac6 100644
--- a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
+++ b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
@@ -52,6 +52,14 @@
 # long-standing rule ("use a fresh root whenever the seeded composition changed") applies to this
 # extension exactly as it would to detector logic.
 #
+# goal-rapid-microscope-iter-18 extends this file once more, again in place: after the tick-dataset
+# fixtures above stage, it also runs seed_micro_graduation_iter18_fixture.py (a plain dataset +
+# vault-shard + real evaluate_sealed_verdict() call, never a hand-rolled JSON blob) so J-07's own
+# GET /research/desk/micro/graduation finally photographs a real, non-empty, discriminating
+# families entry on this rig instead of the honest-but-non-discriminating empty state every prior
+# browser pass recorded. Uses a symbol (PGQA) distinct from the PG tick fixtures above so the two
+# seed steps' datasets never collide.
+#
 # Usage:
 #   bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh [root_dir] [port]
 #
@@ -107,6 +115,11 @@ export TAPEOLOGY_JOURNAL_DB="$JOURNAL_DB"
 
 "$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_playbook_iter8_replay_rig.py" "$ROOT"
 
+# goal-rapid-microscope-iter-18 (J-07): seed ONE real, discriminating graduation family through the
+# now-fixed (r9/TR-30) evaluate_sealed_verdict() -- see seed_micro_graduation_iter18_fixture.py's
+# own docstring for the full seven-step sequence this exercises for real.
+"$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_micro_graduation_iter18_fixture.py" "$ROOT"
+
 echo "[playbook-iter8-replay-fixture-scoped-backend] root=$ROOT port=$PORT" >&2
 for var in TAPEOLOGY_BAR_DIR TAPEOLOGY_DESK_UNIVERSE_DIR TAPEOLOGY_DESK_PLAYBOOK_DIR \
            TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR \
diff --git a/apps/backend/tests/test_micro_sealed_evaluation.py b/apps/backend/tests/test_micro_sealed_evaluation.py
index 69f94cc..60879ea 100644
--- a/apps/backend/tests/test_micro_sealed_evaluation.py
+++ b/apps/backend/tests/test_micro_sealed_evaluation.py
@@ -2,6 +2,15 @@
 ``docs/rapid-validation-spec.md`` section 8.1) -- test-first contract: TC-1 through TC-9, per
 ``docs/phases/goal-rapid-microscope-iter-17.md``.
 
+**iteration 18 (r9 owner ruling 2026-08-20, TR-30) extends this file, never rewrites it.** The
+``_TINY_FLOORS`` candidate-spec override every PASS-path fixture below used to rely on is RETIRED
+(the exact mechanism r9 exists to close): every fixture that needs a "sufficient" verdict now
+supplies >= ``SEALED_MIN_OBSERVATIONS`` (30) REAL observation dicts from the single fixture shard
+instead. The TR-30-specific trap tests (`test_tr30_*`, TC-1..TC-7 of
+``docs/phases/goal-rapid-microscope-iter-18.md``, plus the mutation-proof) live in their own
+labeled block near the end of this file, distinct from the r6/TR-23 ``test_tc1``..``test_tc9``
+numbering above (a DIFFERENT trap's own TC-N scheme; the prefix disambiguates the two).
+
 Fixture-only throughout (goal.md's own "do not seed/mutate/expose real Vault data" instruction;
 zero real sealed shards exist this era) -- every scenario plants a REAL dataset + snapshot on disk
 (the ``test_micro_accessor.py`` ``_plant_dataset_and_snapshot`` precedent, so the evaluator's own
@@ -20,6 +29,7 @@ test so the fixture's own soundness does not rely on the mutation succeeding."""
 
 from __future__ import annotations
 
+import inspect
 import re
 
 import pytest
@@ -44,10 +54,6 @@ _ASSIGNED_AT = "2026-01-05T00:00:00.000000Z"
 _EXPOSED_AT = "2026-01-06T00:00:00.000000Z"
 _EVALUATED_AT = "2026-06-10T00:00:00.000000Z"
 
-# Tiny floors so a 3-observation hand-built fixture clears the "sufficient" status without needing
-# 30 real observations -- the test_walkforward.py `floors={"wf_fold_min_observations": 1, ...}`
-# precedent, mirrored exactly.
-_TINY_FLOORS = {"wf_fold_min_observations": 3, "wf_fold_min_signal_sessions": 1, "wf_fold_min_symbols": 1}
 _ECON_FLOOR = {"floor_bps": 5.0}
 
 
@@ -55,30 +61,32 @@ def _observation(session_date: str, symbol: str, value: float) -> dict:
     return {"session_date": session_date, "symbol": symbol, "value": value}
 
 
-def _passing_observations() -> list[dict]:
-    """Mean effect = 10.0 -- clears ``_ECON_FLOOR``'s 5.0 bps floor in the "long"/positive
-    direction. THE "correct" fixture TC-9 discriminates against."""
-    return [
-        _observation("2026-06-08", "PG", 10.0),
-        _observation("2026-06-08", "PG", 12.0),
-        _observation("2026-06-08", "PG", 8.0),
-    ]
+def _passing_observations(n: int = 30) -> list[dict]:
+    """(r9) >= ``SEALED_MIN_OBSERVATIONS`` REAL observations from the single fixture shard (PG /
+    2026-06-08 -- session/symbol breadth no longer matters at shard scope under r9, so every
+    observation shares the one session/symbol the fixture shard itself is keyed on). Deliberately
+    DIFFERENT values (never a repeated constant, iter-16's own lesson) symmetric around 10.0, so
+    the mean -- and therefore the recomputed effect -- is EXACTLY 10.0: clears ``_ECON_FLOOR``'s
+    5.0 bps floor in the "long"/positive direction. THE "correct" fixture TC-9 discriminates
+    against. ``n`` lets a caller take a strict PREFIX below the floor (TC-2/TR-30 TC-2)."""
+    values = [10.0 + (i - 14.5) for i in range(30)]  # -4.5 .. 24.5 step 1.0, symmetric -> mean 10.0
+    return [_observation("2026-06-08", "PG", v) for v in values[:n]]
 
 
-def _below_floor_observations() -> list[dict]:
-    """Mean effect = 1.0 -- POSITIVE (correct direction) but strictly below the 5.0 bps econ floor,
-    so it FAILS on magnitude alone, never on direction. Deliberately a DIFFERENT numeric value from
-    ``_passing_observations``'s own 10.0 (TC-9: never coincidentally equal)."""
-    return [
-        _observation("2026-06-08", "PG", 1.0),
-        _observation("2026-06-08", "PG", 1.2),
-        _observation("2026-06-08", "PG", 0.8),
-    ]
+def _below_floor_observations(n: int = 30) -> list[dict]:
+    """(r9) >= ``SEALED_MIN_OBSERVATIONS`` REAL observations, mean effect = 1.0 -- POSITIVE
+    (correct direction) but strictly below the 5.0 bps econ floor, so it FAILS on magnitude alone,
+    never on direction. Deliberately a DIFFERENT numeric value from ``_passing_observations``'s own
+    10.0 (TC-9: never coincidentally equal)."""
+    values = [1.0 + (i - 14.5) for i in range(30)]  # -13.5 .. 15.5 step 1.0, symmetric -> mean 1.0
+    return [_observation("2026-06-08", "PG", v) for v in values[:n]]
 
 
 def _insufficient_observations() -> list[dict]:
-    """Only 2 observations -- below ``_TINY_FLOORS``'s own ``wf_fold_min_observations: 3`` floor."""
-    return [_observation("2026-06-08", "PG", 10.0), _observation("2026-06-08", "PG", 12.0)]
+    """(r9/TR-30 TC-2) Exactly 29 real observations -- one short of ``SEALED_MIN_OBSERVATIONS`` =
+    30, the ONLY sufficiency floor at shard scope. A strict prefix of ``_passing_observations``,
+    never a second, differently-shaped fixture."""
+    return _passing_observations(n=29)
 
 
 def _rig(tmp_path):
@@ -117,15 +125,22 @@ def _candidate_spec(
     *, family_root_id: str, candidate_id: str = "cand-1", family_id: str = "fam-a",
     spec_hash: str = "spec-hash-1", sidedness: str = "long", econ_floor: dict | None = _ECON_FLOOR,
     evidence_class: str = wf.EVIDENCE_CLASS_HISTORICAL_OOS, process_label: str = wf.PROCESS_LABEL_RULE,
-    registered_at: str = _SPEC_REGISTERED_AT, rule_hash: str | None = None, floors: dict | None = _TINY_FLOORS,
+    registered_at: str = _SPEC_REGISTERED_AT, rule_hash: str | None = None, floors: dict | None = None,
 ) -> dict:
-    return {
+    """(r9) ``floors`` defaults to ``None`` and, when ``None``, the returned dict carries NO
+    ``"floors"`` key at all -- the "no override" shape ``evaluate_sealed_verdict`` requires to
+    resolve cleanly. Passing an explicit ``floors={...}`` dict is how a test constructs the
+    refused-override shape (TR-30 TC-1/TC-5) -- the retired mechanism this module no longer
+    honours, kept here ONLY so a test can exercise the refusal, never to make it work again."""
+    spec = {
         "family_root_id": family_root_id, "candidate_id": candidate_id, "family_id": family_id,
         "spec_hash": spec_hash, "sidedness": sidedness, "econ_floor": econ_floor,
         "evidence_class": evidence_class, "process_label": process_label, "registered_at": registered_at,
         "sealed_pass_rule_hash": rule_hash if rule_hash is not None else sealed_eval.sealed_pass_rule_hash(),
-        "floors": floors,
     }
+    if floors is not None:
+        spec["floors"] = floors
+    return spec
 
 
 def _family_root_id(seed: str) -> str:
@@ -173,7 +188,7 @@ def test_tc2_the_full_mandatory_sequence_derives_a_deterministic_pass_verdict_an
     assert row["evidence_class"] == wf.EVIDENCE_CLASS_HISTORICAL_OOS
     assert row["process_label"] == wf.PROCESS_LABEL_RULE
     assert row["outcome_basis"] == "mid"
-    assert row["n"] == 3
+    assert row["n"] == 30
     assert row["n_sessions"] == 1
     assert row["n_symbols"] == 1
     assert row["effect"] == pytest.approx(10.0)
@@ -452,7 +467,7 @@ def test_tc9_the_correct_and_corrupted_recomputed_effects_are_different_numbers_
     ``_below_floor_observations()`` recomputes to effect=1.0 (correct direction, below floor ->
     FAIL). 10.0 != 1.0 -- the two paths' own recomputed numbers are never coincidentally equal, so
     this assertion cannot pass for the wrong reason (iteration-16's own named lesson)."""
-    floors = _TINY_FLOORS
+    floors = sealed_eval._sealed_floors()  # (r9) the FIXED, evaluator-owned floors -- never a candidate override
     passing_summary = wf.summarize_fold_observations(_passing_observations(), floors)
     below_floor_summary = wf.summarize_fold_observations(_below_floor_observations(), floors)
 
@@ -533,19 +548,24 @@ def test_insufficient_verdict_is_never_coerced_to_fail_or_pass_in_the_graduation
         g.evaluate_sealed_survivor_transition(grad_ledger, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
 
 
-# === iteration-17 AUDIT finding B1: the floors condition 1 ACTUALLY applied are on the artifact ========
+# === iteration-17 AUDIT finding B1, RETIRED by r9/TR-30 (iteration 18): the artifact records the
+# EVALUATOR-OWNED floors_applied -- a candidate spec can no longer narrow (or widen) anything.
+# Replaces the pre-r9 test of the exact "candidate spec MAY NARROW them" behavior this rule retires
+# (that test asserted ``_resolved_floors({"floors": {...}})`` honoured a caller override -- the
+# function itself no longer exists at all, see the TR-30 mutation-proof test below). ===================
 
 
-def test_the_artifact_records_the_floors_condition_1_actually_applied(tmp_path):
+def test_the_artifact_records_the_evaluator_owned_floors_never_a_candidate_narrowed_value(tmp_path):
     """spec section 8.1 requires the evaluation artifact to be "sufficient to reproduce the
-    verdict". Condition 1 is decided by ``summarize_fold_observations``'s RESOLVED floors, which a
-    candidate spec may NARROW below the section-1 constants ``sealed_pass_rule_hash()`` embeds --
-    so the floors actually applied are recorded verbatim and a narrowed floor can never be silent
-    in a permanent verdict (see the module docstring's own T-1 disclosure; owner-owed)."""
+    verdict". (r9) Condition 1 is now decided ENTIRELY by this module's own pinned
+    ``SEALED_MIN_OBSERVATIONS`` and fixed breadth policy -- never anything a candidate spec
+    supplies. ``floors_applied`` is therefore IDENTICAL on every persisted artifact, regardless of
+    what a candidate spec might otherwise wish it recorded (it cannot even ask any more -- carrying
+    a ``floors`` key is refused outright, proven separately by the TR-30 TC-1/TC-5 tests below)."""
     dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
-    family_root_id = _family_root_id("floors-applied")
+    family_root_id = _family_root_id("floors-applied-r9")
     shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
-    candidate_spec = _candidate_spec(family_root_id=family_root_id)  # carries _TINY_FLOORS
+    candidate_spec = _candidate_spec(family_root_id=family_root_id)  # (r9) carries NO floors key at all
     accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
     grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
 
@@ -556,22 +576,19 @@ def test_the_artifact_records_the_floors_condition_1_actually_applied(tmp_path):
     )["row"]
 
     assert row["verdict"] == sealed_eval.SEALED_VERDICT_PASS
-    # the RESOLVED triple this verdict was actually decided under -- the fixture's NARROWED floors.
+    # the EVALUATOR-OWNED triple this verdict was actually decided under -- fixed, never candidate-controlled.
     assert row["floors_applied"] == {
-        "wf_fold_min_observations": 3, "wf_fold_min_signal_sessions": 1, "wf_fold_min_symbols": 1,
-    }
-    section_1_pinned = {
-        "wf_fold_min_observations": wf.WF_FOLD_MIN_OBSERVATIONS,
-        "wf_fold_min_signal_sessions": wf.WF_FOLD_MIN_SIGNAL_SESSIONS,
-        "wf_fold_min_symbols": wf.WF_FOLD_MIN_SYMBOLS,
+        "min_observations": sealed_eval.SEALED_MIN_OBSERVATIONS,
+        "min_signal_sessions": sealed_eval.SEALED_BREADTH_NOT_APPLICABLE,
+        "min_symbols": sealed_eval.SEALED_BREADTH_NOT_APPLICABLE,
     }
-    # 3/1/1 vs 30/8/2 -- deliberately different numbers, so the narrowing is VISIBLE on the
-    # permanent record even though `rule_hash` (condition 4's identity check) pins section 1.
-    assert row["floors_applied"] != section_1_pinned
+    assert row["floors_applied"]["min_observations"] == 30
+    # never a silent integer -- the literal string, every time (TC-4).
+    assert row["floors_applied"]["min_signal_sessions"] == "not_applicable_single_shard"
+    assert row["floors_applied"]["min_symbols"] == "not_applicable_single_shard"
+    assert not isinstance(row["floors_applied"]["min_signal_sessions"], int)
+    assert not isinstance(row["floors_applied"]["min_symbols"], int)
     assert row["rule_hash"] == sealed_eval.sealed_pass_rule_hash()
-    # a spec carrying NO override resolves to the section-1 constants verbatim.
-    assert sealed_eval._resolved_floors({}) == section_1_pinned
-    assert sealed_eval._resolved_floors({"floors": {"wf_fold_min_symbols": 5}})["wf_fold_min_symbols"] == 5
 
 
 # === guard: no threshold-sweep loop in this new module (goal.md Constraints: "new micro modules add
@@ -621,3 +638,244 @@ def test_the_evaluator_refuses_a_fenced_accessor(tmp_path):
             candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
             observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
         )
+
+
+# ==========================================================================================
+# === TR-30 (spec section 9, r9 owner ruling 2026-08-20) -- "sealed sufficiency is
+# evaluator-owned": docs/phases/goal-rapid-microscope-iter-18.md TC-1..TC-7, plus the
+# mutation-proof. Distinct TC-N numbering from the r6/TR-23 ``test_tc1``..``test_tc9`` block
+# above -- prefixed ``test_tr30_`` throughout so grep can tell the two traps' tests apart.
+# ==========================================================================================
+
+
+def test_tr30_tc1_a_floors_override_with_one_observation_is_refused_never_a_pass(tmp_path):
+    """A candidate_spec carrying ``floors={"wf_fold_min_observations": 1, ...}`` -- the exact
+    caller-controlled shortcut r9 retires -- is refused OUTRIGHT, even paired with just one
+    observation that the override would otherwise have called "sufficient". No artifact is ever
+    persisted."""
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("tr30-tc1")
+    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
+    candidate_spec = _candidate_spec(
+        family_root_id=family_root_id,
+        floors={"wf_fold_min_observations": 1, "wf_fold_min_signal_sessions": 1, "wf_fold_min_symbols": 1},
+    )
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    with pytest.raises(sealed_eval.SealedEvaluationRefusedError, match="floors"):
+        sealed_eval.evaluate_sealed_verdict(
+            grad_ledger, shard_ledger, universe_ledger, accessor,
+            candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+            observations=[_observation("2026-06-08", "PG", 10.0)],  # exactly ONE observation
+            evaluated_at=_EVALUATED_AT,
+        )
+    assert g.sealed_evaluations_for_family(grad_ledger, family_root_id) == []
+
+
+def test_tr30_tc2_twenty_nine_observations_reads_insufficient(tmp_path):
+    """(r9) With NO floors override, 29 real observations -- one short of
+    ``SEALED_MIN_OBSERVATIONS`` = 30 -- reads ``insufficient``, never a pass."""
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("tr30-tc2")
+    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
+    candidate_spec = _candidate_spec(family_root_id=family_root_id)
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    observations = _passing_observations(n=29)
+    assert len(observations) == 29
+    row = sealed_eval.evaluate_sealed_verdict(
+        grad_ledger, shard_ledger, universe_ledger, accessor,
+        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+        observations=observations, evaluated_at=_EVALUATED_AT,
+    )["row"]
+    assert row["verdict"] == sealed_eval.SEALED_VERDICT_INSUFFICIENT
+
+
+def test_tr30_tc3_thirty_otherwise_valid_observations_can_clear_sufficiency(tmp_path):
+    """(r9) With NO floors override, 30 otherwise-valid observations (correct registered
+    sidedness, magnitude at or above the family's econ floor, ``historical_oos``/``rule_process``)
+    reads ``pass`` -- sufficiency can clear at exactly the pinned constant."""
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("tr30-tc3")
+    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
+    candidate_spec = _candidate_spec(family_root_id=family_root_id)
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    observations = _passing_observations(n=30)
+    assert len(observations) == 30
+    row = sealed_eval.evaluate_sealed_verdict(
+        grad_ledger, shard_ledger, universe_ledger, accessor,
+        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+        observations=observations, evaluated_at=_EVALUATED_AT,
+    )["row"]
+    assert row["verdict"] == sealed_eval.SEALED_VERDICT_PASS
+    # test_tr30_tc4/tc6 below each build their OWN fresh fixture rather than reusing this row -- a
+    # persisted artifact is one-shot per (family_root_id, dataset_id), so it cannot be shared.
+
+
+def test_tr30_tc4_the_breadth_fields_are_the_literal_string_never_the_integer_one(tmp_path):
+    """(r9) The TC-3 persisted artifact's session-breadth and symbol-breadth fields both equal the
+    literal string ``"not_applicable_single_shard"`` -- never the integer ``1``, even though this
+    fixture's OWN observations happen to span exactly one session and one symbol (which is why the
+    "silently 1" failure mode would be so easy to miss without this explicit type check)."""
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("tr30-tc4")
+    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
+    candidate_spec = _candidate_spec(family_root_id=family_root_id)
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    row = sealed_eval.evaluate_sealed_verdict(
+        grad_ledger, shard_ledger, universe_ledger, accessor,
+        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+        observations=_passing_observations(n=30), evaluated_at=_EVALUATED_AT,
+    )["row"]
+
+    assert row["verdict"] == sealed_eval.SEALED_VERDICT_PASS
+    session_breadth = row["floors_applied"]["min_signal_sessions"]
+    symbol_breadth = row["floors_applied"]["min_symbols"]
+    assert session_breadth == "not_applicable_single_shard"
+    assert symbol_breadth == "not_applicable_single_shard"
+    assert session_breadth != 1
+    assert symbol_breadth != 1
+    assert not isinstance(session_breadth, int)
+    assert not isinstance(symbol_breadth, int)
+    # the informational (never floor-compared) counts stay real integers, separately.
+    assert row["n_sessions"] == 1
+    assert row["n_symbols"] == 1
+    assert isinstance(row["n_sessions"], int)
+    assert isinstance(row["n_symbols"], int)
+
+
+def test_tr30_tc5_two_variants_differing_only_in_a_caller_floor_value_both_refused(tmp_path):
+    """(r9) Two candidate_spec variants differing ONLY in a caller-supplied floor value (5 vs 25
+    for ``wf_fold_min_observations``), each paired with the SAME 30 real observations, both raise
+    ``SealedEvaluationRefusedError`` -- neither floor value ever reaches a persisted verdict, and
+    changing the floor value changes NOTHING about the outcome (both are refused identically)."""
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("tr30-tc5")
+    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    observations = _passing_observations(n=30)
+
+    spec_low = _candidate_spec(family_root_id=family_root_id, floors={"wf_fold_min_observations": 5})
+    with pytest.raises(sealed_eval.SealedEvaluationRefusedError, match="floors"):
+        sealed_eval.evaluate_sealed_verdict(
+            grad_ledger, shard_ledger, universe_ledger, accessor,
+            candidate_spec=spec_low, dataset_id=dataset_meta["id"],
+            observations=observations, evaluated_at=_EVALUATED_AT,
+        )
+    assert g.sealed_evaluations_for_family(grad_ledger, family_root_id) == []
+
+    spec_high = _candidate_spec(family_root_id=family_root_id, floors={"wf_fold_min_observations": 25})
+    with pytest.raises(sealed_eval.SealedEvaluationRefusedError, match="floors"):
+        sealed_eval.evaluate_sealed_verdict(
+            grad_ledger, shard_ledger, universe_ledger, accessor,
+            candidate_spec=spec_high, dataset_id=dataset_meta["id"],
+            observations=observations, evaluated_at=_EVALUATED_AT,
+        )
+    # neither attempt ever reached a persisted verdict -- the single shot is still untouched.
+    assert g.sealed_evaluations_for_family(grad_ledger, family_root_id) == []
+
+
+def test_tr30_tc6_rule_hash_agrees_with_fresh_computation_and_the_runtime_constant(tmp_path):
+    """(r9) The persisted PASS artifact's ``rule_hash`` agrees byte-for-byte with
+    ``sealed_pass_rule_hash()`` computed fresh, and with the ``SEALED_MIN_OBSERVATIONS`` constant
+    actually used at runtime (proven by the fact that exactly 30 observations -- the pinned
+    constant's own value -- were what made this verdict "pass" rather than "insufficient")."""
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("tr30-tc6")
+    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
+    candidate_spec = _candidate_spec(family_root_id=family_root_id)
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    row = sealed_eval.evaluate_sealed_verdict(
+        grad_ledger, shard_ledger, universe_ledger, accessor,
+        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+        observations=_passing_observations(n=30), evaluated_at=_EVALUATED_AT,
+    )["row"]
+
+    fresh_hash = sealed_eval.sealed_pass_rule_hash()
+    assert row["rule_hash"] == fresh_hash
+    assert sealed_eval.sealed_pass_parameters()["sealed_min_observations"] == sealed_eval.SEALED_MIN_OBSERVATIONS
+    assert row["floors_applied"]["min_observations"] == sealed_eval.SEALED_MIN_OBSERVATIONS
+    assert row["n"] == sealed_eval.SEALED_MIN_OBSERVATIONS == 30
+    assert row["verdict"] == sealed_eval.SEALED_VERDICT_PASS  # 30 obs cleared the runtime constant for real
+
+
+def test_tr30_tc7_an_insufficient_verdict_still_consumes_the_single_shot(tmp_path):
+    """(r9/TR-12 preserved) After a 29-observation ``insufficient`` verdict persists against an
+    assigned-and-exposed shard, a second ``evaluate_sealed_verdict`` call for the SAME
+    (``family_root_id``, ``dataset_id``) pair is refused -- no fresh shard on thin data, which
+    would be repeated holdout sampling."""
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("tr30-tc7")
+    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
+    candidate_spec = _candidate_spec(family_root_id=family_root_id)
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    first = sealed_eval.evaluate_sealed_verdict(
+        grad_ledger, shard_ledger, universe_ledger, accessor,
+        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+        observations=_passing_observations(n=29), evaluated_at=_EVALUATED_AT,
+    )
+    assert first["row"]["verdict"] == sealed_eval.SEALED_VERDICT_INSUFFICIENT
+
+    with pytest.raises(g.GraduationTransitionRefusedError, match="never a second draw"):
+        sealed_eval.evaluate_sealed_verdict(
+            grad_ledger, shard_ledger, universe_ledger, accessor,
+            candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+            observations=_passing_observations(n=30), evaluated_at="2026-06-11T00:00:00.000000Z",
+        )
... [diff_bound] apps/backend/tests/test_micro_sealed_evaluation.py: 46 more diff lines omitted — Read the file for full detail
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 7 +++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl | 2 ++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
