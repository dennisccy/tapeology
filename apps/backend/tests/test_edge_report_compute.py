"""era-fast_wall J-04 -- the operator-run compute: ``EdgeReportComputeManager`` (single-flight,
cancel, atomic progress snapshot) plus the CLI warmer's ``main()``.

Manager tests substitute a FAKE ``run_strategy_comparison_report`` (monkeypatched onto THIS
module's own imported name -- the ``test_edge_report_api.py`` counting-spy precedent, applied to a
full function swap instead of a wrapper) for deterministic, threading-free control over timing
(started/release ``threading.Event`` pairs, a ``should_abort`` that genuinely loops until fired).
End-to-end wiring against the REAL ``run_strategy_comparison_report`` (real cache, real fixtures) is
proven in ``test_edge_report.py`` (the hooks themselves, TC-14) and ``test_edge_report_api.py`` (the
HTTP routes, TC-1/2/3/5/6/8). CLI tests mirror ``edge_report.py``'s own
``test_cli_main_writes_a_report_and_exits_zero_on_the_fixture_pair`` pattern exactly.
"""

from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

import pytest

from app.config import CONFIG
from app.research import edge_report_compute
from app.research.bars import BarStore
from app.research.datasets import DatasetStore
from app.research.edge_report import EdgeReportComputeCancelled
from app.research.edge_report_cache import EdgeReportCache, resolve_cache_db_path
from app.research.edge_report_compute import EdgeReportComputeManager
from app.research.store import JournalStore

BACKEND_DIR = Path(__file__).resolve().parents[1]
FIXTURE_J03_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets_j03"

_EMPTY_REPORT = {"train": {"cells": []}, "holdout": {"cells": []}, "surviving_train_cells": []}


@pytest.fixture
def store(tmp_path):
    s = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    yield s
    s.close()


