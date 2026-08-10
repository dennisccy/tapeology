"""``desk_playbook_compute.py`` (Era B2, J-02) — ``run_playbook_and_record``'s reuse/cancel/
session-refusal/ledger-write discipline, ``DeskPlaybookComputeManager``'s single-flight + cancel
mechanics, the CLI warmer, and the compute/runs routes end to end. Mirrors the manager/route/CLI
sections of ``test_desk_forward.py`` in shape; ``test_desk_playbook_log.py`` covers the ledger
store module in isolation.

Reuses ``test_desk_playbook``'s own bar/universe fixture helpers (the ``from test_copy_discipline
import find_violations`` cross-file-import precedent already established there) rather than
duplicating them."""

from __future__ import annotations

import sys
import threading
import time

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.research import desk_playbook_compute
from app.research.bars import BarStore
from app.research.desk_playbook import (
    PlaybookSessionRefused,
    PlaybookStore,
    compute_playbook_input_signature,
    resolve_desk_playbook_dir,
)
from app.research.desk_playbook_compute import DeskPlaybookComputeManager, run_playbook_and_record
from app.research.desk_playbook_log import PlaybookRunStore, resolve_desk_playbook_log_dir
from app.research.desk_routes import get_desk_playbook_compute_manager
from app.research.desk_sessions import non_session_refusal, session_evidence
from app.research.desk_universe import UniverseStore
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore
from test_desk_playbook import (
    E_OPEN,
    SESSION_DATE,
    _bar,
    _plant,
    _plant_baseline_sessions,
    _plant_firing_session,
    _register_universe,
)


@pytest.fixture
def env(tmp_path):
    bar_store = BarStore(tmp_path / "bars")
    universe_store = _register_universe(tmp_path, ["AAA"])
    playbook_store = PlaybookStore(tmp_path / "playbook")
    return bar_store, universe_store, playbook_store


