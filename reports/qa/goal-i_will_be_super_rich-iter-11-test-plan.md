# Goal Iteration 11 Functional Test Plan

**Phase:** goal-i_will_be_super_rich-iter-11  
**Date:** 2026-06-07  
**Frontend Present:** yes

## Phase Goal

Make every credential-gated vendor path responsive and honestly bounded: enforce a real call-level vendor deadline with an actionable message, load busy historical windows fast by design (concurrent fetch + cached reuse + prompt warm-up), and ensure symbol search is warmed/cancellable with no multi-keystroke stalls — closing the final three Must-have journeys (J-28, J-29, J-30).

## Test Cases

### TC-01 — Backend timeout is enforced at the HTTP/SDK boundary

**Type:** api  
**Preconditions:** Backend running; `vendor_call_timeout_seconds` and HTTP-level timeout configured in `apps/backend/app/config.py`

**Steps:**
1. Invoke a Historical watch with a slow/large-response vendor double via `POST /watch/TICKER` with historical body
2. Wait for the vendor call to exceed the HTTP-level deadline
3. Verify the request to `GET /tape/TICKER/state` returns a `RealDataError` with `provider_timeout` reason

**Expected outcome:** The HTTP timeout fires at the vendor-call boundary; no engine instance is created (no tape state returned)

**Pass criteria:** The timeout error surfaces within the configured `vendor_call_timeout_seconds` bound; the error reason is exactly `provider_timeout` (not a generic retry message); `/tape/TICKER/state` returns 404 (no fabricated tape)

---

### TC-02 — Backend timeout is strictly shorter than frontend timeout

**Type:** api  
**Preconditions:** Backend and frontend running; both timeouts configured

**Steps:**
1. Read `vendor_call_timeout_seconds` from `apps/backend/app/config.py` (and the HTTP-level deadline if separate)
2. Read `WATCH_REQUEST_TIMEOUT_MS` from `apps/frontend/lib/config.ts`
3. Assert the backend-effective bound is strictly less than the frontend bound

**Expected outcome:** Backend timeout wins before the frontend client-side timeout fires

**Pass criteria:** `backend_timeout_ms < 12000` (the frontend timeout); documented in config.py with the ordering invariant

---

### TC-03 — Oversize/high-volume window returns actionable message

**Type:** api  
**Preconditions:** Backend running; Historical watch triggered for a simulated oversized window

**Steps:**
1. Invoke `POST /watch/TSLA` with historical params spanning a very large time window (or use a vendor double that returns huge result sets)
2. Wait for the timeout or oversize detection
3. Inspect the error message via `POST /watch/TSLA` response or the failure panel's message field

**Expected outcome:** Error reason is `provider_timeout` with a message variant like "that window is very high-volume — try a shorter range"

**Pass criteria:** Message is distinct from a generic "try again"; it is actionable (names the root cause: window size, high volume); no tape state is fabricated

---

### TC-04 — Trades and quotes are fetched concurrently

**Type:** api  
**Preconditions:** Backend running with the concurrent fetch implementation; a vendor double with measurable timing

**Steps:**
1. Invoke a Historical watch with a timed vendor double that records when `get_stock_trades` and `get_stock_quotes` are called
2. Wait for both to complete
3. Assert that the calls overlapped (second call started before the first finished)
4. Measure total elapsed time vs. the sum of individual call times

**Expected outcome:** Both calls run in parallel; total time ≈ max(t_trades, t_quotes), not the sum

**Pass criteria:** Total fetch time is noticeably less than sequential time (e.g., if each takes 1s, concurrent is ~1s not ~2s); order is preserved (quote-before-trade semantics intact in the engine)

---

### TC-05 — Needless pre-flight round-trip is removed

**Type:** api  
**Preconditions:** Backend running; a vendor double that counts API calls

**Steps:**
1. Invoke `POST /watch/AAPL` for a Historical window with a real symbol
2. Count the number of vendor API calls made by the adapter (use a call-counting double)
3. Repeat with an unknown symbol; count the calls and verify the error reason

