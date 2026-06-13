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
from .excursions import ExcursionTracker, compute_and_persist_excursions
from .feed_basis import data_feed_for_scenario
from .execution_checks import compute_and_persist_execution_checks
from .grades import compute_and_persist_grades
from .hints import HintEngine
from .marks import marks_projection
from .stance import (
    EntryChecklistEvaluator,
    StanceEvaluator,
    build_checklist,
    compute_position_readouts,
)
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
    management_stance_label,
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

# ``data_feed_for_scenario`` is the ONE consolidated scenario -> ``data_feed`` mapping, owned by the
# leaf ``feed_basis`` module (data-contract row 26, iter-24). It is re-exported here (imported above)
# so existing ``from app.research.monitor import data_feed_for_scenario`` call sites keep resolving;
# the single DEFINITION lives in ``feed_basis`` (no parallel copy — the hints.py duplicate is gone).
__all__ = ["data_feed_for_scenario"]


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


# --- Per-statement FINAL statuses, persisted ONCE at terminal resolution (J-55) -----------------
# A FINAL-status-only enum value: where no live evaluation context exists at the terminal moment
# (e.g. the restart-expiry sweep over an unwatched thesis), each statement records this explicit,
# honest enum — never fabricated, never recomputed at read.
_NOT_EVALUATED = "not_evaluated"


def compute_final_statement_statuses(
    thesis: ThesisRecord, snapshot: EngineSnapshot | None, config: Config
) -> list[dict]:
    """The FINAL status of each frozen statement at the terminal moment (J-55), computed ONCE.

    For a live-monitored terminal path (user resolve while still watched, system invalidation,
    stream-end expiry) the snapshot is the engine's read at the terminal moment, and each statement's
    final status is its at-resolution evaluation from the SAME ``_evaluate_statement`` the live
    projection uses (one owner — no second evaluation rule). Where no live context exists (the
    restart-expiry sweep over an unwatched thesis, ``snapshot is None``) every statement records the
    explicit ``not_evaluated`` enum — an honest "no read at the terminal moment", never a fabricated
    met/violated.

    Returns one ``{"status": <enum>}`` entry per frozen statement, in statement order. The frozen
    ``statements`` JSON is NEVER mutated — this is an additive parallel list keyed positionally to it.
    """
    if snapshot is None:
        return [{"status": _NOT_EVALUATED} for _ in thesis.statements]
    return [
        {"status": _evaluate_statement(s, snapshot, thesis, config)}
        for s in thesis.statements
    ]


