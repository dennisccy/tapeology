# Project story so far

Tapeology is an app for studying how stocks trade — a live simulated price tape, a trading journal, a research lab for testing trading strategies against history, and a chart of a stock's real price structure, all in one place.

## How it has grown

It began as a way to watch simulated buying and selling pressure move a price tape, then grew a trading journal, a strategy-testing research lab, an honest profit scorecard, and a Structure page of support-and-resistance levels and zones with a side-by-side strategy comparison — all running on simulated or empty test data.

The current chapter, "The Library," is replacing that empty data with the real thing, for free. After an honest checkpoint confirmed real price-fetching didn't exist yet, the app gained the ability to pull real daily stock history from Yahoo Finance — no signup, no cost — and save it permanently with tamper detection, then grew that into the full set of time windows (weekly down to 1-minute, plus an honestly self-built 4-hour view), and then learned not to repeat itself, instantly handing back a stock's history from what it already saved instead of asking Yahoo Finance twice.

Most recently, the app proved that its existing support-and-resistance calculator — already powering the Structure page — gives correct, real results once it has this genuine price history to work with, not just empty test data. A stock with real saved prices now produces real support-and-resistance levels and real confluence zones, checked against the same trustworthy math the app has always used, with nothing invented and no shortcuts taken.

There's still no button to press for any of this. Next: a genuine "Fetch from Yahoo Finance" button on the Structure page, so a person can trigger a real fetch and watch real levels and zones appear on screen by clicking, rather than only through the programming interface.

## What it can do today

The product lets users watch live simulated tape reading, keep a trading journal, run replay research studies, check an honest profit scorecard, and view a stock's support-and-resistance levels and zones on the Structure page with a side-by-side strategy comparison and champion badge. Behind the scenes, it can also pull and permanently save real historical stock prices from Yahoo Finance across every standard time window, skip re-fetching data it already has, let saved data be searched by symbol and timeframe, and correctly compute real support-and-resistance levels and zones on that real data — none of this reachable by clicking yet.

_Last updated: 2026-07-10 after iteration 4._
