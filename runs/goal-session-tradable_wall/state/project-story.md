# Project story so far

Tapeology is an app for studying how stocks trade — a simulated price tape, a trading journal, a strategy research lab, and a chart of a stock's real price structure, all in one place.

## How it has grown

An earlier chapter, "The Library," taught the app to fetch and permanently save real stock price history from Yahoo Finance and compute real support-and-resistance levels — but exposed a problem: on a real stock, thousands of minor levels buried the handful that actually matter.

This chapter, "The Tradable Wall," began with a checkpoint confirming everything still worked, then built a tool that distills that flood of levels into a short, ranked list of no more than ten price zones — scored by touch history, timeframe agreement, recency, and round-number significance — correctly picking the real Apple $300–302 zone as the single best resistance zone.

Next, the project scanned a panel of 12 well-known stocks for every historical moment price touched one of those zones and labeled what happened next, turning up more than 800 real examples — including the pinned Apple case, which showed the expected rejection and drop.

Most recently, the project connected real market evidence to those zones: opening a recorded price-touch moment can now replay what buyers and sellers were actually doing right around that touch, taken from the real market feed rather than invented. With the operator's trading-data access now available, a real trial recording ran across 15 examples spanning 12 different stocks — including the pinned Apple case — confirming the replay genuinely works on real activity, though the trial currently sits in a temporary holding area rather than the permanent library, so this piece is real progress but not yet fully finished.

Nothing has broken along the way — the cockpit, journal, replay studies, profit scorecard, and Structure page all still work exactly as before. Next, the project will compare which trading approach would actually have profited from these walls, using the recorded evidence so far.

## What it can do today

The product lets users watch simulated tape reading, keep a trading journal, run replay research studies, and check an honest profit scorecard. On the Structure page it shows a stock's support-and-resistance levels with a side-by-side strategy comparison, and fetches real historical stock prices from Yahoo Finance with one click. Behind the scenes, it also distills the level flood into the short list that matters, maintains a growing library of more than 800 real historical examples of price reacting at those zones across a 12-stock panel, and can look up real tape evidence for a recorded price-touch event — none of this is shown on screen yet.

_Last updated: 2026-07-14 after iteration 3._
