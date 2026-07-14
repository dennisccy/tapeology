# goal-tradable_wall-iter-1 Functional Test Plan

**Phase:** goal-tradable_wall-iter-1  
**Date:** 2026-07-14  
**Frontend Present:** no

## Phase Goal

Deliver the tradable level map backend: a new `GET /research/tradability` endpoint that consumes raw levels from `compute_levels` verbatim, clusters them into ≤10 quality-scored price bands per side, enforces morning-markup as-of discipline (basis = prior completed session close), and serves a byte-identical read-only MCP proxy — distilling AAPL's 1,800 levels into ≤10 bands with the 300.48–302.07 resistance wall ranking top-2.

## Test Cases

### TC-01 — Tradability API returns ≤10 bands total for AAPL 2026-06-22

**Type:** api  
**Preconditions:**
- Backend server running (`http://localhost:8000`)
- AAPL fixture with bars through 2026-06-18 close loaded into bar store
- Config constants for band cap K, band-width scaling, and quality-score weights initialized

**Steps:**
1. Call `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T12:00:00Z` (timestamp inside the 2026-06-22 session)
2. Capture the HTTP status code and response body
3. Parse the JSON response and count total bands across support and resistance

**Expected outcome:** HTTP 200 with a JSON object containing `{"symbol": "AAPL", "as_of": "...", "bands": [...]}` structure

**Pass criteria:**  
Status code = 200 AND response contains exactly ≤10 total bands (sum of support + resistance) AND bands list is non-empty

---

### TC-02 — AAPL 2026-06-22 resistance band contains 300.48–302.07 and ranks top-2 by quality

**Type:** api  
**Preconditions:** Same as TC-01

**Steps:**
1. Call `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T12:00:00Z`
2. Filter response bands to resistance side only (side = "resistance")
3. Sort by quality_score descending
4. Identify the band whose price range encompasses both 300.48 and 302.07
5. Check that band's rank position (1st or 2nd)
6. Verify round_number_flag = true for the 300 level

**Expected outcome:** One resistance band with price_min ≤ 300.48 and price_max ≥ 302.07, ranked 1st or 2nd by quality_score, with round_number_flag = true

**Pass criteria:**  
Exactly one band found with price range [300.48–302.07] AND its rank is ≤ 2 AND round_number_flag = true

---

### TC-03 — Morning-markup as-of resolution: map basis = 2026-06-18 close, not 2026-06-19

**Type:** api  
**Preconditions:** Same as TC-01; 2026-06-19 is a market holiday (no daily bar)

**Steps:**
1. Call `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T14:30:00Z` (during 2026-06-22 session)
2. Extract the resolved basis timestamp (the as-of epoch used internally; inspect via server logs or a debug endpoint if needed)
3. Verify it corresponds to the 2026-06-18 session close
4. Verify no band member or basis timestamp exceeds the 2026-06-18 close

**Expected outcome:** Internal basis resolves to 2026-06-18 close; all member zones and daily bar data are strictly earlier

**Pass criteria:**  
Resolved basis timestamp ≤ 2026-06-18T20:00:00Z (or equivalent close time) AND all member zone timestamps ≤ basis AND no lookahead bar data detected in band members

---

### TC-04 — Repeat-call determinism: identical requests return byte-identical JSON

**Type:** api  
**Preconditions:** Same as TC-01

**Steps:**
1. Call `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T14:30:00Z` and capture full response body as string
2. Wait 1 second
3. Call the same endpoint again with identical params
4. Capture the second response body as string
5. Compare both strings byte-for-byte (including whitespace and key order)

**Expected outcome:** Two identical HTTP 200 responses with byte-identical JSON payloads

**Pass criteria:**  
response_1 == response_2 (exact string match)

---

### TC-05 — REST and MCP proxy byte-identity for same params

**Type:** api  
**Preconditions:**
- Same as TC-01
- MCP server running and the `tradability` tool available
- Direct httpx/curl access to the REST endpoint confirmed working

**Steps:**
1. Call REST `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T14:30:00Z` and capture response body
2. Call MCP `tradability` tool with params `symbol=AAPL` and `as_of=2026-06-22T14:30:00Z`
3. Capture MCP response body
4. Compare both response bodies byte-for-byte

**Expected outcome:** REST response and MCP response are byte-identical JSON

**Pass criteria:**  
REST response body == MCP response body (exact string match)

---

### TC-06 — Frozen levels output unchanged: GET /research/levels byte-identical

