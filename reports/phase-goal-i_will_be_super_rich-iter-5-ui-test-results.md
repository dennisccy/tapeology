# Goal Mode Iteration 5 — UI Test Results (Re-baseline: J-01–J-20)

**Phase:** goal-i_will_be_super_rich-iter-5
**Date:** 2026-06-05
**Written by:** browser-qa-agent
**Mode:** verify-only re-baseline (no code changes)

---

**Browser QA Verdict:** FAIL

<!-- FAIL: J-16–J-20 are unbuilt (to-build FAILs expected in this re-baseline); J-01–J-15 floor re-confirmed. -->

**Overall:** 14/20 journeys passed (1 skipped, 5 failed as expected to-build)

Backend suite: **128 passed, 1 skipped** — matches iter-4 baseline, no regressions.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Watch a ticker and see the live tape cockpit | happy-path | P1 | All panels render with live values, WebSocket updates | SIM-BUYER: all panels populated (bid/ask/spread/last, recent trades, 14 features, Buyer Control 0.870, observations, event log). Status: Live. | PASS | UT-J-01-initial.png, UT-J-01-result.png |
| UT-J-02 | Buyer-control scenario is identified | happy-path | P1 | tape_state=buyer_control, confidence ≥ threshold, aggressive_buy_ratio high, buy_price_impact positive | SIM-BUYER: Buyer Control confidence 0.870, aggressive_buy_ratio 0.925, buy_price_impact 0.420, event log "Tape state changed to buyer_control" | PASS | UT-J-01-result.png |
| UT-J-03 | Seller-control scenario is identified | happy-path | P1 | tape_state=seller_control, confidence ≥ threshold, aggressive_sell_ratio high, sell_price_impact negative | SIM-SELLER: Seller Control confidence 0.868, aggressive_sell_ratio 0.923, sell_price_impact -0.450, event log "Tape state changed to seller_control" | PASS | UT-J-03-result.png |
| UT-J-04 | Bid absorption detected (price impact, not aggression) | happy-path | P1 | tape_state=bid_absorption despite high sell aggression; price not lower; absorption_score elevated | SIM-BIDABS: Bid Absorption confidence 0.917, aggressive_sell_ratio 1.000, sell_price_impact 0.000, absorption_score 1.000, event log "Large sell print absorbed", "Bid refreshing at 100.00" | PASS | UT-J-04-result.png |
| UT-J-05 | Ask absorption detected (price impact, not aggression) | happy-path | P1 | tape_state=ask_absorption despite high buy aggression; price not higher; absorption_score elevated | SIM-ASKABS: Ask Absorption confidence 0.917, aggressive_buy_ratio 1.000, buy_price_impact 0.000, absorption_score 1.000, event log "Large buy print absorbed", "Ask refreshing at 100.02" | PASS | UT-J-05-result.png |
| UT-J-06 | Unclear / choppy tape reported as unclear | happy-path | P1 | tape_state=unclear, low confidence, no directional call | SIM-CHOP: Unclear confidence 0.200, buy/sell ratios 0.500 each, price_impact 0.000, observation "Mixed or weak evidence — no clear side in control" | PASS | UT-J-06-result.png |
| UT-J-07 | Tape-state transitions announced in event log and observations | happy-path | P1 | Event log records "Tape state changed to …"; observations reflect current evidence | SIM-BUYER: event log "Tape state changed to buyer_control"; observations "Buyer aggression increasing", "Price lifting on buy prints", "Spread stable and narrow" | PASS | UT-J-07-result.png |
| UT-J-08 | REST and live UI agree (single source of truth) | happy-path | P1 | REST /state and /features match UI values exactly | Historical F active: scenario label matches REST params; bid/ask/spread/last and features consistent; honest "Warming up" state (no fabrication) | PASS | UT-J-08-result.png |
| UT-J-09 | Stop watching a ticker | happy-path | P1 | After Stop, cockpit returns to idle, stream closes | After Stop: "No ticker watched" idle screen, status Idle, no active watch in header | PASS | UT-J-09-result.png |
| UT-J-10 | Choose a data source (Live / Historical / Simulated) | happy-path | P1 | 3 modes with correct mode-specific controls; SIM-BUYER still buyer_control | Live: market-closed indicator + symbol input. Historical: date/time picker + speed selector. Simulated + SIM-BUYER: buyer_control confirmed. No regression. | PASS | UT-J-10-live.png, UT-J-10-historical.png, UT-J-10-simulated-buyer.png |
| UT-J-11 | Replay a real historical session | happy-path | P1 | Backend fetches real trades/quotes; cockpit populates; REST and UI agree | Historical F (2026-06-02 13:30–13:32, 1×): cockpit active, real prices (bid 15.72 / ask 16.67), trades list with UNKNOWN/BUY/SELL sides, features populated, honest warm-up | PASS | UT-J-11-result.png |
| UT-J-12 | Stream a real live ticker (UI controls) | happy-path | P1 | Live controls present; market-status indicator renders; real-socket gated | Live mode: symbol input present, "market closed — next open Jun 5, 02:30 PM GMT+1" with zone label. Real-socket gated (outside market hours). | PASS | UT-J-12-live-controls.png |
| UT-J-13 | Find a symbol by search | happy-path | P1 | Search returns matching tradable symbols; selecting fills ticker | Live mode, typed "F": dropdown shows F (Ford Motor Company), F.PRB, F.PRC, F.PRD, FA, FAAA, FAAR, FAB with company names. | PASS | UT-J-13-dropdown.png, UT-J-13-search-results.png, UT-J-13-result.png |
| UT-J-14 | Real-data edge cases handled honestly (no fabricated data) | happy-path | P1 | Unknown symbol / empty window / market closed each show explicit distinct error, no tape | ZZZNOTREAL: "not a tradable symbol". F 01/01/2020: "no data for that window". F Live closed: "market is closed" with next open time. No tape fabricated in any case. | PASS | UT-J-14-unknown-symbol.png, UT-J-14-no-data.png, UT-J-14-market-closed.png |
| UT-J-15 | Live-feed gap shows `stale`, then recovers | gated | P2 | Status flips stale during lull; recovers to live; no fabricated trades | No screenshot — requires live market hours + vendor credentials (neither present). Operator/gated check per iter spec. | SKIP | none |
| UT-J-16 | Historical recent-trades show resolved side (not `unknown`) | to-build | P1 | Majority BUY/SELL via quote-rule + tick-test; low UNKNOWN fraction | Historical F (13:30–14:30, 10×): recent-trades predominantly UNKNOWN — quote-rule-only classifier, no tick-test fallback. High UNKNOWN fraction. Gap J-16 exists to close. | FAIL | UT-J-16-result.png |
| UT-J-17 | Price chart with tape-state markers on simulated data | to-build | P1 | Candlestick chart above cockpit with bar-size selector and tape-state markers | SIM-BUYER at buyer_control: no chart, no bar-size selector anywhere. Chart component entirely absent (no charting library, no /history endpoint). | FAIL | UT-J-17-not-implemented.png |
| UT-J-18 | Inspect tape-state prediction on real historical chart | to-build | P1 | Candlestick chart reflects real prices; bars match /history; markers at transitions | No chart component or GET /tape/{ticker}/history endpoint exists. Not runnable (chart absent per J-17 evidence). | FAIL | UT-J-17-not-implemented.png |
| UT-J-19 | Pause and resume a watch without losing state | to-build | P1 | Pause button beside Stop; freezes state with PAUSED indicator; Resume continues; Stop still tears down | SIM-BUYER: only Watch + Stop controls visible — no Pause button, no Resume, no PAUSED indicator. Pause/resume mechanism entirely unbuilt. | FAIL | UT-J-19-not-implemented.png |
| UT-J-20 | Pick a historical window in local time with US-session quick-picks | to-build | P1 | Explicit timezone label on picker; "Open 9:30 ET / Close 16:00 ET / Full RTH" quick-picks with local equivalents | Historical picker: native date + time inputs only, no timezone label, no quick-pick buttons. Naive-UTC gap (iter-2 lesson) unresolved. | FAIL | UT-J-20-historical-picker.png |

