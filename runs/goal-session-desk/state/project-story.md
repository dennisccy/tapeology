# Project story so far

Tapeology is a research tool for reading a stock's price action right now and mapping its key price levels — an honest study instrument, never a trading system.

## How it has grown

Before this chapter, the product was a two-page instrument — a live Cockpit for price action and a Structure page mapping support and resistance. This chapter, "The Desk," added a third page — a daily ~100-stock screen — in stages: fetching the watchlist, filling in price history, ranking by closeness to a key level, shipping the ranked page with "Run Screen"/"Top-up" buttons, fixing a bad-price bug along the way, then proving it with every required photograph.

Later rounds gave the Desk a memory — clicking a past scan shows what was recorded, and any row jumps into the Structure chart already loaded — and let Claude read the Desk's data directly. The chapter then stalled, waiting on the owner's written word on an earlier data-repair fix to two protected parts of the product.

That answer came: the owner wrote permission directly into the plan, naming exactly which files the repair could touch. The team proved nothing else had changed by rebuilding the product as it stood before this chapter and comparing answers side by side, then took the last missing photograph — the main page in "Historical" mode with a real chart and support/resistance lines drawn — closing all seven original promises with real, opened proof.

With those seven promises proven, a routine review found one more honest gap: a ranked stock's distance-to-wall could be measured from a same-day price or an eleven-day-old one, with no way to tell which. This round closed that gap — every ranked row now names the exact date its measurement came from and how old that reading is, both at a glance and in full detail on hover, with an honest "not recorded" note on older, untouched scans. The numbers check out against an independent re-check. The one loose end is a photograph, not a defect: the plan wanted a same-day-old reading beside an eleven-day-old one in one picture; the picture taken instead shows three days beside fourteen — legible "fresh vs. stale" proof, just not the exact numbers asked for. One more short, code-free round to retake that photo is all that's left.

## What it can do today

The product lets users run a simulated tape-reading session that settles into a read like "Buyer Control," with live moving price bars; open a Structure page to see a stock's support and resistance levels on a real chart, with case studies of past price touches; and open a Desk page that screens about 100 stocks, refresh price history, run a fresh ranking, and see the result — including how old each row's price reading is — with an honest note on anything unrankable. Users can revisit any past scan and jump from any row into the Structure chart for that stock and date. A connected Claude conversation can read the Desk's data directly too.

_Last updated: 2026-07-27 after iteration 9._
