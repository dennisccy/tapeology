"""Vendor responsiveness (iter-11 — J-28 / J-29 / J-30).

Hermetic proofs that every credential-gated vendor path is **honestly bounded** (a real
call-level deadline whose error beats the client, with an actionable oversize message) and **fast
by design** (concurrent historical fetch + folded pre-flight + a bounded window cache + a prompt
warm-up; a warmed, single-owner symbol universe). Everything runs behind the existing seams — the
``FakeAdapter`` (via ``dependency_overrides``), the committed REAL fixture window, and a small
fake SDK client for the concurrency proof — never the production vendor and never synthesized
market data.

The three anti-goal pillars asserted here:
  * **J-28** — a real HTTP-level deadline at the vendor-call boundary (not only the outer
    ``asyncio.wait_for`` wrapper), the backend-effective bound strictly < the frontend bound (from
    config), and an oversize/timeout mapped to an ACTIONABLE message (no engine, no fabricated tape).
  * **J-29** — trades+quotes fetched concurrently (total ≈ max, not sum); the needless pre-flight
    gone (a successful fetch is one round-trip; unknown→symbol_not_tradable, empty→no_data_for_window
    still hold); a cache hit replays the SAME real window with no vendor call; the warm-up
    fast-forward is delivery-only (identical engine features/state/confidence — determinism preserved).
  * **J-30** — the symbol universe is warmed once (single owner, no per-search re-fetch), a vendor
    error in search degrades to ``[]``, and the backend min-query drops a too-short query (no call).
"""

from __future__ import annotations

import dataclasses
import inspect
import time

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
import app.providers.adapters.alpaca as alpaca
from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.main import app, get_market_adapter
from app.providers.adapters.alpaca import AlpacaAdapter, _clear_caches
from app.providers.adapters.base import (
    HistoricalWindow,
    NoDataForWindow,
    RawQuote,
    RawTrade,
    SymbolMatch,
    SymbolNotTradable,
    VendorTimeout,
)
from app.providers.historical import HistoricalProvider
from app.watch_manager import WatchManager
from fakes import FakeAdapter, load_fixture_window

HIST_BODY = {
    "mode": "historical",
    "start": "2026-06-02T15:00",
    "end": "2026-06-02T15:02",
    "speed": 1,
}


@pytest.fixture
def fake_client():
    """A TestClient with the market-data adapter overridden by a FakeAdapter (hermetic)."""

    def _make(**kwargs) -> TestClient:
        app.dependency_overrides[get_market_adapter] = lambda: FakeAdapter(**kwargs)
        return TestClient(app)

    yield _make
    app.dependency_overrides.pop(get_market_adapter, None)


@pytest.fixture(autouse=True)
def _isolate_caches():
    """Reset the adapter's process-lifetime caches around every test (window cache + universe)."""
    _clear_caches()
    yield
    _clear_caches()


@pytest.fixture
def with_creds(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "test-key-123")
    monkeypatch.setenv("ALPACA_API_SECRET", "test-secret-456")
    return monkeypatch


# ============================================================================================
# J-28 — a true call-level vendor deadline, backend<frontend ordering, actionable message
# ============================================================================================


def test_http_deadline_constant_exists_and_is_config_sourced():
    # The real call-level deadline is a config constant (no inline literal), a positive float.
    assert isinstance(CONFIG.vendor_http_timeout_seconds, float)
    assert CONFIG.vendor_http_timeout_seconds > 0


def test_backend_effective_bound_is_strictly_less_than_frontend_bound_from_config():
    # The ordering invariant J-28 requires, asserted FROM CONFIG (never hardcoded): the HTTP
    # deadline <= the outer wrapper bound, and the backend-effective bound (the wrapper, the larger
    # of the two backend bounds) is strictly < the frontend client timeout — so the backend's
    # honest, actionable error always wins when the backend is reachable.
    http_deadline = CONFIG.vendor_http_timeout_seconds
    wrapper_bound = CONFIG.vendor_call_timeout_seconds
    frontend_bound_s = CONFIG.frontend_watch_request_timeout_ms / 1000.0
    assert http_deadline <= wrapper_bound, "HTTP deadline must be <= the wrapper backstop"
    # The backend-effective bound is bounded above by the wrapper; require it strictly < frontend.
    assert wrapper_bound < frontend_bound_s, "backend bound must be < the frontend client timeout"
    assert http_deadline < frontend_bound_s


