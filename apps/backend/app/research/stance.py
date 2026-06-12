"""The management-stance evaluator (data-contract row 25, stance half; capability 27 / J-53).

While the user HOLDS a journaled position (an entry-marked, unresolved thesis), the thesis strip
answers one question — *does the tape still support this position?* — with the **management stance**:

  * ``thesis_intact``       — the latest published verdict is ``confirming``;
  * ``thesis_weakening``    — the latest published verdict shows the position is NOT confirmed
                              (``weakening`` / ``rejecting``, or still ``pending`` after the entry —
                              the honest J-54 case: an entry while pending NEVER reads intact);
  * ``thesis_invalidated``  — the verdict resolved ``invalidated`` (the J-44 auto-resolve) — a
                              TERMINAL, dwell-exempt display treatment.

DISCIPLINE (the iter-20 spec + the goal anti-goals):
  * **Pure derivation, never a record.** The stance is derived EXCLUSIVELY from the latest row-16
    PUBLISHED verdict — it composes NO new indicator, reads NO engine/feature state directly, and is
    NEVER persisted (schema stays v7). The research layer stays read-only over the engine.
  * **No naked stance.** Every stance carries plain-language EVIDENCE. For ``thesis_intact`` /
    ``thesis_weakening`` the evidence is the published verdict's own evidence (already
    thesis-attributed, present-tense, descriptive); for the honest ``pending`` case it names the
    actual verdict ("the tape has not confirmed your thesis since you marked entry"); for
    ``thesis_invalidated`` it is the offending-print facts the verdict engine recorded.
  * **Its own dwell, ``invalidated`` dwell-exempt.** The stance publishes through a config-owned,
    LOGICAL-time dwell (``management_stance_dwell_seconds``) so a single flickering verdict tick never
    flaps the stance — EXCEPT ``thesis_invalidated``, which is dwell-exempt (it mirrors the hard,
    dwell-exempt invalidation trigger and is terminal). The dwell is a derivation-timing concern only;
    the stance is never stored, so the dwell state lives in memory on the monitor.
  * **Never imperative, never predictive.** Present-tense, factual, thesis-attributed copy — it
    describes what the tape is doing NOW relative to the declared thesis, never a forecast and never
    a buy/sell/enter/exit command. The "Descriptive only — not trading advice" register extends here.

The LIVE position readouts that travel WITH the stance (``distance_to_invalidation`` in $ and R, and
``open_r``) are computed by :func:`compute_position_readouts` from the SAME single ``r_basis()`` helper
in ``marks.py`` (data-contract row 27) — the stance is its FIFTH registered consumer, never a second
R formula. ``open_r`` is the current open move in R, SIGNED BY DIRECTION with the SAME convention as
``marks.py``'s realized move (a move in the thesis's favor is positive).
"""

from __future__ import annotations

from .marks import r_basis
from .taxonomy import (
    STANCE_PENDING_EVIDENCE,
    stance_for_verdict,
)

# The published-verdict -> management-stance map (the backend-owned table the spec mandates). The
# FULL five-verdict mapping lives in ``taxonomy.stance_for_verdict`` (the single copy owner); this
# module reads it so the mapping + its display copy have ONE home. ``expired`` never reaches the
# stance (an expired thesis is unmarked or survives not-evaluated — the stance keys are absent then).


