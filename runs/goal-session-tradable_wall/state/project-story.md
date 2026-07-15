# Project story so far

Tapeology is an app for studying how stocks trade — a simulated price tape, a trading journal, a strategy research lab, and a chart of a stock's real price structure, all in one place.

## How it has grown

An earlier chapter, "The Library," taught the app to fetch and permanently save real stock price history from Yahoo Finance — but exposed a problem: thousands of minor price levels buried the handful that actually matter.

This chapter, "The Tradable Wall," opened with a checkpoint confirming nothing had broken, then distilled thousands of levels into a short, ranked list of at most ten price zones, correctly ranking the real Apple $300–302 zone as the best resistance zone. A scan across 12 well-known stocks turned up over 800 real historical examples of price touching those zones, including the pinned Apple case showing the expected rejection and drop, and a first trial recording connected real market evidence to 15 of those touches (real, but not yet permanently filed away). The project then added a third way of simulating trades — following the map's short list of price zones instead of the long raw list — and built an honest report comparing all three approaches' actual performance, broken down by zone quality, market side, and touch reaction.

Most recently, before any of this reached a screen, the team ran a quiet quality-control pass on that research work: very recent price touches now carry an honest label when there hasn't been enough time yet to know how they turned out, and the multi-minute, 12-stock scan now runs once and is remembered afterward instead of repeating on every request — the same lookup that used to take minutes now comes back in under a second. Nothing looks different yet; this was groundwork so the next chapter's page loads quickly and honestly.

Nothing has broken along the way — the cockpit, journal, replay studies, profit scorecard, and Structure page all still work exactly as before. Next, the project will finally bring the price-zone map, example browser, and profit comparison onto the Structure page so people can see and use them.

## What it can do today

The product lets users watch simulated tape reading, keep a trading journal, run replay research studies, and check an honest profit scorecard. On the Structure page it shows a stock's support-and-resistance levels with a side-by-side strategy comparison, and fetches real historical prices from Yahoo Finance with one click. Behind the scenes, it also distills the level flood into the short list that matters, holds a growing library of 800+ real touch examples across a 12-stock panel, and can now honestly compare three trading approaches head-to-head — that comparison's plumbing is freshly cleaned up, fast, and ready, though none of this newer research work is shown on screen yet.

_Last updated: 2026-07-15 after iteration 5._
