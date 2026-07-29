# UI Test Results (merged)

**Date:** 2026-07-29
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 9/10 journeys passed (1 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-14-evidence/J-01-verify.png |
| UT-J-02 | Coverage + explicit bar top-up over the universe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-14-evidence/J-02-verify.png |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-14-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-14-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-14-evidence/J-05-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-14-evidence/J-07-verify.png |
| UT-J-08 | Every ranked briefing row names the bar its distance was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-14-evidence/J-08-verify.png |
| UT-J-09 | Every top-up run leaves an append-only record of what it attempted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-14-evidence/J-09-verify.png |
| UT-J-10 | The coverage the briefing shows is the coverage the frozen store can prove | happy-path | P1 | Honest empty reconciliation state + dark AAPL `1d` badge captured FIRST; then one reconciliation run + one new screen run; then populated reconciliation detail + lit `1d` badge captured, both composite screenshots legible | Empty state captured first (`{"runs": [], "latest": null}` confirmed via API before any UI interaction); "Reconcile Index" clicked → run `reconcile-2026-07-29-74a66e4611a7` resolved `state: done`, `rows_indexed` 345→369, 24 AAPL `1d` unindexed-series drift entries repaired to zero; "Run Screen" clicked → NEW append-only snapshot `screen-2026-07-29-e7e5de9a5815` recorded (not a reuse), AAPL `1d` badge now `data-has-bars="true"`; prior screen `screen-2026-07-27-073795dff864` remained present and distinct in Screen History (unchanged `bar_store_signature`) | PASS | `reports/qa/goal-desk-iter-14-evidence/UT-J-10-TC17-empty-before.png`, `reports/qa/goal-desk-iter-14-evidence/UT-J-10-TC18-populated-after.png` |
| UT-J-06 | MCP contract v3 — 17 read-only tools | happy-path | P1 | N/A — journey's own acceptance text is explicitly "(Keyless; automated.)"; goal.md's "Testing Requirements" line states "J-06 by its 17-tool contract test (no browser surface)" | No UI surface exists for this journey; nothing to drive in a browser | SKIP | none |

## Skipped Tests

### UT-J-06 — MCP contract v3 — 17 read-only tools

**Verdict:** SKIPPED
**Reason:** No UI surface exists for this journey; nothing to drive in a browser

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-29

