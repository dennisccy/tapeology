# Phase goal-rapid-microscope-iter-14 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-14
**Date:** 2026-08-19
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301 (backend http://localhost:8301)

---

## Before You Start — Operational Notes

- **The Scout "Run Screen" and Walk-Forward "Run Walk-Forward" buttons start REAL, long-running
  computations against the live backend.** The developer observed the first of 6 Scout candidates
  still not finished after 25+ minutes of wall-clock time against the real 18-dataset corpus. Do
  not run UT-06 or UT-08 (the "reaches a terminal state" tests) back-to-back with other tests that
  need a fast or idle backend — running a live compute concurrently with other backend load once
  made `/health` briefly unresponsive to ALL routes this same iteration. If you need a fast check
  of the full trigger→terminal cycle, use a scoped/fixture-backed backend instance instead.
- **The real `.data` store today has zero Scout families, zero Vault shards/universes, and one
  populated Walk-Forward sequence.** Test steps below are written against this real, live state —
  not a hypothetical. If the store's contents change before you run this plan (e.g., a Scout run
  has since completed and written ledger rows), treat any real, non-fabricated row as satisfying
  the "populated" assertions; the empty-state assertions may no longer apply and are not failures.
- **Do not seed, mutate, or expose Validation Vault data to run these tests.** The Vault section is
  deliberately read-only in this iteration and has no control for it in the UI. The two-stage
  opaque/revealed rendering paths (TC-4/TC-5 in the phase spec) were already verified by the code
  reviewer using a constructed backend fixture and a field-by-field source trace — see
  `reports/reviews/goal-rapid-microscope-iter-14-review.md`. UT-04 below tests what is honestly
  observable on the real, live instance today (the empty state).
- **If capturing screenshots as evidence (e.g. via headless Chrome), take a full-page screenshot
  (`fullpage: true`), not a viewport or single-element capture, for any state reached after
  scrolling or after expanding a section below the fold.** This session's headless-Chrome setup
  reproducibly returns a blank/uniform-color PNG for viewport or element screenshots taken shortly
  after a large `scrollIntoView` — a tooling characteristic (confirmed against a pre-existing,
  unmodified section), not a sign the content failed to render. A full-page capture after the same
  scroll renders correctly.
- **If the Cockpit (`/`) chart looks static or frozen during a headless pass (UT-16), verify
  against the backend payload before reporting it as broken.** A headless tab whose
  `visibilityState` is `"hidden"` is known to freeze this specific live tape chart even though the
  underlying data keeps updating — an environment quirk, not a product regression.

---

## Test Cases

---

### UT-01 — `/desk` loads with all sections present but collapsed (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend running at http://localhost:3301, backend running at http://localhost:8301

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- Section headers "Microscope Readiness", "Scout Ledger", "Walk-Forward", and "Validation Vault"
  are all visible on the page, each showing a closed "▸" arrow (not expanded)
- No console errors
- The top navigation shows exactly "Cockpit", "Structure", "Desk"

---

### UT-02 — Operator can view Scout Ledger contents (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Scout Ledger section

**Preconditions:**
- On `http://localhost:3301/desk`

**Steps:**
1. Click the "Scout Ledger" section header (`data-testid="desk-section-expand-scoutLedger"`)
2. Observe the section body that appears

**Expected Result:**
- The header's arrow changes from "▸" to "▾" and `aria-expanded` becomes `true`
- A line reading "Ledger chain verification: ok" is visible
- Given the real backend has zero registered families today: an empty-state block reading "No
  candidates ledgered." appears (no fabricated rows). If a family exists instead, its header reads
  `"<family_id> — N variants tried"` and is followed by a 9-column table with headers Candidate,
  Feature, Horizon, Registered, Decision, Reason, Notes, Withheld excluded, Screen detail
- Below that, a "Run History" sub-heading appears, followed by either "No scout runs recorded
  yet." or a 6-column table (Run, State, Started, Finished, Candidates, Error)
- An enabled "Run Screen" button and no "Cancel" button are visible

---

### UT-03 — Operator can view Walk-Forward contents (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Walk-Forward section

