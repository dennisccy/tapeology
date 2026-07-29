# goal-desk-iter-14 Frontend Handoff

**Phase:** goal-desk-iter-14
**Date:** 2026-07-29
**Agent:** developer
**Status:** complete

## Re-dispatch note

See the dev handoff's "Re-dispatch note" section for full context: this dispatch found the
frontend implementation below already complete and unmodified from an earlier pass of this same
iteration (already reviewer-PASS/QA-PASS/audit-PASS_WITH_GAPS). No frontend source file was edited
this dispatch; this handoff re-verifies `tsc`/copy-discipline fresh and re-states what shipped, and
records the new scoped-rig path this dispatch prepared for downstream browser evidence.

## What Was Built

`/desk` gains a third operator-triggered control ("Reconcile Index") and a third durable,
read-only history section ("Index Reconciliation"), sitting beside the existing "Top-up runs"
section. No new page, no nav change (nav stays exactly Cockpit / Structure / Desk).

- **`ReconcileIndexControl`** (`apps/frontend/app/desk/page.tsx`) — a button mirroring
  `TopupComputeControl`'s exact UX pattern: idle → "Reconcile Index"; running → "Reconciling…" with
  a pulsing-dot progress line reading the compute's own `progress.phase` label
  (classifying/reindexing/verifying) plus a Cancel button; failed → "Retry Reconcile Index" with the
  error surfaced; cancelled → a note that the index was not repaired that run. Rendered in BOTH
  places Top-up's own control already lives: the pre-screen empty state and the populated-screen
  "Run Screen / Top-up / Reconcile Index" panel (renamed to name all three controls it now holds).
- **`ReconciliationSection`** — a new, unconditional `<section aria-label="Index Reconciliation">`
  placed immediately after the existing "Top-up runs" section, always rendered regardless of
  whether a screen has ever been computed. Three states: loading, unavailable (fetch failed), and
  populated/empty — the honest empty state reads "No reconciliation run recorded yet."
  `IndexReconciliationTable` renders every recorded run's summary (date, run id, state, series on
  disk, rows indexed before → after); `LatestReconciliationDetail` renders the latest run's full
  before/after drift (every affected pair, labeled by which of the three honest buckets it came
  from) and any store errors (corrupt files), verbatim and legible.
