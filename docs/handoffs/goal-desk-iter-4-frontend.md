# goal-desk-iter-4 Frontend Handoff

**Phase:** goal-desk-iter-4
**Date:** 2026-07-25
**Agent:** developer
**Status:** complete

## What Was Built

The product's **third page**, `/desk` — the era's first frontend surface (`Frontend Present: no`
on J-01/J-02/J-03). No existing page or shared component was edited beyond the two lib files new
functions/types live in; `NavBar.tsx` needed no change (it already renders whatever
`GET /meta/ui-routes` serves, and the backend's `UI_ROUTES` gained the third row in the same
commit).

- **`apps/frontend/app/desk/page.tsx`** (new, ~640 lines) — a single-file page mirroring
  `structure/page.tsx`'s own established conventions (local `LoadingPanel`/`UnavailablePanel`/
  `EmptyState` helpers rather than shared exports — this project's own "each page owns its tiny
  helpers" convention; reuses `Panel`/`Metric` from `components/Panel.tsx`):
  - **Empty state** (`latest === null`): exact text "Desk screen not computed yet." + an enabled
    Run Screen button, inside an amber `NotComputedPanel`-style treatment. Also hosts the Top-up
    button (first-ever run needs bars before a screen is worth computing).
  - **Provenance panel**: universe snapshot id, screen date, `as_of`, `config_fingerprint`, and the
    bar-store freshness value labeled **"Window last requested"** (never "last bar" — audit
    B9/iter-2 B2) using the existing `Metric` component.
  - **Briefing table**: symbol / side / band-class chip (+ "nearest same-class band" caption,
    honest about what `_select_best_band` actually selects — see the dev handoff's assumptions
    note) / distance-bps / band score / per-timeframe coverage badges / tick-evidence badge. Every
    value is `String(...)`-rendered verbatim from the served row — nothing recomputed.
  - **Coverage badges**: rendered from `Object.entries(row.coverage)` — i.e. whatever timeframe
    keys the SERVED row actually carries, never a hardcoded `["1h","4h","1d","1w"]` list — colored
    green (has bars) or muted (does not), each with a `title` tooltip reading "window last
    requested: …".
  - **Skipped-members section**: grouped under "Skipped — no bars (N)" / "Skipped — no basis
    session (N)" headings, each rendered only when its group is non-empty; renders correctly even
    when `rows` is empty (never conflated with the "not computed" state — that's `latest === null`
    only).
  - **Screen-history panel**: read-only table (date, rows/skipped counts, provenance summary) from
    the meta-only `screens` list — no click/select interaction this iteration (J-05 scope).
  - **Run Screen / Top-up controls**: two independent, non-generic control components
    (`ScreenComputeControl`, `TopupComputeControl`) — each wires trigger/poll/cancel to its own
    compute manager, mirrors `/structure`'s `NotComputedPanel` UX pattern (pulsing-dot progress
    line, Cancel button, `disabled={triggering || isRunning}` single-flight guard). "Run Screen"
    always submits the CLIENT's own today (`todayUtcDate()`, a byte-for-byte local copy of
    `/structure`'s own helper — this codebase's convention is each page owns its tiny formatting
    helpers rather than sharing one).
  - Mount issues exactly three GETs (`fetchDeskScreen`, `fetchDeskScreenCompute`,
    `fetchDeskTopupCompute`) and zero POSTs; each compute's poll `useEffect` only runs while
    `state === "running"`, refetching the screen list once a screen-compute tick observes a
    terminal state.
- **`apps/frontend/lib/api.ts`** — 7 new functions (`fetchDeskScreen`, `triggerDeskScreenCompute`,
  `fetchDeskScreenCompute`, `cancelDeskScreenCompute`, `triggerDeskTopupCompute`,
  `fetchDeskTopupCompute`, `cancelDeskTopupCompute`), each a byte-for-byte shape mirror of the
  existing `fetchEdgeReport`/`triggerEdgeReportCompute`/`fetchEdgeReportCompute`/
  `cancelEdgeReportCompute` family (`{ok, data, error}`, 422/unreachable folding).
- **`apps/frontend/lib/types.ts`** — 10 new interfaces (`DeskScreenRow`, `DeskScreenSkip`,
  `DeskScreenSnapshot`, `DeskScreenMeta`, `DeskScreenListResult`, `DeskScreenComputeProgress`,
  `DeskScreenComputeSnapshot`, `DeskTopupOutcome`, `DeskTopupComputeProgress`,
  `DeskTopupComputeSnapshot`) matching the backend's registered Data Contract shapes field-for-field
  (`runs/goal-session-desk/state/blueprint.md`).

## Files Changed

- `apps/frontend/app/desk/page.tsx` — new file, the whole page.
- `apps/frontend/lib/api.ts` — `+171` lines (7 new functions), nothing else touched.
- `apps/frontend/lib/types.ts` — `+125` lines (10 new interfaces), nothing else touched.

