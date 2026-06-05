# goal-i_will_be_super_rich-iter-8 Functional Test Plan

**Phase:** goal-i_will_be_super_rich-iter-8
**Date:** 2026-06-05
**Frontend Present:** yes

## Phase Goal

A user selects a historical date/time window in their local timezone (with explicit zone label) or uses US-session quick-picks (Open 9:30 ET / Close 16:00 ET / Full RTH), the fetched window matches the selected local instant (no UTC shift), and the real-historical candlestick chart is rendered with populated real-data prices (J-18 promoted to passing; J-20 closes).

## Test Cases

### TC-01 — Historical picker displays local timezone label

**Type:** browser
**Preconditions:** Frontend is running; no credentials needed (UI-only check)

**Steps:**
1. Navigate to `http://localhost:3000`
2. Click the data-source selector and choose **Historical**
3. Observe the date/time picker controls

**Expected outcome:** The Historical picker displays an explicit timezone label showing the user's local timezone (e.g., "America/New_York" or the local offset like "EST" / "EDT").

**Pass criteria:** A timezone label is visible adjacent to the date/time inputs; the label accurately reflects the system's local timezone (derived from `Intl.DateTimeFormat().resolvedOptions().timeZone` or the local offset).

---

### TC-02 — US-session quick-pick buttons render with local-time annotations

**Type:** browser
**Preconditions:** Frontend is running; Historical mode is selected

**Steps:**
1. Navigate to `/`, select **Historical**
2. Choose a date (e.g., today)
3. Observe the quick-pick buttons

**Expected outcome:** Three quick-pick buttons are present: **Open 9:30 ET**, **Close 16:00 ET**, and **Full RTH (9:30–16:00 ET)**, each annotated with its local-time equivalent for the chosen date (e.g., "Open 9:30 ET → 08:30 local" if in EDT).

**Pass criteria:** All three quick-pick buttons render; each displays both the ET time and a calculated local equivalent; the local times are correct for the chosen date (accounting for DST if applicable).

---

### TC-03 — Quick-pick (Open) fills valid start/end times

**Type:** browser
**Preconditions:** Frontend is running; Historical mode is selected; a date is chosen

**Steps:**
1. Navigate to `/`, select **Historical**
2. Choose a date
3. Click the **Open 9:30 ET** quick-pick button
4. Observe the start and end time inputs

**Expected outcome:** The start time input is populated with 9:30 ET (converted to the local timezone); the end time remains empty or is set to a reasonable default that is greater than the start time.

**Pass criteria:** Start time field contains a valid time that represents 9:30 ET in the user's local timezone; start < end (if end is filled).

---

### TC-04 — Quick-pick (Close) fills valid start/end times

**Type:** browser
**Preconditions:** Frontend is running; Historical mode is selected; a date is chosen

**Steps:**
1. Navigate to `/`, select **Historical**
2. Choose a date
3. Click the **Close 16:00 ET** quick-pick button
4. Observe the start and end time inputs

**Expected outcome:** The end time input is populated with 16:00 ET (converted to the local timezone); the start time remains as entered or a reasonable default.

**Pass criteria:** End time field contains a valid time representing 16:00 ET in the user's local timezone.

---

### TC-05 — Quick-pick (Full RTH) fills 9:30–16:00 ET window in local time

**Type:** browser
**Preconditions:** Frontend is running; Historical mode is selected; a date is chosen

**Steps:**
1. Navigate to `/`, select **Historical**
2. Choose a date
3. Click the **Full RTH (9:30–16:00 ET)** quick-pick button
4. Observe the start and end time inputs

**Expected outcome:** Both start and end time inputs are populated: start = 9:30 ET → local, end = 16:00 ET → local.

**Pass criteria:** Start time represents 9:30 ET in local time; end time represents 16:00 ET in local time; start < end.

---

### TC-06 — Submitted historical window has tz-aware UTC instant (network inspection)

**Type:** api
**Preconditions:** Frontend is running; Historical mode is selected; a DST date is chosen (e.g., June for EDT, or January for EST)

**Steps:**
1. Open browser DevTools (F12) and navigate to the Network tab
2. In the frontend, select **Historical**, choose a date, fill start/end times (or use a quick-pick), then click Watch
3. Inspect the `POST /watch/{ticker}` request body in the Network tab
4. Examine the `start` and `end` fields

**Expected outcome:** The `start` and `end` fields in the POST body are **offset-bearing ISO-8601 strings** (e.g., `2026-06-02T09:30:00-04:00` for EDT or `2026-01-02T09:30:00-05:00` for EST), **not** naive strings without an offset.

**Pass criteria:** 
- `start` and `end` contain a timezone offset (e.g., `-04:00` or `Z`)
- The offset matches the local system timezone for the chosen date
- The UTC instant represented is equal to the selected local time (verify by converting: local time + offset = UTC)

---

### TC-07 — Backend offset-bearing instant is fetched for exact UTC moment

**Type:** api
**Preconditions:** Backend is running and tests are available

