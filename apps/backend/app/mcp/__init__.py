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
    via ``get_endpoint`` — at J-05; ``bars`` at era-4 J-01; ``levels`` at era-4 J-02; ``strategies``
    at era-4 J-04; ``tradability`` at era-5B J-01; ``setups`` at era-5B J-02; ``edge_report`` at
    era-5B J-04; ``desk_universe``/``desk_screen`` at era-desk J-06); an allowlisted-but-UNKNOWN
    path (any unshipped ``/research/*``) still surfaces the backend's honest 404 this way — never
    placeholder data.
  * backend unreachable — an explicit tool error naming the base URL and the failure
    (``BackendUnreachableError``); NEVER cached or fabricated data (no cache, no retry loop,
    no offline snapshot exists anywhere in this module).
  * ``get_endpoint`` — refuses any path outside GET ``/tape/*`` / ``/research/*`` / ``/meta/*``
    explicitly and WITHOUT sending a request (``PathRefusedError``).

Read-only discipline: the advertised tool set is exactly capability 6's read tools (plus each
era-4 structural addition) and the only HTTP verb this module ever issues is GET.
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
    "datasets": "/research/datasets",
    "bars": "/research/bars",
    "backtests": "/research/backtests",
    "strategies": "/research/strategies",
    "pnl_ledger": "/research/pnl/ledger",
    "taxonomy": "/research/taxonomy",
    "ui_route_map": "/meta/ui-routes",
    # `setups` (era-5B J-02) takes no REQUIRED params for the base list (unlike `levels`/
    # `tradability` directly below, both of which need `symbol`+`as_of`) -- the scan already walks
    # every config-owned panel symbol and session on its own, so this is a plain no-arg static path
    # (the `datasets`/`bars` shape), never a third two-param branch. The REST route's OPTIONAL
    # `symbol`/`reaction`/`band_class` filters are NOT exposed here -- this tool always proxies the
    # UNFILTERED list, byte-identical to `GET /research/setups` with no query string.
    "setups": "/research/setups",
    # `edge_report` (era-5B J-04) is the IDENTICAL no-required-param shape: the 3-way
    # strategy-comparison report takes no query params at all -- it aggregates over the WHOLE
    # registered dataset registry on its own.
    "edge_report": "/research/edge-report",
    # `desk_universe`/`desk_screen` (Era B "The Desk" J-06) are the IDENTICAL no-required-param
    # shape as `datasets`/`setups`/`edge_report` above: each proxies an endpoint that already
    # serves an explicit HTTP 200 honest-empty payload before anything is ever registered/computed
    # (never a 404 -- the `datasets`/`bars` no-data convention `desk_universe.py`/`desk_screen.py`
    # themselves follow). Neither tool exposes the `?date=` query variant of
    # `GET /research/desk/screen` -- that stays reachable only through `get_endpoint`.
    "desk_universe": "/research/desk/universe",
    "desk_screen": "/research/desk/screen",
}

_TAPE_PATHS: dict[str, str] = {
    "tape_state": "/tape/{ticker}/state",
    "tape_features": "/tape/{ticker}/features",
    "tape_history": "/tape/{ticker}/history",
}

# The one parametrized tool that is neither a no-arg static path nor a single-ticker path
# substitution: `levels` (era-4 J-02) needs TWO REQUIRED query params (`symbol`, `as_of`), so it
# gets its own name + a dedicated branch in `_request_path` rather than reusing `_STATIC_PATHS` or
# `_TAPE_PATHS`.
_LEVELS_TOOL = "levels"
_LEVELS_PATH = "/research/levels"

# `tradability` (era-5B J-01) is the IDENTICAL two-required-param shape as `levels` directly above
# (`symbol` + `as_of`) -- its own name + path constants, sharing the same dedicated branch in
# `_request_path` (see below) rather than a third near-duplicate branch.
_TRADABILITY_TOOL = "tradability"
_TRADABILITY_PATH = "/research/tradability"

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
        name="levels",
        description=(
            "Read-only proxy of GET /research/levels — deterministic, lookahead-free "
            "support/resistance levels (price, timeframe, type, touch_count, strength) PLUS their "
            "confluence zones (member levels, timeframe-weighted score, honest A/B/C conviction "
            "class) for one symbol as of one UTC instant, computed from the recorded bar store, "
            "JSON verbatim."
        ),
        inputSchema=_object_schema(
            {
                "symbol": {"type": "string", "description": "Symbol, e.g. PG."},
                "as_of": {
                    "type": "string",
                    "description": "UTC ISO-8601 instant, e.g. 2026-06-09T21:00:00Z.",
                },
            },
            ("symbol", "as_of"),
        ),
    ),
    types.Tool(
        name="tradability",
        description=(
            "Read-only proxy of GET /research/tradability — the tradable level map (a lens over "
            "the frozen levels/confluence-zone computation): at most a handful of quality-scored "
            "support/resistance price bands per symbol, computed under morning-markup as-of "
            "discipline (price range, side, quality score, member levels, round-number flag, "
            "inherited A/B/C class) for one symbol as of one UTC instant, JSON verbatim."
        ),
        inputSchema=_object_schema(
            {
                "symbol": {"type": "string", "description": "Symbol, e.g. AAPL."},
                "as_of": {
                    "type": "string",
                    "description": "UTC ISO-8601 instant, e.g. 2026-06-22T15:00:00Z.",
                },
            },
            ("symbol", "as_of"),
        ),
    ),
    types.Tool(
        name="setups",
        description=(
            "Read-only proxy of GET /research/setups -- the touch-event / case-study registry: "
            "every band-touch event the scanner finds across the config-owned 12-symbol panel's "
            "stored 5-minute bars (session, band, touch OHLC, a deterministic rejected/broke/"
            "chopped reaction label, forward returns at each configured horizon, and a "
            "tape_timeline field that is present but empty until real tape is recorded), JSON "
            "verbatim. Always the UNFILTERED list -- the REST route's optional symbol/reaction/"
            "band_class filters are not exposed here."
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
        name="strategies",
        description=(
            "Read-only proxy of GET /research/strategies — the registered strategy grammar "
            "registry (v1 plus the additive structure_tape) and the current champion strategy id, "
            "JSON verbatim."
        ),
        inputSchema=_object_schema({}),
    ),
    types.Tool(
        name="edge_report",
        description=(
            "Read-only proxy of GET /research/edge-report -- the 3-way strategy-comparison report "
            "(v1 vs the frozen structure_tape vs the additive structure_tape_map) aggregated into "
            "per strategy x class x side x reaction x feed cells over every registered "
            "event-window dataset that resolves an owning, classified touch event (n, gross/net R "
            "and $, win rate, max drawdown, a seeded null baseline, and an insufficient_sample "
            "label below the configured minimum n), plus a ranked list of train cells clearing the "
            "positivity gate with their own hold-out status -- JSON verbatim. Never pools across "
            "feeds, and never pools train with hold-out."
        ),
        inputSchema=_object_schema({}),
    ),
    types.Tool(
        name="desk_universe",
        description=(
            "Read-only proxy of GET /research/desk/universe -- Era B \"The Desk\" J-01's "
            "registered universe-snapshot list: every dated, checksummed S&P constituents "
            "snapshot ever registered, its normalized membership, and the most recently "
            "registered snapshot (`latest`, `null` before any registration -- an explicit "
            "honest-empty 200, never a 404), JSON verbatim."
        ),
        inputSchema=_object_schema({}),
    ),
    types.Tool(
        name="desk_screen",
        description=(
            "Read-only proxy of GET /research/desk/screen -- Era B \"The Desk\" J-03's "
            "append-only screen-snapshot ledger: a meta-only list of every recorded screen plus "
            "the most recently recorded screen's full ranked/skipped rows and provenance "
            "(`latest`, `null` before any screen is ever computed -- an explicit honest-empty "
            "200, never a 404), JSON verbatim. Takes no arguments here; `get_endpoint` reaches "
            "the `?date=` lookup variant for one specific past screen."
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
    if name in (_LEVELS_TOOL, _TRADABILITY_TOOL):
        symbol = arguments.get("symbol")
        as_of = arguments.get("as_of")
        if not isinstance(symbol, str) or not symbol:
            raise ToolArgumentError(f"tool {name!r} requires a non-empty string 'symbol' argument")
        if not isinstance(as_of, str) or not as_of:
            raise ToolArgumentError(f"tool {name!r} requires a non-empty string 'as_of' argument")
        path = _LEVELS_PATH if name == _LEVELS_TOOL else _TRADABILITY_PATH
        return f"{path}?symbol={quote(symbol, safe='')}&as_of={quote(as_of, safe='')}"
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
