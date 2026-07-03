# Project story so far

Tapeology watches a stock's live trade-by-trade order flow and tells you, moment to moment, whether buyers or sellers are in control — and this new chapter is teaching it to measure whether that read would actually have made money.

## How it has grown

This chapter, the profit-research era, opened with a check-up confirming the working product underneath — the live tape-reading cockpit, journal, and replay-studies tool — still worked, before any profit-measuring pieces existed. The next round added a direct connection that other tools and AI assistants can use to read the product's data, and made the navigation menu build itself automatically instead of being hand-maintained. After that came a permanent library for historical market data, each slice checked for tampering on every read and locked forever as "practice" or "final exam" data the moment it's saved.

Then came the payoff those saved slices were waiting for: an engine that runs a defined trading strategy against stored historical data and reports, honestly, whether the simulated trades would have won or lost money — trade count, win count, overall result, and a random-guessing comparison shown alongside every number so nothing can be dressed up to look better than it really was. Running the exact same test twice was proven to give back the exact same result.

This round gave the product its permanent memory: a tamper-proof scoreboard that keeps one honest row for every trading-strategy improvement, forever, with no way to edit or erase an entry once it's written. Its very first entry — the founding baseline, measuring the current strategy on both the practice and final-exam data — is now live: on today's small starter data the strategy lost a little in practice and gained a little on the final exam, both results honestly flagged as too small a sample to mean much yet. That scoreboard reads identically no matter how you ask for it — through the app's data connection, in a plain saved report, or via an AI assistant — and everything proven in earlier rounds was reconfirmed still working. There's still no dedicated screen to look at it on; that arrives next, when the product gets its fourth page, Performance, to finally put this scoreboard on display alongside a summary of the current best strategy.

## What it can do today

The product lets users type in a stock ticker (or use the built-in demo tickers) and watch Tapeology read live trade-by-trade action, classifying whether buyers or sellers are in control. Users can write trading theses into a journal, revisit them later, and run replay studies against past market data. It can permanently store and faithfully replay slices of historical market data, and run a defined trading strategy against that data to produce an honest profit-or-loss report, always shown alongside a fair random-guessing comparison. Under the hood, it also keeps a permanent, append-only scoreboard of every strategy improvement's result, exposes everything to AI assistants through a direct read-only connection, and its navigation builds itself automatically.

_Last updated: 2026-07-03 after iteration 4._
