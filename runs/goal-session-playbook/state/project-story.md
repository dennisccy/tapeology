# Project story so far

Tapeology is a research desk for reading a stock's tape and structure — never a trading system, and never a source of advice.

## How it has grown

Before this chapter began, the desk already let someone watch a simulated ticker's buy-and-sell pressure live, load a real stock's chart with support-and-resistance walls drawn on it, and run a daily screen across roughly a hundred large companies with a ranked briefing and forward-looking return numbers. This chapter, nicknamed "The Playbook," teaches the desk to recognize classic intraday chart patterns from a well-known trading book, record every time one shows up, and honestly report what happened afterward, with no predictions or advice attached.

The opening rounds built the plumbing: a checkup confirmed everything already shipped still worked, the desk then learned to spot and permanently record its first pattern (a clean opening-range breakout, with an honest note whenever there wasn't enough history to say), and after that it learned to measure what happened afterward using the desk's own trusted measuring rules — though only reachable through a technical back door at that point.

The fourth round put the Playbook in front of the person using the product for the first time: the Desk page gained a "Playbook Signals" section — pick a date, press Run Playbook, and read a table of the patterns found, what happened afterward next to a random-chance comparison, and honest messages for "nothing computed yet," "already running," and closed-market days.

The fifth round taught the desk three more patterns: a Jump-Base Explosion (a tight pause after a sharp move up, then another breakout), its downside mirror the Drop-Base Implosion, and a Cup and Handle (a rounded dip-and-recovery, then a small pullback, then a breakout). A careful second check caught and fixed a real problem before anyone saw it: a downside pattern was briefly labeled with the wrong shape word.

The sixth round added a fifth pattern, Capitulation — a sharp panic decline that reverses — plus, for the first time across any pattern, a "recent climax" tag marking any signal that fires shortly after this kind of reversal. The sentence describing the section, and the page's own wording, were also widened to finally name all five patterns instead of just the first one, closing a gap left over from the round before. A careful review of the new detection code found nothing broken, but flagged that two small rules about how the new pattern measures itself were written straight into the code rather than into the written rulebook first — a paperwork gap, not a product bug, scheduled to close alongside the next pattern family (range trades and double-top/double-bottom), which is next up for a deeper, more careful build round.

## What it can do today

The product lets users watch a simulated ticker and see whether buyers or sellers are in control on a live price chart, load a real company's stock chart with support and resistance zones drawn on it, and run the desk's daily screen for a ranked briefing with forward-looking return numbers and past runs. It also lets users open the Desk page, pick a date, and see five kinds of chart pattern the desk found for that day — opening-range breakouts, Jump-Base Explosions, Drop-Base Implosions, Cup and Handles, and now Capitulation reversals — each measured for what happened afterward against a random-chance baseline, with any pattern firing soon after a sharp reversal now flagged as a "recent climax."

_Last updated: 2026-08-11 after iteration 5._
