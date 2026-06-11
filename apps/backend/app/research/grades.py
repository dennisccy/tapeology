"""Outcome × process grades (capability 29, J-56) — the SINGLE-owner pure functions.

This is the ONE place the two review grades are computed. Every terminal-resolution code path (the
user ``POST /research/thesis/{id}/resolve``, the system invalidation auto-resolve, the stream-end /
stop expiry, and the restart-expiry sweep) calls THIS once at the defining moment — right AFTER the
execution checks are persisted — and stores the result on the thesis row (schema v6). The journal
surfaces serve the persisted result VERBATIM; nothing is recomputed at read.

Both axes are ENUM LABELS with plain-language evidence — NEVER a numeric score (the no-numeric-score
anti-goal):

  * **outcome** ∈ ``thesis_held | thesis_failed | no_read`` — 1:1 from the resolution via the
    config-owned ``process_outcome_grade_map`` (goal.md capability 29). A fixed mapping, never a
    judgement: ``played_out → thesis_held``, ``invalidated → thesis_failed``,
    ``expired``/``abandoned → no_read``.
  * **process** ∈ ``clean | flagged | violated`` — a config-owned RULE over the named,
    evidence-backed checks (the FROZEN entry risk flags + the persisted execution checks). The worst
    named finding wins: a FAILED execution check (grounded in the user's OWN recorded marks)
    ``violates``; an entry risk flag that fired at declaration (advisory) ``flags``; neither is
    ``clean``. CRITICALLY — **being invalidated is never by itself a process failure** (the system
    enforces invalidation): an invalidated thesis with no failed execution check and no fired risk
    flag grades ``clean``. The grade is evidence-backed: it names exactly which checks / flags drove
    it (no-naked-outputs).

The grade thresholds (how many failed checks ``violate``, how many fired flags ``flag``) are
config-owned (``process_violated_min_failed_checks`` / ``process_flagged_min_risk_flags``) — no
literal lives here.
"""

from __future__ import annotations

from ..config import Config
from .store import ThesisRecord

# The grade enum ids (display copy lives in the taxonomy — the frontend hardcodes none of them).
OUTCOME_GRADES: tuple[str, ...] = ("thesis_held", "thesis_failed", "no_read")
PROCESS_GRADES: tuple[str, ...] = ("clean", "flagged", "violated")

_FAILED = "failed"  # the execution-check status that grounds a process violation


def _compute_outcome(resolution: str, config: Config) -> str:
    """The outcome grade — 1:1 from the resolution via the config-owned map (never a judgement).

    A resolution outside the map (which should never happen — the four terminal statuses are the
    only resolutions) yields ``no_read`` honestly rather than a fabricated outcome."""
    return config.process_outcome_grade_map.get(resolution, "no_read")


def _named_findings(thesis: ThesisRecord) -> tuple[list[str], list[str]]:
    """The named findings the process rule weighs, read VERBATIM from the persisted record:

      * the FAILED execution checks (by check name) — grounded in the user's OWN recorded marks;
      * the fired entry risk flags (by flag id) — advisory, frozen at declaration.

    Honest absence: a thesis with no computed execution checks contributes no failed checks; one
    never risk-assessed (``risk_flags`` ``None``) contributes no fired flags. Neither is fabricated.
    """
    failed_checks: list[str] = []
    if thesis.execution_checks is not None:
        for check in thesis.execution_checks.get("checks", []):
            if check.get("status") == _FAILED:
                failed_checks.append(check.get("check", "unknown_check"))
    fired_flags: list[str] = []
    if thesis.risk_flags:  # None (never assessed) or [] (nothing fired) -> no fired flags
        fired_flags = [f.get("flag", "unknown_flag") for f in thesis.risk_flags]
    return failed_checks, fired_flags


def _process_evidence(grade: str, failed_checks: list[str], fired_flags: list[str]) -> str:
    """Plain-language evidence naming the checks/flags that drove the process grade (no naked grade).

    Present-tense, descriptive, thesis-attributed (J-66) — never imperative/predictive, never a
    numeric score. Names the SPECIFIC findings so the grade is auditable."""
    def _names(ids: list[str]) -> str:
        return ", ".join(i.replace("_", " ") for i in ids)

    if grade == "violated":
        return (
            f"Your own execution checks flagged: {_names(failed_checks)}. "
            "A process violation reflects what you did — being invalidated is never itself a "
            "process failure."
        )
    if grade == "flagged":
        return (
            f"No execution check failed, but entry risk flags fired at declaration: "
            f"{_names(fired_flags)}. The entry carried advisories you declared into."
        )
    # clean
    return (
        "No execution check failed and no entry risk flag fired — the process was clean. "
        "Being invalidated is never itself a process failure."
    )


def _compute_process(thesis: ThesisRecord, config: Config) -> tuple[str, str]:
    """The process grade + its evidence (the config-owned rule over the named checks).

    Worst named finding wins: a FAILED execution check ``violates``; else a fired entry risk flag
    ``flags``; else ``clean``. Invalidation alone never grades a failure (the system enforces it —
    it is recorded as the outcome ``thesis_failed``, never re-counted as a process fault)."""
    failed_checks, fired_flags = _named_findings(thesis)
    if len(failed_checks) >= config.process_violated_min_failed_checks:
        grade = "violated"
    elif len(fired_flags) >= config.process_flagged_min_risk_flags:
        grade = "flagged"
    else:
        grade = "clean"
    return grade, _process_evidence(grade, failed_checks, fired_flags)


def compute_grades(thesis: ThesisRecord, resolution: str, *, config: Config) -> dict:
    """Compute the outcome × process grades ONCE at terminal resolution (capability 29, J-56).

    PURE: derives both from the (already-persisted at this point) execution checks + the FROZEN entry
    risk flags + the resolution + ``config`` — no engine, no live snapshot. Returns::

        {
          "outcome": "thesis_held" | "thesis_failed" | "no_read",
          "process": "clean" | "flagged" | "violated",
          "process_evidence": "<plain-language sentence naming the checks/flags that drove it>",
        }

    Both axes are ENUM labels — NEVER a numeric score. The display copy for the labels comes from the
    taxonomy (the frontend hardcodes none); ``process_evidence`` is the no-naked-outputs evidence
    naming the specific named findings.
    """
    outcome = _compute_outcome(resolution, config)
    process, process_evidence = _compute_process(thesis, config)
    return {
        "outcome": outcome,
        "process": process,
        "process_evidence": process_evidence,
    }


def compute_and_persist_grades(store, thesis_id: str, resolution: str, config: Config) -> dict | None:
    """Compute the grades for a just-resolved thesis ONCE and persist them on the thesis row.

    Called by every terminal-resolution path right AFTER the execution checks are persisted (the
    process rule weighs those checks), so the grades are computed and stored exactly ONCE at the
    defining moment — never recomputed at read. Reads the thesis BACK from the store (so it picks up
    the just-persisted ``execution_checks``), runs the pure :func:`compute_grades`, and persists via
    ``store.set_grades``. Returns the computed result (or ``None`` if the thesis is gone). Idempotent
    guard: if the thesis already carries grades (a double-resolve race), it is NOT recomputed — the
    first computation stands (append-only spirit)."""
    thesis = store.get_thesis(thesis_id)
    if thesis is None:
        return None
    if thesis.grades is not None:
        return thesis.grades
    result = compute_grades(thesis, resolution, config=config)
    store.set_grades(thesis_id, result)
    return result