class StanceEvaluator:
    """Holds one entry-marked thesis's PUBLISHED management stance and advances it per event (no I/O).

    Constructed when the monitor holds a thesis; advanced in ``on_event`` AFTER the verdict step so it
    reads the just-published verdict for this snapshot. Owns: the currently published stance, and the
    dwell tracker (which raw stance is accumulating + the first logical instant it began). Performs NO
    persistence and reads NOTHING but the published verdict + the snapshot's logical timestamp it is
    handed — so the engine stays byte-identical with it attached (equivalence anti-goal).

    The stance only MATTERS once an entry mark exists, but the dwell accumulates from the verdict
    regardless, so by the time the user marks entry the stance is already settled (no artificial
    "warm-up" gap at the mark). Whether the stance/readout keys are actually SERVED is gated separately
    in ``build_projection`` (entry-marked AND unresolved AND a live monitor).
    """

    def __init__(self, dwell_seconds: float) -> None:
        self._dwell = float(dwell_seconds)
        # Published stance state. Starts at the pending reading (no published confirmation yet) — an
        # entry while pending never reads ``thesis_intact`` by construction.
        self._published: str = "thesis_weakening"
        self._published_evidence: str = STANCE_PENDING_EVIDENCE
        self._terminal = False  # thesis_invalidated => frozen terminal stance
        # Dwell tracker: which raw stance is currently accumulating and the first logical instant it
        # held. Seeded ``None`` so the first event starts the dwell clock.
        self._pending_raw: str | None = None
        self._raw_first_ts: float | None = None

    @property
    def published_stance(self) -> str:
        return self._published

    @property
    def published_evidence(self) -> str:
        return self._published_evidence

    def advance(
        self,
        *,
        verdict: str,
        verdict_evidence: str,
        logical_ts: float,
        invalidation_evidence: str | None = None,
    ) -> None:
        """Advance the published stance against the latest published verdict for this event.

        ``verdict`` is the monitor's CURRENT published verdict (already dwell-gated by the verdict
        engine); ``verdict_evidence`` is that verdict's plain-language evidence (carried verbatim onto
        the stance — no naked stance). ``logical_ts`` is the snapshot's logical timestamp (the dwell is
        logical-time). ``invalidation_evidence`` overrides the evidence on the terminal invalidated
        stance (the offending-print facts the verdict engine recorded), when available.

        Publication rule: the raw stance derived from the verdict must hold CONTINUOUSLY for the dwell
        before it is published — EXCEPT ``thesis_invalidated``, which publishes IMMEDIATELY (dwell-exempt)
        and freezes the stance terminal.
        """
        if self._terminal:
            return

        raw_stance = stance_for_verdict(verdict)
        raw_evidence = self._evidence_for(raw_stance, verdict, verdict_evidence, invalidation_evidence)

        # thesis_invalidated is dwell-exempt + terminal — publish immediately, freeze.
        if raw_stance == "thesis_invalidated":
            self._published = raw_stance
            self._published_evidence = raw_evidence
            self._terminal = True
            return

        # Dwell tracking for the non-terminal stances: reset the clock whenever the raw stance changes,
        # so a transition publishes only after the raw stance has held continuously for the dwell.
        if raw_stance != self._pending_raw:
            self._pending_raw = raw_stance
            self._raw_first_ts = logical_ts

        held_for = logical_ts - (self._raw_first_ts if self._raw_first_ts is not None else logical_ts)
        dwell_elapsed = held_for >= self._dwell

        if raw_stance == self._published:
            # Same stance — keep the evidence current (the verdict evidence may refresh) without a flap.
            self._published_evidence = raw_evidence
            return
        if dwell_elapsed:
            self._published = raw_stance
            self._published_evidence = raw_evidence

    @staticmethod
    def _evidence_for(
        raw_stance: str,
        verdict: str,
        verdict_evidence: str,
        invalidation_evidence: str | None,
    ) -> str:
        """The plain-language evidence carried on a raw stance (no naked stance).

        ``thesis_intact`` / ``thesis_weakening`` carry the published verdict's OWN evidence verbatim
        (already descriptive + thesis-attributed). The honest ``pending`` case (an entry while pending —
        no published confirmation) reads its OWN explicit copy naming the actual verdict, never the
        seeded pending placeholder. ``thesis_invalidated`` carries the offending-print evidence the
        verdict engine recorded when available, else the published verdict evidence.
        """
        if raw_stance == "thesis_invalidated":
            return invalidation_evidence or verdict_evidence or STANCE_PENDING_EVIDENCE
        if verdict == "pending" or not verdict_evidence:
            # Entry while pending: the tape has not confirmed the thesis since the mark — name it
            # honestly rather than read as "weakening from a confirmation that never happened".
            return STANCE_PENDING_EVIDENCE
        return verdict_evidence


def compute_position_readouts(
    *,
    entry_price: float,
    invalidation_price: float,
    direction: str,
    last: float | None,
) -> dict:
    """The LIVE position readouts that travel with the stance (data-contract row 27, consumer #5).

    Computed ONCE here from the SAME single ``marks.r_basis()`` helper (never a second R formula):

      * ``r_basis`` — ``R = |entry − invalidation|`` (the goal-doc R unit). The single basis both the
        distance-in-R and the open-R divide by.
      * ``distance_to_invalidation`` — how far the CURRENT last sits from the declared invalidation,
        in ``dollars`` (signed so a POSITIVE distance means price is on the SAFE side of the
        invalidation — above it for a long, below it for a short; negative once price has crossed it)
        and in ``r`` (that dollar distance ÷ the R basis). A move toward the invalidation shrinks it
        toward 0; a print through it goes negative — the honest "how close is the idea to being wrong".
      * ``open_r`` — the current open move from entry to the last, in R units, SIGNED BY DIRECTION
        with the SAME convention as ``marks.py``'s realized move (a long that is up, or a short that is
        down, is POSITIVE). ``None`` until a ``last`` exists.

    A degenerate ``R == 0`` basis (entry exactly at the invalidation) yields ``None`` for the R-unit
    figures (never a divide-by-zero / fabricated infinity), while the dollar distance still reads —
    honest absence over a fabricated number (mirrors ``marks.py``'s realized-R discipline). ``last``
    is ``None`` only before any trade prints; the R/dollar readouts that need it are then ``None``.
    """
    basis = r_basis(entry_price, invalidation_price)

    distance_dollars: float | None = None
    distance_r: float | None = None
    open_r: float | None = None
    if last is not None:
        # Signed so POSITIVE = the safe side of the invalidation (above it for a long, below for a short).
        if direction == "long":
            distance_dollars = last - invalidation_price
            open_dollars = last - entry_price
        else:
            distance_dollars = invalidation_price - last
            open_dollars = entry_price - last
        if basis > 0:
            distance_r = distance_dollars / basis
            open_r = open_dollars / basis

    return {
        "r_basis": basis if basis > 0 else None,
        "distance_to_invalidation": {
            "dollars": distance_dollars,
            "r": distance_r,
        },
        "open_r": open_r,
    }
