# Goal Iteration 13 Functional Test Plan

**Phase:** goal-i_will_be_super_rich-iter-13
**Date:** 2026-06-09
**Frontend Present:** yes

## Phase Goal

Enable a user to change the historical replay speed mid-replay and have it apply immediately; classify real directional moves as control (not `unclear`) by judging spread/impact relative to price level; and load long historical windows via chunked sub-window fetches instead of returning the "very high-volume" error.

## Test Cases

### TC-01 — POST /watch/{ticker}/speed with valid speed

**Type:** api
**Preconditions:** Backend running; a watch is actively running on ticker SIM-BUYER with a historical window loaded

**Steps:**
1. GET `/watch/SIM-BUYER` to confirm watch is running
2. POST `/watch/SIM-BUYER/speed` with body `{"speed": 10.0}` (assuming `10.0` is in `CONFIG.allowed_replay_speeds`)
3. GET `/watch/SIM-BUYER` immediately after to verify the speed field updated
4. Wait ~2s and GET `/watch/SIM-BUYER` again to confirm the watch is still running (not torn down)

**Expected outcome:** POST returns 200 with a canonical watch summary; the speed in the response reflects the new value; the watch is not restarted

**Pass criteria:** HTTP status 200; response JSON includes `speed: 10.0`; subsequent GET shows `state` is still running; no new watch `created_at` timestamp

---

### TC-02 — POST /watch/{ticker}/speed with invalid (out-of-set) speed

**Type:** api
**Preconditions:** Backend running; a watch is actively running on ticker SIM-BUYER

**Steps:**
1. POST `/watch/SIM-BUYER/speed` with body `{"speed": 999.0}` (out of `CONFIG.allowed_replay_speeds`)

**Expected outcome:** Request returns 422 Unprocessable Entity; response indicates the speed value is not allowed

**Pass criteria:** HTTP status 422; response error message references invalid speed or allowed values

---

### TC-03 — POST /watch/{ticker}/speed on unwatched ticker

**Type:** api
**Preconditions:** Backend running; ticker SIM-UNKNOWN is not being watched

**Steps:**
1. POST `/watch/SIM-UNKNOWN/speed` with body `{"speed": 1.0}`

**Expected outcome:** Request returns 404 Not Found; response indicates the ticker is not being watched

**Pass criteria:** HTTP status 404; response error message references ticker not watched or not found

---

### TC-04 — Determinism: same window at two different speeds yields identical features/state/confidence

**Type:** api
**Preconditions:** Backend running; test harness can make two sequential watch → replay cycles on the same window (fixed symbol and time range)

**Steps:**
1. POST `/watch/SIM-BUYER` with a fixed historical window (e.g., `start_time=1700000000`, `end_time=1700003600`)
2. Wait for the replay to complete at speed 1.0; GET `/watch/SIM-BUYER` and record the final `tape_state`, `confidence`, `buy_price_impact`, `sell_price_impact`, `spread_bps`
3. Stop the watch (POST `/watch/SIM-BUYER/pause` → resume or restart)
4. POST `/watch/SIM-BUYER` again with the same historical window and parameters
5. Immediately after receiving the watch response (before replay completes), POST `/watch/SIM-BUYER/speed` with `{"speed": 10.0}`
6. Wait for the replay to complete; GET `/watch/SIM-BUYER` and record the same feature snapshot

**Expected outcome:** Both final snapshots (at 1× and 10× speed) are byte-identical for `tape_state`, `confidence`, `buy_price_impact`, `sell_price_impact`, and `spread_bps`

**Pass criteria:** Feature JSON dicts are equal (no floating-point tolerance needed if values are identical); `tape_state` and `confidence` match exactly

---

### TC-05 — J-33: Real directional move (relative spread/impact) resolves to seller_control

**Type:** api
**Preconditions:** Backend running; classifier tuned with relative-spread and relative-impact gates; a deterministic fixture scenario (warmed, high sell ratio, strong negative relative impact, spread wide in absolute $ but normal relative to price)

**Steps:**
1. POST `/watch/GME` (or a reference ~$30–50 symbol) with a historical window designed to trigger the fixture scenario
2. Wait for the tape to warm and the directional move to complete
3. GET `/watch/GME` and extract `tape_state` and `confidence`

**Expected outcome:** `tape_state` is `seller_control`; `confidence` is ≥ a reasonable threshold (e.g. 0.65)

**Pass criteria:** JSON field `tape_state` == `"seller_control"` and `confidence` >= 0.65

