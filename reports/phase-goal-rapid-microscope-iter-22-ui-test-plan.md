# Phase goal-rapid-microscope-iter-22 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-22
**Date:** 2026-08-20
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301 (backend: http://localhost:8301 — offset ports per
`scripts/start-backend.sh`/`start-frontend.sh`, matching iter-21/iter-20's own scoped-QA port
convention)

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` loads with Scout Ledger and Walk-Forward sections present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Backend running at `http://localhost:8301` against a scoped QA fixture store (never the real
  `.data/` store).
- Frontend running at `http://localhost:3301`.
- No login required.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load.

**Expected Result:**
- Page renders without a blank screen or error message.
- The section header button "Scout Ledger" (`data-testid="desk-section-expand-scoutLedger"`) is
  visible.
- The section header button "Walk-Forward" (`data-testid="desk-section-expand-walkForward"`) is
  visible, directly below "Scout Ledger".
- No console errors.

---

### UT-02 — Operator can screen Study 1 (range-wall failed aggression) and see it on `/desk` (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` Scout Ledger section + `POST /research/desk/micro/scout/compute`

**Preconditions:**
- A freshly launched scoped QA backend (no prior Scout runs on this instance, so the new family
  is unambiguous).

**Steps:**
1. In a terminal, run:
   `curl -s -X POST http://localhost:8301/research/desk/micro/scout/compute -H "Content-Type: application/json" -d '{"grid":"range_wall_failed_aggression_pilot"}'`
2. Confirm the response is `{"state":"running","run_id":"<id>"}`.
3. Poll `curl -s http://localhost:8301/research/desk/micro/scout/compute` every 5–10 seconds
   until the `"state"` field reads `"done"`.
4. Navigate to `http://localhost:3301/desk` (or refresh if already open).
5. Click the "Scout Ledger" header (`data-testid="desk-section-expand-scoutLedger"`) to expand it.

**Expected Result:**
- A family block with `data-testid="scout-family-failed_aggression_score__band_touch__trades_20"`
  is visible, with the header text `failed_aggression_score__band_touch__trades_20`.
- That family's trial-row table (`data-testid="scout-family-failed_aggression_score__band_touch__trades_20-trial-rows"`)
  contains a row whose Feature cell reads `failed_aggression_score / threshold (band_touch)` and
  whose Decision cell is non-blank (a closed-vocabulary word, e.g. `killed_insufficient_n` or
  `survive`).

---

### UT-03 — Operator can screen Study 3 (capitulation exhaustion) and see it on `/desk` (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` Scout Ledger section + `POST /research/desk/micro/scout/compute`

**Preconditions:**
- UT-02's run has already reached `"state":"done"` on the same backend instance (no run is
  currently in flight).

**Steps:**
1. In a terminal, run:
   `curl -s -X POST http://localhost:8301/research/desk/micro/scout/compute -H "Content-Type: application/json" -d '{"grid":"capitulation_exhaustion_pilot"}'`
2. Confirm the response is `{"state":"running","run_id":"<id>"}`.
3. Poll `curl -s http://localhost:8301/research/desk/micro/scout/compute` until `"state"` reads
   `"done"`.
4. Refresh `http://localhost:3301/desk`.
5. Click "Scout Ledger" to expand it (if not already expanded).

**Expected Result:**
- A family block with `data-testid="scout-family-failed_aggression_score__playbook_signal__trades_20"`
  is visible, header text `failed_aggression_score__playbook_signal__trades_20`.
- That family's trial-row table contains a row whose Feature cell reads
  `failed_aggression_score / threshold (playbook_signal)` and whose Decision cell is non-blank.
- The Study 1 family from UT-02 is still visible in the same Scout Ledger — confirms this run
  added a row rather than replacing prior data.

---

### UT-04 — Both new studies record an honest walk-forward floor-check row (business-rule validation)

**Type:** validation
**Priority:** P1
**Surface:** `/desk` Scout Ledger section

**Preconditions:**
- UT-02 and UT-03 have both completed (`"state":"done"`) against a backend whose exposure
  registry holds zero `historical_oos` sessions (the default state of a fresh scoped fixture
  backend — no code change is required to reach this precondition).

**Steps:**
1. On `http://localhost:3301/desk`, with "Scout Ledger" expanded, locate the
   `failed_aggression_score__band_touch__trades_20` family block.
