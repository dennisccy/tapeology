# goal-desk-iter-6 Functional Test Plan

**Phase:** goal-desk-iter-6  
**Date:** 2026-07-26  
**Frontend Present:** yes

## Phase Goal

An operator on `/desk` can click a past recorded screen to view its exact snapshot (no recompute), and click any briefing row to navigate to `/structure` with that symbol and as-of already loaded and rendered.

## Test Cases

### TC-01 — Click history row renders past snapshot verbatim

**Type:** browser  
**Preconditions:**
- Backend running with committed fixture desk screens (2026-06-22 and 2026-07-25 snapshots exist)
- `/desk` page loaded, displaying the latest screen with history list visible
- Test backend isolated in a fixture-scoped data root (not ambient `.data/`)

**Steps:**
1. Locate the history-list row dated 2026-06-22
2. Click that row
3. Wait for page to re-render
4. Capture screenshot showing the rendered desk briefing table

**Expected outcome:**
- Page displays exactly the 2026-06-22 snapshot's own rows
- AAPL row present with values: `band_class: A`, `distance_bps: 0.33523150389608725`, `price_low: 298.02`, `price_high: 300.1001`
- Skipped row count matches the snapshot's original `skipped` count
- All row data field-for-field identical to `GET /research/desk/screen?date=2026-06-22` JSON response
- No POST request issued (only GET to fetch the dated snapshot)

**Pass criteria:** Screenshot shows AAPL row with exact values; network log shows only one GET to `/research/desk/screen?date=2026-06-22`, no POST/compute requests.

---

### TC-02 — Latest control reverts to top-level snapshot

**Type:** browser  
**Preconditions:**
- Previous state from TC-01: 2026-06-22 past snapshot is currently displayed
- Latest control is visible on the page

**Steps:**
1. Click the "Latest" control/button
2. Wait for page to re-render
3. Capture screenshot

**Expected outcome:**
- Page reverts to displaying the top-level `latest` snapshot from the initial `GET /research/desk/screen` call
- Rendering is identical to the pre-TC-01 state (same AAPL row values, same skipped count as the most recent screen)
- No new API call issued (the `latest` snapshot is already in memory from the initial page load)

**Pass criteria:** Screenshot matches the initial page-load state before TC-01; no network request is made (only a local state change).

---

### TC-03 — Briefing row click navigates to /structure with prefill and auto-load

**Type:** browser  
**Preconditions:**
- 2026-06-22 snapshot is displayed (from TC-01)
- AAPL row is visible in the briefing table
- Test backend isolated in fixture-scoped root with seeded `screen-2026-06-22` snapshot and real AAPL bars

**Steps:**
1. Locate the AAPL row in the displayed briefing
2. Click any clickable part of that row (symbol name or row link)
3. Verify browser URL and wait for Structure page to load
4. Wait for the load to complete (bands/zones rendered)
5. Capture screenshot of the loaded Structure page

**Expected outcome:**
- Browser navigates to `/structure?symbol=AAPL&asof=2026-06-22T23:59:59Z`
- Symbol input field shows "AAPL"
- As-of input field shows "2026-06-22T23:59:59Z"
- Load has already executed automatically (not awaiting manual Load button click)
- Tradable-map bands are rendered, covering the 298.02–300.1001 price region
- Chart displays correctly with no blank/loading state

**Pass criteria:** URL parameters match exactly; input fields show correct values; bands covering 298.02–300.1001 are visible in screenshot; no manual Load button click was needed.

---

### TC-04 — /structure with no query params shows empty default state

**Type:** browser  
**Preconditions:**
- Fresh navigation to `/structure` with no query parameters

**Steps:**
1. Navigate to `/structure` (or click Structure in nav without any prior context)
2. Wait for page to fully render
3. Capture screenshot of the page state

**Expected outcome:**
- Symbol input field is empty
- As-of input field is empty
- No load has been triggered automatically
- Rendered state is pixel-identical to the pre-iteration baseline (empty/default with no chart data, Load form visible)
- All controls and layout unchanged from the shipped version

**Pass criteria:** Screenshot matches the known pre-iteration baseline; input fields are both empty; no chart data or bands are rendered.

---

### TC-05 — Guard test: desk page has no tradability/levels recompute calls

**Type:** artifact  
**Preconditions:**
- Source file `apps/frontend/app/desk/page.tsx` is available

**Steps:**
1. Read the entire source of `apps/frontend/app/desk/page.tsx`
2. Search for string patterns: `/research/tradability`, `/research/levels`, `compute_tradability`, `compute_levels`
3. Count the number of matches

