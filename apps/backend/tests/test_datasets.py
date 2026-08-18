"""The historical tape dataset store (capability 1 / era-3, J-02) — store-level discipline.

The store is the SINGLE owner of Data Contract row 30: recording, checksums, the immutable
train/holdout split tag, verified loads, and byte-identical unpaced replay through a fresh
``TapeEngine``. Everything here is keyless: recording resolves the committed PG SIP reference
fixture through the SAME source-resolution path studies use, so CI proves
record -> register -> replay end-to-end with no credentials.

Locked disciplines (each an anti-goal or a J-02 acceptance clause):
  * metadata correctness — symbol, UTC window, ``data_feed`` (via the ONE feed_basis mapping),
    exact event counts, a content checksum, the split tag, and the epoch anchor;
  * split immutability — the tag is assigned at registration and frozen: re-recording the same
    content under ANY split is refused with a 409-style ``DatasetAlreadyRegistered`` (there is
    no update/re-tag/delete code path at all — immutability is structural);
  * verified loads — the checksum is recomputed on EVERY load; a corrupted or tampered file
    (events OR the split field itself) surfaces an explicit ``DatasetIntegrityError``, never
    silence, never a fabricated dataset;
  * byte-identical replay — replaying a stored dataset through a fresh engine equals replaying
    the ORIGINAL source stream, tick for tick (full snapshot equality) and in the serialized
    history, and re-runs are identical (determinism);
  * the committed miniature train + holdout fixture pair loads through the REAL store path and
    replays keyless in CI;
  * ``dataset_dir`` is an operational storage location EXCLUDED from ``config_fingerprint``
    (the ``journal_db_path`` precedent) — two journals identical in every threshold but storing
    datasets in different directories MUST share a fingerprint.
"""

from __future__ import annotations

import ast
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.config import CONFIG, Config
from app.engine.tape_engine import TapeEngine
from app.providers.adapters.base import HistoricalWindow
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.providers.historical import HistoricalProvider
from app.research.datasets import (
    SPLIT_HOLDOUT,
    SPLIT_TRAIN,
    DatasetAlreadyRegistered,
    DatasetIntegrityError,
    DatasetNotFound,
    DatasetStore,
    EmptyWindowError,
    record_from_source,
)
from app.serializers import serialize_history
from fakes import load_fixture_window

PG_FIXTURE = (
    Path(__file__).parent / "fixtures" / "alpaca" / "PG_20260609_170000_171000_sip.json"
)
# The committed miniature train + holdout dataset pair (generated ONCE through the real record
# path by scripts/generate_dataset_fixtures.py — never hand-crafted JSON).
FIXTURE_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets"

# Two DISJOINT sub-windows of the committed PG SIP reference window (17:00–17:10 UTC): nothing
# is ever judged on the data it was tuned on, so train and holdout never overlap.
TRAIN_START, TRAIN_END = "2026-06-09T17:00:00Z", "2026-06-09T17:01:00Z"
HOLDOUT_START, HOLDOUT_END = "2026-06-09T17:05:00Z", "2026-06-09T17:05:45Z"


def _epoch(iso: str) -> float:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def _sliced_reference_window(start_iso: str, end_iso: str) -> HistoricalWindow:
    """The ORIGINAL source stream's window for a requested slice — built independently of the
    store (the comparison baseline the byte-identity assertions replay)."""
    window, _raw = load_fixture_window(PG_FIXTURE)
    s, e = _epoch(start_iso), _epoch(end_iso)
    return HistoricalWindow(
        window.symbol,
        tuple(t for t in window.trades if s <= t.epoch < e),
        tuple(q for q in window.quotes if s <= q.epoch < e),
    )


def _record_reference(store: DatasetStore, start: str, end: str, split: str) -> dict:
    return record_from_source(
        store,
        source_kind="reference",
        source_id="",
        split=split,
        start=start,
        end=end,
        config=CONFIG,
    )


def _replay_window(window: HistoricalWindow, scenario: str) -> tuple[TapeEngine, list]:
    """Replay a source window unpaced through a FRESH engine (the studies-runner pattern),
    returning the engine and the full snapshot path."""
    provider = HistoricalProvider(window.symbol, window, scenario)
    engine = TapeEngine(window.symbol, scenario, CONFIG, epoch_anchor=provider.epoch_anchor)
    return engine, [engine.process_event(ev) for ev in provider.stream()]


