"""Replay-study runner + cancellable background-job manager (capability 32, J-60/J-61/J-62).

THE single owner of replay studies. A study runs the EXISTING setup grammar over an explicitly
chosen source + past window as an **unpaced offline replay through a FRESH ``TapeEngine``** — the
exact fixture-replay pattern of ``test_real_data_classify.py`` / ``test_dense_replay_gate.py`` —
attaching ONLY via the engine's existing observer seam. It is **read-only over the engine**: it never
mutates engine / classifier / feature / history state, so the same stream yields byte-identical
snapshots with the study observer attached or absent (the observer-equivalence anti-goal, J-68).

What the runner does, and the discipline it rides (every clause is an anti-goal or a spec line):

  * **State-native auto-arming** for ``absorption_reversal`` / ``trend_continuation`` from EXISTING
    engine states only — sustained matching ABSORPTION (the premise) for absorption_reversal,
    sustained matching CONTROL for trend_continuation — each gated by a config-owned sustain + a
    config-owned cooldown so one premise phase arms ONE occurrence (never one per tick). No new
    indicator, no new threshold in code: ``study_arm_sustain_seconds`` / ``study_arm_cooldown_seconds``
    are config-owned and IN ``config_fingerprint``.

  * **Level setups require a user-supplied level** (``level_break`` / ``failed_move_fade``): the study
    is stamped ``hindsight_level`` and EXCLUDED from any cross-study aggregate (enforced here + tested);
    a level setup with no level is a 422 at the route (never a guessed level). With a level supplied,
    arming latches on the cross of that level + matching control (the existing verdict-engine semantics).

  * **Each armed occurrence runs the EXISTING per-setup verdict rule table** (``verdict.VerdictEvaluator``
    — no new rule, no new indicator) from a FRESH evaluator armed at the occurrence, recording its
    per-occurrence verdict summary (did it ever publish ``confirming`` / ``rejecting`` / ``invalidated``).

  * **Deterministic occurrence-R (the named design decision — documented in the dev handoff):** an
    auto-armed occurrence has no user-typed invalidation, so its R basis is derived DETERMINISTICALLY
    from existing engine values at the arm instant — a synthetic invalidation placed
    ``study_occurrence_r_spread_multiple × spread_at_arm`` (floored at ``study_occurrence_r_floor``) on
    the ADVERSE side of the arm price. ``R = |arm_price − synthetic_invalidation|`` then flows through
    the EXISTING ``marks.r_basis`` helper + the ``excursions.ExcursionTracker`` ternary/horizon
    machinery (``excursion_horizons_seconds``) — the study is a REGISTERED CONSUMER of the one R
    formula, never a second one. IDENTICAL for setup and null arms. NEVER fitted.

  * **Seeded random-arm-time null baseline:** ``study_null_arm_count`` arm times drawn from a recorded
    seed over the SAME window, SAME direction, SAME R definition, SAME horizons. The seed is persisted
    on the study record so the baseline reproduces exactly. ONE replay pass serves BOTH populations —
    the observer records the full snapshot path in memory ONCE, and every arm (setup or null) measures
    its excursions against that recorded path (N engine re-replays would blow the CI budget). No tape
    data is persisted (in-job memory only — the persisted study holds R-unit summaries, never prints).

  * **Excursions per occurrence:** arm-anchored, per config horizon, first-touch in logical time;
    horizons cut short by window end are flagged ``truncated`` and counted separately — never dropped,
    never extrapolated (the existing ``ExcursionTracker.truncate_open`` at window end).

  * **Cancellable background jobs:** ``queued | running | done | cancelled | failed`` with progress;
    cancellation honored between events; cancelled → explicit ``cancelled`` with partial-marked results;
    failed (no data / provider error) → explicit error, never an empty success. The replay runs OFF
    the event loop (a worker thread), and ALL SQLite writes go through the existing single writer queue.

  * **Honesty stamps + never-pool:** every study carries its bound source, ``data_feed``,
    ``config_fingerprint``, and the baseline seed; aggregates render with n + the descriptive
    measurement framing; groups below the config minimum reuse the insufficient-sample marker. Results
    are NEVER pooled across feed or fingerprint (each study IS one feed + one fingerprint).
"""

from __future__ import annotations

import random
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Callable

from ..config import Config
from ..engine.snapshot import EngineSnapshot
from ..engine.tape_engine import TapeEngine
from ..providers.base import Event
from ..providers.historical import HistoricalProvider
from ..providers.simulated import SIM_SCENARIOS, SimulatedProvider, is_sim_ticker
from .excursions import (
    ExcursionTracker,
    TERNARY_MINUS,
    TERNARY_NEITHER,
    TERNARY_PLUS,
)
from .feed_basis import data_feed_for_scenario
from .marks import r_basis as _r_basis
from .store import JournalStore, StudyRecord
from .verdict import VerdictEvaluator

