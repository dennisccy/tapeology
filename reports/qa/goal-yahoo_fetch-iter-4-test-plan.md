# goal-yahoo_fetch-iter-4 Functional Test Plan

**Phase:** goal-yahoo_fetch-iter-4  
**Date:** 2026-07-09  
**Frontend Present:** no

## Phase Goal

Prove that the existing, frozen era-4 structure module computes **real, non-empty support/resistance levels and A/B/C confluence zones from real Yahoo bars** — `GET /research/levels?symbol=<S>&as_of=<T>` (and the MCP `levels` proxy) populate from stored `feed="yahoo"` data with no second computation path, verified by committed tests and coherence audit.

---

## Test Cases

### TC-01 — Levels populate from committed Yahoo fixture

**Type:** api  
**Preconditions:** 
- Backend is running
- Committed real-Yahoo fixture files exist under `apps/backend/tests/fixtures/yahoo/` (AAPL_1d_20260601_20260604.json and/or AAPL_1h_20260601_20260603.json or a richer real-Yahoo window)
- Fixture is seeded into a temp BarStore via the test helper chain

**Steps:**
1. Load the committed Yahoo fixture(s) into a temporary BarStore using the existing `_load_yahoo_fixture()` / `_yahoo_fixture_dataframe()` / `_install_fake_yahoo_ticker()` helper pattern (or equivalent)
2. Call `compute_levels(store, symbol="AAPL", as_of_epoch=<T>, config)` at a chosen `as_of` timestamp within the fixture's date range
3. Inspect the returned `LevelsResponse` object

**Expected outcome:** 
- `no_bar_series_for_symbol: false`
- `levels` list is non-empty (contains at least one S/R level)
- `confluence_zones` list contains at least one zone with an A/B/C `class` field populated (not null)

**Pass criteria:** All three fields meet their expected state AND exact values are asserted in the committed test (e.g., `assert len(response.levels) > 0 and response.confluence_zones[0].class in ["A", "B", "C"]`)

---

### TC-02 — REST endpoint returns levels on Yahoo fixture

**Type:** api  
**Preconditions:**
- Backend service running on configured port
- Committed Yahoo fixture seeded into temp BarStore
- `symbol=AAPL`, `as_of=<T>` (timestamp within fixture range) as query parameters

**Steps:**
1. Make HTTP GET request: `curl -X GET "http://localhost:8301/research/levels?symbol=AAPL&as_of=<as_of_epoch>" -H "Content-Type: application/json"`
2. Capture HTTP status code and response body

**Expected outcome:**
- HTTP 200 status
- Response JSON contains: `no_bar_series_for_symbol: false`, non-empty `levels`, `confluence_zones` with at least one entry having a non-null `class`

**Pass criteria:** Status is 200 AND JSON structure matches expected shape AND at least one confluence zone has `class` in ["A", "B", "C"]

---

### TC-03 — MCP levels tool returns byte-for-byte identical JSON as REST endpoint

**Type:** api  
**Preconditions:**
- Backend running with MCP `levels` tool exposed
- Committed Yahoo fixture seeded into temp BarStore
- Same `symbol=AAPL`, `as_of=<T>` parameters as TC-02

**Steps:**
1. Call the MCP `levels` tool with `symbol="AAPL"` and `as_of=<as_of_epoch>`
2. Capture the returned JSON object
3. Call the REST `GET /research/levels?symbol=AAPL&as_of=<as_of_epoch>` endpoint
4. Capture the response JSON body
5. Compare the two JSON payloads for exact byte-for-byte equality (serialize both to canonical JSON and diff)

**Expected outcome:**
- MCP tool response JSON is byte-identical to REST endpoint response JSON
- Both contain the same `levels` list, `confluence_zones` list, and `class` values

**Pass criteria:** `assert json.dumps(mcp_response, sort_keys=True) == json.dumps(rest_response, sort_keys=True)` passes

---

### TC-04 — No lookahead: storing a bar after as_of does not change computed levels

**Type:** api  
**Preconditions:**
- Backend running
- Committed Yahoo fixture partially seeded (bars up to and including timestamp T)
- `as_of=T` (or slightly before T)

**Steps:**
1. Compute levels at `as_of=T` with the partial bar set: `levels_before = compute_levels(store, "AAPL", as_of_epoch=T, config)`
2. Store an additional real Yahoo bar with timestamp `T + 1day` (after the as_of boundary)
3. Recompute levels at the same `as_of=T`: `levels_after = compute_levels(store, "AAPL", as_of_epoch=T, config)`
4. Compare the two results

**Expected outcome:**
- `levels_before` and `levels_after` are identical in all fields (same `levels`, same `confluence_zones`, same `class` assignments)
- The bar stored after T does not affect the levels computed as-of T

**Pass criteria:** `assert levels_before == levels_after` (deep equality on the entire response object)

---

### TC-05 — Unrecorded symbol returns honest no_bar_series_for_symbol state

**Type:** api  
**Preconditions:**
- Backend running with committed Yahoo fixture seeded
- Request uses a symbol NOT in the fixture (e.g., symbol="NOTEXIST")