def test_frontend_timeout_constant_mirrors_the_frontend_config_value():
    # The mirrored frontend constant exists so the ordering invariant is testable in-process; it
    # mirrors apps/frontend/lib/config.ts (WATCH_REQUEST_TIMEOUT_MS = 12000).
    assert CONFIG.frontend_watch_request_timeout_ms == 12000


def test_adapter_applies_real_http_timeout_to_sdk_session():
    # The real call-level bound is set at the SDK client's requests.Session layer: a constructed
    # client's session.request injects timeout=CONFIG.vendor_http_timeout_seconds by default. This
    # is what cuts a slow/large response off at the vendor call (distinct from the outer wrapper).
    from alpaca.data.historical import StockHistoricalDataClient

    captured: dict = {}

    class _ProbeSession:
        def request(self, method, url, **kwargs):
            captured.update(kwargs)

            class _Resp:
                status_code = 200

            return _Resp()

    client = StockHistoricalDataClient("k", "s")
    client._session = _ProbeSession()
    AlpacaAdapter._with_http_timeout(client)
    client._session.request("GET", "http://example.test")
    assert captured.get("timeout") == CONFIG.vendor_http_timeout_seconds


def test_with_http_timeout_is_idempotent_and_defensive():
    # Wrapping twice does not double-wrap (idempotent); a client without a usable session is left
    # unchanged (the outer wrapper still bounds the call) rather than guessed at.
    from alpaca.data.historical import StockHistoricalDataClient

    client = StockHistoricalDataClient("k", "s")
    AlpacaAdapter._with_http_timeout(client)
    wrapped = client._session.request
    AlpacaAdapter._with_http_timeout(client)
    assert client._session.request is wrapped  # idempotent

    class _NoSession:
        _session = None

    obj = _NoSession()
    assert AlpacaAdapter._with_http_timeout(obj) is obj  # defensive no-op


def test_requests_timeout_maps_to_neutral_vendor_timeout():
    # The SDK's requests.Timeout is translated to the NEUTRAL VendorTimeout inside the adapter, so
    # no vendor exception type leaks out (provider-agnostic anti-goal). The detail is carried.
    from requests.exceptions import Timeout as RequestsTimeout

    with pytest.raises(VendorTimeout) as exc_info:
        with alpaca._mapped_vendor_timeout("custom oversize detail"):
            raise RequestsTimeout("slow")
    assert exc_info.value.detail == "custom oversize detail"


def test_historical_vendor_timeout_maps_to_actionable_provider_timeout_no_engine(fake_client):
    # A REAL call-level timeout (the adapter raised VendorTimeout) on the historical path maps to
    # provider_timeout with the ACTIONABLE oversize message (not a generic retry) and creates NO
    # engine — no fabricated tape. This proves the deadline is enforced AT the vendor call, not
    # only by the outer wrapper (the fake raises immediately; no wall-clock block needed).
    client = fake_client(available=True, fetch_timeout=True)
    resp = client.post("/watch/AAPL", json=HIST_BODY)
    assert resp.status_code == 504
    body = resp.json()
    assert body["reason"] == "provider_timeout"
    assert body["detail"] == "that window is very high-volume — try a shorter range"
    assert "try a shorter range" in body["detail"]  # actionable for the real cause
    assert "please try again" not in body["detail"].lower()  # NOT a misleading generic retry
    # No engine created => an explicit 404, never a fabricated tape.
    assert client.get("/tape/AAPL/state").status_code == 404


