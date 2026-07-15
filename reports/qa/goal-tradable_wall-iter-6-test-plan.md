# goal-tradable_wall-iter-6 Functional Test Plan

**Phase:** goal-tradable_wall-iter-6 (J-05: `/structure` decluttered)
**Date:** 2026-07-15
**Frontend Present:** yes

## Phase Goal

Render the Tradable Map (≤10 quality-scored bands) as the default view on `/structure`, with raw 1,800-level rendering behind an off-by-default toggle; add a Case Studies browser (registry + per-event drill-in) and an Edge Report section — every value read verbatim from backend endpoints, recomputing nothing in the browser.

## Test Cases

### TC-01 — Backend cache atomicity: no torn read under concurrent callers

**Type:** api
**Preconditions:** Backend running; `_SCAN_CACHE` cache is empty (cold start).

**Steps:**
1. Spawn two concurrent HTTP client threads.
2. Both threads simultaneously call `GET /research/setups` with a cold cache (same config hash).
3. Both threads complete; capture the responses.

**Expected outcome:** Both threads receive a complete `{ok: true, data: [...]}` response with identical results. No thread observes `{ok: false}` or `{ok: true, data: null}`. No 500 error.
**Pass criteria:** Both threads receive HTTP 200 with identical byte-equal payload; no 500 error; no `None` result in response; cache query spy confirms the cold scan runs exactly once.

---

### TC-02 — Tradable Map renders by default on `/structure` load

**Type:** browser
**Preconditions:** Frontend running at `http://localhost:3000`; backend populated with 12-symbol panel data; symbol input shows AAPL; date picker shows 2026-06-22 (the pinned session).

**Steps:**
1. Navigate to `/structure` page.
2. Load form is displayed with symbol AAPL and date 2026-06-22 already filled.
3. Wait for the Tradable Map section to render (loading state clears).
4. Inspect the map table: count visible rows (bands).
5. Inspect the chart: verify candle rendering + price area overlays (band zones).

**Expected outcome:** Page loads; Tradable Map is the first rendered section (not raw levels). The bands table displays ≤10 rows. Chart shows candlesticks with distinct colored price-area bands overlaid. Each band row shows: price range (`price_low`–`price_high`), `side`, `quality_score`, `class`, `member_count`, `round_number` flag, and all values are byte-identical to `GET /research/tradability` JSON.
**Pass criteria:** Bands table has ≤10 rows; chart renders candles + area overlays; at least one band's range spans the ~300–302 rejection cluster (AAPL 06-22 pinned case); `quality_score` and `class` fields match endpoint JSON verbatim; screenshot shows map as default (not levels/zones below it).

---

### TC-03 — "Raw levels" toggle off by default; on restores era-5 rendering unchanged

**Type:** browser
**Preconditions:** `/structure` page is loaded with AAPL 2026-06-22; Tradable Map is visible; raw levels section should not be visible.

**Steps:**
1. Locate the "Show raw levels" toggle control (off by default).
2. Verify toggle is in OFF state; raw levels / confluence zones panels are NOT rendered.
3. Click toggle to ON.
4. Wait for re-render; inspect the panels.
5. Verify the two panels (S/R levels + confluence zones) are now visible with the same visual style and data as before this iteration (pre-iter-6 rendering).
6. Click toggle back to OFF.
7. Verify raw panels vanish; Tradable Map remains visible.

**Expected outcome:** Toggle defaults to OFF; clicking ON renders the era-5 raw levels + confluence zones panels verbatim (byte-identical rendering to the pre-iter-6 state). Toggle is stateful within the page session. Clicking OFF removes the panels, returning focus to the Tradable Map.
**Pass criteria:** Toggle exists and defaults to OFF; raw panels absent when OFF; raw panels present when ON with all columns/data unchanged from era-5; toggle can be toggled multiple times without error; screenshot of both states.

---

### TC-04 — Case Studies section renders registry from `GET /research/setups`

**Type:** browser
**Preconditions:** `/structure` loaded with AAPL 2026-06-22; backend has setups events in response.

