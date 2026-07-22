"""The ``/research/bars*`` endpoints (era-4 capability 1, J-01) — record/register, list, detail.

Exactly THREE routes exist (Product Shape, the ``test_datasets_api.py`` precedent): ``POST
/research/bars`` (the explicit credentialed record/register action — recording is never
ambient), ``GET /research/bars`` (list, plus the era-5 J-03 ``?symbol=&timeframe=`` filter), and
``GET /research/bars/{id}`` (detail). There is NO PATCH/PUT/DELETE — immutability is structural.
Validation is explicit and never silent coercion: an out-of-set timeframe / missing symbol / bad
window are 422; an unknown id is 404; re-recording DIFFERENT-window-but-identical CONTENT is 409
(the frozen ``store.record`` duplicate-content refusal); a corrupted file is an explicit 500
integrity error surfaced in ``integrity_errors`` on list rather than hidden.

Missing credentials on ``POST`` is the EXISTING explicit unavailable (503) state (never
fabricated bars) — per the spec's explicit Definition-of-Done/Testing-Requirements text, this is
DISTINCT from the 422 the historical-DATASET path uses for the analogous credentials gap.

Era-5 J-03 adds a STORE-FIRST coordinator ahead of the fetch: an identical repeat ``POST`` (same
symbol/timeframe/window) is now served from storage with ZERO adapter calls instead of re-hitting
the vendor (see ``test_duplicate_window_post_is_served_store_first_no_second_fetch`` below — this
REPLACES the old route-level "exact repeat is a 409" expectation, which was exactly the
Yahoo-re-hit behavior J-03 exists to end; the frozen store-level content-duplicate refusal is
unaffected and still covered directly in ``tests/test_bars.py``).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest
import yfinance
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager
from app.providers.adapters.base import RawBar, VendorTimeout
from app.providers.adapters.yahoo import YahooAdapter
from app.research.bar_index import BarIndex
from app.research.routes import ResearchRegistry, get_bar_fetch_adapter, get_bar_index, set_registry
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


# --- era-5 J-03: store-first idempotence -- an identical repeat POST is served from storage -------


def test_duplicate_window_post_is_served_store_first_no_second_fetch(ctx):
    """Era-5 J-03 REPLACES the old "an exact repeat POST is a 409" expectation: a second POST of
    the SAME ``(symbol, timeframe, window)`` is now served from storage — the store-first
    coordinator intercepts BEFORE the adapter is ever touched, so the second call makes ZERO
    ``fetch_bars`` calls and returns the identical stored series. (Content-duplicate refusal for a
    DIFFERENT window that happens to fetch identical content is still the frozen ``store.record``
    409 — unaffected, and directly covered at the store level in
    ``tests/test_bars.py::test_rerecording_identical_content_is_refused``.)"""
    client, bar_dir = ctx
    adapter = _inject_adapter(bars=_bars())
    first = client.post("/research/bars", json=_body())
    assert first.status_code == 200
    original = first.json()["bar_series"]

    duplicate = client.post("/research/bars", json=_body())
    assert duplicate.status_code == 200
    served = duplicate.json()["bar_series"]
    assert served["id"] == original["id"]
    assert served["checksum"] == original["checksum"]
    assert served == original

    # The adapter was touched exactly once -- the store-first hit made zero fetch_bars calls.
    assert len(adapter.fetch_bars_calls) == 1

    # Still exactly one file on disk -- no second write either.
    assert len(list(bar_dir.glob("*.json"))) == 1


def test_store_first_hit_pointing_at_a_corrupted_series_self_heals_via_a_refetch(ctx):
    """Edge case (flagged in the plan for deliberate handling, not explicitly specced): an index
    entry whose underlying JSON file was corrupted since indexing must NEVER be served fabricated
    or partial -- the coordinator treats this as a miss and falls through to a REAL refetch, which
    additively overwrites the stale index entry. Nothing is silently hidden: the orphaned corrupt
    file still surfaces in ``integrity_errors`` on list, exactly as it would have without J-03."""
    client, bar_dir = ctx
    adapter = _inject_adapter(bars=_bars())
    first = client.post("/research/bars", json=_body())
    assert first.status_code == 200
    original = first.json()["bar_series"]

    path = bar_dir / f"{original['id']}.json"
    data = json.loads(path.read_text())
    data["record"]["bars"][0]["close"] = data["record"]["bars"][0]["close"] + 1.0
    path.write_text(json.dumps(data))

    second = client.post("/research/bars", json=_body())
    assert second.status_code == 200
    healed = second.json()["bar_series"]
    assert healed["id"] != original["id"]  # a NEW series was written -- nothing fabricated/partial
    assert healed["bar_count"] == 3
    assert len(adapter.fetch_bars_calls) == 2  # the corrupted hit fell through to a REAL 2nd fetch

    listed = client.get("/research/bars").json()
    assert len(listed["integrity_errors"]) == 1  # the orphaned corrupt file is still surfaced


# --- era-5 J-03: the additive ?symbol=&timeframe= filter, and no-param byte-identity ---------------


def test_symbol_and_timeframe_filter_returns_only_the_matching_series(ctx):
    client, _bar_dir = ctx
    _inject_adapter(bars=_bars())
    pg = client.post("/research/bars", json=_body()).json()["bar_series"]
    _inject_adapter(bars=_bars(symbol="F", timeframe="1h"))
    f_hourly = client.post(
        "/research/bars", json=_body(symbol="F", timeframe="1h")
    ).json()["bar_series"]

    both = client.get("/research/bars", params={"symbol": "PG", "timeframe": "1d"})
    assert both.status_code == 200
    assert [row["id"] for row in both.json()["bar_series"]] == [pg["id"]]
    assert both.json()["integrity_errors"] == []

    symbol_only = client.get("/research/bars", params={"symbol": "f"})  # lowercase -- normalized
    assert [row["id"] for row in symbol_only.json()["bar_series"]] == [f_hourly["id"]]

    timeframe_only = client.get("/research/bars", params={"timeframe": "1h"})
    assert [row["id"] for row in timeframe_only.json()["bar_series"]] == [f_hourly["id"]]

    no_match = client.get("/research/bars", params={"symbol": "ZZZZ"})
    assert no_match.status_code == 200
    assert no_match.json()["bar_series"] == []


def test_no_param_get_is_byte_identical_to_a_direct_store_list_call(ctx):
    """Era-5 J-03: the NO-PARAM ``GET /research/bars`` path is UNCHANGED — it still calls
    ``store.list()`` verbatim and never consults the index. Proven by diffing the route's response
    against a DIRECT ``store.list()`` call against the SAME underlying directory."""
    client, bar_dir = ctx
    _inject_adapter(bars=_bars())
    client.post("/research/bars", json=_body())
    _inject_adapter(bars=_bars(symbol="F", timeframe="1h"))
    client.post("/research/bars", json=_body(symbol="F", timeframe="1h"))

    from app.research.bars import BarStore as _BarStore

    direct_records, direct_errors = _BarStore(str(bar_dir)).list()

    r = client.get("/research/bars")
    assert r.status_code == 200
    body = r.json()
    assert body["bar_series"] == direct_records
    assert body["integrity_errors"] == direct_errors


def test_blank_symbol_param_is_byte_identical_to_no_param_even_with_an_unindexed_series(ctx):
    """Era-5 J-05 audit carry-forward B2: a blank ``?symbol=`` (present but empty) must normalize
    to ``None`` BEFORE the no-param short-circuit, so it takes the exact same byte-identical
    ``store.list()`` path as a true no-param call — never the index-only path (which would miss a
    series the index never learned of, e.g. an un-indexed legacy record). Proven with an actual
    UN-INDEXED record present: written directly through the store (bypassing the route's
    ``index.insert()`` entirely), so if the blank-param path fell through to
    ``index.list(None, None)`` (the pre-fix bug) this record would silently be absent from the
    blank-param response while still present in the no-param response."""
    client, bar_dir = ctx
    from app.research.bars import BarStore as _BarStore

    direct_store = _BarStore(str(bar_dir))
    direct_store.record(
        symbol="UNINDEXED",
        timeframe="1d",
        window_start_utc=START,
        window_end_utc=END,
        feed="yahoo",
        bars=list(_bars(symbol="UNINDEXED")),
    )

    no_param = client.get("/research/bars")
    assert no_param.status_code == 200
    assert any(row["symbol"] == "UNINDEXED" for row in no_param.json()["bar_series"])

    blank_symbol = client.get("/research/bars", params={"symbol": ""})
    assert blank_symbol.status_code == 200
    assert blank_symbol.json() == no_param.json()

    blank_timeframe = client.get("/research/bars", params={"timeframe": ""})
    assert blank_timeframe.json() == no_param.json()

    both_blank = client.get("/research/bars", params={"symbol": "", "timeframe": ""})
    assert both_blank.json() == no_param.json()


# --- the viewport-paging reads: metadata-only listing + bounded candle slices ---------------------
# Both exist so a chart can fill its visible area (and lazily page more in) without pulling every
# candle of every series into the browser. Both are ADDITIVE projections of the SAME verified store
# records -- never a second, unverified candle source.


def test_include_bars_false_omits_candles_and_keeps_every_other_field_identical(ctx):
    """``?include_bars=false`` serves the SAME records with ONLY the ``bars`` key omitted (absent,
    never an empty list -- an empty list would be indistinguishable from a series holding no
    candles). Holds on BOTH selection paths: the no-param ``store.list()`` branch and the indexed
    ``?symbol=`` filter branch."""
    client, _bar_dir = ctx
    _inject_adapter(bars=_bars())
    client.post("/research/bars", json=_body())
    _inject_adapter(bars=_bars(symbol="F", timeframe="1h"))
    client.post("/research/bars", json=_body(symbol="F", timeframe="1h"))

    for params in ({}, {"symbol": "PG"}, {"timeframe": "1h"}):
        full = client.get("/research/bars", params=params).json()
        lean = client.get("/research/bars", params={**params, "include_bars": "false"}).json()
        assert lean["integrity_errors"] == full["integrity_errors"]
        assert len(lean["bar_series"]) == len(full["bar_series"])
        for lean_row, full_row in zip(lean["bar_series"], full["bar_series"], strict=True):
            assert "bars" not in lean_row
            assert lean_row == {k: v for k, v in full_row.items() if k != "bars"}
            assert full_row["bars"]  # the full projection still carries the candles


def test_explicit_include_bars_true_is_byte_identical_to_omitting_the_param(ctx):
    client, _bar_dir = ctx
    _inject_adapter(bars=_bars())
    client.post("/research/bars", json=_body())
    assert (
        client.get("/research/bars", params={"include_bars": "true"}).json()
        == client.get("/research/bars").json()
    )


def _record_ten_bars(client) -> tuple[str, list[dict]]:
    """One 10-candle series (ts = base, base+day, ...), returning its id + the stored rows."""
    bars = tuple(
        RawBar(SYMBOL, TIMEFRAME, _BASE_EPOCH + i * _DAY, 100.0 + i, 101.0 + i, 99.0 + i, 100.5 + i, 1_000 + i)
        for i in range(10)
    )
    _inject_adapter(bars=bars)
    meta = client.post("/research/bars", json=_body()).json()["bar_series"]
    return meta["id"], meta["bars"]


def test_candles_with_no_cursor_serves_the_newest_limit_rows_verbatim(ctx):
    client, _bar_dir = ctx
    series_id, rows = _record_ten_bars(client)

    r = client.get(f"/research/bars/{series_id}/candles", params={"limit": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["bar_series_id"] == series_id
    assert body["symbol"] == SYMBOL
    assert body["timeframe"] == TIMEFRAME
    assert body["bar_count"] == 10
    assert body["bars"] == rows[-3:]  # verbatim stored rows, in stored order
    assert body["has_more_before"] is True
    assert body["has_more_after"] is False


def test_candles_before_ts_is_inclusive_and_serves_the_last_matching_rows(ctx):
    client, _bar_dir = ctx
    series_id, rows = _record_ten_bars(client)

    body = client.get(
        f"/research/bars/{series_id}/candles",
        params={"limit": 3, "before_ts": rows[5]["ts"]},
    ).json()
    assert body["bars"] == rows[3:6]  # rows 3,4,5 -- the cursor row INCLUDED
    assert body["has_more_before"] is True
    assert body["has_more_after"] is True


def test_candles_after_ts_is_inclusive_and_serves_the_first_matching_rows(ctx):
    client, _bar_dir = ctx
    series_id, rows = _record_ten_bars(client)

    body = client.get(
        f"/research/bars/{series_id}/candles",
        params={"limit": 3, "after_ts": rows[5]["ts"]},
    ).json()
    assert body["bars"] == rows[5:8]  # rows 5,6,7 -- the cursor row INCLUDED
    assert body["has_more_before"] is True
    assert body["has_more_after"] is True


def test_candles_flags_report_the_true_series_edges(ctx):
    client, _bar_dir = ctx
    series_id, rows = _record_ten_bars(client)

    oldest = client.get(
        f"/research/bars/{series_id}/candles", params={"limit": 2, "after_ts": rows[0]["ts"]}
    ).json()
    assert oldest["bars"] == rows[:2]
    assert oldest["has_more_before"] is False
    assert oldest["has_more_after"] is True

    whole = client.get(f"/research/bars/{series_id}/candles", params={"limit": 500}).json()
    assert whole["bars"] == rows
    assert whole["has_more_before"] is False
    assert whole["has_more_after"] is False

    beyond = client.get(
        f"/research/bars/{series_id}/candles",
        params={"limit": 5, "before_ts": rows[0]["ts"] - 1},
    ).json()
    assert beyond["bars"] == []  # honestly empty -- never the nearest rows instead
    assert beyond["has_more_before"] is False
    assert beyond["has_more_after"] is False


def test_candles_validation_is_explicit_never_a_silent_clamp(ctx):
    client, _bar_dir = ctx
    series_id, rows = _record_ten_bars(client)

    assert client.get(f"/research/bars/{series_id}/candles", params={"limit": 0}).status_code == 422
    assert (
        client.get(f"/research/bars/{series_id}/candles", params={"limit": 5001}).status_code == 422
    )
    both = client.get(
        f"/research/bars/{series_id}/candles",
        params={"limit": 5, "before_ts": rows[0]["ts"], "after_ts": rows[1]["ts"]},
    )
    assert both.status_code == 422
    assert "before_ts" in both.json()["detail"]
    assert client.get("/research/bars/no-such-id/candles", params={"limit": 5}).status_code == 404


def test_candles_on_a_corrupted_series_is_an_explicit_500_never_partial_rows(ctx):
    client, bar_dir = ctx
    series_id, _rows = _record_ten_bars(client)
    path = bar_dir / f"{series_id}.json"
    payload = json.loads(path.read_text())
    payload["record"]["bars"][0]["close"] = 999.0  # tamper -- both checksums now disagree
    path.write_text(json.dumps(payload))

    r = client.get(f"/research/bars/{series_id}/candles", params={"limit": 5})
    assert r.status_code == 500
    assert "integrity check failed" in r.json()["detail"]


# --- the MERGED candle read (GET /research/candles) ----------------------------------------------
# A symbol accumulates many overlapping immutable recordings; a chart paging ONE of them runs out of
# history while a longer recording of the same symbol/timeframe sits on disk. The merged read folds
# every recording for a (symbol, timeframe) into one ascending series -- deduped by timestamp, the
# most recently created recording winning where two hold the same timestamp with different values.


def _iso_day(index: int) -> str:
    return (
        datetime.fromtimestamp(_BASE_EPOCH + index * _DAY, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _record_window(client, *, symbol=SYMBOL, timeframe=TIMEFRAME, first_index: int, count: int, close_offset: float = 0.0):
    """Record ONE series covering bars [first_index, first_index+count) of a shared daily grid.
    Each call posts its OWN distinct UTC window (otherwise the store-first coordinator would serve
    the earlier recording back instead of recording a second one). ``close_offset`` shifts the
    closes so a later recording of the same timestamps is a genuinely REVISED row rather than
    duplicate content (which ``record`` refuses outright)."""
    bars = tuple(
        RawBar(
            symbol,
            timeframe,
            _BASE_EPOCH + i * _DAY,
            100.0 + i,
            101.0 + i,
            99.0 + i,
            100.5 + i + close_offset,
            1_000 + i,
        )
        for i in range(first_index, first_index + count)
    )
    _inject_adapter(bars=bars)
    body = _body(
        symbol=symbol,
        timeframe=timeframe,
        start=_iso_day(first_index),
        end=_iso_day(first_index + count),
    )
    response = client.post("/research/bars", json=body)
    assert response.status_code == 200, response.json()
    return response.json()["bar_series"]


def test_merged_read_folds_every_recording_for_the_symbol_and_timeframe(ctx):
    client, _bar_dir = ctx
    _record_window(client, first_index=0, count=5)  # days 0-4
    _record_window(client, first_index=8, count=4)  # days 8-11, disjoint
    # A DIFFERENT symbol and a different timeframe must never leak into the fold.
    _record_window(client, symbol="F", first_index=0, count=3)
    _record_window(client, timeframe="1h", first_index=0, count=3)

    body = client.get(
        "/research/candles", params={"symbol": "pg", "timeframe": " 1d ", "limit": 500}
    ).json()
    assert body["symbol"] == SYMBOL and body["timeframe"] == TIMEFRAME  # normalized like the store
    assert body["series_count"] == 2
    assert body["bar_count"] == 9
    assert [row["ts"] for row in body["bars"]] == [
        _BASE_EPOCH + i * _DAY for i in [0, 1, 2, 3, 4, 8, 9, 10, 11]
    ]
    assert body["revised_timestamps"] == 0
    assert body["integrity_errors"] == []
    assert body["has_more_before"] is False and body["has_more_after"] is False


def test_merged_read_beats_what_any_single_series_can_serve(ctx):
    """The whole point: the per-series read is bounded by ONE recording's window; the merged read
    spans them all."""
    client, _bar_dir = ctx
    _record_window(client, first_index=0, count=5)
    newest = _record_window(client, first_index=8, count=4)

    single = client.get(
        f"/research/bars/{newest['id']}/candles", params={"limit": 500}
    ).json()
    merged = client.get(
        "/research/candles", params={"symbol": SYMBOL, "timeframe": TIMEFRAME, "limit": 500}
    ).json()
    assert single["bar_count"] == 4
    assert merged["bar_count"] == 9 > single["bar_count"]


def test_a_timestamp_recorded_twice_resolves_to_the_most_recent_recording_and_is_counted(ctx):
    client, _bar_dir = ctx
    older = _record_window(client, first_index=0, count=5)
    newer = _record_window(client, first_index=3, count=5, close_offset=0.25)  # days 3-7, revised
    assert older["created_utc"] <= newer["created_utc"]

    body = client.get(
        "/research/candles", params={"symbol": SYMBOL, "timeframe": TIMEFRAME, "limit": 500}
    ).json()
    assert body["bar_count"] == 8  # days 0-7, each exactly once
    assert body["revised_timestamps"] == 2  # days 3 and 4 were recorded twice, with different values
    by_ts = {row["ts"]: row for row in body["bars"]}
    for day in (3, 4):
        assert by_ts[_BASE_EPOCH + day * _DAY]["close"] == 100.5 + day + 0.25  # the NEWER recording
    assert by_ts[_BASE_EPOCH + 0 * _DAY]["close"] == 100.5  # untouched where only one recording exists


def test_merged_cursors_and_flags_match_the_per_series_contract(ctx):
    client, _bar_dir = ctx
    _record_window(client, first_index=0, count=5)
    _record_window(client, first_index=5, count=5)
    ts = [_BASE_EPOCH + i * _DAY for i in range(10)]
    params = {"symbol": SYMBOL, "timeframe": TIMEFRAME}

    newest = client.get("/research/candles", params={**params, "limit": 3}).json()
    assert [r["ts"] for r in newest["bars"]] == ts[7:]
    assert newest["has_more_before"] is True and newest["has_more_after"] is False

    before = client.get(
        "/research/candles", params={**params, "limit": 3, "before_ts": ts[5]}
    ).json()
    assert [r["ts"] for r in before["bars"]] == ts[3:6]  # cursor row INCLUDED
    assert before["has_more_before"] is True and before["has_more_after"] is True

    after = client.get("/research/candles", params={**params, "limit": 3, "after_ts": ts[0]}).json()
    assert [r["ts"] for r in after["bars"]] == ts[:3]
    assert after["has_more_before"] is False and after["has_more_after"] is True


def test_merged_read_for_an_unrecorded_symbol_is_an_honest_empty_payload(ctx):
    client, _bar_dir = ctx
    _record_window(client, first_index=0, count=3)
    body = client.get(
        "/research/candles", params={"symbol": "ZZZZ", "timeframe": TIMEFRAME, "limit": 10}
    ).json()
    assert body["bars"] == [] and body["bar_count"] == 0 and body["series_count"] == 0
    assert body["has_more_before"] is False and body["has_more_after"] is False


def test_merged_read_surfaces_a_corrupted_file_instead_of_merging_it(ctx):
    client, bar_dir = ctx
    healthy = _record_window(client, first_index=0, count=5)
    corrupt = _record_window(client, first_index=5, count=5)
    path = bar_dir / f"{corrupt['id']}.json"
    payload = json.loads(path.read_text())
    payload["record"]["bars"][0]["close"] = 999.0
    path.write_text(json.dumps(payload))

    body = client.get(
        "/research/candles", params={"symbol": SYMBOL, "timeframe": TIMEFRAME, "limit": 500}
    ).json()
    assert body["series_ids"] == [healthy["id"]]  # the corrupt recording contributes NOTHING
    assert body["bar_count"] == 5
    assert len(body["integrity_errors"]) == 1
    assert f"{corrupt['id']}.json" == body["integrity_errors"][0]["file"]


def test_merged_read_reflects_a_newly_recorded_series_immediately(ctx):
    """The fold is memoized; the memo key names every contributing series AND its checksum, so a
    fresh recording can never be served a stale merge."""
    client, _bar_dir = ctx
    _record_window(client, first_index=0, count=3)
    params = {"symbol": SYMBOL, "timeframe": TIMEFRAME, "limit": 500}
    assert client.get("/research/candles", params=params).json()["bar_count"] == 3
    _record_window(client, first_index=3, count=4)
    assert client.get("/research/candles", params=params).json()["bar_count"] == 7


def test_merged_read_validation_is_explicit(ctx):
    client, _bar_dir = ctx
    _record_window(client, first_index=0, count=3)
    params = {"symbol": SYMBOL, "timeframe": TIMEFRAME}
    assert client.get("/research/candles", params={**params, "limit": 0}).status_code == 422
    assert client.get("/research/candles", params={**params, "limit": 5001}).status_code == 422
    both = client.get(
        "/research/candles", params={**params, "limit": 5, "before_ts": 1.0, "after_ts": 2.0}
    )
    assert both.status_code == 422
    assert client.get("/research/candles", params={"symbol": " ", "timeframe": TIMEFRAME}).status_code == 422
    assert client.get("/research/candles", params={"symbol": SYMBOL}).status_code == 422  # timeframe required


def test_get_bar_index_resolves_to_a_sibling_of_the_bar_dir_by_default(ctx, monkeypatch):
    """A direct, hermetic proof of the ``get_bar_index`` resolver itself (the
    ``test_bar_fetch_adapter_resolver_defaults_to_yahoo_with_no_override`` pattern): with NO
    ``TAPEOLOGY_BAR_INDEX_DB`` override, the index DB lands as a SIBLING file next to the
    config-owned bar directory; the env override wins when set."""
    _client, bar_dir = ctx
    index = get_bar_index()
    assert isinstance(index, BarIndex)
    assert index.db_path == str(bar_dir.parent / "bar_index.db")

    monkeypatch.setenv("TAPEOLOGY_BAR_INDEX_DB", str(bar_dir.parent / "custom_index.db"))
    overridden = get_bar_index()
    assert overridden.db_path == str(bar_dir.parent / "custom_index.db")


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


def test_end_before_start_is_422(ctx):
    client, _bar_dir = ctx
    r = client.post("/research/bars", json=_body(start=END, end=START))
    assert r.status_code == 422


# --- era-5C: the UTC ``end`` is INCLUSIVE by calendar date -----------------------------------------
# The adapter/yfinance ``end`` stays half-open ``[start, end)``; the ROUTE compensates once by
# extending the vendor window through the end of ``end``'s UTC day. The store/index still key on the
# VERBATIM request strings, so the store-first key is unchanged. FakeAdapter records every
# ``fetch_bars`` call as ``(symbol, start, end, timeframe)`` — we assert the datetimes it received.


def test_start_equal_to_end_is_a_valid_single_day_window(ctx):
    """``start == end`` is no longer a 422 (era-5C inclusive end): it is a one-full-UTC-day window.
    The stored window echoes the request verbatim; the adapter receives a vendor window that runs
    from that day's start through the NEXT day (``[Jun 1, Jun 2)``)."""
    client, _bar_dir = ctx
    adapter = _inject_adapter(bars=_bars())
    r = client.post("/research/bars", json=_body(start=START, end=START))
    assert r.status_code == 200
    meta = r.json()["bar_series"]
    assert meta["window_start_utc"] == START
    assert meta["window_end_utc"] == START  # echoed verbatim, never the extended vendor bound
    _sym, sent_start, sent_end, _tf = adapter.fetch_bars_calls[0]
    assert sent_start == datetime(2026, 6, 1, tzinfo=timezone.utc)
    assert sent_end == datetime(2026, 6, 2, tzinfo=timezone.utc)  # +1 day, inclusive of Jun 1


