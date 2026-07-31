# Phase goal-desk-iter-34 — User-Visible Changes

**Phase:** goal-desk-iter-34
**Date:** 2026-07-31
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On `/desk`, in the **Top-up Runs** panel's latest-run detail, users can now trust that the
  "newest recorded reach" line and the "Pairs recorded earlier" list never contradict each other —
  a pair whose printed date is the same calendar day as the "newest recorded reach" date can no
  longer also appear listed under "Pairs recorded earlier" (it did before this fix).
- When a run's true count of earlier-than-newest pairs exceeds 20, users now see an honest
  disclosure sentence — "showing 20 of `<true total>`" (e.g. "showing 20 of 101") — directly below
  the "Pairs recorded earlier (N)" heading, so they know the visible list has been shortened and by
  how much, instead of scrolling through an unbounded, hundreds-of-rows-long column with no
  indication it was truncated (or, previously, not truncated at all).

## What Changed in the Visible UI

- On `/desk` → **Top-up Runs** → the selected/latest run's detail panel, the "Pairs recorded
  earlier (N)" heading's count `N` is now always the TRUE total of earlier pairs — previously `N`
  was simply the length of the (unbounded) rendered list, so the heading and the list always agreed
  with each other even though the underlying grouping was wrong.
- The "Pairs recorded earlier" row list now renders at most 20 rows. On the ambient run currently
  on disk (`topup-2026-07-31-8fb5c9a1f737`), this list previously rendered 303 rows in one
  unbroken column; after this fix it renders 20 rows with the heading still reading the true count.
- A new one-line sentence — "showing `<shown>` of `<true total>`" — appears between the "Pairs
  recorded earlier (N)" heading and the row list, but ONLY when the true total exceeds 20. It uses
  the same small, muted descriptive-text styling already used for the panel's other fallback text
  (e.g. "library reach not recorded in this run"); no new color, badge, or emphasis was introduced.

## What Old Behavior Changed

- **"Pairs recorded earlier" list on `/desk`'s Top-up Runs latest-run detail**: previously, a pair
  recorded a few hours behind another pair on the SAME calendar day was still counted as "earlier"
  purely because of its own sub-day timestamp precision, even though its printed date (truncated to
  the day at render time) visibly matched the "newest recorded reach" line's own printed date —
  producing a visibly self-contradictory pair of lines/lists on the page. Now, grouping uses the
  same calendar-day precision the page already prints, so a pair dated the same day as "newest"
  can never appear under "earlier" again.
- **"Pairs recorded earlier" list length**: previously the list was unbounded — it could render
  hundreds of rows in a single scrolling column with no cap and no indication of how many there
  were beyond counting the rows yourself. Now it is capped at 20 rows, with the true total always
  visible in the heading and, when truncated, in the new disclosure sentence as well.

## Not Visible Yet

None. This iteration is a pure frontend display-logic fix (plus test-only backend changes to guard
that fix and a golden-replay-script update) — there is no new backend capability awaiting UI
wiring. Everything the code changed is directly observable on `/desk`.
