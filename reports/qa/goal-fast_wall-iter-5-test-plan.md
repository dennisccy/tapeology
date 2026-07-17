# goal-fast_wall-iter-5 Functional Test Plan

**Phase:** goal-fast_wall-iter-5  
**Date:** 2026-07-17  
**Frontend Present:** yes

## Phase Goal

Close J-04's browser verification gap with zero new product code (a screenshot of the "Compute edge report" flow), then make the edge report sweep genuinely resumable (cached dataset×strategy pairs skip recomputation on re-trigger) and parallel (process pool). Iteration 5 delivers J-04's missing browser evidence and J-05's resumable, parallel backend sweep infrastructure.

---

## Test Cases

### TC-1 — Browser: Compute edge report live progress cycle

**Type:** browser  
**Preconditions:**
- Backend and frontend both running on scoped ports 8391/3391
- Environment set: `TAPEOLOGY_DATASET_DIR=apps/backend/tests/fixtures/datasets_j03`, `TAPEOLOGY_EDGE_REPORT_CACHE_DB=/tmp/edge_report.db`, `TAPEOLOGY_EDGE_SWEEP_CACHE_DB=/tmp/edge_report_backtests.db` (both fresh/empty)
- `/structure` page is loaded, Edge Report section shows the "Compute edge report" button (not-computed state)
- Chrome MCP session is healthy and ready for automation

**Steps:**
1. Capture screenshot of the pre-click state showing the "Compute edge report" button clearly visible
2. Click the "Compute edge report" button
3. Within 3 seconds, verify the panel transitions to `state === "running"` and begins emitting progress updates
4. Capture screenshot showing progress line with at least one mid-run update (e.g., "backtests_done / backtests_total" counter visible, `state` field showing "running")
5. Wait up to 90 seconds for the compute to complete
6. Verify the panel transitions out of the running state within 90 seconds (either to `state === "done"` with report body rendered, OR `state === "failed"` with error message)
7. Capture screenshot of the terminal state (completed report or error panel)
8. Verify zero full-page reloads occurred (page path unchanged, no 404s in network log)

**Expected outcome:** The compute progresses from idle → running → terminal (done or failed) within 90 seconds, with visible progress updates mid-run and no full-page reload.

**Pass criteria:**
- Progress line visible while `state === "running"`
- Terminal state reached within 90 seconds
- Two valid screenshots captured (mid-run and terminal)
- No full-page reload occurred
- Browser console has no uncaught errors blocking the panel

---

### TC-2 — Browser: J-01 not-computed panel and J-07 broader structure sections render unchanged

**Type:** browser  
**Preconditions:**
- Same scoped session as TC-1, immediately after TC-1's compute completes
- Page remains at `/structure` (no manual reload yet performed)

