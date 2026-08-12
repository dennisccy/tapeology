"""``desk_playbook_backscan.py`` (Era B2, J-07) -- ``plan_backscan``'s purity, ``run_backscan``'s
resumable/cancel-safe walk over the ONE shared ``run_playbook_and_record`` entry point,
``DeskPlaybookBackscanComputeManager``'s single-flight + cancel mechanics, ``BackscanRunStore``'s
terminal-state-only ledger discipline, the ``_assert_scoped`` positive scoping guard (TC-13), and
the three wired routes end to end.

Reuses ``test_desk_playbook``'s own bar/universe fixture helpers (the ``test_desk_playbook_compute``
cross-file-import precedent) rather than duplicating them. Test-first contract: TC-1 through TC-17
in ``docs/phases/goal-playbook-iter-7.md``."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.research import desk_playbook_backscan
from app.research.bars import BarStore
from app.research.desk_playbook import PlaybookStore, compute_playbook_input_signature
from app.research.desk_playbook_backscan import (
    BackscanRunStore,
    DeskPlaybookBackscanComputeManager,
    PlaybookNotScopedError,
    _assert_scoped,
    malformed_days,
    plan_backscan,
    resolve_desk_playbook_backscan_log_dir,
    run_backscan,
)
from app.research.desk_routes import get_desk_playbook_backscan_manager
from app.research.desk_universe import UniverseStore
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore
from test_desk_playbook import E_OPEN, _bar, _plant, _plant_baseline_sessions, _register_universe

D0 = "2026-06-22"
D1 = "2026-06-23"
D2 = "2026-06-24"
DAY_SECONDS = 86_400.0


def _plant_firing_session_at(bar_store: BarStore, symbol: str, day_open: float) -> None:
    """The canonical open_high_break session (``test_desk_playbook``'s own ``_plant_firing_session``
    shape), shifted to fire on ANY day open -- fires exactly one signal every time, so three calls
    at three different day opens plant three independently-recordable sessions."""
    bars_1m = [_bar(symbol, "1m", day_open + i * 60.0, 100.5, 101.0, 100.0, 100.5, 500) for i in range(15)]
    bars_5m = [
        _bar(symbol, "5m", day_open, 100.5, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", day_open + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", day_open + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", day_open + 900.0, 100.8, 101.5, 100.7, 101.2, 1000),
        _bar(symbol, "5m", day_open + 1200.0, 101.2, 101.4, 101.0, 101.1, 800),
        _bar(symbol, "5m", day_open + 1500.0, 101.1, 101.3, 100.9, 101.0, 800),
    ]
    _plant(bar_store, symbol, "1m", bars_1m)
    _plant(bar_store, symbol, "5m", bars_5m)


def _plant_three_firing_sessions(bar_store: BarStore, symbol: str = "AAA") -> None:
    """10 prior baseline sessions (2026-06-08..17) plus three independently-firing sessions on
    D0/D1/D2 (2026-06-22..24) -- each of D1/D2 also inherits the sessions before it as EXTRA prior
    baseline (>= the 10-session floor either way)."""
    _plant_baseline_sessions(bar_store, symbol)
    _plant_firing_session_at(bar_store, symbol, E_OPEN)
    _plant_firing_session_at(bar_store, symbol, E_OPEN + DAY_SECONDS)
    _plant_firing_session_at(bar_store, symbol, E_OPEN + 2 * DAY_SECONDS)


def _plant_daily_bar(bar_store: BarStore, symbol: str, day: str) -> None:
    epoch = datetime.fromisoformat(f"{day}T00:00:00+00:00").timestamp()
    _plant(bar_store, symbol, "1d", [_bar(symbol, "1d", epoch, 100.0, 101.0, 99.0, 100.0)])


@pytest.fixture
def env(tmp_path):
    bar_store = BarStore(tmp_path / "bars")
    universe_store = _register_universe(tmp_path, ["AAA"])
    playbook_store = PlaybookStore(tmp_path / "playbook")
    return bar_store, universe_store, playbook_store


def _members(universe_store: UniverseStore) -> list[str]:
    records, _errors = universe_store.list()
    return list(records[-1]["members"]) if records else []


# --- plan_backscan: TC-1, TC-3, TC-7, TC-9, TC-17 ---------------------------------------------------


def test_tc1_three_recorded_session_dates_none_yet_in_the_playbook_store_are_all_missing(tmp_path, env):
    bar_store, universe_store, playbook_store = env
    _plant_three_firing_sessions(bar_store)

    result = plan_backscan(D0, D2, bar_store, _members(universe_store), CONFIG.config_fingerprint(), playbook_store)

    assert result["from"] == D0 and result["to"] == D2
    assert result["total"] == 3 and result["missing"] == 3
    assert [d["session_date"] for d in result["dates"]] == [D0, D1, D2]
    assert all(d["status"] == "missing_at_current_signature" for d in result["dates"])


def test_tc3_after_recording_all_three_the_plan_shows_zero_missing(tmp_path, env):
    bar_store, universe_store, playbook_store = env
    _plant_three_firing_sessions(bar_store)
    run_backscan([D0, D1, D2], universe_store, bar_store, CONFIG, playbook_store)

    result = plan_backscan(D0, D2, bar_store, _members(universe_store), CONFIG.config_fingerprint(), playbook_store)

    assert result["missing"] == 0
    assert all(d["status"] == "recorded_at_current_signature" for d in result["dates"])


def test_tc7_a_monkeypatched_threshold_flips_every_recorded_date_back_to_missing(tmp_path, env, monkeypatch):
    bar_store, universe_store, playbook_store = env
    _plant_three_firing_sessions(bar_store)
    run_backscan([D0, D1, D2], universe_store, bar_store, CONFIG, playbook_store)
    before = plan_backscan(D0, D2, bar_store, _members(universe_store), CONFIG.config_fingerprint(), playbook_store)
    assert before["missing"] == 0

    from app.research import desk_playbook as desk_playbook_module

    monkeypatch.setattr(desk_playbook_module, "PLAYBOOK_OR_MINUTES", 999)

    after = plan_backscan(D0, D2, bar_store, _members(universe_store), CONFIG.config_fingerprint(), playbook_store)
    assert after["missing"] == 3
    assert all(d["status"] == "missing_at_current_signature" for d in after["dates"])


def test_tc17_an_inverted_range_is_an_honest_empty_plan(tmp_path, env):
    bar_store, universe_store, playbook_store = env
    result = plan_backscan(D2, D0, bar_store, [], CONFIG.config_fingerprint(), playbook_store)
    assert result == {
        "from": D2, "to": D0,
        "playbook_input_signature": compute_playbook_input_signature(bar_store, [], CONFIG.config_fingerprint()),
        "dates": [], "total": 0, "missing": 0,
    }


# --- goal-playbook-iter-8 TC-9: a malformed/partial date is an honest empty plan, never a 500 ------


def test_iter8_tc9_a_malformed_from_date_is_an_honest_empty_plan_not_a_500(tmp_path, env):
    """A half-typed From box (``2026-06-2``, mid-keystroke) used to raise ``ValueError`` straight
    out of ``date.fromisoformat`` -- the SAME empty-plan shape the already-handled inverted-range
    case (TC-17) returns, never an exception."""
    bar_store, universe_store, playbook_store = env
    result = plan_backscan("2026-06-2", D2, bar_store, [], CONFIG.config_fingerprint(), playbook_store)
    assert result == {
        "from": "2026-06-2", "to": D2,
        "playbook_input_signature": compute_playbook_input_signature(bar_store, [], CONFIG.config_fingerprint()),
        "dates": [], "total": 0, "missing": 0,
    }


def test_iter8_tc9_a_malformed_to_date_is_also_an_honest_empty_plan(tmp_path, env):
    bar_store, universe_store, playbook_store = env
    result = plan_backscan(D0, "not-a-date", bar_store, [], CONFIG.config_fingerprint(), playbook_store)
    assert result["dates"] == [] and result["total"] == 0 and result["missing"] == 0


def test_iter8_tc9_route_level_malformed_date_returns_http_200_never_500(tmp_path, monkeypatch):
    """Route-level companion (mirrors ``test_tc9_route_level_stub_barstore_returns_http_200_...``
    above): ``GET .../backscan/plan?from=2026-06-2&to=...`` returns an honest HTTP 200 empty plan,
    never the HTTP 500 the uncaught ``ValueError`` used to produce."""
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)

    with TestClient(app) as client:
        response = client.get(
            "/research/desk/playbook/backscan/plan", params={"from": "2026-06-2", "to": D2}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["dates"] == [] and body["total"] == 0 and body["missing"] == 0

    set_registry(None)
    store.close()


# --- goal-playbook-iter-8 AUDIT (B1): the plan READ tolerates a malformed date; the TRIGGER must
# refuse it outright, never start a phantom job that appends an un-prunable "done" ledger row -------


def test_audit_b1_malformed_days_names_only_the_unparseable_boundaries():
    """The ONE shared parse rule: an inverted range is NOT malformed (both boundaries are real
    days, it simply names an empty span -- TC-17's honestly-empty walk stays legitimate)."""
    assert malformed_days(D0, D2) == []
    assert malformed_days(D2, D0) == []  # inverted, but both are real calendar days
    assert malformed_days("2026-06-2", D2) == ["2026-06-2"]
    assert malformed_days(D0, "not-a-date") == ["not-a-date"]
    assert malformed_days("2026-06-2", "") == ["2026-06-2", ""]


def test_audit_b1_trigger_refuses_a_malformed_date_and_writes_no_ledger_row(route_ctx):
    """Before this fix the iter-8 ``_planned_dates`` try/except turned a half-typed From box into
    an HTTP 200 ``started: true`` job over ZERO dates, which then finalized ``"done"`` and appended
    a permanent ``{"from": "2026-06-2", ..., "status": "done", "planned_total": 0}`` row to the
    append-only run ledger -- a false success over a string nothing could parse, in a store the
    immutable-data rail forbids ever pruning. The trigger now refuses (422) BEFORE any job exists,
    the ``trigger_desk_playbook_compute`` non-session pre-check precedent verbatim."""
    client, manager, _tmp = route_ctx

    response = client.post(
        "/research/desk/playbook/backscan/compute",
        json={"from_day": "2026-06-2", "to_day": D2},
    )
    assert response.status_code == 422
    assert "2026-06-2" in response.json()["detail"]

    assert manager.snapshot()["status"] == "idle"  # no job was ever created
    runs = client.get("/research/desk/playbook/backscan/runs").json()
    assert runs["runs"] == [] and runs["latest"] is None  # and no ledger row was written


def test_audit_b1_an_inverted_range_still_starts_an_honestly_empty_walk(route_ctx):
    """The refusal is scoped to UNPARSEABLE boundaries only -- TC-17's inverted-but-real range
    keeps its established behavior (a started job that walks zero dates and records its own honest
    ledger row), so this fix narrows nothing the spec already decided."""
    client, manager, _tmp = route_ctx
    response = client.post(
        "/research/desk/playbook/backscan/compute", json={"from_day": D2, "to_day": D0}
    )
    assert response.status_code == 200
    assert response.json()["started"] is True
    snap = _wait_for_terminal(manager)
    assert snap["status"] == "done" and snap["planned_total"] == 0


class _RaisingBarStore:
    """A stub proving ``plan_backscan`` performs ZERO ``BarStore`` bar-CONTENT reads (TC-9) --
    every content-reading method raises; ``list`` (metadata-only, exactly what
    ``compute_playbook_input_signature`` calls) is the one method delegated to a real store."""

    def __init__(self, real: BarStore) -> None:
        self._real = real

    def list(self, *args, **kwargs):
        return self._real.list(*args, **kwargs)

    def get(self, *args, **kwargs):
        raise AssertionError("plan_backscan must never call BarStore.get")

    def merged_bars(self, *args, **kwargs):
        raise AssertionError("plan_backscan must never call BarStore.merged_bars")

    def candles(self, *args, **kwargs):
        raise AssertionError("plan_backscan must never call BarStore.candles")

    def merged_candles(self, *args, **kwargs):
        raise AssertionError("plan_backscan must never call BarStore.merged_candles")

    def load_bars(self, *args, **kwargs):
        raise AssertionError("plan_backscan must never call BarStore.load_bars")

    def record(self, *args, **kwargs):
        raise AssertionError("plan_backscan must never call BarStore.record")


def test_tc9_plan_backscan_performs_zero_bar_content_reads(tmp_path, env):
    bar_store, universe_store, playbook_store = env
    _plant_three_firing_sessions(bar_store)
    stub = _RaisingBarStore(bar_store)

    result = plan_backscan(D0, D2, stub, _members(universe_store), CONFIG.config_fingerprint(), playbook_store)

    assert result["total"] == 3
    assert len(result["dates"]) == 3


def test_tc9_route_level_stub_barstore_returns_http_200_with_populated_dates(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)

    bar_store = BarStore(tmp_path / "bars")
    _plant_three_firing_sessions(bar_store)
    universe_store = _register_universe(tmp_path, ["AAA"])

    def _boom(*_args, **_kwargs):
        raise AssertionError("plan_backscan route must never call this BarStore method")

    for name in ("get", "candles", "merged_candles", "merged_bars", "load_bars"):
        monkeypatch.setattr(BarStore, name, _boom)

    with TestClient(app) as client:
        response = client.get("/research/desk/playbook/backscan/plan", params={"from": D0, "to": D2})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["dates"]) == 3

    set_registry(None)
    store.close()


