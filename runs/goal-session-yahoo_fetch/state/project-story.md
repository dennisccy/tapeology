# Project story so far

Tapeology is an app for studying how stocks trade — a live simulated price tape, a trading journal, a research lab for testing trading strategies against history, and now a chart of a stock's real price structure, all in one place.

## How it has grown

Tapeology started as a way to watch simulated buying and selling pressure move a price tape in real time, then grew a trading journal, a research lab for testing trading ideas against history, and an honest profit scorecard that never overstates its results. A more recent chapter added a Structure page showing a stock's key support-and-resistance price levels and zones, with a side-by-side comparison of two trading strategies and a "Champion" badge for whichever one currently performs best on trustworthy, held-back data.

All of that has run so far on simulated or empty test data — the research lab has genuinely never had enough real market history to say anything meaningful. This new chapter, "The Library," exists to fix that for free: letting a person fetch real historical stock prices straight from Yahoo Finance, with no paid account or credentials needed, so the Structure page's levels and zones can finally be computed on real data instead of an empty placeholder.

This opening round did no building at all, on purpose. The team spent it confirming exactly what already works (everything from before, still intact) and honestly confirming that the real-data fetching doesn't exist yet. That gives the next round of work a clean, accurate starting line: fetching real prices from Yahoo Finance is the very next thing to be built, with support for multiple time windows, a fast local index for instant re-use, and a fetch button on the Structure page itself following right after.

## What it can do today

The product lets users watch live simulated tape reading, keep a trading journal, run replay research studies, check an honest profit scorecard, and view a stock's support-and-resistance levels and zones on the Structure page with a side-by-side strategy comparison and champion badge — all still running on simulated or empty test data, with real historical stock-price fetching not yet built.

_Last updated: 2026-07-09 after iteration 0._
