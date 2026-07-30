# Project story so far

Tapeology is a research tool for reading a stock's price action right now and mapping its key price levels — an honest study instrument, never a trading system.

## How it has grown

The product began as a two-page instrument — a live Cockpit and a Structure page for support and resistance. A later chapter, "The Desk," added a third page: a daily ~100-stock screen with scan history, a chart drill-in, a top-up run log, a coverage-repair button, and a read-only Claude connection.

Several rounds then turned from building to proving. Every ranked row gained a note on how many price levels its wall is built from, its timeframe split, and whether it sits at a round number, proven row by row against the product's own trusted math. That made the table too wide to read without scrolling sideways, so the whole ranked table was redesigned to fit a normal screen with no sideways scrolling, at about half its old row height. The redesign's own missing walkthrough video, and a couple of earlier open checks, were then closed out, and the project was judged finished twice, pending the owner's confirmation each time.

Each time, though, the improvement loop kept proposing more work before that confirmation landed. Most recently it taught the Desk's "top up my data" button to say honestly what it actually asked the data supplier for: a fourth outcome ("nothing new came back") beside reused/fetched/failed, a note on which stocks needed a full re-fetch versus a quick catch-up, and each failed stock's own exact requested date range. That capability was built and proven number-for-number against a real run — but its own short walkthrough video has now failed to record properly twice in a row. The first attempt used a stale, misconfigured copy of the page and skipped the recording step entirely; the most recent attempt aimed the camera at the wrong copy of the page and captured five identical blank frames instead of the feature, even though the underlying rebuild-and-recheck work that same round succeeded (the app now talks to the right server again, and all sixteen older screens were re-checked and still work).

One more short attempt is planned, aimed at the correct copy of the page this time. If it works, the project can again be proposed as finished. If it fails a second time in the same way, the team will treat the video as optional polish and propose finishing anyway, since every one of the Desk's abilities has already been proven to work by other means.

## What it can do today

The product lets users run a simulated tape-reading session with live moving price bars on the Cockpit, open a Structure page showing a stock's support and resistance on a real chart, and open a Desk page that screens about 100 stocks and ranks them. Each row shows how much history backs it up, its wall's price range and close, the nearest wall on the other side of price, how many price levels built that wall, its round-number status, and its timeframe breakdown — all fitting on one normal screen with no sideways scrolling. Users can hover a row for wall-grade detail, repair the Desk's coverage badges, browse past scans, jump from a saved scan into the matching Structure chart, read Desk data through a connected Claude conversation, and top up the Desk's stored price history on demand while seeing an honest account of what each stock's fetch actually asked for and got back.

_Last updated: 2026-07-31 after iteration 27._
