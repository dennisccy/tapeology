# goal-desk-iter-23 Frontend Handoff

**Phase:** goal-desk-iter-23
**Date:** 2026-07-30
**Agent:** developer
**Status:** complete

## What Was Built

`/desk`'s ranked-rows table (`apps/frontend/app/desk/page.tsx`) gains one new `levels` column,
placed after the existing `opposite` column (the tail-append pattern every prior iteration used for
basis/history/band/opposite). It renders, verbatim, three new fields the backend now serves on
every ranked row of a NEW screen snapshot:

- A tally string: `${band_member_count} levels · ${timeframe} ${count} · ...` — e.g. `155 levels ·
  1d 68 · 1h 57 · 4h 19 · 1w 11`. Built with a plain `Object.entries(...).map(...).join(" · ")` over
  `row.band_member_timeframes` — no client-side counting, arithmetic, or re-derivation of any kind.
- `/structure`'s own "round number" badge, reused byte-for-byte (same `data-testid=
  "tradable-band-round-number"`, same className — `inline-block whitespace-nowrap rounded border
  border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[11px] text-slate-300`), rendered only when
  `row.band_round_number` is true.
- The established legacy-absence copy `"composition not recorded in this snapshot"` when
  `row.band_member_count`/`row.band_member_timeframes` are `undefined` (a screen snapshot recorded
  before this iteration never carries these keys at all).

No new tooltip line was added: unlike basis/history/band(reference_close)/opposite, all three new
values are exact integers/booleans with no rounded display, so there is no full-precision detail to
surface on hover.

## Files Changed

- `apps/frontend/lib/types.ts` — `DeskScreenRow` interface gains `band_member_count?: number`,
  `band_round_number?: boolean`, `band_member_timeframes?: Record<string, number>`.
- `apps/frontend/app/desk/page.tsx` — new `<td data-testid="desk-row-levels">` cell in `DeskRow`;
  new `<th>levels</th>` header cell in `DeskRowsTable`; page-header comment block documents the
  addition.

## UI Evolution

- New user-facing capability: every ranked `/desk` row now discloses how many levels its selected
  wall is built of, whether it's a round-number band, and the per-timeframe split — the same
  composition detail `/structure`'s own band table already shows for the identical band.
- New information displayed: `band_member_count`, `band_round_number`, `band_member_timeframes`.
- New user actions: none — pure disclosure, no new button or control.
- UI surface changes: `/desk` ranked table gains one column (`levels`); no new page, no new
  section, no navigation change.
- Visual pattern: plain `<td>`/`<th>` using the existing `LABEL_CELL`/`HEADER_CELL_LEFT` classes
  already used by every sibling column on this table — no new component, no new visual effect.

## Verification Done

- `npx tsc --noEmit` — clean, zero errors.
- `rm -rf .next && npx next build` — compiles, lints (Next's built-in ESLint), and type-checks
  cleanly; `/desk` route builds to a static page as before (7.98 kB, 117 kB First Load JS).
- `scripts/dev.sh` start/stop/restart cycle — both `GET /desk` (frontend) and `GET
  /research/desk/screen` (backend) returned HTTP 200 on both runs.
- No frontend unit/component test framework exists in this repository at all (confirmed via a
  repo-wide search: no jest/vitest config, no `test` script in `package.json`, no existing
  `*.test.*`/`*.spec.*` file anywhere). Every prior `/desk` iteration (J-08 through J-14) shipped
  its column additions the same way — TypeScript + build verification here, full behavioral
  verification via the browser-qa-agent lane. This iteration follows that same established
  convention rather than introducing new test infrastructure mid-iteration.

## Known Issues

None from the frontend side. Actual browser rendering (populated tally text + round-number badge
legible together, per TC-10/TC-11) is the browser-qa-agent's responsibility on the fixture-scoped
rig — not exercised by this dev pass beyond the plain HTTP-200 service-startup check above.