- **Data flow**: two mount-time GETs (`fetchDeskReconcileCompute`, `fetchDeskReconcileRuns` — six
  total now), a third poll effect (mirrors the existing screen/top-up polls exactly: 700ms while
  `state === "running"`, refetch the durable run list once on terminal, "keep last known state on a
  failed refetch" preserved), and two handlers (`handleTriggerReconcile`, `handleCancelReconcile`).
  Page-load GETs still trigger zero computes.

## Files Changed (relative to the last committed state, iter-13)

- `apps/frontend/lib/types.ts` — nine new interfaces (`DeskReconcileUnindexedSeries`,
  `DeskReconcileOrphanRow`, `DeskReconcileStaleChecksumRow`, `DeskReconcileDrift`,
  `DeskReconcileStoreError`, `DeskReconcileRunMeta`, `DeskReconcileRun`,
  `DeskReconcileRunsListResult`, `DeskReconcileComputeProgress`, `DeskReconcileComputeSnapshot`).
  Purely additive — no existing interface's shape changed.
- `apps/frontend/lib/api.ts` — four new functions (`triggerDeskReconcileCompute`,
  `fetchDeskReconcileCompute`, `cancelDeskReconcileCompute`, `fetchDeskReconcileRuns`), each a
  direct mirror of its `DeskTopup*` sibling's `{ok, data?, error?}` shape and error-handling
  discipline (backend `detail` surfaced verbatim; "Backend unreachable" on a network exception).
- `apps/frontend/app/desk/page.tsx` — additive throughout: new components (`ReconcileIndexControl`,
  `driftEntryCount`, `DriftList`, `IndexReconciliationRunRow`, `IndexReconciliationTable`,
  `LatestReconciliationDetail`, `ReconciliationSection`), a new `ReconcileControlProps` interface,
  a `reconcile`/`reconcileControlProps` prop on `DeskNotComputedPanel`/`DeskPopulatedScreen`, six
  new state hooks, two GET calls added to the mount effect, one new poll effect, two new handlers,
  and the new bottom section. Every existing component/handler/effect is otherwise byte-unchanged.

## Design system compliance

Zero new design tokens — reused `Panel`, `EmptyState`, `LoadingPanel`, `UnavailablePanel`,
`HEADER_CELL`/`HEADER_CELL_LEFT`/`LABEL_CELL`/`NUMERIC_CELL`, `PRIMARY_BUTTON_CLASS`,
`CANCEL_BUTTON_CLASS` exactly as Top-up's own control/table already do. Dense, terminal-grade,
dark-only — matches the established house style. All interactive states present:
idle/hover/focus/active (inherited from the shared button classes), disabled (while triggering or
running), running (pulsing dot + live phase text + cancel), failed (error text + retry label),
cancelled (amber note). Copy is descriptive measurement only — `tests/test_copy_discipline.py`
green, unmodified (its lint walks `apps/frontend/app`/`components` source automatically, so the new
section is covered with zero lint-file changes).

## Live verification (this dispatch, via direct HTTP against the fresh scoped rig)

Booted a fresh scoped backend (`:8301`) + frontend (`:3301`) — path
`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-14.3302867/desk-iter14-scoped-qa` (see the dev
handoff's "Evidence sequencing" section for the exact seeding recipe) — and confirmed via direct
endpoint reads:

- `GET /desk` on the frontend returns HTTP 200 (page renders without a server error).
- `GET /research/desk/screen?date=2026-07-27` on the scoped backend: AAPL ranked Class A,
  `distance_bps≈1.50`, `1d` coverage `has_bars: false` (dark) beside `1h`/`4h`/`1w` `true` (lit) —
  the exact state the "Index Reconciliation" section's badge-linkage design depends on (the
  coverage badge component itself, shipped at J-02, took zero code change this iteration).
- `GET /research/desk/coverage/reconcile/runs` on the scoped backend: `{"runs": [], "latest":
  null}` — the honest empty state the new section's `EmptyState` branch renders as "No
  reconciliation run recorded yet."

This dispatch did not drive a real browser (Chrome MCP) against this rig — that is
browser-qa-agent's job downstream, and per this iteration's one-way-door constraint, the FIRST real
browser visit to `/desk` on this rig (before any reconciliation is ever triggered there) is the
official TC-17 evidence and must not be pre-empted by a developer-side dry run.

## Tests Run

`npx tsc --noEmit -p tsconfig.json` (from `apps/frontend/`), re-run fresh this dispatch — zero
errors, zero warnings. No dedicated frontend unit-test runner exists in this project
(`package.json` has only `dev`/`build`/`start` scripts); type-checking plus the backend's
`test_copy_discipline.py` (which lints the actual frontend source files, re-run fresh this
dispatch, green) are this project's established frontend verification surface.

## Known Issues

- No new frontend test file was added — this project has no frontend unit-test harness to add one
  to; coverage comes from `tsc --noEmit` and the copy-discipline lint.
- The official TC-17 (honest-empty + dark badge) and TC-18 (post-repair drift + lit badge)
  screenshots remain for browser-qa-agent, against THIS dispatch's fresh scoped rig (the earlier
  pass's own rig and its TC-17/TC-18 PNG files are stale — see the dev handoff's "Known Issues" for
  why the earlier pass's audit found those two specific files did not show the certified states).
- One non-blocking gap carried forward from the earlier audit pass, frontend-side: no visual
  feedback when a Cancel click arrives after the reconciliation's one cancel-observation window has
  already passed (finding F1) — the run simply completes and the "Cancelling…" state disappears
  with no note. Not fixed this dispatch (audit recommended backlogging it, not touched here).