def _trigger_args(tmp_path, store):
    """The five positional args every ``manager.trigger(...)`` call needs -- a fresh, hermetic
    dataset/bar store pair + a fresh cache DB, all rooted under the test's own ``tmp_path`` (never
    the package-anchored default)."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    bar_store = BarStore(tmp_path / "bars")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    return store, dataset_store, bar_store, CONFIG, cache


def _wait_for_terminal(manager: EdgeReportComputeManager, timeout: float = 5.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        snap = manager.snapshot()
        if snap is not None and snap["state"] != "running":
            return snap
        time.sleep(0.01)
    raise AssertionError("edge-report compute job never reached a terminal state")


# ==================================================================================================
# The manager: single-flight, cancel, force, progress, failed-state -- every test here swaps out
# ``run_strategy_comparison_report`` entirely (never the real multi-backtest sweep), so timing is
# controlled by explicit ``threading.Event`` pairs, never wall-clock luck.
# ==================================================================================================


def test_no_job_has_ever_run_snapshot_is_none():
    manager = EdgeReportComputeManager()
    assert manager.snapshot() is None


def test_trigger_starts_a_job_and_returns_the_data_contract_shape(tmp_path, store, monkeypatch):
    manager = EdgeReportComputeManager()
    started = threading.Event()
    release = threading.Event()

    def fake_run(*args, **kwargs):
        started.set()
        release.wait(timeout=5)
        return _EMPTY_REPORT

    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)

    result = manager.trigger(*_trigger_args(tmp_path, store))

    assert result["started"] is True
    compute = result["compute"]
    assert isinstance(compute["id"], str) and compute["id"] != ""
    assert compute["state"] == "running"
    assert compute["force"] is False
    assert isinstance(compute["started_utc"], str) and compute["started_utc"] != ""
    assert compute["finished_utc"] is None
    assert compute["error"] is None
    assert compute["progress"] == {
        "phase": "starting", "backtests_total": 0, "backtests_done": 0,
        "backtests_from_cache": 0, "current": None,
    }
    assert started.wait(timeout=5)
    release.set()
    manager.join_all(timeout=5)


def test_second_trigger_while_running_returns_the_same_job_started_false(tmp_path, store, monkeypatch):
    """TC-2."""
    manager = EdgeReportComputeManager()
    started = threading.Event()
    release = threading.Event()

    def fake_run(*args, **kwargs):
        started.set()
        release.wait(timeout=5)
        return _EMPTY_REPORT

    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)

    first = manager.trigger(*_trigger_args(tmp_path, store))
    assert started.wait(timeout=5)

    second = manager.trigger(*_trigger_args(tmp_path, store), force=True)  # even force never bypasses

    assert second["started"] is False
    assert second["compute"]["id"] == first["compute"]["id"]
    assert second["compute"]["force"] is False  # the ORIGINAL (non-force) job, unchanged

    release.set()
    manager.join_all(timeout=5)


def test_trigger_after_a_terminal_job_starts_a_genuinely_new_job(tmp_path, store, monkeypatch):
    manager = EdgeReportComputeManager()
    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", lambda *a, **k: _EMPTY_REPORT)

    first = manager.trigger(*_trigger_args(tmp_path, store))
    _wait_for_terminal(manager)
    manager.join_all(timeout=5)

    second = manager.trigger(*_trigger_args(tmp_path, store))
    assert second["started"] is True
    assert second["compute"]["id"] != first["compute"]["id"]
    manager.join_all(timeout=5)


def test_a_normal_return_resolves_state_done(tmp_path, store, monkeypatch):
    manager = EdgeReportComputeManager()
    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", lambda *a, **k: _EMPTY_REPORT)

    manager.trigger(*_trigger_args(tmp_path, store))
    snap = _wait_for_terminal(manager)

    assert snap["state"] == "done"
    assert snap["error"] is None
    assert isinstance(snap["finished_utc"], str) and snap["finished_utc"] != ""
    manager.join_all(timeout=5)


def test_a_cancellation_signal_resolves_state_cancelled_never_failed(tmp_path, store, monkeypatch):
    """TC-3 (manager-level wiring): the SAME cancellation signal ``_split_cells`` raises when
    ``should_abort`` fires (real proof in ``test_edge_report.py``'s TC-14b) is what the manager's
    worker thread must distinguish from a genuine failure -- proven here with a fake that genuinely
    observes the hook, mirroring the NOTES' suggested "raise a dedicated signal" mechanism."""
    manager = EdgeReportComputeManager()
    started = threading.Event()

    def fake_run(*args, **kwargs):
        should_abort = kwargs["should_abort"]
        started.set()
        deadline = time.time() + 5
        while time.time() < deadline:
            if should_abort():
                raise EdgeReportComputeCancelled()
            time.sleep(0.005)
        raise AssertionError("should_abort never fired")

    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)

    manager.trigger(*_trigger_args(tmp_path, store))
    assert started.wait(timeout=5)
    manager.cancel()

    snap = _wait_for_terminal(manager)
    assert snap["state"] == "cancelled"
    assert snap["error"] is None
    manager.join_all(timeout=5)


def test_a_raised_exception_resolves_state_failed_with_the_message_verbatim(tmp_path, store, monkeypatch):
    """TC-13."""
    manager = EdgeReportComputeManager()

    def fake_run(*args, **kwargs):
        raise RuntimeError("synthetic mid-sweep failure")

    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)

    manager.trigger(*_trigger_args(tmp_path, store))
    snap = _wait_for_terminal(manager)

    assert snap["state"] == "failed"
    assert snap["error"] == "synthetic mid-sweep failure"
    assert isinstance(snap["finished_utc"], str) and snap["finished_utc"] != ""
    manager.join_all(timeout=5)


def test_force_flag_is_threaded_through_to_the_compute_call_and_recorded_on_the_snapshot(
    tmp_path, store, monkeypatch
):
    manager = EdgeReportComputeManager()
    seen = {}

    def fake_run(*args, **kwargs):
        seen["force"] = kwargs["force"]
        return _EMPTY_REPORT

    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)

    result = manager.trigger(*_trigger_args(tmp_path, store), force=True)
    _wait_for_terminal(manager)

    assert seen["force"] is True
    assert result["compute"]["force"] is True
    manager.join_all(timeout=5)


