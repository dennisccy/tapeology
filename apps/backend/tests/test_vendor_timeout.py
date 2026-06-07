"""Per-call vendor timeout gate (iter-9, J-22 backend half / no-unbounded-waits anti-goal).

A single outbound vendor request that gates a Watch — the historical-window fetch in
``_watch_historical`` and the market-clock pre-flight in ``_watch_live`` — runs under an explicit
``asyncio.wait_for(..., timeout=CONFIG.vendor_call_timeout_seconds)`` bound. A hung/slow vendor
therefore CANNOT block the Watch request indefinitely: it is refused with an explicit, distinct
``provider_timeout`` error and NO engine is created (no fabricated tape).

The bound is proven by a FakeAdapter that blocks its worker thread longer than a tiny test-set
timeout, so ``wait_for`` fires first. The timeout value is asserted to come from config (no inline
literal), and the post-timeout canonical read is a 404 (proving the watch was never registered).
"""

from __future__ import annotations

import dataclasses
import inspect

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.config import CONFIG
from app.main import app, get_market_adapter
from fakes import FakeAdapter

HIST_BODY = {
    "mode": "historical",
    "start": "2026-06-02T15:00",
    "end": "2026-06-02T15:02",
    "speed": 1,
}

# A tiny per-call bound for the tests; the fake vendor blocks far longer, so wait_for fires first.
TINY_TIMEOUT = 0.05
HANG_SECONDS = 2.0


@pytest.fixture
def tiny_timeout(monkeypatch):
    """Shrink the per-call vendor timeout to TINY_TIMEOUT so the bound fires quickly in tests.

    ``Config`` is a frozen dataclass (single source of truth), so we swap the module-level
    ``CONFIG`` for a ``replace``d copy rather than mutating the frozen instance — the production
    code reads ``CONFIG.vendor_call_timeout_seconds`` from this module reference.
    """
    fast = dataclasses.replace(CONFIG, vendor_call_timeout_seconds=TINY_TIMEOUT)
    monkeypatch.setattr(main_module, "CONFIG", fast)
    return fast


@pytest.fixture
def fake_client():
    def _make(**kwargs) -> TestClient:
        app.dependency_overrides[get_market_adapter] = lambda: FakeAdapter(**kwargs)
        return TestClient(app)

    yield _make
    app.dependency_overrides.pop(get_market_adapter, None)


# --- Config-sourced bound (no magic number) -------------------------------------------------

def test_vendor_call_timeout_seconds_exists_and_is_distinct_from_stale_gap():
    # The bound is a config constant (no inline literal in the route) and is a `*_seconds` float.
    assert isinstance(CONFIG.vendor_call_timeout_seconds, float)
    assert CONFIG.vendor_call_timeout_seconds > 0
    # It is a DIFFERENT knob than the mid-stream delivery-gap watchdog — they MUST NOT be merged.
    assert (
        CONFIG.vendor_call_timeout_seconds is not CONFIG.stale_gap_seconds
    )


def test_watch_route_reads_timeout_from_config_no_inline_literal():
    # The route wraps the vendor calls in asyncio.wait_for with the config-sourced timeout and
    # contains no inline numeric timeout literal in either wait_for call.
    src = inspect.getsource(main_module._watch_historical) + inspect.getsource(
        main_module._watch_live
    )
    assert "asyncio.wait_for" in src
    assert "CONFIG.vendor_call_timeout_seconds" in src
    # No bare numeric timeout= literal smuggled in beside the config read.
    assert "timeout=CONFIG.vendor_call_timeout_seconds" in src


# --- Historical fetch: a hung vendor times out -> provider_timeout, NO engine ----------------

def test_historical_hung_fetch_times_out_provider_timeout_no_engine(fake_client, tiny_timeout):
    client = fake_client(available=True, fetch_hang_seconds=HANG_SECONDS)
    resp = client.post("/watch/AAPL", json=HIST_BODY)
    assert resp.status_code == 504
    body = resp.json()
    assert body["reason"] == "provider_timeout"
    # iter-11 (J-28): a Historical-fetch timeout is ACTIONABLE for its real cause (the window
    # pulled too much data) — not the generic "please try again". The reason stays provider_timeout.
    assert body["detail"] == "that window is very high-volume — try a shorter range"
    assert "try a shorter range" in body["detail"]
    # No engine was created => a subsequent canonical read is an explicit 404 (no fabricated tape,
    # and the watch was never registered after the timeout).
    assert client.get("/tape/AAPL/state").status_code == 404


# --- Live market-clock pre-flight: a hung clock times out -> provider_timeout, NO engine -----

def test_live_hung_clock_times_out_provider_timeout_no_engine(fake_client, tiny_timeout):
    client = fake_client(available=True, clock_hang_seconds=HANG_SECONDS)
    resp = client.post("/watch/AAPL", json={"mode": "live"})
    assert resp.status_code == 504
    body = resp.json()
    assert body["reason"] == "provider_timeout"
    assert body["detail"] == "market data provider timed out"
    assert client.get("/tape/AAPL/state").status_code == 404


# --- provider_timeout is a distinct sibling of the other row-9 reasons -----------------------

def test_provider_timeout_reason_is_distinct(fake_client, tiny_timeout):
    timed_out = fake_client(available=True, fetch_hang_seconds=HANG_SECONDS).post(
        "/watch/AAPL", json=HIST_BODY
    )
    assert timed_out.json()["reason"] == "provider_timeout"
    # It is none of the existing real-data refusal reasons (a NEW additive sibling).
    assert timed_out.json()["reason"] not in {
        "provider_unavailable",
        "symbol_not_tradable",
        "no_data_for_window",
        "market_closed",
    }
    # The timeout body carries no spurious next_open (that field is market_closed-only).
    assert "next_open" not in timed_out.json()
