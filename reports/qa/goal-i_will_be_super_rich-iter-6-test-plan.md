# Goal Iter-6 Functional Test Plan

**Phase:** goal-i_will_be_super_rich-iter-6
**Date:** 2026-06-05
**Frontend Present:** yes

## Phase Goal

Implement a candlestick price chart with tape-state-transition markers and a 10/30/60s bar-size selector, displayed above the cockpit for Simulated and Historical modes only, so users can visually correlate marked tape-state transitions with subsequent price movement on the same screen.

## Test Cases

### TC-01 — Engine history buffer accumulates OHLC bars at configured bin sizes

**Type:** api
**Preconditions:** Backend is running with config keys for bar sizes (10, 30, 60 s)

**Steps:**
1. Call `GET /tape/SIM-BUYER/history?bar=10` to fetch the history buffer
2. Verify response structure: `{bars: [{timestamp, open, high, low, close}, ...], markers: [...]}`
3. Call with `?bar=30` and `?bar=60` to verify all three bin sizes return data
4. Observe during a running SIM-BUYER watch that bars accrue in chronological order

**Expected outcome:** API returns OHLC bars binned at the requested interval with increasing timestamps and non-zero OHLC values derived from trade prices

**Pass criteria:** Status code 200; bars list contains 2+ bars with logical-timestamp ordering and realistic OHLC ranges (high >= low, close within open/high/low bounds); each bar size returns different granularity (60s bars fewer than 10s bars)

---

### TC-02 — Tape-state-transition markers emit only on meaningful state changes

**Type:** api
**Preconditions:** Engine processing a known event stream with state transitions; watch SIM-BUYER through SIM-SELLER transitions

**Steps:**
1. Call `GET /tape/SIM-BUYER/history?bar=10` and collect the markers array
2. Verify each marker has fields: `{timestamp, state, confidence}`
3. Check that markers only appear for states `buyer_control`, `seller_control`, `bid_absorption`, `ask_absorption`
4. Verify that transitions **to** `unclear` do not produce a marker

**Expected outcome:** Markers array contains entries only at meaningful state transitions with correct state values and 0 < confidence < 1

**Pass criteria:** Markers list non-empty for a watched ticker; all marker states are in {buyer_control, seller_control, bid_absorption, ask_absorption}; no marker has state == unclear; confidence values are numeric in range (0, 1); timestamps are unique and ordered

---

### TC-03 — Single source of truth: marker state/confidence match engine snapshot at transition time

**Type:** api
**Preconditions:** Backend storing snapshots and markers side-by-side; watch SIM-BUYER

**Steps:**
1. Observe a tape-state transition (e.g., SIM-BUYER → buyer_control)
2. Call `GET /tape/SIM-BUYER/history?bar=10` and locate the marker for that transition
3. Compare marker's `state` and `confidence` against the engine snapshot's `tape_state` and `confidence` at that timestamp
4. Repeat for at least 2 additional transitions

**Expected outcome:** Marker values are identical to snapshot values (no independent re-classification)

**Pass criteria:** For each marker, `marker.state == snapshot.tape_state` at the marker's timestamp; `marker.confidence == snapshot.confidence` at that timestamp; 100% match rate across all marked transitions

---

### TC-04 — GET /tape/{ticker}/history rejects out-of-range bar size with 4xx error

**Type:** api
**Preconditions:** Backend is running; config defines valid bar sizes as {10, 30, 60}

**Steps:**
1. Call `GET /tape/SIM-BUYER/history?bar=5` (not in config)
2. Call `GET /tape/SIM-BUYER/history?bar=999` (out of range)
3. Call `GET /tape/SIM-BUYER/history?bar=invalid` (non-numeric)

**Expected outcome:** All three requests return a 4xx status code with a descriptive error message

**Pass criteria:** Status code is 400, 422, or similar 4xx (not 200, not 500); error message contains the word "invalid" or "bar" or "range"; invalid bar is NOT silently coerced to a default

---

### TC-05 — GET /tape/{ticker}/history returns 404 for non-watched ticker

**Type:** api
**Preconditions:** Backend running; no watch active for ticker UNKNOWN-TICKER

**Steps:**
1. Call `GET /tape/UNKNOWN-TICKER/history?bar=10`
2. Verify status code and response body

**Expected outcome:** Request returns 404 Not Found

**Pass criteria:** Status code == 404; response indicates ticker is not currently watched (not a fabricated empty 200)

---

### TC-06 — GET /tape/{ticker}/history returns empty bars/markers for ticker with no trades yet

