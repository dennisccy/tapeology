# goal-tradable_wall-iter-5 Functional Test Plan

**Phase:** goal-tradable_wall-iter-5  
**Date:** 2026-07-14  
**Frontend Present:** no

## Phase Goal

Resolve two backend-blocking watch-items (B1: recency-boundary disclosure on touch events; B3: memoized scan cache for bounded load times) that must be fixed before J-05 renders `/structure` in iter-6. No journey flips; measurable capability only.

## Test Cases

### TC-01 — Boundary event carries effective horizon + boundary flag

**Type:** api  
**Preconditions:** Backend running; test fixture with a touch event whose reaction horizon is truncated at the last stored bar (`touch_index + horizons[0] >= len(all_bars)`)

**Steps:**
1. Call `GET /research/setups` with the boundary-event fixture
2. Extract the most-recent-session boundary touch event from the response
3. Verify the event's `reaction` field has a definitive label (e.g., `"rejected"`, `"accepted"`)
4. Verify the event's `forward_returns[0].return_fraction` is `None` (truncated horizon-0 return)
5. Verify the event carries `reaction_boundary_truncated: true`
6. Verify the effective reaction horizon is strictly less than `Config.setups_forward_return_horizons_bars[0]` (78)

**Expected outcome:** Boundary event additively discloses the truncated horizon and is flagged as boundary-truncated.

**Pass criteria:** All six checks pass with exact values; the event is NOT dropped or mutated; the definitive reaction is present; the boundary flag is `true`; effective horizon `< 78`.

---

### TC-02 — Non-boundary event byte-identical to pre-change output (AAPL 2026-06-22)

**Type:** api  
**Preconditions:** Backend running; AAPL 5m committed fixture (`tests/fixtures/yahoo/AAPL_5m_20260615_20260630.json`) loaded; the pinned 2026-06-22 event pre-change output recorded (reaction: `"rejected"`, forward returns: `[-0.462%, -4.269%]`, `touch_ts: 2026-06-22T13:30:00Z`)

**Steps:**
1. Call `GET /research/setups` with the AAPL fixture
2. Filter events to the one with `touch_ts == "2026-06-22T13:30:00Z"` and symbol `AAPL`
3. Extract the `reaction`, `forward_returns`, and `touch_ts` fields
4. Verify `reaction_boundary_truncated: false` (non-boundary)
5. Verify the effective reaction horizon equals 78 (full configured horizon)
6. Verify `reaction == "rejected"`, `forward_returns == [-0.462%, -4.269%]`, `touch_ts == "2026-06-22T13:30:00Z"`

**Expected outcome:** Non-boundary event is byte-identical to pre-change output except for the two additive fields.

**Pass criteria:** All six checks pass; `reaction`, `forward_returns`, and `touch_ts` are exact byte-identical values; boundary flag `false`; effective horizon == 78.

---

### TC-03 — Cached setups list equals fresh compute (byte-identity)

**Type:** api  
**Preconditions:** Backend running; BarStore with 12-symbol populated data; cache initially empty

**Steps:**
1. Call `GET /research/setups` (first call, cache miss)
2. Record the full response body (setups list, all events, all fields)
3. Call `GET /research/setups` again (cache hit)
4. Compare the second response byte-for-byte with the first

**Expected outcome:** Cached response is identical to fresh compute.

**Pass criteria:** Response bodies match exactly (same JSON, same field order, same precision).

---

### TC-04 — Cached setup by ID equals fresh compute (byte-identity)

**Type:** api  
**Preconditions:** Backend running; BarStore with populated data; cache initially empty; `setup_id` known from TC-03

**Steps:**
1. Call `GET /research/setups/{id}` with a known setup ID (first call, cache miss)
2. Record the full response body (single setup, all fields including `tape_timeline`)
3. Call `GET /research/setups/{id}` again (cache hit)
4. Compare the second response byte-for-byte with the first

**Expected outcome:** Cached response is identical to fresh compute.

**Pass criteria:** Response bodies match exactly; `tape_timeline` enrichment is present and identical.

---

### TC-05 — Edge report cached compute equals fresh (byte-identity)

**Type:** api  
**Preconditions:** Backend running; BarStore with populated data; cache initially empty

