# goal-desk-iter-8 Dev Handoff

**Phase:** goal-desk-iter-8
**Date:** 2026-07-27
**Agent:** developer
**Status:** complete

## What Was Built

This iteration closes J-07's remaining evidence gaps and two one-line hygiene items. No new
product surface — every change is verification/hygiene, per the iter spec's own "New user-facing
capability: None" line.

- **Era-open kept-route baseline diff (DoD 1 & 2, TC-1/TC-2/TC-3).** A disposable diagnostic
  (`apps/backend/scripts/goal-desk-iter8-baseline-diff.py`) that: creates a scratch `git worktree`
  at the era-open commit `047c38e`; boots it against a throw-away copy of `.data/` + the journal
  DB; boots the current tree against an identical throw-away copy of the SAME data snapshot; curls
  18 kept routes with the spec's concrete inputs (AAPL as-of 2026-06-22/2026-07-25, the real PG
  dataset id, the real AAPL 1d bar-series id, a live-resolved setup id) against both; diffs every
  body byte-for-byte; and writes `reports/goal-desk-iter-8-kept-route-baseline.md`. Result: **16
  match / 2 differ**, both differences explained, not defects — `/research/candles` (merged AAPL
  1d) differs by exactly the R-1 price-less-row exclusion (`integrity_errors` 0→1,
  `revised_timestamps` 188→187), and `/meta/ui-routes` differs by the named 2→3 exemption. The
  report also runs `git diff --name-only 047c38e -- apps/` (42 files) and accounts for every one
  against either R-1's eight named files or `docs/goal.md`'s Key Capability inventory — **zero
  unaccounted files**. Never touches the ambient `apps/backend/.data/`; both throw-away copies and
  the scratch worktree are torn down after the run.
- **Golden-script restore + proof (DoD 3, TC-4).** `runs/goal-session-desk/journey-scripts/J-07.json`
  step 10's target restored from `{"testid": "tradable-map-table"}` (iter-7's out-of-scope, false-premise
  edit) back to `{"testid": "tradable-map-chart-caption"}`. Proved with a real
  `--mode verify --journeys J-04,J-05,J-07` deterministic-replay run against a fixture-scoped
  backend (a throw-away copy of `.data/`, never the ambient store) + a freshly `rm -rf .next`-rebuilt
  frontend on the era's `:8301`/`:3301` browser-QA rig convention — all three journeys PASS, 0
  failed. Results kept at `reports/phase-goal-desk-iter-8-regression-replay-results.md`; screenshots
  at `reports/qa/goal-desk-iter-8-evidence/{J-04,J-05,J-07}-verify.png`.
- **B1 fix — isolated MCP date-lookup test (DoD 5, TC-6).**
  `test_get_endpoint_desk_screen_date_query_proxies_verbatim`
  (`apps/backend/tests/test_mcp_server.py`) now seeds its OWN screen snapshot under a third,
  distinct date (`DESK_SCREEN_ISOLATED_DATE = "2026-06-23"`) instead of depending on
  `test_desk_screen_tool_byte_identical_on_a_populated_state`'s side effect. Passes standalone
  (`pytest -k ...`) and inside the full module/suite. No other test in the file touched.