---

## Passed Tests

### UT-J-01 — Watch a ticker and see the live tape cockpit
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-01-initial.png`, `UT-J-01-result.png`
- Initial: idle cockpit, "No ticker watched" placeholder, Simulated mode active.
- After Watch SIM-BUYER: all 6 panels rendered — Quote (bid 100.46, ask 100.48, spread 0.02, last 100.47), Recent Trades (14 rows, PRICE/SIZE/SIDE), Features (14 metrics, 5 time windows), Tape State (Buyer Control, confidence 0.870), Observations (3 messages), Event Log ("Tape state changed to buyer_control"). Status dot: Live.

---

### UT-J-02 — Buyer-control scenario is identified
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-01-result.png`
- SIM-BUYER stabilized to Buyer Control, confidence 0.870 (above threshold).
- aggressive_buy_ratio 0.925 (high), buy_price_impact 0.420 (positive), sell_price_impact -0.140.
- Event log: "Tape state changed to buyer_control". All acceptance criteria met.

---

### UT-J-03 — Seller-control scenario is identified
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-03-result.png`
- SIM-SELLER: Seller Control, confidence 0.868. aggressive_sell_ratio 0.923, sell_price_impact -0.450 (negative).
- Observations: "Seller aggression increasing", "Price falling on sell prints", "Spread stable and narrow".
- Event log: "Tape state changed to seller_control".

---

### UT-J-04 — Bid absorption detected (price impact, not aggression)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-04-result.png`
- SIM-BIDABS: Bid Absorption (not seller_control), confidence 0.917.
- aggressive_sell_ratio 1.000 (high), sell_price_impact 0.000 (price not moving lower — key absorption test passed).
- absorption_score 1.000, bid_refresh_score 1.000. Event log: "Bid refreshing at 100.00", "Large sell print absorbed", "Tape state changed to bid_absorption".

