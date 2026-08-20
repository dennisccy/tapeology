# Iteration diff (bounded)

Files changed: 9. Shown in full: 5.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/micro_graduation.py` (119 lines not shown)
- `apps/backend/tests/test_micro_graduation.py` (17 lines not shown)
- `apps/backend/app/research/micro_sealed_evaluation.py` (24 lines not shown)
- `apps/backend/tests/test_micro_sealed_evaluation.py` (229 lines not shown)

```diff
diff --git a/apps/backend/app/research/micro_accessor.py b/apps/backend/app/research/micro_accessor.py
index 165f300..c951a06 100644
--- a/apps/backend/app/research/micro_accessor.py
+++ b/apps/backend/app/research/micro_accessor.py
@@ -20,8 +20,9 @@ module existed -- this is the "generic hook a J-06 vault can extend without re-d
 discipline" the goal.md IN SCOPE names, proven now on a fixture (TC-2) rather than left unbuilt
 and unproven until J-06 lands.
 
-**Two callers, two disciplines (a disclosed interpretation call, T-1).** ``micro_join.py`` and
-``scout.py`` are re-pointed THROUGH this module this iteration (TR-3's import-ban), but their own
+**Two callers, two disciplines (a disclosed interpretation call, T-1) -- corrected iter-17: NO
+current production caller constructs an origin-fenced read.** ``micro_join.py`` and ``scout.py``
+are re-pointed THROUGH this module this iteration (TR-3's import-ban), but their own
 served/ledgered values must stay BYTE-IDENTICAL (TC-4, TC-5) -- they have never been
 chronologically fenced, and the corpus they read (the legacy tick corpus) is r2-pre-marked
 EXPOSED for its entire span regardless. Fencing them now would be a silent, unrequested behavior
@@ -31,10 +32,21 @@ the exposure registry either -- appending a hash-chained row on every one of ``s
 extract_anchors``'s thousands-of-anchors-per-dataset calls would reintroduce exactly the O(n)-
 per-read cost the iter-4 audit's perf fixes eliminated, for a registry entry that would be
 redundant with r2's own initialization (every window of the legacy/playbook corpus is ALREADY
-marked exposed from the moment the registry exists -- see ``ExposureRegistry`` below). Only
-``walkforward.py``'s OWN origin-fenced reads (an ``origin`` given, an ``ExposureRegistry`` given)
-participate in exposure logging -- the one path where "was this window ever served before?" is an
-actual, load-bearing question this era asks.
+marked exposed from the moment the registry exists -- see ``ExposureRegistry`` below).
+``micro_sealed_evaluation.py`` (J-07/TR-23, iteration 17) is re-pointed through this module too --
+its shard read is a POST-exposure, whole-shard outcome recomputation, not a rolling-origin
+walk-forward fold, so it is a THIRD ``origin=None`` unfenced caller, not a fenced one.
+
+**The FENCED mode is a real, tested capability of this class -- not a claim that a fenced
+production caller exists.** An ``origin`` AND an ``ExposureRegistry`` supplied together make a read
+participate in exposure logging (the "was this window ever served before?" question) --
+proven directly by ``test_origin_fenced_mode_with_a_registry_logs_exactly_one_exposure_entry``. But
+as of iteration 17, confirmed by a direct grep of every ``MicroAccessor(`` construction site in
+``app/``, NO production module actually constructs one this way: ``walkforward.py`` itself never
+constructs a ``MicroAccessor`` at all -- it works over abstract, caller-supplied ``observations``
+per its own "one abstract input" design, never raw snapshot rows directly. The fenced mode remains
+exactly what it has always been: a capability this class offers, proven on fixtures, available to a
+FUTURE rolling-origin caller -- never (today) an actually-exercised production path.
 
 **The exposure registry (section 6.7, r2).** ``ExposureRegistry`` is a corpus-scoped, hash-chained
 ledger (``micro_chain_ledger.HashChainedLedger``) of ``{surface, window, corpus_id, logged_at}``
diff --git a/apps/backend/app/research/micro_graduation.py b/apps/backend/app/research/micro_graduation.py
index 442e741..d7169a0 100644
--- a/apps/backend/app/research/micro_graduation.py
+++ b/apps/backend/app/research/micro_graduation.py
@@ -28,24 +28,28 @@ never guesses a join" discipline ``evaluate_mode_b_fold`` itself uses for ``spec
 future join (a Scout candidate registering ITS OWN sequence_id at Mode-B spec time) is a natural
 J-08/J-09 wiring concern, not invented here.
 
-**The sealed-shard EVALUATION verdict is caller-supplied, not computed here -- a disclosed T-1
-interpretation call.** Spec section 8 state 3 requires "additionally passed its single-shot
-root-family-level sealed-shard evaluation (section 7.4, keyed on family_root_id) under a spec frozen
-before assignment" as a CONDITION -- it does not prescribe the statistical MACHINERY that produces a
-pass/fail verdict from a sealed shard's exposed event data (that would be a Mode-B-style evaluation
-run through the accessor against real vault data, which does not exist anywhere in this codebase yet
-and is out of THIS iteration's scope: zero real sealed shards exist this era, J-06 step 4 is
-human-blocked, and TR-3/accessor territory is explicitly deferred to a dedicated J-10 hardening
-iteration). ``vault.py`` itself carries no pass/fail concept at all -- only shard LIFECYCLE state
-(sealed/assigned/exposed). So ``record_sealed_evaluation`` below is handed an ALREADY-COMPUTED
-``passed`` verdict (mirroring ``walkforward.py``'s own "a corpus-specific reader feeds a
-corpus-agnostic statistical core" split for its Mode-B evaluator) and is responsible for exactly the
-TWO things spec section 8 DOES specify: (1) confirming, via ``vault.py``'s existing, UNMODIFIED
-``build_vault_state`` (never a new vault.py function), that the named shard genuinely reached
-``exposed`` for this EXACT ``family_root_id`` before any verdict is ever recorded against it -- never
-trusting the caller's claim alone; and (2) recording that verdict PERMANENTLY, exactly once per
-(family_root_id, dataset_id) (TR-12) -- pass OR fail, since spec section 7.4's own words are "a
-failed sealed verdict is a permanent root-family fact carried in every later export bundle".
+**The sealed-shard EVALUATION verdict now has a named owner -- ``micro_sealed_evaluation.py`` (r6
+owner ruling, 2026-08-18, spec section 8.1, "the sealed verdict has one owner").** Iteration 10's
+``record_sealed_evaluation`` used to accept an ALREADY-COMPUTED ``passed: bool`` straight from its
+caller, disclosed at the time as a T-1 placeholder because the statistical machinery to derive that
+boolean "does not exist anywhere in this codebase yet". That machinery now exists:
+``micro_sealed_evaluation.evaluate_sealed_verdict`` runs the full seven-step mandatory sequence
+(require an assigned-then-exposed shard frozen-before-assignment; verify the candidate's registered
+spec; obtain the shard through the accessor; RECOMPUTE the outcome via
+``walkforward.summarize_fold_observations``, never trust a caller-computed effect; derive a
+tri-state PASS/FAIL/``insufficient`` verdict from ``SEALED_PASS_RULE_V1``'s five conditions) and
+calls THROUGH to ``record_sealed_evaluation`` below for the actual write. This module's own role is
+therefore exactly what spec section 8.1's opening line says it should be: "the ledger owns history;
+the evaluator owns the answer" -- ``record_sealed_evaluation`` below no longer accepts a bare
+``passed: bool`` AT ALL (that parameter shape is structurally gone, not merely deprecated); it
+accepts a whole, already-derived ``artifact: dict`` and (1) persists it PERMANENTLY, exactly once
+per (family_root_id, dataset_id) (TR-12) -- pass, fail, OR ``insufficient`` alike, since spec
+section 7.4's own words are "a failed sealed verdict is a permanent root-family fact carried in
+every later export bundle" -- and (2) enforces the single-shot discipline (an identical repeat is an
+idempotent replay; a genuinely different second attempt is refused). It does NOT re-confirm vault
+exposure binding a second time -- that confirmation is ``micro_sealed_evaluation.py``'s own step 1/3
+responsibility (checked once, by the module that actually reads the shard), never duplicated here as
+a second, independently-valued implementation of the same vault-state check.
 
 **The export bundle is buildable for ANY ledgered family, at ANY state -- not gated to
 ``sealed_survivor``+.** This is what makes TC-6's "a failed-sealed twin's permanent failed verdict
@@ -59,14 +63,27 @@ earned by attempting to build a bundle for a ``sealed_survivor`` candidate and h
 
 **No new module constant, no ``graduation_parameters()``.** Every sibling module with its own tuned
 constants (``scout.py``'s ``SCOUT_SCREEN_ALPHA``, ``walkforward.py``'s ``WF_MIN_SUFFICIENT_FOLDS``,
-...) embeds a ``*_parameters()`` function so a persisted record can key on their hash (the era's
-Parameters discipline, goal.md Constraints). This module introduces NO tunable numeric constant of
-its own -- ``WF_SURVIVOR_RULE_V1`` is evaluated ENTIRELY by ``walkforward.sequence_verdict``
-(consulted, never reimplemented, per this iteration's own spec), and the sealed-shard verdict is
-caller-supplied. A ``graduation_parameters()`` function would have nothing genuine to embed, so none
+``micro_sealed_evaluation.py``'s ``SEALED_PASS_RULE_V1``...) embeds a ``*_parameters()`` function so
+a persisted record can key on their hash (the era's Parameters discipline, goal.md Constraints).
+This module introduces NO tunable numeric constant of its own -- ``WF_SURVIVOR_RULE_V1`` is
+evaluated ENTIRELY by ``walkforward.sequence_verdict`` and the sealed-shard verdict ENTIRELY by
+``micro_sealed_evaluation.evaluate_sealed_verdict`` (both consulted, never reimplemented, per this
+era's own spec). A ``graduation_parameters()`` function would have nothing genuine to embed, so none
 exists -- inventing one would be exactly the "config for behavior the spec fixed" the simplicity bar
 forbids.
 
+**The lineage-wide confirmation boundary (r6 owner ruling, spec section 8.2, TR-24).** The proposed
+confirmation boundary used to be "the latest timestamp on this ONE sequence's own surviving evidence
+rows" -- exactly the naive formula the owner ruling REJECTED, because it lets lineage knowledge be
+laundered through candidate selection (register three siblings, discard the two whose evidence is
+inconveniently recent, keep the one whose own evidence looks old). The corrected formula scans the
+WHOLE ``family_root_id`` lineage -- every scout trial (survivors AND kills), every walk-forward fold
+of ANY verdict/class/process-label, every sealed evaluation of ANY verdict including FAIL/
+``insufficient`` -- for the LATEST instant any of them consumed, then adds the applicable embargo,
+then rounds forward to the first eligible session boundary. See ``_lineage_data_frontier``/
+``_evidence_safe_boundary``/``_proposed_confirmation_boundary`` below for the full derivation and
+this iteration's own disclosed embargo-application interpretation call.
+
 **Idempotent, identity-keyed, replay-safe (the iter-5 lesson, named for this exact journey in this
 iteration's own spec).** Every state-advancing function below checks FIRST whether the target
 transition (or, for sealed evaluation, the identical (family_root_id, dataset_id) verdict) is
@@ -81,11 +98,12 @@ from __future__ import annotations
 import hashlib
 import json
 import os
-from datetime import datetime, timezone
+from datetime import date, datetime, timedelta, timezone
 from pathlib import Path
 
 from . import vault
 from . import walkforward as wf
+from . import walkforward_ledger as wl
 from .micro_chain_ledger import HashChainedLedger
 from .scout_ledger import ScoutLedger, distinct_variant_count
 
@@ -114,6 +132,7 @@ __all__ = [
     "bundle_validates",
     "evaluate_referee_handoff_ready_transition",
     "list_graduation_families",
+    "final_confirmation_boundary",
 ]
 
 # === spec section 8's four states, strictly ordered (transcribed verbatim) ==========================
@@ -337,67 +356,54 @@ def evaluate_walkforward_survivor_transition(
 
 def record_sealed_evaluation(
     graduation_ledger: GraduationLedger,
-    vault_shard_ledger: "vault.VaultShardLedger",
-    vault_universe_ledger: "vault.VaultUniverseLedger",
     *,
     family_root_id: str,
     dataset_id: str,
-    spec_hash: str,
-    passed: bool,
-    detail: dict | None = None,
-    evaluated_at: str | None = None,
+    artifact: dict,
 ) -> dict:
-    """Records a single-shot sealed-shard evaluation verdict (module docstring: the verdict itself
-    is caller-supplied; this function's own job is the confirmation + the permanent recording).
-    Confirms, via ``vault.build_vault_state`` (existing, unmodified), that ``dataset_id`` is
-    genuinely ``exposed`` and bound to this EXACT ``family_root_id`` -- refusing
-    (``GraduationTransitionRefusedError``) a claimed evaluation against a shard that was never
-    actually exposed to this family, rather than trusting the caller's say-so.
+    """Persists an ALREADY-COMPUTED sealed-shard evaluation artifact -- spec section 8.1's "the
+    ledger owns history; the evaluator owns the answer" (r6 owner ruling). This function's ONLY
+    caller is ``micro_sealed_evaluation.evaluate_sealed_verdict`` (the sole scientific owner of the
+    verdict, module docstring); it accepts a whole, already-derived ``artifact`` dict, never a bare
+    caller-supplied ``passed: bool`` -- TC-1: the OLD shape's ``passed`` parameter no longer exists
+    on this function's signature AT ALL, so a call built the old way raises ``TypeError`` at the
+    Python argument-binding level, before any of this function's own logic ever runs. This function
+    does NOT re-confirm vault exposure binding (the evaluator's own step 1/3 already did, via the
+    SAME ``vault.build_vault_state`` call this function used to make itself -- never duplicated
+    here as a second, independently-valued check of the same fact).
 
     Single-shot (TR-12): a SECOND call for the identical ``(family_root_id, dataset_id)`` pair is an
-    idempotent ``replayed`` no-op when it repeats the SAME ``(passed, spec_hash)`` verdict (a benign
-    repeat of an operator act, the ``register_fold_spec`` precedent), but is REFUSED outright when it
-    would record a DIFFERENT verdict -- "sealed exposure is ... never a second draw" (goal.md
-    anti-goal) means even a caller HONESTLY re-evaluating never gets to overwrite or supplement a
-    verdict already on permanent record."""
+    idempotent ``replayed`` no-op when it repeats a BYTE-IDENTICAL artifact (a benign repeat of an
+    operator act, the ``register_fold_spec`` precedent), but is REFUSED outright when the artifact
+    content differs -- "sealed exposure is ... never a second draw" (goal.md anti-goal) means even a
+    caller HONESTLY re-evaluating never gets to overwrite or supplement a verdict already on
+    permanent record."""
     existing_for_shard = [
         row for row in sealed_evaluations_for_family(graduation_ledger, family_root_id)
         if row.get("dataset_id") == dataset_id
     ]
+    artifact_content = dict(artifact)
     if existing_for_shard:
         prior = existing_for_shard[-1]
-        if prior["passed"] == bool(passed) and prior["spec_hash"] == spec_hash:
+        prior_content = {
+            k: v for k, v in prior.items()
+            if k not in ("row_kind", "family_root_id", "dataset_id", "row_index", "prev_hash", "row_hash")
+        }
+        if prior_content == artifact_content:
             return {"transition": TRANSITION_REPLAYED, "row": dict(prior)}
         raise GraduationTransitionRefusedError(
             family_root_id, GRADUATION_STATE_SEALED_SURVIVOR,
             f"a sealed-shard evaluation for dataset_id {dataset_id!r} is ALREADY recorded "
-            f"(passed={prior['passed']!r}, spec_hash={prior['spec_hash']!r}); a second, DIFFERENT "
-            f"evaluation attempt (passed={bool(passed)!r}, spec_hash={spec_hash!r}) is refused "
-            "(spec section 7.4/TR-12): sealed exposure is single-shot, never a second draw",
-        )
-
-    vault_state = vault.build_vault_state(vault_shard_ledger, vault_universe_ledger)
-    shard_entry = next((s for s in vault_state["shards"] if s.get("dataset_id") == dataset_id), None)
-    if (
-        shard_entry is None
-        or shard_entry.get("exposure_state") != vault.STATE_EXPOSED
-        or shard_entry.get("family_root_id") != family_root_id
-    ):
-        raise GraduationTransitionRefusedError(
-            family_root_id, GRADUATION_STATE_SEALED_SURVIVOR,
-            f"dataset_id {dataset_id!r} is not an EXPOSED vault shard bound to this exact "
-            "family_root_id -- refused (spec section 7.4): a sealed-shard evaluation can only be "
-            "recorded against a shard genuinely exposed to this family",
+            f"(verdict={prior.get('verdict')!r}); a second, DIFFERENT evaluation attempt "
+            f"(verdict={artifact_content.get('verdict')!r}) is refused (spec section 7.4/TR-12): "
+            "sealed exposure is single-shot, never a second draw",
         )
 
     fields = {
         "row_kind": ROW_KIND_SEALED_EVALUATION,
         "family_root_id": family_root_id,
         "dataset_id": dataset_id,
-        "spec_hash": spec_hash,
-        "passed": bool(passed),
-        "detail": dict(detail) if detail else {},
-        "evaluated_at": evaluated_at if evaluated_at is not None else _iso_utc_now(),
+        **artifact_content,
     }
     row = graduation_ledger.append_row(fields)
     return {"transition": TRANSITION_APPENDED, "row": row}
@@ -411,12 +417,19 @@ def evaluate_sealed_survivor_transition(
     evaluated_at: str | None = None,
 ) -> dict:
     """Requires the family to already be ``walkforward_survivor`` (states are strictly ordered,
-    spec section 8's own opening line -- never skipped) and requires an ALREADY-RECORDED, PASSING
-    ``record_sealed_evaluation`` verdict for ``(family_root_id, dataset_id)``. A recorded FAILING
-    verdict refuses this transition outright (TC-6: the state never advances past
-    ``walkforward_survivor``, but the failed verdict itself stays permanently on record via
-    ``sealed_evaluations_for_family``/``build_export_bundle``). Idempotent + identity-keyed exactly
-    like ``evaluate_walkforward_survivor_transition`` above."""
+    spec section 8's own opening line -- never skipped) and requires an ALREADY-RECORDED sealed
+    evaluation artifact for ``(family_root_id, dataset_id)`` whose ``verdict`` field is the literal
+    string ``"pass"``. A recorded ``"fail"`` OR ``"insufficient"`` verdict refuses this transition
+    outright (TC-6: the state never advances past ``walkforward_survivor``, but the verdict itself
+    stays permanently on record, still distinguishable, via ``sealed_evaluations_for_family``/
+    ``build_export_bundle`` -- never silently coerced to one boolean). The literal string ``"pass"``
+    is compared here rather than importing ``micro_sealed_evaluation.SEALED_VERDICT_PASS`` -- a
+    disclosed, ONE-WAY-dependency interpretation call (T-1): ``micro_sealed_evaluation.py`` already
+    imports FROM this module (``GraduationLedger``, ``record_sealed_evaluation``), so importing back
+    would create a cycle; the three-value vocabulary (``"pass"``/``"fail"``/``"insufficient"``) is
+    frozen (spec section 8.1 point 1) and used in exactly this one spot, so a literal string carries
+    no real drift risk. Idempotent + identity-keyed exactly like
+    ``evaluate_walkforward_survivor_transition`` above."""
     already = [
         row for row in state_transitions_for_family(graduation_ledger, family_root_id)
         if row["to_state"] == GRADUATION_STATE_SEALED_SURVIVOR
@@ -440,15 +453,16 @@ def evaluate_sealed_survivor_transition(
         raise GraduationTransitionRefusedError(
             family_root_id, GRADUATION_STATE_SEALED_SURVIVOR,
             f"no sealed-shard evaluation recorded for dataset_id {dataset_id!r} -- refused: "
-            "record_sealed_evaluation must run first",
+            "micro_sealed_evaluation.evaluate_sealed_verdict must run first",
         )
     evaluation = evaluations[-1]
-    if not evaluation["passed"]:
+    if evaluation.get("verdict") != "pass":  # tri-state -- "fail" AND "insufficient" both refuse here
         raise GraduationTransitionRefusedError(
             family_root_id, GRADUATION_STATE_SEALED_SURVIVOR,
-            f"the recorded sealed-shard evaluation for dataset_id {dataset_id!r} is a permanent "
-            "FAILED verdict -- refused (spec section 7.4): a failed sealed verdict never advances "
-            "and is never re-evaluated",
+            f"the recorded sealed-shard evaluation for dataset_id {dataset_id!r} carries verdict "
+            f"{evaluation.get('verdict')!r}, not \"pass\" -- refused (spec section 7.4/8.1): a "
+            "non-passing sealed verdict is a permanent root-family fact and never advances, "
+            "never re-evaluated",
         )
 
     fields = {
@@ -466,29 +480,148 @@ def evaluate_sealed_survivor_transition(
 
 # === the export bundle (spec section 8 point 4, TC-3/TC-4/TC-6) =====================================
 
-
-def _latest_timestamp(values: list[str | None]) -> str | None:
-    present = [v for v in values if v]
-    return max(present) if present else None  # ISO-8601 Z-suffixed strings sort chronologically
+# === TR-24: the lineage-wide confirmation boundary (spec section 8.2, r6 owner ruling) ===============
+
+# The embargo-application rule's own disclosed name (persisted on every bundle, never silent) --
+# see ``_roll_forward_weekday_sessions``'s own docstring for why this simplification exists.
+_EMBARGO_RULE_ID = "weekday_roll_forward_v1"
+
+
+def _evidence_item_observed_through(kind: str, row: dict) -> str | None:
+    """Each evidence-item TYPE's own already-recorded timestamp field, standing in for spec section
+    8.2's ``observed_through`` -- no ledger row anywhere is named that (confirmed by direct source
+    read; ``runs/goal-session-rapid-microscope/state/assumptions.md``'s second iter-17 entry). Never
+    a new field, never a wall-clock read: ``scout_trial`` rows (survivors AND kills alike) carry
+    their own ``registered_at``; ``fold_result`` rows (of ANY verdict/class/process-label) carry
+    ``validation_revealed_at`` (Mode A's own LATER reveal instant, preferred when present -- TC-11's
+    own "moves to the later observed_through, never the earlier anchor_at") or ``registered_at``
+    (Mode B rows, which carry no separate reveal instant); ``sealed_evaluation`` rows (of ANY
+    verdict including FAIL/``insufficient``) carry their own ``evaluated_at``."""
+    if kind == "scout_trial":
+        return row.get("registered_at")
+    if kind == "fold_result":
+        return row.get("validation_revealed_at") or row.get("registered_at")
+    if kind == "sealed_evaluation":
+        return row.get("evaluated_at")
+    raise ValueError(f"_evidence_item_observed_through: unknown evidence kind {kind!r}")
+
+
+def _lineage_data_frontier(scout_trials: list[dict], fold_results: list[dict], sealed_evaluations: list[dict]) -> dict:
+    """spec section 8.2: ``lineage_data_frontier`` = ``max(observed_through)`` across EVERY evidence
+    item the ``family_root_id`` lineage ever touched -- survivors, killed/superseded Scout siblings
+    (TC-10), walk-forward folds of ANY verdict/class/process-label (not just eligible ones), sealed
+    evaluations of any verdict including FAIL/``insufficient`` (TR-24's own trap text). Returns the
+    frontier value PLUS which evidence item(s) achieved it (spec: "the bundle persists... the
+    evidence ids contributing to the max") -- an auditable "why here", never a bare timestamp."""
+    items: list[tuple[str, str | None, str | None]] = []  # (kind, evidence_id, observed_through)
+    for row in scout_trials:
+        evidence_id = row.get("candidate_id") or row.get("row_hash")
+        items.append(("scout_trial", evidence_id, _evidence_item_observed_through("scout_trial", row)))
+    for row in fold_results:
+        evidence_id = (
+            f"{row.get('sequence_id')}#{row.get('fold_index')}" if row.get("fold_index") is not None
+            else row.get("row_hash")
+        )
+        items.append(("fold_result", evidence_id, _evidence_item_observed_through("fold_result", row)))
+    for row in sealed_evaluations:
+        evidence_id = row.get("dataset_id") or row.get("row_hash")
+        items.append(("sealed_evaluation", evidence_id, _evidence_item_observed_through("sealed_evaluation", row)))
+
+    dated_items = [item for item in items if item[2] is not None]
+    if not dated_items:
+        return {"frontier": None, "contributing_evidence_ids": []}
+    frontier = max(item[2] for item in dated_items)
+    contributing = sorted({item[1] for item in dated_items if item[2] == frontier and item[1] is not None})
+    return {"frontier": frontier, "contributing_evidence_ids": contributing}
+
+
+def _embargo_for_lineage(wf_ledger: "wf.WalkForwardLedger", fold_results: list[dict]) -> dict:
+    """The applicable dependency embargo (spec section 6.3) for this lineage's OWN registered fold
+    geometry -- read from the LATEST fold spec of the fold results' own ``corpus_id`` (never a
+    second, independently-tuned embargo value; ``wl.latest_fold_spec`` is the SAME reader
+    ``walkforward.py``'s own machinery already uses). Honestly ``0``/no rule (spec section 6.3: "E=0
+    is a legitimate outcome") when no fold geometry is registered yet for this lineage -- a family
+    with only Scout trials and no walk-forward history has no identified cross-boundary dependency
+    to embargo against."""
+    corpus_id = fold_results[0].get("corpus_id") if fold_results else None
+    if corpus_id is None:
+        return {"embargo_sessions": 0, "embargo_rule_id": None}
+    spec = wl.latest_fold_spec(wf_ledger, corpus_id)
+    if spec is None:
+        return {"embargo_sessions": 0, "embargo_rule_id": None}
+    return {
+        "embargo_sessions": spec["geometry"].get("embargo_sessions", 0),
+        "embargo_rule_id": _EMBARGO_RULE_ID,
+    }
 
 
-def _proposed_confirmation_boundary(fold_results: list[dict], sealed_evaluations: list[dict]) -> str | None:
-    """A disclosed T-1 interpretation call: spec section 8 point 4 names "the proposed confirmation
-    boundary" as a required bundle field without a formula. Read here as the LATEST instant this
-    family's own ledgered evidence has already consumed -- the earliest a genuinely FRESH Referee
-    registration could legitimately start counting new sessions from, since evidence at or before
-    this instant has already been read by this candidate's own historical evaluation. Derived
-    entirely from timestamps already ON the ledgered rows (Mode A's ``validation_revealed_at``, both
-    modes' ``registered_at``, and every sealed evaluation's ``evaluated_at``) -- never a new,
-    independently-tunable rule; honestly ``None`` when no evidence exists yet, never a fabricated
-    date."""
-    candidates: list[str | None] = []
-    for fold in fold_results:
-        candidates.append(fold.get("validation_revealed_at"))
-        candidates.append(fold.get("registered_at"))
-    for evaluation in sealed_evaluations:
-        candidates.append(evaluation.get("evaluated_at"))
-    return _latest_timestamp(candidates)
+def _roll_forward_weekday_sessions(instant: str, n_sessions: int) -> str:
+    """Advances the CALENDAR DATE of an ISO instant forward by ``n_sessions`` weekday (Mon-Fri)
+    sessions, returning a date-only ``YYYY-MM-DD`` string -- a disclosed interpretation call (T-1).
+    No trading-SESSION calendar (holiday-aware) authority exists anywhere in this codebase (source
+    search confirms it) that could answer "the Nth session after an arbitrary FUTURE instant" --
+    every existing session-aware function this era ships only SLICES an already-known, already-
+    fetched ``session_dates`` list (``build_folds``), never projects one forward past the corpus it
+    was given; building a full holiday-aware trading calendar is real, unrequested scope this round
+    was never asked to carry. This weekday-only roll-forward is monotonic and order-preserving --
+    exactly what TR-24's own traps (TC-10..TC-14) assert -- and is DISCLOSED, never presented as
+    calendar-exact: a real market holiday inside the span is not skipped, so the boundary this
+    produces is honest but not guaranteed session-exact. Recorded as ``_EMBARGO_RULE_ID`` on every
+    bundle so the simplification is never silent. Since this bundle's ``proposed_confirmation_
+    boundary`` is explicitly advisory (spec section 8.2: the REAL gate is the untouched Referee's
+    own registration-time boundary, computed by a future named revision of ``referee_*.py``), a
+    slightly-conservative estimate carries no admission risk this era."""
+    day = date.fromisoformat(instant[:10])
+    remaining = n_sessions
+    while remaining > 0:
+        day += timedelta(days=1)
+        if day.weekday() < 5:  # Monday=0 .. Friday=4
+            remaining -= 1
+    return day.isoformat()
+
+
+def _next_eligible_session_on_or_after(instant: str) -> str:
+    """The first ELIGIBLE weekday session ON OR AFTER an instant's own calendar date -- the SAME
+    weekday-only interpretation call as ``_roll_forward_weekday_sessions`` (module docstring
+    there): Saturday/Sunday roll forward to the following Monday; a weekday date is already
+    eligible and returned unchanged."""
+    day = date.fromisoformat(instant[:10])
+    while day.weekday() >= 5:
+        day += timedelta(days=1)
+    return day.isoformat()
+
+
+def _evidence_safe_boundary(lineage_data_frontier: str | None, embargo_sessions: int) -> str | None:
+    """spec section 8.2: ``evidence_safe_boundary`` = ``lineage_data_frontier`` + the applicable
+    embargo, applied in session semantics (never an ad-hoc wall-clock delta). Honestly ``None`` when
+    the frontier itself is ``None`` (no lineage evidence exists yet)."""
+    if lineage_data_frontier is None:
+        return None
+    if embargo_sessions <= 0:
+        return _next_eligible_session_on_or_after(lineage_data_frontier)
+    return _roll_forward_weekday_sessions(lineage_data_frontier, embargo_sessions)
+
+
+def _proposed_confirmation_boundary(evidence_safe_boundary: str | None, handoff_created_at: str) -> str:
+    """spec section 8.2: the first eligible session boundary STRICTLY AFTER
+    ``max(evidence_safe_boundary, handoff_created_at)``. ``handoff_created_at`` always participates
+    (even when there is no lineage evidence at all yet) so a freshly-registered, evidence-free
+    family still gets an honest, non-``None`` proposed boundary anchored at "now", never a stale
... [diff_bound] apps/backend/app/research/micro_graduation.py: 119 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_micro_accessor.py b/apps/backend/tests/test_micro_accessor.py
index 4fd7f82..35cd344 100644
--- a/apps/backend/tests/test_micro_accessor.py
+++ b/apps/backend/tests/test_micro_accessor.py
@@ -350,6 +350,28 @@ def test_exposure_registry_chain_is_verified(tmp_path):
     assert registry.verify_chain()["ok"] is True
 
 
+# === GAP B3 (goal-rapid-microscope-iter-17, TC-16): an EXACTLY-simultaneous exposure logging does
+# NOT count as "before" -- locks down `is_exposed_before`'s strict `<` boundary the iteration-16
+# audit's own `<`->`<=` mutation could otherwise silently drift. ======================================
+
+
+def test_gap_b3_an_exactly_simultaneous_logging_does_not_count_as_before(tmp_path):
+    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
+    same_instant = "2026-06-09T05:00:00.000000Z"
+    registry.log_exposure(corpus_id="c", window="2026-06-08", surface="test", logged_at=same_instant)
+
+    # a validation window REGISTERED at the EXACT SAME instant the exposure was logged -- strict
+    # `<` semantics: an exactly-simultaneous logging does NOT count as "before".
+    assert registry.is_exposed_before(corpus_id="c", window="2026-06-08", instant=same_instant) is False
+
+    # one microsecond later genuinely counts as before -- proves the predicate is not simply
+    # always-False, only that equality specifically fails to qualify.
+    assert registry.is_exposed_before(corpus_id="c", window="2026-06-08", instant="2026-06-09T05:00:00.000001Z") is True
+
+    # one microsecond earlier is also honestly NOT before (the exposure had not happened yet).
+    assert registry.is_exposed_before(corpus_id="c", window="2026-06-08", instant="2026-06-09T04:59:59.999999Z") is False
+
+
 def test_tc14_r2_initialization_pre_marks_every_named_window_exposed_before_any_serving_act(tmp_path):
     """given a freshly initialized exposure registry, when any window of the (here, a small
     stand-in) corpus is queried for its exposure state, then it reads already-exposed from r2
@@ -410,3 +432,41 @@ def test_origin_fenced_mode_with_a_registry_logs_exactly_one_exposure_entry(rig,
     assert rows[0]["window"] == "2026-06-08"
     assert rows[0]["surface"] == "walkforward_test"
     assert rows[0]["logged_at"] == "2026-06-09T05:00:00.000000Z"
+
+
+# === TC-15 (this file's half, goal-rapid-microscope-iter-17): the corrected module docstring's
+# claim matches the actual production call sites exactly -- zero origin-fenced production callers.
+# =====================================================================================================
+
+
+def test_tc15_the_corrected_docstring_matches_every_production_construction_site():
+    """Direct grep of every ``MicroAccessor(`` construction site in ``app/`` (excluding this
+    module's own class definition and docstring prose): each one either omits ``origin=``
+    entirely or passes ``origin=None`` explicitly -- NO production call site constructs a FENCED
+    accessor. Proves the corrected docstring's claim ("NO current production caller constructs an
+    origin-fenced read") against the actual shipped code, not merely against prose."""
+    app_dir = _APP_DIR
+    call_sites: list[str] = []
+    for path in sorted(app_dir.rglob("*.py")):
+        if "__pycache__" in path.parts or path.name == "micro_accessor.py":
+            continue
+        text = path.read_text(encoding="utf-8")
+        tree = ast.parse(text, filename=str(path))
+        for node in ast.walk(tree):
+            if (
+                isinstance(node, ast.Call)
+                and isinstance(node.func, ast.Name)
+                and node.func.id == "MicroAccessor"
+            ):
+                for kw in node.keywords:
+                    if kw.arg == "origin":
+                        # a literal None is fine; anything else (a string, a variable) is a
+                        # FENCED construction site -- the exact claim the docstring makes.
+                        is_none_literal = isinstance(kw.value, ast.Constant) and kw.value.value is None
+                        if not is_none_literal:
+                            call_sites.append(f"{path.relative_to(app_dir)}: origin= is not a literal None")
+    assert call_sites == [], f"docstring claims zero origin-fenced production callers, found: {call_sites}"
+    # the docstring itself makes this claim in plain language -- not merely proven by this grep.
+    docstring = " ".join((ma.__doc__ or "").split())  # normalize whitespace/line-wraps
+    assert "NO current production caller constructs an origin-fenced read" in docstring
+    assert "walkforward.py`` itself never constructs a ``MicroAccessor`` at all" in docstring
diff --git a/apps/backend/tests/test_micro_graduation.py b/apps/backend/tests/test_micro_graduation.py
index e82e849..07c5b6e 100644
--- a/apps/backend/tests/test_micro_graduation.py
+++ b/apps/backend/tests/test_micro_graduation.py
@@ -1,12 +1,22 @@
 """``micro_graduation.py`` (Era "The Rapid Microscope" J-07) -- test-first contract: TC-1 through
-TC-9, per ``docs/phases/goal-rapid-microscope-iter-10.md``. Fixture-only throughout (no real
-sealed shard exists this era; J-06 step 4 is human-blocked) -- every scenario builds its OWN
-ledgered evidence directly through the sibling modules' existing public functions
-(``walkforward_ledger.append_fold_result``, ``vault.seal_shard``/``assign_shard``/``expose_shard``,
-``scout_ledger.ScoutLedger.append_row``) and then exercises ``micro_graduation.py``'s own
-evaluation functions against it -- mirroring ``test_walkforward.py``'s own "hand-built,
-ledgered-but-not-re-deriving-the-producer's-own-machinery" style for testing a CONSUMER's logic in
-isolation."""
+TC-9 (iteration 10) plus TC-10 through TC-15 (iteration 17, TR-24, ``docs/phases/goal-rapid-
+microscope-iter-17.md``). Fixture-only throughout (no real sealed shard exists this era; J-06 step
+4 is human-blocked) -- every scenario builds its OWN ledgered evidence directly through the
+sibling modules' existing public functions (``walkforward_ledger.append_fold_result``,
+``vault.seal_shard``/``assign_shard``/``expose_shard``, ``scout_ledger.ScoutLedger.append_row``)
+and then exercises ``micro_graduation.py``'s own evaluation functions against it -- mirroring
+``test_walkforward.py``'s own "hand-built, ledgered-but-not-re-deriving-the-producer's-own-
+machinery" style for testing a CONSUMER's logic in isolation.
+
+**Iteration 17 (r6 owner ruling, spec section 8.1): the sealed-evaluation verdict is no longer
+caller-supplied.** ``record_sealed_evaluation`` now takes a whole, already-computed ``artifact``
+dict (produced, in production, exclusively by ``micro_sealed_evaluation.evaluate_sealed_verdict``
+-- tested end-to-end, including its own mutation-proof and fixture-discrimination requirements, in
+``test_micro_sealed_evaluation.py``). This file's own TC-2/TC-3/TC-4/TC-6-labeled tests below
+(iteration 10's original numbering) build a hand-crafted artifact via the new ``_sealed_artifact``
+helper, exercising ``micro_graduation.py``'s OWN persistence/transition/bundle logic in isolation --
+never re-deriving the scientific computation, exactly this file's own established convention for
+every OTHER sibling ledger."""
 
 from __future__ import annotations
 
@@ -95,6 +105,28 @@ def _scout_row(*, family_root_id: str, family_id: str, candidate_id: str, decisi
     }
 
 
+def _sealed_artifact(*, passed: bool, spec_hash: str = "spec-fixture-hash-1", **extra) -> dict:
+    """A hand-built sealed-evaluation ARTIFACT (iteration 17: ``micro_graduation.record_sealed_
+    evaluation`` no longer accepts a caller-supplied ``passed: bool`` -- ``micro_sealed_evaluation.
+    py`` is the sole scientific owner of the verdict now, tested in its own
+    ``test_micro_sealed_evaluation.py``). This file tests ``micro_graduation.py``'s OWN persistence/
+    transition logic in isolation -- the ``test_walkforward.py`` "hand-built, ledgered-but-not-
+    re-deriving-the-producer's-own-machinery" style, applied here to the sealed-evaluation artifact
+    shape exactly as it already is to fold rows."""
+    fields = {
+        "spec_hash": spec_hash,
+        "verdict": "pass" if passed else "fail",
+        "failure_reason": None if passed else "below_economic_floor",
+        "effect": 10.0 if passed else 1.0, "sign": "positive", "n": 40, "n_sessions": 10, "n_symbols": 3,
+        "missing": {}, "econ_floor": _ECON_FLOOR, "registered_direction": "long",
+        "evidence_class": wf.EVIDENCE_CLASS_HISTORICAL_OOS, "process_label": wf.PROCESS_LABEL_RULE,
+        "rule_id": "SEALED_PASS_RULE_V1", "rule_version": 1, "rule_hash": "fixture-rule-hash",
+        "observed_through": "2026-06-09T13:01:00.000000Z", "evaluated_at": "2026-06-10T00:00:00.000000Z",
+    }
+    fields.update(extra)
+    return fields
+
+
 # === TC-1: exploratory -> walkforward_survivor =======================================================
 
 
@@ -194,11 +226,11 @@ def test_tc2_a_passing_sealed_evaluation_advances_to_sealed_survivor(tmp_path):
 
     shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id, dataset_id="dataset-pass")
     eval_result = g.record_sealed_evaluation(
-        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-pass",
-        spec_hash="spec-fixture-hash-1", passed=True,
+        grad_ledger, family_root_id=family_root_id, dataset_id="dataset-pass",
+        artifact=_sealed_artifact(passed=True),
     )
     assert eval_result["transition"] == g.TRANSITION_APPENDED
-    assert eval_result["row"]["passed"] is True
+    assert eval_result["row"]["verdict"] == "pass"
 
     result = g.evaluate_sealed_survivor_transition(grad_ledger, family_root_id=family_root_id, dataset_id="dataset-pass")
     assert result["transition"] == g.TRANSITION_APPENDED
@@ -206,35 +238,19 @@ def test_tc2_a_passing_sealed_evaluation_advances_to_sealed_survivor(tmp_path):
     assert g.current_graduation_state(grad_ledger, family_root_id) == g.GRADUATION_STATE_SEALED_SURVIVOR
 
 
-def test_sealed_evaluation_is_refused_against_a_shard_never_exposed_to_this_family(tmp_path):
-    family_root_id = scout_ledger.compute_family_root_id("a", "b", "c")
-    other_family_root_id = scout_ledger.compute_family_root_id("x", "y", "z")
-    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
-    # the shard is exposed, but to a DIFFERENT family entirely.
-    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=other_family_root_id)
-
-    with pytest.raises(g.GraduationTransitionRefusedError, match="not an EXPOSED vault shard"):
-        g.record_sealed_evaluation(
-            grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
-            spec_hash="spec-x", passed=True,
-        )
-    assert g.sealed_evaluations_for_family(grad_ledger, family_root_id) == []
-
-
 def test_a_second_identical_sealed_evaluation_call_is_replayed_a_second_different_one_is_refused(tmp_path):
     family_root_id = scout_ledger.compute_family_root_id("microprice_drift", "band_wall_touch", "trades_20")
     grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
-    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id)
 
     first = g.record_sealed_evaluation(
-        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
-        spec_hash="spec-x", passed=True,
+        grad_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
+        artifact=_sealed_artifact(passed=True),
     )
     assert first["transition"] == g.TRANSITION_APPENDED
 
     replay = g.record_sealed_evaluation(
-        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
-        spec_hash="spec-x", passed=True,
+        grad_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
+        artifact=_sealed_artifact(passed=True),
     )
     assert replay["transition"] == g.TRANSITION_REPLAYED
     assert replay["row"] == first["row"]
@@ -242,8 +258,8 @@ def test_a_second_identical_sealed_evaluation_call_is_replayed_a_second_differen
 
     with pytest.raises(g.GraduationTransitionRefusedError, match="never a second draw"):
         g.record_sealed_evaluation(
-            grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
-            spec_hash="spec-x", passed=False,  # a genuinely DIFFERENT verdict for the same pair
+            grad_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
+            artifact=_sealed_artifact(passed=False),  # a genuinely DIFFERENT verdict for the same pair
         )
     assert len(g.sealed_evaluations_for_family(grad_ledger, family_root_id)) == 1  # still never a duplicate
 
@@ -254,10 +270,9 @@ def test_sealed_survivor_transition_is_refused_before_walkforward_survivor_is_re
     evaluation on record."""
     family_root_id = scout_ledger.compute_family_root_id("spread_change", "band_wall_touch", "trades_20")
     grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
-    shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id)
     g.record_sealed_evaluation(
-        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
-        spec_hash="spec-x", passed=True,
+        grad_ledger, family_root_id=family_root_id, dataset_id="dataset-1",
+        artifact=_sealed_artifact(passed=True),
     )
     with pytest.raises(g.GraduationTransitionRefusedError, match="strictly ordered"):
         g.evaluate_sealed_survivor_transition(grad_ledger, family_root_id=family_root_id, dataset_id="dataset-1")
@@ -277,10 +292,10 @@ def test_tc6_a_failed_sealed_evaluation_never_advances_and_is_carried_into_the_b
 
     shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id, dataset_id="dataset-fail")
     eval_result = g.record_sealed_evaluation(
-        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-fail",
-        spec_hash="spec-fixture-hash-1", passed=False, detail={"reason": "fixture: sealed effect below floor"},
+        grad_ledger, family_root_id=family_root_id, dataset_id="dataset-fail",
+        artifact=_sealed_artifact(passed=False),
     )
-    assert eval_result["row"]["passed"] is False
+    assert eval_result["row"]["verdict"] == "fail"
 
     with pytest.raises(g.GraduationTransitionRefusedError, match="permanent"):
         g.evaluate_sealed_survivor_transition(grad_ledger, family_root_id=family_root_id, dataset_id="dataset-fail")
@@ -290,10 +305,10 @@ def test_tc6_a_failed_sealed_evaluation_never_advances_and_is_carried_into_the_b
     scout = ScoutLedger(str(tmp_path / "scout"))
     bundle = g.build_export_bundle(
         grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
-        family_root_id=family_root_id, sequence_id=sequence_id,
+        family_root_id=family_root_id, sequence_id=sequence_id, handoff_created_at="2026-06-15T00:00:00.000000Z",
     )
     assert bundle["state"] == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR
-    failed_verdicts = [e for e in bundle["sealed_evaluations"] if e["passed"] is False]
+    failed_verdicts = [e for e in bundle["sealed_evaluations"] if e["verdict"] == "fail"]
     assert len(failed_verdicts) == 1
     assert failed_verdicts[0]["dataset_id"] == "dataset-fail"
     assert bundle["family_multiplicity"]["prior_sealed_verdicts"] == bundle["sealed_evaluations"]
@@ -314,8 +329,8 @@ def test_tc3_and_tc4_the_full_pipeline_produces_a_validating_bundle_and_referee_
 
     shard_ledger, universe_ledger = _exposed_shard(tmp_path, family_root_id=family_root_id, dataset_id="dataset-e2e")
     g.record_sealed_evaluation(
-        grad_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id, dataset_id="dataset-e2e",
-        spec_hash="spec-fixture-hash-1", passed=True,
+        grad_ledger, family_root_id=family_root_id, dataset_id="dataset-e2e",
+        artifact=_sealed_artifact(passed=True),
     )
     g.evaluate_sealed_survivor_transition(grad_ledger, family_root_id=family_root_id, dataset_id="dataset-e2e")
 
@@ -397,13 +412,26 @@ def test_bundle_is_buildable_and_honestly_partial_for_a_family_with_no_evidence_
     shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
     universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
 
-    bundle = g.build_export_bundle(grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id)
+    bundle = g.build_export_bundle(
+        grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger, family_root_id=family_root_id,
+        handoff_created_at="2026-06-01T00:00:00.000000Z",
+    )
     assert bundle["state"] == g.GRADUATION_STATE_EXPLORATORY
     assert bundle["scout_trials"] == []
     assert bundle["fold_results"] == []
     assert bundle["shards_touched"] == []
     assert bundle["sealed_evaluations"] == []
-    assert bundle["proposed_confirmation_boundary"] is None
+    # TR-24 (iteration 17): with NO lineage evidence at all, the frontier/embargo/evidence_safe_
+    # boundary are all honestly None/zero -- but proposed_confirmation_boundary is NEVER None, it is
+    # anchored at handoff_created_at (the bundle's own "now") so a freshly-registered, evidence-free
+    # family still gets an honest, non-stale advisory boundary.
+    assert bundle["lineage_data_frontier"] is None
+    assert bundle["lineage_frontier_evidence_ids"] == []
+    assert bundle["evidence_safe_boundary"] is None
+    assert bundle["embargo_sessions"] == 0
+    assert bundle["embargo_rule_id"] is None
+    assert bundle["handoff_created_at"] == "2026-06-01T00:00:00.000000Z"
+    assert bundle["proposed_confirmation_boundary"] == "2026-06-02"  # the first weekday strictly after
     assert g.bundle_validates(bundle)  # honestly EMPTY fields still validate -- nothing is MISSING
 
 
@@ -554,3 +582,206 @@ def test_graduation_served_copy_clears_the_copy_discipline_lexicon():
     disclaimer -- carry no imperative/predictive/certainty-claim language."""
     assert find_violations(g.EMPTY_LEDGER_MESSAGE) == []
     assert find_violations(g.REFEREE_FUTURE_REVISION_SENTENCE) == []
+
+
+# ============================================================================================
+# TR-24 (iteration 17, r6 owner ruling, spec section 8.2): the lineage-wide confirmation
+# boundary. "Survivor rows are NOT the basis; the LINEAGE is" -- a killed Scout sibling's own
+# LATER evidence must push the boundary past it, proving lineage knowledge cannot be laundered
+# through candidate selection (register three siblings, keep only the one whose own evidence
+# looks conveniently old).
+# ============================================================================================
+
+
+def _append_fold_with_reveal(
+    wf_ledger: wl.WalkForwardLedger, *, fold_index: int, sequence_id: str, corpus_id: str,
+    registered_at: str, validation_revealed_at: str, **overrides,
+) -> dict:
+    """A Mode-A-shaped fold row carrying BOTH ``registered_at`` (the fold spec's own freeze
+    instant -- TC-11's "anchor_at" stand-in) AND ``validation_revealed_at`` (the LATER test-window
+    reveal instant -- TC-11's "observed_through" stand-in), so a single fixture can prove the
+    lineage frontier picks the LATER field, never the earlier one."""
+    fields = {
+        "sequence_id": sequence_id, "corpus_id": corpus_id, "mode": "A", "fitting_rule": "training_quantile(0.90)",
+        "realized_fitted_value": 1.0, "spec_hash": "spec-fixture-hash-1", "fold_index": fold_index,
+        "sidedness": "long", "econ_floor": _ECON_FLOOR, "evidence_class": wf.EVIDENCE_CLASS_HISTORICAL_OOS,
+        "process_label": wf.PROCESS_LABEL_RULE, "registered_at": registered_at,
+        "spec_hash_recorded_at": registered_at, "validation_revealed_at": validation_revealed_at,
+        "status": wf.FOLD_STATUS_SUFFICIENT, "n": 40, "n_sessions": 10, "n_symbols": 3,
+        "effect": 10.0, "sign": "positive", "missing": {},
+    }
+    fields.update(overrides)
+    return wl.append_fold_result(wf_ledger, fields)
+
+
+# === TC-10 + TC-14 (mutually reinforcing): a KILLED sibling's later observed_through pushes the
+# boundary past it -- built on deliberately DIFFERENT calendar instants (never coincidentally
+# equal), so this is simultaneously TC-10's own scenario and TC-14's discrimination proof. ========
+
+
+def test_tc10_and_tc14_a_killed_siblings_later_evidence_pushes_the_boundary_past_it(tmp_path):
+    family_root_id = scout_ledger.compute_family_root_id("tc10_tc14_feature", "band_wall_touch", "trades_20")
+    corpus_id = "graduation-fixture-corpus-tc10"
+    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
+    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    # the SURVIVOR's own fold evidence -- deliberately EARLY (2026-02-10).
+    _append_fold_with_reveal(
+        wf_ledger, fold_index=0, sequence_id=sequence_id, corpus_id=corpus_id,
+        registered_at="2026-02-01T00:00:00.000000Z", validation_revealed_at="2026-02-10T00:00:00.000000Z",
+    )
+
+    scout = ScoutLedger(str(tmp_path / "scout"))
+    # the survivor candidate's own registration -- also early.
+    scout.append_row({
+        "family_id": "fam-survivor", "family_root_id": family_root_id, "candidate_id": "cand-survivor",
+        "decision": "survive", "reason": None, "notes": "", "registered_at": "2026-02-05T00:00:00.000000Z",
+    })
+    # the KILLED SIBLING -- same family_root_id, a DIFFERENT variant, registered MONTHS later
+    # (2026-05-01) -- a deliberately DIFFERENT calendar instant from every survivor-side timestamp
+    # above (TC-14: never coincidentally equal).
+    scout.append_row({
+        "family_id": "fam-killed-sibling", "family_root_id": family_root_id, "candidate_id": "cand-killed",
+        "decision": "killed_null", "reason": None, "notes": "", "registered_at": "2026-05-01T00:00:00.000000Z",
+    })
+
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
+    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    bundle = g.build_export_bundle(
+        grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
+        family_root_id=family_root_id, sequence_id=sequence_id, handoff_created_at="2026-01-01T00:00:00.000000Z",
+    )
+
+    # the frontier is the KILLED SIBLING's own later timestamp -- NOT the survivor's own (earlier)
+    # evidence alone.
+    assert bundle["lineage_data_frontier"] == "2026-05-01T00:00:00.000000Z"
+    assert bundle["lineage_data_frontier"] != "2026-02-10T00:00:00.000000Z"  # the survivor-only (wrong) answer
+    assert "cand-killed" in bundle["lineage_frontier_evidence_ids"]
+    assert bundle["frontier_observed_through"] == bundle["lineage_data_frontier"]
+    # the proposed boundary is therefore pushed to strictly after the killed sibling's own instant.
+    assert bundle["proposed_confirmation_boundary"] > "2026-05-01"
+    assert bundle["evidence_safe_boundary"] >= "2026-05-01"
+
+
+# === TC-11: a deferred feature's LATER observed_through moves the frontier, never its earlier
+# anchor_at. =========================================================================================
+
+
+def test_tc11_a_deferred_folds_later_observed_through_moves_the_frontier_not_its_earlier_anchor(tmp_path):
+    family_root_id = scout_ledger.compute_family_root_id("tc11_feature", "band_wall_touch", "trades_20")
+    corpus_id = "graduation-fixture-corpus-tc11"
+    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
+    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    _append_fold_with_reveal(
+        wf_ledger, fold_index=0, sequence_id=sequence_id, corpus_id=corpus_id,
+        registered_at="2026-02-01T00:00:00.000000Z",  # the "anchor_at" stand-in -- EARLIER
+        validation_revealed_at="2026-03-01T00:00:00.000000Z",  # the "observed_through" stand-in -- LATER
+    )
+    scout = ScoutLedger(str(tmp_path / "scout"))
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
+    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+
+    bundle = g.build_export_bundle(
+        grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
+        family_root_id=family_root_id, sequence_id=sequence_id, handoff_created_at="2026-01-01T00:00:00.000000Z",
+    )
+    assert bundle["lineage_data_frontier"] == "2026-03-01T00:00:00.000000Z"  # the LATER reveal instant
+    assert bundle["lineage_data_frontier"] != "2026-02-01T00:00:00.000000Z"  # never the earlier registration
+
+
+# === TC-12: the final Referee-registration boundary is never earlier than either input =================
+
+
+def test_tc12_final_confirmation_boundary_is_never_earlier_than_either_input():
+    # proposed EARLIER than registration -- both already weekdays.
+    final = g.final_confirmation_boundary("2026-06-02", "2026-06-10")
+    assert final == "2026-06-10"
+    assert final >= "2026-06-02" and final >= "2026-06-10"
+
+    # proposed LATER than registration, and its OWN date (2026-06-20) is a Saturday -- rolls
+    # forward to the next eligible weekday (Monday 2026-06-22).
+    final2 = g.final_confirmation_boundary("2026-06-20", "2026-06-05")
+    assert final2 == "2026-06-22"
+    assert final2 >= "2026-06-20" and final2 >= "2026-06-05"
+
+    # a weekend max (Saturday 2026-06-06) rolls forward to the following Monday.
+    final3 = g.final_confirmation_boundary("2026-06-01", "2026-06-06")
+    assert final3 == "2026-06-08"
+    assert final3 >= "2026-06-01" and final3 >= "2026-06-06"
+
+
+# === TC-13 (mutation evidence): narrowing the lineage scan back to "only the survivor's own
+# sequence" (the r6-REJECTED naive form) makes the killed-sibling assertion fail, naming the too-
+# early boundary it produces; restoring the lineage-wide scan makes it pass again. ==================
+
+
+def test_tc13_narrowing_the_lineage_scan_to_survivor_only_makes_the_killed_sibling_case_fail(monkeypatch, tmp_path):
+    """The established, already-praised mutation-proof pattern
+    (``test_micro_observer.py``'s ``test_tc12_tr26_reverting_the_fix_makes_the_corrected_
+    assertion_fail_restoring_it_passes``), mirrored exactly for TR-24: ``monkeypatch.setattr``
+    installs the REJECTED naive formula (the owner ruling's own words: "the dev's 'latest
+    timestamp on surviving evidence rows' is REJECTED") -- ``fold_results`` only, ignoring
+    ``scout_trials`` (so a killed sibling's later evidence is invisible) and ``sealed_
+    evaluations`` entirely -- reproduces the exact too-early wrong value the naive formula would
+    have produced, then restores and shows the correct, later value returns."""
+    family_root_id = scout_ledger.compute_family_root_id("tc13_feature", "band_wall_touch", "trades_20")
+    corpus_id = "graduation-fixture-corpus-tc13"
+    sequence_id = wf.sequence_id_for(corpus_id, "fixture-rule")
+    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    _append_fold_with_reveal(
+        wf_ledger, fold_index=0, sequence_id=sequence_id, corpus_id=corpus_id,
+        registered_at="2026-02-01T00:00:00.000000Z", validation_revealed_at="2026-02-10T00:00:00.000000Z",
+    )
+    scout = ScoutLedger(str(tmp_path / "scout"))
+    scout.append_row({
+        "family_id": "fam-survivor", "family_root_id": family_root_id, "candidate_id": "cand-survivor",
+        "decision": "survive", "reason": None, "notes": "", "registered_at": "2026-02-05T00:00:00.000000Z",
+    })
+    scout.append_row({
+        "family_id": "fam-killed-sibling", "family_root_id": family_root_id, "candidate_id": "cand-killed",
+        "decision": "killed_null", "reason": None, "notes": "", "registered_at": "2026-05-01T00:00:00.000000Z",
+    })
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
+    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+
+    def _naive_survivor_only_frontier(scout_trials, fold_results, sealed_evaluations):
+        # BUG (the r6-REJECTED naive form): only fold_results -- ignores scout_trials (so a
+        # killed sibling's later evidence is invisible) and sealed_evaluations entirely.
+        candidates = [row.get("validation_revealed_at") or row.get("registered_at") for row in fold_results]
+        candidates = [c for c in candidates if c is not None]
+        if not candidates:
+            return {"frontier": None, "contributing_evidence_ids": []}
+        return {"frontier": max(candidates), "contributing_evidence_ids": []}
+
+    monkeypatch.setattr(g, "_lineage_data_frontier", _naive_survivor_only_frontier)
+    corrupted_bundle = g.build_export_bundle(
+        grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
+        family_root_id=family_root_id, sequence_id=sequence_id, handoff_created_at="2026-01-01T00:00:00.000000Z",
+    )
+    # the exact TOO-EARLY wrong value the naive code produces -- proves the corrected assertion
+    # (frontier == "2026-05-01...", the killed sibling's own instant) WOULD fail against it.
+    assert corrupted_bundle["lineage_data_frontier"] == "2026-02-10T00:00:00.000000Z"
+    assert corrupted_bundle["lineage_data_frontier"] != "2026-05-01T00:00:00.000000Z"
+
+    monkeypatch.undo()
+    restored_bundle = g.build_export_bundle(
+        grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
... [diff_bound] apps/backend/tests/test_micro_graduation.py: 17 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_micro_observer.py b/apps/backend/tests/test_micro_observer.py
index 3d7ba6f..7a391a1 100644
--- a/apps/backend/tests/test_micro_observer.py
+++ b/apps/backend/tests/test_micro_observer.py
@@ -252,6 +252,57 @@ def test_tc9_response_asymmetry_is_unavailable_when_the_session_ends_first():
     assert all(d["unavailable"] is True and d["value"] is None for d in response_completions)
 
 
+# === GAP B4 (goal-rapid-microscope-iter-17, TC-17): a session whose LAST event is a TRADE, not a
+# quote -- finalize()'s session-end stamp equals the TRADE's own timestamp, numerically DIFFERENT
+# from what it would be had the session ended on a quote instead (`self._last_event_ts` is set
+# unconditionally in `_consume` for EVERY event type, before the trade/quote branch -- this test
+# proves that behavior directly, on the close-out row itself, with a discriminating twin). ==========
+
+
+def _events_ending_on_a_trade() -> list:
+    """5 buy-aggressive trades (far short of RESPONSE_K_TRADES=20, so response_asymmetry stays
+    pending into finalize()) -- the stream's OWN LAST event is the 5th TRADE, at ts=5.0."""
+    events: list = [QuoteEvent(TICKER, 0.0, 100.00, 100.02, 500, 500)]
+    ts = 1.0
+    for _i in range(5):
+        events.append(TradeEvent(TICKER, ts, 100.02, 10, Side.UNKNOWN))
+        ts += 1.0
+    return events  # last event: TradeEvent at ts=5.0
+
+
+def test_gap_b4_a_trade_terminated_session_stamps_finalize_at_the_trades_own_timestamp():
+    rows = _run(_events_ending_on_a_trade())
+    close_out_rows = [r for r in rows if r.get("close_out")]
+    assert len(close_out_rows) == 1
+    close_out = close_out_rows[0]
+    # the session's LAST event was the 5th trade, at ts=5.0 -- finalize()'s own stamp equals it.
+    assert close_out["anchor_at"] == close_out["observed_through"] == close_out["available_at"] == 5.0
+    pending = [d for d in close_out["deferred"] if d["kind"] == "response_asymmetry"]
+    assert len(pending) == 5
+    assert all(d["observed_through"] == d["available_at"] == 5.0 for d in pending)
+
+
+def test_gap_b4_discriminating_twin_a_trailing_quote_moves_the_same_stamp_to_a_different_instant():
+    """The discriminating twin (TC-17's own requirement: correct and corrupted-basis values must
+    be numerically DIFFERENT, never coincidentally equal): the IDENTICAL 5-trade stream, PLUS one
+    trailing QuoteEvent at ts=9.0 -- now the session ends on a QUOTE instead. finalize()'s own
+    stamp moves to 9.0 -- proving the trade-terminated case's 5.0 is genuinely the trade's OWN
+    timestamp, not some incidental default that would show up regardless of what the last event
+    was."""
+    events = _events_ending_on_a_trade() + [QuoteEvent(TICKER, 9.0, 100.00, 100.02, 500, 500)]
+    rows = _run(events)
+    close_out_rows = [r for r in rows if r.get("close_out")]
+    assert len(close_out_rows) == 1
+    close_out = close_out_rows[0]
+    assert close_out["anchor_at"] == close_out["observed_through"] == close_out["available_at"] == 9.0
+    # numerically DIFFERENT from the trade-terminated case's own 5.0 -- never coincidentally equal.
+    assert close_out["observed_through"] != 5.0
+    pending = [d for d in close_out["deferred"] if d["kind"] == "response_asymmetry"]
+    assert len(pending) == 5
+    assert all(d["observed_through"] == d["available_at"] == 9.0 for d in pending)
+    assert all(d["observed_through"] != 5.0 for d in pending)
+
+
 # --- F-LIQUIDITY: quote_imbalance, microprice, quote_depletion, refill_consistent (TC-10) ----------
 
 
diff --git a/docs/goal.md b/docs/goal.md
index 1ac3843..52c3536 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -154,7 +154,7 @@ items, in that order.**
    `08e471b10130e1e2` every iteration; every `referee_*` module byte-identical to `main` at
    era open (SHA-256 listing recorded at iteration 0 and re-checked); every kept `/`,
    `/structure`, `/desk` behavior browser-verified as shipped.
-2. **No leakage trap fails, ever.** The TR-1…TR-29 suite of
+2. **No leakage trap fails, ever.** The TR-1…TR-30 suite of
    [`docs/rapid-validation-spec.md`](rapid-validation-spec.md) §9 is implemented and green:
    prefix discipline, origin fencing, sealed-shard sweeps, cherry-pick refusal, class-mixing
    refusal, purge exactness, screening calibration, pool invariance, ledger chain integrity,
@@ -165,7 +165,7 @@ items, in that order.**
    the r6 traps: TR-23 sealed-verdict ownership, TR-24 lineage confirmation boundary,
    TR-25 vault-ledger integrity, TR-26 depletion revealing-quote availability — and the r7
    traps: TR-27 nonced rule commitment, TR-28 coarse pre-release volumes, and the r8
-   trap TR-29 halt-only vault recovery.
+   trap TR-29 halt-only vault recovery, and the r9 trap TR-30 evaluator-owned sealed sufficiency.
 3. **Every trial is on the record.** The scout ledger is hash-chained append-only; every
    evaluated variant — every kill, with its closed-vocabulary reason — is a permanent row; the
    union-N denominator is served beside every family; "statistically above null" and
@@ -662,13 +662,13 @@ operator-attended act inside the era.
 
 - **J-10: The kept product stands — traps armed, sentinel green**
   - Steps:
-    1. Land the full TR-1…TR-29 suite (whichever traps did not ship inside J-02…J-07 land
+    1. Land the full TR-1…TR-30 suite (whichever traps did not ship inside J-02…J-07 land
        here — the r2 traps TR-17 availability, TR-18 units, TR-19 preservation, TR-20 root
        lineage, TR-21 process labels, TR-22 exposure registry, and the r6 traps TR-23
        sealed-verdict ownership, TR-24 lineage boundary, TR-25 vault-ledger integrity,
        TR-26 depletion revealing quote, and the r7 traps TR-27 nonced rule commitment,
        TR-28 coarse pre-release volumes, and the r8 trap TR-29 halt-only vault
-       recovery, included) plus the extended
+       recovery, and the r9 trap TR-30 evaluator-owned sealed sufficiency, included) plus the extended
        guard tests (accessor import-ban, micro threshold-sweep ban, copy discipline for micro
        copy, `_PRICE_ARITHMETIC_FIELDS` additions).
     2. Run the deterministic-rerun check (byte-identical snapshot/screen/fold outputs on a
diff --git a/docs/rapid-validation-spec.md b/docs/rapid-validation-spec.md
index 6d427aa..3be9979 100644
--- a/docs/rapid-validation-spec.md
+++ b/docs/rapid-validation-spec.md
@@ -125,6 +125,26 @@
 > be designed ad hoc inside this fix. Owner's governing sentence: **for this era, safety wins over
 > degraded availability — unknown or unprovable exposure history means the vault is unavailable,
 > never "fresh".** Traps → TR-29.
+>
+> **Revision r9 (2026-08-20, owner ruling — sealed sufficiency is shard-scoped and pinned).** The
+> iteration-17 audit PROVED by execution that `SEALED_PASS_RULE_V1` condition 1 read its
+> sufficiency floors from the CALLER's spec: a spec carrying `floors={1,1,1}` and a single
+> observation produced a permanent `verdict: "pass"` whose `rule_hash` certified floors of 30/8/2
+> that the run never applied — precisely the defect §8.1 exists to prevent. But mechanically
+> pinning §1's walk-forward floors was ALSO wrong: §7.3 seals a shard per `symbol:date`, so one
+> shard is one symbol-day and `WF_FOLD_MIN_SIGNAL_SESSIONS`/`WF_FOLD_MIN_SYMBOLS` are
+> unsatisfiable, making PASS permanently unreachable. §8.1 and §7.3 genuinely contradicted each
+> other. **The owner resolved it by separating the two stages scientifically rather than by
+> changing the sealing unit: the walk-forward stage owns BREADTH; the sealed stage owns UNTOUCHED
+> REPLICATION on one hidden symbol-day.** r9 adds the sealed-specific pinned constant
+> `SEALED_MIN_OBSERVATIONS` (§1), declares session and symbol breadth `not_applicable_single_shard`
+> at shard scope (never silently 1), and REFUSES any caller-supplied floor or threshold override —
+> the evaluator owns the rule. The rule hash is computed from the sealed rule actually executed.
+> Single-shot semantics are preserved and reinforced: **`insufficient` still consumes that family's
+> sealed evaluation on the assigned shard** — a family does NOT get a fresh shard merely because the
+> first lacked observations, which would be repeated holdout sampling. **The sealing unit is
+> UNCHANGED.** The auditor's honesty-only artifact-field fix is necessary but insufficient; the
+> evaluator's authority must be fixed before any sealed graduation is allowed. Traps → TR-30.
 
 ---
 
@@ -184,6 +204,7 @@
 | `WF_FOLD_MIN_SIGNAL_SESSIONS` | `8` | Per-fold floor: validation sessions carrying ≥1 observation |
 | `WF_FOLD_MIN_OBSERVATIONS` | `30` | Per-fold floor |
 | `WF_FOLD_MIN_SYMBOLS` | `2` | Per-fold floor whenever symbol breadth is claimed |
+| `SEALED_MIN_OBSERVATIONS` | `30` | **(r9)** The ONLY sufficiency floor at sealed-shard scope (§8.1). A shard is one symbol × one session-date (§7.3), so session and symbol breadth are `not_applicable_single_shard` there — never silently 1. Never sourced from a candidate or caller spec |
 | `DIAGNOSTIC_GEOMETRY` | `train=40, embargo=5, test=20, step=20` | Pinned geometry of the ONE playbook-corpus diagnostic acceptance run (§6.6). The `embargo=5` here is that run's predeclared choice, not a universal law — see §6.3 |
 | `VAULT_SEAL_HEX_BELOW` | `4` | Seal iff the last hex digit of the §7.3 HMAC < 4 (≈25% of a universe) |
 | `TRANCHE_MINIMUMS` | §7.6 table | The starter-tranche diversity floors |
@@ -811,18 +832,30 @@ persistence and transition machinery and neither accepts nor invents the scienti
 6. persist an immutable **evaluation artifact** (below);
 7. pass ONLY that artifact's id + hash to the graduation transition.
 
-**`SEALED_PASS_RULE_V1` (frozen; introduces no new constant).** A (root family, shard) evaluation
+**`SEALED_PASS_RULE_V1` (frozen; r9 replaces condition 1).** A (root family, shard) evaluation
 `passes` iff ALL of:
-1. the shard's recomputed observations meet the per-fold sufficiency floors already pinned in §1 —
-   `WF_FOLD_MIN_OBSERVATIONS` observations, `WF_FOLD_MIN_SIGNAL_SESSIONS` signal-bearing sessions,
-   and `WF_FOLD_MIN_SYMBOLS` symbols whenever the family claims breadth; below any floor the
-   verdict is `insufficient`, which is neither a pass nor a fail and consumes the single shot
-   ONLY if the shard was exposed (an exposure is irreversible either way);
+1. **(r9) the shard's recomputed observations meet the SEALED-SPECIFIC pinned floor**
+   `SEALED_MIN_OBSERVATIONS` (§1). The walk-forward per-fold breadth floors are **NOT** reused
+   here: a sealed shard is ONE symbol × ONE session-date (§7.3), so session and symbol breadth are
+   inapplicable at shard scope and MUST be recorded explicitly as
+   `min_signal_sessions: not_applicable_single_shard` and
+   `min_symbols: not_applicable_single_shard` — **never silently set to 1**. Below the observation
+   floor the verdict is `insufficient`, which is neither a pass nor a fail and consumes the single
+   shot ONLY if the shard was exposed (an exposure is irreversible either way).
+   **No sufficiency value may be sourced from the candidate or caller spec.** A caller supplying
+   floors, altered thresholds, or any equivalent override is REFUSED — the evaluator owns the rule.
+   *Scientific rationale (record it wherever the rule is served): the walk-forward stage owns
+   BREADTH — `WF_SURVIVOR_RULE_V1` establishes temporal, session and symbol breadth before a
+   candidate may reach the sealed stage at all. The sealed stage owns UNTOUCHED REPLICATION on one
+   hidden symbol-day. Mechanically reusing breadth floors at shard scope conflates the two.*
 2. the session-clustered effect lies in the family's REGISTERED direction (§5.1 sidedness);
 3. its magnitude ≥ the family's own pre-registered economic floor (§5.5) — the same floor the
    walk-forward applied, not a new one;
 4. the evaluation rule id/version/hash recorded at assignment is byte-identical to the one applied
-   (a rule changed after assignment fails CLOSED);
+   (a rule changed after assignment fails CLOSED). **(r9) The rule hash is computed from the
+   SEALED-SPECIFIC rule actually executed; it must never certify one set of floors while execution
+   applied another** — the artifact records the rule definition/hash AND the actual applied values,
+   and the two must agree byte-for-byte with runtime behaviour;
 5. the shard's evidence class is `historical_oos` and its process label `rule_process` (§6.7/§6.8).
 Anything less is a FAIL, and a fail is permanent for the root family (§7.4). There is no
 discretionary override and no partial credit.
@@ -899,6 +932,7 @@ boundary by its `observed_through`.
 | TR-23 sealed-verdict ownership (r6 §8.1) | A caller-asserted `passed` boolean is impossible/refused · mutating any evaluation input changes the artifact hash and invalidates the transition · a rule unregistered, or changed after assignment, fails closed · re-running the evaluator on identical inputs yields a byte-identical artifact and verdict · a second sealed evaluation for the same (`family_root_id`, shard) is refused · a failed verdict travels in every later export bundle |
 | TR-24 lineage boundary (r6 §8.2) | A KILLED sibling of the same `family_root_id` with a later `observed_through` than the survivor pushes `proposed_confirmation_boundary` past it (lineage knowledge cannot be laundered through candidate selection) · a deferred feature with `anchor_at < observed_through` moves the boundary by its `observed_through` · the final Referee boundary is never earlier than either the proposed or the registration boundary |
 | TR-25 vault-ledger integrity (r6 §7.8) | Tail truncation ⇒ every exposure predicate fails closed · interior-row mutation ⇒ fails closed · a last-known-good prefix still fails closed when a committed checkpoint proves later history existed · a hash-pinned reconstruction restores the exact prior exposure state · an unverifiable recovery never makes an affected shard fresh again — **under r8 that means the recovery is REFUSED and the tranche stays blocked** (the `exposure_unknown` state this row originally named was deleted with r8's graded-resume branch; see TR-29) |
+| TR-30 sealed sufficiency is evaluator-owned (r9 §8.1) | A spec carrying `floors={1,1,1}` is REFUSED and can never make one observation pass · 29 sealed observations ⇒ `insufficient` · 30 otherwise-valid observations ⇒ sufficiency can clear · session and symbol breadth are recorded `not_applicable_single_shard`, never silently 1 · changing ANY caller floor field cannot change the verdict · the artifact's `rule_hash`, its applied-floor values, and runtime behaviour agree byte-for-byte · an `insufficient` verdict still CONSUMES that family's single sealed shot on the assigned shard (no fresh shard on thin data — that would be repeated holdout sampling) |
 | TR-29 recovery is halt-only (r8 §7.8) | The demonstrated attack: seal `d-1`/`d-2`/`d-3`, destroy the row containing `d-3`, present a SAME-LENGTH reconstructed suffix containing an unrelated `d-fake` ⇒ recovery REFUSES, and `d-3` never becomes sealable again under another universe · same row count with REORDERED identities ⇒ refuse · same row count with a SUBSTITUTED identity ⇒ refuse · same final-row count but a missing earlier exposure ⇒ refuse · a cleanly internally re-chained forged suffix is NOT proof of historical completeness · operator attestation never substitutes for missing identity evidence |
 | TR-27 nonced rule commitment (r7 §7.2) | One ledger-tracked shard exposed while untracked pool members remain withheld ⇒ rule contents hidden · ALL tracked shards exposed but one untracked ORIGINAL-pool member still withheld ⇒ still hidden · after the final pool member is released ⇒ `symbol_rule` + `date_rule` + nonce reveal and recompute EXACTLY to the registered `rule_commitment` · a plausible-rule dictionary attack against the served commitment cannot verify guesses without the nonce · no other API/UI/MCP surface serves the symbol or date axes pre-release |
 | TR-28 coarse pre-release volumes (r7 §7.1) | A one-symbol-day run while withheld ⇒ no exact trade/quote/byte count appears on ANY surface · a multi-shard pool ⇒ coarse bucket labels only, never rounded numbers · expose one shard and re-query ⇒ the remaining withheld counts cannot be solved exactly from the before/after response pair (differencing resistance) · buckets never narrow as the pool shrinks · the final ORIGINAL-pool member released ⇒ exact totals may be served |
diff --git a/apps/backend/app/research/micro_sealed_evaluation.py b/apps/backend/app/research/micro_sealed_evaluation.py
new file mode 100644
index 0000000..825eb86
--- /dev/null
+++ b/apps/backend/app/research/micro_sealed_evaluation.py
@@ -0,0 +1,418 @@
+"""``micro_sealed_evaluation.py`` -- Era "The Rapid Microscope" J-07/TR-23 (r6 owner ruling,
+
+``docs/rapid-validation-spec.md`` section 8.1, ``runs/goal-session-rapid-microscope/state/
+assumptions.md`` 2026-08-18 "OWNER RULINGS (4)"): the SOLE scientific owner of the sealed-shard
+evaluation verdict. Before this module existed, ``micro_graduation.record_sealed_evaluation`` took
+an already-computed ``passed: bool`` straight from its caller -- a disclosed T-1 interpretation
+call its own module docstring named as a placeholder, because "the statistical MACHINERY... does
+not exist anywhere in this codebase yet". This module IS that machinery.
+
+**The ledger owns history; the evaluator owns the answer (spec section 8.1's own opening line).**
+``micro_graduation.py`` and ``vault.py`` remain persistence and transition machinery -- neither
+accepts nor invents the scientific answer. This module never writes to a ledger file directly and
+never hand-rolls a second hash chain: it computes an artifact, then calls THROUGH to
+``micro_graduation.record_sealed_evaluation`` (the ALREADY-EXISTING ``GraduationLedger``/
+``ROW_KIND_SEALED_EVALUATION`` machinery, reused verbatim) for the actual write.
+
+**The seven-step mandatory sequence (spec section 8.1, any step failing => typed refusal, never a
+verdict):**
+
+1. require an ASSIGNED-then-``exposed`` shard (``vault.build_vault_state``, read-only, unmodified)
+   bound to this EXACT ``family_root_id``, and a candidate spec whose own ``registered_at`` is
+   STRICTLY BEFORE the shard's own ``assigned_at`` (spec: "frozen BEFORE that assignment").
+2. verify the candidate spec's own ``spec_hash``/``family_root_id``/sidedness/``econ_floor`` are
+   present, and that its recorded ``sealed_pass_rule_hash`` is byte-identical to the CURRENT
+   ``sealed_pass_rule_hash()`` -- a mismatch (the rule changed, or was never registered) fails
+   CLOSED with a typed refusal, never a computed verdict (TC-3).
+3. obtain the shard ONLY through ``micro_accessor.MicroAccessor`` (an UNFENCED, ``origin=None``
+   accessor the CALLER constructs -- the module docstring's own "two callers, two disciplines"
+   precedent: this is a third such caller, a post-exposure whole-shard read, never a rolling-origin
+   walk-forward fold, so wiring a live fence here would be the unrequested behavior change that
+   module's own docstring warns against) plus ``vault.build_vault_state`` to confirm genuine
+   ``exposed`` binding.
+4. RECOMPUTE the outcome from canonical, already-consulted machinery --
+   ``walkforward.summarize_fold_observations`` (never a second, independently-valued
+   implementation) over a caller-supplied ``observations: list[dict]`` (the era's own "observations
+   are the engine's one abstract input" convention, ``walkforward.py``'s module docstring, mirrored
+   here exactly as ``evaluate_mode_b_fold`` already does it) -- never trusting a caller-computed
+   effect number directly.
+5. derive the verdict deterministically from ``SEALED_PASS_RULE_V1``'s five conditions.
+6. persist an immutable evaluation artifact through ``micro_graduation.record_sealed_evaluation``.
+7. return only that artifact's id (``dataset_id``/``family_root_id``) + hash (``row_hash``) --
+   callers that want the full artifact read it back via ``micro_graduation.
+   sealed_evaluations_for_family`` (single source of truth: the persisted row, never a second
+   in-memory copy this function hands back as if it were authoritative).
+
+**``SEALED_PASS_RULE_V1`` introduces NO new numeric constant** (spec section 8.1, r6 owner ruling
+point 1): it reuses ``walkforward.WF_FOLD_MIN_OBSERVATIONS``/``_SIGNAL_SESSIONS``/``_SYMBOLS``
+(the SAME per-fold sufficiency floors a walk-forward fold already enforces, via the SAME
+``summarize_fold_observations`` function) and the family's OWN pre-registered spec section 5.5
+economic floor (``candidate_spec["econ_floor"]`` -- never a second, independently-tuned floor).
+``rule_id``/``rule_version`` are IDENTITY metadata (mirroring ``walkforward.WF_SURVIVOR_RULE_V1``'s
+own "the rule's own name IS its identity" convention), not tunable thresholds.
+
+**Condition 1's floors are the section-1 defaults, but a candidate spec MAY NARROW them --
+disclosed, unresolved, OWNER-OWED (rule T-1; iteration-17 audit finding B1).**
+``summarize_fold_observations`` honours a per-spec ``floors`` override key-by-key (the
+``evaluate_mode_b_fold(floors=...)`` precedent this module reuses verbatim), so a candidate spec
+carrying its own ``floors`` -- not the section-1 constants ``sealed_pass_rule_hash()`` embeds --
+decides condition 1. This module does NOT silently pin the override away, because pinning it makes
+a PASS verdict structurally UNREACHABLE: a vault shard is ONE symbol-day (spec section 7.3's own
+``f"{symbol}:{YYYY-MM-DD}"`` seal key), so a single shard can never carry
+``WF_FOLD_MIN_SIGNAL_SESSIONS`` = 8 signal-bearing SESSIONS or ``WF_FOLD_MIN_SYMBOLS`` = 2 SYMBOLS,
+and every evaluation would return ``insufficient`` forever (verified: pinning the floors turns all
+four of this module's own PASS/FAIL fixtures into ``insufficient``). Spec section 8.1 condition 1
+and section 7.3/7.4 are therefore in genuine tension over what "the shard's recomputed
+observations" spans -- ONE shard, or the family's whole exposed tranche -- and under rule T-1 that
+is an OWNER RULING, never a dev or auditor invention. Until it is ruled, the floors ACTUALLY
+applied are recorded verbatim on every persisted artifact as ``floors_applied``: spec section 8.1
+requires the artifact to be "sufficient to reproduce the verdict", and condition 1 is NOT
+reproducible from ``n``/``n_sessions``/``n_symbols`` alone -- so a narrowed floor can never be
+silent in a permanent verdict or in any later export bundle.
+
+**The rule-identity-at-assignment interpretation call (T-1, disclosed).** Spec condition 4 needs
+"the evaluation rule id/version/hash recorded AT ASSIGNMENT" to compare against "the one applied" --
+but ``vault.assign_shard`` (frozen this era, OUT OF SCOPE to touch) carries no rule-identity field
+at all. Since assignment binds ONE candidate family LINE to a shard, and a candidate spec must
+already exist and be frozen before its shard is ever assigned (step 1 above), THIS module reads
+"the rule recorded at assignment" as a field on the CANDIDATE SPEC ITSELF --
+``candidate_spec["sealed_pass_rule_hash"]``, which a real caller would stamp with THIS module's own
+``sealed_pass_rule_hash()`` at spec-registration time (before assignment, by construction of the
+one-way vault lifecycle). A fixture proving "the rule changed after assignment" therefore supplies
+a candidate spec whose OWN recorded hash no longer matches the CURRENT constant.
+
+**Tri-state verdict (spec section 8.1 point 1): PASS / FAIL / ``insufficient`` -- never coerced to a
+boolean.** ``insufficient`` fires when the recomputed observations miss ANY per-fold floor; it
+consumes the single evaluation shot (the shard was genuinely exposed) but is neither a pass nor a
+fail, and stays distinguishable from FAIL in the persisted artifact and every later export bundle
+(``micro_graduation.build_export_bundle`` carries the artifact verbatim, never filtering or
+collapsing it)."""
+
+from __future__ import annotations
+
+import hashlib
+import json
+from datetime import datetime, timezone
+
+from . import vault
+from . import walkforward as wf
+from .micro_accessor import MicroAccessor
+from .micro_graduation import (
+    GraduationLedger,
+    GraduationTransitionRefusedError,
+    record_sealed_evaluation,
+)
+
+__all__ = [
+    "SEALED_PASS_RULE_V1",
+    "SEALED_PASS_RULE_VERSION",
+    "SEALED_VERDICT_PASS",
+    "SEALED_VERDICT_FAIL",
+    "SEALED_VERDICT_INSUFFICIENT",
+    "SEALED_VERDICTS",
+    "SEALED_FAIL_REASONS",
+    "SealedEvaluationRefusedError",
+    "sealed_pass_parameters",
+    "sealed_pass_rule_hash",
+    "evaluate_sealed_verdict",
+]
+
+# === spec section 8.1's rule identity -- a NAME/VERSION, never a tunable numeric (module docstring) ==
+
+SEALED_PASS_RULE_V1 = "SEALED_PASS_RULE_V1"
+SEALED_PASS_RULE_VERSION = 1
+
+# The tri-state verdict vocabulary (spec section 8.1 point 1) -- OWNED here (the scientific answer's
+# own module), never redefined a second time elsewhere. ``micro_graduation.py`` compares against the
+# literal string "pass" directly (a disclosed, one-way-dependency interpretation call logged on
+# ``evaluate_sealed_survivor_transition``'s own docstring) rather than importing this name, so that
+# module -- which this module already imports FROM -- never has to import back, avoiding a cycle.
+SEALED_VERDICT_PASS = "pass"
+SEALED_VERDICT_FAIL = "fail"
+SEALED_VERDICT_INSUFFICIENT = "insufficient"
+SEALED_VERDICTS = (SEALED_VERDICT_PASS, SEALED_VERDICT_FAIL, SEALED_VERDICT_INSUFFICIENT)
+
+# The closed-vocabulary FAIL reasons (the ``scout.KILL_REASONS`` convention, mirrored per the phase
+# spec's own suggestion) -- one per non-floor SEALED_PASS_RULE_V1 condition. The floor condition's
+# own failure reason is ``insufficient`` itself (a distinct verdict, not a FAIL reason) plus the
+# ``summarize_fold_observations`` ``missing`` arithmetic, carried on the artifact separately.
+SEALED_FAIL_REASONS: tuple[str, ...] = (
+    "wrong_direction",
+    "below_economic_floor",
+    "evidence_class_or_process_label_ineligible",
+)
+
+REQUIRED_EVIDENCE_CLASS = wf.EVIDENCE_CLASS_HISTORICAL_OOS
+REQUIRED_PROCESS_LABEL = wf.PROCESS_LABEL_RULE
+
+
+def _canonical(obj: object) -> bytes:
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def _iso_utc_now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
+
+
+def sealed_pass_parameters() -> dict:
+    """Every constant ``SEALED_PASS_RULE_V1`` depends on, embedded verbatim (the
+    ``walkforward.walkforward_parameters``/``scout.scout_parameters`` pattern) -- introduces NO new
+    numeric value (module docstring): the three floors are IMPORTED from ``walkforward.py``, never
+    re-declared. Hashed into ``sealed_pass_rule_hash()``, which a candidate spec must carry
+    (recorded before assignment) for condition 4's rule-identity check."""
+    return {
+        "sealed_pass_rule_id": SEALED_PASS_RULE_V1,
+        "sealed_pass_rule_version": SEALED_PASS_RULE_VERSION,
+        "wf_fold_min_observations": wf.WF_FOLD_MIN_OBSERVATIONS,
+        "wf_fold_min_signal_sessions": wf.WF_FOLD_MIN_SIGNAL_SESSIONS,
+        "wf_fold_min_symbols": wf.WF_FOLD_MIN_SYMBOLS,
+        "required_evidence_class": REQUIRED_EVIDENCE_CLASS,
+        "required_process_label": REQUIRED_PROCESS_LABEL,
+    }
+
+
+def sealed_pass_rule_hash() -> str:
+    return _sha256(_canonical(sealed_pass_parameters()))
+
+
+class SealedEvaluationRefusedError(Exception):
+    """A step of the mandatory sequence (spec section 8.1) failed BEFORE any verdict was derived --
+    never a fabricated result, never a silent skip. Distinct from a recorded ``FAIL`` verdict: this
+    exception means no evaluation artifact was computed or persisted at all (the single evaluation
+    shot is NOT consumed), whereas a recorded ``FAIL``/``insufficient`` verdict IS a permanent,
+    persisted outcome that DOES consume the shot when the shard was genuinely exposed."""
+
+    def __init__(self, family_root_id: str, dataset_id: str, reason: str) -> None:
+        self.family_root_id = family_root_id
+        self.dataset_id = dataset_id
+        self.reason = reason
+        super().__init__(
+            f"sealed evaluation refused for family_root_id {family_root_id!r}, dataset_id "
+            f"{dataset_id!r}: {reason}"
+        )
+
+
+def _expected_sign(sidedness: str) -> str:
+    return "positive" if sidedness == "long" else "negative"
+
+
+def _resolved_floors(candidate_spec: dict) -> dict:
+    """The three per-fold sufficiency floors condition 1 ACTUALLY applies -- the section-1 pinned
+    constants, EXCEPT wherever the candidate's own registered spec carries a ``floors`` override
+    (which ``walkforward.summarize_fold_observations`` honours key-by-key; see the module
+    docstring's own T-1 disclosure for why this module surfaces that rather than pinning it away).
+    Returned fully RESOLVED, never the caller's partial dict, so the ``floors_applied`` field on
+    the persisted artifact is self-contained."""
+    override = candidate_spec.get("floors") or {}
+    return {
+        "wf_fold_min_observations": override.get("wf_fold_min_observations", wf.WF_FOLD_MIN_OBSERVATIONS),
+        "wf_fold_min_signal_sessions": override.get("wf_fold_min_signal_sessions", wf.WF_FOLD_MIN_SIGNAL_SESSIONS),
+        "wf_fold_min_symbols": override.get("wf_fold_min_symbols", wf.WF_FOLD_MIN_SYMBOLS),
+    }
+
+
+def _derive_verdict(
+    summary: dict, *, sidedness: str, econ_floor: dict | None, evidence_class: str | None, process_label: str | None,
+) -> tuple[str, str | None, dict]:
+    """``SEALED_PASS_RULE_V1``'s five conditions (spec section 8.1), evaluated against an ALREADY-
+    RECOMPUTED ``summarize_fold_observations`` summary -- extracted into its own, standalone,
+    monkeypatchable function (the ``walkforward.evaluate_survivor_rule``/``sequence_verdict``
+    precedent: the discretion-free predicate lives in ONE named place a test can mutate directly,
+    mirroring the established mutation-proof shape rather than a big inline block a test could only
+    exercise indirectly). Returns ``(verdict, failure_reason, conditions)`` -- ``failure_reason`` is
+    ``None`` for both ``pass`` and ``insufficient`` (the latter's own arithmetic lives in the
+    caller's ``summary["missing"]``, never duplicated here as a second reason string)."""
+    condition_1_floors = summary["status"] == wf.FOLD_STATUS_SUFFICIENT
+    if not condition_1_floors:
+        return SEALED_VERDICT_INSUFFICIENT, None, {"sufficient_observations": False}
+
+    expected_sign = _expected_sign(sidedness)
+    condition_2_direction = summary["sign"] == expected_sign
+    condition_3_magnitude = (
+        econ_floor is not None
+        and econ_floor.get("floor_bps") is not None
+        and abs(summary["effect"]) >= econ_floor["floor_bps"]
+    )
+    condition_5_class_process = (
+        evidence_class == REQUIRED_EVIDENCE_CLASS and process_label == REQUIRED_PROCESS_LABEL
+    )
+    conditions = {
+        "sufficient_observations": True,
+        "registered_direction": condition_2_direction,
+        "clears_economic_floor": condition_3_magnitude,
+        "historical_oos_rule_process": condition_5_class_process,
+    }
+    if condition_2_direction and condition_3_magnitude and condition_5_class_process:
+        return SEALED_VERDICT_PASS, None, conditions
+    if not condition_2_direction:
+        failure_reason = "wrong_direction"
+    elif not condition_3_magnitude:
+        failure_reason = "below_economic_floor"
+    else:
+        failure_reason = "evidence_class_or_process_label_ineligible"
+    return SEALED_VERDICT_FAIL, failure_reason, conditions
+
+
+def evaluate_sealed_verdict(
+    graduation_ledger: GraduationLedger,
+    shard_ledger: "vault.VaultShardLedger",
+    universe_ledger: "vault.VaultUniverseLedger",
+    accessor: MicroAccessor,
+    *,
+    candidate_spec: dict,
+    dataset_id: str,
+    observations: list[dict],
+    evaluated_at: str | None = None,
+) -> dict:
+    """The whole seven-step mandatory sequence (module docstring), steps 1-5 computed HERE, step 6
+    delegated to ``micro_graduation.record_sealed_evaluation`` (the ledger's own single-shot
+    dedup/idempotent-replay discipline, TR-12, applies unchanged), step 7 satisfied by this
+    function's own return value (``result["row"]`` carries ``dataset_id``+``row_hash`` -- the ONLY
+    fields a transition needs to consume, per ``evaluate_sealed_survivor_transition``'s existing,
+    unchanged read of ``row_hash``).
+
+    ``observations`` is caller-supplied (the "one abstract input" convention, module docstring) --
+    a future J-08/J-09 route/CLI reduces the shard's raw snapshot rows to
+    ``{session_date, symbol, value}`` triples for THIS candidate's own feature/structure_context/
+    outcome definition (Scout's own job, ``scout.extract_anchors``'s territory -- not reinvented
+    here, matching ``micro_graduation.py``'s own established "a real future join... is a natural
+    J-08/J-09 wiring concern, not invented here" precedent). This function's OWN accessor read
+    (below) is independent of ``observations`` -- it exists to satisfy step 3 for real (the shard
+    must be genuinely obtainable through the sanctioned door) and to stamp the artifact's own
+    ``observed_through`` from the shard's actual recorded data timeline, never from ``observations``
+    or a caller-supplied value."""
+    family_root_id = candidate_spec.get("family_root_id")
+    if not family_root_id:
+        raise SealedEvaluationRefusedError(
+            str(family_root_id), dataset_id,
+            "candidate_spec carries no family_root_id -- refused (step 2): a spec identity is "
+            "mandatory before any shard read",
+        )
+    spec_hash = candidate_spec.get("spec_hash")
+    sidedness = candidate_spec.get("sidedness")
+    econ_floor = candidate_spec.get("econ_floor")
+    recorded_rule_hash = candidate_spec.get("sealed_pass_rule_hash")
+    spec_registered_at = candidate_spec.get("registered_at")
+    if not (spec_hash and sidedness and spec_registered_at):
+        raise SealedEvaluationRefusedError(
+            family_root_id, dataset_id,
+            "candidate_spec is missing one of spec_hash/sidedness/registered_at -- refused "
+            "(step 2): the candidate's canonical registered spec must be complete before a sealed "
+            "evaluation is attempted",
+        )
+
+    # --- step 2 (rule identity half): the rule recorded on the spec BEFORE assignment must be
+    # byte-identical to the one this evaluator is ABOUT to apply -- a mismatch fails CLOSED, never
+    # a computed verdict (TC-3). Checked BEFORE any shard read, so a rule change is caught even if
+    # the shard read would otherwise succeed. ------------------------------------------------------
+    current_rule_hash = sealed_pass_rule_hash()
+    if recorded_rule_hash != current_rule_hash:
+        raise SealedEvaluationRefusedError(
+            family_root_id, dataset_id,
+            f"the candidate spec's recorded sealed_pass_rule_hash {recorded_rule_hash!r} does not "
+            f"match the currently-applied {SEALED_PASS_RULE_V1!r} hash {current_rule_hash!r} -- "
+            "refused (spec section 8.1 condition 4): a rule changed (or never registered) after "
+            "assignment fails closed, never a pass",
+        )
+
+    # --- step 1 + step 3 (vault half): the shard must be genuinely EXPOSED and bound to this EXACT
+    # family_root_id (never trust a caller's say-so -- the same confirmation the retired
+    # record_sealed_evaluation used to perform, reused verbatim via the SAME build_vault_state call,
+    # never a second implementation of vault semantics). ---------------------------------------------
+    vault_state = vault.build_vault_state(shard_ledger, universe_ledger)
+    shard_entry = next((s for s in vault_state["shards"] if s.get("dataset_id") == dataset_id), None)
+    if (
+        shard_entry is None
+        or shard_entry.get("exposure_state") != vault.STATE_EXPOSED
+        or shard_entry.get("family_root_id") != family_root_id
+    ):
+        raise SealedEvaluationRefusedError(
+            family_root_id, dataset_id,
+            f"dataset_id {dataset_id!r} is not an EXPOSED vault shard bound to this exact "
+            "family_root_id -- refused (spec section 7.4/8.1 step 1): a sealed-shard evaluation "
+            "can only run against a shard genuinely exposed to this family",
+        )
+    assigned_at = shard_entry.get("assigned_at")
+    if not assigned_at or not (spec_registered_at < assigned_at):
+        raise SealedEvaluationRefusedError(
+            family_root_id, dataset_id,
+            f"candidate spec registered_at {spec_registered_at!r} is not STRICTLY BEFORE the "
+            f"shard's own assigned_at {assigned_at!r} -- refused (spec section 8.1 step 1): the "
+            "candidate spec must be frozen before assignment, never after",
+        )
+
+    # --- step 3 (accessor half): obtain the shard ONLY through the sanctioned accessor -- an
+    # UNFENCED (origin=None) accessor, exactly like micro_join.py/scout.py's own re-pointed reads
+    # (module docstring). A fenced accessor here would be a silent, unrequested behavior change. ----
+    if accessor.origin is not None:
+        raise SealedEvaluationRefusedError(
+            family_root_id, dataset_id,
+            f"the sealed evaluator requires an UNFENCED accessor (origin=None); this accessor's "
+            f"origin is {accessor.origin!r} -- refused",
+        )
+    raw_rows = accessor.read_snapshot_rows(dataset_id)
+    observed_through_values = [row["observed_through"] for row in raw_rows if row.get("observed_through") is not None]
+    observed_through = max(observed_through_values) if observed_through_values else None
+
+    # --- step 4: RECOMPUTE via the canonical statistical core, never trust a caller-computed
+    # effect -- summarize_fold_observations is the SAME function walk-forward folds themselves
+    # consult (never reimplemented; the per-fold sufficiency floors ARE SEALED_PASS_RULE_V1
+    # condition 1, reused verbatim, no new constant). ------------------------------------------------
+    floors = _resolved_floors(candidate_spec)
+    summary = wf.summarize_fold_observations(observations, floors)
+
+    evaluated_at_value = evaluated_at if evaluated_at is not None else _iso_utc_now()
+
+    # --- step 5: derive the tri-state verdict from SEALED_PASS_RULE_V1's five conditions ----------
+    verdict, failure_reason, conditions = _derive_verdict(
+        summary,
+        sidedness=sidedness,
+        econ_floor=econ_floor,
+        evidence_class=candidate_spec.get("evidence_class"),
+        process_label=candidate_spec.get("process_label"),
+    )
+
+    # --- step 6: persist the immutable artifact through the ALREADY-EXISTING ledger machinery
+    # (micro_graduation.py's own "persistence stays there" contract, module docstring). -------------
+    artifact = {
+        "candidate_id": candidate_spec.get("candidate_id"),
+        "family_id": candidate_spec.get("family_id"),
+        "spec_hash": spec_hash,
+        "shard_checksum": shard_entry.get("content_checksum"),
+        "shard_symbol": shard_entry.get("symbol"),
+        "shard_session_date": shard_entry.get("session_date"),
+        "evidence_class": candidate_spec.get("evidence_class"),
+        "process_label": candidate_spec.get("process_label"),
+        "outcome_basis": candidate_spec.get("outcome_basis", "mid"),
+        "n": summary["n"],
+        "n_sessions": summary["n_sessions"],
+        "n_symbols": summary["n_symbols"],
+        # spec section 8.1: the artifact must be "sufficient to reproduce the verdict" -- condition 1
... [diff_bound] apps/backend/app/research/micro_sealed_evaluation.py: 24 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_micro_sealed_evaluation.py b/apps/backend/tests/test_micro_sealed_evaluation.py
new file mode 100644
index 0000000..69f94cc
--- /dev/null
+++ b/apps/backend/tests/test_micro_sealed_evaluation.py
@@ -0,0 +1,623 @@
+"""``micro_sealed_evaluation.py`` (Era "The Rapid Microscope" J-07/TR-23, r6 owner ruling,
+``docs/rapid-validation-spec.md`` section 8.1) -- test-first contract: TC-1 through TC-9, per
+``docs/phases/goal-rapid-microscope-iter-17.md``.
+
+Fixture-only throughout (goal.md's own "do not seed/mutate/expose real Vault data" instruction;
+zero real sealed shards exist this era) -- every scenario plants a REAL dataset + snapshot on disk
+(the ``test_micro_accessor.py`` ``_plant_dataset_and_snapshot`` precedent, so the evaluator's own
+accessor read is genuine, never mocked), a real seal->assign->expose vault shard sequence (the
+``test_micro_graduation.py`` ``_exposed_shard`` precedent), and a hand-built ``observations`` list
+(the ``test_walkforward.py`` ``_observation``/small-floors-override precedent) -- mirroring, never
+re-deriving, this codebase's own established fixture conventions.
+
+**The governing acceptance rule for this trap (iteration-17 phase spec, "the round's central
+risk").** Two consecutive prior rounds shipped a brand-new trap that was structurally unable to
+fail. TC-8 below is the mutation-proof (a deliberately weakened ``_derive_verdict`` makes the
+corrected assertion fail, naming the specific wrong verdict; restoring makes it pass again). TC-9
+is the fixture-discrimination proof (the correct and corrupted recomputed effects are DIFFERENT
+numeric values -- 10.0 vs 1.0 -- never coincidentally equal), run independently of the mutation
+test so the fixture's own soundness does not rely on the mutation succeeding."""
+
+from __future__ import annotations
+
+import re
+
+import pytest
+
+from app.config import CONFIG
+from app.research import micro_graduation as g
+from app.research import micro_sealed_evaluation as sealed_eval
+from app.research import scout_ledger
+from app.research import vault
+from app.research import walkforward as wf
+from app.research.datasets import DatasetStore
+from app.research.micro_accessor import MicroAccessor, MicroAccessorOriginFenceError
+from app.research.micro_snapshots import resolve_micro_snapshots_dir
+from tests.test_micro_accessor import _plant_dataset_and_snapshot
+
+# === helpers ==========================================================================================
+
+_FIXTURE_VAULT_SECRET = b"a-sealed-evaluation-fixture-vault-secret"
+_SEALED_AT = "2026-01-01T00:00:00.000000Z"
+_SPEC_REGISTERED_AT = "2026-01-02T00:00:00.000000Z"  # strictly before assigned_at, below
+_ASSIGNED_AT = "2026-01-05T00:00:00.000000Z"
+_EXPOSED_AT = "2026-01-06T00:00:00.000000Z"
+_EVALUATED_AT = "2026-06-10T00:00:00.000000Z"
+
+# Tiny floors so a 3-observation hand-built fixture clears the "sufficient" status without needing
+# 30 real observations -- the test_walkforward.py `floors={"wf_fold_min_observations": 1, ...}`
+# precedent, mirrored exactly.
+_TINY_FLOORS = {"wf_fold_min_observations": 3, "wf_fold_min_signal_sessions": 1, "wf_fold_min_symbols": 1}
+_ECON_FLOOR = {"floor_bps": 5.0}
+
+
+def _observation(session_date: str, symbol: str, value: float) -> dict:
+    return {"session_date": session_date, "symbol": symbol, "value": value}
+
+
+def _passing_observations() -> list[dict]:
+    """Mean effect = 10.0 -- clears ``_ECON_FLOOR``'s 5.0 bps floor in the "long"/positive
+    direction. THE "correct" fixture TC-9 discriminates against."""
+    return [
+        _observation("2026-06-08", "PG", 10.0),
+        _observation("2026-06-08", "PG", 12.0),
+        _observation("2026-06-08", "PG", 8.0),
+    ]
+
+
+def _below_floor_observations() -> list[dict]:
+    """Mean effect = 1.0 -- POSITIVE (correct direction) but strictly below the 5.0 bps econ floor,
+    so it FAILS on magnitude alone, never on direction. Deliberately a DIFFERENT numeric value from
+    ``_passing_observations``'s own 10.0 (TC-9: never coincidentally equal)."""
+    return [
+        _observation("2026-06-08", "PG", 1.0),
+        _observation("2026-06-08", "PG", 1.2),
+        _observation("2026-06-08", "PG", 0.8),
+    ]
+
+
+def _insufficient_observations() -> list[dict]:
+    """Only 2 observations -- below ``_TINY_FLOORS``'s own ``wf_fold_min_observations: 3`` floor."""
+    return [_observation("2026-06-08", "PG", 10.0), _observation("2026-06-08", "PG", 12.0)]
+
+
+def _rig(tmp_path):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    snapshots_dir = resolve_micro_snapshots_dir(str(tmp_path / "datasets"))
+    dataset_meta = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="PG",
+        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
+    )
+    return dataset_store, snapshots_dir, dataset_meta
+
+
+def _exposed_shard_for(
+    tmp_path, *, family_root_id: str, dataset_id: str,
+    assigned_at: str = _ASSIGNED_AT, exposed_at: str = _EXPOSED_AT,
+) -> tuple["vault.VaultShardLedger", "vault.VaultUniverseLedger"]:
+    """seal -> assign -> expose ONE fixture shard, with EXPLICIT, controllable
+    ``assigned_at``/``exposed_at`` timestamps (the ``test_micro_graduation.py`` ``_exposed_shard``
+    precedent, extended: step 1 of the mandatory sequence needs a spec ``registered_at`` strictly
+    BEFORE the shard's own ``assigned_at``, so the fixture must be able to pin that instant)."""
+    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
+    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    vault.seal_shard(
+        shard_ledger, dataset_id=dataset_id, universe_id="u1", content_checksum="c" * 64,
+        event_count=500, vault_secret=_FIXTURE_VAULT_SECRET, sealed_at=_SEALED_AT,
+    )
+    vault.assign_shard(
+        shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id, symbol="PG",
+        session_date="2026-06-09", assigned_at=assigned_at,
+    )
+    vault.expose_shard(shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id, exposed_at=exposed_at)
+    return shard_ledger, universe_ledger
+
+
+def _candidate_spec(
+    *, family_root_id: str, candidate_id: str = "cand-1", family_id: str = "fam-a",
+    spec_hash: str = "spec-hash-1", sidedness: str = "long", econ_floor: dict | None = _ECON_FLOOR,
+    evidence_class: str = wf.EVIDENCE_CLASS_HISTORICAL_OOS, process_label: str = wf.PROCESS_LABEL_RULE,
+    registered_at: str = _SPEC_REGISTERED_AT, rule_hash: str | None = None, floors: dict | None = _TINY_FLOORS,
+) -> dict:
+    return {
+        "family_root_id": family_root_id, "candidate_id": candidate_id, "family_id": family_id,
+        "spec_hash": spec_hash, "sidedness": sidedness, "econ_floor": econ_floor,
+        "evidence_class": evidence_class, "process_label": process_label, "registered_at": registered_at,
+        "sealed_pass_rule_hash": rule_hash if rule_hash is not None else sealed_eval.sealed_pass_rule_hash(),
+        "floors": floors,
+    }
+
+
+def _family_root_id(seed: str) -> str:
+    return scout_ledger.compute_family_root_id(f"impact_efficiency_trend_{seed}", "band_wall_touch", "trades_20")
+
+
+# === TC-1: the old caller-supplied `passed: bool` shape is structurally impossible ====================
+
+
+def test_tc1_the_old_passed_bool_call_shape_is_structurally_refused(tmp_path):
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+    with pytest.raises(TypeError):
+        g.record_sealed_evaluation(  # the OLD call shape, verbatim
+            grad_ledger, family_root_id="f", dataset_id="d", spec_hash="s", passed=True,
+        )
+
+
+# === TC-2: the full seven-step sequence, positive path =================================================
+
+
+def test_tc2_the_full_mandatory_sequence_derives_a_deterministic_pass_verdict_and_persists_it(tmp_path):
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("tc2")
+    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
+    candidate_spec = _candidate_spec(family_root_id=family_root_id)
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    result = sealed_eval.evaluate_sealed_verdict(
+        grad_ledger, shard_ledger, universe_ledger, accessor,
+        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+        observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
+    )
+
+    assert result["transition"] == g.TRANSITION_APPENDED
+    row = result["row"]
+    assert row["verdict"] == sealed_eval.SEALED_VERDICT_PASS
+    assert row["failure_reason"] is None
+    assert row["family_root_id"] == family_root_id
+    assert row["dataset_id"] == dataset_meta["id"]
+    assert row["candidate_id"] == "cand-1"
+    assert row["family_id"] == "fam-a"
+    assert row["spec_hash"] == "spec-hash-1"
+    assert row["shard_checksum"] == "c" * 64
+    assert row["evidence_class"] == wf.EVIDENCE_CLASS_HISTORICAL_OOS
+    assert row["process_label"] == wf.PROCESS_LABEL_RULE
+    assert row["outcome_basis"] == "mid"
+    assert row["n"] == 3
+    assert row["n_sessions"] == 1
+    assert row["n_symbols"] == 1
+    assert row["effect"] == pytest.approx(10.0)
+    assert row["sign"] == "positive"
+    assert row["econ_floor"] == _ECON_FLOOR
+    assert row["registered_direction"] == "long"
+    assert row["rule_id"] == sealed_eval.SEALED_PASS_RULE_V1
+    assert row["rule_version"] == sealed_eval.SEALED_PASS_RULE_VERSION
+    assert row["rule_hash"] == sealed_eval.sealed_pass_rule_hash()
+    assert row["evaluated_at"] == _EVALUATED_AT
+    assert row["observed_through"] is not None  # a genuine, real accessor read happened
+    assert "row_hash" in row  # step 7: the id+hash a transition needs
+
+    # persisted permanently, readable back via the single source of truth.
+    persisted = g.sealed_evaluations_for_family(grad_ledger, family_root_id)
+    assert len(persisted) == 1
+    assert persisted[0]["dataset_id"] == dataset_meta["id"]
+
+
+# === step 1/3 (migrated from test_micro_graduation.py -- this refusal moved here with the vault
+# confirmation itself): a shard exposed to a DIFFERENT family is refused, never trusted ===============
+
+
+def test_a_shard_exposed_to_a_different_family_is_refused(tmp_path):
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("wrong-family")
+    other_family_root_id = _family_root_id("the-actual-owner")
+    # the shard is exposed, but to a DIFFERENT family entirely.
+    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=other_family_root_id, dataset_id=dataset_meta["id"])
+    candidate_spec = _candidate_spec(family_root_id=family_root_id)
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    with pytest.raises(sealed_eval.SealedEvaluationRefusedError, match="not an EXPOSED vault shard"):
+        sealed_eval.evaluate_sealed_verdict(
+            grad_ledger, shard_ledger, universe_ledger, accessor,
+            candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+            observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
+        )
+    assert g.sealed_evaluations_for_family(grad_ledger, family_root_id) == []
+
+
+def test_a_spec_registered_after_shard_assignment_is_refused(tmp_path):
+    """Step 1's OTHER half: "frozen BEFORE that assignment" -- a candidate spec whose own
+    ``registered_at`` is AFTER the shard's own ``assigned_at`` is refused, never evaluated."""
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("late-registration")
+    shard_ledger, universe_ledger = _exposed_shard_for(
+        tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"], assigned_at=_ASSIGNED_AT,
+    )
+    late_spec = _candidate_spec(family_root_id=family_root_id, registered_at="2026-06-01T00:00:00.000000Z")  # AFTER _ASSIGNED_AT
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    with pytest.raises(sealed_eval.SealedEvaluationRefusedError, match="STRICTLY BEFORE"):
+        sealed_eval.evaluate_sealed_verdict(
+            grad_ledger, shard_ledger, universe_ledger, accessor,
+            candidate_spec=late_spec, dataset_id=dataset_meta["id"],
+            observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
+        )
+    assert g.sealed_evaluations_for_family(grad_ledger, family_root_id) == []
+
+
+# === TC-3: a rule changed (or never registered) after assignment fails CLOSED, never a pass ===========
+
+
+def test_tc3_a_rule_identity_mismatch_fails_closed_and_persists_nothing(tmp_path):
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("tc3")
+    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
+    candidate_spec = _candidate_spec(family_root_id=family_root_id, rule_hash="a-stale-or-never-registered-rule-hash")
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    with pytest.raises(sealed_eval.SealedEvaluationRefusedError, match="rule-identity|condition 4"):
+        sealed_eval.evaluate_sealed_verdict(
+            grad_ledger, shard_ledger, universe_ledger, accessor,
+            candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+            observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
+        )
+    # never a pass, never ANY verdict -- no artifact persisted at all.
+    assert g.sealed_evaluations_for_family(grad_ledger, family_root_id) == []
+
+
+# === TC-4: re-running on identical inputs yields a byte-identical artifact and verdict =================
+
+
+def test_tc4_rerunning_on_identical_inputs_is_byte_identical(tmp_path):
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("tc4")
+    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
+    candidate_spec = _candidate_spec(family_root_id=family_root_id)
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    first = sealed_eval.evaluate_sealed_verdict(
+        grad_ledger, shard_ledger, universe_ledger, accessor,
+        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+        observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
+    )
+    assert first["transition"] == g.TRANSITION_APPENDED
+
+    second = sealed_eval.evaluate_sealed_verdict(
+        grad_ledger, shard_ledger, universe_ledger, accessor,
+        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+        observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
+    )
+    assert second["transition"] == g.TRANSITION_REPLAYED
+    assert second["row"] == first["row"]
+    assert len(g.sealed_evaluations_for_family(grad_ledger, family_root_id)) == 1  # never a duplicate row
+
+
+# === TC-5: a second, DIFFERENT evaluation attempt for the SAME pair is refused, never a second draw ===
+
+
+def test_tc5_a_second_different_evaluation_attempt_is_refused(tmp_path):
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("tc5")
+    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
+    candidate_spec = _candidate_spec(family_root_id=family_root_id)
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    first = sealed_eval.evaluate_sealed_verdict(
+        grad_ledger, shard_ledger, universe_ledger, accessor,
+        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+        observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
+    )
+    assert first["row"]["verdict"] == sealed_eval.SEALED_VERDICT_PASS
+
+    # A genuinely DIFFERENT re-evaluation attempt (different observations -> a different recomputed
+    # effect, a different verdict) for the identical (family_root_id, dataset_id) pair.
+    with pytest.raises(g.GraduationTransitionRefusedError, match="never a second draw"):
+        sealed_eval.evaluate_sealed_verdict(
+            grad_ledger, shard_ledger, universe_ledger, accessor,
+            candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+            observations=_below_floor_observations(), evaluated_at="2026-06-11T00:00:00.000000Z",
+        )
+    # still exactly the FIRST verdict on permanent record -- never overwritten.
+    persisted = g.sealed_evaluations_for_family(grad_ledger, family_root_id)
+    assert len(persisted) == 1
+    assert persisted[0]["verdict"] == sealed_eval.SEALED_VERDICT_PASS
+
+
+# === TC-6: below any per-fold floor -> insufficient, distinct from FAIL, single shot still consumed ===
+
+
+def test_tc6_below_floor_observations_verdict_is_insufficient_and_consumes_the_single_shot(tmp_path):
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("tc6")
+    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
+    candidate_spec = _candidate_spec(family_root_id=family_root_id)
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    result = sealed_eval.evaluate_sealed_verdict(
+        grad_ledger, shard_ledger, universe_ledger, accessor,
+        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+        observations=_insufficient_observations(), evaluated_at=_EVALUATED_AT,
+    )
+    row = result["row"]
+    assert row["verdict"] == sealed_eval.SEALED_VERDICT_INSUFFICIENT
+    assert row["verdict"] != sealed_eval.SEALED_VERDICT_PASS
+    assert row["verdict"] != sealed_eval.SEALED_VERDICT_FAIL  # tri-state -- never coerced to a boolean
+    assert row["failure_reason"] is None
+    assert row["missing"]  # the exact arithmetic (e.g. "2 < 3") is carried, never silently dropped
+
+    # the single evaluation shot was genuinely consumed (the shard WAS exposed) -- a second attempt,
+    # even with now-sufficient observations, is refused, never a second draw.
+    with pytest.raises(g.GraduationTransitionRefusedError, match="never a second draw"):
+        sealed_eval.evaluate_sealed_verdict(
+            grad_ledger, shard_ledger, universe_ledger, accessor,
+            candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+            observations=_passing_observations(), evaluated_at="2026-06-11T00:00:00.000000Z",
+        )
+
+
+# === TC-7: a permanent FAILED verdict travels in every later export bundle =============================
+
+
+def test_tc7_a_failed_verdict_travels_permanently_in_the_export_bundle(tmp_path):
+    dataset_store, snapshots_dir, dataset_meta = _rig(tmp_path)
+    family_root_id = _family_root_id("tc7")
+    shard_ledger, universe_ledger = _exposed_shard_for(tmp_path, family_root_id=family_root_id, dataset_id=dataset_meta["id"])
+    candidate_spec = _candidate_spec(family_root_id=family_root_id)
+    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
+    grad_ledger = g.GraduationLedger(str(tmp_path / "grad"))
+
+    result = sealed_eval.evaluate_sealed_verdict(
+        grad_ledger, shard_ledger, universe_ledger, accessor,
+        candidate_spec=candidate_spec, dataset_id=dataset_meta["id"],
+        observations=_below_floor_observations(), evaluated_at=_EVALUATED_AT,
+    )
+    assert result["row"]["verdict"] == sealed_eval.SEALED_VERDICT_FAIL
+    assert result["row"]["failure_reason"] == "below_economic_floor"
+
+    from app.research.scout_ledger import ScoutLedger
+    from app.research import walkforward_ledger as wl
+    scout = ScoutLedger(str(tmp_path / "scout"))
+    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    bundle = g.build_export_bundle(
+        grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
+        family_root_id=family_root_id, handoff_created_at="2026-06-12T00:00:00.000000Z",
+    )
+    failed = [e for e in bundle["sealed_evaluations"] if e["verdict"] == sealed_eval.SEALED_VERDICT_FAIL]
+    assert len(failed) == 1
+    assert failed[0]["dataset_id"] == dataset_meta["id"]
+    assert bundle["family_multiplicity"]["prior_sealed_verdicts"] == bundle["sealed_evaluations"]
+
+
+# === TC-8 (mutation evidence): a deliberately weakened _derive_verdict makes the corrected assertion
+# fail, naming the specific wrong verdict; restoring makes it pass again. ==============================
+
+
+def test_tc8_weakening_the_economic_floor_condition_makes_the_below_floor_case_wrongly_pass(monkeypatch, tmp_path):
+    """The established, already-praised pattern (``test_micro_observer.py``'s TR-26 fix,
+    ``test_tc12_tr26_reverting_the_fix_makes_the_corrected_assertion_fail_restoring_it_passes``),
+    mirrored exactly: ``monkeypatch.setattr`` installs a deliberately-weakened ``_derive_verdict``
... [diff_bound] apps/backend/tests/test_micro_sealed_evaluation.py: 229 more diff lines omitted — Read the file for full detail
```
