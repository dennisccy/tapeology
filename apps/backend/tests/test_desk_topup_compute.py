"""``desk_topup_compute.py`` (Era B "The Desk", J-02 + J-09) — the desk bar top-up: manager
mechanics (single-flight, cancel, atomic progress) plus the store-first/resumability guarantee,
plus the HTTP routes; and (J-09, this iteration) the append-only run-log writer wired into both the
manager and the CLI.

Manager-mechanics tests substitute a FAKE ``_run_one_pair`` (monkeypatched onto this module's own
imported name — the ``test_edge_report_compute.py`` fake-swap precedent) for deterministic,
threading-free control over timing. The store-first/resumability guarantee and the honest-failure
taxonomy are proven end to end against the REAL ``record_bar_series`` path, through
``app.dependency_overrides[get_market_adapter]`` injecting ``FakeAdapter`` (the
``test_bars_api.py`` seam) — zero real network calls anywhere in this file. Route-level tests
(``TestClient``) cover GET-never-computes (TC-10), single-flight/cancel through HTTP, and idle
cancel returning 409 (TC-15) — the manager itself never raises on an idle cancel (the
``cancel_edge_report_compute`` precedent: the ROUTE owns the 409).

J-09 tests are threaded through the SAME manager/route fixtures rather than a separate file's own
fixture set, since every J-09 assertion is "and ALSO a run record landed correctly" on top of an
existing J-02 scenario (cancelled, failing-pair, second-run, CLI) — the store module's OWN
isolated discipline (checksum, corruption, no-dedup-append-only, interrupted-run) lives in
``test_desk_topup_log.py``."""

from __future__ import annotations

import sys
import threading
import time
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager as ws_manager
from app.providers.adapters.base import NoDataForWindow
from app.research import desk_topup_compute
from app.research.bar_index import BarIndex
from app.research.bars import BarStore
from app.research.desk_coverage import DESK_TOPUP_TIMEFRAMES
from app.research.desk_routes import get_desk_topup_manager, get_topup_run_store
from app.research.desk_topup_compute import DeskTopupComputeManager, run_topup
from app.research.desk_topup_log import TopupRunStore
from app.research.desk_universe import UniverseStore
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore
from fakes import FakeAdapter

TWO_MEMBERS = ["AAA", "BBB"]
FIVE_MEMBERS = ["AAA", "BBB", "CCC", "DDD", "EEE"]


def _bars():
    from app.providers.adapters.base import RawBar

    return (
        RawBar("X", "1d", 1780358400.0, 100.0, 101.0, 99.0, 100.5, 1000),
        RawBar("X", "1d", 1780444800.0, 100.5, 102.0, 100.0, 101.5, 1100),
    )


def _register_universe(tmp_path, members: list[str]) -> UniverseStore:
    store = UniverseStore(tmp_path / "universe")
    store.record(
        members=sorted(members), raw_members={m: m for m in members},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    return store


def _wait_for_terminal(mgr: DeskTopupComputeManager, timeout: float = 5.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        snap = mgr.snapshot()
        if snap is not None and snap["state"] != "running":
            return snap
        time.sleep(0.01)
    raise AssertionError("desk top-up compute job never reached a terminal state")


@pytest.fixture
def manager_env(tmp_path):
    """Manager-level tests: no ``TestClient``/``set_registry`` needed — every dependency is passed
    explicitly to ``manager.trigger(...)`` (the ``EdgeReportComputeManager`` per-call-injection
    precedent), so this fixture stays fully isolated from the global registry singleton.
    ``topup_run_store`` (J-09) is the 5th value every ``manager_env``-consuming test now threads
    into ``.trigger(...)`` — the run-log store, hermetic per test."""
    universe_store = UniverseStore(tmp_path / "universe")
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "index.db"))
    journal = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(journal, CONFIG)
    topup_run_store = TopupRunStore(tmp_path / "topup_runs")
    yield universe_store, bar_store, bar_index, registry, topup_run_store
    journal.close()
    app.dependency_overrides.pop(get_market_adapter, None)


def _inject_adapter(**kwargs) -> FakeAdapter:
    adapter = FakeAdapter(**kwargs)
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    return adapter


# ==================================================================================================
# Manager mechanics -- a FAKE `_run_one_pair` gives deterministic, threading-free control (never
# wall-clock luck).
# ==================================================================================================


def test_no_job_has_ever_run_snapshot_is_none():
    assert DeskTopupComputeManager().snapshot() is None


def test_trigger_with_no_universe_snapshot_is_an_honest_zero_pair_job_that_completes(manager_env):
    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
    mgr = DeskTopupComputeManager()

    result = mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    assert result["started"] is True
    assert result["compute"]["progress"]["pairs_total"] == 0

    snap = _wait_for_terminal(mgr)
    assert snap["state"] == "done"
    assert snap["progress"]["outcomes"] == []
    mgr.join_all(timeout=5)


def test_trigger_shape_pairs_total_equals_members_times_four(manager_env, monkeypatch):
    """TC-6 (shape): ``pairs_total == N * len(DESK_TOPUP_TIMEFRAMES)``, known synchronously at
    trigger time (before the background thread even starts)."""
    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
    universe_store.record(
        members=sorted(FIVE_MEMBERS), raw_members={m: m for m in FIVE_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )

    def fake_one_pair(symbol, timeframe, *_args):
        return "fetched", None

    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", fake_one_pair)

    mgr = DeskTopupComputeManager()
    result = mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    assert result["compute"]["progress"]["pairs_total"] == len(FIVE_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)

    snap = _wait_for_terminal(mgr)
    assert snap["state"] == "done"
    outcomes = snap["progress"]["outcomes"]
    assert len(outcomes) == len(FIVE_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
    assert {o["outcome"] for o in outcomes} == {"fetched"}
    assert {(o["symbol"], o["timeframe"]) for o in outcomes} == {
        (s, tf) for s in FIVE_MEMBERS for tf in DESK_TOPUP_TIMEFRAMES
    }
    mgr.join_all(timeout=5)


def test_second_trigger_while_running_returns_the_same_job_started_false(manager_env, monkeypatch):
    """TC-9: single-flight."""
    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
    universe_store.record(
        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    started = threading.Event()
    release = threading.Event()

    def fake_one_pair(symbol, timeframe, *_args):
        started.set()
        release.wait(timeout=5)
        return "fetched", None

    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", fake_one_pair)

    mgr = DeskTopupComputeManager()
    first = mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    assert started.wait(timeout=5)

    second = mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    assert second["started"] is False
    assert second["compute"]["id"] == first["compute"]["id"]

    release.set()
    _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)


def test_trigger_after_a_terminal_job_starts_a_genuinely_new_job(manager_env, monkeypatch):
    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
    universe_store.record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", lambda *a: ("fetched", None))

    mgr = DeskTopupComputeManager()
    first = mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)

    second = mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    assert second["started"] is True
    assert second["compute"]["id"] != first["compute"]["id"]
    _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)