**Type:** api  
**Preconditions:**
- Backend with the new tradability module
- A recorded baseline of `GET /research/levels?symbol=AAPL&as_of=2026-06-22T14:30:00Z` output from before iter-1 changes

**Steps:**
1. Call `GET /research/levels?symbol=AAPL&as_of=2026-06-22T14:30:00Z`
2. Capture the full response body
3. Compare against the baseline recorded output

**Expected outcome:** Identical JSON; no change to raw levels or confluence zones

**Pass criteria:**  
Current levels response == baseline levels response (byte-identical)

---

### TC-07 — config_fingerprint remains 4d665603569b9dbf

**Type:** api  
**Preconditions:**
- Backend configured with tradability constants added to fingerprint exclusion set
- Live config_fingerprint can be read via `GET /research/strategies` or a config endpoint

**Steps:**
1. Start the backend server
2. Read the current config_fingerprint value
3. Verify it equals the pinned value `4d665603569b9dbf`

**Expected outcome:** config_fingerprint = `4d665603569b9dbf` (unchanged from era-4)

**Pass criteria:**  
Fingerprint string equals `4d665603569b9dbf`

---

### TC-08 — Missing symbol param returns 422

**Type:** api  
**Preconditions:** Backend running

**Steps:**
1. Call `GET /research/tradability?as_of=2026-06-22T14:30:00Z` (no `symbol` param)
2. Capture HTTP status and error response

**Expected outcome:** HTTP 422 Unprocessable Entity with a validation error message

**Pass criteria:**  
Status code = 422

---

### TC-09 — Malformed as_of param returns 422

**Type:** api  
**Preconditions:** Backend running

**Steps:**
1. Call `GET /research/tradability?symbol=AAPL&as_of=not-a-timestamp`
2. Capture HTTP status and error response

**Expected outcome:** HTTP 422 Unprocessable Entity with an ISO parse error

**Pass criteria:**  
Status code = 422

---

### TC-10 — Symbol with no bar series returns explicit empty map

**Type:** api  
**Preconditions:** Backend running; a symbol with no bar data (e.g., "NOSYMBOL" or a trading halt ticker)

**Steps:**
1. Call `GET /research/tradability?symbol=NOSYMBOL&as_of=2026-06-22T14:30:00Z`
2. Capture the response

**Expected outcome:** HTTP 200 with a JSON object containing empty bands list (honest empty state, not an error or fabricated bands)

**Pass criteria:**  
Status code = 200 AND bands array is empty AND response contains explicit symbol and as_of fields

---

### TC-11 — Symbol with series but no derivable bands returns explicit empty bands

**Type:** api  
**Preconditions:**
- Backend running
- A test symbol with sparse or unstructured bar data (no clusters forming zones)

**Steps:**
1. Call `GET /research/tradability?symbol=SPARSE_TICKER&as_of=2026-06-22T14:30:00Z`
2. Capture the response

**Expected outcome:** HTTP 200 with empty bands list (not an error; represents no tradable structure detected)

**Pass criteria:**  
Status code = 200 AND bands array is empty AND response fields indicate honest empty state

---

### TC-12 — No-lookahead: earlier as_of within same session never pulls future bars

**Type:** api  
**Preconditions:**
- Same AAPL fixture as TC-01
- Two requests for different times within the 2026-06-22 session

**Steps:**
1. Call `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T09:30:00Z` (market open)
2. Capture bands and member zone references
3. Call `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T14:00:00Z` (later same session)
4. Capture bands and member zone references
5. Verify no band member from the second call has a timestamp strictly earlier than the first call's basis

**Expected outcome:** Both requests return valid maps; neither request pulls bar data from the 2026-06-19 session (the market holiday)

**Pass criteria:**  
All member zone timestamps ≤ basis (2026-06-18 close) for both requests AND no lookahead-revealing band change when shifting as_of earlier within the same session

---

### TC-13 — Unit test: band clustering produces correct count and price ranges

**Type:** artifact  
**Preconditions:**
- Unit test file `tests/test_tradability.py` exists
- AAPL fixture loaded with real levels computed

**Steps:**
1. Run `pytest tests/test_tradability.py::test_band_clustering_aapl_fixture -v`
2. Inspect test assertions for band count and price range verification

**Expected outcome:** Test passes; asserts exact band count ≤10 and verifies the 300.48–302.07 resistance band

**Pass criteria:**  
Test passes AND assertions confirm band clustering logic and quality scoring work as specified

