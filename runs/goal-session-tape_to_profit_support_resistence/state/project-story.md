# Project story so far

Tapeology watches a stock's live trade-by-trade order flow to judge whether buyers or sellers are in control, and it already has an honest engine for measuring whether that read actually turns into profit — this newest chapter is teaching it to anchor that read to real price structure, support and resistance, instead of reading the tape in a vacuum.

## How it has grown

Earlier chapters built Tapeology's live tape reader, journal, replay studies, and an honest profit-measuring engine that proved the first trading strategy loses money on real data — now frozen as the proven foundation. This newest chapter set out to anchor that tape-reading to real price structure instead, starting with price history and price levels.

First, Tapeology learned to fetch, save, and faithfully read back a stock's real multi-year price history at several time scales — hourly, daily, weekly, monthly — with tamper detection and an honest message when no data connection is configured.

Then it learned to pinpoint real support and resistance levels from that history — prices where the market has previously turned, or a prior day/week/month's high, low, or close — each scored for strength from a documented settings file, never a guess, and proven never to let a later price bar sneak into an earlier answer.

Now, in the newest round, Tapeology groups those levels together: whenever several timeframes agree on roughly the same price, it bundles them into a single "zone" and grades how convincing that zone is — an honest A, B, or C — based on how many timeframes agree and whether at least one is a longer-term view (daily, weekly, or monthly). A zone seen on only one timeframe still gets reported honestly as the lowest grade, never hidden or inflated, and every zone also carries a combined strength score. None of this changed the tape reader, journal, studies, or performance pages, and none of it is visible in the app yet. Next, Tapeology will turn these graded zones into an actual trading rule that waits for the live tape to confirm a real entry.

## What it can do today

The product lets users type in a stock ticker and watch live trade-by-trade action to see who's in control, journal trading ideas, run replay studies, backtest a strategy into an honest profit-or-loss report beside a random-guessing comparison, view that scorecard on a Performance page, and let AI assistants read all of it directly. The price-history, price-level, and confluence-zone work from the last three chapters is not yet visible in the app — it is groundwork for a future feature.

_Last updated: 2026-07-06 after iteration 3._
