# Project story so far

Tapeology is an app for studying how stocks trade — a live simulated price tape, a trading journal, a research lab for testing trading strategies against history, and a chart of a stock's real price structure, all in one place.

## How it has grown

It began as a way to watch simulated buying and selling pressure move a price tape in real time, then grew a trading journal, a research lab for testing trading ideas against history, an honest profit scorecard, and a Structure page showing a stock's support-and-resistance levels and zones with a side-by-side strategy comparison and a "Champion" badge — all running on simulated or empty test data.

The current chapter, "The Library," is fixing that for free. After an honest checkpoint confirmed real-data fetching didn't exist yet, the app quietly gained the ability to pull daily price history for any stock from Yahoo Finance — free, no signup — and save it permanently with built-in tamper detection.

This round widened that single daily window into the full set the plan always intended: weekly, hourly, 5-minute, and 1-minute history now come straight from Yahoo Finance too, plus a 4-hour view the app builds itself from real hourly prices (Yahoo doesn't offer it the way this product wants it) — never invented numbers, and honest about a shorter last stretch when a trading day doesn't divide evenly. When a request genuinely can't be filled, the app now explains why in plain terms — a timeframe it doesn't offer yet, versus no data for that stock or date range — instead of one vague message for everything. Everything was checked against the real Yahoo Finance service, and every existing part of the app was re-confirmed to work exactly as before.

There's still no button to press for any of this — that arrives later. Next: a fast local memory so a repeat lookup is instant instead of re-fetching every time, then real support-and-resistance levels computed on this real data, and finally a genuine "Fetch from Yahoo Finance" button on the Structure page.

## What it can do today

The product lets users watch live simulated tape reading, keep a trading journal, run replay research studies, check an honest profit scorecard, and view a stock's support-and-resistance levels and zones on the Structure page with a side-by-side strategy comparison and champion badge. Behind the scenes, it can now also pull real historical stock prices from Yahoo Finance across every standard time window — daily, weekly, hourly, 5-minute, 1-minute, and a derived 4-hour view — save them permanently, and explain clearly when a specific request can't be filled, though none of this is reachable by clicking anything yet.

_Last updated: 2026-07-09 after iteration 2._
