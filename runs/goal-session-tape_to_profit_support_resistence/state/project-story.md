# Project story so far

Tapeology watches a stock's live trade-by-trade order flow to tell you whether buyers or sellers are in control, and now has an honest engine for measuring whether that read actually turns into profit — this newest chapter is teaching it to anchor that read to real price structure, support and resistance.

## How it has grown

Earlier chapters built Tapeology's live tape reader, its trading journal, replay studies, and an honest profit-measuring engine that proved the very first trading strategy actually loses money on real data — all of that is now frozen as the proven foundation this new chapter builds on top of.

This chapter opened with a check-up rather than a build: before adding anything, the team confirmed every earlier capability still worked exactly as before (it did), then mapped out the six new capabilities this chapter needs, in order — remembering historical price data at multiple time scales, spotting meaningful price levels where a stock tends to turn, grading how strongly those levels line up across time scales, teaching the strategy to act on a level only when the live tape confirms it, sizing each trade to match a level's strength, and finally measuring the new approach honestly against the existing strategy.

The first of those six is now built. Tapeology can fetch a real, multi-year history of a stock's price bars — daily, weekly, monthly, hourly, and more — save it permanently, and read it back exactly as recorded, with built-in tamper detection and an honest "please connect your data account" message if no data connection is configured. It was checked by three independent reviewers, each of whom re-ran the tests themselves and confirmed it works completely, breaks nothing that came before, and never invents fake price data. Next up: teaching Tapeology to spot the actual support-and-resistance price levels hiding in that stored history.

## What it can do today

The product lets users type in a stock ticker and watch live trade-by-trade action to see who's in control, journal trading ideas, run replay studies against past data, backtest a strategy into an honest profit-or-loss report beside a random-guessing comparison, view that scorecard on a Performance page, and let AI assistants read all of it directly. This chapter's new price-structure work is not yet visible in the app.

_Last updated: 2026-07-06 after iteration 1._