# --- record: metadata correctness ----------------------------------------------------------------


def test_record_reference_slice_stores_correct_metadata(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    meta = _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)

    source_window = _sliced_reference_window(TRAIN_START, TRAIN_END)
    assert meta["symbol"] == "PG"
    assert meta["split"] == SPLIT_TRAIN
    assert meta["window_start_utc"] == TRAIN_START
    assert meta["window_end_utc"] == TRAIN_END
    # data_feed via the ONE scenario -> feed mapping (feed_basis): a recorded dataset is
    # historical tape, so it stamps the config-owned historical feed — never a hardcoded "sip".
    assert meta["data_feed"] == CONFIG.historical_feed
    # EXACT event counts — the slice's real trades and quotes, nothing dropped or fabricated.
    assert meta["event_counts"]["trades"] == len(source_window.trades)
    assert meta["event_counts"]["quotes"] == len(source_window.quotes)
    assert meta["event_counts"]["total"] == len(source_window.trades) + len(source_window.quotes)
    assert meta["event_counts"]["trades"] > 0 and meta["event_counts"]["quotes"] > 0
    # Content checksum present (sha256 hex) and the epoch anchor is the slice's first record.
    assert isinstance(meta["checksum"], str) and len(meta["checksum"]) == 64
    int(meta["checksum"], 16)  # hex or this raises
    first_epoch = min(
        [t.epoch for t in source_window.trades] + [q.epoch for q in source_window.quotes]
    )
    assert meta["epoch_anchor"] == first_epoch
    assert meta["source_kind"] == "reference"
    assert meta["id"] and meta["created_utc"].endswith("Z")


def test_split_tags_register_and_survive_a_store_reload(tmp_path):
    root = tmp_path / "datasets"
    train = _record_reference(DatasetStore(root), TRAIN_START, TRAIN_END, SPLIT_TRAIN)
    holdout = _record_reference(DatasetStore(root), HOLDOUT_START, HOLDOUT_END, SPLIT_HOLDOUT)

    # A FRESH store instance over the same directory (a reload) serves the same frozen tags.
    reloaded = DatasetStore(root)
    assert reloaded.get(train["id"])["split"] == SPLIT_TRAIN
    assert reloaded.get(holdout["id"])["split"] == SPLIT_HOLDOUT
    records, errors = reloaded.list()
    assert errors == []
    assert {r["id"]: r["split"] for r in records} == {
        train["id"]: SPLIT_TRAIN,
        holdout["id"]: SPLIT_HOLDOUT,
    }


# --- split immutability (409-style refusal; no re-tag path exists) --------------------------------


def test_retagging_registered_content_is_refused(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    original = _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)

    # The SAME tape content under a DIFFERENT split is a re-tag attempt — refused, naming the
    # existing dataset and its frozen tag.
    with pytest.raises(DatasetAlreadyRegistered) as excinfo:
        _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_HOLDOUT)
    assert original["id"] in str(excinfo.value)
    assert SPLIT_TRAIN in str(excinfo.value)
    assert "frozen" in str(excinfo.value)

    # The same split is refused too (the dataset already exists — immutable, never re-recorded).
    with pytest.raises(DatasetAlreadyRegistered):
        _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)

    # Nothing was written by either refusal and the original tag is untouched.
    records, errors = store.list()
    assert errors == []
    assert [r["id"] for r in records] == [original["id"]]
    assert store.get(original["id"])["split"] == SPLIT_TRAIN


# --- replay: byte-identical to the source stream, deterministic across re-runs --------------------


