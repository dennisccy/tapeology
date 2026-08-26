"""The Hypothesis Foundry -- the deterministic exhaust runner (spec §9). Orchestrates the pieces
built by the other four ``foundry_*.py`` modules over one hermetic manifest in canonical order:
Foundry family order, then variant ordinal within family (§9.1) -- never reordered by effect,
p-value, n, or a sibling's own verdict.

**Scope this iteration (goal-hypothesis-foundry-iter-2).** This module operates on hermetic
fixture epoch ids only (module docstring convention shared with every sibling ``foundry_*.py``
this iteration) -- there is no real freeze/manifest wiring yet, so the post-first-read-lock
science-hash verification this module will eventually need before EVERY resumed candidate
(``foundry_freeze.verify_freeze_set_unchanged``) is not yet called from here; that wiring is real-
epoch (J-06/J-07) territory. What IS in scope and proven here is the one identity this era's
hermetic runner already has something meaningful to verify on resume: the pinned intent row's own
economic-floor pin (§6/TC-51) -- see ``FoundryResumeIdentityMismatch`` below."""

from __future__ import annotations

import errno
import fcntl
from contextlib import contextmanager
from pathlib import Path
from typing import Sequence

from . import foundry_family as ffam
from . import foundry_interpreter as fi
from . import foundry_ledger as fl
from .foundry_compiler import CandidateSpec

__all__ = [
    "SCOUT_TO_FOUNDRY_STATE",
    "map_scout_decision",
    "FoundryResumeIdentityMismatch",
    "run_one_candidate",
    "run_family",
    "ConcurrentRunnerRefused",
    "SingleFlightLock",
]

# --- §7.2's mechanical, closed Scout-decision -> Foundry-state mapping (TC-17) --------------------
SCOUT_TO_FOUNDRY_STATE = {
    "killed_insufficient_n": "EVALUATED_INSUFFICIENT",
    "killed_null": "EVALUATED_KILLED",
    "killed_direction": "EVALUATED_KILLED",
    "killed_concentration": "EVALUATED_KILLED",
    "killed_economic": "EVALUATED_KILLED",
    "killed_fragile": "EVALUATED_KILLED",
    "survive": "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
}


def map_scout_decision(scout_decision: str) -> str:
    """§7.2: "there is no second Foundry verdict" -- a fixed, closed lookup; an unmapped Scout
    decision raises rather than silently defaulting to any of the three Foundry states."""
    try:
        return SCOUT_TO_FOUNDRY_STATE[scout_decision]
    except KeyError as exc:
        raise ValueError(
            f"Scout decision {scout_decision!r} has no Foundry mapping -- the closed vocabulary is "
            f"{sorted(SCOUT_TO_FOUNDRY_STATE)!r}"
        ) from exc


class FoundryResumeIdentityMismatch(Exception):
    """§6/TC-51: "any existing `EVALUATION_INTENT_RECORDED` row's numeric floor and provenance must
    equal a deterministic re-derivation from the same pinned eligible corpus before evaluation
    continues... A floor-input/output ordering or resume-consistency violation halts evaluation."
    Raised when a resumed candidate's caller-supplied ``econ_floor`` disagrees with the value
    already pinned on its own intent row."""


