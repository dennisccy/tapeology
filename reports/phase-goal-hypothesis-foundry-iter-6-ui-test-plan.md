# Phase goal-hypothesis-foundry-iter-6 — UI Test Plan

**Phase:** goal-hypothesis-foundry-iter-6
**Date:** 2026-08-27
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL (scoped QA rig):** http://localhost:8301

**Environment note:** the scoped QA rig on `:8301` is already provisioned with the real recorded
exhaust ledger (confirmed live: `GET http://localhost:8301/research/desk/micro/foundry` returns
`exhaust_progress.first_read_lock_recorded: true`). A known capture artifact of this environment:
a screenshot taken of the "Runner / Checkpoint" subsection while the page is scrolled down can come
back blank. Enlarge the browser viewport height (or zoom out) before capturing so the subsection
sits fully inside the unscrolled page — this reliably produces a real image.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` loads and the Hypothesis Foundry panel is present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend (scoped QA rig) is running at http://localhost:8301
- No login required (this app has no auth gate on `/desk`)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error page
- A section with the visible heading "Hypothesis Foundry" is present on the page (collapsed by
  default)
- No console errors in the browser DevTools console
- No element with `data-testid="foundry-panel-unavailable"` is present

---

### UT-02 — Operator can expand Runner / Checkpoint and see the real exhaust state (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Hypothesis Foundry → Runner / Checkpoint

**Preconditions:**
- Same as UT-01
- The real exhaust CLI has already been run (confirmed live on the `:8301` rig — do not re-run it)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the section header button with `data-testid="desk-section-expand-hypothesisFoundry"`
   (visible text "Hypothesis Foundry")
3. Click the subsection header button with
   `data-testid="desk-section-expand-foundry-epoch-manifest-section"` (visible text "Epoch /
   Manifest") to confirm the sibling subsection above the new one still opens normally
4. Click the subsection header button with
   `data-testid="desk-section-expand-foundry-runner-checkpoint-section"` (visible text "Runner /
   Checkpoint")

**Expected Result:**
- After step 2: text "Era-Open Baseline" becomes visible
- After step 3: text `epoch:afd19e9c11a6534f` becomes visible inside the Epoch / Manifest body
- After step 4: an element with `data-testid="foundry-runner-checkpoint"` becomes visible,
  containing:
  - `data-testid="foundry-runner-checkpoint-real-banner"` with text "Real Epoch — not a fixture"
  - `data-testid="foundry-runner-first-read-lock"` with text "First-read lock recorded at:
    2026-08-27T06:55:51.071173Z"
  - `data-testid="foundry-runner-eligible-corpus-hash"` with text "Eligible-corpus manifest hash:
    da7488f8609c801f7a6f7c27c736e8a2a713e98f53b2d7006956c355df5c3260"
  - `data-testid="foundry-runner-checkpoint-ordinal"` with text "Checkpoint: 0 of 0"
  - `data-testid="foundry-runner-protected-read-count"` with text "Protected/withheld/sealed reads:
    0"
  - `data-testid="foundry-runner-single-flight-status"` with text "Runner lock: Idle — lock free"
  - `data-testid="foundry-runner-freeze-integrity-verdict"` with text "Freeze integrity: green"
  - `data-testid="foundry-runner-exhaust-complete"` with text containing "Exhaust complete" and
    "zero FROZEN_READY variants this epoch — an honest, vacuous completion"
- The element `data-testid="foundry-runner-checkpoint-empty"` is NOT present (the pre-lock empty
  state must not render once the lock is recorded)
- The element `data-testid="foundry-runner-exhaust-incomplete"` is NOT present

---

### UT-03 — Runner / Checkpoint renders every field with a real value, no placeholder leakage (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/desk` → Hypothesis Foundry → Runner / Checkpoint

**Preconditions:**
- Same as UT-02; the subsection is already expanded

**Steps:**
1. With the "Runner / Checkpoint" subsection expanded (from UT-02), open the browser DevTools
   Network tab and reload `http://localhost:3301/desk`
