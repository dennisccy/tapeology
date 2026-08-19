# goal-rapid-microscope-iter-11 — Implementation Summary

**Phase:** goal-rapid-microscope-iter-11
**Date:** 2026-08-19
**Written by:** developer

---

## Features Implemented

- **A recorded tranche now stays one opaque pool, even before anyone explicitly "seals" it.**
  Previously, a dataset only became invisible on the public dataset listing and the corpus
  readiness page once someone had run an explicit sealing step against it. Nothing in the product
  actually does that sealing step today — so a freshly recorded dataset that belonged to a
  registered recording plan would have been fully visible (symbol, date, everything) the moment
  it finished recording, defeating the whole point of keeping a research pool's membership hidden
  until it is genuinely revealed. Now, simply being a member of a registered recording plan is
  enough to keep a dataset hidden from these two surfaces until it is deliberately, explicitly
  released — no separate manual step required.
- **The live "recording in progress" view no longer shows which symbol or date is currently being
  fetched.** Watching a recording job run used to reveal each chunk's stock symbol and date as it
  was fetched — which itself would have leaked which stocks/dates are part of a pool meant to stay
  hidden. The live progress view now shows only totals: how many chunks are done out of the total,
  how many succeeded/were reused/failed, how many trades and quotes have come in, percent
  complete, and elapsed time — never which specific symbol or date is currently being worked on.

## Changed Behavior

- **The public dataset listing (`GET /research/datasets`) and the corpus-readiness page**:
  Previously, a dataset was hidden from these views only if someone had explicitly run a "seal"
  action on it. Now, a dataset is also hidden if it is part of a registered recording plan that
  hasn't been fully resolved yet — even if no one ever explicitly sealed it. This closes a real
  gap: today, nothing in the product performs that explicit sealing step, so this change is what
  actually makes the "hidden until released" promise true in practice, rather than true only on
  paper.
- **The live recording-progress view**: Previously carried each chunk's symbol and date (though
  the specific dataset id was never shown, due to an existing quirk). Now carries only aggregate
  counts, at every point during a run — before, during, and after.

## Backend-Only Items

- None. This is entirely a data-visibility correction to two already-shipped, already-visible
  surfaces (the dataset listing and the corpus readiness page) plus one already-shipped live
  progress view — there is no new page, no new button, and no new information an operator needs to
  learn to use.

## Incomplete Items

- **The actual "record real tape from a live vendor" step remains a separate, manual, gated
  action** that this iteration does not perform or unlock. This iteration only makes sure that
  *if* a real recording were run today, it would correctly stay hidden as part of an opaque pool.
  No real recording was made against the operator's actual data in the course of this work.
- **There is still no way to deliberately release a dataset for everyday research use** (as
  opposed to being formally "sealed" for a strict held-out test). This was already a known,
  intentionally-unaddressed gap before this iteration and remains so — a hidden dataset today
  simply stays hidden indefinitely, which is the safe direction, but the mechanism for eventually
  releasing it for ordinary use has not yet been designed.

## Config and Environment Changes

None. No new environment variable, no new configuration field, no migration.

## Known Limitations

- The corpus readiness page and dataset listing are unaffected in every case that matters today,
  because the operator's real data store has zero registered recording plans right now — so
  nothing an operator currently sees on screen changes as a result of this work. The effect only
  becomes visible the next time a recording plan is registered and tape is actually recorded
  against it.
- The live recording-progress view's new "trades so far" and "quotes so far" counters only count
  data that was freshly fetched during the CURRENT run — if a run resumes previously-fetched data
  from an earlier interrupted attempt, that earlier data's trade/quote counts are not re-added to
  the running total (though the "chunks done" count still reflects it correctly). This matches how
  the equivalent counts already behave on the separate historical run-log view.