def test_replay_is_deterministic_across_reruns(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    meta = _record_reference(store, HOLDOUT_START, HOLDOUT_END, SPLIT_HOLDOUT)

    first = list(store.replay(meta["id"], CONFIG))
    second = list(store.replay(meta["id"], CONFIG))
    assert len(first) == meta["event_counts"]["total"] > 0
    # Full frozen-snapshot equality at EVERY tick — state, confidence, features, history inputs.
    assert first == second


def test_replay_matches_the_original_source_stream_byte_identically(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    meta = _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)

    # The ORIGINAL source stream: the same slice replayed straight from the committed fixture
    # through the SAME provider + a fresh engine (never through the store).
    source_window = _sliced_reference_window(TRAIN_START, TRAIN_END)
    source_engine, source_path = _replay_window(source_window, meta["source"])

    dataset_path = list(store.replay(meta["id"], CONFIG))
    assert len(dataset_path) == len(source_path) > 0
    assert dataset_path == source_path  # every snapshot field, every tick

    # The serialized history (bars + markers) is byte-identical too: drive a fresh engine over
    # the store's VERIFIED loaded events and compare the canonical projection.
    dataset_engine = TapeEngine(
        meta["symbol"], meta["source"], CONFIG, epoch_anchor=meta["epoch_anchor"]
    )
    for event in store.load_events(meta["id"]):
        dataset_engine.process_event(event)
    for bar in CONFIG.history_bar_sizes:
        a = json.dumps(
            serialize_history(dataset_engine.history, bar, epoch_anchor=dataset_engine.epoch_anchor),
            sort_keys=True,
        )
        b = json.dumps(
            serialize_history(source_engine.history, bar, epoch_anchor=source_engine.epoch_anchor),
            sort_keys=True,
        )
        assert a == b, f"history at bar={bar}s diverged between dataset and source replay"


# --- verified loads: corruption is an explicit, distinct error ------------------------------------


def _tamper(path: Path, mutate) -> None:
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data))


def test_corrupted_event_data_surfaces_an_explicit_integrity_error(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    meta = _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)
    file_path = tmp_path / "datasets" / f"{meta['id']}.json"

    def corrupt_price(data):
        for row in data["record"]["events"]:
            if row["type"] == "trade":
                row["price"] = row["price"] + 1.0  # one tampered print
                return

    _tamper(file_path, corrupt_price)
    with pytest.raises(DatasetIntegrityError):
        store.get(meta["id"])
    with pytest.raises(DatasetIntegrityError):
        list(store.replay(meta["id"], CONFIG))
    with pytest.raises(DatasetIntegrityError):
        store.load_events(meta["id"])


def test_tampering_the_split_tag_itself_breaks_the_checksum(tmp_path):
    # The split is INSIDE the verified region: editing the file's tag is detected on load — the
    # frozen-at-registration guarantee is enforced by the checksum, not by policing an API.
    store = DatasetStore(tmp_path / "datasets")
    meta = _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)
    file_path = tmp_path / "datasets" / f"{meta['id']}.json"

    _tamper(file_path, lambda data: data["record"]["meta"].__setitem__("split", SPLIT_HOLDOUT))
    with pytest.raises(DatasetIntegrityError):
        store.get(meta["id"])


def test_unparseable_file_is_an_explicit_integrity_error(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    meta = _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)
    (tmp_path / "datasets" / f"{meta['id']}.json").write_text("{not json")
    with pytest.raises(DatasetIntegrityError):
        store.get(meta["id"])


