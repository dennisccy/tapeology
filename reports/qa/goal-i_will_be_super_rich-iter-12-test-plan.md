# goal-i_will_be_super_rich-iter-12 Functional Test Plan

**Phase:** goal-i_will_be_super_rich-iter-12
**Date:** 2026-06-08
**Frontend Present:** yes

## Phase Goal

The price chart's time axis and all UI dates display in true clock time (real market time for historical, synthetic session clock for simulated) formatted as `dd-MM-yyyy HH:mm:ss`, with every date across the UI using a single shared `dd-MM-yyyy` formatter and the native date picker replaced by a validated custom `dd-MM-yyyy` text input.

## Test Cases

### TC-01 — Backend: Historical epoch anchor is preserved and exposed

**Type:** api
**Preconditions:** Backend is running; the `/tape/{ticker}/history` endpoint is available.

**Steps:**
1. Fetch historical bars via `curl -X GET "http://localhost:8000/api/tape/AAPL/history?start_ts=1609459200&end_ts=1609545600" -H "Accept: application/json"`
2. Parse the JSON response.
3. Verify the response contains an `epoch_anchor` or `display_anchor` field.
4. Record the epoch value (a Unix timestamp representing the first real record's UTC epoch).

**Expected outcome:** The API returns status 200 with a JSON object containing the epoch anchor as a numeric value (seconds since Unix epoch).
**Pass criteria:** Response status is 200 AND the anchor field exists AND is a positive integer representing a valid UTC timestamp.

---

### TC-02 — Backend: Simulated mode synthetic session-start anchor is computed from config

**Type:** api
**Preconditions:** Backend is running; a `SIM-*` ticker has been started in simulated mode; the `/tape/{ticker}/history` endpoint is available.

**Steps:**
1. Fetch history for a `SIM-*` ticker: `curl -X GET "http://localhost:8000/api/tape/SIM-TEST/history?start_ts=0&end_ts=600" -H "Accept: application/json"`
2. Parse the response and extract the `epoch_anchor` field.
3. Verify the anchor value matches a deterministic session-start convention (should be retrievable from `app/config.py`).

**Expected outcome:** The API returns status 200 with an epoch anchor that is a consistent synthetic session-start instant (e.g., a fixed timestamp defined in config, not a wall-clock time).
**Pass criteria:** Response status is 200 AND the anchor is a deterministic value (same for all sim requests in the same session/test run) AND differs from the current wall-clock time.

---

### TC-03 — Backend: Anchor is additive; determinism preserved (same event stream → byte-identical features/state)

**Type:** api
**Preconditions:** Backend unit tests are runnable; the test suite includes a determinism test that replays the same event sequence twice.

**Steps:**
1. Run the backend unit test suite: `cd apps/backend && python -m pytest tests/ -v -k determinism`
2. Check that a test named (or containing) "determinism" or "additive_anchor" passes.
3. Verify the test output confirms that replaying the same ordered events yields byte-identical classification features and state values, regardless of anchor presence.

**Expected outcome:** The unit test passes, confirming that the epoch anchor is purely additive display metadata and does not perturb classification.
**Pass criteria:** Test exits with code 0 AND output contains a passing assertion that feature/state/confidence values are identical across runs with different (or absent) anchor values.

---

### TC-04 — Frontend: Shared dd-MM-yyyy formatter produces correct output

**Type:** artifact
**Preconditions:** The file `apps/frontend/lib/datetime.ts` exists and contains the shared formatter functions.

**Steps:**
1. Read the file `apps/frontend/lib/datetime.ts`.
2. Verify that functions `formatDateDMY` and `formatDateTimeDMY` are exported.
3. Inspect the function bodies to confirm they produce output in `dd-MM-yyyy` and `dd-MM-yyyy HH:mm:ss` (24-hour) formats.
4. Confirm explicit timezone label is included where a time (not just date) is shown.

**Expected outcome:** Both formatter functions exist, handle valid Date objects, and produce the correct format.
**Pass criteria:** Functions exist AND are called `formatDateDMY` / `formatDateTimeDMY` (or clearly equivalent) AND return strings matching pattern `\d{2}-\d{2}-\d{4}` for dates and `\d{2}-\d{2}-\d{4}\s\d{2}:\d{2}` for date-times AND include a zone label in time outputs.

---

### TC-05 — Browser: Historical chart axis shows real market clock time in dd-MM-yyyy HH:mm:ss

**Type:** browser
**Preconditions:** Backend is running on `localhost:8000`; frontend is running on `localhost:3000`; a real symbol (e.g., AAPL) has at least 5 bars of historical data for a known past intraday window (e.g., 2024-01-08 09:30–11:00 US Eastern).

**Steps:**
1. Navigate to `http://localhost:3000/` in Chrome.
2. In the Historical controls, enter a known past date (e.g., `08-01-2024`) in the custom `dd-MM-yyyy` date field.
3. Ensure the time fields are set to a valid trading window (e.g., 09:30–11:00).
4. Click "Watch" or equivalent to load the historical chart.
5. Wait for at least 5 bars to appear in the price chart.
6. Inspect the chart's time axis labels (tick marks and crosshair timestamp).
7. Take a screenshot of the populated chart.
8. Verify the axis shows times like `08-01-2024 09:31:23`, NOT `0` or `120` (elapsed seconds) and NOT `2024-01-08` (ISO format).

**Expected outcome:** The chart renders with a populated candlestick pane (≥5 bars); the time axis displays real market clock times in the format `dd-MM-yyyy HH:mm:ss` with timezone label visible in the crosshair or axis region.
**Pass criteria:** Chart contains ≥5 bars AND axis ticks and crosshair show timestamps matching `\d{2}-\d{2}-\d{4}\s\d{2}:\d{2}:\d{2}` AND no elapsed-time counter (e.g., "0 s", "120 s") is visible on the axis AND screenshot bytes are non-placeholder (real candlestick data visible).

---

### TC-06 — Browser: Simulated mode chart axis shows synthetic session-clock in dd-MM-yyyy HH:mm:ss

**Type:** browser
**Preconditions:** Backend is running; frontend is running; a `SIM-*` ticker is available (e.g., `SIM-TEST`).

**Steps:**
1. Navigate to `http://localhost:3000/`.
2. In the Historical controls, select (or type) a `SIM-*` ticker (e.g., `SIM-TEST`).
3. Click "Watch" to load the simulated chart.
4. Wait for bars to populate the chart pane.
5. Inspect the time axis labels.
6. Take a screenshot of the populated chart.
7. Verify the axis shows synthetic clock times (e.g., `01-01-1970 12:34:56`, a fixed synthetic session date), NOT a 0…600 elapsed-seconds counter.

**Expected outcome:** The simulated chart renders with bars; the time axis displays a synthetic session-start clock face in `dd-MM-yyyy HH:mm:ss` format.
**Pass criteria:** Chart contains bars AND axis shows timestamps matching pattern `\d{2}-\d{2}-\d{4}\s\d{2}:\d{2}:\d{2}` AND is consistent across bar sizes (10/30/60 s switching does not change the clock format or base anchor) AND screenshot is non-placeholder.

---

### TC-07 — Browser: Switching bar sizes (10/30/60 s) preserves real-time axis

**Type:** browser
**Preconditions:** A historical or simulated chart with populated bars is displayed (from TC-05 or TC-06).

**Steps:**
1. Note the current axis time labels and tick positions.
2. Click the bar-size control to change from 10 s to 30 s (or equivalent dropdown/button).
3. Wait for the chart to re-bin and re-render.
4. Verify the time axis labels remain in `dd-MM-yyyy HH:mm:ss` format.
5. Repeat for 60 s.
6. Take screenshots at each bar size.

**Expected outcome:** The time axis format remains `dd-MM-yyyy HH:mm:ss` across all bar sizes; the clock anchor does not revert to elapsed seconds or change format.
**Pass criteria:** All three bar-size screenshots show time axis in `dd-MM-yyyy HH:mm:ss` format AND axis base anchor (epoch) remains the same across sizes AND no elapsed-seconds labels appear.

---

### TC-08 — Browser: Custom dd-MM-yyyy date input parses valid dates and resolves to correct tz-aware instant

**Type:** browser
**Preconditions:** Frontend is running on `localhost:3000`; a historical date picker is visible on the page.

**Steps:**
1. Navigate to `http://localhost:3000/`.
2. Locate the Historical date input field (should be a text input replacing the native `<input type="date">`).
3. Clear any existing value and type a valid date in `dd-MM-yyyy` format (e.g., `15-03-2024`).
4. Verify the field accepts the input without rejecting it.
5. Tab or click away to trigger any blur/validation events.
6. Click "Watch" to confirm the date resolves correctly.
7. Verify that a known historical window loads (bars appear for the expected date).

**Expected outcome:** The custom date input accepts valid `dd-MM-yyyy` entries; the field resolves to the correct local-time instant (same as if the native date picker had been used) with no silent UTC shift.
**Pass criteria:** Input field accepts `dd-MM-yyyy` format AND no validation error is shown AND the loaded chart corresponds to the entered local date AND the window start/end timestamps match the expected local instant (verify via backend `/history` response timestamps or by comparing with J-20 tests).

---

### TC-09 — Browser: Custom date input rejects invalid dates with inline validation error

**Type:** browser
**Preconditions:** Frontend is running; the Historical date input field is visible.

**Steps:**
1. Navigate to `http://localhost:3000/`.
2. Locate the Historical date input field.
3. Enter an invalid `dd-MM-yyyy` entry (e.g., `31-02-2024`, malformed like `15-3-2024` or `2024-03-15`, or empty string).
4. Trigger validation (blur, press Enter, or click "Watch").
5. Inspect the field and surrounding area for an inline error message.
6. Verify that "Watch" does NOT silently load a window (no request made to the backend).

**Expected outcome:** The field displays an inline validation error (e.g., "Invalid date format" or "Date does not exist") and prevents submission.
**Pass criteria:** An error message is visible near the input field AND the field has a visual error state (red border, error icon, etc.) AND no backend request is made when "Watch" is clicked (or "Watch" is disabled).

---

### TC-10 — Browser: Market-status indicator and provider-unavailable messages use dd-MM-yyyy HH:mm:ss formatting

**Type:** browser
**Preconditions:** Backend is running; frontend is running; a real market-status message is displayed (either "Market hours" or an unavailability notice with a timestamp).

**Steps:**
1. Navigate to `http://localhost:3000/`.
2. Locate the market-status indicator (typically top-left or top-right of the page).
3. Inspect any timestamp shown in the status message.
4. If an unavailability or error message appears (e.g., "Provider unavailable since…"), verify the timestamp format.
5. Take a screenshot showing the status area.

**Expected outcome:** Any timestamp in the market-status or provider-unavailable message is formatted as `dd-MM-yyyy HH:mm:ss` (24-hour) with an explicit timezone label. No "Jun 8" locale-specific, `MM/DD/YYYY`, or ISO `YYYY-MM-DD` format is visible.
**Pass criteria:** Status timestamps match pattern `\d{2}-\d{2}-\d{4}\s\d{2}:\d{2}:\d{2}` AND timezone label is present (e.g., "UTC", "EST", local zone abbreviation) AND no alternate date format is visible in the component.

---

### TC-11 — Browser: Watched-source descriptor shows dd-MM-yyyy date format (historical)

**Type:** browser
**Preconditions:** A historical chart is loaded with a real symbol and date (from TC-05).

**Steps:**
1. Navigate to a historical chart view (steps from TC-05).
2. Locate the watched-source descriptor (typically displays something like "Historical AAPL 08-01-2024" or similar).
3. Inspect the date portion.
4. Take a screenshot of the descriptor.

**Expected outcome:** The descriptor shows the date in `dd-MM-yyyy` format (e.g., `Historical AAPL 08-01-2024`).
**Pass criteria:** Descriptor contains a date matching pattern `\d{2}-\d{2}-\d{4}` AND no ISO `YYYY-MM-DD` or locale format (e.g., "Jun 8") is used.

---

### TC-12 — Browser: Real-data trade/event timestamps use dd-MM-yyyy HH:mm:ss format

**Type:** browser
**Preconditions:** A real-data historical chart is loaded; the Recent Trades panel or Event Log is visible and populated with real trades/events.

**Steps:**
1. Navigate to a historical view with real data (e.g., TC-05).
2. Locate the Recent Trades panel or similar panel showing trade/event timestamps.
3. Inspect any timestamp column or in-trade timestamp display.
4. If timestamps are shown, take a screenshot.
5. If no timestamp is currently shown, note it as "no timestamp column present" (satisfies J-35 requirement: "where a timestamp is rendered… it goes through the shared formatter").

**Expected outcome:** If timestamps are rendered for real-data trades/events, they use the `dd-MM-yyyy HH:mm:ss` format via the shared formatter. If no timestamp is shown, the requirement is satisfied by absence (no non-conforming format to fix).
**Pass criteria:** Timestamps (if shown) match pattern `\d{2}-\d{2}-\d{4}\s\d{2}:\d{2}:\d{2}` OR no timestamp column is present (non-blocking).

---

### TC-13 — Browser: Empty historical window yields empty chart (no fabricated timestamps)

**Type:** browser
**Preconditions:** Backend is running; frontend is running.

**Steps:**
1. Navigate to `http://localhost:3000/`.
2. Enter a valid `dd-MM-yyyy` date for a weekend or market-closed day (e.g., `06-07-2024` if a Saturday) or a future date.
3. Set time range to valid trading hours.
4. Click "Watch".
5. Wait for the backend to process the request.
6. Inspect the chart pane.
7. Take a screenshot.

**Expected outcome:** The chart pane shows an empty state (no bars, no axis labels) or displays a message like "No price history for this window yet". The time axis does NOT show fabricated timestamps or placeholder times.
**Pass criteria:** Chart is empty (zero bars) AND no fabricated timestamps are visible on the axis AND an empty-state message may appear (non-blocking).

---

### TC-14 — Backend & Frontend: dd-MM-yyyy formatter and custom input do not introduce J-20 regression (timezone handling)

**Type:** api
**Preconditions:** Backend is running; the row-12 resolver (`resolveLocalWindowInstant`) is available; backend unit tests include a timezone round-trip test.

**Steps:**
1. Run backend unit tests that verify the historical window resolver: `cd apps/backend && python -m pytest tests/ -v -k "timezone or local_window"`
2. Verify tests pass, confirming that the row-12 resolver still correctly interprets local dates without silent UTC shifts.
3. In the frontend, test the custom date input against the resolver: enter a known local date (e.g., `15-03-2024 09:00`) and verify the backend receives the correct tz-aware instant (matching what the old native picker would have sent).

**Expected outcome:** Backend tests confirm the resolver maintains tz-correct behavior; frontend custom input resolves to the same tz-aware instant as the prior native input.
**Pass criteria:** Backend timezone tests pass (exit code 0) AND the frontend date-input resolver produces the same Unix epoch timestamp as the old native picker for the same local date (verify via backend response or explicit resolver call).

---

## Summary

**Total test cases:** 14
- **API tests:** 3 (TC-01, TC-02, TC-03)
- **Browser tests:** 10 (TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14)
- **Artifact checks:** 1 (TC-04)

---

## Key Coverage Notes

- **J-31 Coverage:** TC-05, TC-06, TC-07 directly verify the true-clock chart axis in both historical and simulated modes with real rendered evidence.
- **J-35 Coverage:** TC-04, TC-08, TC-09, TC-10, TC-11, TC-12 verify the shared `dd-MM-yyyy` formatter and its application across all UI date surfaces, plus the custom date input replacing the native picker.
- **Anti-goal guards:** TC-03 verifies the anchor is additive and does not perturb determinism; TC-13 ensures no fabricated data is synthesized for empty windows.
- **Regression guards:** TC-14 confirms no J-20 timezone regression from the custom date input; existing J-01–J-30 backend and frontend unit suites are assumed to remain passing.
