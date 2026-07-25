# Project story so far

Tapeology is a research tool for reading how a stock's price is behaving right now and understanding its key price levels — an honest instrument for study, never a trading system.

## How it has grown

Before this chapter began, the product had already grown into a two-page instrument: a live Cockpit for watching a stock's price action settle into a read like "buyer in control," and a Structure page where the operator loads a chosen stock and date to see its key support and resistance levels.

This chapter, nicknamed "The Desk," is adding a third page: a daily screening desk that will scan roughly 100 well-known stocks at once and point the operator at which ones have interesting price levels worth a closer look today. It opened with a confirm-only round that changed nothing on purpose, then began building its first two pieces in order.

The first piece, finished in round two, taught the system to fetch the current list of roughly 100 major companies from a public source, double-check the list looks right, and save it as a permanent, dated record — refusing to save a duplicate and refusing to guess at a garbled page. The second piece, just finished this round, taught the system to check which of those companies already have price history on file across four different time windows (hourly, 4-hour, daily, weekly), and to run a job that safely fills in whatever is missing. That fill-in job can be paused and resumed without redoing any work it already finished, and it was proven against the real data source, not just a test copy. Both pieces are still entirely behind the scenes — there is still no button or page for an operator to see or trigger either of them — but everything shipped so far was checked thoroughly, and every existing part of the product was double-checked to still work exactly as before.

Next up: the actual daily scan itself — walking through the whole company list, ranking which stocks have the most interesting price levels right now, and keeping a permanent, dated record of each day's results.

## What it can do today

The product lets users run a simulated tape-reading session and watch it settle into a read such as "Buyer Control," complete with live moving price bars; switch to a real stock's historical chart and see support and resistance bands drawn over the candles; open the Structure page, choose a symbol and date, and see its key price levels mapped out; open a case study for a past price touch and see how it played out; and check the Edge Report section, which honestly reports when a deeper study has not been run yet. Every reading is described, not recommended — the product never offers trading advice.

_Last updated: 2026-07-25 after iteration 2._
