"""The read-only stdio MCP server (J-01, capability 6) — byte-identity, read-only discipline,
allowlist, honest failures.

Byte-identity is asserted against a REAL uvicorn instance of the app (a subprocess on an
ephemeral port with a temp journal DB), because the tools are HTTP proxies — an in-process
ASGI shim would not exercise the actual seam. SIM-BUYER is watched and then PAUSED so the
snapshot freezes and tool-vs-curl comparisons are deterministic byte-for-byte.

Most tests drive ``app.mcp.call_tool`` (the registered dispatcher) directly and assert the
module's result contract; ``test_stdio_session_end_to_end`` additionally spawns the real
``python -m app.mcp`` subprocess and speaks MCP over stdio — the exact J-01 client flow,
including the SDK's exception→``isError`` conversion.
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import CONFIG
from app.mcp import (
    ALLOWED_GET_PREFIXES,
    BackendUnreachableError,
    PathRefusedError,
    TOOL_NAMES,
    ToolArgumentError,
    UnknownToolError,
    call_tool,
    list_tools,
)
from app.providers.adapters.base import RawBar
from app.research.bars import BarSeriesAlreadyRegistered, BarStore
from app.research.desk_screen import ScreenStore
from app.research.desk_universe import UniverseStore

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Capability 6, verbatim — order and content are the advertised contract. ``bars`` (era-4 J-01),
# ``levels`` (era-4 J-02), ``strategies`` (era-4 J-04), ``tradability`` (era-5B J-01), ``setups``
# (era-5B J-02), and ``desk_universe``/``desk_screen`` (era-desk J-06, MCP contract v3 -- 15 -> 17
# tools) are the newest additions, each positioned right after its dependency-order sibling (the
# same store/registry+route+MCP shape, mirrored end to end).
EXPECTED_TOOLS = (
    "tape_state",
    "tape_features",
    "tape_history",
    "datasets",
    "bars",
    "levels",
    "tradability",
    "setups",
    "backtests",
    "strategies",
    "edge_report",
    "desk_universe",
    "desk_screen",
    "pnl_ledger",
    "taxonomy",
    "ui_route_map",
    "get_endpoint",
)

FIXTURE_BAR_DIR = Path(__file__).parent / "fixtures" / "bars"
YAHOO_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "yahoo"

# Every registered tool's endpoint has now shipped (``datasets`` at J-02, ``backtests`` at J-03,
# ``pnl_ledger`` at J-04 — each moved to the live byte-identity coverage below with zero MCP code
# changes), and ``/research/profiles`` (row 33, reached via ``get_endpoint``) shipped its minimal
# serving side at J-05 — so the honest-404 premise set is retired; the honest-404 WIRE FORM stays
# covered on a PERMANENTLY-unknown ``/research/*`` path, which no journey will ever ship.
UNKNOWN_RESEARCH_PATH = "/research/nonexistent-path-canary"

# clean_slate J-03: a path that WAS a real, shipped route (the journal-era `journal` MCP tool
# proxied it) until clean_slate J-01 deleted its route handler — distinct from
# UNKNOWN_RESEARCH_PATH above, which was NEVER real. Proves the honest-404 contract holds for an
# actually-deleted surface, not only a synthetic canary.
DELETED_RESEARCH_ROUTE = "/research/journal"

# Live 2xx no-argument tools and their canonical endpoints.
LIVE_STATIC = {
    "taxonomy": "/research/taxonomy",
    "ui_route_map": "/meta/ui-routes",
}


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _dead_base() -> str:
    """A base URL guaranteed to refuse connections (bound-then-closed ephemeral port)."""
    return f"http://127.0.0.1:{_free_port()}"


@pytest.fixture(scope="module")
def backend_paths(tmp_path_factory):
    """The test backend's persistence env (journal DB + dataset dir) — a separate fixture so the
    J-04 seeding-CLI subprocess can write into the SAME store the backend serves (the ledger has
    no REST write surface; the CLI is the machine action)."""
    return {
        "TAPEOLOGY_JOURNAL_DB": str(tmp_path_factory.mktemp("mcp-journal") / "journal.db"),
        "TAPEOLOGY_DATASET_DIR": str(tmp_path_factory.mktemp("mcp-datasets")),
        "TAPEOLOGY_BAR_DIR": str(tmp_path_factory.mktemp("mcp-bars")),
        "TAPEOLOGY_DESK_UNIVERSE_DIR": str(tmp_path_factory.mktemp("mcp-desk-universe")),
        "TAPEOLOGY_DESK_SCREEN_DIR": str(tmp_path_factory.mktemp("mcp-desk-screen")),
    }


@pytest.fixture(scope="module")
def backend(backend_paths, tmp_path_factory):
    """A REAL uvicorn instance of the app on an ephemeral port with a temp journal DB."""
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.update(backend_paths)
    log_path = tmp_path_factory.mktemp("mcp-uvicorn") / "uvicorn.log"
    with open(log_path, "wb") as log:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=BACKEND_DIR,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.time() + 20
            while True:
                try:
                    if httpx.get(f"{base}/health", timeout=1.0).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                if proc.poll() is not None or time.time() > deadline:
                    raise AssertionError(
                        f"test backend failed to start:\n{log_path.read_text()[-2000:]}"
                    )
                time.sleep(0.2)
            yield base
        finally:
            proc.terminate()
            proc.wait(timeout=10)


@pytest.fixture(scope="module")
def watched_backend(backend):
    """The test backend with SIM-BUYER watched, settled, and PAUSED (frozen snapshot), so
    tool-vs-curl byte comparisons are deterministic."""
    assert httpx.post(f"{backend}/watch/SIM-BUYER", timeout=5.0).status_code == 200
    deadline = time.time() + 15
    while time.time() < deadline:
        summary = httpx.get(f"{backend}/tape/SIM-BUYER/summary", timeout=5.0).json()
        if summary.get("market", {}).get("last") is not None and summary.get("tape_state") == "buyer_control":
            break
        time.sleep(0.2)
    else:
        raise AssertionError("SIM-BUYER did not settle to buyer_control on the test backend")
    assert httpx.post(f"{backend}/watch/SIM-BUYER/pause", timeout=5.0).status_code == 200
    time.sleep(0.5)  # drain any in-flight event delivery
    first = httpx.get(f"{backend}/tape/SIM-BUYER/state", timeout=5.0).content
    second = httpx.get(f"{backend}/tape/SIM-BUYER/state", timeout=5.0).content
    assert first == second, "pause did not freeze the snapshot — byte comparisons would flap"
    return backend


@pytest.fixture
def mcp_env(watched_backend, monkeypatch):
    """Point the MCP proxy at the live test backend."""
    monkeypatch.setenv("TAPEOLOGY_API_BASE", watched_backend)
    return watched_backend


# --- Read-only discipline -------------------------------------------------------------------


@pytest.mark.anyio
async def test_advertised_tool_set_is_exactly_capability_6():
    tools = await list_tools()
    assert tuple(t.name for t in tools) == EXPECTED_TOOLS
    assert TOOL_NAMES == EXPECTED_TOOLS
    write_verbs = (
        "post", "put", "patch", "delete", "create", "update", "write", "set", "append",
        "insert", "remove", "cancel", "resolve", "declare", "watch", "pause", "resume",
        "record", "register", "mutate",
    )
    for tool in tools:
        # Word-wise (underscore-split): "datasets" is a read noun, "delete_dataset" is not.
        for word in tool.name.lower().split("_"):
            assert word not in write_verbs, f"write verb {word!r} in tool name {tool.name!r}"
        # Arguments are read selectors only.
        assert set(tool.inputSchema.get("properties", {})) <= {
            "ticker", "bar", "path", "symbol", "as_of",
        }
        assert tool.inputSchema.get("additionalProperties") is False


def test_server_source_performs_only_gets_and_imports_no_app_modules():
    """The proxy's whole HTTP vocabulary is GET, and it is not a second implementation of
    anything: no engine/serializer/app imports, no caching, no retries."""
    source = (BACKEND_DIR / "app" / "mcp" / "__init__.py").read_text()
    assert ".get(" in source
    for forbidden_call in (".post(", ".put(", ".patch(", ".delete(", ".request(", ".stream(", ".send("):
        assert forbidden_call not in source, f"non-GET HTTP call {forbidden_call!r} in app/mcp"
    import_lines = [
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    assert import_lines, "expected real import statements to scan"
    for line in import_lines:
        for forbidden in ("app.", "from .", "from ..", " engine", " serializers", " config", " main"):
            assert forbidden not in line, f"app-internal import {line!r} in app/mcp"
    main_source = (BACKEND_DIR / "app" / "mcp" / "__main__.py").read_text()
    assert "from . import main" in main_source


# --- Byte-identity against the running backend ------------------------------------------------


@pytest.mark.anyio
async def test_tape_tools_json_byte_identical_to_rest(mcp_env):
    for name, path in (
        ("tape_state", "/tape/SIM-BUYER/state"),
        ("tape_features", "/tape/SIM-BUYER/features"),
        ("tape_history", "/tape/SIM-BUYER/history"),
    ):
        result = await call_tool(name, {"ticker": "SIM-BUYER"})
        rest = httpx.get(f"{mcp_env}{path}", timeout=5.0)
        assert rest.status_code == 200
        assert result.isError is False
        assert len(result.content) == 1
        assert result.content[0].text == rest.text
        assert result.content[0].text.encode("utf-8") == rest.content, f"{name} not byte-identical"


@pytest.mark.anyio
async def test_static_live_tools_json_byte_identical_to_rest(mcp_env):
    for name, path in LIVE_STATIC.items():
        result = await call_tool(name, {})
        rest = httpx.get(f"{mcp_env}{path}", timeout=5.0)
        assert rest.status_code == 200
        assert result.isError is False
        assert len(result.content) == 1
        assert result.content[0].text.encode("utf-8") == rest.content, f"{name} not byte-identical"


# --- Era B "The Desk" J-06: desk_universe / desk_screen (empty + populated + ?date= proxy) -------
#
# Both stores are rooted at their OWN env-scoped temp dirs (`backend_paths` above) that nothing
# else in this module ever touches, so the honest-empty state below is genuinely observed BEFORE
# either populated-state test seeds anything (file order matters here, same as everywhere else in
# this module -- there is no pytest-randomly plugin in this project).

DESK_SCREEN_DATE = "2026-06-22"
DESK_SCREEN_NONMATCH_DATE = "2020-01-01"
# audit B1: the ?date= proxy test below seeds its OWN screen under this THIRD, distinct date
# rather than reusing DESK_SCREEN_DATE's record (seeded by the populated-state test above) --
# so it now passes standalone (`pytest -k ...`), not just inside the full module.
DESK_SCREEN_ISOLATED_DATE = "2026-06-23"


@pytest.mark.anyio
async def test_desk_universe_tool_byte_identical_on_the_honest_empty_state(mcp_env):
    """Before any universe snapshot is ever registered, ``desk_universe`` proxies
    ``GET /research/desk/universe``'s explicit HTTP 200 honest-empty payload -- never a 404 (the
    ``datasets``/``bars`` no-data convention ``desk_universe.py`` itself follows)."""
    result = await call_tool("desk_universe", {})
    rest = httpx.get(f"{mcp_env}/research/desk/universe", timeout=5.0)
    assert rest.status_code == 200
    assert rest.json() == {"snapshots": [], "latest": None, "integrity_errors": []}
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "desk_universe not byte-identical"


@pytest.mark.anyio
async def test_desk_universe_tool_byte_identical_on_a_populated_state(mcp_env, backend_paths):
    """The ``bars``/``levels``/``tradability``/``setups`` J-01 precedent, applied to the desk
    universe store: seed ONE real snapshot directly through ``UniverseStore.record()`` -- the
    exact persistence call ``POST /research/desk/universe/fetch`` itself makes -- into the live
    backend's env-scoped ``TAPEOLOGY_DESK_UNIVERSE_DIR``, then prove the tool's JSON is
    byte-identical to its curl equivalent on a NON-EMPTY result."""
    universe_dir = Path(backend_paths["TAPEOLOGY_DESK_UNIVERSE_DIR"])
    UniverseStore(universe_dir).record(
        members=["AAPL", "MSFT"],
        raw_members={"AAPL": "AAPL", "MSFT": "MSFT"},
        source_url=CONFIG.desk_universe_source_url,
        min_members=CONFIG.desk_universe_min_members,
        max_members=CONFIG.desk_universe_max_members,
    )
    result = await call_tool("desk_universe", {})
    rest = httpx.get(f"{mcp_env}/research/desk/universe", timeout=5.0)
    assert rest.status_code == 200
    body = rest.json()
    assert len(body["snapshots"]) >= 1, "the live list must be non-empty for this proof"
    assert body["latest"] is not None
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "desk_universe not byte-identical"


@pytest.mark.anyio
async def test_desk_screen_tool_byte_identical_on_the_honest_empty_state(mcp_env):
    """Before any screen has ever been computed, ``desk_screen`` proxies
    ``GET /research/desk/screen``'s explicit HTTP 200 honest-empty payload -- never a 404 (the
    ``GET /research/desk/universe`` convention ``desk_screen.py`` itself follows)."""
    result = await call_tool("desk_screen", {})
    rest = httpx.get(f"{mcp_env}/research/desk/screen", timeout=5.0)
    assert rest.status_code == 200
    assert rest.json() == {"screens": [], "latest": None, "integrity_errors": []}
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "desk_screen not byte-identical"


@pytest.mark.anyio
async def test_desk_screen_tool_byte_identical_on_a_populated_state(mcp_env, backend_paths):
    """The ``desk_universe`` populated-state precedent immediately above, applied to the screen
    store: seed ONE real snapshot directly through ``ScreenStore.record()`` -- the exact
    persistence call the screen compute manager itself makes -- into the live backend's
    env-scoped ``TAPEOLOGY_DESK_SCREEN_DIR``, then prove the tool's JSON is byte-identical to its
    curl equivalent on a NON-EMPTY result. This screen snapshot is also what the ``get_endpoint``
    ``?date=`` proxy test right below reads."""
    screen_dir = Path(backend_paths["TAPEOLOGY_DESK_SCREEN_DIR"])
    ScreenStore(screen_dir).record(
        screen_date=DESK_SCREEN_DATE,
        as_of="2026-06-22T21:00:00Z",
        universe_snapshot_id="universe-2026-07-25-817cc184bbb3",
        config_fingerprint=CONFIG.config_fingerprint(),
        bar_store_signature="mcp-test-signature",
        rows=[
            {
                "symbol": "AAPL",
                "side": "resistance",
                "band_class": "A",
                "distance_bps": 12.5,
                "band_score": 3.1,
                "price_low": 300.0,
                "price_high": 302.0,
                "coverage": {"1d": {"has_bars": True, "latest_window_end_utc": "2026-06-22T00:00:00Z"}},
                "tick_evidence": True,
            }
        ],
        skipped=[
            {
                "symbol": "PG",
                "skipped": True,
                "reason": "no_bars",
                "coverage": {"1d": {"has_bars": False, "latest_window_end_utc": None}},
                "tick_evidence": False,
            }
        ],
    )
    result = await call_tool("desk_screen", {})
    rest = httpx.get(f"{mcp_env}/research/desk/screen", timeout=5.0)
    assert rest.status_code == 200
    body = rest.json()
    assert len(body["screens"]) >= 1, "the live list must be non-empty for this proof"
    assert body["latest"] is not None
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "desk_screen not byte-identical"


@pytest.mark.anyio
async def test_get_endpoint_desk_screen_date_query_proxies_verbatim(mcp_env, backend_paths):
    """TC-6/TC-7: ``get_endpoint`` reaches the ``?date=`` lookup variant ``desk_screen`` itself
    does not expose -- byte-identical for a matching date (seeded HERE, under its own distinct
    date -- audit B1 fix, so this test passes standalone, never relying on
    ``test_desk_screen_tool_byte_identical_on_a_populated_state``'s side effect), and the honest
    ``{"screen": null}`` 200 (never a 404, never an error) for a non-matching one."""
    screen_dir = Path(backend_paths["TAPEOLOGY_DESK_SCREEN_DIR"])
    ScreenStore(screen_dir).record(
        screen_date=DESK_SCREEN_ISOLATED_DATE,
        as_of="2026-06-23T21:00:00Z",
        universe_snapshot_id="universe-2026-07-25-817cc184bbb3",
        config_fingerprint=CONFIG.config_fingerprint(),
        bar_store_signature="mcp-test-isolated-date-signature",
        rows=[
            {
                "symbol": "AAPL",
                "side": "resistance",
                "band_class": "A",
                "distance_bps": 12.5,
                "band_score": 3.1,
                "price_low": 300.0,
                "price_high": 302.0,
                "coverage": {"1d": {"has_bars": True, "latest_window_end_utc": "2026-06-23T00:00:00Z"}},
                "tick_evidence": True,
            }
        ],
        skipped=[],
    )

    matching_path = f"/research/desk/screen?date={DESK_SCREEN_ISOLATED_DATE}"
    result = await call_tool("get_endpoint", {"path": matching_path})
    rest = httpx.get(f"{mcp_env}{matching_path}", timeout=5.0)
    assert rest.status_code == 200
    assert rest.json()["screen"] is not None
    assert result.isError is False
    assert result.content[0].text.encode("utf-8") == rest.content, "desk screen date-match not byte-identical"

    nonmatch_path = f"/research/desk/screen?date={DESK_SCREEN_NONMATCH_DATE}"
    result = await call_tool("get_endpoint", {"path": nonmatch_path})
    rest = httpx.get(f"{mcp_env}{nonmatch_path}", timeout=5.0)
    assert rest.status_code == 200
    assert rest.json() == {"screen": None}
    assert result.isError is False
    assert result.content[0].text.encode("utf-8") == rest.content, "desk screen date-nonmatch not byte-identical"


@pytest.mark.anyio
async def test_get_endpoint_desk_screen_id_query_proxies_verbatim(mcp_env, backend_paths):
    """goal-desk-iter-16 (J-12) TC-7: ``get_endpoint`` reaches the NEW ``?id=`` lookup variant with
    ZERO MCP code change (the existing ``/research/`` allowlist prefix already covers it) --
    byte-identical for a matching id (seeded HERE, under its own distinct date so this test passes
    standalone) and the honest ``{"screen": null}`` 200 for an unknown id (never a 404)."""
    screen_dir = Path(backend_paths["TAPEOLOGY_DESK_SCREEN_DIR"])
    recorded = ScreenStore(screen_dir).record(
        screen_date="2026-07-27",
        as_of="2026-07-27T21:00:00Z",
        universe_snapshot_id="universe-2026-07-25-817cc184bbb3",
        config_fingerprint=CONFIG.config_fingerprint(),
        bar_store_signature="mcp-test-id-query-signature",
        rows=[
            {
                "symbol": "NFLX",
                "side": "resistance",
                "band_class": "A",
                "distance_bps": 8.0,
                "band_score": 2.5,
                "price_low": 400.0,
                "price_high": 402.0,
                "coverage": {"1d": {"has_bars": True, "latest_window_end_utc": "2026-07-27T00:00:00Z"}},
                "tick_evidence": True,
            }
        ],
        skipped=[],
    )

    matching_path = f"/research/desk/screen?id={recorded['id']}"
    result = await call_tool("get_endpoint", {"path": matching_path})
    rest = httpx.get(f"{mcp_env}{matching_path}", timeout=5.0)
    assert rest.status_code == 200
    assert rest.json()["screen"] is not None
    assert rest.json()["screen"]["id"] == recorded["id"]
    assert result.isError is False
    assert result.content[0].text.encode("utf-8") == rest.content, "desk screen id-match not byte-identical"

    nonmatch_path = "/research/desk/screen?id=does-not-exist"
    result = await call_tool("get_endpoint", {"path": nonmatch_path})
    rest = httpx.get(f"{mcp_env}{nonmatch_path}", timeout=5.0)
    assert rest.status_code == 200
    assert rest.json() == {"screen": None}
    assert result.isError is False
    assert result.content[0].text.encode("utf-8") == rest.content, "desk screen id-nonmatch not byte-identical"


@pytest.mark.anyio
async def test_desk_screen_reference_close_field_proxies_verbatim(mcp_env, backend_paths):
    """goal-desk-iter-17 (J-13) TC-10: `reference_close` -- `desk_screen.py`'s new ranked-row field
    -- is proxied byte-identical through both the `desk_screen` tool (no-arg) and `get_endpoint`'s
    existing `/research/` allowlist prefix (`?date=`), with ZERO MCP code change -- the same proxy
    contract every prior `desk_screen` row-field addition (basis/history) already covers
    automatically. Seeded under its own distinct date so this test passes standalone."""
    screen_dir = Path(backend_paths["TAPEOLOGY_DESK_SCREEN_DIR"])
    ScreenStore(screen_dir).record(
        screen_date="2026-07-29",
        as_of="2026-07-29T21:00:00Z",
        universe_snapshot_id="universe-2026-07-25-817cc184bbb3",
        config_fingerprint=CONFIG.config_fingerprint(),
        bar_store_signature="mcp-test-reference-close-signature",
        rows=[
            {
                "symbol": "AMZN",
                "side": "resistance",
                "band_class": "A",
                "distance_bps": 5.0,
                "band_score": 4.2,
                "price_low": 200.0,
                "price_high": 202.0,
                "coverage": {"1d": {"has_bars": True, "latest_window_end_utc": "2026-07-29T00:00:00Z"}},
                "tick_evidence": True,
                "reference_close": 199.9,
            }
        ],
        skipped=[],
    )

    result = await call_tool("desk_screen", {})
    rest = httpx.get(f"{mcp_env}/research/desk/screen", timeout=5.0)
    assert rest.status_code == 200
    assert rest.json()["latest"]["rows"][0]["reference_close"] == 199.9
    assert result.isError is False
    assert result.content[0].text.encode("utf-8") == rest.content, (
        "reference_close not byte-identical via the desk_screen tool"
    )

    date_path = "/research/desk/screen?date=2026-07-29"
    result = await call_tool("get_endpoint", {"path": date_path})
    rest = httpx.get(f"{mcp_env}{date_path}", timeout=5.0)
    assert rest.status_code == 200
    assert rest.json()["screen"]["rows"][0]["reference_close"] == 199.9
    assert result.isError is False
    assert result.content[0].text.encode("utf-8") == rest.content, (
        "reference_close not byte-identical via get_endpoint"
    )


@pytest.mark.anyio
async def test_desk_screen_opposite_band_and_bands_by_class_fields_proxy_verbatim(mcp_env, backend_paths):
    """goal-desk-iter-18 (J-14) TC-14: `opposite_band`/`bands_by_class` -- `desk_screen.py`'s two
    newest ranked-row fields -- are proxied byte-identical through both the `desk_screen` tool
    (no-arg) and `get_endpoint`'s existing `/research/` allowlist prefix (`?date=`), with ZERO MCP
    code change -- the same proxy contract every prior `desk_screen` row-field addition (basis/
    history/reference-close) already covers automatically. Seeded under its own distinct date so
    this test passes standalone."""
    screen_dir = Path(backend_paths["TAPEOLOGY_DESK_SCREEN_DIR"])
    ScreenStore(screen_dir).record(
        screen_date="2026-07-30",
        as_of="2026-07-30T21:00:00Z",
        universe_snapshot_id="universe-2026-07-25-817cc184bbb3",
        config_fingerprint=CONFIG.config_fingerprint(),
        bar_store_signature="mcp-test-opposite-band-signature",
        rows=[
            {
                "symbol": "AMZN",
                "side": "resistance",
                "band_class": "A",
                "distance_bps": 5.0,
                "band_score": 4.2,
                "price_low": 200.0,
                "price_high": 202.0,
                "coverage": {"1d": {"has_bars": True, "latest_window_end_utc": "2026-07-30T00:00:00Z"}},
                "tick_evidence": True,
                "reference_close": 199.9,
                "opposite_band": {
                    "side": "support",
                    "band_class": "B",
                    "price_low": 190.0,
                    "price_high": 191.0,
                    "band_score": 2.1,
                    "distance_bps": 452.2,
                },
                "bands_by_class": {"A": 1, "B": 1, "C": 0, "unclassified": 0},
            }
        ],
        skipped=[],
    )

    result = await call_tool("desk_screen", {})
    rest = httpx.get(f"{mcp_env}/research/desk/screen", timeout=5.0)
    assert rest.status_code == 200
    row = rest.json()["latest"]["rows"][0]
    assert row["opposite_band"]["band_class"] == "B"
    assert row["bands_by_class"] == {"A": 1, "B": 1, "C": 0, "unclassified": 0}
    assert result.isError is False
    assert result.content[0].text.encode("utf-8") == rest.content, (
        "opposite_band/bands_by_class not byte-identical via the desk_screen tool"
    )

    date_path = "/research/desk/screen?date=2026-07-30"
    result = await call_tool("get_endpoint", {"path": date_path})
    rest = httpx.get(f"{mcp_env}{date_path}", timeout=5.0)
    assert rest.status_code == 200
    row = rest.json()["screen"]["rows"][0]
    assert row["opposite_band"]["band_class"] == "B"
    assert row["bands_by_class"] == {"A": 1, "B": 1, "C": 0, "unclassified": 0}
    assert result.isError is False
    assert result.content[0].text.encode("utf-8") == rest.content, (
        "opposite_band/bands_by_class not byte-identical via get_endpoint"
    )


@pytest.mark.anyio
async def test_datasets_tool_byte_identical_on_a_non_empty_live_list(mcp_env, backend_paths):
    """J-02 flips ``datasets`` from honest 404 to live data with ZERO MCP code changes: after
    recording a dataset (the committed reference window, keyless), the tool's JSON is
    byte-identical to its curl equivalent on a NON-EMPTY 200 list.

    era-fast_wall J-02 (TC-8, MCP leg): every recorded dataset file's mtime is pushed past the
    ~2s racy-write guard via a direct disk ``os.utime`` call BEFORE the byte-identity calls below
    (the SAME filesystem the subprocess backend itself reads — there is no in-process reset
    possible against a separate OS process, unlike the same-process proof in
    ``test_datasets_api.py``). Without this, a freshly-recorded file's own racy-write guard would
    force every read cold for this short-lived test, silently never exercising the WARM-cache
    path the datasets.py metadata cache adds — the extension the iter-1-applied lesson calls for
    (this exact test previously depended on module-scoped shared-backend state; the fix here must
    hold both standalone and inside the full module, so it deliberately ages EVERY file in the
    dataset dir rather than just the one this call may or may not have just recorded)."""
    recorded = httpx.post(
        f"{mcp_env}/research/datasets",
        json={
            "source_kind": "reference",
            "split": "train",
            "start": "2026-06-09T17:00:00Z",
            "end": "2026-06-09T17:00:30Z",
        },
        timeout=15.0,
    )
    assert recorded.status_code in (200, 409)  # 409 = already recorded by an earlier run/test

    dataset_dir = Path(backend_paths["TAPEOLOGY_DATASET_DIR"])
    past = time.time() - 5.0
    for f in dataset_dir.glob("*.json"):
        os.utime(f, (past, past))

    warm_up = httpx.get(f"{mcp_env}/research/datasets", timeout=5.0)  # populate the warm cache
    assert warm_up.status_code == 200

    result = await call_tool("datasets", {})
    rest = httpx.get(f"{mcp_env}/research/datasets", timeout=5.0)
    assert rest.status_code == 200
    assert len(rest.json()["datasets"]) >= 1, "the live list must be non-empty for this proof"
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "datasets not byte-identical"


@pytest.mark.anyio
async def test_bars_tool_byte_identical_on_a_non_empty_live_list(mcp_env, backend_paths):
    """``bars`` (era-4 J-01) ships in the SAME iteration as its endpoint — there is no honest-404
    state to prove a flip from (unlike the J-02/J-03/J-04 tools, which shipped after their MCP
    entries already existed). Recording real bars needs live Alpaca credentials, which CI does not
    have, so this proves byte-identity on a NON-EMPTY list by seeding the live backend's bar
    directory with the committed KEYLESS fixture pair directly (no vendor call, no credentials
    touched) — the same store directory the running backend's ``GET /research/bars`` reads fresh
    on every call."""
    bar_dir = Path(backend_paths["TAPEOLOGY_BAR_DIR"])
    fixtures = list(FIXTURE_BAR_DIR.glob("*.json"))
    assert fixtures, "the committed bar fixture directory must not be empty"
    for fixture in fixtures:
        shutil.copy(fixture, bar_dir / fixture.name)
    result = await call_tool("bars", {})
    rest = httpx.get(f"{mcp_env}/research/bars", timeout=5.0)
    assert rest.status_code == 200
    assert len(rest.json()["bar_series"]) >= 1, "the live list must be non-empty for this proof"
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "bars not byte-identical"


@pytest.mark.anyio
async def test_levels_tool_byte_identical_on_a_non_empty_live_result(mcp_env, backend_paths):
    """``levels`` (era-4 J-02, confluence zones added at J-03) ships in the SAME iteration as its
    endpoint — the ``bars`` J-01 precedent: seed the live backend's bar directory with the
    committed KEYLESS fixture pair directly (no vendor call, no credentials touched), then prove
    the two-argument tool's JSON is byte-identical to its curl equivalent on a NON-EMPTY result --
    including the ``confluence_zones`` field (J-03), so this proxy proof meaningfully covers it too
    (not merely a vacuous byte-match on an empty list)."""
    bar_dir = Path(backend_paths["TAPEOLOGY_BAR_DIR"])
    fixtures = list(FIXTURE_BAR_DIR.glob("*.json"))
    assert fixtures, "the committed bar fixture directory must not be empty"
    for fixture in fixtures:
        shutil.copy(fixture, bar_dir / fixture.name)
    as_of = "2026-06-09T21:00:00Z"  # at/after both fixtures' window_end_utc
    result = await call_tool("levels", {"symbol": "PG", "as_of": as_of})
    rest = httpx.get(f"{mcp_env}/research/levels", params={"symbol": "PG", "as_of": as_of}, timeout=5.0)
    assert rest.status_code == 200
    assert len(rest.json()["levels"]) >= 1, "the live result must be non-empty for this proof"
    assert len(rest.json()["confluence_zones"]) >= 1, "the live zones must be non-empty for this proof"
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "levels not byte-identical"


@pytest.mark.anyio
async def test_levels_tool_byte_identical_on_a_non_empty_live_result_on_the_yahoo_fixture(
    mcp_env, backend_paths
):
    """era-5 J-04: the SAME byte-identity proof as
    `test_levels_tool_byte_identical_on_a_non_empty_live_result` above, re-run on a REAL Yahoo
    (`feed="yahoo"`) bar series instead of the PG/`sip` fixture -- confirms the levels/MCP glue
    serves Yahoo-sourced data identically, with no second, feed-specific code path anywhere (the
    defining "single source of truth" acceptance). Seeded HERMETICALLY (no network, no `yfinance`
    call): the committed raw-capture Yahoo fixtures (`tests/fixtures/yahoo/`) are written directly
    through the real `BarStore.record()` API (bypassing the adapter/route -- this test's backend is
    a SEPARATE subprocess, so `test_levels_api.py`'s in-process `yfinance.Ticker` monkeypatch seam
    is not reachable here; `BarStore.record()` is the SAME persistence call the route itself makes,
    just invoked directly with the real captured Yahoo OHLCV, stamped `feed="yahoo"`) into the live
    backend's bar dir -- the SAME `shutil.copy`-into-`bar_dir` precedent
    `test_bars_tool_byte_identical_on_a_non_empty_live_list` and the PG version of this test already
    use, just generated from the committed Yahoo capture instead of pre-existing in `BarStore`'s
    on-disk format (independently confirmed to reproduce byte-identical levels/zones to the real
    adapter+route path via a standalone probe before this test was written)."""
    bar_dir = Path(backend_paths["TAPEOLOGY_BAR_DIR"])
    store = BarStore(bar_dir)
    for name in ("AAPL_1d_20260601_20260604.json", "AAPL_1h_20260601_20260603.json"):
        fixture = json.loads((YAHOO_FIXTURE_DIR / name).read_text())
        bars = [
            RawBar(
                fixture["symbol"], fixture["timeframe"], b["epoch"],
                b["open"], b["high"], b["low"], b["close"], b["volume"],
            )
            for b in fixture["bars"]
        ]
        store.record(
            symbol=fixture["symbol"],
            timeframe=fixture["timeframe"],
            window_start_utc=fixture["start"],
            window_end_utc=fixture["end"],
            feed="yahoo",
            bars=bars,
        )

    as_of = "2026-06-05T00:00:00Z"  # at/after both fixtures' actual last bar
    result = await call_tool("levels", {"symbol": "AAPL", "as_of": as_of})
    rest = httpx.get(f"{mcp_env}/research/levels", params={"symbol": "AAPL", "as_of": as_of}, timeout=5.0)
    assert rest.status_code == 200
    assert rest.json()["no_bar_series_for_symbol"] is False
    assert len(rest.json()["levels"]) >= 1, "the live result must be non-empty for this proof"
    assert len(rest.json()["confluence_zones"]) >= 1, "the live zones must be non-empty for this proof"
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "levels not byte-identical on Yahoo data"


@pytest.mark.anyio
async def test_levels_tool_requires_both_arguments(monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_API_BASE", _dead_base())
    with pytest.raises(ToolArgumentError):
        await call_tool("levels", {"as_of": "2026-06-09T21:00:00Z"})
    with pytest.raises(ToolArgumentError):
        await call_tool("levels", {"symbol": "PG"})
    with pytest.raises(ToolArgumentError):
        await call_tool("levels", {})


@pytest.mark.anyio
async def test_tradability_tool_byte_identical_on_a_non_empty_live_result(mcp_env, backend_paths):
    """``tradability`` (era-5B J-01) ships in the SAME iteration as its endpoint -- the ``bars``
    J-01 / ``levels`` J-02 precedent: seed the live backend's bar directory with the committed
    real AAPL daily fixture (``BarStore.record()`` directly, the ``test_levels_tool_...
    _on_the_yahoo_fixture`` technique -- this test's backend is a SEPARATE subprocess, so an
    in-process ``yfinance.Ticker`` monkeypatch seam is not reachable here), then prove the
    two-argument tool's JSON is byte-identical to its curl equivalent on a NON-EMPTY result,
    including J-01's pinned AAPL 2026-06-22 acceptance (the top resistance band containing both
    300.48 and 302.07), so this proxy proof meaningfully covers real bands (not a vacuous empty
    match)."""
    bar_dir = Path(backend_paths["TAPEOLOGY_BAR_DIR"])
    store = BarStore(bar_dir)
    fixture = json.loads((YAHOO_FIXTURE_DIR / "AAPL_1d_20260101_20260626.json").read_text())
    bars = [
        RawBar(
            fixture["symbol"], fixture["timeframe"], b["epoch"],
            b["open"], b["high"], b["low"], b["close"], b["volume"],
        )
        for b in fixture["bars"]
    ]
    store.record(
        symbol=fixture["symbol"], timeframe=fixture["timeframe"],
        window_start_utc=fixture["start"], window_end_utc=fixture["end"],
        feed="yahoo", bars=bars,
    )

    as_of = "2026-06-22T15:00:00Z"
    result = await call_tool("tradability", {"symbol": "AAPL", "as_of": as_of})
    rest = httpx.get(f"{mcp_env}/research/tradability", params={"symbol": "AAPL", "as_of": as_of}, timeout=5.0)
    assert rest.status_code == 200
    body = rest.json()
    assert body["no_bar_series_for_symbol"] is False
    assert len(body["bands"]) >= 1, "the live result must be non-empty for this proof"
    resistance = [b for b in body["bands"] if b["side"] == "resistance"]
    pinned = next(b for b in resistance if b["price_low"] <= 300.48 and b["price_high"] >= 302.07)
    assert resistance.index(pinned) in (0, 1)
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "tradability not byte-identical"


@pytest.mark.anyio
async def test_tradability_tool_requires_both_arguments(monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_API_BASE", _dead_base())
    with pytest.raises(ToolArgumentError):
        await call_tool("tradability", {"as_of": "2026-06-22T15:00:00Z"})
    with pytest.raises(ToolArgumentError):
        await call_tool("tradability", {"symbol": "AAPL"})
    with pytest.raises(ToolArgumentError):
        await call_tool("tradability", {})


@pytest.mark.anyio
async def test_setups_tool_byte_identical_on_a_non_empty_live_result(mcp_env, backend_paths):
    """``setups`` (era-5B J-02) ships in the SAME iteration as its endpoint -- the ``bars``/
    ``tradability`` J-01 precedent: seed the live backend's bar directory with the committed real
    AAPL daily fixture PLUS the committed real AAPL 5-minute slice (``BarStore.record()`` directly
    -- this test's backend is a SEPARATE subprocess, so an in-process fixture-seeding seam is not
    reachable here), then prove the NO-ARGUMENT tool's JSON is byte-identical to its curl
    equivalent on a NON-EMPTY result, including J-02's pinned AAPL 2026-06-22 `rejected` event (not
    a vacuous empty-list match)."""
    bar_dir = Path(backend_paths["TAPEOLOGY_BAR_DIR"])
    store = BarStore(bar_dir)
    for name in ("AAPL_1d_20260101_20260626.json", "AAPL_5m_20260615_20260630.json"):
        fixture = json.loads((YAHOO_FIXTURE_DIR / name).read_text())
        bars = [
            RawBar(
                fixture["symbol"], fixture["timeframe"], b["epoch"],
                b["open"], b["high"], b["low"], b["close"], b["volume"],
            )
            for b in fixture["bars"]
        ]
        try:
            store.record(
                symbol=fixture["symbol"], timeframe=fixture["timeframe"],
                window_start_utc=fixture["start"], window_end_utc=fixture["end"],
                feed="yahoo", bars=bars,
            )
        except BarSeriesAlreadyRegistered:
            pass  # already recorded by an earlier test sharing this module-scoped bar_dir/backend

    result = await call_tool("setups", {})
    rest = httpx.get(f"{mcp_env}/research/setups", timeout=5.0)
    assert rest.status_code == 200
    body = rest.json()
    assert len(body["events"]) >= 1, "the live result must be non-empty for this proof"
    pinned = next(
        e for e in body["events"]
        if e["session_date"] == "2026-06-22" and e["band"]["side"] == "resistance"
        and e["band"]["price_low"] <= 300.48 and e["band"]["price_high"] >= 302.07
    )
    assert pinned["reaction"] == "rejected"
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "setups not byte-identical"


@pytest.mark.anyio
async def test_backtests_tool_byte_identical_on_a_non_empty_live_list(mcp_env):
    """J-03 flips ``backtests`` from honest 404 to live data with ZERO MCP code changes (the
    J-02 ``datasets`` precedent): after running a backtest to a TERMINAL status (so the stored
    row is frozen and byte comparisons cannot flap), the tool's JSON is byte-identical to its
    curl equivalent on a NON-EMPTY 200 list."""
    recorded = httpx.post(
        f"{mcp_env}/research/datasets",
        json={
            "source_kind": "reference",
            "split": "train",
            "start": "2026-06-09T17:00:00Z",
            "end": "2026-06-09T17:00:30Z",
        },
        timeout=15.0,
    )
    assert recorded.status_code in (200, 409)  # 409 = already recorded by an earlier test
    datasets = httpx.get(f"{mcp_env}/research/datasets", timeout=5.0).json()["datasets"]
    assert len(datasets) >= 1
    created = httpx.post(
        f"{mcp_env}/research/backtests",
        json={"dataset_id": datasets[0]["id"], "strategy_id": "v1", "profile": "default"},
        timeout=15.0,
    )
    assert created.status_code == 200, created.text
    backtest_id = created.json()["backtest"]["id"]
    deadline = time.time() + 30
    while time.time() < deadline:
        payload = httpx.get(f"{mcp_env}/research/backtests/{backtest_id}", timeout=5.0).json()["backtest"]
        if payload["status"] in ("done", "failed", "cancelled"):
            break
        time.sleep(0.2)
    assert payload["status"] == "done", payload.get("error")
    result = await call_tool("backtests", {})
    rest = httpx.get(f"{mcp_env}/research/backtests", timeout=5.0)
    assert rest.status_code == 200
    assert len(rest.json()["backtests"]) >= 1, "the live list must be non-empty for this proof"
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "backtests not byte-identical"


@pytest.mark.anyio
async def test_strategies_tool_byte_identical_on_a_non_empty_live_result(mcp_env):
    """``strategies`` (era-4 J-04) ships in the SAME iteration as its endpoint — unlike
    ``bars``/``levels``/``backtests``, the registry (``v1`` + ``structure_tape``) and the champion
    pointer are ALWAYS present (config-owned + auto-seeded at store-open), so this proves
    byte-identity on a NON-EMPTY result with no seeding at all."""
    result = await call_tool("strategies", {})
    rest = httpx.get(f"{mcp_env}/research/strategies", timeout=5.0)
    assert rest.status_code == 200
    assert len(rest.json()["strategies"]) >= 1, "the live registry must be non-empty for this proof"
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "strategies not byte-identical"


@pytest.mark.anyio
async def test_edge_report_tool_byte_identical_to_rest(mcp_env):
    """``edge_report`` (era-5B J-04) ships in the SAME iteration as its endpoint. era-fast_wall
    J-01 (TC-6): by this point in the module, an earlier test
    (``test_datasets_tool_byte_identical_on_a_non_empty_live_list``) has already registered a
    dataset against this SAME shared backend, and nothing in this module has called
    ``/research/edge-report`` before now — so the registry is genuinely non-empty and the cache is
    genuinely cold, and this GET naturally returns the not-computed payload rather than the
    era-5B full-report shape. Proves REST<->MCP byte-identity in exactly that new state, with no
    seeding of this test's own."""
    datasets = httpx.get(f"{mcp_env}/research/datasets", timeout=5.0).json()["datasets"]
    assert len(datasets) >= 1, "an earlier test in this module must have already registered one"

    result = await call_tool("edge_report", {})
    rest = httpx.get(f"{mcp_env}/research/edge-report", timeout=5.0)
    assert rest.status_code == 200
    payload = rest.json()
    assert payload.get("status") == "not_computed", (
        "expected the not-computed shape: registry is non-empty and nothing has warmed the cache"
    )
    assert set(payload) == {"status", "detail", "dataset_count", "register", "compute"}
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "edge_report not byte-identical"


