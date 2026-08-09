"""``desk_deep_backfill.py`` -- deep 1m/5m history from the credentialed Alpaca adapter, for the
years the Yahoo top-up cannot reach.

Everything here runs against planted, scoped stores under ``tmp_path`` with a FAKE adapter (never
``apps/backend/.data``, never a real vendor call, never a real credential). The properties that
matter, in order of how much damage getting them wrong would do:

  1. **The overlap clamp.** ``BarStore.merged_bars`` resolves a contested timestamp in favour of the
     most recently CREATED series, so a deep window reaching into the Yahoo-covered region would
     permanently replace the recent tape's Yahoo prices with SIP ones in an append-only store. Every
     planned window must end before that region begins, and the ceiling must come from the SAME
     constant the top-up floors at.
  2. **Resumability.** An already-recorded chunk is answered store-first with zero vendor calls --
     what makes an interrupted multi-hour sweep resume rather than restart.
  3. **Confinement.** This module never names an Alpaca credential and never imports the SDK.
"""

from __future__ import annotations

import inspect
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager as ws_manager
from app.providers.adapters.base import RawBar
from app.research import desk_deep_backfill
from app.research.bar_index import BarIndex
from app.research.bars import BarStore
from app.research.desk_deep_backfill import (
    DESK_DEEP_CHUNK_DAYS,
    DESK_DEEP_TIMEFRAMES,
    DESK_DEEP_VENDOR,
    DeepBackfillRunStore,
    DeskDeepBackfillComputeManager,
    deep_window_ceiling,
    plan_deep_windows,
    run_deep_backfill,
)
from app.research.desk_routes import (
    get_desk_deep_backfill_manager,
    get_deep_backfill_run_store,
)
from app.research.desk_topup_compute import _TOPUP_FINE_LOOKBACK_DAYS
from app.research.desk_universe import UniverseStore
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore

TODAY = date(2026, 8, 8)


# ==================================================================================================
# 1. Window planning and the overlap clamp.
# ==================================================================================================


def test_the_ceiling_is_the_top_ups_own_retention_floor_not_a_second_number():
    """The one property that keeps the two vendors' regions meeting without overlapping. A separate
    constant here would drift and start silently overwriting Yahoo's recent tape, in a store where
    nothing can be deleted or re-tagged."""
    for timeframe, lookback in _TOPUP_FINE_LOOKBACK_DAYS.items():
        expected = date(2026, 8, 8).toordinal() - lookback
        assert deep_window_ceiling(timeframe, TODAY) == date.fromordinal(expected).isoformat()


def test_a_timeframe_with_no_retention_floor_is_refused_rather_than_guessed():
    with pytest.raises(ValueError, match="no fine-bar retention floor"):
        deep_window_ceiling("1d", TODAY)


def test_no_planned_window_ever_reaches_into_the_yahoo_covered_region():
    plan = plan_deep_windows(["AAA", "BBB"], DESK_DEEP_TIMEFRAMES, "2025-01-01", "2026-08-08", TODAY)

    assert plan, "a plan reaching back to 2025 cannot be empty"
    for chunk in plan:
        ceiling = deep_window_ceiling(chunk["timeframe"], TODAY)
        # STRICTLY before: `end` is inclusive by UTC date at the record route, so a chunk ending ON
        # the ceiling would fetch one session inside the Yahoo-covered region -- and that region's
        # bars can never be un-replaced once the newer series wins the merge.
        assert chunk["end"][:10] < ceiling, (
            f"{chunk['symbol']} {chunk['timeframe']} reaches {chunk['end']}, at or past the "
            f"{ceiling} boundary where the Yahoo-recorded region begins"
        )


def test_a_range_entirely_inside_the_yahoo_region_plans_nothing_and_is_not_an_error():
    """The honest answer, not a failure: those bars are already on file from the top-up."""
    plan = plan_deep_windows(["AAA"], DESK_DEEP_TIMEFRAMES, "2026-08-01", "2026-08-08", TODAY)

    assert plan == []


def test_a_range_crossing_the_boundary_is_truncated_rather_than_refused():
    plan = plan_deep_windows(["AAA"], ("5m",), "2026-05-01", "2026-08-08", TODAY)

    assert plan
    ceiling = date.fromisoformat(deep_window_ceiling("5m", TODAY))
    assert plan[-1]["end"][:10] == (ceiling - timedelta(days=1)).isoformat()