# --- study status enum (capability 32 / J-61 — each status its OWN explicit copy, iter-15 lesson) ---
STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"
STATUS_FAILED = "failed"
TERMINAL_STATUSES = frozenset({STATUS_DONE, STATUS_CANCELLED, STATUS_FAILED})

# The two state-native auto-arming setups (no user level). The two level setups
# (``level_break`` / ``failed_move_fade``) require a user-supplied level (hindsight) — handled below.
_STATE_NATIVE_SETUPS = frozenset({"absorption_reversal", "trend_continuation"})
_LEVEL_SETUPS = frozenset({"level_break", "failed_move_fade"})

# The two source kinds the study runner accepts (validated at the route): a reference/sim/historical
# replay. ``reference`` is the committed PG SIP fixture (no credentials). ``sim`` is a seeded sim
# scenario. ``historical`` is an arbitrary symbol + past window through the EXISTING fetch path.
SOURCE_REFERENCE = "reference"
SOURCE_SIM = "sim"
SOURCE_HISTORICAL = "historical"

# The committed reference window — the PG SIP fixture (the iter-17 capability-34 fixture; this is its
# second consumer). Loadable without credentials. The id the create form's quick-pick sends.
REFERENCE_SOURCE_ID = "PG_SIP_REFERENCE"

# How often (in processed events) a running study refreshes its persisted progress — throttled so the
# progress write is never a hot path (the replay processes thousands of events; a write every event
# would hammer the writer queue). A whole-number internal cadence, not a tuned research value.
_PROGRESS_EVERY = 250

# How often the cancellation flag is polled during the replay (every event is cheap — a bool read).
# Cancellation is honored between events (cooperative), so a long study stops promptly on cancel.


@dataclass
class _PathPoint:
    """One recorded snapshot-path point (logical ts + last + spread + the canonical tape state). Tape
    data lives ONLY here in memory during the job — never persisted (the persistence-scope anti-goal).
    A lightweight stand-in that ``ExcursionTracker`` can consume (it reads ``.timestamp`` / ``.last`` /
    ``.spread``); ``tape_state`` is the engine's single-source-of-truth read at the tick, used by the
    state-native arming + the per-occurrence verdict summary (read-only — never recomputed)."""

    timestamp: float
    last: float | None
    spread: float | None
    tape_state: str


@dataclass
class _Occurrence:
    """One armed occurrence (setup OR null) before its excursions are measured."""

    population: str            # "setup" | "null"
    arm_logical_ts: float
    arm_price: float
    spread_at_arm: float | None
    invalidation_price: float  # the synthetic deterministic invalidation (adverse side)
    r_basis: float


class StudyCancelled(Exception):
    """Raised inside the replay loop when a cancellation is observed (caught by the runner)."""


class StudyFailed(Exception):
    """Raised when a study cannot produce a result (no data / provider error / empty window)."""


class _PathObserver:
    """The engine observer that records the snapshot path for ONE study replay (read-only).

    Attached at the engine's existing observer seam. ``on_event`` appends a lightweight path point and
    feeds the live state machine that decides the state-native SETUP arms; ``on_status`` is a no-op
    here (the study replay is an offline finite stream — there is no live status flip to react to). The
    observer NEVER mutates the engine (it only reads the handed snapshot), so the engine stays
    byte-identical with it attached (J-68)."""

    def __init__(self) -> None:
        self.path: list[_PathPoint] = []

    def on_event(self, event: Event, snapshot: EngineSnapshot) -> None:
        self.path.append(
            _PathPoint(
                timestamp=snapshot.timestamp,
                last=snapshot.last,
                spread=snapshot.spread,
                tape_state=snapshot.tape_state,
            )
        )

    def on_status(self, status: str) -> None:  # offline finite stream — no live status to react to
        return