def test_vendor_window_extends_one_day_past_the_inclusive_end(ctx):
    """The vendor window handed to the adapter ends one UTC day past the requested ``end`` so every
    bar ON ``end``'s date is included; the stored window is still the verbatim request; and the
    store-first key is unaffected by the extension (an identical repeat is served without a 2nd
    fetch)."""
    client, _bar_dir = ctx
    adapter = _inject_adapter(bars=_bars())
    r = client.post("/research/bars", json=_body())  # END = 2026-06-04T00:00:00Z
    assert r.status_code == 200
    meta = r.json()["bar_series"]
    assert meta["window_end_utc"] == END  # verbatim, not the extended vendor bound
    _sym, sent_start, sent_end, _tf = adapter.fetch_bars_calls[0]
    assert sent_start == datetime(2026, 6, 1, tzinfo=timezone.utc)
    assert sent_end == datetime(2026, 6, 5, tzinfo=timezone.utc)  # Jun 4 inclusive -> vendor end Jun 5

    # The +1-day vendor extension does NOT change the store-first key (verbatim request strings):
    # an identical repeat POST is still served store-first, with no second fetch.
    again = client.post("/research/bars", json=_body())
    assert again.status_code == 200
    assert len(adapter.fetch_bars_calls) == 1


def test_end_with_a_time_component_includes_that_whole_utc_day(ctx):
    """A time-of-day on ``end`` does not truncate the day: the vendor window floors ``end`` to its
    UTC date and adds one day, so an ``end`` of ``2026-06-04T14:30:00Z`` still fetches through the
    end of Jun 4 (vendor end Jun 5), never stopping at 14:30."""
    client, _bar_dir = ctx
    adapter = _inject_adapter(bars=_bars())
    r = client.post("/research/bars", json=_body(end="2026-06-04T14:30:00Z"))
    assert r.status_code == 200
    _sym, _sent_start, sent_end, _tf = adapter.fetch_bars_calls[0]
    assert sent_end == datetime(2026, 6, 5, tzinfo=timezone.utc)


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


