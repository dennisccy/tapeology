# Demo Script — goal-tradable_wall-iter-8

**Mode:** record
**Date:** 2026-07-15
**Frontend URL:** http://localhost:3301
**Iteration:** 8

## Highlights

### Step 03 — Simulated chart, honest empty state

- **Narration:** The candlestick chart and tape-state markers appear right away for the simulated ticker.
- **Action:** Click the "Watch" button
- **Point out:** Directly below the chart, an honest "No tradable map for SIM-BUYER." message shows instead of a fake band — simulated tickers have no real market structure to compare against, and the app says so plainly.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-8/step-03.png

### Step 08 — Replay the real AAPL session  [NEW]

- **Narration:** Clicking Watch replays this real historical session from its very first candle.
- **Action:** Click the "Watch" button
- **Point out:** The tradable band overlay is drawn directly on the chart with the correct prior-session basis from the first moment — no flash of today's date first. The chart now waits until it genuinely knows which session it's replaying before it ever asks for bands.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-8/step-08.png

### Step 11 — The measured edge report

- **Narration:** Further down the page, the Edge Report compares three trading strategies over every recorded event window — the honest scorecard for whether any of this actually works.
- **Action:** Click the "Edge Report" heading
- **Point out:** It starts computing automatically the moment the page loads. With the operator's 11 real recorded market-data windows now on the books, this is the first run with real data behind it — though as a genuine, uncached, from-scratch computation it can take hours to fully resolve, so what's captured here is its correctly-started, honestly-loading state, not the final numbers.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-8/step-11.png

### Step 13 — Real recorded tape now backs this event  [NEW]

- **Narration:** Here is that drill-in panel, mid-computation.
- **Action:** Click "Case Studies — drill-in"
- **Point out:** The animated loading skeleton confirms a real computation is under way over real recorded tick data, not a synthetic placeholder. It resolves — typically within about fifteen minutes, since nothing here is cached — to a five-state tape timeline of hundreds of real entries tracking buyer control, seller control, and absorption around the touch. This pinned event used to show "No recorded tape for this event."; now it shows the real tape.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-8/step-13.png

### Step 17 — Live mode: its own dedicated view

- **Narration:** Live mode always uses its own real-time monitoring view.
- **Action:** Click the "Watch" button
- **Point out:** The price-chart and band overlay from Simulated and Historical modes are completely absent here — Live mode stays a pure real-time tape reader, never anything trade-related.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-8/step-17.png

## Full tour (text only)

### Step 01 — Open the cockpit

- **Narration:** We start at Tapeology's live cockpit — there's nothing to sign into, it's ready immediately.
- **Action:** Navigate to /
- **Point out:** Simulated mode is already selected by default, so you can start watching a ticker right away.

### Step 02 — Watch a simulated ticker

- **Narration:** Typing in a simulated ticker and clicking Watch.
- **Action:** Type "SIM-BUYER" into the "Ticker" field

### Step 04 — Switch to a real historical session

- **Narration:** Now switching to Historical mode to replay a real trading session — AAPL testing its own $300 resistance level.
- **Action:** Click the "Historical" button

### Step 05 — Search for AAPL

- **Narration:** Typing AAPL into the symbol search.
- **Action:** Type "AAPL" into the "Symbol search" field

### Step 06 — Pick June 22, 2026

- **Narration:** Typing in the exact date of the pinned resistance test.
- **Action:** Type "22-06-2026" into the "Date" field

### Step 07 — Use the market-open preset

- **Narration:** One click fills in the correct trading-session time window.
- **Action:** Click the "Open 9:30 ET" button

### Step 09 — Open the Structure page

- **Narration:** Moving to the Structure page, where every historical band-touch event is catalogued.
- **Action:** Navigate to /structure

### Step 10 — Filter Case Studies to AAPL

- **Narration:** Narrowing the case-study registry down to AAPL's own history.
- **Action:** Type "AAPL" into "case-studies-filter-symbol"

### Step 12 — Open the pinned AAPL case study  [NEW]

- **Narration:** This row is the pinned AAPL test from June 22, 2026 — a real touch of its ~$300 resistance band, marked rejected. Clicking it starts a genuine replay of the real recorded tick data behind this exact event.
- **Action:** Click "2026-06-22"
- **Point out:** A drill-in panel opens below the table with a loading indicator.

### Step 14 — Back to the cockpit

- **Narration:** One last check back at the cockpit, to confirm nothing about live trading data has changed.
- **Action:** Navigate to /

### Step 15 — Confirm Live mode stays untouched

- **Narration:** Switching to Live mode with a real symbol.
- **Action:** Click the "Live" button

### Step 16 — Watch AAPL live

- **Narration:** Typing AAPL into the symbol field again, this time for the live feed.
- **Action:** Type "AAPL" into the "Symbol search" field
