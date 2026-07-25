"""``desk_screen_compute.py`` (Era B "The Desk", J-03) — manager mechanics (single-flight, cancel,
atomic progress), the append-only reuse guarantee (TC-4), the four HTTP routes, and the CLI
warmer's ``main()`` (TC-18).

Manager-mechanics tests substitute a FAKE ``compute_screen`` (monkeypatched onto THIS module's own
imported name — the ``test_desk_topup_compute.py``/``test_edge_report_compute.py`` fake-swap
precedent) for deterministic, threading-free control over timing. The append-only reuse guarantee
and the routes are proven end to end against the REAL ``compute_screen`` (real fixture universe,
real AAPL bars). CLI tests mirror ``test_edge_report_compute.py``'s own CLI pattern (``sys.argv``
+ scoped env vars, never the ambient real ``.data/`` tree).
"""

from __future__ import annotations

import json
import shutil
import sys
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager as ws_manager
from app.providers.adapters.base import RawBar
from app.research import desk_screen_compute
from app.research.bar_index import BarIndex
from app.research.bars import BarStore
from app.research.datasets import DatasetStore
from app.research.desk_routes import get_desk_screen_compute_manager
from app.research.desk_screen import ScreenStore
from app.research.desk_screen_compute import DeskScreenComputeManager, run_screen_and_record
from app.research.desk_universe import UniverseStore
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore

FIXTURE_UNIVERSE_DIR = Path(__file__).parent / "fixtures" / "universe"
REGISTERED_SNAPSHOT_PATH = FIXTURE_UNIVERSE_DIR / "universe-2026-07-25-817cc184bbb3.json"
FIXTURE_YAHOO_DIR = Path(__file__).parent / "fixtures" / "yahoo"
AAPL_DAILY_FIXTURE = "AAPL_1d_20260101_20260626.json"

SCREEN_DATE = "2026-06-22"
SMALL_MEMBERS = ["AAA", "BBB"]


def _load_yahoo_fixture(name: str) -> dict:
    return json.loads((FIXTURE_YAHOO_DIR / name).read_text())


def _seed_yahoo_fixture(bar_store: BarStore, bar_index: BarIndex, fixture: dict) -> None:
    bars = [
        RawBar(
            fixture["symbol"], fixture["timeframe"], b["epoch"],
            b["open"], b["high"], b["low"], b["close"], b["volume"],
        )
        for b in fixture["bars"]
    ]
    meta = bar_store.record(
        symbol=fixture["symbol"], timeframe=fixture["timeframe"],
        window_start_utc=fixture["start"], window_end_utc=fixture["end"],
        feed="yahoo", bars=bars,
    )
    bar_index.insert(meta)


def _register_fixture_universe(universe_dir: Path) -> UniverseStore:
    universe_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REGISTERED_SNAPSHOT_PATH, universe_dir / REGISTERED_SNAPSHOT_PATH.name)
    return UniverseStore(universe_dir)


def _register_small_universe(universe_dir: Path, members: list[str]) -> UniverseStore:
    store = UniverseStore(universe_dir)
    store.record(
        members=sorted(members), raw_members={m: m for m in members},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    return store


def _wait_for_terminal(mgr: DeskScreenComputeManager, timeout: float = 5.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        snap = mgr.snapshot()
        if snap is not None and snap["state"] != "running":
            return snap
        time.sleep(0.01)
    raise AssertionError("desk screen compute job never reached a terminal state")


@pytest.fixture
def manager_env(tmp_path):
    """Manager-level tests: no ``TestClient``/registry needed -- every dependency is passed
    explicitly to ``manager.trigger(...)`` (the ``EdgeReportComputeManager``/
    ``DeskTopupComputeManager`` per-call-injection precedent)."""
    universe_store = _register_small_universe(tmp_path / "universe", SMALL_MEMBERS)
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "index.db"))
    dataset_store = DatasetStore(tmp_path / "datasets")
    screen_store = ScreenStore(tmp_path / "screen")
    return universe_store, bar_store, bar_index, dataset_store, screen_store


