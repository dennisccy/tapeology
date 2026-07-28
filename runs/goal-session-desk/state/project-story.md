# Project story so far

Tapeology is a research tool for reading a stock's price action right now and mapping its key price levels — an honest study instrument, never a trading system.

## How it has grown

Before this chapter the product was a two-page instrument — a live Cockpit and a Structure page for support and resistance. This chapter, "The Desk," added a third page: a daily ~100-stock screen with a memory of past scans, a chart drill-in, and a read-only Claude connection, later made honest about how old each row's price reading is.

The team then closed a second gap: refreshing a stock's price history used to lose its outcome once the next refresh started. A new panel fixed that, listing every refresh run ever completed — what it tried, reused, fetched, or failed, and why — with an honest count of anything a stopped run never reached.

The only piece left was a short recorded guide proving that panel end to end, empty first then a finished run. Two rounds in a row failed to film it, both for organizational reasons — once filmed too late in the round to count, once with the "nothing saved yet" moment skipped before a camera was ready.

This round fixed both problems at once. The team filmed the empty panel first, then three practice runs — one ordinary, one stopped partway, one that failed on purpose — and joined both moments into one guide. A final check caught that the first cut had quietly mismatched its own words and picture, and fixed it before anything shipped. Every other part of the Desk was re-checked the same day and still works as before. With the guide finished, everything this chapter set out to build is now built, proven, and shown — the team is waiting on the owner to confirm it is done.

## What it can do today

The product lets users run a simulated tape-reading session that settles into a read like "Buyer Control," with live moving price bars; open a Structure page showing a stock's support and resistance levels on a real chart; and open a Desk page that screens about 100 stocks, refreshes their price history, ranks them, and shows how old each row's reading is. Users can jump from a past scan into the Structure chart for that stock and date, look back at any past refresh run to see exactly what it did, and read the Desk's data through a connected Claude conversation.

_Last updated: 2026-07-28 after iteration 13._
