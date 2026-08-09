"""``desk_screen.py`` (Era B "The Desk", J-03) — the screen-snapshot store discipline, the
``bar_store_signature`` index-only derivation (T-4/TC-15), best-band selection + ``distance_bps``,
and the row-computation function (``compute_screen``) against the REAL committed fixture universe
(103 members) and the real AAPL/MSFT bar fixtures — never a synthetic ``AAA...EEE`` stand-in for
any clause naming real symbols (lessons.md iter-2). Compute-manager/route/CLI coverage lives in
``test_desk_screen_compute.py``.
"""

from __future__ import annotations

import json
import shutil
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.config import CONFIG
from app.providers.adapters.base import RawBar
from app.providers.base import Side, TradeEvent
from app.research.bar_index import BarIndex
from app.research.bars import BarStore
from app.research.datasets import SPLIT_TRAIN, DatasetStore
from app.research.desk_coverage import get_desk_coverage
from app.research.desk_screen import (
    ScreenAlreadyRecorded,
    ScreenIntegrityError,
    ScreenStore,
    compute_bar_store_signature,
    compute_screen,
    resolve_desk_screen_dir,
    screen_as_of,
)
from app.research.desk_screen import (
    _bands_by_class,
    _basis_age_days,
    _distance_bps,
    _epoch,
    _row_rank_key,
    _select_best_band,
    _select_opposite_band,
)
from app.research.desk_universe import UniverseStore

FIXTURE_UNIVERSE_DIR = Path(__file__).parent / "fixtures" / "universe"
REGISTERED_SNAPSHOT_PATH = FIXTURE_UNIVERSE_DIR / "universe-2026-07-25-817cc184bbb3.json"
FIXTURE_YAHOO_DIR = Path(__file__).parent / "fixtures" / "yahoo"

AAPL_DAILY_FIXTURE = "AAPL_1d_20260101_20260626.json"
MSFT_DAILY_FIXTURE = "MSFT_1d_20260101_20260626.json"
MSFT_HOURLY_FIXTURE = "MSFT_1h_20260601_20260618.json"

# The pinned session goal.md's J-01/J-05/J-07 acceptance text already names (test_tradability.py's
# own golden: as_of="2026-06-22T15:00:00Z" resolves basis_as_of="2026-06-18T04:00:00.000000Z") --
# any as_of inside this same UTC calendar day resolves the identical basis (T-6), so this is a
# zero-new-fixture-risk screen_date.
SCREEN_DATE = "2026-06-22"

# The goal.md build-anchors' own 11 recorded dataset symbols. SPY is in this list but is NOT an
# S&P 100 constituent (it is the index-tracking ETF, never a member of the index itself) -- so it
# never appears in the fixture universe's `rows`/`skipped` and its tick_evidence is never asserted.
DATASET_SYMBOLS = (
    "AAPL", "AMD", "AMZN", "GOOGL", "META", "MSFT", "NFLX", "NVDA", "PG", "SPY", "TSLA",
)


def _load_yahoo_fixture(name: str) -> dict:
    return json.loads((FIXTURE_YAHOO_DIR / name).read_text())


def _seed_yahoo_fixture(bar_store: BarStore, bar_index: BarIndex, fixture: dict) -> None:
    bars = [
        RawBar(
            fixture["symbol"], fixture["timeframe"], b["epoch"],
            b["open"], b["high"], b["low"], b["close"], b["volume"],
        )
        for b in fixture["bars"]
    ]
    meta = bar_store.record(
        symbol=fixture["symbol"], timeframe=fixture["timeframe"],
        window_start_utc=fixture["start"], window_end_utc=fixture["end"],
        feed="yahoo", bars=bars,
    )
    bar_index.insert(meta)


def _register_fixture_universe(universe_dir: Path) -> UniverseStore:
    """"The fixture universe" (J-01's own naming): the REAL committed 103-member snapshot, copied
    into a temp universe dir exactly as ``test_desk_universe.py``'s
    ``test_the_committed_fixture_snapshot_loads_cleanly_through_the_store`` does."""
    universe_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REGISTERED_SNAPSHOT_PATH, universe_dir / REGISTERED_SNAPSHOT_PATH.name)
    return UniverseStore(universe_dir)


def _register_dataset(dataset_store: DatasetStore, symbol: str) -> None:
    """A minimal, single-trade synthetic dataset registration -- proves ONLY that ``symbol`` is a
    presence in the dataset store (the tick-evidence badge's own honest contract), never a claim
    about real tick content."""
    dataset_store.record(
        symbol=symbol, source=f"synthetic {symbol}", source_kind="reference", source_id=symbol,
        split=SPLIT_TRAIN, window_start_utc="2026-01-02T14:30:00Z", window_end_utc="2026-01-02T14:30:01Z",
        data_feed="sim", epoch_anchor=None,
        events=[TradeEvent(symbol, 0.0, 100.0, 100, Side.UNKNOWN)],
    )


@pytest.fixture
def ctx(tmp_path):
    """A fully-scoped desk context: the real fixture universe + empty bar/dataset stores, all
    rooted under ``tmp_path`` -- never the ambient real ``.data/`` tree."""
    universe_store = _register_fixture_universe(tmp_path / "universe")
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "index.db"))
    dataset_store = DatasetStore(tmp_path / "datasets")
    return universe_store, bar_store, bar_index, dataset_store


# ==================================================================================================
# as_of translation (T-6)
# ==================================================================================================


def test_screen_as_of_is_a_pure_function_of_screen_date():
    assert screen_as_of("2026-06-22") == "2026-06-22T23:59:59Z"
    assert screen_as_of("2026-01-01") == "2026-01-01T23:59:59Z"


# ==================================================================================================
# bar_store_signature (T-4, TC-15)
# ==================================================================================================


def test_bar_store_signature_issues_zero_bar_store_calls(ctx, monkeypatch):
    """T-4/TC-15: instrumented exactly like ``test_desk_coverage.py``'s
    ``test_coverage_issues_zero_bar_store_calls`` -- derivation goes entirely through
    ``desk_coverage.get_desk_coverage`` (index-only), never a ``BarStore`` read."""
    universe_store, bar_store, bar_index, _dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))

    calls: list[str] = []
    original_list = BarStore.list
    original_get = BarStore.get

    def _tracked_list(self, *args, **kwargs):
        calls.append("list")
        return original_list(self, *args, **kwargs)

    def _tracked_get(self, *args, **kwargs):
        calls.append("get")
        return original_get(self, *args, **kwargs)

    monkeypatch.setattr(BarStore, "list", _tracked_list)
    monkeypatch.setattr(BarStore, "get", _tracked_get)

    signature = compute_bar_store_signature(universe_store, bar_index)

    assert calls == []
    assert isinstance(signature, str) and len(signature) == 16


def test_bar_store_signature_changes_when_coverage_changes(ctx):
    universe_store, bar_store, bar_index, _dataset_store = ctx
    before = compute_bar_store_signature(universe_store, bar_index)

    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    after = compute_bar_store_signature(universe_store, bar_index)

    assert before != after


def test_bar_store_signature_is_deterministic_across_fresh_instances(ctx):
    universe_store, bar_store, bar_index, _dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))

    first = compute_bar_store_signature(universe_store, bar_index)
    second = compute_bar_store_signature(UniverseStore(universe_store.root), BarIndex(bar_index.db_path))
    assert first == second


# ==================================================================================================
# best-band selection + distance_bps (assumptions.md iter-3 entry 1) -- pure-function unit tests
# ==================================================================================================


def _band(
    side: str, price_low: float, price_high: float, band_class: str | None, quality: float,
    *, members: list[dict] | None = None, round_number: bool = False,
) -> dict:
    """A minimal band dict carrying every key `_select_best_band`/`_select_opposite_band`/the row
    builder read. `members` defaults to a single synthetic `1d` level at `price_low` (goal-desk-
    iter-23, J-15) -- an honest, valid single-member band -- so every EXISTING call site (none of
    which cares about wall-composition) keeps working unchanged; `member_count` is ALWAYS
    `len(members)`, mirroring `tradability.py`'s own `_band`, which never lets the two diverge."""
    if members is None:
        members = [{"price": price_low, "timeframe": "1d", "type": "level", "touch_count": 1}]
    return {
        "side": side, "price_low": price_low, "price_high": price_high, "class": band_class,
        "quality_score": quality, "member_count": len(members), "round_number": round_number,
        "members": members,
    }


def test_distance_bps_resistance_uses_the_low_edge():
    band = _band("resistance", 101.0, 102.0, "A", 10.0)
    assert _distance_bps(band, 100.0) == pytest.approx((101.0 - 100.0) / 100.0 * 10_000.0)


def test_distance_bps_support_uses_the_high_edge():
    band = _band("support", 98.0, 99.0, "A", 10.0)
    assert _distance_bps(band, 100.0) == pytest.approx((100.0 - 99.0) / 100.0 * 10_000.0)


def test_select_best_band_prefers_higher_class_over_closer_distance():
    close_but_low_class = _band("resistance", 100.1, 100.2, "C", 500.0)
    far_but_high_class = _band("resistance", 110.0, 111.0, "A", 1.0)
    best = _select_best_band([close_but_low_class, far_but_high_class], 100.0)
    assert best is far_but_high_class


def test_select_best_band_ties_on_class_prefer_closer_distance():
    near = _band("resistance", 100.5, 100.6, "B", 1.0)
    far = _band("resistance", 120.0, 121.0, "B", 999.0)
    best = _select_best_band([far, near], 100.0)
    assert best is near


def test_select_best_band_ties_on_class_and_distance_prefer_higher_quality():
    a = _band("resistance", 105.0, 105.0, "B", 5.0)
    b = _band("resistance", 105.0, 105.0, "B", 50.0)
    best = _select_best_band([a, b], 100.0)
    assert best is b


def test_select_best_band_exact_tie_keeps_the_served_order_first_item():
    a = _band("resistance", 105.0, 105.0, "B", 5.0)
    b = _band("resistance", 105.0, 105.0, "B", 5.0)
    assert _select_best_band([a, b], 100.0) is a
    assert _select_best_band([b, a], 100.0) is b


def test_select_best_band_null_class_ranks_below_every_graded_class():
    graded = _band("resistance", 200.0, 201.0, "C", 1.0)
    ungraded_and_closer = _band("resistance", 100.1, 100.2, None, 999.0)
    best = _select_best_band([graded, ungraded_and_closer], 100.0)
    assert best is graded


# ==================================================================================================
# opposite-band selection + bands-by-class count (goal-desk-iter-18, J-14) -- pure-function unit
# tests, mirroring the best-band-selection suite immediately above.
# ==================================================================================================


def test_select_opposite_band_returns_the_nearest_band_on_the_other_side():
    best_side = _band("resistance", 105.0, 106.0, "A", 1.0)
    near_opposite = _band("support", 99.0, 99.5, "B", 5.0)
    far_opposite = _band("support", 80.0, 81.0, "B", 5.0)
    opposite = _select_opposite_band([best_side, near_opposite, far_opposite], 100.0, "resistance")
    assert opposite is near_opposite


def test_select_opposite_band_is_null_when_no_band_exists_on_the_other_side():
    """TC-8: an honest ``None`` -- never an invented or wrong-side band -- when every served band
    shares the SAME side as the row's own selected ``best`` band."""
    resistance_only = [
        _band("resistance", 101.0, 102.0, "A", 10.0),
        _band("resistance", 110.0, 111.0, "B", 1.0),
    ]
    assert _select_opposite_band(resistance_only, 100.0, "resistance") is None


def test_select_opposite_band_prefers_closer_distance_over_higher_class():
    """TC-1 (goal-desk-iter-19 correction): the opposite selection uses its OWN distance-first
    tie-break tuple -- distinct from `_select_best_band`'s class-first tuple, which governs only
    the row's own same-side selection (`test_select_best_band_prefers_higher_class_over_closer_
    distance` above, unchanged). goal.md J-14 step 1: "distance ascending, then class rank
    descending... then band_score descending" -- a close-but-lower-class opposite-side band beats a
    farther-but-higher-class one."""
    best_side = _band("resistance", 105.0, 106.0, "A", 1.0)
    close_but_low_class = _band("support", 99.9, 99.95, "C", 500.0)
    far_but_high_class = _band("support", 90.0, 91.0, "A", 1.0)
    opposite = _select_opposite_band(
        [best_side, close_but_low_class, far_but_high_class], 100.0, "resistance"
    )
    assert opposite is close_but_low_class


