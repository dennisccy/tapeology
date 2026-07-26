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
import os
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
    NonFiniteBarPriceError,
    _canonical,
    _content_checksum,
    _sha256,
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


# --- the priceless-bar rail (era-desk-iter-4 audit B1) -------------------------------------------
# A candle with no finite price is not a candle. `record` REFUSES one (nothing reaches disk); the
# merged read EXCLUDES any already-recorded priceless ROW and reports it in `integrity_errors`,
# never touching the append-only file. Both halves matter: the write guard stops the bleeding, the
# read guard is what makes the 60 series poisoned before it existed harmless (58 symbols, incl. the
# era's pinned AAPL, each holding ONE priceless row beside hundreds of real bars -- quarantining
# whole FILES would silently move every band those real bars support).


@pytest.mark.parametrize("field", ["open", "high", "low", "close"])
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_record_refuses_a_bar_carrying_a_non_finite_price(tmp_path, field, bad):
    store = BarStore(tmp_path / "bars")
    prices = {"o": 148.0, "h": 149.5, "l": 147.5, "c": 149.0}
    prices[{"open": "o", "high": "h", "low": "l", "close": "c"}[field]] = bad
    poisoned = _bar(
        "PG", "1d", datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp(),
        prices["o"], prices["h"], prices["l"], prices["c"], 1_000_000,
    )
    with pytest.raises(NonFiniteBarPriceError) as exc_info:
        store.record(
            symbol="PG", timeframe="1d", window_start_utc=WINDOW_START, window_end_utc=WINDOW_END,
            feed="yahoo", bars=[poisoned],
        )
    assert "PG 1d" in str(exc_info.value)
    # Nothing reached disk: not a file, not a registry row, not an integrity error.
    assert store.list() == ([], [])
    assert not (tmp_path / "bars").exists() or list((tmp_path / "bars").glob("*.json")) == []


def test_record_refuses_the_whole_series_when_only_one_bar_is_priceless(tmp_path):
    # The real vendor shape: hundreds of good bars plus ONE not-yet-traded row. The refusal is
    # per-SERIES (nothing partially recorded) so the caller drops the bad row and re-records.
    store = BarStore(tmp_path / "bars")
    bars = _small_daily_series("PG") + [
        _bar("PG", "1d", datetime(2026, 6, 4, tzinfo=timezone.utc).timestamp(),
             float("nan"), float("nan"), float("nan"), float("nan"), 47402209)
    ]
    with pytest.raises(NonFiniteBarPriceError):
        store.record(
            symbol="PG", timeframe="1d", window_start_utc=WINDOW_START, window_end_utc=WINDOW_END,
            feed="yahoo", bars=bars,
        )
    assert store.list() == ([], [])


def _plant_priceless_row(store: BarStore, meta: dict) -> float:
    """Rewrite an ALREADY-recorded series' file with one APPENDED priceless row and BOTH checksums
    recomputed — reproducing the exact on-disk state of the 60 series written before ``record``'s
    finite guard existed (a fully VALID file, both checksums correct, holding a row whose OHLC are
    the JSON ``NaN`` token). It cannot go through ``record`` any more, which is the point.
    Returns the planted row's timestamp."""
    path = store.root / f"{meta['id']}.json"
    payload = json.loads(path.read_text())
    record = payload["record"]
    rows = record["bars"]
    priceless_ts = rows[-1]["ts"] + 86400.0
    rows.append({
        "ts": priceless_ts, "open": float("nan"), "high": float("nan"),
        "low": float("nan"), "close": float("nan"), "volume": 47402209,
    })
    record["meta"]["bar_count"] = len(rows)
    record["meta"]["checksum"] = _content_checksum(
        record["meta"]["symbol"], record["meta"]["timeframe"], record["meta"]["feed"], rows
    )
    payload["file_checksum"] = _sha256(_canonical(record))
    path.write_text(json.dumps(payload))
    return priceless_ts


def test_a_planted_priceless_series_still_passes_both_checksums(tmp_path):
    # Guard on the guard: the planted file is NOT a corrupt file (that path is already covered).
    # It verifies cleanly and is served by every per-series read verbatim — the stored truth.
    store = BarStore(tmp_path / "bars")
    meta = _record_small_series(store)
    priceless_ts = _plant_priceless_row(store, meta)
    records, errors = store.list()
    assert errors == [] and len(records) == 1
    assert [row["ts"] for row in records[0]["bars"]][-1] == priceless_ts
    assert len(store.get(meta["id"])["bars"]) == 4


