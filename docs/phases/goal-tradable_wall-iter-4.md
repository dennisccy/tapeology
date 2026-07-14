# Goal Iteration 4 — J-04 the 3-way edge report + `structure_tape_map` (backend, keyless)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tradable_wall
- **Iteration:** 4
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-04
- **Required-still-passing journeys:** J-01, J-02, J-03 (keyless substrate only), J-07
- **Anti-goal reminders** (verbatim from `docs/goal.md`):
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **No gate bending for a headline.** n≥5 per reported cell, train/hold-out separation, null baseline, and the full PnL register hold everywhere; an empty or all-`insufficient_sample` edge report is a valid, publishable outcome. *(critical)*
  - **The champion moves only through the existing sweep gate on hold-out data.** This era may feed the gate; it never hand-promotes `structure_tape_map` or anything else. *(critical)*
  - **New strategy code is additive and registered — never a mutation.** `structure_tape_map` is a new config-owned registry entry beside frozen `v1`/`structure_tape`; no frozen definition, parameter, or output changes; the `config_fingerprint` stays `4d665603569b9dbf`. *(critical)*
  - **Feed honesty — never pool across feeds.** The `feed` stamp comes verbatim from the adapter/key tier; `iex`, `sip`, and Yahoo-bar lineages are never pooled in any analysis cell, report row, or claim; `iex` is never presented as the consolidated tape. *(critical)*
  - **Descriptive, never imperative.** Chips, case studies, and reports state conditions and cite measured history — never "buy/sell/short now", no prediction or expected-return language, anywhere in UI copy. *(critical)*

## GOAL

Deliver the honest 3-way edge report — `v1` vs the frozen `structure_tape` vs a new registered `structure_tape_map`, backtested over the recorded event window(s) and aggregated into per strategy × class × side × reaction cells (n≥5 or `insufficient_sample`, train/hold-out never pooled, feeds never pooled, null baseline, full PnL register) — served from the new canonical `GET /research/edge-report` (+ read-only MCP proxy), all keyless over the committed fixture.

## BACKGROUND

Dependency order is J-01 → J-02 → J-03 → J-04; J-01/J-02 are passing, J-03's keyless join substrate landed (partial), and the iter-3 evaluator explicitly recommends building **J-04 next at full depth** — it is the last measurement layer before J-05 can render the map/cases/report. No journey regressed and the last coherence verdict was `COHERENCE-PASS`, so no consolidation is owed. **Depth is full** because this iteration touches the strategy-registry data model (`config.py`), spans four backend modules (`config` + `backtests` + `edge_report` + `routes`) plus the MCP surface, and requires new tests well beyond browser smoke (gate integrity, feed non-pooling, byte-identity, fingerprint-frozen, no-hand-promotion) — the "touches data model / requires new tests beyond browser smoke" trigger; every prior build iteration was full and each surfaced a real pre-ship issue. Per the assumption ledger (iter-4), J-04's **passing core is the keyless run** over the committed `datasets_j03/` fixture — an all-`insufficient_sample` report is a valid outcome; the credentialed ≥10-window enrichment is an operator-gated carry parallel to J-03, not a blocker.

**Lessons carried in (from `lessons.md`):**
- *(iter-1, applies to J-04 edge-report cells)* Ship a realistic **MULTI-TIMEFRAME** fixture for anything that aggregates/scores across timeframes, plus a guard that bites under intraday density — a daily-only fixture hid J-01's ranking CRITICAL. `structure_tape_map` arms on multi-timeframe-scored tradable-map bands, so its arming/aggregation must be exercised under multi-timeframe density, never daily-only.
- *(iter-3, applies explicitly to "J-04's credentialed edge-report run")* A credentialed / operator-gated headline is not durable until PERSISTED, re-openable artifacts + a clean native test PASS + the named pinned-case demonstration ALL exist — never a handoff narration or a QA "documents the outcome" check. This iteration therefore scopes J-04's passing target to the keyless fixture run and treats the credentialed enrichment as a carry, not a claimed headline.
- *(iter-2, general pattern)* A headline verified only on committed fixtures can hide a boundary case a live-store run exposes — the credentialed full-store run may surface cells the single fixture window cannot; verify recency-boundary behaviour on the populated store when creds are present, don't extrapolate from the fixture.

