# UI Test Results (merged)

**Date:** 2026-07-31
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 17/18 journeys passed (1 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-29-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-29-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-29-evidence/J-05-verify.png |
| UT-J-06 | MCP contract v3 — 17 read-only tools | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-29-evidence/J-06-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-29-evidence/J-07-verify.png |
| UT-J-09 | Every top-up run leaves an append-only record of what it attempted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-29-evidence/J-09-verify.png |
| UT-J-10 | The coverage the briefing shows is the coverage the frozen store can prove | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-29-evidence/J-10-verify.png |
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-29-evidence/J-12-verify.png |
| UT-J-16 | The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-29-evidence/J-16-verify.png |
| UT-J-17 | A top-up asks the vendor only for the bars the frozen store cannot already prove | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-29-evidence/J-17-verify.png |
| UT-01 | `/desk` loads, Screen Runs panel present | smoke | P1 | Fourth panel "Screen Runs" visible after Index Reconciliation, no blank/error, empty or table state, no h-scroll, no console errors | Panel present with `data-testid="desk-screen-runs-empty"` showing exact text "No screen runs recorded yet."; no h-scroll (scrollWidth=clientWidth=1425 at 1440 viewport); console clean (only React DevTools info line) | PASS | `reports/qa/goal-desk-iter-29-evidence/UT-01-result.png` |
| UT-02 | Freshly-completed run appears in ledger | happy-path | P1 | New row in table, date=today UTC, state=done, attempted/total equal (e.g. 101/101), produced=screen id; Latest-run detail block with heading/state/elapsed/ranked-skipped counts | Real "Run Screen" click walked all 101 members (started 01:58:48Z, finished 02:00:29Z, ~1m41s). Row: `2026-07-31 · screenrun-2026-07-31-725c4ec2bfcd · done · 101 / 101 · screen-2026-07-31-c169546856c7`. Detail block: "Latest run — 2026-07-31 · screenrun-2026-07-31-725c4ec2bfcd", "state: done", "101 of 101 members attempted", "1m 40s elapsed", "screen-2026-07-31-c169546856c7", "100 ranked · 0 skipped (no bars) · 1 skipped (no basis)" | PASS | `reports/qa/goal-desk-iter-29-evidence/UT-02-result.png` |
| UT-03 | Duplicate click short-circuits, recorded as reused | happy-path | P1 | Second click resolves much faster, progress counter does not climb; new row "0 / total"; produced = "reused `<id>` — no walk was performed" with id identical to UT-02's; latest-detail outcome line matches; counts line (if shown) not a fabricated re-count | Second run: started/finished 02:01:55.4866Z/.5010Z (~15ms vs ~1m41s). New row: `done · 0 / 101 · reused screen-2026-07-31-c169546856c7 — no walk was performed` (same screen id as UT-02). Latest-detail outcome (`desk-screen-run-latest-outcome`) text byte-identical. Counts line DID render (state===done) but read "0 ranked · 0 skipped (no bars) · 0 skipped (no basis)" — honest zeros, not the original walk's 100/0/1, i.e. not a fabricated re-count | PASS | `reports/qa/goal-desk-iter-29-evidence/UT-03-result.png` |
| UT-04 | Empty state never fabricates outcome | validation | P2 | Exact text "No screen runs recorded yet." in `desk-screen-runs-empty`; no table; no latest-run detail; nothing invented | Verified against the genuinely-empty ambient store (`GET /research/desk/screen/runs` returned `{"runs":[],"latest":null,"integrity_errors":[]}` before any run this session — confirmed by curl before triggering UT-02, and independently by DOM eval: `emptyText` exact match, `tablePresent:false`, `detailPresent:false`) | PASS | none — see note below |
| UT-05 | Failed run shows verbatim error + member | error | P2 | Failed row's produced column reads "nothing recorded"; latest-detail failure block shows raising member (monospace) + " — " + verbatim error; counts line absent | SKIPPED — see Skipped Tests section | SKIP | none |
| UT-06 | Ranked table unchanged | regression | P1 | Columns/layout unchanged from pre-iteration; row drill-in still navigates to `/structure`; no h-scroll at 1440x900 | Header row unchanged: rank/symbol/side/class/distance/score/coverage/tick evidence/basis/history/band/opposite/levels (13 cols, matches pre-iteration shape). Clicked row's own `data-testid="desk-row-drill-in"` anchor for BRK-B → navigated to `/structure?symbol=BRK-B&asof=2026-07-31T23%3A59%3A59Z`, confirmed via `window.location.href` and "Structure" heading. No h-scroll (1425/1425) | PASS | `reports/qa/goal-desk-iter-29-evidence/UT-06-result.png` |
| UT-07 | Top-up Runs / Index Reconciliation unaffected | regression | P1 | Both sibling panels render as before; no screen-run text leaks into them; section order: Screen History → Run controls → Top-up Runs → Index Reconciliation → Screen Runs (last) | Top-up Runs latest-counts unchanged ("0 reused · 390 fetched · 0 unchanged · 14 failed"); DOM-scoped check confirmed neither Top-up Runs nor Index Reconciliation section contains any `screenrun-` text. `h2` order confirmed: Provenance, Briefing, Skipped Members, Screen History, Run Screen / Top-up / Reconcile Index, Top-up Runs, Index Reconciliation, Screen Runs (last) | PASS | `reports/qa/goal-desk-iter-29-evidence/UT-07-result.png` |
| UT-08 | Screen Runs panel discoverable | ux | P2 | Reached within one scroll from Index Reconciliation; heading style/capitalization matches siblings; no new nav | Reconcile section bottom=1391.5px, Screen Runs section top=1415.5px (one continuous scroll). `className="mt-6"` identical across Top-up Runs / Index Reconciliation / Screen Runs sections; heading class (`text-xs font-semibold uppercase tracking-wider text-slate-500`) identical across all three. Nav bar unchanged (Cockpit / Structure / Desk only) | PASS | `reports/qa/goal-desk-iter-29-evidence/UT-08-result.png` |

## Skipped Tests

### UT-05 — Failed run shows verbatim error + member

**Verdict:** SKIPPED
**Reason:** SKIPPED — see Skipped Tests section

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-31

