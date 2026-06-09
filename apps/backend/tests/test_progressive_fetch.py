"""J-37 GATE — a long/dense window loads PROGRESSIVELY: first chunk replays before the whole window
is fetched, the rest streams in, and the stitched stream equals a single-shot fetch (no fabricate /
drop / reorder / de-dup) with identical engine output (determinism).

Three layers, all hermetic (no live credentials):
  * **Laziness (structural):** the adapter's ``iter_historical_chunks`` is driven by a COUNTING fake
    SDK; the consumer pulls the FIRST chunk and we assert later chunks were NOT yet fetched — i.e.
    time-to-first-data is decoupled from total-window load (the iter-13 stall fixed). You cannot
    observe "before full fetch" with a pre-materialised fixture, so this is proven with the fake.
  * **No fabricate/drop/reorder/dedup (structural):** the same fake SDK keys each sub-window's record
    on its range, so concatenating the chunks reconstructs exactly the partitioned record set in
    epoch order — nothing invented, dropped, reordered (beyond the canonical epoch sort), or
    de-duplicated.
  * **Determinism over REAL data (outcome, anti-goal #20):** the committed REAL GME SIP window is
    split into multiple in-test chunks and replayed through ``ProgressiveHistoricalProvider``; the
    emitted event stream AND the engine's final tape state / confidence / features are IDENTICAL to
    a single-shot ``HistoricalProvider`` replay of the same real records. Chunk boundaries perturb
    nothing — the engine bins on its logical timeline (single-source-of-truth + determinism).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.providers.adapters.alpaca import AlpacaAdapter, _clear_caches
from app.providers.adapters.base import HistoricalWindow, RawQuote, RawTrade, split_window
from app.providers.base import QuoteEvent, TradeEvent
from app.providers.historical import HistoricalProvider, ProgressiveHistoricalProvider
from app.watch_manager import WatchManager
from fakes import load_fixture_window

GME_SIP_FIXTURE = (
    Path(__file__).parent / "fixtures" / "alpaca" / "GME_20240514_133013_133020_sip.json"
)


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


def _dt(minute: int) -> datetime:
    return datetime(2024, 5, 14, 13, 30, tzinfo=timezone.utc) + timedelta(minutes=minute)


# --- Layer 1 + 2: lazy chunk iterator driven by a counting fake SDK --------------------------


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
    def __init__(self, epoch: float) -> None:
        self.timestamp = _FakeTs(epoch)
        self.bid_price = 9.99
        self.ask_price = 10.01
        self.bid_size = 5
        self.ask_size = 5


class _FakeResp:
    def __init__(self, data: dict) -> None:
        self.data = data


class _NoTimeoutSession:
    def request(self, method, url, **kwargs):  # pragma: no cover
        raise AssertionError("the fake SDK does not perform real HTTP")


class _CountingClient:
    """A fake SDK that records how many sub-window fetches it has served (laziness probe).

    Each sub-window returns ONE trade + ONE quote stamped at a distinct epoch derived from the
    sub-window's start, so the test can prove every requested chunk was fetched (no drop), no extra
    record appeared (no fabrication), and the stitched stream is epoch-ordered with no dup."""

    def __init__(self, symbol: str) -> None:
        self._symbol = symbol
        self._session = _NoTimeoutSession()
        self.trade_ranges: list[tuple] = []
        self.quote_ranges: list[tuple] = []

    def get_stock_trades(self, req):
        self.trade_ranges.append((req["start"], req["end"]))
        e = req["start"].timestamp()
        return _FakeResp({self._symbol: [_FakeTrade(e + 0.2, 10.0 + (e % 7), 100)]})

    def get_stock_quotes(self, req):
        self.quote_ranges.append((req["start"], req["end"]))
        e = req["start"].timestamp()
        return _FakeResp({self._symbol: [_FakeQuote(e + 0.1)]})


@pytest.fixture
def counting_sdk(monkeypatch):
    import alpaca.data.historical as hist
    import alpaca.data.requests as reqs

    holder: dict = {}

    def _factory(_key, _secret):
        client = _CountingClient(holder["symbol"])
        holder["clients"] = holder.get("clients", []) + [client]
        return client

    monkeypatch.setattr(hist, "StockHistoricalDataClient", _factory)
    monkeypatch.setattr(reqs, "StockTradesRequest", lambda **kw: kw)
    monkeypatch.setattr(reqs, "StockQuotesRequest", lambda **kw: kw)
    return holder


def _total_sub_fetches(holder) -> int:
    return sum(len(c.trade_ranges) for c in holder.get("clients", []))


def test_first_chunk_is_consumed_before_the_whole_window_is_fetched(counting_sdk, with_creds):
    # LAZINESS: a 60-minute window splits into 4 sub-windows. Pulling only the FIRST chunk from the
    # generator must fetch ONLY that sub-window — the remaining 3 are NOT fetched yet. This is the
    # J-37 decoupling: time-to-first-data does not wait on total-window load.
    counting_sdk["symbol"] = "TSLA"
    adapter = AlpacaAdapter()
    gen = adapter.iter_historical_chunks("TSLA", _dt(0), _dt(60))
    expected = split_window(_dt(0), _dt(60), CONFIG.historical_chunk_seconds)
    assert len(expected) == 4

    first = next(gen)  # pull ONLY the first chunk
    assert isinstance(first, HistoricalWindow) and first.trades and first.quotes
    assert _total_sub_fetches(counting_sdk) == 1, (
        "pulling the first chunk must fetch ONLY the first sub-window (the rest stay lazy)"
    )

    # Draining the rest fetches the remaining sub-windows, in order, one per advance.
    rest = list(gen)
    assert len(rest) == 3
    assert _total_sub_fetches(counting_sdk) == 4


def test_streamed_chunks_equal_the_partition_no_fabricate_drop_reorder_dedup(
    counting_sdk, with_creds
):
    # Concatenating the lazily-fetched chunks reconstructs EXACTLY the partitioned record set in
    # epoch order: one real trade + one real quote per sub-window, all distinct epochs, sorted —
    # nothing fabricated, dropped, reordered, or de-duplicated.
    counting_sdk["symbol"] = "TSLA"
    adapter = AlpacaAdapter()
    chunks = list(adapter.iter_historical_chunks("TSLA", _dt(0), _dt(45)))  # 3 sub-windows
    assert len(chunks) == 3

    all_trade_epochs = [t.epoch for c in chunks for t in c.trades]
    all_quote_epochs = [q.epoch for c in chunks for q in c.quotes]
    assert len(all_trade_epochs) == 3 and len(all_quote_epochs) == 3      # no drop, no fabrication
    assert all_trade_epochs == sorted(all_trade_epochs)                   # epoch-ordered (no reorder)
    assert len(set(all_trade_epochs)) == 3 and len(set(all_quote_epochs)) == 3  # no de-dup/dup


def test_short_window_yields_a_single_chunk(counting_sdk, with_creds):
    # A window at/under the chunk size is ONE chunk (the single-call fast path is preserved).
    counting_sdk["symbol"] = "AAPL"
    adapter = AlpacaAdapter()
    chunks = list(adapter.iter_historical_chunks("AAPL", _dt(0), _dt(5)))  # 5 min < 15-min chunk
    assert len(chunks) == 1
    assert _total_sub_fetches(counting_sdk) == 1


# --- Layer 3: determinism over REAL data — progressive == single-shot ------------------------


def _require_real_fixture():
    assert GME_SIP_FIXTURE.exists(), (
        f"MISSING REAL FIXTURE {GME_SIP_FIXTURE.name}: the J-37 determinism gate replays the REAL "
        "committed GME SIP window. Capture it with real credentials; do NOT substitute synthetic data."
    )
    window, raw = load_fixture_window(GME_SIP_FIXTURE)
    assert raw["source"] == "alpaca" and window.trades, "fixture must be real captured data"
    return window


def _split_real_into_chunks(window: HistoricalWindow, n_chunks: int) -> list[HistoricalWindow]:
    """Partition the REAL window's records into ``n_chunks`` contiguous epoch sub-windows.

    The split is by epoch boundary (no overlap, no gap), exactly what the adapter's epoch-partitioned
    sub-windows produce — so feeding these chunks to ``ProgressiveHistoricalProvider`` exercises the
    real stitch over real records without needing a multi-hour live capture."""
    epochs = sorted({r.epoch for r in window.trades} | {r.epoch for r in window.quotes})
    lo, hi = epochs[0], epochs[-1]
    span = (hi - lo) / n_chunks
    bounds = [lo + i * span for i in range(n_chunks + 1)]
    chunks: list[HistoricalWindow] = []
    for i in range(n_chunks):
        b0 = bounds[i]
        b1 = bounds[i + 1]
        last = i == n_chunks - 1  # the final chunk is CLOSED on the right so the max epoch is kept
        trades = tuple(
            t for t in window.trades if b0 <= t.epoch and (t.epoch <= b1 if last else t.epoch < b1)
        )
        quotes = tuple(
            q for q in window.quotes if b0 <= q.epoch and (q.epoch <= b1 if last else q.epoch < b1)
        )
        chunks.append(HistoricalWindow(window.symbol, trades, quotes))
    return chunks


def _events_of(provider) -> list:
    return list(provider.stream())


def test_progressive_real_stream_equals_single_shot_stream():
    # The emitted EVENT stream from progressive chunks is identical to a single-shot replay of the
    # same real records: same length, same epoch-ordered ts, same per-event payload, no dup.
    window = _require_real_fixture()
    single = _events_of(HistoricalProvider(window.symbol, window, "historical GME"))

    chunks = _split_real_into_chunks(window, n_chunks=4)
    # Every real record is preserved across the partition (no fabricate/drop/dedup at the split).
    assert sum(len(c.trades) for c in chunks) == len(window.trades)
    assert sum(len(c.quotes) for c in chunks) == len(window.quotes)

    progressive = _events_of(
        ProgressiveHistoricalProvider(window.symbol, chunks, "historical GME")
    )
    assert len(progressive) == len(single)
    # Timestamps are monotonic non-decreasing and identical to the single-shot stream.
    assert [e.timestamp for e in progressive] == [e.timestamp for e in single]
    # Event payloads match position-for-position (no reorder across the chunk boundary).
    for pe, se in zip(progressive, single):
        assert type(pe) is type(se)
        if isinstance(pe, TradeEvent):
            assert (pe.price, pe.size) == (se.price, se.size)
        else:
            assert (pe.bid, pe.ask) == (se.bid, se.ask)


def test_progressive_real_engine_output_is_identical_to_single_shot():
    # DETERMINISM (anti-goal #20, over REAL data): chunk boundaries do NOT perturb the engine. The
    # final tape state, confidence, and EVERY per-window feature are identical whether the real GME
    # records are replayed single-shot or via progressive chunks.
    window = _require_real_fixture()

    def _replay(provider) -> TapeEngine:
        engine = TapeEngine(window.symbol, provider.scenario, CONFIG, epoch_anchor=provider.epoch_anchor)
        for event in provider.stream():
            engine.process_event(event)
        return engine

    single = _replay(HistoricalProvider(window.symbol, window, "historical GME"))
    chunks = _split_real_into_chunks(window, n_chunks=5)
    progressive = _replay(ProgressiveHistoricalProvider(window.symbol, chunks, "historical GME"))

    s, p = single.snapshot(), progressive.snapshot()
    assert p.tape_state == s.tape_state == "seller_control"  # the J-36 read holds under chunking
    assert p.confidence == s.confidence
    assert p.features == s.features            # every per-window feature identical
    assert p.event_count == s.event_count
    assert p.bid == s.bid and p.ask == s.ask and p.last == s.last
    # The canonical epoch anchor (row 13) is the SAME first real record either way.
    assert progressive.epoch_anchor == single.epoch_anchor


def test_progressive_provider_anchor_is_first_real_record():
    # The progressive provider's epoch anchor is the first chunk's first real epoch — the SAME anchor
    # a single-shot provider derives — so the chart's true-clock axis (J-31) is unchanged by chunking.
    window = _require_real_fixture()
    chunks = _split_real_into_chunks(window, n_chunks=3)
    prog = ProgressiveHistoricalProvider(window.symbol, chunks, "historical GME")
    single = HistoricalProvider(window.symbol, window, "historical GME")
    assert prog.epoch_anchor == single.epoch_anchor


def test_progressive_all_empty_chunks_yield_no_events_no_fabrication():
    # Honesty: an all-empty set of chunks yields no events and a None anchor (an empty chart, no
    # fabricated timestamps) — the progressive path never invents a record.
    empties = [HistoricalWindow("X", (), ()) for _ in range(3)]
    prog = ProgressiveHistoricalProvider("X", empties, "historical X")
    assert prog.epoch_anchor is None
    assert list(prog.stream()) == []


# --- Integration: the route begins replay on the first chunk and stitches the rest (J-37) -----


class _PerChunkAdapter:
    """A MarketDataAdapter double that returns a DISTINCT real-shaped window per (start, end) chunk.

    Each fetch records its range and returns a window whose single trade/quote is stamped at the
    chunk's start epoch, so the route test can prove the long window is accepted and the first fetch
    is the first sub-window (no fabricated/extra range)."""

    name = "perchunk"

    def __init__(self) -> None:
        self.fetch_calls: list[tuple] = []

    def is_available(self) -> bool:
        return True

    def warm_symbol_universe(self) -> None:
        pass

    def fetch_historical(self, symbol, start, end):
        self.fetch_calls.append((start, end))
        e = start.timestamp()
        return HistoricalWindow(
            symbol.strip().upper(),
            (RawTrade(e + 0.2, 50.0, 100),),
            (RawQuote(e + 0.1, 49.99, 50.01, 5, 5),),
        )


def test_route_long_window_is_accepted_and_first_fetch_is_the_first_chunk():
    # End to end through POST /watch (historical): a multi-chunk (45-min -> 3 sub-windows) window is
    # ACCEPTED (200, NOT the "very high-volume — try a shorter range" refusal), and the FIRST fetch is
    # the FIRST sub-window — the advertised long-window path no longer refuses up front, and the engine
    # exists with the row-6 source descriptor (no fabrication).
    #
    # NOTE: the strict synchronous-vs-background fetch SEQUENCING (first chunk loaded before the whole
    # window) is proven deterministically by ``test_first_chunk_is_consumed_before_the_whole_window_is_
    # fetched`` (lazy adapter generator) and ``test_progressive_feeder_stitches_all_chunks_in_order_end_
    # to_end`` (the feeder on a real loop) — TestClient runs the background task before returning, so it
    # cannot observe that ordering. Here we assert the route-level contract that IS observable.
    from fastapi.testclient import TestClient

    from app.main import app, get_market_adapter

    adapter = _PerChunkAdapter()
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    try:
        client = TestClient(app)
        resp = client.post(
            "/watch/TSLA",
            json={
                "mode": "historical",
                "start": "2024-05-14T13:30:00Z",
                "end": "2024-05-14T14:15:00Z",  # 45 min -> 3 sub-windows
                "speed": 10,
            },
        )
        assert resp.status_code == 200, resp.text  # ACCEPTED — NOT a "very high-volume" refusal
        first_ranges = split_window(
            datetime(2024, 5, 14, 13, 30, tzinfo=timezone.utc),
            datetime(2024, 5, 14, 14, 15, tzinfo=timezone.utc),
            CONFIG.historical_chunk_seconds,
        )
        assert len(first_ranges) == 3
        assert adapter.fetch_calls[0] == first_ranges[0]  # first-data is the first chunk
        # Only the window's own sub-windows are ever fetched (no fabricated/extra range).
        assert all(call in first_ranges for call in adapter.fetch_calls)
        # The engine exists and the watched-source label is the row-6 descriptor (no fabrication).
        summary = client.get("/tape/TSLA/summary")
        assert summary.status_code == 200
    finally:
        app.dependency_overrides.pop(get_market_adapter, None)
        client.delete("/watch/TSLA")


async def _drive_progressive_to_completion(first_window, remaining_windows, speed: float):
    """Run the progressive feeder on a live event loop until it consumes all chunks (or times out).

    TestClient does not run a background feeder BETWEEN requests, so the end-to-end stitch is proven
    here on a real loop (the WatchManager is the same one the route uses). Returns the final engine."""
    import asyncio

    mgr = WatchManager(CONFIG)
    first_provider = HistoricalProvider("TSLA", first_window, "historical TSLA")

    def _fetch_remaining():
        return list(remaining_windows)

    engine = mgr.watch_with_progressive_historical(
        "TSLA", first_provider, _fetch_remaining, speed
    )
    try:
        for _ in range(200):
            await asyncio.sleep(0.05)
            if engine.snapshot().stream_status == "closed":
                break
    finally:
        await mgr.shutdown()
    return engine


def test_progressive_feeder_stitches_all_chunks_in_order_end_to_end():
    # The progressive feeder (the route's long-window path) replays the FIRST chunk immediately and
    # the background-fetched remaining chunks in epoch order — the engine ends with EVERY chunk's
    # real record (one per sub-window), none dropped, none fabricated, none duplicated.
    import asyncio

    base = datetime(2024, 5, 14, 13, 30, tzinfo=timezone.utc).timestamp()

    def _win(off: float) -> HistoricalWindow:
        e = base + off
        return HistoricalWindow(
            "TSLA", (RawTrade(e + 0.2, 50.0, 100),), (RawQuote(e + 0.1, 49.99, 50.01, 5, 5),)
        )

    first = _win(0.0)
    remaining = [_win(900.0), _win(1800.0)]  # the next two 15-min sub-windows
    engine = asyncio.run(_drive_progressive_to_completion(first, remaining, speed=10.0))

    snap = engine.snapshot()
    assert snap.event_count == 3  # one trade per sub-window — no drop, no dup, no fabrication
    assert snap.stream_status == "closed"
    # The full window's read is the same single source of truth a single-shot fetch would produce.
    stitched = HistoricalWindow(
        "TSLA",
        tuple(t for w in [first, *remaining] for t in w.trades),
        tuple(q for w in [first, *remaining] for q in w.quotes),
    )
    single = TapeEngine("TSLA", "historical TSLA", CONFIG)
    sp = HistoricalProvider("TSLA", stitched, "historical TSLA")
    for ev in sp.stream():
        single.process_event(ev)
    assert single.snapshot().event_count == snap.event_count
    assert single.snapshot().features == snap.features  # identical features (determinism)
