"""The ``GET /research/tradability`` endpoint (era-5B capability 1, J-01) -- route-level
integration. Mirrors ``test_levels_api.py``'s ``ctx`` fixture (TestClient + temp bar dir + injected
``FakeAdapter``): a small ``"1d"`` series is recorded through the REAL ``POST /research/bars``
route, then ``GET /research/tradability`` is read back -- the full request path, not a direct
module call (``test_tradability.py`` covers the pure computation's exact values in isolation). The
committed real AAPL fixture is seeded directly into the temp bar dir (the ``test_levels_api.py`` /
``test_mcp_server.py`` technique) to prove J-01's pinned acceptance end to end through the real
route.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager
from app.providers.adapters.base import RawBar
from app.research.bars import BarStore
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore
from fakes import FakeAdapter

YAHOO_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "yahoo"
AAPL_DAILY_FIXTURE = "AAPL_1d_20260101_20260626.json"

SYMBOL = "TRDB"
TIMEFRAME = "1d"
_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)
_DAY = 86400.0


def _iso(day_index: int) -> str:
    return (_BASE + timedelta(days=day_index)).isoformat().replace("+00:00", "Z")


def _bar(day_index: int, high: float, low: float, close: float) -> RawBar:
    return RawBar(SYMBOL, TIMEFRAME, _BASE.timestamp() + day_index * _DAY, close, high, low, close, 1_000)


def _daily_bars() -> tuple[RawBar, ...]:
    # A small 5-day series: day 4 (2026-01-05) is the most recent bar, so a request inside
    # 2026-01-06 resolves its basis to day 4.
    return (
        _bar(0, 50.0, 40.0, 45.0),
        _bar(1, 60.0, 42.0, 55.0),
        _bar(2, 52.0, 41.0, 48.0),
        _bar(3, 58.0, 44.0, 50.0),
        _bar(4, 100.0, 90.0, 95.0),
    )


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    bar_dir = tmp_path / "bars"
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(bar_dir))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    manager.set_on_engine_created(registry.on_engine_created)
    with TestClient(app) as client:
        yield client, bar_dir
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    manager.set_on_engine_created(None)
    set_registry(None)
    app.dependency_overrides.pop(get_market_adapter, None)
    store.close()


def _inject_adapter(**kwargs) -> FakeAdapter:
    adapter = FakeAdapter(**kwargs)
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    return adapter


def _record_daily_bars(client) -> None:
    _inject_adapter(bars=_daily_bars())
    r = client.post(
        "/research/bars",
        json={"symbol": SYMBOL, "timeframe": TIMEFRAME, "start": _iso(0), "end": _iso(5)},
    )
    assert r.status_code == 200, r.text


# --- Happy path: the real route wires symbol/as_of through to compute_tradability ------------


def test_get_tradability_happy_path_through_the_real_route(ctx):
    client, _bar_dir = ctx
    _record_daily_bars(client)

    as_of = _iso(5)  # inside 2026-01-06 -- one session after the last recorded (2026-01-05) bar
    r = client.get("/research/tradability", params={"symbol": SYMBOL, "as_of": as_of})
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == SYMBOL
    assert body["as_of"] == as_of  # echoed VERBATIM (the get_levels precedent) -- never re-derived
    assert body["no_bar_series_for_symbol"] is False
    assert body["basis_as_of"] == "2026-01-05T00:00:00.000000Z"
    assert isinstance(body["bands"], list) and len(body["bands"]) >= 1
    for band in body["bands"]:
        assert set(band) == {
            "side", "price_low", "price_high", "class", "quality_score",
            "round_number", "member_count", "members",
        }
        assert band["side"] in ("support", "resistance")


def test_get_tradability_lowercase_symbol_is_normalized_to_stored_uppercase(ctx):
    client, _bar_dir = ctx
    _record_daily_bars(client)
    r = client.get("/research/tradability", params={"symbol": SYMBOL.lower(), "as_of": _iso(5)})
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == SYMBOL
    assert len(body["bands"]) >= 1


# --- The committed real AAPL fixture: J-01's pinned acceptance through the REAL route ----------


def _seed_yahoo_fixture_into_bar_dir(bar_dir: Path, fixture_name: str) -> None:
    bar_dir.mkdir(parents=True, exist_ok=True)  # BarStore only creates it lazily inside `record()`
    fixture = json.loads((YAHOO_FIXTURE_DIR / fixture_name).read_text())
    bars = [
        RawBar(
            fixture["symbol"], fixture["timeframe"], b["epoch"],
            b["open"], b["high"], b["low"], b["close"], b["volume"],
        )
        for b in fixture["bars"]
    ]
    BarStore(bar_dir).record(
        symbol=fixture["symbol"], timeframe=fixture["timeframe"],
        window_start_utc=fixture["start"], window_end_utc=fixture["end"],
        feed="yahoo", bars=bars,
    )


def test_get_tradability_aapl_pinned_resistance_band_through_the_real_route(ctx):
    """J-01's headline acceptance, through the REAL HTTP route (``test_tradability.py`` proves the
    identical numbers via a direct module call) -- AAPL as of the 2026-06-22 session: <=10 bands
    total, and the top resistance band contains both 300.48 and 302.07 with round_number=true and
    an inherited (non-null) class."""
    client, bar_dir = ctx
    _seed_yahoo_fixture_into_bar_dir(bar_dir, AAPL_DAILY_FIXTURE)

    as_of = "2026-06-22T15:00:00Z"
    r = client.get("/research/tradability", params={"symbol": "AAPL", "as_of": as_of})
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "AAPL"
    assert body["as_of"] == as_of
    assert body["no_bar_series_for_symbol"] is False
    assert body["basis_as_of"] == "2026-06-18T04:00:00.000000Z"

    bands = body["bands"]
    assert len(bands) <= 10
    resistance = [b for b in bands if b["side"] == "resistance"]
    support = [b for b in bands if b["side"] == "support"]
    assert len(resistance) <= 5
    assert len(support) <= 5

    pinned = next(
        b for b in resistance if b["price_low"] <= 300.48 and b["price_high"] >= 302.07
    )
    pinned_rank = resistance.index(pinned)
    assert pinned_rank in (0, 1), "the pinned resistance band must rank in the top 2 by quality score"
    assert pinned["round_number"] is True
    assert pinned["class"] is not None, "an inherited class must be present, never null"

    # REST == the module's own output, byte-for-byte (single source of truth: the route only
    # parses/echoes -- it recomputes nothing).
    from app.research.tradability import compute_tradability

    as_of_epoch = datetime.fromisoformat(as_of.replace("Z", "+00:00")).timestamp()
    direct = compute_tradability(BarStore(bar_dir), "AAPL", as_of_epoch, CONFIG)
    assert direct["bands"] == bands
    assert direct["basis_as_of"] == body["basis_as_of"]
    assert direct["no_bar_series_for_symbol"] == body["no_bar_series_for_symbol"]


def test_frozen_levels_output_is_byte_identical_after_a_tradability_request(ctx):
    """The critical single-source-of-truth guard, through the REAL routes: requesting the tradable
    map must not perturb ``GET /research/levels``' own output on the SAME store/as_of."""
    client, bar_dir = ctx
    _seed_yahoo_fixture_into_bar_dir(bar_dir, AAPL_DAILY_FIXTURE)
    levels_as_of = "2026-06-18T04:00:00Z"

    before = client.get("/research/levels", params={"symbol": "AAPL", "as_of": levels_as_of})
    assert before.status_code == 200

    tradability = client.get(
        "/research/tradability", params={"symbol": "AAPL", "as_of": "2026-06-22T15:00:00Z"}
    )
    assert tradability.status_code == 200

    after = client.get("/research/levels", params={"symbol": "AAPL", "as_of": levels_as_of})
    assert after.status_code == 200
    assert before.content == after.content


