"""The verdict-transition engine (capability 24) — a PURE per-event evaluator.

Given a thesis and the stream of frozen engine snapshots, this maps each snapshot to a published
verdict in ``pending | confirming | weakening | rejecting | invalidated`` using **config-owned,
per-setup rule tables composed ONLY of EXISTING engine tape states / features** (no new indicator,
the no-new-indicators anti-goal). The evaluator is deliberately FastAPI-free and engine-free: it
reads a snapshot in and returns a ``VerdictDecision`` out, so it is unit-testable on unpaced replay
streams without any of the monitor's persistence side effects. The monitor (``monitor.py``) owns
publication, persistence (the append-only timeline), and the ``invalidated`` auto-resolve.

The grammar, per the iteration spec:

  * **Dwell.** A raw verdict rule must hold CONTINUOUSLY for the per-setup ``verdict_dwell_seconds``
    (LOGICAL time, restarting at thesis creation) before it is PUBLISHED. So confirmation always
    requires sustained POST-DECLARATION evidence by construction, and a single flickering tick never
    publishes a transition. Each published transition records ``rule_first_true`` (the first logical
    instant + price at which the raw rule began holding) distinct from ``published_at`` (after the
    dwell elapsed).

  * **absorption_reversal** — confirms on the REVERSAL: the flip to matching control WITH real price
    impact, NEVER on sustained absorption alone (premise met, trigger not-yet) — J-40.

  * **trend_continuation** — confirms while matching control + impact hold; an OPPOSING control tape
    publishes ``rejecting`` (a judgement, the thesis stays active — NOT a resolution) — J-41/J-42.

  * **level_break** — a LATCH: no confirmation, however strong control is, until ``last`` crosses the
    declared level; once latched AND control holds, confirming citing the cross + control — J-45.

  * **failed_move_fade** — the deliberate asymmetry with J-40: the absorption of the failed push IS
    the expected behaviour and reads confirming; a reclaim keeps it confirming; rejecting needs real
    opposite follow-through — J-46.

  * **Confirmed → weakening** — once confirmed, fading evidence (the tape going neutral/unclear)
    publishes ``weakening`` after its dwell — never a silent return to ``pending`` — J-43.

  * **Invalidation (dwell-exempt, robust, system-owned)** — a single print beyond the declared
    invalidation by ≥ ``invalidation_epsilon_spread_multiple × spread``, OR ``invalidation_k_consecutive``
    consecutive prints beyond it, flips the verdict to ``invalidated`` IMMEDIATELY (no dwell), with
    the offending print price + logical timestamp recorded — J-44. A lone bad print INSIDE the ε guard
    band does NOT invalidate.

Every published verdict carries plain-language, present-tense, thesis-attributed EVIDENCE derived
from canonical snapshot values (no naked outputs; no imperative/predictive/certainty language).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Config
from ..engine.snapshot import EngineSnapshot
from .store import ThesisRecord

# Raw (pre-dwell) verdicts the per-setup rule tables emit. ``pending`` is the neutral raw read
# (premise not yet met / trigger not yet fired); the published verdict only ADVANCES through the
# dwell, and ``weakening`` is published (never raw) once a confirmed thesis fades.
_RAW_PENDING = "pending"
_RAW_CONFIRMING = "confirming"
_RAW_REJECTING = "rejecting"


@dataclass(frozen=True)
class VerdictDecision:
    """The evaluator's output for ONE processed event.

    ``changed`` is True only when a NEW verdict is PUBLISHED on this event (the monitor then appends
    exactly one timeline row and updates the projection). When ``changed`` is False the published
    verdict is unchanged this tick (no flapping, no duplicate rows). The fields below describe the
    CURRENTLY published verdict regardless of ``changed`` so the monitor can always read the live
    projection values from the evaluator.
    """

    changed: bool
    verdict: str
    evidence: str
    # Timing record for the published transition (capability 24): the first logical instant + price
    # the raw rule held (``rule_first_true_*``) vs when it was published after the dwell
    # (``published_at_*``). ``None`` for the initial ``pending`` (no raw rule held to publish it).
    rule_first_true_ts: float | None
    rule_first_true_price: float | None
    published_at_ts: float | None
    # The canonical snapshot values stamped on the appended timeline row (single source of truth —
    # the evaluator never recomputes these; it copies the engine read at publication).
    tape_state: str | None
    confidence: float | None
    last: float | None
    # Set ONLY on the invalidation transition: the monitor reads this to auto-resolve the thesis
    # ``invalidated`` through the existing store path. False on every other decision.
    invalidated: bool = False


def _fmt(value: float | None, places: int = 4) -> str:
    """Format a feature/price for an evidence string (canonical value, never recomputed)."""
    if value is None:
        return "n/a"
    return f"{value:+.{places}f}" if places <= 4 else f"{value:.{places}f}"


def _price(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


class VerdictEvaluator:
    """Holds one thesis's verdict state and advances it per processed snapshot (PURE — no I/O).

    Construct with the thesis + config; call :meth:`evaluate` with each frozen snapshot in stream
    order. The evaluator owns: the currently published verdict, the dwell tracker (when the current
    raw rule first became true), the ``level_break`` latch, and the consecutive-bad-print counter.
    It performs NO persistence and reads NOTHING but the snapshot it is handed and the thesis it
    holds (so the engine stays byte-identical with it attached — equivalence anti-goal).
    """

    def __init__(self, thesis: ThesisRecord, config: Config) -> None:
        self._thesis = thesis
        self._config = config
        self._dwell = float(
            config.verdict_dwell_seconds.get(thesis.setup_type, max(config.verdict_dwell_seconds.values()))
        )
        self._epsilon = config.invalidation_epsilon_spread_multiple
        self._k = config.invalidation_k_consecutive

        # Published-verdict state. Starts at ``pending`` (the declaration appended the initial pending
        # row; the evaluator publishes the FIRST transition away from it).
        self._published = "pending"
        self._terminal = False  # invalidated => no further transitions

        # Dwell tracker for the pending->confirming / ->weakening / ->rejecting advance: which raw
        # verdict is currently accumulating, and the first logical instant + price it held.
        self._pending_raw: str | None = None
        self._raw_first_ts: float | None = None
        self._raw_first_price: float | None = None

        # level_break latch: once ``last`` crosses the declared level in the thesis direction it stays
        # latched (a break-and-go does not un-break if price wobbles back to the level — the cross is
        # the trigger; price falling back THROUGH the invalidation is the separate invalidation path).
        self._level_latched = False

        # Invalidation robustness: count of CONSECUTIVE prints strictly beyond the invalidation
        # (inside the ε guard); reset by any print back on the right side.
        self._consecutive_beyond = 0

    # --- public API -----------------------------------------------------------------------------
    @property
    def published_verdict(self) -> str:
        return self._published

    def evaluate(self, snap: EngineSnapshot) -> VerdictDecision:
        """Advance the verdict against ``snap`` and return the decision for this event."""
        # Once invalidated the thesis is terminal — no further transitions, evidence is frozen.
        if self._terminal:
            return self._unchanged(snap)

        # 1) INVALIDATION first — dwell-exempt and system-owned. A qualifying breach short-circuits
        # everything else (a print through the level resolves the thesis regardless of the raw read).
        inval = self._check_invalidation(snap)
        if inval is not None:
            return inval

        # 2) Otherwise advance the published verdict through the per-setup raw rule + dwell.
        raw, raw_evidence = self._raw_verdict(snap)
        return self._advance(snap, raw, raw_evidence)

    # --- invalidation (dwell-exempt, robust) ----------------------------------------------------
    def _check_invalidation(self, snap: EngineSnapshot) -> VerdictDecision | None:
        last = snap.last
        if last is None:
            return None
        direction = self._thesis.direction
        inval = self._thesis.invalidation_price
        # "Beyond" the invalidation = the wrong side for the thesis (long: at/below; short: at/above).
        if direction == "long":
            beyond = last <= inval
            margin = inval - last
        else:
            beyond = last >= inval
            margin = last - inval

        if not beyond:
            self._consecutive_beyond = 0
            return None

        self._consecutive_beyond += 1
        spread = snap.spread if snap.spread is not None else 0.0
        guard = self._epsilon * spread
        big_single = margin >= guard and guard > 0
        # When there is no spread basis (guard == 0), a ≥0 breach with the configured k-consecutive
        # discipline still protects against a lone bad print; a single print only invalidates via the
        # ε rule when a real spread exists (robust to a zero/missing-quote artifact).
        k_consecutive = self._consecutive_beyond >= self._k

        if big_single or k_consecutive:
            self._terminal = True
            self._published = "invalidated"
            if big_single:
                detail = (
                    f"A print at {_price(last)} ran {_price(margin)} through your invalidation "
                    f"at {_price(inval)} — past the {self._epsilon:g}× spread guard "
                    f"({_price(guard)}); the thesis is invalidated."
                )
            else:
                detail = (
                    f"{self._consecutive_beyond} consecutive prints printed through your "
                    f"invalidation at {_price(inval)} (last {_price(last)}); the thesis is "
                    f"invalidated."
                )
            return VerdictDecision(
                changed=True,
                verdict="invalidated",
                evidence=detail,
                rule_first_true_ts=snap.timestamp,
                rule_first_true_price=last,
                published_at_ts=snap.timestamp,
                tape_state=snap.tape_state,
                confidence=snap.confidence,
                last=last,
                invalidated=True,
            )
        return None

    # --- per-setup raw rule tables (EXISTING states/features only) ------------------------------
    def _raw_verdict(self, snap: EngineSnapshot) -> tuple[str, str]:
        """Map the snapshot to a RAW verdict + its evidence for the thesis's setup type.

        Returns ``(_RAW_PENDING | _RAW_CONFIRMING | _RAW_REJECTING, evidence)``. ``weakening`` is NOT
        a raw verdict — it is published by :meth:`_advance` when a CONFIRMED thesis's raw read falls
        back to ``pending``. Composes EXISTING tape states + primary-window price-impact features only.
        """
        setup = self._thesis.setup_type
        if setup == "absorption_reversal":
            return self._raw_absorption_reversal(snap)
        if setup == "trend_continuation":
            return self._raw_trend_continuation(snap)
        if setup == "level_break":
            return self._raw_level_break(snap)
        if setup == "failed_move_fade":
            return self._raw_failed_move_fade(snap)
        return (_RAW_PENDING, "")

    def _control_state(self) -> str:
        return "buyer_control" if self._thesis.direction == "long" else "seller_control"

    def _opposing_control_state(self) -> str:
        return "seller_control" if self._thesis.direction == "long" else "buyer_control"

    def _absorption_state(self) -> str:
        # The absorption an absorption_reversal THESIS is built on: a long absorption_reversal expects
        # sellers absorbed at the bid (bid_absorption); a short expects buyers absorbed at the ask
        # (ask_absorption). (failed_move_fade names its OWN fade absorption inline in
        # ``_raw_failed_move_fade`` — long fades a failed DOWNSIDE break at the bid, per goal.md J-46.)
        return "bid_absorption" if self._thesis.direction == "long" else "ask_absorption"

    def _directional_impact(self, snap: EngineSnapshot) -> float:
        primary = snap.primary_features
        if self._thesis.direction == "long":
            return primary.get("buy_price_impact", 0.0)
        return primary.get("sell_price_impact", 0.0)

    def _has_directional_impact(self, snap: EngineSnapshot) -> bool:
        impact = self._directional_impact(snap)
        return impact > 0 if self._thesis.direction == "long" else impact < 0

    def _impact_phrase(self, snap: EngineSnapshot) -> str:
        impact = self._directional_impact(snap)
        label = "buy_price_impact" if self._thesis.direction == "long" else "sell_price_impact"
        return f"{label} {_fmt(impact)}"

    def _raw_absorption_reversal(self, snap: EngineSnapshot) -> tuple[str, str]:
        # Confirms ONLY on the reversal: the flip to matching control WITH real directional impact.
        # Sustained absorption alone is the PREMISE — it stays pending (premise met, trigger not-yet).
        if snap.tape_state == self._control_state() and self._has_directional_impact(snap):
            side = "buyers" if self._thesis.direction == "long" else "sellers"
            way = "upward" if self._thesis.direction == "long" else "downward"
            return (
                _RAW_CONFIRMING,
                f"The tape reversed: {side} took control with real {way} impact "
                f"({self._impact_phrase(snap)}), lifting price off the absorbed level — "
                f"the reversal your thesis called for.",
            )
        return (_RAW_PENDING, "")

    def _raw_trend_continuation(self, snap: EngineSnapshot) -> tuple[str, str]:
        # Confirms while matching control + impact hold; OPPOSING control publishes rejecting.
        if snap.tape_state == self._control_state() and self._has_directional_impact(snap):
            side = "buyers" if self._thesis.direction == "long" else "sellers"
            way = "up" if self._thesis.direction == "long" else "down"
            return (
                _RAW_CONFIRMING,
                f"Control on your side is sustained — {side} keep pressing price {way} "
                f"({self._impact_phrase(snap)}); the tape confirms your thesis.",
            )
        if snap.tape_state == self._opposing_control_state():
            opp = "sellers" if self._thesis.direction == "long" else "buyers"
            opp_impact = (
                snap.primary_features.get("sell_price_impact", 0.0)
                if self._thesis.direction == "long"
                else snap.primary_features.get("buy_price_impact", 0.0)
            )
            opp_label = (
                "sell_price_impact" if self._thesis.direction == "long" else "buy_price_impact"
            )
            return (
                _RAW_REJECTING,
                f"The opposite side has control — {opp} are pressing price against your thesis "
                f"({opp_label} {_fmt(opp_impact)}); the tape is rejecting it.",
            )
        return (_RAW_PENDING, "")

    def _raw_level_break(self, snap: EngineSnapshot) -> tuple[str, str]:
        # A LATCH: no confirmation, however strong control is, until last CROSSES the declared level.
        level = self._thesis.level_price
        last = snap.last
        if level is not None and last is not None and not self._level_latched:
            crossed = last > level if self._thesis.direction == "long" else last < level
            if crossed:
                self._level_latched = True
        if (
            self._level_latched
            and snap.tape_state == self._control_state()
            and self._has_directional_impact(snap)
        ):
            way = "above" if self._thesis.direction == "long" else "below"
            side = "buyers" if self._thesis.direction == "long" else "sellers"
            return (
                _RAW_CONFIRMING,
                f"Price broke {way} your level at {_price(level)} (last {_price(last)}) and "
                f"{side} hold control after the break ({self._impact_phrase(snap)}); the tape "
                f"confirms the break.",
            )
        return (_RAW_PENDING, "")

    def _raw_failed_move_fade(self, snap: EngineSnapshot) -> tuple[str, str]:
        # The deliberate asymmetry with absorption_reversal: the ABSORPTION of the failed push IS the
        # expected behaviour and reads confirming directly; control on your side keeps it confirming;
        # rejecting needs real OPPOSITE follow-through (the failed move resuming with impact).
        #
        # goal.md J-46 side mapping (iter-6 fix): a LONG failed_move_fade fades a failed DOWNSIDE
        # break — the push LOWER fails and is absorbed at the BID (``bid_absorption``); a SHORT fmf
        # fades a failed UPSIDE break absorbed at the ASK (``ask_absorption``). (The prior code had
        # this INVERTED — ask_absorption for long — which goal.md contradicts in plain words.)
        fade_absorption = "bid_absorption" if self._thesis.direction == "long" else "ask_absorption"
        if snap.tape_state == fade_absorption:
            pushed = "lower" if self._thesis.direction == "long" else "higher"
            return (
                _RAW_CONFIRMING,
                f"The push {pushed} failed to find control and is being absorbed back toward "
                f"your level ({snap.tape_state}); the failed move is fading as your thesis called for.",
            )
        if snap.tape_state == self._control_state() and self._has_directional_impact(snap):
            side = "buyers" if self._thesis.direction == "long" else "sellers"
            return (
                _RAW_CONFIRMING,
                f"Control turned to your side as the failed move faded — {side} now press price "
                f"your way ({self._impact_phrase(snap)}); the tape confirms your fade.",
            )
        if snap.tape_state == self._opposing_control_state():
            opp = "sellers" if self._thesis.direction == "long" else "buyers"
            return (
                _RAW_REJECTING,
                f"The move did not fail — {opp} took real control in the original direction; "
                f"the tape is rejecting your fade.",
            )
        return (_RAW_PENDING, "")

    # --- dwell-gated publication ----------------------------------------------------------------
    def _advance(self, snap: EngineSnapshot, raw: str, raw_evidence: str) -> VerdictDecision:
        # Track when the current raw read first became true (resets whenever the raw read changes), so
        # a transition publishes only after the raw rule has held CONTINUOUSLY for the dwell.
        if raw != self._pending_raw:
            self._pending_raw = raw
            self._raw_first_ts = snap.timestamp
            self._raw_first_price = snap.last

        held_for = snap.timestamp - (self._raw_first_ts if self._raw_first_ts is not None else snap.timestamp)
        dwell_elapsed = held_for >= self._dwell

        target = self._published_target(raw)
        if target is None or target == self._published or not dwell_elapsed:
            return self._unchanged(snap)

        # Publish the transition.
        evidence = self._publish_evidence(target, raw_evidence, snap)
        self._published = target
        return VerdictDecision(
            changed=True,
            verdict=target,
            evidence=evidence,
            rule_first_true_ts=self._raw_first_ts,
            rule_first_true_price=self._raw_first_price,
            published_at_ts=snap.timestamp,
            tape_state=snap.tape_state,
            confidence=snap.confidence,
            last=snap.last,
        )

    def _published_target(self, raw: str) -> str | None:
        """Map a raw read + the current published verdict to the verdict that should be PUBLISHED.

        The state machine: pending -> confirming (raw confirming); pending/confirming -> rejecting
        (raw rejecting); confirming -> weakening (raw falls back to pending — never silently to
        pending again, J-43); weakening can re-confirm or reject. A raw ``pending`` while still
        ``pending`` is no transition.
        """
        if raw == _RAW_CONFIRMING:
            return "confirming"
        if raw == _RAW_REJECTING:
            return "rejecting"
        # raw == pending
        if self._published in ("confirming", "weakening"):
            # Confirmed evidence faded — publish weakening, NEVER a silent return to pending (J-43).
            return "weakening"
        return None  # still pending; nothing to publish

    def _publish_evidence(self, target: str, raw_evidence: str, snap: EngineSnapshot) -> str:
        if target == "weakening":
            # Distinct "supporting evidence faded" register (J-43) — descriptive, present-tense.
            return (
                f"The control that confirmed your thesis has faded — the tape is now {snap.tape_state} "
                f"with no clean impact on your side; support is weakening."
            )
        # confirming / rejecting carry the raw rule's evidence (already thesis-attributed & descriptive).
        return raw_evidence

    def _unchanged(self, snap: EngineSnapshot) -> VerdictDecision:
        return VerdictDecision(
            changed=False,
            verdict=self._published,
            evidence="",
            rule_first_true_ts=None,
            rule_first_true_price=None,
            published_at_ts=None,
            tape_state=snap.tape_state,
            confidence=snap.confidence,
            last=snap.last,
        )