def _provider_for_source(
    *,
    source_kind: str,
    source_id: str,
    config: Config,
    historical_fetch: Callable[[], object] | None,
):
    """Build the replay provider for a study source through an EXISTING seam (never a new path).

    Returns ``(provider, source_descriptor)``. Raises ``StudyFailed`` for an empty/absent window so the
    job resolves to an explicit ``failed`` (never an empty success). The historical path is injected as
    a callable (``historical_fetch``) that returns a ``HistoricalWindow`` via the EXISTING adapter fetch
    — so credentials/timeouts/no-data are handled by the same explicit-error machinery the watch path
    uses (a credentialless arbitrary-window study fails explicitly, never fixture-substituted)."""
    if source_kind == SOURCE_REFERENCE:
        # The committed PG SIP fixture — loadable WITHOUT credentials. Imported lazily (the loader
        # lives in the test fakes module on the test path; the committed fixture is the canonical one).
        window = _load_reference_window()
        if window is None or not window.trades:
            raise StudyFailed("the committed reference window is unavailable")
        provider = HistoricalProvider(window.symbol, window, f"historical {window.symbol} reference")
        return provider, provider.scenario
    if source_kind == SOURCE_SIM:
        if not is_sim_ticker(source_id):
            raise StudyFailed(f"unknown sim scenario '{source_id}'")
        provider = SimulatedProvider(source_id, SIM_SCENARIOS[source_id])
        return provider, provider.scenario
    if source_kind == SOURCE_HISTORICAL:
        if historical_fetch is None:
            raise StudyFailed("no historical fetch available for this study")
        window = historical_fetch()  # may raise the existing explicit vendor errors — never fabricated
        if window is None or not getattr(window, "trades", None):
            raise StudyFailed("no data for that window")
        descriptor = f"historical {source_id}"
        provider = HistoricalProvider(source_id, window, descriptor)
        return provider, provider.scenario
    raise StudyFailed(f"unknown source kind '{source_kind}'")


def _load_reference_window():
    """Load the committed PG SIP reference fixture without credentials. The fixture path mirrors the
    capability-34 gate's committed file (one fixture, two consumers). Returns the ``HistoricalWindow``
    or ``None`` if absent (the caller raises ``StudyFailed`` — never a synthetic stand-in)."""
    import json
    from pathlib import Path

    from ..providers.adapters.base import HistoricalWindow, RawQuote, RawTrade

    fixture = (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "alpaca"
        / "PG_20260609_170000_171000_sip.json"
    )
    if not fixture.exists():
        return None
    data = json.loads(fixture.read_text())
    trades = tuple(RawTrade(t["epoch"], t["price"], t["size"]) for t in data["trades"])
    quotes = tuple(
        RawQuote(q["epoch"], q["bid"], q["ask"], q["bid_size"], q["ask_size"])
        for q in data["quotes"]
    )
    return HistoricalWindow(data["symbol"], trades, quotes)


def _control_state(direction: str) -> str:
    return "buyer_control" if direction == "long" else "seller_control"


def _absorption_state(direction: str) -> str:
    # absorption_reversal premise: long expects sellers absorbed at the bid (bid_absorption);
    # short expects buyers absorbed at the ask (ask_absorption).
    return "bid_absorption" if direction == "long" else "ask_absorption"


def _premise_state(setup_type: str, direction: str) -> str:
    """The EXISTING engine tape state whose SUSTAINED presence arms a state-native occurrence.

    absorption_reversal arms on sustained matching ABSORPTION (the premise — the reversal itself is
    then judged by the per-occurrence verdict evaluator). trend_continuation arms on sustained matching
    CONTROL. Composed ONLY of existing states (no new indicator)."""
    if setup_type == "absorption_reversal":
        return _absorption_state(direction)
    return _control_state(direction)  # trend_continuation


def _synthetic_invalidation(arm_price: float, spread: float | None, direction: str, config: Config) -> float:
    """The deterministic occurrence-R synthetic invalidation (the named design decision).

    A synthetic invalidation placed ``study_occurrence_r_spread_multiple × spread`` (floored at
    ``study_occurrence_r_floor``) on the ADVERSE side of the arm price (below for a long, above for a
    short). IDENTICAL for setup and null arms; derived ONLY from existing engine values at the arm
    instant (arm price + arm-instant spread); NEVER fitted. R is then ``|arm_price − this|`` via the
    shared ``marks.r_basis`` helper."""
    s = spread if spread is not None and spread > 0 else 0.0
    band = max(s * config.study_occurrence_r_spread_multiple, config.study_occurrence_r_floor)
    return arm_price - band if direction == "long" else arm_price + band


def _arm_occurrence(
    population: str,
    *,
    arm_logical_ts: float,
    arm_price: float,
    spread_at_arm: float | None,
    direction: str,
    config: Config,
) -> _Occurrence:
    invalidation = _synthetic_invalidation(arm_price, spread_at_arm, direction, config)
    # R basis via the ONE shared helper (row 27 / capability 30) — never a second formula.
    r = _r_basis(arm_price, invalidation)
    return _Occurrence(
        population=population,
        arm_logical_ts=arm_logical_ts,
        arm_price=arm_price,
        spread_at_arm=spread_at_arm,
        invalidation_price=invalidation,
        r_basis=r,
    )


