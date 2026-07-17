"""The ``GET /research/setups`` + ``GET /research/setups/{id}`` endpoints (era-5B capability 2,
J-02) -- route-level integration. Mirrors ``test_tradability_api.py``'s ``ctx`` fixture (TestClient
+ temp bar dir): the committed real AAPL fixtures are seeded directly into the temp bar dir (the
``test_tradability_api.py`` / ``test_mcp_server.py`` technique), then the REAL routes are read --
the full request path, not a direct module call (``test_setups.py`` covers the pure computation's
exact values in isolation, including the SAME pinned 2026-06-22 event this file re-proves through
HTTP). Routes read the process-global ``CONFIG`` (never a per-request override, mirroring
``get_tradability``/``get_levels``), so every route-level fixture here must work with the SHIPPED
default ``setups_panel_symbols`` (the real 12-symbol panel) -- AAPL is the only panel symbol with
bars seeded, so every other panel symbol honestly contributes zero events.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager
from app.providers.adapters.base import RawBar
from app.research.bars import BarStore
from app.research.datasets import DatasetStore
from app.research.routes import ResearchRegistry, set_registry
from app.research.setups import compute_setups
from app.research.store import JournalStore

YAHOO_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "yahoo"
AAPL_DAILY_FIXTURE = "AAPL_1d_20260101_20260626.json"
AAPL_5M_SETUPS_FIXTURE = "AAPL_5m_20260615_20260630.json"

# The committed J-03 tape-at-the-wall join fixture (see test_setups.py's own header + generation
# script scripts/generate_setups_join_fixture.py for provenance).
FIXTURE_DATASETS_J03_DIR = Path(__file__).parent / "fixtures" / "datasets_j03"


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    bar_dir = tmp_path / "bars"
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(bar_dir))
    # Era-5B J-03: get_setup now also depends on the DatasetStore. Point it at an EMPTY temp dir by
    # default (the test_datasets_api.py ctx precedent) so this file's route-level assertions never
    # accidentally read a real operator's local (gitignored) recorded datasets -- hermetic by
    # construction, exactly like the bar-dir override directly above.
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
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


def _seed_yahoo_fixture_into_bar_dir(bar_dir: Path, fixture_name: str) -> None:
    bar_dir.mkdir(parents=True, exist_ok=True)  # BarStore only creates it lazily inside `record()`
    fixture = json.loads((YAHOO_FIXTURE_DIR / fixture_name).read_text())
    bars = [
        RawBar(
            fixture["symbol"], fixture["timeframe"], b["epoch"],
            b["open"], b["high"], b["low"], b["close"], b["volume"],
        )
        for b in fixture["bars"]
    ]
    BarStore(bar_dir).record(
        symbol=fixture["symbol"], timeframe=fixture["timeframe"],
        window_start_utc=fixture["start"], window_end_utc=fixture["end"],
        feed="yahoo", bars=bars,
    )


def _seed_aapl(bar_dir: Path) -> None:
    _seed_yahoo_fixture_into_bar_dir(bar_dir, AAPL_DAILY_FIXTURE)
    _seed_yahoo_fixture_into_bar_dir(bar_dir, AAPL_5M_SETUPS_FIXTURE)


_EVENT_FIELDS = {
    "id", "symbol", "session_date", "band", "touch_ts", "touch_open", "touch_high",
    "touch_low", "touch_close", "touch_volume", "reaction", "forward_returns", "tape_timeline",
    # B1 (era-5B iter-5): additive recency-boundary disclosure fields.
    "effective_reaction_horizon_bars", "reaction_boundary_truncated",
}


# --- Happy path: the real route wires through to compute_setups verbatim -----------------------


def test_list_setups_happy_path_through_the_real_route(ctx):
    client, _bar_dir = ctx
    _seed_aapl(_bar_dir)

    r = client.get("/research/setups")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["events"], list) and len(body["events"]) >= 1
    for event in body["events"]:
        assert set(event) == _EVENT_FIELDS
        assert event["symbol"] == "AAPL"  # only panel symbol with bars seeded
        assert event["reaction"] in ("rejected", "broke", "chopped")
        assert event["tape_timeline"] == []


def test_list_setups_rest_matches_module_output_byte_for_byte(ctx):
    client, bar_dir = ctx
    _seed_aapl(bar_dir)

    r = client.get("/research/setups")
    assert r.status_code == 200

    direct = compute_setups(BarStore(bar_dir), CONFIG)
    assert r.json() == direct


def test_no_bar_series_at_all_is_an_honest_empty_registry(ctx):
    client, _bar_dir = ctx  # nothing seeded this run
    r = client.get("/research/setups")
    assert r.status_code == 200
    assert r.json() == {"events": []}


# --- era-fast_wall J-06 (TC-8's HTTP leg): a corrupted durable scan-cache DB never blocks the
# route -- the publish-failure-swallowed discipline observed through the REAL request path, not
# just the direct `compute_setups` call `test_setups.py`'s own TC-8 already proves. The route
# (`list_setups`) wires through to `compute_setups` with zero extra error handling (routes.py's own
# source), so this is a genuine end-to-end confirmation, not a restatement. ------------------------


def test_corrupted_durable_scan_cache_db_never_blocks_the_route_still_200s_with_the_fresh_scan(ctx):
    from app.research.setups_scan_cache import resolve_scan_cache_db_path

    client, bar_dir = ctx
    _seed_aapl(bar_dir)

    db_path = Path(resolve_scan_cache_db_path(str(BarStore(bar_dir).root)))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_bytes(b"not a real sqlite database, just garbage bytes " * 20)

    r = client.get("/research/setups")

    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["events"], list) and len(body["events"]) >= 1


# --- The committed real AAPL fixture: J-02's pinned acceptance through the REAL route -----------


def test_get_setups_aapl_pinned_2026_06_22_event_through_the_real_route(ctx):
    client, bar_dir = ctx
    _seed_aapl(bar_dir)

    r = client.get("/research/setups", params={"symbol": "AAPL", "reaction": "rejected"})
    assert r.status_code == 200
    day_events = [e for e in r.json()["events"] if e["session_date"] == "2026-06-22"]
    assert day_events, "the pinned 2026-06-22 rejected event must be present"

    pinned = next(
        e for e in day_events
        if e["band"]["side"] == "resistance"
        and e["band"]["price_low"] <= 300.48 and e["band"]["price_high"] >= 302.07
    )
    assert pinned["reaction"] == "rejected"
    assert len(pinned["forward_returns"]) == 2
    for fr in pinned["forward_returns"]:
        assert fr["return_fraction"] is not None and fr["return_fraction"] < 0


# --- Filters: symbol (free-form) / reaction (enum) / band_class (enum), AND-combined ------------


def test_filter_by_symbol_matches_only_that_symbol(ctx):
    client, bar_dir = ctx
    _seed_aapl(bar_dir)

    matched = client.get("/research/setups", params={"symbol": "AAPL"})
    assert matched.status_code == 200
    assert len(matched.json()["events"]) >= 1

    unmatched = client.get("/research/setups", params={"symbol": "MSFT"})
    assert unmatched.status_code == 200
    assert unmatched.json()["events"] == [], "a well-formed but unmatched symbol is honest empty, never an error"


def test_filter_by_symbol_is_case_insensitive(ctx):
    client, bar_dir = ctx
    _seed_aapl(bar_dir)
    lower = client.get("/research/setups", params={"symbol": "aapl"})
    upper = client.get("/research/setups", params={"symbol": "AAPL"})
    assert lower.status_code == upper.status_code == 200
    assert lower.json() == upper.json()


def test_blank_symbol_normalizes_to_absent_same_as_no_param(ctx):
    """The ``list_bar_series`` era-5 J-05 audit-fixed precedent: a present-but-blank ``?symbol=``
    takes the EXACT SAME path as a true no-param call -- never a silently-different filtered (and
    in this case empty) result."""
    client, bar_dir = ctx
    _seed_aapl(bar_dir)
    blank = client.get("/research/setups", params={"symbol": ""})
    absent = client.get("/research/setups")
    assert blank.status_code == absent.status_code == 200
    assert blank.json() == absent.json()


def test_filter_by_reaction_unknown_value_is_422(ctx):
    client, _bar_dir = ctx
    r = client.get("/research/setups", params={"reaction": "bullish"})
    assert r.status_code == 422
    assert "reaction" in r.json()["detail"]


def test_filter_by_reaction_valid_value_narrows_results(ctx):
    client, bar_dir = ctx
    _seed_aapl(bar_dir)
    all_events = client.get("/research/setups").json()["events"]
    reactions_present = {e["reaction"] for e in all_events}
    assert reactions_present, "the seeded fixture must produce at least one event"
    target = next(iter(reactions_present))

    r = client.get("/research/setups", params={"reaction": target})
    assert r.status_code == 200
    filtered = r.json()["events"]
    assert filtered and all(e["reaction"] == target for e in filtered)
    assert len(filtered) == len([e for e in all_events if e["reaction"] == target])


def test_filter_by_band_class_unknown_value_is_422(ctx):
    client, _bar_dir = ctx
    r = client.get("/research/setups", params={"band_class": "Z"})
    assert r.status_code == 422
    assert "band_class" in r.json()["detail"]


def test_filter_by_band_class_valid_value_narrows_results(ctx):
    client, bar_dir = ctx
    _seed_aapl(bar_dir)
    all_events = client.get("/research/setups").json()["events"]
    classes_present = {e["band"]["class"] for e in all_events if e["band"]["class"] is not None}
    assert classes_present, "the seeded fixture must produce at least one classified band"
    target = next(iter(classes_present))

    r = client.get("/research/setups", params={"band_class": target})
    assert r.status_code == 200
    filtered = r.json()["events"]
    assert filtered and all(e["band"]["class"] == target for e in filtered)


def test_combined_filters_are_and_combined(ctx):
    client, bar_dir = ctx
    _seed_aapl(bar_dir)
    r = client.get("/research/setups", params={"symbol": "AAPL", "reaction": "rejected"})
    assert r.status_code == 200
    assert all(e["symbol"] == "AAPL" and e["reaction"] == "rejected" for e in r.json()["events"])

    r2 = client.get("/research/setups", params={"symbol": "MSFT", "reaction": "rejected"})
    assert r2.status_code == 200
    assert r2.json()["events"] == []


# --- Detail: GET /research/setups/{id} -----------------------------------------------------------


def test_get_setup_detail_matches_the_list_entry(ctx):
    client, bar_dir = ctx
    _seed_aapl(bar_dir)
    listed = client.get("/research/setups").json()["events"]
    assert listed
    target = listed[0]

    r = client.get(f"/research/setups/{target['id']}")
    assert r.status_code == 200
    assert r.json() == {"event": target}


def test_get_setup_unknown_id_is_404(ctx):
    client, bar_dir = ctx
    _seed_aapl(bar_dir)
    r = client.get("/research/setups/does-not-exist")
    assert r.status_code == 404
    assert "does-not-exist" in r.json()["detail"]


def test_get_setup_unknown_id_on_an_empty_store_is_still_404_never_an_error(ctx):
    client, _bar_dir = ctx  # nothing seeded
    r = client.get("/research/setups/anything")
    assert r.status_code == 404


# --- Tape-at-the-wall join through the REAL route (era-5B capability 4, J-03) -------------------
#
# ``list_setups``/``get_setup`` read the process-global ``CONFIG`` (this file's own header
# docstring), so ``setups_panel_symbols`` cannot be overridden per-request -- every route-level
# event here is necessarily a REAL shipped-panel symbol (AAPL). No committed REAL tick fixture
# exists for any shipped panel symbol (only the era-3 PG/F reference captures, neither in the
# panel), so a route-level proof of "a REAL committed dataset ENRICHES a REAL panel event" is only
# reachable with real Alpaca credentials (J-03's own operator-gated headline) -- exactly what
# ``test_setups.py``'s module-level tests already prove keylessly for the join MECHANISM itself
# (bypassing the route's fixed panel via a directly-passed ``Config(setups_panel_symbols=("PG",))``).
# What IS honestly provable here, keyless, through the REAL route: the join is correctly wired
# (never crashes, never silently mismatches) and correctly SYMBOL-SCOPED (a real recorded dataset
# for an off-panel symbol never leaks into an on-panel event's timeline).


def test_get_setup_pinned_aapl_event_through_the_real_route_is_keyless_honest_empty(ctx):
    """The pinned AAPL 2026-06-22 event's drill-in, read through the REAL detail route: keyless (no
    Alpaca credentials, no recorded AAPL dataset in this hermetic dataset dir), so
    ``tape_timeline`` is honestly empty -- the credentialed recording (J-03's operator-gated
    headline) is what fills this in for real."""
    client, bar_dir = ctx
    _seed_aapl(bar_dir)
    listed = client.get(
        "/research/setups", params={"symbol": "AAPL", "reaction": "rejected"}
    ).json()["events"]
    pinned = next(
        e for e in listed
        if e["session_date"] == "2026-06-22" and e["band"]["side"] == "resistance"
        and e["band"]["price_low"] <= 300.48 and e["band"]["price_high"] >= 302.07
    )

    r = client.get(f"/research/setups/{pinned['id']}")
    assert r.status_code == 200
    event = r.json()["event"]
    assert event["reaction"] == "rejected"
    assert event["tape_timeline"] == []


def test_get_setup_detail_stays_unenriched_when_no_dataset_matches_the_symbol(ctx, monkeypatch):
    """A REAL recorded dataset (the committed J-03 fixture) sits in the dataset store, but its
    symbol ("PG") matches no AAPL event -- ``GET /research/setups/{id}`` must stay byte-identical
    to the list entry (the join is correctly symbol-scoped, never a blind "first dataset found"
    attach)."""
    client, bar_dir = ctx
    _seed_aapl(bar_dir)
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(FIXTURE_DATASETS_J03_DIR))

    listed = client.get("/research/setups").json()["events"]
    assert listed
    target = listed[0]

    r = client.get(f"/research/setups/{target['id']}")
    assert r.status_code == 200
    assert r.json() == {"event": target}
    assert r.json()["event"]["tape_timeline"] == []


def test_list_setups_never_enriches_even_when_a_matching_dataset_exists(ctx, monkeypatch):
    """The LIST route (``GET /research/setups``) must stay UN-enriched no matter what the dataset
    store holds -- the join lives ONLY in the detail route (architecture guard: a per-event dataset
    lookup inside the shared scan would regress the already-slow full-panel list route)."""
    client, bar_dir = ctx
    _seed_aapl(bar_dir)
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(FIXTURE_DATASETS_J03_DIR))

    events = client.get("/research/setups").json()["events"]
    assert events
    assert all(e["tape_timeline"] == [] for e in events)


def test_get_setup_rest_matches_direct_module_join_byte_for_byte(ctx, monkeypatch):
    """``GET /research/setups/{id}``'s enriched output matches a direct ``compute_setups`` +
    ``enrich_with_tape_timeline`` call byte-for-byte -- single source of truth, no second
    computation path (the ``test_list_setups_rest_matches_module_output_byte_for_byte`` precedent,
    extended to the join)."""
    client, bar_dir = ctx
    _seed_aapl(bar_dir)
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(FIXTURE_DATASETS_J03_DIR))

    listed = client.get("/research/setups").json()["events"]
    target = listed[0]
    r = client.get(f"/research/setups/{target['id']}")
    assert r.status_code == 200

    from app.research.setups import enrich_with_tape_timeline

    direct_events = compute_setups(BarStore(bar_dir), CONFIG)["events"]
    direct_event = next(e for e in direct_events if e["id"] == target["id"])
    direct_enriched = enrich_with_tape_timeline(
        direct_event, DatasetStore(FIXTURE_DATASETS_J03_DIR), CONFIG
    )
    assert r.json() == {"event": direct_enriched}
