# Project story so far

Tapeology is a research tool for reading a stock's price action right now and mapping its key price levels — an honest study instrument, never a trading system.

## How it has grown

Before this chapter the product was a two-page instrument — a live Cockpit and a Structure page for support and resistance. This chapter, "The Desk," added a third page: a daily ~100-stock screen with scan history, a chart drill-in, and a read-only Claude connection, then closed a string of early honesty gaps — a top-up run log, a coverage-repair button, addressable same-day scans, and run-history panels that speak up when a saved file is damaged.

Each ranked row then gained two disclosures: the exact price range its key wall sits in beside the closing price it was measured from (an independent check caught and fixed a real bug where older rows had silently lost their price range), and a new "opposite" column naming the nearest wall on the other side of price — which first shipped pointing at the wrong wall on 2 of the owner's 63 real stocks and was corrected the very next round, proven row by row against the owner's own stored prices.

With all fourteen planned capabilities confirmed working, the last three rounds have spent their effort on paperwork rather than the product itself: one round retook a missing full-length picture and proved two scans saved the same day really do show different price-history coverage for one stock; the next round attempted a guided walkthrough video of the price and "nearest wall" columns but produced nothing, because its recording script was written incorrectly; this latest round fixed that script and recorded the video, proving every number it speaks against the saved data on disk. Every one of the fourteen planned capabilities is now confirmed working, and nothing has broken along the way.

The only thing left is one small screenshot the team's tools genuinely cannot take — a hover-tip message that the browser draws outside the area it can photograph — and only the project owner can decide how to handle it: reword the requirement, change the page to show the hint differently, approve a different capture method, or accept the finish without that one photo. Once that choice is made, one short run is expected to close out the chapter.

## What it can do today

The product lets users run a simulated tape-reading session with live moving price bars, open a Structure page showing a stock's support and resistance on a real chart, and open a Desk page that screens about 100 stocks, refreshes their price history, and ranks them — each row showing how much history backs it up, its wall's price range and close, and the nearest wall on the other side of price. Users can repair the Desk's coverage badges, browse past scans and refresh runs (including two scans saved the same day), jump from a saved scan into the matching Structure chart, see when a saved record fails its own integrity check, and read Desk data through a connected Claude conversation.

_Last updated: 2026-07-30 after iteration 21._