def test_select_opposite_band_exact_tie_keeps_the_served_order_first_item():
    """TC-9: tie-break stability across repeated calls on a tied fixture -- `min`'s own
    first-of-tie order (never a second, invented tie-break), mirroring
    `test_select_best_band_exact_tie_keeps_the_served_order_first_item` for the opposite side."""
    best_side = _band("resistance", 105.0, 106.0, "A", 1.0)
    a = _band("support", 99.0, 99.0, "B", 5.0)
    b = _band("support", 99.0, 99.0, "B", 5.0)
    assert _select_opposite_band([best_side, a, b], 100.0, "resistance") is a
    assert _select_opposite_band([best_side, b, a], 100.0, "resistance") is b
    # Repeated calls on the identical input return the identical result every time.
    assert _select_opposite_band([best_side, a, b], 100.0, "resistance") is a
    assert _select_opposite_band([best_side, a, b], 100.0, "resistance") is a


def test_bands_by_class_counts_each_class_including_zero_and_unclassified():
    bands = [
        _band("resistance", 105.0, 106.0, "A", 1.0),
        _band("resistance", 110.0, 111.0, "A", 1.0),
        _band("support", 90.0, 91.0, None, 1.0),
    ]
    assert _bands_by_class(bands) == {"A": 2, "B": 0, "C": 0, "unclassified": 1}


def test_bands_by_class_empty_list_is_all_zero():
    assert _bands_by_class([]) == {"A": 0, "B": 0, "C": 0, "unclassified": 0}


# ==================================================================================================
# ScreenStore discipline -- mirrors test_desk_universe.py's store-level suite exactly
# ==================================================================================================


def _record(store: ScreenStore, **overrides) -> dict:
    defaults = dict(
        screen_date="2026-06-22", as_of="2026-06-22T23:59:59Z",
        universe_snapshot_id="universe-2026-07-25-817cc184bbb3",
        config_fingerprint=CONFIG.config_fingerprint(), bar_store_signature="deadbeef00000000",
        rows=[{"symbol": "AAPL", "side": "resistance", "band_class": "C", "distance_bps": 1.0,
               "band_score": 2.0, "price_low": 100.0, "price_high": 101.0,
               "coverage": {}, "tick_evidence": True}],
        skipped=[{"symbol": "ABBV", "skipped": True, "reason": "no_bars", "coverage": {}, "tick_evidence": False}],
    )
    defaults.update(overrides)
    return store.record(**defaults)


def test_record_stores_the_exact_5pin_key_and_content(tmp_path):
    store = ScreenStore(tmp_path / "screen")
    meta = _record(store)

    assert meta["id"].startswith("screen-2026-06-22-")
    checksum_suffix = meta["id"].removeprefix("screen-2026-06-22-")
    assert len(checksum_suffix) == 12
    int(checksum_suffix, 16)  # hex, or this raises
    assert meta["screen_date"] == "2026-06-22"
    assert meta["as_of"] == "2026-06-22T23:59:59Z"
    assert meta["universe_snapshot_id"] == "universe-2026-07-25-817cc184bbb3"
    assert meta["config_fingerprint"] == CONFIG.config_fingerprint()
    assert meta["bar_store_signature"] == "deadbeef00000000"
    assert meta["created_utc"].endswith("Z")
    assert len(meta["rows"]) == 1 and len(meta["skipped"]) == 1
    assert len(list((tmp_path / "screen").glob("*.json"))) == 1


def test_list_serves_the_stored_record_verbatim_oldest_first(tmp_path):
    store = ScreenStore(tmp_path / "screen")
    recorded = _record(store)

    records, errors = store.list()
    assert errors == []
    assert len(records) == 1
    assert records[0] == recorded


def test_store_survives_a_reload_from_disk(tmp_path):
    root = tmp_path / "screen"
    recorded = _record(ScreenStore(root))

    reloaded = ScreenStore(root)
    records, errors = reloaded.list()
    assert errors == [] and records == [recorded]


def test_empty_store_lists_nothing(tmp_path):
    store = ScreenStore(tmp_path / "screen")
    records, errors = store.list()
    assert records == [] and errors == []


# --- append-only refusal on an identical 5-pin key (TC-4, store level) --------------------------


def test_rerecording_an_identical_key_is_refused(tmp_path):
    store = ScreenStore(tmp_path / "screen")
    first = _record(store)

    with pytest.raises(ScreenAlreadyRecorded) as excinfo:
        _record(store)
    assert excinfo.value.existing_id == first["id"]
    assert len(list((tmp_path / "screen").glob("*.json"))) == 1  # no second file


def test_rerecording_an_identical_key_leaves_the_file_byte_unchanged(tmp_path):
    screen_dir = tmp_path / "screen"
    store = ScreenStore(screen_dir)
    _record(store)
    path = next(screen_dir.glob("*.json"))
    before = path.read_bytes()

    with pytest.raises(ScreenAlreadyRecorded):
        _record(store)
    assert path.read_bytes() == before


def test_rerecording_the_same_key_with_different_row_content_is_still_refused(tmp_path):
    """The dedup key is the 5 PINS, never the row content -- two calls sharing the same key but
    carrying different (e.g. accidentally miscomputed) row content still collide, exactly as
    intended (the row content is a deterministic function of the pins, so this can only diverge
    on a genuine bug, and the store must refuse regardless)."""
    store = ScreenStore(tmp_path / "screen")
    first = _record(store)

    with pytest.raises(ScreenAlreadyRecorded) as excinfo:
        _record(store, rows=[], skipped=[])
    assert excinfo.value.existing_id == first["id"]


def test_a_different_key_registers_a_second_distinct_snapshot(tmp_path):
    store = ScreenStore(tmp_path / "screen")
    first = _record(store, screen_date="2026-06-22")
    second = _record(store, screen_date="2026-06-23", as_of="2026-06-23T23:59:59Z")

    assert first["id"] != second["id"]
    records, errors = store.list()
    assert errors == []
    assert {r["id"] for r in records} == {first["id"], second["id"]}


def test_find_by_key_returns_none_when_nothing_matches(tmp_path):
    store = ScreenStore(tmp_path / "screen")
    _record(store)
    assert store.find_by_key("2099-01-01", "2099-01-01T23:59:59Z", "x", "y", "z") is None


def test_find_by_key_returns_the_exact_match(tmp_path):
    store = ScreenStore(tmp_path / "screen")
    recorded = _record(store)
    found = store.find_by_key(
        "2026-06-22", "2026-06-22T23:59:59Z", "universe-2026-07-25-817cc184bbb3",
        CONFIG.config_fingerprint(), "deadbeef00000000",
    )
    assert found == recorded


# --- integrity: a corrupted file is explicit, never silent --------------------------------------


def test_corrupted_snapshot_file_surfaces_explicitly_in_list_errors(tmp_path):
    screen_dir = tmp_path / "screen"
    store = ScreenStore(screen_dir)
    _record(store)
    path = next(screen_dir.glob("*.json"))
    data = json.loads(path.read_text())
    data["record"]["meta"]["screen_date"] = "2099-12-31"  # tamper -- file_checksum now disagrees
    path.write_text(json.dumps(data))

    records, errors = store.list()
    assert records == []
    assert len(errors) == 1
    assert errors[0]["file"] == path.name
    assert "integrity" in errors[0]["error"]


def test_recording_over_a_corrupted_file_at_the_same_key_is_refused_never_a_silent_overwrite(tmp_path):
    """A tampered snapshot is withheld from ``records`` (and reported in ``integrity_errors``), so
    ``find_by_key`` cannot see it -- but the snapshot's PATH is a pure function of the 5-pin key, so
    a re-record for that same key lands on the SAME file. ``record`` must refuse explicitly: never
    overwrite a damaged snapshot (that is a rewrite -- "snapshots are append-only ... never
    rewritten"), and never erase the integrity error the store was honestly surfacing."""
    screen_dir = tmp_path / "screen"
    store = ScreenStore(screen_dir)
    _record(store)
    path = next(screen_dir.glob("*.json"))
    data = json.loads(path.read_text())
    data["record"]["meta"]["rows"] = [{"symbol": "AAPL", "band_class": "TAMPERED"}]
    path.write_text(json.dumps(data))
    tampered_bytes = path.read_bytes()

    with pytest.raises(ScreenIntegrityError) as excinfo:
        _record(store)
    assert path.name in str(excinfo.value)

    assert path.read_bytes() == tampered_bytes, "the damaged file must be left exactly as found"
    records, errors = store.list()
    assert records == []
    assert [e["file"] for e in errors] == [path.name], "the integrity error must still be surfaced"
    assert len(list(screen_dir.glob("*.json"))) == 1, "and no second file may be written either"


def test_load_raises_screen_integrity_error_for_unparseable_json(tmp_path):
    screen_dir = tmp_path / "screen"
    screen_dir.mkdir(parents=True)
    (screen_dir / "screen-2026-01-01-deadbeef0000.json").write_text("{not json")

    store = ScreenStore(screen_dir)
    records, errors = store.list()
    assert records == [] and len(errors) == 1


def test_store_has_no_in_place_rewrite_and_exactly_two_removal_paths():
    """Immutability is structural, not policed (mirrors ``test_desk_universe.py``'s own docstring
    discipline). A recorded file is still NEVER rewritten in place (``record`` only ever creates);
    what has narrowed twice is which removals are allowed:

    * ``prune_superseded`` -- the automatic one the compute path runs, which structurally cannot
      leave a date with nothing (one snapshot per date);
    * ``prune_dates`` -- the operator one, and the only method that CAN empty a date. It exists for
      snapshots recorded for dates that never traded, which no supersede can replace because there
      is no correct snapshot for such a date to be replaced WITH. Nothing in the compute path calls
      it; its only caller is ``desk_screen_cleanup``'s dry-run-by-default ``--non-sessions`` mode.

    This pins the exact public surface: any NEW mutating method has to come here and justify
    itself."""
    public_methods = {name for name in dir(ScreenStore) if not name.startswith("_")}
    assert public_methods == {
        "root", "list", "find_by_key", "find_by_date", "record",
        "prune_superseded", "prune_dates",
    }


def test_prune_dates_removes_a_dates_last_copy_and_touches_no_other_date(tmp_path):
    """The property that separates it from ``prune_superseded``: it empties a date. Scoped exactly
    -- another date's snapshot is never in the blast radius, and a date not named is untouched."""
    store, earlier, later = _plant_same_date_pair(tmp_path / "screen")
    other_date = _record(
        store, screen_date="2026-07-28", as_of="2026-07-28T23:59:59Z",
        bar_store_signature="c" * 16,
    )
    survivor_bytes = (store.root / f"{other_date['id']}.json").read_bytes()

    removed = store.prune_dates({earlier["screen_date"]})

    assert sorted(removed) == sorted([earlier["id"], later["id"]])
    records, errors = store.list()
    assert errors == []
    assert [r["id"] for r in records] == [other_date["id"]]
    assert (store.root / f"{other_date['id']}.json").read_bytes() == survivor_bytes


def test_prune_dates_on_a_date_holding_nothing_is_a_silent_no_op(tmp_path):
    store, earlier, _later = _plant_same_date_pair(tmp_path / "screen")

    assert store.prune_dates({"2099-01-01"}) == []
    assert store.prune_dates(frozenset()) == []
    records, _errors = store.list()
    assert len(records) == 2


