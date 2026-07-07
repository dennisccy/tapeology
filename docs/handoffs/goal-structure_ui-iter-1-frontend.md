# goal-structure_ui-iter-1 Frontend Handoff

**Phase:** goal-structure_ui-iter-1
**Date:** 2026-07-07
**Agent:** developer
**Status:** complete

## What Was Built

The **Structure** tab (`/structure`) — the app's fifth top-bar destination, reached from the new
data-driven nav entry (`GET /meta/ui-routes`, no client hardcoding). For a chosen symbol and as-of
time it renders:

- A dark instrument-panel price chart (`lightweight-charts`, following `PriceChart.tsx`'s established
  dark theme/dynamic-import pattern) with candles from the symbol's recorded bar series and one
  dashed reference line per S/R level, each labelled by its own timeframe + type (e.g. "1h
  swing-pivot 149.48").
- A confluence-zones table: one card per zone, an A/B/C class badge, the zone's score, and a small
  table of its member levels (price / timeframe / type).
- Symbol + as-of controls (reusing `SymbolSearch` verbatim) behind an explicit `Load` button.
- Four distinct honest states (no shared copy) plus loading/idle placeholders — see below.

## New user-facing capability

A person can now open the Structure tab, type a symbol (with the same autocomplete dropdown used
elsewhere in the app) and an as-of time, click Load, and see that symbol's computed support/resistance
levels drawn on a real candle chart plus its A/B/C confluence zones in a table — without `curl` or the
MCP tools. This was previously invisible in the browser (era-4 backend-only).

## Component/file map

- `apps/frontend/app/structure/page.tsx` — the page: controls, state machine (`idle` / `loading` /
  `error` / `ready`), the four honest states, the chart panel, the zones-table panel.
- `apps/frontend/components/StructureChart.tsx` — the chart: a small, dumb, prop-driven component
  (`bars`, `levels` in; draws candles + dashed price lines, nothing else). No fetching, no state
  beyond the chart library's own refs.
- `apps/frontend/lib/api.ts` — `fetchLevels` / `fetchBarSeriesList` (new).
- `apps/frontend/lib/types.ts` — `SrLevel` / `ConfluenceZone` / `LevelsResponse` / `BarRow` /
  `BarSeriesRecord` / `BarSeriesListResult` (new).

## Visual/UX states implemented

| State | Trigger | Copy (verbatim) | `data-testid` |
|---|---|---|---|
| Idle | Page load, before first Load click | "Choose a symbol and an as-of time, then Load, to see its S/R levels and confluence zones." | `structure-idle` |
| Loading | Load clicked, fetch in flight | pulse-skeleton placeholder | `structure-loading` |
| Degraded | Backend unreachable, any non-200 (incl. malformed `as_of` 422, folded in) | Backend's own error `detail`, e.g. "as_of must be an ISO date-time" | `structure-degraded` |
| No bar series | `no_bar_series_for_symbol: true` | "No bar series recorded for `<SYMBOL>`." / "Recording historical bars needs provider credentials." | `structure-no-bar-series` |
| No levels | Series exist, `levels: []` | "No levels found for `<SYMBOL>` as of `<AS_OF>`." / "A bar series is recorded, but nothing is derivable at this as-of time." | `structure-no-levels` |
| No qualifying zone | Levels exist, `confluence_zones: []` (zones panel only — chart still renders) | "No qualifying confluence zone among these levels." / "Levels exist, but none cluster closely enough across timeframes to form a zone." | `structure-no-zones` |
| Populated | Levels + zones both non-empty | chart with level lines + zones table | (chart: `structure-chart-canvas`; zones: `zone-row` × N) |

Every interactive element (Load button, the as-of input, `SymbolSearch`'s input) carries hover/focus/
active states via the same Tailwind classes already established by `/performance` and
`/studies` (`focus:ring-1 focus:ring-emerald-500`, `hover:border-slate-500`, `active:bg-slate-900`,
`disabled:opacity-40` on Load when the form is incomplete).

## Design system conformance

- Dark-only, slate surfaces (`bg-slate-900/60`, `border-slate-800`), font-mono numerics
  (`NUMERIC_CELL`), amber for degraded/honest-empty states (`border-amber-800/60 bg-amber-900/20
  text-amber-300`) — no new color introduced. The A/B/C class badge deliberately reuses the SAME
  neutral slate badge treatment `/performance` already uses for "frozen"/"candidate" (no invented
  traffic-light semantic for A vs. B vs. C — the letter itself carries the meaning).
- Layout: single-column, `max-w-7xl`, matching `/performance`'s shape — header, controls row, chart
  panel, zones panel. No sidebar.
- `LoadingPanel` / `UnavailablePanel` are defined locally in `page.tsx`, mirroring
  `/performance/page.tsx`'s own local (non-shared) definitions verbatim — this is the SECOND
  occurrence of this exact pattern in the codebase, still under the "abstract on the third
  occurrence" threshold, so no shared component was extracted.

## Live browser verification performed

Ran the actual app (`bash scripts/dev.sh`) and drove it with the Chrome MCP browser tool end to end:
nav link present and functional, all four honest states triggered and screenshotted/inspected, and
the populated state's rendered level lines + zones table cross-checked field-by-field against the
live `GET /research/levels` JSON (20 levels / 6 zones — 5×C, 1×B — matched exactly, including exact
prices/timeframes/types/scores). Full detail and exact commands are in the dev handoff
(`docs/handoffs/goal-structure_ui-iter-1-dev.md`) — this file focuses on the UI shape and states, not
the verification transcript.

## Known Issues / Limitations

- No dedicated "all levels" list exists outside the chart's price lines and the zones table's member
  rows — per the spec, the zones table lists only zoned member levels; a lone (non-clustering) level
  is visible ONLY as a chart price line, never in a table row. This matches the backend's own model
  (a lone level has no "zone" home) and the phase spec's literal text — not a gap.
- The chart shows exactly one representative bar series per symbol (the shortest recorded
  timeframe) even when multiple are registered; a single candlestick chart cannot honestly overlay
  two timeframes' OHLC at once. See the dev handoff's "Design decisions" section for the exact
  tie-break rule.
- No responsive breakpoint tuning beyond `flex-wrap` on the controls row and the zones table's own
  `overflow-x-auto` — matches the precedent set by `/performance` and `/studies`, neither of which
  defines explicit `sm:`/`md:`/`lg:` classes for their control rows either.
