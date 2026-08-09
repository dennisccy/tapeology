"""``desk_sessions.py`` -- the desk's one owner of "is this date a trading session", derived from
recorded daily bars rather than any hardcoded calendar. Backend tests over planted, scoped stores
(never ``apps/backend/.data``) -- mirrors ``test_desk_screen_pins.py``'s fixture conventions.

The contract under test, in one line: PROVABLY-not-a-session is the only claim this module makes,
and every other state (no evidence at all, a date past the last recorded daily bar, a date before
the first) fails OPEN so that no consumer refuses, filters or classifies on an unproven date."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager as ws_manager
from app.providers.adapters.base import RawBar
from app.research.bars import BarStore
from app.research.desk_sessions import (
    DESK_SESSION_ANCHOR_LIMIT,
    DESK_SESSION_ANCHOR_TIMEFRAME,
    is_known_non_session,
    recorded_session_dates,
    session_evidence,
)
from app.research.desk_universe import UniverseStore
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore

# A real trading week (Mon 2026-06-01 .. Fri 2026-06-05), the weekend that follows, and the Monday
# after it. Nothing here asserts a weekday NAME -- the point of the module is that it never needs
# to know one.
WEEK = ("2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04", "2026-06-05")
SATURDAY = "2026-06-06"
SUNDAY = "2026-06-07"
NEXT_MONDAY = "2026-06-08"


def _epoch(day: str) -> float:
    return datetime.fromisoformat(f"{day}T14:30:00+00:00").replace(tzinfo=timezone.utc).timestamp()


def _plant_daily(bar_store: BarStore, symbol: str, days: tuple[str, ...]) -> None:
    """One daily bar per named date, recorded exactly as a real fetch would record it."""
    bars = [
        RawBar(symbol, DESK_SESSION_ANCHOR_TIMEFRAME, _epoch(day), 10.0, 11.0, 9.0, 10.5, 1000)
        for day in days
    ]
    bar_store.record(
        symbol=symbol,
        timeframe=DESK_SESSION_ANCHOR_TIMEFRAME,
        window_start_utc=f"{days[0]}T00:00:00Z",
        window_end_utc=f"{days[-1]}T23:59:59Z",
        feed="yahoo",
        bars=bars,
    )


# ==================================================================================================
# The set itself.
# ==================================================================================================


def test_recorded_session_dates_are_exactly_the_dates_daily_bars_exist_for(tmp_path):
    bar_store = BarStore(tmp_path / "bars")
    _plant_daily(bar_store, "AAA", WEEK)

    assert recorded_session_dates(bar_store, ["AAA"]) == frozenset(WEEK)


def test_the_set_is_a_union_so_one_halted_member_cannot_erase_a_session(tmp_path):
    """A single symbol halted for a day the market traded would report a false non-session; the
    union over anchors is exactly what removes that failure mode."""
    bar_store = BarStore(tmp_path / "bars")
    _plant_daily(bar_store, "AAA", ("2026-06-01", "2026-06-02"))  # AAA missed 06-03
    _plant_daily(bar_store, "BBB", ("2026-06-01", "2026-06-03"))  # BBB missed 06-02

    assert recorded_session_dates(bar_store, ["AAA", "BBB"]) == frozenset(
        {"2026-06-01", "2026-06-02", "2026-06-03"}
    )


def test_only_the_daily_timeframe_is_read(tmp_path):
    """A member with a rich fine series and no daily bars contributes no session dates -- the
    anchor timeframe is the market-wide "this date traded" fact, and nothing else stands in."""
    bar_store = BarStore(tmp_path / "bars")
    bar_store.record(
        symbol="AAA", timeframe="5m",
        window_start_utc="2026-06-01T00:00:00Z", window_end_utc="2026-06-01T23:59:59Z",
        feed="yahoo",
        bars=[RawBar("AAA", "5m", _epoch("2026-06-01"), 10.0, 11.0, 9.0, 10.5, 1000)],
    )

    assert recorded_session_dates(bar_store, ["AAA"]) == frozenset()
    assert session_evidence(bar_store, ["AAA"])["anchor_symbols"] == []


def test_the_anchor_union_is_bounded_and_follows_the_callers_member_order(tmp_path):
    """The disclosure resolves on a GET, so the union spans a bounded handful of members rather
    than the whole universe -- and picks them in the caller's own order, so identical inputs pick
    identical anchors."""
    bar_store = BarStore(tmp_path / "bars")
    members = [f"S{i:02d}" for i in range(DESK_SESSION_ANCHOR_LIMIT + 3)]
    for symbol in members:
        _plant_daily(bar_store, symbol, WEEK)

    evidence = session_evidence(bar_store, members)
    assert evidence["anchor_symbols"] == members[:DESK_SESSION_ANCHOR_LIMIT]

    # A member with no daily series is skipped over rather than consuming an anchor slot.
    assert session_evidence(bar_store, ["NODAILY"] + members)["anchor_symbols"] == (
        members[:DESK_SESSION_ANCHOR_LIMIT]
    )


# ==================================================================================================
# The evidence block.
# ==================================================================================================


def test_evidence_reports_the_anchors_and_their_recorded_span(tmp_path):
    bar_store = BarStore(tmp_path / "bars")
    _plant_daily(bar_store, "AAA", WEEK)

    assert session_evidence(bar_store, ["AAA"]) == {
        "anchor_timeframe": "1d",
        "anchor_symbols": ["AAA"],
        "from": WEEK[0],
        "through": WEEK[-1],
        "sessions_total": len(WEEK),
    }


def test_no_daily_bars_at_all_is_an_honest_unknown_not_an_empty_calendar(tmp_path):
    bar_store = BarStore(tmp_path / "bars")

    evidence = session_evidence(bar_store, ["AAA"])
    assert evidence["anchor_symbols"] == []
    assert evidence["from"] is None and evidence["through"] is None
    assert evidence["sessions_total"] == 0


# ==================================================================================================
# ``is_known_non_session`` -- the whole fail-open contract.
# ==================================================================================================


def test_a_weekend_inside_the_evidence_span_is_a_proven_non_session(tmp_path):
    bar_store = BarStore(tmp_path / "bars")
    _plant_daily(bar_store, "AAA", WEEK + (NEXT_MONDAY,))
    sessions = recorded_session_dates(bar_store, ["AAA"])
    evidence = session_evidence(bar_store, ["AAA"])

    assert is_known_non_session(SATURDAY, sessions, evidence) is True
    assert is_known_non_session(SUNDAY, sessions, evidence) is True
    for day in WEEK:
        assert is_known_non_session(day, sessions, evidence) is False


def test_a_date_past_the_last_recorded_daily_bar_is_never_claimed_as_a_non_session(tmp_path):
    """The future is not something daily bars can prove anything about: a session that has not been
    recorded yet is indistinguishable from one that will never exist."""
    bar_store = BarStore(tmp_path / "bars")
    _plant_daily(bar_store, "AAA", WEEK)
    sessions = recorded_session_dates(bar_store, ["AAA"])
    evidence = session_evidence(bar_store, ["AAA"])

    assert is_known_non_session(SATURDAY, sessions, evidence) is False
    assert is_known_non_session(NEXT_MONDAY, sessions, evidence) is False
    assert is_known_non_session("2099-01-01", sessions, evidence) is False


def test_a_date_before_the_first_recorded_daily_bar_is_never_claimed_either(tmp_path):
    bar_store = BarStore(tmp_path / "bars")
    _plant_daily(bar_store, "AAA", WEEK)
    sessions = recorded_session_dates(bar_store, ["AAA"])
    evidence = session_evidence(bar_store, ["AAA"])

    assert is_known_non_session("2024-01-01", sessions, evidence) is False


def test_with_no_evidence_at_all_nothing_is_a_non_session(tmp_path):
    """The fail-open rule every consumer depends on: an empty store refuses nothing, filters
    nothing and classifies nothing."""
    bar_store = BarStore(tmp_path / "bars")
    sessions = recorded_session_dates(bar_store, ["AAA"])
    evidence = session_evidence(bar_store, ["AAA"])

    for day in (*WEEK, SATURDAY, SUNDAY, NEXT_MONDAY, "2024-01-01", "2099-01-01"):
        assert is_known_non_session(day, sessions, evidence) is False


def test_it_never_reads_the_wall_clock(tmp_path):
    """Identical inputs reproduce identical answers -- there is no ``now()`` anywhere in this
    module, so a date's classification never changes because time passed."""
    import inspect

    from app.research import desk_sessions

    source = inspect.getsource(desk_sessions)
    for banned in ("datetime.now(", "time.time(", "date.today("):
        assert banned not in source, f"{banned} makes a session classification time-dependent"


