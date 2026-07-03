# goal-tape_to_profit-iter-7 — Implementation Summary

**Phase:** goal-tape_to_profit-iter-7
**Date:** 03-07-2026
**Written by:** developer

---

## Features Implemented

- **The candidate-sweep command.** Running `python -m app.research.pnl_scan --out <path>` now
  evaluates every registered candidate strategy/profile against the current champion, using the
  frozen train dataset(s) to measure performance and the frozen hold-out dataset(s) to check
  whether the result generalizes. It writes a report file listing, for each candidate: how it did
  on train, how it did on hold-out, whether it counts as a "survivor" (a genuine, validated
  improvement), and whether its train result was "robust" (consistently positive) or merely
  "speculative." Running it is completely safe to repeat — with nothing new to promote, it changes
  nothing and exits cleanly.
- **A real promotion mechanism.** When a candidate genuinely beats the champion on the hold-out
  data (not just the data it was tuned on) by enough of a margin and with enough trades to trust
  the result, the sweep now actually promotes it: it records one honest entry in the PnL ledger
  (the same ledger already visible on the Performance page and via `GET /research/pnl/ledger`)
  explaining the before/after numbers, and it moves the "current champion" pointer to the winning
  candidate. Before this iteration, the champion was a fixed, unchangeable value; now it is a real,
  moveable record that only a validated winner can change.
- **The Performance page and the MCP tools automatically show a promotion.** Because the champion
  is now read from the same live database record every time, no other page or tool needed to
  change — if a candidate is ever promoted, `/performance`, `GET /research/profiles`, and the AI
  dev-chain's MCP tools all show the new champion immediately, with zero extra work.

## Changed Behavior

- **The champion pointer on `GET /research/profiles`.** Previously this always returned a fixed,
  hardcoded value (strategy v1, profile "default"). It now reads from a real, persisted record
  that can change if a candidate is promoted. On the data shipped today, nothing is promoted, so
  the page's Performance panel looks and reads exactly as before — this is a change to *how* the
  value is produced, not to what it currently shows.

## Backend-Only Items

- **The candidate-sweep command itself** — `python -m app.research.pnl_scan --out <path>` — has no
  page or button in the product. It is a command-line tool for a researcher (human or the AI
  dev-chain) to run when they want to check whether any registered candidate has proven itself.
  This matches the plan for this iteration exactly: it is a machine/CLI capability, not meant to
  gain a UI page. Its *effects* (a promotion) ARE visible on the Performance page and via the API,
  the moment they happen.

## Incomplete Items

None — every requirement in the phase spec's Definition of Done is implemented and covered by a
passing automated test (see the dev handoff for the exact test list). On the shipped sample data,
the one existing candidate does not qualify for promotion (its results on the hold-out data are
not strong enough), so the product's visible state does not change today — this is the expected,
honest outcome per the phase spec, not a shortfall.

## Config and Environment Changes

- New setting: `promotion_min_sample_size` (default: `5`) — the minimum number of trades a
  candidate's hold-out result must have before it can even be considered for promotion. This is
  separate from the existing "insufficient sample" label setting used elsewhere, because the two
  numbers answer different questions (one is about what gets promoted, the other about what gets
  labeled on a report).
- Internal database change: the research database gained one new small internal table that stores
  the current champion. It updates automatically and safely the next time the backend starts —
  no manual step is required, and nothing in the existing data changes.

## Known Limitations

- If more than one dataset is ever registered for the training set (or the hold-out set) at the
  same time — which does not happen with the data shipped today — the sweep will still measure and
  report everything, but it will not attempt an automatic promotion in that situation; it will
  print an explanation instead of promoting against an ambiguous choice of dataset. This does not
  affect today's shipped behavior.
- On the sample data included with the product, the one existing candidate strategy does not pass
  the validation bar, so running the sweep today reports "no survivors" and changes nothing. This
  is the correct, honest behavior, not a bug — a real improvement would need to be genuinely
  better on data it was never tuned on.
