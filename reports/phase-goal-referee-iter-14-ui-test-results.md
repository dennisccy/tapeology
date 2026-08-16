# UI Test Results (merged)

**Date:** 2026-08-16
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | The registry — pre-registration with an immutable boundary | regression | P1 | Referee Registry panel expand renders the S-1 hypothesis row (`historical-exploration` origin, `2026-08-15` boundary, `active` status) | Live-driven re-check (fresh nav, timed click→text-found ≈3.06s, well inside the golden's 12s budget) confirms `S-1 / capitulation:long / 2026-08-15 / historical-exploration / active / 0 / 12 / 1 / 1 discovery (exploratory)` all render correctly | PASS | `reports/qa/goal-referee-iter-14-evidence/UT-J-05-result.png` |
| UT-J-07 | The starter family — historical exploration becomes registered questions | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-14-evidence/J-07-verify.png |
| UT-J-09 | The Referee on /desk + MCP contract v5 — 22 read-only tools | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-14-evidence/J-09-verify.png |
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-14-evidence/J-10-verify.png |
| UT-J-11 | The accrual projection states its own basis — the wait, measured in recorded sessions | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-14-evidence/J-11-verify.png |
| UT-J-01 | The era transition stands — reconciliation made testable | keyless | P1 | `apps/backend/tests/test_referee_guards.py` run to completion, all collected tests pass (iter-13 live count: 19) | `19 passed in 0.16s`, 0 failures | PASS | none (backend-only journey, `(Keyless; automated.)` per goal.md — no browser surface exists) |
| UT-J-02 | The evidence contract — two families, one observation shape | keyless | P1 | `apps/backend/tests/test_referee_evidence.py` run to completion, all collected tests pass (iter-13 live count: 29) | `29 passed in 2.48s`, 0 failures | PASS | none (backend-only journey, `(Keyless; automated.)` per goal.md — no browser surface exists) |
| UT-J-12 | The readiness fold gets its reader — why a family cannot speak, visible on the desk | evidence | P1 | An in-frame, legible capture of the `referee-evidence-strategy-block` element (tick-gate sentence + every basis-caveats entry), checksum-distinct from iter-13's `J-12-seeded-rig-result.png`, `J-12-empty-corpus-result.png`, and `J-05-result.png` | Element captured with both `referee-evidence-strategy-tick-gate` and `referee-evidence-strategy-basis-caveats` fully legible; SHA-256 confirmed distinct from all three named iter-13 files | PASS | `reports/qa/goal-referee-iter-14-evidence/J-12-strategy-block-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-16

