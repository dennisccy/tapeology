"""Operator/gated REAL Yahoo Finance keyless daily bar fetch (era-5 "The Library", J-01) —
out-of-loop, not hermetic.

Per `.claude/core.md` (External Integration Testing) the hermetic suite alone is NOT sufficient
evidence the real integration works. This is the runnable proof that ``YahooAdapter.fetch_bars``
genuinely reaches Yahoo Finance and returns real daily OHLCV data, keyless — no credentials, no
market-hours gate (daily bars are historical, not a live session). It is GATED behind an explicit
opt-in so it is SKIPPED in the autonomous loop by default and never makes a network call by
accident (mirrors ``test_live_integration.py``'s existing Alpaca live-socket gate).

Run it (operator, any time — no credentials, no market hours needed):

    TAPEOLOGY_LIVE_INTEGRATION=1 .venv/bin/python -m pytest tests/test_yahoo_live_integration.py -v -s
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from app.providers.adapters.yahoo import YahooAdapter

pytestmark = pytest.mark.integration


def test_real_yahoo_keyless_daily_fetch_returns_real_bars():
    if os.environ.get("TAPEOLOGY_LIVE_INTEGRATION") != "1":
        pytest.skip("gated: set TAPEOLOGY_LIVE_INTEGRATION=1 to run the real Yahoo fetch check")

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