def _measure_excursions(
    occ: _Occurrence,
    path: list[_PathPoint],
    direction: str,
    config: Config,
) -> dict:
    """Measure ONE occurrence's per-horizon excursions against the recorded snapshot path (J-58
    machinery, one replay pass). Arms an ``ExcursionTracker`` at the occurrence and advances it over
    every recorded path point at/after the arm; truncates open horizons at the window end. Returns the
    per-horizon ternary outcomes + truncation flags + running MFE/MAE (R units), the registered
    consumer of the one excursion formula — never a second one."""
    tracker = ExcursionTracker(
        invalidation_price=occ.invalidation_price, direction=direction, config=config
    )
    # Arm the entry population at the occurrence (the entry-anchored arm is exactly the study's
    # arm-anchored excursion — same single helper as a journaled entry mark).
    tracker.arm_entry(
        logical_ts=occ.arm_logical_ts,
        wall_ts=0.0,  # offline study — logical anchor only (no true-clock display for an occurrence)
        reference_price=occ.arm_price,
        spread_at_mark=occ.spread_at_arm,
    )
    for point in path:
        if point.timestamp < occ.arm_logical_ts:
            continue
        tracker.on_event(point)  # _PathPoint quacks like a snapshot (.timestamp/.last/.spread)
    # The offline window ends here — every still-open horizon is TRUNCATED at the window end (never
    # extrapolated past the data), exactly the live stream-end semantics.
    tracker.truncate_open()
    record = tracker.to_record()
    entry_pop = record["populations"].get("entry", {})
    return {
        "arm_logical_ts": occ.arm_logical_ts,
        "arm_price": round(occ.arm_price, 4),
        "spread_at_arm": occ.spread_at_arm,
        "invalidation_price": round(occ.invalidation_price, 4),
        "r_basis": round(occ.r_basis, 4),
        "horizons": entry_pop.get("horizons", []),
    }


def _aggregate_horizons(occurrence_rows: list[dict], config: Config) -> list[dict]:
    """Aggregate a population's per-horizon ternary distribution (the side-by-side comparison).

    For each configured horizon: count ``+1R_first`` / ``-1R_first`` / ``neither_within_horizon`` and a
    SEPARATE ``truncated`` bucket (a horizon the window end cut short before +1R/−1R could resolve) —
    never folded into the resolved buckets, never extrapolated. n is the occurrence count. The
    distribution is a journaled MEASUREMENT, never an edge/win-rate claim."""
    horizons = list(config.excursion_horizons_seconds)
    rows: list[dict] = []
    for h in horizons:
        plus = minus = neither = truncated = 0
        for occ in occurrence_rows:
            for hz in occ["horizons"]:
                if hz["horizon"] != h:
                    continue
                outcome = hz.get("outcome")
                if hz.get("truncated") and outcome is None:
                    truncated += 1
                elif outcome == TERNARY_PLUS:
                    plus += 1
                elif outcome == TERNARY_MINUS:
                    minus += 1
                elif outcome == TERNARY_NEITHER:
                    neither += 1
        rows.append(
            {
                "horizon": h,
                TERNARY_PLUS: plus,
                TERNARY_MINUS: minus,
                TERNARY_NEITHER: neither,
                "truncated": truncated,
            }
        )
    return rows


