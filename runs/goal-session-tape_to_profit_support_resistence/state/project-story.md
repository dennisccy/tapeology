# Project story so far

Tapeology watches a stock's live trade-by-trade order flow and tells you, moment to moment, whether buyers or sellers are in control; an earlier chapter already taught it to honestly measure whether that read turns into profit. This new chapter asks a sharper question — does the read get better when it's anchored to real price structure, support and resistance, instead of read on its own?

## How it has grown

This chapter opened with a check-up rather than a build. Before any new work began, the team confirmed that everything from before — the live tape reading, the trading journal, replay studies, the honest profit-measuring engine, and its scorecard — still worked exactly as it always had. That check came back clean: nothing broke, and nothing new is visible yet for this chapter.

Alongside the check-up, the team mapped out the six capabilities this chapter needs to add, in order: remembering historical price data at multiple time scales, spotting meaningful price levels where a stock tends to turn, grading those levels by how strongly they line up across time scales, teaching the strategy to act on a level only when the live tape confirms it, sizing each simulated trade and its risk to match how strong the level is, and finally measuring the new approach honestly against the existing strategy on data it has never seen. None of those six are built yet — this round only marked where the starting line is.

## What it can do today

The product lets users type in a stock ticker and watch live trade-by-trade action to see who's in control, journal trading ideas, run replay studies against past data, store historical market data, backtest a strategy into an honest profit-or-loss report beside a random-guessing comparison, view that scorecard on a Performance page, and let AI assistants read all of it directly — all delivered in an earlier chapter and confirmed still intact this round. None of this chapter's new price-structure capabilities are ready for users yet.

_Last updated: 2026-07-06 after iteration 0._