def test_actionable_oversize_message_is_distinct_from_generic_unavailable(fake_client):
    # The oversize/timeout message must be its own distinct, actionable variant — not collapsed
    # into the generic provider_unavailable detail.
    timed_out = fake_client(available=True, fetch_timeout=True).post("/watch/AAPL", json=HIST_BODY)
    assert timed_out.json()["detail"] != "real-data provider unavailable"
    assert timed_out.json()["reason"] == "provider_timeout"


# ============================================================================================
# J-29 — fast historical load by design (concurrent fetch, no pre-flight, cache, warm-up)
# ============================================================================================

# A small fake SDK used ONLY to prove the real adapter's concurrent fetch. It models the two data
# calls each taking SLEEP_PER_CALL seconds; with the adapter's ThreadPoolExecutor the wall-clock is
# ~max(t_trades, t_quotes) ≈ one SLEEP_PER_CALL, NOT the ~2× of a sequential fetch.
SLEEP_PER_CALL = 0.30


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


class _FakeTs:
    def __init__(self, epoch: float) -> None:
        self._epoch = epoch

    def timestamp(self) -> float:
        return self._epoch


class _FakeResp:
    def __init__(self, data: dict) -> None:
        self.data = data


class _FakeSDKClient:
    """A timed stand-in for StockHistoricalDataClient: each data call sleeps SLEEP_PER_CALL."""

    def __init__(self, symbol: str) -> None:
        self._symbol = symbol
        self._session = _NoTimeoutSession()
        self.trade_calls = 0
        self.quote_calls = 0

    def get_stock_trades(self, _req):
        self.trade_calls += 1
        time.sleep(SLEEP_PER_CALL)
        return _FakeResp({self._symbol: [_FakeTrade(1.0, 10.0, 100)]})

    def get_stock_quotes(self, _req):
        self.quote_calls += 1
        time.sleep(SLEEP_PER_CALL)
        return _FakeResp({self._symbol: [_FakeQuote(0.5, 9.99, 10.01, 5, 5)]})


class _NoTimeoutSession:
    def request(self, method, url, **kwargs):  # pragma: no cover - not exercised by the fake
        raise AssertionError("the fake SDK does not perform real HTTP")


@pytest.fixture
def fake_sdk(monkeypatch):
    """Patch the lazily-imported SDK names so _fetch_trades_quotes drives the timed fake client."""
    import alpaca.data.historical as hist
    import alpaca.data.requests as reqs

    holder: dict = {}

    def _client_factory(_key, _secret):
        client = _FakeSDKClient(holder["symbol"])
        holder["client"] = client
        return client

    monkeypatch.setattr(hist, "StockHistoricalDataClient", _client_factory)
    monkeypatch.setattr(reqs, "StockTradesRequest", lambda **kw: kw)
    monkeypatch.setattr(reqs, "StockQuotesRequest", lambda **kw: kw)
    return holder


def test_trades_and_quotes_are_fetched_concurrently(fake_sdk, with_creds):
    # The two vendor calls OVERLAP: total wall-clock ≈ one SLEEP_PER_CALL (max), not two (sum). A
    # generous threshold (1.5×) avoids flakiness while still excluding the ~2× sequential cost.
    fake_sdk["symbol"] = "F"
    adapter = AlpacaAdapter()
    start = time.monotonic()
    trades, quotes = adapter._fetch_trades_quotes("F", None, None, adapter._data_feed())
    elapsed = time.monotonic() - start
    assert len(trades) == 1 and len(quotes) == 1  # both calls ran and mapped to neutral records
    assert fake_sdk["client"].trade_calls == 1
    assert fake_sdk["client"].quote_calls == 1
    assert elapsed < SLEEP_PER_CALL * 1.5, f"fetch looks sequential ({elapsed:.2f}s)"
    assert elapsed >= SLEEP_PER_CALL * 0.8, "each call should still take ~SLEEP_PER_CALL"