def test_a_cancellation_signal_resolves_state_cancelled_with_the_partial_outcomes_recorded(
    manager_env, monkeypatch
):
    """Cancellation mechanics: the worker observes ``should_abort`` BETWEEN pairs and stops early
    -- the job resolves ``"cancelled"`` with exactly the outcomes recorded before the signal fired,
    never a raise, never a fabricated remaining outcome."""
    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
    universe_store.record(
        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    started = threading.Event()
    release = threading.Event()
    calls: list[tuple[str, str]] = []

    def fake_one_pair(symbol, timeframe, *_args):
        calls.append((symbol, timeframe))
        if len(calls) == 2:
            started.set()
            release.wait(timeout=5)
        return "fetched", None

    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", fake_one_pair)

    mgr = DeskTopupComputeManager()
    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    assert started.wait(timeout=5)
    mgr.cancel()
    release.set()

    snap = _wait_for_terminal(mgr)
    assert snap["state"] == "cancelled"
    assert snap["error"] is None
    assert len(snap["progress"]["outcomes"]) == 2  # the 2 pairs already in flight when cancel fired
    mgr.join_all(timeout=5)

    # TC-4 (J-09): the persisted run record mirrors the cancelled state, with `pairs_attempted`
    # strictly less than `pairs_total`.
    records, errors = topup_run_store.list()
    assert errors == []
    assert len(records) == 1
    assert records[0]["state"] == "cancelled"
    assert records[0]["pairs_total"] == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
    assert records[0]["pairs_attempted"] == 2
    assert records[0]["pairs_attempted"] < records[0]["pairs_total"]
    assert len(records[0]["outcomes"]) == 2


def test_an_unexpected_crash_outside_run_topup_resolves_state_failed(manager_env, monkeypatch):
    """Safety net: a failure that ``run_topup`` itself cannot recover from (never a per-pair
    outcome -- those are caught inside ``_run_one_pair``) resolves the WHOLE job ``"failed"``, the
    message surfaced verbatim (the ``EdgeReportComputeManager`` precedent)."""
    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
    universe_store.record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )

    def fake_run_topup(*args, **kwargs):
        raise RuntimeError("synthetic catastrophic failure")

    monkeypatch.setattr(desk_topup_compute, "run_topup", fake_run_topup)

    mgr = DeskTopupComputeManager()
    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    snap = _wait_for_terminal(mgr)

    assert snap["state"] == "failed"
    assert snap["error"] == "synthetic catastrophic failure"
    mgr.join_all(timeout=5)

    # J-09: a whole-job "failed" (something escaped run_topup itself) is a genuine terminal state
    # reached WITHIN the process, so a record IS written -- distinct from the interrupted-run case
    # (the process ending before the writer is ever called). `fake_run_topup` raises before
    # publishing any pair, so the record's outcomes are honestly empty.
    records, errors = topup_run_store.list()
    assert errors == []
    assert len(records) == 1
    assert records[0]["state"] == "failed"
    assert records[0]["outcomes"] == []
    assert records[0]["pairs_attempted"] == 0
    assert records[0]["pairs_total"] == len(DESK_TOPUP_TIMEFRAMES)  # 1 member x 4 timeframes


