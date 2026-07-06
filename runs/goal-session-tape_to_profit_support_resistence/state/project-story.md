# Project story so far

Tapeology watches a stock's live trade-by-trade order flow to judge whether buyers or sellers are in control, and it already has an honest engine for measuring whether that read actually turns into profit — this newest chapter is teaching it to anchor that read to real price structure, support and resistance, instead of reading the tape in a vacuum.

## How it has grown

Earlier chapters built Tapeology's live tape reader, journal, replay studies, and an honest profit-measuring engine that proved the very first trading strategy loses money on real data — now frozen as the proven foundation. This chapter opened with a check-up confirming everything still worked, then mapped six new capabilities in dependency order: multi-timeframe price history, support/resistance levels, confluence grading, tape-confirmed entries, level-based sizing, and an honest head-to-head measurement against the existing strategy.

The first of those six landed next: Tapeology learned to fetch, permanently save, and faithfully read back a stock's real multi-year price history at several time scales — hourly, daily, weekly, monthly — complete with tamper detection and an honest message when no data connection is configured.

Now the second capability has landed too: Tapeology can look at that saved history and pinpoint the real support and resistance levels — prices where the market has previously turned, or a prior day, week, or month's high, low, or close — each one scored for strength from one documented settings file, never a guess. The team proved directly that asking about a moment in time never lets a later price bar sneak into the answer, that the same question always gives the identical answer down to the byte, and that asking about a symbol with no history gets an honest "nothing here" rather than a faked result. Next: grouping these individual levels into graded confluence zones — clusters worth more attention than any single level alone — that a future strategy can react to.

## What it can do today

The product lets users type in a stock ticker and watch live trade-by-trade action to see who's in control, journal trading ideas, run replay studies against past data, backtest a strategy into an honest profit-or-loss report beside a random-guessing comparison, view that scorecard on a Performance page, and let AI assistants read all of it directly. The price-history and price-level work from the last two chapters is not yet visible in the app — it is groundwork for a future visible feature.

_Last updated: 2026-07-06 after iteration 2._
