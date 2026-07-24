# Demo Script — goal-clean_slate-iter-2

**Mode:** record
**Date:** 2026-07-24
**Frontend URL:** http://localhost:3301
**Iteration:** 2

## Highlights

### Step 01 — A cleaner cockpit  [NEW]

- **Narration:** Here's Tapeology's home screen today — a live tape reader with a clean, focused menu at the top.
- **Action:** Navigate to /
- **Point out:** The navigation bar now shows just two links, Cockpit and Structure — no leftover menu items.
- **Screenshot:** reports/demo/goal-clean_slate-iter-2/step-01.png

### Step 02 — The old journal page is really gone  [NEW]

- **Narration:** Typing in the address of the old trade-journal page shows an honest "not found" message instead of any leftover screen.
- **Action:** Navigate to /journal
- **Point out:** This confirms the page was removed outright, not just hidden from the menu.
- **Screenshot:** reports/demo/goal-clean_slate-iter-2/step-02.png

### Step 07 — Watching a live simulated tape  [NEW]

- **Narration:** Clicking Watch starts a live simulated price tape, and a fresh set of panels appears on screen.
- **Action:** Click the "Watch" button
- **Point out:** Six panels appear — Tape State, Quote, Features, Recent Trades, Observations, Event Log — above a live price chart, with none of the old thesis, hint, or sound controls.
- **Screenshot:** reports/demo/goal-clean_slate-iter-2/step-07.png

### Step 08 — Live candles keep moving

- **Narration:** Switching the chart to 30-second bars shows the tape is genuinely live, not a frozen picture.
- **Action:** Click "div[aria-label="Tape bar size"] button:nth-of-type(2)"
- **Point out:** New candlestick bars keep appearing at the right edge of the chart as the simulated tape streams.
- **Screenshot:** reports/demo/goal-clean_slate-iter-2/step-08.png

### Step 09 — Stopping cleanly  [NEW]

- **Narration:** Clicking Stop ends the watch and returns straight to the plain idle screen.
- **Action:** Click the "Stop" button
- **Point out:** No leftover panel or banner appears — just the same clean idle screen as before.
- **Screenshot:** reports/demo/goal-clean_slate-iter-2/step-09.png

### Step 15 — Real data, clearly labeled

- **Narration:** Switching to the 1-hour view shows the same support-and-resistance shading as always, now backed by real data.
- **Action:** Click the "1h" button
- **Point out:** A shaded price band renders on the chart, and the "feed" badge reads "SIP (consolidated)" rather than "Simulated".
- **Screenshot:** reports/demo/goal-clean_slate-iter-2/step-15.png

### Step 16 — Exploring the Structure page

- **Narration:** The Structure page is the second and last stop in the app, for studying a stock's price levels.
- **Action:** Navigate to /structure
- **Point out:** A simple form is ready for a symbol and an as-of time — no chart or clutter until something is loaded.
- **Screenshot:** reports/demo/goal-clean_slate-iter-2/step-16.png

### Step 19 — The price wall, unchanged

- **Narration:** Clicking Load reveals the stock's strongest nearby price levels — exactly as this page has always shown them.
- **Action:** Click the "Load" button
- **Point out:** The table's top resistance row spans roughly 300 to 302, marked Class A with a round-number flag, and the same band is drawn directly on the chart below.
- **Screenshot:** reports/demo/goal-clean_slate-iter-2/step-19.png

## Full tour (text only)

### Step 03 — The studies page is gone too  [NEW]

- **Narration:** The old replay-studies workbench is gone the same way.
- **Action:** Navigate to /studies
- **Point out:** Same honest "not found" treatment — no leftover form or results list.

### Step 04 — So is the performance dashboard  [NEW]

- **Narration:** So is the old performance dashboard — cleanly removed, not just hidden.
- **Action:** Navigate to /performance
- **Point out:** All three retired pages behave identically: an honest "not found", never a blank screen or crash.

### Step 05 — Back to the cockpit

- **Narration:** Back on the home screen, ready to watch a live tape.
- **Action:** Navigate to /
- **Point out:** The same simple idle screen, ready for a new watch.

### Step 06 — Typing a ticker to watch

- **Narration:** Typing SIM-BUYER, a built-in scripted simulation, into the ticker field.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** The Watch button, previously dimmed, becomes clickable as soon as a character is typed.

### Step 10 — Switching to real market data

- **Narration:** Switching the data source to Historical, to look at a real recorded trading day instead of a simulation.
- **Action:** Click the "Historical" button
- **Point out:** The header switches to the Historical symbol-search layout.

### Step 11 — Choosing a symbol to replay

- **Narration:** Typing AAPL as the symbol to replay.
- **Action:** Type "AAPL" into "Symbol e.g. AAPL"
- **Point out:** The symbol field accepts free-text entry, no dropdown selection required.

### Step 12 — Choosing a trading day

- **Narration:** Typing in a June trading day to replay.
- **Action:** Type "22-06-2026" into "dd-MM-yyyy"
- **Point out:** The date field uses a simple day-month-year format.

### Step 13 — Jumping straight to the open

- **Narration:** One click fills in the market-open replay window.
- **Action:** Click the "Open 9:30 ET" button
- **Point out:** The start and end time fields fill in automatically for the 9:30am market open.

### Step 14 — Watching the real replay

- **Narration:** Clicking Watch replays that recorded trading day using real market data.
- **Action:** Click the "Watch" button
- **Point out:** The cockpit loads normally with real data, not a "provider unavailable" notice.

### Step 17 — Choosing a symbol to study

- **Narration:** Typing AAPL into the Symbol field.
- **Action:** Type "AAPL" into "e.g. PG"
- **Point out:** The symbol field is ready for input.

### Step 18 — Choosing an as-of time

- **Narration:** Typing in a specific date and time to study.
- **Action:** Type "2026-06-22T21:00:00Z" into "2026-06-09T21:00:00Z"
- **Point out:** The as-of field accepts a precise UTC timestamp.
