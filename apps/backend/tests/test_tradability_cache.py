"""``tradability_cache.py`` + its ONE caller (``GET /research/tradability``) — unit coverage of
the key/lookup/publish/resolve mechanics (mirroring ``test_setups_scan_cache.py``'s structure for
the sibling durable cache) plus route-level proof that the cache accelerates without ever changing
a served byte: hit = zero recompute, every honest bust (this symbol's store content, config
content, algorithm version) recomputes, another symbol's recording does NOT bust, and two
same-UTC-day requests share one row while each echoes its own ``as_of``."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import CONFIG
from app.providers.adapters.base import RawBar
from app.research.bars import BarStore
from app.research.tradability_cache import (
    TradabilityCache,
    resolve_tradability_cache_db_path,
    symbol_store_signature,
    tradability_cache_key,
)

_DAY = 86400.0
_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()

_KEY_PARTS = dict(
    symbol="AAPL",
    basis_day="2026-06-22",
    store_signature=(("1d", "id-1", "sha-1"),),
    config_content_hash="cfg-hash",
)


def _bar(symbol: str, day_index: int, high: float, low: float, close: float) -> RawBar:
    return RawBar(symbol, "1d", _BASE + day_index * _DAY, close, high, low, close, 1_000)


def _seed(store: BarStore, symbol: str, *, days: int = 5, price_base: float = 100.0) -> None:
    store.record(
        symbol=symbol, timeframe="1d",
        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-08T00:00:00Z",
        feed="sip",
        bars=[
            _bar(symbol, i, price_base + 10 * i + 5, price_base + 10 * i - 5, price_base + 10 * i)
            for i in range(days)
        ],
    )


# --- tradability_cache_key: a pure function, non-vacuous key-busting matrix -----------------------


def test_cache_key_is_stable_for_identical_inputs():
    assert tradability_cache_key(**_KEY_PARTS) == tradability_cache_key(**_KEY_PARTS)


def test_cache_key_mutations_are_pairwise_distinct():
    """Each of the four components independently busts the key, and no two mutations collide."""
    keys = {tradability_cache_key(**_KEY_PARTS)}
    for mutation in (
        dict(_KEY_PARTS, symbol="MSFT"),
        dict(_KEY_PARTS, basis_day="2026-06-23"),
        dict(_KEY_PARTS, store_signature=(("1d", "id-2", "sha-2"),)),
        dict(_KEY_PARTS, config_content_hash="other-hash"),
    ):
        keys.add(tradability_cache_key(**mutation))
    assert len(keys) == 5, "every component mutation must yield its own distinct key"


def test_symbol_store_signature_is_symbol_scoped_and_order_independent():
    records = [
        {"symbol": "AAPL", "timeframe": "1d", "id": "b", "checksum": "sb"},
        {"symbol": "MSFT", "timeframe": "1d", "id": "x", "checksum": "sx"},
        {"symbol": "AAPL", "timeframe": "1h", "id": "a", "checksum": "sa"},
    ]
    signature = symbol_store_signature(records, "AAPL")
    assert signature == (("1d", "b", "sb"), ("1h", "a", "sa"))
    assert symbol_store_signature(list(reversed(records)), "AAPL") == signature
    assert symbol_store_signature(records, "MSFT") == (("1d", "x", "sx"),)
    assert symbol_store_signature(records, "NVDA") == ()


# --- lookup / publish mechanics -------------------------------------------------------------------


def test_cold_lookup_is_none(tmp_path):
    cache = TradabilityCache(str(tmp_path / "tradability_cache.db"))
    assert cache.lookup("no-such-key") is None


def test_publish_then_lookup_round_trips_the_result_verbatim(tmp_path):
    cache = TradabilityCache(str(tmp_path / "tradability_cache.db"))
    result = {
        "bands": [{"side": "resistance", "price_low": 300.11, "price_high": 302.2, "class": "A"}],
        "no_bar_series_for_symbol": False,
        "basis_as_of": "2026-06-18T04:00:00.000000Z",
    }
    cache.publish("k", result)
    got = cache.lookup("k")
    assert got == result
    assert json.dumps(got) == json.dumps(result), "key order and floats must round-trip exactly"


def test_stored_value_is_not_sort_keys_serialized(tmp_path):
    """The EdgeReportCache byte-identity discipline: insertion order preserved, never re-sorted."""
    db = str(tmp_path / "tradability_cache.db")
    TradabilityCache(db).publish("k", {"zebra": 1, "alpha": 2})
    raw = sqlite3.connect(db).execute(
        "SELECT result_json FROM tradability_cache WHERE cache_key='k'"
    ).fetchone()[0]
    assert raw.index("zebra") < raw.index("alpha")


def test_durability_across_a_simulated_restart_serves_the_prior_row(tmp_path):
    db = str(tmp_path / "tradability_cache.db")
    TradabilityCache(db).publish("k", {"bands": []})
    assert TradabilityCache(db).lookup("k") == {"bands": []}  # a FRESH instance, same file


def test_corrupted_db_file_never_crashes_lookup_misses_publish_swallows(tmp_path):
    db = tmp_path / "tradability_cache.db"
    db.write_bytes(b"this is not a sqlite database")
    cache = TradabilityCache(str(db))  # construction: no raise
    assert cache.lookup("k") is None
    cache.publish("k", {"bands": []})  # no raise


# --- resolve_tradability_cache_db_path: env-else-sibling-of-bar-store-root ------------------------


def test_resolve_defaults_to_a_sibling_of_the_bar_store_root(tmp_path, monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_TRADABILITY_CACHE_DB", raising=False)
    assert resolve_tradability_cache_db_path(str(tmp_path / "bars")) == str(
        tmp_path / "tradability_cache.db"
    )


def test_resolve_honors_the_env_override(tmp_path, monkeypatch):
    override = str(tmp_path / "elsewhere" / "cache.db")
    monkeypatch.setenv("TAPEOLOGY_TRADABILITY_CACHE_DB", override)
    assert resolve_tradability_cache_db_path(str(tmp_path / "bars")) == override


def test_resolve_never_collides_with_sibling_cache_paths(tmp_path, monkeypatch):
    from app.research.setups_scan_cache import resolve_scan_cache_db_path

    monkeypatch.delenv("TAPEOLOGY_TRADABILITY_CACHE_DB", raising=False)
    monkeypatch.delenv("TAPEOLOGY_SETUPS_CACHE_DB", raising=False)
    bar_root = str(tmp_path / "bars")
    assert resolve_tradability_cache_db_path(bar_root) != resolve_scan_cache_db_path(bar_root)


# --- the route: hit = zero recompute, every honest bust recomputes, bytes never change ------------


def _client_with_store(tmp_path, monkeypatch):
    """A TestClient whose bar store lives under ``tmp_path`` (the ``TAPEOLOGY_BAR_DIR`` env
    idiom every bar API test uses) — the cache DB derives from that same root (the route's own
    hermeticity property) — plus a compute-counting spy on the route's ``compute_tradability``."""
    from app.main import app
    from app.research import routes as routes_module

    bar_dir = tmp_path / "bars"
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(bar_dir))
    store = BarStore(bar_dir)

    calls: list[tuple[str, float]] = []
    real_compute = routes_module.compute_tradability

    def counting_compute(store_arg, symbol, as_of_epoch, config):
        calls.append((symbol, as_of_epoch))
        return real_compute(store_arg, symbol, as_of_epoch, config)

    monkeypatch.setattr(routes_module, "compute_tradability", counting_compute)
    return TestClient(app), store, calls


