# goal-desk-iter-6 Execution Plan

Era B "The Desk" (`docs/goal.md`), iteration 6 — J-05 "Ledger history + drill-in to `/structure`".
J-01–J-04 are already shipped and passing; this iteration is frontend-wiring + one guard test +
one journey-script fix, reusing an already-registered backend contract. No new backend route, no
new Config field, no fingerprint move.

## What to Build

- **`/desk` history click-through.** `DeskHistoryTable`'s rows become clickable. Clicking a row
  fetches `GET /research/desk/screen?date=<screen_date>` (already shipped at
  `apps/backend/app/research/desk_routes.py:248-266`, `?date=` branch — confirmed unused by any
  frontend caller today per `api.ts:920`'s own comment "the `?date=` variant is J-05 scope,
  deferred") and renders that snapshot's own `rows`/`skipped`/provenance **in place of** the
  currently-shown one. No POST, no recompute. Add an explicit "Latest" control that reverts to the
  top-level `latest` snapshot from the already-loaded `GET /research/desk/screen` result (no
  refetch needed — the page already holds it in `screenResult` state).
- **Drill-in links.** Every ranked row (`DeskRow`) AND every skipped row (`DeskSkipRow`) becomes a
  link to `/structure?symbol=<row.symbol>&asof=<currently-displayed snapshot's as_of>` — the
  snapshot-level `as_of` (shared by every row in one screen), not a per-row field. Per
  `assumptions.md` iter-6 entry, BOTH row kinds link (a skipped symbol drills in too; `/structure`
  will honestly show its own empty state for it — no fabrication risk). Use `next/link`'s `Link`
  component, the project's established internal-nav pattern (`components/NavBar.tsx`), not a raw
  `<a>` or router.push.
- **One new API helper.** `apps/frontend/lib/api.ts`: add `fetchDeskScreenByDate(date: string)` —
  byte-identical proxy of the `?date=` GET, mirroring `fetchDeskScreen`'s exact `{ok, data, error}`
  shape (`data: DeskScreenSnapshot | null`, honest `null` when no snapshot matches that date — no
  crash, no blank state, per the spec's error-case requirement).
- **`/structure` query-param prefill (the era's one sanctioned edit to this frozen file).** On
  mount, read `symbol`/`asof` from `useSearchParams()`. When BOTH are present and non-empty,
  prefill `symbolInput`/`asOfInput` (state at `structure/page.tsx:1368-1369`) and call the
  **existing** `handleLoad` (`:1633`) once — the same function `handleSubmit`/`handleLoad` already
  use for a manual Load click. When either or both params are absent, behavior is byte-unchanged
  (T-8, TC-4). App Router requires a `Suspense` boundary around any `useSearchParams()` call in a
  page that isn't already static-opted-out: rename the current `export default function
  StructurePage()` (`:1367`) to an inner component (e.g. `StructurePageContent`) and add a new
  thin `export default function StructurePage()` that renders
  `<Suspense fallback={...}><StructurePageContent /></Suspense>`. This is a wrapper-only change —
  zero edits to chart components, zero edits to the Load flow's internals.
- **Guard test (source-introspection, `test_copy_discipline.py:220`'s pattern — read the .tsx
  source as text, assert on substrings/regex, no browser/runtime).** New test file (or an addition
  to an existing desk test file) asserting:
  (a) `apps/frontend/app/desk/page.tsx` contains zero references to `/research/tradability`,
  `/research/levels`, `compute_tradability`, or `compute_levels` (TC-5 — every desk number still
  comes only from the already-fetched screen snapshot);
  (b) the new `/structure` prefill code path calls `handleLoad` (or `handleSubmit`), not a second
  fetch/compute function (TC-6).
- **Fix the mutating replay step.** `runs/goal-session-desk/journey-scripts/J-04.json` step 5
  currently clicks `desk-run-screen-button` (a WRITE) followed by a `wait_for`. Replace both with
  read-only `expect` assertions of the same states the click was meant to reach, so replaying this
  golden against any backend — including a non-disposable one — never records a screen (TC-7).
- **No new backend route, no new backend test required by default.** `GET
  /research/desk/screen?date=` already has HTTP-level coverage: `test_desk_screen_compute.py:518`
  (`?date=` with nothing recorded → honest null) and `:627` (`?date=` after a real compute →
  verbatim dated snapshot). Only add backend coverage if the new frontend consumption path
  surfaces a genuine gap (e.g. an edge case not already exercised) — do not duplicate.

## Agents Required

- **backend-data: yes** — new source-introspection guard test (TC-5/TC-6); fix `J-04.json` step 5
  (TC-7); confirm (do not assume) the `?date=` route needs no new backend test; re-run full suite
  to confirm the 1328-pass/8-skip floor and `08e471b10130e1e2` fingerprint are unmoved.
- **frontend-ux: yes** — `/desk` history click-through + Latest control; ranked+skip row drill-in
  links; `api.ts` helper; `/structure` Suspense-wrapped query-param prefill.

Frontend Present: yes

## Files to Create/Modify

- `apps/frontend/app/desk/page.tsx` — clickable history rows (fetch-and-swap display state, not a
  route change), Latest control, `Link`-wrapped ranked + skip rows.
- `apps/frontend/lib/api.ts` — add `fetchDeskScreenByDate`.
- `apps/frontend/app/structure/page.tsx` — `useSearchParams` read + prefill + one `handleLoad`
  call on mount; `Suspense` wrapper around the existing default-export component (rename +
  re-wrap only).
- `apps/backend/tests/test_desk_screen.py` or a new `apps/backend/tests/test_desk_ui_guards.py` —
  the new source-introspection guard test (TC-5/TC-6). Prefer co-locating with an existing desk
  test file unless that makes it noisy; either is fine as long as it runs in the default suite.
- `runs/goal-session-desk/journey-scripts/J-04.json` — step 5 fix (remove the write click).
- `docs/handoffs/goal-desk-iter-6-dev.md` — dev handoff (required by DoD).

No changes expected to: any backend route file, `desk_screen.py`/`desk_screen_compute.py`/
`desk_routes.py` (already serve everything this iteration needs verbatim), `app/config.py`,
`StructureChart.tsx`, `PriceChart.tsx`, `bars.py`, `meta.py`.

## UI Evolution

- **New user-facing capability:** an operator can click any past recorded screen in `/desk`'s
  history list and see that exact recorded screen's own rows re-rendered (not the latest one), and
  can click any briefing row (ranked or skipped) to jump straight into `/structure` with that
  symbol and as-of already loaded and the tradable-map bands already drawn.
- **New information displayed:** none — this iteration surfaces already-registered values (past
  screen snapshots via the already-shipped `?date=` endpoint; `/structure`'s existing endpoints)
  through two new interaction paths. No new backend value, module, or route.
- **New user actions:** click a history-list row; click a "Latest" control to return to the newest
  screen; click a ranked or skipped briefing row to drill into `/structure`.
- **UI surface changes:** `/desk`'s screen-history list becomes interactive (a read-only display
  swap in place — no new page, no new route); `/structure`'s existing Load form gains query-param
  prefill + auto-Load, strictly additive, byte-unchanged when params are absent.
- **Navigation changes:** none — nav stays the same three rows (`Cockpit`, `Structure`, `Desk`),
  data-driven from `app/meta.py` (untouched this iteration).

## Visual Requirements

- **Component patterns:** reuse the existing `Panel`/`Metric` components already used throughout
  `/desk`; reuse `next/link`'s `Link` for drill-in navigation (the `NavBar.tsx` precedent) rather
  than introducing a new nav primitive; reuse the existing button classes
  (`PRIMARY_BUTTON_CLASS`/`SECONDARY_BUTTON_CLASS`-equivalent) for the "Latest" control.
- **Layout:** no layout change — the history table and briefing/skipped sections keep their
  current stacked-panel layout on `/desk`; `/structure`'s form layout is unchanged, only its
  initial field values and load timing change when query params are present.
- **Key visual effects:** none new — this is a wiring iteration; keep the house dark/dense/
  terminal-grade style already in place (no new colors, no new chrome).
- **States to handle:** (1) clicking a history row for a date with no matching screen (the
  `?date=` GET returns `{"screen": null}`) must leave the UI on its current snapshot — no crash,
  no blank state; (2) `/structure?symbol=&asof=` with only one of the two params present must
  behave as if neither were present (no partial auto-Load); (3) the currently-displayed-snapshot
  vs latest-snapshot distinction must be visually clear enough that TC-1/TC-2's before/after states
  are unambiguous in a screenshot (e.g. a small "viewing: 2026-06-22 (not latest)" indicator next
  to the Latest control is a reasonable, minimal way to satisfy this — implementer's discretion,
  no new backend value required to render it since `screen_date` is already in the fetched
  snapshot).

## Key Test Scenarios

- TC-1: click the 2026-06-22 history row → page renders exactly that snapshot's AAPL row
  (`band_class A`, `distance_bps 0.33523150389608725`, `price_low 298.02`, `price_high 300.1001`)
  and matching `skipped` count, equal field-for-field to `GET /research/desk/screen?date=2026-06-22`,
  zero new POST issued.
- TC-2: from TC-1's state, click "Latest" → page reverts to the top-level `latest` snapshot,
  unchanged from its pre-TC-1 rendering.
- TC-3: with the 2026-06-22 screen displayed and an AAPL row present, click that row → browser
  navigates to `/structure?symbol=AAPL&asof=2026-06-22T23:59:59Z`; Symbol/As-of fields show exactly
  those values; a load has already run; the AAPL tradable-map band covering 298.02–300.1001 renders
  (screenshot).
- TC-4: `/structure` opened directly with no query params → Symbol/As-of empty, no load triggered,
  pixel-identical to the pre-iteration baseline (screenshot).
- TC-5: guard test scans `apps/frontend/app/desk/page.tsx` source → zero hits for
  `/research/tradability`, `/research/levels`, `compute_tradability`, `compute_levels`.
- TC-6: guard test scans the new `/structure` prefill code → it calls the same load function the
  manual Load button calls, no second fetch/compute function introduced.
- TC-7: `J-04.json` step 5 after the fix is no longer a click on any `run-screen`/`topup` testid;
  replaying it against a freshly-seeded backend leaves that backend's screen-store file count
  unchanged before and after.
- TC-8: full backend suite reports 0 failures at or above the 1328-pass/8-skip floor;
  `Config().config_fingerprint()` still prints `08e471b10130e1e2`.
- TC-9: J-01–J-04 and J-07 re-verify clean (deterministic replay or LLM fallback) — no regression
  from this iteration's `/desk` and `/structure` edits.
- TC-10: a browser-QA pass seeded with a throw-away copy of the real `screen-2026-06-22` snapshot
  plus its real AAPL bars leaves the operator's real `apps/backend/.data/` byte-for-byte unchanged
  before vs. after (iter-4/iter-5 persistence discipline — QA must use a fixture-scoped backend,
  never the ambient store).

## Out of Scope (per phase spec — do not build)

- J-06 (MCP contract v3, 17 tools) — scheduled next iteration.
- Any edit to `StructureChart.tsx`, `PriceChart.tsx`, or `bars.py`.
- A date-picker or alternate-date control on `/desk`'s Run Screen button.
- The three carried one-line hardening items (CLI screen-write-path guard, per-series
  price-less-row filter, chart-guard-test re-tightening) — their files are not opened this
  iteration.
- Obtaining the owner's written ratification of the two still-open iter-4 frozen-file exceptions
  (`bars.py`, `StructureChart.tsx`) — a human action, carried as an active blocker note only.
- Any change to the screen/universe/coverage compute managers or their persisted shapes.

No drift from `docs/goal.md` detected: J-05 is explicitly named in the goal's Must-have journeys
(Key Capability 5, Data Contract row "Screen snapshots, rank rows, skip rows"), and this plan's
scope matches the phase spec's IN SCOPE section exactly, with no additions.
