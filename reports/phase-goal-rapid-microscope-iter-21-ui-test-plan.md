# Phase goal-rapid-microscope-iter-21 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-21
**Date:** 2026-08-20
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301 (the scoped QA fixture backend launched via
`bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh <root_dir> 8301`, paired
with `CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh` — never the
real `.data/` store)

**Sequencing note (important):** UT-01/UT-02/UT-05/UT-07/UT-08/UT-09 assert the section still shows
"No candidates ledgered." or otherwise reflect a fresh, un-triggered ledger — the SAME text J-10's
own golden replay asserts. Run those tests (and any full J-01..J-10 replay pass) against a **fresh,
just-launched** `$ROOT` BEFORE running UT-03/UT-04/UT-06 (which trigger the pilot Scout grid and
permanently populate that `$ROOT`'s ledger for the rest of that backend process's life). Either use
two separate `$ROOT` directories, or run the ledger-populating tests strictly last in a single
session.

---

## Test Cases

---

### UT-01 — `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- The scoped QA fixture backend is running at `http://localhost:8301`
- The frontend is running at `http://localhost:3301`

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error boundary
- The text "Playbook Signals" is visible somewhere on the page
- No console errors in the browser DevTools console

---

### UT-02 — Microscope Readiness shows the materialized band-touch count (happy-path, new info)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Microscope Readiness section

**Preconditions:**
- Fresh scoped QA fixture backend (no pilot grid triggered yet this session)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Microscope Readiness" section header (`data-testid="desk-section-expand-microReadiness"`)
3. Locate the row labeled "Joinable corpus — band touches" in the Sealed Tranche table

**Expected Result:**
- The row's value cell (`data-testid="micro-readiness-band-touch-count"`) contains EITHER a plain
  integer (e.g. `0`) OR the literal text `not enumerated` — never a blank cell, never the raw JSON
  `{"status": "not_enumerated", "count": null}`
- The row labeled "Joinable corpus — withheld (excluded)" immediately above it still shows its
  own pre-existing integer value, unaffected

---

### UT-03 — Operator can trigger the pilot Scout grid and see the band-touch candidate row render (happy-path, core J-09 capability)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Scout Ledger section (triggered via direct API call, not a UI button)

**Preconditions:**
- Scoped QA fixture backend running at `http://localhost:8301`, no Scout compute already running
  (`curl http://localhost:8301/research/desk/micro/scout/compute` shows `"state": "idle"` or
  `"completed"`, not `"running"`)

**Steps:**
1. From a terminal, run:
   `curl -s -X POST http://localhost:8301/research/desk/micro/scout/compute -H "Content-Type: application/json" -d '{"grid":"delta_divergence_pilot"}'`
