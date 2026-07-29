# Phase goal-desk-iter-16 — Implementation Summary

**Phase:** goal-desk-iter-16
**Date:** 2026-07-29
**Written by:** developer

---

## Features Implemented

- **Open any recorded screen snapshot by its own identity, not just by date.** Previously, if two
  screens had ever been recorded for the same date (for example, one recorded before a data-quality
  repair and one after), only the newer of the two could be opened — the older one was listed in
  the history but could never actually be viewed. Now every history entry can be opened
  individually, including an older same-date recording that a newer one has superseded.
- **Each Screen History entry now shows exactly when it was recorded**, not just which trading date
  it covers. Two entries for the same date now read distinctly at a glance.
- **The Provenance panel now names the exact snapshot on screen** (its own identifier and the exact
  time it was recorded), and its default description now honestly says "the most recently recorded
  screen" rather than implying it is simply "the latest date's screen" — an important distinction
  now that two same-date recordings can exist.
- **Data-integrity problems in three of the operational ledgers are now visible on screen instead of
  being silently swallowed.** If a Top-up Run record or a Coverage-Index Reconciliation run record
  file on disk ever fails its own integrity check (corrupted or tampered), the operator now sees a
  plain note naming exactly which file failed and how many — the same disclosure the Screen History
  and Universe ledgers already had internally, now surfaced to the operator for these two as well.

## Changed Behavior

- **Screen History row selection**: Previously, clicking a history row selected by date; if two
  entries shared a date, clicking either row displayed the same (newer) recording, and highlighting
  could not distinguish them. Now, clicking a row opens that exact recording by its own identity,
  and only that row is highlighted — even when another row shares the same date.
- **Provenance panel's default description**: Previously implied "the latest screen date" is what's
  shown by default. Now explicitly says "the most recently recorded screen," which is the accurate
  description once two same-date recordings can exist.
- The existing `?date=` lookup (used internally, unrelated to the operator-visible history list)
  behaves exactly as before — no observable change there.

## Backend-Only Items

- None. Both backend changes (the new `?id=` lookup and the two ledgers' integrity-error
  disclosure) are fully wired into the `/desk` page this iteration.

## Incomplete Items

- **A "Universe" ledger integrity-disclosure line was named in the original plan but does not
  apply — there is no Universe ledger list in the app to add it to.** On inspection, the app has
  never displayed a list of registered universe snapshots; it only shows a single identifier for
  the current universe inside the Provenance panel. The plan's premise that this existed was
  checked directly against the code and found to be incorrect, so building an entirely new page
  section for it was out of scope for this change (it would have been a much larger, undocumented
  addition). This is flagged for the team to decide whether it's worth doing as a future,
  explicitly-scoped addition.

## Config and Environment Changes

- None. No new environment variables, no new configuration fields, no migration. The system's
  configuration fingerprint is unchanged (still `08e471b10130e1e2`), confirming nothing about how
  results are computed changed — only what is already-recorded data is now reachable/visible.

## Known Limitations

- If every recorded screen snapshot were simultaneously corrupted (an extremely unusual situation —
  none currently exist in this state), the Screen History section — and its integrity-error note —
  would not be shown at all, because the page falls back to its existing "no screen computed yet"
  message in that case. This is a pre-existing page behavior, not something this change introduced,
  and does not affect the two ledgers (Top-up Runs, Index Reconciliation) whose disclosure lines are
  always shown independent of screen state.
- The new "most recently recorded" description in the Provenance panel only appears in the default
  view (when no history entry has been manually selected) — this matches what was actually
  requested.
