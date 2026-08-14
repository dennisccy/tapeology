# UI Test Results (merged)

**Date:** 2026-08-14
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-1-evidence/J-10-verify.png |
| UT-J-01 | The era transition stands — reconciliation made testable (evidence readiness fold) | smoke | P1 | `GET /research/desk/referee/evidence` live on the running QA-rig backend, HTTP 200, JSON matching the documented per-family readiness contract (`playbook_occurrence` + `strategy_trade`); `config_fingerprint` pin `08e471b10130e1e2` unchanged; `tick_gate_met` false with a non-empty `tick_gate_statement` naming the gate and shortfall; a non-empty `basis_caveats` entry naming the Card-6.4 `levels._bars_as_of` / `epoch <= as_of` forming-bar admission | Navigated to `http://localhost:8301/research/desk/referee/evidence` — HTTP 200, JSON rendered in-browser, byte-identical to a direct curl of the same URL. Full shape verified (see Passed Tests below); pin unchanged; TC-4's two exact-text requirements both satisfied | PASS | `reports/qa/goal-referee-iter-1-evidence/UT-J-01-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-14