@pytest.mark.anyio
async def test_edge_report_tool_byte_identical_after_recording_a_real_dataset(mcp_env):
    """The IDENTICAL ``datasets``/``backtests`` "flips from empty to a real state with ZERO MCP
    code changes" precedent: after recording ANOTHER real dataset through the live backend, the
    tool's JSON is still byte-identical to its curl equivalent — still the not-computed shape here
    (era-fast_wall J-01: nothing in this module ever warms the cache, so the cache stays cold for
    the rest of the module too) — but the byte-proxy discipline itself is what this test exists to
    prove, on a request whose ``dataset_count`` has now genuinely changed."""
    recorded = httpx.post(
        f"{mcp_env}/research/datasets",
        json={
            "source_kind": "reference",
            "split": "train",
            "start": "2026-06-09T17:01:00Z",
            "end": "2026-06-09T17:01:30Z",
        },
        timeout=15.0,
    )
    assert recorded.status_code in (200, 409)  # 409 = already recorded by an earlier test
    result = await call_tool("edge_report", {})
    rest = httpx.get(f"{mcp_env}/research/edge-report", timeout=15.0)
    assert rest.status_code == 200
    assert result.isError is False
    assert result.content[0].text.encode("utf-8") == rest.content, "edge_report not byte-identical"


