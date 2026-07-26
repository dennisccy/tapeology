# goal-desk-iter-6 Dev Handoff

**Phase:** goal-desk-iter-6
**Date:** 2026-07-26
**Agent:** developer
**Status:** complete

## What Was Built

- **`/desk` screen-history click-through.** `DeskHistoryTable` rows are now clickable. Selecting a
  row fetches `GET /research/desk/screen?date=<screen_date>` (already-shipped J-03 endpoint,
  `apps/backend/app/research/desk_routes.py:248-266`) and swaps THAT snapshot's own
  `rows`/`skipped`/provenance into the page's display, in place — no POST, no recompute. This is
  the first UI caller of the `?date=` branch.
- **"Latest" control.** Reverts the display back to the top-level `latest` snapshot already held
  in `screenResult` state (no refetch). Shown together with a small "viewing: <date> — not the
  latest" indicator whenever a history row (not `latest`) is on screen.
- **Honest failure handling for history clicks.** A date with no matching recorded screen
  (`{"screen": null}`) or an unreachable backend both leave the currently-displayed snapshot
  unchanged — only a small inline note (`desk-history-fetch-error`) changes.
- **Drill-in links.** Every ranked row (`DeskRow`) and every skipped row (`DeskSkipRow`) is now a
  `next/link` `Link` to `/structure?symbol=<row.symbol>&asof=<displayed snapshot's as_of>`. Both
  row kinds link (per the goal's own iter-6 assumption: a skipped symbol still drills in and
  `/structure` honestly shows its own empty state for it). Implemented as a "stretched link"
  (`position: relative` on the `<tr>`, one `<Link className="absolute inset-0">` inside the first
  `<td>`) so the whole row is clickable via one real anchor, without wrapping `<tr>` in `<a>`
  (invalid HTML) and without `router.push`.
- **New API helper.** `apps/frontend/lib/api.ts`: `fetchDeskScreenByDate(date)` — a byte-identical
  proxy of the `?date=` GET, mirroring `fetchDeskScreen`'s `{ok, data, error}` shape (`data:
  DeskScreenSnapshot | null`).
- **`/structure` query-param prefill (the era's one sanctioned edit to this file).** On mount,
  reads `symbol`/`asof` via `useSearchParams()`. When BOTH are present and non-empty, seeds
  `symbolInput`/`asOfInput` and calls the EXISTING `handleLoad` once (the same function the manual
  Load button already uses) — delimited by `// J-05-PREFILL-START` / `// J-05-PREFILL-END` markers.
  Absent or partial params leave every default/control/rendered state byte-unchanged. The App
  Router's `useSearchParams()` requirement is met by renaming the page component to
  `StructurePageContent` and adding a new thin default export `StructurePage` that wraps it in
  `<Suspense fallback={null}>` — a wrapper-only change; zero edits inside the renamed component
  besides the new prefill block.
- **Guard tests (source-introspection).** New file `apps/backend/tests/test_desk_ui_guards.py`:
  (a) `apps/frontend/app/desk/page.tsx` contains zero references to `/research/tradability`,
  `/research/levels`, `compute_tradability`, `compute_levels`; (b) the `J-05-PREFILL-START/END`
  block in `structure/page.tsx` calls `handleLoad(` and none of a forbidden second-fetch/compute
  list. Both carry a seeded counter-test proving the detection logic can actually fail.
- **Fixed the mutating replay step.** `runs/goal-session-desk/journey-scripts/J-04.json` step 5
  (previously a click on `desk-run-screen-button`) and step 6 (a `wait_for`) are replaced with two
  read-only `expect` assertions (`desk-screen-rows-table` showing a `symbol` header,
  `desk-history-table` showing a `date` header) — the same rendered states the click was meant to
  reach, now expected to already hold because this golden is replayed against a backend seeded
  with a real screen. Replaying J-04.json no longer issues any POST or writes a new screen
  snapshot.

## Files Changed

- `apps/frontend/app/desk/page.tsx` -- clickable history rows + "Latest" control + viewing
  indicator; `Link`-wrapped ranked + skip row drill-in (stretched-link pattern); new
  `DeskPopulatedScreen` component extracted to hold the populated-view render (avoids an unsafe
  non-null assertion while keeping `latest === null` as the one empty-state discriminator).
