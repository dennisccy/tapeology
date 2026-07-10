"""The ``GET /research/levels`` endpoint (era-4 capabilities 2 + 3, J-02 + J-03) -- route-level
integration.

Mirrors ``test_bars_api.py``'s ``ctx`` fixture (TestClient + temp bar dir + injected
``FakeAdapter``): a bar series is recorded through the REAL ``POST /research/bars`` route, then
``GET /research/levels`` is read back and asserted against exact values -- the full request path,
not a direct module call (``test_levels.py`` covers the pure level/confluence computation in
isolation). The committed real PG bar-fixture pair is also seeded directly into the temp bar dir
(the ``test_mcp_server.py`` technique) to prove the confluence-zones field end to end on real data.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest
import yfinance
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager
from app.providers.adapters.base import RawBar
from app.research.bars import BarStore
from app.research.levels import compute_levels
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore
from fakes import FakeAdapter

FIXTURE_BAR_DIR = Path(__file__).parent / "fixtures" / "bars"
YAHOO_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "yahoo"

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

    # J-03: this single-timeframe fixture's four pivots are all far apart in price (the closest
    # gap is 200+ bps, well outside the confluence band) -- an honest empty zones list, never
    # fabricated (the pure-computation matrix lives in test_levels.py; this proves the SAME
    # honesty holds through the real route).
    assert body["confluence_zones"] == []


def test_get_levels_confluence_zones_exact_values_on_the_committed_pg_fixture(ctx):
    """The committed real PG bar-fixture pair (era-4 J-01, 2 timeframes: 1h + 1d), seeded directly
    into the temp bar dir, read back through the REAL route -- proving `confluence_zones` is served
    end to end on real data, not just via a direct module call (`test_levels.py`'s
    ``test_committed_fixture_confluence_zones_exact_values_keyless`` owns the exhaustive exact-value
    proof; this asserts the SAME shape survives the route's serialization unchanged)."""
    client, bar_dir = ctx
    bar_dir.mkdir(parents=True, exist_ok=True)  # BarStore only creates it lazily inside `record()`
    fixtures = list(FIXTURE_BAR_DIR.glob("*.json"))
    assert fixtures, "the committed bar fixture directory must not be empty"
    for fixture in fixtures:
        shutil.copy(fixture, bar_dir / fixture.name)

    as_of = "2026-06-09T21:00:00Z"  # at/after both fixtures' window_end_utc
    r = client.get("/research/levels", params={"symbol": "PG", "as_of": as_of})
    assert r.status_code == 200
    body = r.json()
    assert body["no_bar_series_for_symbol"] is False
    zones = body["confluence_zones"]
    assert len(zones) == 6
    assert [z["class"] for z in zones] == ["C", "C", "C", "C", "C", "B"]

    cross_tf_zone = zones[-1]
    assert [m["price"] for m in cross_tf_zone["levels"]] == [148.06, 148.095, 148.23]
    assert {m["timeframe"] for m in cross_tf_zone["levels"]} == {"1h", "1d"}
    assert cross_tf_zone["score"] == 12.0


# --- era-5 J-04: real S/R levels + confluence zones on REAL Yahoo bars (not the synthetic PG
# fixture) -- proves the SAME frozen `research/levels.py` populates from `feed="yahoo"` data with
# zero second computation path. Seeding mirrors `test_bars_api.py`'s established technique: only
# the `yfinance.Ticker` boundary is mocked (no network), so `YahooAdapter`, `BarStore.record`, and
# the REAL route all run end to end -- exactly as J-01/J-02 already prove for `POST /research/bars`,
# now carried through to `GET /research/levels`. The two fixtures below are the SAME committed
# `tests/fixtures/yahoo/*.json` files `test_bars_api.py` uses (real captured AAPL OHLCV, roughly
# $305-$317) -- never `tests/fixtures/bars/` (the iter-1 lesson: that directory's own frozen test
# blanket-asserts `feed=="sip"`).


def _load_yahoo_fixture(name: str) -> dict:
    """The committed real-Yahoo RAW-CAPTURE fixture format (``{symbol, timeframe, start, end,
    bars: [{epoch, open, high, low, close, volume}]}``) -- distinct from the ``BarStore``
    per-record file format the PG fixture uses. Mirrors ``test_bars_api.py``'s helper of the same
    name."""
    return json.loads((YAHOO_FIXTURE_DIR / name).read_text())


def _yahoo_fixture_dataframe(fixture: dict) -> pd.DataFrame:
    index = pd.to_datetime([b["epoch"] for b in fixture["bars"]], unit="s", utc=True)
    return pd.DataFrame(
        {
            "Open": [b["open"] for b in fixture["bars"]],
            "High": [b["high"] for b in fixture["bars"]],
            "Low": [b["low"] for b in fixture["bars"]],
            "Close": [b["close"] for b in fixture["bars"]],
            "Volume": [b["volume"] for b in fixture["bars"]],
        },
        index=index,
    )


def _install_fake_yahoo_ticker(monkeypatch, dataframes_by_interval: dict[str, pd.DataFrame]) -> None:
    """The ``test_bars_api.py::_install_fake_yahoo_ticker`` technique, keyed by ``yfinance``
    interval string so a SINGLE test can seed more than one timeframe (J-04 needs both the
    committed 1d AND 1h Yahoo fixtures for a cross-timeframe confluence zone, mirroring the PG
    fixture pair)."""

    class _FakeTicker:
        def __init__(self, symbol: str) -> None:
            self.symbol = symbol

        def history(self, *, start, end, interval):
            return dataframes_by_interval[interval]

    monkeypatch.setattr(yfinance, "Ticker", _FakeTicker)


def _record_yahoo_fixture(client, fixture: dict) -> dict:
    r = client.post(
        "/research/bars",
        json={
            "symbol": fixture["symbol"],
            "timeframe": fixture["timeframe"],
            "start": fixture["start"],
            "end": fixture["end"],
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["bar_series"]


def test_get_levels_confluence_zones_exact_values_on_the_committed_yahoo_fixture(ctx, monkeypatch):
    """The committed real Yahoo bar-fixture pair (era-5 J-01, 2 timeframes: 1h + 1d), recorded
    through the REAL route -- proving `confluence_zones` is served end to end on REAL Yahoo data,
    mirroring `test_get_levels_confluence_zones_exact_values_on_the_committed_pg_fixture` above but
    sourced from `tests/fixtures/yahoo/`. This is J-04's defining acceptance: the previously-empty
    keyless structure surface now shows real, non-empty levels + an A/B/C zone once Yahoo bars are
    stored for a symbol -- with ZERO new computation (this test only proves the EXISTING, frozen
    `research/levels.py` output on new input; exact values verified directly against the real
    fixture data, independently confirmed via a standalone probe before this test was written)."""
    client, _bar_dir = ctx
    daily = _load_yahoo_fixture("AAPL_1d_20260601_20260604.json")
    hourly = _load_yahoo_fixture("AAPL_1h_20260601_20260603.json")
    _install_fake_yahoo_ticker(
        monkeypatch, {"1d": _yahoo_fixture_dataframe(daily), "1h": _yahoo_fixture_dataframe(hourly)}
    )
    daily_meta = _record_yahoo_fixture(client, daily)
    hourly_meta = _record_yahoo_fixture(client, hourly)
    assert daily_meta["feed"] == "yahoo"
    assert hourly_meta["feed"] == "yahoo"

    as_of = "2026-06-05T00:00:00Z"  # at/after both fixtures' actual last bar and declared window_end
    r = client.get("/research/levels", params={"symbol": "AAPL", "as_of": as_of})
    assert r.status_code == 200
    body = r.json()
    assert body["no_bar_series_for_symbol"] is False
    assert len(body["levels"]) == 14

    zones = body["confluence_zones"]
    assert len(zones) == 4
    assert [z["class"] for z in zones] == ["B", "B", "B", "B"]

    cross_tf_zone = zones[-1]
    assert [m["price"] for m in cross_tf_zone["levels"]] == [
        315.20001220703125,
        315.45001220703125,
        315.45001220703125,
    ]
    assert {m["timeframe"] for m in cross_tf_zone["levels"]} == {"1h", "1d"}
    assert cross_tf_zone["score"] == 12.0


def test_levels_no_lookahead_holds_on_real_committed_yahoo_bars(ctx, monkeypatch):
    """era-5 J-04's no-lookahead acceptance: the SAME lookahead-free proof
    `test_levels.py::test_lookahead_free_a_level_at_t_is_unchanged_by_any_bar_after_t` already
    establishes on the PG fixture, re-run on REAL Yahoo bars recorded through the REAL route -- a
    level computed at `as_of` T is unchanged whether or not bars timestamped strictly after T exist
    in the store. Uses the committed 15-bar hourly Yahoo fixture, truncated at bar index 6
    (2026-06-01T19:30:00Z) -- squarely inside the window, well before the last bar (2026-06-03
    13:30Z). The "full" side goes through the REAL route (real Yahoo-shaped data, mocked only at the
    `yfinance.Ticker` boundary); the "truncated" side calls the frozen `compute_levels` directly
    over a store holding ONLY the bars at-or-before T -- both must agree byte-for-byte."""
    client, bar_dir = ctx
    hourly = _load_yahoo_fixture("AAPL_1h_20260601_20260603.json")
    _install_fake_yahoo_ticker(monkeypatch, {"1h": _yahoo_fixture_dataframe(hourly)})
    recorded = _record_yahoo_fixture(client, hourly)
    assert recorded["feed"] == "yahoo"

    as_of = "2026-06-01T19:30:00Z"  # bar index 6's own ts
    full = client.get("/research/levels", params={"symbol": "AAPL", "as_of": as_of})
    assert full.status_code == 200
    full_body = full.json()
    assert full_body["levels"], "the truncated as-of view must still be non-vacuous"

    full_bars = BarStore(bar_dir).load_bars(recorded["id"])
    as_of_epoch = datetime(2026, 6, 1, 19, 30, tzinfo=timezone.utc).timestamp()
    truncated_bars = [b for b in full_bars if b.epoch <= as_of_epoch]
    assert len(truncated_bars) < len(full_bars), "the truncation must actually drop bars"

    import tempfile

    with tempfile.TemporaryDirectory() as td:
        truncated_store = BarStore(Path(td) / "bars")
        truncated_store.record(
            symbol="AAPL",
            timeframe="1h",
            window_start_utc=hourly["start"],
            window_end_utc=as_of,
            feed="yahoo",
            bars=truncated_bars,
        )
        truncated_result = compute_levels(truncated_store, "AAPL", as_of_epoch, CONFIG)

    assert truncated_result["levels"] == full_body["levels"]
    assert truncated_result["confluence_zones"] == full_body["confluence_zones"]
    assert truncated_result["no_bar_series_for_symbol"] == full_body["no_bar_series_for_symbol"]


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
    assert body["confluence_zones"] == []


def test_no_bar_series_recorded_at_all_is_the_same_distinct_state(ctx):
    client, _bar_dir = ctx  # nothing recorded at all this run
    r = client.get("/research/levels", params={"symbol": SYMBOL, "as_of": _iso(5)})
    assert r.status_code == 200
    body = r.json()
    assert body["levels"] == []
    assert body["no_bar_series_for_symbol"] is True
    assert body["confluence_zones"] == []


def test_as_of_before_any_recorded_bar_is_honest_no_levels_found_not_the_prior_state(ctx):
    client, _bar_dir = ctx
    _record_swing_bars(client)
    r = client.get("/research/levels", params={"symbol": SYMBOL, "as_of": "2020-01-01T00:00:00Z"})
    assert r.status_code == 200
    body = r.json()
    assert body["levels"] == []
    assert body["no_bar_series_for_symbol"] is False  # distinct from the unrecorded-symbol state
    assert body["confluence_zones"] == []


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