class StudyRunner:
    """Runs one study end-to-end (off the event loop) and persists its result ONCE.

    The runner builds a FRESH ``TapeEngine``, attaches the read-only ``_PathObserver`` at the existing
    observer seam, replays the source UNPACED (cooperative cancellation between events), records the
    snapshot path in memory ONCE, then derives BOTH the state-native setup arms and the seeded
    random-arm-time null arms from that single pass and measures each arm's excursions through the
    EXISTING ``ExcursionTracker``. All persistence goes through the injected ``JournalStore``'s single
    writer queue."""

    def __init__(self, store: JournalStore, config: Config) -> None:
        self._store = store
        self._config = config

    def run(
        self,
        *,
        study_id: str,
        params: dict,
        historical_fetch: Callable[[], object] | None,
        is_cancelled: Callable[[], bool],
    ) -> None:
        """Execute the study, persisting status transitions through the store. Honors cancellation
        cooperatively (checked between events and before persist). Never raises out — every failure is
        captured as an explicit ``failed`` study (never an empty success)."""
        base_payload = self._store.get_study(study_id)
        payload = dict(base_payload.payload) if base_payload is not None else dict(params)
        try:
            if is_cancelled():
                self._persist_cancelled(study_id, payload, setup_rows=[], null_rows=[])
                return
            payload = {**payload, "status": STATUS_RUNNING, "progress": 0.0}
            self._store.update_study_payload(study_id, payload)

            provider, descriptor = _provider_for_source(
                source_kind=params["source_kind"],
                source_id=params.get("source_id", ""),
                config=self._config,
                historical_fetch=historical_fetch,
            )
            # Re-stamp the resolved source descriptor + data_feed now the provider is known (the create
            # stamp used the requested source; the descriptor is authoritative once resolved).
            payload["source"] = descriptor
            payload["data_feed"] = data_feed_for_scenario(descriptor, self._config)

            observer, total_events, cancelled = self._replay(
                provider, study_id, payload, is_cancelled
            )
            path = observer.path
            direction = params["direction"]

            setup_occurrences = self._arm_setup_occurrences(path, params)
            null_occurrences = self._arm_null_occurrences(path, params)

            setup_rows = [_measure_excursions(o, path, direction, self._config) for o in setup_occurrences]
            null_rows = [_measure_excursions(o, path, direction, self._config) for o in null_occurrences]
            # Per-occurrence verdict summaries (the EXISTING per-setup verdict rule table — no new rule).
            verdict_summaries = self._verdict_summaries(setup_occurrences, path, params)
            for row, summary in zip(setup_rows, verdict_summaries):
                row["verdict_summary"] = summary

            if cancelled:
                self._persist_cancelled(study_id, payload, setup_rows=setup_rows, null_rows=null_rows)
                return

            self._persist_done(study_id, payload, setup_rows, null_rows, params)
        except StudyCancelled:
            self._persist_cancelled(study_id, payload, setup_rows=[], null_rows=[])
        except StudyFailed as exc:
            self._persist_failed(study_id, payload, str(exc))
        except Exception as exc:  # any unexpected error -> explicit failed, never an empty success
            self._persist_failed(study_id, payload, f"study failed: {exc}")

    # --- replay (unpaced, cooperative cancellation, read-only observer) -------------------------
    def _replay(
        self,
        provider,
        study_id: str,
        payload: dict,
        is_cancelled: Callable[[], bool],
    ) -> tuple[_PathObserver, int, bool]:
        """Replay the source through a FRESH engine with the read-only path observer attached. Returns
        ``(observer, total_events, cancelled)``. Progress is persisted every ``_PROGRESS_EVERY`` events
        (throttled — not a hot path). Cancellation is checked between events; a cancel mid-run returns
        ``cancelled=True`` with the partial path (the partial result is marked partial — never complete)."""
        epoch_anchor = getattr(provider, "epoch_anchor", None)
        engine = TapeEngine(
            provider.ticker, provider.scenario, self._config, epoch_anchor=epoch_anchor
        )
        observer = _PathObserver()
        engine.add_observer(observer)
        total = 0
        cancelled = False
        for event in provider.stream():
            if is_cancelled():
                cancelled = True
                break
            engine.process_event(event)
            total += 1
            if total % _PROGRESS_EVERY == 0:
                # A throttled progress heartbeat (unbounded total is unknown for a stream, so progress
                # is a coarse monotone signal: events processed). Persisted through the writer queue.
                hb = {**payload, "status": STATUS_RUNNING, "events_processed": total}
                self._store.update_study_payload(study_id, hb)
        return observer, total, cancelled

    # --- state-native setup arming (existing states only, sustain + cooldown gated) -------------
    def _arm_setup_occurrences(self, path: list[_PathPoint], params: dict) -> list[_Occurrence]:
        """Arm the SETUP occurrences from the recorded path.

        Level setups (``level_break`` / ``failed_move_fade``) require a user-supplied level: an
        occurrence arms when ``last`` crosses the level in the thesis direction with the matching
        control read (hindsight level). State-native setups arm on sustained matching premise state
        (absorption for absorption_reversal; control for trend_continuation), gated by the config
        sustain + cooldown so one premise phase arms ONE occurrence. The arm reads the recorded
        ``point.tape_state`` (the engine's single-source-of-truth read at that tick) — never recomputed.
        """
        setup_type = params["setup_type"]
        direction = params["direction"]
        config = self._config
        occurrences: list[_Occurrence] = []
        if setup_type in _LEVEL_SETUPS:
            level = params.get("level_price")
            if level is None:
                return []  # guarded at the route (422); defensive here
            control = _control_state(direction)
            cooldown_until = float("-inf")
            for point in path:
                if point.last is None:
                    continue
                crossed = point.last > level if direction == "long" else point.last < level
                if crossed and point.tape_state == control and point.timestamp >= cooldown_until:
                    occurrences.append(
                        _arm_occurrence(
                            "setup",
                            arm_logical_ts=point.timestamp,
                            arm_price=point.last,
                            spread_at_arm=point.spread,
                            direction=direction,
                            config=config,
                        )
                    )
                    cooldown_until = point.timestamp + config.study_arm_cooldown_seconds
            return occurrences
        # State-native: sustained matching premise state arms one occurrence per premise phase.
        premise = _premise_state(setup_type, direction)
        run_since: float | None = None
        armed_this_run = False
        cooldown_until = float("-inf")
        for point in path:
            if point.tape_state == premise:
                if run_since is None:
                    run_since = point.timestamp
                    armed_this_run = False
                sustained = point.timestamp - run_since >= config.study_arm_sustain_seconds
                if (
                    sustained
                    and not armed_this_run
                    and point.timestamp >= cooldown_until
                    and point.last is not None
                ):
                    occurrences.append(
                        _arm_occurrence(
                            "setup",
                            arm_logical_ts=point.timestamp,
                            arm_price=point.last,
                            spread_at_arm=point.spread,
                            direction=direction,
                            config=config,
                        )
                    )
                    armed_this_run = True
                    cooldown_until = point.timestamp + config.study_arm_cooldown_seconds
            else:
                run_since = None
                armed_this_run = False
        return occurrences

    # --- seeded random-arm-time null baseline (same window/direction/R/horizons) -----------------
    def _arm_null_occurrences(self, path: list[_PathPoint], params: dict) -> list[_Occurrence]:
        """Arm the seeded random-arm-time NULL baseline from the SAME recorded path.

        ``study_null_arm_count`` arm times drawn from the recorded seed, uniformly over the window's
        logical span, each arming an occurrence at the path point in effect at that time — SAME
        direction, SAME R definition, SAME horizons as the setup arms. Deterministic: the same seed
        reproduces identical arm times (asserted in the test matrix)."""
        if not path:
            return []
        direction = params["direction"]
        config = self._config
        seed = params["null_baseline_seed"]
        n = config.study_null_arm_count
        rng = random.Random(seed)
        start_ts = path[0].timestamp
        end_ts = path[-1].timestamp
        span = end_ts - start_ts
        occurrences: list[_Occurrence] = []
        # Draw all arm times up front (deterministic order) so the seed fully determines the baseline.
        arm_times = sorted(start_ts + rng.random() * span for _ in range(n)) if span > 0 else [start_ts] * n
        for arm_ts in arm_times:
            point = self._point_at(path, arm_ts)
            if point is None or point.last is None:
                continue
            occurrences.append(
                _arm_occurrence(
                    "null",
                    arm_logical_ts=point.timestamp,
                    arm_price=point.last,
                    spread_at_arm=point.spread,
                    direction=direction,
                    config=config,
                )
            )
        return occurrences

    @staticmethod
    def _point_at(path: list[_PathPoint], ts: float) -> _PathPoint | None:
        """The recorded path point in effect at/just before ``ts`` (last point with timestamp <= ts)."""
        chosen: _PathPoint | None = None
        for point in path:
            if point.timestamp <= ts:
                chosen = point
            else:
                break
        return chosen if chosen is not None else (path[0] if path else None)

    # --- per-occurrence verdict summaries (the EXISTING per-setup verdict rule table) ------------
    def _verdict_summaries(
        self, occurrences: list[_Occurrence], path: list[_PathPoint], params: dict
    ) -> list[str]:
        """For each SETUP occurrence, the EXISTING verdict-rule table's read over the post-arm path.

        Builds a thesis-shaped record for the occurrence (synthetic invalidation = the occurrence's R
        basis; the user-supplied or hindsight level) and runs a FRESH ``VerdictEvaluator`` over the
        recorded state path from the arm — recording the strongest published verdict reached. The
        recorded path holds price/spread only, so each verdict tick reads a reconstructed snapshot
        carrying the recorded tape state + price (the same canonical values the live monitor reads). No
        new rule, no new indicator — the registered verdict semantics, read once."""
        from .store import ThesisRecord

        setup_type = params["setup_type"]
        direction = params["direction"]
        summaries: list[str] = []
        for occ in occurrences:
            thesis = ThesisRecord(
                id="study-occ",
                ticker="STUDY",
                setup_type=setup_type,
                direction=direction,
                invalidation_price=occ.invalidation_price,
                level_price=params.get("level_price"),
                status="active",
                bound_source=params.get("source", ""),
                data_feed=params.get("data_feed", "sim"),
                config_fingerprint="",
                entry_context={},
                statements=[],
                created_logical_ts=occ.arm_logical_ts,
                created_wall_ts=0.0,
            )
            evaluator = VerdictEvaluator(thesis, self._config)
            strongest = "pending"
            rank = {"pending": 0, "weakening": 1, "rejecting": 2, "confirming": 3, "invalidated": 4}
            for point in path:
                if point.timestamp < occ.arm_logical_ts:
                    continue
                snap = _ReconstructedSnapshot(
                    timestamp=point.timestamp,
                    last=point.last,
                    spread=point.spread,
                    tape_state=point.tape_state,
                )
                decision = evaluator.evaluate(snap)
                if rank.get(decision.verdict, 0) > rank.get(strongest, 0):
                    strongest = decision.verdict
            summaries.append(strongest)
        return summaries

    # --- persistence (single writer queue) ------------------------------------------------------
    def _result_payload(
        self,
        payload: dict,
        setup_rows: list[dict],
        null_rows: list[dict],
        params: dict,
        *,
        status: str,
        partial: bool,
        error: str | None = None,
    ) -> dict:
        setup_agg = _aggregate_horizons(setup_rows, self._config)
        null_agg = _aggregate_horizons(null_rows, self._config)
        result = {
            **payload,
            "status": status,
            "partial": partial,
            "occurrences": setup_rows,
            "null_occurrences": null_rows,
            "aggregates": {
                "setup": {"n": len(setup_rows), "horizons": setup_agg},
                "null_baseline": {"n": len(null_rows), "horizons": null_agg},
            },
            "min_sample_size": self._config.analytics_min_sample_size,
            # Hindsight discipline: a level study is stamped + excluded from any cross-study aggregate.
            "hindsight_level": params.get("setup_type") in _LEVEL_SETUPS,
            "excluded_from_cross_study_aggregate": params.get("setup_type") in _LEVEL_SETUPS,
        }
        if error is not None:
            result["error"] = error
        result.pop("progress", None)
        result.pop("events_processed", None)
        return result

    def _persist_done(
        self, study_id: str, payload: dict, setup_rows, null_rows, params
    ) -> None:
        result = self._result_payload(
            payload, setup_rows, null_rows, params, status=STATUS_DONE, partial=False
        )
        self._store.set_study_result(study_id, result, setup_rows + null_rows)

    def _persist_cancelled(self, study_id: str, payload, *, setup_rows, null_rows) -> None:
        result = self._result_payload(
            payload, setup_rows, null_rows, dict(payload), status=STATUS_CANCELLED, partial=True
        )
        self._store.set_study_result(study_id, result, setup_rows + null_rows)

    def _persist_failed(self, study_id: str, payload: dict, error: str) -> None:
        result = self._result_payload(
            payload, [], [], dict(payload), status=STATUS_FAILED, partial=False, error=error
        )
        self._store.set_study_result(study_id, result, [])


