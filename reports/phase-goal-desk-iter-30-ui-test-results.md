# UI Test Results (merged)

**Date:** 2026-07-31
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 11/11 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-30-evidence/J-01-verify.png |
| UT-J-02 | Coverage + explicit bar top-up over the universe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-30-evidence/J-02-verify.png |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-30-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-30-evidence/J-04-verify.png |
| UT-J-06 | MCP contract v3 — 17 read-only tools | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-30-evidence/J-06-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-30-evidence/J-07-verify.png |
| UT-J-09 | Every top-up run leaves an append-only record of what it attempted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-30-evidence/J-09-verify.png |
| UT-J-10 | The coverage the briefing shows is the coverage the frozen store can prove | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-30-evidence/J-10-verify.png |
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-30-evidence/J-12-verify.png |
| UT-J-16 | The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-30-evidence/J-16-verify.png |
| UT-J-18 | Every screen run leaves an append-only record of what it attempted — and a re-run under identical pins says so before it walks | happy-path | P1 | On a freshly-provisioned scoped rig with zero prior screen-run records, `/desk` shows the honest `data-testid="desk-screen-runs-empty"` "No screen runs recorded yet." before any Run Screen click; on the ambient rig, a completed full-walk row shows `101 / 101` and a reused run's own table row states "no walk was performed"; golden replay holds | Scoped rig (backend :8302 `TAPEOLOGY_DESK_UNIVERSE_DIR`=fresh empty dir, frontend :3302) loaded `/desk` as the FIRST action — `GET /research/desk/screen/runs` returned `{"runs":[],"latest":null,"integrity_errors":[]}`, DOM confirmed `data-testid="desk-screen-runs-empty"` with exact text "No screen runs recorded yet.", 1440×900 viewport with no horizontal scroll (scrollWidth=clientWidth=1425). Ambient rig (:3301) regression-checked via DOM read: `desk-screen-runs-table` shows one `101 / 101` full-walk row (screen-2026-07-31-c169546856c7) and two reused rows reading "reused screen-2026-07-31-c169546856c7 — no walk was performed", same screen_id both times (no divergence). Updated golden script `runs/goal-session-desk/journey-scripts/J-18.json` to assert these stable table substrings instead of the prior date/id-pinned "latest run" text (closing iter-29 audit finding T1); replayed clean via `demo_runner.py --mode verify` against the ambient rig (PASS). Scoped rig torn down at end of dispatch. | PASS | `reports/qa/goal-desk-iter-30-evidence/J-18-empty-state.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-31