**Steps:**
1. Call `GET /research/edge-report` with a dataset filter (first call, cache miss)
2. Record the full response body (edge report, all cells, all metrics)
3. Call `GET /research/edge-report` again (cache hit)
4. Compare the second response byte-for-byte with the first

**Expected outcome:** Cached response is identical to fresh compute.

**Pass criteria:** Response bodies match exactly (same report cells, same metrics, same precision).

---

### TC-06 — Underlying compute_setups scan runs exactly once per unchanged store

**Type:** api  
**Preconditions:** Backend running; BarStore with populated data; instrumented `compute_setups` with call counter (spy/monkeypatch)

**Steps:**
1. Reset the call counter to 0
2. Call `GET /research/setups` (first read, increments counter)
3. Call `GET /research/setups` again (cached read, does not increment counter)
4. Call `GET /research/setups/{id}` (cached read, does not increment counter)
5. Call `GET /research/edge-report` (cached read, does not increment counter)
6. Verify the call counter equals 1

**Expected outcome:** The full-panel scan runs once on the first request, then cache serves subsequent requests.

**Pass criteria:** Call counter == 1 across all four endpoint calls; no re-scan on repeated reads.

---

### TC-07 — Cache checksum-bust: store mutation triggers re-scan

**Type:** api  
**Preconditions:** Backend running; BarStore with initial populated data; instrumented call counter; cache initially populated

**Steps:**
1. Call `GET /research/setups` to populate cache (call counter == 1)
2. Append a new bar series to the BarStore (mutate store content)
3. Call `GET /research/setups` again (cache key mismatch, re-scan required)
4. Verify the call counter increments to 2
5. Verify the response includes the new series in subsequent scans

**Expected outcome:** Store mutation invalidates the cache and forces a re-scan.

**Pass criteria:** Call counter increments from 1 to 2 after store mutation; cache never serves stale data.

---

### TC-08 — Cache immutable-safety: drill-in enrichment doesn't leak into list

**Type:** api  
**Preconditions:** Backend running; BarStore with populated data; cache initially populated; setup ID known

**Steps:**
1. Call `GET /research/setups/{id}` (enriches with `tape_timeline`, returns single setup object)
2. Record the enriched event fields (especially `tape_timeline`)
3. Call `GET /research/setups` to fetch the list (should return un-enriched events)
4. Extract the same event from the list by ID
5. Verify the list event does NOT contain `tape_timeline` and is un-enriched
6. Verify the list event's other fields match the cached base output (byte-identical)

**Expected outcome:** Drill-in enrichment is not mutated into the shared cache object; list remains un-enriched.

**Pass criteria:** List event lacks `tape_timeline`; list event is byte-identical to the base cached version; no leak from enriched to cached object.

---

### TC-09 — J-03 keyless enrichment unbroken: tape_timeline join exact

**Type:** api  
**Preconditions:** Backend running; DatasetStore with committed fixture slice (`tests/fixtures/datasets_j03/`); BarStore populated; cache in place

**Steps:**
1. Call `GET /research/setups/{id}` with a setup ID from the fixture
2. Extract the `tape_timeline` array
3. Verify the timeline contains the exact joined records from the committed DatasetStore fixture
4. Verify the join keys (timestamps, tape state, event details) are exact-value matches

**Expected outcome:** J-03 keyless enrichment stays unbroken; tape_timeline join is exact to the fixture.

**Pass criteria:** Timeline records are exact-value matches to the committed fixture; no missing or wrong records.

---

### TC-10 — Config fingerprint frozen (4d665603569b9dbf)

**Type:** artifact  
**Preconditions:** Backend running; `apps/backend/app/config.py` loaded

**Steps:**
1. Call the backend's internal `config_fingerprint()` function
2. Compare the returned value to the frozen target: `"4d665603569b9dbf"`

**Expected outcome:** Config fingerprint remains frozen.

**Pass criteria:** Returned fingerprint == `"4d665603569b9dbf"` exactly.

---

### TC-11 — Strategy registry order frozen (v1, structure_tape, structure_tape_map)

**Type:** artifact  
**Preconditions:** Backend running; strategy registry loaded from config

