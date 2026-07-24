# goal-clean_slate-iter-2 Functional Test Plan

**Phase:** goal-clean_slate-iter-2 (J-02: Frontend + WS demolition)  
**Date:** 2026-07-24  
**Frontend Present:** yes

## Phase Goal

Delete the frontend pages/components/types/api-functions for the manual journal/studies/performance surfaces, strip the cockpit's thesis/hint/sound integration and the WS `thesis`/`hint` frame merge, and trim the nav to exactly Cockpit + Structure — so a real user, in a browser, sees exactly the two-page kept product, with both charts and the provenance badge working exactly as shipped, and the three deleted routes honestly 404.

## Test Cases

### TC-01 — Backend import succeeds after WS + registry deletions

**Type:** api  
**Preconditions:** Backend code changes are complete (WS merge removed, registry stubs deleted)

**Steps:**
1. Open a terminal in the backend directory
2. Run `python -c "import app.main"`

**Expected outcome:** Import completes without errors  
**Pass criteria:** Exit code 0, no `NameError`, `AttributeError`, or `ImportError`

---

### TC-02 — GET /meta/ui-routes returns exactly 2 kept routes

**Type:** api  
**Preconditions:** Backend is running; `app/meta.py` ROUTES tuple trimmed to Cockpit + Structure

**Steps:**
1. Run: `curl -s http://localhost:8000/meta/ui-routes | jq .`
2. Verify the response body exactly

**Expected outcome:** JSON payload with two route objects  
**Pass criteria:** 
```json
{"routes": [{"path": "/", "label": "Cockpit", "nav": true}, {"path": "/structure", "label": "Structure", "nav": true}]}
```
Exact match — no additional routes, no extra fields

---

### TC-03 — Deleted pages render 404

**Type:** browser  
**Preconditions:** Frontend is rebuilt and running; backend is running

**Steps:**
1. In a browser, navigate to `http://localhost:3000/journal`
2. Take a screenshot
3. Navigate to `http://localhost:3000/studies`
4. Take a screenshot
5. Navigate to `http://localhost:3000/performance`
6. Take a screenshot

**Expected outcome:** Each URL renders the app's existing not-found 404 page  
**Pass criteria:** All three pages show the same 404 treatment (not a blank screen, not a redirect, not a 500 error); screenshots confirm the deliberate 404 styling

---

### TC-04 — Top nav shows exactly 2 links

**Type:** browser  
**Preconditions:** Frontend rebuilt and running; backend running

**Steps:**
1. Navigate to `http://localhost:3000/` (Cockpit)
2. Inspect the top navigation bar
3. Count the nav links
4. Take a screenshot showing the nav bar

**Expected outcome:** Top nav displays exactly two link labels: "Cockpit" and "Structure"  
**Pass criteria:** No other nav items visible (journal, studies, performance are gone); nav layout is unbroken

---

### TC-05 — Cockpit sim flow shows no thesis/hint/sound elements

**Type:** browser  
**Preconditions:** Frontend rebuilt; backend running; sim engine active

**Steps:**
1. Navigate to `http://localhost:3000/`
2. Wait for the cockpit to load
3. Click "Watch" on a sim ticker (e.g., `SIM-BUYER`)
4. Wait for tape to reach `buyer_control` state
5. Click "Stop" to settle the position
6. Take a screenshot of the entire cockpit page after settling
7. Inspect for thesis strip, hint dock, and sound-toggle elements

**Expected outcome:** Cockpit settles the position with no thesis strip (between chart and grid), no hint dock, and no sound-cue toggle rendered anywhere on the page  
**Pass criteria:** Screenshot shows the grid panels (quote/trades/features/tape-state/observations/event-log) but none of the deleted thesis/hint/sound UI elements

---

### TC-06 — Cockpit PriceChart renders candles, timeframe switch, bands, live tape bars

**Type:** browser  
**Preconditions:** Frontend rebuilt; backend running; sim watch active

**Steps:**
1. Navigate to `http://localhost:3000/` with the sim cockpit ready
2. Observe the chart above the grid panel (PriceChart)
3. Verify candles are rendered in the chart
4. Click the timeframe selector (if available) and switch to a different timeframe
5. Observe that the chart updates to the new timeframe
6. Watch the tape stream and confirm live bars move in real-time as new tape events arrive
7. Verify the S/R band overlay is visible on the chart
8. Take a screenshot showing all elements working

**Expected outcome:** The cockpit chart renders historical candles, the timeframe selector switches charts, the S/R band overlay is visible, and live tape bars move as events stream  
**Pass criteria:** Chart displays candles and bands; timeframe switch updates the view; live bars move as the tape flows; no console errors

---

### TC-07 — Structure chart renders unchanged with 300-302.4 wall band

