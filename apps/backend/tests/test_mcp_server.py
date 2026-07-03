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

# Capability 6, verbatim — order and content are the advertised contract.
EXPECTED_TOOLS = (
    "tape_state",
    "tape_features",
    "tape_history",
    "journal",
    "analytics",
    "studies",
    "datasets",
    "backtests",
    "pnl_ledger",
    "taxonomy",
    "ui_route_map",
    "get_endpoint",
)

# The honest-404 set: registered NOW, endpoints land at J-02/J-03/J-04.
NOT_YET_SHIPPED = {
    "datasets": "/research/datasets",
    "backtests": "/research/backtests",
    "pnl_ledger": "/research/pnl/ledger",
}

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
def backend(tmp_path_factory):
    """A REAL uvicorn instance of the app on an ephemeral port with a temp journal DB."""
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["TAPEOLOGY_JOURNAL_DB"] = str(tmp_path_factory.mktemp("mcp-journal") / "journal.db")
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


@pytest.mark.anyio
async def test_honest_404_tools_stay_registered_and_surface_the_real_status(mcp_env):
    """``datasets`` / ``backtests`` / ``pnl_ledger`` have no endpoints until J-02+: they must
    surface the backend's ACTUAL 404 byte-for-byte — never a placeholder payload."""
    for name, path in NOT_YET_SHIPPED.items():
        result = await call_tool(name, {})
        rest = httpx.get(f"{mcp_env}{path}", timeout=5.0)
        assert rest.status_code == 404, f"{path} unexpectedly exists — update this test's premise"
        assert result.isError is True
        assert result.content[0].text.encode("utf-8") == rest.content, f"{name} 404 not verbatim"
        assert result.content[1].text == f"HTTP 404 from GET {path}"


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
async def test_get_endpoint_proxies_allowlisted_but_missing_path_404_verbatim(mcp_env):
    """``/research/profiles`` is allowlisted but unshipped (J-06): the backend's real 404 is
    proxied verbatim — not refused, not synthesized."""
    result = await call_tool("get_endpoint", {"path": "/research/profiles"})
    rest = httpx.get(f"{mcp_env}/research/profiles", timeout=5.0)
    assert rest.status_code == 404
    assert result.isError is True
    assert result.content[0].text.encode("utf-8") == rest.content
    assert result.content[1].text == "HTTP 404 from GET /research/profiles"


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
            result = await session.call_tool("datasets", {})
            rest = httpx.get(f"{watched_backend}/research/datasets", timeout=5.0)
            assert result.isError is True
            assert result.content[0].text.encode("utf-8") == rest.content
            assert result.content[1].text == "HTTP 404 from GET /research/datasets"

            # Refusal over the wire: the SDK surfaces the raised refusal as an isError result.
            result = await session.call_tool("get_endpoint", {"path": "/health"})
            assert result.isError is True
            assert "refused" in result.content[0].text
            assert "no request was sent" in result.content[0].text
