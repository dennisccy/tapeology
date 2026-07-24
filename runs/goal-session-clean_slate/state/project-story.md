# Project story so far

Tapeology is a research tool for studying how prices move on the trading tape — a live/simulated Cockpit for watching price action and a Structure page for studying support-and-resistance levels — built without ever placing a real trade.

## How it has grown

Over many earlier chapters the product grew into a five-page app before the owner decided three of those pages weren't helping find a trading edge and asked for them to be removed entirely, clearing ground for a future "Desk" chapter.

This session, "The Clean Slate," is that cleanup. A stock-take pass first confirmed exactly what needed removing without touching any code; a second pass then removed the backend engine behind the old journal, replay-studies, and performance features, relocating a couple of small shared pieces of logic first and checking every number byte-for-byte before and after — invisible from the outside, since only backend plumbing changed at that point.

The cleanup then became visible: the team deleted the old journal, replay-studies, and performance pages outright (their old addresses now show the site's plain "page not found" screen), trimmed the top menu from five links down to two ("Cockpit" and "Structure"), and stripped a leftover thesis-tracking strip, hint panel, and sound toggle off the trading screen. Both charts were re-checked afterward and work exactly as before.

Most recently, the team cleaned up a piece few users ever see directly: the list of tools an outside AI assistant can use to talk to the app. Three of those tools used to point at the now-removed journal, replay-studies, and performance features and had quietly been failing for two passes running — they're now gone from the list, and every remaining tool was re-checked to confirm it still reports the exact same numbers as the website itself.

Three of the session's five goals now hold — the backend cleanup, the visible page-and-menu cleanup, and now the AI-tool-list cleanup — on top of the opening stock-take that confirmed what needed to go. Next, the team tackles the trickiest step yet: retiring some leftover internal settings and updating an internal version marker the app's saved numbers are tied to, without changing any of those numbers. A decision on a hidden "Case Studies" view — bring it back, or formally drop the idea — still awaits whoever plans that final step.

## What it can do today

The product lets users watch a simulated, live, or historical trading tape settle into a market read, with a price chart showing candles, adjustable time windows, support-and-resistance shading, and live-updating bars, plus a Structure page to load a stock and date and see its strongest price walls highlighted. It is now exactly the two-page instrument it set out to be — Cockpit and Structure, nothing else — and the tool list offered to outside AI assistants matches that same trimmed-down product.

_Last updated: 2026-07-24 after iteration 3._
