"""The setup-forming hint engine (capability 33, J-65) — the SINGLE computing owner of hints.

Driven by the research monitor's ``on_event`` / ``on_status`` seam (observer-only; NO
engine/classifier/feature file is ever touched, so engine outputs stay byte-identical with or without
it — the equivalence anti-goal). The engine is a PURE, DETERMINISTIC, LOGICAL-TIME evaluator: it reads
ONLY the frozen snapshot's tape state + its logical timestamp and decides, per event, whether a
state-native pattern has SUSTAINED past the config dwell. No wall-clock enters a hint decision (the wall
ts on a fired record is a stamp only — the verdict-dwell precedent), so sim journeys are deterministic.

Discipline (the goal's capability 33 + the iter-23 spec):
  * **Patterns compose EXISTING engine states ONLY** (no new indicator): a sustained absorption arms an
    absorption_reversal context; a sustained control arms a trend_continuation context. ``unclear`` never
    arms a hint; the two level setups have no state-native arming, so they never produce hints.
  * **Dwell + cooldown are config-owned, logical-time, IN the fingerprint** (``hint_sustain_dwell_seconds``
    / ``hint_cooldown_seconds`` — they shape the persisted hint records, the study-arm precedent). A
    pattern fires ONCE when its premise state holds CONTINUOUSLY past the dwell; the cooldown gates a
    re-fire of the SAME pattern on the SAME ticker. A flapping stream (SIM-CHOP) never holds one premise
    long enough to fire — by construction.
  * **Fire-once persistence** goes through the store's single writer queue (``insert_hint``), NEVER from
    event processing / the WS serialization path; the monitor enqueues it from its exception-isolated
    observer callback so a write failure surfaces as ``monitor_status: failed`` rather than killing the
    feeder.
  * **Active-hint lifecycle**: the hint stays active while its pattern's state persists; it clears when
    the state leaves the pattern, when the watch stops, and on any non-live status flip (paused / stale /
    closed / failed) — present-tense "is forming" copy must never sit over a non-live tape (the iter-22
    J-64 freshness lesson). Clearing an ACTIVE hint never touches the persisted log record.
  * **No naked outputs**: every fired/active hint carries plain-language evidence (with the measured
    sustain duration) and a baseline citation — the user's matching studied baseline cited verbatim, or
    exactly "no studied baseline — unvalidated pattern".
"""

from __future__ import annotations

import logging
import time
import uuid

from ..config import Config
from ..engine.snapshot import EngineSnapshot
from .feed_basis import data_feed_for_scenario
from .store import HintRecord, JournalStore
from .taxonomy import (
    HINT_BASELINE_UNVALIDATED,
    HINT_PATTERNS,
    hint_baseline_citation,
    hint_evidence,
    hint_pattern_label,
)

logger = logging.getLogger(__name__)

# Map a sustained tape state -> the pattern id it arms. The single authority for which states arm a hint
# (composed ONLY of the existing engine states); ``unclear`` is deliberately absent (it never arms one).
_STATE_TO_PATTERN: dict[str, str] = {
    spec["tape_state"]: pid for pid, spec in HINT_PATTERNS.items()
}

# ``data_feed_for_scenario`` is re-exported from the leaf ``feed_basis`` module (the ONE owner,
# data-contract row 26, iter-24) so existing ``from app.research.hints import data_feed_for_scenario``
# call sites keep resolving. The iter-23 LOCAL copy is REMOVED, not paralleled — the single definition
# now lives in ``feed_basis`` and reads the config-owned per-mode feed keys (J-67 single-config-value).


