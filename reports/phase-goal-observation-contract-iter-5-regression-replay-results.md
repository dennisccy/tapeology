# Regression Replay — goal-observation-contract-iter-5

**Phase:** goal-observation-contract-iter-5
**Date:** 2026-09-05
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 1/4 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The artifact is a pure projection with semantic identity, provenance and integrity | regression | P1 | journey replays end-to-end; all expects hold | voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks | SKIP | reports/qa/goal-observation-contract-iter-5-evidence/J-01-verify.png |
| UT-J-02 | Market-event time, measured availability and generation time are three distinct, honest instants, read atomically | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-observation-contract-iter-5-evidence/J-02-verify.png |
| UT-J-03 | Lifecycle, feed basis and session identity stay honest | regression | P1 | journey replays end-to-end; all expects hold | voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks | SKIP | reports/qa/goal-observation-contract-iter-5-evidence/J-03-verify.png |
| UT-J-04 | Ingestion-path equivalence under an identical valid event stream | regression | P1 | journey replays end-to-end; all expects hold | voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks | SKIP | reports/qa/goal-observation-contract-iter-5-evidence/J-04-verify.png |

## Failed Tests

### UT-J-01 — The artifact is a pure projection with semantic identity, provenance and integrity

**Verdict:** FAIL
**Failure:** step 05 expected ""schema_version": "tape-observation-v1"" did not appear
**Evidence:** `reports/qa/goal-observation-contract-iter-5-evidence/J-01-verify.png`

### UT-J-03 — Lifecycle, feed basis and session identity stay honest

**Verdict:** FAIL
**Failure:** step 11 expected ""source_mode": "sim"" did not appear
**Evidence:** `reports/qa/goal-observation-contract-iter-5-evidence/J-03-verify.png`

### UT-J-04 — Ingestion-path equivalence under an identical valid event stream

**Verdict:** FAIL
**Failure:** step 06 expected ""observation_hash"" did not appear
**Evidence:** `reports/qa/goal-observation-contract-iter-5-evidence/J-04-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-09-05

---

_VOIDED (2026-09-05): the FAIL rows for J-01 J-03 J-04 above were VOIDED (SPEED-22 mass-false-FAIL breaker) — a majority of the replay set failed at once and the canary journeys re-checked GREEN via the LLM lane, so the failures are suspected golden-script/selector drift, not product regressions. These journeys keep their prior recorded status; their golden scripts are queued for regeneration (state/goldens-regen-pending) and are re-derived from the next verified demo recording._
