"""The screen's member walk divides across worker processes without changing the screen.

A ~101-member walk is the refresh chain's most expensive step, and every member is independent
CPU-bound work under one GIL — so it divides across processes. What must not move is the recorded
snapshot: the same rows, in the same rank order, with the same pins, byte for byte.

The suite walks in-process everywhere else (see ``conftest._walk_the_screen_in_process``); this file
is where the worker path is opted back in and held against the in-process one."""

from __future__ import annotations

import json

import pytest

from app.config import CONFIG
from app.research import desk_screen
from app.research.desk_screen import compute_screen

pytestmark = pytest.mark.usefixtures("_reset_store_verified_caches")


def _canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


@pytest.fixture
def seeded(tmp_path, monkeypatch):
    """A hermetic store holding enough members to cross the worker threshold, reusing the fixtures
    ``test_desk_screen.py`` already seeds from."""
    from tests.test_desk_screen import (  # noqa: PLC0415 -- shared fixture seeding, not a cycle
        AAPL_DAILY_FIXTURE,
        SCREEN_DATE,
        _load_yahoo_fixture,
        _register_fixture_universe,
        _seed_yahoo_fixture,
    )
    from app.research.bar_index import BarIndex
    from app.research.bars import BarStore
    from app.research.datasets import DatasetStore

    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    universe_store = _register_fixture_universe(tmp_path / "universe")
    bar_store = BarStore(tmp_path / "bars", verify_cache_db_path=str(tmp_path / "verify.db"))
    bar_index = BarIndex(str(tmp_path / "bar_index.db"))
    dataset_store = DatasetStore(tmp_path / "datasets")
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    return universe_store, bar_store, bar_index, dataset_store, SCREEN_DATE


def _screen(seeded, workers: str, monkeypatch, **kwargs) -> dict:
    universe_store, bar_store, bar_index, dataset_store, screen_date = seeded
    monkeypatch.setenv(desk_screen._SCREEN_WORKERS_ENV, workers)
    return compute_screen(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_date, **kwargs
    )


def test_the_parallel_walk_records_a_byte_identical_screen(seeded, monkeypatch) -> None:
    """The load-bearing equivalence. Compared as canonical JSON, so a reordered row, a changed
    float, or a key that moved would all fail — not just a shallow ``==``."""
    members = seeded[0].list()[0]
    assert len(members[-1]["members"]) >= desk_screen._MIN_MEMBERS_FOR_WORKERS, (
        "the fixture universe is too small to engage the worker path at all"
    )

    serial = _screen(seeded, "1", monkeypatch)
    parallel = _screen(seeded, "4", monkeypatch)

    assert _canonical(parallel) == _canonical(serial)
    assert [r["symbol"] for r in parallel["rows"]] == [r["symbol"] for r in serial["rows"]]
    assert parallel["bar_store_signature"] == serial["bar_store_signature"]
    assert parallel["screen_coverage_signature"] == serial["screen_coverage_signature"]


def test_progress_reports_every_member_once_in_member_order(seeded, monkeypatch) -> None:
    """A chunk that finishes first must not reorder the progress stream — an operator's counter
    reads the same sequence either way."""
    members = seeded[0].list()[0][-1]["members"]

    seen_serial: list[str] = []
    _screen(seeded, "1", monkeypatch, progress=lambda p: seen_serial.append(p["symbol"]))
    seen_parallel: list[str] = []
    _screen(seeded, "4", monkeypatch, progress=lambda p: seen_parallel.append(p["symbol"]))

    assert seen_parallel == seen_serial == list(members)


def test_a_cancelled_parallel_walk_records_no_fabricated_row(seeded, monkeypatch) -> None:
    """Cancelling before any chunk is handed out leaves an honest empty walk — never a partial row,
    never a fabricated one."""
    screen = _screen(seeded, "4", monkeypatch, should_abort=lambda: True)
    assert screen["rows"] == [] and screen["skipped"] == []
    # The pins are resolved before the walk, so they are still present and honest.
    assert screen["universe_snapshot_id"] is not None
    assert screen["config_fingerprint"] == CONFIG.config_fingerprint()


def test_a_small_walk_stays_in_process(seeded, monkeypatch) -> None:
    """Below the threshold the spawn cost outweighs the walk, so the pool must not engage — proven
    by a ``monkeypatch`` that only an in-process walk can observe."""
    universe_store, bar_store, bar_index, dataset_store, screen_date = seeded
    universe_store.record(
        members=["AAPL", "MSFT"], raw_members={"AAPL": "AAPL", "MSFT": "MSFT"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    monkeypatch.setenv(desk_screen._SCREEN_WORKERS_ENV, "4")

    seen: list[str] = []
    original = desk_screen.compute_tradability
    monkeypatch.setattr(
        desk_screen, "compute_tradability",
        lambda store, symbol, epoch, config: (seen.append(symbol), original(store, symbol, epoch, config))[1],
    )
    compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_date)
    assert seen == ["AAPL", "MSFT"]


@pytest.mark.parametrize(
    ("raw", "expected"), [(None, 4), ("", 4), ("1", 1), ("2", 2), ("0", 1), ("9", 4), ("nope", 4)]
)
def test_the_worker_knob_is_clamped_and_never_fails_a_run(monkeypatch, raw, expected) -> None:
    if raw is None:
        monkeypatch.delenv(desk_screen._SCREEN_WORKERS_ENV, raising=False)
    else:
        monkeypatch.setenv(desk_screen._SCREEN_WORKERS_ENV, raw)
    assert desk_screen._screen_workers() == expected


def test_the_pool_never_outlives_the_walk() -> None:
    """The era-5C boundary this pool is the considered exception to: children are created inside an
    already-triggered job and torn down with it, so the always-on server holds none between runs.
    Pinned structurally — the executor must be used as a context manager, never stashed."""
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(desk_screen._member_reads).lstrip())
    pooled = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "ProcessPoolExecutor"
    ]
    assert len(pooled) == 1, "the walk should construct exactly one pool"
    withs = [
        item.context_expr for node in ast.walk(tree) if isinstance(node, ast.With)
        for item in node.items
    ]
    assert any(expr is pooled[0] for expr in withs), (
        "the ProcessPoolExecutor must be a `with` context so its workers die with the walk"
    )
