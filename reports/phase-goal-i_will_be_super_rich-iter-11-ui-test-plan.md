# Phase goal-i_will_be_super_rich-iter-11 — UI Test Plan

**Phase:** goal-i_will_be_super_rich-iter-11
**Date:** 2026-06-07
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->
<!-- Vague steps like "test the form" or "verify it works" are not acceptable. -->

---

### UT-01 — Cockpit page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the page to fully load (up to 5 seconds)

**Expected Result:**
- Page renders without a blank screen or error message
- The symbol search input field is visible on the page
- The mode selector (with options such as "Simulated", "Historical", "Live") is visible
- No red error banner or crash overlay appears

---

### UT-02 — Symbol search dropdown shows results for a two-character query (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `SymbolSearch` dropdown

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running and has been running long enough for the symbol universe to warm (at least 5 seconds after backend startup)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the symbol search input field
3. Type the single letter "A"
4. Wait 1 second
5. Observe whether any dropdown suggestions appear
6. Type a second letter so the full query is "AA"
7. Wait 1 second for the debounce to fire

**Expected Result:**
- After typing just "A" (step 4–5): the dropdown shows no suggestions and no loading spinner — the field remains blank/empty below the input
- After typing "AA" (step 7): the dropdown populates with one or more symbol suggestions (e.g., "AAPL" or other AA-prefixed tickers)
- No error banner appears at any point

---

### UT-03 — Rapid typing shows only the final query's results — no out-of-order overwrite (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `SymbolSearch` dropdown

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the symbol search input field
3. Type "TS" quickly (both characters within 200ms)
4. Immediately (within 100ms of finishing "TS") clear the field and type "AAP"
5. Wait 1 second for the debounce to fire and the result to display

**Expected Result:**
- The dropdown shows suggestions matching "AAP" (e.g., "AAPL") — not any suggestions from the earlier "TS" query
- No "TS"-matching ticker (e.g., "TSLA") appears in the list alongside or before the "AAP" results
- The dropdown does not flicker between two different result sets

---

### UT-04 — First symbol search after backend restart responds within one second (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `SymbolSearch` dropdown

**Preconditions:**
- Frontend is running at http://localhost:3650
- The backend has just been restarted (within the last 10 seconds) and is healthy
- The backend has been given at least 5–10 seconds to complete its startup symbol-universe warm in the background

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the symbol search input field
3. Type "AAPL"
4. Start a stopwatch (or note the clock time) the moment you type the last letter "L"
5. Wait for the dropdown to show suggestions

**Expected Result:**
- Dropdown suggestions appear within approximately 1 second of typing "AAPL" — no multi-second visible stall
- At least one suggestion (e.g., "AAPL") appears in the dropdown
- No error banner appears

---

### UT-05 — Aborted/cancelled search leaves no stuck "Searching..." indicator (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` — `SymbolSearch` dropdown

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the symbol search input field
3. Type "T" and immediately (within 100ms) type "S", then "L", then "A" in rapid succession, ending with "TSLA" in the field
4. Wait 1.5 seconds for the debounce to settle

**Expected Result:**
- The dropdown shows suggestions for "TSLA" — not for "T", "TS", or "TSL"
- No "Searching..." spinner or loading indicator remains stuck on screen after results appear
- No error banner or "no results" error message appears (the query resolved to a valid result set)

---

### UT-06 — Oversized Historical window shows actionable timeout error on the failure panel (error)

**Type:** error
**Priority:** P1
**Surface:** `/` — error/failure panel

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running with valid Alpaca credentials configured in `apps/backend/.env`
- Historical mode is available

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select "Historical" mode (click the "Historical" option in the mode selector)
3. Click the symbol search input field and type "AAPL", then select "AAPL" from the dropdown
4. In the date/window picker, select a date during a past US market session (e.g., a recent weekday) and choose the widest available time window (a full trading day or multiple hours)
5. Click the "Watch" button
6. Wait up to 15 seconds for a response

**Expected Result:**
- Within approximately 5–12 seconds, an error/failure panel appears on the page
- The failure panel contains the text "try a shorter range" (exact substring — not a generic "please try again" or a blank message)
- The cockpit tape-state panels do NOT populate with any trade data or classification (no "Buyer Control" or "Seller Control" or confidence value appears)
- No browser-level "request timed out" or network error page is shown — the app handles the error and displays it inside the UI

---