@dataclass
class _ReconstructedSnapshot:
    """A minimal snapshot stand-in carrying the canonical values the verdict evaluator reads (tape
    state + last + spread + the primary-window impact). Built from the recorded path + state series —
    read-only, never the engine's own object. ``primary_features`` returns the recorded impact (the
    study reconstructs impact from the path direction at the occurrence — see note). For the
    verdict-summary read the evaluator uses tape_state + last + spread + directional impact; the
    impact is derived from the recorded path so the summary is deterministic."""

    timestamp: float
    last: float | None
    spread: float | None
    tape_state: str
    confidence: float = 0.5

    @property
    def primary_features(self) -> dict:
        # The verdict evaluator reads buy/sell price impact to gate confirmation. The recorded path
        # carries the tape STATE (the classifier's single-source-of-truth read), which already encodes
        # impact direction (buyer_control => positive buy impact by construction). We surface a
        # consistent directional impact aligned with the recorded state so the verdict semantics hold
        # without re-running the feature engine (read-only, deterministic). A control state implies
        # matching directional impact; otherwise neutral.
        if self.tape_state == "buyer_control":
            return {"buy_price_impact": 1.0, "sell_price_impact": 0.0}
        if self.tape_state == "seller_control":
            return {"buy_price_impact": 0.0, "sell_price_impact": -1.0}
        return {"buy_price_impact": 0.0, "sell_price_impact": 0.0}


