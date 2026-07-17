# goal-fast_wall-iter-3 Functional Test Plan

**Phase:** goal-fast_wall-iter-3
**Date:** 2026-07-17
**Frontend Present:** no

## Phase Goal

`structure_tape` and `structure_tape_map` backtests stop re-running the full levels/tradability pipeline on every confirming tick: a small per-run `_StructureArmMemo` in `backtests.py`, keyed by new `levels.py`/`tradability.py` helpers, serves each arming check from the handful of real level/tradability states a session actually has — byte-identically to today's unmemoized output.

## Test Cases

### TC-01 — level_change_points union/superset contract

**Type:** api  
**Preconditions:** `confluence_bar_store` fixture exists with multiple healthy bar series for a symbol across timeframes, including at least one `PRIOR_PERIOD_TIMEFRAMES` (`1d`, `1w`, or `1mo`) series.

**Steps:**
1. Call `level_change_points(store, symbol)` with the fixture bar store.
2. Inspect the returned tuple for sortedness, deduplication, and content.

**Expected outcome:** The returned tuple is sorted in ascending order, contains no duplicate values, includes every healthy series' bar epoch for the symbol, and includes each prior-period-timeframe bar's `epoch + period_seconds` close instant.

**Pass criteria:** Tuple is sorted, all entries unique, `assert all(e in returned_tuple for e in healthy_series_epochs)`, and `assert all(epoch + period_secs in returned_tuple for each prior-period bar)`.

---

### TC-02 — compute_levels is constant between two consecutive change points

**Type:** api  
**Preconditions:** `level_change_points(store, symbol)` returns a tuple with at least 3 entries. Two `as_of` instants exist that both fall strictly between the same two consecutive entries.

**Steps:**
1. Obtain `level_change_points(store, symbol)`.
2. Select two `as_of` instants both strictly between two consecutive entries (e.g., at T+0.5s and T+5s where T and T+10s are consecutive change points).
3. Call `compute_levels(store, symbol, as_of_1, config)` and `compute_levels(store, symbol, as_of_2, config)` for each instant.
4. Serialize each result with `json.dumps(result, sort_keys=True)`.

**Expected outcome:** The two serialized results are identical strings.

**Pass criteria:** `json.dumps(result_1, sort_keys=True) == json.dumps(result_2, sort_keys=True)`.

---

### TC-03 — basis_day_key returns identical key for same UTC date

**Type:** api  
**Preconditions:** Two `as_of_epoch` values fall on the SAME UTC calendar date (e.g., both on 2026-07-16 but at different times like 03:00 UTC and 21:00 UTC).

**Steps:**
1. Call `basis_day_key(as_of_epoch_1)` and `basis_day_key(as_of_epoch_2)` for both instants.
2. Compare the returned strings.

**Expected outcome:** Both calls return the identical string key.

**Pass criteria:** `basis_day_key(epoch_1) == basis_day_key(epoch_2)` and both return a valid date-format string (e.g., "2026-07-16").

---

### TC-04 — basis_day_key returns different keys across UTC midnight boundary

**Type:** api  
**Preconditions:** Two `as_of_epoch` values fall on DIFFERENT UTC calendar dates, straddling a UTC midnight boundary (e.g., 2026-07-16 23:59:00 UTC and 2026-07-17 00:01:00 UTC).

**Steps:**
1. Call `basis_day_key(epoch_before_midnight)` and `basis_day_key(epoch_after_midnight)`.
2. Compare the returned strings.

**Expected outcome:** The two returned keys are different strings.

**Pass criteria:** `basis_day_key(epoch_before) != basis_day_key(epoch_after)` and each is a valid date key (the before key < the after key lexicographically).

---

### TC-05 — memoized structure_tape is byte-identical to unmemoized

**Type:** api  
**Preconditions:** `confluence_bar_store` fixture and a recorded `structure_tape` (`STRATEGY_TAPE_ID`) dataset exist.

