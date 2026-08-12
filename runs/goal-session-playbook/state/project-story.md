# Project story so far

Tapeology is a research desk for reading a stock's tape and structure. It is never a trading system, and never a source of advice.

## How it has grown

Before this chapter, the desk could already show a simulated ticker's live buy-and-sell pressure, chart a real stock's support-and-resistance walls, and scan roughly a hundred companies daily with a ranked briefing.

This chapter, "The Playbook," taught the desk nine classic intraday chart patterns from a well-known trading book, added a bulk "Backscan" tool to fill in missing pattern records across many days at once, and built an "Evidence" panel that pools recorded history into honest statistics rather than hiding thin data. Claude gained the ability to read the pattern records and the evidence table directly, and a real safety gap — an automated check briefly touching real trading records instead of a safe practice copy — was found and closed along the way.

The chapter paused twice near the finish line, waiting on two owner rulings about pattern-detection edge cases. Once answered, the team wrote the rulings into the pattern rulebook — wording only, never behavior — and used one of them to ship a small new fact: a range-trade signal can now say whether the price swing leading into it turned back at the middle of the tested range.

The chapter looked finished after that, but one honest gap remained: the evidence table's counts didn't explain themselves, so a thin-looking number could be misread as a small sample rather than "mostly unmeasurable." This final round closed that gap for good. The evidence table now states its own honesty up front — a new line shows how many records and which days each pooled result is built from, and new columns show how many of a pattern's signals were actually measurable versus unmeasurable. A warning box on the pattern-scan date field also now turns visibly orange on a bad date instead of staying grey. Two independent reviewers checked the finished chapter and agreed: all eleven planned capabilities work and nothing built earlier broke. Three small paperwork items, not product problems, carry into the next chapter: one earlier summary file wrongly claims a fix shipped before it did, the new orange warning box is proven correct in the code but not yet photographed, and two of this round's proof pictures show the wrong part of the screen (the features they document still pass their own checks anyway).

## What it can do today

The product lets users watch a simulated stock's live buy-and-sell pressure, chart a real company's support-and-resistance zones, and run a daily scan across about a hundred companies with a ranked briefing. On the Desk page, users can scan any trading day for nine intraday chart patterns, each checked against random-chance odds, run one bulk pass to fill in records across many days, and read an honest evidence table showing how much of each pattern's history was actually measurable and which recorded days it draws on. The connected Claude assistant can read the pattern records and the evidence table directly.

_Last updated: 2026-08-12 after iteration 12._
