# Phase goal-referee-iter-10 — UI Test Plan

**Phase:** goal-referee-iter-10
**Date:** 2026-08-15
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301

---

## Important notes before running these tests

1. **Fixture dependency (UT-04):** two of the seven verdict states this round ships UI for —
   `fragile` and a refused-attestation `insufficient_sample` — do not exist on any backend
   instance yet. Per the dev handoff's Known Issues, seeding them is QA's own preparatory step
   (exact mechanics documented there), never a real operator registration act. If that seeding has
   not happened yet on the instance under test, UT-04 is **blocked**, not failed — do not mark it
   FAIL without first confirming the fixture data was never seeded.
2. **Real, irreversible writes (UT-07, UT-08, UT-09, UT-10):** clicking "Build Null" or "Evaluate"
   starts a genuine compute job against whichever store the running backend points at, and appends
   a permanent row to a run ledger with no delete path — there is no "undo." These are marked
   **CAUTION / optional** below. Prefer a disposable/fixture-scoped backend. The host-guard CPU
   mask still applies to these computes exactly as it does to the desk's other compute triggers —
   do not disable or widen it to make a run finish faster.
3. **Adjacent hazard:** the pre-existing "Referee Registry" section sits directly above the two
   new sections and its "Confirm Registration" button is also a real, permanent write (shipped in
   iteration 8, unchanged this round). It is easy to click by accident while scrolling through this
   round's new panels — avoid it unless a test explicitly calls for it.
4. UT-01 through UT-06, UT-13, UT-14, and UT-15 are read-only and safe to run anytime against any
   backend instance.

---

## Test Cases

---

### UT-01 — Desk page loads with all three Referee sections present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend is running at http://localhost:8301 (`curl http://localhost:8301/health` returns
  `{"status":"ok"}`)
- No login is required (this project has no auth gate)
- If the frontend was rebuilt or the backend's routes changed since the last dev server start, run
  `rm -rf apps/frontend/.next` and restart the frontend first (this project's known stale-build
  gotcha)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load
3. Scroll to the very bottom of the page

**Expected Result:**
- Page renders without a blank screen or error message
- The heading "Desk" (`data-testid="desk-title"`) is visible near the top
- The top nav bar shows exactly three links: "Cockpit", "Structure", "Desk"
- Three collapsible section headers appear in this exact order at the bottom of the page:
  "Referee Registry", "Referee Adjudications", "Referee Runs" — with "Referee Runs" last
- All three are collapsed by default (arrow glyph "▸", not "▾")
- No console errors

---

### UT-02 — Referee Adjudications shows the honest empty state on a zero-hypothesis backend (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk` → Referee Adjudications section

**Preconditions:**
- A backend instance with zero registered hypotheses (`GET /research/desk/referee/registry`
  returns `"hypotheses": []`) — NOT the shared dev-verified instance, which already has `S-1`
  registered from iteration 8. Use a fresh fixture-scoped instance for this test.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Referee Adjudications" section header
   (`data-testid="desk-section-expand-refereeAdjudications"`)

**Expected Result:**
- The section expands; its arrow glyph flips from "▸" to "▾"
- A disclosure paragraph renders (`data-testid="referee-adjudications-register"`) beginning
  "Referee verdicts are statistical statements about recorded history under stated assumptions"
- Below it, the text "No hypotheses registered." renders (`data-testid="referee-adjudications-empty"`)
- No table, no verdict chip, and no "∅" empty-state icon's sibling table appear

---

### UT-03 — Referee Adjudications shows a verdict chip and full provenance for each registered hypothesis (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Referee Adjudications section

**Preconditions:**
- At least one hypothesis is registered on the backend under test (as of this writing, `S-1` is
  registered on the iteration-8/9 dev-verified instance)
