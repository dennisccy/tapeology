# Goal Iteration 2 — Deterministic S/R Levels Functional Test Plan

**Phase:** goal-tape_to_profit_support_resistence-iter-2
**Date:** 2026-07-06
**Frontend Present:** no

## Phase Goal

Implement a deterministic, lookahead-free support/resistance level detection module that, given a symbol and as-of time, returns horizontal level candidates (swing pivots and prior-period extremes) with price, timeframe, type, touch count, and strength via `GET /research/levels` and the read-only MCP `levels` tool.

---

## Test Cases

### TC-01 — Swing pivot detection on committed PG 1h fixture

**Type:** api
**Preconditions:**
- Backend is running
- PG 1h bar series is loaded (9 bars, 2026-06-09T13:00–21:00Z, feed `sip`)
- Config N=1 (pivot lookback, meaning 2N+1=3-bar window)

**Steps:**
1. Call `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z`
2. Filter response for levels with `type: "swing-pivot"` and `timeframe: "1h"`

**Expected outcome:** 
At least two swing-pivot levels returned (a swing-high and a swing-low from the bar series).

**Pass criteria:** 
Response includes swing-pivot level at PG 1h with:
- Bar index 3: high=149.4796 (both neighbours lower)
- Bar index 4: low=148.06 (both neighbours higher)
- Both carry `touch_count ≥ 1` and `strength` computed as timeframe_weight × touch_count

---

### TC-02 — Prior-period extreme extraction on committed PG 1d fixture

**Type:** api
**Preconditions:**
- Backend is running
- PG 1d bar series is loaded (5 bars, early June 2026)
- Config includes per-timeframe weights

**Steps:**
1. Call `GET /research/levels?symbol=PG&as_of=2026-06-10T00:00:00Z` (day 2)
2. Filter response for levels with `type: "prior-period-extreme"` and `timeframe: "1d"`

**Expected outcome:** 
Prior-period levels from day 1's high/low/close are returned as referenceable levels.

**Pass criteria:** 
Response includes prior-period-extreme levels with:
- At least one level from the prior day's daily bar
- Each carries `price`, `timeframe: "1d"`, `type: "prior-period-extreme"`, and `touch_count`

---

### TC-03 — Strength calculation uses config-owned weights

**Type:** api
**Preconditions:**
- Backend is running with known config weights (e.g., `sr_timeframe_weights: {"1h": 1.0, "1d": 2.0}`)
- A non-empty level set for symbol PG, as-of T

**Steps:**
1. Call `GET /research/levels?symbol=PG&as_of=<T>`
2. For each returned level, verify `strength = config_weight[timeframe] × touch_count`

**Expected outcome:** 
Strength field matches the deterministic calculation using config values, not magic numbers.

**Pass criteria:** 
For a level with `timeframe: "1d"`, `touch_count: 2`, and config weight 2.0:
- `strength` must equal exactly 4.0

---

### TC-04 — Lookahead-free proof: level at T unchanged by bars after T

**Type:** api
**Preconditions:**
- Backend is running
- PG bar store is loaded with all committed bars
- Two separate test states: (a) as-of T with bars ≤ T only, (b) as-of T with bars ≤ T and bars after T

**Steps:**
1. Call `GET /research/levels?symbol=PG&as_of=2026-06-09T16:00:00Z` (with full fixture)
2. Manually compute or query levels "as if" only bars ≤ 2026-06-09T16:00:00Z existed
3. Compare the two responses byte-for-byte

**Expected outcome:** 
Both calls return identical JSON (same levels, same order, same precision).

**Pass criteria:** 
Response JSON is byte-identical: 
```
MD5(response_a) == MD5(response_b)
```
No level present in response_a is absent or modified in response_b when time T is held constant.

---

### TC-05 — Byte-identical determinism across independent runs

**Type:** api
**Preconditions:**
- Backend is stopped and restarted
- Same bar fixture is loaded

**Steps:**
1. Call `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z`
2. Restart backend (e.g., kill and re-run uvicorn)
3. Call `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z` again
4. Compare JSON response bodies

**Expected outcome:** 
Two independent runs return the same JSON.

**Pass criteria:** 
```
MD5(run_1_response) == MD5(run_2_response)
```

---

### TC-06 — GET /research/levels route happy path with exact expected values

**Type:** api
**Preconditions:**
- Backend is running
- PG bar series is loaded

**Steps:**
1. Send HTTP GET request: `/research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z`
2. Inspect HTTP status code
3. Inspect response JSON structure and field values

