# Project story so far

Tapeology is an app for studying how stocks trade — a simulated price tape, a trading journal, a strategy research lab, and a chart of a stock's real price structure, all in one place.

## How it has grown

An earlier chapter, "The Library," taught the app to fetch and permanently save real stock price history from Yahoo Finance — but exposed a problem: on a real stock, thousands of minor levels buried the handful that actually matter.

This chapter, "The Tradable Wall," opened with a checkpoint confirming nothing had broken, then distilled that flood of levels into a short, ranked list of no more than ten price zones — correctly picking the real Apple $300–302 zone as the single best resistance zone. Next, the project scanned a panel of 12 well-known stocks for every historical moment price touched one of those zones, turning up more than 800 real examples, including the pinned Apple case showing the expected rejection and drop. The project then connected real market evidence to those zones, so a recorded price-touch moment can replay what buyers and sellers were actually doing right at the touch, and ran a first trial recording across 15 examples spanning 12 stocks — though that batch landed in a temporary holding area rather than the permanent library, so this piece is real but not fully finished.

Most recently, the project added a third way of simulating trades, following the same short list of price zones the map shows rather than the long raw list, and built an honest report comparing how well each of the three approaches would actually have done — broken down by zone quality, market side, and touch reaction, with every number carrying its sample size and a "simulated, not real" label. None of this is visible on a page yet; it's ready for the next chapter to display.

Nothing has broken along the way — the cockpit, journal, replay studies, profit scorecard, and Structure page all still work exactly as before. Next, the project will bring the price-zone map, example browser, and this new profit comparison onto the Structure page so they can actually be seen and used.

## What it can do today

The product lets users watch simulated tape reading, keep a trading journal, run replay research studies, and check an honest profit scorecard. On the Structure page it shows a stock's support-and-resistance levels with a side-by-side strategy comparison, and fetches real historical prices from Yahoo Finance with one click. Behind the scenes, it also distills the level flood into the short list that matters, holds a growing library of 800+ real examples of price reacting at those zones across a 12-stock panel, can pull up real tape evidence at a recorded touch, and can now honestly compare three trading approaches head-to-head — none of this newer research work is shown on screen yet.

_Last updated: 2026-07-14 after iteration 4._
