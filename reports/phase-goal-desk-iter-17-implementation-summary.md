# Phase goal-desk-iter-17 — Implementation Summary

**Phase:** goal-desk-iter-17
**Date:** 2026-07-29
**Written by:** developer

---

## Features Implemented

- **Reference-close disclosure on the Desk ranked table**: every ranked row on `/desk` now shows a
  new "band" column that displays the exact price ("close") the row's tradable wall was measured
  against, right next to the price range that wall spans. Previously an operator (or a Claude/MCP
  reader of the screen data) could only see the band's distance in "basis points" — a unit-less
  number that required inverting arithmetic to figure out whether the price was actually inside the
  band or short of it. Now the raw price and the band range are shown side by side, so "the price is
  inside the wall" is a fact you can read directly, not a calculation you have to do yourself.
- **Same disclosure in the hover tooltip**: hovering over a ranked row's symbol shows the same
  close/band detail at full precision, alongside the other measurement details already shown there
  (distance, score, basis date, history depth).

---

## Changed Behavior

- **The ranked table on `/desk` grows from nine columns to ten.** Every other column is unchanged.
- **New screens computed from today forward will carry this new "close" value.** Screens computed
  before this change will not — those rows honestly show "close not recorded in this snapshot"
  instead of guessing or backfilling a value. This matches how the two previous similar additions
  (the "basis" and "history" columns) already behave.

---

## Backend-Only Items

None — the new field is fully wired to the UI in this same iteration (both the new table column and
the hover tooltip).

---

## Incomplete Items

- **A screenshot showing a real example of one price sitting inside its band and one sitting outside
  it** was not captured by this dispatch. All screens currently on record predate this change, so
  right now every row on the live `/desk` page shows the honest "not recorded" message — there is
  nothing to screenshot yet. Capturing a live example requires running a brand-new screen
  computation, which this iteration's rules restrict to an isolated test environment (never writing
  to the real, shared data store) — that step is expected to happen in a later stage of the pipeline
  (browser testing / demo recording), not during this implementation step. The underlying logic
  itself (a price sitting exactly on the edge of its band vs. clearly outside it) is fully covered
  by automated tests, so there is no doubt about correctness — only the live screenshot is
  outstanding.

---

## Config and Environment Changes

None. No new environment variables, no new configuration fields, no database migration. The
project's internal "fingerprint" (a value that changes only when the underlying computation logic
changes) is confirmed unchanged.

---

## Known Limitations

- Rows from screens computed before this update will never show the new close/band detail — this is
  intentional (the project's data is append-only and never rewritten after the fact), and the page
  makes this honest by showing a plain explanatory message rather than a blank or a guessed number.
- No new button, filter, or control was added — this is purely a new piece of information shown
  alongside data the page already displays.
