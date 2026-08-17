# Phase goal-rapid-microscope-iter-6 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-6
**Date:** 2026-08-17
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301 (store-scoped rig — do NOT point at the real
`.data/datasets` store; per the plan's own iteration-hygiene note, the seeder never populates it
with tick datasets)

---

**Why this plan is regression-only:** this iteration's diff is two backend Python files with zero
frontend changes (see `reports/phase-goal-rapid-microscope-iter-6-ui-surface-map.md`). There is no
new capability, form, or page to design happy-path, validation, or error test cases around — writing
any would invent a surface that does not exist. Instead, every test case below re-verifies a
pre-existing surface, because `Frontend Present: yes` is this iteration's mechanism for finally
letting the browser-QA lane dispatch after two consecutive silent skips (iter-4, iter-5). The one
new backend error path this iteration adds (`InsufficientSessionsForFoldsError`, reachable via the
CLI and the compute route) has no UI wiring at all yet — it is covered by the backend test suite
(TC-2/TC-3/TC-4 in `docs/handoffs/goal-rapid-microscope-iter-6-dev.md`), not by a browser test here.

**Preconditions for the whole plan:**
- Backend running at `http://localhost:8301` against the store-scoped rig, healthy (`GET /health`
  returns `{"status":"ok"}`).
- Frontend running at `http://localhost:3301`, after a clean `rm -rf apps/frontend/.next` rebuild
  (T-9 — the plan's own instruction, to rule out a stale build masking real evidence).
- No login/auth required (this product has none).

---

## Test Cases

### UT-01 — `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend is running at http://localhost:8301

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Playbook Signals" is visible
- No blank screen, no error banner, no unhandled exception in the browser console
- This is the baseline that J-02/J-03/J-04 (no dedicated UI element of their own) are checked
  against — see `ui-surface-map.md`'s second row

---

### UT-02 — Microscope Readiness shows real, non-fabricated corpus data (regression — J-01)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Microscope Readiness section

**Preconditions:**
- UT-01 passed (page already loaded)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the bottom of the page and click the section header with
   `data-testid="desk-section-expand-microReadiness"` (title text "Microscope Readiness")
3. Read the "Corpus Totals" table (`data-testid="micro-readiness-totals-table"`)
4. Read the "Legacy Tick Shards" table (`data-testid="micro-readiness-shards-table"`)

**Expected Result:**
- The Corpus Totals table shows "Distinct symbol-days" = `12` and "Distinct datasets" = `18`
  (element `data-testid="micro-readiness-distinct-symbol-days"` and
  `data-testid="micro-readiness-distinct-datasets"` respectively)
- The Legacy Tick Shards table renders exactly 18 data rows (`data-testid="micro-readiness-shard-rows"`),
  each with a non-empty Symbol, Session date, Checksum, Coverage gaps, and Fallback frac cell
- Every row's "Split provenance" column reads `hand_assigned` — the exact text
  `journey-scripts/J-01.json` step 2 asserts
- Every row's "Exposure state" column reads `exploratory` (never `hand_assigned` or
  `historical_oos` — proves this iteration's exposure-registry seeding fix did not leak into the
  readiness-served value, per the dev handoff's TC-7)
- This closes J-01's `evidence_makeup` flag (open since iteration 3) — this screenshot is the
  actual acceptance evidence, not merely a smoke check

---

### UT-03 — Cockpit ticker watch still works (regression — J-10 steps 1–3)

**Type:** regression
**Priority:** P1
**Surface:** `/` (cockpit)

**Preconditions:**
- None (cockpit loads with no watched ticker by default)

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Verify the text "No ticker watched" is visible
3. Type `SIM-BUYER` into the field labeled "Ticker"
4. Click the "Watch" button

**Expected Result:**
- After step 2: the empty-state text "No ticker watched" is visible before any ticker is set
- After step 4: the text "Buyer Control" appears, confirming the watch flow still completes
- No error toast or blank panel appears at any point

---

### UT-04 — `/structure` Tradable Map still loads (regression — J-10 steps 4–7)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Verify the text "Tradable Map" is visible
3. Type `AAPL` into the field labeled "Structure symbol"
4. Type `2026-06-22 17:00:00` into the field with `data-testid="structure-as-of-input"`
5. Click the element with `data-testid="structure-load-button"`

**Expected Result:**
- After step 2: "Tradable Map" heading/label is visible on page load
- After step 5: the text "300.11–302.2" appears (the pinned real S/R band for AAPL as-of
  2026-06-22 17:00:00 ET), proving the structure engine still serves byte-identical output
- No error message replaces the expected band text

---

### UT-05 — Playbook Evidence section still renders real signals (regression — J-10 steps 8–10)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Playbook Evidence section

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Verify the heading "Playbook Signals" is visible
3. Click `data-testid="desk-section-expand-playbookEvidence"`
4. Verify the text "Built from signature:" appears
5. Type `2026-06-22` into the field with `data-testid="desk-playbook-date-input"`

**Expected Result:**
- After step 4: "Built from signature:" is visible, confirming the section reads a real,
  already-computed playbook signature (not a placeholder)
- After step 5: the text "recorded signals, none hidden" appears, confirming the date-filtered
  view still serves the full, unfiltered signal set for that date

---

### UT-06 — Referee Registry section still shows the frozen fingerprint (regression — J-10 step 11)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Referee Registry section

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click `data-testid="desk-section-expand-refereeRegistry"`

**Expected Result:**
- The text "config fingerprint 08e471b10130e1e2" appears
- This is the exact fingerprint value this iteration's own backend check (TC-10,
  `Config().config_fingerprint()`) independently re-verifies — a mismatch here would mean the
  frozen foundation moved, which this iteration must not touch

