# Project story so far

Tapeology is a market-research tool that studies real price and order-flow data honestly, without ever placing a real trade or giving trading advice.

## How it has grown

Earlier chapters built a chart-watching Cockpit, a Structure page mapping price walls, a Desk page checking chart patterns against those walls, and a Referee that judges whether a trading idea really holds up over time.

This chapter, "The Rapid Microscope," is building a faster, lighter way to test small trading ideas before the careful Referee ever sees them. Early rounds added a data-readiness panel, a tick-by-tick reader of buying and selling pressure, a signal-to-activity matcher, a "Scout" screener that permanently records every idea it tests (including failures), and a "walk-forward checker" that can honestly refuse a result — "you only have 11 days of history, you need 105" — instead of hiding that answer in a private test. A safety check running alongside each round has repeatedly caught and fixed honesty bugs before they reached a real result.

Work then began on the recorder that will one day capture brand-new market data: first safe storage for extra recorded-trade detail, then the actual fetching machinery — resumable, paced chunks that pick up where they left off if interrupted.

This round built the recorder's third and most delicate piece: a "Vault" able to seal away newly recorded data the moment it arrives, so nobody — not even the product's own reports — can peek at it before it is formally released. The idea survived three rounds of independent attack in one sitting. The first attack found the vault was quietly leaking enough clues to identify a "hidden" recording elsewhere on the site; the project owner ruled to close it with disguised stand-in labels. The second found two profit-comparison reports could still read a hidden recording directly; the owner ruled to fix that too. The third, deepest attack found that simply watching which recordings are missing from the public list can reveal exactly which ones are hidden — no clues needed — and that gap is still open. The team builds elsewhere next (making sure every failed idea still gets counted honestly on the way to the judge) while the owner decides how to close it. Nothing about the Vault is visible on screen yet, and no real market data has been sealed away; everything that already worked was re-confirmed working exactly as before.

## What it can do today

The product lets users watch live and historical price charts, see mapped-out price walls, check a chart-pattern playbook against those walls, and browse the Referee's record of judged ideas. A Desk-page panel shows how much tick-by-tick market data is on hand. Behind the scenes, it also reads buying and selling pressure tick by tick, matches chart signals to that activity without peeking at the future, screens trading ideas with a tamper-evident record of every trial, and can honestly say "not enough data yet" when a result lacks enough history to be trusted.

_Last updated: 2026-08-18 after iteration 9._