@pytest.mark.anyio
async def test_pnl_ledger_tool_byte_identical_on_a_non_empty_200(mcp_env, backend_paths):
    """J-04 flips ``pnl_ledger`` — the LAST honest 404 — to live data with ZERO MCP code changes
    (the J-02 ``datasets`` / J-03 ``backtests`` precedent): after the REAL keyless seeding CLI
    (``python -m app.research.pnl_baseline``) appends the founding baseline row into the SAME
    journal DB the backend serves, the tool's JSON is byte-identical to its curl equivalent on a
    NON-EMPTY 200 carrying the founding row. The CLI re-run is the honest idempotence leg: an
    explicit "already present" no-op message and a clean exit — no duplicate row."""
    env = os.environ.copy()
    env.update(backend_paths)
    first = subprocess.run(
        [sys.executable, "-m", "app.research.pnl_baseline"],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=180,
    )
    assert first.returncode == 0, f"seeding CLI failed:\n{first.stderr}"
    second = subprocess.run(
        [sys.executable, "-m", "app.research.pnl_baseline"],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=180,
    )
    assert second.returncode == 0, f"seeding CLI re-run failed:\n{second.stderr}"
    assert "already present" in second.stdout
    result = await call_tool("pnl_ledger", {})
    rest = httpx.get(f"{mcp_env}/research/pnl/ledger", timeout=5.0)
    assert rest.status_code == 200
    rows = rest.json()["rows"]
    assert len(rows) == 1, "the live ledger must carry exactly the founding row for this proof"
    assert rows[0]["founding"] is True and rows[0]["baseline"] is None
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "pnl_ledger not byte-identical"