def test_unknown_dataset_id_raises_not_found(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    with pytest.raises(DatasetNotFound):
        store.get("no-such-dataset")
    with pytest.raises(DatasetNotFound):
        store.load_events("no-such-dataset")


def test_empty_requested_window_is_an_explicit_refusal(tmp_path):
    # A window inside the fixture's day but BEFORE its captured span: zero events — an explicit
    # EmptyWindowError, never an empty dataset written, never fabricated events.
    store = DatasetStore(tmp_path / "datasets")
    with pytest.raises(EmptyWindowError):
        _record_reference(store, "2026-06-09T16:00:00Z", "2026-06-09T16:01:00Z", SPLIT_TRAIN)
    records, errors = store.list()
    assert records == [] and errors == []


# --- the committed miniature train + holdout fixture pair (keyless CI proof) ----------------------


def test_committed_fixture_pair_loads_through_the_real_store_path_and_replays_keyless():
    store = DatasetStore(FIXTURE_DATASET_DIR)
    records, errors = store.list()
    assert errors == [], f"committed fixture datasets failed verification: {errors}"
    assert len(records) == 2, "the committed pair is exactly one train + one holdout dataset"
    assert sorted(r["split"] for r in records) == [SPLIT_HOLDOUT, SPLIT_TRAIN]

    for meta in records:
        # Verified load through the REAL store path (checksum recomputed), then a keyless
        # deterministic replay through a fresh engine.
        events = store.load_events(meta["id"])
        assert len(events) == meta["event_counts"]["total"] > 0
        first = list(store.replay(meta["id"], CONFIG))
        second = list(store.replay(meta["id"], CONFIG))
        assert first == second and len(first) == len(events)
        assert first[-1].tape_state in (
            "buyer_control",
            "seller_control",
            "bid_absorption",
            "ask_absorption",
            "unclear",
        )
        assert meta["symbol"] == "PG"
        assert meta["data_feed"] == CONFIG.historical_feed


def test_committed_fixture_pair_windows_are_disjoint():
    # Train and holdout must never overlap — nothing is ever judged on the data it was tuned on.
    store = DatasetStore(FIXTURE_DATASET_DIR)
    records, _errors = store.list()
    by_split = {r["split"]: r for r in records}
    train, holdout = by_split[SPLIT_TRAIN], by_split[SPLIT_HOLDOUT]
    assert (
        train["window_end_utc"] <= holdout["window_start_utc"]
        or holdout["window_end_utc"] <= train["window_start_utc"]
    )
    assert train["checksum"] != holdout["checksum"]


# --- era-fast_wall J-02: the metadata-only stat-keyed verified cache ------------------------------


def _age(path: Path, seconds: float = 5.0) -> None:
    """Backdates a file's mtime past the ~2s racy-write guard window, so a test can
    deterministically exercise the WARM-cache path without a real sleep (the ``test_bars.py``
    identical helper)."""
    past = time.time() - seconds
    os.utime(path, (past, past))


def _spy_on_load(monkeypatch):
    """Installs a counting spy around ``DatasetStore._load`` (the ONE full verifier) and returns
    the call-count list — the ``test_bars.py``/``test_setups.py`` identical technique."""
    import app.research.datasets as datasets_module

    calls: list[int] = []
    real_load = datasets_module.DatasetStore._load

    def _counting_load(self, path):
        calls.append(1)
        return real_load(self, path)

    monkeypatch.setattr(datasets_module.DatasetStore, "_load", _counting_load)
    return calls


def test_list_surfaces_a_tampered_file_as_an_error_after_a_warm_read(tmp_path):
    """TC-4."""
    store = DatasetStore(tmp_path / "datasets")
    meta = _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)
    path = tmp_path / "datasets" / f"{meta['id']}.json"
    _age(path)

    warm_records, warm_errors = store.list()
    assert warm_errors == []
    assert warm_records[0]["id"] == meta["id"]

    def _corrupt(data):
        for row in data["record"]["events"]:
            if row["type"] == "trade":
                row["price"] += 1.0
                return

    _tamper(path, _corrupt)

    records, errors = store.list()
    assert records == [], "the tampered dataset must never be served as healthy metadata"
    assert len(errors) == 1 and f"{meta['id']}.json" in errors[0]["file"]


def test_racy_write_guard_refuses_to_cache_a_freshly_recorded_dataset(tmp_path, monkeypatch):
    """TC-5 (datasets leg)."""
    store = DatasetStore(tmp_path / "datasets")
    calls = _spy_on_load(monkeypatch)

    meta = _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)  # freshly written
    store.get(meta["id"])
    assert len(calls) == 1

    store.get(meta["id"])  # still inside the ~2s racy window
    assert len(calls) == 2, "the racy-write guard must refuse to cache a just-written file"


def test_load_events_and_replay_fully_reverify_even_when_the_metadata_cache_is_warm(tmp_path, monkeypatch):
    """TC-7 — the mechanical proof of the critical "verification trust boundary never weakens"
    anti-goal: ``load_events``/``replay`` must fully re-verify on every call, even once
    ``get``/``list`` have warm-cached this exact dataset's metadata."""
    store = DatasetStore(tmp_path / "datasets")
    meta = _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)
    path = tmp_path / "datasets" / f"{meta['id']}.json"
    _age(path)

    store.get(meta["id"])  # warm the metadata cache
    store.list()

    calls = _spy_on_load(monkeypatch)  # installed AFTER warming -- isolates what happens next

    events = store.load_events(meta["id"])
    assert len(events) == meta["event_counts"]["total"] > 0
    assert len(calls) == 1, "load_events must fully re-verify even with a warm metadata cache"

    list(store.replay(meta["id"], CONFIG))
    assert len(calls) == 2, "replay must fully re-verify even with a warm metadata cache"


