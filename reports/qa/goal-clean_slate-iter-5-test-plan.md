# goal-clean_slate-iter-5 Functional Test Plan

**Phase:** goal-clean_slate-iter-5 (J-05 — The kept product stands: regression sentinel)  
**Date:** 2026-07-24  
**Frontend Present:** yes

## Phase Goal

Prove the four-journey demolition genuinely stands as a whole product: a full-suite-green regression pass under the new fingerprint epoch (08e471b10130e1e2), a complete browser walk of every kept surface, and Case Studies visibility restored on `/structure` — closing J-05, the interlude's final Must-have journey.

## Test Cases

### TC-01 — Full backend suite green under new fingerprint

**Type:** api  
**Preconditions:** Backend running on committed fixtures; pin is `08e471b10130e1e2`

**Steps:**
1. Run `cd /home/dennis-chan/Git/tapeology && python -m pytest apps/backend/tests/ -v 2>&1 | tee reports/qa/iter-5-full-suite.log`
2. Capture exit code and pass/fail counts

**Expected outcome:** Test suite completes with exit code 0; reports exactly 0 failed, 0 errors; expected baseline is 1167 passed / 7 skipped (iter-4 baseline on clean re-run, no new test files added this iteration)

**Pass criteria:** `Test session starts … passed … skipped … failed: 0 … in …s` and `exit code 0`; literal "0 failed" with no carve-outs

---

### TC-02 — Guard and chart-guard suites pass byte-unmodified

**Type:** api  
**Preconditions:** Backend running; guard test files exist (`test_no_execution_path.py`, `test_no_credential_in_artifacts.py`, `test_backtests.py`, `test_setups.py`, `test_cockpit_chart_upgrade.py`, `test_structure_chart_viewport.py`, `test_price_chart_confluence.py`)