def compute_and_persist_final_statuses(
    store: JournalStore,
    thesis_id: str,
    snapshot: EngineSnapshot | None,
    config: Config,
) -> list[dict] | None:
    """Compute the per-statement FINAL statuses for a just-resolved thesis ONCE and persist them.

    The single entry point every terminal-resolution path calls right after the resolution: reads the
    thesis back from the store, computes the final statuses via the pure
    :func:`compute_final_statement_statuses` (using the handed terminal-moment ``snapshot``, or an
    explicit ``not_evaluated`` per statement when there is none), and persists via
    ``store.set_statement_final_statuses`` — so the statuses are recorded exactly ONCE at the defining
    moment, never recomputed at read. Returns the computed list (or ``None`` if the thesis is gone).
    Idempotent guard: if the thesis already carries final statuses (a double-resolve race), it is NOT
    recomputed — the first computation stands (append-only spirit)."""
    thesis = store.get_thesis(thesis_id)
    if thesis is None:
        return None
    if thesis.statement_final_statuses is not None:
        return thesis.statement_final_statuses
    result = compute_final_statement_statuses(thesis, snapshot, config)
    store.set_statement_final_statuses(thesis_id, result)
    return result


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
    management_stance: str | None = None,
    management_stance_evidence: str | None = None,
    entry_checklist: dict | None = None,
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

    ``management_stance`` + ``management_stance_evidence`` (capability 27 / J-53; row 25 stance half)
    are the live monitor's PUBLISHED holding-period stance (computed once by the ``StanceEvaluator``
    from the latest published verdict, dwell-gated). The additive ``management_stance`` /
    ``distance_to_invalidation`` / ``open_r`` keys are served ONLY when the thesis is ENTRY-MARKED AND
    a stance is supplied (a live monitor passes one; the unwatched-survivor + not-evaluated paths pass
    ``None`` so the keys stay ABSENT — no frozen-stale stance). The position readouts come from the
    SAME single ``r_basis()`` helper the marks use (row 27 — the stance is its fifth registered
    consumer, never a second formula). Nothing here is persisted (schema stays v7).

    ``entry_checklist`` (capability 33 / J-63; row 25 checklist half) is the live monitor's PUBLISHED
    entry checklist (the eight checks + their live margins, the dwell-published aggregate stance, the
    blocker list, and the nearest-counterevidence line — computed ONCE by ``build_checklist`` from
    canonical values). The additive ``entry_checklist`` key is served ONLY on the PRE-ENTRY-MARK cue
    path (active + NO entry mark) — MUTUALLY EXCLUSIVE with the management stance (entry-marked) above;
    the survivor / not-evaluated / failed paths pass ``None`` so the key stays ABSENT.
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

    # --- Management stance + live position readouts (capability 27, J-53; row 25 stance half) ------
    # Served ONLY while the thesis is ENTRY-MARKED AND a published stance was supplied (a live monitor
    # passes one; the unwatched-survivor / not-evaluated paths pass ``None`` so the keys stay ABSENT —
    # NO frozen-stale stance, distinct from the "no entry mark yet" absence the strip handles with its
    # own copy). The readouts come from the ONE ``r_basis()`` helper (row 27, fifth registered
    # consumer). Nothing here is persisted (schema v7). An ``invalidated`` terminal stance is still a
    # stance: it renders at/after the auto-resolve moment as the terminal treatment.
    entry = marks.get("entry")
    if management_stance is not None and entry is not None:
        last = snapshot.last if snapshot is not None else None
        readouts = compute_position_readouts(
            entry_price=entry["price"],
            invalidation_price=thesis.invalidation_price,
            direction=thesis.direction,
            last=last,
        )
        projection["management_stance"] = {
            "value": management_stance,
            "evidence": management_stance_evidence or "",
            "label": management_stance_label(management_stance),
        }
        projection["distance_to_invalidation"] = readouts["distance_to_invalidation"]
        projection["open_r"] = readouts["open_r"]

    # --- Entry checklist (capability 33, J-63; row 25 checklist half) -------------------------------
    # Served ONLY on the PRE-ENTRY-MARK cue path — active status, NO entry mark, and a checklist was
    # supplied (a live evaluating monitor passes one; the unwatched-survivor / not-evaluated / failed
    # paths pass ``None`` so the key stays ABSENT). MUTUALLY EXCLUSIVE with the management stance above:
    # an entry-marked thesis shows the management stance and NO checklist; a pre-entry-mark thesis shows
    # the checklist and NO management stance. A resolved (played_out / abandoned) thesis is not active,
    # so an ``invalidated`` terminal projection never carries the checklist (status != active). Nothing
    # here is persisted (schema v7); the strip renders every field verbatim (zero client arithmetic).
    if entry_checklist is not None and entry is None and status == "active":
        projection["entry_checklist"] = entry_checklist
    return projection


