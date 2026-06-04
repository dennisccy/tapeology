"""``GET /market/clock`` (Data Contract row 8): the canonical market-session endpoint read by
the Live market-status indicator. With credentials it serves the real open/closed + next
open/close; with no credentials it is an explicit ``available:false`` (null fields); a vendor/
network failure degrades to the same explicit unavailable — NEVER a fabricated open/closed.

Hermetic via ``FakeAdapter`` + ``dependency_overrides`` (no real network). Anti-goals exercised:
*no fabricated data* (degrade-to-unavailable rather than guess a session) and *single source of
truth* (one computing owner — the adapter — and one serving endpoint).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_market_adapter
from app.providers.adapters.base import MarketClock
from fakes import FakeAdapter

# Authoritative fixtures: ISO-8601 UTC (``Z``). ``next_open`` is non-null so the closed case can
# always tell the operator when the market reopens.
OPEN_CLOCK = MarketClock(
    is_open=True, next_open="2026-06-05T13:30:00Z", next_close="2026-06-04T20:00:00Z"
)
CLOSED_CLOCK = MarketClock(
    is_open=False, next_open="2026-06-05T13:30:00Z", next_close="2026-06-05T20:00:00Z"
)

UNAVAILABLE_BODY = {
    "available": False,
    "is_open": None,
    "next_open": None,
    "next_close": None,
}


@pytest.fixture
def fake_client():
    """A TestClient with the market-data adapter overridden by a FakeAdapter (hermetic)."""

    def _make(**kwargs) -> TestClient:
        app.dependency_overrides[get_market_adapter] = lambda: FakeAdapter(**kwargs)
        return TestClient(app)

    yield _make
    app.dependency_overrides.pop(get_market_adapter, None)


def test_market_clock_open_serves_real_status(fake_client):
    client = fake_client(available=True, clock=OPEN_CLOCK)
    resp = client.get("/market/clock")
    assert resp.status_code == 200
    assert resp.json() == {
        "available": True,
        "is_open": True,
        "next_open": OPEN_CLOCK.next_open,
        "next_close": OPEN_CLOCK.next_close,
    }


def test_market_clock_closed_has_non_null_next_open(fake_client):
    client = fake_client(available=True, clock=CLOSED_CLOCK)
    resp = client.get("/market/clock")
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    assert body["is_open"] is False
    assert body["next_open"] == CLOSED_CLOCK.next_open
    assert body["next_open"] is not None  # the operator is always told when it reopens


def test_market_clock_no_creds_is_unavailable_nulls(fake_client):
    # No credentials -> explicit unavailable with null fields; the adapter clock is NOT consulted
    # (FakeAdapter without a clock would raise if it were) — never a guessed open/closed.
    client = fake_client(available=False)
    resp = client.get("/market/clock")
    assert resp.status_code == 200
    assert resp.json() == UNAVAILABLE_BODY


def test_market_clock_adapter_error_degrades_to_unavailable(fake_client):
    # Creds present but the vendor call fails: degrade to the same explicit unavailable (benign,
    # like /symbols/search) — never a fabricated session state.
    client = fake_client(available=True, clock_raises=True)
    resp = client.get("/market/clock")
    assert resp.status_code == 200
    assert resp.json() == UNAVAILABLE_BODY
