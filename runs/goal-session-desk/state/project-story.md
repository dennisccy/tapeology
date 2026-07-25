# Project story so far

Tapeology is a research tool for reading how a stock's price is behaving right now and understanding its key price levels — an honest instrument for study, never a trading system.

## How it has grown

Before this chapter began, the product was already a two-page instrument: a live Cockpit for reading a stock's price action, and a Structure page for mapping a chosen stock's key support and resistance levels.

This chapter, nicknamed "The Desk," adds a third page: a daily screening desk that scans roughly 100 well-known stocks and points the operator at which ones have interesting price levels worth a look today. It opened with a confirm-only baseline round, then taught the system to fetch and save the company list, and next to check and fill in each company's price history across four time windows.

This round finished the heart of the desk: given any date, the system now walks the whole company list, works out how close each stock sits to one of its own interesting price levels, and ranks them into one saved, dated result — a company with no price history on file is honestly marked "skipped" rather than guessed at. Every scan is permanent: asking for the identical scan again returns the same saved result rather than a new copy, and a reviewer this round caught and fixed one real weak spot — a damaged saved result could quietly have been overwritten — so a damaged result is now refused and flagged instead. All of this still lives entirely behind the scenes.

Next up: the actual on-screen desk page itself, so an operator can press a "Run Screen" button and watch the ranked results appear.

## What it can do today

The product lets users run a simulated tape-reading session and watch it settle into a read such as "Buyer Control," with live moving price bars; switch to a real stock's historical chart and see support and resistance bands over the candles; open the Structure page, choose a symbol and date, and see its key price levels mapped out; open a case study for a past price touch; and check the Edge Report section, which honestly reports when a deeper study has not been run yet. Every reading is described, not recommended. Behind the scenes, it can also fetch the company list, fill in price history, and run a full daily scan — none of it on-screen yet.

_Last updated: 2026-07-25 after iteration 3._
