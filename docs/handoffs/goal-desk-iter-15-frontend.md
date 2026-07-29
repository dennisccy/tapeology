# goal-desk-iter-15 Frontend Handoff

**Phase:** goal-desk-iter-15
**Date:** 2026-07-29
**Agent:** developer
**Status:** complete

## What Was Built

- `/desk`'s ranked briefing table gains one new column, **`history`**, beside the existing `basis`
  column — showing, per ranked row, how many completed daily sessions (and from what start date)
  the row's wall was measured over (e.g. `history 500 sessions · from 2024-07-25`).
- Legacy rows (screen snapshots recorded before this iteration) render the honest fallback text
  `"history not recorded in this snapshot"` instead of a value — never blank, never the literal
  string `"null"`.
- The row's existing drill-in anchor composite hover tooltip (`deskRowDrillInTitle`, the F2
  consolidation pattern from iter-7) gains one more detail line: the full-precision
  `history_sessions`/`history_start`, alongside the existing distance/score/basis/coverage
  details — zero change to the anchor's `href`, `absolute inset-0` class, `data-testid`, or click
  geometry.
- Skip rows (no bars / no basis) are unaffected — they never had a history cell and still don't.
- No new page, no new nav entry, no new button/control — this is disclosure-only, matching the
  J-08 (basis column) precedent structurally.

## Files Changed

- `apps/frontend/lib/types.ts` — `DeskScreenRow` interface gains `history_sessions: number | null`
  and `history_start: string | null`.
- `apps/frontend/app/desk/page.tsx` — new `history` `<th>` header and `<td data-testid=
  "desk-row-history">` cell in the ranked table's `DeskRowsTable`/`DeskRow` components; the
  `deskRowDrillInTitle` tooltip builder gains a `historyLine` alongside the existing `basisLine`.

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit -p tsconfig.json` → clean, zero errors.
Command: `cd apps/frontend && rm -rf .next && npm run build` → compiled successfully; `/desk`
route: 7.26 kB page size, 117 kB First Load JS.

Backend-side coverage of this frontend surface: `apps/backend/tests/test_desk_hover_tooltip_guard.py`
(source-introspection guard proving the tooltip function references `row.history_start`) and
`apps/backend/tests/test_copy_discipline.py` (frontend-literal copy lint, covers the new column
copy automatically — passed unmodified, 30 tests).

## Known Issues

- No actual browser screenshot was captured by this dev dispatch (browser-QA is a downstream
  agent's job). Instead, end-to-end confirmation was done via: (1) `tsc`/`next build` static
  verification, (2) grepping the compiled `.next` bundle for the new `data-testid`/copy strings to
  confirm the build picked up the source change, and (3) a live backend check (see the dev
  handoff's "Live verification" section) proving the API this page consumes actually serves
  `history_sessions` ranging from 27 to 501 across a real computed screen — i.e. the data a
  browser pass would need to screenshot genuinely exists and is genuinely wide-ranging in the real
  store today. The visual screenshot proof (TC-8: a `<=60` row and a `>=400` row legible together;
  TC-9: hovering shows `history_start` in the tooltip) is left to the browser-QA lane.
- The golden replay script (`runs/goal-session-desk/journey-scripts/J-11.json`) intentionally
  checks only generic substrings (`"history"` header, `"sessions"` cell text) rather than a
  specific session count, since `demo_runner.py`'s replay format has no numeric-range assertion and
  goal.md's own J-11 rationale explicitly warns against pinning a specific cited number as a
  byte-for-byte replay target.
