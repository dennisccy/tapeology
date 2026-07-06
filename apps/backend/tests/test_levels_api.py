"""The ``GET /research/levels`` endpoint (era-4 capability 2, J-02) -- route-level integration.

Mirrors ``test_bars_api.py``'s ``ctx`` fixture (TestClient + temp bar dir + injected
``FakeAdapter``): a bar series is recorded through the REAL ``POST /research/bars`` route, then
``GET /research/levels`` is read back and asserted against exact values -- the full request path,
not a direct module call (``test_levels.py`` covers the pure computation in isolation).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager
from app.providers.adapters.base import RawBar
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore
from fakes import FakeAdapter

SYMBOL = "LVL"
TIMEFRAME = "4h"
_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)
_DAY = 86400.0


def _iso(day_index: int) -> str:
    from datetime import timedelta

    return (_BASE + timedelta(days=day_index)).isoformat().replace("+00:00", "Z")


def _bar(day_index: int, high: float, low: float, close: float) -> RawBar:
    return RawBar(SYMBOL, TIMEFRAME, _BASE.timestamp() + day_index * _DAY, close, high, low, close, 1_000)


def _swing_bars() -> tuple[RawBar, ...]:
    # The SAME engineered fixture as test_levels.py's `_swing_fixture`: four pivots, one with a
    # deliberate near-duplicate high (touch_count == 2), three isolated (touch_count == 1).
    return (
        _bar(0, 99.0, 90.0, 95.0),
        _bar(1, 130.0, 120.0, 125.0),
        _bar(2, 110.0, 100.0, 105.0),
        _bar(3, 115.0, 105.0, 110.0),
        _bar(4, 112.0, 102.0, 108.0),
        _bar(5, 130.03, 120.0, 125.0),
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


def _record_swing_bars(client) -> None:
    _inject_adapter(bars=_swing_bars())
    r = client.post(
        "/research/bars",
        json={"symbol": SYMBOL, "timeframe": TIMEFRAME, "start": _iso(0), "end": _iso(6)},
    )
    assert r.status_code == 200, r.text


# --- Happy path: exact price/timeframe/type/touch_count/strength -----------------------------------


def test_get_levels_happy_path_exact_values(ctx):
    client, _bar_dir = ctx
    _record_swing_bars(client)

    as_of = _iso(5)  # the last recorded bar's own instant -- every pivot fully confirmable
    r = client.get("/research/levels", params={"symbol": SYMBOL, "as_of": as_of})
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == SYMBOL
    assert body["as_of"] == as_of
    assert body["no_bar_series_for_symbol"] is False

    by_price = {lvl["price"]: lvl for lvl in body["levels"]}
    assert set(by_price) == {100.0, 102.0, 115.0, 130.0}
    weight = CONFIG.sr_timeframe_weights[TIMEFRAME]
    for price in (100.0, 102.0, 115.0):
        lvl = by_price[price]
        assert lvl["timeframe"] == TIMEFRAME
        assert lvl["type"] == "swing-pivot"
        assert lvl["touch_count"] == 1
        assert lvl["strength"] == weight
    assert by_price[130.0]["touch_count"] == 2
    assert by_price[130.0]["strength"] == weight * 2


def test_get_levels_lowercases_are_normalized_to_the_stored_uppercase_symbol(ctx):
    client, _bar_dir = ctx
    _record_swing_bars(client)
    r = client.get("/research/levels", params={"symbol": SYMBOL.lower(), "as_of": _iso(5)})
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == SYMBOL
    assert len(body["levels"]) == 4


# --- Honest, distinct failure states (three, never one bare ambiguous empty array) ------------------


def test_unrecorded_symbol_is_a_distinct_honest_state_not_an_ambiguous_empty_list(ctx):
    client, _bar_dir = ctx
    _record_swing_bars(client)  # records SYMBOL only
    r = client.get("/research/levels", params={"symbol": "NEVER-RECORDED", "as_of": _iso(5)})
    assert r.status_code == 200
    body = r.json()
    assert body["levels"] == []
    assert body["no_bar_series_for_symbol"] is True


def test_no_bar_series_recorded_at_all_is_the_same_distinct_state(ctx):
    client, _bar_dir = ctx  # nothing recorded at all this run
    r = client.get("/research/levels", params={"symbol": SYMBOL, "as_of": _iso(5)})
    assert r.status_code == 200
    body = r.json()
    assert body["levels"] == []
    assert body["no_bar_series_for_symbol"] is True


def test_as_of_before_any_recorded_bar_is_honest_no_levels_found_not_the_prior_state(ctx):
    client, _bar_dir = ctx
    _record_swing_bars(client)
    r = client.get("/research/levels", params={"symbol": SYMBOL, "as_of": "2020-01-01T00:00:00Z"})
    assert r.status_code == 200
    body = r.json()
    assert body["levels"] == []
    assert body["no_bar_series_for_symbol"] is False  # distinct from the unrecorded-symbol state


# --- 422s: never a silent coercion, never a lookahead-leaking "now" default -------------------------


def test_missing_as_of_is_422(ctx):
    client, _bar_dir = ctx
    r = client.get("/research/levels", params={"symbol": SYMBOL})
    assert r.status_code == 422


def test_missing_symbol_is_422(ctx):
    client, _bar_dir = ctx
    r = client.get("/research/levels", params={"as_of": _iso(5)})
    assert r.status_code == 422


def test_empty_symbol_is_422(ctx):
    client, _bar_dir = ctx
    r = client.get("/research/levels", params={"symbol": "", "as_of": _iso(5)})
    assert r.status_code == 422
    assert "symbol" in r.json()["detail"]


def test_malformed_as_of_is_422(ctx):
    client, _bar_dir = ctx
    r = client.get("/research/levels", params={"symbol": SYMBOL, "as_of": "not-a-date"})
    assert r.status_code == 422
    assert "as_of" in r.json()["detail"]
