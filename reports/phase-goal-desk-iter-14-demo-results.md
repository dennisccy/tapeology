# Demo Results — goal-desk-iter-14

**Demo Verdict:** RECORDED_WITH_NOTES
**Date:** 2026-07-29
**Frontend URL:** http://localhost:3301

## Captured Steps

| Step | Title | Journey | New | Screenshot |
|------|-------|---------|-----|------------|
| 01 | Open the desk | J-04 |  | reports/demo/goal-desk-iter-14/step-01.png |
| 02 | See the index reconciliation panel before any run | J-10 | yes | reports/demo/goal-desk-iter-14/step-02.png |
| 03 | Click Reconcile Index to repair the internal list | J-10 | yes | reports/demo/goal-desk-iter-14/step-03.png |
| 04 | Read the repair results | J-10 | yes | reports/demo/goal-desk-iter-14/step-04.png |
| 05 | Run a fresh screen to capture the fixed coverage | J-10 | yes | reports/demo/goal-desk-iter-14/step-05.png |
| 06 | See the coverage badge now lit | J-10 | yes | reports/demo/goal-desk-iter-14/step-06.png |
| 07 | Check that older records stayed unchanged | J-10 | yes | reports/demo/goal-desk-iter-14/step-07.png |
| 08 | Coverage is now independently verifiable | J-10 | yes | reports/demo/goal-desk-iter-14/step-08.png |

## Soft notes

- Step 02 — expected "No reconciliation run recorded yet." did not appear; recorded anyway.
- Step 05 — expected "Recorded a new snapshot" did not appear; recorded anyway.
- Step 06 — expected {'css': "[data-testid='desk-coverage-badge'][data-has-bars='true']"} did not appear; recorded anyway.

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (record)
- **Demo mode:** record