@pytest.mark.anyio
async def test_tape_history_bar_argument_proxies_the_same_query(mcp_env):
    bar = CONFIG.history_bar_sizes[-1]
    result = await call_tool("tape_history", {"ticker": "SIM-BUYER", "bar": bar})
    rest = httpx.get(f"{mcp_env}/tape/SIM-BUYER/history?bar={bar}", timeout=5.0)
    assert rest.status_code == 200
    assert result.isError is False
    assert result.content[0].text.encode("utf-8") == rest.content


@pytest.mark.anyio
async def test_backend_422_surfaced_explicitly_with_verbatim_payload(mcp_env):
    """A rejected value (bar outside the configured set) proxies the backend's real 422."""
    bad_bar = 999999
    assert bad_bar not in CONFIG.history_bar_sizes
    result = await call_tool("tape_history", {"ticker": "SIM-BUYER", "bar": bad_bar})
    rest = httpx.get(f"{mcp_env}/tape/SIM-BUYER/history?bar={bad_bar}", timeout=5.0)
    assert rest.status_code == 422
    assert result.isError is True
    assert result.content[0].text.encode("utf-8") == rest.content
    assert result.content[1].text == f"HTTP 422 from GET /tape/SIM-BUYER/history?bar={bad_bar}"


@pytest.mark.anyio
async def test_not_watched_ticker_404_proxied_verbatim(mcp_env):
    result = await call_tool("tape_state", {"ticker": "SIM-SELLER"})
    rest = httpx.get(f"{mcp_env}/tape/SIM-SELLER/state", timeout=5.0)
    assert rest.status_code == 404
    assert result.isError is True
    assert result.content[0].text.encode("utf-8") == rest.content
    assert result.content[1].text == "HTTP 404 from GET /tape/SIM-SELLER/state"


