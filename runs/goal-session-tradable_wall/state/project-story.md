# Project story so far

Tapeology is an app for studying how stocks trade — a simulated price tape, a trading journal, a strategy research lab, and a chart of a stock's real price structure, all in one place.

## How it has grown

An earlier chapter, "The Library," taught the app to fetch and permanently save real stock price history from Yahoo Finance — but exposed a problem: thousands of minor price levels buried the handful that actually matter.

This chapter, "The Tradable Wall," set out to fix that. The team distilled thousands of levels into a short, ranked list of at most ten price zones, correctly ranking the real Apple $300–302 zone as the best resistance zone, then scanned 12 well-known stocks for over 800 real historical examples of price touching those zones — including the pinned Apple case, which showed the expected rejection and drop. A third way of simulating trades followed (using the short list instead of the long raw one), plus an honest report comparing all three approaches' real performance. A quality pass then made very recent touches carry an honest "too soon to know" label, and turned a minutes-long 12-stock scan into a sub-second lookup.

None of that had reached a screen — until now. This step finally brought it all onto the Structure page: loading a stock now leads with the short, ranked list of price zones instead of the old wall of a thousand-plus lines (the detailed view is still one click away). A new browsable history lets people click through real examples of price hitting those zones and see what happened, including a moment-by-moment replay where one was recorded. A profit-comparison report sits alongside it — honestly empty for now, since no real trade evidence exists yet for these stocks, but ready to fill in once it does.

Nothing has broken along the way — the cockpit, journal, replay studies, profit scorecard, and every earlier Structure page feature still work exactly as before. Next: bring this same short-listed map to the live cockpit chart, with a small descriptive note when price sits at a meaningful level.

## What it can do today

The product lets users watch simulated tape reading, keep a trading journal, run replay research studies, and check an honest profit scorecard. On the Structure page, loading a stock now leads with a short, ranked list of its handful of truly important price levels, with the full detailed view one click away. Users can browse over 800 real examples of price touching those levels, drill into what happened at each one, and view a report comparing three trading approaches' real performance — currently honest and empty until more real trade data is recorded. The app still fetches fresh real price history from Yahoo Finance with one click.

_Last updated: 2026-07-15 after iteration 6._
