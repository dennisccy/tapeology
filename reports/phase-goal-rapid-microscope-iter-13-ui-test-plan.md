# Phase goal-rapid-microscope-iter-13 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-13
**Date:** 2026-08-19
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301

---

## Scope note — read before running

This iteration shipped **zero frontend changes** (confirmed: `git status --porcelain
apps/frontend/` is empty). The code that changed — `vault.recover_shard_ledger`'s halt-only
recovery rewrite — has no route, button, or CLI wired to it, so **no test case below targets it
directly**; its correctness is proven entirely by the backend unit suite (dev handoff cites
TC-1–TC-9 plus the six-trap TR-29 table, full suite 3227 collected / 3219 passed / 8 skipped / 0
failed). Every test case below is a **regression/sentinel check** on the three already-shipped
routes (`/`, `/structure`, `/desk`), per plan.md's TC-11 (J-10 kept-product sentinel) and TC-10/J-01
(Microscope Readiness re-check). The correct pass condition for all of them is **sameness with the
already-established shipped appearance** — a passing result here means "nothing broke," not "a new
capability was verified."

**Test type coverage note:** `validation` and `error` test types (in their literal
new-form/new-error-surface sense) do not apply this iteration — no form changed and the one
error-path this iteration hardens (the vault's halt-on-unprovable-recovery) has no UI entry point.
UT-07 substitutes the closest UI-observable edge condition (an honest-absence empty state) rather
than a fabricated case. `happy-path` below is reused in its regression sense — the core existing
workflow on each kept surface still completes end-to-end.

**Evidence-capture notes for whoever executes this (browser-qa-agent):**
- A viewport screenshot taken immediately after a large `scrollIntoView` can capture an unpainted
  (blank) frame in headless Chrome — use a full-page capture instead, or wait ~500ms after
  scrolling before capturing.
- `visibilityState: "hidden"` can freeze the Cockpit's live tape chart in a headless pass. If UT-04's
  chart looks static in a screenshot, verify against the backend/WS payload before reporting it as a
  failure — this is a known headless-capture artifact, not a product regression.

---

## Test Cases

---

### UT-01 — Cockpit `/` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at `http://localhost:3301`
- Backend running and healthy (`GET http://localhost:8301/health` returns `{"status":"ok"}`)

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Wait for the page to fully load

**Expected Result:**
- The top bar (ticker input plus Watch/Stop/Pause/Resume controls) renders — no blank screen
- No error banner is shown
- No console errors

---

### UT-02 — Structure `/structure` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at `http://localhost:3301`

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to fully load

**Expected Result:**
- The heading element with `data-testid="structure-title"` is visible
- The "Tradable Map" panel is visible as the default view (per this page's own comment: "Tradable
  Map is the default view, read verbatim from GET /research/tradability")
- No console errors

---

### UT-03 — Desk `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend running at `http://localhost:3301`

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- The "Playbook Signals" panel and the "Backscan" panel are visible immediately (both render
  unconditionally, no click needed)
- No blank screen, no error message, no console errors

---

### UT-04 — Cockpit live tape and chart still render for a watched ticker (happy-path / regression)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at `http://localhost:3301`, backend at `http://localhost:8301`
- Default data mode is "sim" (no external credentials required)

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Type `AAPL` into the ticker input in the top bar
3. Click the "Watch" button
4. Wait up to 10 seconds

**Expected Result:**
- The cockpit leaves its idle state (a "Connecting to AAPL…" acknowledgement may appear briefly,
  then clear)
- A price chart renders below the top bar
- Live tape data (price/volume ticks) begins appearing
- No error banner appears
- See the evidence-capture note above if the chart appears static in a headless screenshot

---

### UT-05 — Structure Tradable Map loads and the Comparison dataset dropdown still works (happy-path / regression)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at `http://localhost:3301`
- Real `.data` store has 18 registered datasets (confirmed via `ls apps/backend/.data/datasets`)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Confirm the "Tradable Map" panel is visible as the default view (no click needed)
3. Scroll down to the "Comparison" panel and click the dropdown with `data-testid="comparison-dataset-select"`
4. Select any dataset from the list (not the default "Choose a dataset…" placeholder option)

**Expected Result:**
- Step 2: the Tradable Map panel shows band/zone data with no unavailable-panel state
- Step 3: the dropdown opens and lists registered datasets — it must NOT show the
  `data-testid="comparison-no-datasets"` empty state ("No datasets registered.")
- Step 4: selecting a dataset populates the comparison view below the dropdown with no console
  error or crash

---

### UT-06 — Desk Microscope Readiness Corpus Totals render from the real store (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend running at `http://localhost:3301`

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the bottom of the page to the last section, "Microscope Readiness"
3. Click the "Microscope Readiness" section header to expand it (this section starts collapsed on
   every page load by design — "every reload starts from the decluttered page")

**Expected Result:**
- A table with `data-testid="micro-readiness-totals-table"` appears, titled "Corpus Totals", with
  five rows: "Distinct symbol-days", "Distinct datasets", "RTH minutes covered",
  "Session-equivalents", "Referee tick-gate (symbol-days)"
- The unavailable panel `data-testid="micro-readiness-unavailable"` does NOT appear — the section
  loads successfully from `GET /research/desk/micro/readiness`

---

### UT-07 — Desk Legacy Tick Shards shows the honest-absence empty state, not a crash (regression / edge case)

**Type:** regression
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Continue directly from UT-06 with "Microscope Readiness" already expanded
- Real `.data` store has zero recorded tick shards and no `micro_vault` directory

**Steps:**
1. With "Microscope Readiness" expanded, scroll to the "Legacy Tick Shards" subsection heading
   (directly below "Corpus Totals")

**Expected Result:**
- The empty state with `data-testid="micro-readiness-shards-empty"` is visible, showing the text
  "No tick shards recorded."
- The table `data-testid="micro-readiness-shards-table"` does NOT render (correctly absent when
  there are zero shards — this is the expected, unchanged behavior on the real store, not a defect)
- No crash, no blank section, no red/error-styled text

---

### UT-08 — Desk Referee and Playbook sections still render unaffected (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- Frontend running at `http://localhost:3301`

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Confirm the "Playbook Signals" panel shows content or its own empty state (always visible, no
   click needed)
3. Click the "Referee Registry" section header to expand it
4. Click the "Referee Adjudications" section header to expand it
5. Click the "Referee Runs" section header to expand it

**Expected Result:**
- Step 2: "Playbook Signals" renders without an error state
- Steps 3–5: each Referee section expands and renders its existing content (registered hypotheses
  table / adjudication fold / run controls) exactly as before this iteration — none of these three
  sections read `vault.py`, so none can be affected by this iteration's code changes
- No console errors on any of the three expand actions

---

### UT-09 — Top-level navigation between Cockpit / Structure / Desk still works (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Navigate directly to `http://localhost:3301/structure`
3. Navigate directly to `http://localhost:3301/desk`

**Expected Result:**
- Each of the three routes loads without a blank page, a 404, or a console error
- Nothing was added to or removed from this three-route set this iteration

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit loads | smoke | P1 | `/` |
| UT-02 | Structure loads | smoke | P1 | `/structure` |
| UT-03 | Desk loads | smoke | P1 | `/desk` |
| UT-04 | Cockpit live tape/chart still render | happy-path | P1 | `/` |
| UT-05 | Structure Tradable Map + Comparison dropdown | happy-path | P1 | `/structure` |
| UT-06 | Desk Microscope Readiness Corpus Totals | regression | P1 | `/desk` |
| UT-07 | Desk Legacy Tick Shards empty state | regression | P1 | `/desk` |
| UT-08 | Desk Referee/Playbook sections unaffected | regression | P2 | `/desk` |
| UT-09 | Cross-route navigation | ux | P2 | nav |

**P1 tests must all pass for browser QA verdict to be PASS.** A PASS here means "the kept product
is unchanged," which is the correct and expected outcome for this backend-only iteration.
