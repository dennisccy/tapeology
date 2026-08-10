# Project story so far

Tapeology is a research desk for reading a stock's tape and structure — never a trading system, and never a source of advice.

## How it has grown

Before this chapter began, the desk already let someone watch a simulated ticker's buy-and-sell pressure live, load a real stock's chart with support-and-resistance walls drawn on it, and run a daily screen across roughly a hundred large companies with a ranked briefing and forward-looking return numbers. This chapter, nicknamed "The Playbook," teaches the desk to recognize a handful of classic intraday chart patterns from a well-known trading book — a stock breaking out of its opening range, or capitulating into a sharp reversal — records every time one shows up, and honestly reports what happened afterward, with no predictions and no advice attached. The first round of work did no building at all, on purpose — a checkup confirming everything already shipped still worked, and that none of the ten new capabilities this chapter promises had started yet.

The second round built the very first piece: the desk began watching the opening minutes of a trading session for each stock and permanently recording every time price later broke cleanly out of that early range, with an honest note whenever there wasn't enough history on file to say. A double-check step caught and fixed a subtle honesty problem the same day it appeared — a session missing its first few minutes of data was briefly getting a made-up "opening range" that looked exactly like a real one; it now gets an honest "can't tell" instead, permanently guarded by a new check.

The third round taught the desk to measure what actually happened after each of those breakouts — using the exact same measuring rules it already trusts elsewhere for forward returns, plus an honest note about whether price later crossed the danger line that would call the pattern off. A separate check also re-ran the whole product top to bottom and confirmed nothing that already worked had broken. Nothing changed yet on the screens a person actually clicks through — Cockpit, Structure, and Desk all still look and behave exactly the same — this new spotting-and-measuring work is only reachable through a technical back door so far. The next round aims to put it on the Desk page itself, with a button an operator can actually press.

## What it can do today

The product lets users watch a simulated ticker and see whether buyers or sellers are in control on a live price chart, load a real company's stock chart with support and resistance zones drawn on it, and run the desk's daily screen for a ranked briefing with forward-looking return numbers and past runs. Behind the scenes, the desk can now also spot a stock's opening-range breakouts and measure what price did afterward for each one, though nobody can trigger or see any of that from a screen yet.

_Last updated: 2026-08-10 after iteration 2._
