# goal-desk-iter-6 Frontend Handoff

**Phase:** goal-desk-iter-6
**Date:** 2026-07-26
**Agent:** developer
**Status:** complete

## What Was Built

- **`/desk` history is now interactive, not just a list.** Clicking any row in the "Screen
  History" panel swaps the entire page's display (provenance line, briefing table, skipped-
  members section) to that exact recorded date's own snapshot, fetched read-only via `GET
  /research/desk/screen?date=`. The clicked row highlights (`bg-slate-800/60`), and a small banner
  appears above the provenance panel: "Viewing the recorded screen for `<date>` — not the latest."
  with a "Latest" button that snaps back to the newest screen instantly (no network call, since
  the page already holds `latest` in memory).
- **Every desk briefing row now links to `/structure`.** Clicking anywhere on a ranked row or a
  skipped row navigates to `/structure?symbol=<SYMBOL>&asof=<the displayed screen's as_of>`. A
  skipped symbol drills in too -- `/structure` shows its own honest empty state for a symbol with
  no bars, which is expected and not an error.
- **`/structure` now honors those links.** Arriving at `/structure` with both `symbol` and `asof`
  query params pre-fills the Symbol and As-of fields and runs the load automatically -- the
  tradable-map bands are already drawn by the time the page is visible, no manual Load click
  needed. Arriving at `/structure` with no params (or only one of the two params) looks and behaves
  exactly as it did before this iteration -- empty fields, nothing loaded, same layout.
- **A new inline note for the rare failure case.** Clicking a history row for a date that turns out
  to have no matching recorded screen (or a momentarily unreachable backend) shows a small amber
  note under the "viewing" banner and leaves whatever was already on screen untouched -- never a
  blank page, never a crash.

## Files Changed

- `apps/frontend/app/desk/page.tsx` -- history click-through + "Latest" control + viewing
  indicator + drill-in links on every row.
- `apps/frontend/app/structure/page.tsx` -- query-param prefill + auto-load (additive only; no
  other visible change).
- `apps/frontend/lib/api.ts` -- one new fetch helper (`fetchDeskScreenByDate`), no other API
  surface change.

## UI Evolution Answered

- **New user-facing capability:** browse the desk's recorded history in place, and jump from any
  briefing row straight into the deep-dive `/structure` view for that exact symbol and date.
- **New information displayed:** none -- every value shown was already being served; this
  iteration only adds two new ways to reach already-registered data.
- **New user actions:** click a history-list row; click "Latest"; click a ranked or skipped
  briefing row.
- **UI surface changes:** `/desk`'s history list is now interactive (no new page, no new route);
  `/structure`'s existing Load form now accepts prefill via URL query params.
- **Navigation changes:** none -- the top nav is unchanged (Cockpit / Structure / Desk).
- **Visual style:** no new colors, no new chrome -- reuses the existing dark/dense/terminal-grade
  panel, button, and table styling already established on both pages (e.g. `/structure`'s own
  `SECONDARY_BUTTON_CLASS` string, copied verbatim onto `/desk`'s new "Latest" button per this
  project's per-page-owns-its-own-copy convention).

## Tests Run

- `cd apps/frontend && npx next build` -- compiled and type-checked cleanly, no errors/warnings;
  `/desk` and `/structure` both built as static routes.
- `cd apps/backend && .venv/bin/python -m pytest tests/ -q` -- 1341 collected / 0 failed / 8
  skipped (see the dev handoff for the exact junit-derived tally); includes the two new
  source-introspection guard tests proving the desk page never references a structure compute
  endpoint and the new `/structure` prefill code calls only the existing load function.
- Manual smoke check via `curl` against a locally started `bash scripts/dev.sh` instance
  (`:8301`/`:3301`): `/`, `/desk`, `/structure` (with and without query params) all returned HTTP
  200; the pre-hydration HTML shell for both edited pages contains their expected `data-testid`
  markers with no server error.

## Known Issues / Not Done By This Handoff

- This handoff did not drive an actual browser click-through (Chrome MCP) to screenshot TC-1
  through TC-4 from the phase spec -- that is the browser-qa-agent's job next in the pipeline. The
  code path for each acceptance criterion was verified by direct code reading against the plan's
  exact test scenarios (TC-1 through TC-10), plus the automated checks listed above.
- No visual regression check (e.g. pixel diff) was run against the pre-iteration `/structure`
  no-params baseline; TC-4's "pixel-for-pixel" requirement should be confirmed by the browser-qa
  pass with an actual screenshot comparison.
