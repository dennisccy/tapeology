# Demo Script — goal-yahoo_fetch-iter-1

**Mode:** record
**Date:** 2026-07-09
**Frontend URL:** http://localhost:3301
**Iteration:** 1

## Highlights

### Step 01 — Open the cockpit

- **Narration:** Let's start at Tapeology's home page — the live cockpit where a trader watches a ticker's tape in real time.
- **Action:** Navigate to /
- **Point out:** The Live / Historical / Simulated toggle at the top, and a friendly empty state waiting for a ticker to watch.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-1/step-01.png

### Step 03 — Watch the live tape

- **Narration:** Click Watch, and the cockpit springs to life with a full set of live tape-reading panels.
- **Action:** Click the "Watch" button
- **Point out:** Six live panels appear — Tape State, Quote, Recent Trades, Features, Observations, and Event Log — with a feed badge confirming the data source.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-1/step-03.png

### Step 04 — Open Structure

- **Narration:** Now let's look at the Structure page, where Tapeology maps out a stock's key support-and-resistance price levels.
- **Action:** Navigate to /structure
- **Point out:** A Symbol and As-of form, plus a Registry panel naming the reigning Champion trading strategy.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-1/step-04.png

### Step 07 — Load the price structure

- **Narration:** Click Load, and the chart renders that symbol's real price history with support-and-resistance levels drawn on top.
- **Action:** Click the "Load" button
- **Point out:** A full candlestick chart appears with level lines, plus a row of confluence zone cards below showing where several levels cluster together.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-1/step-07.png

### Step 08 — Open the Journal

- **Narration:** Next, the Journal — where every trade idea gets logged and later graded against what the tape actually did.
- **Action:** Navigate to /journal
- **Point out:** A table of past theses, each tagged with its data feed and outcome.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-1/step-08.png

### Step 09 — Review a trade idea

- **Narration:** Click into a thesis to see its full review — what was expected, what actually happened, and how it graded.
- **Action:** Click the "SIM-SELLER" link
- **Point out:** The review page breaks down entry risk, execution checks, and the tape's verdict timeline for this trade.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-1/step-09.png

### Step 10 — Open Studies

- **Narration:** Over on Studies, you can replay past trade setups against historical data to see how a strategy would have performed.
- **Action:** Navigate to /studies
- **Point out:** A study-creation form on the left, and a results panel on the right ready to show whatever you select.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-1/step-10.png

### Step 12 — Open Performance

- **Narration:** Finally, Performance — an honest scorecard of how each strategy has actually done, including on data it's never seen before.
- **Action:** Navigate to /performance
- **Point out:** A PnL ledger on the left, and the current Champion strategy summary on the right.
- **Screenshot:** reports/demo/goal-yahoo_fetch-iter-1/step-12.png

## Full tour (text only)

### Step 02 — Choose a ticker to watch

- **Narration:** Type in a ticker to watch — here, the app's own built-in simulated ticker, SIM-BUYER, which needs no real market data or credentials.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** The ticker field now reads SIM-BUYER.

### Step 05 — Pick a symbol

- **Narration:** Enter a real stock symbol — AAPL — to pull up its price structure.
- **Action:** Type "AAPL" into the "Symbol" field
- **Point out:** The Symbol field now reads AAPL.

### Step 06 — Set the as-of time

- **Narration:** Set the as-of time so the chart shows exactly what was known at that moment.
- **Action:** Type "2026-06-05T00:00:00Z" into the "As-of (UTC, ISO-8601)" field
- **Point out:** The As-of field is filled in and ready to load.

### Step 11 — Watch the study form respond live

- **Narration:** Switch the study's data source to a seeded simulation, and a scenario picker appears live — every field in the form responds instantly.
- **Action:** Click the "Seeded sim scenario" radio
- **Point out:** A new "Sim scenario" dropdown shows up with options like SIM-REVERSAL and SIM-BUYER.

### Step 13 — A broken link stays graceful

- **Narration:** Even a broken link stays graceful — if a thesis doesn't exist, the Journal shows a clear message instead of a blank screen or a crash.
- **Action:** Navigate to /journal/does-not-exist-12345
- **Point out:** A clear notice appears, with a link straight back to the Journal.
