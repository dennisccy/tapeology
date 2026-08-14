# UI Test Results (merged)

**Date:** 2026-08-14
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 3/3 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-2-evidence/J-10-verify.png |
| UT-J-01 | The era transition stands — reconciliation made testable (evidence readiness fold) | smoke | P1 | `GET /research/desk/referee/evidence` live on the running QA-rig backend, HTTP 200, JSON matching the documented per-family readiness contract (`playbook_occurrence` + `strategy_trade`); `config_fingerprint` pin `08e471b10130e1e2` unchanged; `tick_gate_met` false with a non-empty `tick_gate_statement`; a non-empty `basis_caveats` entry naming the Card-6.4 forming-bar admission | Navigated to `http://localhost:8301/research/desk/referee/evidence` — HTTP 200 (page rendered the JSON body, no error page), byte-identical to iteration 1's recorded response and to a direct curl of the same URL. Full shape verified (see below) | PASS | `reports/qa/goal-referee-iter-2-evidence/UT-J-01-result.png` |
| UT-J-02 | The evidence contract — two families, one observation shape (live-endpoint regression check) | smoke | P1 | J-02 adds no new route (per DoD: "browser-qa-agent confirms no live-endpoint regression — J-02 adds no new route to smoke"); the existing J-01-built endpoint, served by the SAME module (`referee_evidence.py`) J-02 extends, must remain byte-identical after J-02's changes | Re-navigated to `http://localhost:8301/research/desk/referee/evidence` in a second independent browser navigation — byte-identical response body to the UT-J-01 navigation (diffed the two captured page-content files: 0 differences) and to iteration 1's recorded shape. No new route exists to smoke; none was found | PASS | `reports/qa/goal-referee-iter-2-evidence/UT-J-02-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-14

