# goal-desk-iter-23 Dev Handoff

**Phase:** goal-desk-iter-23
**Date:** 2026-07-30
**Agent:** developer
**Status:** complete

## What Was Built

J-15 — wall-composition disclosure on ranked `/desk` rows. Every ranked screen row now discloses
three fields, copied/tallied VERBATIM off the SAME `best` band dict `_select_best_band` already
returns (zero second `compute_tradability` call, zero second `BarStore` read, zero touch to
`_select_best_band`/`_select_opposite_band`/`_row_rank_key`):

- **`band_member_count`** (int) — copied verbatim from the selected band's own `member_count`
  (`tradability.py:343`).
- **`band_round_number`** (bool) — copied verbatim from the selected band's own `round_number`.
- **`band_member_timeframes`** (`dict[str, int]`) — a new helper, `_band_member_timeframes`, does a
  plain per-timeframe tally over that SAME band's own `members` list (mirrors `_bands_by_class`'s
  "plain dict tally" construction style). Keys are only the timeframes actually present among the
  band's own members, in first-seen order over `compute_tradability`'s own already-sorted
  `members` list (`tradability.py:364`) — Python dict insertion order makes this deterministic and
  stable across runs. Values always sum to `band_member_count` by construction (every member
  increments exactly one key).

Skip rows carry none of the three fields (unchanged code path — they never reach the `best =`
line). A screen snapshot recorded before this iteration has ranked rows that OMIT all three keys
entirely — never backfilled, never defaulted, never present as `null`.

Frontend: `/desk`'s ranked table gains one new `levels` column, beside the existing `band`/
`opposite` columns, rendering `${band_member_count} levels · ${tf1} ${count1} · ${tf2} ${count2}
...` (e.g. `155 levels · 1d 68 · 1h 57 · 4h 19 · 1w 11`) plus `/structure`'s own "round number"
badge — reused verbatim (same `data-testid="tradable-band-round-number"`, same className) — when
`band_round_number` is true. A legacy row (all three keys `=== undefined`) renders the established
honest-absence copy `"composition not recorded in this snapshot"`. No new tooltip line: every one
of the three values is an exact integer/boolean, so there is nothing rounded to disclose full
precision for.

No new endpoint, no new MCP tool, no new `Config` field, no new store, no new index. `GET
/research/desk/screen` (unchanged route) now simply serves these three additional keys on ranked
rows of any NEW snapshot.

## Files Changed

- `apps/backend/app/research/desk_screen.py` — added `_band_member_timeframes` helper; the ranked-
  row builder in `compute_screen` gains `band_member_count`/`band_round_number`/
  `band_member_timeframes`; module docstring gains a "Wall-composition disclosure" section;
  `compute_screen`'s own docstring updated to mention the three new fields.
- `apps/backend/tests/test_desk_screen.py` — `_band()` test helper extended with optional
  `members`/`round_number` kwargs (`member_count` is always `len(members)`, mirroring
  `tradability.py`'s own `_band`) so every EXISTING call site keeps working unchanged; added a
  golden test with three controlled rows (single-member zero-width band, intraday-dominated band,
  round-number multi-timeframe band), a real-fixture sum-invariant test over every ranked row, a
  row-order-unchanged golden, a byte-identical-recompute test, a legacy-row absence test, and a
  call-count guard test (zero extra `compute_tradability`/`merged_bars` calls); extended the
  existing `test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route` with TC-2/TC-3
  assertions against the real `GET /research/tradability` route.
- `apps/frontend/lib/types.ts` — `DeskScreenRow` gains `band_member_count?: number`,
  `band_round_number?: boolean`, `band_member_timeframes?: Record<string, number>` with a doc
  comment matching the established per-iteration convention.
- `apps/frontend/app/desk/page.tsx` — `DeskRow` gains a `levels` `<td>` cell (tally string + reused
  round-number badge, or the legacy-absence copy); `DeskRowsTable`'s header row gains a `levels`
  `<th>` beside `band`/`opposite`; page-header comment block gains a goal-desk-iter-23 section.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: 1454 passed, 8 skipped (full suite; zero failures, zero regressions)

Targeted: `.venv/bin/python -m pytest tests/test_desk_screen.py -v` → 78 passed (was 68 before this
iteration; 10 new/extended tests).
`.venv/bin/python -m pytest tests/test_mcp_server.py -v` → 38 passed (confirms `desk_screen`
byte-identical GET proxy and the exactly-17-tool contract, both unmodified).
`.venv/bin/python -m pytest tests/test_copy_discipline.py -q` → 30 passed unmodified.
`Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged; zero new `Config` fields —
`test_desk_screen_module_adds_no_config_field` passes unmodified).

Frontend: `npx tsc --noEmit` → clean. `rm -rf .next && npx next build` → compiles, lints, and type-
checks cleanly (Next's built-in ESLint pass included; no separate eslint config exists in this
project, confirmed via search — no other iteration ships one either). No frontend unit/component
test framework exists in this repo (no jest/vitest config, no test script in `package.json`, no
existing `*.test.*`/`*.spec.*` files anywhere under `apps/frontend`) — per the project's established
convention, `/desk` UI changes are verified via TypeScript/build + browser QA, not a new test
framework introduced mid-iteration.

`git diff --stat` confirms zero diff on every OUT-OF-SCOPE file: `tradability.py`, `levels.py`,
`bars.py`, `bar_index.py`, `desk_coverage.py`, `StructureChart.tsx`, `PriceChart.tsx`, `config.py`,
`app/engine/`, `app/mcp/`.

## Pre-handoff verification

- Service startup: `scripts/dev.sh` started both backend (`:8301`) and frontend (`:3301`) cleanly
  twice in a row (stop → restart, no port conflicts — `fuser`/`lsof` port-release loop in the
  script handled child processes correctly). `GET /research/desk/screen` → 200, `GET /desk` → 200,
  `GET /` → 200, `GET /structure` → 200 on both runs. All spawned processes killed before finishing
  (verified via `ps aux` — no `uvicorn`/`next dev`/`next-server` process left running).
- No new native dependency, no new external integration in this iteration — nothing to live-test.

## Known Issues

None. This is a pure additive-disclosure change: zero diff to the rank key, zero diff to any
OUT-OF-SCOPE file, zero new `Config` field, zero new MCP tool, zero new frontend test
infrastructure introduced (none existed before). Browser screenshot evidence (TC-10/TC-11) and the
`[NEW]`-flagged demo-narrator walkthrough (TC-12) are QA/showcase-lane responsibilities, not
exercised in this dev pass beyond the plain service-startup checks above.
