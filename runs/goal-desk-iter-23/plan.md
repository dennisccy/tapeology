# goal-desk-iter-23 Execution Plan

Target journey: **J-15** (wall-composition disclosure on ranked `/desk` rows). Required-still-passing
regression set: **J-01..J-14**. Full-depth iteration (real full-stack change: backend row-builder +
frontend column + three Data-Contract additions, per the spec's escape-condition-4 trigger).

## What to Build

- Backend: in `compute_screen`'s ranked-row builder (`apps/backend/app/research/desk_screen.py`,
  the block that appends a row at ~line 445-475), copy three fields VERBATIM off the SAME `best`
  band dict `_select_best_band` already returns (that dict already carries `member_count` (int),
  `round_number` (bool), and `members` (list, each with its own `"timeframe"` key) —
  `tradability.py:352-364`):
  - `band_member_count` = `best["member_count"]`
  - `band_round_number` = `best["round_number"]`
  - `band_member_timeframes` = a plain per-timeframe tally over `best["members"]` (dict[str, int]);
    keys = only the timeframes actually present among that band's own members (never a fabricated
    zero for an absent timeframe — this differs from the `_bands_by_class` precedent, which always
    emits all four keys including zero; only the "build it as a plain dict tally, mirror that
    function's construction style" part of the precedent applies, not its always-present-keys
    behavior); values sum to `band_member_count`. Deterministic order is left to build discretion —
    the simplest zero-extra-compute approach is a first-seen tally walking `best["members"]` in its
    own already-sorted order (`tradability.py:364`'s `sorted(..., key=itemgetter("price",
    "timeframe", "type"))`), since Python dict insertion order is stable; whatever order is chosen
    must stay stable across runs and match the golden test's own assertions.
  - Zero second `compute_tradability` call, zero second `BarStore` read, zero touch to
    `_select_best_band`, `_select_opposite_band`, or `_row_rank_key`. Skip rows get none of the
    three fields (unchanged code path — they never reach the `best =` line).
- Frontend: add one `levels` column to the `/desk` ranked table (`apps/frontend/app/desk/page.tsx`'s
  `DeskRow`/`DeskRowsTable`, beside `band`/`opposite`), rendering `band_member_count` +
  `band_member_timeframes` as a tally string (e.g. `155 levels · 1d 68 · 1h 57 · 4h 19 · 1w 11`)
  plus a "round number" badge when `band_round_number` is true — reuse `/structure`'s own band-table
  badge style/markup verbatim (`apps/frontend/app/structure/page.tsx:612-621`, the
  `data-testid="tradable-band-round-number"` span and its exact className), not a newly invented
  style. Legacy rows (fields entirely absent — `undefined`, not just falsy) render the established
  honest-absence copy `"composition not recorded in this snapshot"`, matching the `== null` /
  `=== undefined` check pattern already used for `basis`/`history`/`band`/`opposite` cells
  (`page.tsx:382/392/407/420`). No new `title` tooltip — all three values are exact/unrounded, so
  `deskRowDrillInTitle` is NOT touched.
- Type contract: add `band_member_count?: number`, `band_round_number?: boolean`,
  `band_member_timeframes?: Record<string, number>` to `DeskScreenRow`
  (`apps/frontend/lib/types.ts:826`), following the SAME optional-key (`?:`), legacy-absent
  documentation-comment convention already used for `reference_close`/`opposite_band`/
  `bands_by_class` on that interface.
- Tests (fixture-scoped, mirroring the established `ctx`-fixture golden-test style already in
  `apps/backend/tests/test_desk_screen.py` for J-08/J-11/J-13/J-14 — e.g.
  `test_opposite_band_golden_near_far_and_null_class_rows`,
  `test_row_order_is_unchanged_by_the_opposite_band_addition`,
  `test_opposite_band_and_bands_by_class_add_zero_extra_compute_tradability_or_merged_bars_calls`,
  `test_a_legacy_row_recorded_without_opposite_band_fields_serves_them_absent_never_backfilled`):
  1. Exact per-row golden assertions for `band_member_count`/`band_round_number`/
     `band_member_timeframes`, including one row whose band holds a single member
     (`price_low == price_high`) and one row whose band is intraday-dominated (`1m`/`5m`).
  2. `sum(band_member_timeframes.values()) == band_member_count` invariant on every ranked row.
  3. Cross-check: for every ranked row, `band_member_count`/`band_round_number` byte-identical to
     `GET /research/tradability?symbol=<sym>&as_of=<snapshot as_of>`'s own selected band's
     `member_count`/`round_number` (mirrors `test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route`).
  4. Byte-identical row content on a same-pins re-run.
  5. Call-count guard: zero additional `BarStore` reads / `compute_tradability` calls.
  6. Rank-order golden: recorded row order byte-identical to a pre-change baseline capture (mirrors
     `test_row_order_is_unchanged_by_the_opposite_band_addition`).
  7. A legacy-row test proving the three fields are entirely absent (never backfilled) and the
     snapshot's `file_checksum` recomputes unchanged.
  8. `test_desk_screen_module_adds_no_config_field` re-run (must still pass unmodified).
  9. `tests/test_mcp_server.py` — confirm `desk_screen` tool stays a byte-identical no-arg GET proxy
     and the tool count stays exactly 17 (no test edit expected, only a re-run to confirm).
  10. `tests/test_copy_discipline.py` re-run unmodified (must still pass — the new `levels` column
      copy is descriptive counts/badges only).
  11. Frontend: extend or add a component test covering the new column's three states (populated
      tally + round-number badge, populated tally without the badge, legacy-absent copy).

## Agents Required

- developer: yes -- implement the backend row-builder fields (`desk_screen.py`), the frontend
  `levels` column + type contract (`page.tsx`, `types.ts`), and the full fixture-scoped test suite
  above (TDD: write the failing golden tests first, then the three-field copy).
  (backend-data: yes, frontend-ux: yes)

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/research/desk_screen.py` -- row-builder gains `band_member_count`/
  `band_round_number`/`band_member_timeframes`, copied verbatim from the `best` band dict; module
  docstring's per-field disclosure sections get a new "Wall-composition disclosure" entry tagged
  goal-desk-iter-23, following the existing per-iteration docstring convention.