**Steps:**
1. Run `python -m pytest apps/backend/tests/test_no_execution_path.py -v`
2. Run `python -m pytest apps/backend/tests/test_no_credential_in_artifacts.py -v`
3. Run `python -m pytest apps/backend/tests/test_backtests.py::test_forbidden_level_internal_substrings -v`
4. Run `python -m pytest apps/backend/tests/test_backtests.py::test_map_arm_source_pins -v`
5. Run `python -m pytest apps/backend/tests/test_setups.py::test_single_scan_cache_rebind -v`
6. Run `python -m pytest apps/backend/tests/test_setups.py::test_forbidden_substring -v`
7. Run `python -m pytest apps/backend/tests/test_cockpit_chart_upgrade.py -v`
8. Run `python -m pytest apps/backend/tests/test_structure_chart_viewport.py -v`
9. Run `python -m pytest apps/backend/tests/test_price_chart_confluence.py -v`
10. Run `git diff apps/backend/tests/test_no_execution_path.py apps/backend/tests/test_no_credential_in_artifacts.py apps/backend/tests/test_backtests.py apps/backend/tests/test_setups.py apps/backend/tests/test_cockpit_chart_upgrade.py apps/backend/tests/test_structure_chart_viewport.py apps/backend/tests/test_price_chart_confluence.py` (outside J-04's fingerprint pin-assertion lines)

**Expected outcome:** Each guard/chart-guard suite passes independently; git diff shows zero changes to test logic (only the already-landed J-04 fingerprint-pin assertion lines differ)

**Pass criteria:** All 9 test runs exit 0 with no failures; file diff is empty (or only shows J-04 pin-assertion line changes with no logic/structure edits)

---

### TC-03 — Levels/bands/setups byte-identical except for config_fingerprint stamp

**Type:** api  
**Preconditions:** Backend running; iter-4 baseline capture exists and is valid; same fixture input (AAPL 2026-06-22)

**Steps:**
1. Fetch fresh levels payload: `curl -s http://localhost:8000/research/levels?symbol=AAPL&as_of=2026-06-22T21:00:00Z`
2. Extract and compare the returned values (excluding the `config_fingerprint` field) against iter-4's saved capture
3. Verify the returned `config_fingerprint` reads exactly `08e471b10130e1e2`

**Expected outcome:** All numeric values (zone bounds, touch counts, etc.) are byte-identical to iter-4; only the fingerprint stamp differs

**Pass criteria:** A diff tool reports zero value differences when `config_fingerprint` is excluded; `config_fingerprint` in response == `08e471b10130e1e2`

---

### TC-04 — Nav shows exactly Cockpit and Structure (no deleted routes)

**Type:** browser  
**Preconditions:** Frontend rebuilt fresh (`rm -rf apps/frontend/.next`), running at http://localhost:3000; backend running at http://localhost:8000

**Steps:**
1. Open http://localhost:3000 in Chrome
2. Inspect the top navigation bar element
3. Count and name the visible nav items
4. Verify no `/journal`, `/studies`, `/performance` links appear anywhere on the page

**Expected outcome:** Exactly 2 nav items: "Cockpit" and "Structure"; no deleted-surface links anywhere on page

**Pass criteria:** `document.querySelectorAll('nav a, nav button').length == 2` and text nodes are exactly ["Cockpit", "Structure"]; no href or text matching `journal|studies|performance`

---

### TC-05 — Sim cockpit SIM-BUYER watch settles and displays "Buyer Control"

**Type:** browser  
**Preconditions:** Cockpit at http://localhost:3000 open; no ticker currently watched

**Steps:**
1. Locate the ticker input field
2. Type `SIM-BUYER` into the ticker field
3. Click the "Watch" button
4. Wait for the tape-state panel to settle (≤2 sec)
5. Inspect the tape-state panel text

**Expected outcome:** Tape-state panel displays "Buyer Control" text (the SIM-BUYER tape-state projection); no error messages

**Pass criteria:** Page contains text "Buyer Control" in the tape-state section; no red error panel

---

### TC-06 — PriceChart renders candles and responds to timeframe switch

**Type:** browser  
**Preconditions:** Cockpit watching `SIM-BUYER`; PriceChart visible

**Steps:**
1. Observe the chart's current candle density (e.g., count visible bars)
2. Locate the timeframe selector control
3. Click to open the timeframe menu
4. Select a different timeframe (e.g., if current is 5m, switch to 1h)
5. Wait for chart re-render (≤1 sec)
6. Observe the candle density change

**Expected outcome:** Chart visibly re-renders with a different bar width/count after timeframe switch; no error panel

**Pass criteria:** Bar width or bar count visibly changes post-switch; `<canvas>` or chart SVG repaints; no console errors

---

### TC-07 — Live tape bars move as new ticks stream in

**Type:** browser  
**Preconditions:** Cockpit watching `SIM-BUYER`; chart visible; ticks are streaming (tape flowing)

**Steps:**
1. Observe the PriceChart's rightmost bar (the current open bar)
2. Wait for 3–5 ticks to arrive (timestamp should advance visibly in the tape)
3. Observe whether the rightmost bar extends or moves

**Expected outcome:** The rightmost bar visibly extends upward/downward and moves rightward as new ticks arrive; S/R band overlay (if rendered) stays anchored at its price level

**Pass criteria:** Rightmost bar's high/low/close changes and moves right; band overlay (if present) maintains its Y-axis position

---

### TC-08 — Cockpit Stop button hides ticker and displays "No ticker watched"

**Type:** browser  
**Preconditions:** Cockpit watching `SIM-BUYER`

**Steps:**
1. Locate the Stop button
2. Click Stop
3. Inspect the tape-state panel

**Expected outcome:** Tape-state panel displays "No ticker watched"; tape stops flowing; all ephemeral state clears

**Pass criteria:** Text "No ticker watched" appears in tape-state section; tape activity ceases

---

### TC-09 — /structure Load renders AAPL candles and wall band for pinned window

**Type:** browser  
**Preconditions:** Frontend at http://localhost:3000; backend running; AAPL 2026-06-22 recorded window available in fixtures

**Steps:**
1. Navigate to http://localhost:3000/structure
2. Locate the symbol input field; enter `AAPL`
3. Locate the as-of date/time input; enter `2026-06-22T21:00:00Z`
4. Click the "Load" button
5. Wait for chart to render (≤2 sec)
6. Inspect the StructureChart canvas/SVG for candle bars
7. Inspect the chart for a visible overlay band (the tradable-map wall band ~300–302.4 price range)
8. Verify the golden script's assertion: the band label or price text contains the substring `300.11`

**Expected outcome:** StructureChart renders AAPL candles for the 2026-06-22 date; a colored band overlay appears at the ~300–302.4 level; the band is visibly labeled or contains `300.11` reference

**Pass criteria:** Canvas/SVG contains multiple candlestick shapes; a band path/shape renders in the 300–302 Y-axis range; band or nearby text matches regex `300\\.1`

---

### TC-10 — Case Studies panel is visible and drill-in works when clicked

**Type:** browser  
**Preconditions:** `/structure` with AAPL 2026-06-22 loaded; `SHOW_CASE_STUDIES` is `true`; Case Studies data available

**Steps:**
1. Scroll down to locate the "Case Studies" section on the `/structure` page
2. Verify the section is visible (not hidden by CSS `display: none`)
3. Locate a listed band-touch event row in the Case Studies table
4. Click on the row to open a drill-in view
5. Wait for drill-in to render (≤1 sec)
6. Inspect the drill-in content for either: (a) a tape timeline visualization, or (b) the text "not recorded"
7. **Take a screenshot of the drill-in**

**Expected outcome:** Case Studies section renders; a row-click opens a drill-in pane showing either a tape timeline or an honest "not recorded" state; no errors

**Pass criteria:** Section element is visible; drill-in pane renders without JavaScript errors; screenshot shows the drill-in content (either bars or "not recorded" text); no blank/broken panel

---

### TC-11 — Edge Report panel shows honest current state (cells or "not computed")

**Type:** browser  
**Preconditions:** `/structure` with AAPL 2026-06-22 loaded; Edge Report section visible

**Steps:**
1. Scroll down to the Edge Report section
2. Inspect the panel's current state
3. Verify one of two conditions: (a) edge-report cells are populated with values (warm cache exists), OR (b) the panel displays the exact text "Edge report not computed yet." with a visible "Compute" button beside it

**Expected outcome:** Edge Report panel renders either populated edge cells OR the exact honest message + Compute button; never a blank/loading panel

**Pass criteria:** Panel contains either: (a) a table/grid with populated cells, OR (b) the text "Edge report not computed yet." AND a button labeled "Compute"; no spinner or blank space

---

### TC-12 — All 15 deleted routes return HTTP 404

**Type:** api  
**Preconditions:** Backend running at http://localhost:8000

**Steps:**
1. For each of the 15 deleted routes, run a curl request and capture the HTTP status code:
   - `GET /research/analytics`
   - `GET /research/thesis/active`
   - `GET /research/hints/active`
   - `GET /research/hints`
   - `GET /research/journal`
   - `GET /research/journal/{thesis_id}` (use any ID, e.g., `1`)
   - `POST /research/thesis`
   - `POST /research/thesis/{thesis_id}/resolve`
   - `POST /research/thesis/{thesis_id}/action`
   - `POST /research/thesis/{thesis_id}/review`
   - `POST /research/studies`
   - `GET /research/studies`
   - `GET /research/studies/{study_id}`
   - `POST /research/studies/{study_id}/cancel`

**Expected outcome:** Every request returns HTTP 404 (not 200, not a redirect, not a "coming soon" placeholder)

**Pass criteria:** All 15 requests return status code 404; response body is the app's standard 404 error JSON (not a thesis/study/journal-era response)

---

### TC-13 — MCP list_tools() returns exactly 15 tool names

**Type:** api  
**Preconditions:** MCP server running alongside backend

**Steps:**
1. Call the MCP server's `list_tools()` method (or invoke via test: `python -m pytest apps/backend/tests/test_mcp_server.py::test_list_tools_contract -v`)
2. Count and name the returned tool IDs

**Expected outcome:** Exactly 15 tools returned with these names (in any order): `tape_state`, `tape_features`, `tape_history`, `datasets`, `bars`, `levels`, `tradability`, `setups`, `backtests`, `strategies`, `pnl_ledger`, `taxonomy`, `edge_report`, `ui_route_map`, `get_endpoint`

**Pass criteria:** `len(tools) == 15` and `set(tool.id for tool in tools) == {"tape_state", "tape_features", "tape_history", "datasets", "bars", "levels", "tradability", "setups", "backtests", "strategies", "pnl_ledger", "taxonomy", "edge_report", "ui_route_map", "get_endpoint"}`

---

### TC-14 — No live imports of 11 deleted modules outside history

**Type:** api  
**Preconditions:** Repository at goal-clean_slate-iter-5 commit

**Steps:**
1. Run a grep to search for imports of deleted modules only under `apps/`:
   ```bash
   grep -r "from .journal_rows import\|from .monitor import\|from .hints import\|from .stance import\|from .verdict import\|from .grades import\|from .marks import\|from .excursions import\|from .execution_checks import\|from .analytics import\|from .studies import" apps/ 2>/dev/null | grep -v "reports/\|runs/\|docs/goal-archive/" | wc -l
   ```
2. Verify the count is 0

**Expected outcome:** Zero imports of the 11 deleted modules appear in live `apps/` code

**Pass criteria:** Command returns 0 (or "0 matches"); no stderr messages indicating found imports

---

### TC-15 — Iteration diff touches only expected files (product + testing artifacts)

**Type:** artifact  
**Preconditions:** Git log shows iter-5 commit(s); iter-0 baseline snapshot exists

**Steps:**
1. Compute cumulative diff from iter-0 baseline through iter-5: `git diff <iter-0-baseline-commit> HEAD -- apps/`
2. For each touched file in `apps/`, verify it is one of: (a) `apps/frontend/app/structure/page.tsx` (product — flag flip + sentence), or (b) anything under `runs/goal-session-clean_slate/iter-5/` or `reports/qa/` (testing artifacts OK)
3. Verify no other `apps/` file is touched by this iteration

**Expected outcome:** Only `apps/frontend/app/structure/page.tsx` is touched under `apps/` in the product scope; no backend source files, no other frontend files

**Pass criteria:** `git diff` output restricted to `apps/frontend/app/structure/page.tsx` (lines ~335 and ~2032–2039) plus any files under `runs/goal-session-clean_slate/iter-5/` or `reports/` (testing/evidence); zero other `apps/` file has changes

---

### TC-16 — SHOW_CASE_STUDIES is true and framing sentence is reinstated

**Type:** artifact  
**Preconditions:** File `apps/frontend/app/structure/page.tsx` exists

**Steps:**
1. Read `apps/frontend/app/structure/page.tsx` and locate line ~335
2. Verify the line reads: `const SHOW_CASE_STUDIES: boolean = true;`
3. Locate the `data-testid="structure-framing"` paragraph (lines ~2032–2039)
4. Verify the paragraph text includes the sentence: "Case Studies lists every band-touch event with its reaction, forward returns, and — once recorded — its tape timeline; " immediately before the sentence starting with "Edge Report compares v1, structure_tape, and structure_tape_map..."

**Expected outcome:** Flag is `true`; reinstated sentence appears verbatim in the framing paragraph in the correct position

**Pass criteria:** Literal grep: `const SHOW_CASE_STUDIES: boolean = true;` found at line ~335; sentence substring "Case Studies lists every band-touch event with its reaction, forward returns, and — once recorded — its tape timeline;" appears before "Edge Report compares" in the structure-framing element

---

### TC-17 — No historical records touched (goal-archive, pnl-history, journal.db)

**Type:** artifact  
**Preconditions:** Repository at iter-5 commit; iter-0 through iter-4 records exist

**Steps:**
1. Run `git diff HEAD~5 HEAD -- docs/goal-archive/ runs/goal-session-clean_slate/iter-0 runs/goal-session-clean_slate/iter-1 runs/goal-session-clean_slate/iter-2 runs/goal-session-clean_slate/iter-3 runs/goal-session-clean_slate/iter-4 reports/pnl/pnl-history.md` (or equivalent commit range)
2. Verify the diff is empty (zero byte changes to these paths)

**Expected outcome:** No changes to archived iterations, goal-archive, or existing PnL ledger rows

**Pass criteria:** Diff output is empty or shows "no changes"; git status shows these paths unmodified across the iteration

---

## Summary

**Total test cases:** 17

| Category | Count |
|----------|-------|
| API tests (backend routes, MCP, grep) | 10 |
| Browser tests (UI flows, navigation, chart rendering) | 6 |
| Artifact checks (file contents, git diff) | 1 |

**Key regression domains:**
- Backend suite green under new fingerprint (TC-01)
- Guard suites unchanged (TC-02)
- Research value byte-identical (TC-03)
- Navigation and product surface (TC-04, TC-13, TC-15, TC-17)
- Browser-verified flows: cockpit (TC-05–TC-08), structure load (TC-09), case studies (TC-10), edge report (TC-11)
- Deleted route 404s (TC-12)
- Deleted module imports (TC-14)
- Product code changes (TC-16)

All test cases map directly to Definition of Done checklist items and Testing Requirements scenarios in the phase spec.
