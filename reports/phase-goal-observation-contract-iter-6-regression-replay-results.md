# Regression Replay — goal-observation-contract-iter-6

**Phase:** goal-observation-contract-iter-6
**Date:** 2026-09-05
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 1/3 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The artifact is a pure projection with semantic identity, provenance and integrity | regression | P1 | journey replays end-to-end; all expects hold | step 05 expected ""schema_version":"tape-observation-v1"" did not appear | FAIL | reports/qa/goal-observation-contract-iter-6-evidence/J-01-verify.png |
| UT-J-02 | Market-event time, measured availability and generation time are three distinct, honest instants, read atomically | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-observation-contract-iter-6-evidence/J-02-verify.png |
| UT-J-03 | Lifecycle, feed basis and session identity stay honest | regression | P1 | journey replays end-to-end; all expects hold | step 11 expected ""source_mode":"sim"" did not appear | FAIL | reports/qa/goal-observation-contract-iter-6-evidence/J-03-verify.png |

## Failed Tests

### UT-J-01 — The artifact is a pure projection with semantic identity, provenance and integrity

**Verdict:** FAIL
**Failure:** step 05 expected ""schema_version":"tape-observation-v1"" did not appear
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/J-01-verify.png`

### UT-J-03 — Lifecycle, feed basis and session identity stay honest

**Verdict:** FAIL
**Failure:** step 11 expected ""source_mode":"sim"" did not appear
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/J-03-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-09-05

---

_Reconciliation (2026-09-05): the replay FAIL row(s) for J-01 J-03 above were overturned by the LLM lane's re-confirmation this iteration (golden-script false positive). The authoritative merged verdicts are in phase-goal-observation-contract-iter-6-ui-test-results.md; the FAIL row(s) above are superseded._
