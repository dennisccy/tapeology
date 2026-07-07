# Goal Iteration 1 (J-01) — Implementation Summary

**Phase:** goal-structure_ui-iter-1
**Date:** 2026-07-07
**Written by:** developer

---

## Features Implemented

- **A new "Structure" tab in the app**: the top bar now shows a fifth tab, Structure, next to
  Cockpit, Journal, Studies, and Performance. Clicking it opens a new page.
- **Pick a symbol and a point in time, see its price structure**: on the new page, type a stock
  symbol (with the same autocomplete suggestions used elsewhere in the app) and a date/time, then
  click Load. The page then shows a price candle chart for that symbol with dashed reference lines
  drawn at every computed support/resistance price level, each labelled with which time-scale it
  came from (e.g. hourly vs. daily).
- **A confluence-zones table**: below the chart, a table lists every "confluence zone" — a spot
  where several of those price levels cluster close together, which the existing engine (built in
  an earlier body of work) considers more significant. Each zone is graded A, B, or C (A being the
  strongest — levels agreeing across the most different time-scales), with its member price levels
  listed underneath.
- **Four honest "nothing to show" messages, each different**: if a symbol has never had any price
  history recorded for it, the page says so plainly and explains that recording history needs
  provider credentials. If history exists but nothing can be computed yet at the chosen time, it
  says that instead. If levels exist but none of them cluster into a zone, the table says that. And
  if the app's backend can't be reached at all (or the typed date/time is invalid), the page shows a
  clearly marked "couldn't load" notice instead of a blank or broken screen. Every one of these has
  its own wording — the page never re-uses one "something's wrong" message for two different
  situations.
- **Everything shown is a straight read, never a guess**: every number, label, and grade on this
  page — every price, every A/B/C grade, every zone's score — comes directly from the same backend
  calculation an engineer could already see with a command-line tool. The page does no math of its
  own; it just draws what the backend already computed.

## Changed Behavior

- **The app's list of pages**: previously the app served four pages from one small internal list.
  That list now has a fifth entry for the new Structure page. This is the ONLY change made to
  existing backend behavior this iteration — everything else (the cockpit, the journal, the
  studies page, the performance page) is untouched and was re-checked to prove it still behaves
  exactly as before.

## Backend-Only Items

- None. Everything this iteration's backend-adjacent list entry supports is now reachable through
  the new Structure page.

## Incomplete Items

- **Two more sections of this same page are planned but not built yet**: a view of the two
  available trading strategies and which one is currently "in charge" (planned for a future
  iteration), and a side-by-side comparison of that alternate strategy against the current one on
  real data (also a future iteration). Neither was in this iteration's assigned scope — this
  iteration only had to deliver the price-levels-and-zones view.
- **The chart draws candles from only one price history at a time.** If a symbol has price history
  recorded at more than one time-scale (for example, both hourly and daily), the chart currently
  shows candles from just one of them (the shortest available) — it draws reference lines for
  levels from every time-scale, just not overlapping candle charts for all of them at once. Showing
  two different time-scales' candles on one chart at the same time is not something a normal price
  chart can do honestly, so this is a deliberate, disclosed choice, not an oversight.

## Config and Environment Changes

- No new environment variables, settings, or database changes were introduced this iteration.

## Known Limitations

- **Real price history still needs to be recorded before this page shows anything for a given
  symbol.** On a machine with no market-data credentials configured, every symbol will show the
  "no bar series recorded" message until history has been recorded for it through the existing
  (separate, credentialed) recording step — this page only displays history that already exists, it
  does not fetch new history itself.
- **A one-time testing hiccup, not a product problem:** while manually testing this feature, running
  a routine one-off verification check at the same time as the live preview server caused the
  preview server's cache to get temporarily confused (a known, previously-documented risk of running
  those two things together). Restarting the preview server fixed it immediately with no data loss
  and no code change needed. This does not affect the deployed feature or any operator using the app
  normally — it only affects a developer running two specific commands back-to-back during testing,
  and is now written down so it isn't repeated.
- The confluence-zones table only lists price levels that cluster into a qualifying zone with at
  least one other level; a level that stands alone (no nearby partner) still appears as a line on
  the chart but not as its own table row — this matches how the underlying engine has always defined
  a "zone" and is not a gap introduced this iteration.