# ==================================================================================================
# Manager mechanics -- a FAKE `compute_screen` gives deterministic, threading-free control.
# ==================================================================================================


def test_no_job_has_ever_run_snapshot_is_none():
    assert DeskScreenComputeManager().snapshot() is None


def test_trigger_members_total_is_known_synchronously_before_any_background_work(manager_env, monkeypatch):
    """``members_total`` (the fixture universe's 2 members) is correct in the response returned
    from ``trigger()`` itself -- known BEFORE the background thread even starts (the
    ``DeskTopupComputeManager`` ``pairs_total`` precedent)."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env

    started = threading.Event()
    release = threading.Event()

    def fake_compute_screen(*_args, **_kwargs):
        started.set()
        release.wait(timeout=5)
        return {
            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z",
            "universe_snapshot_id": "x", "config_fingerprint": "y", "bar_store_signature": "z",
            "rows": [], "skipped": [],
        }

    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)

    mgr = DeskScreenComputeManager()
    result = mgr.trigger(
        SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store,
    )
    assert result["started"] is True
    assert result["compute"]["progress"]["members_total"] == len(SMALL_MEMBERS)
    assert result["compute"]["screen_date"] == SCREEN_DATE
    assert started.wait(timeout=5)
    release.set()
    _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)


def test_trigger_with_no_universe_snapshot_is_an_honest_empty_job_that_completes(tmp_path):
    universe_store = UniverseStore(tmp_path / "universe")
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "index.db"))
    dataset_store = DatasetStore(tmp_path / "datasets")
    screen_store = ScreenStore(tmp_path / "screen")

    mgr = DeskScreenComputeManager()
    result = mgr.trigger(
        SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store,
    )
    assert result["started"] is True
    assert result["compute"]["progress"]["members_total"] == 0

    snap = _wait_for_terminal(mgr)
    assert snap["state"] == "done"
    assert snap["progress"]["members_done"] == 0
    mgr.join_all(timeout=5)

    records, errors = screen_store.list()
    assert errors == [] and len(records) == 1
    assert records[0]["universe_snapshot_id"] is None
    assert records[0]["rows"] == [] and records[0]["skipped"] == []


def test_second_trigger_while_running_returns_the_same_job_started_false(manager_env, monkeypatch):
    """TC-7: single-flight."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
    started = threading.Event()
    release = threading.Event()

    def fake_compute_screen(*_args, **_kwargs):
        started.set()
        release.wait(timeout=5)
        return {
            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z",
            "universe_snapshot_id": "x", "config_fingerprint": "y", "bar_store_signature": "z",
            "rows": [], "skipped": [],
        }

    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)

    mgr = DeskScreenComputeManager()
    first = mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
    assert started.wait(timeout=5)

    second = mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
    assert second["started"] is False
    assert second["compute"]["id"] == first["compute"]["id"]

    release.set()
    _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)


def test_trigger_after_a_terminal_job_starts_a_genuinely_new_job(manager_env, monkeypatch):
    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
    monkeypatch.setattr(
        desk_screen_compute, "compute_screen",
        lambda *a, **k: {
            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
            "config_fingerprint": "y", "bar_store_signature": "z", "rows": [], "skipped": [],
        },
    )

    mgr = DeskScreenComputeManager()
    first = mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
    _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)

    second = mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
    assert second["started"] is True
    assert second["compute"]["id"] != first["compute"]["id"]
    _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)