**Preconditions:**
- On `http://localhost:3301/desk`

**Steps:**
1. Click the "Walk-Forward" section header (`data-testid="desk-section-expand-walkForward"`)
2. Observe the section body that appears

**Expected Result:**
- The header's arrow changes from "▸" to "▾"
- A line reading "Ledger chain verification: ok" is visible
- A "Fold Specs" block appears with at least one collapsed `corpus_id` detail row (the real ledger
  has at least one registered fold spec today)
- Given the real backend's Walk-Forward ledger is non-empty today: at least one sequence block
  appears, each showing a "Sequence verdict:" line (either a verdict string or "refused — <reason>
  ..."), an 8-column fold table (Fold, Status, Effect, N, Sessions, Sign, Evidence class, Process
  label) with at least one row, and a "Recency — older N folds (...), recent N folds (...)" line
- Below that, a "Run History" sub-heading and either "No walk-forward runs recorded yet." or a
  7-column table (Run, State, Started, Finished, Steps, Folds evaluated, Error)
- An enabled "Run Walk-Forward" button and no "Cancel" button are visible

---

### UT-04 — Operator can view Validation Vault contents, read-only (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Validation Vault section

**Preconditions:**
- On `http://localhost:3301/desk`

**Steps:**
1. Click the "Validation Vault" section header (`data-testid="desk-section-expand-validationVault"`)
2. Observe the section body that appears
3. Scan the entire section body for any button, input, or clickable control

**Expected Result:**
- The header's arrow changes from "▸" to "▾"
- Two lines are visible: "Shard ledger chain verification: ok" and "Universe ledger chain
  verification: ok"
- Given the real vault store is empty today: a "Shards" block shows "No shards recorded." and a
  "Universes" block shows "No universes registered." — zero table rows, zero fabricated data
- **No button, form, or interactive control of any kind exists anywhere inside
  `[data-testid="validation-vault-section"]`** — confirms the section is genuinely read-only (no
  seal/assign/expose/compute control)
- Nothing in this section's rendered text references `/research/datasets` or repeats a value from
  the Microscope Readiness section above it

---

### UT-05 — Scout "Run Screen" starts a run and shows live progress (happy path, fast slice)

**Type:** happy-path
**Priority:** P2 *(see Operational Notes — this click has a real, lasting side effect on the shared
backend, so it is not treated as an unconditionally-safe P1 despite being fast to observe)*
**Surface:** `/desk` — Scout Ledger compute control

**Preconditions:**
- Scout Ledger section expanded (UT-02)
- No other Scout screening run currently in flight
- You are prepared for this test to leave a real computation running in the background for 25+
  minutes afterward (see Operational Notes) — this test itself only requires observing the first
  ~1 second of that run

**Steps:**
1. Click the "Run Screen" button (`data-testid="scout-ledger-trigger"`)
2. Within 1–2 seconds, observe the button and the area around it

**Expected Result:**
- The button's label changes from "Run Screen" to "Screening…" and becomes disabled
- A line appears reading "0 / 6 candidates" (or another real total) with a small pulsing dot beside
  it (`data-testid="scout-ledger-progress"`)
- A "Cancel" button appears (`data-testid="scout-ledger-cancel"`)
- No error text appears in `data-testid="scout-ledger-trigger-error"`
- You do NOT need to wait further for this test case to pass — proceed to UT-06 only if you
  intend to observe the full run lifecycle

---

### UT-06 — Scout run can be cancelled and reaches a terminal state (happy path, long-running — OPTIONAL)

**Type:** happy-path
**Priority:** P3 (informational — not required for a PASS verdict; see Operational Notes)
**Surface:** `/desk` — Scout Ledger compute control

**Preconditions:**
- UT-05 has just been run and a Scout screening run is currently in the "Screening…" state
- You have budgeted real wall-clock time for this test (the developer observed candidate 1 of 6
  still incomplete after 25+ minutes on the real corpus) — do not run this as part of a fast smoke
  pass

