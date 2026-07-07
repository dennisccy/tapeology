# goal-structure_ui-iter-3 Functional Test Plan

**Phase:** goal-structure_ui-iter-3
**Date:** 2026-07-07
**Frontend Present:** yes

## Phase Goal

Build the Comparison section on the `/structure` page: choose a dataset, run `structure_tape` and `v1` backtests, render aggregates and per-class A/B/C breakdown side by side, display the champion (read-only) and simulated register verbatim from API payloads — making the honest keyless outcome (`structure_tape` non-survivor, insufficient n) visible in the browser.

## Test Cases

### TC-01 — Navigate to Structure page

**Type:** browser
**Preconditions:** Frontend running at http://localhost:3000; backend running at http://localhost:8000

**Steps:**
1. Navigate to http://localhost:3000
2. Click the **Structure** tab in the top navigation bar
3. Verify the Structure page loads

**Expected outcome:** The Structure page is displayed with the existing Levels & Zones and Registry sections visible
**Pass criteria:** The page renders without error and contains the sections described in J-01 and J-02

---

### TC-02 — Comparison section is present below Registry

**Type:** browser
**Preconditions:** Structure page loaded (TC-01 passing)

**Steps:**
1. Scroll down to view the full page
2. Locate the **Comparison** section below the Registry section

**Expected outcome:** A new Comparison section with `aria-label="structure_tape vs v1 comparison"` is visible
**Pass criteria:** The section exists, contains a dataset selector control, and a "Run comparison" button

---

### TC-03 — Dataset selector populates with registered datasets

**Type:** browser
**Preconditions:** Comparison section visible (TC-02 passing)

**Steps:**
1. Click the dataset selector dropdown in the Comparison section
2. Inspect the list of available datasets

**Expected outcome:** A non-empty list of datasets is shown
**Pass criteria:** At least one dataset appears in the dropdown; each dataset has a name and ID from `GET /research/datasets`

---

### TC-04 — Run comparison button initiates dual backtest jobs

**Type:** browser
**Preconditions:** Comparison section visible (TC-02 passing); a dataset selected in the selector

**Steps:**
1. Select a dataset from the dropdown
2. Click the "Run comparison" button
3. Observe the loading state for 2–3 seconds

**Expected outcome:** Two backtest jobs are queued (one for `v1`, one for `structure_tape`, both with `profile=default` on the chosen dataset); a loading/in-progress state is displayed
**Pass criteria:** The page transitions to an in-progress UI state; no errors are logged to the browser console; both backtest IDs are created (verifiable via `GET /research/backtests/{id}` calls returning `status: "queued"` or `status: "running"`)

---

### TC-05 — Poll loop completes when both backtests reach terminal status

**Type:** browser
**Preconditions:** Dual backtest jobs running (TC-04 passing); both backtests with dataset and strategies specified

**Steps:**
1. Wait for the poll loop to complete (both backtests reach `done`, `failed`, or `cancelled`)
2. Observe the final rendered state

**Expected outcome:** After 10–30 seconds, the page transitions from loading to displaying the backtest results or an error state
**Pass criteria:** The loading spinner disappears; either results are displayed (if both jobs succeeded) or an explicit error/failure state is shown; no infinite spinner

---

### TC-06 — Aggregates rendered verbatim from GET /research/backtests/{id}

**Type:** api
**Preconditions:** A backtest completed with `status: "done"` (may require manually running a backtest via curl if TC-05 passes)

**Steps:**
1. Run: `curl -s http://localhost:8000/research/backtests/{backtest_id_for_v1} | jq '.backtest.result.aggregates'`
2. Compare the returned JSON (n, gross_r, net_r, gross_usd, net_usd, win_rate, max_drawdown_r) with the values rendered in the browser's Comparison section for the v1 strategy

**Expected outcome:** Every numeric field matches byte-for-byte between the API response and the browser display
**Pass criteria:** n, net_r, net_usd, win_rate, max_drawdown_r all match exactly; the displayed values are not rounded or recomputed client-side

---

### TC-07 — Per-class A/B/C table populated from aggregates_by_class

**Type:** browser
**Preconditions:** Both backtests completed (TC-05 passing); results displaying

**Steps:**
1. Locate the per-class A/B/C table in the Comparison section (for both v1 and structure_tape)
2. Inspect the table rows for Class A, B, and C
3. Verify each row displays: n, net_r, net_usd, win_rate, max_drawdown_r, and insufficient_sample flag

**Expected outcome:** Three rows (A, B, C) are rendered for each strategy; all values are non-empty and readable
**Pass criteria:** All three classes are shown; the table layout is legible and matches the spec's two-column (v1 vs structure_tape) design

---

### TC-08 — insufficient_sample flag rendered verbatim per-class

**Type:** api
**Preconditions:** A completed backtest (TC-05 passing)

