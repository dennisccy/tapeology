# goal-i_will_be_super_rich-iter-12 Execution Plan

True-clock chart axis (J-31) + dd-MM-yyyy dates everywhere (J-35). These two journeys
are delivered together as one coherent "time display" outcome. Depth: full (a NEW
data-contract value crosses the backend↔frontend boundary and needs backend unit tests).

## What to Build

- **Backend — additive canonical epoch/display anchor (NEW data-contract row 13).**
  - The engine's logical timeline already starts at `t0 = first record's real UTC epoch`
    (`historical.py` line 55; `live.py` line 51-53). That `t0` is exactly the anchor.
    Preserve it ONCE alongside the existing logical timeline and expose it read-only.
  - For **historical/live**: anchor = the first real record's UTC epoch (so
    `true_clock = anchor_epoch + logical_ts`).
  - For **simulated**: anchor = a synthetic session-start instant, computed once from a
    config-owned convention (a fixed synthetic session-start; an inline literal is forbidden —
    add to `app/config.py`). The sim engine still bins on its deterministic logical timeline.
  - Carry the anchor on the snapshot/engine (additive field, defaulted so all existing
    snapshots/tests are unchanged) and surface it through the `GET /tape/{ticker}/history`
    projection (`serialize_history`) — the chart's single source for true time. Re-expose on
    `/summary` / `WS /stream` only if the chart needs it from those (history is sufficient).
  - The anchor is **display metadata only**: it does NOT feed classification; the engine still
    bins on the deterministic logical timeline; the same ordered stream yields byte-identical
    features/state/confidence.

- **Frontend — one shared dd-MM-yyyy formatter + true-clock chart axis + custom date input.**
  - Add `formatDateDMY(date)` → `dd-MM-yyyy` and `formatDateTimeDMY(date)` →
    `dd-MM-yyyy HH:mm[:ss]` (24h, local zone, explicit zone label where a date-time is shown)
    to `apps/frontend/lib/datetime.ts`. Route EVERY existing date/date-time render through it.
  - `PriceChart.tsx`: replace `time: Math.round(b.time)` (elapsed logical seconds) and the
    marker `time` with **true clock time** = `anchor_epoch + logical_ts` (epoch-seconds the
    lightweight-charts time scale understands), so axis ticks, crosshair, and marker stamps
    read real clock time. The chart still reads `/history` verbatim and recomputes no
    price/side/state. Switching bar size 10/30/60 s keeps the real-time axis. An empty window
    still yields an empty chart (no fabricated timestamps).
  - Replace the native `<input type="date">` in `TopBar.tsx` (line 246-252) with a custom,
    validated `dd-MM-yyyy` text input. It still carries the explicit local zone label and must
    resolve to the SAME tz-aware instant as today via the existing row-12 resolver
    (`resolveLocalWindowInstant`) — convert `dd-MM-yyyy` → the internal `YYYY-MM-DD` the
    resolver expects so there is NO silent UTC shift (J-20 must stay green). Invalid input
    (`31-02-2026`, malformed, empty) → inline validation, never a silent no-op (J-24).
  - Audit + convert every remaining date render to the shared formatter:
    `MarketStatusIndicator.tsx` / `ProviderUnavailable.tsx` (currently `formatMarketTime`
    producing "Jun 8" / locale form), and the watched-source descriptor / any real-data
    recent-trade & event timestamps. No `MM/DD/YYYY`, ISO `YYYY-MM-DD`, or "Jun 8" remains.

## Agents Required

- developer: yes -- backend anchor (engine/snapshot/serializer/config + unit tests) AND
  frontend (shared formatter, true-clock chart axis, custom dd-MM-yyyy input, date-render audit).
  Both backend and frontend changes are in scope for this single iteration.

## Frontend Present
yes

## Files to Create/Modify

- `apps/backend/app/config.py` -- add the simulated synthetic-session-start anchor constant (no inline literal).
- `apps/backend/app/engine/snapshot.py` -- additive `epoch_anchor` (or similarly named) field, defaulted.
- `apps/backend/app/engine/tape_engine.py` and/or feeder/`watch_manager.py`/providers -- preserve the first-real-epoch (or sim synthetic) anchor ONCE; thread it into the snapshot/history buffer.
- `apps/backend/app/engine/history.py` -- expose the anchor on the history buffer (additive read-only) if the projection reads it from there.
- `apps/backend/app/serializers.py` -- `serialize_history` includes the anchor; bar/marker `time` stay logical (chart adds the anchor) OR projection emits true-clock — pick one and keep single-source-of-truth (no recompute outside engine). Document the choice in the dev handoff.
- `apps/backend/tests/` -- new backend tests (anchor exposed for historical + sim; determinism preserved under the additive anchor).
- `apps/frontend/lib/datetime.ts` -- shared `formatDateDMY` / `formatDateTimeDMY`; `dd-MM-yyyy` parse/validate helper for the custom input that feeds the existing row-12 resolver.
- `apps/frontend/components/PriceChart.tsx` -- map logical bar/marker time → true clock via the anchor; axis/crosshair/markers in `dd-MM-yyyy HH:mm:ss`.
- `apps/frontend/components/TopBar.tsx` -- custom validated `dd-MM-yyyy` text input replacing the native date picker; inline validation.
- `apps/frontend/components/MarketStatusIndicator.tsx`, `apps/frontend/components/ProviderUnavailable.tsx` -- route times through the shared formatter.
- `apps/frontend/components/RecentTradesPanel.tsx` / `EventLogPanel.tsx` -- IF real-data timestamps are to be shown, render them as `dd-MM-yyyy HH:mm:ss` via the anchor + shared formatter (see Assumption below).

## UI Evolution

- New user-facing capability: the chart's time axis reads real market clock time (historical)
  or a synthetic session clock (simulated) instead of a 0…600 s playback counter; the whole UI
  shows one consistent `dd-MM-yyyy` date format; historical dates are entered via a `dd-MM-yyyy` field.
- New information displayed: true clock-time stamps on the chart axis / crosshair / markers
  (`dd-MM-yyyy HH:mm:ss`); `dd-MM-yyyy` dates everywhere they were previously locale/ISO/elapsed.
- New user actions: a custom `dd-MM-yyyy` date text field (replacing the native date picker) in
  the Historical controls, with inline validation.
- UI surface changes: the existing price-chart pane (axis/crosshair/marker labels) and the
  existing Historical date/time picker — both on the single `/` HOME cockpit. No new pages/panels/routes.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse existing hand-built panels (`Panel`, `EmptyHint`); the chart stays
  the single lightweight-charts candlestick pane (no indicators/studies/drawing tools — anti-goal).
  The custom date field reuses the existing `INPUT_CLASS` text-input styling.
- Layout: unchanged — chart pane above the cockpit on `/`; the date field sits where the native
  picker was in the Historical control row.
- Key visual effects: unchanged dark instrument-panel surface; load-bearing green/red/amber
  marker semantics preserved.
- States to handle: loading ("Loading price history…"), empty ("No price history for this window
  yet" — empty chart, no fabricated timestamps), and inline date-validation error on the new field.

## Key Test Scenarios

- **J-31 (browser, real evidence required):** Historical replay of a real symbol over a known
  past intraday window — poll backend `/history` for bars >= 5 FIRST, then capture a REAL rendered
  screenshot of the populated chart whose axis/crosshair/markers show real market clock time
  (`dd-MM-yyyy HH:mm:ss`, local zone label), NOT a 0…600 s counter; switching bar size keeps the
  real-time axis. A `SIM-*` ticker shows a synthetic session-clock axis (a real clock face).
  If the shared `:3650` `.next` is corrupted, build into an isolated `NEXT_DIST_DIR` wired to the
  running backend and open the PNG bytes — an idle/placeholder shot is NO evidence.
- **J-35 (browser):** every UI date reads `dd-MM-yyyy` (date-times `dd-MM-yyyy HH:mm[:ss]`, 24h):
  chart axis/crosshair, market-status times, watched-source descriptor, real-data trade/event
  timestamps, and the historical picker; no `MM/DD/YYYY`, ISO, or "Jun 8" remains. The native date
  picker is replaced by a working custom `dd-MM-yyyy` field that still Watches a valid window.
- **Backend unit:** the engine/feeder preserves a correct anchor (historical = first real record
  epoch; simulated = synthetic session-start); the history projection exposes it; the SAME ordered
  event stream still yields byte-identical features/state/confidence (additive anchor; determinism
  preserved); no regression in the existing backend suite.
- **Frontend unit (if runnable):** the shared formatter renders `dd-MM-yyyy` / `dd-MM-yyyy HH:mm:ss`
  for representative instants; the custom input parses/validates `dd-MM-yyyy` and resolves (via the
  row-12 resolver) to the SAME tz-aware instant as the prior native input for the same local date
  (no UTC shift — guard against a J-20 regression).
- **Error cases:** invalid `dd-MM-yyyy` (`31-02-2026`, malformed, empty) → inline validation,
  never a silent no-op (J-24 green); an empty historical window → empty chart, no fabricated axis
  timestamps.
- **Regression:** J-01–J-30 stay green — especially J-17/J-18 chart render, J-20 local-time window,
  J-08 single-source-of-truth, and all five sim classification scenarios J-01–J-09.

## Assumptions (recorded per token policy)

- **Recent-trade timestamps:** `RecentTradesPanel` currently shows NO timestamp column (only
  price/size/side). J-35 names "recent-trade / event timestamps on real data" as a place dates
  must appear. Assumption: where a timestamp is rendered for real-data trades/events it goes
  through the shared `dd-MM-yyyy HH:mm:ss` formatter (converted from logical ts via the anchor).
  The developer may add a compact time column for real modes; this is in scope ONLY as a date-
  format pass, not a redesign. If no trade timestamp is currently shown anywhere, satisfying J-35
  for trades means there is simply no non-conforming date to fix — do not invent a new column
  beyond what the journey requires; prefer the minimal change and note it in the handoff.
- **Where the anchor is applied (engine vs. chart):** the chart adding `anchor_epoch + logical_ts`
  keeps the engine the single computing owner of the logical timeline and the anchor a verbatim
  read (preferred, matches "chart recomputes no price/side/state" because time mapping is a pure
  additive display offset). Either placement is acceptable provided no side/state/price is
  recomputed and the anchor is computed once in the engine/feeder.

## Scope guards (out of scope — excluded)

- J-32 (live replay-speed), J-33 (real-data classification calibration), J-34 (chunked long
  windows) — separate iterations; do NOT touch classification math, feature windows, or confidence.
- No change to the engine's logical timeline, the row-12 timezone resolution semantics, or the
  live-socket teardown / feeder lifecycle beyond reading/preserving the epoch origin.
- No new chart affordance (indicators, studies, drawing tools, pan/zoom changes, any order/
  execution control) — anti-goal: one focused chart only.
- The shared `dd-MM-yyyy` formatter is presentation-only — NOT a new computed/served value (no
  contract row); only the epoch anchor is the new contract row 13.

## Goal alignment

This iteration advances Success Criterion "Tape-state prediction chart … true clock time" and the
Constraint "Dates are entered and shown as dd-MM-yyyy … one shared formatter", and realizes Key
Capabilities #1 (display anchor) and #13 (true-clock time axis). It builds additively on the
existing `/history` projection and row-12 resolver — no duplication of prior work, no drift from
the goal. No spec/goal contradiction found.
