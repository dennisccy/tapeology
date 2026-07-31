# UI Test Results (merged)

**Date:** 2026-07-31
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 10/10 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-36-evidence/J-01-verify.png |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-36-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-36-evidence/J-04-verify.png |
| UT-J-06 | MCP contract v3 — 17 read-only tools | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-36-evidence/J-06-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-36-evidence/J-07-verify.png |
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-36-evidence/J-12-verify.png |
| UT-J-16 | The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-36-evidence/J-16-verify.png |
| UT-J-18 | Every screen run leaves an append-only record of what it attempted — and a re-run under identical pins says so before it walks | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-36-evidence/J-18-verify.png |
| UT-J-20 | Every recorded screen states how it differs from the screen recorded before it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-36-evidence/J-20-verify.png |
| UT-J-21 | The desk says, before the click, whether a screen is already recorded under the pins a run would resolve now | happy-path | P1 | `/desk` shows, before any click, whether a screen run right now would reuse an already-recorded snapshot or walk fresh — for the displayed screen's own date (Provenance panel) and for today (Run Screen control) — with an honest empty state when no universe is registered; three states (match, differ, empty) each browser-verified with a screenshot at 1440×900, no horizontal scroll, ranked table unchanged from J-16 | All three states rendered exactly as specified. Match (fixture-scoped rig): Provenance panel's resolved-pins block read "A screen is recorded under these exact pins — screen-2026-06-22-09cf660a4125, recorded 2026-07-31T13:22:41.106918Z." Differ (ambient rig, read-only): both the Provenance panel and the Run-Screen-control line read "No screen is recorded under the pins that resolve right now for this date — a run would walk 101 members." / "No screen is recorded under the pins that resolve for today — a run would walk 101 members." Empty (fixture-scoped rig, before any registration): "No universe snapshot is registered — whether a run today would reuse a recorded screen cannot be named." rendered beside the Run Screen button. `scrollWidth == clientWidth` (1425px) confirmed on both rig captures. All 21 stored golden replay scripts (J-01..J-21) replay green against the ambient rig. | PASS | `reports/qa/goal-desk-iter-36-evidence/J-21-match.png`, `reports/qa/goal-desk-iter-36-evidence/J-21-differ.png`, `reports/qa/goal-desk-iter-36-evidence/J-21-empty.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-31