class ResearchMonitor:
    """Holds one ticker's active thesis and serves its live projection (capability 20 observer)."""

    def __init__(self, store: JournalStore, config: Config, ticker: str = "") -> None:
        self._store = store
        self._config = config
        self._config_fingerprint = config.config_fingerprint()
        self._ticker = ticker
        # The setup-forming hint engine (capability 33, J-65) — attached at engine creation REGARDLESS of
        # any thesis (a hint fires on the watched ticker with NO thesis declared, exactly what J-65 step 1
        # requires). Observer-only, exception-isolated within ``on_event`` / ``on_status`` (a hint failure
        # surfaces as ``monitor_status: failed`` and never kills the feeder). Independent of the
        # thesis-lifecycle state below — it survives thesis declare/resolve and serves its own projection.
        self._hints = HintEngine(store, config, ticker)
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
        # The in-memory excursion tracker (capability 30, J-58) for the active thesis. Created when a
        # thesis is set / adopted (it needs the invalidation + direction); fed by ``on_event``; armed
        # at the first published ``confirming`` and at the recorded entry mark; SNAPSHOTTED + persisted
        # ONCE at the terminal resolution / stream-end. ``None`` when no thesis is held. The tracker
        # reads ONLY the snapshot (read-only over the engine) — no tape data is persisted, only the
        # R-unit excursion summaries.
        self._excursions: ExcursionTracker | None = None
        # The management-stance evaluator (capability 27, J-53). Created when a thesis is set / adopted;
        # advanced per event AFTER the verdict step (it reads the just-published verdict). Holds the
        # PUBLISHED holding-period stance the projection serves while the thesis is entry-marked. Never
        # persisted (the stance is a live cue, schema stays v7). ``None`` when no thesis is held.
        self._stance: StanceEvaluator | None = None
        # The entry-checklist evaluator (capability 33, J-63). Created when a thesis is set / adopted;
        # advanced per event AFTER the verdict step (it reads the just-published verdict). Holds the
        # PUBLISHED aggregate checklist stance the projection serves while the thesis is active +
        # evaluated + NOT entry-marked. Never persisted (a live cue, schema stays v7). ``None`` when no
        # thesis is held.
        self._checklist: EntryChecklistEvaluator | None = None
        # The latest recorded ``rule_first_true`` price (capability 24) — the anchor the checklist's
        # ``not_chasing`` check measures the chase return FROM (never the post-dwell publish). Updated
        # on each published transition that carries one; ``None`` until a raw rule has first held.
        self._rule_first_true_price: float | None = None

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
        # A FRESH excursion tracker (capability 30, J-58) — keyed to this thesis's invalidation +
        # direction (the R basis + the favorable-side sense). It arms its confirmation population at
        # the first published ``confirming`` and its entry population at the recorded entry mark; both
        # populations stay segregated. Fed by ``on_event`` from here on.
        self._excursions = ExcursionTracker(
            invalidation_price=thesis.invalidation_price,
            direction=thesis.direction,
            config=self._config,
        )
        # A FRESH stance evaluator (capability 27, J-53) — its dwell clock starts here so the stance is
        # settled by the time the user marks entry (no artificial warm-up gap at the mark). It reads the
        # published verdict each event; the keys are SERVED only once an entry mark exists.
        self._stance = StanceEvaluator(self._config.management_stance_dwell_seconds)
        # A FRESH entry-checklist evaluator (capability 33, J-63) — its dwell clock starts here so the
        # aggregate stance is settled by the time the checklist is shown (active + evaluated + no entry
        # mark). It reads the published verdict + the snapshot each event; the keys are SERVED only on
        # the pre-entry-mark path (gated in ``build_projection``). The chase anchor resets here too.
        self._checklist = EntryChecklistEvaluator(self._config.checklist_stance_dwell_seconds)
        self._rule_first_true_price = None
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
        self._excursions = None
        self._stance = None
        self._checklist = None
        self._rule_first_true_price = None

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

    def arm_entry_excursions(
        self, *, logical_ts: float, wall_ts: float, price: float, spread_at_mark: float | None
    ) -> None:
        """Arm the excursion ENTRY population at the recorded entry mark (capability 30, J-58).

        Called from the action route (NOT the hot path) right after an ENTRY mark is recorded, so the
        entry-anchored population arms at the verbatim mark price + the moment spread ALREADY stamped
        on the action row (row 18 — reused, never re-stamped). The two populations stay segregated.
        Idempotent (the tracker keeps the first arming). A no-op when no tracker is held (the thesis
        was resolved / the watch ended) — the entry-mark API already refuses marks on a resolved
        thesis, so a held tracker is the normal case."""
        if self._excursions is None:
            return
        self._excursions.arm_entry(
            logical_ts=logical_ts,
            wall_ts=wall_ts,
            reference_price=price,
            spread_at_mark=spread_at_mark,
        )

    def persist_excursions_on_user_resolve(self, thesis_id: str) -> None:
        """Truncate any open horizon + persist the excursion record at a USER resolution (J-50/J-58).

        Called from the resolve route (NOT the hot path) right after the user resolves a thesis the
        live monitor still holds: the resolution is a terminal moment, so any open horizon is TRUNCATED
        (never bridged, never extrapolated) and the tracker's resolved state is persisted ONCE through
        the SAME single function every terminal path calls. Idempotent at the store level (a record
        already present is never reopened)."""
        if self._excursions is not None:
            self._excursions.truncate_open()
        compute_and_persist_excursions(self._store, thesis_id, self._excursions)

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
            # The setup-forming hint engine (capability 33, J-65) runs FIRST and REGARDLESS of any thesis
            # — a hint fires on the watched ticker with no thesis declared. Read-only over the snapshot;
            # its only write (a fired hint) goes through the store's single writer queue. A failure here
            # falls into the shared try/except below => ``monitor_status: failed``, feeder stays alive.
            self._hints.on_event(snapshot)
            self._maybe_adopt_surviving(snapshot)
            self._evaluate_verdict(snapshot)
            # Advance the management stance AFTER the verdict step (so it reads the verdict just
            # published for THIS snapshot). The stance is a pure derivation from the published verdict
            # (read-only over the engine — no engine/feature mutation) and is never persisted. An
            # ``invalidated`` verdict carries the offending-print evidence the verdict engine recorded
            # (now on ``self._verdict_evidence`` after the verdict step), so the terminal stance reads
            # the same facts. The stance keys are only SERVED once an entry mark exists (gated in the
            # projection); the dwell accumulates regardless so the stance is settled by the mark.
            if self._stance is not None:
                self._stance.advance(
                    verdict=self._verdict,
                    verdict_evidence=self._verdict_evidence,
                    logical_ts=snapshot.timestamp,
                    invalidation_evidence=(
                        self._verdict_evidence if self._verdict == "invalidated" else None
                    ),
                )
            # Advance the entry-checklist aggregate stance AFTER the verdict step (so it reads the
            # verdict just published for THIS snapshot, and the chase anchor reflects any transition).
            # Pure derivation from canonical values (read-only over the engine — no mutation); the
            # checks themselves are recomputed at projection time, only the dwelled STANCE lives here.
            # Served only on the pre-entry-mark path (gated in the projection); the dwell accumulates
            # regardless so the stance is settled when shown.
            if self._checklist is not None and self._thesis is not None and not self._resolved:
                checks = self._compute_checks(snapshot)
                self._checklist.advance(
                    checks=checks, verdict=self._verdict, logical_ts=snapshot.timestamp
                )
            # Advance the excursion tracker AFTER the verdict step (so a confirmation armed on THIS
            # snapshot also sees this snapshot as its dt=0 baseline). Read-only over the engine — the
            # tracker only reads the snapshot's logical ts + last (no engine/feature mutation).
            if self._excursions is not None and not self._resolved:
                self._excursions.on_event(snapshot)
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
        # A fresh tracker so the hot path stays safe; the surviving thesis's excursions were ALREADY
        # measured + persisted ONCE at the prior stream-end (the survival path), so the idempotent
        # guard in ``compute_and_persist_excursions`` never reopens them on a matching-source re-attach
        # (the spec's "never reopened on a matching-source re-attach"). This tracker's state is only
        # used if the thesis somehow lacks a record (defensive); it never overwrites a frozen one.
        self._excursions = ExcursionTracker(
            invalidation_price=candidate.invalidation_price,
            direction=candidate.direction,
            config=self._config,
        )
        # A FRESH stance evaluator on re-attach (capability 27, J-53): the adopted thesis is
        # entry-marked (only entry-marked theses survive to be re-offered), so its holding-period stance
        # resumes from post-restart published verdicts — its dwell restarts here by construction.
        self._stance = StanceEvaluator(self._config.management_stance_dwell_seconds)
        # A fresh checklist evaluator on re-attach (capability 33, J-63). The adopted thesis is
        # entry-marked (only entry-marked theses survive), so the checklist keys are NOT served on this
        # path (the projection gates on NO entry mark) — but the evaluator is created for consistency
        # and the chase anchor resets so a stale anchor never carries across the restart.
        self._checklist = EntryChecklistEvaluator(self._config.checklist_stance_dwell_seconds)
        self._rule_first_true_price = None
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
        # Capture the recorded ``rule_first_true`` price as the checklist's chase anchor (capability
        # 33 / J-63): the ``not_chasing`` check measures the chase return FROM the first instant the
        # raw rule held, NEVER the post-dwell publish. A transition that carries one updates the anchor;
        # it is never read off the post-dwell ``last``.
        if decision.rule_first_true_price is not None:
            self._rule_first_true_price = decision.rule_first_true_price
        if decision.changed:
            self._verdict_evidence = decision.evidence
            event_wall = time.time()
            self._store.append_verdict_event(
                VerdictEventRecord(
                    thesis_id=self._thesis.id,
                    logical_ts=decision.published_at_ts
                    if decision.published_at_ts is not None
                    else snapshot.timestamp,
                    wall_ts=event_wall,
                    verdict=decision.verdict,
                    evidence=decision.evidence,
                    tape_state=decision.tape_state,
                    confidence=decision.confidence,
                    last=decision.last,
                    rule_first_true_ts=decision.rule_first_true_ts,
                    rule_first_true_price=decision.rule_first_true_price,
                )
            )
            # Arm the excursion CONFIRMATION population ONCE at the FIRST published ``confirming``
            # (capability 30, J-58). The reference price is the ``last`` recorded on this published
            # timeline event (the basis the spec mandates — already persisted on the append-only
            # timeline); the spread-at-anchor is captured ONCE from the current snapshot; the anchor's
            # true-clock wall_ts is the same ``event_wall`` stamped on the timeline row. Re-confirmation
            # after weakening never re-arms (the tracker's own idempotent guard). The verdict step runs
            # inside ``on_event``'s try/except, so a tracker error surfaces as ``monitor_status: failed``
            # and never kills the feeder.
            if (
                decision.verdict == "confirming"
                and self._excursions is not None
                and decision.last is not None
            ):
                self._excursions.arm_confirmation(
                    snapshot, reference_price=decision.last, wall_ts=event_wall
                )
            if decision.invalidated:
                # System-owned auto-resolve via the existing resolution path (status row only — the
                # timeline row was just appended, never edited). The monitor stops holding the thesis
                # active; the projection then reflects the resolved/invalidated status (NOT a silent
                # revert to the idle declare affordance — the strip shows the terminal treatment).
                self._store.resolve_thesis(self._thesis.id, "invalidated")
                # Compute the machine-derived execution checks, the per-statement FINAL statuses
                # (J-55), and the outcome × process grades (J-56) ONCE at this terminal resolution and
                # persist them (capabilities 27/29 — the SAME single functions the user-resolve,
                # stream-end-expiry, and restart-sweep paths call; the journal detail serves them
                # verbatim, never recomputed at read). The grades weigh the just-persisted execution
                # checks, so they MUST run after them. The final statuses use the terminal-moment
                # snapshot (the at-invalidation engine read). Runs inside ``on_event``'s try/except, so
                # a failure surfaces as ``monitor_status: failed`` and never kills the feeder; the
                # already-committed invalidation still stands (each key just stays honestly absent).
                compute_and_persist_execution_checks(
                    self._store, self._thesis.id, self._config
                )
                compute_and_persist_final_statuses(
                    self._store, self._thesis.id, snapshot, self._config
                )
                compute_and_persist_grades(
                    self._store, self._thesis.id, "invalidated", self._config
                )
                # Excursions (capability 30, J-58): invalidation is a terminal moment for the thesis —
                # the price path stops mattering here, so any open horizon is TRUNCATED (never bridged
                # past the invalidation, never extrapolated) and the tracker's resolved state is
                # persisted ONCE. The SAME single function every other terminal path calls; the journal
                # detail serves it verbatim. A failure here surfaces as ``monitor_status: failed`` (it
                # runs inside ``on_event``'s try/except) and the key stays honestly absent.
                if self._excursions is not None:
                    self._excursions.truncate_open()
                compute_and_persist_excursions(
                    self._store, self._thesis.id, self._excursions
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
            # The setup-forming hint engine (capability 33, J-65) reacts to EVERY status flip REGARDLESS
            # of any thesis: a non-live status (paused / stale / closed / failed) clears any active hint
            # immediately (a present-tense "is forming" card must never sit over a non-live tape — the
            # iter-22 J-64 freshness lesson). Clearing never touches the persisted log record. Runs inside
            # this try/except so a hint-side failure surfaces ``monitor_status: failed``, feeder alive.
            self._hints.on_status(status)
            if status in ("closed", "failed"):
                # Terminal flips: resolve/detach an active thesis; never run the freshness refresh (a
                # closed/failed stream has nothing live to re-evaluate — the projection clears or
                # survives not-evaluated). A terminal flip with no active thesis is a clean no-op.
                if self._thesis is not None and not self._resolved:
                    # A real position must never be orphaned: an entry-marked thesis survives.
                    if self._store.has_entry_mark(self._thesis.id):
                        self._detach_not_evaluated()
                        return
                    self._expire_active(status=status)
            else:
                # FRESHNESS WIRING (iter-22 / J-64): a NON-terminal status flip — ``paused`` / ``stale``,
                # and the restored prior status on ``resume`` — carries NO event, so ``on_event`` (which
                # advances the checklist + management-stance dwell evaluators and refreshes
                # ``_last_snapshot``) never runs for it. Without this, the served checklist keeps reading
                # the snapshot captured at the LAST event (still ``stream_status: live``) and a frozen
                # green ``conditions_met`` persists over a paused/stale tape — the confirmed iter-21
                # defect. Here we RE-READ the engine's CURRENT canonical snapshot (the engine rebuilds
                # ``self._snapshot`` with the new ``stream_status`` / ``delivery_lag_seconds`` BEFORE it
                # notifies — this is a pure READ of the canonical row-6/row-14 owner, the iter-9
                # precedent, NEVER a second computation) and re-advance the dwell evaluators against it,
                # so the dwell-exempt ``no_fresh_tape`` publishes IMMEDIATELY (and resume restores honest
                # live evaluation). The pure ``stance.py`` logic is correct and is NOT re-derived.
                self._refresh_on_status_flip()
        except Exception:
            self._failed = True
            logger.exception("research monitor on_status failed")

    def _refresh_on_status_flip(self) -> None:
        """Re-advance the checklist + management-stance evaluators against the engine's CURRENT
        snapshot on a non-terminal status flip (paused / stale / resume-restore), so a flip that
        carries no event still degrades (or restores) the served stance immediately.

        Only acts when there is an active thesis to evaluate and an engine to read the current
        canonical snapshot from. Reads ``engine.snapshot()`` (the row-6 ``stream_status`` + row-14
        ``delivery_lag_seconds`` owner — a READ, never recomputed) and refreshes ``_last_snapshot`` so
        the projection-time per-check rows reflect the current status/lag too. The verdict is NOT
        advanced here (no event => no verdict transition); only the freshness-sensitive checklist /
        stance dwell evaluators are re-driven, exactly as ``on_event`` does after the verdict step.
        Runs inside ``on_status``'s try/except — a failure surfaces ``monitor_status: failed`` and the
        feeder stays alive."""
        if self._thesis is None or self._resolved:
            return
        engine = self._engine
        if engine is None:
            return
        snapshot_getter = getattr(engine, "snapshot", None)
        if snapshot_getter is None:
            return
        snapshot = snapshot_getter()
        if snapshot is None:
            return
        # Refresh the served read to the CURRENT canonical snapshot (carries the new status/lag).
        self._last_snapshot = snapshot
        # Re-advance the entry-checklist aggregate stance — its ``no_fresh_tape`` rule is dwell-exempt,
        # so the degradation (or, on resume, the restored read) publishes immediately. The per-check
        # rows are recomputed at projection time from this refreshed snapshot.
        if self._checklist is not None:
            checks = self._compute_checks(snapshot)
            self._checklist.advance(
                checks=checks, verdict=self._verdict, logical_ts=snapshot.timestamp
            )
        # Re-advance the management stance too (its dwell uses the same published verdict; a freshness
        # flip carries no verdict change, but keeping the stance current on the refreshed snapshot is
        # consistent and harmless — the management-stance enum has no freshness state, so a pause is a
        # row-16 gap event for J-53, not a stance change).
        if self._stance is not None:
            self._stance.advance(
                verdict=self._verdict,
                verdict_evidence=self._verdict_evidence,
                logical_ts=snapshot.timestamp,
                invalidation_evidence=(
                    self._verdict_evidence if self._verdict == "invalidated" else None
                ),
            )

    def _detach_not_evaluated(self) -> None:
        """Survive a stop/failure as active-but-not-evaluated (J-47): the entry-marked thesis stays
        ``active`` in the store, NO verdict event is appended, and this monitor stops evaluating it.

        The thesis is NOT held active in THIS dead monitor any longer (the watch is over) — the
        persisted ``active`` row is authoritative, and the registry serves its not-evaluated
        projection from that row via the SAME projection builder until the matching source is
        re-watched (then a fresh monitor adopts it with a ``watch_restarted`` gap event).

        Excursions (capability 30, J-58): the stream end IS the defining (truncation) moment for the
        excursion record even though NO resolution occurs (the thesis survives) — J-58's script ends
        exactly here, so the record MUST exist for the surviving thesis. Any open horizon is TRUNCATED
        at the stream end (never bridged, never extrapolated) and the tracker's resolved state is
        persisted ONCE through the SAME single function the resolved paths call. NO timeline event and
        NO status change accompany it (the append-only timeline + the surviving ``active`` row are
        untouched) — this is purely the one-time excursion measurement at the stream end."""
        if self._thesis is not None:
            if self._excursions is not None:
                self._excursions.truncate_open()
            try:
                compute_and_persist_excursions(
                    self._store, self._thesis.id, self._excursions
                )
            except Exception:
                # A persist failure must not crash the feeder teardown — surface it honestly.
                self._failed = True
                logger.exception(
                    "research monitor failed to persist excursions for surviving thesis %s",
                    self._thesis.id,
                )
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
            # Compute the machine-derived execution checks, the per-statement FINAL statuses (J-55),
            # and the outcome × process grades (J-56) ONCE at this terminal (expiry) resolution and
            # persist them (capabilities 27/29 — the SAME single functions the user-resolve,
            # system-invalidation, and restart-sweep paths call). An expired thesis here is UNMARKED
            # (an entry-marked thesis is exempt and survives via ``_detach_not_evaluated``), so its
            # mark-dependent checks read ``not_applicable`` honestly — never a fabricated pass/fail.
            # The grades weigh the just-persisted execution checks (so they run after them); the final
            # statuses use the last engine read at the terminal moment (``_last_snapshot``).
            compute_and_persist_execution_checks(self._store, thesis.id, self._config)
            compute_and_persist_final_statuses(
                self._store, thesis.id, self._last_snapshot, self._config
            )
            compute_and_persist_grades(self._store, thesis.id, "expired", self._config)
            # Excursions (capability 30, J-58): the stream ended / the watch was stopped — any open
            # horizon is TRUNCATED at the stream end (never bridged across the gap, never extrapolated)
            # and the tracker's resolved state is persisted ONCE. The SAME single function every other
            # terminal path calls; the journal detail serves it verbatim.
            if self._excursions is not None:
                self._excursions.truncate_open()
            compute_and_persist_excursions(self._store, thesis.id, self._excursions)
            self._resolved = True
            self._resolution = "expired"
            self._expiry_reason = reason
        except Exception:
            # A store failure on resolution must surface as failed, never crash the feeder.
            self._failed = True
            logger.exception("research monitor failed to expire thesis %s", thesis.id)

    def _compute_checks(self, snapshot: EngineSnapshot) -> list[dict]:
        """The eight entry-checklist checks for this snapshot (capability 33, J-63) — a PURE read.

        Composes ONLY canonical values (the published verdict, the snapshot, the declared invalidation
        + direction, the recorded chase anchor) — never a second computation of any contract value. Used
        both to advance the dwelled aggregate stance (``on_event``) and to serve the per-check rows
        (``projection`` via ``build_checklist``). ``_evaluate_statement``-style pure derivation: no
        engine/feature mutation, so the engine stays byte-identical (equivalence anti-goal)."""
        from .stance import evaluate_entry_checks

        assert self._thesis is not None
        return evaluate_entry_checks(
            snapshot=snapshot,
            verdict=self._verdict,
            invalidation_price=self._thesis.invalidation_price,
            direction=self._thesis.direction,
            rule_first_true_price=self._rule_first_true_price,
            config=self._config,
        )

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
        # The PUBLISHED management stance (capability 27, J-53): served only while this LIVE monitor is
        # evaluating (``not self._failed``) and the thesis is entry-marked (the builder gates on the
        # entry mark too). A monitor-failed read passes no stance (the strip shows its honest failure
        # notice instead). The terminal ``thesis_invalidated`` stance still renders here (the resolved-
        # invalidated branch above keeps the projection visible) so the strip shows the terminal
        # treatment. The builder serves no stance key when the thesis is not entry-marked.
        stance_value = self._stance.published_stance if self._stance is not None else None
        stance_evidence = self._stance.published_evidence if self._stance is not None else None
        # The PUBLISHED entry checklist (capability 33, J-63): built ONLY while this LIVE monitor is
        # evaluating (``not self._failed``), the thesis is unresolved, and a live snapshot exists. The
        # builder gates its actual PRESENCE on the pre-entry-mark path (active + evaluated + NO entry
        # mark — mutually exclusive with the management stance). A monitor-failed read passes no
        # checklist (the strip shows its honest failure notice instead). The per-check rows are
        # recomputed fresh here from the latest snapshot (a pure read); only the aggregate STANCE is
        # the dwell-published value the evaluator holds.
        checklist = None
        if (
            self._checklist is not None
            and not self._failed
            and not self._resolved
            and self._last_snapshot is not None
        ):
            checklist = build_checklist(
                snapshot=self._last_snapshot,
                verdict=self._verdict,
                published_stance=self._checklist.published_stance,
                invalidation_price=thesis.invalidation_price,
                direction=thesis.direction,
                rule_first_true_price=self._rule_first_true_price,
                config=self._config,
            )
        if self._failed:
            stance_value = None
            stance_evidence = None
            checklist = None
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
            management_stance=stance_value,
            management_stance_evidence=stance_evidence,
            entry_checklist=checklist,
        )

    def hint_projection(self) -> dict | None:
        """The active setup-forming hint projection (capability 33, J-65), or ``None`` (a NORMAL state).

        Independent of any thesis (a hint fires with no thesis declared). Both
        ``GET /research/hints/active`` and the WS ``hint`` key call THIS one function, so the two are
        verbatim-equal by construction (data-contract row 22). A monitor-failed read shows NO hint (the
        same honesty rule the thesis projection applies to the stance/checklist) — a present-tense card
        must never sit over a monitor that has stopped evaluating honestly."""
        if self._failed:
            return None
        return self._hints.projection()
