# goal-structure_ui-iter-3 — Implementation Summary

**Phase:** goal-structure_ui-iter-3
**Date:** 2026-07-07
**Written by:** developer

---

## Features Implemented

- **Strategy comparison, on screen**: On the Structure page, you can now pick a dataset that has
  already been recorded, click "Run comparison," and watch the app run both trading strategies —
  the original `v1` and the newer `structure_tape` — over that data as a background research job.
  When it finishes, you see both strategies' results side by side: how many trades each one made,
  what it returned (measured two ways — in "R" units and in simulated dollars), what fraction of
  trades were winners, and how deep its worst losing streak went.
- **A breakdown by confidence level**: Below each strategy's headline numbers, a small table
  breaks the same results down by the A/B/C confidence grade of the price level each trade was
  based on (A being the strongest). Wherever a grade has too few trades to draw a real conclusion
  from, the app says so plainly ("insufficient sample") right next to the number, instead of hiding
  it or presenting it as more reliable than it is.
- **Always-visible honesty labels**: Every set of results carries the same reminder wherever
  simulated money figures appear: this is a simulated measurement of the past, not a live result and
  not a prediction. This text comes directly from the same backend source used everywhere else in
  the app, so it can never drift out of sync.
- **The "champion" is shown, and protected**: A small panel confirms which strategy is currently the
  app's reigning champion (today, that's `v1`) and makes clear that running a comparison never
  changes this — nothing on this screen can promote a strategy. A "founding baseline" panel shows the
  very first recorded result for reference.
- **Honest handling of every gap**: If no datasets are recorded yet, if a comparison is still
  running, if one side fails or is cancelled, or if the app briefly loses contact with its backend
  server, each of those situations gets its own clear, distinct message. Nothing is ever
  invented or shown as a false success.

---

## Changed Behavior

- **Structure page header**: The short description at the top of the Structure page now mentions
  all three of its sections (levels & zones, the strategy registry, and the new comparison) instead
  of only describing the first one.
- **Project README**: The write-up of the Structure page was updated to describe the comparison
  capability, and a stale one-section description was corrected to describe all three sections.

None if no existing behavior changed — no existing feature's behavior was altered; this is purely
additive.

---

## Backend-Only Items

None. This iteration deliberately made **zero backend changes** — the comparison, the results, the
per-confidence-grade breakdown, and the honesty labels were all already fully computed and served
by the backend from earlier work (confirmed directly against the running server before starting).
This iteration only builds the screen that shows them.

---

## Incomplete Items

Everything in the phase spec is implemented and confirmed working with real, live data. A small
number of rarer situations are built and ready but were not individually demonstrated live this
pass, because reproducing them safely needs either a very precisely timed action or a specially
isolated test setup rather than the normal running app:

- A backtest failing partway through, or being cancelled partway through (both are fully built —
  each shows its own distinct message — but reproducing them live needs deliberately interrupting a
  run at just the right moment).
- The "no datasets recorded yet" message (built and correct, but this project's current data
  already has several datasets recorded, so seeing the truly-empty version live needs a fresh,
  empty setup).
- The message that appears if the connection drops partway through watching a comparison run (built
  and correct; reproducing it live needs disconnecting the server mid-run rather than beforehand).

These will be exercised and confirmed independently by the QA step that follows.

---

## Config and Environment Changes

None. No new environment variables, settings, or database changes were introduced.

---

## Known Limitations

- On the sample data currently loaded on this machine, `structure_tape` (the newer strategy) finds
  no trades to make at all when compared against the champion. This is not a bug — it is the honest,
  expected result on this particular sample data, because that data does not yet include the kind
  of detailed price-history recording `structure_tape` needs to find its setups. The app shows this
  plainly (as "no trades") rather than hiding it or making up a result.
- The comparison always runs both strategies fresh when you click the button — there is no way to
  cancel a comparison from this screen (only to wait for it, or to see honestly if it fails). This
  matches what the current phase asked for; a cancel button was not part of this iteration's scope.
