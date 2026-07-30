# goal-desk-iter-23 — Implementation Summary

**Phase:** goal-desk-iter-23
**Date:** 2026-07-30
**Written by:** developer

---

## Features Implemented

- **Wall-composition disclosure on the Desk briefing**: Every row on the `/desk` ranked table now
  shows a new "levels" column telling you how many price levels the row's selected wall is actually
  built from (e.g. "155 levels"), how those levels break down by timeframe (e.g. "1d 68 · 1h 57 ·
  4h 19 · 1w 11"), and whether the wall sits at a round number — the exact same detail `/structure`
  already shows for the same wall, now visible without leaving the briefing. Before this change,
  two rows both reading "support · Class A · 0.00 bps" could be built from a single touch or from
  hundreds of them, and the briefing had no way to tell you which.

## Changed Behavior

None. This is a pure addition — every existing column, every existing ranking, and every existing
number on `/desk` behaves exactly as before.

## Backend-Only Items

None. The three new values are computed on the backend but are also fully wired into the `/desk`
page this same iteration — nothing is backend-only.

## Incomplete Items

None. Every item in the iteration spec was implemented and tested.

## Config and Environment Changes

None. No new settings, no new environment variables, no new configuration of any kind — the
project's core version-pin number (`config_fingerprint`) is unchanged.

## Known Limitations

- This new "levels" column only appears on screens computed AFTER this update. Any screen snapshot
  that was already saved before today will keep showing the honest message "composition not
  recorded in this snapshot" for this one column — old, already-saved screens are never rewritten
  or backfilled, by design (this project never silently edits a saved record).
- The full visual check (a screenshot proving the new column is legible in a real browser, plus a
  recorded walkthrough video) is done in the next pipeline stage (QA), not in this implementation
  step. This step verified the code compiles, all automated tests pass, and both the backend and
  the website start up and respond correctly.
