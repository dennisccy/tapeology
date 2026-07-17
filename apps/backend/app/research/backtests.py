"""Deterministic backtest runner + cancellable job manager (era-3 capability 4, J-03).

THE single computing owner of Data Contract row 31 (backtest reports): a backtest replays ONE
registered dataset UNPACED through a fresh engine — consumed EXCLUSIVELY via
``DatasetStore.replay`` (row 30's public API; this module never opens or parses a dataset file
itself) — arms simulated entries per the config-owned strategy grammar v1 (row 34,
``Config.strategy_definition``), simulates fills at recorded prices adjusted by the configured
slippage model, applies the configured fee model, and persists the report ONCE. The routes and
the MCP ``backtests`` proxy serve the stored rows VERBATIM ever after — no recomputation on read.

The fresh engine is constructed with the run's RESOLVED profile config (era-3 capability 2, J-06:
``Config.resolved_for_profile``) — ``default`` passes the SAME object unchanged (byte-identical
engine construction, the frozen-default anti-goal); a registered candidate passes a FRESH per-run
overlay Config, applied ONLY to this one replay, never to the shared ``CONFIG`` singleton. Every
OTHER computation in this module (fees, slippage, the strategy grammar, the null baseline) still
reads the manager's base ``self._config`` — a profile is an engine/classifier concern (row 33),
never a strategy-grammar one (row 34).

Every fill in this module is the ONE permitted "fill" in the whole product: computed OFFLINE
against recorded historical tape, labeled simulated via the ``REGISTER`` string carried in every
report payload, and sent nowhere (the no-live-execution anti-goal; enforced repo-wide by
``tests/test_no_execution_path.py``).

The disciplines, clause by clause:

  * **Entries reuse the studies' state-native arming — no new indicator, no new threshold.** Each
    strategy setup x direction combo arms when its premise tape state (via the studies' ONE
    ``_premise_state`` mapping) has held CONTINUOUSLY for ``study_arm_sustain_seconds``, gated by
    ``study_arm_cooldown_seconds`` per combo — the exact sustained-premise + cooldown rules and
    constants the study runner proved. ONE OPEN TRADE AT A TIME: while a simulated position is
    open no new entry arms; eligibility is re-checked every recorded event, exits are processed
    BEFORE arming at each event, and concurrent eligibility resolves in the strategy's declared
    setup order — all deterministic, all documented in the config-owned definition.

  * **Exits: R-stop / reward-target / horizon / state-flip / dataset_end.** The R-stop is the
    studies' arm-instant synthetic invalidation (the REUSED ``_synthetic_invalidation`` helper —
    ``study_occurrence_r_spread_multiple`` x arm spread, floored at ``study_occurrence_r_floor``,
    adverse side), with R via the shared ``marks.r_basis`` (row 27 — never a second formula); it
    triggers on a recorded print at/through the invalidation. ``structure_tape`` AND
    ``structure_tape_map`` trades (era-4 J-05 / era-5B J-04, gated on the arming ``level``/class
    being present, never on the strategy id) instead use a class-scaled, LEVEL-relative
    invalidation (``_class_scaled_invalidation``) and additionally carry a reward-target exit
    (``_class_scaled_target`` — a class R-multiple bounded by the next opposing level/band resolved
    at arm time); v1/null trades never carry a ``target_price`` and so can never reach that exit.
    The state-flip exit fires when the tape reads the OPPOSING control state (the
    studies' ``_control_state`` vocabulary). The time horizon exits at the first recorded event
    at/after ``strategy_exit_horizon_seconds`` past entry. A trade still open when the stream ends
    is handled EXPLICITLY and deterministically: forced exit at the LAST recorded price, labeled
    ``dataset_end`` — documented, never silent. Exit precedence within one event is fixed and
    documented: r_stop, then reward_target, then state_flip, then horizon. Exit evaluation begins
    strictly AFTER the entry event.

  * **Fills, fees, and the two unit systems.** Entry fills at the recorded arm price adjusted
    ADVERSELY by ``strategy_slippage_spread_fraction`` x the recorded at-that-event spread; exit
    fills adversely likewise at the recorded exit price (a moment with no usable quote
    contributes zero slippage — honest absence, never a fabricated cost). Each fill pays
    ``max(strategy_fee_per_share x shares, strategy_fee_min_per_trade)``. Position size is the
    fixed notional: ``shares = strategy_dollars_per_r / R basis`` (v1/null); ``structure_tape``
    AND ``structure_tape_map`` trades (era-4 J-05 / era-5B J-04) scale that SAME fixed notional by
    the arming level's class size multiple (``structure_tape_size_multiple_by_class``) — still a
    per-trade SIMULATED notional only. R and $ are two disclosed unit systems over the SAME
    measurement — GROSS from recorded prices, NET from fills minus fees, and a dollar figure never
    exists without its R counterpart. The per-class (A/B/C) PnL breakdown (era-4 J-05, Data
    Contract row 42) partitions the SAME trade population by ``trade["level"]["class"]`` —
    computed once, alongside the strategy-level aggregate, and served verbatim.

  * **The seeded random-entry null baseline.** ``backtest_null_entry_count`` entry instants (and
    per-entry random directions) drawn from the recorded seed over the SAME dataset, exiting
    under the SAME rules / fees / slippage (the same ``_exit_reason`` + ``_close_trade`` code
    paths). Null entries are simulated INDEPENDENTLY (random entries replace the arming rule —
    that is the point of the baseline); each is labeled ``random_null``, never dressed up as a
    real setup. The seed is recorded in the report (the ``study_null_baseline_seed`` precedent)
    so the baseline reproduces exactly.

  * **Byte-identical re-runs.** The persisted payload separates run-identity metadata (record
    id, ``created_wall_ts``, job status, request echo) from the deterministic ``result`` block
    (trades, aggregates, null baseline, provenance, register). An identical request re-run
    reproduces the ``result`` block byte-for-byte — the unit the acceptance tests compare.

  * **Cancellable job like studies; honest failures.** ``queued -> running -> done | cancelled |
    failed`` persisted through the SAME single writer queue; cancellation is cooperative
    (observed between events) and a cancelled backtest carries NO result block — a partially
    computed simulated PnL is a misleading number, so it is honestly OMITTED rather than served
    partial. A dataset integrity error (or any failure) persists an explicit ``failed`` record
    carrying the error — never silence, never fabricated results. A window arming zero trades is
    a DONE report with an empty trade list and n=0 aggregates (win rate / drawdown honestly
    ``None``) — an answer, not an error.
"""

from __future__ import annotations

import bisect
import random
import threading
import time
import uuid

from ..config import Config, PROFILE_DEFAULT, STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID
from .bars import BarStore
from .datasets import DatasetIntegrityError, DatasetNotFound, DatasetStore
from .levels import compute_levels, level_change_points, CLASS_A, CLASS_B, CLASS_C
from .marks import r_basis
from .store import BacktestRecord, JournalStore
from .tradability import RESISTANCE, SUPPORT, basis_day_key, compute_tradability

# The status vocabulary and the state-native helpers are REUSED from the studies module (one
# owner per literal / per mapping — never a second copy): the premise-state arming map, the
# control-state vocabulary the state-flip exit reads, the arm-instant synthetic invalidation,
# the recorded-path point shape, and the throttled progress cadence.
from .studies import (
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_FAILED,
    STATUS_QUEUED,
    STATUS_RUNNING,
    TERMINAL_STATUSES,
    _control_state,
    _premise_state,
    _synthetic_invalidation,
    _PathPoint,
    _PROGRESS_EVERY,
)