# --- era-5 J-01/J-02: Yahoo is the default bar-fetch vendor; feed is sourced from the adapter,
# and (J-02) the honest error taxonomy is observably distinct ---------------------------------------
# Every test above injects a FakeAdapter via `_inject_adapter` (overriding `get_market_adapter`),
# so all 12 keep passing UNMODIFIED — proving Alpaca/fake stays selectable, opt-in, and
# byte-identical (the vendor-selector contract). The tests below deliberately do NOT override
# `get_market_adapter`, so the bar-fetch resolver falls through to its real, keyless default:
# `YahooAdapter`. The underlying yfinance call is mocked (no network); the committed REAL Yahoo
# capture (tests/fixtures/yahoo/) drives the mocked response so the adapter's real parsing runs
# end to end through the actual route.

YAHOO_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "yahoo" / "AAPL_1d_20260601_20260604.json"


def _load_yahoo_fixture() -> dict:
    return json.loads(YAHOO_FIXTURE_PATH.read_text())


def _yahoo_fixture_dataframe(fixture: dict) -> pd.DataFrame:
    index = pd.to_datetime([b["epoch"] for b in fixture["bars"]], unit="s", utc=True)
    return pd.DataFrame(
        {
            "Open": [b["open"] for b in fixture["bars"]],
            "High": [b["high"] for b in fixture["bars"]],
            "Low": [b["low"] for b in fixture["bars"]],
            "Close": [b["close"] for b in fixture["bars"]],
            "Volume": [b["volume"] for b in fixture["bars"]],
        },
        index=index,
    )


