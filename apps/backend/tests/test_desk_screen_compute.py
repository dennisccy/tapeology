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
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager as ws_manager
from app.providers.adapters.base import RawBar
from app.research import desk_screen, desk_screen_compute
from app.research.bar_index import BarIndex
from app.research.bars import BarStore
from app.research.datasets import DatasetStore
from app.research.desk_routes import get_desk_screen_compute_manager
from app.research.desk_screen import ScreenStore
from app.research.desk_screen_compute import DeskScreenComputeManager, run_screen_and_record
from app.research.desk_screen_log import ScreenRunStore
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
            "universe_snapshot_id": "x", "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc",
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
            "universe_snapshot_id": "x", "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc",
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
            "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc", "rows": [], "skipped": [],
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
            "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc", "rows": [], "skipped": [],
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
            "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc", "rows": [], "skipped": [],
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
            "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc", "rows": [], "skipped": [],
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
    recorded, reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
    )
    assert recorded is not None
    assert reused is False
    assert any(r["symbol"] == "AAPL" for r in recorded["rows"])
    records, errors = screen_store.list()
    assert errors == [] and len(records) == 1 and records[0]["id"] == recorded["id"]


def test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file(real_ctx, tmp_path):
    """TC-4: the manager/store returns the EXISTING snapshot (same id) rather than writing a
    second file -- and (era-desk-iter-4) the second call's own ``reused`` flag says so."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
    first, first_reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
    )
    second, second_reused = run_screen_and_record(
        UniverseStore(universe_store.root), BarStore(bar_store.root), BarIndex(bar_index.db_path),
        DatasetStore(tmp_path / "datasets"), CONFIG, screen_store, SCREEN_DATE,
    )
    assert first_reused is False
    assert second_reused is True
    assert second["id"] == first["id"]
    records, errors = screen_store.list()
    assert errors == [] and len(records) == 1  # no second file


def test_cancel_before_the_walk_starts_returns_none_and_records_nothing(real_ctx):
    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
    result, reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
        should_abort=lambda: True,
    )
    assert result is None
    assert reused is False
    records, _errors = screen_store.list()
    assert records == []


# ==================================================================================================
# era-desk-iter-4 (J-04, audit B2): the manager's own `reused`/`screen_id` fields, resolved through
# a full `trigger()` -> terminal-snapshot round trip against the REAL `compute_screen` (real
# fixture universe, real AAPL bars) -- distinct from the manager-mechanics section above, which
# fakes `compute_screen` for timing control and never asserted these two fields.
# ==================================================================================================


def test_trigger_resolves_reused_false_and_its_own_screen_id_on_a_fresh_compute(real_ctx):
    """TC-8."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
    mgr = DeskScreenComputeManager()
    mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
    snap = _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)

    assert snap["state"] == "done"
    assert snap["reused"] is False
    assert snap["screen_id"] is not None
    records, _errors = screen_store.list()
    assert records[0]["id"] == snap["screen_id"]


def test_trigger_resolves_reused_true_and_the_existing_screen_id_on_a_repeat_compute(real_ctx):
    """TC-7."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
    first_mgr = DeskScreenComputeManager()
    first_mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
    first_snap = _wait_for_terminal(first_mgr)
    first_mgr.join_all(timeout=5)
    assert first_snap["reused"] is False

    second_mgr = DeskScreenComputeManager()
    second_mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
    second_snap = _wait_for_terminal(second_mgr)
    second_mgr.join_all(timeout=5)

    assert second_snap["state"] == "done"
    assert second_snap["reused"] is True
    assert second_snap["screen_id"] == first_snap["screen_id"]
    records, errors = screen_store.list()
    assert errors == [] and len(records) == 1  # no second file


def test_initial_and_running_snapshot_carry_the_honest_reused_false_screen_id_null_defaults(
    manager_env, monkeypatch,
):
    """Initial/running state: ``reused: false``, ``screen_id: null`` -- nothing recorded yet."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
    started = threading.Event()
    release = threading.Event()

    def fake_compute_screen(*_args, **_kwargs):
        started.set()
        release.wait(timeout=5)
        return {
            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z",
            "universe_snapshot_id": "x", "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc",
            "rows": [], "skipped": [],
        }

    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)

    mgr = DeskScreenComputeManager()
    result = mgr.trigger(
        SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store,
    )
    assert result["compute"]["reused"] is False
    assert result["compute"]["screen_id"] is None
    assert started.wait(timeout=5)
    release.set()
    _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)


