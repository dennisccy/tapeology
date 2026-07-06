"""Read-only stdio MCP server (J-01, capability 6) — the product's machine surface.

``python -m app.mcp`` speaks the Model Context Protocol over stdio. Every tool is a THIN
``httpx`` GET proxy against the running backend at ``TAPEOLOGY_API_BASE`` (default
``http://localhost:8000``) — never a second app instance, never an engine/serializer import,
never a second computation or serialization path (single-source-of-truth anti-goal). This
module deliberately imports NOTHING from the rest of the ``app`` package.

Byte-identity by construction: a tool passes the backend response body through VERBATIM as raw
text (``response.text`` — no parse/re-serialize round-trip), so a tool's JSON is byte-identical
to its curl equivalent.

Result contract (locked by ``tests/test_mcp_server.py``):
  * 2xx — ``content[0].text`` == the response body byte-for-byte; ``isError`` false.
  * non-2xx — the backend's ACTUAL status and payload surfaced explicitly: ``content[0].text``
    == the response body byte-for-byte, ``content[1].text`` == ``"HTTP <status> from GET
    <path>"``, ``isError`` true. Every registered tool's endpoint has shipped (``datasets`` at
    (era-3) J-02, ``backtests`` at J-03, ``pnl_ledger`` at J-04; ``/research/profiles`` — reached
    via ``get_endpoint`` — at J-05; ``bars`` at era-4 J-01); an allowlisted-but-UNKNOWN path (any
    unshipped ``/research/*``) still surfaces the backend's honest 404 this way — never
    placeholder data.
  * backend unreachable — an explicit tool error naming the base URL and the failure
    (``BackendUnreachableError``); NEVER cached or fabricated data (no cache, no retry loop,
    no offline snapshot exists anywhere in this module).
  * ``get_endpoint`` — refuses any path outside GET ``/tape/*`` / ``/research/*`` / ``/meta/*``
    explicitly and WITHOUT sending a request (``PathRefusedError``).

Read-only discipline: the advertised tool set is exactly capability 6's twelve read tools and
the only HTTP verb this module ever issues is GET.
"""

from __future__ import annotations

import os
from urllib.parse import quote

import anyio
import httpx
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

# The one configuration seam (capability 6): the running backend's base URL. Read at CALL time,
# not import time, so a client can point an already-spawned server at a different backend only
# by respawning it with a new environment — there is no mutable in-process state.
API_BASE_ENV = "TAPEOLOGY_API_BASE"
DEFAULT_API_BASE = "http://localhost:8000"

# Per-request HTTP timeout (module constant — the ``WS_PUSH_INTERVAL`` precedent in app.main).
# Sits well under the 30s client-side tool timeout registered in
# project-extensions/mcp-servers.yaml; on expiry the tool errors explicitly (never hangs).
HTTP_TIMEOUT_SECONDS = 10.0

# ``get_endpoint`` allowlist: the canonical read surface, nothing else. ``/health``, the
# mutating ``/watch/*`` namespace, and arbitrary paths are refused before any request is made.
ALLOWED_GET_PREFIXES = ("/tape/", "/research/", "/meta/")


class BackendUnreachableError(Exception):
    """The backend did not answer at all — surfaced explicitly, never papered over."""


class PathRefusedError(Exception):
    """A ``get_endpoint`` path outside the read-only allowlist — refused, no request sent."""


class ToolArgumentError(Exception):
    """A required tool argument is missing or malformed."""


class UnknownToolError(Exception):
    """A tool name outside the advertised read-only set."""


def api_base() -> str:
    """The backend base URL: ``TAPEOLOGY_API_BASE`` if set, else the canonical default."""
    return os.environ.get(API_BASE_ENV, DEFAULT_API_BASE)


# --- Tool registry ------------------------------------------------------------------------------
# Exactly the capability-6 set. Static tools map 1:1 onto a fixed canonical GET path; tape tools
# substitute the (URL-quoted) ticker; ``get_endpoint`` proxies any allowlisted GET path verbatim.

_STATIC_PATHS: dict[str, str] = {
    "journal": "/research/journal",
    "analytics": "/research/analytics",
    "studies": "/research/studies",
    "datasets": "/research/datasets",
    "bars": "/research/bars",
    "backtests": "/research/backtests",
    "pnl_ledger": "/research/pnl/ledger",
    "taxonomy": "/research/taxonomy",
    "ui_route_map": "/meta/ui-routes",
}

