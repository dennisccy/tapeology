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
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.engine.aggressor import classify_aggressor
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.research import micro_readiness as micro_readiness_module
from app.research.datasets import DatasetStore
from app.research.micro_readiness import (
    EXPOSURE_STATE_EXPLORATORY,
    PILOT_STUDY_IDS,
    SPLIT_PROVENANCE_HAND_ASSIGNED,
    WF_TEST_MIN_SESSIONS,
    WF_TRAIN_MIN_SESSIONS,
    MicroReadinessCache,
    build_readiness,
    resolve_micro_readiness_cache_db_path,
)
from app.research.desk_playbook import PlaybookStore, playbook_parameters
from app.research.desk_routes import get_playbook_store
from app.research.micro_join import joinable_corpus_counts
from app.research.micro_routes import get_micro_readiness_cache
from app.research.referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS
from app.research.routes import get_dataset_store

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
    # J-03: the route now also depends on a playbook store (the joinable_corpus field) -- a
    # tmp_path-scoped, empty-by-default one, so this fixture's existing hermeticity contract is
    # unaffected (never the real, ambient .data/playbook directory).
    playbook_store = PlaybookStore(tmp_path / "playbook")
    app.dependency_overrides[get_dataset_store] = lambda: dataset_store
    app.dependency_overrides[get_micro_readiness_cache] = lambda: cache
    app.dependency_overrides[get_playbook_store] = lambda: playbook_store
    with TestClient(app) as c:
        yield c, dataset_store, cache
    app.dependency_overrides.pop(get_dataset_store, None)
    app.dependency_overrides.pop(get_micro_readiness_cache, None)
    app.dependency_overrides.pop(get_playbook_store, None)


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
def real_readiness(tmp_path_factory):
    # CONFIG.dataset_dir (never `_resolved()`) is the un-overridden package default -- the
    # committed real corpus, independent of any ambient TAPEOLOGY_DATASET_DIR the environment
    # might carry.
    dataset_dir = CONFIG.dataset_dir
    store = DatasetStore(dataset_dir)
    cache_dir = tmp_path_factory.mktemp("micro_readiness_real_cache")
    cache = MicroReadinessCache(str(cache_dir / "cache.db"))
    return build_readiness(store, cache, dataset_dir=dataset_dir)


@pytest.fixture(scope="module")
def real_dataset_records():
    store = DatasetStore(CONFIG.dataset_dir)
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
    # band_touch_count is a typed "not enumerated" state, never a bare int (iter-4 passenger fix,
    # TC-15) -- distinguishable from a real zero count.
    assert first["band_touch_count"] == {"status": "not_enumerated", "count": None}
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
    }


# --- TC-15 (iter-4 passenger fix, docs/phases/goal-rapid-microscope-iter-4.md): band_touch_count is
# a typed "not enumerated" state on THIS route, never a bare zero a reader could mistake for a real
# count ------------------------------------------------------------------------------------------


def test_tc15_readiness_route_serves_band_touch_count_as_a_typed_not_enumerated_state(client):
    c, _store, _cache = client
    resp = c.get("/research/desk/micro/readiness")
    assert resp.status_code == 200
    band_touch = resp.json()["joinable_corpus"]["band_touch_count"]
    assert not isinstance(band_touch, int)
    assert band_touch == {"status": "not_enumerated", "count": None}


def test_tc15_real_corpus_readiness_also_serves_the_typed_band_touch_count(real_readiness):
    band_touch = real_readiness["joinable_corpus"]["band_touch_count"]
    assert not isinstance(band_touch, int)
    assert band_touch["status"] == "not_enumerated"
    assert band_touch["count"] is None
