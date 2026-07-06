# Project story so far

Tapeology watches a stock's live trade-by-trade order flow to judge whether buyers or sellers are in control, and it already has an honest engine for measuring whether that read actually turns into profit — this newest chapter is teaching it to anchor that read to real price structure, support and resistance, instead of reading the tape in a vacuum.

## How it has grown

Earlier chapters built Tapeology's live tape reader, journal, replay studies, and an honest profit-measuring engine that proved the first trading strategy loses money on real data — now frozen as the proven foundation. This newest chapter then taught Tapeology to fetch and faithfully store a stock's real multi-year price history at several time scales, with tamper detection and an honest message when no data connection is configured.

From that history, it learned to pinpoint real support and resistance levels, then to group levels that agree across timeframes into graded zones — an honest A, B, or C — based on how convincing the agreement is.

Now, in the latest round, Tapeology turned those graded zones into an actual second trading rule that sits alongside the original one: a simulated trade only fires where price sits at one of these zones and the live tape agrees at that same moment — either the tape shows the zone being defended, so the trade fades back the other way, or shows real, sustained conviction carrying straight through it, so the trade follows through. Every simulated trade this new rule takes records exactly which zone triggered it, and it is judged by the exact same honest profit-measuring engine as the original rule, side by side, never replacing it. None of this is visible in the app yet — it still lives behind the same machine-readable connection that has served this whole chapter so far. Next, Tapeology will teach this new rule to size its bets and set its stops according to how convincing each zone is.

## What it can do today

The product lets users type a stock ticker and watch live trade-by-trade action to see who's in control, journal trading ideas, run replay studies, backtest strategies into honest profit-or-loss reports beside a random-guessing comparison, view that scorecard on a Performance page, and let AI assistants read all of it directly. This chapter's price-history, price-level, zone-grading, and new structure-aware trading rule aren't visible in the app yet — reachable only through the product's machine connection — with sizing and risk scaled to each zone's strength coming next.

_Last updated: 2026-07-06 after iteration 4._
