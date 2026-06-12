"""Hint API integration (capability 33, J-65): the live SIM-BIDABS hint fires past the dwell with the
honest absence citation on a fresh DB; the SIM-CHOP negative leg never fires; REST /research/hints/active
== the WS `hint` key verbatim (incl. `hint: null`); the hint log paginates + filters; the declared-from
linkage flips the record and 422s an unknown id; copy discipline (J-66) on the served hint copy.

Each test injects a TEMP-PATH journal store + registry (the existing dependency-override pattern) so the
suite stays hermetic. The default config's hint dwell (5.0s logical) fires within a couple wall-seconds of
SIM-BIDABS warming (the sim feeder paces ~0.04s/event during steady state, so 10 sustained events ≈ 0.4s)."""

import time

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, manager
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore


@pytest.fixture
def client(tmp_path):
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    manager.set_on_engine_created(registry.on_engine_created)
    with TestClient(app) as c:
        yield c
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    manager.set_on_engine_created(None)
    set_registry(None)
    store.close()


def _watch_until_state(client: TestClient, ticker: str, state: str, timeout: float = 12.0) -> None:
    r = client.post(f"/watch/{ticker}")
    assert r.status_code == 200
    deadline = time.time() + timeout
    while time.time() < deadline:
        summary = client.get(f"/tape/{ticker}/summary").json()
        if summary.get("market", {}).get("last") is not None and summary.get("tape_state") == state:
            return
        time.sleep(0.1)
    raise AssertionError(f"{ticker} did not warm to {state} in time")


def _wait_for_hint(client: TestClient, ticker: str, timeout: float = 12.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        hint = client.get(f"/research/hints/active?ticker={ticker}").json()["hint"]
        if hint is not None:
            return hint
        time.sleep(0.1)
    raise AssertionError(f"no active hint appeared for {ticker} in time")


# --- the happy path: SIM-BIDABS fires the hint with the honest absence citation -------------------

def test_bidabs_fires_hint_with_unvalidated_citation_on_fresh_db(client):
    _watch_until_state(client, "SIM-BIDABS", "bid_absorption")
    hint = _wait_for_hint(client, "SIM-BIDABS")
    # The fired hint describes the matching setup type + direction (absorption_reversal / long).
    assert hint["pattern_id"] == "sustained_bid_absorption"
    assert hint["setup_type"] == "absorption_reversal"
    assert hint["direction"] == "long"
    # No naked output: plain-language evidence with a measured value (the sustain seconds).
    assert hint["evidence"]
    assert "sustained" in hint["evidence"].lower()
    # Fresh DB -> no studied baseline -> EXACTLY the honest unvalidated string.
    assert hint["baseline_citation"] == "no studied baseline — unvalidated pattern"
    # Stamps present on every record (source / data_feed / config_fingerprint).
    assert hint["data_feed"] == "sim"
    assert hint["config_fingerprint"] == CONFIG.config_fingerprint()
    assert hint["bound_source"]
    # Copy discipline (J-66): no imperative / prediction / certainty / direction-command words.
    blob = f" {hint['evidence'].lower()} {hint['baseline_citation'].lower()} "
    for word in (" buy ", " sell ", " enter ", " exit ", "should ", "will ", "must ",
                 "predict", "target", "guarantee"):
        assert word not in blob, f"forbidden word {word!r} in hint copy"


def test_hint_appears_in_log_after_firing(client):
    _watch_until_state(client, "SIM-BIDABS", "bid_absorption")
    hint = _wait_for_hint(client, "SIM-BIDABS")
    log = client.get("/research/hints?ticker=SIM-BIDABS").json()["rows"]
    assert len(log) >= 1
    assert log[0]["id"] == hint["id"]
    assert log[0]["pattern_id"] == "sustained_bid_absorption"


# --- the negative leg: SIM-CHOP never fires -------------------------------------------------------

def test_chop_never_fires_a_hint(client):
    r = client.post("/watch/SIM-CHOP")
    assert r.status_code == 200
    # Watch SIM-CHOP at least as long as the BIDABS hint takes to fire; it must NEVER produce a hint
    # (its tape stays unclear in every window by construction — no arming state ever sustains).
    deadline = time.time() + 8.0
    while time.time() < deadline:
        hint = client.get("/research/hints/active?ticker=SIM-CHOP").json()["hint"]
        assert hint is None, "SIM-CHOP must never produce a hint"
        time.sleep(0.2)
    assert client.get("/research/hints?ticker=SIM-CHOP").json()["rows"] == []


# --- REST == WS verbatim --------------------------------------------------------------------------

def test_rest_active_hint_equals_ws_hint_key_verbatim(client):
    _watch_until_state(client, "SIM-BIDABS", "bid_absorption")
    _wait_for_hint(client, "SIM-BIDABS")
    rest = client.get("/research/hints/active?ticker=SIM-BIDABS").json()["hint"]
    assert rest is not None
    with client.websocket_connect("/tape/SIM-BIDABS/stream") as ws:
        ws_hint = ws.receive_json()["hint"]
    assert ws_hint is not None
    # Data-contract row 22: the WS hint key MUST equal the REST projection verbatim (one
    # hint_projection(), never a second path). The hint payload is fully static once fired.
    assert rest == ws_hint


def test_ws_hint_key_is_null_when_none(client):
    # A watched ticker with no fired hint yet carries `hint: null` (a NORMAL state, never an error).
    r = client.post("/watch/SIM-CHOP")
    assert r.status_code == 200
    with client.websocket_connect("/tape/SIM-CHOP/stream") as ws:
        frame = ws.receive_json()
    assert "hint" in frame
    assert frame["hint"] is None


def test_active_hint_on_not_watched_ticker_is_null(client):
    # Not watched -> hint: null (normal, not an error).
    r = client.get("/research/hints/active?ticker=SIM-NOTWATCHED")
    assert r.status_code == 200
    assert r.json()["hint"] is None


# --- the declared-from linkage: prefill never creates; valid id links + flips ----------------------

def test_declare_from_hint_links_thesis_and_flips_record(client):
    _watch_until_state(client, "SIM-BIDABS", "bid_absorption")
    hint = _wait_for_hint(client, "SIM-BIDABS")
    hint_id = hint["id"]
    # Declare a thesis FROM the hint (prefilled setup/direction; the user types the invalidation). The
    # declared_from_hint_id links the created thesis and flips the hint record.
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": hint["setup_type"],
            "direction": hint["direction"],
            "invalidation_price": 99.0,
            "declared_from_hint_id": hint_id,
        },
    )
    assert r.status_code == 200
    thesis_id = r.json()["thesis"]["id"]
    # The hint record is flipped to declared-from the created thesis (visible in the log).
    log = client.get("/research/hints?ticker=SIM-BIDABS").json()["rows"]
    matching = [row for row in log if row["id"] == hint_id]
    assert matching and matching[0]["declared_from"] == thesis_id