# ==================================================================================================
# Routes -- honest-empty (TC-5), ?date= (TC-6), 422 on missing screen_date, GET-never-computes,
# single-flight/cancel through HTTP, idle-cancel 409, no-universe refusal (era-desk-iter-4 TC-9).
# ==================================================================================================


@pytest.fixture
def route_ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_DIR", str(tmp_path / "screen"))
    # era-desk-iter-4 (closes audit T3): the ONE `route_ctx` among this file's siblings that read
    # the ambient `.data/datasets` tree instead of a temp dir -- `trigger_desk_screen_compute`
    # reads `dataset_store` for the tick-evidence badge via `get_dataset_store()`, which resolves
    # `TAPEOLOGY_DATASET_DIR` (unscoped here, previously) or else the real on-disk default.
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
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
    """The endpoint never defaults to the current wall-clock date."""
    client, _mgr, _tmp_path = route_ctx
    r = client.post("/research/desk/screen/compute", json={})
    assert r.status_code == 422


def test_post_trigger_with_no_universe_registered_refuses_and_persists_nothing(route_ctx):
    """era-desk-iter-4 TC-9 (closes audit B4): a screen compute must refuse -- never persist a
    permanent, useless honest-empty snapshot -- when no universe snapshot is registered."""
    client, fresh_manager, _tmp_path = route_ctx
    before = client.get("/research/desk/screen").json()
    assert before == {"screens": [], "latest": None, "integrity_errors": []}

    r = client.post("/research/desk/screen/compute", json={"screen_date": SCREEN_DATE})
    assert r.status_code == 422
    assert "universe" in r.json()["detail"]

    after = client.get("/research/desk/screen").json()
    assert after == {"screens": [], "latest": None, "integrity_errors": []}
    # No background job was even started.
    assert fresh_manager.snapshot() is None
    # The absent-universe wording names the action that fixes it, and does NOT claim a file problem.
    assert "no universe snapshot is registered" in r.json()["detail"]
    assert "POST /research/desk/universe/fetch" in r.json()["detail"]


# --- The non-session refusal --------------------------------------------------------------------
# The second reason a screen compute refuses before starting anything, and the same defect class as
# the no-universe refusal above: a screen for a Saturday, a US market holiday, or a date that has
# not happened yet is permanent, useless, and structurally unmeasurable (its forward record comes
# back all-absent by construction). ~280 of the 939 snapshots on disk on 2026-08-08 were exactly
# that. The refusal is derived from recorded DAILY bars, never a hardcoded calendar, and fails OPEN
# on every unproven case -- which is what keeps every hermetic fixture in this suite working.


def _plant_daily_sessions(tmp_path, symbol: str, days: list[str]) -> None:
    """One daily bar per named date, into the SAME scoped bar dir ``route_ctx`` points the app at."""
    bar_store = BarStore(tmp_path / "bars")
    bar_store.record(
        symbol=symbol, timeframe="1d",
        window_start_utc=f"{days[0]}T00:00:00Z", window_end_utc=f"{days[-1]}T23:59:59Z",
        feed="yahoo",
        bars=[
            RawBar(
                symbol, "1d",
                datetime.fromisoformat(f"{day}T14:30:00+00:00").timestamp(),
                10.0, 11.0, 9.0, 10.5, 1000,
            )
            for day in days
        ],
    )


def _register_one_member(tmp_path, symbol: str = "AAA") -> None:
    UniverseStore(tmp_path / "universe").record(
        members=[symbol], raw_members={symbol: symbol},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )


