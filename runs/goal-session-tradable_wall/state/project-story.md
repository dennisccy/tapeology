# Project story so far

Tapeology is an app for studying how stocks trade — a simulated price tape, a trading journal, a strategy research lab, and a chart of a stock's real price structure, all in one place.

## How it has grown

An earlier chapter, "The Library," taught the app to fetch and permanently save real stock price history from Yahoo Finance for free and compute real support-and-resistance levels — but exposed a problem: on a real stock, thousands of minor levels buried the handful that actually matter.

This chapter, "The Tradable Wall," set out to fix that. After an early checkpoint confirmed everything still worked, the project built its first real piece: a tool that distills that flood of levels into a short, ranked list of no more than ten price zones, scored by touch history, timeframe agreement, recency, and round-number significance — tested against the real, well-known Apple example, correctly picking the $300–302 zone as the single best resistance zone.

Most recently, the project put that tool to work at scale: it fetched fresh real price history for a wider panel of 12 well-known stocks — Apple, Microsoft, Nvidia, Tesla, Amazon, and others — and scanned all of them for every historical moment price touched one of those zones, labeling what happened next as a bounce away, a break through, or an inconclusive wobble, plus how far price moved over the following days. The scan turned up more than 800 real examples across all 12 stocks, and the Apple $300–302 example that motivated this chapter showed up exactly as expected: a rejection followed by a meaningful drop. This evidence library isn't on screen yet, but it gives the next steps real, measured history to build on rather than one hand-picked example.

Next, with the operator's trading-data credentials, the system will record real trade-by-trade activity around the best of these examples to see what actual buying and selling pressure looked like at each wall.

## What it can do today

The product lets users watch simulated tape reading, keep a trading journal, run replay research studies, and check an honest profit scorecard. On the Structure page it shows a stock's support-and-resistance levels with a side-by-side strategy comparison, and fetches and saves real historical stock prices from Yahoo Finance with one click. Behind the scenes, it now also distills that flood of levels into the short, ranked list that matters, and maintains a growing evidence library of more than 800 real historical examples of price reacting at those zones across a 12-stock panel — neither shown on screen yet.

_Last updated: 2026-07-14 after iteration 2._
