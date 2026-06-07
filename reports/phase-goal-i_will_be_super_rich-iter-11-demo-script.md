# Demo Script — goal-i_will_be_super_rich-iter-11

**Mode:** record
**Date:** 2026-06-07
**Frontend URL:** http://localhost:3650
**Iteration:** 11

## Highlights

### Step 01 — Cockpit loads with all three modes ready

- **Narration:** The Tapeology cockpit opens instantly, showing three data-source modes — Simulated, Historical, and Live — alongside the symbol search field. Everything is in place before a single keystroke.
- **Action:** Navigate to /
- **Point out:** Mode buttons (Live, Historical, Simulated) and the symbol search input are all visible with no error banner.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-11/step-01.png

### Step 02 — Symbol search responds immediately  [NEW]

- **Narration:** Typing 'AAPL' into the symbol search box returns a dropdown of matching tickers within about a second — even right after the backend starts, because the symbol list is pre-loaded in the background at startup.
- **Action:** Type "AAPL" into "Symbol"
- **Point out:** A dropdown of AAPL-prefixed suggestions appears promptly, with no multi-second stall.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-11/step-02.png

### Step 05 — Oversized window triggers an actionable error  [NEW]

- **Narration:** Requesting a full trading-day window for a liquid stock would swamp the system, so the app catches that cleanly and tells you exactly what to do: try a shorter range.
- **Action:** Click the "Watch" button
- **Point out:** The failure panel reads 'that window is very high-volume — try a shorter range' — a specific instruction, not a generic error.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-11/step-05.png

### Step 06 — Amber dot signals data is loading

- **Narration:** As soon as you kick off a Historical watch for a short two-minute window, an amber pulsing dot appears immediately so you always know a fetch is in progress — the cockpit is never a mute blank screen.
- **Action:** Click the "Watch" button
- **Point out:** The pulsing amber dot and a 'connecting' or 'waiting' status label appear within the first second of clicking Watch.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-11/step-06.png

### Step 07 — Historical cockpit populates with real tape data

- **Narration:** Within a few seconds the tape-state panel fills in with a real classification, a confidence reading, and the full feature set — trade speed, aggressive buy and sell ratios, net volume, and a list of recent trades with prices and sides.
- **Action:** Click the "Watch" button
- **Point out:** Tape state (e.g. 'Unclear'), confidence value, and feature panel rows all show real non-zero numbers. Recent trades are listed with prices and sides.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-11/step-07.png

### Step 08 — Re-watching the same window is near-instant  [NEW]

- **Narration:** Stop the watch, then request the exact same TSLA window again. Because the app cached the vendor data from the first fetch, it replays the result in under two seconds — no round-trip to the vendor.
- **Action:** Click the "Stop" button
- **Point out:** The cockpit re-populates almost immediately on the second Watch click, visibly faster than the first load.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-11/step-08.png

### Step 09 — Cache hit: cockpit returns in milliseconds  [NEW]

- **Narration:** The second Watch on the identical window hits the in-process cache and the cockpit is live again in well under two seconds — the same tape-state and confidence values from the first load come back immediately.
- **Action:** Click the "Watch" button
- **Point out:** Confidence and tape-state reappear within one to two seconds, with no loading spinner lingering.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-11/step-09.png

### Step 12 — SIM-BUYER resolves to Buyer Control

- **Narration:** The cockpit reads the simulated buyer-control scenario and classifies the tape: Buyer Control, confidence 0.87, with a strong aggressive-buy ratio and positive net volume. The observations panel narrates what is happening in plain language.
- **Action:** Click the "Watch" button
- **Point out:** Tape state shows 'Buyer Control', confidence is above 0.80, aggressive buy ratio is near 0.93, and the observations panel lists entries like 'Buyer aggression increasing'.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-11/step-12.png

## Full tour (text only)

### Step 03 — Select AAPL from the search results

- **Narration:** Clicking the AAPL suggestion in the dropdown locks in the symbol and closes the list cleanly — no lingering spinner, no stale results from earlier keystrokes.
- **Action:** Click the "AAPL" button
- **Point out:** AAPL is selected in the symbol field and the dropdown closes.

### Step 04 — Switch to Historical mode

- **Narration:** Switching to Historical mode reveals the date and time-window pickers. This is where the new caching and fast-load improvements shine.
- **Action:** Click the "Historical" button
- **Point out:** The Historical button is highlighted and the date/time picker UI appears below the mode selector.

### Step 10 — Switch to Simulated mode for SIM-BUYER

- **Narration:** Switching to Simulated mode lets you run any named scenario without live market data. There is no dropdown requirement — just type the scenario name and click Watch.
- **Action:** Click the "Simulated" button
- **Point out:** The Simulated button is active and a plain text input replaces the autocomplete search.

### Step 11 — Type SIM-BUYER without selecting from a dropdown

- **Narration:** In Simulated mode the symbol field accepts free text. Typing 'SIM-BUYER' directly and clicking Watch — without ever touching a dropdown — works perfectly with no blocking validation error.
- **Action:** Type "SIM-BUYER" into the "Symbol" field
- **Point out:** The symbol field contains 'SIM-BUYER' typed in by hand.
