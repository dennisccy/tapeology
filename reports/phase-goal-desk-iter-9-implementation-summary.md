# goal-desk-iter-9 — Implementation Summary

**Phase:** goal-desk-iter-9
**Date:** 2026-07-27
**Written by:** developer

---

## Features Implemented

- **"How stale is this reading?" on every Desk briefing row**: The `/desk` page's ranked table now
  has a new "basis" column. For every symbol the Desk screens, it tells you the exact date of the
  price bar that symbol's distance-to-wall and class were measured from, and how many days before
  today's screen that bar is dated — for example, "basis 2026-07-23 · 4 d before as-of". Before this
  change, a symbol measured off yesterday's close and a symbol measured off a two-week-old close
  looked identical on the ranked list; now the age is visible at a glance.
- **Full-precision detail on hover**: Hovering anywhere on a ranked row's name/symbol cell now also
  shows the exact basis date and age in the row's tooltip, alongside the distance/score/coverage
  detail that was already there.

---

## Changed Behavior

- **The Desk briefing table**: Previously showed 7 columns (symbol, side, class, distance, score,
  coverage, tick evidence). Now shows 8 — the new "basis" column is appended at the end. Nothing
  else about the table's layout, sorting, or the other 7 columns changed.
- **Screens computed before this update**: When you look at an OLDER, previously-recorded screen
  (via the Screen History list), its basis column will honestly say "basis not recorded in this
  snapshot" for every row, because that information genuinely was not captured when that screen was
  run. This is not a bug — it is the deliberate, honest behavior for records that predate this
  feature. Only NEW screens you run from today onward will show the actual dates/ages.

---

## Backend-Only Items

- None. This is a small, fully wired feature — the two new data fields (basis date and basis age)
  are computed on the backend and immediately visible on the `/desk` page; there is no backend
  capability left unexposed to the UI.

---

## Incomplete Items

- **The specific "one very fresh row and one very stale row visible together in the same screenshot"
  check** (called for in the plan as extra visual proof) was not captured by this development pass —
  it is scheduled for the next review step (browser QA), which has better tools for staged
  screenshots. This developer pass DID confirm the feature works correctly on real, current data (a
  spread from 3 days old to 14 days old was observed live), just not framed as that exact two-row
  screenshot yet.
- **A specific "hover precision" browser check** (confirming that hovering directly over the new
  basis text still shows the full tooltip, not something else underneath it) also needs the next
  review step's browser tooling — this developer pass could not exercise mouse-hover positioning
  with the tools available to it, only page content and clicks.
- **The end-to-end walkthrough recording** ("show a fresh reading and a stale reading side by side,
  in plain language") is planned as part of the next showcase step, not this development pass.

Neither of the above blocks the feature from working — both are additional confirmation steps for
the next stage of the pipeline.

---

## Config and Environment Changes

- None. No new settings, environment variables, or configuration options were added. The system's
  internal "fingerprint" (a value that must stay exactly the same all era to prove nothing about how
  results are computed secretly changed) is confirmed unchanged.

---

## Known Limitations

- If you open a screen that was recorded before today's update, its ranked rows will always say
  "basis not recorded in this snapshot" for this new detail — that information was never captured
  for those older records, and the system deliberately never fills in a guessed value for missing
  history. Only screens run from now on carry the new detail.
- The new column is descriptive only — it states a date and a day-count, nothing more. It does not
  flag a reading as "too old to trust" or suggest any action; that kind of judgment is intentionally
  outside what this system tells you (by design, this product never gives trading advice).
