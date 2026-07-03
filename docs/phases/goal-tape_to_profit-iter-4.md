# Goal Iteration 4 — Append-only PnL ledger with the founding baseline row (J-04)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit
- **Iteration:** 4
- **Mode:** next
- **Depth:** lean

Frontend Present: no

- **Target journeys:** J-04
- **Required-still-passing journeys:** J-01, J-02, J-03, J-08
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

The product gains its permanent honesty record: an append-only PnL ledger (journal SQLite) whose founding baseline row measures strategy v1 on profile `default` over the fixture train AND hold-out datasets via the existing backtest engine — readable identically at `GET /research/pnl/ledger`, in a pure-rendered `reports/pnl/pnl-history.md`, and through the MCP `pnl_ledger` tool, with no update or delete path anywhere.

## BACKGROUND

Iter-3 delivered J-03 (strategy grammar v1 + deterministic backtest engine) with COHERENCE-PASS and left the suite at 952 collected (951 passed / 1 skipped). The evaluator recommended J-04 next at lean depth — the next link in the J-02 → J-03 → J-04 → J-05 chain, and the last piece before the `/performance` page (J-05) has real data to render. Everything J-04 needs already exists: the committed PG fixture pair (`tests/fixtures/datasets/` — one `train`, one `holdout`, both keyless via the `PG_SIP_REFERENCE` source), the backtest runner + `BacktestJobManager` (`create`/`run_sync` public API, `app/research/backtests.py:500-608`), the persisted row-31 reports with aggregates (`n`, `gross_r`, `net_r`, `gross_usd`, `net_usd`, `win_rate`, `max_drawdown_r`) and the `REGISTER` string precedent (`backtests.py:121`), the JournalStore versioned-migration discipline (v8 today; the v7→v8 step + committed `journal_v7_schema.sql` fixture are the template), and the `verdict_events` append-only repository standard (`store.py:14`). The MCP `pnl_ledger` tool flips from the LAST remaining honest 404 with zero proxy-logic changes — the path is already mapped (`app/mcp/__init__.py:88`), exactly as `datasets` (iter-2) and `backtests` (iter-3) flipped before it.

**Lessons applied:**
- *(iter-2, applies to J-04 explicitly)* Machine-surface journeys get no golden replay script — `demo_runner.py` supports only goto/click/fill. J-04's durable regression lane is the backend suite; browser-originated verification uses Chrome MCP `eval` issuing in-page `fetch()` from a backend-origin page (the technique proven in iters 2–3). Required-still-passing coverage for J-02/J-03 routes through the automated suite.
- *(iter-1, applies to every iteration)* The merged UI results MUST contain one explicit result row per required-still-passing browser journey (J-01, J-08) — a missing row is NOT a pass; browser-qa runs the fallback legs itself if the replay lane produces no rows.
- *(iter-3, applies to every browser/large-suite lane)* Before diagnosing "flaky browser" or unexplained sqlite I/O errors, check `du -sh /tmp/pytest-of-dennis-chan` against the per-user tmpfs quota. (Checked at planning time: 0 bytes, /tmp at 12% — the iter-3 environment must-fix is RESOLVED; the pump now runs a reaper. Keep the check as a pre-flight.)

## IN SCOPE

