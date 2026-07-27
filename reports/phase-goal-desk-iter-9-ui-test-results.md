# UI Test Results (merged)

**Date:** 2026-07-27
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 17/17 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-9-evidence/J-01-verify.png |
| UT-J-02 | Coverage + explicit bar top-up over the universe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-9-evidence/J-02-verify.png |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-9-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-9-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-9-evidence/J-05-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-9-evidence/J-07-verify.png |
| UT-01 | `/desk` loads with the new 8-column basis header | smoke | P1 | 8-column header ending `...basis`; no error panel; no layout break | Header read exactly `symbol, side, class, distance, score, coverage, tick evidence, basis`; no amber error panel at any point; all panels visible, no overlap | PASS | `reports/qa/goal-desk-iter-9-evidence/UT-01-loaded.png` |
| UT-02 | Operator runs a new screen and basis column populates with real data | happy-path | P1 | Outcome line + real `basis YYYY-MM-DD · N d before as-of` on every row + new history row | Outcome "Recorded a new snapshot — screen-2026-07-27-936543601e75"; all 63 ranked rows show the exact pattern; new `2026-07-27` row present in Screen History (see note: appears at bottom, not top — pre-existing, out of scope) | PASS | `reports/qa/goal-desk-iter-9-evidence/UT-02-screen-history-table-order.png` |
| UT-03 | Fresh and stale basis ages distinguishable at a glance | happy-path | P1 | Visibly different min/max day-counts; stale ≥10d; documented allowance if no row ≤2d | AAPL 3d (freshest) vs NFLX/META/NVDA 14d (stalest); 11-day spread; allowance applied and disclosed (see note) | PASS | `reports/qa/goal-desk-iter-9-evidence/UT-03-fresh-vs-stale.png` |
| UT-04 | Row hover tooltip discloses full-precision basis detail | happy-path | P1 | One consolidated tooltip; `distance → score → basis (full ISO ts) → coverage` order; per-row distinct | Anchor `title` verified directly: NFLX = `distance 0 bps · score 69 · basis 2026-07-13T04:00:00.000000Z (14 d before as-of) · 1h window last requested: never ...`; AAPL shows its own distinct values in the same order | PASS | verified via DOM `title` attribute (see notes — native popup not screenshot-capturable in this browser build) |
| UT-05 | Legacy screen rows show honest "not recorded" fallback | error | P2 | Every basis cell + tooltip segment reads exact fallback text; no crash | All 10 rows of the `2026-07-25` snapshot read exactly "basis not recorded in this snapshot"; tooltip segment matches; rest of row renders normally | PASS | `reports/qa/goal-desk-iter-9-evidence/UT-05-legacy-fallback.png` |
| UT-06 | Screen History drill-through consistent + "Latest" reverts cleanly | regression | P2 | Banner disappears, real data returns; both legacy screens show identical fallback; same component both views | "Latest" click removed banner and restored real basis data (63 rows); `2026-06-22` also showed fallback identically (10/10 rows); no crash at any step; basis stayed in 8th column position both views | PASS | `reports/qa/goal-desk-iter-9-evidence/UT-05-legacy-fallback.png` (start state) + DOM checks |
| UT-07 | Row click-through still works at the new basis cell's location | regression (elevated) | P1 | Click navigates to `/structure?symbol=...&asof=...`; anchor (not `<td>`) receives the pointer | Click on BRK-B's basis-cell text navigated to `/structure?symbol=BRK-B&asof=2026-07-27T23%3A59%3A59Z`; `document.elementFromPoint` at the cell's exact center resolved to the `<a data-testid="desk-row-drill-in">` anchor, not the `<td>` | PASS | `reports/qa/goal-desk-iter-9-evidence/UT-07-clickthrough-structure.png` |
| UT-08 | Other 7 ranked columns and skip-rows table unchanged | regression | P3 | 7 pre-existing columns unchanged; skip table has 4 columns, no basis; buttons unchanged | Skip table confirmed exactly `symbol, reason, coverage, tick evidence` (38 rows, no basis column, reason reads "no bars"); Run Screen/Top-up both present+enabled | PASS | `reports/qa/goal-desk-iter-9-evidence/UT-05-legacy-fallback.png`, `UT-03-fresh-vs-stale.png` |
| UT-09 | Basis copy is plain and descriptive, no advice/urgency language | ux | P3 | No urgency wording; identical styling fresh vs. stale; lowercase header | Text is purely `basis YYYY-MM-DD · N d before as-of`; computed style identical for a 3d row and a 14d row (`color: rgb(148,163,184)`, `font-weight: 400`, transparent background — no highlight); header reads lowercase "basis" | PASS | `reports/qa/goal-desk-iter-9-evidence/UT-03-fresh-vs-stale.png` |
| UT-10 | New basis information visible without extra navigation | ux | P3 | Visible on normal load; horizontal scroll contained in table's own container; full precision reachable via one hover | Fresh navigation to `/desk` showed the basis column immediately; at a 700px viewport the table's own `.overflow-x-auto` container scrolled independently while `document.body` showed zero horizontal overflow | PASS | `reports/qa/goal-desk-iter-9-evidence/UT-01-UT-10-fresh-load.png`, `UT-10-narrow-scroll.png` |
| UT-J-06 | MCP contract v3 — 17 read-only tools (goal-mode regression journey) | regression | P1 | Exactly 17 tools advertised; `desk_universe`/`desk_screen` byte-identical (empty+populated); `get_endpoint` proxies `?date=` verbatim; MCP suite green | Live tool roster for this session lists exactly 17 `mcp__tapeology__*` tools; `apps/backend/tests/test_mcp_server.py` run live: **34 passed, 0 failed** (7.49s), including `test_advertised_tool_set_is_exactly_capability_6` and the 5 desk_universe/desk_screen/get_endpoint byte-identity tests (see notes for a tooling caveat) | PASS | pytest output (below); no UI surface — no screenshot applicable |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-27

