"""``micro_sealed_evaluation.py`` -- Era "The Rapid Microscope" J-07/TR-23 (r6 owner ruling,

``docs/rapid-validation-spec.md`` section 8.1, ``runs/goal-session-rapid-microscope/state/
assumptions.md`` 2026-08-18 "OWNER RULINGS (4)"): the SOLE scientific owner of the sealed-shard
evaluation verdict. Before this module existed, ``micro_graduation.record_sealed_evaluation`` took
an already-computed ``passed: bool`` straight from its caller -- a disclosed T-1 interpretation
call its own module docstring named as a placeholder, because "the statistical MACHINERY... does
not exist anywhere in this codebase yet". This module IS that machinery.

**The ledger owns history; the evaluator owns the answer (spec section 8.1's own opening line).**
``micro_graduation.py`` and ``vault.py`` remain persistence and transition machinery -- neither
accepts nor invents the scientific answer. This module never writes to a ledger file directly and
never hand-rolls a second hash chain: it computes an artifact, then calls THROUGH to
``micro_graduation.record_sealed_evaluation`` (the ALREADY-EXISTING ``GraduationLedger``/
``ROW_KIND_SEALED_EVALUATION`` machinery, reused verbatim) for the actual write.

**The seven-step mandatory sequence (spec section 8.1, any step failing => typed refusal, never a
verdict):**

1. require an ASSIGNED-then-``exposed`` shard (``vault.build_vault_state``, read-only, unmodified)
   bound to this EXACT ``family_root_id``, and a candidate spec whose own ``registered_at`` is
   STRICTLY BEFORE the shard's own ``assigned_at`` (spec: "frozen BEFORE that assignment").
2. verify the candidate spec's own ``spec_hash``/``family_root_id``/sidedness/``econ_floor`` are
   present, and that its recorded ``sealed_pass_rule_hash`` is byte-identical to the CURRENT
   ``sealed_pass_rule_hash()`` -- a mismatch (the rule changed, or was never registered) fails
   CLOSED with a typed refusal, never a computed verdict (TC-3).
3. obtain the shard ONLY through ``micro_accessor.MicroAccessor`` (an UNFENCED, ``origin=None``
   accessor the CALLER constructs -- the module docstring's own "two callers, two disciplines"
   precedent: this is a third such caller, a post-exposure whole-shard read, never a rolling-origin
   walk-forward fold, so wiring a live fence here would be the unrequested behavior change that
   module's own docstring warns against) plus ``vault.build_vault_state`` to confirm genuine
   ``exposed`` binding.
4. RECOMPUTE the outcome from canonical, already-consulted machinery --
   ``walkforward.summarize_fold_observations`` (never a second, independently-valued
   implementation) over a caller-supplied ``observations: list[dict]`` (the era's own "observations
   are the engine's one abstract input" convention, ``walkforward.py``'s module docstring, mirrored
   here exactly as ``evaluate_mode_b_fold`` already does it) -- never trusting a caller-computed
   effect number directly.
5. derive the verdict deterministically from ``SEALED_PASS_RULE_V1``'s five conditions.
6. persist an immutable evaluation artifact through ``micro_graduation.record_sealed_evaluation``.
7. return only that artifact's id (``dataset_id``/``family_root_id``) + hash (``row_hash``) --
   callers that want the full artifact read it back via ``micro_graduation.
   sealed_evaluations_for_family`` (single source of truth: the persisted row, never a second
   in-memory copy this function hands back as if it were authoritative).

**``SEALED_PASS_RULE_V1`` condition 1 is evaluator-owned and sealed-specific (spec section 8.1,
r9 owner ruling 2026-08-20, TR-30) -- it introduces exactly ONE new pinned numeric constant,
``SEALED_MIN_OBSERVATIONS`` (spec section 1), owned by THIS module alone.** The r6-era rule this
replaces reused ``walkforward.WF_FOLD_MIN_OBSERVATIONS``/``_SIGNAL_SESSIONS``/``_SYMBOLS`` verbatim
-- but the iteration-17 audit PROVED by execution that reusing those floors let a candidate spec's
own ``floors`` override certify a permanent ``pass`` off a single observation (a spec carrying
``floors={1,1,1}`` plus one observation produced ``verdict: "pass"`` under a ``rule_hash``
certifying 30/8/2 the run never applied), and separately proved that mechanically PINNING those
same floors was ALSO wrong: a vault shard is ONE symbol-day (spec section 7.3's own
``f"{symbol}:{YYYY-MM-DD}"`` seal key), so a single shard can never carry
``WF_FOLD_MIN_SIGNAL_SESSIONS`` = 8 signal-bearing SESSIONS or ``WF_FOLD_MIN_SYMBOLS`` = 2 SYMBOLS,
making PASS structurally unreachable. **The owner resolved the section-8.1-vs-7.3 contradiction by
separating the two stages scientifically rather than changing the sealing unit: the walk-forward
stage owns BREADTH (``WF_SURVIVOR_RULE_V1`` already establishes it before a candidate reaches the
sealed stage at all); the sealed stage owns UNTOUCHED REPLICATION on one hidden symbol-day.**
Session and symbol breadth are therefore computed for DISCLOSURE only (``n_sessions``/``n_symbols``
on the artifact) but never compared against any numeric floor at shard scope, and are recorded on
the floor-labeled artifact fields as the literal string ``"not_applicable_single_shard"`` --
never silently ``1``. **No sufficiency value may ever be sourced from the candidate or caller
spec**: any ``candidate_spec`` carrying a ``floors`` key (the exact override mechanism this rule
retires) is refused outright, BEFORE any verdict is derived (``SealedEvaluationRefusedError`` --
mirrors the step-2/step-4 fail-closed ordering elsewhere in this sequence). The family's OWN
pre-registered spec section 5.5 economic floor (``candidate_spec["econ_floor"]``) is unaffected by
r9 -- it was never a per-fold breadth floor and stays exactly as it was. ``rule_id``/``rule_version``
stay IDENTITY metadata (mirroring ``walkforward.WF_SURVIVOR_RULE_V1``'s own "the rule's own name IS
its identity" convention) -- r9 replaces condition 1's CONTENT, never the rule's name or version
(spec: "frozen; r9 replaces condition 1").

**The rule-identity-at-assignment interpretation call (T-1, disclosed).** Spec condition 4 needs
"the evaluation rule id/version/hash recorded AT ASSIGNMENT" to compare against "the one applied" --
but ``vault.assign_shard`` (frozen this era, OUT OF SCOPE to touch) carries no rule-identity field
at all. Since assignment binds ONE candidate family LINE to a shard, and a candidate spec must
already exist and be frozen before its shard is ever assigned (step 1 above), THIS module reads
"the rule recorded at assignment" as a field on the CANDIDATE SPEC ITSELF --
``candidate_spec["sealed_pass_rule_hash"]``, which a real caller would stamp with THIS module's own
``sealed_pass_rule_hash()`` at spec-registration time (before assignment, by construction of the
one-way vault lifecycle). A fixture proving "the rule changed after assignment" therefore supplies
a candidate spec whose OWN recorded hash no longer matches the CURRENT constant.

**Tri-state verdict (spec section 8.1 point 1): PASS / FAIL / ``insufficient`` -- never coerced to a
boolean.** ``insufficient`` fires when the recomputed observations miss ANY per-fold floor; it
consumes the single evaluation shot (the shard was genuinely exposed) but is neither a pass nor a
fail, and stays distinguishable from FAIL in the persisted artifact and every later export bundle
(``micro_graduation.build_export_bundle`` carries the artifact verbatim, never filtering or
collapsing it)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from . import vault
from . import walkforward as wf
from .micro_accessor import MicroAccessor
from .micro_graduation import (
    GraduationLedger,
    GraduationTransitionRefusedError,
    record_sealed_evaluation,
)

__all__ = [
    "SEALED_PASS_RULE_V1",
    "SEALED_PASS_RULE_VERSION",
    "SEALED_MIN_OBSERVATIONS",
    "SEALED_BREADTH_NOT_APPLICABLE",
    "SEALED_VERDICT_PASS",
    "SEALED_VERDICT_FAIL",
    "SEALED_VERDICT_INSUFFICIENT",
    "SEALED_VERDICTS",
    "SEALED_FAIL_REASONS",
    "SealedEvaluationRefusedError",
    "sealed_pass_parameters",
    "sealed_pass_rule_hash",
    "evaluate_sealed_verdict",
]

# === spec section 8.1's rule identity -- a NAME/VERSION, never a tunable numeric (module docstring) ==

SEALED_PASS_RULE_V1 = "SEALED_PASS_RULE_V1"
SEALED_PASS_RULE_VERSION = 1

# === spec section 1 (r9) -- the ONE sufficiency floor at sealed-shard scope. Pinned HERE, this
# module's own constant, mirroring (never importing) ``walkforward.WF_FOLD_MIN_OBSERVATIONS``'s
# pattern; never a ``Config`` field; never sourced from a candidate or caller spec. ===================
SEALED_MIN_OBSERVATIONS = 30

# session/symbol breadth are STRUCTURALLY inapplicable at shard scope (one shard = one symbol x one
# session-date, spec section 7.3) -- this literal string, never a silent ``1``, is what the artifact's
# floor-labeled breadth fields record (TC-4).
SEALED_BREADTH_NOT_APPLICABLE = "not_applicable_single_shard"

# The tri-state verdict vocabulary (spec section 8.1 point 1) -- OWNED here (the scientific answer's
# own module), never redefined a second time elsewhere. ``micro_graduation.py`` compares against the
# literal string "pass" directly (a disclosed, one-way-dependency interpretation call logged on
# ``evaluate_sealed_survivor_transition``'s own docstring) rather than importing this name, so that
# module -- which this module already imports FROM -- never has to import back, avoiding a cycle.
SEALED_VERDICT_PASS = "pass"
SEALED_VERDICT_FAIL = "fail"
SEALED_VERDICT_INSUFFICIENT = "insufficient"
SEALED_VERDICTS = (SEALED_VERDICT_PASS, SEALED_VERDICT_FAIL, SEALED_VERDICT_INSUFFICIENT)

# The closed-vocabulary FAIL reasons (the ``scout.KILL_REASONS`` convention, mirrored per the phase
# spec's own suggestion) -- one per non-floor SEALED_PASS_RULE_V1 condition. The floor condition's
# own failure reason is ``insufficient`` itself (a distinct verdict, not a FAIL reason) plus the
# ``summarize_fold_observations`` ``missing`` arithmetic, carried on the artifact separately.
SEALED_FAIL_REASONS: tuple[str, ...] = (
    "wrong_direction",
    "below_economic_floor",
    "evidence_class_or_process_label_ineligible",
)

REQUIRED_EVIDENCE_CLASS = wf.EVIDENCE_CLASS_HISTORICAL_OOS
REQUIRED_PROCESS_LABEL = wf.PROCESS_LABEL_RULE


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def sealed_pass_parameters() -> dict:
    """Every constant ``SEALED_PASS_RULE_V1`` depends on, embedded verbatim (the
    ``walkforward.walkforward_parameters``/``scout.scout_parameters`` pattern) -- (r9) condition 1
    is now SEALED-SPECIFIC: ``SEALED_MIN_OBSERVATIONS`` is this module's own pinned constant (never
    imported from ``walkforward.py``), and the fixed breadth policy
    (``SEALED_BREADTH_NOT_APPLICABLE``) is embedded too, so a future change to either one also
    changes ``sealed_pass_rule_hash()``. The walk-forward per-fold breadth floors
    (``WF_FOLD_MIN_SIGNAL_SESSIONS``/``WF_FOLD_MIN_SYMBOLS``) are DELIBERATELY absent -- they no
    longer govern condition 1 at all (breadth is the walk-forward stage's own province). Hashed
    into ``sealed_pass_rule_hash()``, which a candidate spec must carry (recorded before
    assignment) for condition 4's rule-identity check."""
    return {
        "sealed_pass_rule_id": SEALED_PASS_RULE_V1,
        "sealed_pass_rule_version": SEALED_PASS_RULE_VERSION,
        "sealed_min_observations": SEALED_MIN_OBSERVATIONS,
        "min_signal_sessions": SEALED_BREADTH_NOT_APPLICABLE,
        "min_symbols": SEALED_BREADTH_NOT_APPLICABLE,
        "required_evidence_class": REQUIRED_EVIDENCE_CLASS,
        "required_process_label": REQUIRED_PROCESS_LABEL,
    }


def sealed_pass_rule_hash() -> str:
    return _sha256(_canonical(sealed_pass_parameters()))


class SealedEvaluationRefusedError(Exception):
    """A step of the mandatory sequence (spec section 8.1) failed BEFORE any verdict was derived --
    never a fabricated result, never a silent skip. Distinct from a recorded ``FAIL`` verdict: this
    exception means no evaluation artifact was computed or persisted at all (the single evaluation
    shot is NOT consumed), whereas a recorded ``FAIL``/``insufficient`` verdict IS a permanent,
    persisted outcome that DOES consume the shot when the shard was genuinely exposed."""

    def __init__(self, family_root_id: str, dataset_id: str, reason: str) -> None:
        self.family_root_id = family_root_id
        self.dataset_id = dataset_id
        self.reason = reason
        super().__init__(
            f"sealed evaluation refused for family_root_id {family_root_id!r}, dataset_id "
            f"{dataset_id!r}: {reason}"
        )


def _expected_sign(sidedness: str) -> str:
    return "positive" if sidedness == "long" else "negative"


def _sealed_floors() -> dict:
    """(r9) The per-fold floors dict this module hands to
    ``walkforward.summarize_fold_observations`` -- FIXED, never candidate- or caller-controlled
    (the exact mechanism r9 retires; there is no override parameter anywhere in this function's
    signature, unlike the retired ``_resolved_floors(candidate_spec)`` it replaces). Only the
    observation count is gated, at ``SEALED_MIN_OBSERVATIONS``; session/symbol breadth are pinned
    to ``0`` so ``summarize_fold_observations``'s own per-fold status can never fail on breadth at
    shard scope -- breadth is the walk-forward stage's province (spec section 8.1 condition 1's own
    rationale), not this one's."""
    return {
        "wf_fold_min_observations": SEALED_MIN_OBSERVATIONS,
        "wf_fold_min_signal_sessions": 0,
        "wf_fold_min_symbols": 0,
    }


def _derive_verdict(
    summary: dict, *, sidedness: str, econ_floor: dict | None, evidence_class: str | None, process_label: str | None,
) -> tuple[str, str | None, dict]:
    """``SEALED_PASS_RULE_V1``'s five conditions (spec section 8.1), evaluated against an ALREADY-
    RECOMPUTED ``summarize_fold_observations`` summary -- extracted into its own, standalone,
    monkeypatchable function (the ``walkforward.evaluate_survivor_rule``/``sequence_verdict``
    precedent: the discretion-free predicate lives in ONE named place a test can mutate directly,
    mirroring the established mutation-proof shape rather than a big inline block a test could only
    exercise indirectly). Returns ``(verdict, failure_reason, conditions)`` -- ``failure_reason`` is
    ``None`` for both ``pass`` and ``insufficient`` (the latter's own arithmetic lives in the
    caller's ``summary["missing"]``, never duplicated here as a second reason string)."""
    condition_1_floors = summary["status"] == wf.FOLD_STATUS_SUFFICIENT
    if not condition_1_floors:
        return SEALED_VERDICT_INSUFFICIENT, None, {"sufficient_observations": False}

    expected_sign = _expected_sign(sidedness)
    condition_2_direction = summary["sign"] == expected_sign
    condition_3_magnitude = (
        econ_floor is not None
        and econ_floor.get("floor_bps") is not None
        and abs(summary["effect"]) >= econ_floor["floor_bps"]
    )
    condition_5_class_process = (
        evidence_class == REQUIRED_EVIDENCE_CLASS and process_label == REQUIRED_PROCESS_LABEL
    )
    conditions = {
        "sufficient_observations": True,
        "registered_direction": condition_2_direction,
        "clears_economic_floor": condition_3_magnitude,
        "historical_oos_rule_process": condition_5_class_process,
    }
    if condition_2_direction and condition_3_magnitude and condition_5_class_process:
        return SEALED_VERDICT_PASS, None, conditions
    if not condition_2_direction:
        failure_reason = "wrong_direction"
    elif not condition_3_magnitude:
        failure_reason = "below_economic_floor"
    else:
        failure_reason = "evidence_class_or_process_label_ineligible"
    return SEALED_VERDICT_FAIL, failure_reason, conditions


def evaluate_sealed_verdict(
    graduation_ledger: GraduationLedger,
    shard_ledger: "vault.VaultShardLedger",
    universe_ledger: "vault.VaultUniverseLedger",
    accessor: MicroAccessor,
    *,
    candidate_spec: dict,
    dataset_id: str,
    observations: list[dict],
    evaluated_at: str | None = None,
) -> dict:
    """The whole seven-step mandatory sequence (module docstring), steps 1-5 computed HERE, step 6
    delegated to ``micro_graduation.record_sealed_evaluation`` (the ledger's own single-shot
    dedup/idempotent-replay discipline, TR-12, applies unchanged), step 7 satisfied by this
    function's own return value (``result["row"]`` carries ``dataset_id``+``row_hash`` -- the ONLY
    fields a transition needs to consume, per ``evaluate_sealed_survivor_transition``'s existing,
    unchanged read of ``row_hash``).

    ``observations`` is caller-supplied (the "one abstract input" convention, module docstring) --
    a future J-08/J-09 route/CLI reduces the shard's raw snapshot rows to
    ``{session_date, symbol, value}`` triples for THIS candidate's own feature/structure_context/
    outcome definition (Scout's own job, ``scout.extract_anchors``'s territory -- not reinvented
    here, matching ``micro_graduation.py``'s own established "a real future join... is a natural
    J-08/J-09 wiring concern, not invented here" precedent). This function's OWN accessor read
    (below) is independent of ``observations`` -- it exists to satisfy step 3 for real (the shard
    must be genuinely obtainable through the sanctioned door) and to stamp the artifact's own
    ``observed_through`` from the shard's actual recorded data timeline, never from ``observations``
    or a caller-supplied value."""
    family_root_id = candidate_spec.get("family_root_id")
    if not family_root_id:
        raise SealedEvaluationRefusedError(
            str(family_root_id), dataset_id,
            "candidate_spec carries no family_root_id -- refused (step 2): a spec identity is "
            "mandatory before any shard read",
        )
    spec_hash = candidate_spec.get("spec_hash")
    sidedness = candidate_spec.get("sidedness")
    econ_floor = candidate_spec.get("econ_floor")
    recorded_rule_hash = candidate_spec.get("sealed_pass_rule_hash")
    spec_registered_at = candidate_spec.get("registered_at")
    if not (spec_hash and sidedness and spec_registered_at):
        raise SealedEvaluationRefusedError(
            family_root_id, dataset_id,
            "candidate_spec is missing one of spec_hash/sidedness/registered_at -- refused "
            "(step 2): the candidate's canonical registered spec must be complete before a sealed "
            "evaluation is attempted",
        )

    # --- step 2 (r9 sufficiency-ownership half, TR-30): a candidate_spec carrying a 'floors'
    # override -- the exact caller-controlled mechanism r9 retires -- is refused OUTRIGHT, before
    # any verdict is derived and before the shard/accessor read below. No sufficiency value may
    # ever be sourced from the candidate or caller spec (spec section 8.1 condition 1): the sealed
    # evaluator alone owns SEALED_MIN_OBSERVATIONS and the fixed breadth policy. -------------------
    if "floors" in candidate_spec:
        raise SealedEvaluationRefusedError(
            family_root_id, dataset_id,
            f"candidate_spec carries a 'floors' override ({candidate_spec['floors']!r}) -- refused "
            "(spec section 8.1 condition 1, r9/TR-30): sealed-shard sufficiency is evaluator-owned; "
            "no caller-supplied floor, threshold, or equivalent override is ever honoured",
        )

    # --- step 2 (rule identity half): the rule recorded on the spec BEFORE assignment must be
    # byte-identical to the one this evaluator is ABOUT to apply -- a mismatch fails CLOSED, never
    # a computed verdict (TC-3). Checked BEFORE any shard read, so a rule change is caught even if
    # the shard read would otherwise succeed. ------------------------------------------------------
    current_rule_hash = sealed_pass_rule_hash()
    if recorded_rule_hash != current_rule_hash:
        raise SealedEvaluationRefusedError(
            family_root_id, dataset_id,
            f"the candidate spec's recorded sealed_pass_rule_hash {recorded_rule_hash!r} does not "
            f"match the currently-applied {SEALED_PASS_RULE_V1!r} hash {current_rule_hash!r} -- "
            "refused (spec section 8.1 condition 4): a rule changed (or never registered) after "
            "assignment fails closed, never a pass",
        )

    # --- step 1 + step 3 (vault half): the shard must be genuinely EXPOSED and bound to this EXACT
    # family_root_id (never trust a caller's say-so -- the same confirmation the retired
    # record_sealed_evaluation used to perform, reused verbatim via the SAME build_vault_state call,
    # never a second implementation of vault semantics). ---------------------------------------------
    vault_state = vault.build_vault_state(shard_ledger, universe_ledger)
    shard_entry = next((s for s in vault_state["shards"] if s.get("dataset_id") == dataset_id), None)
    if (
        shard_entry is None
        or shard_entry.get("exposure_state") != vault.STATE_EXPOSED
        or shard_entry.get("family_root_id") != family_root_id
    ):
        raise SealedEvaluationRefusedError(
            family_root_id, dataset_id,
            f"dataset_id {dataset_id!r} is not an EXPOSED vault shard bound to this exact "
            "family_root_id -- refused (spec section 7.4/8.1 step 1): a sealed-shard evaluation "
            "can only run against a shard genuinely exposed to this family",
        )
    assigned_at = shard_entry.get("assigned_at")
    if not assigned_at or not (spec_registered_at < assigned_at):
        raise SealedEvaluationRefusedError(
            family_root_id, dataset_id,
            f"candidate spec registered_at {spec_registered_at!r} is not STRICTLY BEFORE the "
            f"shard's own assigned_at {assigned_at!r} -- refused (spec section 8.1 step 1): the "
            "candidate spec must be frozen before assignment, never after",
        )

    # --- step 3 (accessor half): obtain the shard ONLY through the sanctioned accessor -- an
    # UNFENCED (origin=None) accessor, exactly like micro_join.py/scout.py's own re-pointed reads
    # (module docstring). A fenced accessor here would be a silent, unrequested behavior change. ----
    if accessor.origin is not None:
        raise SealedEvaluationRefusedError(
            family_root_id, dataset_id,
            f"the sealed evaluator requires an UNFENCED accessor (origin=None); this accessor's "
            f"origin is {accessor.origin!r} -- refused",
        )
    raw_rows = accessor.read_snapshot_rows(dataset_id)
    observed_through_values = [row["observed_through"] for row in raw_rows if row.get("observed_through") is not None]
    observed_through = max(observed_through_values) if observed_through_values else None

    # --- step 4: RECOMPUTE via the canonical statistical core, never trust a caller-computed
    # effect -- summarize_fold_observations is the SAME function walk-forward folds themselves
    # consult (never reimplemented). (r9) The floors handed in are FIXED and evaluator-owned
    # (SEALED_PASS_RULE_V1 condition 1's own sealed-specific rule, never the candidate spec's). -----
    floors = _sealed_floors()
    summary = wf.summarize_fold_observations(observations, floors)

    evaluated_at_value = evaluated_at if evaluated_at is not None else _iso_utc_now()

    # --- step 5: derive the tri-state verdict from SEALED_PASS_RULE_V1's five conditions ----------
    verdict, failure_reason, conditions = _derive_verdict(
        summary,
        sidedness=sidedness,
        econ_floor=econ_floor,
        evidence_class=candidate_spec.get("evidence_class"),
        process_label=candidate_spec.get("process_label"),
    )

    # --- step 6: persist the immutable artifact through the ALREADY-EXISTING ledger machinery
    # (micro_graduation.py's own "persistence stays there" contract, module docstring). -------------
    artifact = {
        "candidate_id": candidate_spec.get("candidate_id"),
        "family_id": candidate_spec.get("family_id"),
        "spec_hash": spec_hash,
        "shard_checksum": shard_entry.get("content_checksum"),
        "shard_symbol": shard_entry.get("symbol"),
        "shard_session_date": shard_entry.get("session_date"),
        "evidence_class": candidate_spec.get("evidence_class"),
        "process_label": candidate_spec.get("process_label"),
        "outcome_basis": candidate_spec.get("outcome_basis", "mid"),
        "n": summary["n"],
        # (r9) disclosure-only counts -- informational, never compared against a numeric floor at
        # shard scope (see floors_applied below for the floor-labeled fields TC-4 targets).
        "n_sessions": summary["n_sessions"],
        "n_symbols": summary["n_symbols"],
        # spec section 8.1: the artifact must be "sufficient to reproduce the verdict". (r9) The
        # ONLY sufficiency floor at shard scope is SEALED_MIN_OBSERVATIONS; session/symbol breadth
        # are recorded as the literal string SEALED_BREADTH_NOT_APPLICABLE -- never a silent 1 --
        # because they are structurally inapplicable to a one-symbol-day shard, never because they
        # were unmet (TC-4).
        "floors_applied": {
            "min_observations": SEALED_MIN_OBSERVATIONS,
            "min_signal_sessions": SEALED_BREADTH_NOT_APPLICABLE,
            "min_symbols": SEALED_BREADTH_NOT_APPLICABLE,
        },
        "effect": summary["effect"],
        "sign": summary["sign"],
        "missing": summary["missing"],
        "econ_floor": econ_floor,
        "registered_direction": sidedness,
        "rule_id": SEALED_PASS_RULE_V1,
        "rule_version": SEALED_PASS_RULE_VERSION,
        "rule_hash": current_rule_hash,
        "verdict": verdict,
        "failure_reason": failure_reason,
        "conditions": conditions,
        "observed_through": observed_through,
        "evaluated_at": evaluated_at_value,
    }
    result = record_sealed_evaluation(
        graduation_ledger, family_root_id=family_root_id, dataset_id=dataset_id, artifact=artifact,
    )
    # --- step 7: the caller (a future graduation transition) needs only id+hash -- both already sit
    # on result["row"] (dataset_id, family_root_id, row_hash) -- no second, narrower return shape is
    # invented here; a caller that wants the full artifact reads it back via
    # micro_graduation.sealed_evaluations_for_family, the single source of truth. -------------------
    return result