def test_prune_superseded_removes_only_the_other_copies_of_that_date(tmp_path):
    """The removal path, exactly scoped: every OTHER snapshot for the date goes, the kept one is
    untouched BYTE-FOR-BYTE, and another date's snapshot is never in the blast radius."""
    store, earlier, later = _plant_same_date_pair(tmp_path / "screen")
    other_date = _record(
        store, screen_date="2026-07-28", as_of="2026-07-28T23:59:59Z",
        bar_store_signature="c" * 16,
    )
    kept_bytes = (store.root / f"{later['id']}.json").read_bytes()

    removed = store.prune_superseded("2026-07-27", later["id"])

    assert removed == [earlier["id"]]
    assert not (store.root / f"{earlier['id']}.json").exists()
    assert (store.root / f"{later['id']}.json").read_bytes() == kept_bytes
    assert (store.root / f"{other_date['id']}.json").exists()
    records, errors = store.list()
    assert errors == []
    assert {r["id"] for r in records} == {later["id"], other_date["id"]}


def test_prune_superseded_on_a_date_with_one_copy_removes_nothing(tmp_path):
    store = ScreenStore(tmp_path / "screen")
    only = _record(store)

    assert store.prune_superseded("2026-06-22", only["id"]) == []
    assert (store.root / f"{only['id']}.json").exists()


def test_prune_superseded_refuses_when_the_snapshot_to_keep_is_not_registered(tmp_path):
    """A supersede runs only AFTER its replacement is safely on disk. An unregistered ``keep_id``
    means the caller is about to delete a date's LAST copy -- refused loudly, nothing removed."""
    store, earlier, later = _plant_same_date_pair(tmp_path / "screen")

    with pytest.raises(ValueError):
        store.prune_superseded("2026-07-27", "screen-2026-07-27-notrecorded")

    assert (store.root / f"{earlier['id']}.json").exists()
    assert (store.root / f"{later['id']}.json").exists()


def test_the_screen_list_route_serves_the_latest_screen_date_not_the_latest_recording(
    screen_route_ctx,
):
    """`latest` orders by ``screen_date`` first. Re-walking an OLDER date -- the routine act one
    snapshot per date is built around -- must not make that older date the desk's default view just
    because it was recorded most recently."""
    client, tmp_path = screen_route_ctx
    store = ScreenStore(tmp_path / "screen")
    newest_date = _record(
        store, screen_date="2026-08-04", as_of="2026-08-04T23:59:59Z",
        bar_store_signature="a" * 16,
    )
    # Recorded AFTER it, but for an EARLIER screen date -- exactly what a re-walk of a stale date
    # produces.
    older_date = _record(
        store, screen_date="2026-07-27", as_of="2026-07-27T23:59:59Z",
        bar_store_signature="b" * 16,
    )

    listed = client.get("/research/desk/screen").json()

    assert listed["latest"]["id"] == newest_date["id"]
    assert listed["latest"]["screen_date"] == "2026-08-04"
    assert older_date["created_utc"] >= newest_date["created_utc"]  # the recording order really is reversed
    assert {row["id"] for row in listed["screens"]} == {newest_date["id"], older_date["id"]}


def test_find_by_date_returns_the_newest_copy_of_that_date(tmp_path):
    store, _earlier, later = _plant_same_date_pair(tmp_path / "screen")
    _record(
        store, screen_date="2026-07-28", as_of="2026-07-28T23:59:59Z",
        bar_store_signature="c" * 16,
    )

    assert store.find_by_date("2026-07-27")["id"] == later["id"]
    assert store.find_by_date("2026-01-01") is None


# ==================================================================================================
# resolve_desk_screen_dir -- zero new Config field
# ==================================================================================================


def test_resolve_desk_screen_dir_defaults_to_a_sibling_of_the_universe_dir(monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_DESK_SCREEN_DIR", raising=False)
    resolved = resolve_desk_screen_dir("/some/root/.data/universe")
    assert resolved == "/some/root/.data/screen"


def test_resolve_desk_screen_dir_env_override(monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_DIR", "/tmp/custom-screen-dir")
    assert resolve_desk_screen_dir("/some/root/.data/universe") == "/tmp/custom-screen-dir"


def test_desk_screen_module_adds_no_config_field():
    """TC-16: the fingerprint pin is asserted unchanged by the sentinel every iteration; this
    module introduces zero new Config fields by construction (no import of a new field anywhere)."""
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"


# ==================================================================================================
# compute_screen -- the row-computation function, against the REAL fixture universe + real bars
# ==================================================================================================


def test_no_universe_snapshot_is_an_honest_empty_screen(tmp_path):
    universe_store = UniverseStore(tmp_path / "universe")
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "index.db"))
    dataset_store = DatasetStore(tmp_path / "datasets")

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)

    assert screen["universe_snapshot_id"] is None
    assert screen["rows"] == [] and screen["skipped"] == []
    assert screen["screen_date"] == SCREEN_DATE
    assert screen["as_of"] == "2026-06-22T23:59:59Z"


def test_fixture_universe_with_zero_bars_skips_every_member_as_no_bars(ctx):
    """TC-3: every one of the fixture universe's 103 members, with a completely empty bar store,
    appears in `skipped` with reason "no_bars" and none appears in `rows`."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)

    universe_records, _errors = universe_store.list()
    members = universe_records[-1]["members"]
    assert screen["rows"] == []
    assert len(screen["skipped"]) == len(members)
    assert {s["symbol"] for s in screen["skipped"]} == set(members)
    assert all(s["reason"] == "no_bars" for s in screen["skipped"])
    assert all(s["tick_evidence"] is False for s in screen["skipped"])
    # TC-5 (goal-desk-iter-15, J-11): a skip row never carries either history-disclosure field.
    assert all("history_sessions" not in s and "history_start" not in s for s in screen["skipped"])


def test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route(ctx, monkeypatch):
    """TC-1/TC-2/TC-19: the persisted AAPL row's band_class/distance_bps/band_score/price_low/
    price_high are byte-identical to what GET /research/tradability returns for the band
    desk_screen.py selected as AAPL's "best"; the reference close is the fixture bar's own
    recorded close at basis_as_of. TC-1: the row's own `basis_as_of` is byte-identical to the SAME
    route's own `basis_as_of`. TC-2: `basis_age_days` is the exact calendar-day count between that
    value and the screen's own `as_of` (the fixture's real 2026-06-18 -> 2026-06-22 span = 4 days;
    goal.md's own 12-day illustration is golden-asserted separately, as a pure-function test of the
    same formula, in `test_basis_age_days_matches_goal_mds_own_worked_example` below). (``git diff``
    on ``tradability.py``/``levels.py`` staying empty is verified directly against the repo, not by
    a test in this file.)"""
    from fastapi.testclient import TestClient

    from app.main import app, get_market_adapter, manager
    from app.research.routes import ResearchRegistry, set_registry
    from app.research.store import JournalStore

    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    aapl_rows = [r for r in screen["rows"] if r["symbol"] == "AAPL"]
    assert len(aapl_rows) == 1
    row = aapl_rows[0]

    # Point the REAL route's own `get_bar_store` dependency at this exact bar directory (the
    # `test_tradability_api.py` `ctx`-fixture convention) so `GET /research/tradability` reads
    # the SAME recorded AAPL series through the real request path, not a direct module call.
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(bar_store.root))
    journal = JournalStore(str(bar_store.root.parent / "journal.db"), CONFIG)
    set_registry(ResearchRegistry(journal, CONFIG))
    try:
        with TestClient(app) as client:
            resp = client.get(
                "/research/tradability", params={"symbol": "AAPL", "as_of": screen["as_of"]}
            )
    finally:
        for ticker in list(manager._engines.keys()):
            manager.stop(ticker)
        set_registry(None)
        app.dependency_overrides.pop(get_market_adapter, None)
        journal.close()

    assert resp.status_code == 200
    body = resp.json()
    assert body["basis_as_of"] == "2026-06-18T04:00:00.000000Z"

    # TC-1: the row's own basis_as_of is byte-identical to the SAME route's own basis_as_of --
    # never re-derived, copied verbatim from the identical compute_tradability result this row's
    # band/distance/score were themselves selected from.
    assert row["basis_as_of"] == body["basis_as_of"]
    # TC-2: the exact calendar-day count between that basis and the screen's own as_of
    # ("2026-06-22T23:59:59Z") -- 2026-06-18 -> 2026-06-22 is 4 calendar days.
    assert row["basis_age_days"] == 4

    matching = [
        b for b in body["bands"]
        if b["side"] == row["side"] and b["price_low"] == row["price_low"] and b["price_high"] == row["price_high"]
    ]
    assert len(matching) == 1, "the selected band must be a real, uniquely-identifiable served band"
    served = matching[0]
    assert served["class"] == row["band_class"]
    assert served["quality_score"] == row["band_score"]

    # The reference close is the fixture bar's OWN recorded close at basis_as_of -- resolved by
    # date (never a hardcoded epoch literal) to avoid a copy-paste timestamp mismatch.
    from datetime import datetime, timezone

    basis_date = datetime.fromisoformat(body["basis_as_of"].replace("Z", "+00:00")).date()
    fixture = _load_yahoo_fixture(AAPL_DAILY_FIXTURE)
    basis_bar = next(
        b for b in fixture["bars"]
        if datetime.fromtimestamp(b["epoch"], tz=timezone.utc).date() == basis_date
    )
    expected_close = basis_bar["close"]
    expected_distance = abs(
        (row["price_low"] if row["side"] == "resistance" else row["price_high"]) - expected_close
    ) / expected_close * 10_000.0
    assert row["distance_bps"] == pytest.approx(expected_distance)

    # goal-desk-iter-18 (J-14) TC-2/TC-3/TC-4, against the REAL route rather than an injected band
    # list: `bands_by_class` is a recount of the SAME served `bands`, and `opposite_band` -- when
    # present -- is a real, uniquely-identifiable served band on the OTHER side whose distance
    # reproduces the row's own `_distance_bps` formula against the row's own `reference_close`.
    served_counts = {"A": 0, "B": 0, "C": 0, "unclassified": 0}
    for band in body["bands"]:
        served_counts[band["class"] if band["class"] is not None else "unclassified"] += 1
    assert row["bands_by_class"] == served_counts
    assert sum(row["bands_by_class"].values()) == len(body["bands"])

    served_opposite = [b for b in body["bands"] if b["side"] != row["side"]]
    if row["opposite_band"] is None:
        assert served_opposite == [], (
            "opposite_band may only be null when the canonical route served NO band on the other side"
        )
    else:
        opposite_matching = [
            b for b in served_opposite
            if b["price_low"] == row["opposite_band"]["price_low"]
            and b["price_high"] == row["opposite_band"]["price_high"]
        ]
        assert len(opposite_matching) == 1, (
            "the disclosed opposite band must be a real, uniquely-identifiable served band on the "
            "side the row's own band is NOT on"
        )
        served_opp = opposite_matching[0]
        assert row["opposite_band"]["side"] == served_opp["side"] != row["side"]
        assert row["opposite_band"]["band_class"] == served_opp["class"]
        assert row["opposite_band"]["band_score"] == served_opp["quality_score"]
        expected_opposite_distance = abs(
            (
                served_opp["price_low"]
                if served_opp["side"] == "resistance"
                else served_opp["price_high"]
            )
            - row["reference_close"]
        ) / row["reference_close"] * 10_000.0
        assert row["opposite_band"]["distance_bps"] == pytest.approx(expected_opposite_distance)

    # goal-desk-iter-23 (J-15) TC-2/TC-3: band_member_count/band_round_number are copied verbatim
    # off the SAME served band's own member_count/round_number, and band_member_timeframes is a
    # plain tally of that SAME band's own members list, summing to band_member_count.
    assert row["band_member_count"] == served["member_count"]
    assert row["band_round_number"] == served["round_number"]
    expected_timeframes: dict[str, int] = {}
    for member in served["members"]:
        expected_timeframes[member["timeframe"]] = expected_timeframes.get(member["timeframe"], 0) + 1
    assert row["band_member_timeframes"] == expected_timeframes
    assert sum(row["band_member_timeframes"].values()) == row["band_member_count"]


def test_msft_partial_coverage_still_resolves_a_ranked_row_with_honest_coverage(ctx):
    """TC-2: MSFT (real symbol, 1h+1d bars only -- never 1w/4h) is never mis-skipped merely for
    partial pinned-timeframe coverage, and its coverage field reports 1h/1d has_bars: true, 4h/1w
    has_bars: false."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_HOURLY_FIXTURE))

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    msft_rows = [r for r in screen["rows"] if r["symbol"] == "MSFT"]
    assert len(msft_rows) == 1, "MSFT must resolve a ranked row, never a skip, despite partial coverage"
    row = msft_rows[0]

    assert row["coverage"]["1h"]["has_bars"] is True
    assert row["coverage"]["1d"]["has_bars"] is True
    assert row["coverage"]["4h"]["has_bars"] is False
    assert row["coverage"]["1w"]["has_bars"] is False
    assert row["band_class"] in ("A", "B", "C", None)