__all__ = [
    "BacktestJobManager",
    "BacktestRunner",
    "EXIT_DATASET_END",
    "EXIT_HORIZON",
    "EXIT_REWARD_TARGET",
    "EXIT_R_STOP",
    "EXIT_STATE_FLIP",
    "NULL_SETUP_TYPE",
    "PROFILE_DEFAULT",
    "REGISTER",
    "STATUS_CANCELLED",
    "STATUS_DONE",
    "STATUS_FAILED",
    "STATUS_QUEUED",
    "STATUS_RUNNING",
    "TERMINAL_STATUSES",
]

# The visible honesty register carried by EVERY report payload (the PnL-honesty constraint):
# a simulated measurement of the past under disclosed assumptions — never live results.
REGISTER = "simulated — assumed fees/slippage — not indicative of live results"

# The null-baseline population label — an explicit non-setup so a random entry can never be
# mistaken for (or pooled into) a real strategy setup.
NULL_SETUP_TYPE = "random_null"

# Exit reasons (one explicit copy each — the iter-15 own-copy lesson).
EXIT_R_STOP = "r_stop"
# era-4 J-05: the class-scaled take-profit exit (structure_tape / structure_tape_map trades only —
# v1/null trades carry no ``target_price`` and so can never reach this reason).
EXIT_REWARD_TARGET = "reward_target"
EXIT_HORIZON = "horizon"
EXIT_STATE_FLIP = "state_flip"
EXIT_DATASET_END = "dataset_end"


def _opposing_control_state(direction: str) -> str:
    """The OPPOSING control state whose read is the state-flip exit (existing vocabulary only):
    a long is broken by ``seller_control``, a short by ``buyer_control`` — via the studies' one
    ``_control_state`` mapping, never a second copy of the state names."""
    return _control_state("short" if direction == "long" else "long")


# structure_tape's two "setup_type" values (era-4 J-04, its OWN vocabulary — never v1's setup
# names): which of the two tape-confirmed readings armed the trade.
_STRUCTURE_TAPE_REJECTION = "rejection"
_STRUCTURE_TAPE_BREAKTHROUGH = "breakthrough"


def _structure_tape_reading(tape_state: str, entries: dict) -> tuple[str, str] | None:
    """``(direction, setup_type)`` for the reading ``tape_state`` confirms, or ``None`` if it
    confirms NEITHER structure_tape reading (``unclear``, or any state this strategy does not
    read). The rejection/breakthrough state maps are disjoint (the tape engine's five states are
    mutually exclusive at any one instant), so at most one reading — and one direction — can ever
    match a given state."""
    for direction, state in entries["rejection_states"].items():
        if tape_state == state:
            return direction, _STRUCTURE_TAPE_REJECTION
    for direction, state in entries["breakthrough_states"].items():
        if tape_state == state:
            return direction, _STRUCTURE_TAPE_BREAKTHROUGH
    return None


def _level_provenance(level: dict, zone: dict) -> dict:
    """The arming level's stamped provenance (price/timeframe/class) — the ONE specific classified
    level (never the whole zone) that armed the trade, carrying the CONFLUENCE ZONE's honest A/B/C
    class (an unclassified lone level has no class and never reaches here — only zone members are
    ever tested)."""
    return {"price": level["price"], "timeframe": level["timeframe"], "class": zone["class"]}


# --- class-scaled stop + reward-target (era-4 capability 5, J-05; structure_tape trades only) -----


def _class_scaled_invalidation(
    entry_price: float, level_price: float, level_class: str, direction: str, config: Config
) -> float:
    """The class-scaled, LEVEL-relative invalidation for a structure_tape trade (Data Contract row
    41 extension): a stop placed ``config.structure_tape_stop_bps_by_class[level_class]`` basis
    points beyond the ARMING LEVEL's own price (never the entry fill price — goal.md's "a stop
    ~1bp beyond it" names the level, not wherever the entry print landed inside the confirmation
    band), on the adverse side (below for a long, above for a short).

    A rejection entry may arm anywhere inside the proximity band, on EITHER side of the level, so
    the level-relative price alone could occasionally land AT OR THROUGH the entry print itself
    (an invalid stop — one that would already be violated at arm time). The invalidation is
    therefore the level-relative price when it is genuinely on the adverse side of entry, else a
    fallback at the SAME class-bps distance measured from the entry price instead (still
    config-owned, still the identical class distance — merely re-anchored so the stop is always
    structurally valid). Distinct from the shared, spread-based ``_synthetic_invalidation``
    v1/null keep calling unparameterized (v1 has no arming level to anchor a stop to)."""
    band = level_price * (config.structure_tape_stop_bps_by_class[level_class] / 10_000.0)
    if direction == "long":
        level_relative = level_price - band
        return level_relative if level_relative < entry_price else entry_price - band
    level_relative = level_price + band
    return level_relative if level_relative > entry_price else entry_price + band


def _zone_nearest_price(zone: dict, entry_price: float) -> float:
    """The zone's own member level NEAREST ``entry_price`` — a confluence zone spans a small price
    range (bounded by ``sr_confluence_band_bps``); its nearest member is the honest "edge of
    structure" price representing it for distance comparisons, never an arbitrary anchor."""
    return min(zone["levels"], key=lambda lvl: abs(lvl["price"] - entry_price))["price"]


def _next_opposing_zone_price(
    zones: list[dict], arming_zone: dict, entry_price: float, direction: str
) -> float | None:
    """era-4 J-05: the nearest OTHER zone's representative price on the side ``direction`` implies
    (above entry for a long, below for a short) — the reward-target's "next opposing level",
    excluding the arming zone itself BY IDENTITY (a rejection entry sits AT its own arming level's
    price, which must never be mistaken for its own target). ``None`` when nothing qualifies on
    that side — an honest fallback; the reward-target then bounds by the class R-multiple alone,
    never a fabricated level."""
    candidates = [_zone_nearest_price(z, entry_price) for z in zones if z is not arming_zone]
    if direction == "long":
        side = [p for p in candidates if p > entry_price]
    else:
        side = [p for p in candidates if p < entry_price]
    if not side:
        return None
    return min(side, key=lambda p: abs(p - entry_price))


# --- structure_tape_map candidate sourcing (era-5B capability 5, J-04): the IDENTICAL zone/level
# helpers directly above, twinned for TRADABLE-MAP BANDS (``research/tradability.py``) instead of
# raw confluence zones (``research/levels.py``) — never imported from ``tradability.py`` itself
# (that module owns band COMPUTATION; arming candidate SELECTION over an already-computed band
# list is this module's own, existing "reused technique, twinned container" idiom — the identical
# relationship ``_next_opposing_zone_price``/``_zone_nearest_price`` already have to their zone
# input). A band's ``members`` list is the EXACT SAME level-dict shape (price/timeframe/type/
# touch_count) a zone's ``levels`` list carries, and a band's ``class`` key is read the identical
# way a zone's is — so ``_level_provenance`` above is REUSED UNCHANGED for a band, no twin needed. --


def _band_nearest_price(band: dict, entry_price: float) -> float:
    """The band's own member level NEAREST ``entry_price`` — the ``_zone_nearest_price`` technique,
    applied to a band's ``members`` list."""
    return min(band["members"], key=lambda lvl: abs(lvl["price"] - entry_price))["price"]


