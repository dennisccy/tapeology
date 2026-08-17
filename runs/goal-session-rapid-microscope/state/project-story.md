# Project story so far

Tapeology is a market-research tool that studies real price and order-flow data honestly, without ever placing a real trade or giving trading advice.

## How it has grown

Earlier chapters built a chart-watching Cockpit, a Structure page mapping price walls, a Desk page checking chart patterns against those walls, and a Referee that judges whether a trading idea really holds up over time.

This chapter, "The Rapid Microscope," builds a faster, lighter way to test small ideas about price moves before the slow, careful Referee ever sees them. It opened by confirming everything already shipped still worked, then added a "Microscope Readiness" panel on the Desk page and a tick-by-tick reader of buying/selling pressure, price-response speed, and quote thinning across every recorded trading day.

A behind-the-scenes matcher then paired recorded chart signals and price-wall touches with the tick-by-tick activity happening at that same moment. Next came the "Scout," a screener that tests candidate trading ideas against the tick data and permanently records what happened to every one it tries, including the ones that fail — an independent check caught and fixed four subtle ways that permanent record could have protected itself less well than promised.

This latest step built the "walk-forward checker" — the piece that decides whether a research result is trustworthy enough to ever count. It splits trading history into rolling test windows, keeps a tamper-evident log of every one, and honestly refuses a verdict when there isn't enough evidence rather than guess. Run for real against 154 days of the desk's own history, it produced 5 test windows: 3 said "not enough data yet," and the overall answer honestly refused too. An independent check caught and fixed three more subtle bugs first, including one where pressing "run" twice would have quietly counted the same evidence twice. Two small pieces are still unfinished — marking the old tick-data days as "already looked at," and switching on an existing safety refusal — so this step counts as mostly done rather than fully done. The routine safety check of every already-working screen was again skipped by mistake and needs to actually run next round. Next: close those two loose ends, then start building the recorder that captures brand-new market data nobody has looked at yet.

## What it can do today

The product lets users watch live and historical price charts, see mapped-out price walls, check a chart-pattern playbook against those walls, and browse the Referee's record of judged ideas. A Desk-page panel shows how much tick-by-tick market data is on hand. Behind the scenes, it also reads intraday buying/selling pressure, matches chart signals to that activity, screens trading ideas with a tamper-evident record of every result, and — new this round — checks whether a result is trustworthy enough to count, though none of that last group has its own screen yet.

_Last updated: 2026-08-17 after iteration 5._
