# goal-tape_to_profit_support_resistence-iter-4 Dev Handoff

**Phase:** goal-tape_to_profit_support_resistence-iter-4
**Date:** 2026-07-06
**Agent:** developer
**Status:** complete

## Note on exact field naming (for QA/reviewer alignment)

The pre-dev QA test plan (`reports/qa/goal-tape_to_profit_support_resistence-iter-4-test-plan.md`)
speculatively named some trade fields before the implementation existed (e.g. `entry_reason`,
`level_price`/`level_timeframe`/`level_class`). The actual shape, chosen to match this codebase's
existing conventions (v1's trade dict shape, `_arm_trade`/`_close_trade`):
- Each `structure_tape` trade's reading is `trade["setup_type"]` — exactly `"rejection"` or
  `"breakthrough"` (the same key v1 uses for its own setup names, e.g. `"trend_continuation"`).
- The arming level's provenance is a NESTED `trade["level"]` dict: `{"price": ..., "timeframe": ...,
  "class": ...}` — not flat `level_price`/`level_timeframe`/`level_class` keys.
- Which strategy ran is `result["strategy_id"]` at the REPORT level (present for every strategy,
  not a new per-trade field) — exactly the same key every other backtest report already carries.

## What Was Built

- **`structure_tape`, a second registered backtest strategy (additive beside the frozen `v1`).**
  `Config.strategy_definition("structure_tape")` returns a complete grammar: entries arm when
  price enters a classified support/resistance level's proximity band (rejection — fade) or moves
  beyond it (breakthrough — follow, reusing the studies' `level_break` cross technique), confirmed
  by the matching tape state (`bid_absorption`/`ask_absorption` for rejection,
  `buyer_control`/`seller_control` for breakthrough — the existing five-state vocabulary only, no
  new state). Exits, fees, slippage, and the dollars-per-R notional are IDENTICAL to `v1`'s
  (class-scaled risk/size is J-05, out of scope this iteration).
- **`Config.strategy_registry()`** — the full `[v1, structure_tape]` list in registration order,
  mirroring the existing `profile_registry()` pattern.
- **New `structure_tape`-only config fields** (all excluded from `config_fingerprint()`, so the
  frozen `default`/`v1` fingerprint stays pinned at `4d665603569b9dbf`):
  `structure_tape_proximity_band_bps` (5.0 bps, same order of magnitude as `sr_touch_tolerance_bps`),
  `structure_tape_rejection_state_by_direction` (`{"long": "bid_absorption", "short": "ask_absorption"}`),
  `structure_tape_breakthrough_state_by_direction` (`{"long": "buyer_control", "short": "seller_control"}`).
- **Backtest runner extension** (`app/research/backtests.py`) — `_strategy_trades` dispatches to a
  new `_structure_tape_trades` branch (v1's own branch/code is completely untouched). The new
  branch is the SAME one-open-trade-at-a-time interleaved pass as v1 (exits evaluated first via
  the unchanged `_exit_reason`/`_close_trade`), but arms via a NEW rule: at each flat event, the
  CURRENT tape state is checked against the rejection/breakthrough maps FIRST (a non-confirming
  tick, e.g. `unclear`, never pays for a levels computation); on a match, the row-39 canonical
  `research.levels.compute_levels` is called AS OF THAT EVENT'S OWN absolute timestamp
  (`epoch_anchor + point.timestamp` — datasets carry only a logical clock, so this is the one
  conversion back to the real UTC instant `compute_levels` expects) and every member level of
  every confluence zone is tested in the module's own deterministic order — NO second S/R
  computation exists in the runner. Each armed trade is stamped with a `"level"` key
  (`price`/`timeframe`/`class`) carrying the specific level that armed it; `v1` and null-baseline
  trades never carry this key (byte-identical to before).
- **`BacktestJobManager.start()`/`run_sync()`** now accept an optional `bar_store` kwarg (default
  `None`), threaded through to the runner exactly like the existing `dataset_store` — never baked
  into the constructor. `v1` ignores it; `structure_tape` reads it for the levels its entries arm
  against. A missing `bar_store`/`symbol`/`epoch_anchor` (or a symbol with no recorded/only-corrupt
  bar series — `compute_levels`'s own existing `no_bar_series_for_symbol` aliasing, unchanged)
  yields zero classified levels, so `structure_tape` honestly arms nothing rather than fabricating
  a partial computation.
- **New endpoint `GET /research/strategies`** — mirrors `GET /research/profiles`: serves
  `Config.strategy_registry()` plus the champion strategy id read verbatim from the SAME
  `store.get_champion_pointer()` source `profiles.py` reads (one pointer, two read views, never a
  second champion source). New module `app/research/strategies.py` (`strategies_projection`)
  mirrors `profiles.py` exactly. GET-only (no write surface — a non-GET verb is FastAPI's 405).
- **`POST /research/backtests`** now accepts `strategy_id=structure_tape` (previously 422) with NO
  route-validation change — `Config.strategy_definition` is the one registry the route already
  consults. The route now also depends on `get_bar_store()` and threads it into `jobs.start(...)`.
  The unknown-strategy 422 message now lists every registered strategy id (from
  `Config.strategy_registry()`) rather than naming only `v1`.
- **MCP `strategies` tool** — added to `_STATIC_PATHS` (`"strategies": "/research/strategies"`) and
  the advertised `TOOLS` tuple (a no-arg tool mirroring `datasets`/`bars`/`backtests`); JSON is
  byte-identical to the REST endpoint (verified live, non-empty — the registry/champion are always
  present, unlike `bars`/`levels`/`backtests` which need seeded data).
- **README.md** — one new plain-language bullet describing the strategy registry + `structure_tape`
  + the `strategies` MCP tool (the S/R-bullet half of the doc-parity rider was already done as of
  iter-3's own `readme-maintainer` pass — confirmed via `git blame`, no action needed there); the
  REST endpoint list and the MCP capability bullet were also updated to name the new endpoint/tool.

## Files Changed

- `apps/backend/app/config.py` -- `STRATEGY_TAPE_ID` constant; `_STRATEGY_IDS_IN_ORDER` tuple;
  `structure_tape_proximity_band_bps` / `structure_tape_rejection_state_by_direction` /
  `structure_tape_breakthrough_state_by_direction` fields; `strategy_definition()` extended with
  the `structure_tape` branch (v1's own branch untouched); new `strategy_registry()` method;
  3 new fields added to `config_fingerprint()`'s `excluded` set.
- `apps/backend/app/research/backtests.py` -- `_strategy_trades` dispatches to new
  `_structure_tape_trades`/`_structure_tape_arm`/`_structure_tape_reading`/`_level_provenance`;
  `_arm_trade`/`_close_trade` carry an optional `"level"` key; `run()`, `start()`, `run_sync()`
  accept an optional `bar_store` kwarg.
- `apps/backend/app/research/routes.py` -- new `GET /research/strategies` route;
  `create_backtest` depends on `get_bar_store()` and threads it through; unknown-strategy 422
  message now lists the full registry; removed the now-unused `STRATEGY_V1_ID` import.
- `apps/backend/app/research/strategies.py` -- NEW: `strategies_projection(store, config)`,
  mirroring `profiles.py`.
- `apps/backend/app/mcp/__init__.py` -- `"strategies"` added to `_STATIC_PATHS` and a new
  `types.Tool` entry in `TOOLS` (positioned after `backtests`, before `pnl_ledger`).
- `apps/backend/tests/test_backtests.py` -- `structure_tape` definition/registry tests; the four
  arming-direction tests (rejection long/short, breakthrough long/short) using the SYN-CONFLUENCE
  class-A fixture (imported from `test_levels.py`, per the plan's directive) and the canned
  `SIM-BUYER`/`SIM-SELLER`/`SIM-BIDABS`/`SIM-ASKABS` scenarios recorded under a shared, chosen
  epoch anchor; no-arm tests (no classified levels, tape unconfirmed, before the defining bars are
  visible — the no-lookahead proof); byte-identical rerun; fingerprint-exclusion tests; a
  single-source-discipline source-scan test (`compute_levels` is imported/called, no
  `_swing_pivots`/`_cluster_levels`/etc. reimplemented in the runner).
- `apps/backend/tests/test_strategies_api.py` -- NEW: `GET /research/strategies` registry order +
  champion tests (mirroring `test_profiles_api.py`), 405 no-write-surface, no-duplicate-id-literal
  source scan, `POST /research/backtests` accepting `structure_tape` end-to-end, unregistered
  strategy id still 422.
- `apps/backend/tests/test_mcp_server.py` -- `"strategies"` added to `EXPECTED_TOOLS`; a dedicated
  byte-identity test (`test_strategies_tool_byte_identical_on_a_non_empty_live_result`) — simpler
  than the `bars`/`levels`/`backtests` precedent since the registry/champion need no seeding.
- `README.md` -- new capability bullet (strategy registry + `structure_tape` + `strategies` MCP
  tool); the REST endpoint list and the MCP-tools bullet updated to name the new surface.

`apps/frontend/` is untouched — confirmed via `git diff --stat -- apps/frontend/` (empty).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest -q` (project-template's backend test
command)

