"""``micro_graduation.py`` -- Era "The Rapid Microscope" J-07 (``docs/rapid-validation-spec.md``

section 8): the stage vocabulary ``exploratory -> walkforward_survivor -> sealed_survivor ->
referee_handoff_ready`` and the provenance-complete export bundle. This module OWNS no research
computation of its own -- it is a pure bookkeeping/state-machine layer that reads already-computed,
already-ledgered evidence from three sibling modules and records WHICH state a candidate family has
earned, with full provenance and nothing laundered out.

**A fourth ``HashChainedLedger``, reusing the SAME shared primitive -- never a hand-rolled chain**
(the carried iter-4 lesson, named explicitly in this iteration's own spec). ``walkforward_ledger.py``
already established the "one global chain, N row kinds, discriminated by ``row_kind``" shape for
exactly this reason; this module's ``GraduationLedger`` is a third instance of that SAME shape
(``state_transition`` rows and ``sealed_evaluation`` rows share one physical file), built on
``micro_chain_ledger.HashChainedLedger`` directly -- the tail-anchor discipline (a truncated LAST
row is otherwise invisible to a hash chain alone) comes for free.

**Two identity spaces this era has never joined -- and this module does not invent a join.** A
Scout candidate's identity is ``family_root_id`` (``scout_ledger.compute_family_root_id`` --
``sha256(feature_family_name, structure_context_kind, outcome_horizon_family)``). A walk-forward
SEQUENCE's identity is ``sequence_id`` (``walkforward.sequence_id_for`` --
``sha256(corpus_id, rule_identity)``). No fold_result row anywhere carries a ``family_root_id``
field (confirmed by reading ``register_mode_a_origin``/``evaluate_mode_b_fold``'s own row_fields --
neither stamps one), and OUT OF SCOPE forbids adding one (no change to ``walkforward_ledger.py``'s
persisted row shape). So every function below that needs BOTH identities (``evaluate_walkforward_
survivor_transition``, ``build_export_bundle``) takes ``sequence_id`` as an explicit, caller-supplied
argument alongside ``family_root_id`` -- exactly the same "caller already knows both, this module
never guesses a join" discipline ``evaluate_mode_b_fold`` itself uses for ``spec``/``fold``. A real
future join (a Scout candidate registering ITS OWN sequence_id at Mode-B spec time) is a natural
J-08/J-09 wiring concern, not invented here.

**The sealed-shard EVALUATION verdict is caller-supplied, not computed here -- a disclosed T-1
interpretation call.** Spec section 8 state 3 requires "additionally passed its single-shot
root-family-level sealed-shard evaluation (section 7.4, keyed on family_root_id) under a spec frozen
before assignment" as a CONDITION -- it does not prescribe the statistical MACHINERY that produces a
pass/fail verdict from a sealed shard's exposed event data (that would be a Mode-B-style evaluation
run through the accessor against real vault data, which does not exist anywhere in this codebase yet
and is out of THIS iteration's scope: zero real sealed shards exist this era, J-06 step 4 is
human-blocked, and TR-3/accessor territory is explicitly deferred to a dedicated J-10 hardening
iteration). ``vault.py`` itself carries no pass/fail concept at all -- only shard LIFECYCLE state
(sealed/assigned/exposed). So ``record_sealed_evaluation`` below is handed an ALREADY-COMPUTED
``passed`` verdict (mirroring ``walkforward.py``'s own "a corpus-specific reader feeds a
corpus-agnostic statistical core" split for its Mode-B evaluator) and is responsible for exactly the
TWO things spec section 8 DOES specify: (1) confirming, via ``vault.py``'s existing, UNMODIFIED
``build_vault_state`` (never a new vault.py function), that the named shard genuinely reached
``exposed`` for this EXACT ``family_root_id`` before any verdict is ever recorded against it -- never
trusting the caller's claim alone; and (2) recording that verdict PERMANENTLY, exactly once per
(family_root_id, dataset_id) (TR-12) -- pass OR fail, since spec section 7.4's own words are "a
failed sealed verdict is a permanent root-family fact carried in every later export bundle".

**The export bundle is buildable for ANY ledgered family, at ANY state -- not gated to
``sealed_survivor``+.** This is what makes TC-6's "a failed-sealed twin's permanent failed verdict
is carried into its own bundle" possible at all: if bundle-building required ``sealed_survivor``, a
family that legitimately reached only ``walkforward_survivor`` (its sealed attempt having FAILED)
could never have its own failure inspected through this function. ``build_export_bundle`` therefore
always returns the complete provenance on record PLUS the family's own current ``state`` field --
``referee_handoff_ready`` is a STATE TRANSITION (``evaluate_referee_handoff_ready_transition``)
earned by attempting to build a bundle for a ``sealed_survivor`` candidate and having it VALIDATE
(``bundle_validates``); the bundle-building primitive itself carries no gate.

**No new module constant, no ``graduation_parameters()``.** Every sibling module with its own tuned
constants (``scout.py``'s ``SCOUT_SCREEN_ALPHA``, ``walkforward.py``'s ``WF_MIN_SUFFICIENT_FOLDS``,
...) embeds a ``*_parameters()`` function so a persisted record can key on their hash (the era's
Parameters discipline, goal.md Constraints). This module introduces NO tunable numeric constant of
its own -- ``WF_SURVIVOR_RULE_V1`` is evaluated ENTIRELY by ``walkforward.sequence_verdict``
(consulted, never reimplemented, per this iteration's own spec), and the sealed-shard verdict is
caller-supplied. A ``graduation_parameters()`` function would have nothing genuine to embed, so none
exists -- inventing one would be exactly the "config for behavior the spec fixed" the simplicity bar
forbids.

**Idempotent, identity-keyed, replay-safe (the iter-5 lesson, named for this exact journey in this
iteration's own spec).** Every state-advancing function below checks FIRST whether the target
transition (or, for sealed evaluation, the identical (family_root_id, dataset_id) verdict) is
ALREADY recorded and returns ``{"transition": "replayed", ...}`` without touching the ledger file --
mirroring ``walkforward_ledger.register_fold_spec``'s own "re-registering the IDENTICAL content is an
idempotent replay; a genuinely DIFFERENT one is refused" split. A repeated advancement check with no
new ledgered evidence therefore NEVER appends a second row (TC-7); a genuinely conflicting second
claim is refused outright, never silently accepted (the sealed-evaluation half of this split)."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from . import vault
from . import walkforward as wf
from .micro_chain_ledger import HashChainedLedger
from .scout_ledger import ScoutLedger, distinct_variant_count

__all__ = [
    "GRADUATION_STATE_EXPLORATORY",
    "GRADUATION_STATE_WALKFORWARD_SURVIVOR",
    "GRADUATION_STATE_SEALED_SURVIVOR",
    "GRADUATION_STATE_REFEREE_HANDOFF_READY",
    "GRADUATION_STATES_ORDER",
    "TRANSITION_APPENDED",
    "TRANSITION_REPLAYED",
    "ROW_KIND_STATE_TRANSITION",
    "ROW_KIND_SEALED_EVALUATION",
    "REFEREE_FUTURE_REVISION_SENTENCE",
    "EMPTY_LEDGER_MESSAGE",
    "GraduationTransitionRefusedError",
    "GraduationLedger",
    "resolve_micro_graduation_dir",
    "state_transitions_for_family",
    "current_graduation_state",
    "sealed_evaluations_for_family",
    "evaluate_walkforward_survivor_transition",
    "record_sealed_evaluation",
    "evaluate_sealed_survivor_transition",
    "build_export_bundle",
    "bundle_validates",
    "evaluate_referee_handoff_ready_transition",
    "list_graduation_families",
]

# === spec section 8's four states, strictly ordered (transcribed verbatim) ==========================

GRADUATION_STATE_EXPLORATORY = "exploratory"
# Reuses `walkforward.WF_VERDICT_SURVIVOR` verbatim -- single source of truth for the token: the
# SAME string names both "the WF_SURVIVOR_RULE_V1 verdict" (walkforward.py's own vocabulary) and
# "the graduation state a candidate earns by satisfying it" (spec section 8's own vocabulary),
# because spec section 8 point 2 defines the state to BE exactly that verdict. Minting a second,
# independently-spelled constant here would risk the two silently drifting apart.
GRADUATION_STATE_WALKFORWARD_SURVIVOR = wf.WF_VERDICT_SURVIVOR
GRADUATION_STATE_SEALED_SURVIVOR = "sealed_survivor"
GRADUATION_STATE_REFEREE_HANDOFF_READY = "referee_handoff_ready"

# Documents the invariant (spec section 8's opening line: "States, strictly ordered") -- not used as
# a generic "advance N states" lookup anywhere below (no code path needs one; each transition
# function names its own single, specific predecessor state), so this stays a plain tuple, never a
# rank-comparison helper this iteration has no tested use for.
GRADUATION_STATES_ORDER = (
    GRADUATION_STATE_EXPLORATORY,
    GRADUATION_STATE_WALKFORWARD_SURVIVOR,
    GRADUATION_STATE_SEALED_SURVIVOR,
    GRADUATION_STATE_REFEREE_HANDOFF_READY,
)

TRANSITION_APPENDED = "appended"
TRANSITION_REPLAYED = "replayed"

ROW_KIND_STATE_TRANSITION = "state_transition"
ROW_KIND_SEALED_EVALUATION = "sealed_evaluation"

# spec section 8 point 4, transcribed close to verbatim -- TC-4. A module-level constant (never
# re-composed per call) so `bundle_validates` can compare byte-exactly and every caller (the bundle
# builder, the test suite) reads the identical sentence.
REFEREE_FUTURE_REVISION_SENTENCE = (
    "This referee_handoff_ready state does not imply the current Referee can register or "
    "adjudicate this candidate: a flow-context predicate requires a future named revision of "
    "docs/referee-statistical-spec.md. Where a candidate maps onto the existing referee vocabulary "
    "(setup, side, existing context predicates, existing measures), the bundle is registrable "
    "through the existing operator act unchanged."
)

# goal.md's own Design Direction example, verbatim ("Honest empty/degraded states are first-class
# copy") -- TC-9's own literal string.
EMPTY_LEDGER_MESSAGE = "No candidates ledgered."

_GRADUATION_DIR_ENV = "TAPEOLOGY_MICRO_GRADUATION_DIR"
_LEDGER_FILENAME = "graduation_ledger.jsonl"


class GraduationTransitionRefusedError(Exception):
    """A graduation transition was refused -- never silently skipped, never silently advanced (spec
    section 8; TC-5). Carries the exact ``family_root_id``/``target_state``/``reason`` so a caller
    can report WHY without parsing prose (the ``vault.ShardLifecycleOrderError`` structured-args
    precedent)."""

    def __init__(self, family_root_id: str, target_state: str, reason: str) -> None:
        self.family_root_id = family_root_id
        self.target_state = target_state
        self.reason = reason
        super().__init__(
            f"graduation transition to {target_state!r} refused for family_root_id "
            f"{family_root_id!r}: {reason}"
        )


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def resolve_micro_graduation_dir(dataset_dir_resolved: str) -> str:
    """``TAPEOLOGY_MICRO_GRADUATION_DIR`` if set, else a ``micro_graduation`` SIBLING of the
    caller's already-resolved dataset directory -- the ``scout_ledger.resolve_scout_ledger_dir``/
    ``vault.resolve_vault_dir`` pattern verbatim. Never a ``Config`` field (an operational
    storage-location knob, goal.md Constraints)."""
    override = os.environ.get(_GRADUATION_DIR_ENV)
    if override:
        return override
    return str(Path(dataset_dir_resolved).parent / "micro_graduation")


class GraduationLedger:
    """A thin domain wrapper over ONE ``HashChainedLedger`` -- the ``walkforward_ledger.
    WalkForwardLedger`` "one global chain, N row kinds" shape, mirrored exactly."""

    def __init__(self, root_dir: str | Path) -> None:
        self._chain = HashChainedLedger(root_dir, _LEDGER_FILENAME)

    def verify_chain(self) -> dict:
        return self._chain.verify_chain()

    def all_rows(self) -> list[dict]:
        return self._chain.all_rows()

    def rows_of_kind(self, row_kind: str) -> list[dict]:
        return [row for row in self._chain.all_rows() if row.get("row_kind") == row_kind]

    def append_row(self, fields: dict) -> dict:
        """The pure storage primitive (the ``WalkForwardLedger.append_row`` precedent -- enforces
        no business rule of its own; every function below is the validated entry point)."""
        return self._chain.append_row(fields)


# === read-only queries over THIS module's own ledger =================================================


def state_transitions_for_family(ledger: GraduationLedger, family_root_id: str) -> list[dict]:
    """Every ``state_transition`` row ever recorded for ``family_root_id``, append order --
    including every state it has EVER held, never merely the current one (nothing laundered out)."""
    return [
        row for row in ledger.rows_of_kind(ROW_KIND_STATE_TRANSITION)
        if row.get("family_root_id") == family_root_id
    ]


def current_graduation_state(ledger: GraduationLedger, family_root_id: str) -> str:
    """The family's current state: the LAST recorded ``state_transition`` row's ``to_state``, or
    ``GRADUATION_STATE_EXPLORATORY`` when none exists -- spec section 8 point 1's own "any ledgered
    candidate [is exploratory]" needs no row of its own; a candidate's mere existence in the Scout
    ledger already establishes it, so exploratory is the implicit default this function reads back
    rather than a fact this module ever appends. Append order IS chronological order here (every
    transition function below only ever appends the SINGLE next state after checking its own
    precondition), so the last row is always the current one -- never a rank comparison needed."""
    transitions = state_transitions_for_family(ledger, family_root_id)
    if not transitions:
        return GRADUATION_STATE_EXPLORATORY
    return transitions[-1]["to_state"]


def sealed_evaluations_for_family(ledger: GraduationLedger, family_root_id: str) -> list[dict]:
    """Every ``sealed_evaluation`` row ever recorded for ``family_root_id`` -- pass AND fail alike,
    permanent, never filtered (TR-12/TC-6: a failed verdict is a permanent root-family fact)."""
    return [
        row for row in ledger.rows_of_kind(ROW_KIND_SEALED_EVALUATION)
        if row.get("family_root_id") == family_root_id
    ]


# === state 2: exploratory -> walkforward_survivor (spec section 8 point 2, TC-1/TC-5/TC-7) ==========


def evaluate_walkforward_survivor_transition(
    graduation_ledger: GraduationLedger,
    wf_ledger: "wf.WalkForwardLedger",
    *,
    family_root_id: str,
    sequence_id: str,
    evaluated_at: str | None = None,
) -> dict:
    """Reads this sequence's fold rows via ``walkforward.fold_results_for_sequence`` (existing,
    read-only) and its corpus's voiding state via ``walkforward.is_corpus_era_voided`` (existing,
    read-only) -- ``corpus_id`` is read OFF the ledgered fold rows themselves (``fold_results[0]
    ["corpus_id"]``), never a second caller-supplied value that could drift from what is actually
    ledgered. Delegates the ENTIRE five-condition ``WF_SURVIVOR_RULE_V1`` predicate to
    ``walkforward.sequence_verdict`` -- consulted, never reimplemented (this iteration's own spec):
    the rule's conditions live in exactly ONE function in this codebase, and duplicating them here
    would be the "second, independently-valued copy" this codebase's own conventions warn against.

    Idempotent + identity-keyed (``family_root_id`` + this target state, iter-5 lesson): a
    ``family_root_id`` that already carries a ``walkforward_survivor`` transition row is answered
    ``replayed`` with the EXISTING row -- walk-forward evidence is read-only from this module's own
    vantage, so re-evaluating could only ever reproduce the identical verdict from the identical
    ledgered folds (TC-7). Raises ``GraduationTransitionRefusedError`` (never silently advances,
    never returns a fabricated verdict) when the ledgered evidence does not satisfy the rule --
    covering BOTH "fewer than WF_MIN_SUFFICIENT_FOLDS sufficient folds exist" (``sequence_verdict``'s
    own floor refusal) and "sufficient folds exist but the rule's five conditions are not jointly
    met" (e.g. TC-5's diagnostic-only twin, whose folds are all ``historical_exposed_diagnostic`` and
    so never become ``eligible``, failing condition 1)."""
    already = [
        row for row in state_transitions_for_family(graduation_ledger, family_root_id)
        if row["to_state"] == GRADUATION_STATE_WALKFORWARD_SURVIVOR
    ]
    if already:
        return {"transition": TRANSITION_REPLAYED, "state": GRADUATION_STATE_WALKFORWARD_SURVIVOR, "row": dict(already[-1])}

    fold_results = wf.fold_results_for_sequence(wf_ledger, sequence_id)
    corpus_id = fold_results[0]["corpus_id"] if fold_results else None
    sidedness = fold_results[0]["sidedness"] if fold_results else None
    econ_floor = fold_results[0]["econ_floor"] if fold_results else None
    voided = wf.is_corpus_era_voided(wf_ledger, corpus_id) if corpus_id is not None else False

    verdict = wf.sequence_verdict(fold_results, sidedness=sidedness, econ_floor=econ_floor, voided=voided)
    if verdict.get("refused"):
        raise GraduationTransitionRefusedError(
            family_root_id, GRADUATION_STATE_WALKFORWARD_SURVIVOR,
            f"walkforward.sequence_verdict refused: {verdict['reason']}",
        )
    if verdict["verdict"] != wf.WF_VERDICT_SURVIVOR:
        raise GraduationTransitionRefusedError(
            family_root_id, GRADUATION_STATE_WALKFORWARD_SURVIVOR,
            f"WF_SURVIVOR_RULE_V1 not satisfied -- conditions: {verdict['conditions']}",
        )

    fields = {
        "row_kind": ROW_KIND_STATE_TRANSITION,
        "family_root_id": family_root_id,
        "sequence_id": sequence_id,
        "corpus_id": corpus_id,
        "from_state": GRADUATION_STATE_EXPLORATORY,
        "to_state": GRADUATION_STATE_WALKFORWARD_SURVIVOR,
        "rule_name": verdict["rule_name"],
        "conditions": verdict["conditions"],
        "n_sufficient_folds": verdict["n_sufficient_folds"],
        "n_eligible_folds": verdict["n_eligible_folds"],
        "evaluated_at": evaluated_at if evaluated_at is not None else _iso_utc_now(),
    }
    row = graduation_ledger.append_row(fields)
    return {"transition": TRANSITION_APPENDED, "state": GRADUATION_STATE_WALKFORWARD_SURVIVOR, "row": row}


# === state 3: walkforward_survivor -> sealed_survivor (spec section 8 point 3, TC-2/TC-6) ===========


def record_sealed_evaluation(
    graduation_ledger: GraduationLedger,
    vault_shard_ledger: "vault.VaultShardLedger",
    vault_universe_ledger: "vault.VaultUniverseLedger",
    *,
    family_root_id: str,
    dataset_id: str,
    spec_hash: str,
    passed: bool,
    detail: dict | None = None,
    evaluated_at: str | None = None,
) -> dict:
    """Records a single-shot sealed-shard evaluation verdict (module docstring: the verdict itself
    is caller-supplied; this function's own job is the confirmation + the permanent recording).
    Confirms, via ``vault.build_vault_state`` (existing, unmodified), that ``dataset_id`` is
    genuinely ``exposed`` and bound to this EXACT ``family_root_id`` -- refusing
    (``GraduationTransitionRefusedError``) a claimed evaluation against a shard that was never
    actually exposed to this family, rather than trusting the caller's say-so.

    Single-shot (TR-12): a SECOND call for the identical ``(family_root_id, dataset_id)`` pair is an
    idempotent ``replayed`` no-op when it repeats the SAME ``(passed, spec_hash)`` verdict (a benign
    repeat of an operator act, the ``register_fold_spec`` precedent), but is REFUSED outright when it
    would record a DIFFERENT verdict -- "sealed exposure is ... never a second draw" (goal.md
    anti-goal) means even a caller HONESTLY re-evaluating never gets to overwrite or supplement a
    verdict already on permanent record."""
    existing_for_shard = [
        row for row in sealed_evaluations_for_family(graduation_ledger, family_root_id)
        if row.get("dataset_id") == dataset_id
    ]
    if existing_for_shard:
        prior = existing_for_shard[-1]
        if prior["passed"] == bool(passed) and prior["spec_hash"] == spec_hash:
            return {"transition": TRANSITION_REPLAYED, "row": dict(prior)}
        raise GraduationTransitionRefusedError(
            family_root_id, GRADUATION_STATE_SEALED_SURVIVOR,
            f"a sealed-shard evaluation for dataset_id {dataset_id!r} is ALREADY recorded "
            f"(passed={prior['passed']!r}, spec_hash={prior['spec_hash']!r}); a second, DIFFERENT "
            f"evaluation attempt (passed={bool(passed)!r}, spec_hash={spec_hash!r}) is refused "
            "(spec section 7.4/TR-12): sealed exposure is single-shot, never a second draw",
        )

    vault_state = vault.build_vault_state(vault_shard_ledger, vault_universe_ledger)
    shard_entry = next((s for s in vault_state["shards"] if s.get("dataset_id") == dataset_id), None)
    if (
        shard_entry is None
        or shard_entry.get("exposure_state") != vault.STATE_EXPOSED
        or shard_entry.get("family_root_id") != family_root_id
    ):
        raise GraduationTransitionRefusedError(
            family_root_id, GRADUATION_STATE_SEALED_SURVIVOR,
            f"dataset_id {dataset_id!r} is not an EXPOSED vault shard bound to this exact "
            "family_root_id -- refused (spec section 7.4): a sealed-shard evaluation can only be "
            "recorded against a shard genuinely exposed to this family",
        )

    fields = {
        "row_kind": ROW_KIND_SEALED_EVALUATION,
        "family_root_id": family_root_id,
        "dataset_id": dataset_id,
        "spec_hash": spec_hash,
        "passed": bool(passed),
        "detail": dict(detail) if detail else {},
        "evaluated_at": evaluated_at if evaluated_at is not None else _iso_utc_now(),
    }
    row = graduation_ledger.append_row(fields)
    return {"transition": TRANSITION_APPENDED, "row": row}


def evaluate_sealed_survivor_transition(
    graduation_ledger: GraduationLedger,
    *,
    family_root_id: str,
    dataset_id: str,
    evaluated_at: str | None = None,
) -> dict:
    """Requires the family to already be ``walkforward_survivor`` (states are strictly ordered,
    spec section 8's own opening line -- never skipped) and requires an ALREADY-RECORDED, PASSING
    ``record_sealed_evaluation`` verdict for ``(family_root_id, dataset_id)``. A recorded FAILING
    verdict refuses this transition outright (TC-6: the state never advances past
    ``walkforward_survivor``, but the failed verdict itself stays permanently on record via
    ``sealed_evaluations_for_family``/``build_export_bundle``). Idempotent + identity-keyed exactly
    like ``evaluate_walkforward_survivor_transition`` above."""
    already = [
        row for row in state_transitions_for_family(graduation_ledger, family_root_id)
        if row["to_state"] == GRADUATION_STATE_SEALED_SURVIVOR
    ]
    if already:
        return {"transition": TRANSITION_REPLAYED, "state": GRADUATION_STATE_SEALED_SURVIVOR, "row": dict(already[-1])}

    current_state = current_graduation_state(graduation_ledger, family_root_id)
    if current_state != GRADUATION_STATE_WALKFORWARD_SURVIVOR:
        raise GraduationTransitionRefusedError(
            family_root_id, GRADUATION_STATE_SEALED_SURVIVOR,
            f"family is at state {current_state!r}, not {GRADUATION_STATE_WALKFORWARD_SURVIVOR!r} "
            "-- refused (spec section 8): graduation states are strictly ordered, never skipped",
        )

    evaluations = [
        row for row in sealed_evaluations_for_family(graduation_ledger, family_root_id)
        if row.get("dataset_id") == dataset_id
    ]
    if not evaluations:
        raise GraduationTransitionRefusedError(
            family_root_id, GRADUATION_STATE_SEALED_SURVIVOR,
            f"no sealed-shard evaluation recorded for dataset_id {dataset_id!r} -- refused: "
            "record_sealed_evaluation must run first",
        )
    evaluation = evaluations[-1]
    if not evaluation["passed"]:
        raise GraduationTransitionRefusedError(
            family_root_id, GRADUATION_STATE_SEALED_SURVIVOR,
            f"the recorded sealed-shard evaluation for dataset_id {dataset_id!r} is a permanent "
            "FAILED verdict -- refused (spec section 7.4): a failed sealed verdict never advances "
            "and is never re-evaluated",
        )

    fields = {
        "row_kind": ROW_KIND_STATE_TRANSITION,
        "family_root_id": family_root_id,
        "dataset_id": dataset_id,
        "from_state": GRADUATION_STATE_WALKFORWARD_SURVIVOR,
        "to_state": GRADUATION_STATE_SEALED_SURVIVOR,
        "sealed_evaluation_row_hash": evaluation["row_hash"],
        "evaluated_at": evaluated_at if evaluated_at is not None else _iso_utc_now(),
    }
    row = graduation_ledger.append_row(fields)
    return {"transition": TRANSITION_APPENDED, "state": GRADUATION_STATE_SEALED_SURVIVOR, "row": row}


# === the export bundle (spec section 8 point 4, TC-3/TC-4/TC-6) =====================================


def _latest_timestamp(values: list[str | None]) -> str | None:
    present = [v for v in values if v]
    return max(present) if present else None  # ISO-8601 Z-suffixed strings sort chronologically


def _proposed_confirmation_boundary(fold_results: list[dict], sealed_evaluations: list[dict]) -> str | None:
    """A disclosed T-1 interpretation call: spec section 8 point 4 names "the proposed confirmation
    boundary" as a required bundle field without a formula. Read here as the LATEST instant this
    family's own ledgered evidence has already consumed -- the earliest a genuinely FRESH Referee
    registration could legitimately start counting new sessions from, since evidence at or before
    this instant has already been read by this candidate's own historical evaluation. Derived
    entirely from timestamps already ON the ledgered rows (Mode A's ``validation_revealed_at``, both
    modes' ``registered_at``, and every sealed evaluation's ``evaluated_at``) -- never a new,
    independently-tunable rule; honestly ``None`` when no evidence exists yet, never a fabricated
    date."""
    candidates: list[str | None] = []
    for fold in fold_results:
        candidates.append(fold.get("validation_revealed_at"))
        candidates.append(fold.get("registered_at"))
    for evaluation in sealed_evaluations:
        candidates.append(evaluation.get("evaluated_at"))
    return _latest_timestamp(candidates)


def build_export_bundle(
    graduation_ledger: GraduationLedger,
    scout_ledger: "ScoutLedger",
    wf_ledger: "wf.WalkForwardLedger",
    vault_shard_ledger: "vault.VaultShardLedger",
    vault_universe_ledger: "vault.VaultUniverseLedger",
    *,
    family_root_id: str,
    sequence_id: str | None = None,
) -> dict:
    """The provenance-complete bundle (spec section 8 point 4): buildable for ANY ledgered
    ``family_root_id`` at ANY current state (module docstring) -- the ``state`` field inside the
    return value, not a gate on whether this function may be called at all, is what distinguishes a
    validating ``referee_handoff_ready`` bundle from an honest partial one.

    - ``scout_trials``: EVERY row of ``scout_ledger.all_rows()`` whose OWN ``family_root_id`` field
      matches -- across every finer-grained ``family_id`` bucket that shares this coarser root
      (kills included, nothing filtered; union-N via ``scout_ledger.distinct_variant_count``, TC-3).
    - ``fold_results``: every ledgered fold for ``sequence_id`` (``walkforward.
      fold_results_for_sequence``), each already carrying its own ``evidence_class`` AND
      ``process_label`` verbatim -- empty when no ``sequence_id`` is supplied (a family with no
      walk-forward history yet still gets an honest partial bundle).
    - ``shards_touched``: every vault shard CURRENTLY bound to this ``family_root_id``, at whatever
      lifecycle stage it has reached (``vault.build_vault_state``, section 7.5's own per-stage
      reveal -- never a second projection of that data).
    - ``sealed_evaluations``: every sealed-shard verdict this module has itself recorded for this
      family, pass AND fail (TC-6's own "carried into its own bundle").
    - ``family_multiplicity``: sibling ``family_id``s sharing this root (from ``scout_trials``) and
      the family's complete prior sealed-verdict history (the SAME ``sealed_evaluations`` list,
      named again under this field per spec section 8 point 4's own phrasing)."""
    state = current_graduation_state(graduation_ledger, family_root_id)

    scout_trials = [row for row in scout_ledger.all_rows() if row.get("family_root_id") == family_root_id]
    union_n = distinct_variant_count(scout_trials)

    fold_results = wf.fold_results_for_sequence(wf_ledger, sequence_id) if sequence_id else []
    spec_hash = fold_results[0]["spec_hash"] if fold_results else None

    sealed_evaluations = sealed_evaluations_for_family(graduation_ledger, family_root_id)

    vault_state = vault.build_vault_state(vault_shard_ledger, vault_universe_ledger)
    shards_touched = [s for s in vault_state["shards"] if s.get("family_root_id") == family_root_id]

    sibling_family_ids = sorted({row["family_id"] for row in scout_trials if row.get("family_id")})

    return {
        "family_root_id": family_root_id,
        "state": state,
        "spec_hash": spec_hash,
        "union_n_variants_tried": union_n,
        "scout_trials": scout_trials,
        "fold_results": fold_results,
        "sealed_evaluations": sealed_evaluations,
        "shards_touched": shards_touched,
        "state_transitions": state_transitions_for_family(graduation_ledger, family_root_id),
        "proposed_confirmation_boundary": _proposed_confirmation_boundary(fold_results, sealed_evaluations),
        "family_multiplicity": {
            "sibling_family_ids": sibling_family_ids,
            "prior_sealed_verdicts": sealed_evaluations,
        },
        "referee_registration_note": REFEREE_FUTURE_REVISION_SENTENCE,
    }


_REQUIRED_BUNDLE_FIELDS = (
    "family_root_id", "state", "spec_hash", "union_n_variants_tried", "scout_trials", "fold_results",
    "sealed_evaluations", "shards_touched", "state_transitions", "proposed_confirmation_boundary",
    "family_multiplicity", "referee_registration_note",
)


def bundle_validates(bundle: dict) -> bool:
    """TC-3/TC-4: every required field is PRESENT (an honestly EMPTY list still validates; a
    MISSING key does not) and the disclaimer sentence is byte-exact."""
    if any(field not in bundle for field in _REQUIRED_BUNDLE_FIELDS):
        return False
    return bundle["referee_registration_note"] == REFEREE_FUTURE_REVISION_SENTENCE


# === state 4: sealed_survivor -> referee_handoff_ready (spec section 8 point 4, TC-3/TC-4) ==========


def evaluate_referee_handoff_ready_transition(
    graduation_ledger: GraduationLedger,
    scout_ledger: "ScoutLedger",
    wf_ledger: "wf.WalkForwardLedger",
    vault_shard_ledger: "vault.VaultShardLedger",
    vault_universe_ledger: "vault.VaultUniverseLedger",
    *,
    family_root_id: str,
    sequence_id: str,
    evaluated_at: str | None = None,
) -> dict:
    """Requires the family to already be ``sealed_survivor``. Builds the export bundle
    (``build_export_bundle``) and requires it to VALIDATE (``bundle_validates``) before recording
    the final transition -- "the export bundle exists and validates" IS state 4's own definition
    (spec section 8 point 4). Idempotent + identity-keyed exactly like the two transitions above;
    the returned bundle on replay is RE-BUILT live from the current ledgered facts (never a second,
    independently-stored copy -- the era's single-source-of-truth rail applies to this module's own
    served data just as much as to any other)."""
    already = [
        row for row in state_transitions_for_family(graduation_ledger, family_root_id)
        if row["to_state"] == GRADUATION_STATE_REFEREE_HANDOFF_READY
    ]
    if already:
        bundle = build_export_bundle(
            graduation_ledger, scout_ledger, wf_ledger, vault_shard_ledger, vault_universe_ledger,
            family_root_id=family_root_id, sequence_id=sequence_id,
        )
        return {"transition": TRANSITION_REPLAYED, "state": GRADUATION_STATE_REFEREE_HANDOFF_READY, "row": dict(already[-1]), "bundle": bundle}

    current_state = current_graduation_state(graduation_ledger, family_root_id)
    if current_state != GRADUATION_STATE_SEALED_SURVIVOR:
        raise GraduationTransitionRefusedError(
            family_root_id, GRADUATION_STATE_REFEREE_HANDOFF_READY,
            f"family is at state {current_state!r}, not {GRADUATION_STATE_SEALED_SURVIVOR!r} -- "
            "refused (spec section 8): graduation states are strictly ordered, never skipped",
        )

    bundle = build_export_bundle(
        graduation_ledger, scout_ledger, wf_ledger, vault_shard_ledger, vault_universe_ledger,
        family_root_id=family_root_id, sequence_id=sequence_id,
    )
    if not bundle_validates(bundle):
        raise GraduationTransitionRefusedError(
            family_root_id, GRADUATION_STATE_REFEREE_HANDOFF_READY,
            "the export bundle failed to validate -- refused (spec section 8 point 4): "
            "referee_handoff_ready requires a validating bundle",
        )

    fields = {
        "row_kind": ROW_KIND_STATE_TRANSITION,
        "family_root_id": family_root_id,
        "sequence_id": sequence_id,
        "from_state": GRADUATION_STATE_SEALED_SURVIVOR,
        "to_state": GRADUATION_STATE_REFEREE_HANDOFF_READY,
        "bundle_hash": _sha256(_canonical(bundle)),
        "evaluated_at": evaluated_at if evaluated_at is not None else _iso_utc_now(),
    }
    row = graduation_ledger.append_row(fields)
    return {"transition": TRANSITION_APPENDED, "state": GRADUATION_STATE_REFEREE_HANDOFF_READY, "row": row, "bundle": bundle}


# === GET /research/desk/micro/graduation (served verbatim, no second computation in the route) ======


def list_graduation_families(ledger: GraduationLedger) -> list[dict]:
    """``GET /research/desk/micro/graduation``'s whole body (minus the envelope): every
    ``family_root_id`` this module has EVER recorded anything for (at least one ``state_transition``
    OR ``sealed_evaluation`` row), each carrying its current state, its complete transition history,
    and its complete sealed-evaluation history -- append order, first-seen grouping (the
    ``scout.list_scout_families``/``walkforward.list_walkforward_sequences`` precedent). An empty
    list on a never-touched ledger is the honest, expected state this route serves at HTTP 200
    (TC-9) -- the caller (the route) attaches ``EMPTY_LEDGER_MESSAGE`` when it is empty."""
    order: list[str] = []
    seen: set[str] = set()
    for row in ledger.all_rows():
        family_root_id = row.get("family_root_id")
        if family_root_id and family_root_id not in seen:
            seen.add(family_root_id)
            order.append(family_root_id)
    families = []
    for family_root_id in order:
        families.append(
            {
                "family_root_id": family_root_id,
                "state": current_graduation_state(ledger, family_root_id),
                "transitions": state_transitions_for_family(ledger, family_root_id),
                "sealed_evaluations": sealed_evaluations_for_family(ledger, family_root_id),
            }
        )
    return families
