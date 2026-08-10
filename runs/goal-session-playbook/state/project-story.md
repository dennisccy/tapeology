# Project story so far

Tapeology is a research desk for reading a stock's tape and structure — never a trading system, and never a source of advice.

## How it has grown

Before this chapter began, the desk already let someone watch a simulated ticker's buy-and-sell pressure live, load a real stock's chart with support-and-resistance walls drawn on it, and run a daily screen across roughly a hundred large companies with a ranked briefing and forward-looking return numbers. This chapter, nicknamed "The Playbook," teaches the desk to recognize classic intraday chart patterns from a well-known trading book — like a stock breaking out of its opening range — record every time one shows up, and honestly report what happened afterward, with no predictions or advice attached. The first round of work did no building at all, on purpose: a checkup that confirmed everything already shipped still worked, and that none of the new capabilities this chapter promises had started yet.

The second round built the first real piece: the desk began watching the opening minutes of each trading session and permanently recording every time price later broke cleanly out of that early range, with an honest note whenever there wasn't enough history on file to say. A same-day double-check caught and fixed a subtle honesty problem: a session missing its first few minutes of data was briefly getting a made-up "opening range" that looked exactly like a real one; it now honestly says it can't tell instead.

The third round taught the desk to measure what actually happened after each of those breakouts, using the exact same measuring rules it already trusts elsewhere for forward returns, plus a note on whether the pattern later got invalidated. Nothing changed yet on the screens a person actually clicks through — this spotting-and-measuring work was still only reachable through a technical back door.

The fourth round put it in front of the person using the product for the first time. The Desk page now has a new "Playbook Signals" section: pick a date (or leave it blank for the newest day on file), press Run Playbook, and read a table of the patterns the desk found, what happened to price afterward next to a random-chance comparison, and honest messages for "nothing computed yet," "already running," and days the market was closed. Every screen that already worked — Cockpit, Structure, and the rest of Desk — was checked again in the same pass and still works exactly as before. One small cleanup item was left behind: a test record briefly written into the real data folder during checking still needs deleting. Next, the desk plans to learn three more chart patterns — a continuation breakout, a sharp reversal, and a cup-and-handle shape — built more carefully, with a fuller safety review this time.

## What it can do today

The product lets users watch a simulated ticker and see whether buyers or sellers are in control on a live price chart, load a real company's stock chart with support and resistance zones drawn on it, and run the desk's daily screen for a ranked briefing with forward-looking return numbers and past runs. It also now lets users open the Desk page, pick a date, and see the opening-range breakout patterns the desk found for that day, each one measured for what happened afterward against a random-chance baseline.

_Last updated: 2026-08-10 after iteration 3._
