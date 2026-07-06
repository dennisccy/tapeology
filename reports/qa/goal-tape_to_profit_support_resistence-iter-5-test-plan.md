# Goal Iteration 5 (J-05) — Functional Test Plan

**Phase:** goal-tape_to_profit_support_resistence-iter-5  
**Date:** 2026-07-06  
**Frontend Present:** no

## Phase Goal

Add class-scaled stop, reward target, and simulated position size to the `structure_tape` strategy, gated by A/B/C confluence class; expose per-class PnL breakdown (net R AND net $, n, per train/hold-out split) on the backtest report, all config-owned and caveated as simulated.

## Test Cases

### TC-01 — Config fields exist and are excluded from fingerprint

**Type:** artifact  
**Preconditions:** Phase implementation complete; `apps/backend/app/config.py` contains the new class-scaling fields.

**Steps:**
1. Read `apps/backend/app/config.py` and locate the three new `structure_tape_*` config fields (stop distance, reward target, simulated size multiple).
2. Verify each field has a documented rationale (inline comment explaining the choice).
3. Verify each field name appears in the `config_fingerprint()` function's `excluded` set (lines ~1579-1581).
4. Verify `config_fingerprint()` still returns exactly `'4d665603569b9dbf'` (unchanged from v1/default baseline).

**Expected outcome:** All three new fields exist with clear rationale; all three are explicitly excluded from the fingerprint; fingerprint value is unchanged.  
**Pass criteria:** `grep -E "structure_tape_(stop_distance|reward_target|size_multiple)" apps/backend/app/config.py | wc -l` returns 3 (or more, if used in multiple places); `config_fingerprint()` returns `'4d665603569b9dbf'`; all three field names appear in the `excluded` list with rationale comments.

---

### TC-02 — Class-scaled stop is applied to structure_tape trades only

**Type:** api  
**Preconditions:** Backend running; synthetic 3-timeframe `SYN-CONFLUENCE` fixture loaded in test environment; `structure_tape` strategy selected.

**Steps:**
1. Run the acceptance suite or a focused unit test that arms a `structure_tape` trade on the `SYN-CONFLUENCE` fixture with an A-class (tight-confluence) level.
2. Inspect the trade dict returned by the backtest runner; verify `trade["stop"]` or the invalidation distance reflects the class-A config value (≈ 1bp beyond the level).
3. Verify the stop is computed from the level price plus the class-A distance, NOT from the spread-based `_synthetic_invalidation`.
4. Re-run the same backtest; verify the stop distance reproduces byte-identically.

**Expected outcome:** A-class trade stop is tighter (closer to the level) than B/C stops; all three class values are traceable to named config fields; byte-identical re-run.  
**Pass criteria:** `trade["stop"]` for A-class ≈ 1bp beyond the level; B-class and C-class stops are visibly wider; all three values sourced from config; test_backtests.py contains an assertion on the synthetic fixture with A-class output.

---

### TC-03 — Reward-target exit fires at documented precedence and is lookahead-free

**Type:** api  
**Preconditions:** Backend running; `structure_tape` backtest completed; trade population includes at least one reward-target exit.

**Steps:**
1. Run a backtest with `structure_tape` and inspect the exit reasons logged in the trade dict (field `trade["exit_reason"]`).
2. Verify at least one trade has `exit_reason == "reward_target"` (or equivalent constant name).
3. Inspect the code path in `_exit_reason()` and confirm the reward-target check is placed at a documented fixed position in the precedence order (relative to r_stop, state_flip, horizon).
4. Trace the "next opposing level" resolution: verify it uses the SAME `confluence_zones` list fetched at arm time (`_structure_tape_arm`), NOT a second future levels call.
5. Re-run the same backtest; verify exit reasons reproduce byte-identically.

**Expected outcome:** Reward-target exit exists; fires at predictable precedence; resolved from existing arm-time level data (no lookahead); deterministic re-run.  
**Pass criteria:** At least one trade exits with `exit_reason == "reward_target"`; code comment documents the precedence position; `compute_levels()` is called exactly once per arm, reused for both arming and next-opposing resolution; test_backtests.py asserts lookahead-free resolution.

---

### TC-04 — Class-scaled size multiple is applied to structure_tape only

**Type:** api  
**Preconditions:** Backend running; backtest completed for both `structure_tape` and `v1` strategies on the same trade population.

