# goal-desk-iter-29 Frontend Handoff

**Phase:** goal-desk-iter-29
**Date:** 2026-07-31
**Agent:** developer
**Status:** complete

## What Was Built

A new, read-only "Screen Runs" section on `/desk` -- the fourth ledger section, beside the shipped
Screen History / Top-up Runs / Index Reconciliation sections. It surfaces the new backend run log
(`GET /research/desk/screen/runs`) so the operator can see, for every screen run ever attempted --
including ones that reused an already-recorded snapshot, were cancelled, or failed -- a durable
record of what happened and how long it took.

- **Table** (`ScreenRunsTable`/`ScreenRunRow`): one row per recorded run -- date, run id, terminal
  state, members attempted-of-total, and what the run produced (a screen id, an honest
  `"reused <id> — no walk was performed"` note, or `"nothing recorded"` for a cancelled/failed
  run). Empty state: `"No screen runs recorded yet."` (`EmptyState`, the same component every
  sibling ledger's empty state already uses).
- **Latest-run detail** (`LatestScreenRunDetail`): state, members attempted-of-total, elapsed time
  (a plain difference of the run's own recorded `started_utc`/`finished_utc` -- never
  `Date.now()`), what it produced, an "N not reached" note when the run stopped early, the
  ranked/skipped-by-reason counts on a completed walk, and -- only when `state === "failed"` -- the
  raising member's name plus the exception detail rendered verbatim.
- **Integrity-errors note**: reuses the existing `IntegrityErrorsNote` component verbatim (the same
  one Screen History/Top-up Runs/Index Reconciliation already use).
- **Data flow**: a 7th mount-time GET (`fetchDeskScreenRuns`), plus the EXISTING screen-compute
  poll's terminal tick now also refreshes this list exactly once (the same "on terminal, refresh
  the durable list" precedent the Top-up/Reconcile polls already establish) -- so a run started via
  the Run Screen button appears in Screen Runs without a manual page reload.
- **No new control.** The existing Run Screen button is unchanged; its behavior on a duplicate-pin
  retrigger becomes cheaper (the backend's own reuse short-circuit), which is invisible at the
  button level -- only the new ledger discloses it.
- **No ranked-table change.** Zero edits to `DeskRow`/`DeskRowsTable`/the drill-in anchors -- J-16's
  measured width contract and every stored golden replay script stay untouched (confirmed:
  `test_desk_ui_guards.py`/`test_desk_hover_tooltip_guard.py` pass unmodified).

## Files Changed

- `apps/frontend/lib/types.ts` -- `DeskScreenRunMeta`, `DeskScreenRun`, `DeskScreenSkippedByReason`,
  `DeskScreenRunsListResult` (mirrors the existing `DeskTopupRun*`/`DeskReconcileRun*` shapes).
- `apps/frontend/lib/api.ts` -- `fetchDeskScreenRuns()` (mirrors `fetchDeskTopupRuns`/
  `fetchDeskReconcileRuns` byte-for-byte in shape).
- `apps/frontend/app/desk/page.tsx` -- the new section's components, state, mount-time fetch, poll
  extension, and render placement (fourth `<section>`, after Index Reconciliation).

## Visual / Copy Notes

- Same `Panel` + table/detail component pattern as Top-up Runs / Index Reconciliation -- same
  Loading/Unavailable/Populated state handling, same dark/dense/terminal-grade styling, same
  1440x900 no-horizontal-scroll constraint as its siblings. No new visual primitive, no new color,
  no new effect.
- Copy is descriptive measurement only: "no walk was performed", "nothing recorded", "N members
  attempted", "elapsed", "ranked", "skipped (no bars)", "skipped (no basis)", "N not reached" --
  no advice, imperative, urgency, prediction, or efficiency/speed claim.
  `tests/test_copy_discipline.py` passes unmodified against the new strings.

## Tests Run

- `npx tsc --noEmit` -- zero errors.
- Backend guard tests covering this page's own source
  (`test_desk_ui_guards.py`, `test_desk_hover_tooltip_guard.py`, `test_copy_discipline.py`) -- all
  green, unmodified.
- `bash scripts/dev.sh` started/stopped twice cleanly (backend :8301, frontend :3301); `curl
  http://localhost:3301/desk` returned 200 with the "Screen Runs" panel title present in the SSR
  shell (populated content is client-fetched after hydration, identical to its three siblings).

## Known Issues

- **Full browser verification (screenshots, the three states TC-10/TC-11/TC-12, and the
  demo-narrator walkthrough TC-13) was not performed by this agent** -- that is the
  browser-qa-agent's and demo-narrator's responsibility per the pipeline. This handoff's own checks
  (TypeScript compile, guard tests, a curl-level SSR sanity check) confirm the component renders and
  wires correctly but are not a substitute for the required browser acceptance evidence.
- **Elapsed-time rounding**: whole seconds/minutes only (mirrors `/structure`'s existing
  `formatComputeElapsed`); a sub-second run displays as "0s" (a display choice, not data loss -- the
  underlying record keeps microsecond-precision timestamps).