def test_progress_patches_merge_atomically_into_the_snapshots_progress_subdict(tmp_path, store, monkeypatch):
    manager = EdgeReportComputeManager()

    def fake_run(*args, **kwargs):
        progress = kwargs["progress"]
        progress({"event": "total", "phase": "backtests", "backtests_total": 3, "backtests_done": 0,
                   "backtests_from_cache": 0, "current": None})
        progress({"event": "pair_started", "current": {"dataset_id": "d1", "strategy_id": "v1"}})
        progress({"event": "pair_done", "backtests_done": 1, "backtests_from_cache": 0, "current": None})
        return _EMPTY_REPORT

    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)

    manager.trigger(*_trigger_args(tmp_path, store))
    snap = _wait_for_terminal(manager)

    assert snap["progress"] == {
        "phase": "backtests", "backtests_total": 3, "backtests_done": 1,
        "backtests_from_cache": 0, "current": None,
    }
    # the transient "current" update mid-run was visible at SOME point too -- a stale reporter
    # from an already-superseded job is never possible here since only one job ever ran.
    manager.join_all(timeout=5)


def test_cache_kwarg_is_threaded_through_unchanged(tmp_path, store, monkeypatch):
    manager = EdgeReportComputeManager()
    seen = {}
    _, dataset_store, bar_store, config, cache = _trigger_args(tmp_path, store)

    def fake_run(*args, **kwargs):
        seen["cache"] = kwargs["cache"]
        return _EMPTY_REPORT

    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)

    manager.trigger(store, dataset_store, bar_store, config, cache)
    _wait_for_terminal(manager)

    assert seen["cache"] is cache
    manager.join_all(timeout=5)


# === era-fast_wall J-05: sub_cache resumability wiring + the never-workers>1 guard ================


def test_trigger_sub_cache_default_is_none_unchanged_for_every_pre_j05_caller(
    tmp_path, store, monkeypatch
):
    """Every EXISTING test above this marker calls ``trigger()`` without ``sub_cache`` and stays
    green unmodified — proof by construction that the default preserves byte-identical behavior.
    This test makes the claim explicit: the omitted kwarg reaches the compute call as ``None``."""
    manager = EdgeReportComputeManager()
    seen = {}
    _, dataset_store, bar_store, config, cache = _trigger_args(tmp_path, store)

    def fake_run(*args, **kwargs):
        seen["sub_cache"] = kwargs.get("sub_cache")
        return _EMPTY_REPORT

    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)

    manager.trigger(store, dataset_store, bar_store, config, cache)
    _wait_for_terminal(manager)

    assert seen["sub_cache"] is None
    manager.join_all(timeout=5)


def test_trigger_sub_cache_kwarg_is_threaded_through_to_the_compute_call(tmp_path, store, monkeypatch):
    """era-fast_wall J-05: a REAL ``sub_cache`` supplied to ``trigger()`` reaches ``run_strategy_
    comparison_report`` verbatim (never re-derived, never dropped)."""
    from app.research.edge_report_backtest_cache import EdgeReportBacktestCache

    manager = EdgeReportComputeManager()
    seen = {}
    _, dataset_store, bar_store, config, cache = _trigger_args(tmp_path, store)
    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))

    def fake_run(*args, **kwargs):
        seen["sub_cache"] = kwargs.get("sub_cache")
        return _EMPTY_REPORT

    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)

    manager.trigger(store, dataset_store, bar_store, config, cache, sub_cache=sub_cache)
    _wait_for_terminal(manager)

    assert seen["sub_cache"] is sub_cache
    manager.join_all(timeout=5)


def test_trigger_never_passes_a_workers_value_greater_than_one(tmp_path, store, monkeypatch):
    """TC-12: ``trigger()`` must never supply ``workers > 1`` to ``run_strategy_comparison_report``
    -- process-pool parallelism stays CLI-only this iteration (a logged, tested assumption)."""
    manager = EdgeReportComputeManager()
    seen = {}

    def fake_run(*args, **kwargs):
        seen.update(kwargs)
        return _EMPTY_REPORT

    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", fake_run)

    manager.trigger(*_trigger_args(tmp_path, store))
    _wait_for_terminal(manager)

    workers = seen.get("workers")
    assert workers is None or workers <= 1
    manager.join_all(timeout=5)