# --- get_endpoint allowlist -------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_endpoint_proxies_allowlisted_paths_verbatim(mcp_env):
    for path in ("/tape/SIM-BUYER/state", "/research/taxonomy", "/meta/ui-routes"):
        result = await call_tool("get_endpoint", {"path": path})
        rest = httpx.get(f"{mcp_env}{path}", timeout=5.0)
        assert rest.status_code == 200
        assert result.isError is False
        assert result.content[0].text.encode("utf-8") == rest.content


@pytest.mark.anyio
async def test_get_endpoint_proxies_allowlisted_but_unknown_path_404_verbatim(mcp_env):
    """An allowlisted PREFIX does not guarantee a real endpoint: a permanently-unknown
    ``/research/*`` path surfaces the backend's real 404 verbatim — not refused, not
    synthesized. (Relocated from ``/research/profiles`` when J-05 shipped that endpoint —
    the honest-404 behavior itself stays covered.)"""
    result = await call_tool("get_endpoint", {"path": UNKNOWN_RESEARCH_PATH})
    rest = httpx.get(f"{mcp_env}{UNKNOWN_RESEARCH_PATH}", timeout=5.0)
    assert rest.status_code == 404
    assert result.isError is True
    assert result.content[0].text.encode("utf-8") == rest.content
    assert result.content[1].text == f"HTTP 404 from GET {UNKNOWN_RESEARCH_PATH}"


