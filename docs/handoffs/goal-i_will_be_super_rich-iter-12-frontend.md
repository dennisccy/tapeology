# goal-i_will_be_super_rich-iter-12 Frontend Handoff

**Phase:** goal-i_will_be_super_rich-iter-12
**Date:** 2026-06-08
**Agent:** developer
**Status:** complete

## What Was Built (UI)

- **True-clock price-chart axis (J-31).** The chart's time axis ticks, crosshair tooltip, and
  tape-state-marker stamps now read **real clock time** (`dd-MM-yyyy HH:mm:ss`, 24h, in the
  operator's local zone) instead of an elapsed 0…600 s playback counter. For Historical this is the
  real market clock time; for Simulated it is a synthetic session clock anchored to 09:30 ET (a real
  clock face). Switching bar size 10 / 30 / 60 s keeps the real-time axis. The chart still reads
  `GET /tape/{ticker}/history` verbatim and computes no price/side/state — true time is the backend
  `epoch_anchor` plus the candle's logical bin time, a pure additive offset.
- **One consistent `dd-MM-yyyy` date format everywhere (J-35).** Every date the UI shows now routes
  through one shared formatter (`formatDateDMY` / `formatDateTimeDMY`): the chart axis + crosshair +
  markers, the Live market-status "next open" time, the closed-market panel, and the watched-source
  descriptor (`historical AAPL <window>` now shows `dd-MM-yyyy HH:mm`, not ISO). No `MM/DD/YYYY`,
  ISO `YYYY-MM-DD`, or "Jun 8"-style date remains visible.
- **Custom `dd-MM-yyyy` date input.** The Historical date picker's native `<input type="date">` is
  replaced by a validated `dd-MM-yyyy` text field (placeholder `dd-MM-yyyy`). It carries the same
  explicit local zone label and resolves to the same tz-aware instant as before (no UTC shift). An
  invalid date (`31-02-2026`, malformed, empty) shows inline validation and the field border turns
  amber — the Watch never silently no-ops.

## Files Changed

- `apps/frontend/lib/datetime.ts` -- the shared formatter, the `dd-MM-yyyy` parser/validator, and the watched-source reformat.
- `apps/frontend/lib/types.ts` -- `TapeHistory.epoch_anchor`.
- `apps/frontend/lib/api.ts` -- read `epoch_anchor` from `/history`.
- `apps/frontend/components/PriceChart.tsx` -- true-clock axis + crosshair + markers.
- `apps/frontend/components/TopBar.tsx` -- custom `dd-MM-yyyy` input, inline validation, descriptor formatting.

## UI Evolution

- New capability: read the chart's time axis as real market clock time (historical) or a synthetic
  session clock (simulated); one consistent `dd-MM-yyyy` date format across the product; enter
  historical dates via a `dd-MM-yyyy` field.
- New information: true clock-time stamps on the chart axis/crosshair/markers; `dd-MM-yyyy` dates
  wherever dates were previously locale/ISO/elapsed-formatted.
- New action: the custom `dd-MM-yyyy` date text field (replacing the native picker), with inline
  validation.
- Surface: the existing price-chart pane and the existing Historical date/time picker, both on the
  single `/` HOME cockpit. No new pages, panels, or routes; navigation unchanged.

## States Handled

- Loading: "Loading price history…" (chart not yet fetched).
- Empty: "No price history for this window yet" — empty chart, no fabricated candles/timestamps
  (anchor absent → no time fabricated).
- Invalid date: inline amber validation ("Enter a valid date as dd-MM-yyyy.") and an amber field
  border; Watch stays disabled until the window is valid.

## Design-System Conformance

- Reused the existing `Panel` / `EmptyHint` and the existing `INPUT_CLASS` text-input styling for
  the new date field. No new component library, no new colors — load-bearing green/red/amber marker
  semantics preserved on the chart. The chart remains the single candlestick + markers pane (no
  indicators/studies/drawing tools).

## Verification

- `npm run build` passes (type-check + static generation).
- `datetime.ts` pure functions verified standalone under two timezones (14/14 assertions),
  including the J-20 no-UTC-shift invariant. See the dev handoff for details.
- A real rendered-PNG browser check of the populated chart's clock-time axis is still required by
  the spec (browser-qa / operator step), per the iter-6/7/8 visual-journey lesson.
