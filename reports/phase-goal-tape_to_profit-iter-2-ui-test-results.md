# UI Test Results (merged)

**Date:** 2026-07-03
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 3/3 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | A read-only MCP server exposes the product over the canonical API | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-2-evidence/J-01-verify.png |
| UT-J-08 | The existing product is unchanged (regression sentinel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-2-evidence/J-08-verify.png |
| UT-J-02 | Historical tape datasets persist and replay byte-identically (train/hold-out registry) | functional | P1 | `GET /research/datasets` flips from the iter-0 baseline 404 to live 200 JSON; record/register/re-tag-refusal/checksum-integrity/404 behavior all match the goal.md acceptance line | `GET /research/datasets` confirmed 200 (was 404 at iter-0); recorded 3 real datasets via genuine browser `fetch()` calls (train ×2, holdout ×1) with symbol/UTC window/feed/event-counts/checksum all populated; re-tag attempt on identical content → 409 with explicit frozen-tag message; `sim` source_kind → 422; corrupted-file integrity check → explicit 500 + `integrity_errors` row while healthy rows kept serving; restored file → clean; unknown id → 404; live SIM-BUYER watch/stop cycle wrote zero dataset files (byte-identical directory before/after) | PASS | `reports/qa/goal-tape_to_profit-iter-2-evidence/J-02-01..07-*.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-03

