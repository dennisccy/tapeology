# Goal Iteration 1 — Read-only MCP server + canonical UI route map (J-01)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit
- **Iteration:** 1
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01
- **Required-still-passing journeys:** J-08
- **Anti-goal reminders:**
  - **No live execution path.** Tapeology MUST NOT place, route, or transmit orders anywhere — no brokerage integration, no trading API, **no paper-trading API**, no order tickets, no recommendation to execute. The ONLY permitted "fill" is the offline backtester's simulated fill computed against recorded historical tape, clearly labeled simulated and sent nowhere. *(critical)*
  - **No profit claims and no advice.** Simulated PnL is a caveated measurement: it MUST always appear with its R counterpart, its n, its fee/slippage assumptions, its train-or-hold-out basis, and its null baseline — and MUST never be presented as expected live results, an edge claim, or a reason to trade. No imperative cues, no prediction language. *(critical)*
  - **Default engine outputs are frozen.** Indicator evolution is additive and versioned only: candidate profiles may add feature keys or alternate thresholds, but the `default` profile's outputs stay byte-identical (equivalence-tested), the live cockpit uses `default` only, and no enhancement may mutate an archived-era behavior to pass. *(critical)*
  - **No train-only promotion.** Nothing becomes the champion, a proposed journey, or a claimed improvement on the strength of train data alone: hold-out survival (net R AND net $, with the configured minimum n) is the only promotion gate; overfit results are labeled overfit. *(critical)*
  - **No ML, no online tuning.** Candidate search is bounded, config-enumerated, offline, and deterministic; no fitted models, no optimizer loops inside the engine, no thresholds that move at runtime.
  - **No fabricated data — honest failure states.** No synthesized trades, quotes, fills, datasets, or PnL to force a green journey; every failure mode (backend down, corrupt dataset, empty window, missing credentials, insufficient n) surfaces an explicit, distinct state. *(critical)*
  - **Single source of truth.** Every canonical value in the Data Contract is computed once and read verbatim by every surface — REST, WebSocket, UI, markdown reports, and MCP. A second computation path or a diverging number across surfaces is a defect. *(critical)*
  - **MCP is read-only.** The MCP server exposes no mutating tools, proxies only the canonical GET surface (plus the allowlisted `get_endpoint`), and MUST NOT become a second implementation of any computation. *(critical)*
  - **Persistence stays scoped.** SQLite holds research records (now including backtests and the PnL ledger); the dataset store holds explicitly recorded historical tape for research replay. The live cockpit's tape remains unpersisted; no ambient recording. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the AUTO:journeys marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a PnL-ledger acceptance criterion, keep the default profile byte-identical, and include a [NEW]-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Make the product machine-readable: a read-only stdio MCP server (`python -m app.mcp`) that thinly proxies the canonical REST API, plus the canonical `GET /meta/ui-routes` route map that the rendered top-bar navigation now consumes instead of its hardcoded list.

## BACKGROUND

Iter-0 baseline confirmed J-01–J-07 failing (not built) and J-08 passing (848/849 backend suite, equivalence 7/7, 3-entry hardcoded nav). The evaluator recommended J-01 first: it is independent of the J-02→J-05 chain, it unlocks MCP-assisted verification for every later iteration, and it retires the hardcoded `NAV_ITEMS` list in `apps/frontend/components/NavBar.tsx` behind the canonical route map *before* J-05 adds a Performance entry — pre-empting a duplicate nav source-of-truth coherence failure.

