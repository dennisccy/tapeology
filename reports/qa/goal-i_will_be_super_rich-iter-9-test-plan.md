# goal-i_will_be_super_rich-iter-9 Functional Test Plan

**Phase:** goal-i_will_be_super_rich-iter-9
**Date:** 2026-06-06
**Frontend Present:** yes

## Phase Goal

Every Watch click acknowledges itself within ~1 second with an explicit pending/connecting state, and every outcome (streaming data, empty window, provider unavailable, unknown symbol, market closed, request timeout, unreachable backend, failed initial stream, or invalid input) resolves to a distinct, visible, bounded on-screen state — never a silent no-op and never an infinite spinner.

## Test Cases

### TC-01 — Pending state appears synchronously on Watch click (Simulated)

**Type:** browser
**Preconditions:** Frontend running on localhost:3000; app in Simulated mode; idle cockpit displayed.

**Steps:**
1. Navigate to http://localhost:3000
2. Verify Simulated mode is active (mode selector shows "SIM")
3. Click the Watch button with a valid symbol (e.g., "AAPL")
4. Take a screenshot within 100ms of the click

**Expected outcome:** The cockpit immediately shows a pending/connecting state with "Connecting to AAPL…" text and the connecting-dot affordance (CONN_DOT.connecting), before any tape data is rendered.

**Pass criteria:** Screenshot shows the pending "Connecting to AAPL…" state with the connecting dot visible within 100ms; the idle cockpit never persists between click and pending state.

---

### TC-02 — Pending state appears synchronously on Watch click (Live)

**Type:** browser
**Preconditions:** Frontend running on localhost:3000; app in Live mode; idle cockpit displayed.

**Steps:**
1. Navigate to http://localhost:3000
2. Verify Live mode is active (mode selector shows "LIVE")
3. Click the Watch button with a valid symbol (e.g., "AAPL")
4. Take a screenshot within 100ms of the click

**Expected outcome:** The cockpit immediately shows a pending/connecting state with "Connecting to AAPL…" text and the connecting-dot affordance, before any tape data is rendered.

**Pass criteria:** Screenshot shows the pending "Connecting to AAPL…" state with the connecting dot visible within 100ms; the idle cockpit never persists between click and pending state.

---

### TC-03 — Pending state appears synchronously on Watch click (Historical)

**Type:** browser
**Preconditions:** Frontend running on localhost:3000; app in Historical mode; idle cockpit displayed; a valid time window is selected.

**Steps:**
1. Navigate to http://localhost:3000
2. Verify Historical mode is active (mode selector shows "HIST")
3. Set a valid historical window (e.g., start: 2024-01-01, end: 2024-01-02)
4. Click the Watch button with a valid symbol (e.g., "AAPL")
5. Take a screenshot within 100ms of the click

**Expected outcome:** The cockpit immediately shows a pending/connecting state with "Connecting to AAPL…" text and the connecting-dot affordance, before any tape data is rendered.

**Pass criteria:** Screenshot shows the pending "Connecting to AAPL…" state with the connecting dot visible within 100ms; the idle cockpit never persists between click and pending state.

---

### TC-04 — Backend timeout resolves to explicit bounded error (mocked slow adapter)

**Type:** api
**Preconditions:** Backend running on localhost:8000; a mocked adapter that simulates a 5+ second delay on `fetch_historical` or `get_market_clock`.

**Steps:**
1. Run backend unit test that mocks `adapter.fetch_historical` to block indefinitely (or exceed `vendor_call_timeout_seconds`)
2. Send `POST /watch` request with valid symbol and mode=historical, observing the timeout bounds
3. Verify the response status and error detail

**Expected outcome:** The `POST /watch` endpoint returns within the configured `vendor_call_timeout_seconds` (e.g., 5 seconds) with HTTP 422 or 504 status and a response body with `reason: "provider_timeout"`.

