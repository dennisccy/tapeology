# goal-fast_wall-iter-1 Functional Test Plan

**Phase:** goal-fast_wall-iter-1  
**Date:** 2026-07-17  
**Frontend Present:** yes

## Phase Goal

Make `GET /research/edge-report` answer a cold cache with an honest, instant "not computed" payload instead of silently starting the multi-hour backtest sweep inside the page's own request, and surface that state as a distinct panel on `/structure` — so opening the page never risks pinning the backend at ~98% CPU for hours.

## Test Cases

### TC-01 — Cold Cache Returns Not-Computed Payload

**Type:** api  
**Preconditions:**
- Dataset registry has at least 1 registered dataset
- `edge_report_cache.db` has no row for the current cache key
- Backend is running with frozen config fingerprint `4d665603569b9dbf`

**Steps:**
1. Call `GET /research/edge-report` against the running backend
2. Capture HTTP status code and response body

**Expected outcome:** HTTP 200 response with JSON body containing:
- `"status": "not_computed"`
- `"detail"` — a non-empty string describing what triggers compute
- `"dataset_count"` — integer equal to the number of registered datasets
- `"register"` — string equal to `backtests.REGISTER` value
- `"compute"` — null
- NO `pnl_min_sample_size` or `train`/`holdout` cells keys

**Pass criteria:** Response status is 200 and all five fields have the expected types and values; `json.dumps(response.json(), sort_keys=True)` can be re-parsed without error.

---

### TC-02 — Cold Cache Compute-Spy (Zero Calls to Sweep)

**Type:** api  
**Preconditions:**
- Dataset registry has at least 1 registered dataset
- `edge_report_cache.db` has no row for the current cache key
- `_compute_strategy_comparison_report` is wrapped with a counting spy

**Steps:**
1. Reset the compute-call counter to 0
2. Call `GET /research/edge-report`
3. Capture the spy's call count

**Expected outcome:** `GET /research/edge-report` returns HTTP 200 with not-computed payload; compute-spy records exactly 0 calls

**Pass criteria:** Spy call count equals 0 (mechanical proof that no sweep was triggered)

---

### TC-03 — Empty Registry Returns Full Report (Unchanged)

**Type:** api  
**Preconditions:**
- Dataset registry contains 0 registered datasets
- Backend is running

**Steps:**
1. Call `GET /research/edge-report`
2. Capture HTTP status code and response body

**Expected outcome:** HTTP 200 response with the existing full-report shape:
- `"register"` field present
- `"pnl_min_sample_size"` field present
- `"train"` object with `"cells": []`
- `"holdout"` object with `"cells": []`
- `"surviving_train_cells": []`
- NO `status` key in the body

**Pass criteria:** Response is 200, all expected keys are present, no `status` key exists, cells are empty arrays

---

### TC-04 — Warm Cache Byte-Identity

**Type:** api  
**Preconditions:**
- Dataset registry has at least 1 registered dataset
- `EdgeReportCache.compute_and_publish(dataset_store, config, compute_fn)` has been called and a row exists for the current cache key
- A fresh, cache-cleared compute can be performed independently

**Steps:**
1. Call `GET /research/edge-report` (hits warm cache)
2. Capture the response body and assign to `warm_response`
3. Independently perform a fresh compute without using the cache
4. Assign the result to `fresh_response`
5. Compare: `json.dumps(warm_response, sort_keys=True)` vs `json.dumps(fresh_response, sort_keys=True)`

**Expected outcome:** Both JSON strings are identical (byte-for-byte)

**Pass criteria:** The two JSON serializations match exactly after sort-keys normalization

---

### TC-05 — Integrity Error Returns 500

**Type:** api  
**Preconditions:**
- Dataset store's `list()` method is mocked to raise an integrity error
- Backend is running

**Steps:**
1. Call `GET /research/edge-report`
2. Capture HTTP status code and response body

