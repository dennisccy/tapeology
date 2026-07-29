# goal-desk-iter-18 — Implementation Summary

**Phase:** goal-desk-iter-18
**Date:** 2026-07-29
**Written by:** developer

---

## Features Implemented

- **"Opposite wall" disclosure on the Desk briefing table**: every ranked row on the `/desk` page
  now shows a new "opposite" column — the nearest wall on the OTHER side of price from the one the
  row was ranked on. Previously, several top-ranked names all read identically ("support · class A ·
  0.00 bps") even though their true nearest wall on the other side of price could be a fraction of a
  percent away or dozens of percent away — that gap was invisible on the page. Now the operator can
  see it at a glance: e.g. "opposite resistance A 490.88–494.22 · 0.6 bps" for a near opposite wall,
  or "no band on the other side" / "opposite wall not recorded in this snapshot" when there genuinely
  is none or the row predates this update.
- **"How many walls of each class" disclosure in the row detail**: hovering over any row now also
  shows a breakdown of how many A/B/C/unclassified walls the instrument found for that symbol in
  total (e.g. "bands by class A 10 · B 0 · C 0 · unclassified 0"), giving context for how contested
  or lightly-mapped a symbol's price structure is.

Both are purely descriptive, read-only additions — no new buttons, no new page, no new judgment or
recommendation logic. They are computed from data the instrument already calculates for every
symbol; nothing new is measured or graded.

---

## Changed Behavior

- **`/desk` ranked table**: grows from ten columns to eleven (the new "opposite" column, placed
  after the existing "band" column). No existing column's content or meaning changed.
- **Row hover tooltip**: gains one additional line of detail. No existing tooltip content changed.

---

## Backend-Only Items

None — both new pieces of information are wired into the UI in this same iteration.

---

## Incomplete Items

- **Live screenshot of the new column with real data has not been captured yet.** Every screen
  currently on record was computed before this update landed, so today's `/desk` page honestly shows
  "opposite wall not recorded in this snapshot" on every row. A screenshot showing the new column
  populated with real near/far examples, plus a short recorded walkthrough of the feature, is
  produced by the next stage of the pipeline (browser testing / demo recording), not this
  implementation step. The underlying logic is fully tested and proven correct by the automated test
  suite in the meantime.

---

## Config and Environment Changes

None. No new environment variable, no new configuration field, no new database migration. The
system's internal "fingerprint" (a checksum proving the core calculation engine has not changed)
stays exactly the same as before this update.

---

## Known Limitations

- The new "opposite wall" and "bands by class" information only appears on screens computed FROM
  THIS UPDATE FORWARD. Every screen recorded before today keeps its original content exactly as
  recorded (this product's core promise: past records are never silently rewritten) — those older
  screens will show an honest "not recorded in this snapshot" message instead of the new
  information, forever.
- The "opposite wall" disclosure does not include the wall's own quality score in the visible column
  (only its side, class, price range, and distance) — the score is available in the underlying data
  for a future update if ever needed, but was not part of what this update was scoped to show.
- No new controls were added — this is purely additional information on the existing screen, so
  there is nothing new for an operator to click or configure.