def _baseline_citation(
    store: JournalStore,
    *,
    setup_type: str,
    data_feed: str,
    config_fingerprint: str,
) -> str:
    """Produce the baseline citation ONCE at fire (capability 33, J-65). Reads the user's most recent
    PERSISTED ``done`` study matching this hint's setup_type + data_feed + config_fingerprint (level
    studies excluded by construction) and cites the STORED aggregates VERBATIM (n + the first-horizon
    ternary distribution). When none exists the citation is EXACTLY the honest unvalidated string.

    Never recomputes a study at read — it reads the already-persisted aggregate numbers; a read failure
    degrades to the honest unvalidated string (a citation must never crash the fire path)."""
    try:
        study = store.latest_done_study_for(
            setup_type=setup_type,
            data_feed=data_feed,
            config_fingerprint=config_fingerprint,
        )
    except Exception:  # pragma: no cover - defensive: a citation read must never crash the fire
        logger.exception("hint baseline citation read failed")
        return HINT_BASELINE_UNVALIDATED
    if study is None:
        return HINT_BASELINE_UNVALIDATED
    aggregates = study.payload.get("aggregates", {})
    setup_agg = aggregates.get("setup", {})
    n = setup_agg.get("n", 0)
    horizons = setup_agg.get("horizons", [])
    if n <= 0 or not horizons:
        return HINT_BASELINE_UNVALIDATED
    first = horizons[0]
    return hint_baseline_citation(
        n=n,
        plus=first.get("+1R_first", 0),
        minus=first.get("-1R_first", 0),
        neither=first.get("neither_within_horizon", 0),
        horizon=first.get("horizon", 0),
    )