---

### UT-J-05 — Ask absorption detected (price impact, not aggression)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-05-result.png`
- SIM-ASKABS: Ask Absorption (not buyer_control), confidence 0.917.
- aggressive_buy_ratio 1.000 (high), buy_price_impact 0.000 (price not moving higher — key absorption test passed).
- absorption_score 1.000, ask_refresh_score 1.000. Event log: "Ask refreshing at 100.02", "Large buy print absorbed", "Tape state changed to ask_absorption".

---

### UT-J-06 — Unclear / choppy tape reported as unclear
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-06-result.png`
- SIM-CHOP: Unclear, confidence 0.200 (low). aggressive_buy_ratio 0.500 = aggressive_sell_ratio 0.500 (balanced). buy_price_impact 0.000, sell_price_impact 0.000. Spread 0.20 (wide).
- Observation: "Mixed or weak evidence — no clear side in control". No directional call forced.

---

### UT-J-07 — Tape-state transitions announced in event log and observations
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-07-result.png`
- SIM-BUYER cold start: event log "Tape state changed to buyer_control".
- Observations: "Buyer aggression increasing", "Price lifting on buy prints", "Spread stable and narrow".
- Messages appended live over WebSocket.

---

### UT-J-08 — REST and live UI agree (single source of truth)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-08-result.png`
- Historical F (2026-06-02T16:00–16:02): scenario label in header matches watch parameters exactly ("scenario: historical F 2026-06-02T16:00–2026-06-02T16:02").
- UI bid 16.49, ask 16.50, spread 0.01, last 16.50; all features consistent with engine state. Honest "Warming up — collecting tape data" shown (no fabrication). Single source confirmed.

---

### UT-J-09 — Stop watching a ticker
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-09-result.png`
- After Stop: header shows no active watch label, no Stop button; cockpit shows "No ticker watched"; status Idle. Stream closed cleanly; re-watching would start a fresh read.

---

### UT-J-10 — Choose a data source (Live / Historical / Simulated)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-10-live.png`, `UT-J-10-historical.png`, `UT-J-10-simulated-buyer.png`
- Live: market-closed status indicator + symbol input field visible; no date picker.
- Historical: date picker + start/end time inputs + replay-speed selector present; no sim ticker hint.
- Simulated + SIM-BUYER: buyer_control confirmed (no regression from J-01/J-02).

---

### UT-J-11 — Replay a real historical session
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-11-result.png`
- Historical F (2026-06-02 13:30–13:32, 1×): cockpit active (status Live), quote panel real prices (bid 15.72, ask 16.67, spread 0.95, last 16.70). Recent trades with 9 rows of real prices and classified sides (UNKNOWN/BUY/SELL). Features panel populated. Honest "Warming up — collecting tape data" observation. Real vendor data flows through the same engine.

---

### UT-J-12 — Stream a real live ticker (UI controls)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-12-live-controls.png`
- Live mode: symbol input field present; market-status indicator shows "market closed — next open Jun 5, 02:30 PM GMT+1" (explicit zone label GMT+1). Controls render correctly without a live feed. Real-socket behavior is operator/gated (outside market hours, no credentials).

---

### UT-J-13 — Find a symbol by search
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-13-dropdown.png`, `UT-J-13-search-results.png`, `UT-J-13-result.png`
- Live mode, partial input "F": dropdown returned 8 matching tradable symbols — F (Ford Motor Company), F.PRB (Ford Motor Company 6.20% Notes), F.PRC, F.PRD, FA (First Advantage Corporation), FAAA (Fidelity Merrimack Street Trust), FAAR (First Trust Exchange-Traded Fund), FAB (First Trust Multi Cap Value AlphaDE…). Symbol + full company name shown. Selecting fills the ticker field.

---

### UT-J-14 — Real-data edge cases handled honestly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-14-unknown-symbol.png`, `UT-J-14-no-data.png`, `UT-J-14-market-closed.png`
- Unknown symbol (ZZZNOTREAL, Historical): "SYMBOL NOT TRADABLE — not a tradable symbol" error card. Message: "Tapeology never fabricates data to fill the gap." No tape shown.
- Empty window (F, 01/01/2020): "NO DATA FOR THAT WINDOW — no data for that window" error card. No tape shown.
- Market closed (F, Live): "MARKET IS CLOSED — market is closed" card with next open "Jun 5, 02:30 PM GMT+1". No tape shown. Three distinct honest error states, no fabrication in any case.

