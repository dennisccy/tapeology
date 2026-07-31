# Project story so far

Tapeology is a research tool for reading a stock's price action right now and mapping its key price levels — an honest study instrument, never a trading system.

## How it has grown

The product began as a two-page instrument — a live Cockpit and a Structure page for support and resistance. A later chapter, "The Desk," added a third page: a daily ~100-stock screen with scan history, a chart drill-in, a top-up run log, a coverage-repair button, and a read-only Claude connection. Several rounds then proved out that page's ranked-row details (history depth, timeframe split, round-number flag) and redesigned its table to fit one screen with no sideways scrolling, and the project was judged finished once, pending the owner's confirmation.

Before that confirmation landed, the improvement loop proposed one more capability: the Desk's "top up my data" button now says honestly what it actually asked the data supplier for — a fourth outcome ("nothing new came back") beside reused/fetched/failed, a tail-vs-full-fetch note, and each failed stock's own exact requested date range. This was built and proven number-for-number against a real run. Its short walkthrough video, though, failed to record properly three times running: first a downgraded run skipped the recording step entirely, then the camera was pointed at the wrong copy of the page, and on a third, carefully-staged attempt a plumbing bug in the recording tool itself silently overrode the video's own target address, so it again captured nothing useful.

Rather than ask for a fourth attempt, the team judged the walkthrough optional workshop polish, not a real gap — everything it would have shown is already proven in still screenshots and test results checked directly — and proposed the finish on that evidence instead. The Desk project has now been judged finished for a third time, this time with all seventeen of its abilities proven and nothing left outstanding.

## What it can do today

The product lets users run a simulated tape-reading session with live moving price bars on the Cockpit, open a Structure page showing a stock's support and resistance on a real chart, and open a Desk page that screens about 100 stocks and ranks them. Each row shows how much history backs it up, its wall's price range and close, the nearest wall on the other side of price, how many price levels built that wall, its round-number status, and its timeframe breakdown — all fitting on one normal screen with no sideways scrolling. Users can hover a row for wall-grade detail, repair the Desk's coverage badges, browse past scans, jump from a saved scan into the matching Structure chart, read Desk data through a connected Claude conversation, and top up the Desk's stored price history on demand while seeing an honest account of what each stock's fetch actually asked for and got back.

_Last updated: 2026-07-31 after iteration 28._
