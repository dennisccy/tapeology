# goal-i_will_be_rich-iter-5 Frontend Handoff

**Phase:** goal-i_will_be_rich-iter-5
**Date:** 2026-06-03
**Agent:** developer
**Status:** complete

## What Was Built

All changes live within the existing `/` cockpit — no new page, route, or navigation.

- **Features panel — three new rows.** `Absorption score`, `Bid refresh score`, and
  `Ask refresh score` were appended to the fixed feature list. They render with monospaced
  numerics at 3 decimals, neutral (slate) text — they are not color-by-sign. When a value is
  absent the existing `Metric` null treatment shows "—". The existing nine rows are unchanged.
  This makes the absorption / refresh readouts visible, which J-04/J-05 require the operator
  to read.
- **Two newly reachable amber tape states.** `bid_absorption` → "Bid Absorption" and
  `ask_absorption` → "Ask Absorption" already resolved to amber via `lib/format.ts`
  (`stateColor` → `text-amber-400`, `stateBarColor` → `bg-amber-500`, `stateLabel`). No change
  was needed there; the new backend streams simply make those states reachable on screen.
- **Top-bar stream-status dot — now driven by the engine.** The dot previously read only the
  client-side `connStatus`. It now reads the canonical `snapshot.stream_status` whenever a
  snapshot is present (mapping connecting → amber-pulse, live → emerald, stale → amber,
  closed → rose), and falls back to `connStatus` only for the pre-snapshot idle/connecting
  affordance. An unrecognized status is surfaced honestly (slate dot + the raw label) rather
  than hidden. This removes the parallel client "is the stream live" source and fixes the real
  bug where an exhausted/closed engine stream still showed a stale "live".

## Files Changed

- `apps/frontend/components/FeaturesPanel.tsx` — three absorption rows added to `FEATURE_ROWS`.
- `apps/frontend/components/TopBar.tsx` — `CONN_DOT` (pre-snapshot fallback) + `STREAM_DOT`
  (canonical engine status) maps; the dot/label now derive from `snapshot.stream_status` with
  a `connStatus` fallback.

## Visual / Design-System Conformance

- **Color semantics preserved:** green = buy/positive, red = sell/negative, amber =
  absorption/unclear. The absorption states use the amber tokens exactly; the new feature rows
  are neutral readouts (not directional), so they correctly avoid green/red.
- **Layout unchanged:** the 1/2/3-col responsive cockpit grid is untouched; the rows append to
  the Features panel and the absorption states render in the existing Tape-state panel.
- **No new component types or effects** — reused the existing `Panel`/`Metric` row pattern and
  the existing status-dot affordance (restrained borders + dot, per DESIGN SYSTEM).
- **States handled:** live (resolved absorption render), warm-up/cold-start (honest `unclear`
  before evidence; "—" for absent feature values), and the dot's
  connecting/live/stale/closed states.

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: **Compiled successfully** — type-check + production build clean (route `/` 3.9 kB).

## Known Issues

- The first on-screen **computed-style amber probe** (headline `text-amber-400` +
  confidence-bar `bg-amber-500`, base-selector + `getComputedStyle`, excluding `:hover`/variant
  forms) for a *resolved* absorption state is the browser-QA gate. Build-level prerequisites are
  confirmed: the `./lib/**` Tailwind content glob (iter-3) is in place and the base selectors
  `.text-amber-400{…}` and `.bg-amber-500{…}` are present in the served CSS bundle.
- The dot's `stale` mapping exists but no backend path emits `stream_status = "stale"` yet, so
  that branch is currently unreachable in practice (defensive).