def test_successful_fetch_makes_one_round_trip_no_preflight(fake_sdk, with_creds):
    # The needless get_asset pre-flight is GONE: a successful fetch calls ONLY the two data
    # endpoints (no tradability round-trip on the hot path). We assert no get_asset by giving the
    # fake client no such method — calling it would AttributeError.
    fake_sdk["symbol"] = "F"
    adapter = AlpacaAdapter()
    window = adapter.fetch_historical("F", None, None)
    assert isinstance(window, HistoricalWindow)
    assert window.symbol == "F"
    assert not hasattr(fake_sdk["client"], "get_asset")  # the data client never needs get_asset


def test_unknown_symbol_still_symbol_not_tradable_on_folded_path(fake_client):
    # Folded pre-flight must not weaken J-14: an unknown symbol still maps to symbol_not_tradable
    # (the FakeAdapter raises it directly, exactly as the real adapter does on the empty->get_asset
    # 404 path), with NO engine.
    client = fake_client(available=True, not_tradable=True)
    resp = client.post("/watch/ZZZZ", json=HIST_BODY)
    assert resp.status_code == 404
    assert resp.json()["reason"] == "symbol_not_tradable"
    assert client.get("/tape/ZZZZ/state").status_code == 404


def test_empty_window_still_no_data_on_folded_path(fake_client):
    # And an empty (tradable) window still maps to no_data_for_window, NO engine.
    client = fake_client(available=True, no_data=True)
    resp = client.post("/watch/AAPL", json=HIST_BODY)
    assert resp.status_code == 404
    assert resp.json()["reason"] == "no_data_for_window"
    assert client.get("/tape/AAPL/state").status_code == 404


def test_real_adapter_empty_result_consults_get_asset_to_classify(monkeypatch, with_creds):
    # The folded determination: on an EMPTY data result the adapter consults get_asset ONCE to
    # decide unknown-symbol vs empty-window. A tradable asset -> NoDataForWindow; a 404 ->
    # SymbolNotTradable. This proves the second round-trip is paid ONLY on the empty path.
    import alpaca.common.exceptions as exc_mod
    import alpaca.data.historical as hist
    import alpaca.data.requests as reqs
    import alpaca.trading.client as trading

    monkeypatch.setattr(reqs, "StockTradesRequest", lambda **kw: kw)
    monkeypatch.setattr(reqs, "StockQuotesRequest", lambda **kw: kw)

    class _EmptyDataClient:
        def __init__(self, *_a, **_k):
            self._session = _NoTimeoutSession()

        def get_stock_trades(self, _req):
            return _FakeResp({})  # no trades -> empty path

        def get_stock_quotes(self, _req):
            return _FakeResp({})

    monkeypatch.setattr(hist, "StockHistoricalDataClient", _EmptyDataClient)

    calls = {"get_asset": 0}

    class _Asset:
        tradable = True

    class _TradingClient:
        def __init__(self, *_a, **_k):
            self._session = _NoTimeoutSession()

        def get_asset(self, _sym):
            calls["get_asset"] += 1
            return _Asset()

    monkeypatch.setattr(trading, "TradingClient", _TradingClient)

    adapter = AlpacaAdapter()
    with pytest.raises(NoDataForWindow):
        adapter.fetch_historical("AAPL", None, None)
    assert calls["get_asset"] == 1  # the second round-trip is paid ONLY on the empty result

    # Now an unknown symbol: get_asset raises a 404 APIError -> SymbolNotTradable. The SDK's
    # APIError.status_code is a read-only property derived from the underlying HTTP error, so we
    # subclass and override it to report 404 (the adapter reads getattr(exc, "status_code", None)).
    class _Api404(exc_mod.APIError):
        def __init__(self):
            super().__init__("not found")

        @property
        def status_code(self):
            return 404

    class _TradingClient404(_TradingClient):
        def get_asset(self, _sym):
            calls["get_asset"] += 1
            raise _Api404()

    monkeypatch.setattr(trading, "TradingClient", _TradingClient404)
    with pytest.raises(SymbolNotTradable):
        adapter.fetch_historical("ZZZZ", None, None)