**Steps:**
1. Click the "Cancel" button (`data-testid="scout-ledger-cancel"`)
2. Observe the button immediately after clicking
3. Wait and periodically re-check the section (this may take a long time; the backend's abort
   check only fires at candidate boundaries, so cancelling mid-candidate will not stop it
   instantly)

**Expected Result:**
- Immediately after clicking: the Cancel button's label changes to "Cancelling…" and becomes
  disabled
- Eventually (candidate-boundary-dependent, not necessarily fast): the run reaches a terminal
  state — the "Run Screen" button becomes clickable again ("Run Screen", not "Screening…"), the
  progress line and Cancel button both disappear, and the Run History table gains a new row
- **If this does not reach a terminal state within your available test window, this is a known,
  previously-disclosed gap** (the developer's own dev handoff reports the same open-ended
  behavior and did not observe a terminal state within a 25+ minute pass) — do not treat this
  alone as a NEW regression; note the wait time observed and defer to a longer session or a
  scoped/fixture backend for full confirmation

---

### UT-07 — Walk-Forward "Run Walk-Forward" starts a run and shows live progress (happy path, fast slice)

**Type:** happy-path
**Priority:** P2 *(same rationale as UT-05)*
**Surface:** `/desk` — Walk-Forward compute control

**Preconditions:**
- Walk-Forward section expanded (UT-03)
- No other Walk-Forward run currently in flight

**Steps:**
1. Click the "Run Walk-Forward" button (`data-testid="walk-forward-trigger"`)
2. Within 1–2 seconds, observe the button and the area around it

**Expected Result:**
- The button's label changes from "Run Walk-Forward" to "Running…" and becomes disabled
- A line appears reading "0 / N steps" with a small pulsing dot beside it
  (`data-testid="walk-forward-progress"`)
- A "Cancel" button appears (`data-testid="walk-forward-cancel"`)
- No error text appears in `data-testid="walk-forward-trigger-error"`
- You do NOT need to wait further for this test case to pass

---

### UT-08 — Walk-Forward run can be cancelled and reaches a terminal state (happy path, long-running — OPTIONAL)

**Type:** happy-path
**Priority:** P3 (informational — not required for a PASS verdict)
**Surface:** `/desk` — Walk-Forward compute control

**Preconditions:**
- UT-07 has just been run and a Walk-Forward run is currently in the "Running…" state
- Same wall-clock caveat as UT-06 — this exact scenario was NOT completed live during
  development (time budget), so there is no prior confirmation of how long it takes

**Steps:**
1. Click the "Cancel" button (`data-testid="walk-forward-cancel"`)
2. Observe the button immediately after clicking
3. Wait and periodically re-check the section

**Expected Result:**
- Immediately after clicking: the label changes to "Cancelling…" and becomes disabled
- Eventually: the run reaches a terminal state — "Run Walk-Forward" becomes clickable again, the
  progress line and Cancel button disappear, and the Run History table gains a new row
- This exact path (Walk-Forward cancel → idle) has no prior live observation to compare against —
  treat any outcome other than "reaches idle eventually" as worth reporting, but budget generously
  before calling it a failure

---

### UT-09 — A second trigger click while a run is active is refused, not silently ignored (validation-equivalent)

**Type:** validation
**Priority:** P3 (conditional — only executable if a run is already active from UT-05/06 or UT-07/08)
**Surface:** `/desk` — Scout Ledger or Walk-Forward compute control

**Preconditions:**
- A Scout or Walk-Forward run is currently in the "Screening…" / "Running…" state (from UT-05 or
  UT-07). Do not start a new run solely to test this — reuse an already-active one.

**Steps:**
1. With a run already active, reload `http://localhost:3301/desk`
2. Re-expand the relevant section and click its "Run Screen" / "Run Walk-Forward" button again

**Expected Result:**
- The button briefly disables, then a red error line appears reading exactly "Refused — a scout
  screening run is already running. Wait for it to finish, then try again." (Scout) or "Refused —
  a walk-forward run is already running. Wait for it to finish, then try again." (Walk-Forward) —
  in `data-testid="scout-ledger-trigger-error"` / `data-testid="walk-forward-trigger-error"`