def test_declare_with_unknown_hint_id_is_422(client):
    _watch_until_state(client, "SIM-BIDABS", "bid_absorption")
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
            "declared_from_hint_id": "does-not-exist",
        },
    )
    assert r.status_code == 422
    assert "declared_from_hint_id" in r.json()["detail"]
    # Nothing persisted on the rejection: no active thesis.
    assert client.get("/research/thesis/active?ticker=SIM-BIDABS").json()["thesis"] is None


def test_normal_declare_without_hint_id_is_unchanged(client):
    # The J-38 unprefilled path is byte-unchanged: a declaration with no declared_from_hint_id works.
    _watch_until_state(client, "SIM-BIDABS", "bid_absorption")
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    )
    assert r.status_code == 200


# --- the log endpoint: pagination + ticker filter + malformed params ------------------------------

def test_hint_log_filters_by_ticker(client):
    _watch_until_state(client, "SIM-BIDABS", "bid_absorption")
    _wait_for_hint(client, "SIM-BIDABS")
    # A different ticker has no hints.
    assert client.get("/research/hints?ticker=SIM-ASKABS").json()["rows"] == []
    assert len(client.get("/research/hints?ticker=SIM-BIDABS").json()["rows"]) >= 1


def test_hint_log_pagination_clamps_and_offsets(client):
    _watch_until_state(client, "SIM-BIDABS", "bid_absorption")
    _wait_for_hint(client, "SIM-BIDABS")
    # An over-large / non-positive limit is clamped/defaulted (serving safety, never a 422).
    assert client.get("/research/hints?ticker=SIM-BIDABS&limit=0").status_code == 200
    assert client.get("/research/hints?ticker=SIM-BIDABS&limit=999999").status_code == 200
    # A non-integer limit is a 422 at the schema layer.
    assert client.get("/research/hints?ticker=SIM-BIDABS&limit=abc").status_code == 422


# --- freshness: pausing the watch clears the active hint; the log survives -------------------------

def test_pause_clears_active_hint_log_survives(client):
    _watch_until_state(client, "SIM-BIDABS", "bid_absorption")
    hint = _wait_for_hint(client, "SIM-BIDABS")
    # Pause the watch -> the stream flips to `paused` -> the active hint clears immediately.
    assert client.post("/watch/SIM-BIDABS/pause").status_code == 200
    deadline = time.time() + 5.0
    cleared = False
    while time.time() < deadline:
        if client.get("/research/hints/active?ticker=SIM-BIDABS").json()["hint"] is None:
            cleared = True
            break
        time.sleep(0.1)
    assert cleared, "pausing must clear the active hint (no 'is forming' over a non-live tape)"
    # The persisted log record survives the pause.
    log = client.get("/research/hints?ticker=SIM-BIDABS").json()["rows"]
    assert any(row["id"] == hint["id"] for row in log)


# --- taxonomy canary: the hint copy is backend-owned ----------------------------------------------

def test_taxonomy_serves_hint_copy_canary(client):
    payload = client.get("/research/taxonomy").json()
    assert "hints" in payload
    hints = payload["hints"]
    pattern_ids = {p["id"] for p in hints["patterns"]}
    assert pattern_ids == {
        "sustained_bid_absorption",
        "sustained_ask_absorption",
        "sustained_buyer_control",
        "sustained_seller_control",
    }
    assert hints["baseline_unvalidated"] == "no studied baseline — unvalidated pattern"
    copy = hints["copy"]
    assert copy["dock_title"] and copy["dock_register"].startswith("Descriptive only")
    assert set(hints["log_columns"].keys()) >= {"time", "ticker", "pattern", "evidence", "baseline"}
    # Copy discipline (J-66): no imperative / prediction / certainty words anywhere in the hint copy.
    blob = " ".join(
        [p["name"] for p in hints["patterns"]]
        + list(copy.values())
        + list(hints["log_columns"].values())
        + [hints["baseline_unvalidated"]]
    ).lower()
    for word in (" buy ", " sell ", " enter ", " exit ", "should ", "will ", "predict",
                 "target", "guarantee"):
        assert word not in f" {blob} ", f"forbidden word {word!r} in hint copy"
