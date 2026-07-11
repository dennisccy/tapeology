# goal-yahoo_fetch-iter-6 Functional Test Plan

**Phase:** goal-yahoo_fetch-iter-6
**Date:** 2026-07-11
**Frontend Present:** yes

## Phase Goal

Flip J-05 from `partial` to `passing` by landing missing browser evidence — a clean, unoccluded "Yahoo Finance" provenance-badge screenshot, a browser-captured honest empty state, and three UI-visibility artifacts — without changing one byte of product source.

## Test Cases

### TC-01 — Backend suite regression floor

**Type:** artifact
**Preconditions:** Backend is built and ready to run; no product source changes have been made to `config.py`, `research/levels.py`, `research/backtests.py`, `research/strategies.py`, `research/bars.py`, `research/bar_index.py`, `providers/adapters/`, the tape engine, `research/taxonomy.py`, or `mcp/`.

**Steps:**
1. Run the full backend test suite via `.claude/project-template.md` test command
2. Capture stdout and stderr to a log file
3. Record the exact pass/fail/skipped counts

**Expected outcome:** Test suite completes with all tests passing or skipped (no new failures introduced).
**Pass criteria:** Exit code 0; reported counts ≥1207 passed / 0 failed / 6 skipped (baseline from phase spec).

---

### TC-02 — Engine equivalence and config fingerprint

**Type:** api
**Preconditions:** Backend suite passed (TC-01); the tape engine and `config.py` are byte-identical to prior state.

**Steps:**
1. Run the engine equivalence test (`pytest -k equivalence`)
2. Verify `config_fingerprint` matches the expected value

**Expected outcome:** Engine equivalence test passes; `config_fingerprint` == `4d665603569b9dbf`.
**Pass criteria:** Equivalence test shows 22/22 matches; `config_fingerprint` output line contains exactly `4d665603569b9dbf`.

---

### TC-03 — Zero product source change

**Type:** artifact
**Preconditions:** A clean git state exists at the start of the iteration (snapshot branch or commit ID known).

**Steps:**
1. Run `git diff <snapshot>..HEAD -- apps/`
2. Filter to files in the frozen set: `config.py`, `research/levels.py`, `research/backtests.py`, `research/strategies.py`, `research/bars.py`, `research/bar_index.py`, `providers/adapters/`, tape engine, `research/taxonomy.py`, `mcp/`
3. Record any diffs

**Expected outcome:** No diffs in the frozen set; only test, artifact, and data files may change.
**Pass criteria:** `git diff` output is empty over the full frozen file set.

---

### TC-04 — Fixture present and indexed

**Type:** api
**Preconditions:** Backend is running on `:8301`; the `.data/bar_index.db` index file exists or can be seeded.

**Steps:**
1. Call `GET /research/bars?symbol=AAPL&timeframe=1d` to confirm at least one stored series
2. Call `GET /research/bars/` with no params and verify the full list includes the fixture
3. Verify the indexing returns the series with no network call (check logs or timing)

**Expected outcome:** Fixture is present and indexed; queries return instantly from storage.
**Pass criteria:** HTTP 200; response includes at least one series with `feed="yahoo"`, symbol `AAPL`, timeframe `1d`, and a `checksum` field.

---

### TC-05 — Fetch control renders

**Type:** browser
**Preconditions:** Frontend (`:3301`) and backend (`:8301`) are both running; Chrome MCP is available; user has navigated to `/structure`.

**Steps:**
1. Use Chrome MCP to navigate to `http://localhost:3301/structure`
2. Verify the page loads without error
3. Locate the fetch control elements: symbol input (`SymbolSearch`), timeframe select, start/end date inputs, and "Fetch from Yahoo Finance" button
4. Verify all elements are visible

**Expected outcome:** Fetch control is fully rendered and interactive.
**Pass criteria:** All four control elements present and clickable; no console errors.

---

### TC-06 — Fetch and store-first response

**Type:** browser
**Preconditions:** TC-05 passed (fetch control renders); fixture is pre-seeded and indexed (TC-04); symbol is `AAPL`, timeframe is `1d`.

**Steps:**
1. Use Chrome MCP to interact with the fetch control:
   - Set symbol to `AAPL` (via `SymbolSearch`)
   - Set timeframe to `1d`
   - Set date range to `2026-06-01` to `2026-06-04` (fixture window)
2. Click "Fetch from Yahoo Finance" button
3. Observe the network request (Chrome DevTools Network tab, or check backend logs for response status)
4. Wait for chart to render and verify no second network call to Yahoo is made (store-first serve)

**Expected outcome:** Fetch completes instantly with a 200 store-first response (served from `.data/`); no network call to Yahoo.
**Pass criteria:** Network response status is 200; response time is <1s (store-first); `lightweight-charts` chart renders without error.

---

### TC-07 — Chart renders with real candles, levels, and zones

**Type:** browser
**Preconditions:** TC-06 passed (fetch completes and returns 200); chart is rendering.

