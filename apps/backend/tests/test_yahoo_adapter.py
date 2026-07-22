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
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest
import yfinance

from app.providers.adapters.base import MarketDataAdapter, NoDataForWindow, RawBar, UnsupportedTimeframe
from app.providers.adapters.yahoo import _INTERVAL_MAP, YahooAdapter, _resample_4h

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "yahoo" / "AAPL_1d_20260601_20260604.json"
# Real, live-captured AAPL 1h series (era-5 J-02) driving the 4h resampler tests below: two full
# trading sessions (7 bars each — a 6.5h regular session yields 4+3 real 1h bars) plus a THIRD
# session truncated to its first bar only (a genuine partial-window trailing bucket, not merely
# the every-day 3-bar remainder). See tests/fixtures/yahoo/ for the fetch window.
HOURLY_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "yahoo" / "AAPL_1h_20260601_20260603.json"

START = datetime(2026, 6, 1, tzinfo=timezone.utc)
END = datetime(2026, 6, 4, tzinfo=timezone.utc)


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


def _load_hourly_fixture() -> dict:
    return json.loads(HOURLY_FIXTURE_PATH.read_text())


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


def _raw_bars_from_fixture(fixture: dict, symbol: str = "AAPL") -> tuple[RawBar, ...]:
    """Build ``RawBar`` tuples straight from a committed fixture's rows (bypassing the vendor
    mock entirely) — used to unit-test ``_resample_4h`` as a pure function, independent of
    ``fetch_bars``'s own vendor-call plumbing."""
    return tuple(
        RawBar(symbol, fixture["timeframe"], b["epoch"], b["open"], b["high"], b["low"], b["close"], b["volume"])
        for b in fixture["bars"]
    )


def _expected_bucket(bars: list[dict]) -> dict:
    """The SAME open=first/high=max/low=min/close=last/volume=sum aggregation ``_resample_4h``
    performs, computed independently here directly from raw fixture rows (plain ``max``/``min``/
    ``sum`` over an explicit bucket slice) — an honest, non-circular check of the implementation."""
    return {
        "epoch": bars[0]["epoch"],
        "open": bars[0]["open"],
        "high": max(b["high"] for b in bars),
        "low": min(b["low"] for b in bars),
        "close": bars[-1]["close"],
        "volume": sum(b["volume"] for b in bars),
    }


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


@pytest.mark.parametrize("timeframe", ["8h", "1mo", "15m"])
def test_fetch_bars_raises_unsupported_timeframe_with_zero_vendor_calls(monkeypatch, timeframe):
    # "8h"/"1mo"/"15m" are REGISTERED CONFIG.bar_timeframes values era-5 Yahoo simply does not map
    # this era (era-5 enumerates exactly six: 1w/1d/4h/1h/5m/1m) -- statically knowable, zero
    # vendor calls, never fabricated (era-5 J-02 error-taxonomy case 1; repurposed from J-01's
    # scope-boundary test now that "1h" itself is mapped this iteration).
    calls = _install_fake_ticker(monkeypatch, pd.DataFrame())
    with pytest.raises(UnsupportedTimeframe) as exc_info:
        YahooAdapter().fetch_bars("AAPL", START, END, timeframe)
    assert timeframe in str(exc_info.value)
    assert calls == []  # not even a vendor round-trip for a Yahoo-unsupported timeframe


def test_fetch_bars_raises_no_data_for_window_for_an_empty_vendor_response(monkeypatch):
    # A MAPPED/servable timeframe whose specific symbol/window genuinely returns nothing from the
    # vendor (unknown symbol OR an out-of-retention window -- yfinance answers both with an empty
    # frame, verified live) raises the neutral NoDataForWindow (era-5 J-02 error-taxonomy case 2)
    # -- nothing fabricated, nothing written. Repurposed from J-01's "returns empty tuple" test now
    # that this case is an explicit, distinct signal rather than a silent empty answer.
    _install_fake_ticker(monkeypatch, pd.DataFrame())  # unknown symbol / no data -- both empty
    with pytest.raises(NoDataForWindow) as exc_info:
        YahooAdapter().fetch_bars("ZZZZZNOTREAL", START, END, "1d")
    assert "no data" in str(exc_info.value)
    assert "window" in str(exc_info.value)


def test_interval_map_covers_the_five_directly_fetched_era5_timeframes():
    # Explicit scope proof: exactly the FIVE directly-fetched era-5 timeframes ("4h" is
    # deliberately absent -- it is never requested from the vendor as its own interval; see
    # _resample_4h below). "1d" mapping stays byte-identical to J-01.
    assert _INTERVAL_MAP == {
        "1d": "1d",
        "1w": "1wk",
        "1h": "1h",
        "5m": "5m",
        "1m": "1m",
    }