def _install_fake_yahoo_ticker(monkeypatch, df: pd.DataFrame) -> list[dict]:
    calls: list[dict] = []

    class _FakeTicker:
        def __init__(self, symbol: str) -> None:
            self.symbol = symbol

        def history(self, *, start, end, interval):
            calls.append({"symbol": self.symbol, "start": start, "end": end, "interval": interval})
            return df

    monkeypatch.setattr(yfinance, "Ticker", _FakeTicker)
    return calls


def test_yahoo_is_the_default_bar_fetch_vendor_with_no_override(ctx, monkeypatch):
    """No ``_inject_adapter`` override this time — proves the bar-fetch path resolves to the REAL,
    keyless ``YahooAdapter`` by default. ``feed`` is sourced from the adapter (never
    ``CONFIG.historical_feed``); ``GET .../{id}`` reads the stored series back byte-for-byte
    (single source of truth — nothing recomputed at read)."""
    client, bar_dir = ctx
    fixture = _load_yahoo_fixture()
    _install_fake_yahoo_ticker(monkeypatch, _yahoo_fixture_dataframe(fixture))

    r = client.post(
        "/research/bars",
        json={
            "symbol": fixture["symbol"],
            "timeframe": fixture["timeframe"],
            "start": fixture["start"],
            "end": fixture["end"],
        },
    )
    assert r.status_code == 200
    meta = r.json()["bar_series"]
    assert meta["symbol"] == fixture["symbol"]
    assert meta["timeframe"] == fixture["timeframe"]
    assert meta["feed"] == "yahoo"  # sourced from the adapter, NOT CONFIG.historical_feed ("sip")
    assert meta["feed"] != CONFIG.historical_feed
    assert meta["bar_count"] == len(fixture["bars"]) == 3
    assert len(list(bar_dir.glob("*.json"))) == 1

    detail = client.get(f"/research/bars/{meta['id']}")
    assert detail.status_code == 200
    assert detail.json()["bar_series"] == meta