def test_chunks_abut_without_sharing_a_boundary_date():
    """Both bounds are INCLUSIVE at the record route, so consecutive chunks must start the day
    after the previous one ends -- sharing the date would re-fetch a session per chunk."""
    plan = plan_deep_windows(["AAA"], ("1m",), "2026-01-01", "2026-07-09", TODAY)

    assert plan[0]["start"] == "2026-01-01T00:00:00Z"
    for previous, following in zip(plan, plan[1:]):
        previous_end = date.fromisoformat(previous["end"][:10])
        assert following["start"][:10] == (previous_end + timedelta(days=1)).isoformat(), (
            "a gap or an overlap between consecutive chunks"
        )
    spans = [
        date.fromisoformat(c["end"][:10]).toordinal()
        - date.fromisoformat(c["start"][:10]).toordinal()
        for c in plan
    ]
    assert max(spans) < DESK_DEEP_CHUNK_DAYS


def test_the_plan_is_clock_free_and_reproducible():
    """``today`` is passed in, so a dry run and the apply that follows it plan identically."""
    first = plan_deep_windows(["AAA"], DESK_DEEP_TIMEFRAMES, "2025-06-01", "2026-08-08", TODAY)
    second = plan_deep_windows(["AAA"], DESK_DEEP_TIMEFRAMES, "2025-06-01", "2026-08-08", TODAY)
    assert first == second
    later = plan_deep_windows(
        ["AAA"], DESK_DEEP_TIMEFRAMES, "2025-06-01", "2026-08-08", date(2026, 9, 8)
    )
    assert later != first, "the ceiling must move with the date it is given"


# ==================================================================================================
# 2. The walk: outcome classification, resumability, cancellation.
# ==================================================================================================


class _FakeVendorAdapter:
    """Serves one bar per requested window and counts every call — the seam that proves a reused
    chunk costs ZERO vendor calls. Deliberately NOT ``tests/fakes.FakeAdapter``: that one replays a
    single fixed tuple for every call, so every chunk here would record byte-identical content and
    resolve as a 409 instead of a distinct series."""

    name = "fake"

    def __init__(self) -> None:
        self.fetch_bars_calls: list[tuple] = []

    def is_available(self) -> bool:
        return True

    def warm_symbol_universe(self) -> None:
        """Never raises — the startup warm swallows failures, and this fake is mounted through the
        same ``get_market_adapter`` seam the app warms on."""

    def fetch_bars(self, symbol, start, end, timeframe):
        self.fetch_bars_calls.append((symbol, timeframe, start, end))
        return (RawBar(symbol, timeframe, start.timestamp(), 10.0, 11.0, 9.0, 10.5, 1000),)


@pytest.fixture
def walk_ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_DEEP_BACKFILL_WORKERS", "1")
    adapter = _FakeVendorAdapter()
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    yield (
        adapter,
        BarStore(tmp_path / "bars"),
        BarIndex(str(tmp_path / "index.db")),
        registry,
    )
    set_registry(None)
    app.dependency_overrides.pop(get_market_adapter, None)
    store.close()


def test_a_first_walk_fetches_and_records_every_chunk(walk_ctx):
    adapter, bar_store, bar_index, registry = walk_ctx
    chunks = plan_deep_windows(["AAA"], ("5m",), "2026-01-01", "2026-03-01", TODAY)

    outcomes = run_deep_backfill(chunks, bar_store, bar_index, registry)

    assert len(outcomes) == len(chunks)
    assert {o["outcome"] for o in outcomes} == {"fetched"}
    assert len(adapter.fetch_bars_calls) == len(chunks)
    assert all(o["bars_recorded"] == 1 for o in outcomes)


def test_a_second_walk_over_the_same_chunks_costs_zero_vendor_calls(walk_ctx):
    """Resumability, which is the whole reason a multi-hour sweep is safe to cancel."""
    adapter, bar_store, bar_index, registry = walk_ctx
    chunks = plan_deep_windows(["AAA"], ("5m",), "2026-01-01", "2026-03-01", TODAY)
    run_deep_backfill(chunks, bar_store, bar_index, registry)
    calls_after_first = len(adapter.fetch_bars_calls)

    outcomes = run_deep_backfill(chunks, bar_store, bar_index, registry)

    assert {o["outcome"] for o in outcomes} == {"reused"}
    assert len(adapter.fetch_bars_calls) == calls_after_first
    assert all(o["bars_recorded"] == 0 for o in outcomes)


