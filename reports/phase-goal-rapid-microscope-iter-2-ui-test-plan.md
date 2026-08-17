# Phase goal-rapid-microscope-iter-2 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-2
**Date:** 2026-08-17
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301 (store-scoped QA rig; backend on http://localhost:8301)

---

## Scope note

This iteration ships zero `.tsx` changes (confirmed: `git diff --stat HEAD -- apps/frontend` is
empty). Exactly one surface has a real, testable change — the Microscope Readiness panel on
`/desk` now has non-empty data to show when tested through the store-scoped QA rig (see UT-02).
Every other test case below is part of the mandatory widened regression sentinel (J-10), required
this iteration because the prior iteration's evaluator returned `ESCALATE`.

No validation test case is included: no form was added or changed this iteration, so there is no
new input surface to validate. Writing one anyway would mean testing an unrelated pre-existing
form for a reason unconnected to this iteration's diff, which does not meet the "specific action"
bar this plan holds itself to elsewhere.

Preconditions common to every test case below:
- The store-scoped QA rig is running: backend at `http://localhost:8301`, frontend at
  `http://localhost:3301`, started via `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`
  (the launcher this iteration extended to stage the 2 tick fixtures).
- A full clean rebuild has been done first: `rm -rf apps/frontend/.next` before starting the
  frontend (T-9 in this project's testing conventions) — otherwise a stale build can mask this
  iteration's data change.

---

## Test Cases

---

### UT-01 — `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301
- No login is required anywhere in this product

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to finish its initial load

**Expected Result:**
- Page renders without a blank screen or an error-boundary message
- The heading "Desk" (`data-testid="desk-title"`) is visible
- Scrolling to the bottom shows a section header reading "Microscope Readiness"
  (`data-testid="desk-section-expand-microReadiness"`), collapsed (▸ marker,
  `aria-expanded="false"`)
- No new console errors appear (compare against a baseline load if unsure what is pre-existing)

---

### UT-02 — Microscope Readiness panel shows real, non-empty tick data (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Microscope Readiness panel

**Preconditions:**
- The store-scoped QA rig was started via this iteration's extended
  `qa_playbook_iter7_fixture_scoped_backend.sh` (so its dataset folder actually contains the 2
  staged fixtures)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the bottom of the page
3. Click the "Microscope Readiness" section header button
   (`data-testid="desk-section-expand-microReadiness"`)
4. Wait for the panel body to render

**Expected Result:**
- The header's arrow marker changes from "▸" to "▾" and `aria-expanded` becomes `"true"`
- The "Corpus Totals" table shows "Distinct symbol-days" = `1`
  (`data-testid="micro-readiness-distinct-symbol-days"`) and "Distinct datasets" = `2`
  (`data-testid="micro-readiness-distinct-datasets"`)
- The "Legacy Tick Shards" table (`data-testid="micro-readiness-shards-table"`) shows exactly 2
  rows — NOT the "No tick shards recorded." empty state
  (`data-testid="micro-readiness-shards-empty"` must be absent)
- Both shard rows show Symbol "PG" and Feed "sip"; the Session date column reads `2026-06-09` for
  both rows
- The "Pilot-Study Floors" table (`data-testid="micro-readiness-floors-table"`) renders populated
  rows, not blank
- The integrity-errors area shows the empty state "No integrity errors."
  (`data-testid="micro-readiness-integrity-errors-empty"`), confirming both fixtures loaded
  cleanly with no checksum/identity error

---

### UT-03 — Microscope Readiness panel is discoverable (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` — page-level navigation to the Microscope Readiness panel

**Steps:**
1. Navigate to `http://localhost:3301/desk` (as a first-time visitor would)
2. Scroll toward the bottom of the page, reading each section header in order

**Expected Result:**
- A section header reading exactly "Microscope Readiness" is visible, reachable by scrolling alone
  — zero additional navigation/clicks from page load are required to find it
- It is collapsed by default (▸ marker), consistent with the other reference-material sections on
  this page (Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, Top-up
  Runs, Index Reconciliation, Screen Runs)
- A single click (as in UT-02) is the only action needed to reveal its data — no separate page or
  modal is required

---

### UT-04 — Backend-unreachable state shows an honest message, not a crash (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` — Microscope Readiness panel

**Note:** this iteration ships no new client-triggerable error path (no form submits a value that
could be rejected). This case instead re-confirms the existing honest-unavailable discipline the
panel already carries, since it is the newest section on the page and the one this iteration's
data change touches most directly.

**Preconditions:**
- Backend process stopped, or port 8301 temporarily blocked

**Steps:**
1. Stop the backend process (or make port 8301 unreachable)
2. Navigate to `http://localhost:3301/desk`
3. Click the "Microscope Readiness" section header (`data-testid="desk-section-expand-microReadiness"`)

**Expected Result:**
- The panel renders the shipped unavailable-state component
  (`data-testid="micro-readiness-unavailable"`) with a readable message (e.g., "The microscope
  readiness corpus could not be loaded.")
- The page does NOT show a blank white screen, a raw stack trace, or a silent no-op
- Restart the backend afterward before running any other test case in this plan

---

### UT-05 — Cockpit `/` live watch flow still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (cockpit)

**Preconditions:**
- None beyond the common preconditions above

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Confirm the "Tapeology" header text and a field labeled "Ticker" are visible
3. Type `SIM-BUYER` into the field labeled "Ticker"
4. Click the "Watch" button

**Expected Result:**
- Within a few seconds the page leaves its idle/connecting state and shows the live cockpit price
  chart
- No red/error banner appears
- This confirms the cockpit — a page this iteration's diff never touches — is unaffected

---

### UT-06 — `/structure` Tradable Map load flow still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Confirm the heading "Structure" (`data-testid="structure-title"`) is visible
3. Type `PG` into the "Symbol" field
4. Click the "Today" button (`data-testid="structure-as-of-today-button"`)
5. Click the "Load" button (`data-testid="structure-load-button"`)

**Expected Result:**
- Step 4 fills the "As-of (ET)" field with today's end-of-day market-clock instant
- After step 5, the "Tradable Map" panel renders bands/levels for PG with no error message
- This confirms `/structure` — a page this iteration's diff never touches — is unaffected

---

### UT-07 — `/desk` Playbook Signals filters and Playbook Evidence still work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — "Playbook Signals" section (Band Context / Cohorts) and "Playbook Evidence"
panel

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the always-visible "Playbook Signals" section, change the "show" dropdown
   (`data-testid="desk-playbook-band-filter"`) to "at a wall behind"
3. Change the "and" dropdown (`data-testid="desk-playbook-inside-filter"`) to "inside a band"
4. Scroll down and click the "Playbook Evidence" section header
   (`data-testid="desk-section-expand-playbookEvidence"`)

**Expected Result:**
- After steps 2-3, the count text (`data-testid="desk-playbook-band-filter-count"`) updates to a
  "showing N of M recorded signals..." string with N ≤ M, confirming the band/cohort filters still
  narrow the signals table
- Step 4 expands the Playbook Evidence panel with no error boundary, showing its existing
  read-only content (a table or its own empty-state) — unchanged from before this iteration

---

### UT-08 — `/desk` Referee Registry / Adjudications / Runs still expand and render (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — Referee Registry, Referee Adjudications, Referee Runs panels

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Referee Registry" section header (`data-testid="desk-section-expand-refereeRegistry"`)
3. Click the "Referee Adjudications" section header
   (`data-testid="desk-section-expand-refereeAdjudications"`)
4. Click the "Referee Runs" section header (`data-testid="desk-section-expand-refereeRuns"`)

**Expected Result:**
- Each click expands its panel — `referee-registry-section`, `referee-adjudications-section`, and
  `referee-runs-section` each become visible in turn — with no error boundary
- No `data-testid` or heading-text difference from the previously shipped versions of these three
  sections (this iteration's own acceptance contract, TC-18, requires zero such change anywhere
  outside the QA-rig fixture seeding)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads | smoke | P1 | `/desk` |
| UT-02 | Microscope Readiness shows real 2-row PG data | happy-path | P1 | `/desk` |
| UT-03 | Microscope Readiness discoverability | ux | P2 | `/desk` |
| UT-04 | Backend-down honest unavailable state | error | P2 | `/desk` |
| UT-05 | Cockpit watch flow unaffected | regression | P1 | `/` |
| UT-06 | Structure Tradable Map load unaffected | regression | P1 | `/structure` |
| UT-07 | Playbook Signals filters + Playbook Evidence unaffected | regression | P1 | `/desk` |
| UT-08 | Referee Registry/Adjudications/Runs unaffected | regression | P1 | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-05 through UT-08 are marked P1
(rather than the usual "low-risk regression, P3") specifically because this iteration's own
Definition of Done makes the FULL kept-product sentinel a blocking requirement (mandatory
widening triggered by iteration 1's `ESCALATE` verdict) — a regression on any of them is not
informational this iteration, it is a gate.
