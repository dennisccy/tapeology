# Iteration 5 — Coherence Audit

**Iteration:** goal-tape_to_profit_support_resistence-iter-5
**Date:** 2026-07-06
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

Iter-5 (J-05: class-scaled stop/reward/size + per-class PnL breakdown) touches exactly six files
(`README.md`, `apps/backend/app/config.py`, `apps/backend/app/research/backtests.py`, and three test
files) and zero frontend files, matching the spec's "Frontend Present: no" / "no new surfaces" claim.
Both Data Contract rows this iteration realizes (41, 42) were pre-registered at baseline; I traced
each to confirm the implementation actually kept the single-owner/single-endpoint discipline the
blueprint promises, rather than taking the spec's claim on faith.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Row 41 — `structure_tape` class-scaled stop/reward/size grammar | OK | Computed once in `Config.strategy_definition` (`apps/backend/app/config.py:1344-1362`); `v1`'s branch (evaluated/returned first) is untouched — asserted by `test_structure_tape_definition_is_config_owned_and_additive_beside_v1` (`apps/backend/tests/test_backtests.py:354-384`). Served by the pre-existing `GET /research/strategies` (`apps/backend/app/research/routes.py:1804-1809`, unchanged this iteration — `strategy_registry()` builds its list entirely from `strategy_definition`, `config.py:1400-1405`) and the unchanged MCP `strategies` tool, which passes the REST body through verbatim as raw text (`apps/backend/app/mcp/__init__.py:1-10`, not touched this iteration). No new route, no second grammar copy. |
| Row 42 — Per-class (A/B/C) PnL breakdown | OK | New `_aggregate_by_class()` helper (`apps/backend/app/research/backtests.py:308-330`) is called exactly once, inline in the SAME `BacktestJobManager.run` that already computes `aggregates` (`apps/backend/app/research/backtests.py:413-418`) — not a second computation path, a second module, or a second job manager. Served by the pre-existing `GET /research/backtests/{id}` (`apps/backend/app/research/routes.py:1729-1737`, unchanged — returns `record.payload` verbatim) and the unchanged MCP `backtests` tool (byte-identical by construction). No new endpoint created. Cross-strategy honesty confirmed by `test_v1_backtest_carries_an_honest_all_empty_per_class_breakdown` (v1 trades carry no `level` key → all three classes honestly empty, not omitted). |
| `v1` / `default` byte-identity after the shared-arithmetic split | OK | The three new config dicts (`structure_tape_stop_bps_by_class`, `structure_tape_reward_r_multiple_by_class`, `structure_tape_size_multiple_by_class`) were added to the `config_fingerprint` `excluded` set (`apps/backend/app/config.py:1636-1644`, beside the existing `structure_tape_*` exclusions). The pinned fingerprint `4d665603569b9dbf` is still asserted unchanged in `test_backtests.py:1253`, plus `test_levels.py:645`, `test_profile_equivalence.py:114`, `test_pnl_scan.py:182,255`, `test_edge_report.py:196` — none of those assertions were touched by this diff, confirming no regression on the frozen foundation. `v1`/null trades verified to carry no `level`/`target_price` key and unchanged `shares`/invalidation formula (`_arm_trade`/`_close_trade` gate on `level is not None`, `apps/backend/app/research/backtests.py:698-720,779-793`). |
| No magic numbers (stop/reward/size parameters) | OK | All three values read by name from `Config` (`config.structure_tape_stop_bps_by_class[...]` etc., `apps/backend/app/research/backtests.py:214,282,791`); asserted by `test_structure_tape_class_scaling_parameters_are_config_sourced_no_magic_numbers` (`test_backtests.py`), which greps the source for the three config-attribute references. |
| No lookahead (reward-target's "next opposing level") | OK | `_next_opposing_zone_price` is resolved from the SAME `compute_levels(...)` call already made to arm the trade at the event's own as-of timestamp (`apps/backend/app/research/backtests.py:628-651`) — never a second/future levels read. Asserted by `test_structure_tape_reward_target_exit_fires_lookahead_free`. |
| No-execution grep-guard (new sizing/exit code) | OK | `test_no_execution_path.py` gained `test_class_scaled_sizing_and_reward_target_code_carries_no_execution_vocabulary`, scanning `research/backtests.py` for the same TIER1/TIER2 broker/order/routing patterns already enforced elsewhere. |

No new displayed value/entity outside the two pre-registered rows was introduced — `_aggregate_by_class` and the class-scaled grammar fields are internal computation, not new served concepts.

## Information Architecture check

No new page/route/feature this iteration — `apps/frontend/` has zero diff (confirmed against
`git diff a51313ce...--stat`, which lists no `apps/frontend/*` path), matching the spec's "Frontend
Present: no" / "UI surface changes: None." `reports/phase-goal-tape_to_profit_support_resistence-iter-5-ui-surface-map.md`
independently confirms: "N/A — Backend-only phase... No UI surfaces affected." The two touched
Data Contract rows ride pre-existing machine-surface endpoints (`GET /research/strategies`,
`GET /research/backtests/{id}`) that the blueprint already lists as having no nav home. Nothing to
check against the nav/router components this iteration.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new route this iteration) | OK | N/A — zero frontend diff; blueprint's machine-surface rows unchanged |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None.