def test_merged_read_excludes_a_recorded_priceless_row_and_reports_it(tmp_path):
    store = BarStore(tmp_path / "bars")
    meta = _record_small_series(store)
    clean_rows, _hb, _ha, clean_meta = store.merged_candles("PG", "1d", limit=500)
    assert len(clean_rows) == 3 and clean_meta["integrity_errors"] == []

    priceless_ts = _plant_priceless_row(store, meta)

    rows, _hb, _ha, merged_meta = store.merged_candles("PG", "1d", limit=500)
    # The priceless row contributes NOTHING, and every real bar is byte-identical to before.
    assert rows == clean_rows
    assert priceless_ts not in [row["ts"] for row in rows]
    assert merged_meta["bar_count"] == 3
    assert merged_meta["series_ids"] == [meta["id"]]
    # ...and it is REPORTED, through the same registered channel a corrupt file uses.
    assert len(merged_meta["integrity_errors"]) == 1
    reported = merged_meta["integrity_errors"][0]
    assert reported["file"] == f"{meta['id']}.json"
    assert "1 recorded row(s) carry a non-finite price" in reported["error"]
    assert "the file itself is unchanged" in reported["error"]
    # The typed analytic view (levels/tradability/desk screen read THIS) agrees exactly.
    assert [bar.epoch for bar in store.merged_bars("PG", "1d")] == [row["ts"] for row in clean_rows]


def test_excluding_a_priceless_row_never_touches_the_append_only_file(tmp_path):
    store = BarStore(tmp_path / "bars")
    meta = _record_small_series(store)
    _plant_priceless_row(store, meta)
    path = tmp_path / "bars" / f"{meta['id']}.json"
    before = path.read_bytes()

    store.merged_candles("PG", "1d", limit=500)
    store.merged_bars("PG", "1d")
    store.get(meta["id"])
    store.list()

    assert path.read_bytes() == before  # append-only: never deleted, re-tagged, or perturbed


def test_the_merged_fold_stays_memoized_for_a_pair_holding_a_priceless_row(tmp_path):
    # The priceless report rides ALONG in the memoized value rather than through the uncacheable
    # `errors` set, so an affected pair is not re-folded on every read — and, critically, the
    # cache-HIT path reports the exclusion exactly as the cache-miss path did.
    store = BarStore(tmp_path / "bars")
    meta = _record_small_series(store)
    _plant_priceless_row(store, meta)

    first_rows, first_meta = store._merged_rows("PG", "1d")
    second_rows, second_meta = store._merged_rows("PG", "1d")

    assert second_rows is first_rows  # the memo served the identical folded list
    assert second_meta["integrity_errors"] == first_meta["integrity_errors"]
    assert len(second_meta["integrity_errors"]) == 1


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


# --- era-fast_wall J-02: the stat-keyed verified-record cache -------------------------------------


def _age(path: Path, seconds: float = 5.0) -> None:
    """Backdates a file's mtime past the ~2s racy-write guard window, so a test can
    deterministically exercise the WARM-cache path without a real sleep."""
    past = time.time() - seconds
    os.utime(path, (past, past))


def _spy_on_load(monkeypatch):
    """Installs a counting spy around ``BarStore._load`` (the ONE full verifier) and returns the
    call-count list — the ``test_setups.py`` ``_counting_scan`` precedent (a monkeypatched
    counting wrapper around the real function), applied to this module's own verifier. A "read" in
    every TC below means exactly one call recorded here."""
    import app.research.bars as bars_module

    calls: list[int] = []
    real_load = bars_module.BarStore._load

    def _counting_load(self, path):
        calls.append(1)
        return real_load(self, path)

    monkeypatch.setattr(bars_module.BarStore, "_load", _counting_load)
    return calls


def test_get_serves_zero_reads_on_a_warm_cache_hit(tmp_path, monkeypatch):
    """TC-1."""
    store = BarStore(tmp_path / "bars")
    meta = _record_small_series(store)
    _age(tmp_path / "bars" / f"{meta['id']}.json")
    calls = _spy_on_load(monkeypatch)

    first = store.get(meta["id"])
    assert len(calls) == 1, "the first read must be a real verify"

    second = store.get(meta["id"])
    assert len(calls) == 1, "a warm-cache hit must add ZERO additional reads"
    assert second == first


def test_list_serves_zero_reads_across_all_files_on_a_warm_cache_hit(tmp_path, monkeypatch):
    """TC-2."""
    store = BarStore(tmp_path / "bars")
    a = _record_small_series(store, symbol="PG")
    b = _record_small_series(store, symbol="F")
    for meta in (a, b):
        _age(tmp_path / "bars" / f"{meta['id']}.json")
    calls = _spy_on_load(monkeypatch)

    first_records, first_errors = store.list()
    assert len(calls) == 2, "the first list() must verify every healthy file exactly once"
    assert first_errors == []

    second_records, second_errors = store.list()
    assert len(calls) == 2, "a warm list() must add ZERO additional reads across ALL files"
    assert second_records == first_records
    assert second_errors == []