def test_post_trigger_on_a_bracketed_non_session_refuses_and_persists_nothing(route_ctx):
    """The daily bars record 2026-06-05 and 2026-06-08 and nothing between -- so 2026-06-06 is
    PROVABLY not a session, and screening it would leave a snapshot nothing can ever measure."""
    client, fresh_manager, tmp_path = route_ctx
    _register_one_member(tmp_path)
    _plant_daily_sessions(tmp_path, "AAA", ["2026-06-04", "2026-06-05", "2026-06-08"])

    r = client.post("/research/desk/screen/compute", json={"screen_date": "2026-06-06"})

    assert r.status_code == 422
    detail = r.json()["detail"]
    assert "2026-06-06 is not a recorded trading session" in detail
    # The refusal names its evidence rather than asserting a calendar nobody here holds.
    assert "AAA" in detail and "2026-06-04 through 2026-06-08" in detail
    assert client.get("/research/desk/screen").json()["screens"] == []
    assert fresh_manager.snapshot() is None


def test_post_trigger_on_a_recorded_session_is_not_refused(route_ctx):
    """The other direction of the same guard -- a lint that only ever refuses proves nothing."""
    client, _mgr, tmp_path = route_ctx
    _register_one_member(tmp_path)
    _plant_daily_sessions(tmp_path, "AAA", ["2026-06-04", "2026-06-05", "2026-06-08"])

    r = client.post("/research/desk/screen/compute", json={"screen_date": "2026-06-05"})

    assert r.status_code == 200
    assert r.json()["started"] is True


def test_post_trigger_past_the_last_recorded_daily_bar_is_not_refused(route_ctx):
    """A date after the anchors' recorded span is NOT claimed as a non-session: daily bars cannot
    prove anything about a session nobody has recorded yet. The refresh chain drops those dates by
    intersecting with the recorded sessions instead; this route refuses only what is provable."""
    client, _mgr, tmp_path = route_ctx
    _register_one_member(tmp_path)
    _plant_daily_sessions(tmp_path, "AAA", ["2026-06-04", "2026-06-05"])

    r = client.post("/research/desk/screen/compute", json={"screen_date": "2099-01-01"})

    assert r.status_code == 200


def test_post_trigger_with_no_daily_bars_recorded_refuses_nothing(route_ctx):
    """The fail-open rail that keeps every hermetic fixture in this suite working: with no daily
    evidence at all, the refusal is silent and this route behaves exactly as it did before."""
    client, _mgr, tmp_path = route_ctx
    _register_one_member(tmp_path)

    r = client.post("/research/desk/screen/compute", json={"screen_date": "2026-06-06"})

    assert r.status_code == 200


def test_post_trigger_refusal_names_a_damaged_universe_snapshot_rather_than_claiming_none_exists(
    route_ctx,
):
    """era-desk-iter-4 audit B2: ``UniverseStore.list()`` also reports ``records == []`` when
    snapshot FILES exist but every one failed its integrity check. The refusal is right either way,
    but the two causes need different operator actions, so the message must distinguish them
    instead of saying "nothing is registered" about a universe that IS registered (and damaged)."""
    client, fresh_manager, tmp_path = route_ctx
    universe_dir = tmp_path / "universe"
    snapshot = UniverseStore(universe_dir).record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    path = universe_dir / f"{snapshot['id']}.json"
    payload = json.loads(path.read_text())
    payload["record"]["meta"]["member_count"] = 999  # tamper -- the file checksum now disagrees
    path.write_text(json.dumps(payload))
    records, errors = UniverseStore(universe_dir).list()
    assert records == [] and len(errors) == 1  # the precondition this finding is about

    r = client.post("/research/desk/screen/compute", json={"screen_date": SCREEN_DATE})

    assert r.status_code == 422
    detail = r.json()["detail"]
    assert "no READABLE universe snapshot is registered" in detail
    assert "integrity check" in detail
    assert f"{snapshot['id']}.json" in detail  # the operator is told WHICH file to look at
    assert "POST /research/desk/universe/fetch" not in detail  # not the action this cause needs
    assert fresh_manager.snapshot() is None
    assert client.get("/research/desk/screen").json() == {
        "screens": [], "latest": None, "integrity_errors": [],
    }


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
            "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc", "rows": [], "skipped": [],
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