## IN SCOPE

### Backend
- [ ] Register `structure_tape_map` as a NEW config-owned strategy in `apps/backend/app/config.py`: add `STRATEGY_TAPE_MAP_ID = "structure_tape_map"` and extend `_STRATEGY_IDS_IN_ORDER` to `(STRATEGY_V1_ID, STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID)` using the identical "id constant + Config-owned `strategy_definition` method" pattern already used for `v1`/`structure_tape`. Reuse the existing `structure_tape_*` config params (proximity band, class-scaled stops/rewards/size, the `rejection`/`breakthrough` state mapping) — introduce no magic number; any new constant is pre-registered and added to the `config_fingerprint` **exclusion set** so the fingerprint stays `4d665603569b9dbf`.
- [ ] Add an **additive** arming branch to the backtest runner (`apps/backend/app/research/backtests.py`): dispatch `structure_tape_map` beside the existing `if strategy["strategy_id"] == STRATEGY_TAPE_ID` branch, reusing the same `structure_tape` entry/exit archetype (`_structure_tape_reading` mapping, class-scaled stops/rewards/size) but **armed on tradable-map bands** (band proximity) instead of raw classified levels — the inherited band class drives the existing class-scaled math. `v1` and `structure_tape` code paths and outputs stay byte-identical on identical inputs.
- [ ] Read the tradable-map bands **verbatim** from the canonical `tradability.py` / `GET /research/tradability` value (as-of prior-session close, morning-markup) to arm `structure_tape_map` — never re-detect levels or recompute bands in the runner.
- [ ] Extend the existing era-3 `apps/backend/app/research/edge_report.py` **additively** (NEVER fork a second edge computation): reuse the one `BacktestJobManager.create + run_sync` path and the verbatim `aggregates` read to run all three strategies over each recorded event dataset, then aggregate into per **strategy × class × side × reaction** cells — train cells and hold-out rows kept separate; each cell carries n, R stats, and $ with the full register; cells with n < `pnl_min_sample_size` labelled `insufficient_sample`; a null-baseline comparison; a ranked list of surviving train cells with their hold-out status. The era-3 champion-only CLI (`python -m app.research.edge_report`) behavior stays byte-identical.
- [ ] Add the owned endpoint `GET /research/edge-report` in `apps/backend/app/research/routes.py` serving the aggregated cells verbatim from `edge_report.py` (the single computing owner).
- [ ] Add the read-only MCP proxy `edge_report` in `apps/backend/app/mcp/__init__.py` — one `_TOOL_PATHS` entry `"edge_report": "/research/edge-report"` + one `types.Tool(...)` registration, byte-identical mirror through the existing `get_endpoint` allowlist; no second computation, nothing that mutates state.
- [ ] Keep the edge-report hot path off the ~4m43s full-panel `compute_setups` scan (audit B2): aggregate over the recorded-dataset registry / an already-persisted scan result, not a live full-panel rescan per request.

### Frontend (if applicable)
- N/A — backend-only iteration (`Frontend Present: no`). The `/structure` **Edge Report** section that renders `GET /research/edge-report`, the Case Studies browser, and the map-default declutter are **J-05** (next iteration); the cockpit chip is **J-06**.

### New user-facing capability
None visible in the UI this iteration. A new canonical read surface — `GET /research/edge-report` (REST + MCP `edge_report`) — becomes available for J-05 to render. The product gains its first honest 3-way profit comparison under the existing era-3/4 gates.

### New information displayed
No new UI-displayed value this iteration (backend-only). The edge-report cells become **available** at their canonical endpoint; they are first rendered on `/structure` in J-05.

### New user actions
None (no UI change this iteration).

### UI surface changes
None. `/structure` and the cockpit are untouched this iteration; the Edge Report **section** is J-05.

### Product surface delta
The measurement backend that answers "what actually profits, under the existing gates" exists and is queryable (REST + MCP). No visible surface changes until J-05 renders it.

