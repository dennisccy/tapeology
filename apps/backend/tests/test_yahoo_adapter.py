"""Yahoo Finance adapter unit tests (era-5 "The Library", J-01).

Mocks the underlying ``yfinance`` call — ``monkeypatch.setattr(yfinance, "Ticker", ...)``, the SAME
lazy-import-patching pattern ``test_vendor_responsiveness.py`` already uses for Alpaca's own
lazily-imported SDK classes (``monkeypatch.setattr(hist, "StockHistoricalDataClient", ...)``) — so
the default suite makes NO network call. The interval-mapping + volume-coercion assertions are
driven by the committed REAL Yahoo capture (``tests/fixtures/yahoo/AAPL_1d_20260601_20260604.json``,
fetched live and frozen) so the mocked response is genuinely Yahoo-shaped, not arbitrary numbers.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest
import yfinance

from app.providers.adapters.base import MarketDataAdapter, RawBar
from app.providers.adapters.yahoo import _INTERVAL_MAP, YahooAdapter

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "yahoo" / "AAPL_1d_20260601_20260604.json"

START = datetime(2026, 6, 1, tzinfo=timezone.utc)
END = datetime(2026, 6, 4, tzinfo=timezone.utc)


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


def _fixture_dataframe(fixture: dict) -> pd.DataFrame:
    """Build the SAME shape ``yfinance.Ticker(...).history(...)`` returns (a tz-aware
    DatetimeIndex + Open/High/Low/Close/Volume columns) from the committed fixture's rows, so the
    adapter's real parsing code is exercised against genuinely Yahoo-shaped data."""
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


def _install_fake_ticker(monkeypatch, df: pd.DataFrame) -> list[dict]:
    """Patch ``yfinance.Ticker`` to return ``df`` from ``history()``, recording each call's exact
    kwargs. Returns the (initially empty) call log the test asserts against."""
    calls: list[dict] = []

    class _FakeTicker:
        def __init__(self, symbol: str) -> None:
            self.symbol = symbol

        def history(self, *, start, end, interval):
            calls.append({"symbol": self.symbol, "start": start, "end": end, "interval": interval})
            return df

    monkeypatch.setattr(yfinance, "Ticker", _FakeTicker)
    return calls


# --- identity + keyless availability -----------------------------------------------------------


def test_name_is_yahoo():
    assert YahooAdapter().name == "yahoo"


def test_is_available_is_always_true_keyless():
    assert YahooAdapter().is_available() is True


def test_satisfies_the_market_data_adapter_protocol():
    assert isinstance(YahooAdapter(), MarketDataAdapter)


# --- fetch_bars: the ONE real capability this iteration ----------------------------------------


def test_fetch_bars_maps_daily_timeframe_and_returns_real_shaped_bars(monkeypatch):
    fixture = _load_fixture()
    df = _fixture_dataframe(fixture)
    calls = _install_fake_ticker(monkeypatch, df)

    bars = YahooAdapter().fetch_bars(fixture["symbol"], START, END, "1d")

    assert calls == [{"symbol": fixture["symbol"], "start": START, "end": END, "interval": "1d"}]
    assert len(bars) == len(fixture["bars"]) == 3
    assert all(isinstance(b, RawBar) for b in bars)
    for bar, expected in zip(bars, fixture["bars"]):
        assert bar.symbol == fixture["symbol"]
        assert bar.timeframe == "1d"
        assert bar.epoch == expected["epoch"]
        assert bar.open == expected["open"]
        assert bar.high == expected["high"]
        assert bar.low == expected["low"]
        assert bar.close == expected["close"]
        assert bar.volume == expected["volume"]
        assert isinstance(bar.volume, int)  # explicit int coercion (never numpy.int64/float)


def test_fetch_bars_returns_bars_in_ascending_epoch_order(monkeypatch):
    fixture = _load_fixture()
    _install_fake_ticker(monkeypatch, _fixture_dataframe(fixture))
    bars = YahooAdapter().fetch_bars(fixture["symbol"], START, END, "1d")
    epochs = [b.epoch for b in bars]
    assert epochs == sorted(epochs)


def test_fetch_bars_uppercases_and_strips_the_symbol(monkeypatch):
    df = _fixture_dataframe(_load_fixture())
    calls = _install_fake_ticker(monkeypatch, df)

    bars = YahooAdapter().fetch_bars("  aapl  ", START, END, "1d")

    assert calls[0]["symbol"] == "AAPL"
    assert all(b.symbol == "AAPL" for b in bars)


def test_fetch_bars_returns_empty_tuple_for_an_unmapped_timeframe_this_iteration(monkeypatch):
    # "1h" is a REGISTERED CONFIG.bar_timeframes value but NOT YET mapped by this iteration's
    # adapter (J-02 scope, do not build ahead) -- honestly empty, no vendor call, never fabricated.
    calls = _install_fake_ticker(monkeypatch, pd.DataFrame())
    bars = YahooAdapter().fetch_bars("AAPL", START, END, "1h")
    assert bars == ()
    assert calls == []  # not even a vendor round-trip for an unmapped timeframe


def test_fetch_bars_returns_empty_tuple_for_an_empty_vendor_response(monkeypatch):
    _install_fake_ticker(monkeypatch, pd.DataFrame())  # unknown symbol / no data -- both empty
    bars = YahooAdapter().fetch_bars("ZZZZZNOTREAL", START, END, "1d")
    assert bars == ()


def test_interval_map_covers_only_the_daily_timeframe_this_iteration():
    # Explicit scope-boundary proof (do not build ahead of J-02's full 6-timeframe table).
    assert _INTERVAL_MAP == {"1d": "1d"}


# --- honestly bars-only: raise / empty / no-op, never fabricated -------------------------------


def test_fetch_historical_honestly_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        YahooAdapter().fetch_historical("AAPL", START, END)


def test_get_market_clock_honestly_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        YahooAdapter().get_market_clock()


def test_stream_live_honestly_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        YahooAdapter().stream_live("AAPL")


def test_search_symbols_honestly_returns_empty_list():
    assert YahooAdapter().search_symbols("AAPL") == []


def test_warm_symbol_universe_is_a_no_op_and_never_raises():
    assert YahooAdapter().warm_symbol_universe() is None
