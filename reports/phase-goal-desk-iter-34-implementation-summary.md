# goal-desk-iter-34 — Implementation Summary

**Phase:** goal-desk-iter-34
**Date:** 2026-07-31
**Written by:** developer

---

## Features Implemented

- **Consistent "recorded earlier" listing on the Desk Top-up Runs panel**: the panel that shows
  when the tool last recorded price history for each stock/timeframe now agrees with itself. Before
  this fix, the panel could say "newest recorded reach: 2026-07-30" on one line and then, right
  below it, list pairs "recorded earlier" that were ALSO dated 2026-07-30 — a visible contradiction.
  Now, anything dated on the same day as the newest reach is correctly grouped with it and never
  shown as "earlier."
- **Honest truncation notice**: if more than 20 pairs are genuinely earlier than the newest date,
  the list now shows only the first 20 and adds one plain sentence — "showing 20 of 101" (the exact
  numbers depend on the current data) — so the operator knows the list was shortened and by how
  much. Previously the list had no limit and could run to 300+ rows in one unbroken column.

---

## Changed Behavior

- **Top-up Runs "Pairs recorded earlier" list**: Previously, this list grouped pairs by their exact
  down-to-the-second recorded timestamp, so pairs recorded on the same calendar day but a few hours
  apart were split between "reaches the newest date" and "recorded earlier" — an internally
  contradictory display. Now it groups by calendar day only (matching what's actually printed on
  screen), so same-day pairs are never split apart, and the list is capped at 20 rows with an honest
  count of how many more exist.

---

## Backend-Only Items

None. This iteration is a frontend display fix plus test coverage; no backend code changed.

---

## Incomplete Items

- The formal `[NEW]`-flagged walkthrough recording (a short guided video/screenshot tour of this
  fix) has not been produced yet — that is a separate, later step in the pipeline and is expected to
  run against the now-fixed page.
- One edge case (a run where the "earlier" list genuinely has 20 or fewer pairs) was not observed
  live on today's real data, because the current recorded run happens to have 101 earlier pairs
  (above the 20-row limit). This case was checked in isolated test code instead, and is a
  straightforward consequence of the same fix, not a separate risk.

---

## Config and Environment Changes

None. No new environment variables, config fields, or migrations. The application's internal
"fingerprint" (a value that must never change unless explicitly intended) was checked and confirmed
unchanged: `08e471b10130e1e2`.

---

## Known Limitations

- This fix only changes how the "Pairs recorded earlier" list is grouped and displayed. It does not
  change what data is stored or how it is fetched — the underlying records were already correct;
  only the on-screen grouping was wrong.
- The golden "replay script" used for automated regression checks (a scripted walk-through that
  used to check for one specific, now-fixed, incorrect row of data) has been updated to check for
  stable wording instead of exact dates/counts, so it will keep working correctly even as new data is
  recorded in the future.
