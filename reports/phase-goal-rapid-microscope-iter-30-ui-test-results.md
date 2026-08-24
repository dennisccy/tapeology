# UI Test Results (merged)

**Date:** 2026-08-24
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 10/10 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-30-evidence/J-01-verify.png |
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-30-evidence/J-02-verify.png |
| UT-J-03 | Structure × flow — the join that never looks ahead | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-30-evidence/J-03-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-30-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-30-evidence/J-05-verify.png |
| UT-J-06 | The recorder and the Vault — new tape, sealed at birth | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-30-evidence/J-06-verify.png |
| UT-J-08 | The surface and MCP v6 — the funnel is visible | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-30-evidence/J-08-verify.png |
| UT-J-09 | The pilot studies — three predeclared questions, honest answers | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-30-evidence/J-09-verify.png |
| UT-J-10 | The kept product stands — traps armed, sentinel green | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-30-evidence/J-10-verify.png |
| UT-J-07 | Graduation — provenance in, nothing laundered out | regression | P1 | Fixture candidate walks `exploratory → walkforward_survivor → sealed_survivor → referee_handoff_ready` on synthetic class-2 evidence; diagnostic-only twin refused at first transition; failed-sealed twin carries its permanent verdict in the bundle; referee registration language present; no UI regression around the (by-design) UI-less journey | `pytest tests/test_micro_graduation.py`: 23/23 passed in 2.226s, including `test_tc3_and_tc4_the_full_pipeline_produces_a_validating_bundle_and_referee_handoff_ready`, `test_tc5_a_diagnostic_only_twin_is_refused_and_state_stays_exploratory`, `test_tc6_a_failed_sealed_evaluation_never_advances_and_is_carried_into_the_bundle`. Browser confirmed `GET /research/desk/micro/graduation` (port 8301) returns 200 with real family/sealed-evaluation data (not a 500/empty stub), and confirmed `/desk` (port 3301) still renders its full section list ending at "VALIDATION VAULT" with no Graduation section — matching the goal's own Product Shape (only 4 new `/desk` sections: Microscope Readiness · Scout Ledger · Walk-Forward · Validation Vault; Graduation is not one of them) and the goal doc's framing of J-07 as "keyless/automated" (not one of the two browser-verifiable journeys J-01/J-08). No console errors captured. | PASS | `reports/qa/goal-rapid-microscope-iter-30-evidence/J-07-desk-no-graduation-ui.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-24

