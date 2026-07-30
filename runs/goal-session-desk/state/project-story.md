# Project story so far

Tapeology is a research tool for reading a stock's price action right now and mapping its key price levels — an honest study instrument, never a trading system.

## How it has grown

Before this chapter the product was a two-page instrument — a live Cockpit and a Structure page for support and resistance. This chapter, "The Desk," added a third page: a daily ~100-stock screen with scan history, a chart drill-in, and a read-only Claude connection, and closed early honesty gaps such as a top-up run log, a coverage-repair button, and same-day scans you can tell apart.

Each ranked row then gained a price range plus the closing price it was measured from, and a new "opposite wall" column naming the nearest wall on the other side of price — which first pointed at the wrong wall on 2 of the owner's 63 real stocks and was corrected the very next round, proven row by row against the owner's own stored prices.

The last several rounds turned from building to proving. One round retook a missing picture and showed that two scans saved the same day really do differ in what price history they cover. The next round tried to record a guided walkthrough video of the price and "nearest wall" columns but produced nothing, because its recording script was written incorrectly. The round after that fixed the script and recorded the video, checking every number it speaks against the saved data on disk. That left exactly one thing undone: a small pop-up shown when hovering a row, which the normal screenshot tool could never capture, because the browser draws it outside the area it can photograph. Three rounds in a row proved this same limit, and the project paused, waiting for the owner to decide how to handle it.

This latest round resolved it. The owner approved a special capture method — a separate small screen with a real browser window, watched by a tool that only saves a picture if the pop-up genuinely appears and carries the right words — and the picture was taken. It shows the pop-up spilling outside the browser window itself onto the bare screen behind it, proof it could not have been faked by the normal tool, and every number in it matches the saved records exactly. No product code changed this round; it was purely closing out the last piece of proof. With that photo captured, every one of the fourteen planned capabilities for this chapter is now confirmed working end to end, and the project is waiting on the owner's final confirmation to close the chapter.

## What it can do today

The product lets users run a simulated tape-reading session with live moving price bars, open a Structure page showing a stock's support and resistance on a real chart, and open a Desk page that screens about 100 stocks, refreshes their price history, and ranks them — each row showing how much history backs it up, its wall's price range and close, and the nearest wall on the other side of price, with a hover pop-up giving the wall-grade breakdown. Users can repair the Desk's coverage badges, browse past scans and refresh runs (including two scans saved the same day), jump from a saved scan into the matching Structure chart, see when a saved record fails its own integrity check, and read Desk data through a connected Claude conversation.

_Last updated: 2026-07-30 after iteration 22._