### Blueprint conformance
No new surface and no nav change. The edge report's canonical home is already in the blueprint Information Architecture (`/structure` → **Edge Report** section, under Structure) — realized in the UI at J-05. No `blueprint.reapproval-requested` is written (nav skeleton unchanged).

### Data-contract additions
**None new.** Both canonical values this iteration realizes are ALREADY registered rows in `blueprint.md` from baseline:
- **Edge-report cells** (strategy × class × side × reaction; n, R stats, $ with full register, null baseline) — computed by `app/research/edge_report.py`, served by `GET /research/edge-report`. The blueprint row already notes the era-3 champion-only CLI is extended additively to serve the 3-way endpoint via the one `BacktestJobManager` path.
- **`structure_tape_map` definition + chip rejection/breakthrough state mapping** — config-owned (`app/config.py`, exposed via `app/research/strategies.py`), served by `GET /research/strategies`.

This iteration reads existing Data-Contract values **verbatim** from their single owners and introduces no second computation or second endpoint for any of them: tradable-map bands (`GET /research/tradability`), recorded tick datasets (`DatasetStore` via the committed `datasets_j03/` fixture), backtest aggregates (the one `BacktestJobManager` path), champion pointer (`store.get_champion_pointer()`).

## OUT OF SCOPE

- J-05 `/structure` UI (Edge Report section render, Case Studies browser, map-default declutter + raw-levels toggle) — next iteration.
- J-06 cockpit band overlay + confluence chip.
- The credentialed **≥10-window / ≥5-symbol** recorded-data enrichment (richer n≥5 cells) — operator-Alpaca-credential-gated; carried parallel to J-03. J-04's passing core is keyless over the committed `datasets_j03/` fixture (an all-`insufficient_sample` report is a valid outcome).
- Any mutation of frozen foundations: `v1`, `default`, `structure_tape`, `levels.py` (+ its 5 bps / 20 bps params), the tape engine, the JSON `BarStore`, the Alpaca adapter — all stay byte-identical.
- Any champion hand-promotion or sweep-gate change. The champion pointer stays untouched unless the EXISTING sweep gate independently promotes on hold-out (not exercised here).
- Era-6 "Referee" statistical machinery (bootstrap CIs, multiple-testing control) — deferred by the goal.
- The audit-B1 setups recency-boundary reaction-label fix — carried to J-05 (which first RENDERS setups events); `setups.py` horizon/boundary logic is not touched here.

## DEFINITION OF DONE