**Expected outcome:** Successful fetch makes **one** round-trip (get_stock_trades + get_stock_quotes, concurrent); unknown symbol maps to `symbol_not_tradable` error without a separate `get_asset` pre-flight

**Pass criteria:** Call count is 1 (concurrent trades+quotes) not 2+1 (pre-flight + data); unknown symbol still maps to `symbol_not_tradable`; an empty window still maps to `no_data_for_window`

---

### TC-06 — Cache hit skips vendor round-trip and replays identical data

**Type:** api  
**Preconditions:** Backend running with window cache implemented; backend restarted between test runs to ensure cache state

**Steps:**
1. Invoke `POST /watch/AAPL` for a Historical window (symbol=AAPL, start=2024-01-02 09:30 ET, end=2024-01-02 10:00 ET, feed=iex)
2. Wait for the watch to complete; record the trades/quotes returned via `GET /tape/AAPL/events`
3. Stop the watch (`DELETE /watch/AAPL`)
4. Invoke the exact same Historical watch again
5. Record the trades/quotes; compare with step 2

**Expected outcome:** Second fetch does **not** call the vendor (cache hit); trades and quotes are identical and in the same order

**Pass criteria:** Vendor call count is 1 (first) not 2; the events returned are byte-identical; response time on the second watch is noticeably faster (cache hit latency << network latency)

---

### TC-07 — Warm-up events are delivered with bounded fast-forward, features are deterministic

**Type:** api  
**Preconditions:** Backend running with warm-up fast-forward implemented; a Historical window configured with `warmup_min_events` (e.g., 100)

**Steps:**
1. Invoke a Historical watch and measure the time to the first state snapshot via `GET /tape/TICKER/state`
2. Record the features (trade_speed, aggressive_buy_ratio, etc.) at that snapshot
3. In a separate test, replay the **same window without fast-forward** (manually disable it or use a control flag) and record the features at the equivalent logical event count
4. Compare the two feature sets

**Expected outcome:** Fast-forward enables the first warm-up to appear quickly; the resulting features are **identical** to the un-fast-forwarded replay

**Pass criteria:** Warm-up snapshot arrives within a bounded time (configured fast-forward bound); feature values match (determinism preserved); no trades/quotes are dropped or reordered

---

### TC-08 — Symbol universe is warmed at startup, served from cache

**Type:** api  
**Preconditions:** Backend started fresh (cache empty); no previous universe warm

**Steps:**
1. Start the backend and observe the startup logs for the universe warm task firing
2. Immediately after startup (or after first availability), invoke `GET /symbols/search?q=AAPL` twice
3. Measure the time for both requests; count the vendor calls using a call-counter double

**Expected outcome:** First search may take slightly longer (filling cache if just warmed), but the second search is nearly instant; vendor call count is 0 (both served from the warmed cache)

**Pass criteria:** Universe is warmed in the background during startup (non-blocking); the first search does not trigger a per-request fetch; vendor call count is 0 after the initial startup warm

---

### TC-09 — Symbol search returns empty list on vendor error, never throws

**Type:** api  
**Preconditions:** Backend running with a vendor error scenario (e.g., unavailable credentials, malformed response)

**Steps:**
1. Configure a vendor double that raises an exception (or returns an error) when `get_all_assets()` is called
2. Invoke `GET /symbols/search?q=A`
3. Check the HTTP status and response body

**Expected outcome:** Request returns HTTP 200 with an empty list `[]`; no 5xx error

**Pass criteria:** Status is 200; response is `[]` (not an error object or exception); no error is exposed to the frontend

---

### TC-10 — Min-query is enforced server-side

**Type:** api  
**Preconditions:** Backend running; `symbol_search_min_query` configured (e.g., 2 characters)

**Steps:**
1. Invoke `GET /symbols/search?q=A` (single character, below min)
2. Invoke `GET /symbols/search?q=AA` (at or above min)
3. Count vendor calls in each case

**Expected outcome:** Single-character query returns `[]` without a vendor call; min-query or longer makes a vendor call (or serves from cache if already warmed)

