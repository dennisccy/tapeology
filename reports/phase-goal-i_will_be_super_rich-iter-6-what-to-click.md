# Phase goal-i_will_be_super_rich-iter-6 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich-iter-6
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running at `http://localhost:8000` (confirm with `curl http://localhost:8000/health` — should return 200)
- No login credentials required — the app is unauthenticated
- No seed data required — SIM-* tickers are built into the simulator

---

## Verification Steps

1. Open `http://localhost:3650` in your browser
   - **Expect:** The page loads with a TopBar at the top, a ticker input field, and a mode selector showing "Simulated". No error banner or blank screen.

2. Confirm no chart panel is visible yet (before any watch starts)
   - **Expect:** The page shows only the TopBar area and either an empty cockpit or a "not watching" state. There is NO "Price Chart" panel visible. This confirms the chart only appears when a ticker is being watched.

3. Type `SIM-BUYER` into the ticker input field and click the "Watch" button
   - **Expect:** Within 1–2 seconds, a panel titled "Price Chart — Tape-State Markers" appears above the cockpit grid. Inside the chart area you should briefly see the text "Loading price history…" before candles appear. A bar-size selector showing three buttons ("10s", "30s", "60s") is visible at the top of the chart area.
   - **Broken looks like:** No chart panel appears at all, or the page shows a JavaScript error banner, or a bright white chart widget appears (should be dark slate-950 background).

4. Wait 15–20 seconds and observe the chart canvas
   - **Expect:** At least 3 candlestick bars have appeared on the dark canvas. At some point during the replay, an emerald (bright green) arrow marker appears on the chart — this marks the moment the engine transitions to `buyer_control`. The cockpit's "Tape State" panel simultaneously shows `buyer_control`.
   - **Broken looks like:** No candles appear after 20 seconds, or the markers are missing, or the "Loading price history…" text never clears.

5. Click the "30s" button in the bar-size selector
   - **Expect:** The chart redraws within 1 second showing fewer but wider candle bars (each bar covers 30 seconds of data). The "30s" button gains a darker filled appearance (active style) and the "10s" button becomes unselected. No error or blank canvas.

6. Click the "60s" button in the bar-size selector
   - **Expect:** The chart redraws again showing even fewer candle bars. The "60s" button is now the active/filled one. Click "10s" to confirm returning to fine-grained granularity works.

7. Click the "Live" button (or data-source selector) in the TopBar to switch to Live mode
   - **Expect:** The "Price Chart — Tape-State Markers" panel disappears immediately. Only the TopBar and cockpit panels remain. No empty gap or ghost box where the chart was.
   - **Broken looks like:** The chart panel stays visible after switching to Live mode.

8. Click the "Simulated" button in the TopBar to switch back to Simulated mode, then watch `SIM-BUYER` again
   - **Expect:** The "Price Chart — Tape-State Markers" panel reappears above the cockpit. The chart begins loading (shows "Loading price history…" briefly, then candles). This confirms the chart visibility toggle is bidirectional.

9. Observe the cockpit panels while the chart is running
   - **Expect:** The "Quote" panel bid/ask/last values are updating. The "Recent Trades" panel is adding new rows. The "Tape State" panel shows an updating state label. These confirm the cockpit was not broken by the new chart being inserted above it.

10. Stop the watch (click "Stop" or navigate away and back), then type `SIM-SELLER` and click "Watch"
    - **Expect:** A rose (red/pink) arrow marker appears on the chart during the `seller_control` transition. The marker color is clearly different from the emerald marker seen in the SIM-BUYER watch.

---

## What "Working Correctly" Looks Like

- The "Price Chart — Tape-State Markers" panel has a dark slate-950 background — it blends visually with the cockpit panels below, not a bright or colorful widget
- Colored markers on the chart match: emerald (green) for buyer control, rose (red) for seller control, amber (orange-yellow) for absorption states
- The bar-size buttons show exactly one button with a dark/filled "active" style at all times
- The chart appears above the cockpit and does not push any cockpit panel off-screen or require vertical scrolling

## Common Issues

- **Chart panel does not appear after clicking Watch:** Check that the backend is running (`curl http://localhost:8000/health`) and that mode is "Simulated" (not "Live"). The chart is intentionally hidden in Live mode.
- **"Loading price history…" never clears:** The backend history endpoint may not be reachable. Check the browser console (F12) for a network error on `/tape/SIM-BUYER/history?bar=10`.
- **No markers appear after 20 seconds:** The SIM-BUYER simulation takes a few seconds to reach a meaningful tape state. Wait up to 30 seconds. If still no marker, check that the cockpit "Tape State" panel is showing `buyer_control` — if it is but the chart shows no marker, that is the bug to report.
- **Chart appears in Live mode:** This is a regression — the chart should be hidden when `mode === "live"`. Report with a screenshot.
- **Blank white chart box:** The charting library may have failed to initialize client-side. Check the browser console for `lightweight-charts` import errors.
