# Goal Iteration 0 — Verify-only baseline of the profit-research era (J-01–J-08)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08
- **Required-still-passing journeys:** none (baseline — no prior passing set; archived-era behavior is covered by J-08 itself)
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

Establish a trustworthy baseline: verify all eight era-3 must-have journeys (J-01–J-08) against the current codebase with NO code changes, recording which already pass, which fail, and which are partial.

## BACKGROUND

This is a baseline assessment, not a feature delivery. Era 3 (`tape_to_profit`) starts on top of the completed eras 1–2 product (archived journeys J-01–J-68, GOAL_ACHIEVED). Codebase evidence gathered at planning time: there is no `app/mcp` module, no `/research/datasets`, `/research/backtests`, `/research/pnl/ledger`, or `/research/profiles` endpoint, no `app.research.pnl_scan` module, no `apps/frontend/app/performance/` page, no `/meta/ui-routes` endpoint (the nav list is hardcoded in `apps/frontend/components/NavBar.tsx`), and `project-extensions/mcp-servers.yaml` is an empty placeholder (`servers: {}`). The archived-era product (cockpit `/`, `/journal`, `/journal/[id]`, `/studies`, full backend suite) is intact. Expectation: J-01–J-07 FAIL (not built), J-08 PASSES — but verification must confirm this, not assume it. The session blueprint was drafted this iteration at `runs/goal-session-tape_to_profit/state/blueprint.md`.

## IN SCOPE

### Backend
- (none — no code changes in baseline)

### Frontend
- (none — no code changes in baseline)

### Verification work (the entire scope)
- [ ] Run the full backend suite and record the exact pass count (this is the era-3 baseline count; goal.md cites 848+ tests)
- [ ] Run the engine equivalence test (byte-identical default outputs) and record the result
- [ ] Probe each era-3 REST surface and record the response: `GET /meta/ui-routes`, `GET /research/datasets`, `GET /research/backtests`, `GET /research/pnl/ledger`, `GET /research/profiles` (all expected 404)
- [ ] Attempt `apps/backend/.venv/bin/python -m app.mcp --help` and `... -m app.research.pnl_scan --help` from `apps/backend/` and record the outcome (expected: module not found)
- [ ] Record that `project-extensions/mcp-servers.yaml` is `servers: {}` and that no `.mcp.json` exists at the repo root
- [ ] Record that no dataset store directory/fixture pair, no `reports/pnl/`, and no strategy/profile config sections exist
- [ ] Browser-verify J-08 and the absence checks listed under TESTING REQUIREMENTS

### New user-facing capability
None — verification only.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None. The product is byte-identical before and after this iteration.

### Blueprint conformance
No new surfaces. The blueprint itself was drafted this iteration (`runs/goal-session-tape_to_profit/state/blueprint.md`): archived IA (Cockpit · Journal · Studies) + one registered future entry (Performance, ships with J-05), era-3 Data Contract rows 30–36 registered for future iterations.

### Data-contract additions
None built. Rows 30–36 are registered in the blueprint as the era-3 contract; nothing is implemented this iteration.

## OUT OF SCOPE

- Implementing ANY part of J-01–J-07 (no MCP server, no dataset store, no backtester, no ledger, no `/performance` page, no profiles, no sweep)
- Fixing any failure found during verification — failures are recorded for future iterations, not repaired
- Modifying `NavBar.tsx`, `mcp-servers.yaml`, config, or any source file
- Real Alpaca credential flows — all era-3 journeys are keyless per goal.md; real-scale datasets are an operator action, not a journey requirement
- Writing new tests (the existing suite is run, not extended)

## DEFINITION OF DONE

- [ ] Every journey J-01 through J-08 verified against the current codebase, each with an explicit expected-fail/pass result and concrete evidence recorded
- [ ] Full backend suite executed; exact collected/passed counts recorded as the era-3 baseline
- [ ] No anti-goal violation introduced (trivially satisfied — zero code changes; verify `git status` shows no source modifications)
- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit-iter-0-dev.md` (verification evidence, explicitly noting no code was changed)

## TESTING REQUIREMENTS

- Browser (browser-qa-agent, both services running):
  - **J-08 (expected PASS):** watch `SIM-BUYER` on `/` → cockpit panels populate and state settles `buyer_control`; stop; watch `SIM-SELLER` → settles `seller_control`; spot-check `/journal` renders its thesis table and `/studies` renders its create form + job list
  - **J-05 (expected FAIL):** the persistent nav shows exactly Cockpit · Journal · Studies (no Performance entry); navigating to `/performance` yields the Next.js 404, not a PnL page
  - **J-01 route-map leg (expected FAIL):** `GET /meta/ui-routes` on the backend returns 404
- Unit/integration (verification commands, no new tests):
  - `cd apps/backend && .venv/bin/python -m pytest tests/ -v` — must be green; record counts (J-08 suite clause)
  - Endpoint probes and module-import attempts listed in IN SCOPE, each with recorded status codes/errors (J-01, J-02, J-03, J-04, J-06, J-07 absence evidence)
- Error cases: n/a — verify-only iteration; the "expected 404 / module not found" probes above are the negative evidence.

## NOTES

- The goal-evaluator — not this spec — assigns journey statuses. This spec predicts J-01–J-07 FAIL and J-08 `already_passing`, and supplies the evidence-collection plan.
- Dependency order for subsequent iterations (from goal.md): J-02 → J-03 → J-04 → J-05 and J-06 → J-07; J-01 is independent; J-08 guards continuously. A sensible iter-1 is either J-01 (independent, unlocks MCP-assisted verification of everything later) or J-02 (head of the main chain).
- Lessons ledger is empty (first iteration of this session). Prior sessions' standing discipline carried into the blueprint: versioned SQLite migrations proven against committed fixtures, config-owned thresholds with `config_fingerprint` membership decided explicitly, byte-identity guarded by pinned equivalence tests.
- Blueprint is auto-approved by default; pass `--require-blueprint-approval` to `run-goal.sh` to pause and review `runs/goal-session-tape_to_profit/state/blueprint.md` before iter-1.