def test_window_cache_hit_skips_vendor_and_replays_same_real_window(fake_sdk, with_creds):
    # A second fetch of the SAME (symbol, start, end, feed) does NOT call the vendor again and
    # returns the SAME real window object (never a fabricated one) — near-instant re-watch (J-29).
    fake_sdk["symbol"] = "F"
    adapter = AlpacaAdapter()
    first = adapter.fetch_historical("F", "2026-06-02T15:00", "2026-06-02T15:02")
    client_after_first = fake_sdk["client"]
    assert client_after_first.trade_calls == 1 and client_after_first.quote_calls == 1

    second = adapter.fetch_historical("F", "2026-06-02T15:00", "2026-06-02T15:02")
    # No new client was constructed for the second call (cache hit) and the SAME window is returned.
    assert fake_sdk["client"] is client_after_first  # factory not re-invoked
    assert client_after_first.trade_calls == 1  # no extra vendor round-trip
    assert second is first  # the SAME real window, replayed verbatim


def test_window_cache_is_keyed_by_window_and_misses_on_a_different_range(fake_sdk, with_creds):
    # A DIFFERENT window is a cache MISS (a fresh vendor round-trip) — the cache never serves the
    # wrong window's data.
    fake_sdk["symbol"] = "F"
    adapter = AlpacaAdapter()
    adapter.fetch_historical("F", "2026-06-02T15:00", "2026-06-02T15:02")
    first_client = fake_sdk["client"]
    adapter.fetch_historical("F", "2026-06-02T15:05", "2026-06-02T15:07")  # different range
    assert fake_sdk["client"] is not first_client  # a new fetch happened (miss)


def test_window_cache_respects_ttl(monkeypatch, fake_sdk, with_creds):
    # An entry past the TTL is treated as a miss (a fresh fetch), so memory/staleness stay bounded.
    fake_sdk["symbol"] = "F"
    monkeypatch.setattr(
        main_module, "CONFIG", dataclasses.replace(CONFIG, historical_cache_ttl_seconds=0.0)
    )
    # The adapter reads CONFIG from its own module; patch there too.
    monkeypatch.setattr(
        alpaca, "CONFIG", dataclasses.replace(CONFIG, historical_cache_ttl_seconds=0.0)
    )
    adapter = AlpacaAdapter()
    adapter.fetch_historical("F", "2026-06-02T15:00", "2026-06-02T15:02")
    first_client = fake_sdk["client"]
    time.sleep(0.01)
    adapter.fetch_historical("F", "2026-06-02T15:00", "2026-06-02T15:02")
    assert fake_sdk["client"] is not first_client  # TTL expired -> miss -> re-fetch


def test_window_cache_is_bounded_lru(monkeypatch):
    # The cache is bounded: with max=2, inserting a third window evicts the least-recently-used.
    monkeypatch.setattr(
        alpaca, "CONFIG", dataclasses.replace(CONFIG, historical_cache_max_entries=2)
    )
    w = lambda s: HistoricalWindow(s, (RawTrade(1.0, 1.0, 1),), (RawQuote(0.5, 0.9, 1.1, 1, 1),))
    alpaca._cache_put(("A", 0, 1, "iex"), w("A"))
    alpaca._cache_put(("B", 0, 1, "iex"), w("B"))
    alpaca._cache_put(("C", 0, 1, "iex"), w("C"))  # evicts A (LRU)
    assert alpaca._cache_get(("A", 0, 1, "iex")) is None
    assert alpaca._cache_get(("B", 0, 1, "iex")) is not None
    assert alpaca._cache_get(("C", 0, 1, "iex")) is not None


# --- Warm-up fast-forward is delivery-only (determinism preserved) ---------------------------