def test_yahoo_default_path_receives_the_inclusive_plus_one_day_end(ctx, monkeypatch):
    """End-to-end proof the era-5C inclusive-end extension flows route -> YahooAdapter -> yfinance:
    the mocked ``yfinance.Ticker.history`` is called with ``end`` one UTC day past the fixture's
    requested ``end`` (Jun 4 -> Jun 5) while ``start`` is untouched — the adapter keeps its pure
    half-open contract; the route did the single compensation."""
    client, _bar_dir = ctx
    fixture = _load_yahoo_fixture()  # start=2026-06-01T00:00:00Z, end=2026-06-04T00:00:00Z
    calls = _install_fake_yahoo_ticker(monkeypatch, _yahoo_fixture_dataframe(fixture))

    r = client.post(
        "/research/bars",
        json={
            "symbol": fixture["symbol"],
            "timeframe": fixture["timeframe"],
            "start": fixture["start"],
            "end": fixture["end"],
        },
    )
    assert r.status_code == 200
    assert calls[0]["start"] == datetime(2026, 6, 1, tzinfo=timezone.utc)
    assert calls[0]["end"] == datetime(2026, 6, 5, tzinfo=timezone.utc)


def test_bar_fetch_adapter_resolver_defaults_to_yahoo_with_no_override(ctx):
    """A direct, hermetic proof of the resolver itself: with NO ``dependency_overrides`` on
    ``get_market_adapter``, ``get_bar_fetch_adapter()`` constructs a real ``YahooAdapter`` — never
    Alpaca (``get_study_market_adapter()``'s own Alpaca-only default stays untouched, used only by
    the study/historical-dataset paths, not this resolver)."""
    adapter = get_bar_fetch_adapter()
    assert isinstance(adapter, YahooAdapter)
    assert adapter.name == "yahoo"


