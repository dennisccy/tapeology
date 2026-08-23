# UI Test Results (merged)

**Date:** 2026-08-23
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-23-evidence/J-01-verify.png |
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-23-evidence/J-02-verify.png |
| UT-J-03 | Structure × flow — the join that never looks ahead | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-23-evidence/J-03-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-23-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-23-evidence/J-05-verify.png |
| UT-J-08 | The surface and MCP v6 — the funnel is visible | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-23-evidence/J-08-verify.png |
| UT-J-10 | The kept product stands — traps armed, sentinel green | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-23-evidence/J-10-verify.png |
| UT-J-06 | The recorder and the Vault — new tape, sealed at birth | happy-path | P1 | `/desk` Microscope Readiness section shows `sealed_tranche.by_universe["rapid-microscope-j06-starter"]` as one opaque-pool aggregate (80 shards/80 symbol-days, matching `joinable_corpus.withheld_excluded: 80`); Validation Vault section shows 21 sealed shard rows keyed by opaque surrogate id with rule/vault-secret commitments (not raw values); no symbol/session-date for any withheld/sealed shard anywhere in the DOM; legacy 12 symbol-days still `exploratory` | Both sections rendered exactly this, against a backend instance pointed at the real `apps/backend/.data/datasets` store (80/80 aggregate confirmed; 21 sealed vault rows confirmed, every non-identity column reading `sealed — opaque`; legacy 18-dataset/12-symbol-day table intact and unchanged; only sha256 commitments shown for rule/vault-secret, never raw values) | PASS | `reports/qa/goal-rapid-microscope-iter-23-evidence/J-06-result.png`, `reports/qa/goal-rapid-microscope-iter-23-evidence/J-06-vault-shards.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-23


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | J-07 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-09 | J-09 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
