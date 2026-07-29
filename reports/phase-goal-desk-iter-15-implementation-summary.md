# goal-desk-iter-15 — Implementation Summary

**Phase:** goal-desk-iter-15
**Date:** 2026-07-29
**Written by:** developer

---

## Features Implemented

- **"History" column on the Desk briefing.** Every ranked row on `/desk` now shows how many
  completed daily trading sessions its wall measurement was based on, and the date it started from
  — for example, `history 500 sessions · from 2024-07-25`. This lets the operator see, at a glance,
  whether a name's wall was measured from a deep, well-established price history or from a thin,
  recently-fetched slice, without clicking through to the Structure page. Hovering over a row's
  symbol shows the same detail (full precision) in the existing pop-up tooltip.
- **Honest gap for older screens.** Briefings computed before this update simply don't have this
  information recorded — those older rows show "history not recorded in this snapshot" instead of
  a made-up value. New screens the operator runs from today onward will always carry it.

## Changed Behavior

- **`/desk` ranked table**: previously showed symbol, side, class, distance, score, coverage, tick
  evidence, and basis. Now also shows the new "history" column. No existing column, button, or
  section changed — the table is simply one column wider.

## Backend-Only Items

- None. This iteration is a small, fully-wired disclosure feature — both the underlying computation
  and the on-screen column shipped together.

## Incomplete Items

- None from this iteration's scope. The two new pieces of information (session count, start date)
  are recorded on every NEW screen and shown on the page exactly as specified.

## Config and Environment Changes

- None. No new settings, no new environment variables, no database changes. The product's internal
  "fingerprint" (a technical signature proving nothing about how existing numbers are computed
  changed) is verified unchanged.

## Known Limitations

- Older, already-recorded briefings will always show "history not recorded in this snapshot" for
  this new column — this is intentional (the system never rewrites or backfills a past record) and
  matches how the "basis" column already behaves for briefings recorded before it was added.
- This is a read-only, informational addition. It does not change which names rank where, and it
  does not add any new button or action — it is purely something new to look at on a row you were
  already seeing.
- A live check against the real, currently-running data confirmed the feature genuinely produces a
  wide range of values today (one name with as few as 27 recorded sessions, many with roughly 500)
  — so the new column will show a genuinely useful contrast the first time an operator runs a fresh
  screen after this update ships.
