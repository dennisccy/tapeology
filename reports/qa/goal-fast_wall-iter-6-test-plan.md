# goal-fast_wall-iter-6 Functional Test Plan

**Phase:** goal-fast_wall-iter-6
**Date:** 2026-07-17
**Frontend Present:** yes

## Phase Goal

Implement a durable, restart-surviving cache for `compute_setups`'s multi-minute full-panel touch-event scan, keyed by config content hash and store signature, so a backend restart no longer re-pays the scan cost—closing J-06, the seventh and final Must-have journey of "The Fast Wall" interlude.

## Test Cases

### TC-01 — Restart Simulation: Durable Cache Serves Without Rescanning

**Type:** api
**Preconditions:** 
- Backend running with `compute_setups` already populated in both hot slot and durable cache for a given `(config, store)` pair
- In-process hot slot is clearable via test harness

**Steps:**
1. Call `compute_setups(store, config)` once; record the result and install a call-counting spy on `_run_full_panel_scan`
2. Publish the result to both hot slot (`_SCAN_CACHE`) and durable `SetupsScanCache`
3. Clear the in-process hot slot (simulating a backend restart/process reload)
4. Call `compute_setups(store, config)` again with the same store and config
5. Inspect the spy's call count on `_run_full_panel_scan`
6. Compare the second result to the first via `json.dumps(..., sort_keys=True)`

**Expected outcome:** 
- Call-counting spy records exactly ZERO new calls to `_run_full_panel_scan` (proves durable hit)
- Returned result is byte-identical to the original scan result

**Pass criteria:** Spy call count = 0 AND `json.dumps(result_2, sort_keys=True)` == `json.dumps(result_1, sort_keys=True)`

---

### TC-02 — Content-Hash Key: Equal-Content Distinct-Identity Config Objects Cache-Hit

**Type:** api
**Preconditions:**
- `SetupsScanCache` is warm with an entry for a given config content hash and store signature
- Two Config instances can be constructed with identical field values but different Python object identities

**Steps:**
1. Construct a first `Config(...)` instance and call `compute_setups(store, config_1)`; install spy on `_run_full_panel_scan`
2. Publish result to both hot and durable tiers
3. Clear hot slot
4. Construct a SECOND `Config(...)` instance with identical field values (`id(config_1) != id(config_2)` but all fields equal)
5. Call `compute_setups(store, config_2)` with the new instance
6. Inspect spy call count

**Expected outcome:**
- Call-counting spy records ZERO new calls (proves cache key is derived from config CONTENT, not `id(config)`)
- Returned result matches the first result

**Pass criteria:** Spy call count = 0 AND result identical

---

### TC-03 — Content-Hash Busting: setups_*-Family Field Change Voids Cache

**Type:** api
**Preconditions:**
- `SetupsScanCache` is warm with an entry for Config instance A and store S
- A `setups_*`-family field (e.g., `setups_reaction_threshold_bps`) can be changed on a distinct but otherwise-identical Config instance B

**Steps:**
1. Call `compute_setups(store, config_a)` and publish to both tiers; install spy on `_run_full_panel_scan`
2. Clear hot slot
3. Create `config_b` as an otherwise-identical copy of config_a but with ONE `setups_*`-family field changed (e.g., `setups_reaction_threshold_bps += 1`)
4. Call `compute_setups(store, config_b)`
5. Inspect spy call count

**Expected outcome:**
- Call-counting spy records exactly ONE new call (proves cache key includes the full config CONTENT hash, not just `config_fingerprint()` which excludes `setups_*` families)
- Returned result differs from the first (reflects the field change)

**Pass criteria:** Spy call count = 1 AND result differs from TC-03's original

---

### TC-04 — Store-Signature Busting: New Bar Series Voids Cache

**Type:** api
**Preconditions:**
- `SetupsScanCache` is warm for a store S with one registered "5m" bar series
- A test fixture store allows recording new bar series

