# UI Test Results (merged)

**Date:** 2026-07-28
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-10-evidence/J-01-verify.png |
| UT-J-02 | Coverage + explicit bar top-up over the universe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-10-evidence/J-02-verify.png |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-10-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-10-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-10-evidence/J-05-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-10-evidence/J-07-verify.png |
| UT-J-08 | Every ranked briefing row names the bar its distance was measured from | smoke | P1 | `/desk` (default/latest view) legibly shows one ranked row with `basis_age_days <= 2` and one with `basis_age_days >= 10`, both in a single screenshot | Live browser load of `/desk` on the scoped rig rendered the new `screen-2026-07-25` snapshot (63 rows/38 skipped); rows 0-3/5-11 (BRK-B, DHR, HD, IBM, CRM, AMT, HONA, LOW, LIN, CAT, COST...) read `basis 2026-07-23 · 2 d before as-of` and row 4 (NFLX) reads `basis 2026-07-13 · 12 d before as-of` — both legible together, no scrolling needed | PASS | `reports/qa/goal-desk-iter-10-evidence/UT-J-08-result.png` |
| UT-J-06 | MCP contract v3 — 17 read-only tools | contract | P1 | MCP server advertises exactly 17 read-only tools incl. `desk_universe`/`desk_screen`; byte-identical GET-proxy behavior; honest-error on an unreachable backend (no fabrication) | This session's live tool roster = exactly 17 `mcp__tapeology__*` tools matching `test_mcp_server.py`'s `EXPECTED_TOOLS` tuple verbatim (name-for-name); a fresh, independent re-run of `tests/test_mcp_server.py` (not reused from any other lane) = **34/34 passed**; a live call to `mcp__tapeology__ui_route_map` against the (deliberately not-started this iteration) ambient backend returned an honest `ConnectError... no cached or fabricated data is served` — correct read-only, no-fallback behavior, not a defect | PASS | N/A — no browser surface (see Note below); evidence = pytest transcript + live tool-call transcript, both reproduced in this report |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-28

