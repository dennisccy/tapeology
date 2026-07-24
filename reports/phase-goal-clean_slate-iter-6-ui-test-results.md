# UI Test Results (merged)

**Date:** 2026-07-24
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 12/12 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | Frontend + WS demolition — the two-page product | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-clean_slate-iter-6-evidence/J-02-verify.png |
| UT-01 | Cockpit page loads | smoke | P1 | "No ticker watched" visible, ticker field + Watch button, nav = Cockpit/Structure, no crash | Exactly as expected; nav confirmed 2 items; placeholder "Ticker e.g. SIM-BUYER" and "Watch" button present | PASS | `reports/qa/goal-clean_slate-iter-6-evidence/UT-01-result.png` |
| UT-02 | Structure page loads | smoke | P1 | "Structure" heading, Symbol/As-Of/Load fields, Case Studies table + Edge Report section both present | All present; Case Studies table pre-populated with 9 AAPL rows; Edge Report showed honest not-computed state | PASS | `reports/qa/goal-clean_slate-iter-6-evidence/UT-02-result.png` |
| UT-03 | Cockpit ticker watch → bar-size switch → stop | happy-path | P1 | "Buyer Control" after Watch; "Logical 30s bars..." caption after bar-size click; "No ticker watched" after Stop | All three transitions occurred correctly. Note: the final "No ticker watched" reset after clicking "Stop watching" was NOT instant — see Observations below | PASS | `UT-03-watch-result.png`, `UT-03-barsize-result.png`, `UT-03-stop-result.png` |
| UT-04 | Structure Load → Case Study drill-in | happy-path | P1 | "300.11" appears after Load; `case-drillin` opens after clicking a `case-studies-row` | Load showed a resistance band "300.11–302.2 · Class A" on the chart/table; clicking a case-studies-row opened a real drill-in panel (band, reaction "rejected", forward returns, honest "No recorded tape for this event.") | PASS | `UT-04-load-result.png` (screenshot); `UT-04-drillin-dom-text.txt` (DOM-text — see note below) |
| UT-05 | Load form doesn't fabricate results when empty | validation | P2 | No "300.11"/populated result from an empty Load; no crash | Clicking Load with both fields empty left the Tradable Map in its unchanged idle placeholder ("Choose a symbol and an as-of time..."); no crash, no fabricated data | PASS | `reports/qa/goal-clean_slate-iter-6-evidence/UT-05-result.png` |
| UT-06 | Edge Report honest state | error | P2 | Either populated cells or exact text "Edge report not computed yet." + visible Compute button; no blank/spinner/stack-trace | DOM confirmed the exact text "Edge report not computed yet." plus explanatory copy and a `data-testid="edge-report-compute-button"` (labelled "Compute edge report"); no error text | PASS | `UT-06-dom-text.md` (screenshot hit a known deep-scroll capture limitation — see note below) |
| UT-07 | No orphaned nav links reappear | regression | P1 | Exactly 2 nav items ("Cockpit", "Structure"); no Journal/Analytics/Studies/Monitor/Research label; clicking Structure navigates to `/structure` | Confirmed on both `/` and `/structure`: nav = exactly "Cockpit" + "Structure", no other label, in every DOM capture across the whole session | PASS | `reports/qa/goal-clean_slate-iter-6-evidence/UT-01-result.png`, `UT-02-result.png` |
| UT-08 | Structure reachable in 1 click from home | ux | P3 | "Structure" visible in nav without scrolling; 1 click reaches `/structure`; Load flow immediately visible | Confirmed: clicking "Structure" from `/` reached `/structure` directly, Symbol/As-Of/Load all visible above the fold with no further navigation | PASS | `reports/qa/goal-clean_slate-iter-6-evidence/UT-08-result.png` |
| UT-J-01 | J-01: Backend demolition with byte-identical relocations | regression (keyless/automated per goal.md) | P1 | All 14 I-1 routes 404; `/research/taxonomy` 200 with slimmed `feed_basis`-only payload; fingerprint unmoved; T-12 greps for the 11 deleted modules return zero live hits | All 14 routes curl-confirmed HTTP 404; taxonomy returned HTTP 200 with `{"feed_basis": {...}}` only (feeds: sim/iex/sip/yahoo + disclosure); `config_fingerprint()` = `08e471b10130e1e2`; T-12 grep zero non-test hits for all 11 modules; the 3 raw hits for `ThesisRecord`/`hint_projection_for`/`startup_sweep` were confirmed to be docstring/comment prose only (`edge_report.py:40`, `routes.py:160`, `main.py:150`), not live references; frontend grep for I-7 deleted type/function families = zero hits; deleted test files confirmed absent | PASS | curl/grep/python transcript (this turn); see Notes |
| UT-J-03 | J-03: MCP contract v2 — 15 read-only tools | regression (keyless/automated per goal.md) | P1 | MCP source advertises exactly the 15 I-6 tools (no journal/analytics/studies); `test_mcp_server.py` green | Source grep of `app/mcp/__init__.py` shows only `"taxonomy"` (no `"journal"`/`"analytics"`/`"studies"` entries); `pytest tests/test_mcp_server.py` → 29/29 passed | PASS | pytest transcript (this turn); see Notes re: an unrelated stale MCP tool-binding artifact in my own harness |
| UT-J-04 | J-04: The fingerprint epoch bump — §0.4 Path B | regression (keyless/automated per goal.md) | P1 | `config_fingerprint()` = new pin; old literal gone from live `apps/` code; ledger shows both epochs' founding rows | `config_fingerprint()` = `08e471b10130e1e2`; old literal `4d665603569b9dbf` appears nowhere in live `apps/` code except inside `test_fingerprint_epoch_retirement.py` (the guard test whose job is asserting its absence elsewhere — expected); `reports/pnl/pnl-history.md` contains exactly 1 row for each of the old and new fingerprints; `pytest tests/test_fingerprint_epoch_retirement.py` → 3/3 passed | PASS | pytest/grep transcript (this turn) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-24