**Type:** api
**Preconditions:** Backend running; a ticker is being watched but no trades have been received (or in a historical window with no data)

**Steps:**
1. Start a watch for a real symbol over an empty historical window (e.g., weekend, outside RTH)
2. Call `GET /tape/[symbol]/history?bar=10` immediately
3. Verify response structure and content

**Expected outcome:** Response is HTTP 200 with empty bars list and empty markers list (never invented candles)

**Pass criteria:** Status code == 200; `{bars: [], markers: []}`; no synthetic/placeholder bars; no error thrown

---

### TC-07 — Candle prices derive from engine-computed trade prices (single source)

**Type:** api
**Preconditions:** Backend running with SIM-BUYER watch; watch accumulates trades with known prices

**Steps:**
1. Call `GET /tape/SIM-BUYER/history?bar=60` and extract the first OHLC bar
2. Cross-check the bar's `open`, `high`, `low`, `close` against raw trade prices in that 60s window (via logs or test data)
3. Verify all four values came from actual trades, not computed independently

**Expected outcome:** Bar OHLC values exactly match the min/max/first/last trade prices in that time bin (no second price source or independent binning)

**Pass criteria:** For a known event stream with trades at prices [100, 102, 101], the 60s bar contains open=100, high=102, low=100, close=101 (exact match); bucket boundaries align with logical timestamps, never wall-clock

---

### TC-08 — Browser: SIM-BUYER candlestick chart renders and updates during replay

**Type:** browser
**Preconditions:** Frontend is running at localhost:3000; backend at localhost:8000; user on `/` (home page); mode is `sim`

**Steps:**
1. Select `SIM-BUYER` from the ticker input
2. Confirm the price chart component is visible above the cockpit
3. Observe candles populating as the replay runs (10-15 second warm-up)
4. Confirm chart updates incrementally (new bars added, active bar grows)
5. Hover over a candle to verify it displays its OHLC values

**Expected outcome:** Chart renders with axis labels, grid, and candlesticks; candles are added to the right edge as time progresses

**Pass criteria:** Chart component is present and visible; candles render in white/gray candlestick shape; at least 3 candles visible after warm-up; no console errors; chart updates in real time as new bars accrue

---

### TC-09 — Browser: bar-size selector switches between 10/30/60 seconds and re-renders candles

**Type:** browser
**Preconditions:** Frontend running with SIM-BUYER watch active; chart is visible; mode is `sim`

**Steps:**
1. Confirm the bar-size selector is visible (buttons: "10s", "30s", "60s")
2. Observe current bar count with 10s selected (should be highest count)
3. Click "30s" button
4. Observe bars re-render with fewer but wider candles
5. Click "60s" button and confirm further consolidation
6. Return to "10s" and confirm original granularity

**Expected outcome:** Clicking a button changes the chart data and re-renders candles immediately; 10s produces the finest granularity, 60s the coarsest

**Pass criteria:** Bar-size buttons are clickable and styled distinctly; selected button is visually highlighted; candle count decreases as interval increases; chart data matches `GET /tape/{ticker}/history?bar=<N>` for the selected interval; smooth re-render with no flicker/error

---

### TC-10 — Browser: chart displays emerald marker for buyer_control transition

**Type:** browser
**Preconditions:** Frontend running with SIM-BUYER watch active; chart is visible; replay running long enough for a buyer_control state (3-4s warm-up)

**Steps:**
1. Observe the chart as the replay runs
2. Wait for the cockpit to show tape_state = `buyer_control` with confidence visible
3. Confirm a **green (emerald)** marker appears on the chart at that moment
4. Hover over the marker to verify it displays the state and confidence (optional polish)

**Expected outcome:** A green marker appears on the chart aligned with the tape-state transition timestamp; color matches design system emerald token

**Pass criteria:** Marker is visible on chart canvas; marker color is emerald (green); marker timestamp aligns with the transition (within 1 bar); no marker appears if state is `unclear`

---

### TC-11 — Browser: chart displays rose marker for seller_control and amber markers for absorption

**Type:** browser
**Preconditions:** Frontend running; cycle through SIM-SELLER, SIM-BIDABS, SIM-ASKABS watches; chart visible; mode is `sim`

**Steps:**
1. Switch to `SIM-SELLER` and let the chart populate; observe a red (rose) marker appear
2. Switch to `SIM-BIDABS` and observe an orange (amber) marker appear
3. Switch to `SIM-ASKABS` and confirm an amber marker appears
4. Verify each marker color matches the state: seller_control = rose, bid/ask_absorption = amber

