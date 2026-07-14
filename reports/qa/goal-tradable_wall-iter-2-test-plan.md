# goal-tradable_wall-iter-2 Functional Test Plan

**Phase:** goal-tradable_wall-iter-2
**Date:** 2026-07-14
**Frontend Present:** no

## Phase Goal

Deliver the touch-event scanner and case-study registry: for each of the 12 panel symbols, scan stored 5m bars against that session's morning tradable map (J-01), emit deterministic band-touch events with `rejected`/`broke`/`chopped` reaction labels and forward returns, and serve them via `GET /research/setups` + `GET /research/setups/{id}` (+ read-only MCP `setups` proxy), with the pinned AAPL 2026-06-22 ~300 event surfacing as `rejected` with negative forward returns.

## Test Cases

### TC-01 — Registry returns ≥15 events across ≥8 panel symbols

**Type:** api
**Preconditions:** 
- Backend is running (uvicorn on port 8301)
- Live store populated with 12-symbol panel 5m bars via `POST /research/bars` (AAPL/MSFT/NVDA/TSLA/AMZN/GOOGL/META/AMD/NFLX/SPY/QQQ/JPM)
- `compute_tradability` endpoint is working (J-01 passing)

**Steps:**
1. Start backend: `uvicorn app.main:app --host 0.0.0.0 --port 8301`
2. Populate live store: loop over 12 panel symbols, fetch and store `1d`/`1h`/`5m` bars via existing `POST /research/bars`
3. Query registry: `curl -s http://localhost:8301/research/setups | jq '.setups | length'`
4. Count distinct symbols in the response: `curl -s http://localhost:8301/research/setups | jq '.setups[].symbol' | sort -u | wc -l`

**Expected outcome:** 
- Registry contains ≥15 total band-touch events
- Events span ≥8 distinct panel symbols

**Pass criteria:** 
- `curl http://localhost:8301/research/setups` returns HTTP 200 with JSON body containing `setups` array
- `setups` array length ≥15
- Unique symbol count ≥8

---

### TC-02 — Pinned AAPL 2026-06-22 event with `rejected` reaction and negative forward returns

**Type:** api
**Preconditions:** 
- Backend running (port 8301)
- Live store contains AAPL 5m bars through at least 2026-06-22
- J-01 tradable map computes successfully for AAPL

**Steps:**
1. Query registry filtered by symbol: `curl -s 'http://localhost:8301/research/setups?symbol=AAPL' | jq -r '.setups[]' | grep -i 2026-06-22`
2. Identify the event on the ~300–302 band (resistance): filter by session date and band class
3. Extract the `reaction` field and forward-return fields
4. Verify reaction is `rejected` and all forward-return values are negative (or zero if measured after session close)

**Expected outcome:** 
- AAPL event exists for 2026-06-22 session on a resistance band
- Reaction classification is `rejected`
- Forward-return fields show negative values (or zero per measurement horizon)

**Pass criteria:** 
- `curl http://localhost:8301/research/setups?symbol=AAPL` returns HTTP 200
- Response body contains ≥1 event with `session` date = 2026-06-22
- That event has `reaction: "rejected"`
- Event's forward-return fields are ≤0 (negative or zero per horizon config)

---

### TC-03 — No-lookahead consecutive-session test

**Type:** api
**Preconditions:** 
- Backend running with committed 5m fixture covering multiple sessions (pre-requisite: fixture extends through 2026-06-22)
- `AAPL_5m_20260601_20260618.json` extended or replaced with a slice through at least 2026-06-22 + forward-return horizon

**Steps:**
1. Scan with `as_of` = end of the full fixture window: `curl -s 'http://localhost:8301/research/setups?symbol=AAPL' > scan_full.json`
2. Record the event count and event IDs for the pinned 2026-06-22 session
3. Rescan with earlier `as_of` (before the pinned session): truncate the fixture or use a parameterized `as_of` param if API supports it; re-run scan
4. Compare: events for sessions up to 2026-06-21 must remain identical; 2026-06-22 events may differ (that session moves from "future" to "past" for the map computation)

**Expected outcome:** 
- Events for sessions strictly before the test boundary remain unchanged
- The consecutive-session map recomputation does not retroactively alter already-emitted events for prior sessions

**Pass criteria:** 
- Event count for 2026-06-18 (or other pre-boundary session) is identical in both scans
- Event IDs and reaction classifications for pre-boundary sessions do not change
- No crash or 500 error on API call

---

### TC-04 — Determinism: repeat scans produce byte-identical output

**Type:** api
**Preconditions:** 
- Backend running
- Store and fixture locked (no new bars added during the test)

**Steps:**
1. Scan with specific query: `curl -s 'http://localhost:8301/research/setups?symbol=AAPL' | jq . > scan_1.json`
2. Wait 2 seconds
3. Repeat: `curl -s 'http://localhost:8301/research/setups?symbol=AAPL' | jq . > scan_2.json`
4. Compare: `diff -u scan_1.json scan_2.json`

