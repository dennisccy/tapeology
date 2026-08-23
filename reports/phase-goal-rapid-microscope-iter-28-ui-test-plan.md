# Phase goal-rapid-microscope-iter-28 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-28
**Date:** 2026-08-23
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend is running and reachable
- No login required

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The heading "Desk" (`data-testid="desk-title"`) is visible
- The text "Playbook Signals" is visible somewhere on the page
- No browser console errors

---

### UT-02 — The seal-unaware caveat renders inside the Referee Registry Strategy Family block (happy path — this iteration's actual change)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Referee Registry → Evidence Readiness → Strategy Family

**Preconditions:**
- Frontend is running at http://localhost:3301
- `rm -rf apps/frontend/.next` and rebuild has been performed before this browser pass (T-9)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Referee Registry" section header (`data-testid="desk-section-expand-refereeRegistry"`)
3. Wait for the section body to render (its own deferred fetches resolve)
4. Scroll to the "Evidence Readiness" sub-section, then to its "Strategy Family" sub-heading (below "Playbook Family")
5. Capture an ELEMENT-scoped screenshot of `data-testid="referee-evidence-strategy-block"` (never a full-page stitch)

**Expected Result:**
- The "Strategy Family" block shows its existing `Datasets`, `Train / Holdout`, and `Trades` rows (each with a numeric value) unchanged
- Directly below the existing tick-gate line (`data-testid="referee-evidence-strategy-tick-gate"`) and directly above the existing basis-caveats list (`data-testid="referee-evidence-strategy-basis-caveats"`), a NEW line is visible with `data-testid="referee-evidence-strategy-seal-unaware-caveat"` containing exactly this text:
  "Legacy Referee readiness metric — seal-unaware in the Rapid Microscope era. It may include withheld/unexposed Rapid-Microscope shards and must not be used as the canonical Rapid-Microscope readiness count."
- The new line is styled as muted secondary text (small, gray/slate), visually reading as part of the same disclosure family as the tick-gate and basis-caveats lines, not as a new card or panel
- The new line does not visually overlap or collide with the basis-caveats bullet list below it

---

### UT-03 — Validation: N/A (no form changed this iteration)

**Type:** validation
**Priority:** N/A
**Surface:** N/A

This iteration adds a single static text element — no form, input, or submission flow was added
or changed. There is no validation surface to test.

---

### UT-04 — Error: N/A (no new error state)

**Type:** error
**Priority:** N/A
**Surface:** N/A

The new caveat text is static and unconditional; it carries no loading/error/empty state of its
own (it renders whenever its parent "Strategy Family" block renders). There is no new
backend-error path to trigger.

---

### UT-05 — J-01 golden journey: era transition + Microscope Readiness still works (regression, target journey)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Microscope Readiness section

**Preconditions:**
- Frontend is running at http://localhost:3301

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Confirm the text "Playbook Signals" is visible
3. Click the section header `data-testid="desk-section-expand-microReadiness"`

**Expected Result:**
- The Microscope Readiness section body expands
- The text "hand_assigned" becomes visible somewhere in the expanded section
- No new element from this iteration interferes with this section (it lives in a different collapsible section than the Referee Registry caveat)

---

### UT-06 — J-10 sentinel: kept surfaces still render end to end (regression, target journey)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/structure`, `/desk` (all seven `/desk` collapsible sections plus the cockpit and structure pages)

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend is running with the AAPL 2026-06-22 fixture data available

**Steps:**
1. Navigate to `http://localhost:3301/`
   - **Expect:** text "No ticker watched" is visible
2. Type "SIM-BUYER" into the field labeled "Ticker", then click the "Watch" button
   - **Expect:** text "Buyer Control" appears
3. Navigate to `http://localhost:3301/structure`
   - **Expect:** text "Tradable Map" is visible
4. Type "AAPL" into the field labeled "Structure symbol"
5. Type "2026-06-22 16:00:00" into the field `data-testid="structure-as-of-input"`
6. Click the button `data-testid="structure-load-button"`
   - **Expect:** text "300.11–302.2" appears
7. Navigate to `http://localhost:3301/desk`
   - **Expect:** text "Playbook Signals" is visible
8. Click `data-testid="desk-section-expand-playbookEvidence"`
   - **Expect:** text "Built from signature:" appears
9. Type "2026-06-22" into `data-testid="desk-playbook-date-input"`
   - **Expect:** text "recorded signals, none hidden" appears
10. Click `data-testid="desk-section-expand-microReadiness"`
    - **Expect:** text "Distinct symbol-days" appears
11. Click `data-testid="desk-section-expand-scoutLedger"`
    - **Expect:** text "variants tried" appears
12. Click `data-testid="desk-section-expand-walkForward"`
    - **Expect:** text "No fold specs registered." appears
13. Click `data-testid="desk-section-expand-validationVault"`
    - **Expect:** text "iter18-qa-universe" appears
14. Click `data-testid="desk-section-expand-refereeRegistry"`
    - **Expect:** text "config fingerprint 08e471b10130e1e2" appears (AND, per UT-02, the new seal-unaware caveat line is also present in the Strategy Family block)
15. Click `data-testid="desk-section-expand-refereeAdjudications"`
    - **Expect:** text "No hypotheses registered." appears
16. Click `data-testid="desk-section-expand-refereeRuns"`
    - **Expect:** text "No evaluation runs recorded yet." appears

**Expected Result:**
- All 16 steps complete with their listed text visible — no step fails, no console error, no
  section breaks or fails to expand because of the new caveat markup elsewhere on the page

---

### UT-07 — The new caveat is discoverable within one click (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` → Referee Registry

**Steps:**
1. Navigate to `http://localhost:3301/desk` (home surface for this feature)
2. Look at the collapsible section headers on the page

**Expected Result:**
- A section header reading "Referee Registry" is visible without scrolling past more than the
  page's existing section list
- Clicking it (1 click) reveals the Strategy Family block containing the new caveat text — the
  disclosure is reachable within 1 click from the `/desk` page it lives on

---

### UT-08 — Scout Ledger family row still shows "N variants tried" (regression, passenger capture — TC-11, not this iteration's own scope)

**Type:** regression
**Priority:** P3
**Surface:** `/desk` → Scout Ledger

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click `data-testid="desk-section-expand-scoutLedger"`
3. Locate the block `data-testid="scout-ledger-families-block"`
4. Capture an ELEMENT-scoped screenshot of that block

**Expected Result:**
- At least one family row is visible showing text matching the pattern "N variants tried" (the
  literal count substituted for N)
- This is a pre-existing, already-shipped element — this iteration made no code change to it; the
  capture only confirms it still renders correctly on this page load

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads | smoke | P1 | `/desk` |
| UT-02 | Seal-unaware caveat renders in Strategy Family block | happy-path | P1 | `/desk` Referee Registry |
| UT-03 | Validation — N/A | n/a | n/a | n/a |
| UT-04 | Error — N/A | n/a | n/a | n/a |
| UT-05 | J-01 Microscope Readiness still works | regression | P1 | `/desk` |
| UT-06 | J-10 sentinel — all kept surfaces render | regression | P1 | `/`, `/structure`, `/desk` |
| UT-07 | Caveat discoverable in 1 click | ux | P2 | `/desk` |
| UT-08 | Scout Ledger "variants tried" row (passenger) | regression | P3 | `/desk` Scout Ledger |

**P1 tests must all pass for browser QA verdict to be PASS.**