# --- Honest, distinct failure states -----------------------------------------------------------


def test_unrecorded_symbol_is_a_distinct_honest_state(ctx):
    client, _bar_dir = ctx
    _record_daily_bars(client)  # records SYMBOL only
    r = client.get("/research/tradability", params={"symbol": "NEVER-RECORDED", "as_of": _iso(5)})
    assert r.status_code == 200
    body = r.json()
    assert body["bands"] == []
    assert body["no_bar_series_for_symbol"] is True
    assert body["basis_as_of"] is None


def test_no_bar_series_recorded_at_all_is_the_same_distinct_state(ctx):
    client, _bar_dir = ctx  # nothing recorded at all this run
    r = client.get("/research/tradability", params={"symbol": SYMBOL, "as_of": _iso(5)})
    assert r.status_code == 200
    body = r.json()
    assert body["bands"] == []
    assert body["no_bar_series_for_symbol"] is True
    assert body["basis_as_of"] is None


def test_as_of_before_any_recorded_session_is_honest_empty_not_the_prior_state(ctx):
    client, _bar_dir = ctx
    _record_daily_bars(client)
    r = client.get("/research/tradability", params={"symbol": SYMBOL, "as_of": "2020-01-01T00:00:00Z"})
    assert r.status_code == 200
    body = r.json()
    assert body["bands"] == []
    assert body["no_bar_series_for_symbol"] is False  # distinct from the unrecorded-symbol state
    assert body["basis_as_of"] is None


# --- 422s: never a silent coercion, never a lookahead-leaking "now" default -------------------


def test_missing_as_of_is_422(ctx):
    client, _bar_dir = ctx
    r = client.get("/research/tradability", params={"symbol": SYMBOL})
    assert r.status_code == 422


def test_missing_symbol_is_422(ctx):
    client, _bar_dir = ctx
    r = client.get("/research/tradability", params={"as_of": _iso(5)})
    assert r.status_code == 422


def test_empty_symbol_is_422(ctx):
    client, _bar_dir = ctx
    r = client.get("/research/tradability", params={"symbol": "", "as_of": _iso(5)})
    assert r.status_code == 422
    assert "symbol" in r.json()["detail"]


def test_malformed_as_of_is_422(ctx):
    client, _bar_dir = ctx
    r = client.get("/research/tradability", params={"symbol": SYMBOL, "as_of": "not-a-date"})
    assert r.status_code == 422
    assert "as_of" in r.json()["detail"]
