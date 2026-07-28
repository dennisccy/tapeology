# goal-desk-iter-11 Frontend Handoff

**Phase:** goal-desk-iter-11
**Date:** 2026-07-28
**Agent:** developer
**Status:** complete

## What Was Built

A new read-only "Top-up Runs" panel on `/desk`, disclosing the durable, append-only history of
every desk bar top-up run — closing the gap where a run's outcome vanished the moment the next run
superseded its in-flight compute snapshot.

- **`TopupRunsTable`** — one row per recorded run, meta-only: date (derived from `started_utc`),
  run id, terminal state (`done`/`cancelled`/`failed`), attempted-of-total pair count
  (`pairs_attempted / pairs_total`), and the universe snapshot id it ran against. Honest empty state
  ("No top-up runs recorded yet.") via the shared `EmptyState` component when the list is empty.
- **`LatestTopupRunDetail`** — for the latest run only (the one record the backend serves with its
  full per-pair `outcomes`): a per-outcome breakdown (`N reused · N fetched · N failed`), every
  `failed` pair's recorded detail rendered verbatim and un-truncated (symbol + timeframe + the raw
  detail string), and the honest count of pairs the run never reached (`pairs_total -
  pairs_attempted`) — shown only when it is greater than zero, never a false "0 not reached" claim
  of completeness the run didn't make.
- **`TopupRunsSection`** — the panel's own Loading / Unavailable / Populated states, fed by its own
  independent fetch (`fetchDeskTopupRuns`), never gated on the screen's own load state.
- Wired into the page's mount effect as a 4th GET (screen list, screen-compute snapshot, top-up-
  compute snapshot, and now the top-up run log) — zero new POSTs on load. The existing top-up-
  compute poll effect was extended to re-fetch the run log exactly once when an in-flight top-up
  job reaches a terminal state, so a just-finished run's own record appears without a manual reload
  (mirrors the screen compute poll's identical "on terminal, refresh the list" pattern already on
  this page).
- No new interactive control — no click-through, no filter, no retry button. Pure read-only
  disclosure, per this iteration's explicit scope.

## Placement decision (see dev handoff + `assumptions.md` iter-11 for the full reasoning)

The plan's suggested placement ("immediately after Screen History, before Run Screen/Top-up
controls") lives inside `DeskPopulatedScreen`, which only renders once a screen has been computed —
so literally following it would hide the panel whenever no screen exists yet, even if top-up runs
do. Since a top-up run is independent of whether a screen was ever run, the panel is instead
rendered as its own top-level `<section aria-label="Top-up runs">`, placed after the screen-state
conditional (whichever of the not-computed / populated views is showing) and before `</main>` — so
it is visible in every reachable page state. The plan's own text marks its suggested position as
"not a hard requirement, log the final placement choice if changed" — this is that disclosure.

## Design system conformance

- Reuses `Panel` (section wrapper, title bar) and `EmptyState` (the same `∅` glyph + honest copy
  pattern every other empty state on this page uses) — zero new components at that level.
- Reuses the page's own `HEADER_CELL` / `HEADER_CELL_LEFT` / `LABEL_CELL` / `NUMERIC_CELL` class
  constants for every table cell — no new design tokens, no arbitrary Tailwind values.
- Same dark/dense/terminal-grade house style as the rest of `/desk`: a plain bordered table, no
  glow/gradient/animation (this is a dense data disclosure, not a hero element, per the plan's own
  "Key visual effects: none new" instruction).
- Failed-pair rows use the existing amber accent (`text-amber-200/70`) already used for
  cancelled/warning copy elsewhere on this page (e.g. `desk-topup-compute-cancelled`), for the
  "N pairs not reached" note — consistent, not a new color.
- Copy is descriptive measurement only (dates, ids, counts, state words, raw error text) — no
  advice/imperative/prediction language. `tests/test_copy_discipline.py`'s frontend-literal lint was
  re-run and passes unmodified against the new panel's copy.

## States handled

- **Loading**: `LoadingPanel` (the page's existing skeleton pattern) while the mount-time GET is
  in flight.
- **Unavailable**: `UnavailablePanel` (amber alert) on a non-200/unreachable backend, carrying the
  server's own `detail` message when present.
- **Empty**: `EmptyState` ("No top-up runs recorded yet.") when `runs: []` — a valid, honest
  `ok: true` outcome, never treated as a failure.
- **Populated**: the meta table plus, when `latest !== null`, the full latest-run detail block
  (including its own conditional "Failed pairs" sub-block, which itself is omitted entirely when a
  run had zero failures — never an empty "Failed pairs (0)" heading).

## Files Changed

- `apps/frontend/lib/types.ts` — `DeskTopupRunMeta`, `DeskTopupRun`, `DeskTopupRunsListResult`.
- `apps/frontend/lib/api.ts` — `fetchDeskTopupRuns()`.
- `apps/frontend/app/desk/page.tsx` — the four new components + mount-effect/poll-effect wiring +
  the new top-level section (see dev handoff for the precise diff regions).

## Tests Run

- `npx tsc --noEmit` — clean, zero type errors.
- `rm -rf apps/frontend/.next && npm run build` — compiled successfully; `/desk` prerendered with
  no build/lint errors.
- Live verification: `scripts/start-backend.sh` + `scripts/start-frontend.sh` on ports 8301/3301
  (the project's deterministic pair), restarted twice to confirm no port conflicts; `curl
  http://localhost:3301/desk` returned HTTP 200 with "Top-up Runs" and the
  `desk-topup-runs-*`/`desk-topup-run-*` testids present in the server-rendered HTML against the
  ambient (never-run) store's honest-empty state. Both processes were stopped again before
  finishing (nothing left running).
- Backend contract re-run: `tests/test_copy_discipline.py` (frontend-literal lint over this file)
  — green, unmodified.

No dedicated frontend unit-test framework exists in this project (no test script in
`apps/frontend/package.json`, no `.test.ts(x)` files anywhere in the tree) — UI correctness is
proven by the TypeScript build + backend-served-shape tests + the browser-QA lane that follows this
dispatch, consistent with every prior iteration on this page.

## Known Issues

- Historical run rows show no per-outcome breakdown (only the latest run's full detail does) —
  this is a backend data-shape constraint (the meta-only `runs` list never carries `outcomes`), not
  a frontend omission; see the dev handoff's interpretation call 3.
- No browser screenshot evidence is included in this handoff — that is the browser-qa-agent's own
  downstream step (TC-12/TC-13), not part of this developer dispatch. The live curl/HTML checks
  above prove the panel renders correctly server-side against the ambient store's real (empty)
  state; they are not a substitute for the required browser screenshots of both the empty and
  populated states.
