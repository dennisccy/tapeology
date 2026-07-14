# goal-tradable_wall-iter-4 Dev Handoff

**Phase:** goal-tradable_wall-iter-4
**Date:** 2026-07-14
**Agent:** developer
**Status:** complete

## What Was Built

J-04 — the honest 3-way edge report (`v1` vs the frozen `structure_tape` vs a new registered
`structure_tape_map`), backend-only, keyless.

- **`structure_tape_map` strategy registration** (`app/config.py`): a new `STRATEGY_TAPE_MAP_ID =
  "structure_tape_map"` id registered beside `STRATEGY_V1_ID`/`STRATEGY_TAPE_ID` in
  `_STRATEGY_IDS_IN_ORDER`. `Config.strategy_definition` returns the **exact same grammar dict**
  as `structure_tape` (same six `structure_tape_*` config fields, verbatim — same branch, keyed by
  either id) — differing only in the `strategy_id` value itself. No new `Config` field, so
  `config_fingerprint` stays `4d665603569b9dbf` **trivially** (verified by direct computation, not
  assumed — confirmed both by an ad-hoc script and a dedicated test).
- **`structure_tape_map` arming** (`app/research/backtests.py`): a new additive dispatch branch
  (`_structure_tape_map_trades` / `_structure_tape_map_arm`) that arms on **tradable-map bands**
  (`tradability.compute_tradability`) instead of raw classified levels/zones
  (`levels.compute_levels`). Reuses the identical tape-confirmation check
  (`_structure_tape_reading`), the identical class-scaled stop/reward/size math
  (`_class_scaled_invalidation`, `_class_scaled_target`, `_arm_trade`, `_close_trade`), and the
  identical one-open-trade/exit/fee/slippage loop `structure_tape` already uses — only the
  candidate-sourcing helpers are new (`_band_nearest_price`, `_next_opposing_band_price`,
  `_structure_tape_map_side_for_reading`). A band with no inherited class (`class: null`) never
  arms (there is no A/B/C to scale against). `v1` and `structure_tape`'s own branches are
  byte-identical before/after (proven by a dedicated regression test plus the full unchanged
  suite).
- **The 3-way edge report** (`app/research/edge_report.py`, additive): a new
  `run_strategy_comparison_report(store, dataset_store, bar_store, config)` that reuses the ONE
  `BacktestJobManager.create` + `run_sync` path (never a second computation), runs all three
  strategies over every registered dataset that resolves an owning, classified `compute_setups`
  scan event, and aggregates into cells keyed by **strategy × class × side × reaction × feed**
  (feed is an additive 5th dimension — see Known Issues). The existing champion-only
  `run_edge_report()` / CLI (`python -m app.research.edge_report`) is completely untouched — same
  functions, same behavior, proven byte-identical by the full pre-existing test file still
  passing.
- **`GET /research/edge-report`** (`app/research/routes.py`): serves
  `run_strategy_comparison_report` verbatim, wired through the existing
  `get_registry`/`get_dataset_store`/`get_bar_store` seams. A dataset integrity failure maps to an
  explicit 500 (the `create_backtest` precedent) — never a partial report.
- **MCP `edge_report` proxy** (`app/mcp/__init__.py`): a byte-identical read-only GET proxy, added
  to `_STATIC_PATHS` and `TOOLS`.
- **Full test coverage** across all five changed modules (see Files Changed) — 30 new/updated
  tests, all passing.

## Files Changed

- `apps/backend/app/config.py` — registered `structure_tape_map` beside `v1`/`structure_tape`
  (constant, `_STRATEGY_IDS_IN_ORDER`, the `strategy_definition` branch merge, docstring updates).
  No new `Config` field, no new fingerprint-exclusion entry.
- `apps/backend/app/research/backtests.py` — new `structure_tape_map` dispatch branch
  (`_structure_tape_map_trades`, `_structure_tape_map_arm`), new module-level helpers
  (`_band_nearest_price`, `_next_opposing_band_price`, `_structure_tape_map_side_for_reading`),
  new import of `compute_tradability`/`SUPPORT`/`RESISTANCE`. `v1`/`structure_tape` branches
  untouched.
- `apps/backend/app/research/edge_report.py` — new `run_strategy_comparison_report` section
  (additive, appended after `run_edge_report`), extended `_run_backtest` with an optional
  `bar_store` kwarg (default `None`, backward-compatible). `run_edge_report`/`main`/`_render_report`
  untouched.
