"""Machine-derived execution checks (capability 27, J-54) — the SINGLE-owner pure function.

This is the ONE place the four named execution checks are computed. Every terminal-resolution code
path (the user ``POST /research/thesis/{id}/resolve``, the system invalidation auto-resolve, the
stream-end / stop expiry, and the restart-expiry sweep) calls THIS function exactly ONCE at the
defining moment and persists the result on the thesis row (schema v5). The journal-detail endpoint
serves the persisted result VERBATIM — nothing is recomputed at read (single-source-of-truth + the
data-contract row-19 execution-checks half).

The four checks (capability 27 / goal.md), computed from the recorded action marks + the append-only
verdict timeline + the FROZEN thesis fields ONLY (no engine, no live snapshot — deterministic):

  * ``entered_before_confirmation`` — the entry mark's logical_ts precedes the FIRST published
    ``confirming`` event (or no ``confirming`` was ever published while entry-marked).
  * ``chased_entry`` — the entry price is beyond the recorded ``rule_first_true_price`` + the
    config-owned chase return threshold, direction-aware. The chase check anchors at the recorded
    ``rule_first_true`` price (the first logical instant the raw confirming rule held), NEVER the
    post-dwell publish price (per the Constraints) — reusing the existing ``chase_return_threshold``
    config seam (no new magic number).
  * ``exited_beyond_invalidation`` — the exit mark is recorded beyond the declared invalidation in
    the adverse direction (the user held through the stop).
  * ``cut_confirming_early`` — the exit was recorded while the latest published verdict was
    ``confirming`` (before any weakening / rejecting / invalidation).

Each check yields an ENUM status — ``failed | passed | not_applicable`` (labels, NEVER a numeric
score) — plus plain-language evidence quoting the measured values (timestamps, prices, thresholds).
With no marks the mark-dependent checks read an explicit ``not_applicable`` (never a fabricated
pass/fail). The backend-owned check → suggested-mistake-tag mapping (taxonomy ``CHECK_SUGGESTED_TAG``)
derives the suggested tags for the FAILED checks — the system SUGGESTS only; it never records a
confirmed tag.
"""

from __future__ import annotations

from ..config import Config
from .store import ActionRecord, JournalStore, ThesisRecord, VerdictEventRecord
from .taxonomy import suggested_tag_for_check

# The four checks, in a stable display/order — the result list is built in this order so the served
# payload and every test are deterministic.
CHECK_NAMES: tuple[str, ...] = (
    "entered_before_confirmation",
    "chased_entry",
    "exited_beyond_invalidation",
    "cut_confirming_early",
)

# Enum statuses (labels, never numeric scores).
_FAILED = "failed"
_PASSED = "passed"
_NOT_APPLICABLE = "not_applicable"