def test_a_daily_series_with_no_resolvable_prior_session_is_skipped_no_basis(ctx):
    """TC-11: a real fixture-universe member with a daily series but no PRIOR session (every bar
    dated on/after the requested screen_date) is skipped "no_basis" (distinct from "no_bars"), and
    its coverage still honestly reflects the timeframe that DOES have bars (1d), never all-false."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    meta = bar_store.record(
        symbol="ABBV", timeframe="1d", window_start_utc="2026-06-22T00:00:00Z",
        window_end_utc="2026-06-23T00:00:00Z", feed="yahoo",
        bars=[RawBar("ABBV", "1d", 1782446400.0, 100.0, 101.0, 99.0, 100.5, 1000)],  # 2026-06-25
    )
    bar_index.insert(meta)

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    abbv_skips = [s for s in screen["skipped"] if s["symbol"] == "ABBV"]
    assert len(abbv_skips) == 1
    entry = abbv_skips[0]
    assert entry["reason"] == "no_basis"
    assert entry["coverage"]["1d"]["has_bars"] is True
    assert entry["coverage"]["1h"]["has_bars"] is False
    # TC-5 (goal-desk-iter-15, J-11): a "no_basis" skip row never carries either history field.
    assert "history_sessions" not in entry and "history_start" not in entry


def test_repeat_computation_in_two_fresh_instances_is_byte_identical(ctx, tmp_path):
    """TC-10: no wall-clock, no unseeded randomness -- two fresh computations produce byte-identical
    rows/skipped."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_HOURLY_FIXTURE))

    first = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    second = compute_screen(
        UniverseStore(universe_store.root), BarStore(bar_store.root), BarIndex(bar_index.db_path),
        DatasetStore(tmp_path / "datasets"), CONFIG, SCREEN_DATE,
    )
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_every_row_and_skip_coverage_is_byte_identical_to_get_desk_coverage(ctx):
    """TC-12: proves reuse, not re-derivation."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_HOURLY_FIXTURE))

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    coverage = get_desk_coverage(universe_store, bar_index)
    coverage_by_symbol = {m["symbol"]: m["per_timeframe"] for m in coverage["members"]}

    for entry in (*screen["rows"], *screen["skipped"]):
        assert entry["coverage"] == coverage_by_symbol[entry["symbol"]], entry["symbol"]


def test_tick_evidence_true_for_exactly_the_registered_dataset_symbols(ctx):
    """TC-13: the 11 named dataset symbols (10 of which are actual S&P 100 / fixture-universe
    members -- SPY is not) register true; every other member registers false."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    for symbol in DATASET_SYMBOLS:
        _register_dataset(dataset_store, symbol)

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    all_entries = {e["symbol"]: e for e in (*screen["rows"], *screen["skipped"])}

    universe_records, _errors = universe_store.list()
    members = set(universe_records[-1]["members"])
    expected_true = set(DATASET_SYMBOLS) & members
    assert expected_true, "the fixture universe must contain at least one of the named symbols"

    for symbol in expected_true:
        assert all_entries[symbol]["tick_evidence"] is True, symbol
    for symbol in members - expected_true:
        assert all_entries[symbol]["tick_evidence"] is False, symbol


def test_rows_are_sorted_by_class_then_distance_then_score_then_symbol(ctx):
    """TC-14: AAPL's best band is class C; MSFT's is class B (both verified directly) -- MSFT
    must rank strictly above AAPL by class alone, independent of distance/score."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_HOURLY_FIXTURE))

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    by_symbol = {r["symbol"]: r for r in screen["rows"]}
    assert by_symbol["AAPL"]["band_class"] == "C"
    assert by_symbol["MSFT"]["band_class"] == "B"

    positions = {r["symbol"]: i for i, r in enumerate(screen["rows"])}
    assert positions["MSFT"] < positions["AAPL"]

    # The list-wide invariant: every row's own rank key is non-decreasing.
    keys = [_row_rank_key(r) for r in screen["rows"]]
    assert keys == sorted(keys)


# ==================================================================================================
# basis disclosure (goal-desk-iter-9, J-08) -- basis_as_of / basis_age_days
# ==================================================================================================


def test_basis_age_days_matches_goal_mds_own_worked_example():
    """TC-2 (pure-function form): goal.md's own worked example -- "a basis 12 calendar days before
    as_of yields basis_age_days == 12" -- asserted directly against the helper, independent of any
    fixture's own real date spread (the AAPL cross-check test above golden-asserts the SAME formula
    against a different, real 4-day gap -- 2026-06-18 to 2026-06-22)."""
    assert _basis_age_days("2026-06-13T04:00:00.000000Z", "2026-06-25T23:59:59Z") == 12


def test_basis_age_days_is_a_calendar_date_difference_not_a_raw_hour_delta():
    """``basis_as_of``'s own time-of-day (e.g. ``04:00:00``, a bar's own recorded hour) must never
    leak into the day count against ``as_of``'s fixed ``23:59:59`` -- both sides collapse to a UTC
    calendar DATE first, so a same-calendar-day pair reads 0 even ~20 hours apart, and a
    calendar-adjacent pair reads 1 even ~1 hour apart."""
    assert _basis_age_days("2026-06-22T04:00:00.000000Z", "2026-06-22T23:59:59Z") == 0
    assert _basis_age_days("2026-06-21T23:00:00.000000Z", "2026-06-22T00:00:01.000000Z") == 1


def test_basis_fields_add_zero_extra_compute_tradability_calls(ctx, monkeypatch):
    """TC-8: basis_as_of/basis_age_days are read/derived ENTIRELY from the per-member
    ``compute_tradability`` result already fetched inside the walk -- instrumented exactly like
    ``test_bar_store_signature_issues_zero_bar_store_calls`` (a call-COUNT assertion, not a
    behavior one), this proves the call count equals exactly the member count: one call per member
    (the existing contract), zero calls attributable to the two new fields."""
    import app.research.desk_screen as desk_screen_module

    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))

    calls: list[str] = []
    original = desk_screen_module.compute_tradability

    def _tracked(store, symbol, as_of_epoch, config):
        calls.append(symbol)
        return original(store, symbol, as_of_epoch, config)

    monkeypatch.setattr(desk_screen_module, "compute_tradability", _tracked)

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)

    universe_records, _errors = universe_store.list()
    members = universe_records[-1]["members"]
    assert calls == members, "exactly one compute_tradability call per member, in walk order"
    assert screen["rows"], "the walk must have actually produced at least one ranked row"


def test_recording_a_freshly_computed_screen_twice_is_refused_and_basis_fields_stay_byte_identical(
    ctx, tmp_path
):
    """TC-3: a REAL ``compute_screen()`` result (carrying ``basis_as_of``/``basis_age_days`` on its
    ranked rows) recorded once, then a FRESH computation under the identical pins -- the second
    ``record()`` call is refused (``ScreenAlreadyRecorded``, no second file written), and the
    content already on disk -- read back via ``list()`` -- is byte-identical to the second
    (unrecorded) computation, including both new fields on every ranked row."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    screen_store = ScreenStore(tmp_path / "screen")

    first_screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    recorded = screen_store.record(**first_screen)
    assert len(list((tmp_path / "screen").glob("*.json"))) == 1

    second_screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    with pytest.raises(ScreenAlreadyRecorded) as excinfo:
        screen_store.record(**second_screen)
    assert excinfo.value.existing_id == recorded["id"]
    assert len(list((tmp_path / "screen").glob("*.json"))) == 1, "no second file written"

    stored_records, errors = screen_store.list()
    assert errors == []
    assert len(stored_records) == 1
    assert json.dumps(stored_records[0]["rows"], sort_keys=True) == json.dumps(
        second_screen["rows"], sort_keys=True
    )
    aapl_row = next(r for r in stored_records[0]["rows"] if r["symbol"] == "AAPL")
    assert aapl_row["basis_as_of"] == "2026-06-18T04:00:00.000000Z"
    assert aapl_row["basis_age_days"] == 4


def test_a_legacy_row_recorded_without_basis_fields_serves_them_absent_never_backfilled(tmp_path):
    """The exact shape every screen snapshot recorded BEFORE this iteration has: ranked rows that
    OMIT ``basis_as_of``/``basis_age_days`` entirely (never merely present-as-``null``).
    ``ScreenStore`` performs no row-shape validation or enrichment of any kind -- a plain
    checksum-verified passthrough (``_record``'s own default row, reused across this whole file's
    store-level suite, already carries no such keys) -- so this is true by construction; this test
    pins that contract so a future change cannot silently start defaulting or backfilling legacy
    rows on read."""
    store = ScreenStore(tmp_path / "screen")
    _record(store)  # `_record`'s own default row carries no basis_as_of/basis_age_days key at all

    records, errors = store.list()
    assert errors == []
    row = records[0]["rows"][0]
    assert "basis_as_of" not in row
    assert "basis_age_days" not in row


# ==================================================================================================
# history disclosure (goal-desk-iter-15, J-11) -- history_sessions / history_start
# ==================================================================================================


def _daily_bar_epoch(day: date) -> float:
    """04:00 UTC -- the SAME daily-bar hour every Yahoo fixture in this file already uses."""
    return datetime(day.year, day.month, day.day, 4, 0, 0, tzinfo=timezone.utc).timestamp()


def _iso_of(epoch: float) -> str:
    """The SAME epoch -> ISO formatting ``desk_screen.py``'s own ``_iso`` uses -- a local copy per
    this project's own convention (each module/test owns its tiny formatting helper)."""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _daily_bars(symbol: str, start: date, count: int) -> list[RawBar]:
    """``count`` synthetic daily bars for a REAL fixture-universe member (lessons.md iter-2: never a
    synthetic ``AAA``-style symbol for a clause naming real symbols -- only the price/volume values
    here are synthetic), one per calendar day starting at ``start``. Only the TIMESTAMPS matter to a
    history-depth count, so price/volume are arbitrary constants."""
    return [
        RawBar(symbol, "1d", _daily_bar_epoch(start + timedelta(days=i)), 100.0, 101.0, 99.0, 100.5, 1000)
        for i in range(count)
    ]


def _seed_daily_bars(bar_store: BarStore, bar_index: BarIndex, bars: list[RawBar]) -> None:
    meta = bar_store.record(
        symbol=bars[0].symbol, timeframe="1d",
        window_start_utc=_iso_of(bars[0].epoch), window_end_utc=_iso_of(bars[-1].epoch + 86400.0),
        feed="yahoo", bars=bars,
    )
    bar_index.insert(meta)