**Pass criteria:** HTTP status is 422 or 504; response JSON includes `reason: "provider_timeout"` (or similar distinct key); the response arrives within `vendor_call_timeout_seconds + 0.5s`; no engine instance is created (watch is not registered) after the timeout.

---

### TC-05 — Backend timeout error is wrapped in asyncio.wait_for

**Type:** artifact
**Preconditions:** Backend source code is available.

**Steps:**
1. Open `apps/backend/app/main.py`
2. Locate the `_watch_historical` function
3. Search for `adapter.fetch_historical` and verify it is wrapped in `asyncio.wait_for(..., timeout=CONFIG.vendor_call_timeout_seconds)`
4. Locate the `_watch_live` function
5. Search for `adapter.get_market_clock` and verify it is wrapped in `asyncio.wait_for(..., timeout=CONFIG.vendor_call_timeout_seconds)`

**Expected outcome:** Both outbound vendor calls are wrapped in `asyncio.wait_for` with a timeout sourced from `CONFIG.vendor_call_timeout_seconds` (no inline literal).

**Pass criteria:** Both `fetch_historical` and `get_market_clock` calls are wrapped in `asyncio.wait_for` with the config constant; the timeout value is NOT a hardcoded literal.

---

### TC-06 — Backend timeout config constant exists and has no magic number

**Type:** artifact
**Preconditions:** Backend source code is available.

**Steps:**
1. Open `apps/backend/app/config.py`
2. Search for `vendor_call_timeout_seconds` definition
3. Verify it is a float with a comment explaining its purpose

**Expected outcome:** A `vendor_call_timeout_seconds` constant exists in config, is defined as a float (e.g., 5.0), and has a comment such as "Timeout (in seconds) for a single outbound vendor call" to indicate no magic-number literal.

**Pass criteria:** `vendor_call_timeout_seconds` is defined in config.py with a `*_seconds` naming convention and a comment explaining its purpose.

---

### TC-07 — Frontend client-side timeout aborts request on slow backend

**Type:** browser
**Preconditions:** Frontend running on localhost:3000 with backend on a non-responsive server (e.g., a server that accepts connections but never responds, or responds after >10 seconds).

**Steps:**
1. Start frontend pointing to a hung backend (e.g., via NEXT_PUBLIC_API_URL environment variable)
2. Click Watch with a valid symbol
3. Wait for the frontend to display an error (should occur within ~5-6 seconds if WATCH_REQUEST_TIMEOUT_MS is ~5000ms)
4. Take a screenshot of the error state

**Expected outcome:** The pending "Connecting…" state is replaced by an explicit error message (e.g., "Market data provider timed out" or "Request timed out") within the configured timeout window; the UI does not hang.

**Pass criteria:** An explicit error message is rendered within `WATCH_REQUEST_TIMEOUT_MS + 0.5s` (e.g., within 5.5 seconds for a 5000ms timeout); the error message text is visible in the screenshot; the UI is responsive and does not show an infinite spinner.

---

### TC-08 — Frontend timeout config constant exists and has no magic number

**Type:** artifact
**Preconditions:** Frontend source code is available.

**Steps:**
1. Open `apps/frontend/lib/config.ts`
2. Search for `WATCH_REQUEST_TIMEOUT_MS` definition
3. Verify it is a number (milliseconds) with a comment

**Expected outcome:** A `WATCH_REQUEST_TIMEOUT_MS` constant exists in config.ts, is defined as a number (e.g., 5000), and has a comment explaining its purpose.

**Pass criteria:** `WATCH_REQUEST_TIMEOUT_MS` is defined in lib/config.ts as a number constant with a comment; no inline timeout literal appears in `watchTicker` or `fetchInitialSnapshot` calls.

---

### TC-09 — Failed initial snapshot connection surfaces error (backend stopped)

**Type:** browser
**Preconditions:** Frontend running on localhost:3000; backend running; app in any mode with valid input.

