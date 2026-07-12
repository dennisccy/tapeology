# Demo Script — goal-yahoo_fetch-iter-7

**Mode:** record
**Date:** 2026-07-12
**Frontend URL:** http://localhost:3301
**Iteration:** 7

## Highlights

### Step 01 — Open the Structure page

- **Narration:** Let's open the Structure page — home to real stock price history and the support-and-resistance levels built from it, all sourced straight from Yahoo Finance with no sign-up, no API key, and no fee.
- **Action:** Navigate to /structure
- **Point out:** A 'Fetch from Yahoo Finance' panel sits at the top, and a simpler, read-only 'Load' form sits just below it.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-7/step-01.png

### Step 05 — See the real chart and its levels

- **Narration:** Click Load, and the app draws a real candlestick chart with support-and-resistance levels, plus a confluence-zone breakdown — all computed from real, previously-fetched Yahoo Finance data.
- **Action:** Click the "Load" button
- **Point out:** A real candlestick chart appears with dashed support-and-resistance lines, and a 'Confluence zones' list below shows Class A/B/C zones with scores.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-7/step-05.png

### Step 06 — See exactly where the data came from

- **Narration:** A small badge above the chart names the real source of this data, so where the numbers came from is never a mystery.
- **Action:** Click "[data-testid='structure-title']"
- **Point out:** A dark chip reading 'feed' next to 'Yahoo Finance' in bold sits cleanly above the chart, fully legible with nothing overlapping it.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-7/step-06.png

### Step 07 — Ask for the same window again

- **Narration:** Ask for the same window again, and it comes right back instantly — this history is already safely stored, so there's nothing new to fetch.
- **Action:** Click the "Load" button
- **Point out:** The identical chart and confluence zones reappear immediately.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-7/step-07.png

## Full tour (text only)

### Step 02 — Preview the Yahoo Finance fetch panel

- **Narration:** This top panel is where you'd request brand-new history from Yahoo Finance for any symbol — type a ticker, like AAPL, choose one of six real timeframes (weekly down to 1-minute, including an honestly-computed 4-hour view), pick a date range, and fetch with one click.
- **Action:** Type "AAPL" into the "Fetch symbol" field
- **Point out:** The Symbol field in the Fetch panel now reads AAPL.

### Step 03 — Look up AAPL's saved history

- **Narration:** AAPL's history is already saved from an earlier fetch, so let's pull it up using the simpler, read-only Load form just below.
- **Action:** Type "AAPL" into the "Structure symbol" field
- **Point out:** The Symbol field in the Load form now reads AAPL.

### Step 04 — Set the as-of time

- **Narration:** Enter a point in time to check its levels as of.
- **Action:** Type "2026-06-05T00:00:00Z" into the "As-of (UTC, ISO-8601)" field
- **Point out:** The As-of field is filled in.