**Steps:**
1. Fetch the strategy registry from the backend config
2. Extract the ordered list of registered strategy names
3. Verify the order is exactly: `["v1", "structure_tape", "structure_tape_map"]`

**Expected outcome:** Registry order stays frozen.

**Pass criteria:** Registry order matches exactly: `v1`, `structure_tape`, `structure_tape_map` in that sequence.

---

### TC-12 — Frozen files absent from diff (only setups.py changed)

**Type:** artifact  
**Preconditions:** Git working tree after implementation; ability to run `git diff --name-only -- apps/`

**Steps:**
1. Run `git diff --name-only -- apps/` to list changed files
2. Filter for `.py` files under `apps/backend/app/research/`
3. Verify the diff includes `setups.py` and its test file(s)
4. Verify the diff does NOT include: `levels.py`, `tradability.py`, `engine/`, `strategies.py`, `bars.py`, `datasets.py`, `adapters/`, `edge_report.py`, `backtests.py`

**Expected outcome:** Only `setups.py` and owned tests changed; all frozen files absent.

**Pass criteria:** Diff shows `setups.py` + tests only; no frozen file in the diff.

---

### TC-13 — Full backend suite passes (no regressions)

**Type:** api  
**Preconditions:** Backend fully built; venv activated; all dependencies installed