**Type:** browser  
**Preconditions:** Frontend rebuilt; backend running; `/structure` page accessible

**Steps:**
1. Navigate to `http://localhost:3000/structure`
2. Wait for the page to load
3. Click the "Load" button for the pinned AAPL as-of date (2026-06-22)
4. Wait for the StructureChart to render
5. Inspect the chart for the 300–302.4 class wall band (expected from pre-iteration snapshot)
6. Take a screenshot of the chart
7. Run: `git diff <pre-iteration-commit>..HEAD -- apps/frontend/components/StructureChart.tsx`

**Expected outcome:** Chart renders the tradable wall band at the expected price level; the diff on StructureChart.tsx is empty  
**Pass criteria:** Chart shows the 300–302.4 wall band; screenshot confirms the band is rendered; `git diff` output is empty (zero changes to StructureChart.tsx)

---

### TC-08 — Provenance badge renders feed label from taxonomy

**Type:** browser  
**Preconditions:** Frontend rebuilt; backend running; a live or sim watch active

**Steps:**
1. Navigate to `http://localhost:3000/` with a live or sim ticker watched
2. Locate the provenance/feed-basis badge (typically near the top of the page or chart area)
3. Verify the badge displays a feed label (e.g., "sim", "iex", "sip", "yahoo")
4. Take a screenshot showing the badge and label

**Expected outcome:** The provenance badge renders and displays the feed label sourced from `GET /research/taxonomy`  
**Pass criteria:** Badge is visible; feed label is rendered; label matches one of the kept taxonomy sources

---

### TC-09 — WS frame contains no thesis/hint key

**Type:** api  
**Preconditions:** Frontend and backend running; sim watch active on a ticker

**Steps:**
1. Open browser devtools → Network tab → filter by "WS"
2. Or run: `websocat ws://localhost:8000/tape/SIM-BUYER/stream`
3. Capture a full WS frame JSON while the tape is streaming
4. Inspect the frame for the presence/absence of `thesis` and `hint` keys
5. Verify all pre-existing keys (ticker, stream_status, tape_state, features, recent_trades, etc.) are present

**Expected outcome:** WS frame JSON has no `thesis` key and no `hint` key; all other expected keys are present  
**Pass criteria:** Frame JSON contains `ticker`, `stream_status`, `tape_state`, `features`, `recent_trades` (or equivalent), etc., but NOT `thesis` or `hint`

---

### TC-10 — TypeScript build completes with zero type errors

**Type:** api  
**Preconditions:** Frontend code changes complete (types.ts slimmed, useTapeStream updated)

**Steps:**
1. Navigate to `apps/frontend/`
2. Run: `tsc --noEmit`
3. Or run: `npm run build`

**Expected outcome:** TypeScript compilation completes without errors  
**Pass criteria:** Exit code 0; no type errors reported; no undefined-field references to dropped `thesis?`/`hint?`

---

### TC-11 — Deleted identifiers have zero live hits; fetchTaxonomy survives

**Type:** api  
**Preconditions:** Frontend deletion is complete

**Steps:**
1. Run the orphan-identifier grep:
   ```bash
   grep -rln "declareThesis|resolveThesis|recordAction|saveReview|fetchActiveThesis|fetchActiveHint|fetchHints|fetchJournal|fetchJournalDetail|fetchAnalytics|createStudy|fetchStudies|fetchStudy|cancelStudy|JournalTable|JournalDetailView|JournalFilterBar|ThesisStrip|HintDock|HintLog|SoundCue|StudyList|StudyCreateForm|StudyResultsView|AnalyticsView|onHintDeclare|handleHintDeclare|hintPrefill|survivingThesis|ThesisPrefill" apps/frontend/ | grep -Ev "docs/goal-archive|runs/goal-session"
   ```
2. Verify the result returns zero hits
3. Run: `grep -n "fetchTaxonomy" apps/frontend/lib/api.ts apps/frontend/components/FeedBasisBadge.tsx`

**Expected outcome:** The 14 api.ts functions, 11 components, and 5 dead page.tsx/Cockpit identifiers have zero hits in live code; `fetchTaxonomy` is found in both api.ts and FeedBasisBadge.tsx  
**Pass criteria:** First grep returns zero results; second grep returns hits in both files (proof the keeper survived)

---

### TC-12 — test_meta_routes.py passes with 2-route contract

**Type:** api  
**Preconditions:** Backend tests updated to 2-route contract

**Steps:**
1. Run: `pytest apps/backend/tests/test_meta_routes.py -v`

**Expected outcome:** All tests pass; the contract reflects 2 nav routes (Cockpit, Structure)  
**Pass criteria:** Exit code 0; 0 failed tests; 4 passed tests (2 updated + 2 unchanged per spec)

---