2. In its trial-row table, find the row immediately below the screen-decision row that shares the
   same Candidate ID value.
3. Repeat steps 1–2 for the `failed_aggression_score__playbook_signal__trades_20` family block.

**Expected Result:**
- In both families, the second row's Feature and Horizon cells each show `—` (a single em-dash).
- In both families, the second row's Decision cell reads exactly `killed_insufficient_n` — the
  honest "not enough independently-verified evidence yet" answer, never a blank cell and never a
  fabricated pass.
- Expanding that row's "screen_result" detail (click the `screen_result` text to open the
  `<details>` element) shows `null` in the JSON body — the floor-check row carries no screen
  payload of its own, by design.

---

### UT-05 — An unrecognized `grid` value still surfaces a raw server error (error, documents a known pre-existing limitation)

**Type:** error
**Priority:** P2
**Surface:** `POST /research/desk/micro/scout/compute`

**Preconditions:**
- No Scout compute run currently in flight on the target backend.

**Steps:**
1. In a terminal, run:
   `curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8301/research/desk/micro/scout/compute -H "Content-Type: application/json" -d '{"grid":"not_a_real_selector"}'`

**Expected Result:**
- HTTP status code is `500` (a raw server error, not a friendly `422` validation message) —
  this is a pre-existing, disclosed, explicitly out-of-scope behavior (iter-21 audit finding B5),
  unchanged by this iteration. This test documents the limitation is unchanged, not a new
  regression this round introduced.
- The `/desk` page itself is unaffected — refreshing `http://localhost:3301/desk` still loads
  normally with no error banner.

---

### UT-06 — The shipped "Run Screen" button still triggers only the unchanged default grid (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` Scout Ledger section — "Run Screen" button

**Preconditions:**
- No Scout compute run currently in flight.

**Steps:**
1. On `http://localhost:3301/desk`, with "Scout Ledger" expanded, open the browser DevTools
   Network tab.
2. Click the "Run Screen" button (`data-testid="scout-ledger-trigger"`).
3. Inspect the outgoing `POST /research/desk/micro/scout/compute` request's body in the Network
   tab.
4. Wait for the button label to change from "Screening…" back to "Run Screen" (run complete),
   then refresh the page and re-expand "Scout Ledger".

**Expected Result:**
- The request body in step 3 carries no `grid` field (or `grid: null`) — confirms the on-screen
  button never selects a pilot-study grid.
- Any new trial row this run produced has a Feature cell with NO `(band_touch)` or
  `(playbook_signal)` suffix.
- No row with Decision `killed_insufficient_n` and Feature `—` appears anywhere in this run's
  output (the default grid never produces a floor-check row).

---

### UT-07 — Study 2's walk-forward floor-check row is still visible, freshly confirmed (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` Scout Ledger section

**Preconditions:**
- The `delta_divergence_pilot` grid has been triggered at least once on the target backend (either
  a prior run already on record, or trigger a fresh one: `curl -s -X POST
  http://localhost:8301/research/desk/micro/scout/compute -H "Content-Type: application/json" -d
  '{"grid":"delta_divergence_pilot"}'`, then poll until `"state":"done"`).

**Steps:**
1. On `http://localhost:3301/desk`, expand "Scout Ledger".
2. Locate the family block with header text
   `divergence_at_level_bearish__band_touch__trades_20`.
3. Find the row immediately below the screen row sharing its Candidate ID.

**Expected Result:**
- That row's Feature and Horizon cells show `—`.
- That row's Decision cell reads exactly `killed_insufficient_n`.
- This is the SAME behavior iter-21 shipped and its own audit fixed — this test confirms no
  iter-22 code change disturbed it, with a dated screenshot as evidence (no reused iter-21 asset).

---

### UT-08 — J-07 Graduation surface is unaffected and freshly re-confirmed (regression)

**Type:** regression
**Priority:** P1
**Surface:** `GET /research/desk/micro/graduation` (raw JSON, browser-navigated directly)

