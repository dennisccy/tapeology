# goal-tape_to_profit-iter-1 Dev Handoff

**Phase:** goal-tape_to_profit-iter-1
**Date:** 2026-07-03
**Agent:** developer
**Status:** complete

## What Was Built

- **`GET /meta/ui-routes`** (Data Contract row 35) — new `app/meta.py` router registered on the
  app beside the research router. Serves the canonical route map: Cockpit `/`, Journal
  `/journal`, Studies `/studies` (top-bar entries, `nav: true`) plus `/journal/[id]` as an
  honest `nav: false` child entry. Each entry carries `path` + `label`. No `/performance`
  anywhere (it does not exist until J-05).
- **Read-only stdio MCP server** — new `app/mcp/` package, runnable as
  `apps/backend/.venv/bin/python -m app.mcp` (also from the repo root with
  `PYTHONPATH=apps/backend`, the registered `.mcp.json` shape). Exactly the capability-6 tool
  set: `tape_state`, `tape_features`, `tape_history`, `journal`, `analytics`, `studies`,
  `datasets`, `backtests`, `pnl_ledger`, `taxonomy`, `ui_route_map`, `get_endpoint(path)`.
  Every tool is a thin `httpx` GET against `TAPEOLOGY_API_BASE` (default
  `http://localhost:8000`); the module imports NOTHING from the rest of the `app` package
  (locked by a source-scan test).
  - **Byte-identity by construction:** tools pass `response.text` through verbatim — no
    parse/re-serialize. Result contract: 2xx ⇒ `content[0]` = body verbatim; non-2xx ⇒
    `content[0]` = body verbatim + `content[1]` = `"HTTP <status> from GET <path>"` +
    `isError`; unreachable ⇒ explicit `BackendUnreachableError` ("no cached or fabricated
    data is served" — the module has no cache, retry, or offline path at all).
  - `datasets` / `backtests` / `pnl_ledger` stay registered and surface their honest 404s
    (endpoints land at J-02/J-03/J-04).
  - `get_endpoint` allowlist: GET `/tape/*`, `/research/*`, `/meta/*` only; refusal is decided
    BEFORE any request (proven by a dead-port test), rejects relative, protocol-relative,
    `..`-carrying, and prefix-lookalike paths.
- **New dependency `mcp==1.28.1`** (official Anthropic MCP SDK) — vetted via
  `./scripts/automation/check-install.sh` (decision: ALLOW after allowlisting), installed on
  the real venv interpreter (Python 3.14.4 — SDK carries explicit 3.14 markers), pinned in
  `requirements.txt`. Pure-Python; no post-install step, no native binary. Existing core deps
  (fastapi/starlette/pydantic/httpx) were NOT upgraded (verified: install added only new
  packages).
- **Dev-chain registration** — real `tapeology` server entry in
  `project-extensions/mcp-servers.yaml` (the shape from its comments), synced via
  `sync-cli-assets.sh`; `.mcp.json` generated at the repo root, confirmed gitignored
  (`.gitignore:75`) and untracked; `mcp_sync_selftest.py self-test` passes.
- **NavBar renders from the route map** — `NAV_ITEMS` hardcoded list deleted (no fallback list
  anywhere; grep-verified). Fetches `${API_BASE}/meta/ui-routes` with an abort backstop
  (`UI_ROUTES_REQUEST_TIMEOUT_MS` in `lib/config.ts`); unreachable ⇒ explicit degraded state
  (`data-testid="nav-unavailable"`, "navigation unavailable — backend unreachable", amber) —
  never a fabricated link list. Preserved semantics: `data-testid="app-nav"` / `"nav-link"`,
  `data-label`, `aria-current`, identical active/inactive classes, `/journal/[id]` keeps
  Journal active. The `nav-link-disabled` branch was removed as dead code: the route map lists
  only live routes, so a disabled entry can no longer exist (no archived flow in the preserve
  list uses it).

## Files Changed

- `apps/backend/app/meta.py` — NEW: `/meta` router, canonical `UI_ROUTES` (row-35 owner)
- `apps/backend/app/main.py` — register `meta_router` (import + `include_router`, 2 lines)
- `apps/backend/app/mcp/__init__.py` — NEW: the read-only stdio MCP server (tools, allowlist, proxy, result contract)
- `apps/backend/app/mcp/__main__.py` — NEW: `python -m app.mcp` entrypoint
- `apps/backend/requirements.txt` — add pinned `mcp==1.28.1` with supply-chain comment
- `apps/backend/tests/test_meta_routes.py` — NEW: 5 route-map content tests (exact payload, no `/performance`, honest `/journal/[id]`)
- `apps/backend/tests/test_mcp_server.py` — NEW: 15 tests — per-tool byte-identity vs a REAL uvicorn instance (SIM-BUYER paused so snapshots freeze), honest-404 tools, 422/404 proxying, allowlist accept/refuse (refusal proven request-free), backend-down explicit errors for all 12 tools, read-only tool-list + source-scan discipline, full stdio-subprocess session end-to-end
- `apps/frontend/components/NavBar.tsx` — render from `GET /meta/ui-routes`; hardcoded list deleted; explicit degraded state
- `apps/frontend/lib/config.ts` — add `UI_ROUTES_REQUEST_TIMEOUT_MS` (single source, no inline literal)
- `project-extensions/mcp-servers.yaml` — real `tapeology` stdio server entry
- `incredible_auto_dev/config/install-security-policy.json` — add `mcp` to the python allowlist (repo-root `config/` symlinks here; same procedure as the existing `alpaca-py` entry)

## Tests Run

All results below were re-executed in the RESUMED verification dispatch (03-07-2026,
foreground runs, exit codes read) — none is carried over from the interrupted dispatch:

Command: `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **868 passed, 1 skipped** (exit 0, 351.79s; baseline anchor 848 + 20 new tests; no
archived-era test deleted or weakened)

Engine equivalence: `tests/test_observer_equivalence.py` — **7 passed** (7/7, exit 0)

Frontend build: `cd apps/frontend && npm run build` — **passes** (exit 0; type-check +
compile; `/`, `/journal`, `/journal/[id]`, `/studies` + `_not-found` emitted, no
`/performance`)

MCP sync: `./scripts/automation/sync-cli-assets.sh` (already in sync — wrote 0) then
`python3 scripts/automation/lib/mcp_sync_selftest.py self-test` — **OK** (exit 0);
`.mcp.json` regenerated at repo root, re-confirmed gitignored (`.gitignore:75`) and untracked

## Live Verification (not mocked)

Re-executed in the resumed dispatch (03-07-2026) unless noted:

- **J-01 steps 1–3 live:** backend on `:8000`, real stdio client spawned with the EXACT
  registered `.mcp.json` shape (repo-root cwd, `PYTHONPATH=apps/backend`): 12 tools listed in
  capability-6 order; `tape_state` (watched, settled `buyer_control`, paused SIM-BUYER; 164
  bytes) and `ui_route_map` (214 bytes) both **byte-identical** to their curl-equivalent GETs.
- **J-01 step 5 live:** backend stopped ⇒ `tape_state` over the SAME stdio session returns
  `isError: true` with "tapeology backend unreachable at http://localhost:8000 … no cached or
  fabricated data is served".
- **Service startup:** `scripts/dev.sh` started both services (:8301/:3301 offset ports);
  `GET /meta/ui-routes` served the canonical 4-entry map on the dev port; restarted cleanly
  over itself (its port-kill handles children), both healthy after restart. All processes
  killed after verification; ports confirmed free.
- **Browser sanity (real Chrome — from the interrupted dispatch; not re-run, formal pass
  belongs to browser-qa-agent per the spec's Testing Requirements):** with services up, the
  top bar renders exactly Cockpit · Journal · Studies from the route map (3 `nav-link`s,
  correct `data-label`s); `/journal` marks Journal active (`aria-current="page"` + emerald
  class); with the backend killed, the nav shows the explicit `nav-unavailable` degraded state
  with **zero** fabricated links.

## Resumed-Dispatch Verification Notes (03-07-2026)

This dispatch verified the interrupted dispatch's work against the iter spec — no functional
gap found, zero code changes needed (working tree untouched except these handoffs). Statics
re-confirmed for the reviewer's coherence watchpoints:

- **No second route list:** `NAV_ITEMS` absent from `apps/` (grep); the only route list is
  `app/meta.py::UI_ROUTES`; MCP `ui_route_map` is a pure HTTP proxy of it.
- **`nav-link-disabled`:** referenced nowhere in the repo outside the iter spec's watchpoint
  text and these handoffs; the golden replay script
  (`runs/goal-session-tape_to_profit/journey-scripts/J-08.json`) navigates by URL + page text
  only — no nav selectors, no render-timing dependence.
- **Install policy diff:** exactly one entry — `"mcp"` appended to the python allowlist in
  `incredible_auto_dev/config/install-security-policy.json`.
- **Venv:** Python 3.14.4 (project-template says 3.12 — pre-existing documentation drift,
  noted at iter-0); `mcp 1.28.1` installed; `pip check` clean; core deps present as
  fastapi 0.139.0 / starlette 1.3.1 / pydantic 2.13.4 / httpx 0.28.1 / uvicorn 0.49.0 (the
  868-test archived suite passing on them is the behavioral no-upgrade-breakage evidence).
- **`requirements.txt` diff:** adds only the pinned `mcp==1.28.1` line (+ comment).

## Known Issues

- None functional. Two honest notes:
  - The MCP non-2xx contract puts the verbatim backend payload in `content[0]` and the
    explicit `"HTTP <status> from GET <path>"` note in `content[1]` (documented in the module
    docstring and locked by tests) — byte-identity holds for every tool including the
    honest-404 tools, per the spec.
  - `python -m app.mcp` requires the `app` package on `sys.path` (run from `apps/backend/` or
    with `PYTHONPATH=apps/backend`, exactly as the registered `.mcp.json` entry does). No
    post-install step needed for the SDK itself.

## Suggested Next Phase

J-02 (head of the J-02→J-03→J-04→J-05 chain): the persisted dataset store with frozen
train/hold-out split tags, `POST/GET /research/datasets*`, checksum verification, the
committed miniature fixture pair, and byte-identical replay — at which point the MCP
`datasets` tool's honest 404 flips to live data with zero MCP changes.
