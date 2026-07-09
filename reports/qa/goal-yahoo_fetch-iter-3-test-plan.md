# goal-yahoo_fetch-iter-3 Functional Test Plan

**Phase:** goal-yahoo_fetch-iter-3  
**Date:** 2026-07-09  
**Frontend Present:** no

## Phase Goal

A repeat fetch of an already-stored `(symbol, timeframe, window)` is served from storage instantly with **no** second Yahoo call via a derived SQLite index, while the canonical JSON `BarStore` stays the one source of truth and the no-param `GET /research/bars` response remains byte-identical.

## Test Cases

### TC-01 — Bar Index Creation and Schema

**Type:** artifact  
**Preconditions:** Backend code builds successfully; `apps/backend/app/research/bar_index.py` exists.

**Steps:**
1. Verify the file `apps/backend/app/research/bar_index.py` exists in the repository.
2. Verify the `BarIndex` class is defined with a constructor accepting a DB path.
3. Verify the class implements methods: `lookup()`, `insert()`, `list()`, `reindex()`.
4. Verify the underlying SQLite schema keyed by `(symbol, timeframe, window_start_utc, window_end_utc)` exists.

**Expected outcome:** The bar index module is in place with the required interface.  
**Pass criteria:** File exists; `BarIndex` class instantiable; all four methods are callable; schema can be inspected via SQLite.

---

### TC-02 — Index Lookup on Miss Returns None

**Type:** api  
**Preconditions:** `bar_index.py` is implemented; an empty or test-isolated index DB is in place.

**Steps:**
1. Initialize a `BarIndex` with a fresh test DB.
2. Call `index.lookup(symbol="AAPL", timeframe="1h", window_start_utc="2026-06-01T00:00:00Z", window_end_utc="2026-06-02T00:00:00Z")`.
3. Observe the return value.

**Expected outcome:** Lookup on a miss returns `None`.  
**Pass criteria:** Return value is `None` (falsy); no exception raised.

---

### TC-03 — Index Insert and Exact-Key Lookup Hit

**Type:** api  
**Preconditions:** Fresh test DB; `BarIndex` initialized.

**Steps:**
1. Call `index.insert(symbol="AAPL", timeframe="1h", window_start_utc="2026-06-01T00:00:00Z", window_end_utc="2026-06-02T00:00:00Z", series_id="ser-001", checksum="abc123", bar_count=24)`.
2. Call `index.lookup(symbol="AAPL", timeframe="1h", window_start_utc="2026-06-01T00:00:00Z", window_end_utc="2026-06-02T00:00:00Z")`.
3. Verify the returned hit object.

**Expected outcome:** Lookup returns the inserted record with `series_id`, `checksum`, and `bar_count` intact.  
**Pass criteria:** Hit object is not `None`; `hit.series_id == "ser-001"`; `hit.checksum == "abc123"`; `hit.bar_count == 24`.

---

### TC-04 — Index Lookup Requires Exact String Match on Window Bounds

**Type:** api  
**Preconditions:** Index contains a record with start/end windows as ISO strings.

**Steps:**
1. Insert a record: `window_start_utc="2026-06-01T00:00:00Z"`, `window_end_utc="2026-06-02T00:00:00Z"`.
2. Attempt lookup with the same values.
3. Attempt lookup with equivalent but textually different ISO strings (e.g., missing leading zero, different timezone representation if applicable).

**Expected outcome:** Exact string match succeeds; any textual deviation fails the lookup.  
**Pass criteria:** Exact match returns hit; variant strings return `None`.

---

### TC-05 — Store-First Cache Hit: Zero Network Calls on Repeat Fetch

**Type:** api  
**Preconditions:** Backend server running; test fixture `tests/fixtures/yahoo/AAPL_1h_20260601_20260603.json` exists; `FakeAdapter` with call-counting is wired via `dependency_overrides`.

**Steps:**
1. First `POST /research/bars` with `{"symbol": "AAPL", "timeframe": "1h", "start": "2026-06-01T00:00:00Z", "end": "2026-06-03T00:00:00Z"}`.
2. Verify response status is 200 and a bar series is returned.
3. Note the `FakeAdapter.fetch_bars_calls` count (should be 1).
4. Second `POST /research/bars` with **identical** parameters.
5. Verify response status is 200.
6. Verify the second response has the same `id` and `checksum` as the first.
7. Verify `FakeAdapter.fetch_bars_calls` count has not incremented (still 1).