**Steps:**
1. Click Watch with a valid symbol
2. After the pending "Connecting…" state appears, stop the backend (e.g., `pkill uvicorn`)
3. Wait up to ~5 seconds for the error to surface
4. Take a screenshot of the error state

**Expected outcome:** An explicit "couldn't connect to the tape stream" or similar error message is rendered on the screen; the pending state is replaced by an error panel (existing `ProviderUnavailable` component or the TopBar error banner); no empty `catch` swallows the failure.

**Pass criteria:** An explicit error message is visible in the screenshot within ~5 seconds; the error message mentions connection failure or backend unreachable; the cockpit does not remain in the pending state indefinitely.

---

### TC-10 — Empty symbol input gives immediate inline validation feedback

**Type:** browser
**Preconditions:** Frontend running on localhost:3000; app in Simulated or Live mode; TopBar symbol input field is empty or contains only whitespace.

**Steps:**
1. Navigate to http://localhost:3000 in Simulated or Live mode
2. Ensure the symbol input field is empty
3. Hover over or click the Watch button
4. Take a screenshot

**Expected outcome:** An inline validation message (e.g., "Enter a ticker symbol") is displayed near the symbol input or the Watch button is disabled; no Watch request is sent.

**Pass criteria:** Either (a) a visible inline message appears, or (b) the Watch button is visibly disabled (grayed out, cursor shows "not-allowed"); clicking the disabled button produces no request.

---

### TC-11 — Invalid historical time window gives immediate inline validation feedback

**Type:** browser
**Preconditions:** Frontend running on localhost:3000; app in Historical mode; a valid symbol is entered; the time window is invalid (e.g., end date before start date, or missing start/end).

**Steps:**
1. Navigate to http://localhost:3000 in Historical mode
2. Enter a valid symbol (e.g., "AAPL")
3. Set an invalid time window (e.g., start: 2024-01-02, end: 2024-01-01)
4. Hover over or click the Watch button
5. Take a screenshot

**Expected outcome:** An inline validation message (e.g., "Choose a valid time window" or "End date must be after start date") is displayed, or the Watch button is disabled; no Watch request is sent.

**Pass criteria:** Either (a) a visible inline message appears, or (b) the Watch button is visibly disabled; clicking does not send a request.

---

### TC-12 — Pending state clears on successful cockpit load

**Type:** browser
**Preconditions:** Frontend running on localhost:3000; backend running; app in Simulated mode.

**Steps:**
1. Navigate to http://localhost:3000
2. Click Watch with a valid symbol (e.g., "AAPL")
3. Wait for the cockpit to populate with tape data (should occur within ~2-3 seconds)
4. Take a screenshot of the loaded cockpit

**Expected outcome:** The pending "Connecting to AAPL…" state is replaced by the fully populated cockpit (with tape rows, observations, confidence, etc.); the cockpit displays real tape data, not fabricated or placeholder data.

**Pass criteria:** The cockpit shows populated rows (tape events, observations, confidence score, etc.); no "Connecting…" text is visible; the tape data is consistent with the backend's engine output.

---

### TC-13 — Pending state clears on honest error panel (provider unavailable)

**Type:** browser
**Preconditions:** Frontend running on localhost:3000; backend running; app in Live or Historical mode; a symbol/window is selected that will trigger a provider-unavailable error (e.g., a weekend day in Live mode, or a symbol with no historical data).

**Steps:**
1. Navigate to http://localhost:3000 in Live or Historical mode
2. Set input to trigger a provider-unavailable error
3. Click Watch
4. Wait for the error panel to render (should occur within ~2-3 seconds)
5. Take a screenshot of the error panel

**Expected outcome:** The pending "Connecting…" state is replaced by an honest non-cockpit error panel (e.g., `ProviderUnavailable` component) with a clear message (e.g., "Market is closed" or "No data available for this window"); the cockpit is not shown with fabricated or cached data.

**Pass criteria:** An explicit error panel is rendered (not the cockpit); the error message text is visible and distinct from other errors; the UI is responsive.

---