**Steps:**
1. Scroll to the Case Studies section.
2. Verify the registry table is rendered with columns: symbol, session_date, band_range, side, class, reaction, forward_returns.
3. Verify there are at least 10 rows visible (events exist for AAPL).
4. Locate the row with symbol AAPL, session_date 2026-06-22, and band range covering ~300–302.
5. Verify each column's value matches the corresponding field in `GET /research/setups` JSON (verbatim).

**Expected outcome:** Case Studies table is rendered below the Tradable Map. The pinned AAPL 2026-06-22 ~300 event is present in the list. All column values (reaction, forward_returns, etc.) are byte-identical to the endpoint payload.
**Pass criteria:** Table renders with ≥10 rows; pinned AAPL 06-22 ~300 event is present; all displayed values match endpoint JSON verbatim; table is sortable/scrollable without error; screenshot shows table.

---

### TC-05 — Case Studies filters (symbol and reaction) work correctly

**Type:** browser
**Preconditions:** Case Studies section is visible with full registry; at least one event exists for multiple symbols and reactions.

**Steps:**
1. Locate the symbol filter control (if present) or verify filtering is available.
2. Apply filter: symbol = AAPL (or use endpoint's `?symbol=AAPL` param).
3. Verify table updates; only AAPL events remain.
4. Apply filter: reaction = rejected (if filter UI present).
5. Verify table updates; only AAPL + rejected events remain.
6. Clear filters; verify full registry returns.

**Expected outcome:** Symbol filter reduces rows to AAPL events only. Reaction filter further reduces to rejected events. Clearing filters restores the full registry. Filtered data matches the backend's `GET /research/setups?symbol=AAPL&reaction=rejected` response.
**Pass criteria:** Filters are wired to endpoint parameters (or client-side filters accurately reflect endpoint rows); filtering is instant and correct; clearing filters restores the full list; screenshot of filtered state.

---

### TC-06 — Case Studies drill-in shows detail for a pinned event

**Type:** browser
**Preconditions:** Case Studies section is visible; the pinned AAPL 2026-06-22 ~300 event is visible in the table.

**Steps:**
1. Click the row for the pinned AAPL 2026-06-22 ~300 event.
2. Wait for drill-in detail to open (modal or expanded panel).
3. Verify the drill-in displays:
   - event `id`
   - band range (price_low–price_high)
   - `reaction` field (should be `rejected` for the pinned case)
   - `forward_returns` array (should show negative values for the pinned case)
   - `tape_timeline` array (list of five-state tape records, or empty list if not recorded)
4. Verify all fields are read verbatim from `GET /research/setups/{id}` JSON.
5. Close the drill-in.

**Expected outcome:** Drill-in detail opens and shows all fields from the endpoint payload byte-identically. The pinned event shows `reaction: rejected` and negative forward returns. `tape_timeline` is either populated (if a credentialed recording exists) or an empty list (honest empty state).
**Pass criteria:** Drill-in opens without error; `reaction` field shows `rejected`; `forward_returns` array is negative; `tape_timeline` is present (even if empty); all values match `GET /research/setups/{id}` JSON verbatim; screenshot of drill-in open.

---

### TC-07 — Case Studies drill-in shows recency-boundary event with truncated-horizon disclosure

**Type:** browser
**Preconditions:** Case Studies registry is visible; at least one recency-boundary event exists (check for `reaction_boundary_truncated: true` in the endpoint JSON); such events sit near the most-recent stored session for a symbol.

**Steps:**
1. Scan the Case Studies table for an event near the most-recent session (e.g., AAPL 2026-07-13 or similar, depending on stored data).
2. If a boundary event is found (should have `reaction_boundary_truncated: true`), click to open its drill-in.
3. Verify the drill-in displays:
   - A distinct disclosure: "Reaction read at a truncated {N}-bar horizon" (or similar honest phrasing).
   - `effective_reaction_horizon_bars` value (e.g., 10 or fewer bars, vs. the standard ∞ or large value).
   - The `reaction` label, NOT presented as a full-horizon reaction (copy must say "truncated").
4. Verify this differs visually from a non-boundary event drill-in (which has no truncation note).

**Expected outcome:** Boundary-event drill-in includes an honest, distinct truncation disclosure. The `effective_reaction_horizon_bars` value is shown. The `reaction` label is contextually marked as truncated, never presented as full-horizon. Non-boundary events have no such note.
**Pass criteria:** Boundary event found and drill-in opened; truncation note is present and clear; `effective_reaction_horizon_bars` is displayed; `reaction_boundary_truncated: true` field is present in the JSON; screenshot of boundary drill-in alongside non-boundary for comparison.

---

### TC-08 — Case Studies drill-in displays `tape_timeline` correctly

**Type:** browser
**Preconditions:** A Case Studies event is open in the drill-in; the event may or may not have a `tape_timeline` (depends on whether the event was credentialed-recorded).

**Steps:**
1. In the drill-in, locate the `tape_timeline` section.
2. If `tape_timeline` is an empty array: verify an honest empty-state message is shown (e.g., "No recorded tape data for this event").
3. If `tape_timeline` is populated: verify the list of tape records is rendered (each record shows the tape state: `buyer_control`, `seller_control`, etc.).
4. Verify all tape-state values are byte-identical to the endpoint JSON; no recomputation or filtering in the browser.

**Expected outcome:** Empty timeline shows honest empty state. Populated timeline shows all tape records as served. No tape records are fabricated, filtered, or recomputed in the browser.
**Pass criteria:** Empty timeline renders honest empty-state message; populated timeline shows all records verbatim; screenshot of both states (if available); no fabricated states.

---

### TC-09 — Edge Report section renders verbatim from `GET /research/edge-report`

**Type:** browser
**Preconditions:** `/structure` loaded; Edge Report section should render below Case Studies.

**Steps:**
1. Scroll to the Edge Report section.
2. Verify the report is rendered with columns for: strategy_id, band_class, band_side, reaction, feed, n (sample count), R (return metric), $ (PnL), `insufficient_sample` flag, and full register.
3. If the report is empty / all-`insufficient_sample`: verify an honest empty-state message is shown (e.g., "No sufficient data for edge report on the keyless fixture" or similar).
4. If the report has populated cells: verify each cell's values (n, R, $, register) are byte-identical to the endpoint JSON.

**Expected outcome:** Edge Report renders all cells / empty state verbatim from the endpoint. No cells are fabricated. Empty report is a first-class render, not hidden or missing.
**Pass criteria:** Report is present and visible; if empty, shows honest empty-state message; if populated, all cell values match endpoint JSON verbatim; screenshot shows report (including empty state if applicable).

---

### TC-10 — Edge Report displays `insufficient_sample` cells honestly

**Type:** browser
**Preconditions:** Edge Report section is visible; the endpoint response includes cells with `insufficient_sample: true`.

**Steps:**
1. Locate any cell with `insufficient_sample: true` in the report.
2. Verify the cell renders with a visual or text indicator (e.g., "Insufficient sample" label or grayed-out appearance).
3. Verify the $ / R values in that cell are NOT suppressed or hidden; they may be shown as null/N/A or as-is per the endpoint.
4. Verify the `insufficient_sample` flag is shown explicitly, never as a silent missing value.

**Expected outcome:** Cells with `insufficient_sample: true` render honestly, showing the flag explicitly. Values are not hidden or fabricated.
**Pass criteria:** `insufficient_sample` flag is visible in each affected cell; values are shown as-is from the endpoint (null/N/A or numbers); screenshot shows at least one `insufficient_sample` cell.

---

### TC-11 — Edge Report renders `null` baseline and full register

**Type:** browser
**Preconditions:** Edge Report section is visible; the endpoint response includes `null_baseline` and `register` fields.

**Steps:**
1. Locate the null baseline row/section in the Edge Report.
2. Verify the `null_baseline` values (n, R, $) are displayed prominently or in a distinct row.
3. Locate the full register section (e.g., a table or list of all trades).
4. Verify the register shows each trade's entry/exit/PnL (or equivalent) with all fields from the endpoint.
5. Verify all register values are byte-identical to the endpoint JSON.

**Expected outcome:** Null baseline is shown prominently. Full register is visible below the edge-report cells. All values match the endpoint payload verbatim.
**Pass criteria:** Null baseline is distinct and visible; register is rendered below cells; register values match endpoint JSON verbatim; screenshot shows both sections.

---

### TC-12 — Malformed `as_of` parameter returns 422 and is surfaced honestly

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. Call `GET /research/tradability?symbol=AAPL&as_of=invalid-date` (malformed date).
2. Capture the HTTP status code and response body.

**Expected outcome:** HTTP 422 with `detail` field (or error message) indicating invalid date format.
**Pass criteria:** Status code is 422; response includes `detail` field explaining the error; no 200 OK with default/silent behavior.

---

### TC-13 — Tradability endpoint unreachable or non-200 renders honest degraded panel

**Type:** browser
**Preconditions:** Frontend running; backend service is stopped or the `/research/tradability` endpoint returns 500.

**Steps:**
1. Stop the backend service (or mock a 500 response).
2. Navigate to `/structure` with a valid symbol and date.
3. Wait for the Tradable Map section to load.
4. Verify an honest degraded/error panel is shown (e.g., "Unable to load tradability data" with the backend's error `detail` if available).
5. Verify no cached or fabricated data is shown.

**Expected outcome:** Degraded panel shows an honest error message. The backend's error `detail` is surfaced verbatim. No partial, stale, or fabricated map is rendered.
**Pass criteria:** Error panel is visible and clear; backend `detail` is shown (if available); no cached data leaks; screenshot of error state.

---

### TC-14 — Setups/Edge-Report unreachable renders honest degraded panels

**Type:** browser
**Preconditions:** Frontend running; backend Case Studies / Edge Report endpoints return 500 or are unreachable.

**Steps:**
1. Simulate the backend `/research/setups` or `/research/edge-report` endpoints returning 500.
2. Navigate to `/structure`.
3. Wait for the Case Studies and Edge Report sections to attempt load.
4. Verify each section that fails shows an honest degraded panel with the backend's error message.
5. Verify the Tradable Map section (if its endpoint succeeds) renders independently without cross-contamination.

**Expected outcome:** Failed sections show honest error panels. Successful sections (if any) render independently. No stale cache or fabricated data.
**Pass criteria:** Error panels visible in failed sections; successful sections render unaffected; screenshot of degraded states.

---

### TC-15 — `FeedBasisBadge` (era-5 provenance) still renders and functions

**Type:** browser
**Preconditions:** `/structure` loaded; the era-5 Fetch control and provenance badge are present below the new sections.

**Steps:**
1. Scroll down past the new sections (Tradable Map, Case Studies, Edge Report).
2. Locate the era-5 Fetch control (button: "Fetch from Yahoo Finance") and the `FeedBasisBadge` showing the data source.
3. Verify both are rendered and unchanged from era-5.
4. Click the fetch button (optional: verify it triggers a data refresh without error).

**Expected outcome:** Fetch control and badge are visible and unchanged. Clicking the button does not error. The badge correctly identifies the data source.
**Pass criteria:** Fetch button and badge are present; button is clickable; no errors on click; screenshot shows both.

---

### TC-16 — Era-5 Registry and Comparison sections intact and repositioned below new sections

**Type:** browser
**Preconditions:** `/structure` loaded; scroll to bottom of page.

**Steps:**
1. Scroll to the bottom of the page.
2. Verify the era-5 Registry section is still present with all its data and controls.
3. Verify the Comparison section is still present with the v1 vs. structure_tape comparison unmodified.
4. Verify their visual style and data are byte-identical to era-5 (no changes to their rendering).

**Expected outcome:** Both sections are present, repositioned below the new sections (Tradable Map, Case Studies, Edge Report), and unchanged.
**Pass criteria:** Both sections present; data and styling unchanged; screenshot shows both sections.

---

### TC-17 — No client recomputation of band scores, reactions, or forward returns

**Type:** artifact
**Preconditions:** Browser with DevTools open; `/structure` page loaded with data; network tab captured.

**Steps:**
1. Capture the network traffic for `/research/tradability`, `/research/setups`, and `/research/edge-report` responses.
2. Extract the `quality_score`, `class`, `reaction`, and `forward_returns` values from each response JSON.
3. Inspect the rendered page DOM for the same fields.
4. Use browser DevTools to trace the React component rendering and verify no recalculation or transformation is applied.
5. Compare the rendered text (via `String(value)`) to the JSON values.

**Expected outcome:** Every displayed value is verbatim from the endpoint JSON. No recomputation, rounding, or transformation is applied in the browser.
**Pass criteria:** Rendered values byte-equal endpoint JSON values; React component tree shows no calculation between JSON load and render; screenshot of DevTools network + DOM comparison.

---

### TC-18 — Concurrent cold-cache calls to `/setups` + `/setups/{id}` + `/edge-report` from page load

**Type:** api
**Preconditions:** Backend running; `/research/setups`, `/research/setups/{id}`, and `/research/edge-report` cache is cold.

**Steps:**
1. Clear the backend cache (restart backend or force-clear `_SCAN_CACHE`).
2. Load `/structure` page, which will trigger concurrent calls to all three endpoints.
3. Monitor the network requests and verify all three complete without 500 errors.
4. Verify the page renders all three sections without error.
5. Verify the cache write in `setups.py:377-378` was atomic (no torn reads).

**Expected outcome:** All three requests complete with 200 status. No 500 errors. Page renders all sections. Backend logs show the scan runs exactly once (no duplicate scans due to torn reads).
**Pass criteria:** All three endpoints return 200; page renders successfully; backend spy/test confirms cache write was atomic (no torn read); screenshot of page loading.

---

### TC-19 — Response shapes match documented types (TypeScript compliance)

**Type:** artifact
**Preconditions:** Frontend code is built; types are compiled without errors.

**Steps:**
1. Run TypeScript compiler on `apps/frontend/lib/types.ts` and the new API client functions.
2. Verify no type errors for the four new functions: `fetchTradability`, `fetchSetups`, `fetchSetupDetail`, `fetchEdgeReport`.
3. Verify return types are `{ok, data, error}` shaped (or named-field equivalent).
4. Verify the returned `data` type mirrors the backend JSON schema for each endpoint.

**Expected outcome:** TypeScript compilation succeeds with zero errors. All return types are correctly defined. No `any` casts or `@ts-ignore` suppressions in the new code.
**Pass criteria:** No TypeScript errors; type definitions match backend schema; screenshot of compiler output (zero errors).

---

### TC-20 — Raw levels toggle state persists across navigate-away and return

**Type:** browser
**Preconditions:** `/structure` loaded with AAPL 2026-06-22; raw levels toggle is ON.

**Steps:**
1. Toggle "Show raw levels" to ON.
2. Verify raw levels panels render.
3. Navigate to another page (e.g., `/performance`).
4. Return to `/structure` (by clicking back or navigating directly).
5. Verify the toggle state is restored (ON) and raw levels panels are visible.

**Expected outcome:** Toggle state persists across page navigation (via localStorage or React state + route URL param). User does not have to re-toggle on return.
**Pass criteria:** Toggle state is OFF initially; ON after user toggle; persists across navigate-away and return; screenshot of both states.

---

## Summary

**Total test cases:** 20
- **API tests:** 3 (TC-01, TC-12, TC-18)
- **Browser tests:** 14 (TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-13, TC-14, TC-15, TC-16, TC-20)
- **Artifact checks:** 3 (TC-17, TC-19, combined DevTools + TypeScript)

**Key Coverage:**
- Backend atomicity (concurrent cache safety) — TC-01, TC-18
- Frontend render correctness (Tradable Map, Case Studies, Edge Report) — TC-02, TC-04, TC-09
- User interactions (toggle, filters, drill-in) — TC-03, TC-05, TC-06, TC-07, TC-08
- Honest error handling (malformed input, unreachable endpoints) — TC-12, TC-13, TC-14
- Era-5 preservation (provenance badge, Registry, Comparison sections) — TC-15, TC-16
- Zero recomputation (verbatim rendering) — TC-17, TC-19
- Recency-boundary honesty — TC-07

**Out of scope (per phase spec):**
- J-06 cockpit confluence (band overlay on price chart) — queued for iter-7
- Credentialed tick recording (J-03 parallel carry) — operator-gated, shows as empty `tape_timeline` when not recorded
- Changes to raw levels/zones rendering itself (byte-identical when toggle is ON)
