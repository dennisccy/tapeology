# Demo Script — goal-clean_slate-iter-6

**Mode:** record
**Date:** 2026-07-24
**Frontend URL:** http://localhost:3301
**Iteration:** 6

## Highlights

### Step 01 — Open the Cockpit

- **Narration:** Tapeology opens on the Cockpit — a live, simulated, or historical trading-tape viewer, with no sign-in needed.
- **Action:** Navigate to /
- **Point out:** The page loads idle, inviting you to try a ticker like SIM-BUYER, with a top navigation bar showing just two links.
- **Screenshot:** reports/demo/goal-clean_slate-iter-6/step-01.png

### Step 03 — Watch it settle to a market read

- **Narration:** Clicking Watch starts the simulated tape; within a few seconds it reads which side is in control of the price action.
- **Action:** Click the "Watch" button
- **Point out:** The Tape State panel now reads "Buyer Control", with a live candlestick price chart above it.
- **Screenshot:** reports/demo/goal-clean_slate-iter-6/step-03.png

### Step 04 — Switch the chart's bar size

- **Narration:** The live price chart can be re-grouped into wider logical bars on the fly, without losing the live feed.
- **Action:** Click "[aria-label="Tape bar size"] button:nth-of-type(2)"
- **Point out:** The caption updates and the chart redraws with fewer, wider candles built live from the tape.
- **Screenshot:** reports/demo/goal-clean_slate-iter-6/step-04.png

### Step 06 — Move to the Structure page

- **Narration:** One click on Structure in the top navigation opens the support/resistance analysis view, its panels ready as soon as the page loads.
- **Action:** Click the "Structure" link
- **Point out:** The Symbol/As-of/Load flow, the Case Studies table, and an Edge Report panel are all visible right away — and the Edge Report panel already reports its own honest status rather than a blank space.
- **Screenshot:** reports/demo/goal-clean_slate-iter-6/step-06.png

### Step 07 — Confirm the Load form won't invent a result

- **Narration:** Clicking Load before choosing a symbol or a date proves the page never makes up an answer — it simply stays put.
- **Action:** Click the "Load" button
- **Point out:** The Tradable Map stays on its plain "Choose a symbol and an as-of time" placeholder — no price level appears from an empty form.
- **Screenshot:** reports/demo/goal-clean_slate-iter-6/step-07.png

### Step 10 — Load AAPL's tradable map

- **Narration:** Loading a symbol and a date renders its candlestick chart together with a shaded support/resistance wall band.
- **Action:** Click the "Load" button
- **Point out:** The chart shows AAPL's candles with a tradable wall band around 300.11 to 302.2, and a table below it lists that band's details.
- **Screenshot:** reports/demo/goal-clean_slate-iter-6/step-10.png

### Step 11 — Open a case-study drill-in

- **Narration:** Clicking any row in the Case Studies table opens a detailed drill-in for that specific event.
- **Action:** Click "case-studies-row"
- **Point out:** The drill-in repeats the row's band and reaction, then shows either a recorded tape timeline or the honest note that no tape was recorded for that event.
- **Screenshot:** reports/demo/goal-clean_slate-iter-6/step-11.png

### Step 12 — Back to the Cockpit, navigation still intact

- **Narration:** Clicking back through the same two-item navigation confirms both pages still connect correctly, with nothing extra ever added.
- **Action:** Click the "Cockpit" link
- **Point out:** The nav bar shows only "Cockpit" and "Structure" — exactly the same two links as at the very start of this tour.
- **Screenshot:** reports/demo/goal-clean_slate-iter-6/step-12.png

## Full tour (text only)

### Step 02 — Type a ticker to watch

- **Narration:** Typing a simulated ticker into the ticker field is the first step to watching a live tape settle.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** "SIM-BUYER" now sits in the ticker field, ready to watch.

### Step 05 — Stop watching

- **Narration:** Stopping instantly clears the tape back to its idle state — the watch-and-stop loop still works end to end.
- **Action:** Click the "Stop watching" button
- **Point out:** The page returns to "No ticker watched".

### Step 08 — Enter a symbol to study

- **Narration:** Loading Structure starts with a symbol and a point in time.
- **Action:** Type "AAPL" into "e.g. PG"
- **Point out:** "AAPL" now sits in the Symbol field.

### Step 09 — Enter the as-of date

- **Narration:** The as-of field pins the exact moment the levels and chart are computed for.
- **Action:** Type "2026-06-22T21:00:00Z" into "2026-06-09T21:00:00Z"
- **Point out:** The as-of field now reads the chosen date and time.
