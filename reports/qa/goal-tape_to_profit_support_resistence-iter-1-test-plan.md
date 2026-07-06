# goal-tape_to_profit_support_resistence-iter-1 Functional Test Plan

**Phase:** goal-tape_to_profit_support_resistence-iter-1
**Date:** 2026-07-06
**Frontend Present:** no

## Phase Goal

A multi-timeframe OHLC bar series can be ingested, persisted immutably (checksummed), and read back byte-identically via `GET /research/bars` / `GET /research/bars/{id}` and the MCP `bars` proxy on a committed keyless fixture in CI, while the `default` profile and `v1` remain byte-identical.

## Test Cases

### TC-01 — Bar Store Record and Reload (Byte-Identical)

**Type:** artifact
**Preconditions:** `BarStore` is initialized with a test bar directory; a multi-timeframe bar series exists (symbol, timeframe, UTC window, feed, OHLC candles).

**Steps:**
1. Call `BarStore.record()` to persist the bar series to disk (creates checksummed JSON file).
2. Call `BarStore.load_by_id()` to read the stored series back.
3. Compare the original and reloaded series byte-for-byte.
4. Recompute both checksums (content + whole-file) on load and verify they match stored values.

**Expected outcome:** Stored and reloaded series are byte-identical; both checksums verified without error.
**Pass criteria:** `original_series == reloaded_series` and checksum verification passes on reload.

---

### TC-02 — Bar Store Immutability (Re-record Identical Content Refused)

**Type:** artifact
**Preconditions:** A bar series has been recorded once via `BarStore.record()`.

**Steps:**
1. Call `BarStore.record()` again with identical content (same symbol, timeframe, window, OHLC data).
2. Observe the exception raised.

**Expected outcome:** `BarSeriesAlreadyRegistered` exception is raised.
**Pass criteria:** Exception type is `BarSeriesAlreadyRegistered`.

---

### TC-03 — Bar Store Integrity Check (Corrupt File Detected)

**Type:** artifact
**Preconditions:** A bar series has been recorded to disk.

**Steps:**
1. Manually corrupt the stored JSON file (truncate, alter checksum field, modify OHLC value).
2. Call `BarStore.load_by_id()` to read it back.
3. Observe the exception raised.

**Expected outcome:** `BarSeriesIntegrityError` exception is raised.
**Pass criteria:** Exception type is `BarSeriesIntegrityError`.

---

### TC-04 — Bar Store Empty Window Refusal

**Type:** artifact
**Preconditions:** `BarStore` is initialized.

**Steps:**
1. Attempt to record a bar series with an empty OHLC candle list (no bars in the UTC window).

**Expected outcome:** Record operation fails with an explicit empty-window error.
**Pass criteria:** Exception is raised and message explicitly states empty window.

---

### TC-05 — Bar Store Unknown ID (BarSeriesNotFound)

**Type:** artifact
**Preconditions:** `BarStore` is initialized with no data.

**Steps:**
1. Call `BarStore.load_by_id()` with an unknown ID.

**Expected outcome:** `BarSeriesNotFound` exception is raised.
**Pass criteria:** Exception type is `BarSeriesNotFound`.

---

### TC-06 — GET /research/bars (List Stored Series)

**Type:** api
**Preconditions:** The backend is running; at least one bar series has been recorded.

**Steps:**
1. Execute:
   ```bash
   curl -s http://localhost:8000/research/bars | jq .
   ```
2. Inspect the JSON response for array structure and metadata fields.

**Expected outcome:** HTTP 200; response is an array of bar-series objects, each with symbol, timeframe, UTC window, feed, bar count, and content checksum.
**Pass criteria:** Status code is 200; response contains at least one object with all required fields (symbol, timeframe, start_time, end_time, feed, bar_count, content_checksum).

---

### TC-07 — GET /research/bars/{id} (Read Single Series with OHLC Candles)