_TAPE_PATHS: dict[str, str] = {
    "tape_state": "/tape/{ticker}/state",
    "tape_features": "/tape/{ticker}/features",
    "tape_history": "/tape/{ticker}/history",
}

_TICKER_PROPERTY = {
    "type": "string",
    "description": "Ticker symbol as watched on the backend, e.g. SIM-BUYER.",
}


def _object_schema(properties: dict, required: tuple[str, ...] = ()) -> dict:
    schema: dict = {"type": "object", "properties": properties, "additionalProperties": False}
    if required:
        schema["required"] = list(required)
    return schema


TOOLS: tuple[types.Tool, ...] = (
    types.Tool(
        name="tape_state",
        description=(
            "Read-only proxy of GET /tape/{ticker}/state — the current tape-state snapshot "
            "JSON, verbatim."
        ),
        inputSchema=_object_schema({"ticker": _TICKER_PROPERTY}, ("ticker",)),
    ),
    types.Tool(
        name="tape_features",
        description=(
            "Read-only proxy of GET /tape/{ticker}/features — the engine feature values JSON, "
            "verbatim."
        ),
        inputSchema=_object_schema({"ticker": _TICKER_PROPERTY}, ("ticker",)),
    ),
    types.Tool(
        name="tape_history",
        description=(
            "Read-only proxy of GET /tape/{ticker}/history (optionally ?bar=N) — OHLC bars plus "
            "tape-state markers JSON, verbatim."
        ),
        inputSchema=_object_schema(
            {
                "ticker": _TICKER_PROPERTY,
                "bar": {
                    "type": "integer",
                    "description": "Optional bar size in seconds (backend-validated).",
                },
            },
            ("ticker",),
        ),
    ),
    types.Tool(
        name="journal",
        description="Read-only proxy of GET /research/journal — the research journal rows JSON, verbatim.",
        inputSchema=_object_schema({}),
    ),
    types.Tool(
        name="analytics",
        description="Read-only proxy of GET /research/analytics — the journal analytics JSON, verbatim.",
        inputSchema=_object_schema({}),
    ),
    types.Tool(
        name="studies",
        description="Read-only proxy of GET /research/studies — the replay-study list JSON, verbatim.",
        inputSchema=_object_schema({}),
    ),
    types.Tool(
        name="datasets",
        description=(
            "Read-only proxy of GET /research/datasets — recorded historical tape dataset "
            "metadata (checksum-verified on every load, with explicit integrity errors) JSON, "
            "verbatim."
        ),
        inputSchema=_object_schema({}),
    ),
    types.Tool(
        name="bars",
        description=(
            "Read-only proxy of GET /research/bars — recorded multi-timeframe OHLC bar-series "
            "metadata and candles (checksum-verified on every load, with explicit integrity "
            "errors) JSON, verbatim."
        ),
        inputSchema=_object_schema({}),
    ),
    types.Tool(
        name="backtests",
        description=(
            "Read-only proxy of GET /research/backtests — deterministic backtest PnL reports "
            "(simulated fills against recorded tape; net/gross R and $ beside a seeded null "
            "baseline) JSON, verbatim."
        ),
        inputSchema=_object_schema({}),
    ),
    types.Tool(
        name="pnl_ledger",
        description=(
            "Read-only proxy of GET /research/pnl/ledger — the append-only PnL-ledger rows "
            "(per-enhancement simulated net R and $ on train and hold-out separately, with n, "
            "provenance, and the simulated register) JSON, verbatim."
        ),
        inputSchema=_object_schema({}),
    ),
    types.Tool(
        name="taxonomy",
        description="Read-only proxy of GET /research/taxonomy — the research label taxonomy JSON, verbatim.",
        inputSchema=_object_schema({}),
    ),
    types.Tool(
        name="ui_route_map",
        description=(
            "Read-only proxy of GET /meta/ui-routes — the canonical UI route map JSON, verbatim "
            "(the same single source the rendered navigation reads)."
        ),
        inputSchema=_object_schema({}),
    ),
    types.Tool(
        name="get_endpoint",
        description=(
            "Generic read-only proxy: GET one allowlisted backend path (/tape/*, /research/*, "
            "/meta/* only; query strings allowed). Any other path is refused explicitly without "
            "a request. The response body is returned verbatim."
        ),
        inputSchema=_object_schema(
            {
                "path": {
                    "type": "string",
                    "description": "Absolute backend path starting with /tape/, /research/, or /meta/.",
                }
            },
            ("path",),
        ),
    ),
)