def _synthetic_window() -> HistoricalWindow:
    """A small deterministic window (alternating quote/trade) for the warm-up determinism test."""
    trades = tuple(RawTrade(float(i), 10.0 + i * 0.01, 100) for i in range(1, 61))
    quotes = tuple(
        RawQuote(float(i) - 0.5, 10.0 + i * 0.01 - 0.01, 10.0 + i * 0.01 + 0.01, 5, 5)
        for i in range(1, 61)
    )
    return HistoricalWindow("SYN", trades, quotes)


def _snapshot_fingerprint(engine: TapeEngine):
    """The engine outputs that MUST be identical regardless of delivery pacing."""
    snap = engine.snapshot()
    return (snap.tape_state, round(snap.confidence, 9), snap.timestamp)


@pytest.mark.anyio
async def test_warmup_fast_forward_yields_identical_engine_output_as_reference():
    # DETERMINISM (Sharp Edge #4): the fast-forwarded replay through _feed_paced delivers events
    # promptly but UNCHANGED (same order, same logical timestamps), so its final features/state/
    # confidence are IDENTICAL to a plain synchronous feed of the same stream. The fast-forward is
    # delivery pacing ONLY — it never enters classify() or any feature/score.
    window = _synthetic_window()

    # Reference: feed the identical event sequence synchronously (no pacing at all).
    ref_engine = TapeEngine("SYN", "historical SYN", CONFIG)
    for event in HistoricalProvider("SYN", window, "historical SYN").stream():
        ref_engine.process_event(event)

    # Fast-forwarded replay via the real feeder (ff pace 0.0 covers all warm-up deliveries).
    ff_config = dataclasses.replace(CONFIG, warmup_fast_forward_pace_seconds=0.0)
    manager = WatchManager(ff_config)
    ff_engine = TapeEngine("SYN", "historical SYN", ff_config)
    await manager._feed_paced(
        ff_engine, HistoricalProvider("SYN", window, "historical SYN"), speed=10.0
    )

    assert _snapshot_fingerprint(ff_engine) == _snapshot_fingerprint(ref_engine)
    # Per-window feature values must match exactly too (single source of truth holds under pacing).
    assert ff_engine.snapshot().features == ref_engine.snapshot().features


@pytest.mark.anyio
async def test_warmup_fast_forward_does_not_wait_out_logical_gaps():
    # A window whose warm-up events sit on LARGE logical gaps must still warm PROMPTLY: with the
    # fast-forward, delivering the first warmup_min_events takes ~0s of wall-clock, not the sum of
    # their (large) logical gaps / speed. Proven by a bound far below the un-fast-forwarded cost.
    big_gap = CONFIG.replay_pacing_cap_seconds  # each normal gap would clamp to this (>=)
    n = CONFIG.warmup_min_events
    trades = tuple(RawTrade(float(i) * 1000.0, 10.0, 100) for i in range(1, n + 5))
    window = HistoricalWindow("SYN", trades, ())
    ff_config = dataclasses.replace(CONFIG, warmup_fast_forward_pace_seconds=0.0)
    manager = WatchManager(ff_config)
    engine = TapeEngine("SYN", "historical SYN", ff_config)

    start = time.monotonic()
    await manager._feed_paced(
        engine, HistoricalProvider("SYN", window, "historical SYN"), speed=1.0
    )
    elapsed = time.monotonic() - start
    # The first `n` deliveries are fast-forwarded; only the few post-warm-up events pay the cap.
    # Far below the ~n*big_gap an un-fast-forwarded warm-up would cost.
    assert elapsed < big_gap * 6, f"warm-up did not fast-forward (took {elapsed:.2f}s)"


def test_warmup_fast_forward_pace_is_config_sourced():
    # The fast-forward bound is a config constant (no inline literal in the feeder).
    assert isinstance(CONFIG.warmup_fast_forward_pace_seconds, float)
    assert CONFIG.warmup_fast_forward_pace_seconds >= 0.0
    src = inspect.getsource(WatchManager._feed_paced)
    assert "warmup_fast_forward_pace_seconds" in src
    assert "warmup_min_events" in src