- Referee Adjudications section expanded (UT-02's step 2, on a populated instance instead)

**Steps:**
1. With "Referee Adjudications" expanded, locate row `referee-adjudication-row-S-1`
   (`data-testid="referee-adjudications-table"` should contain it)
2. Read its "Verdict" cell (`data-testid="referee-adjudication-verdict-S-1"`)
3. Read its "Status" cell
4. Read its "Provenance" cell (`data-testid="referee-adjudication-provenance-S-1"`)

**Expected Result:**
- The row renders with the Hypothesis column showing `S-1`
- The Verdict cell's text is exactly one of: `registered`, `pending_forward_confirmation`,
  `insufficient_sample`, `fragile`, `no_evidence`, `corroborated`, `basis_retired` — rendered as a
  plain, uncolored pill (no red/green/amber styling implying a judgment)
- The Status cell shows either a `checkpointed <date>` string (if a checkpoint exists) or a
  `<number> / <number> sessions` pair (if it does not) — never blank, "NaN", or "undefined"
- The Provenance cell shows exactly five lines, each with a value or an em dash ("—"): `basis:`,
  `null spec:`, `test spec:`, `seed identity:`, `attestation:`, and a sixth `BH:` line — the `seed
  identity:` line always shows the value `S-1` (never an em dash), even if the other lines show
  em dashes because no checkpoint exists yet

---

### UT-04 — Populated panel shows a `fragile` verdict and a refused-attestation entry side by side (happy-path)

**Type:** happy-path
**Priority:** P1 (see "Important notes" item 1 — blocked, not failed, if fixtures are unseeded)
**Surface:** `/desk` → Referee Adjudications section

**Preconditions:**
- The QA fixture-seeding step described in the dev handoff's Known Issues has been completed on
  the backend under test: one hypothesis has an adjudication snapshot with a non-empty
  `fragility_triggers` list, and a second (or the same) has a stored attestation that fails
  re-verification at fold time

**Steps:**
1. With "Referee Adjudications" expanded, locate the row for the seeded `fragile` hypothesis
2. Read its Verdict and "Fragility triggers" cells
3. Locate the row for the seeded refused-attestation hypothesis
4. Read its Verdict and Status cells

**Expected Result:**
- The `fragile` hypothesis's Verdict cell reads exactly `fragile`, and its Fragility triggers cell
  shows a non-empty, comma-joined list (not "—")
- The refused-attestation hypothesis's Verdict cell reads exactly `insufficient_sample`
- That row's Status cell (`data-testid="referee-adjudication-refusal-<hypothesis_id>"`) reads
  exactly: "the checkpoint evaluation's oracle attestation is missing, mismatched, or
  version-stale -- confirmatory output is refused"
- Both rows are visible in the same screenshot/scroll position as `S-1`'s own row from UT-03

---

### UT-05 — Referee Runs section expands and shows both Null Builds and Evaluations sub-blocks (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk` → Referee Runs section

**Preconditions:**
- UT-01 passed

**Steps:**
1. Click the "Referee Runs" section header (`data-testid="desk-section-expand-refereeRuns"`,
   directly below "Referee Adjudications")

**Expected Result:**
- The section expands; its arrow flips from "▸" to "▾"
- A "Null Builds" sub-heading renders, followed by either the text "No hypotheses registered —
  nothing to build a null for yet." or one control per distinct null spec in use (e.g. a control
  labeled `referee-null-build-control-referee-null-tod-v1` and/or
  `referee-null-build-control-referee-null-context-v1`), each showing a "Build Null" button
- Below that, either "No null-build runs recorded yet." or a table (`data-testid="referee-null-runs-table"`)
- An "Evaluations" sub-heading renders, followed by either "No hypotheses registered — nothing to
  evaluate yet." or one control per registered hypothesis (e.g.
  `referee-evaluate-control-S-1`), each showing an "Evaluate" button
- Below that, either "No evaluation runs recorded yet." or a table
  (`data-testid="referee-evaluate-runs-table"`)

---

### UT-06 — Trigger button visually disables and relabels the instant it is clicked (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/desk` → Referee Runs → Null Builds or Evaluations control

**Preconditions:**
- Referee Runs section expanded, with at least one "Build Null" or "Evaluate" button visible and
  enabled

**Steps:**
1. Click a "Build Null" or "Evaluate" button once
2. Immediately (before the request resolves) look at the same button

**Expected Result:**
- The button becomes disabled the instant it is clicked (cannot be double-clicked into starting
  two requests)
- Once the request resolves, the label changes to "Building…"/"Evaluating…" if a run actually
  started, or the button re-enables with an inline error/refusal message if it did not (see UT-09
  for the specific single-flight-refusal case)

---

### UT-07 — Operator triggers a null-build compute and watches it run to completion (happy-path — real write)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Referee Runs → Null Builds

**CAUTION:** This test starts a genuine, heavy compute job and appends a permanent row to the null
run ledger with no delete path. See "Important notes" items 2–3 above. Optional — run only
intentionally, ideally against a disposable/fixture-scoped backend.

**Preconditions:**
- Referee Runs section expanded
- At least one null-build control visible with its button reading "Build Null" (not already
  running)

**Steps:**
1. Note the control's null spec label (e.g. `referee-null-tod-v1`)
2. Click its "Build Null" button (`data-testid="referee-null-build-trigger-<null_spec_id>"`)
3. Watch the same control without reloading the page until the run finishes

**Expected Result:**
- The button immediately reads "Building…" and disables
- A live progress line appears (`data-testid="referee-null-build-progress-<null_spec_id>"`)
  showing a pulsing dot and a `<done> / <total>` count that increases over time, with no page
  reload