# ==================================================================================================
# The route.
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


def test_route_serves_sessions_and_proven_non_sessions_in_range(route_ctx):
    client, tmp_path = route_ctx
    UniverseStore(tmp_path / "universe").record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    _plant_daily(BarStore(tmp_path / "bars"), "AAA", WEEK + (NEXT_MONDAY,))

    r = client.get(
        "/research/desk/sessions", params={"from_day": WEEK[0], "to_day": NEXT_MONDAY}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["sessions"] == [*WEEK, NEXT_MONDAY]
    assert body["non_sessions"] == [SATURDAY, SUNDAY]
    assert body["evidence"]["anchor_symbols"] == ["AAA"]
    assert body["evidence"]["through"] == NEXT_MONDAY


def test_route_is_honestly_empty_before_any_universe_or_bars(route_ctx):
    client, _tmp_path = route_ctx

    r = client.get("/research/desk/sessions", params={"from_day": WEEK[0], "to_day": SUNDAY})
    assert r.status_code == 200
    assert r.json() == {
        "sessions": [],
        "non_sessions": [],
        "evidence": {
            "anchor_timeframe": "1d",
            "anchor_symbols": [],
            "from": None,
            "through": None,
            "sessions_total": 0,
        },
    }


def test_route_omitting_the_range_serves_the_whole_recorded_span(route_ctx):
    client, tmp_path = route_ctx
    UniverseStore(tmp_path / "universe").record(
        members=["AAA"], raw_members={"AAA": "AAA"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    _plant_daily(BarStore(tmp_path / "bars"), "AAA", WEEK)

    body = client.get("/research/desk/sessions").json()
    assert body["sessions"] == list(WEEK)
    # Without both bounds there is no range to walk, so nothing is claimed as a non-session.
    assert body["non_sessions"] == []
