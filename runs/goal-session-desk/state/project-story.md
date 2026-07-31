# Project story so far

Tapeology is a research tool for reading a stock's price action right now and mapping its key price levels — an honest study instrument, never a trading system.

## How it has grown

The product began as a two-page instrument — a live Cockpit and a Structure page for support and resistance — then gained a third page, "The Desk," for a daily ~100-stock screen with scan history, a chart drill-in, a top-up log, a coverage-repair button, and a read-only Claude connection. The team then gave the daily scan its own permanent run history, so every scan attempt is recorded and a repeat scan on unchanged data answers almost instantly.

The next idea was to have the Desk tell the operator the actual date each stock's price history reaches after a top-up. Built and tested against a real 404-pair top-up with zero disagreements, a closer look then caught a real bug: the page's "newest recorded reach" line disagreed with its own "pairs recorded earlier" list, which also ran to hundreds of rows instead of a short one. A fix round was twice shortened by the automated scheduler before it finally landed: the panel now groups pairs by calendar day and honestly discloses when its list is shortened ("showing 20 of 101").

Most recently, the team added a brand-new feature: a "Screen Comparison" section on the Desk page that shows how today's screen differs from the one recorded right before it — which stocks moved rank, flipped from support to resistance, or newly entered or left the list, row by row, with an honest "nothing changed" message when two screens are identical, and an honest note on the ledger's very oldest screen ("no earlier screen to compare against"). The team proved every number by hand, re-deriving the whole comparison from the frozen record files and getting an exact match, and re-checked all of the Desk's other older abilities to make sure nothing broke. The one thing still owed is a short guided film demonstrating the new section — the product itself is proven and working, only the recording is missing, and the team does not consider that worth delaying the finish over.

With this new feature, twenty of the Desk's abilities are now checked and working, none of them broken. The team is again asking the project owner to confirm the work is finished, with a handful of small, optional wording notes left over — none of them worth another round.

## What it can do today

The product lets users run a simulated tape-reading session with live moving price bars on the Cockpit, and open a Structure page showing a stock's support and resistance on a real chart. On the Desk page, users can browse a daily ranked screen of about 100 stocks — each row showing its price range, opposite wall, level makeup, and how much history backs it, all fitting one screen with no sideways scroll — browse past scans and jump into the matching Structure chart, top up stored price history with an honest account of what was fetched, and see a permanent record of every scan and top-up ever run. They can also see, for the screen currently on display, exactly how it differs from the screen recorded right before it, and read Desk data through a connected Claude conversation.

_Last updated: 2026-07-31 after iteration 35._