**Steps:**
1. Run backend unit test for historical watch with offset-bearing instant:
   ```bash
   cd apps/backend
   .venv/bin/python -m pytest tests/test_history_api.py -v -k "offset" 2>&1
   ```
2. Inspect the test output

**Expected outcome:** A test asserting that when an offset-bearing `start`/`end` is submitted (e.g., `…T09:30:00-04:00`), the backend fetches data for that **exact UTC instant** (not shifted).

**Pass criteria:** Test named `test_history_api.py::*offset*` or similar passes; the test logs confirm the window is fetched for the exact UTC instant represented by the offset-bearing value.

---

### TC-08 — Backend naive datetime still treated as UTC (no regression)

**Type:** api
**Preconditions:** Backend is running; existing historical tests exist

**Steps:**
1. Run the full backend test suite:
   ```bash
   cd apps/backend
   .venv/bin/python -m pytest tests/test_history_api.py tests/test_historical_provider.py tests/test_watch_manager.py -v 2>&1
   ```
2. Verify all tests pass

**Expected outcome:** All existing historical tests (especially those sending naive datetimes) still pass, proving the backend `_parse_window_dt` fallback is intact and unchanged.

**Pass criteria:** No regressions in `test_history_api.py`, `test_historical_provider.py`, `test_watch_manager.py`; all pass.

---

### TC-09 — Real-historical candlestick chart renders with populated real Ford prices

**Type:** browser
**Preconditions:** Frontend is running against a **clean isolated `.next`** (not the shared harness); backend is running against the committed Ford fixture (`apps/backend/tests/fixtures/alpaca/F_20260602_150000_20260602_150200.json`); **no live credentials required** (fixture is offline-reproducible)

**Steps:**
1. Start a clean isolated frontend build (use `NEXT_DIST_DIR` to bypass the shared `.next`)
2. Start the backend pointing to the fixture
3. Navigate to `/`, select **Historical**
4. Enter ticker `F` and select the window 2026-06-02 15:00–15:02 (or per the fixture timestamp range)
5. Click Watch
6. Wait for the cockpit and chart to populate
7. Observe the chart above the cockpit

**Expected outcome:** A **candlestick chart** renders with real-replayed prices from the Ford fixture (the committed 65 trades / 1772 quotes, real epochs, penny-spread prices). Bars reflect the actual traded prices (candlesticks with high/low/open/close). Tape-state markers may appear if state transitions occur during the window.