@pytest.mark.anyio
async def test_get_endpoint_proxies_a_deleted_route_404_verbatim(mcp_env):
    """clean_slate J-03: unlike ``UNKNOWN_RESEARCH_PATH`` (a path that was NEVER real),
    ``/research/journal`` WAS a real, shipped route — proxied by the now-removed ``journal`` MCP
    tool — until clean_slate J-01 deleted its route handler. The honest-404 contract must hold
    identically for an ACTUALLY-deleted route: the backend's real 404 payload verbatim, plus the
    explicit status message, never a synthesized or cached response."""
    result = await call_tool("get_endpoint", {"path": DELETED_RESEARCH_ROUTE})
    rest = httpx.get(f"{mcp_env}{DELETED_RESEARCH_ROUTE}", timeout=5.0)
    assert rest.status_code == 404
    assert result.isError is True
    assert result.content[0].text.encode("utf-8") == rest.content
    assert result.content[1].text == f"HTTP 404 from GET {DELETED_RESEARCH_ROUTE}"


@pytest.mark.anyio
async def test_get_endpoint_profiles_byte_identical_on_the_live_200(mcp_env):
    """J-05 flips ``/research/profiles`` from honest 404 to live data with ZERO MCP code changes
    (the J-02/J-03/J-04 precedent, this time through ``get_endpoint`` — the blueprint routes
    profiles through it rather than a dedicated tool): the proxied JSON is byte-identical to its
    curl equivalent on the live 200."""
    result = await call_tool("get_endpoint", {"path": "/research/profiles"})
    rest = httpx.get(f"{mcp_env}/research/profiles", timeout=5.0)
    assert rest.status_code == 200
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "profiles not byte-identical"


