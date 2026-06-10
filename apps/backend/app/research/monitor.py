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

from ..engine.snapshot import EngineSnapshot
from .store import JournalStore, ThesisRecord, VerdictEventRecord

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


def _evaluate_statement(statement: dict, snap: EngineSnapshot, thesis: ThesisRecord) -> str:
    """The LIVE status of one frozen statement from EXISTING engine states/features only.

    Returns one of ``met | not_yet | violated``. No new indicator is computed — each ``kind`` reads
    canonical snapshot values (tape_state, primary-window price impact, last vs invalidation). The
    honest default is ``not_yet`` (no evidence is not a failure); ``violated`` is reserved for a read
    that contradicts the statement.
    """
    kind = statement.get("kind")
    params = statement.get("params", {})
    direction = thesis.direction

    if kind == "tape_state_is":
        states = params.get("states", [])
        return "met" if snap.tape_state in states else "not_yet"

    if kind == "directional_impact":
        # Progress in the thesis direction: long => positive buy impact; short => negative sell
        # impact. Read from the primary window verbatim (single source of truth) — never recomputed.
        primary = snap.primary_features
        if direction == "long":
            impact = primary.get("buy_price_impact", 0.0)
            if impact > 0:
                return "met"
            if impact < 0:
                return "violated"
            return "not_yet"
        else:
            impact = primary.get("sell_price_impact", 0.0)
            if impact < 0:
                return "met"
            if impact > 0:
                return "violated"
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

    def __init__(self, store: JournalStore, config_fingerprint: str) -> None:
        self._store = store
        self._config_fingerprint = config_fingerprint
        self._thesis: ThesisRecord | None = None
        self._last_snapshot: EngineSnapshot | None = None
        self._failed = False
        # Set once the engine resolves the thesis terminally (expired-on-stop); the projection then
        # reflects the resolved status and the monitor stops holding it active.
        self._resolved = False

    # --- thesis lifecycle (called from the route, NOT the hot path) -----------------------------
    def set_thesis(self, thesis: ThesisRecord) -> None:
        """Attach the freshly-declared thesis so subsequent events evaluate against it."""
        self._thesis = thesis
        self._resolved = False

    def clear_thesis(self) -> None:
        self._thesis = None
        self._resolved = False

    @property
    def active_thesis_id(self) -> str | None:
        return self._thesis.id if self._thesis is not None and not self._resolved else None

    # --- observer callbacks (the hot path — exception-isolated, read-only) ----------------------
    def on_event(self, event: object, snapshot: EngineSnapshot) -> None:
        # Read-only: remember the latest snapshot so the projection reflects the current engine read.
        # Wrapped defensively so a monitor-side bug surfaces as ``monitor_status: failed`` rather
        # than propagating (the engine ALSO isolates this, but defense in depth keeps the projection
        # honest). NO engine/feature/state mutation happens here.
        try:
            self._last_snapshot = snapshot
        except Exception:
            self._failed = True
            logger.exception("research monitor on_event failed")

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
        verdict is fixed at ``pending`` this iteration. ``monitor_status`` is ``ok`` normally and
        ``failed`` if the monitor or its store write ever errored — surfaced honestly, never hidden.
        """
        thesis = self._thesis
        if thesis is None or self._resolved:
            return None
        snap = self._last_snapshot
        statements = [
            {
                "text": s["text"],
                "status": _evaluate_statement(s, snap, thesis) if snap is not None else "not_yet",
            }
            for s in thesis.statements
        ]
        return {
            "id": thesis.id,
            "ticker": thesis.ticker,
            "setup_type": thesis.setup_type,
            "direction": thesis.direction,
            "invalidation_price": thesis.invalidation_price,
            "level_price": thesis.level_price,
            "status": thesis.status,
            "verdict": "pending",
            "statements": statements,
            "entry_context": thesis.entry_context,
            "bound_source": thesis.bound_source,
            "data_feed": thesis.data_feed,
            "config_fingerprint": thesis.config_fingerprint,
            "monitor_status": "failed" if self._failed else "ok",
        }