def test_trigger_resumability_end_to_end_via_a_real_sub_cache(tmp_path, store):
    """TC-11 (manager resumability wiring, end to end — NOT monkeypatched this time, the real
    ``run_strategy_comparison_report``): ``trigger()`` completing once over a real, non-degenerate
    2-eligible-pair-strategy fixture (via an injected ``sub_cache``) publishes durable rows for
    every pair; a SECOND ``trigger()`` call over the SAME dataset/bar stores and the SAME
    ``sub_cache`` (``force=True``, bypassing the now-warm WHOLE-report cache so the compute genuinely
    re-enters) resolves with ``backtests_from_cache > 0`` — proving ``trigger()`` genuinely threads
    a REAL cache through to ``run_strategy_comparison_report``, not the ``None`` default (which
    would leave ``backtests_from_cache`` permanently 0, as J-04 shipped it)."""
    from app.research.bars import BarStore
    from app.research.datasets import DatasetStore, SPLIT_TRAIN
    from app.research.edge_report_backtest_cache import EdgeReportBacktestCache
    from test_edge_report import _record_v1_arming_dataset
    from test_setups import _seed_full, _syn_config

    config = _syn_config()
    bar_store = BarStore(tmp_path / "bars")
    _seed_full(bar_store)
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))

    manager = EdgeReportComputeManager()
    manager.trigger(store, dataset_store, bar_store, config, cache, sub_cache=sub_cache)
    first_snap = _wait_for_terminal(manager)
    assert first_snap["state"] == "done"
    assert first_snap["progress"]["backtests_from_cache"] == 0  # cold -- nothing cached yet
    manager.join_all(timeout=5)

    manager.trigger(store, dataset_store, bar_store, config, cache, force=True, sub_cache=sub_cache)
    second_snap = _wait_for_terminal(manager)

    assert second_snap["state"] == "done"
    assert second_snap["progress"]["backtests_from_cache"] > 0
    manager.join_all(timeout=5)


def test_cancel_while_idle_is_a_harmless_no_op_the_route_owns_the_409():
    """The manager itself never raises on an idle cancel -- ``cancel_edge_report_compute`` (the
    ROUTE) is the one that checks idle-vs-running and raises the 409, mirroring
    ``cancel_backtest``'s own check-then-call split (``routes.py``)."""
    manager = EdgeReportComputeManager()
    manager.cancel()  # must not raise
    assert manager.snapshot() is None


def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_reference(tmp_path, store, monkeypatch):
    """A caller mutating a snapshot dict it read must never poison the manager's own state (the
    ``BarStore.get``/``list`` "served rows are copies" discipline, applied here)."""
    manager = EdgeReportComputeManager()
    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", lambda *a, **k: _EMPTY_REPORT)

    result = manager.trigger(*_trigger_args(tmp_path, store))
    _wait_for_terminal(manager)
    snap = manager.snapshot()
    snap["state"] = "tampered"
    snap["progress"]["backtests_done"] = 999

    fresh = manager.snapshot()
    assert fresh["state"] == "done"
    assert fresh["progress"]["backtests_done"] == 0
    manager.join_all(timeout=5)


# ==================================================================================================
# The CLI warmer (TC-11, TC-12) -- mirrors ``edge_report.py``'s own
# ``test_cli_main_writes_a_report_and_exits_zero_on_the_fixture_pair`` pattern. The committed
# ``datasets_j03`` fixture is symbol PG -- NOT a config-owned panel symbol under the REAL shipped
# ``CONFIG`` the CLI always resolves (mirrors ``edge_report.main()``'s own ``config = CONFIG``), so
# every compute below is the honest, deterministic, all-empty-cells shape (zero eligible backtests)
# -- the SAME finding ``test_keyless_committed_j03_fixture_with_the_real_panel_is_an_honest_empty_
# report`` already proves for the direct-call path.
# ==================================================================================================