@pytest.mark.anyio
async def test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool(mcp_env):
    """goal-desk-iter-11 TC-9 (J-09): the NEW ``GET /research/desk/topup/runs`` route is reachable
    through ``get_endpoint``'s existing ``/research/`` allowlist prefix with ZERO MCP code change —
    no new tool, no ``_STATIC_PATHS`` entry — and the proxied body is byte-identical to its curl
    equivalent (here the honest-empty ``{"runs": [], "latest": null, "integrity_errors": []}`` this
    module-scoped backend's own temp desk dirs genuinely produce — the ``integrity_errors`` key
    goal-desk-iter-16/J-12 added). The tool count assertion lives in
    ``test_advertised_tool_set_is_exactly_capability_6``; this is the reachability half TC-9 names
    separately."""
    result = await call_tool("get_endpoint", {"path": "/research/desk/topup/runs"})
    rest = httpx.get(f"{mcp_env}/research/desk/topup/runs", timeout=5.0)
    assert rest.status_code == 200
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "topup/runs not byte-identical"
    assert rest.json() == {"runs": [], "latest": None, "integrity_errors": []}
    assert "desk_topup_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 17


@pytest.mark.anyio
async def test_get_endpoint_desk_screen_runs_byte_identical_with_no_new_tool(mcp_env):
    """goal-desk-iter-29 TC-1 (J-18): the NEW ``GET /research/desk/screen/runs`` route is reachable
    through ``get_endpoint``'s existing ``/research/`` allowlist prefix with ZERO MCP code change —
    no new tool, no ``_STATIC_PATHS`` entry — and the proxied body is byte-identical to its curl
    equivalent (here the honest-empty ``{"runs": [], "latest": null, "integrity_errors": []}`` this
    module-scoped backend's own temp desk dirs genuinely produce -- no test in this module ever
    triggers a screen compute). The tool count assertion lives in
    ``test_advertised_tool_set_is_exactly_capability_6``; this is the reachability half."""
    result = await call_tool("get_endpoint", {"path": "/research/desk/screen/runs"})
    rest = httpx.get(f"{mcp_env}/research/desk/screen/runs", timeout=5.0)
    assert rest.status_code == 200
    assert result.isError is False
    assert len(result.content) == 1
    assert result.content[0].text.encode("utf-8") == rest.content, "screen/runs not byte-identical"
    assert rest.json() == {"runs": [], "latest": None, "integrity_errors": []}
    assert "desk_screen_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 17


