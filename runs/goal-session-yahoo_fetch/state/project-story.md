# Project story so far

Tapeology is an app for studying how stocks trade — a live simulated price tape, a trading journal, a research lab for testing trading strategies against history, and a chart of a stock's real price structure, all in one place.

## How it has grown

Tapeology started as a way to watch simulated buying and selling pressure move a price tape in real time, then grew a trading journal, a research lab for testing trading ideas against history, and an honest profit scorecard. A later chapter added a Structure page showing a stock's key support-and-resistance levels and zones, with a side-by-side comparison of two trading strategies and a "Champion" badge for whichever one currently performs best on trustworthy, held-back data.

All of that ran on simulated or empty test data — the research lab never had enough real market history to say anything meaningful. The current chapter, "The Library," fixes that for free: fetching real historical stock prices straight from Yahoo Finance, with no paid account or credentials needed, so the Structure page's levels and zones can finally run on real data instead of an empty placeholder.

The opening round did no building at all, on purpose — the team confirmed everything still worked and honestly confirmed real-data fetching didn't exist yet, giving the next round a clean starting line. The second round built the real thing, quietly: the app can now request a day-by-day price history for any stock symbol from Yahoo Finance, completely free, with no signup, and it saves that history permanently — never silently overwritten or duplicated, with built-in tamper detection. A real live fetch for a real stock symbol was tested and worked. Every existing part of the app was rechecked and confirmed to behave exactly as before, including a careful check that this new data source could never leak into the wrong place — the live simulated tape still only ever labels itself "Simulated," never the new source's name.

There's still no button to press — this round was entirely behind the scenes — but the foundation is now real, not simulated. Next: more time windows (weekly, hourly, and a derived 4-hour view) from Yahoo Finance, a fast local memory so a repeat lookup is instant, and finally a real "Fetch from Yahoo Finance" button on the Structure page itself.

## What it can do today

The product lets users watch live simulated tape reading, keep a trading journal, run replay research studies, check an honest profit scorecard, and view a stock's support-and-resistance levels and zones on the Structure page with a side-by-side strategy comparison and champion badge. Behind the scenes, it can now also pull real historical daily stock prices from Yahoo Finance for free and save them permanently — though that ability isn't reachable by clicking anything yet.

_Last updated: 2026-07-09 after iteration 1._
