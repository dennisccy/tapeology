# Project story so far

Tapeology is a real-time tape-reading tool for a single US stock: you give it one ticker and it watches the live order flow and tells you, right now, whether buyers or sellers are in control, whether aggression is being quietly absorbed, or whether it's simply unclear — and how confident it is.

## How it has grown

It began by locking down a blueprint — a single live "tape cockpit" screen showing one stock at a time, with one trustworthy source for every number — which a person approved before any building started. The first build then delivered the whole foundation: watching the built-in sample "SIM-BUYER" filled the screen with a live read — buy/sell prices, recent trades, named tape measurements, plain-language notes, an event log, and an overall "who's in control" call with a confidence score — settling on "Buyer Control" and honest from the start, calling buyers in control only when aggressive buying genuinely lifts the price, and refusing to invent data for a stock it doesn't recognise.

The next rounds made that foundation trustworthy and legible: the buyer view was confirmed in a real browser, every on-screen number was checked to match the underlying data exactly, and a cosmetic bug was fixed so the green "buying" highlight shows at a glance. Then came the mirror case — watching "SIM-SELLER", the cockpit correctly reads "Seller Control" in red, and only when the selling actually pushes the price down.

This latest round added the case the whole product was built for: absorption. You can now watch two new samples, "SIM-BIDABS" and "SIM-ASKABS", where a flood of one-sided trading hits a price that simply holds — and the cockpit reads these as "Bid Absorption" and "Ask Absorption" in amber rather than as control. The decision rests on whether the price actually moved, not on how much aggression there was: the very same heavy selling reads as "Seller Control" when the price drops, but as "Bid Absorption" when the bid keeps refreshing and the price holds. Three new measurement rows and plain-language notes like "Large sell print absorbed" and "Bid refreshing at 100.00" explain each call, and a small fix means the top-of-screen status light now honestly shows when a stream has ended instead of staying a false "live". Four of the five tape situations are now recognised; next is teaching it to call a genuinely choppy, indecisive tape "unclear", and then letting you stop watching a stock.

## What it can do today

The product lets a user watch a built-in sample stock and see a live read of its trading activity — current buy and sell prices, recent trades, named tape measurements, plain-language observations, an event log, and an overall "who's in control" call with a confidence score. It correctly reads buyers in control (green), sellers in control (red), and heavy aggression being absorbed while the price holds (amber, on both the bid and the ask side), updates live with no page reload, never fabricates a reading for an unknown stock, and keeps every on-screen number matching the underlying data exactly.

_Last updated: 2026-06-03 after iteration 5._