---

## Skipped Tests

### UT-J-15 — A live-feed gap shows `stale`, then recovers
**Verdict:** SKIPPED
**Reason:** Operator/gated credentialed check requiring live market hours and configured vendor API credentials. Neither was present during this baseline run (market closed, no credentials in QA harness). Per iter spec this is expected behavior for a gated check. No screenshot was captured.

---

## Failed Tests (to-build — expected outcome of this re-baseline pass)

### UT-J-16 — Historical recent-trades show resolved side (not `unknown`)
**Verdict:** FAIL (to-build)
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-16-result.png`

**Steps taken:**
1. Selected Historical mode, entered F (Ford), window 2026-06-02 13:30–14:30 at 10×, clicked Watch.
2. Let replay run and read the SIDE column in the recent-trades list.

**Expected:** Majority of trades show BUY or SELL; only genuinely undecidable prints remain UNKNOWN; low UNKNOWN fraction overall.
**Actual:** Recent-trades shows predominantly UNKNOWN entries with occasional BUY rows. The quote-rule-only classifier leaves mid-spread and pre-quote prints unresolved. The tick-test fallback (Lee-Ready) is not yet implemented in `apps/backend/app/engine/aggressor.py`. High UNKNOWN fraction confirms the gap J-16 was created to close.

---

### UT-J-17 — Price chart with tape-state markers on simulated data
**Verdict:** FAIL (to-build)
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-17-not-implemented.png`

**Steps taken:**
1. Watched SIM-BUYER in Simulated mode; let cockpit reach buyer_control.
2. Inspected the page for a candlestick chart above the cockpit and a bar-size selector.

**Expected:** Candlestick chart renders above cockpit; 10/30/60s bar-size selector present; tape-state markers appear at transitions.
**Actual:** No chart component present. No bar-size selector visible. Only the existing cockpit panels render. No charting library in the frontend (`apps/frontend/package.json`) and no GET /tape/{ticker}/history endpoint in the backend.

---

### UT-J-18 — Inspect tape-state prediction on real historical chart
**Verdict:** FAIL (to-build)
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-17-not-implemented.png` (chart absence confirmed by J-17 evidence)

**Steps taken:**
1. Prerequisite chart component absent per J-17 evidence.

**Expected:** Candlestick chart reflects real replayed prices; bars match GET /tape/{ticker}/history; markers align with tape-state transitions.
**Actual:** No chart component exists in the frontend. No GET /tape/{ticker}/history endpoint in the backend. Not runnable. The unbuilt state of J-17 (simulated chart) confirms J-18 (real-data chart) is also absent.

---

### UT-J-19 — Pause and resume a watch without losing state
**Verdict:** FAIL (to-build)
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-19-not-implemented.png`

**Steps taken:**
1. Watched SIM-BUYER in Simulated mode; let cockpit reach buyer_control.
2. Inspected watch controls for a Pause button beside Stop.

**Expected:** Pause button beside Stop; on Pause: state freezes with PAUSED indicator (no teardown); Resume continues; Stop still tears down.
**Actual:** Header shows only Watch and Stop controls — no Pause button, no Resume button, no PAUSED indicator. The `paused` stream_status enum value is absent from the snapshot. POST /watch/{ticker}/pause and /resume endpoints do not exist. Entire pause/resume mechanism unbuilt.

---

### UT-J-20 — Pick a historical window in local time with US-session quick-picks
**Verdict:** FAIL (to-build)
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/UT-J-20-historical-picker.png`

**Steps taken:**
1. Selected Historical mode.
2. Inspected the date/time picker for an explicit timezone label and US-session quick-picks.

**Expected:** Picker shows explicit local-timezone label; "Open 9:30 ET", "Close 16:00 ET", "Full RTH" quick-picks each annotated with local equivalents.
**Actual:** Historical picker shows a native browser `<input type="date">` and two `<input type="time">` fields (start/end) with no timezone label, no zone annotation, and no quick-pick buttons. The iter-2 naive-UTC gap (datetimes sent as naive values, treated as UTC by the backend) is unresolved.

---

## Environment

- **Frontend URL:** http://localhost:3650 (Next.js dev server)
- **Backend URL:** http://localhost:3651 (FastAPI/uvicorn)
- **Browser:** Chrome via MCP (prior run — screenshots captured before this report was written)
- **Test Date:** 2026-06-05
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich-iter-5-evidence/`
- **Backend suite:** 128 passed, 1 skipped (matches iter-4 baseline exactly; no regressions introduced)
- **Re-baseline note:** This is a verify-only pass with no code changes. J-16–J-20 FAILs are the expected authoritative to-build state for the evaluator to register in journey-history.json. J-01–J-15 are re-confirmed green.
