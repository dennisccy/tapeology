# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-18 — UI Test Results

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-18
**Date:** 2026-06-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

**Overall:** 0/33 tests passed (33 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Studies nav entry is active link | smoke | P1 | Nav item clickable with pointer cursor | Frontend not running | SKIP | none |
| UT-02 | Studies nav entry navigates to /studies | smoke | P1 | Navigates to /studies with active highlight | Frontend not running | SKIP | none |
| UT-03 | /studies page loads with required structure | smoke | P1 | Page renders heading, form, and empty right panel | Frontend not running | SKIP | none |
| UT-04 | /studies empty selection state shows placeholder | smoke | P1 | Right column shows "∅" and placeholder text | Frontend not running | SKIP | none |
| UT-05 | StudyList shows "No studies yet" empty state | smoke | P1 | Job list shows "No studies yet" text | Frontend not running | SKIP | none |
| UT-06 | StudyList shows brief loading state on reload | smoke | P2 | Loading indicator visible briefly on hard reload | Frontend not running | SKIP | none |
| UT-07 | Create study with Reference Window: happy path | happy-path | P1 | Study runs to Done, results show distributions and occurrences table | Frontend not running | SKIP | none |
| UT-08 | Create study with Seeded Sim (SIM-REVERSAL) | happy-path | P1 | Seeded sim study runs to Done with feed chip showing sim identifier | Frontend not running | SKIP | none |
| UT-09 | Create study with Symbol + Past Window: fields appear | happy-path | P1 | Symbol, date, time fields and preset buttons visible | Frontend not running | SKIP | none |
| UT-10 | Level setup shows level input and hindsight warning | validation | P1 | Level price field and amber warning visible for level_break; hidden for others | Frontend not running | SKIP | none |
| UT-11 | Run Study disabled when required fields missing | validation | P1 | Run study button disabled until all required fields filled | Frontend not running | SKIP | none |
| UT-12 | Run Study button transitions to "Running…" in flight | validation | P2 | Button text changes to "Running…" during request | Frontend not running | SKIP | none |
| UT-13 | Run Study enabled only after level price filled | validation | P1 | Button enabled only when level price is provided for level_break | Frontend not running | SKIP | none |
| UT-14 | Job list shows correct status badge colors | happy-path | P1 | Done=slate, Running=amber, Cancelled=slate, Failed=rose | Frontend not running | SKIP | none |
| UT-15 | Cancel running study: badge → Cancelled, button gone | happy-path | P1 | Badge changes to Cancelled; Cancel button disappears | Frontend not running | SKIP | none |
| UT-16 | Cancelled study shows PARTIAL warning above results | happy-path | P1 | PARTIAL amber label visible above partial occurrence data | Frontend not running | SKIP | none |
| UT-17 | Failed study shows rose error message in results | error | P1 | Rose error box with backend error message in results panel | Frontend not running | SKIP | none |
| UT-18 | Backend 422 error surfaces inline below form | error | P2 | Rose error box below form on 422 response | Frontend not running | SKIP | none |
| UT-19 | Queued study shows queued-specific absence copy | ux | P2 | Results panel shows queued-specific text, distinct from running copy | Frontend not running | SKIP | none |
| UT-20 | Running study shows running-specific absence copy | ux | P2 | Results panel shows running-specific text, distinct from queued copy | Frontend not running | SKIP | none |
| UT-21 | Running study row shows events-processed counter | ux | P2 | Monospace counter "N events processed" visible on running row | Frontend not running | SKIP | none |
| UT-22 | Results: side-by-side distributions with four chips | happy-path | P1 | Two distribution blocks with +1R, −1R, neither, Truncated chips per horizon | Frontend not running | SKIP | none |
| UT-23 | Results: occurrences table with correct columns | happy-path | P1 | Table with "Arm time (logical s)", "Verdict reached", "R basis" columns in monospace | Frontend not running | SKIP | none |
| UT-24 | Results: honesty stamps visible in header | happy-path | P1 | Three monospace chips: Feed, Config fingerprint, Baseline seed | Frontend not running | SKIP | none |
| UT-25 | Results: measurement-framing line visible twice | happy-path | P1 | "Descriptive only — not trading advice" appears above and below distribution blocks | Frontend not running | SKIP | none |
| UT-26 | Level-break results: hindsight label and amber caption | happy-path | P1 | Amber "Level chosen with hindsight" label and amber caption in results panel | Frontend not running | SKIP | none |
| UT-27 | Level-break row shows amber Hindsight chip in list | happy-path | P1 | Amber "Hindsight level" chip visible on level_break job list row | Frontend not running | SKIP | none |
| UT-28 | Insufficient sample marker in distribution block | ux | P2 | Amber "Insufficient sample (n = X < Y)" chip inside distribution block | Frontend not running | SKIP | none |
| UT-29 | Re-run identical: new row with matching counts | happy-path | P1 | New row with same setup; completed counts match original exactly | Frontend not running | SKIP | none |
| UT-30 | J-68: cockpit unchanged except Studies nav entry | regression | P1 | Cockpit identical to prior iteration; only Studies nav entry changed | Frontend not running | SKIP | none |
| UT-31 | Journal and Cockpit pages still reachable | regression | P1 | Cockpit and Journal nav links load pages without error | Frontend not running | SKIP | none |
| UT-32 | Studies discoverable in 1 click from home | ux | P2 | Studies visible in nav and reachable in exactly 1 click from home | Frontend not running | SKIP | none |
| UT-33 | Feed and fingerprint stamps distinct per study | ux | P1 | Different Feed chip values per source; fingerprint tooltip shows full hash | Frontend not running | SKIP | none |

---

## Passed Tests

None — all tests were skipped.

---

## Failed Tests

None — all tests were skipped.

---

## Skipped Tests

All 33 tests were skipped because the frontend was not running at http://localhost:3650 at the time browser QA was invoked.

### UT-01 — Studies nav entry is active link
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-02 — Studies nav entry navigates to /studies
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-03 — /studies page loads with required structure
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-04 — /studies empty selection state shows placeholder
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-05 — StudyList shows "No studies yet" empty state
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-06 — StudyList shows brief loading state on reload
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-07 — Create study with Reference Window: happy path
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-08 — Create study with Seeded Sim (SIM-REVERSAL)
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-09 — Create study with Symbol + Past Window: fields appear
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-10 — Level setup shows level input and hindsight warning
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-11 — Run Study disabled when required fields missing
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-12 — Run Study button transitions to "Running…" in flight
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-13 — Run Study enabled only after level price filled
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-14 — Job list shows correct status badge colors
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-15 — Cancel running study: badge → Cancelled, button gone
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-16 — Cancelled study shows PARTIAL warning above results
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-17 — Failed study shows rose error message in results
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-18 — Backend 422 error surfaces inline below form
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-19 — Queued study shows queued-specific absence copy
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-20 — Running study shows running-specific absence copy
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-21 — Running study row shows events-processed counter
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-22 — Results: side-by-side distributions with four chips
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-23 — Results: occurrences table with correct columns
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-24 — Results: honesty stamps visible in header
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-25 — Results: measurement-framing line visible twice
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-26 — Level-break results: hindsight label and amber caption
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-27 — Level-break row shows amber Hindsight chip in list
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-28 — Insufficient sample marker in distribution block
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-29 — Re-run identical: new row with matching counts
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-30 — J-68: cockpit unchanged except Studies nav entry
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-31 — Journal and Cockpit pages still reachable
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-32 — Studies discoverable in 1 click from home
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-33 — Feed and fingerprint stamps distinct per study
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Browser:** Chrome via MCP (not used — frontend unavailable)
- **Test Date:** 2026-06-12
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-18-evidence/` (not created — no tests ran)
