# Phase goal-hypothesis-foundry-iter-8 — UI Test Plan

**Phase:** goal-hypothesis-foundry-iter-8
**Date:** 2026-08-27
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301

---

## Environment note (read before running)

Deep-scroll Chrome-MCP screenshots of the Hypothesis Foundry subsections are a known blank-PNG
artifact in this environment. For any step below that calls for a screenshot as evidence, capture
it via `demo_runner --mode verify` rather than a Chrome-MCP deep-scroll screenshot. DOM
queries/evals (`document.querySelector`, `.textContent`, etc.) against the live Chrome session at
CDP `http://127.0.0.1:9222` are reliable and should be used for value-matching assertions (TC-5)
regardless of which screenshot path is used.

---

## Test Cases

---

### UT-01 — `/desk` Hypothesis Foundry panel and Final Summary subsection load without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend running at http://localhost:3301
- Backend running at http://localhost:8301
- No login required

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load
3. Click the "Hypothesis Foundry" section header (`data-testid="desk-section-expand-hypothesisFoundry"`)
4. Wait for the panel body to render
5. Click the "Final Summary" section header (`data-testid="desk-section-expand-foundry-final-summary-section"`)

**Expected Result:**
- The page renders without a blank screen or error message
- After step 3, an element with `data-testid="foundry-era-open-baseline"` is visible
- After step 5, an element with `data-testid="foundry-final-summary"` is visible, positioned
  above the "Sources / Compiler" section header in the DOM
- No console errors appear in the browser DevTools console

---

### UT-02 — Operator reads the full Final Summary and a source's canonical provenance (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Hypothesis Foundry → Final Summary

**Preconditions:**
- The real committed Foundry epoch is present (`docs/hypothesis-foundry/epoch-manifest.json`,
  `source-registry.json`, `freeze-record.json`, `freeze-set.json` all tracked at HEAD — true in
  this repo by default)
- `curl http://localhost:8301/research/desk/micro/foundry` returns HTTP 200 with a non-null
  `final_summary` key (confirm before running this test)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Hypothesis Foundry" section header
3. Click the "Final Summary" section header
4. In the "Source counts by disposition" list, read each disposition/count pair
5. Below it, read the "Family count:", "Variant count:", "Frozen-ready total:", "Evidence class:",
   "Protected/withheld/sealed reads:", "Freeze integrity:", and "Epoch status:" lines
6. Read the diagnostic-survivor sentence and the exhaust-completion sentence
7. Scroll to the "Source detail (11 of 11 required objects)" list and locate the row whose
   `source_id` text reads `pilot-study-1-range-wall-failed-aggression` (badge text
   `ALIASED_PROXY_ONLY`)
8. Click that row's "Canonical provenance" `<summary>` text to expand it

**Expected Result:**
- Step 4: the counts across all disposition labels sum to 11 (e.g. `BLOCKED_DIRECTION: 4`,
  `ALIASED_PROXY_ONLY: 2`, `BLOCKED_SPEC_GAP: 1`, `ALIASED_VARIANT_VOCABULARY: 1`,
  `EXCLUDED_PREVIOUSLY_KILLED: 1`, `EXCLUDED_PREREQUISITE_UNMET: 1`, `EXCLUDED_GATE_CLOSED: 1`)
- Step 5: "Family count: 0", "Variant count: 0", "Frozen-ready total: 0", "Evidence class:
  historical_exposed_diagnostic", "Protected/withheld/sealed reads: 0" (rendered in green),
  "Freeze integrity: green" (rendered in green), "Epoch status: committed"
- Step 6: the text "Zero diagnostic survivors exist for this epoch (diagnostic_survivor_count =
  0) -- no candidate reached DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN this era." is visible (not a bare
  "0"); the text "Exhaust complete -- every frozen candidate reached a terminal state." is visible
  in emerald-colored text