def test_cli_refuses_a_bracketed_non_session_so_the_terminal_is_not_a_way_around_the_route(
    tmp_path, monkeypatch, capsys
):
    """The CLI carries the identical non-session refusal ``POST /research/desk/screen/compute``
    applies. Without it, the guard would be one `python -m` away from being bypassed -- and the
    snapshots it exists to stop are exactly the ones a scripted range walk produces.

    2026-06-20 is a Saturday: the AAPL daily fixture records the sessions on both sides of it and
    nothing on it."""
    _set_cli_env(monkeypatch, tmp_path)
    _register_fixture_universe(tmp_path / "universe")
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "bar_index.db"))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    monkeypatch.setattr(sys, "argv", ["desk_screen_compute", "--date", "2026-06-20"])

    exit_code = desk_screen_compute.main()

    assert exit_code == 2
    assert "2026-06-20 is not a recorded trading session" in capsys.readouterr().out
    # Nothing was walked and nothing was persisted.
    records, errors = ScreenStore(tmp_path / "screen").list()
    assert errors == [] and records == []


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


def test_tc3_cli_run_leaves_exactly_one_matching_screen_run_record(tmp_path, monkeypatch, capsys):
    """TC-3 (goal-desk-iter-31): a CLI-triggered run leaves exactly ONE durable ``ScreenRunStore``
    record whose ``state``/``screen_id``/``members_attempted`` match the ``ScreenStore`` snapshot it
    produced -- the SAME single shared writer (``run_screen_and_record``) the HTTP route uses,
    exercised here through the CLI's own ``main()`` entry point. ``_set_cli_env`` sets no
    ``TAPEOLOGY_DESK_SCREEN_LOG_DIR`` override, so the run log resolves to the sibling-of-universe
    default (``resolve_desk_screen_log_dir``) -- the same ``tmp_path / "screen_runs"`` this file's
    other ``ScreenRunStore`` fixtures already point at."""
    _set_cli_env(monkeypatch, tmp_path)
    _register_fixture_universe(tmp_path / "universe")
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "bar_index.db"))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    monkeypatch.setattr(sys, "argv", ["desk_screen_compute", "--date", SCREEN_DATE])

    exit_code = desk_screen_compute.main()
    assert exit_code == 0
    capsys.readouterr()

    screen_store = ScreenStore(tmp_path / "screen")
    screen_records, screen_errors = screen_store.list()
    assert screen_errors == [] and len(screen_records) == 1
    snapshot = screen_records[0]

    screen_run_store = ScreenRunStore(tmp_path / "screen_runs")
    run_records, run_errors = screen_run_store.list()
    assert run_errors == [] and len(run_records) == 1
    run = run_records[0]
    assert run["state"] == "done"
    assert run["screen_id"] == snapshot["id"]
    assert run["members_attempted"] == run["members_total"]


# ==================================================================================================
# goal-desk-iter-29 (J-18) -- the screen-run log: the five-pin pre-check reuse short-circuit, and
# ONE durable run record per terminal outcome (done/cancelled/failed), written by
# `record_screen_run` from INSIDE `run_screen_and_record` (the one shared entry point both the
# manager and the CLI call). TC-2 through TC-9 -- the three pre-existing tests named in the plan
# (`test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file`,
# `test_cli_second_invocation_with_identical_pins_reuses_the_existing_snapshot`,
# `test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_silent_overwrite`, all
# above) are untouched by this section.
# ==================================================================================================


@pytest.fixture
def run_log_ctx(real_ctx, tmp_path):
    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
    screen_run_store = ScreenRunStore(tmp_path / "screen_runs")
    return universe_store, bar_store, bar_index, dataset_store, screen_store, screen_run_store


def _skip_tally(skipped: list[dict]) -> dict:
    tally = {"no_bars": 0, "no_basis": 0}
    for entry in skipped:
        tally[entry["reason"]] += 1
    return tally


