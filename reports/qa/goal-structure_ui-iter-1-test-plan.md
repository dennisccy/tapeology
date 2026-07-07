# goal-structure_ui-iter-1 Functional Test Plan

**Phase:** goal-structure_ui-iter-1
**Date:** 2026-07-07
**Frontend Present:** yes

## Phase Goal

Ship the read-only `/structure` page that renders, for a chosen symbol and as-of time, a price chart with support/resistance levels (one dashed line per level) and a confluence-zones table (badged A/B/C), where every displayed value is read verbatim from canonical endpoints and distinct honest empty states surface when bars, levels, or zones are missing.

## Test Cases

### TC-01 — Backend route registry includes /structure entry and five pre-existing entries unchanged

**Type:** api
**Preconditions:** Backend is running; database is initialized with default config

**Steps:**
1. Run `curl -s http://localhost:8000/meta/ui-routes | jq '.routes'`

**Expected outcome:** Response contains 6 total entries in order: `/`, `/journal`, `/journal/[id]`, `/studies`, `/performance`, `/structure`; each with `path`, `label`, and `nav` fields; `/structure` has `"nav": true`

**Pass criteria:** 
- Status code 200
- Exact count of 6 entries
- `/structure` entry present with `{"path": "/structure", "label": "Structure", "nav": true}`
- Five pre-existing entries (`/`, `/journal`, `/journal/[id]`, `/studies`, `/performance`) are byte-identical in value and in the same order as before this iteration
- `config_fingerprint` in the same response is still `4d665603569b9dbf`

---

### TC-02 — Structure page loads and displays symbol search and as-of time controls

**Type:** browser
**Preconditions:** Frontend is running at http://localhost:3000; Structure page is reachable from nav

**Steps:**
1. Navigate to http://localhost:3000/structure
2. Verify page title/heading reads "Structure" or similar
3. Locate SymbolSearch component (text input with autocomplete for symbol selection)
4. Locate as-of datetime input field

**Expected outcome:** Page loads without error; both controls are visible and interactive

**Pass criteria:** 
- Page renders with HTTP 200 status
- SymbolSearch input is present and accepts text input
- As-of time input is present and accepts ISO-8601 datetime values
- No JavaScript errors in console

---

### TC-03 — Structure tab is reachable from top-bar nav and comes from data-driven route list

**Type:** browser
**Preconditions:** Frontend is running; user is on any page (e.g., `/`, `/journal`, `/studies`, `/performance`)