2. Find the request to `http://localhost:8301/research/desk/micro/foundry` (or the frontend's
   proxied equivalent) in the Network tab and inspect its JSON response body's `exhaust_progress`
   key
3. Re-expand "Hypothesis Foundry" → "Runner / Checkpoint" and read the on-screen text for each of
   the 9 data lines listed in UT-02's Expected Result

**Expected Result:**
- Every value shown on screen is the literal value from the response JSON's `exhaust_progress` key
  — no value reads `undefined`, `NaN`, `[object Object]`, or an empty string where the JSON has a
  real value
- The `protected_read_count` line ("0") renders in green/emerald text color, not red/rose (checked
  via the element's computed class containing `text-emerald-400`, not `text-rose-400`)
- The `freeze_integrity_verdict` line ("green") renders in green/emerald text color
- No value on screen was computed or reformatted beyond straight string interpolation (e.g., the
  eligible-corpus hash is shown as the full raw hex string, not truncated, reformatted, or
  recalculated)

---

### UT-04 — Backend unavailability shows an honest error, not a blank/crashed panel (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` → Hypothesis Foundry panel

**Preconditions:**
- Frontend running at http://localhost:3301
- Do NOT stop the shared `:8301` backend (other tests in this plan depend on it) — instead simulate
  the failure at the network layer in one browser tab

**Steps:**
1. Navigate to `http://localhost:3301/desk` and confirm the page loads normally first
2. Open browser DevTools → Network tab → enable request blocking, and add a blocking rule for the
   URL pattern `*/research/desk/micro/foundry*`
3. Reload the page (F5)
4. Once you have observed the result, remove the blocking rule from step 2 (cleanup, so the shared
   rig continues to serve other tests normally)

**Expected Result:**
- After step 3: the Hypothesis Foundry panel shows an element with
  `data-testid="foundry-panel-unavailable"` containing an honest error message (either the served
  error text or the fallback "The Hypothesis Foundry panel could not be loaded.")
- The panel does NOT crash the whole page (the rest of `/desk`, e.g. other Desk sections above
  Hypothesis Foundry, remain visible and functional)
- No fabricated `exhaust_progress` values (e.g., no "0 of 0" checkpoint or fake timestamp) appear
  anywhere on the page while the request is blocked

---

### UT-05 — Sibling Foundry subsections render unchanged (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` → Hypothesis Foundry → Sources / Compiler, Interpreter Fixtures, Freeze /
Integrity, Hermetic Oracles

**Preconditions:**
- Same as UT-01; "Hypothesis Foundry" section already expanded

**Steps:**
1. Navigate to `http://localhost:3301/desk` and click
   `data-testid="desk-section-expand-hypothesisFoundry"`
2. Click `data-testid="desk-section-expand-foundry-sources-compiler-section"` (visible text
   "Sources / Compiler")
3. Click `data-testid="desk-section-expand-foundry-interpreter-fixtures-section"` (visible text
   "Interpreter Fixtures")
4. Click `data-testid="desk-section-expand-foundry-freeze-integrity-section"` (visible text "Freeze
   / Integrity")
5. Click `data-testid="desk-section-expand-foundry-hermetic-oracles-section"` (visible text
   "Hermetic Oracles")

**Expected Result:**
- After step 2: text "Hashes match — outcome-blind compilation proven." is visible
- After step 3: text "BLOCKED_UNSUPPORTED_RELATION" is visible
- After step 4: text "docs/hypothesis-foundry/freeze-set.json" is visible
- After step 5: text "Protected-data trip fails closed / evidence class immutable" is visible
- None of these four subsections show any new field related to `exhaust_progress` — they remain
  exactly as before this iteration

---

### UT-06 — J-01 through J-06 golden journeys replay clean (regression, full set)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Hypothesis Foundry (all subsections)

**Preconditions:**
- Frontend running at http://localhost:3301, backend (scoped rig) at http://localhost:8301
- This is the Definition-of-Done "Required-still-passing journeys J-01..J-06" gate — treat a
  failure here as blocking, not advisory

**Steps:**
1. Navigate to `http://localhost:3301/desk` — confirm text "Hypothesis Foundry" is visible (J-01
   step 1)
2. Click the text "Hypothesis Foundry" — confirm text `08e471b10130e1e2` becomes visible (J-01 step
   2, the product fingerprint)
3. Click `data-testid="desk-section-expand-hypothesisFoundry"` if not already open, confirm text
   "Era-Open Baseline" is visible, then click
   `data-testid="desk-section-expand-foundry-sources-compiler-section"` — confirm text "Hashes
   match — outcome-blind compilation proven." (J-02)
4. Click `data-testid="desk-section-expand-foundry-interpreter-fixtures-section"` — confirm text
   "BLOCKED_UNSUPPORTED_RELATION" (J-03)
5. Click `data-testid="desk-section-expand-foundry-freeze-integrity-section"` — confirm text
   "docs/hypothesis-foundry/freeze-set.json" (J-04)
6. Click `data-testid="desk-section-expand-foundry-hermetic-oracles-section"` — confirm text
   "Protected-data trip fails closed / evidence class immutable" (J-05)
7. Click `data-testid="desk-section-expand-foundry-epoch-manifest-section"` — confirm text
   `epoch:afd19e9c11a6534f` (J-06)

**Expected Result:**
- Every one of the six confirmations in steps 1–7 succeeds with the exact text shown — none of the
  six prior journeys regressed after this iteration's additive change
- (If run via the automated golden-replay lane instead of manually: `runs/goal-session-
  hypothesis-foundry/journey-scripts/J-01.json` through `J-06.json` all pass unmodified — grep-
  confirmed that none reference `exhaust`, `foundry-runner`, or "Runner / Checkpoint", so this
  iteration's change cannot have altered their assertions.)

---

### UT-07 — Runner / Checkpoint is discoverable in 2 clicks with an unambiguous label (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/desk` navigation → Hypothesis Foundry panel

**Steps:**
1. Navigate to `http://localhost:3301/desk` (as a first-time operator would, with no prior
   knowledge of where the new capability lives)
2. Look for a section labeled "Hypothesis Foundry" and click it (click 1)
3. Within the expanded panel, look for a subsection labeled "Runner / Checkpoint" and click it
   (click 2)

**Expected Result:**
- The "Runner / Checkpoint" subsection is reached in exactly 2 clicks from landing on `/desk` — no
  scrolling to a hidden nav menu or separate page is required
- The label "Runner / Checkpoint" is self-explanatory in context (it sits directly below "Epoch /
  Manifest" and reads naturally as "the run of that frozen epoch, and its checkpoint progress")
- No duplicate or conflicting label exists elsewhere on the page for the same data (grep-confirmed:
  `exhaust_progress` is rendered nowhere else on `/desk`)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads, Hypothesis Foundry panel present | smoke | P1 | `/desk` |
| UT-02 | Runner / Checkpoint shows the real exhaust state | happy-path | P1 | `/desk` → Hypothesis Foundry → Runner / Checkpoint |
| UT-03 | Every field is a real value, no placeholder leakage | validation | P2 | `/desk` → Runner / Checkpoint |
| UT-04 | Backend outage shows honest error, not a crash | error | P2 | `/desk` → Hypothesis Foundry panel |
| UT-05 | Sibling subsections unchanged | regression | P2 | `/desk` → Sources/Compiler, Interpreter Fixtures, Freeze/Integrity, Hermetic Oracles |
| UT-06 | J-01..J-06 golden journeys replay clean | regression | P1 | `/desk` → Hypothesis Foundry (all subsections) |
| UT-07 | Runner / Checkpoint discoverable in 2 clicks | ux | P3 | `/desk` navigation |

**P1 tests must all pass for browser QA verdict to be PASS.**