- The page does not crash and the existing run's own progress display is unaffected

---

### UT-10 — Backend unreachable shows a typed error, not a blank panel (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` — all 3 new sections

**Preconditions:**
- Backend process is stopped (confirm `curl http://localhost:8301/health` fails/times out before
  proceeding)

**Steps:**
1. Navigate to `http://localhost:3301/desk` (or reload if already there)
2. Click each of "Scout Ledger", "Walk-Forward", and "Validation Vault" to expand them in turn

**Expected Result:**
- Each of the 3 sections shows an amber-bordered panel containing the text "Backend unreachable —
  is the API running?" followed by "Nothing cached and nothing fabricated is shown in its place."
  (`data-testid` ending in `-unavailable`, e.g. `scout-ledger-unavailable`)
- No section shows a blank white area, a stuck loading skeleton, or stale/fabricated data
- Restart the backend afterward before running any other test in this plan

---

### UT-11 — Re-expanding a section does not re-fetch (regression / efficiency check)

**Type:** regression
**Priority:** P3
**Surface:** `/desk` — Scout Ledger section

**Preconditions:**
- On `http://localhost:3301/desk`, backend running normally

**Steps:**
1. Click "Scout Ledger" to expand it; wait for content to settle
2. Click the "Scout Ledger" header again to collapse it
3. Click it a third time to re-expand it

**Expected Result:**
- On the third click, the previously-shown content (families/empty-state, chain verification,
  run history) reappears **instantly**, with no loading skeleton flash — confirms the section's
  data is read once on first expand, not re-fetched on every expand

---

### UT-12 — Microscope Readiness section is unaffected (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — Microscope Readiness section

**Preconditions:**
- On `http://localhost:3301/desk`

**Steps:**
1. Click the "Microscope Readiness" section header to expand it

**Expected Result:**
- Its totals table, `data-testid="micro-readiness-shards-table"`, and floors table all render as
  before, with no visual break introduced by the three new sections below it

---

### UT-13 — Referee Registry / Adjudications / Runs sections are unaffected (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — Referee sections

**Preconditions:**
- On `http://localhost:3301/desk`

**Steps:**
1. Click "Referee Registry" to expand it; verify content, then collapse it
2. Click "Referee Adjudications" to expand it; verify content, then collapse it
3. Click "Referee Runs" to expand it; verify content, then collapse it

**Expected Result:**
- Each of the three sections renders its own existing table/content without an error panel, and
  no heading or `data-testid` collides with any of the 3 new sections

---

### UT-14 — Playbook sections and the main Playbook signal table are unaffected (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — Playbook-related sections

**Preconditions:**
- On `http://localhost:3301/desk`

**Steps:**
1. Scroll to the always-visible Playbook signal table (rows with `data-testid="desk-playbook-
   signal-row"`) near the top of the page and confirm it renders without expansion
2. Click "Screen Runs", "Top-up Runs", "Index Reconciliation", and "Playbook Evidence" in turn to
   expand each

**Expected Result:**
- The main Playbook signal table is present and populated (or honestly empty) exactly as before
- Each of the 4 named collapsible sections still expands to show its own content with no error

---

### UT-15 — `/structure` is unaffected (regression, different route)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to load
3. Locate the comparison dropdown (`data-testid="comparison-dataset-select"`)

**Expected Result:**
- The page loads without error, the Tradable Map renders, and the comparison dropdown is present
  and selectable — unaffected by the `/desk`-only change in this phase

---

### UT-16 — Cockpit (`/`) is unaffected (regression, different route)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3301

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Observe the chart area for 5–10 seconds

**Expected Result:**
- The page loads without error and the chart renders. If the chart appears static in a headless
  capture, cross-check its data against the backend payload before reporting a failure — headless
  Chrome's `visibilityState: "hidden"` is a known trigger for this specific chart to appear frozen
  even though the underlying data is live; this is an environment quirk, not a product regression

---

### UT-17 — New sections are discoverable and correctly ordered (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` navigation/discoverability

**Steps:**
1. Navigate to `http://localhost:3301/desk` fresh (no sections pre-expanded)
2. Scroll down past the Referee sections

