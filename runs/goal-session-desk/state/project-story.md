# Project story so far

Tapeology is a research tool for reading how a stock's price is behaving right now and understanding its key price levels — an honest instrument for study, never a trading system.

## How it has grown

Before this chapter began, the product had already grown into a two-page instrument: a live Cockpit for watching a stock's price action settle into a read like "buyer in control," and a Structure page where the operator loads a chosen stock and date to see its key support and resistance levels, complete with historical case studies and an honest "not computed yet" message wherever deeper analysis hasn't run.

This chapter, nicknamed "The Desk," is adding a third page: a daily screening desk that will scan roughly 100 well-known stocks at once and point the operator at which ones have interesting price levels worth a closer look today. The chapter's first round did no building at all, on purpose — it confirmed the existing two pages still worked exactly as before, so the next round would know precisely what to build first.

The second round then built the very first piece of the new desk: fetching the current list of roughly 100 major companies from a public source, double-checking that the list looks right (rejecting anything garbled rather than guessing at it), and saving it as a permanent, dated record that can be read back later. Fetching the exact same list twice is recognized and refused, never silently duplicated. This work is entirely behind the scenes for now — there is still no button or page for an operator to see or trigger it — but it was tested thoroughly, including a real live fetch against the public source that succeeded, and every existing part of the product was double-checked to still work exactly as before.

Today, the groundwork for the company list is done and verified. The next round will teach the system which of those companies already have price history on file and add a way to fetch what's missing, clearing the path toward the actual daily scan still to come.

## What it can do today

The product lets users run a simulated tape-reading session and watch it settle into a read such as "Buyer Control," complete with live moving price bars; switch to a real stock's historical chart and see support and resistance bands drawn over the candles; open the Structure page, choose a symbol and date, and see its key price levels mapped out; open a case study for a past price touch and see how it played out; and check the Edge Report section, which honestly reports when a deeper study has not been run yet. Every reading is described, not recommended — the product never offers trading advice.

_Last updated: 2026-07-25 after iteration 1._
