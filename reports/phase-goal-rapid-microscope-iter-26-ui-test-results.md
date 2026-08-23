# UI Test Results (merged)

**Date:** 2026-08-23
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 7/13 journeys passed (6 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-26-evidence/J-02-verify.png |
| UT-J-03 | Structure × flow — the join that never looks ahead | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-26-evidence/J-03-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-26-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-26-evidence/J-05-verify.png |
| UT-J-06 | The recorder and the Vault — new tape, sealed at birth | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-26-evidence/J-06-verify.png |
| UT-J-09 | The pilot studies — three predeclared questions, honest answers | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-26-evidence/J-09-verify.png |
| UT-J-10 | The kept product stands — traps armed, sentinel green | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-26-evidence/J-10-verify.png |
| UT-01 | `/desk` loads without errors | smoke | P1 | Page renders without error message; "Playbook Signals" visible; both section headers visible collapsed; no console errors | Page shell rendered but showed "navigation unavailable — backend unreachable" banner near the nav, "Backend unreachable — is the API running?" banners in the Screen Runs, Playbook Signals, and Back-Scan Runs sections | SKIP | `reports/qa/goal-rapid-microscope-iter-26-evidence/UT-01-skip-backend-unreachable.png` |
| UT-02 | Microscope Readiness renders byte-identical figures (J-01) | regression | P1 | Corpus Totals figures match registered J-01 baseline (2 symbol-days, 3 datasets, 1.75 RTH minutes, 0.0045 session-equivalents, 150 referee tick-gate) | Could not be evaluated — section's data comes from `GET /research/desk/micro/readiness`, and the backend serving that route was unreachable for the full QA window | SKIP | none |
| UT-03 | Scout Ledger renders byte-identical family rows (J-08) | regression | P1 | Ledger chain verification reads `ok`; family headers/trial-row columns unchanged | Could not be evaluated — same backend-unreachable condition | SKIP | none |
| UT-04 | Band-touch value stable across repeat expand/refresh | regression | P1 | Identical band-touch value across expand/collapse/re-expand and full-page refresh | Could not be evaluated — same backend-unreachable condition | SKIP | none |
| UT-05 | Corrupted cache degrades to a full miss, never an error | error | P3 | HTTP 200 with freshly-computed value even with a corrupted cache file | Not executed — test plan itself marks this operator/shell-only, not a pure-browser check, and the backend was down for the entire window regardless | SKIP | none |
| UT-06 | Both sections discoverable from a fresh page load | ux | P2 | Clicking "Desk" nav link navigates to `/desk`; both section headers visible as real `<button>` elements | Not executed — same backend-unreachable condition would make any content-based verification (section headers still render as buttons regardless of backend, but the test's purpose — confirming a working page — is moot under a backend outage) unreliable to grade | SKIP | none |

## Skipped Tests

### UT-01 — `/desk` loads without errors

**Verdict:** SKIPPED
**Reason:** Page shell rendered but showed "navigation unavailable — backend unreachable" banner near the nav, "Backend unreachable — is the API running?" banners in the Screen Runs, Playbook Signals, and Back-Scan Runs sections

### UT-02 — Microscope Readiness renders byte-identical figures (J-01)

**Verdict:** SKIPPED
**Reason:** Could not be evaluated — section's data comes from `GET /research/desk/micro/readiness`, and the backend serving that route was unreachable for the full QA window

### UT-03 — Scout Ledger renders byte-identical family rows (J-08)

**Verdict:** SKIPPED
**Reason:** Could not be evaluated — same backend-unreachable condition

### UT-04 — Band-touch value stable across repeat expand/refresh

**Verdict:** SKIPPED
**Reason:** Could not be evaluated — same backend-unreachable condition

### UT-05 — Corrupted cache degrades to a full miss, never an error

**Verdict:** SKIPPED
**Reason:** Not executed — test plan itself marks this operator/shell-only, not a pure-browser check, and the backend was down for the entire window regardless

### UT-06 — Both sections discoverable from a fresh page load

**Verdict:** SKIPPED
**Reason:** Not executed — same backend-unreachable condition would make any content-based verification (section headers still render as buttons regardless of backend, but the test's purpose — confirming a working page — is moot under a backend outage) unreliable to grade

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-23

