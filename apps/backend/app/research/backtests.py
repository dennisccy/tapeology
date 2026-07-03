"""Deterministic backtest runner + cancellable job manager (era-3 capability 4, J-03).

THE single computing owner of Data Contract row 31 (backtest reports): a backtest replays ONE
registered dataset UNPACED through a fresh engine — consumed EXCLUSIVELY via
``DatasetStore.replay`` (row 30's public API; this module never opens or parses a dataset file
itself) — arms simulated entries per the config-owned strategy grammar v1 (row 34,
``Config.strategy_definition``), simulates fills at recorded prices adjusted by the configured
slippage model, applies the configured fee model, and persists the report ONCE. The routes and
the MCP ``backtests`` proxy serve the stored rows VERBATIM ever after — no recomputation on read.

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

  * **Exits: R-stop / horizon / state-flip / dataset_end.** The R-stop is the studies'
    arm-instant synthetic invalidation (the REUSED ``_synthetic_invalidation`` helper —
    ``study_occurrence_r_spread_multiple`` x arm spread, floored at ``study_occurrence_r_floor``,
    adverse side), with R via the shared ``marks.r_basis`` (row 27 — never a second formula); it
    triggers on a recorded print at/through the invalidation. The state-flip exit fires when the
    tape reads the OPPOSING control state (the studies' ``_control_state`` vocabulary). The time
    horizon exits at the first recorded event at/after ``strategy_exit_horizon_seconds`` past
    entry. A trade still open when the stream ends is handled EXPLICITLY and deterministically:
    forced exit at the LAST recorded price, labeled ``dataset_end`` — documented, never silent.
    Exit precedence within one event is fixed and documented: r_stop, then state_flip, then
    horizon. Exit evaluation begins strictly AFTER the entry event.

  * **Fills, fees, and the two unit systems.** Entry fills at the recorded arm price adjusted
    ADVERSELY by ``strategy_slippage_spread_fraction`` x the recorded at-that-event spread; exit
    fills adversely likewise at the recorded exit price (a moment with no usable quote
    contributes zero slippage — honest absence, never a fabricated cost). Each fill pays
    ``max(strategy_fee_per_share x shares, strategy_fee_min_per_trade)``. Position size is the
    fixed notional: ``shares = strategy_dollars_per_r / R basis``, so R and $ are two disclosed
    unit systems over the SAME measurement — GROSS from recorded prices, NET from fills minus
    fees, and a dollar figure never exists without its R counterpart.

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

import random
import threading
import time
import uuid

from ..config import Config
from .datasets import DatasetIntegrityError, DatasetNotFound, DatasetStore
from .marks import r_basis
from .store import BacktestRecord, JournalStore

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

# The only registrable profile until J-06 ships the profile registry — the route refuses any
# other value honestly (422), and every report stamps it.
PROFILE_DEFAULT = "default"

# The null-baseline population label — an explicit non-setup so a random entry can never be
# mistaken for (or pooled into) a real strategy setup.
NULL_SETUP_TYPE = "random_null"

# Exit reasons (one explicit copy each — the iter-15 own-copy lesson).
EXIT_R_STOP = "r_stop"
EXIT_HORIZON = "horizon"
EXIT_STATE_FLIP = "state_flip"
EXIT_DATASET_END = "dataset_end"


def _opposing_control_state(direction: str) -> str:
    """The OPPOSING control state whose read is the state-flip exit (existing vocabulary only):
    a long is broken by ``seller_control``, a short by ``buyer_control`` — via the studies' one
    ``_control_state`` mapping, never a second copy of the state names."""
    return _control_state("short" if direction == "long" else "long")


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
    ) -> None:
        """Execute the backtest, persisting status transitions through the store. Honors
        cancellation cooperatively (between events and before persist). Never raises out —
        every failure is captured as an explicit ``failed`` record (never an empty success)."""
        record = self._store.get_backtest(backtest_id)
        payload = dict(record.payload) if record is not None else dict(params)
        try:
            if is_cancelled():
                self._persist_terminal(backtest_id, payload, STATUS_CANCELLED)
                return
            self._store.update_backtest_payload(
                backtest_id, {**payload, "status": STATUS_RUNNING}
            )
            # The verified metadata load (id -> 404-style DatasetNotFound; corrupt/tampered ->
            # DatasetIntegrityError) — embedded VERBATIM in the report's provenance.
            dataset_meta = dataset_store.get(params["dataset_id"])
            path, cancelled = self._replay(
                dataset_store, params["dataset_id"], backtest_id, payload, is_cancelled
            )
            if cancelled or is_cancelled():
                self._persist_terminal(backtest_id, payload, STATUS_CANCELLED)
                return
            strategy = self._config.strategy_definition(params["strategy_id"])
            if strategy is None:  # route-guarded (422); defensive honesty here
                raise ValueError(f"unknown strategy '{params['strategy_id']}'")
            trades = self._strategy_trades(path, strategy)
            null_trades = self._null_trades(path, params["null_baseline_seed"])
            result = {
                "register": REGISTER,
                # Provenance: the dataset's stored metadata VERBATIM (id + checksum + window +
                # feed + counts), the resolved strategy config echoed verbatim, the profile id,
                # and the config fingerprint (the existing hasher — never a second computation).
                "dataset": dataset_meta,
                "strategy_id": params["strategy_id"],
                "strategy": strategy,
                "profile": params["profile"],
                "config_fingerprint": self._config.config_fingerprint(),
                "trades": trades,
                "aggregates": _aggregate(trades),
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
    ) -> tuple[list[_PathPoint], bool]:
        """Replay the stored dataset unpaced through ``DatasetStore.replay`` (a FRESH engine,
        verified load) recording the snapshot path in memory ONCE. Cancellation is checked
        between events; progress is persisted every ``_PROGRESS_EVERY`` events (throttled —
        never a hot path). Tape data lives ONLY in this in-job memory — never persisted."""
        path: list[_PathPoint] = []
        total = 0
        cancelled = False
        for snapshot in dataset_store.replay(dataset_id, self._config):
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
    def _strategy_trades(self, path: list[_PathPoint], strategy: dict) -> list[dict]:
        """Arm and simulate the strategy's trades over the recorded path — ONE deterministic
        interleaved pass: at each recorded event the open trade's exit is evaluated FIRST, then
        (if flat) each declared setup x direction combo may arm per the sustained-premise rule.
        Premise runs are tracked continuously (a run does not reset because a position was
        open); a combo blocked by an open position arms at the first eligible later event of
        the SAME sustained run. A trade still open at the last event exits ``dataset_end``."""
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
    def _arm_trade(self, index: int, point: _PathPoint, setup_type: str, direction: str) -> dict:
        """Open one simulated trade at a recorded event. The synthetic invalidation is the
        studies' REUSED helper (adverse side, spread multiple with floor) and R flows through
        the ONE shared ``marks.r_basis`` — never a second formula."""
        invalidation = _synthetic_invalidation(point.last, point.spread, direction, self._config)
        return {
            "index": index,
            "entry_ts": point.timestamp,
            "entry_price": point.last,
            "entry_spread": point.spread,
            "invalidation_price": invalidation,
            "r_basis": r_basis(point.last, invalidation),
            "setup_type": setup_type,
            "direction": direction,
            "opposing_state": _opposing_control_state(direction),
        }

    def _exit_reason(self, trade: dict, point: _PathPoint, horizon: float) -> str | None:
        """The exit decision at ONE recorded event, in the documented fixed precedence:
        r_stop (a recorded print at/through the synthetic invalidation), then state_flip (the
        opposing control state reads), then horizon (logical time since entry at/past the
        configured horizon). ``None`` = still open."""
        if trade["direction"] == "long" and point.last <= trade["invalidation_price"]:
            return EXIT_R_STOP
        if trade["direction"] == "short" and point.last >= trade["invalidation_price"]:
            return EXIT_R_STOP
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
        ``shares = dollars_per_r / R basis``."""
        config = self._config
        direction = trade["direction"]
        sign = 1.0 if direction == "long" else -1.0
        entry_spread = trade["entry_spread"] if (trade["entry_spread"] or 0) > 0 else 0.0
        exit_spread = point.spread if (point.spread or 0) > 0 else 0.0
        entry_slip = entry_spread * config.strategy_slippage_spread_fraction
        exit_slip = exit_spread * config.strategy_slippage_spread_fraction
        entry_fill = trade["entry_price"] + sign * entry_slip
        exit_fill = point.last - sign * exit_slip
        shares = config.strategy_dollars_per_r / trade["r_basis"]
        gross_move = sign * (point.last - trade["entry_price"])
        fill_move = sign * (exit_fill - entry_fill)
        fee = max(config.strategy_fee_per_share * shares, config.strategy_fee_min_per_trade)
        fees_usd = 2.0 * fee
        net_usd = fill_move * shares - fees_usd
        return {
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
        the params carry one), and the config fingerprint — and return the served payload. The
        caller (route) then STARTS it."""
        backtest_id = uuid.uuid4().hex
        seed = params.get("null_baseline_seed", self._config.backtest_null_baseline_seed)
        payload = {
            "id": backtest_id,
            "status": STATUS_QUEUED,
            "dataset_id": params["dataset_id"],
            "strategy_id": params["strategy_id"],
            "profile": params["profile"],
            "null_baseline_seed": seed,
            "config_fingerprint": self._config.config_fingerprint(),
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

    def start(self, backtest_id: str, *, dataset_store: DatasetStore) -> None:
        """Start a queued backtest on a worker thread (background). Idempotent — a second start
        for the same id is ignored (the job is already running/terminal)."""
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
                )
            finally:
                with self._lock:
                    self._threads.pop(backtest_id, None)
                    self._cancels.pop(backtest_id, None)

        thread = threading.Thread(target=_work, name=f"backtest:{backtest_id}", daemon=True)
        with self._lock:
            self._threads[backtest_id] = thread
        thread.start()

    def run_sync(self, backtest_id: str, *, dataset_store: DatasetStore) -> None:
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
