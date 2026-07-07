# goal-structure_ui-iter-1 Dev Handoff

**Phase:** goal-structure_ui-iter-1
**Date:** 2026-07-07
**Agent:** developer
**Status:** complete

## What Was Built

**J-01 — the `/structure` page**, reachable from the top-bar nav, rendering a symbol's S/R levels
on a price chart plus its A/B/C confluence zones in a table, read verbatim from the existing
canonical endpoints. Per the spec, this is a pure read/visualize surface — no new backend
computation, no second source of truth.

- **Backend (additive only):** one new entry `{"path": "/structure", "label": "Structure", "nav":
  true}` appended to the `UI_ROUTES` tuple in `apps/backend/app/meta.py`, after `/performance`. This
  is the ONLY backend edit this iteration — confirmed by `git diff --stat -- apps/backend` (below).
- **Frontend:** new `apps/frontend/app/structure/page.tsx` (client component, follows the
  `/performance` page pattern) with:
  - Symbol + as-of controls (`SymbolSearch` reused verbatim + a plain ISO-8601 text input) behind an
    explicit `Load` button/form-submit (a deliberate UX choice — see "Design decisions" below).
  - A price chart (new `apps/frontend/components/StructureChart.tsx`, following — not reusing —
    `PriceChart.tsx`'s dynamic-import + dark-chart-options pattern) rendering candles from ONE
    representative recorded bar series plus one dashed price line per S/R level, labelled by
    timeframe + type.
  - A confluence-zones table: one row per `confluence_zones[]` entry, the A/B/C badge from
    `zone.class` verbatim, member levels (price + timeframe + type), and `score` verbatim.
  - Four distinct honest states: `no_bar_series_for_symbol` (credentials-needed copy),
    series-but-no-levels, levels-but-no-zones (scoped to the zones panel only — the chart still
    renders), and a shared backend-unreachable/non-200 degraded state (folding a malformed-`as_of`
    422 into it, per the plan's documented assumption).
- New `apps/frontend/lib/api.ts` helpers: `fetchLevels(symbol, asOf)` and `fetchBarSeriesList()`,
  both `{ok, data, error}`-shaped, mirroring `fetchPnlLedger`/`fetchProfiles`.
- New `apps/frontend/lib/types.ts` types: `SrLevel`, `ConfluenceZone`, `LevelsResponse`, `BarRow`,
  `BarSeriesRecord`, `BarSeriesListResult` — none existed before this iteration.

## Design decisions (documented per the plan's "Assumptions" + token/questioning policy)

1. **Explicit Load button, not fetch-on-keystroke.** The symbol + as-of controls sit in a `<form>`
   submitted by an explicit `Load` button (disabled until both fields are non-empty). This avoids
   firing a request per keystroke while the user is still typing an ISO date-time, and gives the
   browser-qa-agent's flows a single, deterministic trigger point. Free-text entry into `SymbolSearch`
   and the as-of field both still work exactly as before; nothing here is a "job" or "mutation" — it
   is a plain paired `GET` fetch.
2. **Representative-series pick for the chart.** When a symbol has more than one registered bar
   series (multiple timeframes), the chart draws candles from ONE of them — the shortest available
   timeframe wins, via a local `TIMEFRAME_ORDER` constant in `page.tsx` that mirrors
   `apps/backend/app/config.py`'s `bar_timeframes` tuple order (`1m,5m,15m,1h,4h,8h,1d,1w,1mo`). A tie
   (same timeframe, multiple series) resolves to the most-recently-created series, mirroring
   `research/levels.py`'s OWN `_select_one_series_per_timeframe` tie-break, so the chart's chosen
   series is never in tension with which series the levels computation itself read. This is a display
   choice over already-served rows (like NavBar's `nav: true` filter) — it computes no new
   price/level/zone value.
3. **Chart candles are scoped to the query's `as_of` instant.** Found during my own manual
   verification (see below): `GET /research/bars` has no `as_of` parameter, so without a client-side
   filter the chart would show every recorded candle for the chosen representative series — including
   bars AFTER the `as_of` instant the levels were computed at. That never violates the no-lookahead
   rail (the backend's OWN `_bars_as_of` truncation for the LEVELS computation is unaffected either
   way — this is purely a chart display filter of already-served rows), but it reads as visually
   confusing next to lines that were computed only from earlier data. `page.tsx` now filters
   `representative.bars` to `ts * 1000 <= Date.parse(levels.as_of)` before handing them to
   `StructureChart`, with a safe fallback (show every recorded bar, never a blank chart) if the parse
   ever fails — which it should not, since reaching this code path means the backend's OWN
   `parse_utc_epoch` already accepted `levels.as_of`.
4. **A malformed `as_of` shares the same degraded-state copy** as a network/backend failure, per the
   plan's own documented assumption — never a fifth honest-state copy invented for a rare client input
   mistake.

## Files Changed

- `apps/backend/app/meta.py` -- added the additive `/structure` entry to `UI_ROUTES` (after
  `/performance`); the ONLY backend behavior edit.
- `apps/backend/tests/test_meta_routes.py` -- updated `test_ui_routes_lists_exactly_the_live_routes`
  (now asserts the 6-entry map) and `test_ui_routes_top_bar_entries_match_the_rendered_nav_set` (now
  asserts 5 top-bar entries + `len(routes) == 6`); added
  `test_ui_routes_includes_structure_now_its_page_ships` (mirrors the existing `.../performance`
  precedent test).
- `apps/frontend/app/structure/page.tsx` -- NEW: the Structure page (controls, chart panel, zones
  table panel, all states).
- `apps/frontend/components/StructureChart.tsx` -- NEW: the candle + level-lines chart component.
- `apps/frontend/lib/api.ts` -- added `fetchLevels` and `fetchBarSeriesList`.
- `apps/frontend/lib/types.ts` -- added `SrLevel`, `ConfluenceZone`, `LevelsResponse`, `BarRow`,
  `BarSeriesRecord`, `BarSeriesListResult`.

Confirmed scope discipline: `git diff --stat -- apps/backend` shows **exactly** `meta.py` (+1 line)
and `test_meta_routes.py` — zero edits to `config.py`, `research/levels.py`, `research/bars.py`,
`research/backtests.py`, `research/strategies.py`, or the engine.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

- **Before this iteration's changes (baseline confirmation): 1145 passed, 1 skipped** (1146
  collected), exit 0 — matches the iter-0 dev handoff's recorded opening baseline exactly.
- **After this iteration's changes: 1146 passed, 1 skipped** (1147 collected), 364.77s, exit 0 — the
  +1 is exactly the one new test added (`test_ui_routes_includes_structure_now_its_page_ships`); zero
  regressions, zero tests removed or weakened.
- `config_fingerprint` re-confirmed unchanged: `tests/test_profile_equivalence.py` and
  `tests/test_levels.py` both still assert `CONFIG.config_fingerprint() == "4d665603569b9dbf"` and
  both pass (the additive `UI_ROUTES` entry lives in `meta.py`, entirely outside the `Config`
  dataclass the fingerprint hashes, so this was a confirmed no-op, not an assumption).

Command: `cd apps/frontend && npm run build` (frontend type-check + compile, per README's documented
command — see "Stack configuration source" note below)

- **Compiled successfully, zero type errors**, both before and after the `as_of` candle-filter
  addition. `/structure` appears in the route manifest as a static page (4.31 kB, 110 kB First Load
  JS) alongside the five pre-existing routes.

## Pre-handoff verification (live smoke test, beyond the two commands above)

Ran `bash scripts/dev.sh` (backend :8301, frontend :3301 — this repo's deterministic port offset) and
drove the live app with the Chrome MCP browser tool:

1. **Nav reachability + data-driven source:** `GET http://localhost:8301/meta/ui-routes` returns the
   live 6-entry list including `{"path":"/structure","label":"Structure","nav":true}`; the rendered
   top bar shows a "Structure" link (`<a href="/structure">` present in the DOM — not a hardcoded
   client link) that navigates correctly.
2. **`no_bar_series_for_symbol` state:** with nothing recorded, loading `PG` @
   `2026-06-09T21:00:00Z` renders "No bar series recorded for PG." / "Recording historical bars needs
   provider credentials." (distinct `data-testid="structure-no-bar-series"`).
3. **Populated state (chart + zones table), byte-for-byte:** seeded the committed PG fixture pair
   (`apps/backend/tests/fixtures/bars/*.json`) into `apps/backend/.data/bars/` for the verification
   window only (seed → verify → remove, confirmed by re-querying `no_bar_series_for_symbol: true`
   afterward). Live `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z` returned **20 levels,
   6 confluence zones (5×C, 1×B)** — exactly the plan's predicted values. The rendered page showed
   the SAME 20 levels as chart price lines (labelled e.g. "1h swing-pivot 149.48", "1d
   prior-period-extreme 148.23") over 9 candles from the 1h series, and the SAME 6 zones in the table
   (zone 2's price/timeframe/type rows — 139.89/1d/prior-period-extreme, 139.89/1d/swing-pivot,
   140/1d/prior-period-extreme, score 12 — matched the live JSON exactly).
4. **Series-but-no-levels state:** same PG series, `as_of=2026-05-01T00:00:00Z` (before both windows
   open) → "No levels found for PG as of 2026-05-01T00:00:00Z." / "A bar series is recorded, but
   nothing is derivable at this as-of time." — distinct copy, distinct `data-testid`.
5. **Levels-but-no-zones state:** found by probing the live endpoint per the plan's suggested
   approach — `as_of=2026-06-02T12:00:00Z` (only PG's first 1d bar's period has closed) returns 3
   levels (138.86, 140.28, 141.82 — all far apart in price) and `confluence_zones: []`. The page
   correctly showed the chart with its 3 level lines and the zones panel's distinct "No qualifying
   confluence zone among these levels." copy.
6. **Degraded state (malformed `as_of`):** typing `not-a-date` and clicking Load surfaced the
   backend's own 422 detail verbatim — "as_of must be an ISO date-time" — inside the shared amber
   degraded panel ("Nothing cached and nothing fabricated is shown in its place."). No crash, no
   fabricated chart.
7. Cleaned up: removed the seeded fixture files from `.data/bars/` before finishing (re-confirmed
   `no_bar_series_for_symbol: true` for PG afterward — no test data left behind).

## Service startup verification

- `bash scripts/dev.sh` started both services cleanly on the repo's deterministic port offset
  (backend :8301, frontend :3301); `GET /health` → 200, `GET /structure` → 200.
- **Encountered and resolved a self-inflicted issue, not a code defect:** I ran `npm run build` (a
  one-off production build/type-check) in the SAME `apps/frontend/.next` directory a live `next dev`
  process was using. Both processes share the default `.next` build dir; running them concurrently
  corrupted the dev server's webpack-runtime/module manifest, surfacing as `Cannot find module
  './885.js'`, `__webpack_modules__[moduleId] is not a function`, and a blank `/structure` render with
  a Next.js dev-overlay "1 Issue" badge. **This is a known, already-anticipated risk** —
  `apps/frontend/next.config.js`'s own comment describes exactly this scenario and offers a
  `NEXT_DIST_DIR` env var to isolate a one-off build's output from the running dev server. I killed
  the dev processes (by PID; `pkill` pattern matches on the wrapped `npm exec next dev` command line
  did not match reliably — see Known Issues) and restarted `scripts/dev.sh` fresh; the SAME `.next`
  directory self-healed on the fresh `next dev` start (dev mode recompiles/regenerates what it needs)
  with no further errors — confirmed by re-running the full smoke test above end to end afterward.
  **Lesson for future iterations:** never run `npm run build` while a `next dev` process for the same
  repo is live; if both are genuinely needed concurrently, set `NEXT_DIST_DIR` for the one-off build.
- Stopped both servers again at the end (by PID, then re-verified via `ps aux` that no
  uvicorn/next-dev/next-server process for ports 8301/3301 remained) — confirmed no orphaned process
  and no port conflict. An unrelated project's dev servers on different ports (a different repo,
  `trendora`) were left untouched, confirmed by path/command-line inspection before and after.

## Stack-configuration source note

`.claude/project-template.md` is still the generic, unfilled template (as the iter-0 dev handoff
already noted and `README.md`'s own TODO comment confirms — "likely reset by a recent
incredible_auto_dev framework sync"). I used `README.md`'s verified "How to run"/"Run tests" section
(itself cross-checked against `apps/backend/pyproject.toml`, `apps/frontend/package.json`, and
`scripts/start-backend.sh`/`start-frontend.sh`) as the actual stack/test-command source, matching the
precedent set by the iter-0 baseline iteration of this same session. Not this iteration's scope to
re-fill `project-template.md`.

## Known Issues

- **`pkill -f` pattern matching was unreliable against the wrapped `next dev` process tree** (`npm
  exec next dev -p PORT` spawns `npm exec` → `sh -c` → `node .../next` → a separate `next-server`
  process; a pattern that matches the literal port number in one layer does not always match in
  another). I resolved this by listing PIDs via `ps aux` and killing them explicitly. A future
  cleanup step relying solely on `pkill -f "next dev"` should also verify via `ps aux`/`lsof` that the
  `next-server` grandchild is actually gone, not just the parent.
- The frontend has no unit-test runner (confirmed via `package.json` — only `dev`/`build`/`start`
  scripts exist); `npm run build`'s type-check + compile is the full extent of automated frontend
  verification available, per this project's established convention (`/performance`,
  `/studies`, etc. carry no `.test.tsx` files either).
- **Chart-canvas screenshot timing (a testing-process note, not a product defect):** the browser
  tool's auto-captured screenshot attached to a `click` action fires before `StructureChart`'s
  dynamic `lightweight-charts` import + async draw completes, so an immediate post-click screenshot
  can show a blank canvas even though the chart mounted correctly and drew moments later (confirmed
  via a direct canvas pixel-content check, then a delayed screenshot showing full candles + price
  lines). The browser-qa-agent's evidence-capture step should allow a brief settle/await before
  screenshotting the chart panel specifically (e.g. an explicit wait or an `await_element` on the
  canvas's rendered content) rather than relying on the click action's own auto-capture.
- I did not exercise the "backend unreachable" variant of the degraded state live (stopping the
  backend mid-session) beyond code inspection — `fetchLevels`'s `catch` branch is the same
  well-established pattern already used by every other fetch helper in `lib/api.ts` (e.g.
  `fetchPnlLedger`, `fetchProfiles`), so this is a low-risk gap, but it is honestly noted here rather
  than silently assumed. The browser-qa-agent's dedicated pass should cover it directly per the spec's
  Testing Requirements.
- J-02 (strategy registry) and J-03 (backtest comparison) are explicitly out of scope for this
  iteration and are not built — they are later sections of this same `/structure` page per the
  blueprint.

## Suggested Next Steps

Per `docs/goal.md`'s dependency order (J-01 → J-02 → J-03; J-04 guards continuously), the next
iteration should build **J-02** (the strategy registry + champion cards) as a new section appended to
this same `/structure` page, reading `GET /research/strategies` and `GET /research/profiles` verbatim
— no backend edit expected (both endpoints already exist and are unchanged this iteration).