**Pass criteria:** Query below min-length returns `[]` (no vendor round-trip); query at/above min-length is processed normally

---

### TC-11 — Frontend AbortController cancels in-flight searches

**Type:** browser  
**Preconditions:** Frontend running; backend running with search endpoint

**Steps:**
1. Open the symbol search box (Live or Historical mode)
2. Type "T" and wait ~100ms
3. Type "S" (forming "TS") before the first request resolves
4. Observe the network tab or wire a logging interceptor to confirm the first request is aborted
5. Wait for the second request to complete and verify suggestions for "TS" appear

**Expected outcome:** The first request (for "T") is cancelled; the second request (for "TS") completes; only the newer suggestions are shown

**Pass criteria:** First request has an `AbortError` / is marked as cancelled in the network tab; second request completes successfully; the UI shows suggestions matching "TS", not a stale "T" result

---

### TC-12 — Symbol search respects debounce and min-query on the frontend

**Type:** browser  
**Preconditions:** Frontend running; `SYMBOL_SEARCH_DEBOUNCE_MS` and `SYMBOL_SEARCH_MIN_QUERY` configured in `apps/frontend/lib/config.ts`

**Steps:**
1. Open the symbol search box
2. Type "A" and immediately (before debounce fires) type "P" (forming "AP")
3. Wait for the debounce to expire; verify a single request is made (not two)
4. Verify the min-query: type a single character and observe no request fires; type a second character and observe a request fires

**Expected outcome:** Rapid typing fires only one debounced request; min-query of 2 (or configured value) prevents single-character requests

**Pass criteria:** Request count is 1 for rapid typing (debounce works); single-character query fires no request; multi-character query fires a request

---

### TC-13 — Historical watch of liquid symbol with busy market-open window loads fast

**Type:** browser  
**Preconditions:** Frontend running; backend running with credentials; real Alpaca feed available during market hours

**Steps:**
1. Select **Historical** mode
2. Enter `TSLA` (or another liquid symbol)
3. Pick a past date during US market hours; select the **market-open** quick-pick (09:30–09:31 ET)
4. Click **Watch** and measure the time to the cockpit showing real values (trades, features, tape state)
5. Record the time; then immediately re-watch the same symbol + window and measure again

**Expected outcome:** Cockpit populates with real values within the configured bound (~5–10s or configured value); re-watch is near-instant (cache hit)

**Pass criteria:** First load is fast (bounded); second load is noticeably faster (cache); no routine timeout; the cockpit shows real bid/ask/spread/last, recent trades, and feature values; row-6 `waiting` state is visible during fetch (never blank/idle screen)

---

### TC-14 — Oversized/high-volume Historical window surfaces actionable error within bound

**Type:** browser  
**Preconditions:** Frontend running; backend running; credentials configured

**Steps:**
1. Select **Historical** mode
2. Enter a liquid symbol (e.g., `AAPL`)
3. Pick a very large window (e.g., a full week or a busy day with high volume)
4. Click **Watch** and wait
5. Observe the error message that appears

**Expected outcome:** After ~5–10s (or the configured timeout), an error appears on the failure panel with an actionable message like "that window is very high-volume — try a shorter range"

**Pass criteria:** Error appears within the backend timeout bound (< 12s); message is specific and actionable (not a generic "try again"); the cockpit does not populate with fabricated data

---

### TC-15 — Symbol search is instant after backend restart (no multi-second stall)

**Type:** browser  
**Preconditions:** Frontend running; backend restarted fresh (cache cleared)

**Steps:**
1. Kill and restart the backend
2. Wait for the backend to be ready
3. Click the symbol search box and type "AAPL"
4. Measure the time from typing to suggestions appearing
5. Record whether it is a multi-second stall or responsive (< 1s)

**Expected outcome:** First search after startup is responsive (< 1s), not a multi-second stall

**Pass criteria:** Search completes within ~500–1000ms; suggestions appear quickly; no visible "loading" spinner that lasts > 1s

---