### UT-07 — Historical Watch cockpit populates with real values within a few seconds (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — cockpit panels (tape state, confidence, features)

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running with valid Alpaca credentials configured in `apps/backend/.env`
- Historical mode is available

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select "Historical" mode
3. Click the symbol search input field, type "TSLA", and select "TSLA" from the dropdown
4. In the date/window picker, select a recent past US market session date and choose a 2-minute window during market hours (09:30–09:32 ET or similar)
5. Click the "Watch" button
6. Observe the cockpit panels: note when the waiting/progress indicator appears and when the first non-idle classification appears
7. Start a mental timer from when you click "Watch"

**Expected Result:**
- Within 1–2 seconds of clicking "Watch", the cockpit shows a "waiting" progress indicator (an amber pulsing dot or equivalent) — not a blank idle screen
- Within approximately 10 seconds of the data fetch completing, the tape-state panel shows a non-idle classification (e.g., "Buyer Control", "Seller Control", "Balanced", or similar) with a confidence value
- The features panel (trade speed, aggressive buy ratio, etc.) shows real numeric values — not all zeros or placeholders

---

### UT-08 — Re-watching the identical Historical window is near-instant (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — cockpit — re-watch flow

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running with valid Alpaca credentials
- A Historical Watch has already completed successfully at least once in this backend session (the cache has been warmed)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select "Historical" mode
3. Type "TSLA" in the symbol search and select it from the dropdown
4. Choose the same date and 2-minute window used in the first watch (e.g., the same date and 09:30–09:32 ET)
5. Click the "Watch" button and wait for the cockpit to fully populate (tape state visible with a non-idle classification)
6. Click the "Stop" button (or equivalent stop/reset control) to end the current watch
7. Without changing any settings, click the "Watch" button again using the exact same symbol, date, and window
8. Start a stopwatch from when you click "Watch" the second time

**Expected Result:**
- The cockpit re-populates in under 2 seconds (near-instant) — noticeably faster than the first watch
- The same tape-state classification appears as during the first watch (identical real data replayed from cache)
- No loading spinner lingers for more than 2 seconds on the second watch
- No vendor error or "try again" message appears

---

### UT-09 — Vendor hiccup during symbol search produces an empty dropdown with no error banner (error)

**Type:** error
**Priority:** P2
**Surface:** `/` — `SymbolSearch` dropdown

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running but symbol search may return empty results (e.g., no credentials, or backend returns an empty list for the query)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the symbol search input field
3. Type "ZZZ" (a query unlikely to match any real symbol and may return empty results)
4. Wait 1.5 seconds for the debounce to settle

**Expected Result:**
- The dropdown shows no suggestions (an empty state — no list items)
- No red error banner appears anywhere on the page
- No "Searching..." spinner remains stuck in the input field or dropdown
- The input field still accepts further typing without being frozen

---

### UT-10 — Single-character query fires no search request to the backend (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` — `SymbolSearch` dropdown

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- Browser developer tools are open with the Network tab visible (optional — for confirming no request fired)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Open your browser's developer tools and navigate to the Network tab (optional but recommended for evidence)
3. Click the symbol search input field
4. Type the single letter "A"
5. Wait 2 full seconds

**Expected Result:**
- No dropdown suggestions appear beneath the input field
- No network request to `/symbols/search` is visible in the Network tab during the 2-second wait (if developer tools are open)
- No error banner or loading spinner appears
- The input remains responsive to further typing

---

### UT-11 — Free-text symbol entry works without selecting from the dropdown (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — `SymbolSearch` + Watch button

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select "Simulated" mode
3. Click the symbol search input field
4. Type "SIM-BUYER" character by character (do NOT select any dropdown suggestion — ignore any suggestions that appear)
5. Click the "Watch" button without selecting from the dropdown

**Expected Result:**
- The watch is submitted with the symbol "SIM-BUYER"
- The cockpit begins loading — a waiting/progress indicator appears
- Within 10–30 seconds, the tape-state panel shows a non-idle classification (the simulated watch proceeds regardless of whether "SIM-BUYER" appeared in the dropdown suggestions)
- No error message saying "please select a symbol from the list" or similar blocking validation appears

---

### UT-12 — Simulated watch (J-01 regression) still resolves to buyer_control (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — cockpit panels (tape state, confidence)

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select "Simulated" mode from the mode selector
3. Click the symbol search input field and type "SIM-BUYER" (do not select from the dropdown if no suggestion appears — type it directly)
4. Click the "Watch" button
5. Wait up to 60 seconds for the cockpit to populate

**Expected Result:**
- The tape-state panel displays "Buyer Control" (or "buyer_control") as the classification
- A confidence value greater than 0% is shown alongside the classification
- The features panel shows non-zero values for at least some indicators
- The cockpit does not show a blank screen or an error message for the "SIM-BUYER" simulated ticker