- [ ] `GET /research/edge-report` returns a 3-way (`v1` / `structure_tape` / `structure_tape_map`) report over the committed `apps/backend/tests/fixtures/datasets_j03/` window; an integration test asserts the exact cell structure (per strategy × class × side × reaction).
- [ ] `structure_tape_map` is registered in `Config.strategy_registry` beside `v1`/`structure_tape`; a test asserts `_STRATEGY_IDS_IN_ORDER == (v1, structure_tape, structure_tape_map)` and that `Config.strategy_definition("structure_tape_map")` returns the config-owned definition; an unknown strategy id is still refused (422).
- [ ] `config_fingerprint` recomputes to `4d665603569b9dbf` (new `structure_tape_map` config in the exclusion set) — asserted by the existing fingerprint equivalence test.
- [ ] `v1`, `default`, and `structure_tape` produce byte-identical outputs on identical inputs — asserted by the existing engine/strategy equivalence tests (frozen-foundation guard); the era-3 champion-only CLI `python -m app.research.edge_report` output is byte-identical to before.
- [ ] Every `$` in the report carries R, n, fee/slippage assumptions, basis, null baseline, and the verbatim register string `simulated — assumed fees/slippage — not indicative of live results` — asserted by a report-shape test.
- [ ] Train and hold-out are never pooled; feeds are never pooled — asserted by dedicated guard tests (train/hold-out cells are separate sections; a two-feed input never merges into one cell).
- [ ] Each cell has n≥5 or is labelled `insufficient_sample` — asserted by a test; the keyless single-fixture run is expected all-`insufficient_sample` (a valid, publishable outcome).
- [ ] The champion pointer is unchanged after any edge-report run — asserted by a test (no `_promote`/ledger-append path in the 3-way extension).
- [ ] The MCP `edge_report` proxy returns JSON byte-identical to `GET /research/edge-report` — asserted by a byte-identity proxy test; MCP surface stays read-only.
- [ ] Full backend suite passes; no regressions. Required-still-passing journeys J-01, J-02, J-03 (keyless substrate), J-07 re-verified green (frozen files absent from the diff; fingerprint frozen).
- [ ] No anti-goal violation introduced — deterministic scan-report CLEAN; coherence verdict `COHERENCE-PASS`; no Alpaca credential in any file, log, or artifact.
- [ ] Dev handoff written at `docs/handoffs/goal-tradable_wall-iter-4-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** none this iteration (`Frontend Present: no`; J-04 is not browser-verifiable — J-05 renders the Edge Report section). Do not skip silently — the reason is: no UI surface changes in J-04.
- **Unit/integration (backend, keyless):**
  - `structure_tape_map` registration + `strategy_definition` + registry order; unknown-id refusal (422).
  - `structure_tape_map` arming path in `backtests.py` (band-proximity arming on tradable-map bands, class-scaled stops/rewards/size via the reused `structure_tape` archetype) exercised over a realistic **MULTI-TIMEFRAME** fixture — never daily-only (iter-1 lesson) — with a guard that bites under intraday density.
  - `edge_report.py` 3-way aggregation over the committed `datasets_j03/` window: per strategy × class × side × reaction cells; full register on every $; null baseline present; train/hold-out kept separate; ranked surviving-train list with hold-out status.
  - Gate-integrity guards: n≥5-or-`insufficient_sample` per cell; **no feed pooling** (two-feed input never merged into one cell); **no train/hold-out pooling**; no minimum-n / split-rule weakening.
  - Byte-identity / frozen-foundation guards: `config_fingerprint` == `4d665603569b9dbf`; `v1`/`default`/`structure_tape` unchanged; era-3 champion-only CLI unchanged; frozen `levels.py`/`BarStore`/engine/Alpaca absent from the diff.
  - No-hand-promotion guard: champion pointer unchanged after an edge-report run.
  - MCP `edge_report` proxy byte-identity vs the REST GET.
- **Error cases:** unknown `strategy_id` refused (422, not silently defaulted); a cell with n < `pnl_min_sample_size` labelled `insufficient_sample` (never dropped or fabricated); a two-feed dataset set never pooled into one cell; a dataset failing integrity verification aborts with `EdgeReportError` before anything is written (existing discipline preserved).

## NOTES

- **Evaluator drove this scope.** The iter-3 recommendation names J-04 at full depth with four watch-items, all reflected above: (1) EXTEND era-3 `edge_report.py` additively — never fork; (2) no-pooling-across-feeds becomes actively load-bearing at the report; (3) champion moves only via the existing sweep gate on hold-out — never hand-promote `structure_tape_map`, keep `config_fingerprint` `4d665603569b9dbf`; (4) keep the ~4m43s full-panel `compute_setups` scan (audit B2) off the edge-report hot path.
- **Credential-gate honesty (iter-3 lesson, applies-to J-04 explicitly).** Do not frame the credentialed ≥10-window enrichment as "MET" via handoff narration or a QA "documents the outcome" check. J-04's passing target is the keyless fixture run; the credentialed full run — persisted, re-openable datasets + a clean native test PASS — is an operator-gated carry the evaluator scores separately (mirrors J-03 partial). See assumption ledger iter-4 for the reading this iteration builds on.
- **Required-still-passing rationale.** J-01 (tradable-map bands consumed by `structure_tape_map` arming), J-02 (setups registry / event pool the report aggregates over), J-03 (the committed `datasets_j03/` recorded-window fixture + `DatasetStore.replay` the report backtests over — keyless substrate only), J-07 (foundation sentinel: `config_fingerprint`, frozen strategies byte-identical, champion pointer untouched) — every one shares a Data-Contract value with this iteration's work; together they are the full non-failing set, so replay re-verifies the whole built surface.
- **Blueprint.** No edit — both canonical values are pre-registered rows; the edge_report row already anticipates the additive 3-way extension. No nav change ⇒ no `blueprint.reapproval-requested`.
