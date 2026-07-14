# Project story so far

Tapeology is an app for studying how stocks trade — a simulated price tape, a trading journal, a strategy research lab, and a chart of a stock's real price structure, all in one place.

## How it has grown

The last chapter, "The Library," taught the app to fetch and permanently save real stock price history from Yahoo Finance for free, and to compute real support-and-resistance levels and zones on that real data. That chapter finished with every planned piece built, shown working in the browser, and signed off.

It also exposed the next honest problem: on a real stock, the price-structure chart is overwhelming — one real day showed 1,800 individual price levels and 212 clustered zones, all drawn at once, while the handful of levels a trader actually watched (a well-known zone around $300–302 that rejected the price several times before a sharp drop) got buried in the noise. This new chapter, "The Tradable Wall," sets out to fix that: turn the flood of levels into a short, ranked list of the zones that matter, find historical examples of price reacting at those zones across a panel of stocks, record real market tape at the best examples once the operator supplies trading-data credentials, and publish an honest report on whether trading at those zones would actually have made money.

This iteration was a check-up, not new construction: every one of the seven building blocks for this chapter was tested against today's app, confirming everything from "The Library" and earlier still works exactly as before, and getting an honest read on what's built versus missing. Result: the safety check passed with nothing broken, but none of "The Tradable Wall"'s own new pieces exist yet — no distilled level map, no case library, no real tape recordings, no profit report, and no updated Structure page or cockpit overlay. Next up: building the tool that turns the flood of price levels into that short, ranked list.

## What it can do today

The product lets users watch simulated tape reading, keep a trading journal, run replay research studies, and check an honest profit scorecard. On the Structure page it shows a stock's support-and-resistance levels and zones with a side-by-side strategy comparison, and fetches and permanently saves real historical stock prices from Yahoo Finance with one click, showing a "Yahoo Finance" source label. The next chapter's own features — a short list of tradable price zones, a library of historical examples, real recorded market tape, and an honest profit report — are not built yet.

_Last updated: 2026-07-14 after iteration 0._