**RESUME STATE — read before implementing.** A prior dispatch of this same iteration was interrupted after the developer step. The J-01 implementation ALREADY EXISTS, uncommitted, in the working tree on branch `goal/tape_to_profit` (verified at planning time): `apps/backend/app/meta.py` (route map: Cockpit `/`, Journal `/journal`, `/journal/[id]` as `nav: false`, Studies `/studies` — no `/performance`), `apps/backend/app/mcp/` (stdio server + `__main__.py`), `apps/backend/tests/test_meta_routes.py` + `tests/test_mcp_server.py`, `mcp==1.28.1` pinned in `requirements.txt` (install-gate allowlisted), the real `tapeology` entry in `project-extensions/mcp-servers.yaml`, generated `.mcp.json` at repo root (confirmed gitignored), and `NavBar.tsx` fetching `${API_BASE}/meta/ui-routes` with an explicit `nav-unavailable` degraded state. Dev handoffs exist at `docs/handoffs/goal-tape_to_profit-iter-1-dev.md` / `-frontend.md` claiming 868 passed / 1 skipped and equivalence 7/7. **What never ran: review, browser QA, coherence audit, evaluation.** The developer's job this dispatch is to VERIFY the existing work against this spec — re-run the full suites, the MCP sync self-test, and the frontend build; fix any gap found; keep the handoffs accurate — NOT to rebuild from scratch and NOT to redo finished work. The reviewer reviews the existing uncommitted diff as-is. Lessons ledger is empty (first feature iteration of this session).

## IN SCOPE

### Backend
- [ ] `GET /meta/ui-routes` — the route-map owner module (Data Contract row 35), registered on the app like the existing research router. It lists exactly the live user-facing routes: Cockpit `/`, Journal `/journal`, Studies `/studies` as top-bar entries, and represents the journal detail route `/journal/[id]` honestly (`nav: false` child entry). It MUST NOT list `/performance` until that page exists (J-05) — the nav never carries a dead link. Each entry carries at least `path` and `label` so the nav can render from it verbatim. *(exists in working tree — verify)*
- [ ] `app/mcp` module runnable as `apps/backend/.venv/bin/python -m app.mcp` (stdio MCP server). Tools are thin `httpx` GET clients against the running backend at `TAPEOLOGY_API_BASE` (default `http://localhost:8000`) — never a second app instance, never direct engine imports. Tool set exactly per capability 6: `tape_state`, `tape_features`, `tape_history`, `journal`, `analytics`, `studies`, `datasets`, `backtests`, `pnl_ledger`, `taxonomy`, `ui_route_map`, plus `get_endpoint(path)` allowlisted to GET `/tape/*`, `/research/*`, `/meta/*`. *(exists — verify)*
- [ ] Byte-identity by construction: each tool returns the backend response body verbatim (no parse/re-serialize round-trip), so tool JSON is byte-identical to its curl equivalent. *(exists — verify)*
- [ ] Honest failures: backend unreachable → explicit tool error (never cached or fabricated data); backend non-2xx → the tool surfaces the backend's actual status and payload explicitly. Tools whose endpoints do not exist yet (`datasets`, `backtests`, `pnl_ledger`, and `/research/profiles` via `get_endpoint` — all 404 until J-02+) stay registered and surface that honest 404; do not omit them, do not synthesize placeholder data. *(exists — verify)*
- [ ] New dependency: the official `mcp` Python SDK (`mcp==1.28.1`), vetted via `./scripts/automation/check-install.sh`, pinned in `apps/backend/requirements.txt`, installed on the real venv interpreter. (`httpx` already present — no other new deps.) *(exists — verify no core deps were upgraded)*
- [ ] Registration: real server entry in `project-extensions/mcp-servers.yaml`, `./scripts/automation/sync-cli-assets.sh` run, then `python3 scripts/automation/lib/mcp_sync_selftest.py self-test` — must pass. `.mcp.json` generated at the repo root and stays gitignored/untracked. *(exists — re-run the self-test this dispatch)*
- [ ] Automated tests (this iteration, not deferred): per-tool byte-identity vs the REST endpoint; read-only assertions (tool list contains no write verbs; server code performs only GETs); `get_endpoint` refuses non-allowlisted paths (e.g. `/health`, `/watch/SIM-BUYER`) with an explicit refusal and proxies an unknown-but-allowlisted path's 404 verbatim; backend-down explicit tool error for every tool; `/meta/ui-routes` content test (exactly the live routes; no `/performance`). *(exist — re-run and confirm green)*

