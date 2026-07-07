# goal-structure_ui-iter-1 Execution Plan

Builds J-01 only (goal.md / blueprint.md dependency order: J-01 -> J-02 -> J-03; J-04 guards
continuously). Confirmed no drift from `docs/goal.md` — the phase spec is a faithful, tightly
scoped subset of the goal's J-01 journey; J-02/J-03 are explicitly deferred to later iterations.

## What to Build

- **Backend (additive only):** add `{"path": "/structure", "label": "Structure", "nav": True}` to
  the `UI_ROUTES` tuple in `apps/backend/app/meta.py`, inserted after the `/performance` entry
  (tuple order is nav order). This is the ONLY backend edit this iteration.
- Update `apps/backend/tests/test_meta_routes.py`'s exact-match assertions to reflect the new
  6-entry map (see Files section — 3 assertions currently hardcode the 5-entry list/count).
  Re-verify live that `config_fingerprint` stays `4d665603569b9dbf` (`UI_ROUTES` is already excluded
  from the fingerprint, so this should be a no-op — confirm rather than assume).
- **Frontend:** new `apps/frontend/app/structure/page.tsx` — client component, dark-only Tailwind,
  following `/performance/page.tsx`'s pattern: no business logic, verbatim rendering,
  `{ok, data, error}`-shaped fetch results.
- Symbol + as-of controls: reuse `SymbolSearch` for the symbol; a plain ISO-8601 datetime input for
  `as_of`. On change, fetch `GET /research/levels?symbol=&as_of=`.
- Price chart: a NEW purpose-built chart following `PriceChart.tsx`'s **pattern** (client-only
  dynamic `lightweight-charts` import; dark chart options — slate-950 bg / slate-800 grid /
  slate-400 text; dashed `createPriceLine` calls). Do **not** try to reuse `PriceChart.tsx`
  directly — it is wired to tape-state/thesis polling (`/tape/{ticker}/history`), not
  `/research/bars` + `/research/levels`. Candles come from `GET /research/bars` (a list endpoint
  with no symbol query param — filter client-side by the already-served `symbol` field, the same
  discipline `NavBar` already uses filtering `nav: true`; this is filtering, not recomputation).
  One dashed price line per level, labelled by `timeframe`.
- Confluence-zones table: one row per `confluence_zones[]` entry; class badge from `zone.class`
  verbatim; member levels (price + timeframe); `score` verbatim.
- Four honest, visually distinct states (never share copy): `no_bar_series_for_symbol: true` ->
  explicit "no bar series recorded — recording historical bars needs provider credentials";
  series-but-empty `levels` -> distinct "no levels found"; levels-but-empty `confluence_zones` ->
  distinct "no qualifying confluence zone"; backend unreachable / non-200 -> the existing
  `NavBar`/`UnavailablePanel`-style degraded treatment.
- New `lib/api.ts` fetch helpers + `lib/types.ts` types for `/research/levels` and `/research/bars`
  — confirmed neither exists yet (grepped both files).

## Agents Required

