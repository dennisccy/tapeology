# Goal Iteration 7 Functional Test Plan

**Phase:** goal-i_will_be_super_rich-iter-7  
**Date:** 2026-06-05  
**Frontend Present:** yes

## Phase Goal

Render-verify the prediction chart (J-17/J-18) and build honest pause/resume (J-19) so watches can be frozen without teardown, with visible PAUSED indicator, and resume continues from where it left off.

## Test Cases

### TC-01 — Chart renders SIM-BUYER with emerald buyer_control marker

**Type:** browser  
**Preconditions:** Backend running, frontend running on isolated dist (NEXT_DIST_DIR set), SIM-BUYER dataset available

**Steps:**
1. Navigate to `/`
2. Select provider `SIM-BUYER`
3. Click **Watch**
4. Wait 3 seconds for chart to populate
5. Screenshot the price chart area

**Expected outcome:** Candlesticks render; buyer_control marker shows as **emerald** dot; candles trend upward  
**Pass criteria:** Screenshot shows at least 3 candlestick bars with visible emerald marker and upward price movement

---

### TC-02 — Chart renders SIM-SELLER with rose seller_control marker

**Type:** browser  
**Preconditions:** Backend running, frontend running on isolated dist, SIM-SELLER dataset available

**Steps:**
1. Navigate to `/`
2. Select provider `SIM-SELLER`
3. Click **Watch**
4. Wait 3 seconds for chart to populate
5. Screenshot the price chart area

**Expected outcome:** Candlesticks render; seller_control marker shows as **rose** dot; candles trend downward  
**Pass criteria:** Screenshot shows at least 3 candlestick bars with visible rose marker and downward price movement

---

### TC-03 — Chart renders absorption markers (SIM-BIDABS)

**Type:** browser  
**Preconditions:** Backend running, frontend running on isolated dist, SIM-BIDABS dataset available

**Steps:**
1. Navigate to `/`
2. Select provider `SIM-BIDABS`
3. Click **Watch**
4. Wait 3 seconds for chart to populate
5. Screenshot the price chart area

**Expected outcome:** Candlesticks render; absorption markers show as **amber** dots; price held relatively flat  
**Pass criteria:** Screenshot shows candlestick bars with visible amber markers and minimal price swing

---

### TC-04 — Chart renders absorption markers (SIM-ASKABS)

**Type:** browser  
**Preconditions:** Backend running, frontend running on isolated dist, SIM-ASKABS dataset available

**Steps:**
1. Navigate to `/`
2. Select provider `SIM-ASKABS`
3. Click **Watch**
4. Wait 3 seconds for chart to populate
5. Screenshot the price chart area

**Expected outcome:** Candlesticks render; absorption markers show as **amber** dots; price held relatively flat  
**Pass criteria:** Screenshot shows candlestick bars with visible amber markers and minimal price swing

---

### TC-05 — Chart bar-size selector renders at 10s, 30s, 60s

**Type:** browser  
**Preconditions:** Backend running, frontend running on isolated dist, SIM-BUYER watched and populating

**Steps:**
1. Navigate to `/` and watch SIM-BUYER (wait 3 seconds)
2. Locate the bar-size selector (10 / 30 / 60 buttons)
3. Verify **10 s** button shows; screenshot chart
4. Click **30 s**; wait 1 second; screenshot chart
5. Click **60 s**; wait 1 second; screenshot chart

**Expected outcome:** Selector visible; clicking each button re-renders candles with wider OHLC periods  
**Pass criteria:** All three screenshots captured; each shows different candle density (10s most granular, 60s most aggregated)

---

### TC-06 — Chart hidden in Live mode

**Type:** browser  
**Preconditions:** Backend running, frontend running on isolated dist, SIM-BUYER watched

**Steps:**
1. Navigate to `/` and watch SIM-BUYER
2. Locate provider selector
3. Switch to **Live** mode
4. Screenshot the watch area

**Expected outcome:** Price chart disappears; cockpit (quote / recent trades) still visible  
**Pass criteria:** Screenshot shows no candlestick canvas; quote/tape area still present

---

### TC-07 — Chart renders historical replay (credentialed surface confirmed)

**Type:** browser  
**Preconditions:** Backend running, frontend running on isolated dist, real-market credentials available (optional)

