"""The multi-timeframe OHLC bar store (era-4 capability 1, J-01) — store-level discipline.

Mirrors ``tests/test_datasets.py`` end to end (the spec's own explicit directive): metadata
correctness, structural immutability (no update/re-record path exists), verified loads (double
checksum), the honest failure taxonomy, the committed keyless multi-timeframe fixture, and the
``bar_dir`` / validation-parameter ``config_fingerprint`` exclusions (the ``dataset_dir``
precedent). Also covers the two new Alpaca-adapter helpers this iteration adds (the free-plan
recency-delay clamp and the rate-limit throttle) as small, independently testable pure functions.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.config import CONFIG, Config
from app.providers.adapters.base import RawBar
from app.research.bars import (
    BarSeriesAlreadyRegistered,
    BarSeriesIntegrityError,
    BarSeriesNotFound,
    BarStore,
    EmptyBarWindowError,
)

FIXTURE_BAR_DIR = Path(__file__).parent / "fixtures" / "bars"

WINDOW_START, WINDOW_END = "2026-06-01T00:00:00Z", "2026-06-04T00:00:00Z"


def _bar(symbol: str, timeframe: str, epoch: float, o: float, h: float, l: float, c: float, v: int) -> RawBar:
    return RawBar(symbol, timeframe, epoch, o, h, l, c, v)


def _small_daily_series(symbol: str = "PG") -> list[RawBar]:
    base = datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp()
    day = 86400.0
    return [
        _bar(symbol, "1d", base + 0 * day, 148.0, 149.5, 147.5, 149.0, 1_000_000),
        _bar(symbol, "1d", base + 1 * day, 149.0, 150.0, 148.5, 149.8, 1_100_000),
        _bar(symbol, "1d", base + 2 * day, 149.8, 151.0, 149.2, 150.5, 1_050_000),
    ]


def _record_small_series(store: BarStore, symbol: str = "PG", timeframe: str = "1d") -> dict:
    return store.record(
        symbol=symbol,
        timeframe=timeframe,
        window_start_utc=WINDOW_START,
        window_end_utc=WINDOW_END,
        feed="sip",
        bars=_small_daily_series(symbol),
    )


# --- record: metadata correctness ----------------------------------------------------------------


def test_record_stores_correct_metadata(tmp_path):
    store = BarStore(tmp_path / "bars")
    meta = _record_small_series(store)

    assert meta["symbol"] == "PG"
    assert meta["timeframe"] == "1d"
    assert meta["window_start_utc"] == WINDOW_START
    assert meta["window_end_utc"] == WINDOW_END
    assert meta["feed"] == "sip"
    assert meta["bar_count"] == 3
    assert isinstance(meta["checksum"], str) and len(meta["checksum"]) == 64
    int(meta["checksum"], 16)  # hex or this raises
    assert meta["id"] and meta["created_utc"].endswith("Z")


def test_get_and_list_serve_candles_embedded_verbatim(tmp_path):
    store = BarStore(tmp_path / "bars")
    bars = _small_daily_series()
    meta = store.record(
        symbol="PG", timeframe="1d", window_start_utc=WINDOW_START, window_end_utc=WINDOW_END,
        feed="sip", bars=bars,
    )

    fetched = store.get(meta["id"])
    assert fetched["bars"] == [
        {
            "ts": b.epoch, "open": b.open, "high": b.high, "low": b.low, "close": b.close,
            "volume": b.volume,
        }
        for b in bars
    ]
    records, errors = store.list()
    assert errors == []
    assert records[0]["bars"] == fetched["bars"]
    assert records[0] == fetched


def test_split_series_register_and_survive_a_store_reload(tmp_path):
    root = tmp_path / "bars"
    daily = _record_small_series(BarStore(root), timeframe="1d")
    hourly = _record_small_series(BarStore(root), symbol="F", timeframe="1h")

    reloaded = BarStore(root)
    assert reloaded.get(daily["id"])["timeframe"] == "1d"
    assert reloaded.get(hourly["id"])["timeframe"] == "1h"
    records, errors = reloaded.list()
    assert errors == []
    assert {r["id"]: r["timeframe"] for r in records} == {
        daily["id"]: "1d",
        hourly["id"]: "1h",
    }


# --- immutability (409-style refusal; no update/re-record path exists) ---------------------------


def test_rerecording_identical_content_is_refused(tmp_path):
    store = BarStore(tmp_path / "bars")
    original = _record_small_series(store)

    with pytest.raises(BarSeriesAlreadyRegistered) as excinfo:
        _record_small_series(store)
    assert original["id"] in str(excinfo.value)
    assert "PG" in str(excinfo.value)

    records, errors = store.list()
    assert errors == []
    assert [r["id"] for r in records] == [original["id"]]


# --- verified loads: corruption is an explicit, distinct error -----------------------------------


def _tamper(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data))


def test_corrupted_bar_data_surfaces_an_explicit_integrity_error(tmp_path):
    store = BarStore(tmp_path / "bars")
    meta = _record_small_series(store)
    file_path = tmp_path / "bars" / f"{meta['id']}.json"

    def corrupt_close(data):
        data["record"]["bars"][0]["close"] = data["record"]["bars"][0]["close"] + 1.0

    _tamper(file_path, corrupt_close)
    with pytest.raises(BarSeriesIntegrityError):
        store.get(meta["id"])
    with pytest.raises(BarSeriesIntegrityError):
        store.load_bars(meta["id"])


def test_list_surfaces_a_corrupt_file_explicitly_never_hides_it(tmp_path):
    store = BarStore(tmp_path / "bars")
    healthy = _record_small_series(store, symbol="PG", timeframe="1d")
    corrupt = _record_small_series(store, symbol="F", timeframe="1h")
    _tamper(
        tmp_path / "bars" / f"{corrupt['id']}.json",
        lambda data: data["record"]["bars"][0].__setitem__("volume", 999999999),
    )
    records, errors = store.list()
    assert [r["id"] for r in records] == [healthy["id"]]
    assert len(errors) == 1 and f"{corrupt['id']}.json" in errors[0]["file"]


def test_unparseable_file_is_an_explicit_integrity_error(tmp_path):
    store = BarStore(tmp_path / "bars")
    meta = _record_small_series(store)
    (tmp_path / "bars" / f"{meta['id']}.json").write_text("{not json")
    with pytest.raises(BarSeriesIntegrityError):
        store.get(meta["id"])


def test_unknown_bar_series_id_raises_not_found(tmp_path):
    store = BarStore(tmp_path / "bars")
    with pytest.raises(BarSeriesNotFound):
        store.get("no-such-bar-series")
    with pytest.raises(BarSeriesNotFound):
        store.load_bars("no-such-bar-series")


def test_empty_bar_list_is_an_explicit_refusal(tmp_path):
    store = BarStore(tmp_path / "bars")
    with pytest.raises(EmptyBarWindowError):
        store.record(
            symbol="PG", timeframe="1d", window_start_utc=WINDOW_START, window_end_utc=WINDOW_END,
            feed="sip", bars=[],
        )
    records, errors = store.list()
    assert records == [] and errors == []


# --- the committed miniature multi-timeframe fixture (keyless CI proof) --------------------------


def test_committed_fixture_loads_through_the_real_store_path_keyless():
    store = BarStore(FIXTURE_BAR_DIR)
    records, errors = store.list()
    assert errors == [], f"committed bar fixtures failed verification: {errors}"
    assert len(records) >= 2, "the committed fixture must cover at least two bar series"
    timeframes = {r["timeframe"] for r in records}
    assert len(timeframes) >= 2, "the committed fixture must cover at least two DISTINCT timeframes"

    for meta in records:
        bars = store.load_bars(meta["id"])
        assert len(bars) == meta["bar_count"] > 0
        assert all(isinstance(b, RawBar) for b in bars)
        assert meta["feed"] == CONFIG.historical_feed
        # Byte-identical reload through the real store path.
        again = store.get(meta["id"])
        assert again == meta


# --- config: bar_dir + validation/throttle params are operational, never fingerprint inputs -------


def test_bar_dir_is_excluded_from_config_fingerprint():
    # The dataset_dir precedent: WHERE bar series are stored cannot affect any research value...
    assert Config(bar_dir="/somewhere/else").config_fingerprint() == CONFIG.config_fingerprint()
    # ...while a real classifier threshold still moves it (the counter-test).
    assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()


def test_bar_validation_and_throttle_params_are_excluded_from_config_fingerprint():
    # None of these shape any tape/backtest/study computation — they only govern an unrelated,
    # brand-new bar-storage capability's validation and vendor-fetch mechanics.
    assert Config(bar_timeframes=("1d",)).config_fingerprint() == CONFIG.config_fingerprint()
    assert Config(bar_recency_delay_seconds=1.0).config_fingerprint() == CONFIG.config_fingerprint()
    assert Config(bar_rate_limit_per_minute=1).config_fingerprint() == CONFIG.config_fingerprint()
    assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()


def test_bar_dir_env_override_wins(monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", "/operator/override")
    assert CONFIG.bar_dir_resolved() == "/operator/override"
    monkeypatch.delenv("TAPEOLOGY_BAR_DIR")
    default = CONFIG.bar_dir_resolved()
    assert default.endswith(str(Path(".data") / "bars"))


# --- Alpaca adapter: recency-delay clamp + rate-throttle (pure/injectable helpers) ----------------


def test_bar_fetch_recency_clamp_never_requests_the_embargoed_tail():
    from app.providers.adapters.alpaca import _bar_fetch_end_clamp

    now = datetime(2026, 7, 6, 12, 0, 0, tzinfo=timezone.utc)
    inside_embargo_end = now - timedelta(minutes=2)  # 2 min ago: inside the 15-min embargo
    clamped = _bar_fetch_end_clamp(inside_embargo_end, 900.0, now=now)
    assert clamped == now - timedelta(seconds=900.0)

    outside_embargo_end = now - timedelta(hours=5)  # well before the embargo: unaffected
    assert _bar_fetch_end_clamp(outside_embargo_end, 900.0, now=now) == outside_embargo_end


def test_throttle_bar_fetch_spaces_consecutive_calls(monkeypatch):
    import app.providers.adapters.alpaca as alpaca_module

    monkeypatch.setattr(alpaca_module, "CONFIG", Config(bar_rate_limit_per_minute=600))  # 0.1s interval
    alpaca_module._LAST_BAR_FETCH_MONOTONIC = None
    try:
        t0 = time.monotonic()
        alpaca_module._throttle_bar_fetch()
        t1 = time.monotonic()
        alpaca_module._throttle_bar_fetch()
        t2 = time.monotonic()
    finally:
        alpaca_module._LAST_BAR_FETCH_MONOTONIC = None  # leave clean for later tests
    assert (t1 - t0) < 0.05, "the first call has nothing prior to wait behind"
    assert (t2 - t1) >= 0.09, "the second call must wait ~the configured min interval"


def test_bar_timeframe_vendor_mapping_covers_every_configured_timeframe():
    from app.providers.adapters.alpaca import _TIMEFRAME_PARTS

    assert set(_TIMEFRAME_PARTS) == set(CONFIG.bar_timeframes)