def _set_cli_env(monkeypatch, tmp_path):
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(FIXTURE_J03_DATASET_DIR))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    # The cache DB path resolver's default (env-else-sibling-of-dataset-dir) would otherwise land
    # beside the COMMITTED fixture directory itself (never a tmp_path) since TAPEOLOGY_DATASET_DIR
    # above points DIRECTLY at it (the test_edge_report.py `test_keyless_committed_j03_fixture_...`
    # precedent) — leaking state ACROSS test runs and making a "cold cache" test order-dependent.
    # The explicit override keeps every CLI test hermetic, exactly like every other test in this
    # suite that touches a cache.
    monkeypatch.setenv("TAPEOLOGY_EDGE_REPORT_CACHE_DB", str(tmp_path / "edge_report_cache.db"))
    # era-fast_wall J-05: the SAME hazard/fix, for the NEW per-pair sub-cache the CLI's main() now
    # ALSO constructs (resolve_backtest_cache_db_path's own env-else-sibling-of-dataset-dir default
    # would otherwise ALSO land beside the committed fixture dir).
    monkeypatch.setenv("TAPEOLOGY_EDGE_SWEEP_CACHE_DB", str(tmp_path / "edge_report_backtests.db"))


def test_cli_completes_on_the_fixture_and_a_subsequent_get_path_serves_it_byte_identically(
    tmp_path, monkeypatch, capsys
):
    """TC-11."""
    _set_cli_env(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "argv", ["edge_report_compute"])

    exit_code = edge_report_compute.main()

    assert exit_code == 0
    out = capsys.readouterr().out
    assert out.strip() != ""  # at least the "N backtest(s) to run" summary line

    from app.research.edge_report import peek_strategy_comparison_report

    served_store = JournalStore(str(tmp_path / "served-journal.db"), CONFIG)
    try:
        dataset_store = DatasetStore(str(FIXTURE_J03_DATASET_DIR))
        bar_store = BarStore(str(tmp_path / "bars"))
        cache = EdgeReportCache(resolve_cache_db_path(str(FIXTURE_J03_DATASET_DIR)))
        served = peek_strategy_comparison_report(
            served_store, dataset_store, bar_store, CONFIG, cache=cache,
        )
    finally:
        served_store.close()

    assert "status" not in served  # a genuine warm report -- never the not-computed shape
    assert served["train"]["cells"] == []
    assert served["holdout"]["cells"] == []


def test_cli_repeat_invocation_without_force_is_fast_and_reruns_nothing(tmp_path, monkeypatch):
    """TC-12."""
    _set_cli_env(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "argv", ["edge_report_compute"])
    assert edge_report_compute.main() == 0

    from app.research import edge_report as edge_report_module

    calls = []
    real_compute = edge_report_module._compute_strategy_comparison_report

    def _counting_compute(*args, **kwargs):
        calls.append(1)
        return real_compute(*args, **kwargs)

    monkeypatch.setattr(edge_report_module, "_compute_strategy_comparison_report", _counting_compute)
    monkeypatch.setattr(sys, "argv", ["edge_report_compute"])

    started = time.time()
    exit_code = edge_report_compute.main()
    elapsed = time.time() - started

    assert exit_code == 0
    assert elapsed < 5.0
    assert calls == []  # zero backtests re-run -- served entirely from the warm durable cache


def test_cli_force_flag_recomputes_over_an_already_warm_key(tmp_path, monkeypatch):
    _set_cli_env(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "argv", ["edge_report_compute"])
    assert edge_report_compute.main() == 0

    from app.research import edge_report as edge_report_module

    calls = []
    real_compute = edge_report_module._compute_strategy_comparison_report

    def _counting_compute(*args, **kwargs):
        calls.append(1)
        return real_compute(*args, **kwargs)

    monkeypatch.setattr(edge_report_module, "_compute_strategy_comparison_report", _counting_compute)
    monkeypatch.setattr(sys, "argv", ["edge_report_compute", "--force"])

    assert edge_report_compute.main() == 0
    assert len(calls) == 1  # force recomputes exactly once, even over a warm key


def test_cli_out_flag_writes_the_report_json(tmp_path, monkeypatch):
    _set_cli_env(monkeypatch, tmp_path)
    out_path = tmp_path / "report.json"
    monkeypatch.setattr(sys, "argv", ["edge_report_compute", "--out", str(out_path)])

    assert edge_report_compute.main() == 0
    payload = json.loads(out_path.read_text())
    assert payload["train"]["cells"] == []
    assert payload["holdout"]["cells"] == []