**Steps:**
1. Navigate to `/`
2. Select a real symbol (e.g., AAPL or another historical ticker with credentials)
3. Select **Historical** mode with a real provider
4. Click **Watch**
5. Wait 3 seconds; screenshot the chart
6. Compare on-screen bar prices against `GET /tape/{ticker}/history?bar=30` response

**Expected outcome:** Candlesticks reflect real historical prices; on-screen bars match backend-served OHLC  
**Pass criteria:** Screenshot shows candlesticks; bar high/low/open/close visually match API `/history` response (credentialed run) OR surface + bar-match confirmed (non-credentialed run)

---

### TC-08 — Pause freezes cockpit and chart

**Type:** browser  
**Preconditions:** Backend running, frontend running on isolated dist, SIM-BUYER watched and populating

**Steps:**
1. Navigate to `/` and watch SIM-BUYER
2. Wait 3 seconds; note the recent-trades count and chart candles
3. Click **Pause** button
4. Wait 3 seconds
5. Verify recent-trades count unchanged; verify chart frozen
6. Screenshot the watch area with PAUSED indicator

**Expected outcome:** Pause button replaced by Resume; PAUSED indicator shows (amber); recent trades count frozen; chart stops updating  
**Pass criteria:** Screenshot shows PAUSED amber dot/label; trade count unchanged after pause wait; chart candles identical to pre-pause

---

### TC-09 — Resume continues stream without backfill

**Type:** browser  
**Preconditions:** Paused watch (TC-08 completed), backend running

**Steps:**
1. Continue from TC-08 (watch is paused)
2. Note current recent-trades count = N and chart bar count = B
3. Click **Resume** button
4. Wait 3 seconds
5. Record final recent-trades count and chart bar count
6. Calculate: (final count - N) / 3s elapsed

**Expected outcome:** Resume button replaced by Pause; stream continues; trade count increases naturally (not jumped); chart accrues new candles at normal cadence  
**Pass criteria:** New trades and candles appear at streaming rate (~1-2 per second), no sudden jump indicating backfill

---

### TC-10 — Stop after Pause still tears down watch

**Type:** browser  
**Preconditions:** Paused watch (TC-08), backend running

**Steps:**
1. Have a paused watch visible
2. Click **Stop** button
3. Wait 1 second
4. Attempt to fetch `GET /watch/{ticker}/state`

**Expected outcome:** Cockpit returns to idle (no chart, no quote, no recent trades); API returns 404  
**Pass criteria:** Screenshot shows idle state (no watched data); API request 404 returned

---

### TC-11 — Pause idempotent (pause when already paused)

**Type:** api  
**Preconditions:** Backend running, ticker watched, already paused

**Steps:**
1. Watch a ticker: `curl -X POST http://localhost:8000/watch/AAPL -d '{"provider":"..."}' -H 'Content-Type: application/json'`
2. Pause: `curl -X POST http://localhost:8000/watch/AAPL/pause`
3. Get snapshot: `curl http://localhost:8000/tape/AAPL/summary`
4. Pause again: `curl -X POST http://localhost:8000/watch/AAPL/pause`
5. Get snapshot: `curl http://localhost:8000/tape/AAPL/summary`

**Expected outcome:** Both pause requests return 200; second pause snapshot identical to first (no double-pause state)  
**Pass criteria:** Response status 200; `paused=true` and `stream_status="paused"` both times; no error thrown; no extra task created

---

### TC-12 — Resume idempotent (resume when not paused)

**Type:** api  
**Preconditions:** Backend running, ticker watched and streaming (not paused)

**Steps:**
1. Watch a ticker: `curl -X POST http://localhost:8000/watch/AAPL -d '{"provider":"..."}' -H 'Content-Type: application/json'`
2. Get initial snapshot: `curl http://localhost:8000/tape/AAPL/summary`
3. Resume (not paused): `curl -X POST http://localhost:8000/watch/AAPL/resume`
4. Get snapshot: `curl http://localhost:8000/tape/AAPL/summary`

**Expected outcome:** Resume request returns 200; snapshot unchanged (paused still false, stream_status still live/connecting)  
**Pass criteria:** Response status 200; `paused=false` before and after; `stream_status` not changed; no error thrown

---

### TC-13 — Pause unknown ticker returns 404

**Type:** api  
**Preconditions:** Backend running, ticker UNKNOWN_TICKER_XYZ not watched

