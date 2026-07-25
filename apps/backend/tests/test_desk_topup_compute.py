"""``desk_topup_compute.py`` (Era B "The Desk", J-02) — the desk bar top-up: manager mechanics
(single-flight, cancel, atomic progress) plus the store-first/resumability guarantee, plus the
three HTTP routes.

Manager-mechanics tests substitute a FAKE ``_run_one_pair`` (monkeypatched onto this module's own
imported name — the ``test_edge_report_compute.py`` fake-swap precedent) for deterministic,
threading-free control over timing. The store-first/resumability guarantee and the honest-failure
taxonomy are proven end to end against the REAL ``record_bar_series`` path, through
``app.dependency_overrides[get_market_adapter]`` injecting ``FakeAdapter`` (the
``test_bars_api.py`` seam) — zero real network calls anywhere in this file. Route-level tests
(``TestClient``) cover GET-never-computes (TC-10), single-flight/cancel through HTTP, and idle
cancel returning 409 (TC-15) — the manager itself never raises on an idle cancel (the
``cancel_edge_report_compute`` precedent: the ROUTE owns the 409).
"""

from __future__ import annotations

import threading
import time

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager as ws_manager
from app.providers.adapters.base import NoDataForWindow
from app.research import desk_topup_compute
from app.research.bar_index import BarIndex
from app.research.bars import BarStore
from app.research.desk_coverage import DESK_TOPUP_TIMEFRAMES
from app.research.desk_routes import get_desk_topup_manager
from app.research.desk_topup_compute import DeskTopupComputeManager, run_topup
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
    precedent), so this fixture stays fully isolated from the global registry singleton."""
    universe_store = UniverseStore(tmp_path / "universe")
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "index.db"))
    journal = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(journal, CONFIG)
    yield universe_store, bar_store, bar_index, registry
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
    universe_store, bar_store, bar_index, registry = manager_env
    mgr = DeskTopupComputeManager()

    result = mgr.trigger(universe_store, bar_store, bar_index, registry)
    assert result["started"] is True
    assert result["compute"]["progress"]["pairs_total"] == 0

    snap = _wait_for_terminal(mgr)
    assert snap["state"] == "done"
    assert snap["progress"]["outcomes"] == []
    mgr.join_all(timeout=5)


def test_trigger_shape_pairs_total_equals_members_times_four(manager_env, monkeypatch):
    """TC-6 (shape): ``pairs_total == N * len(DESK_TOPUP_TIMEFRAMES)``, known synchronously at
    trigger time (before the background thread even starts)."""
    universe_store, bar_store, bar_index, registry = manager_env
    universe_store.record(
        members=sorted(FIVE_MEMBERS), raw_members={m: m for m in FIVE_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )

    def fake_one_pair(symbol, timeframe, *_args):
        return "fetched", None

    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", fake_one_pair)

    mgr = DeskTopupComputeManager()
    result = mgr.trigger(universe_store, bar_store, bar_index, registry)
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
    universe_store, bar_store, bar_index, registry = manager_env
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
    first = mgr.trigger(universe_store, bar_store, bar_index, registry)
    assert started.wait(timeout=5)

    second = mgr.trigger(universe_store, bar_store, bar_index, registry)
    assert second["started"] is False
    assert second["compute"]["id"] == first["compute"]["id"]

    release.set()
    _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)


def test_trigger_after_a_terminal_job_starts_a_genuinely_new_job(manager_env, monkeypatch):
    universe_store, bar_store, bar_index, registry = manager_env
    universe_store.record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", lambda *a: ("fetched", None))

    mgr = DeskTopupComputeManager()
    first = mgr.trigger(universe_store, bar_store, bar_index, registry)
    _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)

    second = mgr.trigger(universe_store, bar_store, bar_index, registry)
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
    universe_store, bar_store, bar_index, registry = manager_env
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
    mgr.trigger(universe_store, bar_store, bar_index, registry)
    assert started.wait(timeout=5)
    mgr.cancel()
    release.set()

    snap = _wait_for_terminal(mgr)
    assert snap["state"] == "cancelled"
    assert snap["error"] is None
    assert len(snap["progress"]["outcomes"]) == 2  # the 2 pairs already in flight when cancel fired
    mgr.join_all(timeout=5)


def test_an_unexpected_crash_outside_run_topup_resolves_state_failed(manager_env, monkeypatch):
    """Safety net: a failure that ``run_topup`` itself cannot recover from (never a per-pair
    outcome -- those are caught inside ``_run_one_pair``) resolves the WHOLE job ``"failed"``, the
    message surfaced verbatim (the ``EdgeReportComputeManager`` precedent)."""
    universe_store, bar_store, bar_index, registry = manager_env
    universe_store.record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )

    def fake_run_topup(*args, **kwargs):
        raise RuntimeError("synthetic catastrophic failure")

    monkeypatch.setattr(desk_topup_compute, "run_topup", fake_run_topup)

    mgr = DeskTopupComputeManager()
    mgr.trigger(universe_store, bar_store, bar_index, registry)
    snap = _wait_for_terminal(mgr)

    assert snap["state"] == "failed"
    assert snap["error"] == "synthetic catastrophic failure"
    mgr.join_all(timeout=5)


def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_reference(manager_env, monkeypatch):
    universe_store, bar_store, bar_index, registry = manager_env
    universe_store.record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", lambda *a: ("fetched", None))

    mgr = DeskTopupComputeManager()
    mgr.trigger(universe_store, bar_store, bar_index, registry)
    snap = _wait_for_terminal(mgr)
    snap["progress"]["outcomes"].append({"poison": True})
    snap["progress"]["outcomes"][0]["outcome"] = "POISONED"

    fresh = mgr.snapshot()
    assert len(fresh["progress"]["outcomes"]) == 4  # AAA x 4 timeframes -- the mutation above is invisible
    assert all(o["outcome"] != "POISONED" for o in fresh["progress"]["outcomes"])
    mgr.join_all(timeout=5)


# ==================================================================================================
# Store-first / resumability + honest failure -- against the REAL record_bar_series path, via
# FakeAdapter (zero network).
# ==================================================================================================


def test_first_run_fetches_every_pair_and_records_it(manager_env):
    """TC-6 mechanics (real path): a fresh store, every pair genuinely fetched."""
    universe_store, bar_store, bar_index, registry = manager_env
    universe_store.record(
        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    adapter = _inject_adapter(bars=_bars())

    mgr = DeskTopupComputeManager()
    mgr.trigger(universe_store, bar_store, bar_index, registry)
    snap = _wait_for_terminal(mgr)

    assert snap["state"] == "done"
    outcomes = snap["progress"]["outcomes"]
    assert len(outcomes) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
    assert {o["outcome"] for o in outcomes} == {"fetched"}
    assert len(adapter.fetch_bars_calls) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
    mgr.join_all(timeout=5)


def test_second_run_over_the_same_universe_is_all_reused_with_zero_vendor_calls(manager_env):
    """TC-7: store-first proven end to end."""
    universe_store, bar_store, bar_index, registry = manager_env
    universe_store.record(
        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    adapter = _inject_adapter(bars=_bars())

    first_mgr = DeskTopupComputeManager()
    first_mgr.trigger(universe_store, bar_store, bar_index, registry)
    _wait_for_terminal(first_mgr)
    first_mgr.join_all(timeout=5)
    calls_after_first_run = len(adapter.fetch_bars_calls)
    assert calls_after_first_run == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)

    second_mgr = DeskTopupComputeManager()
    second_mgr.trigger(universe_store, bar_store, bar_index, registry)
    snap = _wait_for_terminal(second_mgr)

    assert snap["state"] == "done"
    outcomes = snap["progress"]["outcomes"]
    assert len(outcomes) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
    assert {o["outcome"] for o in outcomes} == {"reused"}
    assert len(adapter.fetch_bars_calls) == calls_after_first_run  # zero NEW vendor calls
    second_mgr.join_all(timeout=5)


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
    universe_store, bar_store, bar_index, registry = manager_env
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
    mgr.trigger(universe_store, bar_store, bar_index, registry)
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

    universe_store, bar_store, bar_index, registry = manager_env
    universe_store.record(
        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    adapter = _NthCallFailsAdapter(
        bars=_bars(), fail_on_call_index=2, exc=NoDataForWindow("no data for that window")
    )
    app.dependency_overrides[get_market_adapter] = lambda: adapter

    mgr = DeskTopupComputeManager()
    mgr.trigger(universe_store, bar_store, bar_index, registry)
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
