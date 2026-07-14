# goal-tradable_wall-iter-4 Execution Plan

## What to Build

Deliver the honest 3-way edge report (J-04) — extend the era-3 measurement stack additively so
`v1`, the frozen `structure_tape`, and a NEW registered `structure_tape_map` can be compared, over
recorded event-window datasets, in per **strategy × class × side × reaction** cells.

- Register `structure_tape_map` as a new config-owned strategy (`config.py`), beside frozen
  `v1`/`structure_tape` — reusing the existing `structure_tape_*` entry/exit/size fields verbatim,
  introducing no new magic number.
- Add an additive arming branch to the backtest runner (`backtests.py`) so `structure_tape_map`
  arms on **tradable-map bands** (`tradability.compute_tradability`) instead of raw classified
  levels (`levels.compute_levels`) — same tape-confirmation + class-scaled exit/size math as
  `structure_tape`, reused, not re-derived.
- Extend the existing era-3 `edge_report.py` **additively** (never fork a second edge computation):
  a NEW function that runs all three strategies over each recorded event-window dataset and
  aggregates into per strategy × class × side × reaction cells (n≥5 or `insufficient_sample`,
  train/hold-out never pooled, feeds never pooled, null baseline, full PnL register). The existing
  champion-only `run_edge_report()` / CLI (`python -m app.research.edge_report`) stays untouched
  and byte-identical.
- Add the owned endpoint `GET /research/edge-report` (`routes.py`) and the read-only MCP proxy
  `edge_report` (`mcp/__init__.py`).
- Full backend test coverage for the above, including gate-integrity and frozen-foundation guards.
- Dev handoff at `docs/handoffs/goal-tradable_wall-iter-4-dev.md`.

**No UI work this iteration** — `/structure`'s Edge Report section, Case Studies browser, and
map-default declutter are J-05; the cockpit chip is J-06. This iteration only makes the canonical
value **readable** (REST + MCP) for J-05 to render next.

## Agents Required

- developer: yes -- implement all of "What to Build" above: `config.py` registration,
  `backtests.py` additive arming branch, `edge_report.py` additive 3-way extension, `routes.py`
  endpoint, `mcp/__init__.py` proxy, and the full test suite (see Files to Create/Modify + Key Test
  Scenarios). Backend-only; TDD per `.claude/core.md`.
- backend-data: yes -- entirety of this iteration is backend/research-data-layer work (strategy
  registry, backtest runner, aggregation module, REST + MCP surface).
- frontend-ux: no -- no frontend file touched this iteration; the canonical endpoint is consumed
  by J-05, not this iteration.

## Frontend Present
no

Frontend Present: no

(Matches the phase spec's own Goal Mode Metadata: `**Frontend Present:** no`. This is a backend-only
new READ endpoint with zero UI surface change — no page, panel, or control renders it yet — so no
Chrome MCP browser check is required or possible this iteration.)

## Files to Create/Modify