Result: full backend suite green — **1128 passed, 1 skipped (the pre-existing gated live-integration
skip, unrelated to this iteration), 0 failed** (exact count via `pytest -rA`, since bare `-q` in
this pytest version omits the final summary line — noted here so the next agent isn't puzzled by
the same thing). Exactly the iter-3 baseline (1107 passed, 1 skipped) plus the 21 new tests this
iteration adds (13 in `test_backtests.py`, 7 in the new `test_strategies_api.py`, 1 in
`test_mcp_server.py`) — zero regressions. Ran the full suite three times across the session with
identical pass counts (no flakiness introduced). Also ran individually and green:
`tests/test_backtests.py` (39 tests, up from the pre-iteration 26), `tests/test_strategies_api.py`
(7 new tests), `tests/test_backtests_api.py`, `tests/test_profiles_api.py`,
`tests/test_profile_equivalence.py` (unmodified, still green — proves
`v1`/`default` stayed byte-identical), `tests/test_mcp_server.py` (23 tests, up from 22 — real
uvicorn-subprocess byte-identity coverage), `tests/test_no_execution_path.py` (unmodified, still
green with the new strategy grammar's field names).

## Known Issues

- **No dedicated "corrupt sole bar series" test for `structure_tape` specifically.** The Known
  Considerations note asked me to decide `structure_tape`'s honest behaviour when its symbol's sole
  bar series is corrupt. Decision: no new runner code is needed — `research/levels.py`'s
  `compute_levels` already aliases a corrupt sole series to `no_bar_series_for_symbol: true` (empty
  levels/confluence_zones), and `structure_tape`'s arming loop treats an empty `confluence_zones`
  list identically regardless of WHY it's empty (no series recorded vs. corrupt sole series). I
  proved the "empty confluence_zones -> zero arms" path via the simpler "no series recorded" case
  (`test_structure_tape_no_arm_when_symbol_has_no_classified_levels`) rather than duplicating a
  corrupt-file variant, since `compute_levels`'s own corrupt-file aliasing is already exhaustively
  tested in `test_levels.py` and my runner code adds no new logic for that path. Flagging this so
  the reviewer/auditor can decide if an explicit corrupt-file backtest test is wanted.
- **Class-A confluence exercised via the synthetic fixture, not the committed real PG fixture** —
  per the plan/NOTES: the committed real PG bar fixture stores only two timeframes (1h, 1d) and can
  never produce a class-A zone, so the four arming-direction tests use the `SYN-CONFLUENCE`
  synthetic fixture (imported directly from `test_levels.py`) paired with the canned
  `SIM-BUYER`/`SIM-SELLER`/`SIM-BIDABS`/`SIM-ASKABS` tape scenarios recorded under a shared, chosen
  epoch anchor (`epoch_anchor` is purely additive display metadata never read by classification, so
  this recombination changes no classified tape_state or price — verified empirically before
  writing the test assertions).
- **Performance**: `_structure_tape_arm` calls `compute_levels` (which re-reads/re-verifies every
  bar-series file from disk) on every flat event whose tape state matches a rejection/breakthrough
  reading. This is correct (no-lookahead requires an as-of-T computation, and `compute_levels` is
  the one canonical, reused owner — no second computation path) but is O(events × bar files) rather
  than cached. Acceptable for the fixture-scale datasets this era operates on (proven fast in the
  test suite); flagged here in case a future iteration backtests structure_tape over a much larger
  real bar/tape library and needs to revisit.
- No frontend work this iteration (machine surface only, per the phase spec and the J-07
  frozen-frontend guard) — confirmed no `apps/frontend/` changes.
- J-05 (class-scaled stop/reward/size) and J-06 (named-strategy comparison / hold-out promotion)
  are explicitly out of scope this iteration, per the phase spec, and were not touched — confirmed
  via grep (`class_scaled`, no `set_champion_pointer` call added, `pnl_scan.py`/`edge_report.py`
  untouched).
