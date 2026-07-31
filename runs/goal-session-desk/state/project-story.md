# Project story so far

Tapeology is a research tool for reading a stock's price action right now and mapping its key price levels — an honest study instrument, never a trading system.

## How it has grown

The product began as a two-page instrument — a live Cockpit and a Structure page for support and resistance — then gained a third page, "The Desk," for a daily ~100-stock screen with scan history, a chart drill-in, a top-up log, a coverage-repair button, and a read-only Claude connection. The daily scan then got its own permanent run history, so every attempt is recorded and a repeat scan on unchanged data answers almost instantly.

The team next taught the Desk to state the actual date each stock's price history reaches after a top-up. A real bug surfaced — the "newest recorded reach" line contradicted its own "pairs recorded earlier" list — and, after being delayed twice by the automated scheduler, was fixed: the panel now groups pairs by calendar day and says plainly when its list has been shortened.

The team then added a "Screen Comparison" section showing how today's screen differs from the one recorded right before it — which stocks moved rank, flipped from support to resistance, or newly entered or left the list — with honest "nothing changed" and "no earlier screen" messages. Every number was proven by hand against the frozen records.

Most recently, the team gave the Desk foresight: before you click "Run Screen" (or while reading a past screen), the page now tells you in advance whether a fresh run would reuse a screen it already has on file or need to walk the full list of about 100 stocks again — shown both for the screen currently on display and for today's date. The team re-created the product's own answers from scratch against the real records and got an exact match, including the very same screen name a fresh test run produced.

Twenty-one of the Desk's abilities are now checked and working, none broken. Two small guided-video walkthroughs are still owed (for the screen-comparison feature and for this newest one) — the abilities themselves are already proven with screenshots and hand-checked numbers, so the team does not consider the missing videos worth delaying the finish over. The team is again asking the project owner to confirm the work is finished.

## What it can do today

The product lets users run a simulated tape-reading session with live moving price bars on the Cockpit, and open a Structure page showing a stock's support and resistance on a real chart. On the Desk page, users can browse a daily ranked screen of about 100 stocks — each row showing its price range, opposite wall, level makeup, and how much history backs it, all fitting one screen with no sideways scroll — browse past scans and jump into the matching Structure chart, top up stored price history with an honest account of what was fetched, and see a permanent record of every scan and top-up ever run. They can also see how the currently displayed screen differs from the one recorded right before it, see in advance whether pressing "Run Screen" would reuse an existing scan or start a fresh one, and read Desk data through a connected Claude conversation.

_Last updated: 2026-07-31 after iteration 36._