@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
def test_a_walk_interrupted_before_the_terminal_write_leaves_zero_run_record(
    manager_env, monkeypatch
):
    """TC-7 (J-09), the NON-vacuous half: a run that genuinely WALKED pairs — publishing them into
    the live progress snapshot — but whose process/thread ends before the writer's terminal call
    persists NOTHING. ``SystemExit`` raised inside the walk is the simulation: ``_run_one_pair``'s
    own ``except Exception`` does not catch it, ``run_topup`` propagates it, and ``_work``'s
    ``except Exception`` does not catch it either — so neither ``_resolve`` nor the writer ever runs
    and ``threading`` retires the worker silently, exactly as a killed process would. The store must
    gain zero files even though two pairs were already attempted and recorded in memory — never a
    fabricated, partial, or "pending" record (``test_desk_topup_log.py``'s store-level sibling test
    proves the same for a store that was never touched at all; this one proves the MANAGER never
    writes speculatively mid-walk)."""
    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
    universe_store.record(
        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    calls: list[tuple[str, str]] = []

    def fake_one_pair(symbol, timeframe, *_args):
        calls.append((symbol, timeframe))
        if len(calls) == 3:
            raise SystemExit("simulated process death mid-walk")
        return "fetched", None

    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", fake_one_pair)

    mgr = DeskTopupComputeManager()
    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    mgr.join_all(timeout=5)

    assert len(calls) == 3  # the walk genuinely ran, and died on the third pair
    snap = mgr.snapshot()
    assert snap["state"] == "running"  # never resolved -- process-scoped state is honestly lost
    assert len(snap["progress"]["outcomes"]) == 2  # two pairs really were attempted

    records, errors = topup_run_store.list()
    assert records == [] and errors == []
    assert not (topup_run_store.root).exists()  # not even an empty/partial file was created


def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_reference(manager_env, monkeypatch):
    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
    universe_store.record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", lambda *a: ("fetched", None))

    mgr = DeskTopupComputeManager()
    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    snap = _wait_for_terminal(mgr)
    snap["progress"]["outcomes"].append({"poison": True})
    snap["progress"]["outcomes"][0]["outcome"] = "POISONED"

    fresh = mgr.snapshot()
    assert len(fresh["progress"]["outcomes"]) == 4  # AAA x 4 timeframes -- the mutation above is invisible
    assert all(o["outcome"] != "POISONED" for o in fresh["progress"]["outcomes"])
    mgr.join_all(timeout=5)


def test_manager_triggered_runs_persisted_outcomes_are_byte_identical_to_run_topups_own_return(
    manager_env, monkeypatch
):
    """TC-2 (J-09): the persisted run record's ``outcomes`` list is byte-identical (same values,
    same order) to the list ``run_topup`` itself returned for that walk — proven with a spy
    WRAPPING the REAL ``run_topup`` (never a fake substitute), capturing its actual return value
    for direct comparison against what landed in the store."""
    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
    universe_store.record(
        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    _inject_adapter(bars=_bars())

    real_run_topup = desk_topup_compute.run_topup
    captured: list[list[dict]] = []

    def _spy(*args, **kwargs):
        result = real_run_topup(*args, **kwargs)
        captured.append(result)
        return result

    monkeypatch.setattr(desk_topup_compute, "run_topup", _spy)

    mgr = DeskTopupComputeManager()
    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)

    assert len(captured) == 1  # run_topup was called exactly once for this job
    records, errors = topup_run_store.list()
    assert errors == []
    assert len(records) == 1
    assert records[0]["outcomes"] == captured[0]  # byte-identical to run_topup's own return
    assert records[0]["state"] == "done"
    assert records[0]["pairs_total"] == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
    assert records[0]["pairs_attempted"] == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
    assert records[0]["universe_snapshot_id"] is not None
    assert records[0]["requested_window"]["start"] < records[0]["requested_window"]["end"]
    assert records[0]["config_fingerprint"] == CONFIG.config_fingerprint()


# ==================================================================================================
# Store-first / resumability + honest failure -- against the REAL record_bar_series path, via
# FakeAdapter (zero network).
# ==================================================================================================


def test_first_run_fetches_every_pair_and_records_it(manager_env):
    """TC-6 mechanics (real path): a fresh store, every pair genuinely fetched."""
    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
    universe_store.record(
        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    adapter = _inject_adapter(bars=_bars())

    mgr = DeskTopupComputeManager()
    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    snap = _wait_for_terminal(mgr)

    assert snap["state"] == "done"
    outcomes = snap["progress"]["outcomes"]
    assert len(outcomes) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
    assert {o["outcome"] for o in outcomes} == {"fetched"}
    assert len(adapter.fetch_bars_calls) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
    mgr.join_all(timeout=5)


def test_second_run_over_the_same_universe_is_all_reused_with_zero_vendor_calls(manager_env):
    """TC-7: store-first proven end to end."""
    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
    universe_store.record(
        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    adapter = _inject_adapter(bars=_bars())

    first_mgr = DeskTopupComputeManager()
    first_mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    _wait_for_terminal(first_mgr)
    first_mgr.join_all(timeout=5)
    calls_after_first_run = len(adapter.fetch_bars_calls)
    assert calls_after_first_run == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)

    second_mgr = DeskTopupComputeManager()
    second_mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    snap = _wait_for_terminal(second_mgr)

    assert snap["state"] == "done"
    outcomes = snap["progress"]["outcomes"]
    assert len(outcomes) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
    assert {o["outcome"] for o in outcomes} == {"reused"}
    assert len(adapter.fetch_bars_calls) == calls_after_first_run  # zero NEW vendor calls
    second_mgr.join_all(timeout=5)

    # TC-6 (J-09): the second run appended a SECOND, distinct record -- the first stays exactly as
    # it was (no dedup, no update; see test_desk_topup_log.py for the byte-level file-unchanged
    # proof of this same guarantee at the store layer).
    records, errors = topup_run_store.list()
    assert errors == []
    assert len(records) == 2
    assert records[0]["id"] != records[1]["id"]
    assert {o["outcome"] for o in records[0]["outcomes"]} == {"fetched"}  # the FIRST run's own record
    assert {o["outcome"] for o in records[1]["outcomes"]} == {"reused"}  # the SECOND run's own record


def test_pairs_already_recorded_report_reused_while_the_rest_report_fetched_the_resumability_guarantee(
    manager_env,
):
    """TC-8 (the resumability GUARANTEE): resumability in this design comes entirely from
    ``record_bar_series``'s own store-first coordinator, not from job-level "resume from pair N"
    bookkeeping -- so this test proves the guarantee directly (deterministic, no threading): M
    pairs are recorded FIRST (standing in for an earlier top-up run that was cancelled after
    completing them), then a FRESH top-up trigger runs over ALL pairs. Those M pairs must report
    "reused" with no growth in vendor calls; the rest must report "fetched". (The cancellation
    MECHANISM itself -- state transitions to "cancelled" with a partial outcomes list -- is proven
    separately, above, with a deterministic mocked fake.)"""
    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
    universe_store.record(
        members=sorted(FIVE_MEMBERS), raw_members={m: m for m in FIVE_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    adapter = _inject_adapter(bars=_bars())

    # Pre-populate exactly the pairs an earlier, cancelled run would already have completed: every
    # timeframe for the first 2 (of 5) members, in the SAME iteration order run_topup itself uses
    # -- via the SAME real record_bar_series path (run_topup directly, zero shortcuts), standing
    # in for what an earlier top-up job would have already written to the store before a cancel.
    pre_populated = [(s, tf) for s in sorted(TWO_MEMBERS) for tf in DESK_TOPUP_TIMEFRAMES]
    run_topup(sorted(TWO_MEMBERS), bar_store, bar_index, registry)
    calls_after_prepopulate = len(adapter.fetch_bars_calls)
    assert calls_after_prepopulate == len(pre_populated)

    mgr = DeskTopupComputeManager()
    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    snap = _wait_for_terminal(mgr)

    assert snap["state"] == "done"
    by_pair = {(o["symbol"], o["timeframe"]): o["outcome"] for o in snap["progress"]["outcomes"]}
    for pair in pre_populated:
        assert by_pair[pair] == "reused", pair
    remaining = [(s, tf) for s in sorted(FIVE_MEMBERS) if s not in TWO_MEMBERS for tf in DESK_TOPUP_TIMEFRAMES]
    for pair in remaining:
        assert by_pair[pair] == "fetched", pair
    # Only the REMAINING pairs made a new vendor call -- the pre-populated ones did not.
    assert len(adapter.fetch_bars_calls) == calls_after_prepopulate + len(remaining)
    mgr.join_all(timeout=5)


def test_a_failing_pair_reports_failed_with_the_detail_preserved_and_the_run_continues(manager_env):
    """TC-14: an honest per-pair vendor failure never aborts the whole job, and the detail is
    preserved verbatim -- proven with a small local adapter double that fails on exactly ONE call
    (never all of them), so "the run continues to the remaining pairs" is genuinely distinguishable
    from "the job stopped after the first failure"."""

    class _NthCallFailsAdapter:
        name = "fake"

        def __init__(self, bars, fail_on_call_index: int, exc: Exception) -> None:
            self._bars = bars
            self._fail_on = fail_on_call_index
            self._exc = exc
            self.fetch_bars_calls: list[tuple] = []

        def is_available(self) -> bool:
            return True

        def fetch_bars(self, symbol, start, end, timeframe):
            self.fetch_bars_calls.append((symbol, start, end, timeframe))
            if len(self.fetch_bars_calls) == self._fail_on:
                raise self._exc
            return self._bars

    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
    universe_store.record(
        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    adapter = _NthCallFailsAdapter(
        bars=_bars(), fail_on_call_index=2, exc=NoDataForWindow("no data for that window")
    )
    app.dependency_overrides[get_market_adapter] = lambda: adapter

    mgr = DeskTopupComputeManager()
    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
    snap = _wait_for_terminal(mgr)

    assert snap["state"] == "done"  # the JOB completes even though one pair failed
    outcomes = snap["progress"]["outcomes"]
    assert len(outcomes) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)  # every pair attempted
    failed = [o for o in outcomes if o["outcome"] == "failed"]
    assert len(failed) == 1
    assert "no data for that window" in failed[0]["detail"]
    assert sum(1 for o in outcomes if o["outcome"] == "fetched") == len(outcomes) - 1
    mgr.join_all(timeout=5)
    app.dependency_overrides.pop(get_market_adapter, None)

    # TC-5 (J-09): the persisted record's failed pair carries its detail verbatim, and every OTHER
    # pair (both before and after it in iteration order) is still present -- the run-level state is
    # still "done" (a per-pair failure never demotes the run itself; see the module docstring's
    # trap #2 distinction).
    records, errors = topup_run_store.list()
    assert errors == []
    assert len(records) == 1
    assert records[0]["state"] == "done"
    persisted_failed = [o for o in records[0]["outcomes"] if o["outcome"] == "failed"]
    assert len(persisted_failed) == 1
    assert persisted_failed[0]["detail"] == failed[0]["detail"]
    assert len(records[0]["outcomes"]) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)


# ==================================================================================================
# goal-desk-iter-26 (J-17) -- a per-pair fetch window derived from that pair's OWN frozen content
# (never `bar_index.window_end_utc`), plus the honest "unchanged" outcome for a vendor call that
# genuinely ran and returned only content already frozen. `_plant_bar_series`/`_epoch_days_ago`
# give a test control over EXACTLY which bars are frozen for a pair BEFORE the walk under test
# runs, by writing directly through `BarStore.record` -- bypassing `record_bar_series`/the fetch
# route (and therefore `bar_index`) entirely, so a subsequent real walk's store-first index lookup
# genuinely misses and falls through to the injected `FakeAdapter`.
#
# THE ONE EXISTING-ASSERTION CARVE-OUT (reviewer-directed; see
# `reports/reviews/goal-desk-iter-26-review.md`, CRITICAL):
# `test_cli_triggered_run_persists_a_record_with_the_identical_shape_as_a_manager_triggered_one`'s
# `assert outcome.keys() == {...}` (above, ~line 1081) is the SINGLE existing assertion this
# iteration edits -- its four-key literal is EXTENDED to the eight keys the Data Contract mandates
# on every per-pair outcome entry (`requested_window`/`store_frozen_from`/`store_frozen_through`/
# `window_basis`). It is a schema mirror, not a window pin, so the iteration spec's own
# "disclose rather than edit" exception (which covers only tests pinning the SHIPPED WINDOW) does
# not reach it, while the DEFINITION OF DONE's unqualified "full backend suite green" does.
# There is no implementation of the mandated contract under which a REAL run's persisted outcome
# entries keep exactly four keys. Proven structurally, not just observed: the SAME file's
# `test_manager_triggered_runs_persisted_outcomes_are_byte_identical_to_run_topups_own_return`
# requires the persisted record's `outcomes` to equal `run_topup`'s own raw return value
# byte-for-byte, so the new fields MUST originate inside `run_topup`/`_run_one_pair` itself (never
# a downstream enrichment step) for that assertion to keep holding -- which means every path
# (manager- and CLI-triggered alike) produces the same eight-key entries. The edit preserves the
# assertion's stated intent (exact cross-path key-SET equality against the one shared writer's
# schema; a drift between the CLI and manager paths still fails it) and is the ONLY edit to any
# pre-existing assertion in this file -- TC-7 (all-reused second run) and TC-8 (resumability), the
# two the spec names explicitly, pass untouched. See `docs/handoffs/goal-desk-iter-26-dev.md`.
# ==================================================================================================


def _epoch_days_ago(days: float) -> float:
    return (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()


def _plant_bar_series(bar_store: BarStore, *, symbol: str, timeframe: str, feed: str, bars) -> dict:
    """Directly record a bar series into `bar_store` (bypassing `record_bar_series`/the fetch
    route and `bar_index` entirely) -- see this section's own header comment."""
    epochs = [b.epoch for b in bars]
    window_start = datetime.fromtimestamp(min(epochs), tz=timezone.utc).date().isoformat() + "T00:00:00Z"
    window_end = datetime.fromtimestamp(max(epochs), tz=timezone.utc).date().isoformat() + "T00:00:00Z"
    return bar_store.record(
        symbol=symbol, timeframe=timeframe,
        window_start_utc=window_start, window_end_utc=window_end,
        feed=feed, bars=list(bars),
    )


def test_desk_topup_compute_reads_merged_bars_and_never_reads_bar_index_window_end_utc():
    """A source-introspection guard (TESTING REQUIREMENTS' own explicit ask): the window
    derivation reads the canonical `BarStore.merged_bars` accessor and never ATTRIBUTE-ACCESSES
    `bar_index`'s `window_end_utc` field — proven by reading `desk_topup_compute.py`'s own source
    as text (the `test_desk_ui_guards.py` pattern, applied backend-side). Matches a literal
    `.window_end_utc` attribute access (never present in this module's CODE — only in its prose,
    which explains why it deliberately reads `merged_bars` instead), so a real regression (some
    future edit reaching into `bar_index`'s own `window_end_utc` column) is what this guard would
    actually catch — proven by the counter-test below."""
    import pathlib
    import re

    source = pathlib.Path(desk_topup_compute.__file__).read_text()
    assert "merged_bars(" in source
    assert re.search(r"\.window_end_utc\b", source) is None


def test_the_window_end_utc_guard_can_fail_on_a_seeded_violation():
    """The guard above can never fail proves nothing -- a seeded `.window_end_utc` attribute
    access is caught."""
    import re

    seeded = 'latest = bar_index.window_end_utc\nmerged_bars(x)\n'
    assert re.search(r"\.window_end_utc\b", seeded) is not None


def test_pair_window_is_the_byte_identical_full_lookback_when_nothing_is_frozen(manager_env):
    """TC-2 (goal.md J-17): a pair with NO frozen bars asks for the byte-identical full
    `_TOPUP_LOOKBACK_DAYS` window `_fetch_window_now()` already asks for today."""
    _universe_store, bar_store, _bar_index, _registry, _topup_run_store = manager_env
    expected_start, expected_end = desk_topup_compute._fetch_window_now()

    window = desk_topup_compute._pair_window(bar_store, "NEW", "1d")

    assert window["window_basis"] == "full_lookback"
    assert window["requested_window"] == {"start": expected_start, "end": expected_end}
    assert window["store_frozen_from"] is None
    assert window["store_frozen_through"] is None


def test_pair_window_is_the_byte_identical_full_lookback_when_frozen_history_is_shorter_than_the_lookback(
    manager_env,
):
    """TC-3 (goal.md J-17): a pair whose frozen history does NOT reach back to the lookback start
    keeps asking for the SAME full window -- short histories keep deepening exactly as they do
    today."""
    _universe_store, bar_store, _bar_index, registry, _topup_run_store = manager_env
    short_epoch = _epoch_days_ago(10)  # far short of the 730-day lookback
    from app.providers.adapters.base import RawBar

    _plant_bar_series(
        bar_store, symbol="SHORT", timeframe="1d", feed=registry.config.historical_feed,
        bars=[RawBar("SHORT", "1d", short_epoch, 10.0, 11.0, 9.0, 10.5, 500)],
    )
    expected_start, expected_end = desk_topup_compute._fetch_window_now()

    window = desk_topup_compute._pair_window(bar_store, "SHORT", "1d")

    assert window["window_basis"] == "full_lookback"
    assert window["requested_window"] == {"start": expected_start, "end": expected_end}
    assert window["store_frozen_from"] == desk_topup_compute._iso_bar_epoch(short_epoch)
    assert window["store_frozen_through"] == desk_topup_compute._iso_bar_epoch(short_epoch)


def test_pair_window_is_a_tail_window_when_frozen_history_reaches_the_lookback_start(manager_env):
    """TC-1 (goal.md J-17): a pair whose frozen bars reach back past `_TOPUP_LOOKBACK_DAYS` asks
    for a tail window starting at its own newest frozen bar's UTC date."""
    _universe_store, bar_store, _bar_index, registry, _topup_run_store = manager_env
    deep_epoch = _epoch_days_ago(desk_topup_compute._TOPUP_LOOKBACK_DAYS + 70)  # past the lookback
    newest_epoch = _epoch_days_ago(5)
    from app.providers.adapters.base import RawBar

    _plant_bar_series(
        bar_store, symbol="DEEP", timeframe="1d", feed=registry.config.historical_feed,
        bars=[
            RawBar("DEEP", "1d", deep_epoch, 10.0, 11.0, 9.0, 10.5, 500),
            RawBar("DEEP", "1d", newest_epoch, 20.0, 21.0, 19.0, 20.5, 700),
        ],
    )
    _lookback_start, expected_end = desk_topup_compute._fetch_window_now()
    expected_tail_start = (
        datetime.fromtimestamp(newest_epoch, tz=timezone.utc).date().isoformat() + "T00:00:00Z"
    )

    window = desk_topup_compute._pair_window(bar_store, "DEEP", "1d")

    assert window["window_basis"] == "tail"
    assert window["requested_window"] == {"start": expected_tail_start, "end": expected_end}
    assert window["store_frozen_from"] == desk_topup_compute._iso_bar_epoch(deep_epoch)
    assert window["store_frozen_through"] == desk_topup_compute._iso_bar_epoch(newest_epoch)


def test_run_topup_asks_the_fake_adapter_for_the_derived_tail_window_and_records_it_on_the_outcome(
    manager_env,
):
    """TC-1's end-to-end half: the walk's fake adapter genuinely RECEIVES the derived tail window
    (proven on `adapter.fetch_bars_calls`), and the recorded outcome entry carries the identical
    `requested_window`/`window_basis`/`store_frozen_from`/`store_frozen_through`."""
    _universe_store, bar_store, bar_index, registry, _topup_run_store = manager_env
    deep_epoch = _epoch_days_ago(desk_topup_compute._TOPUP_LOOKBACK_DAYS + 70)
    newest_epoch = _epoch_days_ago(5)
    from app.providers.adapters.base import RawBar

    _plant_bar_series(
        bar_store, symbol="DEEP", timeframe="1d", feed=registry.config.historical_feed,
        bars=[
            RawBar("DEEP", "1d", deep_epoch, 10.0, 11.0, 9.0, 10.5, 500),
            RawBar("DEEP", "1d", newest_epoch, 20.0, 21.0, 19.0, 20.5, 700),
        ],
    )
    adapter = _inject_adapter(bars=_bars())  # distinct content -> a genuinely NEW series ("fetched")
    expected_tail_start = (
        datetime.fromtimestamp(newest_epoch, tz=timezone.utc).date().isoformat() + "T00:00:00Z"
    )

    outcomes = run_topup(["DEEP"], bar_store, bar_index, registry)

    entry = next(o for o in outcomes if o["symbol"] == "DEEP" and o["timeframe"] == "1d")
    assert entry["outcome"] == "fetched"
    assert entry["window_basis"] == "tail"
    assert entry["requested_window"]["start"] == expected_tail_start
    assert entry["store_frozen_through"] == desk_topup_compute._iso_bar_epoch(newest_epoch)
    call = next(c for c in adapter.fetch_bars_calls if c[0] == "DEEP" and c[3] == "1d")
    assert call[1].astimezone(timezone.utc).date().isoformat() == expected_tail_start[:10]


def test_a_vendor_answer_holding_only_already_frozen_bars_records_unchanged_not_failed(manager_env):
    """TC-4 (goal.md J-17): the vendor's "you already have this" answer --
    `record_bar_series`'s own 409 (`BarSeriesAlreadyRegistered`) -- is recorded as `"unchanged"`,
    never `"failed"`: a genuine vendor call ran, but wrote no second series file.
    `requested_window` and `store_frozen_through` are both present on the recorded entry."""
    _universe_store, bar_store, bar_index, registry, _topup_run_store = manager_env
    already_frozen = _bars()
    _plant_bar_series(
        bar_store, symbol="SAME", timeframe="1d", feed=registry.config.historical_feed,
        bars=already_frozen,
    )
    before_series, before_errors = bar_store.list(include_bars=False)
    assert before_errors == []
    _inject_adapter(bars=already_frozen)  # the vendor's answer holds ONLY content already frozen

    outcomes = run_topup(["SAME"], bar_store, bar_index, registry)

    entry = next(o for o in outcomes if o["symbol"] == "SAME" and o["timeframe"] == "1d")
    assert entry["outcome"] == "unchanged"
    assert entry["detail"] is not None
    assert entry["requested_window"] is not None
    assert entry["store_frozen_through"] is not None

    after_series, after_errors = bar_store.list(include_bars=False)
    assert after_errors == []
    # No second series file was written for this pair -- the store gained nothing new.
    same_before = [m for m in before_series if m["symbol"] == "SAME" and m["timeframe"] == "1d"]
    same_after = [m for m in after_series if m["symbol"] == "SAME" and m["timeframe"] == "1d"]
    assert len(same_before) == 1
    assert same_after == same_before


# ==================================================================================================
# Routes -- GET-never-computes, single-flight/cancel through HTTP, idle-cancel 409 (TC-15).
# ==================================================================================================


@pytest.fixture
def route_ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    fresh_manager = DeskTopupComputeManager()
    app.dependency_overrides[get_desk_topup_manager] = lambda: fresh_manager
    with TestClient(app) as client:
        yield client, fresh_manager, tmp_path
    fresh_manager.join_all(timeout=5.0)
    for ticker in list(ws_manager._engines.keys()):
        ws_manager.stop(ticker)
    set_registry(None)
    app.dependency_overrides.pop(get_market_adapter, None)
    app.dependency_overrides.pop(get_desk_topup_manager, None)
    store.close()


def test_get_topup_compute_before_any_trigger_is_an_honest_null_and_starts_nothing(route_ctx):
    """TC-10: GET-never-computes."""
    client, fresh_manager, _tmp_path = route_ctx
    adapter = _inject_adapter(bars=_bars())

    r = client.get("/research/desk/topup/compute")
    assert r.status_code == 200
    assert r.json() is None
    assert fresh_manager.snapshot() is None
    assert adapter.fetch_bars_calls == []


def test_coverage_get_before_any_universe_or_bars_starts_nothing(route_ctx):
    """TC-10, the coverage half: a GET issues zero vendor/compute side effects."""
    client, _fresh_manager, _tmp_path = route_ctx
    adapter = _inject_adapter(bars=_bars())

    r = client.get("/research/desk/coverage")
    assert r.status_code == 200
    assert r.json() == {
        "universe_snapshot_id": None,
        "timeframes": list(DESK_TOPUP_TIMEFRAMES),
        "members": [],
    }
    assert adapter.fetch_bars_calls == []


def test_post_trigger_runs_to_completion_and_get_polls_the_same_snapshot(route_ctx):
    client, _fresh_manager, tmp_path = route_ctx
    UniverseStore(tmp_path / "universe").record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    _inject_adapter(bars=_bars())

    r = client.post("/research/desk/topup/compute")
    assert r.status_code == 200
    body = r.json()
    assert body["started"] is True
    assert body["compute"]["progress"]["pairs_total"] == len(DESK_TOPUP_TIMEFRAMES)

    deadline = time.time() + 5
    snap = None
    while time.time() < deadline:
        snap = client.get("/research/desk/topup/compute").json()
        if snap is not None and snap["state"] != "running":
            break
        time.sleep(0.02)
    assert snap["state"] == "done"
    assert len(snap["progress"]["outcomes"]) == len(DESK_TOPUP_TIMEFRAMES)


def test_cancel_while_idle_is_409(route_ctx):
    """TC-15."""
    client, _fresh_manager, _tmp_path = route_ctx
    r = client.post("/research/desk/topup/compute/cancel")
    assert r.status_code == 409


def test_cancel_while_running_succeeds_and_a_subsequent_cancel_is_409(route_ctx, monkeypatch):
    client, fresh_manager, tmp_path = route_ctx
    UniverseStore(tmp_path / "universe").record(
        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    started = threading.Event()
    release = threading.Event()

    def fake_one_pair(symbol, timeframe, *_args):
        started.set()
        release.wait(timeout=5)
        return "fetched", None

    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", fake_one_pair)

    trigger_resp = client.post("/research/desk/topup/compute")
    assert trigger_resp.json()["started"] is True
    assert started.wait(timeout=5)

    cancel_resp = client.post("/research/desk/topup/compute/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json() == {"cancelling": True}
    release.set()

    _wait_for_terminal(fresh_manager)
    fresh_manager.join_all(timeout=5)

    idle_cancel = client.post("/research/desk/topup/compute/cancel")
    assert idle_cancel.status_code == 409


# ==================================================================================================
# GET /research/desk/topup/runs (J-09) -- honest-empty before any run, GET-never-computes,
# meta-only list + full latest record, and the store's directory resolution (TC-14: already
# scoped by `route_ctx`'s own `TAPEOLOGY_DESK_UNIVERSE_DIR` override -- `resolve_desk_topup_log_dir`
# defaults to a SIBLING of it, exactly like `resolve_desk_screen_dir`, so no separate env var is
# needed here).
# ==================================================================================================


def test_get_topup_runs_before_any_run_is_the_honest_empty_payload_and_starts_nothing(route_ctx):
    """TC-1 + TC-8: HTTP 200 ``{"runs": [], "latest": null, "integrity_errors": []}`` before any
    top-up run has ever completed, and the GET itself triggers no compute (the ``/topup/compute``
    snapshot stays untouched). ``integrity_errors`` added goal-desk-iter-16 (J-12) — see
    ``test_get_topup_runs_surfaces_a_corrupted_run_records_integrity_error`` below for the
    non-empty case."""
    client, _fresh_manager, _tmp_path = route_ctx
    adapter = _inject_adapter(bars=_bars())

    r = client.get("/research/desk/topup/runs")
    assert r.status_code == 200
    assert r.json() == {"runs": [], "latest": None, "integrity_errors": []}
    assert adapter.fetch_bars_calls == []

    # TC-8, precisely: calling the new GET (any number of times) never starts a top-up compute --
    # the UNRELATED `/topup/compute` snapshot stays `null`.
    client.get("/research/desk/topup/runs")
    client.get("/research/desk/topup/runs")
    assert client.get("/research/desk/topup/compute").json() is None


def test_get_topup_runs_after_a_completed_run_serves_the_full_latest_record_and_a_meta_only_list_entry(
    route_ctx,
):
    client, _fresh_manager, tmp_path = route_ctx
    UniverseStore(tmp_path / "universe").record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    _inject_adapter(bars=_bars())

    trigger_resp = client.post("/research/desk/topup/compute")
    assert trigger_resp.json()["started"] is True

    deadline = time.time() + 5
    while time.time() < deadline:
        snap = client.get("/research/desk/topup/compute").json()
        if snap is not None and snap["state"] != "running":
            break
        time.sleep(0.02)

    runs_deadline = time.time() + 5
    body = None
    while time.time() < runs_deadline:
        body = client.get("/research/desk/topup/runs").json()
        if body["latest"] is not None:
            break
        time.sleep(0.02)  # the writer call happens just after the snapshot resolves terminal

    assert body["latest"] is not None
    latest = body["latest"]
    assert latest["state"] == "done"
    assert latest["pairs_total"] == len(DESK_TOPUP_TIMEFRAMES)
    assert latest["pairs_attempted"] == len(DESK_TOPUP_TIMEFRAMES)
    assert len(latest["outcomes"]) == len(DESK_TOPUP_TIMEFRAMES)
    assert latest["universe_snapshot_id"] is not None

    # The bulk `runs` list carries the SAME run as a meta-only projection -- every field except
    # `outcomes` (mirrors the screen list's own meta-only convention).
    assert len(body["runs"]) == 1
    meta = body["runs"][0]
    assert "outcomes" not in meta
    assert meta["id"] == latest["id"]
    assert meta["state"] == latest["state"]
    assert meta["pairs_total"] == latest["pairs_total"]
    assert meta["pairs_attempted"] == latest["pairs_attempted"]
    assert body["integrity_errors"] == []  # a genuinely clean run has no integrity problem to name


def test_get_topup_runs_surfaces_a_corrupted_run_records_integrity_error(route_ctx):
    """goal-desk-iter-16 (J-12) TC-5: a corrupt run-record file planted in the run log's own
    directory -- a SIBLING of `route_ctx`'s scoped `TAPEOLOGY_DESK_UNIVERSE_DIR`, resolved via
    `get_topup_run_store` exactly as the route itself resolves it, never `apps/backend/.data` --
    is named in `integrity_errors` and excluded from `runs`/`latest`, alongside one genuine record
    that survives untouched."""
    client, _fresh_manager, _tmp_path = route_ctx
    store = get_topup_run_store()
    genuine = store.record(
        universe_snapshot_id="universe-2026-07-25-49b33fa31680",
        requested_window={"start": "2024-07-28T00:00:00Z", "end": "2026-07-28T00:00:00Z"},
        config_fingerprint=CONFIG.config_fingerprint(),
        started_utc="2026-07-28T09:00:00.000000Z",
        finished_utc="2026-07-28T09:05:00.000000Z",
        state="done",
        pairs_total=1,
        outcomes=[{"symbol": "AAA", "timeframe": "1h", "outcome": "fetched", "detail": None}],
    )
    corrupt_path = store.root / "topup-2026-01-01-deadbeef0000.json"
    corrupt_path.write_text("{not json")

    r = client.get("/research/desk/topup/runs")
    assert r.status_code == 200
    body = r.json()
    assert len(body["runs"]) == 1
    assert body["runs"][0]["id"] == genuine["id"]
    assert body["latest"]["id"] == genuine["id"]
    assert body["integrity_errors"] == [
        {"file": corrupt_path.name, "error": body["integrity_errors"][0]["error"]}
    ]
    assert "corrupted or tampered" in body["integrity_errors"][0]["error"]


def test_topup_run_store_directory_defaults_to_a_sibling_of_the_scoped_universe_dir(route_ctx):
    """TC-14: with no ``TAPEOLOGY_DESK_TOPUP_LOG_DIR`` override, the run log lands as a sibling of
    whatever ``TAPEOLOGY_DESK_UNIVERSE_DIR`` this test's own ``route_ctx`` fixture already scopes
    to ``tmp_path`` -- proven by reading the file straight off that exact path, with zero
    additional env var set by this test."""
    client, _fresh_manager, tmp_path = route_ctx
    UniverseStore(tmp_path / "universe").record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    _inject_adapter(bars=_bars())

    client.post("/research/desk/topup/compute")
    deadline = time.time() + 5
    while time.time() < deadline:
        snap = client.get("/research/desk/topup/compute").json()
        if snap is not None and snap["state"] != "running":
            break
        time.sleep(0.02)

    store = TopupRunStore(tmp_path / "topup_runs")  # the sibling-of-universe-dir default, by hand
    records, errors = store.list()
    assert errors == []
    assert len(records) == 1  # the route's own default resolution landed exactly here


# ==================================================================================================
# The CLI warmer -- TC-3: a CLI-triggered run's record has the identical shape (field names/types)
# as a manager-triggered one, proving ONE shared writer / ONE schema.
# ==================================================================================================


@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    """Hermetic env-var scoping for ``desk_topup_compute.main()`` -- the ``test_edge_report_compute.
    py``/``_set_cli_env`` precedent, applied to the desk top-up's own three store seams (universe,
    bars, journal); the run-log dir is left on its DEFAULT resolution (a sibling of the scoped
    universe dir) rather than a fourth explicit override, proving TC-14's default path is what the
    real operator CLI actually uses too."""
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    UniverseStore(tmp_path / "universe").record(
        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    yield tmp_path
    app.dependency_overrides.pop(get_market_adapter, None)


def test_cli_triggered_run_persists_a_record_with_the_identical_shape_as_a_manager_triggered_one(
    cli_env, monkeypatch, capsys
):
    """TC-3."""
    tmp_path = cli_env
    _inject_adapter(bars=_bars())
    monkeypatch.setattr(sys, "argv", ["desk_topup_compute"])

    exit_code = desk_topup_compute.main()
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "desk top-up complete" in out

    store = TopupRunStore(tmp_path / "topup_runs")
    records, errors = store.list()
    assert errors == []
    assert len(records) == 1
    record = records[0]

    # The identical schema a manager-triggered record carries -- same field NAMES and TYPES (one
    # shared writer, one shape; see the manager-side
    # `test_manager_triggered_runs_persisted_outcomes_are_byte_identical_to_run_topups_own_return`
    # for the sibling manager-path assertion this mirrors).
    assert set(record.keys()) == {
        "id", "universe_snapshot_id", "requested_window", "config_fingerprint",
        "started_utc", "finished_utc", "state", "pairs_total", "pairs_attempted", "outcomes",
    }
    assert isinstance(record["id"], str)
    assert isinstance(record["universe_snapshot_id"], str)
    assert record["requested_window"].keys() == {"start", "end"}
    assert record["config_fingerprint"] == CONFIG.config_fingerprint()
    assert record["state"] == "done"  # the CLI has no cancel signal -- always "done" on success
    assert record["pairs_total"] == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
    assert record["pairs_attempted"] == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
    assert len(record["outcomes"]) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
    assert {o["outcome"] for o in record["outcomes"]} == {"fetched"}
    for outcome in record["outcomes"]:
        # goal-desk-iter-26 (J-17), the ONE reviewer-sanctioned carve-out to this iteration's
        # "existing assertions pass unmodified" rule: this pin is a mirror of the SHARED writer's
        # per-pair schema, extended -- not relaxed -- with the four Data-Contract fields every path
        # now carries. It stays an exact key-SET equality, so cross-path schema drift (the property
        # this test's own name claims) still fails it. See the section header below and
        # `docs/handoffs/goal-desk-iter-26-dev.md` for why no implementation of the mandated
        # contract can keep a real run's outcome entries at four keys.
        assert outcome.keys() == {
            "symbol", "timeframe", "outcome", "detail",
            "requested_window", "store_frozen_from", "store_frozen_through", "window_basis",
        }


def test_cli_with_no_universe_snapshot_persists_no_run_record(tmp_path, monkeypatch):
    """The CLI's existing no-universe refusal (unmodified, exit 1) writes no run record -- there is
    nothing to walk, so the writer is never reached (the honest interrupted/never-attempted case,
    not a bug)."""
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    monkeypatch.setattr(sys, "argv", ["desk_topup_compute"])

    exit_code = desk_topup_compute.main()
    assert exit_code == 1

    store = TopupRunStore(tmp_path / "topup_runs")
    records, errors = store.list()
    assert records == [] and errors == []
    assert not (tmp_path / "topup_runs").exists()
