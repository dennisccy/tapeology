# Phase goal-desk-iter-19 — User-Visible Changes

**Phase:** goal-desk-iter-19
**Date:** 2026-07-29
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None. This iteration adds no new capability, no new page, and no new user action. It corrects the
computed VALUE of a field the `/desk` page has rendered since iter-18 (`opposite`) — it does not add
anything a user could not already do.

---

## What Changed in the Visible UI

- Nothing changed in the UI's structure, labels, or layout — no new column, no new tooltip line, no
  new button, no navigation change. The `/desk` ranked table's "opposite" column (header text
  "opposite") and its per-row cell (`opposite <side> <class> <low>–<high> · <distance> bps`, or the
  honest "no band on the other side" / "opposite wall not recorded in this snapshot" states) render
  in exactly the same place, with exactly the same text format, as they did after iter-18.
- What DOES change, on a `/desk` screen computed for the first time after this fix ships: on any row
  where two candidate walls exist on the far side of price and the closer one is lower-graded than
  the farther one, the "opposite" cell now names the closer wall instead of the farther, higher-graded
  one. On real production data checked during this iteration, this affects a minority of rows (2 of
  63 real symbols measured at the prior iteration's audit) — most rows are unaffected because they
  either have only one candidate wall on the far side, or their nearest wall already happens to be the
  highest-graded one.
- The row's hover tooltip (opened by hovering a row's symbol, which is also the drill-in link into
  `/structure`) is visually and structurally unchanged — it still shows the same composite line
  including the `bands by class A n · B n · C n · unclassified n` breakdown added in iter-18. Its
  content is unaffected by this fix (it lists per-class band counts, not the selected opposite band).

---

## What Old Behavior Changed

- **`/desk` "opposite" column selection rule, on newly computed screens only**: previously, when a
  row had more than one candidate wall on the side of price opposite its own selected band, the
  column named the highest-graded (best band-class) wall on that side — even when a closer, lower-
  graded wall existed. Now it names the wall genuinely nearest to price by distance, using the band
  class only to break an exact-distance tie.
  - Concrete real-data example (from this iteration's own verification against the live historical
    data store): a HONA row's "opposite" cell previously read `opposite ... Class A ... 336.96 bps`;
    the next time a screen is computed for that symbol under the same conditions, it will instead
    read `opposite ... Class B ... 153.67 bps` — a wall genuinely more than twice as close. A META
    row similarly moves from a Class A wall 232.58 bps away to a Class C wall 92.05 bps away.
  - **Important caveat for testers**: this only applies going forward. Any screen snapshot already
    recorded before this fix — including anything already stored in the "Screen History" list on
    `/desk` — is append-only and keeps exactly the value it originally recorded. Re-opening an
    already-recorded old screen from Screen History will still show the OLD (pre-fix, class-first)
    selection, by design; only a freshly computed screen shows the corrected value. Do not treat an
    unchanged old history entry as a regression.

---

## Not Visible Yet

None. There is no backend capability introduced by this iteration that lacks UI wiring — the
`opposite`/`bands_by_class` fields were already fully wired into `/desk` as of iter-18, and this
iteration only corrects which value one of them resolves to.
