# Phase goal-i_will_be_super_rich-iter-8 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich-iter-8
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running (default port)
- No login credentials required — all steps use Simulated mode or fixture-based Historical mode
- Know your local IANA timezone (e.g., `Asia/Hong_Kong`). Find it in 5 seconds by opening the browser console (F12 → Console tab) and typing: `Intl.DateTimeFormat().resolvedOptions().timeZone`

---

## Verification Steps

1. Open `http://localhost:3650` in your browser
   - **Expect:** The page loads showing the top bar with a mode selector (options such as "Live", "Simulated", "Historical"). A chart area and cockpit area are visible below. No error page, no blank white screen, no "500" or "Something went wrong" message.

2. Click the "Historical" option in the mode selector in the top bar
   - **Expect:** A row of Historical controls expands (or becomes visible) showing: a date input, a start time input, an end time input, a replay speed input, and a small muted monospaced label showing your local timezone name (e.g., `Asia/Hong_Kong` or `America/New_York`). Three quick-pick buttons are also visible: "Open 9:30 ET", "Close 16:00 ET", "Full RTH 9:30–16:00 ET" — all three are faded (approximately 40% opacity). Hovering any button shows a `not-allowed` cursor.
   - **Broken if:** No timezone label appears, the three quick-pick buttons are missing entirely, or the buttons are already active/full-opacity with no date entered.

3. Type `2026-06-02` into the date input field and press Tab or click away to commit the value
   - **Expect:** All three quick-pick buttons immediately become visually active (full opacity, standard pointer cursor on hover). Each button now shows a local-time annotation in parentheses alongside the ET time — for example "Open 9:30 ET (09:30 PM local)" if you are in Hong Kong, or "Open 9:30 ET (09:30 AM local)" if you are in New York. The annotation must show a time, not be blank.
   - **Broken if:** Buttons stay faded after the date is entered, or annotations show "(undefined local)" or "(NaN local)".

4. Click the "Full RTH 9:30–16:00 ET" button
   - **Expect:** Both the start time and end time input fields are populated immediately. The start time shows the local equivalent of 9:30 ET on 2026-06-02, and the end time shows the local equivalent of 16:00 ET on that date. Both values are valid times (not empty, not "00:00"/"00:00", not the same value). The start time is earlier than the end time.
   - **Broken if:** Either input remains empty after clicking, both show the same time, or the end time is earlier than the start time.

5. Open browser DevTools by pressing F12 and click the "Network" tab. Then type `F` in the ticker input field and click the "Watch" button.
   - **Expect:** In the DevTools Network tab, a new request appears for `POST /watch/F` (or a path containing `/watch/`). Click on that request, find its "Request Payload" or "Body" section, and verify the `start` and `end` fields are strings ending in `Z` or a timezone offset like `-04:00` (e.g., `"2026-06-02T13:30:00.000Z"`). They must NOT look like `"2026-06-02T09:30"` (no timezone suffix = broken).
   - **Broken if:** `start` or `end` are naive strings with no `Z` or offset suffix. That is the pre-fix bug.

6. Close DevTools (F12). Observe the cockpit and chart after watching `F` in Historical mode with the RTH window.
   - **Expect:** The chart above the cockpit renders populated candlestick bars with real Ford prices from the fixture. The chart is NOT the idle "No ticker watched" placeholder. The cockpit panels show real bid/ask values, recent trades with prices, a tape state label, and a confidence score.
   - **Broken if:** The chart remains on the idle placeholder, or shows a "no data for window" message (this would indicate the time resolution is still sending UTC-shifted times that miss the fixture window).

7. Locate the bar-size selector (labeled "10s", "30s", "60s") near the chart. Click "30s", then click "60s".
   - **Expect:** Each click re-renders the chart. At 30s there are noticeably fewer bars than at 10s. At 60s there are fewer still. The price range and direction of the trend are consistent across all three views. No crash or indefinitely-spinning loader.

8. Click the "Simulated" option in the mode selector. Type `SIM-BUYER` in the ticker field and click "Watch".
   - **Expect:** The cockpit populates with simulated data within 5–10 seconds. A candlestick chart renders with upward-trending bars. This confirms that switching from Historical back to Simulated still works (regression check).
   - **Broken if:** The chart stays idle, the cockpit shows no data, or a JavaScript error appears after switching modes.

9. With `SIM-BUYER` running and the cockpit updating, click the "Pause" button in the top bar.
   - **Expect:** All cockpit values (bid/ask, tape state, confidence, trades) stop changing. A visible "PAUSED" indicator or changed button state appears. Then click "Resume" — values begin updating again within 3 seconds with no data reset.
   - **Broken if:** Values keep changing after Pause, or the "PAUSED" indicator never appears.

---

## What "Working Correctly" Looks Like

- The timezone label in Historical mode shows your exact IANA timezone name (e.g., `Asia/Hong_Kong`), not "UTC" or a raw offset
- All three quick-pick buttons are faded when no date is entered; they become active and show local-time annotations immediately after a date is typed
- Clicking a quick-pick fills both time inputs with a valid start < end window
- The `POST /watch/` body's `start` and `end` fields end in `Z` or an offset like `-04:00` — no naked datetime strings
- The Ford fixture chart renders actual candlestick bars (not the idle placeholder) in under 10 seconds

## Common Issues

- **Quick-pick buttons still faded after entering a date**: The date field value may not have been committed — try pressing Tab after typing the date instead of just clicking away
- **Timezone label shows "UTC" instead of the local timezone**: The browser's system timezone may be set to UTC; the label is correct — your system, not the app, is set to UTC
- **POST body still shows naive datetime strings**: The frontend build may be stale. Confirm you are hitting the current build at port 3650 and not a cached older version
- **Ford fixture chart shows "no data for window"**: The local time entered (or the quick-pick resolved time) may not overlap the fixture window (15:00–15:02 UTC). Use the local-timezone equivalent of 15:00 UTC for the start time. For Asia/Hong_Kong (UTC+8) that is `23:00`; for America/New_York EDT (UTC-04) that is `11:00`
