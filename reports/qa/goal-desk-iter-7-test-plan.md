# goal-desk-iter-7 Functional Test Plan

**Phase:** goal-desk-iter-7
**Date:** 2026-07-26
**Frontend Present:** yes

## Phase Goal

The MCP server advertises exactly 17 tools (adding `desk_universe` and `desk_screen` to the existing 15), the F2 hover-honesty regression on `/desk` rows is repaired by consolidating lost tooltips onto the row's drill-in anchor without changing click geometry, the golden J-05 script selects its history row by date instead of position, and the era's full kept-product regression walk (Cockpit, Structure, desk, MCP tool count, kept-route byte-identity) receives the complete browser-evidence pass J-07 has required since iteration 4.

## Test Cases

### TC-01 — MCP `desk_universe` returns honest-empty body when no universe registered

**Type:** api
**Preconditions:** Fresh fixture-scoped test backend with no universe snapshot ever recorded; `TAPEOLOGY_DESK_UNIVERSE_DIR` env-var pointing to the test temp store.

**Steps:**
1. Initialize a test backend with no pre-recorded universe.
2. Call `app.mcp.call_tool("desk_universe", {})`.
3. Inspect the returned `content[0].text`.

**Expected outcome:** Response is byte-identical to `curl GET /research/desk/universe` on the same backend: `{"snapshots": [], "latest": null, "integrity_errors": []}`.

**Pass criteria:** JSON response body matches exactly (no extra fields, no null → undefined conversion).

---

### TC-02 — MCP `desk_universe` returns populated body with committed fixture

