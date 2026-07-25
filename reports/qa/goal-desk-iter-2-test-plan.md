# goal-desk-iter-2 Functional Test Plan

**Phase:** goal-desk-iter-2  
**Date:** 2026-07-25  
**Frontend Present:** no

## Phase Goal

Ship the era's first desk compute manager: an honest per-member × per-timeframe bar coverage read off `bar_index`, plus an operator-run, resumable, cancellable bar top-up over the pinned universe snapshot's members that walks store-first through the existing `POST /research/bars` path.

## Test Cases

### TC-01 — Coverage honest-empty state

**Type:** api  
**Preconditions:** No universe snapshot has ever been registered (fresh test-scoped universe dir)

**Steps:**
1. Call `GET /research/desk/coverage`
2. Inspect response status code and payload

**Expected outcome:** HTTP 200 with `universe_snapshot_id: null` and `members: []`  
**Pass criteria:** Status is 200, never 404 or 500; payload contains exactly `{"universe_snapshot_id": null, "members": [], "timeframes": ["1h", "4h", "1d", "1w"]}`

---

### TC-02 — Coverage truth-table: all-missing bars

**Type:** api  
**Preconditions:** Universe snapshot with 5 members exists; bar store is empty

**Steps:**
1. Call `GET /research/desk/coverage`
2. Verify all members are listed with all 4 timeframes reporting `has_bars: false`

**Expected outcome:** Response lists all 5 members; each member's per-timeframe map shows `has_bars == false` for `1h`, `4h`, `1d`, and `1w`  
**Pass criteria:** Exact count = 5 members, each with 4 timeframe entries, all `has_bars == false`

---

### TC-03 — Coverage truth-table: partial bars

**Type:** api  
**Preconditions:** Bar-store fixture with bars for exactly 2 of 5 members across all 4 pinned timeframes; other 3 members have no bars

**Steps:**
1. Call `GET /research/desk/coverage`
2. Verify the 2 covered members report `has_bars: true` for all 4 timeframes
3. Verify the 3 uncovered members report `has_bars: false` for all 4 timeframes

**Expected outcome:** Per-member truth-table matches fixture expectations exactly  
**Pass criteria:** 2 members × 4 timeframes = 8 entries with `has_bars: true`; 3 members × 4 timeframes = 12 entries with `has_bars: false`; no mixed states within a member

---

### TC-04 — Coverage freshness: latest_window_end_utc accuracy

**Type:** api  
**Preconditions:** Bar-store fixture with a known recorded bar series for a covered symbol at a specific `window_end_utc` timestamp

**Steps:**
1. Query the fixture bar store to record the expected `window_end_utc` value
2. Call `GET /research/desk/coverage`
3. Locate the covered symbol in the response and inspect its `latest_window_end_utc` for the matching timeframe

**Expected outcome:** The reported `latest_window_end_utc` matches the fixture value exactly  
**Pass criteria:** String comparison: reported value == fixture value; not rounded, not fabricated, verbatim from `bar_index`

---

### TC-05 — Coverage latency: bar_index reads only

**Type:** api  
**Preconditions:** Bar-store fixture with entries; `bar_index` call counter instrumented

**Steps:**
1. Instrument `bar_index.lookup()` and `BarStore.list()` with call counters
2. Call `GET /research/desk/coverage`
3. Assert zero `BarStore.list()` calls

**Expected outcome:** Coverage read uses only `bar_index` reads; zero full-store-hash operations  
**Pass criteria:** `bar_index` call count ≥ 1; `BarStore.list()` call count == 0

---

### TC-06 — Top-up single-flight and progress tracking

**Type:** api  
**Preconditions:** Fixture universe with 5 members and empty bar store

**Steps:**
1. Call `POST /research/desk/topup/compute`
2. Verify the response contains `started: true` and a compute job snapshot
3. Poll `GET /research/desk/topup/compute` until state reaches `"done"`
4. Inspect the final snapshot's `progress.pairs_total` and outcomes

**Expected outcome:** `pairs_total == 5 * 4 == 20`; exactly 20 outcome entries in `progress.outcomes`; each outcome has `symbol`, `timeframe`, and `outcome` in `{"fetched", "reused", "failed"}`  
**Pass criteria:** Exact pair count = 20; one outcome per pair; state progresses from `"running"` to `"done"`

---

### TC-07 — Store-first reuse: second top-up all-reused

**Type:** api  
**Preconditions:** Completed top-up run (TC-06); vendor-fetch seam instrumented with call counter; same universe snapshot and bar store

**Steps:**
1. Instrument vendor-fetch call counter
2. Call `POST /research/desk/topup/compute` a second time
3. Poll until `state == "done"`
4. Count vendor calls made

**Expected outcome:** Every outcome entry reports `outcome == "reused"`; zero vendor calls  
**Pass criteria:** All 20 outcomes have `outcome: "reused"` exactly; vendor-call counter == 0

---

### TC-08 — Top-up resumability after cancel

**Type:** api  
**Preconditions:** Top-up in progress; able to trigger cancel after M pairs complete (M < 20)

**Steps:**
1. Trigger top-up run via `POST /research/desk/topup/compute`
2. Poll until M pairs are completed
3. Call `POST /research/desk/topup/compute/cancel` to stop the run
4. Verify state transitions to `"cancelled"`
5. Trigger `POST /research/desk/topup/compute` again
6. Poll to completion
7. Inspect outcomes for the resumed run

