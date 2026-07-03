# Goal Iteration 2 — Historical tape dataset store with frozen train/hold-out registry (J-02)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit
- **Iteration:** 2
- **Mode:** next
- **Depth:** lean

Frontend Present: no

- **Target journeys:** J-02
- **Required-still-passing journeys:** J-01, J-08
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

The product gains its historical tape dataset store: explicitly recorded trade/quote streams that persist with metadata + checksum, carry an immutable `train | holdout` split tag frozen at registration, and replay byte-identically through a fresh engine — the reproducibility bedrock for every PnL measurement this era will make.

## BACKGROUND

Iter-1 delivered J-01 (read-only MCP server + canonical route map) and kept J-08 green. The evaluator recommended J-02 next at lean depth: it is the head of the J-02 → J-03 → J-04 → J-05 chain, goal.md sizes each journey for one lean iteration, and the MCP `datasets` tool's honest 404 flips to live data with **zero MCP changes** — a free extra byte-identity assertion.

**Lesson applied (iter-1, applies to every iteration):** the deterministic replay of required-still-passing journeys silently no-oped in iter-1 because Playwright is not installed (`engine.log` 04:00:13: "Playwright (Python) is not available"), while the merged UI report still claimed replay coverage with no result rows. Golden scripts now exist for BOTH required journeys (`runs/goal-session-tape_to_profit/journey-scripts/J-01.json`, `J-08.json`), so without the fix this iteration's entire browser regression lane would silently no-op. The evaluator named the Playwright install a must-fix for this iteration — it is IN SCOPE below, and the evaluator must refuse any required-still-passing browser leg that lacks an explicit result row (replay row or LLM row), never trusting the merge header.

