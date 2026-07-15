# goal-tradable_wall-iter-6 Frontend Handoff

**Phase:** goal-tradable_wall-iter-6
**Date:** 2026-07-15
**Agent:** developer
**Status:** complete

## What Was Built

`/structure` flips from "1,800 raw levels first" to "the handful of tradable bands + the case
evidence + the edge report first" — no new page, no new route, no nav change. The existing Load
form (symbol + as-of) now drives four reads in parallel instead of two.

- **Tradable Map (new default view).** On Load, the page renders the price chart (candles + solid
  band-edge price lines, one pair per band, colored by side — rose for resistance, emerald for
  support, matching the candle up/down palette) plus a bands table: side, price range, inherited
  class (or an honest "Unclassified" when no confluence zone overlaps — never a fabricated grade),
  quality score, member count, round-number flag. The map's `basis_as_of` (the morning-markup prior-
  session-close stamp) is shown above the chart. Three distinct honest states beyond the populated
  one: idle (nothing loaded yet), `no_bar_series_for_symbol` (needs provider credentials), and an
  unresolved basis (`bands: []`, "no prior-session basis derivable yet").
- **"Show raw levels" toggle**, off by default. Toggling it on reveals the exact pre-existing
  "Price chart — S/R levels" + "Confluence zones" panels, unchanged (verified via a whitespace-
  normalized diff against the pre-iteration source — byte-identical, same testids, same states,
  same provenance badge). Toggling off hides it again; no state is lost (levels/bars are already
  fetched regardless of toggle position, since the raw section reads the SAME `levelsState`/
  `barsState` the Load form already populates).