**Expected outcome:** 
- Two scans produce byte-identical JSON bodies

**Pass criteria:** 
- `diff scan_1.json scan_2.json` returns no output (exit code 0)
- No random values in response (e.g., timestamps, UUIDs that vary between calls)

---

### TC-05 — REST == MCP byte-identity for `setups` proxy

**Type:** api
**Preconditions:** 
- Backend running with MCP server enabled
- `mcp__tapeology__setups` tool is available (read-only proxy)

**Steps:**
1. GET via REST: `curl -s 'http://localhost:8301/research/setups' | jq . > rest_body.json`
2. Call via MCP: invoke `mcp__tapeology__setups` tool (simulated as a direct call or via Claude MCP bridge)
3. Extract the returned body and normalize JSON: `jq . > mcp_body.json`
4. Compare: `diff -u rest_body.json mcp_body.json`

**Expected outcome:** 
- REST and MCP return identical JSON payloads

**Pass criteria:** 
- `diff rest_body.json mcp_body.json` returns no output
- Both return HTTP 200 / successful MCP result code
- Content is byte-identical (order, keys, values, all fields)

---

### TC-06 — Drill-in endpoint returns event details and handles errors

**Type:** api
**Preconditions:** 
- Backend running
- Registry contains ≥1 event (from TC-01 or fixture)

**Steps:**
1. From TC-01/TC-02, extract a valid setup `id`
2. Drill-in: `curl -s 'http://localhost:8301/research/setups/{id}' | jq .`
3. Verify response contains `band`, `reaction`, `forward_returns`, and `tape_timeline` (present but empty until J-03)
4. Test unknown ID: `curl -s -w "%{http_code}" 'http://localhost:8301/research/setups/invalid-id-xyz' -o /dev/null`
5. Test malformed filter: `curl -s -w "%{http_code}" 'http://localhost:8301/research/setups?reaction=invalid_reaction' -o /dev/null`

**Expected outcome:** 
- Valid ID returns HTTP 200 with complete event details
- `tape_timeline` field is present (but empty/null until J-03)
- Unknown ID returns HTTP 404
- Malformed filter returns HTTP 422

**Pass criteria:** 
- `curl .../setups/{valid-id}` returns HTTP 200 with JSON body containing `band`, `reaction`, `forward_returns`, `tape_timeline`
- `curl .../setups/invalid-id` returns HTTP 404
- `curl .../setups?reaction=invalid` returns HTTP 422 or 400

---

### TC-07 — Reaction classification under intraday density (regression guard)

**Type:** artifact
**Preconditions:** 
- Committed fixture is a realistic multi-session/5m slice (NOT daily-only per iter-1 lesson)
- Fixture includes at least one session with high intraday volume / multiple touches on the same band
- Expected reaction output is documented in test fixture metadata (synthetic guard values)

**Steps:**
1. Load the committed multi-session 5m fixture: `apps/backend/tests/fixtures/yahoo/AAPL_5m_*.json`
2. Run unit test: `pytest apps/backend/tests/test_setups.py::test_reaction_classification_under_intraday_density -v`
3. Verify the fixture contains a shallow high-volume intraday touch that must NOT be misclassified as the daily rejection
4. Assert exact reaction output for that fixture session

**Expected outcome:** 
- Fixture scan produces deterministic reaction labels
- Shallow intraday touch is NOT misclassified as daily rejection (per iter-1 lesson)
- Guard condition catches any regression

**Pass criteria:** 
- Test exits with code 0
- Asserted reaction values match expected (exact-value assertions, not "something returned")
- No intra-day false positives for the pinned session

---

### TC-08 — Symbol with no bar series returns honest empty

**Type:** artifact
**Preconditions:** 
- Backend running
- 12-symbol panel includes at least one symbol with no stored 5m bars (e.g., a symbol never fetched)

**Steps:**
1. Query a symbol with no bars: `curl -s 'http://localhost:8301/research/setups?symbol=UNKNOWN' | jq .`
2. Verify the response is an empty array or explicit empty structure (no crash, no fabricated events)

**Expected outcome:** 
- Query returns HTTP 200 with empty `setups` array or `{setups: []}`
- No 500 error or fabricated events

**Pass criteria:** 
- `curl .../research/setups?symbol=UNKNOWN` returns HTTP 200
- Response body has `setups: []` (or equivalent empty structure)
- No stack trace or error message

---

### TC-09 — Session with zero-band morning map produces no events

**Type:** artifact
**Preconditions:** 
- Committed fixture includes at least one session whose morning tradable map has zero bands (honest output from `compute_tradability` when no daily series exists or no prior session resolves)

**Steps:**
1. In the fixture, identify a session where `compute_tradability` would return `bands: []`
2. Run unit test: `pytest apps/backend/tests/test_setups.py::test_zero_band_map_no_events -v`
3. Assert that the session contributes zero events to the registry

