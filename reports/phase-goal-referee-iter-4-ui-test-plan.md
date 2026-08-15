# Phase goal-referee-iter-4 — UI Test Plan

**Phase:** goal-referee-iter-4
**Date:** 2026-08-14
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301

---

## Scope note

This iteration shipped **zero new UI capability** — every changed production file
(`apps/backend/app/research/referee_stats.py`, `apps/backend/app/research/referee_evidence.py`)
is backend-only and consumed by no route, page, or MCP tool (see
`reports/phase-goal-referee-iter-4-ui-surface-map.md`). There is therefore no new form, button,
page, or user action to write happy-path, validation, error, or UX-discoverability tests for —
those four categories are intentionally empty this iteration, not omitted by oversight.

What this iteration's own Definition of Done DOES require in the browser is journey **J-10**, the
"kept product stands" regression sentinel, which rides every iteration regardless of what changed,
specifically to prove a backend-only diff broke nothing already shipped (phase spec TC-15). All
`smoke` and `regression` test cases below implement that requirement, with exact steps taken
verbatim from the project's own stored golden replay script,
`runs/goal-session-referee/journey-scripts/J-10.json` (UT-01/02/03/04/05/06), plus one
supplementary regression spot-check (UT-07) giving broader "every shipped `/desk` section"
coverage than the golden script's single literal section check.

---

## Test Cases

---

### UT-01 — Cockpit loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` (Cockpit)

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend is running and reachable (no login required — this app has no auth)

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The text "No ticker watched" is visible
- No console errors

---

### UT-02 — Ticker watch flow still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Cockpit)

**Preconditions:**
- UT-01 passed (Cockpit already loaded at `http://localhost:3301/`)

**Steps:**
1. Type "SIM-BUYER" into the field labeled "Ticker"
2. Click the "Watch" button

**Expected Result:**
- The idle "No ticker watched" panel is replaced by the tape-read view
- The text "Buyer Control" appears somewhere on the page
- No error toast or blank panel appears

---

### UT-03 — Structure page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend is running at http://localhost:3301

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The text "Structure" is visible
- No console errors

---

### UT-04 — Pinned-AAPL structure Load still renders the same output (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- UT-03 passed (Structure page already loaded at `http://localhost:3301/structure`)
- The backend's bar store still has AAPL history covering 2026-06-22 (unchanged this iteration —
  this iteration wrote to no store file)

**Steps:**
1. Type "AAPL" into the field with aria-label "Structure symbol" (placeholder "e.g. PG")
2. Type "2026-06-22 12:00:00" into the field with test id `structure-as-of-input` (placeholder
   "2026-06-09 17:00:00")
3. Click the button with test id `structure-load-button`

**Expected Result:**
- The text "2026-06-18" appears on the page (the resolved trading-day window for the pinned
  as-of timestamp)
- The Tradable map and Levels/zones sections populate with data (no empty/error state)
- No error toast appears

---

### UT-05 — Desk page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The text "Playbook Signals" is visible
- No console errors

---

### UT-06 — Playbook Evidence section still expands and renders (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — "Playbook Evidence" collapsible section

**Preconditions:**
- UT-05 passed (Desk page already loaded at `http://localhost:3301/desk`)

**Steps:**
1. Click the button with test id `desk-section-expand-playbookEvidence` (the "Playbook Evidence"
   section header, showing a "▸" collapse marker before the click)

**Expected Result:**
- The button's `aria-expanded` attribute becomes `"true"` and the collapse marker changes from
  "▸" to "▾"
- The section body (`id="desk-section-body-playbookEvidence"`) renders
- The text "Built from signature" appears inside it
- This is the one Desk section whose backing route (`GET /research/desk/referee/evidence`) just
  gained the new, currently-empty `stale_basis_dates` field this iteration — confirm no visibly
  different or broken rendering resulted from that backend change

---

### UT-07 — Remaining Desk reference sections still expand (regression, supplementary)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` — "Top-up Runs", "Index Reconciliation", "Screen Runs", "Screen Comparison",
"Provenance" collapsible sections

**Preconditions:**
- UT-05 passed (Desk page already loaded at `http://localhost:3301/desk`)

**Steps:**
1. Click the button with test id `desk-section-expand-topupRuns` ("Top-up Runs")
2. Click the button with test id `desk-section-expand-indexReconciliation`
   ("Index Reconciliation")
3. Click the button with test id `desk-section-expand-screenRuns` ("Screen Runs")
4. Click the button with test id `desk-section-expand-screenComparison` ("Screen Comparison")
5. Click the button with test id `desk-section-expand-provenance` ("Provenance")

**Expected Result:**
- Each button's `aria-expanded` attribute becomes `"true"` and its collapse marker changes from
  "▸" to "▾"
- Each section's body renders content (a table, list, or explicit empty-state message) with no
  error toast and no permanently-blank panel
- This test gives broader coverage of the phase spec's "every shipped `/desk` section" testing
  requirement beyond the one section (`playbookEvidence`) the stored golden script checks

---

## Not Applicable This Iteration

- **Happy-path**: no new capability exists to exercise end-to-end.
- **Validation**: no new or changed form exists.
- **Error**: no new backend error path is reachable from the UI — the one backend change with a
  live route (`referee_evidence.py`'s `stale_basis_dates`) only ever returns an empty list on
  today's data and is not rendered by any component regardless.
- **UX / discoverability**: no new navigation entry, button, or link was added.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit loads | smoke | P1 | `/` |
| UT-02 | Ticker watch flow | regression | P1 | `/` |
| UT-03 | Structure page loads | smoke | P1 | `/structure` |
| UT-04 | Pinned-AAPL structure Load | regression | P1 | `/structure` |
| UT-05 | Desk page loads | smoke | P1 | `/desk` |
| UT-06 | Playbook Evidence expand | regression | P1 | `/desk` |
| UT-07 | Remaining 5 Desk sections expand | regression | P2 | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-01 through UT-06 collectively
implement journey J-10 (this iteration's Required-still-passing regression sentinel, TC-15); UT-07
is supplementary and non-blocking.