**Steps:**
1. Run a backtest of `structure_tape` and extract the `shares` (position size notional) for a trade with A-class level (best class).
2. Run the same backtest with `v1` strategy and extract shares for a comparable trade.
3. Verify the `structure_tape` A-class shares are larger by the configured A-class size multiple (read from config).
4. Verify B-class and C-class trades have progressively smaller shares.
5. Verify `v1` trades and null-baseline trades are byte-identically unchanged (no `level` key → unchanged `shares` formula).

**Expected outcome:** `structure_tape` applies class-scaled size multiple; A > B > C; `v1` and null trades unaffected.  
**Pass criteria:** `shares_a_class * config.structure_tape_size_multiple_a == shares_strategy` (or similar proportionality); `v1` backtest produces same shares as baseline; test_backtests.py asserts class-scaled size and v1/null byte-identity.

---

### TC-05 — Per-class PnL breakdown sums to strategy total

**Type:** api  
**Preconditions:** Backend running; `structure_tape` backtest report generated with at least 5 trades per class.

**Steps:**
1. Call `GET /research/backtests/{id}` and extract the new per-class breakdown (row 42, or the equivalent location in the JSON).
2. Verify the response includes per-class (A/B/C) sections with: net R, net $, count (n), per train/hold-out split.
3. Sum the net R across A+B+C and verify it matches the strategy-level aggregate (within floating-point tolerance).
4. Sum the net $ across A+B+C and verify it matches the strategy-level aggregate.
5. Verify the count (n) sums correctly per split.
6. Repeat the backtest run; verify the per-class breakdown reproduces byte-identically in the JSON.

**Expected outcome:** Per-class data exists; A+B+C sums equal the strategy total; one aggregation path (no second scan); byte-identical re-run.  
**Pass criteria:** `response["class_breakdowns"]["A"]["net_r"] + response["class_breakdowns"]["B"]["net_r"] + response["class_breakdowns"]["C"]["net_r"] == response["aggregates"]["net_r"]` (or equivalent JSON structure); test_backtests.py includes an assertion on per-class aggregate correctness; MCP `backtests` tool returns the same JSON byte-identically.

---

### TC-06 — Sub-minimum-n class labeled "insufficient sample"

**Type:** api  
**Preconditions:** Backend running; `structure_tape` backtest where one class (e.g., A) has fewer than the configured minimum n.

**Steps:**
1. Call `GET /research/backtests/{id}` and locate the per-class breakdown for the sub-minimum-n class.
2. Verify the response includes a label or flag indicating "insufficient sample" (or the standard insufficient_sample precedent from the codebase).
3. Verify the class still appears in the breakdown (not omitted) and carries honest counts (n, rates showing `None` or `null` if appropriate).
4. Verify the label is consistent with the existing `insufficient_sample` pattern in `analytics.py`, `pnl_ledger.py`, or `edge_report.py`.

**Expected outcome:** Sub-minimum-n class marked as insufficient sample; count and rates are honest (not fabricated).  
**Pass criteria:** Response includes `"insufficient_sample": True` (or equivalent) on the class object; n < minimum_threshold; rate fields are `None`; test includes a case with n < minimum.

---

### TC-07 — A class with zero trades is honest-empty, not fabricated

**Type:** api  
**Preconditions:** Backend running; `structure_tape` backtest where one class (e.g., B) produces zero trades.

**Steps:**
1. Call `GET /research/backtests/{id}` and locate the per-class breakdown for the zero-trade class.
2. Verify the class still appears in the response (complete set, not omitted).
3. Verify the class carries n=0 and rate fields are `None` (or the honest-empty representation in the codebase).
4. Verify no fabricated data (e.g., no synthetic 0% return, no synthetic trade).

**Expected outcome:** Zero-trade class appears with n=0 and `None` rates; no synthetic data injected.  
**Pass criteria:** `response["class_breakdowns"]["B"]["n"] == 0`; `response["class_breakdowns"]["B"]["net_r"]` is `None` or `null`; test includes a zero-trade case.

---

### TC-08 — v1 and default profile remain byte-identical after the split

**Type:** artifact  
**Preconditions:** Phase implementation complete; both `v1` and `structure_tape` strategies implemented.

**Steps:**
1. Run the backtest suite with the `v1` strategy and capture the full trade population dict.
2. Run `tests/test_profile_equivalence.py` to verify byte-identical v1 output.
3. Verify that the new class-scaling split in `_arm_trade`, `_close_trade`, and `_exit_reason` is guarded by `if level is not None:` and does NOT affect v1 or null-baseline trades.
4. Verify a `v1` trade dict does NOT carry a `level` key and uses the original `_synthetic_invalidation` formula unchanged.
5. Verify `config_fingerprint() == '4d665603569b9dbf'` (unchanged).

