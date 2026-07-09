"""Operator/gated REAL Yahoo Finance keyless bar fetch (era-5 "The Library", J-01 + J-02) —
out-of-loop, not hermetic.

Per `.claude/core.md` (External Integration Testing) the hermetic suite alone is NOT sufficient
evidence the real integration works. This is the runnable proof that ``YahooAdapter.fetch_bars``
genuinely reaches Yahoo Finance and returns real OHLCV data, keyless — no credentials, no
market-hours gate (all six era-5 timeframes are historical fetches, not a live session). It is
GATED behind an explicit opt-in so it is SKIPPED in the autonomous loop by default and never makes
a network call by accident (mirrors ``test_live_integration.py``'s existing Alpaca live-socket
gate).

J-02 adds: all six era-5 timeframes fetch real bars within their real retention windows; the live
``4h`` equals the deterministic resample of the live ``1h`` (``_resample_4h`` is a pure function —
this is the SAME computation the hermetic fixture-driven tests in ``test_yahoo_adapter.py``
already prove, now proven against the real vendor); a real out-of-retention ``1m`` window and a
real Yahoo-unsupported ``8h`` request each surface the explicit neutral error, live.

Run it (operator, any time — no credentials, no market hours needed):

    TAPEOLOGY_LIVE_INTEGRATION=1 .venv/bin/python -m pytest tests/test_yahoo_live_integration.py -v -s
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from app.providers.adapters.base import NoDataForWindow, UnsupportedTimeframe
from app.providers.adapters.yahoo import YahooAdapter, _resample_4h

pytestmark = pytest.mark.integration


def _skip_unless_live_integration() -> None:
    if os.environ.get("TAPEOLOGY_LIVE_INTEGRATION") != "1":
        pytest.skip("gated: set TAPEOLOGY_LIVE_INTEGRATION=1 to run the real Yahoo fetch check")


def test_real_yahoo_keyless_daily_fetch_returns_real_bars():
    _skip_unless_live_integration()

    adapter = YahooAdapter()
    assert adapter.is_available() is True  # keyless — always available, no credential gate

    symbol = os.environ.get("TAPEOLOGY_LIVE_SYMBOL", "AAPL").upper()
    # A recent-past 10-day window, ending a week ago (safely inside Yahoo's daily retention and
    # clear of any same-day/embargoed-bar ambiguity) — almost certainly spans several real trading
    # days regardless of weekends/holidays.
    end = datetime.now(timezone.utc) - timedelta(days=7)
    start = end - timedelta(days=10)

    bars = adapter.fetch_bars(symbol, start, end, "1d")

    assert len(bars) > 0, f"no real Yahoo daily bars returned for {symbol} over {start}..{end}"
    for bar in bars:
        assert bar.symbol == symbol
        assert bar.timeframe == "1d"
        assert bar.low <= bar.open <= bar.high
        assert bar.low <= bar.close <= bar.high
        assert bar.volume >= 0
        assert isinstance(bar.volume, int)
    epochs = [b.epoch for b in bars]
    assert epochs == sorted(epochs), "bars must be in ascending epoch order"


# --- era-5 J-02: the full six-timeframe set, incl. honestly-resampled 4h, live -------------------


def test_real_yahoo_all_six_era5_timeframes_fetch_within_real_retention():
    _skip_unless_live_integration()

    adapter = YahooAdapter()
    symbol = os.environ.get("TAPEOLOGY_LIVE_SYMBOL", "AAPL").upper()
    now = datetime.now(timezone.utc)

    # Each window is chosen comfortably INSIDE that timeframe's real Yahoo retention (goal.md:
    # 1m ~ last few days, 5m ~ 60 days, 1h/4h ~ 730 days, 1d/1w unlimited) with enough span to
    # cross at least one real trading day regardless of weekends/holidays.
    windows = {
        "1w": (now - timedelta(days=150), now - timedelta(days=2)),
        "1d": (now - timedelta(days=20), now - timedelta(days=2)),
        "4h": (now - timedelta(days=20), now - timedelta(days=2)),
        "1h": (now - timedelta(days=20), now - timedelta(days=2)),
        "5m": (now - timedelta(days=20), now - timedelta(days=2)),
        "1m": (now - timedelta(days=5), now - timedelta(days=1)),
    }
    for timeframe, (start, end) in windows.items():
        bars = adapter.fetch_bars(symbol, start, end, timeframe)
        assert len(bars) > 0, f"no real Yahoo {timeframe} bars for {symbol} over {start}..{end}"
        for bar in bars:
            assert bar.symbol == symbol
            assert bar.timeframe == timeframe
            assert bar.low <= bar.open <= bar.high
            assert bar.low <= bar.close <= bar.high
            assert bar.volume >= 0
            assert isinstance(bar.volume, int)
        epochs = [bar.epoch for bar in bars]
        assert epochs == sorted(epochs), f"{timeframe} bars must be in ascending epoch order"


def test_real_yahoo_4h_equals_the_deterministic_resample_of_real_1h():
    _skip_unless_live_integration()

    adapter = YahooAdapter()
    symbol = os.environ.get("TAPEOLOGY_LIVE_SYMBOL", "AAPL").upper()
    end = datetime.now(timezone.utc) - timedelta(days=2)
    start = end - timedelta(days=18)

    hourly = adapter.fetch_bars(symbol, start, end, "1h")
    four_hour = adapter.fetch_bars(symbol, start, end, "4h")

    assert len(hourly) > 0
    assert len(four_hour) > 0
    assert four_hour == _resample_4h(hourly), (
        "the live 4h fetch must equal the pure, deterministic resample of the live 1h fetch — "
        "4h is never a second, independent vendor call/computation"
    )


def test_real_yahoo_out_of_retention_1m_window_raises_no_data_for_window():
    _skip_unless_live_integration()

    adapter = YahooAdapter()
    symbol = os.environ.get("TAPEOLOGY_LIVE_SYMBOL", "AAPL").upper()
    # ~2 years back — empirically confirmed against the live vendor to be well outside 1m's real
    # (~7-day) retention window; yfinance answers with an empty frame, never an exception.
    end = datetime.now(timezone.utc) - timedelta(days=730)
    start = end - timedelta(days=2)

    with pytest.raises(NoDataForWindow):
        adapter.fetch_bars(symbol, start, end, "1m")


def test_real_yahoo_unsupported_8h_timeframe_raises_unsupported_timeframe():
    _skip_unless_live_integration()

    adapter = YahooAdapter()
    symbol = os.environ.get("TAPEOLOGY_LIVE_SYMBOL", "AAPL").upper()
    end = datetime.now(timezone.utc) - timedelta(days=7)
    start = end - timedelta(days=5)

    # Statically rejected before any vendor call — real network availability is irrelevant to this
    # outcome, but it is exercised here (live-gated) per the plan's explicit instruction to prove
    # it live alongside the other five/six-timeframe checks.
    with pytest.raises(UnsupportedTimeframe):
        adapter.fetch_bars(symbol, start, end, "8h")