def test_route_repeat_request_is_a_cache_hit_with_zero_recompute(tmp_path, monkeypatch):
    client, store, calls = _client_with_store(tmp_path, monkeypatch)
    _seed(store, "AAPL")
    first = client.get("/research/tradability", params={"symbol": "AAPL", "as_of": "2026-01-04T00:00:00Z"})
    assert first.status_code == 200 and len(calls) == 1
    second = client.get("/research/tradability", params={"symbol": "AAPL", "as_of": "2026-01-04T00:00:00Z"})
    assert second.status_code == 200
    assert len(calls) == 1, "the repeat must be served from the durable cache, never recomputed"
    assert second.content == first.content, "a cached response must be byte-identical"


def test_route_same_utc_day_shares_one_row_but_echoes_each_requests_own_as_of(tmp_path, monkeypatch):
    client, store, calls = _client_with_store(tmp_path, monkeypatch)
    _seed(store, "AAPL")
    morning = client.get("/research/tradability", params={"symbol": "AAPL", "as_of": "2026-01-04T09:30:00Z"})
    evening = client.get("/research/tradability", params={"symbol": "AAPL", "as_of": "2026-01-04T20:00:00Z"})
    assert len(calls) == 1, "same UTC date resolves the same basis — one compute, one row"
    assert morning.json()["as_of"] == "2026-01-04T09:30:00Z"
    assert evening.json()["as_of"] == "2026-01-04T20:00:00Z"
    assert morning.json()["bands"] == evening.json()["bands"]