2. Confirm the response is `{"state":"running","run_id":"<some-id>"}` (HTTP 200)
3. Poll `curl -s http://localhost:8301/research/desk/micro/scout/compute` every 2 seconds until
   the `"state"` field reads `"completed"` (should take well under a minute on the fixture-scoped
   backend's small dataset)
4. Navigate to `http://localhost:3301/desk`
5. Click the "Scout Ledger" section header (`data-testid="desk-section-expand-scoutLedger"`)

**Expected Result:**
- The "Ledger chain verification" line reads `ok`
- The section does NOT show the "No candidates ledgered." empty state
- At least one family block (`data-testid="scout-family-{family_id}"`) is visible
- Inside that family's trial rows (`data-testid="scout-family-{family_id}-trial-rows"`), one row's
  Feature cell reads exactly `divergence_at_level_bearish / threshold (band_touch)` — the
  `(band_touch)` suffix must be present and visible on screen

---

### UT-04 — Walk-forward floor-check decision appears as a second ledger row under the same candidate (happy-path, secondary)

**Type:** happy-path
**Priority:** P2
**Surface:** `/desk` → Scout Ledger section

**Preconditions:**
- UT-03 has already been run in this session (the delta-divergence candidate is screened and its
  `candidate_id` is known/visible)

**Steps:**
1. With Scout Ledger still expanded from UT-03, locate the trial row immediately following the
   `divergence_at_level_bearish / threshold (band_touch)` row inside the same family's trial table
2. Confirm this second row shares the same `candidate_id` value as the row above it (visible in
   the row's own detail, or via `curl http://localhost:8301/research/desk/micro/scout | python3 -m json.tool`
   and matching `candidate_id` across two entries)
3. Click to expand that second row's `<details>` / collapsed JSON block

**Expected Result:**
- The second row's Feature and Horizon columns both display `—` (em-dash), not blank and not a
  fabricated feature name
- The Decision column for that row shows `insufficient_n`
- The expanded `screen_result` JSON detail shows `null`

---

### UT-05 — Studies 1 and 3 never appear as ledgered rows, even after the pilot grid runs (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/desk` → Scout Ledger section

**Preconditions:**
- UT-03 has already been run in this session

**Steps:**
1. With Scout Ledger expanded, inspect every family block and every trial row rendered on screen
2. Separately, `curl -s http://localhost:8301/research/desk/micro/scout | python3 -m json.tool`
   and inspect every `family_root_id` / `feature.name` combination in the full JSON response

**Expected Result:**
- No row anywhere (on screen or in the raw JSON) has `feature.name` matching
  `failed_aggression_score` paired with `structure_context.kind = "band_touch"` (Study 1 — range-wall
  failed aggression)
- No row anywhere has `structure_context.setup_id = "capitulation"` (Study 3 — capitulation
  exhaustion)
- Only the `divergence_at_level_bearish` candidate (Study 2) and its walk-forward floor-check
  companion row exist

---

### UT-06 — Scout Ledger shows the real backend-unavailable message when the fetch fails (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` → Scout Ledger section, `data-testid="scout-ledger-unavailable"`

**Preconditions:**
- Frontend running at `http://localhost:3301`

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Open the browser DevTools console and run a `window.fetch` override that makes any request to
   a URL containing `/research/desk/micro/scout` reject (e.g. patch `window.fetch` to throw for
   matching URLs, mirroring UT-10's existing technique)
3. Click the "Scout Ledger" section header (`data-testid="desk-section-expand-scoutLedger"`)
4. Capture a screenshot of ONLY the element with `data-testid="scout-ledger-unavailable"` (element
   capture, not a full-page screenshot)

**Expected Result:**
- The `scout-ledger-unavailable` element is visible and contains real, non-empty message text
  describing the failure (e.g. "The scout ledger could not be loaded." or the fetch error text) —
  never a blank panel, never a loading spinner frozen mid-state

---

### UT-07 — The shipped "Run Scout" button still triggers only the default grid (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Scout Ledger section, "Run Scout" control

**Preconditions:**
- Scoped QA fixture backend running, no compute currently running

**Steps:**
1. Navigate to `http://localhost:3301/desk`, expand "Scout Ledger"
2. Open the browser DevTools Network tab
3. Click the shipped "Run Scout" button (`data-testid` on the compute-trigger button inside
   `ScoutLedgerSection` — the existing `onTrigger`/`handleTriggerScout` control)
4. Inspect the outgoing `POST /research/desk/micro/scout/compute` request body in the Network tab

**Expected Result:**
- The request body is empty (or contains no `grid` field) — the UI button never sends
  `{"grid": "delta_divergence_pilot"}` or any other grid selector
- Any rows this run produces are unconditionally `structure_context.kind = "none"` and render with
  NO parenthetical suffix in the Feature cell, byte-identical to every pre-iteration screenshot

---

### UT-08 — J-10 golden replay: restored Playbook Evidence assertions pass (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Playbook Evidence section

**Preconditions:**
- Fresh scoped QA fixture backend (matches `J-10.json`'s own preconditions — steps 1–8 of that
  script already run: watch `SIM-BUYER`, load `/structure` for `AAPL` as of `2026-06-22 16:00:00`,
  navigate to `/desk`)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Playbook Evidence" section header (`data-testid="desk-section-expand-playbookEvidence"`)
3. Fill the field with `data-testid="desk-playbook-date-input"` with the value `2026-06-22`

**Expected Result:**
- After step 2: the text "Built from signature:" is visible on the page
- After step 3: the text "recorded signals, none hidden" is visible on the page
- Every subsequent shipped section (Microscope Readiness, Scout Ledger, Walk-Forward, Validation
  Vault, Referee Registry, Referee Adjudications, Referee Runs) still expands and still shows its
  own already-established golden text unchanged (`Distinct symbol-days`, `No candidates
  ledgered.` — only true on a FRESH `$ROOT`, `No fold specs registered.`, `iter18-qa-universe`,
  `config fingerprint 08e471b10130e1e2`, `No hypotheses registered.`, `No evaluation runs recorded
  yet.`)

---

### UT-09 — The pilot Scout grid has no discoverable UI control anywhere on `/desk` (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` (whole page)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Visually scan every section for any button, dropdown, or form field mentioning "pilot",
   "grid", "delta divergence", "band touch", or "playbook signal" as a selectable Scout option
3. Use the browser's "Find in page" (Ctrl+F / Cmd+F) to search the fully-rendered page text for
   the string `delta_divergence_pilot`

**Expected Result:**
- No button, dropdown, or form field exists anywhere on `/desk` that lets an operator select or
  trigger the pilot grid
- The "Find in page" search for `delta_divergence_pilot` returns zero matches in the rendered DOM
  text (the string exists only in backend source/API payloads, never as UI copy)
- This is intentional per this iteration's own scope (goal.md OUT OF SCOPE: "a UI trigger button
  for the pilot grid") — a FAIL here would mean scope crept beyond what was planned, not that a
  feature works differently than expected

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads | smoke | P1 | `/desk` |
| UT-02 | Band-touch count row renders | happy-path | P1 | Microscope Readiness |
| UT-03 | Pilot grid triggers band_touch row | happy-path | P1 | Scout Ledger |
| UT-04 | Walk-forward floor-check row renders | happy-path | P2 | Scout Ledger |
| UT-05 | Studies 1/3 never ledgered | validation | P1 | Scout Ledger |
| UT-06 | Backend-unavailable panel (element capture) | error | P2 | Scout Ledger |
| UT-07 | Default "Run Scout" unchanged | regression | P1 | Scout Ledger |
| UT-08 | J-10 restored assertions pass | regression | P1 | Playbook Evidence + full `/desk` |
| UT-09 | Pilot grid has no UI control | ux | P2 | `/desk` (whole page) |

**P1 tests must all pass for browser QA verdict to be PASS.**
