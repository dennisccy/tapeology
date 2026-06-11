"""Journal-row projection (J-51, data-contract row 21 — journal-rows half) — the SINGLE source.

This is the ONE place a compact journal-list row is built from a persisted thesis record. The list
endpoint ``GET /research/journal`` is the ONLY serving path for these rows (no second endpoint, no
second computation). Mirrors ``marks.py``'s single-owner discipline: every value is a VERBATIM read
of an already-persisted record — id, ticker, bound source, ``data_feed``, ``config_fingerprint``,
setup, direction, declared logical + wall timestamps, status, the resolution (the terminal status,
or ``None`` while active), the VERBATIM persisted expired/interruption reason, and entry/exit-mark
presence. NOTHING is recomputed at read: the resolution reason is the literal ``evidence`` string the
verdict engine / lifecycle sweep already wrote to the terminal timeline event; mark presence is the
persisted action fact, never inferred from a price.

Grade / reviewed fields (data-contract row 21 — the pre-announced additive keys, J-56/J-57): the
``grades`` object is added VERBATIM as a row key ONLY once it has been computed at resolution (a
pre-grade row OMITS it — honest omission, never a dishonest placeholder); ``reviewed`` is ALWAYS
present (a boolean fact — ``False`` until the user saves a review). Both are reads of the persisted
record — never recomputed at read.
"""

from __future__ import annotations

from .store import ThesisRecord

# The terminal statuses that count as a RESOLUTION (a resolution IS the thesis's terminal status).
# An ``active`` thesis has no resolution — the row reports ``resolution: None`` (honest absence).
_TERMINAL_STATUSES = ("played_out", "abandoned", "invalidated", "expired")


def journal_row(
    thesis: ThesisRecord,
    *,
    resolution_reason: str | None,
    has_entry: bool,
    has_exit: bool,
) -> dict:
    """The single, canonical compact journal-list row for one persisted thesis (computed once).

    Args (all read VERBATIM from already-persisted records — never recomputed):
      * ``thesis`` — the persisted ``theses`` row.
      * ``resolution_reason`` — the verbatim ``evidence`` of the thesis's terminal verdict event (the
        persisted expired/interruption/resolution reason), or ``None`` while the thesis is active. The
        caller reads it from the append-only timeline; this function never derives it.
      * ``has_entry`` / ``has_exit`` — the persisted action-mark presence facts (never inferred).

    ``resolution`` is the terminal status (or ``None`` while active) — the same string as ``status``
    once terminal, surfaced under its own key so the frontend reads a resolution explicitly rather
    than inferring one from the status."""
    is_terminal = thesis.status in _TERMINAL_STATUSES
    row = {
        "id": thesis.id,
        "ticker": thesis.ticker,
        "bound_source": thesis.bound_source,
        "data_feed": thesis.data_feed,
        "config_fingerprint": thesis.config_fingerprint,
        "setup_type": thesis.setup_type,
        "direction": thesis.direction,
        "created_logical_ts": thesis.created_logical_ts,
        "created_wall_ts": thesis.created_wall_ts,
        "status": thesis.status,
        # A resolution IS the terminal status; ``None`` while active (honest absence, never fabricated).
        "resolution": thesis.status if is_terminal else None,
        # The VERBATIM persisted reason (terminal-event evidence) — never recomputed at read.
        "resolution_reason": resolution_reason if is_terminal else None,
        # Mark presence — the persisted action fact the UI reads (never inferred from a price).
        "has_entry": has_entry,
        "has_exit": has_exit,
        # The user-confirmed-review fact (J-57, data-contract row 21) — ALWAYS present (a boolean: a
        # pre-review row reads ``False``, never absent — it is a definite fact, not a computed value).
        "reviewed": thesis.reviewed,
    }
    # The outcome × process grades (J-56, data-contract row 21) — added VERBATIM ONLY once computed at
    # resolution (a pre-grade row OMITS the key entirely — honest omission, never a fabricated grade).
    if thesis.grades is not None:
        row["grades"] = thesis.grades
    return row