### TC-14 — No regression: J-01 Simulated cockpit populates

**Type:** browser
**Preconditions:** Frontend running on localhost:3000; backend running; app in Simulated mode.

**Steps:**
1. Navigate to http://localhost:3000
2. Click Watch with a valid symbol (e.g., "AAPL")
3. Wait for the cockpit to populate
4. Verify the cockpit displays tape rows and data

**Expected outcome:** The cockpit populates with tape data within ~2-3 seconds; tape rows are visible and contain tape events; the observations, confidence, and other fields are populated.

**Pass criteria:** Cockpit has at least 5 tape rows populated; confidence score is displayed; no empty state persists after Watch click; data matches backend snapshot.

---

### TC-15 — No regression: J-09 Stop button returns to idle

**Type:** browser
**Preconditions:** Frontend running on localhost:3000; backend running; app in Simulated mode with an active cockpit displayed.

**Steps:**
1. Navigate to http://localhost:3000 and load a cockpit
2. Click the Stop button
3. Verify the cockpit is cleared and idle state is shown

**Expected outcome:** The cockpit is cleared; the idle state with no tape rows is displayed; the mode selector and input fields are visible again.

**Pass criteria:** Cockpit is cleared (no tape rows visible); idle state is rendered.

---

### TC-16 — No regression: J-10 Mode switch changes display

**Type:** browser
**Preconditions:** Frontend running on localhost:3000; backend running.

**Steps:**
1. Navigate to http://localhost:3000
2. Verify the mode selector (SIM/LIVE/HIST) is visible
3. Switch from Simulated to Live
4. Verify the UI updates to show the Live mode input
5. Switch to Historical
6. Verify the historical time window controls appear

**Expected outcome:** Switching modes updates the TopBar controls and resets the cockpit to idle; each mode has the correct controls (symbol input for SIM/LIVE, symbol + time window for HIST).

**Pass criteria:** Mode selector switches without errors; TopBar controls update per mode; cockpit resets to idle.

---

### TC-17 — No regression: J-14 Honest failure panels render unchanged

**Type:** browser
**Preconditions:** Frontend running on localhost:3000; backend running; app in Live mode during market-closed hours or Historical mode with a symbol/window that has no data.

**Steps:**
1. Navigate to http://localhost:3000 in Live mode during market-closed hours
2. Click Watch
3. Verify a market-closed error panel is rendered
4. Switch to Historical mode
5. Select a symbol/window with no data (e.g., a future date)
6. Click Watch
7. Verify a no-data error panel is rendered

**Expected outcome:** Honest failure panels (market-closed, no-data-for-window, provider-unavailable) are rendered with clear error messages; the cockpit is not shown with fabricated data.

**Pass criteria:** Error panels are rendered with appropriate messages; no cockpit is displayed when data is unavailable; error messages are distinct and accurate.

---

### TC-18 — No silent dead-click on invalid input (empty symbol)

**Type:** browser
**Preconditions:** Frontend running on localhost:3000; app in Simulated mode.

**Steps:**
1. Navigate to http://localhost:3000
2. Leave the symbol input field empty
3. Click the Watch button
4. Observe the UI for 1 second

**Expected outcome:** The Watch button is disabled or an inline error message appears; no request is sent to the backend; the UI changes immediately (no silent no-op).

**Pass criteria:** Either the Watch button is visibly disabled, or an inline validation message is displayed; no network request is made (verify with browser dev tools); the UI is not frozen or in a pending state.

---

### TC-19 — Backend timeout: no engine created after vendor call timeout

**Type:** api
**Preconditions:** Backend running; unit tests available.

**Steps:**
1. Run the backend unit test that mocks `adapter.fetch_historical` to timeout (or indefinitely block)
2. Assert that after the `asyncio.TimeoutError` is caught and converted to an HTTP 422 response, the watch is NOT registered in the engine
3. Verify that no tape state is created for the symbol