- A "Cancel" button appears beside it while running
- Once finished, the button returns to "Build Null" (re-enabled), the progress line and Cancel
  button disappear, and a new row appears in the null run ledger table below showing that run's
  `run_id`, the same null spec id, `state: "completed"`, and populated `started_at`/`finished_at`
  timestamps

---

### UT-08 — Operator triggers an evaluation compute and watches it run to completion (happy-path — real write)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Referee Runs → Evaluations

**CAUTION:** Same real-write caveat as UT-07, scoped to the evaluation run ledger and the named
hypothesis's evaluation history. Optional — run only intentionally.

**Preconditions:**
- Referee Runs section expanded
- At least one evaluation control visible with its button reading "Evaluate" (not already running)

**Steps:**
1. Note the control's hypothesis id (e.g. `S-1`)
2. Click its "Evaluate" button (`data-testid="referee-evaluate-trigger-<hypothesis_id>"`)
3. Watch the same control without reloading the page until the run finishes

**Expected Result:**
- The button immediately reads "Evaluating…" and disables
- A live progress line appears (`data-testid="referee-evaluate-progress-<hypothesis_id>"`) with a
  `<done> / <total>` count that increases over time, with no page reload
- A "Cancel" button appears beside it while running
- Once finished, the button returns to "Evaluate" (re-enabled), and a new row appears in the
  evaluation run ledger showing that run's `run_id`, the hypothesis id, a terminal `state`, and
  populated `started_at`/`finished_at` timestamps

---

### UT-09 — A second trigger for the same in-flight key is refused, not queued or duplicated (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` → Referee Runs (either sub-block)

**CAUTION:** Requires a run already in flight — depends on UT-07 or UT-08's own real-write caveat.

**Preconditions:**
- A null-build or evaluation run is currently in the `running` state for a specific key (started
  via UT-07 or UT-08, not yet finished)

**Steps:**
1. While that run is still showing "Building…"/"Evaluating…", click the SAME control's trigger
   button again (it should still be visually disabled — if the button is disabled, this test
   instead confirms the disabled state prevents the click; if a race allows a second submission,
   continue to step 2)
2. Read the control's error line

**Expected Result:**
- No second run record is ever created for the same key — the run ledger shows only one row per
  actual run start
- If a duplicate request does reach the backend (e.g. via a second browser tab targeting the same
  key), the control's `data-testid="referee-null-build-trigger-error-<id>"` or
  `"referee-evaluate-trigger-error-<id>"` shows exactly: "Refused — a null build is already
  running for this spec. Wait for it to finish, then try again." (null builds) or "Refused — an
  evaluation is already running for this hypothesis. Wait for it to finish, then try again."
  (evaluations)
- The page does not crash or lose the rest of the Referee Runs section

---

### UT-10 — Operator cancels an in-flight run (happy-path — real write, secondary flow)

**Type:** happy-path
**Priority:** P2
**Surface:** `/desk` → Referee Runs (either sub-block)

**CAUTION:** Requires a run already in flight (UT-07/UT-08's caveat applies). Optional.

**Preconditions:**
- A null-build or evaluation run is currently `running` for a specific key

**Steps:**
1. Click that control's "Cancel" button (`data-testid="referee-null-build-cancel-<id>"` or
   `"referee-evaluate-cancel-<id>"`)

**Expected Result:**
- The Cancel button's label changes to "Cancelling…" and disables
- The run eventually leaves the `running`/`cancelling` state (progress line and Cancel button
  disappear); the corresponding ledger row's `state` reflects a terminal, non-`"completed"` value
  once the section's run history refreshes
- No error is shown unless the backend genuinely rejects the cancel (e.g. the run already
  finished), in which case a red inline message (`referee-null-build-cancel-error-<id>"` /
  `"referee-evaluate-cancel-error-<id>"`) renders with the backend's own explanation text

---

### UT-11 — Run ledger renders a finished run's fields verbatim (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Referee Runs (either run ledger table)

**Preconditions:**
- At least one null-build or evaluation run has reached a terminal state (from UT-07/UT-08, or
  already present in ledger history on the instance under test)

**Steps:**
1. In the relevant ledger table, locate any row
2. Read its `run`, spec/hypothesis id, `state`, `progress`, `started`, `finished`, and `error`
   columns

**Expected Result:**
- Every column shows a value read directly from the backend response — `progress` shows
  `<done> / <total>`, `started`/`finished` show ET-formatted timestamps, and `error` shows either
  an em dash ("—") or the backend's own error text, never a client-computed or blank value
- Clicking a sortable column header (e.g. "started") re-orders the table rows; the "progress" and
  "error" columns are not sortable (no visible sort indicator on their headers)

---

### UT-12 — MCP connector advertises 22 tools; the two new tools are byte-identical to their REST equivalents (technical verification, non-browser)

