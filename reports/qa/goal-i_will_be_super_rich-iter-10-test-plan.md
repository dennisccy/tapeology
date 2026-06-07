# goal-i_will_be_super_rich-iter-10 Functional Test Plan

**Phase:** goal-i_will_be_super_rich-iter-10
**Date:** 2026-06-07
**Frontend Present:** yes

## Phase Goal

After a Watch click connects, the cockpit always resolves to an honest non-idle terminal state — never a mute/blank cockpit or a confident `live` status over empty data. A connected stream with no first event shows an explicit "waiting" state; if the feeder fails, it surfaces an explicit error; if no data arrives within the configured gap, the status bounds to `stale`.

## Test Cases

### TC-01 — Engine: connected stream with no first event sets `waiting` status

**Type:** api
**Preconditions:** Backend is running; a test uses `FakeLiveProvider` with no-event mode or a paced feeder with empty stream

**Steps:**
1. POST `/watch/TEST-SYMBOL` with mode `live` (or `paced` for sim) and the provider configured to yield no events
2. Wait 100 ms for the feeder to signal stream-open
3. GET `/tape/TEST-SYMBOL/summary` to read `stream_status`
4. Advance time/tick the engine (do NOT send an event)
5. GET `/tape/TEST-SYMBOL/summary` again and confirm status

**Expected outcome:** After stream-open but before any event, `stream_status === "waiting"` (not `connecting`, not `live`); no trade or quote is fabricated in the event list

**Pass criteria:** `stream_status` field in the JSON response equals `"waiting"` and `event_count === 0`

---

### TC-02 — Engine: first event flips `waiting` → `live`

**Type:** api
**Preconditions:** Same as TC-01, stream is in `waiting` status

