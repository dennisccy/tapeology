# goal-i_will_be_super_rich-iter-10 Frontend Handoff

**Phase:** goal-i_will_be_super_rich-iter-10
**Date:** 2026-06-07
**Agent:** developer
**Status:** complete

## What Was Built (UI)

Two new in-place treatments in the single `/` cockpit area, plus two new status dots — all driven
ONLY by the canonical engine `stream_status` (read verbatim; no client-side guess, no recomputation
of any engine value). No new page, no new route, no new buttons/forms/controls, no nav change.

- **Waiting treatment (J-26)** — when the snapshot's `stream_status === "waiting"` (the stream is
  open but no first trade/quote has arrived), the cockpit shows an explicit, human-readable
  "Connected to `<SYMBOL>` (`<mode>`) — waiting for the first trade…" block IN PLACE OF the blank
  panel grid. Labelled with the symbol (monospaced) and the mode (Simulated / Live / Historical).
  Amber pulsing dot = in-progress; the status dot reads `waiting`, never a confident `live` over an
  empty tape. The block also states no tape is shown until real data arrives (no fabrication).
- **Post-connect failure treatment (J-27)** — when the snapshot's `stream_status === "failed"` (the
  background feeder raised after connecting — distinct from iter-9's pre-snapshot
  `connStatus === "failed"`), the cockpit reuses the existing `StreamFailedState` panel + the TopBar
  error banner. Never a mute/blank `live` cockpit, never frozen at "Connecting…".
- **Cold-start guard (J-25)** — an empty cold-start snapshot now arrives as `waiting` (or briefly
  `connecting`), so it can no longer short-circuit into the full cockpit grid as a settled `live`
  connection. A transient `connecting` snapshot routes to the existing `ConnectingState`.
- **Status dots** — `TopBar.tsx` `STREAM_DOT` gained `waiting` (amber + `animate-pulse`,
  consistent with `connecting`) and `failed` (rose, consistent with `StreamFailedState`).

## Files Changed

- `apps/frontend/components/IdleState.tsx` -- NEW `WaitingState({ symbol, mode })` component (reuses
  the existing `ConnectingState` / `StreamFailedState` honest-non-cockpit pattern: centered
  `min-h-[40vh]` block, amber pulsing dot, monospaced symbol, `data-testid="waiting-state"`,
  `aria-live="polite"`). Added a display-only `MODE_LABEL` map (sim→Simulated, live→Live,
  historical→Historical).
- `apps/frontend/components/Cockpit.tsx` -- renders `WaitingState` (with `snapshot.ticker`) when
  `stream_status === "waiting"` instead of the blank grid (backstop; the page does the primary
  routing with full mode context).
- `apps/frontend/app/page.tsx` -- computes `snapshotWaiting` / `snapshotFailed` /
  `snapshotConnecting` from the canonical snapshot; routes `failed` → `StreamFailedState` + banner,
  `waiting` → `WaitingState` (symbol + mode), transient `connecting` → `ConnectingState`; hides the
  price chart in all three (nothing to chart yet — no invented candles). The error banner now also
  surfaces a message for a snapshot-borne `failed`.
- `apps/frontend/components/TopBar.tsx` -- `STREAM_DOT` gained `waiting` (amber pulse) + `failed`
  (rose).
- `apps/frontend/lib/types.ts` -- extended the `stream_status` doc comment with `waiting` / `failed`
  (still a free `string`; no shape change).

## Design System Conformance

- Reused the established honest-non-cockpit component idiom (`ConnectingState` /
  `StreamFailedState`) — no new component library, no raw-div soup beyond the existing panel idiom.
- Colors per the DESIGN SYSTEM: `waiting` = amber (`bg-amber-400 animate-pulse`, in-progress,
  matching `connecting`); `failed` = rose (`text-rose-400` / `bg-rose-500`, matching the failure
  panel). Symbol rendered `font-mono`. No new effects invented.
- Layout: the waiting/failed treatments occupy the same centered cockpit real estate
  (single-column, `min-h-[40vh]` centered block) as the existing idle / connecting / failed states.
  The cockpit panel grid is unchanged.
- States handled: waiting (new), post-connect failure (new), plus the unchanged idle / connecting /
  cockpit / honest-panel / pre-snapshot-failure / paused states. The waiting treatment is itself the
  empty/loading state for a connected-but-quiet tape.

## Tests Run

`cd apps/frontend && NEXT_DIST_DIR=.next-devcheck npm run build` — compiled + type-checked cleanly
(route `/` = 10 kB). Built into an isolated dist dir to avoid touching the shared harness `:3650`
`.next` (iter-3/6/8 lesson); the build's auto-edits to `tsconfig.json` / `next-env.d.ts` were
reverted and the isolated dir removed (no build-artifact noise committed).

## DOM-Text Anchors for Browser QA

The waiting/failed treatments are fast/empty-path UI states (the placeholder-screenshot trap from
iter-9). Assert on DOM text, not just pixels, on a CLEAN isolated frontend:
- Waiting: `data-testid="waiting-state"`, text "waiting for the first trade", "Connected to
  `<SYMBOL>`", and the mode label; the TopBar status dot label reads `waiting` (NOT `live`).
- Post-connect failure: `data-testid="stream-failed-state"`, the rose `failed` dot, the error
  banner; "not stuck on Connecting", never a blank `live` cockpit.

## Known Limitations

- During the live `waiting` phase the Pause button is hidden (pause behavior is unchanged this
  iteration); Stop remains available. This is intentional scope discipline.
- The real-socket `waiting` / `stale` / `failed` UI is exercised here via the isolated-stack /
  provider-seam doubles; off-hours real-feed confirmation remains an operator/gated check (as for
  J-12 / J-15).
