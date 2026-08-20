# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 3.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/micro_graduation.py` (119 lines not shown)
- `apps/backend/tests/test_micro_graduation.py` (17 lines not shown)

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
 
 
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 7 +++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl | 2 ++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