# --- fetch_bars: the four NEWLY-mapped direct timeframes (era-5 J-02) --------------------------
# Each interval string was confirmed against the LIVE vendor during implementation (not assumed
# from documentation) -- see the live-integration test for the runnable proof. A lightweight
# synthetic one-row frame is enough here to prove the CORRECT ``interval=`` kwarg reaches the
# vendor call and the returned bar carries the requested neutral timeframe label; the daily case
# above already exercises the real-shaped-data parsing path end to end.


def _one_row_frame() -> pd.DataFrame:
    index = pd.to_datetime([1780320600.0], unit="s", utc=True)
    return pd.DataFrame(
        {"Open": [100.0], "High": [101.0], "Low": [99.0], "Close": [100.5], "Volume": [1000]},
        index=index,
    )


@pytest.mark.parametrize(
    "timeframe, vendor_interval",
    [("1w", "1wk"), ("1h", "1h"), ("5m", "5m"), ("1m", "1m")],
)
def test_fetch_bars_maps_each_newly_added_direct_timeframe(monkeypatch, timeframe, vendor_interval):
    # A RECENT three-day window, because Yahoo's intraday caps are measured against the wall clock:
    # the fixed June-2026 window used elsewhere in this module is now older than 1m's 30-day
    # retention, and the adapter (correctly) refuses it before any vendor call. This test is about
    # the interval STRING reaching the vendor, so it asks for a window every timeframe can serve.
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=3)
    calls = _install_fake_ticker(monkeypatch, _one_row_frame())
    bars = YahooAdapter().fetch_bars("AAPL", start, end, timeframe)
    assert calls == [{"symbol": "AAPL", "start": start, "end": end, "interval": vendor_interval}]
    assert len(bars) == 1
    assert bars[0].timeframe == timeframe
    assert bars[0].volume == 1000
    assert isinstance(bars[0].volume, int)


def test_fetch_bars_1h_returns_real_shaped_bars_from_the_committed_hourly_fixture(monkeypatch):
    # The SAME real-Yahoo-shaped-data proof the daily test above gives "1d", now for "1h" (the
    # fixture the 4h resampler tests below also drive).
    fixture = _load_hourly_fixture()
    calls = _install_fake_ticker(monkeypatch, _fixture_dataframe(fixture))

    bars = YahooAdapter().fetch_bars(fixture["symbol"], START, END, "1h")

    assert calls == [{"symbol": fixture["symbol"], "start": START, "end": END, "interval": "1h"}]
    assert len(bars) == len(fixture["bars"]) == 15
    for bar, expected in zip(bars, fixture["bars"]):
        assert bar.timeframe == "1h"
        assert bar.epoch == expected["epoch"]
        assert bar.open == expected["open"]
        assert bar.volume == expected["volume"]
        assert isinstance(bar.volume, int)


# --- 4h resample: era-5 J-02's one named new backend computation, confined to yahoo.py ----------
# Driven by the committed REAL AAPL 1h capture (tests/fixtures/yahoo/AAPL_1h_20260601_20260603.json)
# -- two full 6.5h trading sessions (7 real 1h bars each: a 4-bar bucket + a naturally-partial
# 3-bar bucket) plus a third session truncated to ITS first bar only (a genuinely partial trailing
# bucket from a mid-session fetch cutoff, not just the every-day 3-bar remainder). Expected values
# are computed INDEPENDENTLY in each test via ``_expected_bucket`` (plain max/min/sum over explicit
# fixture slices) -- never by calling ``_resample_4h`` on itself.


def test_resample_4h_ohlc_aggregation_exact_on_a_full_bucket():
    fixture = _load_hourly_fixture()
    hourly = _raw_bars_from_fixture(fixture)

    resampled = _resample_4h(hourly)

    assert len(resampled) == 5  # 4+3 (day 1) + 4+3 (day 2) + 1 (partial day 3)
    expected_first = _expected_bucket(fixture["bars"][0:4])
    first = resampled[0]
    assert first.symbol == "AAPL"
    assert first.timeframe == "4h"
    assert first.epoch == expected_first["epoch"]
    assert first.open == expected_first["open"]
    assert first.high == expected_first["high"]
    assert first.low == expected_first["low"]
    assert first.close == expected_first["close"]
    assert first.volume == expected_first["volume"]
    assert isinstance(first.volume, int)


def test_resample_4h_matches_independent_aggregation_candle_for_candle():
    fixture = _load_hourly_fixture()
    hourly = _raw_bars_from_fixture(fixture)
    resampled = _resample_4h(hourly)

    expected_slices = [
        fixture["bars"][0:4],
        fixture["bars"][4:7],
        fixture["bars"][7:11],
        fixture["bars"][11:14],
        fixture["bars"][14:15],
    ]
    assert len(resampled) == len(expected_slices)
    for bucket, expected_slice in zip(resampled, expected_slices):
        expected = _expected_bucket(expected_slice)
        assert bucket.epoch == expected["epoch"]
        assert bucket.open == expected["open"]
        assert bucket.high == expected["high"]
        assert bucket.low == expected["low"]
        assert bucket.close == expected["close"]
        assert bucket.volume == expected["volume"]