**Steps:**
1. Scroll up to view the Edge Report section (confirm TC-1's compute result is visible above this step)
2. Reload `/structure` to reset the page state
3. Wait for the page to fully load
4. Verify the Edge Report section displays the now-warm cached result (no "Compute" button, no "not-computed" panel)
5. Scroll to view and capture the Tradable Map section — verify it renders with zones, level lines, and the ≤10-band structure exactly as shown in era-5B reference screenshots
6. Capture the Case Studies section — verify it displays the anchored support/resistance case data unchanged
7. Capture the Registry section header and champion row — verify the registry badge and champion pointer are unchanged
8. Capture the Comparison section header with the v1/structure_tape/structure_tape_map row labels — verify the row headers and comparison logic are unchanged

**Expected outcome:** All four `/structure` sections render exactly as they did before this iteration, with zero visual regressions or missing elements.

**Pass criteria:**
- Edge Report section no longer shows the "not-computed" button (shows the warm-cached report instead)
- Tradable Map renders the ≤10-band zones exactly as baseline
- Case Studies displays anchored case data unchanged
- Registry shows champion pointer unchanged
- Comparison displays the three-way row labels and logic unchanged
- Four distinct screenshots captured and match baseline era-5B evidence

---

### TC-3 — Browser: Failed-state error message renders verbatim

**Type:** browser  
**Preconditions:**
- Same scoped backend/frontend pair as TC-1/TC-2
- A compute snapshot at `state: "failed"` has been injected via a direct backend POST call with a known error message (e.g., "Test error: simulated compute failure")
- Browser navigates to (or polls) `/structure` after the error is set

**Steps:**
1. Use a direct backend call (e.g., `curl` or test POST to `/research/edge-report/compute`) to set the compute snapshot to `state: "failed"` with `error: "Test error: simulated compute failure"`
2. Navigate browser to `/structure` (or trigger a poll tick if already at the page)
3. Wait for the Edge Report panel to render the error state
4. Capture screenshot showing the error message panel
5. Verify the exact error string "Test error: simulated compute failure" is visible in the panel verbatim

**Expected outcome:** The error state panel renders the exact error string from the backend without truncation, mangling, or alteration.

**Pass criteria:**
- Error panel is visible and not hidden behind a loading spinner
- Error text contains the exact string "Test error: simulated compute failure"
- Error message is readable (not truncated or wrapped off-screen)
- Screenshot clearly shows the verbatim error text

---

### TC-4 — Unit: EdgeReportBacktestCache durability and byte-identity equivalence

**Type:** api  
**Preconditions:**
- Fresh empty `EdgeReportBacktestCache` DB file (path resolved via env or default)
- Committed fixture dataset registry with 2+ datasets (e.g., `apps/backend/tests/fixtures/datasets_j03`)
- `run_strategy_comparison_report` function and `EdgeReportBacktestCache` class are available

**Steps:**
1. Create an empty `EdgeReportBacktestCache` instance pointing to a fresh DB
2. Call `run_strategy_comparison_report(..., sub_cache=<cache>)` on the fixture registry with 3 registered strategies
3. For each (dataset, strategy) pair, verify the cache DB now contains exactly one durable row
4. Serialize the returned report with `json.dumps(..., sort_keys=True)`
5. In a second Python process, call `run_strategy_comparison_report(..., sub_cache=None)` with identical inputs
6. Serialize that report with `json.dumps(..., sort_keys=True)`
7. Byte-compare the two serialized reports for equality

**Expected outcome:** Every eligible (dataset, strategy) pair is durably persisted as one row in the cache DB, and a full run using the cache produces byte-identical output to an uncached run of the same inputs.

**Pass criteria:**
- Cache DB contains one row per (dataset, strategy) pair
- Row keys include all 8 components (dataset_id, dataset_checksum, strategy_id, profile, config_fingerprint, config_content_hash, strategy_registry, bar_store_signature)
- Byte-comparison equality: `report_cached_json == report_uncached_json`
- Both reports render the same cells, register, gates, and summary fields

---

### TC-5 — Unit: Key-busting matrix (8 components independently bust the cache)

**Type:** api  
**Preconditions:**
- One warm `EdgeReportBacktestCache` row for a known (dataset, strategy) pair
- A call-counting spy (mock or wrapper) on `_run_backtest` to track fresh compute calls
- Ability to independently mutate each of the 8 key components

**Steps:**
1. Establish a cache hit: call `run_strategy_comparison_report(..., sub_cache=<cache>)` with a known pair; verify the pair is cached durably
2. Reset the call spy counter to 0
3. Re-request the same pair (should be a cache hit); verify spy count stays 0
4. For each of the 8 key components (dataset_id, dataset_checksum, strategy_id, profile, config_fingerprint, config_content_hash, strategy_registry, bar_store_signature):
   a. Mutate that component independently (e.g., change dataset_id from "DS1" to "DS2", or flip one bit in the config_content_hash)
   b. Reset spy counter to 0
   c. Re-request the pair with the SAME dataset and strategy IDs but the mutated key component
   d. Verify spy count incremented exactly once (one fresh `_run_backtest` call)
   e. Revert the mutation

**Expected outcome:** Each of the 8 key components is proven independently necessary — mutating any one forces a recompute.

**Pass criteria:**
- Spy records 0 calls for the initial cache hit
- For EACH of the 8 mutations, spy records exactly 1 fresh `_run_backtest` call
- No false negatives: all 8 mutations must produce a call (a cache silently ignoring one component would fail that row)
- Mutations are independent: reverting one does not affect the next test

---

### TC-6 — Unit: Kill-and-resume sweep re-computes only missing pairs

**Type:** api  
**Preconditions:**
- Fresh empty `EdgeReportBacktestCache` DB
- Fixture dataset registry with ≥2 datasets
- A `should_abort` hook (mock or test harness) to interrupt the sweep partway through

**Steps:**
1. Start a sweep call to `run_strategy_comparison_report(..., sub_cache=<cache>)` with a spy on `_run_backtest`
2. Trigger the abort hook after exactly 3 pairs have been published to the cache (e.g., after the first dataset completes)
3. Verify the cache DB now contains exactly 3 rows (3 pairs from the first dataset)
4. Verify spy count equals 3 (three fresh computes)
5. In a new sweep call (same `sub_cache`, same inputs), re-trigger `run_strategy_comparison_report(..., sub_cache=<cache>)`
6. Reset the spy counter
7. Allow the second sweep to complete fully
8. Verify spy records exactly N new calls (N = total eligible pairs minus 3, the already-cached ones)
9. Verify the progress snapshot's `backtests_from_cache` field equals 3
10. Verify the final cache DB contains all eligible pairs

**Expected outcome:** The resumed sweep skips cached pairs and computes only the missing ones; the progress counter accurately reports cache hits.

**Pass criteria:**
- First sweep publishes 3 pairs to cache
- Second sweep recomputes only the remaining pairs (spy count = total pairs - 3)
- `backtests_from_cache` field in progress snapshot equals 3
- Final cache contains all eligible pairs (no duplicates, no gaps)
- Total runtime of both sweeps is faster than a single uncached sweep

---

### TC-7 — Unit: New dataset costs exactly three fresh backtests

**Type:** api  
**Preconditions:**
- Fully-warm `EdgeReportBacktestCache` DB with all pairs for the fixture registry cached
- Ability to register a new dataset (e.g., copy an existing fixture dataset and register it)
- Spy on `_run_backtest` to count fresh compute calls

**Steps:**
1. Verify the cache is fully warm: call `run_strategy_comparison_report(..., sub_cache=<cache>)` and verify spy count equals 0 (all cache hits)
2. Register one additional new dataset (distinct from all pre-existing datasets in the registry)
3. Reset spy counter
4. Call `run_strategy_comparison_report(..., sub_cache=<cache>)` again (same config, but with the new dataset now registered)
5. Verify spy records exactly 3 new calls (one per registered strategy: v1, structure_tape, structure_tape_map)
6. Verify for every pre-existing dataset, spy count remains 0 (cache hits, no recompute)
7. Verify the new dataset's 3 pairs are durably published to the cache

**Expected outcome:** Registering a new dataset costs exactly three fresh backtests (one per strategy), with zero re-computation for pre-existing datasets.

**Pass criteria:**
- Pre-existing pairs remain fully cached (spy count = 0 for those)
- Exactly 3 fresh `_run_backtest` calls for the new dataset (one per strategy)
- New dataset's pairs are durably cached after the sweep
- Next re-run with both datasets uses 100% cache hits (spy count = 0)

---

### TC-8 — Unit: Parallel (--workers 2) equivalence and non-vacuous multi-process proof

**Type:** api  
**Preconditions:**
- Fixture dataset registry with ≥2 datasets
- Two fresh empty `EdgeReportBacktestCache` DB instances (one for sequential, one for parallel run)
- CLI interface to run `python -m app.research.edge_report_compute --workers N`
- Process ID spy to track which worker PIDs were actually used

**Steps:**
1. Run sequential sweep: call `run_strategy_comparison_report(..., workers=None, sub_cache=<cache_seq>)` against the fixture registry
2. Serialize the report with `json.dumps(..., sort_keys=True)` → `report_seq`
3. In a fresh Python process, run the CLI warmer: `python -m app.research.edge_report_compute --workers 2` (pointing to the same fixture registry and a fresh cache DB `cache_par`)
4. Capture the process tree during the CLI run; record all unique worker process IDs used
5. Extract the CLI's emitted report and serialize with `json.dumps(..., sort_keys=True)` → `report_par`
6. Byte-compare: `report_seq == report_par` (should be byte-identical)
7. Verify the process ID spy recorded at least 2 distinct worker PIDs during the parallel run

**Expected outcome:** A 2-worker parallel sweep produces a byte-identical report to a sequential sweep, and the proof is non-vacuous (multiple worker processes actually ran, not a silent sequential fallback).

**Pass criteria:**
- `report_seq` and `report_par` are byte-identical (`json.dumps(..., sort_keys=True)` equality)
- Process ID spy shows ≥2 distinct worker process IDs (proof of parallelism)
- Parallel run completes faster than sequential (wall-clock time comparison, not required for pass but expected)
- No errors or exceptions during parallel execution

---

### TC-9 — Unit: Cache loss (DB deletion) triggers full recompute with byte-identical output

**Type:** api  
**Preconditions:**
- Fully-warm `EdgeReportBacktestCache` DB with all pairs cached
- Spy on `_run_backtest` to count fresh computes
- Ability to delete the cache DB file

**Steps:**
1. Verify the cache is fully warm: call `run_strategy_comparison_report(..., sub_cache=<cache>)` and verify spy count equals 0
2. Serialize the report with `json.dumps(..., sort_keys=True)` → `report_warm`
3. Delete the cache DB file (e.g., `os.remove(cache_path)`)
4. Reset spy counter
5. Call `run_strategy_comparison_report(..., sub_cache=<cache>)` again (same inputs, cache DB is gone)
6. Verify spy records fresh calls for EVERY pair (no cache hits)
7. Serialize the report with `json.dumps(..., sort_keys=True)` → `report_recomputed`
8. Byte-compare: `report_warm == report_recomputed`

**Expected outcome:** Deleting the sub-cache DB forces a full recompute with zero cache hits, and the resulting report is byte-identical to the original warm-cache run.

**Pass criteria:**
- Spy shows 0 calls on warm cache, all pairs cached
- After DB deletion, spy shows fresh calls for every pair
- `report_warm == report_recomputed` (byte-identical)
- No errors or corruption detected during recompute

---

### TC-10 — Unit: CLI warmer's published rows are reusable by bare function calls

**Type:** api  
**Preconditions:**
- Committed fixture dataset registry
- Fresh empty `EdgeReportBacktestCache` DB at the default resolved path (env `TAPEOLOGY_EDGE_SWEEP_CACHE_DB` or sibling of dataset dir)
- Spy on `_run_backtest` to count fresh computes

**Steps:**
1. Run the CLI warmer: `python -m app.research.edge_report_compute` pointing to the fixture registry
2. Verify the warmer completes and publishes pairs to the durable sub-cache DB
3. In a new Python process (or same process, after the CLI finishes), instantiate an `EdgeReportBacktestCache` pointing to the SAME resolved cache DB path
4. Reset spy counter
5. Call `run_strategy_comparison_report(..., sub_cache=<cache>)` with identical inputs
6. Verify spy count equals 0 (all pairs are cache hits)
7. Verify the returned report is byte-identical to the CLI warmer's report (if the warmer printed one)

**Expected outcome:** The durable sub-cache rows published by the CLI are fully reusable by a subsequent bare function call, with zero re-computation.

**Pass criteria:**
- CLI warmer completes without error
- Bare function call reads 100% cache hits (spy count = 0)
- No fresh `_run_backtest` calls needed
- Returned report matches the warmer's output

---

### TC-11 — Unit: EdgeReportComputeManager.trigger() threads real sub_cache and is resumable

**Type:** api  
**Preconditions:**
- `EdgeReportComputeManager` instance with a fresh empty `EdgeReportBacktestCache` passed to `trigger()`
- Fixture dataset registry
- Ability to trigger a partial abort on a second `trigger()` call (e.g., mock `should_abort` after N pairs)
- Spy on `_run_backtest` to count fresh computes

**Steps:**
1. Call `manager.trigger(sub_cache=<cache>)` and allow it to complete fully
2. Verify the cache DB now contains durable rows for eligible pairs
3. In a second call, trigger a fresh `trigger(sub_cache=<cache>)` with a `should_abort` hook set to interrupt after exactly 1 pair from dataset 2
4. Verify the first pair from dataset 2 is published to cache, but the sweep is aborted before completing all of dataset 2
5. In a third call, re-trigger `manager.trigger(sub_cache=<cache>)` with the SAME cache (no abort)
6. Reset spy counter
7. Allow the third call to complete
8. Verify spy records fresh calls only for the remaining pairs (not the already-cached ones)
9. Verify the progress snapshot's `backtests_from_cache` field is greater than 0

**Expected outcome:** The manager threads a real sub_cache, demonstrating resumability across multiple trigger() calls; cached pairs are skipped on re-trigger.

**Pass criteria:**
- First `trigger()` publishes pairs durably to cache
- Third `trigger()` reuses those cached pairs (no re-computation)
- `backtests_from_cache` is strictly greater than 0 in the third call's progress snapshot
- Full convergence: third call completes with all eligible pairs cached or computed

---

### TC-12 — Unit: EdgeReportComputeManager.trigger() never passes workers > 1

**Type:** api  
**Preconditions:**
- Test module with a monkeypatch wrapper on `run_strategy_comparison_report`
- `EdgeReportComputeManager` with a mocked/spy-wrapped `run_strategy_comparison_report`

**Steps:**
1. Monkeypatch/wrap `run_strategy_comparison_report` to capture its kwargs on each call
2. Call `manager.trigger(sub_cache=<cache>)` (no explicit `workers` parameter passed)
3. Allow the trigger to complete
4. Inspect the captured kwargs for all `run_strategy_comparison_report` calls made by `trigger()._work()`
5. Assert that for every captured call, either `workers` is absent OR `workers <= 1` (never `workers > 1`)

**Expected outcome:** The manager never supplies `workers > 1` to the underlying report function, enforcing the scope decision (process-pool parallelism is CLI-only this iteration).

**Pass criteria:**
- All captured `run_strategy_comparison_report` calls from `trigger()` have `workers <= 1` or `workers` absent
- No `workers > 1` is ever passed by the manager
- Test passes with zero assertion failures

---

### TC-13 — Unit: Hooked path byte-identity: sub_cache=None vs warm sub_cache

**Type:** api  
**Preconditions:**
- Fixture dataset registry
- Two identical `EdgeReportBacktestCache` instances (or one that's pre-warmed)

**Steps:**
1. Call `run_strategy_comparison_report(..., sub_cache=None)` with the fixture inputs
2. Serialize report with `json.dumps(..., sort_keys=True)` → `report_no_cache`
3. Warm an `EdgeReportBacktestCache` by running a full sweep: `run_strategy_comparison_report(..., sub_cache=<cache>)` with identical inputs
4. Reset the same cache (clear in-memory hotslot but keep durable rows)
5. Call `run_strategy_comparison_report(..., sub_cache=<cache>)` again (cold hotslot, warm durable DB)
6. Serialize report with `json.dumps(..., sort_keys=True)` → `report_with_cache`
7. Byte-compare: `report_no_cache == report_with_cache`

**Expected outcome:** The presence of a `sub_cache` parameter (even when fully warm) does not alter the bytes of the returned report; the hooked aggregation path is transparent.

**Pass criteria:**
- `report_no_cache == report_with_cache` (byte-identical)
- Both reports contain the same cells, register, summary fields, and gate logic
- No field presence/absence differences

---

### TC-14 — Unit: Frozen foundations and anti-goal compliance

**Type:** api  
**Preconditions:**
- Full backend test suite after iter-5's diff is applied
- Git diff available comparing pre-iter-5 to post-iter-5 state

**Steps:**
1. Run the full backend unit test suite: `pytest apps/backend/tests/ -v`
2. Capture the test results (should be all green, or skip/xfail as before)
3. Run the existing source-introspection guards:
   - `pytest apps/backend/tests/test_backtests.py::test_no_unlisted_dependency_imports -v`
   - `pytest apps/backend/tests/test_backtests.py::test_no_execution_path -v`
   - `pytest apps/backend/tests/test_setups.py::test_setup_methods_use_only_mock_data -v`
   - `pytest apps/backend/tests/test_mcp_server.py::test_advertised_tool_set_is_exactly_capability_6 -v` (verify MCP tool count is still 18)
4. Verify `config.config_fingerprint()` returns `"4d665603569b9dbf"` (unchanged)
5. Run `git diff --stat <pre-iter-5>...HEAD -- apps/backend/app/research/levels.py apps/backend/app/research/tradability.py apps/backend/app/research/backtests.py apps/backend/app/research/bars.py apps/backend/app/research/datasets.py apps/backend/app/research/dataset_index.py apps/backend/app/mcp/__init__.py` and verify zero lines changed in these files
6. Verify no changes to `EdgeReportCache` method bodies (only imports from it are allowed)

**Expected outcome:** All tests pass, frozen foundation files are byte-unchanged, config fingerprint is stable, and anti-goal constraints are met.

**Pass criteria:**
- Full test suite green (or matching pre-iter-5 pass/skip/xfail counts)
- Source-introspection guards all pass without modification
- `config_fingerprint() == "4d665603569b9dbf"`
- Seven frozen foundation files (levels, tradability, backtests, bars, datasets, dataset_index, mcp) have zero diff
- No execution-path or MCP write-surface violations
- No new Config fields added

---

## Summary

**Total test cases:** 14

| Type | Count |
|------|-------|
| Browser | 3 |
| API/Unit | 11 |

**Browser test cases (TC-1, TC-2, TC-3):** Verify J-04's live compute flow, J-01/J-07 regression checks, and error-state rendering against a scoped fixture backend.

**Unit test cases (TC-4 through TC-14):** Prove `EdgeReportBacktestCache` durability, key-component independence, resumability, parallel equivalence with multi-process proof, cache loss harmlessness, CLI/manager wiring, byte-identity, and frozen-foundation compliance.

**Pass criteria summary:**
- All 3 browser tests produce valid screenshots with zero full-page reloads and zero regressions in J-01/J-07 sections
- All 11 unit tests demonstrate cache correctness, determinism, parallel equivalence, manager wiring, and frozen-foundation preservation
- `config_fingerprint` remains `4d665603569b9dbf`, full test suite passes, zero source-guard violations
