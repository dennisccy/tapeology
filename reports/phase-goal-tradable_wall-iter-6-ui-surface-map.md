# Phase goal-tradable_wall-iter-6 — UI Surface Map

**Phase:** goal-tradable_wall-iter-6
**Date:** 2026-07-15
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-------------|-------------|-------------|
| `/structure` | Tradable Map — idle state (`tradable-map-idle`) | New component | New default section needs its own pre-Load state | On a fresh page load (nothing typed into the Load form yet), confirm the "Tradable Map" panel shows the message "Choose a symbol and an as-of time, then Load, to see its tradable level map." and no bands table or chart is rendered |
| `/structure` | Tradable Map — populated (`tradable-map-table`, `tradable-band-row`, `tradable-map-basis`, chart band overlays) | New feature | New default view: ≤10 quality-scored bands replace the raw ~1,800-line view | Submit the Load form with symbol `AAPL` and as-of `2026-06-22T15:00:00Z`; confirm `tradable-map-table` renders exactly 10 `tradable-band-row` rows (not more), confirm `tradable-map-basis` shows a prior-session date, and confirm one row has `tradable-band-range` inside `300.17–302.27`, `tradable-band-class` = "Class A", `tradable-band-round-number` badge visible, and the highest `tradable-band-score` value of all 10 rows (153.0 on the reference dataset) |
| `/structure` | Tradable Map chart overlays (`StructureChart` `bands` prop) | New component behavior | Bands drawn as solid price lines distinct from raw dashed level lines | After the AAPL `2026-06-22` load above, inspect the chart canvas and confirm solid (not dashed) rose-colored horizontal price lines appear near 300 and 302 on the price axis, with an axis label showing "R class A · score 153 · round" (or equivalent) on hover/at the line |
| `/structure` | Tradable Map — honest degraded/empty states (`tradable-map-unavailable`, `tradable-map-no-bar-series`, `tradable-map-no-bands`) | New component (honest states) | Never fabricate a band map when data is missing or unreachable | (a) Load a symbol with no recorded bar series and confirm `tradable-map-no-bar-series` renders "No bar series recorded for {symbol}."; (b) submit a malformed as-of value (e.g. `not-a-date`) and confirm `tradable-map-unavailable` shows the backend's verbatim error text, not a silent fallback to "now" |
| `/structure` | "Show raw levels" toggle (`raw-levels-toggle` button) | New control | Declutter — raw view is now opt-in, off by default | On page load, confirm the "Price chart — S/R levels" and "Confluence zones" panels are absent; click the button (labeled "Show raw levels") and confirm its label changes to "Hide raw levels" and both raw panels appear below it; click it again and confirm both panels disappear and the label reverts to "Show raw levels" |
| `/structure` | Levels & Zones panels (raw levels + confluence zones, now toggle-gated) | Changed behavior (repositioned, content unchanged) | Must render byte-identically to pre-iteration when shown | With the toggle on, load AAPL as-of `2026-06-22` and confirm the "Price chart — S/R levels" panel and "Confluence zones" table (`ZoneRow` entries, A/B/C badges) render with the same data and same `structure-*` testids as they did before this iteration — dashed level lines on the chart, not solid |
| `/structure` | Case Studies — table + filters (`case-studies-table`, `case-studies-filter-symbol`, `case-studies-filter-reaction`) | New feature | Browsable, filterable history of every band-touch event | On page load (no Load-form submission needed — this fetches on mount), confirm `case-studies-table` lists rows; type `AAPL` into the symbol filter (`case-studies-filter-symbol`) and confirm only rows with symbol AAPL remain; then select `rejected` in the reaction dropdown (`case-studies-filter-reaction`) and confirm only rows showing reaction "rejected" remain |
| `/structure` | Case Studies — row → drill-in (`case-studies-row`, `case-drillin-reaction`, `case-forward-returns`) | New feature | Row click opens the full event story | With the symbol filter set to `AAPL`, click the row dated `2026-06-22`; confirm the drill-in panel opens below the table showing `case-drillin-reaction` = "rejected" and `case-forward-returns` displaying negative return values at both configured horizons (78 and 234 bars on the reference dataset) |
| `/structure` | Case Studies drill-in — truncated-horizon disclosure (`case-drillin-boundary-note`, `case-studies-row-boundary-flag`) | New feature (honest state) | Recency-boundary events must disclose truncation, never claim a full-horizon reaction | Clear the symbol filter, locate a row carrying the `case-studies-row-boundary-flag` "truncated horizon" badge (e.g. an AAPL row dated `2026-07-13`), click it, and confirm the drill-in shows `case-drillin-boundary-note` text beginning "Reaction read at a truncated 77-bar horizon —" rather than presenting `chopped` as an ordinary full-horizon reaction |
| `/structure` | Case Studies drill-in — tape timeline (`case-drillin-tape-timeline`, `case-drillin-tape-timeline-empty`) | New feature (honest state) | Distinct empty state when no tape was recorded for an event | Click a Case Studies row for an event with no recorded dataset (e.g. the same `2026-07-13` boundary row) and confirm the drill-in shows the exact text "No recorded tape for this event." under "Tape timeline" rather than an empty list or blank space |
| `/structure` | Case Studies — honest empty / unavailable / filtered-to-zero states (`case-studies-empty`, `case-studies-unavailable`, `case-studies-no-match`) | New component (honest states) | Distinguish "nothing exists" from "nothing matches the filter" from "can't load" | Set the symbol filter to a value no event has (e.g. `ZZZZZ`) and confirm `case-studies-no-match` renders "No events match these filters." with detail text — this must NOT be the same copy/testid as the true-empty (`case-studies-empty`) state |
| `/structure` | Edge Report — honest empty state (`edge-report-empty`, `edge-report-register`) | New feature (honest state) | An empty/all-`insufficient_sample` report is a valid, first-class outcome, never hidden | On page load (fetches on mount), scroll to "Edge Report" and confirm `edge-report-register` (the simulated-results disclosure line) is visible, and — on the operator's current real data store, where no watchlist-symbol recordings exist yet — confirm `edge-report-empty` renders with "No edge-report cells yet." rather than a blank section or a loading spinner that never resolves |
| `/structure` | Edge Report — populated cell table (`edge-report-cell-row`, `edge-report-insufficient-sample`, `edge-report-train-table`, `edge-report-holdout-table`) | New feature (populated state — not yet exercisable on current data) | Per-cell n/R/$/win_rate with inline (never hidden) insufficient-sample flag | Not currently reproducible against the operator's real store (verified honestly empty as of this iteration). Once a credentialed recording exists for a watchlist symbol: reload Edge Report and confirm any `edge-report-cell-row` with n below `pnl_min_sample_size` shows the `edge-report-insufficient-sample` badge ("insufficient sample (n < X)") inline beside its real n/R/$ numbers, not as a separately hidden row |
| `/structure` | Fetch from Yahoo Finance control + `FeedBasisBadge` (repositioned) | Changed behavior (position only) | Moved below the three new sections; behavior preserved | Scroll past Tradable Map, Case Studies, and Edge Report to reach the "Fetch from Yahoo Finance" panel; submit a fetch for a symbol/timeframe/UTC date range and confirm it still returns success and the "Yahoo Finance" `FeedBasisBadge` still renders beside the loaded chart, exactly as it did before this iteration |
| `/structure` | Registry section (repositioned) | Changed behavior (position only) | Moved further down the page | Scroll to the "Registry" panel (below Fetch-from-Yahoo) and confirm it still lists strategies `v1`, `structure_tape`, and `structure_tape_map` plus the current champion pointer, identical in content to before this iteration |
| `/structure` | Comparison section (repositioned) | Changed behavior (position only) | Moved further down the page | Scroll to the "Comparison" panel at the bottom of the page, select a registered dataset, click "Run comparison," and confirm it still produces the `structure_tape`-vs-`v1` aggregate and per-class A/B/C breakdown as before this iteration |
| `/structure` | Page intro copy (H1 subtitle + `structure-framing` paragraph) | Changed behavior (copy) | Describes the new Tradable-Map-first layout | Confirm the paragraph under the "Structure" heading now reads "Load a symbol and an as-of time to see its tradable level map — at most a handful of quality-scored bands, not the full raw level set…" instead of the pre-iteration "Fetch real historical bars from Yahoo Finance (keyless), then see deterministic support/resistance levels…" copy |
| `/structure` (all new sections) | API client layer (`lib/api.ts`, `lib/types.ts` — `fetchTradability`, `fetchSetups`, `fetchSetupDetail`, `fetchEdgeReport`) | New capability (supporting, no visual surface of its own) | Wires the 3 previously-unwired read endpoints into the page | Open the browser Network tab, load AAPL as-of `2026-06-22`, and confirm requests fire to `GET /research/tradability`, `GET /research/setups`, and `GET /research/edge-report` (plus `GET /research/setups/{id}` after clicking a Case Studies row), each returning 200 with JSON whose fields match what the corresponding section displays |

