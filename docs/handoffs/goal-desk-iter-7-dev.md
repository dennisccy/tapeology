# goal-desk-iter-7 Dev Handoff

**Phase:** goal-desk-iter-7
**Date:** 2026-07-26
**Agent:** developer
**Status:** complete

## What Was Built

Journey **J-06** (MCP contract v3, 15 -> 17 read-only tools) plus audit finding **F2**'s
hover-honesty fix on the already-shipped `/desk` page, plus a golden-script fix for J-05. No new
page, panel, button, or route — `Frontend Present: yes` only because F2 touches an already-shipped
page and both changes need the reviewer/QA chain's UI-aware checks; J-07's own browser walk is a
QA-agent dispatch, not dev work (no new code was implied for it and none was added).

### Backend (J-06)

- **Two new no-required-argument MCP tools** in `apps/backend/app/mcp/__init__.py`: `desk_universe`
  -> `GET /research/desk/universe` and `desk_screen` -> `GET /research/desk/screen`, added to
  `_STATIC_PATHS` and the `TOOLS` tuple immediately after `edge_report` and before `pnl_ledger` (the
  file's own "newest addition after its dependency-order sibling" convention). `TOOL_NAMES` grows
  from 15 to 17. Both mirror the `datasets`/`setups`/`edge_report` no-arg shape exactly — a thin GET
  proxy with `inputSchema=_object_schema({})` — and proxy ONLY the base (no `?date=`) path; the
  `?date=` lookup variant of `GET /research/desk/screen` stays reachable exclusively through the
  existing `get_endpoint` tool (no code change needed there — `/research/desk/*` is already covered
  by the `/research/` allowlist prefix). `get_endpoint`'s allowlist was not touched.
- **`tests/test_mcp_server.py` extended to the 17-tool contract:**
  - `EXPECTED_TOOLS` gains `desk_universe`/`desk_screen` in the same position.
  - `backend_paths` fixture gains `TAPEOLOGY_DESK_UNIVERSE_DIR`/`TAPEOLOGY_DESK_SCREEN_DIR` (fresh
    per-module temp dirs), mirroring the existing `TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_DATASET_DIR`
    pattern, so the live test backend's desk stores are fully isolated from every other test.
  - 5 new tests: `desk_universe`/`desk_screen` each proven byte-identical to their curl equivalent
    in the honest-EMPTY state (asserted FIRST, before either store is ever seeded) and in a
    POPULATED state (seeded directly via `UniverseStore(dir).record(...)` /
    `ScreenStore(dir).record(...)` — the exact persistence calls the real routes make — into the
    live backend's env-scoped store dirs, the same `BarStore.record()`-direct-seeding precedent
    already used for `bars`/`levels`/`tradability`/`setups` in this file); plus one `get_endpoint`
    proxy test hitting `/research/desk/screen?date=2026-06-22` (a match, using the screen the
    populated-state test just recorded) and `?date=2020-01-01` (a non-match, asserting the honest
    `{"screen": null}` 200, never an error).
  - Every other existing test in the file (tool-set assertions, honest-404/backend-down loops,
    stdio session) already iterates `EXPECTED_TOOLS`/`TOOL_NAMES` generically, so no other test
    needed a code change to cover the two new tools.

### F2 — the hover-honesty regression (frontend + backend guard)

- **`apps/frontend/app/desk/page.tsx`**: the row's stretched drill-in anchor
  (`desk-row-drill-in`/`desk-skip-row-drill-in`, `absolute inset-0`) paints above every cell in the
  row, so the per-cell `title`s at `desk-row-distance`/`desk-row-score` and each coverage badge's
  own `title` — which carried the row's full-precision `distance_bps`/`band_score` and each
  timeframe's "window last requested" freshness — became pointer-unreachable (iter-6 audit finding
  F2). Fixed by adding a composite `title` directly on each anchor instead of touching any covered
  cell: `deskRowDrillInTitle(row)` builds `"distance <full precision> bps · score <full precision>
  · <timeframe> window last requested: <value|never> · ..."` for ranked rows;
  `deskSkipDrillInTitle(skip)` builds ONLY the coverage-freshness portion for skipped rows (no
  fabricated distance/score — a skip row has neither field). **Zero change** to either anchor's
  `href`, `absolute inset-0` class, `data-testid`, or any other row markup — this was the explicit
  build-time constraint (logged in the phase spec, not by me) to protect J-05 step 4's
  already-passing whole-row click. The rounded 2-decimal cell DISPLAY (audit F3) is unchanged; only
  the full-precision hover surface moved.
- **`apps/backend/tests/test_desk_hover_tooltip_guard.py`** (new file, sibling of
  `test_desk_ui_guards.py`, same read-the-.tsx-as-text discipline, no browser): locates each
  anchor's `title={fn(...)}` expression by its `data-testid`, extracts that function's own source
  block (brace-depth walk), and asserts:
  - the ranked-row anchor's function references `row.distance_bps`, `row.band_score`, AND
    `latest_window_end_utc`;
  - the skip-row anchor's function references `latest_window_end_utc` but NEVER
    `distance_bps`/`band_score`;
  - a seeded-violation counter-test proves both checks can actually fail (a static `title` with no
    dynamic expression, and a tooltip function missing a required field).

### Golden fix

