# Phase goal-desk-iter-31 — UI Test Plan

**Phase:** goal-desk-iter-31
**Date:** 2026-07-31
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
- Frontend is running at `http://localhost:3301`
- Backend is running at `http://localhost:8301` (the ambient `/desk` store already has recorded screen runs — no setup needed)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load (the "Screen Runs" panel data finishes fetching)

**Expected Result:**
- Page renders without a blank screen or error message
- The heading with `data-testid="desk-title"` reading "Desk" is visible
- A panel titled "Screen Runs" is visible
- No browser console errors

---

### UT-02 — Reused latest run suppresses the "not reached" note and the counts line (happy path — the core fix)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → "Screen Runs" panel → "Latest run" detail block (`LatestScreenRunDetail`)

**Preconditions:**
- The ambient store's latest recorded screen run is `screenrun-2026-07-31-fe0829e64a0d`
  (`state: "done"`, `reused: true`, `members_attempted: 0` of `members_total: 101`,
  `screen_id: "screen-2026-07-31-c169546856c7"`) — confirm with
  `curl -s http://localhost:8301/research/desk/screen/runs | python3 -c "import json,sys; print(json.load(sys.stdin)['latest']['id'])"`
  and expect it to print `screenrun-2026-07-31-fe0829e64a0d`. If a newer run has since been
  recorded, re-derive its `state`/`reused`/`id` the same way before running this test.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll down to the panel titled "Screen Runs"
3. Locate the sub-heading reading "Latest run — 2026-07-31 · screenrun-2026-07-31-fe0829e64a0d"
4. Inspect the row of small text directly below that heading (state / attempted / elapsed / outcome)
5. Inspect the area immediately below that row (where the amber note and counts line would render)

**Expected Result:**
- The element `data-testid="desk-screen-run-latest-outcome"` reads exactly
  "reused screen-2026-07-31-c169546856c7 — no walk was performed"
- No element with `data-testid="desk-screen-run-latest-unreached"` is present anywhere on the page
  (i.e. no amber "101 members not reached" text)
- No element with `data-testid="desk-screen-run-latest-counts"` is present anywhere on the page
  (i.e. no "0 ranked · 0 skipped (no bars) · 0 skipped (no basis)" line)
- The element `data-testid="desk-screen-run-latest-attempted"` still reads "0 of 101 members attempted" (unaffected — this element is not part of the suppression)

---

### UT-03 — Screen Runs history table still shows the full append-only record (regression — ties to J-18)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → "Screen Runs" panel → history table (`data-testid="desk-screen-runs-table"`)

**Preconditions:**
- The ambient store contains at least one completed full-walk run (e.g. `screenrun-2026-07-31-725c4ec2bfcd`, `101/101` attempted) and at least one reused run

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the "Screen Runs" panel and locate the table with `data-testid="desk-screen-runs-table"`
3. Read every row's "attempted / total" cell (`data-testid="desk-screen-run-attempted"`)
4. Read every row's "produced" cell (`data-testid="desk-screen-run-outcome"`)

**Expected Result:**
- At least one row's attempted/total cell reads "101 / 101"
- At least one row's produced cell contains the substring "no walk was performed"
- The table itself is unaffected by this iteration's "Latest run" detail fix — every row from prior
  runs is still present (nothing was removed from the append-only history)

---

### UT-04 — Crash-before-any-attempt no longer fabricates a `failed_member` (backend-verified — not live-triggerable)

**Type:** error
**Priority:** P2
**Surface:** `apps/backend/app/research/desk_screen_compute.py` → `run_screen_and_record`, rendered on `/desk` by `data-testid="desk-screen-run-latest-failed"` if such a run ever becomes "latest"

**Preconditions:**
- None (this runs against the committed test fixtures, not the live ambient store — the ambient
  store currently has no crash-before-any-attempt run to inspect through the browser)

**Steps:**
1. Open a terminal in the repository root
2. Run:
   `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_screen_compute.py -k "test_tc1_a_crash_before_any_member_is_attempted_records_failed_member_null or test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_failed_member" -q`

**Expected Result:**
- Both tests pass (`2 passed`)
- This confirms: a run that crashes before attempting any member records `failed_member: null`
  (TC-1, the new honesty fix), while a run that crashes after genuinely reaching a member still
  correctly names that member (TC-2 regression guard, unchanged)
- Should either test ever be recorded as the ambient store's "latest" run in the future, the
  frontend's existing (unchanged) `run.failed_member ?? "(member not recorded)"` fallback on
  `apps/frontend/app/desk/page.tsx` line ~1346 will render "(member not recorded)" for the
  null case instead of a fabricated company symbol — this can be confirmed by reading that line

---

### UT-05 — `/desk` is discoverable from the top navigation (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation bar (`data-testid="app-nav"`)

**Preconditions:**
- Frontend is running at `http://localhost:3301`

**Steps:**
1. Navigate to `http://localhost:3301` (the Cockpit home page)
2. Look at the top navigation bar (`data-testid="app-nav"`)

**Expected Result:**
- A link labeled "Desk" (`data-testid="nav-link"`) is visible in the navigation bar
- Clicking it navigates to `http://localhost:3301/desk` and that link becomes the active
  (highlighted) one — this is unchanged from before this iteration; the fix does not add or move
  any navigation entry

---

### UT-06 — `done && !reused` counts line stays byte-unchanged (regression — code-read verification)

**Type:** regression
**Priority:** P3
**Surface:** `/desk` → `LatestScreenRunDetail`, `data-testid="desk-screen-run-latest-counts"`

**Preconditions:**
- None — this branch is not exercisable live this iteration because the ambient store's current
  *latest* run is reused, not a genuine full walk (logged in
  `runs/goal-session-desk/state/assumptions.md`, iter-31)

**Steps:**
1. Open `apps/frontend/app/desk/page.tsx` and locate the `LatestScreenRunDetail` function
   (around line 1312)
2. Read the block starting `{run.state === "done" && !run.reused && (` (around line 1337)
3. Compare the JSX inside it (`{run.ranked_count} ranked · {run.skipped_by_reason.no_bars} skipped
   (no bars) · {run.skipped_by_reason.no_basis} skipped (no basis)`) against the pre-iteration
   version at `git show 48c5fc2:apps/frontend/app/desk/page.tsx` (the last commit before this
   iteration's changes)

**Expected Result:**
- The only diff in this component versus `48c5fc2` is the two added boolean guards
  (`!(run.state === "done" && run.reused)` and `!run.reused`) — the JSX content inside both
  conditionally-rendered blocks, and every other line of the component, is character-for-character
  identical
- Confirm with: `git diff 48c5fc2 -- apps/frontend/app/desk/page.tsx` and verify only the two `+`/`-`
  lines shown are the added `&&` conditions

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads without errors | smoke | P1 | `/desk` |
| UT-02 | Reused latest run suppresses note/counts | happy-path | P1 | `/desk` "Screen Runs" latest-run block |
| UT-03 | History table retains full append-only record | regression | P1 | `/desk` `desk-screen-runs-table` |
| UT-04 | Crash-before-any-attempt records null `failed_member` | error | P2 | backend `desk_screen_compute.py` |
| UT-05 | `/desk` discoverable from top nav | ux | P2 | `app-nav` |
| UT-06 | `done && !reused` counts line byte-unchanged | regression | P3 | `/desk` `desk-screen-run-latest-counts` |

**P1 tests must all pass for browser QA verdict to be PASS.**