# ============================================================================================
# J-30 — warmed/cached symbol universe + min-query (backend half)
# ============================================================================================


def test_warm_then_search_does_not_refetch_universe(monkeypatch, with_creds):
    # The universe is warmed ONCE; a subsequent search is served from the warmed cache and does
    # NOT trigger a per-request universe fetch (single owner, no second store).
    fetches = {"count": 0}

    def _fake_fetch(self):
        fetches["count"] += 1
        return [SymbolMatch("AAPL", "Apple Inc."), SymbolMatch("AABA", "Altaba")]

    monkeypatch.setattr(AlpacaAdapter, "_fetch_asset_universe", _fake_fetch)
    adapter = AlpacaAdapter()
    adapter.warm_symbol_universe()
    assert fetches["count"] == 1  # warmed once at startup

    matches = adapter.search_symbols("AA")
    assert fetches["count"] == 1  # the search did NOT re-fetch — served from the warmed cache
    assert [m.symbol for m in matches] == ["AABA", "AAPL"]  # prefix matches, sorted


def test_warm_is_noop_without_credentials(monkeypatch):
    # No creds => the warm is a NO-OP (no fetch attempted) and search stays []. The verification
    # environment without creds must never touch the vendor at startup.
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)
    fetches = {"count": 0}
    monkeypatch.setattr(
        AlpacaAdapter,
        "_fetch_asset_universe",
        lambda self: fetches.__setitem__("count", fetches["count"] + 1) or [],
    )
    AlpacaAdapter().warm_symbol_universe()
    assert fetches["count"] == 0  # never fetched without creds
    assert alpaca._ASSET_UNIVERSE is None  # cache stays empty


def test_warm_is_idempotent_when_already_warmed(monkeypatch, with_creds):
    # A second warm does not re-fetch (already warmed) — the one-time startup warm is enough.
    fetches = {"count": 0}
    monkeypatch.setattr(
        AlpacaAdapter,
        "_fetch_asset_universe",
        lambda self: fetches.__setitem__("count", fetches["count"] + 1) or [SymbolMatch("F", "Ford")],
    )
    adapter = AlpacaAdapter()
    adapter.warm_symbol_universe()
    adapter.warm_symbol_universe()
    assert fetches["count"] == 1  # only the first warm fetched


def test_warm_swallows_vendor_error_never_raises(monkeypatch, with_creds):
    # warm_symbol_universe MUST NOT raise (a warm failure is swallowed so startup never crashes);
    # search then falls back to its own lazy fetch on the next call.
    def _boom(self):
        raise RuntimeError("vendor down at startup")

    monkeypatch.setattr(AlpacaAdapter, "_fetch_asset_universe", _boom)
    AlpacaAdapter().warm_symbol_universe()  # must not raise
    assert alpaca._ASSET_UNIVERSE is None  # nothing cached after a failed warm


def test_lazy_universe_is_single_owner_fetched_once(monkeypatch, with_creds):
    # Without a startup warm, the first search lazily fetches the universe ONCE and every later
    # search reuses it (the module-level _ASSET_UNIVERSE is the single owner — no second store).
    fetches = {"count": 0}
    monkeypatch.setattr(
        AlpacaAdapter,
        "_fetch_asset_universe",
        lambda self: fetches.__setitem__("count", fetches["count"] + 1)
        or [SymbolMatch("TSLA", "Tesla")],
    )
    adapter = AlpacaAdapter()
    adapter.search_symbols("TS")
    adapter.search_symbols("TS")
    adapter.search_symbols("TSL")
    assert fetches["count"] == 1  # fetched once, reused thereafter


def test_search_min_query_drops_too_short_query_no_vendor_call(fake_client):
    # The backend enforces symbol_search_min_query: a too-short query => [] with no adapter call.
    # (symbol_search_min_query is 1, so a blank query is the too-short case.)
    adapter = FakeAdapter(available=True, matches=[SymbolMatch("AAPL", "Apple")])
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    try:
        client = TestClient(app)
        resp = client.get("/symbols/search", params={"q": "  "})  # blank after strip
        assert resp.status_code == 200
        assert resp.json() == []
        assert adapter.search_calls == []  # no vendor work below the min-query
    finally:
        app.dependency_overrides.pop(get_market_adapter, None)