---

### UT-07 — Referee Adjudications and Runs sections still render their honest-empty states (regression — J-10 steps 12–13)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Referee Adjudications section, Referee Runs section

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click `data-testid="desk-section-expand-refereeAdjudications"`
3. Verify the text "No hypotheses registered" appears
4. Click `data-testid="desk-section-expand-refereeRuns"`
5. Verify the text "No evaluation runs recorded yet." appears

**Expected Result:**
- Both empty-state messages appear exactly as written above — neither section shows a fabricated
  row, a loading spinner that never resolves, or an error message in place of the honest-empty
  state

---

### UT-08 — Microscope Readiness section is discoverable without prior knowledge (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` navigation / section list

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll down through the page's collapsible sections without using browser search (Ctrl+F)

**Expected Result:**
- A section labeled "Microscope Readiness" is visible as the last section on the page, directly
  below "Referee Runs" — reachable by scrolling alone, no more than a few seconds of scanning
- The section header text is human-readable ("Microscope Readiness"), not an internal code name

---

## Absent Test Categories (and why)

- **Happy-path / validation / error tests:** not written. This iteration ships no new form, button,
  or page — writing one would invent a UI surface the diff does not contain. The one new error path
  this iteration adds (`InsufficientSessionsForFoldsError`) has no UI wiring; it is exercised by
  the backend test suite only (`test_walkforward.py` TC-2/TC-3/TC-4), not by a browser test.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads without errors | smoke | P1 | `/desk` |
| UT-02 | Microscope Readiness shows real corpus data | regression | P1 | `/desk` → Microscope Readiness |
| UT-03 | Cockpit ticker watch still works | regression | P1 | `/` |
| UT-04 | `/structure` Tradable Map still loads | regression | P1 | `/structure` |
| UT-05 | Playbook Evidence section still renders | regression | P1 | `/desk` → Playbook Evidence |
| UT-06 | Referee Registry shows frozen fingerprint | regression | P1 | `/desk` → Referee Registry |
| UT-07 | Referee Adjudications/Runs honest-empty states | regression | P1 | `/desk` → Referee Adjudications, Referee Runs |
| UT-08 | Microscope Readiness discoverable | ux | P2 | `/desk` navigation |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-02 additionally closes J-01's
`evidence_makeup` flag; UT-03 through UT-07 collectively re-run `journey-scripts/J-10.json`'s
13-step sentinel by surface.
