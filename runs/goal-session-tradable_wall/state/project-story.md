# Project story so far

Tapeology is an app for studying how stocks trade — a simulated price tape, a trading journal, a strategy research lab, and a chart of a stock's real price structure, all in one place.

## How it has grown

Earlier chapters built the simulated tape reader, the trading journal, and a replay-based research lab; a more recent chapter, "The Library," taught the app to fetch and permanently save real stock price history from Yahoo Finance — but that exposed a new problem: thousands of minor price levels buried the handful that actually mattered.

This chapter, "The Tradable Wall," set out to fix that. Step by step, the team distilled thousands of levels into a short, ranked list of at most ten price zones per stock — correctly ranking the real Apple $300–302 zone as the best resistance zone — then scanned 12 well-known stocks for over 800 real historical examples of price touching those zones, including the pinned Apple case, which showed the expected rejection and drop. A third way of simulating trades followed, built specifically around these zones, alongside an honest report comparing all three approaches' real performance. A quality pass then made very recent touches carry an honest "too soon to know" label instead of a premature verdict, and turned a minutes-long scan across all 12 stocks into a lookup that comes back in well under a second.

This latest step finally brought all of that onto a screen. Loading a stock on the Structure page now leads with the short, ranked list of price zones instead of the old wall of a thousand-plus lines — the detailed original view is still there, just one click away behind a "show raw levels" switch. A new browsable history lets people click through those 800-plus real examples of price hitting a zone and see exactly what happened, including a moment-by-moment tape replay for the cases where one was recorded. Sitting beside it, a profit-comparison report is fully wired up — honestly empty for now, since no real trade evidence has been recorded yet for these stocks, but ready to fill in the moment it is.

Nothing has broken along the way — the cockpit, journal, replay studies, profit scorecard, and every earlier Structure page feature still work exactly as before, just repositioned slightly lower on the page. Next: bring this same short list of important price zones to the live cockpit chart, with a small descriptive note appearing whenever the price is sitting at one of them.

## What it can do today

The product lets users watch simulated tape reading, keep a trading journal, run replay research studies, and check an honest profit scorecard. On the Structure page, users can fetch fresh real price history from Yahoo Finance with one click, then see a short, ranked list of a stock's handful of truly important price zones by default (the full detailed view is one click away). Users can browse more than 800 real historical examples of price touching those zones, drill into what happened at each one, and view a profit-comparison report across three trading approaches — currently honest and empty until more real trade data is recorded.

_Last updated: 2026-07-15 after iteration 6._
