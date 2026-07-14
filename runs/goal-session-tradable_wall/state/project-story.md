# Project story so far

Tapeology is an app for studying how stocks trade — a simulated price tape, a trading journal, a strategy research lab, and a chart of a stock's real price structure, all in one place.

## How it has grown

An earlier chapter, "The Library," taught the app to fetch and permanently save real stock price history from Yahoo Finance and compute real support-and-resistance levels — but exposed a problem: on a real stock, thousands of minor levels buried the handful that actually matter.

This chapter, "The Tradable Wall," began with a checkpoint confirming everything still worked, then built a tool that distills that flood of levels into a short, ranked list of no more than ten price zones — scored by touch history, timeframe agreement, recency, and round-number significance — correctly picking the real Apple $300–302 zone as the single best resistance zone.

Next, the project scanned a panel of 12 well-known stocks for every historical moment price touched one of those zones and labeled what happened next, turning up more than 800 real examples — including the pinned Apple case, which showed the expected rejection and drop.

Most recently, the project connected real market evidence to those zones: it can now look up whether a specific price-touch moment was ever captured from the real market feed and replay what buyers and sellers were doing right around that touch. With the operator's trading-data credentials now available, it ran a real trial recording across 15 examples spanning 12 different stocks — including the pinned Apple case — proving the replay works on real activity, though that recording currently sits in a temporary holding area rather than the permanent library.

Nothing has broken along the way — the cockpit, journal, replay studies, profit scorecard, and Structure page all still work exactly as before. Next, the project will compare which trading approach actually would have profited from these walls, building an honest scorecard on the recorded evidence.

## What it can do today

The product lets users watch simulated tape reading, keep a trading journal, run replay research studies, and check an honest profit scorecard. On the Structure page it shows a stock's support-and-resistance levels with a side-by-side strategy comparison, and fetches real historical stock prices from Yahoo Finance with one click. Behind the scenes, it also distills that flood of levels into the short list that matters, maintains a growing library of more than 800 real historical examples of price reacting at those zones across a 12-stock panel, and can now pull up real tape evidence for a recorded price-touch event — none of this is shown on screen yet.

_Last updated: 2026-07-14 after iteration 3._