**Expected outcome:** HTTP 500 response with JSON body; `detail` field contains the substring `"integrity"` (exact same behavior as before this iteration)

**Pass criteria:** Status is 500 and "integrity" appears in the `detail` field

---

### TC-06 — MCP Edge-Report Byte-Identity with REST (Not-Computed State)

**Type:** api  
**Preconditions:**
- Cold cache + non-empty dataset registry (preconditions for TC-01)
- MCP `edge_report` tool is available and connected to the same backend
- Backend is running

**Steps:**
1. Call `GET /research/edge-report` via REST and capture raw response body bytes
2. Call the MCP `edge_report` tool and capture raw response bytes
3. Compare the two byte sequences

**Expected outcome:** Raw response bytes are identical between REST and MCP

**Pass criteria:** Byte-for-byte equality (confirms MCP proxy serves the new not-computed shape identically)

---

### TC-07 — Non-GET Verbs Return 405

**Type:** api  
**Preconditions:**
- Backend is running
- `/research/edge-report` endpoint is registered

**Steps:**
1. Send POST request to `/research/edge-report`
2. Send PUT request to `/research/edge-report`
3. Send PATCH request to `/research/edge-report`
4. Send DELETE request to `/research/edge-report`
5. Capture HTTP status code for each verb

**Expected outcome:** All four requests return HTTP 405 Method Not Allowed (unchanged from baseline)

**Pass criteria:** All four verbs return status 405

---

### TC-08 — EdgeReportCache.lookup() on Cache Miss

**Type:** api  
**Preconditions:**
- `EdgeReportCache` instance is initialized
- No hot slot and no durable row exist for the derived key
- A compute-counting wrapper is in place

**Steps:**
1. Call `EdgeReportCache.lookup(records, config)` directly with a cache miss
2. Capture the return value
3. Capture the spy's call count

**Expected outcome:** Method returns `None`; compute spy records 0 calls (no compute function was invoked)

**Pass criteria:** Return value is `None` and spy call count is 0

---

### TC-09 — EdgeReportCache.compute_and_publish() Publishes and Persists

**Type:** api  
**Preconditions:**
- `EdgeReportCache` instance is initialized
- No row exists for the derived key
- A mock `compute_fn` is available that returns a sample report dict

**Steps:**
1. Call `EdgeReportCache.compute_and_publish(dataset_store, config, compute_fn)` with the mock function
2. Capture the returned result
3. Verify the result was published to the durable row by calling `lookup(records, config)` with the same key
4. Capture the lookup result

**Expected outcome:**
- `compute_and_publish` returns the computed result (non-None dict)
- `compute_fn` is called exactly once
- A subsequent `lookup()` call for the same key returns that exact result (byte-identical)

**Pass criteria:** Return value is a dict, function called once, lookup retrieves the same bytes

---

### TC-10 — Shared Cache-DB-Path Resolver (Hermetic)

**Type:** api  
**Preconditions:**
- Environment variable `TAPEOLOGY_EDGE_REPORT_CACHE_DB` is unset
- `TAPEOLOGY_DATASET_DIR` points at a temporary directory with a known path (e.g., `/tmp/test_datasets`)

**Steps:**
1. Call the shared cache-DB-path resolver function with the dataset dir
2. Capture the resolved path

**Expected outcome:** Resolved path equals `<dirname(dataset_dir)>/edge_report_cache.db`

**Pass criteria:** Path matches the expected sibling directory location

---

### TC-11 — Browser: Cold Cache Shows Not-Computed Panel

**Type:** browser  
**Preconditions:**
- Scoped keyless fixture backend is running (not the default real-corpus backend)
- `edge_report_cache.db` has no row for the current cache key
- At least 1 dataset is registered in the fixture
- Frontend is running at the configured URL (e.g., `http://localhost:3000`)

**Steps:**
1. Navigate to `/structure` in Chrome
2. Wait for the page to load and the Edge Report section to render
3. Inspect the DOM for specific text and element presence

