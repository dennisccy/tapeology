"""The ``/research/backtests*`` endpoints (era-3 capability 4, J-03) — create / list / detail / cancel.

Exactly FOUR routes on the existing research router (Product Shape): ``POST /research/backtests``
(create + start the cancellable job), ``GET /research/backtests`` (list), ``GET
/research/backtests/{id}`` (detail), ``POST /research/backtests/{id}/cancel``. GET serves the
runner's persisted rows VERBATIM — no recomputation on read (Data Contract row 31). Validation is
honest and distinct: unknown dataset id -> 404; unknown strategy id -> 422; an UNREGISTERED
profile -> 422 (``default`` plus the J-06 candidate ``candidate-faster-warmup`` are both
accepted — ``Config.profile_definition`` is the ONE registry, see
``tests/test_profile_equivalence.py`` for its resolution/fingerprint unit tests); malformed body
-> 422; cancel mirrors studies (404 unknown / 409 terminal).

Everything is keyless: the dataset under test is recorded over the API through the committed PG
SIP reference window (the iter-2-proven flow), and the backtest job runs as a real background
thread polled to terminal (bounded).
"""

from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG, PROFILE_CANDIDATE_FASTER_WARMUP, STRATEGY_V1_ID
from app.main import app, get_market_adapter, manager
from app.research.backtests import PROFILE_DEFAULT, REGISTER
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore

TRAIN_START, TRAIN_END = "2026-06-09T17:00:00Z", "2026-06-09T17:01:00Z"


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    manager.set_on_engine_created(registry.on_engine_created)
    with TestClient(app) as c:
        yield c, store, registry
    registry.study_jobs.join_all(timeout=10.0)
    registry.backtest_jobs.join_all(timeout=10.0)
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    manager.set_on_engine_created(None)
    set_registry(None)
    app.dependency_overrides.pop(get_market_adapter, None)
    store.close()


def _record_reference_dataset(client, start=TRAIN_START, end=TRAIN_END) -> dict:
    r = client.post(
        "/research/datasets",
        json={"source_kind": "reference", "split": "train", "start": start, "end": end},
    )
    assert r.status_code == 200, r.text
    return r.json()["dataset"]


def _poll_until_terminal(client, backtest_id, attempts=400):
    for _ in range(attempts):
        pl = client.get(f"/research/backtests/{backtest_id}").json()["backtest"]
        if pl["status"] in ("done", "failed", "cancelled"):
            return pl
        time.sleep(0.05)
    raise AssertionError(f"backtest {backtest_id} did not reach a terminal status")


def _create(client, dataset_id, *, strategy_id=STRATEGY_V1_ID, profile=PROFILE_DEFAULT):
    return client.post(
        "/research/backtests",
        json={"dataset_id": dataset_id, "strategy_id": strategy_id, "profile": profile},
    )


# --- create + start (background job -> done) -------------------------------------------------------


def test_create_runs_to_done_with_the_full_provenanced_report(ctx):
    client, _store, _reg = ctx
    dataset = _record_reference_dataset(client)
    r = _create(client, dataset["id"])
    assert r.status_code == 200, r.text
    created = r.json()["backtest"]
    assert created["status"] == "queued"
    assert created["dataset_id"] == dataset["id"]
    assert created["strategy_id"] == STRATEGY_V1_ID
    assert created["profile"] == PROFILE_DEFAULT
    assert created["null_baseline_seed"] == CONFIG.backtest_null_baseline_seed
    assert created["config_fingerprint"] == CONFIG.config_fingerprint()

    pl = _poll_until_terminal(client, created["id"])
    assert pl["status"] == "done"
    result = pl["result"]
    # The visible simulated register — every $ beside its R, its n, its assumptions.
    assert result["register"] == REGISTER
    # Full provenance: dataset id + checksum (the stored metadata verbatim), the strategy config
    # echoed verbatim, the profile id, and the config fingerprint.
    assert result["dataset"]["id"] == dataset["id"]
    assert result["dataset"]["checksum"] == dataset["checksum"]
    assert result["strategy"] == CONFIG.strategy_definition(STRATEGY_V1_ID)
    assert result["profile"] == PROFILE_DEFAULT
    assert result["config_fingerprint"] == CONFIG.config_fingerprint()
    # Aggregates: net AND gross R AND $, win rate, max drawdown (R), n — beside the seeded null.
    agg = result["aggregates"]
    assert set(agg) == {"n", "gross_r", "net_r", "gross_usd", "net_usd", "win_rate", "max_drawdown_r"}
    assert agg["n"] == len(result["trades"])
    nb = result["null_baseline"]
    assert nb["seed"] == CONFIG.backtest_null_baseline_seed
    assert nb["entry_count"] == CONFIG.backtest_null_entry_count
    assert set(nb["aggregates"]) == set(agg)


def test_detail_serves_the_persisted_payload_verbatim(ctx):
    client, store, _reg = ctx
    dataset = _record_reference_dataset(client)
    bid = _create(client, dataset["id"]).json()["backtest"]["id"]
    pl = _poll_until_terminal(client, bid)
    # No recomputation on read: the served detail IS the stored row.
    assert pl == store.get_backtest(bid).payload


