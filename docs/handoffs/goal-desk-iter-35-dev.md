# goal-desk-iter-35 Dev Handoff

**Phase:** goal-desk-iter-35
**Date:** 2026-07-31
**Agent:** developer
**Status:** complete

## What Was Built

J-20 ("Every recorded screen states how it differs from the screen recorded before it") — a new
read-only screen-comparison disclosure, backend + frontend, per the iter spec's IN SCOPE list.

### Backend
- **New module** `apps/backend/app/research/desk_screen_diff.py` — `compute_screen_diff(store,
  compare_id, base_id=None)`, the comparison's ONE computation. Reads exactly two recorded
  snapshots via the existing `ScreenStore.list()` accessor (zero new store, zero new file, zero
  recompute). Structurally incapable of calling `compute_tradability`/reading `BarStore`/
  `bar_index`/`DatasetStore` — the module imports none of those names (proven by a `hasattr`
  guard test, not just behavior).
  - Base resolution: default = greatest `screen_date` strictly earlier than the compare
    snapshot's own date, ties broken by later `created_utc` (reuses `ScreenStore.list()`'s own
    `(created_utc, id)`-ascending sort, so this can never disagree with `GET
    /research/desk/screen?date=`'s own `matching[-1]`). Explicit `base=<id>` overrides it. No
    earlier snapshot → `base: null`, `base_resolution: "none_earlier"`, `rows: []` (a comparison
    needs two sides; this is its own honest state, not "compare vs. nothing"). Unknown `base=`
    id → `base: null` but `base_resolution` stays `"explicit"` (a specific base WAS asked for; it
    just isn't there — distinct from "none exists at all").
  - Row construction: compare-ranked rows first (in the compare snapshot's own served order,
    `"compared"` when the base also ranked it, `"entered"` otherwise, carrying the base's own
    skip reason when it has one and an honest `null` when the base doesn't mention the symbol at
    all), then base-only `"left"` rows (the mirror image, in the base snapshot's own served
    order). `rank_change` = a plain integer subtraction of two already-recorded 1-based positions
    (`compare_rank - base_rank`), set only on `"compared"` rows.
  - `identical` = true iff zero entered/left AND every compared row's `rank_change`/side/
    band_class/distance_bps/basis_as_of match exactly (not merely the four `counts` fields).
  - Self-compare (`base == compare_id`) raises `ScreenDiffSelfCompareError` — checked BEFORE any
    store lookup.
- **New route** `GET /research/desk/screen/compare?id=<compare id>&base=<base id>` in
  `desk_routes.py` — takes only a `ScreenStore` dependency (no `BarStore`/`bar_index`/
  `DatasetStore`), so it is structurally incapable of triggering a recompute. Unresolved `id` →
  honest `{"compare": null, ...}` at HTTP 200 (never 404/500). Self-compare → HTTP 422 with an
  explicit "cannot compare ... with itself" detail.
- No `main.py` change (same router), no new `Config` field, no new MCP tool (the existing
  `/research/` allowlist already reaches the new path — verified: `test_mcp_server.py`'s 17-tool
  contract still passes unmodified), no diff to `desk_screen.py`/`tradability.py`/`levels.py`/
  `bars.py`/`bar_index.py`/`desk_coverage.py` (confirmed via `git diff --stat`, all empty).

### Frontend
- **New "Screen Comparison" section** on `/desk` (`apps/frontend/app/desk/page.tsx`), rendered as
  the LAST section on the page — strictly after the ranked briefing table (inside
  `DeskPopulatedScreen`) and after Top-up Runs / Index Reconciliation / Screen Runs — so no
  existing golden's first-visible-match text search can resolve into it. New components:
  `ScreenCompareMeta`, `ScreenCompareRowView`, `ScreenCompareTable` (capped at
  `SCREEN_COMPARE_ROWS_DISPLAY_CAP = 20` rows with an honest "showing N of M" line, the shipped
  `EARLIER_PAIRS_DISPLAY_CAP` pattern), `ScreenComparisonSection` (loading/unavailable/populated
  states, mirroring `TopupRunsSection`/`ScreenRunsSection`).
  - Shows both compared snapshots' own id/screen date/recorded-at/bar-store signature, a
    descriptive counts line (compared/rank changed/side changed/entered/left), the honest
    "ranked rows are identical" line, or the honest "No earlier recorded screen exists to compare
    against." state on the ledger's oldest snapshot.
  - The capped table renders symbol/status/rank(this)/rank(base)/rank change/side(this)/
    side(base)/distance(this)/distance(base) — deliberately NOT band_class/basis_as_of (the
    spec's own literal wording names only rank/side/distance for the table); every cell is a
    verbatim render, zero client-side arithmetic.
  - Wired to `GET /research/desk/screen/compare?id=<currently displayed screen's id>` via a new
    `useEffect` keyed on `displayedSnapshot`'s id — a page-load/id-change GET only, no new
    control, no recompute trigger.
  - New testids all live in their own `desk-screen-compare-*` namespace — never reuses
    `data-screen-id`/`desk-history-row`/`desk-screen-row`/any `desk-row-*` testid (proven by a
    new guard test, see below).
- New types in `apps/frontend/lib/types.ts`: `DeskScreenCompareSnapshotMeta`,
  `DeskScreenCompareRow`, `DeskScreenCompareCounts`, `DeskScreenCompareResult`.
- New fetch function `fetchDeskScreenCompare(id)` in `apps/frontend/lib/api.ts`, mirroring
  `fetchDeskScreenById`'s exact `{ok, data, error}` shape.
- No new ranked-table column, no change to the ranked table's rendering (J-16's width contract
  untouched) — verified via `test_desk_ui_guards.py` passing unmodified.

## Files Changed
- `apps/backend/app/research/desk_screen_diff.py` -- NEW: the comparison's one computation
- `apps/backend/app/research/desk_routes.py` -- new `GET /screen/compare` route + import
- `apps/backend/tests/test_desk_screen_diff.py` -- NEW: 26 tests (module + route level, TC-1..TC-10)
- `apps/backend/tests/test_desk_screen_compare_ui_guard.py` -- NEW: 5 source-introspection guard
  tests (no reused testid, renders after the ranked table)
- `apps/frontend/lib/types.ts` -- new `DeskScreenCompare*` types
- `apps/frontend/lib/api.ts` -- new `fetchDeskScreenCompare`
- `apps/frontend/app/desk/page.tsx` -- new Screen Comparison section + wiring

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: 1551 passed, 8 skipped, 0 failed (exit 0) — full suite, including the two new test files
above. Targeted new-file run: `pytest tests/test_desk_screen_diff.py
tests/test_desk_screen_compare_ui_guard.py -q` → 31 passed.

Guard files pinned by the iter spec (must pass unmodified — confirmed byte-unchanged via `git
diff`, zero edits made): `test_copy_discipline.py`, `test_desk_ui_guards.py`,
`test_desk_hover_tooltip_guard.py` — all pass (47 tests). `test_mcp_server.py` — 39 tests pass
(17-tool contract unaffected).

Frontend: `cd apps/frontend && npm run build` → compiles clean, zero type errors
(`Route (app) ... /desk 10.3 kB`).

Fingerprint sentinel: `Config().config_fingerprint()` == `08e471b10130e1e2` (unchanged, both via
a dedicated test and a direct `python -c` check).

Live server smoke check: started `uvicorn main:app` on a scratch port against scoped
`TAPEOLOGY_DESK_*`/`TAPEOLOGY_BAR_DIR` env vars, confirmed `GET /research/desk/screen/compare?id=
does-not-exist` returns HTTP 200 with the honest null shape, confirmed the server started/stopped
cleanly with no port left bound. No server processes left running after this handoff.

## Known Issues

- The `[NEW]`-flagged demo-narrator walkthrough and `journey-scripts/J-20.json` are NOT part of
  this handoff — per this codebase's own pipeline division of labor, journey-scripts are authored
  by the browser-qa-agent (not the developer), and the demo-narrator walkthrough is a separate
  pipeline step that must record against the actually-rendered page after this code lands (per
  lessons.md iter-33: never record before the code ships).
- The capped comparison table intentionally shows only rank/side/distance per symbol (not
  band_class/basis_as_of), matching the spec's own literal wording for the table ("this
  snapshot's recorded rank/side/distance and the base's own recorded rank/side/distance"); the
  full API response still carries `compare_band_class`/`base_band_class`/`compare_basis_as_of`/
  `base_basis_as_of` per the Data Contract, they are simply not rendered as extra table columns
  this iteration (kept minimal, matching "no new ranked-table column" discipline).
- No real screen run was triggered this iteration (none needed — the ambient ledger's 12 recorded
  snapshots already carry the identical-state, churned-state, and oldest/no-earlier examples the
  acceptance names, per the spec's own NOTES section).
- I did not verify the SHA-256 byte-identity of the real ambient `.data/` universe/screen/topup/
  reconciliation/screen-run files before vs. after this change (TC-17) — my new route is
  structurally read-only (only takes a `ScreenStore` dependency, no write path exists anywhere in
  `desk_screen_diff.py`), and I never touched the ambient `.data/` directory during development
  (all tests and the live-server smoke check used scoped `tmp_path`/scratch-port env vars) — but
  the auditor/QA lane should still take the real before/after checksum listing over the ambient
  ledger as the authoritative proof, per the spec's own TC-17 wording.