### TC-13 — test_copy_discipline.py passes unedited after frontend deletions

**Type:** api  
**Preconditions:** Frontend pages/components deleted; test_copy_discipline.py NOT edited

**Steps:**
1. Run: `pytest apps/backend/tests/test_copy_discipline.py -v`

**Expected outcome:** All tests pass; the dynamic glob now scans fewer files but applies the same lint rules  
**Pass criteria:** Exit code 0; 0 failed tests; test count unchanged (same number of lints, just on fewer files)

---

### TC-14 — Byte-comparison re-capture matches iter-1 baseline except meta.ui-routes

**Type:** api  
**Preconditions:** Backend running; iter-1 `kept-route-after.txt` baseline exists

**Steps:**
1. Run every KEPT `/research`, `/tape`, and `/meta` GET route via curl
2. Capture sha256 of each response
3. Compare against the iter-1 baseline in `runs/goal-session-clean_slate/iter-1/kept-route-after.txt`
4. Document all routes and their matches

**Expected outcome:** Every kept route produces a byte-identical hash to iter-1, EXCEPT `GET /meta/ui-routes` which has shrunk from 6 to 2 rows (documented, sanctioned diff)  
**Pass criteria:** All routes hash-match iter-1 baseline; `meta.ui-routes` shows the documented shrink (cumulative I-9 sanctioned diff per assumption logged); zero unexpected deltas

---

### TC-15 — Fingerprint unchanged; config.py untouched; 13 pins unchanged

**Type:** api  
**Preconditions:** Full J-02 diff complete

**Steps:**
1. Run: `python -c "from app.config import Config; print(Config().config_fingerprint())"`
2. Verify the output
3. Run: `git diff <pre-iteration>..HEAD -- apps/backend/app/config.py`
4. Verify zero changes
5. Run: `git diff <pre-iteration>..HEAD` and check all 13 fingerprint pin sites from I-9 (test assertion lines)

**Expected outcome:** Fingerprint still prints `4d665603569b9dbf`; config.py has zero diff; all 13 pin assertion sites are unchanged  
**Pass criteria:** Fingerprint literal matches pre-iteration value; config.py diff is empty; all 13 test assertion lines unchanged (T-3 pin discipline holds)

---

### TC-16 — Historical records untouched (goal-archive, runs, reports, journal.db)

**Type:** api  
**Preconditions:** Full J-02 diff complete

**Steps:**
1. Run: `git diff <pre-iteration>..HEAD -- docs/goal-archive/ runs/goal-session-* reports/goal-session-*-delivered.md`
2. Run: `git status -- journal.db`

**Expected outcome:** Zero diffs on historical records; journal.db shows no changes (dormant tables remain)  
**Pass criteria:** All diffs are empty; no historical records edited, deleted, or re-stamped (T-11 honesty rule)

---

### TC-17 — Full backend suite passes with same single pre-authorized failure

**Type:** api  
**Preconditions:** Backend fully implemented and rebuilt

**Steps:**
1. Run: `pytest apps/backend/tests/ -v`
2. Record the exit code and summary line
3. Verify `test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest` is the ONLY failure
4. Count collected tests against iter-1 post-J-01 baseline

**Expected outcome:** Full suite runs; exactly one pre-authorized failure (the MCP test, J-03's to close); zero other failures/errors; collected-test count unchanged from iter-1  
**Pass criteria:** Exit code 1 (one failure expected); summary shows "1 failed"; `test_static_live_tools_json_byte_identical_to_rest` is the failed test; collected test count matches iter-1 (no test file added/removed)

---

### TC-18 — Chart guard suites pass byte-unmodified

**Type:** api  
**Preconditions:** Frontend rebuilt; all changes complete

**Steps:**
1. Run: `git diff <pre-iteration>..HEAD -- apps/backend/tests/test_cockpit_chart_upgrade.py`
2. Verify diff is empty
3. Run: `pytest apps/backend/tests/test_cockpit_chart_upgrade.py -v`
4. Repeat for `test_structure_chart_viewport.py`
5. Repeat for `test_price_chart_confluence.py`

**Expected outcome:** All three test files have zero diffs; all tests pass  
**Pass criteria:** `git diff` output is empty for all three files; `pytest` shows 0 failed for each file (T-8 veto-class — chart regression is a defect)

---

## Summary

**Total test cases: 18**

- **API tests:** 11 (TC-01, TC-02, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-16, TC-17, TC-18)
- **Browser tests:** 5 (TC-03, TC-04, TC-05, TC-06, TC-07, TC-08)
- **WebSocket tests:** 1 (TC-09)

All test cases derive directly from the phase spec's "Test-first contract" section (TC-1 through TC-18) and the DEFINITION OF DONE acceptance criteria. Each test is specific, reproducible, and verifiable within the project environment.