**Expected outcome:** Markers are rendered in the correct semantic colors; color coding is consistent across all meaningful states

**Pass criteria:** Rose marker appears for seller_control; amber marker appears for bid_absorption and ask_absorption; unclear state has no marker; color tokens match design system (emerald, rose, amber)

---

### TC-12 — Browser: chart is hidden when mode is switched to Live

**Type:** browser
**Preconditions:** Frontend running; currently watching SIM-BUYER with chart visible; data-source/mode selector available

**Steps:**
1. Confirm chart is visible with mode = `sim`
2. Switch data source from `Simulated` to `Live` (if available in UI) or set mode to `live`
3. Verify the chart component is not displayed on the page
4. Switch back to `Simulated` and confirm chart reappears

**Expected outcome:** Chart visibility is tied to mode; hidden for Live, shown for Simulated/Historical

**Pass criteria:** Chart div is not rendered (display: none or removed from DOM) when mode is `live`; chart reappears when mode returns to `sim`; no console errors; cockpit and other panels remain visible

---

### TC-13 — Browser: chart pan/zoom functions (library default interaction)

**Type:** browser
**Preconditions:** Frontend running with SIM-BUYER watch; chart is visible with multiple candles

**Steps:**
1. Attempt to scroll/pan horizontally on the chart canvas (drag left/right)
2. Attempt to zoom with mouse wheel or pinch gesture (if available)
3. Verify the chart scales and translates appropriately

**Expected outcome:** User can navigate the chart; zoom/pan behavior matches the charting library's default (library-default is sufficient, no custom interaction required)

**Pass criteria:** Chart responds to pan/zoom gestures; no crashes or errors; chart remains readable after interaction

---

### TC-14 — Browser: empty chart shows "no price history yet" when no bars available

**Type:** browser
**Preconditions:** Frontend running; watch a real symbol over an empty/past historical window with no trades

**Steps:**
1. Select `Historical` mode
2. Choose a weekend date or a time outside regular trading hours (no trades expected)
3. Wait for the chart to load
4. Verify the chart displays an empty state (not blank canvas, but a clear message)

**Expected outcome:** Chart shows a message like "no price history yet" or displays an empty canvas without fabricated candles

**Pass criteria:** Chart is visible but candles list is empty; a text message or placeholder indicates no data; no invented bars; HTTP 200 with empty response from backend

---

### TC-15 — Browser: Historical mode candlesticks reflect real replayed prices

**Type:** browser
**Preconditions:** Frontend running; credentials configured (or gated/fixture path used); select Historical mode with a real symbol (e.g., Ford/F) over a past RTH window with known data

**Steps:**
1. Select `Historical` mode in the UI
2. Choose a liquid symbol (e.g., Ford/F) and a past date/time window (e.g., 2024-01-15 09:30-11:00 ET)
3. Observe the chart populate with candlesticks as the replay runs
4. Visually verify candles reflect realistic price movement (not flatlined, not inverted)
5. Confirm bar-size selector works (toggle 10/30/60s)
6. Confirm markers appear at tape-state transitions (if the engine encounters meaningful states during replay)

**Expected outcome:** Historical candlesticks display realistic OHLC values for the chosen symbol and window; bar-size selector functions; markers appear only at meaningful transitions

**Pass criteria:** Candles are not all identical (H != L for at least one bar); price range is reasonable for the symbol (e.g., Ford 15–25 range, not 0.01–0.99); no console errors; if credentials absent, gated/fixture path is used and chart surface is browser-verifiable

---

### TC-16 — Browser: page remains one screen (no vertical scroll added by chart)

**Type:** browser
**Preconditions:** Frontend running; mode is `sim`; SIM-BUYER watch active

**Steps:**
1. Load the page on a desktop viewport (e.g., 1920x1080)
2. Observe the layout: chart above, cockpit panels below
3. Verify the page fits within the viewport without requiring vertical scrolling

**Expected outcome:** Chart + cockpit fit on one screen; layout is responsive and does not overflow vertically

**Pass criteria:** No `overflow-y: scroll` on body; page height <= viewport height on standard desktop; chart height is reasonable relative to cockpit (chart does not dominate the screen)

---

### TC-17 — Backend tests: history buffer produces expected OHLC at each bin size

**Type:** artifact
**Preconditions:** Backend tests exist in `apps/backend/tests/test_history.py`

**Steps:**
1. Run the backend test suite: `cd apps/backend && .venv/bin/python -m pytest tests/test_history.py -v`
2. Verify all history buffer tests pass

**Expected outcome:** Test output shows OHLC bar generation tests passing for 10s, 30s, and 60s bin sizes