**Expected outcome:** Resumed run skips the M already-covered pairs (reports `outcome: "reused"` for them with zero vendor calls) and attempts only the remaining pairs  
**Pass criteria:** First M outcomes in resumed run = `"reused"` with no fetch calls; remaining outcomes transition to `"fetched"` or `"failed"` based on vendor availability

---

### TC-09 — Top-up single-flight: concurrent trigger returns same job

**Type:** api  
**Preconditions:** Top-up job in running state

**Steps:**
1. While a top-up is `state == "running"`, call `POST /research/desk/topup/compute` again
2. Inspect the response's `started` flag and job `id`

**Expected outcome:** Response reports `started: false`; job `id` is identical to the in-flight run  
**Pass criteria:** `started == false` exactly; `id` field matches the existing running job

---

### TC-10 — GET-never-computes: coverage and topup GET routes

**Type:** api  
**Preconditions:** Vendor-fetch seam and compute-manager `trigger` instrumented with call counters; fresh state

**Steps:**
1. Call `GET /research/desk/coverage` only
2. Assert no vendor fetch or compute trigger occurs
3. Call `GET /research/desk/topup/compute` (poll call) only
4. Assert no vendor fetch or compute trigger occurs

**Expected outcome:** GET requests never trigger background fetches or compute jobs  
**Pass criteria:** Vendor-call counter == 0; compute-trigger counter == 0 after both GET calls

---

### TC-11 — Suite regression: fingerprint stable, test counts floor

**Type:** artifact  
**Preconditions:** Full backend test suite run after iter-2 diff applied

**Steps:**
1. Run `pytest apps/backend/tests -v`
2. Capture pass count, skip count, and any `Config().config_fingerprint()` value
3. Check fingerprint value under any new desk Config field's non-default override (if added)

**Expected outcome:** Pass count ≥ 1210; skip count ≥ 8; fingerprint == `08e471b10130e1e2`  
**Pass criteria:** Suite output shows pass ≥ 1210 and skip ≥ 8; fingerprint assertion passes unchanged across all code paths

---

### TC-12 — J-01 regression: universe endpoint byte-identical

**Type:** api  
**Preconditions:** Same fixture universe snapshot from iter-1; fresh iter-2 codebase

**Steps:**
1. Call `GET /research/desk/universe`
2. Capture response JSON
3. Compare byte-for-byte with iter-1's baseline capture

**Expected outcome:** Response is byte-identical to iter-1's captured baseline  
**Pass criteria:** Diff shows zero differences in JSON structure, field order, values, or formatting

---

### TC-13 — Kept-route byte-comparison: all 24 GET templates

**Type:** artifact  
**Preconditions:** Pre-iteration captures of 24 kept GET route templates; fixture data dir populated by this iteration's top-up run

**Steps:**
1. Capture all 24 kept GET route templates before iter-2 diff
2. Apply iter-2 diff
3. Repeat captures of all 24 templates against the same (now-populated) data dir
4. Diff the two sets of captures

**Expected outcome:** Every route template returns byte-identical payloads except for label/port comment lines  
**Pass criteria:** Diff shows no value or structure changes; only line-number/comment diffs allowed

---

### TC-14 — Top-up error handling: vendor failure surfaces honestly

**Type:** api  
**Preconditions:** Fixture where one or more bar-fetch attempts will raise `NoDataForWindow`, `VendorTimeout`, or `UnsupportedTimeframe`

**Steps:**
1. Trigger top-up run via `POST /research/desk/topup/compute`
2. Poll until the job completes
3. Inspect the outcome entry for the failed pair

**Expected outcome:** Outcome entry reports `outcome: "failed"` with the error detail preserved verbatim; run continues to remaining pairs; no job abort  
**Pass criteria:** Error detail field is non-null and non-empty; remaining pairs after the failed pair show outcomes; job state is `"done"`, not `"failed"`

---

### TC-15 — Cancel on idle: returns 409

**Type:** api  
**Preconditions:** Compute manager is idle (no job ever run, or last job is terminal)

**Steps:**
1. Verify no job is currently running
2. Call `POST /research/desk/topup/compute/cancel`

**Expected outcome:** HTTP 409 Conflict  
**Pass criteria:** Status code == 409; no exception or 500 error

---

## Summary

**Total test cases:** 15  
**API tests:** 14 (TC-01 to TC-10, TC-12, TC-14, TC-15)  
**Artifact checks:** 2 (TC-11, TC-13)  

**Coverage areas:**
- Coverage endpoint honest-empty, partial, and full states (TC-01–TC-04)
- Coverage latency guarantee (T-4 contract): bar_index-only, no store re-hash (TC-05)
- Top-up compute manager: single-flight, state progression, progress tracking (TC-06, TC-09)
- Store-first reuse and resumability (TC-07, TC-08)
- GET-never-computes rule enforcement (TC-10)
- Error handling and honest failure surfacing (TC-14)
- Regression assurance: fingerprint pin, suite floor, J-01 byte-identity, all-kept-routes (TC-11, TC-12, TC-13)
- Cancel on idle idempotence (TC-15)