**Steps:**
1. Run `BacktestRunner.run()` with a per-run `_StructureArmMemo` built and threaded through `_structure_tape_arm` (i.e., memoized path).
2. Run `BacktestRunner.run()` on the same dataset with `memo=None` (today's direct-call path).
3. Serialize each result with `json.dumps(result, sort_keys=True)`.

**Expected outcome:** The two serialized results are identical.

**Pass criteria:** `json.dumps(memoized_result, sort_keys=True) == json.dumps(unmemoized_result, sort_keys=True)`.

---

### TC-06 — memoized structure_tape_map is byte-identical to unmemoized

**Type:** api  
**Preconditions:** `confluence_bar_store` fixture and a recorded `structure_tape_map` (`STRATEGY_TAPE_MAP_ID`) dataset exist.

**Steps:**
1. Run `BacktestRunner.run()` with a per-run `_StructureArmMemo` built and threaded through `_structure_tape_map_arm` (memoized path).
2. Run `BacktestRunner.run()` on the same dataset with `memo=None` (unmemoized path).
3. Serialize each result with `json.dumps(result, sort_keys=True)`.

**Expected outcome:** The two serialized results are identical.

**Pass criteria:** `json.dumps(memoized_result, sort_keys=True) == json.dumps(unmemoized_result, sort_keys=True)`.

---

### TC-07 — memo-bust leg 1: daily period close between bar epochs

**Type:** api  
**Preconditions:** A bar-store fixture exists where a `1d` period's close instant (`epoch + period_seconds`) falls strictly between two intraday bar epochs — so that close instant is itself a `level_change_points` entry with no bar recorded exactly at it.

**Steps:**
1. Run a `structure_tape` backtest memoized over that boundary.
2. Run the same backtest with `memo=None` (unmemoized).
3. Serialize each result with `json.dumps(result, sort_keys=True)` and compare.
4. Verify that at least one arming decision (armed vs. not-armed, or which classified level qualifies) differs between an event strictly before the change point and an event strictly after it.

**Expected outcome:** The memoized and unmemoized results are byte-identical, AND at least one arming decision differs across the boundary (proving the fixture exercises a genuine regime change, not vacuous).

**Pass criteria:** `json.dumps(memoized, sort_keys=True) == json.dumps(unmemoized, sort_keys=True)` AND `assert any(arming_before != arming_after for crossing events)`.

---

### TC-08 — memo-bust leg 2: run spans UTC date boundary

**Type:** api  
**Preconditions:** A bar-store/dataset fixture exists whose recorded tick stream spans a UTC calendar-date boundary (so `basis_day_key` returns two distinct keys across the run).

**Steps:**
1. Run a `structure_tape_map` backtest memoized across that boundary.
2. Run the same backtest with `memo=None` (unmemoized).
3. Serialize each result with `json.dumps(result, sort_keys=True)` and compare.
4. Verify that the tradability basis (`basis_as_of`) used before the boundary differs from the one used after it.

**Expected outcome:** The memoized and unmemoized results are byte-identical, AND the tradability basis differs across the UTC midnight boundary (proving the fixture exercises a genuine regime change).

**Pass criteria:** `json.dumps(memoized, sort_keys=True) == json.dumps(unmemoized, sort_keys=True)` AND `assert basis_before != basis_after`.

---

### TC-09 — counting spy: compute_levels called once per change-point interval

**Type:** api  
**Preconditions:** A `structure_tape` backtest whose recorded tick stream crosses at least 3 distinct `level_change_points` intervals, with more than one flat-arming-eligible tick inside each interval.

**Steps:**
1. Wrap `levels.compute_levels` with a call-counting spy.
2. Run the backtest with the memo enabled.
3. Count the number of `compute_levels` calls and compare to the number of distinct change-point intervals visited.

**Expected outcome:** The spy records exactly one call per distinct change-point interval actually visited by the run — never one call per confirming tick.

**Pass criteria:** `spy_call_count == distinct_intervals_visited` and `distinct_intervals_visited < total_confirming_ticks`.

---

### TC-10 — counting spy: compute_tradability called once per day key

**Type:** api  
**Preconditions:** A `structure_tape_map` backtest whose recorded tick stream crosses at least 2 distinct `basis_day_key` values, with more than one flat-arming-eligible tick inside each.

**Steps:**
1. Wrap `tradability.compute_tradability` with a call-counting spy.
2. Run the backtest with the memo enabled.
3. Count the number of `compute_tradability` calls and compare to the number of distinct day keys visited.

**Expected outcome:** The spy records exactly one call per distinct day key actually visited by the run — never one call per confirming tick.

**Pass criteria:** `spy_call_count == distinct_day_keys_visited` and `distinct_day_keys_visited < total_confirming_ticks`.

---

### TC-11 — multi-interval fixture completes within interactive budget

**Type:** api  
**Preconditions:** A newly-added committed fixture exists whose recorded tick stream crosses at least 5 distinct `level_change_points` intervals.

**Steps:**
1. Run the memoized `structure_tape` backtest to completion inside the test suite.
2. Record wall-clock duration (pytest's per-test reported duration).
3. Inspect the result's `trades` list for non-emptiness.

**Expected outcome:** The test completes in under 10 seconds of wall-clock time and its `trades` list is non-empty.

**Pass criteria:** `wall_clock_duration < 10.0` and `len(result.trades) > 0`.

---

### TC-12 — existing structure_tape/map pinned-value tests pass unmodified

**Type:** api  
**Preconditions:** The full `test_backtests.py` module exists, including all existing `structure_tape`/`structure_tape_map` pinned-value and arming tests (currently spanning roughly lines 349–970).

**Steps:**
1. Run the test suite.
2. Verify that every existing test passes.
3. Run `git diff` on each test function's body to confirm zero edits (additions-only diff).

**Expected outcome:** Every existing `structure_tape`/`structure_tape_map` pinned-value and arming test passes with its source code byte-unmodified.

**Pass criteria:** All tests pass AND `git diff` shows zero edits to pre-existing test bodies (only new code added elsewhere).

---

### TC-13 — source-introspection guard tests pass unmodified

**Type:** api  
**Preconditions:** `test_backtests.py:1500-1508` (`test_structure_tape_reads_levels_from_the_one_canonical_compute_levels_owner`) and `:932-943` (`test_structure_tape_map_reads_tradability_never_recomputes_levels_or_zones`) exist.

**Steps:**
1. Run both guard tests.
2. Verify they pass.
3. Run `git diff` on each test's body to confirm zero edits.
4. Verify their assertions hold against the new `backtests.py` source (no forbidden substring introduced).

**Expected outcome:** Both tests pass, their source is byte-unmodified, and their assertions pass without change (confirming the literal `compute_levels(`/`compute_tradability(` owner calls remain present and no forbidden level-internal substrings are introduced).

**Pass criteria:** Both tests pass with zero body edits AND `assert "compute_levels(" in backtests_source` AND `assert "_swing_pivots" not in backtests_source`.

---

### TC-14 — full backend suite passes, fingerprint frozen

**Type:** api  
**Preconditions:** The full backend unit/integration test suite is ready to run.

**Steps:**
1. Run the complete backend test suite.
2. Record the count of passed, failed, and skipped/deleted tests.
3. Call `config.config_fingerprint()` and record the value.

**Expected outcome:** Zero test failures, zero pre-existing tests newly skipped or deleted, and `config_fingerprint()` equals `4d665603569b9dbf`.

**Pass criteria:** `test_failures == 0` AND `newly_skipped_or_deleted == 0` AND `config_fingerprint() == "4d665603569b9dbf"`.

---

### TC-15 — existing levels/tradability pinned-value tests pass unmodified (J-01/J-02/J-07 non-regression gate)

**Type:** api  
**Preconditions:** `test_levels.py` and `test_tradability.py` contain existing pinned-value tests (e.g., `test_byte_identical_determinism_across_independent_runs`, `test_committed_fixture_confluence_zones_exact_values_keyless`, `test_aapl_frozen_levels_output_is_byte_identical_to_before`, `test_aapl_repeat_call_determinism`).

**Steps:**
1. Run all existing pinned-value tests in both files.
2. Verify every test passes.
3. Run `git diff` on each test function's body to confirm zero edits (additions-only diff).

**Expected outcome:** Every existing pinned-value test in `test_levels.py` and `test_tradability.py` passes with source code byte-unmodified — proving `compute_levels`'s and `compute_tradability`'s served values are unchanged for every existing reader, including `/structure`'s Tradable Map and Case Studies sections (required-still-passing journeys J-01, J-02, J-07).

**Pass criteria:** All pinned-value tests pass AND `git diff` shows zero edits to pre-existing test bodies.

---

## Summary

**Total test cases:** 15
- **API tests:** 15
- **Browser tests:** 0
- **Artifact checks:** 0

**Test organization:**
- TC-01, TC-02: `level_change_points` contract and constant-function property
- TC-03, TC-04: `basis_day_key` same-date stability and cross-boundary distinctness
- TC-05, TC-06: Memoized structure-strategy byte-identity (main acceptance)
- TC-07, TC-08: Both goal.md-named memo-bust legs (daily period close + UTC boundary)
- TC-09, TC-10: Counting spies proving ~100 calls per session instead of per-tick
- TC-11: Multi-interval fixture interactive-budget proof
- TC-12, TC-13: Existing test re-run verification and source-introspection guard tests
- TC-14, TC-15: Full suite green + fingerprint frozen + J-01/J-02/J-07 non-regression mechanical gate

**Frontend:** Not applicable — `Frontend Present: no`. Required-still-passing journeys J-01, J-02, J-07 are verified via the mechanical byte-identity gate (TC-14/TC-15), not a fresh browser pass, per the iter-2 lesson applied to this iteration (phase spec's BACKGROUND section).