# --- run_backscan: TC-2, TC-4, TC-8, TC-12 (short-side is a separate test file) --------------------


def test_tc2_a_fresh_backscan_records_all_three_dates(tmp_path, env):
    bar_store, universe_store, playbook_store = env
    _plant_three_firing_sessions(bar_store)

    outcomes = run_backscan([D0, D1, D2], universe_store, bar_store, CONFIG, playbook_store)

    assert [o["outcome"] for o in outcomes] == ["recorded", "recorded", "recorded"]
    records, errors = playbook_store.list()
    assert errors == [] and len(records) == 3


def test_tc4_a_second_backscan_over_the_same_range_reuses_with_zero_detector_calls(tmp_path, env, monkeypatch):
    bar_store, universe_store, playbook_store = env
    _plant_three_firing_sessions(bar_store)
    run_backscan([D0, D1, D2], universe_store, bar_store, CONFIG, playbook_store)

    from app.research import desk_playbook_compute as desk_playbook_compute_module

    calls = []

    def _counting(*args, **kwargs):
        calls.append(1)
        raise AssertionError("compute_playbook must never be called on an all-reused re-run")

    monkeypatch.setattr(desk_playbook_compute_module, "compute_playbook", _counting)

    outcomes = run_backscan([D0, D1, D2], universe_store, bar_store, CONFIG, playbook_store)

    assert [o["outcome"] for o in outcomes] == ["reused", "reused", "reused"]
    assert calls == []


