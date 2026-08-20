# Phase goal-rapid-microscope-iter-19 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-19
**Date:** 2026-08-20
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301

---

## Context

This iteration shipped **zero `.tsx` changes** — every surface below is existing and unchanged. What changed is the automated regression harness: four golden replay scripts (J-02–J-05) now assert real, section-specific text instead of an unrelated pre-existing Desk heading, and the full 8-journey golden-replay set (J-01, J-02, J-03, J-04, J-05, J-06, J-08, J-10) is mandatory this round because the diff touches the shared QA launcher and four golden scripts. These test cases exist to give a human operator the same discriminating coverage the deepened golden scripts now have, plus the standing J-10 kept-product sentinel re-verification. No test case below exercises a new capability.

All `/desk` sections referenced are collapsed by default; each must be expanded by clicking its section header (`data-testid="desk-section-expand-<id>"`) before its body content is checked.

---

## Test Cases

---

### UT-01 — `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend is running and reachable (fixture-scoped backend for an isolated QA pass, per `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`, or the ambient dev backend for a manual spot-check)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The heading "Playbook Signals" is visible
- No console errors

---

### UT-02 — Microscope Readiness section shows "Fallback frac" column (happy-path, J-02 target)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Microscope Readiness section

**Preconditions:**
- `/desk` is loaded (UT-01)
- Backend readiness data includes at least one recorded tick shard (the "Fallback frac" header only renders inside the Legacy Tick Shards table, which is replaced by an "No tick shards recorded." empty state when `shards` is empty — the fixture-scoped QA backend seeds shard data for this)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Microscope Readiness" section header (`data-testid="desk-section-expand-microReadiness"`)
3. Scroll to the "Legacy Tick Shards" table within the expanded section

**Expected Result:**
- The section body expands (arrow marker flips from "▸" to "▾")
- A table with the column header text "Fallback frac" is visible under the "Legacy Tick Shards" heading
- The table has additional column headers alongside it: "Symbol", "Session date", "Feed", "Window (ET)", "Trades", "Quotes", "Bytes", "Coverage gaps", "Checksum", "Split provenance", "Exposure state"

---

### UT-03 — Microscope Readiness section shows "Joinable corpus — withheld (excluded)" row (happy-path, J-03 target)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Microscope Readiness section

**Preconditions:**
- `/desk` is loaded (UT-01)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Microscope Readiness" section header (`data-testid="desk-section-expand-microReadiness"`)
3. Locate the Joinable Corpus summary table (above the Legacy Tick Shards table)

**Expected Result:**
- A table row with the label text "Joinable corpus — withheld (excluded)" is visible
- The row's right-hand cell (`data-testid="micro-readiness-withheld-excluded"`) shows a numeric value (not blank, not an error string)

---

### UT-04 — Scout Ledger section shows "Ledger chain verification:" (happy-path, J-04 target)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Scout Ledger section

**Preconditions:**
- `/desk` is loaded (UT-01)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Scout Ledger" section header (`data-testid="desk-section-expand-scoutLedger"`)

**Expected Result:**
- The section body expands
- The text "Ledger chain verification:" is visible, immediately followed by either the word "ok" or a string of the form "failed at row N (reason)"
- This value is sourced from `GET /research/desk/micro/scout`'s `chain_verification` field — it must not read "Loading" or show the "The scout ledger could not be loaded." unavailable message

---

### UT-05 — Walk-Forward section shows "Ledger chain verification:" (happy-path, J-05 target)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Walk-Forward section

**Preconditions:**
- `/desk` is loaded (UT-01)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Walk-Forward" section header (`data-testid="desk-section-expand-walkForward"`)

**Expected Result:**
- The section body expands
- The text "Ledger chain verification:" is visible, immediately followed by either the word "ok" or a string of the form "failed at row N (reason)"
- This value is sourced from `GET /research/desk/micro/walkforward`'s `chain_verification` field — it must not read "Loading" or show the "The walk-forward ledger could not be loaded." unavailable message

---

### UT-06 — J-10 kept-product sentinel: Cockpit → Structure → Desk, end to end (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/structure`, `/desk`

**Preconditions:**
- Frontend and backend running; for a faithful replay use the fixture-scoped backend seeded per `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` (its AAPL bar series is copied verbatim from the real store so the `/structure` step measures the kept product, not a fixture)

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Confirm the text "No ticker watched" is visible
3. Type "SIM-BUYER" into the field labeled "Ticker"
4. Click the "Watch" button
5. Confirm the text "Buyer Control" appears
6. Navigate to `http://localhost:3301/structure`
7. Confirm the text "Tradable Map" is visible
8. Type "AAPL" into the field labeled "Structure symbol"
9. Type "2026-06-22 16:00:00" into the field with `data-testid="structure-as-of-input"`
10. Click the button with `data-testid="structure-load-button"`
11. Confirm the text "300.11–302.2" appears
12. Navigate to `http://localhost:3301/desk`
13. Confirm the text "Playbook Signals" is visible
14. Click the "Microscope Readiness" section header (`data-testid="desk-section-expand-microReadiness"`); confirm "Distinct symbol-days" is visible
15. Click the "Scout Ledger" section header (`data-testid="desk-section-expand-scoutLedger"`); confirm "No candidates ledgered." is visible
16. Click the "Walk-Forward" section header (`data-testid="desk-section-expand-walkForward"`); confirm "No fold specs registered." is visible

