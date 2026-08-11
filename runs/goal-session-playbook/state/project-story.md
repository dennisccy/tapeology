# Project story so far

Tapeology is a research desk for reading a stock's tape and structure — never a trading system, and never a source of advice.

## How it has grown

Before this chapter, the desk already let someone watch a simulated ticker's buy-and-sell pressure live, load a real stock's chart with support-and-resistance walls, and run a daily screen across roughly a hundred large companies with a ranked briefing and forward-looking return numbers. This chapter, "The Playbook," teaches the desk to recognize classic intraday chart patterns from a well-known trading book and honestly report what happened afterward.

The opening rounds built the plumbing and shipped the first pattern (an opening-range breakout), then taught the desk to measure outcomes using its own trusted rules, adding a "Playbook Signals" section to the Desk page — pick a date, press Run Playbook, read the results. The next rounds taught four more patterns — jump-base and drop-base breakouts, cup-and-handle, and capitulation with a "recent climax" tag — catching and fixing a mislabeled pattern and some stale summary text along the way. A later round finished the set with range trades and double-top/double-bottom reversals, all nine patterns now sitting together on the page, and added a "Backscan" panel that checks, in bulk, which recorded days already have a saved pattern record and fills in the gaps in one resumable pass — the desk's own real records were kept untouched throughout, confirmed by checking every file on disk.

This latest round pooled all of that recorded history into one place: a new "Playbook Evidence" panel at the bottom of the Desk page now shows, per pattern and direction, how many times each one fired and what happened to price afterward, compared against a random-chance baseline, with thin, not-yet-trustworthy rows honestly marked rather than hidden. A small date-typing bug in the Backscan panel was also fixed so a half-typed date never triggers a raw error. The bigger story of this round happened behind the scenes: the automated checking process that verifies the product was itself caught briefly reading and writing the operator's real trading records instead of a safe practice copy, and a proper safety mechanism — not just a promise — was built to close that gap for good, proven by checking that all 9,841 protected files were untouched by the end of the round. A misleading sentence on the new evidence table, which claimed it compared against more data than it actually did, was also caught and corrected before shipping.

Two owner decisions about pattern-detection edge cases are still waiting for a yes/no answer and are deliberately left alone until the owner rules on them. Next up: giving outside programs two new ways to read the playbook and its evidence table, then a full walkthrough of the whole product in a real browser to prove nothing else changed by accident.

## What it can do today

The product lets users watch a simulated ticker and see whether buyers or sellers are in control on a live price chart, load a real company's stock chart with support and resistance zones drawn on it, and run the desk's daily screen for a ranked briefing with forward-looking return numbers and past runs. It also lets users open the Desk page, pick a date, and see every one of the book's nine chart patterns found for that day, each measured against a random-chance baseline; run one bulk scan across a date range to check and fill in those pattern records for many days at once; and now scroll further down to see all of that recorded history pooled into one evidence table, showing how each pattern has actually performed, with thin data honestly flagged rather than hidden.

_Last updated: 2026-08-11 after iteration 8._
