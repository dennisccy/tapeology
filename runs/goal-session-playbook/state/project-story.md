# Project story so far

Tapeology is a research desk for reading a stock's tape and structure — never a trading system, and never a source of advice.

## How it has grown

Before this chapter, the desk already let someone watch a simulated ticker's buy-and-sell pressure live, load a real stock's chart with support-and-resistance walls, and run a daily screen across roughly a hundred large companies with a ranked briefing. This chapter, "The Playbook," taught the desk to recognize nine classic intraday chart patterns from a well-known trading book and honestly report what happened afterward.

Round by round the desk learned five pattern families — opening-range breakouts, jump-base and drop-base breakouts, cup-and-handle, capitulation, and finally range trades and double-top/double-bottom reversals — added a "Backscan" panel to bulk-fill missing records for a whole date range in one resumable pass, and added a "Playbook Evidence" panel pooling all recorded history into honest per-pattern statistics, with thin data flagged rather than hidden. Along the way, a real safety gap was caught and closed: an automated check had briefly touched the operator's real trading records instead of a safe practice copy.

By the next round, Claude could read the pattern records and the evidence table directly (its toolset grew from 18 to 20 tools), the evidence panel began naming which batch of settings its numbers came from, and the whole product was walked end to end in a real browser with nothing broken. All ten of the chapter's planned capabilities worked — but that round paused short of calling the chapter finished, because two small rulings about pattern-detection edge cases were still waiting on the owner.

This round, the owner answered both questions, and the team wrote the rulings into the pattern rulebook in four places — a wording correction only, changing no pattern's actual behavior — then used the same ruling to ship one small new fact: a range-trade signal's detail can now also say whether the price swing leading into it turned back right at the middle of the tested range, next to the note already there. That note hasn't fired on a real example yet, so it is proven correct but not yet observed. The team also fixed two behind-the-scenes test bugs: a broken practice-copy chart that drew nothing, and an automated check that had quietly stopped checking anything real. All ten capabilities still work and both owner questions are closed, but the chapter isn't finished: Claude's read access needs a quick re-check the last round ran out of time for, a small display glitch needs a decision, and the team wants one more safeguard in place before calling this chapter done.

## What it can do today

The product lets users watch a simulated stock's live buy-and-sell pressure on the Cockpit page, and load a real company's price chart with support-and-resistance zones on the Structure page. On the Desk page, users can pick a trading day and see all nine chart patterns the desk recognizes for that day — including breakouts, cup-and-handle, capitulation, range trades, and double tops and bottoms — each checked against random-chance odds; run one bulk pass to fill in records across many days at once; and see a table of how each pattern has actually performed, with thin data honestly flagged. The connected Claude assistant can read the pattern records and evidence table directly.

_Last updated: 2026-08-12 after iteration 10._