- `apps/backend/tests/test_desk_screen.py` -- new golden/invariant/call-count/rank-order/legacy-row
  tests per "What to Build" above.
- `apps/frontend/lib/types.ts` -- `DeskScreenRow` gains the three optional fields + a doc comment
  matching the existing per-iteration comment style (~after line 849).
- `apps/frontend/app/desk/page.tsx` -- `DeskRow` gains a `levels` cell; `DeskRowsTable`'s header row
  gains a `levels` `<th>` beside `band`/`opposite`.
- Possibly a small frontend test file (wherever `/desk` component/unit tests currently live -- locate
  via existing test conventions before adding) covering the new column's three render states.
- `docs/handoffs/goal-desk-iter-23-dev.md` -- dev handoff (required by DoD).

Do NOT touch (OUT OF SCOPE, zero diff required): `_select_best_band`, `_select_opposite_band`,
`_row_rank_key`, `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`,
`StructureChart.tsx`, `PriceChart.tsx`, `config.py`, `app/engine/`, any MCP file, any `Config` field.

## UI Evolution

- New user-facing capability: every ranked `/desk` row now discloses how many levels its selected
  wall is built of, whether it's a round-number band, and the per-timeframe split of those levels --
  the same composition detail `/structure`'s own band table already shows for the identical band.
- New information displayed: `band_member_count`, `band_round_number`, `band_member_timeframes` per
  ranked row.
- New user actions: none -- pure disclosure, no new button/control.
- UI surface changes: `/desk` ranked table gains one column (`levels`), beside `band`/`opposite`; no
  new page, no new section.
- Navigation changes: none.

## Visual Requirements

- Component patterns: plain table cell (matches the existing `LABEL_CELL`/`NUMERIC_CELL` classes
  already used by sibling cells in `DeskRow`); the round-number badge reuses
  `/structure`'s exact `BandRow` badge markup/className (`structure/page.tsx:614-621`) verbatim --
  do not invent a new badge style.
- Layout: no layout change -- one additional `<td>`/`<th>` inserted into the existing ranked table,
  same row/column structure as the `band`/`opposite` columns it sits beside.
- Key visual effects: none new -- dense terminal-grade table row, matching house style (dark-only,
  no marketing chrome).
- States to handle: (1) populated tally + round-number badge, (2) populated tally with no badge
  (`band_round_number` false), (3) legacy snapshot -- entirely-absent fields render
  `"composition not recorded in this snapshot"`, matching the established `basis`/`history`/`band`/
  `opposite` legacy-absence pattern exactly (loose `== null` / `=== undefined` checks, never a
  computed fallback).

## Key Test Scenarios

- A NEW fixture-scoped screen computed over a universe + bar store already frozen (never written to
  the ambient `apps/backend/.data`) records `band_member_count`/`band_round_number`/
  `band_member_timeframes` on every ranked row, byte-identical to `GET /research/tradability`'s
  selected band for the same symbol/as-of.
- `sum(band_member_timeframes.values()) == band_member_count` holds on every ranked row, including a
  single-member row (count 1) and an intraday-dominated row (contains `1m`/`5m` keys).
- A same-pins re-run returns the existing snapshot honestly (no new file, byte-identical rows); a
  pre-iteration legacy snapshot's rows serve the three fields absent and its `file_checksum`
  recomputes unchanged.
- Rank order (`band_class`, `distance_bps`, `band_score`, `symbol`) is byte-identical to the
  pre-change baseline; a call-count guard proves zero additional `BarStore` reads/
  `compute_tradability` calls.
- Full backend suite green; `Config().config_fingerprint()` still `08e471b10130e1e2`; zero new
  `Config` fields; `tests/test_copy_discipline.py` green unmodified; MCP tool count still 17 and
  `desk_screen` still a byte-identical GET proxy.
- Browser (fixture-scoped rig, distinct ports from any ambient dev processes, `rm -rf
  apps/frontend/.next` clean rebuild first per T-9): a screenshot of the populated `/desk` `levels`
  column shows at least one row with `band_member_count <= 5` and one with `>= 100` legible together,
  plus a "round number" badge legible in the same or one further screenshot of the same rendered
  screen (T-10: no screenshot -> `unknown`, never `passing`).
- Regression: J-01..J-14 remain green via deterministic replay + LLM fallback; a `[NEW]`-flagged
  demo-narrator walkthrough (record mode, this iteration's working surface) narrates the `levels`
  column and round-number badge over populated ranked rows, `Demo Verdict: RECORDED` with a
  non-empty gallery.