def _price(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def _ts(value: float | None) -> str:
    # Logical seconds, one decimal place — quotes the measured logical instant honestly (e.g.
    # "14.0s"). The journal detail renders the same timeline in TRUE clock time from the persisted
    # wall_ts; this evidence string names the logical instant the check measured.
    return "n/a" if value is None else f"{value:.1f}s"


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _first(actions: list[ActionRecord], kind: str) -> ActionRecord | None:
    return next((a for a in actions if a.kind == kind), None)


def _first_confirming(timeline: list[VerdictEventRecord]) -> VerdictEventRecord | None:
    """The FIRST published ``confirming`` event in the append-only timeline (insertion order)."""
    return next((e for e in timeline if e.verdict == "confirming"), None)


def _check(name: str, status: str, evidence: str) -> dict:
    """One execution-check result row — status is an ENUM label, never a numeric score."""
    return {"check": name, "status": status, "evidence": evidence}


# --- the four checks ------------------------------------------------------------------------------

def _entered_before_confirmation(
    thesis: ThesisRecord,
    entry: ActionRecord | None,
    first_confirming: VerdictEventRecord | None,
) -> dict:
    name = "entered_before_confirmation"
    if entry is None:
        return _check(
            name,
            _NOT_APPLICABLE,
            "No entry was recorded, so whether the entry preceded confirmation cannot be checked.",
        )
    if first_confirming is None:
        return _check(
            name,
            _FAILED,
            f"You recorded an entry at {_ts(entry.logical_ts)}, but the thesis never published a "
            f"confirming verdict while you held it.",
        )
    if entry.logical_ts < first_confirming.logical_ts:
        return _check(
            name,
            _FAILED,
            f"Your entry at {_ts(entry.logical_ts)} precedes the first confirming verdict published "
            f"at {_ts(first_confirming.logical_ts)} — you entered before the tape confirmed your "
            f"thesis.",
        )
    return _check(
        name,
        _PASSED,
        f"Your entry at {_ts(entry.logical_ts)} came after the first confirming verdict published "
        f"at {_ts(first_confirming.logical_ts)}.",
    )


def _chased_entry(
    thesis: ThesisRecord,
    entry: ActionRecord | None,
    first_confirming: VerdictEventRecord | None,
    config: Config,
) -> dict:
    name = "chased_entry"
    if entry is None:
        return _check(
            name,
            _NOT_APPLICABLE,
            "No entry was recorded, so whether the entry chased an extended move cannot be checked.",
        )
    # Anchor at the recorded ``rule_first_true`` price — the first logical instant the raw confirming
    # rule held — NEVER the post-dwell publish price (per the Constraints). Without that anchor the
    # check cannot be measured (a fabricated pass/fail would be dishonest).
    anchor = first_confirming.rule_first_true_price if first_confirming is not None else None
    if anchor is None:
        return _check(
            name,
            _NOT_APPLICABLE,
            "No first-confirmation anchor price was recorded, so whether the entry chased an "
            "extended move cannot be measured.",
        )
    threshold = config.chase_return_threshold
    if thesis.direction == "long":
        # A long chases when it enters ABOVE the anchor by more than the chase return.
        band = anchor * (1.0 + threshold)
        chased = entry.price > band
        side = "above"
    else:
        # A short chases when it enters BELOW the anchor by more than the chase return (the move has
        # already fallen).
        band = anchor * (1.0 - threshold)
        chased = entry.price < band
        side = "below"
    move_return = abs(entry.price - anchor) / anchor if anchor else 0.0
    if chased:
        return _check(
            name,
            _FAILED,
            f"Your entry at {_price(entry.price)} is {side} the first-confirmation price "
            f"{_price(anchor)} by {_pct(move_return)}, past the {_pct(threshold)} chase threshold — "
            f"the move had already run before you entered.",
        )
    return _check(
        name,
        _PASSED,
        f"Your entry at {_price(entry.price)} is within {_pct(threshold)} of the first-confirmation "
        f"price {_price(anchor)} ({_pct(move_return)} away) — you did not chase an extended move.",
    )


def _exited_beyond_invalidation(
    thesis: ThesisRecord,
    exit_: ActionRecord | None,
) -> dict:
    name = "exited_beyond_invalidation"
    if exit_ is None:
        return _check(
            name,
            _NOT_APPLICABLE,
            "No exit was recorded, so whether the exit was beyond your invalidation cannot be checked.",
        )
    inval = thesis.invalidation_price
    if thesis.direction == "long":
        beyond = exit_.price <= inval  # a long is invalidated at/below the invalidation
        side = "at or below"
    else:
        beyond = exit_.price >= inval  # a short is invalidated at/above the invalidation
        side = "at or above"
    if beyond:
        return _check(
            name,
            _FAILED,
            f"Your exit at {_price(exit_.price)} is {side} your invalidation at {_price(inval)} — "
            f"you held through the stop.",
        )
    return _check(
        name,
        _PASSED,
        f"Your exit at {_price(exit_.price)} is on the right side of your invalidation at "
        f"{_price(inval)} — you did not hold through the stop.",
    )


def _cut_confirming_early(
    thesis: ThesisRecord,
    exit_: ActionRecord | None,
    timeline: list[VerdictEventRecord],
) -> dict:
    name = "cut_confirming_early"
    if exit_ is None:
        return _check(
            name,
            _NOT_APPLICABLE,
            "No exit was recorded, so whether a confirming thesis was cut early cannot be checked.",
        )
    # The latest PUBLISHED verdict at the exit's logical_ts: the last timeline row whose logical_ts is
    # at or before the exit (the append-only timeline is in insertion = logical order). A verdict
    # describes the tape at its logical instant; the exit is judged against the verdict in effect then.
    latest_verdict: str | None = None
    latest_ts: float | None = None
    for e in timeline:
        if e.logical_ts <= exit_.logical_ts and e.verdict in (
            "pending",
            "confirming",
            "weakening",
            "rejecting",
            "invalidated",
        ):
            latest_verdict = e.verdict
            latest_ts = e.logical_ts
    if latest_verdict == "confirming":
        return _check(
            name,
            _FAILED,
            f"Your exit at {_ts(exit_.logical_ts)} came while the latest published verdict was "
            f"confirming (published at {_ts(latest_ts)}) — you cut a confirming thesis early, "
            f"before it weakened or rejected.",
        )
    return _check(
        name,
        _PASSED,
        f"Your exit at {_ts(exit_.logical_ts)} came while the latest published verdict was "
        f"{latest_verdict or 'pending'} — you did not cut a confirming thesis early.",
    )


def compute_execution_checks(
    thesis: ThesisRecord,
    *,
    actions: list[ActionRecord],
    timeline: list[VerdictEventRecord],
    config: Config,
) -> dict:
    """Compute the four named execution checks ONCE at terminal resolution (capability 27, J-54).

    PURE: derives everything from the persisted ``actions`` (in insertion order), the append-only
    ``timeline`` (in insertion = logical order), and the FROZEN ``thesis`` fields + ``config`` — no
    engine, no live snapshot. Returns ``{"checks": [...], "suggested_mistake_tags": [...]}``:
      * ``checks`` — one row per check (in ``CHECK_NAMES`` order), each ``{check, status, evidence}``
        with an ENUM status (``failed | passed | not_applicable`` — never a numeric score) and
        plain-language evidence quoting the measured values;
      * ``suggested_mistake_tags`` — the backend-owned tags for the FAILED checks (taxonomy
        ``CHECK_SUGGESTED_TAG``), de-duplicated and in ``CHECK_NAMES`` order. The system SUGGESTS
        only; the user confirms tags in the review flow (J-57).
    """
    entry = _first(actions, "entry")
    exit_ = _first(actions, "exit")
    first_confirming = _first_confirming(timeline)

    checks = [
        _entered_before_confirmation(thesis, entry, first_confirming),
        _chased_entry(thesis, entry, first_confirming, config),
        _exited_beyond_invalidation(thesis, exit_),
        _cut_confirming_early(thesis, exit_, timeline),
    ]

    # Suggested tags for the FAILED checks only — deduplicated, in CHECK_NAMES order.
    suggested: list[str] = []
    for check in checks:
        if check["status"] != _FAILED:
            continue
        tag = suggested_tag_for_check(check["check"])
        if tag is not None and tag not in suggested:
            suggested.append(tag)

    return {"checks": checks, "suggested_mistake_tags": suggested}


def compute_and_persist_execution_checks(
    store: JournalStore, thesis_id: str, config: Config
) -> dict | None:
    """Compute the execution checks for a just-resolved thesis from the store ONCE and persist them.

    The single entry point every terminal-resolution code path calls (user resolve, system
    invalidation, stream-end / stop expiry, restart-expiry sweep) right AFTER the thesis status is
    flipped: it reads the thesis + its recorded marks + its append-only timeline back from the store,
    runs the pure :func:`compute_execution_checks`, and persists the result on the thesis row via
    ``store.set_execution_checks`` — so the checks are computed and stored exactly ONCE at the
    defining moment, never recomputed at read. Returns the computed result (or ``None`` if the thesis
    is gone). Idempotent guard: if the thesis already carries execution_checks (a double-resolve
    race), it is NOT recomputed — the first computation stands (append-only spirit)."""
    thesis = store.get_thesis(thesis_id)
    if thesis is None:
        return None
    if thesis.execution_checks is not None:
        return thesis.execution_checks
    result = compute_execution_checks(
        thesis,
        actions=store.get_actions(thesis_id),
        timeline=store.verdict_events(thesis_id),
        config=config,
    )
    store.set_execution_checks(thesis_id, result)
    return result