**Steps:**
1. Inspect the rendered chart for candle bodies and wicks (OHLCV bars)
2. Verify support/resistance level lines are drawn on the chart (colored horizontal lines)
3. Verify the A/B/C confluence zone table is rendered below or beside the chart
4. Use Chrome DevTools to inspect the chart's data source and confirm it matches `/research/bars` and `/research/levels` responses

**Expected outcome:** Chart displays real candles, S/R levels, and confluence zones, all read verbatim from backend endpoints.
**Pass criteria:** At least 3 candles visible with correct OHLCV data; at least 2 support/resistance lines visible; A/B/C table has rows with class labels and zone scores.

---

### TC-08 — Levels and zones read verbatim from backend

**Type:** api
**Preconditions:** Chart has rendered (TC-07); backend is accessible.

**Steps:**
1. Call `GET /research/bars?symbol=AAPL&timeframe=1d` with the fixture window to retrieve bar data
2. Call `GET /research/levels?symbol=AAPL&as_of=2026-06-05T00:00:00Z` to retrieve computed levels and zones
3. Compare the chart's rendered data (via Chrome DevTools DOM inspection) to the exact JSON from these endpoints
4. Verify byte-for-byte match (no client-side recomputation)

**Expected outcome:** Chart displays exactly what the backend endpoints return.
**Pass criteria:** DOM data attributes or chart data series match the JSON values exactly (e.g., level prices, zone scores, class labels).

---

### TC-09 — Clean, unoccluded "Yahoo Finance" badge

**Type:** browser
**Preconditions:** TC-06 and TC-07 passed (chart rendered); the `SymbolSearch` dropdown may be open.

**Steps:**
1. Use Chrome MCP to click outside the `SymbolSearch` suggestion dropdown (e.g., click on the chart background or a neutral area in the panel)
2. Verify the dropdown closes (it has an outside-click handler per `SymbolSearch.tsx:71-77`)
3. Locate the `FeedBasisBadge` component (via Chrome DevTools, `data-testid="feed-basis"`); it should display the text "Yahoo Finance"
4. Take a screenshot of the badge and save it to `reports/qa/goal-yahoo_fetch-iter-6-evidence/TC-09-clean-badge.png`
5. Visually verify the badge is unoccluded and the text is fully legible

**Expected outcome:** Badge is rendered cleanly, unoccluded by the dropdown, and displays "Yahoo Finance" verbatim from the taxonomy label.
**Pass criteria:** Screenshot shows the full badge text "Yahoo Finance"; no dropdown or other UI elements obscure it; the label is sourced from `FEED_BASIS_LABELS` (confirmed via reading `FeedBasisBadge.tsx`).

---

### TC-10 — Honest empty state for a symbol with no stored bars

**Type:** browser
**Preconditions:** Frontend (`:3301`) and backend (`:8301`) are running; a symbol with zero recorded bar series has been identified (e.g., `TSLA` or `GOOGL` — confirmed via `GET /research/bars?symbol=<X>` returning empty list).

**Steps:**
1. Use Chrome MCP to navigate to `/structure`
2. Interact with the fetch control:
   - Set symbol to the no-bars symbol (e.g., `TSLA`)
   - Set timeframe to `1d`
   - Leave date range at defaults or pick any valid range
3. Click "Fetch from Yahoo Finance" (this will result in an error/empty-state response)
4. Observe the rendered state — it should be a distinct honest empty/error state, not an empty chart or a partial render
5. Take a screenshot of the empty state and save it to `reports/qa/goal-yahoo_fetch-iter-6-evidence/TC-10-empty-state.png`
6. Verify via Chrome DevTools that the DOM element has `data-testid="structure-no-bar-series"` or similar

**Expected outcome:** A distinct, unambiguous empty state is rendered when a symbol has no stored bars; the state clearly communicates why the chart is empty.
**Pass criteria:** Screenshot shows an `UnavailablePanel` or `EmptyState` component; the message is clear and distinct from a loading state or error; DOM confirms the empty-state element is present.

---

### TC-11 — UI-visibility artifacts exist with real content

**Type:** artifact
**Preconditions:** Browser lane has completed; all test cases TC-05 through TC-10 have passed and screenshots are saved.

**Steps:**
1. Verify the following files exist and contain real, non-vague content (not SKIPPED stubs):
   - `reports/phase-goal-yahoo_fetch-iter-6-ui-test-plan.md`
   - `reports/phase-goal-yahoo_fetch-iter-6-what-to-click.md`
   - `reports/phase-goal-yahoo_fetch-iter-6-ui-test-results.md`
2. Verify evidence screenshots exist:
   - `reports/qa/goal-yahoo_fetch-iter-6-evidence/TC-05-fetch-control-renders.png` (or similar naming)
   - `reports/qa/goal-yahoo_fetch-iter-6-evidence/TC-06-chart-candles.png` (or similar)
   - `reports/qa/goal-yahoo_fetch-iter-6-evidence/TC-09-clean-badge.png`
   - `reports/qa/goal-yahoo_fetch-iter-6-evidence/TC-10-empty-state.png`
3. Open each artifact and verify it contains substantive content (>100 words for plans; actual test step descriptions and assertions for results)