def test_one_failing_chunk_never_aborts_the_walk(walk_ctx):
    adapter, bar_store, bar_index, registry = walk_ctx

    original = adapter.fetch_bars

    def _explode(symbol, start, end, timeframe):
        if symbol == "BBB":
            raise RuntimeError("the vendor said no")
        return original(symbol, start, end, timeframe)

    adapter.fetch_bars = _explode
    chunks = plan_deep_windows(["AAA", "BBB", "CCC"], ("5m",), "2026-01-01", "2026-02-01", TODAY)

    outcomes = run_deep_backfill(chunks, bar_store, bar_index, registry)

    assert len(outcomes) == len(chunks)
    failed = [o for o in outcomes if o["outcome"] == "failed"]
    assert failed and {o["symbol"] for o in failed} == {"BBB"}
    # The detail is preserved verbatim rather than flattened into a generic message.
    assert "the vendor said no" in failed[0]["detail"]
    assert {o["outcome"] for o in outcomes if o["symbol"] != "BBB"} == {"fetched"}


def test_an_abort_stops_the_walk_and_keeps_what_it_finished(walk_ctx):
    _adapter, bar_store, bar_index, registry = walk_ctx
    chunks = plan_deep_windows(["AAA"], ("5m",), "2026-01-01", "2026-06-01", TODAY)
    assert len(chunks) > 2
    seen = 0

    def _abort() -> bool:
        return seen >= 2

    def _count(_entry) -> None:
        nonlocal seen
        seen += 1

    outcomes = run_deep_backfill(
        chunks, bar_store, bar_index, registry, progress=_count, should_abort=_abort
    )

    assert len(outcomes) == 2
    records, errors = bar_store.list(include_bars=False)
    assert errors == [] and len(records) == 2  # every finished chunk is on disk


def test_every_recording_is_stamped_with_the_credentialed_feed_not_yahoo(walk_ctx):
    """``feed`` is part of both the content checksum and the ``bar_index`` primary key, which is
    what makes an Alpaca series structurally incapable of colliding with a Yahoo one."""
    _adapter, bar_store, bar_index, registry = walk_ctx
    chunks = plan_deep_windows(["AAA"], ("5m",), "2026-01-01", "2026-02-01", TODAY)

    run_deep_backfill(chunks, bar_store, bar_index, registry)

    records, _errors = bar_store.list(include_bars=False)
    assert {r["feed"] for r in records} == {CONFIG.historical_feed}
    assert "yahoo" not in {r["feed"] for r in records}


# ==================================================================================================
# 3. Confinement -- the rails `test_real_data_gate.py` polices for the adapter, applied here.
# ==================================================================================================


def test_this_module_names_no_credential_and_imports_no_vendor_sdk():
    source = inspect.getsource(desk_deep_backfill)
    for banned in ("ALPACA_API_KEY", "ALPACA_API_SECRET", "from alpaca", "import alpaca"):
        assert banned not in source, (
            f"desk_deep_backfill names {banned!r} -- credentials and the SDK are confined to "
            "providers/adapters/alpaca.py, and this module only ever passes the vendor STRING"
        )
    assert f'DESK_DEEP_VENDOR = "{DESK_DEEP_VENDOR}"' in source


def test_this_module_adds_no_config_field():
    """The fingerprint is pinned; every knob here is a plain module constant or an env var."""
    source = inspect.getsource(desk_deep_backfill)
    assert "CONFIG." in source  # it reads config...
    assert "class Config" not in source and "Config(" not in source  # ...and never defines one


# ==================================================================================================
# 4. The run ledger.
# ==================================================================================================