**Expected outcome:**
- Zero matches found for any of the four patterns
- Confirms that desk page numbers are read only from the already-fetched screen snapshot, never recomputed

**Pass criteria:** `grep -E "(/research/tradability|/research/levels|compute_tradability|compute_levels)" apps/frontend/app/desk/page.tsx` returns no output.

---

### TC-06 — Guard test: /structure prefill calls existing load function

**Type:** artifact  
**Preconditions:**
- Source files available: `apps/frontend/app/structure/page.tsx`

**Steps:**
1. Read the new `/structure` prefill code (the useSearchParams hook + mounted prefill logic)
2. Trace the function call when both symbol and asof params are present
3. Verify it calls the existing `handleLoad` or `handleSubmit` function
4. Confirm no new fetch/compute function is introduced in the prefill code path

**Expected outcome:**
- The prefill code reads `useSearchParams()` to get `symbol` and `asof`
- When both params are present and non-empty, it calls the same `handleLoad` function already used by the manual Load button
- No second fetch, no compute function, no new API helper is called
- The function reference matches exactly the existing load path

**Pass criteria:** Code inspection shows a call to `handleLoad()` (or `handleSubmit()` which calls `handleLoad()`) when both params are present; no other fetch/compute function is invoked.

---

### TC-07 — J-04.json step 5 is no longer a write action

**Type:** artifact  
**Preconditions:**
- File `runs/goal-session-desk/journey-scripts/J-04.json` has been modified per spec requirements

**Steps:**
1. Read `J-04.json` and locate step 5
2. Verify that step 5 is NOT a click action on testid matching `run-screen`, `desk-run-screen-button`, or `topup`
3. Replay J-04.json against a fresh, fixture-scoped backend
4. Count the number of files in the backend's screen-store before the replay
5. Run the replay
6. Count the number of files in the backend's screen-store after the replay
7. Verify counts are identical

**Expected outcome:**
- Step 5 is replaced with read-only `expect`/assertion actions (not a click)
- The journey-script no longer writes a new screen snapshot when replayed
- Backend's screen-store file count before = file count after
- The golden can be replayed against any backend (including non-disposable ones) without side effects

**Pass criteria:** `J-04.json` step 5 contains no `click` action on `run-screen` or `topup` testids; screen-store file count is unchanged after replay.

---

### TC-08 — Backend suite passes with frozen fingerprint

**Type:** api  
**Preconditions:**
- Backend code has all changes from TC-05/TC-06/TC-07 applied
- Full test suite runs without external network calls

**Steps:**
1. Run the backend test suite: `cd apps/backend && python -m pytest`
2. Capture the full output including pass/fail/skip counts
3. Verify exit code is 0
4. Run `python -c "from app.config import Config; print(Config().config_fingerprint())"` against the build
5. Capture the fingerprint string

**Expected outcome:**
- Test suite passes with ≥1328 pass, ≤8 skip, 0 fail
- Exit code is 0
- `Config().config_fingerprint()` outputs exactly `08e471b10130e1e2` (unchanged)
- No new test failures introduced by desk/structure edits
- Guard test (TC-05/TC-06) is part of the passing suite

**Pass criteria:** Pytest reports `passed` >= 1328, `skipped` <= 8, `failed` == 0; fingerprint is `08e471b10130e1e2`.

---

### TC-09 — Required journeys J-01, J-02, J-03, J-04, J-07 remain green

**Type:** browser  
**Preconditions:**
- All five required journey-scripts exist and are committed
- Backend fully loaded with all changes from this iteration
- Browser automation ready (Chrome MCP or deterministic replay)

**Steps:**
1. Run deterministic golden replay for each of J-01, J-02, J-03, J-04, J-07
2. For each journey, capture pass/fail status and any error messages
3. If deterministic replay fails for any journey, run LLM fallback
4. Document which journeys used golden vs. fallback

**Expected outcome:**
- All five journeys pass (green status)
- No regression from pre-iteration state
- Journey-history.json is updated to record pass state
- Each journey renders the same acceptance criteria as recorded in its journey-history entry

**Pass criteria:** All 5 journeys report PASS; zero FAIL or REGRESSION verdicts.

---

### TC-10 — QA browser pass does not mutate ambient .data/ directory

**Type:** browser  
**Preconditions:**
- Ambient `apps/backend/.data/` directory exists and is read-only during QA
- QA pass uses a fixture-scoped, throw-away data root (with seeded screen/bars copied from the ambient store)
- Backend is configured to use the QA data root, not the ambient one