**Type:** regression
**Priority:** P2
**Surface:** MCP connector (not a browser surface — verify via an MCP-capable client or the
project's own MCP test harness, not Chrome)

**Preconditions:**
- The backend under test is reachable and its MCP module is loadable against it

**Steps:**
1. Request the full MCP tool list against the backend under test
2. Invoke the `desk_referee` tool with no arguments; separately, `curl
   http://localhost:8301/research/desk/referee/adjudications`
3. Invoke the `desk_referee_registry` tool with no arguments; separately, `curl
   http://localhost:8301/research/desk/referee/registry`

**Expected Result:**
- The tool list contains exactly 22 entries, including `desk_referee` and `desk_referee_registry`
- Step 2's tool output and curl output are byte-identical JSON (same for step 3), in both an empty
  and a populated backend state
- Repeat with an integrity-broken hypothesis file present in the store: both tools still return
  the endpoint's own honest `integrity_errors` disclosure rather than raising an unhandled
  exception

---

### UT-13 — Every previously-shipped `/desk` section is unaffected (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` (all pre-existing sections)

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Expand the "Referee Registry" section header (directly above "Referee Adjudications")
3. Expand every other pre-existing section on the page (Screen history, Forward Returns, Refresh
   chain/Briefing, Skipped, Runs/Pins/Compare/Provenance, Playbook Evidence, and every Playbook
   section with its context columns/filters/cohort views)

**Expected Result:**
- "Referee Registry" still shows its 5-row shortlist table and "Registered Hypotheses" table (or
  empty state) exactly as before this round — no visual shift or missing data caused by the two
  new sections rendered below it
- Every other section listed above still renders its own content, headings, columns, and
  data-testids exactly as shipped in prior rounds

---

### UT-14 — Cockpit and Structure pages still work (regression — J-10 kept-product walk)

**Type:** regression
**Priority:** P1
**Surface:** `/` (cockpit), `/structure`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/` (cockpit)
2. Verify the chart and live/tape elements render
3. Navigate to `http://localhost:3301/structure`
4. Set the date to a pinned AAPL date used in prior iterations' verification (e.g. 2026-06-22) and
   click "Load"

**Expected Result:**
- Cockpit renders its chart and does not error
- Structure's "Load" completes and renders levels/zones for the requested date exactly as in prior
  rounds — no regression introduced by this round's backend or frontend changes

---

### UT-15 — Referee Adjudications and Referee Runs are discoverable without prior knowledge (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/desk` navigation / layout

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk` as if for the first time
2. Scroll down the page looking for anything related to hypothesis verdicts or running new
   computations

**Expected Result:**
- Sections clearly labeled "Referee Adjudications" and "Referee Runs" are reachable with a single
  scroll and a single click each (to expand) — no separate navigation item, no hidden menu, no
  undocumented URL needed
- "Referee Adjudications" sits immediately below "Referee Registry" in a place a reader already
  looking at hypothesis registration would naturally scroll to next

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Desk page loads with all three Referee sections present | smoke | P1 | `/desk` |
| UT-02 | Adjudications honest empty state (zero hypotheses) | smoke | P1 | `/desk` → Adjudications |
| UT-03 | Adjudications verdict chip + provenance per hypothesis | happy-path | P1 | `/desk` → Adjudications |
| UT-04 | Populated panel shows `fragile` + refused-attestation entries | happy-path | P1 (blocked if unseeded) | `/desk` → Adjudications |
| UT-05 | Referee Runs shows Null Builds + Evaluations sub-blocks | smoke | P1 | `/desk` → Runs |
| UT-06 | Trigger button disables instantly on click | validation | P2 | `/desk` → Runs |
| UT-07 | Trigger + watch a null-build to completion (real write) | happy-path | P1 | `/desk` → Runs → Null Builds |
| UT-08 | Trigger + watch an evaluation to completion (real write) | happy-path | P1 | `/desk` → Runs → Evaluations |
| UT-09 | Second in-flight trigger refused single-flight | error | P2 | `/desk` → Runs |
| UT-10 | Cancel an in-flight run (real write) | happy-path | P2 | `/desk` → Runs |
| UT-11 | Run ledger renders finished-run fields verbatim | happy-path | P1 | `/desk` → Runs ledgers |
| UT-12 | MCP: 22 tools, 2 new ones byte-identical to REST | regression | P2 | MCP connector (non-browser) |
| UT-13 | Every pre-existing `/desk` section unaffected | regression | P1 | `/desk` |
| UT-14 | Cockpit + Structure pinned-AAPL Load still work | regression | P1 | `/`, `/structure` |
| UT-15 | New sections discoverable without prior knowledge | ux | P3 | `/desk` navigation |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-04 is P1 but conditionally
blocked (not failed) if its fixture data was never seeded — see "Important notes" item 1.
