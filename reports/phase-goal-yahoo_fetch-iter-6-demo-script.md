# Demo Script — goal-yahoo_fetch-iter-6

**Mode:** record
**Date:** 2026-07-11
**Frontend URL:** http://localhost:3301
**Iteration:** 6

## Highlights

### Step 01 — Open the Structure page

- **Narration:** Let's open the Structure page, where real stock price history and its support-and-resistance levels come together in one view.
- **Action:** Navigate to /structure
- **Point out:** The 'Fetch from Yahoo Finance' panel at the top, and a second 'Load' form just below it.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-6/step-01.png

### Step 06 — Fetch real bars from Yahoo Finance

- **Narration:** Click once and the app pulls real historical prices straight from Yahoo Finance — no signup, no fee — and draws the chart immediately.
- **Action:** Click the "Fetch from Yahoo Finance" button
- **Point out:** A real candlestick chart appears with dashed support-and-resistance lines, and a 'Confluence zones' list below shows Class A/B/C zones with scores.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-6/step-06.png

### Step 07 — See exactly where the data came from  [NEW]

- **Narration:** A small badge above the chart names the real source of this data, so where the numbers came from is never a mystery.
- **Action:** Click "[data-testid='structure-title']"
- **Point out:** A dark chip reading 'feed' next to 'Yahoo Finance' in bold sits cleanly above the chart, fully readable with nothing overlapping it.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-6/step-07.png

### Step 10 — An honest message when there's no data yet  [NEW]

- **Narration:** Instead of a blank or broken-looking chart, the app plainly tells you there's nothing recorded for this symbol yet.
- **Action:** Click the "Load" button
- **Point out:** The message 'No bar series recorded for TSLA.' appears, with 'Recording historical bars needs provider credentials.' underneath — no chart, no badge, no zones.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-6/step-10.png

### Step 12 — The original Load button still works

- **Narration:** The original Load button — the one that predates today's fetch feature — still pulls up a real chart exactly as it always has.
- **Action:** Click the "Load" button
- **Point out:** The candlestick chart and confluence zones reappear for AAPL.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-6/step-12.png

### Step 15 — Nothing is ever faked

- **Narration:** The app refuses to guess — it shows a clear, honest error instead of ever making up data.
- **Action:** Click the "Fetch from Yahoo Finance" button
- **Point out:** An amber panel reads 'end must be after start,' followed by 'Nothing cached and nothing fabricated is shown in its place.' The chart above stays exactly as it was.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-6/step-15.png

## Full tour (text only)

### Step 02 — Type in a stock symbol

- **Narration:** Type a stock symbol into the fetch panel — we'll use AAPL.
- **Action:** Type "AAPL" into the "Fetch symbol" field
- **Point out:** The Symbol field now reads AAPL.

### Step 03 — Pick a daily timeframe

- **Narration:** Choose the daily timeframe, so each candle represents one trading day.
- **Action:** Type "1d" into the "Timeframe" field
- **Point out:** The Timeframe dropdown now reads 1d.

### Step 04 — Set the start of the date range

- **Narration:** Enter the start of the window of history to fetch, in UTC.
- **Action:** Type "2026-06-01T00:00:00Z" into the "Start (UTC, ISO-8601)" field
- **Point out:** The Start field is filled in.

### Step 05 — Set the end of the date range

- **Narration:** And the end of that window.
- **Action:** Type "2026-06-04T00:00:00Z" into the "End (UTC, ISO-8601)" field
- **Point out:** The End field is filled in, and the Fetch button is no longer greyed out.

### Step 08 — Ask about a symbol with no saved history  [NEW]

- **Narration:** Now let's try a symbol that has never been fetched before — TSLA — using the separate Load form below.
- **Action:** Type "TSLA" into the "Structure symbol" field
- **Point out:** The Symbol field in the Load form now reads TSLA.

### Step 09 — Set the as-of time  [NEW]

- **Narration:** Enter a time to check its levels as of.
- **Action:** Type "2026-06-05T00:00:00Z" into the "As-of (UTC, ISO-8601)" field
- **Point out:** The As-of field is filled in.

### Step 11 — Switch back to a symbol with real data

- **Narration:** Switch the symbol back to AAPL, which does have saved history.
- **Action:** Type "AAPL" into the "Structure symbol" field
- **Point out:** The Symbol field now reads AAPL again.

### Step 13 — Try an invalid date range

- **Narration:** Let's see what happens if the dates are entered backwards — end before start.
- **Action:** Type "2026-06-04T00:00:00Z" into the "Start (UTC, ISO-8601)" field
- **Point out:** The Start field in the fetch panel now holds the later date.

### Step 14 — Finish the backwards range

- **Narration:** And the End field now holds the earlier date.
- **Action:** Type "2026-06-01T00:00:00Z" into the "End (UTC, ISO-8601)" field
- **Point out:** The End field now holds a date before the Start field's date.
