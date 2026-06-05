# goal-i_will_be_super_rich-iter-7 Frontend Handoff

**Phase:** goal-i_will_be_super_rich-iter-7
**Date:** 2026-06-05
**Agent:** developer
**Status:** complete

## What Was Built

The watch-control cluster on `/` (the single tape-cockpit HOME) gains **Pause / Resume** beside the
existing **Stop**, plus a **PAUSED** state on the existing stream-status dot/label. No new page, no
new route, no new panel — the blueprint already places Pause/Resume + PAUSED in the persistent
app-shell watch controls. The prediction chart shipped in iter-6 is unchanged (render-verify only).

- **Pause / Resume buttons.** In `TopBar.tsx`, inside the existing `{watched && (...)}` Watching/Stop
  cluster. Plain `<button>` matching Stop's `rounded border … px-2.5 py-1 text-xs font-semibold`
  style, in **amber** (`text-amber-400`, `border-amber-400/70`, amber hover/focus/active) — amber is
  the load-bearing color for paused/stale/absorption/unclear. Each button has hover, focus, and
  active states. Resume shows while `paused`; Pause shows while the feed is active and not paused.
- **PAUSED status indicator.** One new `STREAM_DOT` entry (`paused` → amber dot, `paused` label),
  rendered by the existing status-dot pattern. The dot reads the engine's canonical `stream_status`
  — it reads **paused**, never **live**, while frozen.
- **Canonical, no client guess.** Visibility and the indicator are computed from
  `snapshot.paused` / `snapshot.stream_status` only — the UI never derives paused client-side.
  `paused` flows in both over the WS stream (`serialize_stream`) and the REST initial paint (added
  to `fetchInitialSnapshot`).

## Files Changed

- `apps/frontend/components/TopBar.tsx` -- Pause/Resume buttons; `paused` `STREAM_DOT` entry;
  `onPause`/`onResume` props; `paused` + `pauseable` computed from the canonical snapshot.
- `apps/frontend/app/page.tsx` -- `handlePause`/`handleResume` calling `pauseTicker`/`resumeTicker`;
  passed to `<TopBar>`. **No teardown** — pause does NOT call `stopTicker` and does NOT
  `setTicker(null)`, so the cockpit + chart stay mounted and freeze in place.
- `apps/frontend/lib/api.ts` -- `pauseTicker`/`resumeTicker` (POST via a shared `postWatchAction`;
  404 handled); `paused` carried into the REST initial snapshot.
- `apps/frontend/lib/types.ts` -- `paused?: boolean` on `TapeSnapshot`; documented `"paused"` as a
  valid `stream_status`.

## Behavior While Paused

- The cockpit (quote / recent trades / features / tape state) and the price chart **freeze** — the
  engine emits no new snapshots and accrues no new candles while paused, so the existing components
  simply stop updating. The UI does NOT clear or tear down the cockpit and does NOT fabricate a
  `live` reading. The chart keeps reading `/history` verbatim (it just gets no new candles).
- On **Resume** the WS stream resumes pushing fresh snapshots and the chart accrues candles again.
- On **Stop** (unchanged) the cockpit returns to idle and the WS closes client-side.

## States Handled

- **Pause shown**: `stream_status ∈ {connecting, live, stale}` and not paused.
- **Resume shown**: `paused === true` (status reads `paused`).
- Neither shown when the stream is `closed`/idle (nothing to pause).

## Tests Run

Frontend build: `cd apps/frontend && npx next build` (isolated `NEXT_DIST_DIR`, not the shared
`.next`) — compiled successfully, types clean. Route `/` First Load JS ~110 kB.

## Known Issues

- **J-17/J-18 render-verification is the browser-QA step's job** — no chart code changed here. The
  populated-candlestick screenshots must be captured on a CLEAN isolated build (isolated
  `NEXT_DIST_DIR` + isolated backend, NEVER the shared `:3650`/`.next`).
- The live QA-harness dev servers (`:3650`/`:3651`) were already running; I did not start or restart
  them and did not build against the shared `.next` (used an isolated dist for the type-check).