def test_history_sessions_and_start_match_the_seeded_daily_series_up_to_basis(ctx):
    """TC-1: a real fixture-universe member (ABBV) seeded with 5 synthetic daily bars, all dated
    strictly before ``SCREEN_DATE`` (so every seeded bar counts and the basis resolves to the LAST
    one) -- the ranked row's ``history_sessions`` equals the seeded count and ``history_start``
    equals the earliest seeded bar's own timestamp."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    bars = _daily_bars("ABBV", start=date(2026, 6, 12), count=5)  # 06-12 .. 06-16, all < 06-22
    _seed_daily_bars(bar_store, bar_index, bars)

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    row = next(r for r in screen["rows"] if r["symbol"] == "ABBV")

    assert row["basis_as_of"] == _iso_of(bars[-1].epoch)
    assert row["history_sessions"] == 5
    assert row["history_start"] == _iso_of(bars[0].epoch)


def test_history_sessions_is_not_off_by_one_when_the_basis_bar_is_the_series_first_bar(ctx):
    """Error case (goal.md's own TESTING REQUIREMENTS): a member whose basis resolves to the VERY
    FIRST bar in its own series -- ``history_sessions`` must read ``1``, never ``0`` (an off-by-one
    undercount) nor any value implying a second, unseen bar."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    bars = _daily_bars("ABBV", start=date(2026, 6, 18), count=1)
    _seed_daily_bars(bar_store, bar_index, bars)

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    row = next(r for r in screen["rows"] if r["symbol"] == "ABBV")

    assert row["history_sessions"] == 1
    assert row["history_start"] == row["basis_as_of"] == _iso_of(bars[0].epoch)


def test_short_and_long_history_members_carry_visibly_different_session_counts_in_the_same_run(ctx):
    """TC-2: two real fixture-universe members, each seeded with its OWN synthetic daily series --
    ABBV short (5 sessions), ACN long (450 sessions), both entirely BEFORE ``SCREEN_DATE`` so every
    seeded bar counts -- resolve visibly different ``history_sessions`` in the SAME screen run,
    independently confirming the DoD's <=60 / >=400 split is reachable in THIS rig (iter-9 lesson:
    never trust goal.md's own cited live numbers as a byte-for-byte target)."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    short_bars = _daily_bars("ABBV", start=date(2026, 6, 12), count=5)
    long_bars = _daily_bars("ACN", start=date(2025, 1, 1), count=450)
    _seed_daily_bars(bar_store, bar_index, short_bars)
    _seed_daily_bars(bar_store, bar_index, long_bars)

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    by_symbol = {r["symbol"]: r for r in screen["rows"]}
    assert "ABBV" in by_symbol and "ACN" in by_symbol

    short_row, long_row = by_symbol["ABBV"], by_symbol["ACN"]
    assert short_row["history_sessions"] == 5
    assert short_row["history_start"] == _iso_of(short_bars[0].epoch)
    assert long_row["history_sessions"] == 450
    assert long_row["history_start"] == _iso_of(long_bars[0].epoch)

    # The DoD's own split (<=60 short, >=400 long), confirmed reachable in THIS run.
    assert short_row["history_sessions"] <= 60
    assert long_row["history_sessions"] >= 400


def test_history_fields_stay_byte_identical_on_a_recompute_under_identical_pins(ctx, tmp_path):
    """TC-3: mirrors ``test_recording_a_freshly_computed_screen_twice_is_refused_and_basis_fields_
    stay_byte_identical`` for the two NEW fields -- a screen recorded once, then a FRESH computation
    under the identical pins, is refused a second write, and the content already on disk (read back
    via ``list()``) is byte-identical to the second (unrecorded) computation's ``history_sessions``/
    ``history_start`` on every ranked row."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    screen_store = ScreenStore(tmp_path / "screen")

    first_screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    recorded = screen_store.record(**first_screen)

    second_screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    with pytest.raises(ScreenAlreadyRecorded) as excinfo:
        screen_store.record(**second_screen)
    assert excinfo.value.existing_id == recorded["id"]

    stored_records, errors = screen_store.list()
    assert errors == []
    assert json.dumps(stored_records[0]["rows"], sort_keys=True) == json.dumps(
        second_screen["rows"], sort_keys=True
    )
    aapl_row = next(r for r in stored_records[0]["rows"] if r["symbol"] == "AAPL")
    assert aapl_row["history_sessions"] == next(
        r for r in second_screen["rows"] if r["symbol"] == "AAPL"
    )["history_sessions"]
    assert aapl_row["history_start"] is not None


def test_a_legacy_row_recorded_without_history_fields_serves_them_absent_never_backfilled(tmp_path):
    """TC-4: the exact shape every screen snapshot recorded BEFORE this iteration has: ranked rows
    that OMIT ``history_sessions``/``history_start`` entirely (never merely present-as-``null``) --
    mirrors ``test_a_legacy_row_recorded_without_basis_fields_serves_them_absent_never_backfilled``
    for the two new fields. ``_record``'s own default row carries no such keys at all, so this is
    true by construction; this test pins that contract so a future change cannot silently start
    defaulting or backfilling legacy rows on read."""
    store = ScreenStore(tmp_path / "screen")
    _record(store)

    records, errors = store.list()
    assert errors == []
    row = records[0]["rows"][0]
    assert "history_sessions" not in row
    assert "history_start" not in row


def test_history_fields_add_zero_extra_merged_bars_calls(ctx, monkeypatch):
    """TC-6: proves the row builder's reference-close-plus-history derivation
    (``_resolve_reference_close_and_history``) issues exactly the ONE ``BarStore.merged_bars(symbol,
    "1d")`` call it already issued before J-11 (goal-desk-iter-9's own reference-close walk) -- never
    a second, separate walk for the history fields. Compares the per-symbol total ``merged_bars(...,
    "1d")`` call count of a FULL screen walk against ``compute_tradability`` run ALONE on the
    identical inputs (the only OTHER source of ``merged_bars(symbol, "1d")`` calls in this walk, via
    ``tradability.py``'s own ``_select_daily_series`` and ``compute_levels``'s per-timeframe reads):
    the full walk must add exactly ONE more such call -- the SAME single call the row builder always
    made -- never two. goal-desk-iter-17 (J-13) TC-7: `reference_close` is read from this SAME
    `_resolve_reference_close_and_history` tuple (no separate accessor of its own), so this guard
    already covers it -- no additional test is needed to prove `reference_close` adds zero further
    `merged_bars` calls."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))

    as_of_epoch = _epoch(screen_as_of(SCREEN_DATE))
    calls: list[tuple[str, str]] = []
    original = BarStore.merged_bars

    def _tracked(self, symbol, timeframe):
        calls.append((symbol, timeframe))
        return original(self, symbol, timeframe)

    monkeypatch.setattr(BarStore, "merged_bars", _tracked)

    from app.research.tradability import compute_tradability as _compute_tradability

    _compute_tradability(bar_store, "AAPL", as_of_epoch, CONFIG)
    baseline_1d_calls = sum(1 for symbol, timeframe in calls if symbol == "AAPL" and timeframe == "1d")
    calls.clear()

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    assert any(r["symbol"] == "AAPL" for r in screen["rows"]), "AAPL must resolve a ranked row"
    full_1d_calls = sum(1 for symbol, timeframe in calls if symbol == "AAPL" and timeframe == "1d")

    assert full_1d_calls == baseline_1d_calls + 1, (
        "the row builder's reference-close+history derivation must add exactly ONE merged_bars "
        "call beyond compute_tradability's own basis resolution -- never a second walk for history"
    )


def test_aapl_row_history_cross_checks_against_get_candles(ctx, monkeypatch):
    """TC-7: single-source-of-truth cross-check -- the AAPL ranked row's ``history_sessions``/
    ``history_start`` match ``GET /research/candles``'s own merged, price-less-row-excluded response
    (the SAME route the chart itself reads) filtered to bars at or before the row's own
    ``basis_as_of``, proving the desk never derives a divergent count from a second, independent
    read."""
    from fastapi.testclient import TestClient

    from app.main import app, get_market_adapter, manager
    from app.research.routes import ResearchRegistry, set_registry
    from app.research.store import JournalStore

    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    row = next(r for r in screen["rows"] if r["symbol"] == "AAPL")

    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(bar_store.root))
    journal = JournalStore(str(bar_store.root.parent / "journal.db"), CONFIG)
    set_registry(ResearchRegistry(journal, CONFIG))
    try:
        with TestClient(app) as client:
            resp = client.get(
                "/research/candles", params={"symbol": "AAPL", "timeframe": "1d", "limit": 500}
            )
    finally:
        for ticker in list(manager._engines.keys()):
            manager.stop(ticker)
        set_registry(None)
        app.dependency_overrides.pop(get_market_adapter, None)
        journal.close()

    assert resp.status_code == 200
    body = resp.json()

    basis_epoch = datetime.fromisoformat(row["basis_as_of"].replace("Z", "+00:00")).timestamp()
    filtered = [bar for bar in body["bars"] if bar["ts"] <= basis_epoch]
    assert len(filtered) == row["history_sessions"]
    earliest_ts = min(bar["ts"] for bar in filtered)
    assert _iso_of(earliest_ts) == row["history_start"]


# ==================================================================================================
# reference-close disclosure (goal-desk-iter-17, J-13) -- reference_close: the exact price the row's
# band was measured against, so "the price is inside the wall" is a fact visible on screen instead
# of arithmetic recovered by inverting distance_bps against a band edge.
# ==================================================================================================


def test_aapl_row_reference_close_equals_the_fixture_bars_own_recorded_close(ctx):
    """TC-1/TC-19: `reference_close` is byte-identical to the AAPL fixture bar's own recorded close
    at `basis_as_of` -- the SAME `expected_close` derivation
    `test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route` already uses for its
    own `distance_bps` assertion, confirming the new field is copied from the identical `close`
    local that assertion is itself built from."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    row = next(r for r in screen["rows"] if r["symbol"] == "AAPL")

    basis_date = datetime.fromisoformat(row["basis_as_of"].replace("Z", "+00:00")).date()
    fixture = _load_yahoo_fixture(AAPL_DAILY_FIXTURE)
    basis_bar = next(
        b for b in fixture["bars"]
        if datetime.fromtimestamp(b["epoch"], tz=timezone.utc).date() == basis_date
    )
    assert row["reference_close"] == basis_bar["close"]


def test_reference_close_golden_in_band_and_out_of_band_rows(ctx, monkeypatch):
    """TC-1: two controlled ranked rows -- one whose `reference_close` sits exactly on its selected
    band's near edge (`distance_bps == 0.0`, the boundary case of "the price is inside the wall":
    `price_low <= reference_close <= price_high`), and one whose close sits strictly outside its
    band. `compute_tradability` is monkeypatched to return exact, controlled bands (the
    `test_basis_fields_add_zero_extra_compute_tradability_calls` precedent) so both scenarios are
    deterministic rather than hoped-for from real fixture data; the CLOSE itself is real -- resolved
    by the real `_resolve_reference_close_and_history` walk over a synthetic daily bar seeded
    through the real `BarStore`, never hand-set on the row."""
    import app.research.desk_screen as desk_screen_module

    universe_store, bar_store, bar_index, dataset_store = ctx
    inband_bar = _daily_bars("ABBV", start=date(2026, 6, 18), count=1)[0]
    outband_bar = _daily_bars("ACN", start=date(2026, 6, 18), count=1)[0]
    _seed_daily_bars(bar_store, bar_index, [inband_bar])
    _seed_daily_bars(bar_store, bar_index, [outband_bar])

    inband_basis = _iso_of(inband_bar.epoch)
    outband_basis = _iso_of(outband_bar.epoch)

    # price_low == the seeded close exactly -> distance_bps 0.0, and reference_close sits AT the
    # near edge, i.e. inside [price_low, price_high].
    inband_band = _band("resistance", inband_bar.close, inband_bar.close + 5.0, "A", 10.0)
    # price_low strictly above the seeded close -> distance_bps > 0, reference_close outside
    # [price_low, price_high].
    outband_band = _band("resistance", outband_bar.close + 5.0, outband_bar.close + 10.0, "B", 5.0)

    original = desk_screen_module.compute_tradability

    def _tracked(store, symbol, as_of_epoch, config):
        if symbol == "ABBV":
            return {"no_bar_series_for_symbol": False, "basis_as_of": inband_basis, "bands": [inband_band]}
        if symbol == "ACN":
            return {"no_bar_series_for_symbol": False, "basis_as_of": outband_basis, "bands": [outband_band]}
        return original(store, symbol, as_of_epoch, config)

    monkeypatch.setattr(desk_screen_module, "compute_tradability", _tracked)

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    by_symbol = {r["symbol"]: r for r in screen["rows"]}

    inband_row = by_symbol["ABBV"]
    assert inband_row["reference_close"] == inband_bar.close
    assert inband_row["distance_bps"] == 0.0
    assert inband_row["price_low"] <= inband_row["reference_close"] <= inband_row["price_high"]

    outband_row = by_symbol["ACN"]
    assert outband_row["reference_close"] == outband_bar.close
    assert outband_row["distance_bps"] > 0.0
    assert not (outband_row["price_low"] <= outband_row["reference_close"] <= outband_row["price_high"])


def test_row_order_is_unchanged_by_the_reference_close_addition(ctx):
    """TC-3: `_row_rank_key` is computed entirely from `band_class`/`distance_bps`/`band_score`/
    `symbol` -- unchanged this iteration (verify via `git diff`, appearing only as unchanged
    CONTEXT) -- none of which the new `reference_close` field touches. The ranked-row symbol
    SEQUENCE for this same fixture spread (the `test_rows_are_sorted_by_class_then_distance_then_
    score_then_symbol` precedent) is exactly the sort of `_row_rank_key` over the SAME rows,
    confirming the new field is a pure addition to row CONTENT, never a reordering."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_HOURLY_FIXTURE))

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    symbols = [r["symbol"] for r in screen["rows"]]
    expected = [r["symbol"] for r in sorted(screen["rows"], key=_row_rank_key)]
    assert symbols == expected
    assert symbols == ["MSFT", "AAPL"], "pin the exact fixture-spread order so a silent reorder is caught"


def test_aapl_row_reference_close_cross_checks_against_get_candles(ctx, monkeypatch):
    """TC-2: `reference_close` is byte-identical to the `close` field of the `1d` bar dated at the
    row's own `basis_as_of`, read via `GET /research/candles?symbol=AAPL&timeframe=1d` -- the SAME
    route the chart itself reads -- mirroring `test_aapl_row_history_cross_checks_against_get_
    candles`'s single-source-of-truth proof for the two history fields, applied to the new one."""
    from fastapi.testclient import TestClient

    from app.main import app, get_market_adapter, manager
    from app.research.routes import ResearchRegistry, set_registry
    from app.research.store import JournalStore

    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    row = next(r for r in screen["rows"] if r["symbol"] == "AAPL")

    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(bar_store.root))
    journal = JournalStore(str(bar_store.root.parent / "journal.db"), CONFIG)
    set_registry(ResearchRegistry(journal, CONFIG))
    try:
        with TestClient(app) as client:
            resp = client.get(
                "/research/candles", params={"symbol": "AAPL", "timeframe": "1d", "limit": 500}
            )
    finally:
        for ticker in list(manager._engines.keys()):
            manager.stop(ticker)
        set_registry(None)
        app.dependency_overrides.pop(get_market_adapter, None)
        journal.close()

    assert resp.status_code == 200
    body = resp.json()

    basis_epoch = datetime.fromisoformat(row["basis_as_of"].replace("Z", "+00:00")).timestamp()
    filtered = [bar for bar in body["bars"] if bar["ts"] <= basis_epoch]
    basis_bar = max(filtered, key=lambda b: b["ts"])
    assert row["reference_close"] == basis_bar["close"]


