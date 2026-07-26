# goal-desk-iter-4 Functional Test Plan

**Phase:** goal-desk-iter-4  
**Date:** 2026-07-25  
**Frontend Present:** yes

## Phase Goal

The operator can open a new third page `/desk`, click "Run Screen" to compute a desktop briefing, and read a ranked list of tradable walls across the registered universe with full provenance tracking — adding a third permanent top-nav entry (Cockpit · Structure · Desk).

## Test Cases

### TC-01 — Empty state on initial load

**Type:** browser  
**Preconditions:** Fixture-scoped backend is running with a registered universe but no screen has been computed yet.

**Steps:**
1. Navigate to `http://localhost:3000/desk`
2. Wait for page load to complete
3. Observe the rendered state

**Expected outcome:** Page shows the exact text "Desk screen not computed yet." and an enabled "Run Screen" button.  
**Pass criteria:** Text appears verbatim; button is clickable and not disabled; screenshot shows the complete empty state with nav bar displaying Cockpit · Structure · Desk.

---

### TC-02 — Run Screen trigger and single-flight refusal

**Type:** browser  
**Preconditions:** `/desk` page is loaded with empty state (no screen computed).

**Steps:**
1. Click the "Run Screen" button
2. Immediately observe the button state change to reflect progress
3. While the compute is running (`state === "running"`), click "Run Screen" again
4. Observe the UI response to the second click

**Expected outcome:** First click fires `POST /research/desk/screen/compute` with `screen_date` set to the client's today. Button enters a running/progress state. Second click while computing observes the SAME in-flight job (no new POST initiated); the UI shows the same job ID and status.  
**Pass criteria:** Only one POST request observed in network log during the sequence; same job snapshot returned for both clicks; screenshot shows progress state with a running indicator (pulsing dot or similar).

---

### TC-03 — Populated briefing table with honest skipped grouping

**Type:** browser  
**Preconditions:** A screen compute has reached terminal state `done` and the page has refetched the latest snapshot.

**Steps:**
1. Observe the rendered briefing table
2. Verify each column header and row data
3. Look for the skipped-members section below the ranked rows
4. Verify grouping by skip reason