**Expected outcome:** After a vendor call timeout, the `POST /watch` request returns an error and the watch is not registered; no tape is fabricated.

**Pass criteria:** Test assertion passes: `engine.watches[symbol]` does not exist after timeout; response includes `reason: "provider_timeout"`; no tape data is returned.

---

### TC-20 — Frontend AbortController timeout uses single config constant

**Type:** artifact
**Preconditions:** Frontend source code is available.

**Steps:**
1. Open `apps/frontend/lib/api.ts`
2. Locate the `watchTicker` function
3. Search for `AbortController` instantiation
4. Verify the timeout is sourced from `WATCH_REQUEST_TIMEOUT_MS` from `lib/config.ts` and not an inline literal
5. Repeat for `fetchInitialSnapshot`

**Expected outcome:** Both `watchTicker` and `fetchInitialSnapshot` use an `AbortController` with a timeout from the single `WATCH_REQUEST_TIMEOUT_MS` constant; no inline timeout literals (e.g., no hardcoded `5000` in the function).

**Pass criteria:** `AbortController` timeout is set via `WATCH_REQUEST_TIMEOUT_MS` (imported from config); no inline millisecond literal is present in the abort setup.

---

### TC-21 — useTapeStream does not swallow initial-snapshot failure

**Type:** artifact
**Preconditions:** Frontend source code is available.

**Steps:**
1. Open `apps/frontend/lib/useTapeStream.ts`
2. Locate the initial-snapshot fetch call (typically `fetchInitialSnapshot()`)
3. Verify there is no `.catch(() => {})` that swallows the error
4. Verify the catch block (if present) handles the error explicitly (e.g., sets a `connectStatus` or error state)

**Expected outcome:** The initial-snapshot fetch error is not silently swallowed; it is either propagated to the caller or explicitly handled with a state update (e.g., `connectStatus = "failed"`).

**Pass criteria:** No empty `.catch(() => {})` exists for the initial-snapshot fetch; any catch block logs or records the error via state.

---

### TC-22 — WebSocket pre-snapshot error surfaces as connect failure

**Type:** artifact
**Preconditions:** Frontend source code is available; `useTapeStream.ts` is the hook handling the WebSocket.

**Steps:**
1. Open `apps/frontend/lib/useTapeStream.ts`
2. Locate the WebSocket `onerror` and `onclose` handlers
3. Verify that if `onerror` or `onclose` fires BEFORE any snapshot is received, an explicit error state is set (e.g., `connectStatus = "failed"`)
4. Verify `app/page.tsx` renders this error state as a visible panel or banner

**Expected outcome:** A pre-snapshot WS error/close triggers an explicit error state that is rendered to the user; the UI does not remain in a pending or frozen state.

**Pass criteria:** `onerror` or early `onclose` sets an explicit error state; `app/page.tsx` renders it visibly (e.g., via the TopBar error banner or a failure panel).

---

## Summary

Total test cases: 22
- API tests: 3 (TC-04, TC-19, and config validation in TC-05, TC-06, TC-08, TC-20, TC-21, TC-22 as artifact checks)
- Browser tests: 11 (TC-01, TC-02, TC-03, TC-07, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-16, TC-17, TC-18)
- Artifact checks: 8 (TC-05, TC-06, TC-08, TC-20, TC-21, TC-22 — code inspection for no magic numbers, proper timeout wrapping, error handling)

**Coverage alignment:**
- **J-21 (Pending state):** TC-01, TC-02, TC-03, TC-12, TC-14
- **J-22 (Backend & frontend timeout):** TC-04, TC-05, TC-06, TC-07, TC-08, TC-19, TC-20
- **J-23 (Failed connection):** TC-09, TC-21, TC-22
- **J-24 (Input validation):** TC-10, TC-11, TC-18
- **Regression (J-01–J-20):** TC-14, TC-15, TC-16, TC-17
- **Anti-goal no-silent-dead-clicks:** TC-18
- **Anti-goal no-fabricated-data:** TC-13, TC-19
