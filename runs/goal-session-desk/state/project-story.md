# Project story so far

Tapeology is a research tool for reading a stock's price action right now and mapping its key price levels — an honest study instrument, never a trading system.

## How it has grown

The product began as a two-page instrument — a live Cockpit and a Structure page for support and resistance — then gained a third page, "The Desk," with a daily ~100-stock screen, scan history, a chart drill-in, a top-up run log, a coverage-repair button, and a read-only Claude connection. Several early rounds proved out the Desk's ranked-row details and reflowed its table to fit one screen with no sideways scrolling.

Next, the Desk's "top up my data" button was made to say honestly what it actually asked the data supplier for — reused, freshly fetched, unchanged, or failed, each failed stock naming its own requested date range. That work was proven number-for-number against a real run, though its short walkthrough video failed to record properly three times running (a skipped step, the wrong page, then a recording-tool bug); the team judged the video optional polish, since the screenshots and tests already proved the behavior, and confirmed the Desk finished with all seventeen abilities in place.

Just as that confirmation was being sought, one more idea arrived: the Desk's own daily scan, unlike its two smaller siblings, kept no history of its own runs. The team built that eighteenth ability — every scan attempt, whether it fully computes, reuses a prior result, is cancelled, or fails, is now permanently recorded, and a repeat scan on unchanged data answers in about a hundredth of a second instead of the roughly minute-and-forty-second full recheck. A new "Screen Runs" panel on the Desk page shows this history, and for the first time this project's own walkthrough video actually captured the feature it was meant to demonstrate. The team checked the new record's numbers directly against the files on disk, and the Desk project has now been judged finished a fourth time, with all eighteen abilities proven.

## What it can do today

The product lets users run a simulated tape-reading session with live moving price bars on the Cockpit, open a Structure page showing a stock's support and resistance on a real chart, and open a Desk page that screens about 100 stocks and ranks them — each row showing its history depth, price range and close, opposite wall, and level composition, all fitting one screen with no sideways scrolling. Users can hover a row for wall-grade detail, repair the Desk's coverage badges, browse past scans and jump into the matching Structure chart, read Desk data through a connected Claude conversation, top up stored price history while seeing an honest account of what each stock's fetch asked for and got back, and now see a permanent record of every scan ever run — including reused, cancelled, or failed ones — with a repeat scan on unchanged data answering almost instantly.

_Last updated: 2026-07-31 after iteration 29._