**Preconditions:**
- At least one graduation family exists on the target backend (pre-existing fixture/seed state
  from an earlier iteration's setup — no new action needed this round).

**Steps:**
1. Navigate the browser directly to `http://localhost:8301/research/desk/micro/graduation`.

**Expected Result:**
- HTTP 200, body renders in the browser's built-in JSON viewer.
- The `families` array is non-empty; at least one entry shows a `family` identifier, a sealed
  reading (`verdict`, `rule_hash`), and an observation count (`n`).
- The body is identical in shape to iter-20's own capture (no field added, removed, or renamed) —
  confirms this iteration made no code change to this endpoint, only a fresh dated look.

---

### UT-09 — Neither new study is discoverable as an on-screen control (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` (whole page)

**Steps:**
1. On `http://localhost:3301/desk`, press Ctrl+F (or Cmd+F) and search the whole rendered page
   for the text `range_wall_failed_aggression_pilot`.
2. Repeat the search for `capitulation_exhaustion_pilot`.
3. Look for any dropdown, radio button, or form field near the "Run Screen" button that offers a
   choice of study/grid.

**Expected Result:**
- Both searches return zero matches — confirms there is no on-screen label, tooltip, or hidden
  text naming either new grid-selector value.
- No dropdown, radio group, or additional form field exists near "Run Screen" — the trigger
  surface is visually identical to before this iteration; the two new studies are reachable only
  via the CLI or a direct API call, exactly as the phase spec intends.

---

### UT-10 — The CLI path independently produces the same ledger rows as the route (smoke / cross-path regression)

**Type:** smoke
**Priority:** P2
**Surface:** CLI (`python -m app.research.scout`), verified via the on-disk ledger file (not a
browser surface, but the operator-facing entry point the phase spec names as equally required)

**Preconditions:**
- A fixture-pointed dataset/scout/bar/exposure directory setup (env-var-pointed, never the real
  `.data/` corpus) — mirrors the dev handoff's own CLI-path test setup.

**Steps:**
1. From `apps/backend`, with the fixture env vars set, run:
   `.venv/bin/python -m app.research.scout --grid range_wall_failed_aggression_pilot`
2. Observe stdout.
3. Inspect the on-disk scout ledger JSONL file under the fixture's scout directory.

**Expected Result:**
- Stdout includes the line `1 candidate(s) processed`.
- The ledger file contains two new rows for the run's candidate: one screen-stage row with a
  closed-vocabulary `decision` and `structure_context.kind == "band_touch"`, and one
  `stage == "walkforward_floor_check"` row with `decision == "killed_insufficient_n"` — the same
  two rows UT-02/UT-04 confirm through the browser, now proven reachable via the CLI
  independently of the HTTP route.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads with Scout Ledger + Walk-Forward present | smoke | P1 | `/desk` |
| UT-02 | Study 1 screens and appears on `/desk` | happy-path | P1 | `/desk` + `POST /scout/compute` |
| UT-03 | Study 3 screens and appears on `/desk` | happy-path | P1 | `/desk` + `POST /scout/compute` |
| UT-04 | Both new studies record an honest floor-check row | validation | P1 | `/desk` Scout Ledger |
| UT-05 | Unrecognized `grid` value still 500s | error | P2 | `POST /scout/compute` |
| UT-06 | "Run Screen" button still only runs the default grid | regression | P1 | `/desk` Scout Ledger |
| UT-07 | Study 2's floor-check row still renders, freshly confirmed | regression | P1 | `/desk` Scout Ledger |
| UT-08 | J-07 Graduation surface unaffected, freshly confirmed | regression | P1 | `GET /graduation` |
| UT-09 | Neither new study has an on-screen control | ux | P2 | `/desk` |
| UT-10 | CLI path independently produces the same rows | smoke | P2 | CLI |

**P1 tests must all pass for browser QA verdict to be PASS.**

---

## Sequencing Note (binding, carried from the phase spec)

UT-02/UT-03/UT-06/UT-07 each mutate the scoped QA backend's Scout ledger via a `POST
/scout/compute` call. Per the phase spec's own binding "Do not redo" rig rule, this invalidates
`J-08.json` step 3 / `J-10.json` step 12's "No candidates ledgered." assertion for any LATER lane
sharing the same backend instance. Run the deterministic golden-replay lane (J-01…J-05, J-08,
J-10) FIRST, against a clean backend, before running any of this test plan's mutating steps
(UT-02, UT-03, UT-06, UT-07) on that same instance — or use a freshly launched backend instance
for this test plan, as UT-02's own precondition already specifies.
