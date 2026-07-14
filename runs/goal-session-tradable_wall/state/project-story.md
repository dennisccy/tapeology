# Project story so far

Tapeology is an app for studying how stocks trade — a simulated price tape, a trading journal, a strategy research lab, and a chart of a stock's real price structure, all in one place.

## How it has grown

An earlier chapter, "The Library," taught the app to fetch and permanently save real stock price history from Yahoo Finance for free and compute real support-and-resistance levels on it — but exposed a problem: on a real stock the price-structure chart was overwhelming, burying the handful of levels a trader actually watches under thousands of minor ones.

This chapter, "The Tradable Wall," set out to fix that. Iteration 0 confirmed everything still worked and listed what was missing. Iteration 1 built the first real piece: a tool that distills that flood of levels into a short, ranked list of no more than ten price zones, scored by touch history, timeframe agreement, recency, and round-number significance. Tested against the real, well-known AAPL example, it correctly picked out the $300–302 zone as the single best resistance zone, after an early scoring bug that briefly buried it was caught and fixed before shipping.

Iteration 2 put that tool to work at scale, fetching fresh real price history for a wider panel of 12 well-known stocks — Apple, Microsoft, Nvidia, Tesla, Amazon, and others — and scanning all of them for every historical moment price touched one of those zones, labeling what happened next: a bounce away, a break through, or an inconclusive wobble. The scan found over 800 real examples across all 12 stocks, and the original $300–302 example that motivated this chapter showed up exactly as expected — a rejection followed by a meaningful drop over the following sessions. This evidence library isn't shown on any screen yet, but it gives the next steps real, measured history to build on rather than a single hand-picked example.

Next: with the operator's trading-data credentials, the system will record real trade-by-trade activity around the best of these examples, to show what actual buying and selling pressure looked like at each wall.

## What it can do today

The product lets users watch simulated tape reading, keep a trading journal, run replay research studies, and check an honest profit scorecard. On the Structure page it shows a stock's support-and-resistance levels with a side-by-side strategy comparison, and fetches and saves real historical stock prices from Yahoo Finance with one click. Behind the scenes, it now also distills that flood of levels into the short, ranked list that matters, and maintains a growing evidence library of over 800 real historical examples of price reacting at those zones across a 12-stock panel — though neither is shown on screen yet.

_Last updated: 2026-07-14 after iteration 2._
