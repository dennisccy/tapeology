# UI Test Results (merged)

**Date:** 2026-08-12
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The signal contract — opening-range breaks end to end, lookahead-clean and pre-registered | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-12-evidence/J-01-verify.png |
| UT-J-02 | Every signal measured — the rail's own conventions, anchored at the trigger bar | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-12-evidence/J-02-verify.png |
| UT-J-03 | The Playbook lands on /desk | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-12-evidence/J-03-verify.png |
| UT-J-07 | The back-scan — every recorded session, resumable and append-only | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-12-evidence/J-07-verify.png |
| UT-J-08 | The evidence view — distributions beside the null, min-n honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-12-evidence/J-08-verify.png |
| UT-J-09 | MCP contract v4 — 20 read-only tools | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-12-evidence/J-09-verify.png |
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-12-evidence/J-10-verify.png |
| UT-J-11 | Every evidence cell states the basis of its own n | happy-path | P1 | On `/desk`, the Playbook Evidence section shows a new basis line beside "Built from signature:" and at least one visible cell row shows `n_unmeasured > 0` beside its own `n` | Basis line renders exactly `GET /research/desk/playbook/evidence`'s `basis` block, byte-identical to the raw API response; cell `open_high_break / long / 1m` renders `n=0, n_unmeasured=15` (signal) and `n_baseline=0, n_unmeasured=11` (baseline), also byte-identical to the API | PASS | `reports/qa/goal-playbook-iter-12-evidence/UT-J-11-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-12