def test_the_run_ledger_derives_every_count_from_the_outcomes_it_is_given(tmp_path):
    store = DeepBackfillRunStore(tmp_path / "runs")

    meta = store.record(
        vendor="alpaca",
        requested_window={"start": "2025-01-01", "end": "2026-06-01"},
        timeframes=["1m", "5m"],
        members_total=3,
        config_fingerprint=CONFIG.config_fingerprint(),
        started_utc="2026-08-08T00:00:00.000000Z",
        finished_utc="2026-08-08T01:00:00.000000Z",
        state="done",
        chunks_total=5,
        outcomes=[
            {"outcome": "fetched", "bars_recorded": 8000},
            {"outcome": "fetched", "bars_recorded": 7500},
            {"outcome": "reused", "bars_recorded": 0},
            {"outcome": "unchanged", "bars_recorded": 0},
            {"outcome": "failed", "bars_recorded": 0},
        ],
    )

    assert meta["chunks_attempted"] == 5
    assert meta["chunks_fetched"] == 2
    assert meta["chunks_reused"] == 1
    assert meta["chunks_unchanged"] == 1
    assert meta["chunks_failed"] == 1
    assert meta["bars_recorded"] == 15500


def test_the_run_ledger_refuses_a_non_terminal_state(tmp_path):
    store = DeepBackfillRunStore(tmp_path / "runs")
    with pytest.raises(ValueError, match="invalid terminal state"):
        store.record(
            vendor="alpaca", requested_window={}, timeframes=[], members_total=0,
            config_fingerprint="x", started_utc="2026-08-08T00:00:00.000000Z",
            finished_utc="2026-08-08T00:00:00.000000Z", state="running",
            chunks_total=0, outcomes=[],
        )


def test_an_unwritten_ledger_is_honestly_empty_never_a_crash(tmp_path):
    assert DeepBackfillRunStore(tmp_path / "never-created").list() == ([], [])


def test_a_tampered_run_record_is_surfaced_never_served_as_data(tmp_path):
    store = DeepBackfillRunStore(tmp_path / "runs")
    meta = store.record(
        vendor="alpaca", requested_window={}, timeframes=[], members_total=0,
        config_fingerprint="x", started_utc="2026-08-08T00:00:00.000000Z",
        finished_utc="2026-08-08T00:00:00.000000Z", state="done", chunks_total=0, outcomes=[],
    )
    path = store.root / f"{meta['id']}.json"
    path.write_text(path.read_text().replace('"chunks_total": 0', '"chunks_total": 999'))

    records, errors = store.list()

    assert records == []
    assert len(errors) == 1 and "integrity check" in errors[0]["error"]


# ==================================================================================================
# 5. The routes.
# ==================================================================================================


@pytest.fixture
def route_ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_BAR_INDEX_DB", str(tmp_path / "index.db"))
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    monkeypatch.setenv("TAPEOLOGY_DESK_DEEP_BACKFILL_WORKERS", "1")
    adapter = _FakeVendorAdapter()
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    fresh_manager = DeskDeepBackfillComputeManager()
    run_store = DeepBackfillRunStore(tmp_path / "deep_runs")
    app.dependency_overrides[get_desk_deep_backfill_manager] = lambda: fresh_manager
    app.dependency_overrides[get_deep_backfill_run_store] = lambda: run_store
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    set_registry(ResearchRegistry(store, CONFIG))
    with TestClient(app) as client:
        yield client, fresh_manager, run_store, adapter, tmp_path
    fresh_manager.join_all(timeout=10.0)
    for ticker in list(ws_manager._engines.keys()):
        ws_manager.stop(ticker)
    set_registry(None)
    for dependency in (get_market_adapter, get_desk_deep_backfill_manager, get_deep_backfill_run_store):
        app.dependency_overrides.pop(dependency, None)
    store.close()


def _register_universe(tmp_path, members):
    UniverseStore(tmp_path / "universe").record(
        members=members, raw_members={m: m for m in members},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )


def test_the_plan_route_discloses_the_clamp_before_anything_is_clicked(route_ctx):
    client, _mgr, _runs, _adapter, tmp_path = route_ctx
    _register_universe(tmp_path, ["AAA", "BBB"])

    body = client.get(
        "/research/desk/backfill/plan", params={"from_day": "2025-01-01", "to_day": "2026-08-08"}
    ).json()

    assert body["members_total"] == 2
    assert body["chunks_total"] > 0
    assert set(body["per_timeframe"]) == set(DESK_DEEP_TIMEFRAMES)
    for timeframe, detail in body["per_timeframe"].items():
        assert detail["clamped_end"] < "2026-08-08"
        assert detail["chunks"] > 0
        assert timeframe in DESK_DEEP_TIMEFRAMES


