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

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Capability 6, verbatim — order and content are the advertised contract. ``bars`` (era-4 J-01) is
# the newest addition, positioned right after its ``datasets`` sibling (the same store+route+MCP
# shape, mirrored end to end).
EXPECTED_TOOLS = (
    "tape_state",
    "tape_features",
    "tape_history",
    "journal",
    "analytics",
    "studies",
    "datasets",
    "bars",
    "backtests",
    "pnl_ledger",
    "taxonomy",
    "ui_route_map",
    "get_endpoint",
)

FIXTURE_BAR_DIR = Path(__file__).parent / "fixtures" / "bars"

# Every registered tool's endpoint has now shipped (``datasets`` at J-02, ``backtests`` at J-03,
# ``pnl_ledger`` at J-04 — each moved to the live byte-identity coverage below with zero MCP code
# changes), and ``/research/profiles`` (row 33, reached via ``get_endpoint``) shipped its minimal
# serving side at J-05 — so the honest-404 premise set is retired; the honest-404 WIRE FORM stays
# covered on a PERMANENTLY-unknown ``/research/*`` path, which no journey will ever ship.
UNKNOWN_RESEARCH_PATH = "/research/nonexistent-path-canary"

# Live 2xx no-argument tools and their canonical endpoints.
LIVE_STATIC = {
    "journal": "/research/journal",
    "analytics": "/research/analytics",
    "studies": "/research/studies",
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
        assert set(tool.inputSchema.get("properties", {})) <= {"ticker", "bar", "path"}
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


@pytest.mark.anyio
async def test_datasets_tool_byte_identical_on_a_non_empty_live_list(mcp_env):
    """J-02 flips ``datasets`` from honest 404 to live data with ZERO MCP code changes: after
    recording a dataset (the committed reference window, keyless), the tool's JSON is
    byte-identical to its curl equivalent on a NON-EMPTY 200 list."""
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