**Pass criteria:** 
- Chart is visibly populated with candlesticks (not idle "No ticker watched" placeholder)
- Bars contain real price data from the Ford fixture (verifiable by spot-checking a candle's OHLC against the fixture values)
- No "fabricated" or smoothed prices; the chart reflects actual traded prices

---

### TC-10 — Real-historical chart bar-size selector re-renders 10→30→60 s

**Type:** browser
**Preconditions:** Frontend is running with the clean isolated build; historical Ford window is being watched and chart is populated

**Steps:**
1. With the chart displayed for the Ford historical window, locate the **bar-size selector** (usually a set of buttons or dropdown showing "10s", "30s", "60s")
2. Switch from 10 s to 30 s
3. Observe the chart; count the number and height of candlesticks
4. Switch to 60 s
5. Observe the chart again

**Expected outcome:** Each bar-size change re-renders the candlesticks: smaller bar sizes (10s) show more, thinner bars; larger bar sizes (30s, 60s) show fewer, taller (aggregate) bars. The price range and trend remain the same; the granularity changes.

**Pass criteria:** 
- Switching bar size visibly re-renders the chart
- The number of bars and their individual sizes change per the selection (10s > more bars; 60s > fewer bars)
- No flickering or loading delays between switches
- Chart data remains consistent (same price range across all bar sizes)

---

### TC-11 — Quick-pick with no date chosen is disabled or no-op

**Type:** browser
**Preconditions:** Frontend is running; Historical mode is selected; **no date is chosen** (date field is empty)

**Steps:**
1. Navigate to `/`, select **Historical**
2. Leave the date field empty
3. Try to click a quick-pick button (e.g., **Open 9:30 ET**)

**Expected outcome:** The quick-pick button is either disabled (grayed out) or clicking it has no effect (no window is filled, or an error message appears).

**Pass criteria:** Quick-pick buttons do not fill invalid/empty windows when no date is chosen.

---

### TC-12 — End time ≤ start time is rejected (existing 422, no regression)

**Type:** browser
**Preconditions:** Frontend is running; backend is running

**Steps:**
1. Navigate to `/`, select **Historical**
2. Enter a valid date, start time = 16:00, end time = 09:30 (end < start)
3. Click Watch
4. Observe the response

**Expected outcome:** The backend returns a 422 (Unprocessable Entity) error; the frontend displays an error message (e.g., "End time must be after start time").

**Pass criteria:** A 422 error is returned for an invalid window; the existing validation is not regressed.

---

### TC-13 — Empty historical window yields empty chart and `no_data_for_window` state (no fabricated data)

**Type:** browser
**Preconditions:** Frontend is running with clean isolated build; backend is running; credentials are configured (or a known empty-window symbol/date is used)

**Steps:**
1. Navigate to `/`, select **Historical**
2. Enter a symbol and a window known to have no real data (e.g., weekend or after-hours; or use a symbol with no data in the fixture)
3. Click Watch
4. Observe the cockpit and chart

**Expected outcome:** The cockpit displays an explicit "no data for window" message; the chart **remains empty** (no fabricated candles, no placeholder shapes).

**Pass criteria:** 
- An explicit error or state message is shown ("no data for window", "empty result", etc.)
- The chart is visibly empty (no candles, no placeholder bars)
- No fabricated prices or fake candles are rendered

---

### TC-14 — J-17 regression check: simulated chart still renders

**Type:** browser
**Preconditions:** Frontend is running; no credentials needed

**Steps:**
1. Navigate to `/`
2. Select **Simulated** mode
3. Enter ticker `SIM-BUYER` and click Watch
4. Wait for the cockpit to populate
5. Observe the chart above the cockpit

**Expected outcome:** A candlestick chart renders for the simulated buy-control scenario, with bars trending upward and green tape-state markers at transitions (per J-17 spec).

**Pass criteria:** 
- Chart is visibly populated with candlesticks (not idle placeholder)
- Bars show a clear upward trend
- Green markers appear at meaningful tape-state transitions

---

### TC-15 — J-11 regression check: historical AAPL/Ford replay populates cockpit

**Type:** browser
**Preconditions:** Frontend is running with clean isolated build; backend is running; credentials configured (if using live vendor) or using committed Ford fixture

**Steps:**
1. Navigate to `/`, select **Historical**
2. Enter ticker `AAPL` (with credentials) or `F` (fixture)
3. Pick a past window and a replay speed
4. Click Watch
5. Observe the cockpit: bid/ask, recent trades, features, tape state, confidence

**Expected outcome:** The cockpit populates with real values (bid/ask, recent trades with price/size/side resolved, feature readouts, tape state, confidence, observations, event log).

**Pass criteria:** 
- All cockpit panels render with real data
- Recent trades show resolved side (buy/sell, not predominantly unknown)
- Features display numeric values
- Tape state and confidence are shown

---

### TC-16 — J-19 regression check: pause/resume preserves state

**Type:** browser
**Preconditions:** Frontend is running; no credentials needed

**Steps:**
1. Navigate to `/`, watch `SIM-BUYER` in Simulated mode
2. Let the cockpit populate
3. Click **Pause**; observe the tape state, chart, and counters freeze
4. Verify a **PAUSED** indicator is shown
5. Click **Resume**; observe the replay continue

**Expected outcome:** On pause, the display freezes and a PAUSED indicator appears; on resume, the replay continues from where it left off (no data loss, no teardown).

**Pass criteria:** 
- Pause freezes all values and shows PAUSED indicator
- Resume continues the watch without losing state
- Charts and counters resume updating from the paused point (not from a reset state)

---

### TC-17 — DST correctness: ET quick-pick on a DST date resolves to correct UTC

**Type:** api (or browser network inspection)
**Preconditions:** Frontend is running; a DST-affected date is available

**Steps:**
1. In browser DevTools Network tab, navigate to `/`
2. Select **Historical** and choose a date during DST (e.g., June 2, 2026 is in EDT / UTC-04:00)
3. Click the **Open 9:30 ET** quick-pick
4. Click Watch on a symbol
5. Inspect the `POST /watch/{ticker}` request body

**Expected outcome:** The `start` field is `…T09:30:00-04:00` (EDT offset), not a hardcoded `-05:00` (EST offset). The UTC instant is correct: 09:30 EDT = 13:30 UTC.

**Pass criteria:** 
- Offset reflects the actual DST status of the chosen date (EDT or EST, not hardcoded)
- The UTC instant is computed correctly via `America/New_York` timezone logic (DST-aware, not a fixed offset)

---

## Summary

Total test cases: 17
API tests: 4 (TC-07, TC-08, TC-06 network, TC-17 network)
Browser tests: 13 (TC-01 through TC-05, TC-09 through TC-16)
Artifact checks: 0

**Key blockers tested:**
- Local timezone label visible and correct (TC-01)
- Quick-picks render with local-time annotations and fill valid windows (TC-02 through TC-05)
- Submitted window is tz-aware UTC (TC-06, TC-17)
- Backend correctly fetches offset-bearing instants without regression (TC-07, TC-08)
- Real-historical Ford chart renders with populated prices (TC-09, TC-10)
- Empty windows yield empty charts, not fabricated data (TC-13)
- Regressions blocked: simulated chart (TC-14), historical replay (TC-15), pause/resume (TC-16)

All tests are verifiable without live market data (fixture-based) and directly address the DEFINITION OF DONE for J-20 (timezone-correct picker + quick-picks) and J-18 (real-historical chart render).