def test_yahoo_out_of_retention_or_unknown_symbol_is_422_no_data_for_window(ctx, monkeypatch):
    """A genuinely unservable Yahoo request on a MAPPED timeframe (unknown symbol, or a real
    window outside that timeframe's retention — yfinance answers both with an empty frame) is
    era-5 J-02's error-taxonomy case 2: an explicit, neutral ``NoDataForWindow`` 422 — nothing
    fabricated, nothing written. (Evolved from J-01's "reuses the existing EmptyBarWindowError, no
    new exception type" test now that this case is its own explicit, distinct signal — see
    ``yahoo.py``'s module docstring for the full three-way taxonomy this iteration adds.)"""
    client, bar_dir = ctx
    _install_fake_yahoo_ticker(monkeypatch, pd.DataFrame())  # yfinance's own honest-empty answer

    r = client.post("/research/bars", json=_body(symbol="ZZZZZNOTREAL"))
    assert r.status_code == 422
    assert "no data" in r.json()["detail"]
    assert "window" in r.json()["detail"]
    assert not bar_dir.exists() or list(bar_dir.glob("*.json")) == []


# --- era-5 J-02: the honest error taxonomy is THREE observably distinct states ------------------


def test_yahoo_unsupported_timeframe_is_422_with_zero_vendor_calls(ctx, monkeypatch):
    """A config-valid ``bar_timeframes`` entry Yahoo simply does not serve this era (``8h`` — still
    passes the route's OWN out-of-set pre-check, since it IS in ``CONFIG.bar_timeframes``) is
    era-5 J-02's error-taxonomy case 1: a distinct, explicit ``UnsupportedTimeframe`` 422,
    statically knowable with ZERO vendor calls — never the generic "no data for that window" text,
    and never a fabricated/padded bar."""
    client, bar_dir = ctx
    assert "8h" in CONFIG.bar_timeframes
    calls = _install_fake_yahoo_ticker(monkeypatch, pd.DataFrame())

    r = client.post("/research/bars", json=_body(timeframe="8h"))

    assert r.status_code == 422
    assert "8h" in r.json()["detail"]
    assert calls == []  # zero vendor round-trips for a statically-unsupported timeframe
    assert not bar_dir.exists() or list(bar_dir.glob("*.json")) == []


def test_unsupported_timeframe_and_no_data_for_window_are_observably_distinct(ctx, monkeypatch):
    """The two era-5 J-02 error states never collapse into the same generic response — proven by
    directly diffing their detail text (both currently 422; the plan's own explicit requirement is
    "different detail text and/or status", so a distinct message is sufficient)."""
    client, _bar_dir = ctx
    _install_fake_yahoo_ticker(monkeypatch, pd.DataFrame())

    unsupported = client.post("/research/bars", json=_body(timeframe="8h"))
    no_data = client.post("/research/bars", json=_body(symbol="ZZZZZNOTREAL"))

    assert unsupported.status_code == no_data.status_code == 422
    assert unsupported.json()["detail"] != no_data.json()["detail"]


