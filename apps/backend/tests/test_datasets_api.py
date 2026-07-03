"""The ``/research/datasets*`` endpoints (era-3 capability 1, J-02) — record/register, list, detail.

Exactly THREE routes exist (Product Shape): ``POST /research/datasets`` (record/register — an
explicit research action, never ambient), ``GET /research/datasets`` (list), and
``GET /research/datasets/{id}`` (detail). There is NO PATCH/PUT/DELETE — immutability is
structural. Validation is explicit and never silent coercion: unknown source / bad split /
missing window are 422; an unknown id is 404; re-recording already-registered content (the
re-tag attempt) is 409; a corrupted file is an explicit 500 integrity error, and the list
surfaces corrupt files in ``integrity_errors`` rather than silently hiding them.

Also locked here: watching a sim ticker end-to-end writes ZERO dataset files (recording is an
explicit research action — the no-ambient-recording anti-goal).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore
from fakes import FakeAdapter, load_fixture_window

TRAIN_START, TRAIN_END = "2026-06-09T17:00:00Z", "2026-06-09T17:01:00Z"
HOLDOUT_START, HOLDOUT_END = "2026-06-09T17:05:00Z", "2026-06-09T17:05:45Z"


def _reference_body(split: str, start: str = TRAIN_START, end: str = TRAIN_END) -> dict:
    return {"source_kind": "reference", "split": split, "start": start, "end": end}


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    dataset_dir = tmp_path / "datasets"
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(dataset_dir))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    manager.set_on_engine_created(registry.on_engine_created)
    with TestClient(app) as client:
        yield client, dataset_dir
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    manager.set_on_engine_created(None)
    set_registry(None)
    app.dependency_overrides.pop(get_market_adapter, None)
    store.close()


# --- record/register (the explicit research action) -----------------------------------------------


def test_post_reference_records_and_registers_a_dataset_keyless(ctx):
    client, dataset_dir = ctx
    r = client.post("/research/datasets", json=_reference_body("train"))
    assert r.status_code == 200
    meta = r.json()["dataset"]
    assert meta["symbol"] == "PG"
    assert meta["split"] == "train"
    assert meta["window_start_utc"] == TRAIN_START
    assert meta["window_end_utc"] == TRAIN_END
    assert meta["data_feed"] == CONFIG.historical_feed
    assert meta["event_counts"]["trades"] > 0
    assert meta["event_counts"]["quotes"] > 0
    assert len(meta["checksum"]) == 64
    # The dataset landed as ONE file in the configured dataset dir.
    assert len(list(dataset_dir.glob("*.json"))) == 1


def test_list_and_detail_serve_the_stored_metadata_verbatim(ctx):
    client, _dataset_dir = ctx
    train = client.post("/research/datasets", json=_reference_body("train")).json()["dataset"]
    holdout = client.post(
        "/research/datasets", json=_reference_body("holdout", HOLDOUT_START, HOLDOUT_END)
    ).json()["dataset"]

    listed = client.get("/research/datasets")
    assert listed.status_code == 200
    body = listed.json()
    assert body["integrity_errors"] == []
    assert [row["id"] for row in body["datasets"]] == [train["id"], holdout["id"]]
    assert body["datasets"][0] == train  # the stored row, verbatim — no recompute at read
    assert body["datasets"][1] == holdout

    detail = client.get(f"/research/datasets/{train['id']}")
    assert detail.status_code == 200
    assert detail.json()["dataset"] == train


def test_unknown_dataset_id_is_404(ctx):
    client, _dataset_dir = ctx
    r = client.get("/research/datasets/no-such-id")
    assert r.status_code == 404
    assert "no-such-id" in r.json()["detail"]


# --- split immutability over REST: the re-tag attempt is a 409 ------------------------------------


def test_retag_attempt_is_refused_409(ctx):
    client, _dataset_dir = ctx
    first = client.post("/research/datasets", json=_reference_body("train"))
    assert first.status_code == 200
    original = first.json()["dataset"]

    # Same content, DIFFERENT split — the re-tag attempt. Refused; the tag is frozen.
    retag = client.post("/research/datasets", json=_reference_body("holdout"))
    assert retag.status_code == 409
    assert original["id"] in retag.json()["detail"]
    assert "frozen" in retag.json()["detail"]

    # Same content, same split — the dataset is immutable; re-recording is refused too.
    duplicate = client.post("/research/datasets", json=_reference_body("train"))
    assert duplicate.status_code == 409

    # The registered tag is untouched.
    assert client.get(f"/research/datasets/{original['id']}").json()["dataset"]["split"] == "train"


# --- validation: 422 matrix (never silent coercion) ------------------------------------------------


def test_bad_split_value_is_422(ctx):
    client, _dataset_dir = ctx
    r = client.post(
        "/research/datasets",
        json={"source_kind": "reference", "split": "test", "start": TRAIN_START, "end": TRAIN_END},
    )
    assert r.status_code == 422
    assert "split" in r.json()["detail"]


def test_unknown_source_kind_is_422(ctx):
    client, _dataset_dir = ctx
    r = client.post("/research/datasets", json={"source_kind": "telepathy", "split": "train"})
    assert r.status_code == 422


def test_sim_source_is_not_recordable(ctx):
    # Datasets are HISTORICAL tape: a seeded sim stream reproduces on demand, so recording one
    # is refused (422) — 'sim' is not a dataset source kind.
    client, _dataset_dir = ctx
    r = client.post(
        "/research/datasets",
        json={"source_kind": "sim", "source_id": "SIM-BUYER", "split": "train"},
    )
    assert r.status_code == 422


def test_unknown_reference_id_is_422(ctx):
    client, _dataset_dir = ctx
    r = client.post(
        "/research/datasets",
        json={"source_kind": "reference", "source_id": "NOT_A_REFERENCE", "split": "train"},
    )
    assert r.status_code == 422


def test_historical_missing_window_is_422(ctx):
    client, _dataset_dir = ctx
    r = client.post(
        "/research/datasets", json={"source_kind": "historical", "source_id": "F", "split": "train"}
    )
    assert r.status_code == 422
    assert "start and end" in r.json()["detail"]


def test_historical_missing_symbol_is_422(ctx):
    client, _dataset_dir = ctx
    r = client.post(
        "/research/datasets",
        json={"source_kind": "historical", "split": "train", "start": TRAIN_START, "end": TRAIN_END},
    )
    assert r.status_code == 422


def test_malformed_iso_window_is_422(ctx):
    client, _dataset_dir = ctx
    r = client.post(
        "/research/datasets",
        json={"source_kind": "reference", "split": "train", "start": "yesterday", "end": TRAIN_END},
    )
    assert r.status_code == 422


def test_end_not_after_start_is_422(ctx):
    client, _dataset_dir = ctx
    r = client.post(
        "/research/datasets",
        json={"source_kind": "reference", "split": "train", "start": TRAIN_END, "end": TRAIN_START},
    )
    assert r.status_code == 422


def test_half_open_window_only_one_bound_is_422(ctx):
    client, _dataset_dir = ctx
    r = client.post(
        "/research/datasets",
        json={"source_kind": "reference", "split": "train", "start": TRAIN_START},
    )
    assert r.status_code == 422


def test_empty_window_is_422_and_writes_nothing(ctx):
    client, dataset_dir = ctx
    r = client.post(
        "/research/datasets",
        json=_reference_body("train", "2026-06-09T16:00:00Z", "2026-06-09T16:01:00Z"),
    )
    assert r.status_code == 422
    assert "no events" in r.json()["detail"]
    assert not list(dataset_dir.glob("*.json")) if dataset_dir.exists() else True


def test_historical_without_credentials_is_an_explicit_422(ctx):
    client, _dataset_dir = ctx
    app.dependency_overrides[get_market_adapter] = lambda: FakeAdapter(available=False)
    r = client.post(
        "/research/datasets",
        json={
            "source_kind": "historical",
            "source_id": "F",
            "split": "train",
            "start": "2026-06-02T15:00:00Z",
            "end": "2026-06-02T15:02:00Z",
        },
    )
    assert r.status_code == 422
    assert "unavailable" in r.json()["detail"]


def test_historical_records_through_the_existing_adapter_seam(ctx):
    client, _dataset_dir = ctx
    window, _raw = load_fixture_window()  # the committed F window (REAL captured data)
    adapter = FakeAdapter(window=window)
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    r = client.post(
        "/research/datasets",
        json={
            "source_kind": "historical",
            "source_id": "F",
            "split": "holdout",
            "start": "2026-06-02T15:00:00Z",
            "end": "2026-06-02T15:02:00Z",
        },
    )
    assert r.status_code == 200
    meta = r.json()["dataset"]
    assert meta["symbol"] == "F"
    assert meta["split"] == "holdout"
    assert meta["data_feed"] == CONFIG.historical_feed
    assert meta["event_counts"]["total"] > 0
    # The fetch went through the EXISTING neutral adapter seam, once.
    assert len(adapter.fetch_calls) == 1
    assert adapter.fetch_calls[0][0] == "F"


# --- integrity: a corrupted file is explicit, never silent -----------------------------------------


def test_corrupted_dataset_file_surfaces_explicitly_on_detail_and_list(ctx):
    client, dataset_dir = ctx
    healthy = client.post("/research/datasets", json=_reference_body("train")).json()["dataset"]
    corrupt = client.post(
        "/research/datasets", json=_reference_body("holdout", HOLDOUT_START, HOLDOUT_END)
    ).json()["dataset"]

    # Tamper one stored print in the second dataset's file.
    path = dataset_dir / f"{corrupt['id']}.json"
    data = json.loads(path.read_text())
    for row in data["record"]["events"]:
        if row["type"] == "trade":
            row["price"] += 1.0
            break
    path.write_text(json.dumps(data))

    detail = client.get(f"/research/datasets/{corrupt['id']}")
    assert detail.status_code == 500
    assert "integrity" in detail.json()["detail"]

    listed = client.get("/research/datasets").json()
    # The healthy dataset still serves; the corrupt one is surfaced EXPLICITLY — not silently
    # hidden, not fabricated.
    assert [row["id"] for row in listed["datasets"]] == [healthy["id"]]
    assert len(listed["integrity_errors"]) == 1
    assert f"{corrupt['id']}.json" in listed["integrity_errors"][0]["file"]


# --- no ambient recording ---------------------------------------------------------------------------


def test_watching_a_sim_ticker_end_to_end_writes_zero_dataset_files(ctx):
    client, dataset_dir = ctx
    assert client.post("/watch/SIM-BUYER").status_code == 200
    deadline = time.time() + 15
    while time.time() < deadline:
        state = client.get("/tape/SIM-BUYER/state")
        if state.status_code == 200 and state.json()["timestamp"] > 0:
            break
        time.sleep(0.1)
    else:
        raise AssertionError("SIM-BUYER never delivered an event")
    assert client.delete("/watch/SIM-BUYER").status_code == 200
    # The watch path never touches the dataset store: no dir, no files, nothing ambient.
    assert not dataset_dir.exists() or list(dataset_dir.glob("*")) == []
