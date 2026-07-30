# UI Test Results (merged)

**Date:** 2026-07-30
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 17/17 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-01-verify.png |
| UT-J-02 | Coverage + explicit bar top-up over the universe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-02-verify.png |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-05-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-07-verify.png |
| UT-J-08 | Every ranked briefing row names the bar its distance was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-08-verify.png |
| UT-J-09 | Every top-up run leaves an append-only record of what it attempted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-09-verify.png |
| UT-J-10 | The coverage the briefing shows is the coverage the frozen store can prove | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-10-verify.png |
| UT-J-11 | Every ranked briefing row states how much completed history its wall was measured over | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-11-verify.png |
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-12-verify.png |
| UT-J-13 | Every ranked briefing row states the price its wall sits at and the close it was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-13-verify.png |
| UT-J-14 | Every ranked briefing row states where the nearest wall on the OTHER side of price sits | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-14-verify.png |
| UT-J-15 | Every ranked briefing row states what its wall is actually made of | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-15-verify.png |
| UT-J-16 | The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-26-evidence/J-16-verify.png |
| UT-J-06 | MCP contract v3 — 17 read-only tools | regression/contract | P1 | MCP server advertises exactly 17 tools; `desk_universe`/`desk_screen` byte-identical to curl in empty AND populated states; `get_endpoint` proxies `/research/desk/screen` verbatim incl. honest errors; MCP suite green | 17 tools enumerated live; `desk_universe`/`desk_screen`/`get_endpoint` matched curl byte-for-byte empty AND populated (fixture-scoped rig); a real 404 proxied verbatim; `tests/test_mcp_server.py` 38 passed | PASS | see "J-06 verification transcript" below (no browser-observable acceptance state exists for this journey — see notes) |
| UT-J-17 | A top-up asks the vendor only for the bars the frozen store cannot already prove | full-stack/browser | P1 | On a fixture-scoped rig, `/desk`'s Top-up Runs section shows 4-outcome counts incl. ≥1 `unchanged`, a tail-vs-full-lookback line, and ≥1 failed pair's own `requested_window`, legible in one 1440×900 screenshot with no horizontal scroll; ranked table renders as J-16 shipped it | Real top-up on a fixture-scoped rig (never ambient `.data`) produced `0 reused · 6 fetched · 2 unchanged · 4 failed`, `2 pairs asked for a tail window · 10 pairs asked for the full lookback window`, and 4 failed `ZZZINVALIDXYZ` rows each showing `requested 2024-07-30 → 2026-07-30`; all rendered in one screenshot, `scrollWidth === clientWidth` (1425 < 1440, no horizontal scroll); a bonus real screen compute confirmed the J-16 ranked table (13 columns, 2 ranked + 1 skipped row) renders unchanged | PASS | `reports/qa/goal-desk-iter-26-evidence/J-17-topup-window-disclosure.png` (+ `J-17-ranked-table-regression-check.png`) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-30

