# Phase goal-rapid-microscope-iter-16 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-16
**Date:** 2026-08-20
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301

---

## Ground Rules For This Round

- **Do NOT click "Run Screen" (Scout Ledger) or "Run Walk-Forward" (Walk-Forward) in any test
  below.** A live Scout compute has previously run past 25 minutes against the real corpus without
  producing one completed candidate, with no reliable fast cancel. No test in this plan depends on
  either finishing.
- **Do NOT seed, mutate, or expose real Vault data.** Sealed exposure is single-shot and permanent.
  This round's diff does not touch the Validation Vault section at all — every Vault check below
  just reads the real store's current, already-empty state.
- **This round ships no new user-facing capability.** There is no "happy path" or "form validation"
  test category below for that reason — the phase spec states it explicitly ("New user-facing
  capability: none") and the diff confirms it (5 of 6 changed files are backend/test-only; the one
  frontend file's two edits are both resilience fixes to already-shipped sections). Coverage below
  is weighted toward smoke/regression checks that the two resilience fixes hold and nothing else
  moved, plus one optional error-path check.
- **Real store state today** (frozen at the time this plan was written, confirmed live against
  `http://localhost:8301`): Microscope Readiness has 2 real tick shards (symbol `PG`, session
  `2026-06-09`; totals "Distinct symbol-days: 1", "Distinct datasets: 2"). Scout Ledger, Walk-Forward,
  and Validation Vault are all genuinely empty (0 families / 0 fold specs / 0 sequences / 0 vault
  shards / 0 vault universes / 0 runs of any kind). Tests below are written against these actual
  values, not assumed seed data.
- **Browser-console checks are the highest-value checks in this plan.** A hydration-error defect
  previously survived a full iteration because every test lane asserted only on DOM content and none
  checked the console — it was caught only when someone opened a screenshot and noticed a red badge.
  Open DevTools → Console before expanding any section and re-check after every expand.
- **Capture notes for whoever executes this with browser automation:** (1) a viewport screenshot
  taken immediately after a large `scrollIntoView` can capture an unpainted/blank frame in headless
  Chrome — use a full-page capture for any below-the-fold section (Microscope Readiness, Scout
  Ledger, Walk-Forward, Validation Vault, and the three Referee sections are all below the fold).
  (2) `visibilityState: "hidden"` can freeze the Cockpit's live tape chart in a headless/background
  tab — if the chart looks static in a capture, verify against the backend WS/HTTP payload before
  recording it as a failure.
- If `/desk` was rebuilt recently and looks stale, `rm -rf apps/frontend/.next` and restart the
  frontend before running this plan (a known gotcha in this project's history).

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` loads cleanly with zero console errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend running at http://localhost:3301, backend running at http://localhost:8301
- No login required

**Steps:**
1. Open DevTools → Console tab
2. Navigate to `http://localhost:3301/desk`
3. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error banner
- The heading "Desk" (`data-testid="desk-title"`) is visible
- Scrolling down shows every section header, including "Microscope Readiness", "Scout Ledger",
  "Walk-Forward", "Validation Vault", and the three Referee sections, each collapsed with a closed
  "▸" arrow
- Zero red errors in the browser console

---

### UT-02 — Microscope Readiness section carries its DOM wrapper testid in all three render states (regression — this round's headline frontend fix, TC-13)

**Type:** regression
**Priority:** P1 — this is the iteration's named frontend Definition-of-Done item (TC-13) and closes
iteration 15's own COHERENCE-WARN
**Surface:** `/desk` → Microscope Readiness

**Preconditions:**
- Real corpus has 2 tick shards today (no setup required)
- Ability to stop/restart the backend process for the second half of this test

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Microscope Readiness" section header (`data-testid="desk-section-expand-microReadiness"`)
3. Once the "Corpus Totals" table appears, right-click anywhere inside the panel → Inspect → confirm
   the nearest ancestor `<div>` carries `data-testid="micro-readiness-section"`
4. Stop the backend process (e.g. `pkill -f uvicorn`, or close the terminal running it)
5. Reload `http://localhost:3301/desk`, then click "Microscope Readiness" again
6. Right-click the amber panel that appears → Inspect → confirm its wrapping `<div>` also carries
   `data-testid="micro-readiness-section"`
7. Restart the backend before running any other test in this plan

**Expected Result:**
- Step 3 (loaded state): wrapper testid present; the panel shows "Distinct symbol-days: 1",
  "Distinct datasets: 2" in the Corpus Totals table, and 2 rows (both symbol `PG`) in the "Legacy
  Tick Shards" table
- Step 6 (unavailable state): the panel reads "Backend unreachable — is the API running?" AND its
  wrapping `<div>` carries the same `data-testid="micro-readiness-section"` — before this round,
  only the loaded state carried this attribute
- Zero new console errors at any point

---

### UT-03 — Scout Ledger renders the real honest-empty state with zero console errors (smoke / regression)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk` → Scout Ledger

**Preconditions:**
- Real Scout ledger has zero registered families today (no setup required)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Open DevTools console
3. Click the "Scout Ledger" section header (`data-testid="desk-section-expand-scoutLedger"`)

**Expected Result:**
- The section expands showing the "Run Screen" button (`data-testid="scout-ledger-trigger"`) — do
  NOT click it
- The empty state "No candidates ledgered." (`data-testid="scout-ledger-families-empty"`) renders
- Below it, "Run History" shows "No scout runs recorded yet." (`data-testid="scout-ledger-runs-empty"`)
- Zero new console errors from the expansion

---

### UT-04 — [OPTIONAL, non-gating] Scout Ledger table degrades a malformed trial row gracefully under an isolated fixture (error)

**Type:** error
**Priority:** P3 — optional; not required for a PASS verdict this round. Include only if the
executing lane can stand up an isolated, scoped backend/frontend pair separate from the shared dev
instance.
**Surface:** `/desk` → Scout Ledger (isolated fixture rig only — never the shared `.data` store)

**Preconditions:**
- A SEPARATE backend process pointed at an isolated `tmp_path`-scoped (or equivalent scoped) Scout
  directory — never the operator's real `.data` store
- That directory seeded via the real, unmodified `ScoutLedger.append_row()` with one family whose
  only trial row uses the exact sparse field set
  `test_desk_scout_tool_byte_identical_on_a_populated_state` (`test_mcp_server.py`) already uses:
  `family_id`, `family_root_id`, `candidate_id`, `decision`, `reason` — no `feature`/`outcome` key
  at all
- A frontend instance pointed at that scoped backend's port

**Steps:**
1. With the scoped backend seeded as above, navigate to that frontend instance's `/desk`
2. Click "Scout Ledger"
3. Locate the seeded family's single trial row

**Expected Result:**
- The row renders without throwing — the Feature column shows `"— / —"` and the Horizon column
  shows `"—"` (the optional-chaining fallback), not a crash
- Every other section on the same page load — Microscope Readiness, Walk-Forward, Validation Vault,
  Playbook Signals, the three Referee sections — still renders normally, confirming the degradation
  is row-local, not page-wide
- **Never run this against the operator's real `.data` store.**

---

### UT-05 — Console stays clean across every collapsible Desk section (smoke — highest-value check this round)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk` (all 13 collapsible sections)

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Open DevTools → Console tab
3. Click every collapsible section header in order, waiting for each to finish loading before
   clicking the next: "Top-up Runs", "Index Reconciliation", "Screen Runs", "Screen Comparison",
   "Provenance", "Playbook Evidence", "Referee Registry", "Referee Adjudications", "Referee Runs",
   "Microscope Readiness", "Scout Ledger", "Walk-Forward", "Validation Vault"
4. Re-check the console after each expansion

**Expected Result:**
- Zero red console errors after any single expansion
- In particular, no React hydration warning of the form "Hydration failed because the initial UI
  does not match…" or "Text content did not match…" appears at any point — this specific error
  class previously escaped a full iteration's UI checks because nothing asserted on the console
- No section throws or blanks the rest of the page

---

### UT-06 — Walk-Forward and Validation Vault still render their real empty states (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` → Walk-Forward, Validation Vault

**Preconditions:**
- Real Walk-Forward ledger and Vault are both genuinely empty today (no setup required)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click "Walk-Forward" (`data-testid="desk-section-expand-walkForward"`) — confirm the "Run
   Walk-Forward" button is visible but do NOT click it
3. Click "Validation Vault" (`data-testid="desk-section-expand-validationVault"`)

**Expected Result:**
- Walk-Forward shows "No fold specs registered." (`walk-forward-fold-specs-empty`) and "No
  walk-forward sequences run." (`walk-forward-sequences-empty`)
- Validation Vault shows "No shards recorded." (`validation-vault-shards-empty`) and "No universes
  registered." (`validation-vault-universes-empty`), with no compute/seal/expose control anywhere
  in the section (it is read-only by design)
- Zero console errors from either expansion

---

### UT-07 — Playbook and Referee sections are unaffected (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` → Playbook Signals, Referee Registry, Referee Adjudications, Referee Runs

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Confirm "Playbook Signals" is visible without clicking anything (it is not collapsible)
3. Click "Referee Registry", then "Referee Adjudications", then "Referee Runs" in turn

**Expected Result:**
- "Playbook Signals" renders its content immediately, above the fold
- Each of the three Referee sections expands to show its own table/content, no error panel, no
  console error

---

### UT-08 — Cockpit live tape and chart regression (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Cockpit)

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Confirm the mode selector shows "Simulated" (the default)
3. Type `SIM-BUYER` into the ticker field
4. Click the "Watch" button

**Expected Result:**
- The chart renders and the live tape begins updating for `SIM-BUYER`
- No error banner appears
- If a headless capture shows a static-looking chart, cross-check against the backend payload
  before calling it a failure — `visibilityState: "hidden"` is known to freeze this specific chart
  in headless Chrome

---

### UT-09 — `/structure` load, Tradable Map, and Comparison dropdown regression (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- None (AAPL @ 2026-06-22 16:00:00 ET is confirmed live against the real backend to return a
  10-band Tradable Map)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `AAPL` into the "Symbol" field
3. Type `2026-06-22 16:00:00` into the "As-of (ET)" field (`data-testid="structure-as-of-input"`)
4. Click the "Load" button (`data-testid="structure-load-button"`)

**Expected Result:**
- No error banner appears
- The Tradable Map table (`data-testid="tradable-map-table"`) renders with band rows (10 bands for
  this exact symbol/as-of pair against the real backend)
- The comparison dropdown (`data-testid="comparison-dataset-select"`) is present and selectable

---

### UT-10 — Nav bar unaffected (regression)

**Type:** regression
**Priority:** P2
**Surface:** top navigation, all pages

**Preconditions:**
- None

**Steps:**
1. From any page (`/`, `/structure`, or `/desk`), look at the top navigation

**Expected Result:**
- Exactly 3 links are visible, labeled "Cockpit", "Structure", "Desk" — no fourth link, matching
  this round's "no navigation changes" scope

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads, zero console errors | smoke | P1 | `/desk` |
| UT-02 | Microscope Readiness testid present in all 3 states | regression | P1 | `/desk` → Microscope Readiness |
| UT-03 | Scout Ledger renders honest empty state | smoke | P1 | `/desk` → Scout Ledger |
| UT-04 | [Optional] Malformed Scout row degrades gracefully | error | P3 | `/desk` (isolated fixture rig) |
| UT-05 | Console clean across every Desk section | smoke | P1 | `/desk` (all sections) |
| UT-06 | Walk-Forward / Validation Vault unaffected | regression | P2 | `/desk` |
| UT-07 | Playbook / Referee sections unaffected | regression | P2 | `/desk` |
| UT-08 | Cockpit live tape + chart | regression | P1 | `/` |
| UT-09 | `/structure` load + Tradable Map + Comparison | regression | P1 | `/structure` |
| UT-10 | Nav bar unaffected | regression | P2 | nav |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-04 is explicitly optional and does
not gate the verdict.