### Frontend
- [ ] `NavBar.tsx` renders its links from `GET /meta/ui-routes` (via the existing `NEXT_PUBLIC_API_URL` base convention). The hardcoded `NAV_ITEMS` list is deleted — no hardcoded route list may remain, including as a "fallback" (a fallback list IS the hand-maintained duplicate this journey exists to retire). *(exists — verify)*
- [ ] If the route map is unreachable, the nav shows an explicit degraded state (brand plus an honest placeholder, `data-testid="nav-unavailable"`) — never a fabricated link list. Once loaded, links render exactly the endpoint's entries. *(exists — verify)*
- [ ] Preserve the existing nav test ids and semantics (`data-testid="app-nav"`, `data-testid="nav-link"`, `data-label`, active-link styling, `/journal/[id]` keeping Journal active) so archived-era browser flows and golden replay scripts are untouched. *(exists — browser-verify)*

### New user-facing capability
The top bar is now driven by the product's own canonical route map — when a future page ships (e.g. Performance at J-05), the nav updates from one source with no frontend list edit. Agents (and the dev-chain itself) can read the entire product over MCP tools that mirror the REST API exactly.

### New information displayed
None visually new — the nav shows the same three links (Cockpit · Journal · Studies), now sourced from `GET /meta/ui-routes`. The route map itself is new machine-readable information (REST + MCP `ui_route_map`).

### New user actions
None in the browser. New machine actions: 12 read-only MCP tools callable from a stdio client session.

### UI surface changes
`NavBar.tsx` rendering source changes (hardcoded list → route-map fetch); pixel-identical link set and styling. No new pages, panels, or cards.

### Product surface delta
The product gains its machine surface: `python -m app.mcp` registered in `project-extensions/mcp-servers.yaml` / generated `.mcp.json`, and `GET /meta/ui-routes` as the single nav source of truth. Browser experience is unchanged (that is the point — J-08 must not notice).

### Blueprint conformance
No new UI surfaces. Nav skeleton unchanged (Cockpit · Journal · Studies). This iteration implements exactly what the blueprint's Information Architecture already prescribes: "the rendered nav reads `GET /meta/ui-routes` (row 35) once J-01 lands — the hardcoded list in `apps/frontend/components/NavBar.tsx` is replaced by that single source, never duplicated." The MCP server and `mcp-servers.yaml` registration live under the blueprint's registered "Machine surface". No blueprint edit, no reapproval request.

### Data-contract additions
None new — Data Contract row 35 (UI route map, owner: route-map module behind `GET /meta/ui-routes`) was registered at baseline; this iteration implements it. The MCP server owns NO values (thin proxy only, per row-35 notes and the MCP tool-set clause in the blueprint).

## OUT OF SCOPE

- Any part of J-02–J-07: no dataset store, no `/research/datasets|backtests|pnl/ledger|profiles` endpoints, no strategy grammar, no backtester, no PnL ledger, no `/performance` page, no Performance nav entry, no profile registry, no `app.research.pnl_scan`
- Mutating MCP tools of any kind; MCP proxying of the WebSocket stream; `get_endpoint` support for anything but GET on the three allowlisted prefixes
- Engine, classifier, config-threshold, or cockpit/journal/studies page changes (NavBar rendering source is the only frontend change)
- Caching, retry loops, or offline snapshots inside the MCP server (backend down = explicit error, full stop)
- Real Alpaca credential flows — J-01 is keyless
- Rewriting or restructuring the already-implemented working-tree code for style — verify and fix gaps only (surgical changes)

## DEFINITION OF DONE

- [ ] Target journey J-01 passes via browser-qa-agent (route-map leg) plus the automated byte-identity/read-only/allowlist/backend-down tests listed above
- [ ] Required-still-passing journey J-08 remains green: full backend suite green with all ≥848 archived-era tests intact (dev-claimed count 868 passed / 1 skipped — to be confirmed this dispatch; no archived-era test deleted or weakened), engine equivalence 7/7, cockpit/journal/studies render intact with the same 3-link nav
- [ ] No anti-goal violation introduced (MCP read-only; no execution path; no fabricated data; single source of truth)
- [ ] MCP sync self-test passes; `.mcp.json` generated at repo root and not tracked by git
- [ ] Unit tests pass; no regressions; frontend build passes
- [ ] Dev handoff at `docs/handoffs/goal-tape_to_profit-iter-1-dev.md` verified accurate (it already exists from the interrupted dispatch — update it if verification finds any drift)

