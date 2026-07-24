# Phase goal-clean_slate-iter-5 — User-Visible Changes

**Phase:** goal-clean_slate-iter-5
**Date:** 2026-07-24
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see the **"Case Studies"** panel again on the `/structure` page — a list of every
  recorded support/resistance band-touch event (symbol, session date, band range/side/class,
  reaction, and forward returns at each configured horizon). For the last several days this panel
  was completely absent from the page (an unrelated commit had silently switched it off three days
  before this clean-up project began); this iteration turns it back on.
- Users can now filter that list by typing a symbol (e.g. "AAPL") into a **Symbol** field and/or
  choosing **rejected / broke / chopped** from a **Reaction** dropdown — the table narrows to
  matching rows, or shows an honest "no match" message if the combination matches nothing.
- Users can now click any row in the Case Studies table to open a **"Case Studies — drill-in"**
  detail view for that specific event, showing its band, its reaction (flagged **"truncated
  horizon"** when the forward-return window ran past the end of the stored series), its forward
  returns, and its recorded tape-timeline playback — or the honest text **"No recorded tape for
  this event."** when no dataset was ever captured around it.

---

## What Changed in the Visible UI

- The `/structure` page's **"Case Studies"** section (`<section aria-label="Case studies">`)
  reappears in its original position — between the Levels & Zones / "Show raw levels" toggle area
  and the Edge Report section. No new page, no new component, no restyle: it is the exact panel,
  table, filters, and drill-in that existed before, simply rendering again.
- The short framing paragraph at the top of `/structure` (`data-testid="structure-framing"`) now
  reads, in full: "...toggle 'Show raw levels' for the underlying S/R levels and confluence zones
  (off by default). **Case Studies lists every band-touch event with its reaction, forward returns,
  and — once recorded — its tape timeline;** Edge Report compares v1, structure_tape, and
  structure_tape_map over recorded windows..." — restoring the bolded sentence, which had been
  silently missing since three days before this clean-up project began.

---

## What Old Behavior Changed

- None, in the sense of a working feature now behaving differently. The Case Studies panel's
  several-day absence was itself an unrelated regression, not an intentional old behavior this
  iteration is revising — this iteration reverses that regression rather than changing settled
  behavior. Its filtering, row-click, and drill-in logic are byte-identical to how they worked
  before the panel went dark: the underlying state, handlers, and data-fetch (`GET
  /research/setups`) were never touched, only the on/off render gate.
- Testers should note: nothing else on `/structure` or the Cockpit page changed this iteration. The
  sim-cockpit ticker watch, both charts (candles, timeframe switching, live tape moving bars, S/R
  band overlay), the Tradable-Map load-by-symbol-and-date flow, and the Edge Report panel were all
  independently re-run and re-verified this iteration as part of a full regression sentinel — but
  they produce byte-identical output to before and are not new or changed. A full browser walk of
  those surfaces is expected as part of this iteration's own evidence, not because anything about
  them moved.

---

## Not Visible Yet

- None. The Case Studies panel's underlying data path (`GET /research/setups`) was already fully
  wired to this exact UI before it was hidden — this iteration adds no new backend capability or
  endpoint, it only flips the existing client-side render gate back on. There is no backend change
  from this iteration waiting on a UI hookup.
