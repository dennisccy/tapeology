# Project story so far

Tapeology is a research tool for reading a stock's price action right now and mapping its key price levels — an honest study instrument, never a trading system.

## How it has grown

The product began as a two-page instrument — a live Cockpit and a Structure page for support and resistance — then gained a third page, "The Desk," with a daily ~100-stock screen, scan history, a chart drill-in, a top-up log, a coverage-repair button, and a read-only Claude connection, with early rounds polishing its ranked-row details and fitting its table to one screen with no sideways scrolling.

Next, the Desk's "top up my data" button was made to say honestly what it actually asked the data supplier for and got back — proven number-for-number against a real run, though its walkthrough video never recorded properly across three separate tries and was judged optional polish once the screenshots and tests already proved the behavior. The team confirmed the Desk finished with seventeen abilities in place.

One more idea then arrived: give the Desk's own daily scan a permanent run history, like its two smaller siblings already had. The team built it — every scan attempt is now recorded, whether it fully computes, reuses a prior result, is cancelled, or fails, and a repeat scan on unchanged data answers in about a hundredth of a second instead of a minute and forty seconds of full rechecking. The team called the Desk finished a fourth time, but the confirmation was turned back on one specific ground: nobody had ever photographed the new scan-history panel's honest "nothing recorded yet" message before any scan had run.

The most recent round closed exactly that gap — a brand-new, empty copy of the Desk's data was set up and photographed before any scan ever ran, proving the honest "No screen runs recorded yet." message. But the round was given less work time than its own plan called for, so two small wording fixes and a few tests meant to ride along with it were skipped, and a small housekeeping slip (two project files left pointing at a folder that no longer exists) needs tidying. Nothing the product does is broken — all eighteen abilities still work — and one more ordinary round of work is expected to close these last loose ends.

## What it can do today

The product lets users run a simulated tape-reading session with live moving price bars on the Cockpit, open a Structure page showing a stock's support and resistance on a real chart, and open a Desk page that screens about 100 stocks and ranks them — each row showing its history depth, price range and close, opposite wall, and level composition, all fitting one screen with no sideways scrolling. Users can hover a row for wall-grade detail, repair the Desk's coverage badges, browse past scans and jump into the matching Structure chart, read Desk data through a connected Claude conversation, top up stored price history while seeing an honest account of what each stock's fetch asked for and got back, and see a permanent record of every scan ever run — including reused, cancelled, or failed ones — with a repeat scan on unchanged data answering almost instantly.

_Last updated: 2026-07-31 after iteration 30._