- `apps/backend/app/research/routes.py` — new `GET /research/edge-report` route + import.
- `apps/backend/app/mcp/__init__.py` — new `edge_report` static path + `Tool` registration.
- `apps/backend/tests/test_backtests.py` — registration/definition/fingerprint tests for
  `structure_tape_map`; 8 new arming tests (breakthrough/rejection, unclassified-band skip,
  side-awareness proof, no-bar-series, determinism, `compute_tradability`-not-`compute_levels`
  guard, v1/structure_tape frozen-foundation regression); updated the pre-existing registry-order
  test to 3 entries.
- `apps/backend/tests/test_strategies_api.py` — updated registry-order assertions to 3 entries;
  added a `structure_tape_map`-accepted-by-`POST /research/backtests` test (mirroring the existing
  `structure_tape` one).
- `apps/backend/tests/test_edge_report.py` — 20 new tests for `run_strategy_comparison_report`
  (keyless committed-fixture honest-empty case, synthetic scan+join real cells, feed non-pooling +
  pooling, train/holdout separation, register/null-baseline shape, champion-unchanged, hot-path
  call-count guard, determinism, gate/ranking pure-function proofs, source-scan guard); fixed one
  pre-existing test's monkeypatched stub signature to accept the new `bar_store` kwarg.
- `apps/backend/tests/test_edge_report_api.py` — **NEW**: route-level tests (empty-registry 200,
  byte-identity to the module function, integrity-failure 500, 405 on non-GET, dependency-seam
  guard).
- `apps/backend/tests/test_mcp_server.py` — added `edge_report` to `EXPECTED_TOOLS`; 2 new
  byte-identity tests (default response; after recording a real dataset).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1331 passed, 7 skipped, 0 failed, 0 errors** (1338 collected — skip count unchanged from
before this diff; no `@pytest.mark.integration` tests were added).

Targeted re-runs during development (all green): `test_backtests.py` (63/63 combined with
`test_strategies_api.py`), `test_edge_report.py` (28/28), `test_edge_report_api.py` (5/5),
`test_mcp_server.py` (28/28, real-subprocess uvicorn byte-identity suite), plus explicit
frozen-foundation re-checks (`test_observer_equivalence.py`, `test_profile_equivalence.py`,
`test_no_execution_path.py`, `test_no_credential_in_artifacts.py`, `test_tradability.py`,
`test_tradability_api.py`, `test_setups.py`, `test_setups_api.py`) — all pass.

`config_fingerprint()` confirmed `4d665603569b9dbf` by direct computation (ad-hoc script) and by a
new pinned test (`test_default_fingerprint_still_pinned_after_registering_structure_tape_map`).

**Live smoke test** (pre-handoff verification): started the real backend via
`scripts/start-backend.sh` twice — once against the operator's actual `.data/` store (see Known
Issues #5), once against isolated empty `TAPEOLOGY_DATASET_DIR`/`TAPEOLOGY_BAR_DIR`/
`TAPEOLOGY_JOURNAL_DB` — confirmed `/health` OK, `GET /research/edge-report` returns the correct
honest-empty shape in 7ms on an empty store, and `GET /research/strategies` shows the live 3-way
registry (`['v1', 'structure_tape', 'structure_tape_map']`). Both server processes were stopped
before finishing (confirmed via `ss -ltn` — no listener remains).

## Known Issues

Several genuine judgment calls were made where the phase spec/plan left room for interpretation.
Each is also documented in the code itself (module/function docstrings); flagging them here for
the reviewer/auditor:

1. **Cell key is a 5-tuple (strategy × class × side × reaction × `feed`), not the literal 4-tuple
   the DoD names.** `feed` was added as an additive dimension because "feeds are never pooled...
   in any analysis cell" (goal.md anti-goal) is only achievable if two different feeds' recordings
   never share a cell — with only strategy/class/side/reaction as the key, a mixed-feed dataset
   registry would either have to silently merge feeds (a rail violation) or be rejected outright
   (over-strict, and not asked for). Tested explicitly
   (`test_two_same_feed_datasets_pool_and_a_different_feed_never_pools`).

2. **Cells are materialized lazily** (only for `(strategy, class, side, reaction, feed)`
   combinations that a real dataset+event pair actually produces), not pre-registered as an
   exhaustive skeleton the way `_aggregate_by_class`'s three fixed classes are. Reasoning: `feed`
   is data-driven and unbounded (unlike the fixed A/B/C enum), so there is no fixed "every
   combination" list to pre-populate honestly. Consequence: **the literal committed
   `datasets_j03/` fixture (symbol `PG`, not a config-owned panel symbol) produces `cells: []`
   under the real, shipped 12-symbol panel** — a valid, degenerate case of "all cells
   insufficient_sample" (vacuously — zero cells to violate the gate), not a populated-but-labeled
   set of cells. I proved the **non-degenerate** case (real, populated, all-`insufficient_sample`
   cells) separately, using the committed `datasets_j03/` fixture's own PG tick content combined
   with `test_setups.py`'s existing synthetic scan fixture under a test-local panel override —
   see `test_synthetic_scan_join_produces_real_cells_all_insufficient_sample` in
   `test_edge_report.py`. The shipped default panel (`AAPL MSFT NVDA TSLA AMZN GOOGL META AMD NFLX
   SPY QQQ JPM`) is never touched by any test.

