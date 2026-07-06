# Project story so far

Tapeology watches a stock's live trade-by-trade order flow to judge whether buyers or sellers are in control, and it has an honest engine for measuring whether that read turns into real profit — its newest chapter anchors that read to real price structure, support and resistance, instead of the tape alone.

## How it has grown

Earlier chapters built the live tape reader, journal, replay studies, and an honest profit-measuring engine that proved the original trading rule loses money on real data — now a frozen foundation. This chapter then taught Tapeology to store a stock's real multi-year price history at several time scales, find real support and resistance levels in it, and group agreeing levels into graded zones — an honest A, B, or C.

It then turned those graded zones into a second trading rule alongside the original: a simulated trade fires only where price sits at a zone and the live tape agrees at that moment, fading a defended zone or following a broken one, always recording which zone triggered it.

Most recently, that new rule learned to size its bets and set its stops by how strong each zone is — the strongest ("A") zones get a tight stop, a bigger simulated bet, and a more generous profit target, while weaker zones get progressively more cautious treatment — and the same profit-measuring engine now breaks results down zone by zone, to see whether the strongest zones really perform better. None of this is visible in the app yet — it lives behind the same machine connection that has served this whole chapter. Next, Tapeology will honestly compare this new zone-aware rule against the original rule, head to head, on historical data.

## What it can do today

The product lets users type a stock ticker and watch live trade-by-trade action to see who's in control, journal trading ideas, run replay studies, backtest strategies into honest profit-or-loss reports beside a random-guess comparison, and view that scorecard on a Performance page — with AI assistants able to read all of it directly. This chapter's price history, levels, zone grading, and the new structure-aware trading rule — now with its own sizing, stops, and zone-by-zone results — aren't visible in the app yet, reachable only through the product's machine connection; a fair head-to-head comparison against the original rule comes next.

_Last updated: 2026-07-06 after iteration 5._
