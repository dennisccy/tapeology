"""Real-data gate (iter-1): the optional ``{mode}`` watch body routes sim vs. real, the
no-credentials gate returns an explicit 503 ``provider_unavailable`` with NO engine created,
an unknown mode is a 4xx, ``real_data_available`` reflects env presence/absence, and the
Alpaca credential names live in exactly one module.

Anti-goals exercised: *no fabricated data* (real-mode-no-creds => explicit 503 + a 404 on the
post-rejection read proves no synthesized snapshot), *no secrets in source* + *provider-agnostic
engine* (credential names confined to the single Alpaca adapter; the engine/API import no vendor
SDK), *single source of truth* (the sim path is byte-for-byte unchanged).
"""

import pathlib

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.providers.adapters.alpaca import AlpacaAdapter, real_data_available

ALPACA_ENV = ("ALPACA_API_KEY", "ALPACA_API_SECRET")
APP_DIR = pathlib.Path(__file__).resolve().parents[1] / "app"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def no_creds(monkeypatch):
    """Guarantee no Alpaca credentials are visible (the verification environment)."""
    for name in ALPACA_ENV:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


@pytest.fixture
def with_creds(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "test-key-123")
    monkeypatch.setenv("ALPACA_API_SECRET", "test-secret-456")
    return monkeypatch


# --- Backward-compatible sim routing (regression: no body / {} / mode:"sim" are unchanged) ---

def test_no_body_watch_still_watches_sim(client):
    resp = client.post("/watch/SIM-BUYER")
    assert resp.status_code == 200
    assert resp.json() == {"ticker": "SIM-BUYER", "scenario": "buyer_control", "status": "watching"}
    assert client.delete("/watch/SIM-BUYER").status_code == 200


def test_empty_object_body_watches_sim(client):
    resp = client.post("/watch/SIM-BUYER", json={})
    assert resp.status_code == 200
    assert resp.json() == {"ticker": "SIM-BUYER", "scenario": "buyer_control", "status": "watching"}
    assert client.delete("/watch/SIM-BUYER").status_code == 200


def test_mode_sim_body_watches_sim(client):
    resp = client.post("/watch/SIM-SELLER", json={"mode": "sim"})
    assert resp.status_code == 200
    assert resp.json() == {"ticker": "SIM-SELLER", "scenario": "seller_control", "status": "watching"}
    assert client.delete("/watch/SIM-SELLER").status_code == 200


def test_sim_mode_with_unknown_ticker_still_400(client):
    # The sim path's own validation is unchanged: an unknown sim ticker is an explicit 400.
    resp = client.post("/watch/NOPE123", json={"mode": "sim"})
    assert resp.status_code == 400
    assert client.get("/tape/NOPE123/state").status_code == 404


# --- No-credentials gate: explicit 503, NO engine created (no fabricated data) ---------------

def test_live_watch_without_creds_returns_503_and_creates_no_engine(client, no_creds):
    resp = client.post("/watch/AAPL", json={"mode": "live"})
    assert resp.status_code == 503
    body = resp.json()
    assert body["detail"] == "real-data provider unavailable"
    assert body["reason"] == "provider_unavailable"
    # No engine was created => a subsequent canonical read is an explicit 404, never a snapshot.
    assert client.get("/tape/AAPL/state").status_code == 404


def test_historical_watch_without_creds_returns_503_and_creates_no_engine(client, no_creds):
    resp = client.post(
        "/watch/AAPL",
        json={"mode": "historical", "start": "2025-01-02T14:30", "end": "2025-01-02T15:00", "speed": 2.0},
    )
    assert resp.status_code == 503
    body = resp.json()
    assert body["detail"] == "real-data provider unavailable"
    assert body["reason"] == "provider_unavailable"
    assert client.get("/tape/AAPL/state").status_code == 404


def test_live_watch_with_creds_does_not_fabricate_a_cockpit(client, with_creds):
    # Even WITH credentials, the real live/historical provider is not wired this iteration
    # (J-11/J-12). The watch MUST surface an explicit non-cockpit error — never a synthesized
    # cockpit/snapshot (no-fabricated-data anti-goal). Distinct reason from the no-creds case.
    resp = client.post("/watch/AAPL", json={"mode": "live"})
    assert resp.status_code == 503
    assert resp.json()["reason"] == "provider_not_implemented"
    assert client.get("/tape/AAPL/state").status_code == 404


# --- Unknown mode => explicit 4xx, no engine ------------------------------------------------

def test_unknown_mode_is_rejected_4xx(client, no_creds):
    resp = client.post("/watch/AAPL", json={"mode": "bogus"})
    assert resp.status_code == 422  # Pydantic Literal rejection (a 4xx; never a silent real feed)
    assert client.get("/tape/AAPL/state").status_code == 404


# --- real_data_available reflects env presence/absence (monkeypatched both ways) -------------

def test_real_data_available_false_without_creds(no_creds):
    assert real_data_available() is False
    assert AlpacaAdapter().is_available() is False


def test_real_data_available_true_with_creds(with_creds):
    assert real_data_available() is True
    assert AlpacaAdapter().is_available() is True


def test_partial_creds_are_not_available(monkeypatch):
    # Key present but secret absent must NOT count as available (both are required).
    monkeypatch.setenv("ALPACA_API_KEY", "test-key-123")
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)
    assert real_data_available() is False


def test_blank_creds_are_not_available(monkeypatch):
    # Empty / whitespace values (as shipped in .env.example) are NOT credentials.
    monkeypatch.setenv("ALPACA_API_KEY", "  ")
    monkeypatch.setenv("ALPACA_API_SECRET", "")
    assert real_data_available() is False


def test_default_feed_is_iex(monkeypatch):
    # The free IEX feed is the default when ALPACA_FEED is unset (non-secret config).
    monkeypatch.delenv("ALPACA_FEED", raising=False)
    assert AlpacaAdapter().feed == "iex"


def test_configured_feed_is_used(monkeypatch):
    monkeypatch.setenv("ALPACA_FEED", "sip")
    assert AlpacaAdapter().feed == "sip"


# --- Single-module confinement: vendor credential names + SDK live in exactly one module -----

def test_alpaca_credential_names_confined_to_one_module():
    hits = sorted(
        p.relative_to(APP_DIR).as_posix()
        for p in APP_DIR.rglob("*.py")
        if "ALPACA_API_KEY" in p.read_text() or "ALPACA_API_SECRET" in p.read_text()
    )
    assert hits == ["providers/adapters/alpaca.py"]


def test_engine_and_canonical_modules_reference_no_vendor():
    # The engine, config, serializers, and the existing providers stay vendor-agnostic — no
    # "alpaca" reference leaks into them (the seam keeps vendor specifics in the one adapter).
    targets = ["engine", "config.py", "serializers.py", "providers/base.py", "providers/simulated.py"]
    for rel in targets:
        target = APP_DIR / rel
        files = list(target.rglob("*.py")) if target.is_dir() else [target]
        for f in files:
            assert "alpaca" not in f.read_text().lower(), f"{f} unexpectedly references alpaca"
