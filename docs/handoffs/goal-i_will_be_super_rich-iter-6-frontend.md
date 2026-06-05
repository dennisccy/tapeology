# goal-i_will_be_super_rich-iter-6 Frontend Handoff

**Phase:** goal-i_will_be_super_rich-iter-6
**Date:** 2026-06-05
**Agent:** developer
**Status:** complete

## What Was Built

A **tape-state prediction chart** above the cockpit on `/` — a candlestick price chart with
markers at meaningful tape-state transitions and a 10 / 30 / 60 s bar-size selector. Shown for
**Simulated** and **Historical** watches only; **hidden for Live** (per the blueprint IA). This is
the first frontend change of the J-16–J-20 extension and turns the textual tape read into a
testable visual one on the same screen.

- **`PriceChart` component** (`apps/frontend/components/PriceChart.tsx`, `"use client"`):
  - Renders OHLC candlesticks via `lightweight-charts` v5 (`addSeries(CandlestickSeries, …)`),
    plus tape-state-transition markers via `createSeriesMarkers`.
  - **Marker colors carry the load-bearing semantics**: emerald (`#34d399`) = buyer_control, rose
    (`#fb7185`) = seller_control, amber (`#fbbf24`) = bid/ask_absorption. `unclear` is never marked
    (the backend emits no `unclear` marker). Up/down candle bodies use the same emerald/rose.
  - The chart canvas is themed to the dark instrument-panel surface (slate-950 background,
    slate-800 grid, slate-400 monospaced axis text) so it does not read as a bright third-party
    widget.
  - **Bar-size selector**: three plain buttons (10s / 30s / 60s) styled to match the cockpit; the
    active button is visually distinct (`bg-slate-700 text-slate-100`), with hover / focus / active
    states on the inactive buttons and `aria-pressed` for the selected one.
  - **States handled**: *loading/idle* ("Loading price history…" overlay before the first fetch),
    *empty window* ("No price history for this window yet" — same empty treatment, **never**
    placeholder candles), *active* (candles render and re-render as bars accrue / on bar-size
    change). No separate error state — the cockpit-level honest non-cockpit panels own real-data
    failures, and the chart is simply hidden for Live.
  - **Pan/zoom**: library default (drag to pan, scroll/pinch to zoom); `fitContent()` is called
    when candles are present so the latest data is in view.
- **Mounted** in `apps/frontend/app/page.tsx` above `<Cockpit>`, gated on
  `ticker && (mode === "sim" || mode === "historical")`. The page remains exactly one screen.

## Data Flow (single source of truth)

The chart reads its data **only** from `GET /tape/{ticker}/history?bar=` via
`fetchHistory(ticker, bar)` (`apps/frontend/lib/api.ts`) and renders the returned candles +
markers **verbatim**:
- It **re-bins no candles** and **re-derives no marker** state/side/price — every value (OHLC,
  marker time, marker state, marker confidence) comes straight from the engine buffer.
- It **does not consume the WS stream and does not open a second WebSocket**. It polls
  `…/history` on a 1 s interval (matching the cockpit's WS push cadence) while a ticker is watched;
  the poll resets on ticker or bar-size change.
- Any fetch failure / not-watched (404) / not-yet-warmed window yields empty data, so the chart
  falls back to its empty treatment — it never invents candles.

## SSR / packaging

`lightweight-charts` is **client-only**: it is `await import("lightweight-charts")` **inside a
`useEffect`**, so it never executes during server render. The production build confirmed `/`
prerenders as static content with no SSR error. It adds **no backend dependency** and is
candlestick + markers only — no indicators, studies, drawing tools, or any order/execution
affordance on or near the chart.

## Files Changed

- `apps/frontend/components/PriceChart.tsx` -- NEW: the chart component (candles + markers +
  bar-size selector + empty-state handling).
- `apps/frontend/app/page.tsx` -- mount `<PriceChart ticker={ticker} />` above `<Cockpit>`, only
  for sim/historical (hidden for live).
- `apps/frontend/lib/api.ts` -- add `fetchHistory(ticker, bar)`.
- `apps/frontend/lib/types.ts` -- add `OhlcBar`, `TapeMarker`, `TapeHistory`, `HISTORY_BAR_SIZES`,
  `HistoryBarSize`.
- `apps/frontend/package.json` / `package-lock.json` -- add `lightweight-charts ^5.2.0`.
- `apps/frontend/next.config.mjs` -- env-gated `distDir` override (`NEXT_DIST_DIR`), no-op by
  default (used only to isolate a one-off build from the running dev server's `.next`).

## Verification

- `npx tsc --noEmit` → clean.
- `NEXT_DIST_DIR=.next-iter6-build npm run build` → compiled successfully, `/` static-prerendered
  (no SSR violation). Built into an **isolated** dist dir so the harness's shared `.next` (a
  separate copy under `/tmp/tapeology-fe-qa/`) and my working-dir `.next` were never touched; the
  temp dir was removed and the build's auto-edits to `next-env.d.ts` / `tsconfig.json` were
  reverted.

## Notes for QA

- **J-17 (no credentials, browser):** Watch `SIM-BUYER` → candles render + an **emerald**
  buyer_control marker appears; toggle 10 → 30 → 60 s and confirm the candles re-render. Then
  `SIM-SELLER` (down trend + **rose** marker) and `SIM-BIDABS` / `SIM-ASKABS` (**amber** markers,
  price held). Switch the data source to **Live** → the chart is **hidden**.
- **J-18:** with credentials, a Historical watch of a penny-spread name (Ford) over a past RTH
  window populates real candles + markers; without credentials, verify the chart surface +
  bar-size + empty/honest behaviour and rely on the backend `…/history`-agrees-with-engine test.
- Markers may overlap visually at coarse bar sizes (a transition's logical-second timestamp is
  rounded to the chart's integer time axis); the marker count and colors remain correct (assert
  against `GET …/history`, not pixel positions).
