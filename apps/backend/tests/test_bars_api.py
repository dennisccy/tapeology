"""The ``/research/bars*`` endpoints (era-4 capability 1, J-01) — record/register, list, detail.

Exactly THREE routes exist (Product Shape, the ``test_datasets_api.py`` precedent): ``POST
/research/bars`` (the explicit credentialed record/register action — recording is never
ambient), ``GET /research/bars`` (list), and ``GET /research/bars/{id}`` (detail). There is NO
PATCH/PUT/DELETE — immutability is structural. Validation is explicit and never silent coercion:
an out-of-set timeframe / missing symbol / bad window are 422; an unknown id is 404;
re-recording already-registered content is 409; a corrupted file is an explicit 500 integrity
error surfaced in ``integrity_errors`` on list rather than hidden.

Missing credentials on ``POST`` is the EXISTING explicit unavailable (503) state (never
fabricated bars) — per the spec's explicit Definition-of-Done/Testing-Requirements text, this is
DISTINCT from the 422 the historical-DATASET path uses for the analogous credentials gap.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager
from app.providers.adapters.base import RawBar, VendorTimeout
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore
from fakes import FakeAdapter

SYMBOL = "PG"
TIMEFRAME = "1d"
START, END = "2026-06-01T00:00:00Z", "2026-06-04T00:00:00Z"
_BASE_EPOCH = 1780358400.0  # 2026-06-01T00:00:00Z
_DAY = 86400.0


def _bars(symbol: str = SYMBOL, timeframe: str = TIMEFRAME) -> tuple[RawBar, ...]:
    return (
        RawBar(symbol, timeframe, _BASE_EPOCH, 148.0, 149.5, 147.5, 149.0, 1_000_000),
        RawBar(symbol, timeframe, _BASE_EPOCH + _DAY, 149.0, 150.0, 148.5, 149.8, 1_100_000),
        RawBar(symbol, timeframe, _BASE_EPOCH + 2 * _DAY, 149.8, 151.0, 149.2, 150.5, 1_050_000),
    )


def _body(symbol: str = SYMBOL, timeframe: str = TIMEFRAME, start: str = START, end: str = END) -> dict:
    return {"symbol": symbol, "timeframe": timeframe, "start": start, "end": end}


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    bar_dir = tmp_path / "bars"
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(bar_dir))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    manager.set_on_engine_created(registry.on_engine_created)
    with TestClient(app) as client:
        yield client, bar_dir
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    manager.set_on_engine_created(None)
    set_registry(None)
    app.dependency_overrides.pop(get_market_adapter, None)
    store.close()


def _inject_adapter(**kwargs) -> FakeAdapter:
    adapter = FakeAdapter(**kwargs)
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    return adapter


# --- record/register (the explicit credentialed research action) --------------------------------


def test_post_records_and_registers_a_bar_series(ctx):
    client, bar_dir = ctx
    _inject_adapter(bars=_bars())
    r = client.post("/research/bars", json=_body())
    assert r.status_code == 200
    meta = r.json()["bar_series"]
    assert meta["symbol"] == SYMBOL
    assert meta["timeframe"] == TIMEFRAME
    assert meta["window_start_utc"] == START
    assert meta["window_end_utc"] == END
    assert meta["feed"] == CONFIG.historical_feed
    assert meta["bar_count"] == 3
    assert len(meta["checksum"]) == 64
    assert len(meta["bars"]) == 3
    # The bar series landed as ONE file in the configured bar dir.
    assert len(list(bar_dir.glob("*.json"))) == 1


def test_list_and_detail_serve_the_stored_metadata_verbatim(ctx):
    client, _bar_dir = ctx
    _inject_adapter(bars=_bars())
    posted = client.post("/research/bars", json=_body()).json()["bar_series"]

    listed = client.get("/research/bars")
    assert listed.status_code == 200
    body = listed.json()
    assert body["integrity_errors"] == []
    assert [row["id"] for row in body["bar_series"]] == [posted["id"]]
    assert body["bar_series"][0] == posted  # the stored row, verbatim — no recompute at read

    detail = client.get(f"/research/bars/{posted['id']}")
    assert detail.status_code == 200
    assert detail.json()["bar_series"] == posted


def test_unknown_bar_series_id_is_404(ctx):
    client, _bar_dir = ctx
    r = client.get("/research/bars/no-such-id")
    assert r.status_code == 404
    assert "no-such-id" in r.json()["detail"]


# --- immutability over REST: re-recording identical content is a 409 ------------------------------


def test_duplicate_content_is_refused_409(ctx):
    client, _bar_dir = ctx
    _inject_adapter(bars=_bars())
    first = client.post("/research/bars", json=_body())
    assert first.status_code == 200
    original = first.json()["bar_series"]

    duplicate = client.post("/research/bars", json=_body())
    assert duplicate.status_code == 409
    assert original["id"] in duplicate.json()["detail"]

    # The registered series is untouched — exactly one file still on disk.
    assert client.get(f"/research/bars/{original['id']}").json()["bar_series"]["bar_count"] == 3


# --- validation: 422 matrix (never silent coercion) -----------------------------------------------


def test_bad_timeframe_value_is_422(ctx):
    client, _bar_dir = ctx
    assert "17m" not in CONFIG.bar_timeframes
    r = client.post("/research/bars", json=_body(timeframe="17m"))
    assert r.status_code == 422
    assert "timeframe" in r.json()["detail"]


def test_missing_symbol_is_422(ctx):
    client, _bar_dir = ctx
    r = client.post("/research/bars", json=_body(symbol=""))
    assert r.status_code == 422
    assert "symbol" in r.json()["detail"]


def test_malformed_iso_window_is_422(ctx):
    client, _bar_dir = ctx
    r = client.post("/research/bars", json=_body(start="yesterday"))
    assert r.status_code == 422


def test_end_not_after_start_is_422(ctx):
    client, _bar_dir = ctx
    r = client.post("/research/bars", json=_body(start=END, end=START))
    assert r.status_code == 422


def test_empty_fetch_result_is_422_and_writes_nothing(ctx):
    client, bar_dir = ctx
    _inject_adapter(bars=())
    r = client.post("/research/bars", json=_body())
    assert r.status_code == 422
    assert "no bars" in r.json()["detail"]
    assert not bar_dir.exists() or list(bar_dir.glob("*.json")) == []


# --- missing credentials: the EXISTING explicit unavailable (503) state, never fabricated ---------


def test_missing_credentials_is_an_explicit_503(ctx):
    client, bar_dir = ctx
    _inject_adapter(available=False)
    r = client.post("/research/bars", json=_body())
    assert r.status_code == 503
    assert "unavailable" in r.json()["detail"]
    assert not bar_dir.exists() or list(bar_dir.glob("*.json")) == []


# --- vendor timeout: the neutral VendorTimeout maps to the existing 504 --------------------------


def test_vendor_timeout_is_504(ctx):
    client, _bar_dir = ctx
    _inject_adapter(bars=(), bars_raise=VendorTimeout("that window is very high-volume — try a shorter range"))
    r = client.post("/research/bars", json=_body())
    assert r.status_code == 504


# --- integrity: a corrupted file is explicit, never silent ----------------------------------------


def test_corrupted_bar_series_file_surfaces_explicitly_on_detail_and_list(ctx):
    client, bar_dir = ctx
    _inject_adapter(bars=_bars())
    healthy = client.post("/research/bars", json=_body()).json()["bar_series"]

    _inject_adapter(bars=_bars(symbol="F", timeframe="1h"))
    corrupt = client.post("/research/bars", json=_body(symbol="F", timeframe="1h")).json()["bar_series"]

    path = bar_dir / f"{corrupt['id']}.json"
    data = json.loads(path.read_text())
    data["record"]["bars"][0]["close"] = data["record"]["bars"][0]["close"] + 1.0
    path.write_text(json.dumps(data))

    detail = client.get(f"/research/bars/{corrupt['id']}")
    assert detail.status_code == 500
    assert "integrity" in detail.json()["detail"]

    listed = client.get("/research/bars").json()
    # The healthy series still serves; the corrupt one is surfaced EXPLICITLY — not silently
    # hidden, not fabricated.
    assert [row["id"] for row in listed["bar_series"]] == [healthy["id"]]
    assert len(listed["integrity_errors"]) == 1
    assert f"{corrupt['id']}.json" in listed["integrity_errors"][0]["file"]