**Steps:**
1. Make HTTP GET request: `curl -X GET "http://localhost:8301/research/levels?symbol=NOTEXIST&as_of=<T>" -H "Content-Type: application/json"`
2. Capture response

**Expected outcome:**
- HTTP 200 status
- Response JSON: `no_bar_series_for_symbol: true`, `levels: []`, `confluence_zones: []`

**Pass criteria:** Status is 200 AND `no_bar_series_for_symbol: true` AND both lists are empty

---

### TC-06 — as_of before symbol's first bar returns empty honest state

**Type:** api  
**Preconditions:**
- Backend running with committed Yahoo fixture seeded (e.g., AAPL bars start 2026-06-01)
- `as_of` parameter is set to a timestamp **before** the fixture's earliest bar

**Steps:**
1. Make HTTP GET request: `curl -X GET "http://localhost:8301/research/levels?symbol=AAPL&as_of=<T_before_first_bar>" -H "Content-Type: application/json"`
2. Capture response

**Expected outcome:**
- HTTP 200 status
- Response JSON: `no_bar_series_for_symbol: false` (the series exists), `levels: []`, `confluence_zones: []` (empty due to as_of truncation, not missing series)

**Pass criteria:** Status is 200 AND `no_bar_series_for_symbol: false` AND both lists are empty (not the "series missing" state)

---

### TC-07 — Malformed symbol parameter returns 422

**Type:** api  
**Preconditions:**
- Backend running

**Steps:**
1. Make HTTP GET request: `curl -X GET "http://localhost:8301/research/levels?symbol=&as_of=1234567890" -H "Content-Type: application/json"`
2. Capture HTTP status code

**Expected outcome:**
- HTTP 422 Unprocessable Entity

**Pass criteria:** Status code is exactly 422

---

### TC-08 — Malformed as_of parameter returns 422

**Type:** api  
**Preconditions:**
- Backend running

**Steps:**
1. Make HTTP GET request: `curl -X GET "http://localhost:8301/research/levels?symbol=AAPL&as_of=notanumber" -H "Content-Type: application/json"`
2. Capture HTTP status code

**Expected outcome:**
- HTTP 422 Unprocessable Entity

**Pass criteria:** Status code is exactly 422

---

### TC-09 — Coherence: research/levels.py unchanged and remains single owner

**Type:** artifact  
**Preconditions:**
- Phase implementation completed
- Dev handoff written at `docs/handoffs/goal-yahoo_fetch-iter-4-dev.md`

**Steps:**
1. Run `git diff HEAD -- apps/backend/app/research/levels.py` (comparing against pre-iteration baseline)
2. Verify no modifications to the file (zero diff output expected)
3. Grep the entire codebase for second `compute_levels` or `compute_confluence_zones` implementations: `grep -r "def compute_levels\|def compute_confluence_zones" apps/backend/app/ --include="*.py" | grep -v "research/levels.py"`
4. Grep for any new levels/zone computation logic in adapters or routes: `grep -r "confluence_zones\|compute_level" apps/backend/app/adapters/ apps/backend/app/research/routes.py --include="*.py" | grep -v "research/levels.py" | grep -v "# " | grep -v "import"`

**Expected outcome:**
- `git diff` output is empty (no changes to `research/levels.py`)
- Grep for second computation paths finds zero results OR only import/reference statements (no new computation logic)
- `research/levels.py` is the sole owner of levels and zones computation

**Pass criteria:** All git diff and grep checks confirm `research/levels.py` is byte-identical to baseline AND no second computation path exists anywhere in the codebase

---

### TC-10 — REST and MCP both call the same compute_levels owner (code inspection)

**Type:** artifact  
**Preconditions:**
- Source code is available at `apps/backend/app/research/routes.py` and `apps/backend/app/mcp/__init__.py`

**Steps:**
1. Read `apps/backend/app/research/routes.py`, locate the `get_levels` function
2. Inspect what function it calls (should be `compute_levels` from `research/levels.py`)
3. Read `apps/backend/app/mcp/__init__.py`, locate the `"levels"` tool definition
4. Inspect what function the tool calls (should be the same `compute_levels`)
5. Verify both reference the same import source

**Expected outcome:**
- `routes.py::get_levels()` calls `compute_levels(...)` from `app.research.levels`
- `mcp/__init__.py` levels tool calls the same `compute_levels(...)` from the same module
- Both paths resolve to the **single owner** in `research/levels.py`

**Pass criteria:** Both code paths converge on a single function call to `research/levels.compute_levels`; no alternative compute paths exist

---

## Summary

| Category | Count | Details |
|----------|-------|---------|
| Total test cases | 10 | TC-01 through TC-10 |
| API tests | 8 | TC-01 (in-memory call), TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08 |
| Artifact checks | 2 | TC-09 (coherence: frozen source + single owner), TC-10 (code convergence) |
| Browser tests | 0 | Frontend Present: no (keyless, backend-verifiable phase) |

**Scope note:** This phase is **verify-and-lock** on real Yahoo bars. All acceptance criteria are backend/API-verifiable on the committed fixture; no frontend capability is in scope. The tests focus on proving that real levels + zones populate from real Yahoo data, REST==MCP agreement, no lookahead leaks, and that no second computation path was introduced anywhere (coherence lock).
