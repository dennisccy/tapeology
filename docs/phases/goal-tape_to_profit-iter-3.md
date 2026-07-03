# Goal Iteration 3 — Strategy grammar v1 + deterministic backtest engine (J-03)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit
- **Iteration:** 3
- **Mode:** next
- **Depth:** lean

Frontend Present: no

- **Target journeys:** J-03
- **Required-still-passing journeys:** J-01, J-02, J-08
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

The product gains its first PnL measurement machinery: a config-owned strategy grammar v1 and a deterministic backtest engine that replays a stored dataset unpaced through a fresh engine, simulates entries/exits with explicit fee and slippage models, and persists a fully-provenanced report — net AND gross R AND $, win rate, max drawdown (R), n — beside a seeded random-entry null baseline, byte-identical on re-run.

## BACKGROUND

Iter-2 delivered J-02 (dataset store with frozen train/hold-out registry) with COHERENCE-PASS, installed Playwright so the deterministic replay lane produces real result rows, and left the suite at 901 passed / 1 skipped. The evaluator recommended J-03 next at lean depth: it is the next link in the J-02 → J-03 → J-04 → J-05 chain, sized for one lean iteration by goal.md, and now keyless-unblocked by the committed PG fixture dataset pair plus `DatasetStore.replay`. The MCP `backtests` tool flips from honest 404 to live data exactly as `datasets` did in iter-2 — with zero MCP proxy-logic changes.

**Reuse anchors (all proven in the codebase — do not reinvent):** the cancellable-job pattern (`StudyJobManager` in `app/research/studies.py`: create/start/run_sync/cancel/join_all, persisted queued→running→done|cancelled|failed statuses); the state-native arming rules (`_premise_state` — sustained matching CONTROL arms `trend_continuation`, sustained matching ABSORPTION arms `absorption_reversal`, gated by `study_arm_sustain_seconds` / `study_arm_cooldown_seconds`); the ONE shared R formula (`marks.r_basis` — Data Contract row 27 discipline: never a second formula); `DatasetStore.replay(dataset_id, config)` for deterministic unpaced replay through a fresh engine; the JournalStore single-writer queue + versioned on-open migrations proven against the committed old-schema fixture; and the `study_null_baseline_seed` precedent for a recorded, overridable null seed.

**Lessons applied:**
- *(iter-2, applies to J-03 explicitly)* Machine-surface journeys cannot get golden replay scripts — `demo_runner.py` supports only goto/click/fill and `normalize_url` rewrites any localhost URL onto the frontend base. J-03's durable regression lane is the backend suite; its browser-originated verification uses Chrome MCP `eval` issuing in-page `fetch()` from a backend-origin page (the iter-2 technique that drove POST/409/422 flows).
- *(iter-1, applies to every iteration)* The replay lane silently no-ops without result rows. Playwright is now installed (verified iter-2), but the merged UI results MUST still contain one explicit result row per required-still-passing browser journey (J-01, J-08) — a missing row is NOT a pass, and browser-qa must run those legs itself if the replay lane produces no rows.

## IN SCOPE

