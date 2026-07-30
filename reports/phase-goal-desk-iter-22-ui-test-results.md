# UI Test Results (merged)

**Date:** 2026-07-30
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 6/6 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-22-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-22-evidence/J-05-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-22-evidence/J-07-verify.png |
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-22-evidence/J-12-verify.png |
| UT-J-13 | Every ranked briefing row states the price its wall sits at and the close it was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-22-evidence/J-13-verify.png |
| UT-J-14 | Every ranked briefing row states where the nearest wall on the OTHER side of price sits (this iteration: the owed native-tooltip photograph) | evidence-capture | P1 | `/desk` opposite column shows a near (≤25bps) and far (>1000bps) opposite wall legible in the same screenshot; the row's native `title` tooltip (`bands by class A n · B n · C n · unclassified n`) is photographed via the owner-approved headed qa-rig (T-10a), exits 0, contains the literal substring "bands by class", and matches the DOM-read title and the on-disk `bands_by_class` field; the rig's negative guard is re-verified live | All of the above confirmed live against the ambient rig (`:3301`/`:8301`), which already serves `screen-2026-07-20-ca185294a384` as its latest screen | PASS | `reports/qa/goal-desk-iter-22-evidence/J-14-desk-opposite-column.png`, `reports/qa/goal-desk-iter-22-evidence/J-14-tooltip.png`, `reports/qa/goal-desk-iter-22-evidence/J-14-tooltip-crop.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-30