The replay/record machinery reuses proven patterns: unpaced offline replay through a fresh `TapeEngine` exactly as `app/research/studies.py` and `test_real_data_classify.py` already do, and the keyless committed fixture windows under `apps/backend/tests/fixtures/alpaca/` (e.g. the PG SIP reference window already used by studies' `reference` source) back the record path with no credentials.

## IN SCOPE

### Backend
- [ ] **Config:** `TAPEOLOGY_DATASET_DIR` env override in `app/config.py` (default `apps/backend/.data/datasets/`, already covered by the `.data/` gitignore entry), mirroring the existing `TAPEOLOGY_JOURNAL_DB` pattern. Any new knob this feature needs lives in config — no magic numbers or inline paths.
- [ ] **Dataset store module** (new, e.g. `app/research/datasets.py`) — the single owner of Data Contract row 30. File-based (NOT SQLite — blueprint persistence note): one dataset = stored neutral seam events (TradeEvent/QuoteEvent fields, provider-agnostic — never raw vendor payloads) + metadata: id, symbol, UTC window, `data_feed` (reuse `feed_basis` helpers), event counts, content checksum, immutable split tag, created timestamp. This module is the only code that reads or writes dataset files.
- [ ] **Record/register:** an explicit research action that fetches a historical window through the EXISTING historical-fetch seam (the same source resolution studies use; the keyless committed reference fixture window must work with no credentials) and persists it. Checksum computed at registration; split tag (`train | holdout`) assigned at registration and immutable forever after — any attempt to change a registered dataset's split returns a 409-style refusal. Synchronous handling is fine at fixture scale — do NOT build a job manager for recording.
- [ ] **Integrity on load:** checksum verified on EVERY load; a corrupted/tampered file surfaces an explicit, distinct error (never silent, never a fabricated dataset). Unknown dataset id → 404. Invalid record request (unknown source, bad split value, missing window) → 422.
- [ ] **Replay:** a store/module-level function that replays a stored dataset unpaced through a FRESH `TapeEngine` (the studies-runner pattern), yielding snapshots byte-identical to replaying the original source stream, deterministic across re-runs. No new REST endpoint for replay (Product Shape lists none) — it is exercised by tests now and consumed by J-03's backtester next.
- [ ] **Routes** on the existing research router: `POST /research/datasets` (record/register), `GET /research/datasets` (list), `GET /research/datasets/{id}` (detail) — exactly these three, per Product Shape. No PATCH/PUT/DELETE paths exist (immutability is structural, not policed).
- [ ] **Committed miniature fixture pair:** one train + one holdout dataset, generated ONCE through the real record path from the committed keyless fixture windows (never hand-crafted JSON), committed under `apps/backend/tests/fixtures/` (outside the gitignored `.data/`), miniature enough for fast CI. Tests load them through the real store path (checksum verification included) and replay them keyless.
- [ ] **No ambient recording:** watching a live or sim ticker (e.g. `SIM-BUYER` end-to-end) writes zero dataset files — test-locked.
- [ ] **MCP: zero code changes.** The existing `datasets` tool flips from honest 404 to live data automatically. Re-run the byte-identity suite; if the existing per-tool test only ever saw the 404 case, extend it minimally to assert byte-identity on a non-empty 200 list — surgical, no restructuring.

### Test/CI infrastructure (harness, not product code)
- [ ] **Install Playwright for the deterministic replay runner** (evaluator must-fix from iter-1): run `./scripts/automation/check-install.sh "pip install playwright"` first (install gate; if a policy allowlist entry is needed, mirror the `mcp` precedent — reviewer confirms the policy diff is exactly that one entry), then install so the plain `python3` the harness invokes can import it: `python3 -m pip install --user playwright && python3 -m playwright install chromium` (add `--break-system-packages` only if PEP 668 blocks `--user`, and say so in the handoff). Verify: `python3 -c "import playwright"` exits 0 and `python3 -m playwright --version` prints. Playwright MUST NOT be added to `apps/backend/requirements.txt` — it is harness tooling, not a product dependency.

### Frontend
None — no frontend changes this iteration.

### New user-facing capability
The researcher (and the dev-chain over MCP) can record a historical tape window as a permanent, checksummed dataset, freeze it as `train` or `holdout` at registration, list and inspect datasets over REST/MCP, and trust that replaying it reproduces the source stream's engine outputs byte-for-byte.

### New information displayed
No UI change. New machine-readable information: dataset records (symbol, UTC window, feed, event counts, checksum, split tag) at `GET /research/datasets*` and via the MCP `datasets` tool — which stops 404ing and starts serving real data.

### New user actions
None in the browser. New API action: `POST /research/datasets` (record/register — an explicit research action, never ambient).

### UI surface changes
None. Cockpit, Journal, Studies pages and the 3-link nav are untouched.

### Product surface delta
The machine surface grows its first era-3 data capability: the dataset registry behind `/research/datasets*`, feeding J-03's backtester next iteration. Browser experience is unchanged.

### Blueprint conformance
No new UI surfaces. Datasets are homed exactly where the blueprint's IA table places J-02: "API `/research/datasets*` + MCP `datasets` | machine" — a machine-surface feature with no nav requirement. Nav skeleton untouched. No blueprint edit, no reapproval request.

### Data-contract additions
None new — Data Contract row 30 (Dataset records; owner: dataset store module, single writer; served by exactly `POST/GET /research/datasets*`) was registered at baseline; this iteration implements it as written. No second computation or serving path for any existing contract value: MCP stays a verbatim proxy, and nothing else reads dataset files except the store module.

## OUT OF SCOPE

- Any part of J-03–J-07: no strategy grammar, no backtest engine or `/research/backtests*`, no PnL ledger or `/research/pnl/ledger`, no `/research/profiles`, no `app.research.pnl_scan`, no `/performance` page or nav entry
- Recording live or sim watch streams (a seeded sim stream reproduces on demand; datasets are HISTORICAL tape) — and any ambient/automatic recording of the live cockpit's tape
- Credentialed Alpaca recording flows or tests — J-02 is keyless; real-scale recording is a later operator action through the same seam and changes no behavior
- Any UI for datasets (machine surface per blueprint); any frontend change at all
- Engine, classifier, config-threshold, serializer, or profile changes; any change to `app/mcp/` or `app/meta.py`
- Dataset update/delete/re-tag endpoints, retention/GC policies, compression, or background job machinery for recording
- Editing the stored golden replay scripts (`journey-scripts/J-01.json`, `J-08.json`)

## DEFINITION OF DONE

- [ ] Target journey J-02 passes: full automated acceptance below green, plus the browser-visible flip of `GET /research/datasets` from baseline 404 to live 200 JSON captured as evidence
- [ ] Required-still-passing journeys J-01 and J-08 remain green **with one explicit result row each** in the merged UI test results (deterministic replay row or LLM browser-qa row — a missing row is NOT a pass)
- [ ] Playwright installed and verified for the harness `python3`; the replay lane produced real result rows this iteration (no silent no-op)
- [ ] No anti-goal violation introduced (no execution path; no ambient recording; honest failure states for corrupt/unknown/invalid; single source of truth; MCP untouched and read-only)
- [ ] Full backend suite green (all ≥868 existing tests intact — none deleted or weakened) plus the new dataset tests; engine equivalence suite 7/7; frontend build still passes (`npm run build`, unchanged code)
- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit-iter-2-dev.md`

## TESTING REQUIREMENTS

- Browser (services running; browser-qa-agent + deterministic replay):
  - **J-02 slice:** open `GET /research/datasets` on the backend base URL → 200 JSON listing the registered fixture datasets (iter-0 baseline screenshot showed 404) — capture a screenshot as evidence
  - **J-01, J-08 regression:** verified via deterministic replay of the stored golden scripts now that Playwright is installed — the merged results file MUST contain one result row per required journey. If the replay lane still produces no rows (e.g. the install failed), the browser-qa agent MUST execute the J-01 route-map leg and the J-08 legs (SIM-BUYER on `/` settles `buyer_control` with populated panels; `/journal` and `/studies` render with the 3-link nav) itself, despite any "a deterministic replay verifies them separately" exclusion in its dispatch prompt — that exclusion is only true when replay rows actually exist (lesson iter-1)
- Unit/integration (all keyless; run the FULL suite, not just new tests):
  - Record from the keyless committed fixture window → metadata correct: symbol, UTC window, `data_feed`, event counts, checksum present
  - Register `train` and `holdout` tags; any re-tag attempt on a registered dataset → 409-style refusal; tag survives store reload
  - Replay a stored dataset through a fresh engine twice → identical snapshots; replay vs the original source stream → **byte-identical** state/confidence/features/history (reuse the existing snapshot-comparison approach from the equivalence/real-data-classify tests)
  - Checksum verified on load: corrupt a copy of a dataset file → explicit, distinct error (not silence, not a fabricated dataset)
  - Committed miniature train + holdout fixture pair loads through the real store path and replays in CI without credentials
  - Watching a sim ticker end-to-end writes zero dataset files (no ambient recording)
  - REST: list + detail shapes; unknown id → 404; invalid record body (unknown source / bad split / missing window) → 422
  - MCP `datasets` tool byte-identical to `GET /research/datasets` with non-empty live data (zero MCP code changes)
  - Full backend suite green; engine equivalence suite 7/7 (`default` outputs untouched by construction — no engine files change)
- Error cases: corrupt dataset file → explicit integrity error; re-tag → 409; unknown dataset id → 404; malformed record request → 422; no dataset writes from any watch path

## NOTES

- **Depth rationale:** lean per the iter-1 evaluator recommendation and goal.md's explicit sizing ("Each is sized for one lean iteration"). The store is additive and isolated — a new module + three routes + a file store; zero engine, serializer, frontend, or MCP code changes — so the full 11-step pipeline buys nothing over dev → review → browser-qa with the full automated suite green.
- **Lesson surfaced (iter-1, Applies to: every future iteration):** replay of required-still-passing journeys silently no-ops without Playwright while the merged report still claims replay coverage. This spec (a) puts the install in scope as the evaluator's must-fix, and (b) instructs browser-qa and the evaluator to demand a per-journey result row — no row, no pass.
- **Coherence watchpoints for the reviewer:** (1) the dataset store module is the ONLY reader/writer of dataset files — no second loader in tests or future-facing helpers (tests go through the store's API); (2) checksum verification must not be bypassable by any load call; (3) no dataset write is reachable from the watch/stream path; (4) `app/mcp/` and `app/meta.py` diffs must be empty (the `datasets` flip is free by construction); (5) no new backend dependency expected (stdlib `hashlib`/`json` suffice) — `apps/backend/requirements.txt` should be untouched, and Playwright must appear ONLY at the harness level.
- **Fixture-pair honesty:** the committed pair is generated through the real record path from committed keyless fixture windows and then frozen — never hand-authored — so CI proves record→register→replay end-to-end, including checksum verification, with no credentials.
- **`Frontend Present` parsing (applies to future specs too):** iter-1's bolded `- **Frontend Present:** yes` metadata bullet did not match `detect_frontend_in_plan()`'s literal grep (`frontend present: yes`), so the demo step stubbed itself claiming a backend-only iteration. This spec writes the field as a plain unbolded line; this iteration it is genuinely `no`, so the demo N/A stub is honest.
- **Environment note (carried from iter-1, doc drift only):** the backend venv runs Python 3.14.4 while project-template says 3.12.
- **Next natural target after J-02:** J-03 (strategy grammar v1 + deterministic backtest engine over these datasets), continuing the chain toward J-04/J-05; the MCP `backtests` tool then flips from honest 404 the same way `datasets` does now.