**Steps:**
1. Send: `curl -X POST http://localhost:8000/watch/UNKNOWN_TICKER_XYZ/pause`

**Expected outcome:** 404 response; no engine created  
**Pass criteria:** HTTP status 404; response body indicates ticker not found

---

### TC-14 — Resume unknown ticker returns 404

**Type:** api  
**Preconditions:** Backend running, ticker UNKNOWN_TICKER_XYZ not watched

**Steps:**
1. Send: `curl -X POST http://localhost:8000/watch/UNKNOWN_TICKER_XYZ/resume`

**Expected outcome:** 404 response; no engine created  
**Pass criteria:** HTTP status 404; response body indicates ticker not found

---

### TC-15 — Pause keeps feeder task alive

**Type:** api  
**Preconditions:** Backend running, ticker watched and streaming

**Steps:**
1. Watch ticker: `curl -X POST http://localhost:8000/watch/AAPL -d '{"provider":"SIM-BUYER"}' -H 'Content-Type: application/json'`
2. Wait 1 second
3. Pause: `curl -X POST http://localhost:8000/watch/AAPL/pause`
4. Fetch state: `curl http://localhost:8000/watch/AAPL/state` (verify 200, engine/snapshot alive)
5. Check WS stream or re-fetch summary; verify no 404

**Expected outcome:** State endpoint returns 200; engine snapshot still present; feeder task running (not cancelled)  
**Pass criteria:** HTTP 200 on `/watch/{ticker}/state` after pause; snapshot contains `paused=true`, `stream_status="paused"`, and prior data intact

---

### TC-16 — Pause sets stream_status to "paused", never "live"

**Type:** api  
**Preconditions:** Backend running, ticker watched and streaming, WS stream available

**Steps:**
1. Watch ticker: `curl -X POST http://localhost:8000/watch/AAPL -d '{"provider":"SIM-BUYER"}' -H 'Content-Type: application/json'`
2. Wait 2 seconds (ensure stream_status = "live")
3. Connect to WS: `wscat -c ws://localhost:8000/stream/AAPL`
4. Record first message (verify `stream_status="live"`, `paused=false`)
5. Pause: `curl -X POST http://localhost:8000/watch/AAPL/pause`
6. Record next WS message (within 2 seconds)

**Expected outcome:** WS message after pause shows `stream_status="paused"`, `paused=true`; never shows `stream_status="live"` with `paused=true`  
**Pass criteria:** JSON snapshot on WS contains exactly `"stream_status": "paused"` and `"paused": true`; no live reading while paused

---

### TC-17 — Resume restores prior stream_status, not fabricated

**Type:** api  
**Preconditions:** Backend running, ticker watched, paused (stream_status before pause was "live")

**Steps:**
1. Watch ticker: `curl -X POST http://localhost:8000/watch/AAPL -d '{"provider":"SIM-BUYER"}' -H 'Content-Type: application/json'`
2. Wait 2 seconds (stream_status="live")
3. Pause: `curl -X POST http://localhost:8000/watch/AAPL/pause`
4. Verify snapshot: `stream_status="paused"`, `paused=true`
5. Resume: `curl -X POST http://localhost:8000/watch/AAPL/resume`
6. Verify snapshot: `stream_status="live"` (restored, not guessed), `paused=false`

**Expected outcome:** Resume restores the pre-pause status (live) without fabricating a new status value  
**Pass criteria:** `stream_status` returns to `"live"` (not `"connecting"` or other); `paused` returns to `false`

---

### TC-18 — Stop after pause fully tears down

**Type:** api  
**Preconditions:** Backend running, ticker watched and paused

**Steps:**
1. Watch ticker: `curl -X POST http://localhost:8000/watch/AAPL -d '{"provider":"SIM-BUYER"}' -H 'Content-Type: application/json'`
2. Pause: `curl -X POST http://localhost:8000/watch/AAPL/pause`
3. Verify paused state (snapshot present): `curl http://localhost:8000/tape/AAPL/summary`
4. Stop: `curl -X DELETE http://localhost:8000/watch/AAPL`
5. Verify stopped: `curl http://localhost:8000/tape/AAPL/summary`

**Expected outcome:** Stop request returns 200 or 204; subsequent summary fetch returns 404 (engine destroyed)  
**Pass criteria:** First summary (paused) returns 200; second summary (after stop) returns 404

---