def test_tc8_a_date_with_zero_bars_bracketed_by_daily_evidence_is_refused_non_session(tmp_path, env):
    bar_store, universe_store, playbook_store = env
    _plant_baseline_sessions(bar_store, "AAA", dates=[f"2026-06-{d:02d}" for d in range(1, 11)])
    _plant_firing_session_at(bar_store, "AAA", E_OPEN)  # 2026-06-22 -- fires
    _plant_firing_session_at(bar_store, "AAA", E_OPEN + DAY_SECONDS)  # 2026-06-23 -- fires
    # A provable non-session gap: daily bars bracket 06-24 without recording it.
    for day in (D0, D1, "2026-06-25"):
        _plant_daily_bar(bar_store, "AAA", day)

    outcomes = run_backscan([D0, D1, "2026-06-24"], universe_store, bar_store, CONFIG, playbook_store)

    assert [o["outcome"] for o in outcomes] == ["recorded", "recorded", "refused_non_session"]
    assert outcomes[2]["detail"] is not None
    records, _errors = playbook_store.list()
    assert {r["session_date"] for r in records} == {D0, D1}  # no file for the refused date


def test_run_backscan_a_failing_date_is_classified_failed_and_the_walk_continues(tmp_path, env, monkeypatch):
    bar_store, universe_store, playbook_store = env
    _plant_three_firing_sessions(bar_store)

    from app.research import desk_playbook_compute as desk_playbook_compute_module

    real_compute = desk_playbook_compute_module.compute_playbook
    call_count = {"n": 0}

    def _boom_on_first(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("the bar store went away mid-walk")
        return real_compute(*args, **kwargs)

    monkeypatch.setattr(desk_playbook_compute_module, "compute_playbook", _boom_on_first)

    outcomes = run_backscan([D0, D1, D2], universe_store, bar_store, CONFIG, playbook_store)

    assert [o["outcome"] for o in outcomes] == ["failed", "recorded", "recorded"]
    assert "went away mid-walk" in outcomes[0]["detail"]


def test_run_backscan_should_abort_stops_before_the_next_date_starts(tmp_path, env):
    bar_store, universe_store, playbook_store = env
    _plant_three_firing_sessions(bar_store)

    calls = {"n": 0}

    def _abort_after_first():
        calls["n"] += 1
        return calls["n"] > 1

    outcomes = run_backscan(
        [D0, D1, D2], universe_store, bar_store, CONFIG, playbook_store, should_abort=_abort_after_first,
    )
    assert [o["outcome"] for o in outcomes] == ["recorded"]


# --- the manager: single-flight + cancel + terminal-state-only ledger (TC-5, TC-6, TC-10) ----------


def _wait_for_terminal(manager: DeskPlaybookBackscanComputeManager, timeout: float = 5.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        snap = manager.snapshot()
        if snap["status"] != "running":
            return snap
        time.sleep(0.01)
    raise AssertionError("back-scan compute never reached a terminal state")


def test_manager_snapshot_is_idle_before_any_job_has_ever_run():
    manager = DeskPlaybookBackscanComputeManager()
    assert manager.snapshot() == {
        "id": None,
        "status": "idle", "from": None, "to": None, "planned_total": 0, "completed": 0,
        "outcomes": {"reused": 0, "recorded": 0, "refused_non_session": 0, "failed": 0},
        "current_date": None, "error": None,
    }


def test_tc5_cancel_after_one_date_completes_logs_a_partial_row_and_the_next_plan_shows_the_split(
    tmp_path, env, monkeypatch
):
    bar_store, universe_store, playbook_store = env
    _plant_three_firing_sessions(bar_store)
    run_store = BackscanRunStore(tmp_path / "backscan_runs")

    # Pause INSIDE the FIRST date's own call, set cancel while it is in flight (it has already
    # "paid for its walk" per the module docstring, so it completes regardless), then release --
    # the walk observes the cancel at the boundary BEFORE the second date ever starts, landing
    # exactly 1 completed date.
    entered_first = threading.Event()
    release = threading.Event()
    from app.research import desk_playbook_compute as desk_playbook_compute_module

    real_run_and_record = desk_playbook_compute_module.run_playbook_and_record
    call_index = {"n": 0}

    def _pausing_run_and_record(*args, **kwargs):
        call_index["n"] += 1
        if call_index["n"] == 1:
            entered_first.set()
            release.wait(timeout=5)
        return real_run_and_record(*args, **kwargs)

    monkeypatch.setattr(desk_playbook_backscan, "run_playbook_and_record", _pausing_run_and_record)

    manager = DeskPlaybookBackscanComputeManager()
    started = manager.trigger(D0, D2, universe_store, bar_store, CONFIG, playbook_store, run_store)
    assert started["compute"]["id"] is not None
    assert entered_first.wait(timeout=5)
    manager.cancel()
    release.set()

    snap = _wait_for_terminal(manager)
    assert snap["status"] == "cancelled"
    assert snap["completed"] == 1
    # The job's own id reaches its terminal snapshot -- what the refresh chain's seventh step
    # matches on to know the scan it is watching is the one it started.
    assert snap["id"] == started["compute"]["id"]
    manager.join_all(timeout=5)

    rows, errors = run_store.list()
    assert errors == [] and len(rows) == 1
    assert rows[0]["status"] == "cancelled"
    assert rows[0]["outcomes"]["recorded"] == 1

    plan = plan_backscan(D0, D2, bar_store, _members(universe_store), CONFIG.config_fingerprint(), playbook_store)
    statuses = {d["session_date"]: d["status"] for d in plan["dates"]}
    assert statuses[D0] == "recorded_at_current_signature"
    assert statuses[D1] == "missing_at_current_signature"
    assert statuses[D2] == "missing_at_current_signature"


def test_tc6_re_triggering_after_a_partial_cancel_resumes_the_recorded_date_as_reused(tmp_path, env):
    bar_store, universe_store, playbook_store = env
    _plant_three_firing_sessions(bar_store)
    run_store = BackscanRunStore(tmp_path / "backscan_runs")

    # Simulate TC-5's cancel-after-one outcome directly via run_backscan (cheaper than re-driving
    # the manager's own threads a second time in the same test).
    run_backscan([D0], universe_store, bar_store, CONFIG, playbook_store)

    manager = DeskPlaybookBackscanComputeManager()
    manager.trigger(D0, D2, universe_store, bar_store, CONFIG, playbook_store, run_store)
    snap = _wait_for_terminal(manager)
    manager.join_all(timeout=5)

    assert snap["status"] == "done"
    assert snap["outcomes"]["reused"] == 1
    assert snap["outcomes"]["recorded"] == 2


def test_tc10_cancel_before_any_date_completes_leaves_no_ledger_row(tmp_path, env, monkeypatch):
    bar_store, universe_store, playbook_store = env
    _plant_three_firing_sessions(bar_store)
    run_store = BackscanRunStore(tmp_path / "backscan_runs")

    # Pause at the very ENTRY of run_backscan itself (before its loop's first should_abort()
    # check ever runs), so a cancel set while paused here is observed on the FIRST date boundary --
    # zero dates ever start.
    started = threading.Event()
    release = threading.Event()
    real_run_backscan = desk_playbook_backscan.run_backscan

    def _pausing_run_backscan(*args, **kwargs):
        started.set()
        release.wait(timeout=5)
        return real_run_backscan(*args, **kwargs)

    monkeypatch.setattr(desk_playbook_backscan, "run_backscan", _pausing_run_backscan)

    manager = DeskPlaybookBackscanComputeManager()
    manager.trigger(D0, D2, universe_store, bar_store, CONFIG, playbook_store, run_store)
    assert started.wait(timeout=5)
    manager.cancel()
    release.set()

    snap = _wait_for_terminal(manager)
    assert snap["status"] == "cancelled"
    assert snap["completed"] == 0
    manager.join_all(timeout=5)

    rows, errors = run_store.list()
    assert errors == [] and rows == []


def test_manager_single_flight_second_trigger_returns_the_same_job(tmp_path, env, monkeypatch):
    bar_store, universe_store, playbook_store = env
    _plant_three_firing_sessions(bar_store)
    run_store = BackscanRunStore(tmp_path / "backscan_runs")

    started = threading.Event()
    release = threading.Event()
    from app.research import desk_playbook_compute as desk_playbook_compute_module

    real_run_and_record = desk_playbook_compute_module.run_playbook_and_record
    first_call = {"seen": False}

    def _blocking(*args, **kwargs):
        if not first_call["seen"]:
            first_call["seen"] = True
            started.set()
            release.wait(timeout=5)
        return real_run_and_record(*args, **kwargs)

    monkeypatch.setattr(desk_playbook_backscan, "run_playbook_and_record", _blocking)
    manager = DeskPlaybookBackscanComputeManager()
    first = manager.trigger(D0, D2, universe_store, bar_store, CONFIG, playbook_store, run_store)
    assert first["started"] is True
    assert started.wait(timeout=5)

    second = manager.trigger(D0, D2, universe_store, bar_store, CONFIG, playbook_store, run_store)
    assert second["started"] is False
    assert second["compute"]["from"] == first["compute"]["from"] == D0

    release.set()
    snap = _wait_for_terminal(manager)
    assert snap["status"] == "done"
    manager.join_all(timeout=5)


# --- the routes ---------------------------------------------------------------------------------------


@pytest.fixture
def route_ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR", str(tmp_path / "playbook_runs"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR", str(tmp_path / "playbook_backscan_runs"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    fresh_manager = DeskPlaybookBackscanComputeManager()
    app.dependency_overrides[get_desk_playbook_backscan_manager] = lambda: fresh_manager
    with TestClient(app) as client:
        yield client, fresh_manager, tmp_path
    fresh_manager.join_all(timeout=5.0)
    set_registry(None)
    app.dependency_overrides.pop(get_desk_playbook_backscan_manager, None)
    store.close()


def test_routes_honest_idle_and_idle_cancel_409(route_ctx):
    client, _manager, _tmp = route_ctx
    idle = client.get("/research/desk/playbook/backscan/compute")
    assert idle.status_code == 200
    assert idle.json()["status"] == "idle"

    idle_cancel = client.post("/research/desk/playbook/backscan/compute/cancel")
    assert idle_cancel.status_code == 409

    runs = client.get("/research/desk/playbook/backscan/runs")
    assert runs.status_code == 200
    assert runs.json() == {"runs": [], "latest": None, "integrity_errors": []}


def test_tc11_plan_trigger_and_runs_end_to_end_through_the_routes(route_ctx):
    client, manager, tmp = route_ctx
    bar_store = BarStore(tmp / "bars")
    _plant_three_firing_sessions(bar_store)
    _register_universe(tmp, ["AAA"])

    plan = client.get("/research/desk/playbook/backscan/plan", params={"from": D0, "to": D2})
    assert plan.status_code == 200
    assert plan.json()["missing"] == 3

    trigger = client.post("/research/desk/playbook/backscan/compute", json={"from_day": D0, "to_day": D2})
    assert trigger.status_code == 200
    assert trigger.json()["started"] is True

    snap = _wait_for_terminal(manager)
    assert snap["status"] == "done"
    assert snap["outcomes"]["recorded"] == 3

    runs = client.get("/research/desk/playbook/backscan/runs").json()
    assert len(runs["runs"]) == 1
    row = runs["runs"][0]
    assert row["status"] == "done"
    assert row["outcomes"] == {"reused": 0, "recorded": 3, "refused_non_session": 0, "failed": 0}
    assert runs["latest"]["run_id"] == row["run_id"]

    plan_after = client.get("/research/desk/playbook/backscan/plan", params={"from": D0, "to": D2})
    assert plan_after.json()["missing"] == 0


def test_route_plan_missing_universe_snapshot_is_honestly_empty(route_ctx):
    client, _manager, _tmp = route_ctx
    response = client.get("/research/desk/playbook/backscan/plan", params={"from": D0, "to": D2})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert all(d["status"] == "missing_at_current_signature" for d in body["dates"])


# --- resolve_desk_playbook_backscan_log_dir --------------------------------------------------------


def test_resolve_desk_playbook_backscan_log_dir_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR", str(tmp_path / "custom"))
    assert resolve_desk_playbook_backscan_log_dir(str(tmp_path / "universe")) == str(tmp_path / "custom")


def test_resolve_desk_playbook_backscan_log_dir_defaults_to_a_universe_sibling(monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR", raising=False)
    result = resolve_desk_playbook_backscan_log_dir("/x/y/universe")
    assert result == "/x/y/playbook_backscan_runs"


# --- TC-13: the positive scoping guard ----------------------------------------------------------------
# goal-playbook-iter-12 (J-11 passenger, TC-15): extended from four to five vars --
# TAPEOLOGY_BAR_INDEX_DB joins the other four. The three tests below are widened so "all env vars
# unset"/"all env vars properly scoped" keep meaning what they say; a NEW dedicated negative
# counter-test (below) isolates the fifth var alone, and a source-scan test pins that this guard
# still has no caller under desk_routes.py (never wired into a live route).

_ALL_SCOPED_ENV_VARS = (
    "TAPEOLOGY_DESK_PLAYBOOK_DIR",
    "TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR",
    "TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR",
    "TAPEOLOGY_DESK_UNIVERSE_DIR",
    "TAPEOLOGY_BAR_INDEX_DB",
)


def _set_all_scoped(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR", str(tmp_path / "playbook_runs"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR", str(tmp_path / "playbook_backscan_runs"))
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_BAR_INDEX_DB", str(tmp_path / "bar_index.db"))


def test_tc13_assert_scoped_raises_when_all_five_env_vars_are_unset(tmp_path, monkeypatch):
    for name in _ALL_SCOPED_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(PlaybookNotScopedError):
        _assert_scoped(tmp_path)


def test_tc13_assert_scoped_raises_when_a_var_points_at_a_dot_data_store(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR", str(tmp_path / "playbook_runs"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR", str(tmp_path / "playbook_backscan_runs"))
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", "/some/repo/apps/backend/.data/desk_universe")
    monkeypatch.setenv("TAPEOLOGY_BAR_INDEX_DB", str(tmp_path / "bar_index.db"))

    with pytest.raises(PlaybookNotScopedError):
        _assert_scoped(tmp_path)


def test_tc13_assert_scoped_passes_when_all_five_are_properly_scoped(tmp_path, monkeypatch):
    _set_all_scoped(tmp_path, monkeypatch)

    _assert_scoped(tmp_path)  # does not raise


def test_tc15_assert_scoped_raises_when_only_the_fifth_var_is_unset_and_names_it(tmp_path, monkeypatch):
    """TC-15's own negative counter-test: the other four properly scoped, ONLY
    ``TAPEOLOGY_BAR_INDEX_DB`` unset -- still refused, and the raised message names that exact var
    (not a generic "something is wrong")."""
    _set_all_scoped(tmp_path, monkeypatch)
    monkeypatch.delenv("TAPEOLOGY_BAR_INDEX_DB", raising=False)

    with pytest.raises(PlaybookNotScopedError) as excinfo:
        _assert_scoped(tmp_path)
    assert "TAPEOLOGY_BAR_INDEX_DB" in str(excinfo.value)
    # And it is the ONLY problem named -- the other four were genuinely fine.
    for name in _ALL_SCOPED_ENV_VARS[:-1]:
        assert f"{name} is unset" not in str(excinfo.value)
        assert f"{name}=" not in str(excinfo.value)


def test_tc15_assert_scoped_has_no_caller_under_desk_routes():
    """TC-15: a source-scan confirms ``_assert_scoped`` is still never wired into a live HTTP route
    -- it stays a test/browser-QA-rig-only positive guard, exactly as its own docstring claims."""
    import pathlib

    import app.research.desk_routes as desk_routes_module

    routes_source = pathlib.Path(desk_routes_module.__file__).read_text()
    assert "_assert_scoped" not in routes_source, (
        "desk_routes.py must never call _assert_scoped -- an operator's REAL compute legitimately "
        "runs with none of the five scoping env vars set, and wiring the guard into a route would "
        "wrongly refuse every genuine production compute"
    )