### Backend
- [ ] **PnL-ledger store (Data Contract row 32) — new `pnl_ledger` table in the journal-scoped SQLite** via the EXISTING JournalStore single-writer queue, added by the versioned on-open v8→v9 migration and proven against a NEW committed old-schema fixture `tests/fixtures/journal_v8_schema.sql` (the exact v7→v8 precedent from iter-3). Row fields per row 32: enhancement id (unique) + title; baseline net R AND net $ vs candidate net R AND net $ on train AND hold-out **separately** (four value pairs — train and hold-out never pooled, no combined figure anywhere); n per split; provenance (per split: source backtest report id, dataset id + checksum; plus strategy id, profile id, `config_fingerprint`); timestamp. **Append-only at the repository level, the `verdict_events` standard (`store.py:14`):** the repository exposes NO update and NO delete method for ledger rows, and no UPDATE/DELETE SQL targets the table outside migration bookkeeping. A duplicate enhancement id → explicit refusal (uniqueness enforcement is not an update path; "one honest row per enhancement" is the model).
- [ ] **Validation append path + the founding baseline row.** A single writer module (e.g. `app/research/pnl_ledger.py`) owns row-32 composition: it takes COMPLETED backtest reports (one train, one hold-out) and copies their aggregates **verbatim** (`net_r`, `net_usd`, `n` from the persisted row-31 payloads — never recomputing trades, never re-deriving R or $). A keyless, deterministic module CLI (developer's naming latitude, e.g. `python -m app.research.pnl_baseline`) seeds the founding row: it obtains the fixture train + hold-out datasets (recording them through the real keyless `PG_SIP_REFERENCE` store path if not already registered), runs one backtest per split via the EXISTING `BacktestJobManager` public API (`create` + `run_sync` — `app/research/backtests.py` computing logic untouched), and appends the row. **Founding-row honesty:** no prior incumbent exists, so the baseline side is explicitly null/absent with a clear founding marker (config-owned enhancement id + title, e.g. "founding baseline — strategy v1 on default") — NEVER fabricated zeros implying a measured comparator. Re-running the seeding command when the founding row already exists → explicit "already present" no-op message and clean exit (idempotent; no duplicate row, no mutation).
- [ ] **`GET /research/pnl/ledger`** on the existing research router — exactly this one route, per Product Shape. Serves the stored rows verbatim (no recomputation on read); the payload carries the visible register **"simulated — assumed fees/slippage — not indicative of live results"** (reuse the existing `REGISTER` constant — never a second copy of the string); each split's figures are labeled **"insufficient sample"** when its n is below the NEW config-owned minimum (marker with n still present — the `analytics_min_sample_size` precedent, `config.py:558-569`); an empty ledger is an honest 200 empty list, never an error. Any non-GET verb on the path → 405 (FastAPI default — no write surface exists).
- [ ] **`reports/pnl/pnl-history.md` — pure render of the stored rows, committed.** A render function + module CLI (developer's naming latitude) reads rows through the SAME store read the route uses and writes the markdown deterministically: regenerating with unchanged rows is a **byte-level no-op** (no wall-clock, no environment-dependent formatting in the render — every displayed value derives only from stored row values); dates render dd-MM-yyyy (foundation invariant 12); every $ figure sits beside its R figure and its n; train and hold-out columns separate; "insufficient sample" labels applied identically to REST; the register string appears verbatim. An empty ledger renders an honest explicit empty state.
- [ ] **Config (no magic numbers):** the minimum-n threshold for the "insufficient sample" label is a new named config value; the founding enhancement id/title are config-owned constants. Document the `config_fingerprint` decision for each new knob with the established commentary + pinning tests (the labeling-only minimum follows the documented `analytics_min_sample_size` EXCLUSION rationale unless the developer records a reason otherwise; nothing here changes any computed research value).
- [ ] **MCP:** zero proxy/transport/handler logic changes — the `pnl_ledger` tool flips from honest 404 to live data by construction (path already mapped at `app/mcp/__init__.py:88`). The ONLY permitted `app/mcp/__init__.py` diff is documentation strings made stale by this iteration: the `pnl_ledger` tool description ("404 until J-04 ships the ledger", `__init__.py:180-184`) and the module-docstring sentence naming the honest-404 premise ("`datasets` / `backtests` / `pnl_ledger` until J-02+…", `__init__.py:17-19`). In `tests/test_mcp_server.py`: move `pnl_ledger` out of `NOT_YET_SHIPPED` into live byte-identity coverage with a non-empty-200 test (the twice-proven `datasets`/`backtests` pattern); with the dict now empty, retire the vacuous honest-404 premise loop and the empty dict surgically (a test that iterates over nothing asserts nothing — removing it is not weakening the suite; every registered tool is now live).

### Frontend
None — no frontend changes this iteration.

### New user-facing capability
The researcher (and the dev-chain over MCP) can read the product's permanent, append-only PnL record: the founding baseline row measuring strategy v1 on profile `default` over the frozen train AND hold-out fixture datasets — net R and net $ per split with n, full provenance, and the simulated register — identically over REST, in the committed `reports/pnl/pnl-history.md`, and via the MCP `pnl_ledger` tool.

### New information displayed
No UI change. New machine-readable information: PnL-ledger rows at `GET /research/pnl/ledger` (which stops 404ing), the same rows pure-rendered in `reports/pnl/pnl-history.md`, and the MCP `pnl_ledger` tool serving live data — the last registered tool to leave the honest-404 state.

### New user actions
None in the browser. New machine actions: the keyless founding-baseline seeding CLI and the markdown regeneration CLI (both deterministic module entries; no REST write path exists for the ledger).

### UI surface changes
None. Cockpit, Journal, Studies pages and the 3-link nav are untouched; no Performance entry yet (that ships with J-05's page, per the blueprint's no-dead-link rule).

### Product surface delta
The machine surface gains the era's scorekeeping backbone: `/research/pnl/ledger` + `reports/pnl/pnl-history.md` on the same research router and journal DB. J-05's `/performance` page gains real data to render next iteration; the browser experience is unchanged this one.

### Blueprint conformance
No new UI surfaces. The ledger is homed exactly where the blueprint's IA table places J-04: "API `/research/pnl/ledger` + `reports/pnl/pnl-history.md` + MCP `pnl_ledger` | machine" — a machine-surface feature with no nav requirement (`reports/pnl/pnl-history.md` is already listed in the blueprint's machine-surface section). Nav skeleton untouched. No blueprint edit, no reapproval request.

### Data-contract additions
None new — Data Contract row 32 (PnL-ledger rows; appended ONCE at validation time by the validation path; served by `GET /research/pnl/ledger`; markdown a pure render; under-min-n splits labeled "insufficient sample") was registered at baseline; this iteration implements it as written. No second computation path for any existing value: ledger figures are verbatim copies of the persisted row-31 backtest aggregates (provenance-linked by report id), backtests run only through `BacktestJobManager`'s public API, datasets only through `DatasetStore`'s public API (row 30), the register string reuses the existing `REGISTER` constant, and REST/markdown/MCP all serve the same stored rows.

## OUT OF SCOPE

- Any part of J-05–J-07: no `/performance` page, no nav change, no frontend change at all; no `/research/profiles` or candidate-profile registry; no champion pointer, no candidate evaluation, no promotion logic, no `app.research.pnl_scan` sweep (the validation append function is built for one caller today — the founding-baseline CLI; the sweep becomes its second caller in J-07)
- Multi-dataset-per-split aggregation beyond the founding row's one-train + one-hold-out shape (per-split multi-dataset breakdown is row-36/J-07 territory)
- Any change to the backtest runner's computing logic, the dataset store, studies, engine, classifier, or serializers (`app/research/backtests.py` compute paths, `app/research/datasets.py`, `app/engine/`, `app/serializers.py` untouched)
- Any `app/mcp/__init__.py` change beyond the stale documentation strings named above; any `app/meta.py` change
- Any update/delete/edit affordance for ledger rows, anywhere, under any name
- Real-scale or credentialed dataset flows — J-04 is keyless on the committed fixture pair
- Editing the stored golden replay scripts (`journey-scripts/J-01.json`, `J-08.json`)

## DEFINITION OF DONE

- [ ] Target journey J-04 passes: full automated acceptance below green, plus browser-visible evidence of the `GET /research/pnl/ledger` flip from the iter-0 404 (`reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-04-research-pnl-ledger-404.png`) to a live 200 carrying the founding row — R beside $ per split, n per split, provenance, register string
- [ ] Required-still-passing journeys remain green: J-01 and J-08 each with one explicit result row in the merged UI test results (deterministic replay row or LLM browser-qa fallback row — a missing row is NOT a pass); J-02 and J-03 via their full automated suites (dataset + backtest + MCP tests) staying green
- [ ] No anti-goal violation introduced (no execution path — `test_no_execution_path.py` green over the new modules; every $ beside its R, its n, its split basis, and the register; no engine change — equivalence 7/7; append-only proven, honest failure states; single source of truth across REST/markdown/MCP; MCP read-only with documentation-strings-only diff)
- [ ] Full backend suite green (all ≥952 existing collected tests intact — none deleted or weakened; the retired vacuous NOT_YET_SHIPPED premise is the one sanctioned removal, replaced by a stronger live byte-identity test) plus the new ledger tests; engine equivalence suite 7/7; frontend build still passes (`npm run build`, unchanged code)
- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit-iter-4-dev.md`

## TESTING REQUIREMENTS

- Browser (services running; browser-qa-agent via Chrome MCP using in-page `fetch()` from a backend-origin page — machine-surface journey, no golden replay script possible per lessons.md):
  - **404→200 flip:** open `GET /research/pnl/ledger` on the backend base URL → 200 JSON with the founding row (iter-0 baseline screenshot showed 404) — capture
  - **Founding-row honesty leg:** display the row's JSON: enhancement id + title, candidate net R AND net $ on train AND hold-out separately with n per split, explicit null/founding baseline side, provenance (backtest report ids, dataset ids + checksums, strategy id, profile `default`, `config_fingerprint`), timestamp, the register string verbatim, and any "insufficient sample" labels — capture
  - **No-write leg:** in-page `fetch()` POST (or DELETE) to `/research/pnl/ledger` → 405 — the ledger has no REST write surface — capture
  - **J-01, J-08 regression:** deterministic replay of the stored golden scripts — the merged results file MUST contain one result row per required journey; if the replay lane produces no rows, browser-qa MUST execute those legs itself (J-01: nav rendered from `/meta/ui-routes`, still 3 links, no `/performance` yet; J-08: SIM-BUYER settles `buyer_control` on `/`, `/journal` and `/studies` render) — lesson iter-1
- Unit/integration (all keyless; run the FULL suite, not just new tests):
  - **Row shape + verbatim copy:** the founding row's per-split net R / net $ / n equal the persisted source backtest reports' aggregates EXACTLY (assert equality against the row-31 payloads fetched by report id — no recomputation tolerance); provenance carries report id, dataset id + checksum per split, strategy id, profile id, `config_fingerprint`; train and hold-out fields separate with no pooled figure anywhere in the payload
  - **Append-only:** the repository exposes no update/delete method for ledger rows (source-level assertion mirroring the verdict-events standard); rows survive store reload; duplicate enhancement id → explicit refusal; seeding CLI re-run → explicit "already present" no-op, ledger byte-identical before/after
  - **Founding baseline side:** explicitly null/absent (never zeros); the founding marker id/title come from config
  - **Determinism:** the seeding path on the fixture pair is deterministic — re-run against a fresh store reproduces identical row values (timestamp/record-identity fields excepted, mirroring the backtest result-payload separation)
  - **Insufficient-sample label:** exercised BOTH ways by controlling the configured minimum in tests (n below min → labeled with n still present; n at/above min → unlabeled); label logic identical on REST and markdown
  - **Markdown render:** pure render through the same store read the route uses; regenerating with unchanged rows is a byte-level no-op (render twice → identical bytes); appending a row then regenerating changes the file; dates dd-MM-yyyy; register string present; every $ beside its R and n; empty ledger → honest explicit empty state
  - **REST:** 200 list shape; empty ledger → 200 empty list; register present; non-GET verbs → 405
  - **Migration:** v8→v9 arrives via the versioned on-open discipline, proven against the NEW committed `tests/fixtures/journal_v8_schema.sql`; existing migration suite intact
  - **MCP:** `pnl_ledger` tool byte-identical to `GET /research/pnl/ledger` on a non-empty 200 (moved out of the honest-404 premise; the vacuous empty-dict premise retired); full MCP suite green; `app/mcp/__init__.py` diff is exactly the stale documentation strings
  - **No-execution gate:** `test_no_execution_path.py` green over the new ledger/CLI modules
  - **Full backend suite green (≥952 collected intact); engine equivalence suite 7/7** (`default` outputs untouched by construction — zero engine files change)
- Error cases: duplicate enhancement id → explicit refusal; seeding re-run → honest no-op; corrupt/missing source backtest report at composition time → explicit error, no partial row; non-GET on the ledger route → 405; empty ledger → honest 200 empty list and honest markdown empty state — never fabricated rows

## NOTES

- **Depth rationale:** lean, per the iter-3 evaluator recommendation and goal.md's sizing. The work is additive and machine-surface — one table + migration, one writer module + two CLI entries, one GET route, one markdown render, MCP doc-strings only — reusing the proven job/store/migration/register patterns with zero engine, frontend, or MCP-logic changes.
- **Lessons surfaced:** (iter-2, Applies to: J-04) machine-surface journey — browser verification via in-page `fetch()` from a backend-origin page; durable regression lane is the backend suite. (iter-1, Applies to: every iteration) one explicit result row per required-still-passing browser journey. (iter-3, Applies to: every browser lane) pre-flight the tmpfs check — resolved at planning time (0 bytes, /tmp 12%) but verify before diagnosing any browser flake.
- **Coherence watchpoints for the reviewer:** (1) ledger figures are verbatim copies of persisted row-31 aggregates, provenance-linked — any recomputation of R, $, n, or trades in the ledger path is a row-31/row-27 violation; (2) one writer module composes row 32; the route, markdown render, and MCP proxy serve the same stored rows — no second query/render path that could diverge; (3) exactly ONE new route on the existing research router, GET only; (4) the register string is the existing `REGISTER` constant, not a second copy; (5) backtests run only via `BacktestJobManager` public API and datasets only via `DatasetStore` public API (extend the iter-3 source-scan pattern to the new modules); (6) `app/mcp/__init__.py` diff is documentation strings only, `app/meta.py` zero diff; (7) no new backend dependency — stdlib suffices, `apps/backend/requirements.txt` untouched.
- **Founding-row framing:** this row is the era's incumbent measurement — the number every future enhancement is judged against on hold-out. Its honesty posture (null baseline side, verbatim copies, small-n labels if the 1-minute fixture windows arm few trades) matters more than its magnitude; iter-3's fixture backtest produced net_r −1.239 on n=5, and an honest negative founding row is a perfectly good founding row.
- **Fingerprint discipline:** the new minimum-n label threshold is labeling-only (it changes no computed research value) — the documented `analytics_min_sample_size` exclusion precedent applies, with pinning tests; if the developer instead folds it in, the reason must be recorded in the config commentary. Note J-07 will later use a configured minimum as a promotion gate — that decision belongs to J-07, not here.
- **`reports/pnl/pnl-history.md` is committed** (not gitignored), so the byte-level no-op regeneration is verifiable via `git diff` as well as by the render-twice test.
- **`Frontend Present` parsing (carried from iters 2–3):** the field is written as a plain unbolded line so `detect_frontend_in_plan()` matches it; this iteration it is genuinely `no`, so the demo N/A stub is honest.
- **Next natural target after J-04:** J-05 (the `/performance` page + Performance nav entry rendered from `/meta/ui-routes`) — the first frontend iteration of the era, rendering exactly this iteration's ledger rows verbatim.
