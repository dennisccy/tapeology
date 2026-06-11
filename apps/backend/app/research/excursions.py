"""Excursion outcomes (capability 30, J-58) — the SINGLE-owner in-memory tracker + persist seam.

This is the ONE place per-horizon excursion outcomes are measured. Excursions are the first surface
of the EVIDENCE layer: after a thesis runs its course the journal detail shows — per configured
horizon — how far the tape actually went FOR and AGAINST the idea in **R units**, separately from the
moment the tape CONFIRMED it and from the moment the user actually ENTERED. Two populations, never
pooled.

Discipline (the binding lessons + anti-goals this rides):
  * **Read-only over the engine.** The tracker is fed ONLY by the research-monitor observer's
    ``on_event`` snapshots — it never mutates engine/feature/classifier state. Engine outputs stay
    byte-identical with or without it (equivalence anti-goal).
  * **R basis reuses ONE helper.** ``R = |reference - invalidation|`` via the SAME ``r_basis`` helper
    row 27 (``marks.r_basis``) uses — never a second formula.
  * **Reference prices come from already-persisted facts.** The confirmation anchor's reference price
    is the ``last`` recorded on the FIRST published ``confirming`` timeline event (already on the
    append-only timeline). The entry anchor's reference price is the verbatim entry-mark price.
  * **Spread-at-anchor is a MOMENT value, stamped ONCE at arming** (mirroring row 18's
    ``spread_at_mark``) — never recomputed at read. The entry population REUSES row 18's already
    stamped ``spread_at_mark`` (never re-stamped); the confirmation population captures the snapshot
    spread once at the arming instant.
  * **First-touch ternary in LOGICAL time.** Each horizon resolves to ``+1R_first | -1R_first |
    neither_within_horizon`` by which R multiple (``excursion_target_r``) the price touches FIRST,
    measured in logical seconds past the anchor. Running MFE/MAE in R are tracked per population.
  * **Truncation, never extrapolation.** An open horizon is TRUNCATED at stream end or at a gap
    event (``paused`` teardown / ``watch_restarted`` / a stale span) — flagged ``truncated``, never
    bridged across a gap, never extrapolated past the data.
  * **Two populations fully segregated end to end** — separate anchors, separate R bases, separate
    per-horizon rows; nothing pooled or averaged across them.
  * **Persist ONCE at the defining moment, never recomputed at read.** ``compute_and_persist_excursions``
    snapshots the tracker's resolved state and persists it on the thesis row (schema v7) through the
    single writer queue. Once persisted, values are frozen. Where no tracker is available at the
    persist moment (the restart-expiry sweep after a backend restart — the watch that declared the
    thesis is long gone), an explicit honest ``not_tracked`` record is persisted — never fabricated
    numbers, never a dishonest zero.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..config import Config
from ..engine.snapshot import EngineSnapshot
from .marks import r_basis as _r_basis
from .store import JournalStore

# The two population ids — segregated end to end, never pooled.
CONFIRMATION = "confirmation"
ENTRY = "entry"

# The ternary per-horizon outcome enum (by first touch, in logical time). LABELS only — never a
# numeric score. ``not_resolved`` is NOT one of these: an open horizon reads ``neither_within_horizon``
# only once the horizon has fully elapsed; before that it is reported as ``truncated`` if the stream
# ended inside it.
TERNARY_PLUS = "+1R_first"
TERNARY_MINUS = "-1R_first"
TERNARY_NEITHER = "neither_within_horizon"


@dataclass
class _Population:
    """One armed excursion population (confirmation OR entry) — its anchor + per-horizon running state.

    Mutable while live (the tracker advances it each event); SNAPSHOTTED to a frozen dict at the
    persist moment. ``reference_price`` and ``invalidation_price`` give the R basis (computed via the
    ONE shared ``marks.r_basis`` helper); ``r`` is cached once at arming (the basis never changes).
    ``spread_at_anchor`` is the moment spread stamped ONCE at arming. Each horizon tracks running
    MFE/MAE (in R) and a resolved ternary outcome + a per-horizon ``done`` / ``truncated`` flag.
    """

    population: str
    anchor_logical_ts: float
    anchor_wall_ts: float
    reference_price: float
    invalidation_price: float
    spread_at_anchor: float | None
    r: float
    # Per horizon (keyed by the horizon's float seconds): the running excursion state.
    horizons: dict[float, "_HorizonState"] = field(default_factory=dict)


@dataclass
class _HorizonState:
    horizon: float
    mfe_r: float = 0.0          # max favorable excursion in R (>= 0; favorable = the thesis direction)
    mae_r: float = 0.0          # max adverse excursion in R (<= 0)
    # The ternary outcome LATCHED at FIRST TOUCH (the R target reached first). Distinct from
    # ``done``: the ternary is decided once and never changes, but the horizon keeps tracking running
    # MFE/MAE over the WHOLE window (goal.md capability 30 — MFE/MAE are measured over the horizon,
    # the ternary is a separate first-touch determination).
    outcome: str | None = None
    done: bool = False          # the horizon fully elapsed (MFE/MAE final) — no longer updated
    truncated: bool = False     # the stream/gap cut this horizon short before it fully elapsed


class ExcursionTracker:
    """Tracks running excursions for one thesis across the two populations (capability 30, J-58).

    Fed ONLY by the research-monitor observer: ``on_event(snapshot)`` advances every armed population,
    ``arm_confirmation`` / ``arm_entry`` arm a population ONCE at its defining moment, and
    ``truncate_open`` marks every still-open horizon ``truncated`` at a stream end / gap event. The
    tracker is read-only over the engine — it only reads the handed snapshot.

    Determinism: the tracker reads ONLY the snapshot's logical timestamp + last (and, once, the
    arming spread), so the SAME ordered stream + the SAME arming sequence yields a byte-identical
    persisted record (J-58's determinism clause).
    """

    def __init__(self, *, invalidation_price: float, direction: str, config: Config) -> None:
        self._invalidation = invalidation_price
        self._direction = direction
        self._config = config
        self._populations: dict[str, _Population] = {}

    # --- arming (called at the defining moments, NOT every event) -------------------------------
    def arm_confirmation(
        self, snapshot: EngineSnapshot, reference_price: float, *, wall_ts: float | None = None
    ) -> None:
        """Arm the confirmation population ONCE at the first published ``confirming`` event.

        ``reference_price`` is the ``last`` recorded on that published timeline event (the basis the
        spec mandates). ``wall_ts`` is the true clock instant the monitor stamped on that published
        event (passed in so the anchor's true-clock display matches the timeline row verbatim); when
        omitted (the pure unit path) it defaults to ``0.0`` — an honest sentinel, the UI renders the
        logical anchor regardless. The spread-at-anchor is captured ONCE here from the snapshot (a
        moment value, like row 18's ``spread_at_mark``). Re-confirmation after weakening never re-arms
        (idempotent guard) — the FIRST confirmation owns the population."""
        if CONFIRMATION in self._populations:
            return
        if reference_price is None:
            return
        self._populations[CONFIRMATION] = self._make_population(
            CONFIRMATION,
            anchor_logical_ts=snapshot.timestamp,
            anchor_wall_ts=wall_ts if wall_ts is not None else 0.0,
            reference_price=reference_price,
            spread_at_anchor=snapshot.spread,
        )

    def arm_entry(
        self,
        *,
        logical_ts: float,
        wall_ts: float,
        reference_price: float,
        spread_at_mark: float | None,
    ) -> None:
        """Arm the entry population ONCE at the recorded entry mark.

        ``reference_price`` is the verbatim mark price; ``spread_at_mark`` is the moment spread ALREADY
        stamped by row 18 on the action record (REUSED here, never re-stamped). Idempotent — a second
        entry can never exist (the API enforces one entry), but the guard keeps the FIRST arming."""
        if ENTRY in self._populations:
            return
        self._populations[ENTRY] = self._make_population(
            ENTRY,
            anchor_logical_ts=logical_ts,
            anchor_wall_ts=wall_ts,
            reference_price=reference_price,
            spread_at_anchor=spread_at_mark,
        )

    def _make_population(
        self,
        population: str,
        *,
        anchor_logical_ts: float,
        anchor_wall_ts: float,
        reference_price: float,
        spread_at_anchor: float | None,
    ) -> _Population:
        # R basis via the ONE shared helper (row 27) — never a second formula.
        r = _r_basis(reference_price, self._invalidation)
        pop = _Population(
            population=population,
            anchor_logical_ts=anchor_logical_ts,
            anchor_wall_ts=anchor_wall_ts,
            reference_price=reference_price,
            invalidation_price=self._invalidation,
            spread_at_anchor=spread_at_anchor,
            r=r,
            horizons={
                h: _HorizonState(horizon=h)
                for h in self._config.excursion_horizons_seconds
            },
        )
        return pop

    @property
    def is_armed(self) -> bool:
        return bool(self._populations)

    @property
    def armed_populations(self) -> tuple[str, ...]:
        return tuple(self._populations.keys())

    # --- the hot path (read-only over the engine) ------------------------------------------------
    def on_event(self, snapshot: EngineSnapshot) -> None:
        """Advance every armed population against this snapshot (read-only).

        For each population with at least one open horizon: compute the directional move in R from the
        anchor's reference price, update running MFE/MAE, resolve the ternary by FIRST TOUCH (the R
        target reached first wins), and mark a horizon ``done`` once the logical time past the anchor
        exceeds it. A degenerate ``R == 0`` basis (reference exactly at the invalidation) yields no
        measurable move — every horizon resolves ``neither_within_horizon`` honestly (never a
        divide-by-zero, never a fabricated infinity)."""
        last = snapshot.last
        if last is None:
            return
        for pop in self._populations.values():
            self._advance_population(pop, snapshot.timestamp, last)

    def _advance_population(self, pop: _Population, logical_ts: float, last: float) -> None:
        dt = logical_ts - pop.anchor_logical_ts
        if dt < 0:
            return  # a snapshot before the anchor never contributes (defensive)
        # Directional move in R: favorable = the thesis direction (long => price up; short => down).
        if pop.r > 0:
            raw_move = last - pop.reference_price
            directed = raw_move if self._direction == "long" else -raw_move
            move_r = directed / pop.r
        else:
            move_r = 0.0  # degenerate basis — no measurable move (honest, never fabricated)
        target = self._config.excursion_target_r
        for hs in pop.horizons.values():
            if hs.done:
                continue
            within = dt <= hs.horizon
            if within:
                # Running MFE/MAE in R over the WHOLE horizon window (favorable >= 0, adverse <= 0) —
                # kept updating even after the ternary latches (MFE/MAE and the ternary are distinct
                # measurements over the same window, per goal.md capability 30).
                if move_r > hs.mfe_r:
                    hs.mfe_r = move_r
                if move_r < hs.mae_r:
                    hs.mae_r = move_r
                # First-touch ternary: whichever R target is reached FIRST within the horizon wins,
                # latched ONCE (re-touch never changes it). The horizon stays OPEN for MFE/MAE.
                if hs.outcome is None:
                    if move_r >= target:
                        hs.outcome = TERNARY_PLUS
                    elif move_r <= -target:
                        hs.outcome = TERNARY_MINUS
            else:
                # The logical time has passed the horizon: MFE/MAE are final. If no R target was ever
                # touched within the window, the ternary resolves ``neither_within_horizon``. The
                # horizon is fully elapsed (not truncated) — never updated again.
                if hs.outcome is None:
                    hs.outcome = TERNARY_NEITHER
                hs.done = True

    # --- truncation (stream end / gap event) -----------------------------------------------------
    def truncate_open(self) -> None:
        """Mark every still-open horizon (in every armed population) ``truncated`` (J-58).

        Called at the defining truncation moment — a stream end, or a gap event (``paused`` teardown,
        ``watch_restarted``, a stale span). A horizon is TRUNCATED iff its ternary outcome is still
        UNDETERMINED (``outcome is None``) AND it has not fully elapsed: the window was cut short
        before the question "did the tape reach +1R or -1R within H seconds?" could be answered, so it
        is flagged ``truncated`` (its running MFE/MAE so far are kept as the honest partial excursion),
        never bridged across the gap, never extrapolated. A horizon whose ternary ALREADY latched by
        first touch (``+1R_first`` / ``-1R_first``) is NOT truncated — that answer is final regardless
        of the cut (the target was definitively touched within the window); only its MFE/MAE stop
        growing. A horizon already fully elapsed (``done``) is untouched."""
        for pop in self._populations.values():
            for hs in pop.horizons.values():
                if hs.done:
                    continue
                if hs.outcome is None:
                    hs.truncated = True
                # In both cases the horizon stops updating at the cut (no extrapolation past the data).
                hs.done = True

    # --- snapshot to the persisted shape ---------------------------------------------------------
    def to_record(self) -> dict:
        """Freeze the tracker's resolved state into the persisted excursion record (schema v7).

        Returns ``{"tracked": True, "populations": {confirmation?: {...}, entry?: {...}}}`` where each
        present population carries its anchor (logical + wall ts, reference price, R basis,
        spread-at-anchor) and per-horizon rows (horizon, mfe_r, mae_r, outcome, truncated). Only ARMED
        populations appear — a never-confirmed thesis has NO confirmation key; a no-entry thesis has
        NO entry key (honest omission, never a fabricated zero). Both populations are fully
        segregated — independent anchors, independent R bases, independent rows."""
        populations: dict[str, dict] = {}
        for pop_id, pop in self._populations.items():
            populations[pop_id] = {
                "population": pop.population,
                "anchor_logical_ts": pop.anchor_logical_ts,
                "anchor_wall_ts": pop.anchor_wall_ts,
                "reference_price": pop.reference_price,
                "invalidation_price": pop.invalidation_price,
                "r_basis": pop.r,
                "spread_at_anchor": pop.spread_at_anchor,
                "horizons": [
                    {
                        "horizon": hs.horizon,
                        "mfe_r": _round_r(hs.mfe_r),
                        "mae_r": _round_r(hs.mae_r),
                        # An open-but-not-truncated horizon (e.g. a persist mid-stream that never
                        # truncated) reads ``neither_within_horizon`` only once fully elapsed; while
                        # genuinely open it is ``None`` and the ``truncated`` flag tells the story.
                        "outcome": hs.outcome,
                        "truncated": hs.truncated,
                    }
                    for hs in pop.horizons.values()
                ],
            }
        return {"tracked": True, "populations": populations}


def _round_r(value: float) -> float:
    """Round an R figure to 4 dp so the persisted/served numbers are byte-stable across runs.

    The deterministic seeded re-run must reproduce IDENTICAL numbers (J-58's determinism clause);
    rounding kills any last-ULP float drift while keeping R to a precision finer than the 2-dp display
    the UI renders."""
    return round(value, 4)


# --- the not-tracked honest marker (restart-expiry sweep, no tracker available) -------------------

def not_tracked_record() -> dict:
    """The explicit honest record persisted where no tracker state exists at the persist moment.

    The restart-expiry sweep resolves a thesis whose declaring watch is long gone (a backend restart):
    there is no in-memory price path to measure excursions from, and tape data is NEVER persisted, so
    the excursions CANNOT be reconstructed. Rather than fabricate numbers or a dishonest zero, persist
    ``{"tracked": False}`` — the journal detail then renders an explicit not-tracked notice."""
    return {"tracked": False, "populations": {}}


# --- the persist seam (mirrors execution_checks / grades / final-statuses) -----------------------

def compute_and_persist_excursions(
    store: JournalStore,
    thesis_id: str,
    tracker: "ExcursionTracker | None",
) -> dict | None:
    """Persist the excursion record for a thesis ONCE at its defining moment (capability 30, J-58).

    Called by every terminal-resolution path (user resolve, system invalidation, stream-end / stop
    expiry, restart-expiry sweep) AND at the stream-end SURVIVAL path for an entry-marked thesis that
    survives active-but-not-evaluated (J-58's script ends exactly there — the record must exist
    without a resolution). Follows the proven persist-once seam: it snapshots the live ``tracker``'s
    resolved state (the price path is in memory, NEVER persisted — tape data stays unpersisted) and
    writes it on the thesis row via ``store.set_excursions`` through the single writer queue. Once
    persisted, the values are frozen — never recomputed at read, never reopened on a matching-source
    re-attach.

    ``tracker`` is ``None`` ONLY where no tracker exists at the persist moment (the restart-expiry
    sweep after a backend restart): an explicit ``not_tracked`` record is then persisted (honest
    absence over fabricated numbers). Idempotent guard: if the thesis already carries an excursion
    record (a double-resolve race), it is NOT recomputed — the first record stands (append-only
    spirit). Returns the persisted record (or ``None`` if the thesis is gone)."""
    thesis = store.get_thesis(thesis_id)
    if thesis is None:
        return None
    if thesis.excursions is not None:
        return thesis.excursions
    record = tracker.to_record() if tracker is not None else not_tracked_record()
    store.set_excursions(thesis_id, record)
    return record