**Type:** api
**Preconditions:** The backend is running; a bar series has been recorded and assigned an ID.

**Steps:**
1. Execute:
   ```bash
   curl -s http://localhost:8000/research/bars/{id} | jq .
   ```
   (where `{id}` is from TC-06 response)
2. Inspect the JSON response for metadata and OHLC candle list.

**Expected outcome:** HTTP 200; response includes all bar-series metadata plus an ordered list of OHLC candles (open, high, low, close, volume per candle).
**Pass criteria:** Status code is 200; response contains metadata fields and candles array with at least one candle; each candle has open, high, low, close, volume.

---

### TC-08 — GET /research/bars/{id} (Unknown ID Returns 404)

**Type:** api
**Preconditions:** The backend is running.

**Steps:**
1. Execute:
   ```bash
   curl -s http://localhost:8000/research/bars/nonexistent-id -w "\n%{http_code}" | tail -1
   ```

**Expected outcome:** HTTP 404.
**Pass criteria:** Status code is 404.

---

### TC-09 — POST /research/bars with Missing Credentials (Returns 503)

**Type:** api
**Preconditions:** The backend is running; Alpaca credentials are NOT set in the environment.

**Steps:**
1. Prepare a POST request to record a bar series from a real provider:
   ```bash
   curl -X POST http://localhost:8000/research/bars \
     -H "Content-Type: application/json" \
     -d '{
       "symbol": "AAPL",
       "timeframe": "daily",
       "start": "2024-01-01",
       "end": "2024-12-31"
     }' -w "\n%{http_code}" | tail -1
   ```
2. Observe the HTTP response code.

**Expected outcome:** HTTP 503 (explicit unavailable state).
**Pass criteria:** Status code is 503; response message indicates "real-data provider unavailable — a historical bar recording needs credentials".

---

### TC-10 — POST /research/bars with Out-of-Set Timeframe (Returns 422)

**Type:** api
**Preconditions:** The backend is running.

**Steps:**
1. Execute:
   ```bash
   curl -X POST http://localhost:8000/research/bars \
     -H "Content-Type: application/json" \
     -d '{
       "symbol": "AAPL",
       "timeframe": "invalid_timeframe",
       "start": "2024-01-01",
       "end": "2024-12-31"
     }' -w "\n%{http_code}" | tail -1
   ```

**Expected outcome:** HTTP 422 (validation error).
**Pass criteria:** Status code is 422; response indicates invalid timeframe (never silently coerced).

---

### TC-11 — MCP `bars` Tool (Byte-Identical to GET /research/bars)

**Type:** api
**Preconditions:** The backend is running; MCP server is initialized; at least one bar series has been recorded.

**Steps:**
1. Call the MCP `bars` tool (equivalent to `GET /research/bars`).
2. Call `curl http://localhost:8000/research/bars` directly.
3. Compare the two JSON responses byte-for-byte.

**Expected outcome:** Both responses are identical.
**Pass criteria:** MCP response JSON is byte-identical to REST API response (same structure, values, field order).

---

### TC-12 — MCP `bars` Tool (Backend Down Error)

**Type:** api
**Preconditions:** MCP server is initialized; backend is NOT running.

**Steps:**
1. Stop the backend service.
2. Call the MCP `bars` tool.
3. Observe the error returned.

**Expected outcome:** An explicit tool error is raised naming the base URL.
**Pass criteria:** Error message explicitly names the backend URL and indicates unreachability.

---

### TC-13 — Config Fingerprint Stability (bar_dir Excluded)

**Type:** artifact
**Preconditions:** The project is built; config module is loaded.