**Steps:**
1. Call `compute_setups(store, config)` and publish to both tiers; install spy on `_run_full_panel_scan`
2. Clear hot slot
3. Record a NEW "5m" bar series into the SAME store (changing `_store_signature`)
4. Call `compute_setups(store, config)` again with the unchanged config
5. Inspect spy call count

**Expected outcome:**
- Call-counting spy records exactly ONE new call (proves store signature change busts the cache key)

**Pass criteria:** Spy call count = 1

---

### TC-05 — Cache-Loss Harmless: DB Deletion Recomputes Identically

**Type:** api
**Preconditions:**
- `SetupsScanCache` durable DB file contains at least one published row for a `(config, store)` key
- DB file path is known and accessible

**Steps:**
1. Call `compute_setups(store, config)` and publish to both tiers; record the result
2. Delete the durable cache DB file from disk
3. Clear the hot slot
4. Call `compute_setups(store, config)` again with the unchanged store and config
5. Install spy on `_run_full_panel_scan` and inspect call count
6. Compare the new result to the pre-deletion result via `json.dumps(..., sort_keys=True)`

**Expected outcome:**
- Call-counting spy records exactly ONE new call (proves cache miss triggers full recompute)
- Returned result is byte-identical to pre-deletion result

**Pass criteria:** Spy call count = 1 AND results are byte-identical

---

### TC-06 — Mutation Probe (Non-Vacuous): Durable Hit Returns Wrong Payload Verbatim

**Type:** api
**Preconditions:**
- Hot slot is cleared (simulating restart)
- Durable cache DB is pre-seeded with a row under the EXACT current `(config, store)` key containing a DELIBERATELY WRONG payload (e.g., empty events list or fabricated event ID)

**Steps:**
1. Pre-seed the durable `SetupsScanCache` with a deliberately-wrong events payload under the current cache key (e.g., `{"events": []}` when a real scan would find events, or a fabricated/impossible event record)
2. Call `compute_setups(store, config)` with hot slot already cleared
3. Inspect the returned result

**Expected outcome:**
- `compute_setups` returns the deliberately-wrong stored payload VERBATIM (not a freshly-rescanned correct result)
- This proves the durable-hit code path is genuinely exercised, not dead code silently falling through to a fresh scan

**Pass criteria:** Returned result matches the seeded wrong payload exactly (e.g., `json.dumps(result, sort_keys=True)` == `json.dumps(wrong_payload, sort_keys=True)`)

---

### TC-07 — Frozen Foundations: Guard Tests and Config Fingerprint Unchanged

**Type:** artifact
**Preconditions:**
- Full backend test suite runs after implementing J-06
- Guard-test source files exist at expected locations

**Steps:**
1. Run the full backend suite: `pytest apps/backend/tests/ -v`
2. Verify test passes: `tests/test_setups.py::test_compute_setups_itself_never_touches_the_dataset_store` (`:758-771`)
3. Verify test passes: `tests/test_setups.py::test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes` (`:995-1017`)
4. Verify test passes: `tests/test_mcp_server.py::test_advertised_tool_set_is_exactly_capability_6` (reports 18 tools)
5. Check `Config().config_fingerprint()` value

**Expected outcome:**
- Both guard tests pass with source UNCHANGED in the guarded sense (no "dataset" substring in `compute_setups`/`_run_full_panel_scan`; exactly one `_SCAN_CACHE = (` rebind)
- MCP tool count is still exactly 18
- `Config().config_fingerprint()` is still `4d665603569b9dbf`

**Pass criteria:** All three tests PASS AND fingerprint still `4d665603569b9dbf` AND MCP tool count still 18

---

### TC-08 — Publish Failure Swallowed: Broken Durable Cache Never Blocks Serving

**Type:** api
**Preconditions:**
- `SetupsScanCache` can be constructed against a DB path that cannot be written (e.g., parent directory read-only or file replaced with unparseable content)