def test_tc2_tc4_a_pin_miss_run_walks_every_member_and_records_a_matching_run_log_entry(run_log_ctx):
    """TC-2/TC-4: a fresh pin set walks every member and records ONE run whose counts/pins/
    ``screen_id`` are byte-identical to the snapshot it produced."""
    universe_store, bar_store, bar_index, dataset_store, screen_store, screen_run_store = run_log_ctx

    recorded, reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
        screen_run_store=screen_run_store,
    )
    assert reused is False

    records, errors = screen_run_store.list()
    assert errors == [] and len(records) == 1
    run = records[0]
    assert run["state"] == "done"
    assert run["reused"] is False
    assert run["screen_date"] == recorded["screen_date"]
    assert run["universe_snapshot_id"] == recorded["universe_snapshot_id"]
    assert run["config_fingerprint"] == recorded["config_fingerprint"]
    assert run["bar_store_signature"] == recorded["bar_store_signature"]
    assert run["screen_id"] == recorded["id"]
    assert run["members_total"] == run["members_attempted"]
    assert run["ranked_count"] == len(recorded["rows"])
    assert run["skipped_by_reason"] == _skip_tally(recorded["skipped"])
    assert run["error"] is None and run["failed_member"] is None


def test_tc3_an_identical_pin_retrigger_makes_zero_compute_tradability_calls_and_reuses(
    run_log_ctx, monkeypatch,
):
    """TC-3: the reuse short-circuit resolves the five pins and hits ``ScreenStore.find_by_key``
    BEFORE ``compute_screen`` (and therefore ``compute_tradability``) is ever called -- a real
    call-counting wrapper around the REAL ``compute_tradability`` proves zero NEW calls on the
    second, identical-pin invocation."""
    universe_store, bar_store, bar_index, dataset_store, screen_store, screen_run_store = run_log_ctx

    calls = {"n": 0}
    real_compute_tradability = desk_screen.compute_tradability

    def _counting_compute_tradability(*args, **kwargs):
        calls["n"] += 1
        return real_compute_tradability(*args, **kwargs)

    monkeypatch.setattr(desk_screen, "compute_tradability", _counting_compute_tradability)

    first, first_reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
        screen_run_store=screen_run_store,
    )
    assert first_reused is False
    calls_after_first = calls["n"]
    assert calls_after_first > 0  # the fixture universe has more than zero members

    second, second_reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
        screen_run_store=screen_run_store,
    )
    assert second_reused is True
    assert second["id"] == first["id"]
    assert calls["n"] == calls_after_first, "the retrigger must make ZERO new compute_tradability calls"

    records, errors = screen_run_store.list()
    assert errors == [] and len(records) == 2  # two DISTINCT run-log entries -- one per attempt
    second_run = records[1]
    assert second_run["reused"] is True
    assert second_run["members_attempted"] == 0
    assert second_run["screen_id"] == first["id"]

    screen_records, screen_errors = screen_store.list()
    assert screen_errors == [] and len(screen_records) == 1  # no second screen snapshot file