def _next_opposing_band_price(
    bands: list[dict], arming_band: dict, entry_price: float, direction: str
) -> float | None:
    """era-5B J-04: the nearest OTHER band's representative price on the side ``direction`` implies
    — the ``_next_opposing_zone_price`` technique, applied to the tradable map's bands. Considers
    EVERY other band regardless of its own inherited class (including an unclassified ``class:
    null`` band — the reward-target's "next opposing level" is a PRICE-STRUCTURE question, not a
    conviction one; only the ARMING band's own class scales the stop/reward/size, exactly as an
    unclassified zone never existed for ``_next_opposing_zone_price`` to consider in the first
    place). Excludes the arming band itself BY IDENTITY. ``None`` when nothing qualifies on that
    side — the identical honest fallback."""
    candidates = [_band_nearest_price(b, entry_price) for b in bands if b is not arming_band]
    if direction == "long":
        side = [p for p in candidates if p > entry_price]
    else:
        side = [p for p in candidates if p < entry_price]
    if not side:
        return None
    return min(side, key=lambda p: abs(p - entry_price))


def _structure_tape_map_side_for_reading(direction: str, setup_type: str) -> str:
    """Which tradable-map SIDE (``tradability.SUPPORT`` / ``RESISTANCE``) a (direction, setup_type)
    reading tests — goal.md's own floor/ceiling language for the tape-confirmation mapping
    (``structure_tape_rejection_state_by_direction`` / ``..._breakthrough_state_by_direction``'s
    own docstring in ``config.py``), made MECHANICAL now that a BAND — unlike a raw classified
    level/zone, which carries no side at all — has an explicit ``side`` field to test it against: a
    REJECTION defends the level it sits at (long defends a FLOOR — a support band; short defends a
    CEILING — a resistance band); a BREAKTHROUGH moves BEYOND the level in its own direction (long
    breaks a CEILING — resistance; short breaks a FLOOR — support).

    A deliberate, flagged judgment call (see the dev handoff): ``_structure_tape_arm`` above has no
    equivalent side filter because raw confluence zones carry no side at all, so it tests every
    zone regardless of which side of price it sits on. Bands make the correct, side-aware test
    possible for the first time — without it, a short "breakthrough" could arm against a distant
    RESISTANCE band merely because price sits numerically below it, which is not a breakthrough of
    anything. This never changes ``structure_tape``'s own byte-identical behaviour (a separate
    branch, untouched)."""
    if setup_type == _STRUCTURE_TAPE_REJECTION:
        return SUPPORT if direction == "long" else RESISTANCE
    return RESISTANCE if direction == "long" else SUPPORT


def _class_scaled_target(
    entry_price: float,
    direction: str,
    level_class: str,
    r_basis_value: float,
    opposing_price: float | None,
    config: Config,
) -> float:
    """era-4 J-05: the reward-target price for a structure_tape trade — "R:R toward the next
    opposing level" (goal.md), genuinely config-bounded both ways. The take-profit distance is the
    SMALLER of (a) this class's R-multiple (``structure_tape_reward_r_multiple_by_class``) times
    the trade's own R basis, and (b) the distance to ``opposing_price`` (resolved at arm time from
    the SAME as-of ``compute_levels`` read — never a second/future levels read) when one was
    found. Bounding by the real next opposing level keeps the target honest (never demanding a
    move past already-detected structure); bounding by the class multiple keeps it from demanding
    an unrealistic R when that zone sits very far away. ``opposing_price`` is ``None`` when no
    zone qualified on that side — an honest fallback to the pure R-multiple alone."""
    sign = 1.0 if direction == "long" else -1.0
    distance = config.structure_tape_reward_r_multiple_by_class[level_class] * r_basis_value
    if opposing_price is not None:
        distance = min(distance, abs(opposing_price - entry_price))
    return entry_price + sign * distance


def _aggregate(trades: list[dict]) -> dict:
    """The report aggregates over one trade population (setup or null), computed ONCE here.

    net AND gross, R AND $, win rate, max drawdown (R), n. Honest emptiness: n=0 serves zero
    sums with ``win_rate`` / ``max_drawdown_r`` ``None`` (no rate on an empty pool — never a
    dishonest 0%). Win rate counts trades positive NET of costs; max drawdown is the deepest
    peak-to-trough of the cumulative net-R curve in trade order (0.0 when nothing ever gave
    back — a real measured zero, distinct from the n=0 ``None``)."""
    n = len(trades)
    gross_r = sum(t["gross_r"] for t in trades)
    net_r = sum(t["net_r"] for t in trades)
    gross_usd = sum(t["gross_usd"] for t in trades)
    net_usd = sum(t["net_usd"] for t in trades)
    win_rate = (sum(1 for t in trades if t["net_r"] > 0) / n) if n else None
    if n:
        peak = 0.0
        cum = 0.0
        dd = 0.0
        for t in trades:
            cum += t["net_r"]
            peak = max(peak, cum)
            dd = max(dd, peak - cum)
        max_dd = dd
    else:
        max_dd = None
    return {
        "n": n,
        "gross_r": gross_r,
        "net_r": net_r,
        "gross_usd": gross_usd,
        "net_usd": net_usd,
        "win_rate": win_rate,
        "max_drawdown_r": max_dd,
    }


def _aggregate_by_class(trades: list[dict], config: Config) -> dict:
    """era-4 J-05 (Data Contract row 42): the per-class (A/B/C) PnL breakdown — the SAME
    ``_aggregate`` computed over each class's OWN partition of ``trades`` (keyed by
    ``trade["level"]["class"]``; structure_tape trades only — v1/null trades carry no ``level``
    key and so contribute to NO class, an honest all-empty three-way split for a strategy that
    never touches levels at all). Always all THREE classes, computed ONCE here at persist time —
    this module's own established discipline (never re-derived at read, unlike
    ``pnl_ledger.ledger_projection``'s read-time label). Sub-minimum-n classes carry
    ``insufficient_sample`` (``n`` still present) — REUSES the existing ``pnl_min_sample_size``
    floor (the ``edge_report.py`` precedent: "reuses that field rather than minting a third
    minimum"), never a fourth new threshold. A class with zero trades is the honest
    ``_aggregate([])`` emptiness (n=0, rates ``None``), never fabricated."""
    by_class: dict[str, list[dict]] = {CLASS_A: [], CLASS_B: [], CLASS_C: []}
    for t in trades:
        level = t.get("level")
        if level is not None:
            by_class[level["class"]].append(t)
    breakdown: dict[str, dict] = {}
    for cls in (CLASS_A, CLASS_B, CLASS_C):
        agg = _aggregate(by_class[cls])
        agg["insufficient_sample"] = agg["n"] < config.pnl_min_sample_size
        breakdown[cls] = agg
    return breakdown


class _StructureArmMemo:
    """goal-fast_wall J-03 ("the arm memo", ``docs/goal.md`` Key Capability 3): a small per-run
    accelerator serving ``structure_tape``/``structure_tape_map``'s arming checks from the
    handful of real level/tradability states a session actually has, instead of re-running the
    FULL ``compute_levels``/``compute_tradability`` pipeline on every confirming tick.

    In-memory, ONE instance built fresh inside ``_structure_tape_trades`` /
    ``_structure_tape_map_trades`` -- once per ``BacktestRunner.run()`` call, never shared across
    runs, never persisted to disk or any store: a rebuildable, non-canonical accelerator (the
    interlude's "never a source of truth" discipline -- deleting/skipping it loses nothing, since
    every miss falls through to the SAME canonical owner call a ``memo=None`` caller would make).

    ``levels_at(as_of_epoch)`` buckets ``as_of_epoch`` via ``bisect.bisect_right`` into the
    ``levels.level_change_points`` tuple resolved ONCE at construction -- the contract that
    function documents (``compute_levels`` is constant between two consecutive change points)
    means every ``as_of_epoch`` landing in the SAME bucket shares a byte-identical result, so the
    real owner is called at most once per bucket actually visited. ``tradability_at(as_of_epoch)``
    buckets by ``tradability.basis_day_key(as_of_epoch)`` (constant per UTC session date) the
    identical way. Both are a PURE memoization of an EXISTING owner call -- never a second
    computation path (the two source-introspection guard tests pin this: the literal
    ``compute_levels(``/``compute_tradability(`` owner calls stay present in
    ``_structure_tape_arm``'s/``_structure_tape_map_arm``'s own fallback branch, and no
    level-internal helper name is ever referenced here)."""

    def __init__(self, bar_store: BarStore, symbol: str, config: Config) -> None:
        self._bar_store = bar_store
        self._symbol = symbol
        self._config = config
        self._change_points = level_change_points(bar_store, symbol)
        self._levels_cache: dict[int, dict] = {}
        self._tradability_cache: dict[str, dict] = {}

    def levels_at(self, as_of_epoch: float) -> dict:
        bucket = bisect.bisect_right(self._change_points, as_of_epoch)
        cached = self._levels_cache.get(bucket)
        if cached is None:
            cached = compute_levels(self._bar_store, self._symbol, as_of_epoch, self._config)
            self._levels_cache[bucket] = cached
        return cached

    def tradability_at(self, as_of_epoch: float) -> dict:
        key = basis_day_key(as_of_epoch)
        cached = self._tradability_cache.get(key)
        if cached is None:
            cached = compute_tradability(self._bar_store, self._symbol, as_of_epoch, self._config)
            self._tradability_cache[key] = cached
        return cached


