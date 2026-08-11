# Project story so far

Tapeology is a research desk for reading a stock's tape and structure — never a trading system, and never a source of advice.

## How it has grown

Before this chapter, the desk already let someone watch a simulated ticker's buy-and-sell pressure live, load a real stock's chart with support-and-resistance walls, and run a daily screen across roughly a hundred large companies with a ranked briefing and forward-looking return numbers. This chapter, "The Playbook," teaches the desk to recognize classic intraday chart patterns from a well-known trading book and honestly report what happened afterward.

The opening rounds built the plumbing and shipped the first pattern (an opening-range breakout), then taught the desk to measure outcomes using its own trusted rules, adding a "Playbook Signals" section to the Desk page — pick a date, press Run Playbook, read the results. The next rounds taught four more patterns — Jump-Base Explosion, Drop-Base Implosion, Cup and Handle, and Capitulation (with a "recent climax" tag) — catching and fixing a mislabeled pattern and lagging summary text along the way. The following round finished the set with Range Trade and Double Top/Double Bottom, all nine patterns now sitting together on the page, with a real bug caught and fixed mid-round before it shipped.

This round added a new capability rather than a new pattern: a "Backscan" panel that checks, in bulk, which recorded trading days already have a saved pattern record and which are missing across a whole date range, then runs one resumable scan that fills in the gaps and reports what happened to each day. The desk's own real records were kept untouched while building it, confirmed by checking every file on disk. A handful of small technical follow-ups and owner judgment calls are carried forward, none of which change anything already on screen. Next up: pooling every recorded pattern into one results view, showing how each pattern actually performed against random chance.

## What it can do today

The product lets users watch a simulated ticker and see whether buyers or sellers are in control on a live price chart, load a real company's stock chart with support and resistance zones drawn on it, and run the desk's daily screen for a ranked briefing with forward-looking return numbers and past runs. It also lets users open the Desk page, pick a date, and see every one of the book's nine chart patterns found for that day, each measured against a random-chance baseline — and now lets them run one bulk scan across a date range to check and fill in those pattern records for many days at once.

_Last updated: 2026-08-11 after iteration 7._
