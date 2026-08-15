# Project story so far

Tapeology is a research app with three screens — a Cockpit that reads the live tape as it happens, a Structure page that maps the price levels where a stock tends to bounce or stall, and a Desk that scans for chart setups and logs every signal it sees, honestly, without ever placing a real trade. This chapter, "The Referee," is teaching the product to check its own homework.

## How it has grown

Five earlier chapters built the whole working product before a pattern noticed by eye could ever be told apart from a shape imagined in noise. The Referee chapter opened by confirming nothing new existed yet and everything old still worked, then did quiet groundwork: a tool that honestly counts how much evidence exists, and a shared record shape so every logged signal and every recorded trade can be compared the same way.

It then built the actual judge — a statistics engine that decides whether a chart pattern is real evidence or just noise. Checking its own checker rather than trusting it, the team found and fixed a genuine flaw in how confident that engine was allowed to sound. Next came a way to compare every recorded signal against fair "nothing special happened" moments from the same stock, at the same time of day, measured exactly the same way as the real signal — plus more honesty fixes to the statistics engine, so it can no longer claim a more certain answer than the math allows.

This round built a permanent notebook for research questions: a person (or an automated stand-in, for now) can write a specific question down — like "does this chart pattern mean something more than chance?" — before checking whether it's true. The system stamps the exact moment it was written down, and neither the question nor that starting date can ever be edited or deleted afterward; it can only be withdrawn, and only before it has been checked for real. While double-checking this new machinery — because permanent records that can never be edited demand extra care — the team found a real hole: the starting date could quietly be backdated, which would have let old data sneak in and count as fresh proof. It was caught and fixed before anything was ever saved for real. The old three screens still work exactly as before. Next: the actual judge that compares each recorded signal to its fair comparisons and writes down one permanent verdict per question.

## What it can do today

The product lets users watch the live tape on the Cockpit, look up a stock's price map on the Structure page, and scan for chart setups on the Desk — the same three screens as before. The Referee chapter's fact-checking work is now five rounds deep, including a statistics engine, fair comparison moments, and a permanent notebook for research questions, but none of it has a page of its own yet, so there is nothing new to click.

_Last updated: 2026-08-15 after iteration 6._
