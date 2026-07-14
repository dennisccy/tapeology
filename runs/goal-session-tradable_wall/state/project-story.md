# Project story so far

Tapeology is an app for studying how stocks trade — a simulated price tape, a trading journal, a strategy research lab, and a chart of a stock's real price structure, all in one place.

## How it has grown

The last chapter, "The Library," taught the app to fetch and permanently save real stock price history from Yahoo Finance for free, and to compute real support-and-resistance levels on that data. It also exposed a problem: on a real stock the price-structure chart is overwhelming — one day showed 1,800 individual price levels and 212 zones, burying the handful of levels a trader actually watches (the well-known $300–302 zone that rejected price several times before a sharp drop).

This new chapter, "The Tradable Wall," set out to fix that. It opened with a check-up (iteration 0) confirming everything built so far still worked and honestly cataloguing what was missing. Iteration 1 then built the first real piece: a behind-the-scenes tool that distills a stock's flood of price levels into a short, ranked list of no more than ten price zones, each scored by how many times it's been touched, how many chart timeframes agree on it, how recent it is, and whether it sits on a round, psychologically important price. Tested against the real AAPL example, it correctly picked out the exact $300–302 zone traders actually watched as the single best resistance zone — after an early version of the scoring briefly buried it under a flood of minor, short-term touches and had to be corrected before shipping.

This tool isn't on screen yet — for now it only answers direct questions asked of the system. Next, the plan is to scan a wider panel of stocks for more real historical examples of price reacting at these zones, then later put the distilled map on the Structure page and the live trading chart.

## What it can do today

The product lets users watch simulated tape reading, keep a trading journal, run replay research studies, and check an honest profit scorecard. On the Structure page it shows a stock's support-and-resistance levels and zones with a side-by-side strategy comparison, and it fetches and permanently saves real historical stock prices from Yahoo Finance with one click. Behind the scenes, it can now also distill a stock's flood of price levels into a short, ranked list of the zones that actually matter — though that list isn't shown on any screen yet.

_Last updated: 2026-07-14 after iteration 1._