### TC-19 — Honest pause: no trades applied while paused (deterministic hermetic test)

**Type:** api  
**Preconditions:** Backend running, deterministic SIM-BUYER feeder available

**Steps:**
1. Watch ticker: `curl -X POST http://localhost:8000/watch/AAPL -d '{"provider":"SIM-BUYER"}' -H 'Content-Type: application/json'`
2. Wait 2 seconds; fetch summary: `curl http://localhost:8000/tape/AAPL/summary` → record `recent_trades_count = T1`
3. Pause: `curl -X POST http://localhost:8000/watch/AAPL/pause`
4. Wait 5 seconds (while paused)
5. Fetch summary: `curl http://localhost:8000/tape/AAPL/summary` → record `recent_trades_count = T2`
6. Assert `T2 == T1` (no new trades accrued)

**Expected outcome:** Trade count frozen; no new events applied to snapshot while paused  
**Pass criteria:** `T2 == T1` and snapshot identical before/after wait (no new candles, no new features)

---

### TC-20 — Honest resume: no backfill jump (deterministic hermetic test)

**Type:** api  
**Preconditions:** Backend running, paused watch with known pre-resume trade count

**Steps:**
1. Watch ticker: `curl -X POST http://localhost:8000/watch/AAPL -d '{"provider":"SIM-BUYER"}' -H 'Content-Type: application/json'`
2. Wait 2 seconds; pause
3. Record paused snapshot: `paused_trades = T_paused`
4. Resume: `curl -X POST http://localhost:8000/watch/AAPL/resume`
5. Wait 2 seconds
6. Fetch summary: `curl http://localhost:8000/tape/AAPL/summary` → record `resumed_trades = T_resumed`
7. Assert `(T_resumed - T_paused) ≈ 2 trades` (normal 1 trade/sec cadence, not a jump)

**Expected outcome:** Trade count increases at natural streaming rate (~1-2 per second), no sudden backfill spike  
**Pass criteria:** Increase is linear, not a single large jump from a synthesized backfill

---

### TC-21 — Chart data (/history) unchanged from iter-6 (byte-identical OHLC)

**Type:** api  
**Preconditions:** Backend running, SIM-BUYER watched and populating

**Steps:**
1. Watch SIM-BUYER: `curl -X POST http://localhost:8000/watch/AAPL -d '{"provider":"SIM-BUYER"}' -H 'Content-Type: application/json'`
2. Wait 3 seconds
3. Fetch history at 30s bars: `curl http://localhost:8000/tape/AAPL/history?bar=30` → record response body (prettify as JSON)
4. Assert response contains `bars` array with OHLC fields (open, high, low, close)
5. Compare high/low values to iter-6 golden file if available

**Expected outcome:** `/history` returns same OHLC data as iter-6; no regression to chart-data computation  
**Pass criteria:** Response contains valid OHLC bars; byte-identical to iter-6 (or visually identical prices if no golden file)

---

### TC-22 — Required journeys J-01–J-16 still pass (smoke test)

**Type:** api  
**Preconditions:** Backend running, all prior journey tests available

**Steps:**
1. Run backend unit test suite: `pytest apps/backend/tests/ -v`
2. Verify test count ≥ 159 passed, ≤ 1 skipped
3. Verify no new failures introduced

**Expected outcome:** Test suite passes; no regressions in J-01–J-16 paths (engine, classifier, feature, aggressor, chart-data unchanged)  
**Pass criteria:** All prior tests pass; exit code 0; test count confirms no regression

---

## Summary

**Total test cases:** 22
- **Browser tests:** 7 (TC-01 to TC-07)
- **API tests:** 15 (TC-08 to TC-22)

**Key coverage:**
- J-17 chart render: TC-01, TC-02, TC-03, TC-04, TC-05, TC-06 (marker colors, bar-size toggle, live mode hide)
- J-18 historical surface: TC-07 (render + price matching)
- J-19 pause/resume: TC-08 to TC-20 (freeze, resume without backfill, stop after pause, idempotency, honest state transitions)
- Regression guard: TC-21, TC-22 (chart data byte-identical, prior journeys unaffected)
- Error paths: TC-13, TC-14 (unknown ticker 404s)
- Anti-goal guardrails: TC-16, TC-17, TC-19, TC-20 (honest pause — no fabricated `live`, no backfill, frozen count, restored status)