### TC-16 — Rapid symbol search shows no pile-up or out-of-order results

**Type:** browser  
**Preconditions:** Frontend running; backend running

**Steps:**
1. Open the symbol search box
2. Type "T", wait 100ms, type "S", wait 100ms, type "L", wait 100ms, type "A"
3. Observe the suggestions that appear after the final keystroke
4. (Optional) Use a request debugger to verify that stale requests are cancelled

**Expected outcome:** Suggestions match "TSLA", not "T" or "TS" or "TSL"; no flicker of out-of-date results

**Pass criteria:** Only the final query result is displayed; no older results overwrite newer ones; cancellation is visible in the network log

---

### TC-17 — Free-text watch entry remains possible despite search

**Type:** browser  
**Preconditions:** Frontend running; backend running (or not running for the "vendor hiccup" case)

**Steps:**
1. Open the symbol search box and start typing
2. Ignore the dropdown suggestions and instead manually type a symbol into the search field
3. Click **Watch** without selecting from the dropdown
4. Verify the watch is processed (whether successful or with an explicit error)

**Expected outcome:** The system accepts free-text entry; watch proceeds regardless of dropdown

**Pass criteria:** Clicking Watch with a free-text entry does not require a dropdown selection; the watch is submitted with the typed symbol

---

### TC-18 — Vendor hiccup in symbol search yields empty list, never an error

**Type:** api  
**Preconditions:** Backend running with a vendor error double configured

**Steps:**
1. Configure the vendor to return an error (e.g., HTTP 5xx, timeout, connection refused)
2. Invoke `GET /symbols/search?q=AA`
3. Verify the response status and body

**Expected outcome:** Returns HTTP 200 with an empty list `[]`

**Pass criteria:** Status is 200 (not 5xx or error); response is `[]`; no error message leaks to the frontend

---

### TC-19 — No-credentials path: search returns empty, startup warm is a no-op

**Type:** api  
**Preconditions:** Backend running with **no** vendor credentials configured (unset API keys)

**Steps:**
1. Verify that the startup warm does not raise an exception (check logs)
2. Invoke `GET /symbols/search?q=AAPL`
3. Verify no error occurs

**Expected outcome:** Startup warm completes (non-blocking); search returns `[]`; no error

**Pass criteria:** Backend starts cleanly without credential errors; search returns 200 with `[]`; the app remains functional in simulator mode

---

### TC-20 — J-01 regression: Simulated ticker still resolves to expected tape state

**Type:** browser  
**Preconditions:** Frontend running; backend running

**Steps:**
1. Select **Simulated** mode
2. Enter `SIM-BUYER` and click **Watch**
3. Wait for the cockpit to populate
4. Read the tape-state panel and confidence

**Expected outcome:** Tape state settles on **buyer_control** with reasonable confidence; features and observations appear

**Pass criteria:** J-01 behavior unchanged; no regression from the search/fetch edits

---

### TC-21 — J-14 regression: Unknown symbol on folded fetch still maps to symbol_not_tradable

**Type:** api  
**Preconditions:** Backend running with credentials

**Steps:**
1. Invoke `POST /watch/FAKESYMBOL123` with historical mode
2. Wait for the error response
3. Verify the failure reason

**Expected outcome:** Error reason is `symbol_not_tradable` (or equivalent), not a timeout or generic error

**Pass criteria:** Unknown symbol is still detected on the folded fetch path (no separate pre-flight needed); correct reason code is returned

---

### TC-22 — J-14 regression: Empty historical window still maps to no_data_for_window

**Type:** api  
**Preconditions:** Backend running with credentials; a historical window with no trades/quotes (e.g., a quiet off-market hour)

**Steps:**
1. Invoke `POST /watch/AAPL` with historical mode for a window known to have no data (e.g., 2024-01-01 00:00–01:00 ET)
2. Wait for the error response
3. Verify the failure reason

**Expected outcome:** Error reason is `no_data_for_window`

**Pass criteria:** Empty window is detected and reported correctly; no fabricated data is returned

---