def test_the_plan_route_issues_no_vendor_call(route_ctx):
    client, _mgr, _runs, adapter, tmp_path = route_ctx
    _register_universe(tmp_path, ["AAA"])

    client.get(
        "/research/desk/backfill/plan", params={"from_day": "2025-01-01", "to_day": "2026-06-01"}
    )

    assert adapter.fetch_bars_calls == []


def test_trigger_with_no_universe_refuses_and_starts_nothing(route_ctx):
    client, fresh_manager, _runs, _adapter, _tmp_path = route_ctx

    r = client.post(
        "/research/desk/backfill/compute", json={"from_day": "2025-01-01", "to_day": "2026-06-01"}
    )

    assert r.status_code == 422
    assert "no universe snapshot is registered" in r.json()["detail"]
    assert fresh_manager.snapshot() is None


def test_trigger_refuses_a_timeframe_this_path_does_not_serve(route_ctx):
    client, fresh_manager, _runs, _adapter, tmp_path = route_ctx
    _register_universe(tmp_path, ["AAA"])

    r = client.post(
        "/research/desk/backfill/compute",
        json={"from_day": "2025-01-01", "to_day": "2026-06-01", "timeframes": ["1h"]},
    )

    assert r.status_code == 422
    assert "1h" in r.json()["detail"]
    assert fresh_manager.snapshot() is None


def test_a_trigger_runs_to_done_and_leaves_exactly_one_run_record(route_ctx):
    import time

    client, fresh_manager, run_store, adapter, tmp_path = route_ctx
    _register_universe(tmp_path, ["AAA"])

    r = client.post(
        "/research/desk/backfill/compute",
        json={"from_day": "2026-01-01", "to_day": "2026-03-01", "timeframes": ["5m"]},
    )
    assert r.status_code == 200 and r.json()["started"] is True

    deadline = time.time() + 15
    snapshot = None
    while time.time() < deadline:
        snapshot = client.get("/research/desk/backfill/compute").json()
        if snapshot is not None and snapshot["state"] != "running":
            break
        time.sleep(0.02)
    assert snapshot["state"] == "done"
    assert snapshot["progress"]["chunks_done"] == snapshot["progress"]["chunks_total"] > 0
    assert snapshot["progress"]["bars_recorded"] == snapshot["progress"]["chunks_total"]
    assert adapter.fetch_bars_calls

    runs = client.get("/research/desk/backfill/runs").json()
    assert len(runs["runs"]) == 1
    assert runs["latest"]["state"] == "done"
    assert runs["latest"]["vendor"] == "alpaca"
    assert runs["integrity_errors"] == []
    # The bulk list stays light: a run over thousands of chunks must not ship every one of them.
    assert "outcomes" not in runs["runs"][0]
    assert "outcomes" in runs["latest"]


def test_a_second_trigger_while_running_adopts_rather_than_starting_a_second_walk(route_ctx):
    client, _mgr, _runs, _adapter, tmp_path = route_ctx
    _register_universe(tmp_path, [f"S{i:02d}" for i in range(20)])

    first = client.post(
        "/research/desk/backfill/compute",
        json={"from_day": "2025-01-01", "to_day": "2026-06-01"},
    ).json()
    second = client.post(
        "/research/desk/backfill/compute",
        json={"from_day": "2025-01-01", "to_day": "2026-06-01"},
    ).json()

    if first["compute"]["state"] == "running":
        assert second["started"] is False
        assert second["compute"]["id"] == first["compute"]["id"]
    client.post("/research/desk/backfill/compute/cancel")


def test_cancelling_an_idle_backfill_is_a_409(route_ctx):
    client, _mgr, _runs, _adapter, _tmp_path = route_ctx

    r = client.post("/research/desk/backfill/compute/cancel")

    assert r.status_code == 409


def test_the_runs_route_is_honestly_empty_before_any_backfill(route_ctx):
    client, _mgr, _runs, _adapter, _tmp_path = route_ctx

    assert client.get("/research/desk/backfill/runs").json() == {
        "runs": [], "latest": None, "integrity_errors": []
    }


def test_the_compute_get_never_starts_a_walk(route_ctx):
    client, fresh_manager, _runs, adapter, tmp_path = route_ctx
    _register_universe(tmp_path, ["AAA"])

    assert client.get("/research/desk/backfill/compute").json() is None
    assert fresh_manager.snapshot() is None
    assert adapter.fetch_bars_calls == []
