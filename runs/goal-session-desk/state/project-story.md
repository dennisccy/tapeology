# Project story so far

Tapeology is a research tool for reading a stock's price action right now and mapping its key price levels — an honest study instrument, never a trading system.

## How it has grown

Before this chapter the product was a two-page instrument — a live Cockpit and a Structure page for support and resistance. This chapter, "The Desk," added a third page: a daily ~100-stock screen with scan history, a chart drill-in, and a read-only Claude connection. The team then closed a string of honesty gaps one at a time: a permanent Top-up Runs panel records every price-refresh run's outcome; a Reconcile Index button lets the team check and repair the ranked list's coverage badges instead of asking anyone to trust them; every saved scan opens by its own name, including an older same-day scan that used to sit unreachable behind a newer one; and the run-history panels now speak up when one of their own saved files is damaged.

More recently, each ranked row started saying how many days of price history it's measured over, and then how much history that wall was measured across, followed by the exact closing price each wall was measured against, shown beside the price range it spans — so "the price sits inside the wall" is something you can read directly. An independent check caught and fixed a real slip before that one shipped: older rows had briefly lost their price range entirely.

Most recently, the team tried to add one more disclosure — a new "opposite" column showing, for every ranked row, the nearest wall on the OTHER side of price from the one it was ranked on, plus a tooltip line counting how many A/B/C walls exist for that stock. The numbers are proven correct, and the feature is live on the page. But a careful check against the goal's own wording found that the column currently names the best-graded wall on the far side, not the truly nearest one — on 2 of the owner's 63 real stocks, that means it points at a wall more than twice as far away as the closest one really is. That one detail needs a small fix before this piece is considered finished, and the guided walkthrough film for it — plus two earlier walkthroughs — still needs a proper re-take.

## What it can do today

The product lets users run a simulated tape-reading session with live moving price bars, open a Structure page showing a stock's support and resistance on a real chart, and open a Desk page that screens about 100 stocks, refreshes their price history, ranks them, and for each row shows its history depth, its measured closing price and wall range, and (not yet fully accurate) a nearby wall on the other side of price. Users can check and repair the Desk's coverage badges, look back at any past refresh run or scan — including two scans saved the same day — jump from a past scan into the matching Structure chart, see when a saved record fails its own integrity check, and read Desk data through a connected Claude conversation.

_Last updated: 2026-07-29 after iteration 18._