## TESTING REQUIREMENTS

- Browser (browser-qa-agent, both services running — NEVER run before this dispatch; must run now):
  - **J-01 route-map leg:** fetch `GET /meta/ui-routes`; verify the rendered top-bar links on `/`, `/journal`, and `/studies` match its `nav: true` entries exactly (Cockpit · Journal · Studies, no Performance); verify `/journal/[id]` navigation still marks Journal active
  - **J-08 regression:** watch `SIM-BUYER` on `/` → panels populate and state settles `buyer_control`; spot-check `/journal` and `/studies` render their data/empty states with the nav present
- Unit/integration (re-run all this dispatch; do not trust the interrupted dispatch's claims without re-execution):
  - Per-tool byte-identity: each MCP tool's returned JSON == the corresponding REST endpoint body, byte-for-byte (including the honest-404 tools: `datasets`, `backtests`, `pnl_ledger`)
  - Read-only guarantees: advertised tool list contains no write verbs; server performs only GETs; `app/mcp` imports nothing from the rest of the `app` package (source-scan test)
  - `get_endpoint` allowlist: `/tape/*`, `/research/*`, `/meta/*` accepted; `/health`, `/watch/SIM-BUYER`, and arbitrary paths refused explicitly (refusal decided before any request)
  - Backend down: every tool returns an explicit error, no cached/fabricated payloads
  - `/meta/ui-routes`: lists exactly the live routes with path + label; excludes `/performance`
  - Full backend suite: `cd apps/backend && .venv/bin/python -m pytest tests/ -v` — all green, ≥848 archived tests intact; equivalence suite 7/7
  - `python3 scripts/automation/lib/mcp_sync_selftest.py self-test` passes after `./scripts/automation/sync-cli-assets.sh`
  - Frontend build: `cd apps/frontend && npm run build` passes
- Error cases: non-allowlisted `get_endpoint` path → explicit refusal (not a proxied call); allowlisted-but-missing path (e.g. `/research/profiles`) → backend's real 404 proxied verbatim; backend stopped → explicit tool error; frontend with backend down → explicit degraded nav state (`nav-unavailable`), no fabricated link list

## NOTES

- **Depth rationale:** lean per the iter-0 evaluator recommendation — one journey, no data model, no persistence, no engine changes; the frontend delta is a single component's data source. The lean cycle (developer → reviewer → browser-qa) still requires the full automated test set above to be green in this dispatch, since most of J-01's acceptance is automated, not browser-visible.
- **Resume integrity:** the evaluator — not the dev handoff — assigns journey status. The interrupted dispatch's claims (868/869 suite, live stdio byte-identity, browser sanity) are treated as unverified until this dispatch's reviewer/browser-qa/evaluator confirm them.
- **Coherence watchpoints for the reviewer:** (1) no second route list anywhere (frontend fallback, MCP-side constant, or test fixture masquerading as the source); (2) MCP tools must not import engine/serializer modules — HTTP proxy only; (3) `.mcp.json` must remain untracked; (4) the developer removed the `nav-link-disabled` branch as dead code — confirm no archived-era browser flow or golden replay script referenced it; (5) the documented MCP non-2xx result contract (`content[0]` = verbatim body, `content[1]` = "HTTP <status> from GET <path>", `isError`) must still satisfy per-tool byte-identity of the body.
- **Install gate:** `mcp==1.28.1` was allowlisted in `incredible_auto_dev/config/install-security-policy.json` via the check-install gate during the interrupted dispatch — reviewer confirms the policy diff is exactly that one allowlist entry. Environment note from iter-0: the backend venv actually runs Python 3.14.4 (project-template says 3.12) — documentation drift only.
- **Demo walkthrough flag (goal.md [NEW]):** narrate one MCP tool call beside its curl equivalent (e.g. `tape_state` for `SIM-BUYER` vs `curl /tape/SIM-BUYER/state`).
- Next natural targets after J-01: J-02 (head of the J-02→J-03→J-04→J-05 chain), at which point the MCP `datasets` tool's honest 404 flips to live data with zero MCP changes.