**Pass criteria:** All test_history.py tests pass; test count includes assertions for:
- OHLC bars are created with correct open/high/low/close
- Bars are binned by logical timestamp (not wall-clock)
- Each bin size produces expected number of bars
- Determinism test confirms same stream → identical bars on replay

---

### TC-18 — Backend tests: marker emission only on meaningful state transitions

**Type:** artifact
**Preconditions:** Backend tests exist in `apps/backend/tests/test_history.py`

**Steps:**
1. Run backend tests filtering for marker tests: `cd apps/backend && .venv/bin/python -m pytest tests/test_history.py::test_*marker* -v`
2. Verify marker logic tests pass

**Expected outcome:** Tests confirm markers are emitted only for {buyer_control, seller_control, bid_absorption, ask_absorption} and NOT for `unclear`

**Pass criteria:** Marker tests pass; test assertions verify:
- No marker on transition to unclear
- Marker emitted on transition to buyer_control
- Marker emitted on transition to seller_control
- Marker state == snapshot.tape_state at transition
- Marker confidence == snapshot.confidence

---

### TC-19 — Backend tests: GET /tape/{ticker}/history projection correctness

**Type:** artifact
**Preconditions:** Backend API tests in `apps/backend/tests/test_api.py` (or new `test_history_api.py`)

**Steps:**
1. Run API projection tests: `cd apps/backend && .venv/bin/python -m pytest tests/test_api.py -k history -v` (or equivalent)
2. Verify projection tests pass for 404, 4xx, and 200 cases

**Expected outcome:** All projection tests pass; coverage includes error cases and empty-window handling

**Pass criteria:** Tests pass; test assertions include:
- 404 for non-watched ticker
- 4xx for invalid bar size
- 200 with empty bars/markers for empty window
- 200 with correct bars/markers for watched ticker
- Bar data in response == engine buffer data (no projection loss)

---

### TC-20 — Backend test suite: no regression in existing tests

**Type:** artifact
**Preconditions:** Backend test suite was passing with 141 tests at iter-5; new tests added for history feature

**Steps:**
1. Run full backend test suite: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
2. Count passing and failing tests
3. Compare count to iter-5 baseline (141 passed, 1 skipped)

**Expected outcome:** Test count is >= 141 (new history tests added); all previously passing tests still pass

**Pass criteria:** Total passing tests >= 141; no new failures; test count has risen (history tests added, e.g., +10–20 tests); no skipped tests increased; summary line shows `X passed, 0 failed, 1 skipped`

---

### TC-21 — Artifact: app/config.py contains bar sizes and marker parameters

**Type:** artifact
**Preconditions:** Developer has committed code to main branch

**Steps:**
1. Inspect `apps/backend/app/config.py`
2. Verify presence of config keys for bar sizes (e.g., `history_bar_sizes = (10, 30, 60)`)
3. Verify no magic numbers for bar size, threshold, or binning parameter appear inline in engine code

**Expected outcome:** Config dataclass contains history-related keys; engine code references config, not hardcoded literals

**Pass criteria:** File contains: `history_bar_sizes`, no bar-size literal (5, 10, 30, 60) appears in `tape_engine.py` or `history.py`; any threshold/parameter referenced in engine comes from config

---

### TC-22 — Artifact: PriceChart component exists and is client-only

**Type:** artifact
**Preconditions:** Developer has committed code

**Steps:**
1. Inspect `apps/frontend/components/PriceChart.tsx`
2. Verify `"use client"` directive is present at the top
3. Verify the component dynamically imports the charting library (not top-level import)
4. Verify the component reads data only from `GET /tape/{ticker}/history`

**Expected outcome:** Component is marked as client-side; library is lazy-loaded; no server-side rendering of chart

**Pass criteria:** File contains `"use client"` at line 1; charting library import is inside `useEffect()` or dynamic `import()`; no chart rendering on server side; component accepts `ticker` and `mode` props

---

### TC-23 — Artifact: PriceChart is mounted above Cockpit in page.tsx

**Type:** artifact
**Preconditions:** Developer has committed code

**Steps:**
1. Inspect `apps/frontend/app/page.tsx`
2. Locate the `PriceChart` component mount
3. Verify it is rendered **before** (above) the `<Cockpit>` component in JSX order
4. Verify conditional rendering: `mode === "sim" || mode === "historical"` shows chart; `mode === "live"` hides it

**Expected outcome:** Chart is mounted above cockpit; visibility is conditional on mode

