# Phase N — Implementation Summary

**Phase:** goal-tape_to_profit_support_resistence-iter-4
**Date:** 2026-07-06
**Written by:** developer

---

## Features Implemented

- **A second trading strategy, `structure_tape`, alongside the original `v1`**: this is the first
  strategy that ties the tape read to price structure instead of reading the tape in a vacuum. It
  only opens a simulated trade where price sits at (or has just moved through) one of the
  support/resistance levels the product already computes, AND the live tape read agrees at that
  moment — either the tape shows that level being defended (price gets rejected, so the trade fades
  back the other way) or shows real, sustained price impact carrying straight through it (the trade
  follows through in that direction). Every past trade the strategy would have simulated records
  exactly which level (its price, timeframe, and A/B/C conviction grade) triggered it.
- **A visible list of the registered strategies and today's "champion"**: a new read endpoint
  (`GET /research/strategies`) and a matching AI-tool entry list both strategies (`v1` and
  `structure_tape`) in order, plus which one is currently the measured champion. This mirrors the
  existing indicator-profile list exactly.
- **The existing backtest tool now accepts the new strategy**: running a backtest can now be
  pointed at `structure_tape` (previously only `v1` was accepted), and the resulting report looks
  exactly like every other backtest report — simulated return in both R-multiples and dollars,
  beside the same random-chance comparison, with the "simulated, not real results" disclaimer
  attached as always.

---

## Changed Behavior

- **The backtest error message for an unrecognized strategy**: previously named only `v1` as the
  valid choice; now lists every registered strategy (`v1` and `structure_tape`). Purely a wording
  fix so the message stays honest now that two strategies exist — no behavior change for a request
  that already worked.

<!-- No other existing behavior changed. -->

---

## Backend-Only Items

- `GET /research/strategies` and the `structure_tape` strategy itself — no browser page exists yet
  for either. Both are reachable only through the research API and the matching AI-tool connection,
  exactly like every other research-era capability shipped so far (datasets, backtests, bar series,
  support/resistance levels). This is consistent with how the product has shipped every prior
  research capability — there is no regression here, just no new UI this iteration either.

---

## Incomplete Items

- **Class-scaled risk and position sizing** (a better-graded level getting a tighter stop, a better
  reward target, and a larger simulated size) is explicitly the NEXT iteration's work, not this
  one. This iteration's `structure_tape` trades use the exact same stop/target/size rules as `v1`.
- **Comparing `structure_tape` against `v1` on real trading history, and possibly promoting it to
  "champion"** is also explicitly the iteration after next. This iteration only registers the
  strategy and proves it arms correctly — it does not yet get measured against the real record or
  become the shown champion.

Both of the above are exactly as scoped by this iteration's plan — nothing was left half-built.

---

## Config and Environment Changes

- No new environment variables. Three new internal tuning numbers were added (how close price must
  be to a level to count, and which tape reading counts as a "level held" versus a "level broken"
  signal) — all fixed defaults, not exposed as environment variables, and none of them affect any
  existing strategy, chart, or report.

---

## Known Limitations

- There is no dedicated browser page for the strategy list or for running a `structure_tape`
  backtest yet — same situation as every other research-API-only capability shipped in this era so
  far (bar series, support/resistance levels). It is fully usable today through the API and the
  AI-tool connection.
- Every `structure_tape` result is a simulated measurement against past recorded tape, exactly like
  every other backtest in this product — never a live trade, never advice, never a promise about
  future results.
