"""``desk_screen_pins.py`` (Era B "The Desk", goal-desk-iter-36, J-21) -- the pin-resolution read
that answers, for a caller-supplied ``screen_date``, whether a screen run right now would reuse an
already-recorded snapshot or walk the universe fresh. Backend tests over planted, scoped stores
(goal.md step 6, never ``apps/backend/.data``) -- mirrors ``test_desk_screen_diff.py``'s /
``test_desk_screen_compute.py``'s own fixture conventions.

TC references below are this file's own copy of the phase spec's test-first contract
(``docs/phases/goal-desk-iter-36.md``): TC-1/TC-2 (already-recorded pins name the exact snapshot a
trigger reuses), TC-3/TC-4 (a planted bar-index row shifts the signature and a trigger then walks
fresh, leaving the earlier file untouched), TC-5 (honest empty before any universe), TC-6 (zero
``compute_tradability``/``BarStore`` calls -- structural, not just behavioral), TC-7 (byte-identical
repeat), TC-8 (422 on a missing ``screen_date``).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager as ws_manager
from app.providers.adapters.base import RawBar
from app.research import tradability as tradability_module
from app.research.bar_index import BarIndex
from app.research.bars import BarStore
from app.research.datasets import DatasetStore
from app.research.desk_screen import ScreenStore
from app.research.desk_screen_compute import run_screen_and_record
from app.research.desk_screen_pins import resolve_desk_screen_pins
from app.research.desk_universe import UniverseStore
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore

FIXTURE_UNIVERSE_DIR = Path(__file__).parent / "fixtures" / "universe"
REGISTERED_SNAPSHOT_PATH = FIXTURE_UNIVERSE_DIR / "universe-2026-07-25-817cc184bbb3.json"
FIXTURE_YAHOO_DIR = Path(__file__).parent / "fixtures" / "yahoo"
AAPL_DAILY_FIXTURE = "AAPL_1d_20260101_20260626.json"

SCREEN_DATE = "2026-06-22"


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


def _plant_extra_index_row(bar_index: BarIndex) -> None:
    """Plants ONE new ``bar_index`` row for a member/timeframe pair the fixture universe never
    seeded (AAPL/``1h``) -- changes that member's OWN frozen coverage (T-4: ``bar_index`` only,
    never touching ``BarStore``/the recorded screen files at all) so
    ``compute_bar_store_signature`` resolves a DIFFERENT signature than before (TC-3)."""
    bar_index.insert(
        {
            "symbol": "AAPL", "timeframe": "1h",
            "window_start_utc": "2026-06-20T00:00:00Z", "window_end_utc": "2026-06-21T00:00:00Z",
            "feed": "yahoo", "id": "planted-synthetic-series", "checksum": "0" * 64,
            "bar_count": 1,
        }
    )


@pytest.fixture
def real_ctx(tmp_path):
    """Mirrors ``test_desk_screen_compute.py``'s own ``real_ctx`` fixture exactly -- the REAL
    fixture universe (103 members) plus real AAPL daily bars, so pin resolution and an actual
    ``run_screen_and_record`` walk share the identical stores."""
    universe_store = _register_fixture_universe(tmp_path / "universe")
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "index.db"))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    dataset_store = DatasetStore(tmp_path / "datasets")
    screen_store = ScreenStore(tmp_path / "screen")
    return universe_store, bar_store, bar_index, dataset_store, screen_store


# ==================================================================================================
# TC-5: honest empty before any universe snapshot exists.
# ==================================================================================================


def test_tc5_no_universe_snapshot_is_an_honest_empty_payload(tmp_path):
    universe_store = UniverseStore(tmp_path / "universe")
    bar_index = BarIndex(str(tmp_path / "index.db"))
    screen_store = ScreenStore(tmp_path / "screen")

    result = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)

    assert result == {
        "screen_date": SCREEN_DATE,
        "as_of": f"{SCREEN_DATE}T23:59:59Z",
        "universe_snapshot_id": None,
        "config_fingerprint": CONFIG.config_fingerprint(),
        "bar_store_signature": None,
        "members_total": 0,
        "decision": {
            "action": "record",
            "screen_id": None,
            "reason": (
                f"no universe snapshot is registered yet, so nothing can be screened for "
                f"{SCREEN_DATE} -- fetch the universe first."
            ),
        },
        "recorded": None,
    }


# ==================================================================================================
# TC-1/TC-2: an already-recorded pin set names the exact snapshot ``run_screen_and_record`` reuses.
# ==================================================================================================


def test_tc1_tc2_resolved_pins_name_the_exact_snapshot_a_trigger_reuses(real_ctx):
    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx

    # Before any screen has ever been computed, the pins are already resolvable (universe + index
    # both exist) but nothing is recorded under them yet.
    before = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)
    assert before["recorded"] is None
    assert before["universe_snapshot_id"] == "universe-2026-07-25-817cc184bbb3"
    assert before["members_total"] == 103
    assert before["bar_store_signature"] is not None

    first, first_reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
    )
    assert first_reused is False

    after = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)

    # TC-1: every resolved pin is byte-identical to ``run_screen_and_record``'s OWN resolution --
    # the two can never disagree (same accessors, same order, same stores).
    assert after["screen_date"] == first["screen_date"]
    assert after["as_of"] == first["as_of"]
    assert after["universe_snapshot_id"] == first["universe_snapshot_id"]
    assert after["config_fingerprint"] == first["config_fingerprint"]
    assert after["bar_store_signature"] == first["bar_store_signature"]
    assert after["members_total"] == 103

    assert after["recorded"] is not None
    assert after["recorded"]["id"] == first["id"]
    assert after["recorded"]["screen_date"] == first["screen_date"]
    assert after["recorded"]["created_utc"] == first["created_utc"]
    assert after["recorded"]["bar_store_signature"] == first["bar_store_signature"]
    assert after["recorded"]["ranked_count"] == len(first["rows"])
    assert after["recorded"]["skipped_count"] == len(first["skipped"])

    # TC-2: a trigger for the same date reuses exactly the snapshot the pins already named --
    # J-18's shipped reuse behaviour, unchanged.
    second, second_reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
    )
    assert second_reused is True
    assert second["id"] == first["id"] == after["recorded"]["id"]


# ==================================================================================================
# TC-3/TC-4: one planted bar-index row INSIDE the screen date's own window shifts the signature; a
# trigger then walks fresh and REPLACES the earlier snapshot (one snapshot per date).
# ==================================================================================================


def test_tc3_tc4_a_planted_index_row_differs_the_signature_and_a_trigger_replaces_the_snapshot(
    real_ctx,
):
    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx

    first, first_reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
    )
    assert first_reused is False
    first_path = screen_store.root / f"{first['id']}.json"

    before_plant = resolve_desk_screen_pins(
        SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store
    )
    assert before_plant["recorded"]["id"] == first["id"]
    assert before_plant["decision"]["action"] == "reuse"

    # The planted row ends 2026-06-21, INSIDE this screen date's own as_of window -- bars this
    # screen genuinely could have consumed, so the date's completeness pin moves and the recorded
    # snapshot is honestly out of date.
    _plant_extra_index_row(bar_index)

    # TC-3: the same GET for the same date now resolves a DIFFERENT signature and an honest
    # ``recorded: null`` -- a run would walk, and the decision says so and names what it replaces.
    after_plant = resolve_desk_screen_pins(
        SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store
    )
    assert after_plant["bar_store_signature"] != before_plant["bar_store_signature"]
    assert after_plant["universe_snapshot_id"] == before_plant["universe_snapshot_id"]
    assert after_plant["recorded"] is None
    assert after_plant["decision"]["action"] == "replace"
    assert after_plant["decision"]["screen_id"] == first["id"]

    # TC-4: a trigger for the same date now walks every member fresh, records a NEW snapshot and
    # supersedes the stale one -- the date is left holding exactly one copy.
    second, second_reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
    )
    assert second_reused is False
    assert second["id"] != first["id"]
    assert second["bar_store_signature"] == after_plant["bar_store_signature"]
    assert not first_path.exists()

    records, errors = screen_store.list()
    assert errors == []
    assert {r["id"] for r in records} == {second["id"]}


def test_bars_arriving_AFTER_the_screen_date_never_re_dirty_it(real_ctx):
    """The whole point of the date-scoped pin. A top-up that only extends coverage a member ALREADY
    had past this date cannot change one row of it, so that date must stay reused -- zero walk, zero
    second file. Under the old unclamped 5-pin key this exact sequence wrote a second snapshot for
    the date, which is how the live store came to hold six dates with two copies each.

    The pair extended here is AAPL/``1d``, whose fixture coverage already ends 2026-06-26 -- past
    this screen's own 2026-06-22T23:59:59Z as_of, so its clamped tuple is already pinned AT as_of
    and settled. (A pair crossing as_of for the FIRST time is the opposite case and rightly does
    re-walk the date once: that is the session data the screen was missing arriving.)"""
    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx

    first, _reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
    )
    before = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)

    # A later top-up: AAPL/1d coverage now runs to 2026-08-04, further past this screen's as_of.
    bar_index.insert(
        {
            "symbol": "AAPL", "timeframe": "1d",
            "window_start_utc": "2026-06-26T00:00:00Z", "window_end_utc": "2026-08-04T00:00:00Z",
            "feed": "yahoo", "id": "planted-later-series", "checksum": "1" * 64, "bar_count": 1,
        }
    )

    after = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)

    # The UNCLAMPED pin moved (bars really did arrive) -- the date-scoped one did not, and the
    # decision follows the date-scoped one.
    assert after["bar_store_signature"] != before["bar_store_signature"]
    assert after["decision"]["action"] == "reuse"
    assert after["recorded"]["id"] == first["id"]

    second, second_reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
    )
    assert second_reused is True
    assert second["id"] == first["id"]

    records, errors = screen_store.list()
    assert errors == []
    assert {r["id"] for r in records} == {first["id"]}


# ==================================================================================================
# TC-6: zero ``compute_tradability`` calls and zero ``BarStore`` reads -- structural, not just
# behavioral (every ``BarStore`` method is poisoned to raise; the call still succeeds).
# ==================================================================================================


def test_tc6_zero_compute_tradability_calls_and_zero_bar_store_reads(real_ctx, monkeypatch):
    universe_store, _bar_store, bar_index, _dataset_store, screen_store = real_ctx

    def _boom(*_args, **_kwargs):
        raise AssertionError("resolve_desk_screen_pins must never call this")

    monkeypatch.setattr(tradability_module, "compute_tradability", _boom)
    for name in ("get", "list", "candles", "merged_candles", "merged_bars", "load_bars", "record"):
        monkeypatch.setattr(BarStore, name, _boom)

    result = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)

    # Resolves fine despite EVERY BarStore method and compute_tradability itself being poisoned --
    # proof this module never reaches either.
    assert result["universe_snapshot_id"] is not None
    assert result["bar_store_signature"] is not None


# ==================================================================================================
# TC-7: the same ``screen_date`` requested twice in succession is byte-identical (no wall-clock
# field, T-6).
# ==================================================================================================


def test_tc7_the_same_request_twice_in_succession_is_byte_identical(real_ctx):
    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
    run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
    )

    first = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)
    second = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)

    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


# ==================================================================================================
# ONE ``find_by_date`` per resolve -- the decision and ``recorded`` are two readings of a single
# lookup, never two lookups.
# ==================================================================================================


def test_the_resolve_asks_the_screen_store_for_the_date_exactly_once(real_ctx, monkeypatch):
    """``decision`` and ``recorded`` both need the date's recorded snapshot, and the store is
    immutable within a request -- so the two readings can only ever have agreed. Asking twice simply
    verified that snapshot twice per page load. Instrumented by call count rather than reasoned
    about (``test_desk_screen_diff.py``'s own instrumentation style), on BOTH branches: the ``reuse``
    one (which did the double lookup) and a date holding nothing. The body is asserted byte-identical
    to the one resolved before the instrumentation, so the saving costs no served value."""
    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
    run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
    )
    before = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)
    assert before["recorded"] is not None, "the reuse branch -- the one that read the date twice"

    calls: list[str] = []
    original_find_by_date = ScreenStore.find_by_date

    def _tracked_find_by_date(self, screen_date):
        calls.append(screen_date)
        return original_find_by_date(self, screen_date)

    monkeypatch.setattr(ScreenStore, "find_by_date", _tracked_find_by_date)

    after = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)

    assert calls == [SCREEN_DATE]
    assert json.dumps(after, sort_keys=True) == json.dumps(before, sort_keys=True)

    calls.clear()
    unrecorded = resolve_desk_screen_pins(
        "2026-06-19", universe_store, bar_index, CONFIG, screen_store
    )
    assert calls == ["2026-06-19"]
    assert unrecorded["recorded"] is None


# ==================================================================================================
# Route-level: TC-8 (422 on a missing ``screen_date``), honest empty at HTTP 200, basic wiring.
# ==================================================================================================


@pytest.fixture
def route_ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_DIR", str(tmp_path / "screen"))
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    with TestClient(app) as client:
        yield client, tmp_path
    for ticker in list(ws_manager._engines.keys()):
        ws_manager.stop(ticker)
    set_registry(None)
    app.dependency_overrides.pop(get_market_adapter, None)
    store.close()


def test_route_missing_screen_date_is_422(route_ctx):
    """TC-8: the endpoint never defaults to the current wall-clock date."""
    client, _tmp_path = route_ctx
    r = client.get("/research/desk/screen/pins")
    assert r.status_code == 422


def test_route_no_universe_snapshot_is_an_honest_empty_200(route_ctx):
    """TC-5 via HTTP."""
    client, _tmp_path = route_ctx
    r = client.get("/research/desk/screen/pins", params={"screen_date": SCREEN_DATE})
    assert r.status_code == 200
    assert r.json() == {
        "screen_date": SCREEN_DATE,
        "as_of": f"{SCREEN_DATE}T23:59:59Z",
        "universe_snapshot_id": None,
        "config_fingerprint": CONFIG.config_fingerprint(),
        "bar_store_signature": None,
        "members_total": 0,
        "decision": {
            "action": "record",
            "screen_id": None,
            "reason": (
                f"no universe snapshot is registered yet, so nothing can be screened for "
                f"{SCREEN_DATE} -- fetch the universe first."
            ),
        },
        "recorded": None,
    }


def test_route_names_the_recorded_snapshot_after_a_real_trigger(route_ctx):
    client, tmp_path = route_ctx
    UniverseStore(tmp_path / "universe").record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )

    r = client.post("/research/desk/screen/compute", json={"screen_date": SCREEN_DATE})
    assert r.status_code == 200
    assert r.json()["started"] is True

    import time

    deadline = time.time() + 5
    snap = None
    while time.time() < deadline:
        snap = client.get("/research/desk/screen/compute").json()
        if snap is not None and snap["state"] != "running":
            break
        time.sleep(0.02)
    assert snap["state"] == "done"

    r = client.get("/research/desk/screen/pins", params={"screen_date": SCREEN_DATE})
    assert r.status_code == 200
    body = r.json()
    assert body["recorded"] is not None
    assert body["recorded"]["id"] == snap["screen_id"]
    assert body["members_total"] == 1
