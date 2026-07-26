# Project story so far

Tapeology is a research tool for reading how a stock's price is behaving right now and understanding its key price levels — an honest instrument for study, never a trading system.

## How it has grown

Before this chapter began, the product was already a two-page instrument: a live Cockpit for reading a stock's price action, and a Structure page for mapping a chosen stock's key support and resistance levels. This chapter, nicknamed "The Desk," set out to add a third page: a daily screening desk that scans roughly 100 well-known stocks and points the operator at which ones have interesting price levels worth a look today. It opened with a confirm-only baseline round, then taught the system to fetch and save the company list, then to check and fill in each company's price history across four time windows, and then to walk the whole list and rank companies by how close they sit to one of their own key price levels into one saved, dated result.

This round finally put that ranked result on screen. A new third page, "Desk," now sits in the navigation bar next to Cockpit and Structure. An operator can click "Run Screen" to watch today's ranking compute live, and "Top-up" to fetch fresh price history for the list — the first on-screen button for a job that previously only had a behind-the-scenes trigger. The page shows the full ranked table, an honest note on which companies could not be ranked and why, and a complete paper trail for every scan. While building it, the team also found and fixed a real bug: a blank-priced entry from the price-history feed could quietly break the historical chart on the Structure page; it is now stopped at the source, refused if anyone tries to save it, and skipped safely if it ever gets through.

The new Desk page works in every check the team could run themselves, but the one photograph the plan calls for — Run Screen running, with a second click properly refused — was never taken, so this feature is not yet fully signed off. The next round's first job is to take that photograph properly and fix a test report that has some things wrong in it; only after that does new work resume, starting with letting an operator click on a past scan to jump straight to that company's own chart.

## What it can do today

The product lets users run a simulated tape-reading session and watch it settle into a read such as "Buyer Control," with live moving price bars. It lets them switch to a real stock's historical chart and see support and resistance bands over the candles, open the Structure page to choose a symbol and date and see its key price levels mapped out, open a case study for a past price touch, and check an Edge Report that honestly reports when a deeper study has not been run yet. Every reading is described, not recommended. Behind the scenes, it can also fetch a company list, fill in price history, and run a full daily scan — the on-screen page for that scan now exists too, though its verification photographs are still being finished.

_Last updated: 2026-07-26 after iteration 4._