### TC-23 — Backend unit tests: slow/large vendor double proves deadline enforcement

**Type:** api  
**Preconditions:** Test suite running; `apps/backend/tests/test_vendor_responsiveness.py` exists

**Steps:**
1. Run: `cd apps/backend && python -m pytest tests/test_vendor_responsiveness.py::test_slow_vendor_double -v`
2. Verify the test passes
3. Inspect the test code to confirm it uses a slow-response double (not a time.sleep() wrapper that the background task ignores)

**Expected outcome:** Test passes; the double proves the HTTP timeout fires at the vendor-call boundary

**Pass criteria:** Test passes; double exhibits timeout behavior (call is interrupted, not just abandoned)

---

### TC-24 — Backend unit tests: concurrent fetch timing test

**Type:** api  
**Preconditions:** Test suite running; concurrency test exists

**Steps:**
1. Run: `cd apps/backend && python -m pytest tests/test_vendor_responsiveness.py::test_concurrent_trades_quotes -v`
2. Verify the test passes
3. Inspect the timing assertion to confirm it proves overlap (total ≈ max, not sum)

**Expected outcome:** Test passes; timing assertion proves concurrency

**Pass criteria:** Test passes; total elapsed time is demonstrably less than sequential sum

---

### TC-25 — Backend unit tests: cache-hit test

**Type:** api  
**Preconditions:** Test suite running; cache-hit test exists

**Steps:**
1. Run: `cd apps/backend && python -m pytest tests/test_vendor_responsiveness.py::test_window_cache_hit -v`
2. Verify the test passes
3. Inspect to confirm it calls the same (symbol, start, end, feed) twice and asserts the second call does not invoke the vendor

**Expected outcome:** Test passes; second fetch hits cache and does not call vendor

**Pass criteria:** Test passes; vendor call count is 1 (first) not 2

---

### TC-26 — Backend unit tests: warm-up determinism test

**Type:** api  
**Preconditions:** Test suite running; warm-up test exists

**Steps:**
1. Run: `cd apps/backend && python -m pytest tests/test_vendor_responsiveness.py::test_warmup_fast_forward_determinism -v`
2. Verify the test passes
3. Inspect to confirm features match between fast-forward and non-fast-forward replays

**Expected outcome:** Test passes; features are identical

**Pass criteria:** Test passes; fast-forward is delivery-pacing only, not affecting classification

---

### TC-27 — Backend unit tests: universe warm and cache test

**Type:** api  
**Preconditions:** Test suite running; J-30 backend tests exist

**Steps:**
1. Run: `cd apps/backend && python -m pytest tests/test_vendor_responsiveness.py::test_universe_warm -v`
2. Verify the test passes
3. Inspect to confirm the search after startup does not trigger a per-request fetch

**Expected outcome:** Test passes; universe is warmed and cached

**Pass criteria:** Test passes; no vendor call on search after startup

---

### TC-28 — Full backend test suite passes with zero regressions

**Type:** api  
**Preconditions:** All backend tests

**Steps:**
1. Run: `cd apps/backend && python -m pytest tests/ -v`
2. Verify all tests pass (or only skipped tests remain from iter-10 baseline)

**Expected outcome:** All tests pass; no new failures; regression count = 0

**Pass criteria:** Test count ≥ iter-10 baseline (198 passed / 1 skipped); zero new failures

---

## Summary

**Total test cases:** 28  
**API tests:** 18 (TC-01–TC-09, TC-19, TC-21–TC-28)  
**Browser tests:** 9 (TC-11–TC-17, TC-20)  
**Artifact checks:** 1 (implicit in TC-02, TC-10, TC-12)

**Key journeys covered:**
- **J-28:** Real call-level timeout (TC-01–TC-03, TC-23)
- **J-29:** Fast historical load & concurrent fetch (TC-04–TC-07, TC-13, TC-24–TC-25)
- **J-30:** Warmed/cancellable symbol search (TC-08–TC-12, TC-15–TC-16, TC-27)

**Regressions verified:** J-01, J-14 (TC-20–TC-22)