class BacktestRunner:
    """Runs one backtest end-to-end and persists its report ONCE (row 31's single computer).

    Deterministic, seeded, unpaced, single-threaded per run: the dataset replays through
    ``DatasetStore.replay`` (a fresh engine per run, checksum-verified load — the ONLY dataset
    access path), the recorded snapshot path is held in memory for the one pass, and both the
    strategy trades and the seeded null baseline are simulated against it. All persistence goes
    through the injected ``JournalStore``'s single writer queue."""

    def __init__(self, store: JournalStore, config: Config) -> None:
        self._store = store
        self._config = config

    def run(
        self,
        *,
        backtest_id: str,
        params: dict,
        dataset_store: DatasetStore,
        is_cancelled,
        bar_store: BarStore | None = None,
    ) -> None:
        """Execute the backtest, persisting status transitions through the store. Honors
        cancellation cooperatively (between events and before persist). Never raises out —
        every failure is captured as an explicit ``failed`` record (never an empty success).

        ``bar_store`` (era-4 J-04) is the run's row-39 level source, threaded in ONLY at call
        time (the ``dataset_store`` precedent) — never baked into the constructor. It is read
        ONLY by the ``structure_tape`` branch of ``_strategy_trades``; v1 never touches it.
        ``None`` (the default — every existing v1 caller is unaffected) makes ``structure_tape``
        honestly arm nothing, exactly like a symbol with no recorded bar series."""
        record = self._store.get_backtest(backtest_id)
        payload = dict(record.payload) if record is not None else dict(params)
        try:
            if is_cancelled():
                self._persist_terminal(backtest_id, payload, STATUS_CANCELLED)
                return
            self._store.update_backtest_payload(
                backtest_id, {**payload, "status": STATUS_RUNNING}
            )
            # The per-run RESOLVED profile config (J-06): default is self._config UNCHANGED
            # (byte-identical); a registered candidate is a FRESH overlay — self._config is never
            # mutated. Route-guarded (422 for an unregistered profile); defensive honesty here.
            run_config = self._config.resolved_for_profile(params["profile"])
            if run_config is None:
                raise ValueError(f"unknown profile '{params['profile']}'")
            # The verified metadata load (id -> 404-style DatasetNotFound; corrupt/tampered ->
            # DatasetIntegrityError) — embedded VERBATIM in the report's provenance.
            dataset_meta = dataset_store.get(params["dataset_id"])
            path, cancelled = self._replay(
                dataset_store, params["dataset_id"], backtest_id, payload, is_cancelled, run_config
            )
            if cancelled or is_cancelled():
                self._persist_terminal(backtest_id, payload, STATUS_CANCELLED)
                return
            strategy = self._config.strategy_definition(params["strategy_id"])
            if strategy is None:  # route-guarded (422); defensive honesty here
                raise ValueError(f"unknown strategy '{params['strategy_id']}'")
            trades = self._strategy_trades(
                path,
                strategy,
                bar_store=bar_store,
                symbol=dataset_meta.get("symbol"),
                epoch_anchor=dataset_meta.get("epoch_anchor"),
            )
            null_trades = self._null_trades(path, params["null_baseline_seed"])
            result = {
                "register": REGISTER,
                # Provenance: the dataset's stored metadata VERBATIM (id + checksum + window +
                # feed + counts), the resolved strategy config echoed verbatim, the profile id,
                # and the config fingerprint of the RESOLVED per-run config (the existing hasher —
                # never a second computation; folds the profile through the overlaid, always-
                # hashed engine fields, so default's fingerprint stays untouched and a candidate's
                # is distinct).
                "dataset": dataset_meta,
                "strategy_id": params["strategy_id"],
                "strategy": strategy,
                "profile": params["profile"],
                "config_fingerprint": run_config.config_fingerprint(),
                "trades": trades,
                "aggregates": _aggregate(trades),
                # era-4 J-05 (Data Contract row 42): the per-class (A/B/C) breakdown of the SAME
                # trade population above — computed once here, alongside the strategy-level
                # aggregate, and served verbatim ever after (never the null baseline, which is
                # strategy-agnostic and carries no level/class provenance at all).
                "aggregates_by_class": _aggregate_by_class(trades, self._config),
                "null_baseline": {
                    "seed": params["null_baseline_seed"],
                    "entry_count": self._config.backtest_null_entry_count,
                    "trades": null_trades,
                    "aggregates": _aggregate(null_trades),
                },
            }
            self._persist_terminal(backtest_id, payload, STATUS_DONE, result=result)
        except (DatasetNotFound, DatasetIntegrityError) as exc:
            self._persist_terminal(backtest_id, payload, STATUS_FAILED, error=str(exc))
        except Exception as exc:  # any unexpected error -> explicit failed, never silence
            self._persist_terminal(
                backtest_id, payload, STATUS_FAILED, error=f"backtest failed: {exc}"
            )

    # --- replay (unpaced, cooperative cancellation, via the ONE public dataset API) -----------
    def _replay(
        self,
        dataset_store: DatasetStore,
        dataset_id: str,
        backtest_id: str,
        payload: dict,
        is_cancelled,
        config: Config,
    ) -> tuple[list[_PathPoint], bool]:
        """Replay the stored dataset unpaced through ``DatasetStore.replay`` (a FRESH engine,
        verified load) recording the snapshot path in memory ONCE. Cancellation is checked
        between events; progress is persisted every ``_PROGRESS_EVERY`` events (throttled —
        never a hot path). Tape data lives ONLY in this in-job memory — never persisted.

        ``config`` is the run's RESOLVED profile config (``Config.resolved_for_profile`` — J-06):
        ``default`` passes ``self._config`` UNCHANGED (byte-identical engine construction to
        pre-J-06); a candidate passes a FRESH per-run overlay — ``self._config`` itself is never
        mutated, so concurrent runs under different profiles never race."""
        path: list[_PathPoint] = []
        total = 0
        cancelled = False
        for snapshot in dataset_store.replay(dataset_id, config):
            if is_cancelled():
                cancelled = True
                break
            path.append(
                _PathPoint(
                    timestamp=snapshot.timestamp,
                    last=snapshot.last,
                    spread=snapshot.spread,
                    tape_state=snapshot.tape_state,
                )
            )
            total += 1
            if total % _PROGRESS_EVERY == 0:
                hb = {**payload, "status": STATUS_RUNNING, "events_processed": total}
                self._store.update_backtest_payload(backtest_id, hb)
        return path, cancelled

    # --- strategy simulation (one pass, one open trade at a time) ------------------------------
    def _strategy_trades(
        self,
        path: list[_PathPoint],
        strategy: dict,
        *,
        bar_store: BarStore | None = None,
        symbol: str | None = None,
        epoch_anchor: float | None = None,
    ) -> list[dict]:
        """Arm and simulate ONE registered strategy's trades over the recorded path (era-4 J-04:
        dispatches to the additive ``structure_tape`` branch; era-5B J-04 adds the additive
        ``structure_tape_map`` branch beside it; v1's own branch — and the code below it — is
        UNCHANGED, so v1 stays byte-identical).

        v1: ONE deterministic interleaved pass: at each recorded event the open trade's exit is
        evaluated FIRST, then (if flat) each declared setup x direction combo may arm per the
        sustained-premise rule. Premise runs are tracked continuously (a run does not reset
        because a position was open); a combo blocked by an open position arms at the first
        eligible later event of the SAME sustained run. A trade still open at the last event
        exits ``dataset_end``."""
        if strategy["strategy_id"] == STRATEGY_TAPE_ID:
            return self._structure_tape_trades(path, strategy, bar_store, symbol, epoch_anchor)
        if strategy["strategy_id"] == STRATEGY_TAPE_MAP_ID:
            return self._structure_tape_map_trades(path, strategy, bar_store, symbol, epoch_anchor)
        config = self._config
        sustain = strategy["entries"]["arm_sustain_seconds"]
        cooldown = strategy["entries"]["arm_cooldown_seconds"]
        horizon = strategy["exits"]["horizon_seconds"]
        combos = [(s["setup_type"], s["direction"]) for s in strategy["entries"]["setups"]]
        run_since: dict[tuple, float | None] = {c: None for c in combos}
        armed_this_run: dict[tuple, bool] = {c: False for c in combos}
        cooldown_until: dict[tuple, float] = {c: float("-inf") for c in combos}
        position: dict | None = None
        trades: list[dict] = []
        for i, point in enumerate(path):
            # Exits FIRST (strictly after the entry event), so a just-freed slot may re-arm at
            # this same event deterministically (the declared-order rule).
            if position is not None and i > position["index"] and point.last is not None:
                reason = self._exit_reason(position, point, horizon)
                if reason is not None:
                    trades.append(self._close_trade(position, point, reason))
                    position = None
            for combo in combos:
                setup_type, direction = combo
                premise = _premise_state(setup_type, direction)
                if point.tape_state == premise:
                    if run_since[combo] is None:
                        run_since[combo] = point.timestamp
                        armed_this_run[combo] = False
                    sustained = point.timestamp - run_since[combo] >= sustain
                    if (
                        sustained
                        and not armed_this_run[combo]
                        and point.timestamp >= cooldown_until[combo]
                        and point.last is not None
                        and position is None
                    ):
                        position = self._arm_trade(i, point, setup_type, direction)
                        armed_this_run[combo] = True
                        cooldown_until[combo] = point.timestamp + cooldown
                else:
                    run_since[combo] = None
                    armed_this_run[combo] = False
        if position is not None:
            # Explicit deterministic stream-end handling: forced exit at the LAST recorded
            # price, labeled dataset_end — documented, never silent, never extrapolated.
            trades.append(self._close_trade(position, path[-1], EXIT_DATASET_END))
        return trades

    # --- structure_tape simulation (era-4 J-04): one open trade at a time, tape-confirmed --------
    def _structure_tape_trades(
        self,
        path: list[_PathPoint],
        strategy: dict,
        bar_store: BarStore | None,
        symbol: str | None,
        epoch_anchor: float | None,
    ) -> list[dict]:
        """Arm and simulate ``structure_tape``'s trades over the recorded path — the SAME
        one-open-trade-at-a-time interleaved pass as v1 (exits evaluated FIRST, then, while flat,
        one arming check per event), but with a DIFFERENT entry rule: price enters a classified
        level's proximity band (rejection — fade) or moves beyond it (breakthrough — follow, the
        studies' level-cross technique), confirmed by the matching tape state.

        Levels are read from the row-39 canonical, lookahead-free ``research.levels.compute_levels``
        — NEVER a second S/R computation — AS OF EACH flat event's OWN absolute timestamp
        (``epoch_anchor + point.timestamp``; datasets carry only a LOGICAL clock, so this is the
        one conversion back to the real UTC instant ``compute_levels`` expects), exactly like
        ``GET /research/levels`` computes at any instant: a level used to arm at T never sees a
        bar recorded after T. Levels are needed only for ENTRY arming (never for exits, which reuse
        ``_exit_reason``/``_close_trade`` unchanged), so this is evaluated only while flat — the
        same shape v1's combo loop already checks every event.

        Honest emptiness, never a fabricated arm: a missing ``bar_store``/``symbol``/
        ``epoch_anchor`` (a defensive floor — the route always wires a real ``BarStore``), a
        symbol with no recorded bar series, and a corrupt SOLE bar series (``compute_levels``
        aliases that to ``no_bar_series_for_symbol`` — the iter-2 seam, unchanged here) each yield
        zero classified levels to test against, so ``structure_tape`` arms nothing rather than
        fabricating a partial computation.

        goal-fast_wall J-03: builds exactly ONE ``_StructureArmMemo`` here (per run, in-memory,
        never shared/persisted) and threads it into every ``_structure_tape_arm`` call below —
        collapsing the per-tick ``compute_levels`` calls this loop used to make into one per real
        level-change-point interval, byte-identically (see ``_StructureArmMemo``'s own docstring)."""
        if bar_store is None or not symbol or epoch_anchor is None:
            return []
        memo = _StructureArmMemo(bar_store, symbol, self._config)
        entries = strategy["entries"]
        horizon = strategy["exits"]["horizon_seconds"]
        cooldown = entries["arm_cooldown_seconds"]
        config = self._config
        position: dict | None = None
        cooldown_until = float("-inf")
        trades: list[dict] = []
        for i, point in enumerate(path):
            if position is not None and i > position["index"] and point.last is not None:
                reason = self._exit_reason(position, point, horizon)
                if reason is not None:
                    trades.append(self._close_trade(position, point, reason))
                    position = None
            if (
                position is None
                and point.last is not None
                and point.timestamp >= cooldown_until
            ):
                arm = self._structure_tape_arm(
                    point, bar_store, symbol, epoch_anchor + point.timestamp, entries, config,
                    memo=memo,
                )
                if arm is not None:
                    direction, setup_type, level, opposing_price = arm
                    position = self._arm_trade(
                        i, point, setup_type, direction, level=level, opposing_price=opposing_price
                    )
                    cooldown_until = point.timestamp + cooldown
        if position is not None:
            trades.append(self._close_trade(position, path[-1], EXIT_DATASET_END))
        return trades

    @staticmethod
    def _structure_tape_arm(
        point: _PathPoint,
        bar_store: BarStore,
        symbol: str,
        as_of_epoch: float,
        entries: dict,
        config: Config,
        *,
        memo: "_StructureArmMemo | None" = None,
    ) -> tuple[str, str, dict, float | None] | None:
        """One flat-event arming check: resolve which reading (if any) the CURRENT tape state
        confirms, and — only then — read the row-39 levels as of THIS event's own absolute
        timestamp and test every member level of every confluence zone (an unclassified lone
        level carries no class and never arms) in the module's own served, deterministic order.
        Returns ``(direction, setup_type, level_provenance, next_opposing_zone_price)`` for the
        FIRST qualifying level, or ``None``. The state check runs FIRST so a non-confirming tick
        (``unclear`` or a state this strategy does not read) never pays for a levels computation
        at all.

        ``next_opposing_zone_price`` (era-4 J-05) is resolved from this SAME ``compute_levels``
        result (never a second/future levels read — the no-lookahead discipline) via
        ``_next_opposing_zone_price``, feeding the class-scaled reward-target exit; ``None`` when
        no zone qualifies on the side ``direction`` implies.

        ``memo`` (goal-fast_wall J-03, keyword-only, defaulting to ``None``): when provided,
        levels are served through its ``levels_at`` (a memoized read, byte-identical to a fresh
        ``compute_levels`` call — see ``_StructureArmMemo``'s own docstring for the contract);
        ``None`` (every caller that does not opt in, e.g. a direct test call) preserves today's
        EXACT direct-call behaviour, unchanged."""
        reading = _structure_tape_reading(point.tape_state, entries)
        if reading is None:
            return None
        direction, setup_type = reading
        if memo is not None:
            result = memo.levels_at(as_of_epoch)
        else:
            result = compute_levels(bar_store, symbol, as_of_epoch, config)
        band_bps = entries["proximity_band_bps"]
        zones = result["confluence_zones"]
        for zone in zones:
            for level in zone["levels"]:
                price = level["price"]
                if setup_type == _STRUCTURE_TAPE_REJECTION:
                    tolerance = price * (band_bps / 10_000.0)
                    qualifies = abs(point.last - price) <= tolerance
                else:  # breakthrough — the studies' level-cross technique (price beyond the level)
                    qualifies = point.last > price if direction == "long" else point.last < price
                if qualifies:
                    opposing_price = _next_opposing_zone_price(zones, zone, point.last, direction)
                    return direction, setup_type, _level_provenance(level, zone), opposing_price
        return None

    # --- structure_tape_map simulation (era-5B J-04): the IDENTICAL one-open-trade-at-a-time
    # interleaved pass as structure_tape directly above (exits evaluated FIRST, then, while flat,
    # one arming check per event), a NEW arming source only -------------------------------------
    def _structure_tape_map_trades(
        self,
        path: list[_PathPoint],
        strategy: dict,
        bar_store: BarStore | None,
        symbol: str | None,
        epoch_anchor: float | None,
    ) -> list[dict]:
        """Arm and simulate ``structure_tape_map``'s trades over the recorded path — BYTE-IDENTICAL
        control flow to ``_structure_tape_trades`` above (same one-open-trade loop, same
        ``_exit_reason``/``_close_trade``/``_arm_trade`` calls — reused, never duplicated); the
        ONLY difference is the arming SOURCE: ``_structure_tape_map_arm`` (tradable-map bands)
        instead of ``_structure_tape_arm`` (raw classified levels/zones). See
        ``_structure_tape_map_arm``'s own docstring for the arming rule and its honest-emptiness
        floors (missing bar_store/symbol/epoch_anchor, no bar series, no classified band).

        goal-fast_wall J-03: builds exactly ONE ``_StructureArmMemo`` here (per run, in-memory,
        never shared/persisted — a SEPARATE instance from ``_structure_tape_trades``'s own, since
        each is scoped to its own run) and threads it into every ``_structure_tape_map_arm`` call
        below — collapsing the per-tick ``compute_tradability`` calls this loop used to make into
        one per real UTC session date, byte-identically (see ``_StructureArmMemo``'s docstring)."""
        if bar_store is None or not symbol or epoch_anchor is None:
            return []
        memo = _StructureArmMemo(bar_store, symbol, self._config)
        entries = strategy["entries"]
        horizon = strategy["exits"]["horizon_seconds"]
        cooldown = entries["arm_cooldown_seconds"]
        config = self._config
        position: dict | None = None
        cooldown_until = float("-inf")
        trades: list[dict] = []
        for i, point in enumerate(path):
            if position is not None and i > position["index"] and point.last is not None:
                reason = self._exit_reason(position, point, horizon)
                if reason is not None:
                    trades.append(self._close_trade(position, point, reason))
                    position = None
            if (
                position is None
                and point.last is not None
                and point.timestamp >= cooldown_until
            ):
                arm = self._structure_tape_map_arm(
                    point, bar_store, symbol, epoch_anchor + point.timestamp, entries, config,
                    memo=memo,
                )
                if arm is not None:
                    direction, setup_type, level, opposing_price = arm
                    position = self._arm_trade(
                        i, point, setup_type, direction, level=level, opposing_price=opposing_price
                    )
                    cooldown_until = point.timestamp + cooldown
        if position is not None:
            trades.append(self._close_trade(position, path[-1], EXIT_DATASET_END))
        return trades

    @staticmethod
    def _structure_tape_map_arm(
        point: _PathPoint,
        bar_store: BarStore,
        symbol: str,
        as_of_epoch: float,
        entries: dict,
        config: Config,
        *,
        memo: "_StructureArmMemo | None" = None,
    ) -> tuple[str, str, dict, float | None] | None:
        """One flat-event arming check — the IDENTICAL shape ``_structure_tape_arm`` performs
        (resolve which reading the CURRENT tape state confirms FIRST, so a non-confirming tick
        never pays for a map computation at all; then test candidates AS OF this event's own
        absolute timestamp; return the FIRST qualifying candidate's ``(direction, setup_type,
        level_provenance, next_opposing_price)``, or ``None``), sourcing candidates from the
        row-"Tradable level map" canonical ``compute_tradability`` BANDS (era-5B J-01) instead of
        ``compute_levels`` confluence-zone levels — never levels.py's raw output directly (the
        tradable map is the ONLY lens this strategy reads; never a second, independent levels
        computation).

        A band's ``members`` list is the SAME level-dict shape a zone's ``levels`` list carries, so
        the per-member proximity/breakthrough test below and the class-scaled exit math it feeds
        (via ``_level_provenance``, reused UNCHANGED) are IDENTICAL to ``_structure_tape_arm`` —
        only the outer container, and which side of that container is searched, differ:

          * An UNCLASSIFIED band (``class: null`` — no overlapping confluence zone, an honest
            absence ``tradability.py`` itself documents) is skipped BEFORE any member test: there
            is no A/B/C to scale a stop/reward/size against, so a band with no inherited class arms
            nothing (the identical "an unclassified lone level never joins a zone and never arms"
            discipline ``structure_tape`` already relies on — ``compute_tradability`` merely makes
            the null case reachable here, since EVERY level joins some band, unlike zone
            membership, which requires >= 2 members).
          * Only bands on the SIDE ``_structure_tape_map_side_for_reading`` names for this
            (direction, setup_type) reading are tested (a genuine, flagged judgment call — see that
            function's own docstring and the dev handoff): a band, unlike a raw zone, carries an
            explicit support/resistance side, so this arming can finally test the semantically
            correct side rather than every band regardless of position.

        ``next_opposing_price`` is resolved from this SAME ``compute_tradability`` result (never a
        second/future map read) via ``_next_opposing_band_price``, feeding the identical
        class-scaled reward-target exit ``structure_tape`` uses; ``None`` when no band qualifies on
        the side ``direction`` implies.

        ``memo`` (goal-fast_wall J-03, keyword-only, defaulting to ``None``): when provided,
        tradability is served through its ``tradability_at`` (a memoized read, byte-identical to a
        fresh ``compute_tradability`` call — see ``_StructureArmMemo``'s own docstring for the
        contract); ``None`` (every caller that does not opt in, e.g. a direct test call) preserves
        today's EXACT direct-call behaviour, unchanged."""
        reading = _structure_tape_reading(point.tape_state, entries)
        if reading is None:
            return None
        direction, setup_type = reading
        if memo is not None:
            result = memo.tradability_at(as_of_epoch)
        else:
            result = compute_tradability(bar_store, symbol, as_of_epoch, config)
        band_bps = entries["proximity_band_bps"]
        bands = result["bands"]
        wanted_side = _structure_tape_map_side_for_reading(direction, setup_type)
        for band in bands:
            if band["class"] is None or band["side"] != wanted_side:
                continue
            for level in band["members"]:
                price = level["price"]
                if setup_type == _STRUCTURE_TAPE_REJECTION:
                    tolerance = price * (band_bps / 10_000.0)
                    qualifies = abs(point.last - price) <= tolerance
                else:  # breakthrough — the studies' level-cross technique (price beyond the level)
                    qualifies = point.last > price if direction == "long" else point.last < price
                if qualifies:
                    opposing_price = _next_opposing_band_price(bands, band, point.last, direction)
                    return direction, setup_type, _level_provenance(level, band), opposing_price
        return None

    # --- the seeded random-entry null baseline (same exits, fees, slippage) --------------------
    def _null_trades(self, path: list[_PathPoint], seed: int) -> list[dict]:
        """The seeded random-entry null baseline over the SAME recorded path: entry instants
        (and per-entry directions) drawn from the recorded seed, each simulated INDEPENDENTLY
        through the SAME exit/fee/slippage code paths. Deterministic: the same seed reproduces
        identical entries; the drawn order is fixed (times then direction per draw, sorted by
        time) so the seed fully determines the baseline. A draw landing before any recorded
        price is skipped (no price, no honest fill)."""
        if not path:
            return []
        config = self._config
        horizon = config.strategy_exit_horizon_seconds
        rng = random.Random(seed)
        start_ts = path[0].timestamp
        span = path[-1].timestamp - start_ts
        draws: list[tuple[float, str]] = []
        for _ in range(config.backtest_null_entry_count):
            offset = rng.random() * span if span > 0 else 0.0
            draws.append((start_ts + offset, rng.choice(("long", "short"))))
        draws.sort(key=lambda d: d[0])
        trades: list[dict] = []
        for entry_ts, direction in draws:
            index = self._index_at(path, entry_ts)
            point = path[index]
            if point.last is None:
                continue
            entry = self._arm_trade(index, point, NULL_SETUP_TYPE, direction)
            trades.append(self._simulate_exit(entry, path, horizon))
        return trades

    @staticmethod
    def _index_at(path: list[_PathPoint], ts: float) -> int:
        """The index of the recorded point in effect at/just before ``ts`` (the studies'
        ``_point_at`` semantics; the first point when ``ts`` precedes the whole path)."""
        chosen: int | None = None
        for i, point in enumerate(path):
            if point.timestamp <= ts:
                chosen = i
            else:
                break
        return chosen if chosen is not None else 0

    # --- one trade: arm, exit decision, close (the SINGLE fill/fee/R/$ arithmetic) -------------
    def _arm_trade(
        self,
        index: int,
        point: _PathPoint,
        setup_type: str,
        direction: str,
        *,
        level: dict | None = None,
        opposing_price: float | None = None,
    ) -> dict:
        """Open one simulated trade at a recorded event. ``level`` (era-4 J-04) is the arming
        level's provenance for a ``structure_tape`` OR ``structure_tape_map`` trade (era-5B J-04
        reuses this same gate — the CALLER, never this method, decides which strategy passes
        ``level``); v1 and the null baseline never pass it, so their trade dicts carry no ``level``
        key at all (byte-identical to before).

        v1/null (``level is None``): the invalidation is the studies' REUSED, spread-based helper
        — UNCHANGED. structure_tape / structure_tape_map (``level is not None``, era-4 J-05): the
        invalidation is the NEW class-scaled, level-relative ``_class_scaled_invalidation``, and
        the position also
        carries a ``target_price`` (the class-scaled reward target, bounded by ``opposing_price`` —
        the next opposing level resolved at arm time, or ``None``). Either way R flows through the
        ONE shared ``marks.r_basis`` — never a second formula."""
        if level is not None:
            invalidation = _class_scaled_invalidation(
                point.last, level["price"], level["class"], direction, self._config
            )
        else:
            invalidation = _synthetic_invalidation(point.last, point.spread, direction, self._config)
        r = r_basis(point.last, invalidation)
        position = {
            "index": index,
            "entry_ts": point.timestamp,
            "entry_price": point.last,
            "entry_spread": point.spread,
            "invalidation_price": invalidation,
            "r_basis": r,
            "setup_type": setup_type,
            "direction": direction,
            "opposing_state": _opposing_control_state(direction),
        }
        if level is not None:
            position["level"] = level
            position["target_price"] = _class_scaled_target(
                point.last, direction, level["class"], r, opposing_price, self._config
            )
        return position

    def _exit_reason(self, trade: dict, point: _PathPoint, horizon: float) -> str | None:
        """The exit decision at ONE recorded event, in the documented fixed precedence:
        r_stop (a recorded print at/through the synthetic invalidation), then reward_target (era-4
        J-05: a recorded print at/through the class-scaled take-profit — ``structure_tape`` trades
        only, via their ``target_price`` key; v1/null trades carry no such key and can never reach
        this branch), then state_flip (the opposing control state reads), then horizon (logical
        time since entry at/past the configured horizon). ``None`` = still open."""
        if trade["direction"] == "long" and point.last <= trade["invalidation_price"]:
            return EXIT_R_STOP
        if trade["direction"] == "short" and point.last >= trade["invalidation_price"]:
            return EXIT_R_STOP
        target_price = trade.get("target_price")
        if target_price is not None:
            if trade["direction"] == "long" and point.last >= target_price:
                return EXIT_REWARD_TARGET
            if trade["direction"] == "short" and point.last <= target_price:
                return EXIT_REWARD_TARGET
        if point.tape_state == trade["opposing_state"]:
            return EXIT_STATE_FLIP
        if point.timestamp - trade["entry_ts"] >= horizon:
            return EXIT_HORIZON
        return None

    def _simulate_exit(self, trade: dict, path: list[_PathPoint], horizon: float) -> dict:
        """Walk the recorded path strictly after the entry event to the trade's exit (the null
        baseline's independent walk — the strategy pass interleaves the SAME ``_exit_reason``
        decision inside its one-position loop). Open at the end -> the explicit dataset_end."""
        for i in range(trade["index"] + 1, len(path)):
            point = path[i]
            if point.last is None:
                continue
            reason = self._exit_reason(trade, point, horizon)
            if reason is not None:
                return self._close_trade(trade, point, reason)
        return self._close_trade(trade, path[-1], EXIT_DATASET_END)

    def _close_trade(self, trade: dict, point: _PathPoint, reason: str) -> dict:
        """Close one simulated trade at a recorded event — the SINGLE fill/fee/R/$ arithmetic.

        Fills at the recorded prices adjusted ADVERSELY by the slippage model (a missing/zero
        recorded spread contributes zero slippage — honest absence). GROSS is measured from the
        recorded prices; NET from the adjusted fills minus both fills' fees. The fixed
        ``strategy_dollars_per_r`` notional makes R and $ two views of one measurement:
        ``shares = dollars_per_r / R basis`` — v1/null, UNCHANGED. structure_tape /
        structure_tape_map (era-4 J-05 / era-5B J-04, ``"level" in trade``): ``shares`` is scaled
        by the arming level's class size multiple (``structure_tape_size_multiple_by_class``) over
        the SAME fixed notional — still a PER-TRADE SIMULATED notional only, never a real order."""
        config = self._config
        direction = trade["direction"]
        sign = 1.0 if direction == "long" else -1.0
        entry_spread = trade["entry_spread"] if (trade["entry_spread"] or 0) > 0 else 0.0
        exit_spread = point.spread if (point.spread or 0) > 0 else 0.0
        entry_slip = entry_spread * config.strategy_slippage_spread_fraction
        exit_slip = exit_spread * config.strategy_slippage_spread_fraction
        entry_fill = trade["entry_price"] + sign * entry_slip
        exit_fill = point.last - sign * exit_slip
        if "level" in trade:
            size_multiple = config.structure_tape_size_multiple_by_class[trade["level"]["class"]]
            shares = size_multiple * config.strategy_dollars_per_r / trade["r_basis"]
        else:
            shares = config.strategy_dollars_per_r / trade["r_basis"]
        gross_move = sign * (point.last - trade["entry_price"])
        fill_move = sign * (exit_fill - entry_fill)
        fee = max(config.strategy_fee_per_share * shares, config.strategy_fee_min_per_trade)
        fees_usd = 2.0 * fee
        net_usd = fill_move * shares - fees_usd
        closed = {
            "setup_type": trade["setup_type"],
            "direction": direction,
            "entry": {
                "logical_ts": trade["entry_ts"],
                "price": trade["entry_price"],
                "fill_price": entry_fill,
                "spread": trade["entry_spread"],
            },
            "exit": {
                "logical_ts": point.timestamp,
                "price": point.last,
                "fill_price": exit_fill,
                "spread": point.spread,
                "reason": reason,
            },
            "invalidation_price": trade["invalidation_price"],
            "r_basis": trade["r_basis"],
            "shares": shares,
            "gross_r": gross_move / trade["r_basis"],
            "net_r": net_usd / config.strategy_dollars_per_r,
            "gross_usd": gross_move * shares,
            "net_usd": net_usd,
            "fees_usd": fees_usd,
            "slippage_usd": (gross_move - fill_move) * shares,
        }
        if "level" in trade:  # era-4 J-04: the arming level's provenance (structure_tape only)
            closed["level"] = trade["level"]
            closed["target_price"] = trade["target_price"]  # era-4 J-05: the reward-target price
        return closed

    # --- persistence (single writer queue; result computed once, served verbatim) --------------
    def _persist_terminal(
        self,
        backtest_id: str,
        payload: dict,
        status: str,
        *,
        result: dict | None = None,
        error: str | None = None,
    ) -> None:
        final = {**payload, "status": status}
        final.pop("events_processed", None)
        final.pop("progress", None)
        if result is not None:
            final["result"] = result
        if error is not None:
            final["error"] = error
        self._store.set_backtest_result(backtest_id, final)


