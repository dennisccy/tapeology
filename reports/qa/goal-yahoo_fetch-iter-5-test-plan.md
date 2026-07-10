# goal-yahoo_fetch-iter-5 Functional Test Plan

**Phase:** goal-yahoo_fetch-iter-5
**Date:** 2026-07-10
**Frontend Present:** yes

## Phase Goal

On `/structure`, a user picks a symbol, timeframe, and date range, clicks **Fetch from Yahoo Finance**, and the page renders real candles + real S/R level lines + A/B/C confluence-zone table with a "Yahoo Finance" provenance badge — closing Era 5's final journey (J-05).

## Test Cases

### TC-01 — Taxonomy label "yahoo" exists and is readable

**Type:** api
**Preconditions:** Backend is running. `/research/taxonomy` endpoint is available.

**Steps:**
1. GET `/research/taxonomy`
2. Parse the response and locate `feed_basis.feeds[]`
3. Search for an entry with `id: "yahoo"`

**Expected outcome:** The `feed_basis.feeds` array contains an object `{"id": "yahoo", "name": "Yahoo Finance"}`
**Pass criteria:** Response status is 200 and `feed_basis.feeds` includes `{"id": "yahoo", "name": "Yahoo Finance"}`

---

### TC-02 — B2 fix: blank symbol parameter normalizes before filter

**Type:** api
**Preconditions:** Backend is running. `/research/bars` endpoint is available. A pre-seeded, un-indexed test series with `feed="yahoo"` exists in the BarStore.

**Steps:**
1. GET `/research/bars?symbol=` (blank string, no timeframe param)
2. Capture the full JSON response and record its byte-length and checksum
3. GET `/research/bars` (no params)
4. Capture the full JSON response and record its byte-length and checksum
5. Compare the two responses byte-for-byte

**Expected outcome:** Both GET requests return identical JSON (same series list, same checksum, same byte length)
**Pass criteria:** Byte-identical response bodies confirm that blank `?symbol=` is normalized to `None` before the filter short-circuit, matching the behavior of no-param

---

### TC-03 — POST /research/bars helper accepts and forwards symbol/timeframe/start/end

**Type:** api
**Preconditions:** Backend is running. Frontend API client module `apps/frontend/lib/api.ts` has been updated with a new POST helper for `/research/bars`.

**Steps:**
1. Call the new POST client helper with body `{symbol: "AAPL", timeframe: "1d", start: "2026-01-01T00:00:00Z", end: "2026-01-10T00:00:00Z"}`
2. Verify the helper constructs a POST request to `/research/bars`
3. Confirm the helper returns `{ok: true, bar_series: {...}}` on a 200 response

**Expected outcome:** The client helper correctly marshals the four parameters into a POST request and unpacks the response
**Pass criteria:** Helper returns an object with `ok: true` and a `bar_series` field containing the fetched series object

---

### TC-04 — POST /research/bars error handling: unsupported timeframe returns 422

**Type:** api
**Preconditions:** Backend is running. A timeframe like `"8h"` or `"1mo"` is not supported by Yahoo.

**Steps:**
1. POST `/research/bars` with body `{symbol: "AAPL", timeframe: "8h", start: "2026-01-01T00:00:00Z", end: "2026-01-10T00:00:00Z"}`
2. Capture the response status and body

**Expected outcome:** Response status is 422; body contains `detail` or error message explaining the timeframe is unsupported
**Pass criteria:** Status is 422 and error message is present (not a 200 or 500)

---

### TC-05 — Fetch control section renders on /structure page

**Type:** browser
**Preconditions:** Frontend is running at `http://localhost:3301`. User is on the `/structure` page.

**Steps:**
1. Navigate to `/structure`
2. Look for a section containing inputs for symbol, timeframe, date range, and a submit button
3. Confirm the section has a label or header "Fetch from Yahoo Finance" or similar

**Expected outcome:** The fetch-control section is visible on the page
**Pass criteria:** Visible elements include: a symbol input (or search), a timeframe selector dropdown, start/end date inputs, and a button labeled "Fetch from Yahoo Finance"

---

### TC-06 — Fetch button is disabled until all inputs are filled

**Type:** browser
**Preconditions:** Frontend is running. User is on `/structure` page with the fetch control visible.

**Steps:**
1. Observe the "Fetch from Yahoo Finance" button state (should be disabled initially)
2. Fill only the symbol field
3. Verify button state
4. Fill the timeframe field
5. Verify button state
6. Fill start and end date fields
7. Verify button state

**Expected outcome:** Button remains disabled until all four fields (symbol, timeframe, start, end) are populated; then it becomes enabled
**Pass criteria:** Button has `disabled` attribute or visual disabled state until the last field is filled; becomes clickable once all fields have values

