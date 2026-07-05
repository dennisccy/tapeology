# goal-tape_to_profit-iter-8 — Implementation Summary

**Phase:** goal-tape_to_profit-iter-8
**Date:** 05-07-2026
**Written by:** developer

---

## Features Implemented

- **The baseline-edge report command.** Running `python -m app.research.edge_report --out <path>`
  now measures the current champion strategy — today "strategy v1 on profile default" — across
  every dataset that has ever been recorded, and writes a report answering one question honestly:
  does the tape read actually carry a positive, disciplined edge, dataset by dataset, or not? For
  every dataset it shows the champion's result (in R-multiples and dollars, alongside how many
  trades that result is based on) next to a random-entry comparison line, and it ranks the datasets
  best-to-worst within the training data and, separately, within the held-out data (the two are
  never mixed together). A dataset only earns a "positive edge" mark on the held-out side, and only
  when the result is genuinely positive, has enough trades to be trustworthy, and beats the random
  comparison — not merely because the sign looks good.
- **An honest "no edge found" outcome, not a forced answer.** If nothing clears that bar — including
  the case where no datasets are recorded yet at all — the report says so explicitly ("no
  positive-edge dataset") and still exits cleanly. Nothing is invented to make the report look more
  favorable than the data supports.
- **Completely safe to re-run, and to run at any time.** This command changes nothing else in the
  product: it does not touch the recorded datasets, the running champion, or the performance
  history ledger. Running it twice in a row on the same data produces the exact same report,
  byte for byte.

## Changed Behavior

None. This is a brand-new, additive command; nothing that already existed in the product changed
behavior. The cockpit, the journal, the studies page, and the Performance page all look and work
exactly as before.

## Backend-Only Items

- **The baseline-edge report command itself** — `python -m app.research.edge_report --out <path>` —
  has no page or button in the product. It is a command-line tool for a researcher (human or the AI
  dev-chain) to run whenever they want an honest read of whether the champion is actually working
  across a library of recorded market windows. This matches the plan for this iteration exactly: it
  is a machine/command-line capability, not meant to gain a UI page this iteration.

## Incomplete Items

None against this iteration's own scope — every requirement in the phase spec's Definition of Done
is implemented and covered by a passing automated test (see the dev handoff for the exact list).

One larger, deliberately-deferred piece of work belongs to the operator, not to this iteration: the
underlying vision is to eventually measure the champion across a *real*, diverse library — several
different stocks, each across more than one kind of trading session — which requires the operator's
own Alpaca market-data credentials to record. That real-data recording step is out of scope for this
iteration by design (the phase spec calls it out explicitly as a separate, later, operator-run
action); this iteration built and thoroughly verified the *report itself*, keeping it fully testable
today using the practice data already in the product (no credentials required to prove it works).

## Config and Environment Changes

None. No new settings were added, and the one existing "minimum sample size" setting (already used
elsewhere to decide when a result has enough trades to trust) was reused rather than duplicated,
since it was designed to answer exactly this kind of question already.

## Known Limitations

- On the practice data included with the product today, the report honestly finds no dataset that
  clears the positive-edge bar — this is the correct, disclosed outcome (not a bug), and matches
  what the earlier PnL history already shows for this same champion on this same data.
- The report is a file you generate by running a command; it does not (yet) have its own page in
  the product. Its numbers are drawn from the exact same underlying records the Performance page
  already shows, so nothing about it is hidden or computed a second, different way — it is simply
  not yet presented as a page of its own.
