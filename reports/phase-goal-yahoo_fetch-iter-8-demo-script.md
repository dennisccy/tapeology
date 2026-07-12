# Demo Script — goal-yahoo_fetch-iter-8

**Mode:** record
**Date:** 2026-07-13
**Frontend URL:** http://localhost:3301
**Iteration:** 8

## Highlights

### Step 01 — Open the Structure page

- **Narration:** Let's open the Structure page — this is where Tapeology fetches real stock price history straight from Yahoo Finance, no sign-up or fee required, and turns it into support-and-resistance levels.
- **Action:** Navigate to /structure
- **Point out:** A 'Fetch from Yahoo Finance' panel sits at the top of the page, with a simpler, read-only 'Load' form just below it.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-8/step-01.png

### Step 06 — Fetch real bars from Yahoo Finance

- **Narration:** Click once, and the app pulls real historical prices straight from Yahoo Finance — no sign-up, no API key, no fee — and draws the chart immediately.
- **Action:** Click the "Fetch from Yahoo Finance" button
- **Point out:** A real candlestick chart appears with dashed support-and-resistance lines, and a 'Confluence zones' list below shows Class A/B/C zones with scores drawn from several real timeframes together.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-8/step-06.png

### Step 07 — See exactly where the data came from

- **Narration:** A small badge above the chart names exactly where this data came from, so it's never a mystery.
- **Action:** Click "[data-testid='structure-title']"
- **Point out:** A dark chip reading 'feed' next to 'Yahoo Finance' in bold sits cleanly above the chart.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-8/step-07.png

### Step 08 — Ask for the same window again

- **Narration:** Ask for that exact same window again, and it comes right back instantly — this history is already safely stored, so there's nothing new to fetch and nothing gets duplicated.
- **Action:** Click the "Fetch from Yahoo Finance" button
- **Point out:** The identical chart and confluence zones reappear immediately.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-8/step-08.png

### Step 11 — Load the same real levels from storage

- **Narration:** Click Load, and the same real support-and-resistance levels and confluence zones appear again, this time read straight from storage rather than a fresh fetch.
- **Action:** Click the "Load" button
- **Point out:** The candlestick chart and confluence-zone list reappear for AAPL.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-8/step-11.png

### Step 12 — Confirm the rest of the app still works

- **Narration:** Finally, a quick check that nothing else broke while this chapter was being finished: the replay studies lab — where past trade setups get tested against history — still opens exactly as it always has.
- **Action:** Navigate to /studies
- **Point out:** The 'Replay studies' heading renders cleanly at the top of the page.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-8/step-12.png

## Full tour (text only)

### Step 02 — Type in a stock symbol

- **Narration:** Type in a stock symbol to fetch its real history — we'll use AAPL.
- **Action:** Type "AAPL" into the "Fetch symbol" field
- **Point out:** The Symbol field in the fetch panel now reads AAPL.

### Step 03 — Choose a real timeframe

- **Narration:** Pick a timeframe. Six real choices are on offer here — weekly down to 1-minute, including an honestly self-computed 4-hour view — and every one of them is genuine, never invented.
- **Action:** Type "1d" into the "Timeframe" field
- **Point out:** The Timeframe field now reads 1d.

### Step 04 — Set the start of the date range

- **Narration:** Set the start of the date range to fetch, in UTC.
- **Action:** Type "2026-06-01T00:00:00Z" into the "Start (UTC, ISO-8601)" field
- **Point out:** The Start field is filled in.

### Step 05 — Set the end of the date range

- **Narration:** And the end of that range.
- **Action:** Type "2026-06-04T00:00:00Z" into the "End (UTC, ISO-8601)" field
- **Point out:** The End field is filled in, and the fetch button is no longer greyed out.

### Step 09 — Look up the same stock a simpler way

- **Narration:** The page also has a simpler, read-only Load form below the fetch panel — let's look up AAPL through that instead.
- **Action:** Type "AAPL" into the "Structure symbol" field
- **Point out:** The Symbol field in the Load form now reads AAPL.

### Step 10 — Set the as-of time

- **Narration:** Enter a point in time to check its levels as of.
- **Action:** Type "2026-06-05T00:00:00Z" into the "As-of (UTC, ISO-8601)" field
- **Point out:** The As-of field is filled in.
