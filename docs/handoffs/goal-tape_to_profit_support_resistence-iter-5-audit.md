# goal-tape_to_profit_support_resistence-iter-5 Audit Report

**Date:** 2026-07-06
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

J-05 is fully and correctly implemented: `structure_tape` now sizes and stops each simulated entry by its arming level's A/B/C class and carries a class-scaled reward-target exit, and the backtest report exposes a per-class PnL breakdown (net R AND net $, n, `insufficient_sample`) served verbatim by the existing `GET /research/backtests/{id}` + MCP `backtests`. I independently re-ran the critical proofs rather than trusting the handoff: the pinned fingerprint `4d665603569b9dbf` is unmoved, `test_profile_equivalence.py` is green, the class-scaled arithmetic is traced correct end-to-end, and the tests re-derive every formula independently (no self-agreeing import). The frozen `v1`/`default` anti-goal, the no-execution/no-capital anti-goals, and the no-lookahead discipline all hold. Only minor test-thoroughness observations remain — none compromise the phase goal.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no defect): class-scaled risk math is correct and gated cleanly on `level is not None`.**
Traced `apps/backend/app/research/backtests.py`:
- `_class_scaled_invalidation` (line 197) places the stop the class's own bps beyond the *arming level's* price on the adverse side, with a correct entry-relative fallback when the level-relative price would land at/through the entry print (the documented `SIM-ASKABS` rejection-short case). For a long the returned price is provably `< entry`; for a short provably `> entry`, so `r_basis` (line 37 of `marks.py`, `abs(reference - invalidation)`) is always `> 0` — no divide-by-zero downstream.
- `_next_opposing_zone_price` (line 229) excludes the arming zone **by object identity** (`z is not arming_zone`), correctly handling a rejection entry that sits at its own level's price; filters to the side `direction` implies; returns `None` honestly when no zone qualifies.
- `_class_scaled_target` (line 248) is bounded both ways via `min(class_R_multiple * r_basis, |opposing - entry|)`; target is provably strictly beyond entry (distance `> 0`), so it can never fire at the entry event.
- Exit precedence (line 745): `r_stop → reward_target → state_flip → horizon`, with the reward branch reached only via `trade.get("target_price")`, which is `None` for v1/null trades (they never set the key) — so v1/null exit behavior is unchanged.
- Size scaling (`_close_trade`, line 791) branches on `"level" in trade`; v1/null trades take the unchanged `dollars_per_r / r_basis` formula.
No fix needed. `_zone_nearest_price`'s `min(zone["levels"], …)` cannot receive an empty list — `levels.py:204` guarantees every confluence zone has ≥2 members.

**B2 — OBSERVATION (no defect): the "per train/hold-out split" DoD clause is satisfied via dataset provenance, not a second in-report axis.**
The spec's DoD (line 86) reads "per train/hold-out split." A single backtest runs over exactly one dataset, and a dataset carries one frozen `split` tag (`apps/backend/app/research/datasets.py:63-64`, persisted at line 325). `run()` (line 381/407) embeds `dataset_meta` — including `split` — verbatim into `result["dataset"]`, so `aggregates_by_class` is inherently scoped to and labeled by its report's split. The cross-split comparison is J-06 (explicitly out of scope). This is the honest single-source interpretation, not a partial implementation. The handoff documents this correctly.

### Frontend Findings

None. `apps/frontend/` diff is empty (`git diff --stat -- apps/frontend/` confirmed empty). Frontend Present: no. J-07's frozen-cockpit leg is protected by the zero-diff.

### Test Findings

**T1 — GAP: the `insufficient_sample: False` branch (a class with n ≥ `pnl_min_sample_size`) is never exercised.**
`apps/backend/app/research/backtests.py:328` computes `insufficient_sample = agg["n"] < config.pnl_min_sample_size`. Every J-05 fixture arms exactly one trade (cooldown-limited), so only `n=0` and `n=1` (both under the floor of 5) are tested — the "sufficient sample" case is never seen. The comparison is trivial and `_aggregate` is independently well-tested, so this is a coverage gap, not a correctness risk. The spec required the "insufficient sample" *label* (which IS tested), not the negative case. Not fixed — writing a ≥5-trade-in-one-class fixture is scope creep for a one-line boolean.