**Expected outcome:** 
HTTP 200 response with a JSON array of level objects.

**Pass criteria:** 
- Status code: 200
- Response is valid JSON
- Each level object contains fields: `price` (number), `timeframe` (string), `type` (enum: "swing-pivot" | "prior-period-extreme"), `touch_count` (integer ≥ 1), `strength` (number)
- Field values match known test data (e.g., exact price for PG swing pivot at index 3)

---

### TC-07 — Honest "no levels found" state for empty result

**Type:** api
**Preconditions:**
- Backend is running
- A symbol+as-of pair with no derivable levels (or a non-existent symbol)

**Steps:**
1. Call `GET /research/levels?symbol=UNKNOWN&as_of=2026-06-09T21:00:00Z`
2. Inspect HTTP status and response body

**Expected outcome:** 
An explicit, distinct "no levels found" error state (not a fabricated empty array masking failure).

**Pass criteria:** 
- Either HTTP 404 with a message like "no levels found" or HTTP 200 with an empty array AND a clear indication this is the expected honest failure state (not a bug)
- Response does NOT contain fabricated levels
- Error message (if any) is explicit and distinct from other failure modes

---

### TC-08 — Malformed/missing as_of parameter returns 422

**Type:** api
**Preconditions:**
- Backend is running

**Steps:**
1. Call `GET /research/levels?symbol=PG` (no `as_of` param)
2. Call `GET /research/levels?symbol=PG&as_of=not-a-timestamp`

**Expected outcome:** 
Both requests are rejected with HTTP 422 (Unprocessable Entity).

**Pass criteria:** 
- Status code: 422
- Error message indicates missing or malformed `as_of` parameter
- No silent default to "now" (which would leak lookahead)

---

### TC-09 — Unknown symbol with zero recorded bar series

**Type:** api
**Preconditions:**
- Backend is running

**Steps:**
1. Call `GET /research/levels?symbol=NONEXISTENT&as_of=2026-06-09T21:00:00Z`
2. Inspect response

**Expected outcome:** 
An explicit state distinct from "no levels found at that as_of" (a symbol with bars but no derivable levels).

**Pass criteria:** 
- Response code and/or message explicitly indicates "no bar series recorded for symbol"
- Not conflated with "bars exist but no levels found"

---

### TC-10 — Out-of-set timeframe in bar series surfaces existing 422 discipline

**Type:** api
**Preconditions:**
- Backend is running
- A bar series with an invalid/unknown timeframe exists in the fixture

**Steps:**
1. Call `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z` with a bar series bearing an unsupported timeframe
2. Inspect response

**Expected outcome:** 
HTTP 422 with an explicit error message.

**Pass criteria:** 
- Status code: 422
- Error message identifies the unsupported timeframe
- Matches existing bar/dataset route error discipline

---

### TC-11 — MCP levels tool output byte-identical to REST endpoint on non-empty result

**Type:** api
**Preconditions:**
- Backend is running with MCP server enabled
- PG bar series is loaded

**Steps:**
1. Call MCP `levels` tool with `symbol: "PG"`, `as_of: "2026-06-09T21:00:00Z"`
2. Call `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z` via HTTP
3. Compare JSON outputs

**Expected outcome:** 
MCP output matches REST response byte-for-byte.

**Pass criteria:** 
```
MD5(mcp_response) == MD5(rest_response)
```

---

### TC-12 — MCP levels tool raises ToolArgumentError on missing symbol/as_of

**Type:** api
**Preconditions:**
- Backend is running with MCP server enabled

**Steps:**
1. Call MCP `levels` tool with only `symbol: "PG"` (missing `as_of`)
2. Call MCP `levels` tool with only `as_of: "2026-06-09T21:00:00Z"` (missing `symbol`)

**Expected outcome:** 
ToolArgumentError is raised before any HTTP call is made.

**Pass criteria:** 
- Error type: ToolArgumentError (or equivalent MCP argument validation)
- Error message indicates missing required parameter
- No HTTP 422 from backend (validation happens client-side in MCP dispatch)

---

### TC-13 — config_fingerprint remains pinned at 4d665603569b9dbf with sr_* fields excluded

**Type:** artifact
**Preconditions:**
- Backend is running or code is analyzed statically

**Steps:**
1. Inspect `apps/backend/app/config.py`
2. Verify all new `sr_*` config fields are added to the `config_fingerprint()` `excluded` set
3. Run or trace `Config().config_fingerprint()`

**Expected outcome:** 
The computed fingerprint remains exactly `4d665603569b9dbf` (unchanged from iter-1).

