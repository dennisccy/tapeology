"""The research monitor — attached to the engine's observer seam, read-only over the engine.

One ``ResearchMonitor`` is attached per watched ticker via ``TapeEngine.add_observer`` (capability
20). It holds that ticker's active thesis, recomputes each frozen expected-behaviour statement's
LIVE status (met / not_yet / violated) on every processed event from EXISTING engine
states/features ONLY, and serves the single thesis projection that feeds BOTH the REST
``/research/thesis/active`` read and the WS ``thesis`` key (so they are verbatim-equal by
construction). The verdict is fixed at ``pending`` this iteration.

Discipline:
  * **Read-only over the engine** — the monitor never mutates engine/classifier/feature state, so
    engine outputs stay byte-identical with or without it (equivalence anti-goal). It only READS the
    snapshot handed to ``on_event`` and the thesis it is holding.
  * **Exception-isolated, feed never dies** — the engine already isolates a throwing observer; on
    top of that, the monitor catches its OWN errors (e.g. a statement-eval bug, or a store write
    failure on the verdict-event path) and flips an internal ``_failed`` flag so the projection
    reads ``monitor_status: failed`` rather than killing the feeder or silently dropping records.
  * **Writes go through the store's queue** — the initial ``pending`` event is enqueued; a store
    write failure surfaces as ``monitor_status: failed``.

The projection deliberately OMITS ``risk_flags`` entirely this iteration (J-49 builds it) — an
always-empty list would dishonestly read as "no risks found".
"""

from __future__ import annotations

import logging
import time

from ..config import Config
from ..engine.snapshot import EngineSnapshot
from .store import JournalStore, ThesisRecord, VerdictEventRecord
from .verdict import VerdictEvaluator

logger = logging.getLogger(__name__)


def data_feed_for_scenario(scenario: str) -> str:
    """Map the snapshot's source descriptor (``scenario``) to the canonical ``data_feed`` stamp.

    A ``live <SYM>`` source streams the IEX feed; a ``historical <SYM> <window>`` source replays the
    SIP consolidated feed; everything else is a simulated scenario (``sim``). This mirrors the
    per-mode feed config (``historical_feed`` = sip, ``live_feed`` = iex) — the feed-per-mode seam
    stays config-aligned so honesty stamps are correct."""
    if scenario.startswith("live "):
        return "iex"
    if scenario.startswith("historical "):
        return "sip"
    return "sim"


def _evaluate_statement(
    statement: dict, snap: EngineSnapshot, thesis: ThesisRecord, config: Config
) -> str:
    """The LIVE status of one frozen statement from EXISTING engine states/features only.

    Returns one of ``met | not_yet | violated``. No new indicator is computed — each ``kind`` reads
    canonical snapshot values (tape_state, primary-window price impact, last vs invalidation). The
    honest default is ``not_yet`` (no evidence is not a failure); ``violated`` is reserved for a read
    that contradicts the statement. ``config`` supplies the config-owned cutoffs the
    ``directional_impact`` adverse-side dominance test reuses (no magic number in research code).
    """
    kind = statement.get("kind")
    params = statement.get("params", {})
    direction = thesis.direction

    if kind == "tape_state_is":
        states = params.get("states", [])
        return "met" if snap.tape_state in states else "not_yet"

    if kind == "directional_impact":
        # Progress in the thesis direction must be DIRECTION-AWARE against the ADVERSE side, not just
        # a sign check on the thesis-side impact (iter-6 fix). On a falling tape the incidentally
        # positive ``buy_price_impact`` of a LONG thesis must NOT read ``met`` while sellers press
        # price DOWN — that is the tape moving against the thesis, so it reads ``violated``.
        #
        # Composes ONLY the existing primary-window ``buy_price_impact`` / ``sell_price_impact``
        # values, read verbatim from the snapshot (single source of truth — never recomputed). The
        # "material adverse impact" dominance test reuses the classifier's OWN config-owned
        # real-price-progress cutoffs (no magic number in research code): for a LONG thesis the
        # adverse side is selling, so ``sell_price_impact <= max_sell_price_impact`` means sellers are
        # making REAL downward progress against the thesis; symmetrically for SHORT against buying.
        #   * material adverse impact => violated  (the tape is moving AGAINST the thesis)
        #   * favorable progress on the thesis side, no material adverse impact => met
        #   * genuinely flat / no clean progress => not_yet (no evidence is not a failure)
        primary = snap.primary_features
        buy_impact = primary.get("buy_price_impact", 0.0)
        sell_impact = primary.get("sell_price_impact", 0.0)
        if direction == "long":
            adverse = sell_impact <= config.max_sell_price_impact
            favorable = buy_impact >= config.min_buy_price_impact
        else:
            adverse = buy_impact >= config.min_buy_price_impact
            favorable = sell_impact <= config.max_sell_price_impact
        if adverse:
            return "violated"
        if favorable:
            return "met"
        return "not_yet"

    if kind == "above_invalidation":
        # last on the correct side of the declared invalidation (long => above; short => below).
        # A print through the invalidation reads ``violated``; this is a status read only — the
        # dwell-exempt invalidation-RESOLUTION engine arrives next iteration.
        last = snap.last
        if last is None:
            return "not_yet"
        if direction == "long":
            return "met" if last > thesis.invalidation_price else "violated"
        else:
            return "met" if last < thesis.invalidation_price else "violated"

    return "not_yet"


