# Demo Script — goal-tradable_wall-iter-10

**Mode:** record
**Date:** 2026-07-16
**Frontend URL:** http://localhost:3301
**Iteration:** 10

## Highlights

### Step 03 — An honest empty state for a made-up ticker

- **Narration:** Click Watch. SIM-BUYER is a made-up practice ticker with no real trading history behind it, so there's no real price zone to show for it.
- **Action:** Click the "Watch" button
- **Point out:** Right below the live chart, a small honest note reads "No tradable map for SIM-BUYER." — the app never invents a price zone that isn't really there.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-10/step-03.png

### Step 08 — Replay a real AAPL session

- **Narration:** Click Watch to replay that real session from its first candle.
- **Action:** Click the "Watch" button
- **Point out:** Real support and resistance lines are drawn directly over the candles near $300 — the same price map the Structure page builds — and where the tape sits right on one of them, a short factual note explains what's happening, never what to trade.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-10/step-08.png

### Step 09 — Open Structure — still decluttered

- **Narration:** Now to the Structure page, where this price map gets researched and studied in depth.
- **Action:** Navigate to /structure
- **Point out:** It still opens straight to a short, clean list of price zones by default — the thousands of raw underlying levels stay tucked out of sight until asked for.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-10/step-09.png

### Step 12 — The short list, not the flood

- **Narration:** Click Load to build the price map for that exact moment.
- **Action:** Click "structure-load-button"
- **Point out:** Instead of a flood of raw levels, this session boils down to no more than ten price bands — and the $300 zone from the cockpit chart shows up again here, ranked as the single strongest resistance band on the list.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-10/step-12.png

### Step 13 — Peek behind the curtain

- **Narration:** Click "Show raw levels" to see the full underlying detail this short list was distilled from.
- **Action:** Click "raw-levels-toggle"
- **Point out:** The original, denser price-level chart and its confluence zones reveal themselves — still there for anyone who wants it, just no longer the first thing anyone sees.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-10/step-13.png

### Step 14 — Every recorded band touch, filterable

- **Narration:** Further down the page, the Case Studies registry lists every recorded touch of a price band across a whole panel of stocks. Typing AAPL narrows it to this stock's own history.
- **Action:** Type "AAPL" into "case-studies-filter-symbol"
- **Point out:** Each row names the band that was touched, whether price got rejected or broke through, and what happened afterward — a real, measured track record.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-10/step-14.png

### Step 15 — The edge report finally resolves  [NEW]

- **Narration:** Scrolling to the Edge Report — the honest scorecard comparing trading strategies over everything ever recorded.
- **Action:** Click the "Edge Report" heading
- **Point out:** This panel used to sit loading indefinitely, because building it from scratch could take upwards of ten hours. Today it resolves in seconds, and reports the honest truth for what's recorded so far — including saying plainly when nothing yet clears this project's own strict bar for a reportable result, rather than hiding the question.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-10/step-15.png

## Full tour (text only)

### Step 01 — Open the cockpit

- **Narration:** Start at Tapeology's cockpit — the screen for watching any stock's live tape. There's nothing to sign into; it's ready right away.
- **Action:** Navigate to /
- **Point out:** The data-source control at top-left is already set to Simulated, so there's a ticker ready to watch immediately.

### Step 02 — Pick the practice ticker

- **Narration:** Type SIM-BUYER, the app's built-in practice ticker, into the Ticker field.
- **Action:** Type "SIM-BUYER" into the "Ticker" field
- **Point out:** The Ticker field now reads SIM-BUYER.

### Step 04 — Switch to a real trading day

- **Narration:** Click Historical to replay a real recorded trading session instead of a simulation.
- **Action:** Click the "Historical" button
- **Point out:** The controls switch to a real symbol search plus a date and time window.

### Step 05 — Search for AAPL

- **Narration:** Type AAPL into the symbol search.
- **Action:** Type "AAPL" into the "Symbol search" field
- **Point out:** The Symbol field now reads AAPL.

### Step 06 — Pick the pinned session

- **Narration:** Type in a real June trading day — the session where AAPL tested its own $300 ceiling.
- **Action:** Type "22-06-2026" into the "Date" field
- **Point out:** The Date field now reads 22-06-2026.

### Step 07 — Fill the whole session in one click

- **Narration:** Click the full-session quick-pick to fill the whole trading day's time window in one click.
- **Action:** Click the "Full RTH 9:30–16:00 ET" button
- **Point out:** The start and end time fields fill in automatically.

### Step 10 — Pick the same stock

- **Narration:** Type AAPL into the Symbol field.
- **Action:** Type "AAPL" into the "Structure symbol" field
- **Point out:** The Symbol field now reads AAPL.

### Step 11 — Pick the same moment

- **Narration:** Enter that same June session as an as-of time.
- **Action:** Type "2026-06-22T21:00:00Z" into "structure-as-of-input"
- **Point out:** The As-of field now reads the chosen date and time.