- `apps/backend/app/config.py` -- MODIFY: add `STRATEGY_TAPE_MAP_ID = "structure_tape_map"`
  (module-level constant, beside `STRATEGY_V1_ID`/`STRATEGY_TAPE_ID` at ~line 22-29); extend
  `_STRATEGY_IDS_IN_ORDER` (line 57) to `(STRATEGY_V1_ID, STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID)`;
  add a `structure_tape_map` branch to `strategy_definition()` (~line 1441-1554, evaluated before
  the `STRATEGY_V1_ID` fallback, the identical pattern the `STRATEGY_TAPE_ID` branch already uses)
  that reuses the EXISTING `structure_tape_proximity_band_bps` /
  `structure_tape_rejection_state_by_direction` / `structure_tape_breakthrough_state_by_direction`
  / `structure_tape_stop_bps_by_class` / `structure_tape_reward_r_multiple_by_class` /
  `structure_tape_size_multiple_by_class` fields verbatim. **Verified finding: these six fields are
  ALREADY in the `config_fingerprint` exclusion set** (lines 1840-1845, with the rationale at
  1825-1839 explaining the fingerprint is scoped ONLY to the frozen `default`/`v1` threshold set —
  any additive strategy's own config is out of scope by construction). Since `structure_tape_map`
  introduces no new `Config` dataclass field, `config_fingerprint` is expected to stay
  `4d665603569b9dbf` **trivially, with no new exclusion-set entry required** — confirm this by
  direct computation rather than assuming new fields must be added and excluded. (`STRATEGY_TAPE_MAP_ID`
  / `_STRATEGY_IDS_IN_ORDER` are module-level constants outside `Config`, so `asdict(self)` never
  sees them regardless.) If the arming implementation genuinely needs one new tunable, follow the
  `tradability_*`/`setups_*`/`recording_*` precedent at ~line 1686-1722 exactly (namespace it
  `structure_tape_map_*`, document rationale, add to the exclusion set) — but reuse-only is the
  spec's stated default.
- `apps/backend/app/research/backtests.py` -- MODIFY: add an additive dispatch branch in
  `_strategy_trades` (~line 494, beside `if strategy["strategy_id"] == STRATEGY_TAPE_ID`) for
  `STRATEGY_TAPE_MAP_ID`, mirroring `_structure_tape_trades`/`_structure_tape_arm` (~line 542-644)
  but sourcing arming candidates from `compute_tradability(bar_store, symbol, as_of_epoch, config)`
  bands instead of `compute_levels(...)` confluence zones — same `_structure_tape_reading`
  tape-confirmation check, same class-scaled stop/reward/size math, same one-open-trade/exit/fee/
  slippage code paths (reused, not duplicated). `v1` and `structure_tape`'s own branches and every
  line below them stay byte-identical (equivalence-tested).
- `apps/backend/app/research/edge_report.py` -- MODIFY, additive only: `run_edge_report`, `main`,
  `_render_report`, and every existing helper stay untouched (the era-3 champion-only CLI's output
  stays byte-identical). Add a NEW function (e.g. `run_strategy_comparison_report`) that:
  1. Reuses the ONE `BacktestJobManager.create` + `run_sync` path and the verbatim `aggregates`
     read (the existing `_run_backtest`/`_measurement` helpers, or twins of them) — never a second
     R/$/edge computation.
  2. For each recorded event-window dataset, resolves its owning `compute_setups` event (class,
     side, reaction) — reuse or adapt `setups.py`'s `_matching_dataset`-style symbol + `touch_ts`
     window-containment join (datasets do not carry class/side/reaction themselves; only events
     do). **Architecture constraint (explicit DoD/audit carry-item, do not violate):** do NOT call
     the full ~4m43s `compute_setups` panel scan on every `GET /research/edge-report` request — no
     caching of that scan exists yet, so the developer must choose a bounded approach (e.g. compute
     the event set once per report run / module-level memoization / scope the join to only the
     datasets actually present in the registry, which is small) rather than a live full-panel
     rescan per request.
  3. Runs `v1` / `structure_tape` / `structure_tape_map` per dataset, buckets each into cells keyed
     by `(strategy_id, band_class, band_side, reaction)`, train and hold-out kept in separate
     sections (never pooled), feeds never pooled into one cell.
  4. Each cell carries `n`, R stats, `$` with the full register (reuse `backtests.REGISTER =
     "simulated — assumed fees/slippage — not indicative of live results"`, never restate the
     string); `n < config.pnl_min_sample_size` (5) → `insufficient_sample`; a null-baseline
     comparison per cell; a ranked list of surviving train cells with hold-out status.
  5. An all-`insufficient_sample` report (expected on the single-fixture keyless run) is a valid,
     fully-written outcome — never an error.
- `apps/backend/app/research/routes.py` -- MODIFY: add `GET /research/edge-report` near the
  existing `/tradability` (~1812), `/setups` (~1850-1908), `/backtests` (~1922-2009), `/strategies`
  (~2055) routes, wired through the existing `get_dataset_store`/`get_bar_store`/`get_registry`
  `Depends` seams, serving the new `edge_report.py` function's output verbatim.
- `apps/backend/app/mcp/__init__.py` -- MODIFY: the codebase's actual dict is named
  `_STATIC_PATHS` (NOT `_TOOL_PATHS` as the phase spec's prose names it — a naming mismatch to be
  aware of, not a blocker). Add `"edge_report": "/research/edge-report"` to `_STATIC_PATHS`
  (~line 85-103, the `datasets`/`bars`/`setups` no-required-param precedent — `edge-report` takes
  no query params) + one new `types.Tool(name="edge_report", ...)` entry in the `TOOLS` tuple
  (~line 137-314), following the `setups` tool's docstring style.
- `apps/backend/tests/test_backtests.py` -- MODIFY/ADD: `structure_tape_map` registration test
  (`_STRATEGY_IDS_IN_ORDER == (v1, structure_tape, structure_tape_map)`, `strategy_definition`
  returns the reused config verbatim, unknown id still returns `None`/422 at the route);
  `structure_tape_map` arming test exercised over a **MULTI-TIMEFRAME** fixture — never
  daily-only (iter-1 lesson: a daily-only fixture previously hid a real ranking bug) — with a guard
  that the arming path reads `compute_tradability`, not `compute_levels` (a static/behavioral guard
  in the `test_setups_join_reuses_dataset_store_replay_never_a_second_tape_engine` idiom); `v1`/
  `structure_tape` byte-identical-output regression test (same inputs, before/after this diff).
- `apps/backend/tests/test_config.py` (or wherever the strategy-registry/fingerprint tests
  currently live — follow existing file, don't create a new one) -- ADD: fingerprint-stability
  test (`config_fingerprint() == "4d665603569b9dbf"` after registering `structure_tape_map`) +
  the paired real-threshold counter-test (perturbing a genuinely fingerprinted field still moves
  it) mirroring the `structure_tape`/J-05 precedent at config.py:1825-1839.
- `apps/backend/tests/test_edge_report.py` -- MODIFY/ADD (or a new `test_edge_report_api.py` for
  route-level tests, following the `test_backtests.py`/`test_backtests_api.py` and
  `test_setups.py`/`test_setups_api.py` split precedent — developer's choice, stay consistent):
  3-way cell-structure test over the committed `apps/backend/tests/fixtures/datasets_j03/` window
  (exact cell shape: strategy × class × side × reaction); full-register-on-every-`$` test;
  null-baseline-present test; train/hold-out-never-pooled guard; no-feed-pooling guard (a two-feed
  input never merges into one cell); n≥5-or-`insufficient_sample` guard (the single-fixture keyless
  run is expected all-`insufficient_sample` — assert that explicitly as a valid outcome, not an
  error); champion-pointer-unchanged-after-run guard (no `_promote`/ledger-append path reachable
  from the new function); era-3 CLI (`main()`/`run_edge_report`) byte-identical-output regression
  test; unknown `strategy_id` still refused 422 (not silently defaulted).
- `apps/backend/tests/test_mcp_server.py` -- ADD: `edge_report` proxy byte-identity test (MCP tool
  response == `GET /research/edge-report` response, byte-for-byte) + the tool's presence in
  `list_tools()`.
- `docs/handoffs/goal-tradable_wall-iter-4-dev.md` -- NEW: dev handoff (What Was Built, Files
  Changed, Tests Run with exact pass/fail/skip counts, Known Issues, Suggested Next Phase).

## UI Evolution
N/A — `Frontend Present: no`. No page, panel, control, or navigation changes this iteration. The
new `GET /research/edge-report` value becomes available for J-05 to render next.

## Visual Requirements
N/A — no UI work this iteration.

## Key Test Scenarios

- `structure_tape_map` is registered beside `v1`/`structure_tape`; registry order and
  `strategy_definition("structure_tape_map")` return the reused config verbatim; an unknown
  strategy id is still refused 422 (never silently defaulted).
- `config_fingerprint` recomputes to `4d665603569b9dbf` after registering `structure_tape_map`
  (verify by direct computation whether this is trivial — no new `Config` field — or requires a new
  exclusion-set entry; either way the pinned value must hold).
- `v1` and `structure_tape` produce byte-identical backtest outputs on identical inputs before and
  after this diff (frozen-foundation regression guard); the era-3 champion-only CLI
  (`python -m app.research.edge_report --out <path>`) output is byte-identical to before.
- `structure_tape_map` arms on tradable-map bands (not raw levels/zones) under a genuinely
  multi-timeframe fixture, with a static/behavioral guard proving it reads `compute_tradability`
  and never `compute_levels` for arming.
- `GET /research/edge-report` returns a 3-way report (strategy × class × side × reaction cells)
  over the committed `datasets_j03/` fixture; the keyless single-fixture run is expected
  all-`insufficient_sample` (n<5 per cell) — asserted as a valid, fully-written, non-error outcome.
- Every `$` in the report carries R, n, fee/slippage assumptions, basis, null baseline, and the
  exact register string `simulated — assumed fees/slippage — not indicative of live results`.
- Train and hold-out are never pooled (separate sections); two different `feed` values never merge
  into one cell.
- The champion pointer is byte-unchanged after running the new report function (no promotion path
  reachable from it).
- The MCP `edge_report` tool's response is byte-identical to `GET /research/edge-report`; the MCP
  surface stays read-only (no new tool issues anything but GET).
- `GET /research/edge-report` does not trigger a live ~4m43s full-panel `compute_setups` rescan on
  a normal request (hot-path guard, per the audit B2 carry-item).
- Full backend suite passes with zero regressions (expect roughly 1300+ collected, 0 failed, 0
  errors; skip count unchanged aside from any new `@pytest.mark.integration` tests, honestly
  skipped without `TAPEOLOGY_LIVE_INTEGRATION=1`); required-still-passing journeys J-01
  (`tradability.py`/`GET /research/tradability`), J-02 (`setups.py`/`GET /research/setups`), J-03
  keyless substrate (`enrich_with_tape_timeline` + the `datasets_j03/` fixture join), and J-07
  (fingerprint, frozen strategies, champion pointer, BarStore, Alpaca adapter all byte-identical)
  are all re-verified green by this same full-suite run — no separate action needed beyond running
  it.
- No Alpaca credential literal appears in any file, log, test artifact, or report this iteration
  touches (this iteration is fully keyless; no recording occurs).

## Out of Scope (per phase spec — do not build)

- `/structure` UI: Edge Report section render, Case Studies browser, map-default declutter + raw
  toggle — J-05.
- Cockpit band overlay + confluence chip — J-06.
- The credentialed ≥10-window/≥5-symbol recorded-data enrichment (richer non-`insufficient_sample`
  cells) — operator-gated, carried parallel to J-03; this iteration's passing core is the keyless
  fixture run only.
- Any mutation of frozen foundations: `v1`, `default`, `structure_tape`, `levels.py`, the tape
  engine, the JSON `BarStore`, the Alpaca adapter.
- Any champion hand-promotion or sweep-gate change.
- Era-6 "Referee" statistical machinery.
- The audit-B1 setups recency-boundary reaction-label fix (carried to J-05).

## Notes / Assumptions

- This plan is built directly from the current codebase state (not just the phase spec prose): I
  read `edge_report.py`, `config.py` (strategy registry + fingerprint exclusion set),
  `backtests.py` (the `structure_tape` arming dispatch), `routes.py` (the `/tradability`/`/setups`/
  `/backtests`/`/strategies` route precedents), and `mcp/__init__.py` (`_STATIC_PATHS` + `TOOLS`)
  directly, plus the iter-3 dev handoff and audit (PASS_WITH_GAPS; the credentialed ≥10-window
  headline is real but ephemeral — do not assume those 15 datasets persist; only the committed
  `datasets_j03/` fixture and the 7 pre-existing era-3 `.data/datasets/` fixtures are guaranteed
  present).
- The phase spec's DoD phrasing "(new `structure_tape_map` config in the exclusion set)" is the
  decomposer's anticipated mechanism; my direct code read shows the six reused `structure_tape_*`
  fields are ALREADY excluded, so no new field/exclusion work may be needed at all — flagged above,
  not prescribed, so the developer verifies rather than assumes.
- The exact test-file split (extend `test_edge_report.py` only vs. also adding
  `test_edge_report_api.py`) is left to the developer, following the codebase's existing
  module-tests/route-tests split convention (`test_backtests.py`+`test_backtests_api.py`,
  `test_setups.py`+`test_setups_api.py`, `test_tradability.py`+`test_tradability_api.py`).
- Environment: before running any test/build command, `export TMPDIR=/tmp/iad.goal-tradable_wall-iter-4.2865738 TMP=/tmp/iad.goal-tradable_wall-iter-4.2865738 TEMP=/tmp/iad.goal-tradable_wall-iter-4.2865738` (this pipeline run isolates temp files).
- No scope creep found: the phase spec is tightly scoped to J-04 and matches `docs/goal.md`'s Era
  5B vision (capability 6, "the edge report") and Success Criterion 5 exactly; nothing in the spec
  reaches beyond what goal.md authorizes for this iteration.
