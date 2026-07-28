# UI Test Results (merged)

**Date:** 2026-07-28
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 9/9 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-12-evidence/J-01-verify.png |
| UT-J-02 | Coverage + explicit bar top-up over the universe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-12-evidence/J-02-verify.png |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-12-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-12-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-12-evidence/J-05-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-12-evidence/J-07-verify.png |
| UT-J-08 | Every ranked briefing row names the bar its distance was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-12-evidence/J-08-verify.png |
| UT-J-06 | MCP contract v3 — 17 read-only tools | regression | P1 | Per goal.md: "the MCP server advertises exactly 17 tools; `desk_universe`/`desk_screen` outputs are proven byte-identical to their curl equivalents (empty AND populated fixture states); `get_endpoint` on `/research/desk/screen` proxies verbatim; the MCP suite is green." Tagged `(Keyless; automated.)` in goal.md — no browser surface. | Ran `tests/test_mcp_server.py` live (not merely cited): **35 passed, 0 failed** in 7.25s. `EXPECTED_TOOLS` read directly from source = exactly 17 names incl. `desk_universe`/`desk_screen`. Confirmed by name: `test_advertised_tool_set_is_exactly_capability_6` (17-tool count), `test_desk_universe_tool_byte_identical_on_the_honest_empty_state` + `_on_a_populated_state`, `test_desk_screen_tool_byte_identical_on_the_honest_empty_state` + `_on_a_populated_state`, `test_get_endpoint_desk_screen_date_query_proxies_verbatim`, `test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool` (also re-confirms `len(TOOL_NAMES)==17`), `test_stdio_session_end_to_end` (spawns the REAL `python -m app.mcp` subprocess over stdio — the actual production entry point). All passed. Confirmed via `goto`-and-read-nav that no dedicated MCP page exists in the UI (nav = Cockpit/Structure/Desk only) — consistent with goal.md's own "no browser surface" framing for this journey. | PASS | `reports/qa/goal-desk-iter-12-evidence/UT-J-06-nav-context.png` (supplementary nav context only — this journey's real evidence is the pytest run, quoted above and in the Environment section) |
| UT-J-09 | Every top-up run leaves an append-only record — standalone browser-qa screenshots for both states | happy-path | P1 | Per iter-12's IN SCOPE: standalone browser-qa-agent screenshots exist for (a) the honest empty "No top-up runs recorded yet." state and (b) the populated Top-up Runs section (attempted-of-total, per-outcome counts, a failed pair's own detail), on a scoped rig, never ambient. | (a) Navigated `:3302/desk` (fresh scoped, genuinely empty rig) — DOM text extraction showed exactly "No top-up runs recorded yet." under the "Top-up Runs" heading; screenshot legibly shows the empty-state panel (circle-slash icon + the exact text) with the Run Screen/Top-up buttons visible-but-unclicked above it. (b) Navigated `:3301/desk` (dev's populated rig) — DOM text + screenshot both show the 3-row table (`done 404/404`, `cancelled 3/404`, `done 404/404`) and "Latest run — 2026-07-28 · topup-2026-07-28-6b40a8029a75 — state: done, 404 of 404 pairs attempted, 0 reused · 403 fetched · 1 failed" with "Failed pairs (1): AAPL 1h — no data for that window" all legible in one image; cross-checked byte-for-byte against a live `curl :8301/research/desk/topup/runs`. Neither rig had "Top-up"/"Run Screen" clicked. | PASS | `reports/qa/goal-desk-iter-12-evidence/UT-J-09-empty-topup-section.png` (+ `UT-J-09-empty-fullpage.png`), `reports/qa/goal-desk-iter-12-evidence/UT-J-09-populated-topup-section.png` (+ `UT-J-09-populated.png`) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-28

