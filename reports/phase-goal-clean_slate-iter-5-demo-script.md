# Demo Script — goal-clean_slate-iter-5

**Mode:** record
**Date:** 2026-07-24
**Frontend URL:** http://localhost:3301
**Iteration:** 5

## Highlights

### Step 01 — Open the Cockpit

- **Narration:** Tapeology opens on the Cockpit — a live, simulated, or historical trading-tape viewer, with no sign-in needed.
- **Action:** Navigate to /
- **Point out:** The page loads idle, hinting to try a ticker like SIM-BUYER, with a top navigation bar showing just two links.
- **Screenshot:** reports/demo/goal-clean_slate-iter-5/step-01.png

### Step 03 — Watch it settle to a market read

- **Narration:** Clicking Watch starts the simulated tape; within a few seconds it reads which side is in control of the price action.
- **Action:** Click the "Watch" button
- **Point out:** The Tape State panel now reads "Buyer Control", and a live candlestick price chart has appeared above it.
- **Screenshot:** reports/demo/goal-clean_slate-iter-5/step-03.png

### Step 04 — Switch the chart's bar size

- **Narration:** The live price chart can be re-grouped into wider logical bars on the fly, without losing the live feed.
- **Action:** Click "[aria-label="Tape bar size"] button:nth-of-type(2)"
- **Point out:** "30s" is now highlighted, the caption updates, and the chart redraws with fewer, wider candles built live from the tape.
- **Screenshot:** reports/demo/goal-clean_slate-iter-5/step-04.png

### Step 09 — Load AAPL's tradable map

- **Narration:** Loading a symbol and a date renders its candlestick chart together with a shaded support/resistance wall band.
- **Action:** Click the "Load" button
- **Point out:** The chart shows AAPL's candles with a tradable wall band around 300.11 to 302.2, and a table below it lists that band's details.
- **Screenshot:** reports/demo/goal-clean_slate-iter-5/step-09.png

### Step 10 — Browse every recorded price-wall touch  [NEW]

- **Narration:** Scrolling down reveals the Case Studies panel — a list of every recorded support/resistance band touch — which had been hidden from the page until this chapter's clean-up restored it. Typing a symbol narrows the list instantly.
- **Action:** Type "AAPL" into "e.g. AAPL"
- **Point out:** The table narrows to AAPL's recorded events only, each row showing its band, its reaction, and its forward returns.
- **Screenshot:** reports/demo/goal-clean_slate-iter-5/step-10.png

### Step 11 — Open a case-study drill-in  [NEW]

- **Narration:** Clicking any row opens a detailed drill-in for that specific event.
- **Action:** Click "case-studies-row"
- **Point out:** The drill-in repeats the row's band and reaction, then shows either a recorded tape timeline or the honest note that no tape was recorded for that event.
- **Screenshot:** reports/demo/goal-clean_slate-iter-5/step-11.png

### Step 12 — Check the Edge Report's honest state

- **Narration:** The Edge Report compares three trading strategies over recorded windows — when it has not been computed yet, it says so plainly instead of showing a blank panel, and offers a button to start the comparison.
- **Action:** Click the "Compute edge report" button
- **Point out:** Clicking Compute edge report immediately switches the label to "Computing…" and shows a live progress line, confirming the control is wired up.
- **Screenshot:** reports/demo/goal-clean_slate-iter-5/step-12.png

### Step 15 — Back to the Cockpit

- **Narration:** Clicking back through the trimmed navigation confirms both pages still connect correctly.
- **Action:** Click the "Cockpit" link
- **Point out:** The nav bar shows only "Cockpit" and "Structure" — nothing left over from the three retired pages — and the Cockpit is back to its idle state.
- **Screenshot:** reports/demo/goal-clean_slate-iter-5/step-15.png

## Full tour (text only)

### Step 02 — Type a ticker to watch

- **Narration:** Typing a simulated ticker into the ticker field is the first step to watching a live tape settle.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** "SIM-BUYER" now sits in the ticker field, ready to watch.

### Step 05 — Stop the watch

- **Narration:** Stopping instantly clears the tape back to its idle state — the watch-and-stop loop still works end to end.
- **Action:** Click the "Stop" button
- **Point out:** The page returns to "No ticker watched".

### Step 06 — Move to the Structure page  [NEW]

- **Narration:** The top navigation shows exactly two links — Cockpit and Structure — nothing left over from the research pages retired this chapter.
- **Action:** Click the "Structure" link
- **Point out:** The Structure page's framing paragraph now mentions Case Studies again — a sentence that had gone missing and is reinstated this iteration.

### Step 07 — Enter a symbol to study

- **Narration:** Loading Structure starts with a symbol and a point in time.
- **Action:** Type "AAPL" into "e.g. PG"
- **Point out:** "AAPL" now sits in the Symbol field.

### Step 08 — Enter the as-of date

- **Narration:** The as-of field pins the exact moment the levels and chart are computed for.
- **Action:** Type "2026-06-22T21:00:00Z" into "2026-06-09T21:00:00Z"
- **Point out:** The as-of field now reads the chosen date and time.

### Step 13 — Cancel the compute run

- **Narration:** Cancelling stops the run cleanly and leaves no long job running in the background.
- **Action:** Click the "Cancel compute" button
- **Point out:** The Cancel button confirms it is finishing the current backtest before stopping.

### Step 14 — Confirm a retired page is really gone

- **Narration:** Visiting one of the three removed research pages directly still shows the app's plain not-found screen, never a stale leftover page.
- **Action:** Navigate to /journal
- **Point out:** "This page could not be found" appears, and the same two-item navigation bar is still there at the top.