def test_a_cancellation_signal_resolves_state_cancelled_with_partial_progress_and_nothing_recorded(
    manager_env, monkeypatch,
):
    """TC-8: cancel mid-flight -- state transitions to "cancelled" with fewer than members_total
    processed, and (append-only) the partial walk is NEVER persisted as a screen snapshot."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
    started = threading.Event()
    release = threading.Event()
    calls: list[str] = []

    def fake_compute_screen(_us, _bs, _bi, _ds, _cfg, _sd, *, progress=None, should_abort=None):
        for symbol in SMALL_MEMBERS:
            calls.append(symbol)
            if len(calls) == 1:
                started.set()
                release.wait(timeout=5)
            if should_abort is not None and should_abort():
                break
            if progress is not None:
                progress({"symbol": symbol})
        return {
            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
            "config_fingerprint": "y", "bar_store_signature": "z", "rows": [], "skipped": [],
        }

    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)

    mgr = DeskScreenComputeManager()
    mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
    assert started.wait(timeout=5)
    mgr.cancel()
    release.set()

    snap = _wait_for_terminal(mgr)
    assert snap["state"] == "cancelled"
    assert snap["error"] is None
    assert snap["progress"]["members_done"] < snap["progress"]["members_total"]
    mgr.join_all(timeout=5)

    records, _errors = screen_store.list()
    assert records == [], "a cancelled (partial) walk must never be persisted"


def test_an_unexpected_crash_resolves_state_failed(manager_env, monkeypatch):
    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env

    def fake_compute_screen(*_args, **_kwargs):
        raise RuntimeError("synthetic catastrophic failure")

    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)

    mgr = DeskScreenComputeManager()
    mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
    snap = _wait_for_terminal(mgr)

    assert snap["state"] == "failed"
    assert snap["error"] == "synthetic catastrophic failure"
    mgr.join_all(timeout=5)
    records, _errors = screen_store.list()
    assert records == []


def test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_silent_overwrite(
    manager_env, monkeypatch,
):
    """The job-level view of ``ScreenStore.record``'s integrity refusal: a re-trigger whose 5-pin
    key lands on an already-corrupted file resolves ``"failed"`` with the explicit integrity error
    -- never a silent overwrite, and never a fabricated ``"done"``."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
    monkeypatch.setattr(
        desk_screen_compute, "compute_screen",
        lambda *a, **k: {
            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
            "config_fingerprint": "y", "bar_store_signature": "z", "rows": [], "skipped": [],
        },
    )

    mgr = DeskScreenComputeManager()
    mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
    assert _wait_for_terminal(mgr)["state"] == "done"
    mgr.join_all(timeout=5)

    path = next(Path(screen_store.root).glob("*.json"))
    data = json.loads(path.read_text())
    data["record"]["meta"]["rows"] = [{"symbol": "AAPL", "band_class": "TAMPERED"}]
    path.write_text(json.dumps(data))
    tampered_bytes = path.read_bytes()

    mgr2 = DeskScreenComputeManager()
    mgr2.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
    snap = _wait_for_terminal(mgr2)
    mgr2.join_all(timeout=5)

    assert snap["state"] == "failed"
    assert "integrity" in snap["error"]
    assert path.read_bytes() == tampered_bytes
    records, errors = screen_store.list()
    assert records == [] and len(errors) == 1


def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_reference(manager_env, monkeypatch):
    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
    monkeypatch.setattr(
        desk_screen_compute, "compute_screen",
        lambda *a, **k: {
            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
            "config_fingerprint": "y", "bar_store_signature": "z", "rows": [], "skipped": [],
        },
    )

    mgr = DeskScreenComputeManager()
    mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
    snap = _wait_for_terminal(mgr)
    snap["progress"]["current"] = "POISONED"

    fresh = mgr.snapshot()
    assert fresh["progress"]["current"] != "POISONED"
    mgr.join_all(timeout=5)


# ==================================================================================================
# Append-only reuse (TC-4) + cancel-returns-None -- against the REAL compute_screen.
# ==================================================================================================


@pytest.fixture
def real_ctx(tmp_path):
    universe_store = _register_fixture_universe(tmp_path / "universe")
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "index.db"))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    dataset_store = DatasetStore(tmp_path / "datasets")
    screen_store = ScreenStore(tmp_path / "screen")
    return universe_store, bar_store, bar_index, dataset_store, screen_store


def test_first_run_screen_and_record_persists_a_new_snapshot(real_ctx):
    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
    recorded = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
    )
    assert recorded is not None
    assert any(r["symbol"] == "AAPL" for r in recorded["rows"])
    records, errors = screen_store.list()
    assert errors == [] and len(records) == 1 and records[0]["id"] == recorded["id"]