**Expected outcome:** Table renders ranked rows with columns: symbol, side, band-class chip (reading "nearest same-class band" where applicable), distance-bps chip, band score, per-timeframe coverage badge (each timeframe's `has_bars` rendered honestly), tick-evidence badge. Skipped members render below in a distinct section, grouped by reason (`no_bars` vs `no_basis`). Even when `rows` is empty but `skipped` is not empty, both sections render.  
**Pass criteria:** All row data matches verbatim from `GET /research/desk/screen`'s `latest.rows` and `latest.skipped`; chip text is exact ("nearest same-class band"); per-timeframe badges show truthful boolean values per iter-2's lesson; screenshot shows table structure.

---

### TC-04 — Provenance line accuracy

**Type:** browser  
**Preconditions:** Screen snapshot is rendered on `/desk`.

**Steps:**
1. Locate the provenance line below the briefing table
2. Read each field: universe snapshot id, date, `as_of`, `config_fingerprint`, bar-store freshness value
3. Cross-reference against the backend `GET /research/desk/screen` response

**Expected outcome:** Provenance line displays all five values verbatim from the snapshot: universe snapshot id + date, `as_of`, `config_fingerprint`, and bar-store freshness labeled "window last requested" (never "last bar").  
**Pass criteria:** Each field matches exactly; label for freshness is "window last requested"; all values match the response JSON verbatim.

---

### TC-05 — Screen-history list with metadata-only display

**Type:** browser  
**Preconditions:** Multiple screens have been computed in the session or fixture.

**Steps:**
1. Scroll to the screen-history section
2. Observe each entry in the list
3. Attempt to click on a history entry

**Expected outcome:** Each entry shows the screen's date + rows/skipped counts read verbatim from `GET /research/desk/screen`'s meta-only `screens` list. No click interaction is available on entries; no per-entry full-row data is fetched.  
**Pass criteria:** Entries display date and counts correctly; entries are read-only (no click handlers); no additional GET requests fire when hovering or focusing history items.

---

### TC-06 — Navigation bar displays three routes

**Type:** browser  
**Preconditions:** Application is running with `/desk` page built.

**Steps:**
1. Open any page (e.g., `/desk`)
2. Observe the top navigation bar
3. Verify the route list via `GET /meta/ui-routes` API call

**Expected outcome:** Top navigation renders three entries in order: Cockpit · Structure · Desk. API endpoint returns exactly three routes: `[{path: "/", label: "Cockpit"}, {path: "/structure", label: "Structure"}, {path: "/desk", label: "Desk"}]`.  
**Pass criteria:** Nav bar shows three links in exact order; API response contains exactly three entries with correct paths and labels; screenshot taken in each major test (TC-01, TC-02, TC-03 screenshots all show the nav bar).

---

### TC-07 — Reused snapshot detection

**Type:** api  
**Preconditions:** A desk-screen compute job has been completed and the snapshot persisted. A second compute is triggered with the same 5-pin key (same universe, screen date, as_of, config_fingerprint, bar_store_signature).

**Steps:**
1. Trigger `POST /research/desk/screen/compute` with screen_date = today
2. Poll `GET /research/desk/screen/compute` until state reaches terminal
3. Inspect the response snapshot for `reused` and `screen_id` fields
4. Verify `ScreenStore.list()` shows no new file was created

**Expected outcome:** Compute job resolves with `reused: true` and `screen_id` equal to the EXISTING snapshot's id. `ScreenStore.list()` shows no new file was written; the file count remains unchanged.  
**Pass criteria:** `reused === true`; `screen_id` equals the pre-existing snapshot's id (not a new UUID); file count before and after POST is identical; exact curl: `curl -s http://localhost:8301/research/desk/screen/compute | jq '.reused'` outputs `true`.

---

### TC-08 — Fresh snapshot on first compute

**Type:** api  
**Preconditions:** Backend is in a clean state with universe registered but no screen snapshot exists yet.

**Steps:**
1. Trigger `POST /research/desk/screen/compute` with screen_date = today
2. Poll `GET /research/desk/screen/compute` until state reaches terminal
3. Inspect the response snapshot for `reused` and `screen_id` fields
4. Verify a new file was created in `ScreenStore`

**Expected outcome:** Compute job resolves with `reused: false` and `screen_id` set to a new UUID. A new file is written to the screen store.  
**Pass criteria:** `reused === false`; `screen_id` is a valid UUID (not null); file count increases by 1; curl: `curl -s http://localhost:8301/research/desk/screen/compute | jq '.screen_id'` returns a non-null UUID.

---

### TC-09 — No-universe refusal

**Type:** api  
**Preconditions:** Backend is running with NO universe snapshot registered.

**Steps:**
1. Trigger `POST /research/desk/screen/compute` with screen_date = today
2. Capture the HTTP response status and body
3. Verify `ScreenStore.list()` before and after the call

**Expected outcome:** Request returns an HTTP 4xx status (e.g., 422 or 400) with an error message naming the missing universe. No background job starts. `ScreenStore.list()` returns zero records both before and after the call.  
**Pass criteria:** HTTP status is 4xx; error message contains "universe" (case-insensitive); no job is queued; file count unchanged; curl: `curl -s -X POST http://localhost:8301/research/desk/screen/compute -d '{"screen_date":"2026-07-25"}' -H 'Content-Type: application/json' -w '%{http_code}'` returns 400–499 range.

---

### TC-10 — Corrupt universe snapshot rejection

**Type:** api  
**Preconditions:** A universe snapshot file exists on disk at a content-checksum path but the file is corrupted (e.g., truncated or modified).

**Steps:**
1. Manually create a corrupted snapshot file at a known checksum path (e.g., by truncating an existing valid file)
2. Trigger `UniverseStore.record()` with content that hashes to the same checksum
3. Observe the exception raised
4. Verify the damaged file remains unchanged and no second file is written

**Expected outcome:** `UniverseStore.record()` raises an integrity error (mirroring `ScreenStore.record`'s guard). The corrupted file is NOT overwritten. No secondary file is created.  
**Pass criteria:** Exception message references integrity/corruption; file byte-count before and after is identical; exactly one file exists at that checksum path; the error is logged without silent failure.

---

### TC-11 — Single-flight job lock

**Type:** api  
**Preconditions:** A desk-screen compute job is actively running (`state === "running"`).

**Steps:**
1. While the first job runs, trigger `POST /research/desk/screen/compute` a second time
2. Capture the response snapshot

**Expected outcome:** Second POST returns a snapshot with `started: false` and the same job id as the first. No concurrent job is created.  
**Pass criteria:** `started === false`; returned `id` matches the original job; job count in the compute manager remains 1; curl: `curl -s -X POST http://localhost:8301/research/desk/screen/compute ...` returns `started: false` when called mid-flight.

---

### TC-12 — Top-up compute with live progress

**Type:** browser  
**Preconditions:** `/desk` page is open.

**Steps:**
1. Click the "Top-up" button
2. Observe the progress indicator while `state === "running"` (pairs_done / pairs_total)
3. While running, click "Cancel"
4. Observe the state transition to cancelling/cancelled

**Expected outcome:** Click fires `POST /research/desk/topup/compute`. Live progress displays `pairs_done`/`pairs_total` while running. Cancel button posts `/research/desk/topup/compute/cancel` and UI reflects a cancelling/cancelled state.  
**Pass criteria:** Progress numbers update in real-time; Cancel button is functional and sends the correct POST; UI state transitions to cancelled; screenshot shows the progress UI with live counter.

---

### TC-13 — Copy discipline on new page

**Type:** artifact  
**Preconditions:** All frontend source under `apps/frontend/app/desk` exists and the linter is configured.

**Steps:**
1. Run `pytest tests/test_copy_discipline.py::test_lint_frontend_source_literals_are_clean -v`
2. Capture the output, specifically any violations in the `/desk` module

**Expected outcome:** The linter reports zero violations. No imperative language ("buy", "sell", "opportunity"), no predictions ("will", "should"), no certainty claims ("guaranteed").  
**Pass criteria:** Test passes with exit code 0; the output shows zero violations for `apps/frontend/app/desk/page.tsx`; lint message reads "OK" or "0 violations found".

---

### TC-14 — Chip copy accuracy (no _select_best_band diff)

**Type:** artifact  
**Preconditions:** The `/desk` page renders a screen row where the headline band is not the highest-scoring same-class band.

**Steps:**
1. Inspect the rendered band-class chip for that row
2. Read the chip text
3. Verify `desk_screen.py`'s `_select_best_band` function in the codebase

**Expected outcome:** Chip reads "nearest same-class band" (exact text from assumptions.md iter-4 entry 1). `_select_best_band` function shows zero lines changed from before this iteration.  
**Pass criteria:** Chip text is exact; `git diff` of `desk_screen.py` shows `_select_best_band` function is byte-identical; no conditional logic or ranking changes inside the function.

---

### TC-15 — Route count assertions updated

**Type:** artifact  
**Preconditions:** `apps/backend/tests/test_meta_routes.py` file exists and has been updated.

**Steps:**
1. Read `test_meta_routes.py` and find `test_ui_routes_lists_exactly_the_live_routes` and `test_ui_routes_top_bar_entries_match_the_rendered_nav_set`
2. Verify the hardcoded route counts in these tests
3. Run the test suite: `pytest apps/backend/tests/test_meta_routes.py -v`

**Expected outcome:** Tests expect exactly three routes (`/`, `/structure`, `/desk`) in order. Tests pass without assertion errors.  
**Pass criteria:** Both test functions contain the 3-route set; test execution passes; no assertion about route count fails; commit includes both the `UI_ROUTES` change in `app/meta.py` and the assertion updates in the same change.

---

### TC-16 — J-07 regression: golden replay step 8

**Type:** browser  
**Preconditions:** Backend is fixture-scoped with `tradability_cache` pre-warmed for AAPL as-of `2026-06-22T21:00:00Z`. `journey-scripts/J-07.json` step 8 has `timeout_ms: 20000` set. Deterministic replay runner is configured.

**Steps:**
1. Warm the cache by running one `GET /research/structure?symbol=AAPL&as_of=2026-06-22T21:00:00Z` (or `/research/tradability?symbol=AAPL&as_of=2026-06-22T21:00:00Z`)
2. Run the deterministic replay for J-07: `demo_runner.py journey-scripts/J-07.json`
3. Monitor step 8's execution and assertion result

**Expected outcome:** Step 8's expected band-boundary text (a plain `<td data-testid="tradable-band-range">` cell) is observed within the `20000` ms timeout. No golden false-negative.  
**Pass criteria:** Step 8 assertion passes; timeout is not exceeded; the rendered AAPL band range (`300–302.4` or similar, per the registered fixture) matches the assertion; if replay fails on step 8 only while the LLM fallback passes, treat as a golden false-negative and flag without marking J-07 as regressed.

---

### TC-17 — Frozen research modules (zero diff)

**Type:** artifact  
**Preconditions:** The phase implementation is complete.

**Steps:**
1. Run `git diff HEAD -- apps/backend/app/research/config.py apps/backend/app/research/tradability.py apps/backend/app/research/levels.py apps/backend/app/research/bars.py apps/backend/app/research/bar_index.py`
2. Verify that all five files show zero changed lines
3. Run `python3 -c "from app.research.config import Config; print(Config().config_fingerprint())"`

**Expected outcome:** No diff output (files are byte-identical). `config_fingerprint()` still prints `08e471b10130e1e2`.  
**Pass criteria:** Git diff output is empty or shows no actual changes; fingerprint value is exactly `08e471b10130e1e2`; no logic or constant was altered in any of the five modules.

---

### TC-18 — All-skipped screen rendering

**Type:** browser  
**Preconditions:** A screen compute completes with `rows: []` (no tradable members) and `skipped: [...]` (some members were skipped).

**Steps:**
1. Wait for the compute to finish
2. Observe the `/desk` page render
3. Look for the ranked-rows section (which should be empty)
4. Look for the skipped-members section (which should be populated)

**Expected outcome:** Both the empty ranked-rows section and the populated skipped-members section are rendered. The page does NOT show the "Desk screen not computed yet." message (that message renders only when `latest === null`).  
**Pass criteria:** Table header/structure is visible but with zero data rows; skipped section shows grouped entries; "not computed yet" message is absent; the two sections are visually distinct.

---

### TC-19 — Page-load GETs only (no POST on mount)

**Type:** browser  
**Preconditions:** `/desk` page is about to be loaded; network monitoring is active.

**Steps:**
1. Open DevTools Network tab
2. Navigate to `http://localhost:3000/desk`
3. Wait for all initial requests to complete
4. Filter for requests to `/research/desk/*` endpoints

**Expected outcome:** Only GET requests fire on mount: `GET /research/desk/screen`, `GET /research/desk/screen/compute`, and `GET /research/desk/topup/compute`. Zero POST requests without an explicit button click.  
**Pass criteria:** Network log shows no POST requests during initial page load; only GET requests are present; clicking Run Screen then triggers a POST to `/research/desk/screen/compute`.

---

### TC-20 — Suite pass count non-decreasing

**Type:** api  
**Preconditions:** Phase implementation is complete. Backend is running.

**Steps:**
1. Run the full backend test suite: `pytest apps/backend/tests -v --tb=short`
2. Capture the final pass/skip/fail counts
3. Verify against the floor: 1299 passed / 8 skipped

**Expected outcome:** Test suite reports a pass count ≥ 1299, skip count ≥ 8, and fail count = 0. No new test failures introduced.  
**Pass criteria:** Exit code is 0; summary line reads "passed" with count ≥ 1299; zero failures; existing tests in `desk_universe.py`, `desk_coverage.py`, `desk_topup_compute.py`, `desk_screen.py` all still pass except the new tests added (corrupt-file guard, no-universe refusal).

---

### TC-21 — Backend unreachable during poll (no fabrication)

**Type:** browser  
**Preconditions:** A screen compute is running and the browser is polling `GET /research/desk/screen/compute`.

**Steps:**
1. Start a screen compute (click Run Screen)
2. While polling, stop or disconnect the backend (simulate a network failure)
3. Observe the UI behavior during the next poll attempt

**Expected outcome:** The UI keeps the last known snapshot state (does not update). No fabricated snapshot is displayed. The UI remains stable with the last known data.  
**Pass criteria:** UI state does not change to a new/empty snapshot; no error message invents data; the last known `state` value persists on screen; mirrors the `fetchEdgeReportCompute` `{ok: false, data: null}` error fold.

---

## Summary

**Total test cases:** 21

**By type:**
- Browser tests: 9 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-12, TC-16, TC-18, TC-19, TC-21)
- API tests: 9 (TC-07, TC-08, TC-09, TC-10, TC-11, TC-20)
- Artifact tests: 3 (TC-13, TC-14, TC-15, TC-17)

**Coverage mapping:**
- Empty state & initialization: TC-01, TC-19
- Screen compute lifecycle: TC-02, TC-07, TC-08, TC-11
- Data display accuracy: TC-03, TC-04, TC-05, TC-14, TC-18
- Navigation & routes: TC-06, TC-15
- Error handling & guards: TC-09, TC-10, TC-21
- Regression verification: TC-16, TC-17
- Quality & copy discipline: TC-13
- Top-up feature: TC-12
- Suite health: TC-20
