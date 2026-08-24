"""``micro_readiness.py`` + ``GET /research/desk/micro/readiness`` (Era "The Rapid Microscope",
J-01) -- the corpus-truth fold. Test-first contract: TC-1 through TC-7 in
``docs/phases/goal-rapid-microscope-iter-1.md``.

The real-corpus tests (TC-1 through TC-5) run against the ACTUAL committed 18-dataset legacy tick
corpus at ``apps/backend/.data/datasets`` -- the acceptance values ARE the real 18-dataset/
12-symbol-day counts, and a fixture cannot substitute for this check (the phase spec's own
TESTING REQUIREMENTS). They share ONE module-scoped ``real_readiness`` fixture (the per-shard
``fallback_frac`` classification is genuinely expensive over ~0.92 GB of real tick events) so the
cost is paid once for the whole file. Every OTHER test builds its own small, hermetic,
``tmp_path``-scoped ``DatasetStore`` (never the real corpus) -- the ``test_referee_evidence.py``
"hand-crafted records through the store's own public write path" precedent."""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.engine.aggressor import classify_aggressor
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.research import micro_readiness as micro_readiness_module
from app.research.datasets import DatasetStore, parse_utc_epoch
from app.research.micro_readiness import (
    EXPOSURE_STATE_EXPLORATORY,
    PILOT_STUDY_IDS,
    SPLIT_PROVENANCE_HAND_ASSIGNED,
    WF_TEST_MIN_SESSIONS,
    WF_TRAIN_MIN_SESSIONS,
    MicroBandTouchCache,
    MicroReadinessCache,
    build_readiness,
    resolve_micro_band_touch_cache_db_path,
    resolve_micro_readiness_cache_db_path,
)
from app.research.bars import BarStore
from app.research.desk_playbook import PlaybookStore, playbook_parameters
from app.research.desk_playbook_context import BandMapResolver
from app.research.desk_routes import get_playbook_store
from app.research.micro_join import BAND_TOUCH_STATUS_ENUMERATED, joinable_corpus_counts
from app.research.micro_routes import get_micro_band_touch_cache, get_micro_readiness_cache
from app.research.referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS
from tests.real_corpus_cache import real_corpus_dataset_store, real_corpus_readiness_cache
from app.research.routes import get_bar_store, get_dataset_store
from app.research.tradability_cache import TradabilityCache, resolve_tradability_cache_db_path
from app.research import vault

_ET = ZoneInfo("America/New_York")


# --- fixture builders (the store's own public write path -- never a hand-typed file) ---------------


def _events(symbol: str) -> list:
    """One quote followed by three trades spanning every `_quote_rule_decides` branch (a Stage-1
    BUY, a Stage-1 SELL, and one strictly-between-bid-ask fallback) -- never all-decided or
    all-fallback, so a fixture's own `fallback_frac` is a genuine, non-degenerate fraction."""
    return [
        QuoteEvent(symbol, 0.0, 99.99, 100.02, 100, 100),
        TradeEvent(symbol, 0.1, 100.03, 10, Side.BUY),  # >= ask -> Stage 1
        TradeEvent(symbol, 0.2, 100.00, 10, Side.BUY),  # strictly between -> fallback
        TradeEvent(symbol, 0.3, 99.99, 10, Side.SELL),  # <= bid -> Stage 1
    ]


def _plant_dataset(
    store: DatasetStore,
    *,
    symbol: str,
    split: str = "train",
    window_start_utc: str = "2026-06-09T13:00:00Z",
    window_end_utc: str = "2026-06-09T13:01:00Z",
) -> dict:
    return store.record(
        symbol=symbol,
        source="fixture",
        source_kind="fixture",
        source_id=f"{symbol}-fixture",
        split=split,
        window_start_utc=window_start_utc,
        window_end_utc=window_end_utc,
        data_feed="sip",
        epoch_anchor=0.0,
        events=_events(symbol),
    )