---

### TC-14 — Unit test: morning-markup as-of resolution skips holiday

**Type:** artifact  
**Preconditions:**
- Unit test file `tests/test_tradability.py` exists
- Test data including 2026-06-19 market holiday

**Steps:**
1. Run `pytest tests/test_tradability.py::test_morning_markup_as_of_resolution -v`
2. Inspect test for basis calculation when a market holiday precedes the request

**Expected outcome:** Test passes; resolves basis to 2026-06-18 close, not the holiday

**Pass criteria:**  
Test passes AND basis timestamp correctly skips the 2026-06-19 holiday

---

### TC-15 — Unit test: config_fingerprint stability (new constants excluded)

**Type:** artifact  
**Preconditions:**
- Unit test file `tests/test_tradability.py` exists
- config_fingerprint exclusion set includes new tradability constants

**Steps:**
1. Run `pytest tests/test_tradability.py::test_tradability_config_excluded_from_fingerprint -v`
2. Verify test compares old and new fingerprints

**Expected outcome:** Test passes; fingerprint remains `4d665603569b9dbf`

**Pass criteria:**  
Test passes AND fingerprint value == `4d665603569b9dbf`

---

### TC-16 — Unit test: config_fingerprint moves on genuine threshold change (counter-test)

**Type:** artifact  
**Preconditions:**
- Unit test file `tests/test_tradability.py` exists
- A paired counter-test that modifies an existing threshold (e.g., sr_pivot_lookback) and verifies fingerprint changes

**Steps:**
1. Run `pytest tests/test_tradability.py::test_genuine_config_change_updates_fingerprint -v`
2. Verify test modifies a non-excluded config value and checks fingerprint differs

**Expected outcome:** Test passes; fingerprint changes when an existing threshold changes

**Pass criteria:**  
Test passes AND counter-test proves the fingerprint mechanism works (not broken by the exclusion)

---

### TC-17 — Unit test: determinism on identical input

**Type:** artifact  
**Preconditions:**
- Unit test file `tests/test_tradability.py` exists

**Steps:**
1. Run `pytest tests/test_tradability.py::test_tradability_determinism -v`
2. Inspect test that calls tradability twice with identical params and compares serialized output

**Expected outcome:** Test passes; byte-identical JSON produced

**Pass criteria:**  
Test passes AND two identical calls produce the same serialized string

---

### TC-18 — Integration test: levels.py output unchanged (equivalence test)

**Type:** artifact  
**Preconditions:**
- Integration test file `tests/test_levels.py` exists
- Baseline recorded levels output from before tradability was added

**Steps:**
1. Run `pytest tests/test_levels.py -v` (the existing levels equivalence tests)
2. Verify all pass without modification

**Expected outcome:** Existing levels test suite passes; levels.py computation byte-identical

**Pass criteria:**  
All levels tests pass AND no test weakened or deleted

---

### TC-19 — MCP server test: tradability tool validates required params

**Type:** artifact  
**Preconditions:**
- Test file `tests/test_mcp_server.py` exists
- New tradability tool tests added

**Steps:**
1. Run `pytest tests/test_mcp_server.py::test_tradability_missing_symbol -v`
2. Inspect test that calls MCP tradability tool without symbol param

**Expected outcome:** Test passes; MCP returns error or rejects the call (consistent with REST 422)

**Pass criteria:**  
Test passes AND MCP validation matches REST behavior

---

### TC-20 — MCP server test: tradability REST == MCP byte-identity

**Type:** artifact  
**Preconditions:**
- Test file `tests/test_mcp_server.py` exists
- New tradability tool tests added

**Steps:**
1. Run `pytest tests/test_mcp_server.py::test_tradability_rest_mcp_byte_identity -v`
2. Inspect test comparing REST and MCP responses on the AAPL fixture

**Expected outcome:** Test passes; responses are byte-identical

**Pass criteria:**  
Test passes AND assertion confirms REST body == MCP body

---

### TC-21 — Backend suite passes: J-07 regression sentinel

**Type:** artifact  
**Preconditions:**
- Full backend test suite runnable
- All existing tests (observer_equivalence, profile_equivalence, levels, etc.) still present

**Steps:**
1. Run `pytest apps/backend/tests/ -v --tb=short` (full backend suite)
2. Capture test summary (passed / skipped / failed count)
3. Compare against baseline (expected ~1207 collected, 1201 passed, 6 skipped per plan)