**Expected outcome:** 
- Session with empty morning map is skipped (no events emitted for it)
- No fabricated or placeholder events

**Pass criteria:** 
- Test exits with code 0
- Event count for that session = 0
- No assertion failures

---

### TC-10 — Config fingerprint stability and exclusion-set counter-test

**Type:** artifact
**Preconditions:** 
- `config.py` includes new setup-related constants (panel, reaction definitions, horizons, re-arm rule, retention window)
- All new constants are in the `config_fingerprint` exclusion set
- Counter-test mirrors the tradability pattern in `test_tradability.py`

**Steps:**
1. Run unit test: `pytest apps/backend/tests/test_config.py::test_config_fingerprint_stability -v`
2. Verify `config_fingerprint` = `4d665603569b9dbf` (unchanged)
3. Run counter-test: `pytest apps/backend/tests/test_config.py::test_setup_constants_affect_fingerprint_exclusion -v`
4. Mutate one new setup constant and re-compute fingerprint; verify it stays `4d665603569b9dbf` (proves exclusion works)

**Expected outcome:** 
- Current fingerprint is `4d665603569b9dbf` with new constants added
- Counter-test proves new constants are correctly excluded from fingerprint computation

**Pass criteria:** 
- All fingerprint tests exit with code 0
- Fingerprint value matches `4d665603569b9dbf`
- Counter-test verifies constant exclusion logic

---

### TC-11 — Frozen foundations remain byte-identical

**Type:** artifact
**Preconditions:** 
- Full backend suite can run
- No mutations to `levels.py`, `tradability.py`, `backtests.py`, tape engine, or Alpaca paths expected

**Steps:**
1. Run full suite with diff check: `pytest --tb=short 2>&1 | tee test_output.log`
2. Verify test counts match baseline: 1240 collected, ≥1234 passed, ≤6 skipped
3. Run frozen-foundation guards: `pytest apps/backend/tests/test_frozen_foundations.py -v`
4. Verify tape engine equivalence test: `pytest apps/backend/tests/test_engine_equivalence.py -v` → 22/22 green

**Expected outcome:** 
- No new test failures compared to iter-1 baseline
- `levels.py` and `tradability.py` byte-identical output (no behavior change)
- Tape engine equivalence: 22/22 passing

**Pass criteria:** 
- Exit code 0 for all frozen-foundation tests
- Test count: 1240 collected, ≥1234 passed, ≤6 skipped (zero deletions/weakenings)
- Engine equivalence: 22/22 tests passing

---

### TC-12 — J-01 (tradable map) and J-07 (regression sentinel) remain green

**Type:** artifact
**Preconditions:** 
- J-01 (`tradability.py`) is passing per prior iter-1
- J-07 (regression sentinel) is passing per prior baseline

**Steps:**
1. Run J-01 tests: `pytest apps/backend/tests/test_tradability.py -v`
2. Run J-07 tests: `pytest apps/backend/tests/test_engine_equivalence.py -v`
3. Verify both pass with no regressions

**Expected outcome:** 
- All J-01 tradability tests pass
- All J-07 engine-equivalence tests pass

**Pass criteria:** 
- J-01 test exit code 0
- J-07 test exit code 0
- No new failures or reduced test counts

---

### TC-13 — MCP `setups` tool in EXPECTED_TOOLS and error handling

**Type:** artifact
**Preconditions:** 
- MCP server code is updated to include `setups` tool
- `test_mcp_server.py` includes `setups` in `EXPECTED_TOOLS`
- Error path tests cover backend-down scenario

**Steps:**
1. Run MCP tool tests: `pytest apps/backend/tests/test_mcp_server.py::test_all_tools_listed -v`
2. Verify `setups` appears in `EXPECTED_TOOLS` list
3. Run error handling test: `pytest apps/backend/tests/test_mcp_server.py::test_setups_tool_backend_down -v`
4. Simulate backend down and verify MCP tool returns error (not hung or silent)

**Expected outcome:** 
- `setups` tool is registered in `EXPECTED_TOOLS`
- All tools listed correctly
- Backend-down error handling works

**Pass criteria:** 
- Test exit code 0
- `setups` appears in tools list
- Error test verifies graceful failure mode

---

## Summary

**Total test cases:** 13
**API tests:** 7 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-12)
**Artifact/Unit tests:** 6 (TC-07, TC-08, TC-09, TC-10, TC-11, TC-13)

**Coverage:**
- Registry size and symbol diversity (TC-01)
- Pinned AAPL event correctness (TC-02)
- No-lookahead consecutive-session hazard (TC-03)
- Determinism and reproducibility (TC-04)
- REST == MCP byte-identity (TC-05)
- API error handling (TC-06)
- Reaction classification regression (TC-07)
- Empty cases and honest behavior (TC-08, TC-09)
- Config stability and fingerprint (TC-10)
- Frozen foundations (TC-11)
- Required-still-passing journeys (TC-12)
- MCP integration (TC-13)
