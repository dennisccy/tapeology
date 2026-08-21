# Phase goal-rapid-microscope-iter-22 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-22
**Date:** 2026-08-20
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | Scout Ledger section — new family block `data-testid="scout-family-failed_aggression_score__band_touch__trades_20"` | New data in existing table | Study 1 (range-wall failed aggression) is now reachable via `POST /research/desk/micro/scout/compute {"grid":"range_wall_failed_aggression_pilot"}` and appends its screen decision to this ledger | POST `{"grid":"range_wall_failed_aggression_pilot"}` to `http://localhost:8301/research/desk/micro/scout/compute`, poll `GET .../scout/compute` until `"state":"done"`, refresh `/desk`, click "Scout Ledger" (`data-testid="desk-section-expand-scoutLedger"`), and confirm a family block whose header reads `failed_aggression_score__band_touch__trades_20` appears with a trial row whose Feature cell reads `failed_aggression_score / threshold (band_touch)` and a non-blank Decision value. |
| `/desk` | Scout Ledger section — new family block `data-testid="scout-family-failed_aggression_score__playbook_signal__trades_20"` | New data in existing table | Study 3 (capitulation exhaustion) is now reachable via `POST /research/desk/micro/scout/compute {"grid":"capitulation_exhaustion_pilot"}` and appends its screen decision to this ledger | POST `{"grid":"capitulation_exhaustion_pilot"}` to `http://localhost:8301/research/desk/micro/scout/compute`, poll until `"state":"done"`, refresh `/desk`, expand "Scout Ledger", and confirm a family block whose header reads `failed_aggression_score__playbook_signal__trades_20` appears with a trial row whose Feature cell reads `failed_aggression_score / threshold (playbook_signal)` and a non-blank Decision value. |
| `/desk` | Scout Ledger section — walk-forward floor-check row under Study 1's family | New row in existing table | `register_screen_and_walkforward_check` appends the floor-check result as a second ledger row under the same `candidate_id`, never editing the screen row | In the `failed_aggression_score__band_touch__trades_20` family block, locate the row immediately below the screen row sharing its Candidate ID, and confirm its Feature and Horizon cells both show `—` (em-dash) and its Decision column reads exactly `killed_insufficient_n`. |
| `/desk` | Scout Ledger section — walk-forward floor-check row under Study 3's family | New row in existing table | Same floor-check chain, run for Study 3 | In the `failed_aggression_score__playbook_signal__trades_20` family block, locate the row immediately below the screen row sharing its Candidate ID, and confirm its Feature and Horizon cells both show `—` and its Decision column reads exactly `killed_insufficient_n`. |
| `/desk` | Scout Ledger section — Study 2's existing walk-forward floor-check row (`divergence_at_level_bearish__band_touch__trades_20` family) | Re-verification only — no code change | The iter-21 audit fixed this row but it was never freshly photographed on screen; this iteration's DoD requires a fresh, dated capture | Trigger `{"grid":"delta_divergence_pilot"}` (or confirm a prior run's row is still present), expand "Scout Ledger", locate the `divergence_at_level_bearish__band_touch__trades_20` family's second row under a shared Candidate ID, and confirm its Feature/Horizon cells show `—` and Decision reads `killed_insufficient_n` — capture a screenshot dated this iteration, not a reused iter-21 asset. |
| `/desk` | Scout Ledger section — "Run Screen" button (`data-testid="scout-ledger-trigger"`) | Regression check (unchanged behavior) | Confirms the shipped on-screen control still triggers only the unchanged default grid — no dropdown or control was added to select Study 1/2/3 | Click the "Run Screen" button on `/desk`, inspect the Network tab request body, and confirm it carries no `grid` field (or `grid: null`); after it completes, confirm any new row it produces has no `(band_touch)`/`(playbook_signal)` suffix in its Feature cell and no `killed_insufficient_n` floor-check row appears anywhere in that run's output. |
| `POST /research/desk/micro/scout/compute` (backend endpoint) | none — no UI control exists for either new value | New API request-body values, deliberately not wired to any control | `grid: "range_wall_failed_aggression_pilot"` and `grid: "capitulation_exhaustion_pilot"` are additive; the phase spec keeps this CLI/API-only this iteration | `curl -X POST http://localhost:8301/research/desk/micro/scout/compute -H "Content-Type: application/json" -d '{"grid":"range_wall_failed_aggression_pilot"}'` and confirm HTTP 200 with `{"state":"running","run_id":"..."}` (or `{"state":"refused","reason":"already_running"}` if a run is in flight); repeat with `{"grid":"capitulation_exhaustion_pilot"}` after the first completes. |
| `python -m app.research.scout --grid <selector>` (CLI, operator terminal) | none — terminal output, not a browser surface | Two new `--grid` choices added, wired the same way as the route | Proves the CLI path (not only the HTTP route or a unit test) produces the ledger rows | Run `python -m app.research.scout --grid range_wall_failed_aggression_pilot` from `apps/backend` against a fixture-pointed dataset dir, and confirm stdout prints `1 candidate(s) processed`; then confirm the on-disk scout ledger file gained the two expected rows (screen + `walkforward_floor_check`). |
| `GET /research/desk/micro/graduation` (backend endpoint, browser-navigated directly — J-07) | none — raw JSON body rendered by the browser's built-in viewer, not a `/desk` page section | Re-verification only — no code change expected; the round's wall-clock cut the prior fresh capture | Navigate the browser directly to `http://localhost:8301/research/desk/micro/graduation` and confirm the JSON body's `families` array is non-empty with each entry showing `family`, a sealed reading (`verdict`, `rule_hash`), and an observation count (`n`); capture a screenshot dated this iteration, not a reused iter-20 asset. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/scout.py` — `GRID_SELECTOR_RANGE_WALL_PILOT`,
  `GRID_SELECTOR_CAPITULATION_PILOT`, `_PILOT_GRID_SELECTORS` table, `ScoutComputeManager.trigger`'s
  generalized selector/resolver/`playbook_store` validation, and the CLI `main()`'s extended
  `--grid` choices/dispatch — pure backend wiring; its only observable trace is the two new Scout
  Ledger family rows already listed above. No new route, no new response field.
- `apps/backend/app/research/micro_routes.py` — `trigger_scout_compute`'s additive
  `playbook_store: PlaybookStore = Depends(get_playbook_store)` dependency and the
  selector-aware `_BAND_TOUCH_PILOT_SELECTORS`/`_PLAYBOOK_SIGNAL_PILOT_SELECTORS` construction —
  request-routing logic behind the already-listed `POST /scout/compute` endpoint; no new endpoint,
  no new response shape.
- `apps/backend/tests/test_scout.py` — rewritten `test_tc7_...` (now a positive proof) plus 7 new
  unit/route/CLI-path tests — test-only, zero UI surface.

---

## Summary

- **Frontend surfaces changed:** 0 files (no `apps/frontend/**` diff — confirmed by `git status`
  in the dev handoff); 1 already-shipped surface (`/desk` Scout Ledger table) gains new rows
  through its existing generic rendering.
- **New pages/routes:** 0
- **Modified components:** 0 (zero React component files touched)
- **Navigation changes:** no
- **Backend-only changes:** 3 (grid-selector wiring in `scout.py`, selector-aware dependency
  wiring in `micro_routes.py`, and the rewritten/added test suite in `test_scout.py`)