def test_resample_4h_buckets_align_to_the_real_session_open_not_naive_wall_clock():
    # Each bucket's epoch is the FIRST real 1h bar's OWN epoch (2026-06-01/02 09:30 ET and
    # 13:30 ET, 2026-06-03 09:30 ET) -- a real session-open/mid-session boundary the vendor itself
    # returned, never a naive ``epoch % 14400`` wall-clock grid.
    fixture = _load_hourly_fixture()
    hourly = _raw_bars_from_fixture(fixture)
    resampled = _resample_4h(hourly)

    assert [b.epoch for b in resampled] == [
        fixture["bars"][0]["epoch"],
        fixture["bars"][4]["epoch"],
        fixture["bars"][7]["epoch"],
        fixture["bars"][11]["epoch"],
        fixture["bars"][14]["epoch"],
    ]
    # A naive wall-clock ``epoch % 14400 == 0`` grid would NOT land on these real session times.
    for bucket in resampled:
        assert bucket.epoch % (4 * 3600) != 0


def test_resample_4h_partial_trailing_bucket_uses_only_the_completed_1h_bars():
    # Day 3 is truncated to ONE real 1h bar (a genuine mid-session fetch cutoff) -- the trailing
    # bucket must be built from exactly that one bar, never padded/forward-filled/backfilled with a
    # future bar to reach four.
    fixture = _load_hourly_fixture()
    hourly = _raw_bars_from_fixture(fixture)
    resampled = _resample_4h(hourly)

    trailing = resampled[-1]
    only_bar = fixture["bars"][14]
    assert trailing.open == only_bar["open"]
    assert trailing.high == only_bar["high"]
    assert trailing.low == only_bar["low"]
    assert trailing.close == only_bar["close"]
    assert trailing.volume == only_bar["volume"]  # NOT padded -- a single real bar's own volume


def test_resample_4h_every_days_second_bucket_is_naturally_partial_three_bars():
    # A 6.5h regular session yields 7 real 1h bars -- 4 + 3, never 4 + 4. This is a REAL fact about
    # regular trading hours (not a fetch-window artifact like the trailing-day case above), so the
    # second bucket of BOTH full days in the fixture is honestly a 3-bar bucket.
    fixture = _load_hourly_fixture()
    hourly = _raw_bars_from_fixture(fixture)
    resampled = _resample_4h(hourly)

    day1_second, day2_second = resampled[1], resampled[3]
    assert day1_second.volume == sum(b["volume"] for b in fixture["bars"][4:7])
    assert day2_second.volume == sum(b["volume"] for b in fixture["bars"][11:14])


def test_resample_4h_is_pure_and_byte_identical_across_two_identical_calls():
    fixture = _load_hourly_fixture()
    hourly = _raw_bars_from_fixture(fixture)
    assert _resample_4h(hourly) == _resample_4h(hourly)


def test_resample_4h_of_empty_input_is_honestly_empty():
    assert _resample_4h(()) == ()


def test_fetch_bars_4h_resamples_the_real_1h_fetch_end_to_end(monkeypatch):
    # The route-facing path: requesting "4h" fetches "1h" under the hood (proven via the recorded
    # vendor call) and returns the SAME resample ``_resample_4h`` computes directly.
    fixture = _load_hourly_fixture()
    calls = _install_fake_ticker(monkeypatch, _fixture_dataframe(fixture))

    bars = YahooAdapter().fetch_bars(fixture["symbol"], START, END, "4h")

    assert calls == [{"symbol": fixture["symbol"], "start": START, "end": END, "interval": "1h"}]
    assert len(bars) == 5
    assert all(b.timeframe == "4h" for b in bars)
    expected = _resample_4h(_raw_bars_from_fixture(fixture, symbol=fixture["symbol"]))
    assert bars == expected


def test_fetch_bars_4h_is_byte_identical_across_two_identical_requests(monkeypatch):
    fixture = _load_hourly_fixture()
    _install_fake_ticker(monkeypatch, _fixture_dataframe(fixture))
    first = YahooAdapter().fetch_bars(fixture["symbol"], START, END, "4h")
    second = YahooAdapter().fetch_bars(fixture["symbol"], START, END, "4h")
    assert first == second


def test_fetch_bars_4h_propagates_no_data_for_window_when_the_underlying_1h_fetch_is_empty(monkeypatch):
    # The 4h path is NOT special-cased around the honest-error taxonomy -- an empty underlying 1h
    # fetch (out-of-retention window / unknown symbol) propagates the SAME NoDataForWindow a direct
    # 1h request would raise, never a fabricated or empty-but-200 4h series.
    _install_fake_ticker(monkeypatch, pd.DataFrame())
    with pytest.raises(NoDataForWindow):
        YahooAdapter().fetch_bars("ZZZZZNOTREAL", START, END, "4h")


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
