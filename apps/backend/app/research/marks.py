"""Action-mark + realized-R projection (J-52, data-contract rows 18 & 27) — the SINGLE source.

This is the ONE place the entry/exit marks and the realized move in R are computed. Both the
row-15 thesis projection (REST ``/research/thesis/active`` ≡ the WS ``thesis`` key) and
``GET /research/journal/{id}`` call THIS function, so the values are identical by construction
(no second computation path, no client-side arithmetic — the strip renders the result verbatim).

R semantics (per the goal doc glossary + the iter spec):
  * **R basis** ``R = |entry_price − invalidation_price|`` — present once an ENTRY mark exists.
  * **Realized move in R** — present ONLY once BOTH marks exist: the price change from entry to exit
    expressed in R units and SIGNED BY DIRECTION (a long that exited higher than entry is a positive
    realized move; a short that exited lower is positive). It is a journaled MEASUREMENT in R units
    only — never currency P&L, never a profit/loss claim (no-profitability anti-goal).
  * With no marks, the realized keys are ``None`` — NO realized metric is shown (no dishonest zero).
  * ``spread_at_mark`` is carried per mark verbatim (a recorded moment value; never recomputed).

A degenerate ``R == 0`` basis (entry exactly at invalidation — the API rejects a wrong-side
invalidation, but a mark recorded verbatim could still land there) yields a ``None`` realized move
rather than a divide-by-zero or a fabricated infinity — honest absence over a fabricated number.
"""

from __future__ import annotations

from .store import ActionRecord, ThesisRecord


def _mark_dict(record: ActionRecord) -> dict:
    """One mark, projected verbatim (price + logical/wall stamps + recorded moment spread)."""
    return {
        "kind": record.kind,
        "price": record.price,
        "logical_ts": record.logical_ts,
        "wall_ts": record.wall_ts,
        "spread_at_mark": record.spread_at_mark,
    }


def marks_projection(thesis: ThesisRecord, actions: list[ActionRecord]) -> dict:
    """The single, canonical marks + realized-R projection for a thesis (computed once).

    ``actions`` is the thesis's persisted action rows in insertion order. Returns a dict with:
      * ``entry`` / ``exit`` — the verbatim mark (or ``None`` if not recorded);
      * ``has_entry`` — the entry-marked fact the UI reads to WITHDRAW the Abandon control (it never
        guesses);
      * ``r_basis`` — ``|entry − invalidation|`` once an entry exists, else ``None``;
      * ``realized_r`` — the signed realized move in R once BOTH marks exist, else ``None``.
    The first ``entry`` / first ``exit`` win (one of each is enforced at the API; this is defensive).
    """
    entry = next((a for a in actions if a.kind == "entry"), None)
    exit_ = next((a for a in actions if a.kind == "exit"), None)

    r_basis: float | None = None
    realized_r: float | None = None
    if entry is not None:
        r_basis = abs(entry.price - thesis.invalidation_price)
        if exit_ is not None and r_basis > 0:
            # Price change from entry to exit, signed so a move in the thesis's FAVOR is positive
            # (long: exit above entry; short: exit below entry), expressed in R units.
            raw_move = exit_.price - entry.price
            directed = raw_move if thesis.direction == "long" else -raw_move
            realized_r = directed / r_basis

    return {
        "entry": _mark_dict(entry) if entry is not None else None,
        "exit": _mark_dict(exit_) if exit_ is not None else None,
        "has_entry": entry is not None,
        "r_basis": r_basis,
        "realized_r": realized_r,
    }