---

### TC-06 — J-33: Wide relative spread (no proportionate price impact) resolves to absorption or unclear

**Type:** api
**Preconditions:** Backend running; classifier tuned; a deterministic negative-guard fixture (wide relative spread with no proportionate price progress)

**Steps:**
1. Craft a test scenario with the negative-guard fixture (high-volume tape with 50/50 buy/sell ratio, spread in basis points normal or wide relative to price, no strong price movement)
2. POST `/watch/<ticker>` with the fixture window
3. Wait for the tape to warm
4. GET `/watch/<ticker>` and extract `tape_state` and `confidence`

**Expected outcome:** `tape_state` is `absorption` or `unclear`; `confidence` is not artificially high

**Pass criteria:** JSON field `tape_state` in [`"absorption"`, `"unclear"`]; `confidence` < 0.85 OR state correctly reflects the weak signal

---

### TC-07 — J-33: Absorption gate is the exact complement of control impact condition

**Type:** api
**Preconditions:** Backend running; unit tests for classifier are available; a test that verifies absorption gates against control conditions

**Steps:**
1. Run `pytest tests/test_classifier.py -v` (backend test suite)
2. Verify that test coverage includes a regression fixture asserting absorption gates are the complement of control impact gates
3. Confirm all tests pass

**Expected outcome:** All classifier tests pass; regression fixture confirms that if a scenario does NOT meet the control impact condition, it resolves to absorption (not a silent reclassification of J-04/J-05)

**Pass criteria:** pytest exit code 0; test output includes a line confirming "absorption gates are complement of control"

---

### TC-08 — J-34: Chunk-split and in-order stitch for long historical window

**Type:** api
**Preconditions:** Backend running; Alpaca adapter has chunked-fetch logic; unit tests are available

**Steps:**
1. Run `pytest tests/test_alpaca.py -v -k chunk` (or similar test targeting the chunk logic)
2. Verify that a long window is split into the expected bounded sub-windows
3. Confirm the merged stream is epoch-ordered with no fabricated/dropped/reordered/de-duplicated prints

**Expected outcome:** All chunk-related tests pass; no assertion errors on stream ordering or print integrity

**Pass criteria:** pytest exit code 0; test output shows chunking and stitch logic exercised; no "fabricated" or "dropped" errors

---

### TC-09 — J-34: Full-RTH historical window loads for a liquid symbol

**Type:** api
**Preconditions:** Backend running; Alpaca credentials available; a liquid symbol (e.g., SPY, QQQ) is available

**Steps:**
1. POST `/watch/SPY` with a Full-RTH (6.5-hour) historical window (e.g., 9:30 AM to 4:00 PM ET)
2. Wait for the fetch and replay to complete
3. GET `/watch/SPY` and verify the watch is running with a non-empty chart

**Expected outcome:** Window loads successfully; no "very high-volume" error; watch shows a valid tape state and chart

**Pass criteria:** HTTP status 200 on the initial POST; response includes `tape_state` != `null`; no error message about "very high-volume"

---

### TC-10 — J-34: Re-watch of the same symbol+window hits the window cache (fast load)

**Type:** api
**Preconditions:** Backend running; a long historical window has already been fetched and cached (from TC-09 or prior)

**Steps:**
1. POST `/watch/SPY` with the same Full-RTH window as before (same `start_time`, `end_time`)
2. Measure the elapsed time from request to response
3. Compare with the first fetch time from TC-09

**Expected outcome:** The second watch responds significantly faster (sub-second, vs. several seconds for the first fetch)

**Pass criteria:** Response time < 1 second; response JSON matches the first fetch (same `buy_price_impact`, `sell_price_impact`, feature counts)

---

### TC-11 — J-32: Browser — change replay speed on a running historical replay

**Type:** browser
**Preconditions:** Frontend running at http://localhost:3000; a historical replay is active with multiple events streaming; Historical mode control panel is visible

**Steps:**
1. Navigate to the home page (`/`)
2. Click the Historical quick-pick to start a replay (e.g., Full-RTH on SIM-BUYER)
3. Wait for the chart to begin rendering and events to scroll
4. Locate the replay-speed control (a dropdown or slider in the Historical panel)
5. Change the speed from 1.0 to 10.0
6. Observe the chart and cockpit for the next ~2s
7. Verify the event cadence increases (events arrive faster in the DOM) without a re-Watch call

