# Project story so far

Tapeology is a research tool for reading a stock's price action right now and mapping its key price levels — an honest study instrument, never a trading system.

## How it has grown

The product began as a two-page instrument — a live Cockpit and a Structure page for support and resistance — then gained a third page, "The Desk," for a daily ~100-stock screen with scan history, a chart drill-in, a top-up log, a coverage-repair button, and a read-only Claude connection.

The team then gave the daily scan its own permanent run history, like its two smaller siblings already had — every scan attempt is recorded, whether it fully computes, reuses a prior result, is cancelled, or fails, and a repeat scan answers in a fraction of a second. Confirming that took three tries — a missing photo of the empty "nothing recorded yet" state, then two small honesty fixes and a stray housekeeping slip — before all eighteen of the Desk's abilities were checked and the team called it finished.

The next idea was to have the Desk tell the operator the actual date each stock's price history reaches after a top-up, not just the window it asked the supplier for. The team built it, tested it against a real 404-pair top-up with zero disagreements, and called the Desk finished again. A closer second look then caught a real bug: the page's "newest recorded reach" line disagreed with its own "pairs recorded earlier" list, which also ran to hundreds of rows instead of a short one. The most recent round was meant to fix that, but the automated scheduler shortened it twice in a row, so no developer worked on it and the bug is still there, unchanged. Nothing broke and nothing of the owner's data was touched — the team corrected its own earlier over-eager "finished" mark on this one feature and is waiting for an ordinary full round to make the real fix.

## What it can do today

The product lets users run a simulated tape-reading session with live moving price bars on the Cockpit, open a Structure page showing a stock's support and resistance on a real chart, and open a Desk page that screens about 100 stocks and ranks them — each row showing its history depth, price range and close, opposite wall, and level makeup, all fitting one screen with no sideways scrolling. Users can hover a row for wall-grade detail, repair the Desk's coverage badges, browse past scans and jump into the matching Structure chart, read Desk data through a connected Claude conversation, and top up stored price history while seeing an honest account of what each stock's fetch asked for and got back. They can also see a permanent, truthful record of every scan ever run, including reused, cancelled, or failed ones, with a repeat scan on unchanged data answering almost instantly. One newer feature — seeing exactly how current each stock's price history is after a top-up — is built but still shows a confusing, self-contradicting summary on screen, so it is not yet ready to rely on.

_Last updated: 2026-07-31 after iteration 33._
