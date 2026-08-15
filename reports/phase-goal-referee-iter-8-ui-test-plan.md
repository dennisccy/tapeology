# Phase goal-referee-iter-8 — UI Test Plan

**Phase:** goal-referee-iter-8
**Date:** 2026-08-15
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301

---

## Important note on the write path

Registering a shortlist candidate (UT-06 below, and anything that depends on it: UT-07, UT-08,
UT-09) performs a **real, permanent write** to whichever registry store the running backend
points at — this is the one genuine, irreversible action in this iteration's UI. As of this
writing the live store is empty (`GET /research/desk/referee/registry` → `"hypotheses": []`),
matching the project's own explicit design: real production registrations are optional and
operator-gated this iteration (`docs/goal.md` J-07 acceptance text; the phase spec's own OUT OF
SCOPE list says "do not fabricate a registration"). Run UT-06 onward against a disposable/fixture
backend where one is available; if run against a shared instance, do so only intentionally.
UT-01 through UT-05, UT-10, and UT-11 are all read-only/non-destructive and safe to run anytime.

---

## Test Cases

---

### UT-01 — Desk page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend is running at http://localhost:8301 (`curl http://localhost:8301/health` returns
  `{"status":"ok"}`)
- No login is required (this project has no auth gate)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The heading "Desk" (`data-testid="desk-title"`) is visible near the top
- The top nav bar shows exactly three links: "Cockpit", "Structure", "Desk"
- No console errors

---

### UT-02 — Referee Registry section expands and shows all 5 shortlist candidates (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk` → Referee Registry section

**Preconditions:**
- UT-01 passed

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the very bottom of the page
3. Click the "Referee Registry" section header (the last section on the page, directly below
   "Playbook Evidence")

**Expected Result:**
- The section expands — its arrow glyph flips from "▸" to "▾"
- A table (`data-testid="referee-shortlist-table"`) renders with exactly 5 rows, with
  `data-testid` values `referee-shortlist-row-S-1` through `referee-shortlist-row-S-5`, in that
  order
- Each row shows a Candidate id, an Estimand ("A", "B", or "C"), a Setup/Side value, a Primary
  horizon, a non-empty Rationale sentence, and numeric values in the n / Sessions / Accrual per
  day / Projected days columns
- A "Registered Hypotheses" heading renders below the shortlist, followed by either a table or
  the text "No hypotheses registered."

---

### UT-03 — Zero-corpus candidates render honest placeholder values, never a crash (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk` → Referee Registry shortlist table

**Preconditions:**
- Referee Registry section expanded (UT-02)
- As of 2026-08-15, live candidates S-4 and S-5 (`range_trade:long`, `at_wall` context) have zero
  recorded matching signals (verified via `curl http://localhost:8301/research/desk/referee/registry/shortlist`)

**Steps:**
1. With the Referee Registry section expanded, locate row `referee-shortlist-row-S-4`
2. Read its "Accrual / day" and "Projected days" cells
3. Repeat for row `referee-shortlist-row-S-5`

**Expected Result:**
- Both rows render completely — candidate id, estimand ("B" for S-4 / "C" for S-5), and
  "range_trade:long (at_wall)" in the Setup/Side column — the row is never missing or blank
- The "Accrual / day" cell reads "0.00" (not blank, "NaN", or "Infinity")
- The "Projected days" cell reads "—" (an em dash), not "0", "NaN", or "Infinity"
- No error message appears and the page does not crash or blank out

---

### UT-04 — Operator selects a candidate and reviews the confirmation panel (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Referee Registry

**Preconditions:**
- Referee Registry section expanded
- Candidate S-4 not yet registered (its button reads "Select", not "Registered")

**Steps:**
1. In the shortlist table, click the "Select" button in row `referee-shortlist-row-S-4`
   (`data-testid="referee-shortlist-select-S-4"`)

**Expected Result:**
- A confirmation panel (`data-testid="referee-registration-confirm-panel"`) appears directly
  below the shortlist table
- The panel's text reads exactly: "Register S-4 (range_trade:long, Estimand B)? This records a
  permanent, boundary-stamped hypothesis — the boundary is stamped at registration time and can
  never move."
- Two buttons are visible: "Confirm Registration" and "Cancel"
- No write has occurred yet — the "Registered Hypotheses" table/empty-state is unchanged

---

### UT-05 — Operator cancels a pending selection (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Referee Registry confirmation panel

**Preconditions:**
- UT-04's confirmation panel is open for S-4

**Steps:**
1. Click the "Cancel" button (`data-testid="referee-registration-cancel-button"`) in the
   confirmation panel

**Expected Result:**
- The confirmation panel disappears immediately
- Row `referee-shortlist-row-S-4`'s action button still reads "Select" (not "Registered")
- The "Registered Hypotheses" table/empty-state is unchanged from before UT-04 step 1 — confirms
  no write occurred

---

### UT-06 — Operator completes registration end-to-end (happy-path — real, permanent write)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Referee Registry

**CAUTION:** This test performs a genuine, irreversible write to the registry store the running
backend uses. See "Important note on the write path" above before running this test.

**Preconditions:**
- Referee Registry section expanded
- Pick any shortlist row whose button still reads "Select" — this test uses S-1
  (`capitulation:long`), which as of 2026-08-15 shows `n=1`, `n_sessions=1`, accrual rate "0.02",
  and 517 projected days

**Steps:**
1. Click "Select" on row `referee-shortlist-row-S-1`
2. In the confirmation panel, click "Confirm Registration"
   (`data-testid="referee-registration-confirm-button"`)