**Steps:**
1. Fetch the backtest result: `curl -s http://localhost:8000/research/backtests/{backtest_id} | jq '.backtest.result.aggregates_by_class'`
2. For each class (A, B, C), note the boolean value of `insufficient_sample`
3. In the browser, inspect the Comparison section's per-class table for visual indicators (e.g., badges or text) indicating insufficient sample

**Expected outcome:** The per-class `insufficient_sample` flags in the UI match the API payload verbatim
**Pass criteria:** Every class marked `insufficient_sample: true` in the API is visibly flagged in the UI; none are fabricated or recomputed

---

### TC-09 — Register string rendered verbatim from payload

**Type:** browser
**Preconditions:** Both backtests completed (TC-05 passing); results displaying

**Steps:**
1. Locate the simulated register text in the Comparison section
2. Note the exact text displayed

**Expected outcome:** The text reads "simulated — assumed fees/slippage — not indicative of live results" (the full served constant, not the goal doc's abbreviated paraphrase)
**Pass criteria:** The register text matches `REGISTER` from `backtests.py:142` exactly; no hardcoded shorter version is used

---

### TC-10 — Register string verifiable from API

**Type:** api
**Preconditions:** A completed backtest (TC-05 passing)

**Steps:**
1. Fetch one completed backtest: `curl -s http://localhost:8000/research/backtests/{backtest_id} | jq '.backtest.result.register'`
2. Compare the returned string with the register text in the browser's Comparison section

**Expected outcome:** The rendered text matches the API payload's `register` string
**Pass criteria:** No frontend literal; the string is read from the payload

---

### TC-11 — Champion badge displayed read-only (v1/default)

**Type:** browser
**Preconditions:** Both backtests completed (TC-05 passing); results displaying

**Steps:**
1. Locate the champion badge in the Comparison section
2. Verify it displays "v1" and "default"
3. Inspect for any button, link, or interactive control that could move the champion

**Expected outcome:** The champion is displayed as a read-only badge; no promotion control exists
**Pass criteria:** The champion shows v1/default; no clickable element can change the champion pointer

---

### TC-12 — No set_champion_pointer call in diff

**Type:** artifact
**Preconditions:** Code diff available for review

**Steps:**
1. Run: `git diff HEAD -- apps/frontend | grep -i "set_champion_pointer"`
2. Run: `git diff HEAD -- apps/frontend | grep -i "PUT.*strategies" | grep -v "GET"`
3. Check for any POST/PUT to `/research/strategies`

**Expected outcome:** No such calls appear in the frontend diff
**Pass criteria:** Zero matches; promotion control is not implemented

---

### TC-13 — Founding baseline row renders from PnL ledger

**Type:** browser
**Preconditions:** Both backtests completed (TC-05 passing); results displaying

**Steps:**
1. Locate the founding baseline row in the Comparison section
2. Verify it displays PnL values (e.g., net R, net $)

**Expected outcome:** A row labelled "founding baseline" (or similar) is visible beside the comparison aggregates
**Pass criteria:** The row exists and displays values from `GET /research/pnl/ledger`; the data is not fabricated

---

### TC-14 — Empty datasets state — dataset selector shows no options

**Type:** browser
**Preconditions:** Backend configured to have zero registered datasets (requires isolated environment or temp-dir override); Comparison section visible

**Steps:**
1. Scroll to the dataset selector in the Comparison section
2. Click to open the dropdown

**Expected outcome:** An empty state message is displayed (e.g., "No datasets registered")
**Pass criteria:** The dropdown shows an explicit empty state, not a broken selector or misleading content

---

### TC-15 — Running state during backtest poll

**Type:** browser
**Preconditions:** Dual backtest jobs queued or running (TC-04 passing); Comparison section displaying

**Steps:**
1. After "Run comparison" is clicked, immediately take a screenshot of the loading state
2. Verify the loading indicator and status message are clear

**Expected outcome:** An amber or slate in-progress panel displays, mirroring the Studies page's loading state
**Pass criteria:** The state is distinct from idle, completed, and failed states; a spinner or similar indicator is visible

---

### TC-16 — Failed backtest state renders distinct UI

**Type:** browser
**Preconditions:** A backtest failed (may require manual intervention via curl to cancel/fail a job)

**Steps:**
1. Trigger a failed backtest (or if one fails naturally during TC-04/TC-05, observe)
2. Verify the page displays a distinct failed state

**Expected outcome:** An explicit error/failed state is shown (mirroring `results-failed` from StudyResultsView)
**Pass criteria:** The failure is visibly distinct from loading, success, and other states; no incomplete or fabricated data is shown

---

### TC-17 — Cancelled backtest state renders distinct UI

**Type:** browser
**Preconditions:** A backtest cancelled (may require manual intervention via curl to POST `/research/backtests/{id}/cancel`)

**Steps:**
1. Trigger a cancelled backtest (if possible)
2. Verify the page displays a distinct cancelled state

**Expected outcome:** An explicit cancelled state is shown (mirroring `results-cancelled` from StudyResultsView)
**Pass criteria:** The cancellation is visibly distinct from other states

---

### TC-18 — Backend unreachable state — dataset fetch fails

**Type:** browser
**Preconditions:** Backend shut down or unavailable; Comparison section visible

**Steps:**
1. Ensure the backend is unreachable (kill the backend process)
2. Click the dataset selector dropdown to trigger `GET /research/datasets`
3. Observe the error state

**Expected outcome:** An explicit error message is displayed (e.g., "Unable to reach backend")
**Pass criteria:** No fabricated data; the error is clear and distinct

---

### TC-19 — Backend unreachable state — POST backtest fails

**Type:** browser
**Preconditions:** Backend shut down after Comparison section loads; a dataset selected

**Steps:**
1. Ensure the backend becomes unreachable while trying to POST a backtest
2. Click "Run comparison" with the backend unreachable
3. Observe the error state

**Expected outcome:** An explicit error state is displayed
**Pass criteria:** No partial/fabricated results; the error is clear

---

### TC-20 — Backend unreachable state — poll fails

**Type:** browser
**Preconditions:** Backend unreachable during the poll loop (TC-04/TC-05 running)

**Steps:**
1. Start a backtest (TC-04), then shut down the backend mid-poll
2. Observe the error handling

**Expected outcome:** An explicit error/unreachable state is displayed
**Pass criteria:** The poll loop stops cleanly; no infinite retry loop or partial data

---

### TC-21 — Honest outcome on keyless reference dataset

**Type:** browser
**Preconditions:** Both backtests completed (TC-05 passing) on the committed keyless reference dataset

**Steps:**
1. Select the keyless/reference dataset in the selector
2. Run the comparison (TC-04/TC-05)
3. Inspect the results for structure_tape

**Expected outcome:** structure_tape shows `insufficient_sample: true` on all classes (A/B/C); net_r, net_usd, win_rate, max_drawdown_r are honest (null for win_rate/max_drawdown_r if n is very low)
**Pass criteria:** structure_tape is displayed as a non-survivor (insufficient n); the champion remains v1/default; no fabricated edge case or green result

---

### TC-22 — No client-side recomputation of win_rate

**Type:** browser
**Preconditions:** Both backtests completed (TC-05 passing)

**Steps:**
1. Inspect the browser's React DevTools or Network tab for any post-processing of `win_rate`
2. Compare the displayed win_rate with the API payload's win_rate field

**Expected outcome:** The rendered value matches the API field verbatim (not recomputed from trades or aggregates)
**Pass criteria:** No client-side calculation; the value is read directly from the payload

---

### TC-23 — No client-side recomputation of aggregates

**Type:** browser
**Preconditions:** Both backtests completed (TC-05 passing)

**Steps:**
1. Verify that no React effect or computed property recalculates n, net_r, net_usd, or max_drawdown_r
2. Compare all aggregates with the API payload

**Expected outcome:** All aggregates are read directly from `GET /research/backtests/{id}` and rendered as-is
**Pass criteria:** Every aggregate matches the payload; no recomputation or rounding occurs

---

### TC-24 — J-01 regression: Levels and zones still render

**Type:** browser
**Preconditions:** Structure page visible; Comparison section added below Registry

**Steps:**
1. Scroll to the top of the Structure page
2. Verify the Levels & Zones section (J-01) is still present and functional
3. Choose a symbol and verify the chart and zones table render

**Expected outcome:** J-01's levels/zones rendering is unaffected by the addition of the Comparison section
**Pass criteria:** Levels appear on the chart; zones table displays with correct A/B/C classes; no visual occlusion or layout breakage

---

### TC-25 — J-01 chart overlay z-index intact

**Type:** browser
**Preconditions:** Structure page visible with Levels & Zones section (J-01)

**Steps:**
1. Look at the `lightweight-charts` price chart on the page
2. Verify that any overlay (e.g., a tooltip or legend) is not hidden behind other elements
3. Confirm the chart remains interactive (scroll, zoom)

**Expected outcome:** The chart is fully usable and layered correctly; no elements from the Comparison section occlude it
**Pass criteria:** The chart's z-index is preserved; overlays render above the canvas

---

### TC-26 — J-02 regression: Registry and champion still render

**Type:** browser
**Preconditions:** Structure page visible; Comparison section added below Registry

**Steps:**
1. Scroll to the Registry section (J-02)
2. Verify it displays v1 and structure_tape cards with their parameters
3. Verify the champion badge is present and shows v1/default

**Expected outcome:** The Registry section is unaffected by the Comparison section
**Pass criteria:** Both strategy cards render correctly; the champion badge displays the correct strategy and profile

---

### TC-27 — J-02 testid collision check

**Type:** artifact
**Preconditions:** Code diff available

**Steps:**
1. Search the frontend diff for testid="champion-strategy" and testid="champion-profile"
2. Count occurrences
3. If the Comparison section re-renders a champion, verify its testids are distinct (e.g., "comparison-champion-strategy")

**Expected outcome:** No duplicate testid on the same page
**Pass criteria:** If a second champion is rendered, it has unique testids (e.g., `comparison-champion-*`); no collision with Registry section testids

---

### TC-28 — Header subtitle updated (Polish, non-gating)

**Type:** browser
**Preconditions:** Structure page visible

**Steps:**
1. Inspect the header subtitle (data-testid="structure-framing")
2. Verify it mentions all three sections: Levels & Zones, Registry, and Comparison

**Expected outcome:** The subtitle text previews all three shipped sections
**Pass criteria:** The subtitle text is updated to reflect the full Structure page surface (non-gating, does not block J-03)

---

### TC-29 — README.md updated (Polish, non-gating)

**Type:** artifact
**Preconditions:** Repository files accessible

**Steps:**
1. Read `README.md`
2. Locate the "Structure page" bullet
3. Verify it describes all three sections (Levels/Zones, Registry, Comparison)

**Expected outcome:** The README's Structure page description is no longer J-01-only; it reflects the full iter-3 surface
**Pass criteria:** The bullet text mentions the comparison surface; it is not a placeholder or stale (non-gating)

---

### TC-30 — Dev handoff written

**Type:** artifact
**Preconditions:** Phase work completed

**Steps:**
1. Check for the file `docs/handoffs/goal-structure_ui-iter-3-dev.md`
2. Verify it contains a summary of the work done and any known issues

**Expected outcome:** The handoff file exists and is non-empty
**Pass criteria:** The file is present and documents the iteration's scope and outcomes

---

### TC-31 — Backend diff is empty (no backend changes)

**Type:** artifact
**Preconditions:** Repository state after implementation

**Steps:**
1. Run: `git diff HEAD -- apps/backend`
2. Verify the output is empty or contains only additive changes to `meta.py`'s `UI_ROUTES`

**Expected outcome:** `apps/backend/` has no substantive changes (only the nav-registry entry may change)
**Pass criteria:** `config.py`, `research/levels.py`, `research/backtests.py`, `research/strategies.py`, and the engine are untouched

---

### TC-32 — Backend tests pass (regression sentinel)

**Type:** api
**Preconditions:** Repository state after implementation; backend running

**Steps:**
1. Run: `cd apps/backend && python -m pytest -xvs`
2. Capture the test count

**Expected outcome:** Tests pass; at least 1146 passed, 1 skipped (the baseline from iter-2)
**Pass criteria:** Exit code 0; no regressions introduced

---

### TC-33 — config_fingerprint unchanged

**Type:** artifact
**Preconditions:** Repository state after implementation

**Steps:**
1. Run: `python3 scripts/automation/lib/config_fingerprint.py --check`
2. Verify the output shows `4d665603569b9dbf`

**Expected outcome:** The fingerprint remains unchanged
**Pass criteria:** The fingerprint is identical to the era-4 baseline

---

### TC-34 — 5-link nav intact

**Type:** browser
**Preconditions:** Structure page visible; navigation bar displayed

**Steps:**
1. Inspect the top navigation bar
2. Count the tabs/links visible

**Expected outcome:** All five navigation links are present: Cockpit, Journal, Studies, Performance, and Structure
**Pass criteria:** All five tabs render without error

---

### TC-35 — /performance page unaffected

**Type:** browser
**Preconditions:** Backend and frontend running

**Steps:**
1. Navigate to the `/performance` page
2. Verify it loads and renders correctly

**Expected outcome:** The Performance page is unchanged by iter-3 work
**Pass criteria:** The page loads; all journeys (J-04) remain passing

---

## Summary

**Total test cases:** 35
**Browser tests:** 24 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-07, TC-08, TC-09, TC-11, TC-13, TC-14, TC-15, TC-16, TC-17, TC-18, TC-19, TC-20, TC-21, TC-22, TC-23, TC-24, TC-25, TC-26, TC-28, TC-35)
**API tests:** 5 (TC-06, TC-10, TC-32, and parts of TC-18/TC-19/TC-20 that verify backend state)
**Artifact checks:** 6 (TC-12, TC-27, TC-29, TC-30, TC-31, TC-33, TC-34)

All test cases verify:
- The Comparison section renders with correct data (verbatim from payloads)
- All honest states (empty, running, failed, cancelled, insufficient-n, unreachable) are distinct
- No promotion or backend mutations occur
- No client-side recomputation
- J-01, J-02, J-04 regressions do not occur
- The register string is read from the payload, not hardcoded