**Expected outcome:** Second identical fetch is served from storage; adapter is never called.  
**Pass criteria:** After both requests, `fetch_bars_calls == 1`; second response matches first on `id`/`checksum`; status 200 both times.

---

### TC-06 — Store-First Cache Miss Falls Through to Adapter

**Type:** api  
**Preconditions:** Backend server running; fresh test index; `FakeAdapter` wired.

**Steps:**
1. `POST /research/bars` with `{"symbol": "AAPL", "timeframe": "4h", "start": "2026-06-01T00:00:00Z", "end": "2026-06-03T00:00:00Z"}` (different timeframe, not cached).
2. Verify the adapter's `fetch_bars` is called exactly once.
3. Verify the series is returned and indexed.

**Expected outcome:** On a cache miss, the normal fetch flow runs; adapter is called; index is updated after storage.  
**Pass criteria:** Status 200; `fetch_bars_calls == 1`; returned series is indexed.

---

### TC-07 — Filter: GET /research/bars?symbol=AAPL&timeframe=1h Returns Only Matches

**Type:** api  
**Preconditions:** Backend server; index contains multiple series with different symbols/timeframes.

**Steps:**
1. Pre-populate index with: `(AAPL, 1h, ...)`, `(AAPL, 4h, ...)`, `(MSFT, 1h, ...)`.
2. `GET /research/bars?symbol=AAPL&timeframe=1h`.
3. Verify the response.

**Expected outcome:** Only the `(AAPL, 1h)` series is returned.  
**Pass criteria:** Response contains exactly one series; `series.meta.symbol == "AAPL"` and `series.meta.timeframe == "1h"`.

---

### TC-08 — Filter: symbol-Only Returns All Timeframes for That Symbol

**Type:** api  
**Preconditions:** Index contains `(AAPL, 1h, ...)` and `(AAPL, 4h, ...)`.

**Steps:**
1. `GET /research/bars?symbol=AAPL`.
2. Verify both the 1h and 4h series are in the response.

**Expected outcome:** All AAPL series regardless of timeframe are returned.  
**Pass criteria:** Response count equals 2; all have `symbol == "AAPL"`.

---

### TC-09 — No-Param GET /research/bars Stays Byte-Identical

**Type:** api  
**Preconditions:** Backend running; index populated; known baseline of `GET /research/bars` response before change.

**Steps:**
1. `GET /research/bars` (no query parameters).
2. Capture the full response body.
3. Compare against a cached baseline captured before the index was implemented.

**Expected outcome:** Response is byte-identical to pre-index behavior (still calls `store.list()` verbatim).  
**Pass criteria:** Response bytes match baseline exactly (or within acceptable encoding variance); no filtering applied.

---

### TC-10 — Reindex Rebuilds Index from BarStore.list()

**Type:** api  
**Preconditions:** Index DB populated with records; `BarStore.list()` is healthy; `reindex()` method is implemented.

**Steps:**
1. Call `index.reindex()`.
2. Verify the index is repopulated from `BarStore.list()`.
3. Perform several lookups that were in the old index.

**Expected outcome:** All previously cached lookups are available after reindex.  
**Pass criteria:** Lookups succeed; returned values match pre-reindex data.

---

### TC-11 — Reindex After DB Deletion Reproduces Identical Lookups

**Type:** api  
**Preconditions:** Index DB file exists with populated data; `BarStore` is unchanged.

**Steps:**
1. Perform a lookup and record the result.
2. Delete the index DB file.
3. Call `reindex()` to rebuild.
4. Perform the same lookup again.

**Expected outcome:** Post-reindex lookup returns identical metadata.  
**Pass criteria:** Pre-deletion and post-deletion lookup results are identical (same `series_id`, `checksum`, `bar_count`).

---

### TC-12 — Corrupt Index DB Self-Heals via Reindex

**Type:** api  
**Preconditions:** Index DB exists; `BarStore` is intact.

**Steps:**
1. Call `reindex()` to rebuild the index after corruption (simulated by truncating the DB file or corrupting its header).
2. Perform a lookup for a series known to exist in `BarStore`.