**Expected outcome:** Full suite passes; no regressions; equivalence tests (7/7 observer, 15/15 profile) remain green

**Pass criteria:**  
Exit code = 0 AND test count matches baseline (no tests deleted or weakened) AND equivalence tests all pass

---

### TC-22 — Artifact check: tradability.py exists and contains no pivot/extreme re-detection

**Type:** artifact  
**Preconditions:** Implementation complete

**Steps:**
1. Read `apps/backend/app/research/tradability.py`
2. Search for patterns: "pivot", "extreme", "detect", "_find", "_identify" (case-insensitive)
3. Verify no level-detection logic; confirm it only calls `compute_levels` and post-processes its output

**Expected outcome:** File exists; no pivot/extreme detection code found; consumes `compute_levels` verbatim only

**Pass criteria:**  
File exists AND no pivot/extreme detection logic found AND contains calls to `compute_levels`

---

### TC-23 — Artifact check: config.py has tradability constants in exclusion set

**Type:** artifact  
**Preconditions:** Implementation complete

**Steps:**
1. Read `apps/backend/app/config.py`
2. Find the `config_fingerprint` exclusion set (around line 1494-1518)
3. Verify new tradability constants (band cap K, band-width scaling, quality-score weights, round-number rule) are listed in the exclusion

**Expected outcome:** File modified; new constants present and excluded from fingerprint calculation

**Pass criteria:**  
Exclusion set includes all new tradability-related constants by name

---

### TC-24 — Artifact check: routes.py has GET /research/tradability endpoint

**Type:** artifact  
**Preconditions:** Implementation complete

**Steps:**
1. Read `apps/backend/app/research/routes.py`
2. Find the `get_tradability` or equivalent route function
3. Verify it mirrors `get_levels` pattern: parses ISO as_of, handles 422s, returns verbatim module output

**Expected outcome:** Endpoint function exists; mirrors get_levels pattern

**Pass criteria:**  
Route defined AND mirrors get_levels (parses ISO once, returns verbatim, 422 on error)

---

### TC-25 — Artifact check: mcp/__init__.py has tradability tool with two required params

**Type:** artifact  
**Preconditions:** Implementation complete

**Steps:**
1. Read `apps/backend/app/mcp/__init__.py`
2. Find `tradability` in TOOLS list and tool definitions
3. Verify two required params: symbol and as_of
4. Confirm it mirrors the `levels` tool pattern (lines 107-108, 309-316 precedent)

**Expected outcome:** Tool defined; two required params; mirrors levels pattern

**Pass criteria:**  
Tool `tradability` exists in TOOLS AND has exactly 2 required params (symbol, as_of) AND implementation mirrors `levels` tool

---

### TC-26 — Artifact check: dev handoff exists at docs/handoffs/goal-tradable_wall-iter-1-dev.md

**Type:** artifact  
**Preconditions:** Implementation complete

**Steps:**
1. Check file exists: `docs/handoffs/goal-tradable_wall-iter-1-dev.md`
2. Verify it contains summary of changes, test results, and any known issues

**Expected outcome:** File exists and documents the iteration's work

**Pass criteria:**  
File exists AND contains non-empty handoff summary

---

## Summary

**Total test cases:** 26  
**API tests:** 13 (TC-01 through TC-12, plus TC-19–TC-20 partial)  
**Artifact checks:** 10 (TC-13 through TC-18, TC-22 through TC-26)  
**Unit/integration tests (implicit via TC-13–TC-21):** 9  

**Test Coverage:**
- Band clustering and quality scoring (TC-01, TC-02, TC-13)
- Morning-markup as-of resolution (TC-03, TC-14)
- Determinism and idempotency (TC-04, TC-17)
- REST ↔ MCP byte-identity (TC-05, TC-20)
- Frozen levels (TC-06, TC-18)
- Config fingerprint stability and counter-test (TC-07, TC-15, TC-16)
- Error cases (TC-08, TC-09, TC-19)
- Honest empty states (TC-10, TC-11)
- No-lookahead constraint (TC-12)
- Code review checks: no re-detection, config exclusions, route pattern, MCP proxy (TC-22–TC-25)
- Regression sentinel: full suite + equivalence (TC-21)
- Handoff artifact (TC-26)

All test cases derive directly from the phase spec DEFINITION OF DONE and TESTING REQUIREMENTS sections. Frontend Present = no, so no browser tests; backend-only validation via API + unit + artifact checks.