<!-- Change Type options used above: New component | New feature | New component behavior | New control | New capability | Changed behavior -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/setups.py` — `_SCAN_CACHE` changed from a two-key mutable dict (two
  separate writes) to a single immutable `(key, result)` tuple published via one atomic rebind,
  closing a torn-read race window. Cached output is byte-identical to before; this makes it safe
  for the new page's three sections to fire `/setups`, `/setups/{id}`, and `/edge-report`
  concurrently on one load, but has no UI surface or visible behavior of its own — no UI surface
  affected.
- `apps/backend/tests/test_setups.py` — two new backend tests (a structural guard against
  reintroducing the two-write pattern, and a 16-thread concurrency stress test) covering the fix
  above — no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 1 route (`/structure`) — 3 brand-new sections (Tradable Map, Case
  Studies, Edge Report), 1 new control (raw-levels toggle), 1 repositioned block of 3 pre-existing
  sections (Fetch-from-Yahoo, Registry, Comparison), plus updated header/framing copy.
- **New pages/routes:** 0 (no new route; declutter of the existing `/structure` page)
- **Modified components:** 2 files directly changed (`apps/frontend/app/structure/page.tsx`,
  `apps/frontend/components/StructureChart.tsx`); `page.tsx` gained 11 new inline sub-components
  (`BandRow`, `BandsTable`, `ForwardReturnsList`, `SetupRow`, `TapeTimelineList`, `SetupDrillIn`,
  `EdgeReportMeasurementCells`, `EdgeReportCellRow`, `EdgeReportCellsTable`, `SurvivingCellRow`,
  `SurvivingCellsTable`, `EdgeReportBody`); 2 supporting library files extended
  (`apps/frontend/lib/api.ts`, `apps/frontend/lib/types.ts`).
- **Navigation changes:** no (no new route, no nav entry — explicit anti-goal for this iteration)
- **Backend-only changes:** 2 (`apps/backend/app/research/setups.py`,
  `apps/backend/tests/test_setups.py`)