**Expected outcome:** v1 trades and null-baseline trades byte-identical to baseline; no regression in equivalence test.  
**Pass criteria:** `tests/test_profile_equivalence.py` passes; v1 backtest JSON byte-identical to iter-4 baseline; `v1` trade dicts lack the `level` key; `config_fingerprint()` unchanged; test_backtests.py asserts v1/null byte-identity AFTER the split.

---

### TC-09 — No execution/routing/broker identifier introduced in sizing/exit code

**Type:** artifact  
**Preconditions:** Phase implementation complete; new sizing and exit-reason code paths added.

**Steps:**
1. Run the extended `tests/test_no_execution_path.py` grep-guard to scan the new sizing code in `_close_trade`.
2. Run the extended grep-guard to scan the new exit-reason code in `_exit_reason`.
3. Verify no patterns like "broker", "order", "routing", "execution", "paper_trading", "transmit", or similar identifiers appear in the new code.
4. Verify the sizing is documented as "simulated notional" and carries no side effects (no external API calls, no order placement, no capital tracking).

**Expected outcome:** No execution/broker/routing identifier present; sizing code is side-effect-free and documented as simulated.  
**Pass criteria:** `tests/test_no_execution_path.py` passes with the new code included; no grep matches for execution-related identifiers; code comments document "simulated notional, transmits nothing".

---

### TC-10 — Strategy registry includes structure_tape with class-scaled grammar

**Type:** api  
**Preconditions:** Backend running; `GET /research/strategies` endpoint available.

**Steps:**
1. Call `GET /research/strategies` and verify the response includes both `v1` and `structure_tape` strategy entries.
2. Locate the `structure_tape` entry and verify it includes the class-scaled grammar: stop distance per class (A/B/C), reward target, and simulated size multiple per class.
3. Verify each grammar field is read by name from the config (no inline literals).
4. Verify the `v1` grammar is unchanged.

**Expected outcome:** Strategy registry lists both strategies; `structure_tape` shows class-scaled parameters; all values sourced from config.  
**Pass criteria:** `response["strategies"]` is an array with 2+ entries; `structure_tape` entry has `class_scaled_stop`, `reward_target`, `class_scaled_size` (or equivalent field names) populated from config; test_strategies_api.py confirms the response structure.

---

### TC-11 — Required-still-passing journeys J-01, J-02, J-03, J-04, J-07 remain green

**Type:** api  
**Preconditions:** Full backend test suite executable; required journey test suites defined.

**Steps:**
1. Run the full backend test suite (`pytest` from `.claude/project-template.md` or equivalent).
2. Verify all unit tests pass (including journey acceptance suites for J-01, J-02, J-03, J-04, J-07).
3. Verify no regression: the passing count should be >= iter-4 baseline (1128 passed, 1 skipped).
4. If any test fails, record the failure as a blocker.

**Expected outcome:** Full backend suite green; no regression against iter-4 baseline.  
**Pass criteria:** Exit code 0; pass count >= 1128; J-01/J-02/J-03/J-04/J-07 acceptance suites all PASS.

---

### TC-12 — MCP backtests tool returns per-class breakdown byte-identically to REST

**Type:** api  
**Preconditions:** Backend running; MCP server running; backtest completed.

**Steps:**
1. Call `GET /research/backtests/{id}` via REST and capture the JSON response.
2. Call the MCP `backtests` tool (from the tapeology MCP server) with the same backtest ID and capture the response.
3. Compare the two responses: verify the per-class breakdown (row 42 data) is byte-identically the same in both.
4. Verify no additional processing or divergence between REST and MCP.

**Expected outcome:** REST and MCP return identical per-class breakdown.  
**Pass criteria:** JSON strings match exactly (or after JSON-canonical normalization); test_backtests_api.py includes an assertion comparing REST and MCP responses.

---

## Summary

**Total test cases:** 12  
**API tests:** 9 (TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-10, TC-11, TC-12)  
**Artifact checks:** 3 (TC-01, TC-08, TC-09)  

All test cases are backend-only (Frontend Present: no). Success criteria are specific and verifiable; each test maps to a DEFINITION OF DONE item from the phase spec.
