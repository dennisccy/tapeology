# Project story so far

Tapeology is a research tool for reading how a stock's price is behaving right now and understanding its key price levels — an honest instrument for study, never a trading system.

## How it has grown

Before this chapter began, the product was already a two-page instrument: a live Cockpit for reading a stock's price action, and a Structure page mapping a chosen stock's key support and resistance levels. This chapter, "The Desk," added a third page — a daily screening desk over roughly 100 well-known stocks. Early rounds taught it to fetch and save the company list, fill in each company's price history, rank companies by closeness to a key price level, and show that ranking on a Desk page with "Run Screen" and "Top-up" buttons, fixing a bug along the way where a blank-priced entry from the price feed could break the price chart.

A later round finished proving the Desk page with every required photograph, including a scan running live with a repeat click refused. The next round gave the Desk a memory: clicking any past scan shows exactly what was recorded that day, and every row — even a skipped one — jumps straight into the Structure chart for that stock and date, already loaded. The round after let Claude read the Desk's company list and scan results directly, and fixed a small bug where hovering over a scan row had stopped showing its full detail — but the chapter stalled there, waiting on the owner's written word on whether an earlier data-repair fix to two protected parts of the product could stay.

This final round got that answer: the owner wrote his permission directly into the project's plan, naming exactly which files the repair could touch. The team then proved — by rebuilding the product exactly as it stood before this chapter and comparing its answers side by side — that nothing outside the agreed repair had changed, put back a stray edit to the project's own self-check script, tidied a leftover code comment, and took the last missing photograph: the main page in "Historical" mode on a real company, its price chart drawn with support and resistance lines. Every one of this chapter's seven promises now has real, opened proof, and the chapter is complete.

## What it can do today

The product lets users run a simulated tape-reading session and watch it settle into a read such as "Buyer Control," with live moving price bars. It lets them open a Structure page to pick a stock and date and see its key support and resistance levels mapped over a real price chart, and open a case study of a past price touch. It lets them open a Desk page that scans about 100 well-known stocks, run a fresh ranking on demand, refresh the underlying price history with one click, and see the fully ranked result with an honest note on every stock that couldn't be ranked and why. It lets them revisit any past scan exactly as it was recorded, and jump from any scan row straight into the Structure chart for that stock and date, already loaded. Through a connected Claude conversation, Claude can read the Desk's company list and scan results directly too.

_Last updated: 2026-07-27 after iteration 8._