**Pass criteria:** JSX contains `<PriceChart ... />` before `<Cockpit />` in the render tree; conditional logic is present: `{(mode === 'sim' || mode === 'historical') && <PriceChart ... />}`; no `mode === 'live'` renders the chart

---

### TC-24 — Artifact: api.ts fetchHistory function exists and calls correct endpoint

**Type:** artifact
**Preconditions:** Developer has committed code

**Steps:**
1. Inspect `apps/frontend/lib/api.ts`
2. Locate `fetchHistory(ticker: string, bar: number)` function
3. Verify it calls `GET /tape/{ticker}/history?bar={bar}`
4. Verify return type matches the backend response schema

**Expected outcome:** API function is present and correctly formatted

**Pass criteria:** Function signature is `fetchHistory(ticker, bar)` or similar; function calls endpoint `/tape/${ticker}/history?bar=${bar}`; function returns Promise with { bars, markers } structure; error handling for 404/4xx is present

---

### TC-25 — Artifact: types.ts defines OHLC and TapeMarker types

**Type:** artifact
**Preconditions:** Developer has committed code

**Steps:**
1. Inspect `apps/frontend/lib/types.ts`
2. Verify `OhlcBar` type (or similar) with fields: timestamp, open, high, low, close
3. Verify `TapeMarker` type (or similar) with fields: timestamp, state, confidence
4. Verify response type for history endpoint

**Expected outcome:** Types are defined correctly; frontend can consume backend response with type safety

**Pass criteria:** Types include:
- `OhlcBar { timestamp: number, open: number, high: number, low: number, close: number }`
- `TapeMarker { timestamp: number, state: TapeState, confidence: number }`
- History response: `{ bars: OhlcBar[], markers: TapeMarker[] }`

---

### TC-26 — Browser: J-17 comprehensive journey (SIM-BUYER with chart, mode switch, bar-size toggle)

**Type:** browser
**Preconditions:** Frontend and backend running; mode is `sim`

**Steps:**
1. Navigate to `/` (home page)
2. Select `SIM-BUYER` from the ticker input
3. Observe chart renders above cockpit with candlesticks and an emerald buyer_control marker
4. Toggle bar size from 10s → 30s → 60s and confirm re-render each time
5. Select `SIM-SELLER` and confirm chart updates with rose marker
6. Select `SIM-BIDABS` and confirm amber marker appears
7. Select `SIM-ASKABS` and confirm amber marker appears
8. Switch data source to `Live` and confirm chart is hidden
9. Switch back to `Simulated` and confirm chart reappears

**Expected outcome:** Full end-to-end journey completes without errors; all visual elements render correctly; state changes are reflected in markers and candles

**Pass criteria:** All steps execute without console errors; chart remains visible and interactive throughout; mode switch hides/shows chart correctly; all marker colors are correct; bar-size selector works reliably

---

### TC-27 — Browser: J-18 comprehensive journey (Historical replay with real symbol, bar-size toggle)

**Type:** browser
**Preconditions:** Frontend/backend running; select Historical mode; credentials present or gated/fixture path used

**Steps:**
1. Navigate to `/` (home page)
2. Select `Historical` mode from data-source selector
3. Choose a real symbol (e.g., Ford/F) and a past RTH window (e.g., 2024-01-15 09:30-11:00 ET)
4. Confirm chart populates with candlesticks reflecting real price data
5. Toggle bar size 10s → 30s → 60s and observe candles consolidate/expand
6. Confirm markers appear at meaningful tape-state transitions (if any during replay)
7. Verify chart handles an empty window gracefully (no invented candles, "no data" message)

**Expected outcome:** Historical replay displays realistic price action; bar-size selector works; markers are accurate; empty windows are handled honestly

**Pass criteria:** Candlesticks show realistic OHLC values for the symbol; bar-size toggle re-renders chart correctly; markers align with tape-state transitions; no console errors; empty window displays empty chart (not fabricated bars)

---

## Summary

**Total test cases:** 27
**API tests:** 7 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07)
**Browser tests:** 13 (TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-16, TC-26, TC-27)
**Artifact checks:** 7 (TC-17, TC-18, TC-19, TC-20, TC-21, TC-22, TC-23, TC-24, TC-25)

All tests map back to specific requirements in the phase spec:
- **Definition of Done:** tests TC-17–TC-20 verify journey and regression targets
- **IN SCOPE requirements:** tests TC-01–TC-07 verify backend mechanics; TC-08–TC-16 verify frontend behavior
- **Anti-goal validation:** TC-04–TC-07 ensure no magic numbers, no fabricated data, single source of truth; TC-12 ensures chart hidden for Live