**Steps:**
1. With the stream in `waiting` status, send the first real trade event via the provider
2. Process the event (call the engine's tick)
3. GET `/tape/TEST-SYMBOL/summary`

**Expected outcome:** `stream_status === "live"` (the rung order: connecting → waiting → live holds)

**Pass criteria:** `stream_status` field equals `"live"` and `recent_trades` list is non-empty

---

### TC-03 — Engine: connected stream with no first event bounds to `stale` after `stale_gap_seconds`

**Type:** api
**Preconditions:** Backend is running; test overrides `CONFIG.stale_gap_seconds` to 1 second; a no-event provider is active

**Steps:**
1. POST `/watch/TEST-SYMBOL` with the no-event provider
2. Wait for the feeder to signal stream-open and confirm `stream_status === "waiting"`
3. Wait 1.5 seconds (exceeding `stale_gap_seconds`)
4. GET `/tape/TEST-SYMBOL/summary` and read `stream_status`

**Expected outcome:** `stream_status === "stale"` (bounded by config, not left at `waiting` forever)

**Pass criteria:** `stream_status` field equals `"stale"`

---

### TC-04 — Engine: feeder exception sets `failed` status and logs the ticker

**Type:** api
**Preconditions:** Backend is running; a mock provider is configured to raise a `ValueError` mid-stream; `caplog` fixture is set up to capture server logs

**Steps:**
1. POST `/watch/TEST-SYMBOL` with the provider configured to raise after stream-open
2. The feeder's event loop encounters the exception
3. GET `/tape/TEST-SYMBOL/summary` and read `stream_status`
4. Inspect the server log for a line naming the ticker and the exception

**Expected outcome:** `stream_status === "failed"` (not stuck at `connecting` or `live`); server log contains a record naming "TEST-SYMBOL" and the exception type

**Pass criteria:** `stream_status` equals `"failed"` AND log output contains the ticker name and exception (e.g., "TEST-SYMBOL.*ValueError" or similar)

---

### TC-05 — Engine: feeder cancellation remains `closed`, not `failed`

**Type:** api
**Preconditions:** Backend is running; a feeder is active and receives a cancel signal (e.g., user calls DELETE /watch)

**Steps:**
1. POST `/watch/TEST-SYMBOL` and let the stream reach `live`
2. DELETE `/watch/TEST-SYMBOL` (sends a cancel signal to the feeder task)
3. Wait for the task to tear down
4. Attempt GET `/tape/TEST-SYMBOL/summary`

**Expected outcome:** `stream_status === "closed"` (or the endpoint returns 404 because the instance is gone); the log does NOT report this as a failure

**Pass criteria:** Response is 404 OR `stream_status === "closed"`; log does NOT contain a `failed` entry for this cancel

---

### TC-06 — Cockpit: renders waiting treatment when `stream_status === "waiting"`

**Type:** browser
**Preconditions:** Frontend is running; backend is running with the isolated `.next` build; a no-event provider is active

**Steps:**
1. Navigate to `/`
2. Use the Chrome MCP to enter a test symbol (e.g., `WAIT-TEST`) and click Watch
3. Wait for the connecting state to resolve
4. Take a screenshot of the cockpit after stream-open but before any first event
5. Assert the DOM for the waiting treatment text

**Expected outcome:** The cockpit displays an explicit message like "Connected to WAIT-TEST (live) — waiting for the first trade…" instead of blank panels; the status dot reads amber (waiting, not green/live)

**Pass criteria:** DOM text includes "waiting" or "first trade" AND does not contain blank/empty panels; status dot is amber/`bg-amber-400`

---

### TC-07 — Cockpit: waiting treatment bounds to a stale or explicit state after gap timeout

**Type:** browser
**Preconditions:** Frontend is running; backend uses `CONFIG.stale_gap_seconds = 2` for testing; no-event provider is active

**Steps:**
1. Navigate to `/` and watch the waiting-treatment symbol
2. Observe the waiting message appears
3. Wait 2.5 seconds (exceeding the gap timeout)
4. Observe the state change and take a screenshot

**Expected outcome:** After the timeout, the cockpit transitions from waiting to an explicit state (e.g., "Stale" or a closed/no-data message) or shows an error

**Pass criteria:** The waiting message is replaced by a distinct state message (not waiting, not blank); status dot is amber (stale/paused) or rose (failed) or closed indicator

---

### TC-08 — TopBar: status dot reads `waiting` as amber pulsing

**Type:** browser
**Preconditions:** Frontend is running; backend is connected with `stream_status === "waiting"`

**Steps:**
1. Navigate to `/` and trigger a watch that enters `waiting` status
2. Observe the TopBar status dot
3. Take a screenshot

**Expected outcome:** The status dot renders in amber (`bg-amber-400`) with `animate-pulse` effect, matching the style of `stale`/`paused` (in-progress, not settled)

**Pass criteria:** Status dot has the CSS class `bg-amber-400` or `amber` and `animate-pulse`

---

### TC-09 — TopBar: status dot reads `failed` as rose

**Type:** browser
**Preconditions:** Frontend is running; backend has a feeder that raises and sets `stream_status === "failed"`

**Steps:**
1. Navigate to `/` and trigger a watch with a provider that raises mid-stream
2. Observe the TopBar status dot when `stream_status` becomes `failed`
3. Take a screenshot

**Expected outcome:** The status dot renders in rose/pink (`bg-rose-500` or similar) matching the existing `StreamFailedState` visual language

**Pass criteria:** Status dot has the CSS class containing `rose` or matches the failure dot color; the error banner also appears on the page

---

### TC-10 — Frontend: snapshot-borne `failed` routes to `StreamFailedState` + error banner

**Type:** browser
**Preconditions:** Frontend is running; backend has a feeder that raises, setting `stream_status === "failed"`

**Steps:**
1. Navigate to `/` and trigger a watch whose feeder raises
2. Wait for the response and the UI to render
3. Observe the page content
4. Take a screenshot

**Expected outcome:** Instead of a blank cockpit, the page displays the existing `StreamFailedState` component plus an error banner at the top (reusing iter-9 patterns), with a message like "Stream failed" or "Connection error"

**Pass criteria:** DOM contains the `StreamFailedState` component text (e.g., "Connection error", warning icon) AND an error banner; no blank panel grid

---

### TC-11 — Frontend: empty cold-start snapshot does NOT short-circuit to a full cockpit

**Type:** browser
**Preconditions:** Frontend is running; backend returns an empty snapshot (no trades, no quotes yet) but `stream_status === "waiting"`

**Steps:**
1. Navigate to `/` and watch a symbol with a no-event provider
2. The backend returns a snapshot with zero trades/quotes and `stream_status === "waiting"`
3. Observe the rendered cockpit
4. Take a screenshot

**Expected outcome:** The page does NOT render a full cockpit with blank panels under a green `live` dot; instead it renders the waiting treatment (or an explicit empty state)

**Pass criteria:** DOM does not contain blank trade rows or blank quote/spread panels; the waiting treatment or explicit state message is visible

---

### TC-12 — J-25 (Real modes): valid Watch always leaves idle within ~1s and resolves to non-idle terminal state

**Type:** browser
**Preconditions:** Frontend is running; backend is running with credentials configured (or FakeAdapter for market-closed testing)

**Steps:**
1. Navigate to `/`
2. In **Historical** mode, enter a real symbol (e.g., `AAPL`) and a past valid window, then click Watch
3. Measure the time from click to the page changing (watch the DOM for a non-idle state)
4. Observe the resolved state after the watch completes
5. Repeat in **Live** mode for a real symbol (include an off-hours test if available)

**Expected outcome:** Idle screen leaves within ~1 second; the watch resolves to streaming data, an explicit waiting/connecting state, an explicit honest state (market_closed, unavailable, etc.), or an explicit error — never idle, never a fake-`live` empty cockpit

**Pass criteria:** Idle screen is replaced within 1 second AND the final state is non-idle (cockpit with data, waiting message, stale, closed, market-closed, or error message visible)

---

### TC-13 — J-26 (Real modes): connected stream with no first event shows explicit "waiting" treatment with symbol/mode

**Type:** browser
**Preconditions:** Frontend is running; a no-event provider is configured (or a page.route HTTP hold to delay snapshot arrival)

**Steps:**
1. Navigate to `/` and trigger a watch on a symbol (e.g., `QUIET-TEST`) that connects but yields no immediate events
2. Wait for the connecting state to resolve to waiting
3. Observe the rendered message and status dot
4. Take a screenshot

**Expected outcome:** The cockpit displays "Connected to QUIET-TEST (live) — waiting for the first trade…" (or similar) with the symbol and mode filled in; the status dot is amber (waiting); no blank panels

**Pass criteria:** DOM text includes "Connected to" + the symbol + "waiting" or "first trade"; no blank trade/quote panels visible; status dot is amber

---

### TC-14 — J-27 (Real modes): feeder failure surfaces explicit error + log, never swallowed

**Type:** browser
**Preconditions:** Frontend is running; backend is running; a provider is configured to raise mid-stream

**Steps:**
1. Navigate to `/` and trigger a watch (e.g., `FAIL-TEST`)
2. Let the feeder connect, then the provider raises/exits
3. Observe the UI state and verify the server log

**Expected outcome:** The UI surfaces an explicit failure state (error banner + `StreamFailedState`) within a bounded time; the server log contains a line naming the ticker and the exception; the cockpit never shows a blank `live` grid

**Pass criteria:** Error banner or `StreamFailedState` is visible; server log contains the ticker name and exception type; no blank panels or stuck "Connecting" state

---

### TC-15 — Regression smoke: J-01 (SIM-BUYER full cockpit)

**Type:** browser
**Preconditions:** Frontend is running; backend is running in simulator mode

**Steps:**
1. Navigate to `/`
2. Select **Simulated** mode (if not default)
3. Enter `SIM-BUYER` and click Watch
4. Wait for the cockpit to populate with a tape state
5. Observe the bid/ask/spread/last, recent trades, features, and tape state

**Expected outcome:** The cockpit shows buyer_control state with high aggressive_buy_ratio and positive buy_price_impact; the feature readouts and event log match J-01 acceptance criteria

**Pass criteria:** tape_state === "buyer_control" AND aggressive_buy_ratio and buy_price_impact are both positive/high values

---

### TC-16 — Regression smoke: J-10 (3-mode controls switch without regression)

**Type:** browser
**Preconditions:** Frontend is running; backend is running

**Steps:**
1. Navigate to `/`
2. Use the data-source selector to switch between Live, Historical, and Simulated
3. For each mode, verify the correct controls appear (symbol search for real modes, date picker for historical, ticker input for sim)
4. Switch back to Simulated and watch `SIM-BUYER`

**Expected outcome:** Selector works; mode-specific controls appear and disappear correctly; `SIM-BUYER` still resolves to buyer_control (no regression)

**Pass criteria:** Correct controls visible per mode AND `SIM-BUYER` produces buyer_control state

---

### TC-17 — Regression smoke: J-21 (synchronous connecting state)

**Type:** browser
**Preconditions:** Frontend is running; backend is running

**Steps:**
1. Navigate to `/` (idle screen)
2. Enter a valid symbol and click Watch
3. Measure the time until the idle screen leaves and a connecting/pending state appears
4. Take a screenshot

**Expected outcome:** Idle screen is replaced with an explicit "Connecting to <SYMBOL>" state within ~1 second

**Pass criteria:** Idle screen gone within 1s AND connecting message or status visible in DOM

---

### TC-18 — Regression smoke: J-24 (inline validation on empty input)

**Type:** browser
**Preconditions:** Frontend is running

**Steps:**
1. Navigate to `/`
2. Leave the symbol field empty (or whitespace) and click Watch
3. Observe the response

**Expected outcome:** An inline validation message appears (e.g., "Enter a ticker symbol") or the Watch button is disabled; no silent no-op

**Pass criteria:** DOM contains a validation message or the Watch button is disabled/prevented

---

## Summary

Total test cases: 18
- API tests: 5 (TC-01, TC-02, TC-03, TC-04, TC-05)
- Browser tests: 13 (TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-16, TC-17, TC-18)

**Key coverage:**
- Engine status rungs: connecting → waiting → live; waiting → stale; failed path
- Feeder exception handling: logged, not swallowed; status flips to failed
- UI treatments: waiting message with symbol/mode; failed error state; no blank cockpits
- Regression smoke: J-01, J-10, J-21, J-24 remain green
- Real modes: J-25, J-26, J-27 verified with credentials or explicit state testing
