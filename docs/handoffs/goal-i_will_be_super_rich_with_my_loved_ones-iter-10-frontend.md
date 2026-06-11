# goal-i_will_be_super_rich_with_my_loved_ones-iter-10 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-10
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

The `/` cockpit price chart now renders the declared thesis geometry (J-48) — read VERBATIM from
the WS `thesis` key's `geometry` object. No new pages, panels, nav, or user controls; the chart
gains no interaction affordance. The same one `PriceChart` component serves all modes (sim /
historical / live) — no mode-specific geometry code path.

- **`PriceChart` takes a `thesis` prop** (`snapshot?.thesis ?? null` from `page.tsx`) and reads its
  served `geometry`. With `thesis: null` (no thesis, cleared, or resolved-non-invalidated) the chart
  renders exactly as before — every price-line removed and the thesis-marker layer cleared (the
  J-68/J-17 no-thesis regression render).
- **Price-lines** render via the charting library's `series.createPriceLine` at the served prices
  with the served labels — invalidation (rose, the idea is dead beyond it) and, when present, level
  (slate, a neutral reference) — dashed, with axis labels, visually distinct from each other. Prior
  lines are removed before each update so there are never stale/duplicate lines.
- **Thesis markers** render through the EXISTING series-marker mechanism, **visually distinct from
  tape-state markers**: tape-state markers stay ABOVE the bar with a down-arrow; thesis markers sit
  BELOW the bar — a circle for verdict-transition / first-confirmation (verdict palette: confirming
  emerald, weakening amber, rejecting/invalidated rose, pending/expired slate), and an up-arrow for
  the user's entry/exit marks (slate-200, with the verbatim mono price in the label). Both marker
  owners funnel through one `setCombinedMarkers()` that sets their union sorted by time (the library
  replaces the whole marker set on each `setMarkers`).
- **X-placement** uses the SAME canonical epoch anchor the candles use (`epoch_anchor +
  logical_ts`, the established J-31 additive display offset). The chart computes no state, side,
  price, or time basis of its own.

## Files Changed
- `apps/frontend/lib/types.ts` -- `GeometryPriceLine`, `GeometryMarker`, `ThesisGeometry` types; optional `geometry` field on `ThesisProjection`.
- `apps/frontend/components/PriceChart.tsx` -- `thesis` prop; verdict/price-line/mark color maps (DESIGN SYSTEM tokens); price-line refs + a geometry effect (draws lines + thesis markers, clears on null); the combined-markers helper that unions engine + thesis markers.
- `apps/frontend/app/page.tsx` -- passes `snapshot?.thesis ?? null` into `PriceChart`.

## Design-system conformance
- Colors are the established load-bearing semantics only: emerald = confirming/buy, rose =
  rejecting/invalidated/sell, amber = weakening/absorption, slate = pending/level/neutral, slate-200
  = the user's own marks. Hex values mirror the configured Tailwind tokens (the charting canvas
  takes raw colors, not classes).
- Marker/line labels are backend-served or verbatim verdict-enum copy — present-tense, descriptive,
  never imperative or predictive ("Descriptive only — not trading advice" register extends to the
  chart).
- No new chart capability beyond the geometry overlay (no pan/zoom/tooltip/click/drawing additions),
  honoring the Stay-in-scope / No-execution anti-goals.

## Tests Run
- `npx tsc --noEmit` — clean (lightweight-charts 5.2.0 API verified for every symbol used).
- `next dev` — compiles and serves `/` => HTTP 200; no compile errors in the dev log.
- Frontend behavior is covered by browser QA in the qa step (per project-template — no frontend unit suite).

## Known Issues / QA notes for the browser leg
- Per the binding lessons: the chart is below the fold — SCROLL IT INTO VIEW (or capture full-page)
  before every chart assertion; run the server-freshness canary first; capture the pre-cross
  (pending, lines only) and post-confirmation (markers) moments WHILE the SIM-BUYER watch is live
  (it is a bounded stream); use `NEXT_DIST_DIR=.next-qa` for any build.
- Live-mode chart render is operator-gated (credentials/market-hours); the same component renders it
  — note explicitly in results, do not skip silently.