**Expected outcome:** Lookup succeeds after reindex; no stale or fabricated data is returned.  
**Pass criteria:** Lookup returns the correct series; no exception on corrupted DB during reindex; lookups work post-heal.

---

### TC-13 — Store-First Hit Is Checksum-Verified from BarStore

**Type:** api  
**Preconditions:** Backend running; index contains a cached series; `BarStore.get()` is available.

**Steps:**
1. Index lookup returns a `series_id` and `checksum`.
2. Call `BarStore.get(series_id)` to retrieve the full series.
3. Verify the returned series' checksum matches the index metadata.

**Expected outcome:** Served series is checksum-verified against the canonical store.  
**Pass criteria:** Checksum from index equals checksum from `BarStore.get()`; series is intact.

---

### TC-14 — config_fingerprint Remains Unchanged (4d665603569b9dbf)

**Type:** artifact  
**Preconditions:** Backend codebase includes the new `bar_index.py` and all changes.

**Steps:**
1. Call `config.config_fingerprint()` or run the unit test `test_config_fingerprint()`.
2. Compare against the expected value `4d665603569b9dbf`.

**Expected outcome:** Fingerprint is unchanged.  
**Pass criteria:** `config_fingerprint() == "4d665603569b9dbf"`; no new `Config` field was added that wasn't fingerprint-excluded.

---

### TC-15 — Required Journeys J-01, J-02, J-06 Remain Green

**Type:** api  
**Preconditions:** Full backend test suite runs; tests for J-01 (keyless Yahoo fetch), J-02 (multi-timeframe), and J-06 (engine equivalence) are in place.

**Steps:**
1. Run the backend test suite: `pytest apps/backend/tests/ -v`.
2. Filter for test cases tagged or named for J-01, J-02, J-06.
3. Verify all pass.

**Expected outcome:** No regressions in previously passing journeys.  
**Pass criteria:** J-01, J-02, J-06 test suites pass; no tests regressed to FAIL.

---

### TC-16 — Engine Equivalence 22/22 Passes (J-06 Guard)

**Type:** api  
**Preconditions:** Backend test suite includes engine equivalence tests; J-06 defines the 22 expected passing cases.

**Steps:**
1. Run engine equivalence tests (e.g., `pytest apps/backend/tests/test_engine_equivalence.py -v`).
2. Count passing vs. skipped vs. failed.

**Expected outcome:** 22 tests pass; 0 regress to FAIL.  
**Pass criteria:** Passed count equals 22; failed count is 0.

---

### TC-17 — Full Backend Test Suite Passes (No Regressions)

**Type:** api  
**Preconditions:** All backend tests are runnable; baseline from iter-2 is 1183 passed / 6 skipped / 0 failed.

**Steps:**
1. Run `pytest apps/backend/tests/ -v --tb=short` (or the command in `.claude/project-template.md`).
2. Capture test counts: passed, skipped, failed.
3. Compare against baseline.

**Expected outcome:** Test count is stable (≥1183 passed); no new failures.  
**Pass criteria:** Passed ≥ 1183; Failed == 0; skipped ≈ 6 (minor variance acceptable).

---

### TC-18 — Coherence Audit Passes (No COHERENCE-FAIL)

**Type:** artifact  
**Preconditions:** Coherence audit tooling is available; the iteration's dev handoff and all code changes are in place.

**Steps:**
1. Run the coherence-auditor (or equivalent audit) on the iteration's code.
2. Verify the audit report states `COHERENCE-PASS`.

**Expected outcome:** No violations of anti-goals; index owns nothing; single source of truth intact.  
**Pass criteria:** Audit report contains `COHERENCE-PASS` verdict; no "second bar store" or "index as source of truth" violations flagged.

---

### TC-19 — Dev Handoff Exists

**Type:** artifact  
**Preconditions:** Development is complete.

**Steps:**
1. Check for file `docs/handoffs/goal-yahoo_fetch-iter-3-dev.md`.

**Expected outcome:** Handoff file exists and documents the implementation.  
**Pass criteria:** File exists at the specified path; contains implementation notes and test evidence.

---

## Summary

**Total test cases:** 19  
**API tests:** 13 (TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-17)  
**Artifact checks:** 5 (TC-01, TC-14, TC-18, TC-19, and TC-16 categorized as api for suite stats)  
**Backend-integration tests:** 1 (TC-15)
