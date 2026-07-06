# Iteration 4 — Coherence Audit

**Iteration:** goal-tape_to_profit_support_resistence-iter-4
**Date:** 2026-07-06
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Row 40 — Strategy registry + champion pointer | OK | `apps/backend/app/config.py:1347` `Config.strategy_registry()` built entirely from `strategy_definition()` (no second id/grammar copy — confirmed only definition site repo-wide); `apps/backend/app/research/strategies.py:28-38` `strategies_projection()` reads `store.get_champion_pointer()` — the identical call `apps/backend/app/research/profiles.py:47` (`profiles_projection`) makes. Served by new `apps/backend/app/research/routes.py:1803` `GET /research/strategies` (single route definition, confirmed no duplicate) + MCP `strategies` proxy `apps/backend/app/mcp/__init__.py:216,224-232`. |
| Row 41 — `structure_tape` strategy definition | OK | New branch added directly inside the EXISTING `Config.strategy_definition()` (`config.py:129-156`, evaluated before the `v1` branch, `v1`'s own dict untouched); consumed only by the ONE existing `BacktestRunner._strategy_trades` (`apps/backend/app/research/backtests.py:352-353` dispatches to `_structure_tape_trades`) — no second backtest runner or execution path introduced. |
| Row 39 — S/R levels / confluence classes (consumed, not re-registered) | OK | `apps/backend/app/research/backtests.py:442` calls `compute_levels(bar_store, symbol, as_of_epoch, config)` — verified this is the real canonical signature (`apps/backend/app/research/levels.py:279`). Independently grepped `backtests.py` for the actual internal level-computation function names (`_swing_pivots`, `_prior_period_extremes`, `_cluster_levels`, `_grade_zone`, all confirmed as the real implementation internals of `levels.py:122/146/194/226`) — none appear in `backtests.py`. No second S/R computation path exists. |
| Per-trade "level provenance" (price/timeframe/class stamped on a `structure_tape` trade) | OK (not a new contract value) | `apps/backend/app/research/backtests.py:277-282` `_level_provenance()` merely extracts fields from the level/zone dicts `compute_levels` already returned — a re-format/stamp of canonical data onto the existing row-31 trade record, not an independent computation. Matches the iter spec's "Data-contract additions: None" claim, independently verified against `blueprint.md` rows 40-41 (already present at baseline). |
| Champion-pointer mutation (J-06 promotion) | OK — correctly untouched | Grepped `set_champion_pointer` repo-wide: only caller remains `apps/backend/app/research/pnl_scan.py:256` (pre-existing, out of scope this iteration); no new call site introduced. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /research/strategies` + MCP `strategies` | OK | Blueprint IA table (`state/blueprint.md` J-04 row) designates this journey's canonical home as machine-surface-only ("no nav home — read-only, spawned on demand"). Confirmed `git diff <snapshot>..HEAD --stat -- apps/frontend/` and `git status --porcelain -- apps/frontend/` both empty — zero frontend changes, no parallel shell, no nav file touched. Nav skeleton (Cockpit · Journal · Studies · Performance, driven by `GET /meta/ui-routes`) is unmodified. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None of substance. The iteration is unusually disciplined about single-source-of-truth: it independently ships its own coherence self-check (`apps/backend/tests/test_strategies_api.py::test_strategies_module_carries_no_second_copy_of_the_id_strings` and `apps/backend/tests/test_backtests.py::test_structure_tape_reads_levels_from_the_one_canonical_compute_levels_owner`) asserting exactly the guards this audit verified independently. No new displayed value was left unregistered; no nav change was needed or made.
