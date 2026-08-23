# UI Test Results (merged)

**Date:** 2026-08-23
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 9/9 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-25-evidence/J-01-verify.png |
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-25-evidence/J-02-verify.png |
| UT-J-03 | Structure × flow — the join that never looks ahead | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-25-evidence/J-03-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-25-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-25-evidence/J-05-verify.png |
| UT-J-08 | The surface and MCP v6 — the funnel is visible | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-25-evidence/J-08-verify.png |
| UT-J-09 | The pilot studies — three predeclared questions, honest answers | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-25-evidence/J-09-verify.png |
| UT-J-10 | The kept product stands — traps armed, sentinel green | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-25-evidence/J-10-verify.png |
| UT-J-06 | The recorder and the Vault — new tape, sealed at birth | regression/acceptance | P1 | Vault "Sealed at" cell for the pre-existing exposed shard is a bare date (no clock time); the new still-sealed shard's row renders the literal "sealed — opaque" text across Dataset/Family root/Symbol/Session date/Assigned at/Exposed at/Content checksum | Navigated to `/desk`, expanded "Validation Vault". Exposed shard `vshard-b018e9...` "Sealed at" cell reads `2026-05-01` — bare date, no `T`, no colon, no clock time. New sealed shard `vshard-71a307...` "Sealed at" cell reads `2026-06-07` — also bare. The sealed shard's Dataset/Family root/Symbol/Session date/Assigned at/Exposed at/Content checksum cells all render the literal text "sealed — opaque"; the exposed shard's same columns show real values (dataset id, family root, symbol `PGQA`, session date, timestamps, checksum). Confirmed both via page-text extraction and two screenshots (full-width and horizontally-scrolled to reveal the opaque columns). | PASS | `reports/qa/goal-rapid-microscope-iter-25-evidence/UT-J-06-result.png` (+ `J-06-vault-sealed-opaque.png`) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-23

