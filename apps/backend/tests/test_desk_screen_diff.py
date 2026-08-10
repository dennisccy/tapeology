"""``desk_screen_diff.py`` (Era B "The Desk", J-20) -- the screen-comparison computation over
planted, scoped ``ScreenStore`` snapshots (goal.md step 6: "Backend tests over planted scoped
snapshots"). Synthetic ``AAA``/``BBB``/``CCC``... symbols are used throughout (the
``test_desk_screen_compute.py``/``test_desk_topup_compute.py`` convention for generic plumbing
tests over planted store records) -- lessons.md iter-2's "never a synthetic symbol for a clause
naming a REAL symbol" applies to ``compute_screen``'s real-tradability cross-checks, not to this
module's pure row-diffing logic, which names no real symbol in its own acceptance criteria.

Route-level tests (``GET /research/desk/screen/compare``) live in the second half of this file,
mirroring ``test_desk_screen.py``'s ``screen_route_ctx``/``_plant_same_date_pair`` fixtures.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from app.config import CONFIG
from app.research.desk_screen import ScreenStore
from app.research.desk_screen_diff import (
    ScreenDiffSelfCompareError,
    compute_screen_diff,
)

UNIVERSE_SNAPSHOT_ID = "universe-2026-01-01-000000000000"
BAR_STORE_SIGNATURE = "aaaaaaaaaaaaaaaa"


def _row(symbol: str, *, side="resistance", band_class="B", distance_bps=10.0,
         basis_as_of="2026-01-01T04:00:00.000000Z", omit: tuple[str, ...] = ()) -> dict:
    """A minimal ranked-row dict carrying only the four fields this module discloses
    (``side``/``band_class``/``distance_bps``/``basis_as_of``) plus ``symbol`` -- ``ScreenStore``
    performs no row-shape validation, so a planted test row never needs the full
    ``compute_screen``-produced shape. ``omit`` drops named keys entirely (the legacy-row
    precedent, TC-10)."""
    row = {
        "symbol": symbol, "side": side, "band_class": band_class, "distance_bps": distance_bps,
        "basis_as_of": basis_as_of,
    }
    for key in omit:
        row.pop(key, None)
    return row


def _skip(symbol: str, reason: str = "no_bars") -> dict:
    return {"symbol": symbol, "skipped": True, "reason": reason}


def _plant(store: ScreenStore, *, screen_date: str, rows: list[dict], skipped: list[dict] | None = None,
           bar_store_signature: str = BAR_STORE_SIGNATURE) -> dict:
    return store.record(
        screen_date=screen_date, as_of=f"{screen_date}T23:59:59Z",
        universe_snapshot_id=UNIVERSE_SNAPSHOT_ID, config_fingerprint=CONFIG.config_fingerprint(),
        bar_store_signature=bar_store_signature, rows=rows, skipped=skipped or [],
    )


@pytest.fixture
def store(tmp_path) -> ScreenStore:
    return ScreenStore(tmp_path / "screen")


def _row_by_symbol(result: dict, symbol: str) -> dict:
    matching = [r for r in result["rows"] if r["symbol"] == symbol]
    assert len(matching) == 1, f"expected exactly one row for {symbol!r}, got {len(matching)}"
    return matching[0]


# ==================================================================================================
# TC-1: identical ranked rows report zero changes
# ==================================================================================================


def test_identical_ranked_rows_report_zero_changes(store):
    _plant(store, screen_date="2026-01-01", rows=[_row("AAA"), _row("BBB", side="support")])
    later = _plant(store, screen_date="2026-01-02", rows=[_row("AAA"), _row("BBB", side="support")])

    result = compute_screen_diff(store, later["id"])

    assert result["identical"] is True
    assert result["counts"] == {
        "compared": 2, "rank_changed": 0, "side_changed": 0, "entered": 0, "left": 0,
    }
    assert result["base_resolution"] == "default_prior_date"
    for row in result["rows"]:
        assert row["status"] == "compared"
        assert row["rank_change"] == 0
        assert row["compare_side"] == row["base_side"]
        assert row["compare_band_class"] == row["base_band_class"]
        assert row["compare_distance_bps"] == row["base_distance_bps"]
        assert row["compare_basis_as_of"] == row["base_basis_as_of"]


# ==================================================================================================
# TC-2/TC-4/TC-5 (compound, goal.md's own worked acceptance): a moved rank, a flipped side, an
# entered symbol, and a left symbol -- each reported EXACTLY ONCE with both recorded values verbatim.
# ==================================================================================================


def test_moved_rank_flipped_side_entered_and_left_each_report_exactly_once(store):
    base = _plant(
        store, screen_date="2026-01-01",
        rows=[
            _row("AAA", side="resistance", band_class="A", distance_bps=5.0),   # rank 1
            _row("BBB", side="support", band_class="B", distance_bps=20.0),    # rank 2
            _row("CCC", side="support", band_class="C", distance_bps=50.0),    # rank 3 -- will "leave"
        ],
    )
    compare = _plant(
        store, screen_date="2026-01-02",
        rows=[
            _row("BBB", side="resistance", band_class="B", distance_bps=20.0),  # rank 1 -- flipped side
            _row("AAA", side="resistance", band_class="A", distance_bps=5.0),   # rank 2 -- moved from 1
            _row("DDD", side="support", band_class="C", distance_bps=99.0),     # rank 3 -- "entered"
        ],
    )

    result = compute_screen_diff(store, compare["id"], base["id"])

    assert result["base_resolution"] == "explicit"
    assert result["identical"] is False
    assert len(result["rows"]) == 4  # AAA, BBB, DDD (compare order) + CCC (left)

    aaa = _row_by_symbol(result, "AAA")
    assert aaa["status"] == "compared"
    assert aaa["base_rank"] == 1 and aaa["compare_rank"] == 2
    assert aaa["rank_change"] == 1
    assert aaa["compare_side"] == aaa["base_side"] == "resistance"

    bbb = _row_by_symbol(result, "BBB")
    assert bbb["status"] == "compared"
    assert bbb["base_rank"] == 2 and bbb["compare_rank"] == 1
    assert bbb["rank_change"] == -1
    assert bbb["base_side"] == "support" and bbb["compare_side"] == "resistance"

    ddd = _row_by_symbol(result, "DDD")
    assert ddd["status"] == "entered"
    assert ddd["base_rank"] is None and ddd["compare_rank"] == 3
    assert ddd["compare_side"] == "support" and ddd["base_side"] is None
    assert ddd["skip_reason"] is None  # base doesn't mention DDD at all

    ccc = _row_by_symbol(result, "CCC")
    assert ccc["status"] == "left"
    assert ccc["compare_rank"] is None and ccc["base_rank"] == 3
    assert ccc["base_side"] == "support" and ccc["compare_side"] is None
    assert ccc["skip_reason"] is None  # compare doesn't mention CCC at all

    assert result["counts"] == {
        "compared": 2, "rank_changed": 2, "side_changed": 1, "entered": 1, "left": 1,
    }


# ==================================================================================================
# TC-4: an entered symbol carries the base's own recorded skip reason when it has one
# ==================================================================================================


def test_entered_symbol_carries_the_base_skip_reason_when_it_has_one(store):
    base = _plant(store, screen_date="2026-01-01", rows=[_row("AAA")], skipped=[_skip("EEE", "no_bars")])
    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA"), _row("EEE")])

    result = compute_screen_diff(store, compare["id"], base["id"])

    eee = _row_by_symbol(result, "EEE")
    assert eee["status"] == "entered"
    assert eee["skip_reason"] == "no_bars"


# ==================================================================================================
# TC-5: a left symbol carries the compare's own recorded skip reason when it has one
# ==================================================================================================


def test_left_symbol_carries_the_compare_skip_reason_when_it_has_one(store):
    base = _plant(store, screen_date="2026-01-01", rows=[_row("AAA"), _row("FFF")])
    compare = _plant(
        store, screen_date="2026-01-02", rows=[_row("AAA")], skipped=[_skip("FFF", "no_basis")]
    )

    result = compute_screen_diff(store, compare["id"], base["id"])

    fff = _row_by_symbol(result, "FFF")
    assert fff["status"] == "left"
    assert fff["skip_reason"] == "no_basis"


# ==================================================================================================
# TC-3: the oldest recorded snapshot reports the honest no-earlier-screen state
# ==================================================================================================


def test_oldest_recorded_snapshot_reports_the_honest_no_earlier_screen_state(store):
    only = _plant(store, screen_date="2026-01-01", rows=[_row("AAA")])

    result = compute_screen_diff(store, only["id"])

    assert result["base"] is None
    assert result["base_resolution"] == "none_earlier"
    assert result["rows"] == []
    assert result["counts"] == {"compared": 0, "rank_changed": 0, "side_changed": 0, "entered": 0, "left": 0}
    assert result["compare"]["id"] == only["id"]


# ==================================================================================================
# TC-6: the same two ids requested twice in succession produce a byte-identical body
# ==================================================================================================


def test_the_same_two_ids_requested_twice_produce_a_byte_identical_body(store):
    base = _plant(store, screen_date="2026-01-01", rows=[_row("AAA")])
    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA")])

    first = compute_screen_diff(store, compare["id"], base["id"])
    second = compute_screen_diff(store, compare["id"], base["id"])

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


# ==================================================================================================
# TC-7: an unknown snapshot id is an honest null, never an error
# ==================================================================================================


def test_unknown_compare_id_is_an_honest_null(store):
    _plant(store, screen_date="2026-01-01", rows=[_row("AAA")])

    result = compute_screen_diff(store, "does-not-exist")

    assert result["compare"] is None
    assert result["base"] is None
    assert result["base_resolution"] is None
    assert result["rows"] == []
    assert result["identical"] is False


def test_unknown_explicit_base_id_is_an_honest_null_but_stays_explicit(store):
    """An explicit ``base=`` that does not resolve is distinct from "no earlier snapshot exists at
    all" -- ``base_resolution`` stays ``"explicit"`` (a specific base WAS asked for; it just isn't
    there), never silently reclassified as ``"none_earlier"``."""
    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA")])

    result = compute_screen_diff(store, compare["id"], "does-not-exist")

    assert result["base"] is None
    assert result["base_resolution"] == "explicit"
    assert result["rows"] == []


# ==================================================================================================
# TC-8: a snapshot compared with itself is an honest refusal, never a silent zero-diff no-op
# ==================================================================================================


def test_self_compare_is_refused(store):
    only = _plant(store, screen_date="2026-01-01", rows=[_row("AAA")])

    with pytest.raises(ScreenDiffSelfCompareError) as excinfo:
        compute_screen_diff(store, only["id"], only["id"])
    assert only["id"] in str(excinfo.value)


def test_self_compare_is_refused_even_when_the_id_does_not_resolve():
    """The self-compare check runs BEFORE any store lookup -- ``id == base`` is refused
    unconditionally, never silently falling through to the not-found branch."""
    store = ScreenStore.__new__(ScreenStore)  # never touched -- proves no lookup precedes the check
    with pytest.raises(ScreenDiffSelfCompareError):
        compute_screen_diff(store, "same-id", "same-id")


# ==================================================================================================
# TC-9: zero compute_tradability / BarStore / bar_index / dataset read of any kind -- structural,
# not merely behavioral: this module never imports any of those names in the first place.
# ==================================================================================================


def test_module_imports_no_store_or_compute_dependency():
    import app.research.desk_screen_diff as module

    for forbidden_name in ("BarStore", "compute_tradability", "BarIndex", "DatasetStore"):
        assert not hasattr(module, forbidden_name), (
            f"desk_screen_diff.py imports {forbidden_name!r} -- it must be structurally incapable "
            "of a BarStore/bar_index/dataset read or a compute_tradability call, since it never "
            "receives a store reference of any kind"
        )


def test_compute_screen_diff_reads_only_the_snapshots_it_discloses(store, monkeypatch):
    """A call-count instrumentation counterpart to the structural test above (mirrors
    ``test_bar_store_signature_issues_zero_bar_store_calls``'s style). This module reads its store
    ONLY through the targeted reads, and never walks it: an explicit base is two ``get``s, and a
    default base is one ``get`` plus one ``find_latest_before``. ``list()`` -- which verifies every
    recorded snapshot to hand back two -- must not be called at all, since a comparison is a plain
    read of the two snapshots it names in its own response."""
    base = _plant(store, screen_date="2026-01-01", rows=[_row("AAA")])
    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA")])

    calls: list[str] = []
    originals = {
        name: getattr(ScreenStore, name) for name in ("list", "get", "find_latest_before")
    }

    def _track(name):
        def _tracked(self, *args, **kwargs):
            calls.append(name)
            return originals[name](self, *args, **kwargs)

        return _tracked

    for name in originals:
        monkeypatch.setattr(ScreenStore, name, _track(name))

    compute_screen_diff(store, compare["id"], base["id"])
    assert calls == ["get", "get"]

    calls.clear()
    compute_screen_diff(store, compare["id"])
    assert calls == ["get", "find_latest_before"]
    assert "list" not in calls


# ==================================================================================================
# TC-10: a legacy base row missing basis_as_of is reported absent, never derived or backfilled
# ==================================================================================================


def test_legacy_base_row_missing_basis_as_of_is_reported_absent_never_derived(store):
    base = _plant(store, screen_date="2026-01-01", rows=[_row("AAA", omit=("basis_as_of",))])
    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA", basis_as_of="2026-01-02T04:00:00.000000Z")])

    result = compute_screen_diff(store, compare["id"], base["id"])

    aaa = _row_by_symbol(result, "AAA")
    assert aaa["base_basis_as_of"] is None
    assert aaa["compare_basis_as_of"] == "2026-01-02T04:00:00.000000Z"


# ==================================================================================================
# Row order: each snapshot's own served order, never re-sorted
# ==================================================================================================


def test_rows_use_each_snapshots_own_served_order_never_resorted(store):
    base = _plant(store, screen_date="2026-01-01", rows=[_row("ZZZ"), _row("MMM")])  # deliberately non-alpha
    compare = _plant(store, screen_date="2026-01-02", rows=[_row("BBB"), _row("ZZZ"), _row("AAA")])

    result = compute_screen_diff(store, compare["id"], base["id"])

    symbols = [r["symbol"] for r in result["rows"]]
    # compare-ranked symbols first, in compare's own served order (BBB, ZZZ, AAA), then base-only
    # ("left") symbols in base's own served order (MMM, since ZZZ was already emitted above).
    assert symbols == ["BBB", "ZZZ", "AAA", "MMM"]


# ==================================================================================================
# Default base resolution -- greatest strictly-earlier screen_date, ties broken by later created_utc
# ==================================================================================================


def test_default_base_picks_the_greatest_strictly_earlier_screen_date(store):
    _plant(store, screen_date="2026-01-01", rows=[_row("AAA")])
    middle = _plant(store, screen_date="2026-01-05", rows=[_row("AAA")])
    compare = _plant(store, screen_date="2026-01-10", rows=[_row("AAA")])

    result = compute_screen_diff(store, compare["id"])

    assert result["base"]["id"] == middle["id"]
    assert result["base_resolution"] == "default_prior_date"


def test_default_base_tie_break_prefers_the_later_created_utc_among_same_earlier_date(store):
    _plant(store, screen_date="2026-01-01", rows=[_row("AAA")], bar_store_signature="a" * 16)
    later_same_date = _plant(
        store, screen_date="2026-01-01", rows=[_row("AAA")], bar_store_signature="b" * 16
    )
    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA")])

    result = compute_screen_diff(store, compare["id"])

    assert result["base"]["id"] == later_same_date["id"]


def test_ranked_count_and_skipped_count_are_plain_lengths(store):
    base = _plant(
        store, screen_date="2026-01-01", rows=[_row("AAA"), _row("BBB")],
        skipped=[_skip("CCC"), _skip("DDD"), _skip("EEE")],
    )
    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA")], skipped=[])

    result = compute_screen_diff(store, compare["id"], base["id"])

    assert result["base"]["ranked_count"] == 2
    assert result["base"]["skipped_count"] == 3
    assert result["compare"]["ranked_count"] == 1
    assert result["compare"]["skipped_count"] == 0


def test_snapshot_meta_carries_every_named_field_verbatim(store):
    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA")])

    result = compute_screen_diff(store, compare["id"])

    meta = result["compare"]
    assert meta["id"] == compare["id"]
    assert meta["screen_date"] == compare["screen_date"]
    assert meta["as_of"] == compare["as_of"]
    assert meta["created_utc"] == compare["created_utc"]
    assert meta["bar_store_signature"] == compare["bar_store_signature"]
    assert meta["universe_snapshot_id"] == compare["universe_snapshot_id"]


def test_desk_screen_diff_module_adds_no_config_field():
    """TC-16: the fingerprint pin stays unchanged by this iteration; this module introduces zero
    new Config fields by construction (no import of a new field anywhere)."""
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"


# ==================================================================================================
# Route-level tests -- GET /research/desk/screen/compare, mirroring test_desk_screen.py's
# screen_route_ctx / _plant_same_date_pair fixtures.
# ==================================================================================================


@pytest.fixture
def screen_route_ctx(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app, get_market_adapter, manager as ws_manager
    from app.research.routes import ResearchRegistry, set_registry
    from app.research.store import JournalStore

    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_DIR", str(tmp_path / "screen"))
    journal = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(journal, CONFIG)
    set_registry(registry)
    with TestClient(app) as client:
        yield client, tmp_path
    for ticker in list(ws_manager._engines.keys()):
        ws_manager.stop(ticker)
    set_registry(None)
    app.dependency_overrides.pop(get_market_adapter, None)
    journal.close()


def test_route_returns_the_same_body_compute_screen_diff_would(screen_route_ctx):
    client, tmp_path = screen_route_ctx
    route_store = ScreenStore(tmp_path / "screen")
    base = _plant(route_store, screen_date="2026-01-01", rows=[_row("AAA")])
    compare = _plant(route_store, screen_date="2026-01-02", rows=[_row("AAA")])

    expected = compute_screen_diff(route_store, compare["id"], base["id"])

    r = client.get(
        "/research/desk/screen/compare", params={"id": compare["id"], "base": base["id"]}
    )
    assert r.status_code == 200
    assert r.json() == expected


def test_route_default_base_omits_the_base_param(screen_route_ctx):
    client, tmp_path = screen_route_ctx
    route_store = ScreenStore(tmp_path / "screen")
    base = _plant(route_store, screen_date="2026-01-01", rows=[_row("AAA")])
    compare = _plant(route_store, screen_date="2026-01-02", rows=[_row("AAA")])

    r = client.get("/research/desk/screen/compare", params={"id": compare["id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["base"]["id"] == base["id"]
    assert body["base_resolution"] == "default_prior_date"


def test_route_unknown_id_is_http_200_never_a_404_or_500(screen_route_ctx):
    client, _tmp_path = screen_route_ctx
    r = client.get("/research/desk/screen/compare", params={"id": "does-not-exist"})
    assert r.status_code == 200
    assert r.json()["compare"] is None


def test_route_self_compare_is_an_honest_4xx_refusal(screen_route_ctx):
    client, tmp_path = screen_route_ctx
    route_store = ScreenStore(tmp_path / "screen")
    only = _plant(route_store, screen_date="2026-01-01", rows=[_row("AAA")])

    r = client.get(
        "/research/desk/screen/compare", params={"id": only["id"], "base": only["id"]}
    )
    assert 400 <= r.status_code < 500
    assert "itself" in r.json()["detail"]


def test_route_missing_id_param_is_a_422(screen_route_ctx):
    client, _tmp_path = screen_route_ctx
    r = client.get("/research/desk/screen/compare")
    assert r.status_code == 422


def test_route_never_calls_compute_tradability_or_reads_the_bar_store(screen_route_ctx, monkeypatch):
    """TC-9 at the request level: instrumented exactly like ``test_bar_store_signature_issues_
    zero_bar_store_calls`` -- a real compare request through the actual FastAPI route issues zero
    ``compute_tradability`` calls and zero ``BarStore`` reads."""
    import app.research.tradability as tradability_module
    from app.research.bars import BarStore

    client, tmp_path = screen_route_ctx
    route_store = ScreenStore(tmp_path / "screen")
    base = _plant(route_store, screen_date="2026-01-01", rows=[_row("AAA")])
    compare = _plant(route_store, screen_date="2026-01-02", rows=[_row("AAA")])

    calls: list[str] = []
    original_tradability = tradability_module.compute_tradability
    original_list = BarStore.list
    original_get = BarStore.get

    def _tracked_tradability(*args, **kwargs):
        calls.append("compute_tradability")
        return original_tradability(*args, **kwargs)

    def _tracked_list(self, *args, **kwargs):
        calls.append("BarStore.list")
        return original_list(self, *args, **kwargs)

    def _tracked_get(self, *args, **kwargs):
        calls.append("BarStore.get")
        return original_get(self, *args, **kwargs)

    monkeypatch.setattr(tradability_module, "compute_tradability", _tracked_tradability)
    monkeypatch.setattr(BarStore, "list", _tracked_list)
    monkeypatch.setattr(BarStore, "get", _tracked_get)

    r = client.get(
        "/research/desk/screen/compare", params={"id": compare["id"], "base": base["id"]}
    )

    assert r.status_code == 200
    assert calls == []


def test_route_get_writes_nothing_sha256_of_every_screen_file_unchanged(screen_route_ctx):
    """The GET writes nothing (goal.md step 3): a SHA-256 checksum of every screen snapshot file on
    disk, taken before and after exercising the compare endpoint several times (including the
    unknown-id and self-compare-refusal branches), must come back identical."""
    client, tmp_path = screen_route_ctx
    route_store = ScreenStore(tmp_path / "screen")
    base = _plant(route_store, screen_date="2026-01-01", rows=[_row("AAA")])
    compare = _plant(route_store, screen_date="2026-01-02", rows=[_row("AAA")])

    screen_dir = tmp_path / "screen"

    def _checksums() -> dict[str, str]:
        return {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(screen_dir.glob("*.json"))
        }

    before = _checksums()
    assert len(before) == 2

    client.get("/research/desk/screen/compare", params={"id": compare["id"], "base": base["id"]})
    client.get("/research/desk/screen/compare", params={"id": compare["id"]})
    client.get("/research/desk/screen/compare", params={"id": "does-not-exist"})
    client.get("/research/desk/screen/compare", params={"id": compare["id"], "base": compare["id"]})

    after = _checksums()
    assert after == before
