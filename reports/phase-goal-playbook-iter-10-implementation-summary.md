# Phase goal-playbook-iter-10 — Implementation Summary

**Phase:** goal-playbook-iter-10
**Date:** 2026-08-12
**Written by:** developer

---

## Features Implemented

- **A new "turned at midrange" disclosure on range-trade signals**: an already-shipped `range_trade`
  signal's info line on `/desk` can now also say whether the price swing leading up to the trade
  turned back around right at the middle of the tested range — the book's own "midrange rule" — in
  addition to the existing "crossed midrange" note it already showed. This is purely informational,
  the same way the existing notes are: it never changes which signals appear or how they are
  scored, it only adds one more fact to read.

---

## Changed Behavior

- **The playbook rulebook document now matches the code exactly in four places.** Four small
  wording corrections were made to the written rulebook (`docs/playbook-detector-spec.md`) so it
  describes precisely what the already-shipped detectors do — not a change to any detector's
  behavior, just fixing four places where the written description was looser or slightly
  mismatched from the code. The operator ratified these corrections before this work began.
  Nothing a user sees changes because of these four edits.

<!-- No other existing behavior changed. -->

---

## Backend-Only Items

<!-- None. The one new field is served AND rendered in this same pass. -->

---

## Incomplete Items

<!-- None from this iteration's own scope. The one open item below is a deliberate handoff, not an unfinished task. -->

- **Fresh browser screenshots for this iteration's two target checks (J-06, J-10)** are not part of
  this developer pass — by design, that verification happens in the next pipeline stage (a
  dedicated browser-testing pass), which runs against a safe, isolated test copy of the data
  rather than the operator's real records. This developer pass did directly confirm — by reading
  the real, live data — that old recorded signals correctly do NOT show the new note (they predate
  it) and that nothing crashed or broke when serving them.

---

## Config and Environment Changes

<!-- None. No new environment variable, no new configuration field, no database migration. -->

---

## Known Limitations

- **A pre-existing, unrelated small gap in the test-data-preparation script was found and left
  alone.** While fixing the test rig's own indexing (see below), one already-existing test symbol
  (unrelated to this iteration's feature) turned out to be recorded twice under the same slot in a
  lookup helper, so only the most recent copy is currently reachable that way. This predates this
  iteration, does not affect the feature built here, and does not affect any real operator data —
  it is noted for whoever next touches that specific test-data script.
- **One long-standing test-infrastructure defect was fixed as part of this iteration's cleanup**:
  the practice/test copy of the product used for automated checks was missing real price data for
  one chart it needs to show. That is now fixed (confirmed directly), so the next automated
  check of that chart should show real candlesticks instead of a blank box.
- **One stale automated-test assertion was fixed — twice, because the first correction was still
  wrong.** The automated "nothing we already shipped has broken" check for the Desk page had
  drifted to look for a value that changes every time the practice data is rebuilt, so it was no
  longer testing anything meaningful. It was first re-pointed at the heading of the Desk page's
  "Forward Returns" section — but that section only appears once a desk screen has been recorded,
  and the practice data deliberately has none. Worse, the check still *passed*: the words "forward
  returns" also appear in an explanatory sentence elsewhere on the page, so the test was quietly
  matching ordinary body text and would have kept passing even if the Forward Returns section were
  deleted outright. It now checks three section headings that the Desk page always shows regardless
  of what data exists — "Top-up Runs", "Index Reconciliation" and "Screen Runs" — and this was
  proved not to be a rubber stamp: with those three sections removed from the page, all three
  checks fail, while the old wording still matched. The corrected check was then run end to end
  against the practice copy and passed.
