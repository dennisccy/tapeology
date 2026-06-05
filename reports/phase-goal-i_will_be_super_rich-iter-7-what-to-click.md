# Phase goal-i_will_be_super_rich-iter-7 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich-iter-7
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running at `http://localhost:8000`
- No login required
- No seed data required — SIM-BUYER provider is built in

---

## Verification Steps

1. Open `http://localhost:3650` in your browser
   - **Expect:** The page loads with a top bar containing a ticker/provider selector and a "Watch" button. No error banner. No "Pause" or "Resume" button is visible yet.

2. Select provider `SIM-BUYER` (if not already selected) and click the "Watch" button
   - **Expect:** Within 3 seconds the stream-status dot in the top-right corner shows a pulsing green dot labeled "live". An amber-bordered "Pause" button appears in the top bar beside the "Stop" button. The cockpit begins populating with price data and recent trades.

3. Click the amber "Pause" button in the top bar
   - **Expect:** The "Pause" button is immediately replaced by an amber "Resume" button. The stream-status dot in the top-right changes from green "live" to a non-pulsing amber dot labeled "paused". The cockpit (Quote, Recent Trades, Feature Counters, Tape State) stays visible — it does NOT clear or go blank.
   - **Broken looks like:** The dot still says "live", or the cockpit clears entirely, or no "Resume" button appears.

4. Wait 5 seconds without clicking anything and observe the Recent Trades count
   - **Expect:** The trade count shown in the Recent Trades panel does NOT increase during the 5 seconds. The chart (if visible) does not add new candles. The "paused" amber dot remains in the top-right throughout.
   - **Broken looks like:** The trade count keeps climbing, indicating pause did not actually freeze the stream.

5. Click the amber "Resume" button
   - **Expect:** The "Resume" button is immediately replaced by the "Pause" button again. The stream-status dot changes from amber "paused" back to green pulsing "live". Within the next 3 seconds the Recent Trades count increases by 1–3 trades (normal cadence) — NOT a sudden jump of 10 or more trades.
   - **Broken looks like:** The count jumps by a large number all at once (backfill fabrication), or the dot stays "paused" after clicking Resume.

6. Click the "Stop" button while the watch is live (not paused)
   - **Expect:** The entire "Watching SIM-BUYER … Pause Stop" cluster disappears from the top bar. The cockpit returns to idle/empty state. The stream-status dot no longer shows "live".

7. Click "Watch" again to start a second SIM-BUYER session
   - **Expect:** A new watch starts cleanly: the "live" dot reappears, the cockpit repopulates with fresh data, and the "Pause" button reappears. No error banner or frozen state from the previous session.

8. Let the new watch run for 3 seconds, then click "Pause", then immediately click "Stop"
   - **Expect:** The Stop succeeds even from a paused state. The watch-control cluster disappears, the cockpit clears, and the stream-status dot shows no active state (no "paused", no "live").
   - **Broken looks like:** The UI is stuck showing "paused" after Stop, or the cockpit data does not clear.

---

## What "Working Correctly" Looks Like

- An amber "Pause" button appears beside "Stop" whenever a watch is active and not yet paused
- Clicking Pause immediately swaps the button to "Resume" and changes the status dot to amber "paused"
- The cockpit panels (Quote, Recent Trades, features, tape state) hold their last values while paused — they do not blank out
- Clicking Resume immediately restores the green "live" dot and resumes the trade count at a natural ~1/second rate (no backfill spike)
- Stop always closes the session and clears the cockpit, whether called from a live or paused state

## Common Issues

- **"Pause" button not appearing**: Check that the stream-status dot shows "live" (green) — if it shows "connecting" (amber) or "stale" the watch may not have fully established; wait a few more seconds or check `curl http://localhost:8000/health`
- **Status dot still shows "paused" after clicking Resume**: Reload the page and retry — this may indicate the backend /resume endpoint is not responding; confirm backend is up with `curl http://localhost:8000/health`
- **Cockpit goes blank when Pause is clicked**: This is a regression. The cockpit should freeze with data intact, not clear. Check browser console for errors and confirm the frontend build is up to date.
- **Blank page / error screen on load**: Confirm the backend is running (`curl http://localhost:8000/health`) and the frontend dev server is running at port 3650.