---

### TC-07 — Store-first fetch of pre-seeded fixture returns data without network

**Type:** browser
**Preconditions:** Frontend is running. Backend is running. A committed Yahoo fixture (e.g., `AAPL_1d_20260601_20260604.json`) has been pre-seeded into the BarStore via the store-first POST path or via `reindex()`, so the index can serve it without network. Browser and backend can reach each other.

**Steps:**
1. Navigate to `/structure`
2. Fill the fetch control with the fixture's exact parameters: symbol=`AAPL`, timeframe=`1d`, start=`2026-06-01T00:00:00Z`, end=`2026-06-04T00:00:00Z`
3. Click "Fetch from Yahoo Finance"
4. Wait for the response and observe the chart render

**Expected outcome:** The chart populates with real candles for the fixture window. No network request to Yahoo is made (served store-first from the index).
**Pass criteria:** Candles are rendered on the chart immediately (< 1 second) with correct OHLC values matching the stored fixture, and the server returns HTTP 200 with `store_hit: true` or similar indicator of a cache hit

---

### TC-08 — Levels and zones render after fetch

**Type:** browser
**Preconditions:** Frontend is running. Backend is running. Fetch control has been submitted and candles are rendered (TC-07 passed).

**Steps:**
1. Observe the chart area below the candles (or on the right side)
2. Look for level lines overlaid on the chart corresponding to support/resistance levels
3. Look for the A/B/C confluence zone table below the chart
4. Confirm the table has rows for each zone with class (A/B/C) and score columns

**Expected outcome:** Level lines and zones are visible, read from `/research/levels` endpoint verbatim
**Pass criteria:** At least one level line is rendered; the zone table shows one or more rows with visible class labels (A, B, or C) and numeric scores

---

### TC-09 — Provenance badge displays "Yahoo Finance"

**Type:** browser
**Preconditions:** Frontend is running. Backend is running. Fetch control has been submitted and chart is rendered (TC-07 passed).

**Steps:**
1. Observe the area near the chart or the series metadata section
2. Look for a badge or label displaying the data source/provenance
3. Verify the badge text reads "Yahoo Finance" (read from taxonomy, not hardcoded)

**Expected outcome:** A "Yahoo Finance" provenance badge is visible, sourced from `/research/taxonomy`
**Pass criteria:** Badge is rendered with text "Yahoo Finance" and is positioned near the chart/series metadata

---

### TC-10 — No hardcoded "Yahoo Finance" literal in frontend

**Type:** artifact
**Preconditions:** Source code for `apps/frontend/` is available.

**Steps:**
1. Run `grep -r "Yahoo Finance" apps/frontend` (excluding `.next` build dir)
2. Inspect results

**Expected outcome:** No hardcoded "Yahoo Finance" string appears in the frontend source (only in data structures/taxonomy reads)
**Pass criteria:** grep returns only results from FeedBasisBadge or similar taxonomy-driven render component, never a string literal in JSX/template

---

### TC-11 — Empty state when no bars stored for symbol

**Type:** browser
**Preconditions:** Frontend is running. Backend is running.

**Steps:**
1. Navigate to `/structure`
2. Fill the fetch control with a symbol that has no stored bars (e.g., `UNKNOWN`)
3. Click "Fetch from Yahoo Finance"
4. Observe the result

**Expected outcome:** An empty state message appears (distinct from error); candles and zones do not render
**Pass criteria:** A message like "No bars found for this symbol" or similar distinct empty state is displayed; no error toast; chart is blank

---

### TC-12 — Repeat fetch of same window returns store-first (200, no network)

**Type:** api
**Preconditions:** Backend is running. A fixture window (e.g., AAPL 1d 2026-06-01 to 2026-06-04) has been fetched and stored once.

**Steps:**
1. POST `/research/bars` with the same parameters as the first fetch
2. Capture the response status and any `detail` or metadata indicating a cache hit
3. Verify no network call to Yahoo is made (observable via network logs or server logs)

**Expected outcome:** Response status is 200; the same series is returned; metadata indicates store-first cache hit (no re-fetch)
**Pass criteria:** Status is 200 (not 409); response includes the series with matching checksums to the original fetch; server logs show zero Yahoo adapter calls

---

### TC-13 — Levels /J-04 regression: levels still render on /structure

**Type:** browser
**Preconditions:** Frontend is running. Backend is running. The `/structure` page with J-04 "Load levels" functionality (read-only form) is accessible.

**Steps:**
1. Navigate to `/structure`
2. Fill the existing "Load" form (symbol + as-of date) — the read-only flow from J-04
3. Submit the form
4. Observe the chart and zone table

