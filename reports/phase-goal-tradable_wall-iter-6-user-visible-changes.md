# Phase goal-tradable_wall-iter-6 — User-Visible Changes

**Phase:** goal-tradable_wall-iter-6
**Date:** 2026-07-15
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now load a symbol + as-of time on `/structure` and see, by default, a **Tradable Map**
  of at most ~10 quality-scored price bands (verified: exactly 10 for AAPL as-of `2026-06-22`)
  instead of the full raw level list (which can run into the hundreds or thousands of lines) —
  each band shows its side, price range, inherited A/B/C class (or an honest "Unclassified" when no
  confluence zone overlaps it), quality score, member count, and round-number flag, plus the map's
  morning-markup `basis_as_of` stamp above the chart.
- Users can now see the bands drawn directly on the `/structure` price chart as solid, color-coded
  lines (rose for resistance, emerald for support) — visually distinct from the raw levels' dashed
  lines.
- Users can now click a **"Show raw levels"** toggle (off by default) to reveal the previous
  full raw-level-list + confluence-zone view, and toggle it back off — the raw view, when shown,
  renders exactly as it did before this iteration.
- Users can now browse a **Case Studies** registry of every historical band-touch event scanned
  across the 12-symbol watchlist (801 such events on the operator's real store), each showing
  symbol, session date, band, reaction outcome (rejected / broke / chopped), and forward returns.
- Users can now filter Case Studies by symbol (text field) and by reaction outcome (dropdown),
  narrowing the already-loaded list without a page reload.
- Users can now click any Case Studies row to open a drill-in panel showing the event's band,
  reaction, forward returns, an honest disclosure note for recency-boundary events ("Reaction read
  at a truncated N-bar horizon…" — never presented as a full-horizon outcome), and a
  moment-by-moment tape timeline where one was recorded, or an honest "No recorded tape for this
  event." message when it was not.
- Users can now view an **Edge Report** section comparing three trading strategies (`v1`,
  `structure_tape`, `structure_tape_map`) across recorded event windows, split into train and
  hold-out tables, with each cell's sample size (n), net R, net $, win rate, and an inline
  "insufficient sample" flag when a cell doesn't meet the minimum sample size — plus the simulated-
  results register line and an informational "surviving train cells" ranking. When no data
  qualifies yet, the section shows this honestly rather than appearing blank or broken.

---

## What Changed in the Visible UI

- The `/structure` page's default view flipped: loading a symbol now shows the new **Tradable Map**
  section first. Previously, loading a symbol immediately rendered the raw "Price chart — S/R
  levels" and "Confluence zones" panels.
- Those two raw panels are still on the page, unchanged, but now sit behind the new "Show raw
  levels" toggle button and are collapsed (hidden) by default.
- Two entirely new sections appear on `/structure`, between the raw-levels toggle and the
  repositioned older sections: **Case Studies** (registry table + symbol/reaction filters + a
  row drill-in) and **Edge Report** (register line + train/hold-out cell tables + surviving-cells
  ranking).
- The existing "Fetch from Yahoo Finance" control, its "Yahoo Finance" provenance badge, the
  **Registry** section (strategy list + champion), and the **Comparison** section
  (`structure_tape`-vs-`v1` backtest tool) are all still present and work exactly as before, but now
  appear lower on the page, below the three new sections instead of near the top.
- The page's intro paragraph under the "Structure" heading was rewritten to describe the new
  Tradable-Map-first layout ("Load a symbol and an as-of time to see its tradable level map…")
  instead of the old copy that led with fetching bars and S/R levels.
- One framing sentence inside the (now-repositioned) Fetch-from-Yahoo panel was updated to match
  its new position on the page ("…served through the Tradable Map and Levels & Zones sections
  above" instead of "…the Levels & Zones section below").

---

## What Old Behavior Changed

- Loading a symbol on `/structure` previously rendered the raw S/R levels chart and confluence-
  zones table immediately, with no way to hide them. Now it renders the new Tradable Map by
  default, and seeing the raw view requires one extra click on "Show raw levels" — when shown, that
  view is byte-identical to how it rendered before this iteration (same chart, same zone table,
  same states, same provenance badge).
- Everything else pre-existing on the page — the Fetch-from-Yahoo control, the strategy Registry,
  and the Comparison tool — behaves identically to before; only their position on the page moved
  further down.

---

## Not Visible Yet

- The cockpit's live price chart does not yet show these tradable bands or a descriptive chip —
  bands currently only render on `/structure`. That surface (referred to as J-06 in the underlying
  spec) is explicitly deferred to the next iteration.
- The Case Studies filters cover symbol and reaction only. The backend endpoint also supports
  filtering by band class (`band_class`), but no UI control for it was added this iteration.
- The Edge Report section is fully built and wired, but on the operator's current real data it
  renders its honest empty state — no strategy currently has any recorded trade window for a
  watchlist symbol (the only real recordings collected so far are for a reference symbol, PG, which
  is not on the watchlist). The populated view (per-cell n/R/$ numbers, the inline
  "insufficient sample" badge) will only be visible once credentialed trade-by-trade recordings
  exist for a watchlist symbol — a separate, operator-run action unrelated to this iteration.
- The backend reliability fix (making the internal scan-cache publish atomic in `setups.py`) has no
  UI of its own — it is what makes it safe for this page's three new sections to fire their reads
  concurrently on every load; there is nothing to see or click for this change specifically.
