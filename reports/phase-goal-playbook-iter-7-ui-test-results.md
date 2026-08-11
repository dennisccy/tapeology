# UI Test Results (merged)

**Date:** 2026-08-11
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 7/7 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The signal contract — opening-range breaks end to end, lookahead-clean and pre-registered | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-7-evidence/J-01-verify.png |
| UT-J-02 | Every signal measured — the rail's own conventions, anchored at the trigger bar | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-7-evidence/J-02-verify.png |
| UT-J-03 | The Playbook lands on /desk | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-7-evidence/J-03-verify.png |
| UT-J-04 | The continuation family — JBE, DBI, cup-and-handle | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-7-evidence/J-04-verify.png |
| UT-J-05 | The climax family — capitulation entry, euphoria marker | happy-path | P1 | A capitulation signal and a marker-decorated signal legible on the fixture rig | `/desk` Playbook Signals for date `2026-06-22` shows `capitulation:long` (DECOR) row; expanded detail reads "1 approach attempt(s) · 0 bar(s) to close · **euphoria recent**" — the capitulation signal is itself the marker-decorated row (euphoria fired earlier in the same session, decorates the later capitulation per spec §3.5) | PASS | `reports/qa/goal-playbook-iter-7-evidence/UT-J-05-result.png` |
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-7-evidence/J-10-verify.png |
| UT-J-07 | The back-scan — every recorded session, resumable and append-only | happy-path | P1 | Plan preview over a From/To range + a completed fixture scan's run row with per-outcome counts legible | Typed From=`2026-06-22`, To=`2026-06-24` into the Backscan panel → plan preview read "3 dates planned · 3 missing at the current signature" listing all 3 dates; clicked "Run Backscan" → run completed and the runs table shows row `2026-06-22 → 2026-06-24 · done · 0 reused · 3 recorded · 0 refused · 0 failed` — all four per-outcome counts legible | PASS | `reports/qa/goal-playbook-iter-7-evidence/UT-J-07-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-11


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-06 | J-06 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