**Expected Result:**
- Every confirm step above passes on the first attempt, in order, with no navigation error, blank page, or console error at any step
- This proves the whole kept-product sentinel is unaffected by this iteration's harness-only changes

---

### UT-07 — Validation Vault and all three Referee sections still render correctly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — Validation Vault, Referee Registry, Referee Adjudications, Referee Runs sections

**Preconditions:**
- `/desk` is loaded (UT-01)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Validation Vault" section header (`data-testid="desk-section-expand-validationVault"`); confirm "iter18-qa-universe" is visible
3. Click the "Referee Registry" section header (`data-testid="desk-section-expand-refereeRegistry"`); confirm "config fingerprint 08e471b10130e1e2" is visible
4. Click the "Referee Adjudications" section header (`data-testid="desk-section-expand-refereeAdjudications"`); confirm "No hypotheses registered." is visible
5. Click the "Referee Runs" section header (`data-testid="desk-section-expand-refereeRuns"`); confirm "No evaluation runs recorded yet." is visible

**Expected Result:**
- All four confirm steps pass; none of these sections' text has changed from prior iterations

---

### UT-08 — Section headings stay visible while collapsed (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` — all `CollapsibleSection` sections

**Preconditions:**
- `/desk` is loaded (UT-01), no sections expanded yet

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Without clicking anything, visually scan the page below "Playbook Signals"

**Expected Result:**
- The headings "Referee Registry", "Referee Adjudications", "Referee Runs", "Microscope Readiness", "Scout Ledger", "Walk-Forward", "Validation Vault" are all visible even though every section body is collapsed
- Each heading shows a "▸" (collapsed) marker to its left
- No section heading is missing or replaced by blank space

---

### UT-09 — Expanding then re-collapsing a section hides its body but keeps the heading (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` — Microscope Readiness section

**Preconditions:**
- `/desk` is loaded (UT-01)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Microscope Readiness" section header (`data-testid="desk-section-expand-microReadiness"`)
3. Confirm the body content (Joinable Corpus table, "Fallback frac" column) is now visible and the marker shows "▾"
4. Click the "Microscope Readiness" section header again
5. Confirm the body content disappears and the marker returns to "▸"

**Expected Result:**
- The heading "Microscope Readiness" remains visible through both clicks
- The body mounts on first expand and unmounts on re-collapse (not merely hidden via CSS — confirms the section's own data fetch is deferred to first expand, per `CollapsibleSection`'s documented design)

---

### UT-10 — Backend-unavailable state shows the real error panel, not fabricated ledger text (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` — Scout Ledger section

**Preconditions:**
- A way to make `GET /research/desk/micro/scout` fail or time out (e.g., stop the backend process after the frontend has loaded but before expanding the section, or block the route via devtools network throttling/offline mode)

**Steps:**
1. Navigate to `http://localhost:3301/desk` with the backend reachable
2. Stop the backend process (or set the browser to offline / block the `/research/desk/micro/scout` request)
3. Click the "Scout Ledger" section header (`data-testid="desk-section-expand-scoutLedger"`)

**Expected Result:**
- The section shows an unavailable-state panel (`data-testid="scout-ledger-unavailable"`) with an error message (e.g., "The scout ledger could not be loaded.")
- The text "Ledger chain verification:" does NOT appear — this proves UT-04's assertion is not vacuous: the deepened golden script would correctly fail here rather than silently pass, since the `UnavailablePanel` branch renders different text than the asserted string

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads | smoke | P1 | `/desk` |
| UT-02 | Microscope Readiness "Fallback frac" (J-02) | happy-path | P1 | `/desk` |
| UT-03 | Microscope Readiness withheld-excluded row (J-03) | happy-path | P1 | `/desk` |
| UT-04 | Scout Ledger chain verification (J-04) | happy-path | P1 | `/desk` |
| UT-05 | Walk-Forward chain verification (J-05) | happy-path | P1 | `/desk` |
| UT-06 | J-10 kept-product sentinel, end to end | regression | P1 | `/`, `/structure`, `/desk` |
| UT-07 | Validation Vault + Referee sections | regression | P1 | `/desk` |
| UT-08 | Collapsed headings stay visible | ux | P2 | `/desk` |
| UT-09 | Expand/collapse mounts and unmounts body | ux | P2 | `/desk` |
| UT-10 | Backend-unavailable shows real error panel | error | P2 | `/desk` |

**Validation-type tests:** none — no form was added or changed this iteration.

**P1 tests must all pass for browser QA verdict to be PASS.**