- developer: yes — this project has ONE `developer` agent covering both backend and frontend (no
  separate `backend-data`/`frontend-ux` agents exist in this framework's roster); both flags below
  route to it:
  - backend-data: yes — the additive `/structure` `UI_ROUTES` entry + the `test_meta_routes.py`
    assertion updates. No new computation, no new endpoint, zero touch to `config.py`,
    `research/levels.py`, `research/bars.py`, `research/backtests.py`, `research/strategies.py`, or
    the engine.
  - frontend-ux: yes — the new `/structure` page: symbol/as-of controls, price chart with level
    lines, A/B/C zones table, four honest states, new `api.ts`/`types.ts` plumbing.

## Frontend Present
yes

## Files to Create/Modify

- `apps/backend/app/meta.py` — add the additive `/structure` entry to `UI_ROUTES`, after `/performance`
- `apps/backend/tests/test_meta_routes.py` — update `test_ui_routes_lists_exactly_the_live_routes`
  (6-entry exact dict) and `test_ui_routes_top_bar_entries_match_the_rendered_nav_set` (5-entry
  top-bar list + `len(routes) == 6`); re-run `test_ui_routes_every_entry_carries_path_and_label`
  and `test_ui_routes_represents_journal_detail_honestly` (no code change expected, just re-verify)
- `apps/frontend/app/structure/page.tsx` — NEW: the Structure page (controls + chart + zones table
  + 4 honest states), following `apps/frontend/app/performance/page.tsx`
- `apps/frontend/lib/api.ts` — add e.g. `fetchLevels(symbol, asOf): Promise<{ok, data:
  LevelsResponse | null, error?, status?}>` and `fetchBarSeriesList(): Promise<{ok, data:
  BarSeriesListResult | null, error?}>`, mirroring `fetchPnlLedger`/`fetchProfiles`'s shape
- `apps/frontend/lib/types.ts` — add `SrLevel`, `ConfluenceZone`, `LevelsResponse`, `BarRow`,
  `BarSeriesRecord`, `BarSeriesListResult` (none exist today)
- Optionally `apps/frontend/components/StructureChart.tsx` (or similar) if the developer prefers
  factoring the chart out of `page.tsx` — not required; `/performance` keeps everything in one file

## UI Evolution

- New user-facing capability: open the Structure tab, pick a symbol + as-of time, see that symbol's
  S/R levels on a price chart plus its A/B/C confluence zones in a table — read-only, no more
  curl/MCP-only access to era-4's structure computation.
- New information displayed: per-symbol level lines (price + timeframe + type) over candles; a
  zones table (class, member levels, score) — all verbatim from `GET /research/levels`.
- New user actions: select a symbol (`SymbolSearch`), set an as-of time, click the new "Structure"
  top-bar link. Read-only — no mutation, no job, no submission.
- UI surface changes: one new page `/structure` with a Levels & Zones section (chart + table +
  states). Registry (J-02) and comparison (J-03) sections are later iterations' additions to this
  SAME page per the blueprint — not built now.
- Navigation changes: one new top-bar link "Structure", served by `GET /meta/ui-routes`
  (data-driven `NavBar`, zero client hardcoding).

## Visual Requirements

- Component patterns: reuse `SymbolSearch` verbatim; follow (not reuse) `PriceChart.tsx`'s
  dynamic-import + dark-theme chart-options pattern for the new chart; mirror
  `/performance/page.tsx`'s table cell constants (`NUMERIC_CELL`/`HEADER_CELL`/`LABEL_CELL`) and its
  `UnavailablePanel`/`LoadingPanel` treatments for the zones table and the four honest states.
- Layout: single-column page like `/performance` (`max-w-7xl` main content): header (title +
  simulated/read-only framing copy) -> symbol/as-of controls row -> chart panel -> zones table
  panel. No sidebar needed this iteration.
- Key visual effects: dark instrument-panel style consistent with `/journal`/`/studies`/
  `/performance` — slate surfaces, restrained borders, font-mono numerics; amber accent for the
  honest-empty/degraded states (the established `UnavailablePanel` treatment); level price-lines
  dashed (declared-reference-line convention, not solid price data), matching `PriceChart.tsx`'s
  existing thesis-geometry dashed-line precedent.
- States to handle: loading (pulse skeleton, mirror `LoadingPanel`); the 3 distinct empty states +
  the 1 degraded/unreachable state (4 total, distinct copy + distinct `data-testid` each); the
  populated state (chart + table together).

## Key Test Scenarios

- Backend: `GET /meta/ui-routes` returns 6 entries in order; the 5 pre-existing entries stay
  byte-identical; `/structure` present with `nav: true`; `config_fingerprint` still
  `4d665603569b9dbf`; full backend suite green (baseline **1145 passed / 1146 collected**, per the
  iter-0 dev handoff).
- Browser, nav: the Structure link is reachable from every existing page and is proven data-driven
  (comes from the fetched route list — not a hardcoded `<Link href="/structure">` in source).
- Browser, populated state: seed the **committed PG bar-series fixture**
  (`apps/backend/tests/fixtures/bars/*.json` — the exact pair `test_levels.py` and the era-4
  `tape_to_profit_support_resistence` session's iter-2/iter-3 dev handoffs already use) into the
  live backend for the QA window only — either start the backend with
  `TAPEOLOGY_BAR_DIR=apps/backend/tests/fixtures/bars`, or copy-then-remove into `.data/bars/`
  exactly as those dev handoffs did (seed -> verify -> remove; never leave test data behind). Load
  symbol `PG` at `as_of=2026-06-09T21:00:00Z` (proven by
  `test_committed_fixture_confluence_zones_exact_values_keyless` to yield 20 levels / 6 zones — 5xC,
  1xB; class A is not reachable on this 2-timeframe fixture, which is fine — the DoD only requires a
  populated table, not all three grades). Screenshot the chart + zones table; byte-compare every
  rendered price/timeframe/type/class/score against the live
  `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z` JSON.
- Browser, `no_bar_series_for_symbol`: any symbol with nothing seeded (or PG before seeding).
  Screenshot the distinct credentials-needed copy.
- Browser, series-but-no-levels: query the seeded PG series at an `as_of` before its window opens
  (e.g. `2026-05-01T00:00:00Z`, before both the 1h window `2026-06-09T13:00Z` and the 1d window
  starting `2026-06-01`) -> `no_bar_series_for_symbol: false`, `levels: []`. Screenshot the distinct
  "no levels found" copy.
- Browser, levels-but-no-zones: the real PG fixture clusters into >=1 zone once enough of its
  window is visible, so either (a) probe intermediate `as_of` values on the live endpoint until one
  yields `levels` non-empty with `confluence_zones: []`, or (b) seed a small dedicated scratch
  series with widely separated pivots, mirroring
  `test_no_qualifying_cluster_on_bar_derived_levels_is_an_honest_empty_zones_list`'s fixture via
  direct `BarStore.record()` calls (never the credentialed HTTP endpoint). Screenshot the distinct
  "no qualifying confluence zone" copy.
- Browser, degraded: backend stopped or a forced non-200 -> explicit degraded state, never a
  blank/broken page.
- Regression (J-04): sim cockpit flows (`SIM-BUYER`/`SIM-SELLER`) + `/journal`, `/studies`,
  `/performance` still work; full suite + both equivalence suites (`test_observer_equivalence.py`,
  `test_profile_equivalence.py`) green; `config_fingerprint` unchanged; champion pointer unchanged
  (`v1`/`default`).
- Coherence: `git diff --stat -- apps/backend` shows ONLY `meta.py` + `test_meta_routes.py`; zero
  edits to `config.py`, `research/levels.py`, `research/bars.py`, `research/backtests.py`,
  `research/strategies.py`, the engine. Every rendered number traces to `GET /research/levels` or
  `GET /research/bars` verbatim — no client-side grading/aggregation.
- **Evidence discipline (carried forward from `lessons.md` iter-0):** every browser scenario above
  MUST produce a screenshot in `reports/qa/goal-structure_ui-iter-1-evidence/` — a "renders
  correctly" claim on prose alone is `unknown`, not `passing`.

## Assumptions (documented per token/questioning policy — no blocking ambiguity found)

- Chart timeframe selection: when a symbol has more than one registered bar series (multiple
  timeframes — the committed PG fixture has exactly 1h + 1d), the chart renders ONE representative
  series (suggest: the shortest available timeframe for that symbol), since a single candle chart
  cannot honestly overlay multiple timeframes' OHLC at once. This is a display choice over
  already-served data, not a new computation — document the exact rule chosen in the dev handoff.
- The `as_of` input produces an ISO-8601 UTC string (e.g. `2026-06-09T21:00:00Z`); a malformed value
  must never crash the page, but need not get its own unique copy distinct from the general
  degraded state — folding a 422 into the same "couldn't load" treatment satisfies the DoD's "never
  a crash or fabricated chart" bar. Add a more specific message only if trivial.
- No new `apps/frontend/components/` file is mandated; the developer may keep the page
  self-contained (the `/performance` precedent) or factor out the chart if `page.tsx` grows
  unwieldy.

## Out of Scope (confirmed — no drift from docs/goal.md)

- J-02 (strategy registry + champion cards) and J-03 (`structure_tape`-vs-`v1` comparison) — later
  sections of this same page, not this iteration.
- Any change to `config.py`, `research/levels.py`, `research/bars.py`, `research/backtests.py`,
  `research/strategies.py`, the engine, or any other existing surface's behavior.
- Any client-side recomputation of levels/classes/scores; any champion mutation; any PnL rendering
  (none exists in J-01); a `/datasets` library-inventory page (roadmap Card 5.9 — explicitly
  deferred).
- Blueprint: already approved (`runs/goal-session-structure_ui/state/blueprint.approved` exists)
  and already lists this exact IA/data-contract row set — no `blueprint.reapproval-requested`
  needed.