**Expected Result:**
- "Microscope Readiness" appears first among the Rapid-Microscope-era sections, immediately
  followed by "Scout Ledger", then "Walk-Forward", then "Validation Vault" — in that exact order,
  each one click away (a single click on its own header, no sub-navigation or hidden menu)
- Each of the 3 new sections' heading text remains visible even while collapsed (only the body is
  hidden)

---

## Known Issues Reflected in This Plan (not independently live-testable today)

These two code-review findings are real, but the app's current live data state makes them
impossible to demonstrate through the browser without either seeding data (disallowed for the
Vault) or waiting for the one real, populated ledger to become empty (not something a tester
should force). They are listed here for visibility, not as executable UT cases:

- **Scout `family_root_id` omission** (`apps/frontend/app/desk/page.tsx:6197`) — the real Scout
  ledger has zero families today, so there is no live family row to inspect. Confirmed by reading
  the source directly: the family header only interpolates `family.family_id` and
  `family.variants_tried`.
- **Walk-Forward empty-state copy bug** (`apps/frontend/app/desk/page.tsx:6431`) — the real
  Walk-Forward ledger is non-empty today, so this branch cannot render on the live app. Confirmed
  by reading the source directly: the `EmptyState` title for zero sequences is still the literal
  string `"No candidates ledgered."` (copied from Scout Ledger's own empty state) rather than
  sequence-appropriate wording.
- **Compute polls do not stop on navigation** (`apps/frontend/app/desk/page.tsx:9934`,`:9997`) —
  if a Scout or Walk-Forward run is active and the operator navigates to another page (e.g. clicks
  "Structure" in the nav) before it finishes, the 700ms polling loop keeps calling the backend in
  the background; there is no user-visible symptom for this from a single browser tab, so it is
  not written as a click-driven UT case. A tester with browser DevTools open can confirm it by:
  starting a run (UT-05/UT-07), opening the Network tab, clicking "Structure" in the nav, and
  observing that `GET /research/desk/micro/scout/compute` (or `.../walkforward/compute`) requests
  continue to fire every ~700ms even though `/desk` is no longer the active page.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads, all headers present, collapsed | smoke | P1 | `/desk` |
| UT-02 | View Scout Ledger contents | happy-path | P1 | `/desk` Scout Ledger |
| UT-03 | View Walk-Forward contents | happy-path | P1 | `/desk` Walk-Forward |
| UT-04 | View Validation Vault contents, confirm read-only | happy-path | P1 | `/desk` Validation Vault |
| UT-05 | Scout "Run Screen" starts + shows progress (fast slice) | happy-path | P2 | `/desk` Scout Ledger |
| UT-06 | Scout Cancel reaches terminal state (long-running) | happy-path | P3 | `/desk` Scout Ledger |
| UT-07 | Walk-Forward "Run Walk-Forward" starts + shows progress (fast slice) | happy-path | P2 | `/desk` Walk-Forward |
| UT-08 | Walk-Forward Cancel reaches terminal state (long-running) | happy-path | P3 | `/desk` Walk-Forward |
| UT-09 | Second trigger click is refused, not ignored | validation | P3 | `/desk` Scout/Walk-Forward |
| UT-10 | Backend unreachable shows typed error | error | P2 | `/desk` all 3 new sections |
| UT-11 | Re-expand does not re-fetch | regression | P3 | `/desk` Scout Ledger |
| UT-12 | Microscope Readiness unaffected | regression | P1 | `/desk` |
| UT-13 | Referee sections unaffected | regression | P1 | `/desk` |
| UT-14 | Playbook sections unaffected | regression | P1 | `/desk` |
| UT-15 | `/structure` unaffected | regression | P1 | `/structure` |
| UT-16 | Cockpit unaffected | regression | P1 | `/` |
| UT-17 | New sections discoverable, correctly ordered | ux | P2 | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.** P2/P3 tests are important but
non-blocking — in particular, UT-06/UT-08's long-running tails and UT-09's conditional scenario
should not be allowed to block a verdict on their own; see Operational Notes.
