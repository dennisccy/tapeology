# goal-tape_to_profit_support_resistence-iter-5 Execution Plan

## Goal alignment

Faithful realization of `docs/goal.md` **J-05** ("Class-scaled stop, reward, and simulated
size"), the next journey in the strict J-01→J-06 dependency order. No drift detected between
the phase spec and goal.md — IN SCOPE / DEFINITION OF DONE mirror J-05's steps and acceptance
almost verbatim. This is backend-only, additive-only work layered on the frozen `v1`/`default`
foundation (era 3) and the already-shipped `structure_tape` registration (iter-4, J-04). No
scope creep found; the spec's own OUT OF SCOPE list (J-06, `pnl_scan.py`/`edge_report.py`,
champion pointer, any real position/account concept) is correctly excluded and must stay excluded.

## What to Build

- Three new `structure_tape_*`-namespaced, per-class (A/B/C) `Config` fields, each with
  documented rationale and NO literal in `research/backtests.py`:
  1. per-class **stop distance** — A ≈ 1bp beyond the arming level's price; B/C wider.
  2. per-class **reward target** — an R:R multiple and/or next-opposing-level rule, config-bounded.
  3. per-class **simulated size multiple** — applied over the existing `strategy_dollars_per_r`.
- All new fields added to `config_fingerprint()`'s `excluded` set (beside the 3 existing
  `structure_tape_*` exclusions) so `default`/`v1`'s pinned fingerprint `4d665603569b9dbf` does
  not move.