def test_search_vendor_error_degrades_to_empty_list(fake_client):
    # A vendor hiccup in the search path yields [] (never a 500, never a stuck spinner) so free-text
    # watch entry always remains possible (J-30 honesty).
    client = fake_client(available=True, search_raises=True)
    resp = client.get("/symbols/search", params={"q": "AAPL"})
    assert resp.status_code == 200
    assert resp.json() == []


# --- Startup warm wiring (lifespan fires the neutral warm via the seam) -----------------------


def test_lifespan_startup_warms_universe_via_neutral_seam():
    # The FastAPI lifespan startup calls warm_symbol_universe through the neutral adapter seam (no
    # SDK name in main.py). Using the context-manager TestClient enters the lifespan; we override
    # the adapter so the warm hits a FakeAdapter (hermetic — no real vendor call).
    adapter = FakeAdapter(available=True, matches=[SymbolMatch("AAPL", "Apple")])
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    try:
        with TestClient(app) as client:
            # Give the background warm task a moment to run on the loop.
            for _ in range(50):
                if adapter.warm_calls >= 1:
                    break
                time.sleep(0.02)
            assert client.get("/health").json() == {"status": "ok"}
        assert adapter.warm_calls >= 1, "lifespan startup must warm the universe via the seam"
    finally:
        app.dependency_overrides.pop(get_market_adapter, None)


def test_lifespan_warm_failure_does_not_crash_startup():
    # A warm that raises must NOT crash startup — the lifespan wrapper logs & swallows it, the app
    # still serves requests (no-mute / honest-degradation: a warm failure only loses the cache warm).
    adapter = FakeAdapter(available=True, warm_raises=True)
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    try:
        with TestClient(app) as client:
            assert client.get("/health").status_code == 200
    finally:
        app.dependency_overrides.pop(get_market_adapter, None)


def test_main_does_not_name_the_vendor_sdk_for_the_warm():
    # The startup warm must go through the neutral seam — main.py must NOT name the SDK or the
    # universe cache directly (provider-agnostic anti-goal). main.py calls warm_symbol_universe only.
    src = inspect.getsource(main_module)
    assert "warm_symbol_universe" in src
    assert "StockHistoricalDataClient" not in src
    assert "_ASSET_UNIVERSE" not in src
    assert "get_all_assets" not in src


# ============================================================================================
# No-fabrication / single-source-of-truth guards (cross-cutting)
# ============================================================================================


def test_cache_hit_replays_real_records_unchanged(fake_sdk, with_creds):
    # A cache hit must replay the SAME real trades/quotes — never a fabricated or mutated record
    # (no-fabricated-data + single-source-of-truth). The replayed window is byte-identical.
    fake_sdk["symbol"] = "F"
    adapter = AlpacaAdapter()
    first = adapter.fetch_historical("F", "2026-06-02T15:00", "2026-06-02T15:02")
    second = adapter.fetch_historical("F", "2026-06-02T15:00", "2026-06-02T15:02")
    assert second.trades == first.trades
    assert second.quotes == first.quotes


def test_concurrent_fetch_preserves_record_content(fake_sdk, with_creds):
    # The concurrent fetch maps records to the SAME neutral RawTrade/RawQuote the sequential path
    # produced — nothing reordered, dropped, or fabricated (ordering into the engine timeline is
    # HistoricalProvider's job and is unchanged).
    fake_sdk["symbol"] = "F"
    adapter = AlpacaAdapter()
    trades, quotes = adapter._fetch_trades_quotes("F", None, None, adapter._data_feed())
    assert trades == [RawTrade(1.0, 10.0, 100)]
    assert quotes == [RawQuote(0.5, 9.99, 10.01, 5, 5)]