def test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file(real_ctx, tmp_path):
    """TC-4: the manager/store returns the EXISTING snapshot (same id) rather than writing a
    second file."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
    first = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
    )
    second = run_screen_and_record(
        UniverseStore(universe_store.root), BarStore(bar_store.root), BarIndex(bar_index.db_path),
        DatasetStore(tmp_path / "datasets"), CONFIG, screen_store, SCREEN_DATE,
    )
    assert second["id"] == first["id"]
    records, errors = screen_store.list()
    assert errors == [] and len(records) == 1  # no second file


def test_cancel_before_the_walk_starts_returns_none_and_records_nothing(real_ctx):
    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
    result = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
        should_abort=lambda: True,
    )
    assert result is None
    records, _errors = screen_store.list()
    assert records == []


# ==================================================================================================
# Routes -- honest-empty (TC-5), ?date= (TC-6), 422 on missing screen_date (TC-9), GET-never-
# computes, single-flight/cancel through HTTP, idle-cancel 409.
# ==================================================================================================


@pytest.fixture
def route_ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_DIR", str(tmp_path / "screen"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    fresh_manager = DeskScreenComputeManager()
    app.dependency_overrides[get_desk_screen_compute_manager] = lambda: fresh_manager
    with TestClient(app) as client:
        yield client, fresh_manager, tmp_path
    fresh_manager.join_all(timeout=5.0)
    for ticker in list(ws_manager._engines.keys()):
        ws_manager.stop(ticker)
    set_registry(None)
    app.dependency_overrides.pop(get_market_adapter, None)
    app.dependency_overrides.pop(get_desk_screen_compute_manager, None)
    store.close()


def test_get_screen_before_any_compute_is_an_honest_empty_200(route_ctx):
    """TC-5."""
    client, _mgr, _tmp_path = route_ctx
    r = client.get("/research/desk/screen")
    assert r.status_code == 200
    assert r.json() == {"screens": [], "latest": None, "integrity_errors": []}


def test_get_screen_with_date_and_no_snapshot_ever_recorded_is_an_honest_null(route_ctx):
    client, _mgr, _tmp_path = route_ctx
    r = client.get("/research/desk/screen", params={"date": "2026-06-22"})
    assert r.status_code == 200
    assert r.json() == {"screen": None}


def test_get_screen_compute_before_any_trigger_is_an_honest_null_and_starts_nothing(route_ctx):
    client, fresh_manager, _tmp_path = route_ctx
    r = client.get("/research/desk/screen/compute")
    assert r.status_code == 200
    assert r.json() is None
    assert fresh_manager.snapshot() is None


def test_post_trigger_missing_screen_date_is_422(route_ctx):
    """TC-9: the endpoint never defaults to the current wall-clock date."""
    client, _mgr, _tmp_path = route_ctx
    r = client.post("/research/desk/screen/compute", json={})
    assert r.status_code == 422


def test_post_trigger_runs_to_completion_and_get_polls_the_same_snapshot(route_ctx):
    client, _mgr, tmp_path = route_ctx
    UniverseStore(tmp_path / "universe").record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )

    r = client.post("/research/desk/screen/compute", json={"screen_date": SCREEN_DATE})
    assert r.status_code == 200
    body = r.json()
    assert body["started"] is True
    assert body["compute"]["screen_date"] == SCREEN_DATE
    assert body["compute"]["progress"]["members_total"] == 1

    deadline = time.time() + 5
    snap = None
    while time.time() < deadline:
        snap = client.get("/research/desk/screen/compute").json()
        if snap is not None and snap["state"] != "running":
            break
        time.sleep(0.02)
    assert snap["state"] == "done"
    assert snap["progress"]["members_done"] == 1

    # The GET (no params) list is meta-only -- never the full rows/skipped arrays.
    listed = client.get("/research/desk/screen").json()
    assert len(listed["screens"]) == 1
    assert "rows" not in listed["screens"][0] and "skipped" not in listed["screens"][0]
    assert listed["screens"][0]["counts"] == {"rows": 0, "skipped": 1}  # AAA has no bars -> skipped
    assert listed["latest"] is not None
    assert "rows" in listed["latest"] and "skipped" in listed["latest"]

    # ?date= serves the exact persisted snapshot verbatim.
    dated = client.get("/research/desk/screen", params={"date": SCREEN_DATE}).json()
    assert dated["screen"] == listed["latest"]


def test_cancel_while_idle_is_409(route_ctx):
    client, _mgr, _tmp_path = route_ctx
    r = client.post("/research/desk/screen/compute/cancel")
    assert r.status_code == 409


def test_cancel_while_running_succeeds_and_a_subsequent_cancel_is_409(route_ctx, monkeypatch):
    client, fresh_manager, tmp_path = route_ctx
    UniverseStore(tmp_path / "universe").record(
        members=sorted(SMALL_MEMBERS), raw_members={m: m for m in SMALL_MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    started = threading.Event()
    release = threading.Event()

    def fake_compute_screen(_us, _bs, _bi, _ds, _cfg, _sd, *, progress=None, should_abort=None):
        started.set()
        release.wait(timeout=5)
        return {
            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
            "config_fingerprint": "y", "bar_store_signature": "z", "rows": [], "skipped": [],
        }

    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)

    trigger_resp = client.post("/research/desk/screen/compute", json={"screen_date": SCREEN_DATE})
    assert trigger_resp.json()["started"] is True
    assert started.wait(timeout=5)

    cancel_resp = client.post("/research/desk/screen/compute/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json() == {"cancelling": True}
    release.set()

    _wait_for_terminal(fresh_manager)
    fresh_manager.join_all(timeout=5)

    idle_cancel = client.post("/research/desk/screen/compute/cancel")
    assert idle_cancel.status_code == 409


# ==================================================================================================
# CLI warmer (TC-18)
# ==================================================================================================


def _set_cli_env(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_DIR", str(tmp_path / "screen"))
    monkeypatch.setenv("TAPEOLOGY_BAR_INDEX_DB", str(tmp_path / "bar_index.db"))
    monkeypatch.setenv("TAPEOLOGY_DATASET_INDEX_DB", str(tmp_path / "dataset_index.db"))


def test_cli_with_no_date_exits_nonzero_with_a_usage_error(tmp_path, monkeypatch, capsys):
    _set_cli_env(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "argv", ["desk_screen_compute"])

    with pytest.raises(SystemExit) as excinfo:
        desk_screen_compute.main()
    assert excinfo.value.code != 0
    assert "--date" in capsys.readouterr().err


def test_cli_with_date_runs_to_completion_against_a_scoped_fixture_dir(tmp_path, monkeypatch, capsys):
    """TC-18: ``--date 2026-06-22`` against a scoped test/fixture dir runs to completion and
    prints a ranked/skipped summary count."""
    _set_cli_env(monkeypatch, tmp_path)
    _register_fixture_universe(tmp_path / "universe")
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "bar_index.db"))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    monkeypatch.setattr(sys, "argv", ["desk_screen_compute", "--date", SCREEN_DATE])

    exit_code = desk_screen_compute.main()

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "ranked" in out and "skipped" in out

    screen_store = ScreenStore(tmp_path / "screen")
    records, errors = screen_store.list()
    assert errors == [] and len(records) == 1
    assert any(r["symbol"] == "AAPL" for r in records[0]["rows"])


def test_cli_second_invocation_with_identical_pins_reuses_the_existing_snapshot(tmp_path, monkeypatch, capsys):
    _set_cli_env(monkeypatch, tmp_path)
    _register_fixture_universe(tmp_path / "universe")
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "bar_index.db"))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    monkeypatch.setattr(sys, "argv", ["desk_screen_compute", "--date", SCREEN_DATE])

    assert desk_screen_compute.main() == 0
    assert desk_screen_compute.main() == 0

    screen_store = ScreenStore(tmp_path / "screen")
    records, errors = screen_store.list()
    assert errors == [] and len(records) == 1  # no second file