**Steps:**
1. Run `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (or full `-v` for diagnostic detail)
2. Capture the exit code and test summary (passed, failed, skipped counts)
3. Verify no test regressions introduced by B1/B3 changes

**Expected outcome:** All backend tests pass; zero failures on J-01, J-02, J-04, J-07 deterministic replays.

**Pass criteria:** Exit code == 0; all tests pass; no new failures vs. baseline.

---

### TC-14 — B1 boundary regression test on populated-store shape

**Type:** api  
**Preconditions:** Backend running; purpose-built boundary test fixture (synthetic or real) that produces a touch event with `touch_index + horizons[0] >= len(all_bars)`

**Steps:**
1. Run the dedicated B1 boundary regression test from `tests/test_setups.py`
2. Verify the test constructs a fixture/shape that reaches the recency boundary
3. Verify the test asserts exact values: definitive `reaction`, horizon-0 `forward_returns[0].return_fraction is None`, `reaction_boundary_truncated is True`, effective horizon `< 78`

**Expected outcome:** Boundary regression test passes with exact values on a real boundary event.

**Pass criteria:** Test passes; boundary event carries all four attributes with correct values; fixture genuinely truncates the horizon.

---

### TC-15 — B1 non-boundary byte-identity test (AAPL 2026-06-22 exact values)

**Type:** api  
**Preconditions:** Backend running; B1 non-boundary byte-identity test in `tests/test_setups.py`

**Steps:**
1. Run the dedicated B1 non-boundary byte-identity test
2. Verify the test asserts the pinned AAPL 2026-06-22 event has exact values:
   - `reaction == "rejected"`
   - `forward_returns == [-0.462%, -4.269%]`
   - `touch_ts == "2026-06-22T13:30:00Z"`
   - `reaction_boundary_truncated == false`
   - Effective horizon == 78

**Expected outcome:** Non-boundary byte-identity test passes with exact recorded values.

**Pass criteria:** Test passes; all five exact-value assertions pass.

---

### TC-16 — B3 cache byte-identity test (all three endpoints)

**Type:** api  
**Preconditions:** Backend running; B3 cache byte-identity test in `tests/test_setups.py` covering `/setups`, `/setups/{id}`, and `edge_report`

**Steps:**
1. Run the B3 byte-identity test suite
2. Verify the test calls each of `/research/setups`, `/research/setups/{id}`, and `edge_report.run_strategy_comparison_report` with both cache-hit and cache-miss scenarios
3. Verify the test asserts cached output == fresh output for each endpoint

**Expected outcome:** All three endpoints return byte-identical results from cache vs. fresh compute.

**Pass criteria:** All byte-identity assertions pass for all three endpoints.

---

### TC-17 — B3 cache computed-once test (spy/monkeypatch precedent)

**Type:** api  
**Preconditions:** Backend running; B3 computed-once test in `tests/test_setups.py` with monkeypatch call counter (mirroring precedent in `test_edge_report.py`)

**Steps:**
1. Run the B3 computed-once test
2. Verify the test instruments the scan body with a call counter
3. Verify the test makes N repeated calls to endpoints (e.g., 3× `/setups`, 2× `/setups/{id}`, 1× edge report)
4. Verify the call counter remains at 1 (scan runs once, cache serves all other reads)

**Expected outcome:** Scan body executes exactly once across all repeated reads.

**Pass criteria:** Call counter == 1 across N endpoint calls; no per-request re-scan.

---

### TC-18 — B3 cache checksum-bust test (store mutation invalidates)

**Type:** api  
**Preconditions:** Backend running; B3 checksum-bust test in `tests/test_setups.py`

**Steps:**
1. Run the B3 checksum-bust test
2. Verify the test populates the cache with the initial store state
3. Verify the test appends a new series to the BarStore
4. Verify the test calls an endpoint again and confirms the cache key (store signature) changed
5. Verify the test asserts a re-scan occurred (call counter incremented)

**Expected outcome:** Appending a series to the store invalidates the cache and forces a re-scan.

**Pass criteria:** Call counter increments when store content changes; no stale cache served.

---

### TC-19 — B3 cache immutable-safety test (enrichment isolation)

**Type:** api  
**Preconditions:** Backend running; B3 immutable-safety test in `tests/test_setups.py`

**Steps:**
1. Run the B3 immutable-safety test
2. Verify the test calls `/setups/{id}` (enriched with `tape_timeline`)
3. Verify the test calls `/setups` (list, un-enriched)
4. Verify the test extracts the same event from the list by ID
5. Verify the test asserts the list event does NOT contain `tape_timeline` and matches the cached base output

**Expected outcome:** Drill-in enrichment is copy-on-write; the shared cache is never mutated by a caller.

**Pass criteria:** List event is un-enriched and byte-identical to the base cached version; no leak.

---

### TC-20 — Unknown reaction filter returns 422 (error handling)

**Type:** api  
**Preconditions:** Backend running; `/research/setups` endpoint with optional `reaction` filter parameter

**Steps:**
1. Call `GET /research/setups?reaction=INVALID_REACTION` with an unknown reaction value
2. Verify the response status code is 422 (Unprocessable Entity)

**Expected outcome:** Unknown filter values are rejected with a 4xx error.

**Pass criteria:** Response status == 422.

---

### TC-21 — Unknown setup_id returns 404 (error handling)

**Type:** api  
**Preconditions:** Backend running; `/research/setups/{id}` endpoint

**Steps:**
1. Call `GET /research/setups/UNKNOWN_ID` with a non-existent setup ID
2. Verify the response status code is 404 (Not Found)

**Expected outcome:** Unknown setup IDs are rejected with a 404.

**Pass criteria:** Response status == 404.

---

### TC-22 — Edge report dataset-integrity failure returns 500 (error handling)

**Type:** api  
**Preconditions:** Backend running; `/research/edge-report` endpoint; a scenario where the DatasetStore fixture is corrupted or missing critical data

**Steps:**
1. Trigger a dataset-integrity failure (e.g., missing tape_timeline data for a required event)
2. Call `GET /research/edge-report` 
3. Verify the response status code is 500 (Internal Server Error)
4. Verify no partial report is returned

**Expected outcome:** Dataset-integrity failures block the entire report and return a 500 error (fail-fast, no partial results).

**Pass criteria:** Response status == 500; no partial edge report in the response.

---

## Summary

**Total test cases:** 22  
**API tests:** 21 (setups endpoints, edge report, cache validation, error handling)  
**Artifact checks:** 1 (config fingerprint, registry order, diff scope)

**Test coverage:**
- B1 recency-boundary disclosure: TC-01, TC-02, TC-14, TC-15
- B3 memoized scan cache: TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-16, TC-17, TC-18, TC-19
- J-03 keyless enrichment regression: TC-09
- Frozen byte-identity re-verification: TC-10, TC-11, TC-12
- Full backend suite + deterministic replay: TC-13
- Error handling: TC-20, TC-21, TC-22

**Success definition:** All 22 test cases pass; backend suite green; zero regressions on J-01/J-02/J-04/J-07 deterministic replay.