---

### UT-13 — Symbol search dropdown returns matches for a real multi-character query (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — `SymbolSearch` dropdown

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running and the symbol universe has warmed (wait at least 5 seconds after backend startup)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the symbol search input field
3. Type "AAPL"
4. Wait 1 second

**Expected Result:**
- The dropdown appears and shows at least one suggestion containing "AAPL"
- The suggestion is clickable and selects "AAPL" as the current symbol when clicked
- No error banner appears

---

### UT-14 — Mode selector controls are all still present and selectable (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/` — mode selector (3-mode controls)

**Preconditions:**
- Frontend is running at http://localhost:3650

**Steps:**
1. Navigate to `http://localhost:3650`
2. Look at the mode selector area of the page
3. Click the "Simulated" option
4. Click the "Historical" option
5. Click the "Live" option (if present; may require credentials)

**Expected Result:**
- All three mode options ("Simulated", "Historical", "Live") are visible in the mode selector
- Clicking "Simulated" highlights/selects it without a crash
- Clicking "Historical" highlights/selects it and reveals the date/window picker UI
- No error banner appears when switching between modes

---

### UT-15 — Waiting/progress indicator appears during a Historical watch fetch (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` — cockpit (row-6 waiting treatment)

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running with valid Alpaca credentials
- Historical mode is selected

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select "Historical" mode
3. Type "TSLA" in the symbol search and select it from the dropdown
4. Choose a recent past market date and a 5-minute window
5. Click the "Watch" button
6. Immediately observe the cockpit — watch what appears in the first 2–3 seconds before data loads

**Expected Result:**
- Within 1–2 seconds of clicking "Watch", a waiting/loading indicator is visible in the cockpit (e.g., an amber pulsing dot, a spinner, or a "waiting" label)
- The cockpit does NOT show a blank idle screen during the fetch — there is always a visual signal that a fetch is in progress
- The waiting indicator disappears once data loads and is replaced by the tape-state classification

---

### UT-16 — Actionable error message is specific, not generic (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` — error/failure panel

**Preconditions:**
- A Historical watch timeout error has been triggered (as in UT-06 above) — the failure panel is visible

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select "Historical" mode
3. Type "AAPL" in the symbol search and select it
4. Choose a very large date range (spanning several hours of market activity)
5. Click the "Watch" button and wait for the timeout error to appear (up to 15 seconds)
6. Read the exact text of the error message in the failure panel

**Expected Result:**
- The failure panel displays a message that includes the phrase "try a shorter range"
- The message does NOT say only "please try again" or display a generic "Error" label with no instruction
- The message is readable and actionable — a user who sees it would understand they should submit a shorter Historical time window

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit page loads without errors | smoke | P1 | `/` |
| UT-02 | Symbol search shows results for two-character query | happy-path | P1 | `/` — SymbolSearch |
| UT-03 | Rapid typing shows only final query results | happy-path | P1 | `/` — SymbolSearch |
| UT-04 | First search after backend restart responds within one second | happy-path | P1 | `/` — SymbolSearch |
| UT-05 | Aborted search leaves no stuck "Searching..." indicator | validation | P2 | `/` — SymbolSearch |
| UT-06 | Oversized Historical window shows actionable timeout error | error | P1 | `/` — failure panel |
| UT-07 | Historical watch cockpit populates with real values quickly | happy-path | P1 | `/` — cockpit |
| UT-08 | Re-watching identical Historical window is near-instant | happy-path | P1 | `/` — cockpit |
| UT-09 | Vendor hiccup produces empty dropdown with no error banner | error | P2 | `/` — SymbolSearch |
| UT-10 | Single-character query fires no search request | validation | P2 | `/` — SymbolSearch |
| UT-11 | Free-text symbol entry works without dropdown selection | regression | P1 | `/` — SymbolSearch + Watch |
| UT-12 | Simulated SIM-BUYER watch resolves to buyer_control | regression | P1 | `/` — cockpit |
| UT-13 | Symbol search returns matches for real multi-character query | regression | P1 | `/` — SymbolSearch |
| UT-14 | Mode selector controls are all present and selectable | regression | P2 | `/` — mode selector |
| UT-15 | Waiting indicator appears during Historical watch fetch | ux | P2 | `/` — cockpit |
| UT-16 | Actionable error message is specific, not generic | ux | P2 | `/` — failure panel |

**P1 tests must all pass for browser QA verdict to be PASS.**
