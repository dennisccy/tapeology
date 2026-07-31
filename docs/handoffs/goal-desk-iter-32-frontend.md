# goal-desk-iter-32 Frontend Handoff

**Phase:** goal-desk-iter-32
**Date:** 2026-07-31
**Agent:** developer
**Status:** complete

## What Was Built

`/desk`'s already-shipped Top-up Runs section (`apps/frontend/app/desk/page.tsx`) is extended with
J-19's library-reach disclosure — no new section, no new control, and no new column on either the
ranked briefing table or the Top-up Runs summary table (J-16's measured width contract untouched):

- `topupLibraryReach` (new function) reads `store_frozen_through_after` off every outcome in the
  latest run — a plain read, nothing derived from bars. It computes the newest date across the
  run's own pairs plus how many pairs reach it, and the list of pairs whose own recorded value is
  earlier than that newest date (or `null`). It returns `null` when ANY outcome lacks
  `store_frozen_through_after` (a legacy, pre-iter-32 run), which the render layer maps to a new
  shared constant, `LIBRARY_REACH_NOT_RECORDED = "library reach not recorded in this run"`, rather
  than a computed or backfilled value.
- A new descriptive line (`data-testid="desk-topup-run-latest-reach"`), placed directly after the
  already-shipped `desk-topup-run-latest-window-basis` line, renders either that fallback or
  `"newest recorded reach YYYY-MM-DD · N pairs reach it"` (singular/plural handled per count).
- A short list (`data-testid="desk-topup-run-latest-reach-earlier"`, rendered only when non-empty)
  shows every pair recorded earlier than the newest date, one row each
  (`desk-topup-run-latest-reach-earlier-row`) with `symbol timeframe — date` (or `"no bars
  recorded"` for a `null` per-pair value) verbatim.
- Copy stays descriptive measurement only — dates and counts, never a fresh/stale/current/behind/
  up-to-date judgement, an advice/imperative/urgency/prediction, or a saving/efficiency/speed/
  recommendation claim (`test_copy_discipline.py` passes unmodified).

## Files Changed

- `apps/frontend/lib/types.ts` — `DeskTopupOutcome` gains one optional field,
  `store_frozen_through_after?: string | null`, with a doc comment naming the legacy-run absence
  contract (mirrors `store_frozen_through`'s own established convention).
- `apps/frontend/app/desk/page.tsx` — `topupLibraryReach` + `LIBRARY_REACH_NOT_RECORDED` (both
  new); `LatestTopupRunDetail` renders the new reach line and earlier-pairs list between the
  existing window-basis line and the existing failed-pairs block.

## UI Evolution

- New user-facing capability: the operator can now see, on the already-shipped Top-up Runs panel,
  the actual date each pair's frozen history reaches AFTER a run — not merely the window the run
  requested.
- New information displayed: one descriptive line (newest reach date + pair count) plus a short
  list of pairs whose own recorded reach date is earlier (symbol, timeframe, date each).
- New user actions: none — read-only disclosure inside an already-shipped panel, matching the
  J-09/J-17 precedent's explicit "no new control" scope.
- UI surface changes: Top-up Runs latest-run detail block content only (no new page, no new nav
  row, no new control, no new ranked-table or summary-table column).
- Visual pattern: plain text lines using the section's existing `text-xs text-slate-400` styling
  (the `desk-topup-run-latest-window-basis` sibling's own styling) plus the existing failed-pairs
  list's `text-[11px] font-medium text-slate-500` heading style for the earlier-pairs list header —
  no new component, no new visual effect.

## Verification Done

- `./node_modules/.bin/tsc --noEmit` — clean, zero errors.
- `rm -rf .next && npx next build` — compiles, lints (Next's built-in ESLint), and type-checks
  cleanly; `/desk` route builds to a static page as before (9.43 kB, 119 kB First Load JS).
- `scripts/dev.sh` start/stop/restart cycle — both `GET /desk` (frontend, HTTP 200) and `GET
  /research/desk/topup/runs` (backend, HTTP 200) returned successfully on both runs; the real
  ambient store's one pre-iteration top-up run (`topup-2026-07-29-5de907c83fc4`) correctly lacks
  `store_frozen_through_after` on every outcome, confirming the legacy-absence fallback path is
  exercised by real ambient data. Both servers stopped cleanly afterward (`fuser -k -9` on both
  ports, confirmed free via `ss -tln`); no stray tapeology process left running.
- A new backend-side source-introspection guard test
  (`apps/backend/tests/test_desk_topup_library_reach_guard.py`, the established
  `test_desk_topup_window_disclosure_guard.py` pattern) proves the fallback text is a single shared
  constant, the new block sits between the window-basis and failed-pairs blocks (no reordering, no
  new section), and `topupLibraryReach` returns `null` (never a guessed/backfilled date) rather than
  exercising a frontend component-test framework — no frontend unit/component test framework exists
  in this repository (confirmed by every prior `/desk` iteration's own handoff); this iteration
  follows that same established convention.

## Known Issues

None from the frontend side beyond what's already disclosed in the dev handoff. Actual browser
rendering of the new reach line and earlier-pairs list together with a real, varied
`store_frozen_through_after` spread, legible in one screenshot at 1440×900 with no horizontal
scroll (TC-10), and the `[NEW]`-flagged demo-narrator walkthrough, are the browser-qa/demo lanes'
responsibility on the ambient rig after a real top-up run is triggered — not exercised by this dev
pass beyond the plain HTTP-200 service-startup check above (which used the real ambient store,
correctly showing only the legacy-fallback state since no new-shape run has been recorded there
yet).