No other frontend file was touched — `NavBar.tsx`, `components/Panel.tsx`,
`app/structure/page.tsx`, `components/PriceChart.tsx`, `components/StructureChart.tsx`, and
`app/page.tsx` (Cockpit) are all confirmed byte-unchanged via `git diff --stat` (empty output).

## Visual / UX confirmation

Confirmed live via Chrome MCP against the real running app (`scripts/dev.sh`, backend `:8301`,
frontend `:3301` after `rm -rf apps/frontend/.next` + rebuild), against the REAL ambient
`.data/` tree, which happens to already hold one real recorded screen from prior operator
activity (10 ranked rows, 91 skipped, over the real 101-member universe) — this let the check
cover the POPULATED state live, not just the empty one:

- **Nav**: `Cockpit · Structure · Desk`, Desk shown active (emerald highlight) on `/desk`,
  Structure active on `/structure` — both confirmed by screenshot, both routes verified to render
  exactly 3 nav links.
- **Provenance panel**: all 5 fields render with real values (`universe-2026-07-25-49b33fa31680`,
  `2026-06-22`, `2026-06-22T23:59:59Z`, `08e471b10130e1e2`, and a 16-hex bar-store-signature value
  labeled "Window last requested").
- **Briefing table**: all 10 real rows render (AAPL, AMZN, NVDA, AMD, JPM, TSLA, MSFT, META,
  GOOGL, NFLX), each with the class chip + "nearest same-class band" caption, monospace
  distance/score values, and — verified via a DOM query, not just a screenshot — every row carries
  EXACTLY 4 coverage badges with the row's own true/false `has_bars`. Two real, honest examples
  worth recording: AAPL shows all 4 badges `true` (full coverage); MSFT shows `1h:true, 4h:false,
  1d:true, 1w:false` — the EXACT partial-coverage example the iter-2 lesson (in `goal.md`'s NOTES)
  describes, confirming the "never assume uniform coverage" discipline holds against real data, not
  just the fixture. Several rows (AMZN, NVDA, JPM, TSLA, META, GOOGL, NFLX) show all 4 badges
  `false` despite being RANKED (not skipped) — an honest, expected divergence: `compute_tradability`
  reads `BarStore` directly while the coverage badge reads the separate `bar_index`, and the two are
  independent reads by design (T-4/T-7); this is not a bug in the page.
- **Skipped Members**: "Skipped — no bars (91)" heading + all 91 rows render; one row (`PG`) shows
  a "tick evidence" badge, confirming the tick-evidence read is genuinely independent of the
  coverage read (PG has no bars but IS one of the 11 recorded dataset symbols).
- **Screen History**: one row, `2026-06-22 | 10 | 91`, with the correct provenance summary string.
- **Run Screen / Top-up panel**: both buttons render, both confirmed enabled
  (`{"runScreen":{"text":"Run Screen","disabled":false},"topup":{"text":"Top-up","disabled":false}}`
  via a DOM query) — neither was clicked against the real ambient store (see Known Issues).
- **J-07 kept-surface spot-check**: on `/structure`, loaded `AAPL` as-of `2026-06-22T21:00:00Z` —
  the pinned wall renders (`resistance 300.11–302.2 Class A score 171`), confirming the exact text
  the newly-timeout-adjusted `journey-scripts/J-07.json` step 8 asserts (`"300.11"`) is genuinely
  present and the page is otherwise unchanged.
- Dark/dense/terminal-grade visual language matches `/structure` exactly — same `Panel` borders,
  uppercase section labels, monospace numeric cells, amber not-computed/degraded treatment, emerald
  active-nav/progress-dot accents. No new colors or effects introduced.

## Tests

No frontend test runner exists in this repo (`apps/frontend/package.json` has no `test` script) —
unchanged from every prior iteration. Frontend correctness was verified via:

1. `rm -rf apps/frontend/.next && npm run build` — exit 0, TypeScript strict-mode typecheck clean,
   production build succeeds, `/desk` registers as a static route.
2. The live browser walkthrough above (empty-state text/button structurally confirmed via code
   inspection + the live populated-state render since the ambient store already had a screen;
   Run Screen/Top-up button enabled-state and labels confirmed via DOM query).
3. `test_lint_frontend_source_literals_are_clean` (backend-owned, unmodified) — passes; it scans
   `apps/frontend/app/**/*.tsx` automatically, so `/desk`'s new copy is covered with zero new lint
   surface to add.

## Known Issues

- **Did not click "Run Screen" or "Top-up" against the real ambient store.** Both are confirmed
  wired correctly (enabled, correctly labeled, calling the correct endpoints per code review, and
  the backend's compute-manager mechanics are covered by passing unit/integration tests), but
  actually triggering either against real data is a genuine, slow, side-effecting operator act (a
  new permanent screen snapshot dated today, or up to 404 real Yahoo fetch attempts across ~101
  members) — appropriately left to a real operator or the browser-qa-agent's fixture-scoped pass,
  not a dev sanity check.
- **Did not capture the true EMPTY state screenshot** (`latest === null`) live, since the ambient
  store already has a recorded screen from prior sessions and creating a genuinely fresh empty
  environment locally would have meant standing up a whole separate scoped backend just for one
  screenshot. The empty-state branch was verified by code inspection instead (the exact literal
  string is asserted directly in the JSX, `screenResult.data.latest === null` is the sole gate) and
  is exactly what `TC-1` / the browser-qa-agent's fixture-scoped dispatch will capture next.
- The "nearest same-class band" caption renders for EVERY row with a non-null `band_class`
  (unconditionally, not just when the row happens to differ from its symbol's highest-scoring
  band) — this is a deliberate reading of the phase spec's "where applicable" phrasing (applicable
  = a class exists to be "the same" as), consistent with `_select_best_band`'s tuple always
  prioritizing distance over score by construction, not something that only sometimes applies.

---

## Fix Notes — audit fix pass (2026-07-26)

Four `/desk` findings and one KEPT-surface finding, all live-verified against backend `:8301` +
`next dev :3301` after `rm -rf apps/frontend/.next` and a full rebuild. `npx tsc --noEmit` clean;
`test_lint_frontend_source_literals_are_clean` still reports zero violations on the new copy.
Screenshots: `reports/qa/goal-desk-iter-4-evidence/FIX-desk-populated-relabeled.png` and
`FIX-J-07-structure-alive.png`.

### `app/desk/page.tsx`

- **F1 — provenance label (was a false claim).** `Window last requested  d7bc8f8127904d0a` became
  **`Bar-store signature`** plus a caption (`desk-provenance-signature-note`): the value is a
  checksum over every member's window-last-requested timestamp, a pin and never a time. The
  freshness wording stays on the per-timeframe coverage badge tooltip, which really does carry a
  window end. `blueprint.md` and the phase spec's own bullet are amended in the same commit.
  Rendered live: `Bar-store signature  d7bc8f8127904d0a` + the caption.
- **F2 — the self-contradictory row now explains itself.** `desk-coverage-divergence-note` renders
  above the briefing table only when at least one ranked row has every timeframe badge dark, and
  says why: rank comes from the bar store the screen read directly, coverage from the derived bar
  index — two independent reads, each rendered as served. Live text: "7 ranked row(s) below show
  every timeframe badge dark…", matching the audit's own 7-of-10 count.
- **F3 — scanable numbers.** Distance and score now display through the existing `lib/format.ts`
  `fmt` helper (two decimals — the project's one number-formatting convention) with the SERVED value
  in full on each cell's `title`. `0.33523150389608725 bps` → `0.34 bps`, nothing lost. Live: cell
  `0.00 bps` / `217.00`, titles `0` / `217`.
- **F4 — the terminal-state refetch keeps the last known briefing.** A single failed
  `GET /research/desk/screen` after a compute finishes no longer replaces a populated page with the
  amber unavailable panel (a functional `setScreenResult` update keeps the last GOOD state); when
  nothing good was ever loaded the honest failure is still adopted, so no permanent skeleton.
- **F5 — the reuse signal is now visible.** `desk-screen-compute-outcome` renders on a `done`
  terminal state: "Reused the snapshot already recorded for this key — `<id>`" vs "Recorded a new
  snapshot — `<id>`". Until now `reused`/`screen_id` were threaded, typed, and invisible.

Re-confirmed unchanged by this pass: nav renders `['Cockpit', 'Structure', 'Desk']`; mount issues
**zero** non-GET requests (TC-19); the honest skipped grouping still reads `SKIPPED — NO BARS (91)`.

### `components/StructureChart.tsx` (sanctioned kept-surface edit — audit B1 §5 item 2)

A finite-value guard (`isDrawableCandle`) filters non-finite rows out of both the recorded series and
the live series before `setData`. The viewport anchor, the as-of index and the "any candles at all"
hint all index the FILTERED array, so a dropped row can never shift the operator's scroll position
onto the wrong candle. A `structure-chart-undrawable-rows` note states the count when it is non-zero.
For all-finite data — every fixture, every test, and the live store now that the backend excludes
priceless rows — output is identical to before, and the count renders zero. This is defence in depth:
the chart previously threw `Assertion failed: Candlestick series item data value of open must be a
number, got=object, value=null` and unmounted the entire page (body collapsed to 127 characters) on
one bad row. Live after the fix: zero page errors, zero console errors, body 57,265 characters held
for 8 seconds, `300.11–302.2` on screen, caption visible, 7 canvases drawn.

The guard-test `test_window_changes_preserve_the_visible_range` asserted the literal string
`bars.findIndex((b) => b.ts === anchor.ts)`; it now matches `\w*[Bb]ars\.findIndex\(…\)` so it still
enforces its actual invariant (the anchor is re-located by TIMESTAMP, never by a row count) against
the renamed array. `apps/frontend/app/structure/page.tsx`, `app/page.tsx` and `PriceChart.tsx` are
byte-unchanged.