def run_one_candidate(
    spec: CandidateSpec, anchors: Sequence[fi.PopulationAnchor], *, ledger: fl.FoundryLedger,
    econ_floor: dict, manifest_hash: str, family: ffam.FoundryFamily,
) -> dict:
    """One candidate's full §9.2 resume-aware lifecycle:

    - already-terminal (a prior run, or THIS run's own already-appended row) -> verify identity and
      return the existing row WITHOUT re-executing the screen (TC-14's "verify and skip");
    - an intent row exists with no terminal result (a simulated crash) -> verify the intent row's
      own pinned econ-floor identity against what THIS invocation was given (halting on mismatch --
      TC-51), then deterministically re-execute the exact same screen and append exactly one
      terminal row (TC-15);
    - neither exists yet -> record the intent row (§6 step 4, BEFORE any outcome is measured),
      then execute and append the terminal row.

    Either way the interpreter (``foundry_interpreter.interpret_candidate``) is called with the
    SAME inputs every time -- deterministic re-execution, never a cached/memoized screen result --
    so a resumed candidate's terminal row is reproducible from the frozen CandidateSpec + anchors
    alone, exactly as §9.2 requires."""
    existing_terminal = ledger.terminal_row_for(spec.candidate_spec_hash)
    if existing_terminal is not None:
        return existing_terminal

    existing_intent = ledger.intent_row_for(spec.candidate_spec_hash)
    if existing_intent is not None:
        if existing_intent["econ_floor_bps"] != econ_floor.get("floor_bps"):
            raise FoundryResumeIdentityMismatch(
                f"resume econ_floor_bps mismatch for candidate_spec_hash="
                f"{spec.candidate_spec_hash!r}: pinned intent={existing_intent['econ_floor_bps']!r}, "
                f"resumed with={econ_floor.get('floor_bps')!r}"
            )
    else:
        ledger.record_intent(
            candidate_spec_hash=spec.candidate_spec_hash, manifest_hash=manifest_hash,
            econ_floor_bps=econ_floor.get("floor_bps"), econ_floor_provenance=econ_floor.get("rule"),
        )

    interpretation = fi.interpret_candidate(
        spec, anchors, econ_floor=econ_floor, family_id=family.foundry_family_id,
        n_variants_tried=ffam.n_variants_tried_for(family),
    )
    foundry_state = map_scout_decision(interpretation.screen["decision"])
    rule_id = fl.deterministic_rule_id(spec.epoch_id, spec.candidate_spec_hash)
    root_status = fl.prospective_root_status(spec)

    return ledger.record_terminal(
        candidate_spec_hash=spec.candidate_spec_hash, manifest_hash=manifest_hash,
        foundry_family_id=family.foundry_family_id,
        foundry_family_variant_count=ffam.n_variants_tried_for(family),
        screen_result=interpretation.screen, rule_id=rule_id, prospective_root_status=root_status,
        foundry_state=foundry_state,
    )


def run_family(
    family: ffam.FoundryFamily, variants: Sequence[tuple[CandidateSpec, Sequence[fi.PopulationAnchor]]],
    *, ledger: fl.FoundryLedger, econ_floor: dict, manifest_hash: str,
) -> list[dict]:
    """§9.1: visits every ``variants`` entry in the ORDER GIVEN (the caller's own manifest-order
    sequence -- family order, then variant ordinal within family) with a plain, unconditional
    for-loop. There is no sort/rank/filter anywhere in this function keyed on effect, p-value, n,
    or a sibling's own verdict -- canonical-order invariance (TC-16) holds structurally, not by
    convention. A blocked family (``family.blocked``) has no eligible ordinals
    (``foundry_family.eligible_variant_ordinals``); this function still executes whatever
    ``variants`` it is given (the CALLER -- the real J-06/J-07 manifest walker -- is responsible
    for never including a blocked family's variants in that sequence at all)."""
    return [
        run_one_candidate(spec, anchors, ledger=ledger, econ_floor=econ_floor, manifest_hash=manifest_hash, family=family)
        for spec, anchors in variants
    ]


# === §9's single-flight protection: "Goal Mode may invoke the CLI repeatedly across iterations; it
# must never depend on one long-held agent turn staying alive for the full epoch" -- but exactly
# ONE runner may hold the epoch at a time. ==========================================================


class ConcurrentRunnerRefused(Exception):
    """§9.2: "concurrent second runner -> single-flight refusal" (TC-14)."""


class SingleFlightLock:
    """A real, OS-enforced exclusive lock (``fcntl.flock``, non-blocking) over one lock file --
    never a hand-rolled PID-file/mutex (those race; ``flock`` does not). Two different
    ``SingleFlightLock`` instances (or two different processes) pointed at the SAME path can never
    both hold the lock at once; a released lock (the context manager's own ``__exit__``) is
    immediately available to the next acquirer -- a sequential second acquire is not "concurrent"
    and always succeeds."""

    def __init__(self, lock_path: str | Path) -> None:
        self._path = Path(lock_path)

    @contextmanager
    def acquire(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(self._path, "w")
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            fh.close()
            if exc.errno in (errno.EACCES, errno.EAGAIN):
                raise ConcurrentRunnerRefused(
                    f"another Foundry runner already holds the single-flight lock at {self._path}"
                ) from exc
            raise
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            fh.close()
