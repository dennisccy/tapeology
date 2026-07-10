# Project story so far

Tapeology is an app for studying how stocks trade — a live simulated price tape, a trading journal, a research lab for testing trading strategies against history, and a chart of a stock's real price structure, all in one place.

## How it has grown

It began as a way to watch simulated buying and selling pressure move a price tape, then grew a trading journal, a strategy-testing research lab, an honest profit scorecard, and a Structure page of support-and-resistance levels and zones with a side-by-side strategy comparison — all originally running on simulated or empty test data.

The current chapter, "The Library," replaces that test data with the real thing, for free: the app learned to pull real daily stock history from Yahoo Finance with no signup or cost, save it permanently with tamper detection, support every standard time window down to 1-minute (plus a self-built 4-hour view), reuse already-fetched data instantly instead of re-asking Yahoo Finance for it, and produce correct, real support-and-resistance results once fed this genuine price history.

Most recently, the app got its first real button for all of this: on the Structure page, a person can now pick a symbol, a time window, and a date range, click "Fetch from Yahoo Finance," and watch the real chart, support-and-resistance lines, and confluence-zone table appear automatically, labeled with a "Yahoo Finance" tag showing where the data came from. A reviewer, a tester, and an independent auditor each checked this by hand, including a live click-through in a browser, and confirmed it genuinely works. The one snag: a handful of the automatic reports that formally certify a round of work as finished did not get produced this time — a pipeline hiccup, not a feature problem — and one on-screen label was briefly covered by an unrelated dropdown in the proof screenshots. This round is paused on redoing that paperwork and tidying that visual; once done, it closes out "The Library" chapter entirely.

## What it can do today

The product lets users watch live simulated tape reading, keep a trading journal, run replay research studies, check an honest profit scorecard, and view a stock's support-and-resistance levels and zones on the Structure page with a side-by-side strategy comparison and champion badge. It also fetches and permanently saves real historical stock prices from Yahoo Finance across every standard time window, reuses already-fetched data instantly instead of asking twice, and computes real levels and zones on that data — and, as of this round, a person can trigger that fetch themselves with one click on the Structure page and see the "Yahoo Finance" source label on screen, rather than only through the programming interface.

_Last updated: 2026-07-10 after iteration 5._
