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


def test_end_not_after_start_is_422(ctx):
    client, _bar_dir = ctx
    r = client.post("/research/bars", json=_body(start=END, end=START))
    assert r.status_code == 422


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