class HintEngine:
    """One ticker's setup-forming hint evaluator (capability 33, J-65). Attached at engine creation
    REGARDLESS of any thesis — it observes every event and serves the active-hint projection.

    Holds the in-flight sustain clock (which premise state is currently building and since when), the
    last fired logical time per pattern (the cooldown gate), and the currently ACTIVE hint record (the
    live projection). All decisions are logical-time + deterministic; the store is touched only to
    PERSIST a fired hint (through the single writer queue) and to READ the baseline at fire."""

    def __init__(self, store: JournalStore, config: Config, ticker: str) -> None:
        self._store = store
        self._config = config
        self._ticker = ticker
        # The premise state currently building toward the dwell, and the logical instant it began.
        self._pending_pattern: str | None = None
        self._pending_since: float | None = None
        # The last fired logical time per pattern (the cooldown gate against a same-pattern re-fire).
        self._last_fired_logical: dict[str, float] = {}
        # The currently ACTIVE hint projection (the live dock read) — ``None`` when no hint is active.
        # It carries the persisted record's payload verbatim (the log record + the projection are the
        # same dict by construction). Cleared on state-leave / non-live status (never touches the log).
        self._active: dict | None = None

    # --- the observer seam (driven by the monitor; runs inside its exception isolation) -----------
    def on_event(self, snapshot: EngineSnapshot) -> None:
        """Advance the sustain clock against this event's tape state; fire ONCE past the dwell.

        Pure read of the snapshot (read-only over the engine — no engine/feature mutation). Logical-time
        only: the dwell + cooldown measure ``snapshot.timestamp`` deltas. A non-live stream never sustains
        a hint (an event arriving while the snapshot is not live clears any active hint — defensive; the
        status seam is the primary freshness path)."""
        # Freshness: a present-tense "is forming" hint must never sit over a non-live tape (J-64).
        if snapshot.stream_status != "live":
            self._clear_active()
            self._pending_pattern = None
            self._pending_since = None
            return

        state = snapshot.tape_state
        logical = snapshot.timestamp
        pattern = _STATE_TO_PATTERN.get(state)

        if pattern is None:
            # ``unclear`` (or any non-arming state) — the premise is broken; reset the sustain clock and
            # clear any active hint (its pattern's state has left).
            self._pending_pattern = None
            self._pending_since = None
            self._clear_active()
            return

        # The premise state changed -> restart the sustain clock at THIS logical instant. Any active hint
        # for a now-departed pattern is cleared (its state left). A continuing same-pattern active hint is
        # left in place (it stays active while its state persists).
        if pattern != self._pending_pattern:
            self._pending_pattern = pattern
            self._pending_since = logical
            if self._active is not None and self._active.get("pattern_id") != pattern:
                self._clear_active()

        # If a hint for THIS pattern is already active, keep it (active while its state persists) — no
        # re-fire until the cooldown lets it (which only matters after it clears).
        if self._active is not None and self._active.get("pattern_id") == pattern:
            return

        held_for = logical - (self._pending_since if self._pending_since is not None else logical)
        if held_for < self._config.hint_sustain_dwell_seconds:
            return  # premise not sustained past the dwell yet

        # Cooldown: gate a re-fire of the SAME pattern within the window (logical-time).
        last_fired = self._last_fired_logical.get(pattern)
        if last_fired is not None and (logical - last_fired) < self._config.hint_cooldown_seconds:
            # Within the cooldown — do NOT fire a new record, but the premise IS sustained, so the dock
            # would otherwise show nothing; the spec gates RE-FIRES (new log records), not the visibility
            # of the sustained state. We leave no active hint here (the previous one cleared on
            # state-leave); a re-fire is suppressed until the cooldown elapses.
            return

        self._fire(snapshot, pattern, held_for)

    def on_status(self, status: str) -> None:
        """Clear the active hint on any non-live status flip (paused / stale / closed / failed) — the
        present-tense copy must never sit over a non-live tape (J-64). The sustain clock is also reset so
        a resume re-accrues the dwell from scratch (a paused gap is not sustained tape). Clearing never
        touches the persisted log record (the log survives every status flip)."""
        if status != "live":
            self._clear_active()
            self._pending_pattern = None
            self._pending_since = None

    # --- firing + projection ----------------------------------------------------------------------
    def _fire(self, snapshot: EngineSnapshot, pattern: str, held_for: float) -> None:
        """Produce the hint record ONCE and persist it through the single writer queue.

        Builds the full payload (pattern, plain-language evidence with the measured sustain duration,
        setup-type context + direction, baseline citation, honesty stamps, logical + wall ts), persists
        it via ``insert_hint`` (the writer queue — never the event/WS path), records the cooldown anchor,
        and sets it as the active projection. A persist failure RAISES so the monitor's try/except flips
        ``monitor_status: failed`` (the feeder stays alive) — no half-state: no active hint, no cooldown
        anchor advanced, on failure."""
        spec = HINT_PATTERNS[pattern]
        setup_type = spec["setup_type"]
        direction = spec["direction"]
        data_feed = data_feed_for_scenario(snapshot.scenario, self._config)
        fingerprint = self._config.config_fingerprint()
        citation = _baseline_citation(
            self._store,
            setup_type=setup_type,
            data_feed=data_feed,
            config_fingerprint=fingerprint,
        )
        payload = {
            "id": uuid.uuid4().hex,
            "ticker": self._ticker,
            "pattern_id": pattern,
            "pattern_label": hint_pattern_label(pattern),
            "evidence": hint_evidence(pattern, held_for),
            "setup_type": setup_type,
            "direction": direction,
            "baseline_citation": citation,
            "bound_source": snapshot.scenario,
            "data_feed": data_feed,
            "config_fingerprint": fingerprint,
            "logical_ts": snapshot.timestamp,
            "wall_ts": time.time(),
        }
        record = HintRecord(
            id=payload["id"],
            ticker=self._ticker,
            payload=payload,
            created_wall_ts=payload["wall_ts"],
        )
        # Persist FIRST (through the writer queue). A failure raises out to the monitor's try/except
        # before any in-memory state is advanced, so a failed write never leaves a phantom active hint or
        # a falsely-advanced cooldown.
        self._store.insert_hint(record)
        self._last_fired_logical[pattern] = snapshot.timestamp
        self._active = payload

    def _clear_active(self) -> None:
        """Clear the live active-hint projection (never touches the persisted log record)."""
        self._active = None

    def projection(self) -> dict | None:
        """The active-hint projection (the dock read), or ``None`` (a NORMAL state, not an error).

        Both ``GET /research/hints/active`` and the WS ``hint`` key call THIS one function, so the two
        are verbatim-equal by construction (data-contract row 22). The projection is the fired record's
        payload verbatim — the log record and the live projection are the same dict (single source of
        truth; the dock never recomputes evidence or citation)."""
        return self._active