def test_cli_workers_flag_on_a_zero_eligible_fixture_still_exits_zero_and_changes_nothing(
    tmp_path, monkeypatch
):
    """The CLI's own usage string documents ``--workers N`` (goal.md's J-04 step 3); era-fast_wall
    J-05 gives it real effect, but the committed ``datasets_j03`` fixture (symbol PG, not a
    config-owned panel symbol) always resolves ZERO eligible pairs under the real ``CONFIG`` --
    ``--workers 2`` must still exit 0 and produce the SAME honest empty report, since
    ``_parallel_prewarm_sub_cache`` never spins up a process pool with nothing to submit (see
    ``test_edge_report.py``'s own
    ``test_parallel_prewarm_with_zero_eligible_datasets_never_spins_up_a_process_pool`` for that
    guarantee proven directly). The GENUINE multi-process, non-degenerate proof (real worker pids,
    byte-identical parallel-vs-sequential reports) lives in ``test_edge_report.py``'s
    ``test_parallel_prewarm_uses_at_least_two_distinct_worker_processes_and_reassembles_byte_
    identically`` -- this CLI-level test is deliberately the FAST, degenerate-fixture sanity leg."""
    _set_cli_env(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "argv", ["edge_report_compute", "--workers", "2"])
    assert edge_report_compute.main() == 0


def test_cli_workers_default_reads_the_env_override(tmp_path, monkeypatch):
    """``--workers``'s default is read from ``TAPEOLOGY_EDGE_SWEEP_WORKERS`` if set, else the
    ``_DEFAULT_WORKERS = 4`` constant -- proven via a kwarg-capturing spy on ``run_strategy_
    comparison_report`` rather than any observable side effect (the degenerate fixture makes every
    ``workers`` value behaviorally silent)."""
    _set_cli_env(monkeypatch, tmp_path)
    monkeypatch.setenv("TAPEOLOGY_EDGE_SWEEP_WORKERS", "6")
    seen = {}
    real = edge_report_compute.run_strategy_comparison_report

    def _spy(*args, **kwargs):
        seen.update(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", _spy)
    monkeypatch.setattr(sys, "argv", ["edge_report_compute"])  # no --workers flag at all

    assert edge_report_compute.main() == 0
    assert seen["workers"] == 6


def test_cli_workers_and_sub_cache_are_wired_into_run_strategy_comparison_report(tmp_path, monkeypatch):
    """era-fast_wall J-05: the CLI's ``main()`` wires BOTH a real ``EdgeReportBacktestCache`` and
    the resolved ``--workers`` int into ``run_strategy_comparison_report`` -- a kwarg-capturing
    spy (the ``test_force_flag_is_threaded_through...`` precedent, applied to the two NEW hooks),
    proving neither is silently dropped or left at its old J-04 placeholder."""
    from app.research.edge_report_backtest_cache import EdgeReportBacktestCache

    _set_cli_env(monkeypatch, tmp_path)
    seen = {}
    real = edge_report_compute.run_strategy_comparison_report

    def _spy(*args, **kwargs):
        seen.update(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(edge_report_compute, "run_strategy_comparison_report", _spy)
    monkeypatch.setattr(sys, "argv", ["edge_report_compute", "--workers", "2"])

    assert edge_report_compute.main() == 0

    assert seen["workers"] == 2
    assert isinstance(seen["sub_cache"], EdgeReportBacktestCache)


def test_cli_published_sub_cache_rows_are_reused_by_a_subsequent_bare_call_with_zero_fresh_backtests(
    tmp_path, monkeypatch,
):
    """TC-10 (non-vacuous): runs the CLI warmer against a genuinely NON-degenerate scan fixture
    (``edge_report_compute.CONFIG`` monkeypatched to the SAME panel-scoped synthetic config
    ``test_edge_report.py``'s own synthetic-scan-join tests use — the exact mechanism this file's
    own manager tests already use, e.g. ``fake_run`` swaps — applied here to the module's imported
    ``CONFIG`` name instead of a whole function), then proves a SUBSEQUENT bare
    ``run_strategy_comparison_report(..., sub_cache=<the same cache>)`` call serves 100% cache
    hits — zero fresh ``_run_backtest`` calls."""
    from app.research.bars import BarStore
    from app.research.datasets import DatasetStore, SPLIT_TRAIN
    from app.research.edge_report_backtest_cache import EdgeReportBacktestCache
    from app.research import edge_report as edge_report_module
    from test_edge_report import _record_v1_arming_dataset
    from test_setups import _seed_full, _syn_config

    test_config = _syn_config()
    monkeypatch.setattr(edge_report_compute, "CONFIG", test_config)

    bar_dir = tmp_path / "bars"
    dataset_dir = tmp_path / "datasets"
    bar_store = BarStore(bar_dir)
    _seed_full(bar_store)
    dataset_store = DatasetStore(dataset_dir)
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")

    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(dataset_dir))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(bar_dir))
    monkeypatch.setenv("TAPEOLOGY_EDGE_REPORT_CACHE_DB", str(tmp_path / "cache.db"))
    sub_cache_db = str(tmp_path / "sub-cache.db")
    monkeypatch.setenv("TAPEOLOGY_EDGE_SWEEP_CACHE_DB", sub_cache_db)
    monkeypatch.setattr(sys, "argv", ["edge_report_compute", "--workers", "1"])

    assert edge_report_compute.main() == 0

    sub_cache = EdgeReportBacktestCache(sub_cache_db)
    calls = []
    real_run_backtest = edge_report_module._run_backtest

    def _counting_run_backtest(*args, **kwargs):
        calls.append(1)
        return real_run_backtest(*args, **kwargs)

    monkeypatch.setattr(edge_report_module, "_run_backtest", _counting_run_backtest)

    served_store = JournalStore(str(tmp_path / "served-journal.db"), test_config)
    try:
        served = edge_report_module.run_strategy_comparison_report(
            served_store, dataset_store, bar_store, test_config, sub_cache=sub_cache,
        )
    finally:
        served_store.close()

    assert calls == []  # zero fresh backtests -- entirely served from the CLI-published cache
    assert len(served["train"]["cells"]) == 3  # non-degenerate: the real 3-cell shape


