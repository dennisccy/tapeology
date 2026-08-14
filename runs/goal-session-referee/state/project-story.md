# Project story so far

Tapeology is a research app with three screens — a Cockpit that reads the live tape as it happens, a Structure page that maps the price levels where a stock tends to bounce or stall, and a Desk that scans for chart setups and logs every signal it sees, honestly, without ever placing a real trade. This chapter, "The Referee," is teaching the product to check its own homework.

## How it has grown

Five earlier chapters built the whole working product you see today — the Cockpit, the Structure page, and the Desk — including an honest paper log of chart-setup signals, all without ever placing a real trade.

But a pattern someone notices by eye is not proof it is real, and nothing in Tapeology could yet tell a genuine edge from a shape imagined in noise. The Referee chapter opened carefully, confirming first that nothing new existed yet and everything old still worked; the next two rounds built the quiet groundwork — a private tool that honestly counts how much evidence exists (including an honest admission that there still isn't enough tick-by-tick data for real tests), then a shared, detailed record shape so every logged signal and every recorded trade can be compared the same way. One honest mishap was disclosed along the way: a cleanup command that accidentally stopped an unrelated project's server, still awaiting a restart.

This round built the actual judge: the statistics engine that will decide whether a chart pattern is real evidence or just noise. It passes 77 of its own proof tests, but the team checked the checker themselves rather than trusting that, and caught a genuine flaw nobody else had found: in one of its two ways of asking "how surprising is this result?", the answer can come out more confident than it honestly should, on roughly one case in sixty for the smallest, trickiest datasets. Nothing on any screen uses this engine yet, so no one has seen a wrong number, but it must be fixed and re-proven before anything else is built on it.

Next, the team will fix that flaw, prove the fix holds, and then start looking for fair "nothing happened" moments to compare each pattern against.

## What it can do today

The product lets users watch the live tape on the Cockpit, look up a stock's price map on the Structure page, and scan for chart setups on the Desk — the same three screens as before. The Referee chapter's fact-checking work so far has no page of its own yet, so there is nothing new to click.

_Last updated: 2026-08-14 after iteration 3._
