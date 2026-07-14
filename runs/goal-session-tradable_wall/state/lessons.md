# Goal Session tradable_wall — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-1 — 2026-07-14T08:25:54Z

**Verdict:** CONTINUE
**Lesson:** A daily-only committed fixture could NOT surface J-01's quality-score CRITICAL: an all-timeframe `touch_count` sum let ~70 shallow intraday 5m/1h members outscore the real 300.48–302.07 daily rejection wall (ranked it 7th of 9, off the served top-5). It only appeared under realistic multi-timeframe density on the live `.data/bars`, was caught by the pre-ship reviewer (not the tests), and the fix (count only `"1d"` members' touch, per goal.md's literal "daily touch count") needed a NEW committed multi-timeframe fixture + a regression guard that asserts a higher-raw-touch intraday band ranks BELOW the wall. Separately, `_PriorSessionBarView` fixes a non-obvious no-lookahead hazard: "prior-bar epoch + 1 day" collides with the requested session's own bar epoch for any two CONSECUTIVE sessions (real daily bars share an hour-of-day stamp; `levels.py._bars_as_of` uses one inclusive `<=` for both visibility and period-close).
**Applies to:** any iter adding a scoring/ranking/classification factor that aggregates across timeframes (J-02 reaction classification + forward returns, J-04 edge-report cells) — ship a realistic MULTI-TIMEFRAME fixture, never daily-only, and a guard that bites under intraday density; and any iter reusing J-01's morning-markup as-of resolution per session (J-02 per-session maps, J-06 cockpit as-of) must add its own consecutive-session no-lookahead test.

## iter-2 — 2026-07-14T11:06:04Z

**Verdict:** CONTINUE
**Lesson:** `setups.py` caps its reaction-classification read at the last stored bar (`min(touch_index + horizons[0], len(all_bars)-1)`), so a touch in the most-recent stored session gets a definitive `rejected`/`broke`/`chopped` label computed from a data-dependent SUB-horizon while its forward-return fields honestly report `None` — 13/801 live events (all the boundary session per symbol). This is invisible on the committed fixtures (they stop at 2026-06-30, before the recency boundary) and only surfaced on a live-store scan; it is honest about the returns but inconsistent about the label, and no committed test locks it.
**Applies to:** the J-05 iter (which first RENDERS setups events — it must resolve the contract: surface the effective horizon, flag/suppress the reaction, or exclude the event, with a boundary regression test) and any iter touching `setups.py` horizon/boundary logic. General pattern: a headline verified only on committed fixtures can hide a boundary case that only a live-store run exposes — verify recency-boundary behaviour on the populated store, not just the frozen fixture.