TOOL_NAMES: tuple[str, ...] = tuple(tool.name for tool in TOOLS)


def allowlist_refusal(path: object) -> str | None:
    """The explicit refusal message for a non-allowlisted ``get_endpoint`` path, or ``None``
    when the path is allowed. Pure decision — never touches the network."""
    allowed = ", ".join(f"{prefix}*" for prefix in ALLOWED_GET_PREFIXES)
    if not isinstance(path, str):
        return (
            f"refused: path must be a string, got {type(path).__name__} — no request was sent"
        )
    if not path.startswith("/") or path.startswith("//"):
        return (
            f"refused: {path!r} is not an absolute backend path (must start with a single '/', "
            f"carrying no scheme or host) — no request was sent"
        )
    if ".." in path:
        return f"refused: {path!r} contains a '..' segment — no request was sent"
    route = path.split("?", 1)[0]
    if not route.startswith(ALLOWED_GET_PREFIXES):
        return (
            f"refused: GET {path!r} is outside the read-only allowlist ({allowed}) — "
            f"no request was sent"
        )
    return None


def _request_path(name: str, arguments: dict) -> str:
    """The canonical GET path for one tool call. Raises explicitly for unknown tools, missing
    arguments, and non-allowlisted ``get_endpoint`` paths — always BEFORE any request."""
    if name in _STATIC_PATHS:
        return _STATIC_PATHS[name]
    if name in _TAPE_PATHS:
        ticker = arguments.get("ticker")
        if not isinstance(ticker, str) or not ticker:
            raise ToolArgumentError(f"tool {name!r} requires a non-empty string 'ticker' argument")
        path = _TAPE_PATHS[name].format(ticker=quote(ticker, safe=""))
        if name == "tape_history" and arguments.get("bar") is not None:
            path += f"?bar={arguments['bar']}"
        return path
    if name == "get_endpoint":
        path = arguments.get("path")
        refusal = allowlist_refusal(path)
        if refusal is not None:
            raise PathRefusedError(refusal)
        assert isinstance(path, str)  # allowlist_refusal guarantees it
        return path
    raise UnknownToolError(
        f"unknown tool {name!r} — this read-only server exposes exactly: {', '.join(TOOL_NAMES)}"
    )


async def _proxy_get(path: str) -> httpx.Response:
    """One thin GET against the running backend. Unreachable ⇒ explicit error, nothing served."""
    base = api_base()
    try:
        async with httpx.AsyncClient(base_url=base, timeout=HTTP_TIMEOUT_SECONDS) as client:
            return await client.get(path)
    except httpx.HTTPError as exc:
        raise BackendUnreachableError(
            f"tapeology backend unreachable at {base} (GET {path}): "
            f"{type(exc).__name__}: {exc} — no cached or fabricated data is served"
        ) from exc


server = Server(
    "tapeology",
    instructions=(
        "Read-only proxies of the Tapeology REST API. Every tool's JSON is byte-identical to "
        "its curl equivalent against the running backend; nothing here can change any state."
    ),
)


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Advertise exactly the capability-6 read-only tool set."""
    return list(TOOLS)


@server.call_tool()
async def call_tool(name: str, arguments: dict | None) -> types.CallToolResult:
    """Dispatch one tool call per the module result contract (see module docstring)."""
    path = _request_path(name, arguments or {})
    response = await _proxy_get(path)
    body = types.TextContent(type="text", text=response.text)
    if response.is_success:
        return types.CallToolResult(content=[body], isError=False)
    # Non-2xx: the backend's actual payload verbatim (content[0]) + its actual status,
    # explicitly (content[1]). Honest-404 tools land here until their endpoints ship.
    status_note = types.TextContent(type="text", text=f"HTTP {response.status_code} from GET {path}")
    return types.CallToolResult(content=[body, status_note], isError=True)


async def _serve() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    """Run the read-only stdio MCP server (``python -m app.mcp``)."""
    anyio.run(_serve)
