# Demo Script — goal-clean_slate-iter-3

**Mode:** record
**Date:** 2026-07-24
**Frontend URL:** http://localhost:3301
**Iteration:** 3

## Highlights

### Step 01 — Tapeology today: the same clean two-page cockpit

- **Narration:** This round's work happened behind the scenes — trimming an AI-assistant helper's tool list down to only the pages that still exist — so here is the app looking and working exactly as it did before.
- **Action:** Navigate to /
- **Point out:** The navigation bar still shows just two links, Cockpit and Structure, with nothing left over from pages retired earlier.
- **Screenshot:** reports/demo/goal-clean_slate-iter-3/step-01.png

### Step 02 — A retired page stays retired

- **Narration:** Just to double-check nothing crept back, the old trade-journal address still shows an honest "not found" message instead of any leftover screen.
- **Action:** Navigate to /journal
- **Point out:** Confirms the earlier cleanup is holding steady, not quietly reversed.
- **Screenshot:** reports/demo/goal-clean_slate-iter-3/step-02.png

### Step 05 — Watching a live simulated tape

- **Narration:** Clicking Watch starts a live simulated price tape, the same way it always has, and a fresh set of panels appears on screen.
- **Action:** Click the "Watch" button
- **Point out:** Six panels appear — Tape State, Quote, Features, Recent Trades, Observations, Event Log — above a live price chart.
- **Screenshot:** reports/demo/goal-clean_slate-iter-3/step-05.png

### Step 06 — Live candles keep moving

- **Narration:** Switching the chart to 30-second bars shows the tape is genuinely live, not a frozen picture.
- **Action:** Click "div[aria-label="Tape bar size"] button:nth-of-type(2)"
- **Point out:** New candlestick bars keep appearing at the right edge of the chart as the simulated tape streams.
- **Screenshot:** reports/demo/goal-clean_slate-iter-3/step-06.png

### Step 07 — Stopping cleanly

- **Narration:** Clicking Stop ends the watch and returns straight to the plain idle screen.
- **Action:** Click the "Stop" button
- **Point out:** No leftover panel or banner appears — just the same clean idle screen as always.
- **Screenshot:** reports/demo/goal-clean_slate-iter-3/step-07.png

### Step 13 — Real data, clearly labeled

- **Narration:** Switching to the 1-hour view shows the same support-and-resistance shading as always, now backed by real data.
- **Action:** Click the "1h" button
- **Point out:** A shaded price band renders on the chart, and the "feed" badge reads "SIP (consolidated)" rather than "Simulated".
- **Screenshot:** reports/demo/goal-clean_slate-iter-3/step-13.png

### Step 14 — Exploring the Structure page

- **Narration:** The Structure page is the second and last stop in the app, for studying a stock's price levels.
- **Action:** Navigate to /structure
- **Point out:** A simple form is ready for a symbol and an as-of time — no chart or clutter until something is loaded.
- **Screenshot:** reports/demo/goal-clean_slate-iter-3/step-14.png

### Step 17 — The price wall, unchanged

- **Narration:** Clicking Load reveals the stock's strongest nearby price levels — exactly as this page has always shown them, undisturbed by this round's behind-the-scenes cleanup.
- **Action:** Click the "Load" button
- **Point out:** The table's top resistance row spans roughly 300 to 302, marked Class A with a round-number flag, and the same band is drawn directly on the chart below.
- **Screenshot:** reports/demo/goal-clean_slate-iter-3/step-17.png

## Full tour (text only)

### Step 03 — Back to the cockpit

- **Narration:** Heading back to the home screen, ready to watch a live tape.
- **Action:** Navigate to /
- **Point out:** The same simple idle screen, ready for a new watch.

### Step 04 — Typing a ticker to watch

- **Narration:** Typing SIM-BUYER, a built-in scripted simulation, into the ticker field.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** The Watch button, previously dimmed, becomes clickable as soon as a character is typed.

### Step 08 — Switching to real market data

- **Narration:** Switching the data source to Historical, to look at a real recorded trading day instead of a simulation.
- **Action:** Click the "Historical" button
- **Point out:** The header switches to the Historical symbol-search layout.

### Step 09 — Choosing a symbol to replay

- **Narration:** Typing AAPL as the symbol to replay.
- **Action:** Type "AAPL" into "Symbol e.g. AAPL"
- **Point out:** The symbol field accepts free-text entry, no dropdown selection required.

### Step 10 — Choosing a trading day

- **Narration:** Typing in a June trading day to replay.
- **Action:** Type "22-06-2026" into "dd-MM-yyyy"
- **Point out:** The date field uses a simple day-month-year format.

### Step 11 — Jumping straight to the open

- **Narration:** One click fills in the market-open replay window.
- **Action:** Click the "Open 9:30 ET" button
- **Point out:** The start and end time fields fill in automatically for the 9:30am market open.

### Step 12 — Watching the real replay

- **Narration:** Clicking Watch replays that recorded trading day using real market data.
- **Action:** Click the "Watch" button
- **Point out:** The cockpit loads normally with real data, not a "provider unavailable" notice.

### Step 15 — Choosing a symbol to study

- **Narration:** Typing AAPL into the Symbol field.
- **Action:** Type "AAPL" into "e.g. PG"
- **Point out:** The symbol field is ready for input.

### Step 16 — Choosing an as-of time

- **Narration:** Typing in a specific date and time to study.
- **Action:** Type "2026-06-22T21:00:00Z" into "2026-06-09T21:00:00Z"
- **Point out:** The as-of field accepts a precise UTC timestamp.
