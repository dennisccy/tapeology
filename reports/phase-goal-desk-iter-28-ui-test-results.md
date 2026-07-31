# UI Test Results (merged)

**Date:** 2026-07-31
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 5/5 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-28-evidence/J-04-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-28-evidence/J-07-verify.png |
| UT-J-09 | Every top-up run leaves an append-only record of what it attempted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-28-evidence/J-09-verify.png |
| UT-J-16 | The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-28-evidence/J-16-verify.png |
| UT-J-17 | A top-up asks the vendor only for the bars the frozen store cannot already prove | regression | P1 | `/desk` Top-up Runs section renders the four-outcome counts line, a window-basis disclosure line, and a "Failed pairs (N)" list with each pair's own detail; ranked briefing table (J-16) renders unaffected, no horizontal scroll at 1440×900 | On the ambient rig (`:3301`/`:8301`), `desk-topup-run-latest-counts` reads "0 reused · 390 fetched · 0 unchanged · 14 failed", `desk-topup-run-latest-window-basis` reads "window basis not recorded in this run" (honest legacy-absence disclosure — this run predates the per-pair window fields), `desk-topup-run-latest-failed` lists "Failed pairs (14)" with each pair's own detail text and its own "window basis not recorded in this run" per-pair note; ranked table present (115 rows), `scrollWidth` (1425px) == `clientWidth` (1425px) at 1440×900 — no horizontal scroll | PASS | `reports/qa/goal-desk-iter-28-evidence/J-17-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-31

