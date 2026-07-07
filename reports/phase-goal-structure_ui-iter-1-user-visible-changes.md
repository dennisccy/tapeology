# Phase goal-structure_ui-iter-1 — User-Visible Changes

**Phase:** goal-structure_ui-iter-1
**Date:** 2026-07-07
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now click a new **"Structure"** tab in the top navigation bar (it appears right after "Performance") to open a brand-new page at `/structure`.
- Users can now type a stock symbol — using the same autocomplete search box used elsewhere in the app — and an as-of date/time into the Structure page, then click **Load** to fetch that symbol's computed support/resistance levels and confluence zones.
- Users can now see a price candle chart with a dashed reference line drawn at every computed support/resistance level, each one labelled with which timeframe it came from and what kind of level it is (e.g. "1h swing-pivot 149.48").
- Users can now view a confluence-zones table below the chart: one card per zone, showing its A/B/C strength grade (A = strongest, agreement across the most timeframes), its numeric score, and the member price levels that make it up.
- Users can now tell exactly why nothing is showing, instead of seeing a blank or broken page: the Structure page shows one of four distinct, honestly worded messages depending on the reason (no price history ever recorded for that symbol; history recorded but nothing derivable yet at that time; levels exist but none cluster into a zone; or the app couldn't reach its backend / the typed date was invalid).
- This is the first browser-based way to see any of this "structure" data (support/resistance levels, confluence zones) — previously it was reachable only via `curl` or the MCP command-line tools.

---

## What Changed in the Visible UI

- The top navigation bar now shows a fifth destination, **"Structure"**, added after "Performance". The bar itself was not edited in code — the new link appears because the backend's route list (which the nav bar already reads live) grew by one entry.
- A brand-new page exists at `/structure` with, top to bottom: a page header, a row of controls (symbol box + as-of time box + Load button), a price-chart panel, and a confluence-zones table panel.
- The price chart panel shows dashed horizontal lines for every level at whatever timeframes are available for that symbol (e.g. hourly and daily lines together), even though the candles themselves come from only one of those timeframes at a time (see "Known limitation" below).
- The zones table shows a small table of member levels (price / timeframe / type) nested inside each zone's card, plus the zone's class badge and score.
- No existing page changed in appearance or behavior: the Cockpit, Journal, Studies, and Performance pages, and their own navigation, forms, and tables, are all unchanged.

---

## What Old Behavior Changed

- None. This is a purely additive iteration. The only edit to any existing backend behavior is one new entry appended to the internal list of pages the nav bar reads from — no existing entry in that list changed, and the four previously-existing pages were re-checked and confirmed to behave exactly as before. No existing endpoint's computation, response shape, or output changed.

---

## Not Visible Yet

- **Which trading strategies exist and which one is "in charge"** (the strategy registry) — the backend already has this data available, but there is still no page anywhere that shows it. Planned as a later addition to this same Structure page.
- **A side-by-side comparison of the alternate strategy against the current one on real data** (backtest comparison) — the backend already has this data available, but there is still no page anywhere that shows it. Planned as a later addition to this same Structure page.
- **A library/inventory view listing every recorded price-history series** (a `/datasets`-style page) — not part of this body of work at all; explicitly deferred.
- Note: the "current champion strategy" summary is *not* one of the above gaps — that was already visible on the pre-existing Performance page before this iteration, and nothing changed about it here.

---

## Known Limitation (disclosed by design, not a gap)

- When a symbol has price history recorded at more than one timeframe (e.g. both hourly and daily), the candle chart draws candles from only one of them at a time (the shortest available). It still draws a reference line for every level from every timeframe — it just cannot honestly draw two different timeframes' candles overlapping on one chart. This was a deliberate choice, disclosed in the page's own on-screen caption under the chart.