@pytest.mark.anyio
async def test_get_endpoint_refuses_non_allowlisted_paths_without_any_request(monkeypatch):
    """Refusal is decided BEFORE any request: with the backend base pointing at a dead port,
    a refused path must raise the refusal (an unreachable error would prove a request was
    attempted)."""
    monkeypatch.setenv("TAPEOLOGY_API_BASE", _dead_base())
    for path in (
        "/health",
        "/watch/SIM-BUYER",
        "/symbols/search?q=A",
        "/watch/SIM-BUYER/pause",
        "tape/SIM-BUYER/state",  # relative
        "//evil.example/tape/SIM-BUYER/state",  # protocol-relative
        "/tape/../health",  # traversal
        "/metatarsal",  # prefix lookalike (no slash)
        "",
    ):
        with pytest.raises(PathRefusedError) as excinfo:
            await call_tool("get_endpoint", {"path": path})
        assert "refused" in str(excinfo.value)
        assert "no request was sent" in str(excinfo.value)
    with pytest.raises(PathRefusedError):
        await call_tool("get_endpoint", {"path": None})


def test_allowlist_prefixes_are_exactly_the_canonical_read_surface():
    assert ALLOWED_GET_PREFIXES == ("/tape/", "/research/", "/meta/")


# --- Honest failure: backend down --------------------------------------------------------------


@pytest.mark.anyio
async def test_backend_down_every_tool_raises_an_explicit_error(monkeypatch):
    """With the backend stopped, EVERY tool errors explicitly — nothing cached, nothing
    fabricated (there is no cache in the module at all)."""
    dead = _dead_base()
    monkeypatch.setenv("TAPEOLOGY_API_BASE", dead)
    args_for = {
        "tape_state": {"ticker": "SIM-BUYER"},
        "tape_features": {"ticker": "SIM-BUYER"},
        "tape_history": {"ticker": "SIM-BUYER"},
        "levels": {"symbol": "PG", "as_of": "2026-06-09T21:00:00Z"},
        "tradability": {"symbol": "AAPL", "as_of": "2026-06-22T15:00:00Z"},
        "get_endpoint": {"path": "/meta/ui-routes"},
    }
    for name in EXPECTED_TOOLS:
        with pytest.raises(BackendUnreachableError) as excinfo:
            await call_tool(name, args_for.get(name, {}))
        message = str(excinfo.value)
        assert "unreachable" in message and dead in message
        assert "no cached or fabricated data" in message


@pytest.mark.anyio
async def test_unknown_tool_and_missing_argument_error_explicitly(monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_API_BASE", _dead_base())
    with pytest.raises(UnknownToolError) as excinfo:
        await call_tool("drop_tables", {})
    assert "read-only" in str(excinfo.value)
    with pytest.raises(ToolArgumentError):
        await call_tool("tape_state", {})


# --- The real thing: stdio session against python -m app.mcp -----------------------------------


@pytest.mark.anyio
async def test_stdio_session_end_to_end(watched_backend):
    """Spawn the ACTUAL ``python -m app.mcp`` subprocess and speak MCP over stdio (the J-01
    client flow): list tools, verify byte-identity vs curl-equivalent GETs, and verify the
    wire form of honest errors (``isError`` + explicit message)."""
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp"],
        cwd=str(BACKEND_DIR),
        env={"TAPEOLOGY_API_BASE": watched_backend},
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            listed = await session.list_tools()
            assert tuple(t.name for t in listed.tools) == EXPECTED_TOOLS

            # Byte-identity over the wire: tool JSON == curl-equivalent body.
            for name, args, path in (
                ("tape_state", {"ticker": "SIM-BUYER"}, "/tape/SIM-BUYER/state"),
                ("ui_route_map", {}, "/meta/ui-routes"),
            ):
                result = await session.call_tool(name, args)
                rest = httpx.get(f"{watched_backend}{path}", timeout=5.0)
                assert result.isError is False
                assert result.content[0].text.encode("utf-8") == rest.content

            # Honest 404 over the wire: verbatim payload + explicit status, isError set.
            # (Every registered endpoint has shipped — ``/research/profiles`` at J-05 — so the
            # honest-404 wire form is proven on a permanently-unknown ``/research/*`` path.)
            result = await session.call_tool("get_endpoint", {"path": UNKNOWN_RESEARCH_PATH})
            rest = httpx.get(f"{watched_backend}{UNKNOWN_RESEARCH_PATH}", timeout=5.0)
            assert rest.status_code == 404
            assert result.isError is True
            assert result.content[0].text.encode("utf-8") == rest.content
            assert result.content[1].text == f"HTTP 404 from GET {UNKNOWN_RESEARCH_PATH}"

            # Refusal over the wire: the SDK surfaces the raised refusal as an isError result.
            result = await session.call_tool("get_endpoint", {"path": "/health"})
            assert result.isError is True
            assert "refused" in result.content[0].text
            assert "no request was sent" in result.content[0].text