**Expected outcome:** All artifacts exist with real, mutually consistent content.
**Pass criteria:** Each file is >100 words (plans/results); each screenshot is a valid PNG file; no file contains placeholder text or "SKIPPED" boilerplate.

---

### TC-12 — Phase-closure verdict is CLOSURE-PASS

**Type:** artifact
**Preconditions:** Browser lane has completed; all TC-05 through TC-11 have passed.

**Steps:**
1. The phase-closure-auditor will run as part of the full 11-step pipeline
2. Check `reports/phase-goal-yahoo_fetch-iter-6-closure-verdict.md` for the verdict line
3. Verify the verdict is **CLOSURE-PASS** (not CLOSURE-FAIL or CLOSURE-BLOCKED)
4. Verify the report notes that all six required UI-visibility artifacts exist and are complete

**Expected outcome:** phase-closure-auditor certifies that all evidence artifacts are present, complete, and consistent.
**Pass criteria:** `reports/phase-goal-yahoo_fetch-iter-6-closure-verdict.md` contains the line `**Verdict:** CLOSURE-PASS`.

---

### TC-13 — UX regression review is clean

**Type:** artifact
**Preconditions:** Browser lane has completed; all TC-05 through TC-11 have passed.

**Steps:**
1. The ux-regression-reviewer will run as part of the full 11-step pipeline
2. Check `reports/phase-goal-yahoo_fetch-iter-6-ux-regression.md` for findings
3. Verify that the two iter-5 WARN items (F1 occlusion, TC-11 evidence gap) are resolved by this iteration's capture work (not a source fix)
4. Verify no new regressions are introduced (J-01–J-04, J-06 remain green)

**Expected outcome:** ux-regression-reviewer certifies that the UI evolution is clean and the prior WARN items are resolved.
**Pass criteria:** `reports/phase-goal-yahoo_fetch-iter-6-ux-regression.md` shows a passing or clean verdict; F1 and TC-11 are explicitly noted as resolved; no regressions in J-01–J-06.

---

### TC-14 — Coherence stays COHERENCE-PASS

**Type:** artifact
**Preconditions:** Full pipeline has run; coherence-auditor has completed.

**Steps:**
1. Check the coherence audit report (typically produced midway through the pipeline)
2. Verify that:
   - No new endpoint is added (only browser evidence-capture, no API changes)
   - No computation path is duplicated (the badge still reads taxonomy label; levels still sourced from `research/levels.py`)
   - Data contract is preserved (no second source of truth introduced)

**Expected outcome:** coherence-auditor certifies no violations; the single-source-of-truth rails remain intact.
**Pass criteria:** Coherence audit report shows `**Verdict:** COHERENCE-PASS` (or equivalent); no CRITICAL or IMPORTANT findings related to contract duplication.

---

### TC-15 — Anti-goal verification

**Type:** artifact
**Preconditions:** Full pipeline has completed; dev handoff and all audits are complete.

**Steps:**
1. Verify via code inspection and artifact review that:
   - **Frozen foundations:** `config.py`, `research/levels.py`, `research/backtests.py`, `research/strategies.py`, tape engine, JSON `BarStore`, Alpaca adapter are byte-identical
   - **Immutable data:** No bar series is re-tagged, deleted, or perturbed; append-only integrity is maintained
   - **No vocabulary drift:** No "paper trading", "expected profit", or advice phrasing in UI copy
   - **No fabricated bars:** Empty-state and error cases are explicit, not synthesized
   - **Yahoo data segregation:** `feed="yahoo"` series remain distinct from `sip` (browser test scoped to yahoo-only fixture)
   - **Single source of truth:** UI reads verbatim from canonical endpoints; no client-side recomputation of levels/zones/provenance
2. Read `docs/handoffs/goal-yahoo_fetch-iter-6-dev.md` and verify these points are documented

**Expected outcome:** All anti-goal rails remain intact; no mutation or violation is introduced.
**Pass criteria:** `git diff` shows zero changes in the frozen file set (TC-03); dev handoff explicitly confirms no anti-goal violation.

---

## Summary

**Total test cases: 15**
- **API tests: 2** (TC-02 equivalence, TC-04 fixture, TC-08 verbatim-read)
- **Browser tests: 6** (TC-05 control, TC-06 fetch, TC-07 chart, TC-09 badge, TC-10 empty state, TC-11 artifacts)
- **Artifact checks: 7** (TC-01 regression, TC-03 diff, TC-11 artifacts, TC-12 closure, TC-13 ux-regression, TC-14 coherence, TC-15 anti-goals)

**Test grouping by phase objective:**
- **Regression & Frozen Foundations:** TC-01, TC-02, TC-03, TC-14, TC-15
- **Browser Evidence (J-05 core):** TC-05, TC-06, TC-07, TC-08, TC-09, TC-10
- **Closure & Artifacts:** TC-04, TC-11, TC-12, TC-13

**Execution order:** Run TC-01 and TC-02 first (regression floor); then TC-04 (fixture seed); then TC-05–TC-10 (browser lane); finally TC-11–TC-15 (artifacts and audits).
