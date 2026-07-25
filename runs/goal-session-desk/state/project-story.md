# Project story so far

Tapeology is a research tool for reading how a stock's price is behaving right now and understanding its key price levels — an honest instrument for study, never a trading system.

## How it has grown

Before this chapter began, the product had already grown into a two-page instrument: a live Cockpit for watching a stock's price action settle into a read like "buyer in control," and a Structure page where the operator loads a chosen stock and date to see its key support and resistance levels, complete with historical case studies and an honest "not computed yet" message wherever deeper analysis hasn't been run.

This chapter, nicknamed "The Desk," sets out to add a third page: a daily screening desk that scans roughly 100 well-known stocks at once and tells the operator which ones have interesting price levels worth a closer look today — turning the single-stock instrument into something that can start the day by pointing at what matters.

The very first round of this chapter did no building at all, on purpose. It was a careful check confirming that the existing two pages still work exactly as before (they do, verified with real screenshots of the simulated trading session, the historical chart with its price-level overlay, the Structure page, a case study, and the honest "not computed yet" report) and that the new screening feature genuinely hasn't started yet, so the next round knows exactly what to build first.

Today, nothing on the new screening desk exists yet, but the whole existing product is confirmed healthy and unchanged. The next round begins building its very first piece: fetching and safely storing the list of stocks the desk will screen.

## What it can do today

The product lets users run a simulated tape-reading session and watch it settle into a read such as "Buyer Control," complete with live moving price bars; switch to a real stock's historical chart and see support and resistance bands drawn over the candles; open the Structure page, choose a symbol and date, and see its key price levels mapped out; open a case study for a past price touch and see how it played out; and check the Edge Report section, which honestly reports when a deeper study has not been run yet. Every reading is described, not recommended — the product never offers trading advice.

_Last updated: 2026-07-25 after iteration 0._