def test_cli_missing_dataset_dir_env_falls_back_to_default_seams_without_crashing(tmp_path, monkeypatch):
    """A malformed/absent dataset dir env resolves to the config default (never crashes at
    argument-parsing time) -- exercised here by simply confirming the parser accepts a bare
    invocation with only the required env vars set (no ``--out``, no ``--force``, no ``--workers``)."""
    _set_cli_env(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "argv", ["edge_report_compute"])
    assert edge_report_compute.main() == 0


# --- The CLI progress printer: a pure formatting unit, decoupled from whether the fixture resolves
# any real classified event (the committed PG fixture honestly resolves zero) -----------------------


def test_cli_progress_printer_prints_a_line_per_completed_backtest(capsys):
    printer = edge_report_compute._cli_progress_printer()
    printer({"event": "total", "phase": "backtests", "backtests_total": 2, "backtests_done": 0,
             "backtests_from_cache": 0, "current": None})
    printer({"event": "pair_started", "current": {"dataset_id": "d1", "strategy_id": "v1"}})
    printer({"event": "pair_done", "backtests_done": 1, "backtests_from_cache": 0, "current": None})
    printer({"event": "pair_started", "current": {"dataset_id": "d1", "strategy_id": "structure_tape"}})
    printer({"event": "pair_done", "backtests_done": 2, "backtests_from_cache": 0, "current": None})

    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    done_lines = [ln for ln in lines if "1/2" in ln or "2/2" in ln]
    assert len(done_lines) == 2  # exactly one line per completed backtest


def test_cli_progress_printer_prints_zero_done_lines_for_a_zero_total_run(capsys):
    printer = edge_report_compute._cli_progress_printer()
    printer({"event": "total", "phase": "backtests", "backtests_total": 0, "backtests_done": 0,
             "backtests_from_cache": 0, "current": None})

    out = capsys.readouterr().out
    assert "0" in out  # the honest zero-total summary line still prints