def _wait_for_terminal(manager: DeskPlaybookComputeManager, timeout: float = 5.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        snap = manager.snapshot()
        if snap["status"] not in ("running", "cancelling"):
            return snap
        time.sleep(0.01)
    raise AssertionError("playbook compute never reached a terminal state")


# --- run_playbook_and_record: reuse / cancel / session refusal / ledger (TC-12, TC-13) -----------


def test_a_fresh_run_records_and_logs_exactly_one_row(tmp_path, env):
    bar_store, universe_store, playbook_store = env
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")
    run_store = PlaybookRunStore(tmp_path / "playbook_runs")

    record, reused = run_playbook_and_record(
        universe_store, bar_store, CONFIG, playbook_store, SESSION_DATE, playbook_run_store=run_store,
    )

    assert reused is False and len(record["signals"]) == 1
    rows, errors = run_store.list()
    assert errors == [] and len(rows) == 1
    assert rows[0]["outcome"] == "recorded"
    assert rows[0]["playbook_id"] == record["id"]
    assert rows[0]["playbook_input_signature"] == record["playbook_input_signature"]
    assert rows[0]["signals_recorded"] == 1
    assert rows[0]["error"] is None


def test_a_reused_run_records_a_second_row_carrying_the_existing_records_counts(tmp_path, env):
    bar_store, universe_store, playbook_store = env
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")
    run_store = PlaybookRunStore(tmp_path / "playbook_runs")
    first, _ = run_playbook_and_record(
        universe_store, bar_store, CONFIG, playbook_store, SESSION_DATE, playbook_run_store=run_store,
    )

    second, reused = run_playbook_and_record(
        universe_store, bar_store, CONFIG, playbook_store, SESSION_DATE, playbook_run_store=run_store,
    )

    assert reused is True and second["id"] == first["id"]
    rows = run_store.list_for_session(SESSION_DATE)
    assert len(rows) == 2  # a reuse is its own real attempt, never folded into the first
    assert rows[1]["outcome"] == "reused"
    assert rows[1]["playbook_id"] == first["id"]
    assert rows[1]["signals_recorded"] == rows[0]["signals_recorded"] == 1


def test_a_cancelled_walk_leaves_no_store_file_and_no_ledger_row(tmp_path, env):
    bar_store, universe_store, playbook_store = env
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")
    run_store = PlaybookRunStore(tmp_path / "playbook_runs")

    record, _reused = run_playbook_and_record(
        universe_store, bar_store, CONFIG, playbook_store, SESSION_DATE,
        should_abort=lambda: True, playbook_run_store=run_store,
    )

    assert record is None
    assert playbook_store.list() == ([], [])  # a partial walk is never recorded
    assert run_store.list() == ([], [])  # ...and never logged either (unlike the forward ledger)


def test_a_non_session_date_is_refused_and_logs_a_refused_row(tmp_path, env):
    bar_store, universe_store, playbook_store = env
    for day in ("2026-06-19", "2026-06-20", "2026-06-22"):
        from datetime import datetime
        epoch = datetime.fromisoformat(f"{day}T00:00:00+00:00").timestamp()
        _plant(bar_store, "AAA", "1d", [_bar("AAA", "1d", epoch, 100.0, 101.0, 99.0, 100.0)])
    run_store = PlaybookRunStore(tmp_path / "playbook_runs")

    with pytest.raises(PlaybookSessionRefused) as exc_info:
        run_playbook_and_record(
            universe_store, bar_store, CONFIG, playbook_store, "2026-06-21",
            playbook_run_store=run_store,
        )

    evidence = session_evidence(bar_store, ["AAA"])
    assert str(exc_info.value) == non_session_refusal("2026-06-21", evidence)
    assert playbook_store.list() == ([], [])
    rows, _errors = run_store.list()
    assert len(rows) == 1
    assert rows[0]["outcome"] == "refused_non_session"
    assert rows[0]["playbook_id"] is None


def test_a_failing_walk_records_a_failed_row_and_re_raises(tmp_path, env, monkeypatch):
    bar_store, universe_store, playbook_store = env
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")
    run_store = PlaybookRunStore(tmp_path / "playbook_runs")

    def _boom(*_args, **_kwargs):
        raise RuntimeError("the bar store went away mid-walk")

    monkeypatch.setattr(desk_playbook_compute, "compute_playbook", _boom)

    with pytest.raises(RuntimeError, match="went away mid-walk"):
        run_playbook_and_record(
            universe_store, bar_store, CONFIG, playbook_store, SESSION_DATE,
            playbook_run_store=run_store,
        )

    rows, _errors = run_store.list()
    assert len(rows) == 1
    assert rows[0]["outcome"] == "failed"
    assert rows[0]["error"] == "the bar store went away mid-walk"
    assert rows[0]["playbook_id"] is None


# --- the manager: single-flight + cancel (TC-13, TC-15) --------------------------------------------


def test_manager_single_flight_second_trigger_returns_the_same_job(env, monkeypatch):
    bar_store, universe_store, playbook_store = env
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")

    started = threading.Event()
    release = threading.Event()

    def _blocking_compute(universe_store_arg, bar_store_arg, fp, session_date_arg, *, progress=None, should_abort=None):
        started.set()
        release.wait(timeout=5)
        from app.research.desk_playbook import compute_playbook as _real
        return _real(universe_store_arg, bar_store_arg, fp, session_date_arg)

    monkeypatch.setattr(desk_playbook_compute, "compute_playbook", _blocking_compute)
    manager = DeskPlaybookComputeManager()
    first = manager.trigger(SESSION_DATE, universe_store, bar_store, CONFIG, playbook_store)
    assert first["started"] is True
    assert started.wait(timeout=5)

    second = manager.trigger(SESSION_DATE, universe_store, bar_store, CONFIG, playbook_store)
    assert second["started"] is False
    assert second["compute"]["session_date"] == first["compute"]["session_date"] == SESSION_DATE

    release.set()
    snap = _wait_for_terminal(manager)
    assert snap["status"] == "done"
    assert snap["signals_total"] == 1  # one universe member
    manager.join_all(timeout=5)


def test_manager_cancel_mid_walk_records_nothing_and_reverts_to_idle(env, monkeypatch):
    bar_store, universe_store, playbook_store = env
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")

    entered = threading.Event()
    release = threading.Event()
    from app.research.desk_playbook import compute_playbook as real_compute

    def _pausing_compute(universe_store_arg, bar_store_arg, fp, session_date_arg, *, progress=None, should_abort=None):
        entered.set()
        release.wait(timeout=5)
        return real_compute(
            universe_store_arg, bar_store_arg, fp, session_date_arg,
            progress=progress, should_abort=should_abort,
        )

    monkeypatch.setattr(desk_playbook_compute, "compute_playbook", _pausing_compute)
    manager = DeskPlaybookComputeManager()
    manager.trigger(SESSION_DATE, universe_store, bar_store, CONFIG, playbook_store)
    assert entered.wait(timeout=5)

    manager.cancel()
    cancelling_snap = manager.snapshot()
    assert cancelling_snap["status"] == "cancelling"

    release.set()
    snap = _wait_for_terminal(manager)
    # a completed cancel leaves NO distinct terminal marker -- it reverts to the idle shape
    assert snap == {
        "status": "idle", "session_date": None, "signals_done": 0, "signals_total": 0, "error": None,
    }
    assert playbook_store.list() == ([], [])
    manager.join_all(timeout=5)


def test_manager_snapshot_is_idle_before_any_job_has_ever_run():
    manager = DeskPlaybookComputeManager()
    assert manager.snapshot() == {
        "status": "idle", "session_date": None, "signals_done": 0, "signals_total": 0, "error": None,
    }


# --- the routes --------------------------------------------------------------------------------------


@pytest.fixture
def route_ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR", str(tmp_path / "playbook_runs"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    fresh_manager = DeskPlaybookComputeManager()
    app.dependency_overrides[get_desk_playbook_compute_manager] = lambda: fresh_manager
    with TestClient(app) as client:
        yield client, fresh_manager, tmp_path
    fresh_manager.join_all(timeout=5.0)
    set_registry(None)
    app.dependency_overrides.pop(get_desk_playbook_compute_manager, None)
    store.close()


def test_routes_honest_idle_and_idle_cancel_409(route_ctx):
    client, _manager, _tmp = route_ctx
    idle = client.get("/research/desk/playbook/compute")
    assert idle.status_code == 200
    assert idle.json() == {
        "status": "idle", "session_date": None, "signals_done": 0, "signals_total": 0, "error": None,
    }

    idle_cancel = client.post("/research/desk/playbook/compute/cancel")
    assert idle_cancel.status_code == 409

    runs = client.get("/research/desk/playbook/runs")
    assert runs.status_code == 200
    assert runs.json() == {"runs": [], "latest": None, "integrity_errors": []}


def test_trigger_refuses_a_non_session_date_before_starting_a_job(route_ctx):
    client, manager, tmp = route_ctx
    bar_store = BarStore(tmp / "bars")
    for day in ("2026-06-19", "2026-06-20", "2026-06-22"):
        from datetime import datetime
        epoch = datetime.fromisoformat(f"{day}T00:00:00+00:00").timestamp()
        _plant(bar_store, "AAA", "1d", [_bar("AAA", "1d", epoch, 100.0, 101.0, 99.0, 100.0)])
    universe_store = UniverseStore(tmp / "universe")
    universe_store.record(
        members=["AAA"], raw_members={"AAA": "AAA"}, source_url="test", min_members=1, max_members=10,
    )

    response = client.post("/research/desk/playbook/compute", json={"session_date": "2026-06-21"})
    assert response.status_code == 422
    assert "not a recorded trading session" in response.json()["detail"]
    assert manager.snapshot()["status"] == "idle"  # no job was ever created

    runs = client.get("/research/desk/playbook/runs").json()
    assert runs == {"runs": [], "latest": None, "integrity_errors": []}  # -- and no ledger row


def test_route_compute_runs_to_done_and_the_runs_route_records_it(route_ctx):
    client, manager, tmp = route_ctx
    bar_store = BarStore(tmp / "bars")
    universe_store = UniverseStore(tmp / "universe")
    universe_store.record(
        members=["AAA"], raw_members={"AAA": "AAA"}, source_url="test", min_members=1, max_members=10,
    )
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")

    trigger = client.post("/research/desk/playbook/compute", json={"session_date": SESSION_DATE})
    assert trigger.status_code == 200
    body = trigger.json()
    assert body["started"] is True
    assert body["compute"]["signals_total"] == 1

    snap = _wait_for_terminal(manager)
    assert snap["status"] == "done"

    served = client.get("/research/desk/playbook", params={"date": SESSION_DATE})
    payload = served.json()
    assert payload["versions"] == 1
    record = payload["playbook"]
    assert len(record["signals"]) == 1
    assert record["signals"][0]["forward"] is not None

    runs = client.get("/research/desk/playbook/runs").json()
    assert len(runs["runs"]) == 1
    row = runs["runs"][0]
    assert row["outcome"] == "recorded"
    assert row["playbook_id"] == record["id"]
    assert runs["latest"]["run_id"] == row["run_id"]

    narrowed = client.get("/research/desk/playbook/runs", params={"session_date": SESSION_DATE}).json()
    assert [r["run_id"] for r in narrowed["runs"]] == [row["run_id"]]
    other = client.get("/research/desk/playbook/runs", params={"session_date": "2099-01-01"}).json()
    assert other == {"runs": [], "latest": None, "integrity_errors": []}


def test_a_second_trigger_while_running_is_refused_single_flight(route_ctx, monkeypatch):
    client, manager, tmp = route_ctx
    bar_store = BarStore(tmp / "bars")
    universe_store = UniverseStore(tmp / "universe")
    universe_store.record(
        members=["AAA"], raw_members={"AAA": "AAA"}, source_url="test", min_members=1, max_members=10,
    )
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")

    started = threading.Event()
    release = threading.Event()

    def _blocking_compute(universe_store_arg, bar_store_arg, fp, session_date_arg, *, progress=None, should_abort=None):
        started.set()
        release.wait(timeout=5)
        from app.research.desk_playbook import compute_playbook as _real
        return _real(universe_store_arg, bar_store_arg, fp, session_date_arg)

    monkeypatch.setattr(desk_playbook_compute, "compute_playbook", _blocking_compute)

    first = client.post("/research/desk/playbook/compute", json={"session_date": SESSION_DATE})
    assert first.json()["started"] is True
    assert started.wait(timeout=5)

    second = client.post("/research/desk/playbook/compute", json={"session_date": SESSION_DATE})
    assert second.json()["started"] is False

    cancel = client.post("/research/desk/playbook/compute/cancel")
    assert cancel.status_code == 200

    release.set()
    _wait_for_terminal(manager)
    manager.join_all(timeout=5)


# --- the CLI (TC-14) ---------------------------------------------------------------------------------


def test_cli_records_a_real_signature_matched_record_and_a_non_session_date_exits_1(tmp_path, monkeypatch):
    """The CLI drives the SAME shared ``run_playbook_and_record`` entry point the API route's
    background worker calls (this module's own docstring) -- there is no second code path for it
    to diverge onto. This proves the CLI-triggered record is genuinely real (right shape, right
    signature) and that its non-session refusal exits 1, naming the date."""
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR", str(tmp_path / "playbook_runs"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))

    bar_store = BarStore(tmp_path / "bars")
    universe_store = UniverseStore(tmp_path / "universe")
    universe_store.record(
        members=["AAA"], raw_members={"AAA": "AAA"}, source_url="test", min_members=1, max_members=10,
    )
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")
    expected_signature = compute_playbook_input_signature(bar_store, ["AAA"], CONFIG.config_fingerprint())

    monkeypatch.setattr(sys, "argv", ["desk_playbook_compute", "--session-date", SESSION_DATE])
    assert desk_playbook_compute.main() == 0

    playbook_store = PlaybookStore(resolve_desk_playbook_dir(str(tmp_path / "universe")))
    records, errors = playbook_store.list()
    assert errors == [] and len(records) == 1
    assert records[0]["playbook_input_signature"] == expected_signature
    assert records[0]["payload_version"] == 2
    assert len(records[0]["signals"]) == 1
    assert records[0]["signals"][0]["forward"] is not None
    run_store = PlaybookRunStore(resolve_desk_playbook_log_dir(str(tmp_path / "universe")))
    rows, _errors = run_store.list()
    assert len(rows) == 1 and rows[0]["outcome"] == "recorded"

    # A non-session date: exits 1, prints the refusal sentence, records nothing new.
    for day in ("2026-06-19", "2026-06-20", "2026-06-22"):
        from datetime import datetime
        epoch = datetime.fromisoformat(f"{day}T00:00:00+00:00").timestamp()
        _plant(bar_store, "AAA", "1d", [_bar("AAA", "1d", epoch, 100.0, 101.0, 99.0, 100.0)])
    monkeypatch.setattr(sys, "argv", ["desk_playbook_compute", "--session-date", "2026-06-21"])
    assert desk_playbook_compute.main() == 1
    records_after, _errors = playbook_store.list()
    assert len(records_after) == 1  # unchanged -- the refusal recorded nothing
