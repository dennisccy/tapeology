# Project story so far

Tapeology is a research app with three screens — a Cockpit that reads the live tape as it happens, a Structure page that maps the price levels where a stock tends to bounce or stall, and a Desk that scans for chart setups and logs every signal it sees, honestly, without ever placing a real trade. This chapter, "The Referee," is teaching the product to check its own homework.

## How it has grown

Five earlier chapters built the whole working product. A pattern noticed by eye is not proof it is real, though, and nothing in Tapeology could yet tell a genuine edge from a shape imagined in noise.

The Referee chapter opened by confirming nothing new existed yet and everything old still worked, then spent its early rounds on quiet groundwork: a tool that honestly counts how much evidence exists, and a shared record shape so every logged signal and every recorded trade can be compared the same way. It then built the actual judge — a statistics engine that decides whether a chart pattern is real evidence or just noise — and, checking their own checker rather than trusting it, the team caught and fixed a genuine flaw in how confident that engine was allowed to sound.

This round built the next piece: a way to compare every recorded signal against fair "nothing special happened" moments from the same stock, at the same time of day, with the same amount of trading time left, measured exactly the same way as the real signal. The team also closed one more honesty gap in the statistics engine, so it can no longer claim a more certain answer than the math allows, and it now refuses broken numbers outright instead of quietly using them. Nothing broke — the old three screens still work exactly as before. Because this new work creates permanent records that can never be edited later, the team is moving more slowly and checking itself more carefully before building further on top of it. Next: a permanent record book that writes down each question before any answer exists, so results can never be picked over after the fact.

## What it can do today

The product lets users watch the live tape on the Cockpit, look up a stock's price map on the Structure page, and scan for chart setups on the Desk — the same three screens as before. The Referee chapter's fact-checking work is now four rounds deep, including a way to compare signals against fair "nothing happened" moments, but none of it has a page of its own yet, so there is nothing new to click.

_Last updated: 2026-08-15 after iteration 5._
