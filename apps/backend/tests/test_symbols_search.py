"""GET /symbols/search (J-13): real matches, the config limit, and honest graceful degrade.

The adapter is injected via dependency_overrides (a FakeAdapter) so the suite is hermetic —
no real network call. Free-text watch entry must always remain possible, so a short/empty
query, missing credentials, or an adapter error each yields an empty list (never an error,
never a fabricated suggestion).
"""

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter
from app.providers.adapters.base import SymbolMatch
from fakes import FakeAdapter


@pytest.fixture
def search_client():
    def _make(**kwargs) -> TestClient:
        app.dependency_overrides[get_market_adapter] = lambda: FakeAdapter(**kwargs)
        return TestClient(app)

    yield _make
    app.dependency_overrides.pop(get_market_adapter, None)


def test_search_returns_matching_symbol_and_name(search_client):
    matches = [
        SymbolMatch("AAPL", "Apple Inc. Common Stock"),
        SymbolMatch("AAPLW", "Apple Warrant"),
        SymbolMatch("MSFT", "Microsoft Corp"),
    ]
    client = search_client(available=True, matches=matches)
    resp = client.get("/symbols/search", params={"q": "AAPL"})
    assert resp.status_code == 200
    assert resp.json() == [
        {"symbol": "AAPL", "name": "Apple Inc. Common Stock"},
        {"symbol": "AAPLW", "name": "Apple Warrant"},
    ]


def test_search_matches_on_name_too(search_client):
    matches = [SymbolMatch("F", "Ford Motor Company"), SymbolMatch("GM", "General Motors")]
    client = search_client(available=True, matches=matches)
    resp = client.get("/symbols/search", params={"q": "ford"})
    assert resp.status_code == 200
    assert resp.json() == [{"symbol": "F", "name": "Ford Motor Company"}]


def test_empty_query_returns_empty_list_without_calling_adapter(search_client):
    adapter = FakeAdapter(available=True, matches=[SymbolMatch("AAPL", "Apple")])
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    client = TestClient(app)
    resp = client.get("/symbols/search", params={"q": "   "})  # blank after strip
    assert resp.status_code == 200
    assert resp.json() == []
    assert adapter.search_calls == []  # no adapter work for a blank query
    app.dependency_overrides.pop(get_market_adapter, None)


def test_search_caps_results_to_config_limit(search_client):
    over = CONFIG.symbol_search_limit + 5
    matches = [SymbolMatch(f"AA{i:03d}", f"Test AA {i}") for i in range(over)]
    client = search_client(available=True, matches=matches)
    resp = client.get("/symbols/search", params={"q": "AA"})
    assert resp.status_code == 200
    assert len(resp.json()) == CONFIG.symbol_search_limit


def test_search_without_credentials_returns_empty(search_client):
    # No creds -> graceful free-text degrade (the unavailable state is surfaced at Watch, not here).
    client = search_client(available=False, matches=[SymbolMatch("AAPL", "Apple")])
    resp = client.get("/symbols/search", params={"q": "AAPL"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_adapter_error_degrades_to_empty(search_client):
    client = search_client(available=True, search_raises=True)
    resp = client.get("/symbols/search", params={"q": "AAPL"})
    assert resp.status_code == 200  # never a 500; never fabricated suggestions
    assert resp.json() == []