### Backend
- [ ] **Strategy grammar v1 (config-owned — Data Contract row 34):** the complete v1 strategy definition lives in `app/config.py` (or a config-owned structure it exposes) — never inline in runner code. It declares: entry rules as the EXISTING state-native setup arming (setup type × direction over `trend_continuation` / `absorption_reversal`, long and short, reusing the studies' sustained-premise-state + sustain/cooldown rules and constants — no new indicator, no new inline threshold); exits by invalidation R-stop (the arm-instant synthetic-invalidation approach, R via the shared `marks.r_basis` helper), time horizon, and state-flip; an explicit fee model (per-share fee + minimum-per-trade); an explicit slippage model (spread fraction applied adversely at each fill); a fixed $-per-R notional for dollar conversion. Every knob is a named config value with the established fingerprint commentary (real strategy/fee/slippage thresholds ENTER `config_fingerprint`; serving-only knobs are excluded per the documented pattern with pinning tests). No ML, no runtime mutation. Level setups (`level_break`, `failed_move_fade`) are NOT in v1 — they require an operator-supplied hindsight level and have no state-native arming.
- [ ] **Backtest runner module (new, e.g. `app/research/backtests.py`) — the single computing owner of Data Contract row 31.** Deterministic, seeded, unpaced, single-threaded per run: consumes `DatasetStore.replay` (public API only — never a second dataset-file reader), arms entries per the strategy, simulates fills at recorded prices adjusted by the configured slippage model, applies the fee model, and produces the report computed ONCE and persisted. Report content: per-trade list (direction, setup type, entry/exit logical ts + fill prices, exit reason `r_stop | horizon | state_flip | dataset_end`, gross/net R, gross/net $, fees, slippage) and aggregates — **net AND gross R AND $**, win rate, max drawdown (R), n — beside a seeded random-entry null baseline on the SAME dataset (same exits, fees, slippage; seed recorded in the report; mirror the `study_null_baseline_seed` recorded-override precedent). Stamped with full provenance: dataset id + checksum, the resolved strategy config echoed verbatim, profile id (`default`), `config_fingerprint`. The report payload carries the visible register **"simulated — assumed fees/slippage — not indicative of live results"**. An open trade at stream end is handled explicitly and deterministically (e.g., forced exit at the last recorded price labeled `dataset_end`) — documented, never silent. A window that arms zero trades yields an honest n=0 report (empty trade list, n=0 aggregates), never fabricated trades and not an error.
- [ ] **Byte-identical re-runs:** the persisted report separates the deterministic result payload (trades, aggregates, null baseline, provenance, register) from run-identity metadata (record id, wall-clock created timestamp, job status) so that an identical request re-run produces a **byte-identical** result payload — the unit the acceptance test compares.
- [ ] **Cancellable job like studies:** the backtest runs through a job manager mirroring `StudyJobManager` (queued → running → done | cancelled | failed statuses persisted; cancel honored mid-run; a failure — e.g., a dataset integrity error surfacing from the store — persists an explicit `failed` record with the error, never silence or fabricated results).
- [ ] **Persistence:** backtest records in the journal-scoped SQLite via the EXISTING JournalStore single-writer queue, with a new table added under the versioned on-open migration discipline (proven against the committed old-schema fixture DB, like every prior schema addition). Rows survive store reload.
- [ ] **Routes** on the existing research router — exactly these four, per Product Shape: `POST /research/backtests` (create + start job; body: dataset id, strategy id, profile), `GET /research/backtests` (list), `GET /research/backtests/{id}` (detail), `POST /research/backtests/{id}/cancel` (mirroring studies). GET serves the stored rows verbatim — no recomputation on read. Validation is honest and distinct: unknown dataset id → 404-style refusal; unknown strategy id (anything but the registered v1) → 422; profile other than `default` → 422 (the profile registry is J-06 — until it ships, `default` is the only registrable value and the refusal is honest); malformed body → 422.
- [ ] **Grep-style no-broker test (J-03 acceptance requires it — build it in from the start):** an automated test asserting no broker, order-placement, or account-management code exists anywhere in the repo (e.g., scans `apps/` sources for broker-SDK imports and order-submission/account patterns such as `submit_order`, `create_order`, `paper_trading`, brokerage endpoints). Design it to be signal-bearing (targeted patterns with a documented rationale), not a naive substring grep that false-positives on prose like "ordered events".
- [ ] **MCP:** zero proxy/transport/handler logic changes — the `backtests` tool flips from honest 404 to live data by construction. The ONLY permitted `app/mcp/__init__.py` diff is updating the two now-stale tool description strings: the `datasets` description ("404 until J-02 ships the dataset store", stale since iter-2 — the reviewer's NOTE at app/mcp/__init__.py:165) and the `backtests` description ("404 until J-03 ships", made stale by this iteration). In `tests/test_mcp_server.py`, move `backtests` out of the honest-404 premise and add a byte-identity assertion on a non-empty 200 list, mirroring the iter-2 `datasets` addition — surgical, no restructuring.

### Frontend
None — no frontend changes this iteration.

### New user-facing capability
The researcher (and the dev-chain over MCP) can run a deterministic, cancellable backtest of the config-owned v1 strategy on any registered dataset, and read a fully-provenanced PnL report — per-trade fills and aggregates in net/gross R AND $, win rate, max drawdown, n — always beside a seeded random-entry null baseline, reproducible byte-for-byte.

### New information displayed
No UI change. New machine-readable information: backtest reports at `GET /research/backtests*` and via the MCP `backtests` tool — which stops 404ing and starts serving real data.

### New user actions
None in the browser. New API actions: `POST /research/backtests` (run a backtest job) and `POST /research/backtests/{id}/cancel`.

### UI surface changes
None. Cockpit, Journal, Studies pages and the 3-link nav are untouched; no Performance entry yet (that ships with J-05's page, per the blueprint's no-dead-link rule).

### Product surface delta
The machine surface gains the era's core measurement engine: `/research/backtests*` behind the same research router, feeding J-04's PnL ledger next. Browser experience is unchanged.

### Blueprint conformance
No new UI surfaces. Backtests are homed exactly where the blueprint's IA table places J-03: "API `/research/backtests*` + MCP `backtests` | machine" — a machine-surface feature with no nav requirement. Nav skeleton untouched. No blueprint edit, no reapproval request.

### Data-contract additions
None new — Data Contract rows 31 (Backtest reports; owner: the backtest runner, computed once and persisted; served by exactly `POST/GET /research/backtests*` + cancel) and 34 (Strategy definition v1; config-owned; read by the runner and echoed verbatim in report provenance) were registered at baseline; this iteration implements them as written. No second computation path for any existing value: R comes from the shared `marks.r_basis` helper (row 27), datasets are read only through `DatasetStore`'s public API (row 30), `config_fingerprint` comes from the existing config hasher, and REST/MCP serve the stored report rows verbatim.

## OUT OF SCOPE

- Any part of J-04–J-07: no PnL ledger or `GET /research/pnl/ledger`, no `reports/pnl/` markdown, no `/research/profiles` or candidate-profile registry, no champion pointer or promotion machinery, no `app.research.pnl_scan` sweep, no multi-dataset orchestration
- The `/performance` page, any nav change, any frontend change at all
- Level-setup entries (`level_break`, `failed_move_fade`) in the strategy grammar — no state-native arming exists for them; v1 is state-native only
- Strategy variants/enumeration beyond the single config-owned v1 (variant enumeration is J-07 sweep territory); any per-request inline strategy definition
- Engine, classifier, serializer, or threshold changes of any kind (`app/engine/`, `app/serializers.py` untouched); any change to the dataset store module (`app/research/datasets.py`) or to studies behavior
- Any `app/mcp/__init__.py` change beyond the two stale description strings; any `app/meta.py` change
- Real-scale or credentialed dataset flows — J-03 is keyless on datasets recorded from the committed fixture windows
- Editing the stored golden replay scripts (`journey-scripts/J-01.json`, `J-08.json`)

## DEFINITION OF DONE

- [ ] Target journey J-03 passes: full automated acceptance below green, plus browser-visible evidence of the `GET /research/backtests` flip from baseline 404 to live 200, a completed report's JSON (per-trade + aggregates + null baseline + provenance + register), and a byte-identical re-run
- [ ] Required-still-passing journeys remain green: J-01 and J-08 each with one explicit result row in the merged UI test results (deterministic replay row or LLM browser-qa row — a missing row is NOT a pass); J-02 via its full automated suite (dataset + MCP `datasets` tests) staying green
- [ ] No anti-goal violation introduced (no execution path — grep test green; every $ beside its R, its n, its assumptions, its null baseline, and the simulated register; no engine change — equivalence 7/7; honest failure states; single source of truth; MCP read-only with description-strings-only diff)
- [ ] Full backend suite green (all ≥901 existing tests intact — none deleted or weakened) plus the new strategy/backtest tests; engine equivalence suite 7/7; frontend build still passes (`npm run build`, unchanged code)
- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit-iter-3-dev.md`

## TESTING REQUIREMENTS

- Browser (services running; browser-qa-agent via Chrome MCP using in-page `fetch()` from a backend-origin page — machine-surface journey, no golden replay script possible per lessons.md):
  - **404→200 flip:** open `GET /research/backtests` on the backend base URL → 200 JSON (iter-0 baseline screenshot showed 404) — capture
  - **End-to-end keyless run:** list datasets (record one via the iter-2-proven keyless `POST /research/datasets` reference-source flow if the runtime store is empty) → `POST /research/backtests` with that dataset id + strategy v1 + profile `default` → poll to `done` → open the detail: per-trade list and/or honest n=0, aggregates (net/gross R AND $, win rate, max drawdown, n), null baseline with recorded seed, provenance (dataset id + checksum, strategy echo, profile id, `config_fingerprint`), and the register string visible in the JSON — capture
  - **Determinism leg:** re-POST the identical request, poll to done, and demonstrate the result payloads are byte-identical (e.g., in-page string/hash comparison of the two result blocks) — capture
  - **Error legs:** POST with an unknown dataset id → honest 404-style refusal; POST with a non-`default` profile → 422 — capture at least one
  - **J-01, J-08 regression:** deterministic replay of the stored golden scripts (Playwright installed iter-2) — the merged results file MUST contain one result row per required journey; if the replay lane produces no rows, browser-qa MUST execute those legs itself (J-01: nav rendered from `/meta/ui-routes`; J-08: SIM-BUYER settles `buyer_control` on `/`, `/journal` and `/studies` render) — lesson iter-1
- Unit/integration (all keyless; run the FULL suite, not just new tests):
  - Strategy definition read entirely from config: entry arming reuses the existing state-native rules and constants (no new inline threshold anywhere — assert knobs live in config); exits R-stop / horizon / state-flip; fee, slippage, and $-per-R knobs present and applied
  - Fill honesty: fills at recorded prices adjusted by the slippage model — assert exact adjusted entry/exit prices, fees, gross-vs-net R and $ arithmetic on a known deterministic dataset (record synthetic or fixture windows through the REAL store path; never hand-crafted report JSON)
  - Exit coverage: at least one trade exercising each exit reason (`r_stop`, `horizon`, `state_flip`) plus the explicit `dataset_end` handling for a trade open at stream end
  - Determinism: identical request re-run → byte-identical result payload; the null baseline is seeded, its seed recorded in the report, and re-runs reproduce it exactly
  - Honest emptiness: a dataset window arming zero strategy trades → n=0 report with empty trade list (no error, no fabricated trades); the committed miniature fixture pair runs keyless end-to-end whatever its n
  - Job lifecycle mirrors studies: queued→running→done persisted; cancel → `cancelled` persisted; a corrupt dataset (integrity error from the store) → explicit `failed` record carrying the error
  - Persistence: new table arrives via the versioned migration discipline and is proven against the committed old-schema fixture DB; backtest rows survive store reload
  - REST: list + detail shapes; unknown backtest id → 404; unknown dataset id on POST → 404-style; unknown strategy → 422; non-`default` profile → 422; malformed body → 422; cancel of unknown id → 404
  - MCP: `backtests` tool byte-identical to `GET /research/backtests` on a non-empty 200 (moved out of the honest-404 premise); full MCP suite still green; `app/mcp/__init__.py` diff is exactly the two description strings
  - Grep-style no-broker/order/account test green
  - Full backend suite green (≥901 existing tests intact); engine equivalence suite 7/7 (`default` outputs untouched by construction — zero engine files change)
- Error cases: unknown dataset → 404-style; unknown strategy / non-default profile / malformed body → 422; corrupt dataset mid-job → explicit `failed` with the integrity error; cancel semantics mirror studies exactly; no backtest machinery reachable from any watch/stream path

## NOTES

- **Depth rationale:** lean, per the iter-2 evaluator recommendation and goal.md's sizing ("Each is sized for one lean iteration"). The work is additive and machine-surface — a new runner module + config-owned strategy + four routes + one migration — reusing the proven job/replay/store patterns with zero engine, frontend, or MCP-logic changes, so the full 11-step pipeline buys nothing over dev → review → browser-qa with the full automated suite green.
- **Lessons surfaced:** (iter-2, Applies to: J-03) machine-surface journeys get no golden replay script — browser verification runs through Chrome MCP in-page `fetch()` from a backend-origin page, and J-03's durable regression lane is the backend suite. (iter-1, Applies to: every iteration) required-still-passing browser journeys need one explicit result row each — never trust the merge header.
- **Coherence watchpoints for the reviewer:** (1) the runner computes row 31 ONCE and persists — GET/list/detail and the MCP proxy serve stored rows verbatim, no recomputation on read; (2) R is derived ONLY via the shared `marks.r_basis` helper — a second R formula is a row-27 violation; (3) datasets are read ONLY through `DatasetStore`'s public API — no second dataset-file reader; (4) the strategy config (row 34) is echoed verbatim in provenance, never restated or reinterpreted; (5) exactly four routes on the existing research router, no PATCH/PUT/DELETE; (6) the `app/mcp/__init__.py` diff is exactly two description strings and `app/meta.py` has zero diff; (7) no new backend dependency — stdlib suffices; `apps/backend/requirements.txt` untouched.
- **Fingerprint shift is intended, not a defect:** new strategy/fee/slippage thresholds enter `config_fingerprint` (they shape persisted research values), shifting the fingerprint exactly as every prior research-config addition did; serving-only knobs (e.g., a list cap mirroring `study_list_max`) follow the documented exclusion discipline with pinning tests.
- **Honesty framing for this iteration in particular:** this is the iteration that introduces simulated fills — the single permitted "fill" in the whole product. Every fill is computed offline against recorded historical tape, labeled simulated via the register string in the report payload, and sent nowhere; the grep-style test makes "no broker/order/account code" an enforced invariant from day one.
- **`Frontend Present` parsing (carried from iter-2):** the field is written as a plain unbolded line so `detect_frontend_in_plan()` matches it; this iteration it is genuinely `no`, so the demo N/A stub is honest.
- **Next natural target after J-03:** J-04 (the append-only PnL ledger) — its founding baseline row evaluates strategy v1 on profile `default` over the fixture train AND hold-out datasets using exactly this iteration's backtest reports.
