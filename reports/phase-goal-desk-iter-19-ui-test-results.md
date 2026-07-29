# UI Test Results (merged)

**Date:** 2026-07-29
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 9/10 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-19-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-19-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to `/structure` | regression / happy-path | P1 | Opening a past screen renders its recorded rows verbatim; clicking a row lands on `/structure` with symbol+as-of prefilled and the pinned AAPL 2026-06-22 wall region loaded; `/structure` with no params behaves exactly as shipped | All three sub-claims verified live in a real browser: 2026-06-22 history row rendered recorded rows verbatim; drill-in click navigated to `/structure?symbol=AAPL&asof=2026-06-22T23%3A59%3A59Z`, auto-loaded, and rendered both the 300.11–302.2 and 298.02–300.1001 Class A resistance bands; `/structure` with no query params showed the exact shipped empty-form default state | PASS | `reports/qa/goal-desk-iter-19-evidence/J-05-drillin-structure-aapl.png`, `reports/qa/goal-desk-iter-19-evidence/J-05-structure-no-params-default.png` |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-19-evidence/J-07-verify.png |
| UT-J-08 | Every ranked briefing row names the bar its distance was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-19-evidence/J-08-verify.png |
| UT-J-11 | Every ranked briefing row states how much completed history its wall was measured over | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-19-evidence/J-11-verify.png |
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-19-evidence/J-12-verify.png |
| UT-J-13 | Every ranked briefing row states the price its wall sits at and the close it was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-19-evidence/J-13-verify.png |
| UT-J-06 | MCP contract v3 — 17 read-only tools | regression / keyless-automated | P1 | MCP server advertises exactly 17 tools; `desk_universe`/`desk_screen` byte-identical to curl equivalents; `get_endpoint` proxies `/research/desk/screen` verbatim; MCP suite green | This journey has no browser/UI surface (goal.md tags it "Keyless; automated") — verified by direct execution of `tests/test_mcp_server.py`: 38/38 tests pass, including the exactly-17-tool contract assertion and the byte-identity proxy assertions. The session's live `mcp__tapeology__*` tools target the default port 8000, not this rig's :8301, so they could not be used as a live client against this specific rig; the pytest contract suite is the authoritative, direct verification instead | PASS | `apps/backend/tests/test_mcp_server.py` (38 passed, 0 failed, run live this session) |
| UT-J-14 | Every ranked briefing row states where the nearest wall on the OTHER side of price sits | happy-path (core fix) | P1 | `/desk`'s `opposite` column shows the corrected, distance-first nearest wall (not the best-graded one); at least one row ≤25 bps and one row >1,000 bps legible in one screenshot; a tooltip screenshot shows `bands_by_class` | Core fix confirmed live and definitively on real ambient data (HONA: rendered `opposite support B 210.23–211.63 · 0.00 bps`, cross-checked against `GET /research/tradability` showing farther class-A candidates at ~266/~351 bps that the OLD class-first rule would have picked instead — proof the corrected rule is active). Near (1.22/1.38/2.40 bps) and far (1128.29 bps) rows captured legible together in one screenshot with zero scrolling. `bands_by_class` tooltip CONTENT verified correct via DOM `title`-attribute inspection, but a visual screenshot of it could not be captured — native HTML `title` tooltips do not render into headless Chrome's screenshot surface (confirmed by two independent hover attempts; same null result independently hit by the same-day functional-QA agent) | PASS (with one documented environment-limitation gap, not a product defect — see below) | `reports/qa/goal-desk-iter-19-evidence/J-14-opposite-near-far.png`, `reports/qa/goal-desk-iter-19-evidence/J-14-tooltip-hover-attempt.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-29