- **F1 fix — untrue comment (DoD 6, TC-7).** `apps/frontend/app/desk/page.tsx:207`'s comment no
  longer claims "each cell's `title` carries the served value in full" — it now says the
  full-precision detail is reachable via the row's own drill-in anchor's composite `title`
  (`deskRowDrillInTitle`, audit F2's actual fix), matching reality. Comment-only; zero change to
  any anchor `href`, `absolute inset-0`, `data-testid`, or click geometry.
- **R-1 ratification verified present, untouched.** `docs/goal.md`'s
  `### OWNER RATIFICATION — 2026-07-27 (price-less-bar repair) — R-1` section was read and confirmed
  present verbatim — not re-worded, shortened, or moved.

## Files Changed

- `apps/backend/scripts/goal-desk-iter8-baseline-diff.py` -- new, disposable one-off diagnostic (era-open vs current kept-route diff); lives under `apps/backend/scripts/` (a project-owned dir), NOT the repo-root `scripts/` symlink, which resolves into the vendored `incredible_auto_dev/` framework subtree.
- `apps/backend/tests/test_mcp_server.py` -- `test_get_endpoint_desk_screen_date_query_proxies_verbatim` now seeds its own screen snapshot under an isolated date (audit B1 fix).
- `apps/frontend/app/desk/page.tsx` -- one comment corrected at the `DeskRow` doc-comment block (audit F1 fix); zero code/behavior change.
- `runs/goal-session-desk/journey-scripts/J-07.json` -- step 10's target restored to `tradable-map-chart-caption` (audit T1 fix).
- `reports/goal-desk-iter-8-kept-route-baseline.md` -- new, the required TC-1/TC-2/TC-3 diagnostic report.
- `reports/phase-goal-desk-iter-8-regression-replay-results.md` -- new, the required TC-4/TC-10 deterministic-replay results (J-04, J-05, J-07 all PASS).
- `reports/qa/goal-desk-iter-8-evidence/{J-04,J-05,J-07}-verify.png` -- new, replay evidence screenshots.

## Tests Run

- `apps/backend/.venv/bin/python -m pytest tests/test_mcp_server.py::test_get_endpoint_desk_screen_date_query_proxies_verbatim -q` (standalone) -- 1 passed (TC-6, isolation proven).
- `apps/backend/.venv/bin/python -m pytest tests/test_mcp_server.py -q` (full module) -- 34 passed.
- `apps/backend/.venv/bin/python -m pytest tests/ -q` (full suite) -- **1341 passed, 8 skipped, 0 failed** (exact character-level recount off the progress bar, since this pytest/plugin combo did not print its usual trailing summary line in this run -- exit code 0 corroborates). At/above the 1341/8 floor.
- `python -c "from app.config import Config; print(Config().config_fingerprint())"` -- `08e471b10130e1e2` (pin unchanged).
- `python3 incredible_auto_dev/scripts/automation/lib/demo_runner.py --mode verify --journeys J-04,J-05,J-07 --base-url http://localhost:3301 ...` -- 3 journey(s), 0 failed (PASS). Ran against a fixture-scoped rig: backend on `:8301` pointed at a throw-away copy of `.data/` (never ambient), frontend on `:3301` after `rm -rf apps/frontend/.next` + rebuild (T-9). No write-path side effect landed on the ambient store (TC-10).
- `apps/backend/scripts/goal-desk-iter8-baseline-diff.py` -- see "What Was Built" above; 16 match / 2 differ, both explained; zero unaccounted files in the 42-file `git diff --name-only 047c38e -- apps/` inventory.

## Known Issues

- **DoD item "screenshot of the Cockpit in Historical mode on a real symbol" (TC-5) is NOT captured
  by this dev pass.** The DoD's own wording assigns this to browser-qa-agent ("exists and is opened
  by browser-qa-agent"), and it needs live browser interaction/visual judgment beyond a deterministic
  golden-script replay (there is no golden script covering Cockpit Historical mode). Left for the
  next pipeline stage. A fixture-scoped rig recipe is already proven working in this iteration
  (backend `:8301` + throw-away `.data/` copy + `rm -rf .next` + frontend `:3301`) and can be reused
  directly for that capture.
- **The full DoD "J-07 passes via browser-qa-agent (full kept-product walk...)" line is broader than
  what this dev pass proved.** The GOLDEN SCRIPT `J-07.json` (11 steps: sim cockpit watch + `/structure`
  AAPL load) is deterministically proven PASS here. The wider walk (Case Studies drill-in, Edge
  Report honest state, Historical-mode cockpit) is not encoded in any golden script and needs the
  browser-qa-agent's LLM-driven lane, same division of labor as every prior iteration.
- **The one-off diagnostic script's `/research/setups` call is genuinely slow on a cold cache**
  (observed ~8-10 minutes on a throw-away data copy whose `setups_scan_cache.db` entries key on
  `_config_content_hash(CONFIG)`, which differs between era-open's Config -- fewer `desk_*` fields
  -- and the current tree's, forcing a real recompute on both sides). Not a defect: `setups.py` is
  unchanged code this era (confirmed via `git diff --name-only 047c38e -- apps/backend/app/research/setups.py`
  producing no output), and the script's generous 90s per-request timeout absorbed this without a
  false "differs" in the final report. Worth knowing if this script is ever re-run: expect the
  `setups`/`setups/{id}` rows to take a while the first time.
- **No new product surface, no Config field, no route, no new test beyond the one B1 fix** -- this
  iteration is pure verification + two one-line hygiene edits + one golden-script restore, exactly
  as scoped. `OUT OF SCOPE`'s named files (`bars.py`, `StructureChart.tsx`, `PriceChart.tsx`, any
  guard test) were not touched.