**Expected Result:**
- Both panel buttons disable, and the Confirm button's label changes to "Registering…" while the
  request is in flight
- On success, the confirmation panel closes and a new row (`referee-hypotheses-row-S-1`) appears
  in the "Registered Hypotheses" table showing: Hypothesis id "S-1", Setup/Side
  "capitulation:long", a Boundary date (today's date), Origin "historical-exploration", and a
  Status value (e.g. "active")
- Row `referee-shortlist-row-S-1`'s action button now reads "Registered" and is disabled

---

### UT-07 — Discovery vs. accrual counts render distinctly on a registered hypothesis (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Referee Registry "Registered Hypotheses" table

**Preconditions:**
- UT-06 completed for S-1 (a candidate that already had `n ≥ 1` matching historical evidence at
  registration time)

**Steps:**
1. In the "Registered Hypotheses" table, locate row `referee-hypotheses-row-S-1`
2. Read its "Accrual" and "Discovery" cells

**Expected Result:**
- The "Accrual" cell shows "0 / 12" — zero post-boundary sessions have occurred yet since
  registration happened moments ago; target is 12
- The "Discovery" cell (`data-testid="referee-discovery-S-1"`) shows a count greater than zero
  (observed live on 2026-08-15: "1 / 1") followed by the italic text "discovery (exploratory)"
- The Discovery number and its label are visually distinct from the Accrual cell — a separate
  column, plain italic text, never a colored badge

---

### UT-08 — Already-registered candidate cannot be re-selected (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/desk` → Referee Registry shortlist table

**Preconditions:**
- At least one candidate (e.g. S-1 from UT-06) is already registered

**Steps:**
1. Reload `http://localhost:3301/desk` and re-expand "Referee Registry"
2. Locate row `referee-shortlist-row-S-1`

**Expected Result:**
- The row's action button reads "Registered" instead of "Select", and is visually disabled
- Clicking it produces no effect — no confirmation panel opens

---

### UT-09 — Stale-tab duplicate registration attempt surfaces the backend's refusal inline (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` → Referee Registry confirmation panel

**Preconditions:**
- Two browser tabs (Tab A, Tab B) both open to `http://localhost:3301/desk` with "Referee
  Registry" expanded in both
- A shortlist candidate not yet registered (this test uses S-2, `jbe:long`)

**Steps:**
1. In Tab A, click "Select" on row `referee-shortlist-row-S-2` — leave the confirmation panel
   open, do NOT click Confirm yet
2. In Tab B, click "Select" on the same row `referee-shortlist-row-S-2`, then click "Confirm
   Registration" — verify it succeeds and a new row appears in Tab B's "Registered Hypotheses"
   table
3. Switch back to Tab A (whose data is now stale — it never re-fetched) and click "Confirm
   Registration" on its still-open panel for S-2

**Expected Result:**
- Tab A's request is refused by the backend (HTTP 409 conflict)
- An inline red error line (`data-testid="referee-registration-error"`) appears inside Tab A's
  confirmation panel, showing the backend's own explanation text — not a generic client-side
  message
- Tab A's page does not crash, blank out, or lose the rest of the Referee Registry section

---

### UT-10 — "Playbook Evidence" and prior /desk sections are unaffected (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/desk` (all pre-existing sections)

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Playbook Evidence" section header (directly above the new "Referee Registry"
   section)

**Expected Result:**
- "Playbook Evidence" expands and shows its existing content exactly as it did before this
  phase — no visual shift, no missing data, no broken layout caused by the new section below it
- Every other pre-existing section (Screen history, Forward Returns, Briefing, Playbook Signals,
  Backscan, Top-up runs, Index Reconciliation, Screen Runs, Screen Comparison, Provenance,
  Skipped members) is still present in its prior position, above "Referee Registry"

---

### UT-11 — Referee Registry section is discoverable without prior knowledge (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/desk` navigation / layout

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk` as if for the first time
2. Scroll down the page looking for anything related to hypotheses, research questions, or
   "Referee"

**Expected Result:**
- A section clearly labeled "Referee Registry" is reachable with a single scroll and a single
  click (to expand) — no separate navigation item, no hidden menu, no undocumented URL needed
- The section's own intro text ("Spec-pinned starter-family candidates
  (docs/referee-statistical-spec.md §7) beside their live sample-size readiness…") explains what
  the section is in plain language before any table needs to be read

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Desk page loads without errors | smoke | P1 | `/desk` |
| UT-02 | Referee Registry expands, 5 shortlist rows render | smoke | P1 | `/desk` → Referee Registry |
| UT-03 | Zero-corpus candidates render honestly, never crash | smoke | P1 | `/desk` → shortlist table |
| UT-04 | Select a candidate, review confirm panel | happy-path | P1 | `/desk` → Referee Registry |
| UT-05 | Cancel a pending selection | happy-path | P1 | `/desk` → confirm panel |
| UT-06 | Complete registration end-to-end (real write) | happy-path | P1 | `/desk` → Referee Registry |
| UT-07 | Discovery vs. accrual render distinctly | happy-path | P1 | `/desk` → hypotheses table |
| UT-08 | Already-registered candidate can't be re-selected | validation | P2 | `/desk` → shortlist table |
| UT-09 | Stale-tab duplicate registration shows inline error | error | P2 | `/desk` → confirm panel |
| UT-10 | Playbook Evidence and prior sections unaffected | regression | P3 | `/desk` |
| UT-11 | Referee Registry is discoverable | ux | P3 | `/desk` navigation |

**P1 tests must all pass for browser QA verdict to be PASS.**