- `apps/frontend/lib/api.ts` -- added `fetchDeskScreenByDate`; added `DeskScreenSnapshot` to the
  type-only import list.
- `apps/frontend/app/structure/page.tsx` -- `useSearchParams` read + prefill effect (delimited by
  marker comments) calling the existing `handleLoad`; renamed the component to
  `StructurePageContent`; added a new `Suspense`-wrapped default export `StructurePage`.
- `apps/backend/tests/test_desk_ui_guards.py` (new) -- the TC-5/TC-6 source-introspection guard
  tests plus their seeded counter-tests.
- `runs/goal-session-desk/journey-scripts/J-04.json` -- step 5/6 fix (removed the write click +
  wait, replaced with read-only expects).

No changes to `desk_screen.py`, `desk_screen_compute.py`, `desk_routes.py`, `app/config.py`,
`StructureChart.tsx`, `PriceChart.tsx`, `bars.py`, or `meta.py` -- none were needed; the `?date=`
route already served everything this iteration required.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: 1341 collected, 0 failed, 0 errors, 8 skipped (1333 passed) -- confirmed via
`--junitxml` (`tests="1341" errors="0" failures="0" skipped="8"`); this run's own environment
never prints pytest's final one-line tally to stdout even on success, so the junit report was used
to get the exact numbers. 1333 passed is exactly the prior 1328-pass floor plus this iteration's 5
new guard tests -- no regression, no unaccounted change.

`Config().config_fingerprint()` -> `08e471b10130e1e2` (unchanged, verified directly).

Frontend: `cd apps/frontend && npx next build` (isolated `NEXT_DIST_DIR`) -- "Compiled
successfully", type-check passed, `/desk` and `/structure` both built as static routes with no
errors or warnings. (The isolated build incidentally caused Next to rewrite `tsconfig.json`/
`next-env.d.ts` with its own dist-dir include path; both were reverted via `git checkout --` since
they were an artifact of the isolated build, not a real code change.)

Service startup (pre-handoff checklist): ran `bash scripts/dev.sh` twice in sequence (stop fully
between runs), confirmed backend (`:8301`) and frontend (`:3301`) both start cleanly with no
errors each time, and confirmed no port conflicts on the second start. `curl` against
`/health`, `/research/desk/screen`, `/`, `/desk`, `/structure` (with and without query params) all
returned 200 with expected JSON/HTML both times. All started processes were killed before
finishing (note: `scripts/dev.sh`'s own printed PIDs are the wrapper processes -- the actual
uvicorn reload worker and the `next-server` worker run as separate child PIDs; `dev.sh`'s own
startup routine already handles this correctly via `lsof`/`fuser`-based port ownership rather than
PID tracking, which is why the second `dev.sh` run rebinds cleanly even though ad hoc `pkill -f`
by process name can miss a renamed reload/worker process -- confirmed by hand for this handoff,
not a defect in the product).

## Known Issues

- No backend or product code changes were needed beyond the one new test file and the journey-
  script fix; this was a pure frontend-wiring + guard-test + fixture iteration as scoped.
- Full interactive browser verification (actually clicking a history row, actually clicking a
  drill-in link and confirming the AAPL band renders at :8301/:3301 with a Chrome session) was not
  performed by this developer pass -- that is the browser-qa-agent's job next in the pipeline. This
  handoff's own verification was: (1) full backend suite green with the fingerprint pin unchanged,
  (2) `next build` compiling and type-checking both edited pages with no errors, (3) `curl`-level
  smoke checks confirming both pages serve 200 and their pre-hydration HTML shell renders the
  expected `data-testid` markers, (4) code-level review of the diff for the exact click/Link/state
  wiring described in the plan.
- The three carried one-line hardening items (CLI screen-write-path guard, per-series
  price-less-row filter, chart-guard-test re-tightening) and the owner's written ratification of
  the two still-open iter-4 frozen-file exceptions (`bars.py`, `StructureChart.tsx`) remain exactly
  as before this iteration -- out of scope per the plan, untouched.