**Expected outcome:**
- The Edge Report section is visible
- A panel/message with the text "Edge report not computed yet." is rendered in the DOM
- The text "No edge-report cells yet." does NOT appear in the DOM (that is the warm-empty state)

**Pass criteria:** "Edge report not computed yet." text is visible; "No edge-report cells yet." is absent

---

### TC-12 — Browser: Warm Cache Renders Frozen Empty Text

**Type:** browser  
**Preconditions:**
- Scoped keyless fixture backend is running
- `edge_report_cache.db` has been pre-warmed with a published all-empty-cells report for the current cache key
- Frontend is running

**Steps:**
1. Navigate to `/structure` in Chrome
2. Wait for the Edge Report section to render
3. Inspect the DOM for the frozen empty-state text and register banner

**Expected outcome:**
- The Edge Report section renders with the title "No edge-report cells yet." (the frozen iter-0 baseline text, byte-identical)
- The register banner text appears and matches the baseline
- The page does NOT show "Edge report not computed yet."

**Pass criteria:** Frozen empty-state text and register banner are present and byte-identical to iter-0 baseline (no change to that code path)

---

### TC-13 — Route Wiring Preserves Pinned Depends/cache Signature

**Type:** artifact  
**Preconditions:**
- Source file `apps/backend/app/research/routes.py` exists

**Steps:**
1. Read the source of `GET /research/edge-report` route handler (around lines 2093-2117)
2. Search for the exact strings: `Depends(get_bar_store)`, `Depends(get_dataset_store)`, `Depends(get_edge_report_cache)`, and `cache=cache`

**Expected outcome:** All four strings are present in the route signature and call, exactly as they appear in the test pinning code `test_edge_report_api.py:114-141`

**Pass criteria:** All four required strings are found in the route handler source code

---

### TC-14 — MCP Tool List Unchanged

**Type:** api  
**Preconditions:**
- MCP server is running and connected

**Steps:**
1. Query the MCP server for its complete registered tool list
2. Enumerate all tool names

**Expected outcome:** The tool list contains the same tools as before this iteration; no new compute-related tool has been added

**Pass criteria:** Tool count and names match the baseline (no new tools added)

---

### TC-15 — Config Fingerprint Frozen

**Type:** api  
**Preconditions:**
- Full backend unit/integration test suite has been run to completion
- `config.config_fingerprint()` is called after all tests

**Steps:**
1. Run the full backend test suite: `pytest apps/backend/tests/ -v`
2. Verify all tests pass (0 failures)
3. Call `config.config_fingerprint()` and capture the result

**Expected outcome:** Fingerprint equals `4d665603569b9dbf` (byte-identical to era-5B baseline)

**Pass criteria:** Fingerprint string is exactly `4d665603569b9dbf` and all tests pass with zero failures

---

## Summary

**Total test cases:** 15

**Test breakdown by type:**
- **API tests:** 10 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-15)
- **Browser tests:** 2 (TC-11, TC-12)
- **Artifact checks:** 2 (TC-13, TC-14)

**Critical paths covered:**
- Cold-cache → not-computed payload shape and content (TC-01, TC-11)
- Compute-spy proof of zero sweep invocations (TC-02)
- Empty-registry unchanged behavior (TC-03)
- Warm-cache byte-identity (TC-04)
- Error handling (TC-05)
- REST ↔ MCP proxy byte-identity in new state (TC-06)
- HTTP method enforcement (TC-07)
- Cache layer isolation (`lookup` and `compute_and_publish`) (TC-08, TC-09)
- Path resolver hermetic behavior (TC-10)
- Frontend panel rendering for both cold and warm states (TC-11, TC-12)
- Pinned route wiring preservation (TC-13)
- MCP tool list unchanged (TC-14)
- Config fingerprint frozen (TC-15)

All test cases are derived directly from the phase spec's DEFINITION OF DONE (lines 114-151) and TESTING REQUIREMENTS (lines 129-151).
