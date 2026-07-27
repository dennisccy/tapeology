# Iteration State — desk

**After iteration:** 8 · **Date:** 2026-07-27 · **Verdict:** GOAL_ACHIEVED

## Journeys

7 passing (J-01 J-02 J-03 J-04 J-05 J-06 J-07) · 0 failing · 0 unknown — 7 total

## Active blockers

- none — the era's last blocker (owner ratification of iteration 4's frozen-file repair) is resolved by
  `docs/goal.md:103` "OWNER RATIFICATION — 2026-07-27 (price-less-bar repair) — R-1".
- Open OPERATOR item, not a blocker and not product work: on the ambient `apps/backend/.data/`, the
  `/structure` Case Studies panel scans on page load because this era's sanctioned new `Config` fields
  re-keyed `setups_scan_cache.db`. Values byte-identical; remedy = one operator scan warm.

## Last 2 verdicts

- iter 8: GOAL_ACHIEVED — J-07 `partial → passing` on every clause, each re-run or re-opened by the
  evaluator itself: 1341 pass / 8 skip / 0 fail, pin `08e471b10130e1e2`, `UI_ROUTES` = 3, `TOOL_NAMES` =
  17, 16/18 kept routes byte-identical vs era-open `047c38e` (2 differences named exempt or
  R-1-attributed), guard tests byte-unmodified, ambient registered data untouched, COHERENCE-PASS.
- iter 7: STALLED — every path to a passing J-07 needed one written owner decision; the owner ratified.

## Do not redo

- **J-01–J-06 DONE and clause-verified** (`state/journey-history.json` per-journey
  `last_evidence_path`), all re-verified passing in iter-8. Do not re-derive their internals.
- **Era-open baseline CAPTURED** — `reports/goal-desk-iter-8-kept-route-baseline.md` (16 match / 2
  explained differ + the 42-file out-of-inventory accounting). Do not re-run.
- **R-1's eight files are IN INVENTORY and CLOSED** (`bars.py`, `yahoo.py`, `routes.py`,
  `StructureChart.tsx`, `test_structure_chart_viewport.py`, `test_bars.py`, `test_yahoo_adapter.py`,
  `test_bars_api.py`) — never reopen, revert, or re-word that goal.md section.
- **Goldens settled:** `J-07.json` step 10 = `tradable-map-chart-caption` (replay-proven); `J-05.json`
  carries a deliberate 4 s wait (timing only, target + text unchanged); goldens stay write-free and any
  future edit must be disclosed in the results report.
- **Pictures exist, do not re-shoot** (`reports/qa/goal-desk-iter-8-evidence/`): Cockpit Historical on AAPL, sim cockpit, Structure wall + honest Edge Report, `/desk` briefing, J-05 drill-in/no-params.
- **Settled:** zero new `Config` field all era; suite floor 1341 pass / 8 skip (1349 collected); pin
  `08e471b10130e1e2`; `UI_ROUTES` = 3; MCP = 17 read-only tools; fixture-scoped rigs are the recipe. Carried hygiene when those files next open: guard `run_screen_and_record`; finite-price filter on the per-series read; same-date screen ambiguity; keyboard access for history rows.