**Type:** api
**Preconditions:** Test backend with the committed fixture universe snapshot registered via `UniverseStore(...).record(...)` (103 members, the fixture's checksum).

**Steps:**
1. Seed the fixture universe into the test backend's `TAPEOLOGY_DESK_UNIVERSE_DIR` store.
2. Call `app.mcp.call_tool("desk_universe", {})`.
3. Inspect the returned `content[0].text`.

**Expected outcome:** Response is byte-identical to the curl response on the same backend, including the `latest` snapshot with 103 members and matching checksum.

**Pass criteria:** Entire JSON payload matches, including all snapshot metadata and member records.

---

### TC-03 — MCP `desk_screen` returns honest-empty body when no screen computed

**Type:** api
**Preconditions:** Fresh fixture-scoped test backend with no screen snapshot ever computed; `TAPEOLOGY_DESK_SCREEN_DIR` env-var pointing to the test temp store.

**Steps:**
1. Initialize a test backend with no pre-recorded screens.
2. Call `app.mcp.call_tool("desk_screen", {})`.
3. Inspect the returned `content[0].text`.

**Expected outcome:** Response is byte-identical to `curl GET /research/desk/screen` on the same backend: `{"screens": [], "latest": null, "integrity_errors": []}`.

**Pass criteria:** JSON response body matches exactly.

---

### TC-04 — MCP `desk_screen` returns populated body with recorded snapshot

**Type:** api
**Preconditions:** Test backend with a screen snapshot recorded via `ScreenStore(...).record(...)` for a known date (e.g., 2026-06-22).

**Steps:**
1. Seed a screen snapshot into the test backend's `TAPEOLOGY_DESK_SCREEN_DIR` store.
2. Call `app.mcp.call_tool("desk_screen", {})`.
3. Inspect the returned `content[0].text`.

**Expected outcome:** Response is byte-identical to the curl response on the same backend, including the `latest` snapshot with all fields and the `screens` meta-only list.

**Pass criteria:** Entire JSON payload matches, including `latest` and `screens` array entries.

---

### TC-05 — MCP `list_tools()` advertises exactly 17 tools including desk_universe and desk_screen

**Type:** api
**Preconditions:** Fresh test backend with `app.mcp` module loaded; no prior tool registrations.

**Steps:**
1. Call `app.mcp.list_tools()`.
2. Count the returned tool list and extract tool names.
3. Compare names to the updated `EXPECTED_TOOLS` tuple (15 existing + `desk_universe` + `desk_screen`).

**Expected outcome:** Exactly 17 tools returned; names match the expected set in any order (order is insertion order per the tuple, but equivalence is by set membership).

**Pass criteria:** Tool count is exactly 17; both `desk_universe` and `desk_screen` appear in the returned names; all 15 existing tools still present.

---

### TC-06 — MCP `get_endpoint` proxies `/research/desk/screen?date=` verbatim for matching date

**Type:** api
**Preconditions:** Test backend with a screen snapshot recorded for date `2026-06-22`; `TAPEOLOGY_DESK_SCREEN_DIR` env-var set.

**Steps:**
1. Call `app.mcp.call_tool("get_endpoint", {"path": "/research/desk/screen?date=2026-06-22"})`.
2. Inspect the returned `content[0].text`.
3. Compare to direct curl: `curl "GET /research/desk/screen?date=2026-06-22"` on the same backend.

**Expected outcome:** Response is byte-identical to the curl command, including the `screen` record with all fields populated.

**Pass criteria:** JSON payload matches exactly.

---

### TC-07 — MCP `get_endpoint` returns honest null for non-matching date

**Type:** api
**Preconditions:** Test backend with a screen snapshot recorded for date `2026-06-22`; `TAPEOLOGY_DESK_SCREEN_DIR` env-var set.

**Steps:**
1. Call `app.mcp.call_tool("get_endpoint", {"path": "/research/desk/screen?date=2999-01-01"})`.
2. Inspect the returned `content[0].text` and the `isError` field.

**Expected outcome:** Response is `{"screen": null}` (the honest 200 response from the endpoint); `isError` is false (not treated as an error).

**Pass criteria:** Body equals `{"screen": null}` exactly; `isError` is false.

---

### TC-08 — Hovering `/desk` ranked row shows full-precision composite tooltip on drill-in anchor

**Type:** browser
**Preconditions:** Frontend running at http://localhost:3000; `/desk` page loaded with at least one ranked row (e.g., AAPL with non-empty `distance_bps`, `band_score`, and coverage entries with `latest_window_end_utc`).

**Steps:**
1. Navigate to `/desk`.
2. Locate a ranked row (e.g., by symbol "AAPL").
3. Position mouse pointer anywhere within that row.
4. Wait for the tooltip to appear.
5. Capture the tooltip text.

**Expected outcome:** Tooltip contains the row's full unrounded `distance_bps` (e.g., `0.33523150389608725`), full `band_score`, and each populated timeframe's exact `latest_window_end_utc` value.

**Pass criteria:** All three fields (distance_bps, band_score, coverage freshness for each timeframe) appear in the tooltip; no rounding; no truncation.

---

### TC-09 — Clicking ranked row navigates to `/structure` with unchanged anchor markup

**Type:** browser
**Preconditions:** Frontend running; `/desk` page loaded with a ranked row (e.g., AAPL); the row's drill-in anchor element is visible.

**Steps:**
1. Inspect the `<Link data-testid="desk-row-drill-in">` element in the row using browser DevTools.
2. Record its `href`, `className` (especially `absolute inset-0`), and any other attributes.
3. Click anywhere in the row.
4. Wait for navigation to complete.
5. Verify the new URL.

**Expected outcome:** 
- Anchor's `href`, `absolute inset-0` class, and `data-testid` are unchanged from iteration 6.
- Click navigates to `/structure?symbol=AAPL&asof=<iso-datetime>` exactly as J-05 already verified.

**Pass criteria:** Anchor markup is byte-identical to the iteration 6 baseline; navigation URL matches the expected pattern.

---

### TC-10 — Hovering skipped row tooltip includes only coverage, no fabricated distance/score

**Type:** browser
**Preconditions:** Frontend running; `/desk` page loaded; at least one skipped member row is visible (a row with `distance_bps` and `band_score` fields absent, only coverage data present).

**Steps:**
1. Locate a skipped row (one with no distance/score values).
2. Position mouse pointer anywhere within that row.
3. Wait for the tooltip to appear.
4. Capture the tooltip text.

**Expected outcome:** Tooltip contains only the coverage-freshness fields (timeframe `latest_window_end_utc` values); no distance_bps or band_score values appear.

**Pass criteria:** Tooltip lists only the fields that exist for a skipped row; no fabricated values.

---

### TC-11 — Source-introspection guard test confirms drill-in anchor tooltip is built from row fields

**Type:** artifact
**Preconditions:** `apps/backend/tests/test_desk_ui_guards.py` (or the new guard test file) is present and executable.

**Steps:**
1. Run the F2 tooltip-composition guard test.
2. Verify it reads `apps/frontend/app/desk/page.tsx` and inspects the drill-in anchor's `title` attribute.
3. Confirm the test asserts the tooltip is built from `row.distance_bps`, `row.band_score`, and coverage `latest_window_end_utc`.
4. Run the seeded-violation counter-test (a version where the anchor title is removed or hardcoded to a static string).

**Expected outcome:** 
- Guard test passes on the correct implementation.
- Counter-test fails when the anchor's tooltip composition is broken.

**Pass criteria:** Guard test execution completes successfully; counter-test correctly fails on the violated condition.

---

### TC-12 — J-05.json step 2 selects history row by data-screen-date, not position

**Type:** artifact
**Preconditions:** File `runs/goal-session-desk/journey-scripts/J-05.json` exists and is valid JSON.

**Steps:**
1. Read the J-05.json file.
2. Navigate to step 2 (index 1).
3. Inspect the click target's definition.

**Expected outcome:** Step 2's click target is a CSS selector targeting `[data-testid="desk-history-row"][data-screen-date="2026-06-22"]` (or equivalent date-qualified selector), not a positional first-match on `{"testid": "desk-history-row"}`.

**Pass criteria:** The target uses a date-qualified selector; when replayed against a freshly-seeded backend, the script reaches the expected "Viewing the recorded screen for 2026-06-22" text.

---

### TC-13 — Browser: Cockpit Buyer Control panel settled and screenshotted

**Type:** browser
**Preconditions:** Frontend running at http://localhost:3000; backend running; `SIM-BUYER` strategy in the watchlist.

**Steps:**
1. Navigate to the Cockpit page (`/`).
2. Locate and select `SIM-BUYER` from the strategy list.
3. Wait for the "Buyer Control" panel to settle and render completely (no pending spinners).
4. Take a screenshot.

**Expected outcome:** The "Buyer Control" panel is visibly rendered and settled; the screenshot shows all controls and data without truncation or loading states.

**Pass criteria:** Screenshot captures the full settled panel; no loading spinners or placeholders visible.

---

### TC-14 — Browser: `/structure` Load for pinned AAPL as-of 2026-06-22 renders 300–302.4 wall

**Type:** browser
**Preconditions:** Frontend and backend running; AAPL data available for the target date.

**Steps:**
1. Navigate to `/structure`.
2. Enter AAPL as the symbol (or select from universe).
3. Set the as-of date to `2026-06-22T21:00:00Z`.
4. Click "Load".
5. Wait for the structure (tradable zones) to render.
6. Take a screenshot capturing the zone visualization.

**Expected outcome:** The structure chart renders the 300–302.4 wall with correct zone boundaries; the visualization is clear and complete.

**Pass criteria:** Screenshot shows the expected wall (300–302.4 region) rendered correctly; no error messages.

---

### TC-15 — Browser: Case Studies drill-in renders and is screenshotted

**Type:** browser
**Preconditions:** Frontend and backend running; `/structure` page already loaded with rendered data.

**Steps:**
1. On the `/structure` page, locate the Case Studies section.
2. Click the drill-in action (or link) for a case study row.
3. Wait for the Case Studies panel to open and render.
4. Take a screenshot of the open drill-in view.

**Expected outcome:** The Case Studies panel opens and displays its full drill-in content; no errors or incomplete rendering.

**Pass criteria:** Screenshot shows the complete drill-in panel without truncation or loading states.

---

### TC-16 — Browser: Edge Report panel in honest computed-or-not-computed state is screenshotted

**Type:** browser
**Preconditions:** Frontend and backend running; `/structure` page loaded; the Edge Report data may or may not be computed (both states are valid).

**Steps:**
1. On the `/structure` page, locate the Edge Report panel.
2. Observe whether it shows computed results or an honest "not computed yet" state.
3. Take a screenshot of the panel in its current state.

**Expected outcome:** The panel displays either:
   - Computed results (non-empty cells with data), or
   - An honest "Edge Report not computed yet" message.
   
   Never a fabricated or error-only cell.

**Pass criteria:** Screenshot shows the honest state without fabricated cells; no error messages if not computed.

---

### TC-17 — Kept routes are byte-identical to era-open baseline

**Type:** api
**Preconditions:** Both backend and frontend running; era-open baseline curl captures exist for `/`, `/structure`, `/meta/ui-routes`, `/research/taxonomy`.

**Steps:**
1. Run `curl -s GET http://localhost:8301/` and capture the response.
2. Compare to the era-open baseline capture byte-for-byte.
3. Repeat for `/structure`, `/meta/ui-routes`, `/research/taxonomy`.

**Expected outcome:** All four responses are byte-identical to the baseline (same JSON structure, same field values, same order).

**Pass criteria:** Diff shows zero byte differences for each route.

---

### TC-18 — Navigation structure: exactly 3 routes (Cockpit, Structure, Desk)

**Type:** api
**Preconditions:** Backend running at http://localhost:8301.

**Steps:**
1. Navigate the frontend and count the visible routes in the navigation (e.g., via the sidebar or top nav).
2. Verify programmatically: `curl -s GET http://localhost:8301/meta/ui-routes | jq '.routes | length'`.

**Expected outcome:** Exactly 3 routes visible and registered: `/` (Cockpit), `/structure` (Structure), `/desk` (Desk).

**Pass criteria:** Route count is exactly 3.

---

### TC-19 — MCP tool count: exactly 17 tools

**Type:** api
**Preconditions:** Backend running at http://localhost:8301; `app.mcp` module loaded.

**Steps:**
1. Run `python -c "import sys; sys.path.insert(0, '/home/dennis-chan/Git/tapeology/apps/backend'); import app.mcp; print(len(app.mcp.TOOL_NAMES))"`.
2. Verify the count matches 17.

**Expected outcome:** MCP tool count is exactly 17.

**Pass criteria:** Count equals 17.

---

### TC-20 — Backend suite passes with 1341+ collected, 1333+ passing, ≤8 skipped; fingerprint unchanged

**Type:** api
**Preconditions:** Backend source code is complete; all tests are executable; `TMPDIR` and temp stores are configured.

**Steps:**
1. Run the full backend test suite: `cd apps/backend && python -m pytest tests/ -v`.
2. Capture the test summary (passed, failed, skipped counts).
3. Run `python -c "from app.config import Config; print(Config().config_fingerprint())"` to verify the fingerprint.

**Expected outcome:** 
- Test summary shows ≥1341 collected, ≥1333 passing, ≤8 skipped, 0 failures.
- Fingerprint prints exactly `08e471b10130e1e2`.

**Pass criteria:** All test counts meet the floor; fingerprint is unchanged.

---

### TC-21 — J-01–J-05 remain passing via regression replay or LLM fallback

**Type:** browser
**Preconditions:** Golden journey scripts J-01.json through J-05.json exist; browser running; backend in fixture state.

**Steps:**
1. Replay J-01.json against the fixture backend.
2. Repeat for J-02, J-03, J-04, J-05.
3. For any replay that fails, use LLM fallback to verify the acceptance state (click path, element visibility).

**Expected outcome:** All five journeys complete successfully without regression; each demonstrates its already-recorded acceptance behavior.

**Pass criteria:** All 5 journeys pass; no new failures introduced by the F2 fix or MCP changes.

---

### TC-22 — Fresh J-04 or J-05 browser pass confirms F2 fix composite tooltip and unchanged click behavior

**Type:** browser
**Preconditions:** Frontend and backend running; `/desk` page with recorded screen data.

**Steps:**
1. Navigate to `/desk` and locate a ranked row.
2. Hover over the row to display the composite tooltip.
3. Take a screenshot of the hovering state.
4. Click the row to navigate to `/structure`.
5. Verify the navigation URL.
6. (Optional) Compare the screenshot to J-04/J-05 baselines to confirm no visual regression.

**Expected outcome:** 
- Composite tooltip is clearly visible on hover.
- Row click navigates to `/structure?symbol=<sym>&asof=<iso>` exactly as baseline.

**Pass criteria:** Hover tooltip is reachable; click behavior unchanged.

---

### TC-23 — Cumulative era diff has zero out-of-inventory changes

**Type:** artifact
**Preconditions:** Git branch `goal/desk` is the current branch; `main` is available as the baseline.

**Steps:**
1. Run `git diff main..HEAD --stat` to see the file changes.
2. Compare the changed files to the iteration scope (MCP module, desk page, test files, golden scripts).
3. Verify no unexpected files (e.g., config, external data, unrelated modules) are changed.

**Expected outcome:** All changed files belong to the expected scope:
   - `apps/backend/app/mcp/__init__.py`
   - `apps/backend/tests/test_mcp_server.py`
   - `apps/backend/tests/test_desk_ui_guards.py` (or new guard test)
   - `apps/frontend/app/desk/page.tsx`
   - `runs/goal-session-desk/journey-scripts/J-05.json`
   - `docs/handoffs/goal-desk-iter-7-dev.md`

**Pass criteria:** No out-of-inventory changes (changes outside the expected scope).

---

## Summary

**Total test cases:** 23
**API tests:** 10 (TC-01–TC-07, TC-17, TC-18, TC-19, TC-20)
**Browser tests:** 10 (TC-08–TC-10, TC-13–TC-16, TC-22)
**Artifact checks:** 3 (TC-11, TC-12, TC-23)

**Key verification gates:**
- MCP: exactly 17 tools; `desk_universe` and `desk_screen` byte-identical to curl in both empty and populated states.
- Frontend: F2 fix composite tooltip reachable on row hover; row click behavior unchanged; `/desk` rows (both ranked and skipped) display correct tooltips.
- Golden: J-05.json step 2 selects by date, not position.
- Regression: J-01–J-05 all pass; kept routes byte-identical; fingerprint unchanged.
- Coverage: Cockpit, Structure, Desk pages all verified; nav = 3 routes; era diff contains no out-of-inventory changes.
