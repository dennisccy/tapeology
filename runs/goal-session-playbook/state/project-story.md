# Project story so far

Tapeology is a research desk for reading a stock's tape and structure. It is never a trading system, and never a source of advice.

## How it has grown

Before this chapter, the desk already did three things. It let someone watch a simulated ticker's live buy-and-sell pressure. It could load a real stock's chart with support-and-resistance walls. And it could run a daily screen across roughly a hundred companies with a ranked briefing.

This chapter, "The Playbook," taught the desk nine classic intraday chart patterns from a well-known trading book, built round by round. The team added a bulk "Backscan" tool that fills in missing records across many days at once, and an "Evidence" panel that pools recorded history into honest statistics, flagging thin data rather than hiding it. Along the way, a real safety gap was caught and closed: an automated check had briefly touched the operator's real trading records instead of a safe practice copy.

Claude then gained the ability to read the pattern records and the evidence table directly, and the whole product was walked end to end in a real browser with nothing broken. Still, the chapter paused twice before it could call itself finished. First, two rulings about pattern-detection edge cases needed the owner's decision. Then, once the owner answered both, two small technical loose ends remained. The team wrote the owner's rulings into the pattern rulebook, changing wording only, never behavior, and used one ruling to ship a small new fact: a range-trade signal can now say whether the price swing leading into it turned back at the middle of the tested range. That fact hasn't happened on a real example yet, so it is proven correct but not yet observed.

This final round closed the chapter. The team gave Claude's pattern-reading access its last check, confirming live that all twenty of its tools work correctly, and re-checked every other piece of the chapter to make sure nothing had quietly broken. Nothing had. Two independent reviewers checked the work and agreed: the chapter is finished. Three small items are being carried forward rather than fixed right now. A mistyped-date warning box shows the right error message, but not yet its intended orange color. One safety setting is missing from a test checklist, though nothing was actually put at risk. And a behind-the-scenes proof file for this round wrongly claims the orange-box fix already shipped — it did not, and that mistake is flagged for correction before anyone reads it as fact.

## What it can do today

The product lets users watch a simulated stock's live buy-and-sell pressure, and load a real company's chart with support-and-resistance zones. On the Desk page, users can scan any trading day for the nine intraday chart patterns the desk recognizes, each checked against random-chance odds, run one bulk pass to fill in records across many days, and see an honest table of how each pattern has performed. The connected Claude assistant can read the pattern records and evidence table directly.

_Last updated: 2026-08-12 after iteration 11._