**T2 — OBSERVATION: the partition-sum invariant is proven only on single-trade reports.**
`_assert_per_class_breakdown_isolates_one_trade` (test_backtests.py) asserts `sum(n) == aggregates["n"]`, `sum(net_r)`, `sum(net_usd)` — correctly summing only the additive fields (not the non-additive `win_rate`/`max_drawdown_r`). Because each fixture arms one trade, the "sum" is populated in one class and zero in the other two. A report with trades in ≥2 classes simultaneously is not exercised. The aggregation is a pure partition-sum so the property is guaranteed by construction, and all three classes A/B/C are each covered via a dedicated same-price fixture. Test thoroughness note only.

**T3 — OBSERVATION: `test_structure_tape_reward_target_exit_fires_lookahead_free` proves the value, not mechanically the absence of a future read.**
The test asserts the fired target (100.75) matches the arm-time-derived value (`opposing_price=200.00`, the arm-time zone_b) via the arithmetic helper. Lookahead-freeness itself is guaranteed structurally: `opposing_price` is resolved from the *same* `compute_levels(...)` result used to arm (backtests.py:626-645, `as_of_epoch = epoch_anchor + point.timestamp`) and frozen onto the position — no second/future levels read exists. The property holds by construction; the test name is slightly stronger than its direct assertion. Informational.

---

## 3. Domain Assessment

The core domain logic is sound and honest.

- **Class-scaled risk math** correctly encodes the conviction ordering: A gets the tightest stop (1bp), largest size (2.0×), most generous reward multiple (3.0×); C the widest/smallest/least. All three values live in named `Config` dicts keyed by class (`config.py:1212/1226/1234`), read by name in `backtests.py` — the no-magic-number test asserts the `config.structure_tape_*` substrings are present in source and the arithmetic helper re-derives from config, so a hard-coded literal would fail.
- **Single source of truth** is preserved: `aggregates_by_class` is computed once in `run()` (line 418) alongside `aggregates`, from the same trade population, and served verbatim by REST and (structurally, via the verbatim proxy proven by `test_mcp_server.py:327`) MCP. No second computation path.
- **Honest failure/empty states**: zero-trade classes serve `_aggregate([])` emptiness (n=0, rates `None`); sub-minimum-n classes carry `insufficient_sample: True`; all three classes are always present (no omission, no fabrication) — verified by exact-dict assertions.
- **Frozen `v1`/`default`** (the CRITICAL anti-goal) is intact: fingerprint independently confirmed `4d665603569b9dbf`; the new fields are all in the `excluded` set (config.py:1639-1641); `test_profile_equivalence.py` green; v1/null trades carry no `level`/`target_price` key and take every unchanged code path.
- **No-execution / no-capital anti-goals**: size is pure arithmetic over a fixed simulated notional; the grep-guard is extended with an explicit J-05 test (`test_no_execution_path.py`) that first asserts the scan actually sees the new code (guarding against a vacuous pass) then asserts no Tier-1/Tier-2 execution vocabulary.
- **No lookahead**: stop and target are both fixed at arm time from the as-of `compute_levels` read.

Scope discipline is clean: only `config.py`, `research/backtests.py`, and three test files changed — no `pnl_scan.py`, `edge_report.py`, champion pointer, or frontend touched.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issues were found. The remaining items (T1 gap, T2/T3/B1/B2 observations) are minor test-thoroughness and interpretation notes; fixing them would be scope creep, which the auditor rules prohibit.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

Proceed to release, then advance to **J-06** (the next journey in the J-01→J-06 order), which J-05 unblocks: with `structure_tape` now carrying its class-scaled stop/reward/size math, the edge-report/sweep can honestly compare `structure_tape` vs `v1` on the hold-out promotion path.

Carry-forward for J-06 (not J-05 defects):
- Iter-4 audit item **B1** remains open by design: the breakthrough arm is a static price-position test (`point.last > price`), not a fresh event-to-event cross — a disclosed loose anchor that affects J-06's honest edge comparison, not J-05's sizing math.
- Optionally, when J-06 populates reports with trades across multiple classes, add a multi-class partition-sum assertion (T2) and a ≥`pnl_min_sample_size` per-class case (T1) to close the two coverage notes above.
