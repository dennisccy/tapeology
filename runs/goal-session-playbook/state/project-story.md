# Project story so far

Tapeology is a research desk for reading a stock's tape and structure — never a trading system, and never a source of advice.

## How it has grown

Before this chapter began, the desk already let someone watch a simulated ticker's buy-and-sell pressure live, load a real stock's chart with support-and-resistance walls drawn on it, and run a daily screen across roughly a hundred large companies with a ranked briefing and forward-looking return numbers.

This chapter, nicknamed "The Playbook," teaches the desk to recognize a handful of classic intraday chart patterns from a well-known trading book — a stock breaking out of its opening range, or capitulating into a sharp reversal — records every time one shows up, and honestly reports what happened afterward, with no predictions and no advice attached.

The first round of work did no building at all, on purpose — a checkup confirming everything already shipped still worked, and that none of the ten new capabilities this chapter promises had started yet.

The second round built the very first piece: the desk now watches the opening minutes of a trading session for each stock and permanently records every time price later breaks cleanly out of that early range, with an honest note whenever there isn't enough history on file to say. A double-check step caught and fixed a subtle honesty problem the same day it appeared — a session missing its first few minutes of data was briefly getting a made-up "opening range" that looked exactly like a real one; it now gets an honest "can't tell" instead, permanently guarded by a new check. Nothing on the existing screens changed, and this new pattern-spotter isn't on any screen yet; only a technical back-door can ask the desk what it found. That opening-range detector is the one new piece confirmed working so far — the next round teaches the desk to measure what price did afterward.

## What it can do today

The product lets users watch a simulated ticker and see whether buyers or sellers are in control on a live price chart, load a real company's stock chart with support and resistance zones drawn on it, and run the desk's daily screen for a ranked briefing with forward-looking return numbers and past runs. Behind the scenes, the desk can now also spot and permanently record a stock's "opening range breakout," though nobody can trigger it from a screen yet — that, and measuring what price does afterward, both arrive in later steps.

_Last updated: 2026-08-10 after iteration 1._
