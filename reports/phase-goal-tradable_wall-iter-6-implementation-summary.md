# goal-tradable_wall-iter-6 — Implementation Summary

**Phase:** goal-tradable_wall-iter-6
**Date:** 2026-07-15
**Written by:** developer

---

## Features Implemented

This is the iteration that finally puts the "tradable wall" work of the last five iterations on
screen. Everything below already existed as working, tested backend logic — this iteration is
almost entirely about surfacing it on the `/structure` page.

- **A short, ranked list of price levels instead of a wall of lines.** Loading a symbol on
  `/structure` now shows, by default, at most about ten price "bands" — each one scored for how
  strong it looks (how many timeframes agree on it, how often price has touched it, how recently,
  whether it sits on a round number) — instead of the full raw list, which for a real stock can run
  into the hundreds or thousands of individual lines. Tested against the operator's real stored
  price history for AAPL as of 22 June 2026: the new view shows exactly **10 bands**, and the
  strongest one is the exact price zone (around 300–302) where the price was actually rejected six
  times before a sharp drop — ranked **#1** out of all ten, clearly ahead of every other band.
- **A "show me the old view" switch.** The previous, fully-detailed view (every raw level plus the
  clustered zones) is still available — it's now one click away behind a toggle, off by default. When
  turned on, it looks and behaves exactly as it did before this iteration; nothing about it changed.
- **A browsable history of "what happened last time price touched this level."** A new section lists
  every historical moment, across the whole 12-symbol watchlist, where price actually touched one of
  these bands, and what happened next: it either got rejected, broke through, or chopped around
  without a clear resolution. Each one can be filtered by symbol or by outcome, and clicking one
  opens the full story — the exact band, the outcome, how price moved afterward, and (for the
  handful of cases where real trade-by-trade data has been recorded around that moment) a
  moment-by-moment read of what the tape was doing when the touch happened. Tested against the
  operator's real data: 801 such moments exist across the watchlist; the AAPL 22-June case above
  shows up correctly as "rejected," with price moving further against the level afterward — matching
  exactly what actually happened.
- **An honest "did any of this actually make money" report.** A new section compares three trading
  strategies — the original one, one that reacts to the tape, and a new one built to react to these
  specific bands — over every recorded real-trade window, broken down by band strength and what
  happened at the touch. Every number carries how many trades it's based on, and any group with too
  few trades to trust is labeled as such rather than hidden or faked. Right now this report is
  honestly empty, because the only real trade-by-trade recordings collected so far are for a
  reference stock that isn't on the watchlist — the report correctly says so rather than making
  something up, and will fill in once real recordings exist for watchlist symbols.

---

## Changed Behavior

- **`/structure` page layout.** Previously, loading a symbol immediately showed the full raw level
  list and zone table. Now it shows the new short band list first; the old view is reachable via the
  new toggle. The existing "Fetch from Yahoo Finance" button, its data-source label, the strategy
  list, and the profit-comparison tool are all still there and still work exactly as before — they
  just sit lower on the page now, below the three new sections.
- **A small, invisible reliability fix.** The part of the backend that scans all 801 historical
  touch events was already cached after the previous iteration so it doesn't have to redo that
  multi-minute scan on every request. This iteration closes a narrow theoretical gap where two
  requests arriving at almost the exact same instant could, in a very unlucky case, have gotten a
  half-finished answer instead of a real one. This has no visible effect under normal use — it is a
  safety fix for the fact that this page now genuinely does fire three of those requests at once on
  every load.

---

## Backend-Only Items

None. The one backend change this iteration (the reliability fix above) has no user-facing surface
of its own — it makes the three new sections above safe to load together, which is exactly what
this iteration does.

---

## Incomplete Items

None from this iteration's plan. Everything the plan asked for is built and passing every automated
check available at this stage. What has **not** yet happened, by design:

- A person (or the automated browser-testing step that runs next) has not yet actually clicked
  through the new page in a real browser and looked at it — that is the next step in the pipeline,
  not something this build step does itself. Everything was checked as thoroughly as possible
  without a real browser: the real backend was queried directly and its answers were confirmed to
  match, value-for-value, what the new page is built to show.
- The cockpit's live price chart getting these same bands and a small descriptive note — that is
  next iteration's work, not this one's.
- Recording more real trade-by-trade data for watchlist symbols (which would fill in the currently-
  empty profit report) — a separate, operator-run action using the operator's own market-data
  credentials, unrelated to this iteration.

---

## Config and Environment Changes

None. No new settings, no new environment variables, no database change. The internal fingerprint
the app uses to guarantee "this was computed under the same rules as before" was double-checked and
confirmed unchanged.

---

## Known Limitations

- **The profit-comparison report is currently empty** on this machine's real data, for an honest
  reason explained above (no recorded real-trade data yet for any watchlist symbol) — not a bug.
- **If someone filters the "what happened last time" list and then the row they had open scrolls out
  of view, the details panel for that row stays open** rather than closing itself. It still shows
  correct information for whatever was last clicked; it just doesn't auto-hide. Minor, and not
  something the plan for this iteration asked for.
- **The new page section was not yet confirmed to look right when actually loaded in a browser and
  looked at by a person** (see Incomplete Items) — every other available form of verification (the
  page compiling and loading correctly, the real backend data matching exactly what the page expects
  to display, the full automated test suite) was completed and passed.