**Steps:**
1. Navigate to any existing page (e.g., http://localhost:3000/journal)
2. Inspect the NavBar top-bar links by fetching page DOM
3. Verify that "Structure" link is present in the nav
4. Verify via dev-tools Network tab that the link originates from the fetched `GET /meta/ui-routes` response (not a hardcoded client link)
5. Click the "Structure" link
6. Verify navigation to `/structure` page succeeds

**Expected outcome:** Structure link appears in top-bar nav on all pages, is served by the route registry, and navigation works

**Pass criteria:** 
- "Structure" text appears in NavBar HTML
- Network request shows `GET /meta/ui-routes` response includes `/structure`
- NavBar component filters `nav: true` entries from the response and renders them
- Clicking the link navigates to `/structure` with HTTP 200 status
- No hardcoded `<Link href="/structure">` string in source code (verification via source inspection)

---

### TC-04 — Populated state: chart renders levels as dashed lines with timeframe labels, zones table shows A/B/C badged rows

**Type:** browser
**Preconditions:** 
- Backend running with bar-series fixture seeded at `apps/backend/tests/fixtures/bars/` or `.data/bars/` (symbol PG, 1h + 1d timeframes)
- Frontend running
- As-of time set to 2026-06-09T21:00:00Z (proven to yield 20 levels, 6 zones: 5xC, 1xB)

**Steps:**
1. Navigate to `/structure`
2. Enter symbol `PG` in SymbolSearch
3. Set as-of time to `2026-06-09T21:00:00Z`
4. Wait for page to load (loading state should pass)
5. Inspect rendered chart for price lines
6. Inspect zones table for rows with class badges
7. Fetch live `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z` in parallel
8. Compare each rendered level (price, timeframe, type) to the API response
9. Compare each rendered zone row (class badge, member levels, score) to the API response

**Expected outcome:** 
- Chart displays multiple dashed price lines, each labeled with its timeframe (e.g., "1h", "1d")
- Zones table displays 6 rows (5 with class C badge, 1 with class B badge)
- Every rendered value (price, timeframe, type, class, score) matches the API response byte-for-byte
- No client-side recalculation visible

**Pass criteria:** 
- Chart candles render without errors
- At least 2 dashed level lines are visible on the chart
- Zones table has 6 rows
- Each zone row shows: class badge (A/B/C), list of member level prices + timeframes, score value
- XPath/CSS selector verification: `table rows` count is 6, each row contains badge element with text A, B, or C
- Byte-for-byte match between rendered values and `GET /research/levels` JSON

---

### TC-05 — Honest empty state: no_bar_series_for_symbol renders distinct credentials-needed message

**Type:** browser
**Preconditions:** Frontend running; a symbol with no recorded bar series (or before fixture seeding)

**Steps:**
1. Navigate to `/structure`
2. Enter a symbol with no recorded bars (e.g., `AAPL` if not seeded, or use `PG` before seeding fixture)
3. Set any as-of time (e.g., 2026-06-09T21:00:00Z)
4. Wait for response from `GET /research/levels?symbol=<S>&as_of=<T>`
5. Inspect rendered page for the explicit empty state

**Expected outcome:** Page displays a distinct, non-empty message like "No bar series recorded — recording historical bars needs provider credentials"; no chart, no table, no fabricated data

**Pass criteria:** 
- HTTP 200 response received (endpoint succeeds)
- Rendered content includes text matching "no bar series" or "provider credentials" (case-insensitive)
- Message is distinct from other empty states (different copy)
- No chart or table is rendered
- `data-testid` attribute (if present) should be distinct, e.g., `data-testid="no-bars-state"`

---

### TC-06 — Honest empty state: series present but levels empty renders distinct "no levels found" message

**Type:** browser
**Preconditions:** 
- Backend running with fixture seeded
- Frontend running
- Symbol `PG` queried at an as-of time before its bar window opens (e.g., 2026-05-01T00:00:00Z)

**Steps:**
1. Navigate to `/structure`
2. Enter symbol `PG`
3. Set as-of time to `2026-05-01T00:00:00Z` (before the fixture window start)
4. Wait for `GET /research/levels` response
5. Verify `no_bar_series_for_symbol: false` and `levels: []` in the response
6. Inspect rendered page for the distinct empty state

**Expected outcome:** Page displays a distinct message like "No levels found for this symbol at this time"; chart may be empty, table is absent, no other data fabricated

**Pass criteria:** 
- API response shows `no_bar_series_for_symbol: false` and `levels: []`
- Rendered message is distinct from the "no bar series" state (different copy)
- Message text includes "no levels" or "not found" (case-insensitive)
- `data-testid` attribute (if present) should be distinct, e.g., `data-testid="no-levels-state"`

---

### TC-07 — Honest empty state: levels present but no confluence zones renders distinct "no qualifying confluence zone" message

**Type:** browser
**Preconditions:** 
- Backend running
- Frontend running
- A symbol + as-of time combination that yields `levels: [...]` but `confluence_zones: []`
  (Either: probe intermediate as-of values on live endpoint, or seed a dedicated small fixture with widely separated pivots)

**Steps:**
1. Navigate to `/structure`
2. Enter the test symbol
3. Set as-of time to a value that produces levels but no zones
4. Wait for response
5. Verify `levels` array is non-empty and `confluence_zones: []` in the response
6. Inspect rendered page for the distinct empty state

**Expected outcome:** Page displays distinct message like "No qualifying confluence zones found"; levels chart is NOT rendered; table is absent; no fabricated zones

**Pass criteria:** 
- API response shows `levels: [...]` (non-empty) and `confluence_zones: []`
- Rendered message is distinct from both prior empty states (different copy)
- Message text includes "no" and "confluence zone" or "zone" (case-insensitive)
- `data-testid` attribute (if present) should be distinct, e.g., `data-testid="no-zones-state"`

---

### TC-08 — Degraded state: backend unreachable or non-200 response renders explicit degraded panel

**Type:** browser
**Preconditions:** Frontend running; backend either stopped or forced to return 5xx/error status

**Steps:**
1. Stop the backend (or simulate with a proxy returning 500)
2. Navigate to `/structure`
3. Select a symbol and as-of time
4. Attempt to load levels (fetch will fail)
5. Inspect rendered page for degraded/error state

**Expected outcome:** Page displays an explicit degraded state consistent with `NavBar.tsx` / `UnavailablePanel` pattern (amber accent, apologetic copy); no crash, no blank page, no fabricated chart/table

**Pass criteria:** 
- No JavaScript error or unhandled promise rejection in console
- Page remains interactive (does not crash)
- Rendered content includes explanatory text (e.g., "Unable to load", "service unavailable")
- Styling uses amber/warning accent color (consistent with existing design)
- No chart or table rendered

---

### TC-09 — Start script: both backend and frontend services start without port conflicts, remain running

**Type:** api
**Preconditions:** No existing services running on ports 8000 (backend) and 3000 (frontend)

**Steps:**
1. Navigate to project root
2. Run the project start script (from `.claude/project-template.md`, e.g., `npm run dev:both` or `./scripts/start.sh`)
3. Wait 5 seconds for both services to fully initialize
4. Verify backend is reachable: `curl -s http://localhost:8000/meta/ui-routes > /dev/null; echo $?`
5. Verify frontend is reachable: `curl -s -I http://localhost:3000 | head -1`
6. Stop both services using Ctrl+C
7. Immediately re-run the start script
8. Verify no port-in-use errors; both services start cleanly again

**Expected outcome:** Both services start without errors, both ports are bound, services accept requests, can be stopped and restarted without port conflicts

**Pass criteria:** 
- Initial `npm run dev:both` (or equivalent) exits with status 0 (or runs indefinitely for long-running server)
- Backend health check returns HTTP 200
- Frontend health check returns HTTP 200 or 3xx redirect
- Stop sequence (Ctrl+C) terminates services cleanly
- Re-run succeeds without "port already in use" or "EADDRINUSE" error
- Second run of backend and frontend both accept requests

---

### TC-10 — Regression: all five pre-existing navigation links remain reachable and unchanged

**Type:** browser
**Preconditions:** Frontend running; Structure iteration complete

**Steps:**
1. Navigate to each of the five pre-existing pages: `/`, `/journal`, `/studies`, `/performance`, `/journal/[id]` (with a valid journal entry ID)
2. For each page, verify:
   - Page loads with HTTP 200
   - Title/heading is unchanged from baseline
   - Key page elements render (e.g., nav bar, content panels, tables)
   - No new errors or warnings in console
3. On each page, verify the NavBar still shows at least 4 links (the original set, plus the new Structure link)

**Expected outcome:** All five pre-existing surfaces remain fully functional and visually unchanged

**Pass criteria:** 
- `/` loads and displays the home/dashboard content unchanged
- `/journal` loads and displays the journal list unchanged
- `/journal/[id]` loads for a valid entry and displays entry details unchanged
- `/studies` loads and displays the studies content unchanged
- `/performance` loads and displays the performance content unchanged
- NavBar on each page includes the original nav entries unchanged (new `/structure` is additive)
- No JavaScript errors in console on any page

---

### TC-11 — Config fingerprint remains byte-identical at 4d665603569b9dbf

**Type:** api
**Preconditions:** Backend is running; database initialized with default config

**Steps:**
1. Run `curl -s http://localhost:8000/meta/ui-routes | jq -r '.config_fingerprint'`
2. Compare returned value to expected value `4d665603569b9dbf`

**Expected outcome:** Fingerprint is unchanged from era-4 baseline

**Pass criteria:** 
- Returned fingerprint value is exactly `4d665603569b9dbf`
- No configuration mutations have been introduced by the `/structure` additive nav entry

---

## Summary

| Metric | Value |
|--------|-------|
| **Total test cases** | 11 |
| **API tests** | 3 (TC-01, TC-09, TC-11) |
| **Browser tests** | 8 (TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-10) |
| **Artifact checks** | 0 |

**Coverage:**
- Backend route registry: 1 test (new entry + pre-existing entries unchanged + fingerprint)
- Frontend page load & controls: 1 test
- Navigation integration: 1 test (data-driven, not hardcoded)
- Populated state (chart + table): 1 test (with byte-for-byte value comparison)
- Empty state 1 (no bars): 1 test
- Empty state 2 (no levels): 1 test
- Empty state 3 (no zones): 1 test
- Degraded state (backend unreachable): 1 test
- Service startup & stability: 1 test (no port conflicts, restart cleanly)
- Regression (pre-existing surfaces): 1 test
- Config freeze: 1 test

All test cases are derived directly from the DEFINITION OF DONE and TESTING REQUIREMENTS sections of the phase spec. Every test is specific, reproducible, and maps to a concrete acceptance criterion.
