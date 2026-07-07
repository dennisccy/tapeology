# goal-structure_ui-iter-2 — Implementation Summary

**Phase:** goal-structure_ui-iter-2
**Date:** 2026-07-07
**Written by:** developer

---

## Features Implemented

- **Strategy registry view**: on the existing Structure page, you can now see the two trading
  strategies the system knows about (`v1` and `structure_tape`) side by side, each shown as a card
  with its entry rule, its exit rules, and — for `structure_tape` only — three small tables showing
  how its stop distance, reward target, and simulated position size scale up for a stronger (A-class)
  support/resistance level versus a weaker one (B or C class).
- **Champion badge**: a small panel shows which strategy/profile pair is currently the "champion" —
  today that is the founding pair, `v1` on the `default` profile — plus a one-line note confirming
  this agrees with the same information shown on the Performance page (both come from the exact same
  underlying record, so they should always agree; the note makes that agreement visible rather than
  just assumed).
- **Honest "can't load" state**: if the backend is down or the registry can't be reached, the page
  shows a clear message saying so instead of a blank space or a guessed answer.
- This section appears automatically when you open the Structure page — there is nothing to click or
  configure to see it.

---

## Changed Behavior

None. This iteration only adds a new section to an existing page; nothing that previously worked
now behaves differently.

---

## Backend-Only Items

None. Both pieces of information this section shows (the strategy registry and the current
champion) were already fully available on the backend before this iteration (built and tested in an
earlier iteration) — this work only makes them visible in the app for the first time.

---

## Incomplete Items

None from this iteration's own scope. Two items are explicitly deferred to later work, as planned:

- **Side-by-side backtest comparison** of `structure_tape` versus `v1` (running both strategies and
  comparing results on screen) is a separate, larger piece of work planned for a future iteration —
  it was intentionally not started here.
- **Re-verification of the prior iteration's chart empty-state fix**: a fix from the previous
  iteration (making sure the price chart shows a clear "no data" message instead of a blank box when
  there's nothing to draw) was confirmed still in place by reading the code, but the formal,
  independent browser check of that fix is a separate step in the pipeline that runs after this one.

---

## Config and Environment Changes

None. No new environment variables, settings, or database changes.

---

## Known Limitations

- The "champion agreement" note has a built-in safety message for the case where the two sources of
  the champion ever disagreed — but that situation cannot actually happen with how the system is
  built today (both pieces of information come from the exact same stored record). It's there as an
  extra safety net, not because a disagreement is expected.
- One strategy (`v1`) has two additional internal stop-loss settings that are not shown on its card,
  because none of the planning documents for this iteration asked for them to be displayed — only
  the fields explicitly called for (entry rule, exit rules, and the class-based tables for
  `structure_tape`) are shown, so both cards show a consistent, comparable set of information.
- No new automated test file was added for the new data-fetching function, because this project's
  frontend has no automated unit-test setup (confirmed by checking for one) — the equivalent
  existing function it mirrors was verified the same way. Instead, this was checked by hand: the
  backend was intentionally turned off while the page was open, and the page correctly showed an
  honest "can't load" message rather than an error or blank section.
