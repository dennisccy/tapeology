# goal-desk-iter-26 Frontend Handoff

**Phase:** goal-desk-iter-26
**Date:** 2026-07-30
**Agent:** developer
**Status:** complete

## What Was Built

`/desk`'s already-shipped Top-up Runs section (`apps/frontend/app/desk/page.tsx`) is extended with
J-17's window-honesty disclosure — no new section, no new control, and no new ranked-table column
(J-16's measured width contract is untouched):

- `topupOutcomeCounts` gains an `unchanged` bucket; the latest-run counts line renders `N reused ·
  N fetched · N unchanged · N failed` (was `N reused · N fetched · N failed`).
- `topupWindowBasisCounts` (new function) is a plain tally of the served payload's own
  `window_basis` field on every outcome in the latest run — nothing derived, nothing computed
  beyond a count. It returns `null` when ANY outcome lacks `window_basis` (a legacy, pre-iter-26
  run — a single shared writer lands a run's outcomes all at once, so a run is either entirely
  legacy or entirely new, never a mix), which the render layer maps to a new shared constant,
  `WINDOW_BASIS_NOT_RECORDED = "window basis not recorded in this run"`, rather than a guessed or
  backfilled count. A new descriptive line renders either that fallback or `"N pairs asked for a
  tail window · M pairs asked for the full lookback window"` (singular/plural handled per count).
- Each already-rendered failed pair's row gains its own recorded `requested_window`
  (`requested YYYY-MM-DD → YYYY-MM-DD`) when present, or the same shared fallback text when the run
  predates this iteration.
- Copy stays descriptive measurement only — counts and windows, never a saving/efficiency/speed or
  recommendation claim (`test_copy_discipline.py` passes unmodified).

## Files Changed

- `apps/frontend/lib/types.ts` — `DeskTopupOutcome.outcome` gains the `"unchanged"` literal;
  the interface gains four optional fields (`requested_window`, `store_frozen_from`,
  `store_frozen_through`, `window_basis`) with a doc comment explaining the legacy-run absence
  contract, matching the established per-iteration convention (J-08/J-11/J-13 precedent).
- `apps/frontend/app/desk/page.tsx` — `topupOutcomeCounts` extended; `topupWindowBasisCounts` +
  `WINDOW_BASIS_NOT_RECORDED` (both new); `LatestTopupRunDetail` renders the extended counts line,
  the new tail-vs-full-lookback line, and each failed pair's own `requested_window`; section-header
  comment block gains a "goal-desk-iter-26 (J-17)" note.

## UI Evolution

- New user-facing capability: the operator can now see, per top-up run, whether each pair's fetch
  used a tail window or the full lookback, an honest `unchanged` count when the vendor returned
  nothing new, and each failed pair's own exact requested window.
- New information displayed: per-run outcome counts including `unchanged`; a tail-vs-full-lookback
  pair-count line; a `requested_window` line on each already-rendered failed pair.
- New user actions: none — the existing Top-up button and its trigger/poll/cancel flow are
  unchanged; this is a disclosure enhancement on an already-shipped section.
- UI surface changes: Top-up Runs section content only (no new page, no new nav row, no new
  control, no new ranked-table column).
- Visual pattern: plain text lines using the section's existing `text-xs text-slate-400` /
  `text-amber-200/70` styling already used by the sibling `unreached` line — no new component, no
  new visual effect.

## Verification Done

- `./node_modules/.bin/tsc --noEmit` — clean, zero errors.
- `rm -rf .next && npx next build` — compiles, lints (Next's built-in ESLint), and type-checks
  cleanly; `/desk` route builds to a static page as before (8.44 kB, 118 kB First Load JS).
- `scripts/dev.sh` start/stop/restart cycle — both `GET /desk` (frontend, HTTP 200) and `GET
  /research/desk/topup/runs` (backend) returned successfully on both runs; the real ambient
  store's one pre-iteration top-up run (`topup-2026-07-29-5de907c83fc4`) correctly lacks the four
  new fields, exercising the legacy-absence fallback path against real data.
- A new backend-side source-introspection guard test
  (`apps/backend/tests/test_desk_topup_window_disclosure_guard.py`, the established
  `test_desk_ui_guards.py` pattern) proves the fallback text is a single shared constant (never a
  second, independently-typed copy), the four-outcome counts line is present, and
  `topupWindowBasisCounts` returns `null` (never a guessed/backfilled count) rather than exercising
  a frontend component-test framework — no frontend unit/component test framework exists in this
  repository (confirmed by every prior `/desk` iteration's own handoff); this iteration follows
  that same established convention.

## Known Issues

None from the frontend side. Actual browser rendering of the four-outcome counts line (with a
real `unchanged` > 0), the tail-vs-full-lookback line, and a failed pair's `requested_window` all
legible together in one screenshot (TC-6) is the browser-qa-agent's responsibility on a fresh,
fixture-scoped rig — not exercised by this dev pass beyond the plain HTTP-200 service-startup check
above (which used the real ambient store, correctly showing only the legacy-fallback state since
no new-shape run has been recorded there).