class BacktestJobManager:
    """Owns the cancellable backtest job lifecycle — the ``StudyJobManager`` pattern verbatim.

    A backtest is CREATED (persisted ``queued`` with its identity stamps) and then STARTED on a
    dedicated worker thread — OFF the event loop, never blocking the live cockpit. Each running
    job has a cancellation ``threading.Event``; ``cancel`` sets it (observed cooperatively
    between events). ``run_sync`` is the CI/unit path (in-process, no thread race). The manager
    is process-scoped (one per ``ResearchRegistry``); a backend restart loses in-flight jobs — a
    record left ``running`` from a prior process is surfaced honestly, never silently completed.
    The dataset store is injected per start (the route's dependency-resolved store), so tests
    point it anywhere via the existing env/override seams."""

    def __init__(self, store: JournalStore, config: Config) -> None:
        self._store = store
        self._config = config
        self._runner = BacktestRunner(store, config)
        self._cancels: dict[str, threading.Event] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    def create(self, params: dict) -> dict:
        """Persist a NEW backtest ``queued`` with its identity stamps — the request echo
        (dataset/strategy/profile), the recorded null-baseline seed (the config default unless
        the params carry one), and the config fingerprint of the RESOLVED per-run profile config
        (J-06 — ``default`` unchanged; a registered candidate distinct, matching the fingerprint
        the terminal report stamps) — and return the served payload. The caller (route) then
        STARTS it. ``params["profile"]`` is route-validated already; an unresolvable value
        defensively falls back to the base config rather than raising here (``run`` raises its
        own explicit error at execution time — this stamp is best-effort identity metadata only)."""
        backtest_id = uuid.uuid4().hex
        seed = params.get("null_baseline_seed", self._config.backtest_null_baseline_seed)
        run_config = self._config.resolved_for_profile(params["profile"]) or self._config
        payload = {
            "id": backtest_id,
            "status": STATUS_QUEUED,
            "dataset_id": params["dataset_id"],
            "strategy_id": params["strategy_id"],
            "profile": params["profile"],
            "null_baseline_seed": seed,
            "config_fingerprint": run_config.config_fingerprint(),
            "created_wall_ts": time.time(),
        }
        self._store.insert_backtest(
            BacktestRecord(
                id=backtest_id, payload=payload, created_wall_ts=payload["created_wall_ts"]
            )
        )
        return payload

    @staticmethod
    def _run_params(payload: dict) -> dict:
        return {
            "dataset_id": payload["dataset_id"],
            "strategy_id": payload["strategy_id"],
            "profile": payload["profile"],
            "null_baseline_seed": payload["null_baseline_seed"],
        }

    def start(
        self,
        backtest_id: str,
        *,
        dataset_store: DatasetStore,
        bar_store: BarStore | None = None,
    ) -> None:
        """Start a queued backtest on a worker thread (background). Idempotent — a second start
        for the same id is ignored (the job is already running/terminal). ``bar_store`` (era-4
        J-04) is threaded through at call time exactly like ``dataset_store`` — never baked into
        the constructor — so ``structure_tape`` can read the row-39 levels; v1 ignores it."""
        with self._lock:
            if backtest_id in self._threads:
                return
            cancel = threading.Event()
            self._cancels[backtest_id] = cancel
        record = self._store.get_backtest(backtest_id)
        if record is None:
            return
        params = self._run_params(record.payload)

        def _work() -> None:
            try:
                self._runner.run(
                    backtest_id=backtest_id,
                    params=params,
                    dataset_store=dataset_store,
                    is_cancelled=cancel.is_set,
                    bar_store=bar_store,
                )
            finally:
                with self._lock:
                    self._threads.pop(backtest_id, None)
                    self._cancels.pop(backtest_id, None)

        thread = threading.Thread(target=_work, name=f"backtest:{backtest_id}", daemon=True)
        with self._lock:
            self._threads[backtest_id] = thread
        thread.start()

    def run_sync(
        self,
        backtest_id: str,
        *,
        dataset_store: DatasetStore,
        bar_store: BarStore | None = None,
    ) -> None:
        """Run a queued backtest SYNCHRONOUSLY (the CI/unit path). Completes in-process; honors
        a pre-set cancellation flag so cancel-before-run is testable deterministically."""
        cancel = self._cancels.get(backtest_id, threading.Event())
        record = self._store.get_backtest(backtest_id)
        if record is None:
            return
        self._runner.run(
            backtest_id=backtest_id,
            params=self._run_params(record.payload),
            dataset_store=dataset_store,
            is_cancelled=cancel.is_set,
            bar_store=bar_store,
        )

    def cancel(self, backtest_id: str) -> None:
        """Signal cancellation for a running/queued backtest (cooperative — observed between
        events)."""
        with self._lock:
            cancel = self._cancels.get(backtest_id)
            if cancel is None:
                cancel = threading.Event()
                self._cancels[backtest_id] = cancel
            cancel.set()

    def join_all(self, timeout: float = 30.0) -> None:
        """Wait for all in-flight job threads (used on shutdown so daemons drain cleanly)."""
        with self._lock:
            threads = list(self._threads.values())
        for t in threads:
            t.join(timeout=timeout)