def test_multiple_yahoo_unsupported_timeframes_all_raise_the_same_taxonomy(ctx, monkeypatch):
    """``1mo`` and ``15m`` (both config-valid, both Yahoo-unsupported this era per the goal's
    six-timeframe enumeration) hit the SAME case-1 taxonomy as ``8h`` above."""
    client, _bar_dir = ctx
    _install_fake_yahoo_ticker(monkeypatch, pd.DataFrame())
    for timeframe in ("1mo", "15m"):
        assert timeframe in CONFIG.bar_timeframes
        r = client.post("/research/bars", json=_body(timeframe=timeframe))
        assert r.status_code == 422
        assert timeframe in r.json()["detail"]


# --- Yahoo's per-interval history caps: clamp + chunk instead of returning nothing ----------------
# Yahoo keeps 1m for the last ~30 days and refuses more than 8 days per request; 5m is capped at 60
# days, 1h at 730 (all measured against the live vendor — see `yahoo.py::_INTERVAL_LIMITS`). It
# enforces them by answering with an EMPTY frame, so ONE over-long request used to turn a
# partially-servable window into no recording at all: asking for 1m over six months recorded
# nothing, rather than the 30 days Yahoo does serve.


def _days_ago(days: float) -> str:
    return (
        datetime.now(tz=timezone.utc) - timedelta(days=days)
    ).date().isoformat()


def _intraday_frame(count: int, base_epoch: float, step_seconds: float = 60.0) -> pd.DataFrame:
    index = pd.to_datetime([base_epoch + i * step_seconds for i in range(count)], unit="s", utc=True)
    return pd.DataFrame(
        {
            "Open": [100.0 + i for i in range(count)],
            "High": [101.0 + i for i in range(count)],
            "Low": [99.0 + i for i in range(count)],
            "Close": [100.5 + i for i in range(count)],
            "Volume": [1_000 + i for i in range(count)],
        },
        index=index,
    )


def _install_per_call_yahoo_ticker(monkeypatch, frame_for) -> list[dict]:
    """Like ``_install_fake_yahoo_ticker`` but the frame is chosen PER CALL (so a chunked fetch can
    return distinct — or empty — data per chunk)."""
    calls: list[dict] = []

    class _FakeTicker:
        def __init__(self, symbol: str) -> None:
            self.symbol = symbol

        def history(self, *, start, end, interval):
            calls.append({"symbol": self.symbol, "start": start, "end": end, "interval": interval})
            return frame_for(len(calls) - 1, start, end)

    monkeypatch.setattr(yfinance, "Ticker", _FakeTicker)
    return calls


def test_a_long_1m_request_is_clamped_to_retention_and_chunked(ctx, monkeypatch):
    """The reported bug: 1m over six months recorded nothing. It must now record the 30 days Yahoo
    serves, fetched in chunks no longer than the vendor's per-request cap."""
    client, _bar_dir = ctx
    calls = _install_per_call_yahoo_ticker(
        monkeypatch,
        lambda i, start, end: _intraday_frame(3, start.timestamp()),
    )

    r = client.post(
        "/research/bars",
        json={"symbol": SYMBOL, "timeframe": "1m", "start": _days_ago(200), "end": _days_ago(0)},
    )
    assert r.status_code == 200
    meta = r.json()["bar_series"]

    assert len(calls) > 1, "a 30-day 1m window must be split into several vendor requests"
    horizon = datetime.now(tz=timezone.utc) - timedelta(days=31)
    for call in calls:
        assert call["interval"] == "1m"
        assert call["start"] >= horizon, "no chunk may ask for data older than Yahoo keeps"
        assert (call["end"] - call["start"]) <= timedelta(days=7, seconds=1), (
            "no chunk may exceed the vendor's per-request cap"
        )
    # The chunks are consecutive and non-overlapping — never the same days fetched twice.
    for earlier, later in zip(calls, calls[1:], strict=False):
        assert later["start"] == earlier["end"]

    # The recording says plainly that it is short, and why.
    assert "30 days" in meta["vendor_limit"]
    assert meta["window_start_utc"] == _days_ago(200)  # the REQUEST is recorded verbatim...
    assert meta["covered_start_utc"] > meta["window_start_utc"]  # ...and the coverage is honest
    assert meta["bar_count"] == 3 * len(calls)


def test_a_window_entirely_outside_retention_is_422_naming_the_limit_with_no_vendor_call(ctx, monkeypatch):
    client, bar_dir = ctx
    calls = _install_per_call_yahoo_ticker(monkeypatch, lambda i, start, end: _intraday_frame(3, 0))

    r = client.post(
        "/research/bars",
        json={"symbol": SYMBOL, "timeframe": "1m", "start": _days_ago(400), "end": _days_ago(380)},
    )
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert "30 days" in detail and "1m" in detail
    assert calls == [], "nothing servable — the vendor must not be called at all"
    assert not bar_dir.exists() or list(bar_dir.glob("*.json")) == []


def test_one_empty_chunk_does_not_discard_the_bars_the_other_chunks_returned(ctx, monkeypatch):
    """A holiday week inside a longer window legitimately has no bars; failing the whole fetch over
    it would throw away every real bar the other chunks returned."""
    client, _bar_dir = ctx
    calls = _install_per_call_yahoo_ticker(
        monkeypatch,
        lambda i, start, end: pd.DataFrame() if i == 1 else _intraday_frame(4, start.timestamp()),
    )

    r = client.post(
        "/research/bars",
        json={"symbol": SYMBOL, "timeframe": "1m", "start": _days_ago(200), "end": _days_ago(0)},
    )
    assert r.status_code == 200
    assert r.json()["bar_series"]["bar_count"] == 4 * (len(calls) - 1)


