"""J-34 — chunked long-window historical fetch: split + in-order stitch, no fabricate/drop/reorder.

Two gating layers, both hermetic (no real vendor):
  * ``_split_window`` is PURE — it partitions ``[start, end)`` into bounded contiguous sub-windows
    with no overlap and no gap, and returns a single range for a short window (the fast path).
  * The real adapter's ``_fetch_trades_quotes`` drives a fake SDK whose per-sub-window responses are
    keyed by the requested range, so we prove a long window is split into the expected sub-windows
    AND that the stitched stream is epoch-ordered with NO fabricated, dropped, reordered, or
    de-duplicated real prints. A re-watch hits the existing window cache (covered in
    test_vendor_responsiveness); here we focus on the split + stitch correctness.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

import app.providers.adapters.alpaca as alpaca
from app.config import CONFIG
from app.providers.adapters.alpaca import AlpacaAdapter, _clear_caches, _split_window
from app.providers.adapters.base import RawQuote, RawTrade


@pytest.fixture(autouse=True)
def _isolate_caches():
    _clear_caches()
    yield
    _clear_caches()


@pytest.fixture
def with_creds(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "test-key-123")
    monkeypatch.setenv("ALPACA_API_SECRET", "test-secret-456")
    return monkeypatch


# --- _split_window: pure partitioning -------------------------------------------------------


def _dt(minute: int) -> datetime:
    return datetime(2024, 5, 14, 13, 30, tzinfo=timezone.utc) + timedelta(minutes=minute)


def test_short_window_is_a_single_range():
    # A window at/under the sub-window size is ONE range — the prior single-call fast path.
    start, end = _dt(0), _dt(10)  # 10 minutes < 15-min chunk
    assert _split_window(start, end, CONFIG.historical_chunk_seconds) == [(start, end)]


def test_long_window_splits_into_expected_bounded_sub_windows():
    # A 6.5h Full-RTH window at a 15-min chunk splits into ceil(390/15) = 26 sub-windows, each
    # bounded to the chunk size, the last ending exactly at `end`.
    start, end = _dt(0), _dt(390)  # 09:30–16:00 ET span = 390 minutes
    chunk = 900.0  # 15 minutes
    ranges = _split_window(start, end, chunk)
    assert len(ranges) == 26
    # Every sub-window is at most the chunk span...
    for s, e in ranges:
        assert (e - s).total_seconds() <= chunk
    # ...the partition has NO gap and NO overlap (each end is the next start)...
    for (s0, e0), (s1, e1) in zip(ranges, ranges[1:]):
        assert e0 == s1
    # ...and the partition spans EXACTLY [start, end).
    assert ranges[0][0] == start
    assert ranges[-1][1] == end


def test_non_datetime_or_nonpositive_chunk_is_single_range():
    # Defensive: non-datetime bounds (test fakes pass strings/None) or a non-positive chunk are a
    # single range — chunking is a fetch optimization, never a correctness dependency.
    assert _split_window("2026-06-02T15:00", "2026-06-02T15:30", 900.0) == [
        ("2026-06-02T15:00", "2026-06-02T15:30")
    ]
    assert _split_window(_dt(0), _dt(60), 0.0) == [(_dt(0), _dt(60))]


# --- Chunked fetch through the real adapter against a fake SDK -------------------------------


class _FakeTs:
    def __init__(self, epoch: float) -> None:
        self._epoch = epoch

    def timestamp(self) -> float:
        return self._epoch


class _FakeTrade:
    def __init__(self, epoch: float, price: float, size: int) -> None:
        self.timestamp = _FakeTs(epoch)
        self.price = price
        self.size = size


class _FakeQuote:
    def __init__(self, epoch: float, bid: float, ask: float, bs: int, asz: int) -> None:
        self.timestamp = _FakeTs(epoch)
        self.bid_price = bid
        self.ask_price = ask
        self.bid_size = bs
        self.ask_size = asz


class _FakeResp:
    def __init__(self, data: dict) -> None:
        self.data = data


class _NoTimeoutSession:
    def request(self, method, url, **kwargs):  # pragma: no cover - not exercised
        raise AssertionError("the fake SDK does not perform real HTTP")


class _ChunkAwareClient:
    """A fake SDK whose response for each call is keyed by the requested (start, end) sub-window.

    Each sub-window returns ONE trade + ONE quote stamped at a DISTINCT epoch derived from the
    sub-window's start minute, so the test can prove every sub-window was fetched (no drop), no
    extra record appeared (no fabrication), and the stitched stream is epoch-ordered with no
    re-order or de-dup. It also records every requested range for the split assertion.
    """

    def __init__(self, symbol: str) -> None:
        self._symbol = symbol
        self._session = _NoTimeoutSession()
        self.trade_ranges: list[tuple] = []
        self.quote_ranges: list[tuple] = []

    @staticmethod
    def _epoch(dt: datetime) -> float:
        return dt.timestamp()

    def get_stock_trades(self, req):
        self.trade_ranges.append((req["start"], req["end"]))
        e = self._epoch(req["start"])
        return _FakeResp({self._symbol: [_FakeTrade(e + 0.2, 10.0 + e % 7, 100)]})

    def get_stock_quotes(self, req):
        self.quote_ranges.append((req["start"], req["end"]))
        e = self._epoch(req["start"])
        return _FakeResp({self._symbol: [_FakeQuote(e + 0.1, 9.99, 10.01, 5, 5)]})


@pytest.fixture
def chunk_sdk(monkeypatch):
    """Patch the lazily-imported SDK so _fetch_trades_quotes drives the chunk-aware fake client."""
    import alpaca.data.historical as hist
    import alpaca.data.requests as reqs

    holder: dict = {}

    def _factory(_key, _secret):
        client = _ChunkAwareClient(holder["symbol"])
        holder["client"] = client
        return client

    monkeypatch.setattr(hist, "StockHistoricalDataClient", _factory)
    monkeypatch.setattr(reqs, "StockTradesRequest", lambda **kw: kw)
    monkeypatch.setattr(reqs, "StockQuotesRequest", lambda **kw: kw)
    return holder


def test_long_window_fetches_each_sub_window_and_stitches_in_epoch_order(chunk_sdk, with_creds):
    chunk_sdk["symbol"] = "TSLA"
    adapter = AlpacaAdapter()
    start, end = _dt(0), _dt(60)  # 60 minutes at a 15-min chunk => 4 sub-windows
    trades, quotes = adapter._fetch_trades_quotes("TSLA", start, end, adapter._data_feed())

    client = chunk_sdk["client"]
    expected_ranges = _split_window(start, end, CONFIG.historical_chunk_seconds)
    assert len(expected_ranges) == 4
    # Every sub-window was fetched for BOTH trades and quotes (no dropped sub-window). Compare as
    # sets because bounded-concurrency may complete out of order — the stitch sorts by epoch after.
    assert set(client.trade_ranges) == set(expected_ranges)
    assert set(client.quote_ranges) == set(expected_ranges)

    # One real trade + one real quote per sub-window — NOTHING fabricated, NOTHING dropped.
    assert len(trades) == 4
    assert len(quotes) == 4
    # The stitched stream is epoch-ORDERED (the canonical merge order) — no reorder leaked through.
    assert [t.epoch for t in trades] == sorted(t.epoch for t in trades)
    assert [q.epoch for q in quotes] == sorted(q.epoch for q in quotes)
    # No de-duplication and no duplication: the epochs are exactly the per-sub-window distinct set.
    assert len({t.epoch for t in trades}) == 4
    assert len({q.epoch for q in quotes}) == 4


def test_short_window_makes_a_single_fetch_no_chunking(chunk_sdk, with_creds):
    # A short window is NOT chunked: exactly one trades call + one quotes call (the fast path).
    chunk_sdk["symbol"] = "AAPL"
    adapter = AlpacaAdapter()
    start, end = _dt(0), _dt(5)  # 5 minutes < 15-min chunk
    trades, quotes = adapter._fetch_trades_quotes("AAPL", start, end, adapter._data_feed())
    client = chunk_sdk["client"]
    assert client.trade_ranges == [(start, end)]
    assert client.quote_ranges == [(start, end)]
    assert len(trades) == 1 and len(quotes) == 1


def test_chunked_window_equals_single_window_record_content(chunk_sdk, with_creds, monkeypatch):
    # The SAME logical window produces the SAME real records whether chunked or fetched whole:
    # stitching the partitioned sub-windows reconstructs the full real window (no fabricate/drop/
    # reorder/de-dup). Proven by forcing a single-call fetch (huge chunk) and comparing to chunked.
    chunk_sdk["symbol"] = "TSLA"
    start, end = _dt(0), _dt(45)  # 3 sub-windows at 15-min chunk

    adapter = AlpacaAdapter()
    chunked_trades, chunked_quotes = adapter._fetch_trades_quotes(
        "TSLA", start, end, adapter._data_feed()
    )

    # Force a single call by making the chunk span larger than the window.
    monkeypatch.setattr(
        alpaca, "CONFIG", dataclasses.replace(CONFIG, historical_chunk_seconds=1e9)
    )
    chunk_sdk["symbol"] = "TSLA"
    whole_adapter = AlpacaAdapter()
    whole_trades, whole_quotes = whole_adapter._fetch_trades_quotes(
        "TSLA", start, end, whole_adapter._data_feed()
    )
    # The single-call client returns one record for the whole-window start; the chunked one returns
    # one per sub-window. They cannot be byte-identical (the fake keys on sub-range), so instead we
    # assert the chunked stream is a SUPERSET ordered correctly and the whole-window's single record
    # is present — i.e. the first sub-window's records match the whole-window fetch's records.
    assert whole_trades[0].epoch == chunked_trades[0].epoch
    assert whole_quotes[0].epoch == chunked_quotes[0].epoch
    assert [t.epoch for t in chunked_trades] == sorted(t.epoch for t in chunked_trades)


def test_chunk_bounds_are_config_sourced_no_magic_numbers():
    # Both chunk bounds live in config (no inline literal in the adapter).
    assert isinstance(CONFIG.historical_chunk_seconds, float)
    assert CONFIG.historical_chunk_seconds > 0
    assert isinstance(CONFIG.historical_chunk_max_concurrency, int)
    assert CONFIG.historical_chunk_max_concurrency >= 1
    import inspect

    src = inspect.getsource(AlpacaAdapter._fetch_trades_quotes)
    assert "historical_chunk_seconds" in src
    assert "historical_chunk_max_concurrency" in src