def test_tc5_a_cancellation_mid_walk_records_state_cancelled_with_partial_attempts_and_no_snapshot(
    manager_env, monkeypatch, tmp_path,
):
    """TC-5: a walk cancelled partway through records ``state: "cancelled"``,
    ``members_attempted < members_total``, ``screen_id: null`` -- and no snapshot file."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
    screen_run_store = ScreenRunStore(tmp_path / "screen_runs")

    def fake_compute_screen(_us, _bs, _bi, _ds, _cfg, _sd, *, progress=None, should_abort=None):
        rows: list[dict] = []
        skipped: list[dict] = []
        for symbol in SMALL_MEMBERS:
            if should_abort is not None and should_abort():
                break
            skipped.append(
                {"symbol": symbol, "skipped": True, "reason": "no_bars", "coverage": {}, "tick_evidence": False}
            )
            if progress is not None:
                progress({"symbol": symbol})
        return {
            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
            "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc", "rows": rows, "skipped": skipped,
        }

    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)

    calls = {"n": 0}

    def should_abort() -> bool:
        calls["n"] += 1
        return calls["n"] > 1  # let the first member through, abort before the second

    result, reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
        should_abort=should_abort, screen_run_store=screen_run_store,
    )
    assert result is None
    assert reused is False

    records, errors = screen_run_store.list()
    assert errors == [] and len(records) == 1
    run = records[0]
    assert run["state"] == "cancelled"
    assert run["members_attempted"] < run["members_total"]
    assert run["screen_id"] is None
    assert run["error"] is None

    screen_records, _errors = screen_store.list()
    assert screen_records == []


def test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_failed_member(
    manager_env, monkeypatch, tmp_path,
):
    """TC-6: a member whose computation raises during the walk records ``state: "failed"`` with
    the exception detail verbatim and the raising member's own name -- and no snapshot file. The
    raise ALSO propagates out of ``run_screen_and_record`` itself (re-raised after logging), so the
    manager's/CLI's own existing crash-handling stays byte-unchanged."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
    screen_run_store = ScreenRunStore(tmp_path / "screen_runs")

    def fake_compute_screen(_us, _bs, _bi, _ds, _cfg, _sd, *, progress=None, should_abort=None):
        for symbol in SMALL_MEMBERS:  # sorted: ["AAA", "BBB"]
            if symbol == "BBB":
                raise RuntimeError("synthetic raise on member BBB")
            if progress is not None:
                progress({"symbol": symbol})
        raise AssertionError("unreachable -- BBB always raises before this point")

    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)

    with pytest.raises(RuntimeError, match="synthetic raise on member BBB"):
        run_screen_and_record(
            universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
            screen_run_store=screen_run_store,
        )

    records, errors = screen_run_store.list()
    assert errors == [] and len(records) == 1
    run = records[0]
    assert run["state"] == "failed"
    assert run["error"] == "synthetic raise on member BBB"
    assert run["failed_member"] == "BBB"
    assert run["screen_id"] is None
    assert run["reused"] is False

    screen_records, _errors = screen_store.list()
    assert screen_records == []


def test_tc1_a_crash_before_any_member_is_attempted_records_failed_member_null(
    manager_env, monkeypatch, tmp_path,
):
    """TC-1 (goal-desk-iter-31): a run that crashes before ``_counting_progress`` ever fires
    (``attempted == 0``) must never fabricate a ``failed_member`` -- it records ``null`` rather than
    naming a symbol the walk never reached. Companion regression guard: TC-2, the test immediately
    above (``test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_failed_member``,
    unmodified), proves the ``attempted > 0`` case still names the genuinely in-progress member."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
    screen_run_store = ScreenRunStore(tmp_path / "screen_runs")

    def fake_compute_screen(_us, _bs, _bi, _ds, _cfg, _sd, *, progress=None, should_abort=None):
        raise RuntimeError("synthetic raise before any member is attempted")

    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)

    with pytest.raises(RuntimeError, match="synthetic raise before any member is attempted"):
        run_screen_and_record(
            universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
            screen_run_store=screen_run_store,
        )

    records, errors = screen_run_store.list()
    assert errors == [] and len(records) == 1
    run = records[0]
    assert run["state"] == "failed"
    assert run["error"] == "synthetic raise before any member is attempted"
    assert run["failed_member"] is None
    assert run["screen_id"] is None
    assert run["reused"] is False

    screen_records, _errors = screen_store.list()
    assert screen_records == []


def test_tc7_omitting_the_run_store_leaves_no_durable_record_for_that_run(real_ctx, tmp_path):
    """TC-7: a process that ends before the writer's terminal call (simulated here by simply never
    supplying a ``screen_run_store``) leaves the ledger with no entry for that run -- the SAME
    "structural, not policed" guarantee ``test_desk_screen_log.py`` proves at the store level,
    exercised here through the real run path."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx

    recorded, reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
    )
    assert recorded is not None and reused is False

    # A store constructed AFTER the run, pointed at where a run log WOULD have lived, still finds
    # nothing -- the run never called the writer, so nothing was ever written.
    screen_run_store = ScreenRunStore(tmp_path / "screen_runs")
    records, errors = screen_run_store.list()
    assert records == [] and errors == []


# --- Route-level: TC-1 (honest empty) + TC-8 (two sequential runs) --------------------------------


def test_tc1_get_screen_runs_before_any_run_is_an_honest_empty_200(route_ctx):
    client, _mgr, _tmp_path = route_ctx
    r = client.get("/research/desk/screen/runs")
    assert r.status_code == 200
    assert r.json() == {"runs": [], "latest": None, "integrity_errors": []}


