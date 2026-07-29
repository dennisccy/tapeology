# Project story so far

Tapeology is a research tool for reading a stock's price action right now and mapping its key price levels — an honest study instrument, never a trading system.

## How it has grown

Before this chapter the product was a two-page instrument — a live Cockpit and a Structure page for support and resistance. This chapter, "The Desk," added a third page: a daily ~100-stock screen with a memory of past scans, a chart drill-in, and a read-only Claude connection, later made honest about how old each row's price reading is.

The team then closed a second gap: refreshing a stock's price history used to lose its outcome once the next refresh started. A new panel fixed that, listing every refresh run ever completed — what it tried, reused, fetched, or failed, and why — with an honest count of anything a stopped run never reached. Proving that panel on film took three tries: two rounds failed for organizational reasons (filmed too late to count, or the "nothing saved yet" moment skipped before a camera was ready), and the third finally filmed the empty panel first, then three practice runs, and joined both moments into one guide.

With that behind it, the team measured the live system and found one more honest gap: the small colored badges on the Desk's ranked list, showing which price history is stored for each stock, could quietly go stale. The app's internal lookup table of "what's stored" could fall out of sync with the real files on disk, and a badge could stay wrong forever with no way to fix it. This final round closed that gap: a new "Reconcile Index" button on the Desk page repairs that lookup table straight from the real files, with live progress and a cancel option, and a new permanent "Index Reconciliation" panel records exactly what was wrong before and what got fixed on every run — turning those coverage badges from something a user just had to trust into something they can check and correct themselves. The team filmed the honest "nothing checked yet" moment first, then the repair, in the right order, on one continuous rig, and re-checked every earlier part of the Desk the same day to confirm nothing else moved.

With that self-check built, proven, and shown, everything this chapter, "The Desk," set out to build is complete — ten planned capabilities, all working, all verified against real data, all recorded on screen for a non-technical reviewer to see. The team is now waiting on the owner to look it over and confirm the chapter is finished; only small, optional polish items remain on a backlog, none blocking.

## What it can do today

The product lets users run a simulated tape-reading session that settles into a read like "Buyer Control," with live moving price bars; open a Structure page showing a stock's support and resistance levels on a real chart; and open a Desk page that screens about 100 stocks, refreshes their price history, ranks them, and shows how old each row's reading is. Users can jump from a past scan into the Structure chart for that stock and date, look back at any past refresh run to see exactly what it did, read the Desk's data through a connected Claude conversation, and now also trigger a check that the Desk's coverage badges are telling the truth — repairing them on the spot, with a permanent, browsable record of every check ever run.

_Last updated: 2026-07-29 after iteration 14._