def test_get_and_list_return_event_counts_copies_a_caller_mutation_never_poisons_the_cache(tmp_path):
    """Extends ``test_bars.py``'s TC-6 per-row-copy discipline to this store's one nested
    mutable metadata field (``event_counts``) — not itself a numbered TC, but the identical
    caller-mutation hazard the new cache introduces for this store too."""
    store = DatasetStore(tmp_path / "datasets")
    meta = _record_reference(store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)
    _age(tmp_path / "datasets" / f"{meta['id']}.json")

    fetched = store.get(meta["id"])
    original_total = fetched["event_counts"]["total"]
    fetched["event_counts"]["total"] = -999  # caller mutation, in place

    again = store.get(meta["id"])  # a warm-cache hit
    assert again["event_counts"]["total"] == original_total

    records, _errors = store.list()
    listed = next(r for r in records if r["id"] == meta["id"])
    assert listed["event_counts"]["total"] == original_total


# --- config: the dataset dir is operational, never a fingerprint input ----------------------------


def test_dataset_dir_is_excluded_from_config_fingerprint():
    # The journal_db_path precedent: where datasets are STORED cannot affect any research value,
    # so two configs differing only in dataset_dir MUST share a fingerprint...
    assert Config(dataset_dir="/somewhere/else").config_fingerprint() == CONFIG.config_fingerprint()
    # ...while a real classifier threshold still moves it (the counter-test).
    assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()


