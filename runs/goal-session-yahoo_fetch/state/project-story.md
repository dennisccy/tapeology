# Project story so far

Tapeology is an app for studying how stocks trade — a live simulated price tape, a trading journal, a research lab for testing trading strategies against history, and a chart of a stock's real price structure, all in one place.

## How it has grown

It began as a way to watch simulated buying and selling pressure move a price tape, then grew a trading journal, a strategy-testing research lab, an honest profit scorecard, and a Structure page showing support-and-resistance levels and zones with a side-by-side strategy comparison — all running on simulated or empty test data.

The current chapter, "The Library," is fixing that for free. After an honest checkpoint confirmed real price-fetching didn't exist yet, the app gained the ability to pull real daily price history for any stock from Yahoo Finance — free, no signup — and save it permanently with tamper detection. That then widened into the full set the plan intended: weekly, hourly, 5-minute, and 1-minute history, plus a 4-hour view the app builds itself from real hourly prices, never invented — and the app began explaining clearly why a request can't be filled instead of one vague error for everything.

This round taught the app not to repeat itself. Asking for a stock's history a second time no longer goes back out to Yahoo Finance at all — it's recognized instantly and handed back from what was already saved, tested live at 19 milliseconds. Saved history can now also be searched by symbol and time window instead of only ever listing everything at once, and if the app's internal lookup memory were ever lost, it rebuilds itself perfectly from the permanent data already on file, losing or inventing nothing.

There's still no button to press for any of this — that arrives later. Next: teaching the app to compute real support-and-resistance levels on this real data, and then a genuine "Fetch from Yahoo Finance" button on the Structure page, so a person can trigger all of this by clicking rather than only through the programming interface.

## What it can do today

The product lets users watch live simulated tape reading, keep a trading journal, run replay research studies, check an honest profit scorecard, and view a stock's support-and-resistance levels and zones on the Structure page with a side-by-side strategy comparison and champion badge. Behind the scenes, it can now also pull and permanently save real historical stock prices from Yahoo Finance across every standard time window, avoid re-fetching data it already has, and let saved data be searched by symbol and timeframe — though none of this is reachable by clicking yet.

_Last updated: 2026-07-09 after iteration 3._