def test_get_reverifies_and_raises_after_a_warm_read_is_tampered(tmp_path):
    """TC-3."""
    store = BarStore(tmp_path / "bars")
    meta = _record_small_series(store)
    path = tmp_path / "bars" / f"{meta['id']}.json"
    _age(path)

    warm = store.get(meta["id"])  # populate the cache
    assert warm["symbol"] == "PG"

    _tamper(path, lambda data: data["record"]["bars"][0].__setitem__("close", 999.0))
    with pytest.raises(BarSeriesIntegrityError):
        store.get(meta["id"])  # the tamper's stat change must force a fresh (failing) re-verify —
        # never the stale-good cached value, never a silently-served tampered value.


def test_racy_write_guard_refuses_to_cache_a_freshly_written_bar_series(tmp_path, monkeypatch):
    """TC-5 (bars leg)."""
    store = BarStore(tmp_path / "bars")
    calls = _spy_on_load(monkeypatch)

    meta = _record_small_series(store)  # freshly written -- inside the ~2s racy window
    store.get(meta["id"])
    assert len(calls) == 1

    store.get(meta["id"])  # still inside the window -- must be a real read again, never cached
    assert len(calls) == 2, "the racy-write guard must refuse to cache a just-written file"


def test_get_and_list_return_row_copies_a_caller_mutation_never_poisons_the_cache(tmp_path):
    """TC-6."""
    store = BarStore(tmp_path / "bars")
    meta = _record_small_series(store)
    _age(tmp_path / "bars" / f"{meta['id']}.json")

    fetched = store.get(meta["id"])
    original_close = fetched["bars"][0]["close"]
    fetched["bars"][0]["close"] = -1.0  # caller mutation, in place
    fetched["bars"].append(
        {"ts": 0.0, "open": 0.0, "high": 0.0, "low": 0.0, "close": 0.0, "volume": 0}
    )

    again = store.get(meta["id"])  # a warm-cache hit
    assert again["bars"][0]["close"] == original_close
    assert len(again["bars"]) == 3

    records, _errors = store.list()
    listed = next(r for r in records if r["id"] == meta["id"])
    assert listed["bars"][0]["close"] == original_close
    assert len(listed["bars"]) == 3


def test_bar_store_root_is_a_public_read_only_property(tmp_path):
    """TC-11."""
    root = tmp_path / "bars"
    store = BarStore(root)
    assert store.root == root
    with pytest.raises(AttributeError):
        store.root = tmp_path / "elsewhere"


def test_reset_helper_clears_the_cache_and_prevents_cross_root_leakage(tmp_path_factory, monkeypatch):
    """TC-12 — the autouse conftest fixture's own reset action, exercised directly: after a
    reset, BOTH module-level caches are empty, and a genuinely fresh root's first read is a real
    cache miss — no state survives from an earlier root's warm cache."""
    import app.research.bars as bars_module
    import app.research.datasets as datasets_module

    calls = _spy_on_load(monkeypatch)

    root_a = tmp_path_factory.mktemp("bars_a")
    store_a = BarStore(root_a)
    meta_a = _record_small_series(store_a, symbol="PG")
    _age(root_a / f"{meta_a['id']}.json")
    store_a.get(meta_a["id"])
    assert len(calls) == 1
    assert bars_module._VERIFIED_CACHE, "sanity: the cache must have genuinely warmed"

    bars_module._reset_verified_cache_for_tests()
    datasets_module._reset_verified_cache_for_tests()
    assert bars_module._VERIFIED_CACHE == {}
    assert datasets_module._VERIFIED_META_CACHE == {}

    root_b = tmp_path_factory.mktemp("bars_b")
    store_b = BarStore(root_b)
    meta_b = _record_small_series(store_b, symbol="F")
    _age(root_b / f"{meta_b['id']}.json")
    store_b.get(meta_b["id"])
    assert len(calls) == 2, "a genuinely fresh root's first read must be a real cache miss"


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


def test_every_mapped_timeframe_actually_constructs_against_the_installed_sdk():
    """Covering every configured timeframe is not enough — each entry must also BUILD a real
    ``TimeFrame`` with the SDK that is installed. It did not: ``fetch_bars`` resolved the unit by
    enum VALUE (``TimeFrameUnit("Minute")``) while alpaca-py 0.43.4 gives the member ``Minute`` the
    value ``"Min"``, so every Alpaca bar fetch raised ``ValueError: 'Minute' is not a valid
    TimeFrameUnit`` — a whole vendor path dead with no test noticing. This constructs each mapping
    exactly the way ``fetch_bars`` does, so an SDK rename cannot silently kill it again."""
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

    from app.providers.adapters.alpaca import _TIMEFRAME_PARTS

    for timeframe, (amount, unit_name) in _TIMEFRAME_PARTS.items():
        assert unit_name in TimeFrameUnit.__members__, (
            f"'{unit_name}' ({timeframe}) is not a TimeFrameUnit member in the installed SDK"
        )
        built = TimeFrame(amount, TimeFrameUnit[unit_name])
        assert built.amount_value == amount