- **Case Studies.** A registry table (symbol, session date, band range/side/class, reaction, forward
  returns) sourced from one unfiltered `GET /research/setups` fetch on mount; a symbol text filter
  and a reaction `<select>` narrow the ALREADY-served rows client-side (no re-fetch per keystroke).
  Clicking a row fetches `GET /research/setups/{id}` and opens a drill-in panel below the table
  showing: the band, the reaction, forward returns (raw fraction values, never a percentage
  conversion — kept as a pure verbatim render, never client arithmetic), a truncated-horizon
  disclosure note when `reaction_boundary_truncated` is true ("Reaction read at a truncated N-bar
  horizon — the store does not yet hold the full configured horizon past this touch"), and the tape
  timeline (a list of state/confidence/timestamp entries, or its own honest "No recorded tape for
  this event." empty state).
- **Edge Report.** Renders `GET /research/edge-report` verbatim: the register disclosure line, a
  train-cells table, a hold-out-cells table (each cell: strategy/class/side/reaction/feed identity +
  n/net R/net $/win_rate + `insufficient_sample` shown INLINE on the real numbers, never a separate
  hidden state — reuses this page's own `BacktestClassTable` copy precedent verbatim, including the
  exact `insufficient sample (n < X)` string), and an informational "surviving train cells" ranking
  (each paired with its own hold-out cell's status, or an honest "no hold-out data yet" when none
  exists). An all-empty report (both splits, zero cells) renders its own distinct honest empty
  state — verified this is exactly what the operator's real store currently returns (see the dev
  handoff's live smoke test).
- **Repositioned, unchanged sections.** The era-5 "Fetch from Yahoo Finance" control, its provenance
  badge, the Registry section, and the Comparison section all moved below the three new sections —
  their own JSX, state, and testids are untouched (only one intentional framing-copy sentence
  changed, reflecting the new page position: "the Levels & Zones section below" → "the Tradable Map
  and Levels & Zones sections above").

## Files Changed

- `apps/frontend/lib/types.ts` -- new types only (pure addition, +151 lines): `TradabilityBand`
  (reuses the existing `SrLevel` shape for `members[]`), `TradabilityResponse`, `SetupForwardReturn`,
  `SetupTapeTimelineEntry`, `SetupReaction`, `SetupEvent`, `SetupsListResult`, `SetupDetailResult`,
  `EdgeReportCell` (reuses the existing `BacktestAggregate` shape for `measurement`/`null_baseline`),
  `EdgeReportSurvivingCell`, `EdgeReportResponse`.
- `apps/frontend/lib/api.ts` -- `fetchTradability(symbol, asOf)`, `fetchSetups(filters?)`,
  `fetchSetupDetail(id)`, `fetchEdgeReport()`, each following the file's own established
  `{ok, data, error}` pattern (`fetchLevels`/`fetchStrategies`) — backend `detail` surfaced verbatim
  on any non-200, network failure resolves to the same "Backend unreachable — is the API running?"
  message every other fetch helper in this file uses.
- `apps/frontend/components/StructureChart.tsx` -- one additive optional prop, `bands` (default
  `[]`). Existing `bars`/`levels` rendering path is untouched code (I did not modify a single
  existing line inside the level-line loop) — the raw-levels toggle's "on" render is guaranteed
  unaffected since it never passes a `bands` prop at all.
- `apps/frontend/app/structure/page.tsx` -- the whole feature. See the dev handoff for the full
  state/effect/derived-value breakdown; summarized here from the UI's point of view:
  - New testids, none colliding with any existing one (verified via a source grep for exact-string
    duplicates): `tradable-map-*` (idle/loading/unavailable/no-bar-series/no-bands/basis/table),
    `tradable-band-*` (row/range/class/score/round-number), `raw-levels-toggle`, `case-studies-*`
    (loading/unavailable/empty/no-match/table/filter-symbol/filter-reaction/row/row-reaction/
    row-boundary-flag), `case-forward-returns`, `case-drillin*` (loading/unavailable/reaction/
    boundary-note/tape-timeline/tape-timeline-empty/tape-timeline-entry), `edge-report-*`
    (loading/unavailable/empty/register/train-table/holdout-table/cell-row/insufficient-sample/
    surviving-table/surviving-row/surviving-holdout-status/surviving-empty).
  - Every new component is defined inline in `page.tsx`, matching this file's own 100%-established
    convention (`ZoneRow`, `StrategyCard`, `ClassMapTable`, `BacktestClassTable`,
    `BacktestResultBlock`, `BacktestPanel` are all inline too — none of this page's pre-existing
    sub-components live in separate files, so the new ones don't either).

## Visual / Design Notes

- No new visual effects, no glassmorphism/glow additions — every new element reuses the page's
  existing dark instrument-panel language: `Panel` wrapper, the established `border-slate-800
  bg-slate-900/60` surface, `font-mono` numerics, amber `border-amber-800/60 bg-amber-900/20` for
  every honest-empty/degraded/truncated-disclosure state (matching `UnavailablePanel`'s own amber
  treatment), the `INPUT_CLASS` constant reused verbatim for the new filter controls, and the
  existing button styling (`border-slate-600 bg-slate-800 hover:border-slate-500...`) reused
  verbatim for the raw-levels toggle button.
- Band overlay lines are drawn SOLID (`lineStyle: 0`) versus the pre-existing raw levels' DASHED
  lines (`lineStyle: 2`) — the one deliberate new visual distinction, so a band and a raw level
  never look identical on the same chart if a future iteration ever overlays both (they currently
  never do — Tradable Map and raw levels render in two separate, mutually-exclusive-by-toggle chart
  instances this iteration).
- Table layout for the three new tables (bands, case registry, edge-report cells) follows the exact
  `border-collapse` + `HEADER_CELL`/`LABEL_CELL`/`NUMERIC_CELL` styling constants this page already
  defines and uses throughout (`ZoneRow`'s member table, `BacktestClassTable`'s per-class rows) — no
  new table styling was invented.
- Loading/empty/unavailable states reuse the exact shared `LoadingPanel`/`EmptyState`/
  `UnavailablePanel` components this page already established in earlier iterations — no new
  generic state component was created; only new, distinct `testid`+copy pairs per the page's own
  "never share copy" precedent.

## States Covered Per New Section

- **Tradable Map:** idle, loading, unavailable (backend unreachable / non-200, including a
  malformed `as_of` 422 folded into the same treatment `fetchLevels` already established),
  `no_bar_series_for_symbol`, unresolved basis (`bands: []`), populated. The chart itself has its
  own loading/unavailable sub-states mirroring the raw-levels section's existing `barsState`-gated
  chart rendering.
- **Case Studies:** loading, unavailable, true-empty (zero events scanned anywhere), filtered-to-
  zero (distinct copy from true-empty), populated. Drill-in: loading, unavailable, populated (with
  its own two additive honesty states nested inside — the boundary-truncation note and the tape-
  timeline-empty state).
- **Edge Report:** loading, unavailable, honest all-empty (both splits zero cells), populated (with
  `insufficient_sample` inline per cell, never a separate state).

## Tests

Same situation as every prior iteration: no frontend test runner exists in this repo
(`apps/frontend/package.json` has no `test` script, no `.test.ts(x)` files anywhere). Frontend
correctness was verified via:
1. `npx tsc --noEmit -p tsconfig.json` — exit 0, zero type errors across all changed/new files.
2. The live smoke test described in detail in the dev handoff: real backend responses (against the
   operator's populated 12-symbol panel store) were fetched and their exact JSON shapes checked
   against what each new rendering branch expects — including the pinned AAPL 2026-06-22 case, a
   real recency-boundary event, and the genuinely-empty edge report. Every shape matched.
3. `scripts/dev.sh` full-stack startup: `GET /structure` compiled and returned 200; the server-
   rendered (pre-hydration) HTML showed the correct initial testids in the correct order
   (`tradable-map-idle`, `raw-levels-toggle`, `case-studies-loading`, `edge-report-loading`).
4. The backend's own `test_lint_frontend_source_literals_are_clean` (part of
   `tests/test_copy_discipline.py`, 31/31 passing) walks every `.tsx`/`.ts` file under
   `apps/frontend/components` and `apps/frontend/app` — including everything written this
   iteration — for imperative/predictive/certainty-claim language. Clean.

**Not done by this build step** (the browser-qa-agent's job next): clicking the raw-levels toggle in
a real browser and screenshotting both states; clicking a Case Studies row and screenshotting the
drill-in; visually confirming the band overlay lines render correctly on the chart canvas;
confirming the provenance badge still renders after scrolling to the repositioned Fetch-Yahoo
section.

## Known Issues

See the dev handoff's "Known Issues" section (same list; the frontend-relevant items are #1, #3,
and #4 there).