def test_tc8_two_sequential_triggers_append_two_run_records_first_file_byte_unchanged(route_ctx):
    """TC-8: a second (genuinely distinct-pin) trigger appends a new run record while the first
    run's own log file stays byte-identical on disk, and the meta-only ``runs`` list carries both."""
    client, fresh_manager, tmp_path = route_ctx
    UniverseStore(tmp_path / "universe").record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )

    def _trigger_and_wait(screen_date: str) -> dict:
        resp = client.post("/research/desk/screen/compute", json={"screen_date": screen_date})
        assert resp.status_code == 200
        deadline = time.time() + 5
        snap = None
        while time.time() < deadline:
            snap = client.get("/research/desk/screen/compute").json()
            if snap is not None and snap["state"] != "running":
                break
            time.sleep(0.02)
        assert snap is not None and snap["state"] == "done"
        return snap

    first_snap = _trigger_and_wait(SCREEN_DATE)
    assert first_snap["reused"] is False

    log_dir = tmp_path / "screen_runs"
    first_files = sorted(log_dir.glob("*.json"))
    assert len(first_files) == 1
    first_bytes = first_files[0].read_bytes()

    runs_after_first = client.get("/research/desk/screen/runs").json()
    assert len(runs_after_first["runs"]) == 1
    assert runs_after_first["latest"]["state"] == "done"
    assert "ranked_count" in runs_after_first["latest"]
    assert "ranked_count" not in runs_after_first["runs"][0]  # meta-only list omits the heavy fields

    # A DIFFERENT screen_date is a genuine pin miss -- a second, distinct run.
    second_snap = _trigger_and_wait("2026-06-23")
    assert second_snap["reused"] is False

    assert first_files[0].read_bytes() == first_bytes  # byte-unchanged
    runs_after_second = client.get("/research/desk/screen/runs").json()
    assert len(runs_after_second["runs"]) == 2
    fresh_manager.join_all(timeout=5)


def test_a_terminal_log_write_that_raises_is_never_re_logged_as_a_second_failed_record(
    manager_env, monkeypatch, tmp_path,
):
    """goal-desk-iter-29 audit (B1): the run log is written EXACTLY ONCE per run even when the
    write itself FAILS. A raising terminal write (a full disk, a read-only log dir) must NOT be
    caught by ``run_screen_and_record``'s outer except-clause and re-entered as a SECOND, "failed"
    record -- that record would claim a terminal state the run never had (the snapshot really was
    recorded) and carry the LEDGER's own I/O error as if it were a screen failure. The run leaves
    NO record (the module's documented interrupted-run honesty) and the error propagates verbatim,
    never silently swallowed."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
    screen_run_store = ScreenRunStore(tmp_path / "screen_runs")

    def fake_compute_screen(_us, _bs, _bi, _ds, _cfg, _sd, *, progress=None, should_abort=None):
        skipped = []
        for symbol in SMALL_MEMBERS:
            skipped.append(
                {"symbol": symbol, "skipped": True, "reason": "no_bars", "coverage": {},
                 "tick_evidence": False}
            )
            if progress is not None:
                progress({"symbol": symbol})
        return {
            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
            "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc", "rows": [], "skipped": skipped,
        }

    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)

    calls = {"n": 0}

    def exploding_record_screen_run(*_args, **_kwargs):
        calls["n"] += 1
        raise OSError("[Errno 28] No space left on device: 'screen_runs'")

    monkeypatch.setattr(desk_screen_compute, "record_screen_run", exploding_record_screen_run)

    with pytest.raises(OSError, match="No space left on device"):
        run_screen_and_record(
            universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
            screen_run_store=screen_run_store,
        )

    assert calls["n"] == 1, "a failed terminal write must never be re-entered as a second record"
    records, errors = screen_run_store.list()
    assert records == [] and errors == []  # no fabricated entry for a run whose write never landed
    # The screen snapshot itself was still recorded before the ledger write was attempted -- the
    # walk's own append-only result is untouched by this failure mode.
    screen_records, screen_errors = screen_store.list()
    assert screen_errors == [] and len(screen_records) == 1