def test_dataset_dir_env_override_wins(monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", "/operator/override")
    assert CONFIG.dataset_dir_resolved() == "/operator/override"
    monkeypatch.delenv("TAPEOLOGY_DATASET_DIR")
    default = CONFIG.dataset_dir_resolved()
    assert default.endswith(str(Path(".data") / "datasets"))


# --- era "The Rapid Microscope" J-06 step 1 (spec section 7.1/2.6 r2): the Card-5.1 data- -------
# --- preservation prerequisite -- TC-1, TC-2, TC-3, TC-9 (docs/phases/goal-rapid-microscope- -----
# --- iter-7.md). This is the era's most dangerous change so far (iteration-6 evaluator's own -----
# --- words): it mutates the shared event/row schema every dataset-reading journey depends on. ---


def test_tc1_an_event_with_every_new_field_absent_serializes_to_the_pre_change_row_shape(tmp_path):
    """TC-1 (backward compatibility, the narrow risk surface): an event built the way EVERY call
    site built one before this iteration (every Card-5.1 field left at its default ``None``)
    must serialize to the EXACT same row shape legacy data already has on disk -- no
    ``conditions``/``exchange``/``tape``/``trade_id`` key on a trade row, no
    ``conditions``/``tape``/``bid_exchange``/``ask_exchange`` key on a quote row, and no
    ``schema_basis``/``quote_size_unit`` key in the manifest -- ever appearing for an absent
    value. Reloading must reconstruct byte-identical events (the ``_row_to_event`` half of the
    same round trip the 18 real on-disk datasets exercise)."""
    store = DatasetStore(tmp_path / "datasets")
    events = [
        QuoteEvent("PG", 0.0, 148.49, 148.53, 700, 100),
        TradeEvent("PG", 0.02, 148.53, 100, Side.UNKNOWN),
    ]
    meta = store.record(
        symbol="PG", source="test", source_kind="reference", source_id="",
        split=SPLIT_TRAIN, window_start_utc="2026-06-09T17:00:00Z",
        window_end_utc="2026-06-09T17:00:01Z", data_feed="sip", epoch_anchor=0.0, events=events,
    )
    assert "schema_basis" not in meta
    assert "quote_size_unit" not in meta

    on_disk = json.loads((tmp_path / "datasets" / f"{meta['id']}.json").read_text())
    rows = on_disk["record"]["events"]
    trade_row = next(r for r in rows if r["type"] == "trade")
    quote_row = next(r for r in rows if r["type"] == "quote")
    for key in ("conditions", "exchange", "tape", "trade_id"):
        assert key not in trade_row, f"trade row unexpectedly carries {key!r} for an absent value"
    for key in ("conditions", "tape", "bid_exchange", "ask_exchange"):
        assert key not in quote_row, f"quote row unexpectedly carries {key!r} for an absent value"

    assert store.load_events(meta["id"]) == events


def test_tc2_preservation_fields_round_trip_exactly_through_record_and_load_events(tmp_path):
    """TC-2: a freshly constructed TradeEvent/QuoteEvent carrying real preservation values
    round-trips through ``record()`` -> ``load_events()`` with every field equal to the
    original."""
    store = DatasetStore(tmp_path / "datasets")
    trade = TradeEvent(
        "PG", 0.02, 148.53, 100, Side.UNKNOWN,
        conditions=["@", "I"], exchange="Q", tape="C", trade_id=123456789,
    )
    quote = QuoteEvent(
        "PG", 0.0, 148.49, 148.53, 700, 100,
        conditions=["R"], tape="C", bid_exchange="P", ask_exchange="Q",
    )
    meta = store.record(
        symbol="PG", source="test", source_kind="reference", source_id="",
        split=SPLIT_TRAIN, window_start_utc="2026-06-09T17:00:00Z",
        window_end_utc="2026-06-09T17:00:01Z", data_feed="sip", epoch_anchor=0.0,
        events=[quote, trade],
    )
    reloaded = store.load_events(meta["id"])
    reloaded_trade = next(e for e in reloaded if isinstance(e, TradeEvent))
    reloaded_quote = next(e for e in reloaded if isinstance(e, QuoteEvent))
    assert reloaded_trade == trade
    assert reloaded_quote == quote


def test_the_frozen_split_guard_still_refuses_one_tape_re_fetched_with_preservation_fields(tmp_path):
    """iter-7 audit finding B1 (regression guard). This module's own docstring makes ONE promise
    the whole split discipline rests on: "re-recording the same tape under a different split (the
    re-tag attempt) ... raises the 409-style ``DatasetAlreadyRegistered``". That guard is enforced
    SOLELY by comparing ``_content_checksum``, so the Card-5.1 preservation fields must never
    enter it: otherwise a window recorded BEFORE those fields existed (all 18 real on-disk tick
    datasets) could be re-fetched through the now-populating Alpaca adapter and registered a
    SECOND time under a DIFFERENT split — one tape in both ``train`` and ``holdout``, which is
    train/holdout contamination, not a duplicate.

    The two event lists below are the SAME tape: identical timestamps, prices, sizes and sides;
    the second merely preserves the immutable vendor identifiers Alpaca always returned."""
    store = DatasetStore(tmp_path / "datasets")
    common = dict(
        symbol="AAPL", source="alpaca", source_kind="historical", source_id="AAPL",
        window_start_utc="2026-06-22T17:00:00Z", window_end_utc="2026-06-22T17:10:00Z",
        data_feed="sip", epoch_anchor=1000.0,
    )
    legacy = [
        QuoteEvent("AAPL", 0.0, 100.0, 100.1, 5, 7),
        TradeEvent("AAPL", 0.5, 100.05, 300, Side.BUY),
    ]
    preserved = [
        QuoteEvent("AAPL", 0.0, 100.0, 100.1, 5, 7,
                   conditions=["R"], tape="C", bid_exchange="P", ask_exchange="Q"),
        TradeEvent("AAPL", 0.5, 100.05, 300, Side.BUY,
                   conditions=["@", "I"], exchange="Q", tape="C", trade_id=987654321),
    ]

    first = store.record(split=SPLIT_TRAIN, events=legacy, **common)
    with pytest.raises(DatasetAlreadyRegistered) as exc_info:
        store.record(split=SPLIT_HOLDOUT, events=preserved, **common)
    assert first["id"] in str(exc_info.value)
    assert SPLIT_TRAIN in str(exc_info.value)
    metas, errors = store.list()
    assert errors == []
    assert [m["split"] for m in metas] == [SPLIT_TRAIN], "one tape must never hold two split tags"

    # ...and the reverse order refuses too: the tape's identity does not depend on which shape
    # happened to be recorded first.
    other = DatasetStore(tmp_path / "datasets2")
    rich = other.record(split=SPLIT_HOLDOUT, events=preserved, **common)
    with pytest.raises(DatasetAlreadyRegistered):
        other.record(split=SPLIT_TRAIN, events=legacy, **common)
    # The preservation values themselves still survive the round trip untouched — the checksum
    # ignores them, the STORED ROWS keep them verbatim (TC-2's contract, re-asserted here so a
    # future "just strip them everywhere" shortcut cannot pass this test).
    assert other.load_events(rich["id"]) == preserved


def test_tc3_schema_basis_and_quote_size_unit_are_stamped_verbatim_when_supplied(tmp_path):
    """TC-3: ``record(..., schema_basis=..., quote_size_unit=...)`` stamps both into the manifest
    verbatim and they survive a store reload; an unrecognised ``quote_size_unit`` (outside
    ``micro_features.QUOTE_SIZE_UNITS``) is rejected explicitly, never silently accepted."""
    store = DatasetStore(tmp_path / "datasets")
    meta = store.record(
        symbol="PG", source="test", source_kind="reference", source_id="",
        split=SPLIT_TRAIN, window_start_utc="2026-06-09T17:00:00Z",
        window_end_utc="2026-06-09T17:00:01Z", data_feed="sip", epoch_anchor=0.0,
        events=[TradeEvent("PG", 0.0, 148.53, 100, Side.UNKNOWN)],
        schema_basis="v2_preservation", quote_size_unit="shares",
    )
    assert meta["schema_basis"] == "v2_preservation"
    assert meta["quote_size_unit"] == "shares"

    reloaded = DatasetStore(tmp_path / "datasets").get(meta["id"])
    assert reloaded["schema_basis"] == "v2_preservation"
    assert reloaded["quote_size_unit"] == "shares"

    with pytest.raises(ValueError):
        store.record(
            symbol="PG", source="test2", source_kind="reference", source_id="",
            split=SPLIT_TRAIN, window_start_utc="2026-06-09T17:01:00Z",
            window_end_utc="2026-06-09T17:01:01Z", data_feed="sip", epoch_anchor=0.0,
            events=[TradeEvent("PG", 0.0, 149.0, 50, Side.UNKNOWN)],
            quote_size_unit="not-a-real-unit",
        )


def test_tc9_the_dated_rule_constant_lives_exactly_once_in_tick_recorder_never_duplicated():
    """TC-9 (iter-7) updated to its own anticipated iter-8 shape, not silently dropped:
    ``micro_features.QUOTE_SIZE_UNITS`` stays the SOLE unit-vocabulary tuple in the repo (this
    module validates against it, never defines a second copy). ``ALPACA_QUOTE_SIZE_UNIT_
    EFFECTIVE`` -- the dated-vendor-rule constant the assumption ledger's iter-7 entry explicitly
    reserved for a future ``tick_recorder.py`` -- now lives EXACTLY there (iter-8, J-06 step 2,
    closing that reservation) and NOWHERE else; a second, independently-valued copy anywhere
    (including a second one inside ``tick_recorder.py`` itself) still fails this test."""
    app_dir = Path(__file__).resolve().parents[1] / "app"
    effective_locations: list[str] = []
    offending_second_tuple: list[str] = []
    py_files = sorted(p for p in app_dir.rglob("*.py") if "__pycache__" not in p.parts)
    assert len(py_files) > 50, f"only {len(py_files)} app modules scanned -- has the tree moved?"
    for path in py_files:
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                targets = [node.target.id]
            else:
                continue
            if "ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE" in targets:
                effective_locations.append(str(path.relative_to(app_dir)))
            if "QUOTE_SIZE_UNITS" in targets and path.name != "micro_features.py":
                offending_second_tuple.append(str(path.relative_to(app_dir)))
    assert effective_locations == ["research/tick_recorder.py"], (
        "ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE must be defined exactly once, in tick_recorder.py "
        f"(the module micro_features.py's own docstring reserves it for): found at {effective_locations}"
    )
    assert offending_second_tuple == [], f"a second QUOTE_SIZE_UNITS assignment exists: {offending_second_tuple}"