**Expected outcome:** Levels and zones render via the existing J-04 flow; no regression
**Pass criteria:** Chart displays level lines and zone table shows rows, exactly as in iter-4

---

### TC-14 — Core surfaces J-06 regression: /, /journal, /studies, /performance intact

**Type:** browser
**Preconditions:** Frontend is running. Backend is running.

**Steps:**
1. Navigate to `/` (Cockpit)
2. Verify the cockpit form and tape display are present
3. Navigate to `/journal`
4. Verify journal entries are displayed
5. Navigate to `/studies`
6. Verify study cards or list are displayed
7. Navigate to `/performance`
8. Verify performance metrics are displayed

**Expected outcome:** All four core surfaces render without visual regression or missing content
**Pass criteria:** No broken layouts, missing nav items, or error messages; all four pages load and display their expected content

---

### TC-15 — No anti-goal violations: no hardcoded profit/prediction copy in fetch control

**Type:** artifact
**Preconditions:** Source code for fetch control in `apps/frontend/app/structure/page.tsx` is available.

**Steps:**
1. Inspect the fetch-control section JSX/markup
2. Search for text/copy containing words like "profit", "expect", "predict", "guaranteed", "will", "should outperform", "paper trading", "shadow trading", "annualized"

**Expected outcome:** The fetch control and any error/empty state messages use neutral, honest language ("Fetch from Yahoo Finance", "No bars available", "Unsupported timeframe", etc.)
**Pass criteria:** No prediction, profit claim, or advice language found in the fetch control or related error states

---

### TC-16 — Backend suite green: no regressions

**Type:** api
**Preconditions:** Backend source code is complete. All tests are runnable.

**Steps:**
1. Run the full backend test suite: `cd apps/backend && python -m pytest tests/ -v`
2. Record the total passed, failed, and skipped counts
3. Verify no test failures related to J-01–J-06 or the frozen code paths

**Expected outcome:** All tests pass (or same pass/skip counts as iter-4 baseline); no new failures
**Pass criteria:** Test exit code is 0; passed count >= 1206 (iter-4 baseline); failed count is 0

---

### TC-17 — Engine equivalence test passes

**Type:** api
**Preconditions:** Backend is complete. Engine equivalence test is runnable.

**Steps:**
1. Run the engine equivalence test: `cd apps/backend && python -m pytest tests/test_engine_equivalence.py -v`
2. Record the result

**Expected outcome:** All 22 equivalence tests pass; `default` profile produces byte-identical state/confidence/features across equivalence runs
**Pass criteria:** Test passes with 22/22 engine states confirmed equivalent; no regression in tape engine

---

### TC-18 — config_fingerprint unchanged

**Type:** api
**Preconditions:** Backend is complete. `apps/backend/app/research/config.py` is readable.

**Steps:**
1. Import or parse `config.py`
2. Compute or retrieve the `config_fingerprint` value
3. Compare to the iter-4 frozen value: `4d665603569b9dbf`

**Expected outcome:** `config_fingerprint == "4d665603569b9dbf"`
**Pass criteria:** Fingerprint matches exactly; no mutation of config

---

### TC-19 — Frozen code paths byte-identical

**Type:** artifact
**Preconditions:** Git repository is available. Iter-4 baseline commit is known.

**Steps:**
1. Run `git diff <iter-4-baseline> -- apps/backend/app/research/levels.py apps/backend/app/research/backtests.py apps/backend/app/research/strategies.py apps/backend/app/research/bars.py apps/backend/app/research/bar_index.py apps/backend/app/providers/adapters/alpaca.py apps/backend/app/tape/engine.py`
2. Verify output is empty (no changes to these files)

**Expected outcome:** No diffs; frozen files are untouched
**Pass criteria:** `git diff` output is empty; confirms additive-only changes

---

## Summary

**Total test cases:** 19

**API tests:** 8 (TC-01, TC-02, TC-03, TC-04, TC-12, TC-16, TC-17, TC-18)
**Browser tests:** 7 (TC-05, TC-06, TC-07, TC-08, TC-09, TC-11, TC-13, TC-14)
**Artifact checks:** 4 (TC-10, TC-15, TC-19, plus TC-02 and TC-16 artifact verification)

**Coverage:**
- Backend: Taxonomy label, B2 fix, POST helper, error handling, engine equivalence, frozen code, config fingerprint
- Frontend: Fetch control visibility, button state, store-first hit, levels/zones render, provenance badge, honest states, no hardcoded strings, anti-goal compliance
- Browser: Real-world UI interaction, regression checks on core surfaces