def test_every_chunk_empty_is_still_an_honest_422(ctx, monkeypatch):
    client, bar_dir = ctx
    _install_per_call_yahoo_ticker(monkeypatch, lambda i, start, end: pd.DataFrame())

    r = client.post(
        "/research/bars",
        json={"symbol": SYMBOL, "timeframe": "1m", "start": _days_ago(20), "end": _days_ago(0)},
    )
    assert r.status_code == 422
    assert "no data" in r.json()["detail"]
    assert not bar_dir.exists() or list(bar_dir.glob("*.json")) == []


def test_5m_and_1h_are_clamped_to_their_own_limits(ctx, monkeypatch):
    client, _bar_dir = ctx
    for timeframe, retention, phrase in (("5m", 60, "60 days"), ("1h", 730, "730 days")):
        calls = _install_per_call_yahoo_ticker(
            monkeypatch, lambda i, start, end: _intraday_frame(2, start.timestamp())
        )
        r = client.post(
            "/research/bars",
            json={
                "symbol": SYMBOL,
                "timeframe": timeframe,
                "start": _days_ago(retention + 300),
                "end": _days_ago(0),
            },
        )
        assert r.status_code == 200, r.json()
        assert phrase in r.json()["bar_series"]["vendor_limit"]
        horizon = datetime.now(tz=timezone.utc) - timedelta(days=retention + 1)
        assert all(call["start"] >= horizon for call in calls)


def test_a_fully_served_window_records_no_vendor_limit_and_honest_coverage(ctx, monkeypatch):
    """The other side of the contract: an unclamped recording says so (``vendor_limit: None``), and
    its coverage is the first/last bar's own timestamps — never inferred by a reader."""
    client, _bar_dir = ctx
    fixture = _load_yahoo_fixture()
    _install_fake_yahoo_ticker(monkeypatch, _yahoo_fixture_dataframe(fixture))

    r = client.post(
        "/research/bars",
        json={
            "symbol": fixture["symbol"],
            "timeframe": fixture["timeframe"],
            "start": fixture["start"],
            "end": fixture["end"],
        },
    )
    meta = r.json()["bar_series"]
    assert meta["vendor_limit"] is None
    assert meta["covered_start_utc"][:10] == "2026-06-01"
    assert meta["covered_end_utc"][:10] == "2026-06-03"


def test_a_clamped_window_is_served_store_first_within_the_same_day(ctx, monkeypatch):
    """Re-fetching a clamped window only pays off once the vendor's rolling window has moved a day;
    within the same UTC day the stored recording IS the answer, and no vendor call is made."""
    client, _bar_dir = ctx
    calls = _install_per_call_yahoo_ticker(
        monkeypatch, lambda i, start, end: _intraday_frame(3, start.timestamp())
    )
    body = {"symbol": SYMBOL, "timeframe": "1m", "start": _days_ago(200), "end": _days_ago(0)}
    first = client.post("/research/bars", json=body).json()["bar_series"]
    assert first["vendor_limit"]
    calls_after_first = len(calls)

    repeat = client.post("/research/bars", json=body)
    assert repeat.status_code == 200
    assert repeat.json()["bar_series"]["id"] == first["id"]
    assert len(calls) == calls_after_first, "a same-day repeat must not re-hit the vendor"


def test_a_clamped_recording_from_an_earlier_day_is_eligible_for_a_refetch():
    """The rule itself, in isolation: only a recording that a cap actually shortened AND that was
    made on an earlier UTC day may be re-fetched. Unclamped recordings are immutable answers."""
    from app.research.routes import _clamped_window_may_have_grown

    today = datetime.now(tz=timezone.utc).date().isoformat()
    yesterday = (datetime.now(tz=timezone.utc) - timedelta(days=1)).date().isoformat()

    assert _clamped_window_may_have_grown(
        {"vendor_limit": "Yahoo serves 1m ...", "created_utc": f"{yesterday}T10:00:00Z"}
    )
    assert not _clamped_window_may_have_grown(
        {"vendor_limit": "Yahoo serves 1m ...", "created_utc": f"{today}T10:00:00Z"}
    )
    assert not _clamped_window_may_have_grown(
        {"vendor_limit": None, "created_utc": f"{yesterday}T10:00:00Z"}
    )
    assert not _clamped_window_may_have_grown({})  # a pre-coverage legacy record: never re-fetched


# --- the second vendor: Alpaca serves the history Yahoo caps -------------------------------------


def test_vendor_alpaca_selects_the_alpaca_adapter_and_never_calls_yahoo(ctx, monkeypatch):
    """``vendor: "alpaca"`` is the deep-history path (Alpaca serves 1m years back, where Yahoo keeps
    30 days). With no credentials it is the EXISTING explicit 503 — never a silent fall-back to
    Yahoo, which would answer a request for deep history with a shallow window."""
    client, bar_dir = ctx
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)
    calls = _install_per_call_yahoo_ticker(
        monkeypatch, lambda i, start, end: _intraday_frame(3, start.timestamp())
    )

    r = client.post(
        "/research/bars",
        json={
            "symbol": SYMBOL,
            "timeframe": "1m",
            "start": _days_ago(200),
            "end": _days_ago(190),
            "vendor": "alpaca",
        },
    )
    assert r.status_code == 503
    assert calls == []
    assert not bar_dir.exists() or list(bar_dir.glob("*.json")) == []


def test_the_same_window_from_two_vendors_is_two_distinct_store_first_entries(ctx):
    """The store-first key includes the feed: a Yahoo recording of a window must never answer a
    lookup for the same window from Alpaca (different session coverage, different tape)."""
    from app.research.bar_index import BarIndex

    index = BarIndex(":memory:")
    common = {
        "symbol": SYMBOL,
        "timeframe": "1m",
        "window_start_utc": START,
        "window_end_utc": END,
        "bar_count": 3,
    }
    index.insert({**common, "feed": "yahoo", "id": "yahoo-series", "checksum": "a" * 64})
    index.insert({**common, "feed": "sip", "id": "alpaca-series", "checksum": "b" * 64})

    assert index.lookup(SYMBOL, "1m", START, END, "yahoo").series_id == "yahoo-series"
    assert index.lookup(SYMBOL, "1m", START, END, "sip").series_id == "alpaca-series"
    assert index.lookup(SYMBOL, "1m", START, END, "iex") is None
