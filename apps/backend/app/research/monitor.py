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

The entry risk flags (capability 26, J-49) are computed ONCE at declaration by ``compute_risk_flags``
(invoked from ``POST /research/thesis`` where ``entry_context`` is frozen) and stored verbatim on the
thesis; ``build_projection`` re-exposes the FROZEN list verbatim as the additive ``risk_flags`` key
(omitting the key entirely for a pre-v4 thesis that was never assessed — an absent key and an empty
list are distinct honest states). Flags are never recomputed at read and never a second computation
path — exactly the geometry pattern.
"""

from __future__ import annotations

import logging
import time

from ..config import Config
from ..engine.snapshot import EngineSnapshot
from .execution_checks import compute_and_persist_execution_checks
from .marks import marks_projection
from .store import JournalStore, ThesisRecord, VerdictEventRecord
from .taxonomy import (
    GEOMETRY_ENTRY_MARK_LABEL,
    GEOMETRY_EXIT_MARK_LABEL,
    GEOMETRY_FIRST_CONFIRMATION_LABEL,
    GEOMETRY_INVALIDATION_LINE_LABEL,
    GEOMETRY_LEVEL_LINE_LABEL,
    against_expected_tape_evidence,
    before_warmup_evidence,
    chasing_entry_evidence,
    invalidation_too_tight_evidence,
    low_trade_speed_evidence,
    mismatched_source_notice,
    risk_flag_label,
    verdict_marker_label,
    wide_spread_illiquid_evidence,
)
from .verdict import VerdictEvaluator

# Timeline rows that are GAP/segment delimiters, not published verdict transitions: they are never
# drawn as verdict markers (capability 25 / J-48). ``watch_restarted`` ALSO delimits the current
# watch's drawable segment (the honest segment rule below). ``paused`` / ``stale`` join it here when
# those gap rows are appended (forward-compatible; only ``watch_restarted`` is written today).
_GAP_VERDICTS: frozenset[str] = frozenset({"watch_restarted", "paused", "stale"})

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
        # Progress in the thesis direction is judged by a TRUE favorable-vs-adverse DOMINANCE
        # comparison (iter-8 fix), not the adverse-fires-first ordering of iter-6/7 (which branded a
        # cleanly CONFIRMING SIM-BUYER tape — buy +0.42 dominating a minority sell −0.14 — "violated"
        # one line under evidence saying the tape confirms). It composes ONLY the existing
        # primary-window ``buy_price_impact`` / ``sell_price_impact`` values, read verbatim from the
        # snapshot (single source of truth — never recomputed), against the classifier's OWN
        # config-owned real-price-progress cutoffs (no magic number in research code): a side is
        # "material" when its impact clears that cutoff (``buy_price_impact >= min_buy_price_impact`` /
        # ``sell_price_impact <= max_sell_price_impact``). For a LONG thesis the favorable side is
        # buying and the adverse side is selling; for a SHORT thesis the sides swap.
        #
        # Semantics (direction-aware; the SHORT case is the exact symmetric mirror):
        #   * neither side material            => not_yet  (no evidence is not a failure)
        #   * only the favorable side material => met
        #   * only the adverse side material   => violated
        #   * BOTH material                    => the side with the larger impact MAGNITUDE rules
        #       (favorable dominant => met; adverse dominant => violated). A plain magnitude
        #       comparison — no tolerance/ratio is needed, so no new config value/literal is
        #       introduced (and the config fingerprint is unchanged by this fix).
        #
        # Truth anchors (the four-quadrant + flat tests pin these): SIM-BUYER long (buy +0.42 vs sell
        # −0.14) => met; SIM-SELLER long (sell ~−0.28 dominant) => violated; SIM-BUYER short =>
        # violated; SIM-SELLER short => met. The iter-6 direction-awareness is preserved: an
        # incidentally positive buy_impact on a genuinely falling tape still reads violated for a
        # long because the dominant (adverse) sell impact wins.
        primary = snap.primary_features
        buy_impact = primary.get("buy_price_impact", 0.0)
        sell_impact = primary.get("sell_price_impact", 0.0)
        if direction == "long":
            favorable_impact = buy_impact
            adverse_impact = sell_impact
            favorable = buy_impact >= config.min_buy_price_impact
            adverse = sell_impact <= config.max_sell_price_impact
        else:
            favorable_impact = sell_impact
            adverse_impact = buy_impact
            favorable = sell_impact <= config.max_sell_price_impact
            adverse = buy_impact >= config.min_buy_price_impact

        if not favorable and not adverse:
            return "not_yet"
        if favorable and not adverse:
            return "met"
        if adverse and not favorable:
            return "violated"
        # Both sides are material — the dominant side (by impact magnitude) rules.
        return "met" if abs(favorable_impact) > abs(adverse_impact) else "violated"

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


def _build_geometry(
    thesis: ThesisRecord,
    verdict_events: list,
    marks: dict,
) -> dict:
    """The chart-ready ``geometry`` for a thesis (capability 25 / J-48) — a PURE projection.

    Computed ONCE inside ``build_projection`` (the single row-15 builder) from canonical owners
    ONLY — the declared thesis prices, the append-only verdict timeline (row 16), and the row-18
    action marks already computed by ``marks_projection``. It recomputes NO side/state/price/time
    basis (the chart draws this verbatim on the row-13 epoch anchor); the timeline is never edited or
    recomputed here — its rows are re-exposed verbatim as markers.

    Shape::

        {
          "price_lines": [ {kind, price, label}, … ],   # invalidation always; level only when set
          "markers":     [ {kind, …}, … ],              # verdict transitions + marks + 1st-confirm
        }

    Honest segment rule: only events placeable on the CURRENT watch's logical timeline are drawn —
    i.e. events at/after the latest ``watch_restarted`` gap event when one exists. A re-attached
    thesis's pre-gap events belong to a previous watch's timeline and would be MISPLACED on this
    watch's clock, so they are omitted from the chart (they remain fully visible in the journal
    timeline). Price-lines are time-independent and ALWAYS served.
    """
    # --- price-lines (time-independent; declared prices verbatim) ---------------------------------
    price_lines = [
        {
            "kind": "invalidation",
            "price": thesis.invalidation_price,
            "label": GEOMETRY_INVALIDATION_LINE_LABEL,
        }
    ]
    if thesis.level_price is not None:
        price_lines.append(
            {
                "kind": "level",
                "price": thesis.level_price,
                "label": GEOMETRY_LEVEL_LINE_LABEL,
            }
        )

    # --- segment boundary: the latest watch_restarted gap (current-watch events only) -------------
    # Rows are returned in insertion order (append-only ``id ASC``), so the LAST gap row index is the
    # boundary; everything strictly after it belongs to the current watch's drawable timeline. The
    # boundary is identified positionally for the timeline rows AND by its WALL time for the marks —
    # ``logical_ts`` RESETS per watch (the engine's per-stream logical clock), so it cannot discriminate
    # a pre-gap mark from a post-gap one; ``wall_ts`` is monotonic across re-watches (a re-watch always
    # happens later in real time), so a mark recorded BEFORE the latest restart's wall time belongs to
    # the previous watch's timeline and is omitted (it stays visible in the journal timeline).
    boundary_wall: float | None = None
    boundary_idx = -1
    for i, ev in enumerate(verdict_events):
        if ev.verdict == "watch_restarted":
            boundary_idx = i
            boundary_wall = ev.wall_ts
    current_rows = verdict_events[boundary_idx + 1 :] if boundary_idx >= 0 else verdict_events

    # --- verdict-transition markers (one per published transition; pure projection) ---------------
    markers: list[dict] = []
    first_confirmation_ts: float | None = None
    for ev in current_rows:
        if ev.verdict in _GAP_VERDICTS:
            continue  # a gap delimiter is never drawn as a verdict marker
        markers.append(
            {
                "kind": "verdict",
                "verdict": ev.verdict,
                "logical_ts": ev.logical_ts,
                "wall_ts": ev.wall_ts,
                "last": ev.last,
                "label": verdict_marker_label(ev.verdict),
            }
        )
        if ev.verdict == "confirming" and first_confirmation_ts is None:
            first_confirmation_ts = ev.logical_ts

    # --- the first-confirmation marker (identified once; only within the current segment) ---------
    if first_confirmation_ts is not None:
        markers.append(
            {
                "kind": "first_confirmation",
                "logical_ts": first_confirmation_ts,
                "label": GEOMETRY_FIRST_CONFIRMATION_LABEL,
            }
        )

    # --- entry / exit mark markers (verbatim; present ONLY when the mark exists) -------------------
    # Marks belonging to a PREVIOUS watch (recorded before the latest watch_restarted) are omitted by
    # the same segment rule: a pre-gap mark's logical_ts cannot be placed on the current watch's
    # clock. With no gap (the common case) every recorded mark is current and drawn.
    def _mark_in_segment(mark: dict | None) -> bool:
        if mark is None:
            return False
        if boundary_wall is None:
            return True
        return mark["wall_ts"] >= boundary_wall

    entry = marks.get("entry")
    if _mark_in_segment(entry):
        markers.append(
            {
                "kind": "entry",
                "price": entry["price"],
                "logical_ts": entry["logical_ts"],
                "wall_ts": entry["wall_ts"],
                "label": GEOMETRY_ENTRY_MARK_LABEL,
            }
        )
    exit_ = marks.get("exit")
    if _mark_in_segment(exit_):
        markers.append(
            {
                "kind": "exit",
                "price": exit_["price"],
                "logical_ts": exit_["logical_ts"],
                "wall_ts": exit_["wall_ts"],
                "label": GEOMETRY_EXIT_MARK_LABEL,
            }
        )

    return {"price_lines": price_lines, "markers": markers}


def _expected_tape_states(statements: list[dict]) -> list[str]:
    """The setup's expected tape states — the union of every ``tape_state_is`` statement's resolved
    ``states`` (direction already collapsed at ``frozen_statements``). The single source of truth for
    ``against_expected_tape`` (composes EXISTING engine states only — no new mapping table)."""
    expected: list[str] = []
    for s in statements:
        if s.get("kind") == "tape_state_is":
            for st in s.get("params", {}).get("states", []):
                if st not in expected:
                    expected.append(st)
    return expected


def compute_risk_flags(
    snapshot: EngineSnapshot,
    *,
    setup_type: str,
    direction: str,
    invalidation_price: float,
    statements: list[dict],
    config: Config,
) -> list[dict]:
    """Compute the capability-26 entry risk-flag set ONCE from the declaration-time snapshot + config.

    Called exactly once inside ``POST /research/thesis`` (where ``entry_context`` is frozen); the
    returned list is stored verbatim on the thesis and NEVER recomputed at read. Advisory only —
    creation always succeeds regardless of how many fire. Returns a (possibly empty) list of frozen
    entries, each ``{flag, label, evidence, measured}`` where:
      * ``flag``     — the canonical flag id (taxonomy ``RISK_FLAGS``);
      * ``label``    — the taxonomy-owned chip title (frozen so review reads it verbatim later);
      * ``evidence`` — the plain-language MEASURED margin (taxonomy-owned template, J-66 copy);
      * ``measured`` — the raw canonical values behind the flag (so review can show them with zero
                       recompute).

    Each flag READS canonical engine values verbatim (single source of truth) and REUSES the
    classifier's OWN gates — it never duplicates a threshold:
      * ``before_warmup``        — declaration trade count below ``warmup_min_events``;
      * ``invalidation_too_tight`` — |last − invalidation| below the new
        ``invalidation_too_tight_spread_multiple`` × current spread band;
      * ``chasing_entry``        — the favorable-side price-impact RETURN (direction-aware; the SAME
        ``buy_price_impact`` / ``sell_price_impact`` ÷ the canonical ``reference_price`` the classifier
        uses as its relative impact metric) already past the new ``chase_return_threshold``;
      * ``wide_spread_illiquid`` — the classifier's relative-spread gate VERBATIM (bps vs
        ``max_stable_spread_bps`` when a price basis exists, else absolute vs ``max_stable_spread``);
      * ``low_trade_speed``      — ``trade_speed`` below ``min_trade_speed`` VERBATIM;
      * ``against_expected_tape`` — a DEFINITE snapshot tape state (not ``unclear``) that is NOT among
        the setup's expected premise states (setup-aware; ``unclear`` is no contradiction so it never
        fires).
    """
    flags: list[dict] = []
    primary = snapshot.primary_features
    last = snapshot.last
    spread = snapshot.spread
    reference_price = primary.get("reference_price", 0.0)
    rel = reference_price > 0.0

    def _add(flag: str, evidence: str, measured: dict) -> None:
        flags.append(
            {
                "flag": flag,
                "label": risk_flag_label(flag),
                "evidence": evidence,
                "measured": measured,
            }
        )

    # --- before_warmup (reuses warmup_min_events verbatim) ---------------------------------------
    if snapshot.event_count < config.warmup_min_events:
        _add(
            "before_warmup",
            before_warmup_evidence(snapshot.event_count, config.warmup_min_events),
            {"trade_count": snapshot.event_count, "warmup_min_events": config.warmup_min_events},
        )

    # --- invalidation_too_tight (new spread multiple) --------------------------------------------
    # The invalidation distance vs the spread-multiple band. Needs both a last and a spread; without
    # either there is no measurable band, so the flag honestly does not fire (the wrong-side / no-last
    # cases are already a 422 in the route — a flag is never computed on an incoherent declaration).
    if last is not None and spread is not None and spread > 0:
        distance = abs(last - invalidation_price)
        band = spread * config.invalidation_too_tight_spread_multiple
        if distance < band:
            _add(
                "invalidation_too_tight",
                invalidation_too_tight_evidence(
                    distance, spread, config.invalidation_too_tight_spread_multiple
                ),
                {
                    "distance": distance,
                    "spread": spread,
                    "spread_multiple": config.invalidation_too_tight_spread_multiple,
                    "band": band,
                },
            )

    # --- chasing_entry (new return threshold; the favorable-side impact return, direction-aware) --
    # The favorable side's price-impact RETURN — the EXACT relative impact metric the classifier uses
    # (impact ÷ reference_price). For a long the favorable side is buying (buy_price_impact); for a
    # short it is selling (the |sell_price_impact| magnitude — a short profits as price falls). A
    # missing/zero basis means no return can be expressed, so the flag does not fire (never fabricated).
    if rel:
        buy_return = primary.get("buy_price_impact", 0.0) / reference_price
        sell_return = primary.get("sell_price_impact", 0.0) / reference_price
        if direction == "long":
            chase_return = buy_return
            side_copy = "buy"
        else:
            # A short chases a move that has already fallen — the adverse-to-price sell impact, whose
            # magnitude measures how far the favorable (downward) move has already run.
            chase_return = abs(sell_return)
            side_copy = "sell"
        if chase_return > config.chase_return_threshold:
            _add(
                "chasing_entry",
                chasing_entry_evidence(chase_return, config.chase_return_threshold, side_copy),
                {
                    "impact_return": chase_return,
                    "threshold": config.chase_return_threshold,
                    "side": side_copy,
                },
            )

    # --- wide_spread_illiquid (classifier relative-spread gate VERBATIM) -------------------------
    # The EXACT gate the classifier applies: relative (bps vs max_stable_spread_bps) when a price
    # basis exists, absolute (dollars vs max_stable_spread) otherwise. No second threshold (capability
    # 26's explicit constraint). Needs a spread to measure; absent => no flag (no fabricated read).
    if spread is not None:
        if rel:
            spread_metric = spread / reference_price * 10000.0
            max_spread = config.max_stable_spread_bps
            unit = "bps"
        else:
            spread_metric = spread
            max_spread = config.max_stable_spread
            unit = "dollars"
        if spread_metric > max_spread:
            _add(
                "wide_spread_illiquid",
                wide_spread_illiquid_evidence(spread_metric, max_spread, unit),
                {"spread_metric": spread_metric, "max_spread": max_spread, "unit": unit},
            )

    # --- low_trade_speed (min_trade_speed gate VERBATIM) -----------------------------------------
    trade_speed = primary.get("trade_speed", 0.0)
    if trade_speed < config.min_trade_speed:
        _add(
            "low_trade_speed",
            low_trade_speed_evidence(trade_speed, config.min_trade_speed),
            {"trade_speed": trade_speed, "min_trade_speed": config.min_trade_speed},
        )

    # --- against_expected_tape (setup-aware; composes existing states only) ----------------------
    # Fires when the tape reads a DEFINITE state at declaration that is NOT one the setup expects
    # (e.g. a long absorption_reversal declared during seller_control). ``unclear`` is NOT a
    # contradiction (no read yet), so it never fires — honest-uncertainty is not a risk flag.
    expected = _expected_tape_states(statements)
    tape_state = snapshot.tape_state
    if tape_state != "unclear" and tape_state not in expected:
        _add(
            "against_expected_tape",
            against_expected_tape_evidence(tape_state, expected),
            {"tape_state": tape_state, "expected_states": expected},
        )

    return flags


def build_projection(
    thesis: ThesisRecord,
    actions: list,
    *,
    config: Config,
    snapshot: EngineSnapshot | None,
    status: str,
    verdict: str,
    verdict_evidence: str,
    monitor_status: str,
    monitor_notice: str | None = None,
    verdict_events: list | None = None,
) -> dict:
    """The SINGLE thesis-projection builder (data-contract row 15) — one code path, never a second.

    Both the LIVE monitor (``ResearchMonitor.projection``) and the registry's UNWATCHED-survivor
    fallback (``GET /research/thesis/active`` for a stopped ticker whose entry-marked thesis
    survives) call THIS function, so a surviving thesis is served by the SAME projection path as a
    live one — never recomputed via a second route. Statement statuses are recomputed from the
    handed snapshot (``not_yet`` when there is none — an unwatched survivor accrues no new status).
    Action marks + realized-R come from the ONE ``marks_projection`` (shared with the journal-detail
    read). ``monitor_notice`` (optional) is the backend-owned plain-language lifecycle notice (the
    not-evaluated / mismatched-source copy) rendered VERBATIM by the strip — present only when set.

    ``verdict_events`` (the thesis's canonical append-only timeline rows, in insertion order) feeds
    the additive ``geometry`` key (capability 25 / J-48): a PURE projection of the declared prices +
    those timeline rows + the row-18 marks, computed ONCE here (never a second path, never recomputed
    at the chart). Callers hand the same single-writer rows used by the live and survivor paths; an
    omitted/``None`` list serves price-lines only (no markers) — never a fabricated timeline.
    """
    statements = [
        {
            "text": s["text"],
            "status": _evaluate_statement(s, snapshot, thesis, config)
            if snapshot is not None
            else "not_yet",
        }
        for s in thesis.statements
    ]
    marks = marks_projection(thesis, actions)
    geometry = _build_geometry(thesis, verdict_events or [], marks)
    projection = {
        "id": thesis.id,
        "ticker": thesis.ticker,
        "setup_type": thesis.setup_type,
        "direction": thesis.direction,
        "invalidation_price": thesis.invalidation_price,
        "level_price": thesis.level_price,
        "status": status,
        "verdict": verdict,
        "verdict_evidence": verdict_evidence,
        "statements": statements,
        "entry_context": thesis.entry_context,
        "bound_source": thesis.bound_source,
        "data_feed": thesis.data_feed,
        "config_fingerprint": thesis.config_fingerprint,
        "marks": marks,
        "geometry": geometry,
        "monitor_status": monitor_status,
    }
    # The additive ``risk_flags`` key (capability 26, J-49): re-expose the FROZEN stored list verbatim
    # (never recomputed here — computed once at declaration by ``compute_risk_flags``). Honest-omission
    # semantics: ``None`` (a pre-v4 thesis, never assessed) OMITS the key entirely; an empty list
    # (assessed, nothing fired) is served as ``[]`` — the two states never collapse.
    if thesis.risk_flags is not None:
        projection["risk_flags"] = thesis.risk_flags
    if monitor_notice is not None:
        projection["monitor_notice"] = monitor_notice
    return projection


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
        self._expiry_reason: str | None = None  # the recorded reason on an ``expired`` resolution
        # The verdict-transition engine (capability 24). Created when a thesis is set; the dwell
        # restarts at thesis creation by construction (a fresh evaluator). The PUBLISHED verdict +
        # evidence the projection serves live below.
        self._evaluator: VerdictEvaluator | None = None
        self._verdict = "pending"
        self._verdict_evidence = ""
        # The engine this monitor is attached to (set by the registry at attach time). Read in
        # ``on_status`` to distinguish a user Stop (``watch_stopped``) from a stream that ran out
        # (``stream_closed``) — both flip the engine status to ``closed``, so the reason lives on the
        # engine, not the status string.
        self._engine: object | None = None
        # J-47 re-attach: a SURVIVING entry-marked thesis handed to a FRESH monitor on re-watch. It is
        # only ADOPTED once the first snapshot confirms the new watch's source identity equals the
        # thesis's bound_source (the source descriptor is known at/after the first snapshot, NOT at
        # engine construction). Until then the monitor serves the not-evaluated projection. On a
        # MISMATCH it is never adopted (the projection carries the bound-source notice).
        self._adopt_candidate: ThesisRecord | None = None
        self._adopt_decided = False        # has the first post-restart snapshot resolved adopt/mismatch?
        self._adopt_mismatch = False       # the first snapshot's source differed from bound_source
        self._restart_gap_appended = False # the single watch_restarted gap event has been appended

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

    def attach_engine(self, engine: object) -> None:
        """Remember the engine this monitor observes (set by the registry at attach time).

        Read in ``on_status`` to learn WHY a terminal flip happened (``engine.end_reason``) —
        ``watch_stopped`` (user Stop) vs ``stream_closed`` (the stream ran out) — which the status
        string alone cannot tell apart."""
        self._engine = engine

    def offer_surviving(self, thesis: ThesisRecord) -> None:
        """Hand a SURVIVING entry-marked thesis to this FRESH monitor on re-watch (J-47).

        The thesis is NOT adopted yet: the new watch's source identity is only known at/after the
        first snapshot. ``on_event`` adopts it (appending exactly one ``watch_restarted`` gap event
        and resuming evaluation) iff the first snapshot's ``scenario`` equals the thesis's
        ``bound_source``; on a mismatch it is never adopted and the projection carries the
        bound-source notice. Until the first snapshot the not-evaluated projection is served."""
        self._adopt_candidate = thesis
        self._adopt_decided = False
        self._adopt_mismatch = False
        self._restart_gap_appended = False

    def clear_thesis(self) -> None:
        self._thesis = None
        self._resolved = False
        self._resolution = None
        self._evaluator = None
        self._verdict = "pending"
        self._verdict_evidence = ""
        self._adopt_candidate = None
        self._adopt_decided = False
        self._adopt_mismatch = False
        self._restart_gap_appended = False

    def resolve_by_user(self, resolution: str) -> None:
        """Detach verdict evaluation after a USER resolution (played_out | abandoned), J-50.

        The route has already flipped the persisted status + appended the final timeline event
        atomically; this only updates the in-memory monitor so that (a) the hot-path
        ``_evaluate_verdict`` stops appending verdict events for this thesis (it early-returns while
        ``_resolved``), and (b) the projection clears to ``None`` — a user resolution returns the
        strip to the idle declare affordance (distinct from the system-owned ``invalidated``
        treatment, which the strip KEEPS visible). ``active_thesis_id`` then reads ``None``, so a
        redeclare on the same ticker succeeds (no 409). Called from the route, NEVER the hot path."""
        self._resolved = True
        self._resolution = resolution

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
            self._maybe_adopt_surviving(snapshot)
            self._evaluate_verdict(snapshot)
        except Exception:
            self._failed = True
            logger.exception("research monitor on_event failed")

    def _maybe_adopt_surviving(self, snapshot: EngineSnapshot) -> None:
        """Re-attach a surviving entry-marked thesis to THIS watch iff the source matches (J-47).

        The decision is made ONCE, at the first snapshot after the offer (the source descriptor is
        known then, not at engine construction). On a MATCH (``snapshot.scenario`` == the thesis's
        ``bound_source``): adopt — hold the thesis active again, start a FRESH evaluator (the dwell
        restarts at re-attach so post-restart evidence is required by construction), and append
        EXACTLY ONE ``watch_restarted`` gap event to the append-only timeline (never edited /
        backfilled). On a MISMATCH (a different sim scenario, or live vs historical of the same
        symbol): do NOT adopt — record the mismatch so the projection carries the explicit
        bound-source notice and NO verdict is ever appended against the wrong source. Idempotent: a
        second snapshot does not append a second gap event (``_restart_gap_appended`` guards it)."""
        candidate = self._adopt_candidate
        if candidate is None or self._adopt_decided:
            return
        self._adopt_decided = True
        if snapshot.scenario != candidate.bound_source:
            # Source mismatch — never adopt, never evaluate against the wrong source (anti-goal).
            self._adopt_mismatch = True
            return
        # Source matches — adopt the surviving thesis and resume evaluation from post-restart
        # evidence only (a fresh evaluator => the dwell restarts here).
        self._thesis = candidate
        self._resolved = False
        self._resolution = None
        self._evaluator = VerdictEvaluator(candidate, self._config)
        self._verdict = "pending"
        self._verdict_evidence = (
            "The watch resumed on the source this thesis was declared on; the verdict stays pending "
            "until sustained post-restart evidence accrues."
        )
        if not self._restart_gap_appended:
            self._store.append_verdict_event(
                VerdictEventRecord(
                    thesis_id=candidate.id,
                    logical_ts=snapshot.timestamp,
                    wall_ts=time.time(),
                    verdict="watch_restarted",
                    evidence=(
                        "Watch restarted on the matching source — evaluation resumes from here; "
                        "the gap while unwatched carries no verdicts."
                    ),
                    tape_state=snapshot.tape_state,
                    confidence=snapshot.confidence,
                    last=snapshot.last,
                )
            )
            self._restart_gap_appended = True
        self._adopt_candidate = None

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
                # Compute the machine-derived execution checks ONCE at this terminal resolution and
                # persist them (capability 27, J-54 — the SAME single function the user-resolve,
                # stream-end-expiry, and restart-sweep paths call; the journal detail serves them
                # verbatim, never recomputed at read). Runs inside ``on_event``'s try/except, so a
                # checks failure surfaces as ``monitor_status: failed`` and never kills the feeder; the
                # already-committed invalidation still stands (the key just stays honestly absent).
                compute_and_persist_execution_checks(
                    self._store, self._thesis.id, self._config
                )
                self._resolved = True
                self._resolution = "invalidated"

    def on_status(self, status: str) -> None:
        # Lifecycle honesty (capability 24, J-47): a terminal stream status resolves an UNMARKED
        # active thesis ``expired(reason)`` with a final appended timeline event — BUT an
        # entry-marked thesis (a real position) is NEVER orphaned: it SURVIVES as
        # active-but-not-evaluated (stays ``active`` in the store, NO verdict events appended while
        # unwatched, projection says so). ``closed`` (stop / stream exhaustion) and ``failed``
        # (feeder raised) are terminal; ``paused``/``stale`` are not.
        #
        # The expiry REASON distinguishes a user Stop (``watch_stopped``) from a stream that ran out
        # (``stream_closed`` — J-50's verified leg must not regress) from a feed failure (``failed``).
        # The status string alone cannot tell stop from exhaustion (both are ``closed``); the
        # distinguishing reason lives on the engine (``end_reason``), stamped by the WatchManager.
        try:
            if status in ("closed", "failed") and self._thesis is not None and not self._resolved:
                # A real position must never be orphaned: an entry-marked thesis survives.
                if self._store.has_entry_mark(self._thesis.id):
                    self._detach_not_evaluated()
                    return
                self._expire_active(status=status)
        except Exception:
            self._failed = True
            logger.exception("research monitor on_status failed")

    def _detach_not_evaluated(self) -> None:
        """Survive a stop/failure as active-but-not-evaluated (J-47): the entry-marked thesis stays
        ``active`` in the store, NO verdict event is appended, and this monitor stops evaluating it.

        The thesis is NOT held active in THIS dead monitor any longer (the watch is over) — the
        persisted ``active`` row is authoritative, and the registry serves its not-evaluated
        projection from that row via the SAME projection builder until the matching source is
        re-watched (then a fresh monitor adopts it with a ``watch_restarted`` gap event)."""
        self._thesis = None
        self._evaluator = None

    def _terminal_reason(self, status: str) -> str:
        """Map a terminal stream status to the recorded expiry reason (J-47 / J-50).

        ``failed`` is a feed failure. ``closed`` is refined by the engine's ``end_reason`` into a
        user Stop (``watch_stopped``) vs a stream that ran out (``stream_closed``) — the status
        string alone cannot tell them apart, so the WatchManager stamps the reason on the engine."""
        if status == "failed":
            return "failed"
        engine_reason = getattr(self._engine, "end_reason", None)
        if engine_reason in ("watch_stopped", "stream_closed"):
            return engine_reason
        # No engine reason available (a direct status flip in a test, or a legacy path): default to
        # ``stream_closed`` so J-50's already-verified stream-end leg is preserved by default.
        return "stream_closed"

    def _expire_active(self, status: str) -> None:
        thesis = self._thesis
        if thesis is None:
            return
        reason = self._terminal_reason(status)
        wall = time.time()
        logical = self._last_snapshot.timestamp if self._last_snapshot is not None else 0.0
        last = self._last_snapshot.last if self._last_snapshot is not None else None
        detail = {
            "watch_stopped": "Thesis expired — you stopped the watch that declared it.",
            "stream_closed": "Thesis expired — the stream that declared it ended.",
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
            # Compute the machine-derived execution checks ONCE at this terminal (expiry) resolution
            # and persist them (capability 27, J-54 — the SAME single function the user-resolve,
            # system-invalidation, and restart-sweep paths call). An expired thesis here is UNMARKED
            # (an entry-marked thesis is exempt and survives via ``_detach_not_evaluated``), so its
            # mark-dependent checks read ``not_applicable`` honestly — never a fabricated pass/fail.
            compute_and_persist_execution_checks(self._store, thesis.id, self._config)
            self._resolved = True
            self._resolution = "expired"
            self._expiry_reason = reason
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

        Mismatched-source survivor (J-47): if this fresh monitor was OFFERED a surviving entry-marked
        thesis but the first snapshot's source differed from its ``bound_source``, the thesis is
        NEVER adopted (no verdicts ever appended against the wrong source) — the projection is served
        from the surviving record with ``monitor_status: not_evaluated`` and the explicit
        bound-source notice naming the declared source. The same single ``build_projection`` path is
        used (never a second computation).
        """
        # Mismatched-source survivor: serve the surviving record as not-evaluated with the explicit
        # bound-source notice (never adopted, never evaluated against the wrong source).
        if self._thesis is None and self._adopt_mismatch and self._adopt_candidate is not None:
            candidate = self._adopt_candidate
            watched = (
                self._last_snapshot.scenario if self._last_snapshot is not None else "this source"
            )
            return build_projection(
                candidate,
                self._store.get_actions(candidate.id),
                config=self._config,
                snapshot=None,
                status=candidate.status,
                verdict="pending",
                verdict_evidence=(
                    "The watch is on a different source than this thesis was declared on, so the "
                    "tape is not being judged against it."
                ),
                monitor_status="not_evaluated",
                monitor_notice=mismatched_source_notice(candidate.bound_source, watched),
                verdict_events=self._store.verdict_events(candidate.id),
            )
        thesis = self._thesis
        if thesis is None:
            return None
        if self._resolved and self._resolution != "invalidated":
            return None
        # A resolved-invalidated thesis reports its terminal status/verdict; otherwise the active
        # thesis reports its declared status and the live published verdict. Both go through the ONE
        # shared ``build_projection`` (data-contract row 15 — never a second computation path).
        status = "invalidated" if self._resolution == "invalidated" else thesis.status
        # A read failure inside the builder (e.g. the action read) is caught by the caller's
        # try/except and surfaces as ``monitor_status: failed`` rather than a crash.
        return build_projection(
            thesis,
            self._store.get_actions(thesis.id),
            config=self._config,
            snapshot=self._last_snapshot,
            status=status,
            verdict=self._verdict,
            verdict_evidence=self._verdict_evidence,
            monitor_status="failed" if self._failed else "ok",
            verdict_events=self._store.verdict_events(thesis.id),
        )