def test_list_returns_created_backtests_most_recent_first(ctx):
    client, _store, _reg = ctx
    dataset = _record_reference_dataset(client)
    bid = _create(client, dataset["id"]).json()["backtest"]["id"]
    _poll_until_terminal(client, bid)
    listed = client.get("/research/backtests").json()["backtests"]
    assert len(listed) == 1
    assert listed[0]["id"] == bid
    assert listed[0]["status"] == "done"


def test_identical_request_rerun_is_byte_identical_over_the_api(ctx):
    client, _store, _reg = ctx
    dataset = _record_reference_dataset(client)
    first = _poll_until_terminal(client, _create(client, dataset["id"]).json()["backtest"]["id"])
    second = _poll_until_terminal(client, _create(client, dataset["id"]).json()["backtest"]["id"])
    assert first["id"] != second["id"]
    assert json.dumps(first["result"], sort_keys=True) == json.dumps(second["result"], sort_keys=True)


# --- error matrix (honest, distinct, nothing persisted on rejection) --------------------------------


def test_unknown_dataset_id_is_404(ctx):
    client, _store, _reg = ctx
    r = _create(client, "no-such-dataset")
    assert r.status_code == 404
    assert client.get("/research/backtests").json()["backtests"] == []


def test_unknown_strategy_id_is_422(ctx):
    client, _store, _reg = ctx
    dataset = _record_reference_dataset(client)
    r = _create(client, dataset["id"], strategy_id="v2")
    assert r.status_code == 422
    assert client.get("/research/backtests").json()["backtests"] == []


def test_unregistered_profile_is_422(ctx):
    client, _store, _reg = ctx
    dataset = _record_reference_dataset(client)
    r = _create(client, dataset["id"], profile="nonexistent-profile")
    assert r.status_code == 422
    assert "nonexistent-profile" in r.json()["detail"]
    assert client.get("/research/backtests").json()["backtests"] == []


def test_registered_candidate_profile_is_accepted_and_runs_to_done(ctx):
    # J-06: a candidate registered in Config.profile_definition is accepted (previously 422 for
    # ANY non-default profile) and produces a report stamped with its own profile id and a
    # config_fingerprint distinct from default's — the SAME hasher, no second mechanism.
    client, _store, _reg = ctx
    dataset = _record_reference_dataset(client)
    r = _create(client, dataset["id"], profile=PROFILE_CANDIDATE_FASTER_WARMUP)
    assert r.status_code == 200, r.text
    created = r.json()["backtest"]
    assert created["profile"] == PROFILE_CANDIDATE_FASTER_WARMUP
    assert created["config_fingerprint"] != CONFIG.config_fingerprint()

    pl = _poll_until_terminal(client, created["id"])
    assert pl["status"] == "done"
    result = pl["result"]
    assert result["profile"] == PROFILE_CANDIDATE_FASTER_WARMUP
    assert result["config_fingerprint"] == created["config_fingerprint"]
    assert result["config_fingerprint"] != CONFIG.config_fingerprint()


def test_malformed_body_is_422(ctx):
    client, _store, _reg = ctx
    assert client.post("/research/backtests", json={"strategy_id": STRATEGY_V1_ID}).status_code == 422
    assert client.post("/research/backtests", json={}).status_code == 422
    assert client.post(
        "/research/backtests", json={"dataset_id": 12.5, "strategy_id": [], "profile": {}}
    ).status_code == 422


def test_unknown_backtest_id_detail_is_404(ctx):
    client, _store, _reg = ctx
    assert client.get("/research/backtests/nope").status_code == 404


def test_cancel_unknown_id_is_404(ctx):
    client, _store, _reg = ctx
    assert client.post("/research/backtests/nope/cancel").status_code == 404


def test_cancel_terminal_backtest_is_409(ctx):
    client, _store, _reg = ctx
    dataset = _record_reference_dataset(client)
    bid = _create(client, dataset["id"]).json()["backtest"]["id"]
    _poll_until_terminal(client, bid)
    r = client.post(f"/research/backtests/{bid}/cancel")
    assert r.status_code == 409
    assert "done" in r.json()["detail"]


def test_cancel_mid_run_resolves_to_cancelled_without_a_result(ctx):
    client, _store, _reg = ctx
    # The FULL committed reference window (~14k events) replays for several seconds, so an
    # immediate cancel reliably lands while the job is queued/running; cooperative cancellation
    # resolves it to explicit ``cancelled`` with NO result block (a partial simulated PnL is
    # never served).
    dataset = _record_reference_dataset(client, start=None, end=None)
    created = _create(client, dataset["id"]).json()["backtest"]
    r = client.post(f"/research/backtests/{created['id']}/cancel")
    assert r.status_code == 200
    assert r.json() == {"backtest_id": created["id"], "cancelling": True}
    pl = _poll_until_terminal(client, created["id"])
    assert pl["status"] == "cancelled"
    assert "result" not in pl
