# Goal Iteration 5 (J-05) — Implementation Summary

**Phase:** goal-tape_to_profit_support_resistence-iter-5
**Date:** 2026-07-06
**Written by:** developer

---

## Features Implemented

- **Class-scaled stop distance**: The `structure_tape` simulated strategy now sets a different
  stop distance depending on how convincing the support/resistance level is (its A/B/C
  "confluence class" — see prior iterations). An A-class level (the strongest agreement across
  timeframes) gets a very tight stop, about 1 basis point (0.01%) beyond the level's own price. B
  and C class levels get progressively wider stops (5 and 10 basis points), reflecting lower
  conviction. Every distance is a named, documented setting — never a number buried in code.
- **Class-scaled reward target**: Each simulated trade now also carries a take-profit target. The
  target aims for a multiple of the trade's own risk ("R"), but is capped so it never demands a
  move further than the next real opposing support/resistance level the system has already
  detected — an honest, structure-aware target rather than an arbitrary number. Better-class
  trades are given a more generous target multiple.
- **Class-scaled simulated position size**: A trade taken at a stronger (A-class) level is
  simulated with a larger notional size than one taken at a weaker (C-class) level — still purely
  a simulated, per-trade number used only to compute simulated dollars; never a real order or
  account balance.
- **Per-class performance breakdown**: The existing backtest report (already viewable via
  `GET /research/backtests/{id}` and the MCP `backtests` tool) now additionally breaks its results
  down by class A, B, and C — showing, for each class, how many trades happened and their combined
  simulated profit/loss in both "R" units and dollars. This lets an operator see, for example,
  whether tight-stop A-class trades actually perform better than the wider B/C trades, rather than
  only seeing one blended number for the whole strategy.

## Changed Behavior

- **`structure_tape` strategy trades**: Previously (as of the prior iteration), every
  `structure_tape` trade used the exact same stop, target, and size math as the older `v1`
  strategy. Now, `structure_tape` trades use their own class-aware stop/target/size math. The
  `v1` strategy itself, and the underlying live tape-reading engine, are completely unchanged —
  they were re-verified byte-for-byte identical to before this change.
- **Backtest reports**: Every backtest report (for any strategy) now includes one additional
  section showing the same performance numbers split out by class A/B/C. For the existing `v1`
  strategy (which does not use support/resistance levels at all), this section honestly shows all
  three classes as empty rather than omitting the section — a transparent "not applicable" rather
  than a missing field.

## Backend-Only Items

- Everything in this iteration is a backend/machine-readable capability only — there is no new
  screen or button. The new numbers are visible today only via the REST API
  (`GET /research/backtests/{id}`, `GET /research/strategies`) or the MCP tools an AI agent /
  automation can query. This matches the phase plan: a future "levels view" in the product UI is
  explicitly out of scope for this data-foundation era.

## Incomplete Items

- None from this iteration's assigned scope. The next iteration (not built here) is expected to
  use this class-scaled math to fairly compare `structure_tape` against the older `v1` strategy on
  held-out data and decide whether either one should become the "champion" — that comparison
  machinery itself was intentionally left untouched this time.

## Config and Environment Changes

- Three new internal settings were added (no environment variables, no user-facing
  configuration): the per-class stop distance, per-class reward-target multiple, and per-class
  simulated size multiple. All three are plain code-level defaults with written justification, not
  something an operator needs to set — they exist so the numbers are named and traceable rather
  than hard-coded inline.
- No database migration was needed.

## Known Limitations

- The "per class" breakdown is per single backtest run. Comparing the same class across a
  "training" data window and a separate "held-out" data window (to check the results aren't just a
  fluke of the training data) is the next iteration's job, not this one's — this iteration adds the
  per-class math and the per-class number, but the honest training-vs-holdout comparison for
  `structure_tape` specifically comes next.
- The class B and C examples were verified using small, purpose-built practice data (not the
  single real historical dataset already in the system, which is too short a price move to
  naturally reach a B or C level). This is a normal, disclosed testing technique — it does not
  affect how the feature behaves on real data, only how it was checked during development.
- A note carried over from the previous iteration: the rule for detecting when price "breaks
  through" a level checks the price's current position rather than watching for the exact
  crossing moment. This is a pre-existing, documented simplification unrelated to this iteration's
  work, flagged again here so it isn't lost track of before the next iteration compares strategies
  head-to-head.
