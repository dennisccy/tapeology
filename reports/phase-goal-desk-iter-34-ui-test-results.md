# UI Test Results (merged)

**Date:** 2026-07-31
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 10/12 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-34-evidence/J-04-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-34-evidence/J-07-verify.png |
| UT-J-09 | Every top-up run leaves an append-only record of what it attempted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-34-evidence/J-09-verify.png |
| UT-J-16 | The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-34-evidence/J-16-verify.png |
| UT-J-17 | A top-up asks the vendor only for the bars the frozen store cannot already prove | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-34-evidence/J-17-verify.png |
| UT-01 | `/desk` Top-up Runs panel loads | smoke | P1 | Page renders, table with 5 named columns visible, latest-run detail heading visible, no console errors | Page rendered; `desk-topup-runs-table` had headers exactly `date, run, state, attempted / total, universe snapshot`; `desk-topup-run-latest-detail` heading "Latest run — 2026-07-31 · topup-2026-07-31-8fb5c9a1f737" visible; console showed only the React DevTools info line | PASS | `reports/qa/goal-desk-iter-34-evidence/UT-01-result.png` |
| UT-02 | Reach line and earlier list never share a day | happy-path | P1 | No earlier-row's printed date equals the newest-reach day; ambient run rows all print `2026-07-27` | Reach line read "newest recorded reach 2026-07-30 · 303 pairs reach it"; all 20 rendered earlier rows printed `2026-07-27`; a DOM check (`innerText.indexOf('2026-07-30')` over every earlier row) confirmed 0 matches | PASS | `reports/qa/goal-desk-iter-34-evidence/UT-02-result.png` |
| UT-03 | Cap disclosure shows "showing 20 of N" | happy-path | P1 | "showing 20 of 101" visible below the "Pairs recorded earlier (101)" heading; exactly 20 rows rendered | Heading read "Pairs recorded earlier (101)"; disclosure paragraph read exactly "showing 20 of 101"; `querySelectorAll` over `desk-topup-run-latest-reach-earlier-row` returned exactly 20 elements | PASS | `reports/qa/goal-desk-iter-34-evidence/UT-03-result.png` |
| UT-04 | No disclosure when true total ≤ 20 | validation | P2 | Live branch not exercisable on ambient run (true total 101 > 20, documented environment limitation); fallback pytest tests pass | Ran `pytest tests/test_desk_topup_library_reach_guard.py -k cap -v` — 4 passed, including `test_topup_library_reach_caps_the_earlier_list_and_preserves_the_true_total` and its render-wiring/seeded-violation counterparts | PASS (fallback) | none (no live screenshot possible — see note below) |
| UT-05 | Legacy run still shows honest fallback text | error | P2 | No qualifying legacy run on ambient store (documented environment limitation); fallback pytest test passes | Ran `pytest tests/test_desk_topup_library_reach_guard.py -k lacks_store_frozen_through_after -v` — 1 passed (`test_topup_library_reach_returns_null_when_any_outcome_lacks_store_frozen_through_after`) | PASS (fallback) | none (no live screenshot possible — see note below) |
| UT-06 | Summary table + adjacent pages unaffected | regression | P1 | Top-up Runs table keeps exactly its 5 original columns; Cockpit and Structure pages load without errors | Confirmed table headers unchanged (`date, run, state, attempted / total, universe snapshot`); navigated to `/` (Cockpit) — loaded, no console errors; navigated to `/structure` — "Structure" heading rendered, no console errors | PASS | `reports/qa/goal-desk-iter-34-evidence/UT-06-result.png` |
| UT-07 | Disclosure sentence is plain description | ux | P2 | Sentence contains only "showing" + two numbers, no advice/urgency language; styling matches existing muted fallback text | Sentence text: "showing 20 of 101" (nothing else); `className="mb-1 text-xs text-slate-400"` on the `<p>`, matching the sibling fallback line's `className="text-xs text-slate-400"` — same font size/color, no new badge/icon/color | PASS | `reports/qa/goal-desk-iter-34-evidence/UT-07-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-31