class ResearchMonitor:
    """Holds one ticker's active thesis and serves its live projection (capability 20 observer)."""

    def __init__(self, store: JournalStore, config: Config) -> None:
        self._store = store
        self._config = config
        self._config_fingerprint = config.config_fingerprint()
        self._thesis: ThesisRecord | None = None
        self._last_snapshot: EngineSnapshot | None = None
        self._failed = False
        # Set once the engine resolves the thesis terminally (expired-on-stop, or invalidated by the
        # verdict engine); the projection then reflects the resolved status and the monitor stops
        # holding it active.
        self._resolved = False
        self._resolution: str | None = None  # the terminal resolution (expired | invalidated)
        # The verdict-transition engine (capability 24). Created when a thesis is set; the dwell
        # restarts at thesis creation by construction (a fresh evaluator). The PUBLISHED verdict +
        # evidence the projection serves live below.
        self._evaluator: VerdictEvaluator | None = None
        self._verdict = "pending"
        self._verdict_evidence = ""

    # --- thesis lifecycle (called from the route, NOT the hot path) -----------------------------
    def set_thesis(self, thesis: ThesisRecord) -> None:
        """Attach the freshly-declared thesis so subsequent events evaluate against it."""
        self._thesis = thesis
        self._resolved = False
        self._resolution = None
        # A FRESH evaluator => the per-setup dwell restarts at declaration, so confirmation requires
        # post-declaration evidence by construction (capability 24). The initial published verdict is
        # ``pending`` (the declaration route already appended the initial pending timeline row).
        self._evaluator = VerdictEvaluator(thesis, self._config)
        self._verdict = "pending"
        # Seed the published evidence with the pending register so the projection never carries a
        # NAKED verdict (the no-naked-outputs anti-goal): every verdict — including the initial
        # pending — reads with plain-language evidence. Replaced verbatim by the engine's evidence on
        # the first published transition.
        self._verdict_evidence = (
            "The tape is being watched against your thesis; the verdict stays pending until "
            "sustained post-declaration evidence accrues."
        )

    def clear_thesis(self) -> None:
        self._thesis = None
        self._resolved = False
        self._resolution = None
        self._evaluator = None
        self._verdict = "pending"
        self._verdict_evidence = ""

    @property
    def active_thesis_id(self) -> str | None:
        return self._thesis.id if self._thesis is not None and not self._resolved else None

    # --- observer callbacks (the hot path — exception-isolated, read-only) ----------------------
    def on_event(self, event: object, snapshot: EngineSnapshot) -> None:
        # Read-only over the engine: remember the latest snapshot (the projection reflects the current
        # engine read) and run the verdict engine against it. Wrapped defensively so a monitor-side
        # bug (an evaluator error or a store write failure on the verdict path) surfaces as
        # ``monitor_status: failed`` rather than propagating — the engine ALSO isolates this, but
        # defense in depth keeps the projection honest and the feed alive. NO engine/feature/state
        # mutation happens here (equivalence anti-goal): the evaluator only READS the frozen snapshot.
        try:
            self._last_snapshot = snapshot
            self._evaluate_verdict(snapshot)
        except Exception:
            self._failed = True
            logger.exception("research monitor on_event failed")

    def _evaluate_verdict(self, snapshot: EngineSnapshot) -> None:
        """Advance the verdict against this snapshot; publish + persist any transition.

        Pure-read of the snapshot via the evaluator, then — only on a PUBLISHED transition — append
        ONE append-only timeline row and update the live projection's verdict + evidence. On an
        ``invalidated`` transition the thesis is auto-resolved ``invalidated`` through the existing
        store path (system-owned; distinct from the user-facing resolve endpoint, out of scope this
        iteration). Runs inside ``on_event``'s try/except so any failure surfaces as
        ``monitor_status: failed`` and never kills the feeder."""
        if self._evaluator is None or self._thesis is None or self._resolved:
            return
        decision = self._evaluator.evaluate(snapshot)
        # Keep the live projection's verdict/evidence current (the published verdict, no flapping).
        self._verdict = decision.verdict
        if decision.changed:
            self._verdict_evidence = decision.evidence
            self._store.append_verdict_event(
                VerdictEventRecord(
                    thesis_id=self._thesis.id,
                    logical_ts=decision.published_at_ts
                    if decision.published_at_ts is not None
                    else snapshot.timestamp,
                    wall_ts=time.time(),
                    verdict=decision.verdict,
                    evidence=decision.evidence,
                    tape_state=decision.tape_state,
                    confidence=decision.confidence,
                    last=decision.last,
                    rule_first_true_ts=decision.rule_first_true_ts,
                    rule_first_true_price=decision.rule_first_true_price,
                )
            )
            if decision.invalidated:
                # System-owned auto-resolve via the existing resolution path (status row only — the
                # timeline row was just appended, never edited). The monitor stops holding the thesis
                # active; the projection then reflects the resolved/invalidated status (NOT a silent
                # revert to the idle declare affordance — the strip shows the terminal treatment).
                self._store.resolve_thesis(self._thesis.id, "invalidated")
                self._resolved = True
                self._resolution = "invalidated"

    def on_status(self, status: str) -> None:
        # Lifecycle honesty (subset of capability 24): a terminal stream status auto-resolves an
        # active thesis ``expired(reason)`` with a final appended timeline event. ``closed`` (stop /
        # stream exhaustion) and ``failed`` (feeder raised) are terminal; ``paused``/``stale`` are
        # not. No entry marks exist yet, so there is no survives-with-entry-mark exception.
        try:
            if status in ("closed", "failed") and self._thesis is not None and not self._resolved:
                self._expire_active(reason=status)
        except Exception:
            self._failed = True
            logger.exception("research monitor on_status failed")

    def _expire_active(self, reason: str) -> None:
        thesis = self._thesis
        if thesis is None:
            return
        wall = time.time()
        logical = self._last_snapshot.timestamp if self._last_snapshot is not None else 0.0
        last = self._last_snapshot.last if self._last_snapshot is not None else None
        detail = {
            "closed": "Thesis expired — the watch that declared it was stopped or the stream ended.",
            "failed": "Thesis expired — the feed that declared it failed.",
        }.get(reason, "Thesis expired.")
        try:
            self._store.resolve_thesis(thesis.id, "expired")
            self._store.append_verdict_event(
                VerdictEventRecord(
                    thesis_id=thesis.id,
                    logical_ts=logical,
                    wall_ts=wall,
                    verdict="expired",
                    evidence=detail,
                    tape_state=None,
                    confidence=None,
                    last=last,
                )
            )
            self._resolved = True
            self._resolution = "expired"
        except Exception:
            # A store failure on resolution must surface as failed, never crash the feeder.
            self._failed = True
            logger.exception("research monitor failed to expire thesis %s", thesis.id)

    # --- projection (the single source for REST + WS) -------------------------------------------
    def projection(self) -> dict | None:
        """The thesis projection, or ``None`` when no thesis is active (a normal state, not an error).

        Both ``GET /research/thesis/active`` and the WS ``thesis`` key call THIS one function, so the
        two are verbatim-equal by construction (data-contract row 15). Statement statuses are
        recomputed from the latest engine read each call (projection-level, never persisted); the
        PUBLISHED verdict + its evidence come from the verdict engine (capability 24).
        ``monitor_status`` is ``ok`` normally and ``failed`` if the monitor or its store write ever
        errored — surfaced honestly, never hidden.

        Resolution honesty: an ``expired`` resolution (the watch was stopped / the stream ended)
        clears the projection (``None``) — there is nothing live to show. An ``invalidated``
        resolution KEEPS the projection so the strip shows the TERMINAL treatment (the resolved
        thesis with its ``invalidated`` verdict + the offending evidence) rather than silently
        reverting to the idle declare affordance.
        """
        thesis = self._thesis
        if thesis is None:
            return None
        if self._resolved and self._resolution != "invalidated":
            return None
        snap = self._last_snapshot
        statements = [
            {
                "text": s["text"],
                "status": _evaluate_statement(s, snap, thesis, self._config)
                if snap is not None
                else "not_yet",
            }
            for s in thesis.statements
        ]
        # A resolved-invalidated thesis reports its terminal status/verdict; otherwise the active
        # thesis reports its declared status and the live published verdict.
        status = "invalidated" if self._resolution == "invalidated" else thesis.status
        return {
            "id": thesis.id,
            "ticker": thesis.ticker,
            "setup_type": thesis.setup_type,
            "direction": thesis.direction,
            "invalidation_price": thesis.invalidation_price,
            "level_price": thesis.level_price,
            "status": status,
            "verdict": self._verdict,
            "verdict_evidence": self._verdict_evidence,
            "statements": statements,
            "entry_context": thesis.entry_context,
            "bound_source": thesis.bound_source,
            "data_feed": thesis.data_feed,
            "config_fingerprint": thesis.config_fingerprint,
            "monitor_status": "failed" if self._failed else "ok",
        }