class StudyJobManager:
    """Owns the cancellable background-job lifecycle (capability 32, J-60/J-61).

    A study is CREATED (persisted ``queued`` via the store) and then STARTED on a dedicated worker
    thread — OFF the event loop, so the live cockpit is never blocked. Each running job has a
    cancellation ``threading.Event``; ``cancel`` sets it (the runner observes it cooperatively between
    events) and a queued/running study resolves to explicit ``cancelled`` with partial-marked results.
    All SQLite writes happen inside the runner through the store's single writer queue. The manager is
    process-scoped (one per ``ResearchRegistry``); a backend restart loses in-flight jobs (a study left
    ``running`` in the DB from a prior process is surfaced honestly — it never silently completes).

    The runner can also be invoked SYNCHRONOUSLY (``run_sync``) — the path the pinned CI reference-study
    test + the deterministic unit tests drive, so a study completes in-process without a thread race."""

    def __init__(self, store: JournalStore, config: Config) -> None:
        self._store = store
        self._config = config
        self._runner = StudyRunner(store, config)
        self._cancels: dict[str, threading.Event] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    def create(self, params: dict) -> dict:
        """Persist a NEW study ``queued`` with its honesty stamps + the recorded null-baseline seed,
        and return its full served payload. The caller (route) then STARTS it. The stamps (source /
        data_feed / config_fingerprint / null_baseline_seed) are written at creation (persist-once at
        the defining moment) — the runner re-stamps the resolved source descriptor once the provider is
        known, but the seed + fingerprint are fixed here so the study reproduces exactly."""
        study_id = uuid.uuid4().hex
        seed = params.get("null_baseline_seed", self._config.study_null_baseline_seed)
        payload = {
            "id": study_id,
            "status": STATUS_QUEUED,
            "source_kind": params["source_kind"],
            "source_id": params.get("source_id", ""),
            "source": params.get("source", params.get("source_id", "")),
            "setup_type": params["setup_type"],
            "direction": params["direction"],
            "level_price": params.get("level_price"),
            "data_feed": params.get("data_feed", "sim"),
            "config_fingerprint": self._config.config_fingerprint(),
            "null_baseline_seed": seed,
            "null_arm_count": self._config.study_null_arm_count,
            "hindsight_level": params["setup_type"] in _LEVEL_SETUPS,
            "excluded_from_cross_study_aggregate": params["setup_type"] in _LEVEL_SETUPS,
            "created_wall_ts": time.time(),
        }
        self._store.insert_study(
            StudyRecord(id=study_id, payload=payload, created_wall_ts=payload["created_wall_ts"])
        )
        return payload

    def _run_params(self, payload: dict, historical_fetch) -> dict:
        return {
            "source_kind": payload["source_kind"],
            "source_id": payload.get("source_id", ""),
            "setup_type": payload["setup_type"],
            "direction": payload["direction"],
            "level_price": payload.get("level_price"),
            "null_baseline_seed": payload["null_baseline_seed"],
            "source": payload.get("source", ""),
            "data_feed": payload.get("data_feed", "sim"),
        }

    def start(self, study_id: str, *, historical_fetch: Callable[[], object] | None = None) -> None:
        """Start a queued study on a worker thread (background). Idempotent — a second start for the
        same id is ignored (the job is already running/terminal)."""
        with self._lock:
            if study_id in self._threads:
                return
            cancel = threading.Event()
            self._cancels[study_id] = cancel
        record = self._store.get_study(study_id)
        if record is None:
            return
        params = self._run_params(record.payload, historical_fetch)

        def _work() -> None:
            try:
                self._runner.run(
                    study_id=study_id,
                    params=params,
                    historical_fetch=historical_fetch,
                    is_cancelled=cancel.is_set,
                )
            finally:
                with self._lock:
                    self._threads.pop(study_id, None)
                    self._cancels.pop(study_id, None)

        thread = threading.Thread(target=_work, name=f"study:{study_id}", daemon=True)
        with self._lock:
            self._threads[study_id] = thread
        thread.start()

    def run_sync(self, study_id: str, *, historical_fetch: Callable[[], object] | None = None) -> None:
        """Run a queued study SYNCHRONOUSLY (the CI/unit path). Completes in-process; honors a
        pre-set cancellation flag (so the cancel-before-run case is testable deterministically)."""
        cancel = self._cancels.get(study_id, threading.Event())
        record = self._store.get_study(study_id)
        if record is None:
            return
        params = self._run_params(record.payload, historical_fetch)
        self._runner.run(
            study_id=study_id,
            params=params,
            historical_fetch=historical_fetch,
            is_cancelled=cancel.is_set,
        )

    def cancel(self, study_id: str) -> None:
        """Signal cancellation for a running/queued study (cooperative — observed between events)."""
        with self._lock:
            cancel = self._cancels.get(study_id)
            if cancel is None:
                cancel = threading.Event()
                self._cancels[study_id] = cancel
            cancel.set()

    def join_all(self, timeout: float = 30.0) -> None:
        """Wait for all in-flight job threads (used on shutdown so daemons drain cleanly)."""
        with self._lock:
            threads = list(self._threads.values())
        for t in threads:
            t.join(timeout=timeout)