def test_reference_close_stays_byte_identical_on_a_recompute_under_identical_pins(ctx, tmp_path):
    """TC-4: mirrors `test_history_fields_stay_byte_identical_on_a_recompute_under_identical_pins`
    for `reference_close` specifically -- a screen recorded once, then a FRESH computation under
    identical pins, is refused a second write, and the content already on disk (read back via
    `list()`) is byte-identical to the second (unrecorded) computation's `reference_close` on every
    ranked row."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    screen_store = ScreenStore(tmp_path / "screen")

    first_screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    recorded = screen_store.record(**first_screen)

    second_screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    with pytest.raises(ScreenAlreadyRecorded) as excinfo:
        screen_store.record(**second_screen)
    assert excinfo.value.existing_id == recorded["id"]

    stored_records, errors = screen_store.list()
    assert errors == []
    assert json.dumps(stored_records[0]["rows"], sort_keys=True) == json.dumps(
        second_screen["rows"], sort_keys=True
    )
    aapl_row = next(r for r in stored_records[0]["rows"] if r["symbol"] == "AAPL")
    assert aapl_row["reference_close"] == next(
        r for r in second_screen["rows"] if r["symbol"] == "AAPL"
    )["reference_close"]


def test_a_legacy_row_recorded_without_reference_close_serves_it_absent_never_backfilled(tmp_path):
    """TC-5: the exact shape every screen snapshot recorded BEFORE this iteration has -- ranked rows
    that OMIT `reference_close` entirely (never merely present-as-`null`) -- mirrors the basis/
    history legacy-row precedents for the new field. `_record`'s own default row carries no such key
    at all, so this is true by construction; this test pins that contract so a future change cannot
    silently start defaulting or backfilling legacy rows on read."""
    store = ScreenStore(tmp_path / "screen")
    _record(store)  # `_record`'s own default row carries no reference_close key at all

    records, errors = store.list()
    assert errors == []
    row = records[0]["rows"][0]
    assert "reference_close" not in row


# ==================================================================================================
# opposite-band disclosure (goal-desk-iter-18, J-14) -- opposite_band: the nearest band on the side
# of price the row's own selected band did NOT choose; bands_by_class: a per-class count of every
# band compute_tradability returned for that symbol. Both drawn from the SAME result["bands"] list
# already held for `reference_close`/`distance_bps` -- zero new BarStore read, zero second
# compute_tradability call.
# ==================================================================================================


def test_opposite_band_golden_near_far_and_null_class_rows(ctx, monkeypatch):
    """TC-1/TC-2/TC-3/TC-4: three controlled ranked rows -- one whose nearest opposite-side band is
    within 25 bps, one whose nearest opposite-side band is beyond 1,000 bps, and one whose nearest
    opposite-side band carries `class: None` -- each proving `opposite_band`'s fields are copied
    verbatim from `compute_tradability`'s own served band and `bands_by_class` sums to the symbol's
    total band count. Mirrors the `test_reference_close_golden_in_band_and_out_of_band_rows`
    precedent: `compute_tradability` is monkeypatched to return exact, controlled bands so all three
    scenarios are deterministic, while the reference CLOSE itself is real -- resolved by the real
    `_resolve_reference_close_and_history` walk over a synthetic daily bar seeded through the real
    `BarStore`, never hand-set on the row."""
    import app.research.desk_screen as desk_screen_module

    universe_store, bar_store, bar_index, dataset_store = ctx
    near_bar = _daily_bars("ABBV", start=date(2026, 6, 18), count=1)[0]
    far_bar = _daily_bars("ACN", start=date(2026, 6, 18), count=1)[0]
    null_bar = _daily_bars("ADBE", start=date(2026, 6, 18), count=1)[0]
    _seed_daily_bars(bar_store, bar_index, [near_bar])
    _seed_daily_bars(bar_store, bar_index, [far_bar])
    _seed_daily_bars(bar_store, bar_index, [null_bar])

    near_basis = _iso_of(near_bar.epoch)
    far_basis = _iso_of(far_bar.epoch)
    null_basis = _iso_of(null_bar.epoch)

    # ABBV: best band = resistance A right at close (distance_bps 0.0, always wins on class alone);
    # opposite (support) band ~20 bps below close -- within the 25 bps evidence floor TC-12 names.
    abbv_best = _band("resistance", near_bar.close, near_bar.close + 5.0, "A", 10.0)
    abbv_opposite = _band("support", near_bar.close - 1.0, near_bar.close - 0.2, "B", 5.0)

    # ACN: best band = resistance A right at close; opposite (support) band $20 below close --
    # ~1,990 bps, well beyond the 1,000 bps evidence floor.
    acn_best = _band("resistance", far_bar.close, far_bar.close + 5.0, "A", 10.0)
    acn_opposite = _band("support", far_bar.close - 25.0, far_bar.close - 20.0, "C", 3.0)

    # ADBE: best band = resistance A right at close; the ONLY opposite (support) band carries
    # `class: None` -- proving `bands_by_class` counts it under "unclassified" and `opposite_band`
    # still discloses it (an ungraded band is still a real, servable disclosure).
    adbe_best = _band("resistance", null_bar.close, null_bar.close + 5.0, "A", 10.0)
    adbe_opposite = _band("support", null_bar.close - 2.0, null_bar.close - 1.0, None, 1.0)

    original = desk_screen_module.compute_tradability

    def _tracked(store, symbol, as_of_epoch, config):
        if symbol == "ABBV":
            return {"no_bar_series_for_symbol": False, "basis_as_of": near_basis, "bands": [abbv_best, abbv_opposite]}
        if symbol == "ACN":
            return {"no_bar_series_for_symbol": False, "basis_as_of": far_basis, "bands": [acn_best, acn_opposite]}
        if symbol == "ADBE":
            return {"no_bar_series_for_symbol": False, "basis_as_of": null_basis, "bands": [adbe_best, adbe_opposite]}
        return original(store, symbol, as_of_epoch, config)

    monkeypatch.setattr(desk_screen_module, "compute_tradability", _tracked)

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    by_symbol = {r["symbol"]: r for r in screen["rows"]}

    abbv_row = by_symbol["ABBV"]
    assert abbv_row["opposite_band"] == {
        "side": "support",
        "band_class": "B",
        "price_low": abbv_opposite["price_low"],
        "price_high": abbv_opposite["price_high"],
        "band_score": abbv_opposite["quality_score"],
        "distance_bps": _distance_bps(abbv_opposite, near_bar.close),
    }
    assert abbv_row["opposite_band"]["distance_bps"] <= 25.0
    assert abbv_row["bands_by_class"] == {"A": 1, "B": 1, "C": 0, "unclassified": 0}
    assert sum(abbv_row["bands_by_class"].values()) == 2

    acn_row = by_symbol["ACN"]
    assert acn_row["opposite_band"] == {
        "side": "support",
        "band_class": "C",
        "price_low": acn_opposite["price_low"],
        "price_high": acn_opposite["price_high"],
        "band_score": acn_opposite["quality_score"],
        "distance_bps": _distance_bps(acn_opposite, far_bar.close),
    }
    assert acn_row["opposite_band"]["distance_bps"] > 1000.0
    assert acn_row["bands_by_class"] == {"A": 1, "B": 0, "C": 1, "unclassified": 0}
    assert sum(acn_row["bands_by_class"].values()) == 2

    adbe_row = by_symbol["ADBE"]
    assert adbe_row["opposite_band"] == {
        "side": "support",
        "band_class": None,
        "price_low": adbe_opposite["price_low"],
        "price_high": adbe_opposite["price_high"],
        "band_score": adbe_opposite["quality_score"],
        "distance_bps": _distance_bps(adbe_opposite, null_bar.close),
    }
    assert adbe_row["bands_by_class"] == {"A": 1, "B": 0, "C": 0, "unclassified": 1}
    assert sum(adbe_row["bands_by_class"].values()) == 2


def test_row_order_is_unchanged_by_the_opposite_band_addition(ctx):
    """TC-5: `_row_rank_key` is computed entirely from `band_class`/`distance_bps`/`band_score`/
    `symbol` -- unchanged this iteration (verify via `git diff`, appearing only as unchanged
    CONTEXT) -- neither `opposite_band` nor `bands_by_class` touches it. The ranked-row symbol
    SEQUENCE for this same fixture spread is exactly the sort of `_row_rank_key` over the SAME rows,
    confirming both new fields are a pure addition to row CONTENT, never a reordering."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_HOURLY_FIXTURE))

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    symbols = [r["symbol"] for r in screen["rows"]]
    expected = [r["symbol"] for r in sorted(screen["rows"], key=_row_rank_key)]
    assert symbols == expected
    assert symbols == ["MSFT", "AAPL"], "pin the exact fixture-spread order so a silent reorder is caught"