@pytest.fixture
def client(tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
    # iter-26: the route now also depends on the band-touch cache -- a tmp_path-scoped one, the
    # SAME hermeticity discipline as every other override below (never the real, ambient
    # `.data`-sibling `micro_band_touch_cache.db`).
    band_touch_cache = MicroBandTouchCache(str(tmp_path / "band_touch_cache.db"))
    # J-03: the route now also depends on a playbook store (the joinable_corpus field) -- a
    # tmp_path-scoped, empty-by-default one, so this fixture's existing hermeticity contract is
    # unaffected (never the real, ambient .data/playbook directory).
    playbook_store = PlaybookStore(tmp_path / "playbook")
    # J-09: the route now also depends on a bar store (the resolver that materializes
    # `band_touch_count` -- `BandMapResolver.__init__` unconditionally lists it) -- a
    # tmp_path-scoped, empty-by-default one, the SAME hermeticity discipline as the playbook store
    # above, never the real, ambient `.data/bars` directory.
    bar_store = BarStore(tmp_path / "bars")
    app.dependency_overrides[get_dataset_store] = lambda: dataset_store
    app.dependency_overrides[get_micro_readiness_cache] = lambda: cache
    app.dependency_overrides[get_micro_band_touch_cache] = lambda: band_touch_cache
    app.dependency_overrides[get_playbook_store] = lambda: playbook_store
    app.dependency_overrides[get_bar_store] = lambda: bar_store
    with TestClient(app) as c:
        yield c, dataset_store, cache
    app.dependency_overrides.pop(get_dataset_store, None)
    app.dependency_overrides.pop(get_micro_readiness_cache, None)
    app.dependency_overrides.pop(get_micro_band_touch_cache, None)
    app.dependency_overrides.pop(get_playbook_store, None)
    app.dependency_overrides.pop(get_bar_store, None)


# --- _quote_rule_decides: cross-validated against classify_aggressor's own OBSERVABLE behavior ------
#
# classify_aggressor itself never exposes which stage decided a trade. The oracle below is
# independent of _quote_rule_decides' own formula: with prior_trade_price AND last_tick_dir both
# None, Stage 2 is STRUCTURALLY forced to Side.UNKNOWN (aggressor.py's own documented rule -- "no
# quote AND no prior trade" is the one undecidable case) -- so
# "classify_aggressor(...) is not Side.UNKNOWN" is a reliable, independent ground truth for
# "Stage 1 decided" in this specific probe, never a second copy of the same two-line condition.


@pytest.mark.parametrize(
    "price,bid,ask,expected_stage1",
    [
        (100.03, 99.99, 100.02, True),  # price >= ask -> Stage 1 BUY
        (100.02, 99.99, 100.02, True),  # price == ask -> Stage 1 BUY (>=)
        (99.99, 99.99, 100.02, True),  # price == bid -> Stage 1 SELL (<=)
        (99.98, 99.99, 100.02, True),  # price < bid -> Stage 1 SELL
        (100.01, 99.99, 100.02, False),  # strictly between -> Stage 1 does not decide
        (100.005, 99.99, 100.02, False),  # strictly between -> Stage 1 does not decide
    ],
)
def test_quote_rule_decides_matches_classify_aggressor_with_no_prior_trade(
    price, bid, ask, expected_stage1
):
    quote = QuoteEvent("AAPL", 0.0, bid, ask, 100, 100)
    trade = TradeEvent("AAPL", 0.0, price, 10, Side.BUY)
    mirrored = micro_readiness_module._quote_rule_decides(trade, quote)
    assert mirrored is expected_stage1
    result = classify_aggressor(trade, quote, prior_trade_price=None, last_tick_dir=None)
    assert mirrored == (result is not Side.UNKNOWN)


def test_quote_rule_decides_is_false_with_no_quote_in_effect():
    trade = TradeEvent("AAPL", 0.0, 100.0, 10, Side.BUY)
    assert micro_readiness_module._quote_rule_decides(trade, None) is False
    assert classify_aggressor(trade, None, None, None) is Side.UNKNOWN


# --- _compute_fallback_frac: hand-computed over a small event list ----------------------------------


def test_compute_fallback_frac_hand_computed():
    # 3 trades: BUY@100.03 (Stage 1), BUY@100.00 (fallback), SELL@99.99 (Stage 1) -> 1/3 fallback.
    events = _events("AAPL")
    assert micro_readiness_module._compute_fallback_frac(events) == pytest.approx(1.0 / 3.0)


def test_compute_fallback_frac_no_trades_is_zero():
    events = [QuoteEvent("AAPL", 0.0, 99.99, 100.02, 100, 100)]
    assert micro_readiness_module._compute_fallback_frac(events) == 0.0


def test_compute_fallback_frac_before_any_quote_is_always_fallback():
    events = [TradeEvent("AAPL", 0.0, 100.0, 10, Side.BUY)]
    assert micro_readiness_module._compute_fallback_frac(events) == 1.0


# --- _rth_overlap: cheap RTH-coverage arithmetic, hand-computed (locks in the real corpus's own
#     shapes: a window starting before open, one starting after close, one strictly inside RTH,
#     one with zero overlap, and one that exactly covers the session end to end) -------------------


def test_rth_overlap_window_starts_before_open_ends_before_close():
    start = datetime(2026, 6, 22, 8, 30, tzinfo=_ET)
    end = datetime(2026, 6, 22, 11, 0, tzinfo=_ET)
    minutes, gaps = micro_readiness_module._rth_overlap(start, end, date(2026, 6, 22))
    assert minutes == 90.0
    assert gaps == ["11:00–16:00 ET not covered"]


def test_rth_overlap_window_starts_after_open_ends_after_close():
    start = datetime(2026, 5, 27, 14, 0, tzinfo=_ET)
    end = datetime(2026, 5, 27, 16, 30, tzinfo=_ET)
    minutes, gaps = micro_readiness_module._rth_overlap(start, end, date(2026, 5, 27))
    assert minutes == 120.0
    assert gaps == ["09:30–14:00 ET not covered"]


def test_rth_overlap_window_strictly_inside_rth_has_two_gaps():
    start = datetime(2026, 6, 26, 10, 25, tzinfo=_ET)
    end = datetime(2026, 6, 26, 12, 55, tzinfo=_ET)
    minutes, gaps = micro_readiness_module._rth_overlap(start, end, date(2026, 6, 26))
    assert minutes == 150.0
    assert gaps == ["09:30–10:25 ET not covered", "12:55–16:00 ET not covered"]


def test_rth_overlap_window_entirely_outside_rth_is_one_whole_session_gap():
    start = datetime(2026, 6, 1, 20, 0, tzinfo=_ET)
    end = datetime(2026, 6, 1, 21, 0, tzinfo=_ET)
    minutes, gaps = micro_readiness_module._rth_overlap(start, end, date(2026, 6, 1))
    assert minutes == 0.0
    assert gaps == ["09:30–16:00 ET not covered"]


def test_rth_overlap_window_exactly_covers_rth_has_no_gaps():
    start = datetime(2026, 6, 1, 9, 30, tzinfo=_ET)
    end = datetime(2026, 6, 1, 16, 0, tzinfo=_ET)
    minutes, gaps = micro_readiness_module._rth_overlap(start, end, date(2026, 6, 1))
    assert minutes == 390.0
    assert gaps == []


def test_et_datetime_converts_a_utc_iso_timestamp_with_microseconds():
    # 2026-06-09T17:00:00.002286Z is EDT (UTC-4) -> 13:00:00.002286 ET, same calendar date.
    result = micro_readiness_module._et_datetime("2026-06-09T17:00:00.002286Z")
    assert (result.hour, result.minute) == (13, 0)
    assert result.date().isoformat() == "2026-06-09"


# --- resolve_micro_readiness_cache_db_path: env-else-sibling-of-dataset-dir -------------------------


def test_resolve_defaults_to_a_sibling_of_the_dataset_dir(tmp_path, monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_MICRO_READINESS_CACHE_DB", raising=False)
    assert resolve_micro_readiness_cache_db_path(str(tmp_path / "datasets")) == str(
        tmp_path / "micro_readiness_cache.db"
    )


def test_resolve_honors_the_env_override(tmp_path, monkeypatch):
    override = str(tmp_path / "elsewhere" / "cache.db")
    monkeypatch.setenv("TAPEOLOGY_MICRO_READINESS_CACHE_DB", override)
    assert resolve_micro_readiness_cache_db_path(str(tmp_path / "datasets")) == override


# --- MicroReadinessCache: lookup/publish round trip --------------------------------------------------


def test_cache_lookup_is_none_on_a_genuine_miss(tmp_path):
    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
    assert cache.lookup("no-such-checksum") is None


def test_cache_publish_then_lookup_round_trips(tmp_path):
    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
    cache.publish("checksum-a", 0.42)
    assert cache.lookup("checksum-a") == 0.42


def test_cache_survives_a_corrupted_db_file_as_a_full_miss(tmp_path):
    db_path = tmp_path / "cache.db"
    db_path.write_text("not a sqlite file")
    cache = MicroReadinessCache(str(db_path))
    assert cache.lookup("anything") is None
    cache.publish("anything", 0.5)  # swallowed, never raises


# --- iter-26: MicroBandTouchCache -- composite-key lookup/publish round trip (TC-2/TC-4/TC-5) --------


def test_resolve_micro_band_touch_cache_db_path_defaults_to_a_sibling_file(tmp_path):
    assert resolve_micro_band_touch_cache_db_path(str(tmp_path / "datasets")) == str(
        tmp_path / "micro_band_touch_cache.db"
    )


def test_resolve_micro_band_touch_cache_db_path_honors_the_env_override(tmp_path, monkeypatch):
    override = str(tmp_path / "elsewhere" / "band_touch_cache.db")
    monkeypatch.setenv("TAPEOLOGY_MICRO_BAND_TOUCH_CACHE_DB", override)
    assert resolve_micro_band_touch_cache_db_path(str(tmp_path / "datasets")) == override


def test_band_touch_cache_lookup_is_none_on_a_genuine_miss(tmp_path):
    cache = MicroBandTouchCache(str(tmp_path / "band_touch_cache.db"))
    assert cache.lookup("no-such-checksum", "no-such-map-key") is None


def test_band_touch_cache_publish_then_lookup_round_trips(tmp_path):
    cache = MicroBandTouchCache(str(tmp_path / "band_touch_cache.db"))
    cache.publish("checksum-a", "map-key-a", 3)
    assert cache.lookup("checksum-a", "map-key-a") == 3


def test_band_touch_cache_keys_on_the_composite_never_the_checksum_alone(tmp_path):
    """TC-4's own claim, at the class level: a genuinely different ``map_key`` under the SAME
    checksum is a fresh miss -- the whole reason this cache is keyed on the composite
    ``(checksum, map_key)``, never the checksum alone (a dataset's own bytes never change, but the
    band map a resolver serves for it can)."""
    cache = MicroBandTouchCache(str(tmp_path / "band_touch_cache.db"))
    cache.publish("checksum-a", "map-key-old", 3)
    assert cache.lookup("checksum-a", "map-key-new") is None
    cache.publish("checksum-a", "map-key-new", 7)
    assert cache.lookup("checksum-a", "map-key-old") == 3  # untouched
    assert cache.lookup("checksum-a", "map-key-new") == 7


def test_band_touch_cache_survives_a_corrupted_db_file_as_a_full_miss(tmp_path):
    db_path = tmp_path / "band_touch_cache.db"
    db_path.write_text("not a sqlite file")
    cache = MicroBandTouchCache(str(db_path))
    assert cache.lookup("anything", "any-key") is None
    cache.publish("anything", "any-key", 5)  # swallowed, never raises


def test_readiness_route_survives_a_corrupted_band_touch_cache_db_as_a_full_miss(client, tmp_path):
    """TC-5's route-level claim: a corrupted band-touch cache DB file never turns
    ``GET /research/desk/micro/readiness`` into a 500 -- the request still returns HTTP 200 with a
    freshly-computed ``band_touch_count`` (mirroring ``MicroReadinessCache``'s own self-heal
    contract, proven at the route above for ``fallback_frac``)."""
    c, store, _cache = client
    _plant_dataset(store, symbol="AAPL")
    db_path = tmp_path / "band_touch_cache.db"
    db_path.write_text("not a sqlite file")

    resp = c.get("/research/desk/micro/readiness")

    assert resp.status_code == 200
    body = resp.json()
    assert body["joinable_corpus"]["band_touch_count"]["status"] == BAND_TOUCH_STATUS_ENUMERATED
    assert body["joinable_corpus"]["band_touch_count"]["count"] == 0  # honest -- no band map published


# --- TC-6: a hand-corrupted legacy dataset is surfaced, never dropped, never a crash -----------------


def test_corrupted_dataset_is_surfaced_never_dropped_never_a_crash(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    healthy = _plant_dataset(store, symbol="AAPL")
    corrupted = _plant_dataset(
        store, symbol="MSFT", window_start_utc="2026-06-10T13:00:00Z", window_end_utc="2026-06-10T13:01:00Z"
    )
    path = tmp_path / "datasets" / f"{corrupted['id']}.json"
    payload = json.loads(path.read_text())
    payload["record"]["meta"]["checksum"] = "deadbeef" * 8
    path.write_text(json.dumps(payload))

    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
    result = build_readiness(store, cache, dataset_dir=str(tmp_path / "datasets"))

    assert len(result["integrity_errors"]) == 1
    assert result["integrity_errors"][0]["file"] == f"{corrupted['id']}.json"

    assert result["totals"]["distinct_datasets"] == 1
    assert [s["dataset_id"] for s in result["shards"]] == [healthy["id"]]
    shard = result["shards"][0]
    assert shard["symbol"] == "AAPL"
    assert shard["checksum"] == healthy["checksum"]
    assert shard["trade_count"] == healthy["event_counts"]["trades"]
    assert shard["quote_count"] == healthy["event_counts"]["quotes"]
    assert 0.0 <= shard["fallback_frac"] <= 1.0
    assert shard["split_provenance"] == SPLIT_PROVENANCE_HAND_ASSIGNED
    assert shard["exposure_state"] == EXPOSURE_STATE_EXPLORATORY


def test_corrupted_dataset_surfaces_through_the_route_too(client, tmp_path):
    c, store, _cache = client
    healthy = _plant_dataset(store, symbol="AAPL")
    corrupted = _plant_dataset(
        store, symbol="MSFT", window_start_utc="2026-06-10T13:00:00Z", window_end_utc="2026-06-10T13:01:00Z"
    )
    # `tmp_path` resolves to the SAME directory the `client` fixture built `store` from (pytest
    # caches a function-scoped fixture once per test call and shares it across every consumer).
    path = tmp_path / "datasets" / f"{corrupted['id']}.json"
    payload = json.loads(path.read_text())
    payload["record"]["meta"]["checksum"] = "deadbeef" * 8
    path.write_text(json.dumps(payload))

    resp = c.get("/research/desk/micro/readiness")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["integrity_errors"]) == 1
    assert [s["dataset_id"] for s in body["shards"]] == [healthy["id"]]


# --- iter-28 TC-10: a warm durable index shared with a DIFFERENT store's content must never mask
# a checksum failure in a brand-new store's own files -- ``DatasetIndex.lookup`` keys on the
# absolute file path (``dataset_index.py``), so a scratch copy's never-before-seen path is always
# a genuine miss regardless of what else is warm in the shared index db.


def test_tc10_corrupted_dataset_surfaces_with_a_warm_durable_index_from_a_different_store(tmp_path):
    shared_index_db = str(tmp_path / "shared_dataset_index.db")

    # Warm the shared index db against a FIRST, unrelated, healthy store.
    other_store = DatasetStore(tmp_path / "other_datasets", index_db_path=shared_index_db)
    _plant_dataset(other_store, symbol="GOOG")
    other_store.list()  # populate the durable index for the OTHER store's own paths

    # A brand-new scratch store (a distinct root -> distinct absolute paths) pointed at the SAME
    # now-warm index db.
    store = DatasetStore(tmp_path / "scratch_datasets", index_db_path=shared_index_db)
    healthy = _plant_dataset(store, symbol="AAPL")
    corrupted = _plant_dataset(
        store, symbol="MSFT",
        window_start_utc="2026-06-10T13:00:00Z", window_end_utc="2026-06-10T13:01:00Z",
    )
    path = tmp_path / "scratch_datasets" / f"{corrupted['id']}.json"
    payload = json.loads(path.read_text())
    payload["record"]["meta"]["checksum"] = "deadbeef" * 8
    path.write_text(json.dumps(payload))

    cache = MicroReadinessCache(str(tmp_path / "readiness_cache.db"))
    result = build_readiness(store, cache, dataset_dir=str(tmp_path / "scratch_datasets"))

    assert len(result["integrity_errors"]) == 1
    assert result["integrity_errors"][0]["file"] == f"{corrupted['id']}.json"
    assert result["totals"]["distinct_datasets"] == 1
    assert [s["dataset_id"] for s in result["shards"]] == [healthy["id"]]


# --- iter-28 AUDIT (TC-10 reinforcement): the TC-10 test above plants its corrupted file in a
# scratch store whose absolute paths were NEVER written to the shared index, so
# ``DatasetIndex.lookup`` (``dataset_index.py``, keyed on ``(path, size, mtime_ns)``) is a
# guaranteed miss and the "warm index" premise cannot make that test fail -- it passes identically
# with the warming removed. The case that CAN exercise the cache is a warm row for the SAME path.
# This test pins that real boundary in all three directions, changing no production behaviour:
# (a) METADATA may legitimately be served from a warm row whenever the stat is byte-identical, so
# the one tamper shape that preserves BOTH size and mtime_ns is not surfaced by ``list()`` -- the
# stat IS the documented key; (b) dataset CONTENT is never served from any cache -- the full
# verifier runs on EVERY ``load_events``/``replay`` call with no bypass; (c) ANY stat difference
# re-runs the verifier and surfaces the integrity error explicitly.


def test_tc10b_warm_same_path_index_row_never_serves_tampered_content_and_re_verifies_on_any_stat_change(
    tmp_path,
):
    import app.research.datasets as datasets_module
    from app.research.datasets import DatasetIntegrityError

    index_db = str(tmp_path / "shared_dataset_index.db")
    root = tmp_path / "datasets"
    store = DatasetStore(root, index_db_path=index_db)
    record = _plant_dataset(store, symbol="AAPL")
    path = root / f"{record['id']}.json"

    # Age the file past the racy-write guard so it is publishable to the durable index, then warm
    # a REAL row for THIS exact path.
    st = os.stat(path)
    os.utime(path, ns=(st.st_atime_ns - 10_000_000_000, st.st_mtime_ns - 10_000_000_000))
    records, errors = store.list()
    assert errors == []
    assert len(records) == 1
    warm_stat = os.stat(path)

    # Tamper with the CONTENT while restoring the exact (size, mtime_ns) the warm row is keyed on:
    # a sha256 hex digest is swapped for another 64-character hex string, so the byte size is
    # unchanged by construction.
    original = path.read_text()
    assert original.count(record["checksum"]) == 1
    path.write_text(original.replace(record["checksum"], "deadbeef" * 8))
    os.utime(path, ns=(warm_stat.st_atime_ns, warm_stat.st_mtime_ns))
    tampered_stat = os.stat(path)
    assert tampered_stat.st_size == warm_stat.st_size
    assert tampered_stat.st_mtime_ns == warm_stat.st_mtime_ns

    datasets_module._reset_verified_cache_for_tests()
    warm_store = DatasetStore(root, index_db_path=index_db)

    # (a) the documented boundary, pinned honestly rather than left unknown.
    warm_records, warm_errors = warm_store.list()
    assert warm_errors == []
    assert len(warm_records) == 1

    # (b) CONTENT is never served from a cache -- the full verifier runs on every read.
    with pytest.raises(DatasetIntegrityError):
        warm_store.load_events(record["id"])

    # (c) ANY stat difference re-runs the verifier and surfaces the corruption explicitly.
    os.utime(path, ns=(tampered_stat.st_atime_ns, tampered_stat.st_mtime_ns - 20_000_000_000))
    datasets_module._reset_verified_cache_for_tests()
    restat_store = DatasetStore(root, index_db_path=index_db)
    restat_records, restat_errors = restat_store.list()
    assert [e["file"] for e in restat_errors] == [f"{record['id']}.json"]
    assert restat_records == []


# --- TC-7: a repeat call/GET never re-classifies, and the response is byte-identical ----------------


def test_repeat_build_readiness_call_does_not_reclassify(tmp_path, monkeypatch):
    store = DatasetStore(tmp_path / "datasets")
    _plant_dataset(store, symbol="AAPL")
    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
    dataset_dir = str(tmp_path / "datasets")

    call_count = {"n": 0}
    original = micro_readiness_module._compute_fallback_frac

    def _spy(events):
        call_count["n"] += 1
        return original(events)

    monkeypatch.setattr(micro_readiness_module, "_compute_fallback_frac", _spy)

    first = build_readiness(store, cache, dataset_dir=dataset_dir)
    assert call_count["n"] == 1
    second = build_readiness(store, cache, dataset_dir=dataset_dir)
    assert call_count["n"] == 1  # served from cache -- no second replay
    assert second == first


def test_repeat_get_does_not_reclassify_and_response_bytes_are_identical(client, monkeypatch):
    c, store, _cache = client
    _plant_dataset(store, symbol="AAPL")

    call_count = {"n": 0}
    original = micro_readiness_module._compute_fallback_frac

    def _spy(events):
        call_count["n"] += 1
        return original(events)

    monkeypatch.setattr(micro_readiness_module, "_compute_fallback_frac", _spy)

    first = c.get("/research/desk/micro/readiness")
    second = c.get("/research/desk/micro/readiness")
    assert call_count["n"] == 1
    assert first.status_code == 200 and second.status_code == 200
    assert first.content == second.content


# --- the honest zero-corpus case: still HTTP 200, study_floors still 3 rows -------------------------


def test_zero_corpus_is_an_honest_200_with_three_unmet_floor_rows(client):
    c, _store, _cache = client
    resp = c.get("/research/desk/micro/readiness")
    assert resp.status_code == 200
    body = resp.json()
    assert body["totals"]["distinct_symbol_days"] == 0
    assert body["totals"]["distinct_datasets"] == 0
    assert body["totals"]["rth_minutes_covered"] == 0.0
    assert body["totals"]["session_equivalents"] == 0.0
    assert body["shards"] == []
    assert body["integrity_errors"] == []
    assert len(body["study_floors"]) == 3
    assert {f["study_id"] for f in body["study_floors"]} == set(PILOT_STUDY_IDS)
    for floor in body["study_floors"]:
        assert floor["required_sessions"] == WF_TRAIN_MIN_SESSIONS + WF_TEST_MIN_SESSIONS == 60
        assert floor["available_sessions"] == 0
        assert floor["status"] == "floor_unmet"


# --- TC-1 through TC-5: the REAL 18-dataset / 12-symbol-day legacy corpus ---------------------------
#
# Module-scoped -- the per-shard fallback_frac classification over the real corpus (~0.92 GB of
# tick events) is genuinely expensive; every TC below shares ONE computed response.


@pytest.fixture(scope="module")
def real_readiness():
    # CONFIG.dataset_dir (never `_resolved()`) is the un-overridden package default -- the
    # committed real corpus, independent of any ambient TAPEOLOGY_DATASET_DIR the environment
    # might carry.
    #
    # iter-28: a fresh `tmp_path_factory` dir every pytest invocation forced a full re-parse +
    # re-checksum of the whole real store (26 GB / 98 files at this era's corpus size) on every
    # single run, so BOTH the `MicroReadinessCache` DB and the `DatasetStore`'s own metadata
    # index were given durable paths instead of a throwaway dir. Right primitives, wrong FILES:
    # they resolved to the OPERATOR backend's own `.data/dataset_index.db` and
    # `.data/micro_readiness_cache.db`, so a test run and a running backend became two writers of
    # one SQLite file for no benefit (iter-28 audit; owner ruling 2026-08-24, task A2). Same
    # production classes, same key semantics, same persistence -- now in the suite's OWN
    # `.data/test-cache/` namespace. See `tests/real_corpus_cache.py`.
    dataset_dir = CONFIG.dataset_dir
    store = real_corpus_dataset_store(dataset_dir)
    cache = real_corpus_readiness_cache(dataset_dir)
    return build_readiness(store, cache, dataset_dir=dataset_dir)


@pytest.fixture(scope="module")
def real_dataset_records():
    dataset_dir = CONFIG.dataset_dir
    store = real_corpus_dataset_store(dataset_dir)
    records, errors = store.list()
    assert errors == []  # the committed corpus is healthy -- a real integrity error here would
    # be a repo-hygiene regression, not something this iteration's tests should silently paper
    # over.
    return {record["id"]: record for record in records}


def test_tc1_real_corpus_distinct_symbol_days_and_datasets(real_readiness):
    assert real_readiness["totals"]["distinct_symbol_days"] == 12
    assert real_readiness["totals"]["distinct_datasets"] == 18
    assert len(real_readiness["shards"]) == 18
    assert real_readiness["integrity_errors"] == []


def test_tc2_real_corpus_session_equivalents_and_tick_gate(real_readiness):
    totals = real_readiness["totals"]
    assert 2.9 <= totals["session_equivalents"] <= 3.1
    # Regression-locks the exact measured value (goal.md's own stated "~3.01").
    assert totals["session_equivalents"] == pytest.approx(3.0089, abs=0.001)
    assert totals["referee_tick_gate_symbol_days"] == REFEREE_TICK_GATE_SYMBOL_DAYS == 150


def test_tc3_real_corpus_every_shard_carries_the_frozen_constants(real_readiness):
    fracs = [shard["fallback_frac"] for shard in real_readiness["shards"]]
    for shard, frac in zip(real_readiness["shards"], fracs):
        assert shard["split_provenance"] == "hand_assigned"
        assert shard["exposure_state"] == "exploratory"
        assert 0.0 <= frac <= 1.0
    # The measured real-corpus spread. goal.md's Build anchors describe this informally as
    # "29-76% per dataset"; the ACTUAL measured range (below) is very slightly wider at its top
    # end (one of the seven small PG reference-fixture windows, ~103-3229 trades each, is
    # noisier than the eleven multi-hour historical windows) -- this test locks in the real,
    # honestly-measured values rather than the descriptive approximation. See the dev handoff.
    assert min(fracs) == pytest.approx(0.2931, abs=0.001)
    assert max(fracs) == pytest.approx(0.8252, abs=0.001)


def test_tc4_real_corpus_shard_fields_match_the_store_verbatim(real_readiness, real_dataset_records):
    for shard in real_readiness["shards"]:
        record = real_dataset_records[shard["dataset_id"]]
        assert shard["checksum"] == record["checksum"]
        assert shard["trade_count"] == record["event_counts"]["trades"]
        assert shard["quote_count"] == record["event_counts"]["quotes"]
        assert shard["data_feed"] == record["data_feed"]
        assert shard["window_start_utc"] == record["window_start_utc"]
        assert shard["window_end_utc"] == record["window_end_utc"]
        # the store's OWN split tag stays whatever it was recorded as (train/holdout) -- this
        # module never mutates it; split_provenance describes HOW it was assigned, not its value.
        assert record["split"] in ("train", "holdout")


def test_tc5_real_corpus_all_three_pilot_studies_read_floor_unmet(real_readiness):
    floors = real_readiness["study_floors"]
    assert len(floors) == 3
    assert [f["study_id"] for f in floors] == list(PILOT_STUDY_IDS)
    for floor in floors:
        assert floor["floor_name"] == "wf_fold_geometry"
        assert floor["required_sessions"] == 60
        assert floor["available_sessions"] == 11
        assert floor["status"] == "floor_unmet"


# --- J-03 TC-5: the joinable_corpus field (docs/phases/goal-rapid-microscope-iter-3.md) ------------
#
# NOT the same "TC-5" as the J-01 real-corpus block just above (a numbering coincidence across
# iterations, not a duplicate) -- this section covers THIS iteration's own DEFINITION OF DONE item
# "GET /research/desk/micro/readiness serves the honest joinable_corpus breakdown".


def test_joinable_corpus_defaults_to_an_honest_zero_without_a_playbook_store(tmp_path):
    """``build_readiness`` called the OLD way (no ``playbook_store``, every pre-J-03 call site)
    still serves a well-shaped, honestly-zero ``joinable_corpus`` -- never an error, never an
    absent key."""
    store = DatasetStore(tmp_path / "datasets")
    _plant_dataset(store, symbol="AAPL")
    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
    body = build_readiness(store, cache, dataset_dir=str(tmp_path / "datasets"))
    assert body["joinable_corpus"] == {
        "total": 0,
        "playbook_signal_count": 0,
        "band_touch_count": {"status": "not_enumerated", "count": None},
        "by_setup_id": {},
        "playbook_integrity_errors": [],
        # spec section 7.5 point 6 (r4): the enumerator's own disclosure of what it left out.
        "withheld_excluded": 0,
    }


def test_joinable_corpus_matches_joinable_corpus_counts_directly(tmp_path):
    """``build_readiness``'s served field is BYTE-IDENTICAL to calling ``joinable_corpus_counts``
    directly over the same two stores -- single source of truth, never a second computation."""
    store = DatasetStore(tmp_path / "datasets")
    _plant_dataset(store, symbol="AAPL")
    playbook_store = PlaybookStore(tmp_path / "playbook")
    playbook_store.record(
        session_date="2026-06-09",
        config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature="sig-readiness-tc5",
        payload_version=1,
        parameters=playbook_parameters(),
        register="",
        signals=[
            {"symbol": "AAPL", "setup_id": "opening_range_break", "trigger_ts": "2026-06-09T13:00:30Z"},
        ],
        absences=[], diagnostics=[],
    )
    cache = MicroReadinessCache(str(tmp_path / "cache.db"))

    body = build_readiness(
        store, cache, dataset_dir=str(tmp_path / "datasets"), playbook_store=playbook_store
    )

    assert body["joinable_corpus"] == joinable_corpus_counts(store, playbook_store)
    assert body["joinable_corpus"] == {
        "total": 1,
        "playbook_signal_count": 1,
        "band_touch_count": {"status": "not_enumerated", "count": None},
        "by_setup_id": {"opening_range_break": 1},
        "playbook_integrity_errors": [],
        # spec section 7.5 point 6 (r4): the enumerator's own disclosure of what it left out.
        "withheld_excluded": 0,
    }


def test_joinable_corpus_is_served_through_the_route_and_is_non_negative_and_never_hardcoded(
    client, tmp_path
):
    """TC-5's own route-level acceptance: called twice, the SERVED ``joinable_corpus`` is
    identical, every count is a non-negative int, and it reflects a REAL planted signal -- never a
    hardcoded placeholder."""
    c, store, _cache = client
    _plant_dataset(store, symbol="AAPL")
    # Plants into the SAME tmp_path the `client` fixture already scoped its (overridden) playbook
    # store to -- a second PlaybookStore instance over the identical on-disk directory.
    playbook_store = PlaybookStore(tmp_path / "playbook")
    playbook_store.record(
        session_date="2026-06-09",
        config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature="sig-readiness-route-tc5",
        payload_version=1,
        parameters=playbook_parameters(),
        register="",
        signals=[
            {"symbol": "AAPL", "setup_id": "jbe", "trigger_ts": "2026-06-09T13:00:15Z"},
            {"symbol": "AAPL", "setup_id": "jbe", "trigger_ts": "2099-01-01T00:00:00Z"},  # not joinable
        ],
        absences=[], diagnostics=[],
    )

    first = c.get("/research/desk/micro/readiness").json()["joinable_corpus"]
    second = c.get("/research/desk/micro/readiness").json()["joinable_corpus"]

    assert first == second
    for key in ("total", "playbook_signal_count"):
        assert isinstance(first[key], int) and first[key] >= 0
    # band_touch_count is a typed state, never a bare int (iter-4 passenger fix, TC-15) --
    # distinguishable from a real count read straight off the field. J-09 materializes the ROUTE's
    # own value (this fixture's tmp_path-scoped bar store carries no tradable map, so an honest
    # real zero, never the pre-J-09 sentinel -- see the dedicated TC-15 block below).
    assert first["band_touch_count"] == {"status": BAND_TOUCH_STATUS_ENUMERATED, "count": 0}
    assert first["playbook_signal_count"] == 1  # only the in-window signal counts
    assert first["by_setup_id"] == {"jbe": 1}


def test_real_corpus_readiness_still_serves_an_honest_zero_joinable_corpus_without_a_playbook_store(
    real_readiness,
):
    """The module-scoped real-corpus fixture above calls ``build_readiness`` the OLD way (no
    ``playbook_store``) -- confirms the new field is present and honestly zero there too, never an
    absent key on the real 18-dataset corpus response."""
    assert real_readiness["joinable_corpus"] == {
        "total": 0,
        "playbook_signal_count": 0,
        "band_touch_count": {"status": "not_enumerated", "count": None},
        "by_setup_id": {},
        "playbook_integrity_errors": [],
        # spec section 7.5 point 6 (r4): the enumerator's own disclosure of what it left out.
        "withheld_excluded": 0,
    }


# --- TC-15 (iter-4 passenger fix, docs/phases/goal-rapid-microscope-iter-4.md): band_touch_count is
# a typed state on THIS route, never a bare int a reader could mistake for something else. J-09
# (docs/phases/goal-rapid-microscope-iter-21.md, TC-9) materializes the route's OWN value: it now
# ALWAYS constructs a resolver (`micro_routes.get_micro_readiness`'s own docstring), so this route's
# served state is `enumerated` from this iteration forward -- `build_readiness` called DIRECTLY
# without a `resolver` (every other caller in this file) still serves the honest `not_enumerated`
# sentinel unchanged (`micro_join.py`'s own "byte-identical when omitted" contract). ---------------


def test_tc15_readiness_route_serves_band_touch_count_as_a_typed_enumerated_state(client):
    c, _store, _cache = client
    resp = c.get("/research/desk/micro/readiness")
    assert resp.status_code == 200
    band_touch = resp.json()["joinable_corpus"]["band_touch_count"]
    assert not isinstance(band_touch, int)
    # No dataset planted in this test's own tmp_path corpus, and no tradable map exists in its
    # tmp_path-scoped bar store either -- an honest, real ZERO (never the pre-J-09 sentinel).
    assert band_touch == {"status": BAND_TOUCH_STATUS_ENUMERATED, "count": 0}


# --- TC-9 (goal-rapid-microscope-iter-21, J-09): a 3-known-touch fixture, through the LIVE route --


def _plant_touch_dataset(store: DatasetStore, *, symbol: str = "TQR") -> dict:
    """A trade price sequence crossing a `[149.00, 149.02]` band at exactly 3 known instants
    (t=1.0, 4.0, 6.0) -- the SAME hand-derived oracle pattern `test_micro_join.py`'s own TC-3
    tests use, transcribed here so this route-level test can plant it directly (`_plant_dataset`
    above uses a fixed, unrelated 3-event fixture built for the `fallback_frac` tests)."""
    events = [
        QuoteEvent(symbol, 0.0, 148.98, 149.03, 100, 100),
        TradeEvent(symbol, 0.0, 148.90, 10, Side.SELL),
        TradeEvent(symbol, 1.0, 149.01, 10, Side.BUY),
        TradeEvent(symbol, 2.0, 149.01, 10, Side.BUY),
        TradeEvent(symbol, 3.0, 148.90, 10, Side.SELL),
        TradeEvent(symbol, 4.0, 149.015, 10, Side.BUY),
        TradeEvent(symbol, 5.0, 149.05, 10, Side.BUY),
        TradeEvent(symbol, 6.0, 149.00, 10, Side.BUY),
        TradeEvent(symbol, 7.0, 149.019, 10, Side.BUY),
    ]
    return store.record(
        symbol=symbol, source="fixture", source_kind="fixture", source_id=f"{symbol}-touch-fixture",
        split="train", window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
        data_feed="sip", epoch_anchor=0.0, events=events,
    )


def test_tc9_readiness_route_serves_the_real_band_touch_count_on_a_3_known_touch_fixture(client):
    """TC-9, verbatim: given a fixture with 3 known wall touches, ``GET /research/desk/micro/
    readiness`` serves ``joinable_corpus.band_touch_count == 3``, not the ``not_enumerated``
    sentinel. Publishes the band map into the SAME on-disk cache the route's own internally
    constructed ``BandMapResolver`` reads (``resolve_tradability_cache_db_path`` over the
    ``client`` fixture's own overridden ``bar_store``) -- never a second, in-process-only
    resolver the route could not possibly see."""
    c, store, _cache = client
    meta = _plant_touch_dataset(store)
    bar_store = app.dependency_overrides[get_bar_store]()  # the SAME override the route resolves
    route_cache = TradabilityCache(resolve_tradability_cache_db_path(str(bar_store.root)))
    resolver = BandMapResolver(bar_store, CONFIG, cache=route_cache)
    window_start_epoch = parse_utc_epoch(meta["window_start_utc"])
    resolver._cache.publish(
        resolver.map_key("TQR", window_start_epoch),
        {"basis_day": "2026-06-08", "bands": [{"side": "resistance", "price_low": 149.00, "price_high": 149.02}]},
    )

    resp = c.get("/research/desk/micro/readiness")
    assert resp.status_code == 200
    band_touch = resp.json()["joinable_corpus"]["band_touch_count"]
    assert band_touch == {"status": "enumerated", "count": 3}


def test_tc15_real_corpus_readiness_also_serves_the_typed_band_touch_count(real_readiness):
    """``real_readiness`` (module-scoped) calls ``build_readiness`` DIRECTLY, with no ``resolver``
    -- byte-identical to every pre-J-09 caller (module docstring's own "omitting it keeps the
    sentinel" contract), independent of what the LIVE route now serves."""
    band_touch = real_readiness["joinable_corpus"]["band_touch_count"]
    assert not isinstance(band_touch, int)
    assert band_touch["status"] == "not_enumerated"
    assert band_touch["count"] is None


# === Iteration 11 (docs/phases/goal-rapid-microscope-iter-11.md, spec section 7.5 point 7, r5):
# the opaque-pool predicate widens WHICH datasets `build_readiness` withholds -- TC-1/TC-3/TC-4/
# TC-10. `_plant_pool_dataset` below is a DEDICATED fixture builder, never `_plant_dataset` above
# (whose fixed `_events(symbol)` shape collides across dates for the SAME symbol on
# `DatasetAlreadyRegistered`) -- it mirrors `test_vault.py`'s own per-(symbol, date) content-nonce
# precedent instead.
# =====================================================================================================

_POOL_FIXTURE_SECRET = b"a-micro-readiness-fixture-vault-secret"


def _plant_pool_dataset(store: DatasetStore, *, symbol: str, session_date: str, nonce: float) -> dict:
    """One dataset for (symbol, session_date), content-distinct via `nonce` in its one trade's
    price -- so multiple dates for the SAME symbol never collide on `DatasetAlreadyRegistered`."""
    events = [
        QuoteEvent(symbol, 0.0, 99.99, 100.02, 100, 100),
        TradeEvent(symbol, 0.1, 100.0 + nonce, 10, Side.BUY),
    ]
    return store.record(
        symbol=symbol, source="fixture", source_kind="fixture", source_id=f"{symbol}-fixture",
        split="train", window_start_utc=f"{session_date}T13:30:00Z",
        window_end_utc=f"{session_date}T20:00:00Z", data_feed="sip", epoch_anchor=0.0, events=events,
    )


def _pool_fixture(tmp_path):
    """Registers ONE universe U (``symbol_rule=["ZPQA", "ZPQB"]``, ``date_rule=["2026-06-01",
    "2026-06-02"]``, 4 expected pairs) and records all 4 corresponding datasets AFTER U's
    ``registered_at`` (real sequential execution -- register first, record after -- gives this
    ordering for free, exactly as a real recorder run would). Returns ``(store, dataset_dir,
    shard_ledger, universe_ledger, metas)`` where ``metas`` maps ``(symbol, date) -> meta``; NONE
    of the 4 carries any vault shard-ledger row yet -- callers seal/assign/expose as their own
    scenario requires."""
    dataset_dir = tmp_path / "datasets"
    vault_dir = tmp_path / "micro_vault"
    store = DatasetStore(dataset_dir)
    universe_ledger = vault.VaultUniverseLedger(str(vault_dir))
    symbols, dates = ["ZPQA", "ZPQB"], ["2026-06-01", "2026-06-02"]
    vault.register_universe(
        universe_ledger, universe_id="pool-u1", symbol_rule=symbols, date_rule=dates,
        vault_secret_commitment=vault.commit_vault_secret(_POOL_FIXTURE_SECRET),
    )
    metas = {}
    for s_index, symbol in enumerate(symbols):
        for d_index, session_date in enumerate(dates):
            metas[(symbol, session_date)] = _plant_pool_dataset(
                store, symbol=symbol, session_date=session_date, nonce=s_index * 10 + d_index,
            )
    shard_ledger = vault.VaultShardLedger(str(vault_dir))
    return store, str(dataset_dir), shard_ledger, universe_ledger, metas


def test_tc1_a_registered_pool_with_mixed_ledger_tracked_and_untracked_members_withholds_all_four(
    tmp_path,
):
    """TC-1 (phase spec): a registered universe's 4 expected pairs, 2 carrying an explicit
    ``sealed`` ledger row and the other 2 carrying NONE at all -- ``build_readiness`` withholds
    ALL FOUR per-shard, and ``sealed_tranche`` reports ``shard_count: 4``. This is the exact
    iteration-11 gap made concrete: pre-fix, the 2 untracked members would have appeared in
    ``shards`` with full identity, since the old predicate only ever checked for a ledger row."""
    store, dataset_dir, shard_ledger, _universe_ledger, metas = _pool_fixture(tmp_path)

    # 2 of 4 members get an explicit sealed ledger row; the other 2 get NONE.
    for pair in [("ZPQA", "2026-06-01"), ("ZPQB", "2026-06-02")]:
        meta = metas[pair]
        vault.seal_shard(
            shard_ledger, dataset_id=meta["id"], universe_id="pool-u1",
            content_checksum=meta["checksum"], event_count=meta["event_counts"]["total"],
            vault_secret=_POOL_FIXTURE_SECRET,
        )

    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
    result = build_readiness(store, cache, dataset_dir=dataset_dir)

    assert result["shards"] == []  # none of the 4 -- ledger-tracked OR untracked -- appears
    assert result["sealed_tranche"]["shard_count"] == 4
    assert result["sealed_tranche"]["symbol_days"] == 4
    assert result["sealed_tranche"]["by_universe"] == {"pool-u1": {"shard_count": 4, "symbol_days": 4}}
    assert result["totals"]["distinct_datasets"] == 0


def test_tc3_exposing_one_pool_member_reveals_only_that_one_row(tmp_path):
    """TC-3 (phase spec): one pool member is assigned + exposed via the EXISTING family-bound
    path; the remaining 3 unresolved pairs still contribute zero per-shard rows and only the
    aggregate count, now ``shard_count: 3``."""
    store, dataset_dir, shard_ledger, _universe_ledger, metas = _pool_fixture(tmp_path)
    exposed_pair = ("ZPQA", "2026-06-01")
    exposed_meta = metas[exposed_pair]
    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    vault.seal_shard(
        shard_ledger, dataset_id=exposed_meta["id"], universe_id="pool-u1",
        content_checksum=exposed_meta["checksum"], event_count=exposed_meta["event_counts"]["total"],
        vault_secret=_POOL_FIXTURE_SECRET,
    )
    vault.assign_shard(
        shard_ledger, dataset_id=exposed_meta["id"], family_root_id=family_root,
        symbol=exposed_pair[0], session_date=exposed_pair[1],
    )
    vault.expose_shard(shard_ledger, dataset_id=exposed_meta["id"], family_root_id=family_root)

    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
    result = build_readiness(store, cache, dataset_dir=dataset_dir)

    assert [s["dataset_id"] for s in result["shards"]] == [exposed_meta["id"]]
    assert result["shards"][0]["symbol"] == exposed_pair[0]
    assert result["shards"][0]["session_date"] == exposed_pair[1]
    assert result["sealed_tranche"]["shard_count"] == 3
    assert result["sealed_tranche"]["by_universe"] == {"pool-u1": {"shard_count": 3, "symbol_days": 3}}


def test_tc4_a_dataset_recorded_before_a_later_universes_registration_is_never_withheld(tmp_path):
    """TC-4 (phase spec): a dataset recorded BEFORE a universe's registration is never
    retroactively withheld by that universe's rule, even when it shares a (symbol, date) with it
    -- protects the 12 permanently-exploratory legacy symbol-days from a later universe naming the
    same panel by coincidence."""
    dataset_dir = tmp_path / "datasets"
    vault_dir = tmp_path / "micro_vault"
    store = DatasetStore(dataset_dir)

    # the dataset exists FIRST -- a "legacy" symbol-day, in real chronological order.
    pre_existing = _plant_pool_dataset(store, symbol="ZPQC", session_date="2026-06-03", nonce=1.0)

    # a LATER universe happens to name the exact same (symbol, date) in its rule.
    universe_ledger = vault.VaultUniverseLedger(str(vault_dir))
    vault.register_universe(
        universe_ledger, universe_id="pool-u2", symbol_rule=["ZPQC"], date_rule=["2026-06-03"],
        vault_secret_commitment=vault.commit_vault_secret(_POOL_FIXTURE_SECRET),
    )

    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
    result = build_readiness(store, cache, dataset_dir=str(dataset_dir))

    assert [s["dataset_id"] for s in result["shards"]] == [pre_existing["id"]]
    assert result["sealed_tranche"] == {"shard_count": 0, "symbol_days": 0, "by_universe": {}}

    # the vault predicate directly, at the boundary -- the same claim, as the module's own unit.
    shard_ledger = vault.VaultShardLedger(str(vault_dir))
    membership = vault.unresolved_pool_universe_by_dataset_id(
        shard_ledger, universe_ledger,
        [(pre_existing["id"], "ZPQC", "2026-06-03", pre_existing["created_utc"])],
    )
    assert membership == {}


def test_tc10_the_withhold_check_never_loads_events_for_a_pool_member_before_its_exposure(
    tmp_path, monkeypatch
):
    """TC-10 (phase spec): ``store.load_events`` is never called for a still-withheld shard's
    dataset id during ``build_readiness``'s ``fallback_frac`` walk -- proven DIRECTLY via a spy,
    never inferred from the served shape alone. Exercises BOTH withheld shapes at once (one
    member carries an explicit ``sealed`` ledger row, two carry none at all) alongside a FOURTH,
    genuinely exposed member -- so the spy has something legitimate to prove it still fires
    correctly; a trap that would also pass with ``load_events`` disabled entirely proves
    nothing."""
    store, dataset_dir, shard_ledger, _universe_ledger, metas = _pool_fixture(tmp_path)

    sealed_pair = ("ZPQA", "2026-06-01")
    exposed_pair = ("ZPQB", "2026-06-02")
    untracked_pairs = [("ZPQA", "2026-06-02"), ("ZPQB", "2026-06-01")]

    sealed_meta = metas[sealed_pair]
    vault.seal_shard(
        shard_ledger, dataset_id=sealed_meta["id"], universe_id="pool-u1",
        content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
        vault_secret=_POOL_FIXTURE_SECRET,
    )
    exposed_meta = metas[exposed_pair]
    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    vault.seal_shard(
        shard_ledger, dataset_id=exposed_meta["id"], universe_id="pool-u1",
        content_checksum=exposed_meta["checksum"], event_count=exposed_meta["event_counts"]["total"],
        vault_secret=_POOL_FIXTURE_SECRET,
    )
    vault.assign_shard(
        shard_ledger, dataset_id=exposed_meta["id"], family_root_id=family_root,
        symbol=exposed_pair[0], session_date=exposed_pair[1],
    )
    vault.expose_shard(shard_ledger, dataset_id=exposed_meta["id"], family_root_id=family_root)

    original_load_events = store.load_events
    seen_ids: list[str] = []

    def _spy_load_events(dataset_id):
        seen_ids.append(dataset_id)
        return original_load_events(dataset_id)

    monkeypatch.setattr(store, "load_events", _spy_load_events)

    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
    result = build_readiness(store, cache, dataset_dir=dataset_dir)

    assert [s["dataset_id"] for s in result["shards"]] == [exposed_meta["id"]]
    assert result["sealed_tranche"]["shard_count"] == 3  # 1 sealed + 2 untracked
    withheld_ids = {sealed_meta["id"], *(metas[p]["id"] for p in untracked_pairs)}
    assert seen_ids == [exposed_meta["id"]]  # ONLY the exposed shard's events were ever read
    assert not (set(seen_ids) & withheld_ids)