**Steps:**
1. Configure `compute_setups` to use an unwritable durable cache (either via `TAPEOLOGY_SETUPS_CACHE_DB` env or by making the resolved path read-only)
2. Call `compute_setups(store, config)` with a fresh config/store pair (cache miss expected)
3. Inspect the returned result
4. Check HTTP response via `GET /research/setups` (e.g., `curl http://localhost:8000/research/setups`)

**Expected outcome:**
- `compute_setups` completes without raising an error (publish failure is swallowed internally)
- Returned result contains the freshly-scanned events list (identical to what `_run_full_panel_scan` alone would produce)
- `GET /research/setups` returns HTTP 200 with the same events list

**Pass criteria:** No exception raised AND HTTP 200 AND response body contains valid events list

---

### TC-09 — Browser: /structure Reaches Ready State, No Loading Panels, Zero Visual Regression

**Type:** browser
**Preconditions:**
- Established scoped backend/frontend pair running on ports 8391/3391
- Environment variables set:
  - `TAPEOLOGY_DATASET_DIR` = a copy of `tests/fixtures/datasets_j03`
  - `TAPEOLOGY_BAR_DIR` = a fresh empty directory (no registered series)
  - `TAPEOLOGY_SETUPS_CACHE_DB` = scoped temp dir (the same location as the edge-report cache DB)
- Frontend loaded at `http://localhost:3391/structure`

**Steps:**
1. Navigate to `http://localhost:3391/structure` (fresh page load)
2. Wait up to 10 seconds for all async sections to render
3. Query the DOM for any element with a testid ending in `-loading` (e.g., `case-studies-loading`, `*-loading`)
4. Inspect the Case Studies section for the `case-studies-empty` state rendering ("No band-touch events scanned yet.")
5. Inspect Tradable Map, Edge Report, Registry, and Comparison sections for content matching iter-5's visual appearance

**Expected outcome:**
- No element with a `-loading`-suffixed testid remains anywhere on the page within 10 seconds of navigation
- Case Studies panel renders the honest `case-studies-empty` state (expected because scoped bar dir is empty; no populated table is the correct outcome)
- Tradable Map, Edge Report, Registry, Comparison sections all render and match iter-5's visual appearance (zero regression)

**Pass criteria:** 
- No `-loading`-suffixed testid present after 10s
- Case Studies shows "No band-touch events scanned yet." text OR `case-studies-empty` testid present
- All other sections render without error AND no visual difference from iter-5 screenshots

---

### TC-10 — Required-Still-Passing Regression: J-01, J-02, J-03, J-04, J-05, J-07 Remain Green

**Type:** api
**Preconditions:**
- Full backend test suite runs after J-06 implementation
- `journey-history.json` tracks the status of each journey

**Steps:**
1. Run the deterministic replay verification suite (the standard full backend test run)
2. Confirm all tests pass with no new failures
3. Cross-reference results against `journey-history.json` to verify J-01, J-02, J-03, J-04, J-05, J-07 remain `passing`
4. Verify no tests were deleted or weakened

**Expected outcome:**
- Full suite green (1517 passed / 7 skipped / 0 failed baseline maintained)
- All required-still-passing journeys show `passing` status in journey-history.json
- No regression detected in any of the six required journeys

**Pass criteria:** Full suite passes AND journey-history.json shows all six required journeys as `passing` AND test count matches or exceeds baseline

---

## Summary

**Total test cases:** 10
**API tests:** 9 (TC-01 through TC-08, TC-10)
**Browser tests:** 1 (TC-09)
**Artifact checks:** 1 (TC-07)

**Coverage:**
- Three-tier lookup mechanism (hot slot → durable → full scan)
- Cache key composition (config content hash + store signature)
- Cache busting scenarios (restart, field change, store change, DB loss)
- Mutation probe for non-vacuous durable-hit verification
- Frozen foundations (guard tests, fingerprint, MCP tool count)
- Error handling (publish failure swallowing)
- Browser verification (no loading panels, visual regression check)
- Full regression suite (required-still-passing journeys)
