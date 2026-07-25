"""The ``/research/desk/universe*`` endpoints (Era B "The Desk", J-01) — fetch/register, list.

Exactly TWO routes exist (the plan's Product Shape): ``POST /research/desk/universe/fetch`` (the
explicit operator research action — fetch -> parse -> validate -> register; recording is never
ambient) and ``GET /research/desk/universe`` (snapshot list + latest membership; an explicit HTTP
200 empty payload before any registration — never 404). Four states per the plan's Key Test
Scenarios: empty / registered / corrupted-input / duplicate-input. Mirrors
``test_bars_api.py``/``test_datasets_api.py``'s fixture-injection conventions, using
``app.dependency_overrides`` on ``get_universe_fetcher`` (the ``get_market_adapter``/
``FakeAdapter`` seam) so every test here makes ZERO real network calls.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG, Config
from app.main import app, manager
import app.research.desk_routes as desk_routes
from app.research.desk_routes import get_universe_fetcher, get_universe_store
from app.research.desk_universe import UniverseFetchError
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "universe"
VALID_HTML = (FIXTURE_DIR / "sp100_constituents.html").read_text()
CORRUPTED_HTML = (FIXTURE_DIR / "sp100_constituents_corrupted.html").read_text()

SOURCE_URL = "https://en.wikipedia.org/wiki/S%26P_100"


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    universe_dir = tmp_path / "universe"
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(universe_dir))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    with TestClient(app) as client:
        yield client, universe_dir
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    set_registry(None)
    app.dependency_overrides.pop(get_universe_fetcher, None)
    store.close()


def _inject_fetcher(html: str = VALID_HTML, *, raises: Exception | None = None) -> list[str]:
    """Overrides the universe-page HTML fetch with a scripted response — the
    ``get_market_adapter``/``FakeAdapter`` seam, adapted for a single-callable dependency. Returns
    the list of source URLs the route actually requested (so a test can assert it was called)."""
    calls: list[str] = []

    def _fake_fetch(source_url: str) -> str:
        calls.append(source_url)
        if raises is not None:
            raise raises
        return html

    app.dependency_overrides[get_universe_fetcher] = lambda: _fake_fetch
    return calls


# --- empty state (TC-1) ---------------------------------------------------------------------------


def test_get_with_no_snapshot_is_an_honest_empty_200(ctx):
    client, _universe_dir = ctx
    r = client.get("/research/desk/universe")
    assert r.status_code == 200
    body = r.json()
    assert body == {"snapshots": [], "latest": None, "integrity_errors": []}


# --- valid registration (TC-2, TC-3, TC-6) ----------------------------------------------------


def test_post_fetch_registers_a_valid_snapshot(ctx):
    client, universe_dir = ctx
    _inject_fetcher(VALID_HTML)

    r = client.post("/research/desk/universe/fetch")
    assert r.status_code == 200
    meta = r.json()["universe"]
    assert len(meta["checksum"]) == 12
    assert 90 <= meta["member_count"] <= 110
    assert meta["members"] == sorted(meta["members"])
    assert "BRK-B" in meta["members"]
    assert "BRK.B" not in meta["members"]
    assert meta["raw_members"]["BRK-B"] == "BRK.B"
    assert len(list(universe_dir.glob("*.json"))) == 1


def test_get_after_registration_lists_the_snapshot_and_serves_it_as_latest(ctx):
    client, _universe_dir = ctx
    _inject_fetcher(VALID_HTML)
    posted = client.post("/research/desk/universe/fetch").json()["universe"]

    r = client.get("/research/desk/universe")
    assert r.status_code == 200
    body = r.json()
    assert body["integrity_errors"] == []
    assert [row["id"] for row in body["snapshots"]] == [posted["id"]]
    assert body["snapshots"][0] == posted  # the stored row, verbatim -- no recompute at read
    assert body["latest"] == posted


def test_post_fetch_only_calls_the_vendor_once_for_the_configured_source_url(ctx):
    client, _universe_dir = ctx
    calls = _inject_fetcher(VALID_HTML)
    client.post("/research/desk/universe/fetch")
    assert calls == [CONFIG.desk_universe_source_url]


# --- corrupted input (TC-4) ---------------------------------------------------------------------


def test_post_fetch_with_a_charset_violating_ticker_is_an_explicit_422(ctx):
    client, universe_dir = ctx
    _inject_fetcher(CORRUPTED_HTML)

    r = client.post("/research/desk/universe/fetch")
    assert r.status_code == 422
    assert "charset" in r.json()["detail"]

    listed = client.get("/research/desk/universe").json()
    assert listed == {"snapshots": [], "latest": None, "integrity_errors": []}
    assert not universe_dir.exists() or list(universe_dir.glob("*.json")) == []


def test_post_fetch_with_an_out_of_bounds_count_is_an_explicit_422(ctx):
    client, universe_dir = ctx
    tiny_html = (
        "<html><body><table><tr><th>Symbol</th></tr>"
        "<tr><td>AAPL</td></tr><tr><td>MSFT</td></tr></table></body></html>"
    )
    _inject_fetcher(tiny_html)

    r = client.post("/research/desk/universe/fetch")
    assert r.status_code == 422
    assert "2" in r.json()["detail"]
    assert not universe_dir.exists() or list(universe_dir.glob("*.json")) == []


def test_post_fetch_when_the_vendor_is_unreachable_is_an_explicit_503(ctx):
    client, universe_dir = ctx
    _inject_fetcher(raises=UniverseFetchError("could not reach the source"))

    r = client.post("/research/desk/universe/fetch")
    assert r.status_code == 503
    assert "could not reach" in r.json()["detail"]
    assert not universe_dir.exists() or list(universe_dir.glob("*.json")) == []


# --- duplicate content (TC-5) ---------------------------------------------------------------------


def test_post_fetch_of_identical_already_registered_content_is_a_409(ctx):
    client, universe_dir = ctx
    _inject_fetcher(VALID_HTML)
    first = client.post("/research/desk/universe/fetch")
    assert first.status_code == 200
    original = first.json()["universe"]
    path = next(universe_dir.glob("*.json"))
    before = path.read_bytes()

    duplicate = client.post("/research/desk/universe/fetch")
    assert duplicate.status_code == 409
    assert original["id"] in duplicate.json()["detail"]
    assert path.read_bytes() == before  # byte-unchanged -- never a rewrite
    assert len(list(universe_dir.glob("*.json"))) == 1  # no second file


# --- provenance (TC-10): the exact Path-A values used at registration are embedded --------------


def test_registered_snapshot_embeds_the_exact_config_values_used(ctx):
    client, _universe_dir = ctx
    _inject_fetcher(VALID_HTML)
    meta = client.post("/research/desk/universe/fetch").json()["universe"]

    assert meta["source_url"] == CONFIG.desk_universe_source_url
    assert meta["min_members"] == CONFIG.desk_universe_min_members
    assert meta["max_members"] == CONFIG.desk_universe_max_members

    get_body = client.get("/research/desk/universe").json()
    assert get_body["latest"]["source_url"] == CONFIG.desk_universe_source_url
    assert get_body["latest"]["min_members"] == CONFIG.desk_universe_min_members
    assert get_body["latest"]["max_members"] == CONFIG.desk_universe_max_members


# --- Path-A counter-test at the route level (TC-9): live-wired end to end -----------------------


def test_route_level_counter_test_raising_min_members_refuses_the_same_valid_fixture(ctx, monkeypatch):
    """TC-9, exercised end to end through the ROUTE (not just the pure parser): overriding
    ``desk_universe_min_members`` above the fixture's real member count (103) refuses the SAME
    valid fixture — proving the field is genuinely live-wired into this new path, while
    ``Config().config_fingerprint()`` (asserted separately in ``test_desk_universe.py``) stays
    unaffected."""
    client, universe_dir = ctx
    _inject_fetcher(VALID_HTML)
    monkeypatch.setattr(desk_routes, "CONFIG", Config(desk_universe_min_members=200))

    r = client.post("/research/desk/universe/fetch")
    assert r.status_code == 422
    assert "outside the expected" in r.json()["detail"]
    assert not universe_dir.exists() or list(universe_dir.glob("*.json")) == []


# --- dependency resolvers: direct, hermetic proofs (the get_bar_store/get_bar_index precedent) --


def test_get_universe_store_resolves_to_the_configured_dir_by_default(ctx):
    _client, universe_dir = ctx
    store = get_universe_store()
    assert store.root == universe_dir


def test_get_universe_fetcher_default_is_the_real_keyless_fetch(ctx):
    """A direct, hermetic proof of the resolver itself (the
    ``test_bar_fetch_adapter_resolver_defaults_to_yahoo_with_no_override`` pattern): with NO
    ``dependency_overrides`` on ``get_universe_fetcher``, calling it returns the REAL
    ``fetch_constituents_html``-backed callable (never a test double) — proven by identity of the
    wrapped function's origin, not by making a real network call."""
    _client, _universe_dir = ctx
    app.dependency_overrides.pop(get_universe_fetcher, None)  # ensure no leftover override
    fetch = get_universe_fetcher()
    assert callable(fetch)
    assert fetch.__module__ == desk_routes.__name__


# --- honest 4xx naming the specific validation failure (not a generic message) -------------------


def test_no_symbol_column_failure_names_the_specific_problem(ctx):
    client, _universe_dir = ctx
    no_symbol_html = "<html><body><table><tr><th>No.</th><th>Company</th></tr><tr><td>1</td><td>Apple</td></tr></table></body></html>"
    _inject_fetcher(no_symbol_html)

    r = client.post("/research/desk/universe/fetch")
    assert r.status_code == 422
    assert "Symbol" in r.json()["detail"]
