# goal-fast_wall-iter-4 Frontend Handoff

**Phase:** goal-fast_wall-iter-4
**Date:** 2026-07-17
**Agent:** developer
**Status:** complete

## What Was Built

`/structure`'s existing Edge Report section's `NotComputedPanel` gains the operator-facing
"Compute edge report" button, a live progress line, and a failed-state error render — the ONLY UI
surface change this iteration (no new page, no new panel, no nav entry).

- **`NotComputedPanel`** (was `{ detail }`-only) now also takes `compute` (the live/last
  `EdgeReportComputeSnapshot | null`), `onTriggerCompute`, `triggering`, and `triggerError`. Four
  states:
  - **idle** — button reads "Compute edge report", enabled.
  - **running** — button reads "Computing…", disabled; a progress line renders
    `backtests_done / backtests_total backtests` (+ a "(N from cache)" annotation when
    `backtests_from_cache > 0` — always 0 this iteration, since no per-pair sub-cache exists yet).
  - **failed** — the snapshot's `error` string renders verbatim in a small red line; button reads
    "Retry compute", re-enabled.
  - **done** — this component is no longer rendered at all — the parent re-fetches `GET
    /research/edge-report` the instant `state` is first observed as `"done"`, and the payload loses
    its `status: "not_computed"` discriminator, so the page falls through to the PRE-EXISTING
    `EdgeReportBody` render (zero new report-rendering code).
  - A separate `triggerError` (the POST itself failing — e.g. backend unreachable at click time) is
    rendered distinctly from a `failed` compute JOB, since one is a client-side request failure and
    the other is a server-side outcome of a job that DID start.
- **Visual treatment**: the panel shell is UNCHANGED (`UnavailablePanel`'s amber degraded-state
  container). The button reuses `structure-load-button`'s EXACT classes byte-for-byte (`rounded-md
  border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200
  transition-colors hover:border-slate-500 hover:bg-slate-700 focus:outline-none focus:ring-1
  focus:ring-emerald-500 active:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40
  disabled:hover:border-slate-600 disabled:hover:bg-slate-800`) for its enabled/disabled states —
  no new color, no new button style, matching the phase spec's "no new visual language" Design
  Direction. The progress/error lines reuse the panel's existing `text-amber-200/70` /
  new-but-consistent `text-red-300` (matching the existing `comparisonError`/`fetchError` red-line
  precedent elsewhere on this same page) — no invented palette entries.
- **Polling**: mirrors the EXISTING `needsPolling`/`setInterval(..., 700)` backtest-poll effect
  byte-for-byte in shape (same 700ms interval, same "stop scheduling once terminal" idiom via the
  effect's own dependency array) — a genuinely new `useEffect`, reusing the PATTERN, never the
  endpoint. An unreachable-backend poll tick is an honest no-op (keeps the last known snapshot,
  tries again next tick) rather than surfacing a poll-specific error banner — deliberately simpler
  than the Comparison section's `comparisonPollError`, since a stalled compute job is already
  visible via its own `state` staying `"running"` with a frozen progress line.
- **Mount-time resume**: the not-computed payload's own `compute` field seeds `computeSnapshot` on
  the SAME mount effect that already fetches the edge report — so a page load that lands mid-job
  (or after a job already terminated) shows the correct button/progress/failed state immediately,
  without requiring the operator to click anything first.

## Files Changed

- `apps/frontend/app/structure/page.tsx` — `NotComputedPanel` signature + body; new state
  (`computeSnapshot`, `computeTriggering`, `computeTriggerError`); mount-effect seed; new poll
  `useEffect`; `handleTriggerEdgeReportCompute`; the render call site now passes all four new props.
- `apps/frontend/lib/api.ts` — `triggerEdgeReportCompute(force?)`, `fetchEdgeReportCompute()`,
  `cancelEdgeReportCompute()`.
- `apps/frontend/lib/types.ts` — `EdgeReportComputeProgress`, `EdgeReportComputeSnapshot`; widened
  `EdgeReportNotComputed.compute` from `null`-only to `EdgeReportComputeSnapshot | null`.

## New user-facing capability

The operator can start the first-ever completed real edge-report compute directly from
`/structure` — no out-of-band script, no page-load side effect — watch it progress, and see the
finished report (or an honest failure) render in place.

## New information displayed

Live progress counts (`backtests_done` / `backtests_total` / `backtests_from_cache`), the compute
job's `state`, and — on failure — its `error` string, all inside the existing `NotComputedPanel`.
On `done`, the pre-existing `EdgeReportBody` render takes over (not new information — the same
report shape J-01 already typed, now actually reachable from the browser).

## New user actions

A "Compute edge report" button inside the not-computed panel. Continuous polling while a job is in
flight needs no further user action. No cancel button is wired this iteration (the backend route
and `cancelEdgeReportCompute()` exist and are tested, but the plan's UI Evolution section names
only the compute trigger).

## Tests Run

`cd apps/frontend && NEXT_DIST_DIR=<isolated dir> npm run build` — compiled successfully, zero
TypeScript errors (strict mode), all 7 routes built including `/structure`. This project has no
configured frontend test runner (`package.json` has no `test` script; confirmed via inspection) —
consistent with every prior iteration's own practice, correctness is proven by the strict
TypeScript build plus live verification against a real running backend (see the dev handoff's
"Live verification" section for the full curl-based trigger→running→done→failed cycle exercised
against the actual `/research/edge-report/compute*` routes this UI calls).

## Known Issues

- **No live browser screenshot exists for this iteration's button/poll UI** — Chrome MCP could not
  be started in this session despite extensive diagnosis (see the dev handoff's Known Issues for
  the full trail: a manually-launched Chrome instance works fine on this machine, but the MCP
  bridge's own auto-start consistently timed out). The button/poll/render logic was verified by (a)
  a strict TypeScript build with zero errors, (b) a server-rendered HTML fetch confirming the page's
  structure (including the `edge-report-loading` testid) renders without crashing, and (c) the
  dev handoff's curl-based live verification proving every HTTP response this UI code consumes
  (`POST /research/edge-report/compute`, `GET .../compute`, `GET /research/edge-report`) is shaped
  and sequenced exactly as the render logic expects — including a genuine `state: "failed"` snapshot
  with a verbatim error message. This is NOT the same as a verified visual render; flag for
  browser-qa-agent.
- `cancelEdgeReportCompute()` is implemented and exported from `lib/api.ts` but has no UI caller —
  intentional per the plan's scope (no cancel button specified), not an oversight.
- The `backtests_from_cache` progress field will always render as absent (no "(N from cache)"
  annotation) until J-05 ships the per-pair sub-cache — there is nothing to observe yet, not a bug.
