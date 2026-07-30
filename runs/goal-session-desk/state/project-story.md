# Project story so far

Tapeology is a research tool for reading a stock's price action right now and mapping its key price levels — an honest study instrument, never a trading system.

## How it has grown

The product began as a two-page instrument — a live Cockpit and a Structure page for support and resistance. A later chapter, "The Desk," added a third page: a daily ~100-stock screen with scan history, a chart drill-in, a top-up run log, a coverage-repair button, and a read-only Claude connection. Several rounds then turned from building to proving, including one small hover pop-up that took several extra rounds and a special capture method to finally confirm wasn't faked.

Rather than stop, the project then improved itself on its own initiative: every ranked row gained a note on how many price levels its wall is built from, its timeframe split, and whether it sits at a round number, proven row by row against the product's own trusted math for all one hundred ranked rows. That made the table too wide for its two newest columns to be seen without scrolling sideways, so the whole ranked table was redesigned to fit a normal screen with no sideways scrolling, at about half its old row height.

The next round closed that redesign's remaining gaps — recording its missing walkthrough video and re-confirming the built-in Claude connection and the wall-composition numbers — and the project was judged finished, pending the owner's confirmation. The improvement loop then proposed one more capability on its own: making the Desk's "top up my data" button honest about what it actually asked the data supplier for. This latest round built it — the top-up panel now shows a fourth, honest outcome ("nothing new came back") beside the reused/fetched/failed counts, states how many stocks needed just a short catch-up fetch versus a full one, and shows each failed stock's own exact requested date range, all proven number-for-number against a real saved run. Sixteen capabilities still hold and this seventeenth is proven to work, but its short walkthrough video is still missing — this round's automation took a faster path that skips filming — and a stale copy of the app needs rebuilding first. One more short round is expected before the finish can be confirmed again.

## What it can do today

The product lets users run a simulated tape-reading session with live moving price bars on the Cockpit, open a Structure page showing a stock's support and resistance on a real chart, and open a Desk page that screens about 100 stocks and ranks them. Each row shows how much history backs it up, its wall's price range and close, the nearest wall on the other side of price, how many price levels built that wall, its round-number status, and its timeframe breakdown — all fitting on one normal screen with no sideways scrolling. Users can hover a row for wall-grade detail, repair the Desk's coverage badges, browse past scans, jump from a saved scan into the matching Structure chart, read Desk data through a connected Claude conversation, and top up the Desk's stored price history on demand while seeing an honest account of what each stock's fetch actually asked for and got back.

_Last updated: 2026-07-31 after iteration 26._
