# Regression Replay — goal-observation-contract-iter-7

**Phase:** goal-observation-contract-iter-7
**Date:** 2026-09-05
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 0/1 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The artifact is a pure projection with semantic identity, provenance and integrity | regression | P1 | journey replays end-to-end; all expects hold | step 05 expected ""schema_version":"tape-observation-v1"" did not appear | FAIL | reports/qa/goal-observation-contract-iter-7-evidence/J-01-verify.png |

## Failed Tests

### UT-J-01 — The artifact is a pure projection with semantic identity, provenance and integrity

**Verdict:** FAIL
**Failure:** step 05 expected ""schema_version":"tape-observation-v1"" did not appear
**Evidence:** `reports/qa/goal-observation-contract-iter-7-evidence/J-01-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-09-05

---

_Reconciliation (2026-09-05): the replay FAIL row(s) for J-01 above were overturned by the LLM lane's re-confirmation this iteration (golden-script false positive). The authoritative merged verdicts are in phase-goal-observation-contract-iter-7-ui-test-results.md; the FAIL row(s) above are superseded._
