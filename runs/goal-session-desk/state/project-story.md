# Project story so far

Tapeology is a research tool for reading how a stock's price is behaving right now and understanding its key price levels — an honest instrument for study, never a trading system.

## How it has grown

Before this chapter began, the product was already a two-page instrument: a live Cockpit for reading a stock's price action, and a Structure page for mapping a chosen stock's key support and resistance levels. This chapter, nicknamed "The Desk," set out to add a third page: a daily screening desk that scans roughly 100 well-known stocks and points the operator at which ones have interesting price levels worth a look today. It opened with a confirm-only baseline round, then taught the system to fetch and save the company list, then to check and fill in each company's price history across four time windows, and then to walk the whole list and rank companies by how close they sit to one of their own key price levels into one saved, dated result.

The next round put that ranked result on screen: a new third page, "Desk," appeared in the navigation bar next to Cockpit and Structure, with a "Run Screen" button to compute today's ranking live and a "Top-up" button to fetch fresh price history. While building it, the team found and fixed a real bug — a blank-priced entry from the price-history feed could quietly break the historical chart on the Structure page; it's now stopped at the source, refused on save, and skipped safely if it ever slips through. But that round finished with one photograph missing: nobody had ever actually captured Run Screen mid-computation with a second click properly refused, so the new page could not yet be fully signed off.

This latest round fixed exactly that gap and nothing else. The team went back with a fresh, disposable copy of the data, took all four required pictures of the Desk page — the empty state, the ranking computing live, the second click being refused, and the finished, fully ranked result — and confirmed the operator's real saved data was untouched throughout. With that, the Desk page is now fully proven and signed off, alongside a saved recording of the whole flow so a future change can't silently break it. Two things remain before this chapter can wrap up: letting an operator click a past scan to revisit it and jump straight to a stock's chart, and rounding out one small technical checklist so the "kept product still works" check can pass cleanly too.

## What it can do today

The product lets users run a simulated tape-reading session and watch it settle into a read such as "Buyer Control," with live moving price bars. It lets them open a Structure page to pick a stock and date and see its key support and resistance levels mapped over a real price chart, and open a case study for a past price touch. It lets them open a new Desk page that scans about 100 well-known stocks, run a fresh ranking on demand, refresh the underlying price history with one click, and see the fully ranked result with an honest note on every stock that couldn't be ranked and why.

_Last updated: 2026-07-26 after iteration 5._
