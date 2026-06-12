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

from ..config import Config
from ..engine.snapshot import EngineSnapshot
from .marks import r_basis
from .taxonomy import (
    STANCE_PENDING_EVIDENCE,
    checklist_check_caption,
    checklist_check_label,
    checklist_nearest_counterevidence,
    checklist_stance_evidence,
    checklist_stance_label,
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


# =================================================================================================
# The ENTRY-CHECKLIST evaluator (data-contract row 25, CHECKLIST half; capability 33 / J-63).
# =================================================================================================
#
# At the moment of decision — an active, evaluated, NOT-yet-entry-marked thesis — the strip shows the
# ENTRY CHECKLIST: eight named checks each rendering its LIVE measured margin IN ITS OWN UNITS (never a
# bare boolean), an aggregate STANCE publishing through its own dwell, and a NEAREST-COUNTEREVIDENCE
# line — all computed ONCE here, server-side.
#
# DISCIPLINE (the iter-21 spec + the goal anti-goals):
#   * **Composed from EXISTING canonical values only.** Every check reads a value the engine/monitor
#     ALREADY computed (the published verdict, ``event_count`` vs the warm-up floor, ``stream_status``,
#     the feeder ``delivery_lag_seconds``, the primary-window spread/speed, the declared invalidation,
#     the recorded ``rule_first_true`` price) — NO new indicator, NO second computation of any contract
#     value. The reused gates are the classifier's OWN (warm-up floor, stability spread cap in bps, the
#     trade-speed floor) + the two declaration-time research defaults (invalidation-too-tight multiple,
#     chase-return threshold) — no new threshold.
#   * **A live measured margin per check, never a bare boolean.** Each check carries pass/fail PLUS its
#     measured margin in its own units (a verdict string; events vs floor; the stream status; lag s vs
#     bound; spread bps vs cap; speed vs floor; distance in spread-multiples vs floor; chase return vs
#     threshold), formatted ONCE here so the UI renders it verbatim (display rounding only).
#   * **Read-only over the engine.** The evaluator only READS the snapshot + the published verdict it is
#     handed — it mutates no engine/feature/classifier state, so engine outputs stay byte-identical
#     (equivalence anti-goal). Never persisted (schema stays v7).
#   * **Honest degradation, no frozen green.** Whenever the feed is not live / the tape is not current
#     (``feed_live`` / ``tape_lag_ok`` fail) the aggregate stance is ``no_fresh_tape`` — a previous
#     ``conditions_met`` MUST NOT persist over non-live data.
#   * **Its own dwell.** The aggregate stance publishes through a config-owned LOGICAL-time dwell
#     (``checklist_stance_dwell_seconds``) so a single flickering check never flaps the stance — EXCEPT
#     ``no_fresh_tape``/``tape_against``, which publish IMMEDIATELY (honest degradation must never lag
#     behind a stale feed, and a rejecting verdict is itself already dwell-gated).
#   * **Never imperative, never predictive.** Present-tense, factual copy describing the tape NOW.


def _check(check_id: str, passed: bool, margin: str, distance: float | None) -> dict:
    """One checklist-check projection row — pass/fail + the live measured margin (its own units).

    ``margin`` is the already-formatted, render-verbatim margin string (the UI does display rounding
    only, no arithmetic). ``distance`` is the SIGNED normalized distance from this check's boundary
    (POSITIVE = passing with this much room; NEGATIVE = failing by this much), used ONLY server-side to
    pick the nearest-counterevidence check — it is NOT a second contract value, just a ranking key. The
    label + caption come from the taxonomy (the frontend hardcodes none)."""
    return {
        "check": check_id,
        "label": checklist_check_label(check_id),
        "caption": checklist_check_caption(check_id),
        "passed": passed,
        "margin": margin,
        "_distance": distance,  # server-only ranking key (stripped before serving — see evaluate)
    }


def evaluate_entry_checks(
    *,
    snapshot: EngineSnapshot,
    verdict: str,
    invalidation_price: float,
    direction: str,
    rule_first_true_price: float | None,
    config: Config,
) -> list[dict]:
    """The eight entry-checklist checks, each with its live measured margin, computed ONCE.

    Composes ONLY existing canonical values (single source of truth — never recomputes a contract
    value): the published ``verdict`` (row 16), ``snapshot.event_count`` vs ``warmup_min_events``,
    ``snapshot.stream_status`` (row 6), the feeder ``snapshot.delivery_lag_seconds`` (row 14) vs the
    config bound, the primary-window ``average_spread`` (as bps of ``reference_price`` — the classifier's
    OWN stability metric) vs ``max_stable_spread_bps``, the primary-window ``trade_speed`` vs
    ``min_trade_speed``, ``|last − invalidation|`` in spread-multiples vs
    ``invalidation_too_tight_spread_multiple``, and the directional return from the recorded
    ``rule_first_true_price`` to the current last vs ``chase_return_threshold`` (anchored at
    ``rule_first_true`` — NEVER the post-dwell publish).

    Returns the eight ``_check`` rows in display order. Each ``_distance`` is the signed margin from the
    check's boundary in a comparable, normalized space (used only to rank the nearest counterevidence).
    """
    primary = snapshot.primary_features
    checks: list[dict] = []

    # 1) verdict_confirming — the current published row-16 verdict (margin = the verdict itself). A
    #    rejecting/invalidated verdict fails it; pending/weakening fail it too (only confirming passes).
    vc_pass = verdict == "confirming"
    checks.append(
        _check(
            "verdict_confirming",
            vc_pass,
            margin=f"verdict {verdict}",
            distance=1.0 if vc_pass else -1.0,
        )
    )

    # 2) warm — events processed vs the classifier's OWN warm-up floor (no new threshold).
    events = snapshot.event_count
    floor = config.warmup_min_events
    warm_pass = events >= floor
    checks.append(
        _check(
            "warm",
            warm_pass,
            margin=f"{events}/{floor} events",
            distance=float(events - floor),
        )
    )

    # 3) feed_live — the canonical row-6 stream_status MUST be ``live`` (margin = the actual status).
    status = snapshot.stream_status
    live_pass = status == "live"
    checks.append(
        _check(
            "feed_live",
            live_pass,
            margin=f"status {status}",
            distance=1.0 if live_pass else -1.0,
        )
    )

    # 4) tape_lag_ok — the feeder-owned row-14 ``delivery_lag_seconds`` vs the config bound (seconds).
    #    Reads the SAME value the UI lag readout reads. ``None`` (no lag measured yet) is treated as
    #    NOT current (honest — we cannot assert freshness without a measurement); margin names it.
    bound = config.delivery_lag_ok_bound_seconds
    lag = snapshot.delivery_lag_seconds
    if lag is None:
        lag_pass = False
        lag_margin = f"lag — / {bound:.1f}s"
        lag_distance = -bound  # treated as maximally stale for ranking (no measurement)
    else:
        lag_pass = lag <= bound
        lag_margin = f"lag {lag:.1f}s / {bound:.1f}s"
        lag_distance = bound - lag
    checks.append(_check("tape_lag_ok", lag_pass, margin=lag_margin, distance=lag_distance))

    # 5) spread_stable — the average spread within the classifier's OWN stability domain, in bps
    #    (capability-26 precedent: reuse the classifier gate, no new threshold). The spread is judged
    #    in bps of the canonical ``reference_price`` (the SAME relative metric the classifier uses);
    #    with no price basis it falls back to the absolute dollar cap (byte-identical to the classifier).
    spread = primary.get("average_spread", 0.0)
    reference_price = primary.get("reference_price", 0.0)
    if reference_price > 0.0:
        spread_metric = spread / reference_price * 10000.0  # basis points
        spread_cap = config.max_stable_spread_bps
        spread_margin = f"{spread_metric:.1f} / {spread_cap:.1f} bps"
    else:
        spread_metric = spread
        spread_cap = config.max_stable_spread
        spread_margin = f"{spread_metric:.2f} / {spread_cap:.2f}"
    spread_pass = spread_metric <= spread_cap
    checks.append(
        _check(
            "spread_stable",
            spread_pass,
            margin=spread_margin,
            distance=spread_cap - spread_metric,
        )
    )

    # 6) trade_speed_ok — trade speed at/above the classifier's OWN floor (events/s; no new threshold).
    speed = primary.get("trade_speed", 0.0)
    speed_floor = config.min_trade_speed
    speed_pass = speed >= speed_floor
    checks.append(
        _check(
            "trade_speed_ok",
            speed_pass,
            margin=f"{speed:.2f} / {speed_floor:.2f} trades/s",
            distance=speed - speed_floor,
        )
    )

    # 7) invalidation_distance_ok — the distance from the current last to the declared invalidation, in
    #    SPREAD-MULTIPLES, vs ``invalidation_too_tight_spread_multiple`` (the same too-tight gate, no new
    #    threshold). A stop comfortably outside spread noise PASSES; one inside the band FAILS. With no
    #    spread / no last the multiple is unmeasurable — honest fail naming the absence. Direction-aware
    #    only in the SIGN of "distance" the spec wants: the magnitude |last − invalidation| is what the
    #    too-tight gate measures (a wrong-side invalidation is a 422 at declaration, never reachable here).
    last = snapshot.last
    inval_floor = config.invalidation_too_tight_spread_multiple
    if last is None or spread <= 0.0:
        dist_pass = False
        dist_margin = f"— / {inval_floor:g}× spread"
        dist_distance = -inval_floor
    else:
        multiples = abs(last - invalidation_price) / spread
        dist_pass = multiples >= inval_floor
        dist_margin = f"{multiples:.1f}× / {inval_floor:g}× spread"
        dist_distance = multiples - inval_floor
    checks.append(
        _check(
            "invalidation_distance_ok",
            dist_pass,
            margin=dist_margin,
            distance=dist_distance,
        )
    )

    # 8) not_chasing — the directional return from the recorded ``rule_first_true`` price to the current
    #    last, vs ``chase_return_threshold`` (anchored at ``rule_first_true``, NEVER the post-dwell
    #    publish). A FAVORABLE move past the threshold since the rule first held means the move has run
    #    before this entry => chasing => FAIL. Direction-aware: for a long the favorable move is UP, for
    #    a short it is DOWN. Before any rule has held (no anchor) there is nothing to chase => PASS with
    #    an explicit "no anchor" margin (honest — the move has not begun).
    chase_threshold = config.chase_return_threshold
    if rule_first_true_price is None or rule_first_true_price <= 0.0 or last is None:
        chase_pass = True
        chase_margin = f"+0.00% / {chase_threshold * 100:.2f}% (no rule anchor yet)"
        chase_distance = chase_threshold  # maximal room (nothing has run)
    else:
        raw_return = (last - rule_first_true_price) / rule_first_true_price
        favorable_return = raw_return if direction == "long" else -raw_return
        # Only a FAVORABLE run counts as chasing (an adverse move is not "chasing the move").
        chasing_run = max(favorable_return, 0.0)
        chase_pass = chasing_run < chase_threshold
        chase_margin = f"{favorable_return * 100:+.2f}% / {chase_threshold * 100:.2f}%"
        chase_distance = chase_threshold - chasing_run
    checks.append(
        _check("not_chasing", chase_pass, margin=chase_margin, distance=chase_distance)
    )

    return checks


class EntryChecklistEvaluator:
    """Holds one thesis's PUBLISHED entry-checklist stance and advances it per event (no I/O).

    Constructed when the monitor holds a thesis; advanced in ``on_event`` AFTER the verdict step so it
    reads the just-published verdict for this snapshot. Owns: the currently published aggregate stance
    and its dwell tracker. Performs NO persistence and reads NOTHING but the snapshot + published
    verdict it is handed (engine stays byte-identical — equivalence anti-goal). The PER-CHECK rows and
    the nearest-counterevidence line are recomputed fresh from the latest snapshot at projection time
    (they are a pure read); only the aggregate STANCE is dwell-published here so it does not flap.

    The checklist only MATTERS while the thesis is active + evaluated + NOT entry-marked (gated in
    ``build_projection``), but the dwell accumulates regardless so the stance is settled by the time it
    is shown.
    """

    def __init__(self, dwell_seconds: float) -> None:
        self._dwell = float(dwell_seconds)
        # Published aggregate stance. Starts at ``conditions_not_met`` — pre-confirmation, the verdict
        # check fails by construction, so the honest opening read is "not met", never a fabricated green.
        self._published: str = "conditions_not_met"
        # Dwell tracker: which raw stance is accumulating + the first logical instant it held.
        self._pending_raw: str | None = None
        self._raw_first_ts: float | None = None

    @property
    def published_stance(self) -> str:
        return self._published

    @staticmethod
    def raw_stance(checks: list[dict], verdict: str) -> str:
        """The RAW aggregate stance for this event from the eight checks + the published verdict.

        Priority (the spec's aggregation map):
          * ``no_fresh_tape`` — whenever ``feed_live`` OR ``tape_lag_ok`` fails (the feed is paused /
            closed / stale / failed / lagging) — a previous green NEVER persists over non-live data;
          * ``tape_against``  — the published verdict is rejecting/invalidated (the tape is working
            against the thesis);
          * ``conditions_met``     — every check passes (only reachable after confirmation, since the
            verdict_confirming check is one of the eight);
          * ``conditions_not_met`` — any check fails while the verdict is not rejecting and the tape is
            fresh (incl. the pre-confirmation pending case — the verdict check is unmet).
        """
        by_id = {c["check"]: c for c in checks}
        feed_live = by_id.get("feed_live", {}).get("passed", False)
        tape_lag_ok = by_id.get("tape_lag_ok", {}).get("passed", False)
        if not feed_live or not tape_lag_ok:
            return "no_fresh_tape"
        if verdict in ("rejecting", "invalidated"):
            return "tape_against"
        if all(c["passed"] for c in checks):
            return "conditions_met"
        return "conditions_not_met"

    def advance(self, *, checks: list[dict], verdict: str, logical_ts: float) -> None:
        """Advance the published aggregate stance against this event's raw stance.

        Dwell rule: a raw stance must hold CONTINUOUSLY for the dwell before it publishes — EXCEPT
        ``no_fresh_tape`` and ``tape_against``, which publish IMMEDIATELY (honest degradation must not
        lag a stale feed; a rejecting verdict is itself already dwell-gated). ``conditions_met`` /
        ``conditions_not_met`` transitions dwell so a single flickering check never flaps the stance.
        """
        raw = self.raw_stance(checks, verdict)

        # Honest degradation / tape-against publish IMMEDIATELY (dwell-exempt).
        if raw in ("no_fresh_tape", "tape_against"):
            self._published = raw
            self._pending_raw = raw
            self._raw_first_ts = logical_ts
            return

        # Dwell tracking for conditions_met / conditions_not_met: reset the clock when the raw changes.
        if raw != self._pending_raw:
            self._pending_raw = raw
            self._raw_first_ts = logical_ts

        if raw == self._published:
            return
        held_for = logical_ts - (self._raw_first_ts if self._raw_first_ts is not None else logical_ts)
        if held_for >= self._dwell:
            self._published = raw


def nearest_counterevidence(checks: list[dict], stance: str) -> dict | None:
    """The nearest-counterevidence row (capability 33) — computed ONCE server-side.

    Names the closest condition that would FLIP the current read, with its margin:
      * when ``conditions_met`` — the PASSING check nearest its boundary (smallest positive distance);
      * otherwise               — the nearest-to-passing FAILING check (the failing check whose
        distance is closest to zero, i.e. the least-negative).
    Returns ``{check, label, margin, line}`` or ``None`` when there is no candidate (e.g. an empty
    check list). ``line`` is the taxonomy-owned, render-verbatim sentence."""
    if not checks:
        return None
    if stance == "conditions_met":
        candidates = [c for c in checks if c["passed"]]
        if not candidates:
            return None
        nearest = min(candidates, key=lambda c: c["_distance"])
        met = True
    else:
        failing = [c for c in checks if not c["passed"]]
        if not failing:
            return None
        # The failing check closest to its boundary = the LARGEST (least-negative) distance.
        nearest = max(failing, key=lambda c: c["_distance"])
        met = False
    return {
        "check": nearest["check"],
        "label": nearest["label"],
        "margin": nearest["margin"],
        "line": checklist_nearest_counterevidence(nearest["label"], nearest["margin"], met),
    }


def build_checklist(
    *,
    snapshot: EngineSnapshot,
    verdict: str,
    published_stance: str,
    invalidation_price: float,
    direction: str,
    rule_first_true_price: float | None,
    config: Config,
) -> dict:
    """The full entry-checklist projection (capability 33, J-63) — computed ONCE server-side.

    Recomputes the eight checks fresh from the latest snapshot (a pure read of canonical values), pairs
    them with the dwell-PUBLISHED aggregate ``published_stance`` (owned by ``EntryChecklistEvaluator`` so
    it does not flap), counts ``N/total`` passing for the factual stance evidence, derives the
    nearest-counterevidence line, and lists the blockers (the failing checks) when not met. The UI
    renders every field verbatim (display rounding only — zero client arithmetic, zero stance
    derivation). The server-only ``_distance`` ranking key is STRIPPED before serving."""
    checks = evaluate_entry_checks(
        snapshot=snapshot,
        verdict=verdict,
        invalidation_price=invalidation_price,
        direction=direction,
        rule_first_true_price=rule_first_true_price,
        config=config,
    )
    total = len(checks)
    passed = sum(1 for c in checks if c["passed"])
    counter = nearest_counterevidence(checks, published_stance)
    # The blocker list (the failing checks) — named only when the conditions are NOT met. Empty on
    # conditions_met (every check passes).
    blockers = [c["check"] for c in checks if not c["passed"]]
    # Strip the server-only ranking key from the served check rows (it is not a contract value).
    served_checks = [
        {k: v for k, v in c.items() if k != "_distance"} for c in checks
    ]
    return {
        "stance": {
            "value": published_stance,
            "label": checklist_stance_label(published_stance),
            "evidence": checklist_stance_evidence(published_stance, passed, total),
        },
        "checks": served_checks,
        "passed": passed,
        "total": total,
        "blockers": blockers,
        "nearest_counterevidence": counter,
    }