- Extend ONLY the `structure_tape` branch of `Config.strategy_definition` (it returns before
  `v1`'s branch) so its grammar declares the class-scaled stop/reward/size, read by name.
- In `BacktestRunner`, gated strictly on `level is not None` (i.e. `structure_tape` trades only —
  `v1`/null trades carry no `level` key and must stay byte-identical):
  - class-scaled stop in `_arm_trade` (a NEW level-relative invalidation for `structure_tape`,
    distinct from the shared spread-based `_synthetic_invalidation` v1/null keep using), R still
    via the one shared `marks.r_basis`.
  - a NEW take-profit exit reason in `_exit_reason` (R:R toward the next opposing level), inserted
    at a documented fixed precedence, lookahead-free (next-opposing-level read comes from the SAME
    as-of `compute_levels` call already made to arm the trade — no second/future levels read).
  - class-scaled `shares` in `_close_trade` (class size multiple × `strategy_dollars_per_r`).
- Per-class PnL breakdown added to the SAME backtest report (no new endpoint, no new module): net R
  AND net $, n, per A/B/C class, computed once by the existing `_aggregate` (partitioned by
  `trade["level"]["class"]`) and served verbatim by the existing `GET /research/backtests/{id}` +
  MCP `backtests`. Sub-minimum-n class → "insufficient sample" (mirror the existing
  `analytics.py`/`pnl_ledger.py`/`edge_report.py` `insufficient_sample` precedent); a class with
  zero trades → honest empty (n=0, rates `None`), never fabricated.
- Extend `tests/test_no_execution_path.py`'s grep-guard to also cover the new sizing/exit code
  (position size = simulated notional; places/routes/transmits nothing).
- Dev handoff at `docs/handoffs/goal-tape_to_profit_support_resistence-iter-5-dev.md`.

## Agents Required

- backend-data: yes -- all of the above (this repo's single `developer` agent implements it;
  there is no separate frontend agent invocation this iteration).
- frontend-ux: no -- `apps/frontend/` MUST NOT be touched (confirm via
  `git diff --stat -- apps/frontend/` empty before handoff, exactly like iter-4).

Frontend Present: no

## Files to Create/Modify

- `apps/backend/app/config.py` -- new `structure_tape_*` class-scaling fields (stop/reward/size)
  with documented rationale near the existing block at lines ~1161-1194; extend the
  `structure_tape` return dict inside `strategy_definition` (~lines 1285-1312, BEFORE the
  `STRATEGY_V1_ID` check at line 1313 -- do not touch v1's own returned dict at lines 1315-1345);
  add every new field name to the `excluded` set beside lines 1579-1581.
- `apps/backend/app/research/backtests.py` -- `_arm_trade` (line 557: currently unconditionally
  calls `_synthetic_invalidation`; branch on `level is not None` to use the new class-scaled,
  level-relative invalidation instead, else unchanged), `_exit_reason` (line 587: add the new
  take-profit reason at a documented point in the precedence -- currently r_stop, state_flip,
  horizon), `_close_trade` (line 615: currently unconditional
  `shares = config.strategy_dollars_per_r / trade["r_basis"]`; branch on `"level" in trade` for
  the class-scaled multiple), `_structure_tape_arm` (line 481: already fetches
  `result["confluence_zones"]` via `compute_levels` at arm time -- reuse this SAME call/result to
  resolve "next opposing level", never a second `compute_levels` call), a new exit-reason constant
  in `__all__`/the `EXIT_*` block (~line 138). `_aggregate` (line 180) is reused unmodified, called
  once more per class partition (report assembly is in `run()`, ~line 282-303, beside the existing
  `"aggregates": _aggregate(trades)`).
- `apps/backend/tests/test_backtests.py` -- class-scaled stop/size assertions on the synthetic
  3-timeframe `SYN-CONFLUENCE` fixture (imported at line 65 from `test_levels.py`; **the committed
  real PG fixture only has 1h+1d and can never produce class A** -- iter-3/iter-4 lesson, do not
  repeat the mistake here) for the class-A case; per-class aggregate correctness (A/B/C partition
  sums to the strategy total); reward-target exit fires and stays lookahead-free; sub-minimum-n
  "insufficient sample" label; zero-trade class honest-empty; `v1`/null byte-identity re-verified
  AFTER the shared-arithmetic split; a "no magic number" source-scan test (this repo's established
  pattern, e.g. in `test_levels.py`/`test_pnl_scan.py`/`test_profile_equivalence.py`).
- `apps/backend/tests/test_no_execution_path.py` -- extend to scan the new sizing/exit code paths.
- `apps/backend/tests/test_strategies_api.py` and/or `test_backtests_api.py` -- confirm
  `GET /research/strategies` echoes the new class-scaled grammar fields, and
  `GET /research/backtests/{id}` + MCP `backtests` serve the per-class breakdown byte-identically.
- `docs/handoffs/goal-tape_to_profit_support_resistence-iter-5-dev.md` -- new dev handoff.

## Key Design Decisions Left to the Developer (document the choice made in the handoff)

1. **Exit precedence placement** of the new reward-target reason relative to the existing
   r_stop / state_flip / horizon order -- pick one, document it, and keep it deterministic.
2. **"Next opposing level" resolution rule** -- from the SAME `confluence_zones` list already
   fetched to arm the trade, deterministically pick the nearest zone on the opposite side of the
   entry price from the arming zone (a zone's "kind" is not pre-labeled support/resistance, same
   as an individual level per `levels.py:71-74` -- direction is inferred from which side of price
   it sits on relative to entry, mirroring how the arming logic already treats levels).
3. Whether the class-scaled invalidation is a genuinely new helper beside `_synthetic_invalidation`
   (recommended, since v1/null must keep calling the existing spread-based helper unparameterized)
   or a parameterized extension of it -- either is acceptable as long as v1/null call sites are
   provably unchanged (byte-identical re-run + fingerprint pin are the proof, not the mechanism).

## Key Test Scenarios

- Per-class (A/B/C) net R AND net $, n, sums back to the strategy-level aggregate on the same
  trade population -- one aggregation path, no second scan.
- Class-A stop ≈ 1bp beyond the level on the `SYN-CONFLUENCE` fixture; B/C visibly wider; all
  three values traceable to named config fields (no literal in `research/backtests.py`).
- Class-scaled size: better class -> larger `shares`/notional; multiple is config-owned.
- Reward-target exit fires toward the next opposing level, at the documented precedence position,
  and is proven lookahead-free (same as-of read used for arming, not a future levels computation).
- `config_fingerprint() == '4d665603569b9dbf'` unmoved; `tests/test_profile_equivalence.py` green;
  `v1` and null-baseline trades reproduce byte-identically (no `level` key, unchanged `shares` /
  invalidation formula) AFTER the shared-arithmetic split in `_arm_trade`/`_close_trade`.
- Sub-minimum-n class -> "insufficient sample"; a class with zero trades -> honest empty (n=0,
  rate `None`), never fabricated; unknown `strategy_id` still 422.
- `tests/test_no_execution_path.py` stays green with the new sizing/exit code included in its scan.
- Byte-identical re-run of the per-class report; MCP `backtests` per-class JSON byte-identical to
  REST.
- Full backend suite green with zero regressions against the iter-4 baseline (1128 passed,
  1 skipped); required-still-passing journeys J-01, J-02, J-03, J-04, J-07 unaffected
  (`apps/frontend/` diff empty, engine/profile equivalence green).