- Step 8: the expanded body shows a "Mechanism:" line whose text mentions "band-map wall
  touches"/"aggression", an "Audit note:" line whose text mentions "ALIASED_PROXY_ONLY", a
  "Direction derivation:" line reading `BLOCKED_DIRECTION`, a "Comparator derivation:" line reading
  `complement_within_same_eligible_population`, a "Threshold provenance:" line, a "Superseded
  fields:" line, an "Alternatives:" line, a "Source hash:" line (64-character lowercase hex), and
  at least one quoted line of the form `"…text…" @ 0` (the first quoted span's location)

---

### UT-03 — Missing optional provenance field renders explicit absence text, not blank (validation / edge case)

**Type:** validation
**Priority:** P2
**Surface:** `/desk` → Hypothesis Foundry → Final Summary → source detail drill-in

**Preconditions:**
- Same as UT-02 (real epoch loaded)
- At least one real source record has `threshold_provenance: null` (verified directly against
  `docs/hypothesis-foundry/source-registry.json` before this test — several of the 11 real records
  carry a null value for this field)

**Steps:**
1. Navigate to `http://localhost:3301/desk`, expand "Hypothesis Foundry", then expand "Final
   Summary"
2. Find any source row in the "Source detail" list whose expanded body's "Threshold provenance:"
   value would come from a `null` underlying field (cross-check the row's `source_id` against
   `source-registry.json` to confirm `threshold_provenance` is `null` for that record)
3. Click that row's "Canonical provenance" `<summary>` to expand it
4. Read the "Threshold provenance:" line

**Expected Result:**
- The "Threshold provenance:" line shows the literal text `(none)` — never blank, never the
  literal string `null`, never omitted entirely
- If that same record's `alternatives` array is empty, the "Alternatives:" line similarly shows
  `(none)` rather than blank
- If that same record's `superseded_fields` object is empty, the "Superseded fields:" line shows
  `{}` rather than blank

---

### UT-04 — Foundry panel degrades honestly when the backend is unreachable (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` → Hypothesis Foundry

**Preconditions:**
- Frontend running at http://localhost:3301
- Chrome DevTools available to block a network request

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Open Chrome DevTools → Network tab, and add a request-blocking rule for the URL pattern
   `*/research/desk/micro/foundry*`
3. Reload the page (F5)
4. Click the "Hypothesis Foundry" section header

**Expected Result:**
- The panel does NOT crash the page or show a blank white screen
- An element with `data-testid="foundry-panel-unavailable"` is visible with an explicit error
  message (e.g. "The Hypothesis Foundry panel could not be loaded." or the underlying fetch error
  text)
- No `foundry-final-summary` element renders (since no data was returned) — no fabricated/zeroed
  values are shown in its place

---

### UT-05 — The six pre-existing Foundry subsections still render correctly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Hypothesis Foundry → Sources/Compiler, Interpreter Fixtures,
Freeze/Integrity, Hermetic Oracles, Epoch/Manifest, Runner/Checkpoint

**Preconditions:**
- Same as UT-02 (real epoch loaded, backend reachable)

**Steps:**
1. Navigate to `http://localhost:3301/desk`, expand "Hypothesis Foundry"
2. Click each of the following section headers one at a time, in order, and confirm each expands:
   "Sources / Compiler" (`desk-section-expand-foundry-sources-compiler-section`), "Interpreter
   Fixtures" (`desk-section-expand-foundry-interpreter-fixtures-section`), "Freeze / Integrity"
   (`desk-section-expand-foundry-freeze-integrity-section`), "Hermetic Oracles"
   (`desk-section-expand-foundry-hermetic-oracles-section`), "Epoch / Manifest"
   (`desk-section-expand-foundry-epoch-manifest-section`), "Runner / Checkpoint"
   (`desk-section-expand-foundry-runner-checkpoint-section`)
3. Inside "Epoch / Manifest", locate `data-testid="foundry-epoch-source-disposition-rows"` and
   confirm all 11 source rows still render their `source_id` and `disposition` text
4. Inside "Runner / Checkpoint", read `data-testid="foundry-runner-freeze-integrity-verdict"` and
   `data-testid="foundry-runner-exhaust-complete"` (or `-exhaust-incomplete`)

**Expected Result:**
- Each of the six subsections expands and shows its previously-shipped content with no console
  errors and no missing fields
- Step 3: the 11 source-disposition rows in "Epoch / Manifest" render identically to before this
  iteration (unaffected by the new provenance-enrichment fields the backend now attaches — those
  fields are additive, not replacing, so this subsection's own rendering is unchanged)
- Step 4: the freeze-integrity verdict ("green") and exhaust-completion state shown here match
  exactly what "Final Summary" shows for `freeze_integrity_verdict` and `exhaust_complete` (cross-
  subsection consistency — both read the same backend values, never independently recomputed)

---

### UT-06 — Final Summary is discoverable within a few clicks from the home page (UX)

**Type:** ux
**Priority:** P2
**Surface:** navigation → `/desk` → Hypothesis Foundry → Final Summary

**Steps:**
1. Navigate to `http://localhost:3301/` (Cockpit / home page)
2. Look at the top navigation bar (`data-testid="app-nav"`) and click the "Desk" link
3. On `/desk`, scroll down (or use browser find, Ctrl+F, for "Hypothesis Foundry") to locate the
   "Hypothesis Foundry" section header
4. Click it to expand, then locate and click "Final Summary"

**Expected Result:**
- Step 2: the "Desk" link is visible in the nav bar and navigates to `http://localhost:3301/desk`
- Step 3: the "Hypothesis Foundry" section header is visible and labeled clearly (no ambiguous or
  cryptic label)
- Step 4: "Final Summary" is the first subsection to expand inside the Hypothesis Foundry panel
  (appears immediately after the Era-Open Baseline block and before "Sources / Compiler"), so an
  operator does not need to expand any of the six older subsections to find it

---

## Automated-suite-only checks (not manual-browser test cases)

The following Definition-of-Done test scenarios are verified by the automated backend/TypeScript
suites rather than by manual browser interaction, and are out of scope for this manual test plan:

- TC-6 (`test_desk_page_price_arithmetic_guard_catches_foundry_field_arithmetic`) — static-source
  regex guard against client-side arithmetic on served numeric fields
- TC-7 (page effect/timer census unchanged) — static-source guard test
- TC-8 (`test_vault.py` TR-2 opaque-pool inference sweep) — backend integration test
- TC-9 (`test_copy_discipline.py` banned-phrase lint) — static-source lint
- TC-10 (corrected test docstring) — code-review-level check, not a runtime behavior
- TC-11 (full backend suite + `tsc --noEmit`) — CI-level check

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Panel + Final Summary load | smoke | P1 | `/desk` |
| UT-02 | Full Final Summary + source drill-in read | happy-path | P1 | `/desk` → Final Summary |
| UT-03 | Missing optional field renders `(none)` | validation | P2 | `/desk` → Final Summary drill-in |
| UT-04 | Backend unreachable degrade | error | P2 | `/desk` → Hypothesis Foundry |
| UT-05 | Six existing subsections unaffected | regression | P1 | `/desk` → Hypothesis Foundry |
| UT-06 | Discoverability from home | ux | P2 | nav → `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.**
