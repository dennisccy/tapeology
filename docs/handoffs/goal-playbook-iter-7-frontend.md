# goal-playbook-iter-7 Frontend Handoff

**Phase:** goal-playbook-iter-7
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete

## What Was Built

A new `<section aria-label="Backscan">` on `/desk`, rendered directly below the shipped "Playbook
Signals" section, above `</main>`. No new route, no nav change (nav stays exactly `/`, `/structure`,
`/desk`).

- **Plan preview**: From/To `yyyy-MM-dd` text inputs (`desk-backscan-from-input`/`-to-input`,
  mirrors `DeepBackfillControl`'s inputs). Re-read on every change via a plain GET
  (`fetchDeskPlaybookBackscanPlan`) — issues no compute, writes nothing. Renders a totals line
  (`{total} dates planned · {missing} missing at the current signature`) plus a per-date badge list
  (`desk-backscan-plan-date-row`, one badge per planned day, styled by
  `recorded_at_current_signature` vs `missing_at_current_signature`) — every number rendered
  verbatim via `fmt(n, 0)`, no client arithmetic.
- **Run Backscan control**: `desk-backscan-button` triggers `POST .../backscan/compute`
  (`triggerDeskPlaybookBackscanCompute`). While running: a live progress line
  (`{completed} / {planned_total} dates · {reused} reused · {recorded} recorded · {refused_non_session}
  refused · {failed} failed`, via the shared `BackscanOutcomeCounts` component), the current date
  being walked, and a Cancel button (`desk-backscan-cancel` → `POST .../compute/cancel`). Honest
  `error`/`cancelled` states rendered exactly like `DeepBackfillControl`'s.
- **Runs table**: `BackscanRunsSection` → `BackscanRunsTable` (the `TopupRunsSection`/
  `TopupRunsTable` precedent) — one row per completed/cancelled/errored run: date range, status,
  all four per-outcome counts (`BackscanOutcomeCounts`, shared with the live-progress view so the
  two can never drift), and the started timestamp (`formatDateTimeET`). Honest empty state
  (`desk-backscan-runs-empty`, "No back-scan runs recorded yet.") before any run.
- All served numerics render through `fmt(n, 0)` or verbatim string interpolation — zero client-side
  arithmetic anywhere in the panel (`_PRICE_ARITHMETIC_FIELDS` extended in the backend's own
  `test_desk_ui_guards.py` to cover the new fields structurally, not just by convention).

## New effects / state (page census)

- 8 new `useState` hooks: `backscanFromDay`, `backscanToDay`, `backscanPlan`, `backscanCompute`,
  `backscanRunsResult`, `backscanTriggering`, `backscanTriggerError`, `backscanCancelRequested`,
  `backscanCancelError` (9, actually — matches the Playbook Signals section's own state census
  shape).
- 2 new `useEffect`s (page total 17 → 19): a plan-preview read keyed on `[backscanFromDay,
  backscanToDay]` (the `DeepBackfillControl` plan-effect precedent), and a compute poll keyed on
  `[backscanCompute]` that ALSO refreshes the durable runs ledger once on the terminal tick (the
  reconciliation poll's own shape) — this is why the runs table needed no third effect of its own.
- 1 new `setInterval` (page total 6 → 7) inside the poll effect; the page's single `setTimeout`
  (the refresh chain's own wait-tick) is untouched — the Backscan section is not part of the
  chain.
- Mount-time seeding for the compute snapshot AND the runs ledger both joined the EXISTING
  nine-GET mount effect (no new effect for either — the established `forwardComputeRef`-mirror /
  un-keyed-durable-log-read precedent).
- 2 new entries in `test_desk_refresh_chain_guard.py`'s `_TRIGGER_CALLS`
  (`handleTriggerBackscan(`, `triggerDeskPlaybookBackscanCompute(`) — no `useEffect` anywhere
  references either; the section is reachable ONLY from the Run Backscan button's `onClick`.

`apps/backend/tests/test_desk_refresh_chain_guard.py`'s `_EXPECTED_EFFECT_COUNT`/
`_EXPECTED_INTERVAL_COUNT` were re-derived deliberately with the mandatory rationale paragraph
(source comment, `desk_routes.py`-adjacent test file) rather than loosened — both green.

## Files Changed

- `apps/frontend/app/desk/page.tsx` -- new `BackscanOutcomeCounts`/`BackscanPlanPreview`/`BackscanControl`/`BackscanRunRow`/`BackscanRunsTable`/`BackscanRunsSection` components, new state/effects/handlers, new `<section aria-label="Backscan">` below Playbook Signals
- `apps/frontend/lib/api.ts` -- `fetchDeskPlaybookBackscanPlan`, `triggerDeskPlaybookBackscanCompute`, `fetchDeskPlaybookBackscanCompute`, `cancelDeskPlaybookBackscanCompute`, `fetchDeskPlaybookBackscanRuns`
- `apps/frontend/lib/types.ts` -- `DeskPlaybookBackscanPlan`, `DeskPlaybookBackscanPlanDate`, `DeskPlaybookBackscanOutcomeCounts`, `DeskPlaybookBackscanComputeSnapshot`, `DeskPlaybookBackscanRun`, `DeskPlaybookBackscanRunsListResult`

## Tests Run

- `npx tsc --noEmit -p tsconfig.json` -- zero errors.
- Backend guard suite covering this page's source structure:
  `.venv/bin/python -m pytest tests/test_desk_refresh_chain_guard.py tests/test_desk_ui_guards.py
  tests/test_copy_discipline.py -q` -- all green (27 + 37 + 30 tests respectively, no seeded-violation
  regressions).
- Live verification: `GET :3301/desk` (the pinned dev frontend, restarted this session) renders the
  literal text "Backscan" (the new section's Panel title and aria-label), confirming the panel
  mounts without a client error.

## Known Issues

- **No browser screenshot captured by this dev pass.** TC-11 (plan preview + a completed fixture
  scan's run row with all four per-outcome counts legible) and TC-14 (the owed Range Trade row
  re-capture on a freshly rebuilt page, same clean browser pass) are the browser-qa-agent's job next,
  using `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` as the ONLY backend entry
  point. Per T-9/T-10: `rm -rf apps/frontend/.next` + rebuild before that pass; no screenshot ⇒
  `unknown`, never `passing`.
- **The per-date plan badge list has no pagination/cap.** For the fixture-scoped rig's small ranges
  (2–4 days) this is fine; a genuinely wide real-corpus range would render one badge per calendar
  day with no visual cap. Not exercised or required by any TC this iteration (the real full-corpus
  scan is explicitly out of scope) — flagged here rather than silently left for a future iteration
  to discover.
- Capture technique for the browser pass (hiding sibling `<section>`s above Backscan via `eval` for
  the screenshot only) is the QA agent's own technique per the iteration NOTES — no DOM change was
  needed in the page itself to support it.