**Steps:**
1. Capture byte-count and file inventory of `apps/backend/.data/` before browser QA pass starts
2. Run full browser QA (TC-01, TC-02, TC-03, TC-04 and journey tests)
3. After all tests complete, capture byte-count and file inventory of `apps/backend/.data/` again
4. Compare the two inventories

**Expected outcome:**
- `apps/backend/.data/` directory is unchanged (same files, same content, same byte-count)
- All clicks, loads, and navigations in the browser pass use only the fixture-scoped root
- No write operations touch the operator's real ambient store

**Pass criteria:** File inventory before == file inventory after; byte-count is identical; `diff` of directory listings shows no changes.

---

### TC-11 — Skipped row is also a drill-in link (assumption TC-11)

**Type:** browser  
**Preconditions:**
- 2026-06-22 snapshot is displayed (from TC-01)
- A skipped row is visible (e.g., a symbol with no bars, marked as skipped)
- Per the assumption in phase spec, skipped rows are also clickable

**Steps:**
1. Locate a skipped row in the briefing display
2. Click that skipped row
3. Verify browser navigates to `/structure?symbol=<skipped-symbol>&asof=2026-06-22T23:59:59Z`
4. Wait for Structure page to load
5. Capture screenshot

**Expected outcome:**
- Browser navigates to `/structure` with the skipped symbol and as-of
- Symbol and As-of fields are prefilled correctly
- Load executes automatically
- Structure page renders with honest empty state (no bars, no bands) for the skipped symbol — no crash, no error

**Pass criteria:** URL contains correct symbol and asof params; Structure page loads without error; empty state is displayed (no chart data for skipped symbol).

---

### TC-12 — History click with missing date leaves UI on current snapshot

**Type:** browser  
**Preconditions:**
- `/desk` page with history list is displayed
- Backend returns `{"screen": null}` when queried for a non-existent date

**Steps:**
1. In the browser developer console or via test harness, simulate a click on a non-existent date (e.g., 2026-01-01) by directly calling the fetch
2. Observe the page state

**Expected outcome:**
- Page does not crash
- No blank state is rendered
- UI remains on the currently-displayed snapshot (unchanged from before the failed click)
- Error is logged silently or shown in console (no modal/alert)

**Pass criteria:** No crash, no blank page; currently-displayed snapshot is still visible; no JavaScript error is thrown.

---

### TC-13 — /structure with only symbol param ignores it (no partial prefill)

**Type:** browser  
**Preconditions:**
- Navigate to `/structure?symbol=AAPL` (only symbol, no asof)

**Steps:**
1. Navigate to `/structure?symbol=AAPL&asof=` (or just `?symbol=AAPL`)
2. Wait for page to fully render
3. Capture screenshot

**Expected outcome:**
- Symbol input field is empty (or shows the param value but no auto-load is triggered)
- As-of input field is empty
- No load has been triggered
- Rendered state matches the no-params baseline (TC-04)

**Pass criteria:** Input fields are empty and no load is triggered; screenshot matches TC-04 baseline.

---

### TC-14 — /structure with only asof param ignores it (no partial prefill)

**Type:** browser  
**Preconditions:**
- Navigate to `/structure?asof=2026-06-22T23:59:59Z` (only asof, no symbol)

**Steps:**
1. Navigate to `/structure?asof=2026-06-22T23:59:59Z`
2. Wait for page to fully render
3. Capture screenshot

**Expected outcome:**
- As-of input field is empty (or shows the param value but no auto-load is triggered)
- Symbol input field is empty
- No load has been triggered
- Rendered state matches the no-params baseline (TC-04)

**Pass criteria:** Input fields are empty and no load is triggered; screenshot matches TC-04 baseline.

---

## Summary

**Total test cases:** 14

**By type:**
- **Browser tests:** 6 (TC-01, TC-02, TC-03, TC-04, TC-11, TC-12)
- **API/Backend tests:** 1 (TC-08)
- **Artifact/Source-inspection tests:** 4 (TC-05, TC-06, TC-07, TC-13, TC-14)
- **Regression/Golden replay tests:** 1 (TC-09)
- **Persistence/State tests:** 1 (TC-10)

**Key coverage areas:**
- History click-through functionality (TC-01, TC-02, TC-12)
- Drill-in navigation to `/structure` (TC-03, TC-11)
- Default `/structure` behavior with and without params (TC-04, TC-13, TC-14)
- Source-code guards ensuring no recompute on desk page (TC-05, TC-06)
- Journey-script mutation fix (TC-07)
- Backend suite integrity (TC-08)
- Regression coverage (TC-09)
- Data isolation during QA (TC-10)

All test cases derive directly from the phase spec's DEFINITION OF DONE and TESTING REQUIREMENTS sections.