- **`runs/goal-session-desk/journey-scripts/J-05.json` step 2**: target changed from the positional
  `{"testid": "desk-history-row"}` (first DOM match, i.e. table position) to
  `{"css": "[data-testid=\"desk-history-row\"][data-screen-date=\"2026-06-22\"]"}` (the `{"css":
  ...}` target type J-04.json step 4 already uses), so replay selects the intended history row by
  its own recorded `data-screen-date` attribute (`page.tsx:385`) rather than by position. No other
  step changed. Validated as syntactically valid JSON; not replayed against a live browser by me
  (J-05's own regression re-verification is the QA/replay lane's job this iteration, per the plan).

## Files Changed

- `apps/backend/app/mcp/__init__.py` — added `desk_universe`/`desk_screen` to `_STATIC_PATHS` + two
  new `types.Tool(...)` entries in `TOOLS`; one doc-comment line updated to note the new tools'
  shipped state.
- `apps/backend/tests/test_mcp_server.py` — `EXPECTED_TOOLS` grows to 17; `backend_paths` fixture
  gains two new env-dir keys; 5 new tests (see above).
- `apps/backend/tests/test_desk_hover_tooltip_guard.py` (new) — the F2 tooltip-composition guard +
  its seeded-violation counter-test (3 tests).
- `apps/frontend/app/desk/page.tsx` — added `deskRowDrillInTitle`/`deskSkipDrillInTitle`; applied
  `title={...}` to both drill-in anchors. No other line changed.
- `runs/goal-session-desk/journey-scripts/J-05.json` — step 2's click target.

**Not touched, deliberately** (per the plan's explicit out-of-scope list — none of these files were
opened): `desk_screen.py`'s CLI write-path guard, `bars.py`, `test_structure_chart_viewport.py`,
`StructureChart.tsx`, `PriceChart.tsx`, `app/engine/`, any `Config` field, any new backend route,
`apps/frontend/app/structure/page.tsx`, `apps/frontend/components/NavBar.tsx`, `app/meta.py`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junitxml=<path>`

Result: **1349 collected, 1341 passed, 8 skipped, 0 failed, 0 errors** (junit XML attributes
confirmed directly: `errors="0" failures="0" skipped="8" tests="1349"` — this pytest install's `-q`
mode does not print the final one-line summary to stdout in this environment, the same
already-documented quirk prior iterations' handoffs note, hence reading the junit XML instead).
Floor from the spec was 1341 collected / 1333 passing / 8 skipped; this diff adds exactly 8 new
tests (5 in `test_mcp_server.py`, 3 in `test_desk_hover_tooltip_guard.py`), all passing, zero new
skips, zero regressions.

Isolated re-runs for the specific changed areas (all green, all pre-full-suite):
- `tests/test_mcp_server.py` alone — 34 passed.
- `tests/test_mcp_server.py tests/test_desk_hover_tooltip_guard.py tests/test_desk_ui_guards.py
  tests/test_copy_discipline.py` together — 72 passed (proves the F2 fix did not disturb the
  existing desk-guard or copy-discipline lints).

Fingerprint pin: `Config().config_fingerprint()` == `08e471b10130e1e2` for both the live `CONFIG`
singleton and a fresh `Config()` — unchanged (zero new `Config` fields this iteration).

MCP tool count: `python -c 'import app.mcp; print(len(app.mcp.TOOL_NAMES))'` -> `17`, in the exact
order `tape_state, tape_features, tape_history, datasets, bars, levels, tradability, setups,
backtests, strategies, edge_report, desk_universe, desk_screen, pnl_ledger, taxonomy, ui_route_map,
get_endpoint`.

Frontend: `cd apps/frontend && rm -rf .next && npm run build` — compiles successfully, TypeScript
strict-mode typecheck passes with zero errors, `/desk` still registers as a static route alongside
`/` and `/structure` (unchanged route set, unchanged bundle shape).

Live sanity (a throwaway `uvicorn` instance on an unused port, scoped temp store dirs, killed
immediately after — not the pinned `:8301` browser-QA rig, which is the QA agent's own job this
iteration):
- `GET /health` -> `{"status":"ok"}`.
- `GET /meta/ui-routes` -> exactly the three routes (Cockpit/Structure/Desk), unchanged.
- `GET /research/desk/universe` / `GET /research/desk/screen` -> both honest-empty payloads before
  any registration/compute, matching the spec's exact literal bodies.
- A direct `app.mcp.call_tool` run against that same live instance: `list_tools()` returns 17 tools;
  `desk_universe`/`desk_screen` both return `isError=False` with the exact honest-empty JSON.

## Known Issues

- **J-07's browser walk was not performed by me** — per the plan, it needs no new code (only what
  J-06/F2 already produce) and is the browser-qa-agent's own dispatch; I did not touch
  `journey-scripts/J-07.json` or capture any of its required screenshots.
- **`journey-scripts/J-05.json`'s fixed step 2 was not replayed against a live browser by me** — I
  verified it parses as valid JSON and that the `data-screen-date` attribute it now targets already
  exists in the shipped page markup (`page.tsx:385`, unmodified this iteration), but the actual
  replay/browser re-verification of J-04/J-05 against the F2 change is the regression-replay lane's
  job this iteration, per the plan's own "Regression replay for J-01–J-05... re-verified specifically
  against the F2 change" bullet.
- Carried forward, not touched this iteration (per the plan's explicit "do not open" list): the
  owner's written ratification of the iteration-4 `bars.py`/`StructureChart.tsx` frozen-file
  exception; the same-date screen ambiguity; keyboard access for history rows; the three one-line
  hardening items from earlier iterations (CLI write-path guard, per-series price-less-row filter,
  chart-guard-test re-tightening).