3. **`structure_tape_map`'s arming is side-aware** (only tests bands on the semantically correct
   side of a reading — a rejection defends the side it sits at, a breakthrough moves through the
   opposite side), whereas `structure_tape`'s own zone-based arming has no side concept at all
   (a raw confluence zone carries no side field, so it tests every zone regardless of position).
   This is a genuine, deliberate design decision (documented in
   `_structure_tape_map_side_for_reading`'s own docstring): without it, e.g. a "breakthrough
   short" premise could arm against a distant RESISTANCE band merely because price sits
   numerically below it — verified this actually happens on the shared confluence fixture (a
   class-C resistance band at 300 "qualifies" for a short at price ~100 under a naive, non-side-
   aware test) before deciding to add the filter. Proven both ways: side-aware exclusion
   (`test_structure_tape_map_side_aware_reading_never_arms_on_the_wrong_side_band`) contrasted
   against `structure_tape`'s own un-filtered arm on the identical fixture/price as a positive
   control in the same test.

4. **Pooled-cell trades are ordered by reconstructed real UTC entry time**
   (`dataset["epoch_anchor"] + trade["entry"]["logical_ts"]`, the identical reconstruction
   `setups.py`'s tape-timeline join already uses) before calling the shared `_aggregate()` — so a
   cell's `win_rate`/`max_drawdown_r` reflect a genuine chronological sequence across
   *independently recorded* datasets, never scan-order or dataset-id happenstance. This is a small
   but deliberate addition beyond the minimum needed to pass tests, justified because
   `max_drawdown_r` is explicitly "peak-to-trough IN TRADE ORDER" and pooling multiple datasets'
   trades is the report's whole point at credentialed scale.

5. **`GET /research/edge-report` can take several minutes against a fully populated real
   store — this is pre-existing, not a regression.** The implementation satisfies the literal
   hot-path guard (`compute_setups` is called **at most once per report run**, never per-dataset —
   proven by `test_compute_setups_runs_at_most_once_per_report_call`, and the empty-registry case
   skips it entirely). But `compute_setups` **itself** is the same O(12 symbols × every stored
   session) full-panel scan the J-02/audit-B2 finding already named as ~4m43s on a populated
   store — building a caching/memoization layer for it is explicitly out of scope for this
   iteration (the plan's own notes say "no caching of that scan exists yet" and list "once per
   report run" as an *acceptable* bounded approach, not a promise it would be fast). I confirmed
   this live: the operator's actual `.data/datasets/` (7 pre-existing PG datasets) plus a fully
   fetched `.data/bars/` panel (47 real bar-series files) made a real `GET /research/edge-report`
   call hang past 2 minutes before I killed it; against an isolated empty store the identical
   endpoint responds in 7ms. Flagging this explicitly so it isn't mistaken for a wiring bug, and as
   a good candidate for a future iteration's caching work if `/structure`'s Edge Report section
   (J-05) needs a snappier read.

6. **The `datasets_j03/` fixture's symbol (`PG`) is not a panel symbol**, so it can never resolve
   an owning scan event under the real config — this was true before this iteration too (the
   fixture was committed for J-03's *tape-join* test, which only needs symbol+window containment
   against a hand-picked event, not panel membership). Nothing about this iteration made that
   truer or less true; it just means the DoD's literal-fixture cell-shape test needed a synthetic
   companion (item 2 above) to exercise non-empty cells.

**Nothing from the phase spec is incomplete.** All DEFINITION OF DONE items are met; the
Out-of-Scope list (J-05/J-06 UI, credentialed enrichment, frozen-foundation mutation, champion
hand-promotion, era-6 machinery, the audit-B1 setups fix) was respected — no file outside the
named additive surface was touched.

**Notes for J-05** (next iteration, first to render this endpoint): the response shape is
`{"register", "pnl_min_sample_size", "train": {"cells": [...]}, "holdout": {"cells": [...]},
"surviving_train_cells": [...]}`. Each cell carries
`strategy_id/band_class/band_side/reaction/feed/dataset_ids/measurement/null_baseline/
insufficient_sample`. Each `surviving_train_cells` entry carries `train_cell` (a full cell),
`holdout_cell` (a full cell or `null`), and `holdout_positive_edge` (bool, `false` when
`holdout_cell` is `null`) — no fabricated verdict on absent hold-out data.