def test_route_a_new_recording_for_the_symbol_busts_the_row(tmp_path, monkeypatch):
    client, store, calls = _client_with_store(tmp_path, monkeypatch)
    _seed(store, "AAPL")
    client.get("/research/tradability", params={"symbol": "AAPL", "as_of": "2026-01-04T00:00:00Z"})
    assert len(calls) == 1
    # A NEW recording of the SAME symbol (distinct content/window) changes its signature.
    store.record(
        symbol="AAPL", timeframe="1d",
        window_start_utc="2026-01-10T00:00:00Z", window_end_utc="2026-01-11T00:00:00Z",
        feed="sip", bars=[_bar("AAPL", 9, 205.0, 195.0, 200.0)],
    )
    client.get("/research/tradability", params={"symbol": "AAPL", "as_of": "2026-01-04T00:00:00Z"})
    assert len(calls) == 2, "this symbol's own store-content change must recompute"


def test_route_another_symbols_recording_does_not_bust_the_row(tmp_path, monkeypatch):
    client, store, calls = _client_with_store(tmp_path, monkeypatch)
    _seed(store, "AAPL")
    client.get("/research/tradability", params={"symbol": "AAPL", "as_of": "2026-01-04T00:00:00Z"})
    assert len(calls) == 1
    _seed(store, "MSFT", price_base=300.0)  # an unrelated symbol's recording
    client.get("/research/tradability", params={"symbol": "AAPL", "as_of": "2026-01-04T00:00:00Z"})
    assert len(calls) == 1, "the signature is symbol-scoped — another symbol never busts it"


def test_route_config_content_and_algorithm_version_bust_the_row(tmp_path, monkeypatch):
    import app.research.edge_report_cache as edge_cache_module

    client, store, calls = _client_with_store(tmp_path, monkeypatch)
    _seed(store, "AAPL")
    client.get("/research/tradability", params={"symbol": "AAPL", "as_of": "2026-01-04T00:00:00Z"})
    assert len(calls) == 1
    # An algorithm-version bump flows through the SAME shared config-content hash every
    # sibling durable cache keys on — nothing about the store or request changed.
    monkeypatch.setattr(edge_cache_module, "LEVELS_ALGORITHM_VERSION", 999)
    client.get("/research/tradability", params={"symbol": "AAPL", "as_of": "2026-01-04T00:00:00Z"})
    assert len(calls) == 2, "an algorithm-version bump must recompute"


def test_route_cache_db_lands_beside_the_injected_stores_root(tmp_path, monkeypatch):
    """The hermeticity property the route docstring promises: the durable file derives from the
    INJECTED store's own root, so this test's cache lives under ``tmp_path`` — never the real
    ``.data/`` directory."""
    monkeypatch.delenv("TAPEOLOGY_TRADABILITY_CACHE_DB", raising=False)
    client, store, calls = _client_with_store(tmp_path, monkeypatch)
    _seed(store, "AAPL")
    client.get("/research/tradability", params={"symbol": "AAPL", "as_of": "2026-01-04T00:00:00Z"})
    assert Path(tmp_path / "tradability_cache.db").exists()