def test_opposite_band_stays_byte_identical_on_a_recompute_under_identical_pins(ctx, tmp_path):
    """TC-6: mirrors `test_reference_close_stays_byte_identical_on_a_recompute_under_identical_pins`
    for `opposite_band`/`bands_by_class` specifically -- a screen recorded once, then a FRESH
    computation under identical pins, is refused a second write, and the content already on disk
    (read back via `list()`) is byte-identical to the second (unrecorded) computation's
    `opposite_band`/`bands_by_class` on every ranked row."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    screen_store = ScreenStore(tmp_path / "screen")

    first_screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    recorded = screen_store.record(**first_screen)

    second_screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    with pytest.raises(ScreenAlreadyRecorded) as excinfo:
        screen_store.record(**second_screen)
    assert excinfo.value.existing_id == recorded["id"]

    stored_records, errors = screen_store.list()
    assert errors == []
    assert json.dumps(stored_records[0]["rows"], sort_keys=True) == json.dumps(
        second_screen["rows"], sort_keys=True
    )
    aapl_row = next(r for r in stored_records[0]["rows"] if r["symbol"] == "AAPL")
    expected_aapl_row = next(r for r in second_screen["rows"] if r["symbol"] == "AAPL")
    assert aapl_row["opposite_band"] == expected_aapl_row["opposite_band"]
    assert aapl_row["bands_by_class"] == expected_aapl_row["bands_by_class"]


def test_a_legacy_row_recorded_without_opposite_band_fields_serves_them_absent_never_backfilled(
    tmp_path,
):
    """TC-7: the exact shape every screen snapshot recorded BEFORE this iteration has -- ranked rows
    that OMIT `opposite_band`/`bands_by_class` entirely (never merely present-as-`null`) -- mirrors
    the basis/history/reference-close legacy-row precedents for the two new fields. `_record`'s own
    default row carries no such keys at all, so this is true by construction; this test pins that
    contract so a future change cannot silently start defaulting or backfilling legacy rows on read."""
    store = ScreenStore(tmp_path / "screen")
    _record(store)  # `_record`'s own default row carries neither key at all

    records, errors = store.list()
    assert errors == []
    row = records[0]["rows"][0]
    assert "opposite_band" not in row
    assert "bands_by_class" not in row


def test_opposite_band_and_bands_by_class_add_zero_extra_compute_tradability_or_merged_bars_calls(
    ctx, monkeypatch
):
    """TC-10: `opposite_band`/`bands_by_class` are pure selections/counts over the SAME
    `result["bands"]` a symbol's SINGLE `compute_tradability` call already returned -- mirrors
    `test_history_fields_add_zero_extra_merged_bars_calls`'s own call-count-guard style, extended to
    also assert `compute_tradability` itself is invoked exactly once per symbol in a full screen
    walk (never a second call to derive the opposite side), and that the derivation adds ZERO
    `BarStore.merged_bars(symbol, "1d")` calls beyond what iteration 17 (`reference_close`/history)
    already required."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))

    as_of_epoch = _epoch(screen_as_of(SCREEN_DATE))
    merged_calls: list[tuple[str, str]] = []
    original_merged = BarStore.merged_bars

    def _tracked_merged(self, symbol, timeframe):
        merged_calls.append((symbol, timeframe))
        return original_merged(self, symbol, timeframe)

    monkeypatch.setattr(BarStore, "merged_bars", _tracked_merged)

    from app.research.tradability import compute_tradability as _compute_tradability

    _compute_tradability(bar_store, "AAPL", as_of_epoch, CONFIG)
    baseline_1d_calls = sum(1 for symbol, tf in merged_calls if symbol == "AAPL" and tf == "1d")
    merged_calls.clear()

    import app.research.desk_screen as desk_screen_module

    tradability_calls: list[str] = []
    original_tradability = desk_screen_module.compute_tradability

    def _tracked_tradability(store, symbol, as_of_epoch_arg, config):
        tradability_calls.append(symbol)
        return original_tradability(store, symbol, as_of_epoch_arg, config)

    monkeypatch.setattr(desk_screen_module, "compute_tradability", _tracked_tradability)

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    assert any(r["symbol"] == "AAPL" for r in screen["rows"])

    assert tradability_calls.count("AAPL") == 1, (
        "opposite_band/bands_by_class must be derived from the symbol's single existing "
        "compute_tradability call, never a second call"
    )
    full_1d_calls = sum(1 for symbol, tf in merged_calls if symbol == "AAPL" and tf == "1d")
    assert full_1d_calls == baseline_1d_calls + 1, (
        "opposite_band/bands_by_class must add ZERO extra merged_bars calls beyond what "
        "iteration 17's reference_close/history disclosure already required"
    )


# ==================================================================================================
# wall-composition disclosure (goal-desk-iter-23, J-15) -- band_member_count/band_round_number/
# band_member_timeframes, copied/tallied VERBATIM off the SAME `best` band `_select_best_band`
# already returns. Mirrors the opposite-band/bands_by_class suite immediately above.
# ==================================================================================================


def test_band_member_fields_golden_single_member_and_intraday_dominated_rows(ctx, monkeypatch):
    """TC-1/TC-4/TC-5: three controlled ranked rows -- one whose selected band holds a SINGLE
    member (a zero-width `price_low == price_high` band, the goal.md worked example's own #45 SPG
    shape), one whose selected band is dominated by intraday (`1m`/`5m`) members (the worked
    example's own MSFT/AAPL shape), and one "normal" multi-timeframe confluence that is ALSO a
    round-number band -- each proving `band_member_count`/`band_round_number` are copied verbatim
    off the SAME `best` band dict, and `band_member_timeframes` is a plain per-timeframe tally of
    that SAME band's own `members` list, summing to `band_member_count`, with an absent timeframe
    simply missing (never a fabricated zero). Mirrors
    `test_opposite_band_golden_near_far_and_null_class_rows`'s controlled-band monkeypatch style."""
    import app.research.desk_screen as desk_screen_module

    universe_store, bar_store, bar_index, dataset_store = ctx
    single_bar = _daily_bars("AIG", start=date(2026, 6, 18), count=1)[0]
    intraday_bar = _daily_bars("AMGN", start=date(2026, 6, 18), count=1)[0]
    normal_bar = _daily_bars("AMT", start=date(2026, 6, 18), count=1)[0]
    _seed_daily_bars(bar_store, bar_index, [single_bar])
    _seed_daily_bars(bar_store, bar_index, [intraday_bar])
    _seed_daily_bars(bar_store, bar_index, [normal_bar])

    single_basis = _iso_of(single_bar.epoch)
    intraday_basis = _iso_of(intraday_bar.epoch)
    normal_basis = _iso_of(normal_bar.epoch)

    single_member = [{"price": single_bar.close, "timeframe": "1d", "type": "level", "touch_count": 1}]
    aig_best = _band(
        "resistance", single_bar.close, single_bar.close, "A", 10.0,
        members=single_member, round_number=False,
    )

    intraday_members = (
        [{"price": intraday_bar.close, "timeframe": "1m", "type": "level", "touch_count": 1} for _ in range(6)]
        + [{"price": intraday_bar.close, "timeframe": "5m", "type": "level", "touch_count": 1} for _ in range(2)]
        + [{"price": intraday_bar.close, "timeframe": "1d", "type": "level", "touch_count": 1}]
    )
    amgn_best = _band(
        "resistance", intraday_bar.close, intraday_bar.close + 1.0, "B", 5.0,
        members=intraday_members, round_number=False,
    )

    normal_members = (
        [{"price": normal_bar.close, "timeframe": "1d", "type": "level", "touch_count": 1} for _ in range(3)]
        + [{"price": normal_bar.close, "timeframe": "1h", "type": "level", "touch_count": 1} for _ in range(2)]
        + [{"price": normal_bar.close, "timeframe": "4h", "type": "level", "touch_count": 1}]
    )
    amt_best = _band(
        "resistance", normal_bar.close, normal_bar.close + 2.0, "A", 20.0,
        members=normal_members, round_number=True,
    )

    original = desk_screen_module.compute_tradability

    def _tracked(store, symbol, as_of_epoch, config):
        if symbol == "AIG":
            return {"no_bar_series_for_symbol": False, "basis_as_of": single_basis, "bands": [aig_best]}
        if symbol == "AMGN":
            return {"no_bar_series_for_symbol": False, "basis_as_of": intraday_basis, "bands": [amgn_best]}
        if symbol == "AMT":
            return {"no_bar_series_for_symbol": False, "basis_as_of": normal_basis, "bands": [amt_best]}
        return original(store, symbol, as_of_epoch, config)

    monkeypatch.setattr(desk_screen_module, "compute_tradability", _tracked)

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    by_symbol = {r["symbol"]: r for r in screen["rows"]}

    aig_row = by_symbol["AIG"]
    assert aig_row["price_low"] == aig_row["price_high"], "the zero-width band this fixture builds"
    assert aig_row["band_member_count"] == 1
    assert aig_row["band_round_number"] is False
    assert aig_row["band_member_timeframes"] == {"1d": 1}
    assert sum(aig_row["band_member_timeframes"].values()) == aig_row["band_member_count"]

    amgn_row = by_symbol["AMGN"]
    assert amgn_row["band_member_count"] == 9
    assert amgn_row["band_round_number"] is False
    assert amgn_row["band_member_timeframes"] == {"1m": 6, "5m": 2, "1d": 1}
    assert list(amgn_row["band_member_timeframes"].keys()) == ["1m", "5m", "1d"], (
        "key order is first-seen over the band's own already-sorted members list"
    )
    assert sum(amgn_row["band_member_timeframes"].values()) == amgn_row["band_member_count"]

    amt_row = by_symbol["AMT"]
    assert amt_row["band_member_count"] == 6
    assert amt_row["band_round_number"] is True
    assert amt_row["band_member_timeframes"] == {"1d": 3, "1h": 2, "4h": 1}
    assert "1w" not in amt_row["band_member_timeframes"], (
        "a timeframe with no member in this band is simply absent, never a fabricated zero"
    )
    assert sum(amt_row["band_member_timeframes"].values()) == amt_row["band_member_count"]


def test_sum_of_band_member_timeframes_equals_band_member_count_on_every_ranked_row(ctx):
    """TC-3: the sum invariant holds on EVERY ranked row of a REAL (non-monkeypatched) screen --
    not just the controlled golden rows above."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_HOURLY_FIXTURE))

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    assert len(screen["rows"]) >= 1
    for row in screen["rows"]:
        assert sum(row["band_member_timeframes"].values()) == row["band_member_count"]


def test_row_order_is_unchanged_by_the_band_member_fields_addition(ctx):
    """TC-7: `_row_rank_key` is computed entirely from `band_class`/`distance_bps`/`band_score`/
    `symbol` -- unchanged this iteration (verify via `git diff`, appearing only as unchanged
    CONTEXT) -- none of `band_member_count`/`band_round_number`/`band_member_timeframes` touches
    it. Mirrors `test_row_order_is_unchanged_by_the_opposite_band_addition`."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_DAILY_FIXTURE))
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_HOURLY_FIXTURE))

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    symbols = [r["symbol"] for r in screen["rows"]]
    expected = [r["symbol"] for r in sorted(screen["rows"], key=_row_rank_key)]
    assert symbols == expected
    assert symbols == ["MSFT", "AAPL"], "pin the exact fixture-spread order so a silent reorder is caught"


