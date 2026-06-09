# Phase goal-i_will_be_super_rich-iter-13 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich-iter-13
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running (check: open `http://localhost:3650` — page should load without error)
- No login required
- For steps 4 and 5 (real-data checks): Alpaca API credentials must be configured in the backend environment (`APCA_API_KEY_ID` and `APCA_API_SECRET_KEY`). If credentials are not available, skip steps 4 and 5 — those capabilities are covered by backend tests.

---

## Verification Steps

1. Open `http://localhost:3650` in your browser
   - **Expect:** The cockpit page loads. The TopBar is visible at the top. The Historical mode controls are visible, including a replay-speed dropdown showing "1x". No red error banner appears.
   - **Broken looks like:** Blank white page, "Application error" overlay, or a red error banner on initial load.

2. Start a historical SIM-BUYER replay at 1x speed
   - Navigate to `http://localhost:3650`
   - In the symbol input in the TopBar, type `SIM-BUYER`
   - In the Historical mode controls, click the "1H" quick-pick button
   - Click the "Watch" button
   - Wait 3 seconds for the chart to start rendering
   - **Expect:** The chart area populates with candle data. The tape-state panel (row 1) begins showing a state label. No error banner appears.
   - **Broken looks like:** The chart stays blank after 5 seconds, or a red error banner appears.

3. Change the replay speed to 10x while the replay is running
   - With the SIM-BUYER replay still active and streaming (from step 2), locate the replay-speed dropdown in the TopBar
   - Select "10x" from the dropdown
   - Watch the chart and cockpit for the next 2–3 seconds
   - **Expect:** The dropdown shows "10x" as the selected value. The cadence of new candles and trade prints visibly accelerates — events arrive noticeably faster. The chart does NOT reload, blank out, or lose its current position. No error banner appears.
   - **Broken looks like:** The chart reloads/resets to the beginning, a loading spinner appears, the speed dropdown reverts to "1x", or a red error banner appears.

4. Verify the Full RTH quick-pick loads without "very high-volume" error (credential-gated)
   - Stop the current watch (click "Stop" if available, or navigate to `http://localhost:3650` fresh)
   - In the symbol input, type `SPY`
   - In the Historical mode controls, click the "Full RTH 9:30–16:00" quick-pick button
   - Click the "Watch" button
   - Wait up to 30 seconds for the data to load
   - **Expect:** The chart begins populating with SPY tape data. The tape-state panel shows a valid state label. No red error banner containing "very high-volume" or "try a shorter range" appears.
   - **Broken looks like:** A red error banner appears with the text "very high-volume" or "shorter range" before the chart loads.
   - **Skip if:** Alpaca credentials are not configured.

5. Verify SIM-BUYER and SIM-SELLER simulator baselines are unchanged (regression check)
   - Navigate to `http://localhost:3650`
   - In the symbol input, type `SIM-BUYER`, ensure Live/Simulator mode is selected (not Historical), and click "Watch"
   - Wait 6 seconds for the tape to warm up
   - **Expect:** The tape-state panel (row 1) shows `buyer control` with a green label and the confidence bar filled to at least 80%
   - Stop the watch, type `SIM-SELLER` in the symbol input, click "Watch"
   - Wait 6 seconds
   - **Expect:** The tape-state panel shows `seller control` with a red label and confidence bar at least 80% filled
   - **Broken looks like:** Either symbol shows `unclear` (amber) after the warm-up period, or the confidence bar is near empty.

---

## What "Working Correctly" Looks Like

- The replay-speed dropdown shows "10x" and the candle/trade cadence in the chart visibly accelerates within 1 second of selecting it — the chart continues smoothly, no reload
- The Full RTH quick-pick for SPY starts a replay and the chart fills with tape data — no "shorter range" banner
- SIM-BUYER shows a green `buyer control` label; SIM-SELLER shows a red `seller control` label — the J-33 classifier re-tuning has not broken the simulator baselines

## Common Issues

- **Page loads but chart stays blank after 5 seconds:** Check that the backend is running. Open a terminal and run `curl http://localhost:8000/health` (or equivalent). If the backend is down, restart it before testing.
- **Speed dropdown reverts to "1x" immediately after selecting "10x":** The frontend may have failed to call `POST /watch/{ticker}/speed`. Open browser DevTools (F12) → Network tab — look for a request to `/watch/SIM-BUYER/speed`. If it is absent, the wiring from the dropdown to the new API call is broken.
- **Full RTH still shows "very high-volume" error:** The chunked fetch backend change (J-34) may not have deployed. Confirm the backend was restarted after the latest code changes.
- **SIM-BUYER shows "unclear" after 6 seconds:** The J-33 classifier re-tuning may have regressed the simulator gates. Run the backend unit tests (`pytest apps/backend/tests/ -k "scenario or classifier"`) to isolate.
