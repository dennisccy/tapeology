# goal-i_will_be_super_rich-iter-12 Dev Handoff

**Phase:** goal-i_will_be_super_rich-iter-12
**Date:** 2026-06-08
**Agent:** developer
**Status:** complete

## What Was Built

True-clock chart axis (J-31) + dd-MM-yyyy dates everywhere (J-35), delivered together as one
"time display" outcome.

- **NEW Data-Contract row 13 — canonical display/epoch anchor.** An additive `epoch_anchor`
  (real UTC epoch, seconds, that logical-time 0 maps to) is preserved ONCE in the engine/feeder
  from the provider and surfaced read-only through the `GET /tape/{ticker}/history` projection. The
  chart maps each logical bin time to a true clock instant as `epoch_anchor + logical_ts` (a pure
  additive offset — it recomputes no price/side/state). The engine still bins on its deterministic
  logical timeline; the anchor never enters classification.
  - Historical: anchor = the first real record's UTC epoch (the same `t0` the provider already
    subtracts to build the logical timeline).
  - Simulated: anchor = a config-owned synthetic session-start (`sim_session_anchor_epoch`,
    2024-01-02 09:30 ET = 1704205800.0) — a real clock face, not an elapsed 0…600 s counter.
  - Live: `None` (the prediction chart is shown for simulated + historical only).
- **One shared dd-MM-yyyy date/time formatter** (`formatDateDMY` / `formatDateTimeDMY`) routed
  through EVERY UI date render: the chart axis ticks + crosshair + markers, the market-status
  times, the provider-unavailable "next open", and the watched-source descriptor.
- **PriceChart true-clock axis**: axis ticks and crosshair render `dd-MM-yyyy HH:mm:ss` (24h, local
  zone) via the shared formatter; switching bar size keeps the real-time axis. Empty window still
  yields an empty chart (no fabricated timestamps).
- **Custom validated `dd-MM-yyyy` date input** in the Historical picker, replacing the native
  `<input type="date">`. It still carries the explicit local zone label and resolves to the SAME
  tz-aware instant via the existing row-12 resolver (no silent UTC shift; J-20 preserved). Invalid
  input (`31-02-2026`, malformed, empty) drives inline validation — never a silent no-op (J-24).

## Files Changed

Backend:
- `apps/backend/app/config.py` -- added `sim_session_anchor_epoch` (no inline literal in engine/provider code).
- `apps/backend/app/engine/snapshot.py` -- additive `epoch_anchor: float | None = None` field.
- `apps/backend/app/engine/tape_engine.py` -- accept `epoch_anchor` in constructor, expose `epoch_anchor` property, carry it on the snapshot.
- `apps/backend/app/providers/simulated.py` -- expose `epoch_anchor = CONFIG.sim_session_anchor_epoch`.
- `apps/backend/app/providers/historical.py` -- compute `epoch_anchor` = first real record epoch (min over quotes+trades; `None` for empty window).
- `apps/backend/app/providers/live.py` -- declare `epoch_anchor = None` (chart not shown for live).
- `apps/backend/app/watch_manager.py` -- `_provider_anchor(provider)` helper; thread the anchor into the engine on all three watch paths.
- `apps/backend/app/serializers.py` -- `serialize_history` includes `epoch_anchor` (bar/marker `time` stay logical; chart applies the anchor).
- `apps/backend/app/main.py` -- `/history` route passes `engine.epoch_anchor` to the projection.
- `apps/backend/tests/test_epoch_anchor.py` -- NEW: anchor provider values, snapshot carry, projection exposure, determinism-preserved.
- `apps/backend/tests/test_history_api.py` -- updated to assert the projection includes `epoch_anchor`.

Frontend:
- `apps/frontend/lib/datetime.ts` -- shared `formatDateDMY` / `formatDateTimeDMY`; `formatMarketTime` now `dd-MM-yyyy HH:mm`; `parseDMYToIsoDate` / `isValidDMY` for the custom input; `formatWatchedSource` reformats ISO instants in the descriptor.
- `apps/frontend/lib/types.ts` -- `TapeHistory.epoch_anchor: number | null`.
- `apps/frontend/lib/api.ts` -- `fetchHistory` reads `epoch_anchor` verbatim.
- `apps/frontend/components/PriceChart.tsx` -- map logical → true-clock via the anchor; axis/crosshair/marker timestamps via the shared formatter.
- `apps/frontend/components/TopBar.tsx` -- custom `dd-MM-yyyy` date input + inline validation; watched-source descriptor via `formatWatchedSource`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **238 passed, 1 skipped** (the gated live-integration test), 0 failed.

Command: `cd apps/frontend && npm run build`
Result: Compiled successfully; type-check + static generation pass.

Frontend pure-logic verification (no test runner configured for the frontend): the `datetime.ts`
functions were transpiled standalone and exercised under two timezones (America/New_York and
Asia/Hong_Kong) — 14/14 assertions passed, including the J-20 no-regression invariant that the
`dd-MM-yyyy` date resolves to the SAME tz-aware instant as the prior native ISO date, the
`31-02-2026`/malformed/empty rejections, and that the watched-source descriptor reformat leaves no
ISO `YYYY-MM-DD` visible.

Backend live smoke (isolated uvicorn on :8799, then killed): watching `SIM-BUYER` returned
`epoch_anchor = 1704205800.0`; `anchor + logical 0.0 = 2024-01-02T14:30:00Z` (09:30 ET — synthetic
session clock), and the `buyer_control` marker at logical 19.5 mapped to 09:30:19.5 ET. No uvicorn
left running.

## Key Design Choices

- **Anchor applied in the chart, not the serializer.** Bar/marker `time` stay LOGICAL in the
  history projection (the engine's single-source timeline); the chart adds `epoch_anchor + time` as
  a pure additive display offset. This keeps the engine the single computing owner and matches "the
  chart recomputes no price/side/state". The `serialize_history` projection still serves the
  canonical logical buffer verbatim; the anchor is carried alongside.
- **Simulated anchor is a fixed config constant, not wall-clock `now()`.** The synthetic session
  clock is reproducible and the engine remains deterministic (no wall-clock enters anywhere).
- **Recent-trades / event-log have NO timestamp column** (verified). J-35 names "recent-trade /
  event timestamps on real data" — since none are currently rendered, there is no non-conforming
  date to fix there. No new column was invented (per the plan's minimal-change assumption). If a
  future iteration adds a trade-time column, it must route through `formatDateTimeDMY` + the anchor.

## Known Issues

- **Live historical/real-data evidence requires vendor credentials.** The J-31 historical browser
  check (real symbol over a past window) and the J-18 real-chart regression need Alpaca credentials;
  without them, the sim true-clock axis (J-31 sim half) and J-17 markers are fully browser-verifiable
  and the historical anchor is covered by the backend fixture test (`test_epoch_anchor.py`).
- **No frontend unit-test runner** is configured (project convention: frontend behavior covered by
  browser QA + the type-checking build). The shared formatter / parser logic was instead verified
  via a standalone transpile-and-assert pass (documented above) and the production build's
  type-check.
- **lightweight-charts time axis** renders UTC-epoch seconds via the library; the local-zone
  `dd-MM-yyyy HH:mm:ss` rendering comes from the `tickMarkFormatter` / `localization.timeFormatter`
  callbacks (validated by the passing typed build). A real rendered-PNG browser check is still
  required by the spec to confirm the axis labels visually (operator/browser-qa step).