def test_band_member_fields_stay_byte_identical_on_a_recompute_under_identical_pins(ctx, tmp_path):
    """TC-8: mirrors `test_opposite_band_stays_byte_identical_on_a_recompute_under_identical_pins`
    for band_member_count/band_round_number/band_member_timeframes specifically -- a screen
    recorded once, then a FRESH computation under identical pins, is refused a second write, and
    the content already on disk is byte-identical to the second (unrecorded) computation's fields
    on every ranked row."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    screen_store = ScreenStore(tmp_path / "screen")

    first_screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    recorded = screen_store.record(**first_screen)

    second_screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    with pytest.raises(ScreenAlreadyRecorded) as excinfo:
        screen_store.record(**second_screen)
    assert excinfo.value.existing_id == recorded["id"]

    stored_records, errors = screen_store.list()
    assert errors == []
    assert json.dumps(stored_records[0]["rows"], sort_keys=True) == json.dumps(
        second_screen["rows"], sort_keys=True
    )
    aapl_row = next(r for r in stored_records[0]["rows"] if r["symbol"] == "AAPL")
    expected_aapl_row = next(r for r in second_screen["rows"] if r["symbol"] == "AAPL")
    assert aapl_row["band_member_count"] == expected_aapl_row["band_member_count"]
    assert aapl_row["band_round_number"] == expected_aapl_row["band_round_number"]
    assert aapl_row["band_member_timeframes"] == expected_aapl_row["band_member_timeframes"]


def test_a_legacy_row_recorded_without_band_member_fields_serves_them_absent_never_backfilled(
    tmp_path,
):
    """TC-9: the exact shape every screen snapshot recorded BEFORE this iteration has -- ranked
    rows that OMIT band_member_count/band_round_number/band_member_timeframes entirely (never
    merely present-as-`null`) -- mirrors the basis/history/reference-close/opposite-band legacy-row
    precedents. `_record`'s own default row carries no such keys at all, so this is true by
    construction; this test pins that contract so a future change cannot silently start
    defaulting or backfilling legacy rows on read."""
    store = ScreenStore(tmp_path / "screen")
    _record(store)  # `_record`'s own default row carries none of the three keys at all

    records, errors = store.list()
    assert errors == []
    row = records[0]["rows"][0]
    assert "band_member_count" not in row
    assert "band_round_number" not in row
    assert "band_member_timeframes" not in row


def test_band_member_fields_add_zero_extra_compute_tradability_or_merged_bars_calls(ctx, monkeypatch):
    """TC-6: band_member_count/band_round_number/band_member_timeframes are a pure copy/tally over
    the SAME `best` band dict a symbol's SINGLE `compute_tradability` call already returned --
    mirrors `test_opposite_band_and_bands_by_class_add_zero_extra_compute_tradability_or_merged_bars_calls`:
    zero additional `compute_tradability` calls per symbol, zero additional `BarStore.merged_bars`
    calls beyond what iteration 17/18's disclosures already required."""
    universe_store, bar_store, bar_index, dataset_store = ctx
    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))

    as_of_epoch = _epoch(screen_as_of(SCREEN_DATE))
    merged_calls: list[tuple[str, str]] = []
    original_merged = BarStore.merged_bars

    def _tracked_merged(self, symbol, timeframe):
        merged_calls.append((symbol, timeframe))
        return original_merged(self, symbol, timeframe)

    monkeypatch.setattr(BarStore, "merged_bars", _tracked_merged)

    from app.research.tradability import compute_tradability as _compute_tradability

    _compute_tradability(bar_store, "AAPL", as_of_epoch, CONFIG)
    baseline_1d_calls = sum(1 for symbol, tf in merged_calls if symbol == "AAPL" and tf == "1d")
    merged_calls.clear()

    import app.research.desk_screen as desk_screen_module

    tradability_calls: list[str] = []
    original_tradability = desk_screen_module.compute_tradability

    def _tracked_tradability(store, symbol, as_of_epoch_arg, config):
        tradability_calls.append(symbol)
        return original_tradability(store, symbol, as_of_epoch_arg, config)

    monkeypatch.setattr(desk_screen_module, "compute_tradability", _tracked_tradability)

    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
    aapl_row = next(r for r in screen["rows"] if r["symbol"] == "AAPL")
    assert "band_member_count" in aapl_row

    assert tradability_calls.count("AAPL") == 1, (
        "band_member_count/band_round_number/band_member_timeframes must be derived from the "
        "symbol's single existing compute_tradability call, never a second call"
    )
    full_1d_calls = sum(1 for symbol, tf in merged_calls if symbol == "AAPL" and tf == "1d")
    assert full_1d_calls == baseline_1d_calls + 1, (
        "band_member_count/band_round_number/band_member_timeframes must add ZERO extra "
        "merged_bars calls beyond what iteration 17/18's disclosures already required"
    )


# ==================================================================================================
# screen ?id= read (goal-desk-iter-16, J-12) -- individual addressability, including an EARLIER
# same-`screen_date` recording that `?date=` (which always resolves `matching[-1]`) can never reach.
# ==================================================================================================


@pytest.fixture
def screen_route_ctx(tmp_path, monkeypatch):
    """A live-routed screen store, scoped entirely under `tmp_path` (never `apps/backend/.data`):
    same `TestClient`/`ResearchRegistry` wiring `test_aapl_row_cross_checks_byte_identical_to_the_
    real_tradability_route` above already uses inline, lifted into a shared fixture for this
    section's four route-level `?id=` tests."""
    from fastapi.testclient import TestClient

    from app.main import app, get_market_adapter, manager as ws_manager
    from app.research.routes import ResearchRegistry, set_registry
    from app.research.store import JournalStore

    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_DIR", str(tmp_path / "screen"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    with TestClient(app) as client:
        yield client, tmp_path
    for ticker in list(ws_manager._engines.keys()):
        ws_manager.stop(ticker)
    set_registry(None)
    app.dependency_overrides.pop(get_market_adapter, None)
    store.close()


def _plant_same_date_pair(screen_dir) -> tuple[dict, dict, dict]:
    """Two records sharing `screen_date` but differing `bar_store_signature` -- the REAL shape
    goal.md's own worked example names (a pre-/post-repair pair whose reconciliation changed
    coverage, not the requested date). Returns `(store, earlier, later)`, `earlier`/`later`
    determined by the store's OWN `created_utc`-then-`id` sort (never assumed from call order, since
    two same-microsecond wall-clock writes would otherwise make that assumption flaky)."""
    store = ScreenStore(screen_dir)
    _record(store, screen_date="2026-07-27", as_of="2026-07-27T23:59:59Z", bar_store_signature="a" * 16)
    _record(store, screen_date="2026-07-27", as_of="2026-07-27T23:59:59Z", bar_store_signature="b" * 16)
    records, errors = store.list()
    assert errors == []
    matching = [r for r in records if r["screen_date"] == "2026-07-27"]
    assert len(matching) == 2
    return store, matching[0], matching[-1]


def test_get_screen_by_id_returns_the_exact_record_byte_identical_to_disk(screen_route_ctx):
    """TC-1: `?id=<the earlier id>` returns that exact record, byte-identical to its own file on
    disk -- same `id`/`screen_date`/`as_of`/`rows`/`skipped` -- distinct from what `?date=` (which
    still resolves only the later recording, TC-2 below) would return for the same date."""
    client, tmp_path = screen_route_ctx
    _store, earlier, _later = _plant_same_date_pair(tmp_path / "screen")

    r = client.get("/research/desk/screen", params={"id": earlier["id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["screen"] == earlier

    on_disk = json.loads((tmp_path / "screen" / f"{earlier['id']}.json").read_text())
    assert body["screen"] == on_disk["record"]["meta"]


def test_get_screen_by_date_alone_still_resolves_only_the_later_recording(screen_route_ctx):
    """TC-2: `?date=` (no `?id=`) is byte-unchanged by this iteration -- it still serves ONLY the
    later of the two same-date recordings."""
    client, tmp_path = screen_route_ctx
    _store, earlier, later = _plant_same_date_pair(tmp_path / "screen")

    r = client.get("/research/desk/screen", params={"date": "2026-07-27"})
    assert r.status_code == 200
    body = r.json()
    assert body["screen"]["id"] == later["id"]
    assert body["screen"]["id"] != earlier["id"]
    assert body["screen"] == later


def test_get_screen_by_unknown_id_is_an_honest_null_never_a_404(screen_route_ctx):
    """TC-3: mirrors the `?date=` no-match convention -- an unrecognized `id` is `{"screen": null}`
    at HTTP 200, never a 404."""
    client, tmp_path = screen_route_ctx
    _plant_same_date_pair(tmp_path / "screen")

    r = client.get("/research/desk/screen", params={"id": "does-not-exist"})
    assert r.status_code == 200
    assert r.json() == {"screen": None}


def test_get_screen_with_both_id_and_date_is_an_honest_4xx_refusal(screen_route_ctx):
    """TC-4: supplying both query params is refused explicitly -- never a silent precedence rule
    between the two lookup modes."""
    client, tmp_path = screen_route_ctx
    _store, earlier, _later = _plant_same_date_pair(tmp_path / "screen")

    r = client.get(
        "/research/desk/screen", params={"id": earlier["id"], "date": earlier["screen_date"]}
    )
    assert 400 <= r.status_code < 500
    detail = r.json()["detail"]
    assert "id" in detail and "date" in detail


def test_get_screen_id_lookup_never_recomputes_and_the_meta_only_list_is_unaffected(screen_route_ctx):
    """`?id=` is a plain read exactly like `?date=` (TC-6's own "recomputes nothing" clause,
    extended): the no-param meta-only list/`latest`/`integrity_errors` shape is untouched by this
    iteration, and issuing an `?id=` lookup leaves the store's own files byte-unchanged."""
    client, tmp_path = screen_route_ctx
    _store, earlier, later = _plant_same_date_pair(tmp_path / "screen")
    earlier_path = tmp_path / "screen" / f"{earlier['id']}.json"
    before = earlier_path.read_bytes()

    client.get("/research/desk/screen", params={"id": earlier["id"]})

    assert earlier_path.read_bytes() == before

    listed = client.get("/research/desk/screen").json()
    assert {row["id"] for row in listed["screens"]} == {earlier["id"], later["id"]}
    assert listed["latest"]["id"] == later["id"]
    assert listed["integrity_errors"] == []


def test_sha256_of_every_universe_screen_topup_run_reconcile_run_file_is_unchanged_by_this_iteration(
    screen_route_ctx,
):
    """TC-15: this iteration is a pure additive-READ (screen's new `?id=` branch) plus a
    response-shape-only disclosure (`integrity_errors` surfaced on the two run-ledger GETs) --
    neither touches a single byte on disk. A SHA-256 checksum of EVERY universe/screen/topup-run/
    reconcile-run file, taken before and after exercising every GET this iteration touched
    (including the new `?id=`/`?date=` reads and both ledger GETs, each called more than once), must
    come back identical -- proving nothing was backfilled, rewritten, or re-tagged."""
    import hashlib

    from app.research.desk_index_reconcile import ReconcileRunStore
    from app.research.desk_routes import get_reconcile_run_store, get_topup_run_store
    from app.research.desk_topup_log import TopupRunStore

    client, tmp_path = screen_route_ctx

    UniverseStore(tmp_path / "universe").record(
        members=["AAPL", "MSFT"], raw_members={"AAPL": "AAPL", "MSFT": "MSFT"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    _screen_store, earlier, later = _plant_same_date_pair(tmp_path / "screen")

    topup_store: TopupRunStore = get_topup_run_store()
    topup_store.record(
        universe_snapshot_id="universe-2026-07-25-49b33fa31680",
        requested_window={"start": "2024-07-28T00:00:00Z", "end": "2026-07-28T00:00:00Z"},
        config_fingerprint=CONFIG.config_fingerprint(),
        started_utc="2026-07-28T09:00:00.000000Z", finished_utc="2026-07-28T09:05:00.000000Z",
        state="done", pairs_total=1,
        outcomes=[{"symbol": "AAA", "timeframe": "1h", "outcome": "fetched", "detail": None}],
    )

    reconcile_store: ReconcileRunStore = get_reconcile_run_store()
    empty_drift = {"unindexed_series": [], "orphan_index_rows": [], "stale_checksum_rows": []}
    reconcile_store.record(
        config_fingerprint=CONFIG.config_fingerprint(),
        started_utc="2026-07-28T09:00:00.000000Z", finished_utc="2026-07-28T09:05:00.000000Z",
        state="done", series_on_disk=0, rows_indexed_before=0, rows_indexed_after=0,
        drift_before=empty_drift, drift_after=empty_drift, store_errors=[],
    )

    tracked_dirs = [
        tmp_path / "universe", tmp_path / "screen", topup_store.root, reconcile_store.root,
    ]

    def _checksums() -> dict[str, str]:
        return {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for directory in tracked_dirs
            for path in sorted(directory.glob("*.json"))
        }

    before = _checksums()
    assert len(before) == 5  # 1 universe + 2 screen + 1 topup-run + 1 reconcile-run

    client.get("/research/desk/screen")
    client.get("/research/desk/screen", params={"date": "2026-07-27"})
    client.get("/research/desk/screen", params={"id": earlier["id"]})
    client.get("/research/desk/screen", params={"id": later["id"]})
    client.get("/research/desk/screen", params={"id": "does-not-exist"})
    client.get("/research/desk/topup/runs")
    client.get("/research/desk/topup/runs")
    client.get("/research/desk/coverage/reconcile/runs")
    client.get("/research/desk/coverage/reconcile/runs")

    after = _checksums()
    assert after == before