**Steps:**
1. Load `config.bar_dir` (verify it's set).
2. Compute `config.config_fingerprint` before and after setting `bar_dir`.
3. Verify that `bar_dir` is in the `excluded` set.
4. Assert fingerprint value is identical whether `bar_dir` is default or overridden.

**Expected outcome:** `bar_dir` is in the `config_fingerprint` excluded set; fingerprint does not change when `bar_dir` is altered.
**Pass criteria:** `bar_dir` appears in `config.config_fingerprint.excluded` list; fingerprint remains constant with different `bar_dir` values.

---

### TC-14 — Config Fingerprint Counter-Test (Real Threshold Moves Fingerprint)

**Type:** artifact
**Preconditions:** The project is built; config module is loaded.

**Steps:**
1. Compute `config.config_fingerprint` with default settings.
2. Change a real (non-excluded) config parameter (e.g., a threshold or toggle).
3. Recompute `config.config_fingerprint`.
4. Compare the two fingerprints.

**Expected outcome:** Fingerprint changes when a real parameter is altered.
**Pass criteria:** Fingerprints differ when a non-excluded config parameter is modified.

---

### TC-15 — Engine Equivalence Suite (Byte-Identical Default Profile)

**Type:** artifact
**Preconditions:** Full test suite is executable (`tests/test_profile_equivalence.py`).

**Steps:**
1. Run:
   ```bash
   pytest tests/test_profile_equivalence.py -v
   ```
2. Inspect all test results.

**Expected outcome:** All tests pass; `default` profile output is byte-identical across test runs.
**Pass criteria:** Exit code 0; all test cases report PASS.

---

### TC-16 — Engine Equivalence Suite (Observer Byte-Identical Default Profile)

**Type:** artifact
**Preconditions:** Full test suite is executable (`tests/test_observer_equivalence.py`).

**Steps:**
1. Run:
   ```bash
   pytest tests/test_observer_equivalence.py -v
   ```
2. Inspect all test results.

**Expected outcome:** All tests pass; observer output for `default` profile is byte-identical.
**Pass criteria:** Exit code 0; all test cases report PASS.

---

### TC-17 — Committed Keyless Fixture (Ingest → Persist → Read in CI)

**Type:** artifact
**Preconditions:** Test suite is executable; committed bar fixture exists under `tests/fixtures/bars/`.

**Steps:**
1. Run the fixture-loading test:
   ```bash
   pytest tests/test_bars.py::test_committed_fixture_pair_loads_through_the_real_store_path_and_replays_keyless -v
   ```
2. Verify the fixture is loaded without credentials.
3. Verify byte-identical re-read.

**Expected outcome:** Test passes; fixture is read keyless (no Alpaca credentials required).
**Pass criteria:** Exit code 0; test reports PASS; fixture covers at least two timeframes.

---

### TC-18 — Frontend Diff Empty (No apps/frontend/ Changes)

**Type:** artifact
**Preconditions:** The implementation is complete.

**Steps:**
1. Execute:
   ```bash
   git diff --stat -- apps/frontend/
   ```

**Expected outcome:** No changes reported.
**Pass criteria:** `git diff -- apps/frontend/` output is empty (no files modified).

---

### TC-19 — Backend Test Suite Passes (No Regressions, J-07 Green)

**Type:** artifact
**Preconditions:** The implementation is complete; full backend test suite is executable.

**Steps:**
1. Run the full backend test suite:
   ```bash
   pytest tests/ -v --tb=short
   ```
2. Inspect for failures and regressions.

**Expected outcome:** All tests pass; J-07 (eras 1–3 sentinel) remains green.
**Pass criteria:** Exit code 0; no test failures; zero regressions in existing tests.

---

## Summary

**Total test cases:** 19
- **API tests:** 6 (TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12)
- **Artifact tests:** 13 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-13, TC-14, TC-15, TC-16, TC-17, TC-18, TC-19)
- **Browser tests:** 0 (Frontend Present: no)

All test cases are driven by the DEFINITION OF DONE and TESTING REQUIREMENTS sections of the phase spec. Tests validate immutability, integrity, honest failure states, byte-identical read-back, config stability, engine equivalence, and zero frontend diff.