**Pass criteria:** 
- `Config().config_fingerprint()` returns `"4d665603569b9dbf"`
- A comment rationale (matching existing exclusion style) is present for each excluded `sr_*` field
- Test `test_default_fingerprint_is_pinned_and_unmoved_by_the_new_field` passes

---

### TC-14 — Real-threshold counter-test proves computational config changes still move fingerprint

**Type:** artifact
**Preconditions:**
- Static code analysis or test harness

**Steps:**
1. In a test, temporarily modify a COMPUTATIONAL config field (e.g., an engine tape-logic field, not an excluded S/R field)
2. Recompute `Config().config_fingerprint()`
3. Verify it differs from `4d665603569b9dbf`

**Expected outcome:** 
The fingerprint changes when a tape-logic config field is modified, proving the exclusion is selective and correct.

**Pass criteria:** 
- Test `test_fingerprint_changes_on_tape_config_modification` passes
- Fingerprint value is different from the pinned baseline when a real computational field changes

---

### TC-15 — No magic numbers in levels.py

**Type:** artifact
**Preconditions:**
- Static code analysis of `apps/backend/app/research/levels.py`

**Steps:**
1. Grep `levels.py` for all numeric literals (excluding imports, docstrings, type hints)
2. For each literal found, trace to a config reference

**Expected outcome:** 
Every parameter (pivot lookback N, touch tolerance, weights) is sourced from config, not hard-coded.

**Pass criteria:** 
- Grep test `test_levels_module_parameters_are_config_sourced_no_magic_numbers` passes
- No bare numeric literals for S/R computation (e.g., `window_size = 5` must be `window_size = self.config.sr_pivot_lookback`)

---

### TC-16 — J-01 and J-07 regression sentinel: full backend suite remains green

**Type:** artifact
**Preconditions:**
- Backend test suite is available

**Steps:**
1. Run `pytest apps/backend/tests/` (or the project's full test command)
2. Capture pass/fail counts

**Expected outcome:** 
All tests pass (or show the same pass/skip counts as iter-1 baseline: 1069 passed / 1 skipped).

**Pass criteria:** 
- No new test failures introduced
- `test_observer_equivalence.py` and `test_profile_equivalence.py` remain green (byte-identical `default` profile)

---

### TC-17 — Frontend diff is empty (backend-only iteration)

**Type:** artifact
**Preconditions:**
- Git repository with pre-iteration snapshot

**Steps:**
1. Run `git diff <pre-iteration-snapshot>..HEAD -- apps/frontend/`
2. Inspect output

**Expected outcome:** 
No changes to frontend files.

**Pass criteria:** 
- Command output is empty (no lines added, removed, or modified in `apps/frontend/`)

---

### TC-18 — No anti-goal violation: no lookahead, no ML, no fabrication, MCP read-only

**Type:** artifact
**Preconditions:**
- Code review of levels module and routes

**Steps:**
1. Static scan: verify levels computation uses only bars with timestamp ≤ `as_of`
2. Verify no ML/optimizer patterns in levels.py or config
3. Verify no synthesized/fabricated levels in failure paths
4. Verify MCP levels tool is read-only (no PUT/POST/DELETE, only GET proxy)

**Expected outcome:** 
All anti-goals honored.

**Pass criteria:** 
- No lookahead data leak (e.g., no `max(bars)` over the full series, only `filter(bars, timestamp <= as_of)`)
- No fitted models, no optimizer loops
- Honest error states (empty, not fabricated)
- MCP tool is a read-only proxy (`GET /research/levels`, no mutation endpoints exposed)

---

## Summary

**Total test cases:** 18
- **API tests:** 12 (TC-01 through TC-12)
- **Artifact/static checks:** 6 (TC-13 through TC-18)

**Key correctness properties tested:**
1. Swing-pivot detection on committed fixture with exact expected values
2. Prior-period-extreme extraction on 1d bars
3. Strength calculation using config-owned weights
4. Lookahead-free proof (level at T unchanged by bars after T)
5. Byte-identical determinism across runs
6. REST endpoint happy path with full field validation
7. Honest empty/error states (no fabrication)
8. Route parameter validation (422 on malformed/missing `as_of`)
9. Distinct failure modes (unknown symbol vs no levels found)
10. MCP tool byte-identity and argument validation
11. Config fingerprint stability and selective exclusion
12. No magic numbers in S/R module
13. No regression in J-01/J-07 (backend suite green)
14. Backend-only implementation (empty frontend diff)
15. Anti-goal compliance (lookahead-free, no ML, no fabrication, MCP read-only)
