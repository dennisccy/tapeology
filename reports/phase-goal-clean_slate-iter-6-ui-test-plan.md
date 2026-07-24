# Phase goal-clean_slate-iter-6 — UI Test Plan

**Phase:** goal-clean_slate-iter-6
**Date:** 2026-07-24
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301

---

## Context for testers

This iteration deleted 5 dead backend classes, added one backend guard test, and touched
**zero** frontend files. There is no new capability, page, button, or label to test. Every
test case below is a **re-verification** of the already-shipped Cockpit (`/`) and Structure
(`/structure`) pages — evidence that the backend cleanup in `routes.py` (which also serves
several of `/structure`'s live routes) did not disturb anything a user can see or click. A
PASS on every test below means "nothing changed," which is the correct and expected outcome.
Any difference from the expected results is a regression introduced by this iteration's
backend edit and must be reported.

Before testing, the frontend must be rebuilt fresh (this iteration's own T-9 requirement):
the operator/QA agent should confirm `apps/frontend/.next` was cleared and the frontend
restarted before this test session begins, since a stale Next.js build can mask or fake a
"pass."

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Cockpit page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend rebuilt fresh (`.next` cleared) and running at http://localhost:3301
- Backend running at http://localhost:8301
- No ticker is currently being watched (fresh page load)

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The text "No ticker watched" is visible (default idle Tape State)
- A ticker field with placeholder "Ticker e.g. SIM-BUYER" and a "Watch" button are visible
- The top navigation shows "Cockpit" and "Structure"
- No browser console errors

---

### UT-02 — Structure page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend rebuilt fresh (`.next` cleared) and running at http://localhost:3301
- Backend running at http://localhost:8301

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The text "Structure" is visible on the page
- A Symbol field (placeholder "e.g. PG"), an As-Of field (placeholder "2026-06-09T21:00:00Z"), and a "Load" button are all visible
- The Case Studies table and the Edge Report section are both present on the page (even before any Load action)
- No browser console errors

---

### UT-03 — Operator can watch a simulated ticker, switch tape granularity, and stop watching (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend rebuilt fresh and running at http://localhost:3301
- Backend running at http://localhost:8301
- Page is at its default idle state ("No ticker watched" visible — see UT-01)

**Steps:**
1. Navigate to `http://localhost:3301/`; confirm the text "No ticker watched" is visible
2. Type "SIM-BUYER" into the field with placeholder "Ticker e.g. SIM-BUYER"
3. Click the "Watch" button
4. Click the 2nd button inside the control labeled `aria-label="Tape bar size"`
5. Click the "Stop watching" button

**Expected Result:**
- After step 3: the text "Buyer Control" appears on the page
- After step 4: the caption text "Logical 30s bars built live from the tape." appears
- After step 5: the page returns to displaying the text "No ticker watched" (idle state restored)
- At no point does the page show a blank screen, crash, or unhandled error

---

### UT-04 — Operator can load Structure levels for AAPL and drill into a Case Study (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend rebuilt fresh and running at http://localhost:3301
- Backend running at http://localhost:8301
- AAPL bar data for as-of `2026-06-22T21:00:00Z` is already registered/frozen in the backend's dataset store (pre-existing fixture data — no new fetch is required or performed)
- The Case Studies table has at least one existing row (pre-existing data from an earlier iteration)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type "AAPL" into the field with placeholder "e.g. PG"
3. Type "2026-06-22T21:00:00Z" into the field with placeholder "2026-06-09T21:00:00Z"
4. Click the "Load" button
5. Click any row in the Case Studies table (a `case-studies-row` element)

**Expected Result:**
- After step 4: the text "300.11" appears on the page
- After step 5: a case-study drill-in element (`case-drillin`) opens, showing that case study's detail
- At no point does the page show a blank screen, crash, or unhandled error

---

### UT-05 — Structure Load form does not fabricate a result when submitted empty (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Frontend rebuilt fresh and running at http://localhost:3301
- Backend running at http://localhost:8301
- Page has just been freshly loaded (no prior Load performed this session — reload first if needed)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Without typing anything into the Symbol field (placeholder "e.g. PG") or the As-Of field (placeholder "2026-06-09T21:00:00Z"), click the "Load" button

**Expected Result:**
- The page does NOT display the text "300.11" or any other specific price/level value — confirms the form is not silently reusing a cached or fabricated result
- No blank white screen, unhandled JavaScript error overlay, or crash occurs
- One of the following is acceptable: (a) an inline validation message appears near the Symbol or As-Of field, or (b) the Load action has no visible effect and the page stays in its pre-click state. A crash, or a populated result appearing from empty input, is a failure.

---

### UT-06 — Edge Report shows its honest current state, not a crash (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Frontend rebuilt fresh and running at http://localhost:3301
- Backend running at http://localhost:8301
- No specific Edge Report cache state is required — the test accepts either a warm or cold cache

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll down to the Edge Report section of the page

**Expected Result:**
- Exactly one of the following is visible: (a) populated edge-report data cells showing computed values, or (b) the exact text "Edge report not computed yet." together with a visible "Compute" button
- No blank section, indefinitely-spinning loader, or raw error/stack-trace text appears

---

### UT-07 — No deleted-feature links reappear in the navigation (regression)

**Type:** regression
**Priority:** P1 — elevated above the usual regression default because this specific check is this iteration's own primary audit finding (the critical-tagged "Deletion is complete, never cosmetic" anti-goal) and the browser-side evidence for the required-still-passing J-01/J-03/J-04 confirmatory touch, not a low-risk incidental check.
**Surface:** top navigation (all pages)

**Preconditions:**
- Frontend rebuilt fresh and running at http://localhost:3301
- Backend running at http://localhost:8301

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Look at the top navigation bar
3. Count the visible navigation items and read each label
4. Click "Structure" in the navigation, then look at the top navigation bar again

**Expected Result:**
- Exactly 2 navigation items are visible at all times, labeled exactly "Cockpit" and "Structure"
- No navigation item labeled "Journal", "Analytics", "Studies", "Monitor", "Research", or any label other than "Cockpit" / "Structure" is present anywhere
- Clicking "Structure" navigates to `http://localhost:3301/structure`

---

### UT-08 — Both product surfaces remain discoverable within one click of home (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation / `/`

**Preconditions:**
- Frontend rebuilt fresh and running at http://localhost:3301
- Backend running at http://localhost:8301

**Steps:**
1. Open `http://localhost:3301/` in a browser, as a first-time user would
2. Without prior knowledge of the app, look for a way to reach the structure-analysis page
3. Click the navigation item labeled "Structure"

**Expected Result:**
- The "Structure" label is visible in the top navigation without scrolling or opening any menu
- Clicking it reaches `http://localhost:3301/structure` in a single click
- The Structure page's Load flow (Symbol field, As-Of field, "Load" button) is immediately visible without further navigation — the core capability is not hidden behind extra clicks

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit page loads | smoke | P1 | `/` |
| UT-02 | Structure page loads | smoke | P1 | `/structure` |
| UT-03 | Cockpit ticker watch → bar-size switch → stop | happy-path | P1 | `/` |
| UT-04 | Structure Load → Case Study drill-in | happy-path | P1 | `/structure` |
| UT-05 | Load form doesn't fabricate results when empty | validation | P2 | `/structure` |
| UT-06 | Edge Report honest state | error | P2 | `/structure` |
| UT-07 | No orphaned nav links reappear | regression | P1 | nav |
| UT-08 | Structure reachable in 1 click from home | ux | P3 | nav |

**P1 tests must all pass for browser QA verdict to be PASS.** Given this iteration's own
Definition of Done, UT-07 failing (a nav item reappearing) or UT-03/UT-04 failing (the kept
product breaking) would both constitute a genuine regression, not an informational note.