**Expected outcome:** Chart continues rendering; no request to POST `/watch/{ticker}` (re-Watch); the speed control reflects the new value; events stream faster

**Pass criteria:** Browser DevTools shows a POST `/watch/{ticker}/speed` request (not a GET `/watch/{ticker}` which would be a re-Watch); network tab shows no new WebSocket reconnect; chart DOM updates without page reload

---

### TC-12 — J-32: Browser — replay-speed control rejects out-of-set values client-side

**Type:** browser
**Preconditions:** Frontend running; a historical replay is active; the replay-speed control is visible

**Steps:**
1. Attempt to enter or select an invalid speed value (e.g., type `999` in a text input or select a value outside the allowed list)
2. Observe the control's validation behavior

**Expected outcome:** The control either disables/grays out invalid values, clears the input, or shows a validation error; the invalid speed is not submitted to the backend

**Pass criteria:** Input field is disabled or rejected for out-of-set values; no POST `/watch/{ticker}/speed` with an invalid value appears in the network tab

---

### TC-13 — Regression: J-17 (sim chart renders on SIM-BUYER)

**Type:** browser
**Preconditions:** Frontend running; backend running on SIM-BUYER

**Steps:**
1. Navigate to `/`
2. Enter ticker `SIM-BUYER` and press "Watch"
3. Wait ~5s for the chart to render
4. Verify the chart shows buy-side data (green markers, positive impact indication)

**Expected outcome:** Chart renders without errors; buy-side markers are visible and colored green

**Pass criteria:** Chart SVG/canvas element is present in the DOM; at least one marker is visible with a green or emerald color

---

### TC-14 — Regression: J-02/J-03 (SIM-BUYER and SIM-SELLER states still resolve)

**Type:** browser
**Preconditions:** Frontend running; backend running

**Steps:**
1. Watch SIM-BUYER; wait for the state to resolve to `buyer_control` (should reach ~0.87 confidence within ~4s)
2. Stop the watch
3. Watch SIM-SELLER; wait for the state to resolve to `seller_control`
4. Verify the tape-state panel on row 1 shows the correct state and confidence

**Expected outcome:** SIM-BUYER resolves to `buyer_control`; SIM-SELLER resolves to `seller_control`; confidence values are as expected

**Pass criteria:** Row-1 tape-state panel displays `buyer_control` with confidence ≥ 0.80 for SIM-BUYER; `seller_control` with confidence ≥ 0.80 for SIM-SELLER; no state drift after J-33 re-tuning

---

### TC-15 — Regression: J-20 (historical window picker unchanged)

**Type:** browser
**Preconditions:** Frontend running; the window-picker control (quick-picks, date range, time range) is visible

**Steps:**
1. Navigate to `/`
2. Locate the Historical mode quick-picks (e.g., "Full-RTH", "1H", "5M") and the date/time range inputs
3. Click through several quick-picks to verify they work as before
4. Manually enter a custom date/time range and press "Watch"

**Expected outcome:** Quick-picks trigger watches; custom ranges are accepted and submitted correctly

**Pass criteria:** Clicking a quick-pick loads the chart without errors; custom ranges submit a valid watch POST request

---

### TC-16 — Error backstop: window genuinely too large returns actionable "shorter range" message

**Type:** api
**Preconditions:** Backend running; a request is made for a window so large that even chunked fetch cannot complete within budget

**Steps:**
1. POST `/watch/SPY` with a window covering multiple full trading days (e.g., 10 days of 6.5-hour sessions)
2. Wait for the backend to attempt the chunked fetch and hit the timeout or concurrency budget
3. Observe the response

**Expected outcome:** Response includes an error message mentioning "shorter range" or "window too large" (from J-28's actionable error path), not a vague "very high-volume" error

**Pass criteria:** HTTP response includes error text matching "shorter" OR "range" (case-insensitive); response code is 400 or 422 (not 200)

---

## Summary

Total test cases: 16
API tests: 8
Browser tests: 5
Artifact checks (unit test regression): 3

**Test distribution:**
- **J-32 (mutable replay speed):** TC-01, TC-02, TC-03, TC-04 (unit/api); TC-11, TC-12 (browser)
- **J-33 (relative spread/impact):** TC-05, TC-06, TC-07 (api/fixture); TC-14 (browser regression)
- **J-34 (chunked fetch):** TC-08, TC-09, TC-10 (api); TC-16 (error path)
- **Regression:** TC-13, TC-14, TC-15

All test cases map to the Definition of Done and Testing Requirements sections of the phase spec.
